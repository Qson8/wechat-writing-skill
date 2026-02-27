---
name: wechat-writing
description: "Use this skill whenever the user wants to write, optimize, evaluate, or brainstorm WeChat public account articles (公众号文章). Triggers include: requests to write a WeChat article, optimize an existing article, suggest topics, evaluate article quality, rewrite for higher engagement, or generate article components like titles, hooks, summaries, and image descriptions. The target audience is indie developers, programmers, and people pursuing side businesses in China. Writing style is conversational, grounded, mildly provocative — never preachy or hyperbolic. Do NOT use for general blog posts, academic writing, or non-WeChat content unless explicitly asked."
license: MIT
---

# WeChat Public Account Writing Skill

帮你写出风格一致、有传播力的公众号文章。面向副业创业者、独立开发者、AI 从业者。

---

## Overview

This skill provides five services:

| Service | When to use |
|---------|-------------|
| **Write** | User says "帮我写一篇关于XX的文章" |
| **Evaluate** | User provides an article and asks for feedback |
| **Topic Ideas** | User says "不知道写什么" or "给我几个选题" |
| **Rewrite** | User provides existing content and asks to improve it |
| **Remove AI Flavor** | User says "去AI味" or "帮我改得更自然" |

---

## Audience & Positioning

**Target readers:** People who want to start a side business or indie project, but haven't yet — or just got started and hit their first walls. Not experts. Not influencers. Just regular folks figuring it out.

**Content pillars:**
- AI tool reviews & real-world tests
- Indie developer experiences (what worked, what didn't)
- Side income breakdowns (realistic numbers, real paths)
- Programmer's perspective on money, efficiency, and building

---

## Writing Style

### Core principles
- **Plain language first** — if you can say it simply, say it simply
- **Third-person objectivity** — inform, don't preach
- **Real feel** — specific numbers, actual examples, lived experience
- **Mild provocation** — it's OK to make readers feel a little urgency, as long as you give them a way out

### Tone
- Like talking to a friend who sometimes tells you what you don't want to hear
- Direct, opinionated, but never condescending
- Can create mild anxiety — but always ends with actionable hope

### Banned words & phrases
```
颠覆认知 / 逆天 / 炸裂 / 遥遥领先 / 卷王
相信自己 / 努力就会成功 / 你只差一个决定
今天给大家分享 / 本文将为大家介绍
震惊！/ 重磅！
```

### AI-flavored patterns to remove (去AI味)

AI生成的文章有以下特征，写作时必须避免：

| AI味特征 | 问题 | 怎么改 |
|---------|------|-------|
| 过度使用"首先/其次/最后" | 每段都这么写，显得机械 | 用"不过""但是""说到""就拿""其实"等更自然的过渡 |
| 过度礼貌客套 | "感谢您的阅读""希望对您有帮助" | 直接说"看完有收获的点个赞" |
| 句子过于完美对称 | "要学会倾听，也要学会表达" | "不仅要听，还得会说——这是我踩过的坑" |
| 堆砌程度词 | "非常""极其""十分""相当" | 直接删掉，或用具体场景代替 |
| 机械罗列 | "第一点、第二点、第三点" | 用"一个问题""一个例子""一个教训" |
| 正确的废话 | "要善于运用工具提高效率" | 给出具体工具、具体数字、具体场景 |
| 缺乏具体细节 | "我研究了很多AI工具" | "我试了ChatGPT、Claude、Midjourney这三个" |
| 过于书面化 | "因此/鉴于此/综上所述" | "所以""这么一搞""说白了" |

**去AI味的核心：把自己踩过的坑、解决的问题、具体的数字和例子写出来。**

### OK to use (sparingly, ≤2x per article)
```
干货 / 赋能 / 破局
```

---

## Article Structure

### Title (≤25 characters)
- Numbers beat vague claims
- Mild urgency is fine; extreme hyperbole is not
- ✅ `我用3个工具把公众号更新从4小时缩到30分钟`
- ✅ `普通人逆袭的底层逻辑`
- ✅ `你还在用传统方式写文章吗？你已经落后了！`
- ❌ `震惊！这个工具让你效率提升100倍！`

### Opening (3–5 sentences)
- Start with a specific scene or personal experience
- Hook the reader with something they recognize about themselves
- ✅ `上个月我试着用AI帮我写了几篇公众号文章，结果发现一个问题...`
- ❌ Pure self-congratulation with no reader connection

### Body
- Max 4 lines per paragraph
- One idea per paragraph
- Back every claim with a number, case, or step
- Subheadings should be plain and direct (no "深度解析" or "全面拆解")
- Lists are fine, but don't make the whole article a list

### Closing
- One-sentence summary or action recommendation
- Optional: open-ended question to drive comments

---

## Required Output Format

Before writing the article, output the article metrics first:

```
【领域】AI工具 / 独立开发 / 副业路径 / 程序员视角
【字数】800-1500字
【评分预估】标题20分 + 开头18分 + 正文28分 + 语言18分 + 结尾8分 = 92分
【AI味预估】12分（真人级）
```

Then output the 6 sections in order:

```
【标题】
≤25字

【开头引言钩子】
18-22字，反常识 / 扎心 / 悬念 / 数据冲击

【摘要】
110-120字，核心观点 + 读者收益 + 行动号召

【正文】
开头（3-5句场景切入）

**小标题一**
内容...

**小标题二**
内容...

（根据文章长度决定小标题数量）

【结尾问句互动钩子】
18-22字，开放式提问，引发评论

【配图需求】
- 封面图（16:9）：风格 + 画面内容描述
- 正文配图1：内容描述
- 正文配图2：内容描述
- 正文配图3（可选）：内容描述
```

---

## Word Count Guidelines

| Article type | Target length |
|--------------|---------------|
| Tool review | 600–1000 words |
| Personal experience | 1000–2000 words |
| Standard article | 800–1500 words |

---

## Evaluation Rubric

When asked to evaluate an article, score each dimension and give specific improvement suggestions:

| Dimension | Max score | Key criteria |
|-----------|-----------|--------------|
| Title | 15 | Has number or scene, clear reader benefit, no banned words |
| Opening | 15 | Scene-based entry, reader can see themselves, no self-hype |
| Body content | 25 | Concrete data/cases, actionable steps, no fluff |
| Language style | 15 | Plain language, conversational, no banned phrases |
| **AI flavor (去AI味)** | **30** | **0-100 scale, higher = more AI-like** |

### AI Flavor Scoring (0-100分，分值越高AI味越重)

与市面主流AI检测工具（Turnitin、Originality.ai）评分标准一致：

| Score | 等级 | 说明 |
|-------|------|------|
| **0-20** | 真人级 | 细节丰富，像真人写的故事，有踩坑经历 |
| **21-40** | 轻微AI味 | 有一些具体例子，但过渡稍显机械 |
| **41-60** | 中等AI味 | 偶尔出现机械过渡，有客套话，句子较对称 |
| **61-80** | 较高AI味 | 大量机械过渡，堆砌程度词，缺乏具体细节 |
| **81-100** | 严重AI味 | 流水线产品，通篇正确的废话，像AI写的 |

**AI味扣分项（每项扣8-15分）：**
- 全文"首先/其次/最后"出现超过3次
- 有"感谢您的阅读""希望对您有帮助"等客套话
- 句子过度对称（如"要学会A，也要学会B"）超过2处
- 程度词堆砌（非常/极其/十分/相当）超过3处
- 机械罗列"第一点/第二点/第三点"超过2处
- 缺乏具体数字、具体工具名、具体案例
- 过于书面化（因此/鉴于此/综上所述）超过2处
- 没有个人经历或踩坑故事

**AI味加分项（每项加8-15分）：**
- 有具体踩坑经历和解决方案
- 有具体数字（如"省了10小时""赚了3000块"）
- 有具体工具名/产品名
- 有口语化表达（"捣鼓""踩坑""说白了"）
- 句子长短不一，有节奏感
- 有和读者相关的吐槽或共鸣
| Closing | 10 | Clean summary + interaction hook |

**AI味>60分 → 直接重新生成**

当评估时AI味得分>60分，不需要修改建议，直接按照去AI味规则重新生成文章。

---

**Total score interpretation:**
- 90–100: Ready to publish（AI味≤20分）
- 75–89: Minor edits needed（AI味≤40分）
- 60–74: Significant revision required
- Below 60: Consider rewriting

**AI味专项指标（0-100分）：**
- ≤20分：真人级，可发布
- 21-40分：轻微AI味，简单修改
- 41-60分：中等AI味，需要较大修改
- 61-80分：较高AI味，建议重写
- 81-100分：严重AI味，必须重写

---

## Topic Generation

When the user asks for topic ideas, generate 3–5 options. Each should include:
- A working title (following the title formula above)
- The core insight or angle
- Why it fits this audience

Focus areas: AI tools, indie dev, side income, programmer + money mindset.

---

## Image Generation Guidance

When writing `【配图需求】`, describe images in terms of:
- **Cover (16:9):** Dark tech background preferred. Main headline text. Supporting visual (robot, flowchart, code snippet, etc.)
- **Body images:** Comparison tables, flowcharts, feature card grids, step diagrams — anything that can be screenshotted and shared

These descriptions can be fed directly into `render_cover()` and `render_comparison()` from the companion `scripts/render_images.py`.

---

## Integration with Automation Pipeline

This skill is designed to work alongside:

```
SKILL.md (this file)       ← writing style & structure rules
scripts/render_images.py   ← renders cover + body images from .pen template
main.py                    ← full pipeline: generate → render → push to WeChat draft
SKILL_eval.md              ← standalone evaluation rubric
evals.json                 ← test cases for CI validation
```

To use in Claude Code or Cursor, place this repo in your project root. The `CLAUDE.md` file will be auto-loaded by Claude Code. The `.cursor/rules/` directory will be auto-loaded by Cursor.
