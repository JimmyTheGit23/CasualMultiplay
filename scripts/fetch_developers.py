#!/usr/bin/env python3
"""
开发者历史作品抓取
用 Steam Store 页面的 developer 链接反查同开发者所有作品
输出: docs/data/developers.json
"""
import json
import os
import time
import urllib.request
import urllib.error
import re
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'docs', 'data')
REGISTRY_PATH = os.path.join(DATA_DIR, 'game_registry.json')
RICH_DATA_PATH = os.path.join(DATA_DIR, 'steam_rich_data.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'developers.json')

CST = timezone(timedelta(hours=8))


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f'  [FAIL] {url}: {e}')
                return None


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None


def get_developer_apps(developer_name):
    """用 Steam developer 页面反查作品列表"""
    url = f'https://store.steampowered.com/search/?developer={urllib.parse.quote(developer_name)}&l=schinese'
    html = fetch_html(url)
    if not html:
        return []
    
    # 解析搜索结果中的 appid
    appids = re.findall(r'data-ds-appid="(\d+)"', html)
    # 去重
    seen = set()
    unique = []
    for aid in appids:
        if aid not in seen:
            seen.add(aid)
            unique.append(aid)
    return unique


def get_app_brief(appid):
    """抓 app 基础信息: name, release_date, review_score, ccu"""
    url = f'https://store.steampowered.com/api/appdetails?appids={appid}&cc=cn&l=schinese'
    data = fetch_json(url)
    if not data:
        return None
    key = str(appid)
    if key not in data or not data[key].get('success'):
        return None
    info = data[key]['data']
    return {
        'appid': appid,
        'name': info.get('name', ''),
        'release_date': info.get('release_date', {}).get('date', ''),
        'type': info.get('type', ''),
        'developers': info.get('developers', []),
        'publishers': info.get('publishers', []),
        'header_image': info.get('header_image', ''),
    }


def main():
    print('=== 开发者历史作品抓取 ===')
    
    # 从 registry + rich_data 收集所有开发者
    developers_set = set()

    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        for g in registry.get('games', []):
            dev = g.get('dev', '').strip()
            if dev and dev != '自研项目':
                # 可能是 "Dev A / Dev B" 格式
                for d in dev.split('/'):
                    d = d.strip()
                    if d:
                        # 去掉中文括号及其内容,如 "24 Entertainment（网易）" → "24 Entertainment"
                        import re
                        d_clean = re.sub(r'[（(][^）)]*[）)]', '', d).strip()
                        if d_clean:
                            developers_set.add(d_clean)
                        # 原始名也加(可能在 Steam 上能搜到,比如个别游戏真有 "(网易)" 后缀)
                        developers_set.add(d)
    
    if os.path.exists(RICH_DATA_PATH):
        with open(RICH_DATA_PATH, 'r', encoding='utf-8') as f:
            rich = json.load(f)
        for g in rich.get('games', []):
            dev = g.get('developer', '').strip()
            if dev:
                developers_set.add(dev)
    
    print(f'共 {len(developers_set)} 个开发者待查')
    
    result = {
        '_meta': {
            'fetched_at': datetime.now(CST).isoformat(),
            'total_developers': len(developers_set)
        },
        'developers': {}
    }
    
    for i, dev_name in enumerate(sorted(developers_set)):
        print(f'[{i+1}/{len(developers_set)}] {dev_name}...', end=' ')

        # 用 Steam search 反查
        appids = get_developer_apps(dev_name)
        print(f'找到 {len(appids)} 个作品')

        # 只抓前 10 个（避免太多请求）
        apps = []
        for appid in appids[:10]:
            brief = get_app_brief(appid)
            if brief:
                apps.append(brief)
            time.sleep(0.5)

        result['developers'][dev_name] = {
            'name': dev_name,
            'total_apps_on_steam': len(appids),
            'sampled_apps': len(apps),
            'apps': apps,
            'is_first_game': False  # 先标记 False,后面用反向索引重算
        }

        time.sleep(1)

    # 补全: registry 里带中文括号的 dev(如 "24 Entertainment（网易）") 搜不到,
    # 但清理后的名字("24 Entertainment")能搜到。把数据复制一份给原始 key
    import re
    for dev_name in list(result['developers'].keys()):
        info = result['developers'][dev_name]
        if '（' not in dev_name and '(' not in dev_name:
            continue
        clean = re.sub(r'[（(][^）)]*[）)]', '', dev_name).strip()
        if clean and clean in result['developers']:
            result['developers'][dev_name] = {
                'name': dev_name,
                'total_apps_on_steam': result['developers'][clean]['total_apps_on_steam'],
                'sampled_apps': result['developers'][clean]['sampled_apps'],
                'apps': result['developers'][clean]['apps'],
                'is_first_game': result['developers'][clean]['is_first_game'],
                'aliased_to': clean
            }

    # 第二轮: 用反向索引重算 is_first_game
    # dev_name -> [appid1, appid2, ...]
    dev_to_apps = {}
    for dev_name, info in result['developers'].items():
        for app in info['apps']:
            # 只算 game 类型,不把 dlc/soundtrack 算进去
            if app.get('type') != 'game':
                continue
            devs_list = app.get('developers', [])
            for d in devs_list:
                d = d.strip()
                if d:
                    dev_to_apps.setdefault(d, set()).add(app['appid'])

    for dev_name, info in result['developers'].items():
        # 用 dev 自身 + 各种大小写变体匹配 (Steam 大小写可能不一致)
        matched_apps = set()
        for key, apps_set in dev_to_apps.items():
            if key.lower() == dev_name.lower():
                matched_apps.update(apps_set)
        info['is_first_game'] = len(matched_apps) == 1
        # 也存下该 dev 实际参与过的游戏
        info['actual_dev_apps'] = sorted(matched_apps)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f'\n已保存到 {OUTPUT_PATH}')

    # 统计
    first_game_devs = [d for d, info in result['developers'].items() if info['is_first_game']]
    print(f'\n=== 统计 ===')
    print(f'总开发者: {len(result["developers"])}')
    print(f'首作开发者: {len(first_game_devs)}')
    for d in first_game_devs:
        info = result['developers'][d]
        if info['apps']:
            app = info['apps'][0]
            print(f'  {d} → {app["name"]} ({app["release_date"]})')


if __name__ == '__main__':
    import urllib.parse
    main()
