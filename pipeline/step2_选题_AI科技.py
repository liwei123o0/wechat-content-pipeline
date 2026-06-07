#!/usr/bin/env python3
"""
微信公众号内容创作 - Step 2 (AI科技版): 新闻整理与选题
更新版：时效性优先（72h内）+ 程序员受众 + 热度评估
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

# 导入去重工具
import sys
sys.path.insert(0, str(Path(__file__).parent))
from 发布历史_去重 import 读取发布历史, 批量去重, 打印去重统计, 标题相似度

# ── 时区 ──
CST = timezone(timedelta(hours=8))

# ── 时效窗口（小时）：超过此值的新闻不进入TOP3推荐，仅作备选 ──
时效窗口_小时 = 72

# ──────────────────────────────────────────────
# 日期解析（支持多种 RSS 日期格式）
# ──────────────────────────────────────────────
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

def parse_rss_date(raw: str):
    """解析 RSS feed 常见日期格式，返回 datetime 或 None"""
    raw = raw.strip()
    if not raw:
        return None

    # 格式1: "2026-04-23 22:01:47  +0800"
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', raw)
    if m:
        y, mo, d, h, mi, s = map(int, m.groups())
        return datetime(y, mo, d, h, mi, s, tzinfo=CST)

    # 格式2: "Thu, 23 Apr 2026 14:30:00 +0000"
    m = re.match(r'[A-Za-z]{3},\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})', raw)
    if m:
        d, mo_str, y, h, mi, s = m.groups()
        mo = MONTH_MAP.get(mo_str.lower())
        if mo:
            return datetime(int(y), mo, int(d), int(h), int(mi), int(s), tzinfo=CST)

    return None


def 计算时效性分数(pub_date_raw: str, now: datetime) -> float:
    """
    时效性评分：时效窗口内按比例给分，超时不推荐
    0~窗口h → 100-0 分线性衰减；超过窗口 → -999（排除）
    """
    dt = parse_rss_date(pub_date_raw)
    if dt is None:
        return -999  # 无日期信息，降权但不直接排除

    diff = now - dt
    total_seconds = 时效窗口_小时 * 3600
    if diff.total_seconds() <= 0:
        return 100  # 未来时间，视为最新
    if diff.total_seconds() > total_seconds:
        return -999  # 超过时效窗口，直接排除

    # 线性衰减：越新分越高
    score = 100 * (1 - diff.total_seconds() / total_seconds)
    return score


def 计算热度(标题: str, 描述: str, 来源: str) -> float:
    """
    面向程序员群体的热度评分
    总分 = 技术分 + 受众分 + 数据分 + 来源分
    """
    文本 = 标题 + ' ' + 描述

    # ── 2. 技术热词分数（面向程序员圈） ──
    技术热词 = [
        # 编程语言 & 框架
        "Python", "Rust", "Go", "TypeScript", "JavaScript", "Java", "C++", "C#",
        "React", "Vue", "Angular", "Svelte",
        # AI/模型 & 开源
        "LLM", "GPT", "Claude", "Gemini", "DeepSeek", "Qwen", "Llama", "Mistral",
        "MoE", "Agent", "RAG", "Fine-tune", "微调", "RLHF", "SFT",
        "开源", "GitHub", "Star", "HuggingFace",
        # 推理 & 训练
        "推理", "Inference", "训练", "Training", "Benchmark",
        "vLLM", "Ollama", "llama.cpp", "GGUF", "量化",
        # 云 & DevOps
        "Kubernetes", "Docker", "AWS", "GCP", "Azure", "Vercel", "Cloudflare",
        "CI/CD", "Terraform", "Prometheus", "Grafana",
        # 数据库 & 存储
        "PostgreSQL", "MySQL", "Redis", "MongoDB", "向量数据库", "向量检索",
        "SQLite", "ClickHouse", "Iceberg",
        # 安全 & 网络
        "XSS", "SQL注入", "CSRF", "JWT", "OAuth", "零信任",
        "TLS", "mTLS", "WAF", "KMS",
        # 更多AI热词
        "大模型", "多模态", "Kimi", "豆包", "通义千问", "文心", "百灵",
        "多智能体", "MCP", "Function Call", "Tool Use",
        "Transformer", "Attention", "Diffusion",
    ]
    技术分 = sum(20 for 词 in 技术热词 if 词 in 文本)  # ⬆从15→20

    # ── 3. 程序员受众分数 ──
    受众词 = [
        # 开发工具
        "IDE", "Cursor", "VS Code", "Copilot", "V0", "Replit",
        "Claude Code", "GitHub Codespaces",
        # 工程实践
        "API", "SDK", "REST", "GraphQL", "gRPC", "WebSocket",
        "Library", "Framework",
        "重构", "代码审查", "单元测试", "集成测试", "TDD",
        "架构", "微服务", "分布式", "一致性",
        # 系统级
        "Linux", "内核", "Kernel", "内存管理", "并发", "异步",
        "WebAssembly", "WASM", "eBPF",
        # 语言 & 编译器
        "LLVM", "编译器", "JIT", "AOT", "解释器",
        "类型系统", "泛型", "宏", "DSL",
    ]
    受众分 = sum(15 for 词 in 受众词 if 词 in 文本)  # ⬆从12→15

    # ── 4. 具体数据/项目/事件加分 ──
    数据分 = 0
    if re.search(r'\d+[亿万元美]', 文本) or re.search(r'\$\d+', 文本):  # 金额
        数据分 += 20
    if re.search(r'\d+[BMT]参数|\d+B\s*(参数|model)', 文本, re.I):  # 参数量
        数据分 += 20
    if re.search(r'GitHub.*star|Star.*\d+[KkM]', 文本):  # GitHub star
        数据分 += 15
    if re.search(r'发布|开源|Release|上线|版本更新|v\d+\.\d+', 文本):  # 事件
        数据分 += 12
    if re.search(r'漏洞|CVE|安全|攻破|越权', 文本):  # 安全事件
        数据分 += 20
    # 新增：AI/大模型相关事件加分
    if re.search(r'融资|估值|独角兽|收购|上市|IPO|投资', 文本):
        数据分 += 12
    if re.search(r'机器人|具身|自动驾驶|机械臂', 文本):
        数据分 += 12

    # ── 5. 来源权重 ──
    来源权重 = {
        '量子位': 4,
        'OSCHINA': 4,
        '36氪': 3,
        '钛媒体': 3,
        'Arxiv-CS.AI': 5,
        'Arxiv-CS.LG': 5,
        '伯克利AI': 4,
    }
    来源分 = 来源权重.get(来源, 1)

    return round(技术分 + 受众分 + 数据分 + 来源分, 1)


def 生成分类(新闻列表):
    categories = {
        "AI大模型":    ["LLM", "大模型", "GPT", "Claude", "Gemini", "DeepSeek", "MoE", "多模态", "Kimi", "豆包", "通义千问", "Qwen", "Llama", "Mistral", "MiniMax"],
        "AI Agent":    ["Agent", "智能体", "LangChain", "LangGraph", "Dify", "AutoGen", "CrewAI"],
        "开源生态":    ["开源", "GitHub", "模型开源", "Star", "HuggingFace", "GitHub星标"],
        "AI编程":      ["代码生成", "Copilot", "Cursor", "AI编程", "IDE", "V0", "Replit", "Claude Code", "v0.dev"],
        "学术研究":    ["论文", "arXiv", "基准", "评测", "SOTA", "Transformer", "注意力", "推理", "训练", "微调", "RLHF"],
        "算力硬件":    ["H100", "H200", "GPU", "NPU", "算力", "英伟达", "AMD", "芯片", "TPU"],
        "具身智能":    ["机器人", "具身智能", "人形机器人", "灵巧手", "机械臂", "自动驾驶", "Tesla", "Optimus"],
        "商业融资":    ["融资", "估值", "独角兽", "上市", "收购", "投资", "IPO"],
        "AI安全":      ["AI安全", "对齐", "可解释", "幻觉", "数据投毒", "治理", "CVE", "漏洞"],
        "开发工具":    ["IDE", "Cursor", "VS Code", "API", "SDK", "REST", "GraphQL", "Docker", "Kubernetes", "Linux", "内核"],
    }
    stats = {cat: [] for cat in categories}
    stats["其他科技"] = []
    for item in 新闻列表:
        text = item.get('title', '') + item.get('description', '')
        matched = False
        for cat, keys in categories.items():
            if any(k in text for k in keys):
                stats[cat].append(item)
                matched = True
                break
        if not matched:
            stats["其他科技"].append(item)
    return stats


def main():
    print("=" * 60)
    print("📋 Step 2: AI/科技新闻整理与选题（时效优先版，72h窗口）")
    print("=" * 60)

    # ── 读取采集数据 ──
    采集_dir = Path(__file__).parent / "data" / "采集"
    files = list(采集_dir.glob("AI科技_汇总_*.json"))
    if not files:
        print("⚠️ 未找到 AI 科技采集数据，请先运行 step1a_采集_AI科技.py")
        return

    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        raw = json.load(f)
    新闻列表 = raw['数据']
    print(f"📖 读取 {latest.name}，共 {len(新闻列表)} 条新闻")

    now = datetime.now(tz=CST)
    print(f"⏰ 当前时间（北京时间）：{now.strftime('%Y-%m-%d %H:%M')}")

    # ── 新增：先加载发布历史进行去重 ──
    print(f"\n🔍 加载发布历史，检查重复内容...")
    发布历史 = 读取发布历史()
    print(f"   历史库记录数: {len(发布历史.get('已发布', []))} 条")

    去重后列表, 过滤列表 = 批量去重(新闻列表, 发布历史)
    打印去重统计(len(新闻列表), len(去重后列表), 过滤列表)

    if len(去重后列表) < len(新闻列表):
        print(f"\n⚠️  检测到 {len(过滤列表)} 条重复内容，已过滤")
    新闻列表 = 去重后列表

    # ── 过滤 & 评分 ──
    scored = []
    有时效 = 0
    for item in 新闻列表:
        title = item.get('title', '')
        desc = item.get('description', '')
        source = item.get('source', '')
        pub_date = item.get('pubDate', '')

        score = 计算热度(title, desc, source)
        # 时效：同时计算时效分（0-100，越新鲜越高）和实际小时数
        dt = parse_rss_date(pub_date)
        if dt is not None:
            diff = now - dt
            时效_小时 = round(diff.total_seconds() / 3600, 1)
            if diff.total_seconds() < 0:
                # 未来时间，视为最新
                时效 = 100
            elif diff.total_seconds() > 时效窗口_小时 * 3600:
                # 超过时效窗口，时效分-999（排除）
                时效, 时效_小时 = -999, None
            else:
                时效 = 100 * (1 - diff.total_seconds() / (时效窗口_小时 * 3600))
        else:
            时效, 时效_小时 = -999, None
        if 时效 > -999:
            有时效 += 1

        item['时效分'] = round(时效, 1)
        item['时效_小时'] = 时效_小时
        item['热度总分'] = score
        item['标题'] = title
        item['摘要'] = desc[:200] if desc else ''
        scored.append(item)

    print(f"📊 {时效窗口_小时}h 内新闻：{有时效} 条 / {len(新闻列表)} 条")

    # ── 先按时效过滤，再按热度排序 ──
    # 时效分=-999 → 超过时效窗口，不进入TOP3推荐但保留供备选
    推荐列表 = [x for x in scored if x['时效分'] > -999]
    推荐列表.sort(key=lambda x: x['热度总分'], reverse=True)

    # 备选（超过时效窗口但热度较高）
    超时列表 = [x for x in scored if x['时效分'] <= -999]
    超时列表.sort(key=lambda x: x['热度总分'], reverse=True)

    # ── 修复1: 过滤非AI/科技内容，只保留AI相关分类 ──
    print(f"\n🔥 过滤非AI/科技内容...")
    AI分类 = 生成分类(推荐列表 + 超时列表)  # 全部分类
    # AI/科技相关的分类白名单
    AI相关分类 = {"AI大模型", "AI Agent", "开源生态", "AI编程", "学术研究",
                    "算力硬件", "具身智能", "商业融资", "AI安全", "开发工具"}
    
    # ⚠️ 非AI内容黑名单（全部小写，对比时会转小写）
    AI黑名单 = [
        "秋粮", "粮食", "收割", "农产品", "农业",
        "住房公积金", "公积金", "大学毕业生", "就业",
        "油价", "油费", "汽油", "柴油", "加油站",
        "楼市", "房地产", "房价", "购房", "买房",
        "电费", "水费", "话费",
        "filezilla", "ftp client",  # 工具软件更新，非AI科技
        # 公司公告类（不生产、不存在、不涉及、涨幅偏离、异常波动等）
        "不生产", "公告称", "不存在其他", "涨幅偏离", "异常波动",
        "收盘价格", "连续三个交易日",
        # 普通时政/民生类
        "沙特阿美", "马来西亚总理", "苏州优化",
    ]
    
    def 是AI内容(item):
        text = (item.get('标题', '') + item.get('摘要', '') + item.get('title', '') + item.get('description', '')).lower()
        # 先检查黑名单
        for kw in AI黑名单:
            if kw in text:
                return False
        # 再检查AI分类
        for cat in AI相关分类:
            if item in AI分类.get(cat, []):
                return True
        return False

    # 过滤两个列表
    推荐AI列表 = [item for item in 推荐列表 if 是AI内容(item)]
    超时AI列表 = [item for item in 超时列表 if 是AI内容(item)]

    过滤掉数 = len(推荐列表) - len(推荐AI列表) + len(超时列表) - len(超时AI列表)
    print(f"   过滤掉 {过滤掉数} 条非AI内容（秋粮收购、公司公告等）")
    print(f"   ✅ AI相关: {时效窗口_小时}h内 {len(推荐AI列表)} 条 + 备选 {len(超时AI列表)} 条")

    # ── 修复2: 合并排序，分数优先，但窗口内有同分优势 ──
    # 窗口内按新鲜度线性加分（最新最多 +12 分），备选则不加
    def 排序加权(item):
        base = item['热度总分']
        h = item.get('时效_小时')
        # 窗口内的加新鲜分（越新越高）
        if h is not None and h != -1 and h <= 时效窗口_小时:
            return base + (时效窗口_小时 - h) * (12 / 时效窗口_小时)  # 最新最多加12分
        return base - 20  # 备选倒扣20分，除非远高于窗口内

    全部AI = 推荐AI列表 + 超时AI列表
    全部AI.sort(key=排序加权, reverse=True)
    
    # 标记来源
    def 是窗口内(item):
        return item in 推荐AI列表
    
    print(f"\n📌 混合排序（共 {len(全部AI)} 条AI内容，按热度降序）：")
    for i, item in enumerate(全部AI[:8], 1):
        src = item.get('source', '')[:8]
        title = item['标题'][:50]
        score = item['热度总分']
        tag = f"{时效窗口_小时}h内" if 是窗口内(item) else "备选"
        print(f"   {i:2d}. 【{score:>5.1f}分/{tag}】【{src}】{title}")
    
    # 取TOP 1
    最终推荐 = 全部AI[:1]
    print(f"\n   📋 最终推荐选题: {len(最终推荐)} 条")

    # ── 打印推荐 ──
    print(f"\n🔥 最终推荐（按热度，优先{时效窗口_小时}h内）：")
    for i, item in enumerate(最终推荐, 1):
        src = item.get('source', '')[:8]
        title = item['标题'][:55]
        score = item['热度总分']
        时效_小时 = item.get('时效_小时')
        if 时效_小时 and 时效_小时 == -1:
            时效_str = "备选"
        elif 时效_小时 is not None:
            时效_str = f"{时效_小时:.0f}h"
        else:
            时效_str = "?"
        print(f"  {i:2d}. 【{score:>5.1f}分/时效:{时效_str}】【{src}】{title}")

    # ── 关键词统计 ──
    print(f"\n📊 关键词热度排行（{时效窗口_小时}h 内）：")
    kw_counter = Counter()
    kw_pool = [
        "Agent", "LLM", "开源", "GitHub", "DeepSeek", "Qwen", "Llama",
        "机器人", "具身智能", "融资", "arXiv", "代码生成", "Cursor",
        "Python", "Rust", "Kubernetes", "Docker",
    ]
    for item in 推荐列表:
        text = (item.get('title', '') + ' ' + item.get('description', '')).upper()
        for kw in kw_pool:
            if kw.upper() in text:
                kw_counter[kw] += 1
    for kw, cnt in kw_counter.most_common(10):
        print(f"  • {kw}: {cnt}次")

    # ── 分类统计 ──
    print(f"\n📁 分类分布（{时效窗口_小时}h 内）：")
    stats = 生成分类(推荐列表)
    for cat, items in stats.items():
        if items:
            print(f"  {cat}: {len(items)}条")

    # ── 输出文件 ──
    output = {
        "生成时间": now.isoformat(),
        "当前时间": now.strftime("%Y-%m-%d %H:%M"),
        "时效窗口_小时": 时效窗口_小时,
        "原始数量": len(新闻列表),
        "窗口内数量": len(推荐列表),
        "AI过滤后": {
            "窗口内": len(推荐AI列表),
            "备选超时": len(超时AI列表),
        },
        "综合推荐": 最终推荐,  # 修复2: 包含窗口内+备选超时的AI内容
        "热度排行": 推荐AI列表[:20],
        "备选超时": 超时AI列表[:10],
        "关键词热度": dict(kw_counter.most_common(20)),
        "分类统计": {k: len(v) for k, v in stats.items()},
    }

    output_dir = Path(__file__).parent / "data" / "整理"
    output_dir.mkdir(exist_ok=True)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"选题_AI科技_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 选题已保存: {output_file.name}")

    # ── 最终推荐选题 ──
    print("\n" + "=" * 60)
    print(f"🎯 推荐选题 {len(最终推荐)} 篇（1篇，优先{时效窗口_小时}h内AI内容）")
    print("=" * 60)
    for i, item in enumerate(最终推荐, 1):
        h = item.get('时效_小时')
        if h is None:
            时效标签 = f"备选(>{时效窗口_小时}h)"
        elif h == -1:
            时效标签 = f"备选(>{时效窗口_小时}h)"
        else:
            时效标签 = f"{h:.0f}h前"
        print(f"\n【选题{i}】")
        print(f"  标题: {item['标题']}")
        print(f"  来源: {item.get('source', '')}")
        print(f"  热度: {item['热度总分']:.1f} 分")
        print(f"  时效: {时效标签}")
        print(f"  摘要: {item['摘要'][:100]}...")
        print(f"  链接: {item.get('url', '')}")

    # ── 关键修复：选定选题后立即记录原文信息到发布历史 ──
    # 目的：即使文章尚未发布，原文已被标记为"已用"
    #   下次同样RSS文章出现时，URL/标题/指纹会匹配，直接过滤
    print(f"\n📝 记录选定选题到发布历史（防止下次重复选择）...")
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from 发布历史_去重 import 记录发布成功
    for i, item in enumerate(最终推荐, 1):
        原标题 = item.get('标题', item.get('title', ''))
        url = item.get('url', '')
        来源 = item.get('source', item.get('来源', ''))
        记录发布成功(
            标题=原标题,       # 记录原文RSS标题（不是创作后的标题）
            url=url,           # 记录原文链接
            来源=来源,          # 记录来源渠道
            摘要=item.get('摘要', item.get('description', ''))[:200],
        )
        已标记 = str(i)
    print(f"   ✅ 已记录 {len(最终推荐)} 条原文到历史，下次自动过滤")

    return 最终推荐


if __name__ == "__main__":
    main()
