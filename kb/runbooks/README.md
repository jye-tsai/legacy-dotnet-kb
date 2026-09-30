<!-- 由 tools/build_copilot_kb.py 從 runbooks/README.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊索引

> 共 **9** 本。每一本都是「純程式碼閱讀彙整 + 操作步驟」,附程式錨點,未修改任何 ATLAS 原始碼。

> 共同前提在 `architecture.md`——**不要整份讀**,用它的目錄跳到你要的那一節。

## 1. 我要做這件事,該看哪本

| 我要… | 看哪本 | 從哪節開始 |
|---|---|---|
| 欄位要多一個 | [`add-column.md`](add-column.md) | `§2–§9` |
| 欄位改型別或長度 | [`add-column.md`](add-column.md) | `§0 不適用,先問` |
| 報表要多印一欄 | [`add-report.md`](add-report.md) | `§2 第一列` |
| 報表版面要調 | [`add-report.md`](add-report.md) | `§5` |
| 要一支全新的畫面 | [`add-screen.md`](add-screen.md) | `全篇` |
| 要一支新的查詢畫面 | [`add-query-screen.md`](add-query-screen.md) | `§1 差異表` |
| 要一支新的批次 | [`add-batch.md`](add-batch.md) | `全篇` |
| 覆核時要多一條檢核 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.1` |
| 新增時要自動帶值 / 流水號 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.2` |
| 要加稽核軌跡 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.3` |
| 要改 SP / Function / Trigger | [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | `全篇` |
| SP 在資料庫有、repo 沒有 | [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | `§2` |
| 改完了要送測試 / 正式 | [`deploy.md`](deploy.md) | `§2 對照表` |
| WindowsService 要重裝或改帳號 | [`deploy.md`](deploy.md) | `§5` |
| 新人要把環境架起來 | [`build-env.md`](build-env.md) | `§0.1 三個前提` |
| 編不過 / 改了沒效果 | [`build-env.md`](build-env.md) | `§8 症狀表` |

## 2. 手冊清單

| 手冊 | 一句話 | 適用情境 | 行數 | 圖 | 錨點 |
|---|---|---|---|---|---|
| [`add-column.md`](add-column.md) | 最常用。在既有畫面上加一個欄位 | 在一支既有的 **M(維護)畫面**上,替主表或明細表加一個欄位 | 591 | — | — |
| [`add-screen.md`](add-screen.md) | 從零建一支 M 維護畫面 | 在既有模組裡**從零建一支新的 M(維護)畫面**:主檔 + 明細、走四眼、六層全建 | 752 | — | — |
| [`add-query-screen.md`](add-query-screen.md) | 從零建一支 I 查詢畫面(M 的減法版) | 在既有模組裡**從零建一支 I(查詢)畫面**:唯讀、不寫入、不走四眼 | 452 | — | — |
| [`add-batch.md`](add-batch.md) | 從零建一支 B 批次 | **新建或維護一支 B(批次)畫面**:按一顆執行鈕、跑一段伺服端作業、改 DB 或產檔 | 652 | — | — |
| [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | 加 / 改 PL/SQL 物件 | 改一支既有的 Oracle Stored Procedure / Function / Trigger / View,或新增一支 | 499 | — | — |
| [`add-report.md`](add-report.md) | 加 / 改 Crystal 報表 | 在既有報表上加 / 改欄位;替既有 R 畫面加一個新報表版型 | 292 | — | — |
| [`change-eva-flow.md`](change-eva-flow.md) | 改四眼流程:加檢核、加稽核、改預設值 | 在四眼流程上加檢核、加稽核軌跡、改新增時的預設值、加自訂動作 | 272 | — | — |
| [`deploy.md`](deploy.md) | 部署:改了什麼要佈哪些 | 改完程式要送測試 / 正式環境;或新裝一台伺服器 | 354 | — | — |
| [`build-env.md`](build-env.md) | 建置環境:新人第一天 | 新人拿到 ATLAS 原始碼,要把它變成「編得起來、跑得動」的開發機 | 224 | — | — |

## 3. 讀之前先知道的四件事

這四條在多本手冊裡重複出現,因為它們是「照直覺做就會錯」的地方:

| # | 事實 | 為什麼會咬人 | 在哪 |
|---|---|---|---|
| 1 | Remoting 邊界在 **UI 與 FormProxy 之間** | 決定改哪層佈哪台;搞錯的症狀是「我這台好了,別人還是舊的」 | `architecture.md §8.1` |
| 2 | **25 個組件在 repo 有原始碼,卻被綁成預編 DLL** | 重編不更新 `PTPFBlock` 就沒效果,而且開發機上看不出來 | `architecture.md 附錄 C.5` |
| 3 | **程式呼叫 380 支 SP,repo 只有 61 支有腳本** | 批次與報表的邏輯大量在版控外 | `architecture.md 附錄 B.0` |
| 4 | **`TA_PO` 與 `Basic4EyesPO` 共 6,363 行是死碼** | 改了完全沒反應,也不會報錯 | `runbooks/change-eva-flow.md §0.1` |

## 4. 共同工具

```
py -V:3.12 \docs\tools\atlas_scan.py --screen <代號>
py -V:3.12 \docs\tools\atlas_scan.py --table <表名>
```

改過 ATLAS 原始碼後加 `--refresh` 重掃。**不要 Read `*.Designer.cs`**(一支 5,375 行,全庫 2,190 支)。

## 5. 每本手冊都標了什麼

| 標記 | 意思 |
|---|---|
| **〔假設〕缺:輸入** | 拿不到該輸入(DB 連線 / PTPFBlock DLL / 選單表),只能從結構推論。各本附錄 B 彙整 |
| **〔客戶特定〕** | 本站台的值(主機名、路徑、機構代碼),其他站台不同 |
| 附錄 A | 該本引用的檔案與錨點清單 |
| 附錄 B | 待輸入回填:補進來之後要改哪幾段 |

由 build_doc.py v2.0.0 於 2026-09-15 17:58 產生 · 標題 6 · 圖 0 · 表格 4 · 程式錨點 0 · § 連結 0 · 引用檢查：

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
