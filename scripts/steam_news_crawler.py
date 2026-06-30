"""
Steam新闻爬虫 - 为所有追踪的Steam游戏采集最新新闻/补丁公告
数据源：Steam ISteamNews API
输出: docs/data/steam_news.json

为每个游戏提供最新公告，可用于替换HTML中硬编码的版本更新内容
"""

import json
import os
import sys
import urllib.request
import urllib.error
import time
from datetime import datetime

# 追踪的Steam游戏及其AppID
STEAM_GAMES = {
    "R.E.P.O.": 3241660,
    "Lethal Company": 1966720,
    "Phasmophobia": 739630,
    "Content Warning": 2881650,
    "FEEDERS": 4408510,
    "NARAKA: BLADEPOINT": 1203220,
    "Dead by Daylight": 381210,
}


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


def get_game_news(appid, count=10):
    """获取单个游戏的Steam新闻"""
    data = fetch_json(
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
        f"?appid={appid}&count={count}&maxlength=300&format=json"
    )
    if not data or "appnews" not in data:
        return []
    
    items = []
    for item in data["appnews"]["newsitems"]:
        dt = datetime.fromtimestamp(item["date"])
        tags = item.get("tags", [])
        
        items.append({
            "date": dt.strftime("%Y-%m-%d"),
            "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "title": item["title"],
            "url": item["url"],
            "author": item.get("author", ""),
            "feed_label": item.get("feedlabel", ""),
            "is_patch": "patchnotes" in tags,
            "is_official": item.get("feed_type") == 1,
            "contents": item.get("contents", "")[:200],
        })
    
    return items


def crawl_steam_news():
    """批量采集所有游戏的Steam新闻"""
    results = {}
    
    for name, appid in STEAM_GAMES.items():
        print(f"[News] 采集 {name} (appid: {appid})...")
        news = get_game_news(appid, 10)
        
        patches = [n for n in news if n["is_patch"]]
        announcements = [n for n in news if not n["is_patch"]]
        
        results[name] = {
            "appid": appid,
            "all": news,
            "patches": patches,
            "announcements": announcements,
            "latest": news[0] if news else None,
            "latest_patch": patches[0] if patches else None,
            "crawled_at": datetime.now().isoformat(),
        }
        
        print(f"   {name}: {len(news)}条 (补丁{len(patches)}条)")
        time.sleep(1)
    
    return results


if __name__ == "__main__":
    data = crawl_steam_news()
    
    # 保存
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "docs", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "steam_news.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n新闻数据已保存到 {output_path}")
    
    # 摘要
    print("\n=== 最新动向摘要 ===")
    for name, info in data.items():
        latest = info.get("latest")
        latest_patch = info.get("latest_patch")
        print(f"\n{name}:")
        if latest:
            print(f"  最新: {latest['date']} - {latest['title']}")
        if latest_patch:
            print(f"  最新补丁: {latest_patch['date']} - {latest_patch['title']}")
