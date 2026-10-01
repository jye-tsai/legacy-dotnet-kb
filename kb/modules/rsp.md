<!-- 由 tools/build_copilot_kb.py 從 modules/rsp.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS RSP 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、§6.3(`RSPB008_Service`)、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、Designer 內的標籤文字與訊息字串**推測**,待選單表 / 對照表回填。畫面中文名不在版控內,本文的畫面名稱一律標「推測」。 ⚠ **〔客戶特定〕**:落地路徑 `C://Vendor//WindowService//RSPB008//`、郵件群組 `OFD681.SEND_TYPE = '6'`、員工註記 `EMP_CD = '1'`、扣款轉申購日固定 6 / 16 / 26 日、郵局總行代碼 `700`、促銷活動 `86A03` 為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`COD009`(主檔在 COD)、`RSP006A`(BMS / OFD 也讀)、`OFD272A`(BMS / OFD 也掛)、`OFD374A`(主檔在 DSM)四組表跨界,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、SQL 與 Oracle 現況看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、WindowsService 看 `architecture.md §8`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:RSP 管「定期定額」這種契約的一生——客戶簽了約要每個月自動從銀行扣款買基金,這條線從立約、變更、每期扣款、核印、單位數計算,一路到停利出場與契約終止,全部在這個模組裡。**

「RSP」三個字母在 repo 內找不到定義,**不要猜**。但主表 `RSP005A` 的主鍵欄位 `RSP_NO` 的 `msdata:Caption` 就是「契約書號」,明細 `RSP006A` 有「扣款金額」「扣款日1/2/3」「契約手續費率」,批次畫面的標籤是「契約扣款日期」「實際扣款日期」。推測依據如下表,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `RSP_NO`=「契約書號」、`RSP_AMT`=「扣款金額」、`RSP_ALLOT_DAYS1`=「扣款日1」、`SER_FAIL_TIMES`=「連續扣款失敗次數」、`FIRST_SUS_DATE`=「首次扣款成功日期」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:28`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:35` |
| 變更檔的前後對照欄 | `RSP007A` / `RSP013A` 整張表就是 `BEF_xxx` / `AFT_xxx` 成對,例如「變更前扣款行」「變更後扣款行」「變更前扣款金額」「變更後扣款金額」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:189`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:584` |
| 批次訊息字串 | 「執行完成 本次有更新失敗資料,請執行(RSPR038)定期定額契約異動資料查核表」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:104` |
| 批次訊息字串 | 「此契約扣款日期已執行過168循環定額投資扣款轉申購產生作業」「此契約扣款日期已執行過定期定額投資停利計算作業」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:249`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:212` |
| 母子基金欄位名 | `RSP061A` 是「母子基金設定書號」「最低申購金額」「最低轉申購金額」,`RSP062A` 是「母基金代碼」,`RSP063A` 是「子基金代碼」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:93`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:183` |
| 停利欄位名 | `RSP041A` 是「停利轉申購契約書號」「約定停利點」「停利機制」「轉申購手續費率」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17` |
| 服務落地檔 | `C://Vendor//WindowService//RSPB008//RSPB008_yyyyMMdd.txt`,內容寫「處理資料筆數」 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:145` |

本文一律用「定期定額」描述它的範圍,這是從上表推出來的,**不是官方名稱**。

五條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 一般定期定額契約 | 客戶簽約買哪幾檔基金、每檔扣多少、每月哪幾天扣、手續費率與促銷優惠;之後所有變更(換銀行、改金額、暫停、終止)走變更書 | `RSPM004` `RSPB020` `RSPM005` `RSPB008` | `RSP005A`+`RSP006A`(契約)、`RSP007A`+`RSP013A`(變更) |
| B 每期扣款作業 | 產生扣款檔 → 送印鑑核印 → 銀行回覆成功 / 失敗 → 算單位數 → 結轉 → 出錯時淨值回復 → 連續失敗就終止契約 | `RSPB009` `RSPB010` `RSPB011` `RSPB015` `RSPB016` `RSPB018` `RSPB019` `RSPB052` | `RSP008`、`RSP008A`、`RSP008AA`、`CTL006A` |
| C 168 循環定額投資(母子基金) | 先設定哪些母基金可配哪些子基金,再簽 168 契約,每月 6 / 16 / 26 日把母基金贖回轉申購子基金,達停利點就出場 | `RSPM020` `RSPM021` `RSPB025` `RSPM022` `RSPB023` `RSPB021` `RSPB022` `RSPB024` | `RSP061A`/`RSP062A`/`RSP063A`、`RSP070A`/`RSP071A`/`RSP072A`、`RSP073A`/`RSP074A`/`RSP075A` |
| D 定期定額停利轉申購 | 幫既有定期定額契約掛一個「漲到幾成就自動贖回轉申購另一檔」的設定,變更走另一張書號 | `RSPM041` `RSPM042` `RSPB041` `RSPB042` | `RSP041A`、`RSP042A` |
| E 員工 / 員眷契約費率 | 員工離職後,把他與眷屬名下定期定額契約的手續費率改回一般費率 | `RSPM037` | 讀 `COD009`+`COD010`+`BMS001`,只寫 `RSP006` 的 `RSP_CNRT_FEE_RATE` |

另外 31 支 R 報表 / 39 個 `.rpt` 掛在這五條線上(§7)。

### 0.2 這模組最反直覺的六件事

**(1) 17 支「B」畫面裡有兩支根本不是批次,是維護畫面。**

| 畫面 | 基底類別 | 實際行為 |
|---|---|---|
| `RSPB020` | `xMaintainForm` | 跟 `RSPM004` 共用同一組 `RSPM004_Master` / `RSPM004_Detail`,走完整四眼;用來改契約的業務欄位(銷售機構 / 通路 / 推薦人 / 員工 / 介紹人 / 郵局經辦區),存檔時連動更新 `OFD220A` `OFD221A` `OFD306A` |
| `RSPB025` | `xMaintainForm` | 跟 `RSPM021` 共用 `RSPM070_Master` / `RSPM070_Detail`,同樣走四眼 |

錨點:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:23`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB025.cs:24`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:554-610`。其餘 15 支都是 `xOneStepProcessForm`(例:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB009.cs:15`)。**看到 B 就當批次會踩雷**,`architecture.md §6.4` 講的「B 跟 I 是同一份程式碼」在這兩支不成立。

**(2) `RSPM037` 掛的主檔是 `COD009`(員工主檔),但它一個字都沒寫進去。**

`RSPM037_PO` 的 `MasterTable` 在三個方法裡被換三次:`COD009` → `RSP005` → `RSP006`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250`)。`COD009` 只是查詢驅動——輸入「離職日期(起 / 迄)」或「離職員工代碼」,撈出離職員工與其員眷,再帶出他們名下的定期定額契約。**唯一的寫入是 `UPDATE RSP006 SET RSP_CNRT_FEE_RATE`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:271-276`)。掃描母體把它列成「`COD009` 主檔於 `RSPM037`」是照 `MasterTable` 宣告推的,與實際行為不符,詳見 §4.6 與 §8.1。

**(3) `RSPM037` 是整個模組唯一沒有移轉到 Oracle 的畫面。**

同一支 PO 內同時出現 `ISNULL(...)`、`CONVERT(NVARCHAR, x, 111)`、`GetDate()`、方括號識別字、`f_GetAgent()`、`SqlDbType.NVarChar`,而且查的是**沒有 A 尾碼的舊表名** `RSP005` / `RSP006` / `BMS001` / `OFD019` / `OFD071` / `OFD072` / `OFD081` / `OFD199`。其餘 24 支 PO 全是 `[PODbType(DbServerType.Oracle)]` + `OracleDbType` + `NVL`。錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:64`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:152`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:279`。對照 `architecture.md §4.6`(執行期是 Oracle-only)。**假設**:這支畫面在 Oracle 上跑不起來。依據是上述語法在 Oracle 皆非法、且 `RSP005` / `RSP006` 不在本模組任何其他程式的表名清單裡(其他 24 支一律用 `RSP005A` / `RSP006A`)。無法實測,不敢斷言。

**(4) `RSPB008` 有專屬 WindowsService,而且它不是 Remoting 客戶端。**

`architecture.md §8.4` 說四支服務「都是 Remoting 的客戶端,一樣透過 `_Pxy` 打到伺服端,不直接碰資料庫」。**`RSPB008_Service` 不是。** 它直接 `new RSPB008_Ctl()`(Control 層),csproj 參考的是 `Control.RSP` 而不是 `FormProxy.RSP`,全專案 `RemotingConfiguration` 出現 0 次,而它的 `App.config` 自帶五組 `connectionStrings`。錨點:`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:47`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/WindowsService.RSPB008.csproj:116-119`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:72-78`。對照組 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:82`(有 `RemotingConfiguration.Configure`,用 `OFDB600_Pxy`)。詳見 §6.3。

**(5) 同一顆「執行」按鈕,畫面按下去會先擋「還有沒覆核的資料」,服務排程跑則不會。**

`RSPB008` 的 UI 在 `BeforeExecuteButtonClicked` 會先呼叫 `CheckStatus`,有未覆核資料就進 `ValidateErrList` 擋下(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:34-53`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:105-115`)。`RSPB008_Service` 的 `_timer_Elapsed` **直接呼叫 `ctl.Execute(view)`,沒有任何 `CheckStatus`**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:40-73`)。同一條卡控在兩條入口只有一條掛著。

**(6) 「執行成功 / 失敗」的判斷散成四種寫法。**

| 寫法 | 誰 | 錨點 |
|---|---|---|
| SP 的 `MSG` OUT 參數為 NULL 才算成功 | `RSPB021` `RSPB022` `RSPB023` `RSPB041` `RSPB042` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:73-83` |
| 讀 RefCursor 第一列的 `UpdateTimes` / `CORRECT` 欄 | `RSPB008` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:85-110` |
| `ExecuteNonQuery` 的回傳筆數 | `RSPB011` `RSPB015` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:176-190` |
| **硬把回傳筆數蓋成 1,失敗分支永遠不會走** | `RSPM037` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-284` |

最後一條是真缺陷,見附錄 E。

### 0.3 不管什麼

以下**不在** RSP 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料的正規維護 | BMS | `BMS001` 在 RSP 只有一處寫入,而且限定「簡易開戶」情境;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:632-809` |
| 員工主檔、員眷、離職日 | COD | `COD009` / `COD010` 只被 `RSPM037` join,零寫入;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:92-111` |
| 基金主檔、淨值、幣別小數位 | OFD | `OFD081` / `OFD081V` 只讀;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:230-233` |
| 銷售機構 / 通路 / 推薦人主檔 | OFD | `f_GetAgent()` / `OFD071` / `OFD072` 只讀;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:181-190` |
| 結帳與關帳控制 | OFD | `OFD303A` 只用來判斷「買回 / 申購關帳是否已結轉」;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119-130` |
| 銀行 / 總行對照與郵局限額 | OFD | `OFD019.DAY_LMT_AMT` 的檢核整段被註解掉,改寫在 SP 裡;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286` |
| 印鑑核印的實際往返 | OFD | `OFD701` 在 RSP 只被讀 / 被判狀態;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| 受益人歸屬業務員的正規維護 | DSM | `OFD374A` 的維護入口在 `DSMM060`(`dsm.md §8`);RSP 只在簡易開戶時補寫一筆,見 §8.4 |
| 缺件主檔的正規維護 | OFD / BMS | `OFD272A` 在 RSP 是掛在契約底下的明細;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80` |
| **每期扣款的錢怎麼算出來的** | **版控外的 SP** | 13 支 B 畫面全部只負責呼叫 SP,算式在 DB 裡;例 `s_TA_RSPB008_Excute_M`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:65`)、`S_TA_RSPB021_EXCUTE`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:54`) |
| 郵件實際寄送 | 共用 `GenXMLHelper` | `email.Gen49(...)` 只負責產 XML 丟出去;`Dev/ATLAS.RSP/Source/Control/Control.RSP/RSPB008_Ctl.cs:239-240` |

掃描母體列的 SP / Function / Trigger / View 全部是 0 筆——**不是沒有,是全部不在版控內**(附錄 B)。

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 櫃檯 / 作業人員 | 收到契約書輸入 `RSPM004`;客戶要改就開 `RSPM005`;168 開 `RSPM021`、停利開 `RSPM041` | 四支都是標準 `xMaintainForm`,權限在程式內看不到 |
| 覆核人員 | 四眼的 V / A 兩段;`RSP007A` `RSP073A` `RSP042A` 三張變更檔沒覆核完,對應批次就不給跑 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:109-112`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:108-111` |
| 每日作業排程人員 | 依序跑 `RSPB009` → `RSPB010` → `RSPB011` / `RSPB015` → `RSPB016` → `RSPB018`;出錯跑 `RSPB019` 回復 | 訊息字串直接寫出順序:「執行成功!請先從(RSPB016)計算作業開始;如有淨值變動,請先執行淨值回復作業!」`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:92` |
| 排程本身(無人值守) | `RSPB008_Service` 每 60 秒比對一次 `CTL016.RSP_PROC_TIME`,到點就用 `UserID = "AutoJob"` 跑一次契約變更生效 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:42`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:52` |
| 人事 / 作業窗口 | 員工離職後開 `RSPM037` 調整其名下契約手續費率 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:74-114`,查詢條件只有「離職日期起迄」與「離職員工代碼」 |
| 通知信收件人 | `OFD681` 裡 `SEND_TYPE = '6'` 那群人,`RSPB008` 服務每次跑完都寄 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:343-344` |

**本模組所有畫面的功能權限都不在程式碼裡**,由 PTPF 平台庫決定(`architecture.md §3.7`)。報表端也沒有任何白名單或員編寫死的權限判斷(§7.3)。

### 0.5 全域開關

| 開關 | 放哪裡 | 影響 | 錨點 |
|---|---|---|---|
| `formstyle = OneStep` | `UI.RSP/App.config` | 15 支 B 畫面宣告成一步式;`RSPB020` / `RSPB025` / 8 支 M 不宣告 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:35`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:85-92` |
| `mastertable` + `pkey` | `UI.RSP/App.config` | 宣告每支維護畫面的主檔 DataTable 與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:150`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:158`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:166`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:185`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:199`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:207` |
| `ugrdResult` 的 `column` 白名單 | `UI.RSP/App.config` | 查詢結果 grid 顯示哪些欄位 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:152`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:178`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:186` |
| `AUTO_BELONG_EMP` | 系統參數表(`ServerBizUtility.GetSysParam()`) | `= 'Y'` 才會在簡易開戶時補寫 `OFD374A`;`= 'N'` 就不寫。**這是 RSP 碰 DSM 主檔的唯一開關** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-698` |
| `CTL016.RSP_PROC_TIME` | 資料庫 | `RSPB008_Service` 的排程時刻(`HHmm`);取 `rownum = 1`,**全表只認第一列** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302` |
| `CTL014` 預設值 8 組 | 資料庫 | 簡易開戶時 `TRAN_FAX_CD`(081)、`OMNIBUS_ID`(065)、`JOINT_ACC_CD`(066)、`PD_CODE`(069)、`PP_CODE`(070)、`BF_WEB_CD`(078)、`TRAN_PAY_WAY`(079)、`REJ_POST`(083)的來源 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684` |
| `ProductId.TaOfd` / `ProductId.TaNfd` | 授權設定 | 有沒有建置境外 / 境內基金事務系統,決定簡易開戶帶哪組國別碼 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:649-671` |
| 服務落地路徑 | **寫死在程式裡** | `C://Vendor//WindowService//RSPB008//`,不是設定檔 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114`〔客戶特定〕 |
| 服務 timer 間隔 | **寫死在建構子** | `60000` 毫秒 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:25` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] RSP 模組全景：一般契約、扣款作業、168 循環定額、停利轉申購、員工費率與報表五條線
圖中文字:① 一般定期定額契約：立約 → 變更 → 生效 / RSPM004 / 契約 RSP005A/RSP006A / RSPM005 / 變更書 RSP007A/RSP013A / RSPB008 / 變更生效 SP / RSPB008_Service / 排程 CTL016 / RSPB020 / 只改業務欄位 四眼 / ② 每期扣款作業：八支批次串成一條鏈 / RSPB009 / 產生扣款 RSP008 / RSPB010 / 送件 指定淨值日 / RSPB011 RSPB015 / 扣款回覆確認 / RSPB016 RSPB018 / 單位數計算 結轉 / RSPB019 / 淨值回復 RSP008AA / RSPB052 / 連續失敗終止契約 / ③ 168 循環定額投資：母基金贖回轉申購子基金 / RSPM020 / 母子基金白名單 / RSPM021 RSPB025 / 契約 RSP070A-072A / RSPM022 RSPB023 / 變更 RSP073A-075A / RSPB021 B022 B024 / 轉申購 停利 寄信 / ④ 定期定額停利轉申購 / RSPM041 / 停利設定 RSP041A / RSPM042 / 停利變更 RSP042A / RSPB041 / 變更生效 / RSPB042 / 停利計算 LOG109A / ⑤ 員工契約費率 + 報表 / RSPM037 / 離職員工 只改費率 / COD009 COD010 / 員工與員眷 唯讀 / RSPR008 ~ RSPR071 / 31 支 全走版控外 SP / 39 個 rpt 全對得上 / 另一支只出 Excel
```

*圖:圖 1 RSP 全景。橘框=維護入口或關鍵批次;白框=一般批次;橘虛框=含寫死值或未移轉 Oracle〔客戶特定〕;黑框=唯讀或無原始碼。五條線之間幾乎沒有程式呼叫,全靠表相連——① 的 RSP005A/RSP006A 是 ②④⑤ 的共同地基。*

五條線之間幾乎沒有程式呼叫,全靠表相連。線 A 的 `RSP005A` / `RSP006A` 是所有東西的地基:線 B 的扣款檔從它產、線 D 的停利契約用 `RSP_NO` 掛在它身上、線 E 改的是它的明細費率。線 C(168)自成一套表,跟線 A 只透過 `BF_NO` 與基金代碼相關。

### 1.2 資料表關係

21 張表分成六組,主明細配對與主鍵組成見 §2.1 / §2.2。要先記住三件事:

1. **三組「主檔 + 變更檔」是平行結構**:`RSP005A`+`RSP006A`(契約)對 `RSP007A`+`RSP013A`(變更);`RSP070A`+`RSP071A`+`RSP072A`(168 契約)對 `RSP073A`+`RSP074A`+`RSP075A`(168 變更);`RSP041A`(停利)對 `RSP042A`(停利變更)。變更檔一律是 `BEF_xxx` / `AFT_xxx` 成對欄位,**變更當下不動主檔**,要等對應批次跑過才生效。

2. **扣款那組(`RSP008` / `RSP008A` / `RSP008AA`)不是主明細關係**,是同一批扣款資料在不同階段的三張表,而且沒有任何一支 M 畫面維護它們。

3. **`RSP061A` / `RSP062A` / `RSP063A` 是設定檔不是交易檔**,一張 `RE_RSP_NO`(母子基金設定書號)底下掛 N 個母基金與 N 個子基金,是多對多的白名單。

### 1.3 主要維護畫面的四眼與卡控順序

八支 M 畫面(加上偽裝成 B 的 `RSPB020` / `RSPB025`,共十支維護畫面)全部繼承四眼引擎,但**卡控幾乎全部押在 UI 層**:

| 層 | 誰在這一層擋 | 說明 |
|---|---|---|
| UI `validatorManager1` | 十支都有 | 欄位必輸 / 格式,框架做 |
| UI `DoValidate()` | 十支都有,長度差很多 | `RSPM004` 這一支就 228 行(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2195-2418`) |
| PO `BeforeAdd` / `BeforeUpdate` | **只有 `RSPM004` / `RSPB020` / `RSPM005`** | 其餘七支的 PO 只掛取數事件,伺服端沒有第二道防線 |
| 四眼引擎 | 十支都走 | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:205`,細節看 `architecture.md §3` |
| 批次二次驗證 | `RSPB008` / `RSPB023` / `RSPB041` | 變更檔還有非「已覆核」狀態就不給生效 |

**繞過 UI 就等於沒有卡控**,這條在 RSP 特別嚴重:`RSPM004` 的郵局每日扣款限額檢核整段只存在於 UI(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2253-2344`),而 PO 端同名的 `CheckDayLmtAmt` 被整段註解掉(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:184-285`)。

### 1.4 批次 / 報表資料流

一日扣款作業的鏈(依訊息字串與各 PO 的檢核對象推):

| 順序 | 畫面 | 動作 | 主要表 |
|---|---|---|---|
| 1 | `RSPB009` | 產生 / 重作 / 刪除扣款資料 | `RSP005A` `RSP006A` → `RSP008` `RSP008A`,`CTL006A` 控制 |
| 2 | `RSPB010` | 指定實際扣款日與淨值日、送件 / 重新送件 | `RSP008` |
| 3 | `RSPB011` | 扣款回覆逐筆確認(成功 / 失敗 / 扣款中) | `RSP008A` |
| 4 | `RSPB015` | 扣款回覆確認,依扣款行與核印方式小計 | `RSP008A` |
| 5 | `RSPB016` | 單位數計算 | `RSP008A` |
| 6 | `RSPB018` | 結轉,必要時產法人公告警示表 | `RSP008A`、`OFD303A.RSP_CTL_CODE` |
| 例外 | `RSPB019` | 淨值回復,回復後要從 `RSPB016` 重跑 | `RSP008AA` |
| 收尾 | `RSPB052` | 連續扣款失敗達門檻的契約終止 | `RSP005A` `RSP006A` |

168 那條:`RSPB021`(扣款轉申購產生)→ `RSPB022`(停利計算)→ `RSPB024`(產 Email 資料)。停利那條:`RSPB042`(停利計算)。變更生效那三支:`RSPB008`(一般契約)、`RSPB023`(168 契約)、`RSPB041`(停利契約)。

報表全部走版控外的 SP + Crystal Report,取數與畫面不共用任何 PO(§7)。

### 1.5 一日作業泳道

| 時間(推測) | 誰 | 做什麼 | 動到哪張表 |
|---|---|---|---|
| 日間 | 櫃檯 | `RSPM004` / `RSPM005` / `RSPM021` / `RSPM022` / `RSPM041` / `RSPM042` 輸入與送審 | `RSP005A` `RSP006A` `RSP007A` `RSP013A` `RSP070A` `RSP071A` `RSP072A` `RSP073A` `RSP074A` `RSP075A` `RSP041A` `RSP042A` |
| 日間 | 覆核 | 四眼 V / A | 同上的 `Status` |
| `CTL016.RSP_PROC_TIME` 指定時刻 | `RSPB008_Service` | 契約變更生效(無人值守) | `RSP007A` `RSP013A` → `RSP005A` `RSP006A` |
| 扣款日前 | 作業 | `RSPB009` 產生扣款資料 | `RSP008` `RSP008A` `CTL006A` |
| 扣款日 | 作業 | `RSPB010` 送件 → 銀行回覆 → `RSPB011` / `RSPB015` 確認 | `RSP008` `RSP008A` |
| 扣款日 +N | 作業 | `RSPB016` 算單位數 → `RSPB018` 結轉 | `RSP008A`、`OFD303A` 控制碼 |
| 6 / 16 / 26 日 | 作業 | `RSPB021` 168 扣款轉申購 → `RSPB022` 停利計算 → `RSPB024` 寄信 | `RSP070A` `RSP071A` `RSP072A`、`LOG094A` `LOG095A` |
| 每日 | 作業 | `RSPB042` 定期定額停利計算 | `RSP041A`、`LOG109A` |
| 出錯時 | 作業 | `RSPB019` 淨值回復,再從 `RSPB016` 重跑 | `RSP008AA` |

## 2. 資料模型

```text
[圖] RSP 二十一張表的主明細配對、三組變更檔的平行結構,以及外部唯讀表
圖中文字:三組「主檔 + 變更檔」平行結構:變更當下不動主檔,要等批次 / RSP005A / PK 契約書號 / RSP006A / + 契約序號 / RSP007A / PK 變更書號 / RSP013A / + 變更序號 / RSP070A / PK 契約書號 / RSP071A RSP072A / 子基金 / 申購書 / RSP073A / PK 變更書號 / RSP074A RSP075A / 子基金 / 申購書 / RSP041A / PK 停利書號 / (無明細) / 一張設定一列 / RSP042A / PK 停利異動書號 / RSPB041 生效 / 比對 TX_DATE / 扣款檔三兄弟:不是主明細,是同一批資料的三個階段 / RSP008 / 產生 / 送件 / RSP008A / 回覆 / 計算 / 結轉 / RSP008AA / 淨值回復 / CTL006A / 扣款媒體控制 4 欄 / 168 母子基金白名單:多對多,不是交易檔 / RSP061A / PK 設定書號 / RSP062A / 母基金 N 檔 / RSP063A / 子基金 N 檔 雙 unique / 外部表:唯讀 join 或條件寫入 / COD009 COD010 / 員工 / 員眷 / OFD272A / 缺件 明細 / OFD374A / 歸屬業務員 條件寫 / BMS001 OFD130A OFD131A / 簡易開戶時寫
```

*圖:圖 2 資料模型。橘框=主檔;白框=明細或同族表;灰虛框=別的模組的表;黑框=外部唯讀。實線箭頭=主明細;回頭的長箭頭=變更檔經批次套回主檔。RSP063A 的 xsd 同時宣告單欄與雙欄 unique,一檔子基金只能掛一張設定書。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

25 支 PO 裡有 14 支宣告了主明細,其餘 11 支(`RSPB021`–`RSPB024`、`RSPB041`、`RSPB042`、`RSPB052` 等)完全不宣告——它們不用框架的存檔流程,只呼叫 SP。

| 畫面 | 實體主表 | vdb DataTable | 實體明細 | vdb DataTable | 錨點 |
|---|---|---|---|---|---|
| `RSPM004` | `RSP005A` | `RSPM004_Master` | `RSP006A` · `OFD272A` | `RSPM004_Detail` · `OFD272` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:76-80` |
| `RSPB020` | `RSP005A` | `RSPM004_Master` | `RSP006A` | `RSPM004_Detail` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:50-52` |
| `RSPM005` | `RSP007A` | `RSPM005` | `RSP013A` · `OFD272A` | `RSPM005_Detail` · `OFD272` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:147-149` |
| `RSPB008` | `RSP007A` | `RSP007A` | (宣告被註解) | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:42-44` |
| `RSPB009` | `RSP005A` | `RSPB009` | `RSP006A` · `CTL006A` | `RSPB009_Detail` · `CTL006` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:38-40` |
| `RSPB010` | `RSP008` | `RSPB010` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:21` |
| `RSPB011` | `RSP008A` | `RSPB011` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:33` |
| `RSPB015` | `RSP008A` | `RSPB015` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:41` |
| `RSPB016` | `RSP008A` | `RSPB016` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:39` |
| `RSPB018` | `RSP008A` | `RSPB018` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:32` |
| `RSPB019` | `RSP008AA` | `RSPB019` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:36` |
| `RSPM020` | `RSP061A` | `RSP061` | `RSP062A` · `RSP063A` | `RSP062` · `RSP063` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-38` |
| `RSPM021` · `RSPB025` | `RSP070A` | `RSPM070_Master` | `RSP071A` · `RSP072A` | `RSPM070_Detail` · `RSP072` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:51-53`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB025_PO.cs:37-39` |
| `RSPM022` | `RSP073A` | `RSPM022` | `RSP074A` · `RSP075A` | `RSPM022_Detail` · `RSP075` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM022_PO.cs:48-50` |
| `RSPM037` | `COD009` → `RSP005` → `RSP006` | `RSPM037` / `RSPM037_Detail` / `RSPM037_Detail_D` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| `RSPM041` | `RSP041A` | `RSPM041` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42` |
| `RSPM042` | `RSP042A` | `RSPM042` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM042_PO.cs:42` |

三件要注意的:

1. **`RSPM037` 的 `MasterTable` 被換三次。** `Select()` 設 `COD009`、`Select_Detail()` 設 `RSP005`、`Select_Detail_D()` 設 `RSP006`。這不是主明細宣告,是「同一支 PO 用三次 `base.Select()` 撈三張不同的表」。掃描器把第一個 `MasterTable` 當主檔,所以母體才會出現「`COD009` 主檔於 `RSPM037`」。

2. **`RSPB008` 的主明細宣告只剩半套。** `this.MasterTable = new xTableMapping("RSP007A", "RSP007A")` 生效,`RSP013` 的明細宣告躺在註解裡(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:44`)。實際 `RSP013A` 是在 SP 內處理,`CheckStatus` 的 SQL 也自己 join(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`)。

3. **`RSPM004` / `RSPB020` 共用同一組 DataTable 名稱**(`RSPM004_Master` / `RSPM004_Detail`),連 `App.config` 的 `mastertable` 都指同一個名字(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:88`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:150`)。`RSPM021` / `RSPB025` 同理(`RSPM070_Master`)。改 xsd 要兩支一起看。

### 2.2 主鍵與四眼欄位

主鍵取自 xsd 的 `xs:unique` 宣告:

| 實體表 | 主鍵 | 四眼 13 欄 | 來源 |
|---|---|---|---|
| `RSP005A` | `RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:836` |
| `RSP006A` | `RSP_NO` + `RSP_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:18` |
| `RSP007A` | `RSP_CHG_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:189` |
| `RSP013A` | `RSP_CHG_NO` + `RSP_CHG_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:584` |
| `RSP008` | `RSP_NO` + `RSP_SRNO` + `DEF_SUB_DATE` + `REAL_SUB_DATE` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:486` |
| `RSP008A` | `RSP_NO` + `RSP_SRNO` + `DEF_SUB_DATE` + `REAL_SUB_DATE`(`RSPB010` / `RSPB011` 視角) `FUND_ID` + `DEF_SUB_DATE` + `REAL_SUB_DATE`(`RSPB016` / `RSPB018` 視角) | 部分 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB011Model.xsd:17`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB016Model.xsd` |
| `RSP008AA` | (xsd 未宣告 unique) | 無 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB019Model.xsd:26` |
| `RSP061A` | `RE_RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15` |
| `RSP062A` | `RE_RSP_NO` + `MOM_FUND_ID` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:93` |
| `RSP063A` | `RE_RSP_NO` + `SON_FUND_ID`,**外加一條只有 `SON_FUND_ID` 的 unique** | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:183` |
| `RSP070A` | `RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:15` |
| `RSP071A` | `RSP_NO` + `RSP_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:283` |
| `RSP072A` | `RSP_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:494` |
| `RSP073A` | `RSP_CHG_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:15` |
| `RSP074A` | `RSP_CHG_NO` + `RSP_CHG_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:302` |
| `RSP075A` | `RSP_CHG_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:553` |
| `RSP041A` | `RSP_TRN_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17` |
| `RSP042A` | `TX_RSP_TRN_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM042Model.xsd:26` |
| `CTL006A` | `DEF_SUB_DATE` | 無 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:721` |
| `OFD272A`〔共用〕 | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1343` |
| `COD009`〔共用〕 | `EMP_NO` | **RSP 這一側的 xsd 沒宣告四眼欄** | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd:18` |

**`RSP063A` 那兩條 unique 是重點。** xsd 同時宣告了 `SON_FUND_ID`(單欄)與 `RE_RSP_NO,SON_FUND_ID`(兩欄)兩條 unique,單欄那條代表「一檔子基金只能掛在一張母子基金設定書底下」。這是 typed DataSet 層的限制,不保證實體表也這樣建;**改 `RSPM020` 時一定要先確認 DB 端的 unique index 是哪一種**,否則畫面會擋、DB 不擋,或者反過來。

`COD009` 在 RSP 側的 xsd 只宣告 6 欄(`EMP_NO` / `EMP_ID_NO` / `EMP_NAME` / `EMP_NAME_ENG` / `ENTRY_DATE` / `LEAVE_DATE`),而母體說這張表有 56 欄、有四眼——那是從 COD 側掃出來的。**同一張表在兩個模組的 typed DataSet 不同構**,這是 `architecture.md §5.4` 講的情形,不是缺陷。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列各表的識別欄與業務關鍵欄;完整欄位清單請直接看 xsd。

#### `RSP005A` — 定期定額契約主檔(`RSPM004_Master`,57 欄)

| 欄 | 中文名 | 說明 |
|---|---|---|
| `RSP_NO` | 契約書號 | PK,由 `SerialNo.GetRspNoForNfd()` 配號 |
| `RSP_TYPE` | 契約型態 |  |
| `RCV_DATE` | 收件日期 | 必須是營業日(§4.1) |
| `BF_NO` | 受益人戶號 | `-1` 代表要走簡易開戶 |
| `AGENT_ID` / `AGENT_CODE` | 銷售機構區別碼 / 銷售機構代碼 |  |
| `CHANNEL_CD` / `CHANNEL_CODE` | 通路區分碼 / 通路代碼 |  |
| `SPONSOR_CODE` | 推薦人代碼 | 銷售機構標 `SPONSOR_CHK` 時必填 |
| `EMP_NO` / `EMP_DEPT_NO` | 員工代碼 / 員工部門代碼 |  |
| `SER_EMP_NO` | 服務顧問代碼 | Designer 標籤寫「介紹人」 |
| `SUB_ID_TYPE` / `SUB_ID_NO` / `SUB_NAME` | 扣款人身份別 / 身份證字號 / 姓名 |  |
| `SEAL_TYPE` | 核印扣款方式 | 一般 / ACH / 財金三選一 |
| `SUB_BANK_CODE` / `SUB_ACCOUNT_NO` | 扣款行 / 扣款帳號 | `700` = 郵局〔客戶特定〕 |
| `SEAL_MARK` / `SEAL_USER_NO` | 核印註記 / 用戶號碼 |  |
| `STOP_BNG_DATE` / `STOP_END_DATE` | 暫停起始 / 終止日期 |  |
| `STOP_ID` / `STOP_DATE` / `STOP_CD` / `CODE_DESCRP` | 終止碼 / 終止日期 / 終止原因 / 終止原因說明 |  |
| `RSP_ACCT_BY` | 定期定額扣款帳號抓取依據 | 決定扣款資料在主檔還是明細維護(§4.1) |
| `RETIRE_YN` | 退休管家 |  |
| `RSP_NO_O` | 契約書號-舊 | 舊系統移轉來的契約 |

#### `RSP006A` — 定期定額契約基金明細(`RSPM004_Detail`,114 欄)

| 欄 | 中文名 |
|---|---|
| `RSP_NO` + `RSP_SRNO` | 契約書號 + 契約序號(PK) |
| `FUND_ID` / `FUND_SH_NM` / `FH_CD` | 基金代碼 / 基金中文簡稱 / 基金公司代碼 |
| `RSP_AMT` / `RSP_AMT2` / `RSP_AMT3` | 扣款金額 / 申購金額(中) / 申購金額(高) |
| `AMT_RATE_CD` / `HIGH_AMT_RATE` / `LOW_AMT_RATE` | 扣款金額比率 / 扣款金額(高)比率 / 扣款金額(低)比率 |
| `RSP_CNRT_FEE_RATE` / `RSP_CNRT_FEE_RATE2` / `RSP_CNRT_FEE_RATE3` | 契約手續費率 / 申購手續費率1 / 申購手續費率2 |
| `RSP_ALLOT_DAYS1` / `2` / `3` | 扣款日1 / 2 / 3 |
| `CAMPAIGN_CODE` / `CAMPAIGN_SHNM` | 促銷活動代碼 / 活動簡稱 |
| `BNG_DATE` / `END_DATE` / `DISC_TIMES` / `DISC_TIMES1` | 優惠起始 / 終止日期 / 優惠次數 / 已優惠次數 |
| `CAMP_DISC_TYPE` / `DISC_AMT` / `FIX_RATE` / `DISC_RATE` / `FEE_CAL_BASE` | 優惠折扣方式 / 優惠金額 / 優惠固定費率 / 優惠折數 / 手續費折數基準 |
| `FREE_FEE_TIMES` / `FREE_FEE_REASON` | 補償優惠次數 / 補償優惠原因 |
| `LOYAL_MRK` / `LOYAL_MRK1` | 忠實戶註記 / 前忠實戶註記 |
| `DFT_BNG_SUB_DATE` / `FIRST_SUB_DATE` / `FIRST_SUS_DATE` | 可開始扣款日期 / 首次扣款日期 / 首次扣款成功日期 |
| `FAIL_TIMES` / `SER_FAIL_TIMES` / `SUSD_TIMES` / `SER_SUSD_TIMES` | 累積扣款失敗 / 連續扣款失敗 / 累積扣款成功 / 連續扣款成功次數 |
| `SEAL_STATUS` / `SEAL_DATE` / `SEAL_RTN_DATE` / `SEAL_FAIL_ID_CO` / `SEAL_FAIL_ID_BK` | 核印狀態 / 最近送核印日期 / 最近核印回報日期 / 核印失敗原因碼(公司) / (銀行) |
| `INTRO_CODE` / `INTRO_MAIL_ZIP` / `INTRO_MAIL_ADDR` / `INTRO_EMAIL` | 公開說明索取方式 / 寄發地址郵遞區號 / 寄發地址 / 寄發EMAIL |
| `BANK_BRH` / `ACCOUNT_NO` | 收益分配行 / 收益分配帳號 |
| `DEC_LEN` | 幣別小數位數 |

#### `RSP007A` / `RSP013A` — 契約變更主檔 / 明細(`RSPM005` / `RSPM005_Detail`)

整張表的形狀就是 `BEF_xxx` / `AFT_xxx` 成對:「變更前扣款行」/「變更後扣款行」、「變更前扣款金額」/「變更後扣款金額」、「變更前優惠折數」/「變更後優惠折數」…。另有一組控制欄:

| 欄 | 中文名 | 作用 |
|---|---|---|
| `RSP_CHG_NO` / `RSP_CHG_SRNO` | 契約變更書號 / 契約變更序號 | PK |
| `CHG_DATE` | 異動收件日期 |  |
| `ORG_CHG_EFFECT_DATE` / `CHG_EFFECT_DATE` | 原始變更生效日期 / 變更生效日期 | `RSPB008` 用 `CHG_EFFECT_DATE` 挑要生效的資料 |
| `RSP_CHG_CODE` | 變更異動代碼 | 決定這一列改的是哪一組欄位 |
| `CHG_RSP_ALLOT_DAY` / `CHG_CAMP_CODE` / `CHG_STOP_DATE` / `CHG_FAVORED_REL_TYPE` / `CHG_AMT_RATE` | 變更扣款日 / 變更促銷活動代碼 / 變更暫停扣款日 / 變更優惠身份別 / (無 Caption) | 一組「這次有沒有改這一項」的旗標 |
| `RSP_CHG_CD` / `RSP_CHG_FAIL_CD` | 異動成功否 / 異動失敗原因 | **由 `RSPB008` 的 SP 回填**,失敗的要靠 `RSPR038` 撈 |
| `IS_SEAL_YN` | 異動送核否 | 變更扣款帳戶要不要重新送核印 |

#### `RSP070A` / `RSP071A` / `RSP072A` — 168 循環定額投資契約

| 表 | 中文名要點 |
|---|---|
| `RSP070A`(`RSPM070_Master`) | `MOM_FUND_ID` 母基金代碼、`REDEM_DATE` 約定轉申購日期、`REDEM_FEE_RATE1`–`3` 約定轉申購手續費率、`INVEST_TYPE` 投資型態、`GAIN_STOP` 終止停利設定、`STOP_REDEM_NO` 買回書號終止、`RETIRE_YN` 退休管家 |
| `RSP071A`(`RSPM070_Detail`) | `SON_FUND_ID` 子基金、`RSP_AMT1` 約定轉申購金額、`LOCK_POINT` 停利點、`LOCK_FEE_RATE` 停利轉申購手續費率、`GAIN_VALUE` / `GAIN_RATE` |
| `RSP072A`(`RSP072`) | `ALLOT_NO` / `ALLOT_SRNO` / `ALLOT_DATE` / `DATA_TYPE` / `REPRICE_DATE` 加碼生效日——掛在契約下的申購書清單 |

`RSP073A` / `RSP074A` / `RSP075A` 是上面三張的變更版,同樣 `BEF_` / `AFT_` 成對。

#### `RSP041A` / `RSP042A` — 停利轉申購

| 欄 | 中文名 |
|---|---|
| `RSP_TRN_NO` | 停利轉申購契約書號(`RSP041A` PK) |
| `TX_RSP_TRN_NO` | 停利異動書號(`RSP042A` PK) |
| `RSP_NO` | 定時定額契約書號(掛回 `RSP005A`) |
| `MIN_AMT` | 門檻金額(`RSP042A` 的 Caption 是「轉出餘額下限」) |
| `P_RATE` | 約定停利點 |
| `JOB_CD` | 停利機制 |
| `SWITCH_FUND_ID` | 轉出基金代碼 |
| `FEE_RATE` | 轉申購手續費率 |
| `RISK_CFD` | 風險確認 |
| `P_CODE` / `STOP_CODE` | 處理碼 / 終止碼 |

⚠ `RSP041A` 的 `RCV_DATE` 在 xsd 的 Caption 被寫成「門檻金額」,跟下一欄 `MIN_AMT` 撞名(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17`);Designer 的標籤是「收件日期」。**以 Designer 為準**,這是 xsd 的複製貼上錯誤,列入附錄 E。

#### `RSP008` / `RSP008A` / `RSP008AA` — 扣款檔三兄弟

`RSP008`(`RSPB009` / `RSPB010` 視角,55 欄)是一筆一筆的扣款明細:`DEF_SUB_DATE` 契約扣款日期、`REAL_SUB_DATE` 實際扣款日期、`ALLOT_NAV_DATE` 淨值日、`ETD_RSP_ALLOT_AMT` / `RSP_ALLOT_AMT` 預計 / 實際扣款申購金額、`RSP_ALLOT_FEE` / `AGENT_ALLOT_FEE` / `COMP_ALLOT_FEE` 三段手續費、`TOT_SUB_AMT` 扣款總金額、`BANK_SUB_FEE` 銀行手續費、`NAV_B` 淨值、`RSP_ALLOT_UNIT` 單位數、`SUB_STATUS` 扣款進度、`NONSUCS_CODE` 扣款失敗代碼、`DATA_CENTER` 扣款資料處理中心、`BANK_MEDIA_CODE` 銀行媒體代碼。

`RSP008A` 是同一批資料在「回覆 / 計算 / 結轉」階段的視角,`RSP008AA` 是淨值回復用的。**三張表在 repo 內都沒有 DDL**(`DB/Table/` 只有 `update_rsp006a.sql` 與 `create_LOG_RSP070A.sql` 兩個跟 RSP 有關的檔),欄位定義只能從 xsd 反推。

#### `CTL006A` — 扣款日媒體產生控制(4 欄)

`DEF_SUB_DATE`(契約扣款日期)+ `IS_CRE_DISK_DATA` / `IS_CRE_FIS_DATA` / `IS_CRE_ACH_DATA` 三個旗標,對應「一般 / 財金 / ACH」三種扣款媒體有沒有產過。錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:721`。

### 2.4 與其他模組共用的表

| 表 | 前綴屬於 | 主檔維護入口 | RSP 這側做什麼 | 錨點 |
|---|---|---|---|---|
| `COD009` | COD | `CODM009` / `CODB009` | **只讀**,當 `RSPM037` 的查詢驅動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:92-93` |
| `COD010` | COD | COD 側 | **只讀**,撈員眷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:106-108` |
| `OFD272A` | OFD | OFD / BMS 側(`BMSM004` `BMSM006` `OFDM221A` `OFDM231A`) | 當 `RSPM004` / `RSPM005` 的第二明細,存 / 刪缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149` |
| `OFD374A` | OFD(主檔在 DSM 的 `DSMM060`) | `DSMM060` | 簡易開戶且 `AUTO_BELONG_EMP = 'Y'` 時 `INSERT` 一筆 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698-738` |
| `BMS001` | BMS | `BMSM001` | 簡易開戶時 `INSERT` 一筆;其餘一律 join 取姓名 / ID | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:794-808` |
| `OFD130A` / `OFD131A` | OFD | OFD 側 | `RSPM004` 存檔後補建匯款授權書與帳號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1211-1262` |
| `OFD132A` | OFD | OFD 側 | 簡易開戶時依 `OFD040A` 範本產對帳單寄送設定 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741-791` |
| `OFD220A` / `OFD221A` / `OFD306A` | OFD | OFD 側 | `RSPB020` / `RSPB025` 改契約業務欄位時連動 `UPDATE` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:561-610` |
| `OFD303A` | OFD | OFD 側 | 只讀,判斷關帳 / 結轉控制碼 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119-130` |
| `OFD681` | OFD | OFD 側 | 只讀,取 `SEND_TYPE = '6'` 的通知信收件人 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:343-344` |
| `OFD701` | OFD | OFD 側 | 讀 / 判核印狀態,`RSPM004` 存明細時連動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| `CTL014` / `CTL016` | 共用控制檔 | 未知 | 只讀,取預設值與排程時刻 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302` |
| `LOG094A` / `LOG095A` / `LOG109A` | LOG | 未知 | 只讀,判斷批次有沒有跑過 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:230-231`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:190-192` |

反過來,**RSP 自己的表被誰用**見 §8。母體只標了 `RSP006A`(BMS / OFD 也用)一張。

### 2.5 狀態碼(從程式反推,標來源)

#### 四眼 `Status`

RSP 全模組都吃框架的 `Status` 值域,細節看 `architecture.md §3.10`。本模組只有三個地方直接寫死狀態字串:

| 值 | 用在哪 | 錨點 |
|---|---|---|
| `'301'` | `RSPB052` 產出的終止資料、`RSPM004` 補建的 `OFD130A` / `OFD131A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |

其餘一律走 `f_TA_GetEVAStatus('A')` 這個 TVF 取「已生效」的狀態集合,再用 `NOT IN` 找還沒覆核完的:

```
RSP007A.Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))
```

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:154`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:112`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:111`。`f_TA_GetEVAStatus` 不在版控內。

#### `REDEM_DATE` — 168 契約的約定轉申購日(反推自 `DECODE`)

`RSPB021_PO` 用三段 `DECODE` 把代碼展開成 6 / 16 / 26 日,逆推出來的值域是:

| 代碼 | 6 日 | 16 日 | 26 日 |
|---|---|---|---|
| `1` | ✓ |  |  |
| `2` |  | ✓ |  |
| `3` |  |  | ✓ |
| `4` | ✓ | ✓ |  |
| `5` |  | ✓ | ✓ |
| `6` | ✓ |  | ✓ |
| `7` | ✓ | ✓ | ✓ |

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128`。同一組 `DECODE` 在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:163-165` 又抄了一次(子基金版本),**兩份要一起改**。

#### `OFD303A` 的三個控制碼(只列 RSP 讀到的值)

| 欄 | 值 | 意義(依訊息字串) | 錨點 |
|---|---|---|---|
| `REDEM_CTL_CODE` | `'4'` | 買回 NAV 日之買回關帳作業已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148-149` |
| `ALLOT_CTL_CODE` | `'3'` | 此買回 NAV 日之申購關帳作業已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:150-151` |
| `RSP_CTL_CODE` | `'1'` | 請先執行單位數計算作業 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:81` |
| `RSP_CTL_CODE` | `'3'` | 本日定期定額申購資料已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:80` |

#### 本模組自訂的旗標〔客戶特定〕

| 欄 | 值 | 意義 | 錨點 |
|---|---|---|---|
| `STOP_ID` | `'N'` / 空 = 未終止 | `NVL(TRIM(STOP_CD),'N') = 'N'` 是 168 契約「還活著」的判斷式 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:125`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:969` |
| `RSP_CHG_CODE` | `'A'` | 168 變更明細的「新增子基金」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945` |
| `ISCHG_STOP_ID` | `'Y'` / `'N'` | 這一列有沒有改終止設定 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:554`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:562` |
| `SEAL_TYPE` | 一般 / ACH / 財金 | 三種扣款媒體,`RSPB009` / `RSPB010` / `RSPB011` / `RSPB015` 都拿它分流 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2282`(`GetSealType`,順序 FIS → ACH → 一般) |
| `SEND_TYPE` | `'6'` | `OFD681` 裡 RSPB008 通知信的收件人群組 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `EMP_CD` | `'1'` | `COD009` 裡「算員工」的判斷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111` |
| 銀行總行 | `'700'` | 郵局;`RSPM004` 的限額檢核與身份別鎖定都認這個值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753` |
| 促銷活動 | `'86A03'` | `RSPM004` 有一支專門檢核這個活動的方法 `Check86A03` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785` |

## 3. 畫面清冊

56 支畫面:B 17、I 0、M 8、R 31。六層(UI / FormProxy / Control / PO / UIEntity / DataEntity)按掃描母體全部「齊」,實際比對後有兩處要修正,見附錄 D.2。

### 3.1 維護 M

| 代號 | 中文名(推測) | 六層 | 主表 | 明細 | 伺服端卡控 | 彈出視窗 |
|---|---|---|---|---|---|---|
| `RSPM004` | 定期定額契約申請 | 齊 | `RSP005A` | `RSP006A` `OFD272A` | `BeforeAdd` / `AfterAdd` / `AfterUpdate` / `AfterApproveDelete` | `RSPM004p0`–`RSPM004p4`(5 支) |
| `RSPM005` | 定期定額契約變更 | 齊 | `RSP007A` | `RSP013A` `OFD272A` | `BeforeAdd` / `BeforeUpdate` 等 | `RSPM005p0`–`RSPM005p3`(4 支) |
| `RSPM020` | 母子基金設定 | 齊 | `RSP061A` | `RSP062A` `RSP063A` | 只掛取數 | 無 |
| `RSPM021` | 168 循環定額投資契約 | 齊 | `RSP070A` | `RSP071A` `RSP072A` | 只掛取數 | `RSPM021p0` |
| `RSPM022` | 168 循環定額投資契約變更 | 齊 | `RSP073A` | `RSP074A` `RSP075A` | 只掛取數 | `RSPM022p0` |
| `RSPM037` | 離職員工契約手續費率維護 | 齊 | `COD009`(只讀) | `RSP005` / `RSP006`(只讀 / 只改費率) | 無 | `RSPM037p0` `RSPM037p1` |
| `RSPM041` | 停利轉申購契約 | 齊 | `RSP041A` | — | 只掛取數 | 無 |
| `RSPM042` | 停利轉申購契約異動 | 齊 | `RSP042A` | — | 只掛取數 | 無 |

加上偽裝成 B 的 `RSPB020`(定期定額契約業務資料維護)與 `RSPB025`(168 契約業務資料維護),實際維護畫面共十支。

### 3.2 查詢 I

**本模組無 I 畫面**,原因見 §5。

### 3.3 批次 B

| 代號 | 中文名(推測) | 基底 | 主表 | SP | 前置檢核 |
|---|---|---|---|---|---|
| `RSPB008` | 定期定額契約變更生效 | `xOneStepProcessForm` | `RSP007A` | `s_TA_RSPB008_Excute_M` | `CheckStatus`(未覆核就擋) |
| `RSPB009` | 產生 / 重作 / 刪除扣款資料 | `xOneStepProcessForm` | `RSP005A` + `RSP006A` + `CTL006A` | `S_TA_RSPB009_Excute` | 契約扣款日有效、註銷戶詢問、是否已有扣款日 |
| `RSPB010` | 扣款送件與實際扣款日 / 淨值日指定 | `xOneStepProcessForm` | `RSP008` | `EXEC s_RSPB010_Excute …`(字串) | 淨值日已過帳 / 已結轉、實際扣款日已算淨值 / 已最後確認 |
| `RSPB011` | 扣款回覆逐筆確認 | `xOneStepProcessForm` | `RSP008A` | 無(直接 SQL) | 小額扣款控制碼四段 |
| `RSPB015` | 扣款回覆確認(依扣款行小計) | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB015_Excute` | 無 |
| `RSPB016` | 單位數計算 | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB016_Excute` | 無符合資料就擋 |
| `RSPB018` | 結轉 | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB018_Excute` | `OFD303A.RSP_CTL_CODE` + 淨值一致性 |
| `RSPB019` | 淨值回復 | `xOneStepProcessForm` | `RSP008AA` | `S_TA_RSPB019_Excute` | 無 |
| `RSPB020` | 定期定額契約業務資料維護 | **`xMaintainForm`** | `RSP005A` + `RSP006A` | 無(直接 SQL,含 PL/SQL 區塊) | 四眼 |
| `RSPB021` | 168 扣款轉申購產生 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB021_EXCUTE` | `ValidateOFD303A`;`ValidateLOG095A` **被註解掉** |
| `RSPB022` | 168 停利計算 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB022_EXCUTE` | `ValidateLOG094A` + `ValidateOFD303A` |
| `RSPB023` | 168 契約變更生效 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB023_EXCUTE` | `CheckStatus`(查 `RSP073A`) |
| `RSPB024` | 168 轉申購 Email 資料產生 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB024_EXCUTE` | 只擋「轉申購日須為 6/16/26」 |
| `RSPB025` | 168 契約業務資料維護 | **`xMaintainForm`** | `RSP070A` + `RSP071A` + `RSP072A` | 無 | 四眼 |
| `RSPB041` | 停利契約變更生效 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB041_EXCUTE` | `CheckStatus`(查 `RSP042A`) |
| `RSPB042` | 定期定額停利計算 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB042_EXCUTE` | `ValidateLOG109A` + `ValidateOFD303A` |
| `RSPB052` | 連續扣款失敗契約終止 | `xOneStepProcessForm` | 無宣告 | 無(直接 SQL) | 無 |

**「無宣告主明細」的 8 支走的路徑**:它們的 PO **不繼承** `BaseEVADaoPO` / `BasicEVAPO`,只實作自己的介面(例 `public class RSPB021_PO : IRSPB021_PO`,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:26`),自己 `new Database("TA", DbServerType.Oracle)`、自己開交易、自己呼叫 SP。沒有 `MasterTable` 是因為**根本沒用到框架的存檔流程**,不是漏寫。`RSPB052` 是唯一的例外:它不宣告主明細,卻自己寫 `INSERT` / `UPDATE`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`)。

### 3.4 報表 R

31 支 R、39 個 `.rpt`。對應關係見 §7.2;這裡只列代號與標題(標題取自 `SetQueryParameters` 的第三個參數,是程式裡寫死的中文字串,不是推測):

| 代號 | 報表標題 | rpt | SP |
|---|---|---|---|
| `RSPR008` | 定期定額異動資料轉入主檔報表 | `RSPR008RPS` | `s_RSPR008_Get` |
| `RSPR011` | 定期定額-申購扣款明細表 | `RSPR011RPS` | `S_TA_RSPR011_GET` |
| `RSPR012` | 定期定額扣款行回覆資料查核表 | `RSPR012RPS` | `S_TA_RSPR012_GET` |
| `RSPR013` | 定期定額扣款銀行查核表 | `RSPR013RPS` / `RSPR013RPS1` | `S_TA_RSPR013_GET` |
| `RSPR017` | 定期定額-受益人申購明細表 | `RSPR017RPS` / `RSPR017RPS1` / `RSPR017RPS2` | `s_TA_RSPR017_Get` |
| `RSPR020` | 定期定額契約資料查核表 | `RSPR020RPS` / `RSPR020RPS1` | `S_TA_RSPR020_GET` |
| `RSPR021` | 定期定額扣款失敗明細表 | `RSPR021RPS` / `RSPR021RPS1` | `S_TA_RSPR021_GET` |
| `RSPR023` | 定期定額-保管銀行傳真表 | `RSPR023RPS` | `s_RSPR023_Get` + `s_RSPR023_Count` + `s_RSPR023_Total` |
| `RSPR024` | 定期定額-申購扣款總表 | `RSPR024RPS` / `RSPR024RPS1` | `S_TA_RSPR024_GET` |
| `RSPR028` | 定期定額扣款失敗項目統計表 | `RSPR028RPS` | `S_TA_RSPR028_GET` |
| `RSPR029` | 定期定額契約異動項目統計表 | `RSPR029RPS` | `S_TA_RSPR029_GET` |
| `RSPR031` | 定期定額投資計畫 - 收件通知書 | `RSPR031RPS` | `s_TA_RSPR031_Get` |
| `RSPR034` | 定期定額首次扣款通知書 | `RSPR034RPS` | `s_RSPR034_1_Get` / `s_RSPR034_2_Get` |
| `RSPR038` | 定期定額契約異動資料查核表 | `RSPR038RPS` | `S_TA_RSPR038_GET` |
| `RSPR041` | 停利轉申購書查核表 | `RSPR041RPS` | `S_TA_RSPR041_GET` |
| `RSPR042` | 停利轉申購異動書查核表 | `RSPR042RPS` | `S_TA_RSPR042_GET` |
| `RSPR043` | 定期定額停利轉申購(含買回)停利核對表 | `RSPR043RPS` | `S_TA_RSPR043_GET` |
| `RSPR046` | 定期定額契約終止原因統計表 | `RSPR046RPS` | `s_RSPR046_Get` |
| `RSPR047` | 定期定額契約終止原因明細表 | `RSPR047RPS` | `s_RSPR047_Get` |
| `RSPR048` | 定期定額契約連續扣款失敗明細表 | `RSPR048RPS` | `s_TA_RSPR048_Get` |
| `RSPR049` | 定期定額扣款檢核表 | **無 rpt(純 Excel)** | `s_RSPR049_Get` |
| `RSPR051` | 定期定額投資計畫 - 扣款失敗通知書 | `RSPR051RPS` | `s_TA_RSPR051_Get` |
| `RSPR060` | 168循環定額投資法契約核對表 | `RSPR060RPS` / `RSPR060RPS1` | `S_TA_RSPR060_GET` |
| `RSPR061` | 168循環定額投資法契約異動報表 | `RSPR061RPS` | `S_TA_RSPR061_GET` |
| `RSPR062` | 168循環定額投資法契約扣款日記錄表 | `RSPR062RPS` | `S_TA_RSPR062_GET` |
| `RSPR063` | 168循環定額投資法停利核對表 | `RSPR063RPS` | `S_TA_RSPR063_GET` |
| `RSPR064` | 168循環定額投資法客戶查詢報表 | `RSPR064RPS` | `S_TA_RSPR064_GET` |
| `RSPR065` | 168標的基金申購金額不足核對表 | `RSPR065RPS` | `S_TA_RSPR065_GET` |
| `RSPR066` | 168投資契約轉帳明細表(成功 / 失敗) | `RSPR066RPS` / `RSPR066RPS1` / `RSPR066RPS2` | `S_TA_RSPR066_GET` |
| `RSPR070` | 業務受益人定額停扣明細報表(四種標題) | `RSPR070RPS` | `S_TA_RSPR070_GET` |
| `RSPR071` | 定期定額申請暫停扣款查核表 | `RSPR071RPS` | `S_TA_RSPR071_GET` |

### 3.5 一眼看出差別的五件事

1. **沒有任何 I 畫面。** 查詢需求全部由 31 支報表吸收,其中 `RSPR064`(168 客戶查詢報表)、`RSPR070`(業務受益人明細)實質上就是查詢畫面披報表的皮(§5)。

2. **8 支 M + 2 支偽 B 的維護畫面裡,只有 3 支在伺服端還有卡控**(`RSPM004` / `RSPB020` / `RSPM005`),其餘 7 支的 PO 只掛 `BeforeSelect` 之類的取數事件。

3. **三條「變更 → 生效」的鏈長得一模一樣**,但實作細節三種:`RSPB008` 讀 RefCursor、`RSPB023` / `RSPB041` 讀 OUT 參數,而且 `RSPB008` 多了一支 WindowsService。

4. **報表 SP 的命名有三種大小寫風格**:`S_TA_RSPRxxx_GET`(18 支)、`s_TA_RSPRxxx_Get`(5 支)、`s_RSPRxxx_Get`(7 支)。Oracle 的物件名不分大小寫,所以這只是可讀性問題,但 grep 時要三種都試。

5. **`RSPR049` 是 31 支裡唯一不出 Crystal Report 的**,直接把 byte 陣列寫成 `.xlsx` 再 `Process.Start` 打開(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84-97`)。`RSPR070` 則是報表與 Excel 兩套都有(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:234-258`)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] RSP 維護畫面的卡控分層:UI 層、PO 層、四眼引擎,以及兩個不走四眼的例外
圖中文字:① 用戶端(UI):十支維護畫面的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / RSPM004 這支 228 行 / 明細彈窗 / RSPM004p0 3089 行 / ByPass 訊息 / 詢問通過就記錄 / ② 伺服端(PO):十支裡只有三支有第二道防線 / RSPM004 BeforeAdd / 簡易開戶 + 配書號 / RSPM005 BeforeAdd / 鎖契約 + 來源檢核 / RSPB020 存檔後 / 連動三張 OFD 表 / 其餘七支 / PO 只掛取數事件 / ③ 四眼引擎(BaseEVADaoPO,無原始碼) / 輸入 / 待驗證 / 驗證 / 待覆核 / 覆核 / Status 進已生效集合 / 覆核完不等於生效 / 要等 RSPB008 / B023 / B041 / ④ 兩個例外 / RSPM037 / xOneStepProcessForm / 手寫 UPDATE RSP006 / 不寫 Status 不走四眼 / RSPB052 / 自己寫 Status=301 / 產出即已覆核 / 不進任何人的待辦
```

*圖:圖 3 卡控順序。橘框=真正會擋下的關卡;橘虛框=風險或例外;黑框=無原始碼的框架層。十支維護畫面(八 M 加 RSPB020 / RSPB025)裡只有三支在伺服端再驗一次;RSPM037 連四眼都不走,RSPB052 自己把狀態寫成已覆核。*

八支 M 加兩支掛 `xMaintainForm` 的 B(`RSPB020` / `RSPB025`)。後兩支的差異寫在 §4.1 與 §4.4 的節內,不另開節。

### 4.1 `RSPM004` — 定期定額契約維護作業

#### 用途

**這支畫面的中文名不是推測**——`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:33` 的 XML 註解直接寫「程式名稱:定期定額契約維護作業」。它是整個模組的入口:輸入一張契約書(`RSP005A`),底下掛 N 檔基金的扣款設定(`RSP006A`),必要時同時登記缺件(`OFD272A`)。

規模:UI 2,899 行 + 主明細彈出視窗 `RSPM004p0` 3,089 行 + PO 2,883 行,加上 `RSPM004p1`–`RSPM004p4` 四支小彈窗,是全模組最大的一支。

#### 五個彈出視窗

| 彈窗 | 行數 | 做什麼 |
|---|---|---|
| `RSPM004p0` | 3,089 | 基金明細的新增 / 修改,所有金額、費率、優惠、扣款帳號的檢核都在這裡 |
| `RSPM004p1` | 25 | 極小,幾乎是空殼 |
| `RSPM004p2` | 145 | 缺件維護(對應 `DoExp2`) |
| `RSPM004p3` | 75 | 扣款次數查詢(對應 `DoExp3`,取 `OFD315`) |
| `RSPM004p4` | 49 | 文件調閱(對應 `DoExp4`) |

四顆自訂鈕的掛點:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:760`(印鑑 `DoExp1`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:777`(缺件 `DoExp2`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:784`(扣款次數 `DoExp3`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:800`(文件調閱 `DoExp4`)。缺件鈕還有自己的前置驗證 `DoExp2Validate`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:767`)。

#### 「扣款帳號抓取依據」是寫死的 `'2'`

主檔取數 SQL 直接 `SELECT … ,'2' AS RSP_ACCT_BY`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212`),UI 的建構期也硬派 `RspAcctBy = "2"`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:166`),原本要讀系統參數的那段被註解掉(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:161-165`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:85-89`)。

檔頭註解說明了原因:「依規格翻修(`CTL015.RSP_ACCT_BY` 設為 1:依主檔扣款帳號的功能未完成)20090605-000」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:35`),`RSPM005_PO` 也有同一句(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:123`)。

**實務意義:扣款行 / 扣款帳號 / 扣款方式一律在「明細」層維護,主檔那一組欄位永遠不顯示**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:609-613` 的 `IsShowSubData(false)`)。如果哪天要打開 `RSP_ACCT_BY = '1'`,要改的不只是那個常數,還有 `SetMasterToDetail()` 內「扣款帳號抓取依據依照主檔時,將扣款資料寫入明細檔」那一段(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2471`)。

#### 簡易開戶:註解說取消了,程式路徑還在

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:36` 寫「2013.01.29 取消簡易開戶功能,若要使用簡易開戶功能,須 REVIEW 受益人相關欄位是否相符」。但程式沒有任何開關把它關掉:在客戶統編欄輸入一個查不到受益人的統編,就會走到 `SetBfDataVisible(true)`,整組開戶欄位打開、`Simple_Open = true`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:902-919`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1917-1940`)。

存檔時 PO 端的 `BeforeAdd` 會:

1. 用 `SerialNo.GetBFNo()` 配戶號,並 do-while 檢查撞號(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:638-643`)

2. 依 `ProductId.TaOfd` / `ProductId.TaNfd` 帶國別碼與 `BF_SORT_CD`(自然人 `140` / 法人 `090`)(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:649-676`)〔客戶特定〕

3. 從 `CTL014` 取八組預設值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684`)

4. 視 `AUTO_BELONG_EMP` 決定要不要 `INSERT OFD374A`(§8.4)

5. 依 `OFD040A` 範本 `INSERT OFD132A`(對帳單寄送設定)

6. `INSERT BMS001`

**六步驟全部串成同一條 SQL 字串再一次 `ExecuteNonQuery`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-803`)。這條字串的形狀是 `;INSERT OFD374A …;INSERT OFD132A …` 再接 `xTableHelper.GetInsertString(dbProduct, "BMS001")` 的產出,**沒有 `BEGIN` / `END`**。同一支 repo 內只要要送多段 DML 都會自己包 PL/SQL 區塊(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:560`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569`),這一段沒包。**假設**:這條 SQL 在 Oracle 會拋 `ORA-00911`,也就是簡易開戶實際上已經不能用,與 2013 那句註解吻合。依據:`xTableHelper.GetInsertString` 產出的是單一 `INSERT INTO … VALUES ( … )` 不帶分號(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:486-511`),`Database.ExecuteNonQuery` 無原始碼(框架 DLL),無法確認它會不會自動包區塊。

#### 必填與存檔前檢核(UI 層)

`DoValidate(bool IsFinalCheck)`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2195-2418`)。順序與短路點:

1. `ValidateErrList.Clear()` → `validatorManager1.DataValidate()`

2. 明細 grid 沒有資料 → 「明細資料必須輸入」,**而且 `if (ErrorCount > 0) return true` 直接短路**,後面所有檢核都不跑(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2202-2207`)

3. 簡易開戶區塊有開才檢核:戶籍地址、開戶日期 ≤ 收件日期、出生日期 ≤ 開戶日期、出生日期 ≠ `1900/01/01`、出生日期 < 系統日、開戶日期須為營業日

4. 只有按「新增 / 修改」才跑(`IsFinalCheck`):暫停交易檢核 + 郵局扣款日限額

5. 只有「新增」才跑:缺件且限制交易(`IsLackDoc`)

6. 推薦人:銷售機構的 `SPONSOR_CHK` 標了就必填

7. 非簡易開戶時,收件日期不可小於受益人的開戶日期

8. 收件日期須為營業日

9. `IsFinalCheck` 時:員工代碼歸屬的銷售機構與畫面不符 → **詢問**,按「是」寫 ByPass 訊息

#### 郵局扣款日限額:一段只活在 UI 的檢核

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2253-2344`。挑出明細裡扣款行是郵局且未終止的列,依「扣款帳號 + 扣款方式 + 扣款日」分組加總 `RSP_AMT`,丟給 `cnbu.CalcLmtAmt` 算限額。

三個要注意的:

- **篩選條件的第二個分支是死的。** `(SUB_BANK_CODE LIKE '700%' OR (SUB_BANK_CODE='' AND SUB_BANK_CODE LIKE '700%'))` —— `= ''` 和 `LIKE '700%'` 不可能同時成立(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255-2257`)。

- **`SetUtilRow` 把扣款行硬寫成 `"700"`**,不管實際值(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`)。因為外層已經篩過只留郵局,所以目前沒事,但兩處耦合。

- **伺服端沒有對應的檢核。** PO 的 `CheckDayLmtAmt` 整段被註解,註解說「改寫在 StoredProcedure 裡檢核」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286`),而那個 SP 不在版控內。UI 這一段被繞過就沒人擋。

#### 明細層(`RSPM004p0`)的檢核總覽

這支彈窗 3,089 行,檢核密度是全模組最高。分類:

| 類 | 內容 | 錨點 |
|---|---|---|
| 必填 | 扣款金額;公開說明書索取方式選「郵寄 / EMAIL」時對應欄位必填 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2076`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2083-2091` |
| 金額 | 定期不定額時「申購金額(低) ≤ (中) ≤ (高)」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2328` |
| 費率下限 | 契約手續費率不可小於該基金的最低手續費率 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2376` |
| 費率上限 | 不可大於牌告手續費率;沒設定自訂費率就報「自訂銷售手續費率尚未設定(OFDM193)」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2395`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2400` |
| 優惠 | 優惠日期(起)不可大於(迄);優惠日期與次數擇一輸入 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2423`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2462` |
| 高收益基金 | 必須勾風險確認;受益人必須先有風險預告書 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2341`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2346` |
| 扣款帳號 | 已送核 / 已啟動重新送核不可修改;扣款行不支援該扣款方式;非本人時扣款人 ID 不可等於客戶統編;受益人已成年時身份別不可為法定代理人 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2542`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2546`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2555`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2573`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2592` |
| 扣款行限額 | 逐筆算 `CalcLmtAmt` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2427-2456` |
| 銷售機構 | 銷售機構是否有效承銷該基金(`cnbu.IsAgentFund`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2469-2473` |

**詢問類**(跳 `Warn03`,按「是」就寫 ByPass 訊息記錄下來):

| 訊息 | 錨點 |
|---|---|
| 此受益人本日已有相同之基金扣款資料,請確定要存檔? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2155-2164` |
| 扣款帳號為核印失敗狀態,請確定要存檔? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2171-2180` |
| 有多筆未終止的契約資料,是否繼續? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2291-2296` |
| 該客戶為優惠關係人,但有輸入促銷活動代碼是否繼續? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2302-2309` |
| 該客戶為優惠關係人,是否仍要輸入促銷活動代碼? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:1123` |

「此受益人本日已有相同之基金扣款資料」這一條是兩段式:先用 `DataTable.Select` 在畫面上的明細裡找(`RCV_DATE` + `FUND_ID` + 不同 `RSP_SRNO`),沒找到才打 `CheckSameRspData` 去 DB 查其他契約(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2122-2152`)。「有多筆未終止的契約資料」同樣兩段式,DB 那段走 `CheckSameData`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2262-2288`)。

#### 伺服端(PO)做的事

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 簡易開戶(見上)+ 用 `SerialNo.GetRspNoForNfd()` 配契約書號,do-while 防撞號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:623-835` |
| `AfterAdd` / `AfterUpdate` | `BeforeSaveDetail()` 處理明細與核印 + `AddOFD130A()` 補建匯款授權書 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:859-875` |
| `AfterGetMaintainData` | 取跳號一覽表歷史 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2577-2582` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterResend` / `AfterReject` | 六個事件做的是**同一件事**:`SrNoCommentProcessor.AddCommentHistory(對應 EVAType, SrNo.RspNoForNfd, …)`,失敗就 `throw new ApplicationException("")`(**空訊息**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2584-2651` |
| `AfterApproveDelete` | 除了寫跳號紀錄,還要把核印資料收尾:`BuildOldSeal()` 的字串用 `Split(';')` 切成兩段分別執行,再 `CheckOldSeal` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2612-2637` |

`AddOFD130A` 的行為(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1187-1265`):畫面上有填收益分配帳號(`BMS005A_TMP` 有列)才動作;先看 `OFD130A` 有沒有這個受益人的授權書編號,沒有就配一個新的並 `INSERT`,`STATUS` **寫死 `'301'`**、`REJECTDATE` 寫死 `DATE'1900-01-01'`;再把 `BMS005A` 的帳號資料複製一列進 `OFD131A`,`FUND_ID` **寫死字串 `'ALL FUNDS'`**、`PAUSE_PAY` 寫死 `'N'`。

#### 跨表更新一覽

| 表 | 動作 | 條件 | 錨點 |
|---|---|---|---|
| `RSP005A` | INSERT / UPDATE | 框架四眼 | — |
| `RSP006A` | INSERT / UPDATE / DELETE | `BeforeSaveDetail` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:882-1186` |
| `OFD272A` | INSERT / DELETE | 缺件頁籤有資料 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1171-1186` |
| `OFD701` | UPDATE | 核印資料連動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| `BMS001` | INSERT | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:794-808` |
| `OFD374A`〔共用〕 | INSERT | 簡易開戶 **且** `AUTO_BELONG_EMP = 'Y'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698-738` |
| `OFD132A` | INSERT … SELECT | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741-791` |
| `OFD130A` / `OFD131A` | INSERT | 有填收益分配帳號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1211-1262` |

#### 取數 SQL 與下拉過濾

主檔取數 `BuildMasterSQLString`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:174-427`),六張表全部 `LEFT JOIN`,查不到對照就 `NVL(…,'')`,**不會把主檔資料濾掉**:`BMS001A`(受益人)、`COD009`(員工姓名)、`OFD072A`(推薦人)、`TABLE(F_TA_GetAgent())`(銷售機構)、`OFD071A`(通路)、`OFD002`(部門)、`COD006A`(終止原因,固定 `CODE_SORT='42'`)。

明細取數 `BuildDetailSQLString`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:428-621`)分兩段:`RSP006A` 與 `OFD272A`。

`GetSealType`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2282-2354`)依「FIS → ACH → 一般」的優先序決定扣款方式,`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2824` 有對應的 UI 呼叫。扣款行為郵局(`700`)時身份別鎖成「本人」且不可修改(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753`)〔客戶特定〕。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 存檔 | 明細 grid 無資料 | 無明細 | 阻擋(且短路後續全部檢核) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2202-2207` |
| UI 存檔 | 收件日期 < 開戶日期 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2216-2219` |
| UI 存檔 | 出生日期 > 開戶日期 / 格式錯 / ≥ 系統日 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2222-2235` |
| UI 存檔 | 開戶日期非營業日 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2240-2243` |
| UI 存檔 | 郵局扣款日限額 | 加總超限 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2331-2335` |
| UI 存檔 | `CalcLmtAmt` 回 `ReturnCode == false` | 中間層異常 | 阻擋(顯示通用伺服端錯誤) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2336-2340` |
| UI 存檔(新增) | 受益人有缺件且限制交易 | `IsLackDoc` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2347-2352` |
| UI 存檔 | 銷售機構要求推薦人卻沒填 | `SPONSOR_CHK` = 已標記 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2362-2366` |
| UI 存檔 | 收件日期 < 受益人開戶日期(非簡易開戶且無舊契約書號) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2378-2385` |
| UI 存檔 | 收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2388-2392` |
| UI 存檔 | 員工代碼歸屬的銷售機構與畫面不符 | 成立 | 詢問(按否就 focus 回銷售機構) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2397-2414` |
| UI 存檔 | 受益人為暫停做定期定額交易 | `IsPauseTrade` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2434-2449` |
| UI 統編輸入 | 統編為交易列管 | `CheckIsControl` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:909-913` |
| UI 統編輸入 | 客戶為員工 / 員眷 | `IsRelTrade` | 警示 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1086-1109` |
| UI 明細 | 扣款金額為必填 | 空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2076` |
| UI 明細 | 費率低於基金最低費率 / 高於牌告費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2376`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2395` |
| UI 明細 | 高收益基金未勾風險確認 / 無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2341`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2346` |
| UI 明細 | 扣款帳號已送核 / 已啟動重新送核 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2542`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2546` |
| UI 明細 | 本日已有相同基金扣款資料 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2153-2165` |
| UI 明細 | 有多筆未終止的契約資料 | `CheckSameData` > 0 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2289-2296` |
| UI 明細 | 扣款帳號核印失敗 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2169-2180` |
| UI 明細 | 優惠關係人又輸促銷活動 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2300-2309` |
| PO 新增 | 戶號在 `SrNoComment` 已被刪除過 | `CheckSrNoComment` | **形同無效**,見附錄 E | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2356-2372` |
| PO 新增 | 簡易開戶寫 `BMS001` 失敗 | `ExecuteNonQuery <= 0` | 阻擋(`throw`「新增BMS001失敗」) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:805-808` |
| PO 四眼各段 | 跳號紀錄寫入失敗 | `AddCommentHistory` 回 false | 阻擋,但 `throw new ApplicationException("")` **訊息是空的** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2588` |

#### `RSPB020` 與這一支的差別

`RSPB020` 用同一組 DataTable、同一套取數 SQL(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:116-370` 幾乎是 `RSPM004_PO` 的複製),但:

| 面向 | `RSPM004` | `RSPB020` |
|---|---|---|
| 可改什麼 | 全部 | **只有業務欄位**:銷售機構、通路、推薦人、員工、介紹人、郵局經辦區、備註 |
| 明細檢核 | `RSPM004p0` 3,089 行 | 沒有明細彈窗 |
| 存檔後動作 | 核印 + `OFD130A` / `OFD131A` | **PL/SQL 區塊同步更新 `OFD220A` / `OFD221A` / `OFD306A` 的同名業務欄位** |
| 錨點 | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:554-610`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:205-243` |

`OFD221A` 的更新多一條 `AND RSP_TYPE IN ('1','2')`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:587`)〔客戶特定〕;`OFD306A` 用 `WHERE EXISTS` 子查詢掛回申購書(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:599-610`)。**改契約的業務歸屬會連動改三張 OFD 交易表,這是 RSP 對 OFD 影響最大的一條路徑。**

### 4.2 `RSPM005` — 定期定額契約變更

#### 用途

客戶要換扣款銀行、改金額、改扣款日、改促銷活動、暫停、恢復、終止,全部走這支。它**不直接改契約**,而是開一張變更書(`RSP007A` + `RSP013A`),每一列都存「變更前」與「變更後」兩組值,等 `RSPB008` 到了生效日才把值套進 `RSP005A` / `RSP006A`(§6.2)。

規模:UI 1,678 行 + 明細彈窗 `RSPM005p0` 3,909 行(全模組單檔最大)+ PO 2,546 行。

#### 資料何時真的生效 —— 三個時間欄位

| 欄 | 誰寫 | 意義 |
|---|---|---|
| `CHG_DATE` | 畫面 | 異動收件日期。必須是營業日、且不可小於契約收件日期 |
| `ORG_CHG_EFFECT_DATE` | 畫面 | 原始變更生效日期 |
| `CHG_EFFECT_DATE` | 畫面 | 變更生效日期,**`RSPB008` 用它跟「今天」比對挑資料** |
| `CHG_UPD_DTTM` | 未見程式寫入 | 變更資料更新日期時間 |

流程是:輸入(`Status` 進待驗證)→ 驗證 → 覆核(`Status` 進已生效集合)→ **資料還沒生效** → `RSPB008` 在 `CHG_EFFECT_DATE` 當天(或之前)跑,SP 才把值搬進主檔 → 回寫 `RSP_CHG_CD`(異動成功否)與 `RSP_CHG_FAIL_CD`(異動失敗原因)。

**覆核完 ≠ 生效。** 這是這支畫面最容易誤解的地方,也是 `architecture.md §3.8.1`(「覆核完資料就生效」不是通則)在 RSP 的具體案例。要確認一張變更書到底套進去沒有,只能看 `RSP_CHG_CD`,或跑 `RSPR038`(定期定額契約異動資料查核表)。

#### 新增變更書前的兩道伺服端關卡

`RSPM005A_PO_BeforeAdd`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:407-464`):

**第一道:鎖契約。** `UPDATE RSP005A SET RSP_NO = RSP_NO WHERE RSP_NO = :RSP_NO`——一個不改任何值的 UPDATE,純粹為了在交易內鎖住那一列。影響列數 0 就 `throw`「鎖定契約書失敗,請檢查」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:416-420`)。契約書號不存在也會走到這裡,訊息會誤導。

**第二道:來源狀態檢核,但三個條件是 AND 串的。**

```
SELECT COUNT(*) FROM RSP005A
WHERE RSP_NO = :RSP_NO
  AND Status NOT IN (SELECT STATUS FROM TABLE(F_TA_GetEVAStatus('A')))
  AND NOT EXISTS (SELECT 0 FROM RSP008A WHERE RSP_NO = :RSP_NO)
  AND NOT EXISTS (SELECT 0 FROM RSP007A WHERE RSP_NO = :RSP_NO)
```

`> 0` 就 `throw`「契約書已被異動,尚未覆核,不可新增異動資料」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:423-436`)。

三條 AND 的意思是:**只有「契約尚未生效 + 從來沒扣過款 + 從來沒開過變更書」三者同時成立才會擋。** 也就是說,只要這張契約曾經開過任何一張變更書(`RSP007A` 有資料),這道檢核就永遠不成立,即使主檔現在正處於待覆核狀態。程式的區塊註解寫「檢查來源覆核,沒付過款,也沒異動過,也沒覆核的不可新增異動」,與訊息「契約書已被異動,尚未覆核,不可新增異動資料」互相矛盾——**訊息描述的情境(已被異動)正是會讓這條檢核失效的情境**。列入附錄 E。

#### 明細的三種狀態轉換

`BeforeSaveDetail`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:886-1360`)依 `RSP_CHG_CODE` 分流:

| 情境 | 區塊 | 錨點 |
|---|---|---|
| 設終止 | 寫 `STOP_ID` / `STOP_DATE` / `STOP_CD` 回 `RSP006A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:929-948` |
| 取消終止(原本終止,這次改成不終止,且是修改) | 還原 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:949-970` |
| 設暫停(狀態有效) | 寫 `STOP_BNG_DATE` / `STOP_END_DATE` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:971-1005` |
| 取消暫停(修改時) | 還原 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1006-1028` |
| 新明細 | 新增一列 `RSP006A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1029-1061` |
| 核印 | 取用戶號碼 → 處理 `OFD701` → 舊資料收尾 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1062-1360` |

`AfterApproveDelete`(刪除覆核後)要把終止 / 暫停還原,SQL 是這樣組的:

```
strSQL = "BEGIN " + this.CancelStop(row1);
strSQL += this.CancelStop(row1) == "" ? "" : ";";
strSQL += this.CancelPause(row1) + "END;";
if (strSQL != string.Empty) { … 執行 … }
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-583`。兩個問題:`CancelStop(row1)` 被呼叫兩次(第二次只為了判斷要不要加分號);而 `strSQL` 永遠至少是 `"BEGIN END;"`,所以 `if (strSQL != string.Empty)` **永遠成立**,那個守衛等於沒寫。兩段都空的時候會送一個空的 PL/SQL 區塊給資料庫。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 查詢條件必須擇一填寫 | 全空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:516` |
| UI 查詢 | 異動收件日期(起)(迄)必須皆填或皆不填 | 只填一邊 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:521` |
| UI 查詢 | 異動收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:525` |
| UI 存檔 | 異動收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:135` |
| UI 存檔 | 異動收件日期 < 契約收件日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:140` |
| UI 存檔 | 扣款日限額 | 超限 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:232` |
| UI 存檔 | 主檔沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:644` |
| UI 存檔 | 明細沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:807` |
| UI 存檔 | 不可異動「鎖利定額」契約 | — | **整段被註解,現在不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:248` |
| PO 新增 | 鎖不住契約列 | 影響 0 列 | 阻擋 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:419-420` |
| PO 新增 | 契約未覆核且無扣款且無其他變更書 | 三者同時成立 | 阻擋(條件過嚴,見上) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:435-436` |
| PO 四眼各段 | 跳號紀錄寫入失敗 | 回 false | 阻擋,訊息空白 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:559` |

### 4.3 `RSPM020` — 母子基金設定

#### 用途(推測)

168 循環定額投資法要先知道「哪些母基金可以配哪些子基金」。這支畫面就是那張白名單:一張 `RE_RSP_NO`(母子基金設定書號)底下,`RSP062A` 掛 N 檔母基金、`RSP063A` 掛 N 檔子基金,主檔再放兩個金額門檻。

這是全模組**最小的一支 M**:UI 436 行、PO 200 行、Control 116 行,沒有彈出視窗。

#### 主檔只有兩個業務欄位

| 欄 | 中文名 | 檢核 |
|---|---|---|
| `LOWER_LIMIT_AMT` | 最低申購金額 | 不可為 0 |
| `LOWER_SWITCH_AMT` | 最低轉申購金額 | 不可為 0 |

錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:382`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:390`。

`LOWER_LIMIT_AMT` 就是 `RSPM021` 在「合計金額低於母基金最低申購金額」那條檢核用的門檻(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267`)。

#### 兩個 grid,四條一模一樣的檢核

| grid | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| `ugrdMOM` | 母基金代碼為必填 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:398` |
| `ugrdMOM` | 母基金代碼重覆 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:403` |
| `ugrdMOM` | 母基金資料必須輸入(一列都沒有) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:408` |
| `ugrdSON` | 子基金代碼為必填 / 重覆 / 必須輸入 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:415`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:420`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:425` |

「必填」那兩條在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281` / `:293` 與 `:398` / `:415` 各寫了一次,一次在逐列事件、一次在存檔前,**兩套規則兩個地方**,改一邊會漏。

`App.config` 另外對兩個 grid 下了 `required="true"`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:169-170`),這是框架層的第三道。

#### 「執行類別」是死的

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:82` 有一行被註解掉的下拉設定(`GetDropDownDataSrc("309")` 綁 `EXE_TYPE`),`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` 有一條被註解掉的「執行類別 為必填欄位」。也就是子基金原本要分類別,後來取消了,但**欄位與檢核的外殼都留著**。

#### 伺服端

`RSPM020_PO` 只有 200 行,掛一個 `BeforeGetMaintainData` 組三段取數 SQL,沒有任何 `BeforeAdd` / `BeforeUpdate`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-120`)。**這支畫面在伺服端零卡控**,而它控制的是整條 168 業務線能配哪些基金——繞過 UI 就能塞任意基金代碼進去。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 逐列 | 母 / 子基金代碼未填 | 空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:293` |
| UI 存檔 | 最低申購金額 = 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:382` |
| UI 存檔 | 最低轉申購金額 = 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:390` |
| UI 存檔 | 母基金代碼重覆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:403` |
| UI 存檔 | 母基金一列都沒有 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:408` |
| UI 存檔 | 子基金代碼重覆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:420` |
| UI 存檔 | 子基金一列都沒有 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:425` |
| UI 存檔 | 執行類別未填 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` |
| PO | (無) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-38` |

### 4.4 `RSPM021` — 168 循環定額投資契約

#### 用途(推測)

168 循環定額投資法:客戶拿一筆既有的母基金申購書當本金,約定每月 6 / 16 / 26 日其中幾天,把母基金贖回一部分轉申購到指定的子基金;子基金漲到停利點就自動出場。這支畫面建立那張契約(`RSP070A` 主檔 + `RSP071A` 子基金明細 + `RSP072A` 綁定的申購書清單)。

規模:UI 2,309 行 + 彈窗 `RSPM021p0` 1,109 行 + PO 1,189 行。

#### 三層資料的意思

| 表 | 一筆代表 | 關鍵欄 |
|---|---|---|
| `RSP070A` | 一張 168 契約 | `MOM_FUND_ID` 母基金、`REDEM_DATE` 約定轉申購日(值域見 §2.5)、`RSP_EFFECT_DATE` 契約生效日、`FIRST_SUB_DATE` 首次轉申購日、`REDEM_FEE_RATE1`–`3`、`INVEST_TYPE` 投資型態、`GAIN_STOP` 終止停利設定 |
| `RSP071A` | 契約下的一檔子基金 | `SON_FUND_ID`、`RSP_AMT1` 約定轉申購金額、`LOCK_POINT` 停利點、`LOCK_FEE_RATE` 停利轉申購手續費率 |
| `RSP072A` | 綁定的一張母基金申購書 | `ALLOT_NO` + `ALLOT_SRNO` + `ALLOT_DATE`、`DATA_TYPE`、`REPRICE_DATE` 加碼生效日 |

`RSP_DATA` 是畫面上挑申購書用的暫存 DataTable(不是實體表),欄位有 `ISCHECK` / `ALLOT_AMT` / `PRE_ALLOT` / `ALLOT_PROC_CODE`(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:472`)。

#### 挑申購書那一段的四條檢核

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:225-300`(新增時)與 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:340-390`(修改時)是**兩份幾乎一樣的程式碼**:

| 檢核 | 成立時 | 結果 | 錨點(新增 / 修改) |
|---|---|---|---|
| 至少勾一筆申購明細 | 一筆都沒勾 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:253` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:354` |
| 新契約只能勾一筆 | 勾超過一筆 | 阻擋(訊息指路「如有多張申購書需透過異動作業作加碼」) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:256` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:356` |
| 合計金額 ≥ 母基金最低申購金額(`RSPM020` 設的 `LOWER_LIMIT_AMT`) | 低於 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:366` |
| 申購書已被贖回過不可當 168 資金 | `Chk_Allot_Partial` 回 true | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:278` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:377` |

**合計金額是用 `Convert.ToInt64` 累加的**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:242`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:246`),不是 `decimal`。`ALLOT_AMT` 為 0 時改抓 `PRE_ALLOT`(預估申購金額)。金額走整數型別在全庫是異數——`architecture.md §4.6` 實測「金額欄位沒有用 float / double,`Convert.ToDecimal` 3,029 次 vs `Convert.ToDouble` 18 次」,這裡是 `ToInt64`,小數會被四捨五入掉。列入附錄 E。

#### 首次轉申購日會被系統改掉,而且只是「通知」

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:282-295`:拿選到的申購書算出受短線交易 / 員工閉鎖限制後的最早可轉申購日,如果比畫面上填的還晚,跳一個 `Info01`:「首次轉申購日期未符合短線交易/員工閉鎖之限制日期,將被變更為 yyyy/MM/dd(次一扣款日)」——**只有訊息,使用者按掉之後值就被改了**,不是詢問也不是阻擋。歸類為「警示」。

另一條相關檢核在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1835`:「首次轉申購日期需大於【境內基金基本資料(OFDM081A)的『基本資料(一)畫面』的『開始買回日期』】!!」——這條是阻擋。

#### 刪除契約的兩道關

| 檢核 | 現況 | 錨點 |
|---|---|---|
| 契約申購明細資料已結轉不可刪除 | **整段被註解掉** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:660-679` |
| 該契約已執行扣款作業不可刪除(`ChkLOG095A`) | 有效 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:683-686` |

#### 其他值得記的檢核

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 查詢條件必須擇一填寫;收件日期(起)(迄)必須皆填或皆不填;(起) 不可大於 (迄) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:163`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:167`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:172` |
| 明細資料必須輸入 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1746` |
| 此推薦人不存在該通路代碼 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1765` |
| 收件日期須為營業日 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1799` |
| 系統未存在有效 KYC | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1809` |
| 子基金與受益人設定風險等級不符 | **被註解掉** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` |
| 高收益基金需先有風險預告書 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1828` |

注意 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` 那條**風險等級檢核在 `RSPM021` 被註解、在 `RSPM022` 卻是有效的**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:556`)。**新增契約時不擋風險等級,改契約時卻擋** —— 這個不一致列入附錄 E。

#### 伺服端

`RSPM021_PO` 掛了完整一套事件(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:40-79`),但 `BeforeAdd` 只做一件事:配契約書號(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:147-154`)。`BeforeUpdate` / `AfterAdd` / `AfterUpdate` 走 `BeforeSaveDetail`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:180-203`)。六個四眼後置事件跟 `RSPM004` 一樣只寫跳號紀錄(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:634-674`)。**沒有任何業務卡控在伺服端。**

#### `RSPB025` 與這一支的差別

`RSPB025` 用同一組 DataTable(`RSPM070_Master` / `RSPM070_Detail` / `RSP072`)、同一個 `App.config` 主檔宣告(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:121` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:177`),PO 也是 `RSPM021_PO` 的平行複製(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB025_PO.cs:37-39`)。差別在可改的欄位範圍與存檔後動作,跟 `RSPM004` / `RSPB020` 的關係一樣。**兩支要一起改。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:163` |
| UI 挑申購書 | 一筆都沒勾 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:253` |
| UI 挑申購書 | 新契約勾超過一筆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:256` |
| UI 挑申購書 | 合計金額低於母基金最低申購金額 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267` |
| UI 挑申購書 | 申購書有贖回紀錄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:278` |
| UI 挑申購書 | 首次轉申購日不符短線 / 閉鎖限制 | 成立 | 警示(值被改掉) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:286-291` |
| UI 存檔 | 明細資料必須輸入 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1746` |
| UI 存檔 | 推薦人不屬該通路 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1765` |
| UI 存檔 | 收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1799` |
| UI 存檔 | 無有效 KYC | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1809` |
| UI 存檔 | 高收益基金無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1828` |
| UI 存檔 | 首次轉申購日 ≤ 基金開始買回日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1835` |
| UI 存檔 | 子基金風險等級不符 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` |
| UI 刪除 | 已執行扣款作業 | `ChkLOG095A` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:683-686` |
| UI 刪除 | 申購明細已結轉 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:676-679` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:138-154` |

### 4.5 `RSPM022` — 168 循環定額投資契約變更

#### 用途(推測)

168 契約的變更書。結構跟 `RSPM005` 對 `RSPM004` 的關係一樣:`RSP073A` 主檔 + `RSP074A` 子基金變更明細 + `RSP075A` 追加的申購書,全部 `BEF_` / `AFT_` 成對,等 `RSPB023` 到了 `CHG_EFFECT_DATE` 才生效。

規模:UI 1,849 行 + 彈窗 `RSPM022p0` 1,329 行 + PO 1,047 行。

#### 可以改什麼

從 `RSP073A` 的 `CHG_xxx` 旗標欄反推,主檔層可改四項:

| 旗標 | 改什麼 | 前後欄 |
|---|---|---|
| `CHG_REDEM_DATE` | 約定轉申購日期 | `BEF_REDEM_DATE` / `AFT_REDEM_DATE` |
| `CHG_INVEST_TYPE` | 投資型態 | `BEF_INVEST_TYPE` / `AFT_INVEST_TYPE` |
| `CHG_AFEE_TYPE` | 手續費類型 | `BEF_AFEE_TYPE` / `AFT_AFEE_TYPE` |
| `CHG_REDEM_FEE_RATE` | 約定轉申購手續費率 1/2/3 | `BEF_REDEM_FEE_RATE1`–`3` / `AFT_REDEM_FEE_RATE1`–`3` |

明細層(`RSP074A`)可改:子基金代碼、約定轉申購金額(`CHG_RSP_AMT`)、停利點(`CHG_LOCK_POINT`)、停利轉申購手續費率(`CHG_LOCK_FEE_RATE`)、手續費類型、終止 / 恢復(`ISCHG_STOP_ID`)。錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:15`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:302`。

#### 主檔與明細的終止狀態要一致

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:714-724` 兩條對稱的檢核:

- 主契約已終止,明細不可有未終止的資料 → 阻擋

- 明細已終止,主契約不可未終止 → 阻擋

而 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945-970` 是寫值的那一段:`RSP_CHG_CODE == "A"`(新增子基金)或 `ISCHG_STOP_ID == "Y"` 時把 `STOP_ID` 清空,`STOP_ID` 是 `"N"` 或空字串都當「未終止」。**注意這裡同時接受空字串與 `'N'`,而 `RSPB021` 的 SQL 用 `NVL(TRIM(STOP_CD),'N') = 'N'` 判斷的是 `STOP_CD` 不是 `STOP_ID`** —— 兩個欄位、兩套判斷,不要混。

#### 加碼(追加申購書)

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:820-900` 是挑申購書的那一段,檢核與 `RSPM021` 同樣有「該筆申購書號有贖回紀錄」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:837`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:894`),多一條「未填附自主申購聲明書,無法申購!」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:853`)。

終止時的額外守衛:「明細資料已含新增資料,請先刪除新增資料後再行終止」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1511`)。

#### 一組被寫壞的訊息

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:350`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:569` 三處都是:

```
string.Format("未填附自主申購聲明書，無法申購!", d_Row.AFT_SON_FUND_ID)
```

格式字串裡**沒有 `{0}`**,所以傳進去的子基金代碼被丟掉。使用者看到的訊息不會告訴他是哪一檔基金出問題。三處都一樣,列入附錄 E。

#### 變更前後不可相同

跟 `RSPM042` 一樣有一支泛型 `Compare()`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 附近),逐欄比對,相同就報「變更前後的 X 不可相同」。主檔層另有「沒有變更任何欄位」的總檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:279`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:527`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:160` |
| UI 查詢 | 異動收件日期(起)(迄)未成對 / 起 > 迄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:165`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:169` |
| UI 存檔 | 沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:279`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:527` |
| UI 存檔 | 無有效 KYC | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:291`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:537` |
| UI 存檔 | 子基金與受益人風險等級不符 | 成立 | 阻擋(`RSPM021` 同條被註解) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:556` |
| UI 存檔 | 未填附自主申購聲明書 | 成立 | 阻擋(訊息漏基金代碼) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323` |
| UI 存檔 | 異動收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:706` |
| UI 存檔 | 異動收件日期 < 契約收件日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:711` |
| UI 存檔 | 主契約已終止但明細未終止 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:718` |
| UI 存檔 | 明細已終止但主契約未終止 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:723` |
| UI 挑申購書 | 申購書有贖回紀錄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:837` |
| UI 終止 | 明細已含新增資料 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1511` |
| UI 存檔 | 變更前後相同 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM022_PO.cs:48-50` |

### 4.6 `RSPM037` — 離職員工契約手續費率維護

#### 用途

員工與員眷享有優惠的契約手續費率。人離職後,這些契約的費率要調回一般水準。這支畫面就是幹這件事:輸入離職日期區間(或員工代碼),列出離職員工與員眷,雙擊某人帶出他名下的定期定額契約與基金明細,改 `RSP_CNRT_FEE_RATE`,按執行。

**它不維護 `COD009`。** 全支 PO 對 `COD009` / `COD010` 只有 `SELECT` 與 `JOIN`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:85-113`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:166-175`),唯一的 DML 是:

```
Update [RSP006]
   SET [RSP006].RSP_CNRT_FEE_RATE=@RSP_CNRT_FEE_RATE
      ,UpdateID=@UpdateID
      ,UpdateDate=GetDate()
 WHERE [RSP006].RSP_NO=@RSP_NO
   AND [RSP006].RSP_SRNO=@RSP_SRNO
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:271-276`。所以 §8.1 對 `cod.md` 那一側的答案是:**`COD009` 在 RSP 只是查詢條件的來源,不是被維護的主檔;母體的「主檔於 `RSPM037`」是照 `MasterTable` 宣告推出來的假象。**

#### 這支畫面是 M 代號、一步式外殼、零四眼

`public partial class RSPM037 : xOneStepProcessForm`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:21`),`App.config` 也宣告 `formstyle = OneStep`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:192`)。其餘七支 M 都是 `xMaintainForm`。

後果:**改費率不走四眼,按下執行就進資料庫。** 更新語句只寫 `UpdateID` / `UpdateDate`,不動 `Status` 也不走 `VerifyID` / `ApproveID`。這跟 `dsm.md §0.2` 記的 `DSMM906` 是同一類例外,但 `DSMM906` 至少 override 了 `Add` / `Update` / `Delete`;`RSPM037` 是連框架流程都沒進去。

#### 查詢:兩段 `UNION`,員工與員眷

```
-- 第一段:員工本人
FROM COD009 JOIN BMS001 ON COD009.EMP_ID_NO = BMS001.ID_NO
            JOIN RSP005 ON RSP005.BF_NO = BMS001.BF_NO
WHERE 1=1 AND EMP_CD='1' <離職日期 / 員工代碼條件>
UNION
-- 第二段:員眷
FROM COD010 JOIN COD009 ON COD010.EMP_NO=COD009.EMP_NO
            JOIN BMS001 ON COD010.REL_ID_NO = BMS001.ID_NO
            JOIN RSP005 ON RSP005.BF_NO = BMS001.BF_NO
WHERE 1=1 AND EMP_CD='1' <同樣的條件>
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:85-113`。三件事:

1. **`EMP_CD='1'` 是寫死的**〔客戶特定〕。

2. 兩段都是 `JOIN`(INNER),所以**沒有任何定期定額契約的離職員工不會出現在清單上**——這是合理的,但屬於「會把資料濾掉而不提示」。

3. 契約主檔查詢(`GetRSP005`)裡,原本有一條 `AND RSP005.RCV_DATE BETWEEN A.ENTRY_DATE AND A.LEAVE_DATE`,被註解掉並附註「user不想要此功能 20090716」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:176-177`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:243-244`)。**現在會列出該員工在職期間之外簽的契約**,包含離職後才簽的。

另有一處 `UNION` 的欄位別名寫錯:`UNION SELECT REL_ID_NO, ENTRY_DATE, LEAVE_DATE AS ID_NO`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:169`)——`AS ID_NO` 掛在 `LEAVE_DATE` 上。因為 `UNION` 取第一段的欄名,實際行為不受影響,但讀起來會誤導。

#### T-SQL 殘留:這支在 Oracle 上跑不起來(假設)

| 語法 | 錨點 |
|---|---|
| `CONVERT(NVARCHAR, x, 111)` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:64` |
| `[方括號]` 識別字 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:51`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:205` |
| `ISNULL(...)` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:152` |
| `f_GetAgent()`(T-SQL TVF,Oracle 版是 `TABLE(F_TA_GetAgent())`) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184` 對照 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:230` |
| `GetDate()` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274` |
| `SqlDbType.NVarChar` / `@參數` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:279-282` |
| 無 `A` 尾碼的表名 `RSP005` / `RSP006` / `BMS001` / `OFD019` / `OFD071` / `OFD072` / `OFD081` / `OFD199` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |
| 沒有 `[PODbType(DbServerType.Oracle)]` 屬性 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:17` |

**假設**:這支畫面在現行 Oracle 環境不可用。依據是上列語法在 Oracle 皆非法、`f_GetAgent()` 的 Oracle 版全庫寫法是 `TABLE(F_TA_GetAgent())`、且沒有任何其他 RSP 程式引用 `RSP005` / `RSP006` 這兩個表名。`architecture.md §4.6` 也記載全庫 `[PODbType(DbServerType.Oracle)]` 765 次、`MSSql` 只有 12 次。**無法實測,不敢斷言**;可能是這支功能早已停用,也可能是資料庫端真的還留著同名的 SQL Server 相容物件。

#### `Execute` 的失敗分支是死的

```
int o = base.ExecuteNonQuery(dbTA, cmd, tran);
o = 1;
if (o <= 0)
{
    tran.Rollback();
    … AddResultRow(false, 0, "執行失敗，請檢查");
    return mModel;
}
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-292`。`o = 1;` 把真實影響列數蓋掉,所以 `if (o <= 0)` 永遠不成立。**更新 0 列(例如 `RSP_NO` 打錯、或那張契約根本不存在)一樣回「執行成功」。** 這是 `dsm.md 附錄 E` 記的「一律回成功」在 RSP 的同型缺陷,而且比 DSM 那支更直接——DSM 是沒有檢查回傳值,這支是主動把回傳值蓋掉。

#### 明細彈窗的費率檢核

`RSPM037p1`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:43-70`):

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 契約手續費率 < 最低手續費率(用 `DataTable.Select` 做欄位對欄位比較) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:45-46` |
| 基金尚未設定牌告永久手續費率 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:61` |
| 契約手續費率 > 牌告永久手續費率 | 阻擋,**而且 `return` 直接中斷整個迴圈** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:63-67` |

最後一條的 `return` 讓使用者一次只看得到第一檔有問題的基金,改完再按一次才看到下一檔。同一個迴圈裡的另一條檢核(「尚未設定牌告費率」)則沒有 `return`,會繼續跑。兩條規則兩種行為。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 離職日期(起) > 離職日期(迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:39-42` |
| UI 查詢 | 員工沒有任何定期定額契約 | 成立 | 過濾(無提示,INNER JOIN) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:93-94` |
| UI 查詢 | `EMP_CD <> '1'` | 成立 | 過濾(無提示) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96` |
| UI 雙擊 | 此員工無契約書資料 | 成立 | 警示 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:125` |
| UI 執行 | 一筆都沒改 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:91-97` |
| UI 明細 | 費率低於最低手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:45-46` |
| UI 明細 | 未設定牌告永久手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:61` |
| UI 明細 | 費率高於牌告永久手續費率 | 成立 | 阻擋(中斷後續檢核) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:65-66` |
| PO 執行 | 更新 0 列 | — | **記錄不擋**(硬寫成功) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-292` |
| PO 查詢 | 契約收件日須在在職期間 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:177` |

### 4.7 `RSPM041` — 停利轉申購契約

#### 用途(推測)

幫一張既有的定期定額契約(`RSP_NO`)加掛「停利」設定:某檔基金的餘額漲到約定停利點(`P_RATE`)且超過門檻金額(`MIN_AMT`)時,自動贖回轉申購到 `SWITCH_FUND_ID`。一張 `RSP041A` 是一個設定,主鍵 `RSP_TRN_NO`(停利轉申購契約書號),沒有明細表。

UI 888 行、PO 481 行,無彈出視窗。

#### 主要欄位與檢核

| 欄 | 中文名 | 檢核 | 結果 | 錨點 |
|---|---|---|---|---|
| `MIN_AMT` | 門檻金額 | **必須 ≥ 10000**(寫死) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`〔客戶特定〕 |
| `P_RATE` | 約定停利點 | 必須 > 0 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:777` |
| `SWITCH_FUND_ID` | 轉出基金代碼 | 不可與 `FUND_ID` 相同 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:729` |
| `FEE_RATE` | 轉申購手續費率 | ≥ 基金最低費率;≤ 牌告費率;**不可超過牌告費率的對折** | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:816`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:836`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` |
| `FEE_RATE` | 同上 | 沒設自訂費率就報「自訂銷售手續費率尚未設定(OFDM193)」 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:846` |
| `RISK_CFD` | 風險確認 | 高收益基金必勾;受益人必須先有風險預告書 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:745`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:752` |
| — | 同一契約同一基金已有停利設定 | `CheckSameData` > 0 | 阻擋(「已有有相同交易資料,不可新增」,原文如此,多一個「有」) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |

「轉申購手續費率已超過上限之對折」那條寫成 `NoticeFeeRate * Convert.ToDecimal(0.5)`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841`),`0.5` 是 `double` 字面值再轉 `decimal`,值本身沒問題,但**「對折」這個係數寫死在程式裡**,不在任何設定表〔客戶特定〕。

#### 查詢條件

「停利書號, 收件日期(起、迄), 受益人ID, 戶號 必須擇一填寫」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:182`)+「收件日期(起) 不可大於 收件日期(迄)」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:193`)。

#### 伺服端

`RSPM041_PO` 481 行,只有取數與配號,沒有業務卡控(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42`)。`OFD138A`(收益分配行 / 帳號)被當唯讀參考表帶進 xsd(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:169`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 四個條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:182` |
| UI 查詢 | 收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:193` |
| UI 存檔 | 轉申購基金 = 基金代碼 | 停利機制為 `1` 時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:729` |
| UI 存檔 | 高收益基金未勾風險確認 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:745` |
| UI 存檔 | 高收益基金無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:752` |
| UI 存檔 | 門檻金額 < 10000 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765` |
| UI 存檔 | 約定停利點 ≤ 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:777` |
| UI 存檔(新增) | 已有相同交易資料 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |
| UI 存檔 | 費率低於最低 / 高於牌告 / 超過對折 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:816`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:836`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` |
| UI 存檔 | 未設定自訂銷售手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:846` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42` |

### 4.8 `RSPM042` — 停利轉申購契約異動

#### 用途(推測)

`RSP041A` 的變更書,主鍵 `TX_RSP_TRN_NO`(停利異動書號),掛回 `RSP_TRN_NO`。同樣 `xxx_BEF` / `xxx_AFT` 成對,等 `RSPB041` 在 `TX_DATE`(異動生效日期)當天生效。

UI 1,062 行、PO 519 行,無彈出視窗。

#### 三個明確的問題

**(1) 門檻金額的錯誤掛在錯的控制項上。**

```
if (this.unumMIN_AMT_AFT.Value != null)
{
    if (Convert.ToDecimal(this.unumMIN_AMT_AFT.Value) < 10000)
    {
        this.ValidateErrList.AddError(this.unumMIN_AMT_BEF, "門檻金額(變更後)必須大於等於10000");
    }
}
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:824-830`。判斷的是 `unumMIN_AMT_AFT`(變更後),但錯誤掛在 `unumMIN_AMT_BEF`(變更前)。使用者按錯誤清單會被帶到**唯讀的變更前欄位**。

**(2)「已有相同交易資料,不可新增」整段被註解。** `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:836-854`,與 `RSPM041` 的對應檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802`)形成落差:**建立停利設定時會擋重複,改停利設定時不會。**

**(3)「有沒有變更」是數變更前欄位。**

```
int n = 0;
if (this.unumMIN_AMT_AFT.Value != null) n++;
if (this.unumP_RATE_AFT.Value != null) n++;
if (this.custORG_FUND_ID.Value != string.Empty) n++;
if (this.custSWITCH_FUND_ID_BEF.Value != string.Empty) n++;   // BEF
if (this.unumFEE_RATE_BEF.Value != null) n++;                  // BEF
if (this.uoptJOB_CD_AFT.Value != this.uoptJOB_CD_BEF.Value) n++;
if (n == 0) { … "沒有變更任何欄位" … }
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:858-877`。六個條件裡兩個看的是 `_BEF`(變更前)欄位——變更前欄位本來就會有值,所以只要那兩個欄位非空,`n` 就不會是 0,「沒有變更任何欄位」這條**在大多數情況下不會成立**。而且 `if (n == 0)` 之後直接 `this.ValidateErrList.Show()` 卻沒有 `return`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875-877`),後面的 `Compare()` 還是會跑。

#### `Compare()` 的空值判斷

```
if (befObj == null || aftObj == null)
    IsEquals = (befObj == null ^ aftObj != null);
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1018-1019`。用 XOR 表達「兩邊都是 null 才算相同」。真值表算下來結果是對的(兩邊皆 null → `true ^ false` = true),但沒有人讀得懂,而且同一支檔案裡 `RSPM022` 版本的 `Compare()` 是同樣寫法(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 附近)。改的時候兩支都要改。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 四個條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:210` |
| UI 查詢 | 異動收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:221` |
| UI 存檔 | 轉申購基金(變更後) = 基金代碼 | 停利機制為 `1` 時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:816` |
| UI 存檔 | 門檻金額(變更後) < 10000 | 成立 | 阻擋(焦點掛錯欄位) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:828` |
| UI 存檔 | 沒有變更任何欄位 | 六個計數全 0 | 阻擋(條件不可靠,且無 `return`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875` |
| UI 存檔 | 變更前後相同 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1029` |
| UI 存檔 | 費率低於最低 / 高於牌告 / 超過對折 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:924`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:944`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:949` |
| UI 存檔 | 未設定自訂銷售手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:954` |
| UI 存檔 | 高收益基金未勾風險確認 / 無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:968`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:975` |
| UI 存檔(新增) | 已有相同交易資料 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:852` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM042_PO.cs:42` |

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

掃描母體 56 支畫面裡 I 是 0,實際比對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/` 也確實沒有任何 `RSPI*`。

原因(推測,三條依據):

1. **查詢需求被 31 支報表吸收了。** 其中至少兩支的行為就是查詢畫面:`RSPR064`「168循環定額投資法客戶查詢報表」(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR064.cs:106`)、`RSPR070`「業務受益人定額停扣明細報表」有四種標題可選並直接出 Excel(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:177-190`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:234-258`)。`RSPR049` 更是完全不出 Crystal Report,只吐 `.xlsx`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84`)。

2. **維護畫面自己就有夠強的查詢頁。** 八支 M 都是 `xMaintainForm`,第一個頁籤就是條件查詢 + 結果 grid,`App.config` 還替四支宣告了 `ugrdResult` 的欄位白名單(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:152`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:160`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:178`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:186`)。要查契約就開 `RSPM004` 查詢頁,不必另建 I。

3. **兩支掛 `xMaintainForm` 的 B(`RSPB020` / `RSPB025`)補上了「只想改業務欄位」的情境**,那本來也可能被做成 I + 另一支維護。

**要小心的是:因為沒有 I,所有「只想看不想改」的需求都是透過 M 畫面的查詢頁達成的,而 M 畫面的查詢頁沒有任何資料範圍權限**(不像 `dsm.md §5.3` 的 `DSMI001` 有 `CRM002A` 的權限 INNER JOIN)。RSP 的取數 SQL 一律 `LEFT JOIN` 對照表、`WHERE 1=1` 起手,能開畫面的人就看得到全部契約。功能權限由 PTPF 決定(`architecture.md §3.7`),資料權限在程式裡看不到。

## 6. 批次(B)與 WindowsService

```text
[圖] RSP 批次群與 RSPB008_Service 的觸發關係:兩個入口、排程來源、一日扣款鏈、三支變更生效批次
圖中文字:① 兩個入口打同一支 SP,但只有一個會擋未覆核 / RSPB008 畫面 / UI 到 Pxy 走 Remoting / CheckStatus / 未覆核就阻擋 / RSPB008_Ctl / Control 層 / s_TA_RSPB008_Excute_M / 版控外 SP / RSPB008_Service / Timer 60 秒 寫死 / 沒有 CheckStatus / 排程不擋未覆核 / ② 服務怎麼決定什麼時候跑、跑完做什麼 / CTL016.RSP_PROC_TIME / rownum=1 無 ORDER BY / 比對 HHmm / 相等才執行 / UserID = AutoJob / DATE = 今天 / Program.cs 無 UserName 判斷 / 只能當服務跑 / GetOFD681 / SEND_TYPE=6 寄信 / EventLog / Success / Error / C:/Vendor/WindowService/ / RSPB008_yyyyMMdd.txt / finally 再讀一次時刻 / 改設定不用重啟 / ③ 一日扣款鏈:八支批次,前一支沒跑後一支會被擋 / RSPB009 / 產生扣款 / RSPB010 / 送件 / RSPB011 B015 / 回覆確認 / RSPB016 / 單位數計算 / RSPB018 / 結轉 / RSPB019 淨值回復 / 回復後從 B016 重跑 / ④ 三支變更生效批次:結構相同,比較運算子不同 / RSPB008 / CHG_EFFECT_DATE 用 = / RSPB023 / CHG_EFFECT_DATE 用 <= / RSPB041 / TX_DATE 用 <= / 漏跑一天不會被補 / RSPB008 專有風險
```

*圖:圖 4 批次與服務。橘框=真正的關卡;橘虛框=風險或寫死值〔客戶特定〕;黑框=版控外。最重要的一條:RSPB008 畫面會先擋「還有未覆核的變更書」,RSPB008_Service 直接跳過那道檢核,時間到就跑,而且它不是 Remoting 客戶端,直接 new RSPB008_Ctl 在同一個行程裡打資料庫。*

17 支 B 裡:

- **2 支不是批次**(`RSPB020` / `RSPB025`,`xMaintainForm`),已在 §4.1 / §4.4 交代。

- **13 支只是 SP 的外殼**:自己開交易 → 呼叫 SP → 看回傳決定 commit / rollback。

- **2 支自己寫 DML**:`RSPB011`(扣款回覆逐筆確認)與 `RSPB052`(連續扣款失敗契約終止)。

- **1 支有專屬 WindowsService**:`RSPB008`。

### 6.1 共同模式一覽

| 畫面 | 觸發 | 主要輸入 | SP | 寫哪些表 | 執行前檢核 | 失敗處理 |
|---|---|---|---|---|---|---|
| `RSPB008` | 人工按執行 **或** `RSPB008_Service` 排程 | 變更生效日期、異動收件日期、契約變更書號 | `s_TA_RSPB008_Excute_M` | `RSP007A` `RSP013A` → `RSP005A` `RSP006A` | `CheckStatus`:`RSP007A` 還有非已生效狀態就擋(**服務端不跑這段**) | 讀 RefCursor 的 `UpdateTimes` / `CORRECT`;`OracleException` 回原訊息;其他例外回「執行失敗,請檢查」 |
| `RSPB009` | 人工 | 契約扣款日期、實際扣款日期、執行功能(產生 / 重作 / 刪除)、代理扣款機構、三種扣款方式勾選、基金明細逐檔勾選 | `S_TA_RSPB009_Excute`(**逐檔基金呼叫一次**) | `RSP008` `RSP008A` `CTL006A` | 契約扣款日期有效、註銷戶詢問、是否已有扣款日期 | 見 §6.4 |
| `RSPB010` | 人工 | 契約 / 實際扣款日、基金、扣款方式、扣款銀行、更新後實際扣款日與淨值日、需重新送件 | `EXEC s_RSPB010_Excute …`(**T-SQL 字串**) | `RSP008` | 淨值日已過帳 / 已結轉;實際扣款日已算淨值 / 已最後確認;已有扣款資料不做延遲扣款 | `ExecuteNonQuery` 回 0 就 rollback |
| `RSPB011` | 人工 | 逐筆勾選扣款成功 / 失敗 / 扣款中,含失敗原因 | **無**,自己寫 SQL | `RSP008A` | 小額扣款控制碼四段(見 §6.5) | `ExecuteNonQuery` 回 0 就「執行失敗,請檢查」 |
| `RSPB015` | 人工 | 扣款行、基金、確認 | `S_TA_RSPB015_Excute` | `RSP008A` | 無 | SP 的 `strMsg` OUT 非空就 rollback |
| `RSPB016` | 人工 | 基金、契約 / 實際扣款日 | `S_TA_RSPB016_Excute` | `RSP008A` | 「無符合資料可執行」 | 同上 |
| `RSPB018` | 人工 | 基金明細逐檔 | `S_TA_RSPB018_Excute`(**逐檔基金一個交易**) | `RSP008A`、`LOG017A` 讀 | `OFD303A.RSP_CTL_CODE` + 淨值一致性(見 §6.6) | `strMsg` OUT 非空就 rollback 並 `return` |
| `RSPB019` | 人工 | 基金、淨值、申購書號區間、回復說明 | `S_TA_RSPB019_Excute` | `RSP008AA` | 無 | `strMsg` OUT 非空就回訊息 |
| `RSPB021` | 人工 | 執行功能(扣款產生 / 刪除重作)、母基金、契約轉申購日 | `S_TA_RSPB021_EXCUTE` | 版控外 | `ValidateOFD303A`(母 + 子兩段);`ValidateLOG095A` **被註解** | `MSG` OUT 非空就 rollback |
| `RSPB022` | 人工 | 執行功能(停利計算 / 刪除重作)、標的基金、停利日期 | `S_TA_RSPB022_EXCUTE` | 版控外 | `ValidateLOG094A` + `ValidateOFD303A` | 同上 |
| `RSPB023` | 人工 | 異動生效日 | `S_TA_RSPB023_EXCUTE` | `RSP073A` `RSP074A` → `RSP070A` `RSP071A` | `CheckStatus`(查 `RSP073A`) | 同上 |
| `RSPB024` | 人工 | 基金、契約轉申購日 | `S_TA_RSPB024_EXCUTE` | 版控外(產 Email 資料) | 只擋「轉申購日須為 6/16/26」 | RefCursor 第一列 = 0 就回「無資料寄發」 |
| `RSPB041` | 人工 | 變更生效日期 | `S_TA_RSPB041_EXCUTE` | `RSP042A` → `RSP041A` | `CheckStatus`(查 `RSP042A`) | `MSG` OUT 非空就 rollback |
| `RSPB042` | 人工 | 執行功能、原始基金、停利日期 | `S_TA_RSPB042_EXCUTE` | 版控外 | `ValidateLOG109A` + `ValidateOFD303A` | 同上 |
| `RSPB052` | 人工 | 連續扣款失敗次數門檻、基金,逐筆勾選 | **無**,自己寫 SQL | `RSP007A` `RSP013A` `RSP005A` `RSP006A` | 無 | 見 §6.7 |

**「觸發」欄全部是人工**,只有 `RSPB008` 例外。repo 內沒有任何排程設定檔、`sc.exe` 呼叫或 Task Scheduler 匯出檔——除了那一支 WindowsService,RSP 的批次全靠人按按鈕。

### 6.2 `RSPB008` — 定期定額契約變更生效

#### 它到底做什麼

把已覆核的契約變更書(`RSP007A` + `RSP013A`)套用到契約主檔(`RSP005A` + `RSP006A`)。三個輸入參數(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:118-123`):

| 參數 | 畫面欄位 | 給 SP 的名字 | 說明 |
|---|---|---|---|
| `DATE` | 變更生效日期 | `datiDATE` | 挑 `RSP013A.CHG_EFFECT_DATE` 等於這天的 |
| `CHG_DATE` | 異動收件日期 | `datiCHG_DATE`(去掉 `/`) | `19000101` 代表不限 |
| `RSP_CHG_NO` | 契約變更書號 | `striRSP_CHG_NO` | 空字串代表不限 |
| `UserID` | — | `striUserID` | 畫面是 `base.UserID`,服務是字串 `"AutoJob"` |

SP 回一個 RefCursor,程式取第一列的兩個欄位(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:84-110`):

| 欄 | 用途 |
|---|---|
| `UpdateTimes` | 處理筆數。`0` → rollback,回「查無可執行之資料」 |
| `CORRECT` | `'Y'` → 有更新失敗的資料,訊息改成「執行完成 本次有更新失敗資料,請執行(RSPR038)定期定額契約異動資料查核表,查詢明細資料」,**而且 `ReturnCode` 給 `false`** |

`CORRECT = 'Y'` 時 `AddResultRow(false, 0, …)` 但**接著還是 `tran.Commit()`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:102-108`)。也就是「部分成功」被當成失敗回報,資料卻已經寫進去了。畫面端只有 `Result.Count == 2` 時才多跳一個訊息(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:128-131`),而 PO 永遠只 `AddResultRow` 一次,**那段畫面程式是死碼**。

#### 執行前檢核(只有畫面端跑)

```
SELECT COUNT(1)
  FROM RSP007A, RSP013A
 WHERE RSP007A.Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))
   AND (:CHG_DATE = '19000101' OR RSP007A.CHG_DATE = :CHG_DATE)
   AND RSP013A.CHG_EFFECT_DATE = :CHG_EFFECT_DATE
   AND RSP007A.RSP_CHG_NO = RSP013A.RSP_CHG_NO
   AND (:RSP_CHG_NO IS NULL OR RSP007A.RSP_CHG_NO = :RSP_CHG_NO)
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`。`> 0` 就回訊息「仍有資料未覆核,不可執行」,畫面把它塞進 `ValidateErrList` → 阻擋(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:48-52`)。

三件事:

1. `:RSP_CHG_NO IS NULL OR …` —— 畫面傳的是 `utxtRSP_CHG_NO.Text.Trim()`,沒填就是**空字串不是 NULL**。Oracle 把空字串當 NULL,所以這條碰巧成立;但同一支程式的 `CHG_DATE` 用的是哨兵值 `'19000101'`,兩種寫法混用。

2. 這是 `FROM A, B WHERE A.k = B.k` 的舊式 join 寫法,跟同模組其他地方的 `JOIN … ON` 不一致。

3. **`RSP013A.CHG_EFFECT_DATE = :CHG_EFFECT_DATE` 是等於不是小於等於**,跟 `RSPB023` / `RSPB041` 的 `<=` 不同(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:111`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:110`)。**漏跑一天,那天的變更書就不會被這條檢核看到**,下一次執行也不會被擋——三支同型批次三種比較運算子,列入附錄 E。

畫面另有兩條自己的檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:68-74`):變更生效日期不可為空、不可大於系統日。

#### 被註解掉的郵局限額檢核

`CheckDayLmtAmt` 在 PO 與 UI 兩側都被整段註解,PO 側註解標題寫「檢核郵局每日交易限額(改寫在 StoredProcedure 裡檢核)」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:54-66`)。被註解的那段是 T-SQL(`ISNULL` / `CONVERT(NVARCHAR,…,111)` / `@DATE`),讀 `OFD019.DAY_LMT_AMT`、用 `BankBizHelper.GetBankHQ` 判斷是不是郵局(`700`)。**現在這條規則只存在於版控外的 SP,repo 內查不到門檻值。**

### 6.3 `RSPB008_Service` — 唯一的 WindowsService

安裝方式、服務帳號(`LocalSystem`)、`InstallUtil` 指令與部署要帶的 DLL,`runbooks/deploy.md §5` 已經查過,**直接引用不重做**。這裡只補它做什麼、跟畫面的關係、以及執行模式怎麼判。

#### 它做什麼

| 階段 | 行為 | 錨點 |
|---|---|---|
| 建構 | 建一個 `System.Timers.Timer`,`Interval = 60000`(**寫死 60 秒**),`Enabled = true` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:23-27` |
| `OnStart` | 只做一件事:`GetTIMES()` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:29-33` |
| `GetTIMES` | `ctl.GetExecTime(view)` → PO 跑 `SELECT RSP_PROC_TIME FROM CTL016 where rownum=1`,把值存進欄位 `sTIMES`,並寫一筆 EventLog「Message:Next Execute Time is HHmm」 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:86-107`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:294-330` |
| 每 60 秒 | `if (sTIMES != "" && sTIMES == DateTime.Now.ToString("HHmm"))` 才動作 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:42` |
| 到點時 | 組四個參數 → `ctl.Execute(view)` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:46-54` |
| 執行後 | 不論成敗都呼叫 `ctl.GetOFD681(訊息)` 寄通知信 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:55-62` |
| 執行後 | 寫 EventLog(Success / Error)+ 寫檔到 `C://Vendor//WindowService//RSPB008//RSPB008_yyyyMMdd.txt` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:64-73`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:111-148` |
| `finally` | 再 `GetTIMES()` 一次,重新讀下一次的排程時刻 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:79-82` |
| `OnStop` | **空的** | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:35-38` |

服務固定送的三個參數(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:49-52`):

| 參數 | 值 | 意義 |
|---|---|---|
| `DATE` | `DateTime.Today`(`yyyy/MM/dd`) | 只處理「今天生效」的變更書 |
| `CHG_DATE` | `new DateTime(1900,1,1)` | 哨兵值,不限異動收件日 |
| `RSP_CHG_NO` | `string.Empty` | 不限單一變更書號 |
| `UserID` | **`"AutoJob"`** | 排程身分,會寫進 `RSP005A` / `RSP006A` 的 `UpdateID` |

#### 執行模式怎麼判:它根本不判

`runbooks/deploy.md §5.3` 記三支 `OFDB*` 服務用 `Environment.UserName == "SYSTEM"` 區分「服務模式」與「除錯模式」。**`RSPB008` 沒有這段。** 它的 `Program.cs` 只有:

```
ServicesToRun = new ServiceBase[] { new RSPB008_Service() };
ServiceBase.Run(ServicesToRun);
```

`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/Program.cs:22-24`。全專案 grep `Environment.UserName` 0 次。

實務上的三個結論:

1. **改服務帳號不會讓 `RSPB008` 啟動失敗**(那是三支 `OFDB*` 才有的雷),因為它無條件走 `ServiceBase.Run`。

2. **反過來,它也不能用命令列跑起來除錯。** 直接雙擊 exe 會被 SCM 拒絕(`ServiceBase.Run` 在非服務環境會失敗)。要驗證行為只能裝成服務,或改用 `RSPB008` 畫面手動跑同一支 SP。

3. **「什麼時候該執行」完全由 `CTL016.RSP_PROC_TIME` 決定**,不是由服務或設定檔決定。這張表 `SELECT … where rownum=1`,只認第一列(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302`),表內若有多列,哪一列被拿到取決於 Oracle 的回傳順序——**沒有 `ORDER BY`**。

#### 它跟 `RSPB008` 畫面的關係

同一支 `RSPB008_Ctl` / `RSPB008_PO` / 同一支 SP,兩個入口:

| 面向 | `RSPB008` 畫面 | `RSPB008_Service` |
|---|---|---|
| 呼叫層 | UI → `RSPB008_Pxy`(Remoting)→ Control → PO | **直接 `new RSPB008_Ctl()`,同一個行程** |
| `CheckStatus`(未覆核就擋) | 有 | **沒有** |
| 變更生效日期 | 使用者輸入,且會擋「不可大於系統日」 | 固定今天 |
| 異動收件日期 / 變更書號 | 使用者可縮小範圍 | 固定不限 |
| `UserID` | 登入者 | `"AutoJob"` |
| 寄通知信 | 不寄 | **每次都寄**(`OFD681` 的 `SEND_TYPE = '6'`) |
| 落地 log | 無 | `C://Vendor//WindowService//RSPB008//` + EventLog |
| 錨點 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:105-124` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:40-84` |

**最重要的一條:服務不做未覆核檢核。** 排程時間到了,不管 `RSP007A` 裡還有多少張沒覆核完的變更書,SP 照跑。要確認結果只能看 `RSPR038` 或那個 txt log。

#### 它不是 Remoting 客戶端,而且自帶連線字串

`architecture.md §8.4` 說四支服務都是 Remoting 客戶端、透過 `_Pxy` 打伺服端、不直接碰資料庫。**這句對 `RSPB008` 不成立**,三個證據:

| 證據 | 錨點 |
|---|---|
| 用的是 `RSPB008_Ctl`(Control 層)不是 `RSPB008_Pxy` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:47` |
| csproj 只參考 `Control.RSP` / `UIEntity.RSP` / `TA.MappingCode`,**沒有 `FormProxy.RSP`** | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/WindowsService.RSPB008.csproj:112-123` |
| 全專案 `RemotingConfiguration` 出現 0 次(對照 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50`) | grep 結果 |

它的 `App.config` 自帶五組連線字串,**含明碼帳密**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:72-78`):`SWProduct` / `TA` / `Logging` 指向 `AGITest` 的 `sa` / `sa`,`SWEMail` / `TIPS` 指向 `test002` 的 `TAAdmin`。這些是 `System.Data.SqlClient` 的 SQL Server 連線字串——與 PO 端 `new Database("TA", DbServerType.Oracle)` 不符,**假設**這幾組是舊環境殘留、實際連線由 PTPF 平台的設定接管;依據是 PO 建構子明確指定 Oracle,而這份 config 的值(`AGITest` / `sa` / `sa`)一看就是開發機。〔客戶特定〕

#### 值得寫成 runbook 的三個運維點

1. **改排程時間**:改 `CTL016.RSP_PROC_TIME`,服務**不用重啟**——每次執行完的 `finally` 都會重讀一次(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:79-82`)。但如果從沒執行過,只有 `OnStart` 那一次讀過,**改了要等下一次執行才生效,或重啟服務**。

2. **看它有沒有跑**:先看 EventLog(來源 = 服務名),再看 `C://Vendor//WindowService//RSPB008//RSPB008_<日期>.txt`。那個檔每次寫入會先把整份讀進來再整份重寫(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:133-146`),檔案大了會愈來愈慢,而且**沒有任何清檔機制**。

3. **`WriteLog` 用 `Encoding.Default`**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:135`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:141`),不是 UTF-8。中文在非 CP950 的機器上會變亂碼。

### 6.4 `RSPB009` — 產生扣款資料(逐檔基金呼叫 SP)

這支是扣款作業的起點,也是 17 支裡結構最特別的一支:**SP 不是呼叫一次,是對畫面上勾選的每一檔基金各呼叫一次,全部包在同一個交易裡**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:53-94`)。

三種執行功能(Designer 的 `valueListItem`):產生扣款資料 / 重作扣款資料 / 刪除扣款資料,用 `striADMINISTER` 傳給 SP。三種扣款方式(一般 / ACH / 財金)用三個獨立的 `striSEAL_CHK_CODE1`–`3` 傳。

#### 一個永遠不會被執行的 catch

```
catch (SqlException sqlex)
{
    if (Convert.ToString(sqlex.Number) == "2627")
    {
        … AddResultRow(false, 0, "扣款檔key值重覆，請先執行[刪除扣款資料]功能，再執行[產生扣款資料]功能");
    }
    …
}
catch (Exception ex)
{
    … AddResultRow(false, 0, "無符合查詢條件資料可執行。");
}
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109-131`。`SqlException` 是 SQL Server 的例外型別,`2627` 是 SQL Server 的唯一鍵違反錯誤碼。**這支 PO 掛 `[PODbType(DbServerType.Oracle)]`,實際走 Oracle,主鍵重複丟的是 `OracleException`(`ORA-00001`)。** 那個貼心訊息永遠不會出現;主鍵重複會掉進下面的通用 catch,使用者看到的是「無符合查詢條件資料可執行。」——**訊息與真因完全無關,而且會誤導作業人員以為是查詢條件的問題**。

同一個通用 catch 吞掉所有例外(連線斷、SP 不存在、參數型別錯)都回同一句話。列入附錄 E,嚴重度高。

#### 三道執行前檢核

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 契約扣款日期無效 | `GetSubDate` 查不到 | 阻擋 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:744` |
| 受益人為註銷戶 | 有 | **詢問**(「…為註銷戶是否繼續執行」) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:876` |
| 是否已有扣款日期 | 有 | 回筆數給畫面自行判斷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:933-938` |

#### 成功與否

`sb` 收集回傳 `CORRECT = 'N'` 的基金代碼,最後:

- `sb` 空 → 「執行成功」,`ReturnCode = true`

- `sb` 非空 → 「執行完成。基金[…] 無可<執行功能名稱>」,**`ReturnCode` 還是 `true`**

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:98-107`。也就是「部分基金沒資料」不算失敗——這是合理的設計,但要知道 `ReturnCode = true` 不代表每一檔都處理到了。

### 6.5 `RSPB011` — 扣款回覆逐筆確認(唯一自己寫 SQL 的回覆作業)

畫面提供「全部扣款成功」「全部扣款中」兩顆快速鈕,以及逐筆改 `SUB_STATUS` / `NONSUCS_CODE`(扣款失敗代碼),下方即時顯示成功 / 失敗 / 合計的筆數與金額。

執行前跑 `CheckSmallAmountCode`,四段檢核都回 `ReturnCode = true` 只是訊息不同(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:379-399`):

| 訊息 | 意思 |
|---|---|
| 契約扣款日期、實際扣款日期必須存在境內小額扣款日期控制檔 | 日期組合沒建在控制檔 |
| 基金[…]已做扣款回覆確認,不可再異動 | 已經跑過 `RSPB015` |
| 基金[…]已做單位數計算,不可再異動 | 已經跑過 `RSPB016` |
| 基金[…]已做結轉,不可再異動 | 已經跑過 `RSPB018` |

另有一條「此扣款行已作回覆確認,不可再異動」在 `Execute` 內(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:142`)。

**這四段檢核回的 `ReturnCode` 一律是 `true`**,靠訊息非空來判斷有沒有問題。跟 `RSPB008.CheckStatus` 是同一套約定(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:172`),但跟 `RSPB021.ValidateOFD303A`(有問題時回 `false`)相反(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:192`)。**同一個模組兩種相反的約定**,改的時候不要照抄隔壁那支。

### 6.6 `RSPB018` — 結轉(檢核訊息是在 SQL 裡拼出來的)

執行前的檢核不是 C# 寫的,是一大段 `CASE WHEN … THEN '訊息'` 直接在 SQL 裡產出中文訊息(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:78-102`):

| 條件 | 訊息 |
|---|---|
| `OFD303A.RSP_CTL_CODE = '3'` | 本日定期定額申購資料已結轉 |
| `OFD303A.RSP_CTL_CODE = '1'` | 請先執行單位數計算作業 |
| 存在 `RSP008A.NAV_B <> OFD081V.FUND_FACE_AMT` 的資料 | 有部份資料的淨值與目前的淨值不同,請重新執行單位數計算作業 |

執行時對每一檔基金**各開一個交易、各自 commit**,註解寫「20100531, Modify by rgb for 每一檔基金執行完成後即 Commit 以減少 Dead Lock 發生」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:209-241`)。後果:**跑到一半失敗,前面已經結轉的基金不會回滾**,只有當下那一檔 rollback 然後 `return`。這是刻意的取捨,但操作手冊必須寫清楚——重跑之前要先確認哪些基金已經結轉過。

跑完會去 `LOG017A` 查有沒有 `TRAN_TYPE = '1'` 的資料,有就在成功訊息後面加「,請列印法人公告警示表」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:243-264`)。

### 6.7 `RSPB052` — 連續扣款失敗契約終止(繞過四眼的那一支)

#### 它做什麼

畫面輸入「連續扣款失敗次數」門檻與基金,列出達標的契約明細,勾選後按執行。程式對每一筆(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:113-439`):

1. 用 `SerialNo.GetRspChgNoForNfd()` 配一張**契約變更書號**

2. 讀 `RSP005A` + `BMS001A` 組出主檔資料(`TRAN_TERM` 由 `BMS001A.TRAN_FAX_CD` 用 `DECODE` 轉)

3. `INSERT RSP007A`(變更主檔)

4. `INSERT RSP013A`(變更明細,`RSP_CHG_CODE = 'M'`,`CHG_EFFECT_DATE` = 今天)

5. `UPDATE RSP006A` / `UPDATE RSP005A` 設 `STOP_ID = 'Y'`、`STOP_CD = '01'`、`STOP_DATE` = 今天

#### 它把四眼欄位自己填成「已覆核」

```
UseCaseSecurity.SetFunctionSecurityData(row, mModel, EVAType.Add);
row.STATUS = "301";
row.APPROVEID = row.UPDATEID;
row.APPROVEDATE = row.UPDATEDATE;
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:134-137`。先用框架方法設四眼欄位,**再手動把 `STATUS` 蓋成 `'301'`、把覆核人蓋成自己**。產出的 `RSP007A` / `RSP013A` 一出生就是已覆核狀態,不會進任何人的待辦。

這是刻意的(批次終止不應該還要人覆核),但兩個後果要知道:

1. **`RSPB008` 的「仍有資料未覆核」檢核看不到這些變更書**,因為它們已經是已生效狀態。

2. **`'301'` 是寫死的字串**,如果哪天四眼狀態值域改了,這裡不會跟著改。同一個常數在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183` 與 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` 各寫了一次。

#### 跟 `RSPM037` 同型的「一律回成功」

```
int RSP005 = dbProduct.ExecuteNonQuery(cmdUpdRSP005, tran);
RSP005 = 1;
if (RSP005 <= 0) { … rollback … return … }
else { … AddResultRow(true, 1, "") … }
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:417-432`。**更新 0 列(契約已被別人終止、`RSP_NO` 不存在)照樣回成功,而且 `RSP007A` / `RSP013A` 的變更書已經寫進去了。** 結果是:資料庫裡有一張「終止」的變更書,主檔卻沒有被終止,兩邊對不起來。這是全模組最會咬人的一條,列入附錄 E。

注意同一支的 `INSERT RSP007A` 那段**沒有**被蓋掉回傳值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:164-172`),所以插入失敗會正確 rollback。**同一個方法裡兩種處理方式**。

#### 兩個交易、沒有分散式交易

`dbProduct`(業務庫)與 `dbPTPF`(配號 / 待辦庫)各開一個交易(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:110-111`),最後各自 commit(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:440-441`)。兩次 commit 之間若掛掉,會出現「號碼配掉了但變更書沒寫進去」。這是 `architecture.md §4.7` 記的全庫性問題,RSP 這支是其中一個實例。

#### 一行寫了兩次的參數

```
dbProduct.AddInParameter(cmdInsertRSP013, "CHG_UPD_DTTM", …); dbProduct.AddInParameter(cmdInsertRSP013, "CHG_UPD_DTTM", …);
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:193` —— 同一個參數在同一行加了兩次。Oracle 的 `ManagedDataAccess` 預設 `BindByName = false` 時會按位置綁,多一個參數就會讓後面所有參數錯位。目前這支能跑代表框架有設 `BindByName = true`(**假設**,依據是全模組大量使用具名參數且順序與 SQL 不一致),但這一行仍是明顯的複製貼上殘留。

### 6.8 三支「變更生效」批次的差異對照

| 面向 | `RSPB008`(一般契約) | `RSPB023`(168 契約) | `RSPB041`(停利契約) |
|---|---|---|---|
| 來源變更檔 | `RSP007A` + `RSP013A` | `RSP073A` | `RSP042A` |
| 生效日欄位 | `RSP013A.CHG_EFFECT_DATE` | `RSP073A.CHG_EFFECT_DATE` | `RSP042A.TX_DATE` |
| 檢核比較運算子 | **`=`** | `<=` | `<=` |
| SP | `s_TA_RSPB008_Excute_M` | `S_TA_RSPB023_EXCUTE` | `S_TA_RSPB041_EXCUTE` |
| 成敗判斷 | RefCursor 的 `UpdateTimes` / `CORRECT` | `MSG` OUT 參數 | `MSG` OUT 參數 |
| 有無 WindowsService | **有** | 無 | 無 |
| 畫面顯示結果 | `AfterExecuteButtonClicked` 判 `Result.Count == 2`(死碼) | 判 `!ReturnCode` 跳訊息 | 判 `!ReturnCode` 跳訊息 |
| 錨點 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:109-112` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:107-111` |

`RSPB023` 與 `RSPB041` 的 `Execute` / `CheckStatus` 是逐行相同的兩份程式碼,只差 SP 名、表名與參數名(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:41-131` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:41-130`),兩支 UI 也一樣(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB023.cs:40-92` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:40-92`)。連 `RSPB041` 的區塊註解都還寫著「檢核是否仍有未覆核的資料(RSP073A)」——**複製時沒改的註解**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:91`),實際查的是 `RSP042A`。

### 6.9 `RSPB021` / `RSPB022` / `RSPB042` 三支「刪除重作」模式

三支都有一個「執行功能」單選鈕:`1` = 正向執行(扣款產生 / 停利計算),其他值 = 刪除重作。UI 的前置檢核長這樣(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB022.cs:70-93`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB042.cs:63-86`):

```
if (TYPE == "1")
{
    … ValidateLOGxxxA(view);
    if (!view.Util.Result[0].ReturnCode)            // 已經跑過 → 擋
        AddError(udatCALC_DATE, view.Util.Result[0].ReturnMessage);
}
else
{
    … ValidateLOGxxxA(view);
    if (view.Util.Result[0].ReturnCode)             // 沒跑過 → 擋
        AddError(udatCALC_DATE, view.Util.Result[0].ReturnMessage);
}
```

意圖是對的(正向執行不能重複跑、刪除重作必須先跑過),**但 `else` 那一支用的訊息是空字串**:PO 在「沒跑過」時回的是 `AddResultRow(true, 0, "")`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:207`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:244`)。使用者選「刪除重作」而當天沒跑過時,錯誤清單會跳出一列**空白訊息**,完全不知道發生什麼事。三支都一樣,列入附錄 E。

`RSPB021` 更徹底:整段 `ValidateLOG095A` 的 UI 呼叫被註解掉,理由寫「SP已有檢核,故取消」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:67-91`)。PO 的 `ValidateLOG095A` 與 Proxy 的對應方法都還在,**是完整的死碼**;而 SP 內到底有沒有那道檢核,repo 內查不到。

### 6.10 批次的「一律回報成功」逐支檢查

17 支逐支查「呼叫 SP / 執行 DML 之後有沒有硬寫成功」:

| 畫面 | 有無 | 說明 |
|---|---|---|
| `RSPB008` | 否 | 依 `UpdateTimes` / `CORRECT` 判斷,但 `CORRECT='Y'` 時回 `false` 卻仍 commit |
| `RSPB009` | 部分 | 有基金沒資料時仍回 `ReturnCode = true`(設計如此);但 `SqlException` catch 是死的,真錯誤訊息會被換掉 |
| `RSPB010` | 否 | `p > 0` 才 commit |
| `RSPB011` | 否 | `ExecuteNonQuery` 回 0 就報失敗 |
| `RSPB015` | 否 | 依 `strMsg` OUT |
| `RSPB016` | 否 | 依 `strMsg` OUT |
| `RSPB018` | 否 | 依 `strMsg` OUT,但逐檔 commit |
| `RSPB019` | 否 | 依 `strMsg` OUT |
| `RSPB020` | 不適用(維護畫面) | — |
| `RSPB021` | 否 | 依 `MSG` OUT |
| `RSPB022` | 否 | 依 `MSG` OUT |
| `RSPB023` | 否 | 依 `MSG` OUT |
| `RSPB024` | 否 | 依 RefCursor 第一列筆數 |
| `RSPB025` | 不適用(維護畫面) | — |
| `RSPB041` | 否 | 依 `MSG` OUT |
| `RSPB042` | 否 | 依 `MSG` OUT |
| `RSPB052` | **是** | `RSP005 = 1;` 蓋掉 `ExecuteNonQuery` 回傳值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:418`) |

另外五支 SP 外殼(`RSPB021` / `RSPB022` / `RSPB023` / `RSPB041` / `RSPB042`)有一個共同的**回傳漏洞**:

```
T resultVdb = xVirtualDataBase.CreateNewVDB(mModel);
BasicModelVDB ResultVDB = resultVdb as BasicModelVDB;
…
catch (Exception ex)
{
    tran.Rollback();
    model.Utility.Result.Clear();
    model.Utility.Result.AddResultRow(false, 0, "執行失敗，請檢查");   // 寫進 model
    …
}
return resultVdb;                                                      // 回傳 resultVdb
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:42-98`。成功路徑把結果寫進 `ResultVDB`(會被回傳),**例外路徑卻寫進 `model`(不會被回傳)**。發生例外時呼叫端拿到的 `resultVdb` 裡 `Result` 是空的,畫面存取 `Result[0]` 會丟 `IndexOutOfRangeException`,使用者看到的是框架的通用錯誤,不是「執行失敗,請檢查」。五支一模一樣,列入附錄 E。

同五支的 `catch` 還都無條件 `tran.Rollback()` 而不檢查 `tran != null`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:87`),`BeginTransaction()` 本身失敗時會變成 `NullReferenceException` 蓋掉真因——`finally` 那邊倒是有做 null 檢查(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:95`),同一個方法兩種態度。

## 7. 報表(R)

31 支 R 畫面、39 個 `.rpt`、31 支報表 PO。

### 7.1 共同骨架

31 支長得幾乎一樣,四步:

| 步 | 做什麼 | 典型錨點 |
|---|---|---|
| 1 | `DoValidate()`:日期區間、必填 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:95` |
| 2 | `SetQueryParameters(rpt類別名, rpt檔名, 中文標題)` 決定要印哪一支報表 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:122` |
| 3 | `QueryVDB.Util.Parameters.AddParametersRow(…)` 逐一塞查詢條件 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:70-74` |
| 4 | PO 的 `GetData<T>` 呼叫 SP + `RefCursor` → `LoadDataSet` 進 typed DataSet | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:53-92` |

PO 這一層 31 支幾乎是同一份程式碼,只差 SP 名與參數清單。共同特徵:

| 特徵 | 統計 | 說明 |
|---|---|---|
| `cmd.CommandTimeout = 0` | **31 / 31** | 全部設成永不逾時,註解一律寫「此程式讓它永久跑」(`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:62`) |
| 取數 0 筆就 `AddResultRow(false, 0, "")` | 多數 | 「查無資料」與「執行失敗」用同一個回傳值表達 |
| `catch` 之後 `AddResultRow(false, 0, "")` | **28 / 31** | **例外訊息被吞掉,使用者看到的跟「查無資料」一模一樣** |
| 參數一律走 `SQLEVAHelper.GetParamValue(model, "名稱")` | 多數 | 有參數化,沒有字串串接 |

**28 支報表把例外與查無資料混為一談**,這是本章最大的問題:報表印不出來時,從畫面上分不出是「今天真的沒資料」還是「SP 掛了 / 參數型別錯 / 連線斷」。要判斷只能翻框架 log。

### 7.2 39 個 `.rpt` 與程式引用:完全對得上

實測比對 `Dev/ATLAS.RSP.Report/Source/CrystalReports/Report.RSP/*.rpt` 與 31 支 UI 內非註解的 `"RSPRxxxRPSn"` 字串:

| 項目 | 數量 |
|---|---|
| repo 內的 `.rpt` 檔 | 39 |
| 程式實際引用的報表類別名 | 39 |
| 有檔沒引用 | **0** |
| 有引用沒檔 | **0** |

**這一點跟 `dsm.md §7.2`(40 個檔、13 個引用的不在)完全相反**——RSP 的報表資產是乾淨的,不需要另外清。

31 支畫面對 39 個 rpt 的落差來自「一支畫面多個版型」:

| 畫面 | rpt 數 | 怎麼選 | 錨點 |
|---|---|---|---|
| `RSPR013` | 2 | 依排序方式(`uoptOrderType.CheckedIndex == 0`)二選一 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:76-81` |
| `RSPR017` | 3 | 依排序方式 `0` / `1` / `2` 三選一 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:115-126` |
| `RSPR020` | 2 | 同一組判斷在 `:249` 與 `:301` 寫了兩次 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR020.cs:249-251`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR020.cs:301-303` |
| `RSPR021` | 2 | 預覽 / 列印各一組判斷 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR021.cs:80-84` |
| `RSPR024` | 2 | 同 `RSPR020`,判斷寫兩次 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR024.cs:78-82`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR024.cs:108-112` |
| `RSPR060` | 2 | 依條件二選一,另有一處把報表名包成 `KeyValuePair` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:122-126`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:299` |
| `RSPR066` | 3 | 見 §7.4 |  |
| `RSPR049` | **0** | 不出 Crystal Report,直接吐 `.xlsx` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84-97` |

31 − 1(`RSPR049` 無 rpt)= 30 支有 rpt,其中 7 支各有 2–3 個版型,合計 30 + 9 = 39。**帳是平的。**

### 7.3 權限:程式裡一條都沒有

逐支檢查 31 支報表 UI 與 PO,**沒有任何**:

- 員工代號白名單(對照 `dsm.md §7.3` 的員編 `101722`)

- 列印帳號白名單(對照 `dsm.md` 的 `ntaprt05`–`ntaprt11`)

- 部門 / 銷售機構的資料範圍過濾

- `CRM002A` 之類的權限對照表 join

唯一跟身分有關的是把登入者當**參數**傳給 SP(例:`RSPB024` 的 `striUpdateID` 傳 `PermissionInfo[0].UserID`,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB024_PO.cs:55`),而報表 PO 連這個都沒有。

**結論:RSP 報表的資料範圍完全由版控外的 SP 決定,repo 內看不到任何限制。** 能開報表畫面的人看得到什麼,只能問 DBA。

### 7.4 三支值得展開的

#### `RSPR066` — 一次印三份報表,而且用空 `catch` 包起來

168 投資契約轉帳明細表有「成功 / 失敗」兩種,成功那份又依 `orderRep` 分「一般版(`RSPR066RPS`)」與「子基金合計版(`RSPR066RPS2`)」。畫面提供三種操作(`orderTYPE`):

| `orderTYPE` | 行為 | 錨點 |
|---|---|---|
| `"1"` 成功 | 依 `orderRep` 印 `RSPR066RPS` 或 `RSPR066RPS2` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:223-237` |
| `"2"` 失敗 | 印 `RSPR066RPS1` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:239-243` |
| 其他(全部) | **連續呼叫兩次自訂的 `doAct()`**:先印成功版,再印失敗版,最後 `e.Cancel = true` 取消框架原本的流程 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:183-218` |

「全部」那條路徑整段包在:

```
catch
{
    // pass
}
```

`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:205-208`。**空 catch,連註解都寫 `pass`。** 印到一半失敗(第二份報表取數炸掉、Crystal 載入失敗)使用者什麼都不會看到,只會覺得「怎麼只印出一份」。這是全模組唯一的空 catch,嚴重度高。

#### `RSPR034` — 「預覽」按鈕的分支被整段註解掉

`RSPR034_PO.GetData` 是一個 `switch ((BUTTON_TYPE)…)`,三個 case:

| case | 狀態 | SP | 錨點 |
|---|---|---|---|
| `PREVIEW` | **整段(約 55 行)被註解** | `s_RSPR034_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:137-192` |
| `MESSAGE` | 有效 | `s_RSPR034_1_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:194-200` |
| (第三個) | 有效 | `s_RSPR034_2_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:245-246` |

被註解的那一段還是 T-SQL(`@striSEND` / `SqlDbType.NVarChar`,`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:153`),代表它是 Oracle 移轉前就停用的。**`switch` 沒有 `default`**,所以 `BUTTON_TYPE` 若真的傳 `PREVIEW` 進來,會直接跳過整個 `switch`,`j` 維持 0,回「查無資料」——使用者看到的是「沒資料」而不是「這個功能已停用」。

#### `RSPR049` — 唯一不出 Crystal Report 的一支

「定期定額扣款檢核表」直接由 `pxy.GetExcelData(view)` 拿回 `byte[]`,存成 `.xlsx` 再 `Process.Start` 開檔(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:58-105`)。兩個要注意的:

1. **輸出前會在 client 端過濾促銷活動**:`RSPR049_SH1` 沒資料就把 `RSPR049_SH3` 整個清空;有資料就逐列用 `DataTable.Select("CAMPAIGN_CODE = '" + dr.CAMPAIGN_CODE + "' OR L_CAMPAIGN_CODE = '" + …)` 比對,對不到就 `dr.Delete()`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:60-76`)。**這是字串串接進 DataTable 的過濾式**,促銷代碼含單引號就會炸語法。

2. **`catch` 把 `ex.ToString()` 整包丟給使用者看**(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:102`),含完整堆疊。跟其他 30 支「什麼都不說」剛好相反。

### 7.5 報表對維護資料的關係

| 報表 | 看的是哪條線的資料 | 什麼時候該印 |
|---|---|---|
| `RSPR020` 契約資料查核表 | `RSP005A` / `RSP006A` | `RSPM004` 建檔後對帳 |
| `RSPR029` 契約異動項目統計表 · `RSPR038` 契約異動資料查核表 · `RSPR008` 異動資料轉入主檔報表 | `RSP007A` / `RSP013A` | **`RSPB008` 跑完必印 `RSPR038`**,那是唯一能看到 `RSP_CHG_CD` 失敗明細的地方(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:104` 的訊息直接指路) |
| `RSPR011` 申購扣款明細表 · `RSPR024` 申購扣款總表 · `RSPR013` 扣款銀行查核表 · `RSPR023` 保管銀行傳真表 | `RSP008` / `RSP008A` | `RSPB009` 產完扣款資料後 |
| `RSPR012` 扣款行回覆資料查核表 · `RSPR021` 扣款失敗明細表 · `RSPR028` 扣款失敗項目統計表 · `RSPR051` 扣款失敗通知書 | `RSP008A` | `RSPB011` / `RSPB015` 回覆確認後 |
| `RSPR048` 連續扣款失敗明細表 · `RSPR046` / `RSPR047` 契約終止原因統計 / 明細表 | `RSP005A` / `RSP006A` | `RSPB052` 終止前後 |
| `RSPR031` 收件通知書 · `RSPR034` 首次扣款通知書 | `RSP005A` | 對客戶寄發 |
| `RSPR060`–`RSPR066` 七支 | 168 那條線(`RSP070A`–`RSP075A`) | `RSPB021` / `RSPB022` / `RSPB023` 前後 |
| `RSPR041` / `RSPR042` / `RSPR043` | 停利那條線(`RSP041A` / `RSP042A`) | `RSPB041` / `RSPB042` 前後 |
| `RSPR070` 業務受益人定額停扣明細 · `RSPR071` 申請暫停扣款查核表 | 跨線 | 業務單位查詢用 |
| `RSPR049` 扣款檢核表 | `RSP008` + 促銷活動 | 對帳用,只出 Excel |
| `RSPR017` 受益人申購明細表 · `RSPR064` 168 客戶查詢報表 | 跨線 | 客服查詢用 |

### 7.6 畫面端的檢核

報表畫面的 `DoValidate()` 普遍只做兩件事:`validatorManager1.DataValidate()` 加日期區間比大小。兩個共同的小行為:

- **日期自動補齊**:填了起日沒填迄日,離開欄位時自動把迄日設成起日(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:87-93`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:108-113` 附近的 `_Leave` 事件)。

- **`Trim('0')` 處理選項值**:`RSPR017` 把 `RSP_TYPE` 的值做 `Convert.ToString(...).Trim('0')`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:130`)。選項值本身是 `"0"` 時會被 trim 成空字串,SP 收到的就不是「型態 0」而是「不限」。**這是字串處理取代值域對照的典型寫法**,列入附錄 E。

## 8. 跨模組共用

```text
[圖] RSP 四組跨模組關係:COD009 只讀、RSP005A/RSP006A 被 BMS 直接 MERGE、OFD272A 分區共用、OFD374A 條件寫入
圖中文字:A：COD009 —— RSP 是第四個碰它的地方,但只讀 / CODM009 CODB009 / COD 的兩個維護入口 / COD009 / 員工主檔 56 欄 / RSPM037 / RSP 側 xsd 只認 6 欄 / 唯一寫入是 RSP006 費率 / COD009 零寫入 / B：RSP006A / RSP005A —— 不是只有 RSP 在寫 / RSPM004 RSPB020 / RSP 的正規入口 / RSP005A RSP006A / 契約主檔與明細 / BMSB901A〔BMS〕 / MERGE INTO 兩張表 / 寫死 039 到 810 與 2017 日期 / 繞過變更書 / OFDI011 OFDB70x / 唯讀查詢與扣款送件 / C：OFD272A —— 靠 TRN_CD 分區,三個模組各用各的 / OFDM221A OFDM231A / 主檔在 OFD / OFD272A / 缺件資料 / RSPM004 RSPM005 / 當第二明細 / BMSM004 只寫 TRN_CD=5 / 各認各的代碼 / D：OFD374A —— dsm.md 說 RSPM004 會寫,但有兩道閘門 / DSMM060〔DSM〕 / 唯一正規維護入口 / OFD374A / 受益人歸屬業務員 / 閘門1 簡易開戶 / BF_NO = -1 才會走 / 閘門2 AUTO_BELONG_EMP=Y / 兩者都成立才 INSERT / 值來自 BMS001 那一列 / 狀態掛 BMSM001 的四眼
```

*圖:圖 5 跨模組。橘框=RSP 這一側的入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險或寫死值。B 那一組最會咬人:BMS 的 BMSB901A 直接 MERGE 進 RSP005A / RSP006A,不產任何變更書,查「扣款行怎麼被改掉的」時 RSP 這邊完全查不到痕跡。*

RSP 自己的表 19 張(`RSP005A` `RSP006A` `RSP007A` `RSP008` `RSP008A` `RSP008AA` `RSP013A` `RSP041A` `RSP042A` `RSP061A` `RSP062A` `RSP063A` `RSP070A` `RSP071A` `RSP072A` `RSP073A` `RSP074A` `RSP075A`,加上 `CTL006A`),借別人的 2 張(`COD009` / `OFD272A`),另外在程式裡碰到但母體沒列的還有 `OFD374A` `BMS001` `OFD130A` `OFD131A` `OFD132A` `OFD220A` `OFD221A` `OFD306A` `OFD303A` `OFD681` `OFD701` `COD010` `CTL014` `CTL016` `LOG017A` `LOG094A` `LOG095A` `LOG109A` 等。

### 8.1 `COD009`:RSP 是第四個碰它的地方,但只讀

`cod.md §8.2` 列了三個維護入口(`CODM009` / `CODB009` / `RSPM037`)並註明 `RSPM037` 是「只查不寫」,**與本文從 RSP 這側查到的結果一致**。補三件 COD 那側看不到的:

| 事實 | 說明 | 錨點 |
|---|---|---|
| `MasterTable` 換三次 | `RSPM037_PO` 在 `Select()` / `Select_Detail()` / `Select_Detail_D()` 三個方法各設一次,所以 `COD009` 只在第一次查詢時是「主檔」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| RSP 側的 `COD009` 只認 6 欄 | `EMP_NO` / `EMP_ID_NO` / `EMP_NAME` / `EMP_NAME_ENG` / `ENTRY_DATE` / `LEAVE_DATE`,沒有四眼欄;COD 側是 56 欄 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd:18` |
| `RSPM004` / `RSPB020` 也 join `COD009` | 只為了取 `EMP_NAME`,`LEFT JOIN` 不影響筆數 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:222-223` |
| `EMP_CD = '1'` 的過濾只有 RSP 這側有 | `cod.md §8.2` 列的八處寫死清單裡沒有這一條,它是 `RSPM037` 自己加的 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111`〔客戶特定〕 |

**改 `COD009` 要一起看的 RSP 側檔案**:`RSPM037Model.xsd`(6 欄的迷你定義)、`RSPM037_PO.cs`(兩段 `UNION` 的 T-SQL)、`RSPM004_PO.cs` / `RSPB020_PO.cs`(取員工姓名的 `LEFT JOIN`)。

### 8.2 `RSP006A` / `RSP005A`:BMS 會直接 `MERGE` 進來

母體只寫「`RSP006A` 也服務 BMS OFD」。實際反查:

| 模組 | 畫面 / 程式 | 動作 | 錨點 |
|---|---|---|---|
| **BMS** | `BMSB901A` | **`MERGE INTO RSP006A` 改扣款行、核印方式、核印狀態、核印日期;`MERGE INTO RSP005A` 在 `MEMO` 前面串一段說明文字** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169-196` |
| BMS | `BMSB901` | 同族的另一支,讀 `RSP006A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs` |
| BMS | `BMSM001` | 讀 `RSP006A` / `RSP007A` / `RSP008A` 判斷受益人有沒有在途的定期定額 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs` |
| OFDI | `OFDI011` | 讀 `RSP005A` / `RSP007A` / `RSP008A` / `RSP070A` / `RSP072A` / `RSP041A` 做整戶查詢 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:378`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1027-1028`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1050-1071` |
| OFDB | `OFDB050` `OFDB223` `OFDB485` `OFDB501` `OFDB701`–`OFDB705` | 扣款送件 / 核印往返的一整排批次,讀寫 `RSP007A` / `RSP008A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs` |
| OFD | `OFDM068` `OFDM231A` | 讀 `RSP005A` / `RSP070A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs` |
| Common | `BasicRSP_PO.GetRspData` | **全庫共用的契約下拉 / 查詢資料源**,`RSP005A JOIN RSP006A` 一次取 40 幾欄 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicRSP_PO.cs:46-70` |
| Common | `RSP_PO` / `RSP_Ctl` / `RSP_Pxy` / `RSP_MomToSonDataSrc` | 168 母子基金的共用資料源 | `Dev/Common/Source/DataSource/PO.DataSource/RSP_PO.cs`、`Dev/Common/Source/DataSource/UI.DataSource/TableSrc/RSP_MomToSonDataSrc.cs` |
| Common | `ucRSP_TRNData` / `ucTX_RSP_TRN_NOData` | 停利書號的共用查詢控件 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucRSP_TRNData.cs` |

#### `BMSB901A` 這一支要單獨講

它是一支**一次性的資料搬遷批次,但程式還留在系統裡**(`bms.md` 從 BMS 側寫過)。從 RSP 這側看,它做的事是:

```
MERGE INTO RSP006A A
  USING (SELECT a.rsp_no, a.rsp_srno, SEAL_STATUS FROM BMSB901A_LOG A WHERE A.DATAID = :DATAID) B
  ON (A.rsp_no = B.rsp_no and A.rsp_srno = B.rsp_srno)
  WHEN MATCHED THEN UPDATE SET A.SUB_BANK_CODE = '810',
                               A.SEAL_TYPE     = '3',
                               A.SEAL_STATUS   = B.SEAL_STATUS,
                               A.SEAL_RTN_DATE = '20171219',
                               A.SEAL_DATE     = '20171207', …
```

`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169-180`。

| 問題 | 說明 |
|---|---|
| **兩個日期是寫死的字串** | `SEAL_RTN_DATE = '20171219'`、`SEAL_DATE = '20171207'`——2017 年那次搬遷的日期。今天再跑一次,會把契約的核印日期寫成 2017 年 |
| 銀行代碼寫死 | 來源 `'039'`(澳盛)、目的 `'810'`(星展)、`SEAL_TYPE = '3'`(財金)全部寫死〔客戶特定〕 |
| `MEMO` 用字串串接 | `A.MEMO = '澳盛(039)由ACH票交所平台已改為星展(810)財金扣款平台;' \|\| nvl(TRIM(MEMO),'')`,重跑會重複串 |
| **暫存表 `DELETE` 不帶批號** | `begin DELETE BMSB901A_T1; DELETE BMSB901A_T2; end;`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:200-203`)——兩個人同時跑會互刪對方的暫存資料,即使前面的 `INSERT` / `SELECT` 都帶了 `DATAID` |

**對 RSP 的意義:`RSP005A` / `RSP006A` 不是只有 RSP 在寫。** 調查「契約的扣款行怎麼變成 810 了、誰改的」時,`RSP005A.UPDATEID` 會指向跑 `BMSB901A` 的那個人,而 RSP 這邊查不到任何變更書(`BMSB901A` 不產 `RSP007A`)。這是 RSP 側唯一一條**繞過變更書直接改主檔**的外部路徑。

### 8.3 `OFD272A`:RSP 是第三種用法

`bms.md §8.2` 已寫:主檔在 `OFDM221A` / `OFDM231A`,BMS 只寫 `SHORE_ID = '2'` 且 `TRN_CD = '5'` 那一批,**這張表靠 `TRN_CD` 分區使用**。

RSP 這側把它當 `RSPM004` / `RSPM005` 的第二明細(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149`),取數 SQL 在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:583-620`,存 / 刪在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1171-1186`。畫面上是「缺件」頁籤,由 `DoExp2` 開 `RSPM004p2` 維護(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:767-782`)。

RSP 側的 xsd 定義 24 欄(比 BMS 側多 `IsCheck` 與 `ACCOUNT_MEMO` 兩個畫面用欄位,`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1343`),主鍵宣告是 `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID`。**加欄位要同時改 OFD / BMS / RSP 三邊的 xsd**。

### 8.4 `OFD374A`:從 RSP 側驗證 `dsm.md §8.2`

`dsm.md §8.2` 寫「`RSPM004`(RSP)直接 `INSERT OFD374A`」,錨點 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700`。`bms.md §8.2` 也引了同一條。

**從 RSP 這側驗證:這件事成立,但有兩道閘門,`dsm.md` / `bms.md` 都沒寫。**

| 閘門 | 條件 | 錨點 |
|---|---|---|
| 1 | **必須走「簡易開戶」路徑**,也就是 `RSPM004_Master.BF_NO == -1` 或空字串(使用者輸入了一個系統查不到的統編) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:633` |
| 2 | **系統參數 `AUTO_BELONG_EMP` 必須等於 `'Y'`** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-698` |

也就是說:**幫既有受益人建定期定額契約,RSP 不會碰 `OFD374A`;只有「連受益人一起新開」而且開關打開時才會寫一筆。**

再補三件事:

1. **寫入的值從哪來。** `INSERT OFD374A` 的 `BF_NO` / `EMP_NO` / `BELONG_DATE` / 四眼 13 欄全部由 `SetBasicTableColumnAndData` 從 **`BMS001` 那一列** 的同名欄位綁過去(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:798`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2655-2694`),只有 `SAL_DEPT_NO` 被另外指定成 `RSPM004_Detail[0].EMP_DEPT_NO`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:800`)。**歸屬日期 `BELONG_DATE` 用的是 `BMS001.BELONG_DATE`,不是「今天」** ——這跟 `dsm.md §4.6` 記的 `DSMM060`「歸屬日期永遠是今天」不同。

2. **狀態跟著 `BMSM001` 的四眼走。** `Status` 來自 `UseCaseSecurity.SetFunctionSecurityDataInfo(BfRow, model, EVAType.Add, "BMSM001", …)`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:688`),用的是 **`BMSM001` 的功能代號**,不是 `DSMM060` 也不是 `RSPM004`。所以這筆 `OFD374A` 的待辦會掛在 `BMSM001` 的流程底下。

3. **`dsm.md §8.2` 的第 1 點(`DSMM060` 三個 INNER JOIN 查不到不合規的資料)對這批資料成立。** RSP 寫進去的 `SAL_DEPT_NO` 來自 `RSP006A.EMP_DEPT_NO`,只要這個部門不在 `OFD002`,`DSMM060` 就看不到、也改不掉。

**與 `dsm.md` 的結論比對:一致,本文只是把條件補完整。** 要改的話兩篇都要更新——`dsm.md §8.2` 與 `bms.md §8.2` 目前寫的是無條件 `INSERT`。

### 8.5 RSP 用到的共用 PO 與控件

| 共用元件 | 位置 | RSP 怎麼用 |
|---|---|---|
| `BasicRSP_PO` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicRSP_PO.cs:37` | 全庫要查「某受益人的定期定額契約」都走這支,`RSP005A JOIN RSP006A` |
| `RSP_PO` / `RSP_Ctl` / `RSP_Pxy` | `Dev/Common/Source/DataSource/PO.DataSource/RSP_PO.cs` | 168 母子基金與停利書號的共用資料源 |
| `RSP_MomToSonDataSrc` | `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/RSP_MomToSonDataSrc.cs` | 母基金→子基金的下拉連動,吃 `RSP070A` |
| `ucRSP_TRNData` / `ucTX_RSP_TRN_NOData` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucRSP_TRNData.cs` | 停利書號 / 停利異動書號的 searcher 控件,吃 `RSP041A` / `RSP042A` |
| `ClientBizUtility` / `ServerBizUtility` | `Dev/Common/Source/Utility/…` | `GetBusinessDay` / `GetFundBusinessDay` / `GetEMP_AGENT` / `GetSysParam` / `IsAgentFund` / `GetBF_FUND_RISK_ATTR` / `GetIS_PROINVEST`,RSP 幾乎每支畫面都在用 |
| `SerialNo` | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs` | `GetRspNoForNfd` / `GetRspChgNoForNfd` / `GetBFNo` / `GetRDRemitConfirmNo`,一律配 do-while 防撞號 |
| `SrNoCommentProcessor` | 框架 | 跳號一覽表;RSP 有四支畫面(`RSPM004` / `RSPM005` / `RSPM021` / `RSPB052` 間接)掛滿六個四眼後置事件 |
| `GenXMLHelper.Gen49` | `Dev/Common/Source/Utility/…` | `RSPB008_Service` 寄通知信 |
| `xTableHelper` / `xEVAStringHelper` | 框架 DLL,**無原始碼,從呼叫端反推** | `GetInsertString` / `SetEVAParameters` / `AllEVAColumnsForSelect` / `AppendToDoString` |
| `BaseEVADaoPO` / `BasicEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/` | 23 支 PO 走前者(新世代),`RSPB010_PO` / `RSPM037_PO` 走後者(舊世代) |

### 8.6 改動影響面速查

| 要改什麼 | 一定要一起看的 |
|---|---|
| `RSP005A` / `RSP006A` 加欄位 | `RSPM004Model.xsd` + `RSPB020Model.xsd` + `RSPB009Model.xsd` + `RSPB052Model.xsd` + `RSPM037Model.xsd`(五份 xsd,欄位集合都不一樣)、`BasicRSP_PO.GetRspData`、BMS 的 `BMSB901A` / `BMSB901` / `BMSM001`、OFDI 的 `OFDI011` |
| `RSP007A` / `RSP013A` 加欄位 | `RSPM005Model.xsd` + `RSPB008Model.xsd`、`RSPB052_PO`(它自己組 `INSERT`)、OFDB 的 `OFDB050` / `OFDB485` / `OFDB701`–`OFDB705`、`s_TA_RSPB008_Excute_M`(版控外) |
| `RSP008` / `RSP008A` 加欄位 | `RSPB009`–`RSPB019` 六份 xsd、OFDB 的 `OFDB485` / `OFDB501` / `OFDB703`、`OFDI011` |
| `RSP070A`–`RSP075A` 加欄位 | `RSPM021Model.xsd` + `RSPB025Model.xsd` + `RSPM022Model.xsd`、`RSP_MomToSonDataSrc`、`OFDM231A` / `OFDB223` / `OFDI011` |
| `RSP041A` / `RSP042A` 加欄位 | `RSPM041Model.xsd` + `RSPM042Model.xsd`、`ucRSP_TRNData` / `ucTX_RSP_TRN_NOData`、`OFDI011` |
| `COD009` 加欄位 | `cod.md §8.6` 為準;RSP 這側只要確認 `RSPM037Model.xsd` 那 6 欄還在 |
| `OFD272A` 加欄位 | OFD / BMS / RSP 三邊 xsd |
| `OFD374A` 加欄位 | `dsm.md §8.2`(`DSMM060` 的 xsd)+ `BMSM001Model.xsd` + `RSPM004Model.xsd` 的 `OFD374` DataTable |
| 改四眼狀態值域 | RSP 內有三處寫死 `'301'`:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |
| 改 `AUTO_BELONG_EMP` 的語意 | `bms.md §8.3`(BMS 兩支畫面把它寫成兩個相反常數)+ `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698` |

## 附錄 A. 資料表總表

### A.1 母體的 21 張表

| 表 | 中文名(推測) | 主檔於 | 明細於 | 跨模組 | 四眼 |
|---|---|---|---|---|---|
| `RSP005A` | 定期定額契約主檔 | `RSPM004` `RSPB020`(`RSPB009` 讀) | — | BMS OFD OFDB OFDI Common(§8.2) | 有 |
| `RSP006A` | 定期定額契約基金明細 | — | `RSPM004` `RSPB020` `RSPB009` | BMS OFD Common | 有 |
| `RSP007A` | 契約變更主檔 | `RSPM005` `RSPB008` | — | BMS OFDB OFDI | 有 |
| `RSP013A` | 契約變更明細 | — | `RSPM005` | — | 有 |
| `RSP008` | 扣款檔 | `RSPB010`(`RSPB009` 寫) | — | — | 有 |
| `RSP008A` | 扣款回覆 / 計算 / 結轉檔 | `RSPB011` `RSPB015` `RSPB016` `RSPB018` | — | BMS OFDB OFDI | 部分 |
| `RSP008AA` | 淨值回復檔 | `RSPB019` | — | — | 無 |
| `RSP061A` | 母子基金設定主檔 | `RSPM020` | — | — | 有 |
| `RSP062A` | 母基金清單 | — | `RSPM020` | — | 有 |
| `RSP063A` | 子基金清單 | — | `RSPM020` | — | 有 |
| `RSP070A` | 168 契約主檔 | `RSPM021` `RSPB025` | — | OFD OFDB OFDI Common | 有 |
| `RSP071A` | 168 契約子基金明細 | — | `RSPM021` `RSPB025` | — | 有 |
| `RSP072A` | 168 契約綁定申購書 | — | `RSPM021` `RSPB025` | OFDI | 有 |
| `RSP073A` | 168 契約變更主檔 | `RSPM022` `RSPB023` | — | — | 有 |
| `RSP074A` | 168 契約變更明細 | — | `RSPM022` | — | 有 |
| `RSP075A` | 168 契約變更申購書 | — | `RSPM022` | — | 有 |
| `RSP041A` | 停利轉申購契約 | `RSPM041` | — | OFDI Common | 有 |
| `RSP042A` | 停利轉申購異動 | `RSPM042` `RSPB041` | — | Common | 有 |
| `CTL006A` | 扣款日媒體產生控制 | — | `RSPB009` | 共用控制檔 | 無 |
| `COD009`〔共用〕 | 員工主檔 | COD 的 `CODM009` / `CODB009` | `RSPM037` 只讀 | COD | COD 側有,RSP 側 xsd 無 |
| `OFD272A`〔共用〕 | 缺件資料 | OFD 的 `OFDM221A` / `OFDM231A` | `RSPM004` `RSPM005` | OFD BMS OFDB OFDI NFD | 有 |

### A.2 母體沒列、但本文有提到的表

| 表 | RSP 怎麼碰 | 錨點 |
|---|---|---|
| `RSP005` / `RSP006`(無 A 尾碼) | `RSPM037` 專用的舊表名,只有這一支在用 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |
| `COD010` | 員眷,`RSPM037` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:106` |
| `BMS001` / `BMS001A` | 受益人;簡易開戶時寫,其餘只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:795`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:219` |
| `BMS005A` | 收益分配帳號,`AddOFD130A` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1239` |
| `OFD374A`〔共用〕 | 簡易開戶 + 開關打開時寫一筆 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700` |
| `OFD132A` | 簡易開戶時依 `OFD040A` 範本產 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741` |
| `OFD040A` | 對帳單寄送範本,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:788` |
| `OFD130A` / `OFD131A` | 匯款授權書與帳號,存檔後補建 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1212`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1228` |
| `OFD701` | 核印檔,讀 / 寫 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951` |
| `OFD220A` / `OFD221A` / `OFD306A` | `RSPB020` / `RSPB025` 連動更新業務欄位 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:561`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:574`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:588` |
| `OFD303A` | 關帳 / 結轉控制碼,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119` |
| `OFD315` | 受益人各契約各基金扣款次數(`DoExp3` 用) | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1464` |
| `OFD681` | 通知信收件人,`SEND_TYPE = '6'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `OFD081` / `OFD081A` / `OFD081V` | 基金主檔與 view,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:100` |
| `OFD302` / `OFD302A` | 淨值,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:60` |
| `OFD019` / `OFD019A` | 銀行總行,只讀(限額檢核已註解) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:242` |
| `OFD087` | 暫停扣款的基金 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:349` |
| `OFD041` | 說明範本(`GetPhraseItems`) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:610` |
| `OFD071A` / `OFD072A` / `OFD002` / `COD006A` | 通路 / 推薦人 / 部門 / 代碼說明,`LEFT JOIN` 唯讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:225-248` |
| `OFD138A` | 收益分配行 / 帳號,`RSPM041` / `RSPM042` 唯讀 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:169` |
| `OFD190` / `OFD199` | 促銷活動,唯讀 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:1289` |
| `OFD661A` | EC 契約異動,`CheckRspNO` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2538` |
| `CTL014` / `CTL015` / `CTL016` | 預設值 / 扣款帳號依據 / 排程時刻 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:302` |
| `LOG017A` | 法人公告,`RSPB018` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:245` |
| `LOG094A` / `LOG095A` / `LOG109A` | 三支停利 / 轉申購批次的執行紀錄,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:230`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:190` |
| `SrNoComment` | 跳號一覽表(PTPF 庫) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2360` |
| `LOG_RSP070A` | 168 契約異動 log,**repo 內唯一有 DDL 的 RSP 相關表** | `DB/Table/create_LOG_RSP070A.sql:2` |

`DB/Table/` 內與 RSP 有關的檔只有三個:`create_LOG_RSP070A.sql`(建表)、`update_rsp006a.sql`(一次性資料更新,把 `SUB_BANK_CODE` 從 `815` 改成 `012`)、以及兩支報表暫存表 `TA_RSPR011_BONUS_LIST.sql` / `TA_RSPR011_THREE_TEMP.sql`。**21 張核心表沒有任何一張的 DDL 在版控內。**

## 附錄 B. SP / Function / Trigger / View

掃描母體的 SP / Fn / Trigger / View 全部是 **0 筆**——不是沒有,是**全部不在版控內**。`DB/SP/` 底下唯一跟 RSP 沾邊的是 `S_OTA_OFDI011_GetRSPCHG.SQL`,而且屬於 OTA。

### B.1 Stored Procedure(從呼叫端反推,共 30 支)

| SP | 被誰呼叫 | 錨點 |
|---|---|---|
| `s_TA_RSPB008_Excute_M` | `RSPB008` + `RSPB008_Service` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:65` |
| `S_TA_RSPB009_Excute` | `RSPB009`(逐檔基金呼叫) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:57` |
| `s_RSPB010_Excute` | `RSPB010`(**T-SQL `EXEC` 字串**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:155` |
| `S_TA_RSPB015_Excute` | `RSPB015` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:318` |
| `S_TA_RSPB016_Excute` | `RSPB016` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:199` |
| `S_TA_RSPB018_Excute` | `RSPB018` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:203` |
| `S_TA_RSPB019_Excute` | `RSPB019` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:50` |
| `S_TA_RSPB021_EXCUTE` | `RSPB021` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:54` |
| `S_TA_RSPB022_EXCUTE` | `RSPB022` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB022_PO.cs:62` |
| `S_TA_RSPB023_EXCUTE` | `RSPB023` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:55` |
| `S_TA_RSPB024_EXCUTE` | `RSPB024` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB024_PO.cs:50` |
| `S_TA_RSPB041_EXCUTE` | `RSPB041` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:55` |
| `S_TA_RSPB042_EXCUTE` | `RSPB042` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:57` |
| `s_RSPR008_Get` | `RSPR008` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR008_PO.cs:52` |
| `S_TA_RSPR011_GET` | `RSPR011` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR011_PO.cs:60` |
| `S_TA_RSPR012_GET` | `RSPR012` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR012_PO.cs:48` |
| `S_TA_RSPR013_GET` | `RSPR013` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR013_PO.cs:62` |
| `s_TA_RSPR017_Get` | `RSPR017` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR017_PO.cs:69` |
| `S_TA_RSPR020_GET` | `RSPR020` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR020_PO.cs:60` |
| `S_TA_RSPR021_GET` | `RSPR021` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR021_PO.cs:60` |
| `s_RSPR023_Get` · `s_RSPR023_Count` · `s_RSPR023_Total` | `RSPR023`(**一支報表三支 SP**) | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:54`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:71`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:88` |
| `S_TA_RSPR024_GET` | `RSPR024` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR024_PO.cs:61` |
| `S_TA_RSPR028_GET` | `RSPR028` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR028_PO.cs:60` |
| `S_TA_RSPR029_GET` | `RSPR029` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR029_PO.cs:60` |
| `s_TA_RSPR031_Get` | `RSPR031` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR031_PO.cs:57` |
| `s_RSPR034_1_Get` · `s_RSPR034_2_Get` | `RSPR034`(`s_RSPR034_Get` 的分支被註解) | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:199`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:245` |
| `S_TA_RSPR038_GET` | `RSPR038` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR038_PO.cs:55` |
| `S_TA_RSPR041_GET` · `S_TA_RSPR042_GET` · `S_TA_RSPR043_GET` | `RSPR041` / `RSPR042` / `RSPR043` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR041_PO.cs:55`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR042_PO.cs:55`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR043_PO.cs:60` |
| `s_RSPR046_Get` · `s_RSPR047_Get` · `s_TA_RSPR048_Get` · `s_RSPR049_Get` · `s_TA_RSPR051_Get` | `RSPR046`–`RSPR051` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR046_PO.cs:43`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR047_PO.cs:46`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR048_PO.cs:65`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR049_PO.cs:47`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR051_PO.cs:51` |
| `S_TA_RSPR060_GET` – `S_TA_RSPR066_GET` | `RSPR060`–`RSPR066` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:60` 等 |
| `S_TA_RSPR070_GET` · `S_TA_RSPR071_GET` | `RSPR070` / `RSPR071` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR070_PO.cs:60`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR071_PO.cs:60` |

命名有三種風格:`S_TA_RSPxxx_GET`(大寫)、`s_TA_RSPxxx_Get`(混合)、`s_RSPxxx_Get`(無 `TA_`)。前者是新世代,後兩者是舊的。grep 時三種都要試。

### B.2 Function / View

| 類 | 名稱 | 用途 | 錨點 |
|---|---|---|---|
| TVF | `f_TA_GetEVAStatus('A')` | 取「已生效」的四眼狀態集合 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:154` |
| TVF | `F_FormatStringToTable(:DAY)` | 把逗號字串切成表,`CheckSameData` 用 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2396` |
| TVF | `F_TA_GetAgent()` | 銷售機構(Oracle 版) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:230` |
| TVF | `f_GetAgent()` | 銷售機構(**T-SQL 版,只有 `RSPM037` 用**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184` |
| Fn | `f_TA_GetBusinessDay(日期,'1',0)` | 營業日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:121` |
| Fn | `f_TA_GetFNBusinessDay(基金,'2'/'3',日期,0)` | 基金營業日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:122` |
| Fn | `f_TA_GetNavDate(基金,日期,'2')` | 淨值日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:123` |
| Fn | `dbo.f_GetBankHQ(SUB_BANK_CODE)` | 總行代碼(**T-SQL,`dbo.` schema**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:425` |
| View | `OFD081V` | 基金主檔 view,取 `FUND_FACE_AMT` / `DEC_LEN` / `FUND_STATUS` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:100` |

**Trigger:repo 內找不到任何 RSP 相關 trigger 的引用。**

## 附錄 C. 代碼對照

| 代碼欄 | 值 | 意義 | 來源 |
|---|---|---|---|
| `Status`(四眼) | 見 `architecture.md §3.10` | — | 框架 |
| `Status` 寫死值 | `'301'` | 已覆核 / 生效 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135` |
| `REDEM_DATE`(168 約定轉申購日) | `1`–`7` | 6 / 16 / 26 日的七種組合,見 §2.5 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128` |
| `RSP_ACCT_BY` | `'1'` 依主檔 / `'2'` 依明細 | **永遠是 `'2'`**,`'1'` 的功能未完成 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:35`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212` |
| `SEAL_TYPE` | 一般 / ACH / 財金 | 三種扣款媒體,`RSPB052` 寫死 `'3'`=財金 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:175` |
| `SUB_STATUS`(扣款進度) | `'0'` / `'1'` 尚未回報 · `'2'` / `'3'` 已回報 | 由 `RSPB015` 的檢核訊息反推 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:69-70` |
| `SUB_STATUS`(OFDI 側) | `'0'` `'1'` `'2'` 走 `CTL014` 對照;`'3'` 走 `COD006A` | 失敗才有原因碼 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1070-1071` |
| `CTL006.RSP_CTL_CODE` | `0` 未處理 · `1` 扣款行皆已回覆 · `2` 已執行單位數計算 · `3` 已結轉 | 由 `RSPB009` 的檢核訊息反推 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:360-362` |
| `OFD303A.RSP_CTL_CODE` | `'1'` 請先執行單位數計算 · `'3'` 本日已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:80-81` |
| `OFD303A.REDEM_CTL_CODE` | `'4'` 買回關帳已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148` |
| `OFD303A.ALLOT_CTL_CODE` | `'3'` 申購關帳已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:150` |
| `OFD081.FUND_STATUS` | `'0'` 正常,其餘代表已清算或合併 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:65` |
| `STOP_ID` / `STOP_CD` | `'N'` 或空 = 未終止;`'Y'` = 終止 | `RSPB052` 終止時寫 `STOP_CD = '01'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:412-413` |
| `RSP_CHG_CODE` | `'A'` 新增 · `'M'` 修改 | `RSPB052` 產出的變更明細固定 `'M'` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:188` |
| `ISCHG_STOP_ID` | `'Y'` / `'N'` | 這列有沒有改終止設定 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:554` |
| `TRAN_TERM` | `BMS001A.TRAN_FAX_CD = 'Y'` → `'2'`,否則 `'1'` | 交易方式 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:127` |
| `SOURCE_CD` / `SYSTEM_ID` | `RSPB052` 寫死 `'1'` / `'0'` | 資料來源碼 / 交易途徑 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:158-159` |
| `OFD681.SEND_TYPE` | `'6'` = RSPB008 通知信群組 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `COD009.EMP_CD` | `'1'` = 算員工 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96` |
| `COD006A.CODE_SORT` | `'42'` = 定期定額終止原因 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:247` |
| `CTL014` 序號 | `065` `066` `069` `070` `078` `079` `081` `083` | 簡易開戶八個預設值 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684` |
| 銀行代碼 | `'700'` 郵局 · `'039'` 澳盛 · `'810'` 星展 · `'815'` / `'012'` | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:174`、`DB/Table/update_rsp006a.sql:1` |
| 促銷活動 | `'86A03'` | `RSPM004` 有專屬檢核 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785`〔客戶特定〕 |
| 門檻金額 | `10000` | `RSPM041` / `RSPM042` 的停利門檻下限 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`〔客戶特定〕 |
| 轉申購日 | `6` / `16` / `26` | 168 的固定三天 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:61`〔客戶特定〕 |

## 附錄 D. 掃描母體與覆蓋率

### D.1 母體

`docs/_candidates/rsp.md`:畫面 56(B 17 / I 0 / M 8 / R 31)· 表 21 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 39 · Service 1。

重跑:

```
py -V:3.12 /docs/tools/atlas_scan.py --module RSP --doc /docs/modules/rsp.md
```

### D.2 母體有五處與程式不符,以程式為準

| 母體說 | 程式實際 | 依據 |
|---|---|---|
| `COD009` 主檔於 `CODB009` `CODM009` **`RSPM037`** | `RSPM037` **只讀不寫**,`MasterTable` 是在 `Select()` 方法內指定的,而且後面還被換成 `RSP005` / `RSP006` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| `RSPB020` / `RSPB025` 是 B(批次) | 兩支都是 `xMaintainForm`,走完整四眼,是維護畫面 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:23`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB025.cs:24` |
| `RSPB008` 主檔 `RSP007A`、無明細 | `RSP013A` 的明細宣告存在但被註解;實際的 `RSP013A` 處理在 SP 內 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:44` |
| `RSP006A` 只服務 BMS / OFD | BMS 的 `BMSB901A` 會 **`MERGE INTO`** 它與 `RSP005A`,不是唯讀 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:189` |
| `RSPM037` 主檔 `COD009`,沒有提到 `RSP005` / `RSP006` | 這兩張**無 A 尾碼**的表只有 `RSPM037` 在用,掃描器沒把它們算進 21 張 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |

### D.3 「六層齊」的兩個補充

母體說 56 支全部六層齊。實測補兩件事:

1. **`RSPB010` 與 `RSPM037` 的 PO 層是舊世代基底**(`BasicEVAPO`)而不是新世代的 `BaseEVADaoPO`,而且兩支都沒有 `[PODbType(DbServerType.Oracle)]` 屬性。25 支 PO 裡只有這兩支是這樣。六層數量齊,**世代不齊**。

2. **`RSPM037` 的 UI 層是 `xOneStepProcessForm`**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:21`),其餘七支 M 都是 `xMaintainForm`。六層齊,**型別不齊**。

### D.4 39 個 rpt 對得上程式

見 §7.2 的實測:有檔沒引用 0、有引用沒檔 0。**這一點跟 DSM 相反**(`dsm.md §7.2` 記 40 個檔有 13 個引用不在)。

### D.5 本篇引用的覆蓋率

`atlas_scan.py --module RSP --doc docs/modules/rsp.md` 的結果貼在下方(重跑時請一併更新):

- 表:母體 21 張,本文全數提及(含 `RSP008AA` 與 `CTL006A`)。

- 畫面:母體 56 支,本文全數提及。8 支 M 一支一節(§4),17 支 B 全列在 §3.3 與 §6.1 的表內並展開 6 支,31 支 R 全列在 §3.4 與 §7 的表內並展開 3 支。

- rpt:39 個全數對應到畫面(§3.4 / §7.2)。

- Service:1 支,§6.3 專節。

### D.6 未被本文展開、但已在清冊裡處置的項目

| 項目 | 處置 |
|---|---|
| `RSPB016` / `RSPB019` | 只在 §6.1 的共同模式表出現;兩支都是單純的 SP 外殼,沒有畫面端業務邏輯 |
| `RSPR008`–`RSPR071` 的 28 支 | 只在 §3.4 與 §7.5 出現;結構與 §7.1 的骨架一致,差別僅在 SP 名與參數 |
| `RSPM004p1`(25 行) | 幾乎是空殼,只有建構子與一個事件 |
| `RSPM005p2` / `RSPM005p3`(84 / 33 行) | 小型彈窗,無業務卡控 |
| `RSPB019p0`(74 行) | 回復說明範本挑選,無業務卡控 |

### D.7 怎麼自己重跑

```
py -V:3.12 /docs/tools/atlas_scan.py --module RSP
py -V:3.12 /docs/tools/atlas_scan.py --module RSP --doc /docs/modules/rsp.md
py -V:3.12 /docs/tools/atlas_build_doc.py /docs/modules/rsp.md --repo-root  --report /docs/modules/rsp.refcheck.md
```

## 附錄 E. 讀本文時要注意的地方

### E1 會直接產生錯誤資料的五條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `RSPB052` 把 `UPDATE RSP005A` 的影響列數硬寫成 `1`(`RSP005 = 1;`) | 契約主檔沒被終止(已被別人終止 / `RSP_NO` 不存在)照樣回成功,而 `RSP007A` / `RSP013A` 的終止變更書已經寫進去。**資料庫出現「有終止變更書、主檔沒終止」的不一致,而且沒有人會知道** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:417-418` | **高** |
| 2 | `RSPM037.Execute` 同樣把 `ExecuteNonQuery` 回傳值蓋成 `1`(`o = 1;`) | 手續費率更新 0 列照樣回成功。離職員工的優惠費率沒被調回,作業人員以為改好了 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-284` | **高** |
| 3 | 五支 SP 外殼在 `catch` 裡把錯誤寫進 `model`,卻回傳 `resultVdb` | 例外發生時回傳的 VDB 沒有任何 `Result` 列,畫面讀 `Result[0]` 會 `IndexOutOfRangeException`。**批次失敗時使用者看到的是框架的通用錯誤,不是「執行失敗,請檢查」** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:85-98`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB022_PO.cs:92-103`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:81-95`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:80-94`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:87-101` | **高** |
| 4 | `RSPB009` 的 `catch (SqlException)` 在 Oracle 環境永遠不會被觸發 | 主鍵重複(ORA-00001)掉進通用 catch,使用者看到「無符合查詢條件資料可執行。」——與真因完全無關。寫好的指引訊息「請先執行[刪除扣款資料]功能」永遠不會出現 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109-131` | **高** |
| 5 | `RSPB008` 在 `CORRECT = 'Y'`(有更新失敗資料)時回 `ReturnCode = false` **但仍然 `tran.Commit()`** | 「失敗」與「已寫入」同時成立。作業人員看到錯誤訊息可能會重跑一次,造成重複處理 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:102-108` | **高** |

### E2 Oracle 三值邏輯:`<> '值'` 抓不到 NULL

跟 CAS / CLS / DSM / BBS 四個模組一樣的型。RSP 有 **4 處沒有包 `NVL`**:

| 位置 | 判斷式 | 後果 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:338` | `TABLE_NavDate.FUND_STATUS <> '0' THEN '該基金已清算或合併,不可執行'` | `FUND_STATUS` 為 NULL 時整條 `CASE WHEN` 是 UNKNOWN,**已清算的基金會被放行產生扣款資料** | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:65` | 同上,訊息「不可執行單位數計算」 | 同上 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:53` | 同上,訊息「不可執行定期定額申購結轉」 | 同上 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:489` | `WHERE SUB_STATUS <>'0'` | `SUB_STATUS` 為 NULL 的列被靜默濾掉 | 中 |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:531` | `AND RSP013A.RSP_CHG_CODE <>' '` | 同上 | 中 |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:82` | `AND CTL006.RSP_CTL_CODE <> '0'` | 同上 | 中 |

**同一支 `RSPB009` 的其他十幾條判斷都有好好寫 `NVL(x,' ') <> ' '`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:342`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:360-371`),所以上面那三條「基金已清算」是漏網的,不是全域慣例。

### E3 `NVL(x, '') = ''`:在 Oracle 永遠是 UNKNOWN

```
WHEN ((NVL(CTL006.FUND_ID,'')='') AND OFD303A.RSP_CTL_CODE <> '0')
     THEN '本基金於CTL006中，無此實際扣款日期的資料，請洽MIS人員'
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:64`。Oracle 把空字串當 NULL,所以 `NVL(x,'')` 等於 `NVL(x, NULL)` 等於 `x`,再跟 `''`(= NULL)比較永遠是 UNKNOWN。**這條訊息永遠不會出現**;同一支 SQL 的其他地方用的是正確的 `NVL(x,' ') <> ' '`(空格不是空字串)。嚴重度中——遺漏的是一個提示訊息,不是卡控。

### E4 被註解掉但外殼還在的檢核(11 處)

| # | 什麼 | 現況 | 錨點 |
|---|---|---|---|
| 1 | `RSPB021` 的「是否已執行過 168 扣款轉申購」 | UI 呼叫整段註解,理由「SP已有檢核,故取消」;PO 的 `ValidateLOG095A` 與 Proxy 方法都還在 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:67-91` |
| 2 | `RSPB008` 的郵局每日交易限額 | UI + PO 兩側各註解一整段,理由「改寫在 StoredProcedure 裡檢核」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:54-66`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286` |
| 3 | `RSPM004` 的「推薦人必須屬於該銷售機構」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2367-2372` |
| 4 | `RSPM005` 的「不可異動『鎖利定額』契約」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:248` |
| 5 | `RSPM020` 的「執行類別 為必填欄位」+ 對應下拉設定 | 兩處都註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:82`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` |
| 6 | `RSPM021` 的「子基金與受益人風險等級不符」 | 註解,**而 `RSPM022` 的同一條是有效的** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310` |
| 7 | `RSPM021` 的「契約申購明細資料已結轉,契約不可刪除」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:660-679` |
| 8 | `RSPM042` 的「已有相同交易資料,不可新增」 | 註解,**而 `RSPM041` 的同一條是有效的** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:836-854` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |
| 9 | `RSPM037` 的「契約收件日須在在職期間」 | 註解,理由「user不想要此功能 20090716」,兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:177`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:244` |
| 10 | `RSPR034` 的「預覽」分支(約 55 行) | 註解,`switch` 沒有 `default`,傳 `PREVIEW` 進來會靜默回「查無資料」 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:137-192` |
| 11 | `RSPM004` / `RSPM005` 的「郵局(700)自動配核印用戶號碼」 | 四段(各兩處 `BeforeAdd` / `BeforeUpdate`)全註解,日期標 `20181119` / `20181120` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:819-856`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:448-486` |

**第 6 與第 8 是同一支業務線上「新增擋、修改不擋」或「新增不擋、修改擋」的落差**,最容易在實務上出事。

### E5 有訊息但沒有 `return` / 訊息與控制項對不上 / 訊息是空的

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPB022` / `RSPB042` / `RSPB021` 的「刪除重作」分支,`AddError` 帶的是 PO 回傳的**空字串** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB022.cs:90-91`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB042.cs:83-84` | 中 |
| 2 | `RSPM042` 的「門檻金額(變更後)必須大於等於10000」掛在 `unumMIN_AMT_BEF`(變更前、唯讀欄) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:828` | 中 |
| 3 | `RSPM042` 的「沒有變更任何欄位」之後 `ValidateErrList.Show()` 但**沒有 `return`**,後面的 `Compare()` 照跑 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875-877` | 低 |
| 4 | `RSPM022` 三處 `string.Format("未填附自主申購聲明書，無法申購!", d_Row.AFT_SON_FUND_ID)` —— 格式字串沒有 `{0}`,基金代碼被丟掉 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:350`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:569` | 低 |
| 5 | `RSPM004` / `RSPM005` / `RSPM021` 的四眼後置事件失敗時 `throw new ApplicationException("")` —— **訊息是空字串** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2588`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:559`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:643` | 中 |
| 6 | `RSPM005` 的「鎖定契約書失敗,請檢查」在契約書號不存在時也會跳,訊息誤導 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:419-420` | 低 |
| 7 | `RSPB041` 的區塊註解寫「(RSP073A)」,實際查的是 `RSP042A` —— 從 `RSPB023` 複製沒改 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:91` | 低 |
| 8 | `RSPM041` 的「已有**有**相同交易資料,不可新增」—— 多一個字 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` | 低 |
| 9 | 28 支報表 PO 的 `catch` 回 `AddResultRow(false, 0, "")`,與「查無資料」的回傳一模一樣 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:83-89` | 中 |

### E6 空 `catch` 與吞例外

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:205-208` | `catch { // pass }` —— 全模組唯一的空 catch,包住「一次印成功 + 失敗兩份報表」的整段流程 | **高** |
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:100-103` | 反過來把 `ex.ToString()`(含完整堆疊)直接秀給使用者 | 低 |

### E7 六處 `catch (SqlException)` 在 Oracle-only 環境是死碼

`architecture.md §4.6` 已確認執行期是 Oracle-only。RSP 有六支 PO 掛 `catch (SqlException sqlex)`:

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:368`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:240`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:276`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:95`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR049_PO.cs:72`。

**只有 `RSPB008` 用對了 `catch (OracleException)`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:113`)。後果是這六支永遠拿不到資料庫的原始錯誤訊息,全部掉進下方的通用 catch 變成固定字串。嚴重度高(`RSPB009` 那支尤其,見 E1-4)。

### E8 兩支畫面沒有移轉到 Oracle(假設)

| 畫面 | 證據 | 嚴重度 |
|---|---|---|
| `RSPM037` | `ISNULL` / `CONVERT(NVARCHAR,…,111)` / `GetDate()` / `[]` / `f_GetAgent()` / `SqlDbType` / 無 A 尾碼表名 / 無 `[PODbType]` / 基底是 `BasicEVAPO` | **高** |
| `RSPB010` | `EXEC s_RSPB010_Excute @p=@x…` T-SQL 字串 / `SqlDbType` / `dbo.f_GetBankHQ()` / 無 `[PODbType]` / 基底是 `BasicEVAPO` | **高** |

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:17`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:17`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:155`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:425`。

**假設**:這兩支在現行 Oracle 環境不可用。依據是上述語法在 Oracle 皆非法,且其餘 23 支 PO 一律 `[PODbType(DbServerType.Oracle)]` + `OracleDbType` + `NVL`。**無法實測,不敢斷言**——也可能資料庫端留了相容物件,或這兩支功能早已停用。`RSPB010` 是扣款作業鏈上的第二棒(§1.4),如果真的不能用,整條鏈的運作方式跟本文描述的會不一樣,**動手前務必先跟站台確認**。

### E9 簡易開戶:註解說取消,程式路徑還在,而且 SQL 可能組錯

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:36` 寫「2013.01.29 取消簡易開戶功能」,但 UI 沒有任何開關關掉它(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:902-919`)。

PO 側那段把三個 `INSERT` 用 `;` 串成一條 SQL,**沒有包 `BEGIN` / `END`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-803`)。同 repo 要送多段 DML 時都有包(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:560`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569`),`xTableHelper.GetInsertString` 產的也是不帶分號的單句(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:486-511`)。

**假設**:這條 SQL 在 Oracle 會拋 `ORA-00911`,也就是簡易開戶實際上已經不能用——這跟 2013 那句註解吻合。`Database.ExecuteNonQuery` 無原始碼(框架 DLL),無法確認它會不會自動包區塊。嚴重度中(功能本來就宣稱取消,但**畫面還是會把開戶欄位打開讓使用者輸入一整頁資料,按下存檔才爆**)。

### E10 併發與交易

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPB018` 逐檔基金各自 commit,中途失敗前面不回滾 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:209-241` | 中(刻意設計,但操作手冊必須寫) |
| 2 | `RSPB052` 兩個獨立交易(業務庫 + PTPF 庫),沒有分散式交易 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:110-111`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:440-441` | 中(全庫性,見 `architecture.md §4.7`) |
| 3 | 五支 SP 外殼的 `catch` 無條件 `tran.Rollback()` 不檢查 null,而同方法的 `finally` 有檢查 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:87` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:95` | 低 |
| 4 | `RSPB008_Service` 的 `sTIMES` 是執行個體欄位,timer 事件與 `GetTIMES()` 之間沒有同步 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:18`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:99` | 低(60 秒間隔,實務上碰不到) |
| 5 | `RSPB008_Service` 的 log 檔每次寫入先整份讀再整份重寫,而且沒有清檔 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:133-146` | 低 |
| 6 | BMS 的 `BMSB901A` 清暫存表時 `DELETE BMSB901A_T1; DELETE BMSB901A_T2;` **不帶 `DATAID`** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:200-203` | 中(它會 `MERGE` 進 `RSP005A` / `RSP006A`,見 §8.2) |

### E11 字串串接進 SQL / 過濾式

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:56-63` | `AddParam` 把參數值用 `'` 包起來直接串進 SQL,含 `LIKE` / `IN` / `=` 三種 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2363-2364` | `CheckSrNoComment` 把 `SrNo.BfNo` 與 `BF_NO` 串進 SQL | 中(值來自系統不是使用者) |
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:70` | `DataTable.Select("CAMPAIGN_CODE = '" + dr.CAMPAIGN_CODE + "' OR …")` | 低 |
| `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2271-2273` | `string.Format("iSUB_ACCOUNT_NO='{0}' AND iSEAL_TYPE='{1}' AND iSUB_DATE=#2009/1/", …)` 再接扣款日與 `#` | 低 |
| `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:114` | `Select("LEAVE_EMP_NO='" + row.EMP_NO + "'")` | 低 |

`architecture.md §4.7` 已把「全庫 PO 的通用寫法」記為高嚴重度;RSP 這邊多數取數已改用具名參數,`RSPM037` 是唯一還整支字串串接的。

### E12 死條件、死分支、寫反的判斷

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `(SUB_BANK_CODE LIKE '700%' OR (SUB_BANK_CODE='' AND SUB_BANK_CODE LIKE '700%'))` —— 第二個分支不可能成立 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255-2257` | 低 |
| 2 | `RSPM005.AfterApproveDelete` 的 `if (strSQL != string.Empty)` —— `strSQL` 至少是 `"BEGIN END;"`,守衛永遠成立 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-573` | 低 |
| 3 | 同一段 `CancelStop(row1)` 被呼叫兩次,第二次只為了判斷要不要加分號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-570` | 低 |
| 4 | `RSPM005` 新增變更書的來源檢核三條 AND 串:**只要該契約曾經開過任何一張變更書,整條檢核就失效** —— 而訊息正是「契約書已被異動,尚未覆核,不可新增異動資料」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:423-436` | **中高** |
| 5 | `RSPM042` 的「有沒有變更」用六個計數,其中兩個看的是 `_BEF`(變更前)欄位,永遠有值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:858-877` | 中 |
| 6 | `RSPB042.ValidateOFD303A` 迴圈內 `Errmsg = "..."`(不是 `+=`)且用 `else if`,**多檔基金只會留最後一條訊息,而且買回與申購兩種錯誤只報一種** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:143-147` 對照正確寫法 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148-151` | **中高** |
| 7 | `RSPM004.CheckSrNoComment` 用 `ExecuteNonQuery` 去跑 `SELECT COUNT(0)`,拿回來的是「影響列數」不是 count | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2366-2370` | 中(簡易開戶的戶號防撞號守衛形同無效) |
| 8 | `RSPB008` 的 `AfterExecuteButtonClicked` 判 `Result.Count == 2`,而 PO 永遠只 `AddResultRow` 一次 —— 死碼 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:128-131` | 低 |
| 9 | `RSPR034` 的 `switch` 沒有 `default`,`PREVIEW` 分支被註解後會靜默落空 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:135-192` | 中 |
| 10 | `RSPM004.SetBfDataVisible(false)` 沒有把 `Simple_Open` 設回 `false`,旗標只會被設成 `true` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1929-1939` | 低 |

### E13 一個概念多套實作

| 概念 | 幾套 | 說明 |
|---|---|---|
| 「還有沒覆核的資料」的比較運算子 | 3 種 | `RSPB008` 用 `=`、`RSPB023` / `RSPB041` 用 `<=`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:156` / `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:111`) |
| 檢核方法的回傳約定 | 2 種相反 | `CheckStatus` / `CheckSmallAmountCode`:有問題時 `ReturnCode = true` 靠訊息判斷;`ValidateOFD303A` / `ValidateLOGxxxA`:有問題時 `ReturnCode = false`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:172` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:192`) |
| 「不限」的表達 | 2 種 | 哨兵值 `'19000101'` 與 `NULL` 判斷,同一支 SQL 內混用(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:155-158`) |
| 主明細宣告 | 2 種 | `xTableMapping`(23 支)與 `TableMapping`(`RSPB010` / `RSPM037`) |
| PO 基底 | 2 種 | `BaseEVADaoPO`(23 支)與 `BasicEVAPO`(2 支) |
| 168 的 `DECODE(REDEM_DATE, …)` 展開表 | 抄了 2 份 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128` 與 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:163-165` |
| `Compare()` 變更前後比對 | 抄了 2 份 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 與 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1011` |
| 「挑申購書」的四條檢核 | 抄了 2 份 | `RSPM021` 新增(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:225-300`)與修改(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:340-390`) |
| `RSPB023` / `RSPB041` | 整支抄 | PO 與 UI 都是逐行相同,只差表名 |
| `RSPM004` / `RSPB020`、`RSPM021` / `RSPB025` | 整支抄 | 取數 SQL 與 xsd 平行維護 |

### E14 手寫逐欄對應

`RSPB052` 用 `xTableHelper.GetInsertString(dbProduct, "RSP013A")` 產出 `INSERT`,再手動 `AddInParameter` 127 個欄位(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:179-390`)。

`GetInsertString` 的欄位清單來自 **DB schema** 而不是 xsd(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:488-511`),所以**只要有一個實體欄位沒被綁,整段會 `ORA-01008` 失敗**。比對 `RSPM005Model.xsd` 的 `RSPM005_Detail`(153 欄)與實際綁定的 127 個,扣掉四眼 14 欄後還有 11 個沒綁:

`BEF_FUND_NAME` `AFT_FUND_NAME` `BEF_BANK_HQ_SHNM` `AFT_BANK_HQ_SHNM` `BEF_CAMPAIGN_SHNM` `AFT_CAMPAIGN_SHNM` `CODE_DESCRP` `SEAL_FAIL_ID_CO_DESCRP` `BEF_DEC_LEN` `AFT_DEC_LEN` `FIRST_SUB_DATE`

前八個看名字是 join 來的顯示欄(`_NAME` / `_SHNM` / `_DESCRP`),應該不在實體表上。**假設**:`BEF_DEC_LEN` / `AFT_DEC_LEN` / `FIRST_SUB_DATE` 三個也不在實體 `RSP013A` 上,否則 `RSPB052` 每次執行都會失敗。依據是這支程式有被使用的痕跡(2016 年的註解與測試用寫死日期,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:152`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:191-192`)。**無法實測**——這條是 `bms.md` 記的「手寫逐欄對應漏欄」同型風險,加欄位到 `RSP013A` 時**一定要回來補這 127 行**。

另外 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:193` 同一行把 `CHG_UPD_DTTM` 加了兩次。

### E15 寫死常數〔客戶特定〕

| 值 | 在哪 | 錨點 |
|---|---|---|
| `'2'`(扣款帳號抓取依據) | `RSPM004` / `RSPB020` 的 UI 與 PO 各一處 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:166`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212` |
| `'301'`(四眼狀態) | 三處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |
| `'ALL FUNDS'`(`OFD131A.FUND_ID`) | `AddOFD130A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1234` |
| `DATE'1900-01-01'`(`REJECTDATE`) | `AddOFD130A` 兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1217`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1238` |
| `'140'` / `'090'`(`BF_SORT_CD`) | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:661`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:671` |
| `'0001'`(`BF_NATIONALITY`) | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:676` |
| `'700'`(郵局) | `RSPM004` 三處 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753` |
| `10000`(停利門檻下限) | `RSPM041` / `RSPM042` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:826` |
| `0.5`(手續費率上限對折) | `RSPM041` / `RSPM042` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:949` |
| `6` / `16` / `26`(轉申購日) | `RSPB021` / `RSPB024` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:61`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB024.cs:65` |
| `'86A03'`(促銷活動) | `RSPM004_PO.Check86A03` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785` |
| `'1'`(`EMP_CD`) | `RSPM037` 兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111` |
| `'42'`(`COD006A.CODE_SORT`) | `RSPM004` 取數 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:247` |
| `'6'`(`OFD681.SEND_TYPE`) | `RSPB008` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `60000` 毫秒 | 服務 timer | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:25` |
| `C://Vendor//WindowService//RSPB008//` | 服務 log 路徑 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114` |
| `"AutoJob"` | 服務的 `UserID` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:52` |
| `AGITest` / `sa` / `sa` / `test002` / `TAAdmin` | 服務 `App.config` 的明碼連線字串 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:73-77` |
| `'039'` → `'810'` / `'20171207'` / `'20171219'` | BMS 的 `BMSB901A` 寫進 `RSP006A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:174-178` |

### E16 型別與字串處理

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPM021` 的申購金額合計用 `Convert.ToInt64` 累加,不是 `decimal` —— 小數被四捨五入。全庫金額一律 `decimal`(`architecture.md §4.6`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:242`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:246` | 中 |
| 2 | `RSPR017` 把 `RSP_TYPE` 做 `Trim('0')`,值本身是 `"0"` 時會變成空字串 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:130` | 中 |
| 3 | `RSPM004` 的限額檢核用 `Convert.ToInt32(row.RSP_ALLOT_DAYS1)`,扣款日為空字串時會丟例外;而它前面的 `DataTable.Select` 過濾式也會變成語法錯的 `iSUB_DATE=#2009/1/#` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2278-2288` | 中 |
| 4 | `RSPM004` / `RSPM005` 的 `AfterApproveDelete` 用 `BuildOldSeal().Split(';')[0]` / `[1]` 切 SQL —— SQL 內若出現任何分號就錯位 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2623`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2628`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:590`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:596` | 中 |
| 5 | `RSPM042.Compare()` 的空值相等判斷寫成 `(befObj == null ^ aftObj != null)` —— 結果正確但沒人讀得懂,且 `RSPM022` 抄了同一份 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1018-1019` | 低 |
| 6 | `RSPM041` 的 `NoticeFeeRate * Convert.ToDecimal(0.5)` —— `0.5` 是 `double` 字面值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` | 低 |
| 7 | 服務的 `WriteLog` 用 `Encoding.Default` 讀寫中文 log | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:135`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:141` | 低 |

### E17 非 UTF-8 來源檔:40 個

`Dev/ATLAS.RSP/` 與 `Dev/ATLAS.RSP.Report/` 底下的 `.cs` / `.xsd` / `.config` / `.csproj`(排除 `obj/`)共 **40 個是 cp950**,其餘是 UTF-8。集中在兩群:

- `RSPB008` / `RSPB009` / `RSPB016` / `RSPB018` / `RSPB019` 那一整組(UI / Designer / Control / FormProxy / PO 全部)

- `Dev/ATLAS.RSP.Report/Source/Entity/ReportDataEntity.RSP/RSPR060ModelVDB.cs` 那一批共 10 個檔

後果:`grep` / `rg` 直接搜中文字串會漏掉這 40 個檔。本文的所有搜尋都走 `docs/tools/atlas_scan.py` 的 `read_text()`(依序試 `utf-8-sig` / `utf-8` / `cp950`)。**要在這個模組找中文訊息,不要直接用 grep。**

### E18 標「假設」的地方一覽

| # | 假設 | 依據 | 在哪一節 |
|---|---|---|---|
| 1 | `RSPM037` 在現行 Oracle 環境不可用 | T-SQL 語法 + 無 A 尾碼表名 + 無 `[PODbType]` | §0.2、§4.6、E8 |
| 2 | `RSPB010` 同上 | `EXEC` 字串 + `dbo.` TVF + `SqlDbType` | E8 |
| 3 | 簡易開戶的三段 `;` 串接 SQL 在 Oracle 會失敗 | 同 repo 其他多段 DML 都包 `BEGIN`/`END`;`GetInsertString` 產單句 | §4.1、E9 |
| 4 | `RSPB052` 未綁定的 `FIRST_SUB_DATE` / `BEF_DEC_LEN` / `AFT_DEC_LEN` 不是實體欄 | 否則該批次每次執行都會 `ORA-01008` | E14 |
| 5 | 框架的 `Database` 有設 `BindByName = true` | 全模組大量使用具名參數且順序與 SQL 不一致;`RSPB052` 多加一個參數仍能跑 | §6.7 |
| 6 | 服務 `App.config` 的五組 SQL Server 連線字串是舊環境殘留 | PO 建構子明確指定 Oracle;值是開發機 `AGITest` / `sa` | §6.3 |
| 7 | 業務線的劃分(A–E 五條) | 表名、欄位 Caption、Designer 標籤、訊息字串 | §0.1 |
| 8 | 一日作業的先後順序 | `RSPB019` 的訊息字串直接寫出「請先從(RSPB016)計算作業開始」,其餘由各批次的檢核對象反推 | §1.4、§1.5 |
| 9 | 沒有 I 畫面的三個原因 | 報表吸收查詢需求 + M 畫面自帶查詢頁 + 兩支偽 B 補位 | §5 |
| 10 | `SUB_STATUS` / `RSP_CTL_CODE` 的值域 | 全部由檢核訊息字串反推,沒有代碼表佐證 | 附錄 C |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版 |

由 build_doc.py v2.0.0 於 2026-09-15 11:10 產生 · 標題 181 · 圖 5 · 表格 97 · 程式錨點 925 · § 連結 63 · 引用檢查：畫面 77（缺 0） · Table 46（缺 0） · Report 39（缺 0） · 結果集 31（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
