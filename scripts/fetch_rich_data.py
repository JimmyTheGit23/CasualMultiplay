#!/usr/bin/env python3
"""
Enhanced discovery: fetch full app details for ALL registry games,
output a rich data file with header images, screenshots, descriptions, etc.
"""
import json
import time
import urllib.request
import sys

def fetch_app(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=cn&l=schinese"
    req = urllib.request.Request(url, headers={'User-Agent': 'CasualMultiplayBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        key = str(appid)
        if key in data and data[key].get('success'):
            return data[key]['data']
    except Exception as e:
        print(f"  error: {e}", file=sys.stderr)
    return None

def main():
    with open('docs/data/game_registry.json', 'r', encoding='utf-8') as f:
        registry = json.load(f)

    out = {"fetched_at": "2026-07-01", "games": []}
    for g in registry['games']:
        appid = g['appid']
        if appid == 0:  # chaoziran, no Steam data
            continue
        print(f"Fetching {appid} {g.get('cn_name', g['name'])}...", file=sys.stderr)
        data = fetch_app(appid)
        time.sleep(1.2)
        if not data:
            continue
        entry = {
            "appid": appid,
            "name": data.get('name', g['name']),
            "cn_name": g.get('cn_name', g['name']),
            "developer": data.get('developers', [''])[0] if data.get('developers') else '',
            "publisher": data.get('publishers', [''])[0] if data.get('publishers') else '',
            "release_date": data.get('release_date', {}).get('date', ''),
            "is_free": data.get('is_free', False),
            "price": data.get('price_overview', {}).get('final_formatted', '免费') if data.get('price_overview') else '免费',
            "header_image": data.get('header_image', ''),
            "capsule_image": data.get('capsule_imagev5', ''),
            "short_description": data.get('short_description', ''),
            "categories": [c.get('description', '') for c in data.get('categories', [])],
            "genres": [gd.get('description', '') for gd in data.get('genres', [])],
            "screenshots": [s.get('path_thumbnail', '') for s in data.get('screenshots', [])[:6]],
            "recommendations": data.get('recommendations', {}).get('total', 0),
            "achievements": data.get('achievements', {}).get('total', 0),
            "platforms": data.get('platforms', {}),
            "metacritic": data.get('metacritic', {}).get('score', None),
        }
        out['games'].append(entry)
        print(f"  OK ({len(entry['screenshots'])} screenshots)", file=sys.stderr)

    with open('docs/data/steam_rich_data.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(out['games'])} games to docs/data/steam_rich_data.json", file=sys.stderr)

if __name__ == '__main__':
    main()
