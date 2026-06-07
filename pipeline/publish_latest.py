#!/usr/bin/env python3
"""
微信公众号发布工具 v3.0 - 修复正文图片端点 + Markdown HTML 转换
"""
import json, sys, os, requests, re, io
from pathlib import Path
from datetime import datetime
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("publish", str(Path(__file__).parent / "publish_v3.py"))
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)

spec2 = importlib.util.spec_from_file_location("dedup", str(Path(__file__).parent / "发布历史_去重.py"))
dedup = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(dedup)

# ===== 🔑 关键：两个不同的微信图片上传端点 =====
def 上传正文图片(access_token, img_data_bytes):
    """正文配图 → uploadimg 端点 → 返回 mmbiz.qpic.cn URL（可显示）"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    resp = requests.post(url, files={'media': ('img.jpg', img_data_bytes, 'image/jpeg')}, timeout=30)
    result = resp.json()
    return result.get('url')

def 上传封面图(access_token, img_data_bytes):
    """封面图 → add_material 端点 → 返回 media_id（给 thumb_media_id）"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    resp = requests.post(url, files={'media': ('cover.jpg', img_data_bytes, 'image/jpeg')}, timeout=30)
    result = resp.json()
    return result.get('media_id')

def 提取新闻正文图片(news_url, max_images=3):
    """从新闻页面提取正文内的真实照片（多图）"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(news_url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        images = []
        
        # 1. 找 og:image
        og = re.search(r'''og:image["'][^>]*content=["']([^"']+)["']''', html)
        if og and og.group(1) not in images:
            images.append(og.group(1))
        
        # 2. 找文章正文里的 <img> 标签
        img_tags = re.findall(r'''<img[^>]+src=["'](https?://[^"']+\.(?:jpg|jpeg|png|webp)[^"']*)["']''', html, re.I)
        for img in img_tags:
            if img not in images and len(images) < max_images:
                # 过滤图标、logo 等小图
                if not any(x in img.lower() for x in ['icon', 'logo', 'avatar', 'favicon', '1x1', 'pixel']):
                    images.append(img)
        
        return images[:max_images]
    except Exception as e:
        return []

def 下载新闻图片并上传正文(news_url, access_token, max_images=3):
    """从新闻页面提取真实照片 → 下载 → 用 uploadimg 上传 → 返回 mmbiz.qpic.cn URL 列表"""
    img_urls = 提取新闻正文图片(news_url, max_images)
    if not img_urls:
        return []
    
    body_urls = []
    for i, img_url in enumerate(img_urls):
        try:
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            
            # 下载
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(img_url, headers=headers, timeout=15)
            
            # 用 uploadimg 端点上传（正文图片）
            upload_url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
            resp2 = requests.post(upload_url, files={'media': (f'img{i}.jpg', resp.content, 'image/jpeg')}, timeout=30)
            result = resp2.json()
            
            if 'url' in result:
                body_urls.append(result['url'])
                print(f"  ✅ 新闻插图{i+1}: {result['url'][:50]}...")
        except Exception as e:
            print(f"  ⚠️ 图片{i+1}失败: {e}")
    
    return body_urls

def 下载并处理图片(img_url):
    """下载图片并处理成微信格式"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(img_url, headers=headers, timeout=15)
        img = Image.open(io.BytesIO(resp.content)).convert('RGB')
        target_w, target_h = 1280, 544
        ratio = target_w / img.width
        img = img.resize((target_w, int(img.height * ratio)), Image.LANCZOS)
        if img.height > target_h:
            img = img.crop((0, (img.height-target_h)//2, target_w, (img.height+target_h)//2))
        elif img.height < target_h:
            new = Image.new('RGB', (target_w, target_h), (255,255,255))
            new.paste(img, (0, (target_h-img.height)//2))
            img = new
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"  ⚠️ 图片处理失败: {e}")
        return None

def 插入正文配图(正文, access_token, 文章标题):
    """给正文插入配图（正文图用 uploadimg 端点）"""
    try:
        html = publish.markdown_to_html(正文)
        p_count = html.count('</p>')
        配图数量 = min(3, max(2, p_count // 4))
        if 配图数量 < 1:
            return html
        
        print(f"  🎨 生成 {配图数量} 张正文配图...")
        for i in range(配图数量):
            clean = re.sub(r'[^\w\u4e00-\u9fff]', '', 文章标题[:20])
            prompt = f"{clean} 相关的科技主题配图"
            
            # 生成图片数据
            img_bytes = publish.generate_cover_bytes(prompt)
            if not img_bytes:
                continue
            
            # ⚠️ 用 uploadimg 端点获取正确 URL
            img_url = 上传正文图片(access_token, img_bytes)
            if img_url:
                图注 = f"图{i+1}：{文章标题[:18]}..."
                img_html = f'''<p style="text-align:center;margin:30px 0;">
<img src="{img_url}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>
<br/><span style="color:#888;font-size:13px;">▲ {图注}</span></p>'''
                
                parts = html.split('</p>')
                pos = min(len(parts)-1, 3 + i*4)
                parts.insert(pos, img_html)
                html = '</p>'.join(parts)
                print(f"    ✅ 配图 {i+1} (mmbiz.qpic.cn URL)")
        return html
    except Exception as e:
        print(f"  ⚠️ 正文配图失败: {e}")
        return publish.markdown_to_html(正文)

def 读取最新选题():
    整理_dir = Path(__file__).parent / "data" / "整理"
    files = sorted(整理_dir.glob("选题_*.json"), reverse=True)
    if not files: return None
    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ 选题: {files[0].name}")
    return data.get('综合推荐', [])[:3]

def 检查文章是否已生成(选题标题):
    创作_dir = Path(__file__).parent / "data" / "创作"
    清理 = 选题标题.replace("8点1氪丨", "").replace("36氪首发", "")
    关键词列表 = [清理[:4], 清理.split("，")[0][:6], 清理.split("；")[0][:6]]
    for 特殊词 in ["小米", "宇树", "可灵", "贝壳", "Qwen", "千问", "大模型", "AI", "Token", "机甲", "数字员工", "客服"]:
        if 特殊词 in 清理: 关键词列表.append(特殊词)
    关键词列表 = list(set([k.replace(" ","").replace("：","") for k in 关键词列表 if len(k)>1]))
    
    best_match = None; best_score = -1
    for f in 创作_dir.glob("文章_*.md"):
        文件名 = f.name.replace("_","").replace(" ","")
        score = sum(1 for k in 关键词列表 if len(k)>1 and k in 文件名)
        if score > 0:
            import re
            m = re.search(r'(\d{8})', f.name)
            if m and m.group(1) == datetime.now().strftime('%Y%m%d'):
                score += 100  # 偏好今天
            if score > best_score:
                best_score = score; best_match = f
    return best_match

def 读取已生成文章(文章路径):
    with open(文章路径, encoding='utf-8') as f:
        content = f.read()
    title = 文章路径.stem.replace("文章_", "")
    for line in content.split('\n')[:5]:
        if line.strip().startswith('# '):
            title = line.strip()[2:].strip(); break
    return title, content

def 发布文章(标题, 正文, 原标题="", 原文URL="", html_cover=None, html_body=None):
    """发布到微信草稿箱（优先 HTML 渲染图，其次新闻照片，最后 AI 生成）"""
    try:
        access_token = publish.get_access_token()
        if not access_token: return False
        
        # === 封面图：HTML渲染 > 新闻原图 > AI生成 ===
        cover_bytes = None
        if html_cover and Path(html_cover).exists():
            print(f"  🎨 HTML封面: {Path(html_cover).name}")
            from PIL import Image as PILImg
            img = PILImg.open(html_cover).convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            cover_bytes = buf.read()
        
        if not cover_bytes and 原文URL and len(原文URL) > 10:
            cover_img_url = 提取新闻正文图片(原文URL, 1)
            if cover_img_url:
                print(f"  🔍 新闻封面: {cover_img_url[0][:60]}...")
                cover_bytes = 下载并处理图片(cover_img_url[0])
        
        if not cover_bytes:
            print(f"  🤖 AI生成封面...")
            cover_bytes = publish.generate_cover_bytes(标题)
        
        if not cover_bytes: return False
        thumb_media_id = 上传封面图(access_token, cover_bytes)
        if not thumb_media_id: return False
        
        # === 正文配图：HTML渲染 > 新闻照片 > AI生成 ===
        body_img_urls = []
        if html_body:
            print(f"  🎨 HTML正文图: {len(html_body)} 张")
            from PIL import Image as PILImg
            for img_path in html_body:
                if not Path(img_path).exists(): continue
                img = PILImg.open(img_path).convert('RGB')
                img = img.resize((720, int(720 * img.height / img.width)), PILImg.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                buf.seek(0)
                img_url = 上传正文图片(access_token, buf.read())
                if img_url:
                    body_img_urls.append(img_url)
                    print(f"    ✅ {img_url[:50]}...")
        
        if not body_img_urls and 原文URL:
            body_img_urls = 下载新闻图片并上传正文(原文URL, access_token, max_images=3)
        
        if body_img_urls:
            html_content = 插入指定配图到正文(正文, access_token, 标题, body_img_urls)
        else:
            html_content = 插入正文配图(正文, access_token, 标题)
        
        # === 发布 ===
        draft_data = {"articles": [{
            "title": 标题, "content": html_content,
            "thumb_media_id": thumb_media_id, "author": "Python工作圈"
        }]}
        data = json.dumps(draft_data, ensure_ascii=False).encode('utf-8')
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
        resp = requests.post(url, data=data, headers={'Content-Type': 'application/json'}, timeout=30)
        result = resp.json()
        
        if result.get('media_id'):
            print(f"  ✅ media_id: {result['media_id'][:30]}...")
            try: dedup.记录发布成功(标题, 原标题, 原文URL, "自动发布", 正文[:300])
            except: pass
            return True
        else:
            print(f"  ❌ {result}"); return False
    except Exception as e:
        print(f"  ❌ {e}"); return False

def 插入指定配图到正文(正文, access_token, 标题, img_urls):
    """将已有的图片 URL 插入正文适当位置"""
    html = publish.markdown_to_html(正文)
    图注_text = [f"图{i+1}：{标题[:18]}..." for i in range(len(img_urls))]
    
    for i, img_url in enumerate(img_urls):
        img_html = f'''<p style="text-align:center;margin:30px 0;">
<img src="{img_url}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>
<br/><span style="color:#888;font-size:13px;">▲ {图注_text[i]}</span></p>'''
        
        parts = html.split('</p>')
        pos = min(len(parts)-1, 3 + i*4)
        parts.insert(pos, img_html)
        html = '</p>'.join(parts)
    
    return html

def main():
    print("🚀 微信公众号发布工具 v3.1 (含 HTML 渲染配图)")
    print("="*60)
    
    # 尝试加载 HTML 配图模块
    try:
        import importlib.util
        spec_huashu = importlib.util.spec_from_file_location("huashu_images", str(Path(__file__).parent / "huashu_images.py"))
        huashu = importlib.util.module_from_spec(spec_huashu)
        spec_huashu.loader.exec_module(huashu)
        print("✅ HTML配图模块可用")
        html_images_enabled = True
    except Exception as e:
        print(f"⚠️ HTML配图模块不可用: {e}")
        html_images_enabled = False
    选题列表 = 读取最新选题()
    if not 选题列表: return 1
    
    待发布 = []
    for 选题 in 选题列表:
        选题标题 = 选题.get('标题', '')
        已生成 = 检查文章是否已生成(选题标题)
        if 已生成:
            t, body = 读取已生成文章(已生成)
            待发布.append({"标题":t, "正文":body, "原标题":选题标题, "原文URL":选题.get('链接',''), "文章路径":已生成})
            print(f"  ✅ {选题标题[:30]}...")
        else:
            print(f"  ⏳ {选题标题[:30]}...")
    
    if not 待发布:
        print("❌ 无已生成文章"); return 1
    
    # 为每篇文章生成 HTML 配图
    if html_images_enabled:
        print(f"\n🎨 生成 HTML 渲染配图...")
        for item in 待发布:
            try:
                imgs = huashu.generate_images_for_article(str(item["文章路径"]))
                item["html_cover"] = imgs.get("cover")
                item["html_body"] = imgs.get("body", [])
                if item["html_cover"]:
                    print(f"  ✅ {item['标题'][:20]}... 封面 + {len(item['html_body'])}张正文图")
            except Exception as e:
                print(f"  ⚠️ {item['标题'][:20]}...: {e}")
                item["html_cover"] = None
                item["html_body"] = []
    
    print(f"\n📤 发布 {len(待发布)} 篇...")
    ok = sum(1 for item in 待发布 if 发布文章(
        item["标题"], item["正文"], item["原标题"], item["原文URL"],
        html_cover=item.get("html_cover"), html_body=item.get("html_body", [])
    ))
    print(f"\n✅ 完成! {ok}/{len(待发布)} 篇")
    return 0

if __name__ == "__main__":
    exit(main())
