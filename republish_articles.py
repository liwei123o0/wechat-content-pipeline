#!/usr/bin/env python3
"""
重新发布脚本 — 修复 author + 调用 generate_article_covers 生成封面 + 正确编码发布

用法：python republish_articles.py
"""
import sys
import re
import json
import io
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"

def get_access_token():
    import urllib.request
    import urllib.parse
    params = urllib.parse.urlencode({
        "grant_type": "client_credential",
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET,
    })
    url = f"https://api.weixin.qq.com/cgi-bin/token?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        r = json.loads(resp.read().decode("utf-8"))
    if "access_token" in r:
        return r["access_token"]
    raise RuntimeError(f"Token获取失败: {r}")


def upload_cover_to_wechat(access_token, img_path):
    """用 urllib（兼容中文编码）上传封面 → media_id"""
    import urllib.request
    from PIL import Image
    img = Image.open(img_path).convert("RGB")
    img = img.resize((1280, 544), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_data = buf.getvalue()

    boundary = "----WebKitFormBoundary" + str(hash(datetime.now()))
    body = b""
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode()
    body += img_data
    body += f"\r\n--{boundary}--\r\n".encode()

    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        return result["media_id"]
    raise RuntimeError(f"封面上传失败: {result}")


def upload_body_to_wechat(access_token, img_path):
    """用 urllib 上传正文图 → mmbiz.qpic.cn URL"""
    import urllib.request
    from PIL import Image
    img = Image.open(img_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_data = buf.getvalue()

    boundary = "----WebKitFormBoundary" + str(hash(datetime.now()))
    body = b""
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"img.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode()
    body += img_data
    body += f"\r\n--{boundary}--\r\n".encode()

    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "url" in result:
        return result["url"]
    raise RuntimeError(f"正文图上传失败: {result}")


def markdown_to_html(md_text):
    """安全转换 markdown → HTML，去除 frontmatter，正确编码"""
    import markdown
    # 去掉 frontmatter — 精确匹配从开头的 --- 到下一个 -\n
    md_clean = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
    # 修复列表前缺空行（LLM生成常见问题）
    md_clean = re.sub(r'([^\n])\n(?=[\-\*\+]\s|\d+\.\s)', r'\1\n\n', md_clean)
    html = markdown.markdown(md_clean, extensions=['extra'])
    # 微信兼容的样式
    html = html.replace('<table>', '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:14px;">')
    html = html.replace('<th>', '<th style="background:#2d3748;color:#fff;padding:10px;text-align:center;">')
    html = html.replace('<td>', '<td style="padding:8px;border:1px solid #e2e8f0;text-align:center;">')
    html = html.replace('<pre><code>', '<pre style="background-color:#1e1e1e;color:#e8e8e8;padding:36px 24px 20px;border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.7;margin:24px 0;box-shadow:0 4px 20px rgba(0,0,0,0.25);border:1px solid #3d3d3d;background-image:radial-gradient(circle 5px at 24px 18px,#ff5f56 99%,transparent),radial-gradient(circle 5px at 40px 18px,#ffbd2e 99%,transparent),radial-gradient(circle 5px at 56px 18px,#27c93f 99%,transparent);background-repeat:no-repeat;"><code style="font-family:\'SF Mono\',\'Menlo\',\'Monaco\',\'Consolas\',\'Courier New\',monospace;background:transparent;padding:0;color:#e8e8e8;border:none;font-size:13px;">')
    html = html.replace('<blockquote>', '<blockquote style="border:1px solid #bfdbfe;border-left:6px solid #3b82f6;padding:20px 24px;margin:24px 0;background:linear-gradient(135deg,#f8fafc,#eff6ff);color:#374151;font-size:15px;border-radius:0 12px 12px 0;box-shadow:0 2px 8px rgba(0,0,0,0.04);">')
    # H2 标题（蓝左竖线 + 留白清爽版）
    html = html.replace('<h2>', '<h2 style="border-left:4px solid #3b82f6;padding:4px 0 4px 18px;color:#111827;font-size:20px;font-weight:750;margin:38px 0 14px 0;line-height:1.5;letter-spacing:0.5px;">')
    html = html.replace('<ol>', '<ol style="padding-left:24px;margin:14px 0;line-height:1.8;list-style-type:decimal;color:#595959;">')
    # 移除内嵌插图
    html = re.sub(r'<img[^>]*>', '', html)
    # 移除 <li> 内的 <p> 包装（extra 扩展导致多余间距）
    html = re.sub(r'<li([^>]*)>\s*<p[^>]*>\s*', r'<li>', html, flags=re.DOTALL)
    html = re.sub(r'\s*</p>\s*</li>', r'</li>', html, flags=re.DOTALL)
    return html


def publish_article(token, title, html_content, thumb_media_id, author):
    """用 urllib.request + 显式 utf-8 调用 draft/add（修复 requests 库的编码 bug）"""
    import urllib.request
    draft_data = {
        "articles": [{
            "title": title,
            "content": html_content,
            "thumb_media_id": thumb_media_id,
            "author": author,
        }]
    }
    data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result


def parse_frontmatter(content):
    """从 frontmatter 提取字段"""
    result = {}
    m = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
    if m:
        result["title"] = m.group(1)
    m = re.search(r'^author:\s*(.+?)\s*$', content, re.M)
    if m:
        result["author"] = m.group(1)
    m = re.search(r'cover_media_id:\s*(\S+)', content)
    if m:
        result["cover_media_id"] = m.group(1)
    result["body_urls"] = re.findall(r'^\s+-\s+(http://mmbiz\.qpic\.cn/\S+)', content, re.M)
    return result


def main():
    print("=" * 60)
    print("🔄 微信文章重新发布脚本")
    print("=" * 60)

    # 1. 找到今天的所有文章（创作/ + output/ 都算）
    创作_dir = BASE_DIR / "创作"
    output_dir = BASE_DIR / "output"
    today = "20260514"

    articles = []
    # 从创作目录
    articles.extend(sorted(创作_dir.glob(f"文章_*{today}.md")))
    # 从 output 目录（如果创作中没有）
    seen = set(a.name for a in articles)
    for a in sorted(output_dir.glob(f"文章_*{today}.md")):
        if a.name not in seen:
            articles.append(a)

    if not articles:
        print("❌ 没有找到待重新发布的文章")
        return 1

    print(f"\n📄 找到 {len(articles)} 篇文章:")
    for a in articles:
        print(f"   - {a.name}")

    # 2. 为没有封面的文章生成封面
    print(f"\n🎨 检查封面状态...")
    token = get_access_token()
    print(f"   ✅ Token 获取成功")

    to_fix = []
    for a in articles:
        content = a.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if not fm.get("cover_media_id"):
            to_fix.append(a)

    if to_fix:
        print(f"   ⚠️ {len(to_fix)} 篇缺少 cover_media_id，需先生成封面+上传")
        # 导入 huashu_images 生成 HTML 封面
        from huashu_images import generate_images_for_article

        for a in to_fix:
            print(f"\n   🎨 {a.name}...")
            try:
                imgs = generate_images_for_article(str(a))
                cover_path = imgs.get("cover")
                body_paths = imgs.get("body", [])
                if not cover_path:
                    print(f"       ❌ 封面生成为空")
                    continue
                print(f"       ✅ 封面: {Path(cover_path).name}")
                print(f"       ✅ 正文图: {len(body_paths)} 张")

                # 上传封面上传
                media_id = upload_cover_to_wechat(token, cover_path)
                print(f"       📤 media_id: {media_id[:30]}...")
                body_urls = []
                for bp in body_paths:
                    url = upload_body_to_wechat(token, bp)
                    body_urls.append(url)

                # 回写 frontmatter
                content = a.read_text(encoding="utf-8")
                # 替换或添加 cover_media_id
                if "cover_media_id:" in content:
                    content = re.sub(r'cover_media_id:\s*\S+', f'cover_media_id: {media_id}', content)
                else:
                    # 在 --- 前插入
                    content = content.replace("---", f"cover_media_id: {media_id}\n---", 1)
                # 添加 body_image_urls
                if body_urls:
                    yaml_urls = "\n".join(f"  - {u}" for u in body_urls)
                    content = content.replace("---", f"body_image_urls:\n{yaml_urls}\n---", 1)
                # 添加 cover_source
                content = content.replace("---", "cover_source: huashu_html\n---", 1)
                a.write_text(content, encoding="utf-8")
                print(f"       💾 frontmatter 已更新")
            except Exception as e:
                print(f"       ❌ 失败: {e}")
    else:
        print(f"   ✅ 所有文章已有 cover_media_id")

    # 3. 重新发布所有文章（author 从 frontmatter 读取）
    print(f"\n📤 发布到微信草稿箱...")
    published = 0
    failed = 0
    for a in articles:
        content = a.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        title = fm.get("title", a.stem.replace("文章_", ""))
        author = fm.get("author", "Python工作圈")
        media_id = fm.get("cover_media_id")
        body_urls = fm.get("body_urls", [])

        if not media_id:
            print(f"   ⚠️ {a.name}: 无 cover_media_id，跳过")
            failed += 1
            continue

        print(f"\n   📰 {title[:40]}...")
        print(f"      author: {author}")

        # HTML 转换
        html = markdown_to_html(content)

        # 插入正文配图（如果有）
        if body_urls:
            for i, url in enumerate(body_urls):
                img_tag = (f'<p style="text-align:center;margin:30px 0;">'
                           f'<img src="{url}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>'
                           f'<br/><span style="color:#888;font-size:13px;">▲ 图{i+1}</span></p>')
                parts = html.split("</p>")
                pos = min(len(parts) - 1, 3 + i * 4)
                parts.insert(pos, img_tag)
                html = "</p>".join(parts)

        # 发布
        try:
            result = publish_article(token, title, html, media_id, author)
            if "media_id" in result:
                print(f"      ✅ media_id: {result['media_id'][:20]}...")
                # 移至 output（覆盖旧的）
                shutil.copy2(a, output_dir / a.name)
                if a.parent == 创作_dir:
                    a.unlink()
                published += 1
                # 记录发布历史
                try:
                    from 发布历史_去重 import 记录发布成功
                    记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300])
                except:
                    pass
            else:
                print(f"      ❌ 发布失败: {result}")
                failed += 1
        except Exception as e:
            print(f"      ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"📊 {published} 篇成功, {failed} 篇失败")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
