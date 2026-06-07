#!/usr/bin/env python3
"""快速重新发布指定日期的文章（修复 author + 编码）"""
import sys, json, re, urllib.request, urllib.parse, shutil
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
from publish_v3 import markdown_to_html

WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"

def get_token():
    params = urllib.parse.urlencode({"grant_type":"client_credential","appid":WECHAT_APP_ID,"secret":WECHAT_APP_SECRET})
    with urllib.request.urlopen(f"https://api.weixin.qq.com/cgi-bin/token?{params}", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))["access_token"]

days = sys.argv[1:] or ["20260515"]
token = get_token()

for day in days:
    创作_dir = BASE / "创作"
    output_dir = BASE / "output"
    articles = sorted(创作_dir.glob(f"文章_*{day}.md"))
    if not articles:
        print(f"📅 {day}: 无文章")
        continue
    print(f"\n📅 {day}: {len(articles)} 篇")
    for md_path in articles:
        content = md_path.read_text()
        tm = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
        am = re.search(r'^author:\s*(.+?)\s*$', content, re.M)
        mm = re.search(r'cover_media_id:\s*(\S+)', content)
        title = tm.group(1) if tm else md_path.stem
        author = am.group(1) if am else "Python工作圈"
        media_id = mm.group(1) if mm else None
        body_urls = re.findall(r'^\s+-\s+(http://mmbiz\.qpic\.cn/\S+)', content, re.M)
        if not media_id:
            print(f"  ⚠️ {md_path.name}: 无封面")
            continue
        html = markdown_to_html(content)
        for i, url in enumerate(body_urls):
            img_tag = f'<p style="text-align:center;margin:30px 0;"><img src="{url}" style="max-width:100%;border-radius:8px;"/><br/><span style="color:#888;font-size:13px;">▲ 图{i+1}</span></p>'
            parts = html.split("</p>")
            parts.insert(min(len(parts)-1, 3+i*4), img_tag)
            html = "</p>".join(parts)
        draft_data = {"articles":[{"title":title,"content":html,"thumb_media_id":media_id,"author":author}]}
        data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
        if "media_id" in result:
            print(f"  ✅ {title[:35]}... author={author}")
            shutil.copy2(md_path, output_dir / md_path.name)
            md_path.unlink()
        else:
            print(f"  ❌ {title[:35]}: {result}")
