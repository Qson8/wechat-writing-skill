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
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# ==================== 配置区 ====================
WECHAT_APP_ID     = os.getenv("WECHAT_APP_ID", "你的AppID")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "你的AppSecret")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "你的OpenAI Key")

# .pen 模板路径
PEN_TEMPLATE_PATH = os.getenv("PEN_TEMPLATE_PATH", "./post_image_templates.pen")

# 字体路径
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# 写作风格 skill 路径（优先读文件，没有则用内置默认）
SKILL_WRITE_PATH = os.getenv("SKILL_WRITE_PATH", "./SKILL_write.md")

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


def push_to_draft(access_token: str, title: str, content: str, thumb_media_id: str, digest: str = ""):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    if not digest:
        digest = re.sub(r"<[^>]+>", "", content)[:54].strip() + "..."
    payload = {"articles": [{"title": title, "digest": digest, "content": content,
                              "thumb_media_id": thumb_media_id, "need_open_comment": 1}]}
    data = requests.post(url, json=payload).json()
    if "media_id" in data:
        print("✅ 已推送草稿箱，请登录后台手动发布")
        return data["media_id"]
    raise Exception(f"推送草稿失败: {data}")


# ────────────────────────────────────────────────
# AI 生成文章
# ────────────────────────────────────────────────

def generate_article(topic: str) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"🤖 正在生成文章：{topic}")
    resp = client.chat.completions.create(
        model="gpt-4o",
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
    cover_sub = digest[:20]+"..." if len(digest) > 20 else digest

    print(f"✅ 文章生成完成：{title}")
    return dict(title=title, hook=hook, digest=digest, body=body, cta=cta, cover_subtitle=cover_sub)


# ────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────

def run(topic: str, comparison_data: dict = None, workflow_steps: list = None):
    """
    主流程：生成文章 → 渲染配图 → 上传 → 推草稿箱

    comparison_data（可选）:
    {
        "title": "三大框架对比",
        "headers": ["对比项", "A", "B", "C"],
        "rows": [["内存", "394MB", "5MB", "30MB"], ...]
    }

    workflow_steps（可选）:
    [("🎯", "目标设定", "告诉Hand\n要做什么"), ...]
    """
    print(f"\n{'='*50}\n🚀 开始处理：{topic}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}")

    tmpdir = tempfile.mkdtemp()
    try:
        token   = get_access_token()
        article = generate_article(topic)

        # 渲染并上传封面
        cover_path = os.path.join(tmpdir, "cover.png")
        render_cover(article["title"], article["cover_subtitle"], cover_path, PEN_TEMPLATE_PATH)
        thumb_id = upload_image(token, cover_path)

        # 组装正文 HTML
        body_html = f'<p style="color:#6366f1;font-weight:bold;font-size:15px;text-align:center;">{article["hook"]}</p>\n'
        body_html += markdown_to_wechat_html(article["body"])

        # 渲染对比图（可选）
        if comparison_data:
            comp_path = os.path.join(tmpdir, "comparison.png")
            render_comparison(comparison_data["headers"], comparison_data["rows"],
                              comparison_data.get("title","框架对比"), comp_path)
            comp_id    = upload_image(token, comp_path)
            body_html += f'\n<img src="" data-mediaId="{comp_id}" style="width:100%;" />'

        # 渲染流程图（可选）
        if workflow_steps:
            flow_path = os.path.join(tmpdir, "workflow.png")
            render_workflow(workflow_steps, "工作流程", "全程自动运行，无需人工介入", flow_path)
            flow_id    = upload_image(token, flow_path)
            body_html += f'\n<img src="" data-mediaId="{flow_id}" style="width:100%;" />'

        # 结尾钩子
        body_html += f'\n<p style="color:#94a3b8;font-size:15px;margin-top:32px;">{article["cta"]}</p>'

        # 推草稿箱
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
