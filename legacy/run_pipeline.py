#!/usr/bin/env python3
"""
微信公众号内容创作流水线 v3 - 一键运行
自动执行: 采集 -> 选题 -> 深度搜索 -> 创作 -> 发布准备
支持 --column 参数指定栏目（默认自动检测星期几）
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from column_config import get_column, get_today_column, COLUMNS


def print_step(step_num, title):
    print("\n" + "=" * 60)
    print(f"📌 Step {step_num}: {title}")
    print("=" * 60)


def run_script(script_name, args=None):
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"⚠️ 脚本不存在: {script_name}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"\n🚀 运行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️ 执行失败: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="微信公众号流水线 v3")
    parser.add_argument("--column", "-c", choices=list(COLUMNS.keys()),
                       help="栏目slug（默认自动检测今天星期几）")
    args = parser.parse_args()

    栏目slug = args.column or get_today_column()

    if not 栏目slug:
        print("🎉 今天是周日，休息日！流水线暂停。")
        return

    column = get_column(栏目slug)

    print("=" * 60)
    print(f"🚀 微信公众号内容创作流水线 v3")
    print(f"📅 栏目: [{column['name']}] ({column['day']})")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    col_args = ["--column", 栏目slug]

    # Step 4.5: 找到刚生成的文章并审核
    创作_dir = Path(__file__).parent / "创作"
    latest_md = sorted(创作_dir.glob(f"文章_{栏目slug}_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    review_args = [str(latest_md[0])] if latest_md else []

    steps = [
        ("1", f"定向采集 ({column['name']})", "step1_采集.py", col_args),
        ("2", f"选题排序 ({column['name']})", "step2_选题.py", col_args),
        ("3", "深度素材搜索", "step3_深度搜索.py", col_args),
        ("4", f"创作 ({column['name']})", "step4_创作.py", col_args),
        ("4.5", "三维审核", "review_article.py", review_args),
        ("5", "发布准备", "step5_发布.py", col_args),
        ("6", "导出 Docx → 值得顶", "export_docx.py", []),
    ]

    results = {}

    for step_num, title, script, extra_args in steps:
        print_step(step_num, title)
        success = run_script(script, extra_args)
        results[step_num] = success

    # 汇总
    print("\n" + "=" * 60)
    print("📊 流水线执行报告")
    print("=" * 60)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\n完成: {success_count}/{total_count} 个步骤")
    print(f"栏目: {column['name']}")

    # 显示生成的文章
    创作_dir = Path(__file__).parent / "创作"
    md_files = sorted(创作_dir.glob("文章_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if md_files:
        latest = md_files[0]
        print(f"\n📄 最新文章: {latest.name}")

    print("\n" + "=" * 60)
    print("🎉 流水线执行完成!")
    print("=" * 60)

    return success_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
