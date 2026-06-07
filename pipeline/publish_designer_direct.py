#!/usr/bin/env python3
"""
直接从 designer 消息 payload 发布文章到微信草稿箱
接收参数：title, content(HTML), thumb_media_id, author
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from account_config import get_account, get_access_token as get_ac_token
from 发布历史_去重 import 记录发布成功


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


def main():
    title = sys.argv[1] if len(sys.argv) > 1 else ""
    html_content = sys.argv[2] if len(sys.argv) > 2 else ""
    thumb_media_id = sys.argv[3] if len(sys.argv) > 3 else ""

    if not title or not html_content or not thumb_media_id:
        print("用法: python3 publish_designer_direct.py <title> <html_file> <thumb_media_id>")
        sys.exit(1)

    # 如果第二个参数是文件路径，读取文件
    html_path = Path(html_content)
    if html_path.exists():
        html_content = html_path.read_text(encoding="utf-8")

    print("=" * 60)
    print(f"📤 发布 designer v3.1 改版文章")
    print(f"   标题: {title}")
    print(f"   HTML: {len(html_content)} 字符")
    print("=" * 60)

    # Digest
    import re
    body_clean = re.sub(r'<[^>]+>', '', html_content)
    digest = body_clean[:120].replace('\n', ' ').strip()

    token = get_ac_token(None, force_refresh=True)
    if not token:
        print("❌ 获取 access_token 失败")
        sys.exit(1)

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
            记录发布成功(标题=title, url="", 来源="微信自动发布(designer直接)", 摘要=digest)
        except Exception as e:
            print(f"   ⚠️ 记录失败: {e}")
        print("\n🎉 发布成功！请到后台草稿箱检查，设置定时 20:00")
        print(f"   media_id: {result['media_id']}")
        return result['media_id']
    else:
        print(f"❌ 失败: {json.dumps(result, ensure_ascii=False)}")
        return None


if __name__ == "__main__":
    main()
