# FastAPI_plan_v1

## 目標
將 `rag_demo/api/langchain_rag` 既有功能封裝成可被 Web Demo 呼叫的 FastAPI 服務，先達到「功能等價 + 可觀測 + 可維運」三件事：
1. 保留 CLI 版能力（index / query / eval）
2. 提供穩定 API 合約（request/response schema）
3. 提供可部署、可測試、可除錯的服務骨架

---

## 現況盤點（來自 langchain_rag）
目前核心能力在 `src/langchain_rag_app`：
- `build_index()`：建立 Chroma index
- `answer_question(question, question_type="")`：單題問答（含 gate/refusal/retrieval_debug）
- `eval_cmd()`：題庫批次評測，輸出 artifacts
- `load_config()` / `parse_xlsx_questions()` 等工具函式

CLI 對應能力：
- `rag-index`
- `rag-query --question ...`
- `rag-eval`

---

## API 封裝範圍（v1）

### 1) 健康檢查與服務資訊
- `GET /healthz`
  - 用途：liveness probe
  - 回傳：`{"status":"ok"}`
- `GET /readyz`
  - 用途：readiness probe（可檢查 config、env、索引存在性）

### 2) 單題問答（核心）
- `POST /v1/rag/query`
- Request (草案)
  - `question: str` (required)
  - `question_type: str | null` (optional)
  - `include_debug: bool = false`（是否回傳 retrieval_debug/evidence）
- Response (草案)
  - `answer: str`
  - `refusal: bool`
  - `reason: str`
  - `sources: int[]`
  - `gate: object`（可先保持 dict）
  - `retrieval_debug: object | null`（依 include_debug 決定）

### 3) 建索引
- `POST /v1/rag/index`
- 用途：觸發 `build_index()`
- Response：`{"chunks": number, "status": "completed"}`

### 4) 批次評測（先同步版）
- `POST /v1/rag/eval`
- 用途：觸發目前 eval 流程，寫出 artifacts
- Response（精簡）
  - `summary: object`（等價 `eval_summary.json`）
  - `artifacts: {results_path, summary_path, retrieval_debug_path}`

> 備註：v1 先同步執行，若耗時過長，v2 再改 background job + job status。

---

## 建議目錄結構（FastAPI_implementation）

```text
FastAPI_implementation/
  app/
    main.py               # FastAPI app entry
    api/
      v1/
        rag.py            # routers
    schemas/
      rag.py              # Pydantic models
    services/
      rag_service.py      # 包裝 langchain_rag_app.core / eval
    core/
      config.py           # env / path / settings
      logging.py
    dependencies.py
  tests/
    test_health.py
    test_rag_query.py
  pyproject.toml or requirements.txt
  README.md
```

---

## 實作策略

### Phase 0 — 骨架與可啟動
- 建立 FastAPI app + router
- 加入 CORS（web_demo 呼叫需要）
- 完成 `/healthz` `/readyz`
- 補最小 README（如何啟動）

### Phase 1 — Query API（最高優先）
- 建立 `QueryRequest/QueryResponse`
- 服務層呼叫 `answer_question()`
- 例外處理：
  - API key 缺失
  - 索引不存在
  - 上游 LLM error
- 統一錯誤格式（HTTPException + detail code）

### Phase 2 — Index API
- 包裝 `build_index()`
- 加簡單鎖（避免同時重複建索引）
- 回傳 chunk 數

### Phase 3 — Eval API
- 抽出 eval service（避免直接調 CLI）
- 回傳 summary 與 artifacts 路徑
- 先同步執行，並在文件中標註可能耗時

### Phase 4 — 測試與整合
- 單元測試：health/query/index 基本流程
- 合約測試：response schema
- 與 `web_demo` 做一次端到端串接

---

## 關鍵設計決策（v1）
1. **重用既有核心，不重寫演算法**：FastAPI 只做 transport/adaptation layer。
2. **先同步、後非同步**：避免過早複雜化，先讓 Web 能穩定 call。
3. **debug 資訊可控**：`include_debug` 控制回傳大小與敏感資訊。
4. **錯誤碼可前端判斷**：例如 `INDEX_NOT_FOUND`、`MISSING_API_KEY`、`UPSTREAM_LLM_ERROR`。

---

## 風險與對策
- **風險：eval 太慢導致 timeout**
  - 對策：v1 設較長 timeout；v2 改背景任務
- **風險：env/path 相依於目前目錄結構**
  - 對策：集中在 `core/config.py` 管理基底路徑
- **風險：回傳 payload 太大**（retrieval_debug/evidence）
  - 對策：預設關閉 debug，必要時才開
- **風險：併發下重複建索引**
  - 對策：index endpoint 加 process lock

---

## Definition of Done（v1）
- [ ] `uvicorn` 可啟動 API 服務
- [ ] `POST /v1/rag/query` 可回覆與 CLI 等價結果
- [ ] `POST /v1/rag/index` 可成功建索引並回傳 chunks
- [ ] `POST /v1/rag/eval` 可產生 summary 與 artifacts 路徑
- [ ] 基本測試可執行
- [ ] 提供給 `web_demo` 的 API 文件（至少含 request/response 範例）

---

## 下一步（我建議）
1. 先落地 Phase 0 + Phase 1（讓 Web 先能問答）
2. 再補 Phase 2（索引管理）
3. 最後補 Phase 3（評測 API）

如果你同意，我下一步會直接在 `FastAPI_implementation` 建立 v1 骨架，先把 `/healthz` + `/v1/rag/query` 做出來。