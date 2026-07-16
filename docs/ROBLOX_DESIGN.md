# Roblox 专题设计文档

> 归档时间: 2026-07-16
> 数据源: roblox_leaderboard_pivot_full.xlsx (796 款游戏, 129 天玩家数时序)
> 状态: 设计完成, 待实施

## 1. 背景与目标

### 1.1 现状
当前 CasualMultiplay 主站聚焦 Steam 平台 34 款休闲多人游戏,以 Steam Store API + Steam 商店页面 popular_tags 为数据源,提供发现/排行榜/游戏详情/洞察/竞品对比 5 个一级菜单。

### 1.2 新需求
- 隐藏洞察和竞品对比菜单(完成)
- 基于 Roblox 排行榜数据新增独立专题
- Roblox 专题需要一级菜单显示:发现 / 排行榜 / 游戏详情
- 与 Steam 休闲多人专题**明显分割**(数据/视觉/导航三层隔离)

### 1.3 数据资产
| 字段 | 类型 | 说明 |
|---|---|---|
| placeId | int | Roblox 平台 ID |
| name | str | 游戏名(含 emoji) |
| visits | int | 总访问量 (227K ~ 84.5B) |
| peak_players | int | 峰值玩家数 (0 ~ 6.24M) |
| create_time | str | 创建时间 (2008-03 ~ Unknown) |
| 20260227 ~ 20260705 | float | 129 天每日玩家数(可能缺失) |

样本规模:796 款游戏,最近 7 天有数据 250 款。

## 2. 平台分割设计

### 2.1 顶部平台切换器
在 sidebar 顶部加一个**平台切换器**:
```
┌─────────────────────────┐
│  [Steam 休闲多人] [Roblox] │  <- 平台 tab
├─────────────────────────┤
│ ◈ 发现                   │
│ ◈ 排行榜                 │  <- 当前平台对应的导航
│ ◆ 游戏详情               │
└─────────────────────────┘
```

切换平台时:
- 整个 sidebar 导航保留 3 项(发现/排行榜/游戏详情),但底层渲染逻辑切到对应平台数据
- 顶部站点标题加平台标识:`休闲多人游戏聚合情报 — Steam` 或 `Roblox 游戏排行榜`
- URL hash 跟随切换:`#steam` / `#roblox`(便于分享链接)

### 2.2 视觉差异
- Steam 主题色:暗红 `#991B1B`(现有)
- Roblox 主题色:深紫 `#7C3AED`(明显区别于暗红)
- 切换平台时,所有强调色(标题/链接/active tab)跟着换
- Roblox 卡片用紫色调阴影,Steam 卡片保持红色调

### 2.3 数据隔离
| 平台 | registry 文件 | 数据源 |
|---|---|---|
| Steam | docs/data/game_registry.json | Steam Store API + 商店页面 |
| Roblox | docs/data/roblox_games.json | xlsx 导入 + 派生计算 |

前端用全局变量 `currentPlatform` 切换数据源,所有渲染函数检查 `currentPlatform` 决定读哪个数据。

## 3. Roblox 专题菜单设计

### 3.1 发现页(roblox_discover)
- **卡片网格**:796 款游戏,默认按 peak_players 降序
- **筛选条**:
  - 关键词搜索(name 含 emoji,需要支持模糊匹配)
  - 玩家数区间:全量 / >10K / >100K / >1M
  - 创建时间:全部 / 2024 前 / 2024-2025 / 2026 新作
  - 自动分类标签:基于 name 关键词
    - Brainrot (89 款) / Tower (47) / Escape (45) / Anime (26) / RP (24) / Simulator (19) / War (12) / Obby (11) / Tycoon (10) / Fight (8) / Murder (7) / Survival (4) / Parkour (3) / Adopt (1)
- **卡片信息**:
  - 游戏名(含 emoji)
  - placeId
  - 总访问量(visits,格式化 B/M/K)
  - 峰值玩家(peak_players)
  - 最近 7 天日均(若有数据)
  - 7 天增长率(对比 7 天前,绿涨红跌)
  - 创建时间(年份)
- **排序选项**:visits / peak_players / 最近7天日均 / 7天增长率 / 创建时间

### 3.2 排行榜页(roblox_leaderboard)
- **多维度排名 tab**:
  - 总访问量榜(visits)
  - 峰值玩家榜(peak_players)
  - 近7天活跃榜(最近7天日均)
  - 7天增长榜(7天增长率,过滤 peak_players < 1000)
  - 新晋黑马榜(创建时间在2026 + 近7天日均 > 10000)
- **每行显示**:排名 / 游戏名 / placeId / 主指标 / 副指标(创建时间、7天趋势 sparkline)
- **sparkline**:用 ECharts mini 折线图显示最近 30 天玩家数

### 3.3 游戏详情页(roblox_gamedetail)
- **游戏选择器**:搜索框 + 下拉,显示 placeId 和 name
- **基本信息卡**:
  - 游戏名(大字)
  - placeId
  - 创建时间
  - 总访问量
  - 峰值玩家
  - 最近一天玩家数
  - 7天/30天日均
  - 7天/30天增长率
- **核心图表:129 天玩家数时间序列折线图**
  - ECharts 折线图,X 轴日期,Y 轴玩家数
  - 支持缩放(dataZoom)
  - 标注 peak_players 出现的日期
  - 缺失数据用 null(折线断开)
- **派生指标卡**:
  - 7 天日均 / 30 天日均 / 全期日均
  - 7 天增长率 / 30 天增长率
  - 活跃天数 / 总采集天数
  - 峰值出现日期
- **Roblox 商店链接**:https://www.roblox.com/games/{placeId}

## 4. 数据管线设计

### 4.1 数据导入脚本
新增 `scripts/import_roblox_xlsx.py`:
- 输入:`roblox_leaderboard_pivot_full.xlsx`
- 输出:`docs/data/roblox_games.json`

### 4.2 数据结构
```json
{
  "_meta": {
    "imported_at": "2026-07-16T...",
    "source": "roblox_leaderboard_pivot_full.xlsx",
    "total_games": 796,
    "date_range": ["2026-02-27", "2026-07-05"],
    "total_days": 129
  },
  "categories": {
    "Brainrot": {"zh": "脑腐", "count": 89, "keywords": ["Brainrot"]},
    "Tower": {"zh": "塔防", "count": 47, "keywords": ["Tower", "Defence"]},
    "Escape": {"zh": "逃脱", "count": 45, "keywords": ["Escape"]},
    "Anime": {"zh": "动漫", "count": 26, "keywords": ["Anime"]},
    "RP": {"zh": "角色扮演", "count": 27, "keywords": ["RP", "Roleplay"]},
    "Simulator": {"zh": "模拟", "count": 19, "keywords": ["Simulator", "Sim"]},
    "War": {"zh": "战争", "count": 12, "keywords": ["War"]},
    "Obby": {"zh": "跑酷", "count": 11, "keywords": ["Obby"]},
    "Tycoon": {"zh": "大亨", "count": 10, "keywords": ["Tycoon"]},
    "Fight": {"zh": "格斗", "count": 8, "keywords": ["Fight", "Battles"]},
    "Murder": {"zh": "推理", "count": 7, "keywords": ["Murder"]},
    "Survival": {"zh": "生存", "count": 4, "keywords": ["Survival"]},
    "Parkour": {"zh": "跑酷", "count": 3, "keywords": ["Parkour"]},
    "Adopt": {"zh": "养成", "count": 1, "keywords": ["Adopt"]}
  },
  "games": [
    {
      "placeId": 4924922222,
      "name": "Brookhaven 🏡RP",
      "visits": 84568861790,
      "peak_players": 962461,
      "create_time": "2020-04-21",
      "create_year": 2020,
      "categories": ["RP"],
      "daily_players": {
        "2026-02-27": 580000,
        "2026-02-28": 620000,
        ...
      },
      "latest_players": 719085,
      "latest_date": "2026-07-05",
      "avg_7d": 651000,
      "avg_30d": 632000,
      "growth_7d": 5.2,
      "growth_30d": -2.1,
      "active_days": 129,
      "peak_date": "2026-03-15"
    }
  ]
}
```

### 4.3 派生字段计算
- `latest_players`:最近一天有数据的玩家数
- `latest_date`:最近一天日期
- `avg_7d`:最近 7 天日均(忽略 null)
- `avg_30d`:最近 30 天日均
- `growth_7d`:(latest_players - 7天前玩家数) / 7天前玩家数 * 100
- `growth_30d`:同上,30 天
- `active_days`:有数据的天数
- `peak_date`:peak_players 出现的日期
- `categories`:基于 name 关键词匹配,可能多个分类

### 4.4 DataValidator 扩展
新增 `validate_roblox_data.py` 或扩展现有 validate_data.py:
- 检查 roblox_games.json 完整性
- 检查 placeId 唯一性
- 检查 daily_players 日期连续性
- 检查数值合理性(visits > 0, peak_players >= 0)

## 5. 前端实现方案

### 5.1 文件结构
- 单文件方案(推荐):继续在 `docs/index.html` 内扩展
  - 顶部加平台切换器
  - sidebar 改为响应平台切换
  - 现有 3 个 section(overview/leaderboard/gamedetail)内加平台分支判断
- 多文件方案:`docs/roblox.html` 独立页面
  - 完全隔离,但样式/组件需复制
  - 不推荐,维护成本高

### 5.2 关键 JS 改造
```js
let currentPlatform = 'steam'; // 'steam' | 'roblox'
let robloxGamesData = null;     // Roblox 数据
let robloxCategories = null;    // Roblox 分类

function switchPlatform(platform) {
    currentPlatform = platform;
    // 更新主题色
    document.documentElement.style.setProperty('--accent', platform === 'roblox' ? '#7C3AED' : '#991B1B');
    // 重新渲染当前页面
    navTo(currentSection);
    // 更新 URL hash
    history.replaceState(null, '', '#' + platform);
}

// 在每个 render 函数开头判断平台
function renderDiscover() {
    if (currentPlatform === 'roblox') return renderRobloxDiscover();
    // 原 Steam 发现逻辑
}
```

### 5.3 ECharts 配色
- Roblox 折线图主色:`#7C3AED`
- Roblox 涨幅色:`#16A34A`(绿,中A股市色)
- Roblox 跌幅色:`#DC2626`(红)
- 背景:`#FFFFFF`
- 网格线:`#E5E7EB`

## 6. 实施步骤

### 阶段 1:数据导入(0.5 天)
1. 写 `scripts/import_roblox_xlsx.py`
2. 跑一遍生成 `docs/data/roblox_games.json`
3. 写 DataValidator 扩展检查

### 阶段 2:平台切换框架(0.5 天)
1. 顶部加平台切换器(2 个 tab)
2. 加 `switchPlatform()` 函数
3. 改 sidebar 主题色跟随平台
4. 测试切换无残留状态

### 阶段 3:Roblox 发现页(1 天)
1. 卡片网格(复用 Steam 卡片样式)
2. 筛选条(关键词 + 玩家数 + 创建时间 + 分类)
3. 排序选项
4. 卡片信息密度调优

### 阶段 4:Roblox 排行榜(0.5 天)
1. 多维度排名 tab
2. 表格行渲染
3. sparkline mini 折线图

### 阶段 5:Roblox 游戏详情(1 天)
1. 选择器
2. 基本信息卡
3. 129 天折线图(核心)
4. 派生指标卡
5. 商店链接

### 阶段 6:验证与上线(0.5 天)
1. 端到端测试(平台切换/筛选/排序/详情)
2. 响应式适配
3. DataValidator 跑通
4. push 上线

## 7. 风险与权衡

### 7.1 数据时效性
- xlsx 是 2026-07-05 截止的快照,不能每日自动更新
- Roblox 没有公开的玩家数 API,只能定期手动导入新 xlsx
- 折中:在 Roblox 页面顶部加"数据截止:2026-07-05"标识

### 7.2 分类准确性
- 基于 name 关键词分类,会有误判(如 "Tower of Hell" 是 Obby 不是 Tower)
- 折中:分类只是辅助筛选,不强求精确
- 后续可加人工标记修正

### 7.3 单文件性能
- 796 款游戏 + 129 天时序 ≈ 100K 数据点
- JSON 文件可能 1-2MB,前端加载稍慢
- 折中:首次加载显示进度,后续缓存

### 7.4 视觉一致性
- Roblox 用紫色主题,可能跟 Steam 红色形成视觉冲突
- 折中:切换平台时整页过渡 200ms,给用户清晰切换感知

## 8. 验收标准

- [ ] 洞察和竞品对比菜单已隐藏
- [ ] 顶部平台切换器可点击切换 Steam/Roblox
- [ ] 切换平台后主题色变化明显
- [ ] Roblox 发现页显示 796 款游戏卡片
- [ ] Roblox 排行榜支持 5 种维度切换
- [ ] Roblox 游戏详情页显示 129 天折线图
- [ ] 平台切换无状态残留(数据不串)
- [ ] DataValidator 通过
- [ ] GitHub Pages 部署成功
