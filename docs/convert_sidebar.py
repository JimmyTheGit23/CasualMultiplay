#!/usr/bin/env python3
"""Convert top navigation to fixed left sidebar with ScrollSpy."""

import re

BASE = 'c:/Users/alucardzhou/WorkBuddy/20260527101502/horror-intel-dashboard/docs'
with open(f'{BASE}/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ═══════════════════════════════════════════════════════
# 1. Add sidebar CSS variables and styles
# ═══════════════════════════════════════════════════════
sidebar_css = '''
        /* ══════════════════════════════════════════════════
           LEFT SIDEBAR LAYOUT
           Fixed 260px sidebar + scrollable content
        ══════════════════════════════════════════════════ */
        :root {
            --sidebar-w: 260px;
        }

        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            width: var(--sidebar-w);
            height: 100vh;
            z-index: 100;
            display: flex;
            flex-direction: column;
            background: #FFFFFF;
            border-right: 1px solid rgba(0,0,0,0.04);
            box-shadow: 1px 0 4px rgba(0,0,0,0.02);
        }

        .sidebar-header {
            background: var(--bg-nav);
            padding: 20px 20px 16px;
            flex-shrink: 0;
        }

        .sidebar-body {
            flex: 1;
            padding: 16px 0;
            overflow-y: auto;
        }

        .sidebar-section-label {
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-ghost);
            padding: 8px 20px 6px;
        }

        .sidebar-nav-item {
            position: relative;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 11px 20px;
            font-size: 13px;
            font-weight: 400;
            color: #4B5563;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            border-left: 3px solid transparent;
            margin: 1px 0;
        }

        .sidebar-nav-item:hover {
            color: #1E293B;
            background: rgba(0,0,0,0.02);
        }

        .sidebar-nav-item.active {
            color: #0F172A;
            font-weight: 600;
            background: rgba(153,27,27,0.04);
            border-left-color: var(--accent);
        }

        .sidebar-nav-item .nav-icon {
            width: 18px;
            height: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            opacity: 0.6;
            flex-shrink: 0;
        }

        .sidebar-nav-item.active .nav-icon {
            opacity: 1;
        }

        .sidebar-footer {
            padding: 12px 20px;
            border-top: 1px solid rgba(0,0,0,0.04);
            flex-shrink: 0;
        }

        .main-content {
            margin-left: var(--sidebar-w);
            min-height: 100vh;
        }

        /* Hide the old top nav and tab bar */
        .top-nav-bar, .top-tab-bar { display: none !important; }

'''

# Insert sidebar CSS before the closing </style> tag
html = html.replace('</style>', sidebar_css + '</style>')

# ═══════════════════════════════════════════════════════
# 2. Replace old <nav> and tab bar with sidebar HTML
# ═══════════════════════════════════════════════════════

# Mark old nav for CSS hiding (add classes)
html = html.replace(
    '<nav class="sticky top-0 z-50"',
    '<nav class="top-nav-bar sticky top-0 z-50"'
)
html = html.replace(
    '<div class="max-w-7xl mx-auto px-6 pt-5">\n        <div class="flex gap-1 border-b"',
    '<div class="top-tab-bar max-w-7xl mx-auto px-6 pt-5">\n        <div class="flex gap-1 border-b"'
)

# Add sidebar HTML right after <body>
sidebar_html = '''
    <!-- ═════════════════════ LEFT SIDEBAR ═════════════════════ -->
    <aside class="sidebar">
        <!-- Dark Header Anchor -->
        <div class="sidebar-header">
            <div class="flex items-center gap-2.5 mb-1">
                <div class="w-2 h-2 rounded-full" style="background:#991B1B;"></div>
                <h1 class="text-sm font-bold tracking-wide" style="color:#F8FAFC;" data-i18n="title">GRC恐怖多人品类情报</h1>
            </div>
            <p class="text-[10px] tracking-widest ml-[18px]" style="color:#94A3B8;" data-i18n="subtitle">恐怖撤离 / 非对称竞技</p>
            <div class="flex items-center gap-1.5 text-[11px] mt-2 ml-[18px]" style="color:#94A3B8;">
                <span class="pulse-dot w-1.5 h-1.5 rounded-full inline-block" style="background:var(--data-green);"></span>
                <span id="sidebar-last-update">--</span>
            </div>
        </div>

        <!-- White Navigation Body -->
        <div class="sidebar-body">
            <div class="sidebar-section-label" data-i18n="sidebar_nav">导航</div>

            <a href="#section-overview" class="sidebar-nav-item active" data-nav="overview" onclick="navTo('overview')">
                <span class="nav-icon">◈</span>
                <span data-i18n="tab_overview">总览</span>
            </a>
            <a href="#section-chaoziran" class="sidebar-nav-item" data-nav="chaoziran" onclick="navTo('chaoziran')">
                <span class="nav-icon" style="color:var(--accent);">◆</span>
                <span data-i18n="tab_chaoziran">超自然行动组</span>
            </a>
            <a href="#section-repo" class="sidebar-nav-item" data-nav="repo" onclick="navTo('repo')">
                <span class="nav-icon">◈</span>
                <span>R.E.P.O.</span>
            </a>
            <a href="#section-competitors" class="sidebar-nav-item" data-nav="competitors" onclick="navTo('competitors')">
                <span class="nav-icon">◈</span>
                <span data-i18n="tab_competitors">竞品对比</span>
            </a>
        </div>

        <!-- Sidebar Footer: Language + Refresh -->
        <div class="sidebar-footer">
            <div class="flex items-center gap-2">
                <button id="lang-toggle" onclick="toggleLang()" class="pill flex-1 justify-center" style="color:var(--text-muted);background:rgba(0,0,0,0.03);border:1px solid rgba(0,0,0,0.06);" title="Switch Language">EN</button>
                <button id="refresh-btn" onclick="refreshData()" class="pill flex-1 justify-center" style="color:var(--text-muted);background:rgba(0,0,0,0.03);border:1px solid rgba(0,0,0,0.06);">↻ <span data-i18n="refresh">刷新</span></button>
            </div>
        </div>
    </aside>

    <!-- ═════════════════════ MAIN CONTENT ═════════════════════ -->
    <div class="main-content">
'''

html = html.replace(
    '<body class="min-h-screen" style="color:var(--text-primary);">\n\n    <!-- 顶部导航 -->',
    '<body class="min-h-screen" style="color:var(--text-primary);">\n\n' + sidebar_html + '\n    <!-- 顶部导航 (hidden, kept for data refs) -->'
)

# ═══════════════════════════════════════════════════════
# 3. Make all tab-content sections visible + add section anchors
# ═══════════════════════════════════════════════════════

# Replace tab-content divs: remove hidden, add section ids for scroll targets
# Overview
html = html.replace(
    '<div id="tab-overview" class="tab-content fade-in">',
    '<section id="section-overview" class="content-section fade-in" data-section="overview">'
)
html = html.replace(
    '<div id="tab-chaoziran" class="tab-content hidden fade-in">',
    '<section id="section-chaoziran" class="content-section fade-in" data-section="chaoziran">'
)
html = html.replace(
    '<div id="tab-repo" class="tab-content hidden fade-in">',
    '<section id="section-repo" class="content-section fade-in" data-section="repo">'
)
html = html.replace(
    '<div id="tab-competitors" class="tab-content hidden fade-in">',
    '<section id="section-competitors" class="content-section fade-in" data-section="competitors">'
)

# ═══════════════════════════════════════════════════════
# 4. Wrap main content and add closing div
# ═══════════════════════════════════════════════════════

# The <main> needs adjustment: remove max-w-7xl, use proper padding
html = html.replace(
    '<main class="max-w-7xl mx-auto px-6 py-8">',
    '<div class="px-8 py-8 max-w-[1200px]">'
)

# Close sections (they were divs, now sections — closing tags stay the same)
# But we need to close the main-content wrapper div

# Replace footer to be inside main-content
html = html.replace(
    '<footer class="max-w-7xl mx-auto px-6 py-8 text-center text-[11px] mt-8" style="color:var(--text-ghost);border-top:1px solid rgba(0,0,0,0.06);">',
    '<footer class="px-8 py-8 text-center text-[11px] mt-8" style="color:var(--text-ghost);border-top:1px solid rgba(0,0,0,0.06);">'
)

# Add closing div for main-content after footer
html = html.replace(
    '</footer>\n\n    <!-- 竞品卡片悬浮详情 -->',
    '</footer>\n    </div>\n\n    <!-- 竞品卡片悬浮详情 -->'
)

# ═══════════════════════════════════════════════════════
# 5. Replace switchTab() with navTo() and add ScrollSpy
# ═══════════════════════════════════════════════════════

old_switchTab = '''function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.classList.remove('tab-active');
                el.style.color = 'var(--text-muted)';
            });
            document.getElementById('tab-' + tabName).classList.remove('hidden');
            const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
            activeBtn.classList.add('tab-active');
            activeBtn.style.color = '';
        }'''

new_nav_code = '''function navTo(section) {
            const el = document.getElementById('section-' + section);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            setActiveNav(section);
        }

        function setActiveNav(section) {
            document.querySelectorAll('.sidebar-nav-item').forEach(el => {
                el.classList.remove('active');
            });
            const target = document.querySelector(`.sidebar-nav-item[data-nav="${section}"]`);
            if (target) target.classList.add('active');
        }

        // ScrollSpy: detect which section is in view
        function initScrollSpy() {
            const sections = document.querySelectorAll('.content-section');
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const section = entry.target.getAttribute('data-section');
                        setActiveNav(section);
                    }
                });
            }, {
                rootMargin: '-20% 0px -60% 0px',
                threshold: 0
            });
            sections.forEach(s => observer.observe(s));
        }

        // Keep switchTab as alias for backward compatibility
        function switchTab(tabName) { navTo(tabName); }'''

html = html.replace(old_switchTab, new_nav_code)

# ═══════════════════════════════════════════════════════
# 6. Update renderLastUpdate to also update sidebar time
# ═══════════════════════════════════════════════════════

html = html.replace(
    "document.getElementById('last-update').textContent =",
    "document.getElementById('last-update').textContent =\n                    document.getElementById('sidebar-last-update').textContent ="
)

# ═══════════════════════════════════════════════════════
# 7. Add initScrollSpy() call after DOMContentLoaded / loadData
# ═══════════════════════════════════════════════════════

# Find where renderAll is called and add initScrollSpy after
html = html.replace(
    'renderAll();\n        }',
    'renderAll();\n            initScrollSpy();\n        }'
)

# Also add it to DOMContentLoaded if it exists
html = html.replace(
    "document.addEventListener('DOMContentLoaded', () => {",
    "document.addEventListener('DOMContentLoaded', () => {\n            initScrollSpy();"
)

# ═══════════════════════════════════════════════════════
# 8. Fix back-to-top button positioning (inside main-content)
# ═══════════════════════════════════════════════════════

html = html.replace(
    'class="fixed bottom-6 right-6 z-50',
    'class="fixed bottom-6 right-6 z-40'
)

# ═══════════════════════════════════════════════════════
# 9. Add section top padding for scroll offset
# ═══════════════════════════════════════════════════════

section_padding_css = '''

        .content-section {
            padding-top: 16px;
            scroll-margin-top: 16px;
        }

        .content-section + .content-section {
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid rgba(0,0,0,0.04);
        }
'''

# Add before closing </style> (after the sidebar CSS already inserted)
html = html.replace(
    '/* Hide the old top nav and tab bar */',
    '/* Hide the old top nav and tab bar */' + section_padding_css
)

# ═══════════════════════════════════════════════════════
# 10. Add i18n key for sidebar_nav
# ═══════════════════════════════════════════════════════

html = html.replace(
    '"tab_overview":',
    '"sidebar_nav": "NAVIGATION",\n            "tab_overview":'
)

# Also add EN translation
# Find the EN section
html = html.replace(
    '"tab_overview": "Overview"',
    '"sidebar_nav": "NAVIGATION",\n            "tab_overview": "Overview"'
)

# ═══════════════════════════════════════════════════════
# 11. Close </section> tags properly (they were </div>)
# ═══════════════════════════════════════════════════════

# The sections close with </div> which is fine for HTML5
# But let's make sure the main content wrapper closes properly

# ═══════════════════════════════════════════════════════
# Write out
# ═══════════════════════════════════════════════════════
with open(f'{BASE}/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done: Converted to fixed left sidebar with ScrollSpy")
