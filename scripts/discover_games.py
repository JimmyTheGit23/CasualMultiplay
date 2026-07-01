#!/usr/bin/env python3
"""
Steam game discovery script - fetches app details for a list of appids
and outputs JSON suitable for game_registry.json
"""
import json
import time
import urllib.request
import urllib.error
import sys

APPI_DS = [
    4704690,   # MECCHA CHAMELEON
    553850,    # Helldivers 2
    3124540,   # Far Far West
    3844970,   # Burglin' Gnomes
    2211170,   # Unrailed 2
    2445690,   # Lost Castle 2
    548430,    # Deep Rock Galactic
    945360,    # Among Us
    1326470,   # Sons of the Forest
    632360,    # Risk of Rain 2
    1425470,   # It Takes Two
    1911610,   # Windblown
    3989960,   # Frog Sqwad
    4000,      # Garry's Mod
    1782210,   # Crab Game (might be wrong)
    381210,    # Dead by Daylight (already tracked but not in registry)
    2586220,   # Split Fiction (guess)
    2689100,   # Crab Game (alternative)
    2379780,   # PEAK (already in registry, for verification)
]

def fetch_app_details(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=cn&l=schinese"
    req = urllib.request.Request(url, headers={'User-Agent': 'CasualMultiplayBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data
    except Exception as e:
        return {"error": str(e)}

def main():
    results = []
    for appid in APPI_DS:
        print(f"Fetching {appid}...", file=sys.stderr)
        data = fetch_app_details(appid)
        key = str(appid)
        if key in data and data[key].get('success'):
            info = data[key]['data']
            game = {
                'appid': appid,
                'name': info.get('name', ''),
                'type': info.get('type', ''),
                'developer': info.get('developers', [''])[0] if info.get('developers') else '',
                'publisher': info.get('publishers', [''])[0] if info.get('publishers') else '',
                'release_date': info.get('release_date', {}).get('date', ''),
                'price': info.get('price_overview', {}).get('final_formatted', '') if info.get('price_overview') else 'free',
                'platforms': info.get('platforms', {}),
                'categories': [c.get('description', '') for c in info.get('categories', [])],
                'genres': [g.get('description', '') for g in info.get('genres', [])],
                'header_image': info.get('header_image', ''),
                'short_desc': info.get('short_description', ''),
            }
            results.append(game)
            print(f"  OK: {game['name']} ({game['release_date']})", file=sys.stderr)
        else:
            print(f"  FAIL: {appid} - {data}", file=sys.stderr)
        time.sleep(1.5)  # rate limit

    output = json.dumps(results, ensure_ascii=False, indent=2)
    print(output)

if __name__ == '__main__':
    main()
