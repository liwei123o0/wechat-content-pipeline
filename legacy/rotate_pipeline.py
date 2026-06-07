#!/usr/bin/env python3
"""轮转测试：每天跑一个不同栏目的文章，追踪哪个类型受欢迎"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
STATE_FILE = BASE / "rotation_state.json"

# 7个栏目按测试顺序排列
COLUMNS_CYCLE = [
    "vibe-coding",     # 1. Vibe Coding实战
    "ai-tools",        # 2. AI工具解剖
    "agent-money",     # 3. Agent搞钱拆解
    "ai-career",       # 4. 程序员AI生存法则
    "pitfalls",        # 5. 踩坑复盘
    "weekly-ops",      # 6. 本周AI变现机会
    "frontier-news",   # 7. AI前沿资讯
]

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"index": -1, "last_run": None, "history": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_next_column():
    state = load_state()
    next_idx = (state["index"] + 1) % len(COLUMNS_CYCLE)
    slug = COLUMNS_CYCLE[next_idx]
    
    state["index"] = next_idx
    state["last_run"] = datetime.now().isoformat()
    state["history"].append({
        "time": datetime.now().isoformat(),
        "column": slug,
        "round": len([h for h in state["history"] if h["column"] == slug]) + 1
    })
    state["history"] = state["history"][-50:]
    save_state(state)
    return slug

def show_status():
    state = load_state()
    if state["last_run"]:
        print(f"📊 轮转测试状态")
        last_slug = state['history'][-1]['column'] if state['history'] else '无'
        print(f"   上次: {state['last_run'][:16]} → {last_slug}")
        print(f"   已跑: {len(state['history'])} 篇\n")
        for slug in COLUMNS_CYCLE:
            count = len([h for h in state["history"] if h["column"] == slug])
            bar = "█" * count
            print(f"     {slug:20s} {count}次 {bar}")
    else:
        print("📊 尚未开始轮转测试")

def run_pipeline(slug):
    """运行主管线（单篇模式）"""
    pipeline = BASE / "run_pipeline.py"
    print(f"\n▶️ 今日测试栏目: {slug}（第{len([h for h in load_state()['history'] if h['column'] == slug])}轮）")
    print(f"   共 {len(COLUMNS_CYCLE)} 个栏目轮转测试中\n")
    
    result = subprocess.run(
        [sys.executable, str(pipeline), "--column", slug],
        cwd=str(BASE),
        capture_output=False
    )
    return result.returncode == 0

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        show_status()
    else:
        success = run_pipeline(get_next_column())
        sys.exit(0 if success else 1)
