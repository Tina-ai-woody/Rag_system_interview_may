import unittest

from langchain_rag_app.eval.aggregator import aggregate_three_layers
from langchain_rag_app.eval.llm_judge import parse_llm_judge_json
from langchain_rag_app.eval.router import classify_question_type


class TestThreeLayerEval(unittest.TestCase):
    def test_router_numeric(self):
        t = classify_question_type("富邦金控每股盈餘是多少？", "10.77元")
        self.assertEqual(t, "hard_fact_numeric")

    def test_router_summary(self):
        t = classify_question_type("請總結2025年三大子公司策略", "...")
        self.assertEqual(t, "summary_strategy")

    def test_aggregator_hard_fact_not_overridden(self):
        label = aggregate_three_layers(
            question_type="hard_fact_numeric",
            rule_relaxed=False,
            pred_refusal=False,
            gold_is_refusal=False,
            llm_pass=True,
        )
        self.assertEqual(label, "incorrect")

    def test_aggregator_semantic_partial(self):
        label = aggregate_three_layers(
            question_type="summary_strategy",
            rule_relaxed=False,
            pred_refusal=False,
            gold_is_refusal=False,
            llm_pass=True,
        )
        self.assertEqual(label, "partial")

    def test_llm_judge_parser(self):
        txt = '{"pass": true, "semantic_score": 0.82, "completeness_score": 0.67, "faithfulness_score": 0.9, "reason": "ok", "missing_points": [], "hallucination_flags": []}'
        obj = parse_llm_judge_json(txt)
        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertTrue(obj["pass"])


if __name__ == "__main__":
    unittest.main()
