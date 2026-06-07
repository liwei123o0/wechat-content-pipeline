#!/usr/bin/env python3
"""Publish 3 articles to WeChat draft box."""
from pathlib import Path
import sys, json, re, urllib.request, urllib.parse, shutil

sys.path.insert(0, str(Path(__file__).parent))
from publish_v3 import markdown_to_html

WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"

def get_access_token():
    params = urllib.parse.urlencode({
        "grant_type": "client_credential",
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET
    })
    url = f"https://api.weixin.qq.com/cgi-bin/token?{params}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))["access_token"]

创作_dir = Path(__file__).parent / "data" / "创作"
output_dir = Path(__file__).parent / "output"
today = "20260520"

articles = sorted(创作_dir.glob(f"文章_*{today}.md"))
print(f"📤 发现 {len(articles)} 篇待发布文章")

if not articles:
    print("无待发布文章")
    exit(0)

token = get_access_token()
print(f"🔑 Access token 获取成功")

for md_path in articles:
    content = md_path.read_text(encoding="utf-8")
    
    # 从 frontmatter 读取字段
    fm = {}
    m = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
    if m: fm["title"] = m.group(1).strip()
    m = re.search(r'^author:\s*(.+?)\s*$', content, re.M)
    if m: fm["author"] = m.group(1).strip()
    m = re.search(r'^cover_media_id:\s*(\S+)', content, re.M)
    if m: fm["media_id"] = m.group(1).strip()
    fm["body_urls"] = re.findall(r'^\s+-\s+(http[^\s]+)', content, re.M)
    
    title = fm.get("title", md_path.stem)
    author = fm.get("author", "Python工作圈")
    media_id = fm.get("media_id")
    
    if not media_id:
        print(f"⚠️ {md_path.name} 无 cover_media_id，跳过")
        continue
    
    print(f"\n📄 {title[:50]}...")
    
    # HTML 转换
    html = markdown_to_html(content)
    
    # 插入正文配图（HTML 渲染图表）
    for i, url in enumerate(fm.get("body_urls", [])):
        img_tag = f'<p style="text-align:center;margin:30px 0;"><img src="{url}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/><br/><span style="color:#888;font-size:13px;">▲ 图{i+1}</span></p>'
        # 在第二个段落之后插入
        parts = html.split("</p>")
        insert_pos = min(len(parts) - 1, 3 + i * 4)
        parts.insert(insert_pos, img_tag)
        html = "</p>".join(parts)
    
    # 发布 ⚠️ 用 urllib.request，不用 requests
    draft_data = {
        "articles": [{
            "title": title,
            "content": html,
            "thumb_media_id": media_id,
            "author": author
        }]
    }
    data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
        
        if "media_id" in result:
            print(f"  ✅ 发布成功！media_id: {result['media_id'][:30]}...")
            # 移动到 output 目录
            output_dir.mkdir(exist_ok=True)
            shutil.copy2(str(md_path), str(output_dir / md_path.name))
            md_path.unlink()
            # 记录发布历史
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from 发布历史_去重 import 记录发布成功
                记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300])
            except ImportError:
                print("  ⚠️ 未找到 发布历史_去重 模块，跳过历史记录")
        else:
            print(f"  ❌ 发布失败: {result}")
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")

print("\n✅ 发布流程完成")
