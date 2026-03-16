# P3_plan.md — 拒答閘門（Evidence Sufficiency Gate）實作細部計畫

> 目標：將「是否拒答」從單靠 LLM prompt 的不穩定判斷，升級為可控、可解釋、可量測的 Evidence Sufficiency Gate，降低「該拒答不拒答」與「不該拒答卻拒答」。

---

## 1) 問題背景與目標

目前拒答主要依賴模型 prompt 判斷，常見兩種錯誤：

1. **Under-refusal（漏拒答）**
   - 資料不足仍硬答，造成幻覺
2. **Over-refusal（過度拒答）**
   - 明明有足夠證據卻拒答

### P3 目標指標

- 提升 `refusal_precision`
- 提升 `refusal_recall`
- 提升 `refusal_f1`
- 同時維持 `accuracy_relaxed` 不明顯下降

---

## 2) P3 範圍（In Scope / Out of Scope）

### In Scope

- 在推論流程加入 evidence sufficiency gate
- 題目實體對齊（entity alignment）
- 多子題覆蓋判斷（coverage check）
- 標準化拒答輸出
- 新增拒答診斷欄位與指標

### Out of Scope

- 不修改 chunking（P4）
- 不修改主要 retrieval 架構（P1）
- 不重寫評測器核心（P0）

---

## 3) Gate 核心設計

## 3.1 Gate 判定總流程

1. 取得 retrieval final docs（含 page）
2. 從問題抽取關鍵要素（實體、年份、指標、子問題）
3. 檢查 evidence 是否充分支持
4. 產出 `gate_decision`
   - `allow_answer`
   - `force_refusal`
5. 若 `force_refusal`，直接回傳標準 `refusal_text`

---

## 3.2 Evidence Sufficiency 檢查維度

### A) 實體對齊（Entity Alignment）

檢查問題核心實體（如富邦金控/子公司/公司名）是否出現在 final docs。

- 若題目問「外部公司」但資料庫無該公司證據 → `force_refusal`
- 若實體嚴重錯配（問A拿到B）→ `force_refusal`

### B) 數值/年份可驗證性（Fact Verifiability）

當問題屬於 hard fact：
- 若 final docs 內找不到對應數值/年份片段 → `force_refusal`
- 若僅有模糊描述、無可核對值 → `force_refusal`

### C) 多子題覆蓋（Sub-question Coverage）

對 multi-fact / compare 題：
- 子題需達最低覆蓋門檻（建議 `>= 0.8`）
- 低於門檻則拒答，避免只答一半

### D) 推論類型限制（Inference Guard）

- 預測、主觀推論、跨資料邊界問題
- 若 evidence 不含直接支持語句 → `force_refusal`

---

## 4) 規則策略（V1）

## 4.1 rule-based gate（先上線）

先用保守、可解釋規則：

- `missing_entity_match`
- `insufficient_numeric_evidence`
- `subquestion_coverage_too_low`
- `out_of_scope_question`

只要命中任一高風險規則，即拒答。

## 4.2 confidence scoring（可選）

為每題計算 `evidence_confidence`（0~1），作為 debug 訊號：

- entity_match_score
- numeric_support_score
- coverage_score

若總分低於閾值（如 0.6），拒答。

---

## 5) 輸出格式與欄位擴充

## 5.1 answer output 新增欄位（建議）

```json
{
  "answer": "...",
  "refusal": true,
  "reason": "...",
  "gate": {
    "decision": "force_refusal",
    "reasons": ["missing_entity_match", "subquestion_coverage_too_low"],
    "evidence_confidence": 0.42,
    "entity_match": false,
    "subquestion_coverage": 0.5
  }
}
```

## 5.2 eval_results 每題新增

- `gate_decision`
- `gate_reasons`
- `gate_confidence`
- `entity_match`
- `subquestion_coverage`

---

## 6) 實作任務拆解（P3-1 ~ P3-8）

## P3-1：問題要素抽取器

- `extract_question_signals(question)`
- 產出：entities / years / metric_terms / question_type

## P3-2：evidence analyzer

- 輸入 final docs
- 輸出：entity match、numeric evidence 命中、子題覆蓋

## P3-3：gate engine

- `run_evidence_gate(signals, evidence, cfg)`
- 產出 `decision + reasons + confidence`

## P3-4：推論流程串接

- 在 LLM 最終輸出前後掛 gate
- 若 `force_refusal` 直接覆蓋輸出為拒答格式

## P3-5：標準拒答模板

- 使用 config `refusal_text`
- 另外可加 `refusal_reason_code`

## P3-6：config 擴充

建議新增：

```json
{
  "gate": {
    "enabled": true,
    "min_subquestion_coverage": 0.8,
    "min_evidence_confidence": 0.6,
    "hard_rules": {
      "require_entity_match": true,
      "require_numeric_evidence_for_hard_fact": true,
      "block_out_of_scope": true
    }
  }
}
```

## P3-7：評測輸出與指標

新增 gate 專屬指標：
- `gate_force_refusal_rate`
- `over_refusal_by_gate`
- `missed_refusal_after_gate`

## P3-8：單元測試 + 回歸

最小測試情境：
1. 外部公司問題且無證據 → 必拒答
2. hard-fact 無數值證據 → 必拒答
3. multi-fact 覆蓋不足 → 必拒答
4. 有完整證據且實體對齊 → 不拒答
5. 邊界值（coverage=0.8）行為符合設定

---

## 7) 實施階段與時程（建議）

## Phase 1（1 天）
- P3-1 / P3-2 / P3-3（先做 rule-based gate）

## Phase 2（1 天）
- P3-4 / P3-5 / P3-6（接入推論流程與設定）

## Phase 3（0.5~1 天）
- P3-7 / P3-8（指標與測試）
- 完整跑一次 eval 比較 before/after

---

## 8) 驗收標準（DoD）

1. Gate 可透過 config 開關
2. 拒答決策有 reason code 可追溯
3. `refusal_f1` 相較 baseline 提升
4. `accuracy_relaxed` 不顯著惡化（可容忍小幅波動）
5. 錯誤案例可由 `gate_reasons` 快速定位

---

## 9) 風險與緩解

1. **過度拒答風險**
   - 緩解：先用保守閾值；每輪檢查 over_refusal

2. **規則過硬造成 false refusal**
   - 緩解：允許 per-question-type 閾值

3. **與 P2（多子題）耦合**
   - 緩解：先採簡化 coverage 規則，後續再與 query planning整合

---

## 10) 與既有計畫銜接

- P1 提供更好的檢索候選
- P2 提供更完整的子題拆解
- P3 在此基礎上做「最終答或拒答」決策

> 建議順序：先完成 P1 穩定版，再上 P3；P2 可同步推進但不阻塞 P3 V1。

---

## 11) 實作狀態（2026-03-15）

已完成並落地於 `langchain_rag`：

- ✅ P3-1：問題要素抽取器
  - `extract_question_signals(question, question_type)`
- ✅ P3-2：evidence analyzer
  - `analyze_evidence(signals, evidence_text, sources)`
- ✅ P3-3：gate engine
  - `run_evidence_gate(signals, evidence, cfg)`
- ✅ P3-4：推論流程串接
  - 在 `answer_question` 內加入 gate 決策
  - `force_refusal` 會覆蓋成標準拒答輸出
- ✅ P3-5：標準拒答模板
  - 使用 config `refusal_text`
  - `reason` 帶 `gate_force_refusal:<reasons>`
- ✅ P3-6：config 擴充
  - 新增 `gate.enabled/min_subquestion_coverage/min_evidence_confidence/hard_rules`
- ✅ P3-7：評測輸出與指標
  - 每題新增：`gate_decision`, `gate_reasons`, `gate_confidence`, `entity_match`, `subquestion_coverage`
  - summary 新增：`gate_force_refusal_rate`, `over_refusal_by_gate`, `missed_refusal_after_gate`
- ✅ P3-8：單元測試與回歸
  - 新增 `tests/test_gate.py`（5 個最小情境）
  - 全部單元測試通過（30 tests）
