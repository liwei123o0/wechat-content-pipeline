#!/usr/bin/env python3
"""
文章发布前审核 — 去模板化版 v4.1
新增：虚假范围检测、过渡词频率、段落整齐度、极短段比例、主观表达密度
用法: python3 review_article.py 文章.md
返回: PASS / WARN / FAIL + 审核明细
"""
import re, sys, json, statistics
from pathlib import Path

def review(filepath):
    path = Path(filepath)
    if not path.exists():
        return {"verdict": "FAIL", "reason": f"文件不存在"}

    content = path.read_text(encoding="utf-8")
    body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    title = ""
    m = re.search(r"^title:\s*(.+?)\s*$", content, re.M)
    if m: title = m.group(1)

    # 检测是否已有配图
    has_cover = "cover_media_id:" in content
    has_body_images = bool(re.findall(r'body_image_urls:', content))

    dims = {}

    # ═══════════════════════════════════
    # 维度一：内容
    # ═══════════════════════════════════
    c_checks = []
    c_pass = True

    # 1. 字数
    tc = len(body.strip())
    ok = 1500 <= tc <= 3000
    c_checks.append({"name":"字数","status":"PASS" if ok else "WARN","detail":f"{tc}字（建议1500-3000）"})

    # 2. 开头质量
    first_200 = body.strip()[:200]
    first_line = body.strip().split('\n')[0] if body.strip() else ''
    
    sentences_in_first_200 = [s for s in re.split(r'[。！？\n]', first_200) if s.strip()]
    opener_ok = len(sentences_in_first_200) >= 1

    total_ci_count = len(re.findall(r'说句(得罪人|扎心)', body))
    if total_ci_count >= 5:
        opener_ok = False
        detail = f"❌ 「说句得罪人的话」出现{total_ci_count}次，过于频繁"
    else:
        if len(first_200) < 30:
            detail = "开头太短"
        elif not any(c in first_200 for c in ['？','！','。','\n']):
            detail = "开头没有断句，读者第一眼看不到有效信息"
        else:
            detail = "✅"
    
    c_checks.append({"name":"开头质量","status":"PASS" if opener_ok else "WARN" if total_ci_count<3 else "FAIL","detail":detail})
    if total_ci_count >= 5: c_pass = False

    # 2.5 禁止元标签
    meta_labels = ['开篇拍桌', '翻车分析', '核心分析', '争议点', '多方观点',
                   '互动钩子', '收尾留白', '冲击性开场', '冲击性判断',
                   '一、开篇', '二、翻车', '三、核心', '四、争议', '五、多方',
                   '六、互动', '七、收尾', '刺式写法', '话题驱动型']
    found_meta = [label for label in meta_labels if label in body]
    meta_ok = len(found_meta) == 0
    c_checks.append({"name":"禁止元标签","status":"PASS" if meta_ok else "FAIL",
                     "detail":"✅ 无" if meta_ok else f"❌ 发现: {', '.join(found_meta[:5])}"})
    if not meta_ok: c_pass = False

    # ═══════════════════════════════════
    # 3. AI味检测（扩充版 v4.1）
    # ═══════════════════════════════════
    ai_checks = []
    clean = re.sub(r'[#*>|`\[\]]', '', body)  # 去markdown符号，纯文字分析

    # 3a. 「最后说三句」检测
    has_last_three = bool(re.search(r'最后说三句', body))
    ai_checks.append(("最后说三句", has_last_three, "❌ 禁止出现的模板章节标题"))

    # 3b. ①②③编号结尾检测
    has_numbered_ending = bool(re.search(r'(①.*②.*③|❶.*❷.*❸)', body))
    ai_checks.append(("编号套路结尾", has_numbered_ending, "❌ ①②③编号结尾过于模板化"))

    # 3c. 选A/B/C检测
    has_abc = bool(re.search(r'选A.*选B.*选C', body))
    ai_checks.append(("选A/B/C", has_abc, "⚠️ 选A/B/C投票结尾已弃用"))

    # 3d. 「说句得罪人的话」过度使用
    if total_ci_count >= 3:
        ai_checks.append(("刺式话术过度", True, f"⚠️ 「说句得罪人的话」出现{total_ci_count}次，建议≤2次"))

    # 3e. 第一人称检测
    has_first_person = bool(re.search(r'[我咱]', body))
    if not has_first_person:
        ai_checks.append(("缺少第一人称", True, "❌ 全文无「我」，可能缺乏个人视角"))

    # 3f. 检测「欢迎评论区留言」
    has_welcome_comment = bool(re.search(r'欢迎.*(评论|留言)', body))
    if has_welcome_comment:
        ai_checks.append(("欢迎评论区留言", True, "❌ 「欢迎评论区留言」已禁止使用"))

    # 3g. 检测AI过渡词频率
    ai_buzzwords = {
        '值得注意的是': 1, '毋庸置疑': 1, '不言而喻': 1, '众所周知': 1, '值得一提的是': 1,
        '与此同时': 0.5, '综上所述': 1, '总的来说': 0.5, '不可否认': 1,
        '显而易见': 1, '换句话说': 0.5, '从某种意义上说': 1, '从这个角度来说': 0.5,
        '我们需要': 0.3, '我们应该': 0.3, '我们必须': 0.3,
    }
    found_buzz = {w: body.count(w) for w in ai_buzzwords}
    active_buzz = {w: c for w, c in found_buzz.items() if c > 0}
    buzz_score = sum(c * ai_buzzwords[w] for w, c in active_buzz.items())
    if buzz_score > 0:
        buzz_detail = "; ".join(f"{w}x{c}" for w, c in sorted(active_buzz.items(), key=lambda x: -x[1])[:5])
        limit = 2.0
        if buzz_score >= limit:
            ai_checks.append(("AI过渡词", True, f"❌ AI过渡词总计{buzz_score:.0f}分(阈值{limit})：{buzz_detail}"))
        elif buzz_score >= limit * 0.5:
            ai_checks.append(("AI过渡词", True, f"⚠️ AI过渡词{buzz_score:.0f}分：{buzz_detail}"))

    # 3h. 虚假范围检测「从X到Y」
    fake_range_count = len(re.findall(r'从[^。，；]{2,20}到[^。，；]{2,20}', clean))
    if fake_range_count >= 3:
        ai_checks.append(("「从X到Y」句式", True, f"⚠️ 发现{fake_range_count}处「从…到…」句式，AI常用虚假对比"))
    elif fake_range_count >= 1:
        ai_checks.append(("「从X到Y」句式", True, f"ℹ️ 有{fake_range_count}处「从…到…」，注意是否属于生硬对比"))

    # 3i. 段落整齐度检测
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip() 
                  and not p.startswith('>') and not p.startswith('|') 
                  and not p.startswith('#') and not p.startswith('```')]
    if len(paragraphs) >= 4:
        para_lengths = [len(p) for p in paragraphs]
        try:
            stdev = statistics.stdev(para_lengths)
            mean = statistics.mean(para_lengths)
            cv = stdev / mean if mean > 0 else 0  # 变异系数
            if cv < 0.35:
                ai_checks.append(("段落整齐度", True, f"⚠️ 段落长度变异系数{cv:.2f}(<0.35)，段落太整齐有AI味"))
            elif cv < 0.45:
                ai_checks.append(("段落整齐度", True, f"ℹ️ 段落长度变异系数{cv:.2f}，略偏整齐"))
        except:
            pass

    # 3j. 极短段比例
    if len(paragraphs) >= 4:
        short_paras = sum(1 for p in paragraphs if len(p) < 50)
        short_ratio = short_paras / len(paragraphs)
        if short_ratio < 0.1:
            ai_checks.append(("极短段比例", True, f"⚠️ 极短段仅{short_paras}/{len(paragraphs)}({short_ratio:.0%})，缺少节奏变化"))

    # 3k. 主观表达密度
    subjective_patterns = len(re.findall(r'(我觉得|我认为|我判断|我看|依我看|说白了|说实话|坦白说|我试过|我踩过|我发现|我做了|我花了|我用过|我写|我自己)', body))
    if subjective_patterns < 2:
        ai_checks.append(("主观表达", True, f"⚠️ 主观表达仅{subjective_patterns}处，文章偏客观报道，建议加入个人视角"))

    # 3l. 破折号频率检测（破折号已被视作AI标志）
    dash_count = body.count('——')
    if dash_count >= 3:
        ai_checks.append(("破折号过多", True, f"⚠️ 破折号{dash_count}个(阈值≤2)，建议减少"))
    elif dash_count >= 1:
        ai_checks.append(("破折号", True, f"ℹ️ 破折号{dash_count}个，注意控制"))

    # 3m. 「不是……而是……」句式检测
    bushi_count = len(re.findall(r'不是[^。，；]{3,30}而是', clean))
    if bushi_count >= 2:
        ai_checks.append(("「不是…而是…」", True, f"⚠️ 发现{bushi_count}处「不是…而是…」，AI常用对比句式，建议≤1处"))

    # 3n. 「想象一下」开头检测
    xiangxiang = bool(re.search(r'想象一下', clean[:200]))
    if xiangxiang:
        ai_checks.append(("「想象一下」开头", True, "❌ 「想象一下」是AI标志性废话开头"))
    
    # 3o. 行业黑话检测
    buzzwords_industry = ['赋能', '颠覆', '范式', '抓手', '闭环', '底层逻辑',
                          '颗粒度', '护城河', '重构', '破圈', '链路', '落地场景',
                          '组合拳', '方法论', '矩阵', '复用', '对齐']
    found_industry = [w for w in buzzwords_industry if w in body]
    if found_industry:
        ai_checks.append(("行业黑话", True, f"⚠️ 发现黑话: {', '.join(found_industry)}"))

    # 3p. 过渡词重复检测
    trans_words = ['此外', '然而', '因此', '所以', '但是', '不过', '另外', '同时']
    for tw in trans_words:
        cnt = body.count(tw)
        if cnt >= 3:
            ai_checks.append((f"过渡词「{tw}」重复", True, f"⚠️ 「{tw}」出现{cnt}次，建议仅用1次"))
            break  # 一个就够了

    # 汇总AI味检测
    ai_issues = [item for item in ai_checks if item[1]]
    has_fail = any("❌" in c[2] for c in ai_issues)
    has_warn = any("⚠️" in c[2] for c in ai_issues)
    
    if len(ai_issues) == 0:
        ai_pass = True
        ai_detail = "✅ 无明显AI味"
    elif has_fail:
        ai_pass = False
        fail_items = [c[2] for c in ai_issues if "❌" in c[2]]
        warn_items = [c[2] for c in ai_issues if "⚠️" in c[2]]
        ai_detail = "; ".join(fail_items[:3])
        if warn_items:
            ai_detail += "; " + "; ".join(warn_items[:2])
    elif has_warn:
        ai_pass = True
        warn_items = [c[2] for c in ai_issues if "⚠️" in c[2]]
        info_items = [c[2] for c in ai_issues if "ℹ️" in c[2]]
        ai_detail = "; ".join(warn_items[:3])
        if info_items:
            ai_detail += "; " + "; ".join(info_items[:2])
    else:
        ai_pass = True
        info_items = [c[2] for c in ai_issues if "ℹ️" in c[2]]
        ai_detail = "; ".join(info_items) if info_items else "✅ 无明显AI味"

    c_checks.append({"name":"AI味检测","status":"PASS" if ai_pass else "FAIL" if has_fail else "WARN","detail":ai_detail})
    if has_fail: c_pass = False

    # 4. 结尾完整性（宽松版）
    last_200 = body.strip()[-200:] if len(body.strip()) > 200 else body.strip()
    ending_ok = len(last_200) > 50
    c_checks.append({"name":"结尾完整性","status":"PASS" if ending_ok else "WARN","detail":"结尾过短" if not ending_ok else "✅"})
    
    # 观点明确度
    has_opinion = bool(re.search(r'(我觉得|我认为|我判断|我看|依我看|说白了|本质上)', body))
    if not has_opinion:
        has_opinion = bool(re.search(r'(因此|所以|结论|这意味着|这说明)', body))
    c_checks.append({"name":"观点明确度","status":"PASS" if has_opinion else "WARN","detail":"✅ 有明确观点" if has_opinion else "⚠️ 文章偏中性报道，缺乏个人判断"})

    dims["content"] = {"name":"📝 内容","pass":c_pass,"checks":c_checks}

    # ═══════════════════════════════════
    # 维度二：排版样式
    # ═══════════════════════════════════
    f_checks = []
    f_pass = True

    paras = [p.strip() for p in body.split('\n\n') if p.strip() and not p.startswith('>') and not p.startswith('|')]
    long_paras = sum(1 for p in paras if len(p) > 200)
    ok = long_paras < 3
    f_checks.append({"name":"段落长度","status":"PASS" if ok else "WARN","detail":f"{long_paras}段超200字" if long_paras else "适中"})

    has_h1 = bool(re.search(r'^# ', body, re.M))
    has_h2 = bool(re.search(r'^## ', body, re.M))
    has_h3 = bool(re.search(r'^### ', body, re.M))
    has_any_heading = has_h1 or has_h2 or has_h3
    ok = has_any_heading
    f_checks.append({"name":"标题层级","status":"PASS" if ok else "FAIL","detail":f"H1:{int(has_h1)} H2:{int(has_h2)} H3:{int(has_h3)}"})
    if not ok: f_pass = False

    has_table = bool(re.search(r'\|.+\|', body))
    has_quote = bool(re.search(r'^>', body, re.M))
    has_list = bool(re.search(r'^[*-] ', body, re.M))
    fmt_count = sum([has_table, has_quote, has_list])
    ok = fmt_count >= 2
    f_checks.append({"name":"排版丰富度","status":"PASS" if ok else "WARN","detail":f"表格|引用|列表: {fmt_count}/3"})

    ok = bool(re.search(r'\*\*', body))
    f_checks.append({"name":"加粗强调","status":"PASS" if ok else "WARN","detail":"有" if ok else "建议加粗关键数字"})

    lines = body.strip().split('\n')
    max_consec = 0; cur = 0
    for line in lines:
        if line.strip() and not line.startswith('#') and not line.startswith('>') and not line.startswith('|') and not line.startswith('*') and not line.startswith('-'):
            cur += 1; max_consec = max(max_consec, cur)
        else:
            cur = 0
    ok = max_consec <= 6
    f_checks.append({"name":"段落节奏","status":"PASS" if ok else "WARN","detail":f"连续{max_consec}行无断点（建议≤6）" if max_consec>6 else f"最大{max_consec}行"})

    dims["formatting"] = {"name":"🎨 排版","pass":f_pass,"checks":f_checks}

    # ═══════════════════════════════════
    # 维度三：配图/封面
    # ═══════════════════════════════════
    i_checks = []
    i_pass = True

    ok = has_cover
    i_checks.append({"name":"封面图","status":"PASS" if ok else "FAIL","detail":"有" if ok else "缺（需generate_article_covers --pro）"})
    if not ok: i_pass = False

    body_urls = re.findall(r'^\s+-\s+(http://mmbiz\.qpic\.cn/\S+)', content, re.M)
    img_count = len(body_urls)
    ok = img_count >= 2
    i_checks.append({"name":"正文配图","status":"PASS" if ok else "WARN" if img_count>=1 else "FAIL","detail":f"{img_count}张（建议≥2张）"})

    if body_urls:
        all_good = all('mmbiz.qpic.cn' in u for u in body_urls)
        i_checks.append({"name":"配图图床","status":"PASS" if all_good else "FAIL","detail":"微信图床" if all_good else "非微信图床"})
    else:
        i_checks.append({"name":"配图图床","status":"WARN","detail":"无配图"})

    source = re.search(r'cover_source:\s*(.+)', content)
    if source:
        src = source.group(1).strip()
        ok = src == "huashu_html"
        i_checks.append({"name":"封面来源","status":"PASS" if ok else "WARN","detail":f"{src}"})
    else:
        i_checks.append({"name":"封面来源","status":"WARN","detail":"未知"})

    dims["images"] = {"name":"🖼️ 配图","pass":i_pass,"checks":i_checks}

    # ═══════════════════════════════════
    # 综合判定
    # ═══════════════════════════════════
    all_pass = dims["content"]["pass"] and dims["formatting"]["pass"] and dims["images"]["pass"]
    verdict = "PASS" if all_pass else "FAIL"

    return {
        "verdict": verdict,
        "title": title,
        "file": path.name,
        "dims": dims,
    }


def print_report(r):
    v_icon = "✅" if r["verdict"] == "PASS" else "❌"
    print(f"\n{'='*55}")
    print(f"  {v_icon} {r['title'][:45]}")
    print(f"  📄 {r['file']}")
    print(f"  {'='*55}")

    for key, dim in r["dims"].items():
        d_icon = "✅" if dim["pass"] else "❌"
        print(f"\n  {d_icon} {dim['name']}")
        for c in dim["checks"]:
            ci = {"PASS":"✅","WARN":"🟡","FAIL":"❌"}[c["status"]]
            print(f"    {ci} {c['name']:12s} {c['detail'][:80]}")

    print(f"\n  {'─'*55}")
    if r["verdict"] == "PASS":
        print(f"  ✅ 审核通过，可以发布")
    else:
        fail_items = []
        for d in r["dims"].values():
            for c in d["checks"]:
                if c["status"] == "FAIL":
                    fail_items.append(f"{c['name']}: {c['detail'][:60]}")
        print(f"  ❌ 以下问题需要修改：")
        for item in fail_items:
            print(f"     - {item}")
    print()


if __name__ == "__main__":
    import glob
    files = sys.argv[1:] if len(sys.argv) > 1 else ["创作/文章_*.md"]
    all_pass = True
    for f in files:
        for path in sorted(glob.glob(f)):
            r = review(path)
            print_report(r)
            if r["verdict"] != "PASS":
                all_pass = False
    if not all_pass:
        print("⚠️ 部分文章未通过审核")
        sys.exit(1)
    else:
        print("✅ 全部通过")
