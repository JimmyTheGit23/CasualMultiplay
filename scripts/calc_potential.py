#!/usr/bin/env python3
"""
潜力分计算引擎
基于 CCU 增速、好评率、wishlist、标签新颖度算 0-100 潜力分
输出: docs/data/potential_scores.json

评分维度:
- CCU 周增速 (30%): 需 7 天以上历史数据
- 好评率 (20%): Steam 评测好评率
- wishlist 周增速 (30%): 需 7 天以上历史数据,从 registry 的 wishlist_count
- 标签新颖度 (20%): 标签组合的稀有度评分

积累 7 天后才能算周增速。不足 7 天用默认值。
"""
import json
import os
import math
from datetime import datetime, timezone, timedelta
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
REGISTRY_PATH = os.path.join(DATA_DIR, 'game_registry.json')
HISTORY_PATH = os.path.join(DATA_DIR, 'ccu_history.json')
STEAM_DATA_PATH = os.path.join(DATA_DIR, 'steam_data.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'potential_scores.json')

CST = timezone(timedelta(hours=8))


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calc_ccu_growth(history_data, appid):
    """计算 CCU 7 天增速"""
    entries = history_data.get('data', {}).get(str(appid), [])
    if len(entries) < 2:
        return 0.0  # 数据不足,增速为0
    
    # 找 7 天前和今天的
    today_ccu = entries[-1].get('ccu', 0)
    
    # 找 7 天前的数据
    if len(entries) >= 8:
        week_ago_ccu = entries[-8].get('ccu', 0)
    else:
        week_ago_ccu = entries[0].get('ccu', 0)
    
    if week_ago_ccu == 0:
        # 从 0 增长,如果现在有 CCU 就是正增长
        return 100.0 if today_ccu > 0 else 0.0
    
    growth = (today_ccu - week_ago_ccu) / week_ago_ccu * 100
    # 限制在 -100 到 200 之间
    return max(-100, min(200, growth))


def calc_wishlist_growth(registry_game):
    """计算 wishlist 增速 (暂时用 wishlist 数量评分,需要历史快照后改为增速)"""
    wl = registry_game.get('wishlist_count', 0)
    if wl == 0:
        return 0.0
    # 对数缩放: 100 → 20, 1000 → 40, 10000 → 60, 100000 → 80, 600000 → 95
    if wl < 100:
        return 10.0
    score = math.log10(wl) * 20 - 20
    return max(0, min(100, score))


def calc_positive_rate(steam_data, steam_key):
    """从 steam_data 提取好评率"""
    if not steam_key or steam_key not in steam_data:
        return 0.0
    data = steam_data[steam_key]
    if data.get('steamspy'):
        pos = data['steamspy'].get('positive', 0)
        neg = data['steamspy'].get('negative', 0)
        total = pos + neg
        if total > 0:
            return (pos / total) * 100
    if data.get('store') and data['store'].get('review_score'):
        # review_score 是 -1 到 1 的 Steam 内部分数
        return max(0, (data['store']['review_score'] + 1) * 50)
    return 0.0


def calc_tag_novelty(registry_game, all_games, tag_defs):
    """计算标签组合新颖度: 该组合在所有游戏中出现的稀有度"""
    tags = registry_game.get('tags', [])
    if not tags:
        return 0.0
    
    # 统计每个标签出现频率
    tag_freq = Counter()
    for g in all_games:
        for t in g.get('tags', []):
            tag_freq[t] += 1
    
    total_games = len(all_games)
    if total_games == 0:
        return 0.0
    
    # 该游戏标签组合的平均出现频率 (越低越新颖)
    avg_freq = sum(tag_freq.get(t, 0) for t in tags) / len(tags)
    novelty = (1 - avg_freq / total_games) * 100
    
    # 标签数量奖励: 标签越多,组合越独特
    tag_count_bonus = min(20, len(tags) * 5)
    
    return max(0, min(100, novelty * 0.7 + tag_count_bonus * 0.3))


def calc_potential_score(game, steam_data, history_data, all_games, tag_defs):
    """计算 0-100 潜力分"""
    appid = game.get('appid', 0)
    steam_key = game.get('steam_key')
    
    # CCU 周增速 (0-100, 权重 30%)
    ccu_growth = calc_ccu_growth(history_data, appid)
    ccu_score = max(0, min(100, (ccu_growth + 100) / 3))  # -100→0, 100→66, 200→100
    
    # 好评率 (0-100, 权重 20%)
    positive = calc_positive_rate(steam_data, steam_key)
    
    # wishlist 增速/规模 (0-100, 权重 30%)
    wl_score = calc_wishlist_growth(game)
    
    # 标签新颖度 (0-100, 权重 20%)
    novelty = calc_tag_novelty(game, all_games, tag_defs)
    
    # 综合分
    total = ccu_score * 0.3 + positive * 0.2 + wl_score * 0.3 + novelty * 0.2
    
    return {
        'appid': appid,
        'name': game.get('cn_name') or game.get('name', ''),
        'score': round(total, 1),
        'breakdown': {
            'ccu_growth_pct': round(ccu_growth, 1),
            'ccu_score': round(ccu_score, 1),
            'positive_pct': round(positive, 1),
            'positive_score': round(positive, 1),
            'wishlist_score': round(wl_score, 1),
            'tag_novelty': round(novelty, 1)
        },
        'is_ea': game.get('status') == 'EA',
        'status': game.get('status', ''),
        'priority': game.get('priority', 'P2'),
        'tags': game.get('tags', []),
        'note': '潜力分基于有限数据(历史<7天),CCU增速暂为0。积累7天后增速生效。' if len(history_data.get('data', {}).get(str(appid), [])) < 7 else ''
    }


def main():
    print('=== 潜力分计算 ===')
    
    registry = load_json(REGISTRY_PATH)
    history = load_json(HISTORY_PATH)
    steam_data = load_json(STEAM_DATA_PATH)
    
    if not registry or 'games' not in registry:
        print('[ERROR] registry not loaded')
        return
    
    all_games = registry['games']
    tag_defs = registry.get('tag_definitions', {})
    
    results = []
    for game in all_games:
        score = calc_potential_score(game, steam_data, history, all_games, tag_defs)
        results.append(score)
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    output = {
        '_meta': {
            'calculated_at': datetime.now(CST).isoformat(),
            'total_games': len(results),
            'note': '潜力分 0-100, 综合CCU增速/好评率/wishlist/标签新颖度。积累7天后CCU增速生效。'
        },
        'scores': results
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n已保存到 {OUTPUT_PATH}')
    print(f'\n=== 潜力分 Top 15 ===')
    for i, s in enumerate(results[:15]):
        b = s['breakdown']
        print(f'{i+1:2d}. {s["name"]:25s} | 分: {s["score"]:5.1f} | CCU增速: {b["ccu_growth_pct"]:6.1f}% | 好评: {b["positive_pct"]:5.1f}% | WL分: {b["wishlist_score"]:5.1f} | 新颖: {b["tag_novelty"]:5.1f} | {s["status"]}')


if __name__ == '__main__':
    main()
