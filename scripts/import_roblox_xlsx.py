#!/usr/bin/env python3
"""
Roblox xlsx 数据导入
输入: roblox_leaderboard_pivot_full.xlsx (796 款游戏, 129 天玩家数时序)
输出: docs/data/roblox_games.json
"""
import json
import os
import pandas as pd
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
OUTPUT_PATH = os.path.join(DATA_DIR, 'roblox_games.json')

# 默认输入路径(可被 argv[1] 覆盖)
DEFAULT_XLSX = r'C:\Users\alucardzhou\xwechat_files\poorjimmy_144d\msg\file\2026-07\roblox_leaderboard_pivot_full.xlsx'

CST = timezone(timedelta(hours=8))

# 自动分类关键词
CATEGORIES = [
    {'key': 'Brainrot', 'zh': '脑腐', 'keywords': ['Brainrot']},
    {'key': 'Tower', 'zh': '塔防', 'keywords': ['Tower', 'Defence', 'Defense']},
    {'key': 'Escape', 'zh': '逃脱', 'keywords': ['Escape']},
    {'key': 'Anime', 'zh': '动漫', 'keywords': ['Anime']},
    {'key': 'RP', 'zh': '角色扮演', 'keywords': ['RP', 'Roleplay']},
    {'key': 'Simulator', 'zh': '模拟', 'keywords': ['Simulator', ' Sim']},
    {'key': 'War', 'zh': '战争', 'keywords': ['War']},
    {'key': 'Obby', 'zh': '跑酷', 'keywords': ['Obby']},
    {'key': 'Tycoon', 'zh': '大亨', 'keywords': ['Tycoon']},
    {'key': 'Fight', 'zh': '格斗', 'keywords': ['Fight', 'Battles', 'Battle']},
    {'key': 'Murder', 'zh': '推理', 'keywords': ['Murder']},
    {'key': 'Survival', 'zh': '生存', 'keywords': ['Survival']},
    {'key': 'Parkour', 'zh': '跑酷', 'keywords': ['Parkour']},
    {'key': 'Adopt', 'zh': '养成', 'keywords': ['Adopt']},
    {'key': 'Pets', 'zh': '宠物', 'keywords': ['Pet', 'Pets']},
    {'key': 'Grow', 'zh': '种植', 'keywords': ['Grow', 'Garden']},
]


def classify_game(name):
    """根据游戏名匹配分类,可能多个"""
    cats = []
    for c in CATEGORIES:
        for kw in c['keywords']:
            if kw.lower() in name.lower():
                cats.append(c['key'])
                break
    return cats


def parse_create_time(s):
    """解析创建时间,返回 (date_str, year)"""
    s = str(s).strip()
    if not s or s == 'Unknown' or s == 'NaT':
        return '', None
    # 尝试多种格式
    for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d'), dt.year
        except ValueError:
            continue
    # 尝试 pandas
    try:
        dt = pd.to_datetime(s)
        if pd.isna(dt):
            return '', None
        return dt.strftime('%Y-%m-%d'), dt.year
    except Exception:
        return '', None


def date_col_to_date(col):
    """20260227 → 2026-02-27"""
    s = str(col)
    if len(s) == 8 and s.isdigit():
        return f'{s[:4]}-{s[4:6]}-{s[6:8]}'
    return s


def compute_derived(daily_players_dict):
    """计算派生指标"""
    if not daily_players_dict:
        return {
            'latest_players': 0, 'latest_date': '',
            'avg_7d': 0, 'avg_30d': 0,
            'growth_7d': 0.0, 'growth_30d': 0.0,
            'active_days': 0, 'peak_date': ''
        }
    # 按日期排序
    sorted_items = sorted(daily_players_dict.items())
    dates = [d for d, _ in sorted_items]
    values = [v for _, v in sorted_items]
    # 最近有数据的
    latest_date = dates[-1]
    latest_players = values[-1]
    # 平均: 最近 7/30 天有数据的
    last_7 = [v for v in values[-7:] if v is not None and v > 0]
    last_30 = [v for v in values[-30:] if v is not None and v > 0]
    avg_7d = sum(last_7) / len(last_7) if last_7 else 0
    avg_30d = sum(last_30) / len(last_30) if last_30 else 0
    # 增长率: 用 7 天前/30 天前的值对比
    growth_7d = 0.0
    if len(values) >= 8:
        v_7ago = values[-8]
        if v_7ago and v_7ago > 0:
            growth_7d = round((latest_players - v_7ago) / v_7ago * 100, 1)
    growth_30d = 0.0
    if len(values) >= 31:
        v_30ago = values[-31]
        if v_30ago and v_30ago > 0:
            growth_30d = round((latest_players - v_30ago) / v_30ago * 100, 1)
    # 活跃天数
    active_days = sum(1 for v in values if v is not None and v > 0)
    # 峰值日期: daily_players 里的最大值
    peak_date = ''
    peak_val = 0
    for d, v in daily_players_dict.items():
        if v and v > peak_val:
            peak_val = v
            peak_date = d
    return {
        'latest_players': latest_players,
        'latest_date': latest_date,
        'avg_7d': round(avg_7d),
        'avg_30d': round(avg_30d),
        'growth_7d': growth_7d,
        'growth_30d': growth_30d,
        'active_days': active_days,
        'peak_date': peak_date,
    }


def main():
    xlsx_path = os.sys.argv[1] if len(os.sys.argv) > 1 else DEFAULT_XLSX
    if not os.path.exists(xlsx_path):
        print(f'[ERROR] xlsx not found: {xlsx_path}')
        return

    print(f'=== Roblox xlsx 导入 ===')
    print(f'输入: {xlsx_path}')
    df = pd.read_excel(xlsx_path)
    print(f'共 {len(df)} 行, {len(df.columns)} 列')

    # 识别日期列
    date_cols = [c for c in df.columns if str(c).startswith('2026')]
    print(f'日期列: {len(date_cols)} ({date_cols[0]} ~ {date_cols[-1]})')

    games = []
    cat_counter = {}
    for _, row in df.iterrows():
        placeId = int(row['placeId']) if pd.notna(row['placeId']) else 0
        if placeId == 0:
            continue
        name = str(row['name']).strip()
        visits = int(row['visits']) if pd.notna(row['visits']) else 0
        peak_players = int(row['peak_players']) if pd.notna(row['peak_players']) else 0
        create_date, create_year = parse_create_time(row.get('create_time'))
        cats = classify_game(name)
        for c in cats:
            cat_counter[c] = cat_counter.get(c, 0) + 1
        # 构建 daily_players 字典
        daily = {}
        for col in date_cols:
            v = row[col]
            if pd.notna(v) and v > 0:
                daily[date_col_to_date(col)] = int(v)
        derived = compute_derived(daily)
        games.append({
            'placeId': placeId,
            'name': name,
            'visits': visits,
            'peak_players': peak_players,
            'create_time': create_date,
            'create_year': create_year,
            'categories': cats,
            'daily_players': daily,
            **derived,
            'store_url': f'https://www.roblox.com/games/{placeId}',
        })

    # 排序: 按 peak_players 降序
    games.sort(key=lambda g: -g['peak_players'])

    # 构建分类元数据
    categories_meta = {}
    for c in CATEGORIES:
        if c['key'] in cat_counter:
            categories_meta[c['key']] = {
                'zh': c['zh'],
                'count': cat_counter[c['key']],
                'keywords': c['keywords'],
            }

    output = {
        '_meta': {
            'imported_at': datetime.now(CST).isoformat(),
            'source': os.path.basename(xlsx_path),
            'total_games': len(games),
            'date_range': [date_col_to_date(date_cols[0]), date_col_to_date(date_cols[-1])],
            'total_days': len(date_cols),
            'note': 'Roblox 平台游戏排行榜数据,每日玩家数时序',
        },
        'categories': categories_meta,
        'games': games,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: {OUTPUT_PATH}')
    print(f'文件大小: {os.path.getsize(OUTPUT_PATH)/1024:.1f} KB')
    print(f'游戏数: {len(games)}')
    print(f'分类数: {len(categories_meta)}')

    print(f'\n=== Top 10 by peak_players ===')
    for g in games[:10]:
        print(f'  {g["name"][:35]:35s} peak={g["peak_players"]:>8,}  visits={g["visits"]/1e9:.2f}B  7d_avg={g["avg_7d"]:>7,}  7d_growth={g["growth_7d"]:+5.1f}%')

    print(f'\n=== 分类分布 ===')
    for k, v in sorted(categories_meta.items(), key=lambda x: -x[1]['count']):
        print(f'  {k:15s} → {v["zh"]:8s}  {v["count"]} 款')


if __name__ == '__main__':
    main()
