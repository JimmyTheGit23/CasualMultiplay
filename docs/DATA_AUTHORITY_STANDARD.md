# 数据抓取权威性标准

> 本文件规定 CasualMultiplay 聚合情报站所有数字数据的来源、抓取方式、置信度分级和更新策略。所有爬虫脚本必须遵守本标准。

## 1. 数据来源分级

### 1.1 权威源（Tier S，直接采信）

| 数据类型 | 来源 | 抓取方式 | 频率 | 说明 |
|----------|------|----------|------|------|
| Steam CCU（同时在线） | Steamcharts API / Steam Store API | `store.steampowered.com/api/appdetails` | 每小时 | 官方实时数据，无需二次验证 |
| Steam 好评率 / 评测数 | Steam Store API | `store.steampowered.com/app/{appid}` HTML 解析 | 每日 | 官方页面直接展示 |
| Steam 发售日 / 开发商 / 标签 | Steam Store API | `store.steampowered.com/api/appdetails?appids={appid}` | 每周 | 官方元数据 |
| Steam 新闻 / 更新公告 | Steam News API | `api.steampowered.com/ISteamNews/GetNewsForApp/v0002/` | 每日 | 官方接口 |
| iOS 畅销榜 / 免费榜 | 七麦 Qimai API | `api.qimai.cn/rank/indexPlus/brand_id/{mode}` | 每日 | 行业公认第三方，返回 JSON |
| TapTap 排行 / 评分 | TapTap 页面 | HTML 解析 | 每周 | 国产安卓权威分发平台 |

### 1.2 高置信源（Tier A，采信但需交叉验证）

| 数据类型 | 来源 | 抓取方式 | 频率 | 验证方式 |
|----------|------|----------|------|----------|
| Steam 愿望单关注数 | SteamDB | `steamdb.info/app/{appid}/charts/` HTML 解析 | 每日 | SteamDB 为 Steam 社区最权威第三方，数据由 Steam 公开接口推算 |
| Steam 愿望单排名 | SteamDB | `steamdb.info/upcoming/mostfollowed/` | 每日 | 同上 |
| Steam 活跃度排名 | SteamDB | `steamdb.info/stats/` | 每日 | 同上 |
| Steam 历史峰值 CCU | SteamDB / Steamcharts | `steamcharts.com/app/{appid}` | 每周 | 两个站点交叉比对 |

### 1.3 参考源（Tier B，仅用于补充语境，不作为核心指标）

| 数据类型 | 来源 | 抓取方式 | 频率 | 说明 |
|----------|------|----------|------|------|
| 社区讨论热度 | Reddit / r/{game} | 官方 API `reddit.com/r/{sub}.json` | 每周 | 用于趋势判断，非硬指标 |
| 视频播放量 | YouTube Data API | `youtube.googleapis.com/youtube/v3/search` | 每周 | 搜索游戏名按播放量排序，反映传播热度 |
| 国区媒体曝光 | 百度新闻 / 微信指数 | HTML / 第三方 API | 每周 | 辅助判断国区热度 |
| 主播直播数据 | Twitch API | `api.twitch.tv/helix/streams` | 每周 | 仅 P0 游戏抓取 |

### 1.4 禁止使用的数据源

| 类型 | 原因 |
|------|------|
| 第三方数据聚合站（非 SteamDB / Qimai） | 数据来源不明，无法追溯 |
| 维基百科 / 百度百科中的数字 | 不可编辑、更新滞后 |
| 媒体文章中引用的销量数字 | 除非有官方公告背书 |
| 估算类数据（如「预计销量 X 万」） | 缺乏可验证依据 |

## 2. 字段级数据规范

每个游戏的数据必须包含以下字段，且每个字段必须标注来源：

```json
{
  "appid": 3241660,
  "name": "R.E.P.O.",
  "metrics": {
    "ccu_current": {
      "value": 12480,
      "source": "steam_api",
      "source_url": "https://store.steampowered.com/api/appdetails?appids=3241660",
      "fetched_at": "2026-06-30T18:00:00+08:00",
      "tier": "S"
    },
    "wishlist_followers": {
      "value": 180000,
      "source": "steamdb",
      "source_url": "https://steamdb.info/app/3241660/charts/",
      "fetched_at": "2026-06-30T06:00:00+08:00",
      "tier": "A"
    },
    "review_positive_pct": {
      "value": 94,
      "source": "steam_store",
      "source_url": "https://store.steampowered.com/app/3241660/",
      "fetched_at": "2026-06-30T06:00:00+08:00",
      "tier": "S"
    },
    "review_count": {
      "value": 89000,
      "source": "steam_store",
      "source_url": "https://store.steampowered.com/app/3241660/",
      "fetched_at": "2026-06-30T06:00:00+08:00",
      "tier": "S"
    }
  }
}
```

### 2.1 必须字段

| 字段 | Tier | 必须性 | 说明 |
|------|------|--------|------|
| `ccu_current` | S | P0/P1 必须 | 当前同时在线 |
| `review_positive_pct` | S | P0/P1/P2 必须 | 好评百分比 |
| `review_count` | S | P0/P1 必须 | 评测总数 |
| `wishlist_followers` | A | P0/P1 必须 | SteamDB 关注数（愿望单代理指标） |
| `release_date` | S | 全部必须 | 发售日 |
| `dev_publisher` | S | 全部必须 | 开发商/发行商 |
| `tags` | S | 全部必须 | Steam 官方标签 |

### 2.2 可选字段

| 字段 | Tier | 说明 |
|------|------|------|
| `ccu_peak_alltime` | A | 历史峰值 |
| `ccu_peak_24h` | S | 24 小时峰值 |
| `followers_rank` | A | SteamDB 关注排名 |
| `ios_rank` | S | 七麦畅销榜名次（仅 iOS 上架游戏） |
| `reddit_subscribers` | B | Reddit 社区订阅数 |
| `youtube_views_week` | B | 周视频播放量 |

## 3. 抓取流程规范

### 3.1 Steam Store API

```
GET https://store.steampowered.com/api/appdetails?appids={appid}&cc=cn&l=schinese
```

- 必须带 `cc=cn` 获取国区信息
- 必须带 `l=schinese` 获取中文
- 请求间隔 ≥ 3 秒，避免触发限流
- 失败重试 3 次，间隔指数退避

### 3.2 SteamDB HTML 抓取

```
GET https://steamdb.info/app/{appid}/charts/
Header: User-Agent: Mozilla/5.0 (compatible; CasualMultiplayBot/1.0)
```

- 仅抓取关注数（followers）和排名，不抓取估算销量
- 请求间隔 ≥ 5 秒
- 解析 `<div class="app-data">` 区块
- 若返回 403 或 Cloudflare 挑战，跳过并记录，不使用代理绕过

### 3.3 Qimai API

```
GET https://api.qimai.cn/rank/indexPlus/brand_id/{mode}
mode: 0=付费榜, 1=免费榜, 2=畅销榜
```

- 直接返回 JSON，无需加密参数
- 抓取畅销榜（mode=2）前 100 名
- 请求间隔 ≥ 10 秒
- 仅提取游戏类条目

### 3.4 Steam News API

```
GET https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=20&maxlength=300&feeds=steam_community_announcements
```

- 只抓官方公告 feed，不抓第三方新闻聚合
- 每款游戏抓取最近 20 条
- 过滤非中文且非英文的条目

## 4. 数据质量校验

### 4.1 异常检测规则

| 规则 | 处理 |
|------|------|
| CCU 环比波动 > 50% | 标记 `anomaly: true`，保留数据但加警告标记 |
| 好评率突变 > 10 个百分点 | 标记并触发人工核查 |
| 愿望单数与 SteamDB 排名矛盾 | 以 SteamDB 排名为准，修正数值 |
| 抓取值为 0 或 null | 不覆盖上次有效值，记录 `fetch_failed` |
| 发售日早于 2020 年且 CCU > 10000 | 正常（老游戏长期热门） |

### 4.2 数据新鲜度

| Tier | 最大延迟 | 超时处理 |
|------|----------|----------|
| S | 24 小时 | 标记 `stale`，页面上显示灰色「数据延迟」 |
| A | 48 小时 | 标记 `stale` |
| B | 7 天 | 可接受，不标记 |

### 4.3 页面展示规则

- 每个数字旁边必须显示来源徽章：
  - `[S]` 绿色：Steam 官方 / Qimai
  - `[A]` 蓝色：SteamDB
  - `[B]` 灰色：社区参考
- 鼠标悬停显示 `source_url` 和 `fetched_at`
- Tier B 数据默认折叠，点击展开

## 5. 更新调度

### 5.1 每日（06:00 UTC+8）

- 全部 P0 游戏的 Tier S 数据
- 全部 P0/P1 游戏的 SteamDB Tier A 数据
- Qimai iOS 畅销榜

### 5.2 每小时

- P0 游戏的 CCU（仅 Steamcharts 实时接口）

### 5.3 每周（周一 06:00 UTC+8）

- 全部 P1/P2 游戏的 Tier S 数据
- Tier B 社区参考数据
- SteamDB 历史峰值

### 5.4 触发式

- game_registry.json 更新后，立即对新加入游戏执行全量抓取
- 页面上「数据延迟」超过 48 小时，自动加入下次抓取队列

## 6. 脚本规范

### 6.1 文件命名

| 脚本 | 职责 |
|------|------|
| `scripts/main_crawler.py` | 主调度入口，按优先级和时间窗口分发任务 |
| `scripts/steam_crawler.py` | Steam Store API 抓取 |
| `scripts/steamdb_crawler.py` | SteamDB HTML 抓取（待建） |
| `scripts/qimai_crawler.py` | Qimai API 抓取（待建） |
| `scripts/steam_news_crawler.py` | Steam 官方新闻 |
| `scripts/game_discovery.py` | Steam 标签自动发现新游戏（待建） |
| `scripts/validate_links.py` | 校验 store_url 有效性 |

### 6.2 输出格式

所有爬虫输出统一存入 `docs/data/{source}_data.json`，结构：

```json
{
  "fetched_at": "2026-06-30T18:00:00+08:00",
  "source": "steam_api",
  "tier": "S",
  "games": [
    {
      "appid": 3241660,
      "metrics": { ... }
    }
  ]
}
```

### 6.3 日志

- 每次抓取写入 `docs/data/crawl_log.jsonl`
- 字段：`timestamp`, `source`, `appid`, `status`, `latency_ms`, `error`
- 失败重试必须记录原始错误信息

## 7. 数据来源变更流程

当需要新增数据来源时：

1. 在本文件 1.1-1.3 节添加来源定义，标注 Tier
2. 评估该来源的公信力（是否被行业广泛引用）
3. 在对应爬虫脚本中实现抓取逻辑
4. 更新 `game_registry.json` 的 metrics 字段结构
5. 在页面上添加对应的来源徽章

禁止未经本文件定义就引入新数据源。
