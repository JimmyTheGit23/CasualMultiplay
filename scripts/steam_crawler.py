"""
Steam数据爬虫 - 采集恐怖撤离/合作恐怖游戏数据
数据源：Steam Store API + Steam Review API + Steam Player Count API
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime

# 追踪的Steam游戏列表
STEAM_GAMES = {
    "R.E.P.O.": 3241660,
    "Lethal Company": 1966720,
    "Phasmophobia": 739630,
    "Content Warning": 2881650,
    "FEEDERS": 4408510,
    "NARAKA: BLADEPOINT": 1203220,
}


def fetch_json(url, retries=3):
    """带重试的JSON请求"""
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


def fetch_html(url, retries=3):
    """带重试的HTML请求"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAIL] {url}: {e}")
                return None


def get_store_payload(appid, lang="schinese"):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=cn&l={lang}"
    data = fetch_json(url)
    if not data or str(appid) not in data:
        return None

    app_data = data[str(appid)]
    if not app_data.get("success"):
        return None
    return app_data["data"]



def get_steam_app_data(appid):
    """从Steam Store API获取游戏详情，同时补齐英文字段供前端切换语言"""
    zh_info = get_store_payload(appid, "schinese")
    if not zh_info:
        return None

    en_info = get_store_payload(appid, "english") or {}

    zh_price = zh_info.get("price_overview", {}).get("final_formatted", "免费")
    en_price = en_info.get("price_overview", {}).get("final_formatted", zh_price)
    if en_price == "免费":
        en_price = "Free To Play"

    return {
        "name": zh_info.get("name", ""),
        "name_en": en_info.get("name", zh_info.get("name", "")),
        "type": zh_info.get("type", ""),
        "short_description": zh_info.get("short_description", ""),
        "short_description_en": en_info.get("short_description", zh_info.get("short_description", "")),
        "header_image": zh_info.get("header_image", ""),
        "developers": zh_info.get("developers", []),
        "publishers": zh_info.get("publishers", []),
        "price": zh_price,
        "price_en": en_price,
        "release_date": zh_info.get("release_date", {}).get("date", ""),
        "release_date_en": en_info.get("release_date", {}).get("date", zh_info.get("release_date", {}).get("date", "")),
        "metacritic": zh_info.get("metacritic", {}).get("score", None),
        "recommendations": zh_info.get("recommendations", {}).get("total", 0),
        "platforms": zh_info.get("platforms", {}),
        "categories": [c["description"] for c in zh_info.get("categories", [])],
        "categories_en": [c["description"] for c in en_info.get("categories", [])] or [c["description"] for c in zh_info.get("categories", [])],
        "genres": [g["description"] for g in zh_info.get("genres", [])],
        "genres_en": [g["description"] for g in en_info.get("genres", [])] or [g["description"] for g in zh_info.get("genres", [])],
    }


def get_steam_current_players(appid):
    """从Steam社区页面获取当前在线玩家数"""
    url = f"https://store.steampowered.com/app/{appid}/"
    html = fetch_html(url)
    if not html:
        return 0

    # Steam商店页面中包含当前在线人数
    import re
    # 匹配 "当前有 X 名玩家在线" 或类似的格式
    pattern = re.compile(r'(\d[\d,]+)\s*(?:人在线|playing now|In-Game|online)', re.IGNORECASE)
    match = pattern.search(html)
    if match:
        return int(match.group(1).replace(",", ""))

    # 备用: 从SteamDB的API获取
    return 0


def get_steam_reviews(appid):
    """从Steam Review API获取评测摘要"""
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&purchase_type=all&language=schinese&review_type=all"
    data = fetch_json(url)
    summary = data.get("query_summary", {}) if data and data.get("success") else {}

    if not data or not data.get("success") or summary.get("total_reviews", 0) == 0:
        url = f"https://store.steampowered.com/appreviews/{appid}?json=1&purchase_type=all&language=all&review_type=all"
        fallback = fetch_json(url)
        fallback_summary = fallback.get("query_summary", {}) if fallback and fallback.get("success") else {}
        if fallback and fallback.get("success") and fallback_summary.get("total_reviews", 0) > 0:
            data = fallback
            summary = fallback_summary

    if not data or not data.get("success"):
        return None

    return {
        "total_reviews": summary.get("total_reviews", 0),
        "positive": summary.get("total_positive", 0),
        "negative": summary.get("total_negative", 0),
        "positive_rate": round(
            summary.get("total_positive", 0) / max(summary.get("total_reviews", 1), 1) * 100, 1
        ),
    }


def get_steamcharts_ccu(appid):
    """从SteamCharts获取当前在线人数"""
    # SteamCharts的搜索需要游戏slug，这里用另一种方式
    # 直接用Steam API的ISteamUserStats接口
    try:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
        data = fetch_json(url)
        if data and data.get("response", {}).get("result") == 1:
            return data["response"].get("player_count", 0)
    except:
        pass
    return 0


def get_steamspy_data(appid):
    """从SteamSpy获取玩家数据(备用，可能403)"""
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    data = fetch_json(url)
    if not data:
        return None

    return {
        "owners_estimate": data.get("owners", "N/A"),
        "players_2weeks": data.get("players_2weeks", 0),
        "average_2weeks": data.get("average_2weeks", 0),
        "median_2weeks": data.get("median_2weeks", 0),
        "ccu": data.get("ccu", 0),
        "positive": data.get("positive", 0),
        "negative": data.get("negative", 0),
        "positive_rate": round(
            data.get("positive", 0) / max(data.get("positive", 0) + data.get("negative", 0), 1) * 100, 1
        ),
        "tags": dict(list(data.get("tags", {}).items())[:10]),
    }


def crawl_steam():
    """主爬虫：采集所有Steam游戏数据"""
    results = {}

    for name, appid in STEAM_GAMES.items():
        print(f"[Steam] 采集 {name} (appid: {appid})...")

        store_data = get_steam_app_data(appid)
        time.sleep(1.5)

        # 当前在线人数：Steam官方API
        ccu = get_steamcharts_ccu(appid)
        time.sleep(1)

        # SteamSpy数据(已知403，仅在需要时尝试)
        spy_data = None
        if ccu > 0:
            spy_data = {"ccu": ccu}
        else:
            # CCU为0时尝试SteamSpy备用
            spy_data = get_steamspy_data(appid)
            time.sleep(1.5)
            if spy_data and spy_data.get("ccu", 0) > 0:
                ccu = spy_data["ccu"]

        review_data = get_steam_reviews(appid)
        time.sleep(1.5)

        results[name] = {
            "appid": appid,
            "store": store_data,
            "steamspy": spy_data,
            "reviews": review_data,
            "ccu": ccu,
            "crawled_at": datetime.now().isoformat(),
        }
        print(f"   {name} 完成 (在线: {ccu})")

    return results


if __name__ == "__main__":
    data = crawl_steam()
    output_path = "data/steam_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSteam数据已保存到 {output_path}")
