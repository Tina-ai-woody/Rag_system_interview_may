# eval_summary_explain.md

本文件說明 `langchain_rag/artifacts/eval_summary.json` 各欄位「如何計算」與「如何解讀」。

---

## 1) 整體欄位（Top-level）

## `total`
- **計算**：`len(results)`（題目總數）
- **解讀**：本次評測樣本量。你目前通常是 30。

## `accuracy`
- **計算**：目前等同 `accuracy_relaxed`（`relaxed_correct / total`）
- **解讀**：主準確率（寬鬆口徑）。

## `accuracy_strict`
- **計算**：`is_correct_strict=true` 題數 / `total`
- **解讀**：嚴格判對率（格式與精確度要求高）。

## `accuracy_relaxed`
- **計算**：`is_correct_relaxed=true` 題數 / `total`
- **解讀**：寬鬆判對率（容忍表達等價、數值正規化後等價）。

## `avg_coverage_score`
- **計算**：`sum(coverage_score)/total`
- **解讀**：多子題/多要點題目的平均覆蓋度；越高表示漏答越少。

## `citation_coverage`
- **計算**：有 `pred_sources` 的題數 / `total`
- **解讀**：可追溯性比例；高不代表一定答對，只代表有提供來源。

---

## 2) 拒答相關欄位

先定義：
- `gold_is_refusal`：標準答案是否應拒答
- `pred_refusal`：模型是否拒答

## `refusal_confusion_matrix`
- **tp**：應拒答且有拒答
- **fp**：不該拒答卻拒答（過度拒答）
- **fn**：該拒答卻未拒答（幻覺風險）
- **tn**：不該拒答且未拒答

## `refusal_precision`
- **計算**：`tp / (tp + fp)`
- **解讀**：模型「一旦拒答」有多準。低代表 over-refusal 多。

## `refusal_recall`
- **計算**：`tp / (tp + fn)`
- **解讀**：該拒答有沒有抓到。低代表漏拒答多。

## `refusal_f1`
- **計算**：`2 * P * R / (P + R)`
- **解讀**：拒答整體平衡指標，通常是拒答機制的主 KPI。

---

## 3) `layer1`（Rule-based）

## `layer1.accuracy_strict`
- **計算**：同 top-level strict
- **解讀**：規則層嚴格正確率

## `layer1.accuracy_relaxed`
- **計算**：同 top-level relaxed
- **解讀**：規則層寬鬆正確率

---

## 4) `layer2`（LLM Judge）

`llm_rows = llm_judge.enabled == true` 的題目集合。

## `layer2.semantic_pass_rate`
- **計算**：`llm_pass=true` 題數 / `len(llm_rows)`
- **解讀**：語義層通過比例（不是最終 accuracy）。

## `layer2.avg_semantic_score`
- **計算**：`mean(llm_judge.semantic_score)`
- **解讀**：語義對齊平均分。

## `layer2.avg_completeness_score`
- **計算**：`mean(llm_judge.completeness_score)`
- **解讀**：回答完整度平均分。

## `layer2.avg_faithfulness_score`
- **計算**：`mean(llm_judge.faithfulness_score)`
- **解讀**：是否忠於證據平均分（抗幻覺重要指標）。

---

## 5) `layer3`（Embedding 診斷）

`sim_rows = embedding_diagnostics.enabled == true` 的題目集合。

## `avg_ans_gold_sim`
- **計算**：`mean(ans_gold_sim)`
- **解讀**：答案與 gold 的向量相似度（診斷用，不作最終裁決）。

## `avg_ans_q_sim`
- **計算**：`mean(ans_q_sim)`
- **解讀**：答案是否對題（避免答非所問）。

## `avg_ans_evidence_sim`
- **計算**：`mean(ans_evidence_sim)`
- **解讀**：答案與檢索證據的一致程度。

---

## 6) `retrieval`（檢索/重排）

## `retrieval_recall_at_20`
- **計算**：`retrieval_recall_at_20=true` 題數 / `total`
- **解讀**：top-20 候選是否曾包含 gold evidence（召回天花板）。

## `fusion_k_hit_rate`
- **計算**：`fusion_k_hit=true` 題數 / `total`
- **解讀**：不經 rerank，fusion top-k 的命中率。

## `final_k_hit_rate`
- **計算**：`final_k_hit=true` 題數 / `total`
- **解讀**：經 rerank 後最終 top-k 的命中率。

## `final_context_hit_rate`
- **計算**：`final_context_hit=true` 題數 / `total`
- **解讀**：最終送入 LLM 的 context 是否命中 gold evidence。

## `avg_rerank_gain_k`
- **計算**：`mean(rerank_gain_k)`，其中每題 `rerank_gain_k = int(final_k_hit) - int(fusion_k_hit)`
- **解讀**：公平比較 rerank 前後的排序增益：
  - >0：rerank 有幫助
  - =0：中性
  - <0：rerank 可能拖累

## `pipeline_drop_from_20_to_k`
- **計算**：平均 `pipeline_drop_from_20_to_k`
- **解讀**：從 top-20 縮到 top-k 的天然落差（非純 rerank 品質）。

## `rerank_gain`（舊欄位，建議視為 deprecated）
- **計算**：平均舊版 gain（常與 top20 口徑綁定）
- **解讀**：容易受口徑影響，不建議作主 KPI。

## `avg_rerank_latency_ms`
- **計算**：平均每題 rerank 延遲（毫秒）
- **解讀**：排序品質與效能的 trade-off 指標。

---

## 7) `gate`（P3 refusal gate）

## `gate_force_refusal_rate`
- **計算**：`gate_decision == force_refusal` 題數 / `total`
- **解讀**：gate 觸發拒答比例。

## `over_refusal_by_gate`
- **計算**：`gate_decision==force_refusal && !gold_is_refusal` 題數 / `total`
- **解讀**：gate 造成的誤拒答比例。

## `missed_refusal_after_gate`
- **計算**：`gold_is_refusal && gate_decision!=force_refusal` 題數 / `total`
- **解讀**：gate 漏抓該拒答的比例。

---

## 8) `final`（三層聚合後）

## `final_accuracy`
- **計算**：`final_label in {correct_hard, correct_semantic, refusal_correct}` 題數 / `total`
- **解讀**：最終業務口徑正確率。

## `hard_fact_accuracy`
- **計算**：在 `hard_fact_numeric/hard_fact_entity/multi_fact/refusal_expected` 子集上，
  `final_label in {correct_hard, refusal_correct}` 的比例
- **解讀**：硬事實題是否穩定。

## `semantic_task_pass`
- **計算**：語義任務子集的通過率（目前已含 summary/multi_fact）
- **解讀**：摘要與多子題語義任務整體通過情況。

## `semantic_task_pass_summary`
- **計算**：`summary_strategy` 子集通過率
- **解讀**：摘要題專項表現。

## `semantic_task_pass_multifact`
- **計算**：`multi_fact` 子集通過率
- **解讀**：多子題整合能力專項表現。

## `semantic_rule_conflict_rate`
- **計算**：語義層通過但最終被打回的衝突比例
- **解讀**：若高，通常是 aggregator 規則不合理。

---

## 9) 建議判讀順序（實務）

1. **總體是否前進**：`final_accuracy`, `accuracy_relaxed`
2. **拒答是否健康**：`refusal_f1`, `over_refusal_by_gate`, `missed_refusal_after_gate`
3. **檢索是否真提升**：`final_k_hit_rate`, `avg_rerank_gain_k`
4. **語義層是否有效**：`semantic_task_pass`, `semantic_rule_conflict_rate`
5. **效能成本**：`avg_rerank_latency_ms`

---

## 10) 常見誤解提醒

- `citation_coverage=1.0` 不代表答對率高，只代表每題都有來源。
- `retrieval_recall_at_20` 高，不代表 final top-k 一定命中。
- `layer2` 高分不一定代表 `final` 高，還會受 aggregator 與 gate 影響。
- 請優先看 `avg_rerank_gain_k`，不要只看舊 `rerank_gain`。
