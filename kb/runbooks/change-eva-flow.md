<!-- 由 tools/build_copilot_kb.py 從 runbooks/change-eva-flow.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊 — 改四眼流程

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。

> 前提知識在 `architecture.md §3`(四眼引擎)與 `architecture.md §4`(資料存取)。**不要整份讀**。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在四眼流程上加檢核、加稽核軌跡、改新增時的預設值、加自訂動作 |
| **不適用** | **改狀態機本身**(例:跳過覆核直接核准)——見 §5,這件事在 repo 裡做不到 |
| 前提 | 先讀懂 `architecture.md §3` 的狀態機與 `EVAType` 值域 |
| 影響半徑 | 依你改哪一層而定,從「一支畫面」到「908 支全中」,見 §2 |

### 0.1 先看清楚:哪些是活的、哪些是死碼

**這是本手冊最重要的一頁。改錯地方會白做一整天,而且不會有任何錯誤訊息。**

| 類別 | 位置 | 子類數 | 狀態 |
|---|---|---|---|
| `BaseEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17-27` | **271** | ✅ **現行主線(單筆)** |
| `BaseMultiRowEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:18-31` | **61** | ✅ **現行主線(多筆)** |
| `BasicEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:24-24` | 66 | ⚠ 舊世代,仍有人用 |
| `MultiRowEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:16-16` | 11 | ⚠ 舊世代,仍有人用 |
| `TA_PO`(2,106 行) | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:19-19` | **0** | ❌ **死碼** |
| `Basic4EyesPO`(4,257 行) | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:28-28` | **0** | ❌ **死碼** |
| `MultiRow4EyesPO` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2428-2428` | **0** | ❌ **死碼** |

`TA_PO` 與 `Basic4EyesPO` 加起來 **6,363 行躺在核心目錄裡,沒有任何東西繼承或實例化它們**。它們僅存的「子類」宣告都是被 `//` 註解掉的行(`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs:18`、`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM694_PO.cs:20`)。

**動手前先確認你那支畫面的 PO 繼承誰:**

```
grep -n "class .*_PO *:" "%ATLAS_ROOT%\Dev\ATLAS.<MOD>\Source\PO\PO.<MOD>\<代號>_PO.cs"
```

看到 `: BaseEVADaoPO` 或 `: BaseMultiRowEVADaoPO` 才是主線。看到 `TA_PO` 或 `Basic4EyesPO`,那支根本沒在跑。

### 0.2 第二件要先知道的:四眼的主體不在 repo 裡

`BaseEVADaoPO` 本體**只做三件事**(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:22-26`、`:143-146`、`:155-227`):鎖死連線為 `("TA", DbServerType.Oracle)`、一個 `AddM` 轉呼叫、一個 `CopyDetail`。

**`Add` / `Update` / `Verify` / `Approve` / `Reject` 這些 EVA 動作本身,全部在 `BaseEVADao`(PTPFBlock,無原始碼)裡。**

所以本手冊能教你的只有一件事:**在框架留給你的掛點上做文章**。掛點在哪、能做什麼、不能做什麼,就是 §3 與 §4。

## 1. 改動點總覽

```text
[圖] 改四眼流程:活的基底與死碼、四眼主體在無原始碼的 DLL 裡、事件掛點是唯一擴充點、四種改法的影響半徑
圖中文字:① 先確認你改的東西是活的 / BaseEVADaoPO / 271 子類 · 現行主線 / BaseMultiRowEVADaoPO / 61 子類 · 多筆主線 / BasicEVAPO · MultiRowEVAPO / 66 + 11 · 舊世代仍有人用 / TA_PO · Basic4EyesPO / 6,363 行死碼 · 改了沒效 / ② 主體不在 repo 裡 / BaseEVADaoPO 本體 / 只做三件事 / BaseEVADao / PTPFBlock · 無原始碼 / Add / Verify / Approve … / 全在 DLL 裡,改不到 / ③ 唯一的正規擴充點:PO 的事件掛點 / BeforeAdd / 參數綁定前 · 改得到 model / DLL 執行 EVA 動作 / 無原始碼 / After* 七個 / 交易未 commit · throw 可回滾 / commit / ④ 影響半徑 —— 選錯不是效率問題是事故 / 某支畫面的 _PO.cs / 1 支 · 預設選這個 / 某支畫面的 _Ctl.cs / 1 支 / BaseEVADaoPO / 271 支全中 · 幾乎不該動 / BaseEVADao / 全系統 · 做不到 / ⚠ 兩個最常見的錯 / handler 少了表名判斷 / 主檔+每個明細各觸發一次 → 跑好幾遍 / After* 只 return 不 throw / 檢核擋了但資料庫有殘留
```

*圖:圖 1 改四眼流程的全貌。灰虛框=死碼,改了沒效果;灰框=PTPFBlock 黑箱,改不到;橘實框=你能動的地方;橘虛框=警告。*

## 2. 先決定:改在哪一層

影響半徑差三個數量級,選錯不是效率問題是事故:

| 改在哪 | 影響 | 什麼時候用 |
|---|---|---|
| **某支畫面的 `_PO.cs` 事件 handler** | **1 支畫面** | 絕大多數需求。**預設選這個** |
| 某支畫面的 `_Ctl.cs` | 1 支畫面 | 需要在轉換 Model↔View 時做事 |
| `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs` | **271 支畫面** | 幾乎不該動 |
| `BaseEVADao`(DLL) | **全系統** | **做不到**,無原始碼 |

> ⚠ **`TA.DataAccess` 是共用引擎。**動 `BaseEVADaoPO` 或 `BasicEVAPO`,271 + 66 支畫面全部跟著變,而且它們分散在 34 個專案資料夾裡,沒有任何自動化測試會告訴你哪裡壞了(repo 內沒有測試專案)。

> **需求如果只影響一支畫面,就不要動共用層。**這句話沒有例外。

## 3. 事件掛點:唯一的正規擴充點

### 3.1 掛點總表

事件宣告在 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:37-94`(Before 15 個)與 `:100-157`(After 15 個);新世代同名事件改吃 `xEVAEventArgs`(PTPFBlock,無原始碼,從呼叫端反推)。

| 掛點 | 何時觸發 | 能改什麼 | **不能做什麼** |
|---|---|---|---|
| `BeforeAdd` | INSERT 指令組好、**參數還沒綁**之前;主檔一次 + **每個明細表各一次** | 改 model 欄位值(會被後續綁定吃進去)、換掉 `args.DbCmd`、`args.Cancel = true` 跳過 | 不能假設只跑一次;不能自己 commit |
| `BeforeSelect` · `BeforeGetMaintainData` · `BeforeGetToDoData` | 查詢 SQL 組好之前 | 整個換掉 `args.DbCmd` | 同上 |
| `AfterGetMaintainData` | 資料已進 model | 往 model 補掛額外資料 | 不能改 `DbCmd`(已執行完) |
| `AfterVerify` · `AfterApprove` · `AfterReject` · `AfterResend` · `AfterDelete` · `AfterUnDelete` · `AfterApproveDelete` | 對應動作成功、**交易尚未 commit** | 在同一交易內再下 SQL(`args.DbTran` 還活著)、寫稽核軌跡、**`throw` 讓整筆回滾** | **不能自己 commit / rollback** |

`args` 拿得到:`args.ModelVDB` · `args.TableName` · `args.DbCmd` · `args.DbTran` · `args.DbTranPTPF`。

### 3.2 ⚠ 每個 handler 第一行都要判斷表名

事件會**對主檔與每一個明細表各觸發一次**。所以 `CASM001_PO` 的每個 handler 開頭都是:

```
if (args.TableName != this.MasterTable.dbTableName) return;
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:571`

**漏掉這一行,你的邏輯會在一次新增裡跑好幾遍。**症狀:流水號跳號、稽核軌跡重複、檢核訊息跳兩次。

### 3.3 訂閱寫在建構子

`CASM001_PO` 在建構子一次訂 12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:40-60`),handler 本體在 `:77-153` 與 `:569-630`。

加一個掛點就是兩步:建構子加一行 `this.<事件> += <handler>;`,再寫 handler。

## 4. 三種常見需求怎麼做

### 4.1 加一條「覆核時檢核」

**寫在 `AfterVerify`,用 `throw` 否決。**

現況範本(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:593-599`)——`CASM001` 七個 `After*` 都是同一個寫法:

```
private void CASM001_PO_AfterVerify(object sender, xEVAEventArgs args)
{
    if (args.TableName != this.MasterTable.dbTableName) return;
    if (!SrNoCommentProcessor.AddCommentHistory(...)) throw new ApplicationException("");
}
```

改法:在 `return` 之後、原有邏輯之前,加你的檢核:

```
if (<檢核不通過>) throw new ApplicationException("<給使用者看的中文訊息>");
```

**`throw` 是 After 掛點唯一能否決整筆交易的手段。**交易此時還沒 commit,例外會讓它整個回滾。

> 範本那七處都 `throw new ApplicationException("")`——**空訊息**。使用者看到的會是空白錯誤框。你自己加的一定要給中文訊息。

### 4.2 加一條「新增時的預設值 / 流水號」

**寫在 `BeforeAdd`,而且必須在參數綁定之前。**

現況範本(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:88-101`):do-while 取流水號 `genSrNo.GetPR_NO()`,用 `IsExistByData` 檢查撞號就重取,取到之後回填到所有明細 row。

兩個要點:

1. **一定要在 `BeforeAdd`。**`architecture.md §4.2` 說明 INSERT 的參數是由 DataRow 的欄位值綁的,`BeforeAdd` 之後才綁——在 `After*` 改 model 沒有用。

2. **主檔改完要記得回填明細。**主明細是分開觸發的,主檔的新值不會自動傳到明細 row。

### 4.3 加稽核軌跡

**寫在對應的 `After*`,用 `args.DbTran` 在同一交易內下 SQL。**

這樣寫的好處是稽核紀錄與業務資料同進同退——業務資料回滾,稽核紀錄也回滾。如果你希望「即使失敗也要留紀錄」,那就**不能**用 `args.DbTran`,要另開連線;但這樣就沒有交易保護,要自己處理失敗。

> `architecture.md §3.7` 提到業務庫與待辦庫是**兩個獨立交易、沒有分散式交易**,而且兩個世代的 commit 順序相反。加稽核軌跡時不要假設它們是原子的。

## 5. 改狀態機本身:在 repo 裡做不到

計劃書原本要求本節說明「改狀態轉換(例:跳過 Verify 直接 Approve)要動 `TA_PO.EVA()` 的哪一段」。**這個問題的前提是錯的:**

1. `TA_PO` 是死碼(§0.1),改它不會有任何效果。

2. 現行主線 `BaseEVADaoPO` 的 EVA 動作全在 `BaseEVADao`(PTPFBlock,無原始碼)裡(§0.2)。

所以狀態轉換的規則、`EVAStatusCode` 的實際字面值、`SetTASecurityData` 怎麼依 `EVAType` 寫欄位,**都在編譯好的 DLL 內,repo 改不到**。

### 5.1 那實務上怎麼辦

| 需求 | 可行做法 |
|---|---|
| 某些條件下**不需要覆核** | 在 `BeforeAdd` 依條件直接把 `STATUS` 設成 `Approve*` 那組值,略過中間狀態。**〔假設〕**——`STATUS` 是 model 的一般欄位,`BeforeAdd` 改得到;但 DLL 後續是否會覆寫它未經驗證 |
| 加一個**新的動作**(例:「暫緩」) | 不要動狀態機。用一個自訂欄位 + 畫面按鈕 + PO 自訂方法實作,不要試圖新增 `EVAType` 值 |
| 改**誰能做哪個動作** | 權限不在 repo(選單 / 權限表不在版控),要在資料庫端處理 |
| 只是想**看懂**目前的規則 | `architecture.md §3.3`(`EVAType` 10 個值)與 `§3.10`(`STATUS` 12 個值),都是反推的 |

> **〔假設〕缺:PTPFBlock DLL 原始碼。**上表第一列的做法未經驗證。要確定得反編譯 `Vendor.Product.DataAccess.dll`,或在測試環境實測一次。**動正式環境前一定要先驗。**

## 6. 多筆(MultiRow)的差異

如果你那支畫面的 PO 繼承 `BaseMultiRowEVADaoPO`(61 支),規則不同:

| 面向 | 單筆 | 多筆 |
|---|---|---|
| 主檔 | `TableMapping MasterTable` 單一 | `List<TableMapping> MasterTable`(`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:20`) |
| 明細 | `List<TableMapping> DetailTable` | **沒有明細概念** |
| 筆數 | Add 時主檔強制恰好 1 筆,否則丟例外(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:194-196`) | 無限制,整張表逐筆跑 |
| 重複檢查 | `IsExistByData` | 多一支 `IsExistByMasterPK`(`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1465-1487`) |
| 複製 | `CopyDetail`(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:155-227`) | `Copy`(`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:49-175`) |

**對事件 handler 的實際影響**:多筆版沒有明細,所以 §3.2 那行表名判斷的寫法要改成比對 `MasterTable` 清單裡的哪一張,不能直接 `!= this.MasterTable.dbTableName`(那是單筆的寫法,多筆時 `MasterTable` 是 `List` 沒有 `.dbTableName`)。

## 7. 四眼欄位與 `STATUS`

加檢核時常需要判斷「現在在哪一段」。

`STATUS` 的 12 個值分三段四動作(`architecture.md §3.10`):

| 段 | 常數 | 意思 |
|---|---|---|
| Entry | `EntryAdd` / `EntryModify` / `EntryDelete` / `EntryUndoDelete` | 輸入完成,待驗證 |
| Verify | `VerifyAdd` / `VerifyModify` / `VerifyDelete` / `VerifyUndoDelete` | 驗證完成,待覆核 |
| Approve | `ApproveAdd` / `ApproveModify` / `ApproveDelete` / `ApproveUndoDelete` | 已覆核,正式生效 |

判斷用 `TAEVAUtility`(`Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs:20-34` 吃 `string Status`,`:41-61` 吃 `DataRow`)。**它們是字串比較不是 enum**,所以拼錯不會編譯失敗。

15 個系統欄位(`DATAID` · `STATUS` · `CREATEID/DATE` · `UPDATEID/DATE` · `ENTRYID/DATE` · `VERIFYID/DATE` · `APPROVEID/DATE` · `REJECTID/DATE` · `DATAFLAG`)**都在 xsd 裡**,由引擎賦值(`runbooks/add-column.md 附錄 C` H8)。**檢核時可以讀,不要寫。**

## 8. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 確認你改的 PO 繼承 `BaseEVADaoPO` 或 `BaseMultiRowEVADaoPO` | 不是死碼基底(§0.1) |
| 2 | 每個新 handler 第一行有表名判斷 | §3.2 |
| 3 | 新增一筆(檢核應通過) | 成功;`STATUS` 進 `Entry*` |
| 4 | 新增一筆(**故意讓檢核不通過**) | 擋下來,**看得到中文訊息**,而且資料庫沒有殘留 |
| 5 | 覆核 / 核准 / 退回 各跑一次 | 狀態正確流轉,檢核在該擋的地方擋 |
| 6 | 有明細的畫面:一次新增多筆明細 | 檢核 / 流水號**只跑一次**(驗 §3.2) |
| 7 | 檢核擋下後查資料庫 | 主檔與明細都沒有半筆殘留(驗交易有回滾) |
| 8 | 若改的是共用層:抽驗**另外三支**不同模組的畫面 | 四眼流程照舊 |

**第 6 步與第 7 步最容易漏。**

## 9. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **改了完全沒反應** | 改到 `TA_PO` / `Basic4EyesPO` 死碼 | §0.1 |
| **檢核跑了好幾遍 / 流水號跳號** | handler 少了表名判斷那一行 | §3.2 |
| **使用者看到空白錯誤框** | `throw new ApplicationException("")` 沒給訊息 | §4.1 |
| **在 `BeforeAdd` 改了值但沒存進去** | 改的是明細但只處理了主檔(事件分開觸發) | §4.2 |
| **在 `After*` 改 model 沒有效果** | 參數早就綁完了 | §4.2 |
| **檢核擋下來了但資料庫有殘留** | 沒有 `throw`,只是 `return` | §4.1 |
| **稽核紀錄跟著業務資料一起消失** | 用了 `args.DbTran`,同進同退 | §4.3 |
| **自己 commit 之後整個流程壞掉** | 掛點內不能 commit / rollback | §3.1 |
| **多筆畫面上 `this.MasterTable.dbTableName` 編不過** | 多筆版 `MasterTable` 是 `List` | §6 |
| **改了共用層,別的模組壞了才發現** | 影響 271 支畫面,沒有自動化測試 | §2 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs` | `:17-27` `:22-26` `:143-146` `:155-227` | §0.1 §0.2 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs` | `:18-31` `:49-175` | §0.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs` | `:24` `:37-94` `:100-157` `:194-196` | §0.1 §3.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs` | `:16` `:20` `:1465-1487` | §0.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs` | `:19` | §0.1 |
| `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs` | `:28` `:2428` | §0.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs` | `:40-60` `:77-153` `:88-101` `:569-630` `:571` `:593-599` | §3 §4 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs` | `:18` | §0.1 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM694_PO.cs` | `:20` | §0.1 |
| `Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs` | `:20-34` `:41-61` | §7 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **PTPFBlock DLL(或其原始碼)** | §0.2 §5 | 四眼動作的主體看不到,所以「改狀態機」只能說做不到。反編譯 `Vendor.Product.DataAccess.dll` 後可補上真正的狀態轉換規則與 `EVAStatusCode` 字面值 |
| **測試環境** | §5.1 | 「在 `BeforeAdd` 直接設 `STATUS` 略過覆核」這個做法未驗證,實測後改成明確可行 / 不可行 |
| **權限表** | §5.1 | 「誰能做哪個動作」查不到 |

## 附錄 C 與計劃書的差異

計劃書 §4 要求本手冊寫「改狀態轉換動到 `TA_PO.EVA()` 的哪一段,以及這是共用引擎、改了 923 支畫面全中」。

實際讀碼後兩點都要修正:

| 計劃書 | 實際 |
|---|---|
| 改 `TA_PO.EVA()` | **`TA_PO` 是死碼**,零繼承零實例化。改它不會有任何效果 |
| 共用引擎改了 923 支全中 | 現行主線是 `BaseEVADaoPO`(**271** 子類)與 `BaseMultiRowEVADaoPO`(**61**),不是 923;而且真正的 EVA 動作在無原始碼的 DLL 裡,repo 內能改的只有掛點 |

「改了很多支畫面全中」這個警告本身**仍然成立**,只是數字與位置不同——所以 §2 保留了它,並給了正確的影響半徑。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 23 · 圖 1 · 表格 12 · 程式錨點 32 · § 連結 43 · 引用檢查：畫面 1（缺 0） · 結果集 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
