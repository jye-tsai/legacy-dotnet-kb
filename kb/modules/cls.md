<!-- 由 tools/build_copilot_kb.py 從 modules/cls.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS CLS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最容易被誤會的事)、§4 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由彈出視窗標題、表名與欄位中文名(`msdata:Caption`)**推測**,待選單表 / 對照表回填。7 支畫面裡只有 5 支彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼樣式(`S____`)、業務屬性碼(`A` / `B` / `C`)、每公里補助 6 元、30 天回補期限、遮罩長度、`USAGE = '2'`、報表編號「`CLSR002-1`~`-12`」的對外名稱為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`CLS001A` / `CLS002A` 名字看起來是 CLS 的,主人卻是 CAS(見 §8),改動要一起看。

> ⚠ **路徑大小寫**:`Dev/ATLAS.CLS/` 底下的子目錄是大寫 `SOURCE`,不是 `Source`(全庫 36 個專案只有 2 個這樣,見 `architecture.md §2.6`)。`Dev/ATLAS.CLS.Report/` 則是一般的 `Source`。本文錨點照實際大小寫寫,不要「順手改成一致」。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CLS 管「直銷業務員手上的潛在客戶名單,以及他們去拜訪這些客戶留下的紀錄」。**

推測依據五條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 彈出視窗標題 | 「**直銷**客戶查詢作業」——全模組唯一直接寫出業務屬性的字串 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:1073` |
| 表名與欄位中文名 | `CLS001` 的欄位是「潛在客戶序號」「潛在客戶來源代碼」「歸屬業務員」「KYC到期日」「境內庫存 / 境外庫存」;`CLS002` 是「拜訪單號」「預計 / 實際拜訪日期」「交通費」「拜訪記錄」 | `Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM001Model.xsd`、`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM002Model.xsd` |
| 明細彈出視窗標題 | 「目的/支援」「推薦基金」「批次新增拜訪重點」「受益人基本資料」 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.Designer.cs:351`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.Designer.cs:352`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.Designer.cs:172`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001p0.Designer.cs:171` |
| 報表中文名 | 「業務員客戶清冊－總表 / 明細表 / 基金別 / 當月壽星」「客戶來源清冊」「客戶拜訪記錄明細表」「客戶拜訪統計表－未過試用期」「交通費明細表」 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.Designer.cs:369-380`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.Designer.cs:608-627` |
| 建檔權限的判斷式 | 只有 `SAL051` 的業務屬性是 `A` 部門主管 / `B` 組長 / `C` 業務員才能建檔,其餘(助理、交割、其他)只能看 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479`、`:504-510` |

「CLS」三個字母本身的展開在 repo 裡找不到定義,**不要猜**。本文一律用「直銷潛在客戶」描述它的業務範圍,這是從上表推出來的,不是官方名稱。

兩條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 潛在客戶 | 業務員自己維護的潛在客戶名單:來源、風險屬性、KYC 期限、決策者、投資意願與上下限、境內外庫存(AUM) | `CLSM001` | `CLS001` |
| B 拜訪單 | 對名單上的人做的每一次拜訪:預計 / 實際日期與方式、主談者、拜訪重點、推薦了哪檔基金、客戶提了什麼新產品需求、交通費 | `CLSM002` | `CLS002` + `CLS003` `CLS004` `CLS005` |
| C 重算與參數 | 把庫存重算進 `CLS001` 並留一版快照;維護交通費上限與應拜訪次數兩個門檻 | `CLSB001`、`CLSB002` | `CLS012` 與 SP |
| D 報表 | 上面兩條線的清冊與統計,共 22 支版型 | `CLSR001`、`CLSR002` | `CLS001H` 快照 + SP |
| E 借來的查詢 | 看 CAS 那套「客戶拜訪單」裡屬於直銷的那一半 | `CLSI001` | `CLS001A`〔共用〕 |

### 0.2 這模組最容易被誤會的兩件事

**第一件:`CLS001`–`CLS005` 與 `CLS001A` / `CLS002A` 是完全不同的兩套東西。**

|  | `CLS001`~`CLS005` | `CLS001A` / `CLS002A` |
|---|---|---|
| 主檔畫面 | `CLSM001` / `CLSM002`(CLS 自己) | **`CASM002`**(CAS 的客戶拜訪單維護) |
| 拜訪單號欄位 | `CLL_NO` | `CALL_RPT_NO` |
| 潛在客戶主檔 | `CLS001`(CLS 自己維護) | `CRM003A`(CRM / TMK 維護) |
| CLS 這一側怎麼用 | 四眼維護、批次、報表全都用 | **只有 `CLSI001` 唯讀查詢**,而且硬加 `USAGE = '2'` |
| 已寫在哪 | 本文 §2–§7 | `cas.md §8`(從 CAS 那側寫過) |

驗證方式:`atlas_scan.py --table CLS001` 回報「主檔於 `CLSM001`、模組 CLS」;`atlas_scan.py --table CLS001A` 回報「主檔於 `CASM002`、模組 CAS, CLS」。掃描器把 `CLS001A` 歸到 CLS 只是因為**名字開頭三碼**,不是因為 CLS 擁有它。`CLSI001` 的 SQL 也證實這點:`FROM CLS001A` 之後 join 的是 `CRM003A` 與 `CAS004A`,沒有一張 CLS 自己的表(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106-112`)。

**第二件:報表看到的客戶名單,不是現在的 `CLS001`,是批次跑完那天的樣子。**

兩支 R 畫面(以及 `CLSM002` 的查詢)都不直接讀 `CLS001`,而是先用一段叫 `ISHIS` 的 CTE 從 `CLSB001` 取最後一次批次日期,再決定要讀 `CLS001H` 歷史快照還是 `CLS001` 現值:

- 查詢區間的迄日**早於**最後一次批次日 → 讀 `CLS001H`(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:73-83`)

- 查詢區間的迄日**就是**最後一次批次日 → 讀 `CLS001`(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:95-104`)

也就是說**同一筆客戶資料,剛改完馬上查報表看到的可能是舊值**,而且畫面上沒有任何提示。詳見 §2.5 與 §7.2。

### 0.3 不管什麼

以下**不在** CLS 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(已開戶客戶)基本資料 | BMS | `BMS001A` 全部是 `LEFT JOIN` 或 `SELECT`,零 INSERT / UPDATE;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:189-190` |
| 員工主檔、離職日、到職日 | COD | `COD009` 只被 join;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:191-192` |
| 業務屬性與部門歸屬 | 不明(`SAL051` 的主人不在 CLS) | CLS 只 `SELECT`;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:490-494` |
| 「誰可以查誰」的權限資料 | CRM | `CRM002A` 只被 `CLSR001_PO.GetInitData` 讀出來當過濾清單;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:118-137` |
| 基金主檔、淨值、匯率 | OFD | `OFD081A` / `OFD300` 只讀;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:317-319` |
| 實際申購 / 贖回交易 | OFD | `OFD221A_V01` / `OFD251A` 等只在報表被 join 加總;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:889`、`:909` |
| 庫存(AUM)怎麼算出來的 | **版控外的 SP** | `CLS001` 的四個 AUM 欄只由 `S_TA_CLSB001_EXE` 寫,原始碼不在 repo;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:53` |
| 代銷通路的客戶拜訪 | CAS | `cas.md §4.2`;CLS 這側只有 `CLSI001` 讀得到 `USAGE = '2'` 的那一半 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 直銷業務員(`SAL_CD` = `C`) | 建自己的潛在客戶(`CLSM001`)、填拜訪單(`CLSM002`)、印自己的清冊 | 建檔權限判斷在 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:504-510`;拜訪單只看得到自己建的,`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292` |
| 組長 / 部門主管(`SAL_CD` = `A` / `B`) | 同上,另外可以查到底下業務員的資料 | 可查範圍來自 `CRM002A`,`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:120-137`;`INQ_EMP_NO = 'ALL'` 代表整個機構都看得到 |
| 助理 / 交割 / 其他(`SAL_CD` = `D`~`F`) | **只能看不能改**,一進維護頁就跳訊息並鎖住三個鈕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:369-376`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:375-382` |
| 覆核者 | 對 `CLSM001` / `CLSM002` 做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |
| 作業人員 | 跑 `CLSB001` 重算庫存、用 `CLSB002` 調兩個門檻 | 兩支 B 畫面都是人工按「執行」,沒有排程 |

**注意:除了 `SAL_CD` 那條判斷與 `CRM002A` 的可查清單之外,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3`)。

### 0.5 全域開關

repo 內**沒有**任何 CLS 專屬的 `.config` 開關。兩支 `App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:15`(`CLSM001` → `CLS001` / `PR_NO`)、`:22`(`CLSM002` → `CLS002` / `CLL_NO`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:16`、`:23` |
| `formstyle` | `CLSB001` / `CLSB002` / `CLSI001` 宣告為 `OneStep`;兩支 R 宣告為 `Report` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:29`、`:47`、`:53`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/App.config:9` |

三個要記住的:

- **`CLSM002` 沒有宣告 `detailtable`**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:19-25`),但 PO 宣告了三張明細(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:45-47`)。設定檔與程式不一致,**以程式為準**——這跟 CAS 那邊一模一樣(`cas.md §0.5`)。

- **兩支 R 畫面在兩個 `App.config` 裡各宣告一次**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:6-7` 與 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/App.config:3-4`)。R 畫面住在 `.Report` 專案(`architecture.md §6.5`),主專案那兩行是複製殘留。

- **業務參數不在 config,在資料表**:交通費上限 `TRFF_LMT` 與未過試用期應完成次數 `NEED_TM` 存在 `CLS012`,靠 `CLSB002` 畫面改(§6.2)。

`TargetFramework` 側:兩個 `App.config` 都宣告 `.NETFramework,Version=v4.8`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:57`),而五支 PO 檔頭都留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡(例 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:5`)——跟 CAS 同一批逐檔改的。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CLS 模組的四塊:潛在客戶維護、拜訪單維護、兩支批次、兩支報表
圖中文字:A 直銷潛在客戶(四眼) / CLSM001 / CLS001 潛在客戶主檔 / BMS001A / 有戶號就改抓受益人 / SAL051 / SAL_CD 決定能不能建檔 / CRM002A / 可查的機構與員編 / B 拜訪單(四眼 · 一主三明細) / CLSM002 / CLS002 拜訪單 / CLS003 / 拜訪重點與內部支援 / CLS004 / 推薦基金 / CLS005 / 新產品需求 / OFD300 / 匯率換台幣 / C 批次 / CLSB001 / S_TA_CLSB001_EXE 快照 / CLS001H + CLSB001 表 / 每次執行留一版 / CLSB002 / 改 CLS012 兩個門檻 / D 報表(取數全部繞開 A 與 B 的 PO) / CLSR001 / 9 支 rpt · 走 SP / S_TA_CLSR001_GET_n / 原始碼不在 repo / CLSR002 / 13 支 rpt · 自組 SQL / CLS001H 快照當主檔 / 報表看的是批次日的樣子
```

*圖:圖 1 全景。CLS 只有兩條業務線(潛在客戶、拜訪單),兩者靠 `PR_NO` 相連。橘色虛框是會咬人的地方:建檔權限來自別的模組的 `SAL051`、報表讀的是 `CLS001H` 快照而不是現值。黑箱是無原始碼或不屬於 CLS 的東西。*

看圖的三個重點:

1. **兩條業務線靠 `PR_NO` 相連,沒有程式呼叫關係。** `CLSM002` 不會叫 `CLSM001` 的畫面,但它會透過 `CLSM001_Pxy.Query()` 去查 `CLS001`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:159`)——是唯一一處跨畫面呼叫。

2. **報表那一排與維護那一排是斷的。** `CLSR001` 的資料全部來自版控外的 SP;`CLSR002` 自己組 SQL,但主檔讀的是 `CLS001H` 快照。所以**報表數字與維護畫面寫進去的值之間,在 repo 內看不到直接關係**(§7)。

3. **`CLSR001_PO.GetInitData` 是全模組的權限來源。** 兩支 M、兩支 R 一共四個畫面的 `FormInitial` 都去呼叫它拿可查機構與員編(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:289-291`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:237-239`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:150-152`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:143-145`)。**一支報表的 PO 變成了模組的權限服務**,改它會同時影響四個畫面。

### 1.2 資料表關係

見 §2 節首的圖。要記住的是:

- **主明細的綁定靠 `dataid`,不是靠外鍵**(`architecture.md §3.3`),所以 `CLS002` 與三張明細一定一起送審、一起覆核。

- **`CLL_NO` 是在伺服器端才灌進明細的**。`CLSM002_PO_BeforeAdd` 取完單號後,把 `CLL_NO` 迴圈寫進 `model.DataEntity` 的每一張表(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:102-104`);修改時則由 UI 端做同一件事(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:483-485`)。**同一個動作有兩份實作,一份在伺服器一份在用戶端。**

- **`CLS001` 有兩個「入口形狀」**:寫入走 `CLS001`,查詢走 view `CLS001_V01`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188`)。view 的定義不在 repo(`DB/View/` 只有兩支,都不是它)。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。四個階段的分工:① UI 進畫面時決定能不能改、② UI 存檔前檢核、③ PO 的 `BeforeAdd` 取號、④ 框架跑四眼、⑤ PO 的 `After*` 寫跳號註記。**`CLSM001` 只掛了 `AfterAdd` / `AfterUpdate` 兩個事件而且兩個都是空的;`CLSM002` 掛了八個**(§4.2)。

### 1.4 批次 / 報表資料流

見 §6 與 §7 節首的圖。兩張圖合起來看會發現一條隱藏的相依鏈:`CLSB001`(人工按執行)→ `S_TA_CLSB001_EXE` → `CLS001` 的 AUM 欄 + `CLS001H` 快照 + `CLSB001` 表的 `EXEDATE`,而 `CLSR001` / `CLSR002` / `CLSM002` 的查詢**全部從最後那個 `EXEDATE` 起算**。

**沒跑 `CLSB001` 就沒有快照,沒有快照 `ISHIS` 那段 CTE 取不到 `QDATE`,整份報表空白。**這條相依沒有任何地方寫下來,也沒有任何檢查。

### 1.5 一日作業泳道

| 時段 | 誰 | 做什麼 | 畫面 |
|---|---|---|---|
| 隨時 | 業務員 | 新增 / 修改潛在客戶,送出四眼 | `CLSM001` |
| 隨時 | 業務員 | 拜訪回來後 30 天內補拜訪單(含重點、推薦基金、需求、交通費) | `CLSM002` |
| 隨時 | 覆核者 | 驗證 / 覆核 / 退回 | `CLSM001` / `CLSM002` |
| 日終或需要時 | 作業人員 | 指定庫存日期跑重算,產生當日快照 | `CLSB001` |
| 需要時 | 作業人員 | 調整交通費上限與應拜訪次數 | `CLSB002` |
| 需要時 | 業務員 / 主管 | 印清冊、拜訪記錄、統計、交通費明細 | `CLSR001` / `CLSR002` |
| 需要時 | 直銷單位 | 查 CAS 那套拜訪單裡屬於直銷的部分 | `CLSI001` |

**沒有任何時序限制寫在程式裡**——`CLSB001` 的庫存日期只被限制不可大於今天(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33`),其餘全靠人工約定。

## 2. 資料模型

```text
[圖] CLS 自有 5 張表的主明細結構,以及三張不在母體的表與兩張同名不同主的 A 尾表
圖中文字:CLS 自有的 5 張實體表(全部有四眼欄位) / CLS001 / 潛在客戶 · PK PR_NO / CLS002 / 拜訪單 · PK CLL_NO / CLS003 / PK CLL_NO+TOPIC_CODE / CLS004 / PK CLL_NO+FUND_ID / CLS005 / PK CLL_NO+SEQ / 不在母體、但程式會讀的三張 / CLS001H / CLS001 的歷史快照 / CLSB001 / 批次執行日 EXEDATE / CLS012 / 交通費上限與次數門檻 / CLS001_V01 / CLSM001 查詢用的 view / 外部唯讀(CLS 從不寫入) / BMS001A / 受益人主檔 / COD009 / 員工 / SAL051 / 業務屬性 / OFD081A / 基金 / OFD068A / 銷售機構 / CRM002A / 可查範圍 / COD006A / 代碼 / 名字像 CLS 但主檔在 CAS 的兩張(§8) / CLS001A / 客戶拜訪單 · 主檔 CASM002 / CLS002A / 拜訪單續頁 · 明細於 CASM002 / CLSI001 只讀 CLS001A / USAGE = 2 那一半
```

*圖:圖 2 資料表關係。上排是 `CLSM002` 的一主三明細(靠 `CLL_NO` 串,不是外鍵,見 §2.1)。中排三張橘色是掃描母體沒列、但程式一定會讀的表。最底下是本模組最容易誤會的地方:`CLS001A` / `CLS002A` 的主人是 CAS 的 `CASM002`,CLS 只有 `CLSI001` 去讀它,而且只讀 `USAGE` = 2 的那一半。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

兩支 M 畫面的宣告,逐字抄自 PO 建構子:

| 畫面 | 主檔 | 明細 | 錨點 |
|---|---|---|---|
| `CLSM001` | `CLS001` | —(無明細) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:53` |
| `CLSM002` | `CLS002` | `CLS003`、`CLS004`、`CLS005` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:44-47` |

**五張表全部是 CLS 自己的,沒有一張借別人的**——這點跟 CAS 完全相反(`cas.md §0.2` 說 CAS 有一半的維護畫面開在別人的表上)。

三支非 M 畫面的 PO **都沒有 `xTableMapping`**:`CLSI001_PO` 的那行被註解掉(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:41`,而且註解裡寫的是 `OFD701`,跟 CLS 無關,與 `cas.md §5.1` 記的 `CASI001` 同一份樣板);`CLSB001_PO` / `CLSB002_PO` 連註解都沒有,直接自己 `new Database("TA", ...)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:32`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:33`)。這是 I / B 型的通則,見 `architecture.md §6.3`。

另外兩支 M 的 PO 都用 `AddNVarCharColumns` 逐欄宣告哪些是 `NVARCHAR2`(存中文):`CLS001` 六欄(`PR_NAME`、`CMD_PERSON`、`NEED_POC`、`MAIL_ADDR`、`MAIL_ADDR_E`、`CNT_PERSON`,`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:54-59`)、`CLS002` 四欄、`CLS003` 兩欄、`CLS005` 兩欄(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:48-55`)。

**`CLS004` 一欄都沒宣告**,它確實也沒有中文自由輸入欄(基金名稱由 `OFD081A` 帶入)。**加中文欄位時記得補這一行**,否則寫進去會變問號。

### 2.2 主鍵與四眼欄位

五張表**全部有完整的 15 個四眼 / 稽核欄**(`DATAID`、`STATUS`、`CREATEID`/`CREATEDATE`、`UPDATEID`/`UPDATEDATE`、`ENTRYID`/`ENTRYDATE`、`VERIFYID`/`VERIFYDATE`、`APPROVEID`/`APPROVEDATE`、`REJECTID`/`REJECTDATE`、`DATAFLAG`),語意見 `architecture.md §3.5`。

主鍵從 `App.config` 與 xsd 的 `msdata:PrimaryKey` 反推:

| 表 | 主鍵 | 依據 |
|---|---|---|
| `CLS001` | `PR_NO` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:15` 的 `pkey="PR_NO"` |
| `CLS002` | `CLL_NO` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:22` 的 `pkey="CLL_NO"` |
| `CLS003` | `CLL_NO` + `TOPIC_CODE` | `CLSM002p0` 存檔前用 `TOPIC_CODE` 做重複檢查;`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:53-60`。**假設**:xsd 的 `TOPIC_CODE` 不可空且是單內唯一 |
| `CLS004` | `CLL_NO` + `FUND_ID` | 同理,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:97-104` 用 `FUND_ID` 做重複檢查 |
| `CLS005` | `CLL_NO` + `SEQ` | `SEQ` 是 xsd 內唯一不可空的整數欄,而且 UI 完全不碰它——由框架或 DB 產生。**假設** |

**注意:`CLS003` / `CLS004` / `CLS005` 的重複檢查在用戶端做,不在 PO。**繞過畫面(例如兩個視窗同時開)沒有第二道防線。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

#### `CLS001` — 潛在客戶主檔(56 欄,`CLSM001` 主檔)

| 群 | 欄位 → 中文名 |
|---|---|
| 識別 | `PR_NO` 潛在客戶序號(PK) · `BF_NO` 戶號 · `ID_NO` 統編/ID · `PR_NAME` 客戶姓名 · `PR_TYPE` 客戶來源 · `BF_SOURCE_CODE` 潛在客戶來源代碼 |
| 歸屬 | `AGENT_CODE` 銷售機構 · `EMP_NO` 業務員員工代碼 · `EMP_NAME` 歸屬業務員 |
| 風險與合規 | `RISK` 風險屬性 · `CTL_TRADE` 交易列管 · `IN_DATE` KYC生效日 · `TERMINATE_DATE`(xsd 未填,畫面標題是 KYC到期日期)· `REJ_POST` 失聯戶 · `REJ_SELL_CHK` 拒絕行銷 |
| 投資決策 | `CMD_PERSON` 決策者 · `NEED_POC` 績效要求 · `NEED_SIZE` 規模要求(億)· `INV_LIMIT` 投資比例上限(%)· `STOP_GAIN` 停利點(%)· `STOP_LOSS` 停損點(%)· `CUS_LV` 客戶等級 |
| 關係與聯絡 | `REL_BF_NO` / `REL_NAME` 主要關係戶戶號 / 姓名 · `CNT_PERSON` 聯絡人 · `MAIL_ADDR` / `MAIL_ADDR_E` 通訊 / 英文地址 · `EMAIL` · `OF_TEL` / `HM_TEL` / `FAX_TEL` / `CELL_PHONE` 四組電話(各自另有 `_AREA` 區域碼與 `_EXT` 分機) |
| 庫存(批次寫,畫面唯讀) | `ON_AO_AUM` 歸屬AO境內庫存 · `ON_AUM` 境內庫存 · `OF_AO_AUM` 歸屬AO境外庫存 · `OF_AUM` 境外庫存 |
| 四眼 / 稽核 | 15 欄,見 §2.2 |

四個 AUM 欄只由批次寫(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:491-494` 只塞值不回收)。

#### `CLS002` — 拜訪單主檔(39 欄,`CLSM002` 主檔)

| 群 | 欄位 → 中文名 |
|---|---|
| 識別 | `CLL_NO` 拜訪單號(PK)· `PR_NO` 潛在客戶序號 |
| 客戶屬性快照 | `EMP_NO` / `EMP_NAME` · `BF_NO` 戶號 · `ID_NO` 統編/ID · `PR_NAME` 客戶姓名 · `CUS_LV` 客戶等級 · `RISK` 風險屬性 · `IN_DATE` / `TERMINATE_DATE` KYC 生效 / 到期日 · `CMD_PERSON` 決策者 |
| 拜訪內容 | `MAIN_PERSON` 主談者 · `INT_INV` 客戶投資意願(不可空)· `EST_CALL_DATE` / `EST_CALL_TYPE` 預計拜訪日期 / 方式 · `ACT_CALL_DATE` / `ACT_CALL_TYPE` 實際拜訪日期 / 方式 · `CLL_MEMO` 拜訪記錄 |
| 交通 | `DEPARTURE` 出發地 · `DESTINATION` 目的地 · `TRAFFIC` 交通工具 · `KM` 公里數 · `TRAN_FEE` 交通費 |
| 四眼 / 稽核 | 15 欄 |

**「客戶屬性快照」那一群在畫面上全部唯讀**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:426-435`),值是查 `CLS001` 帶進來的(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:192-212`)。也就是**同一份客戶屬性同時存在 `CLS001` 與 `CLS002`,拜訪單存的是當下的快照,客戶之後改了不會回頭同步**。

#### 三張明細(欄位全部含 `CLL_NO` + 15 個四眼欄)

| 表 | 業務欄位 → 中文名 |
|---|---|
| `CLS003`(20 欄) | `TOPIC_CODE` 拜訪重點(`COD006A` 的 `CODE_SORT` = `D2`)· `TOPIC_OTH` 拜訪重點-其它(代碼 `99` 才開放)· `INTER_SUP` 內部支援(下拉 `603`)· `INTER_SUP_OTH` 內部支援-其他(代碼 `4` 才開放) |
| `CLS004`(22 欄) | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `FUND_CURRENCY` 計價幣別(兩者由 `OFD081A` 帶入)· `ALLOT_AMT_ORG` / `ALLOT_AMT` 預計申購金額(原幣 / 台幣)· `ALLOT_DATE` 預計申購日 |
| `CLS005`(19 欄) | `SEQ` 序號 · `COMPETITOR` 競爭對手(不可空)· `MEMO` 需求說明(不可空) |

#### 查詢結果集形狀(不是實體表)

`CLSM001Model.xsd` 除了 `CLS001` 之外還宣告五張只在畫面上顯示的表,對應維護頁的五個頁籤:

| DataTable | 內容 | 由誰填 |
|---|---|---|
| `CLS002`(4 欄) | 該客戶的拜訪紀錄一覽 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:147-155` |
| `tab2`(10 欄) | 推薦基金彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:309-331` |
| `tab3`(7 欄) | 新產品需求彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:356-372` |
| `tab4`(7 欄) | 內部支援彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:397-417` |
| `tab5`(7 欄) | 拜訪重點次數統計 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:443-465` |
| `CLS0021`(4 欄) | **零引用**,全庫 grep 不到任何 `.cs` 用它 | 見附錄 E |

報表側的結果集:`CLSR001Model.xsd` 有 `T1` / `T2` / `T3` / `CRM002A`;`CLSR002Model.xsd` 有 `T0` / `T1` / `T3`。這些是「查詢結果集形狀」不是實體表(`architecture.md §5.5`)。

### 2.4 與其他模組共用的表

掃描器對本模組的結論是「**無跨模組共用表**」——`CLS001`~`CLS005` 沒有被任何非 CLS 的畫面當主檔或明細。這個結論是對的,但**不代表改這五張表沒有跨模組影響**,原因見 §8。

反過來,CLS **讀**了很多別人的表:

| 表 | 主人(推測) | CLS 怎麼用 | 錨點 |
|---|---|---|---|
| `BMS001A` | BMS | 有戶號時用它蓋掉 `CLS001` 的姓名 / 統編;查統編是否已開戶 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:263`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:207-208` |
| `COD009` | COD | 員工姓名、到職日、離職日、`UID_CODE` ↔ `EMP_NO` 換算 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:191-192` |
| `SAL051` / `V_SAL051` | 不明 | 業務屬性 `SAL_CD` 與部門 `SAL_DEPT_NO`(決定能不能建檔) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:491`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:57` |
| `CRM002A` | CRM | 「這個員編可以查哪些機構 / 哪些員編」 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:121` |
| `CRM003A` / `CAS004A` / `CLS001A` | CRM / CAS | 只有 `CLSI001` 讀 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106-112` |
| `CRM004` | CRM | 拜訪次數門檻(`NEED_CNT` / `VISIT_CNT` / `CALL_CNT`) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1289` |
| `OFD068A` · `OFD081A` / `OFD081` · `OFD300` | OFD | 銷售機構簡稱 · 基金名稱與幣別與 `PROF_TYPE` · 匯率 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:199-201`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:129-130`、`:318` |
| `OFD115A` · `OFD123A` · `OFD017A_V01` | OFD | 交易列管期間 · KYC 到期日 · 客戶分類(**join 進來但輸出欄位一個都沒用到**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:259-266`、`:270-272` |
| `OFD221A_V01` / `OFD221` / `OFD251A` / `OFD251` / `OFD252` / `OFD253` / `OFD254` | OFD | 第 6 種報表算申購 / 贖回金額 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:883-943` |
| `OFD302` / `OFD302A` / `OFD306` / `OFD306A` | OFD | 第 8 種報表算庫存 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1427` |
| `COD006A` / `CTL014` / `AA_USER` | COD / CTL / 平台 | 代碼說明 · `USERID` → 中文姓名 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:456-458`、`:409-411`、`:149` |

**這 20 幾張表 CLS 一張都不寫**(唯一的例外是 `CLS012`,那是 CLS 自己的,見 §6.2)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`CLS001`~`CLS005` 的 `STATUS` 由四眼引擎寫,值域是 `EVAStatusCode` 那 12 個常數(`architecture.md §3.10`),CLS 自己的程式**完全沒有比對過 `STATUS`**——全庫 grep `STATUS` 在 CLS 五支 PO 內只出現在 xsd 欄位與 `CLSI001` 的 `DefaultValue`。

唯一的字面值是 `CLSI001_PO` 給查詢結果集塞的 `"301"`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:360`)。這跟 `cas.md §2.5` 記的 `CASB001` 寫 `'301'` 是同一個值,可以互相佐證 `STATUS` 是 3 碼字串。**但 `CLSI001` 是唯讀查詢,這行 `DefaultValue` 只在「新增一列而沒給值」時生效,對查詢沒有作用**,是從 `CASB001` 樣板複製過來的死碼(§5.4)。

#### 本模組自己判斷的旗標值

| 欄位 | 值 | 語意(來源) | 錨點 |
|---|---|---|---|
| `SAL_CD` | `A` 部門主管 / `B` 組長 / `C` 業務員 / `D` 助理 / `E` 外交割人員 / `F` 其他 | **XML 註解直接寫出全部六個值**,是本模組唯一有完整值域文件的代碼 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479` |
| `ACT_CALL_TYPE` / `EST_CALL_TYPE` | `1` 親訪 / `2` 電訪 / `3` E-mail | `1` = 親訪由 UI 判斷式反推(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:95`);`2` / `3` 由 `tab5` 的欄位中文名「親訪次數 / 電訪次數 / E-mail次數」對應 `DECODE(ACT_CALL_TYPE, 1/2/3)` 反推(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:447-449`) |  |
| `TRAFFIC` | `2` = 自行開車(其餘不明) | 只有 `2` 會開放輸入公里數 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:713` |
| `TOPIC_CODE` | `99` = 其他 | 選 `99` 才開放「拜訪重點-其他」文字欄 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:94` |
| `INTER_SUP` | `4` = 其他 | 選 `4` 才開放「內部支援-其他」文字欄 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:73` |
| `AUM`(查詢條件,非欄位) | `1` 有庫存 / `2` 無庫存 | 轉成 `ON_AO_AUM + OF_AO_AUM > 0` 或 `= 0` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182` |
| `USAGE`(`CLS001A` 的欄) | `2` = 直銷(CLS)、`3` = 代銷(CAS) | `CLSI001` 硬寫 `'2'`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132`),`CASI001` 硬寫 `'3'`(`cas.md §5.3`)。**假設**:兩個值就是這兩種通路 |  |
| `INT_INV` | `Y` / `N` | 下拉來源是 `YesNoDataSrc` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:306-308` |
| `BF_COUNTRY_X` | `01` = 本國(其餘視為外國) | 只用在報表的姓名遮罩長度 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1489` |

#### 下拉代碼分類碼

CLS 用到 10 組,分類碼**全部寫死在程式裡**(`601` 客戶來源 · `602` 客戶等級 · `603` 內部支援 · `604` 庫存情況 · `605` 交通工具 · `606` 基金範圍 · `447` 拜訪方式 · `448` 往返 · `404` 風險屬性 · `D2` 拜訪重點),逐一對應見附錄 C.3。

**同一組 `447` 在 `CLSI001` 用了兩套下拉實作**:條件區用 `GetDropDownDataSrc`、grid 用 `GetDropDown9iDataSrc`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:284` 對照 `:287-288`)。這與 `architecture.md §2.7` 記的 `CASM001` 是同一個現象。

## 3. 畫面清冊

七支畫面,五支彈出視窗。**七支全部住在 `Dev/ATLAS.CLS/SOURCE/`(大寫 SOURCE),兩支 R 例外住在 `Dev/ATLAS.CLS.Report/Source/`(一般大小寫)。**

### 3.1 維護 M

| 代號 | 中文名(推測) | 六層 | 主表 | 明細 | 彈出視窗 |
|---|---|---|---|---|---|
| `CLSM001` | 潛在客戶維護 | 齊 | `CLS001` | — | `CLSM001p0`「受益人基本資料」(**目前叫不到,見附錄 E**) |
| `CLSM002` | 客戶拜訪單維護 | 齊 | `CLS002` | `CLS003` `CLS004` `CLS005` | `CLSM001p0`、`CLSM002p0`「目的/支援」、`CLSM002p1`「推薦基金」、`CLSM002p2`「批次新增拜訪重點」 |

### 3.2 查詢 I

| 代號 | 中文名 | 六層 | 主表 | 彈出視窗 |
|---|---|---|---|---|
| `CLSI001` | 直銷客戶查詢作業(**視窗標題直接寫在 `CLSI001p0`**) | 齊 | `CLS001A`〔共用 · 主人是 `CASM002`〕 | `CLSI001p0` 同名明細視窗 |

### 3.3 批次 B

| 代號 | 中文名(推測) | 六層 | 寫哪張表 | Service |
|---|---|---|---|---|
| `CLSB001` | 庫存重算與快照 | **齊,但 Model / View 是空的 DataSet** | `CLS001` 的 AUM 欄、`CLS001H`、`CLSB001`(由 SP 寫) | 無 |
| `CLSB002` | 交通費與拜訪次數門檻維護 | **缺 model / view** | `CLS012` | 無 |

#### `CLSB002` 的「六層不齊」是真缺,不是命名

掃描器對 `CLSB002` 回報「缺 model view」。查下去**確實沒有 `CLSB002Model.xsd` / `CLSB002View.xsd`,也沒有 `_9i` 版本**(`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/` 底下只有 `CLSB001Model.xsd`、`CLSI001Model.xsd`、`CLSM001Model.xsd`、`CLSM002Model.xsd` 四支)。這與 `architecture.md 附錄 D` 記的 `_9i` 假警報**不是同一回事**。

真正的原因是它**刻意借用別人的型別**,三層各借一個:

| 層 | 用的型別 | 錨點 |
|---|---|---|
| UI | `new CLSB001ViewVDB()` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:43` |
| Control | `Execute(CLSB001ViewVDB)` / `Query(CLSB001ViewVDB)`,泛型參數 `CLSB001ModelVDB` | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs:37`、`:132`、`:165` |
| PO | `model as BasicModelVDB`,連 CLS 的型別都不用 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:49`、`:180` |

而 `CLSB001Model.xsd` / `CLSB001View.xsd` 本身是**零張表的空 DataSet**(整份只有一個 `<xs:choice>` 空節點,`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSB001Model.xsd:11-15`)。所以 `CLSB002` 借的其實是「一個什麼都沒有的殼」——它的資料全靠 `Util.Parameters` 進、`Util.Result` 出(§6.2)。

**結論:`CLSB001` 的 model / view 存在但是空的;`CLSB002` 的 model / view 真的不存在,靠借 `CLSB001` 的空殼運作。兩者都不是命名問題,而是「B 型畫面根本不需要 typed DataSet」這條通則的兩種表現**(`architecture.md §6.6`)。

### 3.4 報表 R

| 代號 | 中文名 | 六層(七層) | 取數 | rpt 數 |
|---|---|---|---|---|
| `CLSR001` | 業務員客戶清冊 / 客戶來源清冊 | 齊(`.Report` 七層) | SP `S_TA_CLSR001_GET_<值>` | 9 支 |
| `CLSR002` | 客戶拜訪記錄與統計 | 齊(`.Report` 七層) | 自組 SQL(1,535 行 PO) | 13 支 |

### 3.5 一眼看出差別的五件事

| # | 事實 | 為什麼要記住 |
|---|---|---|
| 1 | 只有兩支 M 有四眼;I / B / R 全部繞過 `BaseEVADaoPO` 自建 `Database` | 這三型不受四眼、交易、連線池治理(`architecture.md §6.7`) |
| 2 | `CLSI001` 查的是**別的模組的表** | 改 `CASM002` 的欄位會打到 `CLSI001`(§8) |
| 3 | 兩支 B 都沒有 WindowsService,也沒有排程 | 全靠人工按鍵;`CLSB001` 沒跑報表就空白(§1.4) |
| 4 | 22 支 rpt 集中在兩支 R 畫面,比例是全庫最高的之一 | 一支畫面十幾種版型,選項與版型的對應只寫在 UI 的兩個 `Dictionary`(§7.1) |
| 5 | `DB/` 底下**零**支 CLS 的 SP / Function / Trigger / View | 所有 SP、`CLS001_V01`、`F_TA_GET_DIRECT_EMPS` 都在版控外(附錄 B) |

## 4. 維護畫面(M)— 一支一節

```text
[圖] 兩支維護畫面從進畫面、UI 檢核、PO 取號到四眼各階段的卡控順序
圖中文字:① 進維護頁之前(兩支 M 共用同一段) / SetEMP_NO / 從 COD009 換員工代碼 / GetSAL_CD / SAL_CD 不是 A/B/C 就鎖三個鈕 / CLSR001 GetInitData / 拿可查機構與員編清單 / Sales 清單 / 空 = 不過濾 / ② 存檔前 UI 檢核(BeforeAdd / BeforeModify → DoValidate) / CLSM001 / 統編與姓名擇一必填 / CLSM002 / 親訪要填目的地與交通工具 / CLSM002 / 實際拜訪日不可未來 / 逾 30 天 / 明細至少一筆 / CLS003 / ③ PO 事件(BeforeAdd) / CLSM001 / GetPR_NO2 取號 · 重號重取 / CLSM002 / GetCALL_RPT_NO 取號 / 把 CLL_NO 灌進所有明細 / 一次寫回四張表 / 無次數上限 / do-while 可能卡死 / ④ 四眼(框架) → ⑤ After 事件 / Entry / 輸入 / Verify / 驗證 / Approve / 覆核 / CLSM002 八個 After / 只寫跳號註記 / CLSM001 沒掛 / 註記只在 M002
```

*圖:圖 3 兩支 M 畫面的四眼與卡控順序。①②在用戶端、③⑤在伺服器、④在框架。橘色虛框是三個要記住的地方:建檔權限由 `SAL051` 決定(§4.1)、拜訪日的 30 天回補期限(§4.2)、以及取號重試沒有次數上限(附錄 E)。*

兩支 M 共用一段「進畫面決定能不能改」的程式(§4.1 的權限段),然後各走各的。

### 4.1 `CLSM001` — 潛在客戶維護

#### 用途(推測)

業務員把還沒開戶(或已開戶但要列入追蹤)的客戶登錄成一筆潛在客戶,填來源、聯絡方式、投資決策條件與客戶等級;送四眼後成為 `CLSM002` 拜訪單的可選對象。**畫面有兩個頁籤(查詢 + 維護)**,維護頁再分五個子頁籤(基本資料 / 推薦基金 / 新產品需求 / 內部支援 / 拜訪重點),後四個是唯讀統計。

#### 進畫面時就決定的三件事

進 `FormInitial` 依序做三件事:(1) 用登入者的 `UserID` 去 `COD009` 換 `EMP_NO` 存進 `EMPNO`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:135-145`、`:277`);(2) 用 `EMPNO` 查 `SAL051` 的業務屬性,不是 `A`/`B`/`C` 就把 `blnCanKeyIn` 設 false(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:281-282` 配 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:482-521`);(3) 呼叫 `CLSR001_Pxy.GetInitData` 拿可查機構 / 員編清單設成下拉的 `Filter`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:289-327`)。

第 2 點的 SQL 值得看一眼:它取的是**部門代碼長度剛好 5 碼**的那些 `SAL051` 列,再用 `MAX(...) KEEP(DENSE_RANK FIRST ORDER BY SAL_CD DESC)` 取 `SAL_CD`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:490-494`)。`LENGTH(SAL_DEPT_NO) = 5` 是**寫死的〔客戶特定〕**,而 `DESC` 取的是字母**最大**的那個(`F` > `C` > `A`),也就是**最沒有權限的那個**;判斷式再用 `Contains` 比對 `A`/`B`/`C`(`:507`)。所以身兼 `C` 業務員與 `F` 其他的人會被判成 `F`,**不能建檔**。這是不是本意,程式裡看不出來。

#### 必填與存檔前檢核

`DoValidate()` 只有兩層(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:120-130`):

| 順序 | 檢核 | 結果 |
|---|---|---|
| 1 | `validatorManager1` 宣告式必填(哪些欄由 Designer 決定) | 阻擋 |
| 2 | 「統編/ID 及客戶姓名 必須擇一填寫」 | 阻擋 |

另外一道在欄位離開焦點時跑:`umskID_NO_Validating` 會拿統編去 `GetBMS001A` 問三件事(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:720-735` 配 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:257-297`):

| 情況 | PO 回什麼 | 使用者看到 |
|---|---|---|
| 這個統編已在 `CLS001` 有資料,而且是**自己**建的 | `AddResultRow(false, 1, "您已維護過此客戶")` | 阻擋 |
| 這個統編已在 `CLS001` 有資料,但是**別人**建的 | `AddResultRow(false, 1, "無維護此客戶權限")` | 阻擋 |
| 統編在 `BMS001A` 查得到戶號 | 把戶號塞進 `tab2`,回成功 | 自動把戶號填進畫面(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:155-162`) |

**注意這裡有個被停用的第四種情況**:原本「有多筆受益人時彈 `CLSM001p0` 讓使用者挑」以及「統編/ID 已存在,不可建為潛在客戶」兩段都被整段註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197`)。結果是 `HasData` 永遠是 false,底下那行 `e.Cancel = IsErr || (HasData && unumBF_NO.Enabled)`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:734`)後半段永遠不成立——註解寫的「不允許有 id 開戶卻沒帶入」這條規則**實際上沒有在擋**。同一支 PO 裡的 `ChkID`(統編重複檢查)也被整塊 `/* */` 註解(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:218-252`)。

還有兩個 `Validating` 整段被註解:戶號(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:707-719`)與客戶姓名(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:736-745`)。

#### 有戶號與沒戶號是兩種不同的資料

`GetData()`(按新增 / 修改前把畫面塞回 row)依戶號分成兩條路(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:51-92`):

| 情況 | 做什麼 |
|---|---|
| **沒填戶號** | 姓名、來源、聯絡人、地址、E-mail、四組電話全部從畫面收 |
| **有填戶號** | 上面那 15 個欄位**全部清成空字串**,改由查詢時 join `BMS001A` 帶出來 |

也就是說**同一張表的同一組欄位,對「已開戶」的客戶是刻意留白的**。看到 `CLS001.PR_NAME` 是空字串不代表資料有問題,要去看 `BF_NO`。

另外,從「沒戶號」變成「有戶號」時(補戶號),UI 會塞一個 `COM` 參數進 `Util.Parameters`,註解寫「補戶號要重算 AUM 和等級」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75`)。**但 PO 端接這個參數的 `AfterAdd` 已整段註解**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:99-123`),所以這個參數現在**送出去沒有人接**——補完戶號的庫存與等級要等下一次 `CLSB001` 才會更新。

#### 查詢條件與「看得到誰」

`BeforeSearchButtonClicked` 收 11 個條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:517-543`),其中三個會影響可見範圍:

| 條件 | 行為 | 錨點 |
|---|---|---|
| 有選業務員 | `EMP_NO = <值>` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:522-523` |
| 沒選業務員但 `Sales` 清單不空 | `EMP_NO IN (<清單>)` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525` |
| 沒選業務員而且 `Sales` 是空的 | **不加任何員編條件 → 看得到全部** | 同上的 else 不存在 |

PO 端把 `IN` 那條改寫成 `AND (C.LEAVE_DATE IS NOT NULL OR <員編條件> OR CLS001.EMP_NO IS NULL)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:172-173`)——**離職者的客戶與「公單」(`EMP_NO` 為 null)一律看得到**。單選業務員時則走另一段字串串接(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:206-213`),邏輯相同但寫法不同,而且是把值直接串進 SQL(附錄 E)。

「庫存情況」那個條件是全模組唯一會**靜默濾掉資料**的地方:

```
選「有庫存」→ AND ON_AO_AUM + OF_AO_AUM > 0
選「無庫存」→ AND ON_AO_AUM + OF_AO_AUM = 0
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182`)。這兩欄可空,Oracle 裡 `NULL + 0` 還是 `NULL`,`NULL > 0` 與 `NULL = 0` 都是 UNKNOWN,**所以還沒跑過 `CLSB001` 的新客戶無論選哪一個都查不到**,而且沒有提示。詳見附錄 E。

#### 「公單」規則

查到資料進維護頁時,`EMP_NO` 是不是 null 決定兩個鈕(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:426-429`):

```
ButtonDeleteEnable = 明細筆數 == 0 && EMP_NO 不為 null
ButtonModifyEnable = EMP_NO 不為 null
```

註解直接寫「只要有一筆明細就不可刪或公單不可刪除」「公單不可修改」。**「公單」= `EMP_NO` 為 null 的客戶**,所有人都查得到、誰都不能改。這條規則只存在於這兩行,沒有任何 UI 提示。

#### 四眼各階段附加動作

| 事件 | 內容 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetPR_NO2()` 取潛在客戶序號,重號就重取 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:85-89` |
| `BeforeSelect` / `BeforeGetToDoData` / `BeforeGetMaintainData` | 三個都改寫主檔 SQL(同一支 `BuildMasterSQLString`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:126-142` |
| `AfterGetMaintainData` | 另外撈該客戶的拜訪紀錄填進 `CLS002` 頁籤 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:144-156` |
| `AfterAdd` / `AfterUpdate` | **整段被註解,實際什麼都不做** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:92-124` |
| `Verify` / `Approve` / `Reject` / `Delete` | **完全沒掛**——`CLSM001` 沒有跳號註記 | 對照 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:58-65` |

`CLSM001_Ctl.Add()` 覆寫成功訊息為「新增成功,潛在客戶序號:`<PR_NO>`」(`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM001_Ctl.cs:62-65`),**沒有檢查 `Result` 陣列長度**(與 `cas.md 附錄 E` 記的 `CASM001_Ctl` 同一個問題)。

UI 端**仍然掛著跳號一覽表的三個事件**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:569-583`),但 PO 端沒有 `SrNoCommentProcessor.AddCommentHistory`,所以註記只讀不寫。

#### 跨表更新

**沒有。**`CLSM001` 只寫 `CLS001` 一張表。五個頁籤的資料全部是 `SELECT`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:304-476`),而且是在使用者切到該頁籤時才去撈,撈過就不再撈(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:673-706`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進維護頁 | `SAL051` 業務屬性不是 `A`/`B`/`C` | 永遠判斷 | 阻擋(鎖新增 / 修改 / 刪除三鈕 + 訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:369-376`、`:406-413` |
| 進維護頁 | 取 `SAL_CD` 出錯 | SQL 例外 | 警示(顯示例外訊息,**不擋**) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:284-287` |
| 進維護頁 | `EMP_NO` 為 null(公單) | 查到的是公單 | 阻擋(修改與刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:427-429` |
| 進維護頁 | 已有拜訪明細 | `ugrdCLS002` 有列 | 阻擋(刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:427` |
| 選業務員時 | 選到不在 `Sales` 清單且在職的人 | `Sales` 不空 | 阻擋(訊息「不可查詢此業務員」+ 清空) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:620-630` |
| 選業務員前 | 沒先填銷售機構 | — | 阻擋(訊息「請先輸入 '銷售機構'」) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:611-618` |
| 統編離開焦點 | 統編已被自己維護過 | `CLS001` 查得到且員編相同 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:273-274` |
| 統編離開焦點 | 統編被別人維護過 | `CLS001` 查得到但員編不同 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:275-276` |
| 統編離開焦點 | 有開戶卻沒帶入戶號 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197` |
| 存檔前 | 統編與姓名都空白 | 兩者皆空 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:125-126` |
| 查詢前 | 至少 3 個查詢條件 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:547-551` |
| 查詢時 | 庫存情況 | 選了有 / 無庫存 | 過濾(無提示,**AUM 為 NULL 的一律被濾掉**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182` |
| 查詢時 | 可查員編清單 | `Sales` 不空 | 過濾(無提示;離職者與公單不受限) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:172-173` |
| 查詢時 | `Sales` 是空的 | 取不到可查清單 | **靜默放大到全部資料** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525` |
| 取號時 | 序號重複 | `IsExistByData` 為真 | 記錄不擋(重取,**無次數上限**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:85-89` |

### 4.2 `CLSM002` — 客戶拜訪單維護

#### 用途(推測)

業務員每拜訪一次客戶就開一張拜訪單:記錄預計與實際的日期與方式、主談者、客戶投資意願、交通資訊與費用,以及三組明細(拜訪重點與需要的內部支援、當場推薦了哪幾檔基金與預計申購金額、客戶提出的新產品需求與競爭對手)。

#### 客戶怎麼帶進來

四個欄位(統編、戶號、潛在客戶序號、客戶姓名)任一個離開焦點,都會用同一支 `GetCLS001` 去查 `CLS001`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:660-683`):

| 查到幾筆 | 行為 |
|---|---|
| 1 筆 | 直接把客戶屬性塞進畫面並鎖住那四個欄位(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:192-212`) |
| 多筆 | 彈 `CLSM001p0` 讓使用者挑(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:181-186`)——**這是 `CLSM001p0` 全模組唯一還活著的呼叫點** |
| 0 筆 | `AddResultRow(true, 0, "查無資料")` → 訊息 + `e.Cancel = true` 留在原欄位 |

`GetCLS001` 一律附帶 `EMP_NO = <登入者員編>`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:158`),所以**只能對自己的潛在客戶開拜訪單**。

#### 必填與存檔前檢核

`DoValidate()` 一共七條(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:87-136`):

| # | 檢核 | 訊息 |
|---|---|---|
| 1 | 宣告式必填(含公里數,僅在啟用時) | 由 Designer 決定 |
| 2 | 實際拜訪方式 = 親訪(`1`)時「目的地」必填 | 「實際行程拜訪方式為親訪時「目的地」 為必填欄位」 |
| 3 | 同上,「交通工具」必填 | 「…「交通工具」 為必填欄位」 |
| 4 | 實際拜訪日期 ≥ 預計拜訪日期 | 「實際拜訪日期 必須 >= 預計拜訪日期」 |
| 5 | 實際拜訪日期不可大於 DB 系統日 | 「提醒: 無法預先維護客戶拜訪紀錄」 |
| 6 | 實際拜訪日期不可早於系統日 -30 天(含假日) | 「提醒: 已逾維護期限, 無法再維護客戶拜訪紀錄」 |
| 7 | `CLS003` 至少一筆;`CLS005` 的需求說明不可空白 | 「目的/支援 至少要有一筆資料」「需求說明 為必填欄位」 |

第 5、6 條是本模組最實質的業務規則:**拜訪單不能預先開,也不能補超過 30 天**。`-30` 寫死在程式裡(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:117`)〔客戶特定〕,而且**同一組判斷在 `udatACT_CALL_DATE_Validating` 又寫了一次**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738`),那一份只跳訊息、沒有 `e.Cancel`,屬於提早提醒;真正擋下來的是 `DoValidate`。**兩份判斷必須一起改**。

第 8 條原本有:「拜訪記錄必須再補充」(要求 `CLL_MEMO` 長度大於自動帶入的拜訪重點文字),已被註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134`),連帶產生那段文字的 `UpdMemo()` 整支方法內容也全被註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:141-149`)。

#### 交通費怎麼算

| 步驟 | 規則 | 錨點 |
|---|---|---|
| 1 | 實際拜訪方式選「親訪」才開放出發地 / 目的地 / 交通工具;出發地預設「公司」 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:645-658` |
| 2 | 交通工具選「自行開車」(`2`)才開放公里數;選任何交通工具都開放交通費 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:709-715` |
| 3 | **公里數 × 6 = 交通費**,自動帶出且可覆寫 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:717-723` |

每公里 6 元是**寫死的整數〔客戶特定〕**,而且**上限 `TRFF_LMT` 在這裡完全沒有被檢查**——`CLS012` 的上限值只在 `CLSR002` 的交通費報表被當成一欄印出來(§7.3),畫面不擋。

#### 三組明細怎麼進來

| 明細 | 進入方式 | 重複檢查 | 錨點 |
|---|---|---|---|
| `CLS003` 拜訪重點 | 雙擊 grid 新增列彈 `CLSM002p0`;或按鈕彈 `CLSM002p2` 一次勾選多筆 | `TOPIC_CODE` 不可重覆 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:586-605`、`:700-707`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:53-60` |
| `CLS004` 推薦基金 | 雙擊 grid 彈 `CLSM002p1` | `FUND_ID` 不可重覆 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:612-643`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:97-104` |
| `CLS005` 新產品需求 | grid 直接編輯(`GridLayoutADU`) | 無 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:285-286` |

**`CLS003` 的「修改既有列」被停用**:雙擊既有列的那段 `new CLSM002p0(dt, row)` 整行註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:602-603`),所以拜訪重點**只能新增與刪除,不能改**,而且雙擊沒有任何反應。

`CLSM002p1` 的推薦基金另有兩條規則:非台幣時呼叫 `CLSM002_PO.GetEX_RATE` 取 `OFD300` 最新匯率,`原幣 × 匯率` 四捨五入成台幣(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:52-77`、`:86-90`);預計申購日必須 ≥ 實際拜訪日期,而且必須是該基金的營業日(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:131-155`)。

匯率那段有個要注意的寫法:`Convert.ToDecimal(vdb.Util.Result[0].ReturnMessage.PadLeft(1, '1'))`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:65`)。`PadLeft(1, '1')` 只有在字串長度為 0 時才會補——也就是**查不到匯率時匯率靜默變成 1**,台幣金額 = 原幣金額,沒有任何提示。

#### 四眼各階段附加動作

`CLSM002_PO` 掛了 12 個事件,是全模組最完整的一支:

| 事件 | 內容 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetCALL_RPT_NO()` 取拜訪單號(重號重取),然後把 `CLL_NO` 灌進 `model.DataEntity` 的**每一張表的每一列** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:96-104` |
| `BeforeSelect` / `BeforeGetToDoData` | 改寫主檔 SQL | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:109-112`、`:138-141` |
| `BeforeGetMaintainData` | 主檔改寫 SQL;`CLS004` 另外 join `OFD081A` 補基金名稱與幣別 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:115-136` |
| `AfterGetMaintainData` | `SrNoCommentProcessor.GetCommentHistory` 讀跳號註記 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:335-340` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterReject` / `AfterResend` | 七個都只做一件事:`SrNoCommentProcessor.AddCommentHistory(<對應 EVAType>, SrNo.AllotNoForNfd, …)`,失敗就 `throw new ApplicationException("")` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:342-396` |

**七個 `throw` 的訊息全是空字串**,與 `cas.md 附錄 E` 記的 `CASM001_PO` 同一個問題(附錄 E)。

另外,四眼的按鈕在進維護頁時還會再收一次(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:464-466`):

```
ButtonDeleteEnable &= row.EMP_NO == EMPNO && row.CREATEID == this.UserID
ButtonModifyEnable &= 同上
```

也就是**只有「歸屬業務員是我」而且「建檔者也是我」才能改或刪**。`&=` 代表在框架已判定的權限上再收一層。

#### 查詢與「看得到誰」

`CLSM002` 的主檔 SQL 是全模組最複雜的一段(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:149-304`),三層 CTE:

| CTE | 做什麼 |
|---|---|
| `ISHIS` | 從 `CLSB001` 取「不晚於查詢迄日的最後一次批次日」`QDATE` 與「全部批次的最後一日」`MAXDATE` |
| `CLS` | `QDATE < MAXDATE` 時讀 `CLS001H` 快照,`QDATE = MAXDATE` 時讀 `CLS001` 現值,兩段 `UNION ALL` |
| `MYCLS001` | 再 join `BMS001A`,把交易列管(`OFD115A`)與 KYC 到期日(`OFD123A`)算出來 |

最後一段的 `WHERE` 裡有一條**硬條件**:

```
AND CLS002.CREATEID = :CREATEID          -- CREATEID 來自 PermissionInfo 的 UserID
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292`、`:300-301`)。**不管畫面上選了哪個業務員,查出來的永遠只有登入者自己建的拜訪單。**這條不在畫面上、沒有提示,而且與「選業務員」那個條件並存——選了別人只會查到 0 筆。

`MYCLS001` 那層還有一條:`WHERE CUS_LV IS NOT NULL`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:273`)。**客戶等級還沒算出來(沒跑過批次)的客戶,它的拜訪單查不到。**

三個明細條件(基金、拜訪重點、需求說明)是用 `CLL_NO IN (SELECT …)` 子查詢做的(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:153-164`),不會讓主檔重複。

#### 跨表更新

**四張表一起寫,沒有其他跨表動作。**`CLSM002` 不碰 `CLS001`(只讀),也不碰任何外部表。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進維護頁 | `SAL051` 業務屬性不是 `A`/`B`/`C` | 永遠判斷 | 阻擋(鎖三鈕 + 訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:375-382`、`:408-415` |
| 進維護頁 | 歸屬業務員或建檔者不是自己 | 查到別人的單 | 阻擋(修改 / 刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:464-466` |
| 客戶欄離開焦點 | 該客戶不在自己的 `CLS001` 名單 | 查 0 筆 | 阻擋(訊息「查無資料」+ 停在原欄位) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:160-161` |
| 客戶欄離開焦點 | 查到多筆 | — | 詢問(彈 `CLSM001p0` 讓使用者挑) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:179-187` |
| 實際拜訪日離開焦點 | 未來日 / 逾 30 天 | — | 警示(**只跳訊息,不擋**) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738` |
| 存檔前 | 親訪但目的地空白 | `ACT_CALL_TYPE` = `1` | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:95-98` |
| 存檔前 | 親訪但交通工具空白 | `ACT_CALL_TYPE` = `1` | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:101-104` |
| 存檔前 | 實際拜訪日 < 預計拜訪日 | 有填實際日 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:106-110` |
| 存檔前 | 實際拜訪日 > DB 系統日 | 永遠判斷 | 阻擋〔客戶特定〕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:113-115` |
| 存檔前 | 實際拜訪日 < 系統日 - 30 天 | 永遠判斷 | 阻擋〔客戶特定〕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:117-120` |
| 存檔前 | `CLS003` 一筆都沒有 | — | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:122-123` |
| 存檔前 | `CLS005` 的需求說明空白 | 有 `CLS005` 列 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:125-132` |
| 存檔前 | 拜訪記錄必須再補充 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134` |
| 明細彈窗 | 拜訪重點重覆 | 同 `TOPIC_CODE` 已存在 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:56-60` |
| 明細彈窗 | 推薦基金重覆 | 同 `FUND_ID` 已存在 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:100-104` |
| 明細彈窗 | 預計申購日 < 實際拜訪日 | 有填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:140-143` |
| 明細彈窗 | 預計申購日不是基金營業日 | 有填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:145-148` |
| 明細彈窗 | 未開推薦基金明細前先填實際拜訪日 | 實際拜訪日空白 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:614-620` |
| 明細彈窗 | 批次新增拜訪重點時一個都沒勾 | — | **無回饋**(視窗不關也不提示,見附錄 E) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:101-107` |
| 查詢前 | 實際拜訪日起迄只填一邊 | XOR 成立 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:316-320` |
| 查詢前 | 起 > 迄 | 兩邊都填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:321-325` |
| 查詢前 | 至少 3 個查詢條件 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:359-363` |
| 查詢時 | 只看自己建的單 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292` |
| 查詢時 | 客戶等級為 null | 客戶還沒被批次算過 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:273` |
| 查詢時 | 沒有任何批次紀錄 | `CLSB001` 表是空的 | 過濾(無提示,**整頁空白**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-179` |
| 取號時 | 單號重複 | `IsExistByData` 為真 | 記錄不擋(重取,**無次數上限**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:96-99` |

## 5. 查詢畫面(I)

本模組只有一支 `CLSI001`「直銷客戶查詢作業」。

### 5.1 結構:查的是別人的表

| 面向 | `CLSI001` | 對照 `CLSM001` |
|---|---|---|
| 介面 | `ICLSI001_PO`,不繼承任何東西 | `ICLSM001_PO : IEvaDataAccess` |
| 類別 | `: ICLSI001_PO`,沒有基底 | `: BaseEVADaoPO, ICLSM001_PO` |
| 連線 | 自己 `new Database("TA")` 與 `new Database("SWProduct")` | 由 `BaseEVADaoPO` 管 |
| 主檔宣告 | **整行被註解**,而且註解裡寫的是 `OFD701` | `xTableMapping("CLS001", "CLS001")` |
| Ctl 的 `InitializeVDBTypes()` | **完全沒有** | 有 |
| 查的表 | **`CLS001A`〔共用 · 主人是 `CASM002`〕** | `CLS001_V01` |

錨點:`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:21`、`:33`、`:35-36`、`:41`;`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:26-29`。

**這支畫面與 `CASI001` 是同一份樣板的兩個後代。**逐行對照就看得出來:兩支的 `_Ctl` 都只剩 `GetData()` 一個活方法、都把 `CLS002A` 的 `TransferTable` 註解掉(`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:102`、`:112`)、兩支 PO 都用 `" > = "` 這個寫法組起迄條件、都在查詢前塞一整排 `DefaultValue`。差別只有三個:

| 差別 | `CLSI001`(直銷) | `CASI001`(代銷) |
|---|---|---|
| 硬條件 | `USAGE = '2'` | `USAGE = '3'` |
| 員工範圍 | `JOIN TABLE(F_TA_GET_DIRECT_EMPS('<員編>'))` 表值函式 | 5 個員編寫死在 SQL 字串裡 |
| 代碼說明 join | 5 個 `COD006A`(`P3` / `20` / `P3` / `19` / `15`) | 10 個 `COD006A` |

### 5.2 查詢條件

畫面收 13 個條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:115-177`):四組起迄(客戶拜訪單號、潛在客戶序號、員工編號、受益人戶號)+ 實際拜訪日期起迄 + 五個下拉(實際拜訪方式、拜訪重點代碼、客戶等級、客戶投資意願、風險屬性)。五組起迄都有「填起不填迄就自動補成相同」的 UI 行為。

四組起迄在按查詢時都會檢查「只填迄」與「起 > 迄」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:68-107`),成立就阻擋。

### 5.3 會把資料濾掉而不提示的條件

#### (1) `USAGE = '2'` 硬條件

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132`。**`CLS001A` 裡不是直銷的那一半永遠查不到**,畫面上沒有這個欄位、也沒有提示。這是 CLS 與 CAS 分割同一張表的唯一機制(§8.2)。

#### (2) 表值函式決定看得到誰

```
JOIN TABLE(F_TA_GET_DIRECT_EMPS('{0}')) T ON CLS001A.EMP_NO = T.DEPT_EMP_NO
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107-108`)。這是 `JOIN` 不是 `LEFT JOIN`,所以**函式回空集合時整份查詢回 0 筆**。函式本體不在 repo(`DB/Function/` 23 支裡沒有它),名字看起來是「取某員編直屬的員工清單」。

參數來源是 `QUERY_EMP_NO`,由 UI 從 `ClientBizUtility.GetEMP_INFO(UserID)` 回傳的逗號字串取第 2 段(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:118-124`)。**取不到就不加這個參數**,而 PO 端是 `.Rows.Find("QUERY_EMP_NO")).Value.ToString()` 沒有 null 檢查(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136`)——**沒有員工代號的使用者一按查詢就是 `NullReferenceException`,被 `catch` 吞成「執行失敗,請檢查」**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:387-392`),看不出真正原因。

而且參數是用 `string.Format` 串進 SQL 字串的,不是綁參數(附錄 E)。

#### (3) 起迄比較符號中間有空白 —— 8 處

```
strSQL += " AND CLS001A.CALL_RPT_NO > = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163`,同樣寫法在 `:174`、`:185`、`:195`、`:206`、`:216`、`:227`、`:237`。SQL 的 `>=` 是單一 token,中間不能有空白。**假設**:這 8 個條件只要有一個被加進去,整段 SQL 就會在 Oracle 端語法錯誤,被 `catch` 吞成「執行失敗,請檢查」;依據是 SQL 標準與 Oracle 的詞法規則,**無法在本機驗證**。與 `cas.md §5.3` 的結論一致——全庫只有 4 個檔有這個寫法,四支是同一份樣板的後代。

#### (4)~(6) 其他三個

| # | 現象 | 影響 | 錨點 |
|---|---|---|---|
| 4 | 實際拜訪日期用**字串比較**(`yyyyMMdd`)。注意這兩條沒有 `Opeartor == Equal` 的包裝、符號也是正確的 `>=` / `<=`,所以**只有日期條件會真的生效** | 只要有一筆存成別的格式(補空白、含分隔符號、空字串)就落在區間外 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:250`、`:266` |
| 5 | 五個 `COD006A` 說明 join 的分類碼寫死成 `P3` / `20` / `P3` / `19` / `15`;其中 `TRACE_CODE` 與 `INTRO_TYPE` **共用 `P3`**,要確認是不是複製貼上的錯 | 都是 `LEFT JOIN` 不會濾掉主檔,但分類碼改動時說明欄整片變空,使用者看到「代碼有值、說明空白」 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:115-129`、`:117` 與 `:123` |
| 6 | 五個下拉條件串成 `"AND CLS001A." + Row.Name + …`,**`AND` 前面沒有空白** | 前一段結尾是 `'`,Oracle 詞法可以斷開字串常數與關鍵字,**推測**不會出錯;靠運氣不是靠設計 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:282`、`:292`、`:303`、`:313`、`:323` |

### 5.4 取數之後做的事

PO 在 `LoadDataSet` 之前塞了 13 個 `DefaultValue`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:360-372`),包括 `STATUS = "301"`、四眼的 ID 欄全設成當前使用者、日期設成當下、`REJECTDATE` 設成 `1900/1/1`。

**這對唯讀查詢沒有意義**——這些是 `DataColumn` 的預設值,只在「新增一列而沒給值」時生效,而查詢不會新增列。它是從批次那份樣板複製過來的死碼,與 `cas.md §5.4` 的結論相同。

查無資料時回 `AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:378-381`)。

### 5.5 明細視窗 `CLSI001p0`

雙擊 grid 任一列會開 `CLSI001p0`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:233-248`)。它是**純唯讀展示**——`Load` 裡把 18 個控件全部 `Enabled = false` 或 `ReadOnly = true`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:48-67`),只有一個「離開」鈕。

三個要注意的地方:

1. **它是全模組唯一寫出「直銷」兩個字的檔案**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:1073`),§0.1 的業務推測主要靠它。

2. **塞值時完全沒有 null 檢查**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89`),`row.EST_CALL_DATE` / `row.TRAFFIC_FEE` 這種可空欄位一旦是 NULL,typed DataSet 會丟 `StrongTypingException`。對照 `CLSM001` 每一欄都寫 `if (!row.IsXxxNull())`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:457-490`)——同一個模組兩種寫法。

3. **控件名與塞進去的欄位對不起來**:`ucSTAFF_TYPE`(理專等級)被塞 `row.CUST_CLASS`(客戶等級)(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:87`),而畫面標題確實是「客戶等級」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:489`)。標題對、控件名錯,改的人很容易搞混。

呼叫端在視窗關閉後會依 `DialogResult` 做 `row.EndEdit()` / `row.CancelEdit()`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:240-247`),但視窗裡沒有任何可編輯的控件,**這兩行是死碼**。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 四組起迄只填「迄」 | 起空迄有值 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:70-71`、`:78-79`、`:86-87`、`:94-95` |
| 按查詢前 | 四組起迄的起 > 迄 | 兩邊都填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:72-74`、`:80-82`、`:88-90`、`:96-98` |
| 按查詢前 | 實際拜訪日期起迄 | 同上 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:101-107` |
| 按查詢前 | 至少填一個條件 | — | **沒有這條檢核** | — |
| 查詢時 | `USAGE = '2'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132` |
| 查詢時 | 直屬員工清單 | 永遠(`JOIN` 不是 `LEFT JOIN`) | 過濾(無提示,空清單 → 0 筆) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107-108` |
| 查詢時 | 取不到員工代號 | `GetEMP_INFO` 回空 | **例外 → 訊息「執行失敗,請檢查」** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136` |
| 查詢時 | SQL 語法錯(`> =`) | 有帶任一起迄條件 | **假設**整個查詢失敗,訊息「執行失敗,請檢查」 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163` |
| 查詢時 | 日期用字串比較 | 資料格式不一致 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:250`、`:266` |
| 查詢時 | 代碼說明的分類碼寫死 | 分類碼改動 | 過濾(無提示,說明變空) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:115-129` |
| 查詢後 | 0 筆 | 無資料 | 警示 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:378-381` |
| 雙擊明細 | 欄位為 NULL | 任一可空欄是 NULL | **例外**(無保護) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89` |

## 6. 批次(B)與 WindowsService

```text
[圖] 兩支批次的資料流:CLSB001 叫 SP 重算庫存並留快照,CLSB002 改 CLS012 的兩個門檻
圖中文字:CLSB001 庫存與快照重算 / 畫面只有一個欄位 / 庫存日期 · 不可未來 / S_TA_CLSB001_EXE / WNAV_DATE + WUSERID / CLS001 的 AUM 欄 / 四個庫存欄被重算 / CLS001H + CLSB001 / 當日快照留一版 / 同一支 SP 本來也掛在 CLSM001 存檔後,已整段註解 / CLSM001 AfterAdd / 整段被註解 / 補戶號時的 COM 參數 / UI 還在塞,PO 不再用 / 結果 / 補戶號後庫存要等下次批次 / CLSB002 交通費與拜訪次數門檻 / 畫面兩個數字 / 上限(元) / 應完成次數 / Query 先讀現值 / SELECT * FROM CLS012 / Execute / UPDATE CLS012 無 WHERE / CLSR002 報表 / RPS6 與 RPS9 讀這兩個值 / 共同點:人工按鍵觸發 · 無四眼 · 無 WindowsService · 直接改正式表
```

*圖:圖 4 批次資料流。兩支都沒有排程、沒有 WindowsService,只能由人在畫面上按「執行」。橘色虛框是三個陷阱:`CLSM001` 存檔後重算庫存那段已整段註解、`CLSB002` 的 UPDATE 不帶 WHERE、以及 `CLS012` 的兩個值被報表當常數讀(附錄 E)。*

**本模組兩支 B 畫面,沒有任何 WindowsService,也沒有排程。**`Dev/ATLAS.CLS/` 底下沒有 `WindowsService` 資料夾,掃描母體的 Service 數是 0。兩支都只能由人在畫面上按「執行」。

### 6.1 `CLSB001` — 庫存重算與快照(推測)

#### 觸發與輸入

畫面只有一個欄位「庫存日期」,預設今天,**最大值限制為今天**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33`、`:38`)。按執行時把它轉成 `yyyyMMdd` 放進 `BAL_DATE` 參數(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:41-45`)。

#### 做什麼

PO 的 `Execute` 只做一件事:開交易、叫 SP、commit(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:45-89`):

```
S_TA_CLSB001_EXE(WNAV_DATE => <庫存日期>, WUSERID => <登入者>)
```

**SP 原始碼不在 repo**(`DB/SP/` 83 支裡沒有它),所以它到底寫了哪些表只能從呼叫端與其他 SQL 反推:

| 證據 | 推論 |
|---|---|
| `CLSM001` 的 AUM 四欄畫面唯讀,而且沒有任何 UPDATE 走 PO | `CLS001.ON_AO_AUM` / `ON_AUM` / `OF_AO_AUM` / `OF_AUM` 由這支 SP 寫 |
| `CLSM002` 與兩支 R 都從 `CLSB001` 這張表取 `EXEDATE` | SP 每跑一次就在 `CLSB001` 表插一列執行日 |
| 同樣那段 CTE 在 `EXEDATE < MAXDATE` 時讀 `CLS001H` | SP 每跑一次會把 `CLS001` 整批複製一份到 `CLS001H` |
| `CLSM002` 的查詢有 `WHERE CUS_LV IS NOT NULL` | `CUS_LV`(客戶等級)也是這支 SP 算出來的 |
| `CLSM001` 被註解的 `AfterAdd` 呼叫的也是這支 SP,而且多傳一個 `WBF_NO` | SP 支援「只重算一個戶號」的模式 |

**注意畫面代號 `CLSB001` 同時是一張表的名字。**`FROM CLSB001` 出現在 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:177-178` 與 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:50-51`。這張表不在掃描母體裡(母體只收被 `xTableMapping` 宣告的表),但**它是整個模組查詢與報表的起點**。

#### 失敗處理

`catch` 分兩路(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:69-81`):

| 情況 | 行為 |
|---|---|
| 例外訊息含 `-20001` | 切 `ex.Message.Split(':')[1]`,再截到 `"ORA-"` 之前,當成「執行失敗:<業務訊息>」 |
| 其他 | 把 `ex.ToString()` **整串當成結果訊息**塞給使用者 |

第一路是「SP 用 `RAISE_APPLICATION_ERROR(-20001, …)` 回業務訊息」的慣用寫法,但**兩個字串操作都沒有防呆**:`Split(':')[1]` 假設一定有冒號、`Substring(0, IndexOf("ORA-"))` 假設一定找得到 `ORA-`。任一個不成立就在 `catch` 裡再丟一次例外。同樣的寫法也出現在 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:83-87`。

**沒有 rollback。**`tran.Commit()` 在 try 裡,失敗時 `finally` 只做 `Dispose(tran)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:82-87`)。這行為依賴 `Database.Dispose(DbTransaction)` 會不會隱含 rollback,而那支沒有原始碼——**要現場確認**。

#### 與 M 畫面的關係

`CLSM001` 的 `AfterAdd` / `AfterUpdate` 原本會在補戶號時就地叫同一支 SP 重算單一戶號(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:99-123`),**整段已被註解**。UI 端塞 `COM` 參數那行還活著(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75`)。**現況是:補完戶號後庫存與客戶等級要等下一次 `CLSB001` 才會出現。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選日期 | 庫存日期不可大於今天 | — | 阻擋(控件 `MaxDate`) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33` |
| 按執行前 | 有沒有選日期 | — | **沒有檢核**(空值會轉成空字串傳給 SP) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:44` |
| 按執行前 | 同一天重複執行 | — | **沒有檢核** | — |
| 執行時 | SP 回 `-20001` | SP 主動擋 | 警示(訊息由 SP 決定) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:71-75` |
| 執行時 | 其他例外 | — | 警示(**把 `ex.ToString()` 給使用者看**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:78` |

### 6.2 `CLSB002` — 交通費與拜訪次數門檻(推測)

#### 觸發與輸入

畫面上兩個數字欄:「每人月交通費上限(元)」`TRFF_LMT` 與「未過試用期應完成次數」`NEED_TM`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.Designer.cs:140`、`:175`),還有一組「變更前 / 變更後」的對照顯示(`:218`、`:230`)。

進畫面會先 `DoSearch()` 把現值讀出來(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:75-78`),讀回來的兩個值用 `Result[0].ReturnRowCount` 與 `Result[1].ReturnRowCount` **靠位置取**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:52-53`)。

#### 寫哪些表

```
UPDATE CLS012 SET TRFF_LMT = :TRFF_LMT, NEED_TM = :NEED_TM,
                  UPDATEID = :USERID, UPDATEDATE = SYSDATE
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53`。**沒有 `WHERE`**——這是本模組唯一的無條件 UPDATE。如果 `CLS012` 永遠只有一列就沒事,但程式裡沒有任何地方保證這件事;讀取那邊也是 `SELECT * FROM CLS012` 直接取 `Rows[0]`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:92-96`)。

`CLS012` **不在掃描母體**(沒有任何 PO 用 `xTableMapping` 宣告它),但它是兩支報表的參數來源:

| 欄位 | 誰讀 | 怎麼用 |
|---|---|---|
| `NEED_TM` | `CLSR002` 第 6 種報表(未過試用期) | `(SELECT NEED_TM FROM CLS012) NEED_TM` 當一整欄印出來,讓報表比對實際次數是否達標;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1001` |
| `TRFF_LMT` | `CLSR002` 第 9 種報表(交通費) | `(SELECT TRFF_LMT FROM CLS012) NEED_TM` —— **別名還是 `NEED_TM`**;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1504` |

兩個語意不同的值共用同一個結果集欄位名 `NEED_TM`(`CLSR002Model.xsd` 的 `T0` 有這一欄),**因為兩份 rpt 版型不同所以不會混**,但改欄位時很容易改錯邊。

**兩個值都沒有任何地方在「擋」。**交通費超過 `TRFF_LMT` 時 `CLSM002` 不會阻止;拜訪次數不足 `NEED_TM` 時也沒有任何畫面提示。它們純粹是**報表上的參考線**。

#### 失敗處理

`Execute` 的 `catch` 把 `ex.ToString()` 當結果訊息(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:68`),`finally` 一律 `dbTA.Dispose()`。**沒有交易**——`ExecuteNonQuery(cmd)` 不帶 `DbTransaction`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:60`),兩個欄位是一起改的所以影響有限。

輸入值用 `Convert.ToInt32(GetParamValue(...))`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:56-57`),**空字串會丟 `FormatException`**,被 `catch` 轉成一長串 .NET 例外文字給使用者。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按執行前 | 宣告式必填 | 由 Designer 決定 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:30-35` |
| 按執行前 | 數值範圍 / 上下限 | — | **沒有檢核**(0 或極大值都存得進去) | — |
| 進畫面 | `CLS012` 一列都沒有 | 表是空的 | **例外**(`Rows[0]` 無保護) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:96` |
| 進畫面 | 讀取失敗 | 例外 | **例外**(`Result[1]` 取不到,見附錄 E) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:53` |
| 執行時 | 輸入非數字 | 空字串 | 警示(`FormatException` 文字) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:56` |
| 執行時 | `CLS012` 有多列 | 資料異常 | **全部被改**(無 `WHERE`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53` |

## 7. 報表(R)

```text
[圖] 兩支報表畫面的選項如何對應到 22 支 rpt 版型,以及取數與取檔的兩條路
圖中文字:CLSR001 業務員客戶清冊(6 個選項 → 9 支 rpt) / 報表種類 6 選 1 / DataValue 6/7/2/3/4/5 / S_TA_CLSR001_GET_ + 值 / SP 名由參數串出來 / 三個 refcursor / T1 / T2 / T3 / RPS2~RPS9 / RPS1 沒有入口 / CLSR002 客戶拜訪記錄(10 個選項 + 兩組 A/B → 13 支 rpt) / 報表種類 10 選 1 / CheckedIndex 0~9 / RptType 字串 / 0A 0B 1 2 3 4 5A 5B 6 7 8 9 / Reflection 叫 GetRpt+值 / NonPublic 也找得到 / 12 個私有方法 / 一個選項可以開多個視窗(MultiPrint) / RptNumber 字典 / 一個 key 對一個陣列 / CLSR001 第 0/1/2 項 / 各開兩個視窗 / CLSR002 第 8 項 / 8B 先開 8A 後開 / 第 2 次不重查 / NeedParam = false / 共同點:rpt 檔名 = 畫面代號 + RPS + 號碼,由用戶端指定,伺服器照收 / SetQueryParameters / report_type 字串 / Util.ReportParameters[0] / 位置取值 / CRReportTransfer / 無原始碼 / 回傳 rpt 位元組
```

*圖:圖 5 報表與 22 支版型的對應。兩支 R 畫面用完全不同的分派方式:`CLSR001` 把選項值串進 SP 名,`CLSR002` 把選項值串進方法名用 Reflection 叫。橘色虛框是四個要注意的地方:`CLSR001RPS1` 沒有畫面入口、SP 名與方法名都由用戶端參數決定、以及多視窗時第二次之後不重新查資料(§7)。*

兩支 R 畫面掛 **22 支 `.rpt`**,是全庫比例最高的模組之一。兩支的分派方式完全不同,要分開讀。

### 7.1 22 支 rpt 掛在哪

#### `CLSR001` — 9 支,一個選項對一支 SP

「報表種類」是 6 選 1 的選項鈕,**選項的 `DataValue` 不等於 `CheckedIndex`**(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.Designer.cs:369-380`),而且取數用 `DataValue`、選 rpt 用 `CheckedIndex`,兩套並行:

| CheckedIndex | 報表中文名 | `DataValue` → SP | rpt(開啟順序) | 對外編號 |
|---|---|---|---|---|
| 0 | 業務員客戶清冊－總表 | `6` → `S_TA_CLSR001_GET_6` | `CLSR001RPS3`、`CLSR001RPS2` | CLSR001-1 |
| 1 | 業務員客戶清冊－明細表 | `7` → `S_TA_CLSR001_GET_7` | `CLSR001RPS3`、`CLSR001RPS4` | CLSR001-2 |
| 2 | 業務員客戶清冊－基金別 | `2` → `S_TA_CLSR001_GET_2` | `CLSR001RPS8`、`CLSR001RPS7` | CLSR001-3 |
| 3 | 業務員客戶清冊－當月壽星 | `3` → `S_TA_CLSR001_GET_3` | `CLSR001RPS9` | CLSR001-4 |
| 4 | 客戶來源清冊(A 總表 / B 明細表) | `4` → `S_TA_CLSR001_GET_4` | `CLSR001RPS5` | CLSR001-5 / -6 |
| 5 | 客戶來源清冊－明細表 | `5` → `S_TA_CLSR001_GET_5` | `CLSR001RPS6` | CLSR001-7 |

錨點:對應表 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:191-204`;rpt 檔名組法 `:323`;SP 名組法 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:57`。

**`CLSR001RPS1` 沒有任何畫面入口。**六個選項的 `RptNumber` 值域是 {2,3,4,5,6,7,8,9},`1` 不在裡面。這支 rpt 仍被編進組件(`Dev/ATLAS.CLS.Report/Source/CrystalReports/Report.CLS/CLSR001RPS1.rpt`),但沒有程式會去載它。**假設**:它是早期版本或給別的入口用的,依據是同目錄的 `S_TA_CLSR001_GET_1` 這支 SP 確實還被 `CLSR002` 用(見下)。

「對外編號」那一欄來自 `RptNumber2` 字典(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:198-204`),註解寫「秀給鳳滿看」,值是 `CLSR001-1`~`-7`,只當成報表上的 `REPORT_NO` 參數印出來〔客戶特定〕。

#### `CLSR002` — 13 支,一個選項對一個私有方法

「報表種類」10 選 1,其中第 0 項與第 5 項各多一組 A / B 子選項,合起來 12 種:

| rptType | 報表中文名 | PO 方法 | rpt(開啟順序) | 對外編號 |
|---|---|---|---|---|
| `0A` | 客戶拜訪記錄明細表－by業務員 | `GetRpt0A` | `CLSR002RPS0A` | CLSR002-1 |
| `0B` | 客戶拜訪記錄明細表－by銷售機構 | `GetRpt0B` | `CLSR002RPS0B` | CLSR002-2 |
| `1` | 客戶拜訪記錄明細表－by客戶 | `GetRpt1` | `CLSR002RPS1` | CLSR002-3 |
| `2` | 客戶拜訪記錄明細表－推薦基金 | `GetRpt2` | `CLSR002RPS2` | CLSR002-4 |
| `3` | 客戶拜訪記錄明細表－新產品需求 | `GetRpt3` | `CLSR002RPS3` | CLSR002-5 |
| `4` | 客戶拜訪記錄明細表－內部支援 | `GetRpt4` | `CLSR002RPS4` | CLSR002-6 |
| `5A` | 拜訪重點－by業務員 | `GetRpt5A` | `CLSR002RPS5A` | CLSR002-7 |
| `5B` | 拜訪重點－by銷售機構 | `GetRpt5B` | `CLSR002RPS5B` | CLSR002-8 |
| `6` | 客戶拜訪統計表－未過試用期 | `GetRpt6` | `CLSR002RPS6` | CLSR002-9 |
| `7` | 客戶拜訪次數及銷售統計表 | `GetRpt7` | `CLSR002RPS7` | CLSR002-10 |
| `8` | 拜訪客戶未完成總表及明細表 | `GetRpt8` | `CLSR002RPS8B`、`CLSR002RPS8A` | CLSR002-11 |
| `9` | 交通費明細表 | `GetRpt9` | `CLSR002RPS9` | CLSR002-12 |

錨點:對應表 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:186-210`;選項中文名 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.Designer.cs:608-627`;rpt 檔名組法 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:286`。

**分派是用 Reflection 做的:**

```
var RptType = EVAStringHelper.GetParamValue(model, "RptType");
MethodInfo mi = this.GetType().GetMethod("GetRpt" + RptType,
                    BindingFlags.Instance | BindingFlags.NonPublic);
mi.Invoke(this, new object[] { model });
```

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:155-157`。**方法名由用戶端傳來的參數串出來,而且連 `NonPublic` 都找得到。**這與 `cas.md §7.3` 記的 `CASR002` 用 `if-else` 階梯是兩種完全不同的做法。好處是加報表不用改分派,壞處是:(1) 傳一個不存在的值 → `mi` 是 null → `NullReferenceException`,被 `catch` 轉成 `ex.ToString()` 給使用者;(2) 任何未來加進這個類別、簽名相符的私有方法都會變成可從用戶端呼叫。

### 7.2 兩支報表的取數路線完全不同

| 面向 | `CLSR001` | `CLSR002` |
|---|---|---|
| 取數 | 一支 SP,三個 refcursor(`OUTTB1` / `OUTTB2` / `OUTTB3` → `T1` / `T2` / `T3`) | **自組 SQL,1,535 行的 PO** |
| 主檔來源 | SP 內部(看不到) | `strCLS` 這段共用 CTE,讀 `CLS001H` 或 `CLS001` |
| 逾時 | `CommandTimeout = 0`(永不逾時) | 預設 |
| 參數傳法 | 把 `Util.Parameters` 整包迴圈丟進去,全部當 `Varchar2`,再手動把兩個改回 `Int32` | 逐段 `AddParam` |
| 另有 | `GetInitData` 供四個畫面查權限(§1.1) | `GetUidCode`(**不在介面上,死碼**) |

錨點:`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:56-79`;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105`;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:113-139`。

`CLSR001_PO.GetData` 的參數處理值得看:它先把 `RptType` 從參數表刪掉(因為那是用來組 SP 名的,不是 SP 參數),再把剩下全部當字串綁,最後對 `IROI_S` / `IROI_E` 兩個特判成整數(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:60-69`)。**這兩個參數名寫死在 PO 裡**,UI 那邊只要漏塞任何一個就是 `KeyNotFoundException`;實際上 UI 是無條件塞的(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:309-318`),所以目前不會爆。

#### `CLSR002` 的共用 CTE:`strCLS`

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105` 是一段 `readonly string`,12 支方法有 11 支以它開頭。三層:

| CTE | 內容 |
|---|---|
| `ISHIS` | `SELECT MAX(EXEDATE) QDATE, MAX((SELECT MAX(EXEDATE) FROM CLSB001)) MAXDATE FROM CLSB001 WHERE EXEDATE <= :ACT_CALL_DATE_END` |
| `MYSAL051` | 從 `V_SAL051` 取每個員編的部門(`SAL_DEPT_NO LIKE 'S____'` 且 `SAL_CD IN ('A','B','C')`) |
| `CLS` | `QDATE < MAXDATE` → `CLS001H`;`QDATE = MAXDATE` → `CLS001`,兩段 `UNION ALL` |

**`CLSM002_PO` 有一份幾乎一樣但不完全相同的複製品**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-273`),差別:

| 差別 | `CLSR002_PO.strCLS` | `CLSM002_PO.BuildMasterSQLString` |
|---|---|---|
| 部門來源 | `V_SAL051` 聚合成 `MYSAL051` | 直接 join `SAL051` |
| `CUS_LV` | `NVL(CUS_LV, ' ')` | 不做 NVL,外層另有 `WHERE CUS_LV IS NOT NULL` |
| 多帶的欄 | — | `CMD_PERSON`、`A.ID_NO`,再接一層 `MYCLS001` |
| `EXEDATE` 上限 | 綁參數 `:ACT_CALL_DATE_END` | **字串串接**,而且沒給日期時寫死 `'29991231'` |

**同一個「要讀快照還是現值」的判斷有兩份實作,改一邊漏一邊查出來的客戶清單就會不一致。**

### 7.3 逐支報表的取數重點

| rptType | 主要 join | 特別的地方 |
|---|---|---|
| `0A` / `0B` | `CLS` + `CLS002` + `CLS003` + `CTL014`(447)+ `COD006A`(D2)+ `OFD068A` | 先查明細再查一次「總計」,用 LINQ join 把總計欄位補回明細列(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:281-291`)。**`0A` 把 `CUS_LV` 條件加了兩次**(附錄 E) |
| `1` | 同上 | 用 `LEAD(B.CLL_NO) OVER (ORDER BY B.CLL_NO)` 判斷是不是同一張單的最後一列來去重計數(`:455-463`) |
| `2` | 多 join `CLS004` + `OFD081A` | 條件多一個 `FUND_ID`(`:572`) |
| `3` | 多 join `CLS005` | — |
| `4` | 多 join `CLS003` + `CTL014`(603) | 硬條件 `AND TRIM(INTER_SUP) IS NOT NULL`(`:680`) |
| `5A` / `5B` | 多 join `CLS003` + `COD006A`(D2) | 兩支差在 `GROUP BY` 的維度 |
| `6` | `OFD081A`+`OFD081`、`OFD300`、`OFD221A_V01`/`OFD221`/`OFD251A`/`OFD251`~`OFD254`、`CRM004` | 全模組最長的一段(約 200 行),算貨幣 / 非貨幣的申購與淨申購,再與 `CLS012.NEED_TM` 比對。硬條件 `COD009.TEST_YN = 'N'`(`:959`) |
| `7` | `CRM004` + `CLS002` | 查完主表**再叫一次 SP** `S_TA_CLSR001_GET_1` 填 `T3` 等級表(`:1258-1263`);硬條件 `AND TRIM(A.EMP_NO) IS NOT NULL`(`:1247`) |
| `8` | `CRM004` + `OFD306A` | 兩段查詢:總表填 `T0`、明細填 `T1`;明細的 `ORDER BY` 尾端接 `SORT` 參數(`:1471-1474`) |
| `9` | `CLS002` + `COD009` + `MYSAL051` + `OFD068A` + `CTL014`(605) | 硬條件 `WHERE TRAN_FEE > 0`;客戶姓名做遮罩;讀 `CLS012.TRFF_LMT`(`:1486-1520`) |

`9` 的遮罩規則寫死在 SQL 裡〔客戶特定〕:

```
CASE WHEN BF_COUNTRY_X = '01'
     THEN SUBSTRB(PR_NAME,1,2) || '＊＊'      || SUBSTRB(PR_NAME,7, LENGTHB(PR_NAME)-6)
     ELSE SUBSTRB(PR_NAME,1,2) || '＊＊＊＊＊' || SUBSTRB(PR_NAME,13,LENGTHB(PR_NAME)-12)
END
```

(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1488-1495`)。本國(`01`)遮 4 個 byte、外國遮 10 個 byte。**姓名 byte 數小於遮罩長度時第二段 `SUBSTRB` 的長度參數會是負數**,Oracle 會回 NULL,整個運算式變成「前 2 byte + 星號」——名字短的人看到的星號比名字還多。

### 7.4 多視窗列印(`MultiPrint`)

兩支畫面都覆寫 `DoPrint` / `DoPreview` 成 `MultiPrint(base.XXX)`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:65-75`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:56-64`)。邏輯:

1. 查字典拿到這個選項對應的 rpt 陣列。

2. 逐支跑 `todoPrint()`,第一支 `NeedParam = true`(真的去查資料),**第二支之後 `NeedParam = false`**。

3. `NeedParam = false` 時 `BeforePreviewOrPrint` 不塞查詢參數,`AfterPreviewOrPrint` 改成把上一次留下的資料 `Merge` 回來(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:316-327`)。

4. 任何一支查到 0 筆就停止,後面的不開。

註解寫「後面的報表先顯示,視窗再往上疊,故最前面的報表要最晚開」(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:184`),所以陣列裡的順序是**倒著寫的**——`{ 3, 2 }` 代表使用者最後看到的是 `RPS2`。

`CLSR001` 多一個變化:`NeedParam = (i == 0 || IsPrint)`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:87`)。**列印時每一支都重查一次,預覽時只查第一次。**同一份報表用預覽與用列印,取數次數不同——如果兩次取數之間資料變了,預覽與列印的內容會不一樣。

### 7.5 畫面端的檢核

#### `CLSR001`

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 生日起迄在選「當月壽星」時必填 | `CheckedIndex == 3` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:109-110` |
| 基金範圍在選「基金別」時必填 | `CheckedIndex == 2` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:111` |
| 報酬率起迄要嘛都填要嘛都不填 | XOR | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:115-117` |
| 生日起迄要嘛都填要嘛都不填 | XOR | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:118-120` |
| 報酬率起 > 迄 | 都填 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:123-125` |
| 生日起 > 迄(只比 `MMdd`) | 都填 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:126-128` |
| 選「境內基金」卻一檔都沒勾 | `ucomFUNDAREA == "1"` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:278-283` |
| 選業務員前要先填銷售機構 | — | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:524-531` |

選項連動:選「當月壽星」時客戶類型被鎖成 `"1"`(自然人)(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:417-424`);排序選項會隨「基金範圍」與報表種類整組換掉(`:429-517`)。

#### `CLSR002`

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 戶號在選「by客戶」時必填 | `custBF_NO.Enabled` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:116` |
| 實際拜訪日起 > 迄 | 有填起 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:120-122` |
| 選業務員前要先填銷售機構 | — | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:398-405` |

選項連動(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:347-390`):第 0 項開 A/B 子選項、第 1 項開戶號、第 2 項開基金、第 5 項開另一組 A/B;第 6 項(未過試用期)與第 9 項(交通費)**應該**要鎖住客戶等級,但那段程式被包在 `if (RptSort.ContainsKey(CheckedIndex))` 裡面,而 `RptSort` 只有 0/1/2/3/4/8 六個 key ——**第 6 與第 9 項根本走不到那段,鎖不住**(附錄 E)。

日期迄日在第 6 項之後會被 disable,並自動把起日補成當月 1 號、迄日補成當月最後一天(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:72-84`、`:383-385`)。

### 7.6 rpt 檔怎麼送到用戶端

兩支 Ctl 的 `GetReportObject` 都是同一行(`Dev/ATLAS.CLS.Report/Source/Control/ReportControl.CLS/CLSR001_Ctl.cs:67-71`、`Dev/ATLAS.CLS.Report/Source/Control/ReportControl.CLS/CLSR002_Ctl.cs:54-58`):

```
string rpt = Convert.ToString(ClassData.Util.ReportParameters[0].ReportClass);
return CRReportTransfer.TransferFileByte(rpt);
```

`CRReportTransfer`(無原始碼,從呼叫端反推)。**報表類別名由用戶端傳入、用位置 `[0]` 取、伺服器照單全收**——與 `cas.md §7` 記的 `CASR001` 完全一樣,是全庫 R 型的通則(`architecture.md §6.5`)。

### 7.7 與維護資料的關係

| 問題 | 答案 |
|---|---|
| 報表看到的客戶清單是現值嗎? | **不一定**。查詢迄日早於最後一次批次日就是 `CLS001H` 快照(§0.2) |
| 報表看到的拜訪單是現值嗎? | **是**。`CLS002`~`CLS005` 沒有歷史表,永遠讀現值 |
| 報表的權限與維護畫面一致嗎? | **不一致**。維護畫面 `CLSM002` 硬限定 `CREATEID = 登入者`;報表只用 `CRM002A` 的可查清單過濾銷售機構與員編,沒有 `CREATEID` 條件 |
| `CLS012` 的兩個門檻改了報表會變嗎? | **會,立刻變**。它是 `SELECT` 子查詢,不是快照 |

## 8. 跨模組共用

### 8.1 CLS 自有的五張表:沒有人當主明細用

掃描器對 `CLS001`~`CLS005` 的跨模組欄位全部是空的,也就是**沒有任何非 CLS 的畫面把它們宣告成 `xTableMapping` 的主檔或明細**。這點與 CAS(一半的維護畫面開在別人的表上,`cas.md §0.2`)和 BMS(12 張配對表橫跨三個模組,`bms.md §2.2`)都不一樣——**CLS 是這批模組裡資料自主性最高的一個**。

但「沒被當主明細用」不等於「改了沒事」,三條要注意:

| 風險 | 說明 | 怎麼查 |
|---|---|---|
| 版控外的 SP | `S_TA_CLSB001_EXE` 會寫 `CLS001` / `CLS001H`;`S_TA_CLSR001_GET_1`~`_7` 會讀。**加欄位或改型別時這些 SP 不會編譯失敗,會在執行期才爆** | 只能請 DBA 撈 `USER_SOURCE` |
| `CLS001H` 必須同步 | 它是 `CLS001` 的歷史快照,兩張表的欄位一定要同形。`CLS001` 加欄位而 `CLS001H` 沒加,`UNION ALL` 那段會直接語法錯 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:62-104` |
| `CLS001_V01` 必須同步 | `CLSM001` 的查詢讀的是這支 view 不是表,新欄位不在 view 裡查詢就看不到 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` |

### 8.2 `CLS001A` / `CLS002A`:名字像 CLS,主人是 CAS

這是本模組最容易踩的誤會,**掃描母體沒有列出它們,但 `CLSI001` 每天都在讀**。

| 事實 | 證據 |
|---|---|
| `CLS001A` 的主檔畫面是 `CASM002`,不是任何 CLS 畫面 | `atlas_scan.py --table CLS001A` 回報「主檔於 `CASM002`」;`cas.md §4.2` |
| `CLS002A` 是 `CASM002` 的明細 | `atlas_scan.py --table CLS002A` 回報「明細於 `CASM002`」 |
| 兩張表的 xsd 定義在 **CAS 專案**裡 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd` |
| CLS 這側唯一的使用者是 `CLSI001`,而且唯讀 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106` 只有 `SELECT`,全檔沒有 INSERT / UPDATE |
| CLS 這側連 `CLS002A` 都不用 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:102`、`:112` 的 `TransferTable` 被註解 |

**同一張 `CLS001A` 被五支畫面用,靠 `USAGE` 切成兩個世界**(CAS 那三支的細節見 `cas.md §8.3`):

| 畫面 | 模組 | `USAGE` 條件 | 動作 |
|---|---|---|---|
| `CASM002` | CAS | 由畫面決定 | 維護(四眼) |
| `CASI001` | CAS | 硬寫 `'3'` | 查詢 |
| `CASB001` | CAS | 無條件 | 查詢 + 直接 UPDATE |
| **`CLSI001`** | **CLS** | **硬寫 `'2'`** | **查詢** |

改 `CLS001A` 的欄位時,**`Dev/ATLAS.CAS/Source/Entity/` 與 `Dev/ATLAS.CLS/SOURCE/Entity/` 兩邊的 xsd 都要重生**,漏一邊就是靜默失敗(`architecture.md §5.4`)。

**反過來說:改 `CLS001`~`CLS005` 不會影響 CAS。**兩套是完全獨立的表,只是名字撞在一起。

### 8.3 CLS 依賴別人、別人不依賴 CLS

| 方向 | 內容 |
|---|---|
| CLS → 別人 | 讀 20 幾張外部表(§2.4),其中 `CRM002A`(可查範圍)、`SAL051`(建檔權限)、`CRM004`(拜訪次數門檻)、`CLS012`(兩個參數)是**四個會改變 CLS 行為的外部輸入** |
| 別人 → CLS | **全庫 grep 不到任何非 CLS 的 `.cs` 引用 `CLS001`~`CLS005`**;也沒有 `CLSxxx_Pxy` 被別的模組呼叫 |

唯一的例外是**模組內部的跨畫面依賴**:`CLSR001_Pxy.GetInitData` 被四個畫面呼叫(§1.1),`CLSM001_Pxy.Query` 被 `CLSM002` 呼叫。**改 `CLSR001_PO.GetInitData` 的回傳形狀會同時打到四個畫面的權限**,這是本模組最集中的單點。

### 8.4 共用的 UI 控件與下拉來源

下拉一律走 `GetDropDownDataSrc` / `GetDropDown9iDataSrc`(同一組 `447` 在 `CLSI001` 用了兩套,見 §2.5);拜訪重點走 `CodeDataSrc`,`CLSM002p2` 另外傳 `Dis = "99"` 排除「其他」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:50-51`)。

四支共用 helper:`UidCodeDateSrc`(`UserID` → `EMP_NO`,`CLSM002` 直接呼叫 `CLSM001.SetEMP_NO` 這個靜態方法,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:225`)、`ClientBizUtility.GetEMP_INFO`(`CLSI001` 取員編,回逗號字串靠位置取)、`ClientBizUtility.GetFundBusinessDay`(`CLSM002p1` 檢查申購日,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:138`)、`JumpSrNoUtility`(兩支 M 的跳號一覽表,`CLSM001` 只讀不寫)。`CLSM002` 的日期檢核取的是 **DB 端**時間 `SystemDateTime.GetSystemDate(DBServer)`,不是用戶端時間。

## 附錄 A. 資料表總表

### A.1 母體的 5 張實體表

| 表 | 欄位 | 四眼 | 主檔於 | 明細於 | 跨模組 |
|---|---|---|---|---|---|
| `CLS001` | 56 | Y | `CLSM001` | — | 無 |
| `CLS002` | 39(掃描器算 40) | Y | `CLSM002` | — | 無 |
| `CLS003` | 20(掃描器算 16) | Y | — | `CLSM002` | 無 |
| `CLS004` | 22(掃描器算 20) | Y | — | `CLSM002` | 無 |
| `CLS005` | 19(掃描器算 18) | Y | — | `CLSM002` | 無 |

括號內是 `atlas_scan.py --table` 回報的數字,與直接數 `CLSM002Model.xsd` 的 `xs:element` 不同。差異來自掃描器把 Model 與 View 的欄位做了合併去重,而兩邊不完全同形(`architecture.md §5.4`)。**以 Model xsd 為準**,因為那是伺服器側寫入用的形狀。

### A.2 母體之外、CLS 實際會動到的四張表

| 表 | 誰用 | 怎麼用 | 錨點 |
|---|---|---|---|
| `CLS001H` | `CLSM002`、`CLSR002` | `CLS001` 的歷史快照,與現值 `UNION ALL` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:73` |
| `CLSB001`(**表,不是畫面**) | `CLSM002`、`CLSR002` | 每次批次執行留一列 `EXEDATE`,是所有查詢的時間基準 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:50-51` |
| `CLS012` | `CLSB002`、`CLSR002` | 兩個參數 `TRFF_LMT` / `NEED_TM`,單列表 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53` |
| `CLS001_V01` | `CLSM001` | 查詢用的 view(定義不在 repo) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` |

**這四張一個都不在掃描母體裡**,因為母體只收被 `xTableMapping` 宣告的表(`architecture.md §5.5`)。改 `CLS001` 時前三張都要一起看。

### A.3 只讀的外部表(20 張)

`AA_USER`、`BMS001A`、`CAS004A`、`CLS001A`、`COD006A`、`COD009`、`CRM002A`、`CRM003A`、`CRM004`、`CTL014`、`OFD017A_V01`、`OFD068A`、`OFD081`、`OFD081A`、`OFD115A`、`OFD123A`、`OFD221`、`OFD221A_V01`、`OFD251`、`OFD251A`、`OFD252`、`OFD253`、`OFD254`、`OFD300`、`OFD302`、`OFD302A`、`OFD306`、`OFD306A`、`SAL051`、`V_SAL051`。用途見 §2.4。

### A.4 只存在於 SQL 字串裡的 CTE 名稱

`ISHIS`、`CLS`、`CLS2`、`MYCLS001`、`MYCLS002`、`MYSAL051`、`MYBMS001A`、`MYCOD`、`MYOFD081`、`MYOFD081V`、`MYOFD300`、`MYOFD302A`、`MYOFD306A`、`MYTRADE`、`MYTRADE2`、`MYROW_DATA`、`MYTRADE_SUM`。**這些是 `WITH` 子句的別名,不是表**,搜尋表名時會誤中。

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:零支

`DB/` 底下 `Function` 23 支、`SP` 83 支、`Table` 158 支、`Trigger` 13 支、`View` 2 支,**沒有任何一支與 CLS 相關**(檔名與內容都 grep 過)。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 類 | 名稱 | 誰呼叫 | 參數 / 回傳 |
|---|---|---|---|
| SP | `S_TA_CLSB001_EXE` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:53`;另有被註解的呼叫 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:103` | `WNAV_DATE`、`WUSERID`(註解版多一個 `WBF_NO`);無回傳 |
| SP | `S_TA_CLSR001_GET_2`~`_7` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:57`(名字由參數串出) | 全部參數當 `Varchar2` 綁,除 `IROI_S` / `IROI_E` 改 `Int32`;三個 refcursor `OUTTB1`/`OUTTB2`/`OUTTB3` |
| SP | `S_TA_CLSR001_GET_1` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1258` | `ICUS_LV`;一個 refcursor `OUTTB` |
| Fn | `F_TA_GET_DIRECT_EMPS` · `F_GET_FND_PROF_TYPE` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107` · `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:843` | 吃員編回 `DEPT_EMP_NO` 集合(表值函式)· 吃 `FUND_ID` 與 `'0'` 回 `PROF_TYPE` |
| View | `CLS001_V01` · `V_SAL051` · `OFD017A_V01` / `OFD221A_V01` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` · `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:57` · `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:270` | 各自表的查詢包裝 |
| 框架 | `CRReportTransfer.TransferFileByte` · `SerialNo.GetPR_NO2` / `GetCALL_RPT_NO` · `SrNoCommentProcessor` | 兩支 R 的 Ctl · 兩支 M 的 `BeforeAdd` · `CLSM002_PO` 的八個事件 | 回傳 rpt 位元組 · 取流水號 · 跳號註記(皆無原始碼,從呼叫端反推) |

**整個模組的「業務算式」(庫存怎麼算、客戶等級怎麼定、清冊怎麼組)全部在版控外。**這是讀本文時最大的限制。

## 附錄 C. 代碼對照

### C.1 有完整值域的:只有 `SAL_CD`

`A` 部門主管 / `B` 組長 / `C` 業務員 / `D` 助理 / `E` 外交割人員 / `F` 其他(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479`)。前三個可以建檔。

### C.2 從判斷式反推的

| 欄位 | 已知值 | 出處 |
|---|---|---|
| `ACT_CALL_TYPE` / `EST_CALL_TYPE` | `1` 親訪 / `2` 電訪 / `3` E-mail | §2.5 |
| `TRAFFIC` · `TOPIC_CODE` · `INTER_SUP` | `2` 自行開車 · `99` 其他 · `4` 其他 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:713`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:94`、`:73` |
| `USAGE`(`CLS001A`) | `2` 直銷 / `3` 代銷 | §2.5 |
| `PR_TYPE` · `FUNDAREA` | `1` 自然人(當月壽星報表鎖住)· `1` 境內 / `2` 境外 / 其他=全部 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:424`、`:264-296` |
| `BF_COUNTRY_X` · `AGENT_ID` · `EX_CD` | `01` 本國 · `0`(`OFD068A` join 寫死)· `1`(匯率種類) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1489`、`:200`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:319` |
| `ALLOT_PROC_CODE` / `REDEM_PROC_CODE` | `2` / `7` / `3` / `5` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:895`、`:905`、`:915`、`:929` |
| `PROF_TYPE` · `TEST_YN` | `3` 貨幣型(其餘非貨幣)· `N` 非測試員工 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:975-980`、`:959` |

### C.3 下拉分類碼

`601` 客戶來源 · `602` 客戶等級 · `603` 內部支援 · `604` 庫存情況 · `605` 交通工具 · `606` 基金範圍 · `447` 拜訪方式 · `448` 往返 · `404` 風險屬性 · `D2` 拜訪重點 · `P3` / `20` / `19` / `15` (`CLSI001` 的五個說明 join)。完整對應見 §2.5。

### C.4 排序參數(報表)

`CLSR001` 的排序值是 `0`~`6`(戶號 / 客戶來源 / 境內歸屬AO / 境內總 / 境外歸屬AO / 境外總 / 生日),當成 `SORTID` 參數送給 rpt(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:207-213`、`:354`)。

`CLSR002` 的排序值是**欄位名字串**(`ACT_CALL_DATE`、`BF_NO`、`B.ACT_CALL_TYPE`、`-ALLOT_AMT`…),直接串進 SQL 的 `ORDER BY`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:214-226`)。前面加 `-` 代表降冪(Oracle 的數值取負)。

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

`atlas_scan.py --module CLS` 的母體:畫面 7(B 2 / I 1 / M 2 / R 2)· 表 5 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 22 · Service 0。

| 類別 | 母體 | 本文已提及 |
|---|---|---|
| 畫面 | 7 | 7(100%) |
| 資料表 | 5 | 5(100%) |
| SP / Fn | 0 | —(母體是 0,實際有 9 支在版控外,見附錄 B) |
| rpt | 22 | 22(100%,§7.1 逐支列出) |

### D.2 母體沒列到、但本文寫了的東西

放進 meta `refcheck-ignore` 的:四張程式天天讀但沒被 `xTableMapping` 宣告的表(`CLS001H` / `CLSB001` 表 / `CLS012` / `CLS001_V01`)、9 支版控外 SP 與 Function、5 支彈出視窗(`CLSM001p0` / `CLSM002p0` / `CLSM002p1` / `CLSM002p2` / `CLSI001p0`,它們不是獨立畫面代號)、17 個 CTE 別名(避免讀者當表去找)、以及 6 張報表 join 到但不在索引的外部表(`OFD306` / `OFD306A` / `V_SAL051` / `AA_USER` / `OFD017A_V01` / `OFD221A_V01`)。

**`CLS001A` / `CLS002A` 兩張都在索引裡,不用 ignore**——它們是 CAS 的表,本文只是從 CLS 這側交代歸屬(§8.2)。

### D.3 母體列了、本文交代不足的

**沒有。**7 支畫面各有專節,5 張表各有欄位表,22 支 rpt 在 §7.1 逐支對應到畫面選項。

### D.4 標「假設」的地方總表

| # | 假設 | 依據 | 怎麼驗 |
|---|---|---|---|
| 1 | `CLS` 三個字母代表「直銷客戶」 | `CLSI001p0` 的視窗標題「直銷客戶查詢作業」 | 問使用者單位 |
| 2 | `USAGE` 的 `2` = 直銷、`3` = 代銷 | `CLSI001` 寫 `'2'`、`CASI001` 寫 `'3'`,兩支同一份樣板 | 查 `CLS001A` 實際資料分布 |
| 3 | `CLS003` / `CLS004` / `CLS005` 的主鍵 | 彈出視窗的重複檢查欄位 + xsd 的不可空欄 | 查 DB 的 constraint |
| 4 | `S_TA_CLSB001_EXE` 寫 `CLS001` 的 AUM、`CLS001H`、`CLSB001` 表、`CUS_LV` | 五條間接證據(§6.1) | 撈 SP 原始碼 |
| 5 | `> =` 這個寫法會讓整段 SQL 語法錯 | SQL 標準與 Oracle 詞法 | 連 DB 實測(與 `cas.md §5.3` 同一條) |
| 6 | `AND` 前面沒空白不會出錯 | Oracle 詞法可斷開字串常數與關鍵字 | 連 DB 實測 |
| 7 | `CLSR001RPS1` 是早期版本或別的入口用的 | 六個選項的值域不含 `1`,但同號 SP 仍被 `CLSR002` 用 | 問使用者單位 |
| 8 | `EX_RATE <= :ACT_CALL_DATE_END` 這條件實際等於沒作用 | `EX_RATE` 是數值、繫結值是 `yyyyMMdd` 字串,隱含轉型後所有匯率都小於它 | 查 `OFD300.EX_RATE` 的型別與值域 |
| 9 | `CLS012` 只有一列 | `SELECT * … Rows[0]` 與無 `WHERE` 的 UPDATE 都這樣假設 | 查 DB |
| 10 | `Database.Dispose(DbTransaction)` 會隱含 rollback | `CLSB001_PO` 沒有任何 `Rollback()` 呼叫 | 反編譯框架 DLL 或實測 |

## 附錄 E. 讀本文時要注意的地方

按嚴重度由高到低。**每條都是讀碼直接看到的,不是推測**(標「假設」者除外)。

### E1 Oracle 三值邏輯:庫存條件會靜默濾掉新客戶 · 嚴重度 高

```
if (row.Value == "1") strSQL += " AND ON_AO_AUM + OF_AO_AUM > 0";
else if (row.Value == "2") strSQL += " AND ON_AO_AUM + OF_AO_AUM = 0";
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182`。兩個 AUM 欄在 xsd 裡都是可空的,而 Oracle 的 `NULL + 0` 仍是 `NULL`,`NULL > 0` 與 `NULL = 0` 都是 UNKNOWN。

**影響**:還沒跑過 `CLSB001` 的新客戶(AUM 是 NULL),使用者選「有庫存」查不到、選「無庫存」也查不到,而且畫面不會提示。與 `cas.md 附錄 E` 記的 `CASB001_PO` 是同一型錯誤。修法是 `NVL(ON_AO_AUM,0) + NVL(OF_AO_AUM,0)`。

### E2 匯率條件拿數值欄比日期字串 · 嚴重度 高

```
LEFT JOIN OFD300 C ON A.FUND_CURRENCY = C.CRNCY_CD
                  AND C.EX_CD = '1'
                  AND EX_RATE <= :ACT_CALL_DATE_END
```

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:861-864`。同一段的聚合是 `MAX(EX_RATE) KEEP(DENSE_RANK LAST ORDER BY CDATE)` —— 排序用的是 `CDATE`,可見**原意應該是 `CDATE <= :ACT_CALL_DATE_END`**,寫成了 `EX_RATE`。

**影響**(**假設**,依據見附錄 D.4 第 8 條):繫結值是 `yyyyMMdd` 八位數字字串,隱含轉型成 20250131 這種數字後,任何正常匯率都小於它,條件恆真——**第 6 種報表的匯率永遠取最新,不是取查詢期間的**。跨期間比較的金額會失真,而且完全沒有症狀。

### E3 `UPDATE` 不帶 `WHERE` · 嚴重度 高

```
"UPDATE CLS012 SET TRFF_LMT = :TRFF_LMT, NEED_TM = :NEED_TM, UPDATEID = :USERID, UPDATEDATE = SYSDATE"
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53`。`CLS012` 若不只一列,全部會被改成同一組值,而且**沒有交易**(`ExecuteNonQuery(cmd)` 不帶 `DbTransaction`)。讀取端也是直接 `Rows[0]`(`:188`),兩邊都假設「只有一列」但沒有人保證。

### E4 字串串接進 SQL(注入面) · 嚴重度 高

| 位置 | 串什麼 | 錨點 |
|---|---|---|
| `CLSI001_PO` | 登入者員編 → 表值函式參數 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136` |
| `CLSI001_PO` | 8 組起迄條件 + 5 個下拉值 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163`~`:323` |
| `CLSI001_PO` | `GetEmpNo` / `GetUidCode` 的 `UserID` / `EmpNo` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:415`、`:446` |
| `CLSM001_PO` | 銷售機構 + 員編 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:208`、`:212` |
| `CLSM002_PO` | 銷售機構 + 員編 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:169` |
| `CLSM002_PO` | **實際拜訪日期迄日**串進 CTE | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:183` |
| `CLSR002_PO` | 銷售機構 + 員編(12 支方法各一份) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:224`、`:229` 等 |
| `CLSR002_PO` | 排序欄位名串進 `ORDER BY` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:238` 等 7 處 |
| `CLSR002_PO` | `GetUidCode` 的 `EmpNo` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:117-119` |

值多半來自下拉或登入者,**不是自由輸入**,所以實際風險比看起來低;但 `CLSM002_PO:183`(日期)與 `CLSR002_PO` 的排序欄位是使用者可控的路徑。**同一支 PO 裡綁參數與串字串兩種寫法並存**(例如 `CLSM002_PO` 的 `:CREATEID` 是綁的、迄日是串的),是最容易誤判的地方。

### E5 可查員編清單沒有加引號,而且空清單會放大範圍 · 嚴重度 高

```
var emp = from CLSR001View.CRM002ARow r in vdb.UIView.CRM002A
          where !r.IsEMP_NONull() select r.EMP_NO;     // 沒有加引號
…
custEMP_NO_0.Filter = string.Format("LEAVE_DATE IS NOT NULL OR EMP_NO IN ({0})",
                                    string.Join(",", Sales.ToArray()));
```

`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:294-303`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:242-252`。**同一份程式在報表側是有加引號的**(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:157`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:150`),兩支 M 沒加。`EMP_NO` 在 DataTable 裡是字串欄,`IN (028039,102736)` 這種寫法在 `DataTable.Filter` 會怎麼解讀要實測,但**兩邊寫法不一致本身就是 bug**。

同一段還有兩個問題:

1. **`OR` 沒有被括號包住**。`LEAVE_DATE IS NOT NULL OR EMP_NO IN (…)` 目前是整條 Filter,但只要框架或後人再 `AND` 一個條件上去,就會變成 `(A AND B) OR C`——與 `cas.md 附錄 E` 記的 `CASB001_PO` 同一型陷阱。

2. **`Sales` 是空的時候整段不執行**,而查詢時的 else 分支也不加員編條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525`)——**取不到可查清單的人看得到全部資料**,這是「靜默放大」不是「靜默縮小」。

### E6 被註解掉但外殼還在的檢核 · 嚴重度 中

| 被停用的東西 | 外殼留下什麼 | 錨點 |
|---|---|---|
| `CLSM001` 統編重複檢查 `ChkID` | 整支方法用 `/* */` 包住,訊息「統編/ID 已存在, 不可重覆建檔」還在 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:218-252` |
| `CLSM001` 多筆受益人挑選 + 「不可建為潛在客戶」 | `HasData` 這個 `out` 參數永遠回 false,呼叫端的判斷式留著 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197` 對照 `:734` |
| `CLSM001` 戶號與姓名的 `Validating` | 兩個事件方法整段註解 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:707-719`、`:736-745` |
| 兩支 M 的「至少 3 個查詢條件」 | `ValidateErrList.Clear()` 與 `if (Show())` 都還在,永遠不成立 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:547-551`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:359-363` |
| `CLSM001` 存檔後重算庫存 | `AfterAdd` / `AfterUpdate` 事件仍掛在建構子上,方法體全註解;UI 端仍塞 `COM` 參數 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:92-124` 對照 `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75` |
| `CLSM002` 「拜訪記錄必須再補充」+ `UpdMemo` | 方法留成空殼,四個呼叫點全註解,`lenTopic` 永遠是 0 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134`、`:141-149`、`:595`、`:603`、`:609`、`:705` |
| `CLSM002` 修改既有拜訪重點 | 雙擊既有列進 else 分支後**什麼都不做**,使用者以為壞掉 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:598-604` |
| `CLSI001` 的 5 人員編白名單 | 整段註解,而且註解裡那個判斷式 `A != x \|\| A != y` 恆真(同 `cas.md` 記的錯誤) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:142-153`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:253-275` |
| `CLSI001` 的 `TRACE_CODE` / `INVEST_CODE` 查詢條件 | 兩段註解,畫面上的下拉還在 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:329-347` |
| `CLSI001_Ctl` 的三個取值方法 + `DoExecute` | 全部註解,PO 端對應的介面宣告也註解 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:45-91` |
| `CLSR001` 的 `uoptFUND` 選項群 | 控件還在 Designer 裡(`Visible = false`),事件方法整段註解 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:412-415`、`:559-569` |

### E7~E10 例外處理與取值方式 · 嚴重度 中

| # | 缺陷 | 影響 | 錨點 |
|---|---|---|---|
| E7 | `catch` 把 `ex.ToString()` 當成資料值塞進 `Result` 回給使用者:`CLSM001_PO` 五處(`:293`、`:338`、`:379`、`:424`、`:472`)、`CLSM002_PO`(`:328`)、`CLSB001_PO`(`:78`)、`CLSB002_PO`(`:68`、`:104`)、`CLSR001_PO`(`:90`、`:146`)、`CLSR002_PO`(`:162`) | 使用者看到完整 .NET 堆疊字串,真正的錯誤沒被歸類。反過來 `CLSI001_PO` 回固定的「執行失敗,請檢查」又什麼線索都沒有——**同模組兩種極端** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:293`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:390` |
| E8 | `CLSM002_PO` 七個 `After*` 事件全是 `throw new ApplicationException("")` —— **空訊息** | 跳號註記寫失敗時使用者只看到空白訊息,而且四眼動作整個 rollback,現場查不出原因(同 `cas.md 附錄 E.3` 的 `CASM001_PO`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:348`、`:356`、`:363`、`:370`、`:381`、`:388`、`:395` |
| E9 | **靠位置取值,沒有長度檢查**:兩支 M 的 Ctl 取 `Result[0]`;`CLSB002` UI 取 `Result[0]` **與 `Result[1]`**(`Query` 失敗時只有 1 列 → 直接爆);`CLSR001_PO` 取 `Parameters[0]` 當 `USERID`;兩支 R 的 Ctl 取 `ReportParameters[0]`;`CLSB002_PO` 取 `row[0]` / `row[1]` **靠欄位順序**;`CLSI001` 取 `GetEMP_INFO` 回傳字串的 `Split(',')[1]` | `CLS012` 改欄位順序兩個參數就對調;參數順序改了就取錯值 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM001_Ctl.cs:62-65`、`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM002_Ctl.cs:62-65`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:52-53`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:97-98`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:139`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:121-124` |
| E9b | `ex.Message.Split(':')[1]` 再 `Substring(0, msg.IndexOf("ORA-"))`,**兩個字串操作都沒防呆**(沒有冒號、或找不到 `ORA-` 就在 `catch` 裡再爆一次);兩處是複製品 | 真正的 SP 業務訊息被二次例外蓋掉 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:73`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:85-86` |
| E10 | **有訊息但沒有 `return` / `Cancel`**:`udatACT_CALL_DATE_Validating` 對「預先維護」與「逾 30 天」都跳訊息卻不設 `e.Cancel`;實際靠 `DoValidate` 再擋一次,**同一條規則兩份實作**。另外 `GetSAL_CD` 失敗時只跳訊息、`blnCanKeyIn` 保持 false | 改一邊漏一邊會出現「提醒了卻存得進去」;DB 連不上時所有人都變成不能建檔,訊息是 SQL 例外文字 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:284-287` |

### E11 「第 6 與第 9 項要鎖住客戶等級」這段程式走不到 · 嚴重度 中

```
if (RptSort.ContainsKey(uoptREPORT_TYPE.CheckedIndex))
{
    …
    else
    {
        //要算未過試用期是否達成或交通費, 所以以下條件不能用
        ucomCUS_LV.Enabled = (CheckedIndex != 6) && (CheckedIndex != 9);
        …
    }
}
```

`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:361-379`。`RptSort` 只註冊了 key `0` / `1` / `2` / `3` / `4` / `8`(`:227-232`),**`6` 與 `9` 不在裡面**,所以 `ContainsKey` 為 false,整個區塊被跳過——註解寫得很清楚要鎖住的那兩項,恰好是唯一鎖不住的兩項。

**影響**:選「未過試用期」或「交通費明細」時客戶等級下拉仍可選,選了會被帶進 SQL 當過濾條件(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:807`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1471`),算出來的「是否達標」與「交通費合計」會少算。

### E13 停損點永遠顯示不出來 · 嚴重度 中

```
if (!row.IsNEED_SIZENull()  && row.NEED_SIZE  > 0) unumNEED_SIZE.Value  = row.NEED_SIZE;
if (!row.IsINV_LIMITNull()  && row.INV_LIMIT  > 0) unumINV_LIMIT.Value  = row.INV_LIMIT;
if (!row.IsSTOP_GAINNull()  && row.STOP_GAIN  > 0) unumSTOP_GAIN.Value  = row.STOP_GAIN;
if (!row.IsSTOP_LOSSNull()  && row.STOP_LOSS  < 0) unumSTOP_LOSS.Value  = row.STOP_LOSS;
```

`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:463-466`。四行只有最後一行是 `< 0`。而存檔那側(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:111-114`)四個欄位一律照畫面值存、空值存 0,**沒有把停損點轉成負數**。

**影響**:停損點存成正數(例如 10 代表 10%)時,再次開啟維護頁該欄位是空白的;使用者若直接存檔就會把它洗成 0。這是「查得到、看不到、一存就掉」的典型。

### E12 · E14~E27 其餘十四條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12 | `GetRpt0A` 把 `AddParam(…, "A", "CUS_LV")` **呼叫了兩次**(`:218` 與 `:232`);12 支 `GetRpt*` 只有這一支這樣 | `AddParam` 同時會加繫結參數,等於同名參數加兩次、條件在 `strCLS` 的兩個 `{0}` 佔位共出現四次。是否丟 Oracle 錯誤要實測,至少是多餘的 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:218`、`:232` | 中 |
| E14 | `SetPermissionInfo(this.ProcessVDB)` 在 `this.ProcessVDB = new …` **之前**呼叫,全庫其他地方都是先 new 再設(註解寫「新vdb就要用」) | 兩支 B 的 PO 都讀 `PermissionInfo.Rows[0].UserID`:框架若沒補就是 index out of range,若有補這兩行就是多餘的——兩種情況都該修 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:29-32`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:41-44` 對照 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:38-40` | 中 |
| E15 | `CLSR002_PO.GetData` 用 Reflection 依用戶端參數叫 `"GetRpt" + RptType`,而且帶 `BindingFlags.NonPublic` | 任何簽名相符的私有方法都成為可呼叫入口;傳不存在的值則是 `NullReferenceException` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:155-157` | 中 |
| E16 | `Convert.ToDecimal(Result[0].ReturnMessage.PadLeft(1, '1'))` —— `PadLeft(1,'1')` 只在字串長度為 0 時補,等於「查不到匯率」被寫成「匯率 = 1」 | 預計申購金額(台幣)直接等於原幣金額,沒有任何提示 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:65` | 中 |
| E17 | `CLSI001p0` 塞值 19 行**完全沒有 `IsXxxNull()` 保護**,而 `EST_CALL_DATE` / `ACT_CALL_DATE` / `TRAFFIC_FEE` / `BF_NO` 在 xsd 都是可空的 | 任一為 NULL 時雙擊明細就丟 `StrongTypingException`;對照 `CLSM001` 每一欄都有檢查 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89` | 中 |
| E18 | `CLSM001p0`「受益人基本資料」在 `CLSM001` 的呼叫點已被註解,只剩 `CLSM002` 一個活呼叫;而且它的 grid 顯示 `ID_NO`/`BF_NO`/`PR_NAME`/`MAIL_ADDR`,資料來源卻是 `vdb.UIView.CLS001`(潛在客戶) | 視窗標題與實際內容對不起來 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001p0.cs:62-63` 對照 `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:181` | 低 |
| E19 | `CLSM002p2` 的 `this.DialogResult = DialogResult.OK;` **寫在 foreach 迴圈裡** | 一個都沒勾時視窗不關、也不提示,使用者以為壞掉 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:101-107` | 低 |
| E20 | `SetParameterValue("FUND", …挑選的基金清單…)` 下一行立刻被 `SetParameterValue("FUND", "境內基金")` 覆蓋 | 報表表頭永遠印「境內基金」,看不到挑了哪幾檔 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:359-360` | 低 |
| E21 | 兩支 B 的四個 `CustomTransfer*` 各自 `as` 出 `view` / `model` 兩個區域變數就直接 `return`,沒搬任何資料 | B 型只靠 `Util` 溝通所以是「對的」,但看起來像沒寫完 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB001_Ctl.cs:46-59`、`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs:53-66` | 低 |
| E22 | `CLSM001Model.xsd` 的 `CLS0021`(4 欄)全庫零引用,欄位與同檔的 `CLS002` 結果集幾乎一樣 | 改版殘留,搜尋時誤導 | `Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM001Model.xsd` | 低 |
| E23 | `CLSR001RPS1` 沒有任何畫面入口(六個選項的 `RptNumber` 值域是 {2,3,4,5,6,7,8,9}) | 22 支 rpt 裡唯一載不到的一支 | §7.1 · `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:191-196` | 低 |
| E24 | `SetCLS001Data` 的 `if (!row.IsID_NONull()) …` 連續寫兩次 | 無功能影響,顯示這段靠複製貼上維護(同 `architecture.md §2.7` 記的 `CASM001.cs:129`/`:136`) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:202-205` | 低 |
| E25 | **本模組沒有非 UTF-8 的來源檔**:兩個專案底下所有 `.cs`/`.xsd`/`.config`/`.csproj`/`.resx` 逐檔 UTF-8 解碼,0 支失敗 | 對照 `bms.md 附錄 E18` 的 BMS 有一支 Big5,CLS 這邊乾淨 | — | — |
| E26 | 「讀快照還是讀現值」有**兩份實作**,而且已經漂移(部門來源、`NVL` 處理、日期繫結方式都不同,見 §7.2 的表) | 查詢畫面與報表看到的客戶清單可能不一致,而使用者認為兩邊應該一樣 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-273` 對照 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105` | 中 |
| E27 | 沒給實際拜訪日迄日時,`ISHIS` 的上限寫死 `'29991231'`,而且是字串串接 | 語意正確,但寫死哨兵值與串接並存(同 E4) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:187` | 低 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。7 支畫面、5 張表、22 支 rpt 全數涵蓋;釐清 `CLS001`~`CLS005` 與 `CLS001A`/`CLS002A` 的歸屬、`CLSB002` 六層不齊的真因、`CLS001H` 快照機制。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 125 · 圖 5 · 表格 67 · 程式錨點 401 · § 連結 46 · 引用檢查：畫面 13（缺 0） · Table 29（缺 0） · Report 22（缺 0） · 結果集 15（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
