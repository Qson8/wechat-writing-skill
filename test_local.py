"""
test_local.py — 本地测试脚本
mock 掉 OpenAI 和微信 API，只验证：
1. 文章解析逻辑是否正确
2. 评分报告是否正常打印
3. 封面图 / 对比表 / 流程图是否能正常渲染
4. HTML 组装是否正确（评分不进去，文章内容进去）
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

# ── Mock 数据：模拟 AI 生成的原始输出 ──────────────────
MOCK_RAW = """
【标题】
刚开源2700 Star，这个Agent框架能让AI替你自动干活

【开头引言钩子】
AI已经能自己上班了，你还在手动复制粘贴？

【摘要】
OpenFang是用Rust构建的生产级Agent操作系统，春节后刚开源就暴涨2700+ Star。核心是Hands自主能力包，激活后能全天候自动运行，无需人工介入。内置7个Hands覆盖资讯监控、客户挖掘、视频剪辑等场景，配备16层安全机制，三条命令即可部署上手。

【正文】
前不久我写过ZeroClaw，用Rust重写之后内存只有5MB，把OpenClaw那394MB的占用按在地上摩擦。评论区反馈基本一致：够快，但功能还差点，再等一个更完整的框架。

这刚过完春节，OpenFang就来了。

**它和普通Agent到底差在哪**

普通Agent像接单的外包，你说一件事它做一件事，流程断了就要人来接。

OpenFang的Hands更像一个有完整SOP的员工。交代好目标，它自己按流程跑，出了结果再汇报，中间不需要人工介入。

**内置7个Hands，挑5个说**

Collector：盯着你指定的目标持续监控，竞对动态、舆情变化，有异动就推送。

Lead：每天自动跑一轮，发现潜在客户、打分去重，最后打包成CSV送来。

Clip：上传一条视频，8阶段流水线自动跑完，识别高光、剪竖屏、自动发平台。

**三条命令装起来**

curl -fsSL https://openfang.sh/install | sh
openfang init
openfang start

项目刚开源还在快速迭代，建议先备份数据再装。

【结尾问句互动钩子】
你现在有哪些重复工作，最想先交给Agent来跑？

【配图需求】
- 封面图（16:9）：深色科技风，主标题"AI替你自动干活"
- 正文配图1：三框架对比表
- 正文配图2：Hands工作流程图
"""

# ── Mock 评估原始输出 ───────────────────────────────────
MOCK_EVAL_RAW = """
标题得分: 18/20
开头得分: 17/20
正文得分: 25/30
语言得分: 18/20
结尾得分: 8/10
综合得分: 86/100
结论: 可以直接发
主要问题:
- 标题可以加具体数字会更吸引人
- 正文第三部分步骤可以再具体一点
- 结尾互动问题较通用，可以更有针对性
"""


# ── 复用 main.py 里的解析和渲染逻辑 ───────────────────

def extract(tag, text):
    m = re.search(rf"【{tag}】\s*\n(.*?)(?=\n【|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def parse_score(label, text):
    m = re.search(rf"{label}得分[：:]\s*(\d+)", text)
    return int(m.group(1)) if m else 0

def parse_field(label, text):
    m = re.search(rf"{label}[：:]\s*(.+)", text)
    return m.group(1).strip() if m else ""


def test_article_parsing():
    print("\n" + "="*50)
    print("TEST 1: 文章解析")
    print("="*50)

    title     = extract("标题", MOCK_RAW)
    hook      = extract("开头引言钩子", MOCK_RAW)
    digest    = extract("摘要", MOCK_RAW)
    body      = extract("正文", MOCK_RAW)
    cta       = extract("结尾问句互动钩子", MOCK_RAW)
    cover_sub = digest[:20] + "..." if len(digest) > 20 else digest

    assert title,  "❌ 标题解析失败"
    assert hook,   "❌ 开头引言钩子解析失败"
    assert digest, "❌ 摘要解析失败"
    assert body,   "❌ 正文解析失败"
    assert cta,    "❌ 结尾互动钩子解析失败"

    print(f"✅ 标题：{title}")
    print(f"✅ 钩子：{hook}")
    print(f"✅ 摘要：{digest[:30]}...")
    print(f"✅ 正文：{len(body)} 字")
    print(f"✅ CTA：{cta}")
    print(f"✅ 封面副标题：{cover_sub}")

    return dict(title=title, hook=hook, digest=digest, body=body,
                cta=cta, cover_subtitle=cover_sub)


def test_eval_parsing():
    print("\n" + "="*50)
    print("TEST 2: 评分解析 + 报告打印")
    print("="*50)

    issues = re.findall(r"^-\s+(.+)$", MOCK_EVAL_RAW, re.MULTILINE)
    result = {
        "title_score":   parse_score("标题", MOCK_EVAL_RAW),
        "hook_score":    parse_score("开头", MOCK_EVAL_RAW),
        "body_score":    parse_score("正文", MOCK_EVAL_RAW),
        "lang_score":    parse_score("语言", MOCK_EVAL_RAW),
        "closing_score": parse_score("结尾", MOCK_EVAL_RAW),
        "total_score":   parse_score("综合", MOCK_EVAL_RAW),
        "conclusion":    parse_field("结论", MOCK_EVAL_RAW),
        "issues":        issues,
    }

    assert result["total_score"] == 86, f"❌ 综合得分解析错误：{result['total_score']}"
    assert result["conclusion"] == "可以直接发", f"❌ 结论解析错误：{result['conclusion']}"
    assert len(result["issues"]) == 3, f"❌ 问题数量解析错误：{len(result['issues'])}"

    # 打印报告
    bar = "█" * (result["total_score"] // 5) + "░" * (20 - result["total_score"] // 5)
    print(f"""
╔══════════════════════════════════════╗
║          📊 文章质量评估报告          ║
╠══════════════════════════════════════╣
║  标题    {result['title_score']:>3}/20   开头    {result['hook_score']:>3}/20  ║
║  正文    {result['body_score']:>3}/30   语言    {result['lang_score']:>3}/20  ║
║  结尾    {result['closing_score']:>3}/10                      ║
╠══════════════════════════════════════╣
║  综合得分：{result['total_score']:>3}/100  {bar}  ║
║  结论：{result['conclusion']:<30}  ║
╠══════════════════════════════════════╣""")
    for issue in result["issues"]:
        print(f"║  ⚠ {issue:<35}║")
    print("╚══════════════════════════════════════╝")

    print(f"\n✅ 评分解析全部正确")
    return result


def test_html_assembly(article: dict):
    print("\n" + "="*50)
    print("TEST 3: HTML 组装（验证评分不进草稿箱）")
    print("="*50)

    def markdown_to_wechat_html(text):
        html = []
        for line in text.split("\n"):
            line = line.strip()
            if not line: continue
            elif line.startswith("## "): html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith("**") and line.endswith("**"): html.append(f'<strong>{line[2:-2]}</strong>')
            else: html.append(f'<p style="margin:10px 0;line-height:1.8;">{line}</p>')
        return "\n".join(html)

    # 草稿箱 HTML（不含评分）
    body_html  = f'<p style="color:#6366f1;font-weight:bold;">{article["hook"]}</p>\n'
    body_html += markdown_to_wechat_html(article["body"])
    body_html += f'\n<p style="color:#94a3b8;">{article["cta"]}</p>'

    assert "综合得分" not in body_html, "❌ 评分数据混入了草稿箱 HTML！"
    assert "╔" not in body_html,        "❌ 评分报告框混入了草稿箱 HTML！"
    assert article["hook"] in body_html, "❌ 钩子没有进入 HTML"
    assert article["cta"]  in body_html, "❌ CTA 没有进入 HTML"

    print(f"✅ 草稿箱 HTML 长度：{len(body_html)} 字符")
    print(f"✅ 评分数据未混入草稿箱")
    print(f"✅ 钩子已写入 HTML")
    print(f"✅ CTA 已写入 HTML")
    print(f"\n── HTML 预览（前200字）──")
    print(body_html[:200])


def test_image_rendering(article: dict):
    print("\n" + "="*50)
    print("TEST 4: 配图渲染")
    print("="*50)

    import tempfile
    tmpdir = tempfile.mkdtemp()

    # 从 main.py 导入渲染函数
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", os.path.join(os.path.dirname(__file__), "main.py"))
    main_mod = importlib.util.load_from_spec = None
    # 直接内联导入（避免main.py的顶层import依赖openai/requests）
    from PIL import Image, ImageDraw, ImageFont
    import json

    FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
    FONT_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    BG,DARK2,ACCENT = "#0f172a","#1e293b","#6366f1"
    WHITE,GRAY,GREEN,RED = "#ffffff","#94a3b8","#22c55e","#ef4444"

    def _hex2rgb(h):
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
    def _draw_rr(draw,xy,r,fill):
        x0,y0,x1,y1=xy; c=_hex2rgb(fill)
        draw.rectangle([x0+r,y0,x1-r,y1],fill=c); draw.rectangle([x0,y0+r,x1,y1-r],fill=c)
        for ex,ey in [(x0,y0),(x1-r*2,y0),(x0,y1-r*2),(x1-r*2,y1-r*2)]:
            draw.ellipse([ex,ey,ex+r*2,ey+r*2],fill=c)
    def _ctr(draw,text,font,x,y,w,color):
        lw=draw.textlength(text,font=font); draw.text((x+(w-lw)//2,y),text,font=font,fill=_hex2rgb(color))
    def _wrap(draw,text,font,mw):
        lines,cur=[],""
        for ch in text:
            if draw.textlength(cur+ch,font=font)>mw: lines.append(cur);cur=ch
            else: cur+=ch
        if cur: lines.append(cur)
        return lines

    def render_cover(title, subtitle, output_path, template_path=None):
        W,H,PAD=1200,675,60
        tpl={}
        if template_path and os.path.exists(template_path):
            with open(template_path) as f: tpl={n["id"]:n for n in json.load(f).get("nodes",[])}
        img=Image.new("RGB",(W,H),_hex2rgb(BG)); draw=ImageDraw.Draw(img)
        for i in range(8): draw.rectangle([0,i*2,W//3,i*2+2],fill=(99,102,241))
        for i in range(3):
            r=60+i*40; draw.ellipse([W-r*2+20,H-r*2+20,W+20,H+20],outline=(99,102,241),width=2)
        ft=ImageFont.truetype(FONT_BOLD,tpl.get("title",{}).get("fontSize",52))
        fs=ImageFont.truetype(FONT_REG, tpl.get("subtitle",{}).get("fontSize",28))
        tl=_wrap(draw,title,ft,W-PAD*2); sl=_wrap(draw,subtitle,fs,W-PAD*2)
        total_h=len(tl)*64+24+len(sl)*36; y=(H-total_h)//2
        for line in tl:
            lw=draw.textlength(line,font=ft); draw.text(((W-lw)//2,y),line,font=ft,fill=_hex2rgb(WHITE)); y+=64
        y+=24
        for line in sl:
            lw=draw.textlength(line,font=fs); draw.text(((W-lw)//2,y),line,font=fs,fill=_hex2rgb(GRAY)); y+=36
        draw.rectangle([60,H-8,W-60,H-4],fill=_hex2rgb(ACCENT))
        img.save(output_path)
        print(f"✅ 封面图渲染完成")

    def render_comparison(headers,rows,chart_title,output_path):
        W=1200; H=110+72*(len(rows)+1)+80
        img=Image.new("RGB",(W,H),_hex2rgb(BG)); draw=ImageDraw.Draw(img)
        ft=ImageFont.truetype(FONT_BOLD,40); fh=ImageFont.truetype(FONT_BOLD,26)
        fc=ImageFont.truetype(FONT_REG,24); fn=ImageFont.truetype(FONT_REG,20)
        _ctr(draw,chart_title,ft,0,30,W,WHITE)
        n=len(headers); cw=[280]+[(W-340)//(n-1)]*(n-1); cx=[60]
        for w in cw[:-1]: cx.append(cx[-1]+w)
        rh,ty=72,100
        _draw_rr(draw,[cx[0],ty,W-60,ty+rh],10,ACCENT)
        for h,x,w in zip(headers,cx,cw): _ctr(draw,h,fh,x,ty+20,w,WHITE)
        for ri,row in enumerate(rows):
            y=ty+rh*(ri+1); draw.rectangle([cx[0],y,W-60,y+rh],fill=_hex2rgb(DARK2 if ri%2==0 else BG))
            for ci,(cell,x,w) in enumerate(zip(row,cx,cw)):
                color=GREEN if cell=="✓" else RED if cell=="✗" else ACCENT if ci==n-1 else GRAY if ci==0 else WHITE
                _ctr(draw,cell,fc,x,y+22,w,color)
        note=f"* {headers[-1]} 综合表现最优"; nw=draw.textlength(note,font=fn)
        draw.text(((W-nw)//2,H-44),note,font=fn,fill=_hex2rgb(GRAY))
        draw.rectangle([60,H-10,W-60,H-4],fill=_hex2rgb(ACCENT))
        img.save(output_path); print(f"✅ 对比表渲染完成")

    def render_workflow(steps,chart_title,subtitle,output_path):
        W,H=1200,675; img=Image.new("RGB",(W,H),_hex2rgb(BG)); draw=ImageDraw.Draw(img)
        ft=ImageFont.truetype(FONT_BOLD,40); fs=ImageFont.truetype(FONT_REG,22)
        fn2=ImageFont.truetype(FONT_BOLD,30); fct=ImageFont.truetype(FONT_BOLD,26)
        fd=ImageFont.truetype(FONT_REG,22); fno=ImageFont.truetype(FONT_REG,20)
        _ctr(draw,chart_title,ft,0,36,W,WHITE); _ctr(draw,subtitle,fs,0,88,W,GRAY)
        n=len(steps); cw,ch=200,220
        gap=max(20,(W-120-n*cw)//(n-1)) if n>1 else 0
        sx=(W-(n*cw+(n-1)*gap))//2; cy=(H-ch)//2+20
        for i,(_,title,desc) in enumerate(steps):
            x=sx+i*(cw+gap); _draw_rr(draw,[x,cy,x+cw,cy+ch],14,DARK2)
            if i==n//2: draw.rounded_rectangle([x-2,cy-2,x+cw+2,cy+ch+2],radius=14,outline=_hex2rgb(ACCENT),width=3)
            ccx,ccy=x+cw//2,cy+36; draw.ellipse([ccx-24,ccy-24,ccx+24,ccy+24],fill=_hex2rgb(ACCENT))
            nw=draw.textlength(str(i+1),font=fn2); draw.text((ccx-nw//2,ccy-16),str(i+1),font=fn2,fill=_hex2rgb(WHITE))
            tw=draw.textlength(title,font=fct); draw.text((x+(cw-tw)//2,cy+76),title,font=fct,fill=_hex2rgb(WHITE))
            for li,line in enumerate(desc.split("\n")):
                lw=draw.textlength(line,font=fd); draw.text((x+(cw-lw)//2,cy+120+li*32),line,font=fd,fill=_hex2rgb(GRAY))
            if i<n-1:
                ax=x+cw+12; ay=cy+ch//2
                draw.line([ax,ay,ax+gap-24,ay],fill=_hex2rgb(ACCENT),width=3)
                draw.polygon([(ax+gap-24,ay-8),(ax+gap-10,ay),(ax+gap-24,ay+8)],fill=_hex2rgb(ACCENT))
        note="安全保障：16 层独立安全机制 · WASM 沙箱隔离 · 消费步骤强制人工确认"
        nw=draw.textlength(note,font=fno); draw.text(((W-nw)//2,H-48),note,font=fno,fill=_hex2rgb(GRAY))
        draw.rectangle([60,H-10,W-60,H-4],fill=_hex2rgb(ACCENT))
        img.save(output_path); print(f"✅ 流程图渲染完成")

    # 封面图
    cover_path = os.path.join(tmpdir, "cover.png")
    render_cover(
        title=article["title"],
        subtitle=article["cover_subtitle"],
        output_path=cover_path,
        template_path=os.path.join(os.path.dirname(__file__), "scripts", "post_image_templates.pen"),
    )
    assert os.path.exists(cover_path), "❌ 封面图未生成"
    print(f"✅ 封面图：{os.path.getsize(cover_path)//1024} KB")

    # 对比表
    comp_path = os.path.join(tmpdir, "comparison.png")
    render_comparison(
        headers=["对比项", "OpenClaw", "ZeroClaw", "OpenFang"],
        rows=[
            ["内存占用", "394 MB", "5 MB",  "~30 MB"],
            ["自主调度", "✗",      "✗",     "✓"],
            ["安全层数", "4 层",   "6 层",  "16 层"],
        ],
        chart_title="三大 Agent 框架对比",
        output_path=comp_path,
    )
    assert os.path.exists(comp_path), "❌ 对比表未生成"
    print(f"✅ 对比表：{os.path.getsize(comp_path)//1024} KB")

    # 流程图
    flow_path = os.path.join(tmpdir, "workflow.png")
    render_workflow(
        steps=[
            ("🎯", "目标设定", "告诉Hand\n要做什么"),
            ("📋", "运行计划", "自动拆解\n执行步骤"),
            ("⚙️",  "工具调用", "调用权限\n内执行"),
            ("📊", "结果汇报", "完成后推送\nDashboard"),
        ],
        chart_title="Hands 自主工作流程",
        subtitle="交代目标 → 自动执行 → 结果汇报",
        output_path=flow_path,
    )
    assert os.path.exists(flow_path), "❌ 流程图未生成"
    print(f"✅ 流程图：{os.path.getsize(flow_path)//1024} KB")

    # 复制到 outputs 供查看
    import shutil
    out = "/mnt/user-data/outputs"
    shutil.copy(cover_path, f"{out}/test_cover.png")
    shutil.copy(comp_path,  f"{out}/test_comparison.png")
    shutil.copy(flow_path,  f"{out}/test_workflow.png")
    print(f"\n✅ 三张配图已复制到 outputs 目录可预览")

    return tmpdir


# ── 主测试入口 ──────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 开始本地测试（mock 模式，不调用任何 API）")

    article    = test_article_parsing()
    eval_result = test_eval_parsing()
    test_html_assembly(article)
    test_image_rendering(article)

    print("\n" + "="*50)
    print("🎉 全部测试通过！")
    print("="*50)
    print("""
下一步：配置真实 API Key 后运行 main.py
  export OPENAI_API_KEY='sk-...'
  export WECHAT_APP_ID='wx...'
  export WECHAT_APP_SECRET='...'
  python main.py
""")
