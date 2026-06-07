#!/usr/bin/env python3
"""
微信公众号内容创作 - Step 1A: AI/科技新闻深度采集
用途: 独立定时任务，多渠道采集AI/科技/大模型/学术前沿新闻
输出: 完整描述文本，供后续LLM深度创作使用
"""

import json
import os
import time
import urllib.request
import urllib.parse
import re
import html
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

def fetch_url(url, timeout=15, headers=None):
    """获取网页内容"""
    try:
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        if headers:
            default_headers.update(headers)
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def clean_html(text):
    """清理HTML实体"""
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ==================== 渠道A1: 36氪 ====================
def 采集36氪():
    """采集36氪AI/科技新闻（RSS）"""
    print("📡 [A1/8] 36氪...")
    news_list = []
    try:
        url = "https://36kr.com/feed"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:30]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:500],
                    'source': '36氪',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '科技创业'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A2: 量子位 ====================
def 采集量子位():
    """采集量子位AI新闻（RSS）"""
    print("📡 [A2/8] 量子位...")
    news_list = []
    try:
        url = "https://www.qbitai.com/feed"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:20]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:500],
                    'source': '量子位',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': 'AI大模型'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A3: OSCHINA ====================
def 采集OSCHINA():
    """采集OSCHINA开源社区新闻（RSS）"""
    print("📡 [A3/8] OSCHINA...")
    news_list = []
    try:
        url = "https://www.oschina.net/news/rss"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:30]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:500],
                    'source': 'OSCHINA',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '开源技术'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A4: 钛媒体 ====================
def 采集钛媒体():
    """采集钛媒体新闻（RSS）"""
    print("📡 [A4/8] 钛媒体...")
    news_list = []
    try:
        url = "https://www.tmtpost.com/rss"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:20]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:500],
                    'source': '钛媒体',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '科技商业'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A5: 伯克利AI ====================
def 采集伯克利AI():
    """采集伯克利AI研究博客（RSS）"""
    print("📡 [A5/8] 伯克利AI...")
    news_list = []
    try:
        url = "https://bair.berkeley.edu/blog/feed.xml"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:15]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:800],
                    'source': '伯克利AI',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '学术研究'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A6: Arxiv CS.AI ====================
def 采集ArxivCS():
    """采集Arxiv CS.AI最新论文（RSS）"""
    print("📡 [A6/8] Arxiv CS.AI...")
    news_list = []
    try:
        url = "https://arxiv.org/rss/cs.AI"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:30]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:800],
                    'source': 'Arxiv-CS.AI',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '学术论文'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A7: Arxiv CS.LG ====================
def 采集ArxivLG():
    """采集Arxiv CS.LG最新论文（RSS）"""
    print("📡 [A7/8] Arxiv CS.LG...")
    news_list = []
    try:
        url = "https://arxiv.org/rss/cs.LG"
        content = fetch_url(url, timeout=15)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:30]:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                pub_el = item.find('pubDate')
                title = title_el.text if title_el is not None else ''
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ''
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc[:800],
                    'source': 'Arxiv-CS.LG',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': '学术论文'
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 渠道A8: VentureBeat AI ====================
def 采集VentureBeat():
    """采集VentureBeat AI频道新闻（RSS）"""
    print("📡 [A8/8] VentureBeat AI...")
    news_list = []
    try:
        url = "https://venturebeat.com/category/ai/feed"
        content = fetch_url(url, timeout=20)
        if content:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            for item in items[:20]:
                # 标题在CDATA中
                title_el = item.find('title')
                title = ''
                if title_el is not None and title_el.text:
                    title = title_el.text.strip()
                link_el = item.find('link')
                desc_el = item.find('description')
                desc = ''
                if desc_el is not None and desc_el.text:
                    # 取前600字符作为description（去掉HTML标签太长的问题）
                    desc = clean_html(desc_el.text)[:600]
                pub_el = item.find('pubDate')
                # 提取分类标签
                categories = [cat.text for cat in item.findall('category') if cat.text]
                category_str = ', '.join(categories[:3]) if categories else 'AI'
                news_list.append({
                    'title': title,
                    'url': link_el.text if link_el is not None else '',
                    'description': desc,
                    'source': 'VentureBeat',
                    'pubDate': pub_el.text if pub_el is not None else '',
                    'category': category_str,
                })
            print(f"    ✅ 获取 {len(news_list)} 条")
    except Exception as e:
        print(f"    ⚠️ 失败: {e}")
    time.sleep(0.5)
    return news_list

# ==================== 去重合并 ====================
def 去重合并(news_list):
    """去重合并"""
    seen = set()
    unique = []
    for item in news_list:
        url = item.get('url', '')
        title = item.get('title', '')
        if url and title and len(title) > 5 and url not in seen:
            seen.add(url)
            unique.append(item)
    return unique

# ==================== 保存数据 ====================
def 保存数据(news_list, source):
    """保存采集数据"""
    output_dir = Path(__file__).parent / "data" / "采集"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"AI科技_{source}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "采集时间": datetime.now().isoformat(),
            "来源": source,
            "数量": len(news_list),
            "数据": news_list
        }, f, ensure_ascii=False, indent=2)
    print(f"  💾 保存 {len(news_list)} 条数据 → {filename.name}")
    return filename

# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("🤖 Step 1A: AI/科技新闻深度采集 (8个渠道)")
    print("=" * 60)

    output_dir = Path(__file__).parent / "data" / "采集"
    output_dir.mkdir(exist_ok=True)

    all_news = []

    # 采集渠道列表
    channels = [
        采集36氪,         # A1. 36氪
        采集量子位,        # A2. 量子位
        采集OSCHINA,      # A3. OSCHINA
        采集钛媒体,        # A4. 钛媒体
        采集伯克利AI,      # A5. 伯克利AI
        采集ArxivCS,      # A6. Arxiv CS.AI
        采集ArxivLG,      # A7. Arxiv CS.LG
        采集VentureBeat,  # A8. VentureBeat AI
    ]

    for channel in channels:
        try:
            news = channel()
            all_news.extend(news)
        except Exception as e:
            print(f"    ⚠️ 渠道异常: {e}")

    # 去重
    all_news = 去重合并(all_news)

    print(f"\n📊 共采集到 {len(all_news)} 条新闻 (去重后)")

    if all_news:
        print("\n📰 来源分布:")
        sources = {}
        for item in all_news:
            src = item.get('source', '未知')
            sources[src] = sources.get(src, 0) + 1
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"  • {src}: {count}条")

        print("\n📰 分类分布:")
        categories = {}
        for item in all_news:
            cat = item.get('category', '未知')
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  • {cat}: {count}条")

        print("\n📰 全部采集结果 (标题+摘要预览):")
        for i, item in enumerate(all_news, 1):
            src = item.get('source', '')[:10]
            cat = item.get('category', '')[:6]
            title = item.get('title', '')[:60]
            desc = item.get('description', '')[:120]
            print(f"\n  {i}. [{src:10}] [{cat:6}] {title}")
            if desc:
                print(f"     📝 {desc}...")

    # 保存
    保存数据(all_news, "汇总")

    print("\n✅ Step 1A 完成!")
    return all_news

if __name__ == "__main__":
    main()
