---
theme: default
title: Fubon Annual Report RAG System (Restructured v2)
info: |
  Fubon MA Interview - Topic 1
class: text-center
drawings:
  persist: false
transition: slide-left
mdc: true
---

# 富邦年報 RAG 問答系統
## 從 Baseline 失敗到可用系統的優化歷程

許峻瑋 (Chun-Wei Hsu)

---
layout: default
---

## 執行摘要

- 我先建立 baseline，確認「可跑通」但效果不佳
- 再針對痛點分階段優化：**檢索 → 生成 → 評估/拒答**
- 最終相較 baseline，整體表現顯著提升（見 comparison report）
- 目前仍有優化空間：語義題完整率、拒答邊界、rerank 穩定增益

---
layout: two-cols-header
---

# 題目理解與成功定義

::left::
## 任務重點
- 以富邦 113 年報建立 RAG 問答系統
- 依題庫驗證正確率（Accuracy）
- 檢測並避免 hallucination

## 成功定義
- **Correctness**：答案正確
- **Verifiability**：可對照來源

::right::
## 面試官會看的
- **Safety**：資料不足是否拒答
- **Explainability**：是否能說清楚方法與取捨
- **Improvement Story**：是否有系統化迭代證據

---
layout: default
---

# 為什麼 Baseline 成果不佳

## Baseline 設計
- PDF 切塊 + TF-IDF 檢索
- Top-k 抽段落 + 規則判分
- 門檻式拒答

## 主要問題
- 對跨頁、多子題問題整合能力弱
- 檢索召回不足，生成上下文不穩
- 拒答策略粗糙（該拒不拒 / 過度拒答）

---
layout: default
---

# Baseline 結果（起點）

- accuracy_strict：**0.0667**
- accuracy_relaxed：**0.1333**
- final_accuracy：**0.1333**
- refusal_f1：**0.0000**
- avg_coverage_score：**0.1444**

> 結論：Baseline 證明流程可執行，但準確率、覆蓋率、拒答品質都不達實務標準。

---
layout: section
---

# 改善過程（What I changed）

---
layout: default
---

# 改善 1：Retrieval 升級

- 單一路徑 TF-IDF → **Hybrid Retrieval**
  - Dense retrieval（向量）
  - BM25（詞項匹配）
  - RRF 融合
- 導入 reranker（含 fallback）提升候選排序品質
- 目的：先把「找對證據」這件事做穩

---
layout: default
---

# 改善 2：Generation + Refusal 控制

- Prompt 改為 evidence-constrained（只能依 context 回答）
- 統一 JSON 輸出：`answer / refusal / reason / sources`
- 增加 refusal gate：
  - 證據不足就拒答
  - 關鍵數值無法對齊就拒答

---
layout: default
---

# 改善 3：Evaluation 框架重構

- 建立三層評估：
  1. Rule-based correctness（strict/relaxed/coverage）
  2. LLM semantic judge（語意完整與可信度）
  3. Similarity diagnostics（診斷信號）
- 修正 semantic pass 過嚴與聚合不合理問題
- 目的：避免「模型進步了但指標看不出來」

---
layout: section
---

# 成效對照（comparison_report.md）

---
layout: default
---

# Cross-system Comparison（核心指標）

| Metric | Baseline | LangChain | Delta |
|---|---:|---:|---:|
| accuracy_strict | 0.0667 | 0.2333 | +0.1666 |
| accuracy_relaxed | 0.1333 | 0.5667 | +0.4334 |
| final.final_accuracy | 0.1333 | 0.5 | +0.3667 |
| refusal_precision | 0.0 | 0.25 | +0.2500 |
| refusal_recall | 0.0 | 0.5 | +0.5000 |
| refusal_f1 | 0.0 | 0.3333 | +0.3333 |
| avg_coverage_score | 0.1444 | 0.5889 | +0.4445 |
| final.semantic_task_pass | 0.0 | 0.25 | +0.2500 |

資料來源：`artifacts/cross_system/comparison_report.md`

---
layout: default
---

# 成效解讀（給主管看的版本）

- **準確率**：relaxed accuracy 提升 +0.4334，代表可用性大幅改善
- **覆蓋率**：avg coverage +0.4445，代表多子題/多面向回答更完整
- **安全性**：refusal F1 從 0 到 0.3333，代表拒答能力從「幾乎沒有」到「可運作」
- **語義題**：semantic_task_pass 從 0 到 0.25，代表語義題不再全面失敗

---
layout: default
---

# 目前限制與後續改善建議

## 目前限制
- refusal precision 仍偏低（仍有 over-refusal）
- semantic 題型通過率還可再提升
- rerank 增益在不同設定下仍有波動

## 後續建議（優先順序）
1. **Refusal gate tuning**：把 precision 拉高，同時維持 recall
2. **Multi-fact query planning**：先拆子題再作答，提升完整率
3. **Reranker A/B 監控**：固定資料集持續比較 latency/accuracy trade-off
4. **錯題儀表板**：以題型分類追蹤迭代成效

---
layout: two-cols-header
---

# 金融落地價值

::left::
## 應用場景
- 投資人關係（IR）問答
- 法遵/稽核文件檢索
- 內部知識助理

::right::
## 監控 KPI
- accuracy（strict/relaxed）
- refusal F1
- citation coverage
- 高風險問題人工覆核率

---
layout: end
---

# Thank You
## Q & A
