# Casual Multiplay Intel

休闲多人游戏聚合情报看板，覆盖合作、竞技、派对、恐怖等多人类休闲游戏品类。

## 功能

- 游戏发现页：标签筛选 + 搜索 + 排序
- 游戏详情页：Hash路由动态生成
- 排行榜：CCU / Wishlist / 好评率多维度排行
- 重点追踪：P0游戏深度分析
- 数据自动采集：每日通过 GitHub Actions 更新

## 数据来源

| 数据项 | 来源 |
|--------|------|
| CCU / 评测 / 价格 | Steam Store API |
| Followers / Wishlist排名 | SteamDB |
| Owners估算 | SteamSpy |
| iOS畅销/免费排名 | 七麦 Qimai |
| TapTap关注/评分 | TapTap |

## 技术栈

- 前端：单文件 HTML + Tailwind CSS + Chart.js
- 爬虫：Python（urllib + requests）
- 调度：GitHub Actions 每日自动运行
- 部署：GitHub Pages

## 目录结构

```
├── docs/                    # GitHub Pages 源
│   ├── index.html           # 主页面
│   ├── data/                # JSON 数据
│   └── images/              # 图片资源
├── scripts/                 # Python 爬虫
│   ├── main_crawler.py      # 主调度
│   ├── game_registry.json   # 游戏注册表
│   └── *.py                 # 各数据源爬虫
└── .github/workflows/       # GitHub Actions
```

## 本地运行

```bash
# 运行爬虫
cd scripts
python main_crawler.py

# 本地预览
cd docs
python -m http.server 8000
```
