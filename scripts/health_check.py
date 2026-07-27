"""
数据健康检查 - 验证关键数据文件是否及时更新
如果 steam_data.json 超过 25 小时未更新，创建 GitHub Issue 告警
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta

STEAM_DATA = "docs/data/steam_data.json"
ROBLOX_DATA = "docs/data/roblox_games.json"
THRESHOLD_HOURS = 25


def get_file_age_hours(path):
    """获取文件最后修改时间距现在的小时数"""
    if not os.path.exists(path):
        return None
    mtime = os.path.getmtime(path)
    age = datetime.now().timestamp() - mtime
    return age / 3600


def get_data_age_hours(path):
    """从 JSON 内容读取 crawled_at 字段，计算数据年龄"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        times = []
        if isinstance(data, dict):
            # steam_data: {game: {crawled_at: "..."}}
            for v in data.values():
                if isinstance(v, dict) and v.get("crawled_at"):
                    times.append(v["crawled_at"])
            # roblox_games: _meta.last_updated
            if "_meta" in data and data["_meta"].get("last_updated"):
                times.append(data["_meta"]["last_updated"])
        if not times:
            return None
        latest = max(times)
        # 解析 ISO 格式
        dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return age
    except Exception as e:
        print(f"读取 {path} 失败: {e}")
        return None


def create_issue(title, body):
    """用 gh CLI 创建 GitHub Issue"""
    try:
        # 检查是否已存在未关闭的同类 Issue
        result = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--search", title, "--json", "number", "-q", ".[0].number"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"已有未关闭 Issue #{result.stdout.strip()}, 跳过创建")
            return
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body, "--label", "data-health"],
            capture_output=True, text=True, timeout=30
        )
        print(f"Issue 已创建: {title}")
    except Exception as e:
        print(f"创建 Issue 失败: {e}")


def main():
    print("=== 数据健康检查 ===")
    issues = []

    # 检查 steam_data.json
    age = get_data_age_hours(STEAM_DATA)
    if age is None:
        issues.append(f"steam_data.json 无法读取或没有 crawled_at 字段")
    elif age > THRESHOLD_HOURS:
        issues.append(f"steam_data.json 已 {age:.1f} 小时未更新 (阈值 {THRESHOLD_HOURS}h)")
    else:
        print(f"steam_data.json: {age:.1f}h (正常)")

    # 检查 roblox_games.json
    age = get_data_age_hours(ROBLOX_DATA)
    if age is None:
        issues.append(f"roblox_games.json 无法读取或没有 last_updated 字段")
    elif age > THRESHOLD_HOURS:
        issues.append(f"roblox_games.json 已 {age:.1f} 小时未更新 (阈值 {THRESHOLD_HOURS}h)")
    else:
        print(f"roblox_games.json: {age:.1f}h (正常)")

    if issues:
        title = f"⚠️ 数据健康检查失败 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        body = "## 问题\n\n" + "\n".join(f"- {i}" for i in issues) + "\n\n请检查 GitHub Actions 是否正常运行。"
        print(f"\n发现问题: {len(issues)} 个")
        for i in issues:
            print(f"  - {i}")
        create_issue(title, body)
        sys.exit(1)
    else:
        print("\n所有数据文件正常")
        sys.exit(0)


if __name__ == "__main__":
    main()
