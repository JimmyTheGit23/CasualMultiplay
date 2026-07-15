#!/usr/bin/env python3
"""
用 Steam 官方 tag 重写 registry 的 tags 和 tag_definitions
数据源: docs/data/steam_tags.json (fetch_steam_tags.py 产出)
"""
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
REGISTRY_PATH = os.path.join(DATA_DIR, 'game_registry.json')
TAGS_PATH = os.path.join(DATA_DIR, 'steam_tags.json')

# Steam tag 英中映射表 (补充 fetch_steam_tags.py 里的)
TAG_EN_ZH = {
    'Horror': '恐怖',
    'Co-op': '合作',
    'Co-op Campaign': '合作战役',
    'Online Co-Op': '在线合作',
    'Multiplayer': '多人',
    'PvP': '对战',
    'Online PvP': '在线对战',
    'PvE': 'PvE',
    'Party': '派对',
    'Party Game': '派对游戏',
    'Party-Based': '派对',
    'Social Deduction': '社交推理',
    'Survival': '生存',
    'Survival Horror': '生存恐怖',
    'Extraction': '撤离',
    'Extraction Shooter': '撤离射击',
    'Looter Shooter': '搜打撤',
    'Asymmetric Multiplayer': '非对称多人',
    'Asymmetric': '非对称',
    'Roguelike': 'Roguelike',
    'Roguelite': 'Roguelite',
    'Action Roguelike': '动作肉鸽',
    'Physics': '物理',
    'Hide and Seek': '捉迷藏',
    'Hidden Object': '隐藏物品',
    'Ghost': '鬼怪',
    'Ghosts': '鬼怪',
    'Paranormal': '超自然',
    'Supernatural': '超自然',
    'Demons': '恶魔',
    'Dark': '黑暗',
    'Dark Fantasy': '黑暗奇幻',
    'FPS': 'FPS',
    'First-Person': '第一人称',
    'Shooter': '射击',
    'Third-Person Shooter': '第三人称射击',
    'Third Person': '第三人称',
    'Top-Down': '俯视',
    'Top-Down Shooter': '俯视射击',
    'Twin Stick Shooter': '双摇杆射击',
    'Action': '动作',
    'Adventure': '冒险',
    'Indie': '独立',
    'Casual': '休闲',
    'Stealth': '潜行',
    'Strategy': '策略',
    'Tactical': '战术',
    'Team-Based': '团队导向',
    'Realistic': '写实',
    'Atmospheric': '氛围',
    'Psychological Horror': '心理恐怖',
    'Zombies': '丧尸',
    'Gore': '鲜血',
    'Violent': '暴力',
    'Sexual Content': '色情内容',
    'Singleplayer': '单人',
    'Early Access': '抢先体验',
    'Free to Play': '免费游玩',
    'Sandbox': '沙盒',
    'Open World': '开放世界',
    'Crafting': '制作',
    'Building': '建造',
    'Procedural Generation': '程序生成',
    'Replay Value': '重玩价值',
    'Difficult': '困难',
    'Comedy': '喜剧',
    'Funny': '搞笑',
    'Cute': '可爱',
    'Colorful': '彩色',
    'Family Friendly': '家庭友好',
    '4 Player Local': '本地4人',
    'Local Co-Op': '本地合作',
    'Local Multiplayer': '本地多人',
    'Split Screen': '分屏',
    'Cross-Platform Multiplayer': '跨平台联机',
    'MMO': 'MMO',
    'Massively Multiplayer': '大型多人',
    'Battle Royale': '吃鸡',
    'Competitive': '竞技',
    'Esports': '电竞',
    'Simulation': '模拟',
    'Sports': '体育',
    'Racing': '赛车',
    'RPG': 'RPG',
    'JRPG': 'JRPG',
    'Hack and Slash': '砍杀',
    'Dungeon Crawler': '地牢探索',
    'Loot': '掉落',
    'Inventory Management': '背包管理',
    'Perma Death': '永久死亡',
    'Choices Matter': '选择重要',
    'Story Rich': '剧情丰富',
    'Dark Humor': '黑色幽默',
    'Mystery': '悬疑',
    'Detective': '侦探',
    'Investigation': '调查',
    'Magic': '魔法',
    'Fantasy': '奇幻',
    'Sci-fi': '科幻',
    'Science Fiction': '科幻',
    'Space': '太空',
    'Post-apocalyptic': '末日',
    'Robots': '机器人',
    'Mecha': '机甲',
    'Pixel Graphics': '像素',
    'Retro': '复古',
    '2D': '2D',
    '3D': '3D',
    'Isometric': '等距',
    'Stylized': '风格化',
    'Cinematic': '电影化',
    'Great Soundtrack': '原声优秀',
    'Soundtrack': '原声',
    'Western': '西部',
    'Trains': '火车',
    'Dwarves': '矮人',
    'Capitalism': '资本主义',
    'Moddable': '可模组',
    'Exploration': '探索',
    'Metroidvania': '银河恶魔城',
    'Puzzle': '解谜',
    'VR': 'VR',
    'Virtual Reality': '虚拟现实',
    'PvPvE': 'PvPvE',
    'Player vs Environment': '玩家对战环境',
    'Player vs Player': '玩家对战',
}


def main():
    print('=== 用 Steam 官方 tag 重写 registry ===')
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        steam_tags = json.load(f)

    # 1. 更新每款游戏的 tags
    updated = 0
    for g in registry['games']:
        appid = g.get('appid', 0)
        if not appid or appid == 0:
            continue
        info = steam_tags['games'].get(str(appid))
        if not info or not info.get('tags_en'):
            continue
        # tags 用英文(Steam 官方),前端通过 tag_definitions 翻译
        g['tags'] = info['tags_en'][:8]  # 保留前 8 个 Steam 官方 tag
        updated += 1

    # 2. 重建 tag_definitions: 扫所有出现过的 tag
    tag_freq = Counter()
    tag_zh_map = {}
    for g in registry['games']:
        for t in g.get('tags', []):
            tag_freq[t] += 1

    # 对每个出现的 tag,从映射表找中文,如果找不到用 steam_tags.json 的中文版
    for appid_str, info in steam_tags['games'].items():
        for en, zh in zip(info.get('tags_en', []), info.get('tags_zh', [])):
            if en and zh:
                # 优先用映射表的翻译
                tag_zh_map[en] = TAG_EN_ZH.get(en, zh)

    # 构建 tag_definitions: 只保留出现 >=2 次的 tag,或者关键的(出现 1 次但常用)
    new_tag_defs = {}
    for tag, count in tag_freq.most_common():
        zh = tag_zh_map.get(tag, TAG_EN_ZH.get(tag, tag))
        new_tag_defs[tag] = {
            'zh': zh,
            'count': count,
            'steam_official': True,
        }

    registry['tag_definitions'] = new_tag_defs

    # 3. 写回
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f'更新 {updated} 款游戏的 tags')
    print(f'tag_definitions 共 {len(new_tag_defs)} 个 Steam 官方 tag')
    print(f'\n=== Top 20 出现频次 ===')
    for tag, count in tag_freq.most_common(20):
        zh = new_tag_defs[tag]['zh']
        print(f'  {tag:30s} → {zh:12s} ({count} 次)')

    print(f'\n=== 未翻译 tag (保留英文) ===')
    untranslated = [t for t, d in new_tag_defs.items() if d['zh'] == t]
    for t in untranslated:
        print(f'  {t}')


if __name__ == '__main__':
    main()
