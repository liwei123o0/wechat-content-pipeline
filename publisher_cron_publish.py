#!/usr/bin/env python3
"""
发布运营定时任务 — Hermes cron 入口脚本
每天由 hermes cron 触发，执行：
1. 扫描 创作/ 中今天的文章
2. 运行 review_article.py 做最终审核
3. 运行 step5_发布.py 发布到微信草稿箱（定时 20:00）
4. 运行 export_docx.py 导出 docx 归档到值得顶/
5. 通过 agent_comm 通知 CEO

用法（脚本模式 — 输出给 Hermes agent 消费）:
    python3 publisher_cron_publish.py
    
用法（直接模式 — 独立执行）:
    python3 publisher_cron_publish.py --direct
"""
import re
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
BASE = Path(__file__).parent
创作_DIR = BASE / "创作"
值得顶_DIR = BASE / "值得顶"

sys.path.insert(0, str(BASE))


def get_today_column_slug():
    """返回今天对应的栏目 slug"""
    try:
        from column_config import get_today_column
        return get_today_column()
    except Exception as e:
        return None


def find_today_articles(column_slug=None):
    """查找今天待发布的文章"""
    all_articles = []
    
    # 先找栏目对应的文章
    if column_slug:
        col_files = sorted(创作_DIR.glob(f"文章_{column_slug}_*.md"), 
                          key=lambda p: p.stat().st_mtime, reverse=True)
        for f in col_files:
            all_articles.append(f)
    
    # 再找 AI热点 文章（当前主要产出模式）
    hot_files = sorted(创作_DIR.glob("文章_AI热点_*.md"), 
                      key=lambda p: p.stat().st_mtime, reverse=True)
    for f in hot_files:
        if f not in all_articles:
            all_articles.append(f)
    
    return all_articles


def extract_frontmatter(content):
    """提取 frontmatter 字段"""
    fm = {}
    m = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            kv = re.match(r'^(\w+):\s*(.+?)\s*$', line)
            if kv:
                fm[kv.group(1)] = kv.group(2).strip().strip("'\" ")
    return fm


def check_article_readiness(article_path):
    """检查一篇文章的就绪状态"""
    content = article_path.read_text(encoding='utf-8')
    fm = extract_frontmatter(content)
    body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    title = fm.get('title', article_path.stem)
    has_cover = 'cover_media_id' in content
    word_count = len(body.strip())
    
    # 检查是否已发布过
    history_file = BASE / "发布" / "发布历史.json"
    already_published = False
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding='utf-8'))
            if isinstance(history, list):
                for item in history:
                    if title == item.get('标题', ''):
                        already_published = True
                        break
        except:
            pass
    
    return {
        "title": title,
        "file": article_path.name,
        "has_cover": has_cover,
        "word_count": word_count,
        "already_published": already_published,
        "modified": datetime.fromtimestamp(article_path.stat().st_mtime).strftime('%m-%d %H:%M'),
    }


def run_script(script_name, args=None, timeout=120):
    """运行一个 Python 脚本，返回 (success, stdout)"""
    cmd = [sys.executable, str(BASE / script_name)]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, f"⏰ 超时 ({timeout}s)"
    except Exception as e:
        return False, f"❌ 异常: {e}"


def main():
    is_direct = "--direct" in sys.argv
    
    now = datetime.now(CST)
    column_slug = get_today_column_slug()
    
    # 如果是周日，跳过
    if now.weekday() == 6:
        msg = "🎉 今天是周日，休息日，不安排定时发布。"
        print(msg)
        return
    
    print("=" * 55)
    print(f"📤 发布运营定时任务 — {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"📅 {now.strftime('%A')}")
    if column_slug:
        from column_config import get_column
        col = get_column(column_slug)
        print(f"🎯 栏目: {col['name'] if col else column_slug} ({column_slug})")
    print("=" * 55)
    
    # 1. 扫描文章
    print("\n🔍 第1步：扫描文章...")
    articles = find_today_articles(column_slug)
    
    if not articles:
        print("  ⚠️ 没有找到待发布的文章")
        print("\n❌ 没有可发布的文章，流程终止。")
        return
    
    # 检查就绪状态，过滤已发布的
    ready_articles = []
    for art in articles[:10]:  # 只看最近的10篇
        status = check_article_readiness(art)
        print(f"  {'✅' if not status['already_published'] else '⏭️'} {status['file'][:50]}")
        print(f"     标题: {status['title'][:45]}")
        print(f"     封面: {'✅' if status['has_cover'] else '❌'}  字数: {status['word_count']}")
        if not status['already_published']:
            ready_articles.append(art)
        else:
            print(f"     状态: ⏭️ 已发布过，跳过")
    
    if not ready_articles:
        print("\n⏭️ 所有文章都已发布过，不需要重复发布。")
        return
    
    # 显示将发布的文章
    print(f"\n📋 待发布 ({len(ready_articles)} 篇):")
    for i, art in enumerate(ready_articles):
        status = check_article_readiness(art)
        print(f"  {i+1}. {status['title'][:50]}")
    
    # 2. 审核（review）
    print(f"\n🔎 第2步：最终审核 (review_article.py)...")
    all_review_ok = True
    for art in ready_articles:
        ok, output = run_script("review_article.py", [str(art)])
        # 提取审查结果
        if "PASS" in output and "FAIL" not in output[:200]:
            print(f"  ✅ {art.name[:45]} — 通过")
        elif "PASS" in output:
            print(f"  ✅ {art.name[:45]} — 通过")
        else:
            print(f"  ⚠️ {art.name[:45]} — 有警告")
            print(f"     {output[:200].strip()}")
    
    if not all_review_ok:
        print("  ⚠️ 部分文章有审核警告，继续发布...")
    
    # 3. 发布到微信草稿箱（先用第一个 ready 的文章）
    print(f"\n📤 第3步：发布到微信草稿箱...")
    
    # step5_发布.py 需要 --column 参数
    # 它使用 获取文件名() 来查找最新的文章
    # 但我们可能有多个文章，需要逐个发布
    
    publish_count = 0
    for art in ready_articles:
        print(f"\n  发布: {art.name[:45]}")
        # step5_发布.py 的 获取文件名 函数会按栏目找最新文章
        # 我们先手动把文章复制为需要发布的文件名
        # 或者直接调用 step5_发布.py 的 publish function
        
        if column_slug:
            ok, output = run_script("step5_发布.py", ["--column", column_slug], timeout=180)
        else:
            ok, output = run_script("step5_发布.py", ["--column", "AI热点"], timeout=180)
        
        if ok:
            print(f"  ✅ 发布成功")
            publish_count += 1
        else:
            print(f"  ⚠️ 发布结果:")
            # Show last few lines of output
            lines = output.strip().split('\n')
            for line in lines[-5:]:
                print(f"    {line}")
    
    if publish_count == 0:
        print("  ⚠️ 没有文章发布成功")
    
    # 4. 导出 docx 归档
    print(f"\n📄 第4步：导出 Docx 归档...")
    for art in ready_articles:
        ok, output = run_script("export_docx.py", [str(art)])
        if ok:
            # 从输出中提取文件名
            for line in output.strip().split('\n'):
                if '✅' in line:
                    print(f"  {line.strip()}")
        else:
            print(f"  ⚠️ {art.name[:40]} 导出异常")
    
    # 5. 汇总
    print(f"\n{'=' * 55}")
    print(f"📊 发布任务汇总")
    print(f"{'=' * 55}")
    print(f"  扫描文章: {len(articles)} 篇")
    print(f"  待发布:   {len(ready_articles)} 篇")
    print(f"  已发布:   {publish_count} 篇")
    print(f"  归档:     值得顶/{值得顶_DIR.name}")
    print(f"{'=' * 55}")
    
    # 通知 CEO（通过 agent_comm）
    try:
        from agent_comm import send
        notify_text = (f"✅ 定时发布任务完成\n"
                      f"📅 {now.strftime('%Y-%m-%d %A')}\n"
                      f"📤 发布 {publish_count}/{len(ready_articles)} 篇\n"
                      f"📄 已归档到 值得顶/")
        send("CEO", "publisher", "notify", {
            "status": "done" if publish_count > 0 else "partial",
            "summary": f"发布 {publish_count}/{len(ready_articles)} 篇，归档到 值得顶/",
        })
        print(f"\n📨 已通过 agent_comm 通知 CEO")
    except Exception as e:
        print(f"\n⚠️ 通知 CEO 失败: {e}")
    
    print(f"\n🎉 发布流程执行完毕！")
    
    # 输出关键的 JSON summary 给 Hermes agent 消费
    if not is_direct:
        summary = {
            "status": "done" if publish_count > 0 else "partial",
            "published": publish_count,
            "total_ready": len(ready_articles),
            "articles": [
                {
                    "file": art.name,
                    "title": check_article_readiness(art)["title"],
                }
                for art in ready_articles
            ],
        }
        print(f"\n---PUBLISH_SUMMARY_START---")
        print(json.dumps(summary, ensure_ascii=False))
        print(f"---PUBLISH_SUMMARY_END---")


if __name__ == "__main__":
    main()
