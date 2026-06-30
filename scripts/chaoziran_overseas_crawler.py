"""
超自然行动组海外数据爬虫 - 采集 Tomb Busters 国际版数据
数据源：Google Play、Reddit、YouTube、tombbusters.net 官网、X/Twitter
"""

import json
import os
import re
import urllib.request
import urllib.parse
import urllib.error
import time
from datetime import datetime


def fetch_html(url, retries=3, lang="en"):
    """带重试的HTML请求"""
    for attempt in range(retries):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": f"{lang},{lang.split('-')[0]};q=0.9,en;q=0.8",
            }
            req = urllib.request.Request(url, headers=headers)
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


def get_google_play_data(package_id="com.game.tombbusters"):
    """从Google Play获取Tomb Busters数据"""
    url = f"https://play.google.com/store/apps/details?id={package_id}"
    html = fetch_html(url, lang="en-US")
    if not html:
        return None

    result = {
        "package_id": package_id,
        "source": "Google Play",
        "url": url,
    }

    # 评分
    score_match = re.search(r'"starRating"\s*:\s*([\d.]+)', html)
    if score_match:
        result["rating"] = float(score_match.group(1))
    else:
        # 备用：从meta/aggregateRating提取
        score_alt = re.search(r'(\d\.\d)\s*(?:stars?|out of)', html)
        if score_alt:
            result["rating"] = float(score_alt.group(1))

    # 评价数
    review_match = re.search(r'"ratingsCount"\s*:\s*"?(\d+)"?', html)
    if review_match:
        result["review_count"] = int(review_match.group(1))
    else:
        review_alt = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:reviews?|ratings?)', html)
        if review_alt:
            count_str = review_alt.group(1).replace(",", "")
            try:
                result["review_count"] = int(float(count_str))
            except ValueError:
                pass

    # 下载数
    download_match = re.search(r'(\d[\d,]*(?:\+?))\s*(?:downloads?|Installs)', html, re.IGNORECASE)
    if download_match:
        result["downloads"] = download_match.group(1).strip()

    # 版本号
    version_match = re.search(r'Current Version[^<]*<[^>]*>([^<]+)', html)
    if version_match:
        result["version"] = version_match.group(1).strip()

    # 更新日期
    updated_match = re.search(r'Updated on[^<]*<[^>]*>([^<]+)', html)
    if updated_match:
        result["updated"] = updated_match.group(1).strip()

    # 开发者
    dev_match = re.search(r'Offered by[^<]*<[^>]*>([^<]+)', html)
    if dev_match:
        result["developer"] = dev_match.group(1).strip()

    # 描述（短）
    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
    if desc_match:
        result["description"] = desc_match.group(1)[:300]

    # 排名（免费榜位置）
    rank_match = re.search(r'#(\d+)\s*(?:Free|Top Free|in )', html)
    if rank_match:
        result["free_rank"] = int(rank_match.group(1))

    # 分类
    cat_match = re.search(r'/store/apps/category/(\w+)', html)
    if cat_match:
        result["category"] = cat_match.group(1)

    result["crawled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"  Google Play: 评分={result.get('rating', '?')}, 评价={result.get('review_count', '?')}, 下载={result.get('downloads', '?')}")
    return result


def get_reddit_posts(query="Tomb Busters game", max_posts=10):
    """从Reddit搜索Tomb Busters相关帖子（JSON API → Bing搜索备用）"""
    posts = []

    # 方法1：Reddit JSON API
    for base in ["https://old.reddit.com", "https://www.reddit.com"]:
        search_url = f"{base}/search.json?q={urllib.parse.quote(query)}&sort=new&limit={max_posts}&t=month"
        data = fetch_json(search_url)
        if data and isinstance(data, dict):
            children = data.get("data", {}).get("children", [])
            for child in children:
                post = child.get("data", {})
                title = post.get("title", "")
                if not title:
                    continue
                posts.append({
                    "title": title,
                    "subreddit": post.get("subreddit", ""),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "author": post.get("author", ""),
                    "created_utc": post.get("created_utc", 0),
                    "selftext": (post.get("selftext", "") or "")[:200],
                    "link_flair_text": post.get("link_flair_text", ""),
                })
            if posts:
                break

    # 方法2：Bing搜索Reddit帖子
    if not posts:
        print("  Reddit API被403，改用Bing搜索...")
        bing_url = f"https://www.bing.com/search?q=site%3Areddit.com+{urllib.parse.quote(query)}"
        html = fetch_html(bing_url, lang="en")
        if html:
            for m in re.finditer(r'<a[^>]*href="(https?://(?:www\.)?reddit\.com/r/[^"]+)"[^>]*>([^<]{10,120})</a>', html):
                url, title = m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip()
                # 提取subreddit
                sr_match = re.search(r'/r/(\w+)', url)
                subreddit = sr_match.group(1) if sr_match else ""
                posts.append({
                    "title": title,
                    "subreddit": subreddit,
                    "score": 0,
                    "num_comments": 0,
                    "url": url,
                    "source": "Bing Search",
                })
                if len(posts) >= max_posts:
                    break

    print(f"  Reddit: 获取到 {len(posts)} 条帖子")
    return posts


def get_youtube_videos(query="Tomb Busters game", max_videos=10):
    """从YouTube搜索Tomb Busters视频（解析搜索结果页）"""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp=CAMSAhAB"
    html = fetch_html(url, lang="en")
    if not html:
        return []

    videos = []
    # YouTube搜索结果数据在ytInitialData中
    data_match = re.search(r'var ytInitialData\s*=\s*(\{.*?\});', html)
    if data_match:
        try:
            data = json.loads(data_match.group(1))
            # 递归搜索videoRenderer
            def find_videos(obj, depth=0):
                if depth > 15:
                    return
                if isinstance(obj, dict):
                    if "videoRenderer" in obj:
                        vr = obj["videoRenderer"]
                        title = ""
                        if "title" in vr:
                            runs = vr["title"].get("runs", [])
                            if runs:
                                title = runs[0].get("text", "")
                        view_count = vr.get("viewCountText", {}).get("simpleText", "")
                        channel = vr.get("ownerText", {}).get("runs", [{}])[0].get("text", "") if vr.get("ownerText") else ""
                        published = vr.get("publishedTimeText", {}).get("simpleText", "")
                        vid_id = vr.get("videoId", "")
                        duration = vr.get("lengthText", {}).get("simpleText", "")

                        if title and vid_id:
                            videos.append({
                                "title": title,
                                "video_id": vid_id,
                                "url": f"https://www.youtube.com/watch?v={vid_id}",
                                "views": view_count,
                                "channel": channel,
                                "published": published,
                                "duration": duration,
                            })
                    for v in obj.values():
                        find_videos(v, depth + 1)
                elif isinstance(obj, list):
                    for v in obj:
                        find_videos(v, depth + 1)

            find_videos(data)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"  [WARN] YouTube数据解析失败: {e}")

    # 去重
    seen_ids = set()
    unique = []
    for v in videos:
        if v["video_id"] not in seen_ids:
            seen_ids.add(v["video_id"])
            unique.append(v)

    print(f"  YouTube: 获取到 {len(unique)} 条视频")
    return unique[:max_videos]


def get_tombbusters_news(max_items=10):
    """从tombbusters.net海外官网获取新闻"""
    url = "https://www.tombbusters.net/en"
    html = fetch_html(url, lang="en")
    if not html:
        return []

    news = []
    seen = set()

    # 尝试多种模式提取新闻/公告
    patterns = [
        # 模式1：标准新闻链接
        r'<a[^>]*href="([^"]*)"[^>]*>([^<]*(?:update|patch|event|release|new|launch|collab|season|news|notice)[^<]*)</a>',
        # 模式2：标题标签
        r'<h[23][^>]*>([^<]*(?:update|patch|event|release|new|launch|collab|season)[^<]*)</h[23]>',
        # 模式3：更宽泛的标题
        r'<a[^>]*href="(/en/[^"]*)"[^>]*class="[^"]*(?:news|post|article)[^"]*"[^>]*>([^<]+)</a>',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, html, re.IGNORECASE)
        for m in matches:
            if len(m.groups()) >= 2:
                href, title = m.group(1), m.group(2)
            else:
                href, title = "", m.group(1)

            title = title.strip()
            if not title or title in seen or len(title) < 5:
                continue
            seen.add(title)

            full_url = href if href.startswith("http") else f"https://www.tombbusters.net{href}"

            news.append({
                "title": title,
                "url": full_url,
                "source": "TombBusters.net",
            })
            if len(news) >= max_items:
                break
        if len(news) >= max_items:
            break

    # 备用：如果没提取到，尝试从script中提取
    if not news:
        ld_match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        if ld_match:
            try:
                ld_data = json.loads(ld_match.group(1))
                items = ld_data if isinstance(ld_data, list) else [ld_data]
                for item in items:
                    if isinstance(item, dict):
                        title = item.get("name", item.get("headline", ""))
                        url = item.get("url", "")
                        if title and title not in seen:
                            seen.add(title)
                            news.append({
                                "title": title,
                                "url": url,
                                "source": "TombBusters.net",
                            })
                            if len(news) >= max_items:
                                break
            except (json.JSONDecodeError, KeyError):
                pass

    print(f"  TombBusters.net: 获取到 {len(news)} 条新闻")
    return news


def get_x_mentions(username="TombBusters_EN", max_items=5):
    """从X/Twitter获取Tomb Busters最新推文（Nitter → Bing搜索备用）"""
    tweets = []

    # 方法1：Nitter实例
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]
    for instance in nitter_instances:
        url = f"{instance}/{username}"
        html = fetch_html(url, retries=1, lang="en")
        if not html:
            continue
        tweet_blocks = re.finditer(
            r'<div class="tweet-content[^"]*"[^>]*>\s*<div[^>]*>(.*?)</div>',
            html, re.DOTALL
        )
        for m in tweet_blocks:
            text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if text:
                tweets.append({
                    "text": text[:300],
                    "url": f"https://x.com/{username}",
                    "source": f"@{username}",
                })
                if len(tweets) >= max_items:
                    break
        if tweets:
            break
        time.sleep(1)

    # 方法2：Bing搜索X推文
    if not tweets:
        print("  Nitter不可用，改用Bing搜索X推文...")
        bing_url = f"https://www.bing.com/search?q=site%3Ax.com+{urllib.parse.quote(username)}+Tomb+Busters"
        html = fetch_html(bing_url, lang="en")
        if html:
            for m in re.finditer(r'<a[^>]*href="(https?://(?:x\.com|twitter\.com)/[^"]+)"[^>]*>([^<]{10,200})</a>', html):
                url, title = m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip()
                if title and 'Tomb Buster' in (title + url):
                    tweets.append({
                        "text": title[:300],
                        "url": url,
                        "source": f"@{username}",
                    })
                    if len(tweets) >= max_items:
                        break

    if not tweets:
        tweets = [{
            "text": f"Follow @{username} on X for the latest Tomb Busters updates",
            "url": f"https://x.com/{username}",
            "source": f"@{username}",
        }]

    print(f"  X/Twitter @{username}: 获取到 {len(tweets)} 条推文")
    return tweets


def get_app_store_more_regions(app_id=6755951087):
    """从更多国家/地区的App Store获取数据（扩展现有5国→10国）"""
    regions = {
        "us": "美国",
        "jp": "日本",
        "kr": "韩国",
        "tw": "台湾",
        "hk": "香港",
        "gb": "英国",
        "de": "德国",
        "fr": "法国",
        "au": "澳大利亚",
        "sg": "新加坡",
        "th": "泰国",
        "br": "巴西",
    }

    result = {}
    for code, name in regions.items():
        try:
            url = f"https://itunes.apple.com/lookup?id={app_id}&country={code}"
            data = fetch_json(url)
            if data and data.get("results"):
                app = data["results"][0]
                result[code] = {
                    "name": name,
                    "rating": round(app.get("averageUserRating", 0), 2),
                    "rating_count": app.get("userRatingCount", 0),
                    "current_version": app.get("version", ""),
                    "price": app.get("formattedPrice", ""),
                    "genre": app.get("primaryGenreName", ""),
                }
                r = result[code]
                print(f"  {name}(iOS): {r['rating']} ({r['rating_count']}评)")
            else:
                result[code] = {"name": name, "rating": None, "rating_count": 0}
        except Exception as e:
            result[code] = {"name": name, "rating": None, "rating_count": 0}
            print(f"  {name}(iOS): 获取失败 - {e}")

    return result


def get_google_play_reviews(package_id="com.game.tombbusters", max_reviews=5):
    """从Google Play页面提取最近评价摘要（非API，解析页面）"""
    url = f"https://play.google.com/store/apps/details?id={package_id}&showAllReviews=true"
    html = fetch_html(url, lang="en")
    if not html:
        return []

    reviews = []
    # Google Play评价在页面中以JSON-LD或特定结构存在
    # 尝试提取评价块
    review_blocks = re.finditer(
        r'"reviewText"\s*:\s*"([^"]{20,300})"', html
    )
    for m in review_blocks:
        text = m.group(1).encode().decode("unicode_escape", errors="replace")
        reviews.append({"text": text, "source": "Google Play"})
        if len(reviews) >= max_reviews:
            break

    if not reviews:
        # 备用：从页面HTML结构中提取
        review_html = re.finditer(
            r'<span[^>]*jsname="[^"]*"[^>]*>([^<]{20,300})</span>',
            html
        )
        seen = set()
        for m in review_html:
            text = m.group(1).strip()
            if text not in seen and len(text) > 20:
                seen.add(text)
                reviews.append({"text": text, "source": "Google Play"})
                if len(reviews) >= max_reviews:
                    break

    print(f"  Google Play评价: {len(reviews)} 条")
    return reviews


def crawl_overseas():
    """主函数：采集超自然行动组全部海外数据"""
    print("=" * 50)
    print("[Tomb Busters 海外] 开始采集海外数据")
    print("=" * 50)

    result = {}

    # 1. Google Play
    print("\n[1/6] 采集Google Play数据...")
    result["google_play"] = get_google_play_data()
    time.sleep(2)

    # 2. Google Play评价
    print("\n[2/6] 采集Google Play评价...")
    result["google_play_reviews"] = get_google_play_reviews()
    time.sleep(2)

    # 3. Reddit
    print("\n[3/6] 采集Reddit讨论...")
    result["reddit"] = get_reddit_posts()
    time.sleep(2)

    # 4. YouTube
    print("\n[4/6] 采集YouTube视频...")
    result["youtube"] = get_youtube_videos()
    time.sleep(2)

    # 5. TombBusters.net官网
    print("\n[5/6] 采集TombBusters.net新闻...")
    result["official_news_en"] = get_tombbusters_news()
    time.sleep(2)

    # 6. X/Twitter
    print("\n[6/6] 采集X/Twitter动态...")
    result["twitter"] = get_x_mentions()

    # 7. App Store扩展区域
    print("\n[补充] 采集更多App Store区域...")
    result["app_store_extended"] = get_app_store_more_regions()

    result["crawled_at"] = datetime.now().isoformat()
    result["crawled_date"] = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'=' * 50}")
    print(f"[Tomb Busters 海外] 采集完成 {datetime.now().isoformat()}")
    print(f"{'=' * 50}")

    return result


if __name__ == "__main__":
    data = crawl_overseas()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "data", "chaoziran_overseas.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n海外数据已保存到 {output_path}")
