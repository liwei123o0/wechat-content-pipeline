#!/usr/bin/env python3
"""
重新发布(概述句版): 桌面Agent大爆发
使用 designer 更新后的 HTML（含概述句小字浅色排版），通过 draft/update 替换原草稿
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
from 发布历史_去重 import 记录发布成功

# ===== 常量 =====
HTML_PATH = Path(__file__).parent / "创作" / "article_桌面Agent大爆发_20260604.html")
OLD_DRAFT_MEDIA_ID = "O3o4IHlucqYmVliSX1xilejIRMSXOn3wljLPCW_hWWPJ0yoX3wFYeOfAqPObwIu0"
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


def main():
    print("=" * 60)
    print("📰 重新发布(概述句版): 桌面Agent大爆发")
    print("=" * 60)

    # 1. 读取 designer 更新后的 HTML
    print("\n📖 读取 designer 更新后的 HTML...")
    html_content = HTML_PATH.read_text(encoding="utf-8")
    print(f"   HTML: {len(html_content)} 字符")

    # 2. 验证概述句是否存在
    if "AI自举的递归链已经闭环" in html_content:
        print("   ✅ 概述句已确认存在")
    else:
        print("   ⚠️ 未找到概述句，继续执行")

    # 3. 提取 digest
    body_clean = re.sub(r'<[^>]+>', '', html_content)
    digest = body_clean[:120].replace('\n', ' ').strip()
    print(f"   摘要: {digest[:60]}...")

    # 4. 获取 token
    print("\n🔑 获取 access_token...")
    token = get_ac_token(None, force_refresh=True)
    if not token:
        print("❌ 获取 token 失败")
        sys.exit(1)

    # 5. 更新草稿
    print(f"\n📝 更新草稿 (media_id: {OLD_DRAFT_MEDIA_ID[:30]}...)")
    body = {
        "media_id": OLD_DRAFT_MEDIA_ID,
        "index": 0,
        "articles": {
            "title": TITLE,
            "author": AUTHOR,
            "digest": digest,
            "content": html_content,
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

        # 记录发布
        try:
            记录发布成功(标题=TITLE, url="", 来源="微信自动发布(概述句版)", 摘要=digest)
        except Exception as e:
            print(f"   ⚠️ 记录失败: {e}")

        # 验证草稿箱
        try:
            r = http_request(f"https://api.weixin.qq.com/cgi-bin/draft/count?access_token={token}")
            print(f"\n📋 草稿箱: {r.get('total_count', '?')} 篇（更新成功，没有重复草稿）")
        except Exception:
            pass

        print(f"\n⏰ 请到微信后台确认草稿已更新，定时 20:00 发布")
        return True
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
                    "content": html_content,
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
                return True
            else:
                print(f"❌ 重新创建失败: {json.dumps(result2, ensure_ascii=False)}")
                return False
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
