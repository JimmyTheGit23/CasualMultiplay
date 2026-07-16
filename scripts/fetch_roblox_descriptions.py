#!/usr/bin/env python3
"""
抓取 Roblox 游戏 description 和游戏类型
输入: docs/data/roblox_games.json (含 icon_url)
输出: 同文件,加 description / game_type_en 字段

流程:
1. 已有 icon 的游戏 (有 universeId 通过 icon 抓取阶段)
2. 抓 https://www.roblox.com/games/{universeId} 的 og:description
3. 提取:
   - description: og:description 的前 200 字符
   - game_type_en: 从描述或 name 关键词提取
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
RBX_PATH = os.path.join(DATA_DIR, 'roblox_games.json')


def fetch_html(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return None


def get_description(universe_id):
    """抓 Roblox 游戏页 og:description"""
    url = f'https://www.roblox.com/games/{universe_id}'
    html = fetch_html(url)
    if not html:
        return None
    m = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
    if m:
        desc = m.group(1)
        # HTML entity 解码
        desc = desc.replace('&#xA;', '\n').replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'").replace('&lt;', '<').replace('&gt;', '>')
        return desc
    return None


def get_universe_id(pid):
    """从 icon URL 阶段已经知道 universeId, 重新获取"""
    url = f'https://apis.roblox.com/universes/v1/places/{pid}/universe'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            d = json.loads(resp.read().decode('utf-8'))
            return d.get('universeId')
    except:
        return None


def extract_game_type(name, desc):
    """从 name 或 description 提取游戏类型"""
    text = (name + ' ' + (desc or '')).lower()
    type_map = [
        (['roleplay', 'brookhaven', 'rp'], 'Roleplay'),
        (['brainrot', 'steal'], 'Steal Game'),
        (['obby', 'obstacle', 'jump', 'tower of'], 'Obby'),
        (['escape', 'run away', 'tsunami', 'evade'], 'Escape'),
        (['tower', 'defense', 'defence'], 'Tower Defense'),
        (['simulator', 'sim'], 'Simulator'),
        (['survive', 'survival'], 'Survival'),
        (['murder', 'mystery'], 'Mystery'),
        (['war', 'battle', 'fight', 'combat'], 'Battle'),
        (['tycoon'], 'Tycoon'),
        (['grow', 'garden', 'plant'], 'Garden'),
        (['adopt', 'pet'], 'Pet Sim'),
        (['parkour'], 'Parkour'),
        (['anime'], 'Anime'),
    ]
    for keywords, t in type_map:
        for k in keywords:
            if k in text:
                return t
    # 默认从 name 猜
    return ''


def shorten(desc, n=200):
    """取前 n 字符, 智能截断"""
    if not desc:
        return ''
    # 清理空白
    desc = re.sub(r'\s+', ' ', desc).strip()
    # 找第一个 \n 之前的内容
    if '\n' in desc:
        first = desc.split('\n')[0].strip()
        if len(first) > 30:
            return first[:n] + ('...' if len(first) > n else '')
    return desc[:n] + ('...' if len(desc) > n else '')


def main():
    print('=== Roblox description 抓取 ===')
    with open(RBX_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    games = data.get('games', [])

    # 只抓前 200 款 (有 icon 的)
    targets = [g for g in games if g.get('icon_url') and not g.get('description')][:200]
    print(f'目标: {len(targets)} 款游戏')

    updated = 0
    failed = 0
    for i, g in enumerate(targets):
        pid = g['placeId']
        # 1. 获取 universeId
        uid = get_universe_id(pid)
        if not uid:
            failed += 1
            continue
        # 2. 抓 description
        desc = get_description(uid)
        if not desc:
            failed += 1
            continue
        # 3. 提取 game_type
        game_type = extract_game_type(g.get('name', ''), desc)
        g['description'] = shorten(desc, 200)
        g['game_type_en'] = game_type
        updated += 1
        if (i + 1) % 20 == 0:
            print(f'  [{i+1}/{len(targets)}] 已抓: {updated}, 失败: {failed}')
        time.sleep(0.15)

    # 写回
    with open(RBX_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\n完成: 抓取 {updated} 款, 失败 {failed}')
    print(f'文件大小: {os.path.getsize(RBX_PATH)/1024:.1f} KB')

    # 抽样
    if updated > 0:
        sample = next((g for g in games if g.get('description')), None)
        if sample:
            print(f'\n=== 样例 ({sample["name"]}) ===')
            print(f'type: {sample.get("game_type_en", "")}')
            print(f'desc: {sample.get("description", "")[:150]}...')


if __name__ == '__main__':
    main()
