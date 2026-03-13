# LangChain RAG Implementation

依 `implementation_plan/langchain_rag_upgrade_plan.md` 實作的 LangChain 版本 RAG。

## 功能
- `rag-index`: 建立 Chroma 向量索引
- `rag-query`: 單題查詢（含來源頁碼、拒答）
- `rag-eval`: 題庫批次評測（accuracy/refusal/citation）

## 使用
```bash
cd langchain_rag
uv sync

# 建索引
uv run rag-index

# 單題查詢
uv run rag-query --question "富邦金控 113 年度合併稅後淨利是多少？"

# 批次評測
uv run rag-eval
```

## 必要環境變數
- `OPENAI_API_KEY`

可選：
- `OPENAI_MODEL`（預設 `gpt-4o-mini`）
- `OPENAI_EMBEDDING_MODEL`（預設 `text-embedding-3-small`）
