#!/usr/bin/env python3
"""
run_evals.py — 运行 wechat-writing skill 的评估用例

用法：
    python evals/run_evals.py
    python evals/run_evals.py --id 1        # 只跑第1个用例
    python evals/run_evals.py --verbose     # 打印完整输出
    python evals/run_evals.py --model claude-opus-4-6

依赖：
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-..."
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("❌ 请先安装依赖：pip install anthropic")
    sys.exit(1)


# ── 加载文件 ──────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
SKILL_MD  = ROOT / "SKILL.md"
EVALS_JSON = ROOT / "evals" / "evals.json"


def load_skill() -> str:
    if not SKILL_MD.exists():
        raise FileNotFoundError(f"找不到 SKILL.md：{SKILL_MD}")
    return SKILL_MD.read_text(encoding="utf-8")


def load_evals() -> list:
    if not EVALS_JSON.exists():
        raise FileNotFoundError(f"找不到 evals.json：{EVALS_JSON}")
    with open(EVALS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return data["evals"]


# ── 评估逻辑 ──────────────────────────────────────────

def check_output(output: str, expected: dict) -> tuple[bool, list[str]]:
    """
    按 expected_output 规则校验模型输出。
    返回 (passed, [失败原因列表])
    """
    failures = []

    # 检查必须包含的 sections
    for section in expected.get("sections", []):
        if section not in output:
            failures.append(f"缺少必要部分：{section}")

    # 检查标题字数
    if "title_max_chars" in expected:
        title_match = re.search(r"【标题】\s*\n(.+)", output)
        if title_match:
            title = title_match.group(1).strip()
            if len(title) > expected["title_max_chars"]:
                failures.append(f"标题超长：{len(title)} 字（限 {expected['title_max_chars']} 字）")

    # 检查禁用词
    for word in expected.get("banned_words_absent", []):
        if word in output:
            failures.append(f"出现禁用词：「{word}」")

    # 检查正文含关键事实
    for fact in expected.get("body_mentions_key_facts", []):
        if fact not in output:
            failures.append(f"正文缺少关键信息：{fact}")

    # 检查总分低于阈值（评估服务）
    if "total_score_below" in expected:
        score_match = re.search(r"综合评分[：:]\s*(\d+)", output)
        if score_match:
            score = int(score_match.group(1))
            if score >= expected["total_score_below"]:
                failures.append(f"评分应低于 {expected['total_score_below']}，实际得分 {score}")

    # 检查选题数量
    if "topic_count_range" in expected:
        lo, hi = expected["topic_count_range"]
        # 简单计数：以数字+. 开头的行
        count = len(re.findall(r"^\d+[\.\、]", output, re.MULTILINE))
        if not (lo <= count <= hi):
            failures.append(f"选题数量 {count} 不在范围 [{lo}, {hi}] 内")

    return len(failures) == 0, failures


def run_eval(eval_case: dict, skill: str, client: anthropic.Anthropic,
             model: str, verbose: bool) -> dict:
    """运行单个用例，返回结果字典"""
    print(f"\n{'─'*50}")
    print(f"▶ 用例 #{eval_case['id']} [{eval_case['service']}]")
    print(f"  Prompt: {eval_case['prompt'][:60]}...")

    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=skill,
            messages=[{"role": "user", "content": eval_case["prompt"]}]
        )
        output = message.content[0].text

        if verbose:
            print(f"\n{'='*40} 模型输出 {'='*40}")
            print(output)
            print("=" * 80)

        passed, failures = check_output(output, eval_case.get("expected_output", {}))

        if passed:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL")
            for f in failures:
                print(f"     - {f}")

        return {
            "id": eval_case["id"],
            "service": eval_case["service"],
            "passed": passed,
            "failures": failures,
            "output_preview": output[:200],
        }

    except Exception as e:
        print(f"  💥 ERROR: {e}")
        return {
            "id": eval_case["id"],
            "service": eval_case["service"],
            "passed": False,
            "failures": [f"API 调用失败：{e}"],
            "output_preview": "",
        }


# ── 主函数 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="运行 wechat-writing skill evals")
    parser.add_argument("--id",      type=int, help="只运行指定 ID 的用例")
    parser.add_argument("--verbose", action="store_true", help="打印完整模型输出")
    parser.add_argument("--model",   default="claude-sonnet-4-6", help="使用的模型")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量：export ANTHROPIC_API_KEY='sk-...'")
        sys.exit(1)

    skill  = load_skill()
    evals  = load_evals()
    client = anthropic.Anthropic(api_key=api_key)

    if args.id:
        evals = [e for e in evals if e["id"] == args.id]
        if not evals:
            print(f"❌ 找不到 ID={args.id} 的用例")
            sys.exit(1)

    print(f"🚀 开始运行 {len(evals)} 个用例（模型：{args.model}）")

    results  = [run_eval(e, skill, client, args.model, args.verbose) for e in evals]
    passed   = sum(1 for r in results if r["passed"])
    total    = len(results)

    print(f"\n{'═'*50}")
    print(f"📊 结果：{passed}/{total} 通过")
    if passed == total:
        print("🎉 全部通过！")
    else:
        failed = [r for r in results if not r["passed"]]
        print(f"⚠️  {len(failed)} 个用例失败：")
        for r in failed:
            print(f"   - 用例 #{r['id']} [{r['service']}]：{r['failures']}")

    # 保存结果
    out_path = ROOT / "evals" / "results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"passed": passed, "total": total, "results": results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n📄 详细结果已保存：{out_path}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
