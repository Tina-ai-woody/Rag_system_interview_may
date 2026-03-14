import argparse
import json
from pathlib import Path

from .core import answer_question, build_index, load_config, parse_xlsx_questions, project_root
from .eval import (
    aggregate_three_layers,
    classify_question_type,
    compute_similarity_diagnostics,
    is_refusal_gold,
    judge_answer,
    judge_with_llm,
    summarize_results,
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

    eval_cfg = cfg.get("eval", {}) if isinstance(cfg, dict) else {}
    llm_enable_types = set(eval_cfg.get("llm_judge_enable_types", ["summary_strategy", "multi_fact"]))
    llm_sample_rate = float(eval_cfg.get("llm_judge_sample_rate", 1.0))
    similarity_enabled = bool(eval_cfg.get("similarity_enabled", True))

    for row in questions:
        pred = answer_question(row["question"])
        gold_is_refusal = is_refusal_gold(row["gold_answer"])
        qtype = classify_question_type(row["question"], row["gold_answer"])

        jr = judge_answer(
            pred_answer=pred["answer"],
            pred_refusal=pred["refusal"],
            gold_answer=row["gold_answer"],
            question=row["question"],
        )

        evidence = "\n".join([f"p{p}" for p in pred.get("sources", [])])
        llm_enabled = (qtype in llm_enable_types) and (llm_sample_rate >= 1.0)
        llm_judge = judge_with_llm(
            question=row["question"],
            gold=row["gold_answer"],
            pred=pred["answer"],
            evidence=evidence,
            enabled=llm_enabled,
        )

        sim = compute_similarity_diagnostics(
            answer=pred["answer"],
            gold=row["gold_answer"],
            question=row["question"],
            evidence=evidence,
            enabled=similarity_enabled,
        )

        final_label = aggregate_three_layers(
            question_type=qtype,
            rule_relaxed=jr.is_correct_relaxed,
            pred_refusal=pred["refusal"],
            gold_is_refusal=gold_is_refusal,
            llm_pass=llm_judge.get("pass"),
        )

        results.append(
            {
                **row,
                "question_type": qtype,
                "gold_is_refusal": gold_is_refusal,
                "pred_answer": pred["answer"],
                "pred_refusal": pred["refusal"],
                "pred_sources": pred["sources"],
                "rule_judge": {
                    "strict": jr.is_correct_strict,
                    "relaxed": jr.is_correct_relaxed,
                    "coverage": jr.coverage_score,
                    "reasons": jr.reason_codes,
                },
                "is_correct_strict": jr.is_correct_strict,
                "is_correct_relaxed": jr.is_correct_relaxed,
                "coverage_score": jr.coverage_score,
                "judge_reason_codes": jr.reason_codes,
                "failed_numeric_facts": jr.failed_numeric_facts,
                "numeric_match_detail": {
                    "failed_count": len(jr.failed_numeric_facts),
                    "all_numeric_matched": len(jr.failed_numeric_facts) == 0,
                },
                "llm_judge": llm_judge,
                "embedding_diagnostics": sim,
                "final_label": final_label,
            }
        )

    summary = summarize_results(results)

    out_dir = project_root() / "langchain_rag" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "eval_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "eval_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
