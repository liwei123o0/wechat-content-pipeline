#!/usr/bin/env python3
"""
huashu-wechat-image 适配版 — HTML 截图生成公众号配图
支持：封面图 (2.35:1)、正文数据对比图 (4:3)、信息图 (4:3)
"""
import subprocess, json, re, io
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / "素材"

# ===== 配色方案 =====
STYLES = {
    "暗夜金": {
        "bg": "linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)",
        "bg_flat": "#1A1A2E",
        "title": "#FFFFFF",
        "accent": "#E2B714",
        "subtitle": "#888888",
        "card_bg": "rgba(255,255,255,0.05)",
        "text": "#CCCCCC",
    },
    "极简专业": {
        "bg": "#F5F5F5",
        "bg_flat": "#F5F5F5",
        "title": "#1A1A1A",
        "accent": "#4A90D9",
        "subtitle": "#666",
        "card_bg": "#FFFFFF",
        "text": "#333333",
    },
    "终端绿": {
        "bg": "#0D1117",
        "bg_flat": "#0D1117",
        "title": "#00FF41",
        "accent": "#00FF41",
        "subtitle": "#6E7681",
        "card_bg": "rgba(0,255,65,0.05)",
        "text": "#C9D1D9",
    },
}

def screenshot_html(html_content, output_name, viewport="1440,1080"):
    """用 Playwright 截图 HTML"""
    html_path = IMG_DIR / f"_{output_name}.html"
    img_path = IMG_DIR / output_name
    
    html_path.write_text(html_content, encoding='utf-8')
    
    result = subprocess.run([
        'npx', 'playwright', 'screenshot',
        f'file://{html_path.absolute()}',
        str(img_path),
        f'--viewport-size={viewport}',
        '--wait-for-timeout=1500'
    ], capture_output=True, text=True, timeout=30)
    
    # Clean up temp HTML
    html_path.unlink(missing_ok=True)
    
    if result.returncode == 0 and img_path.exists():
        return img_path
    return None


def generate_cover(title, subtitle="", stats=None, style="暗夜金"):
    """生成封面图 (1800x766, 2.35:1)"""
    s = STYLES.get(style, STYLES["暗夜金"])
    
    # 封面标题限10字
    封面标题 = title[:10] if len(title) > 10 else title
    
    stats_html = ""
    if stats:
        stats_items = ""
        for k, v in list(stats.items())[:3]:
            stats_items += f'<div class="stat"><div class="stat-num">{v}</div><div class="stat-label">{k}</div></div>'
        stats_html = f'<div class="stats">{stats_items}</div>'
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1800px; height: 766px;
  background: {s["bg"]};
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  padding: 60px 400px;
  font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
}}
.icon {{ font-size: 100px; margin-bottom: 15px; }}
.title {{ font-size: 96px; font-weight: 900; color: {s["title"]}; text-align: center; line-height: 1.3; letter-spacing: 4px; }}
.subtitle {{ font-size: 32px; font-weight: 400; color: {s["accent"]}; text-align: center; margin-top: 25px; }}
.accent {{ width: 180px; height: 4px; background: {s["accent"]}; margin: 25px auto; }}
.stats {{ display: flex; gap: 60px; margin-top: 15px; }}
.stat {{ text-align: center; }}
.stat-num {{ font-size: 48px; font-weight: 900; color: {s["accent"]}; }}
.stat-label {{ font-size: 20px; color: {s["subtitle"]}; margin-top: 5px; }}
</style></head><body>
<div class="icon">🪨</div>
<div class="title">{封面标题}</div>
<div class="accent"></div>
<div class="subtitle">{subtitle[:20]}</div>
{stats_html}
</body></html>'''
    
    return screenshot_html(html, f"cover_{datetime.now().strftime('%H%M%S')}.png", "1800,766")


def generate_bar_chart(title, subtitle, items, style="暗夜金"):
    """
    生成数据对比柱状图 (1440x1080, 4:3)
    items: [{"label": "名称", "before": 100, "after": 20, "save": "87%", "color_before": "#ef4444", "color_after": "#22c55e"}, ...]
    """
    s = STYLES.get(style, STYLES["暗夜金"])
    
    max_val = max(max(itm["before"] for itm in items), 1)
    
    rows = ""
    for itm in items:
        before_pct = int(itm["before"] / max_val * 100)
        after_pct = int(itm["after"] / max_val * 100)
        rows += f'''
<div class="row">
  <div class="label">{itm["label"]}</div>
  <div class="bar-area">
    <div class="before-bar" style="width:{before_pct}%">{itm["before"]}</div>
  </div>
  <div class="after-bar" style="width:{after_pct}%">{itm["after"]}</div>
  <div class="save">{itm.get("save", "")}</div>
</div>'''
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1440px; height: 1080px;
  background: {s["bg_flat"]};
  padding: 50px 100px;
  font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  color: {s["text"]};
}}
.heading {{ font-size: 48px; font-weight: 900; margin-bottom: 8px; color: {s["title"]}; }}
.subhead {{ font-size: 26px; color: {s["subtitle"]}; margin-bottom: 45px; }}
.chart {{ display: flex; flex-direction: column; gap: 20px; }}
.row {{ display: flex; align-items: center; gap: 12px; }}
.label {{ width: 120px; font-size: 22px; color: {s["text"]}; text-align: right; }}
.bar-area {{ flex: 1; height: 40px; border-radius: 6px; overflow: hidden; background: rgba(255,255,255,0.05); }}
.before-bar {{ background: #ef4444; height: 40px; display: flex; align-items: center; justify-content: flex-end; padding: 0 8px; color: white; font-size: 16px; font-weight: 700; border-radius: 6px; }}
.after-bar {{ background: #22c55e; height: 40px; display: flex; align-items: center; justify-content: flex-end; padding: 0 8px; color: white; font-size: 16px; font-weight: 700; border-radius: 6px; }}
.save {{ width: 100px; font-size: 24px; font-weight: 900; color: #22c55e; padding-left: 8px; }}
.footer {{ margin-top: 50px; font-size: 22px; color: {s["subtitle"]}; text-align: center; }}
</style></head><body>
<div class="heading">{title[:20]}</div>
<div class="subhead">{subtitle[:30]}</div>
<div class="chart">{rows}</div>
<div class="footer">▲ 红色 = 原始 | 绿色 = 压缩后</div>
</body></html>'''
    
    return screenshot_html(html, f"chart_{datetime.now().strftime('%H%M%S')}.png", "1440,1080")


def generate_comparison_card(title, items, style="暗夜金"):
    """
    生成对比卡片 (1440x1080, 4:3)
    items: [{"name": "名称", "desc": "描述", "tag": "标签", "tag_color": "#22c55e"}, ...]
    """
    s = STYLES.get(style, STYLES["暗夜金"])
    
    cards = ""
    colors = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6"]
    for i, itm in enumerate(items):
        color = colors[i % len(colors)]
        cards += f'''
<div class="card" style="border-left-color:{color};">
  <div class="card-name" style="color:{color};">{itm["name"]}</div>
  <div class="card-desc">{itm["desc"][:80]}</div>
  <div class="card-tag" style="background:{color}22;color:{color};">{itm["tag"]}</div>
</div>'''
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1440px; height: 1080px;
  background: {s["bg_flat"]};
  padding: 50px 100px;
  font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  color: {s["text"]};
}}
.heading {{ font-size: 48px; font-weight: 900; margin-bottom: 35px; color: {s["title"]}; }}
.cards {{ display: flex; flex-direction: column; gap: 30px; }}
.card {{
  background: {s["card_bg"]};
  border-radius: 12px;
  padding: 25px 30px;
  border-left: 6px solid;
  display: flex; align-items: center; gap: 20px;
}}
.card-name {{ font-size: 30px; font-weight: 800; min-width: 200px; }}
.card-desc {{ font-size: 22px; color: {s["subtitle"]}; flex: 1; line-height: 1.5; }}
.card-tag {{ font-size: 26px; font-weight: 700; padding: 6px 20px; border-radius: 20px; }}
.footer {{ margin-top: 40px; font-size: 20px; color: {s["subtitle"]}; text-align: center; }}
</style></head><body>
<div class="heading">{title[:20]}</div>
<div class="cards">{cards}</div>
<div class="footer">▲ HTML渲染 · 文字100%准确</div>
</body></html>'''
    
    return screenshot_html(html, f"comp_{datetime.now().strftime('%H%M%S')}.png", "1440,1080")


def generate_images_for_article(article_path, 选题_info=None):
    """
    根据文章内容自动判断并生成合适的配图
    返回: {"cover": cover_path, "body": [path1, path2]}
    """
    with open(article_path, encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    lines = content.split('\n')
    title = ""
    for line in lines[:5]:
        if line.strip().startswith('# '):
            title = line.strip()[2:].strip()
            break
    if not title:
        title = Path(article_path).stem.replace('文章_', '')
    
    result = {"cover": None, "body": []}
    
    # 判断内容类型
    有数据表 = '|' in content and content.count('|') > 10
    有对比 = any(kw in content for kw in ['vs', '对比', '相比', '优于', '压缩'])
    有分级 = any(kw in content for kw in ['模式', '方案', '路径', '级别'])
    
    # === 封面 ===
    封面标题 = title[:10]
    副标题 = title[10:30] if len(title) > 10 else "微信公众号"
    
    stats = None
    # 尝试从文章提取关键数字
    pct_match = re.findall(r'(\d+)%', content)
    if pct_match:
        stats = {"压缩率": f"{pct_match[0]}%"}
        if len(pct_match) > 1:
            stats["节省"] = f"{pct_match[1]}%"
    
    cover_path = generate_cover(封面标题, 副标题, stats, "暗夜金")
    if cover_path:
        result["cover"] = cover_path
    
    # === 正文配图 ===
    if 有数据表 or 有对比:
        # 生成数据对比图
        items = []
        # 尝试从 markdown 表格提取数据
        table_rows = re.findall(r'^\|(.+?)\|$', content, re.M)
        for row in table_rows[2:5]:  # 跳过表头
            cols = [c.strip() for c in row.split('|')]
            if len(cols) >= 4:
                try:
                    before = int(re.sub(r'[^\d]', '', cols[1]))
                    after = int(re.sub(r'[^\d]', '', cols[2]))
                    save = cols[3] if len(cols) > 3 else f"{int((before-after)/before*100)}%"
                    items.append({"label": cols[0][:8], "before": before, "after": after, "save": save})
                except:
                    pass
        
        if items:
            chart_path = generate_bar_chart(f"{title[:15]}对比", "数据可视化", items, "暗夜金")
            if chart_path:
                result["body"].append(chart_path)
    
    if 有分级:
        # 生成对比卡片
        mode_items = []
        mode_pattern = re.findall(r'(?:###?\s+)?(\S+(?:模式|方案|路径|级别))[：:]\s*(.+?)(?=\n|$)', content)
        for name, desc in mode_items[:4]:
            mode_items.append({"name": name[:10], "desc": desc[:60], "tag": name[:4]})
        
        if not mode_items:
            # Fallback: 手动指定
            mode_items = [
                {"name": "Lite 轻量", "desc": "去掉废话填充词，最适合日常对话", "tag": "~25%"},
                {"name": "Full 标准", "desc": "去掉不必要修饰，保留技术精确性", "tag": "~65%"},
                {"name": "Ultra 极致", "desc": "电报体，极致精简到只剩关键信息", "tag": "~75%"},
            ]
        
        comp_path = generate_comparison_card(f"{title[:15]}模式", mode_items, "暗夜金")
        if comp_path:
            result["body"].append(comp_path)
    
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        article = sys.argv[1]
        print(f"生成配图: {article}")
        imgs = generate_images_for_article(article)
        print(json.dumps({"cover": str(imgs.get("cover", "")), "body": [str(p) for p in imgs.get("body", [])]}, ensure_ascii=False))
