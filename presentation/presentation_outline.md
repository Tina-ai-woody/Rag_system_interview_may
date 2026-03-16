# Fubon Interview Presentation Outline

## 目標與定位
這份簡報的核心目標是讓面試官（部門主管）在 10 分鐘內明確看到三件事：

1. 我有完成可運作、可驗證的 RAG 系統（基本分）
2. 我有系統性處理 hallucination（重點評分）
3. 我的方法具備金融場景落地價值（加分）

根據題目要求（金融業務應用 60%、提示技術手法 40%），簡報會採「業務價值先行、技術設計支撐」的敘事方式。

---

## 面試官評分重點（從題目文件反推）

### A. 基本分（必做）
- 建置 RAG 系統並說明設計邏輯
- 使用附件題庫驗證
- 計算 Accuracy
- 回答附上來源依據（頁碼/段落）

### B. 關鍵重點（幻覺排除）
- 明確定義 hallucination（無證據回答/超出文本推論）
- 可操作的判斷方式（證據是否足夠）
- 對年報未揭露題目要能正確拒答

### C. 加分方向
- 差異化方法（檢索、建模、前處理、評估）
- 有意義的 insight（錯誤分析與改進）
- 金融業可落地應用情境

---

## 建議頁數規劃（12~14 頁，15 頁內）

### 1) Executive Summary（1頁）
- 問題定義
- 方法摘要
- 核心成果指標（3~4 個）
- 一句話結論（提升與限制）

### 2) 題目理解與成功定義（1頁）
- 任務要求拆解（Accuracy + Hallucination）
- 題型難度結構：基本 19 / 加分 8 / 困難 3
- 成功標準：正確回答 + 可驗證來源 + 正確拒答

### 3) 資料與評測設計（1頁）
- 資料來源：富邦 113 年報 + 問答集
- 評測流程：Question → Retrieval → Answer → Judge
- 指標：accuracy、refusal precision/recall/F1、citation coverage

### 4) Baseline（起點）架構與結果（1~2頁）
- Baseline 架構（TF-IDF + chunk + 門檻拒答）
- Baseline 成效（如 accuracy = 0.1）
- 問題點（跨頁題、複合題、拒答穩定性不足）

### 5) 改善版 LangChain RAG 架構（2頁）
- Indexing：PDF → chunk → embedding → vector store
- Retrieval：Dense + BM25 + Fusion + Rerank
- Generation：Evidence-constrained prompting + JSON output

### 6) Hallucination 治理（1~2頁，關鍵頁）
- 幻覺定義與風險
- 防護機制：檢索門檻、證據檢查、拒答策略、post-check
- 以「應拒答題」展示 before/after

### 7) 成效比較（1頁）
- Baseline vs Improved（表格）
- 顯示提升指標與未達標項目
- 解釋結果（為何提升、為何仍有短板）

### 8) 錯誤分析與下一步（1頁）
- 錯誤分桶：retrieval error / generation error / refusal error
- 下一輪優化計畫（例如提升 refusal F1、優化 rerank）

### 9) 金融場景落地價值（1頁）
- 客服問答、法遵查核、投資人關係
- KPI 設計（回覆速度、人工覆核成本、風險降低）

### 10) English Abstract（1頁，必備）
- Problem / Method / Key Results / Business Impact

---

## 報告敘事主軸（建議）

建議用以下故事線，讓面試官快速建立信任：

1. **先定義問題與風險**：不只是答對，還要可驗證、可拒答
2. **再展示工程方法**：先 baseline，再有系統地升級
3. **最後用數據說話**：指標提升 + 錯誤分析 + 下一步

這種「問題 → 方法 → 驗證 → 落地」結構，最符合主管視角。

---

## 視覺與呈現建議（面試友善）
- 每頁只回答一個核心問題
- 多用流程圖與對照表，少用長段文字
- 每個指標都加上一句 business 意義
- 對限制坦誠，搭配具體改進計畫（展現成熟度）

---

## 10 分鐘時間分配（建議）
- 1 分鐘：Executive Summary
- 2 分鐘：任務與評測設計
- 3 分鐘：Baseline → 改善版方法
- 2 分鐘：結果與錯誤分析
- 1 分鐘：金融應用落地
- 1 分鐘：結論與下一步

---

## 附註
若後續要進一步製作投影片，可直接從本大綱展開：
- 每個章節拆成 1 頁
- 每頁控制 3~5 個 bullet
- 重要數據以單頁 dashboard 呈現
