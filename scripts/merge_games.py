#!/usr/bin/env python3
"""Merge discovered games into game_registry.json"""
import json

with open('docs/data/game_registry.json', 'r', encoding='utf-8') as f:
    registry = json.load(f)

with open('tmp/discovered_games.json', 'r', encoding='utf-8') as f:
    discovered = json.load(f)

existing_appids = {g['appid'] for g in registry['games']}

new_games_data = {
    4704690: {
        "cn_name": "超级变色龙",
        "tags": ["party", "pvp", "social_deduction"],
        "category_zh": "派对捉迷藏", "category_en": "Party Hide & Seek",
        "priority": "P0", "steam_key": "MECCHA CHAMELEON",
        "intro_zh": "在自己身上涂鸦融入背景的多人捉迷藏派对游戏。2-24人，躲藏方用画笔把自己涂成环境颜色，寻找方在限时内找出所有人。16天破1000万销量，2026年最大独立游戏爆款。"
    },
    553850: {
        "cn_name": "绝地潜兵2",
        "tags": ["coop", "pvp", "looter"],
        "category_zh": "合作射击", "category_en": "Co-op Shooter",
        "priority": "P0", "steam_key": "HELLDIVERS 2",
        "intro_zh": "4人合作第三人称射击，民主播撒先驱。PvE撤离+轨道打击，友军火力是最大笑点。2024年现象级爆款，定义了合作射击新范式。"
    },
    3124540: {
        "cn_name": "遥遥西土",
        "tags": ["coop", "extraction", "looter", "roguelike"],
        "category_zh": "合作撤离", "category_en": "Co-op Extraction",
        "priority": "P1", "steam_key": "Far Far West",
        "intro_zh": "4人合作西部奇幻撤离射击。机器人牛仔+法术+撤离任务+Roguelite构筑，48小时卖25万份，首周流水近亿。深岩银河+枪火重生+撤离的混血。"
    },
    3844970: {
        "cn_name": "地精捣蛋团",
        "tags": ["coop", "party", "physics"],
        "category_zh": "合作派对", "category_en": "Co-op Party",
        "priority": "P1", "steam_key": "Burglin' Gnomes",
        "intro_zh": "在线合作潜行派对，化身小地精闯入民宅偷物资搞破坏。搞怪物理引擎+家园升级+避让房主，好友开黑整活效果拉满。"
    },
    2211170: {
        "cn_name": "一起开火车2",
        "tags": ["coop", "party"],
        "category_zh": "合作派对", "category_en": "Co-op Party",
        "priority": "P1", "steam_key": None,
        "intro_zh": "手忙脚乱的铁路协作挑战续作。多人铺设铁轨+火车资源管理+程序化地形，派对合作品类经典IP续作。"
    },
    2445690: {
        "cn_name": "失落城堡2",
        "tags": ["coop", "roguelike"],
        "category_zh": "合作Roguelike", "category_en": "Co-op Roguelike",
        "priority": "P1", "steam_key": "Lost Castle 2",
        "intro_zh": "2D横版合作Roguelite动作冒险，200+武器装备+150+随机宝藏。前作销量200万+，国产肉鸽动作续作。"
    },
    548430: {
        "cn_name": "深岩银河",
        "tags": ["coop", "extraction", "looter"],
        "category_zh": "合作撤离", "category_en": "Co-op Extraction",
        "priority": "P0", "steam_key": "Deep Rock Galactic",
        "intro_zh": "4人合作矮人挖矿撤离射击标杆。程序化洞穴+职业分工+搜打撤公式奠基者，Rock and Stone！品类教科书级作品。"
    },
    945360: {
        "cn_name": "Among Us",
        "tags": ["party", "social_deduction", "pvp"],
        "category_zh": "社交推理", "category_en": "Social Deduction",
        "priority": "P1", "steam_key": "Among Us",
        "intro_zh": "4-15人社交推理派对游戏。船员完成任务vs冒充者暗杀，社交推理品类现象级爆款，定义了线上狼人杀品类。"
    },
    1326470: {
        "cn_name": "森林之子",
        "tags": ["horror", "coop", "survival"],
        "category_zh": "合作生存恐怖", "category_en": "Co-op Survival Horror",
        "priority": "P1", "steam_key": "Sons Of The Forest",
        "intro_zh": "4人合作开放世界生存恐怖续作。建基地+食人族+AI同伴+洞穴探索，前作森林的3D化续作，生存恐怖品类代表作。"
    },
    632360: {
        "cn_name": "雨中冒险2",
        "tags": ["coop", "roguelike"],
        "category_zh": "合作Roguelike", "category_en": "Co-op Roguelike",
        "priority": "P1", "steam_key": "Risk of Rain 2",
        "intro_zh": "4人合作3D第三人称Roguelite射击。物品叠加构筑+越来越强的怪物潮，合作Roguelike射击品类标杆。"
    },
    1911610: {
        "cn_name": "风中行者",
        "tags": ["coop", "roguelike"],
        "category_zh": "合作Roguelike", "category_en": "Co-op Roguelike",
        "priority": "P1", "steam_key": "Windblown",
        "intro_zh": "死亡细胞团队新作，1-3人合作极速Roguelite动作。吸收牺牲勇士力量+锻铸武器，越打越快的充能爆发战斗。"
    },
    3989960: {
        "cn_name": "青蛙小队",
        "tags": ["coop", "party", "physics"],
        "category_zh": "合作派对", "category_en": "Co-op Party",
        "priority": "P2", "steam_key": None,
        "intro_zh": "8人合作撤离式解谜平台。舌头摆荡+弹射队友+吃食物变巨蛙，搞怪物理+下水道探险，派对合作新秀。"
    },
    4000: {
        "cn_name": "盖瑞模组",
        "tags": ["party", "pvp", "physics"],
        "category_zh": "派对沙盒", "category_en": "Party Sandbox",
        "priority": "P2", "steam_key": "Garry's Mod",
        "intro_zh": "Source引擎物理沙盒，Prop Hunt捉迷藏模式发源地。3万+日活玩家，社区创作生态最丰富的多人游戏之一。"
    },
    1782210: {
        "cn_name": "螃蟹游戏",
        "tags": ["party", "pvp"],
        "category_zh": "派对竞技", "category_en": "Party PvP",
        "priority": "P2", "steam_key": "Crab Game",
        "intro_zh": "免费多人派对大乱斗， squid game式淘汰赛。低门槛+搞笑物理+免费，派对品类入门首选。"
    },
    381210: {
        "cn_name": "黎明杀机",
        "tags": ["horror", "pvp", "asymmetric"],
        "category_zh": "非对称恐怖", "category_en": "Asymmetric Horror",
        "priority": "P0", "steam_key": "Dead by Daylight",
        "intro_zh": "1v4非对称恐怖竞技标杆。杀手vs逃生者，IP联动不断（杰森/贞子/生化危机），9年运营长青，非对称恐怖品类绝对王者。"
    }
}

skip_appids = {2689100, 2379780}  # VizLab(tool), Balatro(single)

for game_info in discovered:
    appid = game_info['appid']
    if appid in existing_appids or appid in skip_appids:
        continue
    if appid not in new_games_data:
        continue
    meta = new_games_data[appid]
    release_raw = game_info.get('release_date', '')
    # normalize release date
    release = release_raw.replace(' 年 ', '-').replace(' 月 ', '-').replace(' 日', '').replace(' ', '')
    if '即将' in release or not release:
        release = 'TBA'
    game_entry = {
        "appid": appid,
        "name": game_info['name'],
        "cn_name": meta['cn_name'],
        "tags": meta['tags'],
        "category_zh": meta['category_zh'],
        "category_en": meta['category_en'],
        "status": "已发售",
        "dev": game_info.get('developer', ''),
        "release": release,
        "players": "",
        "priority": meta['priority'],
        "platforms": ["steam"],
        "store_url": f"https://store.steampowered.com/app/{appid}/",
        "steam_key": meta.get('steam_key'),
        "intro_zh": meta['intro_zh']
    }
    registry['games'].append(game_entry)
    print(f"Added: {meta['cn_name']} ({appid})")

registry['version'] = '2.0.0'
registry['updated_at'] = '2026-07-01'
# Add new tag
if 'hide_and_seek' not in registry['tag_definitions']:
    registry['tag_definitions']['hide_and_seek'] = {"zh": "捉迷藏", "steam_tag_id": None}
# Update MECCHA tags to include hide_and_seek
for g in registry['games']:
    if g['appid'] == 4704690:
        if 'hide_and_seek' not in g['tags']:
            g['tags'].append('hide_and_seek')

with open('docs/data/game_registry.json', 'w', encoding='utf-8') as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

print(f"\nTotal games: {len(registry['games'])}")
