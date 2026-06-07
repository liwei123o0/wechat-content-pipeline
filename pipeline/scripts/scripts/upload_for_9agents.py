#!/usr/bin/env python3
"""Upload 9-Agent article images to WeChat"""

import sys, json, io
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import importlib.util
spec = importlib.util.spec_from_file_location("publish_v3", str(BASE_DIR / "publish_v3.py"))
publish_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_v3)

import requests
from PIL import Image as PILImg

WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}"
    resp = requests.get(url, timeout=15).json()
    if "access_token" in resp:
        return resp["access_token"]
    raise RuntimeError(f"Token获取失败: {resp}")

def upload_cover(access_token, img_path):
    with open(img_path, "rb") as f:
        img_data = f.read()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    resp = requests.post(url, files={"media": ("cover.jpg", img_data, "image/jpeg")}, timeout=30).json()
    if "media_id" in resp:
        return resp["media_id"]
    img = PILImg.open(img_path).convert("RGB")
    img = img.resize((1280, 544), PILImg.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    resp2 = requests.post(url, files={"media": ("cover.jpg", buf.read(), "image/jpeg")}, timeout=30).json()
    if "media_id" in resp2:
        return resp2["media_id"]
    raise RuntimeError(f"封面上传失败: {resp} / {resp2}")

def upload_body_image(access_token, img_path):
    img = PILImg.open(img_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    resp = requests.post(url, files={"media": ("img.jpg", buf.read(), "image/jpeg")}, timeout=30).json()
    if "url" in resp:
        return resp["url"]
    raise RuntimeError(f"正文图片上传失败: {resp}")

def update_frontmatter(content, cover_media_id, body_urls):
    lines = content.split("\n")
    fm_end = None
    fm_start = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break
    if fm_end is None:
        return content

    new_fields = [f"cover_media_id: {cover_media_id}", "cover_source: huashu_html"]
    if body_urls:
        new_fields.append("body_image_urls:")
        for url in body_urls:
            new_fields.append(f"  - {url}")

    new_lines = []
    closing_fm_pos = None
    for i, line in enumerate(lines):
        if i <= fm_start or i >= fm_end:
            new_lines.append(line)
            if i == fm_end:
                closing_fm_pos = len(new_lines) - 1
            continue
        if line.startswith("cover:"):
            new_lines.append(f"# {line}  # replaced")
            continue
        if line.startswith("cover_media_id:") or line.startswith("cover_source:") or line.startswith("body_image_urls:"):
            continue
        new_lines.append(line)

    if closing_fm_pos is None:
        closing_fm_pos = len(new_lines) - 1
    for field in reversed(new_fields):
        new_lines.insert(closing_fm_pos, field)

    return "\n".join(new_lines)

# === Main ===
article_path = BASE_DIR / "创作" / "article_hermes_pipeline_20260605.md"
cover_path = BASE_DIR / "素材" / "cover_9agents.png"
body1_path = BASE_DIR / "素材" / "body_9agents.png"
body2_path = BASE_DIR / "素材" / "body_timeline.png"

print("🔄 Getting access token...")
token = get_access_token()
print(f"✅ Token obtained")

print("🔄 Uploading cover...")
media_id = upload_cover(token, str(cover_path))
print(f"✅ Cover media_id: {media_id}")

print("🔄 Uploading body image 1 (architecture)...")
url1 = upload_body_image(token, str(body1_path))
print(f"✅ Body URL 1: {url1}")

print("🔄 Uploading body image 2 (timeline)...")
url2 = upload_body_image(token, str(body2_path))
print(f"✅ Body URL 2: {url2}")

body_urls = [url1, url2]

print("🔄 Updating frontmatter...")
content = article_path.read_text(encoding="utf-8")
updated = update_frontmatter(content, media_id, body_urls)
article_path.write_text(updated, encoding="utf-8")
print("✅ Frontmatter updated")

# Verify
content = article_path.read_text(encoding="utf-8")
print("--- Updated frontmatter ---")
for line in content.split("\n")[:15]:
    print(f"  {line}")

print(f"\n✅ All done! Cover media_id: {media_id}")
for i, url in enumerate(body_urls):
    print(f"   Body {i+1}: {url}")
