#!/usr/bin/env python3
"""
创作阶段封面生成器 — Plan A 核心脚本
用法：python generate_article_covers.py 创作/文章_xxx.md [创作/文章_yyy.md ...]
      python generate_article_covers.py --all           # 扫描创作/中未生成封面的文章
      python generate_article_covers.py --all --pro      # 使用专业设计模板
      python generate_article_covers.py 文章.md --pro    # 单篇使用专业模板

流程：
1. 读取文章 → 调用 huashu_images.generate_images_for_article()
2. Playwright 截图生成封面 + 正文配图（本地 PNG）
3. 上传封面 → material/add_material → media_id
4. 上传正文图 → media/uploadimg → mmbiz.qpic.cn URL
5. 回写 frontmatter：cover_media_id + body_image_urls
6. 输出 JSON 摘要
"""
import json
import re
import sys
import io
from pathlib import Path
from datetime import datetime

import requests

# 项目根
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 导入各模块
import importlib.util

spec = importlib.util.spec_from_file_location("publish_v3", str(BASE_DIR / "publish_v3.py"))
publish_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_v3)

spec_h = importlib.util.spec_from_file_location("huashu_images", str(BASE_DIR / "huashu_images.py"))
huashu = importlib.util.module_from_spec(spec_h)
spec_h.loader.exec_module(huashu)

# ─── WeChat API ───
WECHAT_APP_ID = "wxb445d745c6038a3c"
WECHAT_APP_SECRET = "4e8e62cd319b58b323dee59d6ef1e4b3"

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}"
    resp = requests.get(url, timeout=15).json()
    if "access_token" in resp:
        return resp["access_token"]
    raise RuntimeError(f"Token获取失败: {resp}")

def upload_cover(access_token, img_path):
    """封面图 → material/add_material → media_id"""
    with open(img_path, "rb") as f:
        img_data = f.read()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    resp = requests.post(url, files={"media": ("cover.jpg", img_data, "image/jpeg")}, timeout=30).json()
    if "media_id" in resp:
        return resp["media_id"]
    # PIL fallback: 重新压缩
    from PIL import Image as PILImg
    img = PILImg.open(img_path).convert("RGB")
    # 微信封面推荐 1280x544 (2.35:1)
    img = img.resize((1280, 544), PILImg.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    resp2 = requests.post(url, files={"media": ("cover.jpg", buf.read(), "image/jpeg")}, timeout=30).json()
    if "media_id" in resp2:
        return resp2["media_id"]
    raise RuntimeError(f"封面上传失败: {resp} / {resp2}")

def upload_body_image(access_token, img_path):
    """正文图 → media/uploadimg → mmbiz.qpic.cn URL"""
    from PIL import Image as PILImg
    img = PILImg.open(img_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    resp = requests.post(url, files={"media": ("img.jpg", buf.read(), "image/jpeg")}, timeout=30).json()
    if "url" in resp:
        return resp["url"]
    raise RuntimeError(f"正文图片上传失败: {resp}")


# ─── 核心流程 ───
def generate_covers_for_article(article_path, access_token=None, pro=False):
    """
    为单篇文章生成封面 + 正文配图，上传微信，回写 frontmatter。
    pro=True 时使用 design_templates 专业风格（玻璃拟态/Bento Grid/暗夜大字报）
    返回: {"title": ..., "cover_media_id": ..., "body_urls": [...], "error": ...}
    """
    path = Path(article_path)
    if not path.exists():
        return {"error": f"文件不存在: {article_path}"}

    content = path.read_text(encoding="utf-8")

    # 提取标题
    title = ""
    for line in content.split("\n")[:5]:
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            break
    if not title:
        # frontmatter
        m = re.search(r"^title:\s*(.+?)\s*$", content, re.M)
        if m:
            title = m.group(1)
    if not title:
        title = path.stem.replace("文章_", "")

    print(f"🎨 生成配图: {title[:30]}...")

    # 1. 生成 HTML 封面 + 正文配图（本地 PNG）
    try:
        if pro:
            # 使用 design_templates 专业风格
            import design_templates as dt
            imgs = dt.generate_images_for_article(str(path))
            print(f"  ✨ 使用专业设计模板（暗夜大字报 + 玻璃拟态 + Bento Grid）")
        else:
            imgs = huashu.generate_images_for_article(str(path))
    except Exception as e:
        eng = "design_templates" if pro else "huashu_images"
        print(f"  ⚠️ {eng} 生成失败: {e}")
        return {"title": title, "error": f"{eng}: {e}"}

    cover_path = imgs.get("cover")
    body_paths = imgs.get("body", [])

    if not cover_path:
        print(f"  ⚠️ 封面生成失败（返回 None）")
        return {"title": title, "error": "huashu_images 返回 cover=None"}

    print(f"  ✅ 封面: {Path(cover_path).name}")
    print(f"  ✅ 正文配图: {len(body_paths)} 张")

    # 2. 上传微信
    if access_token is None:
        access_token = get_access_token()

    cover_media_id = None
    body_urls = []

    try:
        cover_media_id = upload_cover(access_token, cover_path)
        print(f"  📤 封面上传: {cover_media_id[:30]}...")
    except Exception as e:
        print(f"  ❌ 封面上传失败: {e}")
        return {"title": title, "cover_path": str(cover_path), "error": f"封面上传: {e}"}

    for i, bp in enumerate(body_paths):
        try:
            url = upload_body_image(access_token, bp)
            body_urls.append(url)
            print(f"  📤 正文图{i+1}: {url[:50]}...")
        except Exception as e:
            print(f"  ⚠️ 正文图{i+1}上传失败: {e}")

    # 3. 回写 frontmatter
    updated = update_frontmatter(content, cover_media_id, body_urls)
    path.write_text(updated, encoding="utf-8")
    print(f"  💾 frontmatter 已更新")

    return {
        "title": title,
        "cover_media_id": cover_media_id,
        "body_urls": body_urls,
        "article_path": str(path),
    }


def update_frontmatter(content, cover_media_id, body_urls):
    """在文章 frontmatter 中注入封面信息"""
    lines = content.split("\n")

    # 找到 frontmatter 结束位置（第二个 ---）
    fm_end = None
    fm_start = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break

    if fm_end is None:
        # 没有 frontmatter，创建一个
        return content

    # 构建要注入的字段
    new_fields = [f"cover_media_id: {cover_media_id}", "cover_source: huashu_html"]
    if body_urls:
        # YAML 数组格式
        new_fields.append("body_image_urls:")
        for url in body_urls:
            new_fields.append(f"  - {url}")

    # 替换原有的 cover: loremflickr URL（保留但注释掉用于参考）
    new_lines = []
    closing_fm_pos = None  # track the closing --- position
    for i, line in enumerate(lines):
        if i <= fm_start or i >= fm_end:
            new_lines.append(line)
            if i == fm_end:
                closing_fm_pos = len(new_lines) - 1
            continue
        # 在 frontmatter 内部
        if line.startswith("cover:") and "cover_media_id" not in line:
            # 保留原 cover 作为参考（注释掉）
            new_lines.append(f"# {line}  # replaced by cover_media_id below")
            continue
        if line.startswith("cover_media_id:") or line.startswith("cover_source:") or line.startswith("body_image_urls:"):
            continue  # 移除旧字段，后面重新注入
        new_lines.append(line)

    # 在前言闭合 --- 之前注入新字段
    if closing_fm_pos is None:
        closing_fm_pos = len(new_lines) - 1
    insert_pos = closing_fm_pos

    # 注入到 --- 之前
    for field in reversed(new_fields):
        new_lines.insert(insert_pos, field)

    return "\n".join(new_lines)


def scan_and_generate(创作_dir=None, today_only=False, pro=False):
    """扫描创作/目录，为所有未生成封面的文章生成封面"""
    if 创作_dir is None:
        创作_dir = BASE_DIR / "data" / "创作"
    else:
        创作_dir = Path(创作_dir)

    articles = sorted(创作_dir.glob("文章_*.md"))
    # 过滤：只处理当天 + 未生成封面的
    today_str = datetime.now().strftime("%Y%m%d")
    pending = []
    for a in articles:
        if today_only and today_str not in a.name:
            continue
        content = a.read_text(encoding="utf-8")
        if "cover_media_id:" not in content:
            pending.append(a)

    if not pending:
        print("✅ 所有文章已有封面，无需生成")
        return []

    print(f"🎨 找到 {len(pending)} 篇待生成封面的文章")
    access_token = get_access_token()
    print(f"✅ Token 获取成功")
    if pro:
        print("✨ 专业设计模式已启用（暗夜大字报 + 玻璃拟态 + Bento Grid）")

    results = []
    for p in pending:
        result = generate_covers_for_article(str(p), access_token, pro=pro)
        results.append(result)
        print()

    # 汇总
    success = sum(1 for r in results if "cover_media_id" in r)
    failed = sum(1 for r in results if "error" in r)
    print(f"\n{'='*60}")
    print(f"📊 汇总: {success} 成功 / {failed} 失败 / {len(results)} 总计")
    return results


# ─── CLI ───
if __name__ == "__main__":
    # 解析 --pro 参数
    argv = [x for x in sys.argv if x != '--pro']
    pro_mode = '--pro' in sys.argv
    
    if len(argv) < 2 or argv[1] == "--all":
        results = scan_and_generate(today_only=True, pro=pro_mode)
    elif argv[1] == "--all-history":
        results = scan_and_generate(today_only=False, pro=pro_mode)
    else:
        articles = argv[1:]
        access_token = get_access_token()
        print(f"✅ Token 获取成功")
        if pro_mode:
            print("✨ 专业设计模式已启用（暗夜大字报封面 + 玻璃拟态/Bento Grid 正文配图）")
        results = []
        for a in articles:
            result = generate_covers_for_article(a, access_token, pro=pro_mode)
            results.append(result)
            print()
        success = sum(1 for r in results if "cover_media_id" in r)
        failed = sum(1 for r in results if "error" in r)
        print(f"\n📊 {success} 成功 / {failed} 失败 / {len(results)} 总计")

    # 输出 JSON 供下游使用
    print("\n" + json.dumps(results, ensure_ascii=False, indent=2))
