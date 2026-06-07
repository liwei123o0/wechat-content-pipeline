#!/usr/bin/env python3
"""AI HOT 素材采集 - 作为公众号流水线的补充素材源"""
import json, urllib.request, os, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 aihot-skill/0.2.0"
BASE = "https://aihot.virxact.com"

BASE_DIR = Path(__file__).parent

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def main():
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")
    
    # 1. 拉日报结构（获取栏目分类）
    daily = fetch(f"{BASE}/api/public/daily")
    date = daily.get("date", today)
    
    # 2. 拉最近24h精选
    since = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT00:00:00Z")
    items = fetch(f"{BASE}/api/public/items?mode=selected&since={since}&take=100")
    hot_items = items.get("items", [])
    
    # 3. 拉各类别精选（模型、产品、行业、论文）
    all_items = []
    for cat in ["ai-models", "ai-products", "industry", "paper"]:
        cat_items = fetch(f"{BASE}/api/public/items?mode=selected&category={cat}&since={since}&take=50")
        all_items.extend(cat_items.get("items", []))
    
    # 4. 去重合并
    seen_titles = set()
    merged = []
    for item in hot_items + all_items:
        title = item.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            merged.append(item)
    
    # 5. 保存为素材文件
    素材_dir = BASE_DIR / "素材"
    素材_dir.mkdir(parents=True, exist_ok=True)
    
    output = {
        "来源": "AI HOT",
        "采集时间": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "日报日期": date,
        "日报": daily,
        "精选条目": merged,
        "条目数量": len(merged),
    }
    
    filepath = 素材_dir / f"aihot_素材_{date}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ AI HOT 素材已保存: {filepath}")
    print(f"   日报日期: {date}")
    print(f"   精选+分类条目: {len(merged)} 条")
    
    # 输出摘要给下游使用
    print(f"\n--- AI HOT 素材摘要 ---")
    print(f"来源: AI HOT (aihot.virxact.com)")
    
    if daily.get("sections"):
        for sec in daily["sections"]:
            label = sec.get("label", "")
            sec_items = sec.get("items", [])
            top3 = [it.get("title", "?")[:50] for it in sec_items[:3]]
            print(f"  📰 {label} ({len(sec_items)}条)")
            for t in top3:
                print(f"    • {t}")
    
    if merged:
        print(f"\n  🔥 精选头条 (共{len(merged)}条)")
        for item in merged[:5]:
            title = item.get("title", "?")[:60]
            source = item.get("source", "?")
            print(f"    • [{source}] {title}")

if __name__ == "__main__":
    main()
