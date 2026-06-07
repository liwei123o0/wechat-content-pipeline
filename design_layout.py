#!/usr/bin/env python3
"""
文章排版管理 v1 — 双风格排版分发引擎
===================================
AI资讯类 (style_news)     → 紧凑简洁，数据高亮，快速阅读
干货类   (style_deep)     → 卡片分区，视觉层次丰富，知识深度阅读

用法:
    from design_layout import format_article
    html = format_article(md_text, column_slug="frontier-news")

栏目→风格映射:
    frontier-news → AI资讯类
    其他          → 干货类
"""
import re

try:
    import markdown as mdlib

    def _md(text):
        return mdlib.markdown(text, extensions=['extra'])
except ImportError:
    def _md(text):
        """纯文本降级"""
        text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
        text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.M)
        text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.M)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        lines = []
        for p in text.split('\n\n'):
            p = p.strip()
            if p:
                lines.append(f'<p>{p}</p>')
        return '\n'.join(lines)


# ───── 公共预处理 ─────

def _clean_md(md_text):
    """移除 frontmatter 和元数据，统一清洗"""
    body = re.sub(r'^---\n.*?\n---\n', '', md_text, flags=re.DOTALL)
    lines = body.split('\n')
    clean = []
    in_meta = False
    for line in lines:
        if re.match(r'^(cover_media_id|cover_source|body_image_urls|thumb_media_id):', line):
            in_meta = True
            continue
        if in_meta:
            if line.strip() == '' or not re.match(r'^\s*[●\-*\d]', line):
                in_meta = False
            continue
        clean.append(line)
    body = '\n'.join(clean)
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = re.sub(r'([^\n|])\n(\|[^\n]+\n\|[-| ]+\n)', r'\1\n\n\2', body)
    return body


def _convert_lists(text):
    """带圈列表转换（公众号不支持 <ul>/<ol> 渲染）"""
    circled = [chr(0x2460 + i) for i in range(20)]
    lines = text.split('\n')
    result = []
    for line in lines:
        um = re.match(r'^\s*[-*+]\s+(.*)', line)
        if um and um.group(1).strip():
            result.append('\u25cf ' + um.group(1).strip())
            continue
        om = re.match(r'^\s*(\d+)\.\s+(.*)', line)
        if om:
            num = int(om.group(1))
            txt = om.group(2).strip()
            if txt:
                marker = circled[num - 1] if 1 <= num <= 20 else str(num) + '.'
                result.append(marker + ' ' + txt)
            continue
        result.append(line)
    return '\n'.join(result)


def _split_bullet_paragraphs(html):
    """同一段落内的多个 ●/①② 拆成独立 <p>"""
    def splitter(m):
        style = m.group(1)
        content = m.group(2)
        items = [l.strip() for l in content.split('\n') if l.strip()]
        if len(items) <= 1:
            return m.group(0)
        return ''.join(f'<p{style}>{l}</p>' for l in items)

    bullet = chr(0x25cf)
    html = re.sub(rf'<p([^>]*)>((?={bullet})(?:{bullet}[^\n]*)(?:\n{bullet}[^\n]*)+)</p>',
                  splitter, html, flags=re.DOTALL)

    circled_set = ''.join(chr(0x2460 + i) for i in range(20))
    html = re.sub(rf'<p([^>]*)>((?=[{circled_set}])(?:[{circled_set}][^\n]*)(?:\n[{circled_set}][^\n]*)+)</p>',
                  splitter, html, flags=re.DOTALL)
    return html


# ══════════════════════════════════════════════
#  风格一：AI资讯类 — 紧凑·蓝调·数据高亮
# ══════════════════════════════════════════════

def style_news(md_text):
    """AI资讯类排版：紧凑间距、蓝色系、数据/数字高亮"""
    body = _clean_md(md_text)

    # Convert markdown lists to symbols
    body = _convert_lists(body)
    html = _md(body)

    # ── 容器（微信兼容 — 用div替代section避免被编辑器剥离） ──
    container_start = (
        '<div style="'
        'color:#374151;letter-spacing:0.3px;'
        'padding:0 14px;'
        'font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;'
        'text-align:justify;">'
    )

    # ── H1 标题（蓝左竖线） ──
    html = re.sub(r'<h1>',
                  '<h1 style="font-size:20px;font-weight:bold;color:#0f172a;'
                  'margin:28px 0 14px;line-height:1.5;'
                  'border-left:4px solid #2563eb;padding:4px 0 4px 14px;">',
                  html)

    # ── H2 标题 ──
    html = re.sub(r'<h2>',
                  '<h2 style="font-size:18px;font-weight:700;color:#1e293b;'
                  'margin:30px 0 12px;line-height:1.5;'
                  'border-left:4px solid #3b82f6;padding:4px 0 4px 14px;">',
                  html)

    # ── H3 标题（蓝色左竖线，与 H1/H2 统一新闻风格） ──
    html = re.sub(r'<h3>',
                  '<h3 style="font-size:16px;font-weight:bold;color:#1e293b;'
                  'margin:22px 0 10px;line-height:1.5;'
                  'border-left:3px solid #60a5fa;padding:3px 0 3px 12px;">',
                  html)

    # ── 段落（紧凑，含字体信息和行距，脱离section也能独立渲染） ──
    html = re.sub(r'<p>',
                  '<p style="margin:0 0 14px;font-size:15px;line-height:1.7;text-align:justify;color:#374151;">',
                  html)

    # ── 加粗（蓝色高亮，资讯风格） ──
    html = re.sub(r'<strong>',
                  '<strong style="color:#1d4ed8;font-weight:700;'
                  'background:linear-gradient(to top,rgba(37,99,235,0.12) 40%,transparent 40%);'
                  'padding:0 2px;">',
                  html)

    # ── 表格（紧凑+蓝头） ──
    html = re.sub(r'<table[^>]*>',
                  '<table style="border-collapse:collapse;width:100%;font-size:12px;margin:18px 0;'
                  'box-shadow:0 1px 3px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">',
                  html)
    html = re.sub(r'<th\b[^>]*>',
                  '<th style="background:#1e3a5f;color:#fff;padding:6px 8px;'
                  'text-align:center;font-weight:600;border:1px solid #15294a;font-size:11px;'
                  'word-break:break-word;">',
                  html)
    html = re.sub(r'<td\b[^>]*>',
                  '<td style="padding:6px 8px;border:1px solid #e2e8f0;text-align:left;color:#475569;'
                  'font-size:11px;word-break:break-word;">',
                  html)

    # ── 引用块（蓝边卡片） ──
    html = re.sub(r'<blockquote[^>]*>',
                  '<blockquote style="border:1px solid #bfdbfe;border-left:6px solid #3b82f6;'
                  'padding:16px 20px;margin:18px 0;background:#f8fafc;color:#374151;font-size:14px;'
                  'border-radius:0 8px 8px 0;">',
                  html)

    # ── 代码块（深色终端风格） ──
    html = re.sub(
        r'<pre><code[^>]*>',
        '<pre style="background-color:#1e1e1e;color:#e8e8e8;padding:32px 20px 16px;'
        'border-radius:8px;overflow-x:auto;font-size:12px;line-height:1.6;margin:18px 0;'
        'box-shadow:0 3px 12px rgba(0,0,0,0.2);border:1px solid #3d3d3d;'
        'background-image:radial-gradient(circle 4px at 20px 14px,#ff5f56 99%,transparent),'
        'radial-gradient(circle 4px at 34px 14px,#ffbd2e 99%,transparent),'
        'radial-gradient(circle 4px at 48px 14px,#27c93f 99%,transparent);'
        'background-repeat:no-repeat;">'
        '<code style="font-family:\'SF Mono\',\'Menlo\',\'Monaco\',\'Consolas\',\'Courier New\',monospace;'
        'background:transparent;padding:0;color:#e8e8e8;border:none;font-size:12px;">',
        html)

    # Inline code
    html = re.sub(r'<code>(?![^<]*</pre)',
                  '<code style="background:#eff6ff;color:#2563eb;padding:2px 8px;'
                  'border-radius:4px;font-size:13px;font-weight:500;'
                  'font-family:\'JetBrains Mono\',\'Fira Code\',monospace;'
                  'border:1px solid #bfdbfe;">',
                  html)

    # ── 分割线（浅蓝细线） ──
    html = re.sub(r'<hr[^>]*>',
                  '<div style="margin:24px 0;text-align:center;">'
                  '<span style="display:block;width:100%;height:1px;background:#e2e8f0;"></span></div>',
                  html)

    # ── 链接 ──
    html = re.sub(r'<a ',
                  '<a style="color:#2563eb;text-decoration:none;'
                  'border-bottom:1px solid #bfdbfe;padding-bottom:1px;" ',
                  html)

    # ── 来源引用/参考资料（极弱视觉权重） ──
    src = re.search(r'<p[^>]*>\s*(?:数据来源[\.：]|参考资料[\.：]).*?</p>', html, flags=re.DOTALL)
    if src:
        block = src.group(0)
        block = re.sub(r'<p style="[^"]*"', '<p style="margin:28px 0 0 0;padding-top:10px;'
                       'border-top:1px solid #f3f4f6;color:#9ca3af;font-size:11px;'
                       'font-weight:300;line-height:1.6;text-align:justify;"', block, count=1)
        block = re.sub(r'<a style="[^"]*"',
                       '<a style="color:#9ca3af;text-decoration:none;border-bottom:1px dotted #d1d5db;"',
                       block)
        # 将换行转 <br/> 防止微信编辑器拆分段落导致丢失样式
        block = block.replace('\n', '<br/>\n')
        html = html.replace(src.group(0), block)

    # ── 列表 ──
    html = re.sub(r'<ul>',
                  '<ul style="padding-left:20px;margin:10px 0;line-height:1.7;list-style-type:disc;color:#374151;">',
                  html)
    html = re.sub(r'<ol>',
                  '<ol style="padding-left:20px;margin:10px 0;line-height:1.7;list-style-type:decimal;color:#374151;">',
                  html)
    html = re.sub(r'<li>',
                  '<li style="margin:2px 0;color:#374151;padding-left:4px;list-style-position:inside;">',
                  html)
    html = re.sub(r'<li([^>]*)>\s*<p[^>]*>\s*', r'<li\1>', html, flags=re.DOTALL)
    html = re.sub(r'\s*</p>\s*</li>', r'</li>', html, flags=re.DOTALL)

    # 拆分列表
    html = _split_bullet_paragraphs(html)

    # ── 概述句（标题下方第一段：小1号、浅色、左侧竖线装饰） ──
    html = re.sub(
        r'(</h1>\s*)<p style="[^"]*">',
        r'\1<p style="margin:-4px 0 18px;font-size:14px;line-height:1.6;text-align:justify;'
        r'color:#888;font-style:italic;'
        r'border-left:3px solid #d1d5db;padding:2px 0 2px 14px;">',
        html,
        count=1
    )

    return container_start + html + '</div>'


# ══════════════════════════════════════════════
#  风格二：干货类 — 知识卡片·分区·丰富视觉
# ══════════════════════════════════════════════

BG_A = '#f7f6f4'
BG_B = '#f5f5f4'


def _esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _p(s, inner):
    return f'<p style="{s}">{inner}</p>'


def _div(s, inner):
    return f'<div style="{s}">{inner}</div>'


def _title_card(t, sub):
    return _div(
        'background:#f0f5ec;border:1px solid #d4e0d0;border-top:4px solid #7db08a;'
        'border-radius:10px;padding:36px 24px;text-align:center;margin-bottom:25px;'
        'box-shadow:0 2px 10px rgba(125,176,138,0.08);',
        _p('color:#2c2c2c;font-size:28px;font-weight:600;letter-spacing:3px;line-height:1.5;margin:0;', _esc(t)) +
        _p('color:#7db08a;font-size:15px;font-weight:400;letter-spacing:2px;margin-top:10px;', _esc(sub))
    )


def _intro_card(text):
    return _div(
        'background:#f7f8f9;border:1px solid #e8ecef;border-radius:6px;padding:22px 20px;margin-bottom:24px;',
        _p('font-size:15px;color:#999;line-height:1.8;margin:0;', _esc(text))
    )


def _sec_label(n, name):
    return _div('font-size:14px;color:#bbbbbb;margin-bottom:12px;', f'{_esc(n)} ｜ {_esc(name)}')


def _sec_title(text):
    return f'<h2 style="font-size:17px;font-weight:bold;color:#2c3e50;margin:0 0 15px;">{_esc(text)}</h2>'


def _para(text, mg='0 0 10px'):
    return _p(f'font-size:16px;color:#333;line-height:2;margin:{mg};', text)


def _golden_box(text):
    return _div(
        'border-left:3px solid #c0392b;background:#ffffff;padding:14px 18px;margin:15px 0;',
        _p('font-size:16px;color:#c0392b;font-weight:bold;line-height:1.8;margin:0;', text)
    )


def _branding_line(text):
    return _p('font-size:15px;color:#888;font-style:italic;text-align:center;', text)


def _divider_line():
    return '<p><br/>---<br/></p>'


def _markup(text):
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def _sec_card(bg, inner):
    return _div(f'background:{bg};padding:20px 18px;border-radius:4px;margin:20px 0;', inner)


def _mem_a(inner):
    return _div(
        'border:1px solid #e8e8e8;background:#fafafa;border-radius:4px;padding:12px 16px;text-align:center;margin:15px 0;',
        _p('font-size:15px;color:#333;line-height:1.8;margin:0;', inner))


def _mem_b(inner):
    return _div(
        'border-left:3px solid #ccc;background:#ffffff;padding:14px 18px;margin:15px 0;',
        _p('font-size:15px;color:#333;line-height:1.8;margin:0;', inner))


def _process_section(lines, idx):
    bg = BG_A if idx % 2 == 0 else BG_B
    m_type = idx % 2
    parts = []
    in_mem = False
    mem_buf = []

    def flush_mem():
        nonlocal in_mem, mem_buf
        if not mem_buf:
            return ''
        content = '<br/>\n'.join(_markup(l) for l in mem_buf)
        mem_buf.clear()
        in_mem = False
        return _mem_a(content) if m_type == 0 else _mem_b(content)

    # Section label
    first = lines[0].strip() if lines else ''
    lm = re.match(r'(零[一二三四五六七八九十]+)\s*[｜|]\s*(.+)', first) if first else None
    if lm:
        parts.append(_sec_label(lm.group(1), lm.group(2).strip()))
        lines = lines[1:]

    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1
            continue
        if ln.startswith('## '):
            parts.append(flush_mem())
            parts.append(_sec_title(ln[3:].strip()))
            i += 1
            continue
        if ln == '---':
            parts.append(flush_mem())
            parts.append(_divider_line())
            i += 1
            continue
        if '不是' in ln and '是' in ln and not ln.startswith('**') and len(ln) < 60:
            parts.append(flush_mem())
            parts.append(_golden_box(_markup(ln)))
            i += 1
            continue
        if ln.startswith('<table') or ln.startswith('<div'):
            parts.append(flush_mem())
            parts.append(ln)
            i += 1
            continue
        if ln.startswith('</table') or ln.startswith('</div'):
            parts.append(flush_mem())
            parts.append(ln)
            i += 1
            continue
        if ln.startswith(('<thead', '<tbody', '<tr', '<th', '<td')):
            parts.append(ln)
            i += 1
            continue
        if ln.startswith(('</thead', '</tbody', '</tr', '</th', '</td')):
            parts.append(ln)
            i += 1
            continue

        is_mem = bool(re.match(r'^\*\*(一句话记|三拍子数法|终端工作流|Copilot|Codex工作流)', ln))
        is_adv = '🎯' in ln

        if is_mem:
            parts.append(flush_mem())
            mem_buf.append(ln)
            in_mem = True
            i += 1
            continue
        if is_adv:
            parts.append(flush_mem())
            parts.append(_para(_markup(ln)))
            i += 1
            continue
        if in_mem:
            mem_buf.append(ln)
            i += 1
            continue
        if ln.startswith('**感觉：') or ln.startswith('**什么场景用'):
            parts.append(_para(_markup(ln)))
            i += 1
            continue

        parts.append(_para(_markup(ln)))
        i += 1

    parts.append(flush_mem())
    return _sec_card(bg, '\n'.join(parts))


def _convert_tables(text):
    """Markdown 表格 → HTML <table>"""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|') and line.count('|') >= 2:
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                sep_line = table_lines[1].strip()
                is_sep = all(c in '| -:' for c in sep_line)
                html = '<table>\n'
                if is_sep:
                    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
                    html += '<thead>\n<tr>\n'
                    for h in headers:
                        html += f'<th>{_esc(h)}</th>\n'
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
                            html += f'<td>{_markup(c)}</td>\n'
                        html += '</tr>\n'
                    html += '</tbody>\n'
                html += '</table>'
                result.append(html)
                continue
        result.append(lines[i])
        i += 1
    return '\n'.join(result)


def _convert_code_blocks(text):
    """```代码块 → Apple Terminal 风格"""
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
            i += 1
            code_text = '\n'.join(code_lines)
            code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
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


def style_deep(md_text):
    """干货类排版：卡片分区、交替背景、结构化知识阅读"""
    body = _clean_md(md_text)
    body = _convert_tables(body)
    body = _convert_code_blocks(body)

    # Parse blocks
    lines = body.split('\n')
    blocks = []
    cur = []
    state = 'start'
    i = 0

    def flush():
        nonlocal cur
        if cur:
            blocks.append(('section', '\n'.join(cur)))
            cur.clear()

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()

        if state == 'start':
            if st == '> 标题卡片':
                state = 'title_card'
                i += 1
                continue
            elif st.startswith('> ') and not st.startswith('>>'):
                blocks.append(('intro', st[2:].strip()))
                state = 'content'
                i += 1
                continue
            elif not st:
                i += 1
                continue
            else:
                cur.append(ln)
                state = 'content'
                i += 1
                continue

        elif state == 'title_card':
            title = ''
            subtitle = ''
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                title = lines[i].strip()
                i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                subtitle = lines[i].strip()
                i += 1
            blocks.append(('title_card', {'title': title, 'subtitle': subtitle}))
            state = 'content'
            continue

        elif state == 'content':
            if not st and not cur:
                i += 1
                continue

            if st.startswith('> ') and len(st) > 2 and not any('零' in l for l in cur):
                flush()
                blocks.append(('intro', st[2:].strip()))
                i += 1
                continue

            if st == '---':
                flush()
                if not (blocks and blocks[-1][0] == 'divider'):
                    blocks.append(('divider', ''))
                i += 1
                continue

            if re.match(r'零[一二三四五六七八九十]+\s*[｜|]', st):
                flush()
                cur.append(ln)
                i += 1
                continue

            if 'Python工作圈' in st:
                flush()
                cur.append(ln)
                i += 1
                while i < len(lines):
                    l = lines[i].strip()
                    if l:
                        cur.append(l)
                    i += 1
                combined = '\n'.join(cur)
                blocks.append(('branding', combined))
                cur = []
                break

            cur.append(ln)
            i += 1

    flush()

    # Render blocks → HTML
    parts = []
    sec_idx = 0
    for bt, bd in blocks:
        if bt == 'title_card':
            parts.append(_title_card(bd['title'], bd['subtitle']))
        elif bt == 'intro':
            parts.append(_intro_card(bd))
        elif bt == 'divider':
            parts.append(_divider_line())
        elif bt == 'section':
            sl = bd.split('\n')
            parts.append(_process_section(sl, sec_idx))
            if any(re.match(r'零[一二三四五六七八九十]', l.strip()) for l in sl if l.strip()):
                sec_idx += 1
        elif bt == 'branding':
            text_lines = [l.strip() for l in bd.split('\n') if l.strip()]
            if text_lines:
                last_html = parts[-1] if parts else ''
                if not last_html.strip().endswith('---<br/></p>'):
                    parts.append(_divider_line())
                if '不是' in text_lines[0] and '是' in text_lines[0]:
                    parts.append(_golden_box(text_lines[0]))
                    if len(text_lines) > 1:
                        parts.append(_branding_line(' '.join(text_lines[1:])))
                else:
                    parts.append(_branding_line(' '.join(text_lines)))

    # Container（微信兼容 — 用div替代section避免被编辑器剥离）
    html = (
        '<div style="font-size:16px;color:#333;line-height:1.8;letter-spacing:0.5px;'
        'padding:0 16px;font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;">'
        + '\n'.join(parts) + '</div>'
    )

    # Post-processing
    html = html.replace('‖CODE_NL‖', '\n')

    # ── 来源引用/参考资料（极弱视觉权重） ──
    # 扩展匹配：从参考资料标题所在的 <p> 到 </div></div>（文章末尾）
    src = re.search(r'<p[^>]*>\s*(?:数据来源[\.：]|参考资料[\.：]).*?</p>', html, flags=re.DOTALL)
    if src:
        ref_start = src.start()
        after_ref = html[ref_start:]
        # 截取到 </div></div> 前
        end_marker = '</div></div>'
        content_end = after_ref.rfind(end_marker)
        trailer = ''
        if content_end > 0:
            trailer = after_ref[content_end:]
            after_ref = after_ref[:content_end]

        # 找出所有 <p> 段落
        all_ps = list(re.finditer(r'<p[^>]*>.*?</p>', after_ref, flags=re.DOTALL))
        if all_ps:
            # 第一个段落：顶部边框 + 灰色样式
            first = all_ps[0].group(0)
            first = re.sub(r'<p[^>]*>',
                           '<p style="margin:28px 0 0 0;padding-top:10px;border-top:1px solid #f3f4f6;color:#9ca3af;font-size:11px;font-weight:300;line-height:1.6;text-align:justify;">',
                           first, count=1)
            first = re.sub(r'<a style="[^"]*"',
                           '<a style="color:#9ca3af;text-decoration:none;border-bottom:1px dotted #d1d5db;"',
                           first)
            after_ref = after_ref.replace(all_ps[0].group(0), first, 1)

            # 后续段落：灰色样式（无顶部边框）
            REF_SUB_STYLE = 'margin:2px 0;padding:2px 0;color:#9ca3af;font-size:11px;font-weight:300;line-height:1.6;text-align:justify;'
            for m in all_ps[1:]:
                old = m.group(0)
                new_p = re.sub(r'<p[^>]*>', f'<p style="{REF_SUB_STYLE}">', old, count=1)
                new_p = re.sub(r'<a style="[^"]*"',
                               '<a style="color:#9ca3af;text-decoration:none;border-bottom:1px dotted #d1d5db;"',
                               new_p)
                after_ref = after_ref.replace(old, new_p)

        after_ref = after_ref.replace('\n', '<br/>\n')
        html = html[:ref_start] + after_ref + trailer
    html = re.sub(
        r'<code>(?![^<]*</pre)',
        '<code style="background:#f0fdf4;color:#16a34a;padding:3px 10px;border-radius:4px;font-size:14px;border:1px solid #bbf7d0;font-family:monospace;">',
        html)
    html = re.sub(r'<table>',
                  '<div style="border:1px solid #e0e0e0;border-radius:4px;overflow:hidden;margin:15px 0;"><table style="width:100%;border-collapse:collapse;font-size:14px;">',
                  html)
    html = re.sub(r'</table>', '</table></div>', html)
    html = re.sub(r'<th>',
                  '<th style="padding:10px 12px;text-align:left;color:#e8c35e;font-weight:bold;border:none;">',
                  html)
    html = re.sub(r'<thead>', '<thead style="background:linear-gradient(135deg,#1a2a3a,#2c3e50);">', html)
    html = re.sub(r'<td>', '<td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;color:#333;">', html)
    rc = [0]
    html = re.sub(r'<tr>', lambda m: (rc.__setitem__(0, rc[0] + 1) or
                 f'<tr style="background:{"#ffffff" if rc[0] % 2 == 1 else "#fafafa"};">'), html)

    return html


# ══════════════════════════════════════════════
#  栏目 → 风格映射
# ══════════════════════════════════════════════

COLUMN_STYLE_MAP = {
    # AI资讯类 — 紧凑·新闻·快速阅读
    "frontier-news": "news",

    # 干货类 — 卡片·深度·知识结构
    "vibe-coding": "deep",
    "ai-tools": "deep",
    "agent-money": "deep",
    "ai-career": "deep",
    "pitfalls": "deep",
    "weekly-ops": "deep",
}

DEFAULT_STYLE = "deep"


def get_style_for_column(column_slug):
    """根据栏目 slug 返回排版风格名"""
    if not column_slug:
        return DEFAULT_STYLE
    return COLUMN_STYLE_MAP.get(column_slug, DEFAULT_STYLE)


def format_article(md_text, column_slug=None, style_name=None):
    """
    统一入口：根据文章内容和栏目返回排版后的 HTML。

    参数:
        md_text     — markdown 原文（含 frontmatter）
        column_slug — 栏目 slug，自动匹配风格
        style_name  — 强制指定风格（覆盖 column 映射）
                      'news' → AI资讯类 | 'deep' → 干货类

    返回:
        str — 排版后的 HTML
    """
    actual_style = style_name or get_style_for_column(column_slug)

    if actual_style == "news":
        return style_news(md_text)
    else:
        return style_deep(md_text)


# ══════════════════════════════════════════════
#  CLI 入口
# ══════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='文章排版管理 — 双风格分发')
    parser.add_argument('file', help='markdown 文章路径')
    parser.add_argument('--column', '-c', default=None, help='栏目 slug（如 frontier-news）')
    parser.add_argument('--style', '-s', choices=['news', 'deep'], default=None,
                        help='强制指定排版风格')
    parser.add_argument('--output', '-o', default=None, help='输出 HTML 文件路径')
    args = parser.parse_args()

    with open(args.file, encoding='utf-8') as f:
        text = f.read()

    html = format_article(text, column_slug=args.column, style_name=args.style)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 已输出到 {args.output}")
    else:
        print(html)
