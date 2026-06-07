#!/usr/bin/env python3
"""
专业配图设计模板 v2 — 根据文章内容自动匹配配图类型
支持：融资/产品/模型/安全/开源/通用 多场景
"""
import re
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
素材_DIR = BASE_DIR / "data" / "素材"


# ═══════════════════════════════
# 内容主题分类
# ═══════════════════════════════

def detect_topic(title, tags=""):
    """根据文章标题和标签判断配图类型"""
    text = (title + " " + tags).lower()
    
    topics = {
        "融资": ["融资","投资","估值","融","美元","亿元","募资","资本","投资人","估值","700亿","财务"],
        "产品": ["发布","新品","推出","上线","产品","版本","更新","研发","流程","策略","模式"],
        "模型": ["大模型","模型","参数","benchmark","评测","开源模型","LLM","参数","上下文","token"],
        "安全": ["安全","漏洞","泄露","攻击","风险","cve","数据泄露","暴露"],
        "开源": ["开源","开源项目","github","star","生态","社区","贡献"],
        "人才": ["入职","加入","离职","招人","人才","崔添翼","挂帅","领衔","加盟"],
        "职场": ["职场","裁员","就业","失业","出路","副业","考公","外包","程序员","面试","跳槽","薪资","35岁"],
        "vibe-coding": ["vibe coding","claude code","cursor","codex","ai编程","codi","windsurf","cline","opencode","氛围编程"],
        "ai-tools": ["ai工具","工具实测","工具评测","效率工具","开发工具","程序员工具","新工具推荐"],
        "agent-money": ["agent","变现","搞钱","副业","收入","赚钱","月入","一人公司","独立开发","接单","代写"],
        "pitfalls": ["踩坑","bug","报错","翻车","教训","部署失败","配置错误","排查","debug","降级","回滚"],
        "weekly": ["本周","周报","汇总","速递","机会","趋势","推荐项目","开源项目"],
    }
    
    scores = {}
    for topic, keywords in topics.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[topic] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "通用"


# ═══════════════════════════════
# 各主题配图生成器
# ═══════════════════════════════

def _make_html(template_name, html_content, viewport_w, viewport_h):
    """写入HTML文件并截图"""
    html_path = 素材_DIR / f"_{template_name}.html"
    html_path.write_text(html_content, encoding="utf-8")
    
    ts = datetime.now().strftime("%H%M%S")
    png_path = 素材_DIR / f"{template_name}_{ts}.png"
    
    subprocess.run([
        "npx", "playwright", "screenshot",
        f"file://{html_path.absolute()}",
        str(png_path),
        f"--viewport-size={viewport_w},{viewport_h}",
        "--wait-for-timeout=1500"
    ], capture_output=True, timeout=30)
    
    return str(png_path) if png_path.exists() else None


def _cover_dark_bold(title, tag=""):
    """暗夜大字报封面"""
    tag_line = f'<div class="tag">{tag}</div>' if tag else ''
    return _make_html("cover", f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1800px;height:766px;background:linear-gradient(160deg,#0B1120 0%,#1A1A2E 40%,#0D1B2A 100%);font-family:"PingFang SC","Microsoft YaHei",sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 400px;position:relative;overflow:hidden}}
body::before{{content:'';position:absolute;width:500px;height:500px;background:radial-gradient(circle,rgba(34,197,94,0.08) 0%,transparent 60%);top:-150px;right:-80px;border-radius:50%}}
body::after{{content:'';position:absolute;width:3px;height:160px;background:linear-gradient(to bottom,#22c55e,transparent);left:320px;top:50%;transform:translateY(-50%);border-radius:2px}}
.tag{{font-size:16px;color:#22c55e;font-weight:600;letter-spacing:3px;margin-bottom:14px}}
h1{{font-size:60px;color:#fff;font-weight:900;line-height:1.15;margin-bottom:14px;letter-spacing:-1px}}
h1 span{{background:linear-gradient(135deg,#22c55e,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.sub{{font-size:22px;color:#94a3b8;font-weight:400;line-height:1.4}}
.line{{width:100px;height:3px;background:#22c55e;border-radius:2px;margin:20px 0}}
.meta{{font-size:16px;color:#64748b}}
</style></head><body>
{tag_line}
<h1>{title}</h1>
<div class="line"></div>
<div class="meta">Python工作圈 · 2026</div>
</body></html>''', 1800, 766)


def _body_glassmorphism(title, items, tag="💡"):
    """玻璃拟态 — 数据显示卡（浅色版：灰白底+绿点缀，手机端优化）"""
    dots = ''
    for it in items:
        dots += f'''<div class="dot"><span class="icon">{it.get('icon','')}</span><div class="name">{it.get('name','')}</div><div class="desc">{it.get('desc','')}</div></div>\n'''
    return _make_html("body", f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:750px;height:1100px;background:linear-gradient(160deg,#F0FDF4 0%,#F8FAFC 40%,#ECFDF5 100%);font-family:"PingFang SC","Microsoft YaHei",sans-serif;display:flex;align-items:center;justify-content:center;padding:40px 50px;position:relative;overflow:hidden}}
body::before{{content:'';position:absolute;width:380px;height:380px;background:radial-gradient(circle,rgba(34,197,94,0.08) 0%,transparent 70%);top:-80px;right:-60px;border-radius:50%}}
body::after{{content:'';position:absolute;width:260px;height:260px;background:radial-gradient(circle,rgba(34,197,94,0.05) 0%,transparent 70%);bottom:-80px;left:-60px;border-radius:50%}}
.card{{position:relative;z-index:1;background:#ffffff;border-radius:28px;padding:56px 64px;width:100%;box-shadow:0 4px 24px rgba(0,0,0,0.06),0 1px 3px rgba(0,0,0,0.04);border:1px solid #e8f5e9}}
.tag{{display:inline-block;font-size:28px;color:#16a34a;font-weight:700;background:rgba(34,197,94,0.08);padding:10px 28px;border-radius:24px;margin-bottom:24px}}
h1{{font-size:52px;color:#1a1a2e;font-weight:800;line-height:1.2;margin-bottom:16px}}
.sub{{font-size:26px;color:#64748b;margin-bottom:30px}}
.dots{{display:flex;gap:20px;flex-wrap:wrap}}
.dot{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:20px;padding:32px 24px;flex:1;min-width:160px;text-align:center;transition:all 0.2s}}
.dot .icon{{font-size:56px;margin-bottom:14px;display:block}}
.dot .name{{font-size:36px;color:#1a1a2e;font-weight:700}}
.dot .desc{{font-size:26px;color:#64748b;margin-top:10px}}
</style></head><body><div class="card"><div class="tag">{tag}</div><h1>{title}</h1><div class="dots">{dots}</div></div></body></html>''', 750, 1100)


def _body_bento_grid(title, items):
    """Bento Grid — 信息卡片（手机端优化：750px画布）"""
    grid = ''
    for it in items:
        wide = ' card-wide' if it.get('wide') else ''
        num = f'<div class="num">{it["num"]}</div>' if it.get('num') else ''
        icon_html = f'<span class="icon">{it["icon"]}</span>' if it.get('icon') else ''
        name = it.get('name', '')
        desc = it.get('desc', '')
        grid += f'<div class="card{wide}">{icon_html}{num}<h3>{name}</h3><p>{desc}</p></div>\n'
    return _make_html("body", f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:750px;height:1100px;background:#FAFAFA;font-family:"PingFang SC","Microsoft YaHei",sans-serif;padding:48px 56px;display:flex;flex-direction:column;justify-content:center}}
h1{{font-size:52px;color:#1a1a2e;font-weight:800;margin-bottom:8px;line-height:1.2}}
.sub{{font-size:24px;color:#666;margin-bottom:36px}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}}
.card{{background:#fff;border-radius:20px;padding:32px 24px;box-shadow:0 2px 16px rgba(0,0,0,0.06);border:1px solid #f0f0f0}}
.card-wide{{grid-column:span 2}}
.card .icon{{font-size:48px;margin-bottom:14px;display:block}}
.card h3{{font-size:32px;color:#1a1a2e;font-weight:700;margin-bottom:6px}}
.card p{{font-size:24px;color:#888;line-height:1.5}}
.card .num{{font-size:80px;font-weight:800;color:#22c55e;margin-bottom:2px;line-height:1}}
</style></head><body><h1>{title}</h1><div class="grid">{grid}</div></body></html>''', 750, 1100)


def _body_dashboard(title, items):
    """数据仪表盘 — 适合Benchmark/对比"""
    bars = ''
    for it in items:
        pct = it.get('pct', 50)
        color = it.get('color', '#22c55e')
        bars += f'''<div class="bar-group"><div class="bar-label">{it.get('label','')}</div><div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div><div class="bar-value">{it.get('value','')}</div></div>\n'''
    cards = ''
    for it in (items or [])[:3]:
        cards += f'''<div class="stat-card"><div class="label">{it.get('label2','')}</div><div class="value">{it.get('value2','')}</div></div>\n'''
    return _make_html("body", f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1440px;height:1080px;background:linear-gradient(180deg,#0F172A 0%,#1E293B 100%);font-family:"PingFang SC","Microsoft YaHei",sans-serif;padding:60px 80px;display:flex;flex-direction:column;justify-content:center}}
h1{{font-size:40px;color:#fff;font-weight:800;margin-bottom:30px;text-align:center}}
h1 span{{color:#22c55e}}
.chart{{display:flex;gap:20px;margin-bottom:30px;justify-content:center;flex-wrap:wrap}}
.bar-group{{flex:1;min-width:200px;text-align:center}}
.bar-label{{color:#94a3b8;font-size:16px;margin-bottom:6px}}
.bar-track{{height:14px;background:rgba(255,255,255,0.06);border-radius:7px;overflow:hidden;margin-bottom:4px}}
.bar-fill{{height:100%;border-radius:7px;transition:width 0.5s}}
.bar-value{{color:#fff;font-size:28px;font-weight:700}}
.stats{{display:flex;gap:16px}}
.stat-card{{flex:1;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:24px;text-align:center}}
.stat-card .label{{color:#94a3b8;font-size:16px;margin-bottom:4px}}
.stat-card .value{{color:#22c55e;font-size:32px;font-weight:800}}
</style></head><body><h1>{title}</h1><div class="chart">{bars}</div><div class="stats">{cards}</div></body></html>''', 1440, 1080)


# ═══════════════════════════════
# 主题 → 配图映射
# ═══════════════════════════════

def _make_topic_images(topic, title):
    """根据主题类型生成2张正文配图"""
    images = []
    
    if topic == "融资":
        # 融资类 → 金额数据图 + 投资人阵容图
        i1 = _body_glassmorphism("融资规模", [
            {"icon":"💰","name":"700亿元","desc":"中国科技初创首轮融资纪录"},
            {"icon":"🏢","name":"投前估值","desc":"450亿美元/3065亿元"},
            {"icon":"👤","name":"梁文锋注资","desc":"个人出资约200亿元"},
        ], tag="💰 融资数据")
        if i1: images.append(i1)
        
        i2 = _body_bento_grid("投资方阵容", [
            {"icon":"🇨🇳","num":"100亿+","name":"国家队领投","desc":"国家AI产业投资基金","wide":True},
            {"icon":"💎","num":"确定","name":"腾讯/IDG","desc":"接近确定参投"},
            {"icon":"🤝","num":"洽谈中","name":"网易/京东","desc":"在洽谈中"},
        ])
        if i2: images.append(i2)
    
    elif topic == "产品":
        i1 = _body_glassmorphism("核心亮点", [
            {"icon":"🚀","name":"新功能","desc":"产品核心能力"},
            {"icon":"⚡","name":"性能提升","desc":"具体数据"},
            {"icon":"🎯","name":"目标用户","desc":"使用场景"},
        ], tag="🔥 产品发布")
        if i1: images.append(i1)
        i2 = _body_bento_grid("功能对比", [
            {"icon":"✅","num":"新","name":"新版本","desc":"新增功能","wide":True},
            {"icon":"❌","num":"旧","name":"旧版本","desc":"已有功能"},
            {"icon":"➕","num":"+","name":"升级","desc":"改进项"},
        ])
        if i2: images.append(i2)
    
    elif topic == "模型":
        i1 = _body_dashboard("Benchmark 表现", [
            {"label":"SWE-bench","value":"80.6%","pct":81,"color":"#22c55e"},
            {"label":"Vibe Code","value":"49.9%","pct":50,"color":"#4ade80"},
            {"label":"性价比","value":"1/17x","pct":90,"color":"#e2b714"},
        ])
        if i1: images.append(i1)
        i2 = _body_glassmorphism("模型参数", [
            {"icon":"🧠","name":"1.6万亿","desc":"参数量"},
            {"icon":"📏","name":"1M Token","desc":"上下文窗口"},
            {"icon":"💰","name":"开源免费","desc":"MIT协议"},
        ], tag="⚡ 技术规格")
        if i2: images.append(i2)
    
    elif topic == "安全":
        i1 = _body_glassmorphism("⚠️ Claude Code 安全事件", [
            {"icon":"🔴","name":"Claude Code v2.1.0以下","desc":"130+版本带洞运行"},
            {"icon":"📊","name":"CVSS 7.7","desc":"settings.json 持久化后门"},
            {"icon":"🕐","name":"隐瞒5个月","desc":"零公告·零通知·$100赏金"},
        ], tag="⚠️ 沙箱漏洞")
        if i1: images.append(i1)
        i2 = _body_bento_grid("🛡️ 立即自查", [
            {"icon":"⬆️","num":"v2.1","name":"升级版本","desc":"立即升级到最新版","wide":True},
            {"icon":"🔍","num":"检查","name":"验证沙箱","desc":"allowedDomains 是否生效"},
            {"icon":"📋","num":"审计","name":"网络出口","desc":"监控异常外连流量"},
        ])
        if i2: images.append(i2)
    
    elif topic == "开源":
        i1 = _body_glassmorphism("开源生态", [
            {"icon":"⭐","name":"Stars","desc":"GitHub星标"},
            {"icon":"🔀","name":"Forks","desc":"分支数"},
            {"icon":"👥","name":"Contributors","desc":"贡献者"},
        ], tag="🌐 开源社区")
        if i1: images.append(i1)
        i2 = _body_bento_grid("社区动态", [
            {"icon":"📈","num":"活跃","name":"近期更新","desc":"最新Release","wide":True},
            {"icon":"💬","num":"讨论","name":"社区声音","desc":"开发者反馈"},
            {"icon":"🔗","num":"依赖","name":"生态项目","desc":"相关工具链"},
        ])
        if i2: images.append(i2)
    
    elif topic == "人才":
        i1 = _body_glassmorphism("核心团队", [
            {"icon":"👤","name":"领军人物","desc":"背景与履历"},
            {"icon":"🏆","name":"成就","desc":"关键成果"},
            {"icon":"🎯","name":"新方向","desc":"负责领域"},
        ], tag="🤝 人才动态")
        if i1: images.append(i1)
        i2 = _body_bento_grid("团队构成", [
            {"icon":"📋","num":"多人","name":"核心成员","desc":"关键岗位","wide":True},
            {"icon":"🔍","num":"招募中","name":"开放职位","desc":"正在招聘"},
            {"icon":"🏢","num":"前东家","name":"背景","desc":"来自知名公司"},
        ])
        if i2: images.append(i2)
    
    elif topic == "职场":
        i1 = _body_glassmorphism("📊 2026 Q1 程序员就业数据", [
            {"icon":"📉","name":"8万人被裁","desc":"全球科技行业Q1裁员"},
            {"icon":"🤖","name":"50% AI替代","desc":"非业务收缩，直接取代"},
            {"icon":"📈","name":"340%增长","desc":"同比2025年裁员增幅"},
        ], tag="📊 就业冲击")
        if i1: images.append(i1)
        i2 = _body_bento_grid("🧭 程序员三条出路对比", [
            {"icon":"🏛️","num":"1","name":"考公上岸","desc":"退休待遇4倍·双非难上岸"},
            {"icon":"🌏","num":"2","name":"出海找活","desc":"降薪30-50%·不卷不996"},
            {"icon":"🔧","num":"3","name":"外包+AI","desc":"1人干3人活·赚2人钱"},
        ])
        if i2: images.append(i2)

    elif topic == "vibe-coding":
        i1 = _body_glassmorphism("🛠️ AI编程工具实测", [
            {"icon":"⚡","name":"效率提升","desc":"具体场景的实测数据"},
            {"icon":"🐛","name":"踩坑记录","desc":"版本/配置/报错细节"},
            {"icon":"💡","name":"最佳实践","desc":"经过验证的工作流"},
        ], tag="🛠️ Vibe Coding")
        if i1: images.append(i1)
        i2 = _body_bento_grid("🔧 工具对比", [
            {"icon":"🤖","num":"Claude","name":"Claude Code","desc":"强项与短板","wide":True},
            {"icon":"🖱️","num":"Cursor","name":"Cursor","desc":"适用场景"},
            {"icon":"📟","num":"Codex","name":"Codex CLI","desc":"终端体验"},
        ])
        if i2: images.append(i2)

    elif topic == "ai-tools":
        i1 = _body_glassmorphism("🔍 深度解剖", [
            {"icon":"💰","name":"价格","desc":"月付vs年付vs免费"},
            {"icon":"✅","name":"能用","desc":"真正用上的功能"},
            {"icon":"❌","name":"鸡肋","desc":"宣传了但用不上的"},
        ], tag="🔍 工具解剖")
        if i1: images.append(i1)
        i2 = _body_bento_grid("⚔️ 竞品对比", [
            {"icon":"🥇","num":"优势","name":"赢了什么","desc":"核心差异点","wide":True},
            {"icon":"🥈","num":"短板","name":"输在哪","desc":"致命缺陷"},
            {"icon":"🎯","num":"适合","name":"谁该买","desc":"目标用户画像"},
        ])
        if i2: images.append(i2)

    elif topic == "agent-money":
        i1 = _body_glassmorphism("💰 变现数据拆解", [
            {"icon":"📊","name":"表面收入","desc":"网上吹的数字"},
            {"icon":"💸","name":"真实成本","desc":"API费/服务器/获客"},
            {"icon":"📉","name":"净利润","desc":"实际到手的钱"},
        ], tag="💰 搞钱拆解")
        if i1: images.append(i1)
        i2 = _body_bento_grid("🔄 可复制性分析", [
            {"icon":"✅","num":"可复制","name":"技术门槛","desc":"需要什么技能","wide":True},
            {"icon":"⚠️","num":"卡点","name":"最大障碍","desc":"不是技术问题"},
            {"icon":"📈","num":"天花板","name":"收入上限","desc":"月入多少封顶"},
        ])
        if i2: images.append(i2)

    elif topic == "pitfalls":
        i1 = _body_glassmorphism("🐛 踩坑时间线", [
            {"icon":"🕐","name":"发现","desc":"怎么发现的问题"},
            {"icon":"🔍","name":"排查","desc":"花了多久排查"},
            {"icon":"✅","name":"修复","desc":"最终解决方案"},
        ], tag="🐛 踩坑复盘")
        if i1: images.append(i1)
        i2 = _body_bento_grid("🧠 教训总结", [
            {"icon":"🚫","num":"别犯","name":"低级错误","desc":"最容易踩的坑","wide":True},
            {"icon":"💡","num":"经验","name":"早知道就好了","desc":"提前该做什么"},
            {"icon":"📋","num":"检查","name":"自查清单","desc":"避免踩同样的坑"},
        ])
        if i2: images.append(i2)

    elif topic == "weekly":
        i1 = _body_glassmorphism("🔥 本周热门", [
            {"icon":"⭐","name":"Star榜","desc":"GitHub涨星最快"},
            {"icon":"🆕","name":"新发布","desc":"本周新上线的工具"},
            {"icon":"📈","name":"趋势","desc":"值得关注的方向"},
        ], tag="📅 每周速递")
        if i1: images.append(i1)
        i2 = _body_bento_grid("📋 本周精选", [
            {"icon":"🥇","num":"TOP1","name":"最值得看","desc":"本周最佳项目","wide":True},
            {"icon":"🥈","num":"潜力","name":"关注","desc":"有增长空间"},
            {"icon":"🚫","num":"避坑","name":"别看","desc":"浪费时间"},
        ])
        if i2: images.append(i2)
    
    else:
        # 通用 → 概念图 + 数据图
        i1 = _body_glassmorphism("核心要点", [
            {"icon":"📊","name":"数据","desc":"关键数字"},
            {"icon":"🎯","name":"影响","desc":"行业影响"},
            {"icon":"💡","name":"洞察","desc":"深度分析"},
        ], tag="💡 深度")
        if i1: images.append(i1)
        i2 = _body_bento_grid("关键信息", [
            {"icon":"📌","num":"1","name":"要点一","desc":"核心发现","wide":True},
            {"icon":"📌","num":"2","name":"要点二","desc":"延伸分析"},
            {"icon":"📌","num":"3","name":"要点三","desc":"趋势判断"},
        ])
        if i2: images.append(i2)
    
    return images


# ═══════════════════════════════
# 对外接口
# ═══════════════════════════════

def generate_images_for_article(article_path):
    """为文章生成全套配图（封面+2张正文），主题自动匹配"""
    content = Path(article_path).read_text(encoding="utf-8")
    
    # 提取标题和标签
    title = ""
    tags = ""
    m = re.search(r"^title:\s*(.+?)\s*$", content, re.M)
    if m: title = m.group(1)
    m = re.search(r"^tags:\s*\[(.+?)\]", content, re.M)
    if m: tags = m.group(1)
    if not title:
        for line in content.split("\n")[:5]:
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()
                break
    if not title:
        title = Path(article_path).stem.replace("文章_", "")
    
    # 检测主题
    topic = detect_topic(title, tags)
    print(f"  🏷️ 主题识别: {topic}")
    
    # 封面（暗夜大字报）
    cover = _cover_dark_bold(title[:15] + ('…' if len(title) > 15 else ''), tag=f"⚡ {topic}")
    print(f"  🖼️ 封面: {topic}风格")
    
    # 正文配图（主题相关）
    body = _make_topic_images(topic, title)
    print(f"  🖼️ 正文图: {len(body)} 张 ({topic}专题)")
    
    return {"cover": cover, "body": body}
