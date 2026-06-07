#!/usr/bin/env python3
"""
Publish an article using the "knowledge card" style (光音谷 piano style).
Reads markdown from 创作/, converts to card-style HTML, publishes to WeChat draft.

Usage:
    cd /home/lw/wechat_publisher
    python scripts/publish_card_style.py 创作/文章_xxx.md --account old
"""
import json, os, re, sys, time, io, urllib.request, urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
from account_config import get_account, get_access_token as get_ac_token

BG_A = '#f7f6f4'; BG_B = '#f5f5f4'

# ─── Helpers ───
def esc(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def p(s, inner): return f'<p style="{s}">{inner}</p>'
def div(s, inner): return f'<div style="{s}">{inner}</div>'

def title_card(t, sub):
    return div(
        'background:#f0f5ec;border:1px solid #d4e0d0;border-top:4px solid #7db08a;'
        'border-radius:10px;padding:36px 24px;text-align:center;margin-bottom:25px;'
        'box-shadow:0 2px 10px rgba(125,176,138,0.08);',
        p('color:#2c2c2c;font-size:28px;font-weight:600;letter-spacing:3px;line-height:1.5;margin:0;',esc(t)) +
        p('color:#7db08a;font-size:15px;font-weight:400;letter-spacing:2px;margin-top:10px;',esc(sub))
    )

def intro_card(text):
    return div('background:#f7f8f9;border:1px solid #e8ecef;border-radius:6px;padding:22px 20px;margin-bottom:24px;',
               p('font-size:15px;color:#999999;line-height:1.8;margin:0;',esc(text)))

def sec_label(n, name):
    return div('font-size:14px;color:#bbbbbb;margin-bottom:12px;', f'{esc(n)} ｜ {esc(name)}')

def sec_title(text):
    return f'<h2 style="font-size:17px;font-weight:bold;color:#2c3e50;margin:0 0 15px;">{esc(text)}</h2>'

def para(text, mg='0 0 10px'):
    return p(f'font-size:16px;color:#333;line-height:2;margin:{mg};', text)

def small_para(text):
    return p('font-size:16px;color:#333;line-height:2;margin:0 0 5px;', text)

def mem_a(inner):
    return div('border:1px solid #e8e8e8;background:#fafafa;border-radius:4px;padding:12px 16px;text-align:center;margin:15px 0;',
               p('font-size:15px;color:#333;line-height:1.8;margin:0;',inner))

def mem_b(inner):
    return div('border-left:3px solid #ccc;background:#ffffff;padding:14px 18px;margin:15px 0;',
               p('font-size:15px;color:#333;line-height:1.8;margin:0;',inner))

def sec_card(bg, inner):
    return div(f'background:{bg};padding:20px 18px;border-radius:4px;margin:20px 0;', inner)

def divider_line():
    return '<p><br  />---<br  /></p>'

def golden_box(text):
    return div('border-left:3px solid #c0392b;background:#ffffff;padding:14px 18px;margin:15px 0;',
               p('font-size:16px;color:#c0392b;font-weight:bold;line-height:1.8;margin:0;', text))

def branding_line(text):
    return p('font-size:15px;color:#888;font-style:italic;text-align:center;', text)

def boldify(text):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

def codeify(text):
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

def markup(text):
    return codeify(boldify(text))

# ─── Section processor ───

def process_section(lines, idx):
    bg = BG_A if idx % 2 == 0 else BG_B
    parts = []
    m_type = idx % 2  # 0=A(border), 1=B(left-border)
    in_mem = False
    mem_buf = []
    
    def flush_mem():
        nonlocal in_mem, mem_buf
        if not mem_buf: return ''
        content = '<br />\n'.join(markup(l) for l in mem_buf)
        mem_buf.clear(); in_mem = False
        return mem_a(content) if m_type == 0 else mem_b(content)
    
    # First line may be section label
    first = lines[0].strip() if lines else ''
    lm = re.match(r'(零[一二三四五六七八九十]+)\s*[｜|]\s*(.+)', first) if first else None
    if lm:
        parts.append(sec_label(lm.group(1), lm.group(2).strip()))
        lines = lines[1:]
    
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if not ln: i += 1; continue
        if ln.startswith('## '): parts.append(flush_mem()); parts.append(sec_title(ln[3:].strip())); i+=1; continue
        if ln == '---': parts.append(flush_mem()); parts.append(divider_line()); i+=1; continue
        # Ending golden quote (last section only - contains "不是...是" pattern at end)
        if '不是' in ln and '是' in ln and not ln.startswith('**') and len(ln) < 60:
            parts.append(flush_mem()); parts.append(golden_box(markup(ln))); i+=1; continue
        # Raw HTML passthrough (table tags, divs)
        if ln.startswith('<table') or ln.startswith('<div'):
            parts.append(flush_mem()); parts.append(ln); i+=1; continue
        if ln.startswith('</table') or ln.startswith('</div'):
            parts.append(flush_mem()); parts.append(ln); i+=1; continue
        if ln.startswith('<thead') or ln.startswith('<tbody') or ln.startswith('<tr') or ln.startswith('<th') or ln.startswith('<td'):
            parts.append(ln); i+=1; continue
        if ln.startswith('</thead') or ln.startswith('</tbody') or ln.startswith('</tr') or ln.startswith('</th') or ln.startswith('</td'):
            parts.append(ln); i+=1; continue
        
        mem_trig = bool(re.match(r'^\*\*(一句话记|三拍子数法|终端工作流|Copilot(核心)?用法|Codex工作流|6/8和3/4的区别|终端三步法)', ln))
        is_adv = '🎯' in ln
        
        if mem_trig: parts.append(flush_mem()); mem_buf.append(ln); in_mem = True; i+=1; continue
        if is_adv: parts.append(flush_mem()); parts.append(para(markup(ln))); i+=1; continue
        if in_mem: mem_buf.append(ln); i+=1; continue
        if ln.startswith('**感觉：'): parts.append(para(markup(ln))); i+=1; continue
        if ln.startswith('**什么场景用'): parts.append(small_para(markup(ln))); i+=1; continue
        
        parts.append(para(markup(ln))); i+=1
    
    parts.append(flush_mem())
    return sec_card(bg, '\n'.join(parts))


# ─── Main conversion ───

# ─── Table conversion ───

def _convert_tables(text):
    """Convert markdown table syntax | ... | to HTML <table> tags"""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detect table: line starts with | and has at least one more |
        if line.startswith('|') and line.count('|') >= 2:
            table_lines = [line]
            i += 1
            # Collect consecutive table lines
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            # Convert to HTML
            if len(table_lines) >= 2:
                # Check second line for separator (|---|)
                sep_line = table_lines[1].strip()
                is_separator = all(c in '| -:' for c in sep_line)
                
                html = '<table>\n'
                if is_separator:
                    # Header row + separator
                    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
                    html += '<thead>\n<tr>\n'
                    for h in headers:
                        html += f'<th>{esc(h)}</th>\n'
                    html += '</tr>\n</thead>\n'
                    body_start = 2
                else:
                    body_start = 0
                
                if body_start < len(table_lines):
                    html += '<tbody>\n'
                    for row_line in table_lines[body_start:]:
                        cells = [c.strip() for c in row_line.split('|')[1:-1]]
                        html += '<tr>\n'
                        for c in cells:
                            html += f'<td>{markup(c)}</td>\n'
                        html += '</tr>\n'
                    html += '</tbody>\n'
                html += '</table>'
                result.append(html)
                continue
        result.append(lines[i])
        i += 1
    return '\n'.join(result)


def _convert_code_blocks(text):
    """Convert ```lang ... ``` code blocks to Apple Terminal style HTML"""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = '\n'.join(code_lines)
            code_text = code_text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            # Replace internal newlines with placeholder to keep block atomic
            code_inner = code_text.replace('\n', '‖CODE_NL‖')
            html = (
                '<pre style="background-color:#1e1e1e;color:#ffffff;padding:36px 24px 20px;'
                'border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.7;margin:15px 0;'
                'box-shadow:0 4px 20px rgba(0,0,0,0.25);border:1px solid #3d3d3d;'
                'background-image:radial-gradient(circle 5px at 24px 18px,#ff5f56 99%,transparent),'
                'radial-gradient(circle 5px at 40px 18px,#ffbd2e 99%,transparent),'
                'radial-gradient(circle 5px at 56px 18px,#27c93f 99%,transparent);'
                'background-repeat:no-repeat;'
                'font-family:\'SF Mono\',\'Menlo\',\'Monaco\',\'Consolas\',\'Courier New\',monospace;'
                '">' + code_inner + '</pre>'
            )
            result.append(html)
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)


def card_html_from_md(md_text):
    body = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
    
    # Convert markdown tables to HTML before processing
    body = _convert_tables(body)
    # Convert code blocks to HTML
    body = _convert_code_blocks(body)
    
    # Remove leaked metadata
    cln = []; in_m = False
    for line in body.split('\n'):
        if re.match(r'^(cover_media_id|cover_source|body_image_urls|thumb_media_id):', line):
            in_m = True; continue
        if in_m:
            if line.strip() == '' or not re.match(r'^\s*[●\-*\d]', line): in_m = False
            continue
        cln.append(line)
    body = '\n'.join(cln)
    
    blocks = []  # (type, data)
    cur = []     # current content lines
    state = 'start'
    lines = body.split('\n')
    i = 0
    
    while i < len(lines):
        ln = lines[i]; st = ln.strip()
        
        if state == 'start':
            if st == '> 标题卡片':
                state = 'title_card'; i+=1; continue
            elif st.startswith('> ') and not st.startswith('>>'):
                blocks.append(('intro', st[2:].strip())); state='content'; i+=1; continue
            elif not st: i+=1; continue
            else: cur.append(ln); state='content'; i+=1; continue
        
        elif state == 'title_card':
            title = ''; subtitle = ''
            i+=1
            while i < len(lines) and not lines[i].strip(): i+=1
            if i < len(lines): title = lines[i].strip(); i+=1
            while i < len(lines) and not lines[i].strip(): i+=1
            if i < len(lines): subtitle = lines[i].strip(); i+=1
            blocks.append(('title_card', {'title':title,'subtitle':subtitle}))
            state='content'; continue
        
        elif state == 'content':
            # Skip blank lines at start of content
            if not st and not cur: i+=1; continue
            
            # Intro text with >
            if st.startswith('> ') and len(st)>2 and not any('零' in l for l in cur):
                _flush(cur, blocks); blocks.append(('intro', st[2:].strip())); i+=1; continue
            
            if st == '---':
                _flush(cur, blocks)
                if not (blocks and blocks[-1][0] == 'divider'): blocks.append(('divider',''))
                i+=1; continue
            
            # Section label
            if re.match(r'零[一二三四五六七八九十]+\s*[｜|]', st):
                _flush(cur, blocks); cur.append(ln); i+=1; continue
            
            # Branding / ending
            if 'Python工作圈' in st:
                _flush(cur, blocks); cur.append(ln); i+=1
                while i < len(lines):
                    l = lines[i].strip()
                    if l: cur.append(l)
                    i+=1
                combined = '\n'.join(cur)
                blocks.append(('branding', combined)); cur=[]; break
            
            cur.append(ln); i+=1
    
    _flush(cur, blocks)
    
    # ─── Render blocks → HTML ───
    parts = []; sec_idx = 0
    for bt, bd in blocks:
        if bt == 'title_card': parts.append(title_card(bd['title'], bd['subtitle']))
        elif bt == 'intro': parts.append(intro_card(bd))
        elif bt == 'divider': parts.append(divider_line())
        elif bt == 'section':
            sl = bd.split('\n')
            parts.append(process_section(sl, sec_idx))
            if any(re.match(r'零[一二三四五六七八九十]', l.strip()) for l in sl if l.strip()):
                sec_idx += 1
        elif bt == 'branding':
            text_lines = [l.strip() for l in bd.split('\n') if l.strip()]
            if text_lines:
                # Only add divider if last part isn't already one
                last_html = parts[-1] if parts else ''
                if not last_html.strip().endswith('---<br  /></p>'):
                    parts.append(divider_line())
                # Check if first line is the golden quote (contains "不是...是")
                if '不是' in text_lines[0] and '是' in text_lines[0]:
                    parts.append(golden_box(text_lines[0]))
                    if len(text_lines) > 1:
                        parts.append(branding_line(' '.join(text_lines[1:])))
                else:
                    parts.append(branding_line(' '.join(text_lines)))
    
    # Wrap in container
    html = (
        '<section style="font-size:16px;color:#333;line-height:1.8;letter-spacing:0.5px;'
        'padding:0 16px;font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;">'
        + '\n'.join(parts) + '</section>'
    )
    
    # Post-process: restore code block newlines
    html = html.replace('‖CODE_NL‖', '\n')
    
    # Post-process: inline code (NOT inside <pre> blocks)
    html = re.sub(
        r'<code>(?![^<]*</pre)',
        '<code style="background:#f0fdf4;color:#16a34a;padding:3px 10px;border-radius:4px;font-size:14px;border:1px solid #bbf7d0;font-family:monospace;">',
        html)
    
    # Table → card style
    html = re.sub(r'<table>',
        '<div style="border:1px solid #e0e0e0;border-radius:4px;overflow:hidden;margin:15px 0;"><table style="width:100%;border-collapse:collapse;font-size:14px;">',
        html)
    html = re.sub(r'</table>', '</table></div>', html)
    html = re.sub(r'<th>', '<th style="padding:10px 12px;text-align:left;color:#e8c35e;font-weight:bold;border:none;">', html)
    html = re.sub(r'<thead>', '<thead style="background:linear-gradient(135deg,#1a2a3a,#2c3e50);">', html)
    html = re.sub(r'<td>', '<td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;color:#333;">', html)
    rc = [0]
    def alt_row(m): rc[0]+=1; return f'<tr style="background:{"#ffffff" if rc[0]%2==1 else "#fafafa"};">'
    html = re.sub(r'<tr>', alt_row, html)
    
    return html

def _flush(cur, blocks):
    if not cur: return
    combined = '\n'.join(cur)
    if combined.strip():
        blocks.append(('section', combined))
    cur.clear()


def generate_cover_bytes(title_text):
    from PIL import Image, ImageDraw, ImageFont
    w, h = 640, 272
    img = Image.new('RGB', (w, h), (240, 245, 236))
    draw = ImageDraw.Draw(img)
    font_paths = ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                  '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc']
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try: font = ImageFont.truetype(fp, 34, index=0); break
            except: pass
    if not font: font = ImageFont.load_default()
    draw.rectangle([0,0,w,4], fill=(125,176,138))
    title = title_text[:10]
    try:
        bb = draw.textbbox((0,0), title, font=font)
        draw.text(((w-bb[2]+bb[0])//2, h//2-(bb[3]-bb[1])-8), title, fill=(44,62,80), font=font)
    except: draw.text((w//4, h//3), title, fill=(44,62,80), font=font)
    try:
        fs = ImageFont.truetype(font_paths[0], 20)
        sub = '知识卡片系列'
        bb = draw.textbbox((0,0), sub, font=fs)
        draw.text(((w-bb[2]+bb[0])//2, h//2+12), sub, fill=(125,176,138), font=fs)
    except: pass
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def upload_cover(token, img_data):
    boundary = "----WebKitFormBoundary" + str(hash(time.time()))
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode(),
        img_data,
        f"\r\n--{boundary}--\r\n".encode()
    ])
    req = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode())
        if "media_id" in r: print(f"  ✅ 封面上传成功: media_id={r['media_id']}"); return r['media_id']
        else: print(f"  ⚠️ 上传失败: {r}"); return None
    except Exception as e: print(f"  ❌ 上传异常: {e}"); return None


def publish(article_path, account='old'):
    print("="*60); print("📤 知识卡片风格发布"); print("="*60)
    with open(article_path, encoding='utf-8') as f: content = f.read()
    fm = {}
    m = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            kv = re.match(r'^(\w+):\s*(.+?)\s*$', line)
            if kv: fm[kv.group(1)] = kv.group(2)
    title = fm.get('title', Path(article_path).stem)
    title = title.strip("'\" ")
    author = fm.get('author', 'Python工作圈')
    print(f"📄 文章: {title}\n👤 作者: {author}")
    print("\n🔄 转换到知识卡片风格HTML...")
    html = card_html_from_md(content)
    print(f"   HTML长度: {len(html)} 字符")
    cfg = get_account(account)
    print(f"\n🔑 获取token [{cfg['name']}]...")
    token = get_ac_token(account)
    if not token: print("❌ 获取token失败"); return False
    print("\n🖼️ 生成并上传封面...")
    cid = upload_cover(token, generate_cover_bytes(title))
    draft = {"articles":[{"title":title,"content":html,"thumb_media_id":cid or "","author":author,"need_open_comment":1,"only_fans_can_comment":0}]}
    print("\n📝 创建微信草稿箱...")
    data = json.dumps(draft, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
        data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode())
        if "media_id" in r:
            print(f"\n✅ 草稿创建成功！media_id={r['media_id']}")
            print(f"\n📌 请登录 mp.weixin.qq.com → 草稿箱 手动群发"); return True
        else: print(f"\n❌ 草稿创建失败: {r}"); return False
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP错误 {e.code}: {e.read().decode('utf-8','replace')[:500]}"); return False
    except Exception as e:
        print(f"\n❌ 异常: {e}"); return False

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='知识卡片风格发布')
    parser.add_argument('file', help='文章markdown路径')
    parser.add_argument('--account','-a', default='old', help='公众号账号')
    args = parser.parse_args()
    sys.exit(0 if publish(args.file, account=args.account) else 1)
