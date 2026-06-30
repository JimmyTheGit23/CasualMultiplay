"""
链接有效性验证脚本 - 检查JSON数据中所有链接，标记失效链接
可作为爬虫后处理步骤运行，也可独立运行
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# Windows控制台编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def check_url(url, timeout=8):
    """
    验证URL是否有效。
    返回: 'valid' | 'invalid' | 'unknown'
    """
    if not url or not url.startswith('http'):
        return 'unknown'

    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })
        opener = urllib.request.build_opener()
        with opener.open(req, timeout=timeout) as resp:
            status = resp.getcode()
            final_url = resp.geturl()

            # 检查是否被重定向到论坛首页
            if '/topic' in final_url and '/moment/' not in final_url and '/moment/' in url:
                return 'invalid'

            if status in (200, 301, 302, 307, 308):
                return 'valid'
            return 'invalid'
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 'invalid'
        # 403可能是反爬，不确定失效
        return 'unknown'
    except Exception:
        return 'unknown'


def validate_data_file(filepath):
    """验证单个JSON数据文件中的所有链接"""
    print(f"\n🔍 验证链接: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = {'valid': 0, 'invalid': 0, 'unknown': 0, 'unchanged': 0}
    changes = []

    # 递归查找所有含url/link_status的对象
    def walk(obj, path=''):
        if isinstance(obj, dict):
            if 'url' in obj and obj['url']:
                url = obj['url']
                old_status = obj.get('link_status', 'unknown')

                # 只验证TapTap moment链接和官网链接（其他来源太杂）
                should_validate = (
                    '/moment/' in url or
                    'chaoziran.com' in url or
                    'store.steampowered.com' in url
                )

                if should_validate and old_status != 'valid':
                    # 之前不是valid的重新验证
                    new_status = check_url(url)
                    if new_status != old_status:
                        obj['link_status'] = new_status
                        changes.append(f"  {path}: {old_status} → {new_status} ({url})")
                    stats[new_status] = stats.get(new_status, 0) + 1
                elif old_status == 'valid':
                    # 之前valid的，抽查验证（防止后来失效）
                    # 每5个验证1个，减少请求量
                    if stats['valid'] % 5 == 0:
                        new_status = check_url(url)
                        if new_status == 'invalid':
                            obj['link_status'] = 'invalid'
                            changes.append(f"  {path}: valid → invalid ({url})")
                            stats['invalid'] += 1
                        else:
                            stats['valid'] += 1
                    else:
                        stats['valid'] += 1
                        stats['unchanged'] += 1
                else:
                    stats[old_status] = stats.get(old_status, 0) + 1

            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    walk(data)

    # 保存结果
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ valid: {stats['valid']} | ❌ invalid: {stats['invalid']} | ❓ unknown: {stats['unknown']} | ⏭️ unchanged: {stats['unchanged']}")
    if changes:
        print(f"  变更 ({len(changes)}):")
        for c in changes[:10]:
            print(c)
        if len(changes) > 10:
            print(f"  ... 还有 {len(changes)-10} 条变更")
    else:
        print("  无变更")

    return stats


if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data')

    # 验证所有JSON文件
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    total_stats = {'valid': 0, 'invalid': 0, 'unknown': 0, 'unchanged': 0}

    for jf in sorted(json_files):
        filepath = os.path.join(data_dir, jf)
        stats = validate_data_file(filepath)
        for k in total_stats:
            total_stats[k] += stats.get(k, 0)
        time.sleep(2)  # 文件间间隔

    print(f"\n📊 总计: valid={total_stats['valid']} invalid={total_stats['invalid']} unknown={total_stats['unknown']} unchanged={total_stats['unchanged']}")
