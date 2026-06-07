#!/usr/bin/env python3
"""批量发布多篇微信公众号草稿"""
import sys, re, json, subprocess, time
from pathlib import Path

base = Path(__file__).parent
templates_dir = base / "创作"

# 今晚的三篇
files = [
    "文章_AI热点_01_GitHubCopilotToken计费_20260601.md",
    "文章_AI热点_02_Anthropic买断Stainless_20260601.md",
    "文章_AI热点_03_快手SRPO效率革命_20260601.md",
]

# 逐个处理
for fname in files:
    fpath = templates_dir / fname
    if not fpath.exists():
        print(f"❌ 未找到: {fname}")
        continue
    
    print(f"\n{'='*50}")
    print(f"📄 发布: {fname}")
    print(f"{'='*50}")
    
    # 直接调用 step5_发布.py，用 --file 参数传文件路径
    # 但 step5_发布.py 没有 --file 参数，只能用 --column
    # 所以我们的策略：直接调用 generate_article_covers 生成封面，
    # 然后从 frontmatter 读取封面media_id，调用 publish_v3 创建草稿
    
    # 先运行 generate_article_covers --pro
    result = subprocess.run(
        ["python3", str(base / "generate_article_covers.py"), str(fpath), "--pro"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"   ⚠️ generate_article_covers 失败: {result.stderr[:200]}")
        print(f"   stdout: {result.stdout[:200]}")
        # 如果失败，尝试用 step5 自带的图像生成
        result2 = subprocess.run(
            ["python3", str(base / "step5_发布.py"), "--column", "AI热点"],
            capture_output=True, text=True, timeout=120
        )
        print(result2.stdout)
        if result2.returncode != 0:
            print(f"   ❌ 发布失败: {result2.stderr[:200]}")
        time.sleep(2)
        continue
    
    # 重新读取文件（封面信息已写入 frontmatter）
    content = fpath.read_text(encoding="utf-8")
    
    # 提取封面
    cover_match = re.search(r'^cover_media_id:\s*(.+?)\s*$', content, re.M)
    if not cover_match:
        print("   ❌ 没有封面 media_id")
        time.sleep(2)
        continue
    thumb_media_id = cover_match.group(1).strip()
    
    # 提取标题
    title_match = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
    title = title_match.group(1).strip() if title_match else fpath.stem
    title = title.replace("'", "\u2018").replace("'", "\u2019")
    
    print(f"   标题: {title[:40]}...")
    print(f"   封面: {thumb_media_id[:20]}...")
    
    # 调用 publish_v3 的 markdown_to_html 和 http_request
    sys.path.insert(0, str(base))
    from publish_v3 import markdown_to_html, http_request
    
    # 提取正文（去掉 frontmatter）
    fm_match = re.search(r'^---\n.*?\n---\n', content, flags=re.DOTALL)
    if fm_match:
        body_md = content[fm_match.end():]
    else:
        body_md = content
    
    # 嵌入正文配图
    body_urls = re.findall(r'^\s+-\s+(http[^\s]+)', content, re.M)
    if body_urls and len(body_urls) >= 2:
        # 插入图片到 ## 标题前
        headings = [m.start() for m in re.finditer(r'\n## ', body_md)]
        if len(headings) >= 2:
            pos = headings[1]
            body_md = body_md[:pos] + f'\n\n![]({body_urls[0]})\n\n' + body_md[pos:]
            if len(headings) >= 3:
                pos2 = [m.start() for m in re.finditer(r'\n## ', body_md)]
                if len(pos2) >= 3:
                    body_md = body_md[:pos2[2]] + f'\n\n![]({body_urls[1]})\n\n' + body_md[pos2[2]:]
        elif len(headings) >= 1 and len(body_urls) >= 1:
            pos = headings[0]
            body_md = body_md[:pos] + f'\n\n![]({body_urls[0]})\n\n' + body_md[pos:]
    
    # markdown → HTML
    html_content = markdown_to_html(body_md)
    print(f"   HTML 长度: {len(html_content)} 字符")
    
    # digest
    digest = body_md[:120].replace('\n', ' ').replace('---', '').replace('`', '').strip()
    
    # 获取 token
    from step5_发布 import get_access_token as step5_token
    token = step5_token()
    if not token:
        print("   ❌ 获取 token 失败")
        time.sleep(2)
        continue
    
    # 创建草稿
    draft_body = {
        "articles": [{
            "title": title,
            "author": "Python工作圈",
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
    result = http_request(url, draft_body, "POST")
    
    if "media_id" in result:
        print(f"   ✅ 草稿创建成功！media_id: {result['media_id']}")
        try:
            from 发布历史_去重 import 记录发布成功
            记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300], 原标题=title)
            print("   ✅ 已记录发布历史")
        except Exception as e:
            print(f"   ⚠️ 记录失败: {e}")
    else:
        print(f"   ❌ 创建草稿失败: {json.dumps(result, ensure_ascii=False)}")
    
    time.sleep(2)

print("\n✅ 三篇全部处理完毕")
