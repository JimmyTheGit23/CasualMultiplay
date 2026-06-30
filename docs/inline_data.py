import os

base = os.path.dirname(os.path.abspath(__file__))

# Read JSON files
with open(os.path.join(base, 'data', 'steam_data.json'), 'r', encoding='utf-8') as f:
    steam_json = f.read().strip()
with open(os.path.join(base, 'data', 'chaoziran_data.json'), 'r', encoding='utf-8') as f:
    czr_json = f.read().strip()
with open(os.path.join(base, 'data', 'history.json'), 'r', encoding='utf-8') as f:
    hist_json = f.read().strip()

# Read HTML
html_path = os.path.join(base, 'index.html')
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

if 'INLINE_STEAM_DATA' in html:
    print('Already inlined, skipping')
    exit(0)

# Build inline data block (insert before data loading section)
marker = '// ========== 数据加载 =========='
if marker not in html:
    print('Marker not found')
    exit(1)

inline_block = f'''<script>
        // ========== 内联数据（用于 file:// 协议本地查看）==========
        const INLINE_STEAM_DATA = {steam_json};
        const INLINE_CHAOZIRAN_DATA = {czr_json};
        const INLINE_HISTORY_DATA = {hist_json};
    </script>
    <script>'''

html = html.replace(marker, inline_block + '\n        ' + marker)

# Update loadData to fallback to inline data on file:// protocol
old_load = '''async function loadData(bustCache = false) {
            const suffix = bustCache ? `?t=${Date.now()}` : '';
            try {
                const steamResp = await fetch('./data/steam_data.json' + suffix);
                steamData = await steamResp.json();
            } catch(e) {
                console.warn('Steam数据加载失败:', e);
            }

            try {
                const czrResp = await fetch('./data/chaoziran_data.json' + suffix);
                chaoziranData = await czrResp.json();
            } catch(e) {
                console.warn('超自然行动组数据加载失败:', e);
            }

            try {
                const histResp = await fetch('./data/history.json' + suffix);
                historyData = await histResp.json();
            } catch(e) {
                console.warn('历史数据加载失败:', e);
            }

            renderAll();
        }'''

new_load = '''async function loadData(bustCache = false) {
            const suffix = bustCache ? `?t=${Date.now()}` : '';
            const isFileProtocol = window.location.protocol === 'file:';

            try {
                const steamResp = await fetch('./data/steam_data.json' + suffix);
                steamData = await steamResp.json();
            } catch(e) {
                console.warn('Steam数据加载失败:', e);
                if (isFileProtocol && typeof INLINE_STEAM_DATA !== 'undefined') steamData = INLINE_STEAM_DATA;
            }

            try {
                const czrResp = await fetch('./data/chaoziran_data.json' + suffix);
                chaoziranData = await czrResp.json();
            } catch(e) {
                console.warn('超自然行动组数据加载失败:', e);
                if (isFileProtocol && typeof INLINE_CHAOZIRAN_DATA !== 'undefined') chaoziranData = INLINE_CHAOZIRAN_DATA;
            }

            try {
                const histResp = await fetch('./data/history.json' + suffix);
                historyData = await histResp.json();
            } catch(e) {
                console.warn('历史数据加载失败:', e);
                if (isFileProtocol && typeof INLINE_HISTORY_DATA !== 'undefined') historyData = INLINE_HISTORY_DATA;
            }

            renderAll();
        }'''

if old_load not in html:
    print('loadData pattern not found')
    exit(1)

html = html.replace(old_load, new_load)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Done: inlined JSON data and updated loadData()')
