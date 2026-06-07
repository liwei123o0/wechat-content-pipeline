#!/usr/bin/env python3
"""
微信公众号内容创作 - Step 1: 多渠道采集 v3.1
中国网络适配版：RSS → 国内可访问源 + Playwright搜索兜底
"""

import json
import os
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from column_config import get_column, COLUMNS

PLAYWRIGHT_SEARCH = str(Path.home() / ".hermes/scripts/playwright_search.py")

# ==================== 通用工具 ====================

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return None


def parse_rss(content, source_name, limit=30):
    """解析RSS/Atom feed"""
    news = []
    if not content:
        return news
    try:
        root = ET.fromstring(content)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        for item in items[:limit]:
            title_el = (item.find('title') if item.find('title') is not None
                       else item.find('{http://www.w3.org/2005/Atom}title'))
            link_el = (item.find('link') if item.find('link') is not None
                      else item.find('{http://www.w3.org/2005/Atom}link'))
            desc_el = (item.find('description') if item.find('description') is not None
                      else item.find('{http://www.w3.org/2005/Atom}summary'))

            title = title_el.text.strip() if title_el is not None and title_el.text else ''
            if link_el is not None:
                link = link_el.text.strip() if link_el.text else (link_el.get('href', '') or '')
            else:
                link = ''
            desc = desc_el.text.strip()[:300] if desc_el is not None and desc_el.text else ''

            # Atom格式用published/updated，RSS 2.0用pubDate
            pub_el = (item.find('pubDate')
                     if item.find('pubDate') is not None
                     else (item.find('{http://www.w3.org/2005/Atom}published')
                          if item.find('{http://www.w3.org/2005/Atom}published') is not None
                          else item.find('{http://www.w3.org/2005/Atom}updated')))
            pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ''

            if title:
                news.append({
                    'title': title,
                    'url': link,
                    'description': desc,
                    'source': source_name,
                    'pubDate': pub_date,
                })
    except Exception as e:
        print(f"    ⚠️ RSS解析失败: {type(e).__name__}: {e}")
    return news


def playwright_search(keyword, limit=10, engine="bing"):
    """使用Playwright脚本搜索"""
    try:
        result = subprocess.run(
            ["python3", PLAYWRIGHT_SEARCH, keyword, "--engine", engine, "--limit", str(limit)],
            capture_output=True, text=True, timeout=45
        )
        output = result.stdout
        # 解析输出（Playwright脚本输出格式: url|title|description）
        news = []
        for line in output.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) >= 2:
                    news.append({
                        'title': parts[1].strip() if len(parts) > 1 else '',
                        'url': parts[0].strip(),
                        'description': parts[2].strip() if len(parts) > 2 else '',
                        'source': f'Playwright-{engine}',
                    })
        return news
    except Exception as e:
        print(f"    ⚠️ Playwright搜索失败: {e}")
        return []


# ==================== 国内可用RSS源 ====================

def 采集OSCHINA():
    print("📡 OSCHINA 开源资讯...")
    return parse_rss(fetch_url("https://www.oschina.net/news/rss"), "OSCHINA", 30)


# ==================== Playwright搜索源 ====================

def 搜索Bing_VibeCoding():
    print("📡 Bing: Vibe Coding...")
    return playwright_search("Vibe Coding Claude Code Cursor 2026 最新", limit=10)

def 搜索Bing_AITools():
    print("📡 Bing: AI工具...")
    return playwright_search("AI开发工具 程序员 2026 推荐", limit=10)

def 搜索Bing_AgentMoney():
    print("📡 Bing: AI Agent变现...")
    return playwright_search("AI Agent 变现 副业 赚钱 2026", limit=10)

def 搜索Bing_AICareer():
    print("📡 Bing: 程序员AI裁员...")
    return playwright_search("程序员 AI 裁员 就业 2026", limit=10)

def 搜索Bing_Pitfalls():
    print("📡 Bing: AI开发踩坑...")
    return playwright_search("AI开发 踩坑 bug 翻车 2026", limit=10)

def 搜索Bing_Weekly():
    print("📡 Bing: 本周AI开源...")
    return playwright_search("GitHub AI 开源项目 本周 热门 2026", limit=10)


# ==================== 栏目→源映射 ====================

COLUMN_SOURCES = {
    "vibe-coding": [采集OSCHINA, 搜索Bing_VibeCoding],
    "ai-tools":    [采集OSCHINA, 搜索Bing_AITools],
    "agent-money": [采集OSCHINA, 搜索Bing_AgentMoney],
    "ai-career":   [搜索Bing_AICareer],
    "pitfalls":    [采集OSCHINA, 搜索Bing_Pitfalls],
    "weekly-ops":  [搜索Bing_Weekly],
}


# ==================== 从column_config动态读取源 ====================

def 采集配置RSS源(栏目slug, limit=15):
    """从column_config.py读取sources配置，自动采集RSS源"""
    column = get_column(栏目slug)
    if not column:
        return []

    all_news = []
    for src in column.get("sources", []):
        name = src.get("name", "")
        url = src.get("url", "")
        stype = src.get("type", "")

        # 跳过已有硬编码的源（避免重复）
        if stype == "rss" and url:
            print(f"📡 {name}...")
            content = fetch_url(url, timeout=15)
            if content:
                news = parse_rss(content, name, limit)
                if news:
                    print(f"    ✅ {len(news)} 条")
                else:
                    print(f"    ⚠️ 0 条")
                all_news.extend(news)
            else:
                print(f"    ❌ 连接失败")
            time.sleep(0.5)

    return all_news


# ==================== Main ====================

def main(栏目slug=None):
    print("=" * 60)
    print("📡 Step 1: 多渠道采集 v3.1 (中国网络适配)")
    print("=" * 60)

    if not 栏目slug:
        from column_config import get_today_column
        栏目slug = get_today_column()
        if not 栏目slug:
            print("🎉 周日休息")
            return

    column = get_column(栏目slug)
    if not column:
        print(f"❌ 未知栏目: {栏目slug}")
        return

    print(f"📅 栏目: [{column['name']}]")

    sources = COLUMN_SOURCES.get(栏目slug, [采集OSCHINA])

    all_news = []
    for src_fn in sources:
        news = src_fn()
        if news:
            print(f"    ✅ {len(news)} 条")
            all_news.extend(news)
        else:
            print(f"    ⚠️ 0 条")
        time.sleep(0.5)

    # 从column_config动态采集RSS源
    config_news = 采集配置RSS源(栏目slug)
    if config_news:
        print(f"   📦 配置RSS源合计: {len(config_news)} 条")
        all_news.extend(config_news)

    # 去重
    seen = set()
    unique = []
    for item in all_news:
        key = item['title'][:80]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"\n📊 采集汇总: {len(all_news)} 条 → 去重后 {len(unique)} 条")

    # ── 过滤低质量内容 ──
    黑名单关键词 = [
        # 会议/论坛/PR
        "大会", "论坛", "报名", "峰会", "Partner·", "产业大会", "圆桌对话",
        "promo", "Sponsor", "Save up to", "days left", "Apply before",
        "Battlefield 200", "TechCrunch Disrupt",
        # 财经噪音
        "现货黄金", "白银", "股价", "跌近", "涨超",
        # 太泛的日报
        "氪星晚报", "8点1氪",
        # 英文栏目广告
        "Ars Asks", "How to watch",
    ]
    过滤前 = len(unique)
    unique = [
        item for item in unique
        if not any(kw.lower() in (item.get('title','') + item.get('description','')).lower()
                   for kw in 黑名单关键词)
    ]
    if 过滤前 > len(unique):
        print(f"🚫 内容过滤: {过滤前} → {len(unique)} 条 (过滤 {过滤前 - len(unique)} 条低质量内容)")

    # 保存
    output_dir = Path(__file__).parent / "data" / "采集"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = {
        "生成时间": datetime.now().isoformat(),
        "栏目": 栏目slug,
        "栏目名": column['name'],
        "数据": unique,
        "统计": {"原始数量": len(all_news), "去重后": len(unique)},
    }

    output_file = output_dir / f"汇总_{栏目slug}_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"💾 保存: {output_file.name}")
    return unique


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--column", "-c", help="栏目slug")
    args = parser.parse_args()
    main(args.column)
