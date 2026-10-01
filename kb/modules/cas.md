<!-- 由 tools/build_copilot_kb.py 從 modules/cas.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS CAS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)目前由表名、欄位中文名(`msdata:Caption`)與少數彈出視窗標題**推測**,待選單表 / 對照表回填。ATLAS 沒有把畫面中文名放進版控,16 支畫面裡只有 4 支彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼(`G3` / `GA` / `G17` / `X01`…)、銷售機構代碼(`A0901`)、員工代號白名單、`USAGE = '3'` 等為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:標記的表同時服務 CRM / TMK / CLS / DSM(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CAS 管「代銷通路」這件事的四個面向——通路上的人、拜訪這些人的紀錄、給業務員的業績目標,以及業績該怎麼分帳。**

推測依據有四條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 表名與欄位中文名 | `CAS003A` 的欄位是「潛在客戶序號」「經辨/理專姓名」「職務」「理專等級代碼」;`CAS004A` / `CAS005A` 是「銷售機構代碼」「業務員代碼」「分配比率％」;`CAS001A` / `CAS002A` 是「業績年度」「境外代銷手續費加項」 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:19-21`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:39-74`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:25-46` |
| 彈出視窗標題 | 「代銷組客戶拜訪主管明細表」「代銷客戶拜訪記錄查詢作業」「業務員複製」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.Designer.cs:2613`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001p0.Designer.cs:2588`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.Designer.cs:557` |
| 報表中文名 | 「訪談報告─親訪」「代銷─客戶拜訪統計表」「銷售機構銷售總表」「銷售機構期間收入統計表」「代銷退休管家庫存明細表」 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:92-109`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:179`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:295`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:191` |
| 郵件主旨 | 「代銷組客戶拜訪主管意見回復作業須回復事項」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:328` |

「CAS」三個字母本身的展開在 repo 裡找不到定義,**不要猜**。本文一律用「代銷通路」描述它的業務範圍,這是從上表推出來的,不是官方名稱。

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 通路與人員 | 銷售機構(銀行分行 / 保經代)及其底下的經辦、理專名單、等級、推薦產品類型 | `CASM001` | `CRM003A`〔共用〕+ `CAS003A` |
| B 拜訪作業 | 業務員去拜訪這些通路的紀錄:預計 / 實際拜訪日、拜訪重點、追蹤事項、主管意見與回覆 | `CASM002`、`CASI001`、`CASB001` | `CLS001A` + `CLS002A`〔共用〕 |
| C 業績目標 | 每位業務員每年 / 每月的目標:境外代銷手續費加項、營業收入、定期定額戶數、百萬戶數 | `CASM003`、`CASM006` | `CAS001A` + `CAS002A`、`DSM001A` + `DSM002A`〔共用〕 |
| D 業績分配 | 同一個銷售機構(甚至同一個受益人戶號)的業績,要按什麼比率分給哪幾位業務員 | `CASM004`、`CASM005` | `CAS004A`、`CAS005A` |
| E 報表 | 上面四條線的統計與明細輸出 | `CASR001`–`CASR008` | 全部來自版控外的 SP |

### 0.2 這模組最反直覺的一件事

**16 支畫面、10 張表,但只有 5 張表是 CAS 自己的;而且三支維護畫面的「主檔」都不是自己的表。**

| 畫面 | 主檔 | 主檔屬於 | 明細 | 明細屬於 |
|---|---|---|---|---|
| `CASM001` | `CRM003A` | **CRM / TMK** | `CAS003A` | CAS |
| `CASM002` | `CLS001A` | **CLS** | `CLS002A` | **CLS** |
| `CASM003` | `CAS001A` | CAS | `CAS002A` | CAS |
| `CASM004` | `CAS004A` | CAS | —(無明細) | — |
| `CASM005` | `CAS005A` | CAS | —(無明細) | — |
| `CASM006` | `DSM001A` | **DSM** | `DSM002A` | **DSM** |

也就是說 **CAS 有一半的維護功能,是在別人的表上開第二個入口**。這件事的後果貫穿全文:

1. **改表要跨模組回歸**。`CRM003A` 同時被 `CRMM003` 當主檔;`DSM001A` / `DSM002A` 同時被 `DSMM001` 當主檔。加欄位、改型別、改 PK,兩邊的 xsd 與 Designer 都要重生(見 §8)。

2. **同一張表,兩個入口的可見範圍不同**。`CASM002` 與 `CASI001` 都硬加 `USAGE = '3'` 過濾,`CASB001` 沒有;`CASM006` 只看 8 個部門,`DSMM001` 沒有這條限制。同一筆資料在 A 畫面看得到、B 畫面看不到是**設計如此**,不是 bug——但沒有任何地方寫下來(見 §5、§6、§8)。

3. **四眼欄位的語意由別的模組決定**。`CLS001A` 的 `STATUS` 被 `CASB001` 直接 UPDATE 成 `'301'`,繞過四眼引擎(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341`)。CLS 模組自己的畫面如果依賴狀態機,會看到不合流程的狀態值。

### 0.3 不管什麼

以下**不在** CAS 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(客戶)基本資料 | BMS | `BMS001A` 只被 join 取 `BF_NAME` 與開戶日,從不寫入;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:299-300` |
| 員工主檔、部門、離職日 | COD | `COD009` 全部是 `LEFT JOIN` 或 `SELECT`,無任何 INSERT/UPDATE;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:221-222` |
| 代碼對照(理專等級、推薦產品類型、拜訪方式) | COD / CTL | `COD006A` 依 `CODE_SORT` 分類、`CTL014` 依 `SOURCETYPE` 分類,都只讀;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 銷售機構名稱主檔 | OFD | `OFD068A` 只被 join 取名稱;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:371-372` |
| 實際的申購 / 贖回交易 | OFD / EC | CAS 的表裡沒有任何交易金額欄位;報表的交易數字全部來自版控外的 SP |
| 業績的實際計算 | **不明** | `CAS001A` / `DSM001A` 只存「目標」,`CAS004A` / `CAS005A` 只存「比率」。真正拿這些比率去分帳的程式不在 CAS 內,repo 裡也找不到。**假設**:在版控外的 SP 或別的模組,依據是本模組沒有任何一支程式讀 `DIV_PCT` 去做計算 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 代銷業務員 | 填拜訪單(`CASM002`)、查自己的拜訪紀錄(`CASI001`) | `CASI001` 用登入者的員工代號當強制條件,只看得到自己的;`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:198-209` |
| 主管 | 批次勾選拜訪單、寫主管意見、寄信要求業務回覆(`CASB001`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342` |
| 5 位特定人員 | 不受「只看自己」限制,看得到全部拜訪紀錄 | 員工代號寫死在 SQL 組字串裡;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206`〔客戶特定〕 |
| 代銷組管理人員 | 維護通路人員(`CASM001`)、設定業績目標(`CASM003` / `CASM006`)與分配比率(`CASM004` / `CASM005`) | 這幾支都是標準四眼維護畫面,權限由框架的功能權限決定,程式內看不到 |
| 覆核者 | 對上述維護做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |

**注意:除了 `CASI001` 那條寫死的員工白名單之外,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。

### 0.5 全域開關

repo 內**沒有**任何 CAS 專屬的設定檔開關。`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔與主鍵,給框架做 grid 的 PK 檢查用 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:28`(`CASM001`)、`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:37`(`CASM002`)、`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:44-45`(`CASM003`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:30` |
| `formstyle` | `CASB001` / `CASI001` 宣告為 `OneStep`;報表側全部 `Report` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:16`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/App.config:16` |

兩個要記住的:

- **`CASM001` 的 `detailtable` 那行是被註解掉的**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:29`),但 PO 確實宣告了明細表(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:47`)。畫面靠 `m_PkeyNotInMaster` 手動補明細 PK(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:129`),不是靠設定。

- **`CASM002` 根本沒宣告 `detailtable`**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:34-40`),但 PO 有(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:47`)。設定檔與程式不一致,以程式為準。

`TargetFramework` 側只有一個註記值得記:`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:74` 宣告 `.NETFramework,Version=v4.8`,而 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:5` 留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡——這批檔案在升版時被逐檔改過,不是整批 retarget。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CAS 模組全景：通路主檔、拜訪作業、業績目標與分配、報表四條線，以及十張表的歸屬
圖中文字:① 通路與人員主檔（資料來源在別的模組） / CASM001 / 銷售機構+經辦 CRM003A / CRM003A〔共用〕 / 主檔屬 CRM／TMK / CAS003A / 經辦明細 本模組自有 / COD009 COD006A / 員工／代碼 外部 / ② 拜訪作業（主檔屬 CLS） / CASM002 / 拜訪單維護 CLS001A / CLS001A CLS002A / 〔共用〕主檔屬 CLS / CASI001 / 拜訪紀錄查詢 唯讀 / CASB001 / 主管批次回覆+寄信 / ③ 業績目標與分配比率 / CASM003 / 年月手續費加項 CAS001A / CASM006 / 年月業績目標 DSM001A / CASM004 / 機構×業務員 CAS004A / CASM005 / 再加戶號 CAS005A / ④ 報表（七層，資料全在版控外的 SP） / CASR001 / 訪談報告6式 / CASR002 / 業務人員統計 Excel / CASR003 CASR007 / 機構銷售／定額契約 / CASR004 CASR008 / 機構期間收入／排行 / CASR005 CASR006 / 退休管家／每日申購 / ⑤ 資料來源：10 張表只有 5 張是 CAS 自有 / CAS001A CAS002A / 年／月手續費加項 / CAS003A / 經辦明細 / CAS004A CAS005A / 分配比率 / CRM003A CLS001A CLS002A / DSM001A DSM002A 借用
```

*圖:圖 1 CAS 全景。橘框=本模組的維護入口；灰虛框=借用別模組的表或唯讀來源；黑框=無原始碼的外部代碼表；橘虛框=行為含寫死值〔客戶特定〕。四條線彼此只靠表相連，沒有程式呼叫關係。*

看圖的三個重點:

1. **四條業務線之間沒有程式呼叫關係。** `CASM001` 不會叫 `CASM002`,`CASM003` 不會叫 `CASM004`。它們只透過表相連:`CASM002` 的主檔 SQL 去 join `CRM003A`(`CASM001` 維護的)與 `CAS004A`(`CASM004` 維護的),`CASI001` 也是。所以改 `CASM004` 的欄位,會打到 `CASM002` 的查詢結果(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224`)。

2. **報表那一排與上面三排完全脫鉤。** 8 支 R 畫面沒有一支引用 CAS 的任何 PO,資料全部來自 `S_TA_CASRnnn_GET` 這類版控外的 SP(§7)。也就是說**報表看到的數字,跟維護畫面寫進去的值之間的關係,在 repo 內是斷的**。

3. **只有 `CASB001` 會寫別條線的資料。** 它直接 UPDATE `CLS002A`,而且把四眼欄位一起蓋掉(§6)。

### 1.2 資料表關係

見 §2 節首的圖。三組主明細、兩張非實體結果集、五張外部唯讀表。要記住的是:

- **主明細的綁定靠 `dataid`,不是靠外鍵。** 同一次 EVA 生命週期內主檔與所有明細共用一個 `Guid`(`architecture.md §3.3`),所以主檔與明細一定一起送審、一起覆核。

- **`CAS004A` 與 `CAS005A` 沒有明細表。** 它們是單表四眼畫面,`DetailTable` 完全沒宣告(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:42`)。

- **`CLS002A` 實際上是 1:1 的續頁,不是真明細。** `CASM002` 存檔時只取第一列(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:103-110`),沒有列數概念。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接 `new` 一個 `_Pxy` 打過去 | 對話框(不是訊息清單) |
| 4 主檔欄位回填明細 | `SetMasterToDetail()` | 不會失敗,但漏欄位會讓明細 PK 是空的 |
| 5 PO 的 `Before*` | `BeforeAdd` 取號、`BeforeSelect` 換 SQL | 例外 → 整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `After*` | 只有 `CASM001` / `CASM002` 有 | `throw` → 整筆回滾 |

**第 1 到第 4 階段全部在用戶端。**伺服器端沒有任何一支程式重驗這些規則,所以任何繞過 UI 的呼叫路徑(例如直接 `new CASM001_Pxy()`)都不受這些卡控保護。

### 1.4 批次 / 報表資料流

見 §7 節首的圖。兩件事:

- **報表是兩條獨立往返**:`GetReportData` 拿資料、`GetReportObject` 拿 `.rpt` 檔的 byte。後者的類別名由用戶端傳過來,伺服器照單全收(`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR005_Ctl.cs:61-62`,與 `architecture.md §6.5` 描述一致)。

- **批次只有一支**(`CASB001`),而且沒有 WindowsService。它是使用者按按鈕觸發的「批次」,不是排程(§6)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,所以以下是**推測**的作業順序,依據是資料相依:某張表要有資料,前一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 年度開始前 | 代銷組管理 | 設定各業務員的年度目標與月分配 | `CASM003`、`CASM006` | 員工要先在 `COD009` 存在 |
| 年度開始前 | 代銷組管理 | 設定各銷售機構的業績分配比率 | `CASM004`、`CASM005` | 機構要先在 `OFD068A` 存在 |
| 平時 | 代銷組管理 | 新增 / 維護通路上的經辦與理專 | `CASM001` | — |
| 平時(拜訪後) | 業務員 | 填拜訪單 | `CASM002` | 通路要先在 `CASM001` 建好(`PR_NO`) |
| 平時 | 業務員 | 查自己的拜訪紀錄 | `CASI001` | — |
| 定期(推測每週 / 每月) | 主管 | 批次勾選、寫主管意見、寄信要求回覆 | `CASB001` | 拜訪單要先存在 |
| 月結 / 期間結束後 | 代銷組管理 | 出各式統計與明細報表 | `CASR001`–`CASR008` | 版控外的 SP 決定 |

**假設**:`CASB001` 的頻率。依據是它的查詢條件預設值是「未閱」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:42`),而且每次重整都會重設成「未閱」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:60`)——這是「把積壓的未處理清掉」的用法,不是「查歷史」的用法。實際頻率要問使用者。

## 2. 資料模型

```text
[圖] CAS 十張表的主明細關係、主鍵組成，以及外部唯讀表
圖中文字:本模組自有（5 張） / CAS001A / PK QUO_YEAR+EMP_NO / CAS002A / +QUO_YYMM 月明細 / CAS003A / PK PR_NO+STAFF_NAME / CAS004A / PK YYMM+3 碼機構+人 / CAS005A / 同上再加 BF_NO / CAS004A_OVER / 結果集 非實體表 / 借用他模組（5 張，改動要看 §8） / CRM003A〔共用〕 / PK PR_NO · CRM TMK / CLS001A〔共用〕 / PK CALL_RPT_NO · CLS / CLS002A〔共用〕 / 同單號 1:1 續頁 / DSM001A DSM002A / 年／月目標 · DSM / 四眼欄位齊不齊（見 §2.2） / 有全套 13 欄 / CAS003A CLS001A CLS002A CRM003A / 只有日期欄有 Caption / CAS001A/2A/4A/5A DSM001A/2A / DATAFLAG 每張都有 / 樂觀鎖唯一比對欄 / 外部唯讀（join 進來，不屬本模組） / COD009 / 員工／部門／離職日 / COD006A / CODE_SORT 代碼說明 / CTL014 / SOURCETYPE 下拉 / OFD068A / 銷售機構名稱 / BMS001A / 受益人資料
```

*圖:圖 2 資料模型。橘框=主檔；灰虛框=借用或非實體表；黑框=外部唯讀表。實線箭頭=主明細（同一次 EVA 一起送審）；虛線=同一支畫面內的弱關聯。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`)。CAS 六支 M 畫面的宣告:

| 畫面 | `MasterTable` | `DetailTable` | 錨點 |
|---|---|---|---|
| `CASM001` | `CRM003A` | `CAS003A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:46-47` |
| `CASM002` | `CLS001A` | `CLS002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:46-47` |
| `CASM003` | `CAS001A` | `CAS002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:33-34` |
| `CASM004` | `CAS004A` | **無** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:42` |
| `CASM005` | `CAS005A` | **無** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:39-43` |
| `CASM006` | `DSM001A` | `DSM002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33` |

`CASI001` 與 `CASB001` 的 `MasterTable` 那行**是被註解掉的**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:42`),兩支都是裸 DAO,不繼承 `BaseEVADaoPO`。掃描器把那行註解當宣告,所以母體會回報一個不存在的主檔 `OFD701`——這個誤判 `architecture.md §6.3` 已經記過,本文一律以程式為準。

八支 R 畫面的 PO 完全沒有 `xTableMapping`,它們的「表」是 SP 回來的結果集形狀(§7)。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源,兩邊一致:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。

| 表 | 主鍵(xsd) | 主鍵(App.config) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `CAS001A` | `QUO_YEAR` + `EMP_NO` | `QUO_YEAR,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:200-204` |
| `CAS002A` | `QUO_YEAR` + `QUO_YYMM` + `EMP_NO` | `QUO_YEAR,EMP_NO,QUO_YYMM` | ✔(順序不同,不影響) | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:205-210` |
| `CAS003A` | `PR_NO` + `STAFF_NAME` | (被註解) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:133-137` |
| `CAS004A` | `YYMM` + `EMP_NO` + `AGENT_CODE` + `AGENT_ID` | `YYMM,AGENT_ID,AGENT_CODE,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:155-161` |
| `CAS005A` | `YYMM` + `EMP_NO` + `AGENT_CODE` + `AGENT_ID` + `BF_NO` | `YYMM,AGENT_ID,AGENT_CODE,EMP_NO,BF_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM005Model.xsd:164-171` |
| `CLS001A` | `CALL_RPT_NO` | `CALL_RPT_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:185-188` |
| `CLS002A` | `CALL_RPT_NO` | (未宣告) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:189-192` |
| `CRM003A` | `PR_NO` | `PR_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:138-141` |
| `DSM001A` | `QUO_YEAR` + `EMP_NO` | `QUO_YEAR,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:211-215` |
| `DSM002A` | `QUO_YEAR` + `QUO_YYMM` + `EMP_NO` | (未宣告) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:216-221` |

**`CLS002A` 的 PK 只有 `CALL_RPT_NO`,跟主檔一樣。**這證實它是 1:1 續頁而不是明細——一張拜訪單只會有一列主管意見。程式也是這樣寫的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:103-110`)。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 有中文名的欄 | 說明 |
|---|---|---|---|
| `CAS003A` | ✔ | 全部 13 欄都有 Caption | 最完整的一張 |
| `CLS001A` | ✔ | 全部 13 欄都有 Caption | 連 `DATAFLAG` 都有「資料異動碼」 |
| `CRM003A` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `CLS002A` | ✔ | 在 `CASM002Model.xsd` 內沒有 | 同一張表在 `CASB001Model.xsd` 內也沒有 |
| `CAS001A` `CAS002A` `CAS004A` `CAS005A` `DSM001A` `DSM002A` | ✔ | **一個都沒有** | 六張表的四眼欄位全部無中文名 |

**結論:10 張表全部有完整四眼欄位,但只有 2 張表的四眼欄位填了中文名。**這直接對應 `architecture.md §5.5` 說的「只有 53% 的欄位有 Caption」——CAS 這邊的缺口集中在四眼欄位上。

`DATAFLAG` 每張表都有,型別一律 `xs:base64Binary`,而且標了 `msdata:ReadOnly="true"`(例:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:102`)。它是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

以下中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**。空白代表該 xsd 沒有填。

#### `CAS001A` — 年度業績目標主檔(20 欄,`CASM003` 主檔)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y | 四眼批次識別 `Guid` |
| `QUO_YEAR` | 業績年度 | string(4) | — | PK |
| `EMP_NO` | 員工代碼 | string(10) | — | PK |
| `BOUNS_ST_YYMM` | 起算年月 | string(6) | Y | 必須與業績年度同年(§4.3) |
| `OFD_INC_ALLOT_FEE_TOT` | 境外代銷手續費加項 | decimal | Y | 預設 0;必須 > 0 且等於明細總和 |
| `EMP_NAME` | 員工姓名 | string | Y | **衍生欄**,`COD009` join 進來,不落地 |
| 其餘 13 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:15-106`。

#### `CAS002A` — 月業績目標明細(19 欄,`CASM003` 明細)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y |  |
| `QUO_YEAR` | 業績年度 | string(4) | — | PK,由主檔回填 |
| `EMP_NO` | 員工代碼 | string(10) | — | PK,由主檔回填 |
| `QUO_YYMM` | 業績年月 | string(6) | — | PK,由「月分配」鈕產生 |
| `OFD_INC_ALLOT_FEE` | 境外代銷手續費加項 | decimal | Y | 預設 0;必須 > 0 |
| 其餘 14 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |

**沒有 `EMP_NAME`。**明細不 join `COD009`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:216-223`)。

#### `CAS003A` — 通路經辦 / 理專明細(35 欄,`CASM001` 明細)

| 欄位 | 中文名 | 型別 | 可空 |
|---|---|---|---|
| `DATAID` |  | string | Y |
| `PR_NO` | 潛在客戶序號 | string | — |
| `STAFF_NAME` | 經辨/理專姓名 | string | — |
| `STAFF_POST` | 職務 | string | Y |
| `STAFF_POSITION` | 經辨職稱 | string | Y |
| `SEX` | 性別 | string | Y |
| `MGR_NAME` | 主管姓名 | string | Y |
| `MGR_POSITION` | 主管職稱 | string | Y |
| `OF_TEL_AREA` | 電話區域碼 | string | Y |
| `OF_TEL` | 電話號碼 | string | Y |
| `FAX_TEL_AREA` | 傳真電話區域碼 | string | Y |
| `FAX_TEL` | 傳真電話 | string | Y |
| `CELL_PHONE` | 行動電話 | string | Y |
| `EMAIL` |  | string | Y |
| `INVEST_CODE` | 投資特性 | string | Y |
| `STAFF_TYPE` | 理專等級代碼 | string | Y |
| `INTRO_TYPE` | 理專推薦產品類型 | string | Y |
| `SEND_FUND_YN` | 傳送基金相關資料 | string | Y |
| `MEMO` | 備註 | string | Y |
| `STATUS` | 資料識別碼 | string | Y |
| `CREATEID` / `CREATEDATE` | 資料建立者 / 日期 | string / dateTime | Y |
| `UPDATEID` / `UPDATEDATE` | 最後修改者 / 日期 | string / dateTime | Y |
| `ENTRYID` / `ENTRYDATE` | 最後輸入者 / 日期 | string / dateTime | Y |
| `VERIFYID` | 資料確認者 | string | **—** |
| `VERIFYDATE` | 資料確認日期 | dateTime | Y |
| `APPROVEID` / `APPROVEDATE` | 資料覆核者 / 日期 | string / dateTime | Y |
| `REJECTID` / `REJECTDATE` | 資料退回者 / 日期 | string / dateTime | Y |
| `DATAFLAG` |  | base64Binary | Y |
| `STAFF_TYPE_DESCRP` | 理專等級代碼說明 | string | Y |
| `INTRO_TYPE_DESCRP` | 理專推薦產品類型說明代碼 | string | Y |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:15-55`。

三件要注意的:

1. **`STATUS` 的 Caption 寫成「資料識別碼」**,那是 `DATAID` 的意思,不是狀態。這個錯字在 `CLS001A` 也一樣(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:45`)。看 Caption 判斷欄位用途會判錯。

2. **`VERIFYID` 是唯一沒有 `minOccurs="0"` 的四眼欄位**(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:44`),也就是 DataSet 層要求它不可為 null。新增一筆還沒驗證時它是什麼值,程式裡看不到——由框架 DLL 決定(**假設**:空字串,依據是 `architecture.md §3.5` 的 13 欄一律送值)。

3. **末兩欄 `*_DESCRP` 是畫面計算欄**,由 SQL 的 `CODE_DESCRP AS …` 產生(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:317-318`),不落地。

#### `CAS004A` — 機構業務員分配比率(26 欄,`CASM004` 主檔)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y |  |
| `YYMM` | 業績年月 | string(6) | — | PK |
| `AGENT_ID` | 銷售機構區別碼 | string(6) | — | PK,下拉來源代碼 `062` |
| `AGENT_CODE` | 銷售機構代碼 | string(9) | — | PK |
| `EMP_NO` | 業務員代碼 | string(10) | — | PK |
| `AREA_CODE` | 區域別 | string(6) | Y | 下拉來源代碼 `467` |
| `DEPT_CODE` | 組別 | string(6) | Y | 下拉來源代碼 `468` |
| `MRG_YN` | 組長別 | string(6) | Y | 下拉來源代碼 `473`,新增預設 `N` |
| `DIV_PCT` | 分配比率％ | decimal | Y | 必須 > 0;同組合加總不得 > 100 |
| `START_DATE` | 開始日期 | string(8) | Y | 預設等於業績年月 |
| 其餘 14 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |
| `AGENT_NAME` | 銷售機構名稱 | string | Y | **衍生欄**,`OFD068A` join |
| `EMP_NAME` | 銷售員姓名 | string | Y | **衍生欄**,`COD009` join |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:15-142`。

#### `CAS005A` — 受益人層分配比率(28 欄,`CASM005` 主檔)

與 `CAS004A` 逐欄相同,只多兩欄:

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `BF_NO` | 受益人戶號 | string(10) | — | **第 5 個 PK 欄** |
| `BF_NAME` | 受益人姓名 | string | Y | **衍生欄**,`BMS001A` join |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM005Model.xsd:15-150`。注意 `AGENT_NAME` 在這裡取的是 `OFD068A` 的 `AGENT_NAME` 欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:283`),而 `CASM004` 取的是 `AGENT_SHNM` 欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:361`)。**同一個概念兩張畫面取不同來源欄,顯示出來的機構名稱可能不一樣**(附錄 E)。

#### 借用的五張表 — 只列本模組會動到的欄

`CRM003A`(`CASM001` 主檔,xsd 內 69 欄,索引記 72 欄):

| 本模組會寫的欄 | 中文名 | 誰寫 |
|---|---|---|
| `PR_NO` | 潛在客戶序號 | `BeforeAdd` 取流水號 |
| `USAGE` | 用途別 | UI 寫死 `"3"` |
| `ID_NO` `PR_NAME` `EMP_NO1` `CNT_PERSON` `POSITION_DESC` `EMAIL` | 銷售機構金資 / 銷售機構 / 員工編號 / 聯絡人 / 職稱 / — | `SetMasterToDetail` |
| `CUST_CLASS1` `CUST_CLASS2` `DES_MAKER` | 總行等級 / 分行等級 / 決策者 | 同上 |
| `ADDR_CODE1` 與 12 個 `MAIL_*` | 通訊地址各段 | 同上,由 `ucAddress` 控件拆解 |
| `OF_TEL_AREA` `OF_TEL` `FAX_TEL_AREA` `FAX_TEL` | 公司電話 / 傳真 | 同上,`OF_TEL` 會把分機用 `#` 串在一起 |
| `AREA_CODE` `DEPT_CODE` `SEND_INFO_YN` | 區域別 / 組別 / 發文通知 | 同上 |

錨點:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:45-95`。**`CRM003A` 其餘約 50 欄本模組不碰**,包括 `BF_NO`、`CUST_TYPE`、`REJ_SELL_*` 那一整組拒絕行銷旗標——但 `CUST_TYPE` 會被讀來擋刪除(§4.1)。

`CLS001A`(`CASM002` 主檔,xsd 內 59 欄;`CASI001` 版 78 欄、`CASB001` 版 74 欄):**同一張表在三支畫面的 xsd 裡欄位集合不同**,這是 `architecture.md §5.4` 說的「Model/View 不同構」在同模組內的加強版——連 Model 之間都不同構。三份 xsd 的差異:

| 只在某一份出現的欄 | 在哪一份 | 用途 |
|---|---|---|
| `CUST_WILL_DESCRP` `CUST_CLASS_DESCRP` | `CASM002Model` | 畫面計算欄 |
| `QUERY_EMP_NO` `CUST_CLASS` 與 9 個 `*_DESCRP` | `CASI001Model` | 查詢畫面的說明欄 |
| `ISCHECK` `EMP_NAME` 與 10 個 `*_DESCRP` | `CASB001Model` | 批次勾選欄與說明欄 |

`ISCHECK` 是 `xs:boolean` 且 `default="false"`(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:70`),**它不是資料庫欄位**,是批次畫面的勾選狀態。同一個 `ISCHECK` 也出現在 `CLS002A` 的定義裡(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:123`),但程式從來不用那一個。

`CLS002A`(`CASM002` 明細,25–26 欄):除 `DATAID` / `CALL_RPT_NO` 與 13 個四眼欄外,只有 9 個業務欄:

| 欄位 | 中文名(取自 `CASM002Model`) |
|---|---|
| `MGR_DESC` | 主管意見 |
| `CFM_USER1` | 主管1(小組長)閱 |
| `CFM_USER2` | 主管2(主管)閱 |
| `CONNECT_DESC` | 溝通事項 |
| `CONNECT_RE` | 業務需回覆否 |
| `ERR_DESC` | 異常狀況 |
| `EXEC_DESC` | 處理情形 |
| `SALES_CONNECT_DESC` | 業務回覆溝通事項 |
| `SALES_CONNECT_RE` | 業務已回覆 |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:85-93`。**這 9 欄就是 `CASB001` 批次更新的全部內容**(§6)。

`DSM001A` / `DSM002A`(`CASM006` 主明細,26 / 24 欄):結構與 `CAS001A` / `CAS002A` 完全平行,差別只在業務欄從 1 個變成 6 個。

| `DSM001A` 欄位 | 中文名 | `DSM002A` 對應欄 |
|---|---|---|
| `QUO_MGR_TOT` | 營業收入 | `QUO_MGR` |
| `QUO_RSP_NM_TOT` | 定期(不)定額戶數-目標 | `QUO_RSP_NM` |
| `QUO_RSP_LNM_TOT` | 定期(不)定額戶數-保守 | `QUO_RSP_LNM` |
| `QUO_RSP_AMT_TOT` | 定期(不)定額扣款成功金額 | `QUO_RSP_AMT` |
| `QUO_MIL_NA_TOT` | 新開百萬戶數 | `QUO_MIL_NA` |
| `QUO_MIL_A_TOT` | 單筆申購交易百萬戶數 | `QUO_MIL_A`(Caption 少了「數」) |

`DSM001A` 另有 `DEPT_NO`(部門代碼)一欄,是 `COD009` join 進來的衍生欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113`),不落地。錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:15-208`。

### 2.4 與其他模組共用的表

完整影響面在 §8。這裡只記歸屬:

| 表 | 屬於 | CAS 怎麼用 | 誰還在用 |
|---|---|---|---|
| `CRM003A` | CRM / TMK | `CASM001` 當主檔,增刪改;`CASM002` / `CASI001` / `CASB001` 唯讀 join | `CRMM003` |
| `CLS001A` | CLS | `CASM002` 當主檔增刪改;`CASI001` 唯讀;`CASB001` 讀 | CLS 模組 |
| `CLS002A` | CLS | `CASM002` 當明細;`CASB001` **直接 UPDATE** | CLS 模組 |
| `DSM001A` | DSM | `CASM006` 當主檔 | `DSMM001` |
| `DSM002A` | DSM | `CASM006` 當明細 | `DSMM001` |

外部唯讀(只 join,不寫):`COD009`(員工)、`COD006A`(代碼說明)、`CTL014`(下拉值)、`OFD068A`(銷售機構名)、`BMS001A`(受益人)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`architecture.md §3.10` 從全庫 SQL 字面量反推,**假設** `EVAStatusCode` 的實際值是單字元 `'0'`–`'9'`。**CAS 提供一個直接的反證:**

```
ResultVDB.DataEntity.CLS001A.STATUSColumn.DefaultValue = "301";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406` 與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:229`,以及批次真的寫進 DB 的那一行 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341`。

三邊互相吻合:

| 證據 | 內容 |
|---|---|
| xsd 宣告 | `STATUS` 一律 `xs:string` `maxLength = 3`(例 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:47-52`) |
| 程式寫入 | 三處都寫 `"301"` |
| 對照 `architecture.md §3.10` | 該節的單字元假設與此不符 |

**結論:`STATUS` 是 3 碼字串,不是單字元。**`"301"` 代表什麼語意,repo 內找不到——`EVAStatusCode` 常數在框架 DLL 裡(無原始碼,從呼叫端反推)。從 `CASB001` 的用法(批次把主管已閱的單子設成這個值,同時把 `APPROVEID` / `APPROVEDATE` 一起寫進去)**推測**它屬於 `Approve*` 那一族,也就是「已覆核」。這是**假設**,要確定得查資料庫或反編譯 `Vendor.Product.Utility.MappingCode`。

#### 本模組自訂的旗標值

以下是 CAS 程式碼裡直接比對的字面值,全部沒有常數定義:

| 欄位 | 值 | 語意(反推) | 錨點 |
|---|---|---|---|
| `USAGE` | `'3'` | 「代銷通路」這一類的 `CRM003A` 資料 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`(寫入)、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224`(過濾) |
| `USAGE` | `<> '1'` | 匯出 Excel 時排除的另一類 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:534` |
| `CUST_TYPE` | `'9'` | 代操客戶,原則上不可刪 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442` |
| `DEPT_NO` | `'X01'` | 可以刪代操客戶的特例部門 | 同上〔客戶特定〕 |
| `SEND_FUND_YN` | `'Y'` | 要傳送基金資料 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:535` |
| `SEND_INFO_YN` | `'Y'` / `'N'` | 發文通知 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:92-95` |
| `ADDR_CODE1` | `'1'` / `'0'` | 通訊地址型別 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:300` |
| `CALL_TYPE2` | `'2'` | 實際拜訪方式 = 不需車資的那一種 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:628` |
| `CFM_USER1` / `CFM_USER2` | `'Y'` | 主管已閱 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:211-214` |
| `CONNECT_RE` | `'Y'` | 業務需回覆 → 觸發寄信 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:323` |
| `MRG_YN` | `'N'` | 非組長(新增預設) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:195` |
| `RPT_KIND` | `'RPT'` | 報表格式(否則走 Excel 版 SP) | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |

#### 代碼分類碼(`CODE_SORT` / `SOURCETYPE`)

CAS 用到的代碼分類,全部寫死在 SQL 或 UI 裡:

| 分類碼 | 表 | 用途(反推) | 錨點 |
|---|---|---|---|
| `CODE_SORT = '20'` | `COD006A` | 理專等級 / 客戶等級 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:217`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:236` |
| `CODE_SORT = 'P1'` | `COD006A` | 拜訪重點代碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:154` |
| `CODE_SORT = 'P3'` | `COD006A` | 追蹤事項 / 推薦產品類型 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:157`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:255` |
| `CODE_SORT = 'P6'` | `COD006A` | 經辦職務 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:216` |
| `CODE_SORT = '19'` | `COD006A` | 客戶投資意願 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:227` |
| `SOURCETYPE = '447'` | `CTL014` | 拜訪方式 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:151` |
| `SOURCETYPE = '469'` | `CTL014` | 投資特性 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:573` |

UI 端的下拉來源代碼(`GetDropDownDataSrc` / `GetDropDown9iDataSrc` 的參數)是另一套編號,整理在附錄 C。**兩套編號互不相通**,而且同一支畫面會混用 `GetDropDownDataSrc` 與 `GetDropDown9iDataSrc` 兩種實作(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:116-121`),這點 `architecture.md §2.6` 已經記過。

## 3. 畫面清冊

16 支畫面,**六層全齊**(掃描器實測,無假警報)。分佈:B 1 / I 1 / M 6 / R 8。中文名一律標「待選單表」——repo 內只有 4 支彈出視窗有 `this.Text`,主畫面標題由框架從平台庫取得,程式裡看不到。

### 3.1 維護 M

| 代號 | 中文名(待選單表) | 六層 | 主表 | 明細 | SP / Fn | rpt / 彈出視窗 |
|---|---|---|---|---|---|---|
| `CASM001` | 通路經辦 / 理專維護(推測) | 齊 | `CRM003A`〔共用〕 | `CAS003A` | 無 | 無;有「匯出 Excel」鈕 |
| `CASM002` | 客戶拜訪單維護(推測) | 齊 | `CLS001A`〔共用〕 | `CLS002A`〔共用〕 | 無 | `CASM002RPS`(拜訪記錄單) |
| `CASM003` | 年度境外代銷手續費加項維護(推測) | 齊 | `CAS001A` | `CAS002A` | 無 | 無 |
| `CASM004` | 銷售機構業務員分配比率維護(推測) | 齊 | `CAS004A` | 無 | `S_TA_CASM004_P01` | `CASM004p0`「業務員複製」 |
| `CASM005` | 受益人層分配比率維護(推測) | 齊 | `CAS005A` | 無 | 無(走程式內複製) | `CASM005p0`「業務員複製」 |
| `CASM006` | 年度業績目標維護(推測) | 齊 | `DSM001A`〔共用〕 | `DSM002A`〔共用〕 | 無 | 無 |

六支的共同結構:`xMaintainForm` + `TabPages = 2`(查詢頁 + 維護頁)+ `BaseEVADaoPO`。逐支的 `FormInitial` 錨點: `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:107-183`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:133-160`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:175-190`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:145-161`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:58-90`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:278-293`。

**兩個分組**,差別大到影響維護方式:

| 分組 | 誰 | 特徵 |
|---|---|---|
| 有跳號一覽表 | `CASM001`、`CASM002` | PO 掛 8 個 `After*` 事件寫 `SrNoComment` 稽核軌跡;UI 掛 `AfterComment` / `AfterModifyTabShow` / `DoMnuCus1Click`;PK 由 `BeforeAdd` 取流水號 |
| 沒有 | `CASM003`–`CASM006` | PO 只掛 3 個 `Before*`;PK 由使用者輸入;刪除不留紀錄 |

差異的根源是 PK 的來源:`CRM003A` 的 `PR_NO` 與 `CLS001A` 的 `CALL_RPT_NO` 是系統流水號,會有「跳號」問題(取號後放棄不用),所以要有一覽表交代;其餘四支的 PK 是年月 + 員工代碼這種業務鍵,不會跳號。

### 3.2 查詢 I

| 代號 | 中文名 | 六層 | 主表 | 明細 | SP / Fn | 備註 |
|---|---|---|---|---|---|---|
| `CASI001` | 代銷客戶拜訪記錄查詢作業 | 齊 | (PO 的宣告被註解)實際查 `CLS001A` | `CLS002A` join 進來 | 無 | 彈出視窗 `CASI001p0` 顯示單筆明細 |

中文名來自 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001p0.Designer.cs:2588`,是彈出視窗的標題,主畫面應該同名(**假設**)。 PO 不繼承任何基底、自建兩條 `Database` 連線(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:33-36`),與 `architecture.md §6.3` 描述的 I 型樣板一致。

### 3.3 批次 B

| 代號 | 中文名 | 六層 | 主表 | 寫哪張 | SP / Fn | 備註 |
|---|---|---|---|---|---|---|
| `CASB001` | 代銷組客戶拜訪主管明細表 | 齊 | (PO 的宣告被註解)實際查 `CLS001A` + `CLS002A` | **`CLS002A`** | 無 | 彈出視窗 `CASB001p0` 編輯單筆;有寄信 |

中文名來自 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.Designer.cs:2613`。 **沒有對應的 WindowsService**,全庫只有 4 支 B 畫面配服務,`CASB001` 不在其中(`architecture.md §6.4`)。它是使用者按「執行」鈕觸發的前景作業。

### 3.4 報表 R

| 代號 | 中文名(取自程式內字串) | 六層 | 取數 SP | rpt |
|---|---|---|---|---|
| `CASR001` | 訪談報告(6 種) | 齊 | `S_TA_CASR001_GET` | `CASR001RPS`…`CASR001RPS6`(6 支) |
| `CASR002` | 代銷組業務人員明細統計表 | 齊 | `S_TA_CASR002_GET` | **無**,只出 Excel |
| `CASR003` | 銷售機構銷售總表 | 齊 | `S_TA_CASR003_GET` | `CASR003RPS`、`CASR003RPS1` |
| `CASR004` | 銷售機構期間收入統計表 | 齊 | `S_TA_CASR004_GET` / `S_TA_CASR004_GET_XLS` | `CASR004RPS` |
| `CASR005` | 代銷退休管家庫存明細表 / 統計表 | 齊 | `S_TA_CASR005_GET` | `CASR005RPS`、`CASR005RPS1`(另有孤兒檔 `CASR005RPS11`) |
| `CASR006` | 每日申購信託基金交易明細表 | 齊 | `S_TA_CASR006_GET` | `CASR006RPS`、`CASR006RPS2` |
| `CASR007` | 銷售機構定額契約統計表 | 齊 | `S_TA_CASR007_GET` | `CASR007RPS` |
| `CASR008` | 銷售機構期間銷售統計表 / 排行表 | 齊 | `S_TA_CASR008_GET` | `CASR008RPS`、`CASR008RPS1`、`CASR008RPS2` |

中文名錨點:`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:92-109`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:332`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:179`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:295`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:191`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:178-187`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:138`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:347-361`。

**R 是七層不是六層**,各層資料夾與組件都加 `Report` 前綴,細節見 `architecture.md §6.5`。第七層 `Report.CAS` 裝 19 支 `.rpt` 中的 17 支,另外 2 支(`CASR003RPS`、`CASR005RPS11`)躺在 `ReportUI.CAS` 資料夾,靠 PostBuild 的 `xcopy` 交付(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331`)。

### 3.5 一眼看出差別的四件事

| 面向 | M(6 支) | I(1 支) | B(1 支) | R(8 支) |
|---|---|---|---|---|
| PO 基底 | `BaseEVADaoPO` | 無基底,自建 `Database` | 無基底,自建 `Database` | 無基底,自建 `Database` |
| SQL 在哪 | PO 的 `BuildMasterSQLString` | PO 的 `Select` 一整段 | PO 的 `Select` 一整段 | **不在程式裡**,全在 SP |
| 四眼 | 走引擎 | 無 | **繞過引擎直接 UPDATE** | 無 |
| 交易 | 框架管 | 無寫入 | 自己 `BeginTransaction` | 自己 `BeginTransaction`(只為讀) |
| SQL 參數化 | **否**,字串串接 | **否** | 查詢否 / 寫入是 | **是**,全部 bind |

最後一列是本模組最大的技術債:**維護與查詢畫面的查詢條件全部用字串串接組進 SQL**,唯二用綁定參數的地方是 `CASM002` 的報表查詢(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:588`)與 `CASB001` 的批次寫入(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354`)。詳見附錄 E。

## 4. 維護畫面(M)— 一支一節

```text
[圖] M 畫面從按鈕到四眼引擎的卡控順序，以及各畫面掛了哪些事件
圖中文字:① 用戶端（UI）：全部卡控都在這一層，伺服器不重驗 / Before*ButtonClicked / Add/Modify/Delete/Search / validatorManager1 / 必填與格式 框架決定 / DoValidate() / 本畫面自訂檢核 / Pxy 直呼 DB 檢核 / IsID_NOExsits 等 / ② SetMasterToDetail：把主檔欄位回填到每一列明細（漏做＝明細 PK 空） / SetMasterToDetail / USAGE/PR_NO 寫死回填 / ProcessVDB / ViewVDB 過 Remoting / ③ 伺服端：PO 事件掛點（見 architecture 四眼章） / BeforeAdd / 取流水號 撞號重取 / BeforeSelect / 整條 SQL 換掉 / BeforeGetToDoData / 待辦清單語法 / EVA 引擎 / 無原始碼 DLL 內 / ④ After*：唯一能否決整筆的手段是 throw / AfterVerify Approve / 跳號一覽表 AddComment / AfterDelete UnDelete / 同上 / AfterReject Resend / 同上 / throw → 整筆回滾 / 失敗訊息是空字串 / ⑤ 只有 CASM001／CASM002 掛 After*；M003–M006 完全沒有 / CASM001 CASM002 / 8 個 After 掛點 / CASM003 CASM006 / 只掛 3 個 Before / CASM004 CASM005 / 只掛 3 個 Before + 複製 / CASB001 繞過 EVA / 直接 UPDATE 四眼欄
```

*圖:圖 3 卡控與四眼順序。橘框=本模組寫的程式碼；黑框=框架 DLL（無原始碼，從呼叫端反推）；橘虛框=寫死值或會咬人的行為。整條鏈只要任一層 e.Cancel 或 throw，後面全部不執行。*

本章每一節的結構固定:用途 → 必填與存檔前檢核 → 四眼各階段附加動作 → 跨表更新 → 卡控總表。

**卡控結果一律分五類**,全文通用:

| 類型 | 使用者看到什麼 | 程式長相 |
|---|---|---|
| **阻擋** | 錯誤訊息,動作不執行 | `ValidateErrList.AddError(...)` 後 `e.Cancel = true`,或 `throw` |
| **警示** | 訊息視窗,按掉後照樣執行 | `MessageBox.Show(...)` 之後沒有 `e.Cancel` |
| **詢問** | 是 / 否對話框,由使用者決定 | `ShowMessage` 取回傳值再分支 |
| **過濾(無提示)** | 資料默默少了,沒有任何訊息 | SQL 裡的 `WHERE` / `JOIN` 條件 |
| **記錄不擋** | 只寫紀錄 / 寫欄位,流程不變 | `AddCommentHistory` 這類 |

### 4.1 `CASM001` — 通路經辦 / 理專維護

#### 用途(推測)

維護「銷售機構」(銀行分行、保經代)這筆主檔,以及機構底下的經辦 / 理專名單。主檔存進 `CRM003A` 並固定寫 `USAGE = '3'`;名單存進 `CAS003A`,一個機構可以有多位經辦。

推測依據:主檔欄位是「銷售機構金資」「銷售機構」「聯絡人」「決策者」「通訊地址」;明細欄位是「經辨/理專姓名」「理專等級代碼」「理專推薦產品類型」「傳送基金相關資料」。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:358-385`(新增)、`:387-396`(修改)、`:514-562`(`DoValidate`)。

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | grid 目前編輯中的列先 `Update()` | 永遠 | 記錄不擋(防資料沒寫進 DataSet) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:360-361` |
| 2 | 框架的必填 / 格式檢核 | 欄位空或格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:517` |
| 3 | 金資代碼長度 > 7 且首字非英文 → 必須是合法身分證 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:519-528` |
| 4 | 金資代碼長度 > 7 且首字是英文 → 必須是合法統編 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:529-535` |
| 5 | 主檔 EMAIL 格式 | 非空且格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:539-540` |
| 6 | 明細每列 EMAIL 格式 | 非空且格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:543-555` |
| 7 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:557-560` |
| 8 | 金資代碼不可重複 | 同一個 `ID_NO` 在 `CRM003A` 已存在(限 `USAGE = '3'`) | 阻擋(對話框,不是訊息清單) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:374-382` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:369-389` |

**第 3、4 兩條的邊界要記住:長度 ≤ 7 的金資代碼完全不檢查。**這是刻意的(金資代碼本身就是 7 碼),但也代表打錯的 7 碼不會被擋。

**第 8 條只在新增時跑。**修改時(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:387-396`)只跑 `DoValidate()`,不查重複。所以把 A 機構的金資代碼改成 B 機構的值,**不會被擋**。

**第 8 條在 DB 出錯時會靜默放行。**`IsID_NOExsits` 的 `catch` 回傳 `-1`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388`),UI 判斷式是 `if (i > 0)`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:376`),`-1` 不成立 → 當成「沒有重複」放行。

還有一個**被註解掉但外殼還在**的檢核:`ID_NODoValidate()` 這支方法留在檔案裡但內容是空的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:567-571`),呼叫點也被註解(`:363`)。讀碼的人會以為有這道檢核。

#### 刪除前的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:436-456`,三次遠端往返:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 9 | 代操客戶不可刪 | `CUST_TYPE = '9'` 且經辦所屬 `DEPT_NO <> 'X01'` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447`〔客戶特定〕 |
| 10 | 已有拜訪紀錄不可刪 | `CLS001A` 內存在同 `PR_NO` 的資料 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:448-453` |

第 9 條的兩支查詢都會在出錯時吞掉:`GetCustType` 與 `GetDeptNo` 的 `catch` 回傳空字串(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:480-484`、`:516-520`),空字串不等於 `'9'` → 放行。而且兩支都直接取 `Rows[0]` 沒有筆數檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:475`、`:511`),查無資料時會丟 `IndexOutOfRangeException`,被 `CommonExceptionBlocker` 吞掉後一樣回傳空字串。**結論:第 9 條只在一切正常時有效。**

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:398-429`。

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 11 | 至少輸入一個查詢條件 | 金資 / 機構名 / 序號 三個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:405-413` |

**第 11 條在待辦(ToDo)流程被跳過**:`if (this.EVAAction == "")` 才檢查。從待辦清單點進來時 `EVAAction` 有值,條件可以全空。

#### 四眼各階段附加動作

`CASM001_PO` 建構子一次訂 12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:42-58`):

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | do-while 取流水號 `GetPR_NO()`,撞號就重取;取到後回填到每一列明細 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77-103` |
| `BeforeSelect` | 把 `args.DbCmd` 整個換成 `BuildMasterSQLString(model, false)` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:105-117` |
| `BeforeGetMaintainData` | 主檔走 `BuildMasterSQLString`,明細走 `BuildDetailSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:119-139` |
| `BeforeGetToDoData` | 同上但 `isToDoString = true`,多接 `AppendToDoString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:141-153` |
| `AfterGetMaintainData` | 讀跳號一覽表歷史 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:569-574` |
| `AfterDelete` | 寫跳號一覽表(`EVAType.Delete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:576-584` |
| `AfterUnDelete` | 同上(`EVAType.UnDelete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:586-591` |
| `AfterVerify` | 同上(`EVAType.Verify`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:593-598` |
| `AfterApprove` | 同上(`EVAType.Approve`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:600-605` |
| `AfterApproveDelete` | 同上(`EVAType.ApproveDelete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:611-617` |
| `AfterResend` | 同上(`EVAType.Resend`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:618-623` |
| `AfterReject` | 同上(`EVAType.Reject`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:625-630` |

七個 `After*` 的寫法完全一樣:`if (!SrNoCommentProcessor.AddCommentHistory(...)) throw new ApplicationException("")`。

**三件事要記住:**

1. **`throw` 的訊息是空字串。**使用者看到的錯誤訊息會是框架的預設文字,追不到是哪一步失敗的。

2. **每個 handler 第一行都是 `if (args.TableName != this.MasterTable.dbTableName) return;`**(例 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:571`),因為事件會對主檔 + 每個明細表各觸發一次。少寫這一行就會寫兩次紀錄。

3. **`BeforeAdd` 沒有那道防護**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77-103`)。它只在 `args.TableName == MasterTable` 時取號,但**流水號回填明細那段在 `if` 外面**(`:98-101`),所以明細表觸發時也會跑一次——重複但無害,因為值一樣。

#### 跨表更新

| 動作 | 寫哪張表 | 說明 |
|---|---|---|
| 新增 / 修改 / 刪除 | `CRM003A` + `CAS003A` | 由四眼引擎產生 SQL,程式看不到 |
| 任何四眼動作 | 跳號一覽表(表名在框架內,無原始碼) | `SrNoCommentProcessor.AddCommentHistory` |
| 匯出 Excel | **不寫** | 只讀 |

**唯讀 join 的表**:`COD006A`(兩次,取 `CUST_CLASS1` / `CUST_CLASS2` 的說明)、`COD009`(取員工姓名)。錨點 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:214-222`。

#### 匯出 Excel

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:458-506` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:524-564`。

取數條件(全部寫死在 SQL 裡):

| 條件 | 值 |
|---|---|
| 機構的 `USAGE` | `<> '1'` |
| 明細的 `EMAIL` | `TRIM(...) IS NOT NULL` |
| 明細的 `SEND_FUND_YN` | `= 'Y'` |
| 去重 | 以 `EMAIL` 分組,取 `MAX(PR_NO)` / `MAX(STAFF_NAME)` / `MAX(EMP_NO1)` |

**這是過濾(無提示)的典型**:畫面上看得到的經辦,匯出檔裡可能沒有,而且沒有任何訊息說明為什麼。三個原因都可能:沒填 EMAIL、`SEND_FUND_YN` 不是 `Y`、或同一個 EMAIL 被別列去重掉了。

還有一個會咬人的:`GetExcel()` 出錯時回傳 `null`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:558-562`),UI 拿到後**沒有判 null 就直接改欄位名稱**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:472-479`)→ `NullReferenceException`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:517` |
| 按新增前 | 身分證 / 統編格式(長度 > 7 才驗) | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:519-536` |
| 按新增前 | 主檔 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:539-540` |
| 按新增前 | 明細 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:550-551` |
| 按新增前 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:557-560` |
| 按新增前 | 金資代碼重複 | 已存在 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:374-382` |
| 按新增前 | 金資代碼重複(DB 出錯時) | `catch` 回傳 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388` |
| 按修改前 | 金資代碼重複 | — | **不檢查** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:387-396` |
| 按刪除前 | 代操客戶 | `CUST_TYPE = '9'` 且非 `X01` 部門 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447`〔客戶特定〕 |
| 按刪除前 | 已有拜訪紀錄 | `CLS001A` 有同序號 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:448-453` |
| 按查詢前 | 至少一個條件 | 三個都空且非待辦流程 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:405-413` |
| 查詢時 | 只看 `USAGE = '3'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| grid 編輯時 | 明細 PK 重複 | 同名經辦 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:642-645` |
| grid 新增列時 | 明細 PK 必填 | `STAFF_NAME` 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:647-652` |
| 修改模式 | 明細 PK 不可編輯 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:613-620` |
| 四眼任一階段 | 寫跳號一覽表失敗 | `AddCommentHistory` 回 false | 阻擋(整筆回滾,訊息空白) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` |
| 匯出 Excel | 三道 SQL 條件 + EMAIL 去重 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:533-541` |

### 4.2 `CASM002` — 客戶拜訪單維護

#### 用途(推測)

業務員填寫對銷售機構的拜訪紀錄:預計 / 實際拜訪日與方式、與談者、拜訪重點、三組追蹤事項、車資與人數;以及主管那一段的意見、溝通事項、異常狀況與回覆(存 `CLS002A`)。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:317-326`(新增)、`:328-337`(修改)、`:535-580`(`DoValidate`)。

`DoValidate()` **只有兩件事**:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架的必填 / 格式檢核 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:538` |
| 2 | 與談者 1 / 2 / 3 不可重複(忽略空白) | 有重複 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:541-552` |

**另外三段「主談者資料不存在」的檢核整段被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579`),而且第三段的複製貼上還沒改對——檢查的是 `ucMAIN_CHATER1` 卻報「主談者3資料不存在」(`:574`)。就算解開註解也是錯的。

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:339-422`,是本模組最完整的一套:

| # | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| 3 | 至少一個條件(待辦流程跳過) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:347-359` |
| 4 | 潛在客戶序號起迄要嘛都填要嘛都不填 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:363-364` |
| 5 | 潛在客戶序號起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:365-367` |
| 6 | 銷售機構金資起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:369-373` |
| 7 | 區域別起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:375-379` |
| 8 | 實際拜訪日期起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:381-385` |

4–8 條全部用 `^`(互斥或)寫,而且**不受 `EVAAction` 影響**——待辦流程也會跑。條件本身沒問題,但待辦流程下所有起迄欄位都是空的,`^` 兩邊都 false 不成立,所以實務上不會擋到。

#### 自動帶值(不是卡控,但會改資料)

| 觸發 | 做什麼 | 失敗時 | 錨點 |
|---|---|---|---|
| 潛在客戶序號變更 | 查 `CRM003A` 帶出員工編號 / 金資 / 機構名 | 查無 → 三欄清空,無提示 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:583-601` |
| 金資代碼離開欄位 | 反查 `CRM003A` 帶出序號 / 員工 / 機構名 | 查無 → 三欄清空,無提示 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:642-663` |
| 與談者 1 選定 | 用該經辦的 `PR_NO` 查 `CAS003A`,帶出理專等級 / 投資特性 / 推薦類型 | 查無 → 三欄清空(訊息被註解掉了) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:665-700` |
| 實際拜訪方式 = `'2'` | 清空並鎖住往返與車資 | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:624-640` |

**三處 `pxy.GetXXX(...)` 的回傳值都沒判 null。**PO 端出錯時回傳 `null`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:444-448`),UI 直接 `.Rows.Count` → `NullReferenceException`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:592`、`:650`、`:681`)。

#### 四眼各階段附加動作

與 `CASM001` 逐行對應,連寫法都一樣:12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:42-58`),`BeforeAdd` 取 `GetCALL_RPT_NO()`(`:92`),七個 `After*` 寫跳號一覽表(`:628-682`)。

差別只有兩處:

| 面向 | `CASM001` | `CASM002` |
|---|---|---|
| 流水號 | `GetPR_NO()` | `GetCALL_RPT_NO()` |
| 多一支方法 | — | `GetReport_Data<T>`(拜訪記錄單報表),`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:522-613` |

#### 跨表更新

| 動作 | 寫哪張表 |
|---|---|
| 新增 / 修改 / 刪除 | `CLS001A` + `CLS002A`(都是〔共用〕表) |
| 四眼各階段 | 跳號一覽表 |

**明細只會有一列。**`SetMasterToDetail()` 在新增或 0 列時 `NewCLS002ARow()`,否則 `FirstOrDefault()`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:101-130`)。畫面上沒有明細 grid,那 9 個欄位是直接放在表單上的。

唯讀 join:`CRM003A`(機構名與客戶等級)、`CAS004A`(區域別)、`COD006A`(兩次)。錨點 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:217-230`。

**`CAS004A` 這個 join 值得單獨看**:

```
LEFT JOIN (SELECT CAS004A.EMP_NO, MAX(CAS004A.YYMM) YYMM
                , MIN(CAS004A.AREA_CODE) KEEP (DENSE_RANK FIRST ORDER BY CAS004A.AREA_CODE) AREA_CODE
             FROM CAS004A GROUP BY CAS004A.EMP_NO ) CAS004A
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224`。`MAX(YYMM)` 被算出來但**沒有任何地方用到**;`AREA_CODE` 取的是該員工**所有月份中最小的區域別**,不是最新月份的。名字叫 `MAX(YYMM)` 會讓人以為取的是最新一筆——不是。對照 `CASI001` 的寫法(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:141-144`)用的是 `ROW_NUMBER() OVER(PARTITION BY EMP_NO ORDER BY YYMM DESC)` 取 `RNO = 1`,**那個才是真的取最新**。同一個概念兩套實作、結果不同。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:538` |
| 按新增 / 修改前 | 與談者 1/2/3 不可重複 | 有重複 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:548-551` |
| 按新增 / 修改前 | 與談者存在性 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579` |
| 按查詢前 | 至少一個條件 | 七個都空且非待辦 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:347-359` |
| 按查詢前 | 四組起迄的成對與大小 | 只填一邊或起 > 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:363-385` |
| 查詢時 | 只看 `USAGE = '3'`(內外各一次) | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:232`、`:236` |
| 查詢時 | 區域別取全期間最小值而非最新月 | 永遠 | 過濾(無提示,值會錯) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` |
| 帶值時 | 查無資料 | 查不到機構 / 經辦 | **靜默清空**(訊息被註解) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:698` |
| 選擇拜訪方式 `'2'` | 鎖住車資欄 | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:628-634` |
| 四眼任一階段 | 寫跳號一覽表失敗 | 回 false | 阻擋(訊息空白) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:634` |
| 列印 | 查無資料 | 報表 SQL 0 筆 | 警示(對話框,不改資料) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:486-489` |

### 4.3 `CASM003` — 年度境外代銷手續費加項維護

#### 用途(推測)

替某位員工設定某個業績年度的「境外代銷手續費加項」總額(`CAS001A`),並把總額拆成 12 個月的明細(`CAS002A`)。畫面上有一顆「月分配」鈕做自動拆分。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:60-92`(`DoValidate`),按順序:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:63` |
| 2 | 起算年月必須與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:66-67` |
| 3 | 年度手續費加項 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:69-70` |
| 4 | 明細 PK 必填 | grid 有列但 PK 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:72-77` |
| 5 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:78-81` |
| 6 | 每列月分配 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:85-86` |
| 7 | 年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:88-90` |

**第 6、7 兩條有前置條件**:`if (this.ValidateErrList.ErrorCount > 0) return;`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:83`)。前面任何一條錯了,這兩條就不跑——使用者要修兩輪才看得到全部錯誤。

另有一條在欄位離開時觸發的檢核:業績年度必須介於 1900 與今年之間(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:319-342`)。**這條實際上幾乎不會觸發**,因為它的前置是 `this.udatBOUNS_ST_YYMM.Value == null`(`:322`),而只要使用者填過起算年月就不成立。而且它用 `MessageBox.Show` 而不是 `ValidateErrList`,與整個畫面的風格不一致。

#### 「月分配」鈕的行為

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:101-173`。分兩條路:

**路徑 A(grid 已有列)**:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:120-137`。依 `QUO_YYMM` 排序逐列,前 11 列各給 `Math.Floor(總額 / 12)`,第 12 列給剩餘。

**路徑 B(grid 沒有列)**:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:138-172`。從起算月往後產 12 列,前 11 列給均分值,最後一列給剩餘。

兩個會咬人的地方:

1. **路徑 A 假設剛好 12 列。**計數器是 `j`,條件 `if (j < 12)`。列數 < 12 時每列都拿均分值,總和小於年度總額 → 存檔被第 7 條擋下,使用者只能手改。列數 > 12 時第 12 列拿到剩餘,**第 13 列以後每列都拿到同一個剩餘值**(`iOFD_INC_ALLOT_FEE_E` 在 else 分支裡沒有再扣),總和暴增。

2. **路徑 B 跨年時月份格式會壞。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151`: `` else if (iQUO_Month > 12) MRow.QUO_YYMM = Convert.ToString(Convert.ToInt16(umskQUO_YEAR.Value) + 1) + "0" + Convert.ToString(iQUO_Month - 12);`` 補零是寫死的 `"0" +`,沒有判斷位數。起算月 = 11 月時,第 11 列的 `iQUO_Month` 是 21 → `21 - 12 = 9` → `"09"`,還好;起算月 = 12 月時第 11 列 `iQUO_Month = 22` → `22 - 12 = 10` → `"0" + "10"` = `"010"`,**`QUO_YYMM` 變成 7 碼**(如 `2026010`)。而 xsd 宣告 `maxLength = 6`(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:131-137`),DataSet 層就會丟例外。 **但第 2 條檢核(起算年月必須與業績年度同年)沒有限制月份**,所以起算月選 12 月是允許的。這條路走得到。

#### 四眼各階段附加動作

**沒有。**`CASM003_PO` 只掛 3 個 `Before*`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:30-32`),沒有任何 `After*`,也沒有 `BeforeAdd`——PK 由使用者輸入,不需要取號。

#### 跨表更新

只寫 `CAS001A` + `CAS002A`。唯讀 join 只有一個 `COD009`,而且是 **`JOIN` 不是 `LEFT JOIN`**:

```
FROM CAS001A JOIN COD009 ON COD009.EMP_NO = CAS001A.EMP_NO
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121`。**員工在 `COD009` 找不到時,這筆業績目標整筆從查詢結果消失,沒有任何提示。**對照 `CASM006` 用的是一樣的 inner join(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:124-126`),而 `CASM004` / `CASM005` 用 `LEFT JOIN`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:373-374`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:297-298`)。**同一件事四支畫面兩種寫法。**

#### 查詢條件的組法

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:127-185`。業績年度與員工代碼都是起迄:

| 參數 | 產生的條件 |
|---|---|
| `QUO_YEAR` | `>= 值` |
| `QUO_YEAR1` | `<= 值`;**沒傳時退回用 `QUO_YEAR` 當上界** |
| `EMP_NO` | `>= 值` |
| `EMP_NO1` | `<= 值`;同樣有退回邏輯 |

退回邏輯的效果是:**只填「起」不填「迄」時,查詢會變成等於**。UI 端已經先幫使用者把「迄」補成「起」了(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:305-315`),所以兩層都在做同一件事。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:219-220` |
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:63` |
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:66-67` |
| 按新增 / 修改前 | 年度總額 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:69-70` |
| 按新增 / 修改前 | 明細至少一列、PK 必填 | 0 列或 PK 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:72-81` |
| 按新增 / 修改前 | 每列 > 0、總和相符 | 不符 | 阻擋(但前面有錯就不跑) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:83-90` |
| 年度欄離開時 | 年度介於 1900~今年 | 只在起算年月為空時判 | 警示改阻擋(`MessageBox` + `e.Cancel`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:319-342` |
| 按查詢前 | 年度 / 員工起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:245-255` |
| 查詢時 | 員工不在 `COD009` → 整筆消失 | 永遠 | **過濾(無提示)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121` |
| 按月分配 | 明細列數不是 12 | 列數 ≠ 12 | 記錄不擋(金額會錯,之後被第 7 條擋) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:120-137` |
| 按月分配 | 起算月 = 12 月 | 跨年月份 ≥ 10 | 記錄不擋(產生 7 碼年月 → 之後丟例外) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151` |
| 修改模式 | 起算年月不可改 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:214` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs` 無 `BeforeDeleteButtonClicked` |

### 4.4 `CASM004` — 銷售機構業務員分配比率維護

#### 用途(推測)

設定某個業績年月、某個銷售機構(區別碼 + 代碼)、某位業務員的分配比率。四個欄位合起來是 PK,同一組機構下多位業務員的比率加總不得超過 100%。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:35-53`(`DoValidate`),只有三件事:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:38` |
| 2 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:40-41` |
| 3 | 同年月 + 機構區別碼 + 機構代碼 的加總比率(排除本人)+ 本次輸入 ≤ 100 | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:49-52` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:273-296` |

第 3 條的 SQL 值得看清楚:

```
SELECT CASE WHEN SUM(DIV_PCT) + To_number('<新值>') > 100 THEN 1 ELSE 0 END
  FROM CAS004A WHERE YYMM = ... AND AGENT_ID = ... AND AGENT_CODE = ... AND EMP_NO <> ...
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:277-282`。三個要注意的:

1. **不分狀態全算。**還在送審中、已退回、甚至邏輯刪除的資料都算在 `SUM` 裡(沒有 `STATUS` 條件)。

2. **同一組合下沒有其他人時 `SUM` 是 NULL**,`NULL + x > 100` 是 unknown,`CASE` 走 `ELSE 0` → 放行。行為正確,但是靠 Oracle 的三值邏輯,不是靠程式。

3. **`catch` 回傳 `-1`**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:291-295`),UI 判 `if (i > 0)` → DB 出錯時**靜默放行**。與 `CASM001` 的第 8 條同一個模式。

另有一條在欄位離開時觸發:分配比率不可為 0(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328`),用 `MessageBox` + `e.Cancel`,與 `DoValidate` 的第 2 條重複但訊息不同(一個說「必須大於 0」,一個說「應介於0.01和100.00之間」)。

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:227-270`:

| # | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| 4 | 業績年月起迄**必填**(不是擇一) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:231-232` |
| 5 | 業績年月起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:233-235` |
| 6 | 機構區別碼起迄成對 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:237-238` |
| 7 | 機構區別碼起 = 迄(不是範圍!) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:239-240` |
| 8 | 機構代碼起迄成對且起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:242-246` |

**第 7 條把「區別碼」的起迄降級成單值**,而且 PO 端真的只送一個參數(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:260-263`,「迄」那行是註解掉的)。畫面上擺兩個欄位卻只能填一樣的值,是留下來沒清乾淨的 UI。

#### 業務員下拉的兩層過濾

| 層 | 條件 | 錨點 |
|---|---|---|
| `FormInitial` 設 `Filter` | `(DEPT_NO <> 'G17') AND (LEAVE_DATE >= '<今年>/01/01' OR LEAVE_DATE IS NULL)` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159`〔客戶特定〕 |
| `BeforeGetDataSource` | **整段被註解**(原本要排除 `G3` / `GA` / `G12` / `G13`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:310-316` |

註解裡留了一句「2015/12/25 改為代銷部門可修改」,說明這是刻意放寬的。但**放寬後只剩 `G17` 一個排除條件,而 `G17` 又是 `CASM005` 明確要納入的部門**(§4.5),兩支畫面的部門規則互相矛盾。

#### 「業務員複製」彈出視窗

`CASM004p0`,由主畫面的 `DoExp1()` 開啟(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:114-139`)。修改模式下會把目前這筆的年月 / 區別碼 / 機構代碼 / 業務員當預設值帶進去(`:121-136`)。

複製的檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:63-121`):

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 9 | 框架必填 / 格式 | — | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:66` |
| 10 | 來源業務員在該月份 / 機構有資料 | `GetEmpAgentStartDate` 回空字串 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:97-99` |
| 11 | 目標業務員不可為空 | 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:114-115` |
| 12 | 年月起 ≤ 迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-70` |
| 13 | 來源與目標業務員不可相同 | — | **被註解**(註記「2016.07.29改為不判斷」) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:74-76` |
| 14 | 來源 / 目標業務員存在性 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:103-112` |
| 15 | 複製後比率不超過 100% | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:116-118` |

**七條檢核裡四條被註解。**其中第 15 條有替代路徑:SP 跑完後會回一張 `CAS004A_OVER` 結果集,列出超過 100% 的機構,由 `CheckOverDivPct` 轉成錯誤訊息(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:54-60`)。也就是**事前不擋、事後才報**——但那時候 SP 已經 commit 了(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:117`)。

**第 10 條的回傳值有個陷阱**:`GetEmpAgentStartDate` 在 `catch` 裡 `return ex.Message;`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231`)。DB 出錯時回傳的是例外訊息字串,`string.IsNullOrWhiteSpace` 為 false → **當成「有資料」放行**。把例外訊息當成業務資料回傳,是本模組最危險的一個寫法。

#### 跨表更新

| 動作 | 寫哪張表 | 怎麼寫 |
|---|---|---|
| 新增 / 修改 / 刪除 | `CAS004A` | 四眼引擎 |
| 複製 | `CAS004A` | **`S_TA_CASM004_P01`**,自行 `BeginTransaction` 並 `Commit`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:94-118`) |

**複製完全繞過四眼引擎。**SP 內做了什麼(新資料的 `STATUS` 是什麼、四眼欄位怎麼填)在 repo 內看不到。SP 的參數有 8 個,包含 `iUSER_ID`,**推測**是 SP 自己填四眼欄位(依據是參數裡有使用者代號,而程式端沒有任何地方設四眼欄位)。

`cmd.CommandTimeout = 0`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:99`),永不逾時。

錯誤處理有一條特判:Oracle 的 `ORA-00001`(唯一鍵衝突)會被翻成「執行失敗,已建立資料,無法複製」(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:126-127`),其餘例外原樣把 `ex.Message` 塞進訊息回給前端(`:130`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:38` |
| 按新增 / 修改前 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:40-41` |
| 按新增 / 修改前 | 同機構加總 ≤ 100% | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:49-52` |
| 按新增 / 修改前 | 同機構加總(DB 出錯時) | `catch` 回 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:291-295` |
| 比率欄離開時 | 不可為 0 | `== 0` | 阻擋(`MessageBox`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328` |
| 按查詢前 | 業績年月起迄必填 | 兩個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:231-232` |
| 按查詢前 | 機構區別碼起 = 迄 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:239-240` |
| 下拉業務員 | 排除 `G17` 部門、排除去年以前離職 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` |
| 複製前 | 來源業務員該月有資料 | 回空字串 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:97-99` |
| 複製前 | 來源業務員該月有資料(DB 出錯時) | 回傳 `ex.Message` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231` |
| 複製前 | 目標業務員不可為空 | 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:114-115` |
| 複製前 | 年月大小、業務員相同、存在性、比率上限 | — | **四條全被註解** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-118` |
| 複製後 | 比率超過 100% 的機構清單 | SP 回傳有列 | 警示(資料已寫入) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:54-60` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs` 無 `BeforeDeleteButtonClicked` |

### 4.5 `CASM005` — 受益人層分配比率維護

#### 用途(推測)

與 `CASM004` 同一件事,但多一個維度:受益人戶號。也就是「這個受益人在這個機構的業績,要怎麼分給業務員」。PK 從 4 欄變 5 欄。

#### 與 `CASM004` 的差異

| 面向 | `CASM004` | `CASM005` |
|---|---|---|
| PK | 4 欄 | 5 欄(多 `BF_NO`) |
| 複製實作 | SP `S_TA_CASM004_P01` | **程式內逐列 `AddM`**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:81-148`) |
| 查詢預設值 | 無 | 機構區別碼固定 `"0"`、機構代碼固定 `"A0901"`,而且設成 `ReadOnly`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81`)〔客戶特定〕 |
| 業務員下拉 | 排除 `G17` | **同時**設 `DEPT_NO <> 'G17'` 與 `DEPT_NO IN ('G3','GA','G12','G13','G17')` |
| 機構名稱來源欄 | `AGENT_SHNM` | `AGENT_NAME` |
| 複製時的存在性檢核 | 被註解 | **還活著** |

**「查詢條件寫死成單一機構」這件事要特別注意。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81` 把起迄兩組都設成 `"0"` + `"A0901"` 並鎖成唯讀,代表**這支畫面實務上只服務一個銷售機構**。換站台一定要改。

**業務員下拉的兩條規則互相打架**:

| 來源 | 條件 | 錨點 |
|---|---|---|
| `FormInitial` 的 `Filter` | `DEPT_NO <> 'G17'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:87-89`〔客戶特定〕 |
| `BeforeGetDataSource` 加的參數 | `DEPT_NO IN ('G3','GA','G12','G13','G17')` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:240-247`〔客戶特定〕 |

兩條同時送到同一個資料來源。**`G17` 一邊排除一邊納入**,最終行為取決於框架怎麼合併 `Filter` 與 `ConditionVDB`(無原始碼,從呼叫端反推)。**假設**:`Filter` 是用戶端 DataView 的過濾,`ConditionVDB` 是伺服端 SQL 的條件,所以 `G17` 會先被 SQL 撈回來再被 DataView 濾掉,淨效果等於排除。依據是兩者的參數形態不同(一個是 DataTable 的 `Filter` 字串,一個是走 `AddParametersRow`)。這條要現場確認。

#### 複製的實作差異

`CASM005` 走的是舊世代的程式內複製(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:81-148`):

1. 先 `GetMaintainData` 把來源資料撈進 Model(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:68`)

2. 逐列把 `EMP_NO` 換成目標業務員,並把四眼欄位全部清空 / 設成 `1900/01/01`(`:92-109`)

3. 逐列呼叫 `AddM` 寫入(`:110-114`)

4. 兩個交易(業務庫 + 平台庫)一起 commit(`:117-123`)

**第 2 步是本模組唯一直接寫四眼欄位的地方**(除了 `CASB001`)。`row.STATUS = row.STATUS;` 這一行(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96`)是自我賦值,等於什麼都沒做——**複製出來的新資料會帶著來源的狀態**,而不是回到「新輸入待驗證」。

對照 `CASM004` 的 SP 版,同一段邏輯在 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:135-190` **整段被註解保留**,可以逐行對照兩代寫法。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:38` |
| 按新增 / 修改前 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:40-41` |
| 按新增 / 修改前 | 同年月+機構+**戶號** 加總 ≤ 100% | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:49-52` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:195-218` |
| 按新增 / 修改前 | 同上(DB 出錯時) | `catch` 回 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:213-217` |
| 按查詢前 | 業績年月起迄必填且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:174-178` |
| 按查詢前 | 機構區別碼起 = 迄 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:181-183` |
| 按查詢前 | 機構代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:186-189` |
| 進入畫面 | 機構固定為 `A0901` 且不可改 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81` |
| 下拉業務員 | 兩條互相矛盾的部門規則 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:87-89` 與 `:240-247` |
| 複製前 | 來源與目標業務員不可相同 | 相同 | 阻擋(**這支還活著**) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:65` |
| 複製前 | 來源業務員存在 | 回 `0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:84-88` |
| 複製前 | 目標業務員資料已存在 | 回 `> 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:89-93` |
| 複製前 | 檢核失敗(DB 出錯) | 回 `-1` | 阻擋(**有判 `-1`,比 `CASM004` 嚴謹**) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:85-86`、`:90-91` |
| 複製後 | 比率超過 100% 的清單 | SP 回傳有列 | 警示(資料已寫入) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:43-49` |
| 複製時 | 新資料沿用來源狀態 | 永遠 | 記錄不擋(四眼狀態不重置) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs` 無 `BeforeDeleteButtonClicked` |

### 4.6 `CASM006` — 年度業績目標維護

#### 用途(推測)

與 `CASM003` 結構完全平行,但管的是另外六個指標:營業收入、定期(不)定額戶數-目標 / -保守、定期(不)定額扣款成功金額、新開百萬戶數、單筆申購交易百萬戶數。年度總額存 `DSM001A`,月分配存 `DSM002A`。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:68-146`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:71` |
| 2 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:74-75` |
| 3 | 總營業收入 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78` |
| 4 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:90-99` |
| 5 | 每列營業收入 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:103-104` |
| 6–11 | **六個指標**各自的年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:122-144` |

**另外五個指標的「必須大於 0」檢核全部被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88` 與 `:106-119`)。也就是說:**六個指標裡只有「營業收入」不能是 0,其餘五個可以是 0 甚至負數**,但六個都必須總和相符。這個組合允許「年度目標 0、每月目標 0」通過。

#### 「月分配」鈕與 `CASM003` 的關鍵差異

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:155-276`。

| 面向 | `CASM003` | `CASM006` |
|---|---|---|
| 可分配月數 | 固定 12 | `13 - 起算月`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`) |
| 新建列時的餘數處理 | 最後一列給剩餘 | **每列都給均分值,剩餘從不寫回** |
| 跨年 | 會發生(月份可到 23) | 不會(月數已經限制在年內) |

第二列是實質缺陷:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:233-257` 的迴圈把 `iQUO_MGR` 這類均分值寫進每一列,原本要補剩餘的那段(`:259-274`)**整段被註解掉**。所以只要年度總額不能被月數整除,第一次按「月分配」產出的明細總和就一定小於年度總額 → 存檔被第 6–11 條擋下 → 使用者必須手動改最後一列。

`CASM003` 的同一段是活的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:160-171`),所以兩支畫面的「月分配」按下去結果不一樣。

#### 查詢條件

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:349-385`,只有兩條檢核(員工代碼起迄成對、起 ≤ 迄),業績年月的起迄檢核**整段被註解**(`:353-357`)。

**而且 `QueryVDB.Util.Parameters.Clear()` 也被註解掉了**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370`、`:373`)。其餘五支 M 畫面都有清這一行(例 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:197`),只有 `CASM006` 沒有。參數集合以欄位名為鍵,同一個鍵加第二次的行為由框架決定(無原始碼)——**假設**會丟重複鍵例外或直接覆蓋,依據是它背後是 typed DataSet 的 `Rows.Find(name)`。實務上的表現是「連按兩次查詢可能失敗或條件沒換」,要現場確認。

#### 跨表更新與部門白名單

只寫 `DSM001A` + `DSM002A`。查詢時 join `COD009`(inner join,同 `CASM003` 的過濾問題),而且**主檔 SQL 尾巴寫死一串部門白名單**:

```
AND COD009.DEPT_NO IN('G3','GA','G11','G12','G13','G14','Z2','G17') ORDER BY ...
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210`〔客戶特定〕。上一行的註解寫「20180103 modify by jye 9000006164_ATLAS系統權限調整 G17=GA, G16=GB」(`:209`),說明這串是隨組織調整手動維護的。

**這一條是 `CASM006` 與 `DSMM001` 最大的行為差異**:同樣兩張表,`CASM006` 只看得到這 8 個部門的員工,`DSMM001` 沒有這個限制(§8)。**明細 SQL 沒有這個條件**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:224-273`),所以只要拿得到主檔,明細一定拿得到。

#### 離職員工的處理

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463`:選到已離職的員工時跳 `MessageBox` 說「此員工已離職!」,**但沒有 `e.Cancel`,照樣可以繼續設定他的業績目標**。這是「警示」類的標準例子。對照 `CASM004` / `CASM005` 是直接在下拉的 `Filter` 裡排除離職者(過濾,無提示)——**同一件事三支畫面兩種處理方式**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:327-328` |
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:71` |
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:74-75` |
| 按新增 / 修改前 | 總營業收入 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78` |
| 按新增 / 修改前 | 其餘五個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88` |
| 按新增 / 修改前 | 明細至少一列、PK 必填 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:90-99` |
| 按新增 / 修改前 | 每列營業收入 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:103-104` |
| 按新增 / 修改前 | 其餘五個指標每列 > 0 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:106-119` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:122-144` |
| 按查詢前 | 員工代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:358-362` |
| 按查詢前 | 業績年月起迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:353-357` |
| 按查詢前 | 清空上次的查詢參數 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370` |
| 查詢時 | 只看 8 個部門的員工 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` |
| 查詢時 | 員工不在 `COD009` → 整筆消失 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:124-126` |
| 選擇員工時 | 已離職 | `LEAVE_DATE` 非空 | **警示(不擋)** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` |
| 按月分配 | 餘數不寫回最後一列 | 總額不能整除 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:259-274` |
| 修改模式 | 起算年月不可改 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:322` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs` 無 `BeforeDeleteButtonClicked` |

## 5. 查詢畫面(I)

本模組只有一支:`CASI001`「代銷客戶拜訪記錄查詢作業」。單頁(`TabPages = 1`)、唯讀、不走四眼。

### 5.1 結構

| 層 | 特徵 | 錨點 |
|---|---|---|
| UI | `xOneStepProcessForm`;grid 用 `GridLayoutUpdateOnly`(不可編修) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:32-48` |
| Ctl | **只覆寫 `InitializeDataAccessPool()`**,沒有 `InitializeVDBTypes()`;143 行裡約 40 行是註解掉的外殼 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:26-29` |
| PO | 不繼承任何基底,自己 `new` 兩條 `Database`(業務庫 `"TA"` + 平台庫 `"SWProduct"`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:33-36` |

`architecture.md §6.3` / `§6.4` 已經記過這個樣板與 `CASB001` 是同一份複製刪減出來的。**本節只記 CAS 特有的行為。**

### 5.2 查詢條件

UI 端的 `ProcessQueryCondition`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:55-194`)送出的參數:

| 參數 | 來源欄位 | PO 端產生的條件 | PO 錨點 |
|---|---|---|---|
| `QUERY_EMP_NO` | **登入者的員工代號**(不是畫面欄位) | `AND COD009.EMP_NO = '值'`,但白名單內的 5 人跳過 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:198-209` |
| `CALL_RPT_NO_BGN` / `_END` | 客戶拜訪單號起 / 迄 | `>= 值` / `<= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:213-232` |
| `PR_NO_BGN` / `_END` | 潛在客戶序號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:235-253` |
| `EMP_NO_BGN` / `_END` | 員工代號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:256-274` |
| `BF_NO_BGN` / `_END` | 受益人戶號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:277-295` |
| `ID_NO_BGN` | 銷售機構金資 | **`= 值`(不是 `>=`)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:301-309` |
| `ACT_CALL_DATE_BGN` / `_END` | 實際拜訪日期起 / 迄 | `>= '值'` / `<= '值'`(字串比較) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:323-351` |
| `CALL_TYPE2` | 實際拜訪方式 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:354-362` |
| `TOPIC_CODE` | 拜訪重點 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:364-372` |
| `TRACE_CODE` | 追蹤事項 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:375-383` |
| `INVEST_CODE` | 投資特性 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:385-393` |

UI 端的檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:69-125`):五組起迄,每組三條規則——只填「起」就自動補「迄」、只填「迄」則阻擋、起 > 迄則阻擋。銷售機構金資那一組**整段被註解掉**(`:101-107`),所以畫面上只剩一個欄位有效。

**沒有「至少填一個條件」的檢核。**全部留空按查詢,會撈出該登入者的所有拜訪紀錄。

### 5.3 哪些條件會靜默濾掉資料

這一節是本章重點。`CASI001` 有 **6 個不會提示的過濾**:

#### (1) `USAGE = '3'` 硬條件

```
WHERE 1=1 AND CLS001A.USAGE = '3'
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:185-186`。非 `'3'` 的拜訪單在這支畫面**永遠查不到**,畫面上也沒有任何欄位可以改這個條件。`CASM002` 有同樣的限制(而且是內外各一次),但 `CASB001` 沒有——**同一批資料,三支畫面的可見範圍不同**。

#### (2) 登入者員工代號的強制條件

```
if (iQUERY_EMP_NO != "028039" && iQUERY_EMP_NO != "102736" && iQUERY_EMP_NO != "103771"
    && iQUERY_EMP_NO != "850094" && iQUERY_EMP_NO != "990667")
    strSQL += " AND COD009.EMP_NO = '" + Row.Value + "'";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207`〔客戶特定〕。

**這是全模組唯一一處把權限寫在程式裡的地方**,而且是寫死的 5 個員工代號。要點:

| 面向 | 內容 |
|---|---|
| 效果 | 白名單內的人看得到全部;其餘人只看得到自己的 |
| 維護方式 | 改 code、重編 `PO.CAS`、重新部署 |
| 沒有的東西 | 沒有設定檔、沒有資料表、沒有註解說明這 5 個人是誰 |
| **反向風險** | 取不到員工代號時 `QUERY_EMP_NO` 這個參數根本不會被加(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136`),PO 端的 `if` 不成立 → **條件完全不加 → 看到所有人的資料** |

反向風險那條要展開講。UI 端:

```
ClientBizUtility biz = new ClientBizUtility();
string data = biz.GetEMP_INFO(this.UserID);
string[] words = data.Split(',');
if (words != null && words.Length > 1 && words[1] != "")
    this.QueryVDB.Util.Parameters.AddParametersRow("QUERY_EMP_NO", ...);
```

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136`。`ClientBizUtility`(無原始碼,從呼叫端反推)回傳一串逗號分隔字串,取第 2 段當員工代號。**只要這一段是空的——使用者沒有對應的員工資料、回傳格式改了、服務出錯回空字串——參數就不會被加,而 PO 端沒有「參數不存在就擋下」的分支。**結果是唯讀畫面的資料範圍從「自己」放大到「全部」,而且無聲無息。

#### (3) 起迄比較符號中間有空白

```
strSQL += " AND CLS001A.CALL_RPT_NO > = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219`,同樣寫法出現在 `:230`、`:241`、`:251`、`:262`、`:272`、`:283`、`:293` 共 8 處。

SQL 的 `>=` 是單一 token,中間不能有空白。**假設**:這 8 個條件只要有一個被加進去,整段 SQL 就會在 Oracle 端語法錯誤,被 `catch` 吞成「執行失敗,請檢查」(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:433-438`)。依據是 SQL 標準與 Oracle 的詞法規則;**無法在本機驗證**,要連 DB 才能確認。

這個寫法在全庫只出現在 4 個檔:`CASI001_PO`、`CASB001_PO`、`CLSI001_PO`、`CRMI001_PO`——全部是同一份查詢樣板的後代。如果這些畫面在正式環境是能用的,那代表 Oracle 或 ODP.NET 有容忍這種寫法的行為,**本文的假設就要推翻**。無論哪一邊為真,這 8 處都該修。

#### (4) 實際拜訪日期是字串比較

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` 直接把日期當字串比:`AND CLS001A.ACT_CALL_DATE >= '<值>'`。`ACT_CALL_DATE` 在 xsd 裡是 `xs:string`,存的是 `yyyyMMdd`(從 `DateTimeHelper.DateToString` 推,`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:64`),字串比較剛好等價於日期比較。**但只要有一筆資料存成別的格式(補空白、含分隔符號、空字串),它就會落在區間外而不被查到。**對照 `CASB001` 對同一個欄位用的是 `to_date(NVL(TRIM(...), '19000101'), ...)`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147`)——**同一個欄位,兩支畫面兩種比法。**

#### (5) `CLS002A` 的 `LEFT JOIN` 是對的,但 `CTL014` 那個不是

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:147-151`:

```
LEFT JOIN CLS002A ON CLS001A.CALL_RPT_NO = CLS002A.CALL_RPT_NO
LEFT JOIN CTL014  ON CLS001A.CALL_TYPE2 = CTL014.TEXTVALUE AND CTL014.SOURCETYPE = '447'
```

兩個都是 `LEFT JOIN`,不會濾掉主檔。**但 `CLS002A` 的 PK 是 `CALL_RPT_NO`,理論上 1:1;如果資料庫實際允許一單多列,這個 join 會讓拜訪單重複出現。**xsd 的 PK 宣告只約束 DataSet,不保證 DB(`architecture.md §5.5`)。

#### (6) 代碼說明 join 的分類碼寫死

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` 共 10 個 `COD006A` join,分類碼寫死成 `'P1'` / `'P3'` / `'20'`。分類碼一旦在 `COD006A` 改動,說明欄會整片變空——而且因為是 `LEFT JOIN`,主檔還在,只是說明是空的。**使用者看到的是「代碼有值但說明空白」,不會意識到是設定問題。**

### 5.4 取數之後做的事

PO 在 `LoadDataSet` 之前塞了一整排 `DefaultValue`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406-418`),包括 `STATUS = "301"`、四眼的 ID 欄全部設成當前使用者、日期欄設成當下。

**這對唯讀查詢沒有意義**——這些是 DataColumn 的預設值,只在「新增一列而沒給值」時生效,而查詢不會新增列。它是從 `CASB001` 那份樣板複製過來的(`CASB001` 確實會新增列),留在這裡是死碼。但它同時也是 §2.5 判定 `STATUS` 是 3 碼字串的證據之一。

查無資料時回 `AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:424-427`)。

### 5.5 兩支不在介面上的方法

`GetEmpNo` 與 `GetUidCode` 是 `public` 但**不在 `ICASI001_PO` 介面裡**(介面宣告被註解,`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:25-27`)。Ctl 走 `GetDaoInstance<ICASI001_PO>()` 取實例(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:39`),拿到的是介面型別,**呼叫不到這兩支**。它們是死碼。

`GetEmpNo` 還有一個潛在例外:直接取 `Rows[0]` 沒有筆數檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:469`),對照 `CASB001` 的同名方法有檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:408`)——同一份樣板,一支修過一支沒修。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 四組起迄只填「迄」 | 起空迄有值 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:71-72`、`:79-80`、`:87-88`、`:95-96` |
| 按查詢前 | 四組起迄的起 > 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:73-75`、`:81-83`、`:89-91`、`:97-99` |
| 按查詢前 | 實際拜訪日期起迄 | 同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:110-116` |
| 按查詢前 | 銷售機構金資起迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:101-107` |
| 按查詢前 | 至少填一個條件 | — | **沒有這條檢核** | — |
| 查詢時 | `USAGE = '3'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:186` |
| 查詢時 | 只看自己的資料(5 人除外) | 取得到員工代號時 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| 查詢時 | 取不到員工代號 | `GetEMP_INFO` 回空 | **靜默放大到全部資料** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136` |
| 查詢時 | 代碼說明的分類碼寫死 | 分類碼改動 | 過濾(無提示,說明變空) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 查詢時 | 日期用字串比較 | 資料格式不一致 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` |
| 查詢時 | SQL 語法錯(`> =`) | 有帶任一起迄條件 | **假設**整個查詢失敗,訊息「執行失敗,請檢查」 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219` |
| 查詢後 | 0 筆 | 無資料 | 警示 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:424-427` |

## 6. 批次(B)與 WindowsService

本模組只有一支 `CASB001`「代銷組客戶拜訪主管明細表」,**沒有 WindowsService**。

### 6.1 觸發

使用者在畫面上按「執行」鈕。流程是:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 按「查詢」撈出拜訪單清單到 grid | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:66-127` |
| 2 | 逐列勾 `ISCHECK`,或按「全選」/「全不選」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:245-270` |
| 3 | 雙擊已勾選的列 → 開 `CASB001p0` 編輯主管意見等欄位 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:205-224` |
| 4 | 按「執行」→ `DoExecute` → PO 的 `ExecuteNonQuery` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASB001_Ctl.cs:45-51` |
| 5 | 執行成功後逐列寄信 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342` |

第 3 步的雙擊有個守門:**沒勾 `ISCHECK` 的列雙擊沒反應**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212`),而且判斷用的欄位名是 `"IsCheck"`(大小寫與其他地方的 `"ISCHECK"` 不同)。Infragistics 的 `Cells[...]` 索引不分大小寫,所以能用,但不一致。

### 6.2 輸入(查詢條件)

| 參數 | PO 端條件 | 錨點 |
|---|---|---|
| `ACT_CALL_DATE_BGN` / `_END` | `to_date(NVL(TRIM(ACT_CALL_DATE),'19000101'),'yyyy-MM-dd') >= to_date(' <值前 10 碼> ','yyyy-MM-dd')` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147`、`:163` |
| `EMP_NO` | `= 值`(值先 `Replace("'","")`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:178` |
| `PR_NAME` | `CRM003A.PR_NAME = 值`(UI 端先把 `'` 換成 `''`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:188` |
| `AREA_CODE` | **`CRM003A.AREA_CODE = 值`** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:199` |
| `CFM_USER` | `'Y'` → `CFM_USER1 = 'Y' OR CFM_USER2 = 'Y'`;否則 → `CFM_USER1 <> 'Y' AND CFM_USER2 <> 'Y'` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:203-216` |

UI 端只有兩條檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:71-127`、`:229-237`):

| # | 檢核 | 結果 |
|---|---|---|
| 1 | 實際拜訪日期 / 業務員工編號 / 銷售機構關鍵字 必擇一 | 阻擋 |
| 2 | 實際拜訪日期起 ≤ 迄 | 阻擋 |

**三個會咬人的查詢問題:**

1. **「未閱」查不到真正的未閱。**`CFM_USER1 <> 'Y' AND CFM_USER2 <> 'Y'` 在 Oracle 裡碰到 NULL 會得到 unknown,整列被濾掉。而**從沒被主管碰過的拜訪單,這兩欄本來就是 NULL**。所以「未閱」這個預設查詢條件(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:42`、`:60`)**撈不到全新的拜訪單**,只撈得到曾經被寫過非 `'Y'` 值的那些。這是本模組最會咬人的過濾。

2. **`PR_NAME` 是等於不是 like。**UI 的欄位標籤叫「銷售機構關鍵字」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:84` 的訊息文字),但 SQL 是 `=`。使用者按「關鍵字」的習慣輸入會查不到東西。

3. **`AREA_CODE` 取自 `CRM003A` 而不是 `CAS004A`。**`CASM002` 與 `CASI001` 的區域別都是從 `CAS004A`(業務員的機構分配)推出來的,`CASB001` 直接用機構主檔上的欄位。**三支畫面的「區域別」語意不同**,篩選結果不會一致。

另外,**`CASB001` 的查詢沒有 `USAGE` 條件**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:134` 的 `WHERE 1=1` 後面沒有接),所以它看得到 `CASM002` / `CASI001` 看不到的資料。

### 6.3 寫哪些表

**只寫 `CLS002A` 一張表**,用一段固定的 `UPDATE`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:302-323`),逐列跑(`:330-358`)。

被更新的欄位分兩類:

| 類 | 欄位 | 值的來源 |
|---|---|---|
| 業務欄(5 個) | `MGR_DESC` `CFM_USER1` `CFM_USER2` `CONNECT_DESC` `CONNECT_RE` | grid 那一列的值 |
| **四眼欄(13 個)** | `STATUS` `CREATEID` `CREATEDATE` `ENTRYID` `ENTRYDATE` `UPDATEID` `UPDATEDATE` `VERIFYID` `VERIFYDATE` `APPROVEID` `APPROVEDATE` `REJECTID` `REJECTDATE` | **全部由程式直接指定** |

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354`。四眼欄的值:

| 欄位 | 值 |
|---|---|
| `STATUS` | `"301"` |
| `CREATEID` `ENTRYID` `UPDATEID` `VERIFYID` `APPROVEID` | **當前操作者** |
| `CREATEDATE` `ENTRYDATE` `UPDATEDATE` `VERIFYDATE` `APPROVEDATE` | **當下時間** |
| `REJECTID` | `" "`(一個空白) |
| `REJECTDATE` | `1900/01/01` |

**這是本模組最嚴重的治理問題,三層:**

1. **繞過四眼引擎。**一個人按下按鈕,`VERIFYID` 與 `APPROVEID` 同時變成他自己——四眼的「輸入 / 驗證 / 覆核要三個階段」在這裡完全失效。

2. **蓋掉建檔軌跡。**`CREATEID` / `CREATEDATE` 被改成執行批次的人與時間,原本誰建的、何時建的**永久遺失**。

3. **`CLS002A` 是 CLS 模組的表。**CLS 自己的畫面如果依賴四眼狀態機,會看到不符流程的資料(§8)。

`CLS001A`(主檔)**完全不動**,所以主檔與明細的四眼狀態會從此不一致。

### 6.4 寫入實作的四個問題

```
i = dbTA.ExecuteNonQuery(cmd, tran);
i = 1;
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356`。

| # | 問題 | 後果 |
|---|---|---|
| 1 | 實際影響筆數被丟掉,硬設成 `1` | 更新 0 筆(單號不存在於 `CLS002A`)也視為成功 |
| 2 | `if (i > 0) tran.Commit();`(`:359-362`) | **一列都沒勾時 `i` 是 0,既不 commit 也不 rollback**,交易在 `finally` 被 `Dispose`(`:384`),靠 Oracle 隱含回滾 |
| 3 | 成功路徑從不 `AddResultRow` | `model.Utility.Result` 只有失敗時才有列 |
| 4 | 綁定變數寫成 `: STATUS`(冒號後有空白) | 見下 |

第 3 點的連鎖效應在 UI:寄信那段的前置條件是 `this.ProcessVDB.Util.Result.Rows.Count > 0 && this.ProcessVDB.Util.Result[0].ReturnCode`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:315`)。PO 成功時沒塞任何結果列,所以**這個條件能不能成立,完全取決於框架的 `ExecPOActionToViewVDB` 有沒有補一列**(無原始碼,從呼叫端反推)。**假設**:框架會補,依據是若不補則本功能的寄信從來沒運作過,而郵件主旨與內容寫得很完整不像沒用過。這條要現場確認。

第 4 點:`UPDATE` 語句裡 13 個綁定變數寫成 `STATUS = : STATUS`、`WHERE CALL_RPT_NO =: CALL_RPT_NO`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:309-323`),冒號與名稱中間有空白,而前 5 個業務欄寫的是正常的 `:MGR_DESC`(`:304-308`)。同一段 SQL 兩種寫法。ODP.NET 對 `: NAME` 的處理方式沒有原始碼可查,**假設**它能接受(依據是這功能有在用,而且 13 個參數都有 `AddInParameter`),但這是要驗的。

### 6.5 寄信

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342`。逐列判斷:勾選了 **且** `CONNECT_RE = 'Y'`(業務需回覆)才寄。

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 用該列的 `EMP_NO` 查 `UID_CODE` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:320` |
| 2 | 用 `UID_CODE` 查 EMAIL | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:321` |
| 3 | 有 EMAIL → `SendMailTo`,寄件人是操作者的 EMAIL | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:328-330` |
| 4 | 沒 EMAIL → `MessageBox` 警示,繼續下一列 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` |

三個問題:

1. **N+1 次遠端往返。**每一列都打兩次 Pxy(`GetUidCode` + `GetEMAIL`),而且第 3 步又多打一次 `pxy.GetEMAIL(user)` 取操作者信箱(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:330`)——那個值在迴圈裡是固定的,卻每列重算。100 列就是 300 次 Remoting 往返。

2. **`GetUidCode` 的 SQL 缺括號。** `` WHERE EMP_NO = '<值>' AND TRIM(LEAVE_DATE) IS NULL OR LEAVE_DATE >= TO_CHAR(SYSDATE, 'YYYYMMDD')`` `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432`。`AND` 的優先序高於 `OR`,所以實際語意是 `(EMP_NO = 值 AND 未離職) OR (任何人 LEAVE_DATE >= 今天)`。**只要資料庫裡有任何一位未來離職日的員工,這支查詢就會回傳他的 `UID_CODE`**,而程式取 `Rows[0]`(`:443`)。結果是**信可能寄給錯的人**。這是本節最會咬人的一條。

3. **迴圈沒有 try/catch。**任一列寄信失敗就中斷整個迴圈,後面的列不會寄,而且資料已經 commit 了。

### 6.6 與 M 畫面的關係

| 面向 | `CASM002`(維護) | `CASB001`(批次) |
|---|---|---|
| 動到 `CLS002A` 的哪些欄 | 9 個業務欄 | 5 個 + 13 個四眼欄 |
| 四眼 | 走引擎 | **繞過** |
| `USAGE` 過濾 | 有 | **無** |
| 區域別來源 | `CAS004A` | `CRM003A` |
| 對 `CLS001A` | 增刪改 | 只讀 |

**兩支畫面對同一張表的寫法完全不同,而且沒有任何一方知道另一方存在。**在 `CASM002` 送審中的拜訪單,可以同時被 `CASB001` 從背後把明細改掉並蓋成「已覆核」。

### 6.7 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 日期 / 員工 / 機構關鍵字 必擇一 | 三個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:79-85` |
| 按查詢前 | 實際拜訪日期起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:233-235` |
| 查詢時 | 「未閱」條件濾掉 NULL | 欄位是 NULL | **過濾(無提示,且違反直覺)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` |
| 查詢時 | 機構名稱是等於不是 like | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:188` |
| 查詢時 | 沒有 `USAGE` 過濾 | 永遠 | (比 M / I 看得更多) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:134` |
| 雙擊列 | 未勾選不可編輯 | `ISCHECK` 是 false | 阻擋(靜默 return) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212` |
| 按執行前 | 只有「顯示既有錯誤清單」 | 清單非空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:188-197` |
| 按執行前 | 至少勾一列 | — | **沒有這條檢核** | — |
| 執行時 | 未勾選的列跳過 | `ISCHECK` false | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:334` |
| 執行時 | 更新 0 筆也算成功 | 單號不在 `CLS002A` | **靜默視為成功** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356` |
| 執行時 | 一列都沒勾 | `i` 停在 0 | 不 commit 也不 rollback | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:359-362` |
| 執行時 | 四眼欄被直接覆寫 | 永遠 | 記錄不擋(**治理漏洞**) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341-353` |
| 寄信時 | 業務不需回覆 | `CONNECT_RE <> 'Y'` | 過濾(無提示) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:323` |
| 寄信時 | 查無 EMAIL | 空字串 | 警示(不擋,繼續下一列) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` |
| 寄信時 | `UID_CODE` 查詢缺括號 | 有未來離職日的員工存在 | **可能寄給錯的人** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432` |
| 寄信時 | 任一列丟例外 | — | 中斷整個迴圈(資料已 commit) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:317-338` |

## 7. 報表(R)

```text
[圖] CAS 報表的資料流：UI 選種類、Ctl 分兩條路、PO 呼叫版控外的 SP、最後落到 Crystal 或 Excel
圖中文字:① 用戶端挑報表種類 → 決定 ReportClass 與 RPT_KIND / CASRxxx UI / uopt 選項決定種類 / SetQueryParameters / ReportClass 字串 / QueryVDB Parameters / SDATE EDATE RPT_KIND / ② 兩條獨立往返：資料一條、rpt 檔一條 / Ctl GetReportData / 走 PO 取資料 / Ctl GetReportObject / 用戶端指定類別名 / CRReportTransfer / 無原始碼 回傳 byte / ③ PO：SP + RefCursor，SQL 一行都不在程式裡 / GetStoredProcCommand / S_TA_CASRnnn_GET / CommandTimeout = 0 / 永不逾時 / C_RES RefCursor / 落地成結果集表 / SP 不在版控 / 8+2 支全部看不到 / ④ 落地：Crystal 或 Excel 二選一 / CreateCRReportDocument / 寫暫存檔再 Load / CrystalViewForm / 預覽視窗 / ExcelCreator / CASR002 只走這條 / 19 支 rpt / 2 支靠 PostBuild xcopy
```

*圖:圖 4 報表流。橘框=本模組程式碼；黑框=無原始碼（框架或版控外的 SP）；橘虛框=要特別留意的行為。資料與 rpt 檔是兩次獨立的遠端往返，版本不一致時不會有任何錯誤訊息。*

8 支 R 畫面、19 支 `.rpt`。**這一章跟前面幾章幾乎沒有交集**:報表不引用任何 CAS 的維護 PO,資料全部來自版控外的 SP,連表名都看不到(§1.1 的第 2 點)。

所以本章能寫的只有三件事:**哪支畫面吐哪些 `.rpt`、呼叫哪支 SP、送哪些參數**。SP 裡面怎麼算,repo 內查不到,要問 DBA 或去 Oracle 撈 `USER_SOURCE`。

### 7.1 一覽

| 畫面 | 取數 SP | `.rpt` | 挑 rpt 的依據 | 錨點 |
|---|---|---|---|---|
| `CASR001` | `S_TA_CASR001_GET` | `CASR001RPS` `CASR001RPS2` `CASR001RPS3` `CASR001RPS4` `CASR001RPS5` `CASR001RPS6` | 報表種類單選鈕的索引 0~5 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:89-113` |
| `CASR002` | `S_TA_CASR002_GET` | **無** | — | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:247-314` |
| `CASR003` | `S_TA_CASR003_GET` | `CASR003RPS` `CASR003RPS1` | 交易別單選鈕 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:178-182` |
| `CASR004` | `S_TA_CASR004_GET`(列印)/ `S_TA_CASR004_GET_XLS`(匯出) | `CASR004RPS` | 固定一支 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:294-296` 配 `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |
| `CASR005` | `S_TA_CASR005_GET` | `CASR005RPS` `CASR005RPS1`(另有孤兒檔 `CASR005RPS11`) | 報表種類單選鈕的索引 0 / 非 0 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:190-192` |
| `CASR006` | `S_TA_CASR006_GET` | `CASR006RPS` `CASR006RPS2` | 交易別;選「合併」時**連續出兩張** | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:173-189` |
| `CASR007` | `S_TA_CASR007_GET` | `CASR007RPS` | 固定一支 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:138` |
| `CASR008` | `S_TA_CASR008_GET` | `CASR008RPS` `CASR008RPS1` `CASR008RPS2` | 三個獨立勾選框,勾幾個出幾張 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:344-364` |

**19 支 `.rpt` 只有 17 支被程式指名**(上表共 15 支 + `CASM002RPS` 屬 §4.2 的拜訪記錄單 + `CASR005RPS11`)。`CASR005RPS11` 全庫**零引用**,是孤兒;它與 `CASR003RPS` 一起躺在 `ReportUI.CAS` 資料夾,靠 PostBuild 的 `xcopy "$(ProjectDir)*.rpt"` 一起被複製到平台的報表目錄(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331`)。也就是說**它會被交付到正式環境,但沒有任何程式叫得動它**。

### 7.2 八支 SP 的參數

全部走同一個樣板:`GetStoredProcCommand` → `AddInParameter`(一律 `Varchar2`)→ `AddOutParameter`(`RefCursor`)→ `LoadDataSet`。

| 畫面 | 參數(依程式順序) |
|---|---|
| `CASR001` | `iSDATE` `iEDATE` `iEMP_NO` `iRPT_KIND` |
| `CASR002` | `iSDATE` `iEDATE` `iAGENT_ID` `iAGENT_CODE` `iEMP_NO` `iPRI_TYPE` `iFUND_ID` `iPROF_TYPE3` `iBANK_KIND` `iRPT_KIND` |
| `CASR003` | `iSDATE` `iEDATE` `iCRNCY` `iBANK_KIND` `iTRADE_KIND` `iAGENT_ID` `iAGENT_CODE` `iFUNDS` |
| `CASR004` | `iSDATE` `iEDATE` `iAGENT_ID_S` `iAGENT_CODE_S` `iAGENT_ID_E` `iAGENT_CODE_E` `iDEPT_CODE` `iFUNDS` `iFUND_YN` |
| `CASR005` | `iSDATE` `iEDATE` `iDATE_KIND` `iFIRST_NULL` `iAGENT_ID` `iDEPT_CODE` `iFUNDS` `iRPT_KIND` |
| `CASR006` | `iKIND` `iSDATE` `iEDATE` `iFUND` `iALLOT_CODE` |
| `CASR007` | `iSDATE` `iEDATE` `iAGENT_ID` `iAGENT_CODE` |
| `CASR008` | `iSDATE` `iEDATE` `iAGENT_ID_ST` `iAGENT_CODE_ST` `iAGENT_ID_END` `iAGENT_CODE_END` `iDEPT_CODE` `iINV_AREA` `iPROF_TYPE` `iPROF_TYPE3` `iRPT_KIND` `iRPT_FIRST` |

錨點:`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:61-66`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:61-72`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:61-70`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:70-80`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:61-71`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:65-73`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR007_PO.cs:61-66`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:69-82`。

三件跨全部八支的共同事實:

| 事實 | 說明 | 錨點(舉一) |
|---|---|---|
| **參數全部綁定,不串字串** | 與 M / I / B 畫面相反,這裡沒有 SQL 注入風險 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:61-68` |
| **`CommandTimeout = 0`** | 永不逾時。SP 掛住時使用者端會一直轉,沒有取消機制 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` |
| **`catch` 把訊息吃掉** | `AddResultRow(false, 0, string.Empty)`——回傳失敗但**訊息是空字串**,使用者只看得到框架的預設文字 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:81-84` |

最後一條要強調:**八支報表只要 SP 出錯,使用者拿到的訊息都是空的**,連「查無資料」都不是。要知道真正發生什麼事只能看伺服器端的 log。

### 7.3 結果集怎麼挑:三種寫法、三種毛病

八支裡有三支要依畫面選項決定把 RefCursor 灌進哪一張結果集。三支的寫法都不一樣,而且各有一個洞。

#### `CASR002` — 11 選 1 的 if-else 階梯

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-113`。依 `RPT_KIND`(1~6)配 `BANK_KIND`(1 = 總行 / 其他 = 分行)決定表名:

| `RPT_KIND` | `BANK_KIND` = 1 | 其他 |
|---|---|---|
| 1 | `CASR002_ALLOT_HQ` | `CASR002_ALLOT_BRH` |
| 2 | `CASR002_REDEM_HQ` | `CASR002_REDEM_BRH` |
| 3 | `CASR002_STOCK_HQ` | `CASR002_STOCK_BRH` |
| 4 | `CASR002_NET_HQ` | `CASR002_NET_BRH` |
| 5 | `CASR002_HQ` | `CASR002_BRH` |
| 6 | `CASR002_STAS`(不分總分行) | 同左 |

**沒有 `else`。**`RPT_KIND` 不是 1~6 時 `tblName` 停在空字串,下一行 `LoadDataSet(..., new string[] { "" })` 與再下一行 `model.DataEntity.Tables[""].Rows.Count`(`:115`、`:118`)都會炸。UI 端的「下載EXCEL必須選取其中之一」檢核**是註解掉的**(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:94`),所以這條路不是理論上的。

#### `CASR005` — 二選一,但兩個選法各看各的

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:72-75`:`RPT_KIND == "1"` 灌進 `CASR005`,否則灌進 `CASR005_S`。 UI 端挑 `.rpt` 卻是看 `CheckedIndex == 0`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:190-192`),而送給 SP 的是同一組單選鈕的 `Value`(`:188`)。

**假設**:該單選鈕索引 0 的 `Value` 就是 `"1"`,兩邊才對得起來;依據是 `.rpt` 的中文名(索引 0 是「明細表」)與 PO 的結果集(`CASR005` 是明細、`CASR005_S` 是統計)語意一致。`Value` 的實際設定在 `.Designer.cs`,**本文不讀 Designer**,要確認請直接開畫面。**一旦 `Value` 與索引脫鉤,就會出現「拿明細的版面套統計的資料」。**

判斷「有沒有資料」時用的是 `CASR005.Count + CASR005_S.Count > 0`(`:78`),兩張加總——這一段反而是穩的。

#### `CASR008` — 迴圈跑多次,但計數漏掉一種

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:65-89`。`RPT_KIND` 是逗號串,每一段跑一次 SP,表名是:

```
tblName = aRPT_KIND[i] == "0" ? "CASR008" : ("CASR008_" + aRPT_KIND[i]);
```

`:86`。但下面數筆數的迴圈寫的是:

```
if (model.DataEntity.Tables["CASR008_" + s] != null)
    nRow = nRow + model.DataEntity.Tables["CASR008_" + s].Rows.Count;
```

`:93-95`。**`"0"` 那一段灌進 `CASR008`,計數時卻去找 `CASR008_0`**,找不到就跳過。所以使用者只選到 `"0"` 這一類時,即使 SP 撈回一堆資料,`nRow` 仍是 0 → 回「查無資料」(`:103`)。這是本章最會咬人的一條。

`iRPT_FIRST` 參數只有第一圈是 `"Y"`(`:80`),**推測**是給 SP 判斷要不要先清暫存表;依據是參數名與 `i == 0` 的條件,SP 無原始碼無法證實。

#### 另外兩支的分支

`CASR004` 是**換 SP 不是換表**:`RPT_KIND` 等於 `"RPT"` 走 `S_TA_CASR004_GET`,否則走 `S_TA_CASR004_GET_XLS`(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60`)。UI 的列印路徑硬塞 `"RPT"`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:282`)、匯出路徑硬塞 `"XLS"`(`:380`)。**兩支 SP 的欄位必須一致才不會壞版面,而這件事沒有任何程式保證。**

`CASR006` 用 `switch (sAllot_Code)`,三個 case:`"1"` 一般、`"4"` 定期定額、`""` 合併(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:74-94`)。**同樣沒有 `default`**,但這支比較安全:落空時 `nCnt` 留 0 → 回「查無資料」,不會丟例外。三個 case 的 `LoadDataSet` 三行一模一樣,差別只在計數用哪一張表。

### 7.4 一次出多張報表的兩支

`CASR006` 與 `CASR008` 會在一次操作裡連續出多張 `.rpt`,用的是同一套手法:

| 步 | 做什麼 | `CASR006` 錨點 | `CASR008` 錨點 |
|---|---|---|---|
| 1 | 第一次進 `BeforePreview` 時 `e.Cancel = true`,取消框架原本的那一次 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:130-133` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:302-303` |
| 2 | 立一個 `isPrintData` 旗標,把查詢參數存進成員變數 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:135-137` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:305-307` |
| 3 | 用匿名委派 `doAct` 逐張呼叫 `DoPreview()` / `DoPrint()` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:142-161`、`:173-189` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:312-326`、`:344-364` |
| 4 | 每一張進來時走 `else` 分支,只設 `.rpt` 類別名 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:196-207` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:369-375` |
| 5 | 資料只查一次,快取在 `m_ReportData` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:425-435` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:280-288` |

兩個要注意的:

1. **`CASR006` 的兩段註解文字是別支畫面的。**`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:176`、`:185` 寫「既有客戶交易異常表」「既有客戶交易異常表-受益人明細」,但實際設的報表名是「每日申購信託基金交易明細表」。複製樣板時沒改註解,讀碼會被誤導。

2. **`CASR008` 的三個勾選框全不勾時,三個 `if` 都不成立,什麼都不會發生**(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:344-364`),而且第一次的作業已經被 `e.Cancel = true` 取消了。使用者按下預覽,畫面沒有任何反應也沒有訊息。對應的「至少選一項」檢核在 `DoValidate` 裡,是由 `ValidateGroupBoxChecked` 對 `ugrpRPT_KIND` 做的(`:235`),**但那一組是「報表選項」,不是決定出哪幾張 rpt 的那三個勾選框**。

### 7.5 畫面端的檢核

| 畫面 | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| `CASR001` | 拜訪日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:60-61` |
| `CASR001` | 報表種類必選 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:63-64` |
| `CASR001` | 種類 1、2 時員工代碼不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:65-67` |
| `CASR001` | 車資表時起迄必須同年月 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:69-71` |
| `CASR002` | 日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:90-91` |
| `CASR002` | 個別基金時基金不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:97-98` |
| `CASR002` | 報表種類必選 | **被註解,不執行** | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:93-94` |
| `CASR003` | 申購期間起 ≤ 迄 / 機構至少一勾 / 基金至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:159-166` |
| `CASR004` | 統計日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:95-96` |
| `CASR004` | 機構別 / 機構代碼起迄成對與大小 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:99-132` |
| `CASR004` | 基金明細至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:134-135` |
| `CASR005` | 日期起 ≤ 迄 / 基金至少一勾 / 機構區分碼至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:56-64` |
| `CASR006` | 申購日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:94-95` |
| `CASR007` | 日期起 ≤ 迄 / 機構至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:116-120` |
| `CASR008` | 統計日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:163-164` |
| `CASR008` | 機構別 / 機構代碼起迄成對與大小 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:166-191` |
| `CASR008` | 投資地區 / 基金類型 / 管理費率類別 / 報表選項各至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:193-243` |
| 全部 | 匯出 Excel 時路徑不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:370-371`(舉一) |

`CASR008` 那四組勾選的取值方式要單獨記:`ValidateGroupBoxChecked` **把送給 SP 的代碼從控件名稱的最後一個字元切出來**:

```
grp.Controls.OfType<UltraCheckEditor>().Where(c => c.Checked)
   .OrderBy(c => c.TabIndex)
   .Select(c => c.Name.Substring(c.Name.Length - 1));
```

`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:110-118`。也就是說 **`uchkINV_A` 這種控件改個名字,送給 SP 的參數值就變了**,而且沒有任何地方寫下這個約定。投資地區那一組還多一條特例:名稱結尾是 `F` 的會被展開成 `F,G`(`:114`)〔客戶特定〕。這是典型的「位置取參數」。

### 7.6 `CASR001` 的員工代碼有一條特別的預設

`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:119-130`:員工代碼欄空白時,程式會去 `EmployeeDataSrc` 用 `IS_CASB001 = 'Y'` 撈一批員工,把代號用逗號串起來當 `EMP_NO` 送給 SP。

兩件事:

1. **「全部」的定義不是真的全部**,是「`IS_CASB001` 為 `Y` 的那一批」。這個旗標的意義在 CAS 內看不到(它屬於員工資料來源,無原始碼,從呼叫端反推),**推測**是「代銷組客戶拜訪作業的適用人員」,依據是旗標名稱直接引用 `CASB001` 這支畫面。

2. **`sEmp` 是畫面層級的成員變數,只在欄位為空時才重算**。同一次開窗內先指定員工、再清空,第二次的 `sEmp` 用的是前一次算好的值——不影響結果(內容一樣),但這個寫法在別的情境會咬人。

### 7.7 對維護資料的關係

**報表不寫任何表,也不引用任何 CAS 的維護 PO。**八支 `_PO` 全部是「不繼承基底、自己 `new Database`、自己 `BeginTransaction` 只為了讀」的樣板(`architecture.md §6.5`)。

所以下列問題在 repo 內**回答不了**,要去 SP 裡查:

| 問題 | 為什麼查不到 |
|---|---|
| `CASM004` / `CASM005` 設的分配比率,哪一支報表在用? | 沒有任何 `.cs` 讀 `CAS004A` / `CAS005A` 做計算(§0.3) |
| `CASM003` / `CASM006` 設的年度目標,哪一支報表在比達成率? | 同上 |
| 報表數字與畫面數字對不起來時該查哪裡? | 只能查 SP |

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` 是專案樣板留下的空類別,12 行、無任何內容,從沒被引用。

## 8. 跨模組共用

```text
[圖] 改 CRM003A、CLS001A、CLS002A、DSM001A、DSM002A 會波及哪些畫面
圖中文字:改這四張表，要一起看的畫面 / CRM003A / 72 欄 四眼齊 / CASM001 主檔 / 本模組 / CRMM003 主檔 / CRM 模組 / CASM002 CASI001 / join 取機構名 / CLS001A／CLS002A：CAS 三支畫面 + CLS 模組自己 / CLS001A CLS002A / 85+26 欄 四眼齊 / CASM002 維護 / USAGE=3 才看得到 / CASI001 查詢 / 同樣 USAGE=3 / CASB001 批次 / 不濾 USAGE 直接改 / CLS 模組畫面 / 同表另一組入口 / DSM001A／DSM002A：CASM006 與 DSMM001 兩個入口 / DSM001A DSM002A / 年／月業績目標 / CASM006 / 只看 8 個部門 / DSMM001 / DSM 模組 無部門限制 / CAS 自有表被誰用（改動只影響本模組） / CAS001A CAS002A / 只有 CASM003 / CAS003A / CASM001 + CASM002 讀 / CAS004A / CASM004 + M002/I001 取區域別 / CAS005A / 只有 CASM005
```

*圖:圖 5 跨模組影響面。橘框=被共用的表；灰虛框=本模組以外的入口；橘虛框=行為與其他入口不一致的地方。左邊的表只要加欄或改型別，箭頭所指的每個入口都要重編與回歸。*

這一章回答一個問題:**改 `CRM003A` / `CLS001A` / `CLS002A` / `DSM001A` / `DSM002A` 會打到誰。**

10 張表裡 CAS 自己的只有 5 張(`CAS001A` `CAS002A` `CAS003A` `CAS004A` `CAS005A`),另外 5 張都是借來的,而且是當**主檔**在借(§0.2)。

### 8.1 三張借來的主檔,三種借法

| 表 | CAS 怎麼用 | 別人怎麼用 | 兩邊會不會看到同一筆 |
|---|---|---|---|
| `CRM003A` | `CASM001` 當主檔,增刪改 | `CRMM003` 當主檔,增刪改;`TMKM001` / `TMKM002` 唯讀 join | **不會**,靠 `USAGE` 分治(§8.2) |
| `CLS001A` + `CLS002A` | `CASM002` 當主明細;`CASB001` 直接 UPDATE 明細 | `CLSI001` / `CRMI001` / `DSMI001` 三支查詢畫面唯讀 | **會**,`CASM002` / `CASI001` 有 `USAGE` 過濾,另外四支沒有(§8.3) |
| `DSM001A` + `DSM002A` | `CASM006` 當主明細 | `DSMM001` 當主明細 | **會,而且範圍不一樣**(§8.4) |

### 8.2 `CRM003A`:靠 `USAGE` 切成兩個互不相見的世界

| 誰 | 寫進去的 `USAGE` | 查詢時的條件 | 錨點 |
|---|---|---|---|
| `CASM001` | `'3'` | `= '3'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| `CRMM003` | `'1'` | `= '1'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `TMKM001` | 不寫 | `= '1'`(唯讀 join) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` |
| `TMKM002` | 不寫 | **無 `USAGE` 條件**(`LEFT JOIN` 取機構名) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` |

**結論:資料層面互不干擾,schema 層面完全共用。**

| 改什麼 | 會打到誰 |
|---|---|
| 加欄位 / 改型別 / 改長度 | `CASM001Model.xsd` 與 `CRMM003Model.xsd` **兩份 xsd 都要重生**,兩支畫面都要回歸(`architecture.md §5`) |
| 改 PK(`PR_NO`) | `CASM001` 的取號、`CASM002` / `CASI001` / `CASB001` 的 join、`CRMM003`、`TMKM001`、`TMKM002` 全打到 |
| 改 `USAGE` 的值域 | **兩個模組的可見範圍同時翻掉**——這是最危險的一種改動 |
| 只改 `USAGE = '3'` 那一批資料 | 只有 CAS 受影響 |

`CRM003A` 的欄位定義同時出現在三份 xsd(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`),**三份不同步就會出現「某支畫面存得進、另一支讀不出來」**。

另外還有三處唯讀引用不在維護畫面上,改欄位時容易漏:`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`,以及共用件 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs`。

### 8.3 `CLS001A` / `CLS002A`:五支畫面、四種可見範圍

| 畫面 | 模組 | 對 `CLS001A` | 對 `CLS002A` | `USAGE` 過濾 |
|---|---|---|---|---|
| `CASM002` | CAS | 主檔,增刪改 | 明細,增刪改 | **有**(內外各一次) |
| `CASI001` | CAS | 唯讀 | 唯讀 `LEFT JOIN` | **有** |
| `CASB001` | CAS | 唯讀 | **直接 UPDATE,繞過四眼** | **無** |
| `CLSI001` | CLS | 唯讀 | 唯讀 | 待查(本文未讀 CLS) |
| `CRMI001` | CRM | 唯讀 | 唯讀 | 待查 |
| `DSMI001` | DSM | 唯讀 | 唯讀 | 待查 |

錨點:`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs`。三支都沒有任何 `INSERT` / `UPDATE` / `DELETE`,**只有 CAS 會寫這兩張表**。

**這裡最要緊的不是「誰讀」,是 `CASB001` 那段 UPDATE(§6.3)。**它把 `CLS002A` 的 13 個四眼欄位直接覆寫成「同一個人輸入 + 驗證 + 覆核」,而 `CLS001A` 主檔不動。後果:

| 現象 | 誰會踩到 |
|---|---|
| 主檔與明細的四眼狀態不一致 | `CASM002` 再開同一筆時,明細已經是 `'301'` 而主檔還在原狀態 |
| `CREATEID` / `CREATEDATE` 被蓋掉 | 任何要追「這筆是誰建的」的稽核需求,包含 CLS 自己 |
| 沒有 `USAGE` 過濾 | `CASB001` 改得到 `CASM002` / `CASI001` 根本看不到的資料 |

**改 `CLS002A` 的欄位時,一定要同時檢查 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:302-323` 那段手寫的 `UPDATE`**——它把欄位名寫死在字串裡,xsd 重生不會同步它,改錯只有在執行時才會炸。

`CLS002A` 的欄位定義出現在三份 CAS 的 xsd(`CASB001Model.xsd` / `CASB001View.xsd` / `CASM002Model.xsd`),CLS 那邊另有一份。

### 8.4 `DSM001A` / `DSM002A`:同一張表,兩支維護畫面,兩種員工範圍

`CASM006` 與 `DSMM001` 都把這兩張當主明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36`),**六個業績指標欄位一模一樣**。差別全在取數 SQL:

| 面向 | `CASM006` | `DSMM001` |
|---|---|---|
| 部門欄從哪來 | `COD009` 的部門欄 | **`SAL051` 的直銷部門欄** |
| 額外 join | 只有 `COD009`(INNER) | `COD009` **加** `SAL051`,兩個都是 INNER |
| 部門限制 | 寫死八個部門的白名單 | 沒有白名單,但被 `SAL051` 的 INNER JOIN 限制成「直銷員工」 |
| 年度查詢 | 只能等於 | 只能等於 |
| 錨點 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113-127`、`:210` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:113-131`、`:144-154` |

`DSMM001_PO` 第 112 行的註解直接寫明:「`SAL051` 為直銷的員工範圍」。

**所以兩支畫面看到的員工集合是兩個不同的集合,不是「一個包含另一個」:**

| 員工 | `CASM006` 看得到 | `DSMM001` 看得到 |
|---|---|---|
| 在八部門白名單內,且在 `SAL051` | ✔ | ✔ |
| 在白名單內,不在 `SAL051` | ✔ | ✘ |
| 不在白名單,在 `SAL051` | ✘ | ✔ |
| 兩者皆非 | ✘ | ✘ |

第二、三列就是「同一筆年度目標,一支畫面查得到、另一支查不到」的來源,而且**兩邊都不會提示**。要改任何一邊的範圍之前,先問清楚業務上這兩個集合是不是刻意分開的。

**`DSMM002` 不算在內。**它的主明細是 `DSM007A` / `DSM008A`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36`),檔案裡出現的 `DSM002A` 全部在註解區塊(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-119`),是從 `DSMM001` 複製樣板留下的。搜尋字串時會誤判,**別被騙**。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `DSM001A` `DSM002A` 欄位 | `CASM006Model.xsd` / `CASM006View.xsd` 與 `DSMM001Model.xsd` 都要重生,兩支畫面都要回歸 |
| 改 `CASM006` 的部門白名單 | 只影響 `CASM006`;`DSMM001` 不受影響 |
| 改 `SAL051` 的內容 | 只影響 `DSMM001` |
| 改 `COD009` | **兩支都影響**,而且因為是 INNER JOIN,刪一個員工等於讓他的目標整筆消失 |

### 8.5 共用的 UI 控件與下拉來源

CAS 沒有用到 `Dev/Common/Source/DataSource/PO.DataSource` 底下的共用 PO,但大量使用共用控件:

| 控件 | 用在哪 | 出現次數 |
|---|---|---|
| `ucFundID` | 報表側的基金選取 | 78 |
| `ucAgentCode` | 銷售機構代碼(靠 `TrustAgentID` 連動區別碼) | 77 |
| `ucEmployeeData` | 員工代碼(`Filter` / `IS_MARKETING` / `LEAVE_DATE` 三種過濾入口) | 53 |
| `ucAddress` | `CASM001` 的通訊地址拆解 | 5 |
| `EmployeeDataSrc` | `CASR001` 的「全部員工」預設值 | 4 |

全部無原始碼,從呼叫端反推。**`ucEmployeeData` 是最需要小心的一個**:它同時吃 `Filter` 字串與 `ConditionVDB` 參數兩種過濾,而 `CASM005` 兩種都設而且互相矛盾(§4.5)。

## 附錄 A. 資料表總表

| 表 | 欄位數 | 四眼欄位 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `CAS001A` | 9 | 無 | CAS | `CASM003` | — | 增刪改 |
| `CAS002A` | 8 | 無 | CAS | — | `CASM003` | 增刪改 |
| `CAS003A` | 35 | 有 | CAS | — | `CASM001` | 增刪改 |
| `CAS004A` | 10 | 無 | CAS | `CASM004` | — | 增刪改 + SP 複製 |
| `CAS005A` | 11 | 無 | CAS | `CASM005` | — | 增刪改 + 程式內複製 |
| `CLS001A` | 85 | 有 | **CLS**〔共用〕 | `CASM002` | — | 增刪改;`CASI001` / `CASB001` 唯讀 |
| `CLS002A` | 26 | 有 | **CLS**〔共用〕 | — | `CASM002` | 增刪改;`CASB001` **直接 UPDATE** |
| `CRM003A` | 72 | 有 | **CRM / TMK**〔共用〕 | `CASM001` `CRMM003` | — | 增刪改(限 `USAGE = '3'`) |
| `DSM001A` | 15 | 無 | **DSM**〔共用〕 | `CASM006` `DSMM001` | — | 增刪改 |
| `DSM002A` | 13 | 無 | **DSM**〔共用〕 | — | `CASM006` `DSMM001` | 增刪改 |

只讀不寫的外部表(join 進來取說明用,本模組從不寫入):

| 表 | 取什麼 | 被誰 join | join 型態 |
|---|---|---|---|
| `COD009` | 員工姓名、部門、離職日 | `CASM001` `CASM003` `CASM004` `CASM005` `CASM006` `CASI001` `CASB001` | `CASM003` / `CASM006` 是 **INNER**,其餘 `LEFT` |
| `COD006A` | 各類代碼說明 | `CASM001`(2 次)`CASM002`(2 次)`CASI001`(10 次) | `LEFT` |
| `CTL014` | 拜訪方式、投資特性說明 | `CASI001` `CASM002` | `LEFT` |
| `OFD068A` | 銷售機構名稱 / 簡稱 | `CASM004` `CASM005` | `LEFT` |
| `BMS001A` | 受益人姓名 | `CASM005` | `LEFT` |
| `SAL051` | (只在 `DSMM001` 用,列出供 §8.4 對照) | `DSMM001` | INNER |

兩張非實體結果集:`CAS004A_OVER`(`CASM004p0` 的超額清單)、`CAS005A_OVER`(`CASM005p0` 的超額清單)。它們不是資料表,是 SP 或程式回傳的暫時結果集(§4.4、§4.5)。

## 附錄 B. SP / Function / Trigger / View

**`DBScript/` 裡屬於本模組的 SP / Function / Trigger / View 是 0 支。**掃描母體(`docs/_candidates/cas.md` 第 3 節)是空表。

但程式確實呼叫了 10 支 SP,**全部不在版控內**:

| SP | 被誰呼叫 | 用途 | 呼叫點錨點 |
|---|---|---|---|
| `S_TA_CASM004_P01` | `CASM004p0` | 複製業務員的機構分配比率 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:97` |
| `S_TA_CASR001_GET` | `CASR001` | 訪談報告 6 種 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58` |
| `S_TA_CASR002_GET` | `CASR002` | 業務人員明細統計(11 種結果集) | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:56` |
| `S_TA_CASR003_GET` | `CASR003` | 銷售機構銷售總表 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:58` |
| `S_TA_CASR004_GET` | `CASR004`(列印) | 期間收入統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |
| `S_TA_CASR004_GET_XLS` | `CASR004`(匯出) | 同上的 Excel 版 | 同上 |
| `S_TA_CASR005_GET` | `CASR005` | 退休管家庫存明細 / 統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:58` |
| `S_TA_CASR006_GET` | `CASR006` | 每日申購信託基金交易明細 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:60` |
| `S_TA_CASR007_GET` | `CASR007` | 定額契約統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR007_PO.cs:58` |
| `S_TA_CASR008_GET` | `CASR008` | 期間銷售統計 / 排行 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:61` |

**這 10 支的內容在 repo 內完全看不到。**要知道報表數字怎麼算、複製功能複製了什麼條件,只能去 Oracle 撈 `USER_SOURCE`,或問 DBA。改這些 SP 沒有版控保護,也沒有 code review 流程——這是本模組最大的結構性風險。

## 附錄 C. 代碼對照

`STATUS` 與本模組自訂旗標值見 §2.5,不重複。這裡補下拉選單的代碼來源編號(`GetDropDownDataSrc` / `GetDropDown9iDataSrc` 的參數)。

| 代碼 | 用途(取自程式註解) | 用在哪 |
|---|---|---|
| `062` | 銷售機構區別碼 | `CASM004` `CASM005` `CASM004p0` |
| `418` | 管理費率類別 | `CASR002` `CASR008` |
| `440` | 主管2(主管)閱 | **只有 `CASB001p0`** |
| `447` | 預估 / 實際拜訪方式 | `CASM002` `CASI001` `CASB001` |
| `448` | 往 / 返 | `CASM002` `CASI001` |
| `467` | 區域別 | `CASM004` `CASM005` `CASB001` |
| `468` | 組別 | `CASM004` `CASM005` |
| `469` | 投資特性(1 / 2 / 3) | `CASM002` `CASI001` |
| `470` | 主管閱(`CFM_USER1` / `CFM_USER2`) | `CASB001` `CASB001p0` `CASI001` |
| `471` | 業務需回覆否 | `CASB001` `CASI001` |
| `472` | 總行 / 分行別 | `CASB001` `CASB001p0` `CASI001` `CASI001p0` |
| `473` | 組長別 | `CASM004` `CASM005` |
| `474` | (無註解;對應 `SEND_FUND_YN`,呼叫已被註解) | `CASM001` |
| `494` | 業務已回覆 | `CASB001` `CASI001` |

**兩件要記住的:**

1. **同一個欄位兩個代碼來源。**`CFM_USER2` 在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.cs:207` 用 `440`,在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:293` 與 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:331` 用 `470`。**同一個欄位的下拉,彈出視窗與 grid 的選項可能不一樣。**

2. **註解與程式錯開一行。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:279-282` 的註解「總行」底下設的是區域別(`467`)、註解「預估拜訪方式」底下設的是主管閱(`470`)。**這一段的註解不能信**,要看控件名。

`COD006A` 的分類碼(`CODE_SORT`)與 `CTL014` 的 `SOURCETYPE` 對照見 §2.5。

## 附錄 D. 掃描母體與覆蓋率

母體來源:`docs/_candidates/cas.md`(由 `atlas_scan.py --module CAS` 產生)。

| 類別 | 母體 | 本文提及 | 覆蓋率 |
|---|---|---|---|
| 畫面 | 16(B 1 / I 1 / M 6 / R 8) | 16 | 100% |
| 實體表 | 10 | 10 | 100% |
| SP / Fn / Trigger / View | 0 | —(版控外的 10 支 SP 另列於附錄 B) | — |
| `.rpt` | 19 | 19 | 100% |
| WindowsService | 0 | — | — |

**沒有未提及的物件。**兩個要註記的邊界情況:

| 物件 | 狀態 | 處置 |
|---|---|---|
| `CASR005RPS11` | 在母體內,但全庫零引用(§7.1) | 已寫入本文並標為孤兒;**建議確認能否刪除** |
| `CAS004A_OVER` / `CAS005A_OVER` | **不在**母體的實體表清單內 | 它們是結果集不是表,本文在 §4.4 / §4.5 與附錄 A 標明 |

本文另外提及但不屬於 CAS 母體的物件(唯讀 join 或跨模組對照,列出以免被當成漏網): `COD009` `COD006A` `CTL014` `OFD068A` `BMS001A` `SAL051` `CRM006A` `CRM004A` `TMK001A` `DSM007A` `DSM008A`,以及畫面 `CRMM003` `CRMI001` `CRMB005` `CLSI001` `DSMM001` `DSMM002` `DSMI001` `TMKM001` `TMKM002` `OFDI011` `CRMR008`。

## 附錄 E. 讀本文時要注意的地方

按「讀碼時會被騙的方式」分類。嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 被註解掉但外殼還在的檢核

最常見的一類。**方法還在、介面還在、Ctl 還在,只有呼叫點被註解**,讀碼的人會以為這道檢核有效。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASM004p0` 的四條複製前檢核(年月大小、來源≠目標、存在性、100% 上限)全被註解 | 複製可以把資料蓋到不該蓋的地方,超額只能事後才報 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-118` | 高 |
| `IsEmpExsits` 三層(PO / 介面 / Ctl)都在,**零呼叫點**,而且它的「迄年月」條件也被註解 | 死碼;解開註解也不會照預期運作 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:241-263`、`:249`、`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM004_Ctl.cs:86-90` | 中 |
| `CASM002` 的三段「主談者資料不存在」檢核被註解,而且第三段複製貼上沒改對 | 解開註解也是錯的 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579` | 中 |
| `CASM001` 的 `ID_NODoValidate()` 方法留著但內容是空的,呼叫點也被註解 | 看起來有一道金資檢核,其實沒有 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:567-571`、`:363` | 中 |
| `CASM006` 的五個年度指標 + 五個明細指標「必須大於 0」全被註解,但六個總和檢核留著 | 允許「年度 0、每月 0」通過;搭配 E.4 的月分配缺陷會讓使用者卡住 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88`、`:106-119` | 中 |
| `CASM006` 的 `QueryVDB.Util.Parameters.Clear()` 被註解(另外三支 M 畫面都有) | 查詢條件累積,清空欄位查不乾淨 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370` | 高 |
| `CASM006` 的業績年度起迄檢核與 PO 的區間條件同時被註解 | 年度只能精確比對 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:353-357`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:142-160` | 低 |
| `CASM004` 的機構區別碼(迄)在 UI 不送參數、PO 整段註解,但查詢檢核還在驗它 | 畫面上兩個欄位只能填一樣的值 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:262-263`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:419-436` | 中 |
| `CASI001` 的銷售機構金資起迄檢核整段被註解 | 該組條件只剩一個欄位有效 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:101-107` | 低 |
| `CASR002` 的「報表種類必選」檢核被註解,而 PO 沒有 `else` | 沒選種類 → PO 端空表名 → 例外 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:93-94` 配 `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-118` | 高 |
| `CASM004` 的員工下拉部門排除整段被註解(留著「2015/12/25 改為代銷部門可修改」的說明) | 與 `CASM005` 的白名單不互斥 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:310-316` | 中 |
| `CASM005_PO` 的 region 名稱結尾多一個 `*/`,沒有對應的開頭 | 讀碼者會誤以為整段檢核是註解掉的(**它是活的**) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:219` | 低 |

### E.2 有訊息但沒有 `return` / 沒有 `Cancel`

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASM006` 選到已離職員工時跳訊息,**但照樣選得下去** | 可以幫離職者設年度目標 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` | 中 |
| `CASM004p0` 選完來源業務員後 `AddError` 但**沒有 `Show()`**,下一次 `DoValidate` 又 `Clear()` | 這則錯誤永遠不會被看到 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:249-262`、`:65` | 中 |
| `CASB001` 寄信時查無 EMAIL 只跳訊息,繼續下一列 | 使用者以為都寄出去了 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` | 中 |
| `CASM004` 比率欄的訊息寫「應介於0.01和100.00之間」,判斷式只有「等於 0」 | 訊息與行為不符 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328` | 低 |
| `CASM005` 查詢的訊息寫「必須皆(不)填寫」,判斷式是「兩個都空才錯」 | 訊息與行為不符 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:174-175` | 低 |
| `CASR008` 三個報表勾選框全不勾時,按預覽**完全沒有反應也沒有訊息** | 使用者不知道發生什麼事 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:302-303`、`:344-364` | 中 |

### E.3 `catch` 吞例外 / 回傳值語意錯誤

**這一類最危險,因為它讓「檢核」在系統出問題時自動放行。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `GetEmpAgentStartDate` 的 `catch` **回傳 `ex.Message` 當開始日期** | 檢核被當成通過,例外訊息還會被寫進日期欄並傳進 SP | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231` 配 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:98`、`:256-260` | **高(本模組最危險)** |
| `IsDIV_PCTExsits` 出錯回 `-1`,UI 判 `i > 0` | 100% 上限檢核靜默放行 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:295`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:218` | 高 |
| `IsID_NOExsits` 出錯回 `-1`,UI 判 `i > 0` | 金資代碼重複檢核靜默放行 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388` | 高 |
| `GetCustType` / `GetDeptNo` 出錯回空字串,而且取 `Rows[0]` 沒判筆數 | 「代操客戶不可刪」只在一切正常時有效 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:475`、`:480-484`、`:511`、`:516-520` | 高 |
| `GetExcel()` 出錯回 `null`,UI 沒判 null 直接用 | `NullReferenceException` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:558-562`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:472-479` | 中 |
| `CASM002` 三處帶值的 `pxy.GetXXX` 都沒判 null | 同上 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:592`、`:650`、`:681` | 中 |
| 八支報表 PO 的 `catch` 都是 `AddResultRow(false, 0, string.Empty)` | **SP 出錯時使用者拿到空訊息**,連「查無資料」都不是 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:81-84` | 高 |
| 七個 `After*` 的 `throw new ApplicationException("")` 訊息是空字串 | 追不到是哪一步失敗 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` | 中 |
| `CASM004` / `CASM005` 的複製在 `catch` 直接 rollback、`finally` 直接 `Dispose`,都沒判 null | 開交易失敗時真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:121-123`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:129-130`、`:136-137`、`:141-145` | 中 |
| `CASB001` 寫入後把實際影響筆數丟掉硬設成 `1` | 更新 0 筆也算成功 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356` | 高 |

### E.4 同一概念多套實作

| 概念 | 幾套 | 差在哪 | 錨點 |
|---|---|---|---|
| 取員工姓名的 join | 2 | `CASM003` / `CASM006` 用 **INNER**(查不到員工整筆消失),`CASM004` / `CASM005` 用 `LEFT` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:373-374` |
| 取「最新月份的區域別」 | 2 | `CASM002` 用 `MAX(YYMM)` 配 `MIN(...) KEEP DENSE_RANK` **結果是全期間最小值**;`CASI001` 用 `ROW_NUMBER() ... ORDER BY YYMM DESC` 才是真的最新 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:141-144` |
| 「區域別」的資料來源 | 2 | `CASM002` / `CASI001` 來自 `CAS004A`,`CASB001` 來自 `CRM003A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:199` |
| 業務員複製 | 2 | `CASM004` 走 SP 繞過四眼;`CASM005` 走程式逐列進四眼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:97-114` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:92-114` |
| 年度的月分配 | 2 | `CASM003` 固定 12 個月會跨年;`CASM006` 只到當年 12 月 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:142-171` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`、`:233-257` |
| 實際拜訪日期的比較 | 2 | `CASI001` 直接字串比;`CASB001` 用 `to_date(NVL(TRIM(...)))` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147` |
| 離職員工的處理 | 2 | `CASM004` / `CASM005` 在下拉過濾掉(無提示);`CASM006` 跳訊息但不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` |
| `CFM_USER2` 的下拉代碼 | 2 | 彈出視窗用 `440`,grid 用 `470` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.cs:207` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:293` |
| 年度欄位的合理性檢查 | 2 | `CASM003` 有 1900~今年;`CASM006` 沒有 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:323-329` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:420-428` |
| `GetEmpNo` 的筆數檢查 | 2 | `CASI001` 沒檢查直接取 `Rows[0]`;`CASB001` 有檢查 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:469` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:408` |
| `CAS004A` 的分配比率上限判斷 | 2 | `CASM004` 不含戶號;`CASM005` 含戶號。兩支對「同一組合」的定義不同 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:279-282` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:200-205` |

### E.5 寫死常數〔客戶特定〕

換站台**一定要逐條確認**。

| 寫死的東西 | 值 | 錨點 |
|---|---|---|
| 可看全部拜訪紀錄的員工白名單 | 5 個員工代號 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| `CASM006` 的部門白名單 | `G3` `GA` `G11` `G12` `G13` `G14` `Z2` `G17` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` |
| `CASM005` 的銷售機構 | 區別碼 `0` + 機構代碼 `A0901`,而且**唯讀** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81`、`:127-130`、`:142-145` |
| `CASM005` 的員工部門白名單 | `G3` `GA` `G12` `G13` `G17` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:244-246` |
| `CASM005p0` 的員工部門白名單 | 同上**加** `G14` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:198-200` |
| `CASM004` / `CASM005` 的員工過濾字串 | 排除 `G17` + 今年以前離職 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` |
| 代操客戶不可刪的例外部門 | `X01` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447` |
| `CRM003A` 的用途別 | `'3'`(CAS)/ `'1'`(CRM / TMK) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467` |
| `CASB001` 寫進 `CLS002A` 的狀態 | `'301'` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341` |
| `CASR008` 投資地區的 `F` 展開成 `F,G` | `F` → `F,G` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:114` |
| `CASR001` 的「全部員工」定義 | `IS_CASB001 = 'Y'` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:122` |

### E.6 位置取參數

「值不是從資料來的,是從**它在哪裡**推出來的」。改名字、改順序就壞,而且編譯不會報錯。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASR008` 把送給 SP 的代碼從**控件名稱的最後一個字元**切出來 | 改控件名 = 改參數值,沒有任何約定文件 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:110-118` | 高 |
| `CASI001` 取登入者員工代號:把回傳字串用逗號切開**取第 2 段** | 回傳格式一改就拿不到值,而且拿不到時條件整個不加 → 看到全部資料(§5.3) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136` | **高** |
| `CASR008` 的表名靠 `RPT_KIND` 字串拼,`"0"` 拼出 `CASR008` 但計數找 `CASR008_0` | 只選該類時回「查無資料」 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:86`、`:93-95` | 高 |
| `CASM006` 的月分配用 `j < 12` 判斷最後一列,但列數是 `13 - 起算月` | 起算月不是 1 月就一定對不平,而且按幾次都修不好 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`、`:201` | **高** |
| `CASM003` 的跨年月份無條件補一個 `"0"` | 11 / 12 月起算會產生 7 碼年月,超過欄位長度 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151` | 中 |
| `CASB001` 雙擊判斷用 `"IsCheck"`,其餘地方用 `"ISCHECK"` | 目前能動(索引不分大小寫),但不一致 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212` | 低 |

### E.7 SQL 層面的髒寫法

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASI001` 的 8 處起迄條件寫成 `> =`(中間有空白) | **假設**整段 SQL 語法錯、被 `catch` 吞成「執行失敗」;無法本機驗證(§5.3) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219`、`:230`、`:241`、`:251`、`:262`、`:272`、`:283`、`:293` | 高 |
| `CASB001` 的 `UPDATE` 裡 13 個綁定變數寫成 `: NAME`(冒號後有空白),同段的前 5 個卻是正常的 | 同一段 SQL 兩種寫法;ODP.NET 的行為要實測 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:309-323` | 中 |
| `GetUidCode` 的 `AND` / `OR` 缺括號 | **信可能寄給錯的人**(§6.5) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432` | **高** |
| `CASB001` 的「未閱」條件 `<> 'Y' AND <> 'Y'` 碰到 NULL 全被濾掉 | **查不到從沒被主管碰過的拜訪單**(§6.2) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` | **高** |
| 維護與查詢畫面的查詢條件**全部字串串接**,唯二用綁定參數的是 `CASM002` 的報表查詢與 `CASB001` 的批次寫入 | SQL 注入面;報表側反而是乾淨的 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:588`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354` | 高 |
| `CASM002` 的 `MAX(YYMM)` 被算出來卻沒有任何地方用到 | 讓人以為取的是最新一筆 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` | 中 |
| `CASR002` / `CASR006` 的結果集分支都**沒有 `default`** | `CASR002` 會丟例外;`CASR006` 靜默回「查無資料」 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-118`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:74-94` | 高 |
| 八支報表 SP 全部 `CommandTimeout = 0` | 永不逾時,使用者端沒有取消機制 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` | 中 |

### E.8 其他讀碼陷阱

| 陷阱 | 說明 | 錨點 |
|---|---|---|
| `CASM005_PO` 的複製有一行 `row.STATUS = row.STATUS;` | 自我賦值,等於沒做。複製出來的資料**沿用來源的四眼狀態** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96` |
| `CASR006` 的兩段註解寫「既有客戶交易異常表」 | 是別支畫面的文字,實際設的報表名完全不同 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:176`、`:185` |
| `CASB001.cs:279-282` 的三行註解與底下的程式各差一行 | 註解不能信,看控件名 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:279-282` |
| 四支 `_PO` 的介面註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製沒改,與實際功能無關 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:16-18` |
| `App.config` 的 `detailtable` 宣告與 PO 不一致(`CASM001` 被註解、`CASM002` 根本沒宣告) | **以程式為準**(§0.5) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:29`、`:34-40` |
| `CASI001_PO` 在唯讀查詢裡設了一整排四眼欄位的 `DefaultValue` | 從 `CASB001` 樣板複製來的死碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406-418` |
| `CASI001_PO` 的 `GetEmpNo` / `GetUidCode` 是 `public` 但不在介面裡 | Ctl 拿到的是介面型別,**呼叫不到**,是死碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:25-27` |
| `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` | 專案樣板留下的空類別,12 行、零引用 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` |
| `CASR005RPS11` | 交付到正式環境但零引用的孤兒報表 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331` |
| `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs` 裡的 `DSM002A` 全在註解區 | 搜尋字串時會誤判成第三支使用者(§8.4) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-119` |

### E.9 標「假設」的地方一覽

本文所有需要現場確認的推論,集中在這裡:

| § | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| §1.5 | `CASB001` 的執行頻率 | 查詢條件預設值與每次重整都重設為「未閱」 | 問使用者 |
| §4.3 | 進維護頁時框架會把參數換成該筆主鍵 | 主檔與明細共用同一份參數集合,而主檔用區間、明細用等於 | 實測:用區間查多筆,點第二筆看明細對不對 |
| §4.5 | `Filter` 與 `ConditionVDB` 合併後 `G17` 的淨效果是排除 | 兩者形態不同(DataView 過濾 vs SQL 條件) | 實測下拉清單有沒有 `G17` 的人 |
| §4.6 | 參數集合同名重加的行為 | 背後是 typed DataSet 的 `Rows.Find(name)` | 實測:連按兩次查詢換條件 |
| §5.3 | `> =` 會造成 Oracle 語法錯誤 | SQL 標準與 Oracle 詞法規則 | 連 DB 跑一次帶起迄條件的查詢 |
| §6.4 | 框架的 `ExecPOActionToViewVDB` 會補一列成功結果 | 否則寄信功能從來沒運作過,而郵件內容寫得很完整 | 實測:勾一列按執行,看有沒有寄信 |
| §6.4 | ODP.NET 能接受 `: NAME` 這種綁定寫法 | 這功能有在用,而且 13 個參數都有 `AddInParameter` | 同上 |
| §7.3 | `CASR005` 報表種類單選鈕索引 0 的值就是 `"1"` | `.rpt` 中文名與 PO 結果集語意一致 | 開畫面看選項值(本文不讀 `.Designer.cs`) |
| §7.3 | `CASR008` 的 `iRPT_FIRST` 是給 SP 判斷要不要清暫存 | 參數名與 `i == 0` 的條件 | 看 SP 原始碼 |
| §7.6 | `IS_CASB001` 是「代銷組客戶拜訪作業的適用人員」 | 旗標名直接引用 `CASB001` | 問使用者或看員工資料來源 |
| §0.3 | 真正拿分配比率去分帳的程式在版控外的 SP 或別的模組 | 本模組沒有任何一支程式讀分配比率做計算 | 查 SP;問 DBA |
| §3.2 | `CASI001` 主畫面的中文名與彈出視窗同名 | 彈出視窗標題是唯一可見的來源 | 看選單表 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純程式碼閱讀彙整,未執行、未連 DB。畫面中文名待選單表回填;版控外的 10 支 SP 內容未涵蓋。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 135 · 圖 5 · 表格 104 · 程式錨點 637 · § 連結 62 · 引用檢查：畫面 27（缺 0） · Table 20（缺 0） · Report 19（缺 0） · 結果集 16（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
