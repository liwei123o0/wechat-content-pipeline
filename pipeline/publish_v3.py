#!/usr/bin/env python3
"""
发布到微信公众号 - 使用永久素材上传封面
支持多账号: --account old|guangyinpiano
"""
import io
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# 导入账号配置管理
sys.path.insert(0, str(Path(__file__).parent))
from account_config import get_account, get_access_token as get_ac_token, add_account_arg, list_accounts

# 当前账号（通过命令行参数设置）
_CURRENT_ACCOUNT = None

sys.path.insert(0, str(Path(__file__).parent))
from 发布历史_去重 import 记录发布成功

BASE_DIR = Path(__file__).parent


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


def get_access_token():
    """获取微信access_token（使用当前账号配置）"""
    global _CURRENT_ACCOUNT
    return get_ac_token(_CURRENT_ACCOUNT)


def generate_cover_bytes(title):
    """生成小尺寸JPEG封面图"""
    from PIL import Image, ImageDraw
    w, h = 300, 200
    colors = [
        (30, 60, 114), (44, 62, 80), (22, 160, 133),
        (52, 73, 94), (41, 128, 185), (142, 68, 173),
        (231, 76, 60), (39, 174, 96), (243, 156, 18),
    ]
    idx = hash(title) % len(colors)
    bg = colors[idx]
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    text = title[:20]
    for i in range(0, len(text), 10):
        line = text[i:i+10]
        draw.text((w//2 - len(line)*4, h//2 - 15 + i//10*22), line, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    return buf.getvalue()


def upload_permanent_image(token, title):
    """上传永久素材到微信"""
    img_data = generate_cover_bytes(title)
    print(f"  🖼️ 封面图: {len(img_data)} bytes")

    boundary = "----WebKitFormBoundary" + str(hash(time.time()))
    # multipart form-data
    body_parts = []
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
    body_parts.append(img_data)
    body_parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(body_parts)

    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if "media_id" in result:
            print(f"  ✅ 永久素材上传成功: media_id={result['media_id']}")
            return result["media_id"]
        else:
            print(f"  ⚠️ 上传失败: {result}")
            return None
    except Exception as e:
        print(f"  ❌ 上传异常: {e}")
        return None


def _convert_lists_to_text(md_text):
    """将 markdown 列表语法转为带符号的普通文本，绕过 WeChat 对 <ul>/<ol>/<li> 的渲染问题"""
    import re
    lines = md_text.split('\n')
    result = []
    # 带圈数字 ①-⑳
    circled = ['\u2460','\u2461','\u2462','\u2463','\u2464',
               '\u2465','\u2466','\u2467','\u2468','\u2469',
               '\u246a','\u246b','\u246c','\u246d','\u246e',
               '\u246f','\u2470','\u2471','\u2472','\u2473']
    
    for line in lines:
        # 无序列表: - Item, * Item, + Item
        um = re.match(r'^\s*[-*+]\s+(.*)', line)
        if um:
            c = um.group(1).strip()
            if c:
                result.append('\u25cf ' + c)
                continue
        
        # 有序列表: N. Item
        om = re.match(r'^\s*(\d+)\.\s+(.*)', line)
        if om:
            num = int(om.group(1))
            text = om.group(2).strip()
            if text:
                marker = circled[num-1] if 1 <= num <= 20 else str(num) + '.'
                result.append(marker + ' ' + text)
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def _split_list_paragraphs(html):
    """将同一段落内的多个 ●/①② 项拆成独立 <p> 标签"""
    import re
    
    def split_bullets(m):
        style = m.group(1)
        content = m.group(2)
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if len(lines) <= 1:
            return m.group(0)
        return ''.join(f'<p{style}>{l}</p>' for l in lines)
    
    # 拆分 ● 段落（U+25CF）
    bullet = chr(0x25cf)
    html = re.sub(
        rf'<p([^>]*)>((?={bullet})(?:{bullet}[^\n]*)(?:\n{bullet}[^\n]*)+)</p>',
        split_bullets,
        html,
        flags=re.DOTALL
    )
    # 拆分 ①②③... 段落（U+2460-U+2473 带圈数字）
    import unicodedata
    circled_set = ''.join(chr(0x2460 + i) for i in range(20))
    pattern_circled = (
        rf'<p([^>]*)>((?=[{circled_set}])(?:[{circled_set}][^\n]*)'
        rf'(?:\n[{circled_set}][^\n]*)+)</p>'
    )
    html = re.sub(
        pattern_circled,
        split_bullets,
        html,
        flags=re.DOTALL
    )
    return html



def markdown_to_html(md_text):
    """留白呼吸排版：充足留白 + 重点卡片化"""
    try:
        import markdown
        import re
        
        # Remove frontmatter
        md_clean = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
        # Strip metadata sections that leak into body (cover_media_id, body_image_urls, etc.)
        # Line-by-line removal: skip lines that look like YAML metadata
        lines = md_clean.split('\n')
        clean_lines = []
        in_meta_block = False
        for line in lines:
            # Detect metadata keys like cover_media_id:, cover_source:, etc.
            if re.match(r'^(cover_media_id|cover_source|body_image_urls|thumb_media_id):', line):
                in_meta_block = True
                continue
            # Multi-line metadata (● bullets after body_image_urls:)
            if in_meta_block and (line.strip() == '' or not re.match(r'^\s*[●\-*\d]', line)):
                in_meta_block = False
                # Don't append this line if it's blank (let next iteration handle it)
                if line.strip() == '':
                    continue
            if in_meta_block:
                continue
            # Also remove standalone metadata key: value lines
            if re.match(r'^[a-z_]+:\s*\S{10,}', line):
                continue
            clean_lines.append(line)
        md_clean = '\n'.join(clean_lines)
        # Collapse multiple blank lines
        md_clean = re.sub(r'\n{3,}', '\n\n', md_clean)
        
        # Fix: ensure blank line before markdown tables (| header |)
        # LLM often outputs tables immediately after paragraphs without a blank line,
        # which causes markdown parser to treat them as inline text
        md_clean = re.sub(r'([^\n|])\n(\|[^\n]+\n\|[-| ]+\n)', r'\1\n\n\2', md_clean)
        
        # Convert markdown list syntax to plain text with symbols
        # WeChat renders <p> reliably but mis-handles <ul>/<ol>/<li>
        md_clean = _convert_lists_to_text(md_clean)
        
        # Convert markdown to HTML with extensions
        html = markdown.markdown(md_clean, extensions=['extra'])
        
        # Fix: clean up \n inside table cells (LLM artifact)
        html = re.sub(r'(<t[dh][^>]*>)(.*?)(</t[dh]>)', 
                      lambda m: m.group(1) + m.group(2).replace('\n', ' ') + m.group(3), 
                      html, flags=re.DOTALL)
        
        # ── 基础容器（留白拉满） ──
        container_start = (
            '<section style="'
            'font-size:16px;'
            'color:#595959;'
            'line-height:1.8;'           # ← 行距1.8，更紧凑耐读
            'letter-spacing:0.5px;'
            'padding:0 16px;'             # ← 两侧留白加大
            'font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;'
            'text-align:justify;'
            '">'
        )
        
        # ── H1 标题 ──
        html = re.sub(
            r'<h1>',
            '<h1 style="font-size:21px;font-weight:bold;color:#1a1a2e;'
            'margin:36px 0 18px 0;line-height:1.5;'
            'border-left:4px solid #22c55e;padding:4px 0 4px 16px;'
            '">',
            html
        )
        
        # ── H2 标题（蓝左竖线 + 留白清爽版） ──
        html = re.sub(
            r'<h2>',
            '<h2 style="border-left:4px solid #3b82f6;'
            'padding:4px 0 4px 18px;'
            'color:#111827;font-size:20px;font-weight:750;'
            'margin:38px 0 14px 0;line-height:1.5;letter-spacing:0.5px;'
            '">',
            html
        )
        
        # ── H3 标题 ──
        html = re.sub(
            r'<h3>',
            '<h3 style="font-size:17px;font-weight:bold;color:#2d3748;'
            'margin:26px 0 14px 0;line-height:1.5;'
            '">',
            html
        )
        
        # ── 段落（段间距加大） ──
        html = re.sub(
            r'<p>',
            '<p style="margin:0 0 18px 0;text-align:justify;'  # ← 段间距18px
            'color:#595959;'
            '">',
            html
        )
        
        # ── 加粗文字（V2 橘红底突出） ──
        html = re.sub(
            r'<strong>',
            '<strong style="color:#c2410c;font-weight:700;'
            'background:linear-gradient(to top,rgba(194,65,12,0.15) 40%,transparent 40%);'
            'padding:0 2px;'
            '">',
            html
        )
        
        # ── 表格 ──
        html = re.sub(
            r'<table[^>]*>',
            '<table style="border-collapse:collapse;width:100%;'
            'font-size:13px;'
            'margin:24px 0;box-shadow:0 1px 4px rgba(0,0,0,0.08);'
            '" cellpadding="0" cellspacing="0">',
            html
        )
        # NOTE: \b required — without it, <thead> matches <th[^>]*> and
        # gets turned into an orphan <th>, adding a phantom column.
        html = re.sub(
            r'<th\b[^>]*>',
            '<th style="background:#2d3748;color:#ffffff;padding:8px 6px;'
            'text-align:center;font-weight:600;border:1px solid #1a202c;'
            'font-size:12px;word-break:break-word;white-space:normal;'
            'overflow-wrap:break-word;'
            '">',
            html
        )
        html = re.sub(
            r'<td\b[^>]*>',
            '<td style="padding:8px 6px;border:1px solid #e2e8f0;'
            'text-align:left;color:#4a5568;font-size:12px;'
            'word-break:break-word;white-space:normal;'
            'overflow-wrap:break-word;'
            '">',
            html
        )
        
        # ── 引用块 → 卡片化（V2 蓝边 + 浅蓝渐变底） ──
        html = re.sub(
            r'<blockquote[^>]*>',
            '<blockquote style="'
            'border:1px solid #bfdbfe;'
            'border-left:6px solid #3b82f6;'
            'padding:20px 24px;'
            'margin:24px 0;'
            'background:linear-gradient(135deg,#f8fafc,#eff6ff);'
            'color:#374151;'
            'font-size:15px;'
            'border-radius:0 12px 12px 0;'
            'box-shadow:0 2px 8px rgba(0,0,0,0.04);'
            '">',
            html
        )
        
        # ── 代码块（Apple Terminal 风格） ──
        html = re.sub(
            r'<pre><code[^>]*>',
            '<pre style="'
            'background-color:#1e1e1e;color:#e8e8e8;'
            'padding:36px 24px 20px;'
            'border-radius:10px;'
            'overflow-x:auto;font-size:13px;line-height:1.7;'
            'margin:24px 0;'
            'box-shadow:0 4px 20px rgba(0,0,0,0.25);'
            'border:1px solid #3d3d3d;'
            'background-image:'
            'radial-gradient(circle 5px at 24px 18px,#ff5f56 99%,transparent),'
            'radial-gradient(circle 5px at 40px 18px,#ffbd2e 99%,transparent),'
            'radial-gradient(circle 5px at 56px 18px,#27c93f 99%,transparent);'
            'background-repeat:no-repeat;'
            '"><code style="font-family:\'SF Mono\',\'Menlo\',\'Monaco\',\'Consolas\',\'Courier New\',monospace;'
            'background:transparent;padding:0;color:#e8e8e8;border:none;font-size:13px;">',
            html
        )
        # Inline code# Inline code
        html = re.sub(
            r'<code>(?![^<]*</pre)',
            '<code style="background:#f0fdf4;color:#16a34a;padding:3px 10px;'
            'border-radius:4px;font-size:14px;font-weight:500;'
            'font-family:\'JetBrains Mono\',\'Fira Code\',monospace;'
            'border:1px solid #bbf7d0;'
            '">',
            html
        )
        
        # ── 水平分割线（Apple 标准浅灰细线） ──
        html = re.sub(
            r'<hr[^>]*>',
            '<div style="margin:32px 0;text-align:center;">'
            '<span style="display:block;width:100%;height:1px;'
            'background:#e5e7eb;"></span></div>',
            html
        )
        
        # ── 图片（已移除：文章不再内嵌插图） ──
        html = re.sub(
            r'<img[^>]*>',
            '',
            html
        )
        
        # ── 链接 ──
        html = re.sub(
            r'<a ',
            '<a style="color:#16a34a;text-decoration:none;'
            'border-bottom:1px solid #bbf7d0;padding-bottom:2px;'
            '" ',
            html
        )

        # ── 来源引用/参考资料段（论文引用风格·极弱视觉权重）──
        # 必须在链接样式替换之后执行，否则会被覆盖
        # 把 数据来源. / 参考资料：段内的所有 a 链接弱化为浅灰点线
        # 先找到 数据来源. / 参考资料：段（用更宽松的匹配，不过滤 "）
        sources_match = re.search(
            r'<p[^>]*>\s*(?:数据来源|参考资料)[\.：].*?</p>',
            html, flags=re.DOTALL
        )
        if sources_match:
            block = sources_match.group(0)
            # 改整体 p 样式为弱化
            block = re.sub(
                r'<p style="[^"]*"',
                '<p style="margin:36px 0 0 0;padding-top:14px;'
                'border-top:1px solid #f3f4f6;'
                'color:#9ca3af;font-size:11px;font-weight:300;'
                'line-height:1.7;letter-spacing:0.2px;'
                'text-align:justify;"',
                block,
                count=1
            )
            # 改 a 样式为弱化
            block = re.sub(
                r'<a style="[^"]*"',
                '<a style="color:#9ca3af;text-decoration:none;'
                'border-bottom:1px dotted #d1d5db;padding-bottom:1px;'
                'font-weight:300;"',
                block
            )
            html = html.replace(sources_match.group(0), block)
        
        # ── 列表 ──
        html = re.sub(
            r'<ul>',
            '<ul style="padding-left:24px;margin:14px 0;line-height:1.8;'
            'list-style-type:disc;color:#595959;">',
            html
        )
        html = re.sub(
            r'<ol>',
            '<ol style="padding-left:24px;margin:14px 0;line-height:1.8;'
            'list-style-type:decimal;color:#595959;">',
            html
        )
        html = re.sub(
            r'<li>',
            '<li style="margin:2px 0;color:#595959;padding-left:6px;'
            'list-style-position:inside;">',
            html
        )
        
        # ── 清理：移除 <li> 内的 <p> 包装（extra 扩展会包一层 p，导致多余空行） ──
        html = re.sub(r'<li([^>]*)>\s*<p[^>]*>\s*', r'<li\1>', html, flags=re.DOTALL)
        html = re.sub(r'\s*</p>\s*</li>', r'</li>', html, flags=re.DOTALL)
        
        # ── 拆分：同一段落内的多个 ●/①② 项拆成独立 <p> 标签 ──
        html = _split_list_paragraphs(html)
        
        # ── H2 后首段加背景卡片（V2 灰蓝底 + 蓝左线） ──
        html = re.sub(
            r'(</h2>\s*<p style=")([^"]+)(">)',
            r'\1background:#f8fafc;padding:14px 18px;border-radius:8px;border-left:3px solid #3b82f6;\2\3',
            html
        )
        
        return container_start + html + '</section>'
        
    except ImportError:
        import re
        html = md_text
        html = re.sub(r'^---\n.*?\n---\n', '', html, flags=re.DOTALL)
        html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        html = re.sub(r'\n\n+', '</p><p>', html)
        lines = html.split('\n')
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not line.startswith('<'):
                result.append(f'<p>{line}</p>')
            else:
                result.append(line)
        return ''.join(result)


def main():
    global _CURRENT_ACCOUNT
    
    import argparse
    parser = argparse.ArgumentParser(description="发布到微信公众号")
    parser.add_argument("--account", "-a", default=None,
                        choices=[a["key"] for a in list_accounts()],
                        help="公众号账号")
    parser.add_argument("files", nargs="*", help="文章文件路径（可选，默认读取创作目录）")
    args = parser.parse_args()
    
    _CURRENT_ACCOUNT = args.account
    cfg = get_account(_CURRENT_ACCOUNT)
    
    print("=" * 60)
    print(f"📤 Step 5: 发布到微信公众号")
    print(f"   账号: {cfg['name']} ({cfg.get('author', '')})")
    print("=" * 60)

    new_articles = [
        "文章_UModel代码知识图谱.md",
        "文章_Reasonix缓存优化.md",
        "文章_TradingAgents多智能体交易.md",
    ]

    创作_dir = BASE_DIR / "data" / "创作"
    md_files = []
    for name in new_articles:
        p = 创作_dir / name
        if p.exists():
            md_files.append(p)
        else:
            print(f"  ⚠️ 文件不存在: {name}")

    if not md_files:
        print("❌ 没有找到待发布的文章")
        return

    print(f"\n📄 将发布 {len(md_files)} 篇:")
    for f in md_files:
        print(f"   - {f.name}")

    token = get_access_token()
    if not token:
        return

    published = []
    failed = []

    for md_path in md_files:
        print(f"\n{'─' * 50}")
        print(f"📄 {md_path.name}")

        with open(md_path, encoding="utf-8") as f:
            content = f.read()

        title_match = re.search(r'^title:\s*(.+?)\s*$', content, re.M)
        title = title_match.group(1).strip() if title_match else md_path.stem
        print(f"   标题: {title}")

        # 上传永久封面素材 - 返回 media_id
        media_id = upload_permanent_image(token, title)

        if not media_id:
            print("  ❌ 封面上传失败，跳过")
            failed.append(title)
            continue

        # 构建html内容
        html_content = markdown_to_html(content)
        if len(html_content) > 60000:
            html_content = html_content[:60000]

        # 创建草稿
        body = {
            "articles": [
                {
                    "title": title,
                    "content": html_content,
                    "thumb_media_id": media_id,
                    "author": cfg.get("author", ""),
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }
            ]
        }
        print(f"   作者: {cfg.get('author', '')}")
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        resp = http_request(url, body, "POST")

        if "media_id" in resp:
            print(f"  ✅ 草稿创建成功！media_id={resp['media_id']}")
            try:
                记录发布成功(标题=title, url="", 来源="微信自动发布", 摘要=content[:300])
            except Exception as e:
                print(f"   ⚠️ 记录发布历史失败: {e}")
            published.append((title, resp["media_id"]))
            dest = BASE_DIR / "data" / "output" / md_path.name
            import shutil
            shutil.copy2(md_path, dest)
            md_path.unlink()
            print(f"   ✅ 已移到 output 目录")
        else:
            print(f"  ❌ 草稿创建失败: {resp}")
            failed.append(title)

        time.sleep(2)

    print(f"\n{'=' * 60}")
    print(f"📊 发布汇总:")
    print(f"   成功: {len(published)} 篇")
    for title, mid in published:
        print(f"   ✅ 「{title}」 → media_id: {mid}")
    if failed:
        print(f"   失败: {len(failed)} 篇")
        for title in failed:
            print(f"   ❌ {title}")


if __name__ == "__main__":
    main()
