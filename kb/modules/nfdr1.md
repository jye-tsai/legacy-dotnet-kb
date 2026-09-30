<!-- 由 tools/build_copilot_kb.py 從 modules/nfdr1.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS NFDR1 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:`Dev/ATLAS.NFD.Report` 專案 127 支報表中的**前 44 支**(`NFDR001`–`NFDR160`)。`NFDR167` 以後的 83 支在別篇。 **建議讀法**:趕時間只讀三段——§0.1(`NFD` 到底是什麼)、§2.1(它讀誰的表)、附錄 E(踩雷)。要動某支報表再翻 §7 對應小節。

> ⚠ **本模組的業務意義**(§0)由**報表中文名、Crystal 參數名、PO 讀到的表名**三路反推。`NFD` 三個字母的展開在 repo 裡找不到任何定義,**本文不造官方名稱**。 ⚠ **〔客戶特定〕**:機構代碼、基金代碼、`CTL014` / `CTL018` 代碼值、寄件主旨與檔名格式為本站台的值。 ⚠ **〔共用〕**:本模組**一張自有主檔都沒有**,讀到的表全部屬於別的模組(見 §2、§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 `NFD` 是什麼(推測)

**一句話:`NFD` 不是一條業務軌,是一個「純輸出層」——它是境內基金(`OFD` 軌)資料的報表與對外文件產生器,自己不維護任何資料。**

這是全庫**唯一只有 R、沒有任何 M / I / B 畫面的模組**。127 支全部是報表,`Dev/ATLAS.NFD.Report` 之外**沒有** `Dev/ATLAS.NFD` 這個主專案——其他模組都是「主專案 + `.Report` 子專案」成對出現(`ATLAS.CAS` / `ATLAS.CAS.Report`、`ATLAS.CLS` / `ATLAS.CLS.Report`…),`NFD` 只有 `.Report` 一半。

推測依據,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 報表中文名 | 「基金受益人名冊」「資金來源分析表」「股權分散表」「員工及其關係人買賣本公司基金月報表」「債券型基金其他資訊揭露月報表」「各基金餘額比例表」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:47`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR002.cs:36`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR003.cs:43`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR004.cs:34`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR006.cs:87`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR007.cs:71` |
| 報表中文名(對外文件) | 「投資對帳單」「貴 賓 理 財 對 帳 單」「申購交易確認書」「申購交易確認書(郵簡)」「買回轉申購交易確認書」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:247`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:252`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR077.cs:233` |
| 報表中文名(扣款與手續費) | 「指定扣款-申購扣款彙總表」「指定扣款-申購扣款明細表」「指定扣款-申購扣款失敗明細表」「各銷售機構各基金手續費明細表」「各銷售機構手續費通知函」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR102.cs:52`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR103.cs:39`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:125`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:129` |
| 讀到的表 | PO 內寫得出表名的地方,清一色是 `OFD*`:`OFD017A`、`OFD081A`、`OFD081V`、`OFD0811A`、`OFD123A`、`OFD132A`、`OFD221A`、`OFD251A`、`OFD303A`、`OFD306A`、`OFD126`、`OFD002` | 見 §2.1 的逐支對照 |
| 專案不成對 | `Dev/` 下有 `ATLAS.OFD` + `ATLAS.OFD.Report`,但只有 `ATLAS.NFD.Report`,沒有 `ATLAS.NFD` | `Dev/ATLAS.NFD.Report/Source/Vendor.ATLAS.NFD.Report.sln` |

**所以 `NFD` 的業務範圍 =「境內基金 TA 的對外文件與法遵/營運報表」**。本文一律用這個描述,不替 `N` 造字(「國內」「Non-offshore」「New」都查不到依據,**不寫**)。

### 0.2 `NFD` 跟 `OFD` 是什麼關係

已知的三條軌(前篇查證):`ATLAS.OFD*` = 境內分戶軌、`ATLAS.OTA*` = 境外綜合帳戶軌、`ATLAS.EC*` = 電子交易軌。

**`NFD` 不是第四條軌**,依據是它沒有自己的表。切分維度是**「報表歸屬」而不是「業務軌」**:

|  | `ATLAS.OFD.Report` | `ATLAS.NFD.Report` |
|---|---|---|
| 支數 | 40 支 | 127 支 |
| 讀的表 | `OFD*` 為主 | `OFD*` 為主(**同一批表**) |
| 有無配對主專案 | 有(`ATLAS.OFD`) | **無** |
| 內容性質(從報表名推測) | 貼著 `OFD` 畫面的作業型清單 | 對外文件(對帳單、確認書)+ 法遵月報 + 手續費/扣款結算 |

**假設**:兩套報表專案共用同一批 `OFD*` 表,差別在**誰是讀者**——`ATLAS.OFD.Report` 是給 `OFD` 畫面操作員看的作業清單,`ATLAS.NFD.Report` 是給受益人、銷售機構、主管機關看的對外文件。依據是報表名:`NFDR004`「員工及其關係人買賣本公司基金月報表」、`NFDR006`「債券型基金其他資訊揭露月報表」是主管機關格式;`NFDR073`「投資對帳單」、`NFDR076`「申購交易確認書」是寄給客戶的。**這是推論,repo 內沒有文字說明兩套的分工。**

另一條可查的線索:`NFD` 的 44 支裡有 11 支自己建暫存表(`NFDR073T0`~`NFDR073T34`、`NFDR104_T0`、`NFDR106_T1`、`NFDR188_T1`、`NFDR352T1`…,DDL 在 `DB/Table/`),也就是說它**會為了印報表而寫入資料庫**,但寫的都是以報表代號命名的 `*T*` 暫存表,不是業務主檔。這佐證「純輸出層」的定位:它可以落地中繼資料,但不擁有業務事實。

### 0.3 不管什麼

| 不管 | 誰管 | 依據 |
|---|---|---|
| 任何資料的新增 / 修改 / 刪除 | `ATLAS.OFD` 的 M 畫面 | 本專案 127 支全是 `xReportForm`,沒有 `xMaintainForm` / `xQueryForm` / `xBatchForm`;見 §4–§6 |
| 四眼覆核 | `ATLAS.OFD` | 本模組 Ctl 只有 `GetXxxReportData` / `GetXxxReportObject`,無 `Verify` / `Approve` / `Reject`,例:`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:39-76` |
| 排程批次 | `ATLAS.OFDB` / WindowsService | 本模組無 B 畫面 |
| 境外綜合帳戶資料 | `ATLAS.OTA*` | 本片 44 支未讀到任何 `OTA*` 表 |

### 0.4 使用角色

| 角色 | 用哪些 | 依據 |
|---|---|---|
| 主管機關申報窗口 | `NFDR003`(股權分散表)、`NFDR004`(員工及其關係人買賣月報)、`NFDR006`(債券型基金其他資訊揭露月報) | 報表中文名,錨點見 §0.1 |
| 客戶服務 / 寄發作業 | `NFDR073`(投資對帳單)、`NFDR073A`、`NFDR073B`(貴賓理財對帳單)、`NFDR076`(申購交易確認書)、`NFDR077`(買回轉申購確認書) | 報表中文名 + `NFDR073B` 有寄信 SP `S_TA_NFDR073B_EMAIL`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs`) |
| 通路 / 手續費結算 | `NFDR107A`、`NFDR107B`(各銷售機構各基金手續費明細/合計/通知函) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:109-129` |
| 扣款作業 | `NFDR101`–`NFDR105`(指定扣款彙總/明細/失敗明細) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58` |

### 0.5 全域開關與前提

| 開關 | 在哪 | 影響 |
|---|---|---|
| Oracle 連線 `Database("TA", DbServerType.Oracle)` | 每支 PO 建構子,例 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:25` | 全模組走 Oracle;PO 上的 `[PODbType(DbServerType.Oracle)]` 決定執行期選哪個 PO |
| `Cmd.CommandTimeout = 0` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56` | **永不逾時**。SP 卡住時 client 會無限等待,沒有取消機制 |
| `CRReportTransfer.TransferFileByte(rpt)` | 每支 Ctl 的 `GetXxxReportObject`,例 `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:45` | 報表範本以**檔名字串**在執行期取得,不是強型別參考。範本檔不在部署路徑就是執行期錯誤,編譯期查不出來(見 §2.3) |

### 0.6 這模組最反直覺的三件事

**一、它是一個「只有下半身」的模組。** 其他模組都是 `ATLAS.XXX`(主專案)+ `ATLAS.XXX.Report`(報表子專案)成對存在。`NFD` 只有 `.Report`。所以在 `Dev/` 下找 `ATLAS.NFD` 找不到不是漏掉,是本來就沒有。同理,任何「`NFD` 的表」「`NFD` 的維護畫面」「`NFD` 的批次」都不存在(§4、§5、§6)。

**二、它的資料層有 36% 目前是壞的,而且是靜悄悄壞的。** 44 支裡 16 支的 PO 繼承 `Basic_PO`,`m_db` 宣告成 `null` 且建構子裡唯一的指派被註解掉(附錄 E-02)。這 16 支在 Oracle 環境按下預覽會 `NullReferenceException`。其中包括 `NFDR073`(投資對帳單)與 `NFDR154`(贖回交易確認單)這種對外文件。**選單上看不出差別**——它們和能跑的 28 支長得一模一樣。

**三、要查「這張報表讀哪些表」,三分之二的情況查不到。** 44 支點名 60 個 stored procedure,版控裡只有 1 支(§2.2)。29 支的 PO 除了 `AddInParameter` 之外一行 SQL 都沒有(§2.1.2)。這代表**任何 `OFD*` 表的影響面分析,在 `NFD` 這裡一定是不完整的**,而且沒有辦法從 repo 補完。

這三件事合起來解釋了為什麼本文的結構和其他模組的文件不一樣:§4 / §5 / §6 是空的但要展開講「為什麼空」,§2 與 §8 特別厚,§7 的重點不是「這張報表怎麼算」(算法在版控外)而是「這張報表怎麼取數、會在哪裡少印」。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] NFD 報表第 1 片全景：五群 44 支報表、取數路徑、讀到的別模組的表、三條輸出出口，以及本模組不存在的四件事
圖中文字:① 五群報表（本片 44 支，全部是 R，沒有 M／I／B） / NFDR001–007 / 受益人結構+法遵月報 7 支 / NFDR021–024 / 排行+異常清冊 3 支 / NFDR071–077 / 對帳單／確認書 8 支 / NFDR101–123 / 申購側 16 支 / NFDR150–160 / 買回／贖回側 10 支 / ② 取數：29 支完全看不到表名（SQL 在版控外的 SP 裡） / 60 支 SP / 版控內只有 1 支 / PO inline SQL / 只有 15 支有 / NFDR073T0–T34 / NFD 自建暫存 17 張 / Basic_PO 16 支 / m_db 未初始化→NRE / INFDRxxx_PO 28 支 / 已遷 Oracle / ③ 真正的業務資料：全部是別人的表 / OFD 軌 14 張 / OFD081V OFD303A OFD0811A… / BMS001A / 受益人主檔 / COD009 SAL051 FSK003 / 員工／業務員／風險屬性 / CTL014 CTL018 / 代碼表（內容在 DB） / ④ 三條出口 / Crystal .rpt × 79 / 42 支；全在版控+csproj / Excel / NFDR123 / 120 / 121 / 文字檔 + ZIP 加密 / NFDR073A（無 .rpt） / Email 佇列 / NFDR073B 寫 SP / ⑤ 不存在的東西（這是 NFD 最大的特徵） / 無 M 畫面 / 不維護任何資料 / 無 I 畫面 / 不做查詢 / 無 B／Service / 沒有排程 / 無 ATLAS.NFD 主專案 / 只有 .Report 一半
```

*圖:圖 1 NFDR1 全景。橘框=本片深寫的重點；灰虛框=借用別模組的表或「不存在」的事實；黑框=無原始碼的黑箱（版控外 SP、代碼表內容）；橘虛框=行為含寫死值或已知風險〔客戶特定〕。實線=同一支報表內的呼叫；虛線=輸出方向。*

### 1.2 資料表關係

本片 44 支報表**沒有任何一張自有業務主檔**。PO 裡寫得出表名的只有 15 支,其餘 29 支的 SQL 全部埋在版控外的 SP 裡(§2.1)。圖見 §2 的扇入圖。

### 1.3 報表的六層呼叫順序

所有 44 支走同一條路,沒有例外:

| 步 | 在哪一層 | 做什麼 | 錨點範例 |
|---|---|---|---|
| 1 | UI `xReportForm` | `FormInitial` 設定 `ResultVDB` 與 `FormProxy` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:32-34` |
| 2 | UI | `BeforePreviewButtonClicked` 跑 `DoValidate()`,有錯就 `e.Cancel = true` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:75-80` |
| 3 | UI | 把畫面條件塞進 `Utility.Parameters`(Name / Operator / Value 三欄) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:151-163` |
| 4 | FormProxy | 轉呼叫遠端 Control | `Dev/ATLAS.NFD.Report/Source/FormProxy/ReportFormProxy.NFD/NFDR001_Pxy.cs` |
| 5 | Control | `GetXxxReportData` → `ExecPOActionToViewVDB` 打 PO;`GetXxxReportObject` → `CRReportTransfer.TransferFileByte(rpt)` 把 `.rpt` 範本傳回 client | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:45,59-62` |
| 6 | PO | `GetStoredProcCommand(...)` 或 `GetSqlStringCommand(strSQL)` 取數,填進 `ModelVDB` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57` |
| 7 | Control | `CustomTransferOracleModelToView` 把 `ModelVDB` 每張 DataTable 搬到 `ViewVDB` | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:92-96` |
| 8 | UI | `ReportLoad` 用 `m_ReportDocument.SetParameterValue(...)` 把「顯示用」參數餵給 Crystal | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:49-53` |

**第 7 步是本模組最常出錯的地方**:`CustomTransferOracleModelToView` 是逐張 DataTable 手抄。SP 多回一張表、或 `Model.xsd` 加了一張表而 Ctl 沒加對應的 `TransferTable`,結果是**該張表在報表上永遠空白,不會報錯**(見附錄 E-07)。

### 1.4 報表輸出的三條出口

| 出口 | 怎麼做 | 哪些支 |
|---|---|---|
| Crystal 預覽 / 列印 | `SetQueryParameters(ReportClass, ReportID, ReportName)` + `.rpt` 範本 | 42 支 |
| Excel 下載 | `ExcelCreator.CreateExcelDocument(dt, sFileName)` 直接存檔,**不經 Crystal** | `NFDR123`;`NFDR120` / `NFDR121` 為混合(有「下載」選項) |
| 文字檔 / ZIP | `CreateTxtFiles.CreateNFDR073AText(...)`,可加密碼壓縮 | `NFDR073A` |

### 1.5 一日作業泳道(推測)

repo 內沒有排程設定可讀,以下由報表名的期間參數推測,**標「假設」**:

| 時點 | 誰跑 | 跑什麼 |
|---|---|---|
| 日終 | 扣款作業 | `NFDR101` / `NFDR102` / `NFDR103`(指定扣款彙總 / 明細 / 失敗明細) |
| 日終 | 交易作業 | `NFDR105`(申購交易確認單)、`NFDR154`(贖回交易確認單)、`NFDR104`(申購明細表) |
| 月底 | 客服 | `NFDR073` / `NFDR073A` / `NFDR073B`(對帳單,`NFDR073A` 有「月對帳單 / 季對帳單」選項,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.Designer.cs:148-150`) |
| 月底 | 財務 | `NFDR107A` / `NFDR107B`(扣帳費 / 手續費)、`NFDR115` / `NFDR158` / `NFDR159`(申購 / 贖回 / 轉申購統計月報) |
| 月底 | 法遵 | `NFDR004`(員工及其關係人買賣月報)、`NFDR006`(債券型基金其他資訊揭露月報) |

### 1.6 要改這個模組的報表之前

操作步驟走 `add-report.md`(七層結構、Crystal 版本、`.rpt` 加進 csproj 的方式、部署路徑),**本文不重複**。以下只列 `NFD` 與該手冊的範例(`CASR001`,`Dev/ATLAS.CAS.Report`)不一樣的地方:

| 項目 | `add-report.md` 的 `CASR001` | `NFD` 本片 44 支 |
|---|---|---|
| 七層結構 | 相同(六層加 `Report` 前綴 + `CrystalReports/Report.XXX`) | **相同**,44 支全齊,無檔名例外 |
| 一支畫面掛多版型 | `CASR001` 掛 6 個 | `NFDR001` / `NFDR076` 掛 5 個,`NFDR073B` / `NFDR151` / `NFDR160` 掛 4 個;**但版型與選項是多對一**(§7.1.1),改一張會影響多個組合 |
| R 畫面沒有四眼 | 是 | **是**,44 支的 PO 都不宣告 `MasterTable` / `DetailTable`(§4) |
| 資料走 SP | 是 | **是,而且 SP 幾乎全在版控外**(§2.2)。改欄位時 repo 內改不到取數那一半 |
| 選版型在客戶端 | 是 | **是**,`SetQueryParameters(ReportClass, ReportID, ReportName)`;`NFDR151` 例外——**分派寫在 PO**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:70-98`),加版型要同時改 UI 與 PO |
| PO 基底 | 單一 | **兩種並存**:28 支 `INFDRxxx_PO`(Oracle)、16 支 `Basic_PO`(未遷移,附錄 E-02)。動到後者要先處理 `m_db` |
| 輸出一定是 `.rpt` | 是 | **兩支不是**:`NFDR073A`(文字檔)、`NFDR123`(Excel) |

**加一張新版型的最小改動清單(本模組版)**:

1. 新增 `.rpt` 到 `Dev/ATLAS.NFD.Report/Source/CrystalReports/Report.NFD/`,並加進 `Report.NFD.csproj`(本片 79 張全都有加,照抄既有寫法)。

2. UI 加一個 `SetQueryParameters("NFDRxxxRPSn", "NFDRxxxRPSn", "報表中文名")` 分支——**記得補 `else`**,否則落在列舉外就靜默什麼都不做(附錄 E-15)。

3. 若新版型需要新的結果集:`Model.xsd` + `View.xsd` + Ctl 的 `TransferTable` **三處一起改**(附錄 E-07)。

4. 若取數要改,**SP 不在版控**,要另外走資料庫變更流程,repo 內留不下痕跡。

## 2. 資料模型

```text
[圖] NFD 讀誰的表：15 支可見報表扇入到 OFD 軌 14 張表與 4 張共用主檔，NFD 自己的業務表是零張
圖中文字:本片 15 支「看得見表名」的報表 → 各模組的表（另 29 支在 SP 黑箱裡） / NFDR073A / 對帳單文字檔 讀 6 個模組 / NFDR076 NFDR077 / 申購／買回轉申購確認書 / NFDR123 / KYC 到期名單 / NFDR107A NFDR107B NFDR114 / 手續費／扣帳費／印花稅 / NFDR115/154/158/159 / 統計月報＋確認單 / NFDR001/073/073B/101 / 名冊／對帳單／扣款 / OFD081V / 4 支 · view，定義不在版控 / OFD303A / 5 支 · 日結檢核的來源 / OFD0811A OFD081A / 基金屬性 INV_AREA／PROF_TYPE2 / OFD221A OFD251A OFD306A / 申購／買回／異動 / OFD002 017A 123A 126 132A / 其餘 OFD 表各 1 支 / BMS001A / 4 支 · 受益人主檔 / COD009 SAL051 FSK003 / 員工／業務員／風險屬性 / CTL014 CTL018 / 代碼表 / OFD 軌 14 張 / 境內分戶軌 = 真正的業務資料 / BMS／COD／SAL／FSK 4 張 / 共用主檔 / CTL 2 張 / 代碼 / NFDR073T* 17 張 / NFD 唯一自有：暫存 / NFD 自己的業務表：0 張 / 這就是「純輸出層」的定義
```

*圖:圖 2 扇入圖（§2.1）。左=本片看得見表名的 15 支；中=被讀到的表；右=按模組彙總。灰虛框=別模組的表（NFD 只讀不寫）；黑框=無原始碼／內容在 DB；橘虛框=NFD 唯一自有的暫存表。另有 29 支的相依性藏在版控外的 SP 裡，這張圖畫不出來。*

### 2.1 `NFD` 讀誰的表(本文最重要的一節)

**結論:44 支裡有 29 支(66%)完全看不到表名**——SQL 在版控外的 SP 裡。剩下 15 支可以從 PO 的 inline SQL 讀出表,清一色是 `OFD*` 加少數共用代碼表。

`NFD` 沒有任何一張自己的業務表。它唯一「自己的」是以報表代號命名的暫存表(`NFDR073T*`),而且只有 `NFDR073` / `NFDR073A` 在用。

#### 2.1.1 表的歸屬統計(僅計 PO 內看得見的)

| 表 | 歸屬模組 | 被本片幾支用 | 哪幾支 | 在 `atlas_index.json` |
|---|---|---|---|---|
| `OFD081V` | OFD | 5 | `NFDR073A` `NFDR115` `NFDR154` `NFDR158` `NFDR159` | 否(view,索引未收) |
| `OFD303A` | OFD | 5 | `NFDR076` `NFDR077` `NFDR107A` `NFDR107B` `NFDR114` | 否 |
| `BMS001A` | BMS | 4 | `NFDR073A` `NFDR076` `NFDR077` `NFDR123` | 是 |
| `CTL018` | CTL(代碼) | 3 | `NFDR073` `NFDR101` `NFDR107B` | 否 |
| `OFD0811A` | OFD | 3 | `NFDR073A` `NFDR076` `NFDR077` | 是 |
| `COD009` | COD | 2 | `NFDR073B` `NFDR123` | 是 |
| `OFD081A` | OFD | 2 | `NFDR073A` `NFDR077` | 是 |
| `OFD221A` | OFD | 2 | `NFDR076` `NFDR123` | 是 |
| `CTL014` | CTL(代碼) | 1 | `NFDR001` | 否 |
| `FSK003` | FSK | 1 | `NFDR073A` | 否 |
| `OFD002` | OFD | 1 | `NFDR073B` | 是 |
| `OFD017A` | OFD | 1 | `NFDR001` | 是 |
| `OFD123A` + `OFD123A_TMP` | OFD | 1 | `NFDR123` | `OFD123A` 是 |
| `OFD126` | OFD | 1 | `NFDR073` | 否 |
| `OFD132A` | OFD | 1 | `NFDR073A` | 是 |
| `OFD251A` | OFD | 1 | `NFDR077` | 是 |
| `OFD306A` + `OFD306_TMP` | OFD | 1 | `NFDR123` | 否 |
| `SAL051` | SAL | 1 | `NFDR073B` | 是 |
| `MYOFD303A` | ?(同義字 / 別名) | 1 | `NFDR077` | 否 |
| `NFDR073T0` `T5`–`T12` `T16`–`T19` `T24` `T29` `T31` `T33` `T34` | **NFD 自建暫存** | 2 | `NFDR073` `NFDR073A` | 否(DDL 在 `DB/Table/`) |
| `OCRMTMP` | ?(暫存) | 1 | `NFDR073` | 否 |

按模組彙總(去重後 42 張表):

| 模組 | 張數 | 佔比 | 說明 |
|---|---|---|---|
| **NFD 自建暫存** `NFDR073T*` | 17 | 40% | 只為了印 `NFDR073` / `NFDR073A` 而存在 |
| **OFD**(境內分戶軌) | 14 | 33% | **真正的業務資料全在這** |
| CTL(代碼) | 2 | 5% | `CTL014` `CTL018` |
| BMS / COD / FSK / SAL | 4 | 10% | 受益人基本資料、代碼、風險屬性、業務員 |
| 不明(`MYOFD303A` / `OCRMTMP` / `F_FORMATSTRINGTOTABLE`) | 3 | 7% | 同義字、暫存表、Oracle function |
| `OFD*_TMP` | 3 | 7% | `OFD123A_TMP` `OFD221A_TMP` `OFD306_TMP` |

**這張表就是 §0.1 結論的證據**:去掉自己造的暫存表,`NFD` 看得見的業務表 100% 是 `OFD` 軌的。

#### 2.1.2 29 支黑箱

以下 29 支的 PO **完全沒有 inline SQL**,只有 `GetStoredProcCommand` + `AddInParameter`,所以讀哪些表**從 repo 讀不出來**:

`NFDR002` `NFDR003` `NFDR004` `NFDR005` `NFDR006` `NFDR007` `NFDR021` `NFDR023` `NFDR024` `NFDR071` `NFDR072` `NFDR075` `NFDR102` `NFDR103` `NFDR104` `NFDR105` `NFDR108` `NFDR109` `NFDR111` `NFDR120` `NFDR121` `NFDR122` `NFDR150` `NFDR151` `NFDR153` `NFDR155` `NFDR156` `NFDR157` `NFDR160`

要查它們讀誰的表,只能到資料庫撈 SP 原始碼。**這是本模組最大的維護風險**(附錄 E-01)。

### 2.2 SP:60 支,版控裡只有 1 支

44 支報表一共點名 60 個 stored procedure。拿 `atlas_index.json` 的 `sps`(83 支)去比對,**只有 `S_TA_NFDR073_1_GET` 一支在版控**(`DB/SP/S_TA_NFDR073_1_GET.SQL`)。

| 命名樣式 | 支數 | 例 |
|---|---|---|
| `s_TA_NFDRxxx_Get` / `S_TA_NFDRxxx_GET` | 30 | `s_TA_NFDR001_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57`) |
| `s_NFDRxxx_Get`(**少了 `TA_`**) | 22 | `s_NFDR023_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR023_PO.cs:64`) |
| 帶序號 `_1_` / `_2_` / `_T2_` | 8 | `S_TA_NFDR151_GET_1`–`_5`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:81-116`) |

**兩套命名並存**且沒有規則可循:同一支 `NFDR073` 用 `s_NFDR073_Get`,而 `NFDR073A` 用 `S_TA_NFDR073_0_GET`~`_4_GET`。要找某支報表的 SP,**不能用代號硬推名字**,必須開 PO 看(見 §7 逐支)。

大小寫也混:`NFDR024` 寫 `S_TA_NFDR024_GET`,`NFDR001` 寫 `s_TA_NFDR001_Get`。Oracle 不分大小寫所以跑得動,但任何依檔名 / 字串比對的工具都會漏。

### 2.3 `.rpt` 範本:全部在版控,而且全部在 csproj

好消息,這片沒有前幾篇踩過的洞:

| 檢查 | 結果 |
|---|---|
| 44 支引用的 Crystal ReportClass 字串 | 共 79 個 |
| 對應的 `.rpt` 檔在 `Dev/ATLAS.NFD.Report/Source/CrystalReports/Report.NFD/` | **79 / 79 都在** |
| 這些 `.rpt` 有沒有進 `Report.NFD.csproj` | **79 / 79 都在** |
| UI / Ctl / PO 三層 `.cs` 有沒有進各自 csproj | **44 / 44 × 3 都在** |
| 六層(UI / Ctl / Pxy / PO / Model.xsd / View.xsd)齊不齊 | **44 支全齊**,沒有 `misc.md` 那種檔名少一個字母的情況 |

例外兩支,是設計如此不是缺陷:

| 支 | 為什麼沒有 `.rpt` | 錨點 |
|---|---|---|
| `NFDR073A` | 產文字檔不產 Crystal 報表,走 `CreateTxtFiles.CreateNFDR073AText(...)` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:114` |
| `NFDR123` | 產 Excel 不產 Crystal,`ExcelCreator.CreateExcelDocument(dt, sFileName)`,檔名寫死「受益人KYC到期名單.xlsx」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79,86` |

`.rpt` 的取得方式仍然是**字串比對**:Ctl 拿前端傳來的 `ReportClass` 字串丟給 `CRReportTransfer.TransferFileByte(rpt)`(`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:44-45`)。編譯器不檢查,改 `.rpt` 檔名不改 UI 字串 = 執行期才爆。

### 2.4 `NFDR073T*` 暫存表家族

`NFDR073` / `NFDR073A` 這組對帳單自己建了 17 張以上的暫存表,DDL 在 `DB/Table/`(`NFDR073T16.sql`、`NFDR073T17.sql`、`NFDR073T18.sql`、`NFDR073BT1.sql`、`NFDR073BT2.sql`…)。

用法是**先 `DELETE` 再由 SP 重灌,以 `dataID` 分租**:

```
DELETE FROM NFDR073T6 WHERE dataID = @dataID; DELETE FROM NFDR073T7 WHERE dataID = @dataID
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385`

`dataID` 由 client 端組出來後截斷到 22 碼(`strDATAID.Substring(0, 22).Trim()`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102`)。**兩個使用者同時跑、`dataID` 前 22 碼撞到,兩份對帳單的資料會混在一起**(附錄 E-03)。

### 2.5 沒有狀態碼

本模組不改任何資料的狀態,所以沒有狀態機。畫面上的「選項」值(`uoptRPT_TYPE` / `uoptPrint` / `uoptOrder` / `uoptPurpose`)只影響**選哪支 SP、選哪張 `.rpt`、給 Crystal 什麼顯示字串**,不寫回資料庫。唯一的例外是 `NFDR073` / `NFDR073A` 寫暫存表(§2.4)與 `NFDR073B` 寄信留紀錄(`S_TA_NFDR073B_EMAIL`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160`)。

### 2.6 欄位中文名:`msdata:Caption` 在這個模組不可信

範本規定「欄位中文名以 `Model.xsd` 的 `msdata:Caption` 為準,不自己翻」。**這條規則在 `NFD` 只有一半適用**。

44 個 `Model.xsd` 裡 27 個有 `msdata:Caption`,17 個一個都沒有。而且有 `Caption` 的那 27 個裡,**有 9 個的 `Caption` 值根本不是中文名,是另一個欄位名**:

| 支 | 欄位 | `Caption` 值 | 這是什麼 |
|---|---|---|---|
| `NFDR002` | `PROF_TYPE` | `PROF_TYPE_NM_C` | 另一個欄位名 |
| `NFDR071` / `NFDR072` | `ANNOUNCE_AMT` | `TRAN_AMT1` | 另一個欄位名 |
| `NFDR073` | `NAV_DEC` | `DEC_LEN` | 另一個欄位名 |
| `NFDR073A` / `NFDR073B` | `FUND_SH_NM` | `FUND_SH_NM1` | 另一個欄位名 |
| `NFDR073A` / `NFDR073B` | `REDEM_COST` | `STK_COST` | 另一個欄位名 |
| `NFDR104` | `REMIT_ACC_TYPE` | `SYSTEM_ID` | 另一個欄位名 |
| `NFDR108` | `AGENT_ID_NM` | `AGENT_ID` | 另一個欄位名 |
| `NFDR151` | `SUM_PAID_AMT` | `SUM_RUNIT` | 另一個欄位名 |

錨點:`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR002Model.xsd`、`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR073AModel.xsd`、`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR151Model.xsd`。

**推測**:`Caption` 在這裡被當成「SP 實際回傳的欄位名」在用——DataSet 的欄位叫 `ANNOUNCE_AMT`,SP 回的欄位叫 `TRAN_AMT1`,用 `Caption` 記下對照。**這是 `Caption` 的誤用**,但改掉會影響 `TransferVDBHelper.TransferTable` 的行為,不能隨手動。

**所以在 `NFD` 查欄位中文名,要先看 `Caption` 值是不是中文**;不是中文就當成欄位對照,真正的中文名去 `.rpt` 或 `Designer.cs` 的 label 找。

### 2.7 欄位中文名總表(取自 `Model.xsd` 的 `msdata:Caption`,僅列中文者)

只有 5 支的 xsd 提供了成規模的中文欄位名。

| 支 | 欄位 → 中文名 |
|---|---|
| `NFDR109` | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `CRNCY_CD` 幣別 · `CRNCY_NM` 幣別名稱 · `AGENT_ID` 銷售機構別 · `AGENT_CODE` 銷售機構代碼 · `AGENT_SHNM` 銷售機構名稱 · `AGENT_SHNM_F` 完整銷售機構名稱(共 21 個) |
| `NFDR120` | `BANK_HQ` 總行代碼 · `BANK_HQ_SHNM` 總行名稱 · `BANK_HQ_SHNM_F` 總行完整名稱 · `BANK_BRH` 分行代碼 · `BANK_BRH_SHNM` 分行名稱 · `BANK_BRH_SHNM_F` 分行完整名稱 · `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱(共 29 個) |
| `NFDR121` | `AGENT_ID` 銷售機構別 · `AGENT_CODE` 部門代碼 · `AGENT_SHNM` 部門名稱 · `SPONSOR_CODE` 推薦人代碼 · `SPONSOR_NAME` 推薦人姓名 · `BF_NO` 受益人戶號 · `ID_NO` 統一編號 · `BF_NAME` 受益人戶名(共 38 個) |
| `NFDR122` | `AGENT_CODE` 部門代碼 · `AGENT_SHNM` 部門名稱 · `SPONSOR_CODE` 推薦人代碼 · `SPONSOR_NAME` 推薦人姓名 · `BF_NO` 受益人戶號 · `ID_NO` 受益人編號 · `BF_NAME` 受益人戶名 · `FUND_ID` 基金代碼(共 23 個) |
| `NFDR123` | `AGENT_ID` 銷售機構區別碼 · `AGENT_CODE` 銷售機構代碼 · `AGENT_NM` 銷售機構名稱 · `SPONSOR_CODE` 推薦人代碼 · `EMP_NO` 員工代碼 · `EMP_NAME` 員工姓名 · `BF_NAME` 客戶姓名 · `BF_NO` 戶號(共 12 個) |
| `NFDR150` | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `CRNCY_CD` 幣別 · `CRNCY_NM` 幣別名稱 · `REDEM_DATE` 買回日期 · `AGENT_ID` 銷售機構別 · `AGENT_CODE` 銷售機構代碼 · `AGENT_SHNM` 銷售機構名稱(共 19 個) |

**注意同一個欄位在不同支的中文名不一致**:`AGENT_CODE` 在 `NFDR109` / `NFDR150` 是「銷售機構代碼」,在 `NFDR121` / `NFDR122` 是「部門代碼」;`ID_NO` 在 `NFDR121` 是「統一編號」,在 `NFDR122` 是「受益人編號」,在 `NFDR023` 是「受益人ID」。**同一個欄位,三份報表三個中文名**——這不是 bug,但客服拿兩張報表對帳時會以為是不同欄位。

其餘 17 支完全沒有 `Caption`,欄位中文名只能從 `.rpt` 的欄位標題看,而 `.rpt` 是 Crystal 二進位,**repo 內讀不出來**。

### 2.8 `Model.xsd` 與 `View.xsd` 的關係

每支有兩個 xsd:

| 檔 | 角色 | 誰填 |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR001Model.xsd` | `ModelVDB`——伺服器端,PO 直接 `LoadDataSet` 進去 | PO |
| `Dev/ATLAS.NFD.Report/Source/Entity/ReportUIEntity.NFD/NFDR001View.xsd` | `ViewVDB`——傳回 client,Crystal 綁這一份 | Ctl 的 `CustomTransferOracleModelToView` 逐張手抄 |

**兩份要長得一樣,但沒有任何東西強制**。中間的 `TransferTable` 是一行一行寫的(§1.3 第 7 步、附錄 E-07)。加一張結果集要改四個地方:`Model.xsd`、`View.xsd`、Ctl 的 `TransferTable`、`.rpt` 的資料來源。少改一個不會編譯失敗,只會在報表上少一塊。

## 3. 報表清冊(44 支)

```text
[圖] 44 支報表依 PO 基底、資料來源、輸出型態、有無查無資料提示四種切法的分群
圖中文字:① 依 PO 基底：28 支已遷 Oracle vs 16 支停在 MSSQL / INFDRxxx_PO（28 支） / [PODbType(Oracle)] + 介面 + DataAccessPool / Basic_PO（16 支） / m_db = null，建構子被註解掉 → 一呼叫就 NRE / Ctl 直接 new PO / 沒有替換機會 / ② 依資料來源：SP 黑箱是主流 / 純 SP（29 支） / 讀哪些表查不出來 / SP + inline（14 支） / 部分可見 / 純 inline（1 支） / NFDR123 的 Oracle CTE / 無 SP 無 inline / （本片沒有） / ③ 依輸出：Crystal 為主，兩支例外 / Crystal 42 支 / 79 張 .rpt / 全在版控+csproj（本片零缺） / NFDR123 → Excel / 檔名寫死 / NFDR073A → 文字檔+ZIP / 密碼來自 config / ④ 依有沒有「查無資料」提示 / 有訊息 14 支 / 零筆會跳警示 / 完全沒有 30 支 / 印出只有表頭的空報表 / 有判斷但訊息是空字串 / NFDR151 / NFDR159 / NFDR105
```

*圖:圖 3 四種分群（§3）。橘框=需要留意的少數派；橘虛框=已知風險；黑框=無原始碼或查不到；灰虛框=空集合。第 ① 列是本模組最重要的一條：同一份選單上，有 16 支的資料層目前是壞的。*

欄位說明:**PO 基底**——`INFDRxxx_PO` 表示走介面 + `[PODbType(DbServerType.Oracle)]`,已完成 Oracle 遷移;`Basic_PO` 表示未遷移的舊版(見附錄 E-02,這 16 支的 `m_db` 永遠是 `null`)。**資料來源**——`SP` / `SP+inline` / `純 inline` / `無 DB`。**`.rpt`**——引用的 Crystal 範本數 / 在版控 / 在 csproj。

### 3.1 第 001–007 群:受益人結構與法遵月報(7 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR001` | 基金受益人名冊 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:47` | `INFDR001_PO` | SP+inline | `s_TA_NFDR001_Get` | `CTL014`、`OFD017A` | 5(全在版控+csproj) |
| `NFDR002` | 資金來源分析表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR002.cs:36` | `INFDR002_PO` | SP | `s_TA_NFDR002_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR003` | 股權分散表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR003.cs:43` | `INFDR003_PO` | SP | `s_TA_NFDR003_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR004` | 員工及其關係人買賣本公司基金月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR004.cs:34` | `INFDR004_PO` | SP | `s_TA_NFDR004_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR005` | 基金受益憑證持有者統計表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR005.cs:79` | `INFDR005_PO` | SP | `s_TA_NFDR005_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR006` | 債券型基金其他資訊揭露月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR006.cs:60` | `INFDR006_PO` | SP | `s_TA_NFDR006_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR007` | 各基金餘額比例表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR007.cs:55` | `INFDR007_PO` | SP | `s_TA_NFDR007_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |

### 3.2 第 021–024 群:受益人排行與異常清冊(3 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR021` | 受益人基金持有／申購／贖回單位數排行表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58` | `INFDR021_PO` | SP | `s_TA_NFDR021_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR023` | 受益人異動及定額異動重覆報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR023.cs:73` | `Basic_PO` | SP | `s_NFDR023_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR024` | 受益人統編異常清冊 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR024.cs:60` | `INFDR024_PO` | SP | `S_TA_NFDR024_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |

### 3.3 第 071–077 群:對帳單、確認書與公告(對外文件)(8 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR071` | 法人公告警示表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR071.cs:34` | `Basic_PO` | SP | `s_NFDR071_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR072` | 法人買回／贖回公告明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR072.cs:35-55` | `Basic_PO` | SP | `s_NFDR072_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR073` | 投資對帳單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49` | `Basic_PO` | SP+inline | `s_NFDR073_1_Get`、`s_NFDR073_Get`、`s_NFDR073_ChkRdm` | `CTL018`、`NFDR073T0`、`NFDR073T6`、`NFDR073T7`、`OCRMTMP`、`OFD126` | 1(全在版控+csproj) |
| `NFDR073A` | 月／季對帳單文字檔產生 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.Designer.cs:148-150` | `INFDR073A_PO` | SP+inline | `S_TA_NFDR073_3_GET`、`S_TA_NFDR073_0_GET`、`S_TA_NFDR073_4_GET`、`S_TA_NFDR073_1_GET`**(在版控)**、`S_TA_NFDR073_2_GET` | `BMS001A`、`FSK003`、`NFDR073T10`、`NFDR073T11`、`NFDR073T12`、`NFDR073T16` …共 23 張 | **0**(非 Crystal) |
| `NFDR073B` | 貴賓理財對帳單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123` | `INFDR073B_PO` | SP+inline | `S_TA_NFDR073B_GET`、`S_TA_NFDR073B_EMAIL` | `COD009`、`OFD002`、`SAL051` | 4(全在版控+csproj) |
| `NFDR075` | 傳真委託申購／委扣－扣款失敗通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR075.cs:44-58` | `INFDR075_PO` | SP | `s_TA_NFDR075_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR076` | 申購交易確認書（含郵簡、彙總） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:179` | `INFDR076_PO` | SP+inline | `S_TA_NFDR076_GET` | `BMS001A`、`OFD0811A`、`OFD221A`、`OFD303A` | 5(全在版控+csproj) |
| `NFDR077` | 買回轉申購交易確認書（含郵簡、彙總） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR077.cs:183` | `INFDR077_PO` | SP+inline | `S_TA_NFDR077_GET` | `BMS001A`、`MYOFD303A`、`OFD0811A`、`OFD081A`、`OFD251A`、`OFD303A` | 3(全在版控+csproj) |

### 3.4 第 101–123 群:申購側:扣款、手續費、稅、統計(16 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR101` | 指定扣款／傳真委扣－申購扣款彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58` | `INFDR101_PO` | SP+inline | `S_TA_NFDR101_GET` | `CTL018` | 1(全在版控+csproj) |
| `NFDR102` | 指定扣款／傳真委扣－申購扣款明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR102.cs:52` | `INFDR102_PO` | SP | `S_TA_NFDR102_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR103` | 指定扣款／傳真委扣－申購扣款失敗明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR103.cs:39` | `Basic_PO` | SP | `s_NFDR103_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR104` | 申購明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR104.cs:286` | `INFDR104_PO` | SP | `s_TA_NFDR104_Get` | **看不到(SP 黑箱)** | 3(全在版控+csproj) |
| `NFDR105` | 申購交易確認單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR105.cs:66` | `Basic_PO` | SP | `s_NFDR105_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR107A` | 各代理扣款機構扣帳費合計／明細、銀行單筆扣款彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107A.cs:175-183` | `INFDR107A_PO` | SP+inline | `s_TA_NFDR107A_Get` | `OFD303A` | 3(全在版控+csproj) |
| `NFDR107B` | 各代理扣款機構／銷售機構各基金手續費合計、明細、通知函 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:109-129` | `Basic_PO` | SP+inline | `s_NFDR107B_Get`、`s_NFDR107B_T2_Get` | `CTL018`、`OFD303A` | 3(全在版控+csproj) |
| `NFDR108` | 公司人員銷售彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR108.cs:77` | `Basic_PO` | SP | `s_NFDR108_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR109` | 銷售彙總查核表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR109.cs:266` | `INFDR109_PO` | SP | `S_TA_NFDR109_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR111` | 手續費彙總表／基金手續費彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR111.cs:140-145` | `INFDR111_PO` | SP | `S_TA_NFDR111_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR114` | 印花稅明細表／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR114.cs:49-53` | `Basic_PO` | SP+inline | `s_NFDR114_Get` | `F_FORMATSTRINGTOTABLE`、`OFD303A` | 2(全在版控+csproj) |
| `NFDR115` | 申購統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR115.cs:120` | `Basic_PO` | SP+inline | `s_NFDR115_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR120` | 代銷銀行單筆／定額申購明細表（列印＋下載） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR120.Designer.cs:439-505` | `INFDR120_PO` | SP | `S_TA_NFDR120_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR121` | 券商單筆／定額申購明細表、彙總表（列印＋下載） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR121.Designer.cs:303-581` | `INFDR121_PO` | SP | `S_TA_NFDR121_GET_1`、`S_TA_NFDR121_GET_2` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR122` | 月平均成本餘額明細／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR122.cs:140-260` | `INFDR122_PO` | SP | `S_TA_NFDR122_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR123` | 受益人 KYC 到期名單（Excel） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` | `INFDR123_PO` | 純 inline | (無) | `BMS001A`、`COD009`、`OFD123A`、`OFD123A_TMP`、`OFD221A`、`OFD221A_TMP`、`OFD306A`、`OFD306_TMP` | **0**(非 Crystal) |

### 3.5 第 150–160 群:買回／贖回／轉申購側(10 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR150` | 買回彙總查核表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR150.cs:227` | `INFDR150_PO` | SP | `S_TA_NFDR150_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR151` | 買回申請書資料查核表／買回費用查核表／買回轉申購明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR151.cs:156-186` | `INFDR151_PO` | SP | `S_TA_NFDR151_GET_Charge`、`S_TA_NFDR151_GET`、`S_TA_NFDR151_GET_1`、`S_TA_NFDR151_GET_2`、`S_TA_NFDR151_GET_3`、`S_TA_NFDR151_GET_5`、`S_TA_NFDR151_GET_4` | **看不到(SP 黑箱)** | 4(全在版控+csproj) |
| `NFDR153` | 贖回沖銷明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR153.cs:100` | `Basic_PO` | SP | `s_NFDR153_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR154` | 贖回交易確認單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR154.cs:84` | `Basic_PO` | SP+inline | `s_NFDR154_Get` | `OFD081V` | 1(全在版控+csproj) |
| `NFDR155` | 買回暫不付款通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR155.cs:81` | `Basic_PO` | SP | `s_NFDR155_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR156` | 買回補件付款通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR156.cs:36` | `Basic_PO` | SP | `s_NFDR156_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR157` | 公司支付郵匯費明細／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR157.cs:196-200` | `INFDR157_PO` | SP | `S_TA_NFDR157_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR158` | 贖回統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR158.cs:136` | `Basic_PO` | SP+inline | `s_NFDR158_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR159` | 轉申購統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR159.cs:115` | `Basic_PO` | SP+inline | `s_NFDR159_Get`、`s_NFDR159_1_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR160` | 轉申購明細／彙總表（轉出＋轉入） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR160.cs:94-112` | `INFDR160_PO` | SP | `s_TA_NFDR160_Get`、`s_TA_NFDR160_1_Get` | **看不到(SP 黑箱)** | 4(全在版控+csproj) |

## 4. 維護畫面(M)

**本模組無 M 畫面。**

原因:`NFD` 是純輸出層,不擁有任何業務表(§0.1、§2.1)。資料的新增 / 修改 / 刪除全部在 `ATLAS.OFD` 的 M 畫面完成,`NFD` 只負責把結果印出來。

這件事在程式上是可驗證的,不是推測:

| 證據 | 內容 |
|---|---|
| 沒有 `ATLAS.NFD` 主專案 | `Dev/` 下只有 `ATLAS.NFD.Report`,其他模組都是「主專案 + `.Report`」成對 |
| 127 支全部繼承 `xReportForm` | 例 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:21`;沒有一支是 `xMaintainForm` |
| Ctl 沒有四眼方法 | 每支 Ctl 只有 `GetXxxReportData` / `GetXxxReportObject`(+ 少數 `chkXxx`),沒有 `Verify` / `Approve` / `Reject`,例 `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:39-76` |
| PO 沒有繼承四眼基底 | 44 支的基底只有 `INFDRxxx_PO`(介面)或 `Basic_PO`,沒有 `Basic4EyesPO` / `BasicEVAPO` / `MultiRow4EyesPO` |

**這是 `NFD` 最大的特徵,也是讀這個模組時最容易誤判的地方**:看到 `NFDR073` 在 `INSERT` / `DELETE` `NFDR073T*`,不要以為它在維護業務資料——那些是為了印一份對帳單而生的中繼表,列印完就沒有意義(§2.4)。同理 `NFDR073B` 的 `S_TA_NFDR073B_EMAIL` 會寫寄信佇列,那是「輸出」的一部分,不是業務異動。

**維護時的推論**:任何「報表數字不對」的問題,`NFD` 這一層能做的只有三件事——條件傳錯、SP 拿錯、Transfer 漏搬。數字本身錯要回 `OFD` 或 SP 去找。

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因同 §4。不過報表畫面本身帶有**查詢性質的副作用**,讀的時候要當成查詢畫面看待:

| 支 | 查詢性質的副作用 | 錨點 |
|---|---|---|
| `NFDR001` | 畫面上有 `ugrdClass` 類別選擇 grid,由 `GetClassData` 另外取數 | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:69-74` |
| `NFDR076` / `NFDR077` | 列印前先打 `chkOFD303A` / `chkOFD221A` 查「這段日期日結了沒」,結果用彈窗問使用者要不要繼續 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:109-131` |
| `NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` | 有 `GetFUND` 取基金下拉清單 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:96-104` |
| `NFDR120` / `NFDR121` / `NFDR123` | 有「下載 Excel」路徑,等同把查詢結果落地 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:75-86` |

## 6. 批次(B)與 WindowsService

**本模組無 B 畫面,也沒有任何 WindowsService。**

但有兩支**在行為上等同批次**,不要因為它們掛在報表清單就當成「印一張紙」:

| 支 | 為什麼像批次 | 錨點 |
|---|---|---|
| `NFDR073A` | 在一個 transaction 內連續跑 5 支 SP(`S_TA_NFDR073_3_GET` / `_0_GET` / `_4_GET` / `_1_GET` / `_2_GET`)灌 17 張暫存表,再產文字檔並可加密壓縮。可選「郵寄」或「E-mail」兩條發送途徑 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:105-150`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:114` |
| `NFDR073B` | 「產生 Email 資料」按鈕跑 `S_TA_NFDR073B_EMAIL`,在 transaction 內寫寄信資料並回傳筆數 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160-190` |

兩支都由**人按按鈕觸發**,沒有排程。所以「這個月對帳單有沒有寄出去」這件事,系統裡沒有任何自動保證——漏按就是漏寄,而且**不會有任何告警**。

## 7. 報表(R)——主體

```text
[圖] NFDR073A 的完整資料流：畫面條件、前置檢核、五支 SP、十七張暫存表、四個模組的表、文字檔與加密壓縮輸出
圖中文字:NFDR073A 月／季對帳單文字檔：條件 → 取數 → 暫存表 → 輸出 / ① 畫面條件 / 淨值日期起迄／戶號／ID／月or季／發送途徑／路徑 / ② 前置檢核 / 路徑必填+Directory.Exists；註銷戶→阻擋 / ③ dataID / Substring(0,22) 截斷 → 併發會撞 / ④ 一個 transaction 內連跑 5 支 SP（全部在版控外，除 _1_GET） / S_TA_NFDR073_3_GET / SEND_TYPE 含 1（郵寄） / S_TA_NFDR073_0_GET / SEND_TYPE 含 2（E-mail）OUT striMSG / S_TA_NFDR073_4_GET / DATA_TYPE 非 1 時走這條 / S_TA_NFDR073_1_GET / **唯一在版控的 SP** / S_TA_NFDR073_2_GET / 最後一支 / ⑤ 灌進 17 張自建暫存表（以 DATAID 分租） / NFDR073T5–T12 / 持股／交易明細 / NFDR073T16–T19 / 彙總 / NFDR073T24 T29 T31 T33 T34 / 格式化後的列 / NFDR073T6 T7 / 與 NFDR073 共用 / ⑥ 再 SELECT 回來（此處才看得到別人的表） / OFD081A OFD081V OFD0811A / 基金名稱／小數位／警語 / OFD132A / — / BMS001A / 受益人 / FSK003 / 風險屬性 / ⑦ 輸出：沒有 .rpt / CreateTxtFiles.CreateNFDR073AText(...) / 文字檔寫到 utxtPath / IsSetZip = Y → 加密壓縮 / 密碼 NFDR073A_PASSWORD 存在 config / 失敗只說「產生檔案失敗」 / 五個字，無細節
```

*圖:圖 4 NFDR073A 資料流（§7.3.3）。這是本片最複雜也最危險的一支：橘虛框=已知風險（dataID 截斷、密碼存 config、錯誤訊息無細節）；黑框=版控外的 SP；灰虛框=別模組的表；橘框=本文重點。注意它沒有任何 .rpt——輸出是文字檔，不是 Crystal 報表。*

### 7.0 怎麼讀這一章

44 支共用同一套骨架(§1.3),所以本章只對**每群最具代表性的一支**、**兩對後綴**、以及**行為異常的那幾支**展開;其餘在 §3 的清冊已經帶過。每節固定四段:**做什麼 / 條件與卡控 / 取數 / 輸出**。

卡控結果一律五類:**阻擋**(不讓印)/ **警示**(印但跳訊息)/ **詢問**(Yes-No 再決定)/ **過濾(無提示)**(悄悄少印)/ **記錄不擋**。

### 7.1 第 001–007 群:受益人結構與法遵月報

七支的共同形狀:**單一 SP、參數走 `Utility.Parameters`、Crystal 出圖**。`NFDR001` 是其中唯一有 grid 與 inline SQL 的,拿它當代表。

#### 7.1.1 `NFDR001` 基金受益人名冊(本群最完整的一支)

**做什麼**:依截止日與申購日期區間,印出某檔基金的受益人名冊,可依不同排序與用途切換版面。

**條件**(全部從 `Utility.Parameters` 傳,無字串串接):

| 參數 | 來源控件 | 傳給 SP 的名字 | 錨點 |
|---|---|---|---|
| `BAL_DATE` | `udatBAL_DATE` | `datiBAL_DATE` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:66-70` |
| `ALLOT_DATE_ST` / `ALLOT_DATE_END` | `udatALLOT_DATE_ST` / `_END` | `datiALLOT_DATE_ST` / `_END` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:71-81` |
| `FUND_ID` | `custFUND_ID_0` | `striFUND_ID` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:83-87` |
| `Purpose` / `Class` / `Class_Code` / `BY_AGENT` | `uoptPurpose` / `uoptClass` / grid / `uoptBY_AGENT` | 同名加 `stri` 前綴 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:88-105` |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按預覽 | `DoValidate()` + `ValidateErrList.Show()` | 有必填未填 | **阻擋**(`e.Cancel = true`) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:75-80` |
| 按預覽 | `uoptOrder` 只認 `"0"`/`"1"`/`"2"`/`"3"`,`uoptPurpose` 只認 `"0"`/`"1"` | 值不在列舉內 | **過濾(無提示)**——整串 `if / else if` 掉出去,**`SetQueryParameters` 一次都沒呼叫**,報表類別是空的 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131` |
| `ReportLoad` | `Purpose` 參數只在 `Purpose=="1"` **且** `Order` 是 `"0"` 或 `"3"` 時才 `SetParameterValue` | 其他組合 | **過濾(無提示)**——Crystal 沿用上一次的值 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:64-68` |
| PO | `Cmd.CommandTimeout = 0` | SP 跑很久 | **記錄不擋**——無限等待 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56` |

**取數**:`s_TA_NFDR001_Get`(**版控外**)。另有一段 inline SQL 取 grid 的類別清單,讀 `CTL014` 與 `OFD017A`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:173`)。

**輸出**:8 種「排序 × 用途」組合對應 5 個 `.rpt`,對應關係**不是一對一**:

| `uoptOrder` | `uoptPurpose` | `.rpt` |
|---|---|---|
| `0` | `0` | `NFDR001RPS2` |
| `0` | `1` | `NFDR001RPS1` |
| `1` | `0` | `NFDR001RPS` |
| `1` | `1` | `NFDR001RPS3` |
| `2` | `0` | `NFDR001RPS` |
| `2` | `1` | `NFDR001RPS4` |
| `3` | `0` | `NFDR001RPS` |
| `3` | `1` | `NFDR001RPS1`(**與 Order=0/Purpose=1 同一張**) |

錨點 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131`。`NFDR001RPS` 被三種排序共用、`NFDR001RPS1` 被兩種共用——**改其中一張會同時影響多個選項組合**,這是本模組改 `.rpt` 最容易踩到的坑。

#### 7.1.2 其餘六支(表格帶過)

| 支 | SP | `.rpt` | 值得注意 |
|---|---|---|---|
| `NFDR002` 資金來源分析表 | `s_TA_NFDR002_Get` | 2 | PO 只有 104 行,純參數轉發 |
| `NFDR003` 股權分散表 | `s_TA_NFDR003_Get` | 1 | 法遵用 |
| `NFDR004` 員工及其關係人買賣本公司基金月報表 | `s_TA_NFDR004_Get` | 1 | 法遵用,PO 96 行 |
| `NFDR005` 基金受益憑證持有者統計表 | `s_TA_NFDR005_Get` | 1 | SP 名直接寫在 `GetStoredProcCommand("…")` 裡,不經變數 |
| `NFDR006` 債券型基金其他資訊揭露月報表 | `s_TA_NFDR006_Get` | 1 | 法遵用 |
| `NFDR007` 各基金餘額比例表 | `s_TA_NFDR007_Get` | 1 | — |

六支**都沒有任何「查無資料」提示**(§附錄 E-05)。SP 回空集合時,使用者看到的是一張只有表頭的 Crystal 報表,分不出「真的沒有」還是「條件打錯」。

### 7.2 第 021–024 群:受益人排行與異常清冊

三支,`NFDR022` 存在於專案內但**不在本片名單**(見 §7.6 跳號說明)。

| 支 | 中文名 | PO 基底 | SP | 特別的地方 |
|---|---|---|---|---|
| `NFDR021` | 受益人基金持有 / 申購 / 贖回單位數排行表、持有餘額排序一覽表 | `INFDR021_PO` | `s_TA_NFDR021_Get` | **一支 SP 服務四種報表名**,由 UI 選項決定標題與 `.rpt`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58`) |
| `NFDR023` | 受益人異動及定額異動重覆報表 | **`Basic_PO`** | `s_NFDR023_Get` | 未遷移,`m_db` 為 `null`(附錄 E-02) |
| `NFDR024` | 受益人統編異常清冊 | `INFDR024_PO` | `S_TA_NFDR024_GET` | SP 名全大寫,與同群 `s_NFDR023_Get` 的小寫風格不一致(§2.2) |

`NFDR021` 的四個報表名共用同一支 SP,代表**四種排行的差異全在 SP 裡的 `ORDER BY`**。想加第五種排行,要改的是版控外的 SP,repo 內只能改標題字串——**這種改動在 code review 時完全看不出風險**。

#### 7.2.1 `NFDR021` 一支 SP 四個報表名的實際寫法

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58` 四個 `SetQueryParameters` 分支:

| 報表名 | 意義 |
|---|---|
| 受益人基金持有單位數排行表 | 目前持有 |
| 受益人基金申購單位數的排行表 | 期間申購 |
| 受益人基金贖回單位數的排行表 | 期間贖回 |
| 受益人持有餘額排序一覽表 | 依金額排序 |

四者共用 `s_TA_NFDR021_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR021_PO.cs:58`),差異全在 SP 內部。**repo 內看不到「排行」是怎麼排的、取前幾名、同名次怎麼處理**——這些全部在版控外。

`.rpt` 只有兩張(`NFDR021RPS`、`NFDR021RPS2`),四個報表名對兩張版型,又是一對多(附錄 E-16)。

#### 7.2.2 `NFDR024` 受益人統編異常清冊

唯一一支名字裡帶「異常」的報表。取數走 `S_TA_NFDR024_GET`(**版控外**,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR024_PO.cs:59`),PO 只有 97 行、純參數轉發。

**「統編異常」的判斷規則完全在 SP 裡**——身分證檢查碼?統編檢核碼?重複?repo 內一個字都查不到。這支是「法遵規則藏在版控外」的典型:規則變了(例如新式統編),改的是資料庫,程式碼的 git log 上什麼都看不到。

#### 7.2.3 `NFDR023` 受益人異動及定額異動重覆報表

本群唯一有欄位中文名的一支(`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR023Model.xsd`):

| 欄位 | 中文名 |
|---|---|
| `RCV_DATE` / `CHG_UPD_DTTM` / `CHG_EFFECT_DATE` | **三個欄位的 `Caption` 都是「異動生效日期」** |
| `DATA_TYPE` | 異動類別 |
| `ID_NO` | 受益人ID |
| `BF_NO` | 戶號 |
| `BF_NAME` | 受益人姓名 |
| `RSP_CHG_NO` | 重覆異動交易單號 |

**三個不同的日期欄位掛同一個中文名**,報表上並排出現時分不出誰是誰。`RCV_DATE`(受理日)、`CHG_UPD_DTTM`(異動寫入時間)、`CHG_EFFECT_DATE`(生效日)語意明顯不同,這是複製貼上 `Caption` 的結果。

這支同時是 `Basic_PO`(附錄 E-02),所以目前跑不起來——**中文名寫錯的問題還輪不到被發現**。

### 7.3 第 071–077 群:對帳單、確認書與公告(本模組的核心)

八支裡有五支是**直接寄給客戶的正式文件**,錯一個字就是客訴。本群也是全片唯一有 inline SQL 大量出現的地方。

#### 7.3.1 `NFDR073` 投資對帳單(本群最複雜,674 行 PO)

**做什麼**:產出受益人的投資對帳單,可單戶、可全戶。

**取數**:兩支 SP 二選一,判斷式在一行三元運算子裡:

```
cmd = string.IsNullOrEmpty(GetParamValue(model, "BF_NO")) && string.IsNullOrEmpty(GetParamValue(model, "ID_NO"))
    ? m_db.GetStoredProcCommand("s_NFDR073_1_Get") : m_db.GetStoredProcCommand("s_NFDR073_Get");
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97`

只有 `IsSelected == "0"` 或 `"1"` 兩個分支;**其他值時 `cmd` 保持 `null`,下一行 `cmd.CommandTimeout = 0` 直接 NRE**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:95-107`)。

**暫存表**:`NFDR073T0` / `T6` / `T7` 以 `dataID` / `SEND_NO` 分租,列印前先清:

```
DELETE FROM NFDR073T6 WHERE dataID = @dataID; DELETE FROM NFDR073T7 WHERE dataID = @dataID
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385`

**這段 SQL 是 MSSQL 語法**:`@dataID` 具名參數、一行兩個 statement 用 `;` 分隔。Oracle 兩者都不吃。同檔還有 `IF EXISTS(SELECT * FROM OCRMTMP WHERE SID = @SID) SELECT 1 ELSE SELECT 0`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:539`)——純 T-SQL。配合 `NFDR073_PO` 是 `Basic_PO`(`m_db` 未初始化)的事實,**這支的這幾條路徑目前跑不起來**(附錄 E-02)。

**輸出**:1 張 `.rpt`(`NFDR073RPS`),報表名寫成 `const string ReportName = "投資對帳單"`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49`)——全片唯一用 `const` 的,其他支都是字面字串散在各分支。

#### 7.3.2 `NFDR073A` / `NFDR073B` 兩個後綴的成因(必答問題 4 之一)

先給結論表:

|  | `NFDR073` | `NFDR073A` | `NFDR073B` |
|---|---|---|---|
| 有沒有不帶後綴的版本 | **有**(就是它自己) | — | — |
| 中文名 | 投資對帳單 | 月 / 季對帳單(**文字檔**) | 貴賓理財對帳單 |
| 用哪些 SP | `s_NFDR073_Get` / `s_NFDR073_1_Get` / `s_NFDR073_ChkRdm` | **`S_TA_NFDR073_0_GET` ~ `_4_GET`** | **`S_TA_NFDR073B_GET`**、`S_TA_NFDR073B_EMAIL` |
| 輸出 | Crystal `.rpt` × 1 | **文字檔 + 可選 ZIP 加密**,無 `.rpt` | Crystal `.rpt` × 4 |
| PO 基底 | `Basic_PO`(未遷移) | `INFDR073A_PO`(Oracle) | `INFDR073B_PO`(Oracle) |
| PO 行數 | 674 | 651 | 347 |

**`A` 的成因**:`NFDR073A` 的 SP **叫 `S_TA_NFDR073_x_GET`,名字裡沒有 `A`**。也就是說 `A` 只存在於**畫面代號**,資料端仍屬 `NFDR073` 這一家。這對應前 24 篇的第 (d) 類——「`A` 是畫面代號的一部分、與表無關」(`ofdi1.md` 的 `OFDI075A` 查 `OFD304A` 是同一型)。**但成因不完全一樣**:`ofdi1.md` 那例是畫面代號與表代號各走各的;這裡是**同一份對帳單的第二個出口**(螢幕預覽 vs 文字檔批次產出),`A` 表示「同資料、不同交付方式」。這是前 24 篇沒出現過的第六種,本文記為 **(f) 同資料的第二個出口**。

**`B` 的成因**:`NFDR073B` 有自己的 `S_TA_NFDR073B_GET`、自己的 4 張 `.rpt`、自己的暫存表(`DB/Table/NFDR073BT1.sql`、`DB/Table/NFDR073BT2.sql`),報表名也不同(貴賓理財對帳單)。這是標準的第 (c) 類——**同概念的第二份產物**,和 `ofd123.md` 的 `OFD017B` 同型。

**不是境內外(第 (a) 類)**:本組三支都沒有出現 `FUND_TYPE = '1'/'2'` 或 `SHORE_ID` 的分流;`NFDR073A` 的分流參數是 `RPT_TYPE`(月 / 季)與 `SEND_TYPE`(郵寄 / E-mail),不是境內外。**不是 MSSQL→Oracle 改名(第 (b) 類)**:三支同時存在且互不重複。

#### 7.3.3 `NFDR073A` 為什麼是全片最危險的一支

| 風險 | 說明 | 錨點 |
|---|---|---|
| `dataID` 截斷到 22 碼 | `strDATAID.Substring(0, 22).Trim()`。暫存表以 `dataID` 分租,**兩人同時跑且前 22 碼相同時,兩份對帳單的資料會互相污染** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102` |
| 長度沒防呆 | `Substring(0, 22)` 在 `strDATAID` 短於 22 時直接丟 `ArgumentOutOfRangeException` | 同上 |
| 五支 SP 在同一個 transaction | 任一支失敗整批 rollback,但 UI 只顯示「產生檔案失敗」五個字 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:120` |
| 密碼來自 config | `NFDR073A_PASSWORD` 從 `GetConfigSetting` 讀,明文存在設定檔〔客戶特定〕 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:25` |
| 存檔路徑可自由輸入 | `utxtPath` 只檢查 `Directory.Exists`,沒有白名單;對帳單是個資 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:60-67` |
| 註銷戶檢核 | 訊息「此 受益人 為註銷戶!」——**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:185,196` |
| `NVL(REJ_POST,' ')<>'Y'` | 這一條寫得**對**:用 `NVL` 包起來,NULL 不會被三值邏輯吃掉。同檔的 `BF_SORT_CD <> '012'` **沒包**,`BF_SORT_CD` 為 NULL 的受益人會被靜默排除 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195,425` |

#### 7.3.4 `NFDR076` / `NFDR077` 申購與買回轉申購交易確認書

這兩支是**全片卡控最完整的一對**,也是唯一會在列印前主動檢查「日結了沒」的。

**`NFDR076` 的卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按預覽 | `DoValidate()` | 必填未填 | **阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:179` 前的驗證區 |
| 按預覽 | `chkOFD303A`——查 `OFD303A` 在日期區間內有沒有 `POST_CTL_CODE = 'N'`(未過帳)的資料 | 有未日結 | **詢問**(`Info03` Yes/No,按 No 就 `e.Cancel`) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:109-117` |
| 按預覽 | `chkOFD221A` | 檢核不過 | **警示**;但若勾了 `uchkData` 則升級為**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:121-133` |
| 取數後 | `無符合查詢條件的資料` 訊息 | 零筆 | **警示** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs`(訊息字串,2 處) |

**`chkOFD303A` 的 SQL 有三個要注意的地方**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:141-158`):

1. **`JOIN` 是 INNER**:`FROM OFD303A JOIN OFD0811A ON OFD303A.FUND_ID = OFD0811A.FUND_ID`。`OFD0811A` 沒有對應基金的交易,**這筆未日結資料就查不到,檢核直接放行**——這是「`INNER JOIN` 讓對不到的資料無聲消失」在檢核上的變形,比在報表上更危險(報表少印看得出來,檢核漏掉看不出來)。

2. **`INV_AREA <> 'D'` 判海外**:`INV_AREA` 為 NULL 時整條是 UNKNOWN,該基金被靜默排除。同一段的 `INV_AREA = 'D'`(判境內)沒有這個問題。

3. **`OR (:striFUND_ID IS NOT NULL AND :striFUND_ID = :striFUND_ID)`**:恆真條件。使用者一旦指定了基金代碼,**整段「基金類型」篩選就全部失效**。看起來像是刻意寫的「指定基金時不看類型」,但寫成恆真式而不是註解說明,下一個維護者很容易當成 bug 刪掉。

**`NFDR077` 與 `NFDR076` 的差異**(必答問題 3 的「最相似的一組」):

|  | `NFDR076` | `NFDR077` |
|---|---|---|
| 報表名 | 申購交易確認書 / (郵簡) / (彙總) | 買回轉申購交易確認書 / (郵簡) / 申購交易確認書(彙總) |
| SP | `S_TA_NFDR076_GET` | `S_TA_NFDR077_GET` |
| 讀的表 | `OFD303A` `OFD0811A` `OFD221A` `BMS001A` | `OFD303A` `OFD0811A` `OFD081A` `OFD251A` `BMS001A` `MYOFD303A` |
| `.rpt` | 5 | 3 |
| 日結檢核 | `chkOFD303A` + `chkOFD221A` | 檢 `OFD251A.REDEM_PROC_CODE<>'3'` 與 `A.REDEM_CTL_CODE <> '4'` |
| PO 行數 | 316 | 428 |

**兩支共用同一段「基金類型」條件**——連 `NOT IN ('7A','7B')` 排除兩檔基金的寫死值都一字不差(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:148-150` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:175-177`)。**這是「成對報表只改一邊」的完美溫床**:業務要調整基金分類時,兩支要一起改,而且 `NFDR076` 自己內部還有兩份複本(`:148` 和 `:238`)、`NFDR077` 也有兩份(`:175` 和 `:352`)——**一次改動要同步四個地方**。

`'7A'` / `'7B'` 是〔客戶特定〕的基金代碼,註解只寫「股票型(海外),排除 7A 及 7B」,沒說為什麼。

#### 7.3.5 本群其餘三支

| 支 | 中文名 | PO 基底 | SP | 注意 |
|---|---|---|---|---|
| `NFDR071` | 法人公告警示表 | **`Basic_PO`** | `s_NFDR071_Get` | 未遷移 |
| `NFDR072` | 法人買回公告明細表 / 法人贖回公告明細表 | **`Basic_PO`** | `s_NFDR072_Get` | 未遷移;同一支 SP 兩個報表名,「買回」與「贖回」在本系統是同義詞 |
| `NFDR075` | 傳真委託申購 / 傳真委扣－扣款失敗通知書 | `INFDR075_PO` | `s_TA_NFDR075_Get` | 已遷移;兩個名字差在「委託申購」vs「委扣」 |

`NFDR073B` 的細節:

| 項目 | 內容 | 錨點 |
|---|---|---|
| 報表名 | 「貴 賓 理 財 對 帳 單」(**字間有全形空白**,四處硬寫,改一處會不一致) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123,134,145,157` |
| 零筆訊息 | `【{報表名}{子名}】無符合查詢條件的資料。`——**警示** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:232` |
| Email 產生 | `S_TA_NFDR073B_EMAIL`,`OUT R_CNT` 回筆數,`> 0` 才算成功 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160-190` |
| `catch (OracleException) { … tran.Rollback(); }` | **`tran` 若在 `BeginTransaction` 之前就拋例外,這裡會 NRE,把真正的錯誤蓋掉** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:193-199` |
| 讀的表 | `OFD002`、`COD009`、`SAL051`、`DUAL` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:258,323` |

### 7.4 第 101–123 群:申購側(16 支,本片最大的一群)

這一群是「錢進來之後」的所有輸出:扣款、手續費、印花稅、統計月報、KYC 名單。也是 `Basic_PO` 未遷移比例最高的一群(16 支裡 6 支)。

#### 7.4.1 群內分工

| 子題 | 支 | 共同點 |
|---|---|---|
| 指定扣款 / 傳真委扣 | `NFDR101` `NFDR102` `NFDR103` | 三支是**同一份資料的彙總 / 明細 / 失敗明細**,各自有「指定扣款」與「傳真委扣」兩個報表名 |
| 交易確認與明細 | `NFDR104` `NFDR105` | `NFDR104` 申購明細表(PO 326 行,本群最長);`NFDR105` 申購交易確認單 |
| 手續費 / 扣帳費 | `NFDR107A` `NFDR107B` `NFDR111` | 見 §7.4.3 |
| 銷售統計 | `NFDR108` `NFDR109` `NFDR115` | `NFDR108` 公司人員銷售彙總、`NFDR109` 銷售彙總查核、`NFDR115` 申購統計月報 |
| 稅 | `NFDR114` | 印花稅明細 / 彙總 |
| 通路明細(可下載) | `NFDR120` `NFDR121` | 代銷銀行 / 券商;兩支都有「列印」與「下載 Excel」雙路徑 |
| 成本與 KYC | `NFDR122` `NFDR123` | `NFDR122` 月平均成本餘額;`NFDR123` KYC 到期名單(純 Excel) |

#### 7.4.2 `NFDR123` 受益人 KYC 到期名單(本群最完整的一支,也是全片唯一純 Oracle CTE)

**做什麼**:列出到某個基準日為止、KYC 快到期或已到期、而且仍有持股的受益人,輸出成 Excel 給業務去催。

**取數**:全片唯一**沒有 SP** 的一支。整段 SQL 是一個 100 行的 Oracle `WITH` 查詢,直接寫在 PO 裡(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:60-93`)。四個 CTE:

| CTE | 讀什麼 | 作用 |
|---|---|---|
| `OFD123A_TMP` | `OFD123A` | KYC 主檔篩選 |
| `OFD306_TMP` | `OFD306A` + `TABLE(F_TA_GETFUNDNAV(...))` | 以 `HAVING SUM(CHG_UNIT) > 0` 只留**還有持股**的人 |
| `OFD221A_TMP` | `OFD221A` | 取每人**最後一筆申購**(`MAX(ALLOT_DATE |
| 主查詢 | `BMS001A` `COD009` | 受益人基本資料與員工姓名 |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 主查詢 | `JOIN BMS001A ON T1.BF_NO = BMS001A.BF_NO`(**INNER**) | 受益人主檔缺這筆 | **過濾(無提示)** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:87` |
| 主查詢 | `JOIN OFD306_TMP T2`(**INNER**) | 目前沒有持股 | **過濾(無提示)**——設計如此 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:88` |
| 主查詢 | `JOIN OFD221A_TMP T3`(**INNER**) | **從來沒有申購紀錄** | **過濾(無提示)**——⚠ 這條不見得是刻意的 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:89` |
| 主查詢 | `LEFT JOIN COD009` | 業務員代碼查不到姓名 | 保留該列,姓名為空(`NVL(..., ' ')`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:90` |
| 主查詢 | `NVL(TRIM(BMS001A.FREEZE_CD),'N') = 'N'` | 凍結戶 | **過濾(無提示)**——但 NULL 處理正確 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:92` |
| 輸出 | `saveFileDialog1.FileName = "受益人KYC到期名單.xlsx"` | 永遠 | 檔名寫死,不帶日期 / 條件 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` |

**第三條是本片最會咬人的一處**:KYC 到期名單是**法遵用途**,少列一個人代表少催一個人。一位受益人如果持股是**轉申購轉進來的**(記在 `OFD306A`,不是 `OFD221A`),`JOIN OFD221A_TMP` 就對不到,他會從名單上**無聲消失**。畫面不會有任何提示,Excel 也不會少一行紅字——只是少一行。

`NFDR123` 的 NULL 處理本身寫得很好(`NVL` 用了 8 次),這反而說明作者知道 NULL 的問題;`INNER JOIN` 的取捨是**取數設計**的問題,不是疏忽型 bug——但效果一樣。

#### 7.4.3 `NFDR107A` / `NFDR107B` 兩個後綴的成因(必答問題 4 之二)

|  | `NFDR107A` | `NFDR107B` |
|---|---|---|
| 有沒有 `NFDR107` | **沒有**。`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/` 與 `PO/ReportPO.NFD/` 都查無 `NFDR107` | 同左 |
| 中文名 | 各代理扣款機構**扣帳費**合計表 / 扣帳費用明細 / 銀行單筆扣款彙總表 | 各代理扣款機構 / 各銷售機構各基金**手續費**合計表 / 明細表 / 通知函 |
| SP | `s_TA_NFDR107A_Get` | `s_NFDR107B_Get`、`s_NFDR107B_T2_Get` |
| PO 基底 | `INFDR107A_PO`(Oracle,已遷移) | **`Basic_PO`**(未遷移) |
| 參數風格 | Oracle bind `:start` / `:end` | MSSQL `@datiALLOT_DATE_ST` 等 17 個 |
| 讀的表 | `OFD303A` | `OFD303A`、`CTL018` |
| `.rpt` | `NFDR107ARPS1` ~ `RPS3` | `NFDR107BRPS1` ~ `RPS3` |
| 檔案編碼 | **cp950** | **cp950** |

**結論:這一對屬於前述五種成因的第 (e) 類「族名」**——`A` 與 `B` 是同一個編號底下的兩個**業務主題**(扣帳費 vs 手續費),沒有不帶後綴的基準版,兩者資料來源與 SP 各自獨立,不是境內外、不是遷移改名、不是同概念的第二張表。

**但有一個前 24 篇沒記錄過的佐證**:兩支的 `.rpt` 都**從 `RPS1` 起算,沒有 `RPS`**(對照 `NFDR001` 是 `RPS` / `RPS1` / … / `RPS4`)。這暗示原本存在一個 `NFDR107` + `NFDR107RPS`,後來被拆成 A / B 兩支而基準版被刪掉。**這是推測,repo 內沒有 `NFDR107` 的任何殘跡可佐證**——連 `.rpt` 都沒有 `NFDR107RPS.rpt`。

**維護上要注意的是兩支的落差**:`NFDR107A` 已經遷到 Oracle、用 bind 變數;`NFDR107B` 停在 MSSQL 且 `m_db` 未初始化。**它們在選單上看起來是一對,實際上一支能跑一支不能**。

`NFDR107A` 還有一處:日結檢核 `check()` 在例外時 `return -1`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:186`)。`-1` 不是「0 筆未日結」也不是「有未日結」,呼叫端如果用 `> 0` 判斷,**查詢失敗會被當成「都日結了」放行**——fail-open。

#### 7.4.4 `NFDR114` 印花稅:一段跑不起來的 SQL

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:136-140` 把字串這樣接起來:

```
"SELECT COUNT(*) AS CNT FROM OFD303A "
+ " WHERE CTL_DATE >= @ALLOT_DATE_ST AND CTL_DATE <= @ALLOT_DATE_END"
+ "   AND ALLOT_CTL_CODE <> '3' "
+ "   AND FUND_ID IN (SELECT * FROM dbo.f_FormatStringToTable(@FUND_ID))"
+ "GROUP BY FUND_ID"
```

三個問題疊在一起:

1. **最後一段少一個空白**,接出來是 `…f_FormatStringToTable(@FUND_ID))GROUP BY FUND_ID`,任何資料庫都是語法錯誤。

2. **`dbo.f_FormatStringToTable` 是 MSSQL 的 table-valued function**,Oracle 沒有 `dbo` schema 也沒有這支;`@` 具名參數同理。

3. **`GROUP BY` + `ExecuteScalar`**:就算文法對了,`ExecuteScalar` 只取第一列第一欄,拿到的是**第一檔基金的筆數**,不是總筆數。

再加上 `NFDR114_PO` 是 `Basic_PO`、`m_db` 未初始化(附錄 E-02),這段實際上執行不到就先 NRE 了。**三重失效互相掩蓋,是這個模組最典型的樣子**:錯誤沒被發現,是因為程式根本沒跑到。

#### 7.4.5 `NFDR105` 申購交易確認單:字串串接進 SQL

```
strWhereCode += " AND [OFD006]." + Row.Name + " = " + "'" + Row.Value + "'";
…
strWhereCode += " AND [OFD006]." + Row.Name + " Like " + "'" + Row.Value + "%'";
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180,185`

**欄位名與值都是直接串進去的**,值連跳脫都沒有。`Row.Name` 來自 `Utility.Parameters`,由 UI 填;`Row.Value` 同理。這是本片唯一一處把使用者可控字串直接拼進 SQL 的地方(`ofdi1.md` 的 `OFDI481_PO.cs:142` 是同型)。

`[OFD006]` 用的是 MSSQL 的中括號識別字,這支同樣是 `Basic_PO`。所以現況是「有洞但打不開」——**遷移這支時必須先修這段,不能照抄**。

#### 7.4.6 本群其餘支(表格帶過)

| 支 | PO 基底 | SP | 值得一提 |
|---|---|---|---|
| `NFDR101` | `INFDR101_PO` | `S_TA_NFDR101_GET` | 另有 inline SQL 讀 `CTL018` 取代碼 |
| `NFDR102` | `INFDR102_PO` | `S_TA_NFDR102_GET` | 純轉發 |
| `NFDR103` | **`Basic_PO`** | `s_NFDR103_Get` | 未遷移 |
| `NFDR104` | `INFDR104_PO` | `s_TA_NFDR104_Get` | PO 326 行,本群最長;`DB/Table/Alter_NFDR104_T0.sql` 顯示它有自己的暫存表 `NFDR104_T0` |
| `NFDR108` | **`Basic_PO`** | `s_NFDR108_Get` | 未遷移 + **cp950 編碼**(Ctl / Pxy / PO 三層都是) |
| `NFDR109` | `INFDR109_PO` | `S_TA_NFDR109_GET` | — |
| `NFDR111` | `INFDR111_PO` | `S_TA_NFDR111_GET` | 一支 SP 兩個報表名(手續費彙總 / 基金手續費彙總) |
| `NFDR115` | **`Basic_PO`** | `s_NFDR115_Get` | 未遷移;`GetFUND` 的 inline SQL 讀 `OFD081V` + `[OFD038]`,**MSSQL 中括號** |
| `NFDR120` | `INFDR120_PO` | `S_TA_NFDR120_GET` | 「下載」選項另走 Excel |
| `NFDR121` | `INFDR121_PO` | `S_TA_NFDR121_GET_1` / `_2` | 兩支 SP 分別對應單筆 / 定額 |
| `NFDR122` | `INFDR122_PO` | `S_TA_NFDR122_GET` | UI 內有 `ReportName` 欄位的工作佇列結構,**一次可連印多張**(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR122.cs:130-185`) |

### 7.5 第 150–160 群:買回 / 贖回 / 轉申購側(10 支)

對稱於 §7.4,這一群是「錢出去」的輸出。`Basic_PO` 比例最高:10 支裡 **7 支**(`NFDR153` `NFDR154` `NFDR155` `NFDR156` `NFDR158` `NFDR159`,加上群外相依的),只有 `NFDR150` `NFDR151` `NFDR157` `NFDR160` 已遷移。

#### 7.5.1 `NFDR151` 買回申請書資料查核表(本群最完整的一支)

**做什麼**:一支畫面產四種 Crystal 報表 + 兩種 Excel 附表,共六種輸出。

**取數分派**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:68-122`):

| 觸發 | 值 | SP | 結果集 |
|---|---|---|---|
| Crystal | `NFDR151RPS` | `S_TA_NFDR151_GET` | `NFDR151` + `NFDR151_CER` |
| Crystal | `NFDR151RPS1` | `S_TA_NFDR151_GET_1` | `NFDR151_1` |
| Crystal | `NFDR151RPS2` | `S_TA_NFDR151_GET_2` | `NFDR151_2` |
| Crystal | `NFDR151RPS3` | `S_TA_NFDR151_GET_3` | `NFDR151_3` |
| Excel | `EXCEL01` | `S_TA_NFDR151_GET_5` | `NFDR151_5` |
| Excel | `EXCEL02` | `S_TA_NFDR151_GET_4` | `NFDR151_4` |
| 加選 | `IsPrintOffsetData == "Y"` | `S_TA_NFDR151_GET_Charge` | `NFDR151_Charge` |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| PO 分派 | `reportClass` 不在四個值內 | 打錯 / 新增報表忘了加分支 | **阻擋**(`throw new Exception("未知的報表格式。")`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:98` |
| PO 分派 | `excelClass` 不是 `EXCEL01` / `EXCEL02` | 同上 | **過濾(無提示)**——`switch` 沒有 `default`,`proc` 保持空字串後續才爆 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:105-118` |
| 取數後 | `i > 0` | 零筆 | **記錄不擋**——`AddResultRow(false, 0, "")`,**訊息是空字串** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:165-170` |
| 例外 | `catch (Exception)` | 任何錯 | **記錄不擋**——`AddResultRow(false, 0, string.Empty)` 後交給 `CommonExceptionBlocker` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:197-201` |

**同一支 PO 裡兩種分派風格並存**:Crystal 用 `if / else if` + `throw`(嚴),Excel 用 `switch` 無 `default`(鬆)。**加第三種 Excel 附表時,忘了加 `case` 不會有任何錯誤訊息**。

#### 7.5.2 `NFDR159` 轉申購統計月報表:唯一寫死境內外的一支

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:107` 的基金清單查詢最後一行:

```
strSQL += "    AND SHORE_ID = '2'" + Environment.NewLine;
```

`'2'` 在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:296` 定義為 `SHORE_ID.OnShore` = **境內基金**。

這一行是**本文 §0.1「`NFD` 是境內基金報表模組」最直接的程式證據**——不是從表名推的,是寫死在條件裡的。同樣寫法也出現在不屬於本片的 `NFDR113`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR113_PO.cs:119`)。

三個問題:

| 問題 | 說明 |
|---|---|
| 寫死常數 | 已經有 `CTL014.SHORE_ID.OnShore` 可用,這裡寫字面 `'2'` |
| 只有兩支這樣寫 | 其餘 42 支沒有這條,代表**境內限定是靠 SP 保證的**,repo 內看不到 |
| 與 `[OFD038]` 中括號共存 | 同一段還是 MSSQL 語法(§7.5.3) |

#### 7.5.3 `NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` 四支複製貼上的 `GetFUND`

四支的基金清單查詢幾乎一字不差:

| 支 | 錨點 | 差異 |
|---|---|---|
| `NFDR115` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:96-104` | 多 `AND OFD081V.FUND_ID <> 'ALL FUNDS'` |
| `NFDR154` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:100-106` | 沒有 `<> 'ALL FUNDS'`;參數叫 `@FUND_GRPCD` 不是 `@FUND_GROUP` |
| `NFDR158` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR158_PO.cs:96-104` | 與 `NFDR115` 同 |
| `NFDR159` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:100-108` | 多 `AND SHORE_ID = '2'`,沒有 `<> 'ALL FUNDS'` |

**同一個下拉清單,四支看到的基金不一樣**——`NFDR115` / `NFDR158` 會排除代碼為 `'ALL FUNDS'` 的那筆,另外兩支不會;`NFDR159` 只給境內。這不是刻意設計,是四份複本各自演化的結果。

四支還共同踩到 `AND` / `OR` 括號問題:`NFDR154` 的 `WHERE (@FUNDCODE = '0') OR (…) OR (…)` **整段沒有外層括號**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:103-105`),而 `NFDR115` / `NFDR158` / `NFDR159` 有(`WHERE ((@FUNDCODE = '0') … ))`)。`NFDR154` 後面沒有再接 `AND`,所以目前不會出事——**但只要有人加一條 `AND`,`NFDR154` 的行為會和另外三支不同**。

#### 7.5.4 本群其餘支(表格帶過)

| 支 | 中文名 | PO 基底 | SP | 值得一提 |
|---|---|---|---|---|
| `NFDR150` | 買回彙總查核表 | `INFDR150_PO` | `S_TA_NFDR150_GET` | 純轉發 |
| `NFDR153` | 贖回沖銷明細表 | **`Basic_PO`** | `s_NFDR153_Get` | 未遷移 |
| `NFDR154` | 贖回交易確認單 | **`Basic_PO`** | `s_NFDR154_Get` | 未遷移;另有 inline 讀 `[OFD126].ST_CD = '03'` |
| `NFDR155` | 買回暫不付款通知書 | **`Basic_PO`** | `s_NFDR155_Get` | 未遷移 |
| `NFDR156` | 買回補件付款通知書 | **`Basic_PO`** | `s_NFDR156_Get` | 未遷移;與 `NFDR155` 是一對(暫不付款 / 補件付款) |
| `NFDR157` | 公司支付郵匯費明細 / 彙總表 | `INFDR157_PO` | `S_TA_NFDR157_GET` | 用 `DataTable.Select("REDEM_PROC_CODE<>'3'")` 在**記憶體裡**再過濾一次,`REDEM_PROC_CODE` 為 `null` 的列會被濾掉(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:88`) |
| `NFDR158` | 贖回統計月報表 | **`Basic_PO`** | `s_NFDR158_Get` | 未遷移 |
| `NFDR160` | 轉申購明細 / 彙總表(轉出 + 轉入) | `INFDR160_PO` | `s_TA_NFDR160_Get`、`s_TA_NFDR160_1_Get` | 四張 `.rpt` 對應「明細 / 彙總」×「轉出 / 轉入」,分派在 UI(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR160.cs:94-112`) |

### 7.6 跳號:`NFDR106` / `NFDR110` / `NFDR152` 到哪去了(必答問題 3 的附帶)

本片名單有三個明顯的跳號。**三支都存在,只是不在本片的 44 支裡**:

| 代號 | 在不在 repo | 六層 | `.rpt` | 判定 |
|---|---|---|---|---|
| `NFDR106` | **在** | UI / Ctl / Pxy / PO / Model / View 齊全 | `NFDR106RPS.rpt` 在 | 由別篇涵蓋,**不是缺陷** |
| `NFDR110` | **在** | 齊全 | `NFDR110RPS.rpt` 在 | 同上 |
| `NFDR152` | **在** | 齊全 | `NFDR152RPS2.rpt` / `NFDR152RPS4.rpt` 在 | 同上 |

同理,名單外還有 `NFDR022`(有 3 張 `.rpt`)、`NFDR074`(有 `NFDR074p0` 子視窗)、`NFDR113`(有 `SHORE_ID = '2'`)也都在專案裡。**本片的 44 支是切片,不是「存在的全部」**;寫任何「缺 XXX」之前先 `ls` 一次。

`NFDR152` 的 `.rpt` 只有 `RPS2` 與 `RPS4`,沒有 `RPS1` / `RPS3` — 這種「編號有洞」的情形在 `NFDR107A` 也出現過(§7.4.3),可能是報表格式被砍過。**不在本片範圍,只記一筆待查。**

## 8. 跨模組共用(本片最重的一節)

```text
[圖] NFD 的跨模組依賴：單向只讀、影響面最大的四張表、三種最危險的改動，以及分析為何天生不完整
圖中文字:① 依賴方向：單向，而且只有讀 / ATLAS.OFD（境內分戶軌） / M／I／B 畫面 + 表 / ATLAS.NFD.Report / 127 支全 R，無主專案 / ATLAS.OFD.Report / 40 支（另一篇） / 沒有反向箭頭 / NFD 不被任何人依賴 / ② 改哪些表要回歸 NFD（依受影響支數排序） / OFD303A → 5 支 / 含 4 支日結檢核，不在報表清單上 / OFD081V → 5 支 / view，改底層表查不到誰在用 / BMS001A → 4 支 / 對外文件全靠它 / OFD0811A → 3 支 / INV_AREA 決定境內／海外 / ③ 最危險的三種改動 / INV_AREA 加第三種值或允許 NULL / NFDR076/077 的「海外」組靜默少基金 / OFD221A 改 PK／ALLOT_NO 長度 / NFDR123 取錯「最後一筆申購」，帶錯業務員 / SP 回傳欄位少一欄 / Model.xsd 與 Ctl 的 TransferTable 沒同步 → 該欄永遠空白 / ④ 影響面分析天生不完整 / 15 支可見 / 表名寫在 PO 的 inline SQL 裡 / 29 支不可見 / SQL 在版控外的 SP，repo 內補不完 / 結論：改 OFD 表要另外撈 SP 原始碼 / 否則上線才在報表上爆
```

*圖:圖 5 跨模組依賴（§8）。橘虛框=改動後會靜默出錯的地方；灰虛框=別模組；黑框=查不到的黑箱；橘框=本文結論。「NFD 不被任何人依賴」是好消息；「NFD 依賴所有人而且一半查不到」是壞消息。*

### 8.1 `NFD` 對外的依賴是單向的

`NFD` **只讀不寫**別的模組的表。本片 44 支沒有任何一行 `INSERT` / `UPDATE` / `DELETE` 打在別人的表上——寫入只發生在自己的 `NFDR073T*` 暫存表與 `OCRMTMP`(§2.4)。

| 方向 | 有沒有 | 證據 |
|---|---|---|
| `NFD` → 別模組的表(讀) | **有,而且是全部** | §2.1 的 42 張表 |
| `NFD` → 別模組的表(寫) | **沒有** | PO 內 `INSERT` / `UPDATE` / `DELETE` 的對象只有 `NFDR073T*` / `OCRMTMP` |
| 別模組 → `NFD` 的表 | **沒有** | `NFD` 沒有業務表可被讀 |
| `NFD` → 別模組的程式 | **沒有** | 各層 csproj 的 `ProjectReference` 只指向 `Common/Source/*` 與自己的六層 |

**所以「改 `NFD` 會不會影響別人」的答案是:不會。** 反過來「改別人會不會影響 `NFD`」的答案是:**幾乎一定會,而且看不出來**。

### 8.2 改哪些表要回歸 `NFD`

按「本片有幾支會受影響」排序:

| 表 | 歸屬 | 改它要重測 | 為什麼容易漏 |
|---|---|---|---|
| `OFD303A` | OFD | `NFDR076` `NFDR077` `NFDR107A` `NFDR107B` `NFDR114` | 四支是日結檢核,不是報表本體,不在「報表清單」上 |
| `OFD081V` | OFD(view) | `NFDR073A` `NFDR115` `NFDR154` `NFDR158` `NFDR159` | 它是 **view**,改底層表時 view 定義不在版控,查不到誰在用 |
| `BMS001A` | BMS | `NFDR073A` `NFDR076` `NFDR077` `NFDR123` | 受益人主檔,幾乎所有對外文件都靠它 |
| `OFD0811A` | OFD | `NFDR073A` `NFDR076` `NFDR077` | 基金屬性(`INV_AREA` / `PROF_TYPE2` / `HIGH_RISK_CD`),決定「算不算海外」 |
| `CTL018` / `CTL014` | CTL | `NFDR073` `NFDR101` `NFDR107B` / `NFDR001` | 代碼表,改代碼值會讓報表分類錯而不報錯 |
| `OFD221A` | OFD | `NFDR076` `NFDR123` | 申購檔 |
| `COD009` | COD | `NFDR073B` `NFDR123` | 員工資料,只用來帶姓名 |
| `OFD081A` `OFD002` `OFD017A` `OFD123A` `OFD126` `OFD132A` `OFD251A` `OFD306A` | OFD | 各 1 支 | — |
| `FSK003` | FSK | `NFDR073A` | 風險屬性,對帳單上的警語靠它 |
| `SAL051` | SAL | `NFDR073B` | — |

**以上只涵蓋 15 支**。另外 29 支的相依性在版控外的 SP 裡(§2.1.2),**這份影響面清單天生不完整,而且沒有辦法從 repo 補完**。

### 8.3 最危險的跨模組情境

| 情境 | 後果 | 為什麼沒人會發現 |
|---|---|---|
| `OFD0811A.INV_AREA` 新增第三種值(現在只有 `'D'` / 非 `'D'`) | `NFDR076` / `NFDR077` 的「海外」判斷 `INV_AREA <> 'D'` 會把新值也算成海外 | 確認書照印,數字看起來合理 |
| `OFD0811A.INV_AREA` 允許 NULL | `INV_AREA <> 'D'` 變 UNKNOWN,該基金從海外組**消失** | 同上 |
| 新增基金代碼但忘了同步 `'7A'` / `'7B'` 的排除清單 | `NFDR076` / `NFDR077` 共四處寫死值,改一處漏三處 | 只有比對兩份報表總數才看得出來 |
| `OFD221A` 改 PK 或 `ALLOT_NO` 長度 | `NFDR123` 的 `MAX(ALLOT_DATE \|\| ALLOT_NO)` 排序邏輯失準,取到錯的「最後一筆申購」 | 通路 / 業務員欄位帶錯人,但名單筆數不變 |
| `BMS001A.FREEZE_CD` 語意改變 | `NFDR123` 的 KYC 名單範圍跟著變 | 法遵名單少人 |
| 任何 `OFD*` 表加欄位 | 對 `NFD` **沒影響**(它只 `SELECT` 指名欄位),但若同時改了 SP 的回傳欄位,`Model.xsd` 與 Ctl 的 `TransferTable` 要一起改 | 多回的欄位不會報錯,**少回的欄位會讓報表該欄空白** |

### 8.4 `NFD` 與 `OFD` 兩套報表專案的分工(必答問題 1 的收尾)

| 判準 | 結論 | 依據 |
|---|---|---|
| 是不是第四條業務軌 | **不是**。沒有自己的表、沒有 M/I/B、沒有主專案 | §0.1、§4 |
| 是什麼 | **境內基金軌(`OFD`)的對外文件與法遵 / 營運報表產生器** | `SHORE_ID = '2'`(§7.5.2)、42 張表全屬 `OFD` 與共用模組(§2.1) |
| 為什麼不併進 `ATLAS.OFD.Report` | **repo 內沒有答案。** 可觀察到的差異只有「支數 127 vs 40」與「對外文件 vs 作業清單」 | §0.2,標〔假設〕 |
| 切分維度 | **讀者**(受益人 / 主管機關 / 通路 vs 內部作業),不是業務軌 | 報表中文名,§0.1 |

## 附錄 A. 資料表總表(僅限 PO 內看得見的)

29 支的表名在版控外的 SP 裡,看不到(§2.1.2)。以下 42 個名稱全部來自 15 支 PO 的 inline SQL。

| 名稱 | 歸屬 | 型態 | 被本片幾支用 | 用它的報表 |
|---|---|---|---|---|
| `OFD081V` | OFD | View(推測,尾碼 V) | 5 | `NFDR073A`、`NFDR115`、`NFDR154`、`NFDR158`、`NFDR159` |
| `OFD303A` | OFD | 表 | 5 | `NFDR076`、`NFDR077`、`NFDR107A`、`NFDR107B`、`NFDR114` |
| `BMS001A` | BMS | 表 | 4 | `NFDR073A`、`NFDR076`、`NFDR077`、`NFDR123` |
| `CTL018` | CTL | 表 | 3 | `NFDR073`、`NFDR101`、`NFDR107B` |
| `OFD0811A` | OFD | 表 | 3 | `NFDR073A`、`NFDR076`、`NFDR077` |
| `COD009` | COD | 表 | 2 | `NFDR073B`、`NFDR123` |
| `NFDR073T6` | **NFD 自建** | 暫存 | 2 | `NFDR073`、`NFDR073A` |
| `NFDR073T7` | **NFD 自建** | 暫存 | 2 | `NFDR073`、`NFDR073A` |
| `OFD081A` | OFD | 表 | 2 | `NFDR073A`、`NFDR077` |
| `OFD221A` | OFD | 表 | 2 | `NFDR076`、`NFDR123` |
| `CTL014` | CTL | 表 | 1 | `NFDR001` |
| `FSK003` | FSK | 表 | 1 | `NFDR073A` |
| `F_FORMATSTRINGTOTABLE` | 不明 | Function | 1 | `NFDR114` |
| `MYOFD303A` | 不明 | 同義字(推測) | 1 | `NFDR077` |
| `NFDR073T0` | **NFD 自建** | 暫存 | 1 | `NFDR073` |
| `NFDR073T10` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T11` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T12` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T16` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T17` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T18` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T19` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T24` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T29` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T31` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T33` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T34` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T5` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T8` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T9` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `OCRMTMP` | 不明 | 暫存 | 1 | `NFDR073` |
| `OFD002` | OFD | 表 | 1 | `NFDR073B` |
| `OFD017A` | OFD | 表 | 1 | `NFDR001` |
| `OFD123A` | OFD | 表 | 1 | `NFDR123` |
| `OFD123A_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `OFD126` | OFD | 表 | 1 | `NFDR073` |
| `OFD132A` | OFD | 表 | 1 | `NFDR073A` |
| `OFD221A_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `OFD251A` | OFD | 表 | 1 | `NFDR077` |
| `OFD306A` | OFD | 表 | 1 | `NFDR123` |
| `OFD306_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `SAL051` | SAL | 表 | 1 | `NFDR073B` |

## 附錄 B. SP / Function / Trigger / View

### B.1 SP 總表(60 支,版控內 1 支)

| SP | 呼叫者 | 在版控 | 錨點 |
|---|---|---|---|
| `s_NFDR023_Get` | `NFDR023` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR023_PO.cs:64` |
| `s_NFDR071_Get` | `NFDR071` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR071_PO.cs:55` |
| `s_NFDR072_Get` | `NFDR072` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR072_PO.cs:54` |
| `s_NFDR073_1_Get` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97` |
| `s_NFDR073_ChkRdm` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:492` |
| `s_NFDR073_Get` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97` |
| `s_NFDR103_Get` | `NFDR103` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR103_PO.cs:48` |
| `s_NFDR105_Get` | `NFDR105` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:55` |
| `s_NFDR107B_Get` | `NFDR107B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107B_PO.cs:65` |
| `s_NFDR107B_T2_Get` | `NFDR107B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107B_PO.cs:67` |
| `s_NFDR108_Get` | `NFDR108` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR108_PO.cs:53` |
| `s_NFDR114_Get` | `NFDR114` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:53` |
| `s_NFDR115_Get` | `NFDR115` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:41` |
| `s_NFDR153_Get` | `NFDR153` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR153_PO.cs:51` |
| `s_NFDR154_Get` | `NFDR154` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:42` |
| `s_NFDR155_Get` | `NFDR155` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR155_PO.cs:53` |
| `s_NFDR156_Get` | `NFDR156` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR156_PO.cs:44` |
| `s_NFDR158_Get` | `NFDR158` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR158_PO.cs:41` |
| `s_NFDR159_1_Get` | `NFDR159` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:51` |
| `s_NFDR159_Get` | `NFDR159` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:47` |
| `s_TA_NFDR001_Get` | `NFDR001` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57` |
| `s_TA_NFDR002_Get` | `NFDR002` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR002_PO.cs:59` |
| `s_TA_NFDR003_Get` | `NFDR003` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR003_PO.cs:59` |
| `s_TA_NFDR004_Get` | `NFDR004` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR004_PO.cs:59` |
| `s_TA_NFDR005_Get` | `NFDR005` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR005_PO.cs:60` |
| `s_TA_NFDR006_Get` | `NFDR006` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR006_PO.cs:61` |
| `s_TA_NFDR007_Get` | `NFDR007` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR007_PO.cs:58` |
| `s_TA_NFDR021_Get` | `NFDR021` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR021_PO.cs:58` |
| `S_TA_NFDR024_GET` | `NFDR024` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR024_PO.cs:59` |
| `S_TA_NFDR073B_EMAIL` | `NFDR073B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160` |
| `S_TA_NFDR073B_GET` | `NFDR073B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:76` |
| `S_TA_NFDR073_0_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:119` |
| `S_TA_NFDR073_1_GET` | `NFDR073A` | **是**(`DB/SP/S_TA_NFDR073_1_GET.SQL`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:142` |
| `S_TA_NFDR073_2_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:147` |
| `S_TA_NFDR073_3_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:112` |
| `S_TA_NFDR073_4_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:137` |
| `s_TA_NFDR075_Get` | `NFDR075` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR075_PO.cs:53` |
| `S_TA_NFDR076_GET` | `NFDR076` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:64` |
| `S_TA_NFDR077_GET` | `NFDR077` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:65` |
| `S_TA_NFDR101_GET` | `NFDR101` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR101_PO.cs:72` |
| `S_TA_NFDR102_GET` | `NFDR102` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR102_PO.cs:65` |
| `s_TA_NFDR104_Get` | `NFDR104` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR104_PO.cs:73` |
| `s_TA_NFDR107A_Get` | `NFDR107A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:68` |
| `S_TA_NFDR109_GET` | `NFDR109` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR109_PO.cs:54` |
| `S_TA_NFDR111_GET` | `NFDR111` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR111_PO.cs:58` |
| `S_TA_NFDR120_GET` | `NFDR120` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR120_PO.cs:51` |
| `S_TA_NFDR121_GET_1` | `NFDR121` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR121_PO.cs:57` |
| `S_TA_NFDR121_GET_2` | `NFDR121` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR121_PO.cs:80` |
| `S_TA_NFDR122_GET` | `NFDR122` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR122_PO.cs:59` |
| `S_TA_NFDR150_GET` | `NFDR150` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR150_PO.cs:54` |
| `S_TA_NFDR151_GET` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:74` |
| `S_TA_NFDR151_GET_1` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:81` |
| `S_TA_NFDR151_GET_2` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:87` |
| `S_TA_NFDR151_GET_3` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:93` |
| `S_TA_NFDR151_GET_4` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:116` |
| `S_TA_NFDR151_GET_5` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:111` |
| `S_TA_NFDR151_GET_Charge` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:175` |
| `S_TA_NFDR157_GET` | `NFDR157` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:61` |
| `s_TA_NFDR160_1_Get` | `NFDR160` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR160_PO.cs:74` |
| `s_TA_NFDR160_Get` | `NFDR160` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR160_PO.cs:69` |

### B.2 Function

| 名稱 | 方言 | 用在哪 | 狀態 |
|---|---|---|---|
| `dbo.f_FormatStringToTable` | **MSSQL** | `NFDR114` 的日結檢核 | Oracle 上不存在,見 §7.4.4 |
| `F_TA_GETFUNDNAV` | Oracle | `NFDR123` 取淨值 | 不在版控 |
| `F_TA_STRTODATE` | Oracle | `NFDR123` 字串轉日期 | 不在版控 |
| `F_TA_GETAGENT` | Oracle | `NFDR123` 取通路簡稱 | 不在版控 |

### B.3 Trigger / View

本片未讀到任何 trigger。唯一疑似 view 的是 `OFD081V`(尾碼 `V`,被 4 支當基金清單來源),**定義不在版控**。

## 附錄 C. 代碼對照

| 代碼 | 值 | 意義 | 來源 |
|---|---|---|---|
| `SHORE_ID` | `2` | 境內基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:296` |
| `SHORE_ID` | `1` | 境外基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:300` |
| `OFD0811A.INV_AREA` | `D` / 非 `D` | 境內 / 海外投資區域 | 從 `NFDR076` 的判斷式反推:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:147-150`,**無定義檔可佐證,標假設** |
| `OFD0811A.PROF_TYPE2` | `1` / `2` | 基金屬性(從 `uchkFUND_TYPE1/2/3` 對應推測) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:145-152`,標假設 |
| `OFD303A.POST_CTL_CODE` | `N` | 未過帳 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:154`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:169` |
| `OFD303A.ALLOT_CTL_CODE` | `3` | 被排除的申購狀態(語意不明) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:157`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:138` |
| `OFD251A.REDEM_PROC_CODE` | `3` | 被排除的買回處理狀態 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:339`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:88` |
| `REDEM_CTL_CODE` | `4` | 被排除的買回狀態 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:167` |
| `BF_SORT_CD` | `012` | 被排除的受益人分類 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` |
| `REJ_POST` | `Y` | 拒收紙本 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` |
| `BMS001A.FREEZE_CD` | `N` | 未凍結 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:92` |
| `OFD126.ST_CD` | `03` | 某種狀態(語意不明) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:161` |
| 基金代碼 `7A` / `7B` | — | 被排除的兩檔股票型(海外)基金〔客戶特定〕 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:150` |
| `FUND_ID` `ALL FUNDS` | — | 基金清單的彙總列,`NFDR115` / `NFDR158` 會排除 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:103` |

**除 `SHORE_ID` 外,以上代碼值的意義全部是從判斷式反推的,repo 內沒有對照表可查。**`CTL014` / `CTL018` 是代碼表但內容在資料庫裡,不在版控。

## 附錄 D. 本片 44 支處置表

取代覆蓋率掃描(`--module NFD` 會拿 132 支來比,本片只寫 44 支)。

| # | 代號 | 本文處置 | PO 基底 | 資料來源 | 引用 `.rpt` 數 | `.rpt` 在版控 | 在 csproj | SP 在版控 |
|---|---|---|---|---|---|---|---|---|
| 1 | `NFDR001` | **已深寫** | `INFDR001_PO` | SP+inline | 5 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 2 | `NFDR002` | 表格帶過 | `INFDR002_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 3 | `NFDR003` | 表格帶過 | `INFDR003_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 4 | `NFDR004` | 表格帶過 | `INFDR004_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 5 | `NFDR005` | 表格帶過 | `INFDR005_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 6 | `NFDR006` | 表格帶過 | `INFDR006_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 7 | `NFDR007` | 表格帶過 | `INFDR007_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 8 | `NFDR021` | 表格帶過 | `INFDR021_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 9 | `NFDR023` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 10 | `NFDR024` | 表格帶過 | `INFDR024_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 11 | `NFDR071` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 12 | `NFDR072` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 13 | `NFDR073` | **已深寫** | **`Basic_PO`** | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/3 在 |
| 14 | `NFDR073A` | **已深寫** | `INFDR073A_PO` | SP+inline | 0 | —(非 Crystal) | UI+Ctl+PO 全在 | **1/5 在** |
| 15 | `NFDR073B` | **已深寫** | `INFDR073B_PO` | SP+inline | 4 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 16 | `NFDR075` | 表格帶過 | `INFDR075_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 17 | `NFDR076` | **已深寫** | `INFDR076_PO` | SP+inline | 5 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 18 | `NFDR077` | **已深寫** | `INFDR077_PO` | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 19 | `NFDR101` | 表格帶過 | `INFDR101_PO` | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 20 | `NFDR102` | 表格帶過 | `INFDR102_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 21 | `NFDR103` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 22 | `NFDR104` | 表格帶過 | `INFDR104_PO` | SP | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 23 | `NFDR105` | **已深寫** | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 24 | `NFDR107A` | **已深寫** | `INFDR107A_PO` | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 25 | `NFDR107B` | **已深寫** | **`Basic_PO`** | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 26 | `NFDR108` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 27 | `NFDR109` | 表格帶過 | `INFDR109_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 28 | `NFDR111` | 表格帶過 | `INFDR111_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 29 | `NFDR114` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 30 | `NFDR115` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 31 | `NFDR120` | 表格帶過 | `INFDR120_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 32 | `NFDR121` | 表格帶過 | `INFDR121_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 33 | `NFDR122` | 表格帶過 | `INFDR122_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 34 | `NFDR123` | **已深寫** | `INFDR123_PO` | 純 inline | 0 | —(非 Crystal) | UI+Ctl+PO 全在 | — |
| 35 | `NFDR150` | 表格帶過 | `INFDR150_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 36 | `NFDR151` | **已深寫** | `INFDR151_PO` | SP | 4 | 全在 | UI+Ctl+PO 全在 | 0/7 在 |
| 37 | `NFDR153` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 38 | `NFDR154` | **已深寫** | **`Basic_PO`** | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 39 | `NFDR155` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 40 | `NFDR156` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 41 | `NFDR157` | **已深寫** | `INFDR157_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 42 | `NFDR158` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 43 | `NFDR159` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 44 | `NFDR160` | 表格帶過 | `INFDR160_PO` | SP | 4 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |

統計:**深寫 17 支、表格帶過 27 支**;`.rpt` **0 支不在版控**、**0 支不在 csproj**;SP **59/60 不在版控**;PO 未遷移(`Basic_PO`)**16 支**。

## 附錄 E. 讀本文時要注意的地方(缺陷與陷阱)

嚴重度:**高**=會產生錯誤的對外文件或法遵報表 / **中**=功能不可用或維護時必踩 / **低**=整潔性。

### E-01 60 支 SP 只有 1 支在版控 —— 嚴重度 **高**

**缺陷**:44 支報表點名 60 個 stored procedure,比對 `atlas_index.json` 的 83 支,只有 `S_TA_NFDR073_1_GET` 在 `DB/SP/`。

**影響**:29 支報表(66%)**讀哪些表完全查不出來**(§2.1.2)。做任何 `OFD*` 表的異動分析時,`NFD` 這 29 支是黑洞——影響面評估天生不完整,而且沒有辦法從 repo 補完。改表上線後才在報表上爆,是這個模組最可能的故障模式。

**錨點**:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57`(代表)、附錄 B.1 全表。

### E-02 16 支的 `m_db` 永遠是 `null`,一呼叫就 NRE —— 嚴重度 **高**

**缺陷**:繼承 `Basic_PO` 的 16 支,每支都在自己類別裡宣告 `private Database m_db = null;`,而建構子裡唯一的指派被註解掉:

```
private Database m_db = null;

public NFDR115_PO()
{
    //SystemConfigurationSource config = new SystemConfigurationSource();
    //DatabaseProviderFactory provider = new DatabaseProviderFactory(config);
    //m_db = provider.Create("TA");
}
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:18-25`

下一個方法第一行就是 `DbConnection Dbcon = m_db.CreateConnection();`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:34`)。

**為什麼不是誤判**:

1. `Basic_PO` 在 `Vendor.Product.DataAccess` DLL 裡(**無原始碼,從呼叫端反推**),就算它有自己的 `m_db`,子類別重新宣告的同名 private 欄位會**遮蔽**基底的;子類別內所有 `m_db` 都指到自己那個 `null`。

2. 對照組:已遷移的 28 支寫的是 `private Database m_db = new Database("TA", DbServerType.Oracle);`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:25`),**宣告時就給值**。

3. 這 16 支的 Ctl 是直接 `new NFDR115_PO()`(`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR115_Ctl.cs:34`),不走 `DataAccessPool` / `GetDaoInstance<T>`,**沒有任何機會被 Oracle 版替換掉**。

**三支例外**:`NFDR073` 用 `private readonly Database m_db;`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:21`)、`NFDR108` / `NFDR155` 用 `private Database m_db;`——**沒有初始值,也沒有指派**,結果一樣是 `null`,只是編譯器警告不同。

**受影響的 16 支**:`NFDR023` `NFDR071` `NFDR072` `NFDR073` `NFDR103` `NFDR105` `NFDR107B` `NFDR108` `NFDR114` `NFDR115` `NFDR153` `NFDR154` `NFDR155` `NFDR156` `NFDR158` `NFDR159`。

**影響**:這 16 支在 Oracle 環境下**一按預覽就 `NullReferenceException`**。其中 `NFDR073`(投資對帳單)是對外文件、`NFDR154`(贖回交易確認單)也是。

**注意這是讀碼推論**,沒有在執行環境驗證過。可能的反面解釋只有一個:`Basic_PO` 的建構子用反射或其他方式塞值進子類別的 private 欄位——極不可能,但 DLL 無原始碼,無法排除。**動手修之前先在測試環境按一次**。

### E-03 `NFDR073A` 的 `dataID` 截斷到 22 碼 —— 嚴重度 **高**

**缺陷**:`m_db.AddInParameter(Cmd1, "striDATAID", OracleDbType.Varchar2, strDATAID.Substring(0, 22).Trim());`

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102`

**影響**:17 張 `NFDR073T*` 暫存表全部以 `DATAID` 分租。兩個使用者同時產對帳單、`DATAID` 前 22 碼相同時,**兩份對帳單的資料會互相污染**——甲的持股印到乙的對帳單上。另外 `strDATAID` 若短於 22 碼直接丟 `ArgumentOutOfRangeException`。

### E-04 `INNER JOIN` 讓法遵名單無聲少人 —— 嚴重度 **高**

| 位置 | JOIN | 少掉誰 |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:89` | `JOIN OFD221A_TMP T3 ON T1.BF_NO = T3.BF_NO` | **從來沒有申購紀錄**(例如持股全來自轉申購)的受益人,從 KYC 到期名單上消失 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:87` | `JOIN BMS001A` | 受益人主檔缺這筆時消失 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:143` | `FROM OFD303A JOIN OFD0811A ON OFD303A.FUND_ID = OFD0811A.FUND_ID` | **日結檢核**:`OFD0811A` 對不到的基金,未日結資料查不出來,檢核直接放行 |

第三條最惡劣:**報表少印使用者還有機會發現,檢核漏掉是完全無聲的**。

### E-05 30 支沒有任何「查無資料」提示 —— 嚴重度 **中**

44 支裡只有 14 支的 UI 有「無符合查詢條件的資料 / 查無資料」之類的訊息。其餘 30 支在 SP 回空集合時,直接開一張**只有表頭的 Crystal 報表**。

使用者分不出「真的沒有」與「條件打錯 / SP 掛了」。對 `NFDR004`(員工及其關係人買賣月報)這種法遵報表,「空的」與「沒跑到」的差別很重要。

**有訊息的 14 支**:`NFDR001` `NFDR073` `NFDR073B` `NFDR075` `NFDR076` `NFDR077` `NFDR101` `NFDR102` `NFDR105` `NFDR114` `NFDR115` `NFDR122` `NFDR123` `NFDR151`(部分只有 `Rows.Count == 0` 判斷而無訊息文字)。

**更糟的是 `NFDR151` / `NFDR159` / `NFDR105`**:有判斷、有 `AddResultRow(false, 0, "")`,但**訊息是空字串**——UI 拿到 `ReturnCode = false` 卻沒有話可講(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:169`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:130`)。

### E-06 Oracle 三值邏輯:`<> '值'` 遇 NULL 靜默排除 —— 嚴重度 **中**

13 處 `<> '…'`,只有一處用 `NVL` 包起來:

| 錨點 | 條件 | 有沒有防 NULL |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` | `NVL(REJ_POST,' ')<>'Y'` | **有** |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` | `BF_SORT_CD <> '012'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:148` | `OFD0811A.INV_AREA <> 'D'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:155` | `OFD303A.ALLOT_CTL_CODE <> '3'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:167` | `A.REDEM_CTL_CODE <> '4'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:339` | `OFD251A.REDEM_PROC_CODE<>'3'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:103` | `OFD081V.FUND_ID <> 'ALL FUNDS'` | 沒有(`FUND_ID` 應為 NOT NULL,風險低) |

另有 4 處 `NOT IN ('7A','7B')`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:150,240`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:177,352`)——`FUND_ID` 為 NULL 時整條 UNKNOWN。

**同一個作者在同一行裡一個包 `NVL` 一個不包**(`NFDR073A_PO.cs:195`),說明這不是「不知道」,是「漏掉」。

### E-07 `CustomTransferOracleModelToView` 是逐張手抄 —— 嚴重度 **中**

```
TransferVDBHelper.TransferTable(view.UIView.NFDR001, model.DataEntity.NFDR001, base.TransferEVAColumn);
TransferVDBHelper.TransferTable(view.UIView.NFDR001_Detail, model.DataEntity.NFDR001_Detail, base.TransferEVAColumn);
TransferVDBHelper.TransferTable(view.UIView.NFDR001_Grid, model.DataEntity.NFDR001_Grid, base.TransferEVAColumn);
```

`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:92-94`

**SP 多回一張表、或 `Model.xsd` 加了一張表而 Ctl 忘了加一行,該張表在報表上永遠空白,不會報錯。** 改報表欄位時,`Model.xsd` / `View.xsd` / Ctl 的 `TransferTable` / `.rpt` 四者要同步,少一個就是「欄位與 xsd 不同步」。

### E-08 MSSQL 語法殘留在 Oracle 連線上 —— 嚴重度 **中**

除了 E-02 的 16 支整體未遷移之外,還有幾處具體的方言殘留:

| 錨點 | 殘留 |
|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385` | `DELETE …; DELETE …` 一行兩個 statement + `@dataID` |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:539` | `IF EXISTS(…) SELECT 1 ELSE SELECT 0` —— 純 T-SQL |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:139` | `dbo.f_FormatStringToTable(@FUND_ID)` |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:98` | `LEFT JOIN [OFD038]` —— 中括號識別字 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180` | `[OFD006]` + 字串串接 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:160` | `FROM [OFD126]` |
| 上述各支的 `AddInParameter` | `SqlDbType.NVarChar` / `SqlDbType.DateTime` 而非 `OracleDbType` |

### E-09 `NFDR114` 的日結檢核 SQL 少一個空白 —— 嚴重度 **中**

```
strSQL += "   AND FUND_ID IN (SELECT * FROM dbo.f_FormatStringToTable(@FUND_ID))";
strSQL += "GROUP BY FUND_ID";
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:139-140`

接出來是 `…(@FUND_ID))GROUP BY FUND_ID`,語法錯誤。再加上 `GROUP BY` 配 `ExecuteScalar` 只會拿到第一組的筆數。**三個錯疊在一起,而且因為 E-02 根本執行不到。**

### E-10 字串串接進 SQL —— 嚴重度 **中**(現況不可觸發)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180,185`:欄位名與值都直接串。值連單引號跳脫都沒有。目前因 E-02 執行不到,**但遷移這支時必須先改寫成 bind 變數**。

### E-11 日結檢核例外時 `return -1` —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:186`:`check()` 在 `catch` 之後 `return -1`。呼叫端若以 `> 0` 判斷「有未日結」,**查詢失敗會被當成「都日結了」而放行**——fail-open。

### E-12 `catch` 內 `tran.Rollback()` 可能自己 NRE —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:193-199`:`catch (OracleException) { … tran.Rollback(); }`。`tran` 在 `try` 中段才 `BeginTransaction`,若之前就拋例外,`tran` 是 `null`,**`Rollback()` 自己 NRE,把原始錯誤蓋掉**。

### E-13 成對報表的條件各有複本 —— 嚴重度 **中**

`NFDR076` / `NFDR077` 的「基金類型 + 排除 `'7A'` `'7B'`」條件**一共有四份複本**:

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:145-152`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:235-242`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:172-179`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:347-354`

改一處漏三處,結果是**申購確認書與買回轉申購確認書的基金範圍不一致**,對帳時才會發現。

### E-14 四份 `GetFUND` 複本,四種基金清單 —— 嚴重度 **中**

見 §7.5.3。`NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` 的基金下拉清單各自演化:兩支排除 `'ALL FUNDS'`、一支限境內、參數名一支叫 `@FUND_GRPCD` 另三支叫 `@FUND_GROUP`。`NFDR154` 的 `WHERE` 還少一層外層括號(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:103-105`)——目前無害,加一條 `AND` 就會出事。

### E-15 `NFDR001` 的選項落在列舉外就什麼都不做 —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131` 是 4×2 的 `if / else if` 巢狀,**沒有 `else`**。`uoptOrder` / `uoptPurpose` 的值只要不在列舉內,`SetQueryParameters` 一次都不會被呼叫,報表類別是空的。同一支的 `ReportLoad`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:64-68`)只在特定組合下 `SetParameterValue("Purpose", …)`,其他組合 Crystal 沿用上一次的值。

`NFDR151` 的 Excel 分派也一樣(`switch` 無 `default`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:105-118`)。

### E-16 `.rpt` 一對多共用 —— 嚴重度 **中**

`NFDR001` 的 8 種選項組合對應 5 張 `.rpt`,`NFDR001RPS` 被三種排序共用、`NFDR001RPS1` 被兩種共用(§7.1.1 的對照表)。**改一張 `.rpt` 會同時影響多個選項組合**,而 UI 上看起來是不同的功能。

### E-17 恆真條件關掉整段篩選 —— 嚴重度 **低**(但極易誤刪)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:152`:

```
OR (:striFUND_ID IS NOT NULL AND :striFUND_ID=:striFUND_ID)
```

指定基金代碼時整段「基金類型」篩選失效。可能是刻意的(指定基金就不看類型),但寫成恆真式而非註解,**下一個維護者會當成 bug 刪掉,刪掉之後行為就變了**。

### E-18 非 UTF-8 來源檔 —— 嚴重度 **低**

9 個檔是 **cp950**(Big5),中文註解在 UTF-8 工具下是亂碼:

`NFDR107A` 的 Ctl / Pxy / PO、`NFDR107B` 的 Ctl / Pxy / PO、`NFDR108` 的 Ctl / Pxy / PO。

例:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:157` 的區段標題在 UTF-8 下讀作亂碼。其餘 123 個檔是 `utf-8-sig`。

### E-19 SP 命名兩套並存 —— 嚴重度 **低**

`s_TA_NFDRxxx_Get` 與 `s_NFDRxxx_Get` 兩套命名並存且沒有規則(§2.2);大小寫也混(`S_TA_NFDR024_GET` vs `s_TA_NFDR001_Get`)。Oracle 不分大小寫所以跑得動,但**任何依名字比對的工具都會漏**。

`NFDR073A` 用的是 `S_TA_NFDR073_x_GET`(名字裡沒有 `A`),**照代號推 SP 名一定推錯**。

### E-20 `CommandTimeout = 0` 遍布全片 —— 嚴重度 **低**

幾乎每支 PO 都有 `Cmd.CommandTimeout = 0; //此程式讓它永久跑`(例 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56`)。SP 卡住時 client 無限等待,使用者只能砍行程。

### E-21 寫死常數 —— 嚴重度 **低**

| 值 | 位置 | 應該用 |
|---|---|---|
| `'2'`(境內) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:107` | `CTL014.SHORE_ID.OnShore` |
| `'7A'` `'7B'` | `NFDR076` / `NFDR077` 四處 | 設定或代碼表 |
| `受益人KYC到期名單.xlsx` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` | 帶日期 / 條件 |
| `貴 賓 理 財 對 帳 單` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123,134,145,157` 四處 | 常數(對照 `NFDR073` 的 `const string ReportName`) |

### E-22 沒有任何 `.rpt` 或 csproj 問題 —— **本片的好消息**

前幾篇踩過的「`.rpt` 不在版控」「檔案存在但不在 csproj」「六層檔名少一個字母」,**本片 44 支一件都沒有**(§2.3)。79 張 `.rpt` 全在版控且全在 `Report.NFD.csproj`;UI / Ctl / PO 三層 132 個檔全在各自 csproj;六層全齊。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `ATLAS.NFD.Report` 前 44 支(`NFDR001`–`NFDR160`)。 |

由 build_doc.py v2.0.0 於 2026-09-15 21:01 產生 · 標題 99 · 圖 5 · 表格 63 · 程式錨點 280 · § 連結 60 · 引用檢查：畫面 53（缺 0） · Table 12（缺 0） · SP 1（缺 0） · Report 14（缺 0） · 結果集 14（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
