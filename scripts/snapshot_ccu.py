#!/usr/bin/env python3
"""
CCU 历史快照系统
每天跑一次，把当前 CCU 存进 ccu_history.json
结构: {appid: [{date, ccu}], ...}
数据源: docs/data/steam_data.json (由 steam_crawler.py 产出)
输出: docs/data/ccu_history.json
"""
import json
import os
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
STEAM_DATA_PATH = os.path.join(DATA_DIR, 'steam_data.json')
HISTORY_PATH = os.path.join(DATA_DIR, 'ccu_history.json')

# 北京时间
CST = timezone(timedelta(hours=8))

def load_steam_data():
    if not os.path.exists(STEAM_DATA_PATH):
        print(f'[ERROR] {STEAM_DATA_PATH} not found')
        return {}
    with open(STEAM_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_history():
    if not os.path.exists(HISTORY_PATH):
        return {}
    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_ccu_from_steam(name, data):
    """从 steam_data.json 提取 CCU"""
    if not isinstance(data, dict):
        return 0
    if data.get('steamspy') and data['steamspy'].get('ccu'):
        return data['steamspy']['ccu']
    if data.get('store') and data['store'].get('ccu'):
        return data['store']['ccu']
    return 0

def get_appid_from_steam(data):
    """从 steam_data.json 提取 appid"""
    if not isinstance(data, dict):
        return None
    if data.get('store') and data['store'].get('appid'):
        return str(data['store']['appid'])
    if data.get('steamspy') and data['steamspy'].get('appid'):
        return str(data['steamspy']['appid'])
    return None

def snapshot():
    steam_data = load_steam_data()
    history = load_history()
    
    today = datetime.now(CST).strftime('%Y-%m-%d')
    
    # 用 steam_key 作为 key（因为 appid 可能在 steam_data 里）
    updated = 0
    skipped = 0
    
    for name, data in steam_data.items():
        appid = get_appid_from_steam(data)
        if not appid:
            # 用 name 做 fallback key
            appid = f'name:{name}'
        
        ccu = get_ccu_from_steam(name, data)
        
        if appid not in history:
            history[appid] = []
        
        # 检查今天是否已存
        existing = [e for e in history[appid] if e.get('date') == today]
        if existing:
            # 更新今天的
            existing[0]['ccu'] = ccu
            existing[0]['name'] = name
            existing[0]['updated_at'] = datetime.now(CST).isoformat()
        else:
            history[appid].append({
                'date': today,
                'ccu': ccu,
                'name': name,
                'updated_at': datetime.now(CST).isoformat()
            })
        
        # 限制最多 365 天
        if len(history[appid]) > 365:
            history[appid] = history[appid][-365:]
        
        updated += 1
    
    # 同时把 registry 里的游戏也加入（即使没 steam_data）
    registry_path = os.path.join(DATA_DIR, 'game_registry.json')
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        for g in registry.get('games', []):
            appid = str(g.get('appid', ''))
            if not appid or appid == '0':
                continue
            if appid not in history:
                # 没有 steam_data 的游戏，CCU 记为 0
                history[appid] = [{
                    'date': today,
                    'ccu': 0,
                    'name': g.get('cn_name') or g.get('name', ''),
                    'updated_at': datetime.now(CST).isoformat()
                }]
                skipped += 1
    
    # 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            '_meta': {
                'last_snapshot': datetime.now(CST).isoformat(),
                'total_games': len(history),
                'with_steam_data': updated,
                'registry_only': skipped
            },
            'data': history
        }, f, ensure_ascii=False, indent=2)
    
    print(f'[Snapshot] {today}: {updated} games from steam_data, {skipped} registry-only')
    print(f'[Snapshot] Total tracked: {len(history)}')
    print(f'[Snapshot] Saved to {HISTORY_PATH}')
    
    # 打印一些统计
    print('\n=== CCU 快照统计 ===')
    for appid, entries in sorted(history.items(), key=lambda x: x[1][-1].get('ccu', 0) if x[1] else 0, reverse=True)[:10]:
        if entries:
            latest = entries[-1]
            days = len(entries)
            print(f'  {latest.get("name", appid):30s} | CCU: {latest["ccu"]:>8,} | {days} days history')

if __name__ == '__main__':
    snapshot()
