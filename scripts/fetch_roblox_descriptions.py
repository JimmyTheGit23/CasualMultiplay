#!/usr/bin/env python3
"""
抓 Roblox 游戏 description + game_type (直接用 placeId, 不转 universeId)
"""
import json
import os
import re
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
RBX_PATH = os.path.join(DATA_DIR, 'roblox_games.json')


def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def extract_description(html):
    if not html:
        return None
    m = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
    if m:
        d = m.group(1)
        d = d.replace('&#xA;', '\n').replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'").replace('&lt;', '<').replace('&gt;', '>')
        return d
    return None


def extract_game_type(name, desc):
    if not desc and not name:
        return ''
    text = ((name or '') + ' ' + (desc or '')).lower()
    type_map = [
        (['roleplay', 'brookhaven', 'rp '], 'Roleplay'),
        (['brainrot', 'steal '], 'Steal Game'),
        (['obby', 'obstacle', 'jump'], 'Obby'),
        (['escape', 'tsunami', 'evade', 'run away'], 'Escape'),
        (['tower', 'defense', 'defence'], 'Tower Defense'),
        (['simulator'], 'Simulator'),
        (['survive', 'survival', 'horror'], 'Survival Horror'),
        (['murder', 'mystery'], 'Mystery'),
        (['war', 'battle', 'fight', 'combat', 'pvp'], 'Battle Royale'),
        (['tycoon'], 'Tycoon'),
        (['grow', 'garden', 'plant', 'pet '], 'Simulation'),
        (['anime'], 'Anime'),
        (['parkour'], 'Parkour'),
        (['gacha'], 'Gacha'),
        (['lucky', 'claw'], 'Lucky Draw'),
        (['clicker', 'simulator'], 'Clicker'),
        (['music', 'rhythm', 'song'], 'Music'),
        (['car', 'racing', 'driving', 'drift'], 'Racing'),
        (['speed', 'fast', 'sprint'], 'Speed Run'),
    ]
    for keywords, t in type_map:
        for k in keywords:
            if k in text:
                return t
    return ''


def shorten(desc, n=200):
    if not desc:
        return ''
    desc = re.sub(r'\s+', ' ', desc).strip()
    first = desc.split('\n')[0].strip() if '\n' in desc else desc
    if len(first) > 30:
        return first[:n] + ('...' if len(first) > n else '')
    return desc[:n] + ('...' if len(desc) > n else '')


def main():
    print('=== Roblox description 抓取 (v2 直接 placeId) ===')
    with open(RBX_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    games = data.get('games', [])

    targets = [g for g in games if g.get('icon_url') and not g.get('description')]
    print(f'目标: {len(targets)} 款游戏')

    updated = 0
    failed = 0
    save_every = 10
    t0 = time.time()

    for i, g in enumerate(targets):
        pid = g['placeId']
        url = f'https://www.roblox.com/games/{pid}'
        html = fetch(url)
        desc = extract_description(html) if html else None
        if desc:
            g['description'] = shorten(desc, 200)
            g['game_type_en'] = extract_game_type(g.get('name', ''), desc)
            updated += 1
        else:
            failed += 1
        # 每 N 个持久化一次
        if (i + 1) % save_every == 0:
            with open(RBX_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(targets) - i - 1) / rate if rate > 0 else 0
            print(f'  [{i+1}/{len(targets)}] ok={updated} fail={failed} | {elapsed:.0f}s | ETA {eta:.0f}s')
        time.sleep(0.3)

    # 最终写回
    with open(RBX_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\n完成: 抓取 {updated} 款, 失败 {failed}, 用时 {time.time()-t0:.0f}s')
    print(f'文件大小: {os.path.getsize(RBX_PATH)/1024:.1f} KB')

    # 抽样
    samples = [g for g in games if g.get('description')][:3]
    for s in samples:
        print(f'\n{s["name"]}: {s.get("game_type_en")}')
        print(f'  {s.get("description", "")[:100]}...')


if __name__ == '__main__':
    main()
