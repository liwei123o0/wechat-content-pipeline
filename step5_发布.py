#!/usr/bin/env python3
"""
微信公众号 Step 5: 发布 v3.3
直接 import publish_v3 的 markdown_to_html 和 http_request
"""

import json
import os
import re
import sys
import io
import shutil
from pathlib import Path
from datetime import datetime

# Add project dir to path
PROJECT_DIR = str(Path(__file__).parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Direct imports - no importlib magic
from publish_v3 import markdown_to_html, http_request
from 发布历史_去重 import 记录发布成功

WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"


def get_access_token():
    import requests
    r = requests.get(
        f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}",
        timeout=15
    )
    return r.json().get("access_token", "")


def generate_cover(title):
    """暗夜大字报封面"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 383), (11, 17, 32))
    draw = ImageDraw.Draw(img)

    # Green accents
    draw.rectangle([40, 60, 140, 63], fill=(34, 197, 94))
    draw.rectangle([40, 320, 140, 323], fill=(34, 197, 94))

    try:
        # 优先中文字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 34, index=0)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 18, index=0)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            font = font_small = ImageFont.load_default()

    lines = []
    current = ""
    for ch in title[:24]:
        current += ch
        if len(current) >= 10:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)

    y = 100
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (900 - w) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += 55

    draw.text((350, 330), "Python工作圈 · 2026", fill=(100, 116, 139), font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()

    import requests
    token = get_access_token()
    files = {"media": ("cover.jpg", img_bytes, "image/jpeg")}
    r = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        files=files, timeout=30
    )
    return r.json().get("media_id", "")


def create_draft(title, author, html_content, thumb_media_id, digest=""):
    token = get_access_token()
    if not token:
        return {}

    body = {
        "articles": [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": html_content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
            "show_cover_pic": 1,
        }]
    }

    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    return http_request(url, body, "POST")


def 获取文件名(栏目slug=None):
    创作_dir = Path(__file__).parent / "创作"
    if 栏目slug:
        md_files = list(创作_dir.glob(f"文章_{栏目slug}_*.md"))
    if not md_files:
        return None
    return max(md_files, key=lambda p: p.stat().st_mtime)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--column", "-c", help="栏目slug")
    args = parser.parse_args()
    栏目slug = args.column

    print("=" * 60)
    print("📤 Step 5: 发布 v3.3 (direct import)")
    print("=" * 60)

    md_file = 获取文件名(栏目slug)
    if not md_file:
        print("没有找到待发布的文章")
        return

    print(f"\n📄 {md_file.name}")

    with open(md_file, encoding="utf-8") as f:
        content = f.read()

    title_match = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
    title = title_match.group(1).strip() if title_match else md_file.stem
    # 清洗标题：替换单引号为中文引号
    title = title.replace("'", "\\u2018").replace("'", "\\u2019")
    print(f"   标题: {title}")

    # ── 1. 封面+配图生成（generate_article_covers.py --pro） ──
    print(f"\n🖼️ 生成封面+配图...")
    import subprocess
    gc_result = subprocess.run(
        ["python3", str(Path(__file__).parent / "generate_article_covers.py"), str(md_file), "--pro"],
        capture_output=True, text=True, timeout=120
    )
    if gc_result.returncode == 0 and "cover_media_id" in gc_result.stdout:
        print(f"   ✅ generate_article_covers --pro 成功")
        # Reload article (frontmatter was updated with cover_media_id and body_image_urls)
        content = md_file.read_text(encoding="utf-8")
    else:
        print(f"   ⚠️ generate_article_covers 失败，回退 PIL 封面")
        thumb_media_id = generate_cover(title)
        if not thumb_media_id:
            print("❌ 封面上传失败")
            return
        print(f"   ✅ PIL封面: {thumb_media_id[:20]}...")

    # Get thumb_media_id: prefer generate_article_covers result, fall back to PIL
    cover_match = re.search(r'^cover_media_id:\s*(.+?)\s*$', content, re.M)
    if cover_match:
        thumb_media_id = cover_match.group(1).strip()
        print(f"   📸 封面: {thumb_media_id[:20]}...")
    # (if generate_article_covers failed, thumb_media_id was set in the else branch above)

    # 2. HTML — 先嵌入正文配图到 markdown
    body_match = re.search(r'^body_image_urls:\s*\n((?:\s+-.*\n?)*)', content, re.M)
    if body_match:
        urls = re.findall(r'-\s+(http[^\s]+)', body_match.group(1))
        if urls:
            fm = re.search(r'(^---\n.*?\n---\n)', content, re.DOTALL).group(1)
            md_body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
            # Insert at ## heading boundaries (not --- separators, to avoid table collision)
            headings = [m.start() for m in re.finditer(r'\n## ', md_body)]
            if len(headings) >= 2 and len(urls) >= 2:
                # Image 1: before second ## heading
                pos = headings[1]
                md_body = md_body[:pos] + f'\n\n![]({urls[0]})\n\n' + md_body[pos:]
                # Image 2: before third ## heading (if exists)
                headings2 = [m.start() for m in re.finditer(r'\n## ', md_body)]
                if len(headings2) >= 3:
                    pos2 = headings2[2]
                    md_body = md_body[:pos2] + f'\n\n![]({urls[1]})\n\n' + md_body[pos2:]
            elif len(headings) >= 1 and len(urls) >= 1:
                pos = headings[0]
                md_body = md_body[:pos] + f'\n\n![]({urls[0]})\n\n' + md_body[pos:]
            content = fm + '\n' + md_body
            print(f"   📸 嵌入 {len(urls)} 张正文配图（## 章节间隔）")
    html_content = markdown_to_html(content)
    print(f"   HTML 长度: {len(html_content)} 字符")

    # 3. Digest
    body_md = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()
    digest = body_md[:120].replace('\n', ' ').replace('---', '').replace('`', '').strip()

    # 4. Draft
    print(f"\n📤 创建草稿...")
    result = create_draft(title, "Python工作圈", html_content, thumb_media_id, digest)

    if "media_id" in result:
        print(f"✅ 草稿创建成功！media_id: {result['media_id']}")
        try:
            记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300], 原标题=title)
        except Exception as e:
            print(f"   ⚠️ 记录失败: {e}")

        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        shutil.copy2(md_file, output_dir / md_file.name)

        print("\n🎉 发布成功！请到后台草稿箱检查")
    else:
        print(f"❌ 失败: {json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
