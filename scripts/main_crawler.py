"""
主采集脚本 - 整合所有爬虫，生成历史数据，输出到docs/data/
"""

import json
import os
import sys
from datetime import datetime

# 确保scripts目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from steam_crawler import crawl_steam
from chaoziran_crawler import crawl_chaoziran, enrich_chaoziran_bilingual
from dbd_crawler import crawl_dbd
from steam_news_crawler import crawl_steam_news
from chaoziran_overseas_crawler import crawl_overseas


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_history(steam_data, history_path):
    """将当日数据追加到历史记录（用于趋势图）"""
    history = load_json(history_path)
    today = datetime.now().strftime("%Y-%m-%d")

    for name, data in steam_data.items():
        if name not in history:
            history[name] = []

        spy = data.get("steamspy") or {}
        reviews = data.get("reviews") or {}

        entry = {
            "date": today,
            "ccu": spy.get("ccu", data.get("ccu", 0)),
            "positive_rate": reviews.get("positive_rate", spy.get("positive_rate", 0)),
            "total_reviews": reviews.get("total_reviews", spy.get("positive", 0) + spy.get("negative", 0)),
        }

        # 避免同一天重复追加
        if history[name] and history[name][-1]["date"] == today:
            history[name][-1] = entry
        else:
            history[name].append(entry)

        # 保留最近30天
        history[name] = history[name][-30:]

    save_json(history, history_path)
    return history


def merge_chaoziran_data(new_data, old_data):
    """增量合并超自然行动组数据：新采集数据为空时保留旧数据"""
    if not old_data or "chaoziran" not in old_data:
        return new_data
    if "chaoziran" not in new_data:
        return new_data

    new_czr = new_data["chaoziran"]
    old_czr = old_data["chaoziran"]

    # 需要增量合并的字段：如果新数据为空，保留旧数据
    merge_fields = ["official_news", "bwiki_updates"]
    for field in merge_fields:
        new_items = new_czr.get(field, [])
        old_items = old_czr.get(field, [])
        if len(new_items) == 0 and len(old_items) > 0:
            new_czr[field] = old_items
            print(f"   [MERGE] {field}: 新采集为空，保留旧数据({len(old_items)}条)")
        elif len(new_items) > 0:
            print(f"   [MERGE] {field}: 新数据({len(new_items)}条)")

    # 社区数据也类似处理
    for sub_field in ["taptap_forum"]:
        new_community = new_czr.get("community", {})
        old_community = old_czr.get("community", {})
        new_items = new_community.get(sub_field, [])
        old_items = old_community.get(sub_field, [])
        if len(new_items) == 0 and len(old_items) > 0:
            if "community" not in new_czr:
                new_czr["community"] = {}
            new_czr["community"][sub_field] = old_items
            print(f"   [MERGE] community.{sub_field}: 新采集为空，保留旧数据({len(old_items)}条)")

    return new_data


def main():
    print("=" * 50)
    print(f"GRC恐怖多人品类情报 - 数据采集开始 {datetime.now().isoformat()}")
    print("=" * 50)

    # 1. 采集Steam数据
    print("\n[1/5] 采集Steam数据...")
    try:
        steam_data = crawl_steam()
        save_json(steam_data, os.path.join(DATA_DIR, "steam_data.json"))
        print("   Steam数据采集完成")
    except Exception as e:
        print(f"   Steam数据采集失败: {e}")
        steam_data = {}

    # 2. 采集超自然行动组数据
    print("\n[2/6] 采集超自然行动组数据...")
    try:
        czr_data = crawl_chaoziran()
        # 增量合并：新数据为空时保留旧数据
        czr_path = os.path.join(DATA_DIR, "chaoziran_data.json")
        old_czr_data = load_json(czr_path)
        czr_data = merge_chaoziran_data(czr_data, old_czr_data)
        czr_data = enrich_chaoziran_bilingual(czr_data)
        # 采集海外数据并合并
        try:
            overseas_data = crawl_overseas()
            if czr_data.get("chaoziran"):
                czr_data["chaoziran"]["overseas"] = overseas_data
            # 同时保存独立文件
            save_json(overseas_data, os.path.join(DATA_DIR, "chaoziran_overseas.json"))
            print("   海外数据已合并到超自然行动组数据")
        except Exception as e:
            print(f"   海外数据采集失败（非致命）: {e}")
        save_json(czr_data, czr_path)
        print("   超自然行动组数据采集完成")
    except Exception as e:
        print(f"   超自然行动组数据采集失败: {e}")
        czr_data = {}

    # 3. 采集DBD数据
    print("\n[3/6] 采集DBD数据...")
    try:
        dbd_data = crawl_dbd()
        save_json(dbd_data, os.path.join(DATA_DIR, "dbd_data.json"))
        print("   DBD数据采集完成")
    except Exception as e:
        print(f"   DBD数据采集失败: {e}")

    # 4. 采集Steam新闻
    print("\n[4/6] 采集Steam新闻...")
    try:
        news_data = crawl_steam_news()
        save_json(news_data, os.path.join(DATA_DIR, "steam_news.json"))
        print(f"   Steam新闻采集完成（{len(news_data)}个游戏）")
    except Exception as e:
        print(f"   Steam新闻采集失败: {e}")

    # 5. 更新历史数据
    print("\n[5/6] 更新历史数据...")
    history_path = os.path.join(DATA_DIR, "history.json")
    history = update_history(steam_data, history_path)
    print(f"   历史数据已更新（{len(history)}个游戏）")

    # 6. 内联数据更新（将JSON数据写入HTML的inline变量）
    print("\n[6/6] 更新HTML内联数据...")
    try:
        inline_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "inline_data.py")
        if os.path.exists(inline_script):
            import importlib.util
            spec = importlib.util.spec_from_file_location("inline_data", inline_script)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "update_inline_data"):
                html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "index.html")
                mod.update_inline_data(html_path)
                print("   HTML内联数据已更新")
    except Exception as e:
        print(f"   HTML内联数据更新失败（非致命）: {e}")

    # 6. 输出摘要
    print("\n" + "=" * 50)
    print("采集摘要:")
    print("-" * 30)

    for name, data in steam_data.items():
        spy = data.get("steamspy") or {}
        reviews = data.get("reviews") or {}
        ccu = spy.get("ccu", "?")
        rate = reviews.get("positive_rate", spy.get("positive_rate", "?"))
        print(f"  {name}: 在线{ccu} | 好评率{rate}%")

    if czr_data.get("chaoziran"):
        czr = czr_data["chaoziran"]
        updates_count = len(czr.get("bwiki_updates", []))
        news_count = len(czr.get("official_news", []))
        print(f"  超自然行动组: 更新公告{updates_count}条 | 官网新闻{news_count}条")

    print("=" * 50)
    print(f"采集完成 {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
