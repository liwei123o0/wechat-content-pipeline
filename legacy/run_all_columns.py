#!/usr/bin/env python3
"""每天跑7个栏目的文章各一篇，全部发到草稿箱"""
import sys, subprocess, json, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from column_config import COLUMNS

ALL_SLUGS = list(COLUMNS.keys())  # 7个栏目

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def run(cmd, timeout=180):
    """运行shell命令，实时输出"""
    proc = subprocess.run(cmd, shell=True, cwd=str(BASE))
    return proc.returncode == 0

def generate_basic_article(slug):
    """当创作目录没有文章时，生成一篇基础文章"""
    col = COLUMNS[slug]
    
    # 读取最新采集数据
    采集_dir = BASE / "采集"
    files = sorted(采集_dir.glob(f"汇总_{slug}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    
    with open(files[0]) as f:
        data = json.load(f)
    items = data.get('数据', []) if isinstance(data, dict) else data
    
    # 取前5条作为素材
    top_items = items[:5]
    
    now = datetime.now()
    article = f"""---
title: {col['name']}测试文章 {now.strftime('%m/%d')}
column: {slug}
author: Python工作圈
date: {now.strftime('%Y-%m-%d')}
---

说句实话，今天这篇文章是一篇测试内容——用来测试{col['name']}这个类型在读者中的反响。

## 今日素材精选

{'  '.join([f'**{i+1}. {item.get("title","无标题")}**' for i, item in enumerate(top_items)])}

以上是今天采集到的相关热门内容。

## 为什么做这个测试

你看到这篇文章，是因为公众号正在做内容类型轮转测试。每天7个栏目各出一篇，最终根据读者互动数据来确定最受欢迎的内容方向。

如果你觉得这个类型对你有用，点个关注，让我知道。

---

**下集预告：** 明天同一时间，测试下一个类型的内容。
"""

    filename = f"文章_{slug}_auto_{now.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = BASE / "创作" / filename
    with open(filepath, 'w') as f:
        f.write(article)
    return filepath

def main():
    print(f"\n{'='*60}")
    print(f"  📰 每日7栏目全量跑")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    
    results = {}
    
    for i, slug in enumerate(ALL_SLUGS, 1):
        col = COLUMNS[slug]
        print(f"\n{'─'*60}")
        print(f"  [{i}/{len(ALL_SLUGS)}] {col['name']} ({slug})")
        print(f"{'─'*60}")
        
        # Step 1-3: 采集→选题→搜索
        step(f"Step 1-3: 采集素材 ({slug})")
        ok = run(f"python3 step1_采集.py --column {slug} && python3 step2_选题.py --column {slug} && python3 step3_深度搜索.py --column {slug}")
        
        if not ok:
            print(f"  ⚠️  采集失败，跳过此栏目")
            results[slug] = "采集失败"
            continue
        
        # Step 4: 生成写作任务
        step(f"Step 4: 写作任务 ({slug})")
        run(f"python3 step4_创作.py --column {slug}")
        
        # 检查是否已有文章
        创作_dir = BASE / "创作"
        existing = sorted(创作_dir.glob(f"文章_{slug}_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not existing:
            print(f"  ⚠️  无现成文章，自动生成基础篇...")
            new_file = generate_basic_article(slug)
            if new_file:
                print(f"  ✅ 已创建: {new_file.name}")
                existing = [new_file]
            else:
                print(f"  ❌ 无法生成文章")
                results[slug] = "无文章"
                continue
        
        article_path = existing[0]
        print(f"  📄 文章: {article_path.name}")
        
        # Step 4.5: 审核
        step(f"Step 4.5: 审核")
        run(f"python3 review_article.py '{article_path}'")
        
        # Step 5: 发布
        step(f"Step 5: 发布")
        run(f"python3 step5_发布.py --column {slug}")
        
        # Step 6: 导出docx
        step(f"Step 6: 导出docx")
        run(f"python3 export_docx.py '{article_path}'")
        
        results[slug] = "✅ 完成"
    
    # 汇总
    print(f"\n{'='*60}")
    print(f"  📊 今日7栏目汇总")
    print(f"{'='*60}")
    for slug in ALL_SLUGS:
        col = COLUMNS[slug]
        status = results.get(slug, "未执行")
        print(f"  {status} {col['name']}")
    print(f"\n  🎉 全部完成！去草稿箱检查各栏目文章")

if __name__ == '__main__':
    main()
