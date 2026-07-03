#!/usr/bin/env python3
"""
DataValidator - 数据质量守护 Agent
每次数据采集后运行,验证 6 个数据文件的完整性/合理性/一致性
输出: docs/data/validation_report.json
有 ERROR 时 exit 1 (阻断 GitHub Action push)
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
OUTPUT_PATH = os.path.join(DATA_DIR, 'validation_report.json')

CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime('%Y-%m-%d')

# 阈值
CCU_MIN, CCU_MAX = 0, 5_000_000
POTENTIAL_MIN, POTENTIAL_MAX = 0, 100
POSITIVE_MIN, POSITIVE_MAX = 0, 100
WISHLIST_MIN, WISHLIST_MAX = 0, 10_000_000
CCU_MUTATION_WARN = 0.5  # 50% 突变告警


def load_json(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {'_parse_error': str(e)}


def check_result(name, status, message, details=None):
    return {
        'name': name,
        'status': status,  # PASS / WARN / ERROR
        'message': message,
        'details': details or []
    }


def main():
    print('=== DataValidator 启动 ===')
    print(f'验证日期: {TODAY}\n')
    
    checks = []
    errors = 0
    warnings = 0
    
    registry = load_json('game_registry.json')
    steam_data = load_json('steam_data.json')
    rich_data = load_json('steam_rich_data.json')
    ccu_history = load_json('ccu_history.json')
    developers = load_json('developers.json')
    potential = load_json('potential_scores.json')
    
    # ========== 1. 完整性检查 ==========
    print('--- 1. 完整性检查 ---')
    
    # 1.1 文件存在性
    missing = []
    for name in ['game_registry.json', 'steam_data.json', 'steam_rich_data.json', 
                 'ccu_history.json', 'developers.json', 'potential_scores.json']:
        path = os.path.join(DATA_DIR, name)
        if not os.path.exists(path):
            missing.append(name)
    if missing:
        checks.append(check_result('文件存在性', 'ERROR', f'缺失文件: {", ".join(missing)}'))
        errors += 1
    else:
        checks.append(check_result('文件存在性', 'PASS', '6 个数据文件全部存在'))
    
    # 1.2 文件可解析性
    parse_errors = []
    for name, data in [('registry', registry), ('steam_data', steam_data), 
                       ('rich_data', rich_data), ('ccu_history', ccu_history),
                       ('developers', developers), ('potential', potential)]:
        if data is None:
            parse_errors.append(f'{name}: 文件不存在')
        elif isinstance(data, dict) and '_parse_error' in data:
            parse_errors.append(f'{name}: {data["_parse_error"]}')
    if parse_errors:
        checks.append(check_result('JSON 解析', 'ERROR', f'{len(parse_errors)} 个文件解析失败', parse_errors))
        errors += 1
    else:
        checks.append(check_result('JSON 解析', 'PASS', '6 个文件全部可解析'))
    
    # 1.3 registry 游戏数量
    if registry and 'games' in registry:
        game_count = len(registry['games'])
        if game_count < 10:
            checks.append(check_result('registry 游戏数', 'WARN', f'游戏数偏少: {game_count}'))
            warnings += 1
        else:
            checks.append(check_result('registry 游戏数', 'PASS', f'{game_count} 款游戏'))
    else:
        checks.append(check_result('registry 游戏数', 'ERROR', 'registry.games 字段缺失'))
        errors += 1
    
    # 1.4 steam_data 游戏数
    if steam_data and isinstance(steam_data, dict):
        sd_count = len(steam_data)
        if sd_count < 5:
            checks.append(check_result('steam_data 游戏数', 'WARN', f'游戏数偏少: {sd_count}'))
            warnings += 1
        else:
            checks.append(check_result('steam_data 游戏数', 'PASS', f'{sd_count} 款游戏有实时数据'))
    else:
        checks.append(check_result('steam_data 游戏数', 'ERROR', 'steam_data 为空或格式错误'))
        errors += 1
    
    # 1.5 rich_data 游戏数
    if rich_data and 'games' in rich_data:
        rd_count = len(rich_data['games'])
        checks.append(check_result('rich_data 游戏数', 'PASS', f'{rd_count} 款游戏有富数据'))
    else:
        checks.append(check_result('rich_data 游戏数', 'WARN', 'rich_data 为空'))
        warnings += 1
    
    # 1.6 developers 数量
    if developers and 'developers' in developers:
        dev_count = len(developers['developers'])
        checks.append(check_result('developers 数量', 'PASS', f'{dev_count} 个开发者'))
    else:
        checks.append(check_result('developers 数量', 'WARN', 'developers 为空'))
        warnings += 1
    
    # 1.7 potential_scores 数量
    if potential and 'scores' in potential:
        pot_count = len(potential['scores'])
        checks.append(check_result('potential_scores 数量', 'PASS', f'{pot_count} 个潜力分'))
    else:
        checks.append(check_result('potential_scores 数量', 'WARN', 'potential_scores 为空'))
        warnings += 1
    
    # ========== 2. 数值合理性 ==========
    print('\n--- 2. 数值合理性检查 ---')
    
    # 2.1 CCU 范围
    if steam_data and isinstance(steam_data, dict):
        bad_ccu = []
        for name, data in steam_data.items():
            if not isinstance(data, dict):
                continue
            ccu = 0
            if data.get('steamspy'):
                ccu = data['steamspy'].get('ccu', 0)
            elif data.get('store'):
                ccu = data['store'].get('ccu', 0)
            if not (CCU_MIN <= ccu <= CCU_MAX):
                bad_ccu.append(f'{name}: CCU={ccu}')
        if bad_ccu:
            checks.append(check_result('CCU 数值范围', 'ERROR', f'{len(bad_ccu)} 个游戏 CCU 越界', bad_ccu[:5]))
            errors += 1
        else:
            checks.append(check_result('CCU 数值范围', 'PASS', '全部在合理范围 (0-5M)'))
    
    # 2.2 潜力分范围
    if potential and 'scores' in potential:
        bad_pot = []
        for s in potential['scores']:
            score = s.get('score', -1)
            if not (POTENTIAL_MIN <= score <= POTENTIAL_MAX):
                bad_pot.append(f'{s.get("name", "?")}: {score}')
        if bad_pot:
            checks.append(check_result('潜力分范围', 'ERROR', f'{len(bad_pot)} 个越界 (0-100)', bad_pot[:5]))
            errors += 1
        else:
            checks.append(check_result('潜力分范围', 'PASS', '全部在 0-100 范围'))
    
    # 2.3 wishlist 范围
    if registry and 'games' in registry:
        bad_wl = []
        for g in registry['games']:
            wl = g.get('wishlist_count', 0)
            if not (WISHLIST_MIN <= wl <= WISHLIST_MAX):
                bad_wl.append(f'{g.get("cn_name", g.get("name", "?"))}: {wl}')
        if bad_wl:
            checks.append(check_result('wishlist 范围', 'ERROR', f'{len(bad_wl)} 个越界', bad_wl[:5]))
            errors += 1
        else:
            checks.append(check_result('wishlist 范围', 'PASS', '全部在合理范围'))
    
    # ========== 3. 跨数据源一致性 ==========
    print('\n--- 3. 跨数据源一致性 ---')
    
    # 3.1 registry appid 在 rich_data 存在
    if registry and rich_data:
        rich_appids = set(str(g.get('appid', '')) for g in rich_data.get('games', []))
        missing_rich = []
        for g in registry.get('games', []):
            appid = str(g.get('appid', ''))
            if appid == '0' or not appid:
                continue  # 超自然等无 appid 的跳过
            if appid not in rich_appids:
                missing_rich.append(f'{g.get("cn_name", g.get("name", "?"))} (appid={appid})')
        if missing_rich:
            checks.append(check_result('registry → rich_data', 'WARN', f'{len(missing_rich)} 个游戏缺富数据', missing_rich[:5]))
            warnings += 1
        else:
            checks.append(check_result('registry → rich_data', 'PASS', '所有有 appid 的游戏都有富数据'))
    
    # 3.2 registry steam_key 在 steam_data 存在
    if registry and steam_data:
        missing_sd = []
        for g in registry.get('games', []):
            key = g.get('steam_key')
            if not key:
                continue
            status = g.get('status', '')
            if status in ('WISHLIST', '在研'):
                continue  # 未发售的可以没有 steam_data
            if key not in steam_data:
                missing_sd.append(f'{g.get("cn_name", g.get("name", "?"))} (key={key})')
        if missing_sd:
            checks.append(check_result('registry → steam_data', 'ERROR', f'{len(missing_sd)} 个已发售游戏缺实时数据', missing_sd[:5]))
            errors += 1
        else:
            checks.append(check_result('registry → steam_data', 'PASS', '所有已发售游戏都有实时数据'))
    
    # 3.3 registry appid 在 ccu_history 存在
    if registry and ccu_history and 'data' in ccu_history:
        hist_appids = set(ccu_history['data'].keys())
        missing_hist = []
        for g in registry.get('games', []):
            appid = str(g.get('appid', ''))
            if appid == '0' or not appid:
                continue
            if appid not in hist_appids:
                missing_hist.append(f'{g.get("cn_name", g.get("name", "?"))} (appid={appid})')
        if missing_hist:
            checks.append(check_result('registry → ccu_history', 'WARN', f'{len(missing_hist)} 个游戏无历史', missing_hist[:5]))
            warnings += 1
        else:
            checks.append(check_result('registry → ccu_history', 'PASS', '所有游戏都有 CCU 历史'))
    
    # ========== 4. 异常检测 ==========
    print('\n--- 4. 异常检测 ---')
    
    # 4.1 CCU 突变检测
    if ccu_history and 'data' in ccu_history:
        mutations = []
        for appid, entries in ccu_history['data'].items():
            if not isinstance(entries, list) or len(entries) < 2:
                continue
            today_ccu = entries[-1].get('ccu', 0)
            yesterday_ccu = entries[-2].get('ccu', 0)
            if yesterday_ccu == 0:
                if today_ccu > 0:
                    mutations.append(f'{entries[-1].get("name", appid)}: 0→{today_ccu} (新增)')
                continue
            change_pct = abs(today_ccu - yesterday_ccu) / yesterday_ccu
            if change_pct > CCU_MUTATION_WARN:
                direction = '↑' if today_ccu > yesterday_ccu else '↓'
                mutations.append(f'{entries[-1].get("name", appid)}: {yesterday_ccu}→{today_ccu} ({direction}{change_pct*100:.0f}%)')
        if mutations:
            checks.append(check_result('CCU 突变检测', 'WARN', f'{len(mutations)} 个游戏 CCU 突变 >50%', mutations[:5]))
            warnings += 1
        else:
            checks.append(check_result('CCU 突变检测', 'PASS', '无 >50% 突变'))
    
    # 4.2 已发售游戏 CCU=0
    if registry and steam_data:
        zero_ccu_released = []
        for g in registry.get('games', []):
            key = g.get('steam_key')
            status = g.get('status', '')
            if status in ('WISHLIST', '在研', 'EA'):
                continue
            if not key or key not in steam_data:
                continue
            data = steam_data[key]
            ccu = 0
            if isinstance(data, dict):
                if data.get('steamspy'):
                    ccu = data['steamspy'].get('ccu', 0)
                elif data.get('store'):
                    ccu = data['store'].get('ccu', 0)
            if ccu == 0:
                zero_ccu_released.append(g.get('cn_name', g.get('name', '?')))
        if zero_ccu_released:
            checks.append(check_result('已发售 CCU=0', 'ERROR', f'{len(zero_ccu_released)} 个已发售游戏 CCU=0', zero_ccu_released[:5]))
            errors += 1
        else:
            checks.append(check_result('已发售 CCU=0', 'PASS', '所有已发售游戏 CCU > 0'))
    
    # 4.3 潜力分=0
    if potential and 'scores' in potential:
        zero_pot = [s.get('name', '?') for s in potential['scores'] if s.get('score', -1) == 0]
        if len(zero_pot) > len(potential['scores']) * 0.5:
            checks.append(check_result('潜力分=0 占比', 'WARN', f'{len(zero_pot)}/{len(potential["scores"])} 个游戏潜力分为 0'))
            warnings += 1
        else:
            checks.append(check_result('潜力分=0 占比', 'PASS', f'仅 {len(zero_pot)} 个游戏潜力分为 0'))
    
    # ========== 5. 历史一致性 ==========
    print('\n--- 5. 历史一致性 ---')
    
    # 5.1 ccu_history 最新日期
    if ccu_history and 'data' in ccu_history:
        latest_dates = set()
        for appid, entries in ccu_history['data'].items():
            if isinstance(entries, list) and entries:
                latest_dates.add(entries[-1].get('date', ''))
        if TODAY in latest_dates:
            checks.append(check_result('history 最新日期', 'PASS', f'今天 ({TODAY}) 数据已入库'))
        else:
            checks.append(check_result('history 最新日期', 'WARN', f'最新日期不是今天,而是: {", ".join(list(latest_dates)[:3])}'))
            warnings += 1
    
    # 5.2 每个 appid 至少 1 条历史
    if ccu_history and 'data' in ccu_history:
        empty_hist = []
        for appid, entries in ccu_history['data'].items():
            if appid.startswith('_') or not isinstance(entries, list):
                continue
            if len(entries) == 0:
                empty_hist.append(appid)
        if empty_hist:
            checks.append(check_result('history 空记录', 'WARN', f'{len(empty_hist)} 个 appid 无历史', empty_hist[:5]))
            warnings += 1
        else:
            checks.append(check_result('history 空记录', 'PASS', '所有 appid 都有历史'))
    
    # ========== 汇总 ==========
    print('\n=== 验证汇总 ===')
    print(f'总检查数: {len(checks)}')
    print(f'PASS: {sum(1 for c in checks if c["status"] == "PASS")}')
    print(f'WARN: {warnings}')
    print(f'ERROR: {errors}')
    
    print('\n--- 详细 ---')
    for c in checks:
        icon = {'PASS': '✓', 'WARN': '⚠', 'ERROR': '✗'}[c['status']]
        print(f'  {icon} [{c["status"]}] {c["name"]}: {c["message"]}')
        for d in c.get('details', [])[:3]:
            print(f'      - {d}')
    
    # 保存报告
    report = {
        '_meta': {
            'validated_at': datetime.now(CST).isoformat(),
            'date': TODAY,
            'passed': errors == 0,
            'total_checks': len(checks),
            'pass_count': sum(1 for c in checks if c['status'] == 'PASS'),
            'warn_count': warnings,
            'error_count': errors
        },
        'checks': checks
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'\n报告已保存: {OUTPUT_PATH}')
    
    # 有 ERROR 时 exit 1,阻断 GitHub Action
    if errors > 0:
        print(f'\n❌ 验证失败: {errors} 个 ERROR')
        sys.exit(1)
    else:
        print(f'\n✅ 验证通过 (有 {warnings} 个警告)')
        sys.exit(0)


if __name__ == '__main__':
    main()
