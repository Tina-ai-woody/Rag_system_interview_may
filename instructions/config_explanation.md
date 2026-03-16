本文件整理 `langchain_rag/config.json` 的關鍵設定與實驗建議，方便快速調參。

---

## 1) `retrieval_mode` 是什麼？

`retrieval_mode` 決定檢索流程採用哪一種策略：

- `dense_only`：只用向量檢索（Dense）
- `hybrid_no_rerank`：Dense + BM25 融合（RRF），**不做 rerank**
- `hybrid_rerank`：Dense + BM25 融合後，再做 rerank（目前預設）

### 建議
如果想驗證「rerank 是否造成負增益」，請先切到：

```json
"retrieval_mode": "hybrid_no_rerank"
```

---

## 2) `fusion` 區塊（RRF）

```json
"fusion": {
  "method": "rrf",
  "rrf_k": 60
}
```

### `method: rrf`
代表使用 Reciprocal Rank Fusion 來融合多個檢索器排名（通常是 dense + bm25）。

### `rrf_k` 的意義
RRF 分數近似：

\[
score(d) = \sum_i \frac{1}{rrf_k + rank_i(d)}
\]

- `rrf_k` 越小（如 10）：更偏重前幾名
- `rrf_k` 越大（如 60、100）：排名差距影響更平滑

目前 `rrf_k = 60` 是常見穩健設定。

---

## 3) `dense_top_n` / `bm25_top_n`

```json
"dense_top_n": 20,
"bm25_top_n": 20
```

表示各檢索器先各取前 N 筆候選再進入融合。

- 調大：召回通常上升，但噪音與延遲也上升
- 調小：速度較快，但可能漏掉關鍵證據

---

## 4) `rerank` 區塊

```json
"rerank": {
  "enabled": true,
  "top_k": 5,
  "candidate_pool": 30,
  "model": "heuristic-reranker-v1"
}
```

- `enabled`：是否啟用 rerank
- `candidate_pool`：融合後送入 reranker 的候選數
- `top_k`：rerank 後最終送給 LLM 的文件數
- `model`：reranker 模型名稱

### 若要關閉 rerank

```json
"retrieval_mode": "hybrid_no_rerank",
"rerank": { "enabled": false, "top_k": 5, "candidate_pool": 30, "model": "heuristic-reranker-v1" }
```

---

## 5) `k` 與 `top_k` 差異

- `k`：通常是傳統 retriever（dense_only）直接取回文件數
- `rerank.top_k`：在 hybrid+rereank 下，最終上下文文件數

當使用 `hybrid_rerank` 時，實際最終上下文多由 `rerank.top_k` 主導。

---

## 6) `refusal_text`

```json
"refusal_text": "根據目前提供之富邦 113 年報資料，無法找到直接可驗證的答案，因此不進行推論。"
```

模型判定資料不足時使用的固定拒答句。

---

## 7) `eval` 區塊（三層評分相關）

```json
"eval": {
  "llm_judge_enable_types": ["summary_strategy", "multi_fact"],
  "llm_judge_sample_rate": 1.0,
  "similarity_enabled": true
}
```

- `llm_judge_enable_types`：哪些題型啟用 LLM Judge
- `llm_judge_sample_rate`：LLM Judge 抽樣比例（1.0 = 全部）
- `similarity_enabled`：是否計算 embedding 相似度診斷

---

## 8) 常見實驗配置範例

## A. 基準（目前）

```json
"retrieval_mode": "hybrid_rerank"
```

## B. 驗證 rerank 影響（推薦）

```json
"retrieval_mode": "hybrid_no_rerank",
"rerank": { "enabled": false, "top_k": 5, "candidate_pool": 30, "model": "heuristic-reranker-v1" }
```

## C. 測試 RRF 敏感度

維持其他設定不變，只調：

- `rrf_k = 20`
- `rrf_k = 60`
- `rrf_k = 100`

觀察 `final_context_hit_rate`、`accuracy_relaxed`、`refusal_f1`。

---

## 9) 補充：LLM 模型不是在 config.json 改

回答模型與 embedding 模型目前由 `.env` 控制：

- `OPENAI_MODEL`（回答模型）
- `OPENAI_EMBEDDING_MODEL`（向量模型）

路徑：`projects/Fubon_interview/langchain_rag/.env`
