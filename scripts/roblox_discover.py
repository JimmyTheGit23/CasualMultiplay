"""
Roblox 新游戏发现 - 用 omni-search 搜索热门关键词，发现不在现有列表的新游戏
数据源：Roblox 官方 search-api/omni-search
输出：把新游戏追加到 docs/data/roblox_games.json
"""

import json
import urllib.request
import time
from datetime import datetime

GAMES_PATH = "docs/data/roblox_games.json"
# 覆盖主要分类 + 热门关键词
SEARCH_KEYWORDS = [
    # 分类
    'simulator', 'tycoon', 'adopt', 'obby', 'horror', 'escape',
    'tower defense', 'fight', 'roleplay', 'racing', 'music',
    'cooking', 'merge', 'puzzle', 'story', 'sports', 'flight',
    'survival', 'anime', 'brainrot', 'steal',
    # 热门通用
    'game', 'new', 'update', 'popular', 'fun', 'multiplayer',
    'adventure', 'action', 'idle', 'clicker', 'incremental',
    'pet', 'farm', 'build', 'destroy', 'battle',
]

BATCH_SIZE = 50


def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [FAIL] {url[:80]}: {e}")
        return None


def search_games(keyword):
    """omni-search 搜索关键词，返回游戏列表"""
    url = f'https://apis.roblox.com/search-api/omni-search?searchQuery={urllib.parse.quote(keyword)}&sessionId=discover_{int(time.time())}'
    d = fetch_json(url)
    if not d:
        return []
    games = []
    for r in d.get('searchResults', []):
        for c in r.get('contents', []):
            uid = c.get('universeId')
            if uid:
                games.append({
                    'universe_id': uid,
                    'name': c.get('name', ''),
                    'playerCount': c.get('playerCount', 0),
                    'totalUpVotes': c.get('totalUpVotes', 0),
                })
    return games


def fetch_universe_batch(universe_ids):
    """批量获取 universe 完整数据"""
    if not universe_ids:
        return {}
    ids_str = ",".join(str(u) for u in universe_ids)
    url = f"https://games.roblox.com/v1/games?universeIds={ids_str}"
    data = fetch_json(url)
    if not data or "data" not in data:
        return {}
    result = {}
    for g in data["data"]:
        uid = g.get("id")
        if uid:
            result[uid] = g
    return result


def get_universe_id(place_id):
    url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
    d = fetch_json(url)
    return d.get("universeId") if d and "universeId" in d else None


def main():
    print("=== Roblox 新游戏发现 ===")
    now = datetime.now().astimezone().isoformat()

    with open(GAMES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    games = data.get("games", [])
    existing_uids = {g.get("universe_id") for g in games if g.get("universe_id")}
    existing_pids = {g.get("placeId") for g in games if g.get("placeId")}
    print(f"现有 {len(games)} 款, {len(existing_uids)} 有 universe_id")

    # 阶段 1: 批量搜索所有关键词
    print(f"\n[1/3] 搜索 {len(SEARCH_KEYWORDS)} 个关键词...")
    found = {}  # uid -> info
    for i, kw in enumerate(SEARCH_KEYWORDS):
        results = search_games(kw)
        for g in results:
            uid = g['universe_id']
            if uid not in existing_uids and uid not in found:
                found[uid] = g
        if (i + 1) % 5 == 0:
            print(f"  [{i + 1}/{len(SEARCH_KEYWORDS)}] 已发现 {len(found)} 款新游戏")
        time.sleep(0.5)

    new_uids = list(found.keys())
    print(f"\n发现 {len(new_uids)} 款新游戏 (不在现有列表)")

    if not new_uids:
        print("没有新游戏, 退出")
        return

    # 阶段 2: 批量抓新游戏的完整数据
    print(f"\n[2/3] 抓 {len(new_uids)} 款新游戏完整数据...")
    new_games = []
    for i in range(0, len(new_uids), BATCH_SIZE):
        batch = new_uids[i:i + BATCH_SIZE]
        batch_data = fetch_universe_batch(batch)
        for uid, info in batch_data.items():
            search_info = found.get(uid, {})
            new_games.append({
                'universe_id': uid,
                'placeId': info.get('rootPlaceId', 0),
                'name': info.get('name', search_info.get('name', '')),
                'visits': info.get('visits', 0),
                'latest_players': info.get('playing', 0),
                'create_time': (info.get('created') or '')[:10],
                'create_year': int((info.get('created') or '0000')[:4]) if info.get('created') else None,
                'description': (info.get('description') or '')[:500],
                'categories': [],  # 新游戏无分类, 后续 classify
                'daily_players': {},
                'peak_players': info.get('playing', 0),
                'store_url': f"https://www.roblox.com/games/{info.get('rootPlaceId', '')}/",
                'icon_url': None,
            })
        time.sleep(0.5)
    print(f"  抓到 {len(new_games)} 款完整数据")

    # 阶段 3: 合并到现有 games (只保留 CCU >= MIN_CCU 的新游戏)
    MIN_CCU = 1000
    print(f"\n[3/3] 合并到 roblox_games.json (过滤 CCU >= {MIN_CCU})...")
    existing_names = {g.get('name', '').lower() for g in games}
    added = 0
    for ng in new_games:
        # 过滤低质量
        if ng.get('latest_players', 0) < MIN_CCU:
            continue
        # 去重 (按 name 或 placeId)
        if ng['placeId'] in existing_pids:
            continue
        if ng['name'].lower() in existing_names:
            continue
        games.append(ng)
        existing_pids.add(ng['placeId'])
        existing_names.add(ng['name'].lower())
        added += 1
    print(f"  新增 {added} 款 (CCU >= {MIN_CCU})")

    data['_meta']['last_discover'] = now
    data['_meta']['total_games'] = len(games)

    with open(GAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n总计 {len(games)} 款游戏")
    print(f"文件: {GAMES_PATH}")


if __name__ == "__main__":
    main()
