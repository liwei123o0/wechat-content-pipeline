#!/usr/bin/env python3
"""
Step 4: 生成写作任务 → 交给 Hermes Agent 来写
不再调用 API，只输出结构化素材和写作要求。
"""

import json, re, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from column_config import get_column, COLUMNS, CI_STYLE


def 读取素材():
    素材_dir = Path(__file__).parent / "data" / "素材"
    files = list(素材_dir.glob("深度素材_*.json"))
    if not files:
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        return json.load(f)


def 读取选题(栏目slug=None):
    整理_dir = Path(__file__).parent / "data" / "整理"
    if 栏目slug:
        files = list(整理_dir.glob(f"选题_{栏目slug}_*.json"))
    if not files:
        files = list(整理_dir.glob("选题_*.json"))
    if not files:
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        return json.load(f)


def main(栏目slug=None):
    from column_config import get_today_column
    if not 栏目slug:
        栏目slug = get_today_column()
    if not 栏目slug:
        print("🎉 周日休息")
        return

    column = get_column(栏目slug)

    print("=" * 60)
    print(f"📋 Step 4: 写作任务")
    print(f"   栏目: {column['name']} ({column['day']})")
    print("=" * 60)

    素材数据 = 读取素材()
    选题数据 = 读取选题(栏目slug)

    if not 素材数据 or not 选题数据:
        print("⚠️ 缺少素材或选题")
        return

    选题列表 = 选题数据.get('热度排行', [])[:1]
    if not 选题列表:
        print("⚠️ 无选题")
        return

    选题 = 选题列表[0]
    title = 选题.get('标题', '')
    url = 选题.get('url', '')

    素材列表 = 素材数据.get('关键内容', [])
    material = "\n\n---\n\n".join([
        f"### {m.get('title', '')}\n来源: {m.get('url', '')}\n\n{m.get('content', '')[:1500]}"
        for m in 素材列表[:3]
    ])

    # 输出给 Hermes 的写作指令
    print(f"\n📌 选题: {title}")
    print(f"🔗 来源: {url}")
    print(f"\n{'='*60}")
    print("素材已就绪 → 交给 Hermes Agent 创作")
    print(f"{'='*60}")

    # 保存任务文件供后续读取
    task = {
        "栏目": column['name'],
        "栏目slug": 栏目slug,
        "选题": title,
        "来源URL": url,
        "素材": material,
        "生成时间": datetime.now().isoformat(),
    }
    task_path = Path(__file__).parent / "data" / "素材" / f"写作任务_{栏目slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(task_path, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    # 输出素材摘要
    print(f"\n📖 素材摘要（共 {len(素材列表)} 条）:")
    for i, m in enumerate(素材列表[:3], 1):
        print(f"  [{i}] {m.get('title', '')[:60]}")
    print(f"\n📁 任务文件: {task_path.name}")

    return task


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--column", "-c", help="栏目slug")
    args = parser.parse_args()
    main(args.column)
