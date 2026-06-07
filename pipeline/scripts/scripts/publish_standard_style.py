#!/usr/bin/env python3
"""
Publish hot-topic articles using standard article-flow style (publish_v3.markdown_to_html).
Strips knowledge-card formatting markers for news articles.
"""
import sys, re, json, urllib.request, time, io
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from publish_v3 import markdown_to_html, generate_cover_bytes, upload_permanent_image
from account_config import get_account, get_access_token as get_ac_token

def strip_card_formatting(md_text):
    """Remove knowledge-card markers, keep content as plain markdown"""
    # Remove frontmatter for processing, keep original
    orig = md_text
    
    body = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
    
    lines = body.split('\n')
    result = []
    skip_intro = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip title card markers
        if stripped == '> 标题卡片':
            skip_intro = True
            continue
        
        # Skip the title and subtitle lines (next 2 non-empty after > 标题卡片)
        # Actually, let's just strip > prefix for intro
        if stripped.startswith('> ') and len(stripped) > 2:
            result.append(stripped[2:])
            skip_intro = False
            continue
        
        # Skip section labels like 零一｜核心逻辑 (they're not standard markdown)
        if re.match(r'零[一二三四五六七八九十]+\s*[｜|]', stripped):
            continue
        
        # Skip empty separator lines that were structural
        if stripped == '' and skip_intro:
            continue
        
        # Keep everything else
        result.append(line)
        skip_intro = False
    
    # Reconstruct
    clean = '\n'.join(result)
    # Collapse excessive blank lines
    clean = re.sub(r'\n{4,}', '\n\n\n', clean)
    
    # Get original frontmatter and prepend
    fm = re.search(r'^---\n.*?\n---', orig, re.DOTALL)
    if fm:
        clean = fm.group(0) + '\n' + clean
    
    return clean


def publish_article(article_path, account='old'):
    print("="*60)
    print("📤 标准文章流风格发布")
    print("="*60)
    
    with open(article_path, encoding='utf-8') as f:
        content = f.read()
    
    # Extract title + author from frontmatter
    fm = {}
    m = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            kv = re.match(r'^(\w+):\s*(.+?)\s*$', line)
            if kv: fm[kv.group(1)] = kv.group(2)
    
    title = fm.get('title', Path(article_path).stem).strip("'\" ")
    author = fm.get('author', 'Python工作圈')
    print(f"📄 文章: {title}")
    print(f"👤 作者: {author}")
    
    # Strip card formatting
    print("\n🔄 转换到标准文章流风格...")
    clean_md = strip_card_formatting(content)
    
    # Convert via publish_v3's markdown_to_html (standard style)
    html = markdown_to_html(clean_md)
    print(f"   HTML长度: {len(html)} 字符")
    
    # Auth
    cfg = get_account(account)
    print(f"\n🔑 获取token [{cfg['name']}]...")
    token = get_ac_token(account)
    if not token:
        print("❌ 获取token失败")
        return False
    
    # Cover
    print(f"\n🖼️ 生成并上传封面...")
    cover_media_id = upload_permanent_image(token, title)
    
    # Draft
    draft = {
        "articles": [{
            "title": title,
            "content": html,
            "thumb_media_id": cover_media_id or "",
            "author": author,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]
    }
    
    print(f"\n📝 创建微信草稿箱...")
    data = json.dumps(draft, ensure_ascii=False).encode('utf-8')
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        if "media_id" in result:
            print(f"\n✅ 草稿创建成功！media_id={result['media_id']}")
            return True
        else:
            print(f"\n❌ 失败: {result}")
            return False
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}")
        return False
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', help='文章md路径')
    parser.add_argument('--account', '-a', default='old')
    args = parser.parse_args()
    
    for f in args.files:
        print()
        publish_article(f, account=args.account)
