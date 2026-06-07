#!/usr/bin/env python3
"""Send agent_comm messages: notify quality-reviewer + hand off to publisher."""
import sys, re
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
from agent_comm import send

DATA = BASE / "data" / "创作"
article_path = str(DATA / "article_hermes_pipeline_20260605.md")
html_path = str(DATA / "article_hermes_pipeline_20260605.html")
content = Path(article_path).read_text(encoding="utf-8")

# Extract cover_media_id and body URLs
m = re.search(r"cover_media_id:\s*(\S+)", content)
media_id = m.group(1) if m else "N/A"

body_urls = re.findall(r"body_image_urls:\n((?:\s+-\s+\S+\n?)+)", content)
urls = re.findall(r"-\s+(\S+)", body_urls[0]) if body_urls else []

html_content = Path(html_path).read_text(encoding="utf-8")

print(f"📤 Sending to publisher: media_id={media_id}, urls={len(urls)}")

# Send to publisher
msg = send(
    to_role="publisher",
    from_role="designer",
    msg_type="task",
    payload={
        "title": "我在公众号后台塞了9个AI Agent，让它们互相审查对方的稿子",
        "author": "Python工作圈",
        "cover_media_id": media_id,
        "body_image_urls": urls,
        "formatted_html": html_content,
        "html_path": html_path,
        "md_path": article_path,
        "column_slug": "frontier-news",
        "style": "news (紧凑蓝调·AI资讯类)",
        "summary": "配图+排版完成: 9-Agent文章 → 暗夜蓝紫大字报封面, 2张正文配图(架构图+时间线, 微信CDN), frontier-news蓝调紧凑排版, 参考资料弱化"
    }
)

print(f"✅ Sent to publisher: msg_id={msg['id']}")

# Confirm to quality-reviewer
send(
    to_role="quality-reviewer",
    from_role="designer",
    msg_type="reply",
    payload={
        "text": "✅ 配图排版已完成，已通知 publisher 发布。",
        "summary": "封面: 暗夜蓝紫大字报(9个AI Agent互相审查) | 正文: 9-Agent架构图 + 25min时间线 | 排版: frontier-news蓝调紧凑",
        "publisher_msg_id": msg["id"]
    }
)

print(f"✅ Notified quality-reviewer")
print(f"🎉 All done!")
