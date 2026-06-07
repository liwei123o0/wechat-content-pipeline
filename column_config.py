#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号「Python工作圈」6栏目主配置文件 v4.0
基于用户反馈扩展：AI写作/公众号/小红书、AI做PPT、AI办公自动化、AI论文辅助、AI变现拆解
新增6个RSS源（n8n Blog、Zapier Blog、Reddit r/AITools、知乎副业、Lifehacker、ProductHunt全局）
"""

from datetime import datetime

# ==================== 6栏目定义 ====================

COLUMNS = {
    "vibe-coding": {
        "day": "周一",
        "name": "Vibe Coding实战",
        "slug": "vibe-coding",
        "desc": "Claude Code/Cursor/Codex一手体验，每篇踩一个具体坑或亮一个骚操作",
        "sources": [
            {"name": "GitHub Trending", "url": "https://github.com/trending?since=weekly", "type": "scrape"},
            {"name": "Claude Code Changelog", "url": "https://docs.anthropic.com/en/docs/claude-code/overview", "type": "scrape"},
            {"name": "OSSInsight AI Trending", "url": "https://ossinsight.io/trending/ai", "type": "scrape"},
            {"name": "GitHub Blog", "url": "https://github.blog/feed/", "type": "rss"},
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage?q=claude+code+cursor+vibe+coding", "type": "rss"},
            {"name": "Reddit r/vibecoding", "url": "https://www.reddit.com/r/vibecoding/.rss", "type": "rss"},
            {"name": "InfoQ 中文", "url": "https://www.infoq.cn/feed", "type": "rss"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed", "type": "rss"},
            {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "type": "rss"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
        ],
        "search_keywords": [
            "Vibe Coding 实战 踩坑 2026",
            "Claude Code 技巧 经验",
            "Cursor AI 编程 对比",
            "AI 编程工具 效率 2026",
        ],
        "color": "#10B981",
        "cover_style": "dark_terminal",
    },

    "ai-tools": {
        "day": "周二",
        "name": "AI工具解剖",
        "slug": "ai-tools",
        "desc": "深扒一款AI工具：AI写作/公众号/小红书、AI做PPT、AI办公自动化、AI论文辅助…我用它干了什么、哪里被坑了",
        "sources": [
            {"name": "ProductHunt AI", "url": "https://www.producthunt.com/topics/artificial-intelligence", "type": "scrape"},
            {"name": "Hacker News Show HN", "url": "https://hnrss.org/show", "type": "rss"},
            {"name": "少数派 AI", "url": "https://sspai.com/tag/AI", "type": "scrape"},
            {"name": "少数派 最新", "url": "https://sspai.com/feed", "type": "rss"},
            {"name": "知乎 AI工具", "url": "https://www.zhihu.com/topic/20060753/hot", "type": "scrape"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "TechCrunch 全局", "url": "https://techcrunch.com/feed/", "type": "rss"},
            {"name": "Ars Technica AI", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "type": "rss"},
            {"name": "36氪 AI", "url": "https://36kr.com/feed", "type": "rss"},
            {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "type": "rss"},
            {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "type": "rss"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
            {"name": "The Decoder", "url": "https://the-decoder.com/feed/", "type": "rss"},
            {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "type": "rss"},
            {"name": "ZDNet AI", "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "type": "rss"},
            {"name": "Synced 机器之心英", "url": "https://syncedreview.com/feed/", "type": "rss"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed", "type": "rss"},
            {"name": "雷锋网 AI", "url": "https://leiphone.com/feed/ai", "type": "rss"},
            {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "type": "rss"},
            {"name": "n8n Blog", "url": "https://blog.n8n.io/rss/", "type": "rss"},
            {"name": "Zapier Blog", "url": "https://zapier.com/blog/feed/", "type": "rss"},
            {"name": "Reddit r/AITools", "url": "https://www.reddit.com/r/artificialintelligence/.rss", "type": "rss"},
        ],
        "search_keywords": [
            "AI工具 实测 2026 写作 办公",
            "AI写作工具 公众号 小红书",
            "AI PPT 制作 工作流 自动化",
            "AI论文辅助 学术工具",
            "AI办公效率 自动化 2026",
        ],
        "color": "#3B82F6",
        "cover_style": "glass_card",
    },

    "agent-money": {
        "day": "周三",
        "name": "Agent搞钱拆解",
        "slug": "agent-money",
        "desc": "拆一个AI变现/AI副业案例：AI代写/代做PPT/AI公众号/AI小红书/AI接单/程序员副业，撕开真实利润和数据",
        "sources": [
            {"name": "V2EX 分享创造", "url": "https://www.v2ex.com/feed/create.xml", "type": "rss"},
            {"name": "即刻 AI创业圈", "url": "https://web.okjike.com/topic/62b9debf1ba490010664d1ca", "type": "scrape"},
            {"name": "程序员客栈", "url": "https://www.proginn.com", "type": "scrape"},
            {"name": "Twitter #buildinpublic", "url": "https://nitter.net/search?f=tweets&q=%23buildinpublic+AI", "type": "scrape"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "36氪 AI", "url": "https://36kr.com/feed", "type": "rss"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
            {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "type": "rss"},
            {"name": "Synced 机器之心英", "url": "https://syncedreview.com/feed/", "type": "rss"},
            {"name": "知乎 副业赚钱", "url": "https://www.zhihu.com/topic/19776749/hot", "type": "scrape"},
            {"name": "Reddit r/sidehustle", "url": "https://www.reddit.com/r/sidehustle/.rss", "type": "rss"},
            {"name": "知乎 AI副业", "url": "https://www.zhihu.com/topic/19948261/hot", "type": "scrape"},
            {"name": "Reddit r/beermoney", "url": "https://www.reddit.com/r/beermoney/.rss", "type": "rss"},
            {"name": "少数派 效率工具", "url": "https://sspai.com/feed", "type": "rss"},
        ],
        "search_keywords": [
            "AI Agent 变现 案例 2026",
            "AI 代写 接单 赚钱 月收入",
            "AI 公众号 小红书 变现 副业",
            "AI代做 PPT 文档 接单",
            "AI 内容创作 赚钱 2026",
            "程序员 AI 副业 赚钱 2026",
            "AI 接单 独立开发 做产品",
        ],
        "color": "#F59E0B",
        "cover_style": "money_dark",
    },

    "ai-career": {
        "day": "周四",
        "name": "程序员的AI生存法则",
        "slug": "ai-career",
        "desc": "职场+AI视角：AI办公自动化、35岁转型、重复劳动替代、裁员数据、跳槽策略、薪资对比、效率翻倍实操",
        "sources": [
            {"name": "脉脉热帖", "url": "https://maimai.cn", "type": "scrape"},
            {"name": "V2EX 职场", "url": "https://www.v2ex.com/feed/jobs.xml", "type": "rss"},
            {"name": "Boss直聘", "url": "https://www.zhipin.com", "type": "scrape"},
            {"name": "知乎 程序员职场", "url": "https://www.zhihu.com/topic/19551275/hot", "type": "scrape"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "36氪 AI", "url": "https://36kr.com/feed", "type": "rss"},
            {"name": "ZDNet AI", "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "type": "rss"},
            {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "type": "rss"},
            {"name": "雷锋网 AI", "url": "https://leiphone.com/feed/ai", "type": "rss"},
            {"name": "Reddit r/productivity", "url": "https://www.reddit.com/r/productivity/.rss", "type": "rss"},
            {"name": "Lifehacker", "url": "https://lifehacker.com/feed/rss", "type": "rss"},
            {"name": "知乎 35岁职场危机", "url": "https://www.zhihu.com/topic/19817365/hot", "type": "scrape"},
            {"name": "V2EX 中年危机", "url": "https://www.v2ex.com/feed/jobs.xml", "type": "rss"},
            {"name": "Reddit r/careerguidance", "url": "https://www.reddit.com/r/careerguidance/.rss", "type": "rss"},
        ],
        "search_keywords": [
            "AI 办公自动化 效率 2026",
            "AI 替代 重复劳动 实操",
            "AI 职场 效率 提升",
            "AI 工具 工作流 自动化",
            "程序员 35岁 转型 AI 方向",
            "AI 时代 程序员 职业规划 2026",
            "中年程序员 AI 转行 出路",
        ],
        "color": "#EF4444",
        "cover_style": "warning_red",
    },

    "pitfalls": {
        "day": "周五",
        "name": "踩坑复盘",
        "slug": "pitfalls",
        "desc": "AI开发具体坑：Agent部署翻车、prompt翻车、量化策略回测陷阱",
        "sources": [
            {"name": "V2EX 技术", "url": "https://www.v2ex.com/feed/tech.xml", "type": "rss"},
            {"name": "Stack Overflow Hot", "url": "https://stackoverflow.com/feeds/week", "type": "rss"},
            {"name": "GitHub Issues AI", "url": "https://github.com/issues?q=is%3Aissue+label%3Abug+AI+agent", "type": "scrape"},
            {"name": "Reddit r/programming", "url": "https://www.reddit.com/r/programming/.rss", "type": "rss"},
            {"name": "Ars Technica AI", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "type": "rss"},
            {"name": "Hacker News Show HN", "url": "https://hnrss.org/show", "type": "rss"},
            {"name": "ZDNet AI", "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "type": "rss"},
        ],
        "search_keywords": [
            "AI Agent 部署 踩坑",
            "Claude Code bug 修复",
            "prompt engineering 翻车",
            "量化策略 回测 陷阱",
        ],
        "color": "#8B5CF6",
        "cover_style": "bug_purple",
    },

    "weekly-ops": {
        "day": "周六",
        "name": "本周AI变现机会",
        "slug": "weekly-ops",
        "desc": "汇总本周AI写作/办公/效率工具与项目+简评",
        "sources": [
            {"name": "GitHub Trending Weekly", "url": "https://github.com/trending?since=weekly", "type": "scrape"},
            {"name": "HuggingFace Trending", "url": "https://huggingface.co/models?sort=trending", "type": "scrape"},
            {"name": "ProductHunt Weekly", "url": "https://www.producthunt.com/leaderboard/weekly/2026", "type": "scrape"},
            {"name": "Hacker News Top", "url": "https://hnrss.org/frontpage", "type": "rss"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "type": "rss"},
            {"name": "MarkTechPost", "url": "https://www.marktechpost.com/feed/", "type": "rss"},
            {"name": "AI Trends", "url": "https://www.aitrends.com/feed/", "type": "rss"},
            {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "type": "rss"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
            {"name": "Synced 机器之心英", "url": "https://syncedreview.com/feed/", "type": "rss"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed", "type": "rss"},
            {"name": "雷锋网 AI", "url": "https://leiphone.com/feed/ai", "type": "rss"},
            {"name": "arXiv cs.AI", "url": "https://rss.arxiv.org/rss/cs.AI", "type": "rss"},
            {"name": "n8n Blog", "url": "https://blog.n8n.io/rss/", "type": "rss"},
            {"name": "ProductHunt 全局", "url": "https://www.producthunt.com/feed", "type": "rss"},
        ],
        "search_keywords": [
            "GitHub trending AI 2026",
            "新AI工具 本周 写作 办公",
            "AI 开源项目 热门 自动化",
            "AI 内容创作 项目 工具",
            "本周 AI 效率 工具 汇总",
        ],
        "color": "#06B6D4",
        "cover_style": "dashboard",
    },

    "frontier-news": {
        "day": "周日",
        "name": "AI前沿资讯",
        "slug": "frontier-news",
        "desc": "一周AI前沿新闻速递：大模型发布、行业动态、技术突破、融资上市，3分钟掌握AI圈大事",
        "sources": [
            {"name": "OSCHINA", "url": "https://www.oschina.net/news", "type": "scrape"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed", "type": "rss"},
            {"name": "雷锋网 AI", "url": "https://leiphone.com/feed/ai", "type": "rss"},
            {"name": "钛媒体", "url": "https://www.tmtpost.com/rss.xml", "type": "rss"},
            {"name": "36氪 AI", "url": "https://36kr.com/feed", "type": "rss"},
            {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
            {"name": "The Decoder", "url": "https://the-decoder.com/feed/", "type": "rss"},
            {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "type": "rss"},
            {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "type": "rss"},
            {"name": "Synced 机器之心英", "url": "https://syncedreview.com/feed/", "type": "rss"},
            {"name": "ArXiv cs.AI", "url": "https://rss.arxiv.org/rss/cs.AI", "type": "rss"},
            {"name": "Hacker News Frontpage", "url": "https://hnrss.org/frontpage", "type": "rss"},
        ],
        "search_keywords": [
            "AI 新闻 本周 大模型 发布",
            "人工智能 前沿 技术突破 2026",
            "AI 行业 动态 融资 上市 一周",
        ],
        "color": "#8B5CF6",
        "cover_style": "dashboard",
    },
}

# ==================== 刺式写作风格配置 ====================

CI_STYLE = {
    "base_rules": [
        "字数：1800-2200字，超2200读者划走",
        "开头不能千篇一律，「说句得罪人的话」不能连续两篇用同一句式，可选：你敢信吗/有没有一种可能/我来告诉你真相/你发现没有/我真服了/说实话/你每个月花XX钱/上周发生了件魔幻的事/数字冲击式（xx亿/xx万）/翻车式（又是xx翻车）/坦白说/聊个扎心的",
        "全文可穿插2-3次刺式话术（说句扎心的/说句得罪人的话/说句不好听的）但不能每篇同款",
        "每篇埋5-7个「刺」——读者想反驳/补充/分享经历的点",
        "结尾用互动钩子（悬念/痛点/金句/反转/收藏/互动投票6种轮换）+ 关注引导+下集预告双层结构，禁止「欢迎评论区讨论」",
        "每段都要有读者想回嘴的点，禁止中性报道和信息堆砌",
    ],
    "forbidden_patterns": [
        "「这恰恰是...」「背后逻辑是...」「值得注意的是...」「事实上...」「毋庸置疑...」",
        "完美平行结构（3+个「第一...第二...第三...」）",
        "「随着...」「在...背景下」「众所周知」",
        "「一方面...另一方面...」和稀泥",
        "总结+呼吁转发套路结尾",
    ],
    "required_elements": [
        "至少3个具体人名/公司名/项目名/数字",
        "5-7处争议点（读者想反驳的地方）",
        "2-5次「说句得罪人的/扎心的」话术",
        "互动结尾（悬念/痛点/金句/反转/收藏/互动6种轮换）+关注引导+下集预告",
        "3-5处金句卡片（> 引用格式）",
        "段落间 --- 分隔线",
    ],
}


# ==================== 栏目×星期映射 ====================

DAY_TO_COLUMN = {
    0: "vibe-coding",    # 周一
    1: "ai-tools",        # 周二
    2: "agent-money",     # 周三
    3: "ai-career",       # 周四
    4: "pitfalls",        # 周五
    5: "weekly-ops",      # 周六
    6: "frontier-news",   # 周日
}


def get_today_column():
    weekday = datetime.now().weekday()
    return DAY_TO_COLUMN.get(weekday)


def get_column(slug):
    return COLUMNS.get(slug)


def get_all_columns():
    return list(COLUMNS.keys())
