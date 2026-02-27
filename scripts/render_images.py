from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

BG       = "#0f172a"
ACCENT   = "#6366f1"
WHITE    = "#ffffff"
GRAY     = "#94a3b8"
DARK2    = "#1e293b"
GREEN    = "#22c55e"
RED      = "#ef4444"


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    fill = hex2rgb(fill)
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius*2, y0 + radius*2], fill=fill)
    draw.ellipse([x1 - radius*2, y0, x1, y0 + radius*2], fill=fill)
    draw.ellipse([x0, y1 - radius*2, x0 + radius*2, y1], fill=fill)
    draw.ellipse([x1 - radius*2, y1 - radius*2, x1, y1], fill=fill)


def centered_text(draw, text, font, x, y, w, color):
    lw = draw.textlength(text, font=font)
    draw.text((x + (w - lw) // 2, y), text, font=font, fill=hex2rgb(color))


# ── 配图1：三框架对比表 ────────────────────────────────────────────
def render_comparison(output_path):
    W, H = 1200, 720
    img = Image.new("RGB", (W, H), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    f_title  = ImageFont.truetype(FONT_BOLD, 40)
    f_head   = ImageFont.truetype(FONT_BOLD, 26)
    f_cell   = ImageFont.truetype(FONT_REG,  24)
    f_label  = ImageFont.truetype(FONT_REG,  20)

    # 标题
    title = "三大 Agent 框架对比"
    centered_text(draw, title, f_title, 0, 36, W, WHITE)

    # 表格数据
    headers = ["对比项", "OpenClaw", "ZeroClaw", "OpenFang"]
    rows = [
        ["内存占用",    "394 MB",  "5 MB",    "~30 MB"],
        ["自主调度",    "✗",       "✗",       "✓"],
        ["安全层数",    "4 层",    "6 层",     "16 层"],
        ["支持LLM数",   "8+",      "6+",       "15+"],
        ["消息平台数",  "3",       "4",        "9"],
        ["一键迁移",    "—",       "—",        "✓"],
    ]

    col_w   = [280, 240, 240, 240]
    col_x   = [60]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)

    row_h   = 72
    table_y = 110

    # 表头背景
    draw_rounded_rect(draw, [col_x[0], table_y, W - 60, table_y + row_h], 10, ACCENT)
    for i, (h, x, w) in enumerate(zip(headers, col_x, col_w)):
        centered_text(draw, h, f_head, x, table_y + 20, w, WHITE)

    # 数据行
    for ri, row in enumerate(rows):
        y = table_y + row_h * (ri + 1)
        bg = DARK2 if ri % 2 == 0 else BG
        draw.rectangle([col_x[0], y, W - 60, y + row_h], fill=hex2rgb(bg))

        for ci, (cell, x, w) in enumerate(zip(row, col_x, col_w)):
            if cell == "✓":
                color = GREEN
            elif cell == "✗":
                color = RED
            elif ci == 3:   # OpenFang列高亮
                color = ACCENT
            elif ci == 0:
                color = GRAY
            else:
                color = WHITE
            centered_text(draw, cell, f_cell, x, y + 22, w, color)

    # 底部说明
    note = "* OpenFang 在功能与性能之间取得平衡，自主调度能力目前唯一"
    nw = draw.textlength(note, font=f_label)
    draw.text(((W - nw) // 2, H - 48), note, font=f_label, fill=hex2rgb(GRAY))

    # 底部装饰线
    draw.rectangle([60, H - 12, W - 60, H - 6], fill=hex2rgb(ACCENT))

    img.save(output_path)
    print(f"✅ 对比表已生成：{output_path}")


# ── 配图2：Hands 工作流程闭环 ────────────────────────────────────
def render_workflow(output_path):
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    f_title = ImageFont.truetype(FONT_BOLD, 40)
    f_step  = ImageFont.truetype(FONT_BOLD, 30)
    f_desc  = ImageFont.truetype(FONT_REG,  22)

    centered_text(draw, "Hands 自主工作流程", f_title, 0, 36, W, WHITE)
    centered_text(draw, "交代目标 → 自动执行 → 结果汇报，全程无需人工介入", f_desc, 0, 90, W, GRAY)

    steps = [
        ("🎯", "目标设定",   "告诉 Hand\n要做什么"),
        ("📋", "运行计划",   "自动拆解\n执行步骤"),
        ("⚙️",  "工具调用",   "调用权限内\n的工具执行"),
        ("📊", "结果汇报",   "完成后推送\nDashboard"),
    ]

    card_w  = 200
    card_h  = 220
    gap     = 60
    total_w = len(steps) * card_w + (len(steps) - 1) * gap
    start_x = (W - total_w) // 2
    card_y  = (H - card_h) // 2 + 20

    for i, (icon, title, desc) in enumerate(steps):
        x = start_x + i * (card_w + gap)

        # 卡片背景
        draw_rounded_rect(draw, [x, card_y, x + card_w, card_y + card_h], 14, DARK2)

        # 高亮边框（当前选中感）
        if i == 2:
            draw.rounded_rectangle([x - 2, card_y - 2, x + card_w + 2, card_y + card_h + 2],
                                    radius=14, outline=hex2rgb(ACCENT), width=3)

        # 序号圆
        cx, cy = x + card_w // 2, card_y + 36
        draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=hex2rgb(ACCENT))
        num = str(i + 1)
        nw = draw.textlength(num, font=f_step)
        draw.text((cx - nw // 2, cy - 16), num, font=f_step, fill=hex2rgb(WHITE))

        # 标题
        f_card_title = ImageFont.truetype(FONT_BOLD, 26)
        tw = draw.textlength(title, font=f_card_title)
        draw.text((x + (card_w - tw) // 2, card_y + 76), title,
                  font=f_card_title, fill=hex2rgb(WHITE))

        # 描述（两行）
        for li, line in enumerate(desc.split("\n")):
            lw = draw.textlength(line, font=f_desc)
            draw.text((x + (card_w - lw) // 2, card_y + 120 + li * 32),
                      line, font=f_desc, fill=hex2rgb(GRAY))

        # 箭头
        if i < len(steps) - 1:
            ax = x + card_w + 12
            ay = card_y + card_h // 2
            draw.line([ax, ay, ax + gap - 24, ay], fill=hex2rgb(ACCENT), width=3)
            draw.polygon([(ax + gap - 24, ay - 8),
                          (ax + gap - 10, ay),
                          (ax + gap - 24, ay + 8)], fill=hex2rgb(ACCENT))

    # 底部说明
    note = "安全保障：16 层独立安全机制 · WASM 沙箱隔离 · 消费步骤强制人工确认"
    f_note = ImageFont.truetype(FONT_REG, 20)
    nw = draw.textlength(note, font=f_note)
    draw.text(((W - nw) // 2, H - 52), note, font=f_note, fill=hex2rgb(GRAY))
    draw.rectangle([60, H - 12, W - 60, H - 6], fill=hex2rgb(ACCENT))

    img.save(output_path)
    print(f"✅ 工作流程图已生成：{output_path}")


# ── 配图3：7个 Hands 功能卡片 ────────────────────────────────────
def render_hands_cards(output_path):
    W, H = 1200, 720
    img = Image.new("RGB", (W, H), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    f_title = ImageFont.truetype(FONT_BOLD, 40)
    f_name  = ImageFont.truetype(FONT_BOLD, 28)
    f_desc  = ImageFont.truetype(FONT_REG,  21)
    f_tag   = ImageFont.truetype(FONT_REG,  18)

    centered_text(draw, "OpenFang 内置 7 个 Hands", f_title, 0, 36, W, WHITE)

    hands = [
        ("Collector", "#6366f1", "持续监控",    "竞对动态/舆情变化\n异动推送+知识图谱"),
        ("Lead",      "#8b5cf6", "客户挖掘",    "自动发现潜在客户\n打分去重CSV输出"),
        ("Researcher","#06b6d4", "深度调研",    "多源交叉验证\n带引用研究报告"),
        ("Clip",      "#f59e0b", "视频剪辑",    "8阶段自动流水线\n识别高光自动发布"),
        ("Browser",   "#10b981", "网页自动化",  "自动点按填表\n消费步骤人工确认"),
        ("Scheduler", "#ec4899", "定时调度",    "按计划触发任务\n全天候自主运行"),
        ("Custom",    "#94a3b8", "自定义",      "写HAND.toml\n封装专属Hand"),
    ]

    card_w  = 260
    card_h  = 175
    cols    = 4
    gap_x   = 24
    gap_y   = 24
    start_x = (W - (cols * card_w + (cols - 1) * gap_x)) // 2
    start_y = 110

    for i, (name, color, tag, desc) in enumerate(hands):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        # 卡片背景
        draw_rounded_rect(draw, [x, y, x + card_w, y + card_h], 12, DARK2)

        # 左侧色条
        draw.rectangle([x, y + 20, x + 4, y + card_h - 20], fill=hex2rgb(color))

        # Hand 名称
        draw.text((x + 20, y + 18), name, font=f_name, fill=hex2rgb(color))

        # 标签胶囊
        tag_w = int(draw.textlength(tag, font=f_tag)) + 20
        draw_rounded_rect(draw, [x + 20, y + 58, x + 20 + tag_w, y + 84], 10, color)
        draw.text((x + 30, y + 61), tag, font=f_tag, fill=hex2rgb(WHITE))

        # 描述
        for li, line in enumerate(desc.split("\n")):
            draw.text((x + 20, y + 96 + li * 30), line, font=f_desc, fill=hex2rgb(GRAY))

    draw.rectangle([60, H - 12, W - 60, H - 6], fill=hex2rgb(ACCENT))

    img.save(output_path)
    print(f"✅ Hands卡片已生成：{output_path}")


if __name__ == "__main__":
    render_comparison("/mnt/user-data/outputs/img_comparison.png")
    render_workflow("/mnt/user-data/outputs/img_workflow.png")
    render_hands_cards("/mnt/user-data/outputs/img_hands.png")
