"""
Roblox 数据定时抓取 - 每天更新所有游戏的 CCU (playing) + visits + 游戏名 + daily_players 时序
数据源：Roblox 官方 universe API (games.roblox.com/v1/games?universeIds=...)
输出：更新 docs/data/roblox_games.json 的 latest_players + visits + name + daily_players 时序 + 统计字段
"""

import json
import urllib.request
import time
from datetime import datetime, date

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
    """批量获取 universe 数据 (CCU + visits + name)"""
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
                "name": g.get("name", ""),
                "description": g.get("description", ""),
                "updated": g.get("updated", ""),
            }
    return result


def get_universe_id(place_id):
    """placeId → universeId"""
    url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
    d = fetch_json(url)
    return d.get("universeId") if d and "universeId" in d else None


def recalc_stats(g):
    """根据 daily_players 重新计算统计字段"""
    dp = g.get("daily_players", {})
    if not dp:
        return
    entries = sorted(dp.items())
    vals = [v for _, v in entries]
    if vals:
        peak = max(vals)
        if peak > (g.get("peak_players") or 0):
            g["peak_players"] = peak
            g["peak_date"] = [d for d, v in entries if v == peak][0]
    last7 = vals[-7:] if len(vals) >= 7 else vals
    last30 = vals[-30:] if len(vals) >= 30 else vals
    g["avg_7d"] = sum(last7) // max(len(last7), 1)
    g["avg_30d"] = sum(last30) // max(len(last30), 1)
    if len(vals) >= 14:
        prev7 = vals[-14:-7]
        g["growth_7d"] = round((g["avg_7d"] - (sum(prev7) / len(prev7))) / max(sum(prev7) / len(prev7), 1) * 100, 1)
    if len(vals) >= 60:
        prev30 = vals[-60:-30]
        g["growth_30d"] = round((g["avg_30d"] - (sum(prev30) / len(prev30))) / max(sum(prev30) / len(prev30), 1) * 100, 1)
    g["active_days"] = len(vals)
    if entries:
        g["latest_date"] = entries[-1][0]


def main():
    print("=== Roblox 数据抓取 (CCU + visits + name + 时序) ===")
    now = datetime.now().astimezone().isoformat()
    today = date.today().isoformat()  # YYYY-MM-DD

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
            if (i + 1) % 50 == 0:
                print(f"  [{i + 1}/{len(need_uid)}] 已补 {done} 个, 保存中...")
                data["_meta"]["last_uid_fetch"] = datetime.now().astimezone().isoformat()
                with open(GAMES_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                time.sleep(5)
            time.sleep(0.3)
        data["_meta"]["last_uid_fetch"] = datetime.now().astimezone().isoformat()
        with open(GAMES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  完成: {done}/{len(need_uid)} 个 universe_id")
    else:
        print("\n[1/2] universe_id 已全部存在, 跳过")

    # 阶段 2: 批量抓 CCU + visits + name
    uid_to_game = {g["universe_id"]: g for g in games if g.get("universe_id")}
    uids = list(uid_to_game.keys())
    print(f"\n[2/2] 批量抓 CCU + visits + name: {len(uids)} 款")

    all_updates = 0
    name_changes = 0
    for i in range(0, len(uids), BATCH_SIZE):
        batch = uids[i:i + BATCH_SIZE]
        print(f"  [{i + 1}~{i + len(batch)}/{len(uids)}]")
        batch_data = fetch_universe_batch(batch)
        for uid, info in batch_data.items():
            g = uid_to_game.get(uid)
            if not g:
                continue
            g["latest_players"] = info["playing"]
            g["visits"] = info["visits"]
            if info["name"] and info["name"] != g.get("name"):
                print(f"  [改名] {g.get('name', '')[:30]} -> {info['name'][:30]}")
                g["name"] = info["name"]
                name_changes += 1
            if "daily_players" not in g:
                g["daily_players"] = {}
            g["daily_players"][today] = info["playing"]
            recalc_stats(g)
            all_updates += 1
        time.sleep(BATCH_DELAY)

    data["_meta"]["last_updated"] = now
    data["_meta"]["updated_games"] = all_updates

    with open(GAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n已更新 {all_updates}/{len(uids)} 款游戏")
    print(f"改名: {name_changes} 款")
    print(f"时序日期: {today}")
    print(f"文件: {GAMES_PATH}")


if __name__ == "__main__":
    main()
