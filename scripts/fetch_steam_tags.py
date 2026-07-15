#!/usr/bin/env python3
"""
Fetch Steam official tags for all registry games via SteamSpy API
Output: docs/data/steam_tags.json  (appid → [tag_en, ...])
"""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
REGISTRY_PATH = os.path.join(DATA_DIR, 'game_registry.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'steam_tags.json')

CST = timezone(timedelta(hours=8))


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f'  [FAIL] {url}: {e}')
                return None


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f'  [FAIL] {url}: {e}')
                return None


def get_steam_spy_tags(appid):
    """SteamSpy API 返回 top tags,对应 Steam 官方用户标签(可能 403)"""
    url = f'https://steamspy.com/api.php?request=appdetails&appid={appid}'
    data = fetch_json(url)
    if not data:
        return []
    tags_dict = data.get('tags', {})
    sorted_tags = sorted(tags_dict.items(), key=lambda x: -int(x[1]) if str(x[1]).isdigit() else 0)
    return [t[0] for t in sorted_tags[:8]]


import http.cookiejar
import re
TAGS_RE = re.compile(r'<a[^>]*class="app_tag"[^>]*>([^<]+)</a>', re.IGNORECASE | re.DOTALL)


def fetch_html_with_cookies(url, retries=3):
    """带 cookie 的请求,用于过 Steam 年龄验证"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    # 预设年龄验证 cookie
    cj.set_cookie(http.cookiejar.Cookie(
        version=0, name='birthtime', value='347155201', port=None, port_specified=False,
        domain='.steampowered.com', domain_specified=True, domain_initial_dot=True,
        path='/', path_specified=True, secure=False, expires=2147483647, discard=False,
        comment=None, comment_url=None, rest={}, rfc2109=False
    ))
    cj.set_cookie(http.cookiejar.Cookie(
        version=0, name='lastagecheckage', value='1-0-1981', port=None, port_specified=False,
        domain='.steampowered.com', domain_specified=True, domain_initial_dot=True,
        path='/', path_specified=True, secure=False, expires=2147483647, discard=False,
        comment=None, comment_url=None, rest={}, rfc2109=False
    ))
    cj.set_cookie(http.cookiejar.Cookie(
        version=0, name='wants_mature_content', value='1', port=None, port_specified=False,
        domain='.steampowered.com', domain_specified=True, domain_initial_dot=True,
        path='/', path_specified=True, secure=False, expires=2147483647, discard=False,
        comment=None, comment_url=None, rest={}, rfc2109=False
    ))
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            })
            with opener.open(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f'  [FAIL] {url}: {e}')
                return None


def get_steam_store_tags(appid, lang='schinese'):
    """直接爬 Steam 商店页面 HTML 提取 app_tag (popular_tags),带 age gate cookie"""
    url = f'https://store.steampowered.com/app/{appid}/?l={lang}'
    html = fetch_html_with_cookies(url)
    if not html:
        return []
    # 直接匹配所有 app_tag 链接
    tags = TAGS_RE.findall(html)
    return [t.strip().replace('\t', '').replace('\n', '').replace('+', '').strip() for t in tags if t.strip()][:10]


def get_steam_tags(appid):
    """优先用 Steam 商店页面,失败回退 SteamSpy"""
    # 中文 Steam 商店页面
    tags_zh = get_steam_store_tags(appid, 'schinese')
    if tags_zh:
        # 同时取英文版用于规范化
        tags_en = get_steam_store_tags(appid, 'english')
        if not tags_en:
            tags_en = tags_zh
        return tags_en, tags_zh
    # 回退 SteamSpy
    tags_en = get_steam_spy_tags(appid)
    if tags_en:
        tags_zh = [TAG_EN_ZH.get(t, t) for t in tags_en]
        return tags_en, tags_zh
    return [], []


# Steam 官方 tag 英中映射表 (常见休闲多人游戏相关)
TAG_EN_ZH = {
    'Horror': '恐怖',
    'Co-op': '合作',
    'Co-op Campaign': '合作战役',
    'Online Co-Op': '在线合作',
    'Multiplayer': '多人',
    'PvP': '对战',
    'Online PvP': '在线对战',
    'Party': '派对',
    'Party-Based': '派对',
    'Social Deduction': '社交推理',
    'Survival': '生存',
    'Extraction': '撤离',
    'Extraction Shooter': '撤离射击',
    'Looter Shooter': '搜打撤',
    'Asymmetric Multiplayer': '非对称多人',
    'Asymmetric': '非对称',
    'Roguelike': 'Roguelike',
    'Roguelite': 'Roguelite',
    'Physics': '物理',
    'Hide and Seek': '捉迷藏',
    'Ghost': '鬼怪',
    'Ghosts': '鬼怪',
    'Paranormal': '超自然',
    'Demons': '恶魔',
    'Dark': '黑暗',
    'Dark Fantasy': '黑暗奇幻',
    'FPS': 'FPS',
    'First-Person': '第一人称',
    'Shooter': '射击',
    'Action': '动作',
    'Adventure': '冒险',
    'Indie': '独立',
    'Casual': '休闲',
    'Stealth': '潜行',
    'Strategy': '策略',
    'Tactical': '战术',
    'Team-Based': '团队',
    'Realistic': '写实',
    'Atmospheric': '氛围',
    'Psychological Horror': '心理恐怖',
    'Survival Horror': '生存恐怖',
    'Zombies': '丧尸',
    'Gore': '血腥',
    'Violent': '暴力',
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
    'Action Roguelike': '动作肉鸽',
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
    'Supernatural': '超自然',
    'Magic': '魔法',
    'Fantasy': '奇幻',
    'Sci-fi': '科幻',
    'Space': '太空',
    'Post-apocalyptic': '末日',
    'Robots': '机器人',
    'Pixel Graphics': '像素',
    'Retro': '复古',
    '2D': '2D',
    '3D': '3D',
    'Isometric': '等距',
    'Third Person': '第三人称',
    'Top-Down': '俯视',
    'Stylized': '风格化',
    'Cinematic': '电影化',
    'Great Soundtrack': '原声优秀',
    'Soundtrack': '原声',
    'Design & Illustration': '设计',
    'Animation & Modeling': '动画',
    'Game Development': '游戏开发',
    'Utilities': '工具',
}


def main():
    print('=== Steam 官方 Tag 抓取 ===')
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    result = {
        '_meta': {
            'fetched_at': datetime.now(CST).isoformat(),
            'source': 'SteamSpy API (proxy for Steam official user tags)',
            'note': 'Tags 来自 SteamSpy aggregated,等价 Steam 官方用户标签'
        },
        'games': {}
    }

    total = 0
    for g in registry.get('games', []):
        appid = g.get('appid', 0)
        if not appid or appid == 0:
            continue
        total += 1
        name = g.get('cn_name') or g.get('name', '?')
        print(f'[{total}] {name} (appid={appid})...', end=' ')
        tags_en, tags_zh_raw = get_steam_tags(appid)
        # 翻译为中文(找不到就保留英文)
        tags_zh = [TAG_EN_ZH.get(t, t) for t in tags_en]
        # 如果中文版页面直接抓到中文,优先用页面中文
        if tags_zh_raw and not all(ord(c) < 128 for c in tags_zh_raw[0]):
            tags_zh = tags_zh_raw
        result['games'][str(appid)] = {
            'appid': appid,
            'name': name,
            'tags_en': tags_en,
            'tags_zh': tags_zh,
        }
        print(f'{len(tags_en)} tags: {", ".join(tags_en[:5])}')
        time.sleep(1.5)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: {OUTPUT_PATH}')
    print(f'共 {len(result["games"])} 款游戏')

    # 统计所有出现的 tag
    all_tags_en = {}
    for appid, info in result['games'].items():
        for t in info['tags_en']:
            all_tags_en[t] = all_tags_en.get(t, 0) + 1
    print(f'\n=== Tag 出现频次 Top 20 ===')
    for t, c in sorted(all_tags_en.items(), key=lambda x: -x[1])[:20]:
        zh = TAG_EN_ZH.get(t, '?')
        print(f'  {t:30s} → {zh:10s}  ({c} 次)')


if __name__ == '__main__':
    main()
