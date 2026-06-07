#!/usr/bin/env python3
"""
发布 designer 交付的 v3 文章到微信公众号草稿箱
使用 markdown 已有的 cover_media_id 和 body_image_urls
"""
import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

# 导入账号配置
sys.path.insert(0, str(PROJECT_DIR))
from account_config import get_account, get_access_token as get_ac_token
from 发布历史_去重 import 记录发布成功


def http_request(url, data=None, method="GET", headers=None):
    if data and isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"errcode": e.code, "errmsg": body[:200]}
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}


def parse_markdown(content):
    """解析 markdown 文件的 frontmatter 和正文"""
    fm = {}
    body = content

    # 解析 YAML frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.split('\n'):
            m = re.match(r'^(\w+):\s*(.+?)\s*$', line)
            if m:
                key, val = m.group(1), m.group(2)
                fm[key] = val
        body = content[fm_match.end():]

    # 解析 body_image_urls 多行格式
    body_img_match = re.search(r'^body_image_urls:\s*\n((?:\s+-.*\n?)*)', content, re.MULTILINE)
    if body_img_match:
        urls = re.findall(r'-\s+(http\S+)', body_img_match.group(1))
        fm['body_image_urls'] = urls

    return fm, body


def embed_body_images(body, image_urls, md_content):
    """在 ## 标题前插入正文配图"""
    if not image_urls:
        return body

    headings = [m.start() for m in re.finditer(r'\n## ', body)]
    result = body

    if len(headings) >= 2 and len(image_urls) >= 2:
        pos = headings[1]
        result = result[:pos] + f'\n\n![]({image_urls[0]})\n\n' + result[pos:]
        headings2 = [m.start() for m in re.finditer(r'\n## ', result)]
        if len(headings2) >= 3:
            pos2 = headings2[2]
            result = result[:pos2] + f'\n\n![]({image_urls[1]})\n\n' + result[pos2:]
    elif len(headings) >= 1 and len(image_urls) >= 1:
        pos = headings[0]
        result = result[:pos] + f'\n\n![]({image_urls[0]})\n\n' + result[pos:]

    return result


def markdown_simple_html(md_text):
    """纯 re 实现 markdown→HTML（零依赖）"""
    html = md_text
    # 代码块（先保护起来避免被后续替换破坏）
    code_blocks = {}
    def _save_code(m):
        idx = len(code_blocks)
        placeholder = f"!!CODEBLOCK{idx}!!"
        code_blocks[placeholder] = (
            '<pre style="background:#1e1e1e;color:#e8e8e8;padding:20px 16px;'
            'border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;'
            'margin:20px 0;"><code style="background:transparent;padding:0;'
            'color:#e8e8e8;font-size:13px;">'
            + m.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            + '</code></pre>'
        )
        return placeholder
    html = re.sub(r'```(\w*)\n(.*?)```', _save_code, html, flags=re.DOTALL)
    html = re.sub(r'`([^`]+)`', r'<code style="background:#f0fdf4;color:#16a34a;padding:2px 8px;border-radius:4px;font-size:14px;">\1</code>', html)

    # 加粗/斜体
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#c2410c;font-weight:700;">\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # 链接
    html = re.sub(r'\[(.+?)\]\((.+?)\)',
                  r'<a style="color:#16a34a;text-decoration:none;border-bottom:1px solid #bbf7d0;" href="\2">\1</a>',
                  html)

    # 图片（designed 文章有配图，保留 ![]() 格式）
    html = re.sub(r'!\[(.*?)\]\((.+?)\)',
                  r'<img src="\2" alt="\1" style="width:100%;border-radius:8px;margin:16px 0;">',
                  html)

    # 引用
    def _blockquote(m):
        text = m.group(1).replace('\n', '<br>')
        return (f'<blockquote style="border-left:4px solid #3b82f6;padding:12px 20px;'
                f'margin:20px 0;background:#f8fafc;border-radius:0 8px 8px 0;color:#374151;">'
                f'{text}</blockquote>')
    html = re.sub(r'^> (.+?)(?=\n\n|\n$|$)', _blockquote, html, flags=re.DOTALL | re.MULTILINE)

    # 标题
    html = re.sub(r'^### (.+)$',
                  r'<h3 style="font-size:17px;font-weight:bold;color:#2d3748;margin:26px 0 14px 0;line-height:1.5;">\1</h3>',
                  html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$',
                  r'<h2 style="border-left:4px solid #3b82f6;padding:4px 0 4px 18px;color:#111827;font-size:20px;font-weight:750;margin:38px 0 14px 0;line-height:1.5;">\1</h2>',
                  html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$',
                  r'<h1 style="font-size:22px;font-weight:bold;color:#1a1a2e;margin:32px 0 18px 0;line-height:1.5;">\1</h1>',
                  html, flags=re.MULTILINE)

    # 水平线
    html = re.sub(r'^---$', '<div style="margin:28px 0;height:1px;background:#e5e7eb;"></div>', html, flags=re.MULTILINE)

    # 列表（无序）
    html = re.sub(r'^[*-] (.+)$', r'● \1', html, flags=re.MULTILINE)

    # 段落（确保每个独立行被 <p> 包裹）
    lines = html.split('\n')
    result = []
    in_pre = False
    for line in lines:
        stripped = line.strip()
        if '!!CODEBLOCK' in line:
            in_pre = not in_pre
            result.append(line)
        elif in_pre:
            result.append(line)
        elif not stripped:
            result.append('')
        elif stripped.startswith('<h') or stripped.startswith('<blockquote') or stripped.startswith('<pre') or stripped.startswith('<div') or stripped.startswith('<img') or stripped.endswith('</h1>') or stripped.endswith('</h2>') or stripped.endswith('</h3>') or stripped.endswith('</blockquote>') or stripped.endswith('</pre>') or stripped.endswith('</div>') or stripped.startswith('</'):
            result.append(line)
        elif stripped.startswith('● '):
            result.append(f'<p style="margin:0 0 10px 0;text-align:justify;color:#374151;line-height:1.8;">{stripped}</p>')
        else:
            result.append(f'<p style="margin:0 0 18px 0;text-align:justify;color:#374151;line-height:1.8;">{stripped}</p>')

    html = '\n'.join(result)

    # 恢复代码块占位符
    for placeholder, code_html in code_blocks.items():
        html = html.replace(placeholder, code_html)

    # 来源引用段弱化
    sources_match = re.search(
        r'<p[^>]*>\s*(?:数据来源|参考资料)\..*?</p>',
        html, flags=re.DOTALL
    )
    if sources_match:
        block = sources_match.group(0)
        block = re.sub(
            r'<p style="[^"]*"',
            '<p style="margin:36px 0 0 0;padding-top:14px;border-top:1px solid #f3f4f6;color:#9ca3af;font-size:11px;font-weight:300;line-height:1.7;"',
            block, count=1
        )
        block = re.sub(
            r'<a style="[^"]*"',
            '<a style="color:#9ca3af;text-decoration:none;border-bottom:1px dotted #d1d5db;"',
            block
        )
        html = html.replace(sources_match.group(0), block)

    container = (
        '<section style="font-size:16px;color:#374151;line-height:1.8;'
        'letter-spacing:0.3px;padding:0 16px;'
        'font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;'
        'text-align:justify;">'
    )
    return container + html + '</section>'


def main():
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not md_path or not md_path.exists():
        print("❌ 请指定有效的 markdown 文件路径")
        sys.exit(1)

    print("=" * 60)
    print(f"📤 发布 designer v3 文章")
    print(f"   文件: {md_path.name}")
    print("=" * 60)

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_markdown(content)

    title = fm.get("title", md_path.stem)
    print(f"   标题: {title}")

    # 1. 封面
    thumb_media_id = fm.get("cover_media_id", "")
    if not thumb_media_id:
        print("❌ 没有 cover_media_id，无法发布")
        sys.exit(1)
    print(f"   📸 封面 media_id: {thumb_media_id[:20]}...")

    # 2. 正文配图嵌入
    body_image_urls = fm.get("body_image_urls", [])
    print(f"   📸 正文配图: {len(body_image_urls)} 张")

    # 提取正文，嵌入配图
    body_text = body
    if body_image_urls:
        body_text = embed_body_images(body, body_image_urls, content)

    # 3. HTML
    html_content = markdown_simple_html(body_text)
    if len(html_content) > 60000:
        html_content = html_content[:60000]
    print(f"   HTML 长度: {len(html_content)} 字符")

    # 4. Digest
    digest = body[:120].replace('\n', ' ').replace('---', '').replace('`', '').strip()

    # 5. 获取 token
    cfg = get_account(None)
    token = get_ac_token(None)
    if not token:
        print("❌ 获取 access_token 失败")
        sys.exit(1)

    # 6. 创建草稿
    body = {
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
    print(f"\n📤 创建草稿...")
    result = http_request(url, body, "POST")

    if "media_id" in result:
        print(f"✅ 草稿创建成功！media_id: {result['media_id']}")
        try:
            记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300])
        except Exception as e:
            print(f"   ⚠️ 记录失败: {e}")
        print("\n🎉 发布成功！请到后台草稿箱设置定时 20:00")
        return True
    else:
        print(f"❌ 失败: {json.dumps(result, ensure_ascii=False)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
