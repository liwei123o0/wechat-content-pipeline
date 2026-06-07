#!/usr/bin/env python3
"""
微信公众号内容工作流 - 一键运行脚本
采集 -> 选题 -> 深度搜索 -> 创作 -> 发布
"""
import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
PYTHON = sys.executable

def run_step(script_name, description):
    """运行一个步骤"""
    print(f"\n{'='*60}")
    print(f"🚀 运行: {description}")
    print(f"📄 脚本: {script_name}")
    print(f"{'='*60}")
    
    cmd = [PYTHON, str(BASE_DIR / script_name)]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=600)
    
    print(result.stdout)
    if result.stderr:
        print(f"⚠️  stderr: {result.stderr}")
    
    if result.returncode != 0:
        print(f"❌ {description} 失败，返回码: {result.returncode}")
        return False
    
    print(f"✅ {description} 完成!")
    return True

def main():
    print("🚀 开始运行微信公众号内容工作流")
    print(f"📍 工作目录: {BASE_DIR}")
    print(f"🐍 Python: {PYTHON}")
    
    # Step 1: 采集
    if not run_step("step1a_采集_AI科技.py", "Step 1: RSS 采集"):
        return 1
    
    # Step 2: 选题
    if not run_step("step2_选题_AI科技.py", "Step 2: 去重 + 选题"):
        return 1
    
    # Step 3: 深度搜索 (生成任务 + 执行搜索 + 汇总)
    print(f"\n{'='*60}")
    print("🚀 运行: Step 3: 深度搜索")
    print(f"{'='*60}")
    
    # 3a: 生成搜索任务
    cmd = [PYTHON, str(BASE_DIR / "step3_深度搜索.py")]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=120)
    print(result.stdout)
    if result.returncode != 0:
        print("❌ 生成搜索任务失败")
        return 1
    
    print("✅ Step 3 完成!")
    
    print(f"\n{'='*60}")
    print("✅ 工作流前三步完成！")
    print("📝 后续步骤（文章创作 + 发布）需要在 Hermes Agent 上下文中运行")
    print(f"{'='*60}")
    print("\n📋 已生成文件:")
    print("  - 整理/选题_AI科技_*.json (选题结果)")
    print("  - 素材/搜索_任务_*.json (搜索任务)")
    print("  - 素材/深度素材_*.json (深度素材汇总)")
    print("\n💡 提示: 文章创作和发布需要 Agent 调用工具，")
    print("   请在 Hermes 对话中调用「发布最新文章」功能完成最后两步。")
    
    return 0

if __name__ == "__main__":
    exit(main())
