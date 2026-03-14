def aggregate_three_layers(question_type: str, rule_relaxed: bool, pred_refusal: bool, gold_is_refusal: bool, llm_pass: bool | None) -> str:
    if gold_is_refusal:
        return "refusal_correct" if pred_refusal else "refusal_incorrect"

    hard_types = {"hard_fact_numeric", "hard_fact_entity", "multi_fact"}
    semantic_types = {"summary_strategy"}

    if question_type in hard_types:
        return "correct_hard" if rule_relaxed else "incorrect"

    if question_type in semantic_types:
        if rule_relaxed and llm_pass is True:
            return "correct_semantic"
        if rule_relaxed or llm_pass is True:
            return "partial"
        return "incorrect"

    return "correct_hard" if rule_relaxed else "incorrect"
