#!/usr/bin/env python3
"""
重新发布(呼吸感优化版): 桌面Agent大爆发
读取更新后的 .md，按设计师v3.1格式生成HTML，通过 draft/update 替换原草稿
"""
import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from account_config import get_access_token as get_ac_token

# ===== 常量 =====
MD_PATH = Path(__file__).parent / "创作" / "article_桌面Agent大爆发_20260604.md")
# 原草稿 media_id（来自上次发布的返回）
OLD_DRAFT_MEDIA_ID = "O3o4IHlucqYmVliSX1xilejIRMSXOn3wljLPCW_hWWPJ0yoX3wFYeOfAqPObwIu0"
# 封面图 media_id（无需重新上传，保持不变）
THUMB_MEDIA_ID = "O3o4IHlucqYmVliSX1xilXvBPWJv8bqSAWK1K6FOTDmapQi4DwfaemVt1NoiyXtH"
TITLE = "48 小时 5 款桌面 Agent 齐发：当 AI 开始用 AI 造自己的工具"
AUTHOR = "Python工作圈"


def http_request(url, data=None, method="GET"):
    if data and isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"errcode": e.code, "errmsg": body[:200]}
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}


def parse_md(md_text):
    """解析 YAML frontmatter 和 body"""
    m = re.match(r"^---\n(.*?)\n---\n(.*)", md_text, re.DOTALL)
    if m:
        frontmatter = m.group(1)
        body = m.group(2)
    else:
        frontmatter = ""
        body = md_text
    return frontmatter, body


def convert_to_designer_html(md_body):
    """
    将 markdown body 转为设计师v3.1风格的HTML
    
    保持原始的分段（writer优化的6处文字墙拆短段落）
    应用设计师的 inline style 格式
    """
    # 设计师样式常量
    DIV_OPEN = '<div style="color:#374151;letter-spacing:0.3px;padding:0 14px;font-family:-apple-system,BlinkMacSystemFont,Helvetica Neue,PingFang SC,Microsoft YaHei,sans-serif;text-align:justify;">\n'
    DIV_CLOSE = "</div>"
    H1_STYLE = 'style="font-size:20px;font-weight:bold;color:#0f172a;margin:28px 0 14px;line-height:1.5;border-left:4px solid #2563eb;padding:4px 0 4px 14px;"'
    H2_STYLE = 'style="font-size:18px;font-weight:700;color:#1e293b;margin:30px 0 12px;line-height:1.5;border-left:4px solid #3b82f6;padding:4px 0 4px 14px;"'
    P_STYLE = 'style="margin:0 0 14px;font-size:15px;line-height:1.7;text-align:justify;color:#374151;"'
    STRONG_STYLE = 'style="color:#1d4ed8;font-weight:700;background:linear-gradient(to top,rgba(37,99,235,0.12) 40%,transparent 40%);padding:0 2px;"'
    A_STYLE = 'style="color:#9ca3af;text-decoration:none;border-bottom:1px dotted #d1d5db;"'
    REFS_P_STYLE = 'style="margin:28px 0 0 0;padding-top:10px;border-top:1px solid #f3f4f6;color:#9ca3af;font-size:11px;font-weight:300;line-height:1.6;text-align:justify;"'

    lines = md_body.strip().split("\n")
    html_parts = []
    i = 0

    def escape_html(text):
        """转义 HTML 特殊字符"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text

    def process_inline(text):
        """处理行内标记：粗体、链接、斜体"""
        # 先处理粗体 **text**
        text = re.sub(
            r'\*\*(.+?)\*\*',
            lambda m: f'<strong {STRONG_STYLE}>{m.group(1)}</strong>',
            text
        )
        # 处理链接 [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: f'<a {A_STYLE} href="{m.group(2)}">{m.group(1)}</a>',
            text
        )
        # 处理斜体 *text* (但不处理已经是 HTML 标签内部的部分)
        text = re.sub(
            r'(?<![<])[\*＿](.+?)[\*＿](?![^<]*>)',
            r'<em>\1</em>',
            text
        )
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # h1 (title)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            content = stripped[2:]
            content = escape_html(content)
            html_parts.append(f'<h1 {H1_STYLE}>{content}</h1>')
            i += 1
            continue

        # h2 (section header)
        if stripped.startswith("## "):
            content = stripped[3:]
            content = escape_html(content)
            html_parts.append(f'<h2 {H2_STYLE}>{content}</h2>')
            i += 1
            continue

        # Image line: ![alt](url)
        img_match = re.match(r'!\[(.*?)\]\((.*?)\)\s*$', stripped)
        if img_match:
            alt = img_match.group(1)
            src = img_match.group(2)
            # 看下一行是不是斜体（caption）
            caption = ""
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                cap_match = re.match(r'[\*＿](.+?)[\*＿]', next_stripped)
                if cap_match:
                    caption = cap_match.group(1)
                    i += 1  # 跳过caption行
            img_html = f'<p {P_STYLE}><img alt="{alt}" src="{src}" />'
            if caption:
                img_html += f'<br/><em>{caption}</em>'
            img_html += '</p>'
            html_parts.append(img_html)
            i += 1
            continue

        # 参考资料行 (以"参考资料."开头)
        if stripped.startswith("参考资料."):
            content = process_inline(escape_html(stripped))
            html_parts.append(f'<p {REFS_P_STYLE}>{content}</p>')
            i += 1
            continue

        # 普通段落
        # 处理行内标记
        paragraph = process_inline(escape_html(stripped))
        html_parts.append(f'<p {P_STYLE}>{paragraph}</p>')
        i += 1

    return DIV_OPEN + "\n".join(html_parts) + "\n" + DIV_CLOSE


def main():
    print("=" * 60)
    print("📰 重新发布(呼吸感优化版): 桌面Agent大爆发")
    print("=" * 60)

    # 1. 读取 .md
    print("\n📖 读取更新后的文章...")
    md_text = MD_PATH.read_text(encoding="utf-8")
    frontmatter, body = parse_md(md_text)
    print(f"   全文: {len(body)} 字符")

    # 2. 检查 frontmatter
    cover_match = re.search(r'cover_media_id:\s*(\S+)', frontmatter)
    if cover_match:
        print(f"   封面 media_id: {cover_match.group(1)[:30]}...")

    # 3. 生成 HTML
    print("\n🎨 转换为设计师v3.1风格HTML...")
    html = convert_to_designer_html(body)
    print(f"   HTML: {len(html)} 字符")

    # 预览前200字
    preview = re.sub(r'<[^>]+>', '', html)[:150].replace('\n', ' ')
    print(f"   预览: {preview}...")

    # 4. 保存新HTML到文件备查
    html_path = MD_PATH.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"   ✅ HTML 已保存: {html_path}")

    # 5. 提取 digest
    body_clean = re.sub(r'<[^>]+>', '', html)
    digest = body_clean[:120].replace('\n', ' ').strip()
    print(f"   摘要: {digest}...")

    # 6. 获取 token
    print("\n🔑 获取 access_token...")
    token = get_ac_token(None, force_refresh=True)
    if not token:
        print("❌ 获取 token 失败")
        sys.exit(1)

    # 7. 更新草稿
    print(f"\n📝 更新草稿 (media_id: {OLD_DRAFT_MEDIA_ID[:30]}...)")
    body = {
        "media_id": OLD_DRAFT_MEDIA_ID,
        "index": 0,
        "articles": {
            "title": TITLE,
            "author": AUTHOR,
            "digest": digest,
            "content": html,
            "content_source_url": "",
            "thumb_media_id": THUMB_MEDIA_ID,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
            "show_cover_pic": 1,
        }
    }

    url = f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}"
    result = http_request(url, body, "POST")

    if "errcode" not in result or result["errcode"] == 0:
        print(f"✅ 草稿更新成功！")
        print(f"   标题: {TITLE}")
        print(f"   封面: 保持原图不变")
        print(f"   原草稿 media_id: {OLD_DRAFT_MEDIA_ID}")
        print(f"\n⏰ 请到微信后台确认草稿已更新，定时 20:00 发布")
    else:
        print(f"❌ 草稿更新失败: {json.dumps(result, ensure_ascii=False, indent=2)}")
        # 错误处理: media_id 失效则重新创建草稿
        if result.get("errcode") == 40007:
            print("\n⚠️  media_id 失效，尝试重新创建草稿...")
            url_add = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
            result2 = http_request(url_add, {
                "articles": [{
                    "title": TITLE,
                    "author": AUTHOR,
                    "digest": digest,
                    "content": html,
                    "content_source_url": "",
                    "thumb_media_id": THUMB_MEDIA_ID,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                    "show_cover_pic": 1,
                }]
            }, "POST")
            if "media_id" in result2:
                print(f"✅ 新草稿创建成功！media_id: {result2['media_id']}")
                print(f"\n⏰ 请到微信后台检查草稿箱，设置定时 20:00")
            else:
                print(f"❌ 重新创建失败: {json.dumps(result2, ensure_ascii=False)}")
                sys.exit(1)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
