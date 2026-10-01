ATLAS 知識庫 — 16-模組-OFDI查詢-OFDR報表

本檔合併以下文件:modules/ofdi1.md、modules/ofdi2.md、modules/ofdr1.md、modules/ofdr2.md


============================================================
【文件】kb/modules/ofdi1.md
============================================================

# ATLAS OFDI1 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:**第一次讀查詢畫面的人,只讀 §0.2 那張 I vs M 對照表就夠用**——後面每一片查詢篇都以它為前提。要動手改某一支的人,查 §3 清冊定位,再跳 §5 的對應小節。急著知道哪裡會咬人的人直接翻附錄 E。

> ⚠ **OFDI1 不是一個業務模組,是一份切片。** 這是全庫第一篇專門寫**查詢畫面(I)**的文件。OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD.Query` 這個獨立方案底下的 **35 支 I 畫面**。切片依據是專案資料夾與型別碼,不是業務;所以本片內部含**六條互不相干的業務線**(§0.3)。名稱 `OFDI1` 為**推測**,取自「OFD 的 I 畫面第 1 片」。

> ⚠ **前 21 篇都是 M(維護)或 B(批次)。** 本篇建立的章節配置會被後續查詢片沿用:**§4 是空的、§5 才是主體**,§6 §7 同樣是空的。

> ⚠ **本片的業務意義**(§0)由表名、畫面上的中文控件標題與 SQL 的 `SELECT` 欄位**推測**,待選單表回填。畫面中文名 ATLAS 不存在 code 內(35 支 Designer 都沒有 `this.Text` 指派),只能由控件標題反推。

> ⚠ **〔客戶特定〕**:集保(TDCC)檔案格式 `TRP8xx` / `ORDR0x`、FATCA 與 CRS 申報欄位、`CTL014` 的 `SourceType` 編號(`'000'` / `'100'` / `'149'` / `'204'` / `'232'` / `'236'`)為本站台的值。

> ⚠ **〔共用〕**:`OFD081A` `OFD081V` `BMS001A` `COD009` `CTL014` `OFD020V` 幾乎每一支都讀,改欄位會同時打到本片十幾支畫面(見 §8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別四種看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

```text
[圖] I 查詢畫面與 M 維護畫面的六層差異對照
圖中文字:M 維護畫面:六層滿血 + 四眼 / UI xMaintainForm / 兩個 TabPage,掛 Add/Modify 事件 / Pxy Basic_Pxy / Add / Modify / Delete / Select / Ctl BaseController / InitializeVDBTypes 有覆寫 / PO BaseEVADaoPO / MasterTable + DetailTable / Model.xsd 是實體表形狀 / 欄位對齊 DB 欄位,含四眼 13 欄 / View.xsd 與 Model 同構 / 逐欄手搬 / 四眼引擎 EVA / Entry / Verify / Approve / Reject 寫回同一批表 / I 查詢畫面(本片 35 支):同樣六層,但後三層意義完全不同 / UI xOneStepProcessForm / 一頁式,只有查詢一個動作 / Pxy Basic_Pxy / 通常只有 Select / GetExcelData / Ctl BaseController / InitializeVDBTypes 35 支全無 / PO 三派基底並存 / 無基底20 BaseEVADaoPO12 BasicEVAPO3死 / Model.xsd 是結果集形狀 / 根節點常叫 OFDI0xx,不是實體表名 / View.xsd 多半同構 兩支例外 / OFDI060 / OFDI702 欄數不等 / 無四眼、無寫入路徑 / MasterTable 35 支全無宣告;LoadDataSet 之外沒有任何 Execute / 真正的分水嶺:條件從哪裡來、怎麼進 SQL / M 值由 Model 逐欄搬 / 使用者改的是資料列,PO 用參數化 UPDATE / I 值由 Utility.Parameters 帶 / 使用者打的是條件字串,13 支直接串進 SQL
```

*圖:圖 2 I vs M。上半 M、下半 I。六層的檔案都在,但 I 的後三層是空殼:Ctl 不宣告 VDB 型別、PO 不宣告主明細表、xsd 不是實體表形狀。紫框是本片的風險點——最下面那一格是全片缺陷的根源(§5.2、附錄 E.1)。*

### 0.1 先更正一件事:OFD.Query 的 PO 就叫 `<代號>_PO.cs`

動手前先破除一個會浪費半天的假設。**`ATLAS.OFD.Query` 底下沒有任何 `OracleDao` 檔**—— `find Dev/ATLAS.OFD.Query -name "*OracleDao*"` 的結果是 0 筆。六層檔名與 M 畫面完全一致,只是資料夾與組件名多了 `Query` 前綴:

| 層 | 資料夾 | 檔名 | 例 |
|---|---|---|---|
| UI | `Source/UI/QueryUI.OFD/` | `<代號>.cs` | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs` |
| FormProxy | `Source/FormProxy/QueryFormProxy.OFD/` | `<代號>_Pxy.cs` | `Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` |
| Control | `Source/Control/QueryControl.OFD/` | `<代號>_Ctl.cs` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs` |
| PO | `Source/PO/QueryPO.OFD/` | **`<代號>_PO.cs`** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs` |
| DataEntity | `Source/Entity/QueryDataEntity.OFD/` | `<代號>Model.xsd` | `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` |
| UIEntity | `Source/Entity/QueryUIEntity.OFD/` | `<代號>View.xsd` | `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI716View.xsd` |

`OracleDao` 這個檔名慣例存在,但**只在 EC 那一條線**: `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/`(48 支)、 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/`(10 支)、 `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/`(8 支)、 `Dev/Common/Source/DataSource/PO.DataSource/Oracle/`(6 支)、 `Dev/Common/Source/Utility/TA.UtilityPO/Oracle/`(3 支)。那是 EC 在 MSSQL→Oracle 遷移時採的「基底版 + Oracle 覆寫版」寫法(`ofd4.md 附錄 E` 記過兩版讀不同表的事故); **OFD.Query 沒走這條路,它是直接把 SQL 改寫成 Oracle 語法蓋回原檔**,所以只有一份 PO。這個差別直接造成本片最大的一類缺陷:**改漏的那幾支還留著 T-SQL**(§5.9、附錄 E.2)。

### 0.2 I 查詢畫面與 M 維護畫面差在哪(本片最重要的一張表)

`architecture.md §6.3` 用 `CASI001` 當樣本,得到「I 的 PO 退化成裸 DAO、沒有基底」的結論。 **這個結論在 OFD.Query 只對了一半。** 本片 35 支逐支核對後,I 與 M 的真實差異如下。每一格都附錨點;「M 側」欄的通則取自 `architecture.md §6.2` 與 `ofd7.md §2`。

| # | 面向 | M 維護畫面 | I 查詢畫面(本片 35 支實測) | 差異性質 |
|---|---|---|---|---|
| 1 | **層數** | 六層 | **同樣六層,但有 6 支只有四層** | 部分退化 |
| 2 | 哪幾支不足六層 | — | `OFDI016` `OFDI912` `OFDI913` `OFDI914` `OFDI915` `OFDI916` **沒有 Model / View xsd**,只有 UI / Pxy / Ctl / PO(§2.4) | 匯出型專有 |
| 3 | **UI 基底** | `xMaintainForm` | **`xOneStepProcessForm`,35 支無一例外** | 全數不同 |
| 4 | UI 頁籤 | 查詢頁 + 維護頁兩個 TabPage | 一頁式,只有「查詢」一個動作按鈕 | 全數不同 |
| 5 | **PO 基底** | `BaseEVADaoPO`(單筆)或 `BaseMultiRowEVADaoPO`(多筆) | **三派並存**:`BaseEVADaoPO` 12 支 · **`BasicEVAPO` 3 支(這 3 支開畫面就 NRE,§5.9)** · **無基底** 20 支(§2.5) | **與 `architecture.md §6.3` 不同** |
| 6 | PO 基底的三派各是誰 | — | `BaseEVADaoPO`:`OFDI022` `OFDI311` `OFDI701` `OFDI702` `OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721` `OFDI751` `OFDI752` `OFDI753`(12 支);`BasicEVAPO`:`OFDI058B` `OFDI375` `OFDI719`;其餘 20 支只實作自己的介面 | 三派 |
| 7 | **PO 介面** | `I<代號>_PO : IEvaDataAccess` | 只有 8 支寫 `: IEvaDataAccess`(`OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721` `OFDI751` `OFDI752` `OFDI753`),其餘光禿禿 | 部分保留 |
| 8 | **`MasterTable` 宣告** | 建構子必宣告,是全庫「實體表」清單的來源 | **35 支全部沒有**(連被註解掉的都沒有,與 `CASI001_PO.cs:41` 那種「註解殘留」不同) | **完全消失** |
| 9 | `DetailTable` 宣告 | 有 | **35 支全部沒有** | 完全消失 |
| 10 | **四眼 13 欄** | 每張表都有 `ENTRYID` / `VERIFYID` / `APPROVEID` … 一整組,PO 掛 10 個事件 | **一個都沒有。** 35 支 PO 沒有任何 `BeforeAdd` / `AfterVerify` / `AfterApprove` 掛鉤 | 完全消失 |
| 11 | 四眼欄位會不會出現在結果集 | — | 會,但是**當一般欄位被 `SELECT` 出來給人看**(例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:80-81` 把 `TRP805A.CreateID` `TRP805A.CreateDate` 當顯示欄) | 語意改變 |
| 12 | **Model.xsd 的角色** | **實體表形狀**:根節點名 = 表名,欄位對齊 DB | **結果集形狀**:29 支的根節點叫 `OFDI0xx`(畫面代號),不是任何一張表(§2.2) | **根本差異** |
| 13 | Model.xsd 的例外 | — | 7 支的根節點用了真實表名:`OFDI019`(`CRSP001`~`CRSP006`)、`OFDI716`(`TRP805`)、`OFDI717`(`TRP806`)、`OFDI718`(`TRP801`)、`OFDI719`(`TRP804`)、`OFDI720` 與 `OFDI721`(都叫 `TRP810`) | 例外 7 支 |
| 14 | **View.xsd 的角色** | 與 Model 同構,`Ctl` 逐欄手搬 | 多半同構,**但有 2 支欄數對不上**:`OFDI060` 的 `OFDI060_SHORT_TIME` Model 9 欄 / View 11 欄;`OFDI702` Model 23 欄 / View 22 欄(附錄 E.9) | 有破口 |
| 15 | **`Ctl` 覆寫 `InitializeVDBTypes()`** | 有 | **35 支全部沒有** | 完全消失 |
| 16 | `Ctl` 覆寫 `InitializeDataAccessPool()` | 有 | 32 支有;`OFDI058B` `OFDI375` `OFDI719` 三支**連 `BaseController` 都沒繼承**(例 `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:13`) | 部分消失 |
| 17 | **寫入路徑** | `Add` / `Modify` / `Delete` + 四眼四段寫回 | **零。35 支 PO 內沒有任何 `ExecuteNonQuery` / `UpdateDataSet` / `INSERT` / `UPDATE` / `DELETE`**,全部只有 `LoadDataSet` | **完全消失** |
| 18 | 例外:有沒有偷寫 | — | 沒有。唯一接近寫入的是 `OFDI058B_PO.CheckPower()` 的 `ExecuteScalar`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:315`),那是 `SELECT COUNT(*)` | 無 |
| 19 | **查詢條件從哪來** | 從 Model 的資料列逐欄搬 | 從 `model.Utility.Parameters` 這個泛用 key-value 袋子撈,欄名與運算子都是字串(§5.2) | **根本差異** |
| 20 | **條件怎麼進 SQL** | 參數化 UPDATE / INSERT | **13 支直接字串串接、2 支走會跳脫單引號的 helper、20 支參數化或走 SP**(§5.2) | **本片最大風險** |
| 21 | 錯誤回報 | `Result` + `ImsError` 階層 | 一律 `model.Utility.Result.AddResultRow(bool, 筆數, 訊息)`,**沒資料時訊息多半是空字串** | 語意變弱 |
| 22 | 例外處理 | 走框架 | 兩派:`CommonExceptionBlocker.HandleBusinessException(ex)`(彈視窗)或 `AddResultRow(false, 0, ex.Message)`(把 Oracle 錯誤原文貼到畫面上),**有 5 支兩個都做**(附錄 E.6) | 不一致 |
| 23 | **分頁** | 不適用 | **35 支全部沒有分頁。** `OFDI701` 與 `OFDI702` 的 `SELECT` 開頭留了 `/*RowNum*/` 註解標記(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:75`),但**全庫沒有任何程式讀這個標記**——是死記號 | 完全沒有 |
| 24 | **匯出** | 無 | **7 支有**(`OFDI016` `OFDI019` `OFDI221A` `OFDI912`~`OFDI916`),三種互不相同的實作(§5.7) | I 專有 |
| 25 | **權限控制** | 由平台 ToDo 機制按角色派工 | **只有 1 支自己做**:`OFDI058B` 用 `OFD152` / `OFD153` 查「這個員工能看哪些基金」(§5.5)。其餘 34 支**任何能開畫面的人看得到全部資料** | I 幾乎沒有 |
| 26 | 交易 | `BeginTransaction` / `Commit` | 無,也不需要 | 不適用 |
| 27 | 連線管理 | 由基底管 | 三種寫法混用:基底的 `dbProduct` / 自建 `private Database m_db = new Database("TA", DbServerType.Oracle)` / 自己 `CreateConnection()` + `Open()` + `finally Close()`(§2.5) | 不一致 |
| 28 | **`[PODbType(DbServerType.Oracle)]` 標註** | 有 | 有 28 支;`OFDI058B` `OFDI375` `OFDI719` `OFDI022` `OFDI311` `OFDI701` `OFDI702`(繼承 `BaseEVADaoPO` 用 `dbProduct` 的那幾支)沒標 | 不一致 |
| 29 | 用到的 SP | M 幾乎不用 | **11 支走 SP,全部在版控外**(§3.3、附錄 B) | I 較依賴 SP |
| 30 | csproj 齊不齊 | `ofd123.md 附錄 D` 記過缺漏 | **35 支的 UI / Pxy / Ctl / PO 四層全部在 csproj 內,缺 0**;唯一異常是 `OFDI701` 的 Model 檔名多一個點(§2.6) | I 反而乾淨 |
| 31 | **`MasterTable` 消失後,主明細怎麼指定** | `xTableMapping` 宣告,框架據此組 SQL | PO 端改成 `LoadDataSet(cmd, model.DataEntity, model.DataEntity.<結果集>.TableName)`(例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:111`);Ctl 端改成逐表 `TransferVDBHelper.TransferTable`(**35 支裡 26 支用它**,另 3 支用 `BasicTableTransferSetter`) | 換成強型別 |
| 32 | 換掉之後好不好 | — | **變好了**:`model.DataEntity.TRP805_D` 是 typed DataSet 的屬性,打錯是**編譯期紅字**;`xTableMapping("OFD191","…")` 那個字串打錯要到執行期才炸 | I 這點勝過 M |
| 33 | **四眼欄位在 xsd 的實證** | 每張 Model 表都有 `DATAID` / `STATUS` / `DATAFLAG` + 四眼 10 欄 | 掃 `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` 的三張表,`DATAID` / `STATUS` / `DATAFLAG` / `ENTRYID` / `VERIFYID` / `APPROVEID` / `REJECTID` **合計 0 個** | 完全消失(已實證) |
| 34 | `atlas_scan --screen` 對 I 的行為 | 「主檔 / 明細」印得出表名 | **一律印 `主檔 —` / `明細 —`。那是「沒有宣告」不是「缺層」**,不要當缺陷寫 | 工具行為,非缺陷 |

> **關於第 5 列的 `BasicEVAPO` 三支**:這不只是「基底不一樣」而已。 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` 把 `dbTA` 宣告成 `protected Database dbTA = null;`, 而建構子裡唯一會給它值的兩行**整段被註解掉**(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:169-170`)。全檔 2200 行、`dbTA` 出現 182 次,**沒有任何一處指派**。三支子類別 `OFDI058B_PO` / `OFDI375_PO` / `OFDI719_PO` 的建構子都是空的,也沒補上。結果是**按下查詢的第一行就 `NullReferenceException`**——詳見 §5.9。

**一句話總結**: **I 畫面保留了 M 畫面的「檔案骨架」,丟掉了「框架契約」。** 六個檔都在、命名鐵律照舊,但 `MasterTable` / `InitializeVDBTypes` / 四眼 / 寫入路徑這四樣**框架真正在用的東西全部不見了**, 剩下的是一支自己組 SQL、自己 `LoadDataSet`、自己回 `Result` 的手工 DAO。所以**讀 I 畫面不能用讀 M 畫面的方法**: 不要去找 `xTableMapping`(沒有)、不要去找四眼掛鉤(沒有)、不要假設 xsd 是表(不是), **唯一可靠的資訊來源是 PO 裡那段 SQL 字串本身**。

### 0.3 這 35 支涵蓋哪些業務線(推測)

依「查的是哪張表」分群,得到六條線。業務名稱由畫面上的中文控件標題與 `SELECT` 欄位反推,**標「推測」**:

| 線 | 畫面 | 在查什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 部位與庫存** | `OFDI075A` `OFDI076A` `OFDI077A` `OFDI078A` `OFDI901` | 受益人在某檔基金的持有單位數(即時 / 日結)、某檔基金的總單位數(即時 / 日結)、以及折算台幣後的庫存 | 表 `OFD304A` / `OFD305A`(帶 `BF_NO`)對 `OFD310A` / `OFD311A`(不帶 `BF_NO`);`OFD305A` / `OFD311A` 多一個 `BAL_DATE` 欄 |
| **B 交易與帳務** | `OFDI022` `OFDI058B` `OFDI060` `OFDI311` `OFDI283` `OFDI481` | 申購 / 贖回明細、大額交易、短線交易次數、受益權轉讓、收益分配、清算配息 | 表 `OFD221A`(申購)`OFD251A`(贖回)`LOG221A`(轉讓軌跡)`OFD281A`/`OFD283A`(分配)`OFD494A`/`OFD496A`/`OFD497A`(清算) |
| **C 集保檔比對** | `OFDI716` `OFDI717` `OFDI718` `OFDI719` `OFDI720` `OFDI721` | 集保(TDCC)上傳檔與回饋檔的內容與結餘比對 | 畫面標題全是「集保上傳日期」「收檔日期」「結餘比對日期」;表全是 `TRP8xx`,且 SQL 用 `FUND_ID_TDCC` 對回本公司基金代碼 |
| **D 集保下單** | `OFDI751` `OFDI752` `OFDI753` | 透過集保通路進來的申購 / 買回 / 轉申購下單與其回報 | 表 `ORDR01` / `ORDR02`;`CP_TXTYPE` 的 `CASE` 直接寫死 `'P.申購'` `'R.買回'` `'S.轉申購'`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:73`) |
| **E 匯出型** | `OFDI016` `OFDI912` `OFDI913` `OFDI914` `OFDI915` `OFDI916` | FATCA 檢核、交易申請書、定額契約、RSS 契約、基金基本資料的整批匯出 | 六支的 PO 唯一方法都叫 `GetExcelData(...)` 回 `DataSet`,UI 端接 `SaveFileDialog` |
| **F 其他單線** | `OFDI010` `OFDI019` `OFDI071` `OFDI072A` `OFDI123A` `OFDI221A` `OFDI375` `OFDI701` `OFDI702` | 刪除書號軌跡、CRS 申報檔、基金控管紀錄、基金交易控管、KYC 資料、申購明細轉檔、兩支核印查詢 | 各自只碰一張主表,彼此無交集 |

**六條線之間沒有任何程式呼叫。** I 畫面不互叫、不叫批次、不被批次叫; 唯一的關聯是**共同讀同一批上游表**(`OFD081A` / `OFD081V` / `BMS001A` / `CTL014`)。讀 OFDI1 的人如果預期整片是一條流程,會在 §5.2 之後完全對不上——先知道這件事比較省時間。

### 0.4 不管什麼

| 不在 OFDI1 | 在哪 | 依據 |
|---|---|---|
| 這些表的**建立與維護** | 各自的 M 畫面與批次,散在 `ATLAS.OFD` / `ATLAS.OFDB` / `ATLAS.BBS` | 本片 35 支 PO 內**零寫入語句**(§0.2 第 17 列) |
| `TRP8xx` 集保檔的**維護與後處理** | **在 `ATLAS.OFDB` 的同號批次**:`OFDB717`(`TRP801A` `TRP804`)、`OFDB718`(`TRP801A`)、`OFDB719` 與 `OFDB720`(`TRP810A`)、`OFDB721`(`TRP805A` `TRP805A_Detail` `TRP806A` `TRP806A_Detail`)、`OFDB722`(`TRP804`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs` 等;**查詢畫面的號碼與批次的號碼是對應的**(`OFDI716`↔`OFDB716`…) |
| `TRP8xx` / `ORDR0x` **第一次怎麼寫進來的** | **repo 內查不到 `INSERT`**,推測在版控外(收檔程式 / 外部載入) | 全 repo 掃 `INSERT INTO TRP8` 與 `INSERT INTO ORDR0` **0 筆**;OFDB 側只有 `UPDATE` 與 `DELETE` |
| `ORDR01` / `ORDR02` 的後處理 | `OFDB752`(`ORDR01`)、`OFDB757`(`ORDR01` `ORDR02`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB752_PO.cs`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB757_PO.cs` |
| 11 支 SP 的**內容** | 版控外(見附錄 B) | `grep -ril` 掃全 repo 的 `.sql`,11 支 SP 一支都找不到 |
| **權限模型本身** | 平台側 + `OFD152` / `OFD153` 這組「查詢群組 × 基金」設定表,維護入口不在本片 | `OFDI058B` 只是讀它(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:199-204`) |
| 報表輸出(`.rpt`) | `ATLAS.OFD.Report` | 本專案內無 `Report` 前綴的任何專案 |
| `OFDI058` `OFDI059` `OFDI070` `OFDI199` `OFDI562` `OFDI902` `OFDI907` `OFDI911` 八支 | 同專案,但不在本片名單 | 留給後續查詢片;本片只涵蓋指定的 35 支(附錄 D) |

### 0.5 使用角色

**35 支裡有 34 支沒有任何資料層級的權限控制。** 能從選單開得起畫面的人,看得到該表全部的資料。唯一的例外是 `OFDI058B`,它把「這個員工屬於哪個查詢群組、那個群組能看哪些基金」做進 SQL:

| 入口 | 做什麼 | 結果類型 | 錨點 |
|---|---|---|---|
| `OFDI058B` 開畫面時 | `CheckPower(UserID)` 數「有幾檔基金是這個人**看不到**的」 | 記錄不擋(回傳值,UI 端自行決定) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:293-327`、UI 端 `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI058B.cs:132` |
| `OFDI058B` 指定基金查詢時 | `CheckFundRight(model)` 查 `OFD152` × `OFD153`,沒權限回訊息「無該基金查詢權限」 | **阻擋** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:190-240`,訊息在 `:225` |
| `OFDI058B` 主查詢 | 主 SQL 本身就從 `COD009` → `OFD152` → `OFD153` 一路 `JOIN` 下來,**沒權限的基金根本不會出現在結果裡** | **過濾(無提示)** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:49-58` |

**這三道之中最重要的是第三道**:它不是提示、不是阻擋,是直接把資料濾掉。使用者看到「查無資料」時,分不清是「今天真的沒這筆交易」還是「這檔基金我沒權限」。更麻煩的是,**同一個庫存數字換一支畫面就看得到**—— `OFDI076A` 查的是同一批 `OFD305A`,但完全不查 `OFD152` / `OFD153`。也就是說 `OFDI058B` 那套權限**只保護這一支畫面,保護不了資料**(附錄 E.11)。

### 0.6 全域開關

本片沒有 `App.config` 層級的業務開關。決定行為的是三個畫面上的選項欄位:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `OFDI058B` 的 `TradeType` | `0` 全部 · `1` 申購 · `2` 贖回 | 決定主 SQL 是單段、還是兩段 `UNION ALL` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:67`、`:107`、`:109` |
| `OFDI058B` 的 `StyleType` | `0` 依基金基本資料 · `1` 自行設定 | 決定大額門檻取自 `OFD0811.LAKH_ALLOT_AMT` 還是使用者打的金額 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:96-103`、`:134-149` |
| `OFDI060` 的 `OPTION` | `0` 全部 · `1` 依基金群組 · `2` 依基金種類 | 決定 `WHERE` 子句;**`1` 與 `2` 兩條路的 SQL 寫壞了**(附錄 E.4) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:78-83` |

`OFDI123A` 另有一個 checkbox「排除無戶號 KYC 資料」(`EC_OP`),勾了就多一條 `BF_NO is not null` (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI123A_PO.cs:75-84`)。這是全片**唯一一個把「過濾」明講在畫面上的控件**——其餘的過濾使用者都不會知道。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDI1 全景:庫存、交易、集保連線、集保下單、匯出型與其他單線業務六群
圖中文字:① 部位與庫存查詢:五支同型,看的是不同時點的同一件事 / OFDI075A OFDI076A / OFD304A / OFD305A 個人庫存 / OFDI077A OFDI078A / OFD310A / OFD311A 基金總庫存 / OFDI901 / OFD305A + OFD300 折台幣 / OFD081A OFD081V BMS001A / 基金主檔 / 受益人主檔 / ② 交易與帳務查詢:申購、贖回、轉讓、清算、配息 / OFDI022 OFDI058B / OFD221A 申購 / OFD251A 贖回 / OFDI311 / LOG221A 受益權轉讓紀錄 / OFDI481 / OFD494A 496A 497A 清算配息 / OFDI283 / OFD281A OFD283A 收益分配 / ③ 集保 TDCC 連線:六支連號比對上傳與回饋檔 / OFDI716 OFDI717 / TRP805A / TRP806A 主+明細 / OFDI718 OFDI719 / TRP801A / TRP804 單表 / OFDI720 OFDI721 / TRP810A 同表兩形狀 / TRP8xx 誰在維護 / OFDB717 到 OFDB722 同號批次 / ④ 集保下單 ORDR:三支連號,其中一支走 SP / OFDI751 / ORDR01 下單明細 / OFDI752 / ORDR02 + ORDR01 回報 / OFDI753 / S_TA_OFDI753_GET 版控外 / OFD751 / 集保 ID 對照戶號 / ⑤ 匯出型查詢:PO 只叫 SP,沒有 Model/View xsd / OFDI912 OFDI913 OFDI914 / s_TA_OFDI91x_Get RefCursor / OFDI915 OFDI916 / s_TA_OFDI915/916_Get / OFDI016 / s_TA_OFDI016_Get FATCA / ExcelCreator / UI 端另存 .xlsx / ⑥ 其他單線業務:核印、法遵申報、歸屬、控管、刪除軌跡 / OFDI701 OFDI702 / OFD701 / OFD702 核印 / OFDI019 OFDI123A / CRSP00x CRS / OFD123A KYC / OFDI071 OFDI072A / OFD309A / OFD303A 控管 / OFDI010 OFDI016 OFDI060 OFDI375 / 刪除軌跡 / 歸屬 / 短線
```

*圖:圖 1 OFDI1 全景。橘框=本片的 35 支查詢畫面;灰虛框=被讀但不歸本片管的上游表;黑框=版控外的 SP;紫框=客戶端檔案落地。六群之間沒有任何程式呼叫——I 畫面彼此不互叫,只靠共同讀同一批表而相關。*

### 1.2 資料表關係

圖放在 §0 的開頭(`ofdi1.figs.py` 的 `h2:0-`),畫的是 **I 與 M 的層級差異**,不是表關係—— 因為本片沒有自己的表,表關係圖畫出來會是「35 支畫面各自指向別人的表」,資訊量低於 §8 那張。要看表怎麼串,直接看 §2.1 與 §8 的圖 5。

### 1.3 主要查詢畫面的過濾順序

圖放在 §5 的開頭(`h2:5-`),拿最具代表性的 `OFDI701` 走一遍。一句話總結:**本片的「卡控」幾乎全是「過濾(無提示)」,而且分布在三個層次—— `INNER JOIN` 濾掉一批、寫死的 `WHERE` 常數濾掉一批、Oracle 三值邏輯再濾掉一批, 三次都不會告訴使用者。**

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。唯一會產生檔案的是 7 支匯出畫面,但它們不是批次——是使用者按按鈕當場撈、當場存檔(§5.7)。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——35 支全是隨查隨用。唯一有時間感的是 C 線(集保檔比對):上游收檔程式把 `TRP8xx` 寫進來之後,人工開畫面比對。但**上游那支收檔程式在 repo 內查不到**(§0.4),泳道畫不完整,不畫。

## 2. 資料模型

### 2.1 本片查的是哪些表(沒有 `xTableMapping` 可抄)

M 畫面的實體表清單來自 PO 建構子的 `xTableMapping`。**I 畫面沒有這個宣告**(§0.2 第 8 列), 所以本節的表清單是**從每支 PO 的 SQL 字串裡的 `FROM` / `JOIN` 逐句抽出來的**, 不是從 `atlas_scan.py --screen` 的「主檔 / 明細」欄——那兩欄對本片 35 支全部回報「—」,那是正確的,不是漏掉。

35 支合計碰到 **44 張不同的表 / View**,依角色分三類:

| 類 | 表 | 誰查 | 說明 |
|---|---|---|---|
| **① 主查對象(本片真正在看的資料)** | `OFD221A` `OFD251A` `OFD281A` `OFD283A` `OFD303A` `OFD304A` `OFD305A` `OFD309A` `OFD310A` `OFD311A` `OFD375` `OFD494A` `OFD496A` `OFD497A` `OFD701` `OFD702` `OFD123A` `LOG221A` `SRNOCOMMENT` `CRSP001`~`CRSP006` `TRP801A` `TRP804` `TRP805A` `TRP805A_Detail` `TRP806A` `TRP806A_Detail` `TRP810A` `ORDR01` `ORDR02` | 各自 1~2 支 | 每張表基本上只被一支畫面查 |
| **② 說明欄來源(`LEFT JOIN` 只取名稱)** | `OFD081A` `OFD081V` `OFD081` `BMS001A` `BMS001` `COD009` `OFD002` `OFD020A` `OFD020V` `OFD711` `TA_AA_USER` `TA_SWPRODUCTSDETAIL` `OFD006A` `OFD038A` `OFD0811` | 幾乎每一支 | 改這幾張的欄名會同時打到十幾支畫面(§8) |
| **③ 代碼轉中文** | `CTL014` | 11 支 | 靠 `SourceType` 分群,一支畫面可能 `JOIN` 四次(見 §5.4) |
| **④ 權限來源** | `OFD152` `OFD153` | 只有 `OFDI058B` | 見 §0.5 |
| **⑤ 匯率** | `OFD300` | 只有 `OFDI901` | 見 §5.6 |
| **⑥ 集保 ID 對照** | `OFD751` | `OFDI751` `OFDI752` | 把集保的統編對回本公司戶號 |
| **⑦ 集保成交 / 委託旁支** | `OFD220A` `OFD233` | 只有 `OFDI058B` | 判斷款項是否已確認 |

**注意**:`OFD081V` 與 `OFD081A` / `OFD081` 三者混用得很亂。同一支 `OFDI719` 的一段 SQL 裡同時 `LEFT JOIN OFD081`(用 `FUND_ID_TDCC` 對) 與 `LEFT JOIN OFD081V`(用 `FUND_ID` 對),兩個 join 條件不同且結果欄互相覆蓋 (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:66-72`)。這是附錄 E.5。

### 2.2 結果集形狀:I 的 xsd 不是表

這是本片與前 21 篇最大的閱讀差異,**看錯會一路錯下去**。

M 的 `Model.xsd` 根節點是**實體表名**,欄位對齊 DB 欄位。 I 的 `Model.xsd` 根節點是**這支畫面的結果集名稱**,29 支直接拿畫面代號當名字:

| 根節點命名法 | 支數 | 例 |
|---|---|---|
| **= 畫面代號**(結果集) | 25 | `OFDI311`(17 欄)、`OFDI283`(39 欄)、`OFDI123A`(**134 欄**)、`OFDI901`(19 欄) |
| **= 畫面代號 + 後綴**(一支多表) | 4 | `OFDI022` + `OFDI022_Grid`、`OFDI481` + `OFDI481_Grid`、`OFDI060_FUND` / `OFDI060_SHORT_TIME` / `OFDI060_SHORT_TIME_2` / `OFDI060_SHORT_DETAIL` |
| **= 真實表名** | 6 | `OFDI019` 的 `CRSP001`~`CRSP006` + `CRSP001_TEMP`;`OFDI716`~`OFDI721` 的 `TRP805` `TRP806` `TRP801` `TRP804` `TRP810` |
| **沒有 xsd** | 6 | `OFDI016` `OFDI912`~`OFDI916`(§2.4) |

**三個坑**:

1. **`TRP805` 這個名字不是表。** `OFDI716Model.xsd` 裡有三張 DataTable:`TRP805`(14 欄)、`TRP805_Detail`(13 欄)、`TRP805_D`(18 欄), 但 SQL 查的是 `TRP805A` 與 `TRP805A_Detail`。 PO 實際把主查詢灌進 `TRP805_D`、明細灌進 `TRP805_Detail` (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:111` 與 `:160`), **`TRP805` 那張 14 欄的從頭到尾沒被用到**。

2. **`OFDI720` 與 `OFDI721` 的 Model 根節點都叫 `TRP810`,但欄數不同**(23 欄 vs 31 欄)。兩支查的是同一張 `TRP810A`,只是切面不同(§5.4)。名字撞號但在不同組件不同 namespace,編得起來,**讀的人很容易以為是同一個東西**。

3. **`OFDI019` 的 xsd 用真實表名,是全片唯一一支「結果集 = 實體表」的**。代價是 `CRSP002` 有 23 欄、`CRSP004` 有 12 欄,改 CRS 申報欄位時**這支 xsd 必須跟著改**,而其他 34 支不用。

### 2.3 欄位中文名

M 篇可以從 `Model.xsd` 的 `msdata:Caption` 抄欄位中文名。**本片抄不到**—— I 的 xsd 是產生器從 SQL 結果集反推出來的,`msdata:Caption` 多半空白。本片的欄位中文名只能從**畫面控件標題**反推(見 §3 清冊的「主要條件」欄), 所以清冊裡的中文全部標**推測**。

### 2.4 六支沒有 xsd 的匯出型畫面

`OFDI016` `OFDI912` `OFDI913` `OFDI914` `OFDI915` `OFDI916` 六支**只有四層**。它們的 PO 不吃 `ModelVDB`、不回 `ModelVDB`,而是:

```
public DataSet GetExcelData(string 參數1, string 參數2, ...)
```

直接吃字串參數、直接回 `System.Data.DataSet` (例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI913_PO.cs:53`)。 `DataSet` 內的 DataTable 名是**中文字串**,在 `LoadDataSet` 那一行寫死:

| 畫面 | SP | RefCursor 數 | DataTable 中文名 | 錨點 |
|---|---|---|---|---|
| `OFDI913` | `s_TA_OFDI913_Get` | 2 | 定額契約主檔 / 定額契約明細檔 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI913_PO.cs:71-74` |
| `OFDI915` | `s_TA_OFDI915_Get` | **9** | 基金基本資料檔(共用 / 境內 / 境內會計 / 其他)、基金申購入帳帳號明細資料、基金經理費率設定、基金可交易幣別、基金保管銀行資料、基金保管銀行聯絡資料 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI915_PO.cs:64-75` |
| `OFDI914` | `s_TA_OFDI914_Get` | 2 | 同 `OFDI913` 的結構 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI914_PO.cs:53` |
| `OFDI912` | `s_TA_OFDI912_1_Get` + `s_TA_OFDI912_2_Get` | — | 兩支 SP 依交易類別二選一 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI912_PO.cs:54` |
| `OFDI916` | `s_TA_OFDI916_Get` | — | RSS 契約相關 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI916_PO.cs:53` |
| `OFDI016` | `s_TA_OFDI016_Get` | — | FATCA 檢核 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI016_PO.cs:52` |

**這六支的「結果集形狀」完全定義在版控外的 SP 裡。** SP 改欄位,C# 這邊不用重編也不會報錯,直接反映到 Excel—— **這是本片唯一一組「改 DB 不用改 code」的畫面,也是唯一一組「改 DB 沒人攔得住」的畫面**(附錄 E.12)。

### 2.5 PO 的三派基底與三種連線寫法

| 派 | 基底 | 連線 | 特徵 | 畫面 |
|---|---|---|---|---|
| **甲 框架派** | `BaseEVADaoPO` | 用基底的 `dbProduct`,不自己開連線 | 介面常寫 `: IEvaDataAccess`;有 `[PODbType]` 的只有部分 | `OFDI022` `OFDI311` `OFDI701` `OFDI702` `OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721` `OFDI751` `OFDI752` `OFDI753` |
| **乙 舊框架派(死畫面)** | `BasicEVAPO` | **基底的 `dbTA` 恆為 `null`**,三支卻都 `dbTA.CreateConnection()` | `Ctl` 也不繼承 `BaseController`;三支同時是 T-SQL 殘留重災區 | `OFDI058B` `OFDI375` `OFDI719` |
| **丙 裸 DAO 派** | 無 | `private Database m_db = new Database("TA", DbServerType.Oracle)` 或 `dbTA` | 20 支,最多;有 `[PODbType(DbServerType.Oracle)]` | 其餘 20 支 |

甲派的 `GetQuery<T>(T model, params object[] args)` 用泛型收發; 丙派多半叫 `GetQueryData<T>(...)`;乙派直接吃具名的 `OFDI0xxModelVDB`。 **三種簽名在同一個資料夾裡並存,沒有任何一致性檢查。**

乙派那個「自己開連線」不只是多餘,**它根本執行不到第二行**:

| 層 | 事實 | 錨點 |
|---|---|---|
| 基底 | `protected Database dbTA = null;` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` |
| 基底建構子 | 唯一會給 `dbTA` 值的兩行**整段被註解** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-173`,註解在 `:169-170` |
| 基底全檔 | 2200 行、`dbTA` 出現 182 次,**零指派** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs` |
| 子類 `OFDI058B_PO` | 建構子空的,`GetQuery` 第一行就 `dbTA.CreateConnection()` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:17-19`、`:35` |
| 子類 `OFDI375_PO` | 同上 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:23-26`、`:46` |
| 子類 `OFDI719_PO` | 同上 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:14-16`、`:30` |

而且**那一行全部在 `try` 外面**(`OFDI058B_PO.cs:35` 對 `:36` 的 `try`、`OFDI375_PO.cs:46` 對 `:55`、`OFDI719_PO.cs:30` 對 `:36`), 所以連 `catch` 都接不到,例外直接往 FormProxy 丟。詳見 §5.9 與附錄 E.1。

甲派沒有這個問題:`BaseEVADaoPO` 用的是基底自己管的 `dbProduct`; 丙派每支自己 `new Database("TA", DbServerType.Oracle)`,也不會是 null。 **只有乙派這三支會死。**

### 2.6 `OFDI701Model..xsd` — 檔名多一個點

`OFDI701` 的 Model 檔實際叫 **`OFDI701Model..xsd`**(兩個點), `.xsc` / `.xss` / `.Designer.cs` 全部跟著多一個點,csproj 也照著多一個點引用:

| csproj 行 | 內容 |
|---|---|
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/QueryDataEntity.OFD.csproj:222` | `<Compile Include="OFDI701Model..Designer.cs">` |
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/QueryDataEntity.OFD.csproj:558` | `<None Include="OFDI701Model..xsd">` |

**編得起來、跑得起來**(檔名只是字串),但:

- 任何用 `<代號>Model.xsd` 規則找檔的工具(含 `atlas_scan.py`)都會把 `OFDI701` 判成「缺 DataEntity 層」;

- `OFDI702` 是它的孿生畫面,檔名正常。**只有 701 錯**,典型的「成對畫面只改一邊」。

這是缺陷,不是慣例。收在附錄 E.10。

## 3. 畫面清冊

```text
[圖] OFDI1 的分群:三組連號、A/B 後綴七支、其餘單線
圖中文字:連號群 A:OFDI716~OFDI721 六支 — 集保檔比對,同一業務 / OFDI716 / TRP805A 主+明細 參數化 / OFDI717 / TRP806A 主+明細 參數化 / OFDI718 / TRP801A 單表 參數化 / OFDI719 / BasicEVAPO 死畫面 + T-SQL / OFDI720 / TRP810A 23 欄 參數化 / OFDI721 / TRP810A 31 欄 參數化 / 連號群 B:OFDI751~OFDI753 三支 — 集保下單,兩支同源一支走 SP / OFDI751 / ORDR01 下單 / OFDI752 / ORDR02 + ORDR01 / OFDI753 / S_TA_OFDI753_GET 版控外 / 共同鍵 OFD751 / 集保 ID 對照戶號 / 連號群 C:OFDI901 + OFDI912~OFDI916 — 9xx 不是同一件事 / OFDI901 / 庫存折台幣 有 xsd 自組 SQL / OFDI912 / s_TA_OFDI912_1 與 _2_Get / OFDI913 OFDI914 / s_TA_OFDI913/914_Get / OFDI915 / s_TA_OFDI915_Get 9 個游標 / OFDI916 / s_TA_OFDI916_Get / A 後綴七支 + B 後綴一支:join 的是哪一種表 / OFDI072A 查 OFD303A / 非 A 版 OFD303 全庫也在用 / OFDI075A 查 OFD304A / 無 OFD075A 這張表 / OFDI076A 查 OFD305A / 無 OFD076A 這張表 / OFDI123A 查 OFD123A / 唯一表名與畫面同號 / OFDI077A 查 OFD310A / 無 OFD077A 這張表 / OFDI078A 查 OFD311A / 無 OFD078A 這張表 / OFDI221A 走 SP / S_TA_OFDI221A_GET 版控外 / OFDI058B 查 OFD221A 251A / B 是第二版 且為死畫面 / 其餘 15 支:一支一條業務線,沒有群 / OFDI010 OFDI016 OFDI019 OFDI022 / 刪除軌跡 / FATCA / CRS / 交易明細 / OFDI060 OFDI071 OFDI283 OFDI311 / 短線 / 控管 / 分配 / 轉讓 / OFDI375 OFDI481 OFDI701 OFDI702 / 歸屬(死畫面) / 清算 / 核印兩支
```

*圖:圖 3 分群。紫框=有風險或例外;黑框=SP 在版控外。三組連號只有 A 群(716~721)是同一業務的六個切面,B 群(751~753)是同一業務但實作分裂,C 群(9xx)根本不是同一件事——OFDI901 與 OFDI912~916 唯一的共同點是代號都以 9 開頭(§5.6)。*

### 3.1 維護 M

**本片無 M 畫面。** `ATLAS.OFD.Query` 是查詢專用方案,35 支代號第 4 碼全部是 `I`。

### 3.2 查詢 I — 35 支逐支清冊

欄位說明: **PO 基底** = `<代號>_PO.cs` 的 class 宣告(已剝 `//` 註解)。 **主要查的表** = 從 SQL 的 `FROM` / `JOIN` 反推,不是 `xTableMapping`(本片沒有)。 **條件參數化** = 參 / 串 / 混 / SP(全部丟給 SP)。 **結果集** = Model xsd 的 DataTable 名與欄數。 **匯出** = 有沒有產檔路徑。 **分頁** = 全片皆無,不另立欄。 **csproj** = UI / Pxy / Ctl / PO 四層是否都在專案檔內。

| 代號 | 中文名(推測) | PO 基底 | 主要查的表 | 條件參數化 | 結果集(表名/欄數) | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `OFDI010` | 刪除書號軌跡查詢 | 無基底 | `SRNOCOMMENT` `TA_AA_USER` | **參**(4 個 bind) | `OFDI010` / 6 | — | 四層齊 |
| `OFDI016` | FATCA 申報檢核資料匯出 | 無基底 | (SP) | **SP** | **無 xsd** | **Excel** | 四層齊 |
| `OFDI019` | CRS 共同申報準則申報檔查詢 | 無基底 | `CRSP001` (SP 取其餘) | **SP + 串**(靜態條件) | `CRSP001`/8 `CRSP002`/23 `CRSP003`/6 `CRSP004`/12 `CRSP005`/7 `CRSP006`/8 `CRSP001_TEMP`/2 | **Excel** | 四層齊 |
| `OFDI022` | 申購贖回交易明細查詢 | `BaseEVADaoPO` | `OFD221A` `OFD251A` `OFD081A` `OFD081V` `OFD038A` `OFD006A` `BMS001A` `CTL014` | **串**(26 處) | `OFDI022`/17 `OFDI022_Grid`/3 | — | 四層齊 |
| `OFDI058B` | 大額交易查詢(第二版) | **`BasicEVAPO`(死)** | `OFD221A` `OFD251A` `OFD0811` `OFD220A` `OFD233` `OFD152` `OFD153` `COD009` | **參**(但用 `@` + `SqlDbType`) | `OFDI058B` / 13 | — | 四層齊 |
| `OFDI060` | 短線交易次數查詢 | 無基底 | `OFD081V` `OFD038A` + (SP) | **混**(SP + 壞掉的 bind) | `OFDI060_FUND`/3 `OFDI060_SHORT_TIME`/9 `OFDI060_SHORT_TIME_2`/6 `OFDI060_SHORT_DETAIL`/15 | — | 四層齊 |
| `OFDI071` | 基金控管紀錄查詢 | 無基底 | `OFD309A` `OFD081A` `COD009` `TA_SWPRODUCTSDETAIL` | **串**(7 處) | `OFDI071` / 21 | — | 四層齊 |
| `OFDI072A` | 基金交易控管碼查詢 | 無基底 | `OFD303A` `OFD081A` | **串**(2 處) | `OFDI072A` / 10 | — | 四層齊 |
| `OFDI075A` | 受益人即時庫存查詢 | 無基底 | `OFD304A` `BMS001A` `OFD081A` | **串**(5 處) | `OFDI075A` / 15 | — | 四層齊 |
| `OFDI076A` | 受益人日結庫存查詢 | 無基底 | `OFD305A` `BMS001A` `OFD081A` | **串**(6 處) | `OFDI076A` / 16 | — | 四層齊 |
| `OFDI077A` | 基金即時總庫存查詢 | 無基底 | `OFD310A` `OFD081A` | **串**(1 處) | `OFDI077A` / 5 | — | 四層齊 |
| `OFDI078A` | 基金日結總庫存查詢 | 無基底 | `OFD311A` `OFD081A` | **串**(2 處) | `OFDI078A` / 6 | — | 四層齊 |
| `OFDI123A` | KYC 資料查詢 | 無基底 | `OFD123A` | **參**(走 4 參數版 helper) | `OFDI123A` / **134** | — | 四層齊 |
| `OFDI221A` | 申購明細轉出 | 無基底 | (SP) | **SP** | `OFDI221A` / 29 | **Excel** | 四層齊 |
| `OFDI283` | 收益分配發放查詢 | 無基底 | `OFD281A` `OFD283A` `OFD081A` `BMS001A` `OFD020V` | **參**(9 個 bind) | `OFDI283` / 39 | — | 四層齊 |
| `OFDI311` | 受益權轉讓查詢 | `BaseEVADaoPO` | `LOG221A` `OFD221A` `BMS001A` `OFD081V` | **串**(5 處) | `OFDI311` / 17 | — | 四層齊 |
| `OFDI375` | 受益人業務歸屬查詢 | **`BasicEVAPO`(死)** | `OFD375` `BMS001` `OFD002` `COD009` | **串**(3 處) | `OFDI375` / 10 | — | 四層齊 |
| `OFDI481` | 清算配息發放查詢 | 無基底 | `OFD494A` `OFD496A` `OFD497A` `OFD020V` `OFD081V` `BMS001A` | **串**(16 處,含 1 處無引號) | `OFDI481`/33 `OFDI481_Grid`/3 | — | 四層齊 |
| `OFDI701` | 扣款帳戶核印查詢 | `BaseEVADaoPO` | `OFD701` `OFD020V` `OFD711` `CTL014`×4 | **串**(9 處) | `OFDI701` / 20 | — | 四層齊(Model 檔名異常,§2.6) |
| `OFDI702` | 代理扣款機構核印查詢 | `BaseEVADaoPO` | `OFD702` `OFD020V` `OFD711` | **串**(9 處) | `OFDI702` / 23(View 22) | — | 四層齊 |
| `OFDI716` | 集保結餘上傳檔查詢 | `BaseEVADaoPO` | `TRP805A` `TRP805A_Detail` `OFD081V` `CTL014` | **參**(10 個 bind) | `TRP805`/14 `TRP805_Detail`/13 `TRP805_D`/18 | — | 四層齊 |
| `OFDI717` | 集保交易上傳檔查詢 | `BaseEVADaoPO` | `TRP806A` `TRP806A_Detail` `OFD081V` `CTL014` | **參**(11 個 bind) | `TRP806`/22 `TRP806_Detail`/22 `TRP806_D`/26 | — | 四層齊 |
| `OFDI718` | 集保回饋檔查詢 | `BaseEVADaoPO` | `TRP801A` `OFD081V` `CTL014` | **參**(5 個 bind) | `TRP801` / 21 | — | 四層齊 |
| `OFDI719` | 集保結餘回饋檔查詢 | **`BasicEVAPO`(死)** | `TRP804` `OFD081` `OFD081V` `CTL014` | **參**(但是 **T-SQL**,見 §5.9) | `TRP804` / 24 | — | 四層齊 |
| `OFDI720` | 集保收檔查詢(摘要) | `BaseEVADaoPO` | `TRP810A` `OFD081V` `CTL014` | **參**(3 個 bind) | `TRP810` / 23 | — | 四層齊 |
| `OFDI721` | 集保收檔結餘比對查詢 | `BaseEVADaoPO` | `TRP810A` `OFD081V` `CTL014` | **參**(2 個 bind) | `TRP810` / 31 | — | 四層齊 |
| `OFDI751` | 集保下單明細查詢 | `BaseEVADaoPO` | `ORDR01` `OFD751` `BMS001A` `OFD081V` `OFD020A` | **串**(走會跳脫的 helper) | `OFDI751` / 26 | — | 四層齊 |
| `OFDI752` | 集保下單回報查詢 | `BaseEVADaoPO` | `ORDR02` `ORDR01` `OFD751` `BMS001A` `OFD081V` | **串**(走會跳脫的 helper) | `OFDI752` / 17 | — | 四層齊 |
| `OFDI753` | 集保下單彙總查詢 | `BaseEVADaoPO` | (SP) | **SP** | `OFDI753` / 28 | — | 四層齊 |
| `OFDI901` | 受益人庫存(折台幣)查詢 | 無基底 | `OFD305A` `BMS001A` `OFD081A` `OFD300` | **串**(`string.Format` 直接內插) | `OFDI901` / 19 | — | 四層齊 |
| `OFDI912` | 交易申請書資料匯出 | 無基底 | (SP ×2) | **SP** | **無 xsd** | **Excel** | 四層齊 |
| `OFDI913` | 定額契約資料匯出 | 無基底 | (SP) | **SP** | **無 xsd** | **Excel** | 四層齊 |
| `OFDI914` | 定額契約異動匯出 | 無基底 | (SP) | **SP** | **無 xsd** | **Excel** | 四層齊 |
| `OFDI915` | 基金基本資料匯出 | 無基底 | (SP,9 個游標) | **SP** | **無 xsd** | **Excel** | 四層齊 |
| `OFDI916` | RSS 契約資料匯出 | 無基底 | (SP) | **SP** | **無 xsd** | **Excel** | 四層齊 |

**分佈統計**:

| 面向 | 分佈 |
|---|---|
| PO 基底 | 無基底 20 · `BaseEVADaoPO` 12 · **`BasicEVAPO` 3(全部是死畫面)** |
| 放大到整個 `QueryPO.OFD` 的 43 支 | 無基底 24 · `BaseEVADaoPO` 15 · `BasicEVAPO` 4(多一支 `OFDI059`,不在本片名單)· `BaseMultiRowEVADaoPO` 0 |
| 條件進 SQL 的方式 | 純參數化 9 · 走 SP 11 · **字串串接 13** · 走會跳脫的 helper 2 |
| 結果集形狀 | 畫面代號命名 29(含多表)· 真實表名 6 · 無 xsd 6(與前者有重疊,見 §2.2) |
| 匯出 | 7 支 |
| 分頁 | **0 支** |
| 權限控制 | **1 支** |
| 在 csproj | **35 支四層全在,缺 0** |

### 3.3 批次 B

**本片無 B 畫面。** 不過 11 支畫面透過 SP 間接吃到伺服端的重活,那些 SP 在版控外(附錄 B)。

### 3.4 報表 R

**本片無 R 畫面。** R 畫面依 `architecture.md §6.5` 的鐵律住在 `ATLAS.OFD.Report`,不在本專案。本片 7 支匯出畫面產的是 Excel,不是 Crystal Report。

## 4. 維護畫面(M)— 一支一節

**本片無 M 畫面。** 原因:`ATLAS.OFD.Query` 是 OFD 模組切出來的**查詢專用方案**, 六層資料夾全部冠 `Query` 前綴(`QueryUI.OFD` / `QueryPO.OFD` / `QueryDataEntity.OFD` …), 方案內 43 支畫面的代號第 4 碼**全部是 `I`**。 OFD 的維護畫面住在 `Dev/ATLAS.OFD`,已由 `ofd123.md` / `ofd4.md` / `ofd5.md` / `ofd6.md` / `ofd7.md` 五片涵蓋。

## 5. 查詢畫面(I)

```text
[圖] OFDI701 核印查詢的四個步驟與三個過濾點
圖中文字:步驟 1 UI 收條件:xOneStepProcessForm 把畫面欄位塞進 Utility.Parameters / 核印日期起迄 / SEAL_DATE_ST 與 _END / 扣款人 ID / SUB_ID_NO / 扣款行 / 核印方式 / SUB_BANK_CODE 與 SEAL_TYPE / 核印狀態 / SEAL_STATUS 0 與 9 被改寫 / 步驟 2 PO 組 SQL:骨架是常數,條件全部字串串接 / 骨架 SELECT 到 WHERE 1=1 / 四個 CTL014 別名 LEFT JOIN 做代碼轉中文 / 逐個 if 串條件 / 把欄名與值直接接成字串 / 步驟 3 三個會讓資料無聲消失或直接爆掉的點 / ① SUB_ID_NO 用 Like 時 / Row.Name 被串兩次 欄名變 SUB_ID_NOSUB_ID_NO / ② SEAL_STATUS 0/9 改寫 / 使用者選 0 時 SQL 另加 BATCH_ID IS NULL / ③ 值含單引號 / 會把 SQL 斷成兩半 / 步驟 4 執行與回報:三種結局,使用者只看得到兩種 / 有資料 / AddResultRow true j 空訊息 / 沒資料 / AddResultRow false 0 訊息是空字串 / SQL 炸了 / catch 只叫 HandleBusinessException Result 一列都沒加 / 結論:查不到時,畫面說的是同一句話 / 條件真的沒資料 / 顯示查無資料 / 條件被 Like 分支寫壞 / 顯示查無資料或跳例外視窗 / 狀態被 0/9 改寫濾掉 / 顯示查無資料且不知條件被改過
```

*圖:圖 4 OFDI701 查詢流程。紫框=過濾(無提示)或會炸的點。這支是全片字串串接最密集的一支,也是唯一被抓到欄名串兩次的一支(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:154`)。最下面一排是本片查詢畫面的通病:三種完全不同的原因,畫面只回同一句查無資料。*

本章是本片的主體。先講三件通則(§5.1~§5.3),再逐群展開(§5.4~§5.10)。

### 5.1 一支 I 畫面從按下查詢到畫面出資料,走過哪些地方

四步,沒有分支:

| 步 | 誰做 | 做什麼 | 錨點(以 `OFDI716` 為例) |
|---|---|---|---|
| 1 | UI(`xOneStepProcessForm`) | 把畫面上的條件控件寫進 `ProcessVDB.Util.Parameters`,每個條件是一列 `{Name, Value, Opeartor}` | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:21`(class 宣告) |
| 2 | FormProxy | 包 `try` / `catch`,轉呼 Ctl | `Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` |
| 3 | Ctl | `InitializeDataAccessPool()` 把 PO 丟進池,再把 ViewVDB ↔ ModelVDB 互搬 | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:15`、`:27` |
| 4 | PO | **組 SQL 字串 → `LoadDataSet` → 數筆數 → `AddResultRow`** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:64-95`(SQL)、`:111`(載入)、`:162-173`(回報) |

第 3 步的「互搬」有兩種寫法:

- **框架搬**:`BasicTableTransferSetter.TransferViewToModel(view, model)` 一行搞定(例 `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:50-57`);

- **手搬**:逐欄 `newrow.XXX = row.IsXXXNull() ? 預設值 : row.XXX`(同一支的 `:66-82`)。

`OFDI375_Ctl` 兩種都做——先手搬 10 個欄位(`:66-82`),最後再叫一次框架搬(`:84`)。 **手搬那段把 NULL 轉成預設值**(數字 0、字串空、日期 `1900/01/01`),這是本片一個容易踩的資料語意問題: 畫面上看到的 `1900/01/01` 可能是「真的有這個日期」,也可能是「這格是 NULL」,**分不出來**(附錄 E.8)。

### 5.2 查詢條件怎麼組 — 本片最重要的一節

35 支的條件全部從同一個袋子來:`model.Utility.Parameters`。它是一張 DataTable,每列三個欄位:`Name`(欄名字串)、`Value`(值字串)、`Opeartor`(運算子;**框架自己拼錯了**)。 PO 拿到之後有四種處理法,風險差距極大:

| 法 | 支數 | 長相 | 注入風險 | 代表 |
|---|---|---|---|---|
| **甲 真參數化** | 9 | `strSQL` 內寫 `:NAME`,再 `AddInParameter(cmd, "NAME", OracleDbType.Varchar2, 值)` | 無 | `OFDI010` `OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721` `OFDI283` `OFDI123A` `OFDI058B` |
| **乙 全丟 SP** | 11 | `GetStoredProcCommand("s_TA_OFDIxxx_Get")` + `AddInParameter` + `RefCursor` | 無(前提是 SP 本身沒有動態 SQL,**repo 內看不到 SP,無法驗證**) | `OFDI016` `OFDI019` `OFDI060`(部分)`OFDI221A` `OFDI753` `OFDI912`~`OFDI916` |
| **丙 走會跳脫的 helper** | 2 | `EVAStringHelper.AddParam(model, "表名", 欄1, 欄2, …)` — 3 參數版,**把值串進字串但會把 `'` 換成 `''`** | 低,**但 `IN` 分支完全沒跳脫** | `OFDI751` `OFDI752` |
| **丁 直接字串串接** | **13** | `strSQL += " And 表." + Row.Name + " = '" + Row.Value + "'"` | **高** | `OFDI022` `OFDI071` `OFDI072A` `OFDI075A` `OFDI076A` `OFDI077A` `OFDI078A` `OFDI311` `OFDI375` `OFDI481` `OFDI701` `OFDI702` `OFDI901` |

#### 5.2.1 甲派長什麼樣(正面教材)

`OFDI010` 是全片寫得最乾淨的一支。它把「條件可為空」也一併處理掉:

| 行 | 內容 |
|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI010_PO.cs:71` | `WHERE (:DEL_DATE_ST IS NULL OR COMMENTUPDATEDATE >= :DEL_DATE_ST)` |
| `:72` ~ `:74` | 另外三個條件同樣包成 `(:X IS NULL OR 欄 = :X)` |
| `:78-81` | 四個 `AddInParameter`,一律 `OracleDbType.Varchar2` |

**這是全片唯一一支「SQL 文字是常數,條件只靠 bind 變數開關」的畫面。** 好處不只是防注入——SQL 文字固定,Oracle 的 shared pool 只會有一份執行計畫; 丁派每換一次條件就是一句新 SQL,**每查一次就硬解析一次**。

#### 5.2.2 丁派長什麼樣(本片的主要風險)

樣板長這樣,`OFDI701` / `OFDI702` / `OFDI311` / `OFDI022` 幾乎逐字相同:

| 行 | 內容 |
|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI311_PO.cs:115` | `strSQL += " And LOG221A." + Row.Name + " = " + "'" + Row.Value + "'" + Environment.NewLine;` |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI311_PO.cs:119` | `strSQL += " And LOG221A." + Row.Name + " Like " + "'" + Row.Value + "%'" + Environment.NewLine;` |

**`Row.Value` 是使用者在畫面上打的字,沒有任何跳脫、沒有任何白名單。** `Row.Name` 也直接串進去當欄名——雖然 `Name` 是程式自己 `Find("BF_NO_OUT")` 找來的, 但 PO 是拿 `Row.Name` 而不是常數字串去組欄名,**改參數名就會改到 SQL 欄名**,這是設計上的脆弱點。

三個現實後果,依可能性排序:

| # | 後果 | 觸發條件 | 結果類型 |
|---|---|---|---|
| 1 | **查詢直接失敗** | 使用者輸入含 `'`(姓名 `O'Brien`、備註文字) | 阻擋(例外視窗)或 過濾(無提示),看該支的 `catch` 怎麼寫 |
| 2 | **查到不該查的資料 / 撈爆整張表** | 使用者輸入 `' OR '1'='1` | **記錄不擋**(SQL 合法,查得出來) |
| 3 | **執行計畫爆量** | 每次查詢的 SQL 文字都不同 | 記錄不擋(效能問題) |

第 2 點在本片有**一個最嚴重的實例**:`OFDI481` 的「期別」條件**連單引號都沒有**:

| 行 | 內容 |
|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI481_PO.cs:142` | `strSQL += " AND A." + Row.Name + " = " + Row.Value + Environment.NewLine;` |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI481_PO.cs:143` | 第二句 SQL 同樣寫法 |

其他丁派至少把值包在 `'…'` 裡,注入要先用一個 `'` 脫逃; 這一行是**裸值**,畫面上打 `1 OR 1=1` 就直接成立,連引號都不用。 `ISSUE_CODE`(期別)在畫面上是一個可輸入欄位(控件標題「期別」)。 **這是全片最該先修的一行。**

#### 5.2.3 丙派的 helper 到底安不安全

`OFDI751` / `OFDI752` 用的是 `EVAStringHelper.AddParam` 的**三參數多載** (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:346-378`)。逐段看:

| 行 | 做什麼 | 安全嗎 |
|---|---|---|
| `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:358-361` | 欄名去掉 `_ST` / `_END` 後綴 | — |
| `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:367-368` | `Like` 時 `strValue.Replace("'", "''") + "%"` | **有跳脫** |
| `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:371-372` | 其餘(含 `=`)`strValue.Replace("'", "''")` | **有跳脫** |
| `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:369-370` | **`IN` / `NotIN` 時 `"(" + strValue + ")"`** | **完全沒跳脫,也沒加引號** |

所以丙派的結論是:**一般條件安全,`IN` 條件是洞。** `OFDI751` 傳進去的八個欄位(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:104-106`) 若有任何一個的 `Opeartor` 被 UI 設成 `IN`,就從安全掉回丁派。 UI 端怎麼設 `Opeartor` 要逐支查,本片未逐支驗證——**標「假設」**: 依據是 helper 的分支條件與 `OFDI751` 傳入的欄位清單,實際 `Opeartor` 由 `xOneStepProcessForm` 的控件型別決定。

順帶一提,**四參數版**的 `AddParam`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:198-201`、實作在 `:228` 起) 才是真參數化版——它組出 `:NAME` 並同時 `AddInParameter` (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:281-286`), `IN` 也走 `f_FormatStringToTable(:NAME)`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:293-297`)。 **兩個多載同名、參數只差一個 `Database`,安全性天差地別。** `OFDI123A` 與 `OFDI901` 用的是四參數版,`OFDI751` / `OFDI752` 用的是三參數版。這是本片最值得寫進 code review checklist 的一條:**看到 `AddParam(model, ...)` 開頭沒有 `db, cmd` 的,就是字串版**。

### 5.3 會把資料濾掉而不提示的條件(五類卡控在查詢畫面的樣子)

查詢畫面的「卡控」和維護畫面完全不是同一件事。維護畫面的卡控會跳訊息; 查詢畫面的卡控**藏在 SQL 裡,使用者只看到「查無資料」**。本片的過濾分四種來源:

| 來源 | 機制 | 結果類型 | 支數 | 代表錨點 |
|---|---|---|---|---|
| **① `INNER JOIN`** | 對不到的資料整列消失 | **過濾(無提示)** | 至少 11 支 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:96-99`(連 3 個 `JOIN`) |
| **② 寫死的 `WHERE` 常數** | 程式決定只看某一類資料 | **過濾(無提示)** | 至少 6 支 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:95`(`AND TRP805A.SIN2 = '0'`) |
| **③ Oracle 三值邏輯** | `欄 <> '值'` 或 `欄 <> 0` 遇 NULL 是 UNKNOWN,整列被濾掉 | **過濾(無提示)** | 至少 3 支 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:112-120` |
| **④ 權限 JOIN** | 只有 `OFDI058B` | **過濾(無提示)** | 1 支 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:49-58` |

五類卡控在本片的實際分佈:

| 結果類型 | 本片有沒有 | 例 |
|---|---|---|
| **阻擋** | 有,2 處 | `OFDI058B` 的「無該基金查詢權限」(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:225`)、`OFDI221A` 匯出前要求填轉出路徑(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI221A.cs:186-190`) |
| **警示** | 有,1 處 | `OFDI058B` 的「該基金尚未成立」(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:271`) |
| **詢問** | **無** | 查詢畫面沒有需要使用者二次確認的動作 |
| **過濾(無提示)** | **大宗,遍佈 35 支** | 見上表四種來源 |
| **記錄不擋** | 有 | `OFDI058B` 的 `CheckPower` 只回數字不做事(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:293-327`) |

**這一節是本片對使用者最有價值的結論:** 在 OFDI1 的 35 支畫面裡,「查無資料」有五種完全不同的意思—— 真的沒有 / 被 `INNER JOIN` 濾掉 / 被寫死常數濾掉 / 被 NULL 吃掉 / 沒權限。 **程式一句都不會告訴你是哪一種。**

### 5.4 C 線:`OFDI716`~`OFDI721` 六支連號(集保檔比對)

#### 5.4.1 相似度:這六支是同一業務嗎

**是。** 逐項比對六支,共同點遠多於差異:

| 面向 | 716 | 717 | 718 | 719 | 720 | 721 |
|---|---|---|---|---|---|---|
| 主表 | `TRP805A` | `TRP806A` | `TRP801A` | `TRP804` | `TRP810A` | `TRP810A` |
| 有明細表 | ✓ `TRP805A_Detail` | ✓ `TRP806A_Detail` | — | — | — | — |
| PO 基底 | `BaseEVADaoPO` | `BaseEVADaoPO` | `BaseEVADaoPO` | **`BasicEVAPO`** | `BaseEVADaoPO` | `BaseEVADaoPO` |
| 介面繼承 `IEvaDataAccess` | ✓ | ✓ | ✓ | **無介面** | ✓ | ✓ |
| xsd 根節點用真實表名 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `JOIN OFD081V` 對回本公司基金 | ✓ | ✓ | ✓ | ✓(還多 join 一次 `OFD081`) | ✓ | ✓ |
| `LEFT JOIN CTL014 SourceType='000'` 轉「刪除註記」 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 條件參數化 | ✓ `:bind` | ✓ | ✓ | **✓ 但用 `@bind` + `SqlDbType`** | ✓ | ✓ |
| SQL 方言 | Oracle | Oracle | Oracle | **T-SQL** | Oracle | Oracle |
| 主要條件 | 集保上傳日 + 結餘日 + 基金 | 同 + 戶號/ID | 集保上傳日 + 結餘日 | 集保上傳日 | 收檔日 | 收檔日 + 結餘比對日 |

**相似度評分(同一業務的程度):9/10。** 六支共用同一套表前綴(`TRP8xx`)、同一組上游(`OFD081V` + `CTL014`)、同一種欄位命名 (`SIN1`~`SIN9` / `STF673S1`~`STF673S15` 這種「集保欄位序號」式命名)、同一種畫面條件(收檔日 / 上傳日 / 結餘日)。 **這是本片三組連號裡唯一一組貨真價實的「同一業務六個切面」。**

`OFDI720` 與 `OFDI721` 查同一張 `TRP810A`,差別只在切面寬窄(23 欄 vs 31 欄)與多一個「結餘比對日期」條件—— **它們是成對畫面,改一邊要記得改另一邊**(本片沒發現實際的不同步,但風險在)。

#### 5.4.2 挑最完整的一支寫:`OFDI716`

`OFDI716` 是六支裡結構最完整的(主 + 明細 + 三張結果集),拿它走一遍。

**SQL 骨架**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:64-95`):

| 段 | 內容 |
|---|---|
| `SELECT` | `TRP805A` 的 `BATCH_ID` / `BATCH_SRNO` / `TRANS_DATE` / `SIN1`~`SIN9` + `OFD081V` 的基金代碼與簡稱 + `CTL014` 的刪除註記中文 |
| 數值換算 | `(CAST(NVL(TRP805A.SIN6,0) AS NUMBER) * 1.000000 / 100)`——**集保檔的數值是「乘 100 的整數」,除回來才是真值**(`:74-76`,三個欄位都這樣) |
| `FROM` | `TRP805A` |
| `LEFT JOIN OFD081V` | `ON OFD081V.FUND_ID_TDCC = TRIM(TRP805A.SIN4)`——用**集保的基金代碼**對回本公司基金 |
| `LEFT JOIN CTL014` | `ON SourceType='000' AND CTL014.TextValue = TRP805A.DEL_YN` |
| `WHERE` | 四個日期 bind + 一個基金清單 + **`AND TRP805A.SIN2 = '0'`** |

**五個值得記的點**:

1. **`AND TRP805A.SIN2 = '0'` 是寫死的常數**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:95`)。畫面上沒有這個條件、使用者不知道它存在。`SIN2` 不是 `'0'` 的資料**永遠查不到**。結果類型:**過濾(無提示)**。同一個常數在明細 SQL 也再寫一次(`:142`)。

2. **基金條件是 `AND (OFD081V.FUND_ID IN (SELECT * FROM TABLE(F_FormatStringToTable(:FUND_ID))))`**(`:92`)。 `OFD081V` 是 `LEFT JOIN` 進來的,但**一旦 `WHERE` 裡對 `OFD081V.FUND_ID` 下條件,`LEFT JOIN` 就退化成 `INNER JOIN`** ——集保檔裡對不到本公司基金的那些列,**在有指定基金時全部消失**,在沒指定基金時也一樣消失(`IN` 對 NULL 不成立)。結果類型:**過濾(無提示)**。這是本片最典型的一個「LEFT JOIN 被 WHERE 打回原形」案例。

3. **明細 SQL 用 `JOIN TRP805A`(inner)**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:129-130`)。明細有、主檔沒有的列(集保檔破損、批號對不上)**不會出現,也不會有任何警告**。

4. **筆數只數主檔**:`i = model.DataEntity.TRP805_D.Rows.Count`(`:162`)。主檔 0 筆但明細有資料時,畫面會說「查無資料」而**明細其實已經載進去了**。

5. **`catch` 把 Oracle 原文貼到畫面**:`AddResultRow(false, 0, ex.Message)`(`:175-179`)。好處是出事看得到;壞處是**使用者看得到表名、欄名與 SQL 片段**。

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 組 SQL | `SIN2 = '0'` 寫死 | 永遠成立 | 過濾(無提示) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:95`、`:142` |
| 組 SQL | `OFD081V.FUND_ID IN (...)` | 基金對不到時 | 過濾(無提示) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:92`、`:139` |
| 組 SQL | 明細 `JOIN TRP805A` | 主檔缺列時 | 過濾(無提示) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:129-130` |
| 回報 | 只數主檔筆數 | 主 0 明細 >0 時 | 過濾(無提示) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:162-173` |
| 例外 | `catch (Exception)` | SQL 失敗時 | 記錄不擋(訊息外露) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:175-179` |

### 5.5 B 線深寫:`OFDI058B`(唯一有權限控制、也是最危險的一支)

`OFDI058B` 是全片最複雜的一支 PO(332 行、4 個公開方法),也是**唯一自己做資料權限**的一支。但它同時是**三支死畫面之一**: `GetQuery` 的第一行 `DbConnection cn = dbTA.CreateConnection();`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:35`) 對著一個恆為 `null` 的 `dbTA`,而且那行在 `try`(`:36`)外面。 **以下讀到的所有商業邏輯,現況都執行不到**——先知道這件事再讀,比較不會白讀(§5.9、附錄 E.1)。

**四個方法**:

| 方法 | 做什麼 | 錨點 |
|---|---|---|
| `GetQuery` | 主查詢:大額申購 / 贖回明細 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:33-184` |
| `CheckFundRight` | 查使用者對指定基金有沒有查詢權 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:190-240` |
| `GetFund_Setup_Date` | 查基金是否尚未成立(`FUND_SETUP_DATE = '1900/1/1'`) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:246-291` |
| `CheckPower` | 數「有幾檔基金這個人看不到」 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:293-327` |

**主查詢的結構**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:42-156`):

1. 先把「這個人有權限、且已成立」的基金撈進暫存表 `#T081`(`:42-60`);

2. 依 `TradeType` 決定要不要組申購段(`:67-105`)、要不要 `UNION ALL`(`:107`)、要不要組贖回段(`:109-150`);

3. 依 `StyleType` 決定大額門檻取自基金設定(`#T081.LAKH_ALLOT_AMT`)還是使用者輸入(`@AllotAmt`)(`:96-103`、`:134-149`);

4. 外層再 `JOIN BMS001` 補受益人姓名,最後 `DROP TABLE #T081`(`:152-156`)。

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 開畫面 | `CheckPower(UserID)` | 回傳看不到的基金數 | 記錄不擋 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:293-327` |
| 查詢前 | `CheckFundRight` | 沒權限 → 「無該基金查詢權限」 | **阻擋** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:217-226` |
| 查詢前 | `GetFund_Setup_Date` | 基金未成立 → 「該基金尚未成立」 | **警示** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:268-272` |
| 組 SQL | `#T081` 的四道 `JOIN` | 沒權限的基金不進暫存表 | **過濾(無提示)** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:49-58` |
| 組 SQL | `AND OFD081V.FUND_SETUP_DATE <> '1900/01/01'` | 未成立基金一律不出現 | **過濾(無提示)**,且 **`<>` 遇 NULL 是 UNKNOWN**(附錄 E.3) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:60` |
| 組 SQL | `AND OFD221A.ALLOT_PROC_CODE <> 'D'` | 排除作廢 | 過濾(無提示),同樣的 `<>` NULL 問題 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:93` |
| 組 SQL | `AND OFD221A.ALLOT_CODE IN('1','2')` | 只看兩種申購別 | 過濾(無提示) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:95` |
| 回報 | `if (Count > 0) AddResultRow(true, 0, "")` | **沒有 `else`** | 0 筆時 `Result` 是空的 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:167-170` |

最後一條要特別講:`:168` 先 `Result.Clear()`,`:169-170` 只在有資料時 `AddResultRow`。 **0 筆時 `Result` 一列都沒有**,呼叫端若照其他 34 支的慣例讀 `Result[0]` 就會 index out of range。其他 34 支都有 `else` 分支。**只有這一支沒有。**

### 5.6 C 群:`9xx` 代號到底是不是管理者專用

**結論:不是。本片的 `9xx` 沒有任何權限控制,而且六支不是同一件事。**

`ofdb5.md` 那片的 `OTAB901` 是系統用途,本片沒有這個規律。逐支查:

| 畫面 | 有 xsd | 走 SP | 有匯出 | 有權限檢查 | 在查什麼(推測) | 像不像管理用途 |
|---|---|---|---|---|---|---|
| `OFDI901` | ✓(19 欄) | ✗(自組 SQL) | ✗ | ✗ | 受益人庫存 + 匯率折台幣 | **不像**,是業務查詢 |
| `OFDI912` | ✗ | ✓ ×2 | ✓ | ✗ | 交易申請書 | 不像,是作業匯出 |
| `OFDI913` | ✗ | ✓ | ✓ | ✗ | 定額契約主 + 明細 | 不像 |
| `OFDI914` | ✗ | ✓ | ✓ | ✗ | 定額契約(另一切面) | 不像 |
| `OFDI915` | ✗ | ✓(**9 個游標**) | ✓ | ✗ | 基金基本資料全套 9 張表 | **勉強像**——一次撈基金主檔、費率、幣別、保管銀行,是建檔稽核用的切面 |
| `OFDI916` | ✗ | ✓ | ✓ | ✗ | RSS 契約 | 不像 |

**`9xx` 在本片的實際含義是「後來加的」,不是「管理用」。** 六支裡有五支是同一批 Excel 匯出畫面(§5.7),另一支 `OFDI901` 是庫存查詢的加強版—— 它與 `OFDI076A` 查同一張 `OFD305A`、`SELECT` 欄位重疊 14 個,只多了匯率三欄 (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:67-69` 的 `CRNCY_CD` / `CDATE` / `EX_RATE`)。 **合理推測是「`OFDI076A` 要加匯率,但不想動舊畫面,所以開一支 901」**——依據是兩支 SQL 的 `SELECT` 清單高度重合。標「假設」。

**`OFDI901` 三個要注意的地方**:

1. **`string.Format` 直接把使用者輸入內插進 SQL**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:64-121`)。 `{0}` 是結餘日期、`{1}` 是**基金代碼清單**,`{1}` 被放進 `FUND_ID IN ({1})` 與 `AND FUND_ID IN ({1})` 兩處(`:87`、`:102`), **兩處都沒有引號、沒有跳脫**。傳進去的值來自 `prms.FindByName("FUND_ID").Value`(`:121`)。雖然畫面上的基金是用挑選器選的(`挑選基金資料`),**但 PO 這一層完全沒有防線**。

2. **`WHERE` 那九個 `<> 0` 是 Oracle 三值邏輯陷阱**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:112-120`): `BAL_UNIT <> 0 OR BAL_RSP_UNIT <> 0 OR …` 共九個 `OR`。 **若某一列的九個欄位全是 NULL**,每個比較都是 UNKNOWN,`OR` 起來還是 UNKNOWN,整列被濾掉。意圖是「排除全零的庫存」,實際效果是「排除全零**與全 NULL**的庫存」—— 如果上游用 NULL 表示「尚未結帳」,這支畫面會讓那些部位**完全消失**。結果類型:**過濾(無提示)**。這是九個模組中過的同一型缺陷,本片也中。

3. **匯率子查詢用 `UNION ALL SELECT 'TWD','{0}',1 FROM DUAL`**(`:110`)補台幣的 1:1 匯率。 `'TWD'` 是寫死常數〔客戶特定〕。

### 5.7 匯出:七支,三種實作,沒有一種相同

| 畫面 | 誰產檔 | 用什麼 | 落地方式 | 錨點 |
|---|---|---|---|---|
| `OFDI912`~`OFDI916`、`OFDI016` | UI | `ExcelCreator.CreateExcelDocument(DataSet, 檔名)` | `SaveFileDialog`,副檔名 `.xlsx` | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI912.cs:132-144`、`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI016.cs:197-209` |
| `OFDI019` | UI | **Infragistics** `ultraGridExcelExporter` + `Infragistics.Documents.Excel.Workbook` | `FolderBrowserDialog` 選資料夾,檔名由程式組(`"CRS-" + 年度 + "-" + 訊息編號 + ".xls"`),副檔名 **`.xls`** | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI019.cs:369-399`、`:496` |
| `OFDI221A` | UI | **`Microsoft.Office.Interop.Excel`** + 自家的 `UIExcelHelper` | 先驗轉出路徑,再 `GenExcelFile` | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI221A.cs:322`、`:334-340`、`:405` |

**三種實作並存的後果**:

- **`OFDI019` 產的是 `.xls`(BIFF8),其餘產 `.xlsx`。** BIFF8 有 65536 列上限,CRS 申報資料筆數一多就會截斷或失敗 (`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI019.cs:399` 的 `BIFF8Writer.WriteWorkbookToFile`)。

- **`OFDI221A` 走 Office Interop**,代表**執行這支的那台用戶端必須裝 Excel**,而且產檔時會起一個 Excel 行程。其餘六支不需要。這是部署差異,不是程式差異——換台機器可能只有這一支不能用。

- **`OFDI221A` 是唯一一支「匯出前有阻擋檢核」的**:沒填轉出路徑就擋下來 (`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI221A.cs:186-190`,訊息「轉 Excel 檔的功能 需要輸入"轉出路徑"。」)。它把「查詢用」與「匯出用」的驗證做成同一個方法的兩種模式:`DoValidate(bool isExcel = false)`(`:171`), 查詢時傳 `false`(`:84`)、匯出時傳 `true`(`:322`)。**這是本片唯一一支把兩條路徑的驗證分開的畫面。**

### 5.8 D 線:`OFDI751`~`OFDI753` 三支連號(集保下單)

#### 5.8.1 相似度

| 面向 | 751 | 752 | 753 |
|---|---|---|---|
| 主表 | `ORDR01` | `ORDR02` + `ORDR01` | (SP `S_TA_OFDI753_GET`) |
| 共同上游 | `OFD751` `BMS001A` `OFD081V` | `OFD751` `BMS001A` `OFD081V` | 不明(SP 在版控外) |
| PO 基底 | `BaseEVADaoPO` | `BaseEVADaoPO` | `BaseEVADaoPO` |
| 條件 | 三參數 `AddParam`(字串版) | 三參數 `AddParam`(字串版) | **14 個 `AddInParameter`** |
| 結果集欄數 | 26 | 17 | 28 |
| 畫面條件 | 下單日 / 交易日 / 戶號 / ID / 基金 / 轉入基金 | 下單日 / 戶號 / ID / 基金 / 集保統編 | 下單日 / 交易日 / 戶號 / ID / 下單編號 / 交易型態 / 集保銷售機構 |

**相似度評分:7/10 —— 同一業務,但實作分裂。** 751 與 752 是同一套寫法(逐行對應,只差表名與欄位清單); **753 完全不同**:它把所有邏輯丟給版控外的 SP,C# 端只剩 14 行 `AddInParameter`。換句話說,`OFDI751` / `OFDI752` 的商業邏輯讀得到,`OFDI753` 的讀不到。

#### 5.8.2 `OFDI751` 的三道 `INNER JOIN`

`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:96-99` 連下三個 `JOIN`(全是 inner):

| JOIN | 條件 | 對不到的下場 |
|---|---|---|
| `JOIN OFD751` | `OFD751.TDCC_ID_NO_IT = ORDR01.CP_IDNO` | **集保統編還沒建對照的下單,整筆消失** |
| `JOIN BMS001A` | `BMS001A.BF_NO = OFD751.BF_NO` | 對照表有、但戶號已刪的,整筆消失 |
| `JOIN OFD081V` | `OFD081V.FUND_IS_TDCC_IT = ORDR01.CP_FUND_ID` | **集保基金代碼還沒對應的下單,整筆消失** |

第四個 join(轉入基金)是 `LEFT JOIN`,還特別加了 `AND NVL(OFD081_SW.FUND_IS_TDCC_IT,' ') <> ' '` 防 NULL(`:99`)—— **同一支 PO 裡,寫的人知道要防 NULL,卻只防了 `LEFT JOIN` 那一個,前三個 inner join 一個都沒防。**

結果類型全部是 **過濾(無提示)**。這是本片最值得警告營運端的一條: **集保下單查不到,不代表集保沒送——很可能是對照表沒建。**

### 5.9 三支死畫面:`OFDI058B` `OFDI375` `OFDI719`

這三支是本片最重要的發現,**兩層各自獨立的致命問題疊在一起**。

#### 5.9.1 第一層:`dbTA` 恆為 `null`,按下查詢的第一行就 NRE

三支的 PO 都繼承 `BasicEVAPO`。追下去:

| # | 事實 | 錨點 |
|---|---|---|
| 1 | 基底把連線物件宣告成 `protected Database dbTA = null;` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` |
| 2 | 基底建構子裡唯一會給它值的兩行(`dbTA = provider.Create("TA")`)**整段被註解掉** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:169-170`(建構子在 `:165-173`) |
| 3 | 基底全檔 2200 行、`dbTA` 出現 182 次,**沒有任何一處指派** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs` |
| 4 | 三支子類的建構子都是空的,也沒補上 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:17-19`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:23-26`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:14-16` |
| 5 | 三支的查詢方法**第一行**就 `dbTA.CreateConnection()` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:35`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:46`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:30` |
| 6 | **那一行全部在 `try` 外面** | `try` 分別在 `:36` / `:55` / `:36` |

**結論:按下查詢 → `NullReferenceException` → `catch` 接不到 → 往 FormProxy 丟。** `OFDI375` 與 `OFDI719` 更糟,連後面那行 `cn.Open()` 也在 `try` 外 (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:49`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:33`)。

對照組:甲派用基底自管的 `dbProduct`(例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:98`), 丙派每支自己 `new Database("TA", DbServerType.Oracle)`(例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:35`)。 **32 支都有連線,只有這三支沒有。**

> **殘留的不確定**:`BasicEVAPO` 的父類 `Basic_PO` **無原始碼**(從呼叫端反推), 若框架在建立 PO 之後用反射補寫這個 `protected` 欄位,則不會 NRE。本片查不到那樣的程式;而且 `BasicEVAPO` 自己的 `Add()` 也是直接 `dbTA.CreateConnection()` (`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`),顯示基底自己也假設有人會給值。 **標「假設」的是「一定 NRE」這個斷言**;**不是假設的是「repo 內查不到任何指派」這個事實**。

#### 5.9.2 第二層:就算連線有了,SQL 也是 T-SQL

`OFD.Query` 走的是「原檔改寫」而不是 EC 那種「Oracle 覆寫版」(§0.1), 所以改漏的會直接留在正式檔裡。三支剛好就是漏掉的那三支:

| 畫面 | T-SQL 特徵 | 錨點 |
|---|---|---|
| **`OFDI058B`** | `INTO #T081`(暫存表)、`DROP TABLE #T081`、`ISNULL()`、`dbo.f_GetBankHQ()`、`dbo.f_Round()`、`dbo.f_GetFundNav()`、`[Status]` 中括號、`@參數` + `SqlDbType` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:48`、`:118-120`、`:125`、`:156`、`:159-165` |
| **`OFDI719`** | `CONVERT(DECIMAL, …)`、`ISNULL()`、`dbo.f_FormatStringToTable()`、`@參數` + `SqlDbType` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:55`、`:60`、`:73-75`、`:82-86` |
| **`OFDI375`** | `[OFD375]` / `[BMS001]` / `[OFD002]` / `[COD009]` 中括號識別字 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:59-70` |

`OFDI719` 最刺眼:它的五個兄弟(`OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721`)全部已經是 Oracle 語法, 連對應的 Oracle 函式 `F_FormatStringToTable` 都用上了(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:92`), **只有 719 還停在 `dbo.f_FormatStringToTable`**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:75`)。典型的「成群畫面只改一部分」。

#### 5.9.3 `OFDI375` 深寫(受益人業務歸屬查詢)

138 行,最小的一支死畫面,結構最容易看懂:

| 段 | 內容 | 錨點 |
|---|---|---|
| 連線 | `dbTA.CreateConnection()` + `cn.Open()` **都在 `try` 外** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:46`、`:49` |
| SQL | `SELECT [OFD375].DATA_SEQ … FROM OFD375 LEFT JOIN BMS001 …` — 欄位用中括號包、表名不包 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:59-70` |
| 條件 | 3 處字串串接(部門 / 員工 / 戶號) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:84`、`:92`、`:100` |
| Ctl | **不繼承 `BaseController`**,`Select()` 自己 `new OFDI375_PO()` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:13`、`:38-44` |
| Ctl 搬資料 | 先手搬 10 欄(NULL 轉預設值),再叫一次框架搬 | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:66-82`、`:84` |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進方法 | `dbTA` 是否為 null | **永遠成立** | 阻擋(未處理例外) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:46` |
| 組 SQL | 三個條件字串串接 | 值含 `'` 時 | 阻擋(SQL 語法錯) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:84`、`:92`、`:100` |
| 搬資料 | NULL → `1900/01/01` / `0` / 空字串 | 欄位為 NULL 時 | 記錄不擋(語意遺失) | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:66-82` |

#### 5.9.4 `OFDI719` 深寫(集保結餘回饋檔查詢)

| 段 | 內容 | 錨點 |
|---|---|---|
| 連線 | 同 `OFDI375`,兩行都在 `try` 外 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:30`、`:33` |
| 數值換算 | `(CONVERT(DECIMAL, ISNULL(TRP804.STF673S11,0)) * 1.000000 / 100)` — 兄弟們寫的是 `CAST(NVL(…) AS NUMBER)` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:55` |
| 雙重 join 基金主檔 | `LEFT JOIN OFD081 ON OFD081.FUND_ID_TDCC = TRP804.STF673S3` **與** `LEFT JOIN OFD081V ON OFD081V.FUND_ID = TRP804.STF673S3` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:66-67`、`:71-72` |
| 條件 | `@TRANS_DATE_ST` / `@TRANS_DATE_END` / `@FUND_ID`,全部 `SqlDbType` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:73-75`、`:82-86` |
| 例外 | `catch` 把 `ex.Message` 貼給使用者,**沒有 `HandleBusinessException`** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:104-108` |

第三列那兩個 join 是獨立的缺陷,**跟死不死沒關係**: 同一個來源欄 `TRP804.STF673S3` 被拿去對 `OFD081.FUND_ID_TDCC`(集保代碼)**又**對 `OFD081V.FUND_ID`(本公司代碼)。兩者是不同編碼系統,不可能同時成立;實際上 `WHERE` 只用 `OFD081.FUND_ID`(`:75`), 所以 `OFD081V` 那個 join **只貢獻一個 `UNIT_DEC` 欄,而且多半對不到、回 NULL**。結果:**畫面上的小數位數欄空白,金額顯示位數錯誤**。結果類型:記錄不擋。收在附錄 E.5。

### 5.10 A / B 後綴七支:屬於哪一種成因

`ofd123.md §2.2` 整理過 OFD 的 `A` 後綴**至少三種成因**: 境內外(`FUND_TYPE` `'2'`/`'1'`,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`)、 MSSQL→Oracle 遷移改名、同概念第二張表。本片的七支帶 `A`、一支帶 `B`,**全部都不屬於這三種——它們是第四種**。

**判準:查它們 `JOIN` 的是 `OFDnnnA` 還是 `OFDnnn`。**

| 畫面 | 主要查的表 | 表名有沒有跟畫面同號 | 全庫 `OFDnnn` 用量 | 全庫 `OFDnnnA` 用量 | 判定 |
|---|---|---|---|---|---|
| `OFDI072A` | `OFD303A` | ✗(303 ≠ 072) | `OFD303` = 487 | `OFD303A` = 839 | **畫面代號自帶 A,與表無關** |
| `OFDI075A` | `OFD304A` | ✗ | `OFD304` = 89 | `OFD304A` = 483 | 同上 |
| `OFDI076A` | `OFD305A` | ✗ | `OFD305` = 7 | `OFD305A` = 191 | 同上 |
| `OFDI077A` | `OFD310A` | ✗ | `OFD310` = 0 | `OFD310A` = 11 | 同上 |
| `OFDI078A` | `OFD311A` | ✗ | `OFD311` = 40 | `OFD311A` = 23 | 同上 |
| `OFDI123A` | `OFD123A` | **✓** | `OFD123` = 0 | `OFD123A` = 511 | **唯一同號的一支**,但 `OFD123` 根本不存在 |
| `OFDI221A` | (SP `S_TA_OFDI221A_GET`) | — | `OFD221` = 3486 | `OFD221A` = 2485 | 查不到表,SP 在版控外 |
| `OFDI058B` | `OFD221A` `OFD251A` | ✗ | — | — | **`B` = 同一畫面的第二版**(`OFDI058` 也在同專案) |

計數方式:`grep -oE "\bOFDnnn\b"` 與 `\bOFDnnnA\b` 掃 `Dev/**/*.cs`,`\b` 確保 `OFD303` 不會誤配到 `OFD303A`。

**結論(本片新增的第四種成因)**:

> **在查詢畫面上,`A` 不是表的後綴,是畫面代號的一部分。** `OFDI075A` 這個代號從頭到尾就叫 `OFDI075A`—— 全庫沒有 `OFDI075`、沒有 `OFD075A` 這張表、`OFD075` 也不是它查的東西。七支裡有五支(`075A` `076A` `077A` `078A` `072A`)查的是**完全不同號的表**, 表的 `A` 後綴是那張表自己的事(多半是 `ofd4.md` 說的遷移改名), **與畫面的 `A` 後綴沒有因果關係**。

唯一的例外是 `OFDI123A` → `OFD123A`:號碼對上了,但 `OFD123`(無 A)在全庫 0 次引用, 所以這也不是「A/非A 成對」,只是**那張表本來就叫 `OFD123A`,畫面照著命名**。

`OFDI058B` 的 `B` 是另一回事:同專案裡 `OFDI058` 與 `OFDI058B` 並存 (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058_PO.cs` 與 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs` 都在), `OFDI058` 不在本片名單。**`B` 是「同一支查詢的第二版」**,與 `ofd123.md §2.2 第 13 列` 對 `OFD017B` 的判定一致 (「同一個業務概念的第二張表 / 第二支畫面」)。

### 5.11 其餘畫面:分群帶過

#### A 線 庫存四支(`OFDI075A` `OFDI076A` `OFDI077A` `OFDI078A`)

四支是同一個樣板複製出來的,差別只在表名與有沒有 `BF_NO` / `BAL_DATE`:

| 畫面 | 表 | 有 `BF_NO` | 有 `BAL_DATE` | 條件段行數 | 錨點 |
|---|---|---|---|---|---|
| `OFDI075A` | `OFD304A` | ✓ | ✗ | 5 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI075A_PO.cs:65-76`、`:93-117` |
| `OFDI076A` | `OFD305A` | ✓ | ✓ | 6 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI076A_PO.cs:65-76`、`:94-125` |
| `OFDI077A` | `OFD310A` | ✗ | ✗ | 1 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI077A_PO.cs:65-73`、`:79` |
| `OFDI078A` | `OFD311A` | ✗ | ✓ | 2 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI078A_PO.cs:65-74`、`:80`、`:87` |

四支共通的兩個問題:

1. **`JOIN OFD081A`(inner)**——基金主檔對不到就整列消失(過濾(無提示))。 `OFDI075A` / `OFDI076A` 還多一個 `JOIN BMS001A`(inner),受益人主檔對不到也消失。

2. **條件全部字串串接**,`OFDI078A` 的日期區間寫得特別脆: `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI078A_PO.cs:87` 把 `between` 也當字串串 (`" And (OFD311A.BAL_DATE " + "between" + "'" + Row.Value + "'" + " AND '" + Row1.Value + "')"`), `between` 與前面的欄名之間靠尾端空白撐著。**改動時很容易把空白吃掉變成 `BAL_DATEbetween`。** 同樣寫法出現在 `OFDI311_PO.cs:106`、`OFDI701_PO.cs:141`、`OFDI702_PO.cs:125`、`OFDI022_PO.cs:455`。

#### F 線 核印兩支(`OFDI701` `OFDI702`)

成對畫面,逐行對應(見 §5.2.2 與圖 4)。`OFDI701` 查扣款人的核印、`OFDI702` 查代理扣款機構的核印。 **兩支的差異全部是缺陷**:

| 差異 | `OFDI701` | `OFDI702` | 說明 |
|---|---|---|---|
| `Like` 分支的欄名 | **`Row.Name` 串兩次**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:154`) | 正常(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI702_PO.cs:138`) | 701 的 `SUB_ID_NO` 模糊查詢**必炸** |
| `SEAL_STATUS` 的 0/9 改寫 | 有(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:186-220`) | **沒有** | 702 選「已批次」查不到同樣的結果 |
| 欄名是否寫死 | 用 `Row.Name` | **`AGENT_BANK` 直接寫死**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI702_PO.cs:148`、`:152`) | 兩種風格混在同一支 |
| Model 檔名 | **`OFDI701Model..xsd`**(§2.6) | 正常 | 只有 701 錯 |
| Model / View 欄數 | 20 / 20 | **23 / 22** | 只有 702 錯 |

**兩支各錯各的,沒有一支是對的。**

#### F 線 控管兩支(`OFDI071` `OFDI072A`)

`OFDI071` 查 `OFD309A`(基金控管紀錄,帶程式代碼與退回備註),`OFDI072A` 查 `OFD303A`(基金交易控管碼)。兩支都是丁派字串串接(7 處 / 2 處),都 `JOIN OFD081A`(inner)。 `OFDI071` 多 `LEFT JOIN TA_AA_USER` 系列取部門與員工代碼,並用 `NVL(COD009.DEPT_NO,' ')` 防 NULL (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI071_PO.cs:72-73`)——**這支知道要 `NVL`,同一支的 inner join 卻沒防**。

#### F 線 `OFDI019`(CRS 申報)

全片結構最特別的一支:**同時走 SP 與自組 SQL**。

| 路徑 | 做什麼 | 錨點 |
|---|---|---|
| `GetQueryData` | 叫 `S_TA_OFDI019_GET`,兩個入參、**五個 RefCursor**,一次灌滿 `CRSP002`~`CRSP006` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:57-71` |
| 另一支方法的 `case "0"` | 自組 SQL 撈訊息編號清單進 `CRSP001_TEMP` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:135-139` |
| 另一支方法的 `case "99"` | 自組 SQL 撈「未被刪除的原訊息編號」 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:154-159` |

`case "99"` 那句 SQL 一行裡踩了兩個 Oracle 三值邏輯陷阱 (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:157-158`):

- `AND MESSAGE_TYPE <> 'CRS702'` —— `MESSAGE_TYPE` 若為 NULL,該列被濾掉;

- `AND MESSAGE_REF_ID NOT IN (SELECT DISTINCT CORR_MESSAGE_REF_ID FROM CRSP001)` —— **`CORR_MESSAGE_REF_ID` 只要有一列是 NULL,整個 `NOT IN` 對所有列都回 UNKNOWN,這句 SQL 會回 0 筆。** 而 `CORR_MESSAGE_REF_ID`(原訊息編號)在非刪除訊息上**本來就會是 NULL**—— 也就是說,**這個下拉清單在正常資料下很可能永遠是空的**。結果類型:**過濾(無提示)**。嚴重度高,因為 CRS 是法遵申報。

另外 `:133-134` 留著兩行被註解掉的 T-SQL(`CONVERT(VARCHAR,DATEPART(YEAR,GETDATE()))`), 是遷移前的訊息編號產生規則——**外殼還在、邏輯已被改成直接讀表**,屬於「被註解但外殼還在」那一型。

#### F 線 `OFDI123A`(KYC)

134 欄的結果集,全片最寬。SQL 本身只有 `SELECT OFD123A.* FROM OFD123A WHERE 1=1` (`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI123A_PO.cs:65-67`),條件走**四參數版 helper**(安全)。但有一個很特別的寫法要記:

```
Cmd.CommandText = strSQL.Replace("OFD123A.BF_COUNTRY_X", "substr('0'||OFD123A.BF_COUNTRY_X,-2)");
```

(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI123A_PO.cs:88`,註解寫「舊系統只有 1 碼」)

**它是在 helper 已經把 SQL 組好之後,再對整段 SQL 文字做字串取代。** 目的是把國別欄補成 2 碼再比對。風險:

- 只要哪天 `SELECT` 清單不是 `OFD123A.*` 而是列出欄名,`SELECT` 裡的 `OFD123A.BF_COUNTRY_X` 也會被換掉,**輸出欄位跟著變形**;

- 取代是無條件的,`WHERE` 與 `ORDER BY` 裡出現同樣字串都會被換。

目前因為 `SELECT` 用 `*` 所以剛好沒事。**這是靠巧合成立的程式**,收在附錄 E.7。

#### F 線 `OFDI060`(短線交易)

混合型:基金清單自組 SQL、短線次數走 SP `s_TA_OFDI060_Get`。自組的那段 SQL 在 `OPTION = 1` 與 `OPTION = 2` 兩條路上**把 bind 變數寫成裸識別字**:

| 行 | 內容 |
|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:81` | `strSQL += "WHERE OFD038A.FUND_GRPCD = FUND_GROUP "` |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:83` | `strSQL += "WHERE OFD081V.PROF_TYPE = FUND_TYPE "` |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:94` | `AddInParameter(cmdSelectDetail, "FUND_GROUP", …)` |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:100` | `AddInParameter(cmdSelectDetail, "FUND_TYPE", …)` |

Oracle 的 bind 變數在 SQL 文字裡必須寫成 `:FUND_GROUP`。寫成 `FUND_GROUP` 時, Oracle 會把它當成**識別字(欄名)**來解析,`OFD038A` 沒有這個欄 → `ORA-00904: invalid identifier`。也就是說 **`OPTION = 1` 與 `OPTION = 2` 這兩條路都會炸**,只有 `OPTION = 0`(全部)能用。嚴重度高。標「假設」的部分是:`Database` 無原始碼,若它會自動把 `AddInParameter` 的名字補上 `:` 再改寫 SQL 文字,則不會炸; 但同專案其他 32 支都老老實實在 SQL 裡寫 `:NAME`(例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:90-94`), **沒有任何證據顯示框架會做這件事**。收在附錄 E.4。

#### F 線 `OFDI022`(交易明細,527 行最長的一支)

全片最長的 PO。結構是「依交易類別 × 依境內外」四組 SQL,每組各自 `WHERE 1=1` 再串條件, 所以 26 處字串串接(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI022_PO.cs:104` 起、`:455` 起)。另有一大段被註解的 T-SQL 遺跡(`:443-449` 的 `dbo.f_FormatStringToTable`)—— **那段註解裡有一句正是把 `FUND_ID` 串進 `IN(...)` 的寫法,復活它等於復活一個注入點。**

#### B 線 `OFDI283`(收益分配)與 `OFDI481`(清算配息)

`OFDI283` 是甲派模範(9 個 `AddInParameter`),39 欄結果集,沒有特別的陷阱。 `OFDI481` 是丁派最糟的一支(§5.2.2),另有一個結構問題: 它**同時組兩句 SQL**(`strSQL` 與 `strSQL2`),兩句的條件要逐條同步維護。 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI481_PO.cs:124-125` 已經出現不同步的徵兆—— 同一個「發放日期」條件,第一句用 `A.PROVIDE_DATE`、第二句用 `X.PROVIDE_DATE`。兩個別名指向不同的表(`A` = `OFD497A` 一類、`X` = `OFD496A`,見 `:94-98`), **這可能是刻意的,也可能是改一邊忘了另一邊**——本片無法從程式判定,標「假設」, 依據是同檔其他 7 組條件(`:106-107`、`:114-115`、`:142-143`、`:151-152`、`:162-163`、`:174-175`)**全部兩句用同一個別名**, 只有這一組不同。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面。** 原因:`ATLAS.OFD.Query` 方案內 43 支畫面的代號第 4 碼全部是 `I`,沒有任何 `B`。本專案也沒有 `WindowsService` 資料夾——`architecture.md §6.4` 列的四支配服務的 B 畫面全部在 `ATLAS.EC` 與 `ATLAS.RSP`,與本片無關。

不過本片與 B 畫面有一條**對號關係**,值得記下來: 集保那兩群的查詢畫面與 `ATLAS.OFDB` 的批次**號碼是對應的**—— `OFDI716`↔`OFDB716`、`OFDI717`↔`OFDB717`、…、`OFDI721`↔`OFDB721`、`OFDI752`↔`OFDB752`。批次負責收檔與後處理,查詢畫面負責給人看同一批資料(§8.2)。 **改 `TRP8xx` 的欄位時,同號的 I 與 B 要一起看。**

## 7. 報表(R)

**本片無 R 畫面。** 原因:`architecture.md §6.5` 的鐵律——R 畫面住在 `ATLAS.<模組>.Report`,七層、多一個 `Report.<模組>` 專案放 `.rpt`。 OFD 的報表在 `Dev/ATLAS.OFD.Report`,不在本專案。

本片有 7 支會產檔(§5.7),但產的是 Excel,由 UI 端自己組,**不經 Crystal Reports、沒有 `.rpt`**。 `Dev/ATLAS.OFD.Report/Source/Entity/ReportDataEntity.OFD/OFDR751Model.Designer.cs` 顯示 `OFDR751` 這支報表也在讀 `ORDR01`——**同一批集保下單資料有 I 與 R 兩個出口**, 兩邊的欄位定義各自維護,沒有共用。

## 8. 跨模組共用

```text
[圖] OFDI1 查的表分別由誰寫入
圖中文字:本片只讀不寫。每一張被查的表,寫入端都在別的地方 / OFD221A OFD251A / 申購 / 贖回主檔 / OFDM 一線 + OFDB 批次 / 在 OFD 與 OFDB 兩個專案 / OFDI022 OFDI058B OFDI311 OFDI060 / 本片的查詢入口 / OFD304A OFD305A OFD310A OFD311A / 個人與基金庫存 即時與日結 / 結帳批次 OFDB 群 / repo 內為 BBS 與 OFDB 共寫 / OFDI075A OFDI076A OFDI077A OFDI078A OFDI901 / 本片的查詢入口 / TRP801A TRP804 TRP805A / TRP806A TRP810A 集保上傳與回饋檔 / OFDB717 到 OFDB722 / 同號批次做後處理 首次載入在版控外 / OFDI716 OFDI717 OFDI718 OFDI719 OFDI720 OFDI721 / 本片的查詢入口 / ORDR01 ORDR02 / 集保下單與回報 / OFDB752 OFDB757 / 同號批次做後處理 / OFDI751 OFDI752 / 本片的查詢入口 / CRSP001 到 CRSP006 / CRS 共同申報準則申報檔 / CRS 產檔批次 / repo 內僅見建表腳本 / OFDI019 唯一用實體表名當結果集 / 本片的查詢入口 / CTL014 / 全庫代碼對照表 共用 / CTL 模組維護 / 本片 11 支靠它把代碼轉中文 / OFDI701 OFDI716 到 OFDI721 OFDI058B / 本片的查詢入口 / 反向:本片的表被別人怎麼用 — 沒有。I 畫面不產生任何資料 / 本片沒有自己的表 / 35 支全部只有 SELECT 與 LoadDataSet / 影響面是單向的 / 上游改欄位本片要跟著改 本片改動不影響任何人
```

*圖:圖 5 跨模組。左欄=被查的表,中欄=寫入端,右欄=本片的查詢入口。灰虛框=寫入端,同號的 OFDB 批次(OFDI716 對 OFDB716 這種對應關係)。最下面一排是本片與其他片最大的差別:影響面完全單向。*

### 8.1 本片用到的共用 PO

**零。** 35 支 PO 沒有任何一支引用 `Dev/Common/Source/DataSource/PO.DataSource` 底下的共用 PO。唯一跨到 Common 的是工具類別:

| 共用元件 | 用途 | 誰用 | 錨點 |
|---|---|---|---|
| `EVAStringHelper.AddParam`(4 參數版) | 組**參數化**條件 | `OFDI123A` `OFDI901` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:198-201` |
| `EVAStringHelper.AddParam`(3 參數版) | 組**字串串接**條件(會跳脫 `'`,但 `IN` 不跳脫) | `OFDI751` `OFDI752` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:346-378` |
| `EVAStringHelper.GetParamValue` | 安全取參數值(有預設值) | `OFDI019` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:387-403` |
| `BasicEVAPO` | PO 基底(**`dbTA` 恆 null**) | `OFDI058B` `OFDI375` `OFDI719` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` |
| `BaseEVADaoPO` | PO 基底 | 12 支 | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17` |
| `SHORE_ID`(境內外代碼) | **本片沒有任何一支用到** | — | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |

最後一列要特別講:`ofd7.md §0.5` 把 `FUND_TYPE` `'1'`/`'2'` 當成本片同族的全域開關, **但 35 支查詢畫面一支都沒有用 `SHORE_ID` 這組常數**—— 境內外的區分在本片是靠查不同的表(`OFD081` vs `OFD081A`)或直接寫死(`OFDI022_PO.cs:75` 的 `AND SHORE_ID= '2'`)。 **寫死那一處是〔客戶特定〕且沒有走常數字典**,收在附錄 E.14。

### 8.2 本片查的表被誰寫 / 被誰共用

只列被本片查、且被三個以上模組碰到的表:

| 表 | 本片誰查 | 別的模組誰碰 | 風險 |
|---|---|---|---|
| `OFD221A`(申購) | `OFDI022` `OFDI058B` `OFDI311` | `ATLAS.OFD`(`OFDM231A` 等)、`ATLAS.OFDB`(多支批次)、`ATLAS.BBS`、`ATLAS.BMS` | 欄位改動打到最多人 |
| `OFD304A` / `OFD305A`(個人庫存) | `OFDI075A` `OFDI076A` `OFDI901` | `ATLAS.BBS`(`BBSM109` `BBSM110` `BBSM113`)、`ATLAS.OFDB`、`ATLAS.RSP`、`ATLAS.CPM` | 結帳批次寫、五個模組讀 |
| `OFD310A` / `OFD311A`(基金總庫存) | `OFDI077A` `OFDI078A` | `ATLAS.BBS`、`ATLAS.OFDB` | 同上 |
| `OFD701` / `OFD702`(核印) | `OFDI701` `OFDI702` | `ATLAS.OFDB` 的核印批次群、`ATLAS.CAS`(`CASI001_PO.cs:41` 的**註解**裡提過 `OFD701`) | `architecture.md §6.3` 提過那個註解害掃描器誤判 |
| `TRP801A` `TRP804` `TRP805A` `TRP806A` `TRP810A`(集保檔) | `OFDI716`~`OFDI721` | `ATLAS.OFDB`(`OFDB717` `OFDB718` `OFDB719` `OFDB720` `OFDB721` `OFDB722`) | **同號對應**,改欄位 I 與 B 要一起改 |
| `ORDR01` / `ORDR02`(集保下單) | `OFDI751` `OFDI752` | `ATLAS.OFDB`(`OFDB752` `OFDB757`)、`ATLAS.OFD.Report`(`OFDR751`) | 三個出口各自維護欄位 |
| `CTL014`(代碼對照) | 11 支 | 幾乎全庫 | 加一個 `SourceType` 不會壞事;**改既有 `TextValue` 會讓本片一批畫面的中文欄變空** |
| `OFD081A` / `OFD081V` / `BMS001A` / `COD009` | 幾乎每一支 | 全庫 | 見 §8.3 |

**`INSERT` 的來源查不到**:全 repo 掃 `INSERT INTO TRP8` 與 `INSERT INTO ORDR0` **0 筆**, OFDB 側只有 `UPDATE` 與 `DELETE`。首次載入推測在版控外(收檔程式 / 外部工具)。標「假設」。

### 8.3 本片的表被誰用 — 沒有

**這是 I 畫面與 M / B 畫面最大的結構差異:影響面是單向的。**

- 本片**不產生任何資料**,所以沒有「本片的表被誰讀」這個問題;

- 上游改欄位 → 本片的 SQL 與 xsd 要跟著改;

- 本片改動 → **不影響任何其他模組**。

實務上的意義:**改這 35 支的風險局限在畫面本身**, 不用像改 M 畫面那樣擔心下游批次、報表、四眼流程。反過來說,**上游任何一次欄位異動都可能讓這裡的某支畫面悄悄壞掉而沒人發現**—— 因為 I 畫面沒有測試、沒有批次會報錯,只有使用者某天說「查不到」。

### 8.4 改動影響面速查

| 你要改的東西 | 本片要跟著看的 |
|---|---|
| `OFD081A` / `OFD081V` 的 `FUND_ID` / `FUND_SH_NM` / `UNIT_DEC` / `DEC_LEN` | **至少 20 支**(幾乎所有畫面都 join 它取基金簡稱與小數位) |
| `BMS001A` 的 `BF_NO` / `ID_NO` / `BF_NAME` | `OFDI075A` `OFDI076A` `OFDI283` `OFDI311` `OFDI481` `OFDI751` `OFDI752` `OFDI901` |
| `CTL014` 的 `SourceType` `'000'` | `OFDI716`~`OFDI721` 六支的「刪除註記」欄會變空白 |
| `CTL014` 的 `SourceType` `'100'` / `'149'` / `'232'` / `'236'` | `OFDI701` 的四個中文欄(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:119-130`) |
| `CTL014` 的 `SourceType` `'204'` | `OFDI058B` 的贖回處理碼中文 |
| `TRP805A` / `TRP806A` 的 `SIN1`~`SIN9` 欄位定義 | `OFDI716` `OFDI717` 的 xsd **與** `OFDB721` 的批次 |
| 11 支版控外 SP 的回傳欄位 | 對應畫面的 xsd(有 xsd 的 5 支)或 Excel 輸出(無 xsd 的 6 支,**不會編譯錯**) |
| `OFD152` / `OFD153`(查詢權限群組) | 只有 `OFDI058B`;但改它**不會**讓其他 34 支跟著受限(§0.5) |

## 附錄 A. 資料表總表

本片**沒有自己的表**。以下是 35 支查詢畫面碰到的 44 張表 / View,依角色分類。「主檔於」欄指哪個模組負責維護,由該表在全庫的 `xTableMapping` 宣告與寫入語句反推;查不到的標「版控外」。

| # | 表 / View | 角色 | 本片誰查 | 主檔於(推測) |
|---|---|---|---|---|
| 1 | `OFD221A` | 申購主檔 | `OFDI022` `OFDI058B` `OFDI311` | `ATLAS.OFD` + `ATLAS.OFDB` |
| 2 | `OFD251A` | 贖回主檔 | `OFDI022` `OFDI058B` | 同上 |
| 3 | `OFD281A` | 收益分配設定 | `OFDI283` | `ATLAS.OFD` |
| 4 | `OFD283A` | 收益分配明細 | `OFDI283` | `ATLAS.OFD` |
| 5 | `OFD303A` | 基金交易控管碼 | `OFDI072A` | `ATLAS.OFD` |
| 6 | `OFD304A` | 受益人即時庫存 | `OFDI075A` | `ATLAS.OFDB` / `ATLAS.BBS` |
| 7 | `OFD305A` | 受益人日結庫存 | `OFDI076A` `OFDI901` | 同上 |
| 8 | `OFD309A` | 基金控管紀錄 | `OFDI071` | `ATLAS.OFD` |
| 9 | `OFD310A` | 基金即時總庫存 | `OFDI077A` | `ATLAS.OFDB` |
| 10 | `OFD311A` | 基金日結總庫存 | `OFDI078A` | `ATLAS.OFDB` |
| 11 | `OFD375` | 受益人業務歸屬 | `OFDI375` | `ATLAS.OFD` |
| 12 | `OFD494A` | 清算主檔 | `OFDI481` | `ATLAS.OFD` |
| 13 | `OFD496A` | 清算配息明細 | `OFDI481` | `ATLAS.OFD` |
| 14 | `OFD497A` | 清算配息發放 | `OFDI481` | `ATLAS.OFD` |
| 15 | `OFD701` | 扣款帳戶核印 | `OFDI701` | `ATLAS.OFDB` |
| 16 | `OFD702` | 代理扣款機構核印 | `OFDI702` | `ATLAS.OFDB` |
| 17 | `OFD711` | 核印退件原因 | `OFDI701` `OFDI702` | `ATLAS.OFD` |
| 18 | `OFD123A` | KYC 資料 | `OFDI123A` | `ATLAS.OFD` |
| 19 | `LOG221A` | 受益權轉讓軌跡 | `OFDI311` | `ATLAS.OFD` |
| 20 | `SRNOCOMMENT` | 刪除書號註記 | `OFDI010` | 版控外(無 `xTableMapping`) |
| 21 | `TA_AA_USER` | 系統使用者 | `OFDI010` | 平台側 |
| 22 | `TA_SWPRODUCTSDETAIL` | 功能選單明細 | `OFDI071` | 平台側 |
| 23 | `CRSP001` | CRS 申報主檔 | `OFDI019` | `ATLAS.OFD`;`DB/Table/CRSP001.sql` 有建表 |
| 24 | `CRSP002` | CRS 帳戶持有人身分 | `OFDI019` | 同上 |
| 25 | `CRSP003` | CRS 帳戶持有人稅籍 | `OFDI019` | 同上 |
| 26 | `CRSP004` | CRS 具控制權人身分 | `OFDI019` | 同上 |
| 27 | `CRSP005` | CRS 具控制權人稅籍 | `OFDI019` | 同上 |
| 28 | `CRSP006` | CRS 金額資料 | `OFDI019` | 同上 |
| 29 | `TRP801A` | 集保回饋檔 | `OFDI718` | `OFDB718` 後處理;`INSERT` 查不到 |
| 30 | `TRP804` | 集保結餘回饋檔 | `OFDI719` | `OFDB717` / `OFDB722`;`INSERT` 查不到 |
| 31 | `TRP805A` | 集保結餘上傳主檔 | `OFDI716` | `OFDB721`;`INSERT` 查不到 |
| 32 | `TRP805A_Detail` | 集保結餘上傳明細 | `OFDI716` | 同上 |
| 33 | `TRP806A` | 集保交易上傳主檔 | `OFDI717` | 同上 |
| 34 | `TRP806A_Detail` | 集保交易上傳明細 | `OFDI717` | 同上 |
| 35 | `TRP810A` | 集保收檔 | `OFDI720` `OFDI721` | `OFDB719` / `OFDB720`;`INSERT` 查不到 |
| 36 | `ORDR01` | 集保下單 | `OFDI751` `OFDI752` | `OFDB752` / `OFDB757`;`INSERT` 查不到 |
| 37 | `ORDR02` | 集保下單回報 | `OFDI752` | `OFDB757`;`INSERT` 查不到 |
| 38 | `OFD751` | 集保 ID 對照戶號 | `OFDI751` `OFDI752` | `ATLAS.OFD` |
| 39 | `OFD152` | 查詢群組 × 員工 | `OFDI058B` | `ATLAS.OFD` |
| 40 | `OFD153` | 查詢群組 × 基金 | `OFDI058B` | `ATLAS.OFD` |
| 41 | `OFD300` | 匯率 | `OFDI901` | `ATLAS.OFD` |
| 42 | `OFD220A` | 申購委託 | `OFDI058B` | `ATLAS.OFD` |
| 43 | `OFD233` | 銀行確認 | `OFDI058B` | `ATLAS.OFD` |
| 44 | `OFD0811` | 基金大額門檻 | `OFDI058B` | `ATLAS.OFD` |

說明欄專用的上游(每支都 `LEFT JOIN` 取名稱,不列進上表的主查對象): `OFD081` `OFD081A` `OFD081V`(基金主檔三版本)、`BMS001` `BMS001A`(受益人)、 `COD009`(員工)、`OFD002`(部門)、`OFD006A` `OFD038A`(基金分類 / 群組)、 `OFD020A` `OFD020V`(銀行)、`CTL014`(代碼對照)。

## 附錄 B. SP / Function / Trigger / View

### B.1 SP — 11 支,**全部在版控外**

`grep -ril` 掃全 repo 的 `.sql` / `.pck` / `.prc`,以下 11 支一支都找不到,已全部列進 meta 的 `refcheck-ignore`:

| SP | 被誰叫 | 入參 | 回傳 | 錨點 |
|---|---|---|---|---|
| `s_TA_OFDI016_Get` | `OFDI016` | 年度 / 國籍 / 國別 / 境內外 / 基金 | DataSet | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI016_PO.cs:52` |
| `S_TA_OFDI019_GET` | `OFDI019` | `iMESSAGE_REF_ID` `iYEARS` | **5 個 RefCursor** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:57-71` |
| `s_TA_OFDI060_Get` | `OFDI060` | — | — | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:133` 起的第二個方法 |
| `S_TA_OFDI221A_GET` | `OFDI221A` | 8 個 bind | — | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI221A_PO.cs:26` 起 |
| `S_TA_OFDI753_GET` | `OFDI753` | **14 個 bind** | — | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI753_PO.cs:24` 起 |
| `s_TA_OFDI912_1_Get` | `OFDI912` | 依交易類別二選一 | DataSet | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI912_PO.cs:54` |
| `s_TA_OFDI912_2_Get` | `OFDI912` | 同上 | DataSet | 同上 |
| `s_TA_OFDI913_Get` | `OFDI913` | 8 個 bind | **2 個 RefCursor** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI913_PO.cs:59-74` |
| `s_TA_OFDI914_Get` | `OFDI914` | 8 個 bind | 2 個 RefCursor | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI914_PO.cs:53` |
| `s_TA_OFDI915_Get` | `OFDI915` | `striFUND_ID` | **9 個 RefCursor** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI915_PO.cs:59-75` |
| `s_TA_OFDI916_Get` | `OFDI916` | 9 個 bind | — | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI916_PO.cs:53` |

**命名不一致**:小寫 s 開頭 7 支、大寫 S 開頭 4 支。Oracle 物件名預設大寫不敏感,所以不影響執行, 但**任何用字串比對找 SP 的工具都要同時試兩種大小寫**。

### B.2 Function — 5 支,4 支在版控外

| Function | 方言 | 被誰用 | 在 repo 內 |
|---|---|---|---|
| `F_FormatStringToTable` | Oracle | `OFDI716` `OFDI717` `OFDI718` `OFDI720` `OFDI721` + 4 參數版 `AddParam` | **只在 `DB/SP/` 底下兩支 OTA 的 SP 內被引用**,本體查不到 |
| `f_FormatStringToTable` | **T-SQL(`dbo.`)** | `OFDI719`(死畫面)、`OFDI022` 的註解 | 查不到 |
| `f_TA_SplitWords` | Oracle | `OFDI481` | 查不到 |
| `f_GetBankHQ` / `f_Round` / `f_GetFundNav` | **T-SQL(`dbo.`)** | `OFDI058B`(死畫面) | 查不到 |

### B.3 Trigger / View

- **Trigger**:本片沒有任何一支 PO 提到 Trigger。

- **View**:`OFD081V` 與 `OFD020V` 從命名與用法判斷是 View(`V` 結尾、只被 `SELECT`、沒有任何模組對它寫入)。本片 20 支以上讀 `OFD081V`。**View 的定義在版控外**,`DB/View/` 底下查不到這兩支。標「假設」。

## 附錄 C. 代碼對照

本片自己不定義任何代碼,全部靠 `CTL014` 的 `SourceType` 分群查表。用到的 `SourceType`:

| `SourceType` | 意義(推測) | 誰用 | 錨點 |
|---|---|---|---|
| `'000'` | 刪除註記(`DEL_YN`) | `OFDI716`~`OFDI721` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:88-89` |
| `'100'` | 核印方式(`SEAL_TYPE`) | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:119-121` |
| `'149'` | 扣款人身分別(`ACC_SUB_ID`) | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:125-127` |
| `'204'` | 贖回處理碼(`REDEM_PROC_CODE`) | `OFDI058B` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:129-131` |
| `'232'` | 核印狀態(`SEAL_STATUS`) | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:122-124` |
| `'236'` | 資料來源(`SOURCE_CD`) | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:128-130` |

**六個編號都是〔客戶特定〕的魔術數字**,程式裡直接寫字面量,沒有走 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的常數字典。

程式裡自己用 `CASE` 寫死、不查 `CTL014` 的代碼(改了要改程式):

| 代碼 | 值域 | 誰寫死 | 錨點 |
|---|---|---|---|
| `CP_TXTYPE`(集保交易型態) | `P` 申購 · `R` 買回 · `S` 轉申購 · `N` No Order | `OFDI751` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:73` |
| `CP_FEE_TYPE`(收費型態) | `F` 前收型 · `B` 後收型 | `OFDI751` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:76`、`:83` |
| `RECEIPT_DOC_ID1` / `2` | `Y` 已寄發 · `N` 未寄發 | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:108-113` |
| `SEAL_STATUS` 的 `0` / `9` | `0` 未批次 · `9` 已批次(**`9` 不是資料庫裡的值,是程式現算的**) | `OFDI701` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:94-97`、`:186-220` |
| `SHORE_ID` 境內 `'2'` | 寫死在 SQL 字串,不走常數 | `OFDI022` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI022_PO.cs:75` |
| `TRADE_TYPE` 中文 `'申購'` / `'贖回'` | 直接寫在 `SELECT` 裡當欄位值 | `OFDI058B` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:69`、`:111` |
| 未成立基金 `FUND_SETUP_DATE = '1900/1/1'` | 哨兵日期 | `OFDI058B` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:254-258` |
| 空日期 `19000101` → 空字串 | 哨兵日期轉換 | `OFDI913` `OFDI914` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI913_PO.cs:62-63` |

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module OFD`** ——那會拿 OFD 模組全部 551 支畫面來比,本片只負責 35 支,覆蓋率會失真。改成自列清單。

### D.1 35 支逐一處置

| # | 代號 | 本文處置 | PO 基底 | 在 csproj(UI/Pxy/Ctl/PO) | 節 |
|---|---|---|---|---|---|
| 1 | `OFDI010` | **已寫**(參數化正面教材) | 無基底 | 四層齊 | §5.2.1 |
| 2 | `OFDI016` | 表格帶過 + 匯出深寫 | 無基底 | 四層齊(無 xsd) | §2.4、§5.7 |
| 3 | `OFDI019` | **已寫**(SP + 自組 SQL 混合、`NOT IN` NULL 陷阱) | 無基底 | 四層齊 | §5.11 |
| 4 | `OFDI022` | **已寫**(最長、26 處串接) | `BaseEVADaoPO` | 四層齊 | §5.11 |
| 5 | `OFDI058B` | **深寫**(死畫面 + 唯一權限控制) | **`BasicEVAPO`(死)** | 四層齊 | §5.5、§5.9 |
| 6 | `OFDI060` | **已寫**(bind 變數漏冒號) | 無基底 | 四層齊 | §5.11 |
| 7 | `OFDI071` | 表格帶過 | 無基底 | 四層齊 | §5.11 |
| 8 | `OFDI072A` | 表格帶過 + A 後綴判定 | 無基底 | 四層齊 | §5.10、§5.11 |
| 9 | `OFDI075A` | 表格帶過 + A 後綴判定 | 無基底 | 四層齊 | §5.10、§5.11 |
| 10 | `OFDI076A` | 表格帶過 + A 後綴判定 | 無基底 | 四層齊 | §5.10、§5.11 |
| 11 | `OFDI077A` | 表格帶過 + A 後綴判定 | 無基底 | 四層齊 | §5.10、§5.11 |
| 12 | `OFDI078A` | 表格帶過 + A 後綴判定 | 無基底 | 四層齊 | §5.10、§5.11 |
| 13 | `OFDI123A` | **已寫**(字串取代改 SQL) | 無基底 | 四層齊 | §5.11 |
| 14 | `OFDI221A` | **已寫**(唯一有匯出前阻擋的) | 無基底 | 四層齊 | §5.7 |
| 15 | `OFDI283` | 表格帶過(甲派模範) | 無基底 | 四層齊 | §5.11 |
| 16 | `OFDI311` | **已寫**(丁派樣板) | `BaseEVADaoPO` | 四層齊 | §5.2.2 |
| 17 | `OFDI375` | **深寫**(死畫面) | **`BasicEVAPO`(死)** | 四層齊 | §5.9.3 |
| 18 | `OFDI481` | **深寫**(無引號注入點) | 無基底 | 四層齊 | §5.2.2、§5.11 |
| 19 | `OFDI701` | **深寫**(圖 4 主角) | `BaseEVADaoPO` | 四層齊(Model 檔名異常) | §5.11、圖 4 |
| 20 | `OFDI702` | **深寫**(成對比較) | `BaseEVADaoPO` | 四層齊 | §5.11 |
| 21 | `OFDI716` | **深寫**(C 群代表) | `BaseEVADaoPO` | 四層齊 | §5.4.2 |
| 22 | `OFDI717` | 表格帶過 | `BaseEVADaoPO` | 四層齊 | §5.4.1 |
| 23 | `OFDI718` | 表格帶過 | `BaseEVADaoPO` | 四層齊 | §5.4.1 |
| 24 | `OFDI719` | **深寫**(死畫面 + T-SQL) | **`BasicEVAPO`(死)** | 四層齊 | §5.9.4 |
| 25 | `OFDI720` | 表格帶過 | `BaseEVADaoPO` | 四層齊 | §5.4.1 |
| 26 | `OFDI721` | 表格帶過 | `BaseEVADaoPO` | 四層齊 | §5.4.1 |
| 27 | `OFDI751` | **深寫**(三道 inner join) | `BaseEVADaoPO` | 四層齊 | §5.8.2 |
| 28 | `OFDI752` | 表格帶過 | `BaseEVADaoPO` | 四層齊 | §5.8.1 |
| 29 | `OFDI753` | 表格帶過(全走 SP) | `BaseEVADaoPO` | 四層齊 | §5.8.1 |
| 30 | `OFDI901` | **深寫**(`9xx` 群 + 三值邏輯) | 無基底 | 四層齊 | §5.6 |
| 31 | `OFDI912` | **已寫**(匯出群) | 無基底 | 四層齊(無 xsd) | §2.4、§5.6、§5.7 |
| 32 | `OFDI913` | **已寫**(匯出群) | 無基底 | 四層齊(無 xsd) | §2.4、§5.6 |
| 33 | `OFDI914` | 表格帶過 | 無基底 | 四層齊(無 xsd) | §5.6 |
| 34 | `OFDI915` | **已寫**(9 個游標) | 無基底 | 四層齊(無 xsd) | §2.4、§5.6 |
| 35 | `OFDI916` | 表格帶過 | 無基底 | 四層齊(無 xsd) | §5.6 |

**覆蓋率:35 / 35 = 100%。深寫 12 支、已寫 9 支、表格帶過 14 支。**

### D.2 csproj 核對

逐支比對六個 csproj 的 `<Compile>` / `<None>` 節點:

| 層 | 應有 | 實際在 csproj | 缺 |
|---|---|---|---|
| UI(`QueryUI.OFD.csproj`) | 35 | 35 | **0** |
| FormProxy(`QueryFormProxy.OFD.csproj`) | 35 | 35 | **0** |
| Control(`QueryControl.OFD.csproj`) | 35 | 35 | **0** |
| PO(`QueryPO.OFD.csproj`) | 35 | 35 | **0** |
| DataEntity(`QueryDataEntity.OFD.csproj`) | 29(6 支本來就沒有) | 29 | **0**,但 `OFDI701` 以 `OFDI701Model..xsd` 登錄(§2.6) |
| UIEntity(`QueryUIEntity.OFD.csproj`) | 29 | 29 | **0** |

**「檔案存在但不在 csproj」這一型缺陷,本片 0 筆。** 這與 `ofd123.md 附錄 D` 的 M 畫面結果不同——查詢專案反而比維護專案乾淨。

### D.3 不在本片的 8 支

同專案還有 8 支 I 畫面不在本片名單,留給後續查詢片: `OFDI058` `OFDI059` `OFDI070` `OFDI199` `OFDI562` `OFDI902` `OFDI907` `OFDI911`。其中 `OFDI059` 也繼承 `BasicEVAPO`,**依 §5.9 的推論它同樣是死畫面**,寫下一片時要先驗這一條。

## 附錄 E. 讀本文時要注意的地方

依嚴重度排序。「嚴重度」分三級:**高**=功能不可用或有安全風險;**中**=特定條件下出錯或給錯資料;**低**=可讀性 / 維護性。

### E.1 `BasicEVAPO.dbTA` 恆為 null,三支畫面按查詢就炸 — **高**

- **缺陷**:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` 宣告 `protected Database dbTA = null;`, 建構子裡唯一的指派被註解掉(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:169-170`),全檔 2200 行無其他指派。

- **影響**:`OFDI058B` `OFDI375` `OFDI719` 三支查詢方法的第一行就 `dbTA.CreateConnection()`, 且**都在 `try` 外**,`NullReferenceException` 直接往上丟。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:35`(`try` 在 `:36`)、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI375_PO.cs:46`(`try` 在 `:55`)、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:30`(`try` 在 `:36`)。

- **注意**:`OFDI059`(不在本片名單)同樣繼承 `BasicEVAPO`,推測同症。

### E.2 `OFDI481` 的期別條件沒有引號,是裸注入點 — **高**

- **缺陷**:`strSQL += " AND A." + Row.Name + " = " + Row.Value` ——值直接接進 SQL,連單引號都沒有。

- **影響**:畫面上「期別」欄輸入 `1 OR 1=1` 即成立,可撈出全表。其他丁派至少要先用 `'` 脫逃。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI481_PO.cs:142` 與 `:143`(兩句 SQL 各一次)。

### E.3 Oracle 三值邏輯:`<>` 與 `NOT IN` 遇 NULL 靜默吃資料 — **高**

九個模組中過同一型,本片三處:

| 處 | 條件 | 後果 | 錨點 |
|---|---|---|---|
| `OFDI901` | 九個 `欄 <> 0` 用 `OR` 串 | 九欄全 NULL 的庫存列**完全消失** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:112-120` |
| `OFDI019` | `MESSAGE_REF_ID NOT IN (SELECT DISTINCT CORR_MESSAGE_REF_ID FROM CRSP001)` | 只要有一列 `CORR_MESSAGE_REF_ID` 是 NULL,**整句回 0 筆**;而該欄在非刪除訊息上本來就是 NULL | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:158` |
| `OFDI019` | `AND MESSAGE_TYPE <> 'CRS702'` | `MESSAGE_TYPE` 為 NULL 的列被濾掉 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:157` |
| `OFDI058B` | `AND OFD081V.FUND_SETUP_DATE <> '1900/01/01'` / `AND OFD221A.ALLOT_PROC_CODE <> 'D'` | 同型 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:60`、`:93` |

`OFDI019` 那一條特別嚴重:**CRS 是法遵申報**,下拉清單空白會讓使用者以為沒有可刪除的申報。

### E.4 `OFDI060` 的 bind 變數少了冒號 — **高**

- **缺陷**:SQL 文字寫 `WHERE OFD038A.FUND_GRPCD = FUND_GROUP`,Oracle 會把 `FUND_GROUP` 當欄名解析。

- **影響**:`OPTION = 1`(依基金群組)與 `OPTION = 2`(依基金種類)兩條路都會 `ORA-00904`,只有 `OPTION = 0` 能用。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI060_PO.cs:81`、`:83`, 對應的 `AddInParameter` 在 `:94`、`:100`。

- **標「假設」**:`Database` 無原始碼;若它會自動補冒號則不成立。但同專案其他 32 支都在 SQL 文字裡寫 `:NAME` (例 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:90-94`),沒有證據顯示框架會做這件事。

### E.5 `OFDI719` 同一欄同時對兩種編碼 join — **中**

- **缺陷**:`TRP804.STF673S3` 同時被 `LEFT JOIN OFD081 ON OFD081.FUND_ID_TDCC = …`(集保代碼) 與 `LEFT JOIN OFD081V ON OFD081V.FUND_ID = …`(本公司代碼)使用。兩者是不同編碼系統。

- **影響**:`OFD081V` 那個 join 幾乎必然對不到,只貢獻一個 `UNIT_DEC` 欄回 NULL → **畫面上金額小數位顯示錯誤**。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:66-67` 與 `:71-72`, `WHERE` 只用 `OFD081.FUND_ID`(`:75`)。

### E.6 例外處理三套並存,同一個錯在不同畫面表現不同 — **中**

| 派 | 做法 | 使用者看到 | 畫面 |
|---|---|---|---|
| 甲 | `AddResultRow(false, 0, ex.Message)` | **Oracle 原文錯誤訊息**(含表名欄名) | `OFDI716` `OFDI719` |
| 乙 | `CommonExceptionBlocker.HandleBusinessException(ex)` | 框架的例外視窗 | `OFDI311` `OFDI701` `OFDI702` `OFDI901` `OFDI123A` 等 |
| 丙 | **兩個都做** | 先塞訊息再彈視窗 | `OFDI010` `OFDI060` `OFDI058B` `OFDI913` `OFDI915` |

- **影響**:甲派把資料庫結構洩漏到畫面;丙派同一個錯誤講兩次。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:175-179`(甲)、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI311_PO.cs:154-157`(乙)、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI010_PO.cs:97-102`(丙)。

### E.7 `OFDI123A` 用字串取代改已組好的 SQL — **中**

- **缺陷**:`Cmd.CommandText = strSQL.Replace("OFD123A.BF_COUNTRY_X", "substr('0'||OFD123A.BF_COUNTRY_X,-2)")` ——對整段 SQL 無條件取代。

- **影響**:目前因為 `SELECT` 用 `OFD123A.*` 所以剛好只命中 `WHERE`。哪天有人把 `SELECT` 展開成欄位清單,**輸出欄位會跟著被包上 `substr`**。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI123A_PO.cs:88`。

### E.8 NULL 在 Ctl 被轉成哨兵值,語意遺失 — **中**

- **缺陷**:`OFDI375_Ctl` 逐欄 `row.IsXXXNull() ? 預設值 : row.XXX`,日期預設 `new DateTime(1900,01,01)`、數字 `0`、字串空。

- **影響**:畫面上的 `1900/01/01` 分不出是「真的是這個日期」還是「NULL」。 `OFDI058B` 又剛好用 `'1900/1/1'` 當「基金未成立」的哨兵(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:257`), **同一個魔術日期在兩個地方代表不同意思**。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI375_Ctl.cs:66-82`。

### E.9 Model 與 View 欄數對不上 — **中**

| 畫面 | Model | View | 錨點 |
|---|---|---|---|
| `OFDI702` | `OFDI702` 23 欄 | `OFDI702` **22 欄** | `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI702Model.xsd` / `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI702View.xsd` |
| `OFDI060` | `OFDI060_SHORT_TIME` 9 欄 | `OFDI060_SHORT_TIME` **11 欄** | `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI060Model.xsd` / `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI060View.xsd` |

- **影響**:`TransferVDBHelper.TransferTable` 是逐欄對應,多出來 / 少掉的欄位**不會報錯,就是空的**。 `OFDI702` 是少一欄(Model 有、View 沒有 → 那個欄永遠傳不到畫面); `OFDI060` 是多兩欄(View 有、Model 沒有 → 畫面上永遠空白)。

### E.10 `OFDI701Model..xsd` 檔名多一個點 — **低**

- **缺陷**:檔名、三個附屬檔與 csproj 全部多一個點。

- **影響**:編譯與執行都正常,但**用命名規則掃檔的工具會判成缺 DataEntity 層**。孿生的 `OFDI702` 檔名正常——成對畫面只錯一邊。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/QueryDataEntity.OFD.csproj:222`、`:558`。

### E.11 `OFDI058B` 的權限保護不了資料 — **中**

- **缺陷**:`OFD152` / `OFD153` 的查詢權限只做在 `OFDI058B` 一支。

- **影響**:同一批 `OFD221A` / `OFD251A` / `OFD305A` 資料,換 `OFDI022` / `OFDI076A` / `OFDI901` 去查**完全不受限**。而 `OFDI058B` 本身又是死畫面(E.1),**等於這套權限現況一支畫面都沒保護到**。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:49-58`; 對照 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI076A_PO.cs:65-76`(同表、無權限條件)。

### E.12 六支匯出畫面的欄位契約完全在版控外 — **中**

- **缺陷**:`OFDI016` `OFDI912`~`OFDI916` 沒有 xsd,結果集形狀由 SP 的 RefCursor 決定。

- **影響**:SP 改欄位,**C# 端不用重編、不會編譯錯、不會執行期錯**,直接反映到使用者的 Excel。沒有任何一層攔得住。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI915_PO.cs:64-75`(9 個游標 + 9 個中文表名寫死)。

### E.13 `IN` 條件在三參數版 `AddParam` 完全沒跳脫 — **中**

- **缺陷**:`strValue = "(" + strValue + ")"`,不加引號也不跳脫。

- **影響**:`OFDI751` / `OFDI752` 若有任何條件的 `Opeartor` 是 `IN`,就從安全掉回注入風險。

- **錨點**:`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:369-370`; 呼叫端 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:104-106`、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI752_PO.cs:97`。

- **標「假設」**:實際 `Opeartor` 由 UI 控件型別決定,本片未逐支驗證。

### E.14 寫死常數與魔術數字 — **低**

`SHORE_ID` 境內 `'2'` 寫死在 SQL(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI022_PO.cs:75`)、六個 `CTL014.SourceType` 編號寫死(附錄 C)、 `'TWD'` 匯率寫死(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:110`)、 `SIN2 = '0'` 寫死(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:95`)。 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 有常數字典但本片一支都沒用。

### E.15 被註解但外殼還在 — **低**

| 處 | 內容 | 錨點 |
|---|---|---|
| `OFDI022` | 一整段 T-SQL 條件組法,含把 `FUND_ID` 串進 `IN(...)` 的寫法 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI022_PO.cs:443-449` |
| `OFDI019` | 遷移前的訊息編號產生規則(`CONVERT(VARCHAR,DATEPART(YEAR,GETDATE()))`) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI019_PO.cs:133-134` |
| `OFDI311` / `OFDI701` | 自建連線的 `Dbcon.Open()` / `finally` 全段註解 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:244-248` |
| `BasicEVAPO` | **就是 E.1 的元兇** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:169-170` |

**復活 `OFDI022` 那段等於復活一個注入點**,不要直接取消註解。

### E.16 `/*RowNum*/` 是死記號 — **低**

`OFDI701` 與 `OFDI702` 的 `SELECT` 開頭有 `/*RowNum*/`,看起來像分頁掛鉤, 但全 repo 只有這兩處提到 `RowNum`,**沒有任何程式讀它**。別以為這兩支有分頁——**35 支全部沒有分頁**,一次撈全部。錨點:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:75`、 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI702_PO.cs:75`。

### E.17 `OFDI058B` 查無資料時 `Result` 是空的 — **中**

- **缺陷**:`Result.Clear()` 之後只在有資料時 `AddResultRow`,**沒有 `else`**。

- **影響**:呼叫端若照其餘 34 支的慣例讀 `Result[0]`,0 筆時 index out of range。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058B_PO.cs:167-170`; 對照有 `else` 的 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:163-173`。

### E.18 `OFDI701` 的 `Like` 分支把欄名串兩次 — **高**

- **缺陷**:`strSQL += " And OFD701." + Row.Name + Row.Name + " Like " + …` —— `Row.Name` 出現兩次。

- **影響**:「扣款人 ID」用模糊查詢時,SQL 變成 `OFD701.SUB_ID_NOSUB_ID_NO Like '…%'` → `ORA-00904`。 **這支畫面的模糊查詢必炸。** 孿生的 `OFDI702` 同一段是對的。

- **錨點**:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI701_PO.cs:154`; 對照 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI702_PO.cs:138`。

### E.19 `INNER JOIN` 讓對不到的資料無聲消失 — **中,但範圍最廣**

至少 11 支中這一型,最嚴重的是 `OFDI751` 連下三個:

| 畫面 | JOIN | 對不到時 | 錨點 |
|---|---|---|---|
| `OFDI751` | `OFD751` / `BMS001A` / `OFD081V` 三個 inner | 集保對照表沒建 → **整筆下單查不到** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI751_PO.cs:96-99` |
| `OFDI716` | 明細 `JOIN TRP805A` | 主檔缺列 → 明細消失 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:129-130` |
| `OFDI075A` `OFDI076A` | `JOIN BMS001A` + `JOIN OFD081A` | 受益人或基金主檔對不到 → 庫存消失 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI075A_PO.cs:65-76` |
| `OFDI010` | `JOIN TA_AA_USER` | 建檔人已離職刪帳號 → **刪除軌跡查不到** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI010_PO.cs:69-70` |
| `OFDI716` 等 | `LEFT JOIN OFD081V` + `WHERE OFD081V.FUND_ID IN (…)` | **`LEFT JOIN` 被 `WHERE` 打回 inner** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:86-92` |

最後一列是最容易被忽略的:寫的人以為用了 `LEFT JOIN` 就安全, **但只要在 `WHERE` 對右表欄位下條件(`IS NULL` 除外),`LEFT JOIN` 就等同 `INNER JOIN`**。

### E.20 `OFDI901` 與 `OFDI076A` 是重複實作 — **低**

兩支查同一張 `OFD305A`、`SELECT` 欄位重疊 14 個,`OFDI901` 只多匯率三欄。改庫存欄位時**兩支都要改**,但沒有任何註解或命名提示它們有關係。錨點:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI076A_PO.cs:65-76` 對 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI901_PO.cs:64-95`。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。全庫第一篇查詢畫面(I)文件,涵蓋 `Dev/ATLAS.OFD.Query` 的 35 支 I 畫面。建立 I vs M 的 34 列對照表(§0.2)與查詢篇章節配置(§4 空、§5 主體、§6 §7 空)。確認:PO 命名為 `_PO.cs` 不是 `OracleDao.cs`(§0.1);三支 `BasicEVAPO` 畫面因 `dbTA` 恆 null 按查詢即 NRE(§5.9、附錄 E.1);13 支把使用者輸入直接串進 SQL、其中 `OFDI481` 連引號都沒有(§5.2、附錄 E.2);`9xx` 不是管理用途(§5.6);`A` 後綴在查詢畫面是第四種成因——畫面代號自帶,與表無關(§5.10);csproj 缺漏 0(附錄 D.2) |

由 build_doc.py v2.0.0 於 2026-09-15 19:52 產生 · 標題 97 · 圖 5 · 表格 58 · 程式錨點 246 · § 連結 119 · 引用檢查：畫面 59（缺 0） · Table 2（缺 0） · 結果集 18（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofdi2.md
============================================================

# ATLAS OFDI2 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先讀 §0.2 的「三條軌」那張表——本片 38 支橫跨三個專案,不先把軌搞清楚,後面每一節都會看成亂碼。要動手改某支的人查 §3 清冊定位再跳 §5。急著知道哪裡咬人的翻附錄 E,**本片的頭號地雷是 §5.1 那個 `NVL(TRIM(:P), 欄)` 樣板**。

> ⚠ **OFDI2 不是一個業務模組,是一份切片**,承接 `ofdi1.md`。涵蓋 `Dev/ATLAS.OTA.Query` 的 24 支 I 畫面 + `Dev/ATLAS.EC.Query` 的 13 支 I 畫面 + `Dev/ATLAS.OFD` 的孤兒 M 畫面 `OFDM287` 一支,共 **38 支**。名稱 `OFDI2` 為**推測**。

> ⚠ **本片與 `ofdi1.md` 最大的差異**:`ofdi1.md` 那 35 支是「一個專案內的六條業務線」;本片 38 支是**同一段業務被三條技術軌切成三份**。看懂切分方式比看懂任何單一支畫面重要。

> ⚠ **本片有 6 支是死的**(檔案在、不在 csproj、PO 整檔被註解),另有 15 支 PO 是**全檔註解的屍體**仍掛在 csproj 上。不要把它們當現行行為讀,見 §0.4。

> ⚠ **〔客戶特定〕**:基金短線交易費率、通路代碼 `CHANNEL_CD` / `AGENT_CODE` 編碼、電子交易來源碼 `SOURCE_CD`、`CTL014` 的 `SourceType` 編號為本站台的值。

> ⚠ **〔共用〕**:`OFD081` / `OFD081A`(基金主檔)、`OFD062`(基金公司)、`OFD601`(受益人基本資料)、`OFD606A`、`BMS001A`、`FSK003`(幣別)、`CTL014`、`OFD019A`(銀行)幾乎每支都讀,改欄位會同時打到本片十幾支畫面(見 §8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §5`、畫面型別四種看 `architecture.md §6`。**不要整份讀**。 I 畫面與 M 畫面的通則差異看 `ofdi1.md §0`,本文不重複,只寫**本片的例外**(§0.5)。

## 0. 系統邊界與角色

### 0.1 先破除三個會浪費半天的假設

動手前先把三件事釘死,否則檔案都找不到。

**假設一:PO 檔名照代號推。錯。** 本片兩個專案用**兩套命名**,而且資料夾名與組件名還故意不一致:

| 專案 | PO 資料夾 | csproj 檔名 | PO 檔名慣例 | 支數 |
|---|---|---|---|---|
| `ATLAS.OTA.Query` | `Source/PO/QueryPO.OFD/` ← **資料夾叫 OFD** | `QueryPO.OTA.csproj` ← **組件叫 OTA** | `<代號>_PO.cs` | 25 |
| `ATLAS.EC.Query` | `Source/PO/QueryPO.EC/Oracle/` | `QueryPO.EC.csproj` | **`<代號>OracleDao.cs`** | 8 |
| `ATLAS.EC.Query` | `Source/PO/QueryPO.EC/MSSQL/` | 同上 | `<代號>_PO.cs`(**全是屍體**) | 15 |

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/` 這個路徑最會騙人:**資料夾名是 `QueryPO.OFD`,但 csproj 是 `QueryPO.OTA.csproj`、namespace 是 `Vendor.Product.TA.QueryPO.OTA`** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:17`)。 Control / FormProxy / UI / Entity 五層同樣是「資料夾 `.OFD`、csproj `.OTA`」。這是從 `ATLAS.OFD.Query` 複製整棵樹改出來的痕跡,**沒改資料夾名**。

**假設二:`ofdi1.md` 說的「查詢畫面一半在串字串」在本片也成立。錯,而且錯很大。** 本片 `ATLAS.OTA.Query` 的 25 支 PO,`EVAStringHelper.AddParam` 的出現次數是 **0**; `db.AddInParameter` 的出現次數是 **125**。**這一片是全庫目前看過參數化最徹底的一片**(§5.2)。代價是換來另一種缺陷——`NVL(TRIM(:P), 欄)` 這個「空條件不過濾」的樣板本身會**無聲吃掉 NULL 資料列**(§5.1、附錄 E.1)。

**假設三:`OFDI601`~`OFDI615` 這段連號被「切成兩半」。錯,它不是切,是搬家搬到一半。** 見 §0.4,這是本片最大的結構問題。

### 0.2 三條軌:境內分戶 / 境外綜合帳戶 / 電子交易

`ofdb5.md` 與 `misc.md` 已查證 `ATLAS.OFD` 是**境內分戶軌**、`ATLAS.OTA` 是**境外綜合帳戶軌**, 分家方式是「畫面代號加後綴 + 表名去掉 `A`」。本片實測把第三條軌補上:

| 軌 | 專案根 | 業務定位(推測) | 資料表命名 | 本片支數 |
|---|---|---|---|---|
| **境內分戶** | `Dev/ATLAS.OFD` / `Dev/ATLAS.OFD.Query` | 國內基金、分戶式登錄 | 帶 `A`:`OFD081A` | 1(只有 `OFDM287`) |
| **境外綜合帳戶** | `Dev/ATLAS.OTA` / `Dev/ATLAS.OTA.Query` | 境外基金、綜合帳戶(omnibus) | **不帶 `A`**:`OFD081` `OFD651` `OFD652` | 24 |
| **電子交易** | `Dev/ATLAS.EC` / `Dev/ATLAS.EC.Query` | 網路 / 語音下單、對帳與軌跡 | 帶 `A`,且多 `LOG600` 系列軌跡表 | 13 |

**關鍵證據:同一個業務概念在兩條軌上是兩張表。** `OFDI612A`(境外軌)查 `OFD651` / `OFD652`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:127-129`); `IPJI612`(電子交易軌)查 `OFD651A` / `OFD652A` / `OFD653A`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:172-176`)。 **`OFD651` 與 `OFD651A` 就是境外 vs 電子交易的同一張表的兩個版本**,和 `ofdb5.md` 記的「去 `A`」規則方向一致 ——只是那篇寫的是「境內有 `A`、境外無 `A`」,本片證實**電子交易軌也用帶 `A` 的那一套**,也就是說: **帶 `A` 的表是「原本那張」,不帶 `A` 的是境外軌另開的一份。**〔假設〕依據是本片 `OTA.Query` 25 支 PO 完全不碰任何帶 `A` 的 `OFD6xx` 表, 而 `EC.Query` 8 支 live PO 完全不碰任何不帶 `A` 的 `OFD6xx` 表——兩邊表名集合**零交集**,不是巧合。

`IPJI620` 是這條規則最漂亮的一個證明:它一支就讀 `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` 五張表 (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI620OracleDao.cs:39-303`), 而境外軌的 `OFDI601`~`OFDI605` 是**一支畫面查一張 `OFD611`~`OFD615`** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:74-77`)。 **同一組五張表,境外軌切成五支畫面、電子交易軌合成一支多頁籤畫面。**

### 0.3 本片 38 支涵蓋哪些業務線

切片依據是專案資料夾,不是業務,所以本片內部仍是**七條互不相干的業務線**:

| # | 業務線 | 畫面 | 支數 | 主要表 |
|---|---|---|---|---|
| 1 | **境外基金申購 / 贖回 / 轉換 單據查詢** | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 5 | `OFD620` `OFD621` `OFD651` `OFD652` `OFD653` `OFD663` `OFD664` `OFD666` `OFD667` |
| 2 | **境外基金作業參數 / 費率主檔查詢** | `OFDI601` `OFDI602` `OFDI603` `OFDI604` `OFDI605` | 5 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615` |
| 3 | **對帳單 / 通知書 產製紀錄查詢** | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` | 5 | `OFD223` `OFD255` `OFD224` `OFD256` |
| 4 | **客戶 / 帳戶 / 稅務資料查詢** | `OFDI002` `OFDI071A` `OFDI072B` `OFDI283A` | 4 | `OFD105` `OFD309` `OFD303` `OFD281` `OFD283` |
| 5 | **定期定額 / 標的組合查詢** | `OFDI531` `OFDI553` `OFDI554` `OFDI563` `OFDI564` | 5 | `OFD535` `OFD536` `OFD551` `OFD552` `OFD554` `OFD555` `OFD563` `OFD564` |
| 6 | **電子交易(網路 / 語音)軌跡與對帳** | `IPJI612` `IPJI613` `IPJI614` `IPJI620` `IPJI630` `OFDI607` `OFDI608` | 7 | `OFD601` `LOG600` `LOG601` `LOG602` `OFD607A` 與 `OFD6xxA` 全家 |
| 7 | **已停用的電子交易舊查詢** | `OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` | 6 | (無,PO 全註解) |
| — | **孤兒 M 畫面** | `OFDM287` | 1 | 見 §4 |

### 0.4 `OFDI601` 到 `OFDI615`:不是切成兩半,是搬家搬到一半

這是本片最大的結構問題,必答問題 1 的答案。**先看三個事實:**

**事實一:`EC.Query` 有完整的 `OFDI601` 到 `OFDI615` 十五支六層,一支不缺。** UI / Pxy / Ctl / Model.xsd / View.xsd 全在 (`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/`、 `Dev/ATLAS.EC.Query/Source/Entity/QueryDataEntity.EC/`)。 **所以這一段連號原本整段住在 `EC.Query`,不是從一開始就分兩邊。**

**事實二:`EC.Query` 那十五支 PO 全部被整檔註解掉,一行沒留。** `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI601_PO.cs:19`、 `OFDI602_PO.cs:17`、`OFDI603_PO.cs:18`、`OFDI604_PO.cs:19`、`OFDI605_PO.cs:19`、 `OFDI606_PO.cs:18`、`OFDI607_PO.cs:19`、`OFDI608_PO.cs:17`、`OFDI609_PO.cs:17`、`OFDI610_PO.cs:17`、 `OFDI611_PO.cs:17`、`OFDI612_PO.cs:17`、`OFDI613_PO.cs:17`、`OFDI614_PO.cs:15`、`OFDI615_PO.cs:15` ——每一支的 class 宣告行都長這樣(以 `OFDI612` 為例):

```
//    public class OFDI612_PO : BasicEVAPO
```

連 `using` 都被註解(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI612_PO.cs:1-14`)。 **而這十五支屍體仍然全部掛在 csproj 上**(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`), 編譯得過只因為整檔沒有任何有效 token。這是本片第一條缺陷(附錄 E.11)。

**事實三:`EC.Query` 的 Control 層 csproj 只收 8 支,其餘 13 支 Ctl 檔在磁碟上但不編譯。** `Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/QueryControl.EC.csproj:108-115` 只列 `IPJI612` `IPJI613` `IPJI614` `IPJI620` `IPJI630` `OFDI607` `OFDI608` `OFDI641` 八支的 `_Ctl.cs`。 `OFDI601_Ctl.cs` 到 `OFDI615_Ctl.cs`(扣掉 607 / 608)這 13 支**不在 csproj**, 而且它們的內容還在 `new OFDI601_PO()`(`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/OFDI601_Ctl.cs:34`) ——一個已經被註解掉、根本不存在的型別。**放回 csproj 就是編譯錯誤**,不是能跑的程式。

**把三個事實接起來,故事是這樣的(〔假設〕,依據見下):**

| 階段 | 發生什麼 | 證據 |
|---|---|---|
| 1 MSSQL 時代 | `OFDI601` 到 `OFDI615` 十五支住在 `EC.Query`,PO 繼承 `BasicEVAPO`,用 `SystemConfigurationSource` + `DatabaseProviderFactory` 取 `TA` 連線 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI612_PO.cs:17,24-27`(註解內) |
| 2 境外軌分家 | 業務切出「境外綜合帳戶」,這段查詢跟著搬到 `ATLAS.OTA.Query` | `OTA.Query` 的 PO 標頭寫 `Created on: 2023/08/28`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:1-6`) |
| 3 Oracle 改寫 | 新軌整支重寫成 Oracle 語法,加 `PODbType` 屬性與 `Database("TA", DbServerType.Oracle)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:28-30` |
| 4 撞名改後綴 | `OFDI612` / `613` / `614` 在 `EC.Query` 已存在,新軌加 `A` 避開,成為 `OFDI612A` / `613A` / `614A` | 同號三對,見 §5.5 |
| 5 舊軌拆一半 | 舊 PO 整檔註解、Ctl 退出 csproj,但 UI / Pxy / xsd / PO 檔本體**都沒刪** | 事實二 / 三 |
| 6 沒搬完 | `OFDI606` `OFDI609` `OFDI610` **兩邊都沒有活的實作**,功能等於消失 | `OTA.Query` 無此三支;`EC.Query` 三支 PO 全註解 |
| 7 兩支留下 | `OFDI607` `OFDI608` 走**第三條路**:留在 `EC.Query`,但改寫成 `OracleDao` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:15` |

所以**「橫跨兩個專案」的正確描述是:一段連號的查詢群在境外軌分家時被整段搬走,搬到 10 / 15, 剩下 5 支中 2 支原地改寫、3 支直接爛在原地。** 不是設計,是遷移殘留。

**這對維護的意義**:

| 你想做的事 | 實際結果 |
|---|---|
| 改 `OFDI612` 的查詢條件 | 改到屍體,線上完全無感——要改的是 `OFDI612A` |
| 把 `OFDI609` 加回選單 | 加不回來,PO 已註解、Ctl 不在 csproj,得整支重寫 |
| 以為 `OFDI611` 在 `EC.Query` 跑 | 跑的是 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs` |
| 搜尋 `OFDI613` 找不到 bug | 搜到的是 `EC.Query` 那份註解,真正跑的叫 `OFDI613A` |

### 0.5 本片相對 `ofdi1.md` 通則的例外

`ofdi1.md §0` 那張 I vs M 對照表是本片的前提,以下只列**本片打破的格**:

| `ofdi1.md` 的結論 | 本片實測 | 差在哪 |
|---|---|---|
| UI 基底一律 `xOneStepProcessForm` | **成立**,`OTA.Query` 25 支全中(`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI601.cs:16`) | 無例外 |
| PO 基底三派並存(無基底 / `BaseEVADaoPO` / `BasicEVAPO`) | **本片 live 的 33 支全部是「無基底」**,只實作自己的 `I<代號>_PO` 或 `I<代號>` 介面 | **更極端** |
| `BasicEVAPO` 是地雷 | 本片 `BasicEVAPO` 出現 15 次,**全部在被註解的屍體裡**(§0.4) | 地雷已被埋起來 |
| `MasterTable` 宣告 0 支 | **成立**,37 支查詢畫面 0 支 | 無例外 |
| 四眼 13 欄 0 個 | **不成立**,`OFDM287` 是 M 畫面,有完整四眼(§4) | **本片唯一例外** |
| 寫入路徑 0 條 | **不成立**,`OFDM287` 有 `Update`(§4) | **本片唯一例外** |
| xsd 是結果集形狀,根節點等於畫面代號 | 成立於 37 支;`OFDM287` 的 Model 根節點是實體表 | 同上一格 |
| 條件組法四派,字串串接 13 / 35 | **本片字串串接 0 / 33**(§5.2) | **完全相反** |

**一句話**:本片 37 支查詢畫面把 `ofdi1.md` 的通則推到極致(更沒基底、更沒四眼、更參數化), 而 `OFDM287` 那一支是整片唯一的反例,所以它單獨佔 §4。

### 0.6 使用角色與全域開關

| 項 | 內容 | 錨點 |
|---|---|---|
| 使用角色(推測) | 境外基金作業人員(業務線 1 / 2 / 5)、對帳與客服(業務線 3 / 4)、電子交易維運(業務線 6) | 由查詢條件與結果欄位反推 |
| 權限控管 | **本片 37 支查詢 PO 內完全沒有權限檢核**,不像 `ofdi1.md` 的 `OFDI058B_PO.CheckPower()`;權限只靠選單層 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/` 全數無 `CheckPower` |
| 全域開關 | 無。本片沒有任何 `app.config` / 參數表驅動的行為分支 | — |
| 連線 | `OTA.Query` 全部 `new Database("TA", DbServerType.Oracle)`;`EC.Query` live 8 支同樣走 Oracle | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:30` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDI2 全景:境外綜合帳戶軌 24 支、電子交易軌 13 支、境內分戶軌 1 支
圖中文字:ATLAS.OTA.Query 境外綜合帳戶軌:24 支,全部 Oracle 參數化 / OFDI611 612A 613A 614A 615 / 申購 贖回 轉換 定額 契約異動 / OFDI601 到 OFDI605 / OFD611 到 OFD615 參數主檔 / OFDI051 052 055 056 057 / 對帳單 通知書 產製紀錄 / OFDI002 071A 072B 283A / 客戶 控管 配息 / OFDI531 553 554 563 564 / 定期定額 授權 匯款 / OFD081 OFD062 FSK003 / 基金 公司 幣別(不帶 A) / BMS001A OFD019A CTL014 / 受益人 銀行 代碼(共用) / ATLAS.EC.Query 電子交易軌:7 支活的 + 6 支死的 / IPJI612 613 614 620 630 / 網路下單軌跡與對帳 / OFDI607 OFDI608 / LOG600 到 LOG602 變更軌跡 / OFDI606 609 610 612 613 614 / 不在 csproj,PO 全註解 / OFD6xxA OFD65xA OFD67xA / 電子交易軌的表(帶 A) / ATLAS.OFD 境內分戶軌:本片只收到一支孤兒 M / OFDM287 / OFD283A 配息給付維護 + 四眼 / OFD283A OFD281A OFD081V / 境內軌的表(帶 A) / OFDI283A 查的是 OFD283 / 同名不同物,見 5.6 / 三軌共同的地雷:NVL(TRIM(:P), 欄) 空條件樣板 / 欄位是 NULL 的資料列 / NULL = NULL 得 UNKNOWN / 不進結果集 / 使用者看到「查無資料」 / 沒有任何提示 / 過濾(無提示),22 支中招
```

*圖:圖 1 OFDI2 全景。橘框=本片的畫面;灰虛框=被讀但不歸本片管的上游表;黑框=在磁碟上但不編譯的死碼;紫框=風險點。三條軌之間沒有任何程式呼叫,只靠表名的 A 後綴規則區分彼此。最下面那一列不是某一支的問題,是三軌共用的 SQL 樣板缺陷。*

### 1.2 三條軌的分工與 `OFDI6xx` 跨專案切分

(圖由 `ofdi2.figs.py` 注入,對應 §2)

這張是本片的招牌圖。要一句話帶走的話:**`OFDI601` 到 `OFDI615` 這段連號不是被「切」成兩半,是「搬」到一半。** 細節見 §0.4 的五階段表與 §5.5 的逐對 diff。

### 1.3 四眼、批次報表、一日作業

三節都不畫。`OFDM287` 是本片唯一的 M,它沒有任何客製階段動作,照 `architecture.md §3` 的通用四眼圖讀即可(卡控寫在 §4); 本片無 B 也無 R(§6 §7);查詢畫面不參與排程,沒有時間軸可畫。

### 1.4 依 PO 基底與條件組法分群

(圖由 `ofdi2.figs.py` 注入,對應 §3)

### 1.5 最重的一支:`OFDI553` 的查詢流程與過濾點

(圖由 `ofdi2.figs.py` 注入,對應 §5)

### 1.6 跨模組:本片讀的表是誰建的

(圖由 `ofdi2.figs.py` 注入,對應 §8)

## 2. 資料模型

```text
[圖] 三條軌的分工與 OFDI6xx 跨專案切分的五個階段
圖中文字:第一階段 MSSQL 時代:OFDI601 到 OFDI615 十五支整段住在 EC.Query / EC.Query 六層齊全 / PO 繼承 BasicEVAPO,走 MSSQL / OFDI601 到 OFDI615 / 一支畫面一個業務,連號無缺 / MSSQL 資料庫 / DatabaseProviderFactory 取 TA / 第二階段 2023 年:境外軌分家,整段搬到 OTA.Query 並改寫 Oracle / 搬走 10 支 / 601 到 605 · 611 · 615 / 撞號改後綴 3 支 / 612 613 614 變 612A 613A 614A / 原地改寫 2 支 / OFDI607 OFDI608 變 OracleDao / 第三階段 收尾沒做完:舊軌留下屍體,三支功能直接消失 / PO 整檔註解 15 支 / 仍掛在 QueryPO.EC.csproj 上 / Ctl 退出 csproj 13 支 / 檔案還在,內容 new 一個不存在的型別 / OFDI606 609 610 蒸發 / 兩邊都沒有活的實作 / 結果:同號三對分屬兩專案,但根本不是同一個查詢 / OFDI612A 境外 / 查 OFD651 OFD652 買回單據 / OFDI612 電子交易(死) / 查網路變更生效日,業務無關 / OFD612A 這張表 / 由 IPJI620 讀,跟兩者都無關 / 穩定成立的分身規則:畫面代號加後綴,表名去掉 A / OFDI071 查 OFD309A(境內) / OFDI071A 查 OFD309(境外) / OFDI072A 查 OFD303A(境內) / OFDI072B 查 OFD303(境外) / OFDI283 查 OFD283A(境內) / OFDI283A 查 OFD283(境外)
```

*圖:圖 2 本片招牌圖。上三列是 OFDI601 到 OFDI615 這段連號被切開的時間順序,第四列說明「同號三對」不是同一查詢的兩個軌、只是代號撞號,最後一列是真正穩定成立的境內外分身規則:畫面代號加後綴、表名去掉 A。*

### 2.1 本片沒有 `xTableMapping`,但有一支例外

`ofdi1.md §0` 的結論是「I 畫面的 `MasterTable` 宣告 0 支」。本片實測:

| 專案 | 支數 | `MasterTable` 宣告 | 取數方式 |
|---|---|---|---|
| `ATLAS.OTA.Query` | 24 | **0 支** | `dbTA.LoadDataSet(cmd, model.DataEntity, model.DataEntity.<代號>.TableName)` |
| `ATLAS.EC.Query`(live) | 7 | **0 支** | `db.LoadDataSet(cmd, resultVDB.DataEntity, resultVDB.DataEntity.<表>.TableName)` |
| `ATLAS.OFD`(`OFDM287`) | 1 | **有**:`this.MasterTable = new xTableMapping("OFD283A", "OFDM287")` | 框架代勞 |

`OFDM287` 那一行在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:32`。 **所以「本片有幾張實體主表」這個問題,只有 `OFDM287` 回答得出來,其餘 37 支只能從 `FROM` / `JOIN` 反推。**

### 2.2 結果集的形狀:三種命名,全部不是實體表

| 命名法 | 例 | 意義 | 支數 |
|---|---|---|---|
| **結果集名 = 畫面代號** | `model.DataEntity.OFDI612A.TableName`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:152`) | 最常見,`OTA.Query` 全部這樣 | 23 |
| **結果集名 = 別支畫面的代號** | `model.DataEntity.OFDI562.TableName`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93`) | **`OFDI563` 借用 `OFDI562` 的整套 xsd**,見 §2.4 | 1 |
| **結果集名 = 實體表名** | `resultVDB.DataEntity.OFD618A.TableName`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:109`)、`OFD673A`(`IPJI612OracleDao.cs:863`) | `EC.Query` 的舊寫法殘留 | 3 |
| **結果集名 = 另一個畫面代號 + 用途後綴** | `resultVDB.DataEntity.IPJI621_Master.TableName`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632`) | **`IPJI612` 的七個結果集全叫 `IPJI621_*`**,見 §5.8 | 1 |

最後一列值得單獨記住:**`IPJI612` 這支畫面的所有結果集都叫 `IPJI621_`**—— `IPJI621` 這支畫面在本庫**不存在**(`find Dev -name "IPJI621*"` 為 0 筆)。〔假設〕是 `IPJI621` 被併進 `IPJI612` 時沒改 xsd 的表名,依據是七個結果集(`IPJI621_Master` `IPJI621_Allot` `IPJI621_Redeem` `IPJI621_RSP` `IPJI621_RSPCHG` `IPJI621_STOPSET` `IPJI621_STOPCHG`)全部同一個前綴, 不像是打錯一次。

### 2.3 Model.xsd 與 View.xsd 的欄數(`OTA.Query` 24 支)

xsd 是**結果集形狀**,不是實體表形狀;欄位中文名取自 `msdata:Caption`。本片 **Model 與 View 欄數 24 支全部一致**,沒有 `ofdi1.md` 那種對不上的破口:

| 畫面 | 結果集表名 | Model 欄 | View 欄 | 對齊 |
|---|---|---|---|---|
| `OFDI002` | `OFDI002` | 13 | 13 | 是 |
| `OFDI051` | `OFDI051` | 43 | 43 | 是 |
| `OFDI052` | `OFDI052` | 51 | 51 | 是 |
| `OFDI055` | `OFDI055` | 40 | 40 | 是 |
| `OFDI056` | `OFDI056` | 45 | 45 | 是 |
| `OFDI057` | `OFDI057` | 59 | 59 | 是 |
| `OFDI071A` | `OFDI071A` | 10 | 10 | 是 |
| `OFDI072B` | `OFDI072B` | 12 | 12 | 是 |
| `OFDI283A` | `OFDI283A` | 64 | 64 | 是 |
| `OFDI531` | `OFDI531` | 38 | 38 | 是 |
| `OFDI553` | `OFDI553` | 50 | 50 | 是 |
| `OFDI554` | `OFDI554` | 44 | 44 | 是 |
| **`OFDI563`** | **`OFDI562`** | **25(借)** | **25(借)** | **沒有自己的 xsd** |
| `OFDI564` | `OFDI564` | 13 | 13 | 是 |
| `OFDI601` | `OFDI601` | 10 | 10 | 是 |
| `OFDI602` | `OFDI602` | 9 | 9 | 是 |
| `OFDI603` | `OFDI603` | 9 | 9 | 是 |
| `OFDI604` | `OFDI604` | 8 | 8 | 是 |
| `OFDI605` | `OFDI605` | 8 | 8 | 是 |
| `OFDI611` | `OFDI611` | 61 | 61 | 是 |
| `OFDI612A` | `OFDI612A` | 61 | 61 | 是 |
| `OFDI613A` | `OFDI613A` | 67 | 67 | 是 |
| `OFDI614A` | `OFDI614A` | 50 | 50 | 是 |
| `OFDI615` | `OFDI615` | 61 | 61 | 是 |

同資料夾還有 `OFDI562`(25 欄)與 `TRPI001`(19 欄、**兩張表 `TRPI001` + `TRP001`**), **兩支都不在本片 38 支名單內**,列出來只是避免下一個人以為漏掉。

### 2.4 `OFDI563`:全片唯一的四層畫面

`OFDI563` 在磁碟上**沒有 `OFDI563Model.xsd`,也沒有 `OFDI563View.xsd`**, `Dev/ATLAS.OTA.Query/Source/Entity/QueryDataEntity.OFD/` 與 `.../QueryUIEntity.OFD/` 兩個資料夾內都找不到。它整套借 `OFDI562` 的:

| 位置 | 內容 | 錨點 |
|---|---|---|
| PO 取數 | `model.DataEntity.OFDI562.TableName` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93` |
| Ctl 簽名 | `public OFDI562ViewVDB Select(OFDI562ViewVDB view)` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:42` |
| Ctl 搬資料 | `TransferVDBHelper.TransferTable(view.UIView.OFDI562, model.DataEntity.OFDI562, base.TransferEVAColumn)` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:58` |
| Ctl 委派型別 | `POActionDelegate<OFDI562ModelVDB>` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:87` |

**這不是 bug,是刻意共用**——`OFDI562`(匯款授權書查詢)與 `OFDI563`(授權申請查詢)結果欄位相同, 差別只在 `OFDI562_PO` 查 `OFD562`、`OFDI563_PO` 查 `OFD563` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:73-86`)。 **但它有後遺症**:改 `OFDI562` 的欄位會同時改到 `OFDI563` 的畫面,而 `OFDI563` 的任何檔名都不會出現在 grep 結果裡。嚴重度:中(見附錄 E.7)。

### 2.5 本片讀到的表總覽(依被讀支數排序)

只列 `FROM` / `JOIN` 真實出現的表;`SELECT` 子句內的欄位別名已濾掉。

| 表 | 被幾支讀 | 讀它的畫面 | JOIN 型 | 備註 |
|---|---|---|---|---|
| `OFD081` | 16 | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI071A` `OFDI072B` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | INNER / LEFT 混用 | 境外軌基金主檔,〔共用〕 |
| `OFD062` | 15 | `OFDI051` `OFDI055` `OFDI071A` `OFDI072B` `OFDI283A` `OFDI553` `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` | 多為 `FROM` 起點 | 境外基金公司,〔共用〕 |
| `FSK003` | 13 | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` | **多為 INNER JOIN** | 幣別主檔,**漏一筆整列消失**(附錄 E.3) |
| `BMS001A` | 10 | `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI563` `OFDI564` `IPJI612` | INNER / LEFT 混用 | 受益人主檔,〔共用〕 |
| `OFD606A` | 10 | `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 全 LEFT JOIN | **境外軌卻用帶 `A` 的表名**,§2.6 的反例 |
| `OFD601` | 9 | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` `OFDI607` `OFDI608` `IPJI612` `IPJI630` | INNER / LEFT 混用 | **兩條軌共讀的唯一一張表** |
| `OFD019A` | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` | LEFT JOIN | 銀行分行 |
| `OFD199` | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` | LEFT JOIN | 活動代碼 `CAMPAIGN_CODE` |
| `OFD081A` | 3 | `IPJI612` `IPJI614` `IPJI620` | INNER / LEFT | 電子交易軌的基金主檔。**grep 會多抓到 `OFDI052`,那是別名不是表**,§2.6 |
| `CTL014` | 3 | `OFDI055` `IPJI612` `IPJI614` | `FROM` / LEFT | 系統代碼對照 |
| `COD006A` | 2 | `OFDI553` `OFDI554` | LEFT JOIN | 以 `CODE_SORT = 'A8'` 過濾 |
| `OFD020V` | 2 | `OFDI283A` `IPJI612` | LEFT JOIN | 分行 View |
| `OFD256` | 2 | `OFDI056` `OFDI057` | `FROM` | 同表兩支畫面,靠 `JOB_CD` 常數分流(§5.3) |
| `OFD551` | 2 | `OFDI553` `OFDI554` | `FROM` / INNER | 定期定額契約主檔 |
| `OFD651` | 2 | `OFDI612A` `OFDI613A` | INNER JOIN | 境外電子單據主檔 |

單支獨讀的表(每張只有一支畫面讀)另列於附錄 A。

### 2.6 表名 `A` 後綴規則的成立範圍與兩個反例

§0.2 提出「帶 `A` 的是境內 / 電子交易軌、不帶 `A` 的是境外軌」。**在 `OFD6xx` 這一段完全成立**:

| 概念 | 境外軌(`OTA.Query`) | 電子交易軌(`EC.Query`) |
|---|---|---|
| 作業參數 1 到 5 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615`(`OFDI601` 到 `OFDI605` 各讀一張) | `OFD611A` 到 `OFD615A`(`IPJI620` 一支全讀) |
| 申購單據 | `OFD620` `OFD621`(`OFDI611`) | `OFD620A` `OFD621A`(`IPJI612`) |
| 贖回單據 | `OFD651` `OFD652`(`OFDI612A`) | `OFD651A` `OFD652A`(`IPJI612`) |
| 轉換單據 | `OFD651` `OFD653`(`OFDI613A`) | `OFD651A` `OFD653A`(`IPJI612`) |
| 定期定額契約 | `OFD663` `OFD664`(`OFDI614A`) | `OFD661A` `OFD662A`(`IPJI612`) |

**六組對照、零交集**,這是 §0.2 那個〔假設〕的全部依據。

**但規則不是全庫通用的,本片就有一個明確反例:**

| 反例 | 事實 | 錨點 |
|---|---|---|
| `OFD606A` | 境外軌的 10 支畫面全部 LEFT JOIN 這張**帶 `A`** 的表取基金簡稱,而全庫沒有 `OFD606` 這張表 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:130` |

所以 §0.2 的規則要縮到「**`OFD6xx` 的單據與參數表這一段成立**」,不能推廣到所有主檔。

### 2.6.1 一個會害你誤判的陷阱:別名長得跟真表一樣

`OFDI052` 看起來像是「境外軌卻讀 `OFD081A`」的反例,**其實不是**。它的 `FROM` 寫的是:

```
FROM OFD255
INNER JOIN OFD081 OFD081A ON OFD255.FUND_ID = OFD081A.FUND_ID
 LEFT JOIN OFD081 OFD081B ON OFD255.SWITCH_FUND_ID = OFD081B.FUND_ID
INNER JOIN FSK003 FSK003A ON OFD255.FUND_CURRENCY = FSK003A.CRNCY_CD
 LEFT JOIN FSK003 FSK003B ON OFD255.SWITCH_FUND_CURRENCY = FSK003B.CRNCY_CD
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:119-123`。 **`OFD081A` / `OFD081B` / `FSK003A` / `FSK003B` 是別名,不是表名**—— 而 `OFD081A` 與 `FSK003A` 剛好是真實存在的別條軌的表名。所以 `grep -rn "OFD081A"` 會在這支檔案裡命中四次,四次全是假的。

同樣的坑還有兩處:

| 檔案 | 別名 | 真表 | 錨點 |
|---|---|---|---|
| `OFDI612A_PO` | `OFD019B` | `OFD019A` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:133` |
| `OFDI553_PO` | `OFD072A` | `MYOFD072A` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:156` |

第二個更惡劣:`LEFT JOIN MYOFD072A OFD072A`,**把一張 `MYOFD` 開頭的表別名成 `OFD072A`**, 而 `OFD072A` 這個代號在別的地方是畫面名(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI072A_PO.cs`)。一個字串同時是表別名與畫面代號,做影響分析時務必先看 `FROM` 再下結論。嚴重度:低(可讀性),但**極易誤判**(附錄 E.4)。

### 2.7 主鍵與四眼欄位

| 項 | 本片 37 支查詢畫面 | `OFDM287` |
|---|---|---|
| 主鍵宣告 | **無**。結果集 xsd 沒有 `xs:key` / `msdata:PrimaryKey` | 有,走框架 `dataid` |
| 四眼 13 欄 | **0 個**,沒有任何 `ENTRYID` / `VERIFYID` / `APPROVEID` 出現在 `SELECT` | **全套**,由 `xEVAStringHelper.AllEVAColumnsForSelect("OFD283A")` 一次帶出(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:121`) |
| `dataid` | 無 | 有,`SELECT OFD283A.dataid` 是第一欄(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:77`) |

### 2.8 狀態碼(從程式反推)

本片只有三處把狀態碼翻成中文,全部寫死在 SQL 的 `CASE WHEN` 裡,**不是查代碼表**:

| 欄位 | 值域 | 中文 | 錨點 |
|---|---|---|---|
| `OFD651.EC_REDEM_PCODE` | `'0'` / `'1'` / `'2'` / `'3'` / `'4'` | 輸入 / 處理中 / 轉入 / **(空字串)** / 刪除 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:100-101` |
| `OFD256.JOB_CD` | `'1'` / `'2'` | 贖回 / 轉換(不翻中文,直接當過濾條件) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123`、`OFDI057_PO.cs:133` |
| `OFD551.STOP_CD` | 走 `COD006A` 的 `CODE_SORT = 'A8'` | 由代碼表帶 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:161-162` |

第一列的 `'3'` 對應到**空字串**(`WHEN OFD651.EC_REDEM_PCODE = '3' THEN ''`), 其餘四個值都翻成「代碼:中文」。**`'3'` 是刻意留白還是漏寫,程式裡看不出來**, `OFDI613A` 同一段 `CASE` 也照抄了這個空字串。嚴重度:低,但畫面上會出現空白欄位(附錄 E.8)。

### 2.9 與其他模組共用的表

見 §8。一句話版本:**本片沒有任何一張「自己的」表**——37 支查詢畫面讀的全部是別的模組維護的資料, 唯一有寫入語意的 `OFDM287` 改的 `OFD283A` 也同時被 `ATLAS.OFD.Query` 的 `OFDI283` 讀。

## 3. 畫面清冊

```text
[圖] 依 PO 基底與查詢條件組法分群
圖中文字:第一派 真參數化 26 支:NVL(TRIM(:P), 欄) + AddInParameter / OTA.Query 全部 24 支 / 無 PO 基底,只實作自己的介面 / IPJI613 IPJI614 / bind 變數 + F_FORMATSTRINGTOTABLE / 風險不是注入 / 是 NULL 欄位被無聲濾掉 / 第二派 混用 2 支:一半 bind 一半串字串 / IPJI612 / 1821 行,七個結果集,部分 bind / IPJI620 / 五個 cmd 併一次 LoadDataSet / 同一支內兩種寫法 / 改的人要逐段判斷 / 第三派 純字串串接 3 支:值與運算子都直接接進 SQL / OFDI607OracleDao / ID_NO 與 BF_NO 接運算子與值 / IPJI630OracleDao / ID_NO BF_NO EMAIL 各兩處,共六處 / OFDM287_PO / M 畫面,八個條件全串字串 / 第四派 全丟 SP 0 支:本片沒有任何一支呼叫預存程序 / 沒有 CommandType.StoredProcedure / 38 支掃描結果為零 / 唯一的外部程式是 TVF / F_FORMATSTRINGTOTABLE 拆多選字串 / 與 ofdi1 的 11 支全丟 SP 相反 / 本片 SQL 全部在 C# 裡 / PO 基底:本片 live 的 33 支全部無基底,BasicEVAPO 只活在註解裡 / 無基底 33 支 / 只實作 I 代號 _PO 或 I 代號 / BaseEVADaoPO 1 支 / 只有 OFDM287,因為它是 M / BasicEVAPO 15 次 / 全在 EC.Query 被註解的屍體內
```

*圖:圖 3 分群。橘框=該派的成員;紫框=該派帶來的風險;黑框=死碼或版控外。ofdi1 那片的四派分佈是「真參數化 9 / 全丟 SP 11 / 字串串接 13 / helper 2」,本片是「真參數化 26 / 混用 2 / 字串串接 3 / 全丟 SP 0」,分佈完全相反。*

### 3.1 維護 M

本片只有一支,`OFDM287`,詳見 §4。

| 代號 | 中文名(由控件標題反推) | 專案 | 六層齊不齊 | PO 基底 | 主表 | 在 csproj |
|---|---|---|---|---|---|---|
| `OFDM287` | 收益分配給付維護(推測) | `ATLAS.OFD` | **六層齊,但 Model 檔名是 `OFDM287Model.xsd.xsd`** | `BaseEVADaoPO` | `OFD283A` | 六層全在 |

### 3.2 查詢 I — `ATLAS.OTA.Query`(24 支)

**欄位說明**:PO 基底是剝掉 `//` 註解後的實際宣告;條件參數化四類取 `ofdi1.md §5.2` 的分法 (真參數化 / 全丟 SP / 直接字串串接 / 走會跳脫的 helper);結果集寫「xsd 表名(欄數)」; 匯出看 UI 有沒有設 `this.ExportGrid`;分頁全片皆無,不另列欄。

| 代號 | 中文名(反推) | PO 基底 | 主要查的表 | 條件參數化 | 結果集(欄數) | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `OFDI002` | 受益人資料變更查詢 | 無基底,`IOFDI002_PO` | `OFD105` | **真參數化**(4 bind) | `OFDI002`(13) | 有 | 六層全在 |
| `OFDI051` | 申購對帳單產製紀錄查詢 | 無基底 | `OFD223` `OFD062` `OFD081` `FSK003` | **真參數化**(5) | `OFDI051`(43) | 有 | 六層全在 |
| `OFDI052` | 贖回對帳單產製紀錄查詢 | 無基底 | `OFD255` `OFD081`×2 `FSK003`×2 | **真參數化**(5) | `OFDI052`(51) | 有 | 六層全在 |
| `OFDI055` | 申購交易通知書查詢 | 無基底 | `OFD224` `OFD062` `OFD081` `OFD012A` `BMS001A` `CTL014` `FSK003` | **真參數化**(4) | `OFDI055`(40) | 有 | 六層全在 |
| `OFDI056` | 贖回交易通知書查詢 | 無基底 | `OFD256` `OFD081` `BMS001A` `FSK003` | **真參數化**(5) | `OFDI056`(45) | 有 | 六層全在 |
| `OFDI057` | 轉換交易通知書查詢 | 無基底 | `OFD256` `OFD081` `BMS001A` `FSK003` | **真參數化**(5) | `OFDI057`(59) | 有 | 六層全在 |
| `OFDI071A` | 基金資料控制查詢(境外) | 無基底 | `OFD309` `OFD062` `OFD081` `SWPRODUCTSDETAIL`(別名 `PROG`) | **真參數化**(5) | `OFDI071A`(10) | 有 | 六層全在 |
| `OFDI072B` | 申贖控制碼查詢(境外) | 無基底 | `OFD303` `OFD062` `OFD081` | **真參數化**(11) | `OFDI072B`(12) | 有 | 六層全在 |
| `OFDI283A` | 收益分配明細查詢(境外) | 無基底 | `OFD281` `OFD283` `OFD062` `OFD081` `BMS001A` `OFD013` `OFD020V` `FSK003` | **真參數化**(9) | `OFDI283A`(64) | 有 | 六層全在 |
| `OFDI531` | 所得認列查詢 | 無基底 | `OFD535` `OFD536` `OFDV531` `OFD081` `BMS001A` `FSK003` | **真參數化**(4) | `OFDI531`(38) | 有 | 六層全在 |
| `OFDI553` | 定期定額契約查詢 | 無基底 | `OFD551` `OFD552` `OFD081` `BMS001A` `COD006A` `COD009` `MYOFD072A` `OFD019A` `OFD068A` `OFD199` `FSK003` `OFD062` `OFD019A` | **真參數化**(11),但 **`AND` / `OR` 缺括號**(§5.7) | `OFDI553`(50) | 有 | 六層全在 |
| `OFDI554` | 定期定額契約異動查詢 | 無基底 | `OFD554` `OFD555` `OFD551` `OFD081` `BMS001A` `COD006A` `OFD199` `FSK003` | **真參數化**(13) | `OFDI554`(44) | 有 | 六層全在 |
| **`OFDI563`** | 授權申請查詢 | 無基底 | `OFD563` `BMS001A` `OFD019A` | **真參數化**(3) | **`OFDI562`(25),借用** | 有 | **只有四層,無 Model / View xsd** |
| `OFDI564` | 匯款處理查詢 | 無基底 | `OFD564` `BMS001A` `OFD019A` | **真參數化**(3) | `OFDI564`(13) | 有 | 六層全在 |
| `OFDI601` | 基金交易付款方式參數查詢 | 無基底 | `OFD611` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI601`(10) | 有 | 六層全在 |
| `OFDI602` | 基金作業參數查詢 2 | 無基底 | `OFD612` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI602`(9) | 有 | 六層全在 |
| `OFDI603` | 基金作業參數查詢 3 | 無基底 | `OFD613` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI603`(9) | 有 | 六層全在 |
| `OFDI604` | 基金作業參數查詢 4 | 無基底 | `OFD614` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI604`(8) | 有 | 六層全在 |
| `OFDI605` | 基金作業參數查詢 5 | 無基底 | `OFD615` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI605`(8) | 有 | 六層全在 |
| `OFDI611` | 境外申購單據查詢 | 無基底 | `OFD620` `OFD621` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD012` `OFD019A` `OFD199` `FSK003` | **真參數化**(6) | `OFDI611`(61) | 有 | 六層全在 |
| `OFDI612A` | 境外買回(贖回)單據查詢 | 無基底 | `OFD651` `OFD652` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD019A`×2 `FSK003` | **真參數化**(6) | `OFDI612A`(61) | 有 | 六層全在 |
| `OFDI613A` | 境外轉換單據查詢 | 無基底 | `OFD651` `OFD653` `OFD601` `OFD606A` `OFD062` `OFD081` `FSK003` | **真參數化**(6) | `OFDI613A`(67) | 有 | 六層全在 |
| `OFDI614A` | 境外定期定額契約查詢 | 無基底 | `OFD663` `OFD664` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD199` `FSK003` | **真參數化**(6) | `OFDI614A`(50) | 有 | 六層全在 |
| `OFDI615` | 境外定期定額契約異動查詢 | 無基底 | `OFD666` `OFD667` `OFD601` `OFD606A` `OFD081` `OFD199` | **真參數化**(6) | `OFDI615`(61) | 有 | 六層全在 |

**這 24 支的一致性高到不像同一個系統的其他部分**:

| 面向 | 24 支的狀況 |
|---|---|
| PO 基底 | 24 / 24 無基底,只實作 `I<代號>_PO` |
| PO 方法簽名 | 24 / 24 是 `T GetData<T>(T mModel, params object[] args)` |
| 連線 | 24 / 24 `new Database("TA", DbServerType.Oracle)` + `[PODbType(DbServerType.Oracle)]` |
| 條件組法 | 24 / 24 真參數化,**零字串串接** |
| 取數 | 24 / 24 一次 `LoadDataSet`,單一結果集 |
| 結果回報 | 24 / 24 `AddResultRow(筆數>0, 筆數, "")`,**訊息一律空字串** |
| 例外處理 | 24 / 24 `AddResultRow(false, 0, ex.Message)` **接著** `CommonExceptionBlocker.HandleBusinessException(ex)` |
| UI 基底 | 24 / 24 `xOneStepProcessForm` |
| 匯出 | 24 / 24 設 `this.ExportGrid = this.ugrdResult` |
| 分頁 | **0 / 24**,全部一次撈完 |
| 作者與日期 | 檔頭 `Original author` 只有 `Jye`(8 支)與 `Kendra`(16 支),`Created on` 落在 2023/02 到 2023/09 |

最後一列是理解這一片的關鍵:**這 24 支是 2023 年同一批人、同一份樣板、七個月內一次做完的**, 所以缺陷也是整批的——不是零星的手滑,是樣板本身的問題(§5.1)。

### 3.3 查詢 I — `ATLAS.EC.Query`(13 支:7 活 6 死)

| 代號 | 中文名(反推) | PO 檔 | PO 基底 | 主要查的表 | 條件參數化 | 結果集(表名) | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|---|
| `IPJI612` | 網路交易明細查詢(含退休試算) | `IPJI612OracleDao.cs`(**1821 行**) | 無基底,`IIPJI612` | `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` `OFD656A` `OFD657A` `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` `OFD601` `OFD601CHG` `OFD304A` `OFD138A` `OFD199A` `OFD020A` `OFD020V` `OFD081A` `BMS001A` `COD006` `CTL014` | **混用**(36 bind + 部分字串) | **`IPJI621_Master` 等 7 張 + `OFD673A`** | 無 | 六層在,**Model 叫 `IPJI612_9iModel.xsd`** |
| `IPJI613` | 基金設定查詢 | `IPJI613OracleDao.cs` | 無基底 | `OFD681A` `OFD682A` `OFD683A` `OFD601` `V_FUND` | **真參數化**(4) | `IPJI613` | 無 | 六層全在 |
| `IPJI614` | 拋轉資料查詢 | `IPJI614OracleDao.cs` | 無基底 | `OFD618A` `OFD081A` `CTL014` | **真參數化**(3)+ `F_FORMATSTRINGTOTABLE` TVF | **`OFD618A`**(實體表名) | 無 | 六層全在 |
| `IPJI620` | 網路交易彙總查詢(五類) | `IPJI620OracleDao.cs` | 無基底 | `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` `OFD081A` | **混用**(24 bind) | `IPJI620_Allot` `_Redem` `_RSP` `_BMS_CHG` `_Switch`(5 張) | 無 | 六層全在 |
| `IPJI630` | 網路開戶紀錄查詢 | `IPJI630OracleDao.cs` | 無基底 | `OFD601` `OFD601CHG` `OFD607A` | **直接字串串接**(6 處,0 bind) | `IPJI630_Master` + 裸 `DataSet` 的 `"OFD601"` | 無 | 六層在,**Model 叫 `IPJI630_9iModel.xsd`** |
| `OFDI607` | 受益人資料變更軌跡查詢 | `OFDI607OracleDao.cs` | 無基底,`IOFDI607` | `LOG602` `OFD601` `OFD607A` `CTL014` | **直接字串串接**(2 處 + 2 處日期,0 bind) | `OFDI607` | 無 | 六層全在 |
| `OFDI608` | 登入與密碼紀錄查詢 | `OFDI608OracleDao.cs` | 無基底,`IOFDI608` | `LOG600` `LOG601` `OFD601` `CTL014`(三次子查詢) | **直接字串串接**(2 處 + 2 處日期,0 bind) | `OFDI608` | 有 | 六層全在 |
| **`OFDI606`** | 受益人資料異動查詢(網路) | `MSSQL/OFDI606_PO.cs` | **整檔註解**(原 `BasicEVAPO`) | — | — | `OFDI606` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI609`** | 網路贖回查詢 | `MSSQL/OFDI609_PO.cs` | **整檔註解** | — | — | `OFDI609` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI610`** | 網路贖回查詢(2) | `MSSQL/OFDI610_PO.cs` | **整檔註解** | — | — | `OFDI610` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI612`** | 網路變更生效查詢 | `MSSQL/OFDI612_PO.cs` | **整檔註解** | — | — | `OFDI612` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI613`** | 網路開戶申請查詢 | `MSSQL/OFDI613_PO.cs` | **整檔註解** | — | — | `OFDI613` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI614`** | 網路紀錄查詢 | `MSSQL/OFDI614_PO.cs` | **整檔註解** | — | — | `OFDI614` | 有 | **UI / Pxy / Ctl 不在 csproj** |

**注意兩個不對稱**:

1. 六支死畫面的 **PO 檔仍在 `QueryPO.EC.csproj` 上**(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`), **Model / View xsd 也仍在**,只有 UI / Pxy / Ctl 三層退出。也就是說:編譯產出的 DLL 裡**還帶著這六支的 typed DataSet**,只是沒人用。

2. 五支活的 `IPJI6xx` **一支都沒有匯出**,而六支死的全部有匯出。〔假設〕是 `IPJI6xx` 這批比較新、改走畫面內的明細彈窗(`IPJI612_P0` 到 `IPJI612_P5` 六個 `PopupForm`), 依據是 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI612_P0.cs:17` 起那六個彈窗類別。

### 3.4 批次 B

**本片無 B 畫面。** 原因:切片依據是 `*.Query` 專案,而 `*.Query` 專案底下**只放 I 畫面**—— `Dev/ATLAS.OTA.Query` 與 `Dev/ATLAS.EC.Query` 兩棵樹內沒有任何 `*B[0-9]*` 代號的檔。境外軌的批次在 `Dev/ATLAS.OTA`,不在本片。

### 3.5 報表 R

**本片無 R 畫面。** 同上,報表在 `Dev/ATLAS.OTA.Report` 與 `Dev/ATLAS.EC.Report`, 本片 38 支沒有任何一支產 `.rpt` 或呼叫 Report Service。

### 3.6 條件參數化四派的分佈(必答問題 4 的答案)

`ofdi1.md` 前一片 35 支分四派:真參數化 9 / 全丟 SP 11 / 直接字串串接 13 / 走會跳脫的 helper 2。 **本片 38 支的分佈完全相反:**

| 派別 | 支數 | 是誰 |
|---|---|---|
| **真參數化** | **26** | `OTA.Query` 全部 24 支(含 `OFDI563`)+ `IPJI613` `IPJI614` |
| **混用**(同一支內 bind 與串接並存) | **2** | `IPJI612` `IPJI620` |
| **直接字串串接** | **4** | `IPJI630` `OFDI607` `OFDI608` **`OFDM287`**(唯一的 M 畫面,§4) |
| **全丟 SP** | **0** | 無。本片 38 支沒有任何 `CommandType.StoredProcedure`,也沒有任何 `EXEC` / `CALL` |
| **走會跳脫的 helper** | **0** | 無。`EVAStringHelper.AddParam` 在本片出現 **0 次** |
| (不適用)死碼 | 6 | `OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` |

26 + 2 + 4 = 32,正好是本片 live 的 32 支(24 + 7 + `OFDM287`);另外 6 支是死碼,不分派。 **四支純串接的那一組就是本片全部的 SQL 注入風險面**,三支在 `EC.Query`、一支是 `OFDM287`。

**關於 `EVAStringHelper.AddParam` 的兩個多載**:任務指名要看的那個坑(4 參數版真參數化、3 參數版 `IN` 分支完全不跳脫,`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:346`,`IN` 分支在 `:373-374`) **在本片一次都沒出現**。本片 `OTA.Query` 用的是同一個類別的另一個方法 `SQLHelper.EVAStringHelper.GetParamValue(model, "欄名")`——**它只負責從 `model.Utility.Parameters` 撈字串值, 不組 SQL**,撈出來的值一律交給 `dbTA.AddInParameter` 當 bind 變數 (例:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:146-151`)。 **所以那個坑本片踩不到。** 真正的風險改成 §5.1 那個 `NVL` 樣板。

### 3.7 PO 基底統計(必答問題:幾支繼承 `BasicEVAPO`)

| 基底 | live 支數 | 說明 |
|---|---|---|
| 無基底 | **31** | `OTA.Query` 24 + `EC.Query` live 7 |
| `BaseEVADaoPO` | **1** | 只有 `OFDM287`,因為它是 M 畫面 |
| `BasicEVAPO` | **0 支 live** | 但**檔案內出現 15 次**,全部在 `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/` 那六支死畫面加另外九支同批屍體的註解裡 |
| (無 PO) | 6 | 六支死畫面 |

`ofdi1.md` 記的「繼承 `BasicEVAPO` 連查詢都 NRE」這條缺陷,**在本片不會發作**—— 唯一那 15 個 `BasicEVAPO` 全被 `//` 蓋住了。但反過來說:**如果有人把那些 PO 解除註解重新啟用,15 支會一次全炸**。

## 4. 維護畫面(M)— 本片只有一支

### 4.1 `OFDM287` — 全庫最後一支沒被任何模組篇提到的 M 畫面

必答問題 5 的答案。先講結論:**它不是死的,它是活的、六層齊全、全部在 csproj、有完整四眼, 前 24 篇沒碰到它純粹是因為它的 Model 檔名多了一個 `.xsd`。**

#### 4.1.1 為什麼前面 24 篇都漏掉它

`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/` 底下,它的 Model 叫:

```
OFDM287Model.xsd.xsd
OFDM287Model.xsd.xsc
OFDM287Model.xsd.xss
OFDM287Model.xsd.Designer.cs
```

**多了一層 `.xsd`**。全庫其他畫面一律是 `<代號>Model.xsd`。掃描器用 `*Model.xsd` 這個樣式收 Model,`OFDM287Model.xsd.xsd` 不符合,於是被判成「有 View 沒有 Model」—— `architecture.md` 那份清單正是這樣記的:**它被列在「5 支只有 View 沒有 Model」那一組**, 跟 `CMM_BFTypeList` `OFDI701` 等擺在一起,當成「改名沒改乾淨」的殘骸,**所以沒有人再回頭查它**。

實際上 View 那邊是正常的 `OFDM287View.xsd`(`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/OFDM287View.xsd`), csproj 也把 `OFDM287Model.xsd.xsd` 正常收了 (`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/DataEntity.OFD8.csproj:185-190,422-431`), 所以它編得出來、跑得動。**這是一個檔名 typo 造成的文件盲點,不是程式缺陷**——但代價是這支畫面到今天為止沒有任何文件。

#### 4.1.2 六層與基本事實

| 層 | 檔 | 關鍵事實 |
|---|---|---|
| UI | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:20` | `public partial class OFDM287 : xMaintainForm`,`this.TabPages = 2`(`:87`) |
| FormProxy | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM287_Pxy.cs:12` | `Basic_Pxy`,只覆寫 `Modify` 與 `Query` 兩個動作 |
| Control | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:13` | `BaseController`,`ModifyData` / `GetData` / `GetMaintainData` 三個方法 |
| PO | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:25` | **`BaseEVADaoPO`**,`[PODbType(DbServerType.Oracle)]`,`Database("TA", DbServerType.Oracle)` |
| Model | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM287Model.xsd.xsd` | 根節點是實體表形狀,不是結果集 |
| View | `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/OFDM287View.xsd` | 與 Model 同構 |

`MasterTable` 宣告在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:32`:

```
this.MasterTable = new xTableMapping("OFD283A", "OFDM287"); //主檔資料
```

**沒有 `DetailTable`**——單表維護。

#### 4.1.3 它管什麼(推測)

主表 `OFD283A` 是**境內分戶軌的收益分配(配息)給付明細**。SQL 撈的欄位說明了業務: `BAL_UNIT`(結餘單位)、`TOTAL_ASSIGN_AMT`(分配總額)、`GET_STATUS`(發放進度)、 `GET_WAY`(給付方式)、`BANK_BRH` / `REMIT_ACC_NO`(匯款帳戶)、 `SWITCH_FUND_ID` / `SWITCH_DATE` / `SWITCH_FEE_RATE` / `SWITCH_FEE` / `SWITCH_AMT`(配息轉申購)、 `POST_FEE` / `REMIT_FEE`(郵資與匯費,各拆公司負擔與銀行負擔)、`TOTAL_TAX_AMT`(扣繳稅額)、 `MAIL_ZIP` / `MAIL_ADDR`(寄送地址)、`DIV_PAY_DESK`(給付櫃檯) (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:77-121`)。

**與本片 `OFDI283A` 的關係是最容易搞混的一點**:

|  | `OFDM287`(本節) | `OFDI283A`(§5) |
|---|---|---|
| 專案 | `Dev/ATLAS.OFD`(境內分戶軌) | `Dev/ATLAS.OTA.Query`(境外綜合帳戶軌) |
| 主表 | **`OFD283A`** | **`OFD283`** |
| 搭配表 | `OFD281A` `OFD081V` `OFD020V` `BMS001A` | `OFD281` `OFD081` `OFD013` `OFD020V` `BMS001A` `FSK003` `OFD062` |
| 型別 | M,可改 | I,唯讀 |
| 四眼 | 有 | 無 |

**畫面代號 `OFDI283A` 的 `A` 跟表名 `OFD283A` 沒有任何關係**,`OFDI283A` 查的是不帶 `A` 的 `OFD283`。這是 §5.6 那份 `A` 後綴成因分析的核心證據之一。

#### 4.1.4 四眼與階段動作

`OFDM287_PO` 只掛三個事件,**全部是「取數前組 SQL」,沒有任何寫入階段的附加動作**:

| 事件 | 用途 | 錨點 |
|---|---|---|
| `BeforeSelect` | 查詢頁取數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:33,53-66` |
| `BeforeGetMaintainData` | 維護頁取單筆 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:34,276-289` |
| `BeforeGetToDoData` | 待辦(四眼待覆核清單)取數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:35,290-303` |

三個事件都呼叫同一個 `BuildMasterSQLString(model, isToDoString)`; 差別只在 `BeforeGetToDoData` 傳 `true`,多接一段 `xTableHelper.AppendToDoString("OFD283A", model)` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:266`)。四眼 13 欄由 `xEVAStringHelper.AllEVAColumnsForSelect("OFD283A")` 一次帶進 `SELECT` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:122`)。 `xEVAStringHelper` / `xTableHelper` / `BaseEVADaoPO` 的實作**無原始碼,從呼叫端反推**。

**沒有 `BeforeAdd` / `AfterVerify` / `AfterApprove` / `AfterReject`**—— 寫回完全交給 `BaseEVADaoPO.Update`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:52` 把它當委派丟給框架), PO 自己沒有一行 `UPDATE` 語句。

#### 4.1.5 它實際上只能改一個欄位

畫面上擺了二十幾個控件,但按下「修改」時只有一個欄位被搬回資料列:

```
private void OFDM287_BeforeModifyButtonClicked(object sender, CancelEventArgs e)
{
    OFDM287View.OFDM287Row Row = ((OFDM287ViewVDB)this.ProcessVDB).UIView.OFDM287[0];
    Row.MEMO = this.utxtMEMO.Text;
}
```

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253`。其餘欄位在 `OFDM287_ModifyDataLoad` 是**單向從資料列填進控件** (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:174-231`),沒有反向搬回。 `OFDM287_Ctl.ModifyData` 的 XML 註解也直說是「修改受益分配**備註**」 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:46`)。

**所以這支 M 畫面的實際能力是:查配息給付明細 + 改備註,其他都是唯讀展示。** 使用者若在畫面上改了金額或帳號欄位再按修改,**不會存進去,也不會有任何提示**—— 結果類型:**過濾(無提示)**。嚴重度:中(附錄 E.9)。

#### 4.1.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 「年度+期別」「分配基準日」「受益人 ID」「戶號」四組必須擇一輸入 | 四組全空 | **阻擋**(`e.Cancel = true` + `ValidateErrList.Show()`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:124-138` |
| 進維護頁 | 停用刪除鈕 | 一律 | 記錄不擋(功能關閉) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:176` |
| 進新增頁 | 停用新增鈕 | 一律 | 記錄不擋(**等於不能新增**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:233-236` |
| 載入維護頁 | `GET_WAY == "3"`(配息轉申購)才顯示轉換相關金額,否則清空 | 給付方式不是 `'3'` | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:200-212` |
| 按修改前 | 只把 `MEMO` 搬回資料列 | 一律 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253` |
| 組查詢 SQL | 八個條件逐一 `if Rows.Contains(...)`,有才加 | 條件沒填 | 過濾(無提示,合理) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:136-247` |

`GET_WAY == "3"` 這個常數寫死在 UI,**沒有走 `MappingCode`**; 同一支畫面的下拉選單卻是走 `GetDropDownDataSrc("380")` 取的 (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:96`)。也就是說:**下拉的值域可以在代碼表改,但「哪個值代表配息轉申購」寫死在程式裡**。代碼表改了而程式沒改,畫面就會停止顯示轉換金額。嚴重度:中(附錄 E.10)。

#### 4.1.7 `OFDM287` 是本片唯一的字串串接 SQL

八個查詢條件全部長這個樣子:

```
strSQL += " And OFD283A." + Row.Name + " = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:143`,另 15 處散在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:147-262`。 **`Row.Name` 與 `Row.Value` 都直接接進 SQL,沒有任何跳脫**:

| 面向 | 風險 |
|---|---|
| `Row.Value` 直接串 | 畫面輸入 `' OR '1'='1` 可改變語意。但**欄位來源受限**——`Row.Value` 只從八個固定控件填入(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:140-172`),其中六個是遮罩 / 數值 / 日期控件,只有 `custID_NO` 與 `custBF_NO` 是文字。嚴重度:**中高** |
| `Row.Name` 直接串 | `Row.Name` 是程式寫死的八個常數,不是使用者輸入。嚴重度:低 |
| `LIKE` 分支 | `" Like " + "'" + Row.Value + "%'"`,樣式字元 `%` `_` 不跳脫,使用者打 `%` 會變萬用字元(`:147`) |

**與同專案的其他 M 畫面比,這支不算特例**——`ofdi1.md` 與 `ofd123.md` 都記過同樣的樣板。放在本片特別刺眼的原因是:**它旁邊那 24 支 2023 年新寫的境外軌查詢是 100% 參數化的**, 一個專案內兩種年代的寫法差距在這裡看得最清楚。

#### 4.1.8 一個沒被用到的旗標

`private bool CanSave = true;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:28`) 在整支檔案裡**只出現這一次**,沒有任何地方讀它或寫它。〔假設〕是原本規劃過「某些狀態不可存檔」的卡控後來拿掉了,依據是欄位名與初值; 但**程式裡找不到那條卡控,所以不能當成現行行為**。嚴重度:低(死碼,附錄 E.12)。

## 5. 查詢畫面(I)

```text
[圖] OFDI553 的查詢流程與三類過濾點
圖中文字:OFDI553 定期定額契約查詢:一支畫面九張表,七個過濾點 / UI xOneStepProcessForm / 收 11 個條件欄位 / Ctl OFDI553_Ctl / TransferVDBHelper 逐表搬 / PO OFDI553_PO / 一段 SQL,11 個 bind 變數 / 過濾點一 INNER JOIN:對不到就整列消失,無提示 / INNER JOIN OFD552 / 契約沒有明細列就看不到契約 / INNER JOIN OFD081 / 基金主檔沒這檔就看不到 / INNER JOIN BMS001A / 受益人主檔對不到就看不到 / 過濾點二 NVL 樣板:欄位本身是 NULL 時,空條件也會濾掉 / AGENT_ID 是 NULL / NULL = NVL(NULL, NULL) 得 UNKNOWN / AGENT_CODE 是 NULL / 同上,該筆契約永遠查不到 / 例外 SUB_BANK_CODE / 另外補了 OR 參數 IS NULL,是對的 / 過濾點三 AND 與 OR 缺括號:最後一行的 OR 把整個 WHERE 吃掉 / WHERE 1=1 AND 條件群 / 前面十個條件 / OR 契約書號 BETWEEN 起 迄 / 沒有外層括號 / 填了契約書號區間 / 基金公司 基金 日期 戶號全部失效 / 結果:查得到別的基金公司 別的客戶的契約,而畫面不會說 / 嚴重度 高 / 越權看到資料,且無任何提示 / 修法 / 把最後一個 OR 條件整段包進括號 / 孿生畫面 OFDI554 / 沒有這個 OR,所以沒中招
```

*圖:圖 4 本片最重的一支。三類過濾點都屬於「過濾(無提示)」:INNER JOIN 讓對不到的資料無聲消失、NVL 樣板讓 NULL 欄位的資料列永遠查不到、AND 與 OR 缺括號則反過來讓不該出現的資料出現。前兩者使用者會以為「真的沒有」,第三者使用者根本不會發現。*

本章是本片主體。**讀法**:§5.1 是全片共用的樣板與它的地雷,不讀後面看不懂; §5.2 講條件怎麼從畫面走到 SQL;§5.3 到 §5.4 用表格帶過分群; §5.5 到 §5.9 是五個需要深寫的主題。

### 5.1 `OTA.Query` 24 支的共用樣板,以及它內建的過濾陷阱

#### 5.1.1 樣板長什麼樣

24 支 PO 是同一份樣板長出來的,骨架一模一樣:

```
public T GetData<T>(T mModel, params object[] args)
{
    OFDI612AModelVDB model = mModel as OFDI612AModelVDB;
    int i = 0;
    try
    {
        string strSQL = string.Empty;
        strSQL += " SELECT ... ";            // 逐行 += ,每行接 Environment.NewLine
        strSQL += " FROM ... JOIN ... ";
        strSQL += " WHERE 1 = 1 ";
        strSQL += " AND 欄 = NVL(TRIM(:P), 欄) ";
        strSQL += " ORDER BY ... ";
        using (DbCommand cmd = dbTA.GetSqlStringCommand(strSQL))
        {
            dbTA.AddInParameter(cmd, "P", OracleDbType.Varchar2,
                SQLHelper.EVAStringHelper.GetParamValue(model, "P"));
            dbTA.LoadDataSet(cmd, model.DataEntity, model.DataEntity.OFDI612A.TableName);
        }
        i = model.DataEntity.OFDI612A.Rows.Count;
        model.Utility.Result.Clear();
        if (i > 0) model.Utility.Result.AddResultRow(true, i, "");
        else       model.Utility.Result.AddResultRow(false, 0, "");
    }
    catch (Exception ex)
    {
        model.Utility.Result.Clear();
        model.Utility.Result.AddResultRow(false, 0, ex.Message);
        CommonExceptionBlocker.HandleBusinessException(ex);
    }
    return mModel;
}
```

樣本:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:55-177`。 **這份樣板本身是好的**:SQL 全參數化、`using` 有包、例外有處理、筆數有回報。問題出在那一行條件的寫法。

#### 5.1.2 地雷:`欄 = NVL(TRIM(:P), 欄)` 遇到 NULL 欄位會無聲吃掉整列

設計意圖很清楚:**參數沒填就不過濾**。`TRIM(:P)` 在 Oracle 裡空字串等於 `NULL`, `NVL(NULL, 欄)` 回傳欄位自己,於是條件變成 `欄 = 欄` ——恆真。

**但只在欄位有值時恆真。** 當那一列的該欄位是 `NULL`:

| 情境 | 條件展開 | Oracle 三值邏輯結果 | 該列 |
|---|---|---|---|
| 參數有填、欄位有值 | `'A' = 'A'` | TRUE / FALSE | 正確過濾 |
| **參數沒填、欄位有值** | `欄 = 欄` | TRUE | 留下(正確) |
| **參數沒填、欄位是 NULL** | `NULL = NVL(NULL, NULL)` 即 `NULL = NULL` | **UNKNOWN** | **被濾掉** |
| 參數有填、欄位是 NULL | `NULL = 'A'` | UNKNOWN | 被濾掉(正確) |

**第三列就是地雷**。使用者什麼條件都不填按查詢,預期是「全部資料」, 實際拿到的是「**該欄位不為 NULL 的資料**」,而畫面**完全不會提示**—— `AddResultRow(false, 0, "")` 的訊息是空字串,只會顯示框架預設的「查無資料」。

卡控結果類型:**過濾(無提示)**。

#### 5.1.3 中招範圍

`OTA.Query` 24 支全部用這個樣板,`EC.Query` 的 `IPJI613` 也用(`NVL(:ID_NO, OFD601.ID_NO)`, `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:81-82`)。但**不是每個條件都會發作**——只有「該欄位在資料上可能為 NULL」時才會。以下列出風險較高的幾個:

| 畫面 | 條件欄 | 為什麼可能是 NULL | 錨點 |
|---|---|---|---|
| `OFDI553` | `OFD551.AGENT_ID` `OFD551.AGENT_CODE` | 直銷件沒有銷售機構 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:169-170` |
| `OFDI553` | `OFD551.BF_NO` | 契約尚未綁定戶號時 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:171` |
| `OFDI554` | `OFD555.RSP_CHG_NO` | 主檔異動未產生明細時 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:161` |
| `OFDI072B` | `OFD303` 的八個控制碼欄 | **八個條件全部套這個樣板**,任一個是 NULL 就整列消失 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI072B_PO.cs:82-92` |
| `OFDI283A` | `OFD281.DIVIDEND_DATE` `OFD281.PAY_DATE` | 配息尚未發放時這兩個日期是空的 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:168-169` |
| `OFDI071A` | `OFD309.PROG_CODE` `OFD309.UPD_USER` | 系統寫入的控制列沒有更新人員 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI071A_PO.cs:84-85` |

**`OFDI072B` 是最嚴重的一支**:它有八個控制碼條件,只要資料列上任何一個控制碼欄位是 `NULL`, 那一列在**任何查詢條件下都查不到**——包括什麼都不填。 `OFDI283A` 的 `DIVIDEND_DATE` / `PAY_DATE` 次之:**還沒發放的配息一律查不到**, 而「查還沒發放的配息」正是這支畫面最可能的用途。

#### 5.1.4 樣板作者自己知道這件事,但只修了三個地方

同一批程式裡有三處寫法不同,證明作者遇過這個問題:

| 寫法 | 出處 | 效果 |
|---|---|---|
| `AND (欄 = NVL(TRIM(:P), 欄) OR :P IS NULL)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`(`SUB_BANK_CODE`) | **正確**。參數沒填就整條為真,不管欄位是不是 NULL |
| `AND NVL(TRIM(欄), '19000101') BETWEEN NVL(TRIM(:ST), '19000101') AND NVL(TRIM(:END), '29991231')` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:164-165` | **正確**。把欄位的 NULL 也補成預設值 |
| `AND NVL(TRIM(欄), 'N') = :P` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:171` | **正確**,但這條是必填條件,沒有「不過濾」的選項 |

**三處修正全部集中在 `OFDI553` / `OFDI554` 這兩支**(2023/02/24 由 `Jye` 寫), 其餘 22 支沒有任何一處。〔假設〕是這兩支在測試時被抓到,修完沒有回頭套到別支; 依據是修正寫法有三種不同版本,不像是樣板本來就有的。

#### 5.1.5 日期區間的 `BETWEEN` 有同樣的問題但表現不同

日期條件的樣板是:

```
AND 欄 BETWEEN NVL(TRIM(:ST), '19000101') AND NVL(TRIM(:END), '29991231')
```

參數沒填時展開成 `欄 BETWEEN '19000101' AND '29991231'`——**看起來安全,但欄位是 `NULL` 時仍然是 UNKNOWN**, 該列照樣被濾掉。而且這裡多一層問題:**`'19000101'` 與 `'29991231'` 是字串比較**, 所以欄位必須是 `YYYYMMDD` 格式的字串才對得起來。本片的日期欄確實都是字串(`OFD651.APPLY_DATE` 在 `SELECT` 裡要 `TO_DATE(..., 'YYYYMMDD')` 才轉成日期, `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:70`),**所以目前是對的**。但**只要有人把某張表的日期欄改成 `DATE` 型別,這個 `BETWEEN` 會變成隱式轉換**, 結果是全表掃描加上不可預期的比較。屬於「現在沒壞但很脆」的地方。

### 5.2 條件怎麼從畫面走到 SQL

三條軌三種走法,**沒有一條走 SP**:

| 軌 | 畫面端 | 中繼 | PO 端 |
|---|---|---|---|
| `OTA.Query` 24 支 | `QueryVDB.Util.Parameters.AddParametersRow("欄名", SQLOperator.Equal, 值)` | `model.Utility.Parameters` 這個 key-value 袋 | `SQLHelper.EVAStringHelper.GetParamValue(model, "欄名")` 撈出字串 → `dbTA.AddInParameter` 當 bind |
| `EC.Query` 新的(`IPJI613` `IPJI614` `IPJI620`) | 同上 | 同上 | `vdb.Utility.Parameters.Rows.Find(...)` → `db.AddInParameter` |
| `EC.Query` 舊的(`IPJI630` `OFDI607` `OFDI608`) | 同上 | 同上 | `vdb.Utility.Parameters.FindByName("X").Value` **直接串進 SQL 字串** |

**關鍵差別在最後一欄**。前兩種值進 bind 變數,運算子寫死在 SQL; 第三種**連運算子都是從畫面帶過來的**:

```
strSQL += " AND OFD601.ID_NO "
        + vdb.Utility.Parameters.FindByName("ID_NO").Opeartor
        + "'" + vdb.Utility.Parameters.FindByName("ID_NO").Value + "'";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102`。 (`Opeartor` 是框架的拼字,不是筆誤。)詳見 §5.9。

**`EVAStringHelper.AddParam` 那兩個多載在本片一次都沒出現。** `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:198` 是 4 參數版(真參數化)、 `:346` 是 3 參數版(字串串接,`IN` 分支在 `:373-374` 直接 `"(" + strValue + ")"`,完全不跳脫)。本片用的是同一個類別的 `GetParamValue`(`:387`),**它只撈值不組 SQL**,所以那個坑踩不到。

### 5.3 分群帶過(一)— 對帳單與通知書五支

| 畫面 | 查什麼 | 主表 | 條件 | 值得注意 |
|---|---|---|---|---|
| `OFDI051` | 申購對帳單產製紀錄 | `OFD223` | 基金公司 / 基金 / 申購書號 / 更新日區間 | 用 `OFD062.FH_CD` 篩基金公司 |
| `OFDI052` | 贖回對帳單產製紀錄 | `OFD255` | 基金公司 / 基金 / 贖回書號 / 更新日區間 | **用 `OFD081` 的別名 `OFD081A` 篩**,與 `OFDI051` 不同路 |
| `OFDI055` | 申購交易通知書 | `OFD224` | 基金公司 / 基金 / 申購日 / 申購書號 | 唯一讀 `OFD012A` 與 `CTL014` 的一支 |
| `OFDI056` | 贖回交易通知書 | `OFD256` | 基金公司 / 基金 / 贖回書號 / 贖回日區間 | **SQL 寫死 `AND OFD256.JOB_CD = '1'`** |
| `OFDI057` | 轉換交易通知書 | `OFD256` | 同上,但是轉出日 | **SQL 寫死 `AND OFD256.JOB_CD = '2'`** |

`OFDI056` 與 `OFDI057` 是同一張表的兩支孿生畫面,差別只有那個常數 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123` 與 `OFDI057_PO.cs:133`) 與結果欄數(45 對 59)。**`JOB_CD` 的值域沒有走代碼表,兩支各寫死一個字元**; 如果之後多一種 `JOB_CD`,要靠人記得這裡有兩支畫面。嚴重度:低(附錄 E.6)。

**這兩支還是全片唯二沒有 `ORDER BY` 的畫面** (`grep -c "ORDER BY"` 對 `OFDI056_PO.cs` 與 `OFDI057_PO.cs` 都是 0)。 Oracle 不保證回傳順序,所以同一個查詢兩次執行的列序可能不同; 使用者匯出 Excel 對帳時會以為資料變了。嚴重度:低。

### 5.4 分群帶過(二)— 參數主檔、客戶資料、定期定額

**參數主檔五支**(`OFDI601` 到 `OFDI605`)是全片最單純的一組,五支結構完全相同:

| 畫面 | 主表 | 結果欄數 | `ORDER BY` |
|---|---|---|---|
| `OFDI601` | `OFD611` | 10 | `FUND_ID, CTL_DATE, TRAN_PAY_WAY` |
| `OFDI602` | `OFD612` | 9 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI603` | `OFD613` | 9 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI604` | `OFD614` | 8 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI605` | `OFD615` | 8 | `FH_CD, FUND_ID, CTL_DATE` |

五支的條件一模一樣(基金公司 / 基金 / 資料控制日區間),各 4 個 bind, `FROM OFD61x LEFT JOIN OFD062 LEFT JOIN OFD606A` 的形狀也一樣 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:74-76`)。 `OFDI601` 的 `ORDER BY` 多了 `TRAN_PAY_WAY` 是唯一的差異。 **這五張表 `OFD611` 到 `OFD615` 在電子交易軌的對應是 `OFD611A` 到 `OFD615A`,由 `IPJI620` 一支全讀**(§5.8)。

**客戶與帳戶四支**:

| 畫面 | 查什麼 | 主表 | 條件數 | 值得注意 |
|---|---|---|---|---|
| `OFDI002` | 受益人資料變更紀錄 | `OFD105` | 3 | **全片唯一單表查詢**,沒有任何 JOIN |
| `OFDI071A` | 基金資料控制紀錄(境外) | `OFD309` | 5 | 境內版是 `OFDI071` 查 `OFD309A` |
| `OFDI072B` | 申贖控制碼(境外) | `OFD303` | **8** | 境內版是 `OFDI072A` 查 `OFD303A`;八個條件全套 NVL 樣板(§5.1.3) |
| `OFDI283A` | 收益分配明細(境外) | `OFD281` `OFD283` | 9 | 境內版是 `OFDI283` 查 `OFD281A` `OFD283A`;`OFD283A` 由 `OFDM287` 維護(§4) |

`OFDI283A` 還有一條與眾不同的條件:

```
AND OFD281.RECORD_DATE LIKE TRIM(:YEAR)||'%'
AND OFD281.RECORD_DATE = NVL(TRIM(:RECORD_DATE), OFD281.RECORD_DATE)
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:165-166`。 **同一個欄位被兩個條件夾擊**:第一個用年度做前綴比對(`:YEAR` 空時 `NULL||'%'` 在 Oracle 等於 `'%'`,恆真,正確), 第二個用完整日期比對。畫面上「年度」與「基準日」兩個欄位同時填時**必須自洽**,不然查不到任何東西—— 而畫面沒有檢查這件事。卡控結果:**過濾(無提示)**。嚴重度:低(使用者多半只填一個)。

**定期定額五支**:

| 畫面 | 查什麼 | 主表 | 條件數 | 值得注意 |
|---|---|---|---|---|
| `OFDI531` | 所得認列明細 | `OFD535` `OFD536` | 4 | 唯一讀 View `OFDV531` 的一支 |
| `OFDI553` | 定期定額契約 | `OFD551` `OFD552` | 11 | **`AND` / `OR` 缺括號**,§5.7 |
| `OFDI554` | 定期定額契約異動 | `OFD554` `OFD555` | 13 | 條件最多的一支;三處 NULL 處理是全片模範 |
| `OFDI563` | 授權申請 | `OFD563` | 3 | **借 `OFDI562` 的 xsd**,§2.4 |
| `OFDI564` | 匯款處理 | `OFD564` | 3 | `OFDI563` 的孿生,但有自己的 xsd |

`OFDI563` / `OFDI564` 是孿生畫面,SQL 骨架一樣,**但一支借 xsd 一支不借**—— 這代表 `OFDI563` 是後來從 `OFDI562` 複製出來的、`OFDI564` 是從 `OFDI563` 複製再補 xsd 的。〔假設〕,依據是三支的 `Created on` 依序是 `OFDI562`(未標)、`OFDI563` 2023/09/04、`OFDI564` 2023/09/05 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:4`、`OFDI564_PO.cs:4`)。

### 5.5 深寫(一)— `OFDI601` 到 `OFDI615` 逐對比對

§0.4 講了搬家的過程,這一節講**三對同號到底是不是同一個查詢**。結論先講:**不是,是撞號。**

#### 5.5.1 三對逐項比較

| 對 | 電子交易軌那支(死)的條件欄位 | 業務 | 境外軌那支(活)的條件欄位 | 業務 | 主表 | 相似度 |
|---|---|---|---|---|---|---|
| `OFDI612` / `OFDI612A` | 交易途徑 / 變更生效日期起迄 | 網路變更生效查詢 | 基金公司 / 基金代碼 / 申請日期 / 買回日期 | 境外基金買回(贖回)單據查詢 | `OFD651` `OFD652` | **0** |
| `OFDI613` / `OFDI613A` | 受益人 ID / 戶號 / 受益人網路流水號 / 開戶申請日期 / 補件日期 / 交易途徑 | 網路開戶申請查詢 | 基金公司 / 基金代碼 / 申請日期 / 轉申購日期 | 境外基金轉換單據查詢 | `OFD651` `OFD653` | **0** |
| `OFDI614` / `OFDI614A` | 記錄類別 / 受益人 ID / 戶號 / 記錄日期 / 受益人網路流水號 | 網路記錄查詢 | 基金公司 / 基金代碼 / 申請日期 / 契約收件日期 | 境外定期定額契約查詢 | `OFD663` `OFD664` | **0** |

「主表」欄只有境外軌那支填得出來——電子交易軌那三支的 PO 整檔被註解,查不到它們查什麼表。

畫面標題欄位取自 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/OFDI612.Designer.cs` 等三支與 `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI612A.designer.cs` 等三支的控件標題(以 `grep` 取,未 Read Designer)。

**三對的相似度都是零。** 所以答案是: **這三對不是「同一查詢的境外軌與電子交易軌兩個版本」,是兩批人各自從 `OFDI6xx` 這個號段取號,撞在一起。**

#### 5.5.2 那「同一查詢的兩個軌」長什麼樣?本片有,但不是這三對

真正的「同一查詢兩個軌」在本片是**業務對應而非代號對應**:

| 業務 | 境外軌 | 電子交易軌 | 對得上嗎 |
|---|---|---|---|
| 申購單據 | `OFDI611` 查 `OFD620` `OFD621` | `IPJI612` 的 `IPJI621_Allot` 結果集查 `OFD620A` `OFD621A` | **對得上** |
| 贖回單據 | `OFDI612A` 查 `OFD651` `OFD652` | `IPJI612` 的 `IPJI621_Redeem` 查 `OFD651A` `OFD652A` | **對得上** |
| 轉換單據 | `OFDI613A` 查 `OFD651` `OFD653` | `IPJI612` 的 `IPJI621_Redeem` 一併查 `OFD653A` | **對得上,但電子交易軌把贖回與轉換併在同一個結果集** |
| 定額契約 | `OFDI614A` 查 `OFD663` `OFD664` | `IPJI612` 的 `IPJI621_RSP` 查 `OFD661A` `OFD662A` | **對得上,但表號不同** |
| 契約異動 | `OFDI615` 查 `OFD666` `OFD667` | `IPJI612` 的 `IPJI621_RSPCHG` | **對得上,表號不同** |
| 停利設定 | (境外軌無對應畫面) | `IPJI612` 的 `IPJI621_STOPSET` `IPJI621_STOPCHG` | **境外軌沒有** |

**所以境外軌的「五支畫面」對應到電子交易軌的「一支畫面的五個結果集」。** 最後兩列的表號對不起來(`OFD663`/`OFD664` 對 `OFD661A`/`OFD662A`), 所以 §0.2 的「去 `A`」規則在這兩組不成立——**〔假設〕的邊界就在這裡**。

#### 5.5.3 維護時的實務結論

| 情境 | 該動哪裡 |
|---|---|
| 境外基金的單據查詢要改 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs` 到 `OFDI615_PO.cs`(含 `OFDI612A_PO.cs` 等三支帶 `A` 的) |
| 網路下單的單據查詢要改 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs`(1821 行,先找對 region) |
| 有人回報「`OFDI612` 壞了」 | 先問是境外還是網路。境外找 `OFDI612A`,網路那支已停用 |
| 要清死碼 | 六支死畫面的 UI / Pxy / Ctl / PO / xsd 全部可刪,**但 PO 要同步從 `QueryPO.EC.csproj:132-146` 移除** |

### 5.6 深寫(二)— `A` / `B` 後綴的第六種成因

`ofdi1.md` 累積出 `A` 後綴的五種成因,並判定「查詢畫面的 `A` 全是第 (d) 種(畫面代號的一部分、與表無關)」。 **本片的四支後綴畫面驗證了這個判定,但補出一個 `ofdi1.md` 沒有的成因。**

#### 5.6.1 逐支判定

| 畫面 | 有沒有同名的表 | 它實際查的表 | 判定 |
|---|---|---|---|
| `OFDI071A` | 沒有 `OFD071A` | `OFD309` | (d) 與表無關 |
| `OFDI072B` | 沒有 `OFD072B` | `OFD303` | (d) 與表無關 |
| `OFDI283A` | **有 `OFD283A`**,而且是活的表 | **`OFD283`**(不帶 `A`) | (d) 與表無關,**而且是反向的** |
| `OFDI612A` | **有 `OFD612A`**,由 `IPJI620` 讀 | `OFD651` `OFD652` | (d) 與表無關 |
| `OFDI613A` | **有 `OFD613A`**,由 `IPJI620` 讀 | `OFD651` `OFD653` | (d) 與表無關 |
| `OFDI614A` | **有 `OFD614A`**,由 `IPJI620` 讀 | `OFD663` `OFD664` | (d) 與表無關 |

**`ofdi1.md` 的判定在本片成立:六支全是第 (d) 種。** 而且本片提供了比 `ofdi1.md` 的 `OFDI075A` 更強的證據—— `OFDI283A` / `OFDI612A` / `OFDI613A` / `OFDI614A` 這四支,**同名的表確實存在、確實是活的、卻由別的畫面在讀**。不是「剛好沒有那張表」,是「**那張表在,但跟這支畫面毫無關係**」。

#### 5.6.2 但「與表無關」只說了一半:後綴從哪來?

`ofdi1.md` 的 (d) 只說「是畫面代號的一部分」,沒說**為什麼會多這個字母**。本片可以回答,而且分兩種:

**成因 (d1):境內外分身,先到先得。**

| 境內軌(`ATLAS.OFD.Query`) | 它查的表 | 境外軌(`ATLAS.OTA.Query`) | 它查的表 |
|---|---|---|---|
| `OFDI071` | `OFD309A` `OFD081A` | **`OFDI071A`** | `OFD309` `OFD081` |
| **`OFDI072A`** | `OFD303A` `OFD081A` | **`OFDI072B`** | `OFD303` `OFD081` |
| `OFDI283` | `OFD281A` `OFD283A` `OFD081A` | **`OFDI283A`** | `OFD281` `OFD283` `OFD081` |

錨點:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI071_PO.cs:87-92`、 `OFDI072A_PO.cs:75-76`、`OFDI283_PO.cs:106-112`, 對照 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI071A_PO.cs:74-80`、 `OFDI072B_PO.cs:76-80`、`OFDI283A_PO.cs:140-159`。

**三對完美對稱:畫面代號加一個字母、表名去掉一個 `A`。** 這正是 `ofdb5.md` 記的分家方式, 本片是它在查詢層的第一份三對實證。而 `OFDI072B` 用 `B` 不用 `A`,是因為**境內版自己已經叫 `OFDI072A`**—— 後綴是往後排的,不是語意編碼。

**成因 (d2):同專案線內撞號避讓。**

`OFDI612A` / `OFDI613A` / `OFDI614A` 不屬於 (d1)——它們的「本尊」`OFDI612` / `OFDI613` / `OFDI614` 不在境內軌,而在**電子交易軌**,而且業務完全不同(§5.5.1)。境外軌 2023 年新建這三支時,`OFDI612` 這個代號在全庫已被 `EC.Query` 佔用 (即使那支當時已經被註解),於是加 `A` 避開。

#### 5.6.3 更新後的成因型錄

| 成因 | 說明 | 本片有無 | 出處 |
|---|---|---|---|
| (a) | 境內外,`FUND_TYPE` `'2'` / `'1'`,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID` | 無 | `ofd5.md` `ofd7.md` |
| (b) | MSSQL 到 Oracle 遷移改名 | 無 | `ofd123.md` |
| (c) | 同概念第二張表 | 無 | `OFD017B` |
| (d) | 畫面代號的一部分、與表無關 | **六支全是** | `ofdi1.md` |
| (d1) | ↳ 境內外分身,後綴先到先得 | `OFDI071A` `OFDI072B` `OFDI283A` | **本片新增** |
| (d2) | ↳ 同專案線內撞號避讓 | `OFDI612A` `OFDI613A` `OFDI614A` | **本片新增** |
| (e) | 族名 | 無 | `ofdb5.md`,標〔假設〕且自承有反例 |

**一句話**:`ofdi1.md` 的「查詢畫面的 `A` 全是第 (d) 種」在本片**完全成立**, 本片把 (d) 拆成兩個可辨識的子成因,並提供了「同名表存在但無關」的四個硬證據。

### 5.7 深寫(三)— `OFDI553` 的 `AND` / `OR` 缺括號

本片最嚴重的一條缺陷。`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:165-174`:

```
 WHERE 1 = 1
   AND OFD551.FH_CD = NVL(TRIM(:FH_CD), OFD551.FH_CD)
   AND OFD552.FUND_ID = NVL(TRIM(:FUND_ID), OFD552.FUND_ID)
   AND OFD551.RCV_DATE BETWEEN NVL(TRIM(:RCV_DATE_ST), '19000101') AND NVL(TRIM(:RCV_DATE_END), '29991231')
   AND OFD551.AGENT_ID = NVL(TRIM(:AGENT_ID), OFD551.AGENT_ID)
   AND OFD551.AGENT_CODE = NVL(TRIM(:AGENT_CODE), OFD551.AGENT_CODE)
   AND OFD551.BF_NO = NVL(TRIM(:BF_NO), OFD551.BF_NO)
   AND BMS001A.ID_NO = NVL(TRIM(:ID_NO), BMS001A.ID_NO)
   AND (OFD551.SUB_BANK_CODE = NVL(TRIM(:SUB_BANK_CODE), OFD551.SUB_BANK_CODE) OR :SUB_BANK_CODE IS NULL)
   AND ((NVL(TRIM(:RSP_NO_ST), OFD551.RSP_NO) = OFD551.RSP_NO)) OR (TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END)
 ORDER BY OFD551.RSP_NO, OFD552.RSP_SRNO
```

**看最後一行。** 括號包的是 `NVL(...) = OFD551.RSP_NO` 那一小段, **`OR` 之後的 `BETWEEN` 沒有任何外層括號把它和前面九個條件圈在一起**。

Oracle 的 `AND` 優先於 `OR`,所以整段 `WHERE` 實際上是:

```
WHERE ( 1=1 AND 條件1 AND ... AND 條件9 )
   OR ( TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END )
```

| 使用者行為 | `:RSP_NO_ST` / `:RSP_NO_END` | `OR` 右側 | 實際結果 |
|---|---|---|---|
| 不填契約書號區間 | 兩者皆 NULL | `X BETWEEN NULL AND NULL` → UNKNOWN | 正常,九個條件生效 |
| **填契約書號區間** | 有值 | 區間內的契約為 TRUE | **前面九個條件全部失效** |

**也就是說:只要使用者填了「契約書號(起)」與「契約書號(迄)」, 基金公司、基金代碼、收件日、銷售機構、戶號、受益人 ID、扣款行全部不算**, 查出來的是**全公司該書號區間內的所有契約**,包含其他基金公司、其他客戶的。

| 面向 | 評估 |
|---|---|
| 結果類型 | **不是過濾,是反向洩漏**——該被濾掉的沒被濾掉 |
| 使用者看得出來嗎 | **看不出來**。多查出來的列與正常列長得一樣,沒有任何提示 |
| 嚴重度 | **高**。越權看到其他基金公司 / 其他受益人的定期定額契約 |
| 修法 | 把最後一個條件整段包起來:`AND ( (NVL(TRIM(:RSP_NO_ST), OFD551.RSP_NO) = OFD551.RSP_NO) OR (TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END) )` |
| 孿生畫面有沒有中招 | **沒有**。`OFDI554` 的 `RSP_NO` 條件是單純的 `= NVL(...)`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:160`),沒有這個 `OR` |

上一行 `SUB_BANK_CODE` 那條**括號是對的**(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`), 證明作者知道要包括號,只是下一行少包了一層。**這是典型的「改對了一條、漏了下一條」。**

### 5.8 深寫(四)— `EC.Query` 的 `IPJI6xx` 五支

必答問題 2 的答案。`IPJ` 這個模組代號 `misc.md` 已查出是**電子交易**(那篇記的 `IJPR611` 是 `IPJ` 的錯字)。本片這五支是電子交易軌的查詢介面,**與同專案的 `OFDI6xx` 八支的關係是「新舊兩代」,不是「兩個業務」**。

#### 5.8.1 五支各管什麼

| 畫面 | 管什麼(推測) | 主表 | 結果集 | 行數 |
|---|---|---|---|---|
| `IPJI612` | 網路交易明細查詢,含退休金試算紀錄 | `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` 到 `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` | **7 張 `IPJI621_*` + `OFD673A`** | **1821** |
| `IPJI613` | 境外到價通知設定查詢 | `OFD681A` `OFD682A` `OFD683A` | `IPJI613` | 173 |
| `IPJI614` | 拋轉資料查詢 | `OFD618A` | **`OFD618A`** | 137 |
| `IPJI620` | 網路交易彙總查詢(申購 / 買回轉換 / 定額 / 受益人異動 / 停利轉申購) | `OFD611A` 到 `OFD615A` | `IPJI620_Allot` `_Redem` `_RSP` `_BMS_CHG` `_Switch` | 307 |
| `IPJI630` | 網路開戶紀錄查詢 | `OFD601` `OFD601CHG` `OFD607A` | `IPJI630_Master` + 裸 `DataSet` `"OFD601"` | 201 |

#### 5.8.2 它們跟同專案的 `OFDI6xx` 八支是什麼關係

| 面向 | `OFDI6xx`(8 支) | `IPJI6xx`(5 支) |
|---|---|---|
| 存活 | 2 活(`OFDI607` `OFDI608`)+ 6 死 | 5 支全活 |
| PO 檔名 | `OracleDao`(活的)/ `_PO`(死的) | 全部 `OracleDao` |
| 條件組法 | 活的兩支**全串字串** | `IPJI613` `IPJI614` 全 bind;`IPJI612` `IPJI620` 混用;`IPJI630` 全串字串 |
| 匯出 | `OFDI608` 有 | **五支全部沒有** |
| 明細彈窗 | 無 | `IPJI612` 有 `_P0` 到 `_P5` 六個,`IPJI614` 有 `_P0` 一個 |
| Model 檔名 | 正常 | **`IPJI612_9iModel.xsd`** `IPJI613Model.xsd` `IPJI614Model.xsd` `IPJI620Model.xsd` **`IPJI630_9iModel.xsd`** |

**`_9i` 那兩支是關鍵線索**:`9i` 是 Oracle 9i。〔假設〕是這兩支的 typed DataSet 在 Oracle 9i 時代就建好、之後沒重建, 所以檔名保留了當時的版本標記;依據是同資料夾其餘 xsd 沒有這個後綴, 而且這兩支正好是五支裡**條件組法最舊**(`IPJI630` 純字串串接)與**檔案最大**(`IPJI612` 1821 行)的兩支。

**關係的結論**:`IPJI6xx` 與 `OFDI6xx` **管同一條業務線(網路 / 語音下單),但是兩代介面**。 `OFDI6xx` 是分散的單一用途查詢(一支查一件事),`IPJI6xx` 是整合式查詢(一支畫面多頁籤多結果集)。新的把舊的取代掉,舊的六支被拔掉 csproj、兩支(`OFDI607` `OFDI608`)因為查的是 `LOG6xx` 軌跡表、 `IPJI6xx` 沒有涵蓋,所以留下來原地改成 `OracleDao`。

#### 5.8.3 `IPJI612`:全片最大的一支

1821 行、七個結果集、`LoadDataSet` 出現 **15 次** (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632,650,657,664,673,684,695,704,710,716,724,733,741,863,961`)。注意 `632` 到 `695` 與 `704` 到 `741` 是**同一組七張表被載入兩次**——兩段分支, 應該是「有挑基金」與「沒挑基金」兩條路。**兩條路各自維護一份 SQL**, 屬於 `ofd4.md 附錄 E` 記過的「基底版與覆寫版讀不同表」的同型風險:改一條忘了改另一條就會不一致。嚴重度:中。

它的結果集全叫 `IPJI621_*` 而畫面叫 `IPJI612`,見 §2.2。

#### 5.8.4 `IPJI613`:兩個沒有守門員的條件

`IPJI613` 的 SQL 裡有兩個**無條件出現**的 bind 變數:

```
WHERE '1' = NVL(:SET_TYPE,'1')
  AND OFD601.ID_NO = NVL(:ID_NO, OFD601.ID_NO)
  AND OFD601.BF_NO = NVL(:BF_NO, OFD601.BF_NO)
  AND OFD682A.FUND_ID IN (SELECT * FROM TABLE(F_FORMATSTRINGTOTABLE(:FUND_ID)))
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:80-83`(第二段 UNION ALL 在 `:108-111`)。而 PO 端加 bind 是**有條件的**:`if (vdb.Utility.Parameters.Rows.Contains("FUND_ID"))` (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:122,127,132,137`),四個條件都這樣寫。

| 風險 | 說明 | 目前會不會發作 |
|---|---|---|
| `ORA-01008` 未繫結全部變數 | SQL 固定有四個 `:` 變數,PO 卻可能只加一部分 | **不會**。UI 一律無條件加四個(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:84-88`) |
| 沒挑基金就查不到任何東西 | `FUND_ID` 是空字串時 `F_FORMATSTRINGTOTABLE('')` 回傳空集合,`IN (空)` 永遠為假 | **〔假設〕會**。`IPJI613` 的 `BeforeSearchButtonClicked` **沒有「至少勾選一檔基金」的檢核**(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:75-89`),而同專案的 `IPJI614` 有(`IPJI614.cs:117`)、`IPJI620` 也有(`IPJI620.cs:259`) |

第二列是**過濾(無提示)**:使用者不挑基金直接查,得到「查無資料」,以為真的沒設定到價通知。 `F_FORMATSTRINGTOTABLE` 是資料庫端的 TVF,**版控外,無原始碼,從呼叫端反推**, 所以空字串的實際回傳沒辦法從程式證實,故標〔假設〕。嚴重度:中。

#### 5.8.5 `IPJI614` / `IPJI620` 的守門員寫得比較好

兩支都在 `BeforeSearchButtonClicked` 前面擋:

| 畫面 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| `IPJI614` | 至少勾選一種拋轉類別 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:105` |
| `IPJI614` | 至少勾選一檔基金 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:117` |
| `IPJI620` | 至少勾選一種交易種類 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:233` |
| `IPJI620` | 查無相關基金明細資料 | **警示** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:243,248` |
| `IPJI620` | 至少勾選一筆基金代碼 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:259` |
| `IPJI612` | 交易日期起迄必填、起必須小於迄 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI612.cs:442-449` |

**這六條是全片僅有的「阻擋」型卡控**(加上 `OFDM287` 的一條,共七條)。 `OTA.Query` 那 24 支**一條都沒有**——什麼都不填就能查,直接把整張表撈回來。加上 §3.2 記的「分頁 0 / 24」,**這 24 支任何一支都可能一次把整張表拉進 client 記憶體**。嚴重度:中(效能與 client 穩定性,不是正確性)。

`IPJI614` 還有一處值得看:多選基金用的是**字串串接進 `IN`**,

```
AND OFD618A.TRADE_TYPE IN (" + xTRADE_TYPE + @")
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:82`。 `xTRADE_TYPE` 由勾選框組出來(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:80` 的 `m_TRADE_TYPE`), **值域是程式產生的固定字串、不是自由輸入**,所以注入風險低; 但同一支的基金多選走的是 TVF(`:90` 的 `F_FORMATSTRINGTOTABLE(:FUND_ID)`)—— **同一支畫面兩種多選、兩種做法**。嚴重度:低(一致性)。

### 5.9 深寫(五)— 三支純字串串接的查詢

#### 5.9.1 `OFDI607` 與 `IPJI630`:值與運算子都直接接進 SQL

樣板:

```
strSQL += " AND OFD601.ID_NO "
        + vdb.Utility.Parameters.FindByName("ID_NO").Opeartor
        + "'" + vdb.Utility.Parameters.FindByName("ID_NO").Value + "'";
```

| 畫面 | 處數 | 欄位 | 錨點 |
|---|---|---|---|
| `OFDI607` | 2 | `ID_NO` `BF_NO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102,106` |
| `OFDI608` | 2 | `ID_NO` `BF_NO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:88,92` |
| `IPJI630` | 6 | `ID_NO` `BF_NO` `EMAIL` 各兩處(兩段 SQL) | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:76,79,82,134,137,140` |

**單引號完全沒有跳脫。** 與 `ofdi1.md` 記的 `OFDI481_PO.cs:142`(連引號都沒有)相比, 這三支至少有包引號,所以打 `1 OR 1=1` 不會成立;但打 `' OR '1'='1` 會。

| 面向 | 評估 |
|---|---|
| 輸入來源 | `custID_NO` / `custBF_NO` / `utxtEMAIL` 三個文字控件,**是自由輸入** |
| `Opeartor` 來源 | 畫面端 `AddParametersRow(..., SQLOperator.Equal, ...)` 寫死,不是使用者控制 |
| 嚴重度 | **高**(`IPJI630` 六處)、**中高**(`OFDI607` `OFDI608` 各兩處) |
| 修法 | 換成 `db.AddInParameter`,與同專案的 `IPJI613` 寫法一致 |

`IPJI630` 另外還有兩處寫死的常數過濾: `AND OFD601.CHG_TYPE = 'Y'`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:57`)。這是**過濾(無提示)**:只有 `CHG_TYPE = 'Y'` 的開戶紀錄查得到,畫面上沒有任何欄位說明這件事。

#### 5.9.2 全片最會咬人的一處:全形空白

`OFDI607` 與 `OFDI608` 處理「日期(迄)」的方式一模一樣:

```
end_date = end_date.Substring(0, 10) + "　23:59:59";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:118` 與 `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:104`。

**`　` 是全形空白(IDEOGRAPHIC SPACE),不是半形空白。** 組出來的字串接著餵給:

```
to_date(' " + end_date + " ','yyyy-MM-dd hh24:mi:ss')
```

格式樣板 `yyyy-MM-dd hh24:mi:ss` 的日期與時間之間是**半形空白**, 而值裡面那個位置是**全形空白**。

| 面向 | 評估 |
|---|---|
| 會怎樣 | Oracle 的 `TO_DATE` 非 `FX` 模式容忍「多個半形空白」,但全形空白是一般字元,**理論上會 `ORA-01861: literal does not match format string`** |
| 標記 | **〔假設〕**。沒有實際跑過,結論由格式樣板與值的字元比對推得 |
| 同一支的「起日」有沒有同樣問題 | **沒有**。`beg_date` 只取 `Substring(0, 10)` 不接時間(`OFDI607OracleDao.cs:113`),格式也只到 `yyyy-MM-dd` |
| 兩支都中 | 是。同一段程式被複製過去 |
| 嚴重度 | **高**(若成立,使用者一填「日期(迄)」就查不動,例外訊息會被 `AddResultRow(false, 0, ex.Message)` 原文貼到畫面上) |
| 怎麼驗 | 在 Oracle 上跑 `SELECT TO_DATE(' 2024-01-01 23:59:59 ', 'yyyy-MM-dd hh24:mi:ss') FROM DUAL` |

**這是本片建議最優先驗證的一條。** 它不需要看懂任何業務,一條 SQL 就能確認。

#### 5.9.3 `OFDI607` 的另一個小問題:位置取參數

```
strSQL += " AND LOG602.CHG_DATETIME >= to_date(' " + beg_date.Substring(0, 10) + " ','yyyy-MM-dd') ";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:113`。 `Substring(0, 10)` 假設畫面送來的字串**一定至少 10 個字元**。畫面端送的是 `DateTime.ToString("yyyy/MM/dd")`,長度剛好 10,目前安全; 但**格式一改(例如改成 `yyyy/M/d`)就會 `ArgumentOutOfRangeException`**, 而且這個例外會被 `catch (Exception ex)` 吞成「查無資料 + 例外訊息」。嚴重度:低(現在不會發作),但屬於「位置取參數」這一類的典型寫法。

#### 5.9.4 `OFDI608` 的一個好設計:ID 遮罩

`OFDI608` 是本片唯一主動遮蔽個資的一支:

```
DECODE(OFD601.ID_NO,'','',SUBSTR(OFD601.ID_NO, 1, 2)||'****'||SUBSTR(OFD601.ID_NO, 7, Length(OFD601.ID_NO))) as ID_NO
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:43`。 **顯示的是遮罩後的 ID,但查詢條件比對的是完整 ID**(`:87` 的 `AND OFD601.ID_NO = '值'`), 所以功能不受影響。值得其他畫面參考——本片另外 37 支的 `ID_NO` 都是明碼輸出。

### 5.10 例外處理:全片兩段式,錯誤訊息會原文上畫面

`OTA.Query` 24 支的 `catch` 完全一致:

```
catch (Exception ex)
{
    model.Utility.Result.Clear();
    model.Utility.Result.AddResultRow(false, 0, ex.Message);
    CommonExceptionBlocker.HandleBusinessException(ex);
}
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:168-173`。

| 面向 | 評估 |
|---|---|
| 好處 | 不吞例外,也有回報 |
| 壞處 | **`ex.Message` 是 Oracle 原文**,`ORA-00904` / `ORA-01861` 這種訊息會直接出現在使用者畫面上,含表名與欄名 |
| 與 `ofdi1.md` 比 | 那片有五支「兩個都做」被當成不一致記在附錄;本片是 **24 支全部兩個都做**,反而是一致的 |
| 結果類型 | 記錄不擋 |
| 嚴重度 | 低(資訊揭露),但排查問題時很好用 |

**沒有任何一支是空 `catch`,也沒有任何一支 `catch (SqlException)`**—— `ofdi1.md` 記的「`catch (SqlException)` 在 Oracle 上是死碼」這條缺陷在本片**不存在**, 因為 24 支都是 2023 年直接照 Oracle 寫的,從來沒有 MSSQL 版本。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**

原因:本片的切片依據是三個專案資料夾,其中兩個是 `*.Query` 專案。 `Dev/ATLAS.OTA.Query` 與 `Dev/ATLAS.EC.Query` 兩棵樹底下**只放 I 畫面**—— 六層資料夾名一律是 `QueryUI` / `QueryFormProxy` / `QueryControl` / `QueryPO` / `QueryDataEntity` / `QueryUIEntity`, 沒有任何批次進入點、沒有 `Program.cs`、沒有 `ServiceBase`。第三個專案 `Dev/ATLAS.OFD` 有 B 畫面,但本片從那裡只收了 `OFDM287` 一支 M。

本片讀的表由誰寫、什麼時候寫,見 §8。

## 7. 報表(R)

**本片無 R 畫面。**

原因同上:報表住在 `Dev/ATLAS.OTA.Report` 與 `Dev/ATLAS.EC.Report`,是另外兩個專案。本片 38 支沒有任何一支產 `.rpt`、呼叫 Report Service、或寫檔到磁碟。 **唯一的「輸出」是 DevExpress 表格的 Excel 匯出**,由 UI 基底 `xOneStepProcessForm` 提供, 畫面只需要指定 `this.ExportGrid = this.ugrdResult` (例:`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI601.designer.cs:397`,以 `grep` 取得,未 Read Designer)。 `xOneStepProcessForm` **無原始碼,從呼叫端反推**。

## 8. 跨模組共用

```text
[圖] 跨模組:本片讀的表是誰建的、誰在寫
圖中文字:本片只讀不寫:38 支裡 37 支沒有任何寫入路徑 / OFDI6xx 境外單據查詢 / 讀 OFD620 621 651 到 653 663 到 667 / 誰在寫這些表 / ATLAS.OTA 的 M 畫面與 B 批次 / 本片不碰 / 沒有 INSERT UPDATE DELETE / 共用主檔:改一個欄位會同時打到十幾支 / OFD081 OFD081A 基金主檔 / 本片 14 支讀 / OFD062 境外基金公司 / 本片 10 支讀 / BMS001A 受益人主檔 / 本片 9 支讀 / FSK003 幣別 / 本片 9 支 INNER JOIN / CTL014 系統代碼 / 本片 4 支讀 / OFD019A 銀行 / 本片 5 支 LEFT JOIN / 電子交易軌的上游:LOG 系列由 EC 的寫入端產生 / LOG600 LOG601 LOG602 / 網路變更軌跡 / OFDI607 OFDI608 讀 / 只查不寫 / 寫入端在 ATLAS.EC / 不在本片範圍 / 唯一的寫入者:OFDM287 走四眼改 OFD283A / OFDM287 xMaintainForm / BaseEVADaoPO + MasterTable / OFD283A 配息給付 / 境內分戶軌的表 / 與 OFDI283A 無關 / 那支查的是 OFD283
```

*圖:圖 5 跨模組。灰虛框=本片只讀、由別的模組維護的表;紫框=風險或唯一的寫入路徑。要判斷改某張表會不會打到本片,看這張圖的第二第三列就夠:基金主檔與幣別表被最多支讀到,而幣別是 INNER JOIN,漏一筆整列就不見。*

### 8.1 本片一張表都不「擁有」

37 支查詢畫面**沒有任何寫入路徑**(§0.5),唯一寫入的 `OFDM287` 改的 `OFD283A` 也是 `ATLAS.OFD` 的表。所以本片對其他模組的影響面是**單向的**:別人改表,本片會壞;本片改程式,不影響別人。

### 8.2 改哪張表會打到本片幾支

| 表 | 打到本片幾支 | 打到誰 | 改動要注意什麼 |
|---|---|---|---|
| `OFD081` | 16 | 見 §2.5 | 境外軌基金主檔。**16 支裡有 6 支是 `INNER JOIN`**,基金主檔少一筆,對應的交易單據整列消失 |
| `OFD062` | 15 | 見 §2.5 | 境外基金公司。多數是 `FROM` 起點或 `LEFT JOIN`,影響較小 |
| `FSK003` | 13 | 見 §2.5 | 幣別主檔。**幾乎全是 `INNER JOIN`**,是本片最危險的共用表(§8.3) |
| `BMS001A` | 10 | 見 §2.5 | 受益人主檔。`OFDI553` `OFDI554` `OFDI283A` 用 `INNER JOIN` |
| `OFD606A` | 10 | `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 全 `LEFT JOIN`,影響只是基金簡稱顯示空白 |
| `OFD601` | 9 | 跨兩條軌 | **唯一被境外軌與電子交易軌同時讀的表**,改欄位要同時測兩邊 |
| `OFD019A` | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` | 全 `LEFT JOIN` |
| `OFD199` | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` | 活動代碼,全 `LEFT JOIN` |
| `OFD081A` | 3 | `IPJI612` `IPJI614` `IPJI620` | 電子交易軌基金主檔。**注意 `OFDI052` 與 `IPJI613` 用這個字串當別名,不是真的讀它** |
| `CTL014` | 3 | `OFDI055` `IPJI612` `IPJI614`,另 `OFDI607` `OFDI608` 以子查詢方式讀 | `SourceType` 的編號是〔客戶特定〕 |

### 8.3 `FSK003` 是本片最危險的共用表

13 支讀它,**其中 `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` 幾乎全用 `INNER JOIN`**, 例:`INNER JOIN FSK003 ON OFD652.FUND_CURRENCY = FSK003.CRNCY_CD` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:135`)。

| 情境 | 結果 |
|---|---|
| 交易的幣別在 `FSK003` 裡沒有對應列 | **整筆交易在查詢結果中消失** |
| 有提示嗎 | **沒有**。卡控結果:**過濾(無提示)** |
| 什麼時候會發生 | 新增一個幣別但 `FSK003` 還沒建;或 `FSK003` 的 `CRNCY_CD` 有前後空白對不上 |
| 嚴重度 | **高**——「查不到某一筆交易」在對帳情境下會被當成資料遺失 |

`OFDI052` 對這件事處理得比較好:主幣別用 `INNER JOIN FSK003 FSK003A`、轉換後幣別用 `LEFT JOIN FSK003 FSK003B` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:122-123`)—— **轉換後幣別可能是空的,所以用 LEFT**。同一支畫面裡兩種 JOIN 是有意識的,不是隨手。

### 8.4 本片被誰引用

**沒有。** 查詢畫面是葉節點:沒有別的模組 `new` 本片的任何 PO / Ctl, 本片的六個組件(`QueryUI.OTA` / `QueryFormProxy.OTA` / `QueryControl.OTA` / `QueryPO.OTA` / `QueryDataEntity.OTA` / `QueryUIEntity.OTA`,加 EC 側的六個)只被主程式的選單載入。

### 8.5 三條軌的改動影響傳遞

| 改動 | 會打到 |
|---|---|
| 改境外軌 `OFD6xx`(不帶 `A`)欄位 | `OTA.Query` 的 `OFDI601` 到 `OFDI605` `OFDI611` 到 `OFDI615`,共 10 支 |
| 改電子交易軌 `OFD6xxA`(帶 `A`)欄位 | `EC.Query` 的 `IPJI612` `IPJI620`,共 2 支(但 `IPJI612` 一支就讀 13 張) |
| 改 `OFD283A` 欄位 | `OFDM287`(本片 §4)+ `Dev/ATLAS.OFD.Query` 的 `OFDI283` |
| 改 `OFD283`(不帶 `A`)欄位 | `OFDI283A`(本片) |
| 改 `LOG600` `LOG601` `LOG602` | `OFDI607` `OFDI608` |

**最後一列值得提醒**:`LOG6xx` 是電子交易的軌跡表,由 `Dev/ATLAS.EC` 的寫入端產生, 本片只讀。那個寫入端**不在本片範圍**。

## 附錄 A. 資料表總表

只列本片 live 的 32 支實際 `FROM` / `JOIN` 到的表;別名已排除。「軌」欄:外=境外綜合帳戶、電=電子交易、內=境內分戶、共=三軌共用。

| 表 | 軌 | 被本片幾支讀 | 讀它的畫面 |
|---|---|---|---|
| `OFD081` | 外 | 16 | 見 §2.5 |
| `OFD062` | 外 | 15 | 見 §2.5 |
| `FSK003` | 共 | 13 | 見 §2.5 |
| `BMS001A` | 共 | 10 | 見 §2.5 |
| `OFD606A` | 外 | 10 | `OFDI601` 到 `OFDI605` `OFDI611` 到 `OFDI615` |
| `OFD601` | 共 | 9 | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` `OFDI607` `OFDI608` `IPJI612` `IPJI630` |
| `OFD019A` | 共 | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` |
| `OFD199` | 外 | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` |
| `OFD081A` | 電 | 3 | `IPJI612` `IPJI614` `IPJI620` |
| `CTL014` | 共 | 5 | `OFDI055` `IPJI612` `IPJI614` `OFDI607` `OFDI608` |
| `COD006A` | 共 | 2 | `OFDI553` `OFDI554` |
| `OFD020V` | 共 | 2 | `OFDI283A` `IPJI612` |
| `OFD256` | 外 | 2 | `OFDI056` `OFDI057` |
| `OFD551` | 外 | 2 | `OFDI553` `OFDI554` |
| `OFD651` | 外 | 2 | `OFDI612A` `OFDI613A` |
| `OFD601CHG` | 電 | 2 | `IPJI612` `IPJI630` |

**以下每張只被一支畫面讀,依讀它的畫面合併列出:**

| 讀它的畫面 | 軌 | 它獨讀的表 |
|---|---|---|
| `IPJI612` | 電 | `COD006` `OFD020A` `OFD138A` `OFD199A` `OFD304A` `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` `OFD656A` `OFD657A` `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` |
| `IPJI613` | 電 | `OFD681A` `OFD682A` `OFD683A` |
| `IPJI614` | 電 | `OFD618A` |
| `IPJI620` | 電 | `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` |
| `IPJI630` | 電 | `OFD607A` |
| `OFDI607` | 電 | `LOG602` |
| `OFDI608` | 電 | `LOG600` `LOG601` |
| `OFDI002` | 外 | `OFD105` |
| `OFDI051` | 外 | `OFD223` |
| `OFDI052` | 外 | `OFD255` |
| `OFDI055` | 外 | `OFD012A` `OFD224` |
| `OFDI071A` | 外 | `OFD309` `SWPRODUCTSDETAIL`(別名 `PROG`) |
| `OFDI072B` | 外 | `OFD303` |
| `OFDI283A` | 外 | `OFD013` `OFD281` `OFD283` |
| `OFDI531` | 外 | `OFD535` `OFD536` `OFDV531` |
| `OFDI553` | 外 | `COD009` `MYOFD072A`(別名 `OFD072A`) `OFD068A` `OFD552` |
| `OFDI554` | 外 | `OFD554` `OFD555` |
| `OFDI563` | 外 | `OFD563` |
| `OFDI564` | 外 | `OFD564` |
| `OFDI601` 到 `OFDI605` | 外 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615`(各一支各一張) |
| `OFDI611` | 外 | `OFD012` `OFD620` `OFD621` |
| `OFDI612A` | 外 | `OFD652` |
| `OFDI613A` | 外 | `OFD653` |
| `OFDI614A` | 外 | `OFD663` `OFD664` |
| `OFDI615` | 外 | `OFD666` `OFD667` |
| **`OFDM287`** | **內** | **`OFD283A`(唯一寫入) `OFD281A` `OFD081V`** |
| `IPJI612` `IPJI630` 兩支 | 電 | `OFD601CHG` |

View(名稱帶 `V`):`OFD020V` `OFD081V` `OFDV531` `V_FUND`。 `OFDV531` 只被 `OFDI531` 讀、`V_FUND` 只被 `IPJI613` 讀(別名 `OFD081A`)。

## 附錄 B. SP / Function / Trigger / View

**本片沒有任何 Stored Procedure。** 38 支掃描結果:`CommandType.StoredProcedure` 0 次、 `EXEC` 0 次、`CALL` 0 次。這是本片與 `ofdi1.md`(11 支全丟 SP)最大的差別之一。

| 物件 | 型別 | 被誰用 | 錨點 | 備註 |
|---|---|---|---|---|
| `F_FORMATSTRINGTOTABLE` | Table Function(TVF) | `IPJI613` `IPJI614` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:83`、`IPJI614OracleDao.cs:90` | 把逗號字串拆成表,供 `IN` 使用。**版控外,無原始碼,從呼叫端反推** |
| `OFD020V` | View | `OFDI283A` `IPJI612` `OFDM287` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:152` | 分行資料 |
| `OFD081V` | View | `OFDM287` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:123` | 境內基金主檔 View |
| `OFDV531` | View | `OFDI531` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI531_PO.cs` | 所得認列用 |
| `V_FUND` | View | `IPJI613` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:73` | **別名為 `OFD081A`**,程式註解記著 `2022.05.13 OFD081A -> V_FUND by Becky` |

**Trigger:本片程式不涉及,未掃描。**

## 附錄 C. 代碼對照

全部從程式的 `CASE WHEN` / `DECODE` 反推,**不是查代碼表**,所以改代碼表不會改到這些顯示。

| 代碼 | 值 | 中文 | 出處 |
|---|---|---|---|
| `OFD611.ALLOT_CTL_CODE` | `'0'` / `'1'` / `'2'` | 未處理 / 已轉處理中 / 已拋轉 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:73` |
| `OFD651.EC_REDEM_PCODE` | `'0'` / `'1'` / `'2'` / `'3'` / `'4'` | 輸入 / 處理中 / 轉入 / **(空字串)** / 刪除 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:100-101` |
| `OFD256.JOB_CD` | `'1'` / `'2'` | 贖回 / 轉換(當過濾條件用,不顯示) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123`、`OFDI057_PO.cs:133` |
| `OFD618A.TRADE_TYPE` | `'1'` 等 | 申購拋轉 等 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:63-68` |
| `OFD682A.INV_CD` | `'1'` / 其他 | 單筆 / 定額 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:69` |
| `OFD681A.ALERT_LIMIT_YN` | `'Y'` / `'N'` | 每次通知 / 一次通知 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:66` |
| `OFD601.CHG_TYPE` | `'Y'` | (寫死過濾,未翻中文) | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:57` |
| `CTL014.Sourcetype` | `'298'` `'299'` `'300'` `'302'` `'346'` | 電子交易的各類代碼群〔客戶特定〕 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:58-59`、`OFDI607OracleDao.cs` |
| `GetDropDownDataSrc` 群組 | `"376"` `"378"` `"380"` `"381"` `"382"` `"419"` | `OFDM287` 的六個下拉〔客戶特定〕 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:94-99` |
| `OFDM287` 的 `GET_WAY` | `'3'` | 配息轉申購(**寫死在 UI,不走代碼表**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:200` |
| `COD006A.CODE_SORT` | `'A8'` | `OFD551.STOP_CD` 的代碼群 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:161` |

境內外的 `SHORE_ID` 值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291`, **本片 38 支沒有任何一支引用它**——三條軌是用**專案與表名**分的,不是用欄位值分的。這一點與 `ofd5.md` / `ofd7.md` 記的境內外分法不同,是本片的觀察。

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module`**,因為本片橫跨三個專案,沒有單一 module key 對得上。改成逐支列表。

| # | 代號 | 專案 | PO 基底 | 在 csproj | 本文處置 |
|---|---|---|---|---|---|
| 1 | `OFDI002` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 2 | `OFDI051` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.3) |
| 3 | `OFDI052` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§2.6.1 §5.3 §8.3) |
| 4 | `OFDI055` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.3) |
| 5 | `OFDI056` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.3,寫死常數 + 無 ORDER BY) |
| 6 | `OFDI057` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.3,同上) |
| 7 | `OFDI071A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.6.2 境內外分身) |
| 8 | `OFDI072B` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.1.3 最嚴重的 NVL 中招 + §5.6.2) |
| 9 | `OFDI283A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§4.1.3 §5.4 §5.6) |
| 10 | `OFDI531` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 11 | `OFDI553` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.7 全片最嚴重缺陷 + 圖 4) |
| 12 | `OFDI554` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.1.4 三處 NULL 處理模範) |
| 13 | `OFDI563` | `OTA.Query` | 無基底 | **UI/Pxy/Ctl/PO 在,無 Model/View xsd** | **已寫**(§2.4 全片唯一四層) |
| 14 | `OFDI564` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 15 | `OFDI601` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.4 §0.4) |
| 16 | `OFDI602` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 17 | `OFDI603` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 18 | `OFDI604` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 19 | `OFDI605` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 20 | `OFDI611` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.2) |
| 21 | `OFDI612A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 22 | `OFDI613A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 23 | `OFDI614A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 24 | `OFDI615` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.2) |
| 25 | `IPJI612` | `EC.Query` | 無基底 | 六層全在(Model 叫 `IPJI612_9iModel.xsd`) | **已寫**(§2.2 §5.8.1 §5.8.3) |
| 26 | `IPJI613` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.8.4) |
| 27 | `IPJI614` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.8.5) |
| 28 | `IPJI620` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§0.2 §5.8.5) |
| 29 | `IPJI630` | `EC.Query` | 無基底 | 六層全在(Model 叫 `IPJI630_9iModel.xsd`) | **已寫**(§5.9.1) |
| 30 | `OFDI606` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 31 | `OFDI607` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.9.1 §5.9.2 §5.9.3) |
| 32 | `OFDI608` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.9.1 §5.9.2 §5.9.4) |
| 33 | `OFDI609` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 34 | `OFDI610` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 35 | `OFDI612` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 36 | `OFDI613` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 37 | `OFDI614` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 38 | `OFDM287` | `ATLAS.OFD` | **`BaseEVADaoPO`** | 六層全在(Model 叫 `OFDM287Model.xsd.xsd`) | **已寫**(§4 全章) |

**統計**:已寫 26 支、表格帶過 12 支;不在 csproj 的 **6 支**(全是 `EC.Query` 那批死畫面的 UI/Pxy/Ctl 三層); 繼承 `BasicEVAPO` 的 **0 支 live**(15 次出現全在註解裡);繼承 `BaseEVADaoPO` 的 **1 支**(`OFDM287`)。

**本片沒有涵蓋但住在同一批專案裡的**(避免下一個人以為漏掉):

| 代號 | 位置 | 為什麼不在本片 |
|---|---|---|
| `OFDI562` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI562_PO.cs` | 不在指派名單。**但 `OFDI563` 借它的 xsd**,所以 §2.4 有提到 |
| `TRPI001` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs` | 不在指派名單;它的 Model 有兩張表(`TRPI001` + `TRP001`),是本專案唯一的多表結果集 |
| `OFDI641` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` | 不在指派名單;`ec.md` 涵蓋 |
| `EC.Query` 的 `OFDI601` 到 `OFDI605` `OFDI611` `OFDI615` | `MSSQL/` 底下 | 不在指派名單,但與名單上那六支死畫面同批、同樣整檔註解(§0.4 事實二) |

## 附錄 E. 讀本文時要注意的地方

每條:缺陷 / 影響 / 錨點 / 嚴重度。**依嚴重度排序。**

### E.1 `NVL(TRIM(:P), 欄)` 樣板讓 NULL 欄位的資料列永遠查不到

- **缺陷**:`欄 = NVL(TRIM(:P), 欄)` 在欄位為 `NULL` 時展開成 `NULL = NULL`,Oracle 三值邏輯得 UNKNOWN,該列被濾掉。參數沒填也一樣。

- **影響**:使用者不填條件按查詢,以為看到全部,實際少了一批。**過濾(無提示)**。

- **錨點**:樣板見 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:138-139`;最嚴重的 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI072B_PO.cs:82-92`(八個條件全中);次之 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:168-169`。

- **嚴重度**:**高**(範圍最廣,`OTA.Query` 24 支全中 + `IPJI613`)

- **正確寫法就在同一批程式裡**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`。

### E.2 `OFDI553` 的 `AND` / `OR` 缺括號,填書號區間就繞過全部條件

- **缺陷**:最後一個條件的 `OR` 沒有外層括號,`AND` 優先於 `OR`,整個 `WHERE` 變成「(九個條件) OR (書號區間)」。

- **影響**:填了契約書號起迄,基金公司 / 基金 / 日期 / 戶號 / 受益人 ID 全部失效,**查得到其他基金公司、其他客戶的契約**,且無任何提示。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:174`

- **嚴重度**:**高**(越權資料揭露)

- **孿生的 `OFDI554` 沒中招**(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:160`)。

### E.3 日期(迄)接了一個全形空白,`TO_DATE` 極可能拋 `ORA-01861`

- **缺陷**:`end_date.Substring(0, 10) + "　23:59:59"`,`　` 是全形空白;格式樣板 `'yyyy-MM-dd hh24:mi:ss'` 那個位置要的是半形空白。

- **影響**:使用者一填「日期(迄)」,查詢就丟例外;例外訊息被 `AddResultRow(false, 0, ex.Message)` 原文貼上畫面。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:118`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:104`

- **嚴重度**:**高**,但標**〔假設〕**——沒有實際在 Oracle 上跑過,結論由字元比對推得。

- **怎麼驗**:`SELECT TO_DATE(' 2024-01-01　23:59:59 ', 'yyyy-MM-dd hh24:mi:ss') FROM DUAL`。**這是本片建議最優先驗證的一條。**

### E.4 `INNER JOIN FSK003` 讓沒有幣別對照的交易無聲消失

- **缺陷**:13 支讀 `FSK003`,幾乎全是 `INNER JOIN`;幣別對不到就整列不見。

- **影響**:對帳時被當成資料遺失。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:135`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs:136`

- **嚴重度**:**中高**

- **同型**:`INNER JOIN BMS001A`(`OFDI283A_PO.cs:144`)、`INNER JOIN OFD081`(`OFDI283A_PO.cs:146`)、`INNER JOIN OFD552`(`OFDI553_PO.cs`)。

### E.5 三支 PO 把畫面輸入直接串進 SQL

- **缺陷**:`" AND 欄 " + Params.FindByName("X").Opeartor + "'" + Params.FindByName("X").Value + "'"`,單引號不跳脫。

- **影響**:`' OR '1'='1` 之類的輸入可改變語意。輸入來源是自由文字控件(受益人 ID / 戶號 / Email)。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:76,79,82,134,137,140`(6 處)、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102,106`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:88,92`

- **嚴重度**:**中高**(`IPJI630` 高)

- **同專案的正確寫法**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:122-137`。

### E.6 `OFDM287` 的八個查詢條件全部字串串接

- **缺陷**:`strSQL += " And OFD283A." + Row.Name + " = " + "'" + Row.Value + "'";`,`LIKE` 分支還不跳脫 `%` `_`。

- **影響**:同 E.5。輸入來源八個控件中六個是遮罩 / 數值 / 日期,只有受益人 ID 與戶號是文字。

- **錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:143,147`,另 15 處在 `:147-262`

- **嚴重度**:**中高**

### E.7 六支死畫面:PO 整檔註解仍掛 csproj,Ctl 退出 csproj 卻還在磁碟上

- **缺陷**:`OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` 的 PO 全檔 `//`,仍列在 `QueryPO.EC.csproj`;對應 Ctl 檔在磁碟上但不在 `QueryControl.EC.csproj`,內容還 `new` 一個不存在的型別。

- **影響**:三支功能(`OFDI606` `OFDI609` `OFDI610`)等於消失且無人知道;改 `OFDI612` 等三支會改到屍體;做影響分析時 `grep` 會命中假結果。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/QueryControl.EC.csproj:108-115`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/OFDI601_Ctl.cs:34`

- **嚴重度**:**中**(維護成本與誤判風險)

### E.8 `OFDI563` 借用 `OFDI562` 的 xsd,改一支動到兩支

- **缺陷**:`OFDI563` 沒有自己的 Model / View,整套借 `OFDI562`;PO 的 `LoadDataSet` 目標是 `model.DataEntity.OFDI562.TableName`。

- **影響**:改 `OFDI562` 的結果欄位會同時改到 `OFDI563` 的畫面,而 `grep OFDI563` 找不到任何 xsd。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93`、`Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:42,58,87`

- **嚴重度**:**中**

### E.9 表別名取成另一張真實存在的表名

- **缺陷**:`INNER JOIN OFD081 OFD081A`、`LEFT JOIN FSK003 FSK003A`、`LEFT JOIN MYOFD072A OFD072A`、`LEFT JOIN OFD019A OFD019B`、`LEFT JOIN V_FUND OFD081A`。

- **影響**:`grep -rn "OFD081A"` 會命中不讀該表的檔案,影響分析容易誤判。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:119-123`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:156`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:133`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:73`

- **嚴重度**:**中**(不影響執行,只影響分析)

### E.10 `OFDM287` 的維護頁只回寫 `MEMO`,其他欄位改了不存也不提示

- **缺陷**:`BeforeModifyButtonClicked` 只做 `Row.MEMO = this.utxtMEMO.Text`。

- **影響**:使用者改了金額 / 帳號 / 日期後按修改,什麼都沒發生,**沒有提示**。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253`

- **嚴重度**:**中**(若那些控件實際上是唯讀,則為低;Designer 未 Read,無法確認)

### E.11 `IPJI613` 沒有「至少挑一檔基金」的守門員

- **缺陷**:SQL 用 `FUND_ID IN (SELECT * FROM TABLE(F_FORMATSTRINGTOTABLE(:FUND_ID)))`,而 UI 不檢查有沒有挑基金;同專案的 `IPJI614` `IPJI620` 都有檢查。

- **影響**:沒挑基金直接查會得到空集合,使用者以為沒有到價通知設定。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:83`、`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:75-89`(無檢核),對照 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:117`

- **嚴重度**:**中**,標**〔假設〕**(`F_FORMATSTRINGTOTABLE` 版控外,空字串的回傳未證實)

### E.12 `OFDM287` 的 `GET_WAY == "3"` 寫死在 UI,下拉卻走代碼表

- **缺陷**:下拉值域走 `GetDropDownDataSrc("380")`,但「哪個值是配息轉申購」寫死。

- **影響**:代碼表改了程式沒改,畫面停止顯示轉換金額。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:96,200`

- **嚴重度**:**中**

### E.13 `IPJI612` 同一組七張結果集有兩段各自維護的 SQL

- **缺陷**:`LoadDataSet` 15 次,`:632-695` 與 `:704-741` 是同一組七張表的兩條分支。

- **影響**:改一條忘了改另一條,兩條路的結果會不一致。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632,704`

- **嚴重度**:**中**

### E.14 `OFDI056` / `OFDI057` 沒有 `ORDER BY`

- **缺陷**:兩支全片唯二沒有 `ORDER BY` 的畫面。

- **影響**:Oracle 不保證回傳順序,同一查詢兩次執行列序可能不同,匯出對帳會誤判。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:128`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI057_PO.cs:138`(`WHERE` 之後直接 `using`)

- **嚴重度**:**低**

### E.15 `OFD651.EC_REDEM_PCODE = '3'` 翻成空字串

- **缺陷**:`CASE WHEN ... = '3' THEN ''`,其餘四個值都翻成「代碼:中文」。

- **影響**:畫面該欄位出現空白,使用者分不出是狀態 `'3'` 還是沒有值。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:101`,`OFDI613A_PO.cs` 同段照抄

- **嚴重度**:**低**

### E.16 `OFDI607` 的 `Substring(0, 10)` 位置取參數

- **缺陷**:假設畫面送來的日期字串長度至少 10;畫面目前送 `yyyy/MM/dd` 剛好 10。

- **影響**:格式一改就 `ArgumentOutOfRangeException`,且會被 `catch (Exception)` 吞成「查無資料」。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:113`、`OFDI608OracleDao.cs:100`

- **嚴重度**:**低**(目前不會發作)

### E.17 `OFDM287` 的 `CanSave` 是死碼

- **缺陷**:`private bool CanSave = true;` 全檔只出現這一次。

- **影響**:無。但讀碼的人會以為有「不可存檔」的卡控。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:28`

- **嚴重度**:**低**

### E.18 `OFDM287` 的 `BF_NO` 條件被複製貼上兩次

- **缺陷**:同一段 `if (model.Utility.Parameters.Rows.Contains("BF_NO"))` 出現兩次,第二次完全重複。

- **影響**:SQL 多一條完全相同的 `AND`,結果不變,但 SQL 變長。

- **錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:207-219` 與 `:221-233`

- **嚴重度**:**低**

### E.19 錯誤訊息把 Oracle 原文貼上畫面

- **缺陷**:`AddResultRow(false, 0, ex.Message)`,24 支一致。

- **影響**:`ORA-xxxxx` 含表名欄名的訊息會顯示給一般使用者。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:171`

- **嚴重度**:**低**(排查很好用,但屬資訊揭露)

### E.20 `OTA.Query` 24 支沒有任何必填檢核,也沒有分頁

- **缺陷**:UI 端沒有 `ValidateErrList.AddError`,PO 端沒有 `ROWNUM` / `FETCH FIRST`。

- **影響**:什麼都不填按查詢就會把整張表撈回 client。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/` 全數無必填檢核;對照 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:233`

- **嚴重度**:**低到中**(效能與 client 穩定性)

### E.21 沒有出現的缺陷(本片體檢結果)

為了讓後面的人不用重查,以下型別**掃過但本片沒有**:

| 型別 | 本片狀況 |
|---|---|
| bind 變數漏冒號(`= FUND_GROUP` 被當欄名) | **無**。24 支的 bind 名與 `AddInParameter` 名逐一核對過 |
| 欄名串兩次(`Row.Name + Row.Name`) | **無** |
| 繼承 `BasicEVAPO` 導致查詢 NRE | **無 live**,15 次全在註解裡 |
| `catch (SqlException)` 在 Oracle 上是死碼 | **無**。`OTA.Query` 24 支從沒有 MSSQL 版本 |
| 空 `catch` / fail-open | **無**。38 支的 `catch` 都有 `AddResultRow` |
| `LIKE` 樣式餵給 `=` | **無** |
| 迴圈 `break` 吞掉後續資料列 | **無**。本片沒有任何逐列迴圈 |
| 非 UTF-8 來源檔 | **無**。38 支全部讀得起來 |
| Model 與 View 欄數對不上 | **無**。24 支逐支比對,全部一致(§2.3) |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `ATLAS.OTA.Query` 24 支 + `ATLAS.EC.Query` 13 支 + `ATLAS.OFD` 的 `OFDM287`,共 38 支 |

由 build_doc.py v2.0.0 於 2026-09-15 21:04 產生 · 標題 110 · 圖 5 · 表格 63 · 程式錨點 164 · § 連結 139 · 引用檢查：畫面 47（缺 0） · Table 27（缺 0） · 結果集 23（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofdr1.md
============================================================

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

============================================================
【文件】kb/modules/ofdr2.md
============================================================

# ATLAS OFDR2 模組 全流程商業邏輯

> 產出日期:2026-09-16(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:**第一次讀報表的人先讀 `ofdr1.md §0.2` 那張 M / I / R 三欄對照表**,本文不重做,只在 §0.3 列出本片與它不同的地方。要動手改某一支的人,查 §3 清冊定位,再跳 §7 對應小節。急著知道哪裡會咬人的人直接翻附錄 E——**本片最危險的一條是 E1:報表 SP 用「全域、不分使用者」的暫存表做資料權限過濾,兩個人同時按預覽會互相蓋掉**。

> ⚠ **OFDR2 不是一個業務模組,是一份切片。** 涵蓋兩個獨立方案底下的 **50 支 R 畫面**:`Dev/ATLAS.OTA.Report`(36 支)與 `Dev/ATLAS.EC.Report`(14 支)。寫完這片,`OFD` 軌(含 `OTA` / `EC` 兩個子軌)的 M / I / B / R 四型全部收齊。名稱 `OFDR2` 為**推測**,取自「`OFDR` 報表第 2 片」。

> ⚠ **本片與 `ofdr1.md`(OFD 報表第 1 片)最大的三個差別**:(1) **SP 在版控**——OTA 那軌 37 個 SP 一個不缺,全在 `DB/SP/`,所以本文能寫出「這張報表真的讀哪些表」;(2) **`Basic_PO` 派 0 支**,`ofdr1.md` 那條「按預覽就 NRE」的缺陷型在本片不存在;(3) **EC 那軌 14 支有 7 支是死碼**——UI / Ctl / Pxy 不在 csproj、PO 整檔被 `//` 註解掉。

> ⚠ **「報表唯讀」在本片是錯的,而且錯在 SP 層。** C# 端只有 1 支寫 DB(`OFDR050` 的「製作資料」),但 38 個 SP 裡 **26 個會 `DELETE` + `INSERT` 暫存工作表**,其中 `OFD068AT0` / `DSMR008T0` / `DSMR008T4` / `TA_DEPT_EMP` 四張是**沒有使用者鍵的全域表**(§2.4、附錄 E)。

> ⚠ **〔客戶特定〕**:境外基金公司代碼 `FH_CD`、銷售機構區別碼 `AGENT_ID` 的 `'0'`~`'5'` 對應(公 / 銀 / 券 / 顧 / 信 / 產)、資料權限豁免部門 `M2` `C2` `G16` `G17`、集保帳號 `TDCC_BF_NO` 為本站台的值。

> ⚠ **〔共用〕**:`OFD081`(境外基金主檔)、`BMS001A`(受益人主檔)、`OFD062`(基金公司)、`FSK003`(幣別)幾乎每個 SP 都讀,改欄位會同時打到本片二十幾支報表(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、SQL 組法看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別四種與 R 的七層看 `architecture.md §6`。**不要整份讀**。報表的通則基準全部取自 `ofdr1.md §0`。

## 0. 系統邊界與角色

```text
[圖] 六對同號 OTA 對 EC,加 OFDR001B 對 OFDR001A、OFDR002 對 OFDR002A 的對應與判定
圖中文字:左 OTA 專案(境外)· 右 EC 或 OFD 專案(境內)· 同一列 = 同號 / OTA / EC / OFD / OFDR601A / 網路申購檢核 / OFDR601 / 網路申購 3 版型 / 兩軌 f 型 / OFDR602A / 網路買回檢核 / OFDR602 / 網路買回 3 版型 / 兩軌 f 型 / OFDR603A / 網路轉申購檢核 / OFDR603 / 轉申購 3 版型 / 兩軌 相似度最高 0.23 / OFDR604A / 網路定額契約檢核 / OFDR604 / 定期定額申購委託 / 兩軌 f 型 / OFDR605A / 網路定額異動檢核 / OFDR605 / 定期定額異動委託 / 兩軌 f 型 / OFDR606A / 網路交易客戶明細 / OFDR606 / 受益人資料異動委託 / 撞號 Jaccard 0.06 / OFDR001B / 境外結餘單位數檢核 / OFDR001A (OFD) / 境內 結餘單位數查核 / 兩軌 f 型 B 讓號 / OFDR002 / 境外結餘單位數清冊 / OFDR002A (OFD) / 境內 結餘單位數清冊 / 兩軌 f 型 A 在 OFD 側 / 判別法:比 UI 條件的業務維度與 SP 主表,不比程式相似度(五對兩軌都 < 0.3)
```

*圖:圖 2 八對同號報表的對應。中間框是判定:橘=同一份業務報表在兩個子系統各做一份(成因 f),紫=撞號。601~605 五對業務動作一一對應,只有 606 兩邊講的不是同一件事;001B/002 從 OTA 側反向驗證 ofdr1.md 的結論成立。虛線箭頭表示「同號但不同業務」。*

### 0.1 兩個子軌各管什麼

| 子軌 | 方案 | 本片支數 | 管什麼(依報表中文名與 SP 名推測) | 不在本片的同方案畫面 |
|---|---|---|---|---|
| **OTA** | `Dev/ATLAS.OTA.Report/Source/Vendor.ATLAS.OTA.Report.sln` | **36** | **境外基金**(Offshore TA,**假設**;依據:36 支報表中文名有 30 支帶「境外」,其餘 6 支的 SP 全部以 `S_OTA_` 開頭)的申購 / 贖回 / 轉換確認書、對帳單、試算檢核清單、受益分配、定期定額、網路交易檢核、AUM 與獎金 | `OFDR561` `OFDR562`(`ofdr1.md` 附錄 D.1 已標記)、`OTAR901` `TRPR001`(`misc.md` 已寫) |
| **EC** | `Dev/ATLAS.EC.Report/Source/Vendor.Product.TA.EC.Report.sln` | **14** | **網路交易**(Electronic Commerce,**假設**;依據:14 支中文名全帶「網路」)的委託資料查核表、前置核對表、比對異常報表、開戶統計 | `IPJR607` `IPJR901` `IJPR611`(`misc.md` 已寫) |

兩軌之間**沒有任何程式呼叫**,也沒有共用 csproj。它們被放進同一片只因為都是 `OFDR` 代號、都是 R 型。

**EC 那軌只有一半是活的。** 14 支裡 `OFDR601`~`OFDR606` `OFDR609` 共 7 支在 `ReportUI.EC.csproj` 內(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/ReportUI.EC.csproj:223-259`), 另外 7 支 `OFDR607` `OFDR608` `OFDR610` `OFDR611` `OFDR612` `OFDR613` `OFDR690` 的 UI / Ctl / Pxy **都不在對應 csproj**,PO 只有 `MSSQL/` 那份、而且**整檔被 `//` 註解**(§7.10)。它們是 MSSQL 時代的遺骸,沒被遷到 Oracle。

### 0.2 六對同號:五對是兩軌、一對是撞號(**本片最重要的結論**)

`OFDR601A`~`OFDR606A`(OTA)與 `OFDR601`~`OFDR606`(EC)六對同號分屬兩專案。逐對比了四件事:報表中文名、SP 名、UI 查詢參數、四層程式的文字相似度(`difflib.SequenceMatcher`,剝註解後逐行比)與 `Model.xsd` 欄位交集。結論:

| 對 | OTA 中文名 | EC 中文名 | OTA SP | EC SP | UI 相似度 | PO 相似度 | xsd 欄位 Jaccard | 判定 |
|---|---|---|---|---|---|---|---|---|
| 601 | 境外網路交易申購檢核列印作業 | 網路申購前置核對表 / 網路申購委託資料查核表 / 網路申購委託資料比對異常報表 | `S_OTA_OFDR601A_GET` | `S_EC_IPJR601_GET` | 0.16 | 0.21 | 0.20 | **兩軌** |
| 602 | 境外網路交易買回檢核表列印作業 | 網路買回前置核對表 / 委託資料查核表 / 比對異常報表 | `S_OTA_OFDR602A_GET` | `S_EC_IPJR602_GET` | 0.16 | 0.23 | 0.14 | **兩軌** |
| 603 | 境外網路交易轉申購檢核表列印作業 | 線上轉申購檢核表 / 網路交易轉申購檢核表列印作業 / 比對異常報表 | `S_OTA_OFDR603A_GET` | `S_EC_IPJR603_GET` | 0.23 | 0.22 | 0.20 | **兩軌** |
| 604 | 境外網路交易定額契約檢核表列印作業 | 網路定期定額申購委託資料查核表 / 比對異常報表 | `S_OTA_OFDR604A_GET` | `S_EC_IPJR604_GET` | 0.22 | 0.21 | 0.19 | **兩軌** |
| 605 | 境外網路交易定額異動檢核表列印作業 | 網路定期定額異動委託資料查核表 / 比對異常報表 | `S_OTA_OFDR605A_GET` | `S_EC_IPJR605_GET` | 0.17 | 0.22 | 0.07 | **兩軌** |
| **606** | **境外網路交易客戶明細表** | **網路受益人資料異動委託資料查核表** / 比對異常報表 | `S_OTA_OFDR606A_GET` | `S_EC_IPJR606_GET` | 0.17 | 0.25 | **0.06** | **撞號** |

錨點:中文名取 `SetQueryParameters` 第三參——`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:162` · `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:92-100` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR606A.cs:154` · `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR606.cs:59-63`; SP 名——`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:66` · `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:46`。

三句話講清楚:

1. **601~605 是「同一份業務報表在兩個子系統各做一份、用後綴讓號」**——與 `ofdr1.md §7.2` 給 `OFDR001A` / `OFDR001B` 定的第 (f) 種成因相同。判別依據不是程式碼相似(0.16~0.36,**幾乎是重寫不是複製**),而是**業務名對得上**:申購 / 買回 / 轉申購 / 定額契約 / 定額異動五個動作一一對應,EC 那邊多的「前置核對表」「比對異常報表」是境內網路交易特有的作業,OTA 那邊多的 `OMNIBUS_ID`(綜合帳戶)、`FH_CD`(基金公司)是境外特有的維度。

2. **606 是撞號。** OTA 的 `OFDR606A` 印「網路交易客戶明細」——條件是申請日、註冊類別、付款方式,讀 `OFD607`(網路交易申請)+ `OFD601`(`DB/SP/S_OTA_OFDR606A_GET.SQL:54-56`);EC 的 `OFDR606` 印「受益人**資料異動**委託查核」——條件是受益人 ID 起迄、戶號起迄、異動生效日、異動狀態。**兩張報表講的不是同一件事**,只是都排在網路交易群的第六號。與 `ofdi2.md` 查出的 `OFDI612` / `OFDI612A` 撞號同型。

3. **判別法可以抄**:同號畫面落在不同專案時,先比 UI 查詢參數的**業務維度**(日期是哪個日期、狀態是哪個狀態),再比 SP 讀的主表。相似度低不代表撞號——本片五對兩軌的相似度都低於 0.3。

### 0.3 本片與 `ofdr1.md §0.2` 那張 M / I / R 對照表不同的地方

`ofdr1.md §0.2` 的三十列對照**直接引用不重做**。以下只列 R 欄在本片實測值**不一樣**的列:

| `ofdr1.md §0.2` 列 | OFD 那片(40 支) | **本片 OTA(36 支)** | **本片 EC(14 支)** | 意義 |
|---|---|---|---|---|
| 2 層數退化 | 0 支缺 xsd | **4 支沒有自己的 xsd**:`OFDR002` 借 `OFDR001BModel`、`OFDR058` 借 `OFDR057Model`、`OFDR132` `OFDR134` 借 `OFDR131Model`(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:59` · `Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/OFDR058_Ctl.cs:37`) | 7 支活的**每支兩套 xsd**:`<代號>Model.xsd`(MSSQL 時代,死)+ `<代號>_9iModel.xsd`(Oracle,活) | 借用 = 改 `OFDR001B` 的欄位會同時打到 `OFDR002` |
| 6 UI 生命週期 | 查詢 → 預覽 / 列印兩段 | **35 支沒有「查詢」按鈕**,只有預覽 / 列印;`DoValidate()` 直接把條件塞進 `QueryVDB`,由 `xReportForm` 在列印前取數(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:152-163` · `:201-219`)。唯一保留查詢鈕的是 `OFDR001B`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:187-200`) | 7 支同 OTA,預覽 / 列印共用一個 handler(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:80`) | **使用者按預覽前看不到筆數** |
| 7 PO 基底 | 兩派:`I<代號>_PO` 26 / `Basic_PO` 13 | **一派:36 支全部 `I<代號>_PO`**,介面與實作寫在同一檔(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:24-31`) | 7 支 `<代號>OracleDao : I<代號>PO`(**沒有底線**),介面另放 `Oracle/Interface/`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/Interface/IOFDR601PO.cs:7-9`) | **`Basic_PO` 派 0 支** |
| 9 `m_db` | 13 支恆 null | **36 支全部 `private Database m_db = new Database("TA", DbServerType.Oracle);` 宣告即初始化**(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR001B_PO.cs:32`) | 7 支欄位叫 `db`,建構子內 `new Database("TA", DbServerType.Oracle)`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:20-25`) | **`m_db` 死碼線本片 0 支** |
| 13 實體表清單從哪來 | SP 內部,SP 不在版控 | **SP 在版控**:`DB/SP/` 有 37 個 `S_OTA_OFDR*` 一個不缺,§2.2 逐支列出讀哪些表 | SP `S_EC_IPJR60x_GET` `S_EC_OFDR609_Get` `S_EC_OFDR609D_Get` **8 個全不在版控** | OTA 是全庫**唯一**報表取數邏輯可 diff 的軌 |
| 20 寫入路徑 | 7 支 C# `ExecuteNonQuery` | **C# 1 支**(`OFDR050` 製作資料,§7.7);**SP 26 / 38 個寫暫存表**(§2.4) | C# 0 支活的(5 支有 `ExecuteNonQuery` 但都在沒人呼叫的 `DoDeleteTempTable` 裡,§7.9) | 寫入下沉到 SP |
| 22 條件怎麼進 PO | `Parameters` 袋逐筆 `rrRow.Name ==` 比對 | **`EVAStringHelper.GetParamValue(model, "欄名")` 一行取一個**(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:69-76`),36 支一致 | 仍是 `foreach rrRow.Name == "@strXxx"` 老寫法,參數名帶 `@` 前綴、SP 端卻是 `wXxx`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:50-101`) | 兩軌兩個世代 |
| 23 條件怎麼進 SQL | 36 支 SP 綁定,3 支串接 | **34 支全綁定;2 支(`OFDR085` `OFDR086`)把 UI 勾選的基金清單串成 `IN ('a', 'b')` 進自組 SQL**(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR085_PO.cs:137`),值來自 grid 勾選不是自由輸入(§2.5) | 7 支活的全綁定;5 支的死方法 `DoDeleteTempTable` 有串接,但沒人呼叫 | 串接面比 OFD 那片小,且不吃鍵盤輸入 |
| 25 輸出介面 | Crystal 36 / Excel 2 / 無 2 | **Crystal 36,其中 `OFDR901A` `OFDR904` 另可轉 Excel**(`Microsoft.Office.Interop.Excel`,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:308-341`) | Crystal 7 | — |
| 28 例外處理 | `AddResultRow(false, 0, ex.Message)` | **`AddResultRow(false, 0, string.Empty)` + `CommonExceptionBlocker.HandleBusinessException(ex)`**——空訊息交給框架(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:95-100`) | 同 OTA | 錯誤原文不貼畫面,比 OFD 那片乾淨 |
| 30 卡控 | 阻擋為主,0 支詢問 | 阻擋 36 支;**詢問 1 支**(`OFDR050` 「此交易日期已有資料, 是否重新產生!?」`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:158`);過濾(無提示)集中在 SP(§7.11) | 阻擋 7 支 | 本片有詢問型 |

其餘二十列(七層、`MasterTable` 全無、四眼 0 個、xsd 是結果集形狀、`Ctl` 用 `TransferVDBHelper` 整表搬、`.rpt` 第三份 schema 無編譯期檢查、DB 型別 Oracle)**與 `ofdr1.md §0.2` 一致,不重列**。

### 0.4 三句話版本

1. **OTA 那軌是 2022~2023 年「OTA 改版」時整批重寫的**(SP 抬頭有 `2023.10.05 OTA改版 OFDR904_P01 => S_OTA_OFDR904_GET`,`DB/SP/S_OTA_OFDR904_GET.sql:17`),所以結構整齊:36 支 PO 同一個模子、SP 全進版控、參數全綁定。**它是全庫報表的「新範本」**,加新報表照 `OFDR601A` 抄就對了。

2. **EC 那軌是舊物**:MSSQL 時代的 PO 被註解掉、Oracle 版只補了 7 支,另 7 支沒補也沒刪,連 csproj 都不掛。方法名還叫 `GetIPJR601Data`、SP 叫 `S_EC_IPJR601_GET`——**`IPJR` 才是它的本名**,`OFDR60x` 是後來改的畫面代號。

3. **本片真正的風險不在 C#,在 SP 的暫存表設計**:26 個 SP 用 `DELETE 全表 + INSERT` 重建 `OFD068AT0`(銷售機構名稱)、`DSMR008T0`(基金清單)、`DSMR008T4`(可查戶號)、`TA_DEPT_EMP`(資料權限),四張表**都沒有 `USERDOMAIN` 欄**。兩個使用者同時按預覽,後者的 `DELETE` 會把前者剛塞進去的資料清掉(附錄 E1~E3)。

### 0.5 資料怎麼從 SP 流到 `.rpt`(以 `OFDR601A` 為例)

| 步 | 在哪 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | UI | `FormInitial`:`ResultVDB` / `FormProxy` 指定,基金下拉鎖境外(`SHORE_ID.OffShore`) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:52-66` |
| 2 | UI | 使用者按「預覽」或「列印」→ `DoValidate()`:清錯誤清單、跑 `FormvalidatorManager`、驗日期起迄 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:201-219` |
| 3 | UI | 不過就 `e.Cancel = true`;過了 `GetQueryVDB()` 把 8 個條件塞進 `Util.Parameters`,再 `SetQueryParameters("OFDR601ARPS1", "OFDR601ARPS1", 中文名)` | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:152-183` |
| 4 | FormProxy | `xReportForm`(無原始碼,從呼叫端反推)呼叫 `OFDR601A_Pxy` 送過 Remoting | `Dev/ATLAS.OTA.Report/Source/FormProxy/ReportFormProxy/OFDR601A_Pxy.cs` |
| 5 | Control | `GetReportData` → `GetDaoInstance<IOFDR601A_PO>()` → `ExecPOActionToViewVDB`;回程 `TransferVDBHelper.TransferDataSet` 整個 DataSet 搬成 View | `Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/OFDR601A_Ctl.cs:48-53` · `:76-85` |
| 6 | PO | `BeginTransaction` → `GetStoredProcCommand("S_OTA_OFDR601A_GET")` → 8 個 `AddInParameter` → `AddOutParameter(RefCursor)` → `LoadDataSet` → `Commit` | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:55-102` |
| 7 | SP | 先 `DELETE OFD068AT0` + `INSERT ... FROM OFD068A_V02`(銷售機構名稱暫存),再 `OPEN OutTB1 FOR` 主查詢 | `DB/SP/S_OTA_OFDR601A_GET.SQL:36-42` |
| 8 | Control | `GetReportObject`:從客戶端傳來的 `ReportParameters[0].ReportClass` 取版型名,`CRReportTransfer.TransferFileByte(rpt)` 回傳 `.rpt` 位元組 | `Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/OFDR601A_Ctl.cs:59-63` |
| 9 | UI | `ReportLoad`:`SetRptSchemaOnDoc()` 綁 schema,再 5 個 `SetParameterValue` 補抬頭(日期區間、基金公司、基金、帳戶別、交易狀態) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:100-145` |
| 10 | CrystalReports | `OFDR601ARPS1.rpt` 排版輸出 | `Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/OFDR601ARPS1.rpt` |

跟 `ofdr1.md §0.4` 的差別只有第 2~3 步:**沒有獨立的「查詢」按鈕**,檢核與取數都掛在預覽 / 列印之前。

### 0.6 這 50 支涵蓋哪些業務線(推測,依報表中文名與 SP 讀的主表歸類)

| 群 | 畫面 | 主表(從 SP 讀出,§2.2) |
|---|---|---|
| ① 結餘單位數查核(OTA) | `OFDR001B` `OFDR002` `OFDR003` | `OFD303` `OFD304`~`OFD306` `OFD310` `OFD311` |
| ② 確認書與對帳單(OTA) | `OFDR042` `OFDR050` `OFDR054` `OFDR085` `OFDR086` `OFDR554` | `OFD221` `OFD252` `OFD253` `OFD132A`(寄發設定)`OFD082` `OFD083`(費率) |
| ③ 交易明細與試算檢核(OTA) | `OFDR051` `OFDR052` `OFDR057` `OFDR058` `OFDR081` `OFDR088` `OFDR089` `OFDR090` `OFDR093` `OFDR094` | `OFD220` `OFD221` `OFD224` `OFD251`~`OFD256` |
| ④ 受益人資料查核(OTA) | `OFDR109` `OFDR111` | `OFD110` `OFD112` |
| ⑤ 受益分配(OTA) | `OFDR131` `OFDR132` `OFDR133` `OFDR134` | `OFD281` `OFD282` `OFD283` |
| ⑥ 定期定額(OTA) | `OFDR551` `OFDR552` `OFDR553` | `OFD551` `OFD552` `OFD554` `OFD555` `OFD904` |
| ⑦ 網路交易檢核(OTA) | `OFDR601A`~`OFDR606A` | `OFD601` `OFD607` `OFD620` `OFD621` `OFD651`~`OFD653` `OFD663` `OFD664` `OFD666` `OFD667` |
| ⑧ 獎金與 AUM(OTA) | `OFDR901A` `OFDR904` | `SAL071` `OFD221` `OFD302` `OFD305` `OFD311` |
| ⑨ 網路交易委託查核(EC,活) | `OFDR601`~`OFDR606` `OFDR609` | SP 不在版控,主表不可知 |
| ⑩ 死碼(EC) | `OFDR607` `OFDR608` `OFDR610`~`OFDR613` `OFDR690` | 無 |

### 0.7 誰用、什麼時候用

從 UI 的預設值與檢核反推(**假設**,無選單表可對):

- 群 ① ③ ⑤ ⑥ ⑦:**股務 / 作業人員**日結後印檢核清單。`OFDR001B` 的檢核表由 SP 回 `strMsg`「帳未平」,`OFDR002` 列印前先查該日 `OFD303.POST_CTL_CODE` 是否全為已過帳(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:124-159`)。

- 群 ②:**客服 / 寄發作業**,有「整批列印 / 指定受益人」與「郵寄 / E-mail / FAX / 親領」寄送選項(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR554.cs:160-167`),依 `OFD132A`(寄發設定)過濾。

- 群 ⑧:**業務 / 財務**月結,可轉 Excel。

- `OFDR042`(交易對帳單)另有**資料權限**:非 `M2` `C2` `G16` `G17` 部門的人只看得到自己銷售關係內的受益人(`DB/SP/S_OTA_OFDR042_GET.SQL:477-562`)——**這是本片唯一有資料權限的一支**,也是唯一把 `USERID` 傳進 SP 的一支。

### 0.8 不管什麼

- 不管**境內**版本:`OFDR001A` `OFDR002A` 在 `ofdr1.md §7.2`;EC 那軌雖然是境內網路交易,但只管報表,委託資料的維護與批次在 `ec.md`。

- 不管 `OFDR561` `OFDR562`(OTA 專案內,`ofdr1.md` 附錄 D.1 標記過,本片依交辦範圍不收)與 `OTAR901` `TRPR001` `IPJR607` `IPJR901` `IJPR611`(`misc.md`)。

- 不管 `.rpt` 內部版面:不 Read 二進位,只比對檔名、csproj 宣告與 UI 引用。

- 不管 EC 軌 8 個版控外 SP 的內容:只從 C# 呼叫端反推參數與結果集。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDR2 全景:OTA 八群 36 支與 EC 活死各 7 支,加兩軌共同的七層結構
圖中文字:OTA 軌 36 支:境外基金,SP 全在版控,PO 同一模子 / OFDR001B OFDR002 OFDR003 / 結餘單位數查核 3 支 / OFDR042 050 054 085 086 554 / 確認書與對帳單 6 支 / OFDR051 052 057 058 081 088~094 / 交易明細與試算檢核 10 支 / OFDR109 OFDR111 / 受益人資料查核 2 支 / OFDR131 132 133 134 / 受益分配 4 支 三支共用 xsd / OFDR551 552 553 / 定期定額 3 支 554 是確認書 / OFDR601A ~ 606A / 網路交易檢核 6 支 對 EC 六對同號 / OFDR901A OFDR904 / 獎金與 AUM 2 支 可轉 Excel / EC 軌 14 支:境內網路交易,SP 不在版控,一半是死碼 / OFDR601 ~ 606 OFDR609 / 活的 7 支 OracleDao 派 / OFDR607 608 610 611 612 613 690 / 死的 7 支 不在 csproj PO 整檔註解 / S_EC_IPJR60x_GET / 8 個 SP 全不在版控 / 兩軌共同結構:七層 Crystal,xReportForm,Model.xsd 是結果集形狀 / UI xReportForm / OTA 35 支沒有查詢鈕 / PO I 代號 PO 或 OracleDao / m_db 全部有初始化 0 支死碼 / SP 38 個在版控 (OTA) / 26 個寫暫存表 4 張全域無使用者鍵 / .rpt 109 個 / 2 個懸空 050 901A
```

*圖:圖 1 OFDR2 全景。橘框=本片 50 支報表,依 §0.6 業務線分群;紫框=有風險的:EC 死碼 7 支、SP 層的全域暫存表;黑框=版控外或無法 diff 的資產。兩軌之間沒有任何程式呼叫;OTA 那軌 SP 全在版控,是全庫唯一能在 repo 內回答「這張報表讀哪些表」的報表專案。*

### 1.2 六對同號與 `OFDR001B` / `OFDR002` 的對應

(圖由 `ofdr2.figs.py` 注入到 §0 之後,對應 §0.2 與 §7.2、§7.3。)

### 1.3 資料來源與 `m_db` 狀態分群

(圖由 `ofdr2.figs.py` 注入到 §2 之後與 §3 之後。)

### 1.4 最重的一支:`OFDR042` 的完整路徑

(圖由 `ofdr2.figs.py` 注入到 §7 之後,對應 §7.8。)

### 1.5 跨模組:報表讀的表是誰建的

(圖由 `ofdr2.figs.py` 注入到 §8 之後。)

## 2. 資料模型

```text
[圖] 兩軌的取數路徑,與 OTA SP 內自用暫存表與全域暫存表兩種設計
圖中文字:OTA 36 支 PO → 37 個 SP:條件全綁定,寫入下沉到 SP / UI Util.Parameters / 欄名 key 不帶 @ / PO GetParamValue 具名綁定 / iXxx 參數 OutTBn RefCursor / SP S_OTA_OFDR*_GET / 38 個檔 cp950 全在 DB/SP / SP 內兩種暫存表 / 自用暫存 USERDOMAIN 鍵 / OFDR002T1 003T1 042T* 050T1~9 552T1 605AT1 901T1 904T1 / DELETE WHERE USERDOMAIN = x / SYS_GUID 或 C# 傳入 併發安全 / 全域暫存 無使用者鍵 / OFD068AT0 DSMR008T0 DSMR008T4 TA_DEPT_EMP OFDR081T1 / DELETE 全表 再 INSERT / 18 / 7 / 5 / 1 / 1 個 SP 併發互蓋 / LEFT JOIN OFD068AT0 / 對不到 → 名稱空白 E2 / INNER JOIN DSMR008T0 / 對不到 → 零筆 E3 / TA_DEPT_EMP 算資料權限 / 越權或漏印 E1 待複驗 / EC 7 支 PO → 8 個 SP:同樣全綁定,但 SP 不在版控 / UI @strXxx 帶 T-SQL 前綴 / MSSQL 時代的 key 沒改 / OracleDao rrRow.Name == 比對 / wXxx 參數 oCUR RefCursor / S_EC_IPJR60x_GET / 版控外 讀什麼表不可知
```

*圖:圖 3 資料怎麼取。上半是 OTA:C# 只組參數,邏輯全在 SP;SP 內 8 個用有使用者鍵的自用暫存表(安全),26 個用沒有使用者鍵、DELETE 全表重建的全域暫存表(紫框,§2.4)。三個紫框出口對應附錄 E1~E3。下半是 EC:結構相同但 SP 在版控外,只能從 C# 反推。*

### 2.1 主表與明細:**本片沒有**

與 `ofdr1.md §2.1` 同:50 支 PO 沒有一支宣告 `MasterTable` / `DetailTable`(`grep -c MasterTable` 在 `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/` 與 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/` 全目錄都是 0)。 `Model.xsd` 的根節點是畫面代號、內部「表」是結果集形狀:`OFDR050Model.xsd` 宣告 `OFDR050_1`~`OFDR050_9` 九張,對應 SP 的九個 `SYS_REFCURSOR` 出參(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:273-290`)。

**但本片能往下多走一層**:OTA 那軌的 SP 在版控,所以「報表真的讀哪張表」寫得出來(§2.2)。這在 `ofdr1.md`(71 個 SP 0 個在版控)與 `nfdr1.md`(60 個只有 1 個)都做不到。

### 2.2 SP:OTA 38 個全在版控,EC 8 個全不在

#### 2.2.1 OTA 那軌:`DB/SP/` 底下 38 個檔

36 支報表呼叫 37 個 SP(`OFDR050` 用兩個:`_EXE` 製作資料、`_GET` 取數),加上被 `S_OTA_OFDR081_GET` 內部呼叫的 `S_OTA_OFDR081T1`(`DB/SP/S_OTA_OFDR081_GET.sql:20`),**38 個檔一個不缺**。另有一個**檔名錯的**:`DB/SP/S_OTA_OFDR601_GET.SQL:1` 的 `CREATE OR REPLACE PROCEDURE SW.S_OTA_OFDR051_GET`——檔名寫 `601`,內容是 `051` 的完整複本(321 行、與 `DB/SP/S_OTA_OFDR051_GET.SQL` 同長)。沒有任何 C# 呼叫 `S_OTA_OFDR601_GET`;它是 `OFDR601A` 開發時複製範本留下的誤名檔(附錄 E)。

欄位說明:**讀的實體表** = 剝掉 `--` / `/* */` 註解後,`FROM` / `JOIN` 後面的識別字,再扣掉 CTE 別名(`X*` `MY*`)與暫存表;**全域暫存表** = 沒有 `USERDOMAIN` 鍵、用 `DELETE 全表` 重建的;**自用暫存表** = 有 `USERDOMAIN` 鍵、以 `SYS_GUID()` 或參數隔離的;**呼叫** = 內部再呼叫的 SP / Function;**INNER / LEFT** = 兩種 JOIN 的次數;**游標** = `OPEN OutTBn FOR` 的個數。

| SP 檔 | 行 | 讀的實體表 | 全域暫存表(寫) | 自用暫存表(寫) | 呼叫 | INNER / LEFT | 游標 |
|---|---|---|---|---|---|---|---|
| `DB/SP/S_OTA_OFDR001_GET.SQL` | 387 | `OFD062` `OFD081` `OFD221` `OFD252` `OFD253` `OFD303` `OFD304` `OFD305` `OFD306` `OFD310` `OFD311` `OFD493` | — | — | — | 2 / 0 | 1 |
| `DB/SP/S_OTA_OFDR002_GET.SQL` | 126 | `OFD062` `OFD081` `OFD303` | — | `OFDR002T1` | `S_OTA_OFDR001_GET` | 3 / 0 | 1 |
| `DB/SP/S_OTA_OFDR003_GET.SQL` | 218 | `BMS001A` `FSK003` `OFD062` `OFD081` `OFD104` `OFD221` `OFD305` `OFD306` | `OFD302AT2` | `OFDR003T1` | `S_TA_IMP_OFD302_RANGE` | 9 / 0 | 1 |
| `DB/SP/S_OTA_OFDR042_GET.SQL` | 931 | `BBS013B` `BMS001A` `BMS999` `COD009` `CRM001A` `CRM002A` `CRM007A` `FSK003` `OFD062` `OFD081` `OFD132A` `OFD221` `OFD251` `OFD252` `OFD253` `OFD254` `OFD300` `OFD302` `OFD305` `OFD306` | `DSMR008T0` `DSMR008T4` `OFD302AT2` `TA_DEPT_EMP` | `OFDR042T1` `OFDR042T2` `OFDR042T4` | `S_TA_IMP_OFD302_RANGE` | 43 / 15 | 5 |
| `DB/SP/S_OTA_OFDR050_EXE.SQL` | 855 | `BMS001A` `FSK003` `OFD020A` `OFD062` `OFD081` `OFD082` `OFD083` `OFD110` `OFD132A` `OFD221` `OFD252` `OFD253` `OFD254` `OFD302` `OFD305` `OFD306` `OFD552` | `DSMR008T0` | `OFDR050T1` `OFDR050T2` `OFDR050T3` `OFDR050T4` `OFDR050T5` `OFDR050T6` `OFDR050T7` `OFDR050T8` `OFDR050T9` | — | 42 / 12 | 1 |
| `DB/SP/S_OTA_OFDR050_GET.SQL` | 242 | (只讀自用暫存表) | — | — | — | 0 / 0 | 9 |
| `DB/SP/S_OTA_OFDR051_GET.SQL` | 321 | `BMS001A` `CTL000` `CTL014` `CTL107` `CTL114` `CTL965` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD220` `OFD221` `OFD224` | `OFD068AT0` | — | — | 8 / 11 | 1 |
| `DB/SP/S_OTA_OFDR052_GET.sql` | 196 | `BMS001A` `FSK003` `OFD019` `OFD030` `OFD062` `OFD071` `OFD081` `OFD199` `OFD220` `OFD221` `OFD300T1` | — | — | `F_TA_GetAgent` `S_TA_IMP_OFD300T1_RANGE2` | 0 / 13 | 1 |
| `DB/SP/S_OTA_OFDR054_GET.SQL` | 357 | `BMS001A` `BMS999` `FSK003` `OFD062` `OFD081` `OFD082` `OFD083` `OFD132A` `OFD221` `OFD305` | `DSMR008T0` `DSMR008T4` | — | — | 27 / 6 | 6 |
| `DB/SP/S_OTA_OFDR057_GET.sql` | 175 | `BMS001A` `CTL000` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD221` `OFD224` | `OFD068AT0` | — | — | 2 / 7 | 1 |
| `DB/SP/S_OTA_OFDR058_GET.sql` | 125 | `BMS001A` `CTL000` `FSK003` `OFD068A_V02` `OFD081` `OFD221` | `OFD068AT0` | — | — | 1 / 3 | 1 |
| `DB/SP/S_OTA_OFDR081_GET.sql` | 376 | `BMS001A` `COD009` `FSK003` `OFD020` `OFD020A` `OFD062` `OFD068A_V01` `OFD081` `OFD251` `OFD252` `OFD253` | `OFD068AT0` | — | `F_TA_GetAgent` `S_OTA_OFDR081T1` `S_TA_IMP_OFD302_RANGE` | 4 / 30 | 5 |
| `DB/SP/S_OTA_OFDR081T1.sql` | 61 | `BMS001A` `COD009` `OFD081` `OFD251` `OFD252` `OFD253` | **`OFDR081T1`**(全表 `DELETE`,無使用者鍵) | — | — | 0 / 8 | 0 |
| `DB/SP/S_OTA_OFDR085_GET.sql` | 352 | `BMS001A` `BMS999` `FSK003` `OFD020V` `OFD062` `OFD081` `OFD082` `OFD083` `OFD132A` `OFD252` `OFD305` | `DSMR008T0` `DSMR008T4` | — | — | 24 / 9 | 6 |
| `DB/SP/S_OTA_OFDR086_GET.sql` | 265 | `BMS001A` `BMS999` `FSK003` `OFD062` `OFD081` `OFD082` `OFD083` `OFD132A` `OFD253` | `DSMR008T0` `DSMR008T4` | — | — | 15 / 5 | 4 |
| `DB/SP/S_OTA_OFDR088_GET.sql` | 117 | `BMS001A` `CTL000` `OFD062` `OFD068A_V02` `OFD081` `OFD251` `OFD252` `OFD253` `OFD254` | `OFD068AT0` | — | — | 1 / 5 | 1 |
| `DB/SP/S_OTA_OFDR089_GET.SQL` | 202 | `BMS001A` `CTL000` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD252` `OFD256` | `OFD068AT0` | — | — | 6 / 3 | 1 |
| `DB/SP/S_OTA_OFDR090_GET.SQL` | 144 | `BMS001A` `CTL000` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD252` | `OFD068AT0` | — | — | 3 / 2 | 1 |
| `DB/SP/S_OTA_OFDR093_GET.sql` | 152 | `BMS001A` `CTL000` `FSK003` `OFD068A_V02` `OFD081` `OFD253` | `OFD068AT0` | — | — | 0 / 6 | 1 |
| `DB/SP/S_OTA_OFDR094_GET.sql` | 177 | `BMS001A` `CTL000` `FSK003` `OFD068A_V02` `OFD081` `OFD253` | `OFD068AT0` | — | — | 3 / 3 | 1 |
| `DB/SP/S_OTA_OFDR109_GET.SQL` | 66 | `BMS001A` `CTL014` `OFD020V` `OFD110` | — | — | — | 1 / 3 | 1 |
| `DB/SP/S_OTA_OFDR111_GET.SQL` | 51 | `BMS001A` `FNDV01` `OFD062` `OFD112` | — | — | — | 1 / 2 | 1 |
| `DB/SP/S_OTA_OFDR131_GET.SQL` | 108 | `BMS001A` `FSK003` `OFD013` `OFD020V` `OFD062` `OFD081` `OFD281` `OFD282` | — | — | — | 1 / 8 | 1 |
| `DB/SP/S_OTA_OFDR132_GET.SQL` | 128 | `BMS001A` `FSK003` `OFD013` `OFD020V` `OFD062` `OFD081` `OFD281` `OFD283` | — | — | `F_OTA_GET_CRNCYAMTDEC` | 1 / 9 | 1 |
| `DB/SP/S_OTA_OFDR133_GET.SQL` | 216 | `BMS001A` `BMS999` `FSK003` `OFD013` `OFD020V` `OFD062` `OFD081` `OFD132A` `OFD281` `OFD283` | `DSMR008T0` | — | — | 6 / 11 | 3 |
| `DB/SP/S_OTA_OFDR134_GET.SQL` | 128 | `BMS001A` `FSK003` `OFD013` `OFD020V` `OFD062` `OFD081` `OFD281` `OFD283` | — | — | `F_OTA_GET_CRNCYAMTDEC` | 1 / 9 | 1 |
| `DB/SP/S_OTA_OFDR551_GET.SQL` | 160 | `BMS001A` `COD009` `FSK003` `OFD019A` `OFD062` `OFD068A_V02` `OFD081` `OFD199` `OFD551` `OFD552` | `OFD068AT0` | — | — | 2 / 7 | 1 |
| `DB/SP/S_OTA_OFDR552_GET.SQL` | 432 | `BMS001A` `COD006A` `FSK003` `OFD062` `OFD081` `OFD551` `OFD552` `OFD554` `OFD555` | — | `OFDR552T1` | `F_OTA_GET_CRNCYAMTDEC` | 5 / 8 | 1 |
| `DB/SP/S_OTA_OFDR553_GET.SQL` | 245 | `BMS001A` `COD006A` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD221` `OFD552` `OFD904` | `OFD068AT0` | — | — | 5 / 13 | 3 |
| `DB/SP/S_OTA_OFDR554_GET.sql` | 355 | `BMS001A` `BMS999` `FSK003` `OFD062` `OFD081` `OFD082` `OFD083` `OFD132A` `OFD221` `OFD305` | `DSMR008T0` `DSMR008T4` | — | — | 27 / 6 | 6 |
| `DB/SP/S_OTA_OFDR601A_GET.SQL` | 170 | `BMS001A` `COD009` `FSK003` `OFD019A` `OFD062` `OFD068A_V02` `OFD081` `OFD199` `OFD601` `OFD620` `OFD621` | `OFD068AT0` | — | — | 5 / 6 | 1 |
| `DB/SP/S_OTA_OFDR602A_GET.SQL` | 146 | `BMS001A` `COD009` `FSK003` `OFD019A` `OFD062` `OFD068A_V02` `OFD081` `OFD601` `OFD651` `OFD652` | `OFD068AT0` | — | — | 5 / 5 | 1 |
| `DB/SP/S_OTA_OFDR603A_GET.SQL` | 175 | `BMS001A` `COD009` `FSK003` `OFD062` `OFD068A_V02` `OFD081` `OFD601` `OFD651` `OFD653` | `OFD068AT0` | — | — | 7 / 4 | 1 |
| `DB/SP/S_OTA_OFDR604A_GET.SQL` | 158 | `BMS001A` `COD009` `CTL014` `FSK003` `OFD019A` `OFD062` `OFD068A_V02` `OFD081` `OFD199` `OFD601` `OFD663` `OFD664` | `OFD068AT0` | — | — | 5 / 8 | 1 |
| `DB/SP/S_OTA_OFDR605A_GET.SQL` | 439 | `BMS001A` `COD006A` `FSK003` `OFD062` `OFD081` `OFD551` `OFD552` `OFD554` `OFD555` `OFD666` `OFD667` | — | `OFDR605AT1` | `F_OTA_GET_CRNCYAMTDEC` | 5 / 8 | 1 |
| `DB/SP/S_OTA_OFDR606A_GET.SQL` | 69 | `CTL014` `OFD601` `OFD607` | — | — | — | 1 / 2 | 1 |
| `DB/SP/S_OTA_OFDR901A_GET.SQL` | 272 | `BMS001A` `COD009` `OFD068A_V000` `OFD081` `OFD221` `SAL071` | `OFD068AT0` | `OFDR901T1` | — | 5 / 5 | 2 |
| `DB/SP/S_OTA_OFDR904_GET.sql` | 627 | `BMS001A` `CTL000` `FSK003` `OFD017A` `OFD068A_V02` `OFD081` `OFD104` `OFD221` `OFD252` `OFD253` `OFD302` `OFD305` `OFD306` `OFD311` | `OFD068AT0` | `OFDR904T1` | — | 4 / 5 | 1 |

38 個檔**全部 cp950 編碼**、全部 `CREATE OR REPLACE PROCEDURE SW.`(schema `SW`)、**全部沒有 `COMMIT`**(交易由 C# 的 `BeginTransaction` / `Commit` 控制)、**只有 `S_OTA_OFDR901A_GET` 有 `EXCEPTION WHEN OTHERS`**(其餘 37 個把例外直接丟回 C#)。

被呼叫的 helper 在不在版控:`S_TA_IMP_OFD302_RANGE`(`DB/SP/S_TA_IMP_OFD302_RANGE.SQL`)是;`F_OTA_GET_CRNCYAMTDEC`(`DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL`)是;`OFD068A_V02`(`DB/View/OFD068A_V02.SQL`)是;**`F_TA_GetAgent` `S_TA_IMP_OFD300T1_RANGE2` `f_FormatStringToTable`(`DB/SP/S_OTA_OFDR133_GET.SQL:43` 用來把逗號串轉表)、`OFD068A_V01` `OFD068A_V000` 不在**。

#### 2.2.2 EC 那軌:8 個全不在版控

| 畫面 | SP | 呼叫端 |
|---|---|---|
| `OFDR601` | `S_EC_IPJR601_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:46` |
| `OFDR602` | `S_EC_IPJR602_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR602OracleDao.cs` |
| `OFDR603` | `S_EC_IPJR603_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR603OracleDao.cs` |
| `OFDR604` | `S_EC_IPJR604_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR604OracleDao.cs` |
| `OFDR605` | `S_EC_IPJR605_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR605OracleDao.cs` |
| `OFDR606` | `S_EC_IPJR606_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR606OracleDao.cs` |
| `OFDR609` | `S_EC_OFDR609_Get`(統計)/ `S_EC_OFDR609D_Get`(明細) | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR609OracleDao.cs:46-53` |

`grep -rli "S_EC_IPJR\|S_EC_OFDR" DB/` 為 0。**EC 那軌的取數邏輯與 `ofdr1.md` 一樣是黑箱**,§7.9 只能從 C# 端反推參數與結果集形狀。另外 7 支死碼的 MSSQL PO 裡寫著 `s_OFDR601_Get` 一類的 T-SQL SP 名(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/MSSQL/OFDR601_PO.cs:54`),那是 MSSQL 時代的名字,整行在註解裡,不算引用。

### 2.3 從 SP 讀出來的實體表:哪些表被幾支報表讀

只算 OTA 38 個 SP(EC 不可知)。**被讀次數 ≥ 5 的表**:

| 表 | 讀它的 SP 數(/37) | 推測用途(依欄位名) | 誰建的(哪一片) |
|---|---|---|---|
| `BMS001A` | **34** | 受益人主檔(`BF_NO` `ID_NO` `BF_NAME` `TDCC_BF_NO` `MAIL_ADDR` `CELL_PHONE`) | BMS(`bms.md`) |
| `OFD081` | **34** | 境外基金主檔(`FUND_ID` `FUND_SH_NM` `FH_CD` `UNIT_DEC` `NAV_DEC` `PROF_TYPE` `AFEE_TYPE` `FUND_STATUS`) | OFD 基金維護(`ofd123.md`) |
| `FSK003` | 29 | 幣別(`CRNCY_CD` `CRNCY_NM` `DEC_LEN`) | 共用代碼 |
| `OFD062` | 29 | 基金公司(`FH_CD` `FH_NM_SH_C`) | OFD |
| `OFD068A_V02` | 15 | 銷售機構名稱 View(`AGENT_ID` `AGENT_CODE` `BANK_HQ_SHNM`),每次被複製進 `OFD068AT0` | `DB/View/OFD068A_V02.SQL` |
| `OFD221` | 13 | 申購交易 | OFD 申購(`ofd4.md`) |
| `OFD252` `OFD253` | 10 / 10 | 贖回交易(個人 / 綜合) | OFD 贖回(`ofd5.md`) |
| `COD009` | 9 | 員工(`EMP_NO` `EMP_NAME` `UID_CODE` `DEPT_NO`) | COD(`cod.md`) |
| `CTL000` | 9 | 公司短名 `INC_SHORT_NAME` | CTL |
| `OFD305` `OFD306` | 8 / 5 | 結餘單位數 | 結帳批次(`ofdb.md`) |
| `OFD132A` | 7 | 寄發設定(`STATEMENT_CODE` `SEND_CODE` `SEND_POST` `SEND_EMAIL` `SEND_FAX` `SEND_COLLECT`) | OFD |
| `BMS999` | 6 | 受益人擴充(**假設**,只見 JOIN) | BMS |
| `OFD020V` | 6 | 銀行 View(**假設**,`ofdr1.md` 同名) | 版控外 |
| `OFD082` `OFD083` | 5 / 5 | 費率(`TRAILER_RATE` `ACP_DATE`) | OFD |
| `OFD552` | 5 | 定期定額契約 | OFD 定期定額(`ofd7.md`) |
| `OFD601` | 5 | 網路交易客戶 | EC / OTA 網路交易 |
| `CTL014` | 4 | 代碼表(`SOURCETYPE` `TEXTVALUE` `DISPLAYNAME`) | CTL |
| `OFD013` `OFD019A` `OFD251` | 4 / 4 / 4 | 基金設定 / 銀行 / 贖回主檔 | OFD |

其餘 50 幾張只被 1~3 支讀,74 張全表列在附錄 A。

### 2.4 暫存表:兩種設計,一種安全一種不安全

OTA 38 個 SP 有 **26 個會寫表**。寫的全部是暫存 / 工作表,**沒有任何一個 SP 寫業務主檔**。但暫存表分兩種:

| 種類 | 表 | 隔離方式 | 寫它的 SP 數 | 錨點(例) | 風險 |
|---|---|---|---|---|---|
| **自用**(安全) | `OFDR002T1` `OFDR003T1` `OFDR042T1` `OFDR042T2` `OFDR042T4` `OFDR050T1`~`OFDR050T9` `OFDR552T1` `OFDR605AT1` `OFDR901T1` `OFDR904T1` | 有 `USERDOMAIN` 欄;SP 開頭 `xUSERDOMAIN := SYS_GUID()` 或由 C# 傳入,`DELETE ... WHERE USERDOMAIN = x` → `INSERT` → `OPEN` → 結尾再 `DELETE` | 8 | `DB/SP/S_OTA_OFDR002_GET.SQL:51-55` · `:98-99` · `:123` | 低。**注意 `OPEN OutTB1 FOR` 之後才 `DELETE`**(`:103-123`):Oracle 游標在 `OPEN` 時固定 SCN,客戶端 fetch 仍讀得到;換成 SQL Server 就不是這樣 |
| **全域**(不安全) | **`OFD068AT0`**(銷售機構名稱) | **無使用者鍵**。`DELETE OFD068AT0; INSERT INTO OFD068AT0 SELECT ... FROM OFD068A_V02` | **18** | `DB/SP/S_OTA_OFDR601A_GET.SQL:36-39` · `DB/SP/S_OTA_OFDR088_GET.sql:43-46` | 兩人同時印任兩支,後者 `DELETE` 清掉前者剛塞的列;前者的 `LEFT JOIN OFD068AT0` 對不到 → **銷售機構名稱印成空白**(附錄 E2) |
| 全域(不安全) | **`DSMR008T0`**(使用者勾的基金清單) | 無使用者鍵。`DELETE DSMR008T0; INSERT ... FROM TABLE(f_FormatStringToTable(xFUND_ID))` | 7 | `DB/SP/S_OTA_OFDR133_GET.SQL:40-43` | 主查詢 `INNER JOIN DSMR008T0`(`:84-85`)→ 被別人清掉就**整張報表零筆或印成別人勾的基金**(E1) |
| 全域(不安全) | **`DSMR008T4`**(可查詢戶號)+ **`TA_DEPT_EMP`**(資料權限) | 無使用者鍵 | 5 / 1 | `DB/SP/S_OTA_OFDR042_GET.SQL:493-495` · `:514-515` | **資料權限用全域表算**,兩個非豁免部門的人同時印對帳單,後者的權限集蓋掉前者的 → 越權或漏印(E1) |
| 全域(不安全) | `OFDR081T1`(贖回日報暫存) | 無使用者鍵,`DELETE FROM OFDR081T1` 全表 | 1 | `DB/SP/S_OTA_OFDR081T1.sql:14-16` | 兩人同時印 `OFDR081` 互蓋 |
| 全域(半安全) | `OFD302AT2`(淨值區間快取) | 由 `S_TA_IMP_OFD302_RANGE` 重建,再 `DELETE` 掉不要的 | 5 | `DB/SP/S_OTA_OFDR003_GET.SQL:75-82` | 同上,但淨值資料兩人重建的內容大致相同,影響小 |

**上表沒有一張在 `DB/Table/`。** 158 個變更腳本裡 `grep -i "OFD068AT0\|OFDR0\|DSMR008\|TA_DEPT_EMP"` 為 0——這些工作表的 DDL 不在版控,只能從 SP 的 `INSERT INTO ...(欄位)` 反推欄位。

### 2.5 參數化程度與自組 SQL

**36 支 OTA PO 全部走 `GetStoredProcCommand` + `AddInParameter`**,參數名一律 `i<欄名>`(SP 端同名),出參 `OutTB1`~`OutTB9`(`OracleDbType.RefCursor`)。另有 **8 支在 PO 內自組 SQL**(`GetSqlStringCommand`),條件值走 `:參數` 綁定;**只有 `OFDR085` `OFDR086` 兩支把 UI 勾選的基金清單串進 `IN (...)`**——UI 端 `"('" + FundList.Replace(",", "', '") + "')"`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR085.cs:238`)→ PO 端 `"AND OFD252.FUND_ID IN " + xFUND_ID_LIST`(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR085_PO.cs:137` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR086_PO.cs:132`)。值來自 grid 的 `FUND_ID` 欄不是鍵盤輸入,注入風險低,但基金代碼含單引號就會炸(附錄 E):

| 畫面 | 自組 SQL 做什麼 | 讀的表 | 綁定 | 錨點 |
|---|---|---|---|---|
| `OFDR002` | 列印前檢核:該基金公司該日的基金是否全部已過帳(`POST_CTL_CODE = 'N'` 就擋) | `OFD081` `OFD303` | `:FH_CD` `:CTL_DATE` | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:126-138` |
| `OFDR050` | 製作資料前檢核:綜合帳戶贖回是否已做分配確認(`OFDB090`)、該交易日是否已有資料 | `OFD252` `OFD253` `BMS001A` `OFD132A` `OFD303` `OFDR050T6` | `:ALLOT_DATE` `:SEND_CODE` `:BF_NO` | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:74-120` · `:143-152` |
| `OFDR085` `OFDR086` | `Is_OFD303_DONE`:勾選的基金在該贖回日是否已做綜合帳戶分配確認(`OFD303.OMNIBUS_PCD_R = '1'`) | `OFD252` / `OFD253` `OFD303` | **`IN` 清單串接**,其餘 `:REDEM_DATE` `:BF_NO` 綁定 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR085_PO.cs:121-164` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR086_PO.cs:132` |
| `OFDR042` | 兩段列印前檢核:(a) `OFD303.OMNIBUS_PCD_A/R/S` 有非 `'0'` `'2'` 者 → 「請先進行綜合帳戶分配確認!!」;(b) `POST_CTL_CODE = 'N'` → 「請先進行結轉!!」 | `OFD303` | 綁定 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR042_PO.cs:148-155` · `:190-195` |
| `OFDR131` `OFDR132` `OFDR134` | 填「記錄日」下拉(選基金後撈 `OFD281` / `OFD283` 的日期) | `OFD281` `OFD283` | 綁定 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR131_PO.cs` |

自組 SQL 裡的 `NVL(:FH_CD, OFD081.FH_CD)` 樣板(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:131`)與 SP 內 164 處 `欄 = NVL(i參數, 欄)`(37 / 38 個 SP 都有)是同一種 Oracle 三值邏輯:**該欄為 NULL 的列在「不篩」時也會消失**(附錄 E5)。

EC 7 支活的 PO 也全部 `AddInParameter` 綁定。5 支帶字串串接的 `DoDeleteTempTable`(`"DELETE " + TableName + " WHERE USERDOMAIN = '" + xUSERDOMAIN + "'"`,`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:157`)**沒有任何呼叫端**(`grep DoDeleteTempTable` 只找到定義),串進去的也是 `Guid.NewGuid()` 不是使用者輸入。

### 2.6 參數命名慣例:兩軌兩套

| 層 | OTA(36 支) | EC(7 支活的) |
|---|---|---|
| UI → `Util.Parameters` 的 key | 純欄名 `FUND_ID` `ALLOT_DATE_ST`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:174-181`) | **帶 T-SQL 前綴** `@strFUND_ID` `@dateALLOT_DATE_ST` `@decEC_BF_NO_ST`(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:104-112`);`OFDR604` `OFDR609` 例外用純欄名 |
| PO 取值 | `EVAStringHelper.GetParamValue(model, "FUND_ID")` | `foreach (rrRow in Parameters.Rows) if (rrRow.Name == "@strFUND_ID")` |
| PO → SP 參數名 | `iFUND_ID` | `wFUND_ID`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:54`);`OFDR609` 直接用欄名 `P_CODE` `O_CODE` `DATE_Start` |
| 日期 | `DateTimeHelper.DateToString` → `yyyyMMdd` 字串,SP 端 `VARCHAR2` 比對 | `ToString("yyyy/MM/dd")` 字串,PO 端再 `ConvertTo.DateTimeorDBNull` 轉 `OracleDbType.Date`;**`"1900/01/01"` 當「未輸入」哨兵值**(`:58-59`) |
| 「全部」 | OTA 用 `'A'`(`OMNIBUS_ID` `EC_ALLOT_PCODE`),SP 端 `NVL(i, 'A')` 再 `CASE` | EC 用空字串或不傳 |

EC 的 `@str` / `@date` / `@dec` 前綴是 MSSQL 時代 `SqlDbType` 對映留下的,Oracle 版 PO 只把 `@` 換成 `w` 送進 SP,**UI 端的 key 沒改**。

### 2.7 `.rpt` 對應表

#### 2.7.1 對應規則

兩軌後綴慣例不同:

| 軌 | 樣式 | 例 |
|---|---|---|
| OTA | **一律 `<代號>RPS<n>`,`n` 從 1 起**,單版型也叫 `RPS1` | `OFDR001BRPS1` `OFDR904RPS1`~`RPS4` |
| EC | 第一張**無數字** `<代號>RPS`,第二張起 `RPS2` `RPS3`;`OFDR690` 例外從 `RPS1` 起 | `OFDR601RPS` `OFDR601RPS2` `OFDR601RPS3` |

伴生 `.cs` 的檔名也有例外:`OFDR042RPS1`~`RPS4` 與 `OFDR057RPS1` `RPS2` 的伴生檔叫 **`OFDR042RPS11.cs`** `OFDR042RPS21.cs`…、`OFDR057RPS11.cs` `OFDR057RPS21.cs`(多一個 `1`),類別名仍是 `OFDR042RPS1`(`Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/OFDR042RPS11.cs:19`); `OFDR042` 另有一套 `OFDR042RPS1.cs`~`RPS4.cs` 躺在磁碟上**但不在 csproj**(`Report.OTA.csproj` 只掛 `RPS11`~`RPS41`,`Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/Report.OTA.csproj:221-239`),類別名相同——若兩者都掛會重複定義,所以那 4 個是廢檔。

#### 2.7.2 版控狀況:OTA 67 個 `.rpt` 全在 csproj、**2 個引用懸空**;EC 42 個全在、0 懸空

`Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/` 實有 **67 個 `.rpt`**,66 個以 `EmbeddedResource` 進 `Report.OTA.csproj`,1 個(`OTAR901RPS1.rpt`,不在本片)以 `None` 進(`Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/Report.OTA.csproj:500`)。 `Dev/ATLAS.EC.Report/Source/CrystalReports/Report.EC/` 實有 **42 個**,全部 `EmbeddedResource`。兩個專案都另有 PostBuildEvent 把 `*.rpt` xcopy 到 `C:\Program Files\Vendor\PTPFBlock\CrystalReports\`(`Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/Report.OTA.csproj:795` · `Dev/ATLAS.EC.Report/Source/CrystalReports/Report.EC/Report.EC.csproj:551`),與 `architecture.md §6` 記的兩條交付路徑相同。

欄位:**UI 要的** = `SetQueryParameters` 第一參;**實有** = 資料夾內 `<代號>RPS*.rpt` 個數;**在 csproj** = 其中進 `EmbeddedResource` 的;**懸空** = UI 要但檔案不存在;**沒人要** = 檔案在、UI 沒引用(可能是子報表,見下)。

| 畫面 | UI 要的 | 實有 | 在 csproj | 懸空 | 沒人要 |
|---|---|---|---|---|---|
| `OFDR001B` | `OFDR001BRPS1` | 1 | 1 | — | — |
| `OFDR002` | `OFDR002RPS1` | 1 | 1 | — | — |
| `OFDR003` | `OFDR003RPS1` | 1 | 1 | — | — |
| `OFDR042` | `OFDR042RPS1` | 4 | 4 | — | `OFDR042RPS2` `OFDR042RPS3` `OFDR042RPS4` |
| `OFDR050` | `OFDR050RPS1` | 0 | 0 | **`OFDR050RPS1`** | — |
| `OFDR051` | `OFDR051RPS1` | 1 | 1 | — | — |
| `OFDR052` | `OFDR052RPS1` `OFDR052RPS2` `OFDR052RPS3` | 3 | 3 | — | — |
| `OFDR054` | `OFDR054RPS1` | 5 | 5 | — | `OFDR054RPS2` `OFDR054RPS3` `OFDR054RPS4` `OFDR054RPS5` |
| `OFDR057` | `OFDR057RPS1` `OFDR057RPS2` | 2 | 2 | — | — |
| `OFDR058` | `OFDR058RPS1` `OFDR058RPS2` | 2 | 2 | — | — |
| `OFDR081` | `OFDR081RPS1` | 4 | 4 | — | `OFDR081RPS2` `OFDR081RPS3` `OFDR081RPS4` |
| `OFDR085` | `OFDR085RPS1` | 4 | 4 | — | `OFDR085RPS2` `OFDR085RPS3` `OFDR085RPS4` |
| `OFDR086` | `OFDR086RPS1` | 3 | 3 | — | `OFDR086RPS2` `OFDR086RPS3` |
| `OFDR088` `OFDR089` `OFDR090` `OFDR093` `OFDR094` `OFDR109` `OFDR111` `OFDR131` `OFDR132` `OFDR133` `OFDR134` `OFDR552` | 各自 `RPS1` | 1 | 1 | — | — |
| `OFDR551` | `OFDR551RPS1` `OFDR551RPS2` | 2 | 2 | — | — |
| `OFDR553` | `OFDR553RPS1` `OFDR553RPS2` `OFDR553RPS3` | 3 | 3 | — | — |
| `OFDR554` | `OFDR554RPS1` | 5 | 5 | — | `OFDR554RPS2` `OFDR554RPS3` `OFDR554RPS4` `OFDR554RPS5` |
| `OFDR601A`~`OFDR606A` | 各自 `RPS1` | 1 | 1 | — | — |
| `OFDR901A` | `OFDR901ARPS1` | 0 | 0 | **`OFDR901ARPS1`** | — |
| `OFDR904` | `OFDR904RPS1`~`OFDR904RPS4` | 4 | 4 | — | — |
| `OFDR601` `OFDR602` `OFDR603` | 各自 `RPS` `RPS2` `RPS3` | 3 | 3 | — | — |
| `OFDR604` `OFDR605` `OFDR606` | 各自 `RPS` `RPS3` | 2 | 2 | — | — |
| `OFDR607` | `OFDR607RPS` `OFDR607RPS2` `OFDR607RPS3` | 3 | 3 | — | —(UI 本身是死碼) |
| `OFDR608` | `OFDR608RPS` `OFDR608RPS2` | 2 | 2 | — | — |
| `OFDR609` | `OFDR609RPS` `OFDR609RPS2` `OFDR609RPS3` `OFDR609RPS4` | 4 | 4 | — | — |
| `OFDR610` `OFDR611` `OFDR612` `OFDR613` | 各自 `RPS` | 1 | 1 | — | — |
| `OFDR690` | `OFDR690RPS1`~`OFDR690RPS5` | 5 | 5 | — | — |

三件事:

1. **兩支懸空**:`OFDR050` 要 `OFDR050RPS1`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:228`)、`OFDR901A` 要 `OFDR901ARPS1`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:134`),**檔案、伴生 `.cs`、csproj 宣告三者皆無**。UI 只用字串名,編譯不會錯;按預覽時 `CRReportTransfer.TransferFileByte` 找不到檔才失敗(附錄 E4)。對照 `ofdr1.md` 的 `OFDR716RPS2`,本片是 2 個。

2. **19 個「沒人要」的 `.rpt`** 集中在 6 支確認書 / 對帳單(`OFDR042` `OFDR054` `OFDR081` `OFDR085` `OFDR086` `OFDR554`)。這 6 支的 SP 都回 3~6 個游標,UI 只 `SetQueryParameters` 一次 `RPS1`——**假設**它們是 `RPS1` 內嵌的子報表(Crystal 主報表 + 子報表各存一檔是常見做法)。但用 ASCII 與 UTF-16LE 兩種方式在 `RPS1.rpt` 二進位內找 `OFDR042RPS2` 等字串都找不到,無法從版控內證實;**也可能是廢版型**。要確認得開 Crystal Designer。

3. **EC 42 / 42 零缺陷**,與 `nfdr1.md` 的 79 / 79 同級——因為那 7 支死碼的 `.rpt` 與伴生 `.cs` 都還乖乖掛在 `Report.EC.csproj`,只有 UI 那層被拔掉。

### 2.8 C# 裡看得見的表(只有 14 張)

50 支 PO 的 C# 文字內出現的表名(自組 SQL):`OFD081` `OFD303` `OFD252` `OFD253` `OFD132A` `BMS001A` `OFDR050T6` `OFD281` `OFD283`(OTA)、`IPJR601T1` `IPJR601T2`(EC 死方法內)。其餘全在 SP 內。 **EC 那軌 C# 內 0 張活的表名**——連自組 SQL 都沒有,是純 SP 呼叫端。

### 2.9 欄位中文名

OTA 那軌的 Model.xsd 有中文 `msdata:Caption`(`Dev/ATLAS.OTA.Report/Source/Entity/ReportDataEntity.OTA/OFDR601AModel.xsd` 47 個欄位全帶,例「申購日期」「申購淨值日」「網路申購書號」「境外基金公司代碼」),**但 R 的 Caption 沒有人讀**——Crystal 的欄位標題存在 `.rpt` 內部,`TransferVDBHelper.TransferDataSet` 只搬值不搬 Caption。所以本片不做「欄位中文名總表」;要改報表欄位標題得開 `.rpt`,改 xsd 的 Caption 沒用。報表抬頭的中文由 UI `SetParameterValue` 補(§0.5 第 9 步)。

### 2.10 狀態碼(從 SP 與 UI 反推)

| 碼 | 值 | 意義 | 來源 |
|---|---|---|---|
| `OMNIBUS_ID` | `A` / `N` / `Y` | 全部 / 個人帳戶 / 綜合帳戶 | `DB/SP/S_OTA_OFDR601A_GET.SQL:3` · `:59-60` |
| `EC_ALLOT_PCODE` | `A` / `0` / `1` / `2` / `4` | 全部 / 輸入 / 處理中 / 下單成功 / 刪除 | `DB/SP/S_OTA_OFDR601A_GET.SQL:4` |
| `TRAN_PAY_WAY` | `A` / `01` / `02` | 全部 / 匯款 / 扣款 | `DB/SP/S_OTA_OFDR601A_GET.SQL:5` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR052.cs:116-118` |
| `SYSTEM_ID` | `99` / `0` / `1` | 全部 / 實體 / EC | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR052.cs:124-126` |
| `AGENT_ID` | `' '` / `0`~`5` | 公司自銷 / 公 / 銀 / 券 / 顧 / 信 / 產 | `DB/SP/S_OTA_OFDR088_GET.sql:98-107` |
| `POST_CTL_CODE` | `N` | 未過帳(不可印) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:148` |
| `REDEM_PROC_CODE` | `5` | 贖回已確認(可印確認書) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:85` |
| `STATEMENT_CODE` | `0100` / `0130` | 交易確認書 / 配息通知書(`OFD132A` 寄發設定類別) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:82` · `DB/SP/S_OTA_OFDR133_GET.SQL:82` |
| `REPORTTYPE`(EC) | `1` / `2` / `3` | 彙總(前置核對)/ 明細(委託查核)/ 比對異常 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:104-119` |
| `CTL014.SOURCETYPE` | `960` / `948` | 網路交易進度 / 付款方式代碼 | `DB/SP/S_OTA_OFDR606A_GET.SQL:29` · `:36` |

## 3. 畫面清冊

```text
[圖] 50 支依專案、PO 派別、SP 與 rpt 版控狀態分成三塊
圖中文字:50 支依「能不能跑」「PO 派別」「SP 在不在版控」分三塊 / OTA 36 支 全部能跑 / I 代號 PO 派 m_db 宣告即初始化 / SP 37 / 37 在版控 / 4 支借別支 xsd 002 058 132 134 / .rpt 44 引用 2 懸空 / OFDR050RPS1 OFDR901ARPS1 / EC 活的 7 支 / OracleDao : I 代號 PO db 建構子初始化 / SP 0 / 8 在版控 / 每支兩套 xsd 一死一活 / .rpt 33 / 33 全在 / DoDeleteTempTable 死方法 5 支 / EC 死的 7 支 / UI Ctl Pxy 不在 csproj / PO 整檔 // 註解 / MSSQL 版 Basic_PO 派 未遷 Oracle / .rpt 與 xsd 仍在 csproj / 磁碟 14 支 能跑 7 支 / ofdr1.md 那條 Basic_PO m_db 死碼線:本片 0 支 / 三項佐證反向全成立 / PODbType Oracle 43 支 new Database 43 支 SqlDbType 0 處 / 對照 OFD 13/40 NFD 16/44 / 本片 OTA 0/36 EC 0/7
```

*圖:圖 4 三塊分群,對應 §3.4 清冊與 §3.5。左塊 OTA 36 支結構整齊,只有 2 個 .rpt 懸空;中塊 EC 活的 7 支能跑但 SP 是黑箱;右塊 EC 死的 7 支整塊紫,磁碟上看得到、DLL 裡沒有。底排是交辦第 6 題的答案:m_db 死碼線本片 0 支。*

### 3.1 維護 M

(本片無此類畫面)——切片依型別碼取 R,兩個 `.Report` 方案內也沒有 M。

### 3.2 查詢 I

(本片無此類畫面)——同上;OTA / EC 的 I 畫面在 `ATLAS.OTA.Query` / `ATLAS.EC.Query`,由 `ofdi1.md` `ofdi2.md` 涵蓋。

### 3.3 批次 B

(本片無此類畫面)——OTA 的 B 畫面在 `ATLAS.OTAB`,`ofdb5.md` 已寫。

### 3.4 報表 R(50 支)

欄位說明:

- **報表中文名**:`SetQueryParameters` 第三參字面值。多版型的取 UI 內第一個分支;完整對應看 §2.7。

- **PO 基底**:剝 `//` 註解後 `class X : Y` 的 `Y`。EC 那 7 支死碼的 PO 整檔在註解裡,標「(整檔註解)」。

- **`m_db`**:`有初始化` = 宣告或建構子內 `new Database("TA", DbServerType.Oracle)`;本片 43 支活的 PO 全是。**沒有一支是 `ofdr1.md §7.12.2` 那種宣告即 null 的死碼線**(三種變體 `= null;` / `;` / `readonly ... ;` 都掃過,0 命中)。

- **資料來源**:`SP` = 只有 `GetStoredProcCommand`;`SP+SQL` = 另有 `GetSqlStringCommand`。

- **SP 在版控**:OTA 37 個 `S_OTA_OFDR*` 全在 `DB/SP/`;EC 8 個全不在。

- **`.rpt`**:`在 csproj / 實有`;UI 要但檔不存在的標 **缺**。

- **條件**:`綁定` = `AddInParameter`;`OFDR085` `OFDR086` 的 `IN` 清單串接見 §2.5,但條件值本身仍綁定。

- **在 csproj**:UI / Ctl / Pxy 三層是否都在對應 csproj 內。

| 代號 | 軌 | 報表中文名 | PO 基底 | `m_db` | 來源 | SP | SP 在版控 | `.rpt` | 條件 | 在 csproj |
|---|---|---|---|---|---|---|---|---|---|---|
| `OFDR001B` | OTA | 境外基金結餘單位數檢核表 | `IOFDR001B_PO` | 有初始化 | SP | `S_OTA_OFDR001_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR002` | OTA | 境外基金結餘單位數查核清冊 | `IOFDR002_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR002_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR003` | OTA | 境外基金受益人結餘清冊 | `IOFDR003_PO` | 有初始化 | SP | `S_OTA_OFDR003_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR042` | OTA | 境外基金交易對帳單 | `IOFDR042_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR042_GET` | 是 | 4/4 | 綁定 | 是 |
| `OFDR050` | OTA | 境外交易確認書 | `IOFDR050_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR050_EXE`, `S_OTA_OFDR050_GET` | 是 | 0/0 **缺 `OFDR050RPS1`** | 綁定 | 是 |
| `OFDR051` | OTA | 總代理-申購明細表列印作業 | `IOFDR051_PO` | 有初始化 | SP | `S_OTA_OFDR051_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR052` | OTA | 銷售機構-申購明細表 | `IOFDR052_PO` | 有初始化 | SP | `S_OTA_OFDR052_GET` | 是 | 3/3 | 綁定 | 是 |
| `OFDR054` | OTA | 境外基金申購確認書 | `IOFDR054_PO` | 有初始化 | SP | `S_OTA_OFDR054_GET` | 是 | 5/5 | 綁定 | 是 |
| `OFDR057` | OTA | 境外個人帳戶申購試算檢核清單 | `IOFDR057_PO` | 有初始化 | SP | `S_OTA_OFDR057_GET` | 是 | 2/2 | 綁定 | 是 |
| `OFDR058` | OTA | 境外綜合帳戶申購試算檢核清單 | `IOFDR058_PO` | 有初始化 | SP | `S_OTA_OFDR058_GET` | 是 | 2/2 | 綁定 | 是 |
| `OFDR081` | OTA | 贖回交易日報表(境外) | `IOFDR081_PO` | 有初始化 | SP | `S_OTA_OFDR081_GET` | 是 | 4/4 | 綁定 | 是 |
| `OFDR085` | OTA | 境外基金買回確認書 | `IOFDR085_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR085_GET` | 是 | 4/4 | 綁定 + `IN` 串接 | 是 |
| `OFDR086` | OTA | 境外基金轉換確認書 | `IOFDR086_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR086_GET` | 是 | 3/3 | 綁定 + `IN` 串接 | 是 |
| `OFDR088` | OTA | 境外贖回沖銷明細表 | `IOFDR088_PO` | 有初始化 | SP | `S_OTA_OFDR088_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR089` | OTA | 個人帳戶贖回試算檢核清單 | `IOFDR089_PO` | 有初始化 | SP | `S_OTA_OFDR089_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR090` | OTA | 綜合帳戶贖回試算檢核清單 | `IOFDR090_PO` | 有初始化 | SP | `S_OTA_OFDR090_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR093` | OTA | 境外個人帳戶轉換試算檢核清單 | `IOFDR093_PO` | 有初始化 | SP | `S_OTA_OFDR093_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR094` | OTA | 境外綜合帳戶轉換試算檢核清單 | `IOFDR094_PO` | 有初始化 | SP | `S_OTA_OFDR094_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR109` | OTA | 境外受益人銀行帳戶資料查核表 | `IOFDR109_PO` | 有初始化 | SP | `S_OTA_OFDR109_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR111` | OTA | 境外受益人綜合帳戶資料查核表 | `IOFDR111_PO` | 有初始化 | SP | `S_OTA_OFDR111_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR131` | OTA | 基金受益分配試算明細表 | `IOFDR131_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR131_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR132` | OTA | 總代理-受益分配明細表 | `IOFDR132_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR132_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR133` | OTA | 境外基金配息通知書 | `IOFDR133_PO` | 有初始化 | SP | `S_OTA_OFDR133_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR134` | OTA | 銷售機構-受益分配明細表 | `IOFDR134_PO` | 有初始化 | SP+SQL | `S_OTA_OFDR134_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR551` | OTA | 境外定期定額契約資料查核表列印作業 | `IOFDR551_PO` | 有初始化 | SP | `S_OTA_OFDR551_GET` | 是 | 2/2 | 綁定 | 是 |
| `OFDR552` | OTA | 境外定期定額契約異動資料查核表列印作業 | `IOFDR552_PO` | 有初始化 | SP | `S_OTA_OFDR552_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR553` | OTA | 境外定期定額產生扣款資料明細表 | `IOFDR553_PO` | 有初始化 | SP | `S_OTA_OFDR553_GET` | 是 | 3/3 | 綁定 | 是 |
| `OFDR554` | OTA | 境外基金定額確認書 | `IOFDR554_PO` | 有初始化 | SP | `S_OTA_OFDR554_GET` | 是 | 5/5 | 綁定 | 是 |
| `OFDR601A` | OTA | 境外網路交易申購檢核列印作業 | `IOFDR601A_PO` | 有初始化 | SP | `S_OTA_OFDR601A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR602A` | OTA | 境外網路交易買回檢核表列印作業 | `IOFDR602A_PO` | 有初始化 | SP | `S_OTA_OFDR602A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR603A` | OTA | 境外網路交易轉申購檢核表列印作業 | `IOFDR603A_PO` | 有初始化 | SP | `S_OTA_OFDR603A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR604A` | OTA | 境外網路交易定額契約檢核表列印作業 | `IOFDR604A_PO` | 有初始化 | SP | `S_OTA_OFDR604A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR605A` | OTA | 境外網路交易定額異動檢核表列印作業 | `IOFDR605A_PO` | 有初始化 | SP | `S_OTA_OFDR605A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR606A` | OTA | 境外網路交易客戶明細表 | `IOFDR606A_PO` | 有初始化 | SP | `S_OTA_OFDR606A_GET` | 是 | 1/1 | 綁定 | 是 |
| `OFDR901A` | OTA | 境外期間手續費獎金明細表 | `IOFDR901A_PO` | 有初始化 | SP | `S_OTA_OFDR901A_GET` | 是 | 0/0 **缺 `OFDR901ARPS1`** | 綁定 | 是 |
| `OFDR904` | OTA | Monthly Aum Report --By 基金分類 | `IOFDR904_PO` | 有初始化 | SP | `S_OTA_OFDR904_GET` | 是 | 4/4 | 綁定 | 是 |
| `OFDR601` | EC | 網路申購前置核對表 | `IOFDR601PO` | 有初始化 | SP | `S_EC_IPJR601_GET` | **否** | 3/3 | 綁定 | 是 |
| `OFDR602` | EC | 網路買回前置核對表 | `IOFDR602PO` | 有初始化 | SP+SQL | `S_EC_IPJR602_GET` | **否** | 3/3 | 綁定 | 是 |
| `OFDR603` | EC | 線上轉申購檢核表 | `IOFDR603PO` | 有初始化 | SP+SQL | `S_EC_IPJR603_GET` | **否** | 3/3 | 綁定 | 是 |
| `OFDR604` | EC | 網路定期定額申購委託資料查核表 | `IOFDR604PO` | 有初始化 | SP+SQL | `S_EC_IPJR604_GET` | **否** | 2/2 | 綁定 | 是 |
| `OFDR605` | EC | 網路定期定額異動委託資料查核表 | `IOFDR605PO` | 有初始化 | SP+SQL | `S_EC_IPJR605_GET` | **否** | 2/2 | 綁定 | 是 |
| `OFDR606` | EC | 網路受益人資料異動委託資料查核表 | `IOFDR606PO` | 有初始化 | SP | `S_EC_IPJR606_GET` | **否** | 2/2 | 綁定 | 是 |
| `OFDR607` | EC | 受益人異動拋轉狀態查核表 | (整檔註解) | 無 PO | — | — | — | 3/3 | 綁定 | **否** |
| `OFDR608` | EC | 網路額度控管表 | (整檔註解) | 無 PO | — | — | — | 2/2 | 綁定 | **否** |
| `OFDR609` | EC | 網路交易開戶統計資料 | `IOFDR609PO` | 有初始化 | SP | `S_EC_OFDR609D_Get`, `S_EC_OFDR609_Get` | **否** | 4/4 | 綁定 | 是 |
| `OFDR610` | EC | 網路交易申購扣款總表 | (整檔註解) | 無 PO | — | — | — | 1/1 | 綁定 | **否** |
| `OFDR611` | EC | 網路交易申購扣款結果一覽表 | (整檔註解) | 無 PO | — | — | — | 1/1 | 綁定 | **否** |
| `OFDR612` | EC | 網路交易申購扣款失敗明細表 | (整檔註解) | 無 PO | — | — | — | 1/1 | 綁定 | **否** |
| `OFDR613` | EC | 網路交易扣款行回覆統計資料 | (整檔註解) | 無 PO | — | — | — | 1/1 | 綁定 | **否** |
| `OFDR690` | EC | 網路員工交易申購審核明細表 | (整檔註解) | 無 PO | — | — | — | 5/5 | 綁定 | **否** |

EC 那 4 支 `SP+SQL` 的 `GetSqlStringCommand` 全在死方法 `DoDeleteTempTable` 內(§7.9),活路徑仍是純 SP。 `OFDR081` 的中文名字面值是 `贖回交易日報表(境外)`,是本片唯一把「境外」放在括號後綴、而不是前綴的(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR081.cs:149`)。 `OFDR904` 四張的中文名是英文 `Monthly Aum Report`,第四張還拼錯(`Rport`,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR904.cs:148`);Excel 檔名再拼錯一次(`OFDR904RP31`,`:296`)。 `OFDR606`(EC)第二個版型的中文名少一個字:`路受益人資料異動委託資料比對異常報表`(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR606.cs:63`)。

### 3.5 從清冊讀出來的七件事

1. **`m_db` 死碼線 0 支。** OTA 36 支宣告即 `new Database(...)`,EC 7 支建構子內 `new`。`ofdr1.md`(13 / 40)與 `nfdr1.md`(16 / 44)那條最高嚴重度的缺陷型,在本片**兩軌都不存在**。三項佐證反過來全成立:36 + 7 支全有 `[PODbType(DbServerType.Oracle)]`、全有 `new Database("TA", DbServerType.Oracle)`、只用 `OracleDbType` 不用 `SqlDbType`(`grep -c SqlDbType` 在兩個活 PO 資料夾都是 0;`SqlDbType` 只出現在 EC `MSSQL/` 那 14 個註解檔內)。

2. **SP 在版控:OTA 37 / 37,EC 0 / 8。** `ofdb5.md` 記「OTAB 是唯一把 SP 進版控的專案(7 支)」——**要改寫:OTA 整個子軌(含 `OTAB` 的 B 與本片的 R)都把 SP 進了版控**,`DB/SP/` 83 個檔裡 78 個是 `S_OTA_*`。OFD(0 / 71)、NFD(1 / 60)、EC(0 / 8)都沒有。這是 OTA 改版時的紀律,不是平台慣例。

3. **EC 7 支死碼**:`OFDR607` `OFDR608` `OFDR610` `OFDR611` `OFDR612` `OFDR613` `OFDR690`。UI / Ctl / Pxy / xsd / `.rpt` 檔都在磁碟,csproj 只掛了 xsd 與 `.rpt`(`Dev/ATLAS.EC.Report/Source/Entity/ReportDataEntity.EC/ReportDataEntity.EC.csproj:419-507` · `Dev/ATLAS.EC.Report/Source/CrystalReports/Report.EC/Report.EC.csproj:241-343`),UI / Ctl / Pxy 三層沒掛(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/ReportUI.EC.csproj:211-266` 只列 10 支)。PO 的 `MSSQL/OFDR607_PO.cs` 153 行只有 1 行不是註解(BOM 那行)。**它們編不進任何 DLL,使用者從選單也開不到**——若選單表(版控外)還留著這 7 支的代號,點下去就是找不到型別(§7.10)。

4. **`.rpt` 懸空 2 支**(`OFDR050` `OFDR901A`),**不在 csproj 但檔案存在 0 個 `.rpt`**,「檔案存在但不在 csproj」的 `.cs` 有 4 個(`OFDR042RPS1.cs`~`RPS4.cs`,類別名與 `RPS11`~`RPS41` 重複,§2.7.1)。

5. **兩軌兩個世代的 UI**:OTA 36 支全部 `FormvalidatorManager` + `DoValidate()` + `GetQueryVDB()` 三段式、35 支沒有查詢鈕;EC 7 支 `validatorManager1` + 基金勾選 grid + `@str` 前綴參數。同一個 `xReportForm` 基底、兩套寫法。

6. **OTA 36 支 PO 是同一個模子刻的**:`BeginTransaction` → `using (cmd = GetStoredProcCommand)` → `AddInParameter ×n` → `AddOutParameter(RefCursor)` → `LoadDataSet(cmd, DataEntity, tran, 表名…)` → `i = 第一張表.Count` → `Commit` → `i > 0 ? AddResultRow(true) : AddResultRow(false, 0, "")` → `catch { tran.Rollback(); ... }`。**37 個 `BeginTransaction` 全在 `try` 內、`tran.Rollback()` 全在 `catch` 內**——`BeginTransaction` 自己丟例外時 `tran` 是 null,`catch` 裡的 `tran.Rollback()` 會用 NRE 蓋掉原例外(附錄 E9)。`OFDR050.Execute` 是唯一在 `finally` 判 `tran != null` 的(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:236-240`)。

7. **零筆的處理**:OTA 36 支 PO 零筆時 `AddResultRow(false, 0, string.Empty)`——`ReturnCode = false` 但**訊息空字串**;`xReportForm` 收到 false 會不會彈訊息、彈什麼,框架無原始碼看不到。唯一自己處理零筆的是 `OFDR001B`(查詢鈕那條路,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:187-190`,彈 `ReturnMessage`,而 `ReturnMessage` 就是那個空字串)與 `OFDR901A` 的 Excel 路(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:318-322` 「無符合查詢條件的資料。」)。**`nfdr1.md` 記的「零查無資料提示」缺陷型,本片 OTA 34 支同型**(附錄 E8)。

## 4. 維護畫面(M)— 一支一節

(本片無此類畫面)——見 §3.1。

## 5. 查詢畫面(I)

(本片無此類畫面)——見 §3.2。

## 6. 批次(B)與 WindowsService

(本片無此類畫面)——見 §3.3。**但有一支報表長得像批次**:`OFDR050` 的「製作資料」按鈕呼叫 `S_OTA_OFDR050_EXE` 把當日確認書資料算好寫進 `OFDR050T1`~`T9`,再由「預覽」讀 `S_OTA_OFDR050_GET`(§7.7)。它是 R 型代號、`xReportForm` 基底,但行為是「先跑一段批次再印」。

## 7. 報表(R)

```text
[圖] OFDR042 境外基金交易對帳單從按鈕到出紙的完整路徑,含 SP 內的資料權限段
圖中文字:UI OFDR042.cs:列印前 7 條 AddError + 兩段 PO 檢核 / 寄發碼 列印選項 日期 基金 / 7 條 AddError :216-258 / befPostCheck 段 1 / OFD303 OMNIBUS_PCD 不在 0 2 → 擋 / befPostCheck 段 2 / OFD303 POST_CTL_CODE = N → 擋 / USERID 進參數 / this.UserID 框架屬性 / SP S_OTA_OFDR042_GET 931 行:資料權限 → 暫存 → 5 個游標 / COD009 查 USERID 部門 / 查無 → XMYREC NULL → 零筆 / M2 C2 G16 G17 豁免 / XALL_FALG = Y 全看 / DELETE TA_DEPT_EMP 全表 / CRM001A CRM002A 算銷售關係 / DELETE DSMR008T4 全表 / OFD221 OFD251 CRM007A 算可查戶號 / DELETE DSMR008T0 全表 / 勾選基金 f_FormatStringToTable / INSERT OFDR042T4 受益人 / JOIN OFD132A / DSMR008T4 / OFDR042T1 T2 交易與結餘 / S_TA_IMP_OFD302_RANGE 淨值 / OPEN OutTB1 ~ OutTB5 / 受益人 交易 本期 前期 說明 / 回程與輸出 / PO LoadDataSet 5 張表 / OFDR042Model 5 個結果集 / Ctl TransferDataSet / 整個 DataSet 搬成 View / OFDR042RPS1.rpt / RPS2~4 在 csproj 但沒人引用 / 過濾 無提示 三處 / 權限 寄發設定 NVL 樣板
```

*圖:圖 5 最重的一支 OFDR042,對應 §7.8。第一排是 C# 端的檢核;第二排是 SP 的資料權限段——三個紫框是沒有使用者鍵、DELETE 全表重建的全域暫存表,兩個非豁免使用者同時按預覽會互相影響(附錄 E1);第三排是取數與五個游標;最後一排回程,右下角是使用者看不到的三處過濫。*

### 7.0 怎麼讀這一章

43 支活的報表共用兩套骨架(OTA 一套、EC 一套,§7.1),所以本章只對**六對同號**(§7.2)、**`OFDR001B` / `OFDR002`**(§7.3)、**四個連號群**(§7.4 §7.5)、**`OFDR901A` / `OFDR904`**(§7.6)、**會寫 DB 的 `OFDR050`**(§7.7)、**最重的 `OFDR042`**(§7.8)、**EC 活的 7 支**(§7.9)、**EC 死的 7 支**(§7.10)展開;§7.11 是卡控總表(含 SP 層的過濾),§7.12 把其餘各支分群帶過。每節固定四段:**做什麼 / 條件與卡控 / 取數 / 輸出**。

卡控結果一律五類:**阻擋**(不讓印)/ **警示**(印但跳訊息)/ **詢問**(Yes-No 再決定)/ **過濾(無提示)**(悄悄少印)/ **記錄不擋**。**本片的過濾(無提示)幾乎全在 SP 裡**,C# 看不到——這是 SP 在版控帶來的好處,也是 OFD / NFD 那兩片寫不出來的一節。

### 7.1 通則:兩套骨架

#### 7.1.1 OTA 骨架(36 支,以 `OFDR601A` 為範本)

| 段 | 事件 / 方法 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | `<代號>_FormInitial` | `ResultVDB` / `FormProxy` 指定;`FormvalidatorManager.DataDefaultInitialize()`;基金下拉 `SOURCE_CD = SHORE_ID.OffShore`(21 支有) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:52-66` |
| 2 | `<代號>_RefreshPage` | 記下列印權限 `blnPrint = ButtonPrintEnable`,選項預設 `'A'`(全部) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:72-79` |
| 3 | `_BeforePreviewButtonClicked` → 轉呼 `_BeforePrintButtonClicked` | `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` → `SetQueryParameters(版型, 版型, 中文名)` | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:147-163` |
| 4 | `DoValidate()` | 清錯誤 → `FormvalidatorManager.DataValidate()`(必填 / 格式,由 Designer 設定,不 Read)→ 自訂檢核(日期起迄)→ `QueryVDB = GetQueryVDB()` | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:201-219` |
| 5 | `GetQueryVDB()` | `new <代號>ViewVDB()`,逐條件 `prm.AddParametersRow(欄名, SQLOperator.Equal, 值)` | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:169-183` |
| 6 | (`xReportForm`,無原始碼) | 拿 `QueryVDB` 呼叫 `Pxy.GetReportData` → `Ctl.GetReportData` → PO;再 `Ctl.GetReportObject` 取 `.rpt` | `Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/OFDR601A_Ctl.cs:48-63` |
| 7 | `<代號>_ReportLoad` | `SetRptSchemaOnDoc()` + `m_ReportDocument.SetParameterValue(...)` 補抬頭 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR601A.cs:100-145` |

**沒有第 2 段的「查詢」按鈕**(`ofdr1.md §7.1` 五段裡的 `ubtnSearch_Click`)。36 支裡只有 `OFDR001B` 保留(§7.3),其餘 35 支使用者按預覽前**看不到筆數、看不到任何資料**。另有 6 支在第 3 段之前多一段「列印前向 PO 詢問業務狀態」:`OFDR002` `OFDR042` `OFDR050` `OFDR085` `OFDR086` 走 `pxy.befPostCheck(qryVDB)` / `g_Pxy.Is_OFD303_DONE(...)`,把 PO 回的 `ReturnMessage` 逐筆 `AddError`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR002.cs:119-127` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR085.cs:238-240`)。

#### 7.1.2 EC 骨架(7 支活的,以 `OFDR601` 為範本)

| 段 | 事件 / 方法 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | `_FormInitial` | `ResultVDB = new OFDR601_9iViewVDB()`;基金勾選 grid 綁 `EC_ECFundIDChoiceType_9iView.FUND_DATA` | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:40-58` |
| 2 | `_BeforePreviewOrPrintButtonClicked`(**一個 handler 兩顆鈕**) | `DoValidate()` → 依 `uoptReportType` 選三張版型之一 → `QueryVDB.Util.Parameters.Clear()` 再逐條件 `AddParametersRow("@strXxx", ...)` | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:80-113` |
| 3 | `DoValidate()` | 基金 grid 至少勾一筆、日期起迄、委託日期起迄成對 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:152-230` |
| 4 | Ctl | `DataAccessPool.Add(new OFDR601OracleDao())` → `GetDaoInstance<IOFDR601PO>()` → `po.GetIPJR601Data`;回程 `TransferTable` 三張表 | `Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/OFDR601_Ctl.cs:24-66` · `:155-163` |
| 5 | PO | `foreach rrRow` 比 `rrRow.Name == "@strFUND_ID"` 逐一 `AddInParameter(cmd, "wFUND_ID", ...)`;`"1900/01/01"` 當未輸入 → `DBNull`;`REPORTTYPE` 決定 `LoadDataSet` 進哪張結果集 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:46-119` |
| 6 | `_ReportLoad` | `SetRptSchemaOnDoc()` + 6 個 `SetParameterValue` | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR601.cs:121-136` |

`OFDR602` 是例外:預覽與列印**各寫一份幾乎相同的 handler**(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR602.cs:140-173` 與 `:175-215`),改一邊忘另一邊就會分岐——成對只改一邊的溫床。

#### 7.1.3 兩套骨架的卡控分佈

| 結果類型 | OTA(36) | EC 活的(7) | 備註 |
|---|---|---|---|
| **阻擋** | 36 支都有,最多 `OFDR042` `OFDR050` `OFDR085` `OFDR086` 各 7 條 `AddError` | 7 支都有,最多 `OFDR604` `OFDR605` 各 13 條 | EC 的條數多是因為「起迄成對必輸」每對寫 3 條 |
| **警示** | 5 支(`OFDR001B` `OFDR042` `OFDR050` `OFDR901A` `OFDR904`)有 `ShowMessage(Info01, ...)` | 0 支 | 全部是「執行成功 / 無資料」類 |
| **詢問** | **1 支**:`OFDR050` 「此交易日期已有資料, 是否重新產生!?」(`Warn02` + `DialogResult.OK`) | 0 支 | `ofdr1.md` 0 支、`nfdr1.md` 0 支,**本片是三片報表裡第一次出現詢問型** |
| **過濾(無提示)** | **SP 層 37 / 38 個 SP 有**(§7.11.2) | SP 不在版控,不可知 | 本片重點 |
| **記錄不擋** | 0 | 0 | — |

### 7.2 六對同號:`OFDR601A`~`606A`(OTA)vs `OFDR601`~`606`(EC)

結論在 §0.2:**五對兩軌、一對撞號**。本節深寫相似度最高的一對(`603`,UI 0.23 / Ctl 0.29)與最低的一對(`606`,xsd Jaccard 0.06,撞號),其餘四對用表帶過。

#### 7.2.1 `OFDR603A`(OTA)vs `OFDR603`(EC):同一件事、兩套實作

**做什麼**:境外 / 境內的「網路轉申購」委託資料檢核表——列出網路下單的轉申購委託,供作業人員核對。

| 面向 | `OFDR603A`(OTA) | `OFDR603`(EC) |
|---|---|---|
| 中文名 | 境外網路交易轉申購檢核表列印作業(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR603A.cs:161`) | 線上轉申購檢核表 / 網路交易轉申購檢核表列印作業 / 網路交易轉申購比對異常報表(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR603.cs:179-185`) |
| 版型 | 1 張 `OFDR603ARPS1` | 3 張 `OFDR603RPS` `RPS2` `RPS3`,由 `uoptReportType` 選 |
| 條件 | `OMNIBUS_ID`(帳戶別)`EC_REDEM_PCODE`(交易狀態)`REDEM_DATE_ST/END` `FH_CD`(**基金公司**)`FUND_ID` `BF_NO` | `@striFUND_ID`(**勾選清單,逗號串**)`@dateRCV_DATE_BNG/END`(收件日)`@dateREDEM_DATE_BNG/END` `@striChoiceEC_REDEM_PCODE` `@striChoiceSYSTEM_ID`(**交易來源**)`@strREPORTTYPE` |
| SP | `S_OTA_OFDR603A_GET`,讀 `OFD601` `OFD651` `OFD653` + `OFD068AT0`(`DB/SP/S_OTA_OFDR603A_GET.SQL`) | `S_EC_IPJR603_GET`,不在版控 |
| 結果集 | `OFDR603A_1` 一張,59 欄 | `OFDR603` `OFDR603_SUB` `OFDR603_DEF` 三張(對應三個 `REPORTTYPE`),42 欄 |
| 欄位交集 | 17 欄(`FUND_ID` `BF_NO` `ID_NO` `BF_NAME` `REDEM_DATE` 等主鍵級欄位) | — |
| 寫入 | SP 重建 `OFD068AT0`(全域暫存,E2) | C# 有 `DoDeleteTempTable`(`IPJR603T1`)但無人呼叫 |

**為什麼是兩軌不是撞號**:兩邊的業務動作都是「轉申購」(`REDEM_PCODE` / `REDEM_DATE` 為主鍵維度),差異全是境內外結構差(`FH_CD` 多家基金公司 vs 單一公司;`OMNIBUS_ID` 綜合帳戶 vs 無)。**改「轉申購檢核表要多印一欄」要改兩邊**,而且兩邊的 SP 一個在版控一個不在。

#### 7.2.2 `OFDR606A`(OTA)vs `OFDR606`(EC):撞號

| 面向 | `OFDR606A`(OTA) | `OFDR606`(EC) |
|---|---|---|
| 中文名 | **境外網路交易客戶明細表** | **網路受益人資料異動委託資料查核表** / 路受益人資料異動委託資料比對異常報表(少字) |
| 條件 | `APPLY_DATE_ST/END`(EC 申請日)`REG_CD`(註冊類別)`EC_PAY_WAY`(付款方式)——**4 個**(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR606A.cs:166-169`) | `@strEC_IDNO_ST/END` `@decEC_BF_NO_ST/END` `@dateCHG_EFFECT_DATE_ST/END` `@strEC_CHG_PCODE` `@dateAPPLY_DATE_ST/END` `@strREPORTTYPE`——**10 個**(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR606.cs:72-86`) |
| 主表 | `OFD607`(網路交易申請)`INNER JOIN OFD601`(網路交易客戶),`LEFT JOIN` 兩個 `CTL014` 代碼 CTE(`DB/SP/S_OTA_OFDR606A_GET.SQL:22-65`) | 不可知;從欄名 `CHG_EFFECT_DATE` `EC_CHG_PCODE` 推測是**受益人資料異動**委託表 |
| 結果集欄 | 13 欄(`APPLY_DATE` `BF_SRNO` `ID_NO` `BF_NO` `EC_NAME` `EC_PAY_WAY` `PROGRESS` `DOC_ARR_YN`…) | 43 欄 |
| 交集 | 3 欄(`ID_NO` `BF_NO` 級) | — |
| 檢核 | 2 條(申請日起迄) | 9 條(ID 起迄成對、戶號起迄成對、生效日起迄) |

**一個是「誰申請了網路交易、進度到哪」的客戶清冊,一個是「誰改了受益人資料」的異動查核。** 它們只共用「網路交易群第 6 號」這個位置。與 `ofdi2.md` 的 `OFDI612` / `OFDI612A` 同型:兩個團隊各自從 601 往下編號,編到 606 時業務對不上了。

`OFDR606A` 另有一個值得記的過濾:`OFD607.REG_CD = NVL(xREG_CD, OFD607.REG_CD)`(`DB/SP/S_OTA_OFDR606A_GET.SQL:63-64`)——`REG_CD` 為 NULL 的申請列,在「不篩註冊類別」時**也不會出現**(Oracle 三值邏輯,E5)。

#### 7.2.3 其餘四對

| 對 | 業務動作 | OTA 特有維度 | EC 特有維度 | OTA SP 讀的主表 | 判定 |
|---|---|---|---|---|---|
| 601 | 網路申購 | `OMNIBUS_ID` `FH_CD` `BF_NO` | `SYSTEM_ID` `APPLY_DATE`(委託日)`REPORTTYPE` 三張版型 | `OFD620` `OFD621`(網路申購主 / 明細)`OFD601` `OFD199` `OFD019A` | 兩軌 |
| 602 | 網路買回 | 同上,`EC_REDEM_PCODE` | `TradeSource` `TradeType` | `OFD651` `OFD652`(網路買回)`OFD601` `OFD019A` | 兩軌 |
| 604 | 網路定期定額契約 | `EC_RSP_PCODE` `RCV_DATE` | `OPEN_DATE` `SYSTEM_ID` | `OFD663` `OFD664` `OFD601` `OFD199` `OFD019A` `CTL014` | 兩軌 |
| 605 | 網路定期定額異動 | `EC_RSP_CHG_PCODE` `RSP_CHG_DATE` | `CHG_DATE` `CHG_EFFECT_DATE` `EC_ALLOT_PCODE` | `OFD666` `OFD667`(網路定額異動)+ `OFD551` `OFD552` `OFD554` `OFD555`(定期定額主檔),寫自用暫存 `OFDR605AT1` | 兩軌;**OTA 這支與 `OFDR552` 讀同一批定期定額表,SP 結構也像**(`DB/SP/S_OTA_OFDR605A_GET.SQL` 439 行 vs `DB/SP/S_OTA_OFDR552_GET.SQL` 432 行,都有 `XTEMP` `XCNT` 與 `OFDR5xxT1` 暫存) |

`A` 後綴歸類(交辦第 3 題):**`OFDR601A`~`OFDR606A` 六支全部是第 (f) 種「同一報表兩子系統各做一份、後綴讓號」**——EC 那邊先有 `OFDR601`~`606`(從 `IPJR601`~`606` 改名而來),OTA 後做時讓號加 `A`。**`606A` 雖然業務對不上,成因仍是 (f) 的「讓號」動作**:OTA 團隊看到 EC 已有 `OFDR606` 就加了 `A`,沒去確認業務是否相同。所以 `A` 的成因是 (f),撞號是結果。

### 7.3 `OFDR001B` / `OFDR002`:從 OTA 這邊反向驗證 `ofdr1.md §7.2`

`ofdr1.md §7.2` 從 OFD 那邊看到 `OFDR001A` / `OFDR002A`(境內)對 `OFDR001B` / `OFDR002`(境外),定為第 (f) 種成因。本節從 OTA 這邊驗證三件事:

| 驗證項 | 結果 | 錨點 |
|---|---|---|
| 中文名帶「境外」? | **帶**:「**境外**基金結餘單位數檢核表」「**境外**基金結餘單位數查核清冊」 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:124` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR002.cs:137` |
| SP 是 `S_OTA_*`? | **是**:`S_OTA_OFDR001_GET` `S_OTA_OFDR002_GET`,**都在版控**(OFD 那邊的 `s_TA_OFDR001A_Get` `s_OFDR002A_Get` 不在) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR001B_PO.cs:65` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:68` |
| 讀的是 `OFD081`(境外)還是 `OFD081A`(境內)? | **`OFD081`**,而且是 `OFD303`(不帶 `A`);OFD 那邊 `ofdr1.md §7.2.2` 記的是 `OFD303A` | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:126-129` · `DB/SP/S_OTA_OFDR002_GET.SQL:40-48` |
| 基金下拉鎖境外? | **是**:`custFUND_IDSide.SOURCE_CD = SHORE_ID.OffShore` | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:60` |

**三項全成立,(f) 型確認**。另外補一個 `ofdr1.md` 沒看到的:**表名的 `A` 在這裡是境內外標記**——境內版讀 `OFD303A`、境外版讀 `OFD303`;境內版讀 `OFD081V` / `OFD081A`(`ofdr1.md §7.2.2`)、境外版讀 `OFD081`。這與 `ofd123.md` 定的「`OFDxxxA` 是 MSSQL→Oracle 遷移改名(成因 b)」**衝突**——至少對 `OFD303` / `OFD303A`、`OFD081` / `OFD081A` 這兩對,`A` 是境內、無 `A` 是境外(成因 a 的表名版)。**假設**:兩對表都存在、各裝一邊的資料;依據是 OTA 這邊 34 個 SP 讀 `OFD081`、一個都沒讀 `OFD081A`。

#### 7.3.1 `OFDR001B`:唯一保留「查詢」按鈕的一支

**做什麼**:單一境外基金、單一結帳日的結餘單位數檢核——把前日餘額、本日申購 / 轉入 / 分配 / 贖回 / 轉出、本日餘額、受益人餘額、交易餘額並列,由 SP 判「帳平不平」。

**條件與卡控**:

| 時點 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| 查詢 / 列印前 | `FormvalidatorManager.DataValidate()`(必填) | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:114-122` |
| 查詢後 | PO `ReturnCode == false` → 彈 `ReturnMessage` | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:187-190` |
| 查詢後 | 有資料才打開預覽 / 列印鈕、鎖查詢鈕 | 阻擋(隱性) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:196-200` |
| PO | SP 出參 `strMsg` 非空 → `Rollback` + `AddResultRow(false, 0, strMsg)` | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR001B_PO.cs:73-84` |

`ofdr1.md §7.2.4` 記 `OFDR001A` 的「帳未平就不准印」是 R 唯一驗輸出的卡控,寫在 C#。**`OFDR001B` 把同一條檢核搬進 SP**:`S_OTA_OFDR001_GET` 用 `strMsg` 出參回「帳未平」類訊息(`DB/SP/S_OTA_OFDR001_GET.SQL` 387 行,`OFDR002` 那邊看得更清楚,見下)。C# 端只負責 `strMsg` 非空就 `Rollback` 並把訊息原樣丟回畫面。**兩邊擋的位置不同(C# vs SP),改帳平公式要改兩個地方。**

**取數**:`S_OTA_OFDR001_GET(iFUND_ID, iCTL_DATE, OutTB1, strMsg)`,讀 `OFD303` `OFD304` `OFD305` `OFD306` `OFD310` `OFD311`(各類結餘表)+ `OFD221` `OFD252` `OFD253`(當日交易)+ `OFD493`,無寫入。

**輸出**:`OFDR001BRPS1`,`ReportLoad` 只 `SetRptSchemaOnDoc()`,沒補任何抬頭參數(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:103-107`)。

#### 7.3.2 `OFDR002`:借 `OFDR001B` 的 xsd、在 SP 內迴圈呼叫 `OFDR001B` 的 SP

**做什麼**:某基金公司、某結帳日的**所有**境外基金結餘單位數清冊——`OFDR001B` 的多基金版。

**條件與卡控**:列印前先 `pxy.befPostCheck(qryVDB)`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR002.cs:119-127`),PO 自組 SQL 讀 `OFD081 INNER JOIN OFD303`:

| 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|
| 該公司該日在 `OFD303` 零筆 | 「無資料可列印!!」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:141-147` |
| 任一基金 `POST_CTL_CODE = 'N'` | 逐基金「尚有基金未過帳, 不可列印!, 基金[X]」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:148-159` |
| `INNER JOIN OFD303` | 沒有 `OFD303` 列的基金**不會被檢核也不會被印** | **過濾(無提示)** | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:128-129` · `DB/SP/S_OTA_OFDR002_GET.SQL:42-44` |
| `FH_CD = NVL(:FH_CD, OFD081.FH_CD)` | `FH_CD` 為 NULL 的基金消失 | 過濾(無提示) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:131` |

**取數**(這一段是本片 SP 在版控才寫得出來的):

```
FOR FUND_UNIT IN FUND_CUR LOOP            -- 該公司該日的每支基金
  S_OTA_OFDR001_GET(FUND_ID, xCTL_DATE, curOFDR001, strMsg);   -- 呼叫 OFDR001B 的 SP
  FETCH ... INTO 27 個變數
  IF TRIM(strMsg) IS NULL THEN
    IF NOT (xOUT_UNIT = xTRAN_UNIT AND xTRAN_UNIT = xBAL_UNIT_BF AND 綜合帳戶同式) THEN
      strMsg := '帳未平!';
  INSERT INTO OFDR002T1(USERDOMAIN, ..., ERR_MSG) VALUES (SYS_GUID 值, ..., strMsg);
END LOOP;
OPEN OutTB1 FOR SELECT ... FROM OFDR002T1 A INNER JOIN OFD062 INNER JOIN OFD081 WHERE USERDOMAIN = x;
DELETE FROM OFDR002T1 WHERE USERDOMAIN = x;
```

錨點 `DB/SP/S_OTA_OFDR002_GET.SQL:57-123`。三件事:

1. **帳平公式在 SP 裡,而且是 `OFDR002` 自己再算一次**(`:91-95`),不是沿用 `S_OTA_OFDR001_GET` 回的 `strMsg`——`strMsg` 非空時才跳過。兩支報表的「帳未平」判定**可能不一致**(`OFDR001B` 的規則在 `S_OTA_OFDR001_GET` 內部,本文未逐行核對)。

2. `OFDR002` 把每筆的 `ERR_MSG` **印在清冊上**(`:113`),不擋——與 `OFDR001B` 「帳未平就不准印」相反。**同一個判定,單筆版阻擋、清冊版列印**;這是刻意的(清冊本來就是給人看哪幾支沒平),但要知道。

3. `OPEN OutTB1 FOR ... ; DELETE FROM OFDR002T1 ...`(`:103-123`)——**先開游標再刪資料**。Oracle 游標在 `OPEN` 時定 SCN,C# 端 `LoadDataSet` 仍能 fetch 到;這段搬到 SQL Server 會回空表。

**C# 端**:`OFDR002_PO.GetData` 把結果塞進 **`OFDR001BModelVDB.OFDR001B_1`**(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:59` · `:77`)——`OFDR002` 沒有自己的 xsd,借 `OFDR001B` 的。`S_OTA_OFDR002_GET` 回的欄位(`FH_CD` `FH_NM_SH_C` `FUND_ID` `FUND_SH_NM` `CTL_DATE` `BAL_UNIT_BF` `BAL_UNIT_BF_O` `TOT_BAL_UNIT_BF` `UNIT_DEC` `strMsg`)是 `OFDR001B_1` 27 欄的子集,`LoadDataSet` 只填有的欄。**改 `OFDR001BModel.xsd` 會同時打到 `OFDR002`**。

**輸出**:`OFDR002RPS1`。

### 7.4 連號群 `OFDR551`~`OFDR554`:三支一組,第四支是別的家族

`ofdr1.md §7.3` 的結論是「連號 ≠ 同系列」。本片這組**三支是同系列、一支不是**:

| 畫面 | 中文名 | SP 讀的主表 | 條件的主軸 | 版型 | 家族 |
|---|---|---|---|---|---|
| `OFDR551` | 境外定期定額契約資料查核表列印作業 | `OFD551` `OFD552`(定期定額契約)`OFD019A` `OFD199` | 收件日起迄 + 契約書號起迄 + 基金公司 / 基金 + 銷售機構 | 2 張(`RPS1` `RPS2`,依 `uopt` 選,中文名相同) | **定期定額** |
| `OFDR552` | 境外定期定額契約異動資料查核表列印作業 | `OFD551` `OFD552` `OFD554` `OFD555`(契約異動),寫 `OFDR552T1` | 異動日起迄 **或** 異動生效日起迄(擇一必輸)+ 戶號 | 1 張 | **定期定額** |
| `OFDR553` | 境外定期定額產生扣款資料明細表 / 契約扣款資料明細表 / 彙總表 | `OFD904`(扣款)`OFD552` `OFD221` `COD006A` | 扣款日起迄 + 基金 + 銷售機構 + `REPORT_TYPE` `DATA_TYPE` | 3 張(`switch REPORT_TYPE`,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR553.cs:124-136`) | **定期定額** |
| **`OFDR554`** | **境外基金定額確認書** | `OFD221`(申購)`OFD305` `OFD082` `OFD083` `OFD132A`(寄發設定),寫 `DSMR008T0` `DSMR008T4` | 基金勾選清單 + 申購日 + **寄發碼 + 郵寄 / E-mail / FAX / 親領 + 整批 / 指定受益人** | 5 張(UI 只要 `RPS1`) | **確認書 / 對帳單**(與 `OFDR042` `OFDR054` `OFDR085` `OFDR086` 同模子) |

判定依據不是號碼,是**三個指紋**:

1. **UI 條件的形狀**:`OFDR551`~`553` 是「日期起迄 + 基金 + 銷售機構」的查核表形狀;`OFDR554` 是「基金 grid 勾選 + `SEND_CODE` + 四個寄送 checkbox + `uoptPrint` 整批 / 指定」的確認書形狀(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR554.cs:160-167` · `:196-233`),與 `OFDR042.cs:216-258` `OFDR054` `OFDR085` `OFDR086` **逐條同文**(「寄發碼必須輸入!」「列印選項必須輸入!」「整批列印, 其寄送選項需擇一輸入!」「指定受益人列印, 受益人ID必須輸入!」「【挑選基金資料】尚未選取任何基金資料!」)。

2. **SP 的參數簽名**:`S_OTA_OFDR554_GET(iFUND_ID, iALLOT_DATE, iSEND_CODE, iSEND_POST, iSEND_EMAIL, iSEND_FAX, iSEND_COLLECT, iBF_NO, OutTB1..OutTB6)`(`DB/SP/S_OTA_OFDR554_GET.sql:3-16`)與 `S_OTA_OFDR042_GET` `S_OTA_OFDR054_GET` `S_OTA_OFDR085_GET` `S_OTA_OFDR086_GET` 同構(多游標、`DSMR008T0` 基金清單、`DSMR008T4` 戶號清單、`OFD132A` 寄發過濾);`S_OTA_OFDR551_GET(iRCV_DATE_S, iRCV_DATE_E, iRSP_NO_S, iRSP_NO_E, iFH_CD, iFUND_ID, iAGENT_ID, iAGENT_CODE, OutTB1)`(`DB/SP/S_OTA_OFDR551_GET.SQL:3-16`)是單游標查核表。

3. **`.rpt` 數量**:確認書家族 3~5 張 `.rpt` 但 UI 只要 `RPS1`(子報表或廢版型,§2.7.2 第 2 點);查核表家族 `.rpt` 數 = UI 分支數。

**所以 `OFDR554` 應該跟 `OFDR054`(申購確認書)放在一起讀**——它是「定期定額扣款成功後寄給受益人的確認書」,`554` 的 `5` 只表示資料來源是定期定額。

`OFDR552` 有一條值得抄的檢核:**「異動日期 或 異動生效日期 必需擇一輸入!」**(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR552.cs:206`)——兩組日期都空就不准印,避免全表掃。本片其他 35 支沒有這種「至少一個範圍條件」的防護;`OFDR606A` 的申請日、`OFDR109` `OFDR111` 的異動日都可以全空。

### 7.5 連號群 `OFDR131`~`OFDR134`:三支共用 xsd,第四支是通知書

| 畫面 | 中文名 | SP 讀的表 | xsd | 家族 |
|---|---|---|---|---|
| `OFDR131` | 基金受益分配試算明細表 | `OFD281`(分配主檔)`OFD282`(**試算**明細)`OFD013` `OFD020V` | 自己的 `OFDR131Model` | 受益分配查核 |
| `OFDR132` | 總代理-受益分配明細表 | `OFD281` `OFD283`(**確認**明細) | **借 `OFDR131Model`** | 受益分配查核 |
| `OFDR134` | 銷售機構-受益分配明細表 | `OFD281` `OFD283` | **借 `OFDR131Model`** | 受益分配查核 |
| **`OFDR133`** | **境外基金配息通知書** | `OFD281` `OFD283` `BMS001A`(受益人地址 / 電話)`OFD132A`(寄發設定),寫 `DSMR008T0` | 自己的,3 張結果集 | **通知書**(寄發家族) |

`OFDR131` / `132` / `134` 三支的 UI **逐行相同**(都 209 行,條件 `FUND_ID` + `RECORD_DATE`,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR131.cs:121-122`),差別只在 SP 名、版型名與**讀哪張明細**:`131` 讀 `OFD282`(試算),`132` `134` 讀 `OFD283`(確認後);`132` 與 `134` 的 SP 只差 `/*境外總代理-…*/` 與 `/*銷售機構-…*/` 的註解(`DB/SP/S_OTA_OFDR132_GET.SQL:15` vs `DB/SP/S_OTA_OFDR134_GET.SQL:15`)和排序 / 欄位順序——**版型不同(總代理看的 vs 給銷售機構的),資料幾乎同一份**。三支另有一段自組 SQL `GetOFD281`,選基金後撈該基金的 `RECORD_DATE` 清單填下拉(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR131_PO.cs:104-129`)。

`OFDR133` 走寄發家族的路:基金 grid 勾選 → `f_FormatStringToTable` 轉表塞 `DSMR008T0`(全域暫存,E1)→ `INNER JOIN DSMR008T0`(`DB/SP/S_OTA_OFDR133_GET.SQL:40-43` · `:84-85`)→ 三個游標(受益人資料 / 明細 / 基金)。它的受益人資料段把 `ID_NO` 用 `HIDE_ID_NO_NEW`、電話用 `HIDE_PHONE_NO` 遮罩(`:50-67`)——**本片唯一做個資遮罩的報表**;同樣印受益人 ID 與電話的 `OFDR042` `OFDR054` `OFDR554` 確認書有沒有遮,要看各自 SP(`grep -li HIDE_ DB/SP/S_OTA_OFDR*` 命中 `042` `054` `085` `086` `133` `554` 六個——確認書家族全有遮,查核表家族全沒有;查核表印的是內部作業用的 ID,**假設**不需遮)。

### 7.6 `OFDR901A` / `OFDR904`:兩支會轉 Excel 的月報,一支 `.rpt` 懸空

#### 7.6.1 `OFDR901A`:境外期間手續費獎金明細表

**做什麼**:依結算月份 / 結算日期區間、基金種類、部門、AO(業務員)、帳戶別,算每筆申購的手續費獎金(`ALLOT_BNS = ALLOT_FEE × SAL_RATE`),出明細表與彙總表,可轉 Excel。

**`A` 後綴歸類**(交辦第 3 題):`OFDR901A` 在 OTA 專案內,同專案有 `OTAR901`(`misc.md`),OFD 專案沒有 `OFDR901`;`DB/SP/` 也沒有 `S_OTA_OFDR901_GET`。**對不上七種成因的任何一種**——沒有另一支同號可讓、不是境內外、不是遷移改名。**假設**:是 (f) 的預防性讓號(開發時預期 OFD 那邊會有 `OFDR901`,先加 `A`),依據是同批 `OFDR601A`~`606A` 都是 (f)。老實說:**這個 `A` 找不到對手**。

**條件與卡控**:

| 檢核 | 結果類型 | 錨點 |
|---|---|---|
| 結算日期起 > 迄 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:192` |
| 選「指定個別基金」但基金空 | 阻擋 | `:197` |
| 轉 Excel 時轉出路徑空 / 不存在 | 阻擋 | `:204` · `:208` |
| Excel 路 PO 回 `false` | 警示「無符合查詢條件的資料。」 | `:318-322` |
| SP 出參 `strMsg` 非空 | `Rollback` + `AddResultRow(false, 0, strMsg)` | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR901A_PO.cs:86-92` |

**取數**:`S_OTA_OFDR901A_GET`(`DB/SP/S_OTA_OFDR901A_GET.SQL`,272 行):

1. `SYS_GUID()` 當 `USERDOMAIN`,`DELETE OFDR901T1 WHERE USERDOMAIN = x`(`:35` · `:46`)——自用暫存,安全。

2. 讀獎金參數 `SAL071 WHERE ROWNUM = 1`,**`WHEN OTHERS` → `strMsg := '查無獎金計算參數檔!'` → `RAISE is_someting_error`**(`:58-67`)。

3. 重建全域 `OFD068AT0`,**這支從 `OFD068A_V000` 讀**(`:69-76`),其他 17 個 SP 從 `OFD068A_V02`、`OFDR081` 從 `OFD068A_V01`——三個 View 版本並存,`V000` `V01` 不在版控。

4. `INSERT INTO OFDR901T1 ... SELECT ... FROM OFD221 ...`(申購)→ `FOR T1_REC LOOP` 逐筆算 `SAL_RATE`、`UPDATE OFDR901T1 SET ALLOT_BNS = CASE FEE_TYPE ...`(`:163-203`)。

5. `OPEN OutTB1`(明細)`OPEN OutTB2`(彙總),兩個都 `LEFT JOIN OFD068AT0 AGENT ON ... AND A.AGENT_CODE LIKE AGENT.AGENT_CODE`(`:230-232` · `:257-259`)。

6. 最外層 `EXCEPTION WHEN is_someting_error THEN DBMS_OUTPUT.put_line(...)`(`:267-269`)。

**第 6 步是缺陷**(附錄 E10):`is_someting_error` 被最外層接住後只 `put_line`,**procedure 正常結束,但 `OutTB1` `OutTB2` 從未 `OPEN`**。C# 端 `LoadDataSet` 對沒開的 RefCursor 會丟例外 → 進 `catch` → `tran.Rollback()` + `AddResultRow(false, 0, string.Empty)`(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR901A_PO.cs:107-112`)→ **`strMsg` 那段(`:86-92`)永遠跑不到,使用者看到的是空訊息,不是「查無獎金計算參數檔!」**。設計者想回訊息,實作卻把訊息吃掉了。

第 5 步的 `LIKE AGENT.AGENT_CODE`:右邊是欄值不是樣式,等同 `=`——**除非 `AGENT_CODE` 含 `_` 或 `%`**,`_` 會變成單字元萬用字元(`LIKE` 樣式餵給 `=` 的反向:`=` 語意餵給 `LIKE`)。銷售機構代碼含底線就會多對到別家(附錄 E11)。

**輸出**:UI 要 `OFDR901ARPS1`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:134`),**`Report.OTA/` 底下沒有這個檔、沒有伴生 `.cs`、csproj 沒宣告**——Crystal 預覽 / 列印必定執行期失敗(附錄 E4)。**Excel 路是活的**:`DoExp1()` → `Pxy.GetReportData` → `UIExcelHelper.GenExcelFile(..., GenExcelR1, GenExcelR2)`(`:310-341`),兩張 sheet 對應兩個游標。**假設**這支報表實際上只有 Excel 在用,依據是 `.rpt` 從未進版控卻沒人修。

#### 7.6.2 `OFDR904`:Monthly AUM Report 四張

**做什麼**:依基金公司 / 日期區間 / 基金 / 帳戶別 / 分群方式(`GROUP` = 0 基金 / 1 銷售機構 / 2 受益人 / 3 會計 AUM movement)/ 是否含受益分配,算期初期末單位數與金額。

**條件**:與 `OFDR901A` 同一套 Excel 路徑檢核(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR904.cs:204-212`);`GROUP` 決定版型(`:134-149`)與 Excel 檔名(`:280-299`)。

**取數**:`S_OTA_OFDR904_GET(iDATE_ST, iDATE_END, iFH_CD, iBAL_TYPE, iFUND_ID, iGROUP, iDIVIDEND, iUSERDOMAIN, OutTB1)`(`DB/SP/S_OTA_OFDR904_GET.sql:1-12`)——**`USERDOMAIN` 由 C# 傳入**(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR904.cs:170` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR904_PO.cs:77`),不是 SP 內 `SYS_GUID()`,是本片唯一這樣做的取數 SP(`OFDR050` 的 `_EXE` 也由 C# 傳,但那是製作資料)。SP 內 `FND_CUR` 逐基金迴圈算餘額,`INSERT INTO OFDR904T1` 四種形狀(`:239` `:263` `:392` `:407`),`OPEN OutTB1`(`:557`)前後各 `DELETE`(`:549` `:622`)。SP 抬頭有 2009 / 2022 / 2023 三代修改註記(`:14-17`),**是本片唯一留有變更史的 SP**。

`FND_CUR` 的 `OFD081.FUND_STATUS = '0'`(`:47`):**只算狀態 `0` 的基金**——清算 / 合併中的基金 AUM 不會進報表,UI 沒有任何提示。過濾(無提示)。

**輸出**:4 張 `.rpt` 全在;Excel 檔名第三張 `OFDR904RP31(受益人分類)` 拼錯(`:296`),不影響功能只影響檔名。

### 7.7 `OFDR050`:本片唯一會寫 DB 的 C# 路徑,也是唯一有「詢問」的一支

**做什麼**:境外交易確認書(合併版)——把某交易日的申購 / 贖回 / 轉換 / 定期定額交易,依受益人合併成一份確認書。分兩步:**製作資料**(算好寫進 `OFDR050T1`~`T9`)→ **預覽 / 列印**(讀回)。

**流程與卡控**:

| 步 | 動作 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 1 | 按「製作資料」 | `pxy.befPostCheck`:自組 SQL 查 `OFD252` / `OFD253` 中 `REDEM_PROC_CODE = '5'` 且 `OMNIBUS_ID = 'Y'` 的綜合帳戶贖回,其 `OFD303.OMNIBUS_PCD_R / _S` 是否 `'1'`(已做 `OFDB090` 分配確認);沒做的逐基金 `AddError`「必須先做綜合帳戶贖回/轉換分配確認作業(OFDB090)」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:72-137` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:143-148` |
| 2 | 同上 | `OFDR050T6.TRADE_DATE = :ALLOT_DATE` 已有資料 → 回 `"ExistsData"` | — | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:141-160` |
| 3 | UI 收到 `ExistsData` | **`ShowMessage(Warn02, "此交易日期已有資料, 是否重新產生!?")`,非 OK 就停** | **詢問** | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:156-158` |
| 4 | `pxy.Execute` | `S_OTA_OFDR050_EXE(iUSERDOMAIN, iFUND_ID, iALLOT_DATE, iSEND_CODE, iBF_NO, strMsg OUT, OutTB1 OUT)`;`strMsg` 非空 → `Rollback` + 錯誤;否則 `Commit` + 「製作資料成功!」或「沒有資料可以處理!!」 | 阻擋 / 警示 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:184-242` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:180-197` |
| 5 | 按「預覽 / 列印」 | 寄發碼 / 列印選項 / 整批寄送選項 / 指定受益人 ID / 至少勾一基金——與確認書家族同文 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:270-293` |
| 6 | `GetData` | `S_OTA_OFDR050_GET(iALLOT_DATE, iBF_NO, OutTB1..OutTB9)` 讀回九張暫存;`OFDR050_6.Count == 0` → 「請先製作資料!」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:256-313` |

**寫入**:`S_OTA_OFDR050_EXE`(855 行,本片第二大 SP)寫 `OFDR050T1`~`T9` 九張自用暫存(`USERDOMAIN` 由 UI 產生傳入,`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:174`)+ 全域 `DSMR008T0`。**但 `S_OTA_OFDR050_GET` 讀 `OFDR050T*` 時只用 `ALLOT_DATE` / `BF_NO` 篩,不帶 `USERDOMAIN`**(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:270-271`)——所以第 2 步「已有資料」是**跨使用者**的:A 製作了 6/30 的資料,B 開畫面選 6/30 按預覽,印的是 A 製作的那份;B 若按製作資料,會被問「是否重新產生」,按 OK 就蓋掉 A 的。**這是設計(當日確認書全公司一份),不是缺陷**,但要知道 `USERDOMAIN` 在這支只用來隔離製作過程,不隔離結果。

`OFDR050_EXE` 用 `OFD132A.STATEMENT_CODE = '0100'` 篩寄發設定(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:82`;`DB/SP/S_OTA_OFDR050_EXE.SQL` 亦 `'0100'`),**其餘五支確認書 / 對帳單(`042` `054` `085` `086` `554`)與配息通知書 `133` 全用 `'0130'`**。`OFD132A` 的類別碼定義不在版控,無法判斷哪個對;**假設**`0100` = 交易確認書(C# 註解如此寫)、`0130` = 對帳單 / 通知書,那 `054` `085` `086` `554` 四支「確認書」用 `0130` 就是抄了對帳單的碼——或者反過來 `050` 抄錯。**六支確認書兩種碼,至少有一邊是錯的**(附錄 E12)。

**輸出**:`OFDR050RPS1`——**懸空**,檔不存在(§2.7.2)。**製作資料那條路是活的,預覽 / 列印那條路必定失敗**;這支報表的「製作」可能只是為了讓 `OFDR054` `OFDR085` `OFDR086`(各自讀 `OFD221` `OFD252` `OFD253`)以外的合併確認書走別的出口(**假設**,版控內找不到誰讀 `OFDR050T*`)。

### 7.8 `OFDR042`:最重的一支,也是資料權限唯一落在報表裡的一支

**做什麼**:境外基金交易對帳單——某期間內每位受益人的申購 / 贖回 / 轉換交易、本期與前期結餘、自訂說明,依寄發設定過濾後整批印或指定受益人印。

**為什麼最重**:SP 931 行(本片最大)、5 個游標、讀 20 張實體表、寫 4 張全域暫存 + 3 張自用暫存、43 個 `INNER JOIN` + 15 個 `LEFT JOIN`;UI 434 行、7 條 `AddError`;PO 兩段自組 SQL 檢核。

**條件與卡控**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 列印前 | 寄發碼、列印選項、交易日起 ≤ 迄、整批時寄送選項擇一、指定受益人時 ID 必輸、至少勾一基金 | 擋 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR042.cs:216-258` |
| 列印前(PO) | 勾選基金在期間內任一日 `OFD303.OMNIBUS_PCD_A/R/S` 不在 `('0','2')` | 「請先進行綜合帳戶分配確認!!」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR042_PO.cs:148-182` |
| 列印前(PO) | 期間內任一日 `POST_CTL_CODE = 'N'` | 「請先進行結轉!!」 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR042_PO.cs:190-222` |
| SP | 使用者部門不在 `M2` `C2` `G16` `G17` → 只留自己銷售關係內的受益人 | 少印 | **過濾(無提示)** | `DB/SP/S_OTA_OFDR042_GET.SQL:477-562` · `:577-581` |
| SP | `INNER JOIN OFD132A ON STATEMENT_CODE = '0130'`:沒有寄發設定的受益人整筆消失 | 少印 | **過濾(無提示)** | `DB/SP/S_OTA_OFDR042_GET.SQL:574-576` |
| SP | 寄發碼 / 寄送方式與 `OFD132A` 旗標比對;**指定 `BF_NO` 時跳過寄發過濾** | 少印 / 不篩 | 過濾(無提示) | `DB/SP/S_OTA_OFDR042_GET.SQL:583-591` |

第一條 PO 檢核的 `OMNIBUS_PCD_A <> '0' AND <> '2'`(`:151-153`):三個欄位任一為 NULL 時該分支為 UNKNOWN,`OR` 起來**只要另一欄成立就擋**、三欄全 NULL 就不擋——NULL 被當成「已確認」放行。Oracle 三值邏輯(E5)。

**取數 / 資料權限**(`DB/SP/S_OTA_OFDR042_GET.SQL`):

```
SELECT A.* INTO XMYREC FROM COD009 A WHERE A.UID_CODE = xUSERID;      -- :479-482,查無 → XMYREC := NULL
IF XMYREC.DEPT_NO IN ('M2','C2','G16','G17') THEN XALL_FALG := 'Y';   -- :488,豁免部門
ELSE
  DELETE TA_DEPT_EMP;  INSERT INTO TA_DEPT_EMP ... FROM CRM001A JOIN CRM002A WHERE A.EMP_NO = XMYREC.EMP_NO;  -- :493-502
  DELETE DSMR008T4;    INSERT INTO DSMR008T4(BF_NO) <OFD221 / OFD251 / CRM007A 三段 UNION,各 INNER JOIN TA_DEPT_EMP>;  -- :514-558
END IF;
INSERT INTO OFDR042T4(USERDOMAIN, BF_NO, IS_TRADE)
SELECT ... FROM BMS001A INNER JOIN OFD132A ... LEFT JOIN DSMR008T4 Z
 WHERE (Z.BF_NO IS NOT NULL OR XALL_FALG = 'Y') ...                    -- :571-591
```

三件事:

1. **`USERID` 從哪來**:UI 第 188 行 `prm.AddParametersRow("USERID", SQLOperator.Equal, this.UserID)`;同檔第 72 行另有 `this.UserId = ...AA_User.Rows[0]["UserID"]`——**兩個不同大小寫的成員**。`UserId`(小寫 d)是畫面自己宣告的欄位,賦了值沒人讀;`UserID`(大寫 D)**假設**是 `xReportForm` 的屬性(無原始碼)。`OFDR601A.cs:35` · `:61` 也宣告並賦值了 `UserId` 卻從未使用——是範本留下的死欄位。只要 `xReportForm.UserID` 存在且正確,權限就對;若不存在會編譯錯,所以它存在。

2. **`XMYREC := NULL` 後 `XMYREC.DEPT_NO`**(`:485` → `:488`):`COD009` 查無該使用者時 `XMYREC` 整個 record 設 NULL,下一行取 `.DEPT_NO`——PL/SQL 對 NULL record 取欄位回 NULL,`NULL IN (...)` 為 UNKNOWN,走 `ELSE` → `TA_DEPT_EMP` 用 `XMYREC.EMP_NO`(NULL)篩 → 空 → `DSMR008T4` 空 → **`Z.BF_NO IS NOT NULL` 全 false、`XALL_FALG = 'N'` → 零筆**。查無使用者的人印出空對帳單,無提示。這是安全的失敗方向(fail-closed),記錄為過濾。

3. **`TA_DEPT_EMP` 與 `DSMR008T4` 都是全域表、`DELETE` 全表重建**(`:493` · `:514`)。兩個非豁免部門的使用者 A、B 同時按預覽:A 建好自己的權限集開始 `INSERT OFDR042T4`;B 的 `DELETE TA_DEPT_EMP` / `DELETE DSMR008T4` 在同一時間執行。Oracle 讀一致性讓 A **已開始的那條 `INSERT ... SELECT`** 看到的是自己語句開始時的快照,所以單一語句內不會被 B 影響;**但 A 的 `DSMR008T4` 重建(`:514`)與 `OFDR042T4` 寫入(`:571`)是兩條語句,中間 B 的 `DELETE DSMR008T4` 若已 commit——不,B 沒 commit,C# 端交易到最後才 `Commit`**。所以在「C# 一個交易包住整個 SP」的前提下,A 看不到 B 未 commit 的 `DELETE`;真正的問題是 **B 的 `DELETE TA_DEPT_EMP` 會等 A 的交易釋放列鎖**(A 剛 `INSERT` 的列被 A 鎖著)→ B 卡住到 A 印完;A 印完 commit 後 B 才刪、重建。結果是**序列化而非互蓋**——前提是兩邊都在交易內。**假設**成立的條件:`Database.BeginTransaction()`(框架,無原始碼)確實把 `GetStoredProcCommand` 掛在同一連線同一交易上。若框架其實是 auto-commit(`LoadDataSet(cmd, ds, tran, ...)` 只是把 `tran` 傳進去而 SP 內部各語句各自 commit——Oracle 的 PL/SQL 不會,除非有 autonomous transaction),互蓋才會發生。**這一條最需要人工複驗**(附錄 E1、E.31)。

**輸出**:`OFDR042RPS1`(另 3 張 `RPS2`~`RPS4` 沒人引用,§2.7.2);`ReportLoad` 補 `TRAN_DATE_ST` `TRAN_DATE_END` 兩個抬頭。

### 7.9 EC 活的 7 支:`OFDR601`~`OFDR606` `OFDR609`

**共同點**:UI 用 `Infragistics` 基金勾選 grid、`@str` 前綴參數、`REPORTTYPE` 選版型;PO 是 `<代號>OracleDao : I<代號>PO`,方法名 `GetIPJR60xData`(`609` 例外 `GetOFDR609Data`);SP `S_EC_IPJR60x_GET` / `S_EC_OFDR609_Get` 不在版控;每支兩套 xsd(`Model` 死、`_9iModel` 活)。

| 畫面 | 版型數 | 結果集(`_9iModel` 內的表) | 特殊點 |
|---|---|---|---|
| `OFDR601` | 3(彙總 / 明細 / 比對異常) | `OFDR601_SUB` `OFDR601` `OFDR601_DEF` | `REPORTTYPE` 決定 `LoadDataSet` 進哪張(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:104-119`);Ctl 舊的逐欄搬移碼被整段註解、改用 `TransferTable`(`Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/OFDR601_Ctl.cs:160-197`) |
| `OFDR602` | 3 | 同型 | **預覽 / 列印兩份 handler**(§7.1.2);參數 `@striTradeSource` `@striTradeType`(命名再換一套) |
| `OFDR603` | 3 | 同型 | 條件多 `RCV_DATE`(收件日) |
| `OFDR604` | 2 | 同型 | 參數**不帶 `@` 前綴**(`FUND_ID` `APPLY_DATE_ST`…)只有 `@strREPORTTYPE` 帶;PO 內有 `BeginTransaction`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR604OracleDao.cs:27-43`),其餘 6 支沒有 |
| `OFDR605` | 2 | 同型 | 13 條 `AddError`(本片最多),全是起迄成對 |
| `OFDR606` | 2 | 同型 | 撞號(§7.2.2);第二版型中文名少字 |
| `OFDR609` | 4(統計三種分類 + 明細) | `OFDR609` `OFDR609B` `OFDR609C` `OFDR609D` | **兩個 SP**:`TYPE = "1"` 走 `S_EC_OFDR609_Get`、否則 `S_EC_OFDR609D_Get`;統計再依 `O_CODE` 選三張表(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR609OracleDao.cs:45-106`);UI 註解說「預存程序已給非必要參數預設值,全部時不傳該參數」但實際五個參數都傳(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR609.cs:66-76`) |

**死方法**:`OFDR601`~`OFDR605` 五支 PO 各有一個 `private void DoDeleteTempTable(...)`,內容 `"DELETE " + TableName + " WHERE USERDOMAIN = '" + xUSERDOMAIN + "'"` + `new OracleCommand` + `db.ExecuteNonQuery`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:141-172`),**沒有任何呼叫端**;`GetIPJR601Data` 開頭的 `xUSERDOMAIN = Guid.NewGuid()`(`:39`)也沒人用。這是 MSSQL 版「C# 先清暫存表再呼叫 SP」的殘骸,Oracle 版把清理搬進 SP(**假設**,SP 不在版控看不到)後忘了刪 C#。`ExecuteNonQuery` 因此在 EC 是 **0 條活路**。

**零筆**:PO 零筆時 `AddResultRow(true, 0, string.Empty)`(`601`~`606`,`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:126-129`)——**`ReturnCode = true`**,與 OTA 的 `false` 相反,`609` 又是 `false`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR609OracleDao.cs:113-116`)。框架收到 `true` + 0 筆會直接開一張空白報表(**假設**)。

### 7.10 EC 死的 7 支:`OFDR607` `OFDR608` `OFDR610`~`OFDR613` `OFDR690`

| 層 | 狀態 | 錨點 |
|---|---|---|
| UI `.cs` | 在磁碟、**不在 `ReportUI.EC.csproj`**;基底 `xReportForm`,用 `EC_ECFundIDChoiceTypeView`(非 `_9i` 版) | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR607.cs:20-32` vs `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/ReportUI.EC.csproj:211-266` |
| Ctl | 在磁碟、不在 csproj;**無基底**,直接 `new OFDR607_PO()` | `Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/OFDR607_Ctl.cs:12` · `:50` |
| Pxy | 在磁碟、不在 csproj | `Dev/ATLAS.EC.Report/Source/FormProxy/ReportFormProxy.EC/OFDR607_Pxy.cs` |
| PO | 只有 `MSSQL/OFDR607_PO.cs`,**在 csproj 但整檔 `//` 註解**(153 行,1 行有效);註解內是 `Basic_PO` 派、`m_db = null`、`provider.Create("TA")`、T-SQL SP `s_OFDR607_Get`、`SqlDbType` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/MSSQL/OFDR607_PO.cs` · `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/ReportPO.EC.csproj:143` |
| xsd | `OFDR607Model.xsd` `OFDR607View.xsd` 在 csproj、有效 | `Dev/ATLAS.EC.Report/Source/Entity/ReportDataEntity.EC/ReportDataEntity.EC.csproj:419` |
| `.rpt` | 3 張全在 `Report.EC.csproj` | `Dev/ATLAS.EC.Report/Source/CrystalReports/Report.EC/Report.EC.csproj:241-253` |

**為什麼是這樣**:MSSQL → Oracle 遷移時,團隊把 14 支的 MSSQL PO 全部註解掉(不是刪除),然後只替 7 支寫了 `OracleDao`。另 7 支沒寫,UI / Ctl / Pxy 因為引用不到 PO 型別會編譯錯,所以從 csproj 拔掉;xsd 與 `.rpt` 不引用 PO,留著也能編,就留著了。**結果:磁碟上看起來 14 支齊全,實際只有 7 支能跑。** 用 `ls` 數畫面會多算 7 支。

**它們原本做什麼**(從 UI 中文名與註解內 PO):`607` 受益人異動拋轉狀態查核表、`608` 網路額度控管表、`610` 申購扣款總表、`611` 扣款結果一覽表、`612` 扣款失敗明細表、`613` 扣款行回覆統計、`690` 員工交易審核明細表(五種交易各一張)。**網路交易的「扣款」系列(`610`~`613`)整批沒遷**——如果這些報表還有人要,Oracle 版要重寫。

**`m_db` 死碼線在這 7 支的位置**:註解裡的 `private Database m_db = null;` + 建構子 `m_db = provider.Create("TA")`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/MSSQL/OFDR601_PO.cs:17-27`,同型)——**這批 MSSQL 版其實有初始化**,不是 `ofdr1.md §7.12.2` 那種被註解掉的初始化。所以就算把註解拿掉,它們會連 `TA` 的 MSSQL 設定,不是 NRE。

### 7.11 卡控總表

#### 7.11.1 阻擋型(43 支活的都有)

| 畫面 | `AddError` 條數 | 最值得注意的一條 |
|---|---|---|
| `OFDR604` `OFDR605`(EC) | 13 | 起迄成對必輸,每對三條 |
| `OFDR606`(EC) | 9 | 「受益人ID(起) 不可大於 受益人ID(迄)」——字串比大小 |
| `OFDR601` `OFDR602` `OFDR603`(EC) | 8 | 「至少勾選一筆基金代碼」 |
| `OFDR042` `OFDR050` `OFDR085` `OFDR086` | 7 | 確認書家族同文五條 + PO 回的業務狀態 |
| `OFDR054` `OFDR133` `OFDR554` `OFDR901A` | 6 | `OFDR901A`:「轉Excel檔的功能 需要輸入""轉出路徑""。」 |
| `OFDR552` `OFDR904` | 4 | `OFDR552`:「異動日期 或 異動生效日期 必需擇一輸入!」(**唯一的「至少一個範圍」防護**) |
| `OFDR002` `OFDR051` `OFDR057` `OFDR058` `OFDR081` `OFDR088`~`OFDR094` `OFDR109` `OFDR111` `OFDR551` `OFDR553` `OFDR601A`~`OFDR606A` `OFDR609` | 2 | 一條 `FormvalidatorManager` 轉發 + 一條日期起迄 |
| `OFDR001B` `OFDR003` `OFDR052` `OFDR131` `OFDR132` `OFDR134` | 1 | 只有 `FormvalidatorManager` 轉發;業務檢核全靠 Designer 的必填設定(不 Read)與 SP |

#### 7.11.2 過濾(無提示)型:SP 層 37 / 38 個有

這一節是 `ofdr1.md` `nfdr1.md` 寫不出來的。分四類,每類舉一個錨點,完整分佈見附錄 A 的「過濾樣板」欄:

| 樣板 | 效果 | SP 數 | 錨點(例) |
|---|---|---|---|
| **`欄 = NVL(i參數, 欄)`**(共 164 處) | 參數空時「不篩」,但**該欄為 NULL 的列仍被丟掉**(`NULL = NULL` 為 UNKNOWN) | **37** | `DB/SP/S_OTA_OFDR606A_GET.SQL:63-64` · `DB/SP/S_OTA_OFDR088_GET.sql:76` |
| **`NVL(TRIM(x), 欄)`** | 同上,`ofdi2.md` 記的 24 支同樣板 | 8(`051` `057` `081` `081T1` `088` `089` `093` + 誤名檔 `601`) | `DB/SP/S_OTA_OFDR088_GET.sql:77-78` |
| **`INNER JOIN` 對不到就消失** | 沒有寄發設定(`OFD132A`)/ 沒有結帳列(`OFD303`)/ 沒有受益人主檔(`BMS001A`)的列不印 | 34(0 個 `INNER JOIN` 的只有 `050_GET` `052` `081T1` `093`) | `DB/SP/S_OTA_OFDR042_GET.SQL:574-576` · `DB/SP/S_OTA_OFDR002_GET.SQL:42-44` · `DB/SP/S_OTA_OFDR133_GET.SQL:74-76` |
| **`INNER JOIN` 全域暫存表** | 暫存表被別人清掉 → 零筆 | 7(`042` `050_EXE` `054` `085` `086` `133` `554` 的 `DSMR008T0`) | `DB/SP/S_OTA_OFDR133_GET.SQL:84-85` |
| **寫死狀態值** | `FUND_STATUS = '0'`(`904`)、`REDEM_PROC_CODE = '5'`(`050`)、`TRUST_CODE = '5'`(`051`)、`ALLOT_PROC_CODE NOT IN ('D','9')`(`051` `052`)、`OFD081.GAGENT_CD <> '0000000000'`(`052`) | 6 | `DB/SP/S_OTA_OFDR904_GET.sql:47` · `DB/SP/S_OTA_OFDR051_GET.SQL:44-46` · `DB/SP/S_OTA_OFDR052_GET.sql:175-176` |
| **資料權限** | 非豁免部門只看自己的受益人 | 1(`042`) | `DB/SP/S_OTA_OFDR042_GET.SQL:477-562` |

`<> '值'` 樣板(`ofdr1.md` E4 型)本片 SP 內有 16 處,但都是對 NOT NULL 的代碼欄(`OMNIBUS_PCD_*` `GAGENT_CD` `FUND_CURRENCY`),**假設**風險低。`NOT IN (...)` 12 處全是常數清單,不是子查詢,無 NULL 陷阱。`= ''` 0 處。全形空白 U+3000 1 處(`DB/SP/S_OTA_OFDR094_GET.sql:115` 的 `INNER JOIN FSK003` 前),在 SQL 空白位置,Oracle 會把它當識別字錯誤還是空白?——**PL/SQL 編譯時全形空白是非法字元**,但這個 SP 顯然在 DB 上跑得動(`OFDR094` 在 csproj、有 UI),**假設**版控內的檔與 DB 上的版本不同步,或該行實際是 tab 被 cp950 解碼誤判。列為附錄 E13 待驗。

#### 7.11.3 警示與詢問

| 畫面 | 訊息 | 類型 | 錨點 |
|---|---|---|---|
| `OFDR050` | 此交易日期已有資料, 是否重新產生!? | **詢問** | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:158` |
| `OFDR050` | 製作資料成功! / 執行失敗,請檢查 (…) | 警示 | `:197` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:233` |
| `OFDR001B` | (PO 回的 `ReturnMessage`,零筆時為空字串) | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR001B.cs:189` |
| `OFDR042` | (`befPostCheck` 回的訊息) | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR042.cs:161` |
| `OFDR901A` `OFDR904` | 無符合查詢條件的資料。/ 執行成功 | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:320` · `:342` |

### 7.12 其餘各支(分群帶過)

深寫過的 26 支之外,其餘 17 支活的按 §0.6 的業務線分群,只記「跟群內範本的差異」。

#### 7.12.1 結餘單位數查核:`OFDR003`

| 畫面 | 中文名 | 跟 `OFDR001B` 的差異 |
|---|---|---|
| `OFDR003` | 境外基金受益人結餘清冊 | 條件多 `BAL_TYPE`(個人 / 綜合 / 全部)`FH_CD` `BF_NO`;SP 先呼叫 `S_TA_IMP_OFD302_RANGE` 重建淨值快取 `OFD302AT2`(往前推三年,`DB/SP/S_OTA_OFDR003_GET.SQL:75-76`),再逐受益人算成本與市值寫自用暫存 `OFDR003T1`;9 個 `INNER JOIN` 0 個 `LEFT JOIN`——沒有 `BMS001A` 列的受益人整筆消失 |

#### 7.12.2 確認書家族:`OFDR054` `OFDR085` `OFDR086`(`OFDR042` `OFDR050` `OFDR554` 已深寫)

| 畫面 | 中文名 | 跟 `OFDR554`(§7.4)的差異 |
|---|---|---|
| `OFDR054` | 境外基金申購確認書 | 主表 `OFD221`(申購)+ `OFD082` `OFD083`(費率);6 游標;5 張 `.rpt` UI 只要 1 |
| `OFDR085` | 境外基金買回確認書 | 主表 `OFD252`(個人贖回);列印前 `Is_OFD303_DONE` 自組 SQL 查勾選基金是否已做分配確認,**`IN` 清單串接**(§2.5);訊息「必須先做綜合帳戶贖回/轉換分配確認作業(OFDB090),才可列印報表!」(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR085_PO.cs:182`) |
| `OFDR086` | 境外基金轉換確認書 | 主表 `OFD253`(綜合贖回 / 轉換);與 `OFDR085` 幾乎逐行同文(419 vs 421 行),含同一條 `IN` 串接(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR086_PO.cs:132`)——**成對報表,改一邊要改另一邊** |

#### 7.12.3 交易明細與試算檢核:10 支

| 畫面 | 中文名 | 特徵 |
|---|---|---|
| `OFDR051` | 總代理-申購明細表列印作業 | 條件 `TYPE`(交易類別)`SYSTEM_ID`(來源)`KIND`(成功 / 失敗)+ 日期 + 基金 + 銷售機構,9 個參數是本片最多;SP 讀 `CTL107` `CTL114` `CTL965` 代碼表;寫死 `TRUST_CODE = '5'` 且 `NVL(TRIM(TRUST_AGENT_ID),'0') = '0'`(公司自身綜合帳戶,`DB/SP/S_OTA_OFDR051_GET.SQL:44-46`)〔客戶特定〕 |
| `OFDR052` | 銷售機構-申購明細表 | 3 張版型依 `SYSTEM_ID`;呼叫版控外 `F_TA_GetAgent` `S_TA_IMP_OFD300T1_RANGE2`;寫死 `GAGENT_CD <> '0000000000'`(`DB/SP/S_OTA_OFDR052_GET.sql:176`)〔客戶特定〕 |
| `OFDR057` `OFDR058` | 境外個人 / 綜合帳戶申購試算檢核清單 | 成對(個人 / 綜合),`OFDR058` **借 `OFDR057Model`**;條件多 `AMT` `UNIT` 門檻;伴生 `.cs` 檔名多一個 `1`(§2.7.1) |
| `OFDR081` | 贖回交易日報表(境外) | SP 先呼叫 `S_OTA_OFDR081T1` 把明細塞進**全域** `OFDR081T1`(`DELETE` 全表,`DB/SP/S_OTA_OFDR081T1.sql:14-16`),再呼叫 `S_TA_IMP_OFD302_RANGE`,5 個游標;參數名用第三套前綴 `striXxx`(`DB/SP/S_OTA_OFDR081_GET.sql:3-9`);30 個 `LEFT JOIN` 本片最多;4 張 `.rpt` UI 只要 1 |
| `OFDR088` | 境外贖回沖銷明細表 | `ROW_NUMBER() OVER (PARTITION BY REDEM_NO)` 讓同一贖回書號的淨值 / 單位數只在第一列顯示(`DB/SP/S_OTA_OFDR088_GET.sql:61-62` · `:91-92`);`OFD251.FH_CD = xFH_CD` **不加 `NVL`**,基金公司不選就零筆(`:75`) |
| `OFDR089` `OFDR090` | 個人 / 綜合帳戶贖回試算檢核清單 | 成對;條件 `DIFF_TYPE` `AMT` `UNIT`;**中文名沒有「境外」**(本片 6 支不帶「境外」的其中 2 支) |
| `OFDR093` `OFDR094` | 境外個人 / 綜合帳戶轉換試算檢核清單 | 成對;條件 `UNIT_OUT` `AMT_OUT` `AMT_IN` `UNIT_IN`;`094` 的 SP 有全形空白(§7.11.2) |

#### 7.12.4 受益人資料查核:`OFDR109` `OFDR111`

| 畫面 | 中文名 | 特徵 |
|---|---|---|
| `OFDR109` | 境外受益人銀行帳戶資料查核表 | 條件 `UPDATEDATE_ST/END` `BF_NO_ST/END`,全可空;SP 66 行讀 `OFD110`(銀行帳戶)`CTL014` `OFD020V` |
| `OFDR111` | 境外受益人綜合帳戶資料查核表 | UI 與 `OFDR109` 逐行同構(都 193 行);SP 51 行讀 `OFD112` `FNDV01`(View,在版控 `DB/View/FNDV01.SQL`) |

#### 7.12.5 網路交易檢核:`OFDR601A` `OFDR602A` `OFDR604A` `OFDR605A`(`603A` `606A` 已深寫)

四支 UI 同模子(227~232 行),差別只在條件欄名與 SP 讀的網路交易表(§7.2.3)。`OFDR605A` 的 SP 439 行、寫自用暫存 `OFDR605AT1`,是六支裡唯一有暫存的。

## 8. 跨模組共用

```text
[圖] 本片 37 個 SP 讀哪些模組的表,以及本片寫的暫存表有沒有別人讀
圖中文字:別的模組建的表(被幾個 SP 讀) / BMS001A BMS999 / BMS 受益人 34 / 6 / OFD081 OFD062 OFD082 083 / OFD 基金 公司 費率 34 29 5 5 / OFD221 OFD251~254 / 申購 贖回 13 4 10 10 3 / OFD303~311 OFD302 / 結帳批次 結餘 淨值 / CRM001A 002A 007A / 銷售關係 權限用 / OFD281~283 OFD551~555 OFD904 / 受益分配 定期定額 / OFD601 607 620 621 651~667 / 網路交易 OTA 側 / OFD132A / 寄發設定 7 個 SP 兩種類別碼 / COD009 CTL000 CTL014 FSK003 / 員工 系統設定 代碼 幣別 / 本片 37 個 SP(OTA) / 26 個寫暫存表 / 全域 6 張 自用 18 張 / 11 個純讀 / 001 050_GET 052 109 111 131 132 134 606A / EC 8 個 SP 版控外 / 讀什麼表不可知 / 本片的表被誰用 / 沒有業務主檔 / 寫的全是暫存 / 工作表 / OFDR050T1~9 OFDR042T* 等 / grep 版控內找不到別的讀者 / DSMR008T0 T4 名字屬於 DSMR008 / 可能跨模組互蓋 DSMR008 的 SP 版控外
```

*圖:圖 6 跨模組,對應 §8。上兩排是被讀的 74 張表按建立模組分群(灰虛=別人的);中排是本片 SP 的讀寫分佈;下排是本片寫出去的東西——沒有業務主檔,只有暫存表,其中 DSMR008T0 / T4 借用了另一個模組報表的暫存表名(紫框)。*

### 8.1 本片讀別人的:74 張表,前四張佔了大半

`ofdr1.md §8.1` 的結論是「36 支報表真正讀的表在版控外的 SP 裡,本表列不出來」。**本片 OTA 那軌列得出來**(EC 那軌一樣列不出來)。§2.3 的前四張(`BMS001A` `OFD081` `FSK003` `OFD062`)被 29~34 個 SP 讀,**改這四張的任何欄位名,要重編譯的不是 C#,是 37 個 SP**——C# 端只認結果集欄名(xsd),SP 內部 `SELECT` 的來源欄改名,C# 不會編譯錯,要跑到才知道。

| 被讀的表 | 誰寫入(推測,依 `ofd*.md` 各片) | 本片誰讀(SP 數) | 本片誰**也寫** |
|---|---|---|---|
| `BMS001A` `BMS999` | BMS 受益人維護 | 34 / 6 | — |
| `OFD081` `OFD062` `OFD082` `OFD083` `OFD013` `OFD017A` `OFD019` `OFD019A` `OFD020` `OFD020A` | OFD 基金 / 公司 / 費率 / 銀行維護(`ofd123.md`) | 34 / 29 / 5 / 5 / 4 / 1 / 1 / 4 / 1 / 2 | — |
| `OFD221` `OFD220` `OFD224` | 申購作業(`ofd4.md`) | 13 / 3 / 2 | — |
| `OFD251` `OFD252` `OFD253` `OFD254` `OFD256` | 贖回 / 轉換作業(`ofd5.md`) | 4 / 10 / 10 / 3 / 1 | — |
| `OFD303` `OFD304` `OFD305` `OFD306` `OFD310` `OFD311` `OFD302` | 結帳批次(`ofdb.md`) | 3 / 1 / 8 / 5 / 1 / 2 / 3 | — |
| `OFD281` `OFD282` `OFD283` | 受益分配作業(`ofd6.md`) | 4 / 1 / 4 | — |
| `OFD551` `OFD552` `OFD554` `OFD555` `OFD904` | 定期定額(`ofd7.md`) | 3 / 5 / 2 / 2 / 1 | — |
| `OFD601` `OFD607` `OFD620` `OFD621` `OFD651`~`OFD653` `OFD663` `OFD664` `OFD666` `OFD667` | 網路交易(`ec.md` / OTA 網路交易) | 5 / 1 / 1 / 1 / 2 / 1 / 1 / 1 / 1 / 1 / 1 | — |
| `OFD132A` | 文件寄發設定 | 7 | — |
| `OFD110` `OFD112` `OFD104` `OFD199` `OFD300` `OFD300T1` `OFD493` | 各 OFD 主檔 | 各 1~4 | — |
| `COD009` `COD006A` | COD 員工 / 代碼(`cod.md`) | 9 / 3 | — |
| `CRM001A` `CRM002A` `CRM007A` | CRM 銷售關係(`crm.md`) | 各 1(`OFDR042` 資料權限) | — |
| `CTL000` `CTL014` `CTL107` `CTL114` `CTL965` | CTL 系統設定 / 代碼 | 9 / 4 / 1 / 1 / 1 | — |
| `BBS013B` `SAL071` | BBS / SAL 獎金參數 | 1 / 1 | — |
| `FSK003` `FNDV01` `OFD068A_V02` | 幣別 / View | 29 / 1 / 15 | — |
| **全域暫存** `OFD068AT0` `DSMR008T0` `DSMR008T4` `TA_DEPT_EMP` `OFD302AT2` `OFDR081T1` | **本片的 SP 自己**(也可能被 `DSM*` / `OFDB*` 其他 SP 用——`DSMR008T*` 的命名顯示它原屬 `DSMR008`) | 18 / 7 / 5 / 1 / 5 / 1 | **同一批 SP** |
| **自用暫存** `OFDR002T1` `OFDR003T1` `OFDR042T1/T2/T4` `OFDR050T1`~`T9` `OFDR552T1` `OFDR605AT1` `OFDR901T1` `OFDR904T1` | 本片 SP | 各自 | 各自 |

**`DSMR008T0` `DSMR008T4` 的名字屬於 `DSMR008`(另一個模組的報表)**,本片 7 個 SP 借用——若 `DSMR008` 的 SP 也在跑,就是跨模組互蓋(E3)。`grep -rli DSMR008T DB/SP/` 只命中本片 7 個,`DSMR008` 自己的 SP 不在版控,無法確認。

### 8.2 本片的表被誰用:只有暫存表,而且找不到讀者

本片沒有任何一張業務主檔。寫入的 20 幾張全是暫存 / 工作表(§2.4)。**`grep -rli "OFDR050T\|OFDR042T\|OFDR901T1" Dev/ DB/`** 只命中本片自己的 SP 與 PO——沒有別的模組讀它們。`OFD068AT0` 也一樣,18 個寫它的 SP 全在本片(`grep -li OFD068AT0 DB/SP/*` = 18,全是 `S_OTA_OFDR*`)。

### 8.3 共用元件

| 元件 | 用在哪 | 原始�礼 |
|---|---|---|
| `xReportForm` | 43 支 UI 基底 | 無,框架 DLL(`Vendor.Product.UI.MiddleForm`),從呼叫端反推 |
| `CRReportTransfer.TransferFileByte` | 43 支 Ctl 的 `GetReportObject` | 無 |
| `TransferVDBHelper.TransferDataSet` / `TransferTable` | OTA Ctl 整個 DataSet 搬 / EC Ctl 逐表搬 | 無 |
| `EVAStringHelper.GetParamValue` | OTA 36 支 PO 取參數 | `Vendor.Product.TA.ServerUtility.SQLHelper`,本文未讀 |
| `ClientOTABizUtility` | OTA 20 支 UI 宣告(`m_OTABiz`),**多數只宣告沒呼叫**(`OFDR601A.cs:29` 宣告後全檔無使用) | `Dev/ATLAS.OTA` 側,本文未讀 |
| `UIExcelHelper.GenExcelFile` | `OFDR901A` `OFDR904` 轉 Excel | 本文未讀 |
| `SHORE_ID.OffShore` | 21 支 UI 鎖境外基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301`(`ofdr1.md §7.2.1` 已定位) |
| `f_FormatStringToTable` | 7 個 SP 把逗號串轉表 | **不在版控** |
| `HIDE_ID_NO_NEW` `HIDE_PHONE_NO` | 6 個確認書 / 通知書 SP 遮罩個資 | `HIDE_PHONE_NO` 在 `DB/Function/HIDE_PHONE_NO.SQL`;`HIDE_ID_NO_NEW` **不在版控** |
| `GET_FH_BF_NO` | `S_OTA_OFDR051_GET` | 不在版控 |
| `S_TA_IMP_OFD302_RANGE` | 5 個 SP 重建淨值快取 | `DB/SP/S_TA_IMP_OFD302_RANGE.SQL` |
| `F_OTA_GET_CRNCYAMTDEC` | 4 個 SP 取幣別小數位 | `DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL` |
| `F_TA_GetAgent` `S_TA_IMP_OFD300T1_RANGE2` | `OFDR052` `OFDR081` | 不在版控 |

### 8.4 改動影響面速查

| 你要改的 | 會打到 | 怎麼找 |
|---|---|---|
| `OFD081` / `BMS001A` 欄位 | 34 個 SP;C# 不會編譯錯 | `grep -li <表名> DB/SP/S_OTA_OFDR*`,再看各 SP `SELECT` 清單 |
| `OFD132A` 寄發旗標 | 7 個確認書 / 對帳單 / 通知書 SP 的 `WHERE`(`:583-591` 樣板) | 同上;注意 `STATEMENT_CODE` 兩種值(E12) |
| `OFD068A_V02` View 欄位 | 15 個 SP 的 `INSERT INTO OFD068AT0(...)` 欄位清單 | 三個 View 版本 `V000` `V01` `V02` 要一起看 |
| `OFDR001BModel.xsd` | `OFDR001B` **和** `OFDR002` | §7.3.2 |
| `OFDR057Model.xsd` / `OFDR131Model.xsd` | `OFDR058` / `OFDR132` `OFDR134` | §0.3 列 2 |
| `OFDR085` 的檢核訊息 | `OFDR086` 同文 | §7.12.2 |
| 任一 `OFDR60xA`(OTA)的欄位 | **不會**自動打到 `OFDR60x`(EC),但業務上是同一張報表,要問要不要一起改 | §7.2 |
| `COD009.DEPT_NO` 的部門碼 | `OFDR042` 資料權限豁免清單 `M2` `C2` `G16` `G17` 寫死在 SP | `DB/SP/S_OTA_OFDR042_GET.SQL:488` |
| 選單表拔掉 EC 那 7 支 | 沒有任何程式相依,可以直接拔 | §7.10 |

## 附錄 A. 資料表總表

OTA 37 個 SP(不含誤名檔與 `s_OTA_GetFNBusinessDay`)剝註解後從 `FROM` / `JOIN` 抓出的實體表 / View,扣掉 CTE 別名與暫存表,共 74 張。EC 8 個 SP 不在版控,不計。

| 表 | 讀它的 SP 數 | 哪些報表(SP 代號數字;`081T1` `050_EXE` 為 helper) |
|---|---|---|
| `BMS001A` | 34 | (34 個 SP,見 §2.3) |
| `OFD081` | 34 | (34 個 SP,見 §2.3) |
| `FSK003` | 29 | (29 個 SP,見 §2.3) |
| `OFD062` | 29 | (29 個 SP,見 §2.3) |
| `OFD068A_V02` | 15 | (15 個 SP,見 §2.3) |
| `OFD221` | 13 | 001 003 042 050 051 052 054 057 058 553 554 901A 904 |
| `OFD252` | 10 | 001 042 050 081 081T1 085 088 089 090 904 |
| `OFD253` | 10 | 001 042 050 081 081T1 086 088 093 094 904 |
| `COD009` | 9 | 042 081 081T1 551 601A 602A 603A 604A 901A |
| `CTL000` | 9 | 051 057 058 088 089 090 093 094 904 |
| `OFD305` | 8 | 001 003 042 050 054 085 554 904 |
| `OFD132A` | 7 | 042 050 054 085 086 133 554 |
| `BMS999` | 6 | 042 054 085 086 133 554 |
| `OFD020V` | 6 | 085 109 131 132 133 134 |
| `OFD082` | 5 | 050 054 085 086 554 |
| `OFD083` | 5 | 050 054 085 086 554 |
| `OFD306` | 5 | 001 003 042 050 904 |
| `OFD552` | 5 | 050 551 552 553 605A |
| `OFD601` | 5 | 601A 602A 603A 604A 606A |
| `CTL014` | 4 | 051 109 604A 606A |
| `OFD013` | 4 | 131 132 133 134 |
| `OFD019A` | 4 | 551 601A 602A 604A |
| `OFD199` | 4 | 052 551 601A 604A |
| `OFD251` | 4 | 042 081 081T1 088 |
| `OFD281` | 4 | 131 132 133 134 |
| `COD006A` | 3 | 552 553 605A |
| `OFD254` | 3 | 042 050 088 |
| `OFD283` | 3 | 132 133 134 |
| `OFD302` | 3 | 042 050 904 |
| `OFD551` | 3 | 551 552 605A |
| `OFD020A` | 2 | 050 081 |
| `OFD104` | 2 | 003 904 |
| `OFD110` | 2 | 050 109 |
| `OFD220` | 2 | 051 052 |
| `OFD224` | 2 | 051 057 |
| `OFD303` | 2 | 001 002 |
| `OFD311` | 2 | 001 904 |
| `OFD554` | 2 | 552 605A |
| `OFD555` | 2 | 552 605A |
| `OFD651` | 2 | 602A 603A |
| `BBS013B` | 1 | 042 |
| `CRM001A` | 1 | 042 |
| `CRM002A` | 1 | 042 |
| `CRM007A` | 1 | 042 |
| `CTL107` | 1 | 051 |
| `CTL114` | 1 | 051 |
| `CTL965` | 1 | 051 |
| `FNDV01` | 1 | 111 |
| `OFD017A` | 1 | 904 |
| `OFD019` | 1 | 052 |
| `OFD020` | 1 | 081 |
| `OFD030` | 1 | 052 |
| `OFD068A_V000` | 1 | 901A |
| `OFD068A_V01` | 1 | 081 |
| `OFD071` | 1 | 052 |
| `OFD112` | 1 | 111 |
| `OFD256` | 1 | 089 |
| `OFD282` | 1 | 131 |
| `OFD300` | 1 | 042 |
| `OFD300T1` | 1 | 052 |
| `OFD304` | 1 | 001 |
| `OFD310` | 1 | 001 |
| `OFD493` | 1 | 001 |
| `OFD607` | 1 | 606A |
| `OFD620` | 1 | 601A |
| `OFD621` | 1 | 601A |
| `OFD652` | 1 | 602A |
| `OFD653` | 1 | 603A |
| `OFD663` | 1 | 604A |
| `OFD664` | 1 | 604A |
| `OFD666` | 1 | 605A |
| `OFD667` | 1 | 605A |
| `OFD904` | 1 | 553 |
| `SAL071` | 1 | 901A |

暫存 / 工作表(不算實體表,DDL 全部不在 `DB/Table/`):

| 類 | 表 | 隔離鍵 |
|---|---|---|
| 全域 | `OFD068AT0` `DSMR008T0` `DSMR008T4` `TA_DEPT_EMP` `OFDR081T1` `OFD302AT2` | 無 |
| 自用 | `OFDR002T1` `OFDR003T1` `OFDR042T1` `OFDR042T2` `OFDR042T4` `OFDR050T1` `OFDR050T2` `OFDR050T3` `OFDR050T4` `OFDR050T5` `OFDR050T6` `OFDR050T7` `OFDR050T8` `OFDR050T9` `OFDR552T1` `OFDR605AT1` `OFDR901T1` `OFDR904T1` | `USERDOMAIN` |
| EC 死方法內 | `IPJR601T1` `IPJR601T2`(及 `602`~`605` 同型) | `USERDOMAIN`,但沒人呼叫 |

## 附錄 B. SP / Function / Trigger / View

### B.1 在版控(`DB/`)

| 類 | 名 | 檔 |
|---|---|---|
| SP(36 支報表各一) | `S_OTA_OFDR001_GET` `S_OTA_OFDR002_GET` `S_OTA_OFDR003_GET` `S_OTA_OFDR042_GET` `S_OTA_OFDR050_GET` `S_OTA_OFDR051_GET` `S_OTA_OFDR052_GET` `S_OTA_OFDR054_GET` `S_OTA_OFDR057_GET` `S_OTA_OFDR058_GET` `S_OTA_OFDR081_GET` `S_OTA_OFDR085_GET` `S_OTA_OFDR086_GET` `S_OTA_OFDR088_GET` `S_OTA_OFDR089_GET` `S_OTA_OFDR090_GET` `S_OTA_OFDR093_GET` `S_OTA_OFDR094_GET` `S_OTA_OFDR109_GET` `S_OTA_OFDR111_GET` `S_OTA_OFDR131_GET` `S_OTA_OFDR132_GET` `S_OTA_OFDR133_GET` `S_OTA_OFDR134_GET` `S_OTA_OFDR551_GET` `S_OTA_OFDR552_GET` `S_OTA_OFDR553_GET` `S_OTA_OFDR554_GET` `S_OTA_OFDR601A_GET` `S_OTA_OFDR602A_GET` `S_OTA_OFDR603A_GET` `S_OTA_OFDR604A_GET` `S_OTA_OFDR605A_GET` `S_OTA_OFDR606A_GET` `S_OTA_OFDR901A_GET` `S_OTA_OFDR904_GET` | `DB/SP/<同名>.SQL` / `.sql`(大小寫混用) |
| SP(製作資料) | `S_OTA_OFDR050_EXE` | `DB/SP/S_OTA_OFDR050_EXE.SQL` |
| SP(內部 helper) | `S_OTA_OFDR081T1` `S_TA_IMP_OFD302_RANGE` | `DB/SP/S_OTA_OFDR081T1.sql` · `DB/SP/S_TA_IMP_OFD302_RANGE.SQL` |
| SP(**誤名檔**) | 檔名 `S_OTA_OFDR601_GET`,內容 `S_OTA_OFDR051_GET` | `DB/SP/S_OTA_OFDR601_GET.SQL:1` |
| Function | `F_OTA_GET_CRNCYAMTDEC` `HIDE_PHONE_NO` | `DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL` · `DB/Function/HIDE_PHONE_NO.SQL` |
| View | `OFD068A_V02` `FNDV01` | `DB/View/OFD068A_V02.SQL` · `DB/View/FNDV01.SQL` |
| Trigger | 無 | — |

### B.2 不在版控

| 類 | 名 | 誰用 |
|---|---|---|
| SP(EC) | `S_EC_IPJR601_GET` `S_EC_IPJR602_GET` `S_EC_IPJR603_GET` `S_EC_IPJR604_GET` `S_EC_IPJR605_GET` `S_EC_IPJR606_GET` `S_EC_OFDR609_Get` `S_EC_OFDR609D_Get` | EC 7 支 PO |
| SP(helper) | `S_TA_IMP_OFD300T1_RANGE2` | `S_OTA_OFDR052_GET` |
| Function | `F_TA_GetAgent` `f_FormatStringToTable` `HIDE_ID_NO_NEW` `GET_FH_BF_NO` | `052` `081` / 7 個寄發家族 SP / 6 個遮罩 SP / `051` |
| View | `OFD068A_V000` `OFD068A_V01` `OFD020V` | `901A` / `081` / 6 個 SP |
| SP(死碼註解內) | `s_OFDR601_Get` 等 14 個 T-SQL 名 | EC `MSSQL/` PO,整檔註解 |

## 附錄 C. 代碼對照

見 §2.10。全部從 SP 參數註解與 UI 選項文字反推,**沒有任何一個在 `CTL014` 以外的代碼表版控腳本裡查到**;`CTL014.SOURCETYPE = '960'`(網路交易進度)與 `'948'`(付款方式)兩組是本片唯一走代碼表的(`DB/SP/S_OTA_OFDR606A_GET.SQL:29` · `:36`),其餘 `OMNIBUS_ID` `EC_ALLOT_PCODE` `TRAN_PAY_WAY` `SYSTEM_ID` `AGENT_ID` 的值域全寫死在 SP 的 `CASE` 或 UI 的 `if`。

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module`**——本片是跨兩個專案的切片。以下自列 50 支處置表。圖例:**已寫** = §7 有專屬小節或專屬表列;**表格帶過** = 只在 §3 清冊與 §7.12 出現。

| # | 代號 | 軌 | 處置 | PO 基底 | `m_db` | 資料來源 | SP 在版控 | `.rpt` 在版控 | 在 csproj |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `OFDR001B` | OTA | **已寫** §7.3 | `IOFDR001B_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 2 | `OFDR002` | OTA | **已寫** §7.3 | `IOFDR002_PO` | 有初始化 | SP+SQL | 是 | 是(1/1) | 是 |
| 3 | `OFDR003` | OTA | 表格帶過 §7.12.1 | `IOFDR003_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 4 | `OFDR042` | OTA | **已寫** §7.8 | `IOFDR042_PO` | 有初始化 | SP+SQL | 是 | 是(4/4) | 是 |
| 5 | `OFDR050` | OTA | **已寫** §7.7 | `IOFDR050_PO` | 有初始化 | SP+SQL | 是 | **否(懸空 `OFDR050RPS1`)** | 是 |
| 6 | `OFDR051` | OTA | 表格帶過 §7.12.3 | `IOFDR051_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 7 | `OFDR052` | OTA | 表格帶過 §7.12.3 | `IOFDR052_PO` | 有初始化 | SP | 是 | 是(3/3) | 是 |
| 8 | `OFDR054` | OTA | 表格帶過 §7.12.2 | `IOFDR054_PO` | 有初始化 | SP | 是 | 是(5/5) | 是 |
| 9 | `OFDR057` | OTA | 表格帶過 §7.12.3 | `IOFDR057_PO` | 有初始化 | SP | 是 | 是(2/2) | 是 |
| 10 | `OFDR058` | OTA | 表格帶過 §7.12.3 | `IOFDR058_PO` | 有初始化 | SP | 是 | 是(2/2) | 是 |
| 11 | `OFDR081` | OTA | 表格帶過 §7.12.3 | `IOFDR081_PO` | 有初始化 | SP | 是 | 是(4/4) | 是 |
| 12 | `OFDR085` | OTA | 表格帶過 §7.12.2 | `IOFDR085_PO` | 有初始化 | SP+SQL | 是 | 是(4/4) | 是 |
| 13 | `OFDR086` | OTA | 表格帶過 §7.12.2 | `IOFDR086_PO` | 有初始化 | SP+SQL | 是 | 是(3/3) | 是 |
| 14 | `OFDR088` | OTA | 表格帶過 §7.12.3 | `IOFDR088_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 15 | `OFDR089` | OTA | 表格帶過 §7.12.3 | `IOFDR089_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 16 | `OFDR090` | OTA | 表格帶過 §7.12.3 | `IOFDR090_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 17 | `OFDR093` | OTA | 表格帶過 §7.12.3 | `IOFDR093_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 18 | `OFDR094` | OTA | 表格帶過 §7.12.3 | `IOFDR094_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 19 | `OFDR109` | OTA | 表格帶過 §7.12.4 | `IOFDR109_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 20 | `OFDR111` | OTA | 表格帶過 §7.12.4 | `IOFDR111_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 21 | `OFDR131` | OTA | **已寫** §7.5 | `IOFDR131_PO` | 有初始化 | SP+SQL | 是 | 是(1/1) | 是 |
| 22 | `OFDR132` | OTA | **已寫** §7.5 | `IOFDR132_PO` | 有初始化 | SP+SQL | 是 | 是(1/1) | 是 |
| 23 | `OFDR133` | OTA | **已寫** §7.5 | `IOFDR133_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 24 | `OFDR134` | OTA | **已寫** §7.5 | `IOFDR134_PO` | 有初始化 | SP+SQL | 是 | 是(1/1) | 是 |
| 25 | `OFDR551` | OTA | **已寫** §7.4 | `IOFDR551_PO` | 有初始化 | SP | 是 | 是(2/2) | 是 |
| 26 | `OFDR552` | OTA | **已寫** §7.4 | `IOFDR552_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 27 | `OFDR553` | OTA | **已寫** §7.4 | `IOFDR553_PO` | 有初始化 | SP | 是 | 是(3/3) | 是 |
| 28 | `OFDR554` | OTA | **已寫** §7.4 | `IOFDR554_PO` | 有初始化 | SP | 是 | 是(5/5) | 是 |
| 29 | `OFDR601A` | OTA | **已寫** §7.2 | `IOFDR601A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 30 | `OFDR602A` | OTA | **已寫** §7.2 | `IOFDR602A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 31 | `OFDR603A` | OTA | **已寫** §7.2 | `IOFDR603A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 32 | `OFDR604A` | OTA | **已寫** §7.2 | `IOFDR604A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 33 | `OFDR605A` | OTA | **已寫** §7.2 | `IOFDR605A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 34 | `OFDR606A` | OTA | **已寫** §7.2 | `IOFDR606A_PO` | 有初始化 | SP | 是 | 是(1/1) | 是 |
| 35 | `OFDR901A` | OTA | **已寫** §7.6 | `IOFDR901A_PO` | 有初始化 | SP | 是 | **否(懸空 `OFDR901ARPS1`)** | 是 |
| 36 | `OFDR904` | OTA | **已寫** §7.6 | `IOFDR904_PO` | 有初始化 | SP | 是 | 是(4/4) | 是 |
| 37 | `OFDR601` | EC | **已寫** §7.2 §7.9 | `IOFDR601PO` | 有初始化 | SP | **否** | 是(3/3) | 是 |
| 38 | `OFDR602` | EC | **已寫** §7.2 §7.9 | `IOFDR602PO` | 有初始化 | SP+SQL | **否** | 是(3/3) | 是 |
| 39 | `OFDR603` | EC | **已寫** §7.2 §7.9 | `IOFDR603PO` | 有初始化 | SP+SQL | **否** | 是(3/3) | 是 |
| 40 | `OFDR604` | EC | **已寫** §7.2 §7.9 | `IOFDR604PO` | 有初始化 | SP+SQL | **否** | 是(2/2) | 是 |
| 41 | `OFDR605` | EC | **已寫** §7.2 §7.9 | `IOFDR605PO` | 有初始化 | SP+SQL | **否** | 是(2/2) | 是 |
| 42 | `OFDR606` | EC | **已寫** §7.2 §7.9 | `IOFDR606PO` | 有初始化 | SP | **否** | 是(2/2) | 是 |
| 43 | `OFDR607` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(3/3) | **否** |
| 44 | `OFDR608` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(2/2) | **否** |
| 45 | `OFDR609` | EC | **已寫** §7.9 | `IOFDR609PO` | 有初始化 | SP | **否** | 是(4/4) | 是 |
| 46 | `OFDR610` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(1/1) | **否** |
| 47 | `OFDR611` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(1/1) | **否** |
| 48 | `OFDR612` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(1/1) | **否** |
| 49 | `OFDR613` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(1/1) | **否** |
| 50 | `OFDR690` | EC | **已寫**(死碼群)§7.10 | (整檔註解) | 無 PO(死碼) | — | — | 是(5/5) | **否** |

### D.1 兩個專案內不在本片的 7 支

| 代號 | 專案 | 已知特徵 | 誰寫 |
|---|---|---|---|
| `OFDR561` | OTA | 境外受益人扣款帳戶資料查核表;`IOFDR561_PO` 派、`S_OTA_OFDR561_GET` 在版控(讀 `OFD562` `OFD019A`)——**與 `ofdr1.md` 附錄 D.1 記的「`Basic_PO` 派、`SqlDbType`」不同,那是 OFD 專案的同號** | 待下一片 |
| `OFDR562` | OTA | 境外扣款授權書集保退件清冊;同上 | 待下一片 |
| `OTAR901` | OTA | 弱勢族群交易回訪報表(境外);`.rpt` 以 `None` 進 csproj | `misc.md` |
| `TRPR001` | OTA | 申報平台月報;PO 檔名少一個 `R`(`TRP001_PO.cs`) | `misc.md` |
| `IPJR607` `IPJR901` `IJPR611` | EC | `IJPR611` 的 `OracleDao` 1,682 行是 EC 專案最大的 PO | `misc.md` |

**注意 `OFDR561` / `OFDR562` 同號在 OFD 與 OTA 兩個專案都有**——又一對 (f) 型,但這對**兩邊都沒加後綴**,是本篩查到的第一個「同號無讓號」案例(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR561.cs:131` vs `ofdr1.md` 附錄 D.1)。

## 附錄 E. 讀本文時要注意的地方

依嚴重度排序。每條:缺陷 / 影響 / 錨點 / 嚴重度。**標「型」的欄位對應交辦的缺陷型錄。**

| # | 型 | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|---|
| E1 | **全域暫存表當資料權限** | `OFDR042` 的資料權限(非豁免部門只看自己的受益人)用 `TA_DEPT_EMP` `DSMR008T4` 兩張**沒有使用者鍵**的表算,`DELETE` 全表重建 | 兩個非豁免使用者同時印對帳單:若框架交易未把整個 SP 包在同一交易內,後者的 `DELETE` 清掉前者的權限集 → 前者**零筆或印到別人的客戶**。若交易正確包住,則後者被鎖住等前者印完。**兩種結果都要複驗**(§7.8 第 3 點) | `DB/SP/S_OTA_OFDR042_GET.SQL:493-495` · `:514-515` · `:577-581` | **最高** |
| E2 | **全域暫存表無聲空白** | 18 個 SP 用 `DELETE OFD068AT0; INSERT ... FROM OFD068A_V02` 重建銷售機構名稱,無使用者鍵 | 併發時 `LEFT JOIN OFD068AT0` 對不到 → 報表上**銷售機構名稱空白**,列數不變,使用者不會發現 | `DB/SP/S_OTA_OFDR601A_GET.SQL:36-39` · `DB/SP/S_OTA_OFDR088_GET.sql:43-46` · `:111-112` | 高 |
| E3 | **全域暫存表 + `INNER JOIN` → 零筆** | 7 個 SP 把使用者勾的基金塞進 `DSMR008T0`(無使用者鍵),主查詢 `INNER JOIN DSMR008T0` | 併發時被清掉 → **整張確認書零筆**,或印到別人勾的基金;`DSMR008T0` 名字屬於 `DSMR008`,可能還跨模組互蓋 | `DB/SP/S_OTA_OFDR133_GET.SQL:40-43` · `:84-85` · `DB/SP/S_OTA_OFDR042_GET.SQL:465-467` | 高 |
| E4 | **`.rpt` 不在版控**(報表獨有) | `OFDR050` 要 `OFDR050RPS1`、`OFDR901A` 要 `OFDR901ARPS1`,**檔案、伴生 `.cs`、csproj 宣告三者皆無** | 兩支的 Crystal 預覽 / 列印必定執行期失敗;`OFDR901A` 的 Excel 路與 `OFDR050` 的製作資料路仍活 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR050.cs:228` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR901A.cs:134` | 高 |
| E5 | **Oracle 三值邏輯** | `欄 = NVL(i參數, 欄)` 164 處 / 37 SP;`NVL(TRIM(x), 欄)` 8 SP;`OMNIBUS_PCD_* <> '0'` 3 欄 | 「不篩」時該欄為 NULL 的列**無聲消失**;`OFDR042` 的分配確認檢核在三欄全 NULL 時放行 | `DB/SP/S_OTA_OFDR606A_GET.SQL:63-64` · `DB/SP/S_OTA_OFDR088_GET.sql:76-78` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR042_PO.cs:151-153` | 高 |
| E6 | **`INNER JOIN` 讓對不到的資料無聲消失** | 34 / 38 個 SP 有 `INNER JOIN`;寄發家族 7 支 `INNER JOIN OFD132A`——沒有寄發設定的受益人整筆不印;`OFDR002` `INNER JOIN OFD303`——沒結帳列的基金不檢核也不印 | **過濯(無提示)**;少寄的確認書使用者不會知道 | `DB/SP/S_OTA_OFDR042_GET.SQL:574-576` · `DB/SP/S_OTA_OFDR002_GET.SQL:42-44` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:128-129` | 高 |
| E7 | **檔案存在但不在 csproj** | EC 7 支 UI / Ctl / Pxy 不在 csproj、PO 整檔註解 | 磁碟上 14 支、能跑 7 支;選單若還掛著就是找不到型別;網路交易扣款系列報表(`610`~`613`)在 Oracle 上**不存在** | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/ReportUI.EC.csproj:211-266` · `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/MSSQL/OFDR607_PO.cs` | 高(若業務還要這些報表) |
| E8 | **零「查無資料」提示** | OTA 34 支 PO 零筆回 `AddResultRow(false, 0, string.Empty)`,訊息空;EC 6 支回 `true` + 0 筆 | 使用者按預覽看到空白或空訊息框,分不出「沒資料」「被過濤」「出錯」;與 E5 E6 疊加後無法診斷 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:90-93` · `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:126-129` | 中 |
| E9 | **`catch` 對 null 的 `tran` 呼叫 `Rollback()`** | 37 個 `BeginTransaction` 在 `try` 內、`tran.Rollback()` 在 `catch` 內;`BeginTransaction` 自己拋例外(連線失敗)時 `tran` 為 null | NRE 蓋掉「連不上 DB」的原例外 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR601A_PO.cs:58-61` · `:95-97`(其餘 35 支同型;`OFDR050.Execute` 例外,`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:236-240`) | 中 |
| E10 | **`catch` fail-open / 訊息被吃掉** | `S_OTA_OFDR901A_GET` 查無 `SAL071` 時 `WHEN OTHERS` 設 `strMsg` 後 `RAISE`,最外層只 `DBMS_OUTPUT.put_line` 就正常結束,`OutTB1` `OutTB2` 沒 `OPEN` | C# `LoadDataSet` 對未開游標拋例外 → 進 `catch` → 空訊息;**「查無獎金計算參數檔!」永遠到不了畫面**;`WHEN OTHERS` 還把所有錯誤都說成查無參數 | `DB/SP/S_OTA_OFDR901A_GET.SQL:58-67` · `:267-269` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR901A_PO.cs:86-92` | 中 |
| E11 | **`LIKE` 樣式餵給 `=`(反向)** | `A.AGENT_CODE LIKE AGENT.AGENT_CODE`,右邊是欄值 | `AGENT_CODE` 含 `_` 時單字元萬用,多對到別家銷售機構的名稱 | `DB/SP/S_OTA_OFDR901A_GET.SQL:232` · `:259` | 中 |
| E12 | **成對報表只改一邊 / 寫死常數** | 寄發類別碼:`OFDR050` 用 `STATEMENT_CODE = '0100'`(註解寫「交易確認書」),`054` `085` `086` `554` 四支確認書與 `042` 對帳單、`133` 通知書全用 `'0130'` | 六支「確認書」兩種碼,至少一邊套錯寄發設定 → 該寄的沒寄或不該寄的寄了。**假設**其中一邊錯,`OFD132A` 類別碼定義不在版控 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:82` · `DB/SP/S_OTA_OFDR042_GET.SQL:575` · `DB/SP/S_OTA_OFDR133_GET.SQL:82` | 中 |
| E13 | **全形空白 U+3000 進 SQL** | `S_OTA_OFDR094_GET` 第 115 行 `INNER JOIN FSK003` 前有 ` ` | PL/SQL 編譯應報非法字元;該 SP 明顯在跑,**假設**版控檔與 DB 版本不同步或為 cp950 解碼誤判。待驗 | `DB/SP/S_OTA_OFDR094_GET.sql:115` | 中(若版控檔與 DB 不同步,整個「SP 在版控」的價值打折) |
| E14 | **檔名與內容不符** | `DB/SP/S_OTA_OFDR601_GET.SQL` 內容是 `S_OTA_OFDR051_GET` | 跑這個檔會覆寫 `051` 的 SP;搜 `601` 會找到錯的東西 | `DB/SP/S_OTA_OFDR601_GET.SQL:1` | 中 |
| E15 | **檔案存在但不在 csproj** | `OFDR042RPS1.cs`~`RPS4.cs` 在磁碟,csproj 掛的是 `RPS11`~`RPS41`,類別名相同 | 兩套都掛會重複定義;現在是 4 個廢檔 | `Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/Report.OTA.csproj:221-239` · `Dev/ATLAS.OTA.Report/Source/CrystalReports/Report.OTA/OFDR042RPS11.cs:19` | 低 |
| E16 | **字串串接進 SQL** | `OFDR085` `OFDR086` 把 grid 勾選的基金清單串成 `IN ('a', 'b')` | 值來自 grid 不吃鍵盤,注入面小;基金代碼含 `'` 就炸 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR085.cs:238` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR085_PO.cs:137` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR086_PO.cs:132` | 低 |
| E17 | 死碼 | EC 5 支 PO 的 `DoDeleteTempTable`(含字串串接 `DELETE`)與 `xUSERDOMAIN = Guid.NewGuid()` 無人呼叫;OTA 20 支 UI 宣告 `ClientOTABizUtility m_OTABiz` 多數沒用;`OFDR042` `OFDR601A` 的 `UserId` 欄位賦值後沒人讀 | 誤導閱讀;`UserId` / `UserID` 大小寫並存尤其容易改錯 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:39` · `:141-172` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR042.cs:72` · `:188` | 低 |
| E18 | **xsd 借用** | `OFDR002` 用 `OFDR001BModel`、`OFDR058` 用 `OFDR057Model`、`OFDR132` `OFDR134` 用 `OFDR131Model` | 改一支的欄位打到兩三支;`OFDR002` 的結果集只填 `OFDR001B_1` 27 欄的子集 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR002_PO.cs:59` · `Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/OFDR058_Ctl.cs:37` | 低 |
| E19 | 檔名含空白 | `OFDR901AView .xsd`(`View` 後有一個空白),csproj 也照這個名字掛 | 能編;但任何用 `<代號>View.xsd` 規則找檔的工具會漏 | `Dev/ATLAS.OTA.Report/Source/Entity/ReportUIEntity.OTA/ReportUIEntity.OTA.csproj:366` | 低 |
| E20 | 死 xsd | EC 7 支活的各有 `<代號>Model.xsd`(MSSQL 版)在 csproj,活的是 `_9iModel` | 兩套 schema 並存,改錯一套不會編譯錯 | `Dev/ATLAS.EC.Report/Source/Entity/ReportDataEntity.EC/ReportDataEntity.EC.csproj:263` · `:331` | 低 |
| E21 | 成對 handler | `OFDR602`(EC)預覽與列印各一份幾乎相同的 handler | 改一邊忘一邊 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR602.cs:140-173` · `:175-215` | 低 |
| E22 | 中文名錯字 | `OFDR606` 第二版型「路受益人…」少「網」;`OFDR904` `Rport` `RP31` | 抬頭 / 檔名錯字 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/OFDR606.cs:63` · `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OFDR904.cs:148` · `:296` | 低 |
| E23 | **可攜性**(記錄) | `OFDR002` `OFDR901A` `OFDR904` 的 SP 在 `OPEN` 游標**之後** `DELETE` 暫存 | Oracle 讀一致性讓 fetch 仍讀得到;搬到 SQL Server 會回空表 | `DB/SP/S_OTA_OFDR002_GET.SQL:103-123` · `DB/SP/S_OTA_OFDR901A_GET.SQL:265` · `DB/SP/S_OTA_OFDR904_GET.sql:622` | 記錄 |
| E24 | 設計,非缺陷(記錄) | `OFDR050` 製作資料用 `USERDOMAIN` 隔離過程,但 `_GET` 讀回時只用日期 / 戶號篩——結果跨使用者共用 | 全公司當日一份,B 重製會蓋 A 的;有詢問對話框 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR050_PO.cs:270-271` | 記錄 |
| E25 | 必輸未提示 | `OFDR088` SP `OFD251.FH_CD = xFH_CD` 不加 `NVL`,基金公司不選就零筆;UI 沒擋 | 零筆無提示(疊 E8) | `DB/SP/S_OTA_OFDR088_GET.sql:75` | 低 |

### E.30 交辦缺陷型錄的逐項核對

| 型錄 | 本片有沒有 | 條目 |
|---|---|---|
| `Basic_PO.m_db` 恆 null → NRE | **無**(0 / 43 活的;EC 註解內的 MSSQL 版有初始化) | — |
| `INNER JOIN` 讓對不到的資料無聲消失 | **有**,34 個 SP | E6 |
| 字串串接進 SQL | 有,2 支,值來自 grid | E16 |
| Oracle 三值邏輯 | **有**,164 處 | E5 |
| `AND` / `OR` 缺括號 | 未見(SP 內 `OR` 都有括號,例 `DB/SP/S_OTA_OFDR051_GET.SQL:179-181`) | — |
| 全形空白進 SQL | 有,1 處,待驗 | E13 |
| bind 變數漏冒號 | 無(自組 SQL 全 `:X` 綁定) | — |
| `LIKE` 樣式餵給 `=` | 反向:`=` 語意餵給 `LIKE` | E11 |
| `catch` fail-open | 有(SP 層) | E10 |
| `i = 1;` 蓋掉 `ExecuteNonQuery` | 無 | — |
| 對已 Commit 的交易 `Rollback()` | 無;是對 null `tran` `Rollback()` | E9 |
| `catch (SqlException)` 在 Oracle 上是死碼 | 無 | — |
| 成對報表只改一邊 | 有(`0100` / `0130`;`085` / `086`;`602` 雙 handler) | E12 E21 |
| 寫死常數 | 有(部門碼、狀態碼、`GAGENT_CD`) | E12、§7.11.2 |
| 位置取參數 | 無(`GetParamValue` 具名) | — |
| 非 UTF-8 來源檔 | `.cs` 全 UTF-8 BOM;**`DB/SP/` 38 個全 cp950** | 記錄(§2.2.1) |
| 檔案存在但不在 csproj | **有**,EC 7 支三層 + OTA 4 個 `.cs` | E7 E15 |
| `.rpt` 不在版控 | **有**,2 支懸空 | E4 |
| 報表欄位與 xsd 不同步 | 無法檢出(不 Read `.rpt`) | — |
| 零「查無資料」提示 | **有**,34 支 | E8 |

### E.31 最需要人工複驗的一條

**E1。** 關鍵在 `Database.BeginTransaction()` + `LoadDataSet(cmd, ds, tran, ...)`(框架,無原始碼)是否真的讓 SP 內所有 DML 跑在同一個 Oracle 交易內、到 C# `Commit()` 才 commit。**是** → 兩個使用者印 `OFDR042` 會序列化(後者卡住等前者),沒有資料錯誤但有等待;**否**(SP 內有 autonomous transaction 或框架 auto-commit)→ 互蓋,越權印出別人客戶的對帳單。 **驗證成本低**:兩個非 `M2` `C2` `G16` `G17` 部門的測試帳號同時按 `OFDR042` 預覽,看後者是等待還是印出前者的受益人。E2 E3 同一個前提,一次驗完。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-16 | 初版。報表第 2 片,收齊 OTA / EC 兩軌 50 支,`OFD` 軌 M / I / B / R 四型至此全部有文件。新增兩個前片沒有的章節型式:§2.2 逐 SP 列實體表(因 SP 在版控)、§2.4 暫存表兩種設計、§7.11.2 SP 層過濾樣板。 |

由 build_doc.py v2.0.0 於 2026-09-16 14:56 產生 · 標題 88 · 圖 6 · 表格 50 · 程式錨點 231 · § 連結 138 · 引用檢查：畫面 63（缺 0） · Table 38（缺 0） · SP 42（缺 0） · Function 2（缺 0） · View 2（缺 0） · Report 59（缺 0） · 結果集 17（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
