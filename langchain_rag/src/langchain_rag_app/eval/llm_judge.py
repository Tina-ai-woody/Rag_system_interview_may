import json
import re
from typing import Any

from ..core import get_llm


JUDGE_SYSTEM_PROMPT = """你是嚴格評分器。請根據 question / gold_answer / pred_answer / evidence 評分。
輸出 JSON，欄位：
- pass: boolean
- semantic_score: 0~1
- completeness_score: 0~1
- faithfulness_score: 0~1
- reason: string
- missing_points: string[]
- hallucination_flags: string[]
不要輸出其他文字。
"""


def parse_llm_judge_json(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", t)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return None

    need = ["pass", "semantic_score", "completeness_score", "faithfulness_score", "reason"]
    if not all(k in obj for k in need):
        return None
    obj.setdefault("missing_points", [])
    obj.setdefault("hallucination_flags", [])
    return obj


def judge_with_llm(question: str, gold: str, pred: str, evidence: str, enabled: bool = True) -> dict[str, Any]:
    if not enabled:
        return {
            "enabled": False,
            "pass": None,
            "semantic_score": None,
            "completeness_score": None,
            "faithfulness_score": None,
            "reason": "disabled",
            "missing_points": [],
            "hallucination_flags": [],
        }

    llm = get_llm()
    user = f"question: {question}\n\ngold_answer: {gold}\n\npred_answer: {pred}\n\nevidence: {evidence}"

    for _ in range(2):
        resp = llm.invoke([("system", JUDGE_SYSTEM_PROMPT), ("user", user)])
        txt = resp.content if isinstance(resp.content, str) else str(resp.content)
        parsed = parse_llm_judge_json(txt)
        if parsed is not None:
            return {"enabled": True, **parsed}

    return {
        "enabled": True,
        "pass": None,
        "semantic_score": 0.0,
        "completeness_score": 0.0,
        "faithfulness_score": 0.0,
        "reason": "llm_judge_parse_failed",
        "missing_points": [],
        "hallucination_flags": [],
    }
