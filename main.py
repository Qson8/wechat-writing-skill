"""
微信公众号自动化发文 - 完整方案
流程：AI生成文章 → 自动渲染配图 → 上传封面图 → 推送草稿箱 → 手动发布
"""

import os
import re
import json
import requests
import schedule
import time
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# 加载 .env 文件
load_dotenv()

# ==================== 配置区 ====================
# 密钥从环境变量读取，请勿硬编码！
# 创建 .env 文件配置：
#   WECHAT_APP_ID=your_app_id
#   WECHAT_APP_SECRET=your_secret
WECHAT_APP_ID     = os.getenv("WECHAT_APP_ID")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET")
if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
    raise ValueError("请设置环境变量 WECHAT_APP_ID 和 WECHAT_APP_SECRET")

# 支持的模型配置
MODELS = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
    },
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3-flash-preview",
    },
}

# 当前启用的模型
ACTIVE_MODEL = os.getenv("ACTIVE_MODEL", "deepseek")


def list_available_models():
    """列出所有可用模型及配置状态"""
    print("\n📋 可用模型列表：")
    print("-" * 60)
    for name, config in MODELS.items():
        status = "✅ 已配置" if config.get("api_key") else "❌ 未配置 API Key"
        marker = "👉 " if name == ACTIVE_MODEL else "   "
        print(f"{marker}{name:12} | {config['model']:20} | {status}")
    print("-" * 60)
    print(f"当前启用: {ACTIVE_MODEL} ({MODELS[ACTIVE_MODEL]['model']})")
    print("切换模型: 设置环境变量 ACTIVE_MODEL=openai/deepseek/anthropic")
    print("配置 API Key: 设置对应环境变量 OPENAI_API_KEY / DEEPSEEK_API_KEY / ANTHROPIC_API_KEY")
    print()

# .pen 模板路径
PEN_TEMPLATE_PATH = os.getenv("PEN_TEMPLATE_PATH", "./post_image_templates.pen")

# 字体路径（自动适配系统）
import platform
if platform.system() == "Darwin":
    FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"
    FONT_REG  = "/System/Library/Fonts/STHeiti Light.ttc"
else:
    FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
    FONT_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# 写作风格 skill 路径（优先读文件，没有则用内置默认）
SKILL_WRITE_PATH = os.getenv("SKILL_WRITE_PATH", "./SKILL_write.md")


def get_ai_client():
    """获取当前启用的 AI 客户端"""
    config = MODELS.get(ACTIVE_MODEL)
    if not config or not config.get("api_key"):
        raise ValueError(f"模型 {ACTIVE_MODEL} 未配置 API Key，请设置环境变量")
    
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    return client, config["model"]


def _load_system_prompt():
    if os.path.exists(SKILL_WRITE_PATH):
        with open(SKILL_WRITE_PATH) as f:
            return f.read()
    return """
你是一个专注于轻创业、程序员、独立开发和AI领域的公众号作者。
写作风格：大白话，真实感，适度制造焦虑但给出路，口语化，段落简短。
严格按以下格式输出：
【标题】
内容

【开头引言钩子】
内容（18-22字）

【摘要】
内容（110-120字）

【正文】
内容

【结尾问句互动钩子】
内容（18-22字）
"""

SYSTEM_PROMPT = _load_system_prompt()
# ================================================


# ────────────────────────────────────────────────
# 图片渲染工具函数
# ────────────────────────────────────────────────

BG, DARK2, ACCENT = "#0f172a", "#1e293b", "#6366f1"
WHITE, GRAY, GREEN, RED = "#ffffff", "#94a3b8", "#22c55e", "#ef4444"

def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    c = _hex2rgb(fill)
    draw.rectangle([x0+radius, y0, x1-radius, y1], fill=c)
    draw.rectangle([x0, y0+radius, x1, y1-radius], fill=c)
    for ex, ey in [(x0,y0),(x1-radius*2,y0),(x0,y1-radius*2),(x1-radius*2,y1-radius*2)]:
        draw.ellipse([ex, ey, ex+radius*2, ey+radius*2], fill=c)

def _centered(draw, text, font, x, y, w, color):
    lw = draw.textlength(text, font=font)
    draw.text((x+(w-lw)//2, y), text, font=font, fill=_hex2rgb(color))

def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur+ch, font=font) > max_w:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines


def render_cover(title: str, subtitle: str, output_path: str, template_path: str = None):
    """基于 .pen 模板渲染封面图（1200x675）"""
    W, H, PAD = 1200, 675, 60
    tpl_nodes = {}
    if template_path and os.path.exists(template_path):
        with open(template_path) as f:
            tpl = json.load(f)
        tpl_nodes = {n["id"]: n for n in tpl.get("nodes", [])}

    img  = Image.new("RGB", (W, H), _hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    for i in range(8):
        draw.rectangle([0, i*2, W//3, i*2+2], fill=(99,102,241))
    for i in range(3):
        r = 60+i*40
        draw.ellipse([W-r*2+20, H-r*2+20, W+20, H+20], outline=(99,102,241), width=2)

    f_t = ImageFont.truetype(FONT_BOLD, tpl_nodes.get("title",{}).get("fontSize", 52))
    f_s = ImageFont.truetype(FONT_REG,  tpl_nodes.get("subtitle",{}).get("fontSize", 28))

    tl = _wrap(draw, title,    f_t, W-PAD*2)
    sl = _wrap(draw, subtitle, f_s, W-PAD*2)
    total_h = len(tl)*64 + 24 + len(sl)*36
    y = (H-total_h)//2

    for line in tl:
        lw = draw.textlength(line, font=f_t)
        draw.text(((W-lw)//2, y), line, font=f_t, fill=_hex2rgb(WHITE)); y += 64
    y += 24
    for line in sl:
        lw = draw.textlength(line, font=f_s)
        draw.text(((W-lw)//2, y), line, font=f_s, fill=_hex2rgb(GRAY)); y += 36

    draw.rectangle([60, H-8, W-60, H-4], fill=_hex2rgb(ACCENT))
    img.save(output_path)
    print(f"✅ 封面图渲染完成")


def render_comparison(headers, rows, chart_title: str, output_path: str):
    """渲染框架对比表"""
    W  = 1200
    H  = 110 + 72*(len(rows)+1) + 80
    img  = Image.new("RGB", (W, H), _hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    f_t    = ImageFont.truetype(FONT_BOLD, 40)
    f_h    = ImageFont.truetype(FONT_BOLD, 26)
    f_cell = ImageFont.truetype(FONT_REG,  24)
    f_note = ImageFont.truetype(FONT_REG,  20)

    _centered(draw, chart_title, f_t, 0, 30, W, WHITE)

    n = len(headers)
    col_w = [280] + [(W-340)//(n-1)]*(n-1)
    col_x = [60]
    for w in col_w[:-1]: col_x.append(col_x[-1]+w)

    row_h, ty = 72, 100
    _draw_rounded_rect(draw, [col_x[0], ty, W-60, ty+row_h], 10, ACCENT)
    for h, x, w in zip(headers, col_x, col_w):
        _centered(draw, h, f_h, x, ty+20, w, WHITE)

    for ri, row in enumerate(rows):
        y = ty+row_h*(ri+1)
        draw.rectangle([col_x[0], y, W-60, y+row_h], fill=_hex2rgb(DARK2 if ri%2==0 else BG))
        for ci, (cell, x, w) in enumerate(zip(row, col_x, col_w)):
            color = GREEN if cell=="✓" else RED if cell=="✗" else ACCENT if ci==n-1 else GRAY if ci==0 else WHITE
            _centered(draw, cell, f_cell, x, y+22, w, color)

    note = f"* {headers[-1]} 综合表现最优"
    nw = draw.textlength(note, font=f_note)
    draw.text(((W-nw)//2, H-44), note, font=f_note, fill=_hex2rgb(GRAY))
    draw.rectangle([60, H-10, W-60, H-4], fill=_hex2rgb(ACCENT))
    img.save(output_path)
    print(f"✅ 对比表渲染完成")


def render_workflow(steps: list, chart_title: str, subtitle: str, output_path: str):
    """渲染流程图，steps = [("emoji", "标题", "描述\n第二行"), ...]"""
    W, H = 1200, 675
    img  = Image.new("RGB", (W, H), _hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    f_t    = ImageFont.truetype(FONT_BOLD, 40)
    f_sub  = ImageFont.truetype(FONT_REG,  22)
    f_num  = ImageFont.truetype(FONT_BOLD, 30)
    f_ct   = ImageFont.truetype(FONT_BOLD, 26)
    f_desc = ImageFont.truetype(FONT_REG,  22)
    f_note = ImageFont.truetype(FONT_REG,  20)

    _centered(draw, chart_title, f_t,   0, 36, W, WHITE)
    _centered(draw, subtitle,    f_sub, 0, 88, W, GRAY)

    n = len(steps)
    card_w, card_h = 200, 220
    gap = max(20, (W-120-n*card_w)//(n-1)) if n > 1 else 0
    sx  = (W - (n*card_w + (n-1)*gap)) // 2
    cy  = (H-card_h)//2 + 20

    for i, (_, title, desc) in enumerate(steps):
        x = sx + i*(card_w+gap)
        _draw_rounded_rect(draw, [x, cy, x+card_w, cy+card_h], 14, DARK2)
        if i == n//2:
            draw.rounded_rectangle([x-2, cy-2, x+card_w+2, cy+card_h+2],
                                    radius=14, outline=_hex2rgb(ACCENT), width=3)
        ccx, ccy = x+card_w//2, cy+36
        draw.ellipse([ccx-24, ccy-24, ccx+24, ccy+24], fill=_hex2rgb(ACCENT))
        nw = draw.textlength(str(i+1), font=f_num)
        draw.text((ccx-nw//2, ccy-16), str(i+1), font=f_num, fill=_hex2rgb(WHITE))
        tw = draw.textlength(title, font=f_ct)
        draw.text((x+(card_w-tw)//2, cy+76), title, font=f_ct, fill=_hex2rgb(WHITE))
        for li, line in enumerate(desc.split("\n")):
            lw = draw.textlength(line, font=f_desc)
            draw.text((x+(card_w-lw)//2, cy+120+li*32), line, font=f_desc, fill=_hex2rgb(GRAY))
        if i < n-1:
            ax = x+card_w+12; ay = cy+card_h//2
            draw.line([ax, ay, ax+gap-24, ay], fill=_hex2rgb(ACCENT), width=3)
            draw.polygon([(ax+gap-24,ay-8),(ax+gap-10,ay),(ax+gap-24,ay+8)], fill=_hex2rgb(ACCENT))

    note = "安全保障：16 层独立安全机制 · WASM 沙箱隔离 · 消费步骤强制人工确认"
    nw = draw.textlength(note, font=f_note)
    draw.text(((W-nw)//2, H-48), note, font=f_note, fill=_hex2rgb(GRAY))
    draw.rectangle([60, H-10, W-60, H-4], fill=_hex2rgb(ACCENT))
    img.save(output_path)
    print(f"✅ 流程图渲染完成")


# ────────────────────────────────────────────────
# 微信 API
# ────────────────────────────────────────────────

def get_access_token() -> str:
    url    = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": WECHAT_APP_ID, "secret": WECHAT_APP_SECRET}
    data   = requests.get(url, params=params).json()
    if "access_token" in data:
        print("✅ access_token 获取成功")
        return data["access_token"]
    raise Exception(f"获取 access_token 失败: {data}")


def upload_image(access_token: str, image_path: str) -> str:
    url  = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(image_path, "rb") as f:
        data = requests.post(url, files={"media": f}).json()
    print(f"📤 上传图片返回: {data}")
    if "media_id" in data:
        print(f"✅ 图片上传成功：{os.path.basename(image_path)}")
        return data["media_id"]
    raise Exception(f"上传图片失败: {data}")


def markdown_to_wechat_html(text: str) -> str:
    html = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        elif line.startswith("## "):
            html.append(f'<h2 style="font-size:18px;font-weight:bold;margin:20px 0 10px;">{line[3:]}</h2>')
        elif line.startswith("### "):
            html.append(f'<h3 style="font-size:16px;font-weight:bold;margin:15px 0 8px;">{line[4:]}</h3>')
        elif line.startswith(("- ","* ")):
            html.append(f'<p style="margin:5px 0;padding-left:1em;">• {line[2:]}</p>')
        else:
            html.append(f'<p style="margin:10px 0;line-height:1.8;font-size:16px;">{line}</p>')
    return "\n".join(html)


def clean_title(title):
    """清理标题中的隐藏字符"""
    invalid_chars = ['\n', '\t', '\r', '　', '\u200b', '\u3000']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title.strip()

def check_wechat_title(title):
    """限制标题在32字以内"""
    if title is None:
        return ""
    if '\\u' in title:
        title = title.encode('utf-8').decode('unicode-escape')
    title = clean_title(title)
    while len(title) > 32:
        title = title[:-1]
    return title

def check_wechat_digest(digest):
    """限制摘要在64字以内"""
    if digest is None:
        return ""
    if '\\u' in digest:
        digest = digest.encode('utf-8').decode('unicode-escape')
    while len(digest) > 64:
        digest = digest[:-1]
    return digest

def push_to_draft(access_token: str, title: str, content: str, thumb_media_id: str, digest: str = ""):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    title = check_wechat_title(title)
    digest = check_wechat_digest(digest)
    
    # 检查并处理 Unicode 转义
    if content and '\\u' in content:
        print("⚠️ 检测到content中有Unicode转义！正在解码...")
        content = content.encode('utf-8').decode('unicode-escape')
    
    # 检查并处理 Unicode 转义
    if content and '\\u' in content:
        content = content.encode('utf-8').decode('unicode-escape')
    if digest and '\\u' in digest:
        digest = digest.encode('utf-8').decode('unicode-escape')
    if title and '\\u' in title:
        title = title.encode('utf-8').decode('unicode-escape')
    
    # 发送 payload
    payload = {"articles": [{"title": title, "digest": digest, "content": content,
                              "thumb_media_id": thumb_media_id, "need_open_comment": 1}]}
    # 使用 data 参数发送 UTF-8 编码的 JSON，避免乱码
    json_str = json.dumps(payload, ensure_ascii=False)
    data = requests.post(url, data=json_str.encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'}).json()
    if "media_id" in data:
        print("✅ 已推送草稿箱，请登录后台手动发布")
        return data["media_id"]
    raise Exception(f"推送草稿失败: {data}")


# ────────────────────────────────────────────────
# AI 生成文章
# ────────────────────────────────────────────────

def generate_article(topic: str) -> dict:
    client, model = get_ai_client()
    print(f"🤖 正在生成文章（{ACTIVE_MODEL}/{model}）：{topic}")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"请写一篇关于「{topic}」的公众号文章，严格按照输出格式"},
        ],
        temperature=0.8,
    )
    raw = resp.choices[0].message.content.strip()
    
    def extract(tag, text):
        m = re.search(rf"【{tag}】\s*\n(.*?)(?=\n【|\Z)", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    title  = extract("标题", raw)
    hook   = extract("开头引言钩子", raw)
    digest = extract("摘要", raw)
    body   = extract("正文", raw)
    cta    = extract("结尾问句互动钩子", raw)
    
    # 检查并解码 Unicode 转义
    if title and '\\u' in title:
        title = title.encode('utf-8').decode('unicode-escape')
    if digest and '\\u' in digest:
        digest = digest.encode('utf-8').decode('unicode-escape')
    if body and '\\u' in body:
        body = body.encode('utf-8').decode('unicode-escape')
    
    cover_sub = digest[:20]+"..." if len(digest) > 20 else digest

    print(f"✅ 文章生成完成：{title}")
    return dict(title=title, hook=hook, digest=digest, body=body, cta=cta, cover_subtitle=cover_sub)


def evaluate_article(article: dict) -> dict:
    """
    使用 SKILL_eval.md 规则对文章打分。
    调用 AI 模型进行评估，返回结构化评分数据。
    """
    eval_skill_path = os.path.join(os.path.dirname(__file__), "SKILL_eval.md")
    if not os.path.exists(eval_skill_path):
        print("⚠️  找不到 SKILL_eval.md，跳过评估")
        return {}

    with open(eval_skill_path, encoding="utf-8") as f:
        eval_skill = f.read()

    content = f"""请评估以下公众号文章，严格按照评分框架输出结构化结果。

标题：{article['title']}

开头引言钩子：{article['hook']}

摘要：{article['digest']}

正文：
{article['body']}

结尾互动钩子：{article['cta']}

请按以下格式输出（只输出这个格式，不要多余说明）：
标题得分: XX/20
开头得分: XX/20
正文得分: XX/30
语言得分: XX/20
结尾得分: XX/10
综合得分: XX/100
结论: [可以直接发/小改再发/需要大改/建议重写]
主要问题:
- 问题1
- 问题2
- 问题3
"""

    client, model = get_ai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": eval_skill},
            {"role": "user",   "content": content},
        ],
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()

    def parse_score(label, text):
        m = re.search(rf"{label}得分[：:]\s*(\d+)", text)
        return int(m.group(1)) if m else 0

    def parse_field(label, text):
        m = re.search(rf"{label}[：:]\s*(.+)", text)
        return m.group(1).strip() if m else ""

    issues = re.findall(r"^-\s+(.+)$", raw, re.MULTILINE)

    result = {
        "title_score":    parse_score("标题", raw),
        "hook_score":     parse_score("开头", raw),
        "body_score":     parse_score("正文", raw),
        "lang_score":     parse_score("语言", raw),
        "closing_score":  parse_score("结尾", raw),
        "total_score":    parse_score("综合", raw),
        "conclusion":     parse_field("结论", raw),
        "issues":         issues,
        "raw":            raw,
    }

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

    return result


# ────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────

def run(topic: str, comparison_data: dict = None, workflow_steps: list = None):
    """
    主流程：生成文章 → 评估打分（本地） → 渲染配图 → 上传 → 推草稿箱

    评分报告只在终端展示，不推入草稿箱。
    草稿箱只包含：封面图 + 引言钩子 + 正文 + 配图 + 结尾钩子。
    """
    list_available_models()
    print(f"\n{'='*50}\n🚀 开始处理：{topic}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}")

    tmpdir = tempfile.mkdtemp()
    try:
        token   = get_access_token()
        article = generate_article(topic)

        # ── 评估打分（仅本地，不进草稿箱）──
        # 评估由外层模型使用 SKILL_eval.md 规则进行
        # 此处只返回待评估内容，不做自动分数检查
        eval_result = evaluate_article(article)

        # ── 渲染并上传封面（进草稿箱）──
        cover_path = os.path.join(tmpdir, "cover.png")
        render_cover(article["title"], article["cover_subtitle"], cover_path, PEN_TEMPLATE_PATH)
        thumb_id = upload_image(token, cover_path)

        # ── 组装草稿箱正文 HTML（不含评分）──
        body_html  = f'<p style="color:#6366f1;font-weight:bold;font-size:15px;text-align:center;">{article["hook"]}</p>\n'
        body_html += markdown_to_wechat_html(article["body"])

        if comparison_data:
            comp_path = os.path.join(tmpdir, "comparison.png")
            render_comparison(comparison_data["headers"], comparison_data["rows"],
                              comparison_data.get("title","框架对比"), comp_path)
            comp_id    = upload_image(token, comp_path)
            body_html += f'\n<img src="" data-mediaId="{comp_id}" style="width:100%;" />'

        if workflow_steps:
            flow_path = os.path.join(tmpdir, "workflow.png")
            render_workflow(workflow_steps, "工作流程", "全程自动运行，无需人工介入", flow_path)
            flow_id    = upload_image(token, flow_path)
            body_html += f'\n<img src="" data-mediaId="{flow_id}" style="width:100%;" />'

        body_html += f'\n<p style="color:#94a3b8;font-size:15px;margin-top:32px;">{article["cta"]}</p>'

        # ── 推草稿箱 ──
        push_to_draft(token, article["title"], body_html, thumb_id, digest=article["digest"])
        print(f"\n🎉 完成！「{article['title']}」已进入草稿箱，等待手动发布。")

    except Exception as e:
        print(f"❌ 出错：{e}")
        raise


# ────────────────────────────────────────────────
# 定时任务（可选）
# ────────────────────────────────────────────────

TOPIC_LIST = [
    "独立开发第一步：怎么找到第一个付费用户",
    "用AI写代码，我踩过的5个坑",
    "订阅制产品为什么比买断更赚钱",
    "程序员副业：从0到月入5000的真实路径",
    "Claude和GPT到底哪个更适合写代码",
]

def scheduled_job():
    idx = int(time.time()/86400) % len(TOPIC_LIST)
    run(TOPIC_LIST[idx])

# schedule.every().day.at("09:00").do(scheduled_job)


# ────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────

if __name__ == "__main__":
    run(
        topic="刚开源2700 Star，这个Agent框架能让AI替你自动干活",
        comparison_data={
            "title": "三大 Agent 框架对比",
            "headers": ["对比项", "OpenClaw", "ZeroClaw", "OpenFang"],
            "rows": [
                ["内存占用",   "394 MB", "5 MB",  "~30 MB"],
                ["自主调度",   "✗",      "✗",     "✓"],
                ["安全层数",   "4 层",   "6 层",  "16 层"],
                ["支持LLM数",  "8+",     "6+",    "15+"],
                ["消息平台数", "3",      "4",     "9"],
                ["一键迁移",   "—",      "—",     "✓"],
            ],
        },
        workflow_steps=[
            ("🎯", "目标设定", "告诉Hand\n要做什么"),
            ("📋", "运行计划", "自动拆解\n执行步骤"),
            ("⚙️",  "工具调用", "调用权限内\n的工具执行"),
            ("📊", "结果汇报", "完成后推送\nDashboard"),
        ],
    )
