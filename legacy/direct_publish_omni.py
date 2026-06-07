#!/usr/bin/env python3
"""直接发布指定文章到微信公众号草稿箱"""
import json, sys, io, re, time
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from publish_v3 import get_access_token, markdown_to_html
from account_config import get_account

# 文章路径
article_path = BASE / "创作" / "文章_谷歌Omni世界模型_20260522.md"
cover_path = BASE / "素材" / "cover_201706.png"

# 1. 读取文章
with open(article_path, encoding='utf-8') as f:
    content = f.read()

# 提取标题（从 frontmatter）
title_match = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
title = title_match.group(1).strip() if title_match else article_path.stem
print(f"📄 标题: {title}")

# 2. 获取 access_token
token = get_access_token()
if not token:
    print("❌ token获取失败")
    sys.exit(1)

# 3. 上传封面图 → media_id
print(f"\n🖼️ 上传封面: {cover_path.name}")
from PIL import Image
img = Image.open(cover_path).convert('RGB')
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
buf.seek(0)
cover_data = buf.read()

boundary = "----Boundary" + str(int(time.time()))
body_parts = []
body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
body_parts.append(cover_data)
body_parts.append(f"\r\n--{boundary}--\r\n".encode())
body = b"".join(body_parts)

import urllib.request
url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        thumb_media_id = result["media_id"]
        print(f"  ✅ media_id: {thumb_media_id[:30]}...")
    else:
        print(f"  ❌ 封面上传失败: {result}")
        if result.get("errcode") == 40164:
            print("  ⚠️ 出口IP不在白名单，需要先加白")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ 上传异常: {e}")
    sys.exit(1)

# 4. 转换 Markdown → HTML
html_content = markdown_to_html(content)

# 限制长度
if len(html_content) > 60000:
    html_content = html_content[:60000]
    print("  ⚠️ 正文超长，已截断")

# 5. 创建草稿
cfg = get_account()
body = {
    "articles": [{
        "title": title,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "author": cfg.get("author", "Python工作圈"),
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }]
}

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
data = json.dumps(body, ensure_ascii=False).encode("utf-8")
draft_req = urllib.request.Request(draft_url, data=data, method="POST")
draft_req.add_header("Content-Type", "application/json; charset=utf-8")

try:
    with urllib.request.urlopen(draft_req, timeout=30) as resp:
        draft_result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in draft_result:
        print(f"\n✅ 发布成功！media_id: {draft_result['media_id']}")
        print(f"   🏷️  标题: {title}")
        # 记录到发布历史
        try:
            sys.path.insert(0, str(BASE))
            from 发布历史_去重 import 记录发布成功
            记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300])
        except Exception as e:
            print(f"   ⚠️ 记录发布历史失败: {e}")
    else:
        print(f"\n❌ 发布失败: {draft_result}")
except Exception as e:
    print(f"\n❌ 发布异常: {e}")
