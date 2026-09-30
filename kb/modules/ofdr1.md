<!-- 由 tools/build_copilot_kb.py 從 modules/ofdr1.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFDR1 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:**第一次讀報表畫面的人,只讀 §0.2 那張 M / I / R 三欄對照表就夠用**——全庫 189 支報表都以它為前提。要動手改某一支的人,查 §3 清冊定位,再跳 §7 的對應小節。急著知道哪裡會咬人的人直接翻附錄 E。加新報表的步驟另有前人寫的 `add-report.md`,本文不重複那 292 行,只補它沒講的:**實際長出來的 40 支跟那份步驟書差在哪**。

> ⚠ **OFDR1 不是一個業務模組,是一份切片。** 這是全庫第一篇專門寫**報表畫面(R)**的文件。OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD.Report` 這個獨立方案底下的 **40 支 R 畫面**(方案內實有 45 支,另 5 支 `OFDR285` `OFDR287` `OFDR461` `OFDR561` `OFDR562` 劃給下一片)。切片依據是專案資料夾與型別碼,不是業務;所以本片內部含**八條互不相干的業務線**(§0.5)。名稱 `OFDR1` 為**推測**,取自「OFD 的 R 畫面第 1 片」。

> ⚠ **前 24 篇都是 M(維護)/ B(批次)/ I(查詢)。** 本篇建立的章節配置會被後續報表片沿用:**§4 §5 §6 全空、§7 才是主體**,而且 §2 多一張 M / I 都沒有的表——**`.rpt` 對應表**(§2.6)。

> ⚠ **「報表唯讀」是錯的。** 本片 40 支裡 **7 支的 PO 帶寫入路徑**(`ExecuteNonQuery`),其中 2 支(`OFDR022` `OFDR023`)根本不是報表、UI 基底是 `xOneStepProcessForm`。細節見 §0.3 與 §7.12。把 R 當唯讀去做影響面評估會漏。

> ⚠ **〔客戶特定〕**:集保(TDCC)平台代號 `FUY` / `FUS`、亞太基金受益人大會的十種票別編號(`0`~`9`)、退休財富管理月報的欄位配置為本站台的值。

> ⚠ **〔共用〕**:基金基本資料與受益人主檔幾乎每一支的 SP 都讀,改欄位會同時打到本片十幾支報表(見 §8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別四種看 `architecture.md §6`。**不要整份讀**。I 畫面的對照基準全部取自 `ofdi1.md §0`。

## 0. 系統邊界與角色

```text
[圖] M I R 三種畫面的層級結構差異,R 多出第七層 Crystal
圖中文字:M 維護畫面:六層 + 四眼寫回 / UI xMaintainForm / 兩個 TabPage 掛 Add Modify / Pxy / Add Modify Delete Select / Ctl BaseController / InitializeVDBTypes 有覆寫 / PO BaseEVADaoPO / MasterTable + DetailTable / I 查詢畫面:同樣六層,MasterTable 與四眼整組消失 / UI xOneStepProcessForm / 一頁式 一顆查詢鈕 / Pxy / GetData 單一入口 / Ctl BaseController / 三支連 BaseController 都沒繼承 / PO 三派並存 / 無基底 20 BaseEVADaoPO 12 BasicEVAPO 3 / R 報表畫面:多出第七層 Crystal,PO 退成兩派,加回一整套列印前檢核 / UI xReportForm / 查詢 預覽 列印 三顆鈕 38 支 / Pxy / GetData 加上各自的檢核方法 / Ctl BaseController / 26 支有 14 支無基底宣告 / PO 兩派 / I 代號 PO 介面 26 支 Basic_PO 13 支 / Model.xsd 結果集形狀 / 根節點是畫面代號 不是表名 / View.xsd 同構 / TransferVDBHelper 整表搬 / .rpt 內部第三份 schema / 二進位 改了不會編譯錯 / 第七層 CrystalReports Report.OFD / SetRptSchemaOnDoc 綁 schema 再 SetParameterValue 補抬頭 這一段沒有編譯期檢查 / 三者唯一相同的地方:查詢條件都走 Util.Parameters 這個字串 key-value 袋 / M 從 Model 資料列逐欄搬 / 參數化 UPDATE INSERT / I 從 Parameters 袋撈 / 13 支直接串進 SQL / R 從 Parameters 袋撈 / 36 支走 SP 具名參數 3 支串接
```

*圖:圖 2 M / I / R 層級對照,對應 §0.2 那張三十列的表。三排由上到下是 M、I、R;R 那排底下再展開第五到第七層。紫框=風險點:I 的三派 PO 有一派開畫面就壞,R 的第七層完全沒有編譯期保護。要記一件事就記:R 的資料層跟 I 一樣空,差別全在輸出端與檢核端。*

### 0.1 先破除一個假設:報表是**七層**,不是六層

M / I / B 三種畫面都是六層。**報表多一層**:Crystal Reports 專案 `Report.OFD`。七層在 `Dev/ATLAS.OFD.Report/Source` 底下的實際落點,已逐層 `ls` 核對:

| 層 | 資料夾 | csproj | 檔名慣例 | 例 |
|---|---|---|---|---|
| 1 UI | `Source/UI/ReportUI.OFD/` | `ReportUI.OFD.csproj` | `<代號>.cs` | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs` |
| 2 FormProxy | `Source/FormProxy/ReportFormProxy/` | `ReportFormProxy.OFD.csproj` | `<代號>_Pxy.cs` | `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR001A_Pxy.cs` |
| 3 Control | `Source/Control/ReportControl.OFD/` | `ReportControl.OFD.csproj` | `<代號>_Ctl.cs` | `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR001A_Ctl.cs` |
| 4 PO | `Source/PO/ReportPO.OFD/` | `ReportPO.OFD.csproj` | `<代號>_PO.cs` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs` |
| 5 DataEntity | `Source/Entity/ReportDataEntity.OFD/` | `ReportDataEntity.OFD.csproj` | `<代號>Model.xsd` | `Dev/ATLAS.OFD.Report/Source/Entity/ReportDataEntity.OFD/OFDR001AModel.xsd` |
| 6 UIEntity | `Source/Entity/ReportUIEntity.OFD/` | `ReportUIEntity.OFD.csproj` | `<代號>View.xsd` | `Dev/ATLAS.OFD.Report/Source/Entity/ReportUIEntity.OFD/OFDR001AView.xsd` |
| **7 CrystalReports** | `Source/CrystalReports/Report.OFD/` | `Report.OFD.csproj` | **`<代號>RPS.rpt` + 同名 `.cs`** | `Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/OFDR001ARPS.rpt` |

**兩個資料夾命名不對稱,會讓 `find` 寫錯**:

1. **FormProxy 那層的資料夾沒有 `.OFD` 後綴**(`ReportFormProxy/`),但**裡面的 csproj 有**(`ReportFormProxy.OFD.csproj`)。其餘六層資料夾與 csproj 同名。

2. 第 7 層的資料夾叫 `Report.OFD`,不是 `ReportCrystal.OFD`,跟前六層的 `Report<層名>.OFD` 構詞相反。

### 0.2 M / I / R 三欄對照表(**本篇最重要的一張表,後面 189 支報表靠它**)

M 欄取自 `architecture.md §6` 的通則; I 欄**全部是 `ofdi1.md §0` 的 35 支實測值,直接引用不重算**; R 欄是本片 40 支逐支核對的結果。**「差異性質」欄寫的是 R 相對 M / I 的位置。**

| # | 面向 | M 維護畫面 | I 查詢畫面(`ofdi1.md §0` 實測 35 支) | **R 報表畫面(本片實測 40 支)** | 差異性質 |
|---|---|---|---|---|---|
| 1 | **層數** | 六層 | 六層(6 支退化成四層,缺 xsd) | **七層。多出 `Source/CrystalReports/Report.OFD`**(§0.1) | **R 獨有** |
| 2 | 層數退化 | — | 6 支缺 Model / View xsd | **0 支缺。40 支的 Model.xsd 與 View.xsd 全齊**(§0.1 逐層 `ls` 核對) | R 比 I 完整 |
| 3 | **UI 基底** | `xMaintainForm` | **`xOneStepProcessForm`,35 支無一例外** | **`xReportForm` 38 支;`xOneStepProcessForm` 2 支**(`OFDR022` `OFDR023`) | **第三種基底** |
| 4 | 那 2 支例外是什麼 | — | — | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR023.cs:15` 的 `xOneStepProcessForm`——**它們不印報表,是掛在報表專案下的「執行型」畫面**(§7.12) | 分類錯置 |
| 5 | UI 頁籤 | 查詢頁 + 維護頁兩個 TabPage | 一頁式,一個「查詢」按鈕 | **一頁式,但有三顆按鈕:查詢 / 預覽 / 列印**(`ButtonPreviewEnable` `ButtonPrintEnable`,例 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:172-173`) | R 獨有 |
| 6 | **UI 的列印生命週期** | 無 | 無 | **`BeforePrintButtonClicked` → `SetQueryParameters(rpt, rpt, 中文名)` → `ReportLoad` → `SetRptSchemaOnDoc()` → `m_ReportDocument.SetParameterValue(...)`**(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:248-296`) | **R 獨有,是本片主軸** |
| 7 | **PO 基底** | `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` | 三派:`BaseEVADaoPO` 12 / `BasicEVAPO` 3 / 無基底 20 | **兩派:只實作自家介面 `I<代號>_PO` 共 26 支 · `Basic_PO` 共 13 支 · 完全無基底無介面 1 支(`OFDR288`)** | **與 I 的三派不同** |
| 8 | 有沒有 `BasicEVAPO` | — | 3 支,開畫面就 NRE(`ofdi1.md §5`) | **0 支。本片沒有任何一支繼承 `BasicEVAPO`**,所以 `ofdi1.md` 那個 NRE 缺陷型在 R 不存在 | **缺陷型不適用** |
| 9 | `Basic_PO` 是什麼 | — | — | 框架 DLL 類別,**無原始碼,從呼叫端反推**。13 支 `Basic_PO` 派全都是**早期**畫面(SP 名無 TA 中綴,§2.2) | R 專有分派 |
| 10 | **PO 介面** | `I<代號>_PO : IEvaDataAccess` | 只有 8 支寫 `: IEvaDataAccess` | **26 支宣告 `I<代號>_PO`,但一支都沒有 `: IEvaDataAccess`。介面裡只有 `GetXxx<T>(T model, params object[] args)` 一類取數方法**(例 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:12-21`) | 介面留著,EVA 掉光 |
| 11 | **`MasterTable` 宣告** | 建構子必宣告,是全庫「實體表」清單來源 | **35 支全無** | **40 支全無。** `grep -c MasterTable` 在 `ReportPO.OFD` 全目錄是 0 | **與 I 一致** |
| 12 | `DetailTable` 宣告 | 有 | 35 支全無 | **40 支全無** | 與 I 一致 |
| 13 | 那實體表清單從哪來 | `MasterTable` | PO 的 `LoadDataSet(..., model.DataEntity.<結果集>.TableName)` | **同 I,但再往下一層**:`LoadDataSet` 的第三參是**結果集名**,真實表名只存在 **SP 內部**(§2.1)。**36 支報表的取數 SQL 完全不在版控**,比 I 更不透明 | **R 更黑箱** |
| 14 | **四眼 13 欄** | 每表一整組,PO 掛 10 個事件 | **0 個** | **0 個。40 支 PO 沒有任何 `BeforeAdd` / `AfterVerify` / `AfterApprove` 掛鉤** | 與 I 一致 |
| 15 | 四眼欄位會不會出現在輸出 | — | 會,當顯示欄 | 會,而且是報表上印出來的「製表人 / 覆核人」欄 | 語意同 I |
| 16 | **`Model.xsd` 的角色** | 實體表形狀 | **結果集形狀**,根節點是畫面代號 | **結果集形狀,根節點是畫面代號。40 支全部如此**(例 `Dev/ATLAS.OFD.Report/Source/Entity/ReportDataEntity.OFD/OFDR001AModel.xsd`) | 與 I 一致 |
| 17 | `View.xsd` 的角色 | 與 Model 同構,`Ctl` 逐欄手搬 | 多半同構,2 支欄數對不上 | 同構,`Ctl` 用 `TransferVDBHelper.TransferTable` 整表搬(§0.4) | 與 I 一致 |
| 18 | **第三份 schema** | 無 | 無 | **有。`.rpt` 內部也存一份欄位 schema**,靠 `SetRptSchemaOnDoc()` 綁 Model。**`.rpt` 是二進位、schema 改了不會編譯錯**——這是 R 獨有的最大破口(附錄 E) | **R 獨有風險** |
| 19 | **`Ctl` 基底** | `BaseController` | 32 支 `BaseController`,3 支無 | **26 支 `BaseController`(即 `I<代號>_PO` 派);14 支 `Ctl` 沒有基底宣告**(`Basic_PO` 派 13 支 + `OFDR288`) | 兩派對齊 PO |
| 20 | **寫入路徑** | `Add` / `Modify` / `Delete` + 四眼四段 | **零。35 支 PO 無任何 `ExecuteNonQuery`** | **7 支有 `ExecuteNonQuery`**:`OFDR022` `OFDR023` `OFDR452` `OFDR453` `OFDR455` `OFDR457` `OFDR564`(§7.12) | **R 不是唯讀** |
| 21 | 寫入在做什麼 | 業務資料異動 | — | 兩類:**(a) 改業務旗標**(`OFDR022` `OFDR023` 標記已寄送、`OFDR564` 標記已通知)、**(b) 請款作業把計算結果寫進暫存工作區再讀回**(`OFDR452` `OFDR453` `OFDR455` `OFDR457`,§7.8) | 副作用 |
| 22 | **查詢條件從哪來** | Model 資料列逐欄搬 | `model.Utility.Parameters` key-value 袋 | **同 I,`ResultVDB.Util.Parameters.AddParametersRow(欄名, SQLOperator, 值)`**(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:161-162`) | 與 I 一致 |
| 23 | **條件怎麼進 SQL** | 參數化 | **13 支直接字串串接**(I 最大風險) | **36 支走 SP 具名參數(`AddInParameter`),4 支在 C# 自組 SQL、其中 3 支字串串接**(§2.3) | **R 比 I 安全得多** |
| 24 | 為什麼 R 比 I 安全 | — | — | 因為 R 幾乎全走 SP:SP 名寫死在 PO,條件透過 `AddInParameter` 具名綁定,**攻擊面被 SP 簽名擋住**。`ofdi1.md` 的 13 支串接問題在 R 只剩 3 支 | 結構性差異 |
| 25 | **輸出介面** | 存回 DB | 畫面 Grid | **三種:Crystal 預覽 / 列印(36 支)· Excel 檔(2 支 `OFDR237` `OFDR453`)· 無輸出只改狀態(2 支 `OFDR022` `OFDR023`)** | **R 獨有** |
| 26 | **報表中文名在哪** | 選單表 | **不存在 code 內,只能由控件標題反推**(`ofdi1.md §0`) | **在 code 裡,`SetQueryParameters` 的第三參就是報表中文名**——`grep -n "SetQueryParameters" *.cs` 一次撈齊(§3) | **R 比 I 好查** |
| 27 | 中文名可靠嗎 | — | — | 大致可靠,但有**兩支被 cp950 編碼污染**(`OFDR511` `OFDR513`,附錄 E)、一支**傳空字串**(`OFDR716` 第三分支,附錄 E) | 有雜訊 |
| 28 | **例外處理** | 走 `ImsError` 階層 | 兩派混用,5 支兩個都做 | **一派為主:`catch (Exception ex)` → `AddResultRow(false, 0, ex.Message)`,把 Oracle 錯誤原文貼到畫面**;部分再 `throw` | 與 I 近似 |
| 29 | **DB 型別** | — | Oracle | **Oracle。PO 一律 `[PODbType(DbServerType.Oracle)]` + `new Database("TA", DbServerType.Oracle)` + `OracleDbType.RefCursor` 出參**(`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:23-26`) | 與 I 一致 |
| 30 | **卡控** | 四眼 + 存檔前檢核 | 過濾(無提示)為主 | **四類都有:阻擋(`ValidateErrList` + `e.Cancel = true`)· 警示 · 詢問 · 過濾(無提示)**。R 的阻擋比 I 多,因為列印前要驗營業日 / 已過帳(§7 各節、§7.13 總表) | **R 卡控比 I 重** |

### 0.3 三句話版本

給沒空看上表的人:

1. **R = I 的取數模型 + 一層 Crystal + 三顆按鈕 + 比 I 硬得多的前置檢核。** 資料層(無 `MasterTable`、xsd 是結果集形狀、`Parameters` 袋子傳條件)跟 I 一模一樣,差別全在輸出端與檢核端。

2. **R 不是唯讀。** 7 / 40 支會寫 DB,2 支根本不印報表。

3. **R 的真正商業邏輯不在 C#,在 SP 裡,而 SP 不在版控。** 本片 40 支引用的 SP / Function **全部找不到原始碼**(§2.2)。C# 那層只負責組參數、接 RefCursor、丟給 Crystal。**要查「這張報表為什麼少一列」,讀 C# 是白費力氣——要去 DB 撈 SP 原始碼。**

### 0.4 資料怎麼從 SP 流到 `.rpt`

以 `OFDR001A` 為例,七層一條線走完(錨點逐段標):

| 步 | 在哪 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | UI | 使用者選基金 + 資料日期,按「查詢」 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:152` |
| 2 | UI | 驗營業日 + 驗已過帳,不過就 `AddError` 擋住 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:34-63` |
| 3 | UI | 條件塞進 `ResultVDB.Util.Parameters` | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:161-162` |
| 4 | FormProxy | `GetData(VDB)` 送過 WCF | `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR001A_Pxy.cs` |
| 5 | Control | 建 Model VDB、呼叫 PO、`TransferVDBHelper.TransferTable` 把 Model 表搬成 View 表 | `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR001A_Ctl.cs` |
| 6 | PO | `GetStoredProcCommand("s_TA_OFDR001A_Get")` + `AddInParameter` ×2 + `AddOutParameter(RefCursor)` + `LoadDataSet` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:42-51` |
| 7 | UI | 列印前檢核過了,`SetQueryParameters("OFDR001ARPS", "OFDR001ARPS", "基金結餘單位數查核表")` | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:280` |
| 8 | UI | `ReportLoad` 事件:`SetRptSchemaOnDoc()` 把 View 的 schema 綁上 `.rpt`,再逐個 `SetParameterValue` 補抬頭參數 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:288-296` |
| 9 | CrystalReports | `OFDR001ARPS.rpt` 照 schema 排版輸出 | `Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/OFDR001ARPS.rpt` |

第 8 步的 `SetRptSchemaOnDoc()` 與 `m_ReportDocument` 都來自 `xReportForm`,**無原始碼,從呼叫端反推**。 **第 8 步是唯一把 C# 與 `.rpt` 綁在一起的地方,而它沒有編譯期檢查**——`.rpt` 少一個欄位,要跑起來才知道(附錄 E)。

### 0.5 這 40 支涵蓋哪些業務線(推測,依報表中文名與 SP 名歸類)

中文名取自 `SetQueryParameters` 第三參,**是 code 裡的字面值,不是猜的**;業務線分組是**推測**。

| 業務線 | 支數 | 代號 | 依據 |
|---|---|---|---|
| **A. 受益人資料與客服** | 7 | `OFDR013` `OFDR014` `OFDR015` `OFDR034` `OFDR035` `OFDR040` `OFDR043` | 中文名「受益人查詢記錄報表」「客服通聯服務統計表」「客戶補件通知書」「受益人退郵資料」等 |
| **B. 集保(TDCC)往來** | 7 | `OFDR021` `OFDR024` `OFDR563` `OFDR564` `OFDR716` `OFDR751` `OFDR752` | 中文名帶「集保」;`OFDR716` 的 `FUY` / `FUS` 也是集保平台代號〔客戶特定〕 |
| **C. 基金單位數與淨值** | 3 | `OFDR001A` `OFDR002A` `OFDR236` | 「基金結餘單位數查核表」「基金結餘單位數查核清冊」「淨值月報表」 |
| **D. 收益分配(配息)** | 4 | `OFDR281` `OFDR282` `OFDR286` `OFDR288` | 「收益分配名冊」「收益分配付款彙總表」「收益分配扣繳憑單」「配息專戶明細表」 |
| **E. 手續費與服務費請款** | 4 | `OFDR452` `OFDR453` `OFDR455` `OFDR457` | 「服務費明細表」「申購手續費請款總表」「買回手續費請款總表」 |
| **F. 銷售與行銷統計** | 5 | `OFDR235` `OFDR237` `OFDR238` `OFDR239` `OFDR501` | 「促銷活動明細表」「每日銷售單位彙總表」「銷售預估明細表」「行銷身分群組明細表」 |
| **G. 基金合併與清算** | 4 | `OFDR495` `OFDR511` `OFDR512` `OFDR513` | 「基金合併確認單」「基金清算名冊列印作業」「基金清算資料彙總表」 |
| **H. 法規申報與會議** | 3 | `OFDR540` `OFDR731` `OFDR733` | 「亞太基金受益人大會開票結果」「結匯申報收檔查核表」「國內貨幣市場共同基金受益憑證持有者統計表」 |
| **X. 不是報表** | 2 | `OFDR022` `OFDR023` | `xOneStepProcessForm`,無 `.rpt`,只改 DB 狀態(§7.12) |

加總 39;`OFDR237` 的「退休財富管理月報」同時具備銷售統計與申報性質,本表只算在 F 一次。**歸類是推測,以報表中文名為唯一依據,選單表不在本專案內無法核實。**

### 0.6 誰用、什麼時候用

- **使用角色**(推測):營運後台人員(受益人 / 集保線)、會計與清算人員(單位數 / 淨值 / 清算線)、通路管理人員(請款線)、法遵人員(申報線)。依據是報表中文名,**ATLAS 的選單權限表不在本專案內,無法核實**。

- **時點**(推測):多數帶「資料日期」或「起訖日」條件且驗「已過帳」(§7.1),屬**日終 / 月結後**作業;`OFDR238` `OFDR239` 名稱帶「每日」,屬**日中**。

- **全域開關**:本片沒有任何組態開關控制報表啟停;`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/App.config` 只有連線與 WCF 設定。

### 0.7 不管什麼

- **不管資料怎麼算出來的。** 算法在 SP,SP 不在版控(§2.2)。

- **不管報表長什麼樣。** 版面在 `.rpt`,二進位,本文不 Read(§2.6 只做檔案存在性與對應規則)。

- **不管排程。** 本片 40 支全是使用者按按鈕觸發,沒有 WindowsService / Batch 入口(§6)。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDR1 全景:受益人、集保、單位數與配息、請款、統計申報五群,加共同的黑箱結構
圖中文字:① 受益人資料與客服:七支,全走 SP,單表輸出 / OFDR013 OFDR014 OFDR015 / 查詢記錄 通聯統計 資料需求 / OFDR034 OFDR035 / 補件通知書 姓名ID異動通知 / OFDR040 OFDR043 / 退郵資料 變更資料查核 / COD006A / 退郵項目與原因代碼 共用 / ② 集保 TDCC 往來:七支,含兩支不印報表的執行型 / OFDR021 OFDR024 / 核對清冊 密碼申請明細 / OFDR563 OFDR564 / 核印費彙總明細 核印失敗通知 / OFDR751 OFDR752 / 平台交易明細 下單檢核 / OFDR022 OFDR023 / 簡訊發送 開畫面即 NRE / ③ 單位數 淨值 與 收益分配:七支,月結後作業 / OFDR001A OFDR002A / 結餘單位數查核表 與清冊 / OFDR236 OFDR716 / 淨值月報 集保登錄 FUY FUS / OFDR281 OFDR282 OFDR286 / 分配名冊 付款 扣繳憑單 / OFDR288 / 配息專戶明細表 / ④ 手續費與服務費請款:四支連號同型,四支都會寫 DB / OFDR452 / 服務費 A2 A3 A4 三張 / OFDR453 / 只出 Excel 沒有 rpt / OFDR455 / 申購手續費 A1 A2 A3 / OFDR457 / 買回手續費 B1 B2 B3 / ⑤ 銷售統計 清算 與 法規申報:十二支 / OFDR235 OFDR238 OFDR239 / 促銷 每日銷售 預估 / OFDR237 OFDR501 / 退休財管月報 行銷群組 / OFDR495 OFDR511 OFDR512 OFDR513 / 基金合併與清算四支 / OFDR540 OFDR731 OFDR733 / 受益人大會 結匯 貨幣基金 / ⑥ 共同結構:本片沒有任何一支報表的取數邏輯在版控內 / 71 個 SP 與 Function / DB/SP 底下一個都找不到 / 71 個 .rpt / 版面二進位 全在 csproj 內但無法 diff
```

*圖:圖 1 OFDR1 全景。橘框=本片的 40 支報表畫面;紫框=有寫入副作用或已壞掉的;灰虛框=被讀但不歸本片管的共用表;黑框=版控外或無法 diff 的資產。五群之間沒有任何程式呼叫——R 畫面彼此不互叫,只靠共同讀同一批表而相關。最下面一排是本片與 M / I 最大的差別:取數邏輯與版面兩端都在版控外。*

### 1.2 七層結構與 M / I / R 差異

圖 2 是 §0.2 那張三十列對照表的圖形版。**只看一張圖的人看這張。**

### 1.3 資料來源三種分流

圖 3。要判斷「改這支報表要動哪裡」,先用這張圖定位它走的是 SP 路還是自組 SQL 路。

### 1.4 最重的一支:`OFDR452` 的完整路徑

圖 4。條件檢核 → 八個 SP 取數 → 寫回 DB → 三張 `.rpt` 輸出。 `OFDR453` `OFDR455` `OFDR457` 三支形狀幾乎相同(§7.8)。

### 1.5 跨模組:報表讀的表是誰建的

圖 5。左欄表、中欄寫入端、右欄本片讀取端。最下面一排標出 R 與 I 的分水嶺。

## 2. 資料模型

```text
[圖] PO 取數的三條路:呼叫 SP、C 井自組 SQL、直接讀表
圖中文字:分流起點:PO 拿到 Util.Parameters 之後只有三條路 / 路 A 呼叫 SP 取 RefCursor / 36 支 佔九成 / 路 B C# 自組 SQL 字串 / 4 支 OFDR002A OFDR022 OFDR023 OFDR040 / 路 C 讀既有表 / 0 支 本片沒有任何一支直接 SELECT 實體表而不經 SP 或自組 SQL / GetStoredProcCommand(SP名) / SP 名是 C# 內的字面常數 / GetSqlStringCommand(strSQL) / strSQL 由 += 疊出來 / AddInParameter 具名綁定 / 條件值不會進 SQL 文字 / 條件值直接串進 SQL 文字 / OFDR022 OFDR023 OFDR002A 三支 / AddOutParameter RefCursor / OracleDbType.RefCursor int.MaxValue / 整段 SQL 送出 / OFDR002A 還留著 T-SQL 中括號 / LoadDataSet(cmd, DataEntity, 結果集名) / 第三參是結果集名 不是表名 真實表名只在 SP 裡 / Ctl TransferVDBHelper.TransferTable / Model 表整表搬成 View 表 / UI 拿 View 資料 再交給 Crystal 或 ExcelHelper / 兩個出口 / 為什麼 R 比 I 安全 / I 有 13 支串接 R 只有 3 支 差別在九成走 SP / 代價是什麼 / 71 個 SP 全不在版控 少印一列讀 C# 沒用
```

*圖:圖 3 資料來源三種分流,對應 §2.3。左欄=九成走的 SP 路;中欄=四支自組 SQL 的路;右欄=本片實際上不存在的第三種。兩條路在 LoadDataSet 那一格合流,之後完全相同。右側兩塊是這個設計的一好一壞:安全性換來的是取數邏輯整個看不到。*

### 2.1 主表與明細:**本片沒有**

`grep -c "MasterTable" Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/*.cs` 全目錄是 **0**。 40 支 PO 一個 `MasterTable` / `DetailTable` 宣告都沒有,這點與 I 完全一致(`ofdi1.md §0`), 也與前人手冊 `add-report.md` 的 `§0.3` 對 `CASR001` 的觀察一致——**不是 OFD 的特例,是 R 型別的通則**。

取而代之的是 PO 的這一行(以 `OFDR001A` 為例):

```
m_db.LoadDataSet(dbcomd, modelVDB.DataEntity, modelVDB.DataEntity.OFDR001A.TableName);
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:51`。 **第三個參數是結果集名(`OFDR001A`,就是畫面代號),不是實體表名。** 所以工具想從 PO 反推「這支報表讀哪些表」,**在本片會全數落空**。

### 2.2 SP 與 Function:**71 個,版控內 0 個**

本片 40 支 PO 引用的 SP / Function 全清單如下。比對基準是 `/DB/` 底下的 279 個檔(`DB/SP/` `DB/Function/` `DB/Table/` `DB/Trigger/` `DB/View/`),以檔名(不含副檔名、大小寫不敏感)比對。

| 畫面 | SP / Function | 在版控 |
|---|---|---|
| `OFDR001A` | `s_TA_OFDR001A_Get` | 否 |
| `OFDR002A` | `s_OFDR002A_Get` | 否 |
| `OFDR013` | `s_OFDR013_Get` | 否 |
| `OFDR014` | `s_OFDR014_Get` | 否 |
| `OFDR015` | `s_OFDR015_Get` | 否 |
| `OFDR021` | `s_OFDR021_Get` `s_OFDR021_1_Get` `s_OFDR021_2_Get` `s_OFDR021_3_Get` `s_OFDR021_4_Get` `s_OFDR021_5_Get` `s_OFDR021_6_Get` `s_OFDR021_BACC_OFF_Get` `s_OFDR021_SACC_OFF_Get` | 否(9 個) |
| `OFDR022` | `Sp_ForTa_Batch_Send` | 否 |
| `OFDR023` | `Sp_ForTa_Batch_Send` | 否 |
| `OFDR024` | `s_OFDR024_Get` | 否 |
| `OFDR034` | `S_TA_OFDR034_GET` | 否 |
| `OFDR035` | `S_TA_OFDR035_GET` | 否 |
| `OFDR040` | `S_TA_OFDR040_GET` | 否 |
| `OFDR041` | `S_TA_OFDR041_GET` `S_TA_OFDR041_GET_T` | 否(2 個) |
| `OFDR043` | `S_TA_OFDR043_Get` | 否 |
| `OFDR235` | `S_TA_OFDR235_GET` | 否 |
| `OFDR236` | `S_TA_OFDR236_GET` | 否 |
| `OFDR237` | `S_TA_OFDR237_GET` | 否 |
| `OFDR238` | `S_TA_OFDR238_GET` | 否 |
| `OFDR239` | `S_TA_OFDR239_GET` | 否 |
| `OFDR281` | `s_TA_OFDR281_Get` | 否 |
| `OFDR282` | `s_TA_OFDR282_Get` | 否 |
| `OFDR286` | `s_TA_OFDR286_Get` | 否 |
| `OFDR288` | `s_OFDR288_Get` | 否 |
| `OFDR452` | `S_TA_OFDR452_GET` `S_TA_OFDR452_A0_Get` `S_TA_OFDR452_A1_Get` `S_TA_OFDR452_A2_Get` `S_TA_OFDR452_A3_Get` `S_TA_OFDR452_A4_Get` `S_TA_OFDR452_A5_Get` `S_TA_OFDR452_DEL` | 否(8 個) |
| `OFDR453` | `S_TA_OFDR453_GET` `S_TA_OFDR453_B1_Get` `S_TA_OFDR453_B2_Get` `S_TA_OFDR453_B3_Get` `S_TA_OFDR453_B4_Get` `S_TA_OFDR453_B5_Get` `S_TA_OFDR453_DEL` | 否(7 個) |
| `OFDR455` | `S_TA_OFDR455_GET` `S_TA_OFDR455_A1_Get` `S_TA_OFDR455_A2_Get` `S_TA_OFDR455_A3_Get` `S_TA_OFDR455_A4_Get` | 否(5 個) |
| `OFDR457` | `S_TA_OFDR457_GET` `S_TA_OFDR457_B1_Get` `S_TA_OFDR457_B2_Get` `S_TA_OFDR457_B3_Get` | 否(4 個) |
| `OFDR495` | `s_TA_OFDR495_Get` `s_TA_OFDR495_1_Get` | 否(2 個) |
| `OFDR501` | `s_OFDR501_Get` | 否 |
| `OFDR511` | `s_TA_OFDR511_Get` | 否 |
| `OFDR512` | `s_TA_OFDR512_Get` | 否 |
| `OFDR513` | `s_TA_OFDR513_Get` | 否 |
| `OFDR540` | `BF_VOTE.OFDR540_Statistics` `BF_VOTE.OFDR540_Detail_Get` `BF_VOTE.OFDR540_Detail_VALID` `BF_VOTE.OFDR540_Detail_AGENT` `BF_VOTE.OFDR540_AGENT_Statistics` `BF_VOTE.OFDR540_AGENT_EMP` | 否(6 個,**唯一用 package 命名的**) |
| `OFDR563` | `s_OFDR563_Get` | 否 |
| `OFDR564` | `s_OFDR564_Get` | 否 |
| `OFDR716` | `s_TA_OFDR716_Get` `s_TA_OFDR716_1_Get` `s_TA_OFDR716_2_Get` | 否(3 個) |
| `OFDR731` | `s_OFDR731_Get` | 否 |
| `OFDR733` | `s_TA_OFDR733_Get` | 否 |
| `OFDR751` | `S_TA_OFDR751_GET` `S_TA_OFDR751_SUM_GET` `S_TA_OFDR751_SHOET_GET` | 否(3 個,**注意第三個是 `SHOET`,疑為 `SHORT` 的拼錯**) |
| `OFDR752` | `S_TA_OFDR752_GET` | 否 |

**合計 71 個不同的 SP / package procedure,版控內 0 個。** 全部進 meta `refcheck-ignore`。

命名沒有統一慣例,實際存在五種:

| 樣式 | 例 | 支數 |
|---|---|---|
| `s_TA_<代號>_Get` 混合大小寫 | `s_TA_OFDR001A_Get` | 13 |
| `S_TA_<代號>_GET` 全大寫 | `S_TA_OFDR034_GET` | 30 |
| `s_<代號>_Get` **沒有 `TA_` 中綴** | `s_OFDR013_Get` | 21 |
| `Sp_ForTa_Batch_Send` **完全不照代號** | 共用簡訊發送 | 1 |
| `BF_VOTE.<名>` **Oracle package** | `BF_VOTE.OFDR540_Statistics` | 6 |

**第三種(無 `TA_` 中綴)與第一、二種的分野,正好等於 PO 基底的兩派**: `Basic_PO` 派 13 支全部用沒有 TA 中綴的樣式,`I<代號>_PO` 派全部用帶 TA 中綴的樣式。 **〔假設〕這是兩個世代**:`Basic_PO` 加上無 TA 中綴的 SP 名是早期寫法,`I<代號>_PO` 加上有 TA 中綴的 SP 名是後期。依據是兩組完全不交叉,且早期那組的 UI 裡留著大量 `//this.SetQueryParameters("OFDRxxxRPS"); //@@@ 步驟2 :指定報表ClassName` 這種範本殘留註解(例 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR014.cs:60`),後期那組沒有。

### 2.3 資料來源三種分流(逐支歸類)

三種來源的定義:**自組 SQL** = PO 內出現 `GetSqlStringCommand`;**呼叫 SP** = 出現 `GetStoredProcCommand`;**讀既有表** = 兩者皆無而直接走框架的表級存取。

| 來源 | 支數 | 代號 |
|---|---|---|
| **呼叫 SP** | 36 | `OFDR001A` `OFDR013` `OFDR014` `OFDR015` `OFDR024` `OFDR034` `OFDR035` `OFDR041` `OFDR043` `OFDR235` `OFDR236` `OFDR237` `OFDR238` `OFDR239` `OFDR281` `OFDR282` `OFDR286` `OFDR288` `OFDR452` `OFDR453` `OFDR455` `OFDR457` `OFDR495` `OFDR501` `OFDR511` `OFDR512` `OFDR513` `OFDR540` `OFDR563` `OFDR564` `OFDR716` `OFDR733` `OFDR751` `OFDR752` + 混合的 `OFDR021` `OFDR731` |
| **SP + 自組 SQL 混合** | 4 | `OFDR002A` `OFDR021` `OFDR040` `OFDR731` |
| **純自組 SQL(無 SP 取數)** | 2 | `OFDR022` `OFDR023`(只呼叫共用的 `Sp_ForTa_Batch_Send` 做寄送,取數全靠自組 SQL) |
| **讀既有表(不經 SP 也不自組 SQL)** | **0** | — |

混合的那四支,自組 SQL 只用來**填下拉選單**,不是報表主資料:

| 畫面 | 自組 SQL 用途 | 錨點 |
|---|---|---|
| `OFDR002A` | 撈基金清單填多選框 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:83-93` |
| `OFDR040` | 撈退郵項目代碼(`COD006A.CODE_SORT = 'E2'`) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR040_PO.cs:159-165` |
| `OFDR040` | 撈退郵原因代碼(`COD006A.CODE_SORT = 'E3'`) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR040_PO.cs:204-210` |
| `OFDR021` | 撈國別代碼 `CTL014` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR021_PO.cs:125-132` |

**只有 `OFDR022` `OFDR023` 的報表主資料是 C# 自組的。** 這兩支也正好是壞的(附錄 E)。

### 2.4 參數化程度

| 作法 | 支數 | 說明 |
|---|---|---|
| `AddInParameter` 具名綁定 | 37 | SP 路一律如此,值不進 SQL 文字 |
| `AddInParameter` + 部分字串串接 | 1 | `OFDR002A`:`@FUNDCODE` 走綁定,但整段 SQL 由 `+=` 疊,見下 |
| **條件值直接串進 SQL 文字** | 2 | `OFDR022` `OFDR023` |

**唯一兩支真正把使用者輸入串進 SQL 的**:

```
case "ID_NO":
    strSQL += " AND BMS001.ID_NO = '" + rrRow.Value + "' " + Environment.NewLine;
    break;
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:259`。同一個 method 內 `BF_NO`(`:256`)、`ConfirmDate_ST` / `_ED`(`:250` `:253`)、`RECEIPT_DOC_ID`(`:263` 起的四個 case)全部同型。 `OFDR023_PO` 的對應段落結構相同。

**這比 `ofdi1.md` 的 13 支好太多**——但要注意原因不是本片寫得比較小心,是**九成走 SP 所以沒有機會串**(§0.2 第 24 列)。

### 2.5 參數命名慣例:**四套並存**

同一個專案內,傳給 SP 的參數名前綴有四種寫法:

| 前綴 | 例 | 用在哪 |
|---|---|---|
| `@stri` / `@data` / `@deci` / `@dat` | `@striID_NO_ST`(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR021.cs:93`) | `OFDR021` `OFDR022` `OFDR023` `OFDR024` `OFDR731` `OFDR564` — **`@` 是 T-SQL 的參數前綴,Oracle 用 `:`**,留在這裡是遷移殘留 |
| `stri` / `dati` / `inti` / `deci` 無 `@` | `striFUND_ID`(`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs:63`) | 清算群、`OFDR239` |
| `i` 單字母開頭 | `iFUND_ID`(`OFDR238` `OFDR235` `OFDR236` `OFDR237` `OFDR751` `OFDR752`) | 銷售統計群、集保下單群 |
| 裸欄名 | `FUND_ID` `ISSUE_CODE`(`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs:129-131`) | `OFDR512` `OFDR513` 的第二個 SP 呼叫 |

`OFDR512_PO` **同一支裡三套都用到**:`:61-76` 用 `stri` / `dati` / `int`,`:129-131` 用裸欄名。這代表**兩段是不同人不同時期寫的**;改參數時不能假設同一支畫面的慣例一致。

### 2.6 `.rpt` 對應表(**M / I 沒有這一節**)

#### 2.6.1 對應規則

**一對多,不是一對一。** 規則是:

```
<畫面代號>RPS[後綴].rpt
```

後綴有三種形態,**沒有統一規律**:

| 形態 | 例 | 意義 |
|---|---|---|
| 無後綴 | `OFDR001ARPS.rpt` | 單版型畫面(21 支) |
| 數字 | `OFDR238RPS1` ~ `RPS4` | 同畫面的四種報表(依 UI 選項切) |
| **字母 + 數字** | `OFDR452A2RPS` `OFDR455A1RPS` `OFDR457B1RPS` | 請款群專有:字母對應 SP 的 `_A2_Get` / `_B1_Get` 後綴,**`RPS` 跑到最後面去了** |

第三種是**構詞例外**:一般是 `<代號>RPS<n>`,請款群是 `<代號><分頁碼>RPS`。 `grep` 找 `OFDR452RPS` 會一無所獲——要找 `OFDR452A*RPS`。

編號也不連續:`OFDR751` 有 `RPS` `RPS2` `RPS3`(**沒有 `RPS1`**); `OFDR540` 有 `RPS` `RPS1` `RPS6` `RPS7` `RPS8` `RPS9`(**沒有 `RPS2`~`RPS5`**,因為 UI 把選項 `1`~`5` 全導到 `RPS1`,見 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:96-102`)。

#### 2.6.2 版控狀況:**71 個全在,1 個引用懸空**

`Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/` 底下實有 **71 個 `.rpt`**, 逐個比對 `Report.OFD.csproj`:

- **磁碟上有、csproj 沒有:0 個**

- **csproj 有、磁碟上沒有:0 個**

- **71 個都有同名伴生 `.cs`,且 71 個 `.cs` 都在 csproj 內**

**這與 `misc.md` 實測的「2 支 `.rpt` 躺在沒有 csproj 的資料夾」是相反的結果——本專案沒有那一型。** 部署路徑也齊全:`Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/Report.OFD.csproj:793` 有 PostBuild

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

`*.rpt` 通配,所以不管 csproj 怎麼宣告都會被複製走。

**唯一的破口是反過來的:UI 要一個不存在的版型。**

```
this.SetQueryParameters("OFDR716RPS2", "OFDR716RPS2", "");
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR716.cs:56`。 `OFDR716RPS2` **沒有 `.rpt`、沒有伴生 `.cs`、不在 csproj、不在磁碟上**。報表中文名也是空字串。走到這個分支必定執行期失敗。嚴重度見附錄 E。

#### 2.6.3 宣告方式兩派

71 個 `.rpt` 在 csproj 內有兩種宣告方式:

| 方式 | 個數 | 例 |
|---|---|---|
| 伴生 `.cs` 用 `<DependentUpon>x.rpt</DependentUpon>` 掛著,`.rpt` 本身不另外列 | 62 | `Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/Report.OFD.csproj:102` |
| `.rpt` 額外列一筆 `<None Include="x.rpt" />` | 9 | `Dev/ATLAS.OFD.Report/Source/CrystalReports/Report.OFD/Report.OFD.csproj:506-514` |

那 9 個正好是請款群的全部:`OFDR452A2` `OFDR452A3` `OFDR452A4` `OFDR455A1` `OFDR455A2` `OFDR455A3` `OFDR457B1` `OFDR457B2` `OFDR457B3`。 **〔假設〕這一批是後來手工加進 csproj 的**,依據是它們同時也是命名構詞例外的那一批(§2.6.1),且 `<None>` 區塊緊接在 `App.config` 後面、與其他 `.rpt` 分開。 **實務上不影響**——PostBuild 的 `*.rpt` 通配會複製它們。

#### 2.6.4 逐支對應

| 畫面 | `.rpt` | 張數 | 全在版控 |
|---|---|---|---|
| `OFDR001A` | `OFDR001ARPS` | 1 | 是 |
| `OFDR002A` | `OFDR002ARPS` | 1 | 是 |
| `OFDR013` | `OFDR013RPS` | 1 | 是 |
| `OFDR014` | `OFDR014RPS` | 1 | 是 |
| `OFDR015` | `OFDR015RPS` | 1 | 是 |
| `OFDR021` | `OFDR021RPS` | 1 | 是 |
| `OFDR022` | **無** | 0 | 不適用(不是報表) |
| `OFDR023` | **無** | 0 | 不適用(不是報表) |
| `OFDR024` | `OFDR024RPS` | 1 | 是 |
| `OFDR034` | `OFDR034RPS` | 1 | 是 |
| `OFDR035` | `OFDR035RPS` | 1 | 是 |
| `OFDR040` | `OFDR040RPS` | 1 | 是 |
| `OFDR041` | `OFDR041RPS` `OFDR041RPS1` | 2 | 是 |
| `OFDR043` | `OFDR043RPS` | 1 | 是 |
| `OFDR235` | `OFDR235RPS1` `OFDR235RPS2` | 2 | 是(**無無後綴版**) |
| `OFDR236` | `OFDR236RPS` | 1 | 是 |
| `OFDR237` | **無** | 0 | 不適用(只出 Excel) |
| `OFDR238` | `OFDR238RPS1` ~ `RPS4` | 4 | 是 |
| `OFDR239` | `OFDR239RPS1` ~ `RPS3` | 3 | 是 |
| `OFDR281` | `OFDR281RPS` | 1 | 是 |
| `OFDR282` | `OFDR282RPS` `OFDR282RPS1` | 2 | 是 |
| `OFDR286` | `OFDR286RPS` `OFDR286RPS1` `OFDR286RPS2` | 3 | 是 |
| `OFDR288` | `OFDR288RPS` | 1 | 是 |
| `OFDR452` | `OFDR452A2RPS` `OFDR452A3RPS` `OFDR452A4RPS` | 3 | 是(**八個 SP 只有三張圖**) |
| `OFDR453` | **無** | 0 | 不適用(只出 Excel) |
| `OFDR455` | `OFDR455A1RPS` `OFDR455A2RPS` `OFDR455A3RPS` | 3 | 是 |
| `OFDR457` | `OFDR457B1RPS` `OFDR457B2RPS` `OFDR457B3RPS` | 3 | 是 |
| `OFDR495` | `OFDR495RPS` | 1 | 是 |
| `OFDR501` | `OFDR501RPS` | 1 | 是 |
| `OFDR511` | `OFDR511RPS` | 1 | 是 |
| `OFDR512` | `OFDR512RPS` `OFDR512RPS1` | 2 | 是 |
| `OFDR513` | `OFDR513RPS` | 1 | 是 |
| `OFDR540` | `OFDR540RPS` `RPS1` `RPS6` `RPS7` `RPS8` `RPS9` | 6 | 是(**動態組名,見 §7.10**) |
| `OFDR563` | `OFDR563RPS1` `OFDR563RPS2` | 2 | 是 |
| `OFDR564` | `OFDR564RPS` | 1 | 是 |
| `OFDR716` | `OFDR716RPS` `OFDR716RPS1` · **`OFDR716RPS2` 不存在** | 2 + 1 懸空 | **否** |
| `OFDR731` | `OFDR731RPS` | 1 | 是 |
| `OFDR733` | `OFDR733RPS1` `OFDR733RPS2` | 2 | 是(**無無後綴版**) |
| `OFDR751` | `OFDR751RPS` `OFDR751RPS2` `OFDR751RPS3` | 3 | 是(**跳過 `RPS1`**) |
| `OFDR752` | `OFDR752RPS` | 1 | 是 |

**合計**:本片 40 支用掉 **63 個 `.rpt`**,全部在版控;另有 **1 個懸空引用**(`OFDR716RPS2`)。專案內其餘 8 個 `.rpt`(`OFDR285RPS` `OFDR285RPS1` `OFDR287RPS` `OFDR287RPS1` `OFDR461RPS` `OFDR461RPS1` `OFDR561RPS` `OFDR562RPS`)屬於劃給下一片的那 5 支畫面。

### 2.7 C# 裡看得見的表(只有 13 張)

由 `FROM` / `JOIN` / `UPDATE` / `INTO` 的字面值抽出。**這不是完整清單,只是「不經 SP 就看得到」的那部分**; 其餘取數表名全在 71 個版控外 SP 裡。

| 表 | 誰讀 / 寫 | 用途(推測) |
|---|---|---|
| `BMS001` | `OFDR022` `OFDR023`(**讀 + 寫**) | 受益人開戶主檔;`RECEIPT_DOC_ID` / `RECEIPT_DOC_ID2` 是境內 / 境外文件寄發旗標 |
| `OFD132` | `OFDR022` | 文件寄發設定;`STATEMENT_CODE` `SEND_CODE` `SEND_NEW_FLASH` |
| `OFD081V` | `OFDR002A` | 基金主檔檢視(`V` 結尾,**假設**為 view) |
| `OFD038` | `OFDR002A` | 基金分群;`FUND_GRPCD` |
| `OFD303A` | `OFDR001A` `OFDR002A` | 結帳控制;`CTL_DATE` 過帳日期 |
| `COD006A` | `OFDR040` | 共用代碼;`CODE_SORT = 'E2'` 退郵項目、`'E3'` 退郵原因 |
| `CTL014` | `OFDR021` | 全庫代碼對照(與 `ofdi1.md` 同一張) |
| `OFD281A` | `OFDR286` | 收益分配 |
| `OFD494A` `OFD496A` | `OFDR512` `OFDR513` | 基金清算(與 `ofdi1.md` 的 `OFDI481` 同一批) |
| `OFD562` | `OFDR564`(**讀 + 寫**) | 境外核印;`RECEIPT_DOC_ID2` 旗標 |

`dbo` 與 `P_GP` 兩個字面值是誤抓(前者是 schema 限定詞、後者是 SQL 內的別名),不列入。

### 2.8 欄位中文名

**本片不做欄位中文名總表。** 原因:xsd 是結果集形狀(§0.2 第 16 列),`msdata:Caption` 描述的是「這張報表的第 N 欄叫什麼」, 不是實體表欄位的中文名,**拿來當表欄位字典會誤導**。要查某張報表印哪些欄,直接看該支的 `Model.xsd`。

### 2.9 狀態碼

本片沒有自己的狀態碼。**唯二會被本片改動的狀態欄**:

| 欄 | 表 | 值 | 誰改 | 錨點 |
|---|---|---|---|---|
| `RECEIPT_DOC_ID` | `BMS001` | `'Y'` / `'N'` | `OFDR022` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:137-157` |
| `RECEIPT_DOC_ID2` | `BMS001` | `'Y'` / `'N'` | `OFDR022` | 同上 |
| `RECEIPT_DOC_ID2` | `OFD562` | `'Y'` | `OFDR564` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR564_PO.cs:123-128` |

`OFDR022` 另外用 `BMS001.OPEN_BF_TYPE` 的 `'1'` / `'2'` 分境內 / 境外 (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:204-208`)。 **這組值域與 `ofd5` / `ofd7` 記的 `FUND_TYPE` `'2'` / `'1'` 不是同一個欄位,不要混用**—— 那邊是基金的境內外,這裡是**開戶**的境內外。

## 3. 畫面清冊

### 3.1 維護 M

(本片無此類畫面)本片切的是 `Dev/ATLAS.OFD.Report` 這個報表專案,型別碼全是 `R`。

### 3.2 查詢 I

(本片無此類畫面)OFD 的 I 畫面在另一個獨立方案 `Dev/ATLAS.OFD.Query`,已由 `ofdi1.md` 涵蓋。

### 3.3 批次 B

(本片無此類畫面)OFD 的 B 畫面在 `Dev/ATLAS.OFDB`,不在本專案內。

### 3.4 報表 R(40 支)

欄位說明:

- **報表中文名**:`SetQueryParameters` 的第三參字面值。多版型的取第一張;完整對應看 §2.6.4。

- **PO 基底**:`<代號>_PO` 的基底宣告,**已先用 `strip_cs_comments` 剝掉 `//` 註解**再比對——這一步不能省,`ofd4.md` 記過 `OFDM125A_PO.cs:28` 留誘餌註解的事;本片沒有同型誘餌,但流程照走。

- **資料來源**:`SP` = 有 `GetStoredProcCommand`;`SQL` = 有 `GetSqlStringCommand`;`SP+SQL` = 兩者都有。

- **條件**:`綁定` = 全走 `AddInParameter`;`串接` = 有使用者輸入直接進 SQL 文字。

- **匯出**:`Crystal` / `Excel` / `TXT`(`StreamWriter` 產純文字檔)。

- **在 csproj**:六層檔案是否全部同時在磁碟上且在對應 csproj 內。

| 代號 | 報表中文名 | PO 基底 | 資料來源 | `.rpt` | 在版控 | 條件 | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|---|
| `OFDR001A` | 基金結餘單位數查核表 | `IOFDR001A_PO` | SP | `OFDR001ARPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR002A` | 基金結餘單位數查核清冊 | `Basic_PO` | SP+SQL | `OFDR002ARPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR013` | 受益人查詢記錄報表 | `Basic_PO` | SP | `OFDR013RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR014` | 客服通聯服務統計表 | `Basic_PO` | SP | `OFDR014RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR015` | 資料需求統計表 | `Basic_PO` | SP | `OFDR015RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR021` | 受益人核對清冊作業 | `Basic_PO` | SP+SQL | `OFDR021RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR022` | (無報表,簡訊發送) | `Basic_PO` | SQL | — | 不適用 | **串接** | 無 | 是 |
| `OFDR023` | (無報表,簡訊發送) | `Basic_PO` | SQL | — | 不適用 | **串接** | 無 | 是 |
| `OFDR024` | 集保網路/語音密碼申請明細表 | `Basic_PO` | SP | `OFDR024RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR034` | 客戶補件通知書 | `IOFDR034_PO` | SP | `OFDR034RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR035` | 受益人姓名／ID異動確認通知信列印作業 | `IOFDR035_PO` | SP | `OFDR035RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR040` | 受益人退郵資料 | `IOFDR040_PO` | SP+SQL | `OFDR040RPS` | 是 | 綁定 | Crystal · Excel | 是 |
| `OFDR041` | 受益人開戶缺件查核表 | `IOFDR041_PO` | SP | `OFDR041RPS` `RPS1` | 是 | 綁定 | Crystal | 是 |
| `OFDR043` | 受益人變更資料查核表 | `IOFDR043_PO` | SP | `OFDR043RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR235` | 促銷活動明細表 | `IOFDR235_PO` | SP | `OFDR235RPS1` `RPS2` | 是 | 綁定 | Crystal · Excel | 是 |
| `OFDR236` | 淨值月報表 | `IOFDR236_PO` | SP | `OFDR236RPS` | 是 | 綁定 | Crystal · Excel | 是 |
| `OFDR237` | 退休財富管理月報 | `IOFDR237_PO` | SP | **無** | 不適用 | 綁定 | **只有 Excel** | 是 |
| `OFDR238` | 每日銷售單位彙總表 | `IOFDR238_PO` | SP | `OFDR238RPS1`~`RPS4` | 是 | 綁定 | Crystal · Excel | 是 |
| `OFDR239` | 銷售預估明細表 | `IOFDR239_PO` | SP | `OFDR239RPS1`~`RPS3` | 是 | 綁定 | Crystal | 是 |
| `OFDR281` | 收益分配名冊 | `IOFDR281_PO` | SP | `OFDR281RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR282` | 收益分配付款彙總表 | `IOFDR282_PO` | SP | `OFDR282RPS` `RPS1` | 是 | 綁定 | Crystal | 是 |
| `OFDR286` | 收益分配扣繳憑單 | `IOFDR286_PO` | SP | `OFDR286RPS` `RPS1` `RPS2` | 是 | 綁定 | Crystal · TXT | 是 |
| `OFDR288` | 配息專戶明細表 | **無基底無介面** | SP | `OFDR288RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR452` | 服務費明細表 | `IOFDR452_PO` | SP | `OFDR452A2RPS` `A3` `A4` | 是 | 綁定 | Crystal · Excel · TXT | 是 |
| `OFDR453` | (三張 Excel,無報表中文名) | `IOFDR453_PO` | SP | **無** | 不適用 | 綁定 | **只有 Excel** | 是 |
| `OFDR455` | 銷售機構申購手續費請款總表 | `IOFDR455_PO` | SP | `OFDR455A1RPS` `A2` `A3` | 是 | 綁定 | Crystal · Excel · TXT | 是 |
| `OFDR457` | 銷售機構買回手續費請款總表 | `IOFDR457_PO` | SP | `OFDR457B1RPS` `B2` `B3` | 是 | 綁定 | Crystal · Excel | 是 |
| `OFDR495` | 基金合併確認單 | `IOFDR495_PO` | SP | `OFDR495RPS` | 是 | 綁定 | Crystal · TXT | 是 |
| `OFDR501` | 行銷身分群組明細表 | `Basic_PO` | SP | `OFDR501RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR511` | 基金清算名冊列印作業 | `IOFDR511_PO` | SP | `OFDR511RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR512` | 基金清算資料彙總表 | `IOFDR512_PO` | SP | `OFDR512RPS` `RPS1` | 是 | 綁定 | Crystal | 是 |
| `OFDR513` | 基金清算發放通知書 | `IOFDR513_PO` | SP | `OFDR513RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR540` | 受益人會議開票結果(十種) | `IOFDR540_PO` | SP | `OFDR540RPS` `RPS1` `RPS6`~`RPS9` | 是 | 綁定 | Crystal | 是 |
| `OFDR563` | 境外集保核印費彙總表 | `Basic_PO` | SP | `OFDR563RPS1` `RPS2` | 是 | 綁定 | Crystal | 是 |
| `OFDR564` | 境外核印失敗通知書 | `Basic_PO` | SP | `OFDR564RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR716` | 開放式受益憑證登錄資料報表-FUY | `IOFDR716_PO` | SP | `OFDR716RPS` `RPS1` · **`RPS2` 懸空** | **否** | 綁定 | Crystal | 是 |
| `OFDR731` | 結匯申報收檔查核表 | `Basic_PO` | SP+SQL | `OFDR731RPS` | 是 | 綁定 | Crystal | 是 |
| `OFDR733` | (信託業、投信業)國內貨幣市場共同基金受益憑證持有者統計表(月報) | `IOFDR733_PO` | SP | `OFDR733RPS1` `RPS2` | 是 | 綁定 | Crystal · TXT | 是 |
| `OFDR751` | 集保平台交易明細表 | `IOFDR751_PO` | SP | `OFDR751RPS` `RPS2` `RPS3` | 是 | 綁定 | Crystal | 是 |
| `OFDR752` | 集保基金下單檢核表 | `IOFDR752_PO` | SP | `OFDR752RPS` | 是 | 綁定 | Crystal | 是 |

### 3.5 從清冊讀出來的六件事

1. **在 csproj:40 支全過。** 六層(UI / Pxy / Ctl / PO / Model.xsd / View.xsd)逐檔比對磁碟與對應 csproj,**40 × 6 = 240 個檔全部同時在磁碟上且在專案內**,沒有 `misc.md` 那種「檔案存在但不在 csproj」的漏網。 **但比對時要注意大小寫**:`Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR452_PXy.cs` 的 `PXy` 是**大寫 X**(csproj 第 134 行同樣寫 `OFDR452_PXy.cs`,所以編得過)。本專案內同型的檔名例外還有兩個,雖不在本片 40 支內但同資料夾會撞到:

- `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR461_PXy.cs`(同樣大寫 X)

- `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR461_Ct.cs`(**少一個 `l`**,不是 `_Ctl.cs`) **這就是交辦裡提醒的「檔名可能不照規則」**——`misc.md` 的 `TRP001_PO.cs` 是同一類。逐支 `ls` 是必要的,照代號硬推檔名在本專案會踩到三次。

1. **`.rpt` 在版控:63 / 63 在,1 個引用懸空。** 唯一的洞是 `OFDR716RPS2`(§2.6.2)。**沒有 `misc.md` 那種「`.rpt` 躺在沒有 csproj 的資料夾」的情形**——本專案只有一個 Crystal 資料夾,而且它有 csproj。

1. **資料來源:SP 壓倒性。** 36 支純 SP、4 支 SP 混自組 SQL(其中三支的自組 SQL 只是填下拉選單)、2 支純自組 SQL。**沒有任何一支「讀既有表」**——本片不存在那個分類。

1. **條件參數化:38 / 40 綁定。** 只有 `OFDR022` `OFDR023` 串接,而這兩支開畫面就壞(附錄 E),實務上等於 0 支在跑。

1. **PO 基底兩派,分野乾淨。** `Basic_PO` 13 支 + `I<代號>_PO` 26 支 + 完全裸的 1 支(`OFDR288`)。 **`Basic_PO` 派與「SP 名沒有 `TA_` 中綴」「UI 留著 `//@@@ 步驟2` 範本註解」三件事完全重合**(§2.2),是同一個世代的產物。

1. **匯出格式不是單選。** 有 6 支同時出 Crystal 與 Excel、4 支同時出 Crystal 與 TXT、`OFDR452` `OFDR455` 三種都出。 **`OFDR237` `OFDR453` 掛在報表專案下卻完全不出報表**,只出 Excel——它們的 UI 基底仍是 `xReportForm`,所以「預覽 / 列印」兩顆按鈕在畫面上,按下去沒有版型可用。 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR237.cs:126` 的註解直說「此功能只開放Excel下載」——**是刻意的,不是漏做**。

## 4. 維護畫面(M)— 一支一節

**本片無 M 畫面。** 原因:切片依據是專案資料夾 `Dev/ATLAS.OFD.Report`,該專案只收型別碼 `R` 的畫面;OFD 的 M 畫面全在 `Dev/ATLAS.OFD`,由 `ofd123.md` `ofd4.md` `ofd5.md` `ofd6.md` `ofd7.md` 五片涵蓋。

## 5. 查詢畫面(I)

**本片無 I 畫面。** 原因:OFD 的 I 畫面在獨立方案 `Dev/ATLAS.OFD.Query`,由 `ofdi1.md` 涵蓋。本文 §0.2 對 I 的所有引用都取自該文,未重新掃描。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService 入口。** 原因:40 支全部由使用者在畫面上按按鈕觸發; `Dev/ATLAS.OFD.Report` 底下六個 csproj 全是 `Library` 或 `WinExe` 型別的 UI 相關組件,沒有 service host。 **唯二帶「批次」字樣的是 `Sp_ForTa_Batch_Send`**(`OFDR022` `OFDR023` 呼叫),那是把簡訊丟進共用寄送佇列的 SP,**寄送本身由別的系統跑**,不在本 repo 內(§7.12)。 OFD 的批次在 `Dev/ATLAS.OFDB`,不在本片範圍。

## 7. 報表(R)

```text
[圖] OFDR452 服務費請款的完整路徑:條件檢核、八個 SP 取數、寫回 DB、三張 rpt 輸出
圖中文字:① 使用者輸入條件 UI 先擋三關 / 選計算年月 通路 基金 / ubtnSearch_Click / 必填檢核 validatorManager1 / 不過 ValidateErrList.Show 阻擋 / 輸出路徑存在檢核 / Directory.Exists 不過就阻擋 / ② 取數:同一支畫面呼叫八個不同的 SP,全部版控外 / S_TA_OFDR452_GET / 主查詢 / S_TA_OFDR452_A0_Get 到 A5_Get / 六個分頁各一個 SP / S_TA_OFDR452_DEL / 刪除既有計算結果 / ③ 副作用:報表畫面會寫 DB / ExecuteNonQuery ×2 / 先 DEL 再重算寫回 / 沒有四眼覆核 / R 畫面沒有 EVA 一按就生效 / 沒有交易包覆的保證 / DEL 成功但重算失敗 資料就空了 / ④ 輸出:三張 rpt 由使用者選的分頁決定 / OFDR452A2RPS 服務費明細表 / SetQueryParameters 第三參是中文名 / OFDR452A3RPS 分支機構服務費總表 / OFDR452A4RPS 分支機構服務費明細表 / ⑤ 綁 schema:唯一連接 C# 與 rpt 的一行,沒有編譯期檢查 / ReportLoad 事件 / SetRptSchemaOnDoc() / m_ReportDocument.SetParameterValue / 補抬頭參數 名稱打錯執行期才知道 / rpt 內部欄位對不上就少印一欄 / 不會報錯 不會編譯失敗 / ⑥ 注意:A0 A1 A5 三個 SP 有呼叫 但沒有對應的 rpt / A0 A1 A5 的資料取了之後 / 只餵畫面 Grid 不出報表 / A2 A3 A4 才有 rpt / 六取三 另外三個查了給人看而已
```

*圖:圖 4 本片最重的一支 OFDR452。六段由上到下依序執行。紫框=風險:寫 DB 卻沒有四眼、DEL 與重算之間沒有交易保證、rpt 綁定沒有編譯期檢查。黑框=版控外。這張圖的形狀在 OFDR453 OFDR455 OFDR457 三支幾乎一模一樣,差別只在 SP 後綴 A 換成 B、rpt 張數不同,以及 OFDR453 用 Excel 取代 Crystal。*

**本章是本片的主體。** §4 §5 §6 都空,因為切片只含 R。排法是:先講 40 支共用的一套流程(§7.1),再挑該深寫的支別(§7.2 ~ §7.12),最後把卡控收成一張總表(§7.13),其餘分群帶過(§7.14)。

### 7.1 通則:一支報表從按鈕到出紙的五段

40 支共用同一套生命週期,由框架類別 `xReportForm` 驅動(**無原始碼,從呼叫端反推**)。五段如下,錨點用 `OFDR001A` 舉例,其餘 37 支 `xReportForm` 畫面同構:

| 段 | 事件 / 方法 | 誰寫的 | 做什麼 | 錨點 |
|---|---|---|---|---|
| 1 | `<代號>_FormInitial` | 各支自己 | `ResultVDB` / `QueryVDB` 建空 VDB,`FormProxy` 指定 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:120-127` |
| 2 | `ubtnSearch_Click` | 各支自己 | 檢核 → 塞 `Util.Parameters` → `FormProxy.GetData` → 填畫面 → 把「預覽 / 列印」兩顆按鈕打開 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:152-236` |
| 3 | `<代號>_BeforePrintButtonClicked` / `_BeforePreviewButtonClicked` | 各支自己 | **列印前再檢核一次**;不過就 `e.Cancel = true`;過了才 `SetQueryParameters(報表類別, 報表類別, 中文名)` | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:248-280` |
| 4 | `<代號>_ReportLoad` | 各支自己 | `SetRptSchemaOnDoc()` 把 View 的 schema 綁上 `.rpt`,再 `m_ReportDocument.SetParameterValue(名, 值)` 補抬頭參數 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:288-296` |
| 5 | `Ctl.Get<代號>ReportObject` | 各支自己 | 從 `ClassData.Util.ReportParameters[0].ReportClass` 取版型名,`CRReportTransfer.TransferFileByte(rpt)` 把 `.rpt` 的位元組傳給客戶端 | `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR013_Ctl.cs:29-33` |

第 5 段是前人手冊 `add-report.md` 的 `§7`(「版型是客戶端選的,伺服端只負責傳檔」)講過的機制,本文不重複。 **本文補的是它沒講的那一半:第 3 段的檢核。** `add-report.md` 的 `§0.3` 寫「報表是唯讀的,不走四眼流程」——這句話對四眼而言正確,但會讓人以為 R 沒有卡控。 **實際上 R 的第 3 段是整個 ATLAS 裡除了 M 的存檔前檢核之外最密的一處**:`OFDR751` 在這一段放了 16 條 `AddError`。

#### 7.1.1 卡控五類在 R 的分佈

| 結果類型 | 在 R 長什麼樣 | 支數 |
|---|---|---|
| **阻擋** | `ValidateErrList.AddError(控件, 訊息)` + `if (ValidateErrList.Show()) { e.Cancel = true; return; }` | 38 支(除 `OFDR022` `OFDR023`) |
| **警示** | `DialogWithNoStatusbar.ShowMessage(FunctionDialogStyle.Info01, 訊息)`,顯示後照跑 | 11 支 |
| **詢問** | 無。全片 40 支的 UI 找不到任何 `FunctionDialogStyle.Question` / `DialogResult.Yes` | **0 支** |
| **過濾(無提示)** | 條件寫死在 C# 或 SQL,畫面上看不到,少印的列使用者不會知道 | **4 處,見 §7.13.2** |
| **記錄不擋** | 無 | 0 支 |

### 7.2 `OFDR001A` / `OFDR002A`:那個 `A` 是什麼

#### 7.2.1 答案:**境內外分身,但機制是「分兩個專案」,不是「同一張表用欄位值分」**

交辦列的五種 `A` 後綴成因,本對屬於 **(a) 境內外**,**但實現方式與 `ofd5` / `ofd7` 記的不同**,要更正一筆。

`ofd5` / `ofd7` 記的是:同一支畫面用 `FUND_TYPE` 的 `'2'` / `'1'` 分境內外,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`。 **本對不是那樣。** 實測如下:

| 代號 | 所在專案 | 報表中文名(`SetQueryParameters` 第三參) | SP |
|---|---|---|---|
| `OFDR001A` | `Dev/ATLAS.OFD.Report` | **基金結餘單位數查核表** | `s_TA_OFDR001A_Get` |
| `OFDR001B` | `Dev/ATLAS.OTA.Report` | **境外**基金結餘單位數檢核表 | `S_OTA_OFDR001_GET` |
| `OFDR002A` | `Dev/ATLAS.OFD.Report` | **基金結餘單位數查核清冊** | `s_OFDR002A_Get` |
| `OFDR002` | `Dev/ATLAS.OTA.Report` | **境外**基金結餘單位數查核清冊 | `S_OTA_OFDR002_GET` |

錨點: `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:280` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:124` · `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR002A.cs:82` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR002.cs:137` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR001B_PO.cs:65` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:68`。

所以:

1. **境內版住 `OFD` 專案、境外版住 `OTA` 專案**(`OTA` **假設**為 Offshore TA,依據是該專案內所有報表中文名都帶「境外」)。

2. **兩邊呼叫完全不同的 SP**,不是同一個 SP 加參數。

3. **`A` / `B` 後綴不是境內外的標記**——`OTA` 那邊 `OFDR001B` 帶 `B`、`OFDR002` 不帶。真正的標記是**專案**。`A` 的功能只是「在 `OFD` 專案裡把號碼讓開,避免與 `OTA` 的同號撞」。

#### 7.2.2 它讀的表帶不帶 `A`?

帶。`OFDR002A` 的自組 SQL(填基金下拉)讀的是 `OFD081V`(不帶 `A`,`V` 結尾)與 `OFD038`(不帶 `A`), `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:83-91`; `OFDR001A` 與 `OFDR002A` 檢核過帳日期讀 `OFD303A`(**帶 `A`**), `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:68-115`。

**表名的 `A` 與畫面代號的 `A` 沒有關係。** `OFD303A` 被 `OFDR001A` 與 `OFDR002A` 共用, 也被 `ofdi1.md` 記的 `OFDI072A` 讀——**那是表自己的 `A`,`ofd123.md` 已證實那批來自 MSSQL→Oracle 遷移改名**(成因 b)。

#### 7.2.3 結論:五種成因要加第六種

本對對不上交辦列的任何一種。**要新增第六種:**

> **(f) 同一份業務報表在兩個子系統各做一份,用後綴讓號。** 判別法:`atlas_index.json` 查同號畫面,若落在不同 `project`,就是這一種。本片實證:`OFDR001A`(OFD)對 `OFDR001B`(OTA)、`OFDR002A`(OFD)對 `OFDR002`(OTA)。 **與 (a) 境內外的差別**:(a) 是同一支畫面內用欄位值分,(f) 是兩支不同畫面、兩支不同 SP、兩個不同專案。改 (a) 只要改一處,改 (f) 要記得改兩邊——這正是「成對報表只改一邊」的溫床。

#### 7.2.4 `OFDR001A` 與 `OFDR002A` 本身的差別

| 面向 | `OFDR001A` | `OFDR002A` |
|---|---|---|
| 報表形態 | **單基金單筆**,22 個單位數欄位攤在畫面上 | **多基金清冊**,勾一批基金逐筆列 |
| PO 基底 | `IOFDR001A_PO`(後期) | `Basic_PO`(**早期,`m_db` 為 null**,§7.12.2) |
| 檢核 | 營業日 + 已過帳 + **帳平不平** | 至少勾一筆基金 + 逐筆檢查 `row.err` |
| DB 型別 | `OracleDbType` | **`SqlDbType`,7 處,一個 `OracleDbType` 都沒有** |

`OFDR001A` 最值得抄的是**帳平不平的檢核**:

```
if (m_unit12 != m_unit21 || m_unit21 != m_unit22 || m_unit11 != m_unit19)
{
    this.ValidateErrList.AddError(this.custFUND_ID_0, "該基金帳未平");
}
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:270-273`。 **這是 R 唯一一處「算出來的結果不對就不准印」的卡控**,結果類型 = 阻擋。其餘 39 支的檢核都只驗輸入,不驗輸出。

`OFDR001A` 的卡控總表:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 / 列印前 | 資料日期必須是該基金的營業日(`ClientBizUtility.GetFundBusinessDay`) | 擋下 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:40-49` |
| 查詢 / 列印前 | 資料日期必須是該基金已過帳的日期(`GetCTL_DATEYN` 回 0) | 擋下 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:51-58` |
| 查詢 / 列印前 | `GetCTL_DATEYN` 回 `-1`(伺服端錯) | 彈 `ServerSideError` 視窗**但不擋**(後面沒有 `AddError`) | **警示** | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:59-62` |
| 選基金時 | 該基金無結帳日期 | 彈訊息,日期欄留空 | 警示 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:143` |
| 查詢後 | SP 回傳的 `ERR_MSG` 非空 | 彈訊息 | 警示 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:229-232` |
| 列印前 | SP 回傳的 `ERR_MSG` 非空 | 擋下 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:266-269` |
| 列印前 | 帳未平 | 擋下 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:270-273` |

**同一個 `ERR_MSG`,查詢時只警示、列印時才阻擋。** 這是刻意的:讓使用者先看到數字,確認後才不准印。

### 7.3 連號群 `OFDR021`–`OFDR024`:**不是同一個業務系列**

四支連號,直覺會以為是一組。**實測不是。**

| 代號 | 中文名 | UI 基底 | 查詢條件(UI 的 `AddParametersRow` key) | 出報表 |
|---|---|---|---|---|
| `OFDR021` | 受益人核對清冊作業 | `xReportForm` | `@striID_NO_ST/ED` `@deciBF_NO_ST/ED` `@dataOPEN_ACC_DATE_ST/ED` `@striBF_COUNTRY_X` `@striSort` | 是 |
| `OFDR022` | (簡訊發送) | **`xOneStepProcessForm`** | `Type` `BF_NO` `ID_NO` `ConfirmDate_ST/ED` `OPEN_ACC_DATE_ST/ED` `RECEIPT_DOC_ID` | **否** |
| `OFDR023` | (簡訊發送) | **`xOneStepProcessForm`** | `SEND_KIND` `BF_NO` `ID_NO` `INCLUDE_SEND` | **否** |
| `OFDR024` | 集保網路/語音密碼申請明細表 | `xReportForm` | (在 `Customer_SetQueryParameters` 內組,不走 UI 的 `AddParametersRow`) | 是 |

**相似度(查詢條件 key 的 Jaccard)**:

| 配對 | Jaccard | 共同 key |
|---|---|---|
| `OFDR021` vs `OFDR022` | 0.00 | 無 |
| `OFDR021` vs `OFDR023` | 0.00 | 無 |
| `OFDR021` vs `OFDR024` | — | 兩支都不在 UI 層組條件,無從比 |
| **`OFDR022` vs `OFDR023`** | **0.20** | `BF_NO` `ID_NO` |
| `OFDR022` vs `OFDR024` | 0.00 | 無 |
| `OFDR023` vs `OFDR024` | 0.00 | 無 |

**結論:連號只是號碼相鄰,不是同一系列。** 唯一真正成對的是 `OFDR022` / `OFDR023` ——它們 Jaccard 只有 0.20,但**共用同一個 SP(`Sp_ForTa_Batch_Send`)、同一個 UI 基底、同一個 `m_db` 為 null 的缺陷、同一個 `trans.Rollback()` 在 `trans` 為 null 時的二次 NRE**,結構上是雙胞胎(§7.12)。

**業務上四支的共同點只有一個:都跟「受益人開戶後的後續處理」有關。** 這是**推測**,依據是四支的條件裡都出現 `BF_NO`(戶號)或 `OPEN_ACC_DATE`(開戶日)。

`OFDR021` 值得記一筆的是它的 `CTL014` 用法:

```
sqlCommand += "   WHERE SourceType in ('415','085','087','138','143','413','146','064') "
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR021_PO.cs:130`。 **八個 `SourceType` 寫死在 C# 裡**,與 `ofdi1.md` 記的 `CTL014` `SourceType` 編號(`'000'` `'100'` `'149'` `'204'` `'232'` `'236'`)**沒有一個重疊**—— 兩片各自寫死各自的一批,`CTL014` 加代碼時沒有一處集中的地方可以改。〔客戶特定〕。

### 7.4 連號群 `OFDR235`–`OFDR239`:**兩支一組,其餘各自獨立**

| 代號 | 中文名 | 條件 key 數 | SP 參數前綴 |
|---|---|---|---|
| `OFDR235` | 促銷活動明細表 / 彙總表 | 10 | `i` |
| `OFDR236` | 淨值月報表 | 4 | `i` |
| `OFDR237` | 退休財富管理月報 | 1 | `i` |
| `OFDR238` | 每日銷售單位彙總表(四張) | 5 | `i` |
| `OFDR239` | 銷售預估明細表(三張) | 10 | **`stri`** |

**相似度**:

| 配對 | Jaccard | 共同 key |
|---|---|---|
| **`OFDR235` vs `OFDR236`** | **0.40** | `SDATE` `EDATE` `FUNDS` `RPT_KIND` |
| `OFDR238` vs `OFDR239` | 0.15 | `FUND_ID` `REPORT_TYPE` |
| 其餘七組配對 | 0.00 | 無 |

**`OFDR235` / `OFDR236` 是真的成對**:條件完全是「起訖日 + 基金多選 + 報表種類」這四件事,`OFDR235` 多六個通路與活動代碼欄。 `OFDR236` 可以看成 `OFDR235` 去掉通路維度的版本。改其中一支的日期語意要一起看另一支。

**`OFDR239` 是群內的異類**:唯一用 `stri` 前綴、唯一在 SP 參數裡出現 `striALLOT_DATE_ST/ED` 與 `striUID_CODE` (UI 傳的是 `CTL_DATE_ST/END`,**名字對不上**——`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR239.cs` 的 key 是 `CTL_DATE_ST`,PO 綁到 SP 的參數叫 `striALLOT_DATE_ST`)。 **這不是 bug**(PO 負責轉譯),但**改 UI 欄名時搜 `ALLOT_DATE` 會搜不到 UI 端**,是維護陷阱。

`OFDR237` 是群內唯一不出 Crystal 的(§7.11)。

### 7.5 連號群 `OFDR511`–`OFDR513`:同系列,但參數慣例三套

三支都是「基金清算」:

| 代號 | 中文名 | `.rpt` | 條件 key |
|---|---|---|---|
| `OFDR511` | 基金清算名冊列印作業 | `OFDR511RPS` | `striFUND_ID` `striBASE_DATE` |
| `OFDR512` | 基金清算資料彙總表 / 明細表 | `OFDR512RPS` `RPS1` | `striFUND_ID` `datiBASE_DATE` `intISSUE_CODE` `striExec` `stripost` `stricheck` `stripostno` `stricheckno` |
| `OFDR513` | 基金清算發放通知書 | `OFDR513RPS` | `striFUND_ID` `striBASE_DATE` `striPROVIDE_DATE` `intISSUE_CODE` `striID_NO` `striBF_NO_0` |

**相似度**:

| 配對 | Jaccard | 共同 key |
|---|---|---|
| `OFDR511` vs `OFDR512` | 0.11 | `striFUND_ID` |
| **`OFDR511` vs `OFDR513`** | **0.33** | `striFUND_ID` `striBASE_DATE` |
| `OFDR512` vs `OFDR513` | 0.17 | `striFUND_ID` `intISSUE_CODE` |

**這一群確實是同一業務系列**(都讀 `OFD494A` `OFD496A`,§2.7), 但 **`OFDR512` 把基準日叫 `datiBASE_DATE`,另外兩支叫 `striBASE_DATE`**——同一個概念三支裡兩個名字。 Jaccard 因此被低估:實際業務相似度高於 0.11 / 0.33 這兩個數字。 **照抄 `ofd7.md §4` 的 diff 手法時要注意這一點:key 名不同不等於語意不同。**

`OFDR512` 是群內最完整的一支,深寫如下。

#### 7.5.1 `OFDR512` 深寫

**兩段取數,兩套參數慣例**:

| 段 | SP | 參數名 | 錨點 |
|---|---|---|---|
| 主查詢 | `s_TA_OFDR512_Get` | `intISSUE_CODE` `striFUND_ID` `datiBASE_DATE` `striExec` `stripost` `stricheck` `stripostno` `stricheckno`(8 個) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs:57-77` |
| 第二段 | 同 SP 另一次呼叫 | **`FUND_ID` `ISSUE_CODE`(裸欄名,無前綴)** | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs:127-131` |

**同一支 PO 裡兩種參數命名。** 這代表兩段是不同時期寫的(§2.5)。改 SP 簽名時**必須兩段都改**,而搜 `striFUND_ID` 只會找到第一段。

`OFDR513` 另有一個寫死的哨兵值:

```
QueryVDB.Util.Parameters.AddParametersRow("striBF_NO_0", SQLOperator.Equal,
    this.custBF_NO_0.Value == "" ? "-1" : this.custBF_NO_0.Value);
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR513.cs:79`。 **戶號空白時傳 `-1` 當「全部」**。這是寫死常數,語意只存在 SP 內;`OFDR511` `OFDR512` 沒有這個約定。

### 7.6 連號群 `OFDR751` / `OFDR752`:**不是同一系列**

| 代號 | 中文名 | 條件 key 數 | 共同 key |
|---|---|---|---|
| `OFDR751` | 集保平台交易明細表 / 短線交易明細表 / 交易彙總表 | 16 | — |
| `OFDR752` | 集保基金下單檢核表 | 6 | — |

**Jaccard = 0.00,一個共同 key 都沒有。** `OFDR751` 查的是**日期區間 + 通路 + 交易類型 + 基金多選**;`OFDR752` 查的是**戶號 + 身分證號 + 下單序號區間 + 日期**。兩者都掛在「集保平台」下,**但一支看交易、一支看下單檢核,不是同一份資料**。與 `ofdi1.md` 記的 `OFDI751` / `OFDI752`(讀 `ORDR01` / `ORDR02`)**號碼相同但那是查詢畫面,不要混**。

#### 7.6.1 `OFDR751` 深寫:全片卡控最密的一支

16 條 `AddError`,全部集中在同一個檢核方法內。**全部是阻擋型**:

| # | 檢核 | 錨點 |
|---|---|---|
| 1 | 下單日期與交易日期必須擇一輸入 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR751.cs:414` |
| 2 | 下單日期(起)不可大於(迄) | `:421` |
| 3 | 下單日期(迄)為必填 | `:427` |
| 4 | 下單日期(起)為必填 | `:429` |
| 5 | 交易日期(起)不可大於(迄) | `:436` |
| 6 | 交易日期(迄)為必填 | `:442` |
| 7 | 交易日期(起)為必填 | `:444` |
| 8 | 下單日期(起)為必填(彙總表分支) | `:453` |
| 9 | 下單日期(迄)為必填(彙總表分支) | `:457` |
| 10 | 銷售機構區別碼(起)(迄)必須同時(不)輸入 | `:466` |
| 11 | 銷售機構區別碼(起)不可大於(迄) | `:473` |
| 12 | 銷售機構代碼(起)不可大於(迄) | `:482` |
| 13 | 交易內容至少要勾選一個項目 | `:493` |
| 14 | 資料種類至少要勾選一個項目 | `:501` |
| 15 | 至少勾選一筆基金代碼 | `:509` |
| 16 | (框架轉拋的自訂訊息) | `:399` |

**這 16 條是全庫報表檢核的最佳範本**,後續 189 支要抄就抄這支。特徵:

- **日期區間三段式**:擇一必填 → 起迄同時填 → 起不大於迄。三段缺一會有洞。

- **成對欄位「同時填或同時不填」**(第 10 條)是 R 特有的,M / I 很少見。

- **多選清單「至少一筆」**(第 13 ~ 15 條)——**不擋的話 SP 會收到空字串,回傳全部或全不回,兩種都是錯的**。

`OFDR751` 的三個 SP 依 `TYPE` / `Order` / `Short` / `Index` 四個旗標分流, 錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR751_PO.cs:60-74`:

| `TYPE` | `Order` | `Short` | `Index` | SP | `.rpt` |
|---|---|---|---|---|---|
| `1` | `1` | — | `0` 或 `1` | `S_TA_OFDR751_GET` | `OFDR751RPS` |
| `1` | — | `1` | `0` 或 `2` | `S_TA_OFDR751_SHOET_GET` | `OFDR751RPS2` |
| `2` | — | — | — | `S_TA_OFDR751_SUM_GET` | `OFDR751RPS3` |

**`Index` 的語意是「印兩張報表時這是第幾張」**(`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR751_PO.cs:74` 的註解原文)。 `0` 代表兩張都印。這是本片唯一一支**一次列印動作產出兩份報表**的畫面。

`S_TA_OFDR751_SHOET_GET` 的 `SHOET` **疑為 `SHORT` 拼錯**(短線交易)。 **不要「順手改正」**——SP 名在 DB 端,改 C# 這一行會直接讓畫面壞掉。

### 7.7 連號群 `OFDR731` / `OFDR733`:**兩支毫無關係**

| 代號 | 中文名 | 條件 key |
|---|---|---|
| `OFDR731` | 結匯申報收檔查核表 | (UI 不組,PO 內只有 `@striDECLARE_YM` 一個) |
| `OFDR733` | (信託業、投信業)國內貨幣市場共同基金受益憑證持有者統計表(月報 / 旬報) | `TYPE` `FUND_ID` `REG_YM` `EXECTYPE` |

**Jaccard = 0.00。** 一支是外匯結匯申報、一支是貨幣市場基金持有者申報,**共同點只有「都是對主管機關的申報」**(推測,依中文名)。 `OFDR732` 不存在,連號中間是斷的——**這本身就是「連號不代表同系列」的證據**。

`OFDR733` 有一處值得記:

```
this.EXECTYPE = "1";
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR733.cs:132`。 **寫在報表版型分支之後、送出之前,無條件覆蓋。** 畫面上另有 `uoptTYPE` 讓使用者選月報 / 旬報(`:124`), `EXECTYPE` 則完全不給選。**〔假設〕`EXECTYPE = "1"` 代表「列印」、另有 `"2"` 代表別的用途(例如產檔)**,依據是同名欄位在 `OFDR733` 的 SP 參數清單裡叫 `striEXECTYPE`,且 UI 有第二條路徑(TXT 匯出)。**沒有讀到定義,不確定。**

### 7.8 請款四支 `OFDR452` `OFDR453` `OFDR455` `OFDR457`:全片最重,也最會咬人

四支不是連號,但**結構是同一個模子刻的**,而且**四支都會寫 DB**。先看骨架(圖 4),再看四支哪裡不一樣。

#### 7.8.1 共同骨架

| 步 | 做什麼 | `OFDR452` 錨點 |
|---|---|---|
| 1 | `tran = m_db.BeginTransaction()` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:53` |
| 2 | `strDATAID = Guid.NewGuid().ToString()` 產一個本次執行的識別碼 | `:57` |
| 3 | 呼叫主 SP `S_TA_OFDR452_GET`,把 `iDATAID` 一起傳進去,**`ExecuteNonQuery`——SP 在 DB 端把計算結果寫進暫存工作區** | `:60-78` |
| 4 | 讀出參 `strMsg`;非 NULL 代表 SP 回報錯誤 → `tran.Rollback()`;NULL → `tran.Commit()` | `:84-97` |
| 5 | 逐一呼叫 `_A0_Get` ~ `_A5_Get` 六個 SP,各自 `LoadDataSet` 進不同結果集 | `:100-155` |
| 6 | 呼叫 `S_TA_OFDR452_DEL` 把暫存資料刪掉 | `:158-165` |
| 7 | `if (i > 0)` 決定回「成功」還是「查無相關資料」 | `:175` |

**所以「報表會寫 DB」這件事的真相是**:寫的是**暫存工作區**,不是業務表,而且步驟 6 會刪掉。這與 `OFDR022` `OFDR023` `OFDR564` 改業務旗標是**兩種不同的寫入**,做影響面評估時要分開看。

#### 7.8.2 缺陷一:`i = 1;` 蓋掉 `ExecuteNonQuery` 的回傳值(**四支全中**)

```
i = m_db.ExecuteNonQuery(cmd, tran);       // 真正的影響筆數
...
else
{
    i = 1;                                  // 無條件蓋掉
    tran.Commit();
}
...
if (i > 0)                                  // 於是永遠成立
```

四支的錨點:

| 畫面 | `ExecuteNonQuery` 取值 | `i = 1;` 覆蓋 | `if (i > 0)` 判斷 |
|---|---|---|---|
| `OFDR452` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:78` | `:96` | `:175` |
| `OFDR453` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR453_PO.cs:79` | `:96` | `:184` |
| `OFDR455` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR455_PO.cs:75` | `:91` | `:138` |
| `OFDR457` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR457_PO.cs:75` | `:91` | `:121` |

**這是 `ofdb5.md` 記過 12 處的同一型缺陷,在本片有 4 處。** 影響:SP 一筆都沒寫進去時,`ExecuteNonQuery` 回 0,但 `i` 被改成 1, 所以**畫面仍然報成功,只是報表是空的**。使用者看到空白報表不會知道是「沒資料」還是「算錯了」。嚴重度:中(不會錯帳,但診斷時會被誤導)。

#### 7.8.3 缺陷二:`OFDR455` `OFDR457` **不刪暫存資料**(成對只改一邊)

| 畫面 | 有沒有 `_DEL` SP | 有沒有執行刪除 |
|---|---|---|
| `OFDR452` | `S_TA_OFDR452_DEL` | 有,`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:158-165` |
| `OFDR453` | `S_TA_OFDR453_DEL` | 有,`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR453_PO.cs:179` |
| **`OFDR455`** | **沒有** | **沒有**——PO 內只有一次 `ExecuteNonQuery`(`:75`),之後沒有刪除呼叫 |
| **`OFDR457`** | **沒有** | **沒有**——同上(`:75`) |

四支用同一個 `Guid.NewGuid()` 暫存機制,**兩支會清、兩支不清**。影響:`OFDR455` `OFDR457` 每跑一次就在暫存工作區留一批資料,**沒有任何機制回收**。 **〔假設〕暫存表會無限成長**,依據是 C# 端找不到任何清除路徑,而 `OFDR452` `OFDR453` 明確有; 無法確認 DB 端是否另有排程清理(SP 不在版控)。嚴重度:高(長期資料量問題,且四支明明同型)。

#### 7.8.4 缺陷三:`tran.Rollback()` 在已 Commit 之後(**四支全中**)

`catch` 區一律:

```
catch (Exception ex)
{
    tran.Rollback();
    model.Utility.Result.AddResultRow(false, 0, string.Empty);
    CommonExceptionBlocker.HandleBusinessException(ex);
}
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:185-190` (`OFDR453_PO.cs:196` · `OFDR455_PO.cs:150` · `OFDR457_PO.cs:133` 同型)。

問題:`tran` 在步驟 4(`:97`)就已經 `Commit()` 了,步驟 5 ~ 7 全都在交易外。 **若例外發生在步驟 5 之後,`tran.Rollback()` 會對一個已完成的交易呼叫,拋 `InvalidOperationException`**, 把原始例外 `ex` 蓋掉——`CommonExceptionBlocker.HandleBusinessException(ex)` 那一行根本執行不到。 **真正的錯誤訊息永遠傳不出來。** 加上 `AddResultRow(false, 0, string.Empty)` 給的是空訊息, 畫面上使用者只會看到一個沒有內容的失敗。嚴重度:高(診斷能力歸零)。

#### 7.8.5 缺陷四:`DATA_TYPE` 三支三種做法

| 畫面 | 畫面上有沒有選項 | 送出的值 | 錨點 |
|---|---|---|---|
| `OFDR452` | **有**(`uoptDATA_TYPE`,還掛了 `ValueChanged` 事件) | 使用者選什麼送什麼 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR452.cs:192` · 事件在 `:1023-1025` |
| `OFDR455` | **沒有**(Designer 內查無 `uoptDATA_TYPE`) | **寫死 `"1"`** | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR455.cs:177` |
| `OFDR457` | **沒有** | **寫死 `"1"`** | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR457.cs:174` |
| `OFDR453` | 沒有 | **根本不送這個參數** | — |

`OFDR455.cs:62` `:155` 與 `OFDR457.cs:62` `:153` 都留著 `//this.uoptDATA_TYPE.Value = "1";` 的註解殘骸。

**這不算「過濾(無提示)」**——因為 `OFDR455` `OFDR457` 的畫面上本來就沒有那個選項,使用者不會以為自己能選。 **但它是「成對報表只改一邊」的實證**:同一組四支,對同一個概念做了四件不同的事。改 `DATA_TYPE` 的語意(例如新增 `'3'`)時,**必須同時檢查這四支,而 grep `DATA_TYPE` 只會找到三支**。嚴重度:中。

#### 7.8.6 `OFDR453`:請款四支裡唯一不出 Crystal 的

`OFDR453` 有 `IOFDR453_PO`、有七個 SP、有 `Model.xsd` / `View.xsd`,**但一張 `.rpt` 都沒有**。輸出全部走 `ExcelCreator.CreateExcelDocument(dt, sFileName)`, 錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:287`。

檔名由畫面上的控件文字串出來:

```
string sFileName = this.utxtPATH.Text + @"\" + m_CAL_DATE + "-"
                 + uchkQUERY_TYPE_B1.Text + "-" + uchkCAL_TYPE1.Text + @".xlsx";
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:284`。 **用控件的顯示文字當檔名的一部分**——改 UI 標題會連帶改輸出檔名,下游若有人照檔名收檔就會斷。嚴重度:低,但要記在**改 UI 文字前的檢查清單**上。

它的輸出路徑檢核是全片唯一一支做目錄存在性驗證的:

| 檢核 | 結果類型 | 錨點 |
|---|---|---|
| 需要輸入「輸出路徑」 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:121` |
| 輸出路徑不存在 | 阻擋 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:125` |

**這兩條應該被後面 189 支抄走**——其餘出檔的畫面(`OFDR235` `OFDR236` `OFDR237` `OFDR238`)是用 `SaveFileDialog` 讓使用者挑,由對話框保證路徑有效;`OFDR453` 是讓使用者打字,所以必須自己驗。

### 7.9 `OFDR716`:`.rpt` 引用懸空,本片唯一的版控外版型

```
if (...)      this.SetQueryParameters("OFDR716RPS",  "OFDR716RPS",  "開放式受益憑證登錄資料報表-FUY");
else if (...) this.SetQueryParameters("OFDR716RPS1", "OFDR716RPS1", "開放式受益憑證淨值傳檔資料報表-FUS");
else          this.SetQueryParameters("OFDR716RPS2", "OFDR716RPS2", "");
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR716.cs:50-56`。

第三個分支要的 `OFDR716RPS2`:

| 檢查 | 結果 |
|---|---|
| `Report.OFD` 資料夾內有 `OFDR716RPS2` 的 `.rpt`? | **否** |
| 伴生 `OFDR716RPS2.cs` 存在? | **否** |
| `Report.OFD.csproj` 內有宣告? | **否** |
| 報表中文名 | **空字串** |

**走到這個分支必定失敗。** 失敗點在伺服端: `Ctl` 的 `CRReportTransfer.TransferFileByte(rpt)`(`Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR013_Ctl.cs:32` 是同型範例) 拿 `"OFDR716RPS2"` 去 `%PTPF%\CrystalReports\` 找檔案,找不到。

三支 SP 對三個分支,而 `s_TA_OFDR716_2_Get` 是有的 (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR716_PO.cs`)—— **資料端做完了,版型端沒做。〔假設〕這是做到一半的功能**,依據是報表中文名留空(其餘 63 個引用都有中文名)。嚴重度:**高**——這是本片對「`.rpt` 不在版控」這個缺陷型的唯一實證,而且它不是「檔案掉了」,是**從來沒有過**。

`OFDR716` 的另外兩個版型 `FUY` / `FUS` 是集保平台的檔案類別代號〔客戶特定〕。

### 7.10 `OFDR540`:唯一動態組報表類別名的一支

39 支都是把 `.rpt` 名字寫成字面常數。`OFDR540` 不是:

```
case "6": case "7": case "8": case "9":
    sRpt = "OFDR540RPS" + this.uOptRptKind.Value.ToString();
    break;
default:
    sRpt = "";
    break;
```

錨點 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:90-139`。

十個選項對六個版型:

| `uOptRptKind` | 報表中文名 | 版型 | 版型存在 |
|---|---|---|---|
| `0` | 受益人會議開票結果 | `OFDR540RPS` | 是 |
| `1` | 亞太基金受益人大會投票明細表(未出席) | `OFDR540RPS1` | 是 |
| `2` | …(無效票) | `OFDR540RPS1` | 是 |
| `3` | …(贊成票) | `OFDR540RPS1` | 是 |
| `4` | …(反對票) | `OFDR540RPS1` | 是 |
| `5` | …(棄權票) | `OFDR540RPS1` | 是 |
| `6` | …(有效票) | `OFDR540RPS6` | 是 |
| `7` | 亞太基金受益人大會投票明細表 | `OFDR540RPS7` | 是 |
| `8` | 亞太基金受益人大會開票結果 | `OFDR540RPS8` | 是 |
| `9` | 亞太基金受益人大會開票結果 | `OFDR540RPS9` | 是 |
| 其他 | **空字串** | **空字串** | — |

六個版型全部在版控內,**所以這支目前是安全的**。 **但它是全片唯一一支「加一個選項就會自動去找一個新 `.rpt`」的畫面**—— 加第 10 個選項時若忘了加 `OFDR540RPS10.rpt`,會變成第二個 `OFDR716RPS2`,而且**編譯不會報錯**。 `default` 分支送空字串出去,一樣是執行期才爆。

另外注意:`8` 與 `9` 兩個選項的**報表中文名完全相同**(「亞太基金受益人大會開票結果」), 版型卻不同(`RPS8` / `RPS9`),註解分別寫「Agent 統計表」與「EMP 目標達成率表」 (`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:133-136`)。 **報表抬頭印出來會一樣,使用者分不出手上這張是哪一種。** 嚴重度:低,但會造成誤用。

`OFDR540` 也是唯一走 Oracle package 的一支:六個 SP 全是 `BF_VOTE.OFDR540_xxx` (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR540_PO.cs:65-96`)。 **其餘 39 支全是裸 procedure 名。** 改 `BF_VOTE` package 時要知道只有這一支在用。

### 7.11 只出 Excel 的兩支:`OFDR237` `OFDR453`

兩支都是「掛在報表專案下、UI 基底是 `xReportForm`、但沒有 `.rpt`」。

| 面向 | `OFDR237` | `OFDR453` |
|---|---|---|
| Excel 產生方式 | `Microsoft.Office.Interop.Excel` + 自家 `ExcelHelper.GenExcelFile` | `ExcelCreator.CreateExcelDocument` |
| 檔名由誰決定 | `SaveFileDialog` 讓使用者挑 | 畫面上的路徑欄 + 控件文字串出來 |
| 產生幾個檔 | 1 | 最多 5 組 × 4 種 = 依勾選而定 |
| 錨點 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR237.cs:210-244` | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:277-340` |

`OFDR237` 的 `// 此功能只開放Excel下載`(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR237.cs:126`) 證明**沒有 `.rpt` 是刻意的,不是漏做**——這一點與 `OFDR716RPS2`(漏做)要分清楚。

**但兩支的 UI 基底仍是 `xReportForm`**,所以框架給的「預覽 / 列印」按鈕還在畫面上。 **〔假設〕這兩支在 `FormInitial` 或 Designer 裡把兩顆按鈕關掉了**,依據是 `OFDR237` `OFDR453` 的程式碼裡完全沒有 `ButtonPreviewEnable = true` 這種打開的動作, 而其餘 38 支查詢成功後都會打開。**沒有讀 Designer,不確定按鈕是否真的隱藏。**

`OFDR237` 用 `Microsoft.Office.Interop.Excel`(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR237.cs:21`)—— **全片唯一一支要求用戶端裝 Office 的畫面**。其餘出 Excel 的走 `ExcelCreator` / `ExcelHelper`,不需要 Office。嚴重度:中(部署相依性隱藏在一支畫面的 `using` 裡)。

### 7.12 `OFDR022` `OFDR023`:不是報表,而且開畫面就壞

#### 7.12.1 它們在做什麼

兩支的 UI 基底是 `xOneStepProcessForm`(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR023.cs:15`), 一頁一顆「執行」按鈕,沒有查詢 / 預覽 / 列印。 `BeforeExecuteButtonClicked` 把條件塞進 `ProcessVDB.Util.Parameters` (`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR023.cs:41-62`),送到 PO。

PO 做兩件事:

1. 自組 SQL 撈出「該寄簡訊的受益人」;

2. 逐筆呼叫 `Sp_ForTa_Batch_Send` 把簡訊丟進共用寄送佇列,再 `UPDATE BMS001` 把寄發旗標改 `'Y'`。

**這是批次作業,不是報表。** 放在 `ATLAS.OFD.Report` 專案下是分類錯置。

#### 7.12.2 缺陷一:`m_db` 永遠是 null(**本片 13 支同型,這是最大的一條**)

```
private Database m_db = null;

public OFDR022_PO()
{
    //SystemConfigurationSource config = new SystemConfigurationSource();
    //DatabaseProviderFactory provider = new DatabaseProviderFactory(config);
    //m_db = provider.Create("TA");
}
...
DbConnection Dbcon = m_db.CreateConnection();   // ← NullReferenceException
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:17-24` 與 `:37`。

**逐檔掃過 40 支,`m_db` 從未被賦值的有 13 支**:

| 畫面 | `m_db` 宣告 | 首次解參考 |
|---|---|---|
| `OFDR002A` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:17` | `:33` |
| `OFDR013` | `OFDR013_PO.cs:17` | `:36` |
| `OFDR014` | `OFDR014_PO.cs:17` | `:35` |
| `OFDR015` | `OFDR015_PO.cs:17` | `:37` |
| `OFDR021` | `OFDR021_PO.cs:17` | `:36` |
| `OFDR022` | `OFDR022_PO.cs:17` | `:37` |
| `OFDR023` | `OFDR023_PO.cs:17` | `:38` |
| `OFDR024` | `OFDR024_PO.cs:17` | `:33` |
| `OFDR288` | `OFDR288_PO.cs:16`(初始化在 `/* */` 區塊內,`:20-23`) | `:44` |
| `OFDR501` | `OFDR501_PO.cs:18`(連 `= null` 都沒寫,預設 null) | `:47` |
| `OFDR563` | `OFDR563_PO.cs:18` | `:44` |
| `OFDR564` | `OFDR564_PO.cs:17` | `:44` |
| `OFDR731` | `OFDR731_PO.cs:17` | `:35` |

三項佐證這不是誤判:

1. **這 13 支同時是「沒有 `[PODbType(DbServerType.Oracle)]`」「沒有 `new Database("TA", DbServerType.Oracle)`」「用 `SqlDbType` 不用 `OracleDbType`」的那一批**——三個特徵完全重合。

2. `Ctl` 確實會 `new` 出 PO 並呼叫取數方法,沒有任何繞道: `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR013_Ctl.cs:37-41`。

3. `Dev/Common/` 底下找不到任何以反射注入私有欄位 `m_db` 的機制。

**〔假設〕這 13 支是 MSSQL 時代留下、Oracle 遷移時整批漏改的。** 依據:同樣的 `private Database m_db = null;` 在全 repo 有 104 個檔, 而在 `Dev/ATLAS.EC.Query` / `Dev/ATLAS.EC.Report` 底下,它們**住在 `MSSQL/` 子資料夾,旁邊有 `Oracle/` 覆寫版** (`ofdi1.md §0` 記過這個「基底版 + Oracle 覆寫版」寫法)。 **`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD` 底下沒有任何子資料夾**,所以這 13 支沒有覆寫版。

**無法百分之百確認的部分**:`Basic_PO` 是框架 DLL 類別(**無原始碼,從呼叫端反推**), 理論上它的建構子有可能透過某種機制設定衍生類別的私有欄位——但 C# 的私有欄位無法被基底類別直接寫入, 且這 13 支各自宣告自己的 `private Database m_db`(不是繼承來的),所以**除非用反射,否則不可能**;而反射機制在 repo 內找不到。

嚴重度:**最高**。若判讀正確,本片 40 支有 13 支(32.5%)完全不能跑。 **驗證方式**:在測試環境開 `OFDR013`(受益人查詢記錄報表)按查詢,看是否 `NullReferenceException`。 **這是本文最需要人工複驗的一條。**

#### 7.12.3 缺陷二:`catch` 裡的二次 NRE

```
catch (Exception ex)
{
    trans.Rollback();          // trans 在 NRE 發生時還是 null
    ...
}
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:177-183` (`OFDR023_PO.cs:133-139` 同型)。

`trans` 在 `Dbcon.Open()` 之後才 `BeginTransaction()`,而 NRE 發生在 `m_db.CreateConnection()`—— **`trans` 還是 null**,`trans.Rollback()` 再 NRE 一次,把原始例外蓋掉。 `finally` 區的 `Dbcon.Close()` 也會 NRE(`Dbcon` 同樣沒建出來)。使用者看到的是一個與根因完全無關的錯誤。嚴重度:高(診斷能力歸零)。

#### 7.12.4 缺陷三:`INNER JOIN` 讓對不到的受益人無聲消失

```
strSQL += "FROM	BMS001 " + Environment.NewLine;
strSQL += "INNER JOIN OFD132 ON OFD132.BF_NO=BMS001.BF_NO " + Environment.NewLine;
strSQL += "	      AND OFD132.STATEMENT_CODE='00' " + Environment.NewLine;
strSQL += "	      AND OFD132.SEND_CODE='Y' " + Environment.NewLine;
strSQL += "	      AND SEND_NEW_FLASH='Y' " + Environment.NewLine;
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:212-216`。

`BMS001` 有資料但 `OFD132` 沒有對應列的受益人,**整筆消失,沒有任何提示**。這是 `ofd6.md` 記的 `OFDM123_PO.cs:250-251` 同一型。 **在報表 / 寄送作業上更危險**:少寄一封通知,使用者只會看到「執行成功,筆數:N 筆」,不會知道 N 應該更大。結果類型:**過濾(無提示)**。嚴重度:高。

#### 7.12.5 缺陷四:`CELL_PHONE <> ''` 在 Oracle 上恆為 UNKNOWN

```
strSQL += "WHERE	CELL_PHONE <> ''  " + Environment.NewLine;
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:217`。

Oracle 把空字串視為 NULL,所以 `CELL_PHONE <> ''` 對**每一列**都是 UNKNOWN, `WHERE` 只收 TRUE,**結果是一列都不回**。這是 `ofdb5.md` 記的 `OFDB305_PO.cs:229`(`REMIT_FAIL_CODE=''`)同一型,**十個模組中過**。正確寫法是 `CELL_PHONE IS NOT NULL`。

**這一條與 §7.12.2 的 NRE 疊在一起**:即使有人把 `m_db` 修好,這支仍然一筆都撈不到。結果類型:**過濾(無提示)**,而且是全濾掉。嚴重度:高。

#### 7.12.6 缺陷五:重寄防護被註解掉

```
strUPD += "WHERE BF_NO=@BF_NO " + Environment.NewLine;
//strUPD += "  AND RECEIPT_DOC_ID <> 'Y'";
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:156-157`。

被註解掉的那一行原本是「已經是 `'Y'` 的就不再更新」。拿掉之後,同一個戶號重跑會再 `UPDATE` 一次。 **更重要的是:簡訊發送(`Sp_ForTa_Batch_Send`)在 `UPDATE` 之前就跑了**(`:121-132`), 所以**重跑一次就重寄一次簡訊**。註解本身也帶著 §7.12.5 的三值邏輯問題——就算解註解,`<> 'Y'` 遇到 `RECEIPT_DOC_ID` 為 NULL 的列一樣是 UNKNOWN。嚴重度:高(對外發送,不可回收)。

#### 7.12.7 缺陷六:寫死的簡訊內容,且 `A` / `B` 兩支完全相同

```
case "A": strMessage = "親愛的客戶：已收到您的開戶文件…德盛安聯投信"; break;
case "B": strMessage = "親愛的客戶：已收到您的開戶文件…德盛安聯投信"; break;   // 與 A 一字不差
case "C": strMessage = "親愛的客戶：已收到您的境外開戶文件…德盛安聯投信"; break;
```

錨點 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:105-118`。

三件事:

1. **`A`(綜合版)與 `B`(境內版)的文字一字不差**,分兩個 case 沒有意義。看註解 `//2013/03/27 Mod 境內版簡訊內容與綜合版一致`——是刻意改成一樣的,但沒有合併 case。

2. **公司名、客服電話寫死在 C# 裡**〔客戶特定〕。換站台要改程式重新編譯。

3. `case "A"` 的 SQL 判斷式(`:204-208`)把 `ELSE` 也導到 `'A'`,所以**沒有任何一列會落到 `'B'` 之外的預期分支**—— 實際上 `MsgType` 只會是 `'A'` 或 `'C'`。

嚴重度:中(維護性),但第 2 點在多站台佈署時是高。

#### 7.12.8 缺陷七:整支還在 T-SQL

`OFDR022_PO` / `OFDR023_PO` 用 `SqlDbType.NVarChar` 與 `@` 參數前綴 (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:124-131`), `Sp_ForTa_Batch_Send` 也是 T-SQL 的 `Sp_` 命名。 **〔假設〕整支是 MSSQL 時代的遺物**,與 §7.12.2 同源。

同型的還有兩處**語法層級**不可能在 Oracle 跑的:

| 畫面 | 內容 | 錨點 |
|---|---|---|
| `OFDR002A` | `LEFT JOIN [OFD038]` — **T-SQL 中括號識別字** | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:85` |
| `OFDR564` | `UpdateDate = GETDATE()` — **T-SQL 函式**,Oracle 是 `SYSDATE` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR564_PO.cs:126` |

這兩處**不可能被任何參數對映層救回來**,是語法錯誤。它們同時也都在 §7.12.2 那 13 支名單裡——**互相佐證那 13 支確實沒在跑**。

### 7.13 卡控總表

#### 7.13.1 阻擋型(38 支都有,列出各支的條數與最值得注意的一條)

| 畫面 | `AddError` 條數 | 最值得注意的一條 |
|---|---|---|
| `OFDR751` | 16 | 「銷售機構區別碼(起)(迄) 必須同時(不)輸入」 |
| `OFDR238` | 10 | (多條件組合) |
| `OFDR041` | 9 | (開戶缺件多條件) |
| `OFDR021` `OFDR453` | 8 | `OFDR453`:「輸出路徑不存在!」 |
| `OFDR040` `OFDR452` `OFDR455` `OFDR457` | 7 | 請款群共用同一套 |
| `OFDR043` `OFDR235` | 6 | — |
| `OFDR001A` `OFDR015` `OFDR024` `OFDR239` | 5 | `OFDR001A`:「該基金帳未平」(唯一驗輸出的) |
| `OFDR034` `OFDR236` `OFDR752` `OFDR286` `OFDR288` | 4 | — |
| `OFDR002A` `OFDR731` `OFDR733` `OFDR022` | 3 | — |
| `OFDR013` `OFDR014` `OFDR035` `OFDR501` `OFDR512` `OFDR563` | 2 | — |
| `OFDR237` `OFDR281` `OFDR282` `OFDR495` `OFDR511` `OFDR513` `OFDR540` `OFDR564` `OFDR716` | 1 | — |
| `OFDR023` | **0** | **這支完全沒有輸入檢核** |

`OFDR023` 是唯一一支一條檢核都沒有的畫面(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR023.cs` 全檔無 `AddError`), 而它的動作是**對外發簡訊**。條件全部可空,空白就等於「全部受益人」。嚴重度:**最高**(若 §7.12.2 判讀錯誤、這支其實跑得動的話)。

#### 7.13.2 過濾(無提示)型 —— **報表最危險的一類**

| # | 畫面 | 內容 | 使用者看得到嗎 | 錨點 | 嚴重度 |
|---|---|---|---|---|---|
| 1 | `OFDR022` | `INNER JOIN OFD132` 把沒有寄發設定的受益人整筆濾掉 | 看不到,只會看到「執行成功,筆數:N 筆」 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:213-216` | 高 |
| 2 | `OFDR022` | `CELL_PHONE <> ''` 在 Oracle 上全濾掉 | 看不到,顯示「無符合發送簡訊之資料」——**與「真的沒有」無法區分** | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:217` | 高 |
| 3 | `OFDR022` | `BMS001.BF_QT='N'` 寫死在 `WHERE` 裡,畫面上沒有這個條件 | 看不到 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:218` | 中 |
| 4 | `OFDR002A` | `OFD081V.FUND_ID <> 'ALL FUNDS'` 寫死排除一個特殊基金代碼 | 看不到;**在 Oracle 上若 `FUND_ID` 為 NULL 亦一併排除**(三值邏輯) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:90` | 中 |
| 5 | `OFDR013` `OFDR014` `OFDR015` `OFDR021` `OFDR024` `OFDR034` …(36 支) | **SP 內部的過濾條件完全看不到** | 完全看不到 | 71 個版控外 SP | **無法評估** |

**第 5 列才是真正的重點。** 前四列是能在 C# 裡讀到的,加起來只有 4 處; **36 支報表的過濾邏輯 100% 在版控外的 SP 裡**,本文無法列舉。 **所以「這張報表為什麼少印一列」這個問題,在 OFDR1 片區內,C# 層永遠給不出答案。** 要回答只有兩條路:(a) 去 DB 撈 SP 原始碼;(b) 把 SP 納入版控。

#### 7.13.3 詢問型:**0 支**

在 `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/` 底下搜 `FunctionDialogStyle.Question`、`ShowQuestion`、`DialogResult.Yes`,**一個檔都沒有命中**。

**本片沒有任何一支在做不可逆動作前跟使用者確認。** 包含:

- `OFDR022` `OFDR023` —— **對外發簡訊**,發出去收不回來;

- `OFDR564` —— 把 `OFD562` 的 `RECEIPT_DOC_ID2` 改成 `'Y'`;

- `OFDR452` `OFDR453` `OFDR455` `OFDR457` —— 重算請款資料。

`OFDR023` 最極端:**零檢核 + 零詢問 + 對外發簡訊**(§7.13.1)。

注意:自動掃描時 `Confirm` 這個關鍵字會被 `ConfirmDate` 欄名誤中, `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR022.cs:55-58` 就是誤中來源。逐條看過才確認是 0 支。

### 7.14 其餘各支(分群帶過)

深寫過的 18 支之外,其餘 22 支按業務線分群,只記「跟群內範本的差異」。

#### 7.14.1 受益人與客服群

| 畫面 | 中文名 | 跟範本(`OFDR013`)的差異 |
|---|---|---|
| `OFDR013` | 受益人查詢記錄報表 | 群內範本;`Basic_PO` 派,`m_db` 為 null(§7.12.2) |
| `OFDR014` | 客服通聯服務統計表 | 同型,SP 換成 `s_OFDR014_Get` |
| `OFDR015` | 資料需求統計表 | 多一組「建立日期起訖」,**空白時傳 `1900/01/01` ~ `9998/12/31`**(`Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR015.cs:80-81`)——寫死常數,`9999` 年的資料會被漏掉 |
| `OFDR034` | 客戶補件通知書 | `I<代號>_PO` 派,正常 |
| `OFDR035` | 受益人姓名／ID異動確認通知信列印作業 | 同 `OFDR034` |
| `OFDR040` | 受益人退郵資料 | 多兩段自組 SQL 填代碼下拉(`COD006A` 的 `'E2'` / `'E3'`,§2.3);另出 Excel |
| `OFDR043` | 受益人變更資料查核表 | 同 `OFDR034`,6 條檢核 |

#### 7.14.2 集保群

| 畫面 | 中文名 | 差異 |
|---|---|---|
| `OFDR024` | 集保網路/語音密碼申請明細表 | 條件在 `Customer_SetQueryParameters()` 內組,不走 UI 的 `AddParametersRow`;5 條阻擋型檢核 |
| `OFDR563` | 境外集保核印費彙總表 / 明細表 | 兩個版型依選項切;`Basic_PO` 派 |
| `OFDR564` | 境外核印失敗通知書 | **會寫 `OFD562.RECEIPT_DOC_ID2 = 'Y'`**,且 SQL 內有 `GETDATE()`(§7.12.8) |
| `OFDR752` | 集保基金下單檢核表 | `I<代號>_PO` 派,6 個條件,單一版型 |

#### 7.14.3 單位數、淨值與配息群

| 畫面 | 中文名 | 差異 |
|---|---|---|
| `OFDR236` | 淨值月報表 | 與 `OFDR235` 成對(§7.4);另出 Excel |
| `OFDR281` | 收益分配名冊 | 單版型,1 條檢核 |
| `OFDR282` | 收益分配付款彙總表 / 明細表 | 兩版型依選項切 |
| `OFDR286` | 收益分配扣繳憑單 / 扣繳清冊 / 海外所得 | **三版型**;另出 TXT;PO 有一處 `ExecuteScalar` |
| `OFDR288` | 配息專戶明細表 | **全片唯一一支 PO 既無基底也無介面**(`public class OFDR288_PO`),且 `m_db` 為 null |

#### 7.14.4 銷售統計群

| 畫面 | 中文名 | 差異 |
|---|---|---|
| `OFDR235` | 促銷活動明細表 / 彙總表 | 與 `OFDR236` 成對,多六個通路與活動代碼欄 |
| `OFDR238` | 每日銷售單位彙總表等四張 | **四個版型**,10 條檢核;另出 Excel |
| `OFDR239` | 銷售預估明細表等三張 | 群內唯一用 `stri` 前綴;UI key 與 SP 參數名對不上(§7.4) |
| `OFDR501` | 行銷身分群組明細表 | `Basic_PO` 派,最單純的一支 |

#### 7.14.5 清算、合併與申報群

| 畫面 | 中文名 | 差異 |
|---|---|---|
| `OFDR041` | 受益人開戶缺件查核表 / 交易缺件查核表 | 兩版型;9 條檢核;兩個 SP(`_GET` 與 `_GET_T`) |
| `OFDR495` | 基金合併確認單 | 兩個 SP;另出 TXT |
| `OFDR511` | 基金清算名冊列印作業 | 原始檔是 **cp950 編碼**(附錄 E) |
| `OFDR513` | 基金清算發放通知書 | 原始檔是 **cp950 編碼**;戶號空白傳 `-1`(§7.5.1) |
| `OFDR731` | 結匯申報收檔查核表 | `Basic_PO` 派;唯一參數 `@striDECLARE_YM` |

## 8. 跨模組共用

```text
[圖] OFDR1 讀的表分別由誰寫入,以及本片自己會寫回哪些表
圖中文字:規則:報表讀的表都不是報表建的。左欄=表,中欄=誰寫,右欄=本片誰讀 / BMS001 受益人開戶主檔 / 含 RECEIPT_DOC_ID 寄發旗標 / BMS 模組維護畫面 / 本片只讀 但 OFDR022 OFDR023 會改旗標 / OFDR022 OFDR023 / 兩支都是壞的 m_db 為 null / OFD081V 基金主檔檢視 / OFD038 基金分群 / OFD 模組維護畫面 / 基金資料的唯一寫入端 / OFDR002A / 唯一在 C# 裡看得到基金表的一支 / OFD303A 結帳控制 / CTL_DATE 過帳日期 / 結帳批次 OFDB 群 / 每日過帳後更新 / OFDR001A OFDR002A / 列印前要先驗這張表 沒過帳就阻擋 / OFD281A 收益分配 / OFD562 境外核印 / 配息與核印作業畫面 / OFDR564 會回寫 RECEIPT_DOC_ID2 / OFDR286 OFDR564 / 扣繳憑單 核印失敗通知 / OFD494A OFD496A 清算 / COD006A 代碼 CTL014 代碼 / CLS 清算模組 COD 代碼模組 / 本片只讀 / OFDR512 OFDR513 OFDR040 OFDR021 / 清算與代碼轉中文 / 反向:本片寫出去的東西 — 跟 I 不同,R 有 / 七支會寫 DB / OFDR022 023 452 453 455 457 564 / 兩類副作用 / 標記已寄送 與 請款計算結果寫回 / 影響面是雙向的 / 改共用表要回頭看這七支 這是 R 與 I 最大的差別
```

*圖:圖 5 跨模組。左欄=被讀的表,中欄=寫入端,右欄=本片的報表入口。灰虛框=純上游、本片只讀;紫框=本片也會寫的地方。最下面一排是 R 與 I 的分水嶺:`ofdi1.md` 的結論是「影響面完全單向」,在 R 不成立——本片七支會回寫,改共用表時必須雙向盤點。*

### 8.1 本片讀別人的:雙向,不是單向

`ofdi1.md §8` 的結論是「I 畫面的影響面完全單向:上游改欄位本片要跟著改,本片改動不影響任何人」。 **這句話在 R 不成立。** 本片 7 支會寫 DB(§0.2 第 20 列),所以影響面是雙向的。

| 被讀的表 | 誰寫入(推測) | 本片誰讀 | 本片誰**也寫** |
|---|---|---|---|
| `BMS001` | BMS 模組的維護畫面 | `OFDR022` `OFDR023` | **`OFDR022`**(`RECEIPT_DOC_ID` / `RECEIPT_DOC_ID2`) |
| `OFD132` | OFD 模組的文件寄發設定畫面 | `OFDR022` | — |
| `OFD081V` `OFD038` | OFD 模組的基金維護畫面 | `OFDR002A` | — |
| `OFD303A` | 結帳批次(OFDB 群) | `OFDR001A` `OFDR002A` | — |
| `COD006A` | COD 代碼模組 | `OFDR040` | — |
| `CTL014` | CTL 代碼模組(與 `ofdi1.md` 同一張) | `OFDR021` | — |
| `OFD281A` | 收益分配作業 | `OFDR286` | — |
| `OFD494A` `OFD496A` | CLS 清算模組 | `OFDR512` `OFDR513` | — |
| `OFD562` | 境外核印作業 | `OFDR564` | **`OFDR564`**(`RECEIPT_DOC_ID2`) |
| **(71 個 SP 內部讀的表)** | — | 36 支 | **`OFDR452` `OFDR453` `OFDR455` `OFDR457`** 的暫存工作區 |

**最後一列是重點**:36 支報表真正讀的表在版控外的 SP 裡,本表列不出來。所以「改 `OFDxxx` 這張表會影響哪些報表」這個問題,**用 grep 在本 repo 內問不出完整答案**。

### 8.2 本片的表被誰用:沒有自己的表

本片沒有任何一張專屬表。寫入的三個欄位(`BMS001.RECEIPT_DOC_ID` / `RECEIPT_DOC_ID2`、`OFD562.RECEIPT_DOC_ID2`)都是別人的表上的旗標。

### 8.3 共用元件

| 元件 | 來源 | 誰用 | 備註 |
|---|---|---|---|
| `xReportForm` | 框架 DLL,**無原始碼,從呼叫端反推** | 38 支 | 提供三顆按鈕、`m_ReportDocument`、`SetRptSchemaOnDoc()`、`SetQueryParameters()` |
| `xOneStepProcessForm` | 框架 DLL | 2 支 | 與 `ofdi1.md` 的 35 支 I 畫面用的是同一個 |
| `Basic_PO` | 框架 DLL | 13 支 | 提供 `LoadDataSet(db, cmd, ds, name)` 與 `ExecuteNonQuery(db, cmd, tran)` 兩個 `base.` 方法 |
| `BaseController` | 框架 DLL | 26 支 | — |
| `CRReportTransfer.TransferFileByte` | `Vendor.Product.TA.ServerUtility` | 全部 | 把 `.rpt` 位元組傳給客戶端 |
| `TransferVDBHelper` / `BasicTableTransferSetter` | 框架 | 全部 | Model ↔ View 整表搬 |
| `ClientBizUtility.GetFundBusinessDay` | `Vendor.Product.TA.ClientUtility` | `OFDR001A` 等 | 營業日檢核 |
| `DateTimeHelper` / `NumericHelper` / `SQLEVAHelper` / `EVAStringHelper` | 框架 | 多支 | 四個 helper 做的事高度重疊,不同世代各用一個 |
| `ExcelCreator` / `ExcelHelper` | 框架 | 6 支 | `OFDR237` 另外直接用 `Microsoft.Office.Interop.Excel` |
| `CommonExceptionBlocker.HandleBusinessException` | 框架 | 多支 | 與 `ofdi1.md` 記的同一個 |

**`SQLEVAHelper.GetParamValue` 與 `EVAStringHelper.GetParamValue` 做同一件事** (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR751_PO.cs:60` 對 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:63`), 外加 `OFDR001A_PO` 用的是不加前綴的 `GetParamValue(modelVDB, "FUND_ID")` (`Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:46`),`OFDR512_PO` 用 `this.GetParamValue(...)`。 **同一個動作四種寫法**,改參數取值行為時要四個地方都找。

### 8.4 改動影響面速查

| 改什麼 | 要回頭看誰 |
|---|---|
| `BMS001` 的 `RECEIPT_DOC_ID` / `RECEIPT_DOC_ID2` 語意 | `OFDR022`(讀+寫)、`OFDR023`(讀+寫) |
| `OFD562` 的 `RECEIPT_DOC_ID2` 語意 | `OFDR564`(讀+寫) |
| `OFD303A` 的 `CTL_DATE` | `OFDR001A` `OFDR002A` 的列印前檢核會整個失效 |
| `CTL014` 加代碼 | `OFDR021_PO.cs:130` 的八個 `SourceType` 寫死清單 |
| `COD006A` 的 `CODE_SORT` `'E2'` / `'E3'` | `OFDR040_PO.cs:163` `:208` |
| 任何一個 `.rpt` 的欄位 | 對應的 `Model.xsd` 與 `View.xsd`,**而且沒有編譯期檢查** |
| 任何一個 SP 的簽名 | 對應 PO 的 `AddInParameter` 清單;`OFDR512` 要改**兩段** |
| `BF_VOTE` package | 只有 `OFDR540` 在用 |
| `Sp_ForTa_Batch_Send` | `OFDR022` `OFDR023`,以及本 repo 外的簡訊寄送系統 |

## 附錄 A. 資料表總表

**本片無法產出完整資料表總表。** 原因見 §2.1 / §2.2: 40 支 PO 沒有 `MasterTable` 宣告,36 支的取數表名在版控外的 SP 內。以下是**在 C# 裡看得到的 13 張**,不是全部。

| 表 | 出現在 | 用途(推測) | 錨點 |
|---|---|---|---|
| `BMS001` | `OFDR022` `OFDR023` | 受益人開戶主檔 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:212` |
| `OFD132` | `OFDR022` | 文件寄發設定 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:213` |
| `OFD081V` | `OFDR002A` | 基金主檔檢視 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:84` |
| `OFD038` | `OFDR002A` | 基金分群 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:85` |
| `OFD303A` | `OFDR001A` `OFDR002A` | 結帳控制(過帳日期) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR001A_PO.cs:74` |
| `COD006A` | `OFDR040` | 共用代碼(退郵項目 / 原因) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR040_PO.cs:162` |
| `CTL014` | `OFDR021` | 全庫代碼對照 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR021_PO.cs:129` |
| `OFD281A` | `OFDR286` | 收益分配 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR286_PO.cs` |
| `OFD494A` | `OFDR512` `OFDR513` | 基金清算 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs` |
| `OFD496A` | `OFDR512` `OFDR513` | 基金清算 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs` |
| `OFD562` | `OFDR564` | 境外核印 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR564_PO.cs:123` |

## 附錄 B. SP / Function / Trigger / View

完整清單在 §2.2。摘要:

| 項目 | 數 |
|---|---|
| 不同的 SP / package procedure | **71** |
| 其中在 `/DB/` 版控內的 | **0** |
| Function | 0(`F_TA_STRTODATE` 出現在 `OFDR512` `OFDR513` 的 SQL 字串內,但那是 SP 內部呼叫,C# 只是把它寫進註解) |
| Trigger | 未見 |
| View | `OFD081V`(**假設**由 `V` 結尾判定,未核實) |

**71 個 SP 全部進 meta `refcheck-ignore`。**

## 附錄 C. 代碼對照

只列在 C# 裡讀得到的。**其餘代碼值在版控外的 SP 內。**

| 代碼 | 值 | 意義 | 錨點 |
|---|---|---|---|
| `BMS001.OPEN_BF_TYPE` | `'1'` / `'2'` | 境內開戶 / 境外開戶 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:204-208` |
| `MsgType`(`OFDR022` 內部計算欄) | `'A'` / `'B'` / `'C'` | 綜合版 / 境內版 / 境外版簡訊 | 同上 |
| `BMS001.RECEIPT_DOC_ID` / `RECEIPT_DOC_ID2` | `'Y'` / `'N'` | 境內 / 境外開戶文件已寄發 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:137-157` |
| `OFD132.STATEMENT_CODE` | `'00'` | 開戶文件寄發碼 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:214` |
| `COD006A.CODE_SORT` | `'E2'` / `'E3'` | 退郵項目 / 退郵原因 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR040_PO.cs:163` `:208` |
| `CTL014.SourceType` | `'415'` `'085'` `'087'` `'138'` `'143'` `'413'` `'146'` `'064'` | `OFDR021` 用到的八類代碼〔客戶特定〕 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR021_PO.cs:130` |
| `OFDR540` 的 `uOptRptKind` | `'0'` ~ `'9'` | 十種票別報表〔客戶特定〕 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:113-137` |
| `OFDR716` 的 `uoptTYPE` | `0` `1` `2` | `FUY` 登錄 / `FUS` 淨值傳檔 / **無版型**〔客戶特定〕 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR716.cs:50-56` |
| `OFDR751` 的 `TYPE` / `Order` / `Short` / `Index` | `'1'` `'2'` / `'1'` / `'1'` / `'0'` `'1'` `'2'` | 報表種類 / 下單資料 / 短線 / 第幾張 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR751_PO.cs:60-74` |
| `OFDR733` 的 `uoptTYPE` | `'1'` / `'2'` | 月報 / 旬報 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR733.cs:124-131` |
| `DATA_TYPE`(請款群) | `'1'` / `'2'` | 計算資料來源,`'2'` 的語意只有 `OFDR452` 知道 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR452.cs:1023-1025` |
| `OFDR513` 的 `striBF_NO_0` | `'-1'` | 戶號空白時的「全部」哨兵值 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR513.cs:79` |
| `OFDR015` 的日期預設 | `'1900/01/01'` ~ `'9998/12/31'` | 未輸入時的「全部」區間 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR015.cs:80-81` |

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module OFD`**——那會拿 551 支 OFD 畫面來比,對一份只涵蓋 40 支的切片沒有意義。以下是本片自列的 40 支處置表。

圖例:**已寫** = §7 有專屬小節;**表格帶過** = 只在 §3 清冊與 §7.14 出現。

| # | 代號 | 處置 | PO 基底 | 資料來源 | `.rpt` 在版控 | 在 csproj | `m_db` 可用 |
|---|---|---|---|---|---|---|---|
| 1 | `OFDR001A` | **已寫** §7.2 | `IOFDR001A_PO` | SP | 是 | 是 | 是 |
| 2 | `OFDR002A` | **已寫** §7.2 | `Basic_PO` | SP+SQL | 是 | 是 | **否** |
| 3 | `OFDR013` | 表格帶過 §7.14.1 | `Basic_PO` | SP | 是 | 是 | **否** |
| 4 | `OFDR014` | 表格帶過 §7.14.1 | `Basic_PO` | SP | 是 | 是 | **否** |
| 5 | `OFDR015` | 表格帶過 §7.14.1 | `Basic_PO` | SP | 是 | 是 | **否** |
| 6 | `OFDR021` | **已寫** §7.3 | `Basic_PO` | SP+SQL | 是 | 是 | **否** |
| 7 | `OFDR022` | **已寫** §7.12 | `Basic_PO` | SQL | 不適用 | 是 | **否** |
| 8 | `OFDR023` | **已寫** §7.12 | `Basic_PO` | SQL | 不適用 | 是 | **否** |
| 9 | `OFDR024` | 表格帶過 §7.14.2 | `Basic_PO` | SP | 是 | 是 | **否** |
| 10 | `OFDR034` | 表格帶過 §7.14.1 | `IOFDR034_PO` | SP | 是 | 是 | 是 |
| 11 | `OFDR035` | 表格帶過 §7.14.1 | `IOFDR035_PO` | SP | 是 | 是 | 是 |
| 12 | `OFDR040` | 表格帶過 §7.14.1 | `IOFDR040_PO` | SP+SQL | 是 | 是 | 是 |
| 13 | `OFDR041` | 表格帶過 §7.14.5 | `IOFDR041_PO` | SP | 是 | 是 | 是 |
| 14 | `OFDR043` | 表格帶過 §7.14.1 | `IOFDR043_PO` | SP | 是 | 是 | 是 |
| 15 | `OFDR235` | **已寫** §7.4 | `IOFDR235_PO` | SP | 是 | 是 | 是 |
| 16 | `OFDR236` | **已寫** §7.4 | `IOFDR236_PO` | SP | 是 | 是 | 是 |
| 17 | `OFDR237` | **已寫** §7.11 | `IOFDR237_PO` | SP | 不適用 | 是 | 是 |
| 18 | `OFDR238` | 表格帶過 §7.14.4 | `IOFDR238_PO` | SP | 是 | 是 | 是 |
| 19 | `OFDR239` | **已寫** §7.4 | `IOFDR239_PO` | SP | 是 | 是 | 是 |
| 20 | `OFDR281` | 表格帶過 §7.14.3 | `IOFDR281_PO` | SP | 是 | 是 | 是 |
| 21 | `OFDR282` | 表格帶過 §7.14.3 | `IOFDR282_PO` | SP | 是 | 是 | 是 |
| 22 | `OFDR286` | 表格帶過 §7.14.3 | `IOFDR286_PO` | SP | 是 | 是 | 是 |
| 23 | `OFDR288` | 表格帶過 §7.14.3 | **無基底無介面** | SP | 是 | 是 | **否** |
| 24 | `OFDR452` | **已寫** §7.8 | `IOFDR452_PO` | SP | 是 | 是 | 是 |
| 25 | `OFDR453` | **已寫** §7.8 | `IOFDR453_PO` | SP | 不適用 | 是 | 是 |
| 26 | `OFDR455` | **已寫** §7.8 | `IOFDR455_PO` | SP | 是 | 是 | 是 |
| 27 | `OFDR457` | **已寫** §7.8 | `IOFDR457_PO` | SP | 是 | 是 | 是 |
| 28 | `OFDR495` | 表格帶過 §7.14.5 | `IOFDR495_PO` | SP | 是 | 是 | 是 |
| 29 | `OFDR501` | 表格帶過 §7.14.4 | `Basic_PO` | SP | 是 | 是 | **否** |
| 30 | `OFDR511` | **已寫** §7.5 | `IOFDR511_PO` | SP | 是 | 是 | 是 |
| 31 | `OFDR512` | **已寫** §7.5 | `IOFDR512_PO` | SP | 是 | 是 | 是 |
| 32 | `OFDR513` | **已寫** §7.5 | `IOFDR513_PO` | SP | 是 | 是 | 是 |
| 33 | `OFDR540` | **已寫** §7.10 | `IOFDR540_PO` | SP | 是 | 是 | 是 |
| 34 | `OFDR563` | 表格帶過 §7.14.2 | `Basic_PO` | SP | 是 | 是 | **否** |
| 35 | `OFDR564` | 表格帶過 §7.14.2 | `Basic_PO` | SP | 是 | 是 | **否** |
| 36 | `OFDR716` | **已寫** §7.9 | `IOFDR716_PO` | SP | **否** | 是 | 是 |
| 37 | `OFDR731` | **已寫** §7.7 | `Basic_PO` | SP+SQL | 是 | 是 | **否** |
| 38 | `OFDR733` | **已寫** §7.7 | `IOFDR733_PO` | SP | 是 | 是 | 是 |
| 39 | `OFDR751` | **已寫** §7.6 | `IOFDR751_PO` | SP | 是 | 是 | 是 |
| 40 | `OFDR752` | **已寫** §7.6 | `IOFDR752_PO` | SP | 是 | 是 | 是 |

**統計**:

| 項 | 數 |
|---|---|
| 已寫專屬小節 | 22 |
| 表格帶過 | 18 |
| `.rpt` 在版控 | 36 / 36 有 `.rpt` 的畫面中 35 支全在;`OFDR716` 有一個懸空引用 |
| 不在 csproj | **0** |
| `m_db` 為 null(**推測不可執行**) | **13** |

### D.1 不在本片的 5 支(劃給下一片)

`OFDR285` `OFDR287` `OFDR461` `OFDR561` `OFDR562`。它們在同一個專案內,共用同樣的七層結構。快速標記,方便下一片接手:

| 代號 | 已知特徵 |
|---|---|
| `OFDR285` | **最大的一支 UI(近 1000 行)**;PO 有 `INSERT` `DELETE` `ExecuteScalar`,是本專案唯一有 `INSERT INTO` 的 PO;UI 另有一個 `OFDR285p0.cs` 分部檔 |
| `OFDR287` | 兩個版型,中文名相同(「無配息帳號名冊」) |
| `OFDR461` | **檔名兩處例外**:`OFDR461_PXy.cs`(大寫 X)、`OFDR461_Ct.cs`(少一個 `l`) |
| `OFDR561` | `Basic_PO` 派,`SqlDbType`,推測同樣 `m_db` 為 null |
| `OFDR562` | 同 `OFDR561` |

## 附錄 E. 讀本文時要注意的地方

依嚴重度排序。每條:缺陷 / 影響 / 錨點 / 嚴重度。 **標「型」的欄位對應交辦的缺陷型錄**,方便後面 189 支比對。

| # | 型 | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|---|
| E1 | **繼承基底 → 連查詢都 NRE** | **13 支 PO 的 `m_db` 永遠是 null**,初始化被註解掉,第一行就解參考 | 若判讀正確,本片 40 支有 13 支完全不能跑(32.5%)。清單與三項佐證見 §7.12.2 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:17-24` 與 `:37`(其餘 12 支同型,逐支行號見 §7.12.2) | **最高** |
| E2 | **`.rpt` 不在版控**(報表獨有) | `OFDR716` 第三分支要 `OFDR716RPS2`,**檔案、伴生 `.cs`、csproj 宣告三者皆無**,報表中文名也是空字串 | 走到該分支必定執行期失敗,編譯不報錯 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR716.cs:56` | **高** |
| E3 | **`INNER JOIN` 讓對不到的資料無聲消失** | `OFDR022` 的 `INNER JOIN OFD132`,沒有寄發設定的受益人整筆消失 | **過濾(無提示)**;少寄的簡訊使用者不會知道 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:213-216` | 高 |
| E4 | **Oracle 三值邏輯** | `OFDR022` 的 `WHERE CELL_PHONE <> ''`;Oracle 把 `''` 當 NULL,整句恆為 UNKNOWN | **一列都不回**,畫面顯示「無符合發送簡訊之資料」,與「真的沒有」無法區分 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:217` | 高 |
| E5 | **迴圈外的清理被漏做**(成對只改一邊) | `OFDR455` `OFDR457` 沒有 `_DEL` SP、沒有刪除呼叫;`OFDR452` `OFDR453` 有 | 暫存工作區每跑一次留一批,**〔假設〕無限成長**(DB 端是否另有清理無法確認) | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR455_PO.cs:75` · `OFDR457_PO.cs:75`(對照 `OFDR452_PO.cs:158-165`) | 高 |
| E6 | **`catch` fail-open / 例外被二次例外蓋掉** | 請款四支的 `catch` 對已 `Commit` 的交易呼叫 `Rollback()`,拋 `InvalidOperationException` 蓋掉原例外;`AddResultRow(false, 0, string.Empty)` 給空訊息 | 真正的錯誤訊息永遠傳不出來 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs:185-190`(`OFDR453_PO.cs:196` · `OFDR455_PO.cs:150` · `OFDR457_PO.cs:133`) | 高 |
| E7 | 同上 | `OFDR022` `OFDR023` 的 `catch` 對 null 的 `trans` 呼叫 `Rollback()`,`finally` 再對 null 的 `Dbcon` 呼叫 `Close()` | 使用者看到的錯誤與根因完全無關 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:177-183` · `OFDR023_PO.cs:133-139` | 高 |
| E8 | **被註解掉的檢核** | `OFDR022` 的重寄防護 `AND RECEIPT_DOC_ID <> 'Y'` 被註解;簡訊在 `UPDATE` 之前就發了 | **重跑一次就重寄一次簡訊**,對外不可回收 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:157` | 高 |
| E9 | **零檢核** | `OFDR023` 全檔沒有一條 `AddError`,也沒有確認對話框,動作是對外發簡訊 | 條件全可空,空白等於「全部受益人」 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR023.cs` 全檔 | 高 |
| E10 | **`i = 1;` 蓋掉 `ExecuteNonQuery` 回傳值** | 請款四支全中;`if (i > 0)` 因此永遠成立 | SP 零筆時仍報成功,報表空白;診斷時被誤導 | `OFDR452_PO.cs:78` → `:96` → `:175`(其餘三支見 §7.8.2) | 中 |
| E11 | **T-SQL 殘留:語法層級** | `OFDR002A` 的 `LEFT JOIN [OFD038]`(中括號識別字)、`OFDR564` 的 `GETDATE()` | Oracle 上是語法錯誤,不可能被參數對映層救回;同時佐證 E1 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR002A_PO.cs:85` · `OFDR564_PO.cs:126` | 中(若 E1 成立則是死碼) |
| E12 | **T-SQL 殘留:型別與參數前綴** | 12 支 PO 只用 `SqlDbType`、一個 `OracleDbType` 都沒有,參數名帶 `@` | 與 E1 是同一批;未遷移的證據 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:124-131`(清單見 §7.12.8) | 中 |
| E13 | **字串串接進 SQL** | `OFDR022` `OFDR023` 把使用者輸入的 `ID_NO` `BF_NO` 日期直接串進 `WHERE` | SQL 注入;`ofdi1.md` 同型在 I 有 13 支,在 R 只有這 2 支 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:250` `:253` `:256` `:259` `:263` 起 | 中(因 E1 目前跑不到) |
| E14 | **成對報表只改一邊** | 請款四支對 `DATA_TYPE` 做了四件不同的事:`OFDR452` 可選、`OFDR455` `OFDR457` 寫死 `'1'`、`OFDR453` 不送 | grep `DATA_TYPE` 只會找到三支,漏掉 `OFDR453` | `OFDR452.cs:192` · `OFDR455.cs:177` · `OFDR457.cs:174` | 中 |
| E15 | **非 UTF-8 來源檔** | `OFDR511.cs` 與 `OFDR513.cs` 是 **cp950**,其餘 38 支是 UTF-8 | 用 UTF-8 讀會得到亂碼(`����M��W�U�C�L�@�~`);任何 grep 中文的工具在這兩支上失準。**`atlas_scan.read_text` 會自動偵測,直接用 `open()` 會壞** | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR511.cs:49` · `OFDR513.cs:71` | 中 |
| E16 | **`.rpt` 與 `.cs` 的第三份 schema 沒有編譯期保護** | `SetRptSchemaOnDoc()` 是唯一綁定點;`.rpt` 是二進位,欄位對不上不會編譯錯 | **報表欄位與 xsd 不同步**(報表獨有型)的結構性成因。本文無法檢出實例(不 Read `.rpt`) | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR001A.cs:290` | 中(結構性) |
| E17 | **檔名不照規則** | `OFDR452_PXy.cs` / `OFDR461_PXy.cs` 大寫 X;`OFDR461_Ct.cs` 少一個 `l` | 照代號硬推檔名的工具會漏;`misc.md` 的 `TRP001_PO.cs` 同型 | `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR452_PXy.cs` · `Dev/ATLAS.OFD.Report/Source/Control/ReportControl.OFD/OFDR461_Ct.cs` | 中(工具面) |
| E18 | **寫死常數** | `OFDR022` 的簡訊全文、公司名、客服電話寫在 C# 裡;`A` / `B` 兩個 case 文字一字不差 | 換站台要改程式重新編譯〔客戶特定〕 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:105-118` | 中 |
| E19 | **寫死常數** | `OFDR021` 把 `CTL014` 的八個 `SourceType` 寫死;與 `ofdi1.md` 記的六個完全不重疊 | `CTL014` 加代碼沒有集中的地方可改 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR021_PO.cs:130` | 中 |
| E20 | **動態組資源名** | `OFDR540` 用 `"OFDR540RPS" + 選項值` 組版型名;`default` 送空字串 | 加選項忘了加 `.rpt` 會變成第二個 E2,編譯不報錯 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:107` `:110` | 中 |
| E21 | **同一支內兩套參數慣例** | `OFDR512_PO` 前段用 `stri` / `dati` / `int` 前綴,後段用裸欄名 | 改 SP 簽名時搜 `striFUND_ID` 只找到一半 | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR512_PO.cs:61-76` 對 `:127-131` | 中 |
| E22 | **UI key 與 SP 參數名對不上** | `OFDR239` 的 UI 傳 `CTL_DATE_ST/END`,PO 綁到 SP 的 `striALLOT_DATE_ST/ED` | 搜 `ALLOT_DATE` 找不到 UI 端 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR239.cs` 對 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR239_PO.cs` | 低 |
| E23 | **寫死常數** | `OFDR015` 未輸入日期時傳 `1900/01/01` ~ `9998/12/31` | `9999` 年資料會被漏掉;哨兵值語意只在 SP 內 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR015.cs:80-81` | 低 |
| E24 | **寫死常數** | `OFDR513` 戶號空白時傳 `-1`;`OFDR511` `OFDR512` 沒有這個約定 | 同群三支對「全部」的表示法不一致 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR513.cs:79` | 低 |
| E25 | **兩個選項同一個報表抬頭** | `OFDR540` 的 `8` 與 `9` 中文名完全相同,版型不同 | 印出來分不出是哪一種 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR540.cs:133-136` | 低 |
| E26 | **控件顯示文字被當檔名** | `OFDR453` 用 `uchkQUERY_TYPE_B1.Text` 串輸出檔名 | 改 UI 標題會連帶改檔名,下游照檔名收檔會斷 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR453.cs:284` | 低 |
| E27 | **隱藏的部署相依** | `OFDR237` 直接 `using Microsoft.Office.Interop.Excel` | 該支要求用戶端裝 Office;其餘出 Excel 的不用 | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR237.cs:21` | 低 |
| E28 | **同功能四個 helper** | `SQLEVAHelper.GetParamValue` / `EVAStringHelper.GetParamValue` / 裸 `GetParamValue` / `this.GetParamValue` | 改參數取值行為要四處找 | §8.3 | 低 |
| E29 | **範本註解殘留** | 13 支 `Basic_PO` 派的 UI 留著 `//@@@ 步驟2 :指定報表ClassName` | 無功能影響,但會干擾 grep | `Dev/ATLAS.OFD.Report/Source/UI/ReportUI.OFD/OFDR014.cs:60` | 低 |

### E.30 交辦缺陷型錄的逐項核對

| 缺陷型 | 本片有沒有 | 條目 |
|---|---|---|
| `INNER JOIN` 讓對不到的資料無聲消失 | **有,1 處** | E3 |
| 字串串接進 SQL | **有,2 支** | E13 |
| Oracle 三值邏輯 | **有,2 處**(`<> ''` 與 `<> 'ALL FUNDS'`) | E4、§7.13.2 第 4 列 |
| `AND` / `OR` 缺括號 | **未發現** | — |
| `LIKE` 樣式餵給 `=` | **未發現** | — |
| 繼承 `BasicEVAPO` → 連查詢都 NRE | **本片沒有 `BasicEVAPO`,但有更嚴重的同型:`m_db` 為 null,13 支** | E1 |
| `catch` fail-open | **有,兩型** | E6、E7 |
| `i = 1;` 蓋掉 `ExecuteNonQuery` 回傳值 | **有,4 處** | E10 |
| `catch (SqlException)` 在 Oracle 上是死碼 | **未發現**(本片一律 `catch (Exception)`) | — |
| 成對報表只改一邊 | **有,2 組**(請款四支的 `DATA_TYPE`、`_DEL` 清理) | E14、E5 |
| 基底版與 Oracle 覆寫版讀不同表 | **不適用**——本專案沒有 `Oracle/` 覆寫資料夾 | §7.12.2 |
| 迴圈 `break` 吞掉後續資料列 | **未發現** | — |
| 寫死常數 | **有,5 處** | E18、E19、E23、E24、§7.8.5 |
| 位置取參數 | **未發現**(全部具名) | — |
| 非 UTF-8 來源檔 | **有,2 支** | E15 |
| 檔案存在但不在 csproj | **0 支**(240 個檔全在) | §3.5 第 1 點 |
| **`.rpt` 不在版控** | **有,1 處懸空引用** | E2 |
| **報表欄位與 xsd 不同步** | **無法檢出**(不 Read `.rpt`);但記下結構性成因 | E16 |

### E.31 最需要人工複驗的一條

**E1。** 若 13 支真的全部 NRE,那是重大事故;若 `Basic_PO` 有本文沒找到的機制,那 E1 整條要撤。 **驗證成本很低**:在測試環境開 `OFDR013`(受益人查詢記錄報表)按查詢,看有沒有 `NullReferenceException`。在複驗之前,**E11 E12 E13 這三條的嚴重度都依附在 E1 上**——如果那 13 支根本沒在跑,它們就只是死碼。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。全庫第一篇報表(R)文件,建立 §0.2 的 M / I / R 三欄對照表與 §2.6 的 `.rpt` 對應表兩個新章節型式,供後續 189 支報表沿用。 |

由 build_doc.py v2.0.0 於 2026-09-15 20:44 產生 · 標題 96 · 圖 5 · 表格 61 · 程式錨點 176 · § 連結 126 · 引用檢查：畫面 51（缺 0） · Table 5（缺 0） · Report 66（缺 0） · 結果集 11（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
