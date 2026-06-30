#!/usr/bin/env python3
"""Convert the horror intel dashboard from Dark Mode to Premium Light Mode."""

import os, re

base = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base, 'index.html')

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# ═══════════════════════════════════════════════════════════════
# 1. CSS DESIGN TOKENS — Complete overhaul to light mode
# ═══════════════════════════════════════════════════════════════
old_root = '''        :root {
            --bg-base: #0D0E12;
            --bg-nav: #0D0E12;
            --card-bg: #16171D;
            --card-border: rgba(255,255,255,0.05);
            --card-hover-border: rgba(255,255,255,0.12);
            --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
            --card-glass: rgba(22,23,29,0.72);
            --accent: #C2410C;              /* Muted Crimson — 克制不张扬 */
            --accent-light: #EA580C;
            --accent-dim: rgba(194,65,12,0.08);
            --accent-glow: rgba(194,65,12,0.15);
            --gold: #E2B875;                /* Champagne Gold — 高级数据高亮 */
            --gold-dim: rgba(226,184,117,0.10);
            --text-primary: #FFFFFF;
            --text-secondary: #F4F4F5;
            --text-muted: #A1A1AA;
            --text-ghost: #71717A;
            --scroll-thumb: #2E2F36;
            --scroll-track: #16171D;
            --divider: rgba(255,255,255,0.06);
            --data-red: #EF4444;
            --data-green: #22C55E;
            --data-amber: #F59E0B;
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-pill: 9999px;
        }'''

new_root = '''        :root {
            --bg-base: #F4F5F7;
            --bg-nav: #0F172A;
            --card-bg: #FFFFFF;
            --card-border: rgba(0,0,0,0.06);
            --card-hover-border: rgba(0,0,0,0.12);
            --card-shadow: 0 1px 3px rgba(0,0,0,0.06);
            --card-glass: rgba(255,255,255,0.92);
            --accent: #991B1B;              /* Dark Wine Red — 克制暗示恐怖 */
            --accent-light: #B91C1C;
            --accent-dim: rgba(153,27,27,0.06);
            --accent-glow: rgba(153,27,27,0.10);
            --gold: #0F172A;                /* Dark Charcoal — 核心数据色 */
            --gold-dim: rgba(15,23,42,0.04);
            --text-primary: #1E293B;
            --text-secondary: #334155;
            --text-muted: #64748B;
            --text-ghost: #94A3B8;
            --scroll-thumb: #CBD5E1;
            --scroll-track: #F1F5F9;
            --divider: rgba(0,0,0,0.06);
            --data-red: #DC2626;
            --data-green: #16A34A;
            --data-amber: #D97706;
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-pill: 9999px;
        }'''

html = html.replace(old_root, new_root)

# ═══════════════════════════════════════════════════════════════
# 2. DESIGN TOKENS comment block
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    "DESIGN TOKENS — Premium Gaming Analytics\n           Cinematic Dark Mode · Sleek & Professional\n           Background: #0D0E12  Card: #16171D  Border: rgba(255,255,255,0.05)\n           Accent: Muted Crimson #C2410C  Gold: #E2B875\n           Text: #FFFFFF / #F4F4F5 / #A1A1AA",
    "DESIGN TOKENS — Premium Analytics Light Mode\n           Minimalist · Sleek & Professional\n           Background: #F4F5F7  Card: #FFFFFF  Border: rgba(0,0,0,0.06)\n           Accent: Dark Wine Red #991B1B  Metric: #0F172A\n           Text: #1E293B / #334155 / #64748B"
)

# ═══════════════════════════════════════════════════════════════
# 3. Body background and card styles
# ═══════════════════════════════════════════════════════════════
# Body class
html = html.replace('class="bg-dark-900 min-h-screen"', 'class="min-h-screen"')

# Glass card — add shadow, increase radius
html = html.replace(
    """        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 24px;
            transition: border-color 0.25s ease;
        }
        .glass-card:hover {
            border-color: var(--card-hover-border);
        }""",
    """        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
            transition: box-shadow 0.25s ease, border-color 0.25s ease;
        }
        .glass-card:hover {
            border-color: var(--card-hover-border);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }"""
)

# Metric card — add shadow, increase radius
html = html.replace(
    """        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 24px;
            transition: border-color 0.25s ease, transform 0.25s ease;
        }
        .metric-card:hover {
            border-color: var(--card-hover-border);
            transform: translateY(-1px);
        }""",
    """        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
            transition: box-shadow 0.25s ease, transform 0.25s ease;
        }
        .metric-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }"""
)

# Callout crimson
html = html.replace(
    """        .callout-crimson {
            border-left: 3px solid var(--accent);
            background: var(--accent-dim);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            padding: 12px 16px;
        }""",
    """        .callout-crimson {
            border-left: 3px solid var(--accent);
            background: var(--accent-dim);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            padding: 12px 16px;
            color: var(--text-muted);
        }"""
)

# Tab active — wine red underline
# Already uses var(--accent), so it will auto-update

# Score badges — light mode
html = html.replace(
    """        .score-high { background: rgba(34,197,94,0.08); color: var(--data-green); }
        .score-mid { background: var(--gold-dim); color: var(--gold); }
        .score-low { background: rgba(239,68,68,0.08); color: var(--data-red); }""",
    """        .score-high { background: rgba(22,163,74,0.08); color: var(--data-green); }
        .score-mid { background: rgba(15,23,42,0.04); color: var(--text-primary); }
        .score-low { background: rgba(220,38,38,0.08); color: var(--data-red); }"""
)

# Tooltip — light mode
html = html.replace(
    '.card-tooltip { position: fixed; z-index: 9999; pointer-events: none; max-width: 340px; min-width: 260px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); box-shadow: 0 8px 30px rgba(0,0,0,0.6); overflow: hidden; opacity: 0; transform: translateY(6px); transition: opacity 0.15s, transform 0.15s; }',
    '.card-tooltip { position: fixed; z-index: 9999; pointer-events: none; max-width: 340px; min-width: 260px; background: #FFFFFF; border: 1px solid rgba(0,0,0,0.08); border-radius: var(--radius-md); box-shadow: 0 8px 30px rgba(0,0,0,0.12); overflow: hidden; opacity: 0; transform: translateY(6px); transition: opacity 0.15s, transform 0.15s; }'
)

# Section title — dark charcoal
html = html.replace(
    """        .section-title {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.04em;
            color: var(--text-secondary);
        }""",
    """        .section-title {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.04em;
            color: var(--text-primary);
            text-transform: uppercase;
        }"""
)

# Hero overlay — light mode gradient
html = html.replace(
    ".hero-banner .hero-overlay { position: absolute; inset: 0; background: linear-gradient(to top, var(--bg-base) 0%, rgba(13,14,18,0.4) 100%); }",
    ".hero-banner .hero-overlay { position: absolute; inset: 0; background: linear-gradient(to top, #0F172A 0%, rgba(15,23,42,0.5) 100%); }"
)

# ═══════════════════════════════════════════════════════════════
# 4. Tailwind config — light mode colors
# ═══════════════════════════════════════════════════════════════
old_tw = """                    colors: {
                        dark: { 
                            900: '#0D0E12', 
                            800: '#16171D', 
                            700: '#1E1F26', 
                            600: '#0D0E12' 
                        },
                        gray: {
                            800: 'rgba(255,255,255,0.05)',
                            700: 'rgba(255,255,255,0.12)',
                            200: 'rgba(255,255,255,0.05)'
                        },
                        accent: { 
                            DEFAULT: '#C2410C', 
                            light: '#EA580C', 
                            dark: '#9A3412' 
                        },
                        gold: { DEFAULT: '#E2B875', dim: 'rgba(226,184,117,0.10)' },
                        horror: { red: '#EF4444', green: '#22C55E', orange: '#E2B875', amber: '#E2B875' }
                    }"""

new_tw = """                    colors: {
                        dark: { 
                            900: '#F4F5F7', 
                            800: '#FFFFFF', 
                            700: '#F8FAFC', 
                            600: '#0F172A' 
                        },
                        gray: {
                            800: 'rgba(0,0,0,0.06)',
                            700: 'rgba(0,0,0,0.12)',
                            200: 'rgba(0,0,0,0.04)'
                        },
                        accent: { 
                            DEFAULT: '#991B1B', 
                            light: '#B91C1C', 
                            dark: '#7F1D1D' 
                        },
                        gold: { DEFAULT: '#0F172A', dim: 'rgba(15,23,42,0.04)' },
                        horror: { red: '#DC2626', green: '#16A34A', orange: '#0F172A', amber: '#0F172A' }
                    }"""

html = html.replace(old_tw, new_tw)

# ═══════════════════════════════════════════════════════════════
# 5. Nav — Dark anchor header (keep dark, text stays light)
# ═══════════════════════════════════════════════════════════════
# Nav already uses var(--bg-nav) which is now #0F172A
# But we need to fix the nav text colors for dark bg
html = html.replace(
    'style="background:var(--bg-nav);border-bottom:1px solid var(--card-border);"',
    'style="background:var(--bg-nav);border-bottom:1px solid rgba(255,255,255,0.08);"'
)

# Nav title should stay white on dark nav
html = html.replace(
    'style="color:var(--text-primary);" data-i18n="title">GRC',
    'style="color:#FFFFFF;" data-i18n="title">GRC'
)

# Nav subtitle
html = html.replace(
    'style="color:var(--text-muted);" data-i18n="subtitle">恐怖撤离',
    'style="color:#94A3B8;" data-i18n="subtitle">恐怖撤离'
)

# Nav last-update and buttons — light on dark nav
html = html.replace(
    'class="flex items-center gap-1.5 text-xs" style="color:var(--text-muted);"\n                    <span class="pulse-dot',
    'class="flex items-center gap-1.5 text-xs" style="color:#94A3B8;"\n                    <span class="pulse-dot'
)

# Language and refresh buttons — light style on dark nav
html = html.replace(
    'style="color:var(--text-muted);background:var(--card-bg);border:1px solid var(--card-border);" title="Switch Language"',
    'style="color:#CBD5E1;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);" title="Switch Language"'
)
html = html.replace(
    'style="color:var(--text-muted);background:var(--card-bg);border:1px solid var(--card-border);">↻',
    'style="color:#CBD5E1;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);">↻'
)

# Tab bar border — light mode
html = html.replace(
    'style="border-color:var(--card-border);"\n            <button class="tab-btn tab-active',
    'style="border-color:rgba(0,0,0,0.08);"\n            <button class="tab-btn tab-active'
)

# Inactive tab buttons
html = html.replace(
    'class="tab-btn pb-3 px-4 text-xs transition shrink-0 font-medium rounded-t-lg" style="color:var(--text-muted);" data-tab="chaoziran"',
    'class="tab-btn pb-3 px-4 text-xs transition shrink-0 font-medium rounded-t-lg" style="color:var(--text-muted);" data-tab="chaoziran"'
)

# ═══════════════════════════════════════════════════════════════
# 6. Section titles — Remove emojis, use clean text
# ═══════════════════════════════════════════════════════════════
emoji_replacements = {
    '📡 最新动态': '最新动态',
    '📊 Steam 在线人数对比': 'Steam 在线人数对比',
    '🧠 AI 洞察摘要': 'AI 洞察摘要',
    '📊 国内核心指标': '国内核心指标',
    '📋 更新公告': '更新公告',
    '🎯 近3个月玩法更新': '近3个月玩法更新',
    '💬 社区舆情': '社区舆情',
    '📊 评测 & 舆论趋势': '评测 & 舆论趋势',
    '🔧 MOD 生态': 'MOD 生态',
    '🎮 基本信息': '基本信息',
    '📊 玩家数据': '玩家数据',
    '📜 版本时间线': '版本时间线',
    '📊 竞品数据对比': '竞品数据对比',
    '📈 在线人数趋势（14天）': '在线人数趋势（14天）',
    '📰 官网新闻': '官网新闻',
}

for old, new in emoji_replacements.items():
    html = html.replace(f'>{old}<', f'>{new}<')

# i18n dict — remove emojis from English values too
i18n_emoji_fixes = {
    "latest_news: { zh: '📡 最新动态'": "latest_news: { zh: '最新动态'",
    "en: '📡 Latest News'": "en: 'Latest News'",
    "steam_ccu_compare: { zh: '📊 Steam 在线人数对比'": "steam_ccu_compare: { zh: 'Steam 在线人数对比'",
    "en: '📊 Steam CCU Comparison'": "en: 'Steam CCU Comparison'",
    "ai_insight: { zh: '🧠 AI 洞察摘要'": "ai_insight: { zh: 'AI 洞察摘要'",
    "en: '🧠 AI Insight'": "en: 'AI Insight'",
    "cn_core_metrics: { zh: '📊 国内核心指标'": "cn_core_metrics: { zh: '国内核心指标'",
    "en: '📊 CN Core Metrics'": "en: 'CN Core Metrics'",
    "update_announce: { zh: '📋 更新公告'": "update_announce: { zh: '更新公告'",
    "en: '📋 Update Announcements'": "en: 'Update Announcements'",
    "content_tracker: { zh: '🎯 近3个月玩法更新'": "content_tracker: { zh: '近3个月玩法更新'",
    "en: '🎯 Content Tracker'": "en: 'Content Tracker'",
    "community_sentiment: { zh: '💬 社区舆情'": "community_sentiment: { zh: '社区舆情'",
    "en: '💬 Community Sentiment'": "en: 'Community Sentiment'",
    "review_trend: { zh: '📊 评测 & 舆论趋势'": "review_trend: { zh: '评测 & 舆论趋势'",
    "en: '📊 Review & Sentiment Trend'": "en: 'Review & Sentiment Trend'",
    "mod_eco: { zh: '🔧 MOD 生态'": "mod_eco: { zh: 'MOD 生态'",
    "en: '🔧 MOD Ecosystem'": "en: 'MOD Ecosystem'",
    "basic_info: { zh: '🎮 基本信息'": "basic_info: { zh: '基本信息'",
    "en: '🎮 Basic Info'": "en: 'Basic Info'",
    "player_data: { zh: '📊 玩家数据'": "player_data: { zh: '玩家数据'",
    "en: '📊 Player Data'": "en: 'Player Data'",
    "version_timeline: { zh: '📜 版本时间线'": "version_timeline: { zh: '版本时间线'",
    "en: '📜 Version Timeline'": "en: 'Version Timeline'",
    "competitor_compare: { zh: '📊 竞品数据对比'": "competitor_compare: { zh: '竞品数据对比'",
    "en: '📊 Competitor Compare'": "en: 'Competitor Compare'",
    "online_trend: { zh: '📈 在线人数趋势（14天）'": "online_trend: { zh: '在线人数趋势（14天）'",
    "en: '📈 Online Trend (14d)'": "en: 'Online Trend (14d)'",
    "official_news: { zh: '📰 官网新闻'": "official_news: { zh: '官网新闻'",
    "en: '📰 Official News'": "en: 'Official News'",
}
for old, new in i18n_emoji_fixes.items():
    html = html.replace(old, new)

# ═══════════════════════════════════════════════════════════════
# 7. Metric numbers — Change white/gold to dark charcoal #0F172A
# ═══════════════════════════════════════════════════════════════
# "1,000万+" — change gold span to dark charcoal
html = html.replace(
    '''<div class="text-3xl font-bold" style="color:#FFFFFF;">1,000<span class="text-lg font-medium" style="color:var(--gold);">万+</span></div>''',
    '''<div class="text-3xl font-bold" style="color:#0F172A;">1,000<span class="text-lg font-medium" style="color:#64748B;">万+</span></div>'''
)

# "10" tracking count
html = html.replace(
    '''<div class="text-3xl font-bold mt-3" style="color:var(--gold);">10</div>''',
    '''<div class="text-3xl font-bold mt-3" style="color:#0F172A;">10</div>'''
)

# "每日"
html = html.replace(
    '''<div class="text-3xl font-bold mt-3" style="color:#FFFFFF;" data-i18n="daily">每日</div>''',
    '''<div class="text-3xl font-bold mt-3" style="color:#0F172A;" data-i18n="daily">每日</div>'''
)

# R.E.P.O. CCU number
html = html.replace(
    '''<div class="text-3xl font-bold" style="color:#FFFFFF;" id="repo-ccu">--</div>''',
    '''<div class="text-3xl font-bold" style="color:#0F172A;" id="repo-ccu">--</div>'''
)

# ═══════════════════════════════════════════════════════════════
# 8. Chaoziran page specific
# ═══════════════════════════════════════════════════════════════
# Hero section TapTap score — keep dynamic, just change initial style
html = html.replace(
    'style="color:var(--gold);" id="hero-taptap-score"',
    'style="color:#0F172A;" id="hero-taptap-score"'
)
html = html.replace(
    'style="color:var(--gold);">1000万+</div>',
    'style="color:#0F172A;">1000万+</div>'
)

# FILE-001 pill — wine red
# Already uses var(--accent) and var(--accent-dim), will auto-update

# Core metrics — change white to dark charcoal
html = html.replace(
    '''<span class="font-semibold" style="color:#FFFFFF;">2亿+</span>''',
    '''<span class="font-semibold" style="color:#0F172A;">2亿+</span>'''
)
html = html.replace(
    '''<span class="font-semibold" style="color:var(--gold);">1,000万+</span>''',
    '''<span class="font-semibold" style="color:#0F172A;">1,000万+</span>'''
)
html = html.replace(
    '''<span class="font-semibold" style="color:#FFFFFF;">100万+</span>''',
    '''<span class="font-semibold" style="color:#0F172A;">100万+</span>'''
)
html = html.replace(
    '''<span class="font-semibold" style="color:var(--gold);">50亿+</span>''',
    '''<span class="font-semibold" style="color:#0F172A;">50亿+</span>'''
)
html = html.replace(
    '''<span class="font-semibold" style="color:#FFFFFF;">1,400亿次</span>''',
    '''<span class="font-semibold" style="color:#0F172A;">1,400亿次</span>'''
)

# iOS rankings — dark charcoal
html = html.replace(
    '''<span class="font-semibold" style="color:var(--gold);">#23 <span style="color:var(--text-muted);" class="text-[10px]" data-i18n="peak4">（峰值#4）</span></span>''',
    '''<span class="font-semibold" style="color:#0F172A;">#23 <span style="color:var(--text-muted);" class="text-[10px]" data-i18n="peak4">（峰值#4）</span></span>'''
)

# ═══════════════════════════════════════════════════════════════
# 9. Category tabs — remove emojis
# ═══════════════════════════════════════════════════════════════
html = html.replace('>🎮 <span data-i18n="cat_new_content">', '>\\u25C6 <span data-i18n="cat_new_content">')
html = html.replace('>🎉 <span data-i18n="cat_event">', '>\\u25C6 <span data-i18n="cat_event">')
html = html.replace('>🤝 <span data-i18n="cat_pr">', '>\\u25C6 <span data-i18n="cat_pr">')
html = html.replace('>👗 <span data-i18n="cat_cosmetic">', '>\\u25C6 <span data-i18n="cat_cosmetic">')
html = html.replace('>🔧 <span data-i18n="cat_patch">', '>\\u25C6 <span data-i18n="cat_patch">')

# Actually use simple dot markers instead
html = html.replace('\\u25C6', '·')

# ═══════════════════════════════════════════════════════════════
# 10. R.E.P.O. page specific
# ═══════════════════════════════════════════════════════════════
# R.E.P.O. hero score/CCU — already uses var(--data-green), will auto-update

# R.E.P.O. version info boxes — change white text to dark
html = html.replace(
    'style="color:var(--text-primary);">500+',
    'style="color:#0F172A;">500+'
)
html = html.replace(
    'style="color:var(--text-primary);">King of The Losers',
    'style="color:#0F172A;">King of The Losers'
)
html = html.replace(
    'style="color:var(--text-primary);">8</div>\n                        <div class="text-[10px]" style="color:var(--text-muted);">含3种法杖',
    'style="color:#0F172A;">8</div>\n                        <div class="text-[10px]" style="color:var(--text-muted);">含3种法杖'
)
html = html.replace(
    'style="color:var(--text-primary);">机械店员 + Reroller',
    'style="color:#0F172A;">机械店员 + Reroller'
)

# R.E.P.O. text-secondary inline references
html = html.replace("style='color:var(--text-secondary);'", 'style="color:var(--text-secondary);"')

# ═══════════════════════════════════════════════════════════════
# 11. Footer — light mode border
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    'style="color:var(--text-ghost);border-top:1px solid var(--card-border);"',
    'style="color:var(--text-ghost);border-top:1px solid rgba(0,0,0,0.06);"'
)

# ═══════════════════════════════════════════════════════════════
# 12. Chart.js colors — light mode
# ═══════════════════════════════════════════════════════════════
# CCU chart colors
html = html.replace(
    "const colors = ['#C2410C', '#E2B875', '#22C55E', '#EA580C', '#D4A76A'];",
    "const colors = ['#991B1B', '#0F172A', '#16A34A', '#B91C1C', '#334155'];"
)

# Chart axis grid/tick colors
html = html.replace(
    "ticks: { color: '#71717A', font: { size: 10 } },\n                            grid: { display: false },",
    "ticks: { color: '#94A3B8', font: { size: 10 } },\n                            grid: { display: false },"
)
html = html.replace(
    "ticks: { color: '#71717A', font: { size: 9 } },\n                            grid: { color: 'rgba(255,255,255,0.04)' },",
    "ticks: { color: '#94A3B8', font: { size: 9 } },\n                            grid: { color: 'rgba(0,0,0,0.04)' },"
)

# Trend chart colors
html = html.replace(
    "const colors = ['#C2410C', '#E2B875', '#22C55E', '#EA580C', '#D4A76A'];\n            const datasets = [];",
    "const colors = ['#991B1B', '#0F172A', '#16A34A', '#B91C1C', '#334155'];\n            const datasets = [];"
)

# Trend chart axis
html = html.replace(
    "labels: { color: '#9ca3af', font: { size: 11 } }",
    "labels: { color: '#64748B', font: { size: 11 } }"
)
# Replace all remaining chart grid colors
html = html.replace("grid: { color: 'rgba(255,255,255,0.04)' }", "grid: { color: 'rgba(0,0,0,0.04)' }")
html = html.replace("ticks: { color: '#71717A'", "ticks: { color: '#94A3B8'")

# ═══════════════════════════════════════════════════════════════
# 13. JS-rendered HTML — fix dark-mode specific classes
# ═══════════════════════════════════════════════════════════════
# bg-dark-900/60 → bg-gray-100
html = html.replace("bg-dark-900/60", "bg-gray-50")

# hover:bg-dark-700/30 → hover:bg-gray-50
html = html.replace("hover:bg-dark-700/30", "hover:bg-gray-50")

# hover:bg-dark-700/50 → hover:bg-gray-100
html = html.replace("hover:bg-dark-700/50", "hover:bg-gray-100")

# hover:bg-dark-700 transition → hover:bg-gray-50 transition
html = html.replace("hover:bg-dark-700 transition", "hover:bg-gray-50 transition")

# bg-dark-900/50 → bg-gray-100/50
html = html.replace("bg-dark-900/50", "bg-gray-100")

# text-white → text-slate-900 (in JS rendered content)
# Be careful — only in specific JS-rendered contexts
html = html.replace("class='text-white font-semibold'", "class='text-slate-900 font-semibold'")
html = html.replace('"text-white font-semibold"', '"text-slate-900 font-semibold"')

# bg-dark-600 → bg-gray-100 (pill/tag backgrounds)
html = html.replace("bg-dark-600", "bg-gray-100")

# text-gray-300 → text-slate-700
html = html.replace("text-gray-300", "text-slate-700")

# text-gray-500 → text-slate-500 (keep some, but update in specific contexts)
# We need to be careful — some text-gray-500 is fine for light mode

# border-gray-800 → border-gray-200
html = html.replace("border-gray-800", "border-gray-200")

# border-gray-700/30 → border-gray-200
html = html.replace("border-gray-700/30", "border-gray-200")
html = html.replace("border-gray-700/40", "border-gray-200")
html = html.replace("border-gray-700/50", "border-gray-200")

# text-gray-600 → text-slate-400 (in some contexts)
# text-gray-700 → text-slate-400
html = html.replace('"text-[10px] text-gray-700"', '"text-[10px] text-slate-400"')

# bg-dark-800/80 → bg-white
html = html.replace("bg-dark-800/80", "bg-white")

# bg-gradient-to-br from-purple-900/20 to-dark-800/80 → light wishlist style
html = html.replace(
    "bg-gradient-to-br from-purple-900/20 to-dark-800/80",
    "bg-white"
)

# from-dark-800 via-dark-800/30 → light gradient
html = html.replace(
    "from-dark-800 via-dark-800/30",
    "from-white via-white/30"
)
html = html.replace(
    "from-dark-800",
    "from-white"
)

# bg-purple-900/30 → bg-purple-50
html = html.replace("bg-purple-900/30", "bg-purple-50")

# bg-purple-900/50 → bg-purple-50
html = html.replace("bg-purple-900/50", "bg-purple-50")

# bg-yellow-900/50 → bg-yellow-50
html = html.replace("bg-yellow-900/50", "bg-yellow-50")

# bg-green-900/50 → bg-green-50
html = html.replace("bg-green-900/50", "bg-green-50")

# bg-red-900/50 → bg-red-50
html = html.replace("bg-red-900/50", "bg-red-50")

# hover:shadow-md hover:shadow-purple-900/10 → neutral shadow
html = html.replace("hover:shadow-purple-900/10", "hover:shadow-black/5")

# Game icon placeholder bg
html = html.replace(
    'class="game-icon flex items-center justify-center" style="background:var(--gold-dim);"',
    'class="game-icon flex items-center justify-center" style="background:#F1F5F9;"'
)

# R.E.P.O. icon emoji color
html = html.replace(
    'class="text-sm" style="color:var(--gold);"',
    'class="text-sm" style="color:#64748B;"'
)

# Card border hover for game icons
html = html.replace(
    'class="game-icon" style="border-color:var(--accent);"',
    'class="game-icon" style="border-color:var(--accent);"'
)

# ═══════════════════════════════════════════════════════════════
# 14. Competitor card specific light mode fixes
# ═══════════════════════════════════════════════════════════════
# Card hover text
html = html.replace("group-hover:text-accent-light", "group-hover:text-accent")
html = html.replace("group-hover:text-gray-100", "group-hover:text-slate-800")
html = html.replace("group-hover:text-gray-400", "group-hover:text-slate-600")
html = html.replace("group-hover:text-purple-300", "group-hover:text-purple-600")

# Text colors in competitor cards
html = html.replace("text-white truncate", "text-slate-900 truncate")
html = html.replace("font-bold text-xs text-white", "font-bold text-xs text-slate-900")
html = html.replace("font-bold text-sm text-white", "font-bold text-sm text-slate-900")
html = html.replace("text-xs font-bold text-white", "text-xs font-bold text-slate-900")

# ═══════════════════════════════════════════════════════════════
# 15. Tomb Busters section light mode
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    'style="color:#FFFFFF;" id="tb-regions-val"',
    'style="color:#0F172A;" id="tb-regions-val"'
)
html = html.replace(
    'style="color:#FFFFFF;">iOS / Android / PC',
    'style="color:#0F172A;">iOS / Android / PC'
)
html = html.replace(
    'style="color:#FFFFFF;" id="tb-version"',
    'style="color:#0F172A;" id="tb-version"'
)

# ═══════════════════════════════════════════════════════════════
# 16. AI daily report — remove emojis from icon spans
# ═══════════════════════════════════════════════════════════════
# These are in JS template literals, keep the emojis but they serve as icons
# Actually the user said "Remove colorful emojis from section titles; use clean, minimalist monochrome icons instead"
# But the AI report icons (📊 👑 ⭐ etc.) are inline items, not section titles.
# Section titles already cleaned above. Keep the AI insight icons as they're data markers.

# Fix AI report text colors
html = html.replace(
    '<span class="text-white font-semibold">',
    '<span class="text-slate-900 font-semibold">'
)

# ═══════════════════════════════════════════════════════════════
# 17. Version timeline dot colors
# ═══════════════════════════════════════════════════════════════
# These use var(--data-green) and var(--gold), which auto-update
# But the --gold is now #0F172A, which is too dark for a dot. Let's fix.
html = html.replace(
    "style='color:var(--gold);'",
    "style='color:#D97706;'"
)

# ═══════════════════════════════════════════════════════════════
# 18. Gold dot indicator in nav — change to wine red
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    'class="w-2 h-2 rounded-full" style="background:var(--gold);"',
    'class="w-2 h-2 rounded-full" style="background:#991B1B;"'
)

# ═══════════════════════════════════════════════════════════════
# 19. Bilibili video card bg-dark-900 → light
# ═══════════════════════════════════════════════════════════════
html = html.replace('bg-dark-900"', 'bg-gray-100"')

# ═══════════════════════════════════════════════════════════════
# 20. R.E.P.O. info/players text colors
# ═══════════════════════════════════════════════════════════════
# renderRepo uses var(--text-primary) and var(--text-secondary) which auto-update
# But some use var(--text-muted) for both label and value, need to differentiate

# ═══════════════════════════════════════════════════════════════
# 21. Back-to-top button (if exists)
# ═══════════════════════════════════════════════════════════════
# Check if there's a back-to-top button
if 'back-to-top' in html:
    html = html.replace('style="background:var(--card-bg);', 'style="background:#FFFFFF;box-shadow:0 2px 8px rgba(0,0,0,0.08);')

# ═══════════════════════════════════════════════════════════════
# 22. Ranking pill with gold color → dark charcoal
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    'style="background:var(--gold-dim);color:var(--gold);"',
    'style="background:rgba(15,23,42,0.04);color:#0F172A;"'
)

# ═══════════════════════════════════════════════════════════════
# 23. Rank color classes for light mode
# ═══════════════════════════════════════════════════════════════
# In JS: text-green-400 → text-green-600, text-red-400 → text-red-600, etc.
html = html.replace("'text-green-400'", "'text-green-600'")
html = html.replace("'text-red-400'", "'text-red-600'")
html = html.replace("'text-yellow-400'", "'text-yellow-600'")
html = html.replace("'text-orange-400'", "'text-orange-600'")
html = html.replace("'text-violet-400'", "'text-violet-600'")
html = html.replace("'text-cyan-400'", "'text-cyan-600'")
html = html.replace("'text-amber-400'", "'text-amber-700'")
html = html.replace("'text-emerald-400'", "'text-emerald-600'")
html = html.replace("'text-purple-400'", "'text-purple-600'")
html = html.replace("'text-purple-300'", "'text-purple-600'")
html = html.replace("'text-sky-400'", "'text-sky-600'")

# ═══════════════════════════════════════════════════════════════
# 24. Am/green/red backgrounds for light mode
# ═══════════════════════════════════════════════════════════════
html = html.replace("bg-amber-500/15", "bg-amber-50")
html = html.replace("bg-amber-500/10", "bg-amber-50")
html = html.replace("bg-green-500/20", "bg-green-50")
html = html.replace("bg-yellow-500/20", "bg-yellow-50")
html = html.replace("bg-pink-500/20", "bg-pink-50")
html = html.replace("bg-gray-500/20", "bg-gray-100")
html = html.replace("bg-gray-500/10", "bg-gray-50")
html = html.replace("bg-amber-500/15", "bg-amber-50")

# Green highlight backgrounds
html = html.replace("rgba(34,197,94,0.06)", "rgba(22,163,74,0.06)")
html = html.replace("rgba(34,197,94,0.08)", "rgba(22,163,74,0.08)")
html = html.replace("rgba(34,197,94,0.1)", "rgba(22,163,74,0.08)")

# Red backgrounds
html = html.replace("rgba(239,68,68,0.06)", "rgba(220,38,38,0.06)")
html = html.replace("rgba(239,68,68,0.08)", "rgba(220,38,38,0.06)")

# ═══════════════════════════════════════════════════════════════
# 25. Am/emerald/purple badge backgrounds for light
# ═══════════════════════════════════════════════════════════════
html = html.replace("bg-emerald-500/15", "bg-emerald-50")
html = html.replace("bg-amber-500/15", "bg-amber-50")
html = html.replace("bg-red-500/15", "bg-red-50")
html = html.replace("bg-purple-500/15", "bg-purple-50")
html = html.replace("bg-sky-500/15", "bg-sky-50")
html = html.replace("bg-amber-500/10", "bg-amber-50")

# ═══════════════════════════════════════════════════════════════
# 26. Border colors for badges — light mode
# ═══════════════════════════════════════════════════════════════
html = html.replace("border-emerald-500/25", "border-emerald-200")
html = html.replace("border-emerald-500/10", "border-emerald-200")
html = html.replace("border-amber-500/25", "border-amber-200")
html = html.replace("border-amber-500/15", "border-amber-200")
html = html.replace("border-red-500/25", "border-red-200")
html = html.replace("border-purple-500/25", "border-purple-200")
html = html.replace("border-purple-500/20", "border-purple-200")
html = html.replace("border-purple-500/10", "border-purple-100")
html = html.replace("border-sky-500/15", "border-sky-200")

# ═══════════════════════════════════════════════════════════════
# 27. R.E.P.O. green border-left → wine red (for consistency)
# ═══════════════════════════════════════════════════════════════
# Actually keep it green since it's R.E.P.O.'s theme. Just adjust for light mode.
html = html.replace("border-left:3px solid var(--data-green)", "border-left:3px solid #16A34A")

# ═══════════════════════════════════════════════════════════════
# 28. Score high/mid/low text colors for light mode
# ═══════════════════════════════════════════════════════════════
# These use Tailwind classes now, which should work in light mode
# score-high uses var(--data-green), score-mid uses var(--text-primary), score-low uses var(--data-red)
# All auto-update with CSS variable changes

# ═══════════════════════════════════════════════════════════════
# 29. Content tracker status badge colors for light
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    """        const trackerStatusConfig = {
            rumored:   { label_zh: '传闻', label_en: 'Rumored', color: 'text-gray-400 bg-gray-500/20' },
            announced: { label_zh: '已官宣', label_en: 'Announced', color: 'text-blue-400 bg-blue-500/20' },
            teased:    { label_zh: '预热中', label_en: 'Teased', color: 'text-yellow-400 bg-yellow-500/20' },
            live:      { label_zh: '已上线', label_en: 'Live', color: 'text-green-400 bg-green-500/20' },
            settled:   { label_zh: '稳定运营', label_en: 'Settled', color: 'text-gray-400 bg-gray-500/20' },
        };""",
    """        const trackerStatusConfig = {
            rumored:   { label_zh: '传闻', label_en: 'Rumored', color: 'text-slate-500 bg-slate-100' },
            announced: { label_zh: '已官宣', label_en: 'Announced', color: 'text-blue-700 bg-blue-50' },
            teased:    { label_zh: '预热中', label_en: 'Teased', color: 'text-amber-700 bg-amber-50' },
            live:      { label_zh: '已上线', label_en: 'Live', color: 'text-green-700 bg-green-50' },
            settled:   { label_zh: '稳定运营', label_en: 'Settled', color: 'text-slate-500 bg-slate-100' },
        };"""
)

# ═══════════════════════════════════════════════════════════════
# 30. fix remaining dark-mode artifact styles in JS
# ═══════════════════════════════════════════════════════════════
# rankColor function in JS — update for light mode
html = html.replace(
    """                            if (v <= 10) return 'text-green-400 font-bold';
                            if (v <= 50) return 'text-green-300';
                            if (v <= 100) return 'text-yellow-400';
                            if (v <= 200) return 'text-orange-400';""",
    """                            if (v <= 10) return 'text-green-700 font-bold';
                            if (v <= 50) return 'text-green-600';
                            if (v <= 100) return 'text-yellow-600';
                            if (v <= 200) return 'text-orange-600';"""
)

# ═══════════════════════════════════════════════════════════════
# 31. Remaining color fixes in renderChaoziran JS
# ═══════════════════════════════════════════════════════════════
# Ranking insight icons
html = html.replace("'<span class=\"text-green-400\">✅", "'<span class=\"text-green-700\">✅")
html = html.replace("'<span class=\"text-yellow-400\">🔄", "'<span class=\"text-amber-600\">🔄")
html = html.replace("'<span class=\"text-red-400\">⚠️", "'<span class=\"text-red-600\">⚠️")
html = html.replace("'<span class=\"text-gray-500\">⏳", "'<span class=\"text-slate-500\">⏳")
html = html.replace("'<span class=\"text-cyan-400\">🎯", "'<span class=\"text-cyan-700\">🎯")

# AI report emojis → clean monochrome dots
# Keep emojis as data markers (they're not section titles), but tone down colors
html = html.replace("text-emerald-400", "text-emerald-700")
html = html.replace("text-amber-400", "text-amber-700")

# Competitor table rateColor in JS
html = html.replace("'text-green-400'", "'text-green-700'")
html = html.replace("'text-yellow-400'", "'text-yellow-700'")
html = html.replace("'text-red-400'", "'text-red-700'")

# ═══════════════════════════════════════════════════════════════
# 32. Cat colors for light mode
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    """        const catColors = {
            new_content: { bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400', label_zh: '新玩法', label_en: 'New' },
            event:       { bg: 'bg-green-500/20', text: 'text-green-400', dot: 'bg-green-400', label_zh: '活动', label_en: 'Event' },
            pr:          { bg: 'bg-yellow-500/20', text: 'text-yellow-400', dot: 'bg-yellow-400', label_zh: 'PR', label_en: 'PR' },
            cosmetic:    { bg: 'bg-pink-500/20', text: 'text-pink-400', dot: 'bg-pink-400', label_zh: '皮肤', label_en: 'Skin' },
            patch:       { bg: 'bg-gray-500/20', text: 'text-gray-400', dot: 'bg-gray-400', label_zh: '修复', label_en: 'Patch' },
            other:       { bg: 'bg-gray-500/10', text: 'text-gray-500', dot: 'bg-gray-500', label_zh: '其他', label_en: 'Other' },
        };""",
    """        const catColors = {
            new_content: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', label_zh: '新玩法', label_en: 'New' },
            event:       { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500', label_zh: '活动', label_en: 'Event' },
            pr:          { bg: 'bg-yellow-50', text: 'text-yellow-700', dot: 'bg-yellow-500', label_zh: 'PR', label_en: 'PR' },
            cosmetic:    { bg: 'bg-pink-50', text: 'text-pink-700', dot: 'bg-pink-500', label_zh: '皮肤', label_en: 'Skin' },
            patch:       { bg: 'bg-slate-100', text: 'text-slate-500', dot: 'bg-slate-400', label_zh: '修复', label_en: 'Patch' },
            other:       { bg: 'bg-gray-50', text: 'text-gray-600', dot: 'bg-gray-400', label_zh: '其他', label_en: 'Other' },
        };"""
)

# ═══════════════════════════════════════════════════════════════
# 33. Content tracker tag colors in JS
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    "bg-amber-500/10 text-amber-300",
    "bg-amber-50 text-amber-700"
)

# ═══════════════════════════════════════════════════════════════
# 34. Wishlist card gradient → clean light
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    "hover:border-purple-400/40",
    "hover:border-purple-300"
)
html = html.replace(
    "border-purple-500/20",
    "border-purple-200"
)

# ═══════════════════════════════════════════════════════════════
# 35. Separator/divider in competitor ranking
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    "bg-gray-800",
    "bg-gray-200"
)

# ═══════════════════════════════════════════════════════════════
# 36. Tab switching — update inactive style color
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    "el.style.color = 'var(--text-muted)';",
    "el.style.color = 'var(--text-muted)';"
)

# ═══════════════════════════════════════════════════════════════
# 37. Fix any remaining inline style color:#FFFFFF references
# ═══════════════════════════════════════════════════════════════
html = html.replace('style="color:#FFFFFF;"', 'style="color:#0F172A;"')

# ═══════════════════════════════════════════════════════════════
# 38. Game icon in light mode — subtle border
# ═══════════════════════════════════════════════════════════════
# Already uses var(--card-border), will auto-update

# ═══════════════════════════════════════════════════════════════
# 39. Chaoziran game intro card — fix colors
# ═══════════════════════════════════════════════════════════════
html = html.replace(
    'class="glass-card p-3 text-xs leading-relaxed" style="color:var(--text-muted);"\n                    <span style="color:var(--accent);" class="font-medium" data-i18n="core_gameplay"',
    'class="glass-card p-3 text-xs leading-relaxed" style="color:var(--text-muted);"\n                    <span style="color:#991B1B;" class="font-medium" data-i18n="core_gameplay"'
)

# ═══════════════════════════════════════════════════════════════
# 40. Write the final file
# ═══════════════════════════════════════════════════════════════
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Done: Converted to Premium Light Mode")
print(f"File size: {len(html)} chars")
