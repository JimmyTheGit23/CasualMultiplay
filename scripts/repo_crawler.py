"""
R.E.P.O. 数据爬虫 - 采集 R.E.P.O. 的 Steam 数据 + 最新动向
数据源：Steam Store API + Review API + Player Count API + News API
输出: docs/data/repo_data.json

与 dbd_crawler.py 结构一致，便于 renderRepo() 复用
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime

REPO_APPID = 3241660
OUTPUT_PATH = "docs/data/repo_data.json"


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAIL] {url}: {e}")
                return None


def get_store():
    """获取 Steam 商店信息（中英文）"""
    zh_data = fetch_json(f"https://store.steampowered.com/api/appdetails?appids={REPO_APPID}&cc=cn&l=schinese")
    en_data = fetch_json(f"https://store.steampowered.com/api/appdetails?appids={REPO_APPID}&cc=us&l=english")

    zh_info = zh_data.get(str(REPO_APPID), {}).get("data", {}) if zh_data and zh_data.get(str(REPO_APPID), {}).get("success") else {}
    en_info = en_data.get(str(REPO_APPID), {}).get("data", {}) if en_data and en_data.get(str(REPO_APPID), {}).get("success") else {}

    zh_price = zh_info.get("price_overview", {}).get("final_formatted", "")
    en_price = en_info.get("price_overview", {}).get("final_formatted", zh_price)

    return {
        "name": zh_info.get("name", "R.E.P.O."),
        "name_en": en_info.get("name", "R.E.P.O."),
        "short_description": zh_info.get("short_description", ""),
        "short_description_en": en_info.get("short_description", ""),
        "header_image": zh_info.get("header_image", ""),
        "developers": zh_info.get("developers", ["semiwork"]),
        "publishers": zh_info.get("publishers", ["semiwork"]),
        "price": zh_price,
        "price_en": en_price,
        "release_date": zh_info.get("release_date", {}).get("date", ""),
        "platforms": zh_info.get("platforms", {}),
        "genres": [g["description"] for g in zh_info.get("genres", [])],
        "is_free": zh_info.get("is_free", False),
    }


def get_reviews():
    """获取评测摘要"""
    data = fetch_json(f"https://store.steampowered.com/appreviews/{REPO_APPID}?json=1&purchase_type=all&language=all&review_type=all")
    if not data or not data.get("success"):
        return None

    summary = data.get("query_summary", {})
    total = summary.get("total_reviews", 0)
    positive = summary.get("total_positive", 0)
    review_score_label = summary.get("review_score_desc", "")
    return {
        "total_reviews": total,
        "positive": positive,
        "negative": total - positive,
        "positive_rate": round(positive / max(total, 1) * 100, 1),
        "review_score_desc": review_score_label,
    }


def get_ccu():
    """获取当前在线人数"""
    data = fetch_json(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={REPO_APPID}")
    if data and data.get("response", {}).get("result") == 1:
        return data["response"].get("player_count", 0)
    return 0


def get_news(count=15):
    """获取最新 Steam 新闻/补丁公告"""
    data = fetch_json(
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        f"?appid={REPO_APPID}&count={count}&maxlength=400&format=json"
    )
    if not data or "appnews" not in data:
        return []

    items = []
    for item in data["appnews"]["newsitems"]:
        dt = datetime.fromtimestamp(item["date"])
        feed_type = "官方" if item.get("feed_type") == 1 else "媒体"
        tags = item.get("tags", [])
        # 自动分类
        title = item.get("title", "")
        title_lower = title.lower()
        if any(k in title_lower for k in ["patch", "update", "v0.", "v1.", "hotfix", "fix"]):
            cat_zh, cat_en = "版本更新", "Patch"
        elif any(k in title_lower for k in ["event", "holiday", "halloween", "christmas", "anniversary"]):
            cat_zh, cat_en = "活动", "Event"
        elif any(k in title_lower for k in ["dlc", "pack", "bundle", "skin", "cosmetic"]):
            cat_zh, cat_en = "DLC/皮肤", "DLC/Skin"
        elif any(k in title_lower for k in ["collab", "crossover", "license"]):
            cat_zh, cat_en = "联动", "Collab"
        else:
            cat_zh, cat_en = "公告", "Announcement"

        items.append({
            "date": dt.strftime("%Y-%m-%d"),
            "timestamp": item["date"],
            "title": title,
            "url": item.get("url", ""),
            "source": feed_type,
            "type_zh": cat_zh,
            "type_en": cat_en,
            "contents": (item.get("contents", "") or "")[:300],
        })
    return items


def get_patches(operations):
    """从 operations 里提取 patch 类"""
    return [op for op in operations if op.get("type_zh") == "版本更新"]


def get_trends():
    """获取近期玩家趋势（从 ccu_history 抓最近 6 个月）"""
    try:
        with open("docs/data/ccu_history.json", "r", encoding="utf-8") as f:
            hist = json.load(f)
        entries = hist.get("data", {}).get(str(REPO_APPID), [])
        if not entries:
            return []
        # 按月聚合
        monthly = {}
        for e in entries:
            d = e.get("date", "")
            if len(d) >= 7:
                month = d[:7]
                if month not in monthly:
                    monthly[month] = []
                monthly[month].append(e.get("ccu", 0))
        trends = []
        for month in sorted(monthly.keys())[-6:]:
            vals = monthly[month]
            trends.append({
                "month": month,
                "avg_players": sum(vals) // max(len(vals), 1),
                "peak": max(vals),
            })
        return trends
    except Exception as e:
        print(f"  [WARN] ccu_history 读取失败: {e}")
        return []


def main():
    print("=== R.E.P.O. 数据抓取 ===")
    now = datetime.now().astimezone().isoformat()

    print("[1/5] Steam Store...")
    store = get_store()
    time.sleep(0.5)

    print("[2/5] Reviews...")
    reviews = get_reviews()
    time.sleep(0.5)

    print("[3/5] CCU...")
    ccu = get_ccu()
    time.sleep(0.5)

    print("[4/5] News...")
    news = get_news(count=15)
    operations = news
    patches = get_patches(operations)
    time.sleep(0.5)

    print("[5/5] Trends (from ccu_history)...")
    trends = get_trends()

    hero = {
        "title": store.get("name", "R.E.P.O."),
        "title_en": store.get("name_en", "R.E.P.O."),
        "subtitle_zh": " · ".join([
            ", ".join(store.get("developers", ["semiwork"])),
            "在线合作恐怖",
            store.get("release_date", ""),
        ]),
        "subtitle_en": " · ".join([
            ", ".join(store.get("developers", ["semiwork"])),
            "Online Co-op Horror",
            store.get("release_date", ""),
        ]),
        "header_image": store.get("header_image", ""),
    }

    data = {
        "snapshot_date": now,
        "hero": hero,
        "operations": operations,
        "patches": patches,
        "trends": trends,
        "store": store,
        "reviews": reviews,
        "ccu": ccu,
        "crawled_at": now,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n已保存到 {OUTPUT_PATH}")
    print(f"  CCU: {ccu:,}")
    print(f"  Reviews: {reviews.get('total_reviews', 0):,} ({reviews.get('positive_rate', 0)}%)" if reviews else "  Reviews: N/A")
    print(f"  News: {len(news)}")
    print(f"  Patches: {len(patches)}")
    print(f"  Trends: {len(trends)} months")


if __name__ == "__main__":
    main()
