"""
Roblox icon 快速抓取 - 补充缺失的 icon_url
- 之前 fetch_roblox_icons.py 抓了 Top 200, 剩下 596 个没抓
- 用更激进的并发 + 短间隔
- 输出: 补全 docs/data/roblox_games.json 的 icon_url
"""

import json
import urllib.request
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

PATH = "docs/data/roblox_games.json"

def fetch_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None

def get_universe_id(place_id):
    """placeId → universeId (单 API)"""
    url = f'https://apis.roblox.com/universes/v1/places/{place_id}/universe'
    d = fetch_json(url)
    if d and 'universeId' in d:
        return d['universeId']
    return None

def get_icons_batch(universe_ids):
    """universeIds 批量 → icon URLs"""
    if not universe_ids:
        return {}
    url = f'https://thumbnails.roblox.com/v1/games/icons?universeIds={",".join(str(u) for u in universe_ids)}&size=256x256&format=Png&isCircular=false'
    d = fetch_json(url)
    if not d or 'data' not in d:
        return {}
    return {item['targetId']: item['imageUrl'] for item in d['data'] if item.get('imageUrl')}

def main():
    with open(PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    games = data['games']
    missing = [g for g in games if not g.get('icon_url')]
    print(f'共 {len(games)} 款, 缺 icon: {len(missing)}')

    # 阶段 1: 并发获取 universeId (10 线程)
    print(f'\n[1/2] 获取 {len(missing)} 个 universeId...')
    pid_to_uid = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(get_universe_id, g['placeId']): g for g in missing}
        done = 0
        for fut in as_completed(futures):
            g = futures[fut]
            uid = fut.result()
            done += 1
            if uid:
                pid_to_uid[g['placeId']] = uid
            if done % 100 == 0:
                print(f'  [{done}/{len(missing)}] {len(pid_to_uid)} 成功 ({time.time()-t0:.0f}s)')
    print(f'  完成: {len(pid_to_uid)}/{len(missing)} 成功 ({time.time()-t0:.0f}s)')

    # 阶段 2: 批量获取 icon URL (每批 100)
    print(f'\n[2/2] 批量获取 icon URL...')
    uids = list(pid_to_uid.values())
    uid_to_icon = {}
    t0 = time.time()
    for i in range(0, len(uids), 100):
        batch = uids[i:i+100]
        icons = get_icons_batch(batch)
        uid_to_icon.update(icons)
        if (i // 100) % 5 == 0:
            print(f'  [{i+len(batch)}/{len(uids)}] {len(uid_to_icon)} 成功 ({time.time()-t0:.0f}s)')
    print(f'  完成: {len(uid_to_icon)}/{len(uids)} 成功 ({time.time()-t0:.0f}s)')

    # 写回
    updated = 0
    for g in games:
        uid = pid_to_uid.get(g['placeId'])
        if uid and uid in uid_to_icon:
            g['icon_url'] = uid_to_icon[uid]
            updated += 1
    data['_meta']['icons_count'] = sum(1 for g in games if g.get('icon_url'))
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\n本次更新 {updated} 个, 总计 {data["_meta"]["icons_count"]}/{len(games)}')

if __name__ == "__main__":
    main()
