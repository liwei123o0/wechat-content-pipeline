#!/usr/bin/env python3
"""流线线终步：为今天所有文章生成百家号版文件"""
import re, glob
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPTS_DIR.parent
CONVERTER = SCRIPTS_DIR / "convert_to_baijiahao.py"

def run():
    import subprocess, datetime

    today = datetime.date.today().strftime("%Y%m%d")
    articles = sorted(PROJECT_DIR.glob(f"创作/文章_*{today}*.md"))

    if not articles:
        print("❌ 没找到今天创作的文章")
        return

    print(f"📄 找到 {len(articles)} 篇今天文章:")
    for art in articles:
        title = re.search(r'^title:\s*(.+?)\s*$', art.read_text('utf-8'), re.M)
        t = title.group(1).strip() if title else art.name
        print(f"   · {t[:50]}")

    for art in articles:
        print(f"\n{'='*50}")
        result = subprocess.run(
            ["python3", str(CONVERTER), str(art), "--format", "docx", "--adapt"],
            capture_output=True, text=True, timeout=30
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(f"  ⚠️ 错误: {result.stderr[:200]}")

    out_dir = PROJECT_DIR / "创作" / "百家号输出"
    files = sorted(out_dir.glob(f"*{today}*") or out_dir.glob("*.docx"))
    print(f"\n{'='*50}")
    print(f"📁 百家号输出目录: {out_dir}/")
    for f in files:
        print(f"  {f.name}  ({f.stat().st_size / 1024:.0f} KB)")

if __name__ == "__main__":
    run()
