"""
Roblox 数据定时抓取 - 每天更新所有游戏的 CCU (playing) 和 visits
数据源：Roblox 官方 universe API (games.roblox.com/v1/games?universeIds=...)
输出：更新 docs/data/roblox_games.json 的 latest_players + visits
"""

import json
import urllib.request
import time
from datetime import datetime

GAMES_PATH = "docs/data/roblox_games.json"
BATCH_SIZE = 50  # Roblox games API batch 限制 50
BATCH_DELAY = 0.5


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


def fetch_universe_batch(universe_ids):
    """批量获取 universe 数据 (CCU + visits)"""
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
            result[uid] = {
                "playing": g.get("playing", 0),
                "visits": g.get("visits", 0),
                "favoritedCount": g.get("favoritedCount", 0),
            }
    return result


def get_universe_id(place_id):
    """placeId → universeId"""
    url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
    d = fetch_json(url)
    return d.get("universeId") if d and "universeId" in d else None


def main():
    print("=== Roblox 数据抓取 (CCU + visits) ===")
    now = datetime.now().astimezone().isoformat()

    with open(GAMES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    games = data.get("games", [])
    print(f"共 {len(games)} 款游戏")

    # 阶段 1: 给没有 universe_id 的游戏补 universe_id
    need_uid = [g for g in games if not g.get("universe_id")]
    if need_uid:
        print(f"\n[1/2] 补 universe_id: {len(need_uid)} 款")
        done = 0
        for i, g in enumerate(need_uid):
            try:
                uid = get_universe_id(g["placeId"])
                if uid:
                    g["universe_id"] = uid
                    done += 1
            except Exception as e:
                print(f"  [SKIP] {g['name'][:30]}: {e}")
            # 每 50 个保存 + 等 5s 防限流
            if (i + 1) % 50 == 0:
                print(f"  [{i + 1}/{len(need_uid)}] 已补 {done} 个, 保存中...")
                data["_meta"]["last_uid_fetch"] = datetime.now().astimezone().isoformat()
                with open(GAMES_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                time.sleep(5)
            time.sleep(0.3)
        # 最后保存
        data["_meta"]["last_uid_fetch"] = datetime.now().astimezone().isoformat()
        with open(GAMES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  完成: {done}/{len(need_uid)} 个 universe_id")
    else:
        print("\n[1/2] universe_id 已全部存在, 跳过")

    # 阶段 2: 批量抓 CCU + visits
    uid_to_game = {g["universe_id"]: g for g in games if g.get("universe_id")}
    uids = list(uid_to_game.keys())
    print(f"\n[2/2] 批量抓 CCU + visits: {len(uids)} 款")

    all_updates = 0
    for i in range(0, len(uids), BATCH_SIZE):
        batch = uids[i:i + BATCH_SIZE]
        print(f"  [{i + 1}~{i + len(batch)}/{len(uids)}]")
        batch_data = fetch_universe_batch(batch)
        for uid, info in batch_data.items():
            g = uid_to_game.get(uid)
            if g:
                g["latest_players"] = info["playing"]
                g["visits"] = info["visits"]
                all_updates += 1
        time.sleep(BATCH_DELAY)

    # 更新时间戳
    data["_meta"]["last_updated"] = now
    data["_meta"]["updated_games"] = all_updates

    with open(GAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n已更新 {all_updates}/{len(uids)} 款游戏")
    print(f"文件: {GAMES_PATH}")


if __name__ == "__main__":
    main()
