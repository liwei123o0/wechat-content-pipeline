#!/usr/bin/env python3
"""
零依赖 docx 生成器 - 将 Markdown 转为 .docx
利用 docx = ZIP 含 XML 的原理，不依赖 python-docx
"""
import re
import sys
import zipfile
import os
from pathlib import Path
from datetime import datetime


def _escape_xml(s):
    """转义 XML 特殊字符"""
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s


def markdown_to_docx(md_path, output_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 提取标题
    title_match = re.search(r'^title:\s*(.+?)\s*$', text, re.M)
    title = title_match.group(1).strip() if title_match else Path(md_path).stem

    # 去除 frontmatter 和 YAML metadata
    body = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
    # 去除残留的 metadata 行 (cover_media_id, body_image_urls 等)
    body = re.sub(r'^(cover_media_id|cover_source|body_image_urls):.*$', '', body, flags=re.MULTILINE)
    body = re.sub(r'^\s*[-*]\s+http\S+', '', body, flags=re.MULTILINE)
    # 清除空行过多
    body = re.sub(r'\n{3,}', '\n\n', body)

    lines = body.strip().split('\n')

    # 构建 Word XML
    body_xml_parts = []

    # 标题样式
    body_xml_parts.append(f'''<w:p>
      <w:pPr><w:pStyle w:val="Title"/></w:pPr>
      <w:r><w:t>{_escape_xml(title)}</w:t></w:r>
    </w:p>''')

    # 日期
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    body_xml_parts.append(f'''<w:p>
      <w:pPr><w:jc w:val="left"/></w:pPr>
      <w:r><w:rPr><w:sz w:val="20"/><w:color w:val="808080"/></w:rPr><w:t>{_escape_xml("发布于: " + date_str)}</w:t></w:r>
    </w:p>''')

    # 空行
    body_xml_parts.append('<w:p><w:r><w:t> </w:t></w:r></w:p>')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # H2
        if stripped.startswith('## '):
            text_content = stripped[3:].strip()
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
              <w:r><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # H3
        elif stripped.startswith('### '):
            text_content = stripped[4:].strip()
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="Heading3"/></w:pPr>
              <w:r><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # 引用
        elif stripped.startswith('> '):
            text_content = stripped[2:].strip()
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="Quote"/><w:jc w:val="left"/></w:pPr>
              <w:r><w:rPr><w:i/><w:color w:val="6B7280"/></w:rPr><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # 无序列表
        elif stripped.startswith('- '):
            text_content = stripped[2:].strip()
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="ListBullet"/></w:pPr>
              <w:r><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # 有序列表
        elif re.match(r'^\d+\.\s', stripped):
            text_content = re.sub(r'^\d+\.\s', '', stripped)
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="ListNumber"/></w:pPr>
              <w:r><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # 分隔线
        elif stripped in ('---', '___', '***') and len(stripped) <= 4:
            body_xml_parts.append('<w:p><w:r><w:t>────────────────────</w:t></w:r></w:p>')
        # 带圈列表（●）
        elif stripped.startswith('●') or stripped.startswith('•'):
            text_content = stripped[1:].strip()
            body_xml_parts.append(f'''<w:p>
              <w:pPr><w:pStyle w:val="ListBullet"/></w:pPr>
              <w:r><w:t>{_escape_xml(text_content)}</w:t></w:r>
            </w:p>''')
        # 普通段落（支持加粗）
        else:
            # 处理 **加粗**
            parts = re.split(r'(\*\*.+?\*\*)', stripped)
            runs_xml = ''
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    text = part[2:-2]
                    runs_xml += f'<w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr><w:t>{_escape_xml(text)}</w:t></w:r>'
                else:
                    runs_xml += f'<w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t>{_escape_xml(part)}</w:t></w:r>'
            body_xml_parts.append(f'<w:p>{runs_xml}</w:p>')

    body_xml = ''.join(body_xml_parts)

    # ── 构建完整的 .docx（ZIP） ──

    # [Content_Types].xml
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

    # _rels/.rels
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    # word/_rels/document.xml.rels
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    # word/styles.xml
    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
    <w:rPr><w:sz w:val="24"/><w:rFonts w:ascii="等线" w:eastAsia="等线"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:rPr><w:sz w:val="36"/><w:b/><w:color w:val="1a1a1a"/><w:rFonts w:ascii="微软雅黑" w:eastAsia="微软雅黑"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:rPr><w:sz w:val="32"/><w:b/><w:color w:val="2d3748"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:rPr><w:sz w:val="28"/><w:b/><w:color w:val="2d3748"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:rPr><w:sz w:val="24"/><w:b/><w:color w:val="374151"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Quote">
    <w:name w:val="Quote"/>
    <w:rPr><w:i/><w:color w:val="6B7280"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListBullet">
    <w:name w:val="List Bullet"/>
    <w:rPr><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListNumber">
    <w:name w:val="List Number"/>
    <w:rPr><w:sz w:val="24"/></w:rPr>
  </w:style>
</w:styles>'''

    # word/document.xml
    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_xml}
  </w:body>
</w:document>'''

    # ── 打包 ──
    os.makedirs(output_dir, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
    filename = f'{safe_title}.docx'
    output_path = Path(output_dir) / filename

    with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('word/_rels/document.xml.rels', doc_rels)
        zf.writestr('word/styles.xml', styles_xml)
        zf.writestr('word/document.xml', document_xml)

    size_kb = os.path.getsize(output_path) / 1024
    print(f'✅ {filename} ({size_kb:.1f} KB)')
    return output_path


if __name__ == '__main__':
    md_path = sys.argv[1] if len(sys.argv) > 1 else None
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '值得顶'

    if not md_path:
        创作_dir = Path(__file__).parent / 'data' / '创作'
        files = sorted(创作_dir.glob('文章_*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
        md_path = str(files[0]) if files else None

    if md_path and Path(md_path).exists():
        markdown_to_docx(md_path, output_dir)
    else:
        print('❌ 未找到文章文件')
