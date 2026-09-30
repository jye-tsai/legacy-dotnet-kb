<!-- 由 tools/build_copilot_kb.py 從 modules/dsm.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS DSM 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、§8(跨模組)、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表標題與郵件內文**推測**,待選單表 / 對照表回填。ATLAS 沒有把畫面中文名放進版控,29 支畫面裡只有 4 個彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼(`S` / `090` / `S01` / `S05` / `08001`)、員工代號(`101722`)、列印帳號(`ntaprt05`–`ntaprt11`)、券商代碼 `551`、退信信箱 `ta-it@example.com` 為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`OFD374A`(給 BMS / OFDI / RSP)、`DSM001A` / `DSM002A`(給 CAS)、`BMS906`(前綴不屬 DSM)、`SAL050` / `SAL051`(沒有對應模組)四組表跨界,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:DSM 管「直銷(自家業務員直接賣)」這條通路的五件事——業務組織怎麼編、業績目標訂多少、客戶歸誰、客戶怎麼移轉、業績與收入怎麼算,外加一整排把結果印出來的報表。**

推測依據五條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `SAL050` / `SAL051` 是「業務部門代碼」「部門屬性」「部門主管獎金計算類別」「業務屬性」「獎金制度」;`DSM001A` 是「業績年度」「營業收入」「新開百萬戶數」;`DSM905` 是「業績拆帳比例」「歸屬A業務員之業績上限」 | `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:19-21`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:46-51`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:63-65` |
| PO 內的原始註解 | 「`SAL051` 為直銷的員工範圍」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:112` |
| 郵件內文 | 「送簽來源:DSMM901 業務移轉申請－新增資料作業」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:101-110` |
| 報表標題 | 「直銷業務處 新開百萬客戶清冊」「直銷業務部實際營收達成表--月報」「業務員基金別餘額彙總日報表」「期間各業務單位淨申購/結存金額統計表」 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:429`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR004.cs:230`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010.cs:261`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR011.cs:262` |
| 彈出視窗標題 | 「業務移轉明細」「業務移轉報表」「E-mail備註」「拷貝作業」 | 四支 `yPopUpForm` 的 Designer,用 `grep -n "this.Text"` 取字串,不 Read Designer |

「DSM」三個字母的展開在 repo 內找不到定義,**不要猜**。本文一律用「直銷業務」描述它的範圍,這是從上表推出來的,不是官方名稱。

六條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 業務組織 | 業務部門的屬性與主管獎金類別、部門底下有哪些人、每個人的業務屬性與獎金制度 | `DSMM050` | `SAL050` + `SAL051` |
| B 業績目標 | 每人 / 每單位 / 每人每基金型別的年度目標與月分配 | `DSMM001` `DSMM002` `DSMM003` | `DSM001A`+`DSM002A`、`DSM007A`+`DSM008A`、`DSM003A`+`DSM004A` |
| C 客戶歸屬與拆帳 | 受益人歸哪個業務員、公單怎麼跟業務員拆帳、離職業務的業績分攤比率 | `DSMM060` `DSMM903` `DSMM005` | `OFD374A`〔共用〕、`DSM905`+`DSM9051`、`DSM005A` |
| D 業務移轉 | 客戶(或個別申購書)從 A 業務員 / A 機構整批搬到 B,走四眼 + 寄信 + 執行 SP | `DSMM901` `DSMM902` | `DSM901`+`DSM902`、`DSM903`+`DSM904` |
| E 收入計算與查詢 | 每日算出每位業務員每檔基金的結存與管理費 / 手續費收入,再給查詢與 17 支報表用 | `DSMB001` `DSMI001` `DSMR001`–`DSMR013` | `DSM006A`(計算結果)+ 版控外的 SP |
| F 對帳單名單 | 業務員自己維護哪些客戶要寄月對帳單 | `DSMM906` | `BMS906`〔前綴不屬 DSM〕 |

### 0.2 這模組最反直覺的四件事

**(1) 16 張表裡有 4 張的前綴不是 `DSM`,其中兩張是別的模組的字頭。**

| 表 | 前綴屬於 | 主檔於 | 為什麼在 DSM |
|---|---|---|---|
| `SAL050` `SAL051` | **沒有任何模組**(全庫沒有 `ATLAS.SAL` 專案,也沒有 `SAL` 開頭的畫面代號) | `DSMM050` | 直銷的業務組織設定,唯一維護入口就在 DSM,見 §8.4 |
| `OFD374A` · `BMS906` | OFD · BMS | `DSMM060` · `DSMM906` | 受益人歸屬業務員(BMS 拿去當明細,§8.2);對帳單郵寄名單(BMS 側沒有任何畫面碰它,§8.3) |

**(2) 有一支維護畫面根本不走四眼引擎。**`DSMM906` 把 `Add` / `Update` / `Delete` 三個方法整個 override 成手寫 SQL,不寫 `STATUS` / `DATAID` / 四眼 13 欄(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-278`);`BMS906` 的 xsd 也確實沒有四眼欄位。**同一顆「新增」按鈕,在這支畫面按下去是直接進資料庫,沒有待驗證 / 待覆核。**

**(3) 兩支「業務移轉」畫面(`DSMM901` / `DSMM902`)的結構幾乎一樣,行為卻差三件事。**

| 面向 | `DSMM901`(戶號層) | `DSMM902`(申購書層) |
|---|---|---|
| 覆核通過後 | **不自動執行**,要人工按執行鈕 | **自動呼叫 `DoExp1()` 跑 SP**,且不寄「執行」通知信 |
| SP 有沒有錯誤回傳 | 沒有 OUT 參數,一律回「執行成功」 | 有 `strMsg` OUT,非空就 rollback 並顯示 |
| 移轉後業務員的檢核 | 只查「員工存在」 | 查「員工存在 + 屬於移轉後部門 + 未離職」 |
| 錨點 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:302-305`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:470-500`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:424-439` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:274-282`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:464-512`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:433-447` |

**(4) 同一顆「月分配」按鈕,三支畫面三種算法。**`DSMM001` 可分配月數是「13 − 起算月」,`DSMM002` 固定 12(所以會跨到次年),`DSMM003` 月數算「13 − 起算月」但補餘額的判斷式寫死 12。細節見 §4.1 / §4.2 / §4.3 與附錄 E3。

### 0.3 不管什麼

以下**不在** DSM 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料 | BMS | `BMS001A` 全部是 `JOIN` 取姓名 / 身分證 / 地址,DSM 沒有任何一行寫入;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| 員工主檔、部門、離職日 | COD | `COD009` 只被 join;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:127-128` |
| 部門名稱主檔 | OFD | `OFD002` 只被 join 取 `DEPT_SH_NM` / `DEPT_CH_NAME`;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127` |
| 銷售機構主檔 | OFD | `OFD068A` 與 view `OFD068A_V02` 只讀不寫;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141` |
| 申購 / 贖回交易本身 | OFD | `OFD221` `OFD221A` `OFD306` `OFD306A` 只讀;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:204-206` |
| 結帳控制 | OFD | `OFD303A` 只用來判斷「有沒有結帳」;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:185-189` |
| 查詢權限對照 | CRM | `CRM002A` 只被 `DSMI001` join;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |
| **收入數字怎麼算出來的** | **版控外的 SP** | `DSMB001` 只負責呼叫 `S_TA_DSMB001_EXCUTE_P01`,算式在 DB 裡;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:66-76`。repo 內**沒有**任何一行程式讀 `DSM905` 的 `RATE_A` / `RATE_B`,也沒有讀 `DSM005A` 的 `SHARE_RATE` 去做計算。**假設**:這些比率全部由 `S_TA_DSMB001_EXCUTE_P01` 在 DB 端套用,依據是 `DSMB001` 的檢核直接查 `DSM006A` 有沒有資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:160-171`),而 `DSM006A` 就是這支 SP 的產出 |
| 業務移轉實際搬資料 | **版控外的 SP** | `S_TA_DSMM901_EXE` / `S_TA_DSMM902_EXE`;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:477`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:472` |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 直銷業務員 | 維護自己客戶的對帳單寄送設定(`DSMM906`)、查自己的收入(`DSMI001`) | `DSMM906` 查詢無條件加上「`EMP_NO` = 登入者員編」(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125`);`DSMI001` 靠 `CRM002A` 決定看得到誰(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89`) |
| 直銷部門主管 | 當公單的預設歸屬人;`DSMM903` 開畫面就去撈業務屬性為 `A` 的在職者 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` |
| 業務助理 / 內勤 | 建業績目標(`DSMM001`–`DSMM003`)、建業務移轉申請(`DSMM901` / `DSMM902`)、跑收入計算(`DSMB001`) | 這幾支都是標準畫面,權限在程式內看不到 |
| 移轉流程的 E / V / A 三種角色 | 輸入 / 驗證 / 覆核,每一段各自收到不同收件人的通知信 | 角色代碼存在 view `DSMM901_V01` 的 `ROLE901` 欄;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:118-132` |
| 報表列印專用帳號 | `ntaprt05`–`ntaprt11` 這批帳號在 `DSMR008` 可以查全部部門 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:134-143`〔客戶特定〕 |
| 一位特定員工 | 員編 `101722` 不受部門限制,看得到全部 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:117-125`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:119-127`〔客戶特定〕 |

**除了上面這兩條寫死的白名單,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。

### 0.5 全域開關

repo 內**沒有**任何 DSM 專屬的設定檔開關。`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔與主鍵,給框架做 grid 的 PK 檢查用 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:32`(`DSMM001`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:67`(`DSMM050`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:76`(`DSMM060`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:108`(`DSMM906`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:34`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:101` |
| `formstyle` | `DSMB001` / `DSMI001` 宣告為 `OneStep`;其餘 M 畫面不宣告 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:20`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:26` |

四個要記住的:

- **五支畫面的 `detailtable` 那行全部被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:33`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:42`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:51`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:68`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:109`),而且那五行被註解的內容**全都寫 `DSM002A`**,連 `DSMM050` 那一行也是——是從 `DSMM001` 複製樣板留下來的殘骸,**別當成事實**。實際的明細表以 PO 建構子為準(§2.1)。

- **`DSMM005` 的 `mastertable` 寫 `DSM005A`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:59`),PO 也確實宣告了,只是用多筆型的 `this.MasterTable.Add(...)` 寫法(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:47`)。掃描器只認 `this.MasterTable = new xTableMapping(...)`,所以母體把 `DSMM005` 判成「沒有主明細」。**設定檔與 PO 一致,母體才是缺的那一方**(附錄 D)。

- **`DSMM902` 的 `detailtable` 的 `pkey` 中間有一個空白**:`BATCHID,ALLOT_NO, ALLOT_SRNO`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:92`)。框架怎麼切這個字串無原始碼,**假設**是 `Split(',')` 之後不 `Trim`,那第三個 PK 名會變成前面帶一個空白而對不上欄位。依據是同檔其他六處 `pkey` 都沒有空白。

- **`DSMM903` 的主鍵含 `AGENT_CODE_LIKE`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:99`),而這個欄位的 Caption 直接寫「原銷售機構代碼LIKE用(固定S%)直鎖專用」(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:33`)。**一個永遠是常數的欄位被放進主鍵**,見 §4.9。

`.Report` 側的 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/App.config` 只宣告 `formstyle`,沒有主明細。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] DSM 模組全景：業務組織、業績目標、客戶歸屬與拆帳、業務移轉、收入計算、報表六條線
圖中文字:① 業務組織：全庫共用的員工編制,唯一維護入口在 DSM / DSMM050 / 業務部門與人員 SAL050/051 / SAL050 SAL051 / 無模組前綴 全庫共用 / 共用員工下拉 / V_SAL051 全庫都吃 / ② 業績目標：三支結構相同、算法各異的畫面 / DSMM001 / 員工年度目標 DSM001A / DSMM002 / 單位年度目標 DSM007A / DSMM003 / 員工x型別 DSM003A / CASM006〔CAS〕 / 同用 DSM001A/002A / ③ 客戶歸屬與拆帳 / DSMM060 / 受益人歸屬 OFD374A / DSMM903 / 公單拆帳 DSM905/9051 / DSMM005 / 離職業務分攤 DSM005A / BMSM001 BMSM006 / 借 OFD374A 當明細 / ④ 業務移轉：四眼 + 寄信 + 版控外的執行 SP / DSMM901 / 業務移轉 戶號層 / DSMM902 / 業務移轉 申購書層 / S_TA_DSMM901_EXE 等 / 版控外 SP / DSMM901_V01 / 通知信收件人 view / ⑤ 收入計算：全模組的匯流點,母體卻沒列到這張表 / DSMB001 / 收入計算 呼叫 SP / DSM006A / 每日業務員收入檔 / DSMI001 / 收入查詢 CRM002A 權限 / DSMR003 DSMR004 / 達成率報表 / ⑥ 報表與對帳單名單 / DSMM906 / 對帳單名單 BMS906 / DSMR001 ~ DSMR013 / 17 支 全走版控外 SP / 40 個 .rpt 在 repo / 另有 13 個引用不在
```

*圖:圖 1 DSM 全景。橘框=本模組的維護入口;灰虛框=別的模組借用同一張表;黑框=無原始碼或版控外的東西;橘虛框=行為含寫死值〔客戶特定〕。六條線之間幾乎沒有程式呼叫,全靠表相連——尤其 ① 的 SAL051 決定了 ② 看得到哪些員工。*

看圖的四個重點:

1. **六條業務線之間幾乎沒有程式呼叫關係。**唯一的例外是 `DSMM902` 覆核後直接叫自己的執行流程(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:280`)。其餘全靠表相連:`DSMM001` / `DSMM003` 的取數 SQL 去 join `SAL051`(`DSMM050` 維護的),所以**改 `DSMM050` 的部門成員,會直接改變 `DSMM001` 查得到的員工集合**(§8.5)。

2. **`DSM006A` 是全模組的匯流點,但沒有任何一支畫面拿它當主檔。**它由 `DSMB001` 呼叫的 SP 產出,被 `DSMI001` 查詢、被大半報表統計。母體的 16 張表裡**沒有它**(它只出現在 `DSMI001Model.xsd`,被判成結果集),見附錄 D。

3. **報表那一排與上面五排在 repo 內是斷的。**17 支 R 畫面沒有一支引用 DSM 的維護 PO,資料全部來自版控外的 SP(§7)。也就是說**報表看到的數字,跟維護畫面寫進去的值之間的關係,在 repo 內查不到**。

4. **只有 `DSMM901` / `DSMM902` 會寄信,而且寄給誰由一支 view 決定。**`DSMM901_V01` 過濾 `DEPT = 'S'`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259`)〔客戶特定〕。

### 1.2 資料表關係

七組配對 + 三張沒有明細的孤兒:

| 組 | 主檔 | 明細 | 配對欄位 |
|---|---|---|---|
| 業績目標(人) | `DSM001A` | `DSM002A` | `QUO_YEAR` + `EMP_NO`,明細再加 `QUO_YYMM` |
| 業績目標(單位) | `DSM007A` | `DSM008A` | `QUO_YEAR` + `DEPT_NO`,明細再加 `QUO_YYMM` |
| 業績目標(人×基金型別) | `DSM003A` | `DSM004A` | `QUO_YEAR` + `EMP_NO` + `FUND_TYPE_SALE`,明細再加 `QUO_YYMM` |
| 業務組織 | `SAL050` | `SAL051` | `SAL_DEPT_NO`,明細再加 `EMP_NO` |
| 業務移轉(戶號層) | `DSM901` | `DSM902` | `BATCHID`,明細再加 `BF_NO` |
| 業務移轉(申購書層) | `DSM903` | `DSM904` | `BATCHID`,明細再加 `ALLOT_NO` + `ALLOT_SRNO` |
| 公單拆帳 | `DSM905` | `DSM9051` | `BF_NO` + `AGENT_ID` + `AGENT_CODE_LIKE`,明細再加 `EMP_NO_A` |
| 孤兒(無明細) | `OFD374A` · `BMS906` · `DSM005A` | — | 見 §2.1 |

### 1.3 主要維護畫面的四眼與卡控順序

三條要記住的:

- **卡控幾乎全在 UI 層。**10 支 M 畫面裡,只有 `DSMM901`(執行基準日 vs 結帳日)與 `DSMM906`(戶號歸屬)在 PO 的 `BeforeAdd` / `BeforeUpdate` 有伺服器端檢核,其餘全靠 `DoValidate()` 擋在按鈕之前。**繞過 UI 就沒有第二道防線**。

- **`DSMM050` 與 `DSMM903` 的 grid 逐列檢核只顯示訊息、不擋。**七處 `e.Cancel = true;` 全部被註解(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:373`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:382`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:394`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:413`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:422`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:431`),真正的閘門是存檔前的 `DoValidate()`,而它比逐列檢核寬。

- **`DSMM906` 沒有四眼。**它的按鈕直接落地,`architecture.md §3` 的狀態機在這支畫面完全不適用。

### 1.4 批次 / 報表資料流

一條直線:`DSMB001`(人工按執行,可跑一段日期區間)→ `S_TA_DSMB001_EXCUTE_P01` → 寫 `DSM006A` → `DSMI001` 查詢、`DSMR003` / `DSMR004` 統計。`DSMR003` / `DSMR004` 在列印前還會先呼叫一支 `Exists` 確認 `DSM006A` 這段區間有沒有資料,沒有就擋下列印(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:282-290`)。

### 1.5 一日作業泳道

程式內看不到排程:`DSMB001` 是 `OneStep` 人工畫面,repo 裡**沒有** DSM 的 WindowsService(母體第 5 節空白)。所以下面這條是**假設**,依據是 `DSMB001` 的檢核要求「該段日期的基金都已結帳」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:132-137`):

| 時點 | 誰 | 做什麼 |
|---|---|---|
| 前一日結帳完成後 | OFD | `OFD303A` 的結帳旗標變 `Y` |
| 當日上班 | 直銷內勤 | 開 `DSMB001`,輸入計算日期起迄,按執行 |
| 執行中 | 版控外的 SP | 重算 `DSM006A`(已有資料會先跳「是否確認要執行」的詢問) |
| 執行後 | 業務員 / 主管 | `DSMI001` 查收入、`DSMR010` 印日報表 |
| 不定期 | 內勤 | `DSMM901` / `DSMM902` 送業務移轉申請;`DSMM060` 設新客戶歸屬,公單客戶另外在 `DSMM903` 設拆帳 |
| 年初 / 每月 | 內勤 | `DSMM001`–`DSMM003` 設當年度目標;`DSMM005` 設當月離職業務分攤比率(可用拷貝一次產生多個月) |

## 2. 資料模型

```text
[圖] DSM 十六張表的主明細配對、主鍵組成,以及外部唯讀表
圖中文字:三組業績目標:主檔 + 月明細,六個指標欄位完全同名 / DSM001A / PK 年度+員工 / DSM002A / + 業績年月 / DSM007A / PK 年度+單位 / DSM008A / + 業績年月 / DSM003A / PK 年度+員工+型別 / DSM004A / + 業績年月 / DSM005A / PK 年月+部門 多筆型 / SAL050 SAL051 / PK 部門 / + 員工 / 兩組業務移轉 + 一組公單拆帳 / DSM901 / PK 期別 / DSM902 / + 戶號 / DSM903 / PK 期別 / DSM904 / + 申購書號+序號 / DSM905 / PK 戶號+機構別+LIKE / DSM9051 / + 業務員 / 三張沒有明細的孤兒,兩張前綴不屬 DSM / OFD374A〔共用〕 / PK 戶號 · 主檔在 DSMM060 / BMS906〔共用〕 / PK 戶號 · 無四眼欄位 / DSM006A / 母體沒列 · 批次產出 / 外部唯讀(join 進來,不屬本模組) / COD009 / 員工/離職日 / OFD002 / 部門名稱 / BMS001A / 受益人資料 / OFD068A(_V02) / 銷售機構 / CRM002A / 查詢權限
```

*圖:圖 2 資料模型。橘框=主檔;白框=明細;灰虛框=前綴不屬 DSM 的共用表;黑框=外部唯讀。實線箭頭=主明細(同一次四眼一起送審)。除了 BMS906 之外,十五張表都有完整的四眼 13 欄。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

以 PO 建構子為唯一事實來源(設定檔那份有五行被註解,見 §0.5):

| 畫面 | PO 基底 | 主檔 | 明細 | 錨點 |
|---|---|---|---|---|
| `DSMM001` | `BaseEVADaoPO` | `DSM001A` | `DSM002A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36` |
| `DSMM002` | `BaseEVADaoPO` | `DSM007A` | `DSM008A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36` |
| `DSMM003` | `BaseEVADaoPO` | `DSM003A` | `DSM004A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:32-33` |
| `DSMM005` | **`BaseMultiRowEVADaoPO`** | `DSM005A`(多筆型) | —(grid 就是主檔本身) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:43-47` |
| `DSMM050` | `BaseEVADaoPO` | `SAL050` | `SAL051` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:39-40` |
| `DSMM060` | `BaseEVADaoPO` | `OFD374A` | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:33` |
| `DSMM901` | `BaseEVADaoPO` | `DSM901` | `DSM902` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:48-49` |
| `DSMM902` | `BaseEVADaoPO` | `DSM903` | `DSM904` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:47-48` |
| `DSMM903` | `BaseEVADaoPO` | `DSM905` | `DSM9051` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:38-39` |
| `DSMM906` | `BaseEVADaoPO`(但三個寫入方法全 override) | `BMS906` | —(建構子那行被註解) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:39-40` |
| `DSMI001` | **無基底**,自訂介面 | —(裸 DAO,見 `architecture.md §6.3`) | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:34` |
| `DSMB001` | **無基底**,自訂介面 | — | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:27` |

**`DSMM005` 是全模組唯一的多筆型 EVA 畫面。**它宣告的是 `MasterPKey` 兩欄(`QUO_YYMM` / `DEPT_NO`)加一張 `MasterTable`,grid 裡的每一列都是主檔的一筆,靠 `ROW_NUMBER() … R_NUM = 1` 把同一個年月 + 部門折成查詢結果的一列(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:129-141`)。

### 2.2 主鍵與四眼欄位

主鍵以 `App.config` 的 `pkey` 為準(框架用它做 grid 的 PK 檢查),PO 的 SQL 條件與之一致:

| 表 | 主鍵 | 四眼 13 欄 | 來源 |
|---|---|---|---|
| `DSM001A` | `QUO_YEAR` + `EMP_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:32` |
| `DSM002A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:215-224` |
| `DSM007A` | `QUO_YEAR` + `DEPT_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:41` |
| `DSM008A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:220-229` |
| `DSM003A` | `QUO_YEAR` + `EMP_NO` + `FUND_TYPE_SALE` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:50` |
| `DSM004A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:210-215` |
| `DSM005A` | `QUO_YYMM` + `DEPT_NO` + `EMP_NO`(設定檔)/ 只有前兩欄(PO) | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:59` vs `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:43-44` |
| `SAL050` | `SAL_DEPT_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:67` |
| `SAL051` | `SAL_DEPT_NO` + `EMP_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:71` 的 `m_PkeyNotInMaster` |
| `OFD374A` | `BF_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:76` |
| `DSM901` | `BATCHID` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:83` |
| `DSM902` | `BATCHID` + `BF_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:84` |
| `DSM903` | `BATCHID` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:91` |
| `DSM904` | `BATCHID` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:92` |
| `DSM905` | `BF_NO` + `AGENT_ID` + `AGENT_CODE_LIKE` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:99` |
| `DSM9051` | 主檔鍵 + `EMP_NO_A` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:100` |
| `BMS906` | `BF_NO` | **無** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:108` |

**兩個要注意的:**

1. **`DSM005A` 的主鍵兩處不一致。**設定檔三欄、PO 兩欄。這不是筆誤——多筆型 EVA 的 `MasterPKey` 是「一組要一起送審的資料共用的鍵」,`EMP_NO` 是列層級的鍵,所以 UI 才另外把它放進 `m_PkeyNotInMaster`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:67`)。**兩邊都對,但只看一邊會誤解。**

2. **母體說只有 5 張表有四眼欄位,那是掃描器的誤判。**實測 16 張表裡 **15 張都有完整的 13 欄**,唯一沒有的是 `BMS906`。原因見附錄 D。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列業務欄,四眼 13 欄與 `DATAID` / `DATAFLAG` 全模組一致不重複列。

#### `DSM001A` — 年度業績目標(人層,26 欄,`DSMM001` 主檔)

| 欄位 | 中文名 |
|---|---|
| `QUO_YEAR` · `EMP_NO` · `BOUNS_ST_YYMM` | 業績年度 · 員工代碼 · 起算年月 |
| `QUO_MGR_TOT` · `QUO_RSP_NM_TOT` · `QUO_RSP_LNM_TOT` | 營業收入 · 定期(不)定額戶數-目標 · 定期(不)定額戶數-保守 |
| `QUO_RSP_AMT_TOT` · `QUO_MIL_NA_TOT` · `QUO_MIL_A_TOT` | 定期(不)定額扣款成功金額 · 新開百萬戶數 · 單筆申購交易百萬戶數 |
| `EMP_NAME` `DEPT_NO` | 員工姓名 / 部門代碼(**join 來的,不是 `DSM001A` 的實體欄**) |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:25-51`。

#### `DSM002A` — 月業績目標明細(24 欄,`DSMM001` 明細)

欄名把主檔的 `_TOT` 去掉就是:`QUO_MGR` / `QUO_RSP_NM` / `QUO_RSP_LNM` / `QUO_RSP_AMT` / `QUO_MIL_NA` / `QUO_MIL_A`,加上 `QUO_YYMM`「業績年月」。注意**明細的 `QUO_MIL_A` 中文名是「單筆申購交易百萬戶」,主檔是「單筆申購交易百萬戶數」**,差一個字(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:51` 對 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:149`)。

#### `DSM007A` / `DSM008A`、`DSM003A` / `DSM004A`、`DSM005A`

| 表(欄數) | 業務欄 | 中文名 |
|---|---|---|
| `DSM007A`(25)/ `DSM008A`(24) | 同 `DSM001A` 的六個指標 | 差別只在鍵:人層是 `EMP_NO`,單位層是 `DEPT_NO`「單位代碼」;join 來的名稱欄叫 `DEPT_NAME`「部門單位名稱」 |
| `DSM003A`(22)/ `DSM004A`(20) | `FUND_TYPE_SALE` · `QUO_NET_IN_TOT` / `QUO_NET_IN` · `SALE_DEPT_NO` | 基金型別 · 淨銷售金額(年度 / 月)· 部門代碼(join 自 `SAL051`) |
| `DSM005A`(21) | `QUO_YYMM` · `DEPT_NO` / `DEPT_SHNM` · `EMP_NO` / `EMP_NAME` · `SHARE_RATE` | 業績年月 · 部門代碼 / 部門名稱 · 員工代碼 / 員工名稱 · 離職業務分攤比率 |

#### `SAL050` / `SAL051` — 業務組織(20 / 22 欄,`DSMM050`)

| 欄位 | 中文名 | 備註 |
|---|---|---|
| `SAL_DEPT_NO` | 業務部門代碼 | 3 碼=大部門、5 碼=小部門,見 §4.5 |
| `DEPT_CD` / `MGR_BNS_KIND` | 部門屬性 / 部門主管獎金計算類別 | 下拉代碼分類 `458` / `459`;後者的 Caption 前面多一個空白 |
| `DEPT_CH_NAME` · `EMP_NO` / `EMP_NAME` | 業務部門名稱(join 自 `OFD002`)· 員工代號 / 姓名 |  |
| `SAL_CD` / `BONUS_TYPE` | 業務屬性 / 獎金制度 | 下拉代碼分類 `460` / `461`,值域見附錄 C |
| `TOT_ADD_AC` | (無 Caption) | 整數欄,repo 內**沒有任何程式讀寫它** |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:19-21`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:46-53`。

#### `OFD374A` — 受益人歸屬業務員(22 欄,`DSMM060` 主檔)〔共用〕

| 欄位 | 中文名 |
|---|---|
| `BF_NO` | 受益人戶號 |
| `EMP_NO` | 員工代號 |
| `SAL_DEPT_NO` | 業務部門代碼 |
| `BELONG_DATE` | 歸屬日期 |
| `BF_NAME` `DEPT_SH_NM` `EMP_NAME` | 受益人中文姓名 / 部門中文簡稱 / 員工姓名(全部 join 來的) |

**業務欄只有四個**,其餘 18 欄是四眼與 join 欄。這一點對 §8.2 很關鍵。

#### 兩組業務移轉表(`DSM901`/`DSM902`、`DSM903`/`DSM904`)

| 表(欄數) | 業務欄與中文名 |
|---|---|
| `DSM901`(23) | `BATCHID` 期別 · `EXEDATE` 執行基準日 · `EXETYPE` 類別 · `EXESTATUS` 執行狀態 · `EXETIME` 實際執行時間 · `EXEUSER` 執行者 · `MEMO` 備註 · `EXESEQ`(無 Caption,第幾次執行,`DSMM901` 拿它當明細 `SEQ` 的預設值) |
| `DSM902`(31) | `SEQ` 序號 · `BF_NO` / `BF_NAME` 戶號 / 受益人姓名 · `AGENT_CODE` / `AGENT_NAME` / `EMP_NO` / `EMP_NAME` 移轉前四欄 · 同名加 `_N` 的移轉後四欄 · `EXEAUM` 移轉時庫存 · `EXESTATUS` 執行結果 |
| `DSM903`(22) | 比 `DSM901` 多一欄 `FUND_TYPE`「基金來源」,少 `EXETYPE` 與 `EXESEQ` |
| `DSM904`(40) | `DSM902` 的前後四欄 + `ALLOT_NO` 申購書號 / `ALLOT_SRNO` 申購序號 + 一整組從 `OFD221` / `OFD221A` 帶進來的顯示欄(`FUND_ID` `FUND_SH_NM` `ALLOT_DATE` `ALLOT_NAV_DATE` `NAV_B` `ALLOT_AMT` `ALLOT_UNIT` `UNIT_DEC` `DEC_LEN` `NAV_DEC`)+ **移轉前後各自的銷售機構別** `AGENT_ID` / `AGENT_ID_N`(`DSM902` 沒有這兩欄,`DSMM901` 固定只做直銷) |

`DSMM901Model.xsd` 內另有三張非實體表:`Total`(`CNT` 筆數、`AUM` 總庫存)、`MAIL`(`ROLE901`、`EMAIL`)、`AO`(`AGENT_CODE`、`EMP_NO`)。錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM901Model.xsd:117-141`。

#### `DSM905` / `DSM9051` — 公單拆帳(27 / 25 欄,`DSMM903`)

| 欄位 | 中文名(原文照抄) |
|---|---|
| `BF_NO` | 戶號 |
| `AGENT_ID` | 原銷售機構別(固定0) |
| `AGENT_CODE_LIKE` | 原銷售機構代碼LIKE用(固定S%)直鎖專用 |
| `AGENT_ID_B` / `AGENT_CODE_B` / `EMP_NO_B` | 公單銷售機構別 / 新銷售機構代碼:公單(預設SAL051部門主管)/ 新員工代碼:公單(預設SAL051部門主管) |
| `MAX_BAL_AMT_A` | 歸屬A業務員之業績上限, 若為0則無上限 |
| `RATE_B` / `RATE_A` | 業績拆帳比例B業務員 / 業績拆帳比例A業務員 |
| `AGENT_ID_A` / `AGENT_CODE_A` / `EMP_NO_A` | 新銷售機構別:業務員(固定0)/ 新銷售機構代碼:業務員(取SAL051業務屬性C)/ 新員工代碼:公單(取SAL051業務屬性C) |
| `SDATE` / `EDATE` | 計算日(起)/ 計算日(迄:預設29991231) |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:25-66`。**`EMP_NO_A` 的 Caption 寫「新員工代碼:公單」是明顯的複製貼上錯誤**,從欄名與取數條件看應該是「業務員」(附錄 E)。

#### `BMS906` — 對帳單郵寄名單(25 欄,`DSMM906` 主檔)〔前綴不屬 DSM〕

**實體欄只有 7 個**:`BF_NO` / `EMP_NO` / `MAIL_YN`「是否郵寄」/ `REMARK`「備註」/ `UPD_USER`「更新者」/ `UPD_DATE`「更新日期」/ `UPD_TIME`「更新時間」——從 PO 的 INSERT 欄位清單反推(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:158-159`)。xsd 裡其餘 18 欄(`BF_NAME` / `ID_NO` / `BIR_DATE` / `AGENT_IN_LAW*` / `PERM_ADDR` / `MAIL_ADDR` / 各種電話 / `EMAIL1`)**全部 join 自 `BMS001A`**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:292-306`)。

**這張 DataTable 叫 `BMS906`,但它不是 `BMS906` 這張實體表。**改 xsd 的欄位跟改實體表是兩件事,見 §8.3。

#### `DSM006A` — 每日直銷及代銷業務員收入檔(34 欄,無畫面當主檔)

| 欄位 | 中文名 |
|---|---|
| `BAL_DATE` / `FUND_ID` / `AGENT_ID` / `AGENT_CODE` / `EMP_NO` | 結存日期 / 基金代碼 / 銷售機構別 / 銷售機構代碼 / 員工代碼 |
| `BAL_UNIT` / `NAV_B` / `BAL_AMT` | 結存單位數 / 淨值 / 結存金額 |
| `MGR_RATE` / `MGR_FEE` / `ALLOT_FEE` | 管理費率 / 管理費 / 手續費 |
| `TOT_FEE` | 總收入(**SQL 算出來的 `MGR_FEE + ALLOT_FEE`,不是實體欄**;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:72`) |
| `LEAVE_YN` | 離職否(**`DECODE` 算出來的**;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:76`) |

注意這張表的 `STATUS` 中文名被寫成「資料識別碼」(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMI001Model.xsd` 內),其他表都寫「資料狀態碼」。

### 2.4 與其他模組共用的表

| 表 | 誰的 | DSM 的角色 | 別人怎麼用 | 詳見 |
|---|---|---|---|---|
| `DSM001A` `DSM002A` | DSM | `DSMM001` 主明細 | `CASM006` 也拿它當主明細 | §8.1 |
| `OFD374A` | OFD(前綴)/ DSM(唯一維護者) | `DSMM060` 主檔,唯一會寫的地方之一 | `BMSM001` `BMSM006` 條件掛明細;`OFDI011` 檢查歸屬;`RSPM004` 直接 INSERT | §8.2 |
| `BMS906` | BMS(前綴)/ DSM(唯一使用者) | `DSMM906` 主檔 | BMS 側沒有任何畫面 | §8.3 |
| `SAL050` `SAL051` | 無模組 | `DSMM050` 主明細 | `SAL051` 被 `DSMM001` `DSMM003` `DSMM901` `DSMM902` `DSMM903` 五支 join | §8.4 §8.5 |
| `OFD068A_V02`(view) | OFD | `DSMM901` 驗機構、`DSMM903` 取機構名 | `OFDI011` 也用 | §8.6 |

外部唯讀(只 join、從不寫):`COD009`、`OFD002`、`BMS001A`、`OFD068A`、`OFD303A`、`OFD306` / `OFD306A`、`OFD221` / `OFD221A`、`OFD081` / `OFD081A` / `OFD081V`、`FSK003`、`CRM002A`。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`(四眼引擎的狀態)

DSM 側出現**兩個字面值**,而且都是三碼:

| 值 | 出現處 | 語意(反推) |
|---|---|---|
| `203` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` 的 `this.strSTATUS != "203"` | **刪除待覆核**。註解寫「刪除覆核不執行SP」,所以覆核一筆 `203` 時不會去跑移轉 |
| 以 `3` 開頭 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:216` 的 `row.STATUS.StartsWith("3")` | **已覆核 / 正式生效**。這是「可以按執行鈕」的前提 |
| `301` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206` 直接塞給查詢結果的 `STATUS` 預設值 | 同上,`3` 開頭的其中一個 |

**這是 DSM 對 `architecture.md §3.10` 那個懸案的補充證據**:該節說全庫 SQL 裡的 `STATUS` 字面量掃出來是單字元 `'0'`~`'9'`,並**假設**單字元就是 `EVAStatusCode` 的實際值。DSM 這三處是三碼,而且語意可以對上「輸入 / 驗證 / 覆核」三段(`2xx` 待覆核、`3xx` 已覆核)。**假設**:本站台的 `STATUS` 是三碼,第一碼是階段、後兩碼是動作別;依據是 `203`(刪除待覆核)與 `301` 這兩個實際值以及 `StartsWith("3")` 的用法。要確定得反編譯 `Vendor.Product.TA.MappingCode` 或直接查資料庫。

#### `EXESTATUS`(移轉批次自己的執行狀態)

值由 `EXE_STATUS` 這組常數決定(無原始碼,`Vendor.Product.TA.MappingCode`):

| 常數 | 用在哪 | 錨點 |
|---|---|---|
| `EXE_STATUS.NonExecute` | 新增時強制設定;`DSMM901` / `DSMM902` 都一樣 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:68`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:67` |
| `EXE_STATUS.Executed` | 判斷「已執行」,決定要不要把 `EXESEQ` 加一、要不要鎖修改 / 刪除 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:207`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:190` |

UI 上顯示的中文由下拉代碼分類 **`322`**(主檔)與 **`300`**(明細)提供——**同一個 `EXESTATUS` 欄位,主檔與明細用兩份不同的代碼表**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:147-151`)。

#### 本模組自訂的旗標與代碼〔客戶特定〕

`SAL_CD`(業務屬性)、`DEPT_CD`(部門屬性)、`FUND_TYPE`(境內外)、`AGENT_ID`(銷售機構別)、`MAIL_YN`、`ROLE901`、`FUND_TYPE_SALE`、`EXETYPE` 與六組下拉代碼分類的值域與出處,整理在附錄 C,不在這裡重複。

## 3. 畫面清冊

29 支:M 10 · I 1 · B 1 · R 17。中文名一律待選單表回填,以下「用途(推測)」欄是本文的推測。

### 3.1 維護 M

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | SP / Fn / View | rpt |
|---|---|---|---|---|---|---|
| `DSMM001` | 業務員年度業績目標與月分配 | 齊 | `DSM001A` | `DSM002A` | — | — |
| `DSMM002` | 業務單位年度業績目標與月分配 | 齊 | `DSM007A` | `DSM008A` | — | — |
| `DSMM003` | 業務員×基金型別年度淨銷售目標 | 齊 | `DSM003A` | `DSM004A` | — | — |
| `DSMM005` | 離職業務分攤比率(多筆型 EVA + 拷貝) | 齊 | `DSM005A` | —(多筆主檔) | — | — |
| `DSMM050` | 業務部門與人員設定 | 齊 | `SAL050` | `SAL051` | — | — |
| `DSMM060` | 受益人歸屬業務員 | 齊 | `OFD374A`〔共用〕 | — | — | — |
| `DSMM901` | 業務移轉申請(戶號層)+ CSV 匯入 + 寄信 + 執行 | 齊 | `DSM901` | `DSM902` | `S_TA_DSMM901_AUM` `S_TA_DSMM901_EXE` `S_TA_DSMM901_GET` · view `OFD068A_V02` `DSMM901_V01` | `DSMM901RPS` |
| `DSMM902` | 業務移轉申請(申購書層)+ CSV 匯入 + 覆核即執行 | 齊 | `DSM903` | `DSM904` | `S_TA_DSMM902_EXE` · view `DSMM901_V01` | — |
| `DSMM903` | 直銷公單拆帳設定 | 齊 | `DSM905` | `DSM9051` | view `OFD068A_V02` | — |
| `DSMM906` | 每月對帳單郵寄名單(業務員自維護) | 齊 | `BMS906`〔共用〕 | — | `S_TA_DSMM906_IMP` | — |

另有四個彈出子視窗(代號沿用母畫面,不列入 29):`DSMM005p0`(拷貝作業)、`DSMM901p0`(業務移轉明細)、`DSMM901p1`(業務移轉報表)、`DSMM901p2`(E-mail備註)。

### 3.2 查詢 I

| 代號 | 用途(推測) | 六層 | 資料來源 |
|---|---|---|---|
| `DSMI001` | 業務員每日收入查詢 | 齊 | `DSM006A` + `CRM002A` 權限對照 |

### 3.3 批次 B

| 代號 | 用途(推測) | 六層 | SP |
|---|---|---|---|
| `DSMB001` | 每日直銷及代銷業務員收入計算 | **缺 model / view** | `S_TA_DSMB001_EXCUTE_P01` |

**「缺 model / view」是真缺,不是命名問題。**`Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:38-39` 明白宣告 `ModelVDBType = typeof(BasicModelVDB)` / `ViewVDBType = typeof(BasicViewVDB)`,也就是**刻意用框架的泛用 VDB**,參數全靠 `Util.Parameters` 傳。對照 `architecture.md 附錄 D.4` 講的兩種假警報(`_9i` 檔名、`.Query` 專案的 `OracleDao` 命名),`DSMB001` **兩種都不是**:`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/` 底下沒有任何 `DSMB001*` 檔,也沒有 `_9i` 變體。

不過 UI 層另外做了一個東西:`Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs:8` 有一支手寫的 29 行 `DSMBViewVDB`(包一個 `DataSet`),`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:36` 用的是它。它繼承自 `BasicViewVDB` 所以傳得過去,只是那個 `UIView` 屬性從頭到尾沒人用。

### 3.4 報表 R

| 代號 | 用途(推測) | 六層 | SP | rpt(程式引用的) |
|---|---|---|---|---|
| `DSMR001` | 新開百萬客戶清冊 / 戶數統計 / 單筆申購金額統計 | 齊 | `S_TA_DSMR001_GET_1`~`S_TA_DSMR001_GET_5` | `DSMR001RPS1` `DSMR001RPS2` `DSMR001RPS3` |
| `DSMR002` | 業務部單筆申購百萬客戶清冊 / 統計(by 戶數) | 齊 | `S_TA_DSMR002_GET_1` `S_TA_DSMR002_GET_2` | `DSMR002RPS1` `DSMR002RPS2` |
| `DSMR003` | 部門 / 員工 / 單位別期間收入目標達成率排行 | 齊 | `S_TA_DSMR003_GET` | `DSMR003RPS1` `DSMR003RPS2` |
| `DSMR004` | 實際營收達成表(月 / 季 / 年報) | 齊 | `S_TA_DSMR004_GET` | `DSMR004RPS1` `DSMR004RPS2` `DSMR004RPS3` |
| `DSMR005` | 業務人員定額 / 不定額 / 168 循環年度配額達成與客戶明細 | 齊 | `S_TA_DSMR005_GET_1`~`S_TA_DSMR005_GET_3` | `DSMR005RPS1`~`DSMR005RPS6` |
| `DSMR006` | 銷售機構 / 促銷方案年度定額月統計 | 齊 | `S_TA_DSMR006_GET_1` `S_TA_DSMR006_GET_2` `S_TA_DSMR006_GET_4` `S_TA_DSMR006_GET_5` | `DSMR006RPS2` `DSMR006RPS3` `DSMR006RPS4` `DSMR006RPS6` `DSMR006RPS7` `DSMR006RPS8` |
| `DSMR007` | 業務員客戶組成表(彙總 / 明細) | 齊 | `S_TA_DSMR007_GET` | `DSMR007RPS1` `DSMR007RPS2` |
| `DSMR008` / `DSMR008_1` | 期間各基金業績(業務員別,含 / 不含申購來源);`_1` 是後綴變體,改走 Query / QryDetail 兩支 SP | 齊 | `S_TA_DSMR008_GET_1`~`S_TA_DSMR008_GET_4`;`S_TA_DSMR008_1_Query` `S_TA_DSMR008_1_QryDetail` | `DSMR008RPS1` `DSMR008RPS2` + 四個 **repo 內沒有的** |
| `DSMR009` / `DSMR009_1` | 期間各基金業績(銷售機構別 / 通路業務處 / MBR) | 齊 | `S_TA_DSMR009_GET` `S_TA_DSMR009_GET_2` `S_TA_DSMR009_GET_MBR`;`S_TA_DSMR009_1_Query` `S_TA_DSMR009_1_QryDetail` | `DSMR009RPS1`–`DSMR009RPS3` + 兩個 **repo 內沒有的** |
| `DSMR010` / `DSMR010a` / `DSMR010b` | 業務員基金別餘額彙總日報表;`a` 是變體,**`b` 已改成「境外基金每日原幣存量」** | 齊 | `S_TA_DSMR010_GET_1`~`S_TA_DSMR010_GET_3`;`S_TA_DSMR010a_GET_3`;`S_TA_DSMR010b_GET` | `DSMR010RPS1` + 三個 **repo 內沒有的** |
| `DSMR011` | 期間各業務單位淨申購 / 結存金額統計(9 種組合) | 齊 | `S_TA_DSMR011_GET` | `DSMR011RPS1`~`DSMR011RPS9` |
| `DSMR012` / `DSMR013` | 累積月平均淨申購;各基金業績表(機構 / 受益人 / 申贖明細) | 齊 | `S_TA_DSMR012_GET_2` `S_TA_DSMR012_GET_3`;`S_TA_DSMR013_GET` | **repo 內都沒有** |

**表尾那五支「repo 內沒有 rpt」不是掃描漏了。**`Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/` 只有 40 個 `.rpt`,最新的是 `DSMR011RPS9`。`DSMR008_1` / `DSMR009_1` / `DSMR010a` / `DSMR010b` / `DSMR012` / `DSMR013` 引用的報表檔名在專案裡都不存在。原因見 §7.2。

### 3.5 一眼看出差別的五件事

1. **只有兩支畫面會寄 e-mail**(`DSMM901` / `DSMM902`),而且信裡的送簽來源字串是寫死的中文,改畫面代號要一起改(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:102`)。

2. **只有兩支畫面會匯入 CSV**(同上兩支),兩支的欄位數不同(5 欄 vs 9 欄),錯誤處理的寬嚴也不同(§4.7 / §4.8)。

3. **只有一支畫面有「拷貝」功能**(`DSMM005`),而且拷貝是一整段 PL/SQL 匿名區塊直接送 DB(§4.4)。

4. **只有一支畫面完全不走四眼**(`DSMM906`)。

5. **17 支 R 畫面裡有 4 支是後綴變體**(`DSMR008_1` `DSMR009_1` `DSMR010a` `DSMR010b`),它們與本體的關係見 §7.4。

## 4. 維護畫面(M)— 一支一節

```text
[圖] DSM 維護畫面的卡控分層:UI 層、PO 層、四眼引擎,以及不走四眼的 DSMM906
圖中文字:① 用戶端(UI):十支 M 畫面的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / 業務檢核 + 總和比對 / grid 逐列檢核 / DSMM050/903 只警示不擋 / SetMasterToDetail / 把主檔鍵塞進明細 / ② 伺服端(PO):只有兩支畫面有第二道防線 / BeforeAdd/Update / DSMM901 結帳日 / BeforeAdd/Update / DSMM906 戶號歸屬 / 其餘八支 / PO 只掛取數事件 / 繞過 UI = 沒有卡控 / 風險 / ③ 四眼引擎(BaseEVADaoPO,無原始碼) / 輸入 2xx / 待驗證 / 驗證 / 待覆核 / 覆核 3xx / 生效 / DSMM902 覆核即執行 / 狀態 203 例外 / ④ 例外:一支畫面完全不走四眼 / DSMM906 / Add/Update/Delete 全 override / 手寫 INSERT/UPDATE/DELETE / 不寫 STATUS 與四眼 13 欄 / 直接落地 / 沒有待驗證/待覆核
```

*圖:圖 3 卡控順序。橘框=真正會擋下的關卡;橘虛框=風險或客戶特定;黑框=無原始碼的框架層。十支 M 畫面裡只有 DSMM901 與 DSMM906 在伺服端再驗一次,DSMM906 更是連四眼都不走。*

十支 M 畫面可以分成三群:**三支業績目標**(`DSMM001` `DSMM002` `DSMM003`,程式幾乎是同一份複製三次)、**三支歸屬與拆帳**(`DSMM005` `DSMM060` `DSMM903`)、**兩支業務移轉**(`DSMM901` `DSMM902`),外加 `DSMM050`(組織)與 `DSMM906`(對帳單名單)兩支獨立的。

### 4.1 `DSMM001` — 業務員年度業績目標

#### 用途(推測)

一位業務員、一個業績年度,設六個指標的年度總額(存 `DSM001A`),再把年度總額拆成每月的目標(存 `DSM002A`)。六個指標見 §2.3。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:69-147`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:72` |
| 2 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:75-76` |
| 3 | 明細 PK 必填 | 有列缺 PK | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:91-96` |
| 4 | 明細至少一列 | grid 空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:97-100` |
| 5–10 | **六個指標**各自的年度總額 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:123-145` |
| — | 年份不得小於 1900 | 離開欄位時 | 阻擋(`e.Cancel`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:476-486` |

**六個指標的「必須大於 0」檢核全部被註解掉**——主檔那六條在 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89`,明細那六條在 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120`。也就是說 **`DSMM001` 的六個指標全部可以是 0、甚至負數**,只要總和相符就過。

> **與 `CASM006` 的差異(§8.1)**:`CASM006` 保留了「總營業收入必須大於 0」那一條(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78`),`DSMM001` 連這條都註解掉了。**同一張表,兩個入口,一邊擋一邊不擋。**

#### 「月分配」鈕的行為

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:154-292`。可分配月數 `iMONTH_COUNT = 12 - 起算月 + 1`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196`),均分值一律 `Math.Floor`。

| 模式 | 行為 | 錨點 |
|---|---|---|
| 新增 | 先 `Clear()`,建 `iMONTH_COUNT - 1` 列均分值,**最後一列補全部餘額** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:243-291` |
| 修改 | 依 `QUO_YYMM` 排序逐列寫入,前 `iMONTH_COUNT - 1` 列均分、之後補餘額 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:210-242` |

**新增模式是對的**(餘額寫得回去,總和檢核會過)。**修改模式有一個坑**:`j` 只在 `if` 分支內遞增(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:230`),一旦 `j` 到達 `iMONTH_COUNT`,**後面每一列都會各自被寫入整筆餘額**。只要明細列數大於可分配月數(例如起算月改過、或手動加了列),按一次月分配就會讓總和爆掉,然後被第 5–10 條擋下。

#### 四眼各階段附加動作

**沒有。**`DSMM001_PO` 只掛三個取數事件(`BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData`),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:32-34`。新增 / 修改 / 刪除的寫入完全交給 `BaseEVADaoPO` 的預設實作。

#### 跨表更新

只寫 `DSM001A` + `DSM002A`。查詢時 join `COD009`(INNER)與 `SAL051`(INNER),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:126-131`。

| join | 型別 | 後果 |
|---|---|---|
| `COD009` | INNER | 員工從員工檔消失 → 這筆目標整筆查不到 |
| `SAL051` | INNER | 員工不在任何業務部門(或被 `DSMM050` 刪掉)→ 這筆目標整筆查不到 |

**兩條都是過濾(無提示)。**PO 的原始註解直接寫「`SAL051` 為直銷的員工範圍」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:112`),所以這是設計如此,不是 bug——但它同時意味著 **`DSMM050` 刪一個人,`DSMM001` 就看不到他的歷年目標**。

#### 查詢條件的組法

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:394-419` 加條件,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:134-184` 組 SQL:

| 畫面條件 | 送出的參數 | SQL 實際長相 |
|---|---|---|
| 業績年度 | `QUO_YEAR` Equal | `DSM001A.QUO_YEAR = '值'` |
| 員工代碼(起) | `EMP_NO` Equal | `DSM001A.EMP_NO >= '值'`(**運算子在 PO 內被改寫成 `>=`**) |
| 員工代碼(迄) | `EMP_NO1` Equal | `DSM001A.EMP_NO <= '值'` |
| 業務部門 | `SAL_DEPT_NO` **Like** | `SAL051.SAL_DEPT_NO LIKE '值'` |

**最後一條有陷阱**:`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148` 是 `" AND SAL051." + Row.Name + Row.Opeartor + "'" + Row.Value + "'"`,直接把運算子字串接上去,**而畫面送的值沒有加 `%`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:417-418`)。`LIKE 'S01'` 在 Oracle 等同於 `= 'S01'`,所以選一個大部門不會帶出底下的小部門。**假設**這是非預期行為,依據是同檔其他條件都明確寫 `=`,只有這一條特地改成 `Like`。

同一行還是**字串串接進 SQL**(值沒有跳脫),見附錄 E7。

#### 下拉的過濾〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:304-312`:三個員工選擇控件都設 `IS_SALE = true`、`SAL_CD = "B,C"`、`Filter = "(LEAVE_DATE >= '<今年>/01/01' OR LEAVE_DATE IS NULL)"`。也就是**只挑業務屬性 B 或 C、且不是往年離職的人**。今年才離職的人**選得到**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:75-76` |
| 按新增 / 修改前 | 六個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:91-100` |
| 按新增 / 修改前 | 明細每列六個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:123-145` |
| 按查詢前 | 員工代碼起迄成對 | 只填一邊 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:398-399` |
| 查詢時 | 員工不在 `COD009` 或不在 `SAL051` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:126-131` |
| 查詢時 | 部門條件用 `LIKE` 但不補 `%` | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148` |
| 選部門時 | 清掉已選的員工起迄 | 部門有值 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:488-502` |
| 選員工時 | 起填了、迄沒填 → 自動補成一樣 | 是 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:469-473` |
| 按月分配 | 明細列數 > 可分配月數時餘額重複寫 | 是 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:215-241` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.2 `DSMM002` — 業務單位年度業績目標

#### 用途(推測)

與 `DSMM001` 結構完全平行,但鍵從「員工」換成「單位」(`DEPT_NO`),六個指標一模一樣。

#### 與 `DSMM001` 的三個實質差異

| 面向 | `DSMM001` | `DSMM002` | 錨點 |
|---|---|---|---|
| **可分配月數** | `13 - 起算月` | **固定 12** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:201-206` |
| **會不會跨年** | 不會(月份鎖在年內) | **會**:起算月非 1 月時,`iQUO_Month > 12` 的那幾列會寫成「次年 + 月」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:254-255`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:279-280` |
| **查詢的員工起迄檢核** | 有 | **整段被註解** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` |

**第二列是關鍵**:同一份「起算年月 = 2026/07」的設定,在 `DSMM001` 會產生 6 列(202607–202612),在 `DSMM002` 會產生 12 列(202607–202712)。**兩支畫面對「年度目標」的定義不一樣**,而且畫面上沒有任何文字說明。

第三個差異還有一個連帶效果:`DSMM002` 的「月分配」是靠 `DSM008A.Rows.Count > 0` 決定走哪一個分支(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:208`),而 `DSMM001` 是靠 `ActionMode`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:210`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:243`)。結果一樣,但讀 code 時很容易對錯。

#### 取數 SQL 的部門對照〔客戶特定〕

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:126-127`:

```
LEFT JOIN OFD002
  ON OFD002.DEPT_NO = DECODE(DSM007A.DEPT_NO, 'S', 'G', '090', 'I', DSM007A.DEPT_NO)
```

也就是說 **`DSM007A` 存的部門代碼 `S` 要對到 `OFD002` 的 `G`、`090` 要對到 `I`**,其餘原樣。這是寫死在 SQL 裡的兩筆對照,不是設定檔,換站台一定要重問。好消息是這裡用的是 `LEFT JOIN`,對不到只是名稱空白,不會整筆消失(對照 `DSMM001` 的兩個 INNER JOIN)。

#### 下拉的過濾

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:302-303`:兩個部門控件的 `Filter` 都是 `LEN(DEPT_NO) = 5`,註解寫「只顯示5碼部門代碼」。**所以 3 碼的大部門在這支畫面選不到**,但資料庫裡可以存(檢核不擋),見附錄 E。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:75-76` |
| 按新增 / 修改前 | 六個指標 > 0(主檔與明細) | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:78-89`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-120` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:91-100` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:123-145` |
| 按查詢前 | 員工代碼起迄 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` |
| 查詢時 | 部門條件用 `LIKE` 但不補 `%` | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:146` |
| 選部門時 | 只能選 5 碼部門 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:302-303` |
| 按月分配 | 固定切 12 個月,會跨年 | 起算月 ≠ 1 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:254-255` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.3 `DSMM003` — 業務員×基金型別年度淨銷售目標

#### 用途(推測)

與前兩支同樣是「年度總額 + 月分配」,但只有**一個**指標(`QUO_NET_IN` 淨銷售金額),而且主鍵多一個 `FUND_TYPE_SALE`(基金型別),也就是同一位業務員可以對不同基金型別各設一組目標。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:62-94`。**這支是三兄弟裡唯一沒有把「必須大於 0」註解掉的**:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:68-69` |
| 2 | **年度淨銷售金額 > 0** | `< 1` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:71-72` |
| 3 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:74-83` |
| 4 | **每列淨銷售金額 > 0** | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:87-88` |
| 5 | 年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:90-92` |

#### 「月分配」鈕的實質缺陷

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:103-178`。可分配月數算 `12 - 起算月 + 1`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:121`),**但修改模式補餘額的判斷式寫死 `j < 12`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130`)。

後果:起算月不是 1 月時,明細列數只有 `iMONTH_COUNT`(< 12),迴圈裡 `j` 永遠到不了 12,**每一列都拿到均分值,餘額從來沒寫回去**。而 `Math.Floor` 幾乎一定會有餘數 → 總和小於年度總額 → 第 5 條把存檔擋下來 → 使用者必須手動改最後一列。

**新增模式沒有這個問題**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:143-177` 用的是 `iMONTH_COUNT - 1` 加一列補餘額)。所以**同一筆資料,第一次建立時月分配是對的,之後改年度總額再按一次就錯**。這是本模組最會咬人的三個缺陷之一(附錄 E3)。

#### 取數 SQL:一個會被查詢條件毀掉的 `LEFT JOIN`

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:120-126`:

```
FROM DSM003A JOIN COD009 ON COD009.EMP_NO = DSM003A.EMP_NO
LEFT JOIN SAL051 ON SAL051.EMP_NO = DSM003A.EMP_NO AND SAL051.SAL_CD = 'C'
```

刻意用 `LEFT JOIN`(不在 `SAL051` 的人也查得到,只是部門顯示空白)。**但只要使用者在查詢畫面選了部門**,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` 會在 `WHERE` 後面加 `AND SAL051.SAL_DEPT_NO = '值'`,這一條會**把 `LEFT JOIN` 變回 INNER JOIN**(NULL 不等於任何值)。

也就是說:**不填部門查得到的資料,填了部門就永遠查不到**——即使那個人真的在該部門、只是 `SAL_CD` 不是 `C`。過濾(無提示)。

#### 下拉的過濾〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:196-216`:

| 控件 | 條件 |
|---|---|
| 基金型別 | 代碼分類 `412`,再用 `RowFilter = "TextValue<>'C'"` **把 `C` 這一項拿掉** |
| 部門 | `(LEN(DEPT_NO) = 5) AND ((DEPT_NO LIKE 'S0%') OR (DEPT_NO LIKE '08%'))` |
| 員工(三個控件) | `IS_SALE = true`、`SAL_CD = "C"`、不是往年離職 |

注意**員工的 `SAL_CD` 在這支是 `"C"`,`DSMM001` 是 `"B,C"`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:305`)。同樣是「選業務員」,兩支畫面的候選人集合不同。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:68-69` |
| 按新增 / 修改前 | 年度淨銷售金額 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:71-72` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:74-83` |
| 按新增 / 修改前 | 年度 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:90-92` |
| 按查詢前 | 員工代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:279-283` |
| 查詢時 | 員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:121-122` |
| 查詢時 | 有填部門 → `LEFT JOIN` 退化成 INNER | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` |
| 選基金型別時 | 代碼 `C` 被拿掉 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:202-204` |
| 選部門時 | 只看 `S0` 與 `08` 開頭的 5 碼部門 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:205` |
| 按月分配 | 修改模式餘額從不寫回 | 起算月 ≠ 1 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.4 `DSMM005` — 離職業務分攤比率

#### 用途(推測)

某個業績年月、某個部門,離職業務員留下來的業績要按什麼比率分給部門裡的哪些人。grid 裡每一列是一個人 + 一個比率,**全部比率加起來必須是 100**。

這是全模組唯一的**多筆型 EVA**(`BaseMultiRowEVADaoPO`):`QUO_YYMM` + `DEPT_NO` 是「一組」的鍵,一組裡的 N 個人一起送審。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:391-451`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:399-402` |
| 2 | 至少一列有員工代碼 | 全空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:405-409` |
| 3 | 每列分攤比率 >= 0 | 有負數 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:412-416` |
| 4 | **分攤比率加總 = 100** | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:419-423` |
| 5 | 新增模式:此年月 + 部門不可已存在 | 查得到 | 阻擋(先送一次查詢去 DB 確認) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:431-448` |

第 5 條是本模組唯一一處「**存檔前先打一次 DB 確認重複**」的寫法,其他畫面都靠主鍵違反去擋。

#### 「加入部門組織成員」鈕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:483-530`:一次把部門底下的人全部帶進 grid,比率預設 0。

| 行為 | 說明 | 錨點 |
|---|---|---|
| 必須先選部門 | 沒選就跳訊息並 `return` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:486-490` |
| **部門代碼第 1 碼是 `S`** → 走直銷分支(`IS_SALE` + `SAL_DEPT_NO` + `SAL_CD = 'C'`);否則只用 `DEPT_NO` | `Substring(0, 1)` 位置取值 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:494-506`〔客戶特定〕 |
| 排除往年離職者 | `LEAVE_DATE.Substring(0, 4)` 取年份 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:514-517` |
| 已在 grid 的人跳過 | 靠 `EMP_NO` 比對 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:518` |

兩個位置取值都沒有長度保護:部門代碼是空字串時 `Substring(0,1)` 會丟例外(前面的必填檢核擋住了),離職日格式不是 `yyyy…` 時 `Convert.ToInt16` 會丟例外(附錄 E6)。

#### 「拷貝」鈕與那段 PL/SQL

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:536-543` 開 `DSMM005p0`,按確定後走 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:191-318` 的 `Copy`。

流程:先數來源筆數(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:201-215`),0 筆就回失敗;否則送一整段 **PL/SQL 匿名區塊**,用 `WHILE` 迴圈從目的起月跑到目的迄月,每個月 `INSERT … SELECT` 一次(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:224-278`)。

這段有五個要記住的地方:

| 項 | 內容 | 錨點 |
|---|---|---|
| **GUID 只產一次** | `xNEW_GUID` 在迴圈**外面**算,每一個月、每一列 `INSERT` 都用同一個值當 `DATAID` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:237-244` |
| **直接寫成已覆核** | `STATUS` 照抄來源列,`ENTRYID` / `VERIFYID` / `APPROVEID` 一次填滿、`REJECTID` 填空白 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:264-276` |
| **已存在的年月直接跳過** | `DECODE(COUNT(*),0,'Y','N')` 判斷,`N` 就 `CONTINUE`,不覆蓋也不提示 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:254-262` |
| **`SYSDATE ASENTRYDATE`** 別名黏字 · **成功卻回報失敗** | 前者靠位置對應所以執行沒事;後者是 `i = ExecuteNonQuery(匿名區塊)` 對 PL/SQL 區塊通常回 0 或 -1,而程式用 `if (i > 0)` 判成功 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:271`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:290-302` |

最後一條的實際表現是「資料明明複製進去了,畫面卻顯示『查無可拷貝的資料 或 資料已存在。』」(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:87-91`)。**假設**:依據是 `ExecuteNonQuery` 對非 DML 敘述的回傳值定義,以及同檔 `Copy` 前半段用 `ExecuteScalar` 數筆數時就沒有這個問題。要確定得實跑一次。

#### 彈出視窗 `DSMM005p0` 的檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:110-155`:

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 來源業績年月必填 · 目的業績年月起迄皆必填且起 ≤ 迄 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:115-132` |
| 部門起迄要嘛都填要嘛都空 · 部門起 ≤ 部門迄 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:138-147` |

**沒有任何一條檢查「來源年月 ≠ 目的年月」**,也沒有檢查目的區間長度。把來源設成 202601、目的設成 202601–203012,會送出一段跑 60 次迴圈的 PL/SQL。

另外:所有錯誤訊息都掛在 `umskQUO_YYMM` 這一個控件上(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:125`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:141`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:146`),即使講的是部門欄的問題,紅框也會標在年月欄上。

#### 查詢的取數

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:117-153`。條件由共用 helper `EVAStringHelper.AddParam` 產生(參數化,**這是全模組少數有綁參數的取數 SQL**),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:136` 一次宣告六個條件名。`OFD002` 是 `LEFT JOIN`,部門名稱查不到只會空白。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 至少一列有員工 | 全空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:405-409` |
| 按新增 / 修改前 | 分攤比率加總 = 100 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:419-423` |
| 按加入成員 | 往年離職者不帶進來 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:514-517` |
| 拷貝 | 來源 = 目的、區間過長 | — | **完全沒有檢核** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:110-155` |
| 拷貝成功 | 回報值判斷式可能永遠為假 | 是 | 記錄不擋(誤報失敗) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:295-302` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.5 `DSMM050` — 業務部門與人員設定

#### 用途(推測)

主檔 `SAL050` 一個業務部門一列(部門屬性、主管獎金計算類別);明細 `SAL051` 是部門底下的人(業務屬性、獎金制度)。**這是整個直銷業務組織的來源**,`DSMM001` `DSMM003` `DSMM901` `DSMM902` `DSMM903` 五支畫面的員工範圍都由它決定(§8.5)。

#### 部門代碼長度決定一切

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:154-240` 的 `DoValidate` 把「部門代碼幾碼」當成主要分支:

| 部門代碼長度 | 部門屬性(`DEPT_CD`)的限制 | 明細業務屬性(`SAL_CD`)的限制 | 錨點 |
|---|---|---|---|
| **5 碼** | 不可為 `0`(大部門) | 不可為 `A`(部門主管);`DEPT_CD = 'A'` 時不可為 `D` / `E`;`DEPT_CD = 'S'` 時不可為 `B` / `C` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:170-176`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:197-216` |
| **3 碼** | 只能是 `0` | **只能是 `A`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:178-184`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:219-226` |
| 其他長度 | **不檢核** | **不檢核** | 同上,兩個 `if` 都只認 3 與 5 |

最後一列是實質漏洞:輸入 4 碼或 6 碼的部門代碼,上面所有規則一條都不會跑。

#### 逐列檢核與存檔前檢核,兩套規則兩種嚴格度

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:346-430` 的 `BeforeRowUpdate` 是另一套:

| `DEPT_CD` | 逐列規則(`BeforeRowUpdate`) | 存檔前規則(`DoValidate`) |
|---|---|---|
| `0` | `SAL_CD` **必須**是 `A` | 只有 3 碼部門才要求 `A` |
| `A` | `SAL_CD` **必須**是 `B` 或 `C` | 只擋 `D` / `E` |
| `S` | `SAL_CD` **必須**是 `D` 或 `E` | 只擋 `B` / `C` |
| 其他 | 不檢核 | 不檢核 |

方向一致,但**逐列那套嚴格、存檔那套寬鬆**;而且**逐列那套的四處 `e.Cancel = true;` 全部被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:373`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:382`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:394`),只剩訊息與紅框。**結論:逐列規則全部是「警示(不擋)」,真正的閘門是比較寬的那一套。**

還有一個小坑:`BeforeRowUpdate` 的每一段檢核前都先 `ValidateErrList.Clear()`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:360`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:369`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:378`),所以**一次只會看到最後一條錯誤訊息**。

#### 下拉與挑人〔客戶特定〕

| 項目 | 來源 | 錨點 |
|---|---|---|
| 部門屬性 / 主管獎金類別 | 代碼分類 `458` / `459`,**用 `GetDropDownDataSrc`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:115-117` |
| 查詢結果 grid 的同兩欄 | 同樣是 `458` / `459`,但**改用 `GetDropDown9iDataSrc`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-78` |
| 明細的業務屬性 / 獎金制度 | 代碼分類 `460` / `461`,`GetDropDown9iDataSrc` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:79-80` |
| 挑員工時的條件 | `AO_CODE = 'Y'` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |
| 明細新列預設值 | `SAL_CD = "C"`、`BONUS_TYPE = "1"` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:320-321` |

**同一個代碼分類用兩套 DataSource 實作**(`GetDropDownDataSrc` 與 `GetDropDown9iDataSrc`),兩者都無原始碼、從呼叫端反推。維護畫面與查詢結果拿到的清單如果不一致,就是從這裡來的。

#### 取數 SQL

| 段 | 寫法 | 風險 |
|---|---|---|
| 主檔 | `FROM SAL050 JOIN OFD002 ON SAL050.SAL_DEPT_NO = OFD002.DEPT_NO`(INNER) | 部門不在 `OFD002` → 整筆查不到(過濾,無提示);`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127` |
| 明細 | `FROM SAL051,COD009 WHERE … SAL051.EMP_NO = COD009.EMP_NO`(舊式逗號 join,等同 INNER) | 員工不在 `COD009` → 該列消失(過濾,無提示);`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178-180` |
| `ORDER BY` | **被註解掉,而且註解裡寫的還是 `DSM003A` 的欄位** | 查詢結果沒有固定排序;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:150` |

**這支 PO 是全模組唯一會對查詢值做單引號跳脫的**:`Row.Value.Replace("'", "''")`,三處(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:139`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:190`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:200`)。其他 PO 全部直接串。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 屬性 `A` 不可配 `D` / `E`;屬性 `S` 不可配 `B` / `C` | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:206-214` |
| 挑員工時 | `AO_CODE = 'Y'` | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |
| 查詢時 | 部門不在 `OFD002` / 員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178-180` |
| 按查詢前 | **完全沒有檢核** | — | — | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:282-292` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.6 `DSMM060` — 受益人歸屬業務員〔共用表〕

#### 用途(推測)

一個受益人戶號歸給一位業務員 + 一個業務部門,加一個歸屬日期。主檔是 `OFD374A`——**OFD 前綴的表,但唯一的維護畫面在 DSM**。BMS 那側怎麼用它見 §8.2。

#### 這支畫面有多小

PO 只有 77 行,沒有任何 `BeforeAdd` / `BeforeUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:28-34` 只掛三個取數事件);UI 187 行,`DoValidate()` 只呼叫框架的欄位驗證(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:50-55`)。**所以「這個戶號是不是已經歸給別人」「這個業務員是不是真的在這個部門」在存檔時完全不檢查**,只靠下拉的連動。

#### 歸屬日期永遠是今天

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:85-86`(新增)與 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:96-97`(修改)都做同一件事:

```
udatBELONG_DATE.DateTime = DateTime.Today;  udatBELONG_DATE.ReadOnly = true;
```

**修改一筆舊資料,歸屬日期會被改成今天**,而且欄位是唯讀的、使用者救不回來。查詢頁的歸屬日期倒是可以自己輸入當條件(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:103-104`)。

#### 下拉連動

| 事件 | 行為 | 錨點 |
|---|---|---|
| 選業務員之前沒選部門 | 跳「須先選擇業務部門。」並 `e.Cancel = true` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:152-159`(維護頁)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:177-184`(查詢頁) |
| 換部門 | 清掉已選的業務員,並把新部門傳給員工控件 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:141-145`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:166-170` |
| 修改模式載入時 | **先解除再重掛**「選業務員前」事件,避免載入既有值時跳警告 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:91`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:95` |

#### 取數 SQL:四張表全是 INNER JOIN

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:48-62`:

```
select a.*, b.bf_name, c.dept_sh_nm, d.emp_name from ofd374a a
  join bms001a b on a.bf_no = b.bf_no
  join ofd002  c on a.sal_dept_no = c.dept_no
  join cod009  d on a.emp_no = d.emp_no
```

三個 INNER JOIN,任何一個對不到,整筆歸屬資料就在畫面上消失。**這一條對 §8.2 很重要**:`RSPM004` 會直接 `INSERT OFD374A`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700`),如果它寫進去的部門代碼不在 `OFD002`,`DSMM060` 就永遠看不到那筆,也改不掉。過濾(無提示)。

好消息:這支 PO 的條件是用 `EVAStringHelper.AddParam(dbProduct, args.DbCmd, …)` 產生的**綁定參數**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:58`),不是字串串接——全模組只有 `DSMM060`、`DSMM005`、`DSMM901`、`DSMM902` 做到這一點。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 業務員是否屬於該部門 | — | **完全沒有檢核**(只靠下拉過濾) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:144` |
| 選業務員前 | 必須先選部門 | 沒選 | 阻擋(`e.Cancel`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:152-159` |
| 新增 / 修改時 | 歸屬日期強制為今天且唯讀 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:85-86`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:96-97` |
| 查詢時 | 戶號不在 `BMS001A`、部門不在 `OFD002`、員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:50-56` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.7 `DSMM901` — 業務移轉申請(戶號層)

#### 用途(推測)

一批(`BATCHID`)要移轉的客戶:每一列是「戶號 + 移轉前銷售機構 / 業務員 → 移轉後銷售機構 / 業務員」。走完四眼、覆核通過後,由人工按「執行」呼叫 SP 真正搬資料,搬完把當時庫存寫回 `EXEAUM`。**每一段狀態變化都寄一封信給下一關。**

#### 期別(`BATCHID`)怎麼產

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:58-75`:

```
SELECT NVL(MAX(DSM901.BATCHID) + 1, <今年>001) FROM DSM901 WHERE DSM901.BATCHID > <今年>000
```

年份用 `DateTime.Today.Year` 直接 `string.Format` 進 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:62`)。**沒有鎖、沒有序列**,兩個人同時新增會拿到同一個號(附錄 E5)。拿到號之後,主檔與明細的 `BATCHID` 一起被覆寫(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:66-74`),同時把 `EXESTATUS` 強制設成未執行、清掉執行時間與執行者。

#### 唯一的伺服器端卡控:執行基準日不可大於結帳日

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:180-200`:

```
SELECT MAX(CTL_DATE) FROM OFD303A A WHERE A.POST_CTL_CODE = 'Y'
   AND CTL_DATE < (SELECT MIN(CTL_DATE) FROM OFD303A WHERE POST_CTL_CODE = 'N')
```

取「最後一個已結帳、且早於第一個未結帳」的日期,基準日晚於它就擋下(`args.Cancel = true`,訊息「執行基準日不可大於結帳日yyyy/MM/dd」)。

三個要注意的:**只有 `EXESEQ == 1` 才檢查**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184`),第二次以後的移轉完全不驗結帳日;`DSM901[0]` 直接取第一列,主檔 0 列時會丟例外(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:183`);`BeforeAdd` 第一行寫成 `if (args.TableName != "DSM901" || CheckExeDATE(args)) return;`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:56`),檢核不過就直接 `return`、**連 `BATCHID` 都不會配**(結果是對的,但讀起來很容易以為漏了)。

#### CSV 匯入:五欄,而且兩道檢核被註解掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:400-491`。「下載範本」鈕只寫一行標題,不含任何資料列(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:493-510`):

```
戶號,移轉前銷售機構代碼,移轉前業務員代碼,移轉後銷售機構代碼,移轉後業務員代碼
```

匯入的逐列處理:

| 步驟 | 行為 | 錨點 |
|---|---|---|
| 第一行當標題丟掉 | 空字串就整個放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:419` |
| **欄數不足 5 就 `break`** | **無訊息、無記錄**,檔案後半直接被丟掉 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:426` |
| 戶號轉數字失敗 · 主鍵重複 | 各自跳訊息並整批放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:428-436`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:462-466` |
| 員工代碼補 0 到 6 碼 | 前後兩個都補 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:439-440`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:450-451`〔客戶特定〕 |
| **「移轉後機構必須是直銷」與「移轉前後不可完全相同」** | **兩段都被註解**,理由分別是「20190808 不檔移轉後需為直銷單位」與「鳳滿說為了活化1不擋 20180820」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` |
| 全部讀完後送 `CheckExists` | 成功才把 grid 換成回傳的資料 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:470-480` |

CSV 讀檔用 `new StreamReader(檔名)`(預設編碼)、寫範本用 `Encoding.Default`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:500`),兩邊不對稱,而且都吃作業系統的 codepage。

#### 逐筆新增(`DSMM901p0`)比 CSV 嚴格

雙擊 grid 的空白列會開 `DSMM901p0`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:357-378`)。它的檢核有三條,**其中兩條就是 CSV 匯入被註解掉的那兩條**:

| 檢核 | 錨點 |
|---|---|
| 戶號 + 移轉前機構 + 移轉前業務員 不可重覆 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:55-62` |
| **銷售機構及員工代碼修改前後不可都一樣** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:64-65` |
| 移轉前業務員留空時,該戶號必須真的有該機構的「公單」交易 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:67-75` |

**同一張表、同一個畫面,用手打跟用 CSV 匯入,規則不一樣。**這是本模組最值得先問清楚的一件事。

`DSMM901p0` 的候選清單來自 `GetEmpNo`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:278-324`):對 `OFD306A` 與 `OFD306` 各跑一次「取基準日之前最後一次異動、且累計單位數 > 0」的查詢,`UNION ALL` 之後再取最新的一筆。也就是**只有「還有庫存」的機構 / 業務員組合才選得到**。查無資料時回一句「查無有庫存之業務員資料」但 `ReturnCode` 仍是 `true`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:314`)——訊息有、不擋。

#### `CheckExists`:逐列打五次 DB

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:330-464`。對 grid 的每一列,依序驗:戶號在 `BMS001A`、移轉前機構在 `OFD068A_V02`、移轉後機構在 `OFD068A_V02`、移轉前員工在 `COD009`、移轉後員工在 `COD009`。任何一條不過就**清空整個明細**並回錯誤訊息。

兩個要記住的:**移轉後員工的檢核在 2019 年被降級**——原本準備了 `sqlEm`(要求員工同時在 `SAL051` 的移轉後部門、且未離職,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:346-354`),但實際執行的那一行被換成只查姓名的 `sqlEmpNM`,舊的留在註解裡(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430`);**`DSMM902` 到今天還在用 `sqlEm`**(§4.8)。另外**「戶號必須有該機構 / 員工的結餘」整段被註解**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:355-369` 的 SQL 與 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` 的呼叫),理由同樣是「鳳滿說為了活化1不擋 20180820」。

`OFD068A_V02` 這支 view 本身有兩個已知問題,對這裡的影響見 §8.6。

#### 執行與列印

| 動作 | 呼叫 | 回傳處理 | 錨點 |
|---|---|---|---|
| 執行(`DoExp1`) | `S_TA_DSMM901_EXE`(IN:期別、執行者) | **SP 沒有 OUT 參數**,只要不丟例外就 `tran.Commit()` 並回「執行成功」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:470-500`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:512-531` |
| 列印(`DoExp2`) | `S_TA_DSMM901_GET`(IN:期別、比較日、機構;OUT:兩個游標) | 明細 0 筆但主檔有 → 「未執行不可列印」;都 0 → 「查無資料」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:506-533` |
| 覆核 / 新增後重算庫存 | `S_TA_DSMM901_AUM`(IN:期別) | 沒有回傳判斷 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:127-140` |

**`S_TA_DSMM901_AUM` 那段有一個明確的 bug**:`cmd` 建立一次,然後在 `foreach` 裡對每一列 `AddInParameter(cmd, "wBATCHID", …)`,**中間沒有 `Parameters.Clear()`**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:131-139`)。主檔只有一列時看不出來,多列就會在同一個 command 上重複加同名參數。附錄 E5。

#### 寄信

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:96-116` 組信、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:118-125` 依角色取收件人。每一段的收件人:

| 事件 | 收件人 / 副本 | 錨點 |
|---|---|---|
| 新增 / 修改 / 刪除 / 復原刪除 / 重送後 | V,副本 E | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:287-295`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:321-334` |
| 驗證後 | A,副本 E | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:297-300` |
| 覆核後 | E + V,無副本 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:302-305` |
| 退回後 | 有覆核權限的人退 → E;否則 → V(副本 E) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:313-319` |

**寄件人是登入者的 e-mail,空的話用寫死的 `ta-it@example.com`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:111-113`)〔客戶特定〕。而且 `SendMail` 第一行會先看 `Util.Result[0].ReturnCode`,前一步失敗就不寄(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:98`)。

#### 兩個會改資料但不是卡控的行為

**改執行基準日 → 明細全刪**(`udatEXEDATE.ValueChanged` 直接把 `DSM902` 每一列 `Delete()`,沒有任何確認,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:543-547`);**載入已執行的批次 → `EXESEQ` 就地加 1**(在 `ModifyDataLoad` 裡改 row 的值,只是為了給明細的 `SEQ` 當預設值,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:207-209`)。前者在新增模式綁在 `AddDataLoad`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:183-184`)、修改模式只在「還沒執行過」時才綁(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:211-212`)——設計是對的,但這種「設值後才綁事件」的寫法很容易在改 code 時破功。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 已執行的批次要有新增 / 修改過的明細 | 全是舊列 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:74-82` |
| 按修改前 | 跳出「E-mail備註」視窗,按取消就中止 | 按取消 | **詢問** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:282-285` |
| 按退回前 | 同上 | 按取消 | **詢問** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:307-311` |
| 新增 / 修改(PO) | 第一次移轉時,執行基準日不可大於結帳日 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:192-197` |
| 新增 / 修改(PO) | 第二次以後不驗結帳日 | 永遠 | **記錄不擋** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184` |
| 選執行基準日 | 不可大於今天 | 是 | 阻擋(控件 `MaxDate`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:156` |
| 改執行基準日 | 明細全部刪除 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:543-547` |
| CSV 匯入 | 欄數 < 5 的那一行起,整個檔案不再讀 | 是 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:426` |
| CSV 匯入 | 移轉後機構須為直銷 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448` |
| CSV 匯入 | 移轉前後不可完全相同 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` |
| 手動新增明細 | 移轉前後不可完全相同 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:64-65` |
| 手動新增明細 | 前業務員留空時須有該機構公單交易 | 否 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:67-75` |
| 手動新增明細 | 可選的機構 / 員工限「基準日前還有庫存」的組合 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:283-309` |
| 送出前檢查 | 戶號 / 前後機構 / 前後員工 任一查不到 | 是 | 阻擋(且清空整個明細) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:373-454` |
| 送出前檢查 | 移轉後員工須屬於移轉後部門且未離職 | — | **被降級成只查姓名** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430` |
| 送出前檢查 | 戶號須有該機構 / 員工的結餘 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` |
| 按執行鈕 | 只有狀態 `3` 開頭且未執行過才亮 | 不符 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:215-216` |
| 執行結果 | SP 沒有錯誤回傳通道 | 永遠 | **記錄不擋(一律回成功)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:481-486` |
| 刪除 | 已執行過(`EXESEQ > 1`)不可刪 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:219-222` |

### 4.8 `DSMM902` — 業務移轉申請(申購書層)

#### 用途(推測)

跟 `DSMM901` 同一件事,但顆粒度到「單一張申購書」(`ALLOT_NO` + `ALLOT_SRNO`),而且要先選境內 / 境外(`FUND_TYPE`)。移轉前後都可以換銷售機構**別**(`AGENT_ID`),不像 `DSMM901` 鎖死直銷。

#### 與 `DSMM901` 的差異總表

| 面向 | `DSMM901` | `DSMM902` | 錨點 |
|---|---|---|---|
| 覆核通過後 | 人工按執行 | **自動 `DoExp1()`**,且原本的「執行」通知信被註解掉 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:274-282` |
| 刪除覆核 | 沒有特例 | **狀態 `203`(刪除待覆核)時不跑 SP** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` |
| SP 錯誤回傳 | 無 | `strMsg` OUT 非空 → `tran.Rollback()` + 顯示訊息 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:476-490` |
| 移轉後員工檢核 | 只查姓名 | **查姓名 + 部門 + 未離職** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:433-447` |
| 執行基準日上限 | `MaxDate = 今天` | **那一行被註解掉,可選未來日** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` |
| 執行基準日 vs 結帳日 | 有檢核 | **`BeforeUpdate` 是空的 `{ };`** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81` |
| 改基準日會不會清明細 | 會 | **事件方法是空的** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:513-515` |
| 列印 | 有(`DoExp2` 開 `DSMM901p1`) | **`DoExp2` 是空的** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:508-511` |
| CSV 欄數 | 5 | 9 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:477` |

**第五、六列合起來是實質風險**:`DSMM902` 的執行基準日既沒有「不可大於今天」也沒有「不可大於結帳日」,完全不驗。

#### CSV 匯入(9 欄)

範本標題(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:477`):

```
戶號,申購書號,申購序號,移轉前銷售機構別,移轉前銷售機構代碼,移轉前業務員代碼,移轉後銷售機構別,移轉後銷售機構代碼,移轉後業務員代碼
```

| 步驟 | 行為 | 錨點 |
|---|---|---|
| 欄數不足 9 就 `break` | **無訊息**,同 `DSMM901` 的毛病 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:401` |
| 戶號 / 申購序號轉型失敗 | 各自跳訊息並整批放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:403-421` |
| 員工代碼補 0 到 6 碼 | 前後都補 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:425-431`〔客戶特定〕 |
| 主鍵重複 | 訊息含戶號與申購書號 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:436-440` |

**`DSMM902` 的 CSV 匯入沒有「移轉前後不可相同」的檢核,也沒有對應的逐筆新增彈出視窗**——`DSM904` 的明細只能靠 CSV 進來(grid 用 `GridLayoutNoUpdate`,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:130-131`)。

#### `CheckExists` 的四段檢核

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:294-458`,逐列:

| 段 | 查什麼 | 特別之處 | 錨點 |
|---|---|---|---|
| 1 | 戶號在 `BMS001A` |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:356-365` |
| 2 | 申購書在 `OFD221A`(境內)或 `OFD221`(境外),**而且只能剛好 1 筆** | 順便把基金 / 淨值 / 金額 / 單位數帶回畫面 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:366-391` |
| 3 | 移轉前 / 後機構在 `OFD068A`(境內)或 `OFD068` (境外) |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:392-417` |
| 4 | 移轉前員工在 `COD009`;**移轉後員工要在 `SAL051` 的移轉後部門且未離職** | 這就是 `DSMM901` 放掉的那條 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:418-447` |

境內 / 境外的切換不是用 `if`,而是**把 `FUND_TYPE` 綁成參數塞進 `WHERE` 當開關**:`AND :FUND_TYPE = '2'` 的那一段與 `AND :FUND_TYPE = '1'` 的那一段用 `UNION` 接起來,哪一段成立就只有那一段回資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:323-336`)。取數 SQL 也用同一招(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:222`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:260`)。這個寫法能跑,但**兩段的 join 對象不同**(境內接 `OFD081V` + `OFD068A`,境外接 `OFD081` + `OFD068` + `FSK003`),看的時候要分開讀。

#### 兩個空掛的事件

`DSMM902_PO` 的 `AfterGetMaintainData`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:105-108`)、`BeforeUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81`)、`AfterUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:115-118`)三個方法**都是空的或只有一行 `return`**,但建構子照樣把它們掛上去。對照 `DSMM901` 的同名方法都有實際內容——這幾個空殼是複製 `DSMM901` 之後沒刪乾淨的,**不要以為 `DSMM902` 也會重算庫存**(它不會,`DSM904` 也沒有 `EXEAUM` 這個欄位)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選執行基準日 | 不可大於今天 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` |
| 新增 / 修改(PO) | 執行基準日 vs 結帳日 | — | **方法是空的** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81` |
| 修改模式 | 已執行 或 自己是驗證 / 覆核者 → 鎖匯入、鎖基準日、鎖修改與刪除 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:189-198` |
| CSV 匯入 | 欄數 < 9 的那一行起,整個檔案不再讀 | 是 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:401` |
| 覆核通過 | 狀態不是 `203` 就自動執行 SP | 是 | 記錄不擋(自動動作) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277-281` |
| 執行結果 | SP 的 `strMsg` 非空 | 是 | 阻擋(rollback + 顯示訊息) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:484-490` |
| 刪除 | 已執行 / 驗證 / 覆核狀態不可刪 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:189-198` |

### 4.9 `DSMM903` — 直銷公單拆帳設定

#### 用途(推測)

一個受益人戶號,原本掛在直銷的「公單」(`AGENT_CODE` 以 `S` 開頭)底下。這支畫面設定:公單這一側掛哪個機構 / 主管(B 側),以及各段期間實際服務的業務員(A 側),兩邊按 `RATE_B` / `RATE_A` 拆帳;A 側還可以設業績上限 `MAX_BAL_AMT_A`(0 表示無上限)。

#### 四個寫死的常數〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29`:

```
static string myAGENT_ID = "0";        static string myAGENT_CODE_LIKE = "S%";
static string myAGENT_ID_B = "0";      static string myAGENT_ID_A = "0";
```

存檔時原封不動寫進主檔與每一列明細(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:51-53`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:70-72`)。**其中 `AGENT_ID` 與 `AGENT_CODE_LIKE` 還是主鍵的一部分**(§0.5),等於主鍵有兩欄永遠是同一個值。想支援非直銷,得同時改這四個常數、主鍵設定與取數 SQL。

用 `static` 存這種常數在 WinForms 單一使用者的情境不會互踩,但它與 BMS 的 `BMSB901A` 那條「靜態批號被兩人同跑互刪」是同一種寫法(`bms.md 附錄 E`),看到要警覺。

#### 開畫面就可能爆掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:200-218`:

```
if (view.UIView.DSHead_INFO.Count > 0) this._DSHead_INFORow = view.UIView.DSHead_INFO[0];
...
this.custEMP_NO_B.Filter = string.Format(" EMP_NO = '{0}'", this._DSHead_INFORow.EMP_NO);
```

`if` 有判斷,但**下面那行無條件用 `_DSHead_INFORow`**。`GetDSHeadInfo` 撈的是「`SAL051` 裡 `SAL_CD = 'A'` 且 `COD009.LEAVE_DATE` 為空」的人(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258`)。**只要沒有任何在職的部門主管,這支畫面在 `FormInitial` 就丟 `NullReferenceException`,根本開不起來。**`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` 還有第二次同樣的用法。附錄 E1。

順帶一提:`GetDSHeadInfo` 讀了 `model.Utility.PermissionInfo[0].UserID` 存進區域變數 `user_id`,**然後完全沒用到**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:247`)。看起來原本想按登入者篩主管,後來改成撈全部。

#### 拆帳比例的檢核只有一半

| 行為 | 說明 | 錨點 |
|---|---|---|
| 新增時 `RATE_B` 預設 30 | 寫死 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:276`〔客戶特定〕 |
| 改 `RATE_B` → `RATE_A = 100 - RATE_B` | 事件連動 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:385-389` |
| 改 `RATE_A` | **沒有反向連動** | 檔內無 `umskRATE_A_ValueChanged` |
| 存檔時 `RATE_A + RATE_B = 100` | **沒有這條檢核**,`DoValidate` 只檢查兩欄非空 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:120-124` |

也就是說**只要使用者最後動的是 `RATE_A`,就可以存出總和不是 100 的拆帳設定**。對照 `DSMM005` 有明確的「加總必須 = 100」檢核(§4.4),這裡是漏的。

#### 期間怎麼自動銜接

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61-79`:存檔前把明細依 `SDATE` **由新到舊**排一次,然後:

- 最新的那一列(`iCnt == 1`)的 `EDATE` 不動(來自 grid 預設值 `29991231`,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355`);

- 其餘每一列的 `EDATE` 被改成「下一段(較新)那列的 `SDATE` 減一天」。

所以**使用者在 grid 裡打的 `EDATE`,除了最新那一列之外全部會被覆蓋**。這不是卡控,是自動改值,而且畫面上 `EDATE` 是可以編輯的、還被設成必填(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:353`),使用者不會知道自己打的值沒有用。

局部變數 `myEDATE` 初值 `"29991231"` 從頭到尾沒被讀過(第一圈就走 `iCnt == 1` 分支),是死碼。

#### 明細挑人的條件〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:252-257`:

```
IS_SALE  = 'Y'
SAL_CD   = 'C'
LEAVE_DATE >= '29991231'
```

最後一條字面意思是「離職日大於等於 29991231」,正常人都沒有離職日。**假設**共用控件 `EmployeeDataSrc` 把 `LEAVE_DATE` 為 NULL 的人視為 `29991231` 來比對(否則這條會把所有人濾光),依據是同 repo 其他畫面用「`LEAVE_DATE >= '今年/01/01' OR LEAVE_DATE IS NULL`」這種明確寫法,而這裡只有一個 `>=` 卻仍然能用。**這條要現場驗證。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 開畫面 | 撈在職的直銷部門主管 | 一個都沒有 | **例外(畫面開不起來)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:217` |
| 按新增 / 修改前 | `RATE_A + RATE_B = 100` | — | **完全沒有檢核** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:120-124` |
| 存檔前 | 除最新一列外,`EDATE` 一律被覆寫成下一段起日減一天 | 永遠 | 記錄不擋(自動改值) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61-79` |
| 存檔前 | `AGENT_ID` / `AGENT_CODE_LIKE` / `AGENT_ID_A` / `AGENT_ID_B` 一律覆寫成常數 | 永遠 | 記錄不擋〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:51-53` |
| 查詢時 | 戶號不在 `BMS001A`、公單業務員不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:133-137` |
| 查詢時 | 機構名稱靠 `OFD068A_V02` 且限 `AGENT_VALID_CODE = 'Y'` | 永遠 | 記錄不擋(`LEFT JOIN`,查不到只是空白) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.10 `DSMM906` — 每月對帳單郵寄名單〔共用表·無四眼〕

#### 用途(推測)

業務員自己維護「我的哪些客戶要寄月對帳單」:一個戶號一列,存是否郵寄與備註。畫面上還會顯示從 `BMS001A` 帶出來的一整組客戶聯絡資料(地址、電話、e-mail、法定代理人)供核對,但那些欄位不寫回去。

#### 這支畫面跟其他九支的根本差別

`DSMM906_PO` 把 `Add` / `Update` / `Delete` 三個方法整個 override,自己寫 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-278`),**不呼叫 `base`**:

| 方法 | SQL | 影響 |
|---|---|---|
| `Add` | `INSERT INTO BMS906 (BF_NO, EMP_NO, MAIL_YN, REMARK, UPD_USER, UPD_DATE, UPD_TIME)` | 只寫 7 欄,**沒有 `DATAID` / `STATUS` / 四眼 13 欄** |
| `Update` | `UPDATE BMS906 SET … WHERE BF_NO = :BF_NO` | 同上;而且**用 `foreach` 跑所有列** |
| `Delete` | `DELETE FROM BMS906 WHERE BF_NO = :BF_NO AND EMP_NO = :EMP_NO AND UPD_USER = :UPD_USER` | **必須三個條件全中才刪得掉** |

`Delete` 那個 `UPD_USER` 條件是隱性的權限控制:**只有「最後一次更新者是你」的那一筆才刪得掉**,不符就影響 0 筆,然後丟「刪除時影響筆數等於 0 筆,刪除失敗,請檢查」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255`)。使用者看到的訊息不會告訴他真正的原因。

#### `Delete` 的守衛式寫反了

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241`:

```
if (Rows.Count < 0 && Rows[0].RowState != DataRowState.Deleted)
    throw new ApplicationException("傳入主檔表格至少一個，請檢查");
```

`Rows.Count < 0` **永遠是 false**(筆數不可能是負的),所以這個守衛從來不會成立;而且 `&&` 的右半在筆數為 0 時會先去讀 `Rows[0]`。實際效果:**空集合時不會得到那句友善訊息,而是在 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:247` 的 `Rows[0]` 丟 `IndexOutOfRangeException`**。應該是 `Count < 1` 配 `||`。附錄 E1。

#### `MAIL_YN` 讀進畫面時被改掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91`:

```
custMAIL_YN.Value = master.IsMAIL_YNNull() ? "N" : (IsNullOrWhiteSpace(master.MAIL_YN) ? "N" : "Y");
```

判斷式只分「空白 → N」與「非空白 → Y」。**資料庫存 `N` 的那一筆,載入修改畫面會顯示成「Y」**,使用者不改任何東西按存檔,`SetData` 就把畫面上的 `Y` 寫回去(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:200`)。

**這是本模組後果最直接的缺陷:一個「不要寄」的設定,只要有人打開來看一下再存檔,就變成「要寄」。**附錄 E1。

#### 登入者的員工代碼

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:50-55`:

```
if (string.IsNullOrWhiteSpace(emp_Info) == false) m_EMP_NO = emp_Info.Split(',')[1];
```

`GetEMP_INFO` 無原始碼(`ClientBizUtility`,從呼叫端反推是「逗號分隔的員工資訊字串」)。這裡**位置取第 2 段**,沒有檢查段數——回傳值只有一段時會 `IndexOutOfRangeException`。對照 `DSMI001` 同一個呼叫有 `words.Length > 1` 的保護(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:106-111`),**同一件事三支畫面三種寫法**(第三種見 §7.3 的 `DSMR008`)。

`m_EMP_NO` 之後被無條件放進查詢條件(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125`),所以**取不到員工代碼時會變成查 `EMP_NO = ''`,永遠查無資料**,而且沒有任何提示。

#### 查詢條件的三選一

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:126-134`:戶號有填就只用戶號;否則身分證有填就用身分證;否則才用姓名。**三個條件永遠只會送出一個**,使用者同時填三個時另外兩個被靜默忽略。

PO 那邊四個條件全部用 `string.Format` 直接串進 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:312-350`),連運算子都是從 `Row.Opeartor` 串進去的。姓名那條還加了 `N` 前綴(`N'值'`)——Oracle 的 `N''` 字面量語法,同檔其他三條沒有。

#### 重建名單鈕(`DoExp1`)

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:299-307` → `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:417-443` → SP `S_TA_DSMM906_IMP`(IN:員工代碼、模式固定 `"1"`),`CommandTimeout = 0`(註解寫「此程式讓它永久跑」)。

回傳判斷是 `if (pxy.RebuildBF_List(...) < 0)` 顯示失敗、否則顯示「執行完成」。而 `RebuildBF_List` 回傳的是 `ExecuteNonQuery` 的影響筆數;Oracle 對 SP 呼叫通常回 -1。**假設**:這支按下去很可能永遠顯示「執行失敗」,依據是 `nResult = i` 直接把 `ExecuteNonQuery` 的結果當成功指標(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:431-435`),而同模組 `DSMB001` 的作者遇到同樣情況是硬寫 `i = 1`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:75`)。**要實跑確認。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | 戶號歸屬檢查 | 屬於別人 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:151-159` |
| 刪除(PO) | 只刪得掉「最後更新者是自己」的那一筆 | 不是 | 阻擋(訊息不說原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:232-233`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255` |
| 刪除(PO) | 空集合守衛 | — | **判斷式寫反,永遠不成立** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241` |
| 載入修改畫面 | `MAIL_YN` 非空白一律顯示成 `Y` | 永遠 | **記錄不擋(靜默改值)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` |
| 查詢時 | 一律只看自己的客戶 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125` |
| 查詢時 | 戶號 / 身分證 / 姓名三選一 | 填多個 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:126-134` |
| 查詢時 | 戶號不在 `BMS001A` | 永遠 | 過濾(無提示,INNER JOIN) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| 按重建鈕 | 無任何確認 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:299-307` |

## 5. 查詢畫面(I)

本模組只有一支:`DSMI001`(業務員每日收入查詢,推測)。單頁(`TabPages = 1`)、唯讀、不走四眼,`architecture.md §6.3` 說的「PO 退化成裸 DAO」在這裡完全成立——`DSMI001_PO` 不繼承任何基底、自己 new 兩個 `Database`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:34-37`)。

### 5.1 結構

| 層 | 特徵 | 錨點 |
|---|---|---|
| UI | `xOneStepProcessForm`,兩個 grid:上面挑基金、下面顯示結果 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:24-32` |
| PO | 唯一的方法是 `Select<T>`,回傳一個**新建的** VDB 而不是改傳入的 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:57-63` |
| 資料 | `DSM006A`(`DSMB001` 產出的)join `CRM002A` / `OFD081A` / `COD009` / `OFD002` / `FSK003` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:71-98` |

`dbPTPF` 這個欄位 new 出來之後**全檔沒有用到**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:37`)。

### 5.2 查詢條件

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:64-145`:

| 條件 | 必填 | 送出的參數 | SQL 長相 |
|---|---|---|---|
| 結存日期(起 / 迄) | **是** | `BAL_DATE_BGN` / `BAL_DATE_END` | `to_date(DSM006A.BAL_DATE,'YYYYMMDD') >= to_date(' 值 ','yyyy-MM-dd')` |
| 基金(勾選) | **至少一檔** | `FUND_ID` | `OFD081A.FUND_ID IN (值清單)` |
| 部門代碼 | 否 | `SAL_DEPT_NO` | `DSM006A.AGENT_CODE LIKE '值%'` |
| 員工代號 | 否 | `EMP_NO` | `DSM006A.EMP_NO = '值'` |
| 是否離職 | 否 | `LEAVE_YN` | `COD009.LEAVE_DATE IS (NOT) NULL` |
| 登入者員工代號 | 自動 | `QUERY_EMP_NO` | 進 `CRM002A` 子查詢當權限條件 |

三條前置檢核(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:74-92`):起迄都必填、起 ≤ 迄、**區間不可超過一個月**、基金至少選一項。

### 5.3 哪些條件會靜默濾掉資料

#### (1) `CRM002A` 的權限 INNER JOIN

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89`:

```
JOIN ( 取 CRM002A 裡 EMP_NO = :iQUERY_EMP_NO 且 INQ_EMP_NO <> 'ALL' 的授權列
       UNION ALL
       取同一人 INQ_EMP_NO = 'ALL' 的列,並把 INQ_EMP_NO 換成 '%' ) CRM002A
  ON DSM006A.AGENT_ID = CRM002A.AGENT_ID AND DSM006A.AGENT_CODE = CRM002A.AGENT_CODE
 AND DSM006A.EMP_NO LIKE CRM002A.INQ_EMP_NO
```

這是本模組唯一一段真正的資料列權限:**登入者在 `CRM002A` 裡有幾筆授權,就看得到幾個機構 / 業務員的資料**。設了 `INQ_EMP_NO = 'ALL'` 就用 `'%'` 放行整個機構。

**`CRM002A` 沒有他的資料 → 一筆都查不到,而且畫面只會說「查無資料」**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:227-230`)。權限與沒資料在這支畫面看起來完全一樣。

#### (2) 三條寫死的硬條件〔客戶特定〕

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:95-97`:

```
WHERE DSM006A.AGENT_ID = '0'
  AND ((NVL(A.DEPT_NO,' ')='G' AND (DSM006A.AGENT_CODE LIKE 'S%' OR DSM006A.AGENT_CODE IN ('08001','08101','08201')))
   OR  (NVL(A.DEPT_NO,' ')<>'G'))
```

| 條件 | 效果 |
|---|---|
| `AGENT_ID = '0'` | **只看直銷**,代銷 / 銀行 / 券商的收入永遠查不到 |
| 登入者部門是 `G` 時 | 只看得到 `S` 開頭的機構,外加三個寫死的代碼 `08001` / `08101` / `08201` |
| 登入者部門不是 `G` 時 | 不受上一條限制 |

三個機構代碼與 `G` 這個部門代碼都是寫死的字面量,換站台必須重問。

#### (3) 基金代碼直接串進 `IN (…)`

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:85-90` 先把勾選的基金組成 `'A','B','C'` 這種字串,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:159` 再原樣接進 `IN (…)`。**沒有綁參數、沒有跳脫**。值來自資料庫撈出來的基金清單,實務上不會被注入,但這是全模組最典型的字串串接寫法(附錄 E7)。

那段組字串還有一個括號放錯位置:`funds.Add("'" + Convert.ToString(row.Cells["FUND_ID"].Value + "'"))`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:89`)——結尾的單引號被接在 `object` 上再轉字串。結果碰巧一樣,但下一個人改這行會踩到。

#### (4) 日期字串與位置取值

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`:

```
" AND to_date (DSM006A.BAL_DATE , 'YYYYMMDD'  ) >= to_date(' " + beg_date.Substring(0,10) + " ','yyyy-MM-dd')"
```

兩個問題:**日期字面量前後各多一個空白**(Oracle 的 `TO_DATE` 對前導空白通常寬容,**假設**目前能跑就是靠這個;依據是這段程式運行多年),以及 `beg_date.Substring(0, 10)` 是位置取值(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:184`),而畫面傳的是 `Convert.ToString(DateTime)`,長度取決於執行緒的地區設定。

#### (5) 部門條件補了 `%`,這支是對的

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:134` 明確寫 `LIKE '值%'`,而且值有做單引號跳脫。對照 `DSMM001` / `DSMM002` 的 `LIKE` 沒補 `%`(§4.1),**同一個概念三支畫面兩種結果**。

### 5.4 取數之後做的事

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206-218` 在載入資料之前,對結果集的 13 個四眼欄位設 `DefaultValue`:`STATUS = "301"`、`CREATEID` / `ENTRYID` / `VERIFYID` / `APPROVEID` 全填登入者、`REJECTDATE` 填 `1900/01/01`。

**這是一支唯讀查詢畫面,設這些值沒有任何用途**(不會寫回 DB),grid 也把它們全部隱藏(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:168-169`)。看起來是從某支 M 畫面複製過來的殘骸。它唯一的副作用是:`STATUS` 的字面值 `301` 被固定在程式裡,成了 §2.5 反推狀態碼的證據之一。

### 5.5 三支死碼方法

`GetEmpNo`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:258-282`)與 `GetUidCode`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:289-315`)是 `public` 但介面宣告被註解掉(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:26-27`),Control 拿不到;兩支都把參數直接串進 SQL,而且對 `Rows[0]` 的存在性檢查不完整。第三支 `GetEmail` 連方法本體都被註解(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:318-349`),查的是 `AA_USER` 這張平台表。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢時 | 登入者不在 `CRM002A` | 永遠 | **過濾(訊息只說「查無資料」)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |
| 查詢時 | 只看 `AGENT_ID = '0'` 的直銷 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:95` |
| 查詢時 | 部門 `G` 的人只看 `S%` 與三個寫死代碼 | 是 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:96-97` |
| 查詢時 | 基金下拉只列正常狀態的基金 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:41` |
| 取數失敗 | 例外一律回「執行失敗，請檢查」 | 是 | 記錄不擋(訊息不含原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:236-241` |

## 6. 批次(B)與 WindowsService

本模組只有一支 B 畫面 `DSMB001`,**沒有** WindowsService(母體第 5 節空白,`Dev/ATLAS.DSM/` 底下也沒有任何 service 專案)。

### 6.1 觸發

人工。`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:45-50` 在 `RefreshPage` 直接把查詢鈕關掉、只留執行鈕(註解寫「只供執行」)。畫面上只有兩個欄位:計算日期(起)與(迄)。

### 6.2 輸入

| 欄位 | 檢核 | 錨點 |
|---|---|---|
| 計算日期(起) | **不可大於今日**(離開欄位時驗) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:178-187` |
| 計算日期(迄) | **沒有「不可大於今日」的檢核** | 檔內無對應的 `Validating` |
| 起 vs 迄 | 起 ≤ 迄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:79-83` |
| 起迄同步 | 填了起、迄還空著,而且起 ≤ 今天 → 自動補成一樣 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:159-166` |

**迄日可以填未來日期**,這是不對稱的地方。

### 6.3 執行前的兩道檢核(`DoCheck`)

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:110-194`,一次跑兩段,結果分別走「阻擋」與「詢問」兩條路:

#### 第一段:有基金未結帳就不給跑(阻擋)

```
SELECT DISTINCT FUND_ID FROM OFD303A
 WHERE CTL_DATE BETWEEN :CAL_DATE_ST AND :CAL_DATE_END AND POST_CTL_CODE <> 'Y'
```

有結果就把基金代碼串成一句「○○,○○基金於計算日期迄日有尚未結帳情形，不可執行批次計算」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:146-152`)。

**`POST_CTL_CODE <> 'Y'` 是 Oracle 三值邏輯的典型陷阱**:該欄為 NULL 時,`NULL <> 'Y'` 的結果是 UNKNOWN,不是 TRUE,那一列**不會**被選出來。也就是說**一檔「結帳旗標還沒寫入」的基金,這道檢核不會抓到它**,批次照跑。與 CAS 的 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` 是同一種缺陷(附錄 E2)。

#### 第二段:已經算過就問一次(詢問)

```
SELECT DISTINCT COUNT(*) FROM DSM006A WHERE BAL_DATE BETWEEN :CAL_DATE_ST AND :CAL_DATE_END
```

有資料就把一句警告字串塞進 `Util.Parameters` 的 `WARNING` 鍵(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:174-178`),UI 收到後跳 Yes/No 對話框,按「否」就取消(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:118-126`)。**這是全模組唯一一處標準的「詢問」型卡控。**

`SELECT DISTINCT COUNT(*)` 的 `DISTINCT` 對聚合結果沒有作用,是多餘的。

### 6.4 寫哪些表

`DSMB001` 自己**一張表都不寫**。它呼叫 `S_TA_DSMB001_EXCUTE_P01`(IN:計算日期起、迄、更新者),`CommandTimeout = 0`,註解寫「此程式讓它永久跑」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:66-76`)。

從 `DoCheck` 第二段查 `DSM006A` 可以反推:**這支 SP 的產出就是 `DSM006A`**。至於它怎麼算管理費 / 手續費、有沒有套 `DSM905` 的拆帳比例與 `DSM005A` 的離職分攤,**在 repo 內查不到**(§0.3)。

### 6.5 失敗處理:永遠回成功

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:74-87`:

```
m_db.ExecuteNonQuery(cmd);
i = 1;
...
if (i > 0) { AddResultRow(true, 0, ""); } else { AddResultRow(false, 0, ""); }
```

`i` 在呼叫之後被**硬寫成 1**,所以那個 `if/else` 的 `else` 分支永遠到不了。只要 SP 沒有丟例外,畫面就顯示成功——**SP 內部自行吞掉的錯誤、或處理 0 筆,使用者完全看不出來**。這與 `DSMM901` 的執行(§4.7)是同一種問題,只是這裡更明顯:作者顯然知道 `ExecuteNonQuery` 的回傳值不能用,於是寫死 1。

例外時一律回「執行失敗，請檢查」,**不帶任何原因**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:89-94`)。

### 6.6 與 M 畫面的關係

沒有直接關係。`DSMB001` 不讀也不寫任何 DSM 的維護表,唯一的交集是**它產出的 `DSM006A` 被 `DSMI001` 與 `DSMR003` / `DSMR004` 消費**。要確認「某位業務員的目標與實績」是不是對得上,得自己比對 `DSM001A`(目標)與 `DSM006A`(實績),程式沒有做這件事。

### 6.7 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 離開計算日期(迄) | 不可大於今日 | — | **完全沒有檢核** | 檔內無對應事件 |
| 按執行前 | 區間內有基金未結帳 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:132-152` |
| 按執行前 | 未結帳判斷用 `<> 'Y'`,NULL 抓不到 | 永遠 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:136` |
| 按執行前 | 該區間已產生過資料 | 是 | **詢問**(按否就取消) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:174-178` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:118-126` |
| 執行結果 | SP 的成敗 | 永遠 | **記錄不擋(一律回成功)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:75` |
| 執行例外 | 訊息固定「執行失敗，請檢查」 | 是 | 記錄不擋(不含原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:89-94` |

## 7. 報表(R)

```text
[圖] DSM 十七支報表的共同骨架、報表檔選擇方式、後綴變體與權限做法
圖中文字:共同骨架:17 支長得幾乎一樣 / DoValidate() / 日期/基金/路徑 / GetReportFileTitle / 決定 rpt 與中文標題 / PO GetData / SP + RefCursor / ReportLoad / SetParameterValue / 決定要印哪一支 rpt 的三種寫法 / switch 階梯 / DSMR001 等 13 支 / 算術 / DSMR011 九選一 / 固定一支 / DSMR010b 分支被註解 / 40 個 rpt 在 repo / 13 個引用的不在 / 四支後綴變體與本體的關係 / DSMR008 / DSMR008_1 / 同權限邏輯 換兩支 SP / DSMR009 / DSMR009_1 / 同上 / DSMR010 / DSMR010a / 只留第三支 SP / DSMR010b / 借殼改成另一張 / 自己做權限的三種做法〔客戶特定〕 / 丟給 SP 判 / QUERY_EMP_NO 參數 / 畫面直接鎖欄位 / DSMR008 白名單 101722 / 取了卻註解掉 / DSMR009 等於沒權限 / 資料全在版控外 / SP 內容看不到
```

*圖:圖 4 報表群。橘框=值得特別看的做法;灰虛框=平行實作,改一邊要改兩邊;橘虛框=客戶特定或已偏離原設計;黑框=版控外。所有數字都來自版控外的 SP,repo 內看不到算法。*

17 支 R 畫面、40 個 `.rpt`。**全部的資料都來自版控外的 SP**(`DB/` 底下一支 DSM 的報表 SP 都沒有),所以本節只能寫「畫面怎麼決定要跑哪支 SP、要印哪個 `.rpt`、以及有哪些檢核」,**SP 內部的算法查不到**。

### 7.1 共同骨架

17 支長得幾乎一樣,差別只在條件欄位與分支:

| 步驟 | 做什麼 | 代表錨點 |
|---|---|---|
| `FormInitial` | new `ResultVDB` + `FormProxy`;多數會呼叫 `ClientBizUtility.GetEMP_INFO(UserID)` 取登入者員工代碼 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:49-69` |
| `BeforePrintOrPreviewButtonClicked` | `DoValidate()` → `GetReportFileTitle()` 取 (rpt 檔名, 中文標題) → `SetQueryParameters(...)` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:115-128` |
| PO `GetData` | `BeginTransaction` → `GetStoredProcCommand` → `AddOutParameter(RefCursor)` → `LoadDataSet` → `Commit` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:48-105` |
| `ReportLoad` | `SetRptSchemaOnDoc()` 之後一連串 `SetParameterValue`,把查詢條件以文字印在報表抬頭 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:134-176` |

幾個全模組一致的慣例:

- **每支 SP 都設 `cmd.CommandTimeout = 0`**,註解一律是「此程式讓它永久跑」。

- **結果集用 `OutTB` / `OutTB2` / `OutTB3` 這種位置命名的 RefCursor**,`LoadDataSet` 靠參數順序對應 DataTable 順序(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:71-78`)。**加一個游標就要同時改兩處而且順序不能錯**,`change-sp-fn-trigger.md §8.3` 講的就是這件事。

- **條件「全部」的表示法是空字串**,報表抬頭則印中文「全部」(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:152`)。

- **有 Excel 匯出的畫面都要填「轉出路徑」**,檢核兩條:非空、`Directory.Exists`(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:294-305`)。

### 7.2 40 個 `.rpt` 與程式引用的對不上

`Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/` 有 40 個 `.rpt` + 40 個對應的 `ReportClass`,涵蓋 `DSMR001`–`DSMR011`。但程式裡叫得出名字的報表檔還包括:

| 程式引用但 repo 內沒有的 rpt(共 13 個) | 錨點 |
|---|---|
| `DSMR008RPS3` / `DSMR008RPS4` · `DSMR008_1RPS1` / `DSMR008_1RPS2` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:388-391`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:347-351` |
| `DSMR009_1RPS1` / `DSMR009_1RPS2` · `DSMR010aRPS1` / `DSMR010aRPS2` · `DSMR010bRPS` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009_1.cs:259-263`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010a.cs:264-267`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:263` |
| `DSMR012RPS1` / `DSMR012RPS2` · `DSMR013RPS1` / `DSMR013RPS2` / `DSMR013RPS3` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR012.cs:286-290`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR013.cs:259-265` |

為什麼還印得出來:**報表檔是在執行期跟伺服器要的**。`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p1.cs:109-131` 示範了完整流程——`FormProxy.GetReportObject(QueryVDB)` 回傳 `byte[]`,寫成使用者「我的文件」底下一個 GUID 檔名的 `.rpt`,`ReportDocument.Load()` 之後立刻 `File.Delete()`。R 畫面走的是框架包好的同一條路(`SetQueryParameters` 把報表名傳下去)。

**所以 `Report.DSM` 專案裡的 40 個檔只是「有被編進 DLL 的那一批」,不是全部。**要找 `DSMR013RPS1` 的長相,得去部署目錄或報表伺服器,repo 內沒有。

另外 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS31.cs:19` 宣告了一個與 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS3.cs:19` **同名**的 `DSMR001RPS3` 類別。兩個檔同時編譯會衝突——查 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/Report.DSM.csproj:132-133` 只把 `DSMR001RPS3.cs` 收進去,`…RPS31.cs` 不在 csproj 裡,是**沒被刪乾淨的孤兒檔**。

### 7.3 權限:三支報表自己做,而且做法不同〔客戶特定〕

| 畫面 | 怎麼取登入者 | 之後做什麼 | 錨點 |
|---|---|---|---|
| `DSMR001` `DSMR002` `DSMR007` | `GetEMP_INFO(UserID).Split(',')[1]`,取不到就空字串 | 當 `QUERY_EMP_NO` 參數丟給 SP,**由 SP 決定看得到什麼** | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:56-68`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:330` |
| `DSMR008` `DSMR008_1` | 同上,**再多取第 3、4 段**當部門與業務屬性 | 在畫面上直接鎖死部門 / 員工欄位 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:69-88` |
| `DSMR009` `DSMR009_1` | 取了之後**把送參數那行註解掉** | 等於沒有權限控制 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009.cs:272-287` |

`DSMR008` 那套值得展開(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:106-144`):

| 登入者 | 可查範圍 |
|---|---|
| 業務屬性為 `C` | 部門鎖成自己的部門、員工鎖成自己,兩個欄位都停用 |
| 其他有業務屬性的人 | 部門鎖成自己部門的前 3 碼 |
| 部門前 3 碼是 `S01` 或 `S05` 且業務屬性 `D` | **解除鎖定,可查全部** |
| **員編 `101722`** | **解除鎖定,可查全部**(兩個分支各寫一次) |
| 帳號 `ntaprt` + 數字 5–11 | **解除鎖定,可查全部** |

三個要記住的:

1. **`if (emp_Info.Count() > 1)` 這個守衛是錯的**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74`)。`Count()` 數的是**字串的字元數**,不是逗號分段數;作者要的是 `Split(',').Count() > 1`。所以只要 `GetEMP_INFO` 回傳超過 1 個字元,就會直接去取 `Split(',')[2]` 與 `[3]`——**回傳格式少於 4 段時丟 `IndexOutOfRangeException`,畫面開不起來**。附錄 E1。

2. **員編 `101722` 寫死兩次**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:118`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:126`),`DSMR008_1` 再各寫一次(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:120`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:128`)。這個人離職就沒有人有全域權限。

3. **`Convert.ToInt32(this.UserID.Substring(6).Trim())`**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:136`)對任何 `ntaprt` 開頭且長度 > 6 的帳號都會執行,後綴不是純數字就丟 `FormatException`。

### 7.4 四支後綴變體與本體的關係

| 變體 | 本體 | 關係 | 依據 |
|---|---|---|---|
| `DSMR008_1` | `DSMR008` | **幾乎整支複製**:同樣的權限邏輯(連 `101722` 與 `Count()` 的 bug 都一樣)、同樣的檢核訊息;差別只在 SP 換成 `S_TA_DSMR008_1_Query` / `S_TA_DSMR008_1_QryDetail` 兩支,報表種類從 4 種縮成 2 種 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:69-128` 對 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:69-126`;`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR008_1_PO.cs:63` |
| `DSMR009_1` | `DSMR009` | 同上的關係,SP 換成 `S_TA_DSMR009_1_Query` / `S_TA_DSMR009_1_QryDetail`,報表從 3 種縮成 2 種 | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR009_1_PO.cs:62`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009_1.cs:259-263` |
| `DSMR010a` | `DSMR010` | 複製後**只留第三支 SP**:`S_TA_DSMR010a_GET_1` 與 `_GET_2` 的呼叫段整段被註解,實際只跑 `S_TA_DSMR010a_GET_3` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:62`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:83`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:99` |
| `DSMR010b` | `DSMR010` | **已經不是同一張報表了**:標題改成「境外基金每日原幣存量」,原本的兩選一分支整段被註解、固定回 `DSMR010bRPS`;PO 讀了 `rpt_type` 卻沒用;結果集的 DataTable 名還沿用 `DSMR010_1`;基金群組那三條檢核也被註解掉 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:263-271`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010b_PO.cs:58-71`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:333-345` |

**結論:`_1` / `a` 是「同一張報表換一組 SP」的平行實作,`b` 是「借殼改成另一張報表」。**改 `DSMR008` 的邏輯時,`DSMR008_1` 要一起改;改 `DSMR010` 時,`DSMR010a` 要一起看,但 `DSMR010b` 不用。

### 7.5 三支值得展開的

#### `DSMR001` — 五支 SP、逐月迴圈、外加一次 DISTINCT

`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:48-224`。分支條件是「報表類型」與「列印類型」兩個參數的組合:

| 條件 | 走哪支 SP |
|---|---|
| 列印類型 ∈ {2,3,4} 且 報表類型 = 1 | `S_TA_DSMR001_GET_3` |
| 列印類型 ∈ {2,3,4} 且 報表類型 ≠ 1(且 ≠ 2 的分支) | `S_TA_DSMR001_GET_4` / `S_TA_DSMR001_GET_5` |
| 其他 且 報表類型 = 1 | **`S_TA_DSMR001_GET_1`,一個月跑一次** |
| 其他 且 報表類型 = 2 | `S_TA_DSMR001_GET_2` |

第三列是重點(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:138-178`):把使用者給的日期區間切成一個月一段,**每個月開一次交易、跑一次 SP、`Merge` 進同一張 `DataTable`**,跑完再用

```
DT.DefaultView.ToTable(true, new string[]{ "AGENT_CODE","AGENT_NAME","EMP_NO","EMP_NAME",
  "BF_NO","BF_NAME","FUND_ID","FUND_SH_NM","ALLOT_DATE","ALLOT_AMT","ALLOT_DATE_B","REDEM_DATE" })
```

做一次 DISTINCT(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:176-177`)。兩個後果:**同一個客戶在兩個月都符合條件時會被折成一列**(這正是「新開百萬客戶清冊」要的),但**這 12 個欄位以外的欄位全部被丟掉**——SP 回的游標若多回欄位,在這裡就消失了;以及 `tran` 在迴圈裡被重新指派(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:152`),**前一個月的交易物件沒有被 `Dispose`**。

另外 `catch` 區塊第一行就是 `tran.Rollback()`(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:213`),而 `tran` 在 `try` 內才賦值——日期轉換那幾行(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:142-143`)丟例外時 `tran` 還是 null,**真正的錯誤會被 `NullReferenceException` 蓋掉**。這個寫法 17 支報表 PO 全都一樣(附錄 E1)。

#### `DSMR011` — 報表檔名用算的

`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR011.cs:249-257`:

```
key = "DSMR011RPS" + ((報表類型 - 1) * 3 + 排序類型)
```

報表類型 1–3、排序類型 1–3,乘出來剛好 1–9,對上 `DSMR011RPS1`–`DSMR011RPS9` 九個檔。程式碼裡還附了算式說明的註解。

**這是全模組唯一一支用算的而不是 `switch` 的**,好處是加組合不用改 code,壞處是任一個選項的值域擴大(例如報表類型多一個 4)就會算出不存在的檔名,而且不會有編譯期或執行期的提示。PO 那側則是**一次抓三個游標,靠「1~3 僅會有一個有資料」的約定**(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:80`)——這個約定只寫在註解裡,SP 那邊沒有任何保證。

#### `DSMR005` — 一個畫面七種報表 + 四種 Excel

`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR005.cs:314-365` 用巢狀 `switch` 決定七種組合(定額 / 不定額 / 168 循環 / 退休財富管理 × 達成表 / 客戶明細,外加一個「By 戶數(含168)」),Excel 匯出再用**另一套幾乎平行的判斷**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR005.cs:878-907`)決定要跑四個產生函式中的哪一個。兩套的條件不完全相同:列印時「退休財富管理」對到 `DSMR005RPS1` / `DSMR005RPS2`,Excel 那側沒有對應分支。**假設**這個選項不支援 Excel 匯出,依據是 Excel 的 `switch` 只列了 168 與非 168 兩支,要現場確認。PO 側三支 SP 的參數與游標數也都不同(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR005_PO.cs:66-134`)。

### 7.6 畫面端的檢核總表

| 檢核 | 出現在幾支 | 代表錨點 |
|---|---|---|
| 日期(起) 不可大於 日期(迄) | 12 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:202-206` |
| 轉 Excel 必須填轉出路徑 + 路徑必須存在 | 10 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:294-305` |
| 基金群組 / 管理費率 / 基金代碼 三選一必選 | 8 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:427-446` |
| 「挑選基金資料」至少勾一筆 | 6 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:355-359` |
| 報表種類 / 部門類別 必須選一個 | 3 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:418-425` |
| **統計日期區間資料仍未產生** | 2 支(`DSMR003` `DSMR004`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:282-290` |
| **統計方式為人數時,某些報表選項不存在** | 1 支(`DSMR006`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR006.cs:444-448` |
| 業務員有輸入時業務部門必須同時輸入 | 1 支(`DSMR007`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:519-522` |
| 生日 / 結餘 / 未交易日 / 報酬率 四組範圍各自「要嘛都填要嘛都空」且起 ≤ 迄 | 1 支(`DSMR007`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:526-598` |

兩個特別的:

- **`DSMR003` / `DSMR004` 的「資料仍未產生」是先打一次 DB 才知道的**:`Exists` 去數 `DSM006A` 在該區間的筆數(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR003_PO.cs:112-146`)。這是報表與 `DSMB001` 之間唯一一條程式層的關聯。那段 SQL 用 `string.Format` 把日期串進 `BETWEEN '{0}' AND '{1}'`(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR003_PO.cs:119-126`),沒有綁參數。

- **`DSMR006` 的「程式無製作此類報表」是最誠實的一條訊息**:統計方式選「人數」而報表選項選「BY促銷代碼」或「BY部門別各基金(EXCEL檔)」時,直接說「程式無製作此類報表，請重新選擇!」(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR006.cs:444-448`)。

### 7.7 對維護資料的關係

| 報表群 | 吃誰的資料 | 在 repo 內看得到嗎 |
|---|---|---|
| `DSMR003` `DSMR004` | `DSM006A`(`DSMB001` 產出)+ 推測來自 `DSM001A` / `DSM007A` 的目標值 | **只看得到前者** |
| 其餘 15 支 | 交易與結存(`OFD` 那批)、定期定額、客戶組成 + `CPM001A` | 看不到;例 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:900` 只看得到參數 |

**沒有任何一支報表讀 `DSM905` / `DSM005A` 的拆帳與分攤比率**——與 §0.3 的結論一致:那些比率只可能在 `S_TA_DSMB001_EXCUTE_P01` 內被套用。

## 8. 跨模組共用

```text
[圖] DSM 四組跨模組共用的表:DSM001A 給 CAS、OFD374A 給 BMS、BMS906 無人共用、SAL051 全庫共用
圖中文字:A：DSM 自己的表借給 CAS / DSMM001〔DSM〕 / 主明細 · SAL051 限制 / DSM001A DSM002A / 六個業績指標 / CASM006〔CAS〕 / 主明細 · 八部門白名單 / 兩個不同的員工集合 / 不是包含關係 / B：OFD 前綴的表,主檔在 DSM / DSMM060〔DSM〕 / 唯一正規維護入口 / OFD374A / 受益人歸屬業務員 / BMSM001 條件寫死 false / 實際永遠不掛明細 / RSPM004 直接 INSERT / OFDI011 檢查歸屬 / C：BMS 前綴,但 BMS 一行都沒碰 / DSMM906〔DSM〕 / 不走四眼 · 手寫 SQL / BMS906 / 實體只有 7 欄 / xsd 另 18 欄來自 BMS001A / DataTable ≠ 實體表 / BMS 側零引用 / 實測 7 個檔全在 DSM / D：沒有模組的表,影響面最大 / DSMM050〔DSM〕 / 唯一維護者 · 刪除無檢核 / SAL050 SAL051 / 業務部門與人員編制 / BasicCOD_PO / V_SAL051 / 共用員工下拉的來源 / 七個模組 十七個檔 / CLS CRM NFD CPM OFDI
```

*圖:圖 5 跨模組。橘框=主檔或維護入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼。四組的「借法」都不一樣,其中 D 的 SAL051 透過共用員工下拉影響全庫,是本模組風險最高的一張表。*

DSM 有四組跨界的表,每一組的「借法」都不一樣:

| 組 | 表 | 誰是主檔 | 誰是借用方 | 借法 |
|---|---|---|---|---|
| A | `DSM001A` `DSM002A` | DSM 自己 | **CAS**(`CASM006`) | 兩邊都是主明細維護,只是取數範圍不同 |
| B | `OFD374A` | **DSM**(`DSMM060`) | BMS / OFDI / RSP | DSM 是唯一的正規維護入口,別人有讀有寫 |
| C | `BMS906` | **DSM**(`DSMM906`) | 沒有人 | 名字是 BMS 的,但 BMS 一行都沒碰 |
| D | `SAL050` `SAL051` | **DSM**(`DSMM050`) | 全庫(透過共用控件) | DSM 是唯一維護者,影響面最大 |

### 8.1 `DSM001A` / `DSM002A`:同一張表,兩支維護畫面,兩種員工範圍

`CASM006` 與 `DSMM001` 都把這兩張當主明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36`),**六個業績指標欄位一模一樣**。`cas.md §8.4` 已經從 CAS 那側寫過一次;從 DSM 這側看,結論相同:

| 面向 | `CASM006` | `DSMM001` |
|---|---|---|
| 部門欄從哪來 | `COD009` 的部門欄 | **`SAL051` 的業務部門欄** |
| 額外 join | 只有 `COD009`(INNER) | `COD009` **加** `SAL051`,兩個都是 INNER |
| 部門限制 | 寫死八個部門的白名單 | 沒有白名單,但被 `SAL051` 的 INNER JOIN 限制成「有在業務部門編制內的人」 |
| 「營業收入 > 0」檢核 | **有**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78`) | **被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-79`) |
| 月分配補餘額 | **被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:259-274`) | **是活的**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:274-290`) |
| 錨點 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113-127`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:113-131`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:144-154` |

**兩支畫面看到的員工集合是兩個不同的集合,不是包含關係**——這一段與 `cas.md §8.4` 的四象限表一致,不重複列。

從 DSM 這側再補兩件 `cas.md` 沒講的:

1. **兩支的「必須大於 0」與「月分配補餘額」剛好互補地壞掉。**`CASM006` 擋得比較嚴(至少營業收入不能是 0)但月分配算錯;`DSMM001` 月分配算對但六個指標都可以是 0。**同一張表可以同時存在「被 CAS 擋下的資料」與「被 DSM 擋下的資料」。**

2. **`DSMM002` 不算在內。**它的主明細是 `DSM007A` / `DSM008A`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36`),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:149-189` 出現的 `SAL051` 與 `EMP_NO` 條件**全部在註解區塊**,是從 `DSMM001` 複製樣板留下的。搜尋字串時會誤判,別被騙——這一點 `cas.md §8.4` 也提過。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `DSM001A` `DSM002A` 欄位 | `CASM006Model.xsd` / `CASM006View.xsd` 與 `DSMM001Model.xsd` / `DSMM001View.xsd` 四份都要重生,兩支畫面都要回歸 |
| 改 `CASM006` 的部門白名單 | 只影響 `CASM006` |
| **改 `DSMM050` 的部門成員** | **只影響 `DSMM001`**(它是靠 `SAL051` INNER JOIN 的那一支) |
| 改 `COD009` | **兩支都影響**,而且都是 INNER JOIN,刪一個員工等於他的目標整筆消失 |

### 8.2 `OFD374A`:DSM 是主檔,BMS 是條件掛載的明細

`bms.md` 已經從 BMS 那側寫過(見該文的 `OFD374A` 段與 `AUTO_BELONG_EMP` 段),**兩邊結論一致**,這裡補 DSM 這側的細節:

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| **`DSMM060`(DSM)** | **主檔**,唯一的正規維護入口。四張表 INNER JOIN 取數;歸屬日期強制為今天 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:48-62` |
| `BMSM001`(BMS) | 條件掛載成明細,但條件寫死 `false`,**實際永遠不掛** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1915` |
| `BMSM006`(BMS) | 條件寫死 `true`,**永遠掛** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2203-2214` |
| `OFDI011`(OFDI) | 有一支 `CheckOFD374A` 專門檢查歸屬 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:5980-5994` |
| `RSPM004`(RSP) | **直接 `INSERT OFD374A`** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700` |

從 DSM 這側要補的三件事:

1. **`DSMM060` 的取數是三個 INNER JOIN**(`BMS001A` / `OFD002` / `COD009`,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:50-56`)。`RSPM004` 直接寫進來的資料,只要部門代碼不在 `OFD002` 或員工不在 `COD009`,**`DSMM060` 就查不到、也改不掉那筆**。BMS 那側是把它當唯讀明細,不受這個影響。

2. **欄位定義有兩份且不同構。**DSM 側 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM060Model.xsd` 宣告 22 欄(4 個業務欄 + 3 個 join 欄 + 15 個四眼相關);BMS 側自己有一份(`bms.md` 已指出)。**加欄位要兩邊一起改**,否則會出現 `architecture.md §5.4` 講的那種靜默失敗。

3. **`DSMM060` 完全沒有業務檢核**(§4.6):不檢查戶號是否已歸屬他人、不檢查員工是否真的在該部門。BMS 側的 `BMSM001` 有一段補業務部門的邏輯,但因為它永遠不掛明細,那段也不會跑(`bms.md` 附錄 E16 的潛伏 bug)。**兩邊都沒有把關的結果,`OFD374A` 的資料品質實際上只由 `DSMM060` 的下拉連動保證。**

### 8.3 `BMS906`:BMS 前綴,DSM 專屬

實測 `grep -rl "BMS906" Dev/` 只命中 7 個檔,**全部在 `Dev/ATLAS.DSM/` 底下**(PO / UI / 兩組 xsd + Designer / `App.config`)。**BMS 模組沒有任何程式碰它。**

為什麼會這樣,repo 內找不到答案。**假設**:這張表原本規劃在 BMS(對帳單是受益人資料的一部分),後來功能改由業務員自己維護,畫面就落在 DSM,表名沒有跟著改。依據有兩條:

- 它的 xsd 裡有 18 個欄位是從 `BMS001A` join 出來的受益人聯絡資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:292-306`),形狀比較像 BMS 的東西;

- `DSMM906` 是全模組唯一不走四眼的維護畫面(§4.10),看起來是後來補的、沒有照 DSM 的規格做。

**改這張表要注意兩件事:**

1. **xsd 裡的 `BMS906` DataTable ≠ 實體表 `BMS906`。**實體欄只有 7 個(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:158-159` 的 INSERT 欄位清單),其餘 18 欄是 join 進來的。要加實體欄位,`INSERT` / `UPDATE` 兩段手寫 SQL 也要一起改(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-226`)——**框架不會幫你組欄位清單,因為這支把寫入方法整個 override 了**。

2. **它沒有四眼欄位**,所以任何「幫 DSM 的表加四眼稽核」的一次性作業,都必須把 `BMS906` 排除,否則 `DSMM906` 的三段手寫 SQL 會因為 NOT NULL 欄位沒填而爆掉。

### 8.4 `SAL050` / `SAL051`:沒有模組的表,影響面卻最大

**`SAL` 這個前綴在全庫沒有對應的專案、沒有對應的畫面代號。**兩張表的唯一維護入口是 `DSMM050`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:39-40`)。

它們管的是**直銷的業務組織**:`SAL050` 一列一個業務部門(部門屬性 `DEPT_CD`、主管獎金計算類別 `MGR_BNS_KIND`),`SAL051` 一列一個「部門 × 員工」的編制(業務屬性 `SAL_CD`、獎金制度 `BONUS_TYPE`)。§2.5 有值域。

**影響面比表名看起來大得多。**實測 `SAL051` 在 DSM 之外還被 **17 個檔、7 個模組**引用:

| 模組 | 檔數 | 怎麼用(從檔名與位置推測) |
|---|---|---|
| `Common` | 4 | **共用員工挑選控件的資料來源**,見下 |
| CLS | 4 + 1(Report) | 拜訪紀錄的業務員範圍 |
| CRM | 2 + 2(Report) | 潛在客戶與業務員的對應 |
| NFD.Report · CPM · OFDI | 2 · 1 · 1 | 報表的業務員部門;其餘兩支從檔名看不出用途 |

**最關鍵的是 `Common` 那四個檔。**`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:284-324` 是共用員工資料來源(`EmployeeDataSrc`)的取數 SQL:

```
JOIN (SELECT …, ROW_NUMBER() OVER(PARTITION BY EMP_NO ORDER BY …) RNO FROM V_SAL051) SAL051
  ON COD009.EMP_NO = SAL051.EMP_NO AND SAL051.RNO = 1
… AND SAL051.SAL_DEPT_NO = '<SAL_DEPT_NO 屬性>'
… AND SAL051.SAL_CD <in/not in> ('<SAL_CD 屬性>')
```

也就是說:**任何畫面上的員工下拉,只要設了 `IS_SALE` / `SAL_DEPT_NO` / `SAL_CD` 這三個屬性,背後查的就是 `SAL051`**(2023-05-23 起改查 view `V_SAL051`,註解留在 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:277`)。共用控件 `ucAssignEmpNo` 的屬性說明也直接寫「屬於業務部門，將會串接SAL051為部門代碼的查詢條件」(`Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignEmpNo.cs:45`)。

**結論:在 `DSMM050` 刪掉一位業務員的編制,不只 DSM 的畫面查不到他,全庫所有「業務員」下拉都會少一個人。**這張表是全庫等級的主檔,但它的維護畫面(§4.5)的卡控是「逐列警示不擋 + 存檔時寬鬆檢核」,而且**刪除完全沒有檢核**。這是本模組風險最高的一件事。

`SAL050` 在 DSM 之外只被 `Common` 引用,影響面小得多。

另外注意 `SAL051` 有一欄 `TOT_ADD_AC`(整數,無 Caption),repo 內完全沒有程式讀寫它——但它可能被版控外的 SP 使用,**不要因為「沒人用」就刪**。

### 8.5 `SAL051` 在 DSM 內部的五種用法

同一張表,五支畫面五種條件,值得並排看:

| 畫面 | join 方式 | 額外條件 | 效果 | 錨點 |
|---|---|---|---|---|
| `DSMM001` | `JOIN`(INNER) | 無 | 不在編制內的人,他的年度目標整筆查不到 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:129-130` |
| `DSMM003` | `LEFT JOIN` | `SAL_CD = 'C'` | 平常查得到、部門欄空白;**一填部門條件就退化成 INNER** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:123-125`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` |
| `DSMM901` | 子查詢 + `ROW_NUMBER() … RNO = 1` | 原本要求「員工在移轉後部門且未離職」 | **這段 SQL 還在,但呼叫點被換掉了**(§4.7) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:346-354` |
| `DSMM902` | 同上 | 同上,**實際有在用** | 移轉後員工必須真的在移轉後部門 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:339-350` |
| `DSMM903` | `INNER JOIN COD009` | `SAL_CD = 'A'` + 未離職 | 撈直銷部門主管;**一個都沒有時畫面開不起來**(§4.9) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258` |
| `DSMM005` / `DSMM050` | 不直接 join,走共用控件 | `IS_SALE` / `SAL_DEPT_NO` / `SAL_CD` / `AO_CODE` | 只影響下拉候選,不影響已存的資料 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:496-501`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |

**`DSMM901` / `DSMM902` 那兩段 `ROW_NUMBER() … RNO = 1` 值得注意**:一個員工同時掛在兩個業務部門時,它靠 `ORDER BY UPDATEDATE DESC, SAL_DEPT_NO` 取「最後更新的那一筆」當唯一部門。也就是說**在 `DSMM050` 改一個人的部門編制,會改變他在移轉檢核裡被認定的部門**,而且沒有任何地方寫下來。

### 8.6 `OFD068A_V02`:一支 view,兩個已知缺陷,對 DSM 的實際影響

這支 view 的問題 `change-sp-fn-trigger.md §7.1` 到 `change-sp-fn-trigger.md §7.3` 已經查過,結論兩條:

1. **view 回 9 欄,共用 typed DataSet 只宣告 5 欄**(`Dev/Common/Source/DataSource/DataEntity.DataSource/OFD_AgentCodeOriginalListModel.xsd:15-22`,DataTable 名字就叫 `OFD068A_V02`)。多回的 `AGENT_CODE_M` / `BANK_KIND` / `AGENT_VALID_CODE` / 一個重複的 `AGENT_ID` 位置會被 `LoadDataSet` 靜默丟掉。

2. **券商那一段的子查詢裡硬寫了一筆常數資料列** `'551','永豐金證券'`(`DB/View/OFD068A_V02.SQL:76`),而該段外層還有 `ROW_NUMBER() … WHERE RNO = 1` 的去重。

DSM 這兩支畫面用它的方式**都不是走那組共用 typed DataSet**,而是 PO 手寫 SQL 直接 join、自己取別名:

| 畫面 | 怎麼用 | 錨點 |
|---|---|---|
| `DSMM901` | `SELECT BANK_BRH_SHNM FROM OFD068A_V02 WHERE AGENT_CODE = :AGENT_CODE`,**當作「這個銷售機構存不存在」的驗證** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:341-344` |
| `DSMM903` | `LEFT JOIN OFD068A_V02 D ON D.AGENT_ID = … AND D.AGENT_CODE = … AND D.AGENT_VALID_CODE = 'Y'`,只取 `BANK_HQ_SHNM AS AGENT_NAME` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:203-206` |

所以**「5 欄 vs 9 欄」那個缺陷不會直接打到這兩支畫面**——它們沒有把 view 載進那組 DataSet,`DSMM903` 甚至用到了 DataSet 沒宣告的 `AGENT_VALID_CODE`(只出現在 join 條件裡,不進結果集)。真正被那個缺陷影響的是任何用共用銷售機構下拉的地方。

**但第 2 條會直接打到 `DSMM901`。**那筆 `'551','永豐金證券'` 是 `UNION ALL` 進 `FSK005` 的,券商段的輸出 `AGENT_CODE` 是 `'K' || 補位後的 STK_BRK`,所以 view 裡會多出一個 `K5510`(或 `K551` 補位後的值)這種**在基礎表裡不存在的銷售機構**。而 `DSMM901.CheckExists` 就是拿 `AGENT_CODE` 去這支 view 查有沒有(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:389-396`):

- **匯入 CSV 時填這個代碼會通過驗證**,然後被送去給 `S_TA_DSMM901_EXE` 執行;

- 第二個效應在 `DSMM903`:券商段的 `ROW_NUMBER() … PARTITION BY 補位後的代碼 ORDER BY NVL(FSK005.STK_BRK, OFD068A.STK_BRK)` 去重時,**這筆常數列有可能贏過真實資料**,讓畫面上的機構簡稱顯示成「永豐金證券」。這一條是**假設**,成不成立要看 `FSK005` 裡 `551` 這個代碼實際存不存在、以及排序鍵是否相同;依據是那個 `PARTITION BY` 用的是補位後的代碼,而常數列與真實列補位後可能落在同一組。

〔客戶特定〕:`551` 與「永豐金證券」都是本站台的值。

**改這支 view 之前先讀 `change-sp-fn-trigger.md §7.2`**:六段 `UNION` 靠位置對齊,加一欄要六段都加,券商那段還要改兩層 SELECT。

### 8.7 共用的 UI 控件與資料來源

DSM 沒有用到 `Dev/Common/Source/DataSource/PO.DataSource` 底下的共用 **PO**(Control 全部只掛自己的 PO),但大量使用共用控件與 DataSource:

| 名稱 | 用在哪 | 為什麼要小心 |
|---|---|---|
| `EmployeeDataSrc` | `DSMM005` `DSMM050` `DSMM903` 的 grid 挑人 | 背後查 `V_SAL051`,見 §8.4 |
| `ucAssignEmpNo` / `ucAssignDeptNo`(從屬性名反推) | 幾乎每支畫面的員工 / 部門欄 | `IS_SALE` / `SAL_CD` / `SAL_DEPT_NO` / `LEAVE_DATE` / `Filter` **五種過濾入口混用**,同一支畫面可能同時設兩種(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:304-306`) |
| `custFundIDClassify` / `custFundIDChoiceType` | 報表與 `DSMI001` 的基金選取 | `FUND_STATUS = "0"` 只列正常狀態基金(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:41`) |
| `GetDropDownDataSrc` vs `GetDropDown9iDataSrc` | `DSMM050` **同時用兩套**取同樣的代碼分類 | 兩套實作可能不同步,見 §4.5 |
| `CodeDataSrc` | `DSMM901` 的 `EXETYPE`(`COD006A` 的 `D1` 分類)、`DSMM902` 的 `FUND_TYPE`(`D4`) | 無原始碼 |
| `ClientBizUtility.GetEMP_INFO` | `DSMM906` `DSMI001` `DSMR001` `DSMR002` `DSMR007` `DSMR008` `DSMR008_1` `DSMR009` `DSMR009_1` | **回傳逗號分隔字串,九支畫面用位置取值,三種不同的長度保護**(§4.10、§5.2、§7.3) |
| `MailUtility.SendMailTo` | `DSMM901` `DSMM902` | 無原始碼;寄件人取不到時用寫死的信箱 |

全部無原始碼,從呼叫端反推。

## 附錄 A. 資料表總表

### A.1 母體的 16 張表

| 表 | 欄位(xsd) | 四眼 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `DSM001A` | 26 | 有 | DSM | `DSMM001` `CASM006` | — | 主檔,新增 / 修改 / 刪除 |
| `DSM002A` | 24 | 有 | DSM | — | `DSMM001` `CASM006` | 明細,隨主檔 |
| `DSM003A` | 22 | 有 | DSM | `DSMM003` | — | 主檔 |
| `DSM004A` | 20 | 有 | DSM | — | `DSMM003` | 明細 |
| `DSM005A` | 21 | 有 | DSM | `DSMM005`(多筆型) | — | 主檔 + 拷貝(PL/SQL 直接 INSERT) |
| `DSM007A` | 25 | 有 | DSM | `DSMM002` | — | 主檔 |
| `DSM008A` | 24 | 有 | DSM | — | `DSMM002` | 明細 |
| `DSM901` | 23 | 有 | DSM | `DSMM901` | — | 主檔;`BATCHID` 由程式取號 |
| `DSM902` | 31 | 有 | DSM | — | `DSMM901` | 明細;CSV 匯入 + SP 回寫 `EXEAUM` |
| `DSM903` | 22 | 有 | DSM | `DSMM902` | — | 主檔 |
| `DSM904` | 40 | 有 | DSM | — | `DSMM902` | 明細;CSV 匯入 |
| `DSM905` | 27 | 有 | DSM | `DSMM903` | — | 主檔 |
| `DSM9051` | 25 | 有 | DSM | — | `DSMM903` | 明細;`EDATE` 被程式覆寫 |
| `SAL050` | 20 | 有 | **無模組** | `DSMM050` | — | 主檔 |
| `SAL051` | 22 | 有 | **無模組** | — | `DSMM050` | 明細;**全庫共用**(§8.4) |
| `OFD374A` | 22 | 有 | OFD | `DSMM060` | `BMSM001` `BMSM006` | 主檔;歸屬日期強制今天 |
| `BMS906` | 25(實體 7) | **無** | BMS | `DSMM906` | — | 主檔;三個寫入方法全 override |

### A.2 母體沒列、但本文有提到的表

| 表 | 為什麼母體沒列 | DSM 怎麼用 | 錨點 |
|---|---|---|---|
| `DSM006A` | 沒有畫面拿它當主明細,只出現在 `DSMI001Model.xsd`,被判成結果集 | **`DSMB001` 的產出、`DSMI001` 與 `DSMR003` / `DSMR004` 的來源** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:71-78` |
| `COD009` · `OFD002` · `BMS001A` | 外部唯讀 | 員工 / 部門 / 受益人的名稱與離職日,是全模組 join 最多的三張 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:127-128`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:126-127`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| `OFD068A` · `OFD303A` | 外部唯讀 | 銷售機構簡稱;結帳日判斷 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:237-242`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:185-189` |
| `OFD306` / `OFD306A` · `OFD221` / `OFD221A` | 外部唯讀 | 取「還有庫存」的機構 / 業務員;申購書資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:283-309`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320` |
| `OFD081` / `OFD081A` / `OFD081V` · `FSK003` | 外部唯讀 | 基金名稱與小數位;幣別小數位 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:219-220`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:257-258` |
| `CRM002A` | 外部唯讀(索引判為結果集) | `DSMI001` 的查詢權限 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |

## 附錄 B. SP / Function / Trigger / View

### B.1 Stored Procedure

`DB/SP/` 底下**只有一支** DSM 的 SP,其餘全部在版控外(`architecture.md 附錄 B.0` 說全庫只有 16% 的 SP 進版控,DSM 這邊的比例是 1/41)。

| SP | 在 `DB/` | 被誰呼叫 | 參數 |
|---|---|---|---|
| `S_TA_DSMB001_EXCUTE_P01` | **有**(cp950) | `DSMB001` | 計算日起、迄、更新者 |
| `S_TA_DSMM901_EXE` | 沒有 | `DSMM901` 執行 | 期別、執行者 |
| `S_TA_DSMM901_GET` | 沒有 | `DSMM901` 列印 | 期別、比較日、機構;2 個 RefCursor |
| `S_TA_DSMM901_AUM` | 沒有 | `DSMM901` 新增 / 修改明細後 | 期別 |
| `S_TA_DSMM902_EXE` | 沒有 | `DSMM902` 執行(覆核後自動) | 期別、執行者;OUT `strMsg` |
| `S_TA_DSMM906_IMP` | 沒有 | `DSMM906` 重建名單 | 員工代碼、模式(寫死 `"1"`) |
| `S_TA_DSMR001_GET_1`–`_5` | 沒有 | `DSMR001` | 見 §7.5 |
| `S_TA_DSMR002_GET_1` `_2` | 沒有 | `DSMR002` | 申購日起迄、機構、查詢者 |
| `S_TA_DSMR003_GET` · `S_TA_DSMR004_GET` | 沒有 | `DSMR003` `DSMR004` | 日期、報表別、業務別、含員工、含分攤、前 N 名(`DSMR003` 多一個排序) |
| `S_TA_DSMR005_GET_1` `_2` `_3` | 沒有 | `DSMR005` | 5 / 8 / 2 個 IN,游標數也不同 |
| `S_TA_DSMR006_GET_1` `_2` `_4` `_5` | 沒有 | `DSMR006` | 期間、業務別、單位別、報表別、定額別 / 促銷代碼 |
| `S_TA_DSMR007_GET` | 沒有 | `DSMR007` | 結存日、部門、員工…(部分參數被註解) |
| `S_TA_DSMR008_GET_1`–`_4` · `S_TA_DSMR008_1_Query` `S_TA_DSMR008_1_QryDetail` | 沒有 | `DSMR008` `DSMR008_1` |  |
| `S_TA_DSMR009_GET` `_GET_2` `_GET_MBR` · `S_TA_DSMR009_1_Query` `S_TA_DSMR009_1_QryDetail` | 沒有 | `DSMR009` `DSMR009_1` |  |
| `S_TA_DSMR010_GET_1` `_2` `_3` · `S_TA_DSMR010a_GET_3` · `S_TA_DSMR010b_GET` | 沒有 | `DSMR010` `DSMR010a` `DSMR010b` | `DSMR010a` 另兩支被註解;`DSMR010b` 吃計算日起迄 + 戶號 |
| `S_TA_DSMR011_GET` | 沒有 | `DSMR011` | 8 個 IN + 3 個 RefCursor |
| `S_TA_DSMR012_GET_2` `_3` · `S_TA_DSMR013_GET` | 沒有 | `DSMR012` `DSMR013` | `_GET_1` 的註解寫「原來的不用 by Mia」 |

### B.2 Function / Trigger / View

**本模組沒有引用任何 Function 或 Trigger**(母體第 3 節也是 0)。View 三支:

| View | 在 `DB/` | 被誰用 | 說明 |
|---|---|---|---|
| `OFD068A_V02` | **有**(112 行,cp950) | `DSMM901` `DSMM903`(外加 OFD 的 `OFDI011`) | 銷售機構六段 `UNION`,見 §8.6 |
| `DSMM901_V01` | 沒有 | `DSMM901` `DSMM902` 取通知信收件人 | 至少有 `DEPT` / `ROLE901` / `EMAIL` 三欄;`WHERE DEPT = 'S'`〔客戶特定〕;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259` |
| `V_SAL051` | 沒有 | 共用員工 DataSource | 2023-05-23 起取代直接查 `SAL051`;`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:277-291` |

## 附錄 C. 代碼對照

彙整 §2.5,方便查:

| 代碼 | 值 | 意義(反推) | 來源 |
|---|---|---|---|
| `STATUS` | `203` | 刪除待覆核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` |
| `STATUS` | `3` 開頭(見到 `301`) | 已覆核 / 生效 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:216`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206` |
| `SAL_CD` | `A` 部門主管 · `B` `C` 組長 / 業務員 · `D` `E` 助理 / (外)交割人員 | 從訊息文字反推 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:199-214`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:397-422`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:257` |
| `DEPT_CD` | `0` 大部門(3 碼部門專用)· `A` `S` 兩種小部門屬性 |  | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:172-183`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:397`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:411` |
| `FUND_TYPE` | `1` 境外 · `2` 境內 |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:222`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:260` |
| `AGENT_ID` | `0`–`5` | 直銷 / 銀行 / 券商 / 投顧 / 投信 / 產壽險 | `DB/View/OFD068A_V02.SQL:11`、`DB/View/OFD068A_V02.SQL:24` |
| `ROLE901` | `E` `V` `A` | 輸入 / 驗證 / 覆核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:127-132` |
| `MAIL_YN` | 空白 = 否;其餘 = 是 | **程式只認這兩種** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` |
| `EDATE` | `29991231` | 無限期 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355` |
| 下拉分類 | `000` 是否 · `300` / `322` 執行狀態(明細 / 主檔,**兩份**)· `412` 基金型別(過濾掉 `C`)· `458` `459` `460` `461` 部門屬性 / 主管獎金類別 / 業務屬性 / 獎金制度 |  | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:66`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:147-151`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:201-204`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-80` |
| `COD006A` 分類 | `D1` `D4` | 移轉類別 / 基金來源 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:152`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:137` |

## 附錄 D. 掃描母體與覆蓋率

### D.1 母體

`docs/_candidates/dsm.md` 由 `atlas_scan.py --module DSM` 產生:

| 類 | 母體數 | 本文處置 |
|---|---|---|
| 畫面 | 29(B 1 / I 1 / M 10 / R 17) | **全部寫到**:M 十支各一節(§4)、I §5、B §6、R §7 + §3.4 一覽 |
| 實體表 | 16 | **全部寫到**:附錄 A.1 逐張列,外加 A.2 補 12 張母體沒列的 |
| SP | 1(`S_TA_DSMB001_EXCUTE_P01`) | §6、附錄 B.1;另補 40 支版控外的 |
| Function / Trigger | 0 / 0 | 確認本模組不用(附錄 B.2) |
| View | 1(`OFD068A_V02`) | §8.6、附錄 B.2;另補 `DSMM901_V01` 與 `V_SAL051` |
| rpt | 40 | §7.2 一覽;另補 13 個「程式引用但 repo 內沒有」的 |
| Service | 0 | 確認本模組沒有(§6) |

### D.2 母體有四處與程式不符,以程式為準

| 母體怎麼說 | 實際 | 為什麼 | 本文寫在哪 |
|---|---|---|---|
| `DSMM005` **沒有主檔 / 明細** | 主檔是 `DSM005A` | PO 用多筆型的 `this.MasterTable.Add(...)`,掃描器只認 `this.MasterTable = new xTableMapping(...)` | §2.1、§0.5 |
| `BMS906` **只有 2 欄** | xsd 有 25 欄(實體 7 欄) | 掃描器只數自封閉且帶 `type=` 的 `<xs:element/>`;`BMS906` 有 23 欄是帶 `<xs:simpleType>` 子節點的寫法 | §2.3、附錄 A.1 |
| 只有 5 張表**有四眼欄位** | **15 張都有**(只有 `BMS906` 沒有) | 同上,四眼欄位多半是帶 `maxLength` 限制的巢狀寫法 | §2.2 |
| 16 張表(不含 `DSM006A`) | `DSM006A` 是本模組最重要的表之一 | 它只出現在 `DSMI001Model.xsd`,沒有畫面拿它當主明細,索引把它歸成結果集 | 附錄 A.2、§6.4 |

驗證方式(不改任何檔):`atlas_scan.py --table BMS906` / `--table DSM005A` / `--screen DSMM005`。

### D.3 `DSMB001` 的「六層不齊」是真缺

母體說 `DSMB001` 缺 model 與 view。`architecture.md 附錄 D.4` 列了兩種假警報(entity 檔名帶 `_9i`、`.Query` 專案改用 `OracleDao` 命名),**`DSMB001` 兩種都不是**:`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/` 與 `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/` 底下沒有任何 `DSMB001` 開頭的檔、也沒有 `_9i` 變體;DSM 也沒有 `.Query` 專案,PO 就叫 `DSMB001_PO`,命名完全合鐵律。

真正的原因寫在 Control 裡:`Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:38-39` 宣告 `ModelVDBType = typeof(BasicModelVDB)` / `ViewVDBType = typeof(BasicViewVDB)`,**刻意用框架的泛用 VDB**,參數靠 `Util.Parameters` 傳、結果靠 `Util.Result` 回,不需要 typed DataSet。這與 `architecture.md §6.4` 講的「B 跟 I 是同一份程式碼、常常沒有自己的 entity」一致。

唯一的旁枝是 `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs`:一支手寫的 29 行 VDB,UI 在用(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:36`)但 Control 不認識它,裡面的 `UIView` 屬性全 repo 零讀取(附錄 E11)。

### D.4 四支後綴變體不是掃描器的誤判

`DSMR008_1` / `DSMR009_1` / `DSMR010a` / `DSMR010b` 四支在母體裡都是獨立畫面、六層齊。實測它們確實各有完整六層(`_Ctl.cs` / `_Pxy.cs` / `_PO.cs` / `Model.xsd` / `View.xsd` / UI),**是真的四支畫面**,不是 `architecture.md 附錄 D.4` 講的 `_9i` 那種命名假警報。它們與本體的關係見 §7.4。

### D.5 本篇引用的覆蓋率

以 `atlas_scan.py --module DSM --doc docs/modules/dsm.md` 計:

| 類 | 母體 | 本文提到 | 覆蓋率 |
|---|---|---|---|
| 實體表 | 16 | 16 | **100%** |
| 畫面 | 29 | 29 | **100%** |
| SP / View | 2 | 2 | 100% |

母體沒列而本文提到的識別字(外部表、版控外的 SP、repo 內沒有的 rpt、彈出子視窗),全部列進 `meta` 的 `refcheck-ignore`,清單見本文開頭。

### D.6 怎麼自己重跑

```
py -V:3.12 docs\tools\atlas_scan.py --module DSM [--doc docs\modules\dsm.md]
py -V:3.12 docs\tools\atlas_build_doc.py docs\modules\dsm.md --repo-root  --report docs\modules\dsm.refcheck.md
```

## 附錄 E. 讀本文時要注意的地方

讀碼過程中發現的缺陷與陷阱。每條:缺陷 / 影響 / 錨點 / 嚴重度。**沒有任何一條被修改過**,本文只是把它們寫下來。

### E1 會直接產生錯誤資料或讓畫面開不起來的六條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`MAIL_YN` 讀進畫面時被改成 `Y`**:判斷式只分「空白 → N」「非空白 → Y」,資料庫存 `N` 也會顯示成 `Y` | 一筆「不寄對帳單」的設定,只要有人打開修改畫面再存檔就變成「要寄」。**業務後果最直接的一條** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:200` | **高** |
| 2 | **`DSMM903` 用 `_DSHead_INFORow` 前只檢查了第一次**:`if (Count > 0)` 之後兩處無條件解參考 | 沒有任何在職的直銷部門主管(`SAL051.SAL_CD = 'A'` 且未離職)時,`FormInitial` 丟 `NullReferenceException`,**畫面完全開不起來** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:205-208` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:217`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` | **高** |
| 3 | **`emp_Info.Count() > 1` 數的是字元不是欄位**:作者要的是 `Split(',').Count() > 1` | `GetEMP_INFO` 回傳少於 4 段時 `Split(',')[2]` / `[3]` 丟 `IndexOutOfRangeException`,`DSMR008` / `DSMR008_1` 開不起來 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74-78`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:74-78` | **高** |
| 4 | **`DSMM906.Delete` 的守衛寫反**:`Rows.Count < 0`(不可能成立)且用 `&&` 串一個會解參考的條件 | 空集合時得不到「傳入主檔表格至少一個」的友善訊息,而是在下一行 `Rows[0]` 丟例外 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:247` | 中 |
| 5 | **`catch { tran.Rollback(); }` 但 `tran` 在 `try` 內才賦值**:17 支報表 PO 全部這樣寫 | 連線開失敗、或 `try` 前段(日期轉換)丟例外時,真正的錯誤被 `NullReferenceException` 蓋掉。與 `architecture.md §3.11` 記錄的 `BasicEVAPO` 同型 | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:211-216`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:93-98`(其餘 15 支同型) | 中 |
| 6 | **`DSMM901` 的結帳日檢核只在第一次移轉時跑**:`if (row.EXESEQ == 1)` | 同一個批次第二次執行完全不驗結帳日,可以對未結帳的期間動資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184` | 中 |

### E2 Oracle 三值邏輯:`<> 'Y'` 抓不到 NULL

| 項 | 內容 |
|---|---|
| 缺陷 | `DSMB001` 的「有沒有基金還沒結帳」檢核寫成 `AND POST_CTL_CODE <> 'Y'`。Oracle 裡 `NULL <> 'Y'` 是 UNKNOWN,那一列不會被選出來 |
| 影響 | **結帳旗標還沒寫入(NULL)的基金,不會被判定為「未結帳」**,收入批次照跑,算出來的 `DSM006A` 可能少了那檔基金的資料 |
| 錨點 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:136` |
| 同型前例 | CAS 的 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` |
| 正解 | `AND NVL(POST_CTL_CODE,'N') <> 'Y'` 或 `AND (POST_CTL_CODE IS NULL OR POST_CTL_CODE <> 'Y')` |
| 嚴重度 | **高** |

全模組再掃一次同型寫法:除了這一處,DSM 沒有其他 `<> '值'` 的過濾條件(`DSMI001` 的 `A.DEPT_NO <> 'G'` 那一段用了 `NVL(A.DEPT_NO,' ')` 包起來,是對的,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:97`)。**寫對的那一處與寫錯的那一處在同一個模組裡**。

### E3 「月分配」三支畫面三種算法,其中一支一定算錯

| 畫面 | 可分配月數 | 修改模式補餘額的判斷 | 結果 |
|---|---|---|---|
| `DSMM001` | `13 - 起算月` | `j < iMONTH_COUNT` | **正確**(但列數多於月數時餘額會被重複寫,見 §4.1) |
| `DSMM002` | 固定 `12` | `j < 12` | 一致,但會跨到次年 |
| `DSMM003` | `13 - 起算月` | **寫死 `j < 12`** | **起算月 ≠ 1 時,餘額永遠不會被寫回去** |

`DSMM003` 那條的實際表現:起算月 7 月 → 6 列明細 → `j` 最多到 6,永遠進不了 `else` → 六列都是 `Math.Floor(年度/6)` → 總和小於年度 → 存檔被「年度淨銷售金額 與 月分配總和不符」擋下 → 使用者只好手動改最後一列。

錨點:`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:215`;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:201-206`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:213`;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:121`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130`。嚴重度:**中**(會被後續檢核擋下,不會產生錯資料,但每次都要手工修)。

### E4 被註解掉但外殼還在的檢核

| # | 被拿掉的檢核 | 錨點 | 註解裡的理由 | 嚴重度 |
|---|---|---|---|---|
| 1 | `DSMM001` 與 `DSMM002` 六個指標「必須大於 0」(主檔 + 明細,各 12 條) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:78-89` | 無 | 中 |
| 2 | `DSMM002` 查詢的員工代碼起迄檢核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` | 無(連對應的查詢條件也一起註解了) | 低 |
| 3 | `DSMM901` CSV 匯入「移轉後機構必須是直銷」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448` | 「20190808 … 不檔移轉後需為直銷單位」 | **高**(有票號可查) |
| 4 | `DSMM901` CSV 匯入「移轉前後不可完全相同」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` | 「鳳滿說為了活化1不擋 20180820」 | **高** |
| 5 | `DSMM901` `CheckExists` 的「戶號須有該機構 / 員工的結餘」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:355-369`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` | 同上 | **高** |
| 6 | `DSMM901` 移轉後員工的部門與在職檢核(`sqlEm` 被換成 `sqlEmpNM`) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430` | 「20190812 … 程式名稱及業務移轉範圍」 | **高** |
| 7 | `DSMM902` 執行基準日的 `MaxDate = 今天` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` | 無 | 中 |
| 8 | `DSMM902` 覆核後的「執行」通知信 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:279` | 無(改成直接執行) | 低 |
| 9 | `DSMM050` / `DSMM903` 逐列檢核的 7 處 `e.Cancel = true;` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:413`(共 7 處) | 無 | 中 |
| 10 | `DSMR010b` 的基金三選一檢核 · `DSMR010a` 的兩支 SP 呼叫 · `DSMI001_PO` 的 `GetEmail` 整支 · `DSMM906_PO` 的 `BeforeDelete` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:333-345`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:62`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:318-349`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:138-142` | 無;`DSMM906` 的刪除改由 `AND UPD_USER = :UPD_USER` 隱性擋 | 低 |

**第 3–6 條(`DSMM901` 那四條)是同一段時期(2018-08 到 2019-08)為了「活化」業務移轉功能而一起放寬的**,四條都有明確的人名或票號。**要收緊之前先找到那批決策的來源**,不要只看程式。

### E5 併發與參數處理

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`BATCHID` 用 `MAX(...)+1` 取號,沒有鎖也沒有序列** | 兩人同時新增拿到同一個期別,第二個人存檔時撞主鍵 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:58-64`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:57-63` | 中 |
| 2 | **`S_TA_DSMM901_AUM` 在 `foreach` 內重複 `AddInParameter` 同一個名字,沒有 `Parameters.Clear()`** | 主檔多於一列時,同一個 command 累積重複參數 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:131-139` | 中 |
| 3 | **`DSMM903` 用 `static` 欄位存四個常數** | 目前是唯讀常數所以不會互踩,但與 BMS `BMSB901A` 那條「靜態批號兩人同跑互刪」是同一種寫法 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29` | 低 |
| 4 | **`DSMM005.Copy` 的 GUID 只在迴圈外產一次** | 拷貝多個月時,所有新列的 `DATAID` 是同一個值 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:237-244` | 中 |
| 5 | **`DSMR001` 逐月迴圈裡重新指派 `tran`,舊的不釋放** | 一次查 12 個月會開 12 個交易物件,只有最後一個被 `Dispose` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:152` | 低 |
| 6 | **`DSMB001_PO` 在 `finally` 釋放類別層級的 `m_db`** | 目前因為 PO 每次 new 而不出事;PO 若改成共用實例,第二次呼叫就拿到已釋放的連線 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:31` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:95-99` | 低 |
| 7 | **`DSMM903_PO` / `DSMM906_PO` 各自 new 一個獨立的 `Database`** | 那些查詢不在四眼的交易裡,讀到的是交易外的資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:30`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:28` | 低 |

### E6 位置取參數

`ClientBizUtility.GetEMP_INFO(UserID)` 回傳一個逗號分隔字串(無原始碼),九支畫面用位置取值,**三種不同的長度保護**:

| 寫法 | 用在哪 | 安全嗎 | 錨點 |
|---|---|---|---|
| `if (非空白) { …Split(',')[1] }` | `DSMM906` `DSMR001` `DSMR002` `DSMR007` `DSMR009` `DSMR009_1` | **否**,單段回傳就爆 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:52-55` |
| `if (words.Length > 1 && words[1] != "")` | `DSMI001` | **是** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:106-111` |
| `if (emp_Info.Count() > 1) { …[2]; …[3] }` | `DSMR008` `DSMR008_1` | **否**,而且守衛本身寫錯(E1-3) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74-78` |

其他位置取值:

| 位置 | 取什麼 / 沒保護時的後果 | 錨點 |
|---|---|---|
| `custDEPT_NO.Value.Substring(0, 1)` · `LEAVE_DATE.Substring(0, 4)` + `Convert.ToInt16` | 部門第 1 碼判直銷 / 離職年份;空字串或格式非 `yyyy…` 丟例外 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:494`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:516` |
| `xUserDept.Substring(0, 3)` · `UserID.Substring(6)` + `Convert.ToInt32` | 部門前 3 碼 / 列印帳號序號;少於 3 碼或後綴非數字丟例外 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:110`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:136` |
| `beg_date.Substring(0, 10)` | 日期前 10 碼;短於 10 碼丟例外 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172` |

### E7 SQL 層面的髒寫法

| # | 寫法 | 出現處 | 嚴重度 |
|---|---|---|---|
| 1 | **查詢值直接串進 SQL,不綁參數也不跳脫**(`DSMM001_PO` `DSMM002_PO` `DSMM003_PO` `DSMM903_PO` `DSMM906_PO` `DSMI001_PO` `DSMR003_PO` `DSMR004_PO` 全部);唯一做跳脫的是 `DSMM050_PO`,真正綁參數的只有 `DSMM005_PO` `DSMM060_PO` `DSMM901_PO` `DSMM902_PO` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:140`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:318`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:139`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:58` | 中(`DSMM906` 的姓名 / 身分證是使用者自由輸入) |
| 2 | **`LIKE` 條件不補 `%`**,等同於 `=` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:146` | 中 |
| 3 | **`LEFT JOIN` 被 `WHERE` 條件退化成 INNER** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:123-125` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` | 中 |
| 4 | 舊式逗號 join · `ORDER BY` 被註解且註解裡是別的畫面的欄位 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:150` | 低 |
| 5 | 日期字面量前後多空白 · `SELECT DISTINCT COUNT(*)` · `SYSDATE ASENTRYDATE` 別名黏字 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:161`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:271` | 低 |
| 6 | 綁定變數當分支開關(`AND :FUND_TYPE = '2'` … `UNION` … `= '1'`) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320` | 低(兩段的 join 對象不同,很容易只讀一半) |
| 7 | 參數型別與欄位型別不符:`BF_NO` / `BATCHID` 是 decimal 卻綁 `Varchar2` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:369`(同檔 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:358` 用 `Decimal`)、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:117` | 低 |

### E8 有訊息但沒有 `return` / 訊息誤導

| # | 情況 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `DSMM050` / `DSMM903` 的逐列檢核顯示訊息但 `e.Cancel` 被註解 | E4-10 | 中 |
| 2 | 訊息文字或掛的控件對不上:`DSMM903` 的「計算日(迄)」寫成「計算日(起)」、`DSMM050` 的獎金類別訊息掛在部門屬性上、`DSMM005p0` 的五條訊息全掛在業績年月上 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:167`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:167`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:141` | 低 |
| 3 | `DSMM050` / `DSMM903` 的 `BeforeRowUpdate` 每段檢核前都 `ValidateErrList.Clear()`,**只看得到最後一條錯誤** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:360`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:369`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:378` | 低 |
| 4 | `DSMM906` 刪除失敗只說「影響筆數等於 0 筆」,不說真正原因是 `UPD_USER` 不符;`DSMI001` 權限不足與真的沒資料**都顯示「查無資料」** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:227-230` | 中 |
| 5 | `DSMB001` / `DSMM903` / `DSMM005` 的例外一律回固定字串,不帶原因 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:92`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:272` | 中 |
| 6 | **相反的問題**:`DSMM901` / `DSMM902` 的 `catch` 把 `ex.ToString()` 當結果訊息回給前端;`DSMM906.chkBF_NO_Valid` 也回 `ex.Message` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:268`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:284`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:403-407` | 中(堆疊資訊外洩到 UI) |

### E9 一律回成功 / 回傳值判斷可疑

| # | 情況 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `DSMB001.Execute` 呼叫 SP 之後**硬寫 `i = 1`**,`else` 分支永遠到不了 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:74-87` | **高**(批次失敗看不出來) |
| 2 | `DSMM901.Execute` 的 SP 沒有 OUT 錯誤通道,只要不丟例外就回「執行成功」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:481-486` | **高** |
| 3 | `DSMM005.Copy` 用 `ExecuteNonQuery` 的回傳值判斷成敗,而它跑的是 PL/SQL 匿名區塊 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:290-302` | 中(**假設**成功會被誤報成失敗) |
| 4 | `DSMM906.RebuildBF_List` 同樣拿 `ExecuteNonQuery` 的回傳值當成敗 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:431-435` | 中(**假設**) |

### E10 寫死常數〔客戶特定〕

| 值 | 意義 | 錨點 |
|---|---|---|
| `"B,C"` / `"C"` · `S0%` / `08%` | 兩支畫面挑業務員的業務屬性不同;`DSMM003` 部門下拉只列這兩種開頭 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:305`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:207`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:205` |
| `'S'→'G'`、`'090'→'I'` | `DSMM002` 取數的部門對照 `DECODE` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:127` |
| `'0'` / `'S%'` · `30` · `29991231` | `DSMM903` 的四個常數、公單拆帳比例預設值、無限期迄日 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:276`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355` |
| `AO_CODE = 'Y'` · `DEPT = 'S'` · `6` | `DSMM050` 挑員工的條件;通知信 view 的過濾;員工代碼補 0 的長度 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:440` |
| `ta-it@example.com` | 寄件人取不到時的退路 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:113`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:100` |
| `'G'`、`08001` / `08101` / `08201` | `DSMI001` 的部門與機構白名單 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:96` |
| `101722` · `S01` / `S05` · `ntaprt` + 5–11 | `DSMR008` / `DSMR008_1` 的三組全域權限白名單 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:117-118`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:135-136` |
| `'551'` / `'永豐金證券'` · `"1"` | view 內硬寫的券商資料列;`DSMM906` 重建名單的模式參數 | `DB/View/OFD068A_V02.SQL:76`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:429` |

### E11 同一概念多套實作 / 死碼

| # | 情況 | 錨點 |
|---|---|---|
| 1 | `GetDropDownDataSrc` 與 `GetDropDown9iDataSrc` 對同樣的代碼分類並存 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-78` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:115-117` |
| 2 | `DSMR008` / `DSMR008_1`、`DSMR009` / `DSMR009_1`、`DSMR010` / `DSMR010a` 三組平行實作 | §7.4 |
| 3 | `DSMR001RPS31.cs` 宣告與 `DSMR001RPS3.cs` **同名的類別**,不在 csproj 內,是沒刪乾淨的孤兒 | `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS31.cs:19` |
| 4 | `DSMBViewVDB` 有 UI 在用,但 Control 宣告的是 `BasicViewVDB`,那個 `UIView` 屬性從沒被讀過 | `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs:18-22` 對 `Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:39` |
| 5 | `DSMI001_PO` 的 `GetEmpNo` / `GetUidCode` 是 public 但介面宣告被註解,拿不到;同檔 new 了 `dbPTPF` 卻沒用 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:26-27`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:37` |
| 6 | 三個取了卻沒用的變數:`GetDSHeadInfo` 的 `user_id`、`DSMM050` 的 `Employ_Util` 與 `tmpVDB`、`DSMM903` 的 `myEDATE` 初值 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:247`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:87-91`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:145-146`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61` |
| 7 | `DSMM902_PO` 的三個事件方法是空殼,卻照樣掛上去 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:105-108`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:115-118` |
| 8 | `SAL051.TOT_ADD_AC` 欄位 repo 內零讀寫(但可能被版控外的 SP 用,**不要刪**) | `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd` |
| 9 | 十個 PO 的介面註解全寫「覆核層級管理 PO 共用介面」;三個 PO 的明細 region 註解寫「明細資料 SQL(OFD200)」,都與實際功能無關 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:19`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:211` |

### E12 其他讀碼陷阱

| # | 陷阱 |
|---|---|
| 1 | **`DSMM002_PO` 內出現的 `SAL051` 與 `EMP_NO` 條件全在註解區塊**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:149-189`)。用 grep 找「誰 join 了 `SAL051`」會誤判 |
| 2 | **五處 `App.config` 的 `detailtable` 註解全寫 `DSM002A`**,包含 `DSMM050`(§0.5) |
| 3 | **`DSMM901p0` 那三條檢核比 CSV 匯入嚴格**,同一支畫面兩條輸入路徑兩套規則(§4.7) |
| 4 | **`DSMM903` 的 `EDATE` 使用者打了也會被覆蓋**(§4.9) |
| 5 | **`DSMM060` 修改一筆舊資料會把歸屬日期改成今天**(§4.6) |
| 6 | **`DSMR010b` 的名字像 `DSMR010` 的變體,實際上是另一張報表**(§7.4) |
| 7 | **`DSM006A` 不在母體的 16 張表裡**,但它是整個 E 線的核心(附錄 A.2) |
| 8 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:89` 的括號位置寫錯(單引號被接在 `object` 上),目前結果碰巧正確 |
| 9 | `DSMM901p1` 列印時會把 `.rpt` 寫進使用者的「我的文件」再刪除;`File.Delete` 失敗就留檔(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p1.cs:121-124`) |
| 10 | **本模組所有原始檔都是 UTF-8 with BOM**,沒有 BMS 那種混編碼問題(實測 `Dev/ATLAS.DSM/` 與 `Dev/ATLAS.DSM.Report/` 底下的 `.cs` / `.xsd` / `.config` 共 0 個例外) |

### E13 標「假設」的地方一覽

| # | 假設 | 依據 | 怎麼驗 | 在哪一節 |
|---|---|---|---|---|
| 1 | 拆帳比率 / 分攤比率由 `S_TA_DSMB001_EXCUTE_P01` 在 DB 端套用 | repo 內零程式讀 `RATE_A` / `RATE_B` / `SHARE_RATE`;`DSMB001` 的檢核直接查 `DSM006A` | 撈 SP 原始碼 | §0.3 |
| 2 | 本站台的 `STATUS` 是三碼(`2xx` 待覆核、`3xx` 已覆核) | `203` 與 `301` 兩個實際值 + `StartsWith("3")` | 查 `TA_STATUS` 相關代碼表或反編譯 `MappingCode` | §2.5 |
| 3 | `DSMM902` 的 `pkey` 中間有空白會讓第三個 PK 名對不上欄位 | 同檔其他六處都沒有空白 | 看框架怎麼切字串,或實測 grid 的 PK 檢查 | §0.5 |
| 4 | `DSMM005.Copy` 成功時會被誤報成失敗 | `ExecuteNonQuery` 對 PL/SQL 匿名區塊的回傳值定義 | 實跑一次拷貝 | §4.4 |
| 5 | `DSMM906` 的重建名單鈕可能永遠顯示「執行失敗」 | 同上 | 實跑一次 | §4.10 |
| 6 | `DSMM903` 挑人條件 `LEAVE_DATE >= '29991231'` 能用,是因為共用控件把 NULL 當 `29991231` | 其他畫面都寫 `OR LEAVE_DATE IS NULL`,只有這裡沒寫卻還能用 | 看 `EmployeeDataSrc` 的實際 SQL,或實測下拉有沒有人 | §4.9 |
| 7 | `DSMI001` 的日期字面量前後空白目前能跑,是因為 Oracle 容忍前導空白 | 這段程式運行多年 | 換 provider 或改 NLS 前實測 | §5.3 |
| 8 | `DSMR005` 的「退休財富管理」不支援 Excel 匯出 | Excel 的 `switch` 只列 168 與非 168 兩支 | 實測 | §7.5 |
| 9 | view 的常數列 `'551','永豐金證券'` 可能在去重時贏過真實資料 | `PARTITION BY` 用的是補位後的代碼,常數列與真實列可能落在同一組 | 撈 `FSK005` 看 `551` 在不在 | §8.6 |
| 10 | `BMS906` 原本規劃在 BMS,後來功能移到 DSM 但表名沒改 | 18 個欄位來自 `BMS001A`;它是唯一不走四眼的 DSM 維護畫面 | 問業務或查當年的需求文件 | §8.3 |
| 11 | `DSMB001` 的 `m_db` 在 `finally` 被釋放目前不出事,是因為 PO 每次都是新實例 | `architecture.md §2.2` 說 Control 在 `InitializeDataAccessPool` 裡 new | 看框架的 DataAccessPool 生命週期 | §6.6 |
| 12 | 一日作業泳道(§1.5) | `DSMB001` 要求該段日期的基金都已結帳 | 問實際作業人員 | §1.5 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。29 支畫面全數涵蓋;16 張表 + 12 張外部表;41 支 SP、3 支 view、40 個 rpt。已與 `cas.md §8.4`(`DSM001A` / `DSM002A`)、`bms.md`(`OFD374A`)、`change-sp-fn-trigger.md §7`(`OFD068A_V02`)對過,結論一致。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 187 · 圖 5 · 表格 105 · 程式錨點 740 · § 連結 100 · 引用檢查：畫面 35（缺 0） · Table 29（缺 0） · SP 1（缺 0） · View 1（缺 0） · Report 29（缺 0） · 結果集 8（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
