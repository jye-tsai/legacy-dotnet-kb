<!-- 由 tools/build_copilot_kb.py 從 modules/cod.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS COD 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:COD 是全系統的代碼值域來源,所以本篇的重心不在畫面而在 §2。趕時間只讀三段:§0.2(這模組最反直覺的事)、**§2.4(代碼表與程式常數字典怎麼對應,哪些查表哪些寫死)**、附錄 E(踩雷)。要查某個代碼欄位的值域從哪來,直接翻附錄 C。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、控件 Label 文字與 DB 腳本的欄位註解**推測**。ATLAS 沒有把畫面中文名放進版控 —— COD 的 13 支 Form **沒有任何一支**有 `this.Text`,連彈出視窗都沒有。 ⚠ **〔客戶特定〕**:部門代碼(`G2` / `G3` / `GA` / `OP1`…)、員工代號黑名單、`CODE_SORT = 'C1'`(列管原因)、作廢原因 `01`–`05`、`FEE_CODE = '07'` 等為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`COD009` 被 12 個專案、121 個檔引用,`COD006A` 被 12 個專案、62 個檔引用(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`TA.MappingCode` 看 `architecture.md §7.2`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:COD 管三件互不相干的事 —— 全系統代碼值域的字典、公司員工與其親屬的主檔、以及受益憑證紙張流水號的發放與作廢。**

推測依據逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 表名與欄位中文名 | `COD006A` 的欄位是「代碼種類說明」「可否異動註記」「有效碼」「顯示順序」;`COD007A` 是「級距代碼說明」「客戶異動註記」 | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:109-124`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:47-55` |
| 控件 Label 文字 | 「代碼種類」「代碼說明」「級距上限」「級距下限」「員工代碼」「親屬關係代碼」「流水號起號」「受益憑證號碼」「作廢原因」「選項類別」「選項說明」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:177`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:262-273`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.Designer.cs:358`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.Designer.cs:201`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.Designer.cs:194-208`、`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.Designer.cs:141-170` |
| 程式訊息 | 「此代碼已存在一般代碼資料或級距代碼資料中,不可刪除!」「該員工代碼仍有親屬資料,不可刪除!」「此區間的流水號已被使用或作廢,不可修改」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:190`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:630`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:113` |
| DB 腳本欄位註解 + 共用 PO 用法 | 「通路職務別\CTL014:701」「職位代號\CTL014:702」;全系統的下拉選單與代碼 Searcher 都去讀 `COD006A` 與 `CTL014` | `DB/Table/updateCOD009.sql:15-17`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197` |

「COD」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「代碼檔」描述它,這是從上表推出來的,不是官方名稱。

三條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 代碼字典 | 代碼種類(哪些代碼類別存在)、該類底下的代碼明細、以及用數值區間表示的級距代碼 | `CODM005`、`CODM006`、`CODM007` | `COD005A`、`COD006A`、`COD007A` |
| A' 下拉選單字典 | 另一套**平行**的代碼表,專門餵 UI 下拉選單 | `CTLB014`〔代號屬 CTL,檔案在本專案內〕 | `CTL014` |
| B 員工與親屬 | 員工基本資料、部門、離職日、系統使用者代號、業務歸屬銷售機構;以及員工親屬(優惠關係人的來源) | `CODM009`、`CODB009`、`CODM010`、`CODB901`、`CODB902` | `COD009`、`COD010` |
| C 憑證流水號 | 每檔基金的紙張流水號區間配發、單張憑證的作廢與取消作廢 | `CODM016`、`CODM017` | `COD016`、`COD017` |
| D 其他 | 待辦事項清除、一張只有兩欄的級距設定 | `CODB000`、`CODM036` | `TODO`、`COD040A` |

### 0.2 這模組最反直覺的一件事

**COD 是代碼檔模組,而它自己的程式常數字典是死碼。**

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 定義了 `CODE_SORT` 類別,31 個常數,每個都附中文註解 ——「語言代碼 = 01」「教育程度代碼 = 02」「客訴內容種類代碼 = 12」。這是 repo 內唯一寫下 `COD006A` 代碼種類語意的地方。

**全庫引用次數:0。**

| 類別 | 檔 | 常數數 | 全庫引用(排除 `TA.MappingCode` 自己與 `*.Designer.cs`) |
|---|---|---|---|
| `CODE_SORT` | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10` | 31 | **0 次** |
| `CTL_SRNO_ID` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993` | 3 | **0 次** |
| `EMP_DEPT_TYPE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:141` | 6 | 74 次 / 19 檔 |
| `EMP_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45` | 5 | 4 次 / 2 檔 |
| `VALID_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81` | 3 | 1 次 / 1 檔 |
| `YES_NO` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11` | 2 | 699 次 / 100 檔 |

取而代之的是**字面值**。`CODE_SORT` 的字面值在全庫 `.cs` 的 SQL 與比較式裡出現約 190 處、涵蓋約 40 個不同的值(逐值清單見附錄 C.2)。最諷刺的兩處都在自己家:

- `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372`:`if (row.CODE_SORT != "C1") return;` —— 「列管原因」這個代碼種類寫死在代碼維護畫面的 PO 裡,而 `C1` 不在 `CODE_SORT` 常數清單中。

- `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109`:`[CTL_SRNO_ID] = '2'` / `= '0'` —— 而 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` 正好有 `CTL_SRNO_ID.Destroy = "2"` 與 `CTL_SRNO_ID.UnUsed = "0"`,就在同一個方案裡,沒被用。

**後果**:看到一個代碼欄位想知道值域,`TA.MappingCode` 只在 `CTL014` 那一半可靠(而且只覆蓋 186 / 395,見 §2.4);`COD006A` 那一半必須**連資料庫**或**grep 字面值**。本文附錄 C 把 grep 得到的部分整理出來,但那不是完整值域。

### 0.3 不管什麼

以下**不在** COD 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 系統使用者帳號本身(密碼、權限、EMAIL) | PTPF 平台(`UC0101`) | `CODB902` 只會改 `AA_USER` 的鎖定與密碼欄,且訊息直接寫「必須先到UC0101設定使用者的〔電子郵件信箱〕」;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:99` |
| 部門主檔 | OFD | `OFD002` 一律 `LEFT JOIN` 取 `DEPT_SH_NM`,COD 內無任何寫入;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:469-470` |
| 銷售機構主檔 | OFD | `OFD068A` 只被 join 取名稱;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:155` |
| 基金主檔 | OFD | `OFD081` 只被 join 取 `FUND_SH_NM`;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:410-411` |
| 優惠關係人(員工與親屬的折扣身分) | OFD(`OFD195A`) | COD 只**查**它決定能不能刪,不寫;寫入的程式碼整段被註解掉;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` |
| 憑證的實際列印與送簽 | OFD(`OFD721`) | `CODM017` 只 join `OFD721` 取 `CER_STATUS` 判斷能不能作廢;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:215-218` |
| 列管(交易管制)本身 | OFD(`OFD115A`) | `CODM006` 只查它決定某個代碼能不能改 / 刪;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343` |
| 員工資料的來源系統 | 外部 eHR | `DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 兩張介接表做同樣的加欄。這兩張表**沒有任何 `.cs` 引用**,所以匯入程式不在本 repo。**假設**:員工資料由 eHR 定期匯入,`CODM009` 是人工補正的入口 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 系統管理 / 參數維護人員 | 維護代碼種類與代碼明細、級距代碼、下拉選單內容 | `CODM005` / `CODM006` / `CODM007` 是標準四眼維護畫面;`CTLB014` 是 OneStep 無四眼;`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:101-106` |
| 人事 / 行政 | 建立與維護員工資料、親屬資料 | `CODM009` 有身分證格式檢核、離職日不得小於進公司日等人事規則;`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:306-317` |
| 通路 / 業務管理 | 批次把一批員工掛到某個銷售機構底下 | `CODB009` 先查後勾再一次改;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76-137` |
| IT 支援 | 使用者被鎖時解鎖、補發密碼;清掉卡住的待辦事項 | `CODB902` 與 `CODB000`;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:57-166`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:36-72` |
| 憑證作業人員 / 覆核者 | 配發紙張流水號區間、作廢單張憑證;以及對 `CODM005`–`CODM010`、`CODM016`、`CODM036` 的異動做驗證 / 覆核 / 退回(四眼流程由框架處理,見 `architecture.md §3`) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:92-177` |

**注意:本模組沒有任何一行程式碼在判斷權限。**`CODM009` 那條員工白名單式的邏輯也不存在(那是 CAS 的寫法)。功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。但 `CODB902` 能改任意使用者的密碼,`CTLB014` 能刪掉整個代碼類別 —— 這兩支的權限設定值得單獨確認。

### 0.5 全域開關

repo 內**沒有**任何 COD 專屬的設定檔開關。`Dev/ATLAS.COD/Source/UI/UI.COD/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:47`(`CODM005`)、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:68`(`CODM009`)、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`(`CODM017`) |
| `ugrdResult` 的 `column` / `columnname` 白名單 | 查詢結果 grid 顯示哪些欄位、順序、以及中文抬頭 | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:48`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:55`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:76` |
| `formstyle` | 四支 B 與 `CTLB014` 宣告為 `OneStep`;八支 M 沒有宣告(走預設維護樣式) | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:20-25`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:101-106` |

四件要記住的:

- **`CODM017` 的 `mastertable` 寫的是 `CODM017`,不是 `COD017`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`)。那是 typed DataSet 的表名,不是實體表名。實體表是 `COD017`,只在 PO 的 SQL 字串裡出現。

- **`CODM036` 的 `pkey` 寫 `dataid`,而 xsd 的主鍵是 `MIN_VALUE`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:97` 對 `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:98-101`)。兩邊不一致,以 xsd 為準(框架的樂觀鎖與 EVA 比對走 xsd 的 PK)。

- **`CODM017` 沒有宣告 `ugrdResult`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:87-93`),因為它是 OneStep 樣式的單筆查詢畫面,沒有結果 grid。

- `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:107` 宣告 `.NETFramework,Version=v4.8`;PO 側每一支都留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的逐檔修補痕跡(例:`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:7`),與 CAS 一致。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] COD 模組全景：代碼字典、員工與親屬、憑證流水號三條線，以及全系統讀代碼的三條路徑
圖中文字:① 代碼字典本體：兩套互不相通的代碼表 / CODM005 / 代碼種類 COD005A / CODM006 / 一般代碼 COD006A / CODM007 / 級距代碼 COD007A / CTLB014〔屬 CTL〕 / 下拉選單 CTL014 / ② 員工與親屬：COD009 一批一維護，兩個入口 / CODM009 / 員工主檔維護 COD009 / CODB009 / 批次改銷售機構 COD009 / CODM010 / 員工親屬 COD010 / CODB901 CODB902 / 旗標與帳號解鎖 / ③ 憑證流水號：唯一走 SQL Server 語法的兩支 / CODM016 / 流水號區間 COD016 / CODM017 / 憑證作廢 COD017 / CODM036 / 級距設定 COD040A / CODB000 / 待辦事項清除 TODO / ④ 資料落點（COD009 另有兩張 eHR 介接表，只在 DB 腳本裡） / COD005A COD006A / 代碼種類與明細 / COD007A / 級距代碼 / COD009 COD010 / 員工與親屬 / COD016 COD017 / 憑證流水號 / COD040A / 級距 掃描器漏掉 / ⑤ 全系統怎麼讀它們：三條路，沒有一條經過本模組的 PO / 共用 BasicCOD_PO / 讀 COD005A COD006A COD009 / 共用 BasicCMM_PO / 讀 CTL014 餵所有下拉 / TA.MappingCode / 編譯期常數 不連 DB
```

*圖:圖 1 COD 全景。橘框＝本模組維護入口；橘虛框＝含寫死值或跨模組行為；黑框＝無原始碼或不在本模組的讀取端；灰虛框＝掃描器漏掉的表。三條業務線之間沒有程式呼叫，只靠表相連。*

看圖的四個重點:

1. **三條業務線之間沒有程式呼叫關係。** `CODM005` 不會叫 `CODM009`,`CODM016` 不會叫 `CODM006`。它們只透過表相連,而且連得很少:整個模組內唯一的跨線關聯是 `CODM017` 的「作廢原因」下拉去讀 `COD006A` 的 `CODE_SORT = '17'`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`)。

2. **代碼字典有兩套,而且互不相通。** `COD005A` / `COD006A` 一套(鍵是 `CODE_SORT`),`CTL014` 一套(鍵是 `SourceType`)。兩套的編號**長得很像但不是同一套**:`COD006A` 的 `17` 是作廢原因,`CTL014` 的 `017` 是定期定額註記(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277`)。詳見 §2.3。

3. **本模組的 PO 不是別人讀代碼的入口。** 全系統讀 `COD006A` / `CTL014` 走的是 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs` 兩支共用 PO,完全不經過 `Dev/ATLAS.COD/`。所以「改 COD 的程式」跟「改別人怎麼讀代碼」是兩件事。

4. **`CTLB014` 的代號屬 CTL,檔案卻六層齊全地放在 `Dev/ATLAS.COD/` 底下。** 掃描器把它歸到 CTL 模組(`atlas_scan.py --screen CTLB014`),所以 COD 的母體是 12 支而不是 13 支。但它維護的正是全系統下拉選單的來源表,實務上要跟 COD 一起看(§8.3)。

### 1.2 資料表關係

見 §2 節首的圖。六張實體表加一張掃描器漏掉的 `COD040A`,分成四組:

- **代碼字典三張**(`COD005A` → `COD006A` / `COD007A`):`COD005A` 是種類主檔,另外兩張各自是它的明細,但**不是四眼意義上的主明細** —— 三支畫面各自宣告自己的 `MasterTable`,沒有任何一支宣告 `DetailTable`(§2.1),關聯只存在於 SQL 的 `LEFT JOIN` 與刪除前的存在性檢查。**員工兩張**(`COD009` / `COD010`)也一樣:`COD010` 靠 `EMP_NO` 指回 `COD009`,是兩支獨立的維護畫面。

- **憑證兩張**(`COD016` / `COD017`):唯一真正有寫入關係的一組 —— `CODM016` 存檔時呼叫 SP `s_CODM016` 依區間**產生** `COD017` 的逐筆資料,刪除時把 `COD017` 整批刪掉(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:317-370`)。

- **級距一張**(`COD040A`):`CODM036` 用 `MasterTable.Add(...)` 的多筆寫法宣告,掃描器的正規式只認 `MasterTable = new xTableMapping(...)`,所以這張表**不在母體也不在索引**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36`)。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 本畫面自訂檢核 | 各畫面的 `DoValidate()`,多半**先**於必填檢核 | `ValidateErrList` 訊息清單 |
| 2 需要查 DB 的檢核 | `DoValidate()` 裡直接 `new` 一個 `_Pxy` 打過去 | 訊息清單或對話框 |
| 3 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 4 PO 的 `Before*` | `BeforeSelect` 換 SQL(七支)、`BeforeUpdate` / `BeforeDelete` 擋(只有 `CODM006`) | `args.Cancel = true` + `CancelMsg` |
| 5 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 6 PO 的 `After*` | `CODM009` / `CODM010` / `CODM016` 有掛,但前兩支的內容整段被註解 | `throw` → 整筆回滾 |

**第 1 到第 3 階段全部在用戶端。**伺服器端只重驗兩條:`CODM005` 覆寫 `Delete` 查下層資料(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232`)、`CODM006` 用 `BeforeUpdate` / `BeforeDelete` 查列管(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:336-392`)。其餘六支的卡控只要繞過 UI 就全部失效。

### 1.4 批次資料流

見 §6 節首的圖。三件事:

- **四支 B 全部是使用者按按鈕觸發的 OneStep 畫面**,不是排程。repo 內沒有任何 COD 的 WindowsService 或排程設定(掃描器回報 Service 0)。

- **四支全部繞過四眼引擎直接下 DML**:`CODB000` 刪 `TODO`、`CODB009` 與 `CODB901` 改 `COD009`、`CODB902` 改 `AA_USER`。`CODB009` 的 PO 雖然繼承 `BaseEVADaoPO` 並宣告了 `MasterTable`,但它覆寫的是 `Execute` 而不是 `Update`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76`),所以四眼欄位一個都不會被寫。

- **只有 `CODB902` 有對外副作用**:寄一封含明文亂數密碼的 EMAIL,並把執行歷程寫進一張叫 `CODB902` 的表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:123-149`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,以下是**推測**的作業順序,依據是資料相依:某張表要有資料,後一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期(一次性) | 系統管理 | 先建代碼種類,再建該種類底下的代碼或級距 | `CODM005` → `CODM006` / `CODM007` | `CODM006` 的種類下拉只列**還沒被 `COD007A` 用掉**的種類(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-614`) |
| 建置期 | 系統管理 | 設定各下拉選單的選項與順序 | `CTLB014` | 要先知道 `SourceType` 編號,而編號本身沒有任何維護畫面(§2.4) |
| 平時(人事異動) | 人事 | 新增 / 修改員工,填離職日 | `CODM009` | 部門要先在 `OFD002` 存在 |
| 平時 | 人事 | 維護員工親屬 | `CODM010` | 員工要先在 `COD009` 存在(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:614-630` 的刪除檢核反向證明了這條相依) |
| 通路調整時 | 通路管理 | 一次把多位員工改掛到某銷售機構 | `CODB009` | 機構要先在 `OFD068A` 存在 |
| 需要時 | IT 支援 | 解鎖 / 補發密碼、清待辦 | `CODB902`、`CODB000` | 使用者要先在 `AA_USER` 存在 |
| 憑證印製前 | 憑證作業 | 配發一批紙張流水號給某檔基金 | `CODM016` | 基金要先在 `OFD081` 存在;起號自動接續該基金的最大迄號(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:186-208`) |
| 憑證毀損時 | 憑證作業 | 作廢單張憑證 | `CODM017` | 該號要先由 `CODM016` 產生到 `COD017`,且 `OFD721` 的 `CER_STATUS` 必須是 `2`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:80-88`) |

**假設**:「建置期一次性」這個定位 —— 依據是三支代碼畫面的查詢條件都極簡(只有代碼種類與代碼),沒有日期區間也沒有狀態篩選。實際頻率要問使用者。

## 2. 資料模型

```text
[圖] COD 的四張代碼表與 TA.MappingCode 程式常數的對應關係，以及兩者對不上的地方
圖中文字:① 執行期：值真的存在資料庫，改了立刻生效 / COD005A 代碼種類 / PK CODE_SORT / COD006A 一般代碼 / PK CODE_SORT+CODE / COD007A 級距代碼 / PK CODE_SORT+RANGE / CTL014 下拉選單 / SourceType 分類 / ② 誰維護：四張表四個入口，只有前三張走四眼 / CODM005 四眼 / 刪除前查下層有無資料 / CODM006 四眼 / MOD_FLAG=N 不可改 / CODM007 四眼 / 上限須大於下限 / CTLB014 無四眼 / 整類刪光再寫回 / ③ 編譯期副本：TA.MappingCode 三支檔，跟上面沒有同步機制 / CTL014.cs / 187 類 566 值 對 CTL014 / CODCode CODE_SORT / 31 值 對 COD005A / CODCode EMP_DEPT_TYPE / 6 值 部門所屬 / SysCode SrNo / 流水號代號 / ④ 對不上的地方（本篇最重要的一段，細節見 §2.4） / 程式用 395 個 SourceType / CTL014.cs 只定義 186 個 / CODE_SORT 常數用 0 次 / 全庫都直接寫字面值 / CTL_SRNO_ID 常數 0 次 / CODM017 寫死 0 與 2 / YES_NO 用 699 次 / 唯一被認真用的 / ⑤ 結論：值域來源共五種，讀的人要先知道在讀哪一種 / CTL014 表 / 下拉選單 走 SourceType / COD006A 表 / Searcher 走 CODE_SORT / COD007A 表 / 級距 上下限比大小 / TA.MappingCode / 程式常數 可被寫 / 字面值寫死 / SQL 或 C# 裡
```

*圖:圖 2 代碼表與程式常數字典。橘框＝執行期真值所在的表；黑框＝編譯期常數（無同步機制）；橘虛框＝實測出來對不上的地方。實線＝維護關係；虛線＝照著抄一份，不是程式相依。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`)。COD 十二支畫面的宣告分成四種寫法:

| 畫面 | 宣告方式 | `MasterTable` | `DetailTable` | 錨點 |
|---|---|---|---|---|
| `CODM005` | `xTableMapping` | `COD005A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:52` |
| `CODM006` | `xTableMapping` | `COD006A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:54` |
| `CODM007` | `xTableMapping` | `COD007A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:47` |
| `CODM009` | `xTableMapping` | `COD009` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:39` |
| `CODM010` | `xTableMapping` | `COD010` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:41` |
| `CODB009` | `xTableMapping` | `COD009` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43` |
| `CODM016` | **舊版 `TableMapping`** | `COD016` | **無**(靠 SP 與手寫 SQL 維護 `COD017`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:50` |
| `CODM036` | **`MasterTable.Add(...)`** | `COD040A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36` |
| `CODM017` | **完全沒有宣告** | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:20-40` |
| `CODB000` | 不繼承 EVA 基底 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:24-26` |
| `CODB901` | 空建構子 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:37-40` |
| `CODB902` | 空建構子 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:38-41` |

**全模組沒有任何一支宣告 `DetailTable`。**COD 沒有主明細結構,十二支畫面每一支都是單表(或無表)。

三個掃描器母體看不出來、但會影響維護的點:

- **`CODM017` 沒有主明細,不是漏寫,是它根本不是四眼 PO。** 它繼承的是 `BasicEVAPO` 而不是 `BaseEVADaoPO`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:20`),只實作了自己的 `Set` 與 `Get` 兩支手寫方法(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:47`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:200`),而且**用的是 SQL Server 語法** —— `[COD017]` 方括號識別字、`@` 參數前綴、`GetDate()`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:75-86`)。`App.config` 裡宣告的 `mastertable` 是 typed DataSet 的表名 `CODM017`,不是實體表(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`)。實體表是 `COD017`。

- **`CODM036` 有主檔,只是掃描器認不出來。** 它繼承 `BaseMultiRowEVADaoPO`,`MasterTable` 是集合不是屬性,所以寫成 `this.MasterTable.Add(new xTableMapping("COD040A", "CODM036"));`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36`)。掃描器的正規式只認賦值寫法,於是 `COD040A` 這張表**不在母體、不在索引、也不在 `architecture.md` 附錄 A 的 367 張表裡**。

- **`CODM016` 用的是沒有 `x` 前綴的舊版 `TableMapping`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:50`),搭配舊版 `PrepareSQLEventHandler` 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:47-53`)。整個 COD 只有這一支停在舊世代,連它用的 `TableHelper.AppendToDoString` 也是 SQL Server 版(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:452`);其餘七支 M 都用 `xTableHelper` / `xEVAStringHelper`。這正是 `architecture.md §4.7` 說的「綁到哪一份取決於檔案頂端的 `using`」的實例。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。

| 表 | 主鍵(xsd) | 主鍵(App.config) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `COD005A` | `CODE_SORT` | `CODE_SORT` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM005Model.xsd:100-103` |
| `COD006A` | `CODE_SORT` + `CODE` | `CODE_SORT,CODE` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:130-134` |
| `COD007A` | `CODE_SORT` + `RANGE_CODE` | `CODE_SORT,RANGE_CODE` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:123-127` |
| `COD009`(`CODM009` 版) | `EMP_NO` | `EMP_NO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:197-200` |
| `COD009`(`CODB009` 版) | `EMP_NO` | (B 畫面不宣告) | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd:184-187` |
| `COD010` | `REL_ID_NO` | `REL_ID_NO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM010Model.xsd:160-163` |
| `COD016` | `FUND_ID` + `BNG_CTL_SRNO` | `FUND_ID,BNG_CTL_SRNO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:198-202` |
| `COD017`(在 `CODM016` 的 xsd 內) | `FUND_ID` + `BF_CTL_SRNO` | — | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:203-207` |
| `COD017`(在 `CODM017` 的 xsd 內,表名叫 `CODM017`) | `FUND_ID` + `BF_CTL_SRNO` | `FUND_ID,BF_CTL_SRNO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM017Model.xsd:114-118` |
| `COD040A`(表名叫 `CODM036`) | `MIN_VALUE` | **`dataid`** | **✘** | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:98-101` 對 `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:97` |
| `CTL014` | **沒有宣告主鍵** | (`CTLB014` 不宣告) | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:18-21` |

**`COD010` 的主鍵只有 `REL_ID_NO`(親屬身分證字號),不含 `EMP_NO`。**意思是同一個人不能同時是兩位員工的親屬 —— 這條限制沒有寫在任何地方,是從 xsd 反推的。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 有中文名的欄 | 說明 |
|---|---|---|---|
| `COD009`(`CODB009` 版) | ✔ | **全部 13 欄都有 Caption** | 全模組唯一完整的一份 |
| `COD005A` `COD006A` `COD007A` `COD009`(`CODM009` 版) `COD010` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `COD016` `COD017` | ✔(但**大小寫不同**) | 一個都沒有 | 寫成 `dataid` / `Status` / `CreateID` / `DataFlag`,其餘表全是大寫 |
| `COD040A` | ✔ | 一個都沒有 | 大寫版 |
| `CTL014` | **完全沒有** | — | 四欄而已,沒有 `DATAID`、沒有 `STATUS`、沒有 `DATAFLAG` |

三個後果:(1) **`COD016` / `COD017` 的四眼欄位是混合大小寫**,而且這兩支的 SQL 是 SQL Server 方言用方括號包 —— 改欄位時不能照其他表的大寫習慣寫;(2) **`CTL014` 沒有 `DATAFLAG` 所以沒有樂觀鎖**,兩人同時開 `CTLB014` 改同一類,後存的無聲蓋掉先存的,而且因為寫法是「整類刪光再寫回」(§8.3),先存的那批**整批消失**;(3) **`CTL014` 沒有 `STATUS` 所以沒有四眼**,全系統下拉選單可以被一個人單獨改掉。

`DATAFLAG` 在有它的六張表上型別一律 `xs:base64Binary`,是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 六張表各是什麼代碼、誰在用

這一節是本篇的主要用途:拿到一個代碼欄位,先在這裡對號入座。「誰讀」是全 `Dev` 下 `.cs` 的表名字面比對(排除 `*.Designer.cs`)。

| 表 | 是什麼(一列 = 什麼) | 主要欄位 | 誰維護 | 誰讀(檔數) | 值域寫在哪 |
|---|---|---|---|---|---|
| `COD005A` | 一個代碼種類,例如 `01` 語言代碼、`12` 客訴內容種類代碼 | `CODE_SORT`(2 碼 PK)、`CODE_SORT_DESCRP` + 13 四眼;17 欄 | `CODM005`(四眼) | 4;只有 `CODM006` / `CODM007` 的種類下拉(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:600-666`)與查詢 join(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:251`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:175-176`) | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 的 `CODE_SORT`(31 個,**零引用**);實際值見附錄 C.2 |
| `COD006A`〔共用〕 | 某代碼種類底下的一個代碼值,例如種類 `17`(作廢原因)底下的 `01` | `CODE_SORT` + `CODE`(PK)、`CODE_DESCRP`、`M_CODE`、`MOD_FLAG`、`VALID_CODE`、`SHOW_ORDER` + 13 四眼;23 欄 | `CODM006`(四眼) | **62**、12 個專案;統一入口 `ucCOD006`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:21`)配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257` | **沒有完整清單**;`CODE_SORT` 靠約 190 處字面值 / 40 值(附錄 C.2),`CODE` 只在資料庫 |
| `COD007A` | 一個數值區間級距,例如投資級距的 0–100 萬 | `CODE_SORT` + `RANGE_CODE`(PK)、`RANGE_CODE_DESCRP`、`MIN_VALUE`、`MAX_VALUE`、`MOD_FLAG` + 13 四眼;22 欄 | `CODM007`(四眼) | 4,其中 3 個在 COD 自己家。**沒有任何共用 DataSrc 讀它**;**假設**由版控外的 SP 或報表使用 | 同 `COD006A`,無程式常數 |
| `COD009`〔共用〕 | 一位員工 | `EMP_NO`(PK)、身分證、中英文姓名、部門、進 / 離職日、系統使用者代號、員工類別、是否公單、業務歸屬機構、通路職務別、職位…;xsd 55 欄(掃描器只算 36) | `CODM009`(四眼)、`CODB009` / `CODB901`(繞過四眼) | **121**、12 個專案;`RSPM037` 也把它當 `MasterTable`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`) | 各代碼欄對應 `CTL014` 的 `SourceType`:`EMP_CD` → `002`、`AO_CODE` → `003`、`MANGR_CODE` → `001`、`AGENT_ID` → `062`、`G_JOB_CODE` → `701`、`JOB_CODE` → `702`(附錄 C.1) |
| `COD010` | 一位員工親屬(優惠關係人的來源) | `REL_ID_NO`(PK)、`EMP_NO`、`REL_NAME`、`REL_CODE`、`BIR_DATE`、生效 / 終止 / 停用 / 異動日 + 13 四眼;35 欄 | `CODM010`(四眼) | 8;`CODM009` 刪除員工前會查它(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:614`) | `REL_CODE` 走 `RelCodeDataSrc`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:120-122`),底層是 `COD006A` 的某個 `CODE_SORT` |
| `COD016` | 「某檔基金配發了流水號 M 到 N 這一段」 | `FUND_ID` + `BNG_CTL_SRNO`(PK)、`END_CTL_SRNO`、`FUND_SH_NM`(join)+ 13 四眼(**小寫混合**);19 欄 | `CODM016`(四眼) | 3,全在 COD | 無代碼欄位 |
| `COD017` | 「某檔基金的第 K 號紙張」及其憑證號碼與作廢狀態 | `FUND_ID` + `BF_CTL_SRNO`(PK)、`BF_CER_ISSUE_CODE`、`BF_CER_NO`、`CTL_SRNO_ID`、`CANCEL_CD` + 13 四眼;21 欄 | **沒有四眼入口**:新增靠 `CODM016` 的 `AfterAdd` 呼叫 `s_CODM016`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:119`),刪除靠 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:178` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:348`,狀態改變靠 `CODM017` 直接 UPDATE | 10(COD 4、Common 4、OFD 2) | `CTL_SRNO_ID` → `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007`(`0` 未使用 / `1` 已使用 / `2` 作廢,**程式不用它**);`CANCEL_CD` → `COD006A` 的 `CODE_SORT = '17'`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`) |
| `COD040A` | 一個級距(業務不明) | `MIN_VALUE`、`MAX_VALUE`、`VAL_DESC` + `DATAID` + 13 四眼;18 欄。xsd 表名是 `CODM036`(`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:28-30`) | `CODM036`(四眼多筆版) | 1,只有 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs` | 無代碼欄位 |

每張表的陷阱:

- `COD005A`:一個 `CODE_SORT` **只能二選一** —— 要嘛在 `COD006A` 有明細、要嘛在 `COD007A` 有,不能兩者都有。這條規則實作在下拉的兩段 SQL(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`),不是任何一個檢核。

- `COD006A`:`MOD_FLAG = 'N'` 會鎖住 `CODM006` 的修改與刪除鈕(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83`),但**這個旗標是使用者自己填的**,新增時一律寫 `Y`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`)。

- `COD007A`:唯一的區間檢核是「上限須大於下限」(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185`)。**級距重疊或留空完全沒有檢核。**

- `COD009`:沒有 eHR 以外的權威來源。`DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 做同樣加欄,但兩表在 `.cs` 零引用 —— 匯入程式不在本 repo。

- `COD010`:xsd 有 `AFT_EMP_NO` / `AFT_EMP_CD` / `BEF_REL_NAME` / `BEF_EFFECTIVE_DATE` / `BEF_TERMINATE_DATE` 五個「異動前後」欄,UI 確實在填(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:287-291`),但 PO 端**沒有任何程式讀它們**。

- `COD017`:資料由**不在版控**的 SP `s_CODM016` 產生。要知道區間怎麼展開、`BF_CER_NO` 怎麼給,只能去資料庫看。

- `COD040A`:查詢用的主檔 SQL 寫死 `WHERE ROWNUM < 3`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52`),維護用的明細 SQL 卻是全表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:66-72`)。同一張表兩種取法,查詢頁最多只看得到 2 列。

### 2.4 代碼表與 `TA.MappingCode` 的對應:哪些查表、哪些寫死

見本節首的圖。**這是本篇最有價值的一段。**

#### 2.4.1 四個層次,先分清楚

| 層次 | 東西 | 執行期會不會變 | 錨點 |
|---|---|---|---|
| L1 執行期真值 | `COD005A` / `COD006A` / `COD007A` / `CTL014` 四張表的內容 | **會**,改完立刻生效 | — |
| L2 讀取入口 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs`(讀 COD 三張)、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197`(讀 `CTL014`) | 不會,但換 SQL 就換值域 | — |
| L3 編譯期副本 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs`(187 類 / 566 值)、`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs`(2 類 / 37 值) | **不會**,改了要重編 | `architecture.md §7.2` |
| L4 字面值 | 散在 SQL 字串與 C# 比較式裡的 `'C1'` / `'17'` / `'2'` | 不會,而且找不到 | — |

**L1 與 L3 之間沒有任何同步機制。**沒有產生器、沒有檢查、沒有測試。`CTL014.cs` 是某個時點手抄一份的結果。

#### 2.4.2 `CTL014` 這一半:覆蓋率 47%

`CTL014` 表的結構是 `SourceType` / `TextValue` / `DisplayName` / `DisplayOrder` / `Description` / `IsDefault`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:150-156`)。`SourceType` 就是「這是哪一類代碼」的三碼編號。

`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的每個類別註解都帶著這個編號,例如「員工類別[002]」(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:44-45`)、「銷售機構區別碼[062]」(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050`)。

實測(掃全 `Dev` 下的 `.cs`,排除 `obj` / `bin`):

| 量 | 數字 | 怎麼算的 |
|---|---|---|
| `CTL014.cs` 帶編號的類別 | **186** | 註解裡出現 `[nnn]` 的 `public static class` |
| 程式實際用到的 `SourceType` | **395** | `new GetDropDownDataSrc("nnn")` 加上 250 個專屬 DataSrc 類別的 `m_sourcetype` 欄位 |
| 用到但 `CTL014.cs` **沒有**對應類別 | **224** | 例如 `063` / `163` / `295` / `404` / `450` / `701` / `702` |
| 有類別但沒有任何地方直接用 | **15** | `022` `032` `033` `034` `086` `112` `120` `121` `122` `123` `132` `135` `136` `147` `247` |

**結論:`CTL014.cs` 只覆蓋了實際在用的 `SourceType` 的 47%。**一個代碼欄位如果在 `CTL014.cs` 裡查得到,那份中文說明可信;查不到(超過一半的情況)就只能去資料庫看 `CTL014` 的 `Description` 欄。

兩個具體例子,都在 `CODM009`:

- `G_JOB_CODE`(通路職務別)走 `new GetDropDownDataSrc("701")`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587`)。`701` 在 `CTL014.cs` 裡沒有類別。值域唯一的線索是 DB 腳本的欄位註解:「1:部門主管;2:組主管/業務員;3:業務助理」(`DB/Table/updateCOD009.sql:15`)。

- `JOB_CODE`(職位代號)走共用控件 `ucCTL014`。該控件**在 repo 內沒有原始碼**(只有 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1900` 的欄位宣告,無原始碼,從呼叫端反推),`702` 在 `CTL014.cs` 裡也沒有類別,值域只寫在 DB 註解「職位代號\CTL014:702」(`DB/Table/updateCOD009.sql:17`)。

#### 2.4.3 `COD005A` / `COD006A` 這一半:覆蓋率 0%

| 量 | 數字 |
|---|---|
| `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10` 的 `CODE_SORT` 常數 | 31 |
| 全庫引用這些常數的次數 | **0** |
| 全庫 `.cs` 內 `CODE_SORT` 的字面值比較 / SQL 條件 | 約 190 處 |
| 涵蓋的相異 `CODE_SORT` 值 | 約 40 個 |
| 其中**在** `CODCode.cs` 裡查得到的 | 10 個(`11` `12` `13` `15` `19` `20` `23` `84` `89` `99`) |
| 其中**查不到**的 | 約 30 個(`00` `17` `1B` `1C` `36` `42` `45` `50` `51` `A7` `A8` `C1` `C5` `C6` `C7` `D2` `E2` `E3` `E4` `E7` `E8` `E9` `HO` `P1` `P3` `P5` `P7` `PC` `PD` `Q2`) |

逐處清單見附錄 C.2。

#### 2.4.4 兩套編號長得一樣但不是同一套

這是最容易踩的坑:

| 編號 | 在 `COD006A`(`CODE_SORT`) | 在 `CTL014`(`SourceType`) |
|---|---|---|
| `17` / `017` | 作廢原因(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`) | 定期定額註記 `RSP_ID`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277`) |
| `02` / `002` | 教育程度代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:19`) | 員工類別 `EMP_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45`) |
| `03` / `003` | 職業別代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:23`) | 業務員區分碼 `SALES_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:67`) |
| `04` / `004` | 職稱代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:27`) | 部門 / 通路 / 銷售機構有效碼 `VALID_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81`) |

**判斷方法**:看控件型別。`ucCOD006` 系列的 Searcher → `COD006A` 的 `CODE_SORT`;`UltraCombo` 配 `xxxDataSrc` 或 `GetDropDownDataSrc` → `CTL014` 的 `SourceType`;`ucCOD005ForCODM006` → `COD005A`。三者在 `CODM009` 同一個畫面上並存(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1891-1900`)。

#### 2.4.5 「哪些查表、哪些寫死」一句話總表

| 代碼欄位的取值方式 | 查表還是寫死 | 典型例子 | 錨點 |
|---|---|---|---|
| UI 下拉(`UltraCombo` + `xxxDataSrc`) | **查表**(`CTL014`) | `CODM009` 的員工類別、業務員區分碼 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:571-588` |
| UI Searcher(`ucCOD006`) | **查表**(`COD006A`) | `CODM009` 的職稱、`CODM017` 的作廢原因 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:89-140` |
| UI 預設值 | **寫死** | `AO_CODE = "N"`、`MANGR_CODE = "0"`、`EMP_CD = "1"`、`FEE_CODE = "07"`、`EMP_QUOTA_CODE = "0"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:89-92`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:232-237` |
| UI 分支條件 | **寫死** | `if (row.MOD_FLAG == "N")`、`ucomEMP_CD.Value == "1"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357` |
| UI 過濾字串 | **寫死,而且是 SQL 片段** | `custCANCEL_CD_0.Filter = "CODE NOT IN ('01','02','03','04','05')"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38` |
| PO 分支條件 | **寫死** | `if (row.CODE_SORT != "C1") return;` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` |
| PO 寫入值 | **寫死** | `[CTL_SRNO_ID] = '2'` / `= '0'` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109` |
| PO 查詢條件 | **寫死** | `AND CTL_SRNO_ID='1'`、`AND CTL_SRNO_ID<>'0'` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672` |
| 共用 PO 的代碼種類 | **寫死** | `WHERE CODE_SORT= '17'` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| 共用 PO 的部門白名單 | **寫死**〔客戶特定〕 | `DEPT_NO IN('G2','G11','G15','GC')` 等四組 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:378`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:392`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:401`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:408` |
| 程式常數 | **有寫但幾乎沒人用** | `YES_NO` 699 次是例外;`CODE_SORT` / `CTL_SRNO_ID` 都是 0 次 | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10`、`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993` |

**一句話:UI 下拉與 Searcher 查表;其餘全部寫死。**

### 2.5 欄位中文名總表(來自 xsd `msdata:Caption`)

中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**;xsd 沒填的改用控件 Label 或 DB 註解,並在「來源」欄註明。四眼 13 欄與 `DATAID` / `DATAFLAG` 不重複列(全模組只有 `CODB009Model.xsd` 那一份有中文名)。

| 表 | 欄位 | 中文名 | 型別 | 來源 |
|---|---|---|---|---|
| `COD005A` | `CODE_SORT` | 代碼種類 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:177` |
| `COD005A` | `CODE_SORT_DESCRP` | 代碼種類說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:197` |
| `COD006A` | `CODE_SORT` / `CODE` / `CODE_DESCRP` | 代碼種類 / 代碼 / 代碼說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:222`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:253`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:233` |
| `COD006A` | `MOD_FLAG` | **可否異動註記** | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:116` |
| `COD006A` | `VALID_CODE` / `SHOW_ORDER` | 有效碼 / 顯示順序 | string / int | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:123-124` |
| `COD006A` | `M_CODE` | (無) | string | —— |
| `COD007A` | `CODE_SORT` / `RANGE_CODE` / `RANGE_CODE_DESCRP` | 代碼種類 / 級距代碼 / 級距代碼說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:211-242` |
| `COD007A` | `MIN_VALUE` / `MAX_VALUE` | 級距下限 / 級距上限 | decimal | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:262-273` |
| `COD007A` | `MOD_FLAG` | **客戶異動註記** | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:55` |
| `COD009` | `EMP_NO` / `EMP_ID_NO` | 員工代碼 / 員工身分證字號 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:25`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:32` |
| `COD009` | `EMP_NAME` / `EMP_NAME_ENG` | 員工中文姓名 / 員工英文姓名 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:39-46` |
| `COD009` | `DEPT_NO` / `DEPT_SH_NM` | 部門代碼 / 部門中文簡稱(join) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:53`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:150` |
| `COD009` | `AO_CODE` / `AO_DATE` | 業務員區分碼 / 業務到職日 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:60` |
| `COD009` | `ENTRY_DATE` / `LEAVE_DATE` | 進公司日期 / 離職日期(`yyyyMMdd`) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:67-68` |
| `COD009` | `UID_CODE` / `MANGR_CODE` / `DAM_CODE` | 系統使用者代號 / 基金經理人 / 全委經理人別 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:69`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:76` |
| `COD009` | `EMP_CD` / `EMP_MEMO` / `POSI_CODE` / `EMP_EMAIL` / `TEST_YN` | 員工類別 / 備註說明 / 職稱 / EMAIL / 試用期滿 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:83`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:90` |
| `COD009` | `IS_COMP_FEAT` / `IS_UPDATE_OFD195` / `BEF_EMP_CD` / `BEF_IS_COMP_FEAT` | 是否為公單 / 修改時是否更新優惠關系人資料 / 更改前員工類別 / 更改前是否為公單 | string / boolean | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:160-161` |
| `COD009` | `TO_EMP_NO` / `AGENT_ID` / `AGENT_CODE` | 通知對象員工代碼 / 業務歸屬銷售機構區分碼 / 業務歸屬銷售機構 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:185-187` |
| `COD009` | `G_JOB_CODE` / `PROBATIONENDDATE` / `JOB_CODE` | 通路職務別 / 試用期滿日 / 職位代號 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:189-191` |
| `COD009` | `SALE_DEPT_NO` `UPD_DATE` `UPD_TIME` `UPD_USER` `EMP_QUOTA1`–`3` `FEE_CODE` `EMP_QUOTA_CODE` `OUTBOUND` `ADD195` | **全部沒有中文名** | —— | —— |
| `COD010` | `EMP_NAME` / `EMP_ID_NO` / `EFFECTIVE_DATE` / `TERMINATE_DATE` | 員工姓名 / 員工ID / 生效日期 / 終止日期 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM010Model.xsd:110-146` |
| `COD010` | `REL_ID_NO` / `REL_NAME` / `REL_CODE` / `BIR_DATE` | 身分證字號 / 姓名 / 親屬關係代碼 / 出生日期 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.Designer.cs:301-358` |
| `COD016` | `FUND_SH_NM` | 基金簡稱(join) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:93` |
| `COD016` | `FUND_ID` / `BNG_CTL_SRNO` / `END_CTL_SRNO` | 基金代碼 / 流水號起號 / 流水號迄號 | string / decimal | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.Designer.cs:189-213` |
| `COD017` | `BF_CTL_SRNO` / `BF_CER_NO` / `CANCEL_CD` / `CTL_SRNO_ID` | 紙張流水號 / 受益憑證號碼 / 作廢原因 / 流水號識別碼 | decimal / string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.Designer.cs:183-377`(**xsd 一個 Caption 都沒有**) |
| `COD040A` | `MIN_VALUE` / `MAX_VALUE` / `VAL_DESC` | 級距下限(Caption 開頭多一個空白)/ 級距上限 / 級距說明 | decimal / string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:28-30` |
| `CTL014` | `TEXTVALUE` / `DISPLAYNAME` | 代碼 / 下拉式選單 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:18-19` |
| `CTL014` | `DISPLAYORDER` | 顯示順序 | Model `string` / **View `int`** | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:20` 對 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:20` |
| `CTL014` | `ISDEFAULT` | Model「是否預設值」/ **View「是否預設值0:是;1:否」** | Model `string` / View `int` | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:21` 對 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:21` |

四件要記住的:

1. **`MOD_FLAG` 在兩張表的中文名不一樣**(`COD006A`「可否異動註記」/ `COD007A`「客戶異動註記」),而程式的用法完全相同(都是 `== "N"` 就鎖住畫面) —— 至少有一邊的 Caption 是錯的。

2. **`CTL014` 的 Model 與 View 不同構**,兩欄 string 對 int;View 的 Caption 還說 `0` 是、`1` 否,與欄位名 `ISDEFAULT` 的直覺相反。UI 的檢核 `row.ISDEFAULT != 1 && row.ISDEFAULT != 0` 兩個值都收(`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs:125-129`)。

3. **`CTLB014Model.xsd` 內缺了 `SOURCETYPE` / `DESCRIPTION` / `USERID` 三欄**,而 PO 的 `INSERT` 確實會寫它們(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`) —— 這三個值從 `Utility.Parameters` 來,不從 DataSet 來。

4. `COD009` 的 `UPD_DATE` / `UPD_TIME` / `UPD_USER` 與四眼的 `UPDATEDATE` / `UPDATEID` **並存且語意重疊**,`CODM009` 新增時一律填空字串(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:233-235`),修改時完全不碰。

### 2.6 與其他模組共用的表

掃描器回報「無跨模組共用表」,因為它只看 `MasterTable` / `DetailTable` 的宣告。**實際上 COD 的表是全庫被讀最多的一組**(詳細影響面見 §8):

| 表 | 本模組外的引用檔數 | 最大宗的讀取端 |
|---|---|---|
| `COD009` | 113 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536`(共用員工查詢)、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`(RSP 當主檔用) |
| `COD006A` | 59 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs`(共用 Searcher) |
| `COD017` | 6 | Common 4、OFD 2 |
| `COD010` | 4 | RSP / OFD / EC.Query 各 1、Common 1 |
| `COD005A` | 1 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:104-158` |
| `COD007A` | 1 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`(只用來排除,不取值) |
| `COD016` / `COD040A` | 0 | 只有本模組 |

反過來,COD **借用**別人的是唯讀 join 六張(`OFD002` 部門、`OFD068A` 銷售機構、`OFD081` 基金、`OFD115A` 列管、`OFD195A` 優惠關係人、`OFD721` 憑證),外加會被寫入的平台庫兩張 `AA_USER` 與 `TODO`(§8.5)。

### 2.7 狀態碼(從程式反推,標來源)

| 欄位 | 在哪張表 | 值域 | 來源 |
|---|---|---|---|
| `STATUS` / `Status` | 六張有四眼的表 | 12 個 `EVAStatusCode` 常數,實際字面值查不到 | 見 `architecture.md §3.10`,本模組沒有任何程式直接比對 `STATUS` |
| `CTL_SRNO_ID` | `COD016` / `COD017` | `0` 未使用 / `1` 已使用 / `2` 作廢 | 類別定義在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007`;程式端全部寫死字面值(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:107`) |
| `CER_STATUS` | `OFD721`(join 來的) | 只知道 `2` 代表「還沒送簽、可以作廢」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:82-84`;其餘值域不在本模組 |
| `MOD_FLAG` | `COD006A` / `COD007A` | `Y` / `N`;`N` 代表畫面鎖定 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110`;新增一律給 `Y`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174`) |
| `VALID_CODE` | `COD006A` | 走 `CTL014` 的 `SourceType = 004` | `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17`;新增預設 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:38`) |
| `IS_COMP_FEAT` | `COD009` | `Y` 公單 / `N` 非公單;非公單時身分證字號變必填 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:467-477` |
| `LEAVE_DATE` | `COD009` | 「在職」有**三種**判斷法,見附錄 E.3 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695` |
| `ISDEFAULT` | `CTL014` | `0` / `1`,語意依 Caption 是「0:是;1:否」 | `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:21` |

## 3. 畫面清冊

掃描器母體:畫面 12(B 4 / I 0 / M 8 / R 0)· 表 6 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 0 · Service 0。另有一支代號屬 CTL 但檔案在本專案內的 `CTLB014`(§8.3)。

### 3.1 維護 M(8 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `CODM005` | 代碼種類維護(推測) | 齊 | `COD005A` | 無 | 無 | 無 |
| `CODM006` | 一般代碼維護(推測) | 齊 | `COD006A` | 無 | 無 | 無 |
| `CODM007` | 級距代碼維護(推測) | 齊 | `COD007A` | 無 | 無 | 無 |
| `CODM009` | 員工資料維護(推測) | 齊 | `COD009` | 無 | 無 | 無 |
| `CODM010` | 員工親屬維護(推測) | 齊 | `COD010` | 無 | 無 | 無 |
| `CODM016` | 憑證流水號區間維護(推測) | 齊 | `COD016` | 無(另寫 `COD017`) | `s_CODM016`(不在版控) | 無 |
| `CODM017` | 憑證作廢 / 取消作廢(推測) | 齊 | **未宣告**(實體表 `COD017`) | 無 | 無 | 無 |
| `CODM036` | 級距設定(推測,業務不明) | 齊 | `COD040A`(掃描器漏) | 無 | 無 | 無 |

### 3.2 查詢 I

**本模組無 I 畫面。**原因見 §5。

### 3.3 批次 B(4 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 寫哪張表 | 觸發 |
|---|---|---|---|---|---|
| `CODB000` | 待辦事項清除(推測) | **缺 model / view 的 xsd**(有手寫 `.cs`,§3.5) | 無宣告 | `TODO` | 使用者按執行 |
| `CODB009` | 員工銷售機構批次回填(推測) | 齊 | `COD009` | `COD009` | 使用者按執行 |
| `CODB901` | 員工旗標維護(推測) | **缺 model / view**(借 `CODB009` 的) | 無宣告 | `COD009` | 使用者按執行 |
| `CODB902` | 使用者帳號解鎖 / 補發密碼(推測) | **缺 model / view**(借 `CODB009` 的) | 無宣告 | `AA_USER` + `CODB902` | 使用者按執行 |

### 3.4 報表 R

**本模組無 R 畫面、無 `.rpt` 檔。**原因見 §7。

### 3.5 「六層不齊」的三支到底缺不缺

`architecture.md 附錄 D.4` 把「六層不齊」拆成假警報與真缺。COD 的三支兩種情況都有:

| 代號 | 掃描器說 | 實情 | 錨點 |
|---|---|---|---|
| `CODB000` | 缺 model / view | **假警報。**Model 與 View 存在,只是手寫成 `.cs` 而不是由 xsd 產生:`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB000Model.cs` 與 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CODB000View.cs`。掃描器以「代號 + `Model.xsd`」字面比對,所以判缺 | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB000_Ctl.cs:41-56`(確實在用 `CODB000ModelVDB` / `CODB000ViewVDB`) |
| `CODB901` | 缺 model / view | **真缺,而且是故意的。**Ctl 明白寫著 `base.ViewVDBType = typeof(CODB009ViewVDB);//借codb009的view來用`,Model 端直接用泛用的 `BasicModelVDB` | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB901_Ctl.cs:37-42` |
| `CODB902` | 缺 model / view | 同上 | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB902_Ctl.cs:37-42` |

**借 view 的後果**:`CODB901` / `CODB902` 的 UI 建的是 `new CODB009ViewVDB()`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:36`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:37`),但兩支畫面根本不用它的 `COD009` 資料表 —— 所有輸入都塞在 `Util.Parameters` 裡。所以**改 `CODB009` 的 xsd 會連帶重編這兩支**,即使它們一個欄位都沒用到。

`Dev/ATLAS.COD/Source/Control/Control.COD/CODB901_Ctl.cs:54-63` 的 `CustomTransferOracleModelToView` 也因此是空的:宣告了 `view` 與 `model` 兩個區域變數,一個欄位都沒搬,只 `AcceptChanges()` 就 return。

### 3.6 一眼看出差別的五件事

| 差別 | 哪幾支 |
|---|---|
| PO 基底(錯誤回報風格 / 交易邊界 / 事件簽名三者都不同,`architecture.md §3.1`) | `BaseEVADaoPO` 六支(`CODM005` `CODM006` `CODM007` `CODM009` `CODM010` `CODB009`)、`BasicEVAPO` 兩支(`CODM016` `CODM017`)、`BaseMultiRowEVADaoPO` 一支(`CODM036`)、不繼承兩支(`CODB000` `CTLB014`) |
| SQL 方言(複製貼上會直接炸) | `CODM016` / `CODM017` 是 SQL Server(`[]` `@` `GetDate()` `dbo.`);其餘是 Oracle(`:` `sysdate` `ROWNUM`) |
| 有沒有 `BeforeSelect` | 七支有;`CODM005` **沒有**,查詢 SQL 由框架自動產生,結果只有 `COD005A` 自己的欄位 |
| 四眼完不完整 | `CODM005`–`CODM010` 完整;`CODM016` 靠 `After*` 補;`CODM017` 完全沒有;四支 B 全部繞過 —— 「有沒有被覆核過」在 `COD017` 與 `CTL014` 上沒有意義 |
| 卡控在哪一層 | `CODM005` / `CODM006` 有伺服端卡控;其餘六支 M 的卡控 100% 在用戶端,繞過 UI 就全部失效 |

## 4. 維護畫面(M)— 一支一節

```text
[圖] COD 八支維護畫面從按鈕到四眼引擎的卡控順序，以及各畫面掛了哪些事件
圖中文字:① 用戶端：八支 M 的卡控幾乎全在這一層 / Before*ButtonClicked / Add/Modify/Delete/Search / DoValidate() / 各畫面自寫 / validatorManager1 / 必填格式 框架決定 / Pxy 直呼 DB 檢核 / Check chkExists CHECK / ② 五種卡控結果在本模組的分佈（見各節卡控總表） / 阻擋 / e.Cancel 或 args.Cancel / 詢問 / Warn02 按取消才擋 / 警示不擋 / 顯示訊息但不 Cancel / 過濾無提示 / ROWNUM 與參數分支 / 記錄不擋 / CODB902 寫執行歷程 / ③ 伺服端 PO 事件：八支裡只有四支真的擋得住 / BeforeSelect 換 SQL / M005 以外的七支 / BeforeUpdate 擋修改 / CODM006 列管原因 / BeforeDelete 擋刪除 / CODM006 列管原因 / Delete 覆寫 / CODM005 查有無下層 / ④ After*：掛了但整段被註解的，比真的有動作的多 / CODM009 AfterUpdate / 只清 LEAVE_DATE / CODM009 AfterAdd Delete / 整段被註解 空殼 / CODM010 四個 After / 整段被註解 空殼 / CODM016 三個 After / 呼叫 SP 並刪 COD017 / ⑤ 三支不走一般四眼：兩支手寫 SQL、一支多筆版 / CODM017 BasicEVAPO / 無 MasterTable 手寫 SQL / CODM036 多筆版 / BaseMultiRowEVADaoPO / CODM016 舊世代 / TableMapping 非 x 版
```

*圖:圖 3 卡控與四眼順序。橘框＝本模組寫的程式碼；黑框＝框架（無原始碼，從呼叫端反推）；橘虛框＝寫死值、空殼或會咬人的行為。任一層 Cancel 或 throw，後面全部不執行。*

本節每一支的格式相同:用途 → 畫面結構 → 存檔前檢核 → PO 事件 → 跨表更新 → 卡控總表。卡控結果一律五類:**阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋**。

### 4.1 `CODM005` — 代碼種類維護

**用途(推測)**:維護「有哪些代碼類別」。`COD005A` 一列一個 `CODE_SORT`。

**畫面結構**:`xMaintainForm`,兩個 Tab(查詢 / 明細)。查詢條件只有一個:代碼種類 `LIKE`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:47-52`)。明細頁只有代碼種類與代碼種類說明兩個欄位,新增時代碼種類可輸入、修改時鎖定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:79`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:89`)。兩個輸入框都套 `AsciiOnlyUtility` 限制只能打半形(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:29-30`)。

**存檔前檢核**:新增與修改都只呼叫 `DoValidate()`,而 `DoValidate()` 裡只有框架的必填檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:110-114`)。**沒有任何自訂規則。**

**刪除前檢核 —— 一個活的、一個死的**:

- **死的(UI)**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:116-134` 建了一個 `view2`、塞好參數,然後**呼叫 Proxy 那一行是被註解掉的**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:123`)。接著判斷 `view2.Util.Result.Rows.Count > 0` —— 一個從沒被填過的結果集,永遠是 0,所以底下的錯誤訊息**永遠不會出現**。Proxy 端的 `CheckCodeSort` 方法本身也整支被註解(`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM005_Pxy.cs:134`)。

- **活的(PO)**:同一條規則在伺服端用**覆寫 `Delete`** 的方式實作 —— `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232` 先呼叫 `CHECK_CODE_SORT`,查 `COD007A` 與 `COD006A` 的 `UNION` 有沒有這個 `CODE_SORT`,有就把 `Result` 換成失敗並**直接 return,不進 `base.Delete`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:167-205`)。

也就是說這條卡控**確實擋得住**,只是擋在伺服端、UI 那段是殘骸。兩段訊息文字還不一樣(UI 版多了代碼種類的值)。

**PO 事件**:一個都沒掛。`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:46-54` 的建構子只設 `MasterTable`。因此**查詢 SQL 由框架產生**,`CODM005` 是全模組唯一沒有 `BeforeSelect` 的 M 畫面。

**Control 層**:`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:48-94` 是四支基本動作,`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:100-157` 是六支 EVA 動作(取待辦 / 驗證 / 覆核 / 反刪除 / 退回 / 重送)。`CustomTransferSQLModelToView` 照例是 `NotImplementedException`(`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:179-187`)。

**跨表更新**:無。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填與格式 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:110-114` |
| 刪除前(UI) | 該代碼種類是否已被 `COD006A` / `COD007A` 使用 | **永遠不成立**(Proxy 呼叫被註解) | 阻擋(實際失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:118-128` |
| 刪除(PO) | 同上,`SELECT count(*)` 兩表 `UNION` | 回傳失敗訊息,不執行刪除 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232` |
| 刪除(PO)例外時 | `CHECK_CODE_SORT` 的 `catch` 只呼叫 `HandleBusinessException`,`strResult` 維持空字串 | 檢核**視為通過**,照常刪除 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:195-198` |

**要注意的**:`CHECK_CODE_SORT` 的 SQL 用字串串接 `strCODE_SORT`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:183`),值來自 DataSet 而非直接的使用者輸入,但路徑上沒有任何跳脫。整支 PO 1,188 行裡**只有約 40 行是活的**,其餘全是被註解的舊實作(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:233-1064` 是一整個 `#region 註解`)。

### 4.2 `CODM006` — 一般代碼維護

**用途(推測)**:維護某個代碼種類底下的代碼值與中文說明。`COD006A` 一列一個 `CODE_SORT` + `CODE`。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件:代碼種類(Searcher,`=`)與代碼(`LIKE`)(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:92-102`)。明細頁欄位:代碼種類、代碼、代碼說明、有效碼(下拉)、顯示順序(數值,預設 1)。

**三個下拉 / Searcher 的來源**:

| 控件 | 來源 | 錨點 |
|---|---|---|
| 代碼種類 `custCODE_SORT` | `ucCOD005ForCODM006`,帶 `ProgramID = "CODM006"`,底層 SQL 是「`COD005A` 裡**還沒被 `COD007A` 用掉**的種類」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:58-59` 配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-637` |
| 有效碼 `ucomVALID_CODE` | `ValidCodeChDataSrc` → `CTL014` 的 `SourceType = 004` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:68` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17` |
| 結果 grid 的 `MOD_FLAG` | `YesNoDataSrc` → `CTL014` 的 `SourceType = 000` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:62` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/YesNoDataSrc.cs:18` |

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:182-223`)** 共三段,順序固定:

1. **只在新增模式**:呼叫 `Check`,查這個代碼種類是不是已經出現在 `COD007A`(級距代碼)裡。是就加錯誤訊息「此'代碼種類',已存在COD007A中,請重新選擇!」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:75-129`)。

2. **新增與修改都做**:`chkExistsOrder` —— 同一種類下有沒有別的代碼用了相同的顯示順序。有就跳 `Warn02` 對話框「此'代碼種類-顯示順序',已存在!確定存入?」,**按取消才擋**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:138-178`)。

3. **同上**:`chkExistsDES` —— 同一種類下有沒有別的代碼用了相同的中文說明。同樣是詢問式(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:187-227`)。

第 2、3 段的 SQL 是**參數化**的(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:153-156`),第 1 段是**字串串接**的(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:99`)。同一支 PO 內兩種安全等級並存。

**`MOD_FLAG` 的鎖定行為**:進修改模式前先看 `MOD_FLAG`,是 `"N"` 就把修改鈕與刪除鈕關掉、代碼說明設唯讀(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:74-90`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:104-134`)。新增時一律寫 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`),所以「不可異動」這件事只能靠直接改資料庫來設定。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:43-48`)**:六個掛點,其中兩個是本模組僅有的伺服端業務卡控。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | 換成自己的 SQL(`COD006A` `LEFT JOIN` `COD005A` 取種類說明) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:394-432` |
| `BeforeUpdate` | **只對 `CODE_SORT = "C1"` 生效**:若這個代碼已被 `OFD115A` 當成列管原因用過,則只允許改中文說明;其他欄位有變就 `args.Cancel = true`,訊息「已作為列管原因,僅可修改列管原因中文說明」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:336-366` |
| `BeforeDelete` / `BeforeApproveDelete` | 同上條件,已被列管用過就完全不准刪,訊息「已作為列管原因,不可刪除」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:368-392` |

**`"C1"` 是寫死的**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372`),而且不在 `CODCode.cs` 的 `CODE_SORT` 清單裡。〔客戶特定〕

`BeforeUpdate` 的實作值得看仔細:它先查 `OFD115A` 有沒有用這個代碼,**沒有就直接 return 放行**;有的話再查 `COD006A` 裡「種類 + 代碼 + 顯示順序 + 有效碼」四個值是否與畫面送來的完全相同,相同才放行。也就是「只准改中文說明」是靠「其他四欄都沒變」反推出來的。兩段 SQL 都是 `string.Format` 串接(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:351-353`)。

**跨表更新**:無(只讀 `OFD115A` 與 `COD005A`、`COD007A`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 代碼種類已存在於 `COD007A` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:109-113` |
| 新增 / 修改前 | 同種類下顯示順序重複 | `Warn02` 對話框 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:208-211` |
| 新增 / 修改前 | 同種類下代碼說明重複 | `Warn02` 對話框 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:218-221` |
| 進入修改模式 | `MOD_FLAG = "N"` | 修改鈕 / 刪除鈕變灰 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83` |
| 伺服端修改 | `C1` 種類且已被 `OFD115A` 列管,且四欄有變 | `args.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:354-358` |
| 伺服端刪除 / 覆核刪除 | `C1` 種類且已被 `OFD115A` 列管 | `args.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:382-385` |
| 種類下拉取值 | 已被 `COD007A` 用掉的種類不出現在下拉 | 下拉清單少幾筆 | 過濾(無提示) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:614` |
| 上述任一檢核發生例外 | `catch` 只呼叫 `HandleBusinessException`,`Cancel` 不設 | **放行** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:362-365`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:388-391` |

### 4.3 `CODM007` — 級距代碼維護

**用途(推測)**:維護用數值區間表示的代碼。`COD007A` 一列一個 `CODE_SORT` + `RANGE_CODE`,帶 `MIN_VALUE` / `MAX_VALUE`。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件:代碼種類(`=`)與級距代碼(`LIKE`)(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:126-137`)。明細頁:代碼種類、級距代碼、級距代碼說明、級距下限、級距上限。

**種類下拉走的是另一半**:同樣用 `ucCOD005ForCODM006`,但 `ProgramID = "CODM007"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:45-46`)。共用 PO 的分支是 `if (strID == "CODM006")` 走「排除 `COD007A`」那條、`else` 走「排除 `COD006A`」那條(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:634-637`)。**注意這是 `else` 不是 `== "CODM007"`** —— 任何沒帶 `ProgramID` 或帶錯值的呼叫端,都會**靜默拿到 `CODM007` 的清單**。

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:176-201`)** 三段:

1. 級距上限必須大於下限(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185`)。兩邊都不是 `DBNull` 才比,所以**只填一邊時這條不生效**。

2. 呼叫 `Check`,查這個代碼種類是不是已經出現在 `COD006A` 裡(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:233-293`)。

3. 框架必填檢核 `validatorManager1.DataValidate()`,**寫在最後一行**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:199`)。

**沒有任何檢核擋「同一種類下兩個級距重疊」或「級距之間有空隙」。**這是本節最值得記住的一件事。

**`MOD_FLAG` 的鎖定行為**:與 `CODM006` 相同,`"N"` 就鎖死整個明細頁(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110`);新增一律寫 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174`)。

**PO 事件**:只有三個 `Before*`,全部只做「換 SQL」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:49-51`)。查詢 SQL 是 `COD007A` `LEFT JOIN` `COD005A`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:156-222`)。

**SQL 裡的兩個毛病**:

- `MOD_FLAG` 被 `SELECT` 了兩次(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:170-171`)。Oracle 允許重複欄名,`DataAdapter` 填進 typed DataSet 時會產生第二個欄位 —— 能不能對上 xsd 取決於框架的 `MissingSchemaAction`,本機看不到。

- 兩個查詢條件都是字串串接,而且 `LIKE` 的 `%` 直接接在使用者輸入後面(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:188-192`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:202-206`)。

**跨表更新**:無。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 上限 ≤ 下限 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185` |
| 新增 / 修改前 | 上限或下限只填一邊 | **不檢查** | —— | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182` |
| 新增 / 修改前 | 同種類下級距重疊 / 有空隙 | **不檢查** | —— | —— |
| 新增 / 修改前 | 代碼種類已存在於 `COD006A` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:269-273` |
| 新增前 | `e.Cancel` 設定後仍繼續存取 `Rows[0]` 並寫 `MOD_FLAG` | 若結果集為空會丟例外 | (缺陷,見附錄 E) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:163-175` |
| 進入修改模式 | `MOD_FLAG = "N"` | 整頁唯讀 + 按鈕變灰 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110` |
| 種類下拉取值 | 已被 `COD006A` 用掉的種類不出現 | 下拉清單少幾筆 | 過濾(無提示) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:619` |
| `Check` 發生例外 | `catch` 把 `Result` 設成 `false` / 空訊息 | 檢核視為通過 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:281-286` |

### 4.4 `CODM009` — 員工資料維護

**用途(推測)**:維護 `COD009`。全模組最大的一支(UI 672 行、PO 758 行),也是全系統最多人 join 的那張表的唯一四眼入口。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件三個:員工代碼(`LIKE`)、中文姓名(`LIKE`)、身分證字號(`=`),後兩者空白就不加條件(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:168-181`)。明細頁二十幾個欄位,下拉與 Searcher 的來源:

| 控件 | 欄位 | 來源 | 錨點 |
|---|---|---|---|
| `ucomAO_CODE` / `ucomMANGR_CODE` / `ucomDAM_CODE` / `ucomEMP_CD` | 業務員區分碼 / 基金經理人 / 全委經理人別 / 員工類別 | `AoCodeDataSrc` `MangrCodeDataSrc` `EmpCdDataSrc` → `CTL014` 的 `003` `001` `002` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:577-583` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/EmpCdDataSrc.cs:18` |
| `ucomAGENT_ID` | 銷售機構區分碼 | `GetDropDownDataSrc("062")` → `CTL014` `062` = `TRUST_AGENT_ID` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:585` 配 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050` |
| `ucomG_JOB_CODE` | 通路職務別 | `GetDropDownDataSrc("701")` → `CTL014` `701`,**`CTL014.cs` 無對應類別** | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587` |
| `custPOSI_CODE` | 職稱 | `ucCOD006` → `COD006A` 某個 `CODE_SORT` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1891` |
| `custJOB_CODE` | 職位代號 | `ucCTL014`(**repo 內無原始碼,從呼叫端反推**)→ `CTL014` `702` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1900` 配 `DB/Table/updateCOD009.sql:17` |
| `custTO_EMP_NO` | 通知對象員工代碼 | `ucEmployeeData` → `COD009` 自己 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1893` |
| `custAGENT_CODE` | 業務歸屬銷售機構 | `ucAgentCode` → `OFD068A` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1896` |

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:456-497`)**:

1. 先跑框架必填,**有錯就直接 return**,底下四段都不執行(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:462-465`)。

2. 非公單(`IS_COMP_FEAT` 沒勾)時:身分證字號必填;有填就呼叫 `CHECK_ID_EXIST` 查重(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:467-477`)。

3. 英文姓名只能英數(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:479-482`)。

4. 業務到職日不得小於進公司日(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:484-485`)。

5. 系統使用者代號有填時呼叫 `CHECK_UID_CODE` 查重(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:488-496`)。

**兩支查重的行為差很多**:

| 方法 | SQL | 「在職」怎麼定義 | 判斷式 | 錨點 |
|---|---|---|---|---|
| `CHECK_UID_CODE` | 同一個系統使用者代號、不同員工代碼、且在職 | `NVL(LEAVE_DATE, ' ') = ' '` | `> 0` 就擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:389-402` |
| `CHECK_ID_EXIST` | 同一個身分證字號、不同員工代碼、且在職 | `(LEAVE_DATE = '19000101' or LEAVE_DATE = ' ')` | **`== 1` 才擋** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:568-581` |

兩個問題:(1) 同一支 PO 內「在職」有兩種寫法,而且 `CHECK_ID_EXIST` 那種**遇到 `LEAVE_DATE` 是 NULL 會整個條件變 UNKNOWN**,該筆不被算進去(Oracle 三值邏輯);(2) `== 1` 表示**已經有兩筆以上重複時反而放行**。兩條都列在附錄 E。

**身分證與 EMAIL 的格式檢核是「可忽略」的**:`CheckID` / `CheckEMail` 跳 `Warn03` 三選一對話框,按「否」才擋,按其他就用 `ByPassAddMessage` 記一筆放行(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:510-544`)。

**修改時的兩條特別規則**:

- **離職日不得小於進公司日**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:306-317`)。注意它先排除 `1900/1/1`,所以用 `1900/1/1` 當「沒離職」的哨兵值。

- **「是否同步更新優惠關係人資料」的詢問**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:320-331`):五個條件同時成立才跳 —— 原本有離職日、現在清空、員工類別是正式員工、原本也是正式員工、現在與原本都不是公單。按確定就把 `IS_UPDATE_OFD195` 設 `true` 帶到 PO。**但 PO 端沒有任何一行程式讀這個欄位**(整段 `AfterAdd` / `AfterDelete` 被註解,見下)。也就是這個問句問完不會發生任何事。

- 這段條件裡「正式員工」用的是常數 `EMP_CODE.Staff`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:324`),而 40 行之後同一個意思寫成字面值 `"1"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357`)。同一支檔案兩種風格。

**刪除前檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:387-445`)**:

1. `CheckEmpNo` —— 查 `COD010` 還有沒有這位員工的親屬,有就擋(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:602-650`)。

2. 「檢核是否已有契約異動資料」整段被註解(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421`)。PO 端的 `CheckRspChgDate` 還活著,但**沒有任何呼叫端**。

3. `CheckOFD195` —— 查 `OFD195A` 有沒有這位員工的優惠關係人資料,有就跳一個 `Warn01` 訊息「請記得至優惠關係人檔刪除該筆身份資料」,**沒有 `e.Cancel`**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429`)。使用者按掉就繼續刪。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:36-45`)**:掛了六個,其中三個是空的。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetToDoData` | 換 SQL(`COD009` `LEFT JOIN` `OFD002`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:343-368` |
| `BeforeUpdate` | **整支是空的**(只有一對大括號) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:370-373` |
| `AfterUpdate` | 若畫面送來的 `LEAVE_DATE` 是空字串,就下一道 `UPDATE` 把它設成真正的 `NULL` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:63-80` |
| `AfterAdd` | **整段被 `/* */` 註解**(原本要維護 `OFD195A`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` |
| `AfterDelete` | **整段被 `/* */` 註解**(原本要設 `OFD195A` 的終止日) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:251-274` |

`AfterUpdate` 那一道補救 `UPDATE` 值得說明:四眼引擎寫回去的是畫面送來的空字串,而 `COD009` 的 `LEAVE_DATE` 是字串欄位,空字串與 NULL 在 Oracle 其實同義 —— 但 `CHECK_UID_CODE` 用 `NVL(LEAVE_DATE,' ') = ' '`、`CHECK_ID_EXIST` 用 `LEAVE_DATE = ' '`,兩者對 NULL 的處理不同,所以這道補救**只讓其中一支查重正確**。

**跨表更新**:目前一個都沒有(全被註解)。設計上原本要同步維護 `OFD195A`。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填與格式 | 訊息清單並提前 return | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:460-465` |
| 新增 / 修改前 | 非公單卻沒填身分證字號 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:473-476` |
| 新增 / 修改前 | 身分證字號重複(在職且不同員工代碼,且**恰好一筆**) | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:579-580` |
| 新增 / 修改前 | 身分證 / 統編格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:514-525` |
| 新增 / 修改前 | EMAIL 格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:531-542` |
| 新增 / 修改前 | 英文姓名含非英數 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:479-482` |
| 新增 / 修改前 | 業務到職日 < 進公司日 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:484-485` |
| 新增 / 修改前 | 系統使用者代號已被別的在職員工用 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:401-402` |
| 修改前 | 離職日 < 進公司日 | 訊息清單 + return | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:310-316` |
| 修改前 | 非正式員工 / 改成公單且 `OFD195A` 有資料 | `Warn01` 提示,不擋 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:284-287` |
| 修改前 | 五條件同時成立時問「是否同步更新優惠關係人」 | 設旗標,**但 PO 不讀** | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:323-331` |
| 刪除前 | 該員工在 `COD010` 還有親屬 | 訊息清單 + return | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:627-631` |
| 刪除前 | 該員工在 `OFD195A` 有優惠關係人 | `Warn01` 提示,不擋 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429` |
| 刪除前 | 該員工已有契約異動資料 | **整段被註解,不執行** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421` |
| 查詢 | 查詢條件字串串接進 SQL | 撈到資料或語法錯 | 過濾(無提示) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:526` |
| Proxy 例外 | `CHECK_UID_CODE` / `CHECK_ID_EXIST` 的 `catch` **回傳 `ex.Message`** | 例外訊息被當成檢核失敗理由顯示 | 阻擋(理由錯誤) | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:36`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:101` |

### 4.5 `CODM010` — 員工親屬維護

**用途(推測)**:維護 `COD010`。一列一位親屬,綁在一位員工底下。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件五個:親屬身分證(`=`)、親屬關係代碼(`=`)、員工代碼(`=`)、員工姓名(`LIKE`)、員工身分證(`=`),全部空白就不加(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:221-250`)。明細頁:親屬身分證、姓名、關係代碼、出生日期、員工代碼、生效日期、終止日期。

**員工 Searcher 有兩道隱藏過濾**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:151-153` 把 `custEMP_NO` 的 `LEAVE_DATE` 設成 `1900/01/01`、`IS_COMP_FEAT` 設成 `"N"`,而 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:429-432` 在每次開 Searcher 前又重設一次 `IS_COMP_FEAT = "N"`。意思是**公單員工挑不到**,而且畫面上沒有任何提示。

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:66-109`)** 只剩兩條活的:

1. 出生日期必填,且必須小於 AP 伺服器的系統日(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:70-80`)。

2. 生效日期必填(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:82-83`)。

中間 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` 是**三份被註解掉的舊實作**,內容都是「親屬關係代碼為未成年子女時出生日期必填」。三份寫法互不相同(一份用 `umskBIR_DATE`、兩份用已不存在的 `udatBIR_DATE`),顯示這條規則被改過三次最後整個拿掉。

**新增時多一條**:親屬身分證第一碼若是英文字母,不可小寫(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:297-312`)。身分證格式本身走 `CheckID`,同樣是 `Warn03` 可忽略式(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:398-415`)。

**修改與刪除前的 `OFD195A` 檢核**:兩處寫法一樣,都是查到就跳 `Warn01`「請記得至優惠關係人檔刪除該筆身份資料」然後**不擋**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:273-282`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:453-462`)。刪除前那段的「契約異動資料」檢核與 `CODM009` 一樣被整段註解(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451`)。

**`CheckOFD195` 的 SQL 有一條反直覺的條件**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:692-697`):

```
WHERE REL_TYPE='1' AND REL_NO=:REL_NO AND REL_IDNO=:REL_IDNO
  AND REL_NO NOT IN (SELECT EMP_NO FROM COD009 WHERE IS_COMP_FEAT = 'N' AND EMP_CD = '1')
```

最後一行把「非公單的正式員工」整批排除掉。也就是**正常員工的親屬永遠查不到優惠關係人資料,提示永遠不會跳**;只有公單或非正式員工的親屬才會跳。`CODM009` 的同名方法**沒有**這一行(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:722-725`)。兩支同名方法、兩種語意。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:32-42`)**:掛了七個,四個是空的。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | 換 SQL(`COD010` `LEFT JOIN` `COD009`),而且**這一支是全模組唯一會綁參數的查詢** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:67-132` |
| `AfterAdd` / `AfterUpdate` / `AfterDelete` / `AfterUnDelete` | **四支的內容全部被註解**,只剩空方法 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:299-624` |

查詢 SQL 混用兩種風格:`REL_ID_NO` / `REL_CODE` 走字串串接的 `AddParam`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:141-175`),`EMP_NO` / `EMP_NAME` / `EMP_ID_NO` 走真正的繫結參數(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:101-118`)。同一條 SQL 兩種安全等級。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 出生日期未填或等於 `1900/01/01` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:70-71` |
| 新增 / 修改前 | 出生日期 ≥ 系統日 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:76-79` |
| 新增 / 修改前 | 生效日期未填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:82-83` |
| 新增前 | 身分證第一碼英文字母小寫 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:303-311` |
| 新增 / 修改前 | 身分證格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:402-414` |
| 新增 / 修改前 | 未成年子女必填出生日期 | **三份實作全被註解** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` |
| 修改 / 刪除前 | `OFD195A` 有該親屬資料(且員工非「非公單正式員工」) | `Warn01` 提示 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:278-281` |
| 刪除前 | 已有契約異動資料 | **整段被註解** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451` |
| 員工 Searcher | 公單員工不出現 | 挑不到人 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:429-432` |
| 終止日期 | 沒有任何「終止日 ≥ 生效日」的檢核 | —— | —— | —— |

### 4.6 `CODM016` — 憑證流水號區間維護

**用途(推測)**:替某檔基金配發一段紙張流水號(起號到迄號),存檔時由 SP 把區間展開成 `COD017` 的逐筆資料。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件只有基金代碼(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:78-90`)。明細頁三個欄位:基金代碼、流水號起號(唯讀)、流水號迄號。

**起號是自動帶的**:選好基金後觸發 `custFUND_ID_ValueChanged`,呼叫 `FindMaxSrno` 取該基金目前最大的迄號 +1;查不到就給 1(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:186-208` 配 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:821-895`)。**只在新增模式才帶**。

**三條伺服端往返的檢核**:

| 方法 | SQL | 用在哪 | 錨點 |
|---|---|---|---|
| `FindMaxSrno` | `SELECT FUND_ID, MAX(END_CTL_SRNO) FROM COD016 GROUP BY FUND_ID` | 帶起號、判斷是不是最後一批 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:821-895` |
| `ChkUsedData` | `COD016` `LEFT JOIN` `COD017`,區間內有 `CTL_SRNO_ID='1'`(已使用) | **宣告了但 UI 沒有任何呼叫端** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:563-638` |
| `ChkDiscardData` | 同上,條件改成 `CTL_SRNO_ID<>'0'`(已使用**或**作廢) | 修改前、刪除前 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:645-720` |

`CTL_SRNO_ID` 的三個值都寫死在 SQL 裡(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672`),而 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` 正好有對應常數。

**「只能改 / 刪最後一批」是怎麼實作的**:`CODM016_ModifyDataLoad` 在載入時就先算好 `Result = CheckMaxSrno(END_CTL_SRNO)`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:74-75`),之後修改與刪除都只看這個**快取下來的布林值**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:116-119`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:167-170`)。畫面停留期間別人新增了一批,這裡不會知道。

**存檔的三個 `After*` 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:51-53`)**:

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `AfterAdd` | 呼叫 SP `s_CODM016`,把起訖號、基金、`dataid` 與 13 個四眼欄位全部傳進去,由 SP 產生 `COD017` 的逐筆資料。`CommandTimeout = 0` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:99-143` |
| `AfterUpdate` | **先 `DELETE FROM COD017 WHERE [dataid] = @dataid`,再重跑一次 `s_CODM016`** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:145-315` |
| `AfterApproveDelete` | `DELETE FROM COD017 WHERE [dataid] = @dataid` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:317-370` |

**注意刪除的鍵是 `dataid` 而不是 `FUND_ID` + 流水號區間。**`dataid` 是四眼批次識別碼(`architecture.md §3.3`),所以「同一次 EVA 產生的 `COD017` 全部刪掉」。這是唯一把 `dataid` 當業務鍵用的地方,而 `COD017` 的 PK 是 `FUND_ID` + `BF_CTL_SRNO`。

`s_CODM016` **不在 `DB/` 底下**,`DB/SP/` 完全沒有這個檔。要知道區間怎麼展開、`BF_CER_NO` 怎麼配、有沒有檢查重疊,只能去資料庫看。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 迄號 < 起號 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:217-224` |
| 新增前 | 起號自動帶最大迄號 +1,且欄位唯讀 | 起號不可能重疊 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:56` |
| 修改前 | 區間內有已使用或已作廢的號碼 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:110-114` |
| 修改前 | 不是該基金最後一批 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:116-119` |
| 刪除前 | 區間內有已使用或已作廢的號碼 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:161-165` |
| 刪除前 | 不是該基金最後一批 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:167-170` |
| 查詢條件 | 基金代碼空白時用 `LIKE ''`、非空白用 `=` | **判斷式寫反**(`== ""` 走 `LIKE`) | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:82-89` |
| 存檔後 | SP 回傳 `i < 0` 才視為失敗 | 回 0 筆視為成功 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:139-142` |
| `ChkExsitData` | 宣告了但沒有呼叫端,且查詢條件用錯參數 | —— | (死碼,見附錄 E) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:774` |

### 4.7 `CODM017` — 憑證作廢 / 取消作廢

**用途(推測)**:針對單一張紙張流水號,做作廢或取消作廢。

**這一支不是四眼畫面**。`formstyle` 沒有宣告,但 UI 繼承的是 `xOneStepProcessForm`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:19`),PO 繼承 `BasicEVAPO` 卻沒有宣告 `MasterTable`,只有兩支手寫方法 `Get` 與 `Set`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:47`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:200`)。**它直接 `UPDATE COD017`,沒有 `STATUS`、沒有待辦、沒有覆核。**

**SQL 方言是 SQL Server**:`UPDATE [COD017] SET ... UpdateDate = GetDate()`,參數 `@` 前綴,型別用 `SqlDbType`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:74-86`)。`architecture.md §4.6` 的結論是執行期 Oracle-only —— 若該結論成立,這一支**執行期就是壞的**;若它還在跑,代表 `architecture.md §4.6` 需要修正。這條標**假設**,兩種可能本文無法從原始碼判定。

**畫面流程**:輸入基金代碼與紙張流水號 →「查詢」→ 顯示該號的受益憑證號碼與狀態 →「執行」。作廢 / 取消作廢由 `uoptAction` 單選鈕決定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:188-201`)。

**作廢原因下拉的兩道寫死過濾**:

- `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37`:`custCANCEL_CD_0.Dis = "00"` —— 排除代碼 `00`。

- `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38`:`custCANCEL_CD_0.Filter = "CODE NOT IN ('01','02','03','04','05')"` —— **一段 SQL 片段直接寫在 UI 的屬性裡**。

- 同樣五個值在 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:177-183` 又用 C# 比較寫了一次(當 `CTL_SRNO_ID != 2` 時不准挑這五個)。

作廢原因本身來自 `COD006A` 的 `CODE_SORT = '17'`,而那個 `'17'` 寫死在共用 PO(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`)。所以「作廢原因有哪些可選」這件事,答案分散在三個檔、兩種語言、三處硬編碼。

**`Get` 的兩條分支**:`Action = "0"` 時查 `CTL_SRNO_ID <> '2'`(還沒作廢的),否則查 `= '2'`(已作廢的)(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:249-252`)。`Action` 由 `uoptAction.CheckedIndex` 直接傳(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:200`) —— 用選項的**位置**當參數值,選項順序一改語意就反。

**`Set` 的結構問題**:`cmdModify` 只在 `act` 參數存在**且**值是 `"Y"` 或 `"N"` 時才會被賦值(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:68-131`);其餘情況走到 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132` 就對 `null` 呼叫 `AddInParameter`。而 `catch` 區塊裡 `tran.Rollback()` 在 `tran` 可能為 `null` 時執行(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:178-186`),真正的錯誤會被 `NullReferenceException` 蓋掉。

還有一個**綁了但沒用的參數**:`@CTL_SRNO_ID` 有 `AddInParameter`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:136`),但兩段 UPDATE 都是把 `[CTL_SRNO_ID]` 寫死成 `'2'` / `'0'`,SQL 裡沒有這個參數。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 / 執行前 | 共用的 `DoValidate` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:150-186` |
| 執行前 | 要作廢但沒填作廢原因 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:157-160` |
| 執行前 | 未作廢卻按「取消作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:162-166` |
| 執行前 | 已作廢卻按「作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:167-171` |
| 執行前 | 已有受益憑證號碼卻按「取消作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:172-175` |
| 執行前 | 非作廢狀態卻挑了 `01`–`05` 的作廢原因 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:177-183` |
| 執行前 | 要作廢且已有憑證號,但 `OFD721` 的 `CER_STATUS` 不是 `2` | `Info01` + `e.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:80-88` |
| 下拉取值 | 作廢原因排除 `00` 與 `01`–`05` | 選項變少 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37-38` |
| 執行 | `act` 參數不是 `Y` / `N` | `cmdModify` 為 `null` → 例外 | (缺陷,見附錄 E) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132` |
| 執行 | 影響筆數為 0 | 回滾並回傳**空訊息** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:168-176` |

### 4.8 `CODM036` — 級距設定(業務不明)

**用途**:`repo` 內查不到。表叫 `COD040A`,欄位只有級距下限、級距上限、級距說明。沒有任何其他程式讀它,也沒有任何註解說明它是什麼的級距。**本文不猜。**

**這是全模組唯一的多筆(MultiRow)四眼畫面**。PO 繼承 `BaseMultiRowEVADaoPO`,`MasterTable` 是集合(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:29-36`)。UI 用一個可編輯的 grid `ugrdCODM036` 直接綁 DataSet(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:67-72`)。

**畫面行為被改造成「只有一筆資料」的樣子**:切到查詢頁時自動查詢,有資料就雙擊第一列進修改模式、沒資料就進新增模式,然後把查詢頁藏起來、刪除鈕關掉(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:34-47`);按新增鈕之後同樣流程再跑一次並 `e.Cancel = true`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:49-65`);清除鈕在修改模式下也被改成「回到第一列」(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:83-98`)。使用者看到的是一個「永遠在編輯同一組級距」的畫面。

**兩段主檔 SQL,兩種取法**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:44-75`):

| 事件 | SQL | 取到什麼 |
|---|---|---|
| `BeforeSelect` / `BeforeGetToDoData` | `SELECT DATAID, MIN_VALUE, <四眼欄位> FROM COD040A WHERE ROWNUM < 3` | **最多 2 列**,而且沒有 `MAX_VALUE` 與 `VAL_DESC` |
| `BeforeGetMaintainData` | `SELECT DATAID, MIN_VALUE, MAX_VALUE, VAL_DESC, <四眼欄位> FROM COD040A WHERE 1 = 1` | 全表 |

`WHERE ROWNUM < 3` 是寫死的,沒有 `ORDER BY`,所以「那 2 列」是哪 2 列由 Oracle 決定。搭配上面的 UI 行為(只雙擊第一列),實務上等於「隨便撈一列進來當入口」。

**grid 端的檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:102-125`)** 三條:grid 一列都沒有 →「明細資料必須輸入」;任一列上下限是空的 →「級距上限,級距下限必須輸入」並標紅(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:134-148`);編輯儲存格時檢查「上下限完全相同的另一列」並擋下(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:150-164`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:215-243`)。**只擋完全相同,不擋重疊。**

**級距連續性交給共用控件**:`LevelGridUtility`(無原始碼,從呼叫端反推)在 `InitializeLayout` 時以下限欄、上限欄、`0.01` 與 `999999999999` 建立(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:172`),並掛在 `BeforeRowInsert` / `BeforeCellUpdate` / `BeforeRowsDeleted` 三個事件上。下限欄被設成不可編輯(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:179`),推測由該控件自動接續上一列的上限。**這條推測沒有原始碼可佐證。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | grid 沒有任何一列 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:106-109` |
| 新增 / 修改前 | 任一列上限或下限空白 | 訊息清單 + 該列標紅 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:118-121` |
| 編輯儲存格時 | 與另一列的上下限完全相同 | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:236-242` |
| 編輯儲存格時 | 級距重疊(不完全相同) | **不檢查** | —— | —— |
| 插入列時 | `LevelGridUtility` 的連續性規則 | 依控件而定 | (無原始碼) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:202-213` |
| 查詢 | `ROWNUM < 3` 且無 `ORDER BY` | 最多 2 列,順序不定 | 過濾(無提示) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` |
| grid 發生錯誤 | `ugrdCODM036_Error` 一律 `e.Cancel = true` | 錯誤被吞掉,畫面無反應 | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:258-261` |
| 刪除 | 刪除鈕在三處被強制關掉 | 這支畫面不能刪資料 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:46`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:63`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:71` |

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因有兩層,都可以從程式看出來:(1) **八支 M 畫面本身就內建查詢頁** —— `xMaintainForm` 的第一個 Tab 就是查詢(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:32`),條件、結果 grid、顯示欄位由 `App.config` 的 `ugrdResult` 宣告(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:48`),而代碼檔的查詢需求只有「用種類或代碼找一筆」;(2) **需要跨模組查員工的地方都走共用元件** —— `ucEmployeeData` 配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 提供了三條主分支加六個附加條件的員工查詢,各模組直接嵌控件,開一支 I 畫面反而多一個入口要維護。

**唯一像 I 的畫面是 `CODB009`**:它有查詢頁、有結果 grid、有篩選器(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:39`),只是多了一個「執行」動作,所以型別碼是 `B` 不是 `I`。`architecture.md §6.4` 說的「B 跟 I 是同一份程式碼」在這裡看得很清楚。

## 6. 批次(B)與 WindowsService

```text
[圖] COD 四支批次畫面的觸發、取數、寫入與副作用
圖中文字:① 四支 B 都是 OneStep 畫面，沒有排程也沒有服務 / CODB000 待辦清除 / 查 TODO 勾選後刪 / CODB009 機構回填 / 查 COD009 勾選後改 / CODB901 旗標維護 / 改 OutBound 與代號 / CODB902 帳號解鎖 / 改 AA_USER 並寄密碼 / ② 取數：兩支有自己的 SQL，兩支根本不查 / s_GetToDoData / SP 不在版控 / BuildMasterSQLString / COD009 OFD002 OFD068A / CODB901 CODB902 / 只吃畫面參數 不查主檔 / ③ 寫入：全部繞過四眼引擎，直接下 DML / DELETE TODO / 依待辦識別碼逐筆 / UPDATE COD009 / IN 清單用字串串接 / UPDATE COD009 / 旗標與系統使用者代號 / UPDATE AA_USER / 密碼與鎖定旗標 / ④ 副作用：只有 CODB902 有，而且三件事都值得注意 / 明文亂數密碼寄信 / 寄失敗就顯示在畫面上 / INSERT INTO CODB902 / 沒有欄位清單 / catch 回傳 ex.ToString / CODB901 CODB902 都是 / 沒勾選也能按執行 / CODB000 檢核沒掛上
```

*圖:圖 4 批次流。橘框＝本模組程式碼；黑框＝無原始碼；橘虛框＝要特別留意的行為。四支全部由使用者按鈕觸發，版控內沒有任何排程設定。*

見本節首的圖。

### 6.1 四支的共同結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| 畫面型別 | 四支都是 `xOneStepProcessForm`,`formstyle = "OneStep"`,一個 Tab | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:20-43` |
| 觸發 | **使用者按「執行」鈕**。repo 內沒有任何 COD 的排程設定或 WindowsService | 掃描器回報 Service 0 |
| 寫入路徑 | 四支全部**繞過四眼引擎**,PO 直接下 DML | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:36-72`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76-137`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:56-114`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:57-166` |
| 交易與失敗回報 | 四支都自己 `BeginTransaction` / `Commit` / `Rollback`、`finally` 裡 `Dispose`;失敗訊息 `CODB000` 是空的、`CODB009` 是中文、`CODB901` 與 `CODB902` **回傳 `ex.ToString()`** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:104`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:156` |

### 6.2 `CODB000` — 待辦事項清除

**做什麼**:查出登入者名下的待辦事項,勾選後刪掉。

**取數**:呼叫 SP `s_GetToDoData`,只傳一個參數 `v_striUserID`(從 `PermissionInfo[0].UserID` 來),用 RefCursor 回一個結果集落地成 `UC0301` 這張非實體表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:74-103`)。`CommandTimeout = 0`(永不逾時)。**這支 SP 不在 `DB/` 底下。**

**寫入**:對每一列 `IsCheck` 為真的資料下 `DELETE TODO WHERE TODODATAID = :TODODATAID`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:43-54`)。參數化,一列一次往返。

**這支的檢核沒有掛上去**:`CODB000_BeforeExecuteButtonClicked` 寫了「至少勾選一筆待辦事項」的檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:85-111`),但 `InitializeComponent` 只掛了 `FormInitial` / `ExecuteDataLoad` / `RefreshPage` / `Load` 四個事件(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:254-257`),**沒有掛 `BeforeExecuteButtonClicked`**。所以一筆都沒勾也可以按執行,結果是什麼都不刪、顯示成功。

**這支沒有 Designer 檔**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:143-281` 的 `InitializeComponent` 直接寫在同一個檔案裡,而且變數命名(`appearance2` / `cODB000ModelVDB` / `new string[0]`)是反編譯工具的典型輸出。`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs` 與 `Dev/ATLAS.COD/Source/Control/Control.COD/CODB000_Ctl.cs` 也是同樣的長相。**假設**:這一組的原始碼遺失過,現行版本是從 DLL 反編譯還原的。依據是三個檔同時具備上述特徵,而其餘 COD 檔案都保留了中文註解與 Designer 分離。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 至少勾選一筆 | **事件沒掛上,不執行** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:99-105` |
| 執行 | 沒有任何一列 `IsCheck` | 迴圈跑 0 次,`Commit` 後回報成功 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:45-57` |
| 執行 | 例外 | `Rollback` + 空訊息 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:59-64` |

### 6.3 `CODB009` — 員工銷售機構批次回填

**做什麼**:依員工代碼 / 姓名 / 部門查出一批員工,勾選後一次把他們的 `AGENT_ID` 與 `AGENT_CODE` 改成畫面上指定的值。

**取數**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:147-171`):

```
SELECT COD009.*, OFD002.DEPT_SH_NM, OFD068A.AGENT_SHNM
  FROM COD009
  LEFT JOIN OFD002   ON ...DEPT_NO
  LEFT JOIN OFD068A  ON ...AGENT_ID AND ...AGENT_CODE
 WHERE 1 = 1
```

三個查詢條件(員工代碼、姓名、部門)走 `EVAStringHelper.AddParam`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:158-159`),這支 helper 對 `Like` / `Equal` 有做單引號跳脫但對 `IN` 沒有(`architecture.md §4.7`)。

**寫入**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:89-109`):先用 LINQ 把勾選列的 `EMP_NO` 收成陣列,再組成

```
UPDATE COD009 SET AGENT_ID = :AGENT_ID, AGENT_CODE = :AGENT_CODE
 WHERE EMP_NO IN ('A','B','C')
```

**`AGENT_ID` / `AGENT_CODE` 是繫結參數,`EMP_NO` 的 `IN` 清單是 `string.Format` 串接**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:99-100`)。員工代碼來自資料庫而非直接輸入,但路徑上沒有跳脫;而且**陣列為空時會組出 `IN ('')`**,那會更新 `EMP_NO` 為空字串的列(如果有的話)。

**四眼欄位一個都不動**:雖然 PO 繼承 `BaseEVADaoPO` 且宣告了 `MasterTable`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43`),但覆寫的是 `Execute` 而不是 `Update`。所以這批資料的 `UPDATEID` / `UPDATEDATE` / `STATUS` 全部維持原值 —— **從 `CODM009` 看不出來誰改的**。

**UI 端的三個行為**:`ucomAGENT_ID` 被強制設成 `"0"` 且永遠 `Enabled = false`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:55-57`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:91`),所以只能掛到區分碼 `0` 的機構〔客戶特定〕;「銷售機構代碼」留空時兩個參數都傳空字串,等於**批次清除**且畫面上沒有提示(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:153-157`);「全選」鈕只勾選**沒有被 grid 篩選掉**的列(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:201-209`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 至少勾選一筆 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:257-267` |
| 執行前 | 銷售機構代碼留空 | 兩個參數傳空字串 → 批次清除 | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:153-157` |
| 執行 | 影響筆數為 0 | 回報失敗但**交易照樣 `Commit`** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:112-121` |
| 執行 | 例外 | `Rollback` + 「執行失敗,請檢查」 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:123-129` |
| 全程 | 不寫四眼欄位 | 異動無痕跡 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:93-109` |

### 6.4 `CODB901` — 員工旗標維護

**做什麼**:針對單一員工,改 `OUTBOUND`(理財中心是否為 OutBound 同仁)與 `UID_CODE`(系統使用者代號)。

**沒有查詢**:畫面上把查詢鈕關掉(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:48`),員工靠 `ucEmployeeData` Searcher 挑,挑完自動把該員工現在的 `OUTBOUND` 與 `UID_CODE` 帶進畫面(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:107-111`)。Searcher 的過濾條件是 `LEAVE_DATE = DateTime.Today`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:50`) —— 這個屬性名與值的關係要看 `ucEmployeeData`,本文不猜。

**寫入**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:66-86`):

```
UPDATE COD009 SET OutBound = :OutBound, UID_CODE = :UID_CODE,
                  UPDATEID = :UpdID, UPDATEDATE = sysdate
 WHERE EMP_NO = :EMP_NO
```

全部繫結參數,這是四支 B 裡 SQL 最乾淨的一支。**而且是唯一會寫 `UPDATEID` / `UPDATEDATE` 的一支**(但不寫 `STATUS`,所以仍然繞過四眼)。

**`OUTBOUND` 的值是 `"Y"` 或空字串**,不是 `"Y"` / `"N"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:71`)。而讀回來時是 `Convert.ToBoolean(...)`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:109`) —— 對字串 `"Y"` 做 `Convert.ToBoolean` 會丟 `FormatException`。**假設**:`ucEmployeeData` 回來的那個欄位已經被 `CASE ... THEN 1 ELSE 0 END` 轉成數字(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:361`),所以實際不會炸。依據是共用 PO 確實有這段轉換,但兩邊沒有任何契約保證。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:93-104` |
| 執行前 | 沒有任何業務檢核(例如新的使用者代號是否已被別人用) | —— | —— | —— |
| 執行 | 影響筆數為 0 | 回報失敗但**交易已 `Commit`** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:88-98` |
| 執行 | 例外 | 回傳 `ex.ToString()` 給畫面 | 阻擋(訊息是堆疊) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:101-106` |

**與 `CODM009` 的關係**:`UID_CODE` 在 `CODM009` 有一條查重檢核(§4.4),**這支完全沒有**。同一個欄位兩個入口、一個有卡控一個沒有。

### 6.5 `CODB902` — 使用者帳號解鎖 / 補發密碼

**做什麼**:兩個功能由一組單選鈕決定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:70`,用 `CheckedIndex` 當參數值,選項順序一改語意就反):

| `EXEC` | 功能 | 對 `AA_USER` 做什麼 | 錨點 |
|---|---|---|---|
| `"0"` | 解鎖 | `LASTLOGINTYPE = 0`、`HOSTNAME = ' '`、`BANMARK = 1` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:74-89` |
| 其他 | 補發密碼 | 先取該帳號的 EMAIL;產生 `Guid.NewGuid().ToString("N")` 當新密碼、加密後寫入,並設 `ISFORCECHANGEPWD = 1`;然後把**明文密碼**寄到那個 EMAIL | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:93-135` |

**三件要注意的事**:(1) **明文密碼會出現在兩個地方** —— 寄出的信件內文(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:126`),以及寄信失敗時**直接顯示在操作者畫面上**的「密碼發送失敗,密碼為:xxx」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:134`);(2) **執行歷程寫進一張叫 `CODB902` 的表**,`INSERT` **沒有欄位清單**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:137-149`),欄位順序一改值就全部錯位,而且這張表不在掃描器母體裡;(3) **EMAIL 沒設定時的提前 `return` 沒有處理交易**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101`),`tran` 已開啟卻沒有 `Commit` 也沒有 `Rollback`,只靠 `finally` 的 `Dispose`。

**寄信走 `ServerMailUtility`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:123`),產品名從 `StarterProxy().GetProductName()` 取(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:124`),兩者都無原始碼,從呼叫端反推。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:89-100` |
| 執行前 | 沒有「這個帳號真的鎖住了嗎」之類的業務檢核 | —— | —— | —— |
| 執行(補發) | 該帳號沒設 EMAIL | 訊息「必須先到UC0101設定使用者的〔電子郵件信箱〕」+ return | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101` |
| 執行(補發) | 寄信失敗 | 回報**成功**,訊息附明文密碼 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:131-135` |
| 執行 | 每次執行都寫一列歷程 | —— | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:137-149` |
| 執行 | 例外 | 回傳 `ex.ToString()` 給畫面 | 阻擋(訊息是堆疊) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:153-158` |

### 6.6 `CODB009` 與 `CODM009` 的分工

兩支畫面的主檔都是 `COD009`,掃描器也是這樣回報的(`主檔於:CODB009, CODM009, RSPM037`)。差別:

| 面向 | `CODM009` | `CODB009` |
|---|---|---|
| 一次處理幾筆 | 一筆 | 多筆(勾選) |
| 改哪些欄位 | 除了 `OUTBOUND` 與 `UPD_*` 之外幾乎全部 | **只有 `AGENT_ID` 與 `AGENT_CODE`** |
| 走不走四眼 | 走(有 `STATUS`、待辦、覆核) | **不走**,直接 `UPDATE` |
| 四眼欄位 | 由引擎寫 | **完全不動** |
| 檢核 | 十幾條(§4.4) | 只有「至少勾一筆」 |
| 查詢條件與顯示欄位 | 員工代碼 / 姓名 / 身分證;`App.config` 指定 7 欄 | 員工代碼 / 姓名 / **部門**;程式指定 9 欄,含機構三欄 |
| xsd | `CODM009Model.xsd`(55 欄,四眼欄位無中文名) | `CODB009Model.xsd`(**四眼欄位全部有中文名**,多一個 `ISCHECK` 與 `AGENT_SHNM`) |

**兩份 xsd 描述同一張表,欄位集合不一樣。**`CODB009Model.xsd` 少了 `BEF_EMP_CD` / `ADD195` / `IS_UPDATE_OFD195` 這類只有維護畫面用得到的暫存欄,多了 `ISCHECK`(勾選)與 `AGENT_SHNM`(join 來的機構名)。**改 `COD009` 的實體欄位時,三份 xsd 都要重生**:`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd`、以及 RSP 模組的 `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd`。

實務上的後果:**`CODB009` 改過的資料,在 `CODM009` 的待辦清單裡不會出現,在四眼紀錄上也看不到**。要追「誰把這批人掛到這個機構」,只能靠資料庫稽核或作業紀錄。

## 7. 報表(R)

**本模組無 R 畫面、無 `.rpt` 檔、無報表專案。**

`Dev/ATLAS.COD/Source/Vendor.ATLAS.COD.sln` 底下只有 `Control` / `Entity` / `FormProxy` / `PO` / `UI` 五個資料夾,沒有 `.Report` 對應專案(對照 CAS 有 `Dev/ATLAS.CAS.Report/`)。

原因(推測)有三條:(1) **代碼檔本身沒有報表需求** —— 三張代碼表的內容就是參數設定,要看直接開維護畫面查詢頁;(2) **員工名冊的報表不在 COD** —— `COD009` 被 12 個專案讀,需要員工清單的報表掛在各自模組下(例如 CAS 的 `CASR001` 用員工代碼當參數);(3) **憑證流水號的報表在 OFD** —— `COD017` 被 `Dev/ATLAS.OFD/` 底下兩個檔引用,列印與統計屬於 OFD(`OFD721` 才是憑證主檔)。

這三條都標**推測**:依據是 repo 內沒有任何 `CODR*` 代號、`rpt` 檔零支、`architecture.md §9.3` 的模組型別分佈也顯示 COD 只有 B 與 M。因此本節沒有「rpt 一覽表」可列。

## 8. 跨模組共用

```text
[圖] COD 六張表分別被哪些模組讀取，以及改動前必須一起看的地方
圖中文字:① COD009 員工主檔：121 個檔引用，遍及 12 個專案 / COD009 / 36 欄 無四眼欄位 / BasicCOD_PO / 共用員工查詢 三種部門版本 / RSPM037 / RSP 也拿它當主檔 / OFD RSP DSM CPM CAS / 只 JOIN 取姓名與部門 / ② COD006A 一般代碼：62 個檔，靠 CODE_SORT 字面值取用 / COD006A / PK CODE_SORT+CODE / ucCOD006 Searcher / 共用控件 走 CodeDataSrc / 約 40 個 CODE_SORT 值 / 散在 190 處字面值 / 作廢原因走 17 / 寫死在共用 PO 裡 / ③ CTL014 下拉選單：唯一有 250 個專屬類別的代碼表 / CTL014 / SourceType 分類 / BasicCMM_PO / 唯一讀取入口 / 250 個 DataSrc 類別 / 各綁死一個 SourceType / GetDropDownDataSrc / 呼叫時才給 SourceType / ④ 其餘四張表：本模組以外多半只讀不寫 / COD005A / CODM005 與共用 PO / COD007A / CODM007 與共用 PO / COD010 / CODM010 加 RSP OFD EC / COD016 COD017 / CODM016 017 加 OFD / ⑤ 改這幾張表之前一定要看的地方 / 改 COD009 欄位 / 三份 xsd 要一起重生 / 改 COD006A 代碼值 / 先查 190 處字面值 / 改 CTL014 某一類 / CTLB014 會整類刪光重寫
```

*圖:圖 5 誰在讀這些代碼表。橘框＝本模組的表；黑框＝共用讀取端（原始碼不在本模組）；灰虛框＝其他模組的入口；橘虛框＝改動前必須確認的事。*

見本節首的圖。掃描器對 COD 回報「無跨模組共用表」,那是因為它只比對 `MasterTable` / `DetailTable` 的宣告 —— **讀取方不會出現在主明細統計裡**。實際反查(對全 `Dev` 下的 `.cs` 做表名字面比對,排除 `*.Designer.cs`)結果如下。

### 8.1 六張表被誰讀

| 表 | 引用檔數 | 本模組外的分佈 |
|---|---|---|
| `COD009` | **121** | Common 19、OFD 16、RSP 11、DSM 10、CPM 9、CAS 8、OFDB 6、CRM 6、EC.Query 5、OFD.Query 4、TMK 3、其餘零星;本模組 8 |
| `COD006A` | **62** | OFD 9、CPM 8、RSP 7、OFDB 4、CAS 4、TMK 3、OTA.Query 3、OTA 3、Common 3、OTAB 2、EC 2;本模組 3 |
| `COD017` / `COD010` | 10 / 8 | `COD017`:Common 4、OFD 2、本模組 4;`COD010`:RSP / OFD / EC.Query / Common 各 1、本模組 4 |
| `COD005A` / `COD007A` | 各 4 | 各自 Common 1、本模組 3 |
| `COD016` / `COD040A` | 3 / 1 | 全在本模組 |

### 8.2 `COD009`:三個維護入口、一個共用查詢 PO

**三個維護入口**(全部把它當 `MasterTable`):

| 畫面 | 模組 | 動作 | 走四眼? | 錨點 |
|---|---|---|---|---|
| `CODM009` | COD | 單筆全欄位維護 | ✔ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:39` |
| `CODB009` | COD | 批次改銷售機構兩欄 | ✘ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43` |
| `RSPM037` | **RSP** | 查離職員工與其員眷 | 只查不寫 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79` |

`RSPM037` 的宣告寫在 `Select()` 方法內而不是建構子(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`),所以它的 `MasterTable` 是**呼叫時才成立的**。加上 `CODB901` 也會 `UPDATE COD009`(§6.4),實際上有**四個地方**會碰這張表。

**共用查詢 PO 才是最大的讀取端**:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 的 `GetEmployeeDataSrc` 一支方法裡有**三條主要分支加六個附加條件**,每一條的可見範圍都不一樣:

| 分支 / 條件 | SQL 主體 | 誰觸發 | 錨點 |
|---|---|---|---|
| 直銷部門版 | `COD009` `JOIN` `V_SAL051`(取最新一筆),部門取 `SAL_DEPT_NO` | 傳 `IS_SALE=Y` / `IS_DIRECT_EMPS` / `SEARCHER` / `SAL_DEPT_NO` 任一 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:279-293` |
| CPM 版 | 主檔換成 `V_TA_CPM_USER`,`COD009` 反而變成 `LEFT JOIN` | 傳 `IS_CPM=Y` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:335-346` |
| 一般部門版(預設) | `COD009` `LEFT JOIN` `OFD002` | 其餘 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:359-370` |
| `IS_Mass=Y` | 加 `DEPT_NO IN('G2','G11','G15','GC')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:378` |
| `IS_CASI001=Y` | 把 `FROM COD009` 字串替換成含 `CLS001A` 的 join,且 `USAGE = '3'` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:384` |
| `IS_CASB001=Y` | 加 `DEPT_NO IN('G3','GA','G17','G12','G13')` **且** `EMP_NO NOT IN ('100676','009037','850094','990651')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:392-393` |
| `IS_MARKETING=Y` | 加 `DEPT_NO IN('G3','GA','G17','G12','G13','G14','Z2')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:401` |
| `IS_SOLVE_DEPT_NO=Y` | 加 `DEPT_NO IN('OP1','M1','M2','E1')`(兩個分支各寫一次) | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:352`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:408` |

**這一支是「同一張員工表在不同畫面看到不同人」的總開關,而它不在 COD 底下。**改 `COD009` 的部門欄位語意、或調整部門代碼,這八處寫死清單全部要重新確認。

`IS_CASB001` 那條的員工代號黑名單(`100676` / `009037` / `850094` / `990651`)是**寫死的四個人**,而 CAS 那邊還有另一份白名單(`architecture.md` 與 CAS 篇都記過)。兩份名單獨立維護。

還有第三種「在職」定義藏在 `GetUidCode`:`AND (TRIM(COD009.LEAVE_DATE) IS NULL OR COD009.LEAVE_DATE >= TO_CHAR(sysdate, 'YYYYMMDD'))`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695`)。連同 §4.4 的兩種,同一個概念在三個地方三種寫法(附錄 E.3)。

### 8.3 `CTL014` 與 `CTLB014`:代號屬 CTL、檔案在 COD

`CTLB014` 六層齊全地放在 `Dev/ATLAS.COD/` 底下:

| 層 | 檔 |
|---|---|
| UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs` |
| FormProxy | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CTLB014_Pxy.cs` |
| Control | `Dev/ATLAS.COD/Source/Control/Control.COD/CTLB014_Ctl.cs` |
| PO | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs` |
| DataEntity | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd` |
| UIEntity | `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd` |

掃描器依代號前三碼把它歸給 CTL 模組,所以它**不在 COD 的母體 12 支裡**;但它是全系統下拉選單來源表 `CTL014` 的唯一維護入口,實務上要跟 COD 一起看。

**這支的行為是本篇最需要提醒的一件事**:

```
DELETE ctl014 WHERE sourcetype = :sourcetype        -- 先把整個代碼類別刪光
INSERT INTO CTL014 VALUES (...)                     -- 再把 grid 上的列一筆一筆寫回
```

`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:28-80`。四個後果:(1) **沒有四眼** —— `CTL014` 沒有 `STATUS` 也沒有 `DATAID`,這支直接 `Execute`,一個人就能改掉全系統某一類下拉選項;(2) **沒有樂觀鎖** —— 沒有 `DATAFLAG`,兩人同時開,後存的把先存的整批刪掉再寫自己的;(3) **`INSERT` 沒有欄位清單**(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`),欄位順序一改七個值全部錯位;(4) **`Description` 整類共用一個值**,從 `Utility.Parameters` 來、每列都寫同一個(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:55`),讀回來時取第一列的當結果訊息(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:95`)。

另外兩個小地方:`SOURCETYPE` 取值用 `vdb.Utility.Parameters[0].Value` —— **靠位置取參數**(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:38`、`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:89`);UI 端塞參數的順序是 `SOURCETYPE` / `DESCRIPTION` / `USERID`(`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs:77-81`),順序一調就全錯。而 `SourceType` 這個「代碼類別編號」本身**沒有任何維護畫面**,要新增一個類別只能直接下 SQL。

**讀取端**:全系統經 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197` 一支方法,由 250 個 `xxxDataSrc` 類別各綁死一個 `SourceType`(`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/`),外加 `GetDropDownDataSrc` 讓呼叫端自己傳(`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/GetDropDownDataSrc.cs:35-38`)。`GetDropDownDataSrc("062")` 一種寫法就出現 100 次。

### 8.4 `COD006A`:靠 `CODE_SORT` 字面值切成約 40 個互不相見的世界

讀取端統一走共用控件 `ucCOD006`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:21`),它提供四個屬性:`CODE_SORT`(單一種類)、`CODE_SORT_IN`(多種類)、`CODE_LIKE`、`Dis`(排除某個代碼)、`LENGTH`(限定代碼長度)。這些條件轉成參數送到 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257`。

**兩個要注意的地方**:

- `ucCOD006` 送出的參數名是 `"Dis"`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:108-110`),而 PO 端找的是 `"DIS"`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:188-189`)。`FindByName` 的實作在框架 DLL 內(無原始碼,從呼叫端反推),**若它大小寫敏感,`Dis` 這個排除條件會被靜默丟棄**。`CODM017` 正好用了這個屬性(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37`)。這條標**假設**,依據是兩邊字面不同且沒有正規化。

- `CODE_SORT_IN` 分支用 `string.Format` 把逗號分隔字串串成 `IN ('a','b')`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:202-211`),其餘條件都是繫結參數。同一支方法內兩種安全等級。

`Filter` 屬性(`CODM017` 用來排除 `01`–`05`)**不在 `ucCOD006` 的原始碼裡**,是基底 `xSimpleSearcher` 的(無原始碼,從呼叫端反推)。也就是那段 SQL 片段會被送到哪一層、有沒有跳脫,repo 內看不到。

### 8.5 COD 借用的表

| 表 | 用途 | 誰用 | 錨點 |
|---|---|---|---|
| `OFD002` / `OFD068A` / `OFD081` | 部門中文簡稱 / 銷售機構簡稱 / 基金簡稱 | `CODM009` `CODM010` `CODB009` / `CODB009` / `CODM016` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:469-470`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:154-155`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:410-411` |
| `OFD115A` | 判斷代碼是否已作為列管原因 | `CODM006` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343` |
| `OFD195A` | 判斷員工 / 親屬是否已是優惠關係人 | `CODM009` / `CODM010` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:722-725`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:692-697` |
| `OFD721` | 憑證狀態,判斷能否作廢 | `CODM017` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:216-218` |
| `AA_USER` / `TODO` | 平台使用者帳號 / 平台待辦事項 | `CODB902` / `CODB000` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:74-80`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:43` |

**全部唯讀,除了 `AA_USER` 與 `TODO`。**COD 會寫平台庫的這兩張表,是本模組唯一跨越業務庫 / 平台庫邊界的地方(`architecture.md §3.7` 說明兩個庫的分工)。

### 8.6 改動影響面速查

| 想改什麼 | 一定要一起看 |
|---|---|
| `COD009` 加 / 改欄位 | 三份 xsd(`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd`)+ `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:426-487` 的欄位清單 + `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 的三條 SQL + `DB/Table/updateCOD009.sql` 那兩張 eHR 介接表 |
| `COD009` 的部門代碼語意 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs` 內四組寫死的部門清單 |
| `COD006A` 某個代碼種類的值 | 先 grep 該 `CODE_SORT` 的字面值(附錄 C.2 有清單),190 處裡可能有人硬比對 |
| `COD006A` 加欄位 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:37-96` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257` 兩支共用查詢的欄位清單、`Dev/Common/Source/DataSource/DataEntity.DataSource/` 底下的 `COD_*` typed DataSet |
| `CTL014` 某一類的選項 | 用 `CTLB014` 改會**整類刪光重寫**;同時確認 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 有沒有對應類別,有的話那份常數不會跟著變 |
| `CTL014` 加欄位 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49` 的 `INSERT` **沒有欄位清單**,加欄位一定要同步改這裡 |
| `COD016` / `COD017` | `s_CODM016` 這支 SP 不在版控,改欄位要連 DB 一起改;而且這兩張表的四眼欄位是混合大小寫 |
| `COD005A` 的種類 | 兩支下拉 SQL(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`)的互斥規則 |

## 附錄 A. 資料表總表

| 表 | 欄位數(xsd) | 四眼 13 欄 | 主檔於 | 被誰讀(檔數) | 說明 |
|---|---|---|---|---|---|
| `COD005A` | 17 | ✔(無中文名) | `CODM005` | 4 | 代碼種類主檔 |
| `COD006A` | 23 | ✔(無中文名) | `CODM006` | 62 | 一般代碼明細〔共用〕 |
| `COD007A` | 22 | ✔(無中文名) | `CODM007` | 4 | 級距代碼 |
| `COD009` | 55(`CODM009` 版)/ 47(`CODB009` 版) | ✔(`CODB009` 版有全套中文名) | `CODM009` `CODB009` `RSPM037` | 121 | 員工主檔〔共用〕 |
| `COD010` | 35 | ✔(無中文名) | `CODM010` | 8 | 員工親屬 |
| `COD016` / `COD017` | 19 / 21 | ✔(**小寫混合**) | `CODM016` / 無四眼入口 | 3 / 10 | 憑證流水號區間與逐筆狀態;`COD017` 由 SP 產生 |
| `COD040A` | 18 | ✔ | `CODM036`(掃描器漏) | 1 | 級距設定,業務不明 |
| `CTL014` | **4** | **✘** | `CTLB014`(代號屬 CTL) | 下拉選單的唯一來源 | 無 PK、無四眼、無樂觀鎖 |
| `CODB902` | (無 xsd) | ✘ | —— | 1 | 解鎖 / 補發密碼的執行歷程;`INSERT` 無欄位清單 |
| `COD009_ehr` / `COD009_eHRLOG` | (無 xsd) | ✘ | —— | **0** | 只出現在 `DB/Table/updateCOD009.sql:2-10`;匯入程式不在本 repo |

**非實體結果集**:`UC0301`(`CODB000` 的待辦清單,由 `s_GetToDoData` 回傳,定義在 `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB000Model.cs`)。**外部唯讀表**:`OFD002`、`OFD068A`、`OFD081`、`OFD115A`、`OFD195A`、`OFD721`、`CLS001A`(經共用 PO)、`SAL051`(經 `V_SAL051`)、`AA_USER`、`TODO`。

## 附錄 B. SP / Function / Trigger / View

掃描器對 COD 回報 SP 0 / Fn 0 / Trigger 0 / View 0 —— **因為 `DB/` 底下沒有任何 COD 的物件檔**。但程式確實呼叫了兩支 SP 與兩個 View:

| 類 | 名稱 | 誰呼叫 | 在 `DB/` 裡? | 錨點 |
|---|---|---|---|---|
| SP | `s_CODM016` | `CODM016` 的 `AfterAdd` / `AfterUpdate` | **否** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:119`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:286` |
| SP | `s_GetToDoData` | `CODB000` 的 `Select` | **否** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:79` |
| View | `V_SAL051` / `V_TA_CPM_USER` | 共用 `GetEmployeeDataSrc` 的直銷部門版 / CPM 版 | **否** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:291`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:343` |
| Function | `F_TA_GET_DIRECT_EMPS` / `sw.f_ta_chk_cls_auth` | 共用 `GetEmployeeDataSrc` 的 `IS_DIRECT_EMPS` / `SEARCHER` 條件 | **否** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:308`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:327` |

`architecture.md 附錄 B.0` 說 `DB/` 只涵蓋 16% 的 SP;COD 這邊是 0%。`DB/` 底下唯一與 COD 有關的檔是 `DB/Table/updateCOD009.sql`(加三個欄位到 `COD009`、兩個到 `COD009_ehr` 與 `COD009_eHRLOG`),schema 前綴是 `sw.`。

## 附錄 C. 代碼對照

本篇的代碼值來源有五種,每一條都標明是**表**還是**程式常數**:

### C.1 `CTL014` 的 `SourceType`(表 + 程式常數,覆蓋率 47%)

`CTL014.cs` 有 187 個靜態類別 / 566 個值,其中 186 個類別的註解帶著 `SourceType` 編號。以下只列與 COD 直接相關的,完整清單請直接讀 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs`。

| SourceType | 類別 | 中文 | 值域 | COD 哪裡用 | 錨點 |
|---|---|---|---|---|---|
| `000` | `YES_NO` | 是 / 否 | `Y` `N` | `CODM006` / `CODM007` 的 `MOD_FLAG` grid 下拉 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-21`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/YesNoDataSrc.cs:18` |
| `001` | `MGR_CODE` | 基金經理人類別 | `0` 其他 / `1` 基金經理人 / `2` 研究員 | `CODM009` 的 `MANGR_CODE`、`DAM_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:27-43` |
| `002` | `EMP_CODE` | 員工類別 | `0` 其他 / `1` 正式員工 / `2` 工讀生 / `3` 臨時工 …… | `CODM009` 的 `EMP_CD`;新增預設 `"1"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45-65`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/EmpCdDataSrc.cs:18` |
| `003` | `SALES_CODE` | 業務員區分碼 | 見類別 | `CODM009` 的 `AO_CODE`;新增預設 `"N"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:67-79`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/AoCodeDataSrc.cs:19` |
| `004` | `VALID_CODE` | 部門 / 通路 / 銷售機構有效碼 | 見類別 | `CODM006` 的 `VALID_CODE`;新增預設 `"Y"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81-93`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17` |
| `062` | `TRUST_AGENT_ID` | 銷售機構區別碼 | 見類別 | `CODM009` / `CODB009` 的 `AGENT_ID`;`CODB009` 強制鎖成 `"0"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:56` |
| `701` | **無對應類別** | 通路職務別 | `1` 部門主管 / `2` 組主管或業務員 / `3` 業務助理(**只寫在 DB 註解**) | `CODM009` 的 `G_JOB_CODE` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587`、`DB/Table/updateCOD009.sql:15` |
| `702` | **無對應類別** | 職位代號 | **repo 內查不到** | `CODM009` 的 `JOB_CODE`(走無原始碼的 `ucCTL014`) | `DB/Table/updateCOD009.sql:17` |
| —— | `CTL_SRNO_ID` | 紙張流水號識別碼 | `0` 未使用 / `1` 已使用 / `2` 作廢 | `COD016` / `COD017`;**程式全部寫死字面值,常數零引用** | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` |

**全庫統計**(掃 `Dev` 下所有 `.cs`,排除 `obj` / `bin`):

| 量 | 數字 |
|---|---|
| `CTL014.cs` 帶編號的類別 | 186 |
| 程式實際用到的 `SourceType`(`GetDropDownDataSrc("nnn")` + 250 個專屬 DataSrc 的 `m_sourcetype`) | 395 |
| 用到但 `CTL014.cs` 沒有對應類別 | **224** |
| 有類別但沒有任何地方直接用 | 15(`022` `032` `033` `034` `086` `112` `120` `121` `122` `123` `132` `135` `136` `147` `247`) |
| 最常被直接呼叫的 SourceType | `062`(100 次)、`107`(36)、`408`(24)、`404`(20)、`000`(20)、`220`(19) |

### C.2 `COD006A` 的 `CODE_SORT`(只有表,程式常數零引用)

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 的 `CODE_SORT` 類別:

| 值 | 常數名 | 中文 | 值 | 常數名 | 中文 |
|---|---|---|---|---|---|
| `01` | `Language` | 語言代碼 | `31` | `ServiceKind` | 服務類別代碼 |
| `02` | `EducationLevel` | 教育程度代碼 | `32` | `InvestAffinity` | 投資傾向代碼 |
| `03` | `CareerKind` | 職業別代碼 | `33` | `ExpectInvestTime` | 預期投資時間代碼 |
| `04` | `CareerTitle` | 職稱代碼 | `39` | `FundAllotLackDoc` | 基金申購缺件文件代碼 |
| `11` | `CtAskData` | 客戶索取資料代碼 | `40` | `FundRedeemLackDoc` | 基金買回缺件文件代碼 |
| `12` | `CtComplainKind` | 客訴內容種類代碼 | `41` | `RSPLackDoc` | 定時定額缺件文件代碼 |
| `13` | `CtComplainProcess` | 客訴處理代碼 | `60` | `AllotDateRecoveryReason` | 申購日結回復說明代碼 |
| `15` | `CtRiskAnalyze` | 客戶風險分析代碼 | `61` | `RedeemDateRecoveryReason` | 贖回日結回復說明代碼 |
| `19` | `CtInvestExpect` | 客戶投資意願代碼 | `84` | `CallCode` | 來電代碼 |
| `20` | `CtLevel` | 客戶等級代碼 | `89` | `NewBFLackDoc` | 開戶缺件文件代碼 |
| `23` | `TurnBackKind` | 退件類別代碼 | `90` | `AllotProblemReason` | 申購問題件原因代碼 |
| `27` | `PotentialCtDealingWithInvestmentTrust` | 潛在客戶往來投信公司 | `91` | `RedeemProblemReason` | 贖回問題件原因代碼 |
| `28` | `PotentialCtDealingWithFund` | 潛在客戶承購基金資料 | `99` | `ContactKind` | 聯絡人作業別 |
| `29` | `PotentialCtNeedService` | 潛在客戶所需服務項目 | `A1` | `InvestRegionLevel` | 投資級距代碼 |
| `30` | `PotentialCtDealingWithBond` | 潛在客戶承購債券資料 | `A2` | `IncomeRegionLevel` | 收入級距代碼 |
| —— | —— | —— | `A3` | `NowInvestRegionLevel` | 目前可投資級距 |

**這 31 個常數的全庫引用次數是 0。**實際在用的是字面值:

| `CODE_SORT` 字面值 | 出現處數 | 在上表? | 首見 |
|---|---|---|---|
| `42` | 19 | ✘ | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1684` |
| `P3` | 18 | ✘ | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:108` |
| `17` | 16 | ✘(**作廢原因**) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| `13` | 15 | ✔ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:451` |
| `20` | 14 | ✔ | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:117` |
| `C7` | 9 | ✘ | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM562_PO.cs:134` |
| `12` | 8 | ✔ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:535` |
| `A7` | 7 | ✘ | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:471` |
| `Q2` | 7 | ✘ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:134` |
| `D2` | 6 | ✘ | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:457` |
| `11` `A8` `E2` `E3` `50` `45` `E4` `PC` | 各 4–5 | 只有 `11` ✔ | —— |
| `1C` `C6` `P5` `P7` `1B` `23` `84` `E8` `PD` | 各 2–3 | `23` `84` ✔ | —— |
| `00` `15` `19` `36` `51` `89` `99` `C5` `E7` `E9` `HO` `P1` | 各 1 | `15` `19` `89` `99` ✔ | —— |
| `C1` | 2(**列管原因**;`!=` 比較,不在上面 `=` / `==` 的統計裡) | ✘ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` |

**約 30 個實際在用的代碼種類,在 `CODCode.cs` 裡查不到中文說明。**要知道它們是什麼,只能連資料庫查 `COD005A` 的 `CODE_SORT_DESCRP`。

### C.3 `EMP_DEPT_TYPE`(程式常數,有在用)

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:141-167`,全庫 74 次引用 / 19 個檔。**COD 自己一次都沒用。**

| 值 | 常數名 | 中文 |
|---|---|---|
| `01` | `IsSellAgent` | 代銷 |
| `02` | `IsSales` | 直銷 |
| `03` | `IsKeyIN` | KEYIN 櫃檯 |
| `04` | `IsOther` | 其它(股務等) |
| `05` / `06` | `IsFin` / `IsProFin` | 理財 / 專戶理財 |

### C.4 本模組內寫死的代碼值〔客戶特定〕

| 值 | 意思 | 在哪 | 錨點 |
|---|---|---|---|
| `"C1"` | 列管原因的代碼種類 | `CODM006` 的 `BeforeUpdate` / `BeforeApproveDelete` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372` |
| `'17'` | 作廢原因的代碼種類 | 共用 PO 的 `GetCancelCdDataSrc` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| `'2'` / `'0'` | `CTL_SRNO_ID` 作廢 / 未使用 | `CODM017` 的兩段 UPDATE、`CODM016` 的兩支檢核、`CODM017` UI 的分支 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:107` |
| `'1'` | `CTL_SRNO_ID` 已使用 | `CODM016` 的 `ChkUsedData` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590` |
| `"00"` 與 `'01'`–`'05'` | 不可挑選的作廢原因 | `CODM017` UI,一次寫在 `Filter` SQL 片段、一次寫在 C# 比較 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37-38`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:179` |
| `"07"` | `FEE_CODE` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:232` |
| `"0"` | `EMP_QUOTA_CODE` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:237` |
| `"N"` / `"0"` / `"1"` | `AO_CODE` / `MANGR_CODE` / `EMP_CD` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:89-92` |
| `"Y"` | `MOD_FLAG` 的新增固定值 | `CODM006` / `CODM007` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174` |
| `"Y"` | `VALID_CODE` 的新增預設值 | `CODM006` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:38` |
| `'19000101'` / `' '` | 「沒有離職日」的兩種哨兵值 | `CODM009` 的兩支查重 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395` |
| `"2"` | `OFD721` 的 `CER_STATUS`「可作廢」 | `CODM017` UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:82` |
| `0.01` / `999999999999` | `CODM036` 級距的上下界 | `CODM036` UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:172` |
| `ROWNUM < 3` | `CODM036` 查詢頁最多兩列 | `CODM036` PO | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` |

### C.5 四眼 `STATUS`

見 `architecture.md §3.10`。本模組沒有任何程式直接比對 `STATUS`,值域完全由框架決定。`CTL014`、`COD017`(由 SP 產生的部分)、以及四支 B 改過的資料**沒有有意義的 `STATUS`**。

## 附錄 D. 掃描母體與覆蓋率

`py -V:3.12 /docs/tools/atlas_scan.py --module COD --doc /docs/modules/cod.md` 的結果。

母體:畫面 12(B 4 / I 0 / M 8 / R 0)· 表 6 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 0 · Service 0。

**本文對母體的處置**:12 支畫面全部寫進 §3–§6(一支一節)、6 張表全部寫進 §2.3 與附錄 A;SP / Fn / Trigger / View / rpt / Service 各 0 的原因寫在 §7 與附錄 B,並補上程式有呼叫、`DB/` 卻沒有的 6 個 DB 物件。

**母體以外、本文額外納入的**:

| 項目 | 為什麼不在母體 | 本文寫在哪 |
|---|---|---|
| `COD040A` | `CODM036` 用 `MasterTable.Add(...)`,掃描器的正規式只認賦值寫法 | §2.1、§2.3 |
| `CTL014` / `CTLB014` | 代號前三碼是 CTL,掃描器歸給 CTL 模組 | §8.3 |
| `COD017` | 不是任何畫面的 `MasterTable`(只在 `CODM016` 的 xsd 內當第二張表) | §2.3、§4.6 |
| `CODB902`(當表用)/ `COD009_ehr` / `COD009_eHRLOG` | 前者不是任何畫面的 `MasterTable`,後兩者只在 DB 腳本裡、`.cs` 零引用 | §0.3、§6.5、附錄 A |
| `s_CODM016` / `s_GetToDoData` / `V_SAL051` / `V_TA_CPM_USER` / `F_TA_GET_DIRECT_EMPS` | `DB/` 底下沒有這些檔,掃描器只掃 `DB/` | 附錄 B |

上述項目中不在掃描索引裡的名字列在 meta 的 `refcheck-ignore`,因為它們**確實存在於系統中** —— 不是本文編造的。

## 附錄 E. 讀本文時要注意的地方

讀碼過程發現的缺陷與陷阱,依類型分。每一條都是**現況記錄,不是修改建議**。

### E.1 Oracle 三值邏輯與 `AND` / `OR` 條件

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | `CheckRspChgDate` 的條件 `WHERE (RSP_CHG_DATE<>'19000101' or RSP_CHG_DATE<>'')` —— 兩個 `<>` 用 `OR` 串,**對任何非 NULL 的值都恆真** | 這條「是否已有契約異動資料」的檢核等於沒有條件,只要該員工在 `OFD195A` 有任何一列就會成立。目前呼叫端被註解掉所以沒發作,一旦解除註解就會**每次都跳警告** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:671` | **高** |
| E1.2 | `CHECK_ID_EXIST` 的在職條件 `AND (LEAVE_DATE = '19000101' or LEAVE_DATE = ' ')` —— **沒有處理 NULL**。而同一支 PO 的 `CHECK_UID_CODE` 用的是 `NVL(LEAVE_DATE, ' ') = ' '` | `LEAVE_DATE` 為 NULL 的在職員工不會被算進重複檢查,身分證字號可以重複輸入。`AfterUpdate` 那道補救 `UPDATE` 正好會把空字串改成 NULL(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:72-79`),**等於系統自己製造出這個漏洞** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573` | **高** |
| E1.3 | `CheckOFD195` 在 `CODM010` 多了一行 `AND REL_NO NOT IN (SELECT EMP_NO FROM COD009 WHERE IS_COMP_FEAT = 'N' AND EMP_CD = '1')`,`CODM009` 的同名方法沒有 | 「非公單的正式員工」的親屬,刪除時**永遠不會跳**優惠關係人提示。兩支同名方法兩種語意,讀 `CODM009` 那支會誤判 `CODM010` 的行為 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:697` | 中 |
| E1.4 | `CheckRspChgDate` 在 `CODM010` 用 `NVL(RSP_CHG_DATE,' ') <>' '`,在 `CODM009` 用 E1.1 那個恆真式 | 同一個檢核兩份實作,一份正確一份壞掉 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:645` | 中 |

### E.2 `catch` 之後把例外訊息當資料值

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | `CODM009_Pxy.CHECK_UID_CODE` 與 `CHECK_ID_EXIST` 的 `catch` **`return ex.Message;`**。呼叫端的判斷是「回傳字串非空 = 檢核不通過」 | 任何 Remoting 中斷或 DB 錯誤,都會變成一則**顯示在欄位旁邊的紅字驗證訊息**,內容是 .NET 例外文字;而且使用者被擋下來的理由與真因無關 | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:36`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:101` | **高** |
| E2.2 | `CODB901` / `CODB902` 的 `catch` **`AddResultRow(false, 0, ex.ToString())`** —— 連堆疊追蹤一起丟到畫面 | 使用者看到完整堆疊(含類別名、行號、伺服器路徑);同一個方案的其他 PO 用的是空字串或固定中文 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:104`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:156` | **高** |
| E2.3 | `CODM005_PO.CHECK_CODE_SORT` 的 `catch` 只呼叫 `HandleBusinessException`,`strResult` 維持空字串 | DB 查不到時檢核**視為通過**,該刪的擋不住 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:195-198` | 中 |
| E2.4 | `CODM006_PO` 的 `BeforeUpdate` / `BeforeApproveDelete` 的 `catch` 不設 `args.Cancel` | 查 `OFD115A` 失敗時,列管保護**自動放行** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:362-365`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:388-391` | 中 |

### E.3 同一概念多套實作

| # | 概念 | 有幾套 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | 「員工在職」 | **三套**:`NVL(LEAVE_DATE,' ')=' '`、`(LEAVE_DATE='19000101' or LEAVE_DATE=' ')`、`(TRIM(LEAVE_DATE) IS NULL OR LEAVE_DATE >= TO_CHAR(sysdate,'YYYYMMDD'))` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695` | **高** |
| E3.2 | 「查詢條件轉 SQL」 | `CODM006` / `CODM009` / `CODM010` 各自有一份 private `AddParam`,三份**逐字相同**;另外還有共用的 `EVAStringHelper.AddParam` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:279-312`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:496-530`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:141-175` | 中 |
| E3.3 | 「取參數值」 | 三份 private `GetParamValue`(逐字相同,而且**全部沒有呼叫端**) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:321-331`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:539-549`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:185-195` | 低 |
| E3.4 | 「檢核身分證格式」 | `CODM009` 用 `ValidateManager`,`CODM010` 用 `UIValidator`,兩個不同的類別 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:514`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:402` | 低 |

### E.4 被註解掉但外殼還在的檢核

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E4.1 | `CODM005` 刪除前的檢核:UI 端組好了 `view2` 與參數,**呼叫 Proxy 那一行被註解**,底下的 `if` 判斷一個永遠空的結果集 | 讀 UI 會以為卡控在用戶端;實際擋住的是伺服端覆寫的 `Delete`。兩邊訊息文字還不一樣 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:123`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM005_Pxy.cs:134` | 中 |
| E4.2 | `CODM009` / `CODM010` 刪除前的「檢核是否已有契約異動資料」整段被註解,但 PO 端的 `CheckRspChgDate` 兩份實作都還活著、介面也還宣告著 | 兩支**沒有任何呼叫端的公開方法**留在 Remoting 契約上 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451` | 中 |
| E4.3 | `CODM009_PO` 的 `AfterAdd` 與 `AfterDelete` **整段被 `/* */` 包起來**,但建構子仍然掛這兩個事件 | 「新增員工時自動建立優惠關係人」「刪除員工時設終止日」兩條規則**現在不存在**,而事件掛點看起來像有 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:251-274`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` | **高** |
| E4.4 | `CODM010_PO` 的四個 `After*` 全部只剩空方法 | 同上 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:299-624` | **高** |
| E4.5 | `CODM010` 的「未成年子女必填出生日期」有**三份被註解的實作**,寫法互不相同,兩份還引用已不存在的控件 | 這條業務規則被改過三次最後拿掉,但沒有人知道是刻意還是遺漏 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` | 中 |
| E4.6 | `CODM005_PO` 1,188 行裡只有約 40 行是活的;`CODM006_PO` 1,362 行約 400 行活;`CODM007_PO` 1,236 行約 290 行活;`CODM016_PO` 2,050 行約 900 行活 | 讀碼成本被放大 3–30 倍;`grep` 會撈到大量死碼 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:233-1064` | 中 |

### E.5 有訊息但沒有 `return` / 沒有 `Cancel`

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | `CODM009` 與 `CODM010` 的 `OFD195A` 檢核:跳 `Warn01`「請記得至優惠關係人檔刪除該筆身份資料」後**沒有 `e.Cancel`** | 使用者按確定就繼續刪 / 改,優惠關係人資料留在 `OFD195A` 變孤兒 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:453-462` | 中 |
| E5.2 | `CODM007_BeforeAddButtonClicked` 在設完 `e.Cancel = true` 之後,**仍然繼續存取 `Rows[0]`** 並寫 `MOD_FLAG` | 若結果集為空會丟例外;而且被取消的動作還在改資料 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:163-175` | 中 |
| E5.3 | `CODM006_BeforeAddButtonClicked` 同樣的結構 | 同上 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:151-165` | 中 |
| E5.4 | `CODB000_BeforeExecuteButtonClicked` 寫了「至少勾選一筆」,但 `InitializeComponent` **沒有掛這個事件** | 檢核從來沒有執行過 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:254-257` | 中 |
| E5.5 | `CODB009` / `CODB901` 影響筆數為 0 時回報失敗,但 `Commit` **已經執行** | 「失敗」訊息與交易狀態不一致 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:112-121`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:88-98` | 低 |
| E5.6 | `CODB902` 寄信失敗時 `AddResultRow(true, ...)` —— 回報**成功** | 操作者以為信寄出去了 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:132-135` | 中 |
| E5.7 | `CODM036` 的 `ugrdCODM036_Error` 一律 `e.Cancel = true` | grid 的所有錯誤被靜默吞掉 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:258-261` | 低 |

### E.6 代碼值寫死在 SQL 或程式裡(代碼模組的自我矛盾)

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | `CODE_SORT` 的 31 個程式常數**全庫零引用**;實際用的是約 40 個字面值散在 190 處 | 改代碼種類的語意時沒有單一真相來源;`CODCode.cs` 的中文說明只覆蓋其中 10 個 | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` | **高** |
| E6.2 | `CTL_SRNO_ID` 的三個常數同樣零引用,而 `CODM016` / `CODM017` 在五個地方寫死 `'0'` `'1'` `'2'` | 同上;而且這三個值的語意只寫在沒人用的常數註解裡 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` | 中 |
| E6.3 | `CODM006_PO` 用 `if (row.CODE_SORT != "C1") return;` 把「列管原因」這個代碼種類寫死在**代碼維護畫面**的 PO 裡 | 換站台或改編號就失效,而且失效時是「保護消失」不是「報錯」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` | **高** |
| E6.4 | `CODM017` 的作廢原因排除清單 `01`–`05` 寫了兩次:一次是 UI 屬性裡的 SQL 片段 `"CODE NOT IN ('01','02','03','04','05')"`,一次是 C# 的五個 `==` 比較 | 兩處要同步改;而且那段 SQL 片段會被送進哪一層、有沒有跳脫,repo 內看不到(`xSimpleSearcher` 無原始碼) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:179` | **高** |
| E6.5 | 共用 PO 的 `GetCancelCdDataSrc` 直接 `WHERE CODE_SORT= '17'` | 「作廢原因是 17 號代碼種類」這件事寫在共用層,COD 這邊完全看不到 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` | 中 |
| E6.6 | `TA.MappingCode` 的欄位是 `public static string` 不是 `const`(`architecture.md §7.2.1`) | 任何一行 `YES_NO.Yes = "1";` 就污染整個 AppDomain,編譯期不擋 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:16` | 中 |
| E6.7 | `CODM009` 同一支檔案內,「正式員工」一處用常數 `EMP_CODE.Staff`、一處用字面值 `"1"` | 讀碼時會以為是兩件事 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:324` 對 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357` | 低 |

### E.7 SQL 層面的髒寫法

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E7.1 | `CODB009` 的 `UPDATE ... WHERE EMP_NO IN (...)` 用 `string.Format` 串接員工代碼清單;陣列為空時組出 `IN ('')` | 沒有跳脫;空勾選時會更新 `EMP_NO` 為空字串的列 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:99-100` | **高** |
| E7.2 | `CODM006` / `CODM007` / `CODM009` / `CODM010` / `CODM016` / `CODM017` 的查詢條件全部用 `'" + value + "'` 串接 | SQL injection / 單引號炸語法。這是全庫的通用寫法(`architecture.md §4.7`),不是單一檔案的問題 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:308`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:188`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:232` | **高** |
| E7.3 | `CODM007` 的主檔 SQL 把 `MOD_FLAG` **`SELECT` 了兩次** | 填進 typed DataSet 時會多一個欄位或直接報錯,取決於框架的 `MissingSchemaAction` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:170-171` | 中 |
| E7.4 | `CODM016.ChkExsitData` 的三個條件中,第二個條件比對的是 `BNG_CTL_SRNO`,綁的參數卻是 `@END_CTL_SRNO` | 複製貼上錯誤。這支方法目前**沒有呼叫端**,所以沒發作 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:774` | 中 |
| E7.5 | 同一支方法內 `@BNG_CTL_SRNO` 宣告成 `SqlDbType.Decimal`、`@END_CTL_SRNO` 宣告成 `SqlDbType.NVarChar`,而兩者在 xsd 都是 `decimal` | 型別不一致,一旦被呼叫會出現隱式轉換或錯誤 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:787-789` | 中 |
| E7.6 | `CTLB014` 與 `CODB902` 的 `INSERT` **都沒有欄位清單** | 表的欄位順序一改,值全部錯位,編譯不會有任何警告 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:138-141` | **高** |
| E7.7 | `CODM036` 的主檔查詢 `WHERE ROWNUM < 3` 沒有 `ORDER BY` | 取到哪兩列由 Oracle 決定 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` | 中 |
| E7.8 | `CODM016` / `CODM017` 用 SQL Server 方言(`[]`、`@`、`GetDate()`、`dbo.`),其餘全模組用 Oracle | 若 `architecture.md §4.6`「執行期 Oracle-only」成立,這兩支執行期就是壞的。**本文無法判定**,標假設 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:75-86`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:747-767` | **高** |

### E.8 位置取參數與其他讀碼陷阱

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | `CTLB014_PO` 兩處用 `Parameters[0].Value` 取 `SOURCETYPE` | UI 端塞參數的順序一改就全錯,而且不會編譯失敗 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:38`、`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:89` | 中 |
| E8.2 | `CODM017` 與 `CODB902` 用 `uoptAction.CheckedIndex` / `uoptExec.CheckedIndex` 當參數值 | 用選項的**位置**當代碼值;Designer 裡調一下順序,作廢就變成取消作廢 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:200`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:70` | **高** |
| E8.3 | `CODM017_PO.Set` 的 `cmdModify` 只在 `act` 是 `"Y"` 或 `"N"` 時才被賦值,之後無條件 `AddInParameter` | 其他值直接 `NullReferenceException`;`catch` 裡的 `tran.Rollback()` 在 `tran` 為 null 時又蓋掉真因 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:180` | **高** |
| E8.4 | `CODM017_PO.Set` 綁了 `@CTL_SRNO_ID` 參數,但兩段 UPDATE 都把該欄寫死,SQL 裡沒有這個參數 | 多綁一個沒用的參數;SQL Server 會忽略,但讀碼者會以為值是動態的 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:136` | 低 |
| E8.5 | `CODB902` 在「EMAIL 未設定」時 `return model;`,此時交易已開啟但沒有 `Commit` 也沒有 `Rollback` | 只靠 `finally` 的 `Dispose` 收尾;行為取決於框架實作 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101` | 中 |
| E8.6 | `CODB902` 產生的明文密碼會出現在寄出的信件內文,寄失敗時**直接顯示在操作者畫面上** | 明文密碼經過 EMAIL 與畫面兩條路徑 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:126`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:134` | **高** |
| E8.7 | `CODM016` 的「只能改最後一批」用的是進入修改模式時**快取的布林值**,不是存檔當下重查 | 畫面停留期間別人新增了一批,這裡不會知道 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:74-75` | 中 |
| E8.8 | `CODM016` 查詢條件的判斷式寫反:`if (custFUND_ID_0.Value == "")` 走 `LIKE`、`else` 走 `=` | 空白時組出 `LIKE ''`(只比對空字串),等於查不到任何資料 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:82-89` | 中 |
| E8.9 | `CODM009` 的 `CHECK_ID_EXIST` 判斷 `Convert.ToInt32(i) == 1` 而不是 `> 0` | 已經有兩筆以上重複時反而放行 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:579` | 中 |
| E8.10 | `ucCOD006` 送出參數名 `"Dis"`,共用 PO 找 `"DIS"` | 若 `FindByName` 大小寫敏感,排除條件會被靜默丟棄(**假設**,`FindByName` 無原始碼) | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:109` 對 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:188` | 中 |
| E8.11 | 共用 PO 的 `GetCodeSortForCODM006` 用 `if (strID == "CODM006") ... else ...`,`else` 涵蓋「沒帶 `ProgramID`」與「帶錯值」 | 任何新的呼叫端忘記設 `ProgramID`,會**靜默拿到 `CODM007` 的清單** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:634-637` | 中 |
| E8.12 | `CODB000` 的 UI / PO / Ctl 三個檔具備反編譯輸出的特徵(無 Designer 分離、`appearance2` 式命名、`new string[0]`、無中文註解) | **假設**:這一組原始碼曾遺失,現行版本由 DLL 反編譯還原。若成立,改這三個檔要特別小心行為差異 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:143-281` | 中 |
| E8.13 | `CODB009` 的 `AGENT_ID` 下拉被強制鎖成 `"0"` 且永遠 disabled | 這支批次只能掛區分碼 `0` 的機構,畫面上看不出來〔客戶特定〕 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:55-57` | 中 |
| E8.14 | `CODM010` 的員工 Searcher 永遠帶 `IS_COMP_FEAT = "N"` | 公單員工挑不到,無提示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:431` | 低 |

### E.9 標「假設」的地方一覽

| # | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| A1 | 員工資料由外部 eHR 定期匯入,`CODM009` 是人工補正入口 | `DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 做同樣加欄,但兩表在 `.cs` 零引用 | 問 DBA 或找 ETL 排程 |
| A2 | 代碼三張表是「建置期一次性」設定,不是日常大量作業 | 查詢條件極簡,無日期區間、無狀態篩選 | 問使用者 |
| A3 | `CODM016` / `CODM017` 的 SQL Server 方言在執行期會不會壞 | `architecture.md §4.6` 說執行期 Oracle-only,但這兩支確實在版控裡且有完整六層 | 實機測一次 |
| A4 | `COD007A` 的級距代碼由版控外的 SP 或報表使用 | 本模組外零引用,但表有完整維護畫面與四眼 | 查資料庫的相依 |
| A5 | `COD040A` 是什麼業務的級距 | **完全查不到**,本文不猜 | 問使用者或查資料庫內容 |
| A6 | `CODB000` / `CODB901` / `CODB902` 這幾支的原始碼曾遺失、由反編譯還原 | 三個檔的命名與結構特徵(E8.12) | 查版控歷史 |
| A7 / A8 | `ucEmployeeData` 回傳的 `OUTBOUND` 已被轉成數字(所以 `CODB901` 的 `Convert.ToBoolean` 不會炸);`FindByName` 大小寫敏感(所以 `Dis` 排除條件失效) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:361` 有 `CASE ... THEN 1 ELSE 0 END`;`Dis` 兩邊字面不同且沒有正規化 | 實機測一次 |
| A9 / A10 | `CODM036` 的下限欄由 `LevelGridUtility` 自動接續上一列的上限;全模組的權限由 PTPF 平台功能權限決定 | 下限欄被設成 `NoEdit` 且控件建構子帶了上下界;程式內零權限判斷(`architecture.md §3.7`) | 實機測 / 查平台設定 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純讀碼彙整,涵蓋 12 支畫面 + `CTLB014`、6 張母體表 + `COD017` / `COD040A` / `CTL014`,重點在 §2.4 的代碼字典對應與附錄 C 的代碼值清單 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 78 · 圖 5 · 表格 73 · 程式錨點 722 · § 連結 36 · 引用檢查：畫面 15（缺 0） · Table 14（缺 0） · 結果集 4（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
