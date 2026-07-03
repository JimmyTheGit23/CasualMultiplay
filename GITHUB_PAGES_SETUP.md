GitHub Pages 配置说明

本仓库的静态网站源码在 `docs/` 目录下。

GitHub Pages 设置步骤:

1. 打开 https://github.com/JimmyTheGit23/CasualMultiplay/settings/pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main"
4. Folder 选择 "/docs"
5. 点击 Save
6. 等待 1-2 分钟,访问 https://jimmythegit23.github.io/CasualMultiplay/

页面配置:
- 首页: docs/index.html
- 数据: docs/data/*.json
- 图片: docs/images/
- 脚本: docs/scripts/ (不发布,仅开发用)

注意:
- GitHub Pages 不支持 server-side,所以 fetch('./data/xxx.json') 会被当作静态文件请求,完全可行
- ECharts 和 Tailwind 通过 CDN 加载,不影响 Pages
- daily-snapshot.yml GitHub Action 会每天更新 docs/data/ 下的数据文件并 push,Pages 自动重新部署
