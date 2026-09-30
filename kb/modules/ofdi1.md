<!-- 由 tools/build_copilot_kb.py 從 modules/ofdi1.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
