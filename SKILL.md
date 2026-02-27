---
name: wechat-writing
description: "Use this skill whenever the user wants to write, optimize, evaluate, or brainstorm WeChat public account articles (公众号文章). Triggers include: requests to write a WeChat article, optimize an existing article, suggest topics, evaluate article quality, rewrite for higher engagement, or generate article components like titles, hooks, summaries, and image descriptions. The target audience is indie developers, programmers, and people pursuing side businesses in China. Writing style is conversational, grounded, mildly provocative — never preachy or hyperbolic. Do NOT use for general blog posts, academic writing, or non-WeChat content unless explicitly asked."
license: MIT
---

# WeChat Public Account Writing Skill

帮你写出风格一致、有传播力的公众号文章。面向副业创业者、独立开发者、AI 从业者。

---

## Overview

This skill provides four services:

| Service | When to use |
|---------|-------------|
| **Write** | User says "帮我写一篇关于XX的文章" |
| **Evaluate** | User provides an article and asks for feedback |
| **Topic Ideas** | User says "不知道写什么" or "给我几个选题" |
| **Rewrite** | User provides existing content and asks to improve it |

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

Every article must include all 6 sections in order:

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
| Title | 20 | Has number or scene, clear reader benefit, no banned words |
| Opening | 20 | Scene-based entry, reader can see themselves, no self-hype |
| Body content | 30 | Concrete data/cases, actionable steps, no fluff |
| Language style | 20 | Plain language, conversational, no banned phrases |
| Closing | 10 | Clean summary + interaction hook |

**Total score interpretation:**
- 85–100: Ready to publish
- 70–84: Minor edits needed
- 50–69: Significant revision required
- Below 50: Consider rewriting

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
