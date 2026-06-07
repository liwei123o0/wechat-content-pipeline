#!/usr/bin/env python3
"""
微信公众号内容创作 - 发布历史管理与去重工具
功能：
1. 记录所有已发布的文章（标题、URL、关键词、发布时间）
2. 在选题阶段过滤重复内容
3. 支持多级去重：URL精确匹配、标题相似度、关键词指纹
"""

import json
import re
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

CST = timezone(timedelta(hours=8))
HISTORY_FILE = Path(__file__).parent / "发布" / "发布历史.json"

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
    "看", "好", "自己", "这", "那", "这是", "就是", "可以", "什么", "因为",
    "的话", "如果", "但是", "而且", "然后", "还有", "以及", "或者", "所以",
    "最新", "发布", "推出", "上线", "发布了", "正式", "现在", "今天", "昨日",
}

def 提取关键词(text: str, top_n: int = 8) -> list:
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS and not w.isdigit()]
    filtered.sort(key=lambda x: -len(x))
    return filtered[:top_n]

def 生成标题指纹(title: str) -> str:
    keywords = 提取关键词(title)
    fingerprint = '|'.join(sorted(keywords[:5]))
    return hashlib.md5(fingerprint.encode()).hexdigest()[:12]

def 标题相似度(title1: str, title2: str) -> float:
    words1 = set(提取关键词(title1))
    words2 = set(提取关键词(title2))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)

def 读取发布历史() -> dict:
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "版本": "1.0",
        "最后更新": "",
        "已发布": [],
        "统计": {
            "总发布数": 0,
            "去重拦截数": 0
        }
    }

def 保存发布历史(history: dict):
    history["最后更新"] = datetime.now(tz=CST).isoformat()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def 检查是否重复(新闻项: dict, history: dict = None, 相似度阈值: float = 0.3) -> tuple:
    if history is None:
        history = 读取发布历史()

    已发布列表 = history.get("已发布", [])
    if not 已发布列表:
        return False, ""

    当前标题 = 新闻项.get('标题', 新闻项.get('title', ''))
    当前URL = 新闻项.get('url', '')
    当前来源 = 新闻项.get('source', 新闻项.get('来源', ''))

    # ── 第一重：URL精确匹配 ──
    if 当前URL:
        for 已发布 in 已发布列表:
            if 已发布.get('URL') == 当前URL:
                return True, f"URL精确匹配: {已发布.get('标题', '')[:30]}..."

    # ── 第二重：标题指纹精确匹配 ──
    当前指纹 = 生成标题指纹(当前标题)
    for 已发布 in 已发布列表:
        if 已发布.get('指纹') == 当前指纹:
            return True, f"标题指纹匹配: {已发布.get('标题', '')[:30]}..."

    # ── 第三重：关键词实体匹配（新！） ──
    # 提取当前标题的关键实体词
    当前关键词 = set(提取关键词(当前标题, top_n=6))
    for 已发布 in 已发布列表:
        历史关键词 = set(已发布.get('关键词', []))
        # 如果两者有3个以上关键词完全相同→重复
        if len(当前关键词 & 历史关键词) >= 3:
            return True, f"关键词重叠({当前关键词 & 历史关键词}): {已发布.get('标题', '')[:30]}..."

    # ── 第四重：标题相似度匹配（阈值降到0.3） ──
    for 已发布 in 已发布列表:
        sim = 标题相似度(当前标题, 已发布.get('标题', ''))
        if sim >= 相似度阈值:
            return True, f"标题相似({sim:.1%}): {已发布.get('标题', '')[:30]}..."

    # ── 第五重：同来源7天内相似（阈值降到0.25） ──
    七天前 = datetime.now(tz=CST) - timedelta(days=7)
    for 已发布 in 已发布列表:
        try:
            pub_time = datetime.fromisoformat(已发布.get('发布时间', ''))
            if pub_time < 七天前:
                continue
        except:
            continue
        if 已发布.get('来源') == 当前来源:
            sim = 标题相似度(当前标题, 已发布.get('标题', ''))
            if sim >= 0.3:
                return True, f"同来源7天内相似({sim:.0%}): {已发布.get('标题', '')[:30]}..."

    # ── 第六重：中文汉字重叠度（补充分词缺陷） ──
    # 提取标题中的中文字符集合
    当前中文字 = set(re.findall(r'[\u4e00-\u9fff]', 当前标题))
    if len(当前中文字) >= 4:  # 至少4个中文字才有意义
        for 已发布 in 已发布列表:
            历史中文字 = set(re.findall(r'[\u4e00-\u9fff]', 已发布.get('标题', '')))
            if len(历史中文字) < 4:
                continue
            # 计算汉字重叠率
            重叠 = 当前中文字 & 历史中文字
            # 取两个集合中较小的size做分母
            基准数 = min(len(当前中文字), len(历史中文字))
            重叠率 = len(重叠) / 基准数 if 基准数 > 0 else 0
            if 重叠率 >= 0.65:  # 65%以上的汉字相同→判断为同话题
                重叠字 = ''.join(list(重叠)[:8])
                return True, f"汉字重叠({重叠率:.0%}): {已发布.get('标题', '')[:30]}..."

    # ── 第七重：关键实体匹配（解决中文同话题不同表述问题） ──
    关键实体库 = [
        "微软", "OpenAI", "Anthropic", "DeepSeek", "Google", "GitHub", "Meta",
        "Claude", "Codex", "Copilot", "Cursor", "ChatGPT", "GPT",
        "定价", "涨价", "降价", "Token", "账单", "API", "成本", "模型",
        "裁员", "替代", "失业", "薪资", "面试",
        "开源", "发布", "更新", "版本", "上线",
        "上市公司", "财报", "市值", "融资", "IPO",
        "机器人", "具身", "自动驾驶",
    ]
    当前实体 = {e for e in 关键实体库 if e.lower() in 当前标题.lower()}
    if len(当前实体) >= 1:  # 标题至少包含1个实体才有比较价值
        for 已发布 in 已发布列表:
            历史实体 = {e for e in 关键实体库 if e.lower() in 已发布.get('标题', '').lower()}
            重叠实体 = 当前实体 & 历史实体
            if len(重叠实体) >= 2:  # ≥2个共享实体→同话题
                实体串 = ','.join(list(重叠实体)[:5])
                return True, f"实体重叠({len(重叠实体)}个:{实体串}): {已发布.get('标题', '')[:30]}..."

    return False, ""

def 批量去重(新闻列表: list, history: dict = None) -> tuple:
    if history is None:
        history = 读取发布历史()

    保留列表 = []
    过滤列表 = []

    for item in 新闻列表:
        重复, 原因 = 检查是否重复(item, history)
        if 重复:
            过滤列表.append({**item, "过滤原因": 原因})
            history["统计"]["去重拦截数"] = history["统计"].get("去重拦截数", 0) + 1
        else:
            保留列表.append(item)

    # 保存更新后的拦截统计
    保存发布历史(history)

    return 保留列表, 过滤列表

def 记录发布成功(标题: str, url: str = "", 来源: str = "", 摘要: str = "", 原标题: str = ""):
    """
    记录发布文章到历史

    参数:
        标题: 发布后的文章标题
        url: 原文链接
        来源: 来源渠道
        摘要: 文章摘要
        原标题: 原文RSS标题（与标题不同时填入，增强去重匹配）
    """
    history = 读取发布历史()

    # ── 先检查是否已存在同标题记录 ──
    for 已发布 in history.get("已发布", []):
        if 已发布.get("标题") == 标题:
            print(f"  ⏭️ 已存在同标题记录，跳过: {标题[:40]}...")
            return

    # 原标题指纹：用原标题生成，确保原始文章匹配
    if 原标题 and 原标题 != 标题:
        指纹 = 生成标题指纹(原标题)
        关键词 = 提取关键词(原标题)
    else:
        指纹 = 生成标题指纹(标题)
        关键词 = 提取关键词(标题)

    history["已发布"].append({
        "标题": 标题,
        "URL": url,
        "来源": 来源,
        "摘要": 摘要[:200] if 摘要 else "",
        "发布时间": datetime.now(tz=CST).isoformat(),
        "指纹": 指纹,
        "关键词": 关键词,
    })

    history["统计"]["总发布数"] = len(history["已发布"])

    九十天前 = datetime.now(tz=CST) - timedelta(days=90)
    history["已发布"] = [
        item for item in history["已发布"]
        if datetime.fromisoformat(item["发布时间"]) > 九十天前
    ]

    保存发布历史(history)
    print(f"✅ 已记录发布: {标题[:40]}...")
    print(f"   历史库现有 {len(history['已发布'])} 条记录（保留90天）")

def 打印去重统计(原始数量: int, 保留数量: int, 过滤列表: list):
    过滤数量 = 原始数量 - 保留数量

    print(f"\n📋 去重统计:")
    print(f"   原始: {原始数量} 条")
    print(f"   去重后: {保留数量} 条")
    print(f"   过滤: {过滤数量} 条")

    if 过滤列表:
        print(f"\n🚫 被过滤的重复内容:")
        for i, item in enumerate(过滤列表, 1):
            标题 = item.get('标题', '')[:40]
            原因 = item.get('过滤原因', '')
            print(f"   {i}. {标题}")
            print(f"      → {原因}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 去重工具测试")
    print("=" * 60)

    history = 读取发布历史()
    print(f"\n📊 现有发布历史: {len(history.get('已发布', []))} 条记录")

    test_titles = [
        "DeepSeek 发布新一代 MoE 模型，性能超越 GPT-4",
        "DeepSeek 推出全新 MoE 大模型，效果超过 GPT-4",
        "OpenAI 发布 GPT-5，AI 能力再升级",
    ]

    print("\n🔍 标题指纹测试:")
    for title in test_titles:
        fp = 生成标题指纹(title)
        print(f"   {title[:40]}...")
        print(f"   → 指纹: {fp}")

    print("\n📐 相似度计算:")
    print(f"   标题1 vs 标题2: {标题相似度(test_titles[0], test_titles[1]):.1%}")
    print(f"   标题1 vs 标题3: {标题相似度(test_titles[0], test_titles[2]):.1%}")
