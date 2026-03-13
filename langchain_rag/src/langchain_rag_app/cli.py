import argparse
import json
from pathlib import Path

from .core import (
    answer_question,
    build_index,
    is_refusal_gold,
    judge,
    load_config,
    parse_xlsx_questions,
    project_root,
)


def index_cmd() -> None:
    n = build_index()
    print(json.dumps({"chunks": n}, ensure_ascii=False))


def query_cmd() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    args = parser.parse_args()
    ans = answer_question(args.question)
    print(json.dumps(ans, ensure_ascii=False, indent=2))


def eval_cmd() -> None:
    cfg = load_config()
    qa_path = project_root() / cfg["qa_xlsx"]
    questions = parse_xlsx_questions(qa_path)

    results = []
    correct = 0
    refusal_total = 0
    refusal_correct = 0
    citation_covered = 0

    for row in questions:
        pred = answer_question(row["question"])
        ok = judge(pred["answer"], pred["refusal"], row["gold_answer"])
        correct += int(ok)

        if is_refusal_gold(row["gold_answer"]):
            refusal_total += 1
            refusal_correct += int(pred["refusal"])

        citation_covered += int(bool(pred.get("sources")))

        results.append({
            **row,
            "pred_answer": pred["answer"],
            "pred_refusal": pred["refusal"],
            "pred_sources": pred["sources"],
            "is_correct": ok,
        })

    total = max(1, len(results))
    summary = {
        "total": len(results),
        "accuracy": round(correct / total, 4),
        "refusal_total": refusal_total,
        "refusal_precision": round(refusal_correct / max(1, refusal_total), 4),
        "citation_coverage": round(citation_covered / total, 4),
    }

    out_dir = project_root() / "langchain_rag" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "eval_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "eval_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
