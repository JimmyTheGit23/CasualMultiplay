#!/usr/bin/env python3
"""
Roblox 游戏图标抓取
输入: docs/data/roblox_games.json
输出: 同文件,给每款游戏加 icon_url 字段

流程:
1. placeId → universeId (单调用 https://apis.roblox.com/universes/v1/places/{pid}/universe)
2. universeIds 批量 → icon URL (https://thumbnails.roblox.com/v1/games/icons,每批 100)
"""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
RBX_PATH = os.path.join(DATA_DIR, 'roblox_games.json')

CST = timezone(timedelta(hours=8))


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 + attempt)
            else:
                return None


def get_universe_id(place_id):
    url = f'https://apis.roblox.com/universes/v1/places/{place_id}/universe'
    d = fetch_json(url)
    if d and 'universeId' in d:
        return d['universeId']
    return None


def get_icons_batch(universe_ids):
    """批量获取 icon URL, 一次最多 100 个"""
    if not universe_ids:
        return {}
    url = f'https://thumbnails.roblox.com/v1/games/icons?universeIds={",".join(str(u) for u in universe_ids)}&size=256x256&format=Png&isCircular=false'
    d = fetch_json(url)
    if not d or 'data' not in d:
        return {}
    result = {}
    for item in d['data']:
        if item.get('state') == 'Completed' and item.get('imageUrl'):
            result[item['targetId']] = item['imageUrl']
    return result


def main():
    print('=== Roblox 游戏图标抓取 ===')
    with open(RBX_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    games = data.get('games', [])
    print(f'共 {len(games)} 款游戏')

    # 已有 icon 的跳过
    need_icon = [g for g in games if not g.get('icon_url')]
    print(f'需要抓取: {len(need_icon)} 款')

    if not need_icon:
        print('全部已有 icon, 跳过')
        return

    # 阶段 1: 收集 universeId
    print('\n--- 阶段 1: placeId → universeId ---')
    pid_to_uid = {}
    failed = []
    for i, g in enumerate(need_icon):
        pid = g['placeId']
        uid = get_universe_id(pid)
        if uid:
            pid_to_uid[pid] = uid
        else:
            failed.append(pid)
        if (i + 1) % 50 == 0:
            print(f'  [{i+1}/{len(need_icon)}] 已获取 universeId: {len(pid_to_uid)}')
        time.sleep(0.2)  # 限速

    print(f'\n阶段 1 完成: {len(pid_to_uid)} 成功, {len(failed)} 失败')

    # 阶段 2: 批量获取 icon URL
    print('\n--- 阶段 2: universeIds → icon URLs (批量 100) ---')
    uid_to_icon = {}
    uids = list(pid_to_uid.values())
    for i in range(0, len(uids), 100):
        batch = uids[i:i+100]
        icons = get_icons_batch(batch)
        uid_to_icon.update(icons)
        print(f'  批次 {i//100 + 1}: {len(batch)} 个 universeId, 获取 {len(icons)} 个 icon')
        time.sleep(0.5)

    print(f'\n阶段 2 完成: {len(uid_to_icon)} 个 icon URL')

    # 写回 games
    updated = 0
    for g in games:
        pid = g['placeId']
        uid = pid_to_uid.get(pid)
        if uid and uid in uid_to_icon:
            g['icon_url'] = uid_to_icon[uid]
            updated += 1
        elif not g.get('icon_url'):
            g['icon_url'] = ''  # 标记为已尝试,前端用占位符

    # 更新 meta
    data['_meta']['icons_fetched_at'] = datetime.now(CST).isoformat()
    data['_meta']['icons_count'] = updated

    with open(RBX_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: {RBX_PATH}')
    print(f'更新 {updated}/{len(games)} 款游戏的 icon_url')
    print(f'文件大小: {os.path.getsize(RBX_PATH)/1024:.1f} KB')


if __name__ == '__main__':
    main()
