# ATLAS 知識庫(去識別化版)

一套老 .NET WinForms + Oracle 系統的**維護知識庫**,純讀原始碼彙整而成,已去識別化。
給「一個人接手一套沒人記得細節的老系統」的工程師用。

**入口:[index.html](index.html)**(全部離線可讀,雙擊即開,不需要 server、不需要網路)。

## 裡面有什麼

| 區 | 內容 |
|---|---|
| 系統介紹 `OVERVIEW.html` | 業務軸:六條業務線、一日作業時序、7 張端到端流程圖 |
| 技術架構 `architecture.html` | 六層架構、.NET Remoting 邊界、四眼(覆核)引擎、資料庫,7 張圖 |
| 模組文件 `modules/` 29 篇 | 一篇一模組:邊界、資料模型、畫面清冊、逐畫面卡控、跨模組依賴、已知缺陷 |
| 維護手冊 `runbooks/` 9 本 | 加欄位、加畫面、加查詢、加批次、加報表、改覆核流程、改 SP、部署、建環境 |
| 離線查詢頁 | `query.html` 代號 / 表名反查 · `messages.html` 錯誤訊息反查 · `defects.html` 缺陷總表(可篩可排) |
| 導覽 | `CHEATSHEET.html` 一頁速查卡 · `TROUBLESHOOT.html` 症狀 → 先看哪 |

規模:畫面 911 支 · 實體表 437 張 · 報表範本 608 張 · 已知缺陷 1,682 條。

## 怎麼做出來的

- **全部來自靜態讀碼**,沒有連過任何執行環境或資料庫;凡是讀不到的(版控外的 SP、資料庫值域、選單權限)都標「假設」或「版控外」,不編造。
- 每個結論附程式錨點(檔案路徑 + 行號);公開版把錨點改為純文字。
- 文件用工具鏈產生並逐項驗證:引用檢查(畫面 / 表 / SP 缺 0)、錨點行號實看、跨文件章節引用 0 未解析、圖無溢出。
- 系統名、客戶名、廠商名、主機名、內網位址、開發者姓名已替換為中性代號;替換規則有殘留掃描,公開版為 0 殘留。

## 怎麼讀

1. `OVERVIEW.html` §0 一頁摘要 + 圖 F1,知道有哪六條線。
2. `CHEATSHEET.html` 印出來。
3. `architecture.html` §1–§3,搞懂六層與覆核引擎。
4. 自己負責的模組那一篇。
5. 要動手時翻 `runbooks/`;卡住時翻 `TROUBLESHOOT.html`。

## 當成 GitHub Copilot agent 使用

repo 已附一個 Copilot 自訂 agent:**`atlas-kb`**(`.github/agents/atlas-kb.agent.md`),只讀 `kb/`,回答附出處、不編造。

| 檔案 | 用途 |
|---|---|
| `.github/agents/atlas-kb.agent.md` | agent 定義:角色、鐵律、「問什麼 → 查哪裡」路由表、回答格式 |
| `.github/copilot-instructions.md` | 一般 Copilot Chat 也會讀到的 repo 說明 |
| `kb/` | HTML 轉出的 Markdown(45 篇)+ 查詢頁資料(`screens.md` / `tables.md` / `objects.md` / `messages.tsv` / `defects.tsv`),約 7 MB,方便 Copilot 搜尋 |
| `tools/build_copilot_kb.py` | 重新產生 `kb/`(只用 Python 標準函式庫) |

**怎麼用**

- **VS Code**:用 VS Code 開這個 repo → Copilot Chat → 上方 agent 下拉選 `atlas-kb` → 直接問,例如「`CASM001` 存檔時檢核哪些欄位?」「使用者看到『資料已被其他使用者異動』是哪裡丟的?」「`CAS003A` 要加欄位要改哪些檔?」
- **github.com**:在 Copilot 對話或指派 Copilot coding agent 時選 `atlas-kb`。
- **搭配真正的 ATLAS 原始碼**:把 `.github/agents/atlas-kb.agent.md` 與 `kb/` 複製到原始碼 repo,agent 就能一邊查知識庫、一邊看實際程式;若希望它也能改程式,在 frontmatter 的 `tools` 加上 `'edit'`。

**HTML 更新後**:重跑 `python3 tools/build_copilot_kb.py`,連同 `kb/` 一起 commit。

## 注意

- 這是**快照**,以產生日期為準;與現行程式不符時以程式為準。
- 內容保留了系統結構、代號、表名與已知缺陷位置——去識別化拿掉的是「這是誰的」,不是「長什麼樣」。
