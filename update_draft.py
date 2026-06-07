import json, urllib.request, urllib.parse, re, markdown

APPID = "wxb445d745c6038a3c"
SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"
ARTICLE_PATH = str(Path(__file__).parent / "创作" / "文章_雷军2026科技动态.md")
COVER_PATH = str(Path(__file__).parent / "素材" / "cover_105828.png")
BODY_IMG_PATH = str(Path(__file__).parent / "素材" / "comp_105832.png")
MEDIA_ID = "O3o4IHlucqYmVliSX1xilbZBShpaEwpYdkYfj36G"
AUTHOR = "Python工作圈"

# 1. Token
print("📡 获取 token...")
params = urllib.parse.urlencode({"grant_type":"client_credential","appid":APPID,"secret":SECRET})
with urllib.request.urlopen(f"https://api.weixin.qq.com/cgi-bin/token?{params}", timeout=15) as resp:
    r = json.loads(resp.read())
token = r["access_token"]

# 2. Parse article
print("📝 解析文章...")
with open(ARTICLE_PATH, encoding="utf-8") as f:
    md_content = f.read()
m = re.search(r"^---\n(.*?)\n---\n(.*)", md_content, re.DOTALL)
md_body = m.group(2) if m else md_content
title = "雷军2026年科技大棋局：芯片出货百万、AI投入600亿、智驾双元年"

# 3. Upload cover (same file as before)
print("🖼️ 上传封面...")
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()
boundary = "----FormBoundaryUpdate"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.jpg"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + cover_data + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
thumb_media_id = result["media_id"]
print(f"✅ 新封面上传, media_id: {thumb_media_id[:30]}...")

# 4. Upload body image
print("🖼️ 上传正文图...")
with open(BODY_IMG_PATH, "rb") as f:
    body_img_data = f.read()
body2 = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="body.jpg"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + body_img_data + f"\r\n--{boundary}--\r\n".encode()
req2 = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}",
    data=body2,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
with urllib.request.urlopen(req2, timeout=30) as resp:
    body_img_url = json.loads(resp.read())["url"]
print(f"✅ 正文图上传成功")

# 5. Markdown → HTML
print("📄 Markdown → HTML...")
html = markdown.markdown(md_body, extensions=["extra"])
img_tag = f'<p style="text-align:center;margin:30px 0;"><img src="{body_img_url}" style="max-width:100%;border-radius:8px;"/></p>'
parts = html.split("<h2>")
if len(parts) > 1:
    html = parts[0] + img_tag + "<h2>" + "<h2>".join(parts[1:])
else:
    html = img_tag + html

# 6. Update draft
print("📰 更新草稿...")
draft = {
    "media_id": MEDIA_ID,
    "index": 0,
    "articles": {
        "title": title,
        "author": AUTHOR,
        "content": html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
}
data = json.dumps(draft, ensure_ascii=False).encode("utf-8")
req3 = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}",
    data=data,
    headers={"Content-Type": "application/json; charset=utf-8"},
)
with urllib.request.urlopen(req3, timeout=30) as resp:
    result3 = json.loads(resp.read())

if "errcode" not in result3 or result3["errcode"] == 0:
    print(f"✅ 草稿更新成功!")
    # 验证
    with urllib.request.urlopen(f"https://api.weixin.qq.com/cgi-bin/draft/count?access_token={token}", timeout=10) as c:
        print(f"  草稿箱: {json.loads(c.read()).get('total_count')} 篇")
else:
    print(f"❌ 更新失败: {result3}")
