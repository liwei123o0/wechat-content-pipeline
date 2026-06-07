#!/usr/bin/env python3
"""
微信公众号内容创作 - Step 3: 深度搜索（Tavily集成版）

设计：
1. 生成模式（默认）：读取选题，生成搜索query，输出JSON供agent读取
2. 汇总模式（--consolidate）：agent搜索完成后，汇总为深度素材

工作流：
   step3_深度搜索.py              → 生成搜索任务
   agent读取任务，web_search每个   → 执行搜索
   step3_深度搜索.py --consolidate → 汇总为深度素材

关键改进：
- query输出格式专为agent的web_search工具设计
- 搜索任务按选题分组，agent可逐个调用
- 汇总模式可累积多轮搜索结果
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).parent

# ============================================================
# 读取选题
# ============================================================
def 读取最新选题(栏目slug: str = None):
    """读取最新的选题文件，可指定栏目"""
    整理_dir = CURRENT_DIR / "整理"
    if 栏目slug:
        files = list(整理_dir.glob(f"选题_{栏目slug}_*.json"))
    if not 栏目slug or (栏目slug and not files):
        files = list(整理_dir.glob("选题_AI科技_*.json"))
        if not files:
            files = list(整理_dir.glob("选题_*.json"))
    if not files:
        print("⚠️ 未找到选题数据")
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)
    print(f"📖 读取 {latest.name}")
    return data

# ============================================================
# 生成搜索查询
# ============================================================
def 生成搜索查询(标题: str, 摘要: str = "", 来源: str = "") -> list:
    """为一个选题生成多角度搜索query"""
    # 从标题提取核心内容（去掉来源前缀和标点）
    核心词 = re.sub(r'^.*?[|:：]', '', 标题).strip()
    核心词 = re.sub(r'[^\w\u4e00-\u9fff\s]', '', 核心词)
    核心词 = re.sub(r'\s+', ' ', 核心词).strip()
    if len(核心词) > 30:
        核心词 = 核心词[:30]

    queries = [
        {"角度": "核心信息", "query": f"{核心词} 最新 2026"},
        {"角度": "背景分析", "query": f"{核心词} 背景 原因 分析"},
        {"角度": "深入解读", "query": f"{核心词} 技术 原理 详情"},
    ]

    # 如果是AI/技术类主题，补充技术解读
    if any(kw in 标题 for kw in ["AI", "模型", "开源", "GitHub", "Agent", "智能体", "芯片", "框架", "架构"]):
        queries.append({"角度": "技术细节", "query": f"{核心词} 技术细节 设计 原理"})

    # 如果是商业/融资类主题，补充行业背景
    if any(kw in 标题 for kw in ["融资", "收购", "上市", "IPO", "估值", "独角兽"]):
        queries.append({"角度": "行业分析", "query": f"{核心词} 行业 市场 前景"})

    return queries

# ============================================================
# 生成搜索任务（供agent读取）
# ============================================================
def 生成搜索任务(热度排行: list, top_n: int = 3) -> list:
    """
    生成搜索任务列表，格式如下：
    [
        {
            "task_id": "task_1",
            "选题": "...",
            "角度": "核心信息",
            "query": "...",
            "来源": "...",
            "摘要": "..."
        },
        ...
    ]
    """
    tasks = []
    for i, 选题 in enumerate(热度排行[:top_n], 1):
        标题 = 选题.get('标题', 选题.get('title', ''))
        摘要 = 选题.get('摘要', 选题.get('description', ''))[:200]
        来源 = 选题.get('来源', 选题.get('source', ''))
        url = 选题.get('url', 选题.get('链接', ''))

        queries = 生成搜索查询(标题, 摘要, 来源)

        for q in queries:
            tasks.append({
                "task_id": f"task_{i}",
                "选题": 标题,
                "来源": 来源,
                "链接": url,
                "角度": q["角度"],
                "query": q["query"],
                "摘要": 摘要,
            })

    return tasks

# ============================================================
# 读取搜索结果
# ============================================================
def 读取搜索结果() -> list:
    """读取已保存的搜索结果"""
    结果_path = CURRENT_DIR / "data" / "素材" / "search_results.json"
    if not 结果_path.exists():
        return []
    with open(结果_path, encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except:
            return []

# ============================================================
# 合并搜索结果到深度素材
# ============================================================
def 汇总深度素材() -> str:
    """
    读取搜索任务 + 搜索结果，汇总为深度素材文件
    返回保存的文件名（路径）
    """
    素材_dir = CURRENT_DIR / "data" / "素材"
    素材_dir.mkdir(exist_ok=True)

    # 读取最新搜索任务
    task_files = list(素材_dir.glob("搜索任务_*.json"))
    if not task_files:
        print("⚠️ 未找到搜索任务文件")
        return None
    latest_task = max(task_files, key=lambda p: p.stat().st_mtime)
    with open(latest_task, encoding='utf-8') as f:
        task_data = json.load(f)
    任务列表 = task_data.get("任务列表", [])

    if not 任务列表:
        print("⚠️ 搜索任务列表为空")
        return None

    # 读取搜索结果
    搜索结果 = 读取搜索结果()
    print(f"📖 读取 {len(搜索结果)} 条搜索结果")

    # 按task_id分组
    results_by_task = {}
    for item in 搜索结果:
        tid = item.get("task_id", "")
        if tid not in results_by_task:
            results_by_task[tid] = []
        results_by_task[tid].append(item)

    # 汇总
    tm = datetime.now()
    timestamp = tm.strftime("%Y%m%d_%H%M%S")

    素材汇总 = []
    seen_tasks = set()
    for task in 任务列表:
        tid = task["task_id"]
        if tid in seen_tasks:
            continue
        seen_tasks.add(tid)

        task_results = results_by_task.get(tid, [])

        素材项 = {
            "选题": task["选题"],
            "来源": task.get("来源", ""),
            "链接": task.get("链接", ""),
        }

        # 组织该任务下所有搜索的结果
        所有结果 = []
        for tr in task_results:
            所有结果.append({
                "角度": tr.get("角度", ""),
                "query": tr.get("query", ""),
                "结果": tr.get("web_results", []),
            })

        素材项["搜索结果"] = 所有结果
        素材汇总.append(素材项)

        print(f"  📌 [{tid}] {task['选题'][:40]}... → {len(task_results)} 条搜索结果")

    # 保存
    output = {
        "生成时间": tm.isoformat(),
        "选题数量": len(素材汇总),
        "素材汇总": 素材汇总,
    }

    output_file = 素材_dir / f"深度素材_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 深度素材已保存: {output_file.name}")
    print(f"   📊 共 {len(素材汇总)} 个选题的深度素材")
    return str(output_file)

# ============================================================
# 生成搜索任务供agent使用（输出为JSON格式）
# ============================================================
def 输出搜索指令(任务列表: list):
    """
    输出 agent 可直接解析的搜索指令
    每个条目独立，agent逐个调用 web_search(query, limit=5)
    """
    print("\n" + "=" * 60)
    print("🤖 搜索指令（给agent的JSON格式任务列表）")
    print("=" * 60)
    print()
    print("请使用 web_search 工具执行以下每个搜索，并保存结果：")
    print()
    for task in 任务列表:
        print(f"📌 [{task['task_id']}] {task['选题'][:50]}")
        print(f"   来源: {task['来源']} | 链接: {task['链接']}")
        print(f"   摘要: {task['摘要'][:100]}...")
        print()

    print("执行步骤：")
    print("1. 对每个任务调用：web_search(query='...', limit=5)")
    print("2. 将结果写入文件：素材/search_results.json")
    print("   每执行一个搜索就追加一条记录")
    print("3. 全部完成后运行：python step3_深度搜索.py --consolidate")
    print()

    # 输出可复用的JSON
    print("📋 任务列表(JSON):")
    print(json.dumps(任务列表, ensure_ascii=False, indent=2))
    print()

# ============================================================
# 保存搜索任务（供agent/consolidate使用）
# ============================================================
def 保存搜索任务(任务列表: list):
    素材_dir = CURRENT_DIR / "data" / "素材"
    素材_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_file = 素材_dir / f"搜索任务_{timestamp}.json"
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump({
            "生成时间": datetime.now().isoformat(),
            "任务列表": 任务列表,
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索任务已保存: {task_file.name}\n")
    return task_file

# ============================================================
# 保存搜索结果（由agent调用，或通过--save标志由脚本读取JSON后保存）
# ============================================================
def 保存搜索结果(结果列表: list):
    """追加搜索结果到search_results.json"""
    结果_path = CURRENT_DIR / "data" / "素材" / "search_results.json"
    
    # 读取现有结果
    现有结果 = 读取搜索结果()
    
    # 按task_id+query去重后追加
    seen = {(r.get("task_id", ""), r.get("query", "")) for r in 现有结果}
    for r in 结果列表:
        key = (r.get("task_id", ""), r.get("query", ""))
        if key not in seen:
            现有结果.append(r)
            seen.add(key)
    
    (CURRENT_DIR / "data" / "素材").mkdir(exist_ok=True)
    with open(结果_path, 'w', encoding='utf-8') as f:
        json.dump(现有结果, f, ensure_ascii=False, indent=2)
    print(f"💾 搜索结果已保存到 search_results.json（共 {len(现有结果)} 条）")

# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("🔍 Step 3: 深度搜索（Tavily集成版）v3")
    print("=" * 60)

    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="generate",
                       help="generate | consolidate | --save-results")
    parser.add_argument("--column", "-c", help="栏目slug")
    # --consolidate is handled manually below
    args, unknown = parser.parse_known_args()

    mode = args.mode
    if "--consolidate" in sys.argv or mode == "consolidate":
        mode = "--consolidate"
    栏目slug = args.column

    if mode == "--consolidate":
        汇总深度素材()
        print("\n✅ Step 3 汇总完成!")
        return

    if mode == "--save-results":
        input_text = sys.stdin.read()
        try:
            结果列表 = json.loads(input_text)
            保存搜索结果(结果列表)
        except:
            print("⚠️ 无法解析JSON输入")
        return

    # 生成模式（默认）
    选题数据 = 读取最新选题(栏目slug)
    if not 选题数据:
        return

    # 优先使用"综合推荐"（24h内AI内容 + 备选超时AI内容）
    选题列表 = 选题数据.get('综合推荐', [])
    if not 选题列表:
        # 兼容旧版本数据
        选题列表 = 选题数据.get('热度排行', [])
    if not 选题列表:
        print("⚠️ 综合推荐为空，尝试备选超时")
        选题列表 = 选题数据.get('备选超时', [])
    
    if not 选题列表:
        print("⚠️ 无选题数据")
        return

    print(f"📋 共 {len(选题列表)} 个候选选题")
    
    任务列表 = 生成搜索任务(选题列表, top_n=1)
    保存搜索任务(任务列表)

    # 输出给agent的直接搜索指令
    输出搜索指令(任务列表)

    print(f"📊 共 {len(任务列表)} 个搜索任务（{len(set(t['task_id'] for t in 任务列表))} 个选题 × 多角度）")
    print()
    print("=" * 60)
    print("✅ Step 3 搜索任务已就绪!")
    print("   下一步：agent执行搜索 → 结果保存 → --consolidate 汇总")
    print("=" * 60)


if __name__ == "__main__":
    main()
