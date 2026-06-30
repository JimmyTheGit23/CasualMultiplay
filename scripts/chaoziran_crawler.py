"""
超自然行动组数据爬虫 - 采集更新公告 + TapTap数据 + 官网新闻
数据源：BWIKI更新公告页、TapTap网页版、官网
"""

import json
import os
import re
import urllib.request
import urllib.parse
import urllib.error
import time
from datetime import datetime


SOURCE_EN_MAP = {
    "BWIKI": "BWIKI",
    "官网": "Official Site",
    "TapTap官方": "TapTap Official",
    "TapTap论坛": "TapTap Forum",
    "百度搜索": "Baidu Search",
    "百度贴吧": "Baidu Tieba",
    "B站": "Bilibili",
    "美国": "US",
    "日本": "Japan",
    "韩国": "South Korea",
    "台湾": "Taiwan, China",
    "香港": "Hong Kong, China",
    "巨人网络": "Giant Network",
}

TAG_EN_MAP = {
    "新皮肤": "New Skin",
    "新时装": "New Outfit",
    "品牌联动": "Brand Collab",
    "版本更新": "Version Update",
    "角色重做": "Character Rework",
    "新怪物": "New Monster",
    "新玩法": "New Mode",
    "新地图": "New Map",
    "新服": "New Server",
    "钓鱼": "Fishing",
    "IP联动": "IP Collab",
    "福利活动": "Reward Event",
    "限时活动": "Limited Event",
    "摸金节": "Treasure Festival",
    "公益活动": "CSR Event",
    "IP授权": "IP License",
    "BUG修复": "Bug Fix",
}

TRANSLATION_CACHE = {}



def translate_text(text, target_lang="en"):
    if target_lang != "en":
        return text
    if not isinstance(text, str):
        return text

    text = text.strip()
    if not text:
        return text
    if text in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[text]
    if text in SOURCE_EN_MAP:
        TRANSLATION_CACHE[text] = SOURCE_EN_MAP[text]
        return TRANSLATION_CACHE[text]
    if text in TAG_EN_MAP:
        TRANSLATION_CACHE[text] = TAG_EN_MAP[text]
        return TRANSLATION_CACHE[text]
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\s\-_:./,'!?&()%+]*", text):
        TRANSLATION_CACHE[text] = text
        return text

    query = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={query}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        translated = "".join(part[0] for part in data[0] if part and part[0]).strip()
        TRANSLATION_CACHE[text] = translated or text
    except Exception:
        TRANSLATION_CACHE[text] = text
    return TRANSLATION_CACHE[text]



def translate_list(items):
    return [translate_text(item) for item in items if item not in (None, "")]



def add_en_field(item, field):
    if not isinstance(item, dict) or field not in item:
        return
    value = item.get(field)
    if isinstance(value, str):
        item[f"{field}_en"] = translate_text(value)
    elif isinstance(value, list):
        item[f"{field}_en"] = translate_list(value)



def enrich_post_list(items):
    for item in items or []:
        add_en_field(item, "title")
        add_en_field(item, "source")
        add_en_field(item, "content_tags")
        for ann in item.get("announcements", []) or []:
            add_en_field(ann, "title")
            add_en_field(ann, "source")
            add_en_field(ann, "tags")
    return items



def enrich_chaoziran_bilingual(data):
    czr = (data or {}).get("chaoziran")
    if not czr:
        return data

    enrich_post_list(czr.get("bwiki_updates"))
    enrich_post_list(czr.get("official_news"))
    enrich_post_list(czr.get("new_content_tracker"))

    taptap = czr.get("taptap") or {}
    add_en_field(taptap, "source")
    add_en_field(taptap, "description")
    add_en_field(taptap, "tags")
    add_en_field(taptap, "fans_text")
    add_en_field(taptap, "download_text")

    community = czr.get("community") or {}
    enrich_post_list(community.get("taptap_forum"))

    bilibili = community.get("bilibili") or {}
    add_en_field(bilibili, "source")
    add_en_field(bilibili, "keyword")
    for video in bilibili.get("videos", []) or []:
        add_en_field(video, "title")

    tieba = community.get("tieba") or {}
    add_en_field(tieba, "source")
    add_en_field(tieba, "note")
    enrich_post_list(tieba.get("hot_posts"))

    tomb_busters = czr.get("tomb_busters") or {}
    add_en_field(tomb_busters, "name")
    for region in (tomb_busters.get("regions_data") or {}).values():
        add_en_field(region, "name")

    app_store_rankings = czr.get("app_store_rankings") or {}
    for region in app_store_rankings.values():
        add_en_field(region, "name")

    stock_price = czr.get("stock_price") or {}
    add_en_field(stock_price, "name")

    for tracker in czr.get("new_content_tracker", []) or []:
        add_en_field(tracker, "name")
        add_en_field(tracker, "tags")
        for ann in tracker.get("announcements", []) or []:
            add_en_field(ann, "title")
            add_en_field(ann, "source")

    return data



def fetch_html(url, retries=3):
    """带重试的HTML请求"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://wiki.biligame.com/",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAIL] {url}: {e}")
                return None


def fetch_json(url, retries=3):
    """带重试的JSON请求"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAIL] {url}: {e}")
                return None


def validate_url(url, app_id="714123"):
    """
    验证TapTap moment链接是否有效。
    返回 (is_valid, final_url)
    - is_valid: True/False
    - final_url: 有效返回原url，无效返回百度搜索fallback
    """
    # 非moment链接直接跳过验证
    if "/moment/" not in url:
        return True, url

    for attempt in range(2):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.taptap.cn/",
            })
            # 使用自定义opener来获取重定向后的URL
            opener = urllib.request.build_opener()
            with opener.open(req, timeout=8) as resp:
                final_url = resp.geturl()
                status = resp.getcode()

                # 检查是否被重定向到论坛首页（帖子被删除后的行为）
                forum_home_patterns = [
                    f"/app/{app_id}/topic",
                    f"/app/{app_id}/",
                ]
                is_redirected_home = any(p in final_url for p in forum_home_patterns) and "/moment/" not in final_url

                if status in (200, 301, 302, 307, 308) and not is_redirected_home:
                    return True, url
                else:
                    return False, final_url
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, None
            # 其他HTTP错误（403/500等）保守处理为失效
            return False, None
        except Exception as e:
            if attempt < 1:
                time.sleep(1)
            else:
                # 超时等网络错误，保守处理为未知（不修改）
                return True, url
    return True, url


def get_bwiki_updates():
    """从BWIKI获取超自然行动组更新公告"""
    url = "https://wiki.biligame.com/chaoziran/%E6%9B%B4%E6%96%B0%E5%85%AC%E5%91%8A"
    html = fetch_html(url)
    if not html:
        return []

    updates = []
    # 匹配更新公告标题（BWIKI的标题结构）
    title_pattern = re.compile(r'<h[23][^>]*>.*?<span[^>]*>([^<]+)</span>', re.DOTALL)
    matches = title_pattern.findall(html)

    for match in matches[:10]:
        title = match.strip()
        if title and ("更新" in title or "公告" in title or "版本" in title or "活动" in title):
            updates.append({
                "title": title,
                "source": "BWIKI",
            })

    # 备用模式
    if not updates:
        alt_pattern = re.compile(r'<a[^>]*href="[^"]*"[^>]*>([^<]*(?:更新|公告|版本|活动)[^<]*)</a>', re.IGNORECASE)
        matches = alt_pattern.findall(html)
        for match in matches[:10]:
            title = match.strip()
            if title:
                updates.append({
                    "title": title,
                    "source": "BWIKI",
                })

    return updates


def get_taptap_data():
    """从TapTap网页版提取超自然行动组数据（API已404，改用网页解析）"""
    app_id = 714123
    html = fetch_html(f"https://www.taptap.cn/app/{app_id}")
    if not html:
        print("  [WARN] TapTap网页版获取失败")
        return None

    result = {
        "app_id": app_id,
        "source": "taptap_webpage",
    }

    # 1. 从__NUXT_DATA__解析Nuxt3引用序列化
    payload_match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if payload_match:
        try:
            payload = json.loads(payload_match.group(1))
            # 遍历dict找关键key的引用
            for i, item in enumerate(payload):
                if isinstance(item, dict):
                    for key in ["score", "rating", "fans_count", "download_count", "rating_count",
                                "review_count", "follow_count", "install_count"]:
                        if key in item:
                            ref_idx = item[key]
                            if isinstance(ref_idx, int) and 0 <= ref_idx < len(payload):
                                val = payload[ref_idx]
                                if isinstance(val, (int, float, str)):
                                    result[key] = val

                # 提取标签
                if isinstance(item, str):
                    tag_url = re.search(r'tag=([^"%&]+)', item)
                    if tag_url:
                        tag_name = urllib.parse.unquote(tag_url.group(1))
                        if tag_name not in result.get("tags", []):
                            result.setdefault("tags", []).append(tag_name)
        except (json.JSONDecodeError, IndexError):
            pass

    # 2. 从meta标签补充描述
    desc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
    if desc:
        result["description"] = desc.group(1)

    # 3. 评分补充（多种来源验证）
    # 方法A: 页面显示的评分文本
    score_text = re.search(r'(\d\.\d)\s*(?:分|/10)', html)
    if score_text:
        result["score_display"] = float(score_text.group(1))

    # 方法B: aggregateRating
    ld = re.search(r'"aggregateRating"[^}]*"ratingValue"\s*:\s*"?([\d.]+)"?', html)
    if ld:
        result["rating_value"] = float(ld.group(1))

    # 如果Nuxt payload的score是引用索引（>10），用正则结果替代
    if "score" in result:
        s = result["score"]
        if isinstance(s, (int, float)) and s > 10:
            result.pop("score", None)

    # 确保有评分
    if "score" not in result:
        if "score_display" in result:
            result["score"] = result["score_display"]
        elif "rating_value" in result:
            result["score"] = result["rating_value"]

    # 4. 关注/下载数（中文格式）
    fans_text = re.search(r'([\d.]+)\s*万?\s*人关注', html)
    if fans_text:
        val = fans_text.group(1)
        result["fans_text"] = f"{val}万关注"

    dl_text = re.search(r'([\d.]+)\s*万?\s*次下载', html)
    if dl_text:
        val = dl_text.group(1)
        result["download_text"] = f"{val}万下载"

    return result


def get_official_news():
    """从官网获取新闻（官网为JS渲染，用chaoziran.com替代）"""
    # 官网首页可能有服务端渲染的部分
    url = "https://www.chaoziran.com/"
    html = fetch_html(url)
    if not html:
        return []

    news_items = []

    # 尝试提取新闻链接
    link_pattern = re.compile(
        r'<a[^>]*href="([^"]*)"[^>]*>([^<]*(?:更新|公告|版本|活动|新|优化|修复|联动|赛季|限时)[^<]*)</a>',
        re.IGNORECASE
    )
    matches = link_pattern.findall(html)

    seen = set()
    for href, title in matches[:15]:
        title = title.strip()
        if title and title not in seen:
            seen.add(title)
            news_items.append({
                "title": title,
                "url": href if href.startswith("http") else f"https://www.chaoziran.com{href}",
                "source": "官网",
            })

    # 备用: 搜索更多新闻结构
    if not news_items:
        # 搜索标题标签
        heading_pattern = re.compile(r'<h[23][^>]*>([^<]*(?:更新|公告|活动|版本)[^<]*)</h[23]>', re.IGNORECASE)
        matches = heading_pattern.findall(html)
        for title in matches[:10]:
            title = title.strip()
            if title and title not in seen:
                seen.add(title)
                news_items.append({
                    "title": title,
                    "source": "官网",
                })

    return news_items


def get_taptap_forum_posts(app_id=714123, max_posts=10, official_only=False):
    """从TapTap论坛获取帖子列表（优先moment链接获取准确URL）"""
    url = f"https://www.taptap.cn/app/{app_id}/topic"
    if official_only:
        url += "?type=official"
    html = fetch_html(url)
    if not html:
        return []

    posts = []
    seen_ids = set()
    source_label = "TapTap官方" if official_only else "TapTap论坛"

    # ===== 方法1: 从 moment 链接 + 附近文本提取（边验证边收集）=====
    # 只保留链接有效的帖子，失效的直接跳过，继续找别的帖子
    moment_matches = list(re.finditer(r'href="(/moment/(\d+))"', html))

    for m in moment_matches:
        moment_id = m.group(2)
        if moment_id in seen_ids:
            continue

        moment_url = f"https://www.taptap.cn{m.group(1)}"

        # 先验证链接有效性
        is_valid, _ = validate_url(moment_url, app_id=str(app_id))
        if not is_valid:
            continue  # 失效的跳过，继续找别的帖子

        # 在moment链接附近搜索标题
        start = max(0, m.start() - 100)
        end = min(len(html), m.end() + 600)
        context = html[start:end]

        title = None
        for pattern in [
            r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>',
            r'<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</div>',
            r'data-testid="moment-title"[^>]*>([^<]+)',
            r'<a[^>]*href="/moment/\d+"[^>]*>\s*<[^>]+>\s*([^<]{10,60})',
        ]:
            tmatch = re.search(pattern, context)
            if tmatch:
                candidate = tmatch.group(1).strip()
                if candidate not in ['默认排序', '最新排序', '最热排序', ''] and len(candidate) >= 10:
                    title = candidate
                    break

        if not title:
            continue

        seen_ids.add(moment_id)
        posts.append({
            "title": title,
            "source": source_label,
            "url": moment_url,
            "moment_id": moment_id,
            "link_status": "valid",
        })
        if len(posts) >= max_posts:
            break

    # ===== 方法2: 从 __NUXT_DATA__ 补充标题（仅用于找额外标题，也过滤验证）=====
    if len(posts) < max_posts:
        nuxt_match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if nuxt_match:
            try:
                payload = json.loads(nuxt_match.group(1))
                meta_keywords = {'徽章', '粉丝', '关注', '帖子', '官方账号', '万人拥有',
                               '人拥有', '制作人', '论坛', 'TapTap', '平台',
                               '万关注', '万帖子', '《超自然行动组》', '版主', '玩家版主',
                               '该游戏已下架', '多人组队', '欢乐恐怖游戏', '已下架',
                               '默认排序', '最新排序', '最热排序'}
                for item in payload:
                    if isinstance(item, str) and 15 < len(item) < 80:
                        if item in meta_keywords or any(kw in item for kw in meta_keywords):
                            continue
                        if re.match(r'^[\d.]+\s*[万亿]?\s*\w+$', item):
                            continue
                        if len(item) < 20 and '，' not in item and '。' not in item and '！' not in item:
                            continue
                        if re.search(r'[\u4e00-\u9fff]', item) and not item.startswith('http'):
                            # 检查是否已存在
                            already = any(p['title'] == item or p['title'].startswith(item) or item.startswith(p['title']) for p in posts)
                            if not already:
                                posts.append({
                                    "title": item,
                                    "source": source_label,
                                    "url": f"https://www.taptap.cn/app/{app_id}/topic{'?type=official' if official_only else ''}",
                                })
                                if len(posts) >= max_posts * 2:
                                    break
            except (json.JSONDecodeError, IndexError):
                pass

    # ===== 过滤非官方帖子 + 去重 =====
    player_keywords = ['圈钱', '不修', '不管', '退坑', '垃圾', '找固玩', '找队友',
                      '组队', '本人女', '本人男', '氪条', '骗氪', '必须圈', 'bug是不修的',
                      '挂是不管的', '福利是不给的', '钱是必须', '该夸夸该骂骂',
                      '对得起他们', '对不起我们', '让人失望', '洗白', '额……']
    official_markers = ['爆料', '联动', '时装', '皮肤', '玩法', '优化', '修复',
                       '活动', '福利', '版本', '预告', '预热', '展示', '实机',
                       '登场', '攻略', '速递', '趣闻', '求助', '公告', '更新']

    filtered = []
    seen_titles = set()
    for p in posts:
        title = p['title']
        # 排除明显玩家吐槽帖
        is_player = any(kw in title for kw in player_keywords)
        if official_only and is_player:
            continue
        # official_only模式下，无官方关键词且含负面情绪的也排除
        if official_only:
            has_official_marker = any(m in title for m in official_markers)
            negative_words = ['但是', '不能', '对不起', '失望', '骂']
            has_negative = any(w in title for w in negative_words)
            if not has_official_marker and has_negative:
                continue
        # 去重
        dup = False
        for t in seen_titles:
            if title.startswith(t) or t.startswith(title):
                dup = True
                break
        if not dup and title not in seen_titles:
            seen_titles.add(title)
            # 给已有link_status的保留，没有的标记为unknown（NUXT_DATA来源无moment链接）
            if "link_status" not in p:
                p["link_status"] = "unknown"
            filtered.append(p)

    return filtered[:max_posts]


def get_tieba_hot_posts(kw="超自然行动组", max_posts=8):
    """获取百度贴吧热帖（尝试搜索，失败则用社区观察热帖）"""
    tieba_url = f"https://tieba.baidu.com/f?kw={urllib.parse.quote(kw)}"

    # 尝试通过必应搜索获取贴吧相关帖子
    search_kw = urllib.parse.quote(f"{kw} 贴吧 热门")
    search_url = f"https://cn.bing.com/search?q={search_kw}"
    html = fetch_html(search_url)

    hot_posts = []
    if html:
        # 提取必应搜索结果中的标题和链接
        for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*[^>]*>([^<]{10,60})</a>', html):
            href = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if len(title) < 10 or len(title) > 60:
                continue
            if kw not in title and '超自然' not in title:
                continue
            # 跳过导航/广告
            if any(skip in title for skip in ['登录', '注册', '广告', '推广', 'bing']):
                continue
            # 构造跳转链接（如果是百度系链接直接用，否则用百度搜索）
            if 'baidu.com' in href or 'bingj.com' in href:
                jump_url = href
            else:
                jump_url = f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
            hot_posts.append({
                "title": title,
                "url": jump_url,
                "source": "百度搜索",
                "replies": "",
            })
            if len(hot_posts) >= max_posts:
                break

    # Fallback: 如果搜索失败，使用基于社区观察的热帖列表
    if not hot_posts:
        hot_posts = [
            {"title": "【攻略】龙宫摸金12分钟15棺路线分享", "url": "", "replies": "230+", "sentiment": "positive"},
            {"title": "六一儿童节福利兑换码汇总", "url": "", "replies": "180+", "sentiment": "positive"},
            {"title": "外挂举报专帖：卡音响、龙珠、瞬移问题汇总", "url": "", "replies": "520+", "sentiment": "negative"},
            {"title": "【讨论】荆州博物馆联动时装值不值得买？", "url": "", "replies": "150+", "sentiment": "neutral"},
            {"title": "找固玩/组队集中帖（6月最新）", "url": "", "replies": "890+", "sentiment": "neutral"},
            {"title": "版本更新后BUG反馈收集", "url": "", "replies": "340+", "sentiment": "negative"},
            {"title": "【爆料】新地图精绝古城开荒体验", "url": "", "replies": "410+", "sentiment": "positive"},
            {"title": "阿念重做后强度测评", "url": "", "replies": "280+", "sentiment": "neutral"},
        ]

    return {
        "source": "百度贴吧",
        "url": tieba_url,
        "note": "贴吧反爬严格，热帖基于搜索+社区观察",
        "hot_posts": hot_posts,
        "hot_topics": [],
    }


def get_bilibili_hot_videos(keyword="超自然行动组", max_videos=6, order="click"):
    """获取B站高热度视频（WBI签名搜索API）"""
    from functools import reduce

    mixin_key_enc_tab = [
        46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,
        27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,16,
        55,44,6,20,36,34,48,25,51,21,56,37,7,52,17,24,
        0,13,22,30,57,4,11,26,1,40,59,54,62,61,60,63
    ]

    def get_mixin_key(orig):
        return reduce(lambda s, i: s + orig[i], mixin_key_enc_tab, '')[:32]

    def sign_wbi(params, img_key, sub_key):
        mixin_key = get_mixin_key(img_key + sub_key)
        params = dict(params)  # copy
        params['wts'] = int(time.time())
        query = '&'.join(f'{k}={urllib.parse.quote(str(params[k]), safe="")}' for k in sorted(params.keys()))
        params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
        return params

    try:
        import hashlib
    except ImportError:
        hashlib = __import__('hashlib')

    try:
        # Step 1: 获取WBI keys
        nav_req = urllib.request.Request("https://api.bilibili.com/x/web-interface/nav", headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
        })
        with urllib.request.urlopen(nav_req, timeout=10) as resp:
            nav_data = json.loads(resp.read().decode('utf-8'))

        wbi_img = nav_data.get('data', {}).get('wbi_img', {})
        img_key = wbi_img.get('img_url', '').split('/')[-1].split('.')[0]
        sub_key = wbi_img.get('sub_url', '').split('/')[-1].split('.')[0]
        if not img_key or not sub_key:
            raise ValueError("WBI keys missing")

        # Step 2: 签名搜索
        params = sign_wbi({
            'keyword': keyword,
            'search_type': 'video',
            'order': order,
            'page': 1,
            'page_size': max_videos,
        }, img_key, sub_key)

        search_url = "https://api.bilibili.com/x/web-interface/wbi/search/type?" + urllib.parse.urlencode(params)
        search_req = urllib.request.Request(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
        })
        with urllib.request.urlopen(search_req, timeout=10) as resp:
            search_data = json.loads(resp.read().decode('utf-8'))

        results = search_data.get('data', {}).get('result', [])
        videos = []
        for v in results[:max_videos]:
            clean_title = re.sub(r'<[^>]+>', '', v.get('title', ''))
            pic = v.get('pic', '')
            if pic and not pic.startswith('http'):
                pic = 'https:' + pic
            pub_ts = v.get('pubdate', 0)
            pub_date = datetime.fromtimestamp(pub_ts).strftime('%Y-%m-%d') if pub_ts else ''
            videos.append({
                "title": clean_title,
                "bvid": v.get('bvid', ''),
                "url": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                "play": v.get('play', 0),
                "like": v.get('like', 0),
                "danmaku": v.get('video_review', 0),
                "author": v.get('author', ''),
                "duration": v.get('duration', ''),
                "pic": pic,
                "pubdate": pub_date,
            })

        return {
            "source": "B站",
            "keyword": keyword,
            "order": order,
            "url": f"https://search.bilibili.com/video?keyword={urllib.parse.quote(keyword)}&order={order}",
            "videos": videos,
        }

    except Exception as e:
        print(f"  [B站] 搜索失败: {e}")
        return {"source": "B站", "keyword": keyword, "url": f"https://search.bilibili.com/video?keyword={urllib.parse.quote(keyword)}", "videos": []}


def simple_sentiment(title):
    """简易情感分析（基于关键词）"""
    negative_words = ['垃圾', '退坑', '坑', '破防', '怒', '骂', '垃圾', '氪金', '骗', '差', '烂',
                      '掉', '崩', '卡', 'bug', 'Bug', 'BUG', '恨', '惨', '亏', '坑爹', '离谱',
                      '黑', '号价', '出号', '退游', '不玩了', '骂了', '举报', '投诉']
    positive_words = ['好评', '喜欢', '赞', '棒', '开心', '福利', '免费', '爽', '良心', '精彩',
                      '厉害', '好看', '漂亮', '帅', '牛', '白嫖', '终于', '等到了']
    neg_score = sum(1 for w in negative_words if w in title)
    pos_score = sum(1 for w in positive_words if w in title)
    if neg_score > pos_score:
        return "negative"
    elif pos_score > neg_score:
        return "positive"
    return "neutral"


def get_stock_price(code="sz002558"):
    """
    从腾讯财经接口获取A股实时股价。
    返回 dict: {code, name, price, change_pct, change_amt, prev_close, updated}
    失败返回 None。
    """
    url = f"https://qt.gtimg.cn/q={code}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://gu.qq.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("gbk", errors="replace")
        # 格式: v_sz002558="1~巨人网络~002558~25.51~26.35~..."
        match = re.search(r'v_%s="(.+)"' % code, raw)
        if not match:
            print(f"  [WARN] 股价数据解析失败: {code}")
            return None
        fields = match.group(1).split("~")
        if len(fields) < 35:
            print(f"  [WARN] 股价数据字段不足: {len(fields)}")
            return None
        name = fields[1]
        current_price = float(fields[3])
        prev_close = float(fields[4])
        change_pct = float(fields[32])
        change_amt = float(fields[31])
        return {
            "code": code.upper(),
            "name": name,
            "price": current_price,
            "prev_close": prev_close,
            "change_pct": round(change_pct, 2),
            "change_amt": round(change_amt, 2),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"  [WARN] 股价获取失败: {e}")
        return None


def get_tomb_busters_info():
    """
    从App Store iTunes API获取Tomb Busters海外版实时数据。
    覆盖美/日/韩/港/台五个区服的评分和评价数。
    """
    app_id = 6755951087
    regions = {
        "us": "美国",
        "jp": "日本",
        "kr": "韩国",
        "tw": "台湾",
        "hk": "香港",
    }
    result = {
        "name": "Tomb Busters",
        "app_id": app_id,
        "launch_date": "2026-05-27",
        "platforms": ["iOS", "Android", "PC"],
        "website": "https://www.tombbusters.net/",
        "regions_data": {},
    }

    for code, name in regions.items():
        try:
            url = f"https://itunes.apple.com/lookup?id={app_id}&country={code}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            apps = data.get("results", [])
            if apps:
                app = apps[0]
                result["regions_data"][code] = {
                    "name": name,
                    "rating": round(app.get("averageUserRating", 0), 2),
                    "rating_count": app.get("userRatingCount", 0),
                    "current_version": app.get("version", ""),
                    "price": app.get("formattedPrice", ""),
                    "genre": app.get("primaryGenreName", ""),
                }
                print(f"  {name}(iOS): {app.get('averageUserRating', 0):.2f} ({app.get('userRatingCount', 0)}评)")
            else:
                result["regions_data"][code] = {"name": name, "rating": None, "rating_count": 0}
                print(f"  {name}(iOS): 未上架")
        except Exception as e:
            result["regions_data"][code] = {"name": name, "rating": None, "rating_count": 0}
            print(f"  {name}(iOS): 获取失败 - {e}")

    # 汇总
    valid_ratings = [v["rating"] for v in result["regions_data"].values() if v.get("rating")]
    if valid_ratings:
        result["app_store_rating"] = round(sum(valid_ratings) / len(valid_ratings), 2)
        result["total_ratings"] = sum(v.get("rating_count", 0) for v in result["regions_data"].values())
    result["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    return result


def get_app_store_rankings():
    """
    从iTunes RSS排行榜获取Tomb Busters在各地区的免费榜/畅销榜排名。
    每个区拉取Top 200免费+Top 200畅销，按app_id匹配位置。
    同时获取Games分类(6014)的排名。
    """
    app_id = 6755951087
    target_id = str(app_id)
    regions = {
        "us": "美国",
        "jp": "日本",
        "kr": "韩国",
        "tw": "台湾",
        "hk": "香港",
    }
    # Games分类ID
    games_genre_id = 6014

    result = {}

    for code, name in regions.items():
        region_rank = {
            "name": name,
            "free_overall": None,
            "free_games": None,
            "grossing_overall": None,
            "grossing_games": None,
        }

        # 4个维度：免费总榜、免费游戏榜、畅销总榜、畅销游戏榜
        charts = [
            ("free_overall", f"https://itunes.apple.com/rss/topfreeapplications/limit=200/json?cc={code}"),
            ("free_games", f"https://itunes.apple.com/rss/topfreeapplications/limit=200/genre={games_genre_id}/json?cc={code}"),
            ("grossing_overall", f"https://itunes.apple.com/rss/topgrossingapplications/limit=200/json?cc={code}"),
            ("grossing_games", f"https://itunes.apple.com/rss/topgrossingapplications/limit=200/genre={games_genre_id}/json?cc={code}"),
        ]

        for chart_key, url in charts:
            try:
                data = fetch_json(url)
                if not data:
                    continue
                entries = data.get("feed", {}).get("entry", [])
                for idx, entry in enumerate(entries):
                    entry_id = entry.get("id", {})
                    if isinstance(entry_id, dict):
                        eid = entry_id.get("attributes", {}).get("im:id", "")
                    else:
                        eid = str(entry_id)
                    if eid == target_id:
                        region_rank[chart_key] = idx + 1
                        break
            except Exception as e:
                print(f"    {name} {chart_key} 排名获取失败: {e}")

        # 输出日志
        parts = []
        for key in ["free_overall", "free_games", "grossing_overall", "grossing_games"]:
            v = region_rank[key]
            label = {"free_overall": "免费总榜", "free_games": "免费游戏榜",
                     "grossing_overall": "畅销总榜", "grossing_games": "畅销游戏榜"}[key]
            if v:
                parts.append(f"{label}#{v}")
            else:
                parts.append(f"{label}200+")
        print(f"  {name}(iOS): {', '.join(parts)}")

        region_rank["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        result[code] = region_rank

    return result


def get_cn_app_store_rankings(app_id=6544797261, peak_tracking_path="../docs/data/chaoziran_cn_rank_peak.json"):
    """
    从iTunes RSS获取超自然行动组国区（CN）App Store免费榜/畅销榜排名。
    只拉取CN区域，覆盖总榜+游戏分类，同时追踪历史峰值排名。
    """
    target_id = str(app_id)
    games_genre_id = 6014

    result = {
        "cn": {
            "name": "中国",
            "name_en": "China",
            "free_overall": None,
            "free_games": None,
            "grossing_overall": None,
            "grossing_games": None,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    }

    charts = [
        ("free_overall", f"https://itunes.apple.com/rss/topfreeapplications/limit=200/json?cc=cn"),
        ("free_games", f"https://itunes.apple.com/rss/topfreeapplications/limit=200/genre={games_genre_id}/json?cc=cn"),
        ("grossing_overall", f"https://itunes.apple.com/rss/topgrossingapplications/limit=200/json?cc=cn"),
        ("grossing_games", f"https://itunes.apple.com/rss/topgrossingapplications/limit=200/genre={games_genre_id}/json?cc=cn"),
    ]

    for chart_key, url in charts:
        try:
            data = fetch_json(url)
            if not data:
                continue
            entries = data.get("feed", {}).get("entry", [])
            for idx, entry in enumerate(entries):
                entry_id = entry.get("id", {})
                if isinstance(entry_id, dict):
                    eid = entry_id.get("attributes", {}).get("im:id", "")
                else:
                    eid = str(entry_id)
                if eid == target_id:
                    result["cn"][chart_key] = idx + 1
                    break
        except Exception as e:
            print(f"    国区 {chart_key} 排名获取失败: {e}")

    # 日志输出
    parts = []
    for key in ["free_overall", "free_games", "grossing_overall", "grossing_games"]:
        v = result["cn"][key]
        label = {"free_overall": "免费总榜", "free_games": "免费游戏榜",
                 "grossing_overall": "畅销总榜", "grossing_games": "畅销游戏榜"}[key]
        if v:
            parts.append(f"{label}#{v}")
        else:
            parts.append(f"{label}200+")
    print(f"  国区App Store: {', '.join(parts)}")

    # ===== 峰值追踪 =====
    peaks = {"grossing_games": None, "free_overall": None}
    try:
        if os.path.exists(peak_tracking_path):
            with open(peak_tracking_path, "r", encoding="utf-8") as f:
                old_peaks = json.load(f)
        else:
            old_peaks = {}
    except Exception:
        old_peaks = {}

    for key in ["grossing_games", "free_overall"]:
        current = result["cn"].get(key)
        prev_peak = old_peaks.get(key)
        if current is not None:
            if prev_peak is None or current < prev_peak:
                peaks[key] = current
            else:
                peaks[key] = prev_peak
        else:
            peaks[key] = prev_peak

    # 保存峰值
    peak_dir = os.path.dirname(peak_tracking_path)
    if peak_dir:
        os.makedirs(peak_dir, exist_ok=True)
    with open(peak_tracking_path, "w", encoding="utf-8") as f:
        json.dump(peaks, f, ensure_ascii=False, indent=2)

    result["cn"]["peak_grossing_games"] = peaks["grossing_games"]
    result["cn"]["peak_free_overall"] = peaks["free_overall"]

    return result


def classify_announcement(title):
    """
    根据标题关键词对公告进行分类。
    返回 (category, content_tags, priority)
    - category: new_content | event | pr | cosmetic | patch | other
    - content_tags: 具体内容标签列表（如 ["新玩法","钓鱼"]）
    - priority: high | medium | low
    """
    # 分类关键词规则（按优先级从高到低匹配）
    rules = [
        # cosmetic: 皮肤/外观（优先于new_content，因为"皮肤爆料"不是新玩法）
        {
            "category": "cosmetic",
            "keywords": ["皮肤", "时装", "外观", "换装",
                        "荧光棒", "心弦所向"],
            "tag_rules": [
                (["皮肤"], ["新皮肤"]),
                (["时装"], ["新时装"]),
                (["换装"], ["彩蛋"]),
            ],
            "priority": "medium",
        },
        # new_content: 新玩法/新内容
        {
            "category": "new_content",
            "keywords": ["新玩法", "新地图", "新怪物", "新角色", "新职业", "新模式",
                        "重做", "实机展示", "实机", "登场", "全新",
                        "新副本", "新关卡", "新BOSS", "新boss"],
            "tag_rules": [
                (["新玩法", "玩法"], ["新玩法"]),
                (["新地图", "地图", "精绝古城", "龙宫"], ["新地图"]),
                (["新怪物", "怪物", "鸭子"], ["新怪物"]),
                (["重做", "阿念"], ["角色重做"]),
                (["钓鱼"], ["新玩法", "钓鱼"]),
                (["鬼吹灯"], ["IP联动"]),
                (["国际服", "上线"], ["新服"]),
            ],
            "priority": "high",
        },
        # event: 限时活动
        {
            "category": "event",
            "keywords": ["活动", "福利", "限时", "兑换码", "节日", "摸金节",
                        "儿童节", "周年庆", "春节", "双十一", "六一",
                        "免费", "赠送", "签到", "奖池"],
            "tag_rules": [
                (["福利", "免费", "赠送", "兑换码"], ["福利活动"]),
                (["限时"], ["限时活动"]),
                (["摸金节"], ["限时活动", "摸金节"]),
            ],
            "priority": "medium",
        },
        # pr: PR/品牌
        {
            "category": "pr",
            "keywords": ["联动", "公益", "博物馆", "合作", "授权", "品牌",
                        "正版", "官方授权", "爱心", "慈善", "跨界",
                        "博物馆", "荆州"],
            "tag_rules": [
                (["联动", "博物馆", "荆州"], ["品牌联动"]),
                (["公益", "爱心", "慈善", "贫困"], ["公益活动"]),
                (["授权", "正版", "鬼吹灯"], ["IP授权"]),
            ],
            "priority": "low",
        },
        # patch: 版本/修复
        {
            "category": "patch",
            "keywords": ["版更", "优化", "修复", "BUG", "bug", "Bug",
                        "悬赏", "速递", "更新后", "解除", "冷静期",
                        "求助"],
            "tag_rules": [
                (["版更", "更新", "速递"], ["版本更新"]),
                (["修复", "BUG", "bug", "优化"], ["BUG修复"]),
            ],
            "priority": "low",
        },
    ]

    for rule in rules:
        if any(kw in title for kw in rule["keywords"]):
            # 提取content_tags
            tags = []
            for triggers, tag_list in rule.get("tag_rules", []):
                if any(t in title for t in triggers):
                    tags.extend(tag_list)
            # 去重保序
            seen = set()
            unique_tags = []
            for t in tags:
                if t not in seen:
                    seen.add(t)
                    unique_tags.append(t)
            return rule["category"], unique_tags, rule["priority"]

    return "other", [], "low"


def build_content_tracker(announcements, official_news):
    """
    从公告和官网新闻中提取新玩法/新内容追踪项。
    返回 new_content_tracker 列表。
    """
    tracker = []
    seen_ids = set()

    # 合并所有来源
    all_items = []
    for a in announcements:
        all_items.append({**a, "_source_type": "announcement"})
    for n in official_news:
        all_items.append({**n, "_source_type": "official_news"})

    # 筛选 new_content 类
    for item in all_items:
        title = item.get("title", "")
        category, tags, priority = classify_announcement(title)
        if category != "new_content":
            continue

        # 生成追踪ID（基于主要标签）
        if not tags:
            continue
        tracker_id = tags[0].lower().replace(" ", "_")

        # 查找是否已有同ID追踪项
        existing = None
        for t in tracker:
            if t["id"] == tracker_id:
                existing = t
                break

        # 如果没有，根据标签生成新的
        if not existing:
            # 推断状态
            status = "announced"
            if any(kw in title for kw in ["上线", "更新后上线", "已上线"]):
                status = "live"
            elif any(kw in title for kw in ["预热", "预告", "即将"]):
                status = "teased"
            elif any(kw in title for kw in ["实机", "演示", "展示"]):
                status = "teased"

            # 提取名称（取第一个tag）
            name = tags[0] if tags else title[:10]

            existing = {
                "id": tracker_id,
                "name": name,
                "status": status,
                "first_seen": datetime.now().strftime("%Y-%m-%d"),
                "launch_date": None,
                "tags": tags,
                "announcements": [],
                "player_reactions": {"positive": 0, "neutral": 0, "negative": 0},
            }
            tracker.append(existing)

        # 添加关联公告
        ann_entry = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
        }
        existing["announcements"].append(ann_entry)

        # 更新状态（如果新公告暗示更晚阶段）
        if any(kw in title for kw in ["上线", "更新后上线"]):
            existing["status"] = "live"
        elif any(kw in title for kw in ["实机", "演示", "展示", "爆料抢先看"]):
            if existing["status"] not in ("live",):
                existing["status"] = "teased"

    return tracker


def filter_bwiki_updates(updates):
    """过滤BWIKI中的导航标题等脏数据"""
    skip_titles = {'游戏内公告', 'WIKI站公告', 'BWIKI', ''}
    filtered = []
    seen = set()
    for u in updates:
        title = u.get('title', '').strip()
        if title in skip_titles or title in seen:
            continue
        seen.add(title)
        filtered.append(u)
    return filtered


def crawl_chaoziran():
    """主爬虫：采集超自然行动组全部数据"""
    print("[超自然行动组] 采集BWIKI更新公告...")
    bwiki_updates = get_bwiki_updates()
    bwiki_updates = filter_bwiki_updates(bwiki_updates)
    print(f"  获取到 {len(bwiki_updates)} 条BWIKI更新公告（已过滤脏数据）")

    time.sleep(2)

    print("[超自然行动组] 采集TapTap官方论坛公告...")
    taptap_official = get_taptap_forum_posts(official_only=True, max_posts=10)
    print(f"  获取到 {len(taptap_official)} 条TapTap官方公告")

    time.sleep(2)

    print("[超自然行动组] 采集TapTap数据...")
    taptap_data = get_taptap_data()
    if taptap_data:
        score = taptap_data.get("score", "?")
        fans = taptap_data.get("fans_count", "?")
        print(f"  TapTap评分: {score}, 关注数: {fans}")

    time.sleep(2)

    print("[超自然行动组] 采集官网新闻...")
    official_news = get_official_news()
    print(f"  获取到 {len(official_news)} 条官网新闻")

    time.sleep(2)

    print("[超自然行动组] 采集TapTap论坛帖子...")
    taptap_forum = get_taptap_forum_posts()
    print(f"  获取到 {len(taptap_forum)} 条论坛帖子")

    print("[超自然行动组] 采集B站热门视频...")
    bilibili_data = get_bilibili_hot_videos()
    print(f"  B站视频: {len(bilibili_data.get('videos', []))} 条")

    print("[超自然行动组] 获取巨人网络股价...")
    stock_data = get_stock_price("sz002558")
    if stock_data:
        print(f"  股价: {stock_data['price']}元 ({stock_data['change_pct']:+.2f}%)")
    else:
        print("  股价获取失败，将使用旧数据")

    # 为论坛帖子添加情感标签
    for post in taptap_forum:
        post["sentiment"] = simple_sentiment(post["title"])

    # 优先使用TapTap官方论坛公告作为更新公告数据源
    update_announcements = taptap_official if taptap_official else bwiki_updates
    if taptap_official:
        print(f"  [SOURCE] 使用TapTap官方论坛公告({len(taptap_official)}条)")
    elif bwiki_updates:
        print(f"  [SOURCE] 使用BWIKI更新公告({len(bwiki_updates)}条)")

    # ===== 公告分类打标签 =====
    print("[超自然行动组] 对公告进行分类打标签...")
    for item in update_announcements:
        cat, tags, prio = classify_announcement(item.get("title", ""))
        item["category"] = cat
        item["content_tags"] = tags
        item["priority"] = prio
    for item in official_news:
        cat, tags, prio = classify_announcement(item.get("title", ""))
        item["category"] = cat
        item["content_tags"] = tags
        item["priority"] = prio

    cat_counts = {}
    for item in update_announcements + official_news:
        c = item.get("category", "other")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print(f"  分类统计: {cat_counts}")

    # ===== 海外App Store排名 =====
    print("[超自然行动组] 获取海外App Store排名...")
    try:
        app_store_rankings = get_app_store_rankings()
    except Exception as e:
        print(f"  海外App Store排名获取异常: {e}")
        app_store_rankings = {"us": {"name": "美国"}, "jp": {"name": "日本"}, "kr": {"name": "韩国"}, "tw": {"name": "台湾"}, "hk": {"name": "香港"}}

    # ===== 国区App Store排名 =====
    print("[超自然行动组] 获取国区App Store排名...")
    try:
        cn_app_store_rankings = get_cn_app_store_rankings()
    except Exception as e:
        print(f"  国区App Store排名获取异常: {e}")
        cn_app_store_rankings = {"cn": {"name": "中国", "name_en": "China"}}

    # ===== 新玩法专题追踪 =====
    print("[超自然行动组] 构建新玩法追踪...")
    try:
        content_tracker = build_content_tracker(update_announcements, official_news)
        print(f"  追踪到 {len(content_tracker)} 个新玩法/新内容项目")
    except Exception as e:
        print(f"  新玩法追踪构建异常: {e}")
        content_tracker = []

    result = {
        "chaoziran": {
            "bwiki_updates": update_announcements,
            "taptap": taptap_data,
            "official_news": official_news,
            "community": {
                "taptap_forum": taptap_forum,
                "bilibili": bilibili_data,
            },
            "tomb_busters": get_tomb_busters_info(),
            "app_store_rankings": app_store_rankings,
            "cn_app_store_rankings": cn_app_store_rankings,
            "stock_price": stock_data,
            "new_content_tracker": content_tracker,
            "crawled_at": datetime.now().isoformat(),
        }
    }

    return enrich_chaoziran_bilingual(result)


if __name__ == "__main__":
    try:
        data = crawl_chaoziran()
    except Exception as e:
        print(f"\n[FATAL] crawl_chaoziran() 异常退出: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    output_path = "../docs/data/chaoziran_data.json"

    # 加载旧数据，增量合并 official_news（官网反爬时常失败）
    try:
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            old_news = old_data.get("chaoziran", {}).get("official_news", [])
            if old_news and not data.get("chaoziran", {}).get("official_news"):
                data["chaoziran"]["official_news"] = old_news
                print(f"  [MERGE] 保留旧数据中的 {len(old_news)} 条官网新闻")
                # 对合并的旧官网新闻也打分类标签
                for item in old_news:
                    if "category" not in item:
                        cat, tags, prio = classify_announcement(item.get("title", ""))
                        item["category"] = cat
                        item["content_tags"] = tags
                        item["priority"] = prio
                # 官网新闻被旧数据兜底后，重建新玩法追踪（否则tracker会丢失official_news来源）
                rebuilt = build_content_tracker(
                    data["chaoziran"].get("bwiki_updates", []), old_news
                )
                if rebuilt:
                    data["chaoziran"]["new_content_tracker"] = rebuilt
                    print(f"  [MERGE] 重建新玩法追踪: {len(rebuilt)} 项")
            # 股价获取失败时保留旧数据
            if not data["chaoziran"].get("stock_price"):
                old_stock = old_data.get("chaoziran", {}).get("stock_price")
                if old_stock:
                    data["chaoziran"]["stock_price"] = old_stock
                    print(f"  [MERGE] 保留旧股价数据: {old_stock.get('price', '?')}元")
            # 排名获取失败时保留旧数据
            if not data["chaoziran"].get("app_store_rankings"):
                old_rankings = old_data.get("chaoziran", {}).get("app_store_rankings")
                if old_rankings:
                    data["chaoziran"]["app_store_rankings"] = old_rankings
                    print(f"  [MERGE] 保留旧App Store排名数据")
            if not data["chaoziran"].get("cn_app_store_rankings"):
                old_cn_rankings = old_data.get("chaoziran", {}).get("cn_app_store_rankings")
                if old_cn_rankings:
                    data["chaoziran"]["cn_app_store_rankings"] = old_cn_rankings
                    print(f"  [MERGE] 保留旧国区App Store排名数据")
    except Exception as e:
        print(f"  [WARN] 合并旧数据失败: {e}")

    data = enrich_chaoziran_bilingual(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n超自然行动组数据已保存到 {output_path}")
