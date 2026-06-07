#!/usr/bin/env python3
"""Format the 9-Agent article with frontier-news style, insert body images."""
import sys, re
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

from design_layout import format_article

DATA = BASE / "data" / "创作"
article_path = str(DATA / "article_hermes_pipeline_20260605.md")
output_path = str(DATA / "article_hermes_pipeline_20260605.html")

with open(article_path, encoding="utf-8") as f:
    md_text = f.read()

# Format with frontier-news (news style)
html = format_article(md_text, column_slug="frontier-news")
print(f"✅ Formatted with frontier-news style (style_news)")
print(f"   HTML length: {len(html)} chars")

# Body image URLs
body_url_1 = "http://mmbiz.qpic.cn/sz_mmbiz_jpg/g2N1jStgNl0PNicIZmYGu016LfD3oQLWAMe7T64enjXGtJf1DSDnOfWDw8rdRDiaDiacwxplFrFfaWcLl2trmGb4yic3VdBpWKorR52euRaicYI4/0?from=appmsg"
body_url_2 = "http://mmbiz.qpic.cn/sz_mmbiz_jpg/g2N1jStgNl3e4RcibUvmGWarmgpkVPGcwBV1zt1qh9rnGBibiaicIzZURQo4nictYmKWw7ckWvFrsdAP2glxCH3zle0iaxDywuciaA5endib2CdTPO8/0?from=appmsg"

# Image HTML tags with style matching style_news
img_style = 'margin:0 0 14px;text-align:center;'
img_tag_1 = f'<p style="{img_style}"><img src="{body_url_1}" alt="9个AI Agent流水线架构图" style="width:100%;border-radius:6px;max-width:700px;"/></p>'
img_tag_2 = f'<p style="{img_style}"><img src="{body_url_2}" alt="25分钟全链时间线" style="width:100%;border-radius:6px;max-width:700px;"/></p>'

# Insert after "说一下技术架构" paragraph (end of intro for section 2)
pos_1 = html.find('说一下技术架构')
if pos_1 > 0:
    end_p1 = html.find('</p>', pos_1)
    if end_p1 > 0:
        insert_1 = end_p1 + 4
        html = html[:insert_1] + '\n' + img_tag_1 + '\n' + html[insert_1:]
        print(f"✅ Inserted architecture diagram after '说一下技术架构'")
else:
    print(f"⚠️ Could not find '说一下技术架构'")

# Insert after "流水线文档里记录" paragraph (intro for section 3)
pos_2 = html.find('流水线文档里记录了')
if pos_2 < 0:
    # Try simplified text
    pos_2 = html.find('流水线文档')
if pos_2 > 0:
    end_p2 = html.find('</p>', pos_2)
    if end_p2 > 0:
        insert_2 = end_p2 + 4
        html = html[:insert_2] + '\n' + img_tag_2 + '\n' + html[insert_2:]
        print(f"✅ Inserted timeline after '流水线文档里记录了'")
else:
    print(f"⚠️ Could not find '流水线文档'")

# Save
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n✅ Saved formatted article to: {output_path}")
print(f"   Final HTML length: {len(html)} chars")

# Print first 100 and last 200 chars to verify
print("--- First 200 chars ---")
print(html[:200])
print("--- Last 200 chars ---")
print(html[-200:])
