<!-- 由 tools/build_copilot_kb.py 從 modules/ofdr2.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-16 -->

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
