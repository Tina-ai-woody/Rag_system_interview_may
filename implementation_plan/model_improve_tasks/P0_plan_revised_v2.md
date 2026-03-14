# P0_plan_revised_v2.md — 三層評分機制設計（Rule + LLM Judge + Similarity）

> 目標：在保留 P0 規則評分可解釋性與可重現性的前提下，引入語意層評估，形成穩定且全面的評測架構，避免「只看字串」或「只看語意」的偏差。

---

## 1) 設計背景

目前 P0 已有：
- strict / relaxed 雙軌
- numeric-aware 判定
- refusal 指標
- coverage score

但仍有兩類問題：
1. **語義題（摘要/策略題）不易靠規則完整評估**
2. **只看規則可能低估模型在自然語言表達上的品質**

因此導入三層評分：
- **Layer 1：Rule-based（主裁決）**
- **Layer 2：LLM-as-a-Judge（語義裁決）**
- **Layer 3：Embedding Similarity（診斷訊號）**

---

## 2) 三層架構總覽

## Layer 1 — Rule-based Hard Judge（主 KPI）

### 適用題型
- 數值、年份、比率、金額、拒答題
- 多子題需要完整覆蓋的問題

### 輸出
- `is_correct_strict`
- `is_correct_relaxed`
- `coverage_score`
- `refusal_*`
- `judge_reason_codes`

### 原則
- **Hard facts 優先以規則判定**
- 對年份/金額等關鍵事實，規則判錯即不可被語義層覆蓋

---

## Layer 2 — LLM-as-a-Judge Semantic Eval（語義 KPI）

### 適用題型
- 摘要題、策略題、比較題（語句變化大）
- 規則難以完整覆蓋的開放式回答

### 評估面向（建議 0~1 分）
1. `semantic_correctness`：語意是否對齊 gold
2. `completeness`：是否回答到所有子問題
3. `faithfulness`：是否有超出 evidence 的推論/幻覺
4. `conciseness`（選填）：是否冗長偏題

### 輸出（每題）
```json
{
  "llm_judge": {
    "pass": true,
    "semantic_score": 0.82,
    "completeness_score": 0.67,
    "faithfulness_score": 0.9,
    "reason": "...",
    "missing_points": ["..."],
    "hallucination_flags": []
  }
}
```

### 穩定性設計
- `temperature=0`
- 固定 rubric + fixed json schema
- 必要時重試一次（格式錯誤時）

---

## Layer 3 — Embedding Similarity Diagnostic Signal（輔助）

### 角色
- **僅作診斷，不直接決定對錯**
- 幫助定位「規則判錯但語意接近」或「語意偏離」

### 指標
- `answer_gold_similarity`（pred vs gold）
- `answer_question_similarity`（pred vs question，防止答非所問）
- `evidence_answer_similarity`（pred vs retrieved evidence 摘要）

### 用途
- 觀察模型 drift
- 輔助分群錯題（低相似/高相似但仍錯）

---

## 3) 層級整合與裁決策略

## 3.1 Final 判定規則（建議）

1. 若題目屬於 hard-fact（數值/拒答/實體明確）：
   - 以 Layer 1 為主
   - Layer 2/3 只能補充，不可覆蓋 Rule fail

2. 若題目屬於 open-semantic（摘要/策略）：
   - Layer 1 + Layer 2 共同決定
   - Layer 3 作風險提示

## 3.2 建議 final label

- `correct_hard`
- `correct_semantic`
- `partial`
- `incorrect`
- `refusal_correct`
- `refusal_incorrect`

---

## 4) 題型路由（Question Type Router）

在評測前先做題型分類：
- `hard_fact_numeric`
- `hard_fact_entity`
- `multi_fact`
- `summary_strategy`
- `refusal_expected`

路由規則可先 rule-based（關鍵詞）起步，之後再升級。

### 例
- 含「多少/幾年/比例/總額/每股」→ `hard_fact_numeric`
- 含「總結/簡述/彙整/比較策略」→ `summary_strategy`

---

## 5) 評測資料結構更新

## 5.1 eval_results.json 每題新增

```json
{
  "question_type": "hard_fact_numeric",
  "rule_judge": {
    "strict": false,
    "relaxed": true,
    "coverage": 1.0,
    "reasons": ["..."]
  },
  "llm_judge": {
    "enabled": true,
    "pass": true,
    "semantic_score": 0.82,
    "completeness_score": 0.67,
    "faithfulness_score": 0.9,
    "reason": "..."
  },
  "embedding_diagnostics": {
    "ans_gold_sim": 0.91,
    "ans_q_sim": 0.73,
    "ans_evidence_sim": 0.88
  },
  "final_label": "correct_hard"
}
```

## 5.2 eval_summary.json 新增

```json
{
  "layer1": {
    "accuracy_strict": 0.2,
    "accuracy_relaxed": 0.37
  },
  "layer2": {
    "semantic_pass_rate": 0.55,
    "avg_semantic_score": 0.62,
    "avg_completeness_score": 0.51,
    "avg_faithfulness_score": 0.84
  },
  "layer3": {
    "avg_ans_gold_sim": 0.78,
    "avg_ans_q_sim": 0.66,
    "avg_ans_evidence_sim": 0.72
  },
  "final": {
    "final_accuracy": 0.43,
    "hard_fact_accuracy": 0.35,
    "semantic_task_pass": 0.58
  }
}
```

---

## 6) 任務拆解（P0-v2-1 ~ P0-v2-7）

## P0-v2-1：題型分類器
- 實作 `classify_question_type(question)`
- 先 rule-based 關鍵詞版本

## P0-v2-2：Layer 1 接口標準化
- 將現有 strict/relaxed/refusal/coverage 封裝成 `rule_judge` 區塊

## P0-v2-3：Layer 2 LLM Judge 模組
- 實作 `judge_with_llm(question, gold, pred, evidence)`
- 固定輸出 JSON schema
- 失敗重試與 fallback

## P0-v2-4：Layer 3 Similarity 模組
- 實作 embedding-based 相似度計算
- 只回傳診斷分數

## P0-v2-5：Final Label Aggregator
- 實作 `aggregate_three_layers(...) -> final_label`
- 保證 hard-fact 不被語義分數覆蓋

## P0-v2-6：輸出格式升級
- 更新 `eval_results.json` / `eval_summary.json`
- 向後相容保留舊欄位

## P0-v2-7：測試與回歸
- 單測：router、aggregator、LLM schema parser
- 回歸：與 P0-revised-v1 結果對照

---

## 7) LLM Judge Rubric（簡版）

請 Judge 嚴格依據：
1. 是否回答題目核心要求
2. 是否涵蓋所有子項
3. 是否與提供 evidence 一致
4. 是否包含無根據延伸

### pass 條件（建議）
- `semantic_score >= 0.7`
- `faithfulness_score >= 0.8`
- 若 `question_type=multi_fact`，`completeness_score >= 0.8`

---

## 8) 成本與延遲控制

1. **只對特定題型啟用 Layer 2**
   - hard fact 可跳過或低頻抽樣
2. **批次化執行 LLM Judge**
3. **錯誤重試上限 1 次**
4. **可設定 `llm_judge_sample_rate`**

---

## 9) 驗收標準（Definition of Done）

1. 三層輸出完整，且 JSON schema 穩定
2. hard-fact 題不會被 LLM judge 錯誤「洗白」
3. summary/strategy 題可得可解釋語義分數
4. `eval_summary` 可同時呈現 rule / semantic / similarity 三視角
5. 與 v1 相比，錯題診斷資訊明顯提升

---

## 10) 導入順序（建議）

### Phase A（低風險）
- 先上 Layer 3（similarity）+ 輸出欄位
- 不影響最終分數

### Phase B（中風險）
- 上 Layer 2（LLM Judge），先僅做報表不參與 final label

### Phase C（受控啟用）
- 啟用 Aggregator，讓 open-semantic 題型使用 Layer1+2 聯合判定

> 原則：先觀測、再裁決，避免一次性改動太大。

---

## 11) 預期收益

- **準確性**：hard facts 維持嚴謹，語義題判定更貼近人工
- **可解釋性**：每題可看規則、語義、相似度三種視角
- **可迭代性**：後續 P1/P2/P3 優化可被更精準地量測與定位
