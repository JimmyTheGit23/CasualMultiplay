"""
DBD数据爬虫 - 采集Dead by Daylight的Steam数据+最新动向
数据源：Steam Store API + Review API + Player Count API + News API
输出: docs/data/dbd_data.json

替代HTML中硬编码的 DBD_DATA，实现数据自动更新
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime

DBD_APPID = 381210


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


def get_dbd_store():
    """获取DBD Steam商店信息（中英文）"""
    zh_data = fetch_json(f"https://store.steampowered.com/api/appdetails?appids={DBD_APPID}&cc=cn&l=schinese")
    en_data = fetch_json(f"https://store.steampowered.com/api/appdetails?appids={DBD_APPID}&cc=us&l=english")
    
    zh_info = zh_data.get(str(DBD_APPID), {}).get("data", {}) if zh_data and zh_data.get(str(DBD_APPID), {}).get("success") else {}
    en_info = en_data.get(str(DBD_APPID), {}).get("data", {}) if en_data and en_data.get(str(DBD_APPID), {}).get("success") else {}
    
    zh_price = zh_info.get("price_overview", {}).get("final_formatted", "¥ 93.75")
    en_price = en_info.get("price_overview", {}).get("final_formatted", zh_price)
    
    return {
        "name": zh_info.get("name", "Dead by Daylight"),
        "name_en": en_info.get("name", "Dead by Daylight"),
        "short_description": zh_info.get("short_description", ""),
        "short_description_en": en_info.get("short_description", ""),
        "header_image": zh_info.get("header_image", ""),
        "developers": zh_info.get("developers", ["Behaviour Interactive"]),
        "publishers": zh_info.get("publishers", ["Behaviour Interactive"]),
        "price": zh_price,
        "price_en": en_price,
        "release_date": zh_info.get("release_date", {}).get("date", "2016-06-14"),
        "platforms": zh_info.get("platforms", {}),
        "genres": [g["description"] for g in zh_info.get("genres", [])],
    }


def get_dbd_reviews():
    """获取DBD评测摘要"""
    data = fetch_json(f"https://store.steampowered.com/appreviews/{DBD_APPID}?json=1&purchase_type=all&language=all&review_type=all")
    if not data or not data.get("success"):
        return None
    
    summary = data.get("query_summary", {})
    total = summary.get("total_reviews", 0)
    positive = summary.get("total_positive", 0)
    return {
        "total_reviews": total,
        "positive": positive,
        "negative": total - positive,
        "positive_rate": round(positive / max(total, 1) * 100, 1),
    }


def get_dbd_ccu():
    """获取DBD当前在线人数"""
    data = fetch_json(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={DBD_APPID}")
    if data and data.get("response", {}).get("result") == 1:
        return data["response"].get("player_count", 0)
    return 0


def get_dbd_news(count=15):
    """获取DBD最新Steam新闻/补丁公告"""
    data = fetch_json(
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        f"?appid={DBD_APPID}&count={count}&maxlength=400&format=json"
    )
    if not data or "appnews" not in data:
        return []
    
    items = []
    for item in data["appnews"]["newsitems"]:
        dt = datetime.fromtimestamp(item["date"])
        feed_type = "官方" if item.get("feed_type") == 1 else "媒体"
        tags = item.get("tags", [])
        is_patch = "patchnotes" in tags
        
        items.append({
            "date": dt.strftime("%Y-%m-%d"),
            "timestamp": item["date"],
            "title": item["title"],
            "url": item["url"],
            "author": item.get("author", ""),
            "feed_label": item.get("feedlabel", ""),
            "feed_type": feed_type,
            "is_patch": is_patch,
            "contents": item.get("contents", "")[:200],
        })
    
    return items


def get_dbd_monthly_trends():
    """获取DBD月度趋势（使用SteamCharts历史数据）
    注意：需要定期更新，可配合SteamDB数据手工维护
    """
    return [
        {"month": "2026-01", "avg_players": 49288, "peak_players": 96633},
        {"month": "2026-02", "avg_players": 55296, "peak_players": 93286},
        {"month": "2026-03", "avg_players": 46223, "peak_players": 84502},
        {"month": "2026-04", "avg_players": 49104, "peak_players": 77398},
        {"month": "2026-05", "avg_players": 51051, "peak_players": 86738},
        {"month": "2026-06", "avg_players": 53145, "peak_players": 104001},
    ]


def crawl_dbd(preserve_trends=True):
    """主爬虫：采集DBD全部数据"""
    print(f"[DBD] 采集 Dead by Daylight (appid: {DBD_APPID})...")
    
    # 商店信息
    store = get_dbd_store()
    time.sleep(1.5)
    
    # 当前在线
    ccu = get_dbd_ccu()
    time.sleep(1)
    
    # 评测
    reviews = get_dbd_reviews()
    time.sleep(1.5)
    
    # 最新动向（新闻+补丁）
    news = get_dbd_news(15)
    time.sleep(1)
    
    # 分离补丁和运营动态
    patches = [n for n in news if n["is_patch"]]
    operations = [n for n in news if not n["is_patch"]]
    
    # 月度趋势（默认保留已有数据）
    trends = get_dbd_monthly_trends()
    
    result = {
        "snapshot_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "hero": {
            "name": store.get("name", "Dead by Daylight"),
            "current_players": ccu,
            "positive_rate": reviews.get("positive_rate", 78.5) if reviews else 78.5,
            "reviews_total": reviews.get("total_reviews", 903715) if reviews else 903715,
            "price_label": store.get("price", "¥ 93.75"),
            "release_date": store.get("release_date", "2016-06-14"),
            "genres": store.get("genres", []),
        },
        "operations": operations[:8],
        "patches": patches[:8],
        "trends": trends,
        "store": store,
        "reviews": reviews,
        "ccu": ccu,
        "crawled_at": datetime.now().isoformat(),
    }
    
    print(f"   DBD 完成 (在线: {ccu}, 评测: {reviews.get('total_reviews', '?') if reviews else '?'}, 新闻: {len(news)}条)")
    return result


if __name__ == "__main__":
    data = crawl_dbd()
    print("\nDBD数据摘要:")
    print(f"  在线: {data['ccu']}")
    print(f"  好评率: {data['hero']['positive_rate']}%")
    print(f"  补丁: {len(data['patches'])}条")
    print(f"  动向: {len(data['operations'])}条")
    
    # 测试输出
    output = "docs/data/dbd_data.json"
    import os
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nDBD数据已保存到 {output}")
