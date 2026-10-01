# Copilot 使用說明(本 repo)

本 repo 是 ATLAS 老系統(.NET WinForms + Oracle)的**維護知識庫**,不是程式碼。

- 給人看的是根目錄與 `modules/`、`runbooks/` 下的 HTML;給 Copilot 讀的是 `kb/`(Markdown / TSV)。回答問題時**優先搜尋 `kb/`**,不要讀 HTML(內含大量樣式與內嵌資料)。
- `kb/` 由 `python3 tools/build_copilot_kb.py` 從 HTML 產生,**不要手改**;改了 HTML 就重跑腳本。
- 回答用繁體中文,結論附 `kb/...` 出處;保留原文的「推測」「假設」「版控外」「〔客戶特定〕」標記,查不到就說查不到。
- 專門的問答 agent 定義在 `.github/agents/atlas-kb.agent.md`。
