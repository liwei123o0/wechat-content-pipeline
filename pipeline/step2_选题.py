#!/usr/bin/env python3
"""
微信公众号内容创作 - Step 2: 选题 v3
栏目感知选题系统，按6大方向分类+热度排序
"""

import json
from datetime import datetime
from pathlib import Path
from collections import Counter

from column_config import get_column, COLUMNS

# 导入去重工具
from 发布历史_去重 import 读取发布历史, 批量去重, 打印去重统计

# ==================== 栏目×关键词矩阵 ====================

COLUMN_KEYWORDS = {
    "vibe-coding": {
        "hot": ["claude code", "cursor", "codex", "vibe coding", "copilot", "codi",
                "windsurf", "cline", "opencode", "Continue", "aide", "bolt", "lovable",
                "ai编程工具", "编程助手", "代码生成", "agent编程"],
        "scoring": ["实测", "对比", "技巧", "效率", "踩坑", "提升", "10x", "翻车", "最佳实践",
                    "横评", "选型", "开发者首选", "vs"],
    },
    "ai-tools": {
        "hot": ["ai工具", "效率工具", "开发工具", "程序员工具", "新工具", "产品发布",
                "开源工具", "免费工具", "vscode插件", "terminal工具"],
        "scoring": ["评测", "使用体验", "值不值", "定价", "替代", "推荐", "避坑"],
    },
    "agent-money": {
        "hot": ["ai agent", "变现", "搞钱", "副业", "赚钱", "独立开发", "一人公司",
                "月入", "收入", "接单", "外包", "淘宝", "代写", "自动化赚钱"],
        "scoring": ["案例", "收入", "成本", "利润", "拆解", "净利润", "能复制吗"],
    },
    "ai-career": {
        "hot": ["裁员", "跳槽", "薪资", "面试", "招聘", "ai替代", "失业", "转行",
                "大厂", "35岁", "内卷", "offer", "涨薪", "年终奖", "pip"],
        "scoring": ["数据", "对比", "趋势", "2026", "真相", "调查", "统计"],
    },
    "pitfalls": {
        "hot": ["踩坑", "bug", "报错", "失败", "翻车", "教训", "debug", "排查",
                "部署失败", "配置错误", "prompt问题", "api报错", "性能问题"],
        "scoring": ["解决", "方案", "经历", "花了多久", "怎么发现的", "避坑指南"],
    },
    "weekly-ops": {
        "hot": ["github", "开源", "新项目", "star", "huggingface", "新模型",
                "新工具", "本周", "热门", "趋势", "机会", "值得关注"],
        "scoring": ["本周", "推荐", "汇总", "简评", "关注", "看好"],
    },
}


# ==================== 核心逻辑 ====================

def 读取采集数据():
    采集_dir = Path(__file__).parent / "data" / "采集"
    files = list(采集_dir.glob("汇总_*.json"))
    if not files:
        print("⚠️ 未找到采集数据")
        return []
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)
    print(f"📖 读取采集数据: {latest.name}，共 {len(data.get('数据', []))} 条")
    return data.get('数据', [])


def 读取aihot数据():
    """读取AI HOT素材数据，字段归一化后与采集数据合并评分"""
    素材_dir = Path(__file__).parent / "data" / "素材"
    files = list(素材_dir.glob("aihot_素材_*.json"))
    if not files:
        print("📭 AI HOT: 无素材数据")
        return []
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('精选条目', [])
    if not items:
        print("📭 AI HOT: 精选条目为空")
        return []

    normalized = []
    for item in items:
        # 优先用 publishedAt，其次是 pubDate，最后从 url/source 推断
        pub = item.get('publishedAt') or item.get('pubDate') or item.get('date') or ''
        if isinstance(pub, str):
            pub = pub.strip()
        normalized.append({
            'title': item.get('title', '') or '',
            'url': item.get('sourceUrl', '') or '',
            'description': item.get('summary', '') or '',
            'source': f"AI HOT/{item.get('sourceName', '未知')}",
            'pubDate': pub,
            '_from_aihot': True,
        })
    print(f"📖 读取AI HOT数据: {latest.name}，共 {len(normalized)} 条 (字段已归一化)")
    return normalized


def 计算栏目匹配度(title, desc, 栏目slug):
    """计算一条新闻对特定栏目的匹配分数"""
    kw = COLUMN_KEYWORDS.get(栏目slug, {})
    text = (title + " " + desc).lower()
    score = 0

    # 热词匹配
    for word in kw.get("hot", []):
        if word.lower() in text:
            score += 15

    # 质量词匹配（加分但不如热词重要）
    for word in kw.get("scoring", []):
        if word.lower() in text:
            score += 8

    return score


def 计算传播热度(title, desc):
    """评估传播潜力"""
    score = 0

    # 数字=具体信息
    if any(c.isdigit() for c in title):
        score += 5

    # 问号=争议性
    if '?' in title or '？' in title:
        score += 5

    # 情绪词
    情绪词 = ["崩了", "炸了", "绝了", "离谱", "破防", "扎心", "崩溃", "真相", "神了"]
    for w in 情绪词:
        if w in title:
            score += 8

    # 标题长度（20-30字最优）
    if 15 <= len(title) <= 35:
        score += 3

    return score


def 选题排序(新闻列表, 栏目slug):
    """按栏目匹配度+传播热度排序"""
    scored = []
    for item in 新闻列表:
        title = item.get('title', '')
        desc = item.get('description', '')

        栏目分 = 计算栏目匹配度(title, desc, 栏目slug)
        热度分 = 计算传播热度(title, desc)
        总分 = 栏目分 + 热度分

        scored.append({
            **item,
            "栏目匹配": 栏目分,
            "传播热度": 热度分,
            "总分": 总分,
        })

    # 按总分排序
    scored.sort(key=lambda x: x['总分'], reverse=True)
    return scored


def 生成分类统计(新闻列表):
    """按栏目分类统计"""
    stats = {slug: [] for slug in COLUMNS}
    stats["未分类"] = []

    for item in 新闻列表:
        title = item.get('title', '')
        desc = item.get('description', '')
        best_slug = None
        best_score = 0

        for slug in COLUMNS:
            s = 计算栏目匹配度(title, desc, slug)
            if s > best_score:
                best_score = s
                best_slug = slug

        if best_score >= 10 and best_slug:
            stats[best_slug].append(item)
        else:
            stats["未分类"].append(item)

    return stats


# ==================== Main ====================

def main(栏目slug=None):
    print("=" * 60)
    print("📋 Step 2: 选题 v3")
    print("=" * 60)

    # 自动检测栏目
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

    print(f"📅 今日栏目: [{column['name']}]")

    # 读取数据（合并step1采集 + AI HOT）
    新闻列表 = 读取采集数据()
    if not 新闻列表:
        return
    aihot列表 = 读取aihot数据()
    if aihot列表:
        合并前 = len(新闻列表)
        新闻列表 = 新闻列表 + aihot列表
        print(f"🔗 合并AI HOT: {合并前} + {len(aihot列表)} = {len(新闻列表)} 条")

    # ── 去重：与历史发布比对，过滤已发选题 ──
    发布历史 = 读取发布历史()
    去重后列表, 过滤列表 = 批量去重(新闻列表, 发布历史)
    print(f"📋 去重: {len(新闻列表)} → {len(去重后列表)} 条 (过滤 {len(过滤列表)} 条)")
    if 过滤列表:
        for item in 过滤列表:
            print(f"   🚫 {item.get('title','')[:50]} → {item.get('过滤原因','')}")

    # 用去重后的列表继续
    新闻列表 = 去重后列表
    if not 新闻列表:
        print("⚠️ 去重后无新选题，终止")
        return

    # 栏目排序
    sorted_news = 选题排序(新闻列表, 栏目slug)

    # 显示 TOP 10
    print(f"\n🔥 [{column['name']}] TOP 10:")
    for i, item in enumerate(sorted_news[:10], 1):
        匹配 = item['栏目匹配']
        热度 = item['传播热度']
        print(f"  {i}. [匹配+{匹配} 热度+{热度}] {item.get('title', '')[:60]}")

    # 跨栏目分类统计
    print(f"\n📁 跨栏目分类:")
    stats = 生成分类统计(新闻列表)
    for slug, items in stats.items():
        name = COLUMNS[slug]['name'] if slug in COLUMNS else slug
        count = len(items)
        bar = "█" * min(count, 20)
        print(f"  {name}: {count}条 {bar}")

    # 保存选题结果
    output_dir = Path(__file__).parent / "data" / "整理"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = {
        "生成时间": datetime.now().isoformat(),
        "栏目": 栏目slug,
        "栏目名": column['name'],
        "原始数量": len(新闻列表),
        "热度排行": sorted_news[:15],
        "分类统计": {k: len(v) for k, v in stats.items()},
    }

    output_file = output_dir / f"选题_{栏目slug}_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 选题结果: {output_file.name}")

    # 推荐选题
    print(f"\n{'=' * 60}")
    print(f"🎯 [{column['name']}] 推荐 TOP 3:")
    print("=" * 60)
    for i, item in enumerate(sorted_news[:3], 1):
        print(f"\n【选题{i}】{item.get('title', '')}")
        print(f"  匹配+{item['栏目匹配']} 热度+{item['传播热度']}")

    return sorted_news


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--column", "-c", help="栏目slug")
    args = parser.parse_args()
    main(args.column)
