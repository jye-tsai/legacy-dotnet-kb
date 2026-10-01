<!-- 由 tools/build_copilot_kb.py 從 modules/crm.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS CRM 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最反直覺的事)、§4–§7 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表中文名與少數彈出視窗標題**推測**。與 CAS 不同的是 CRM 有 11 個報表中文名寫在程式裡,推測的把握度比 CAS 高一截(§0.1)。 ⚠ **〔客戶特定〕**:`USAGE = '1'`、`SAL_CD` 的 `A` / `B` / `C` / `D` 分級、`CODE_SORT` 的 `P5` / `1C` / `11`、部門代碼補 `'01'` 的規則都是本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`CRM003A` 同時服務 CAS 與 TMK,`CRM001A` / `CRM002A` / `CRM007A` 被 `Dev/Common` 的共用 PO 讀,`CRM006A` / `CRM0061A` 被 TMK 與 OFD 讀(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。與 CAS 的交界寫在 `cas.md §8`,本文 §8 從 CRM 這側寫,兩邊結論一致。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CRM 管「還沒成為客戶的人」與「該派誰去接觸他」——潛在客戶的聯絡紀錄、索取資料紀錄,以及把既有受益人名單依規則分配給直銷業務員去追蹤的整套指派作業。**

推測依據四條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 報表中文名(最強的一條) | 「指派單位明細表」「指派業務員明細表」「指派名單追蹤彙總表-By單位別」「指派名單追蹤明細表-By業務員別」「指派名單聯絡結果統計表」「客戶通話記錄明細表」「客服潛在客戶索取資料明細表」 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:221`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:145`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:196-202`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:151`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:122-126` |
| 欄位中文名 | `CRM003A` 是「潛在客戶序號」「潛在客戶姓名」「拒絕電訪行銷」;`CRM007A` 是「分配序號」「本次指派單位代碼」「本次指派業務代碼」「再聯絡日期」「聯絡結果代碼」「有無意願申購」 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |
| 畫面上的中文標籤 | 「規則六:依條件篩選客戶,手動上傳」「備註:依條件篩選的客戶無須『產生名單』,僅須執行『上傳名單』」「已指派歸類(轉出)」「已指派歸類(轉入)」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.Designer.cs:207`、`:220`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.Designer.cs:475`、`:527` |
| 彈出視窗標題 | 「員工銷售機構權限明細設定」「客戶歷史資料」「潛在客戶資料選取視窗」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001p0.Designer.cs:367`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003p0.Designer.cs:281`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003p1.Designer.cs:285` |

「CRM」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「潛在客戶與直銷指派」描述它的業務範圍。

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 查詢權限設定 | 哪個員工可以查哪些銷售機構、以及該機構底下哪些員工的資料 | `CRMM001` | `CRM001A` + `CRM002A` |
| B 部門歸屬設定 | 把銷售機構歸類到「部門歸屬類別」,給指派作業當分群依據 | `CRMM002` | `CRM008A` |
| C 潛在客戶 | 潛在客戶主檔 + 每一次通話紀錄 + 每一次索取資料紀錄;重複客戶合併 | `CRMM003`、`CRMB005`、`CRMR007`、`CRMR008` | `CRM003A` + `CRM006A` / `CRM0061A` / `CRM004A` / `CRM0041A` |
| D 直銷指派 | 依規則產生「該追的客戶名單」,指派給單位 / 業務員,記錄聯絡結果與再聯絡日 | `CRMB001`–`CRMB004`、`CRMI001`、`CRMR001`–`CRMR006` | `CRM007A` |
| E 客戶分級參數 | 客戶等級的庫存級距、應親訪 / 應電訪次數、計算頻率 | `CRMM004` | `CRM004` |

### 0.2 這模組最反直覺的三件事

**(1) 掃描母體少報了四張表。**`docs/_candidates/crm.md` 第 2 節只列 6 張表,實際上本模組動到的實體表是 **10 張**:母體漏了 `CRM001A`、`CRM002A`、`CRM008A`、`CRM007A`。

原因是掃描器的主檔正規式只認 `this.MasterTable = new xTableMapping(...)` 這一種寫法,而:

| 漏掉的表 | 為什麼漏 | 錨點 |
|---|---|---|
| `CRM001A` `CRM002A` | `CRMM001_PO` 繼承 `BaseMultiRowEVADaoPO`,主檔是 `List`,寫法是 `this.MasterTable.Add(...)` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `CRM008A` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:40` |
| `CRM007A` | `CRMI001_PO` / `CRMB001_PO`–`CRMB004_PO` 都是裸 DAO,根本沒有 `xTableMapping`,表名只出現在 SQL 字串裡 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:80`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:107` |

這正是「`CRMM001` 與 `CRMM002` 沒有宣告主明細」的答案:**它們有主檔,只是用多筆版的寫法宣告,而且沒有明細概念**(見 §2.1、§4.1、§4.2)。

**(2) `CRMB001` 的「產生名單」按鈕目前不會產生任何名單。**唯一會下 SQL 的那段(呼叫 `S_TA_CRMB001_EXCUTE`)整段被註解掉了(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`),剩下的只有「從 CSV 上傳指派名單」那條路。按下執行鈕時,`Execute` 走完整個 try 區塊卻一行 SQL 都沒下,而且 `Result` 在開頭被 `Clear()` 之後沒有再塞任何一列(`:77`)。**畫面不會報錯,也不會有成功訊息。**這是本模組最會咬人的一條(附錄 E.1)。

**(3) `CRMM003` 的兩張索取明細永遠查不出資料。**`CRM004A` 與 `CRM0041A` 的取數 SQL 被硬加了 `WHERE 1=2`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454`)。畫面上「索取資料」頁籤在維護模式下一定是空的,實際內容改由 `GetHistory_Call_Req` 另外撈進 `CRM004A_HIS`(§4.3)。

### 0.3 不管什麼

以下**不在** CRM 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(正式客戶)基本資料 | BMS | `BMS001A_V01` 只被 join 取姓名 / 地址 / 電話,從不寫入;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:76-81` |
| 員工主檔、部門、離職日 | COD / OFD | `COD009` 與 `OFD002` 全部是 `LEFT JOIN`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:301-305` |
| 銷售機構主檔 | OFD | `OFD068A` 只被 join 取簡稱,`CRMM001` 的機構清單直接 `SELECT ... FROM OFD068A`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:318-324` |
| 直銷業務員的職級與所屬業務部門 | SAL(版控外) | `SAL051` 只被 `LEFT JOIN` 取 `SAL_CD` 與部門;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:302-303` |
| 電訪(OutBound)本身的作業 | TMK | `TMK001A` / `TMK_BF_V` 只被 join 取電訪人員;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:638-649` |
| 申購 / 贖回交易與庫存金額怎麼算 | OFD / EC | `CRM007A` 的 `TOT_ALLOT_AMT` / `BAL_AMT` 是被寫進來的結果,CRM 內沒有任何一支程式計算它們 |
| 「規則一~規則五」到底怎麼篩客戶 | **不明,在版控外的 SP** | 唯一的呼叫點被註解(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-205`),SP 本體不在 repo 內。**假設**:規則邏輯全寫在 `S_TA_CRMB001_EXCUTE` 裡,依據是被註解的參數只有結算日與規則代碼兩個 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 客服 / 電訪人員 | 建立與維護潛在客戶、記錄每通電話與每次索取資料 | `CRM006A_HIS` 的 `CREATEID` 欄位 Caption 直接寫「客服」;`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| 直銷主管(`SAL_CD` = `A`) | 查詢名單時**必須**指定轉出單位;可以自由改部門與業務員欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:198-201`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348-358` |
| 組主管(`SAL_CD` = `B`) | 同上,部門與業務員欄位解鎖 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348` |
| 直銷業務員(`SAL_CD` = `C`) | 部門與業務員欄位鎖死成自己,只看得到分配給自己的名單 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:98` |
| 直銷助理(`SAL_CD` = `D`) | 在共用的業務員下拉可被排除 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:280-282` |
| 名單管理人員 | 執行產生 / 刪除名單、上傳 CSV 名單、跨單位與跨業務員調撥 | `CRMB001`、`CRMB002`、`CRMB003` |
| 系統管理 | 設定誰能查誰(`CRMM001`)、機構歸屬分類(`CRMM002`)、客戶分級參數(`CRMM004`) | 三支都是標準四眼維護畫面 |
| 覆核者 | 對 M 畫面做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |

**權限不在程式碼裡的部分比 CAS 多。**本模組的「可見範圍」有兩套機制疊在一起:功能權限由 PTPF 平台庫決定(`architecture.md §3.7`),資料可見範圍由 `CRM001A` / `CRM002A` 這兩張表加上 `F_TA_GET_EMPS` 這支版控外的 TVF 決定(§5.3、§8.2)。

### 0.5 全域開關

repo 內**沒有**任何 CRM 專屬的設定檔開關。`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:54`(`CRMM001`)、`:61`(`CRMM002`)、`:69`(`CRMM003`)、`:76`(`CRMM004`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:55`、`:62`、`:70`、`:77` |
| `formstyle` | `CRMB001`–`CRMB005` 與 `CRMI001` 宣告為 `OneStep`;報表側全部 `Report` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`、`:48`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/App.config:15` |

四件要記住的:

- **四支 M 畫面一個都沒宣告 `detailtable`**,但 `CRMM001` 與 `CRMM003` 的 PO 確實有多張表(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:67-71`)。**設定檔與程式不一致,以程式為準。**

- **`CRMM004` 的 `mastertable` 寫的是 `CRMM004` 不是 `CRM004`。**設定檔填的是 typed DataSet 的表名,PO 那邊才是真正的 DB 表名 `CRM004`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:44`)。這是全庫少見的 vdb 表名與 db 表名不同的例子,也是掃描母體把 `CRM004` 報成「0 欄位」的原因(§2.3)。

- **`CRMM001` 的 `pkey` 只寫了 `EMP_NO`**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:54`),而 xsd 的 PK 是 `EMP_NO` + `AGENT_ID` + `AGENT_CODE` 三欄(`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd`)。PO 那邊宣告的 `MasterPKey` 也只有 `EMP_NO`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:51`)——這是刻意的,因為多筆版把「同一個員工的所有列」當成一批(§4.1)。

- `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:80` 宣告 `.NETFramework,Version=v4.8`,而多支 PO 頂端留著 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡(例 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:5`)——與 CAS 同一批升版作業。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CRM 模組全景：設定、潛在客戶、直銷指派、報表四條線，以及五張被別的模組讀的表
圖中文字:① 設定線：誰能查誰、機構怎麼歸類、客戶怎麼分級 / CRMM001 / 查詢權限 CRM001A+CRM002A / CRMM002 / 機構部門歸屬 CRM008A / CRMM004 / 客戶分級參數 CRM004 / COD009 OFD002 OFD068A / 員工／部門／機構 外部 / ② 潛在客戶線（客服） / CRMM003 / 潛在客戶 CRM003A 一主四明細 / CRM003A〔共用〕 / USAGE=1 CRM／3 CAS / CRMB005 / 重複客戶合併 走 SP / CRMR007 CRMR008 / 通話／索取明細表 / ③ 直銷指派線（與②完全沒有資料關聯） / CRMB001 / 產生／刪除／上傳 CRM007A / CRMB002 / 單位調撥 / CRMB003 / 業務員指派 / CRMB004 / 聯絡結果登錄 / CRMI001 / 名單查詢 唯讀 / ④ 報表（資料全在版控外的 SP） / CRMR001 CRMR002 / 指派單位／業務員明細 / CRMR003 CRMR004 CRMR005 / 追蹤彙總／明細 / CRMR006 / 聯絡結果三式 / 10 支 SP 不在版控 / S_TA_CRMnnn_* / ⑤ 對外：本模組維護、別人使用 / CRM001A CRM002A / BasicCRM_PO／CLS／DSM／OFD / CRM007A / 共用控件與下拉的資料來源 / CRM006A CRM0061A / TMK／OFD 唯讀 / CRM003A / CAS／TMK
```

*圖:圖 1 CRM 全景。橘框=本模組的維護／批次入口；灰虛框=被別的模組讀的表；黑框=無原始碼的外部來源；橘虛框=含寫死值或行為會咬人〔客戶特定〕。②與③兩條線之間沒有任何欄位、join 或程式呼叫關係。*

看圖的四個重點:

1. **C 線(潛在客戶)與 D 線(直銷指派)之間沒有任何程式或資料關聯。**`CRM003A` 系列與 `CRM007A` 沒有共同欄位、沒有 join、沒有互相呼叫。它們被放在同一個模組裡是歷史結果,不是設計。要驗證:全庫搜 `CRM003A` 與 `CRM007A` 同時出現的 SQL,零命中。

2. **A 線(`CRMM001`)不是給 CRM 自己用的。**`CRM001A` / `CRM002A` 在 CRM 內部只被 `CRMM001` 自己維護,真正讀它的是共用 PO `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:294-305`,而那支被 CLS / DSM / CRM 的報表共用(§8.2)。**改 `CRMM001` 的資料,會改到別的模組畫面上看得到什麼。**

3. **報表那一排全部靠版控外的 SP。**8 支 R 畫面加上 `CRMB001` 的「產出客戶名單」,共 10 支 SP(`S_TA_CRMR001_GET`…`S_TA_CRMR008_GET_2`、`S_TA_CRMB001_GET`),一支都不在版控內(附錄 B)。

4. **只有 `CRMB002` / `CRMB003` / `CRMB004` 會直接 UPDATE 四眼欄位以外的業務欄位,而且完全繞過 EVA 引擎。**三支都是手寫 `UPDATE CRM007A SET ...`(§6.3)。

### 1.2 資料表關係

見 §2 節首的圖。要記住的:

- **`CRM003A` 是唯一的一主四明細。**四張明細其實是兩組:通話(`CRM006A` 表頭 + `CRM0061A` 種類明細)與索取(`CRM004A` 表頭 + `CRM0041A` 種類明細),兩組結構完全對稱(§2.1)。

- **`CRM001A` 與 `CRM002A` 是 1:N,但在 PO 眼中兩張都是「主檔」。**多筆版沒有明細概念,所以 `CRM002A` 的新增是手寫 INSERT 補的(§4.1)。

- **`CRM007A` 完全獨立**,沒有明細,PK 是 `ASSIGN_NO` + `BF_NO`。

- **`CRM004` 是參數表**,PK 只有 `CUS_LV`,全庫只有 `CRMM004` 一支畫面碰它。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接 `new` 一個 `_Pxy` 或用既有的 `FormProxy` 打過去 | 對話框(不是訊息清單) |
| 4 主檔欄位回填明細 | `CRMM002` 的 `SetMasterToDetail()`;`CRMM001` / `CRMM003` 在 `GetPageValue()` 內一併做 | 不會失敗,但漏欄位會讓明細 PK 是空的 |
| 5 PO 的 `Before*` | `BeforeAdd` 取號、`BeforeSelect` / `BeforeGetMaintainData` 換 SQL、`BeforeUpdate` 做區間重疊檢查 | `args.Cancel = true` + `CancelMsg`,或例外 → 整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `After*` | 只有 `CRMM003` 有(8 個掛點,全是跳號一覽表) | `throw` → 整筆回滾 |

**與 CAS 的差別有兩點**:(a) CRM 有畫面在 `BeforeAdd` / `BeforeUpdate` 用 `args.Cancel + args.CancelMsg` 擋(`CRMM004`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:100-104`),這是**伺服器端**的卡控,CAS 全模組沒有;(b) `CRMM001_PO` 覆寫了 `Add` / `ApproveDelete` / `IsChangedByData` 三個基底方法,直接改寫四眼引擎的行為(§4.1)。

### 1.4 批次 / 報表資料流

見 §6 節首的圖(§7 沒有圖,報表流程與 CAS 同構)。四件事:

- **五支 B 畫面沒有一支是排程。**全部是 `formstyle="OneStep"` 的使用者按鈕觸發(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`),`Dev/` 下也沒有任何 CRM 的 WindowsService。

- **`CRMB002` / `CRMB003` / `CRMB004` 的「執行」是逐列 UPDATE**,一列一個 `DbCommand`,同一個交易內跑完再 commit(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:202-234`)。

- **報表是兩條獨立往返**:`GetReportData` 拿資料、`GetReportObject` 拿 `.rpt` 檔的 byte,後者的類別名由用戶端傳過來(與 `architecture.md §6.5` 描述一致)。

- **報表 PO 全部把 SP 包在明確交易裡**(`m_db.BeginTransaction()` … `tran.Commit()`),這點與 CAS 不同,CAS 的報表 PO 沒有交易(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54`、`:74`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,所以以下是**推測**的作業順序,依據是資料相依:某張表要有資料,前一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期 | 系統管理 | 設定客戶分級參數(級距、應訪次數、頻率) | `CRMM004` | — |
| 建置期 | 系統管理 | 設定銷售機構的部門歸屬分類 | `CRMM002` | 機構要先在 `OFD068A` 存在 |
| 建置期 / 人員異動時 | 系統管理 | 設定員工的查詢權限(可查哪些機構、哪些人) | `CRMM001` | 員工要先在 `COD009` 存在 |
| 每期開始 | 名單管理 | 依規則產生直銷分配客戶名單,或上傳 CSV 名單 | `CRMB001` | 該結算日所有基金都要已結帳 |
| 名單產生後 | 名單管理 | 把名單在單位之間調撥 | `CRMB002` | 名單要先存在 |
| 名單產生後 | 主管 | 把名單指派到業務員 | `CRMB003` | 名單要先存在 |
| 追蹤期間 | 業務員 | 填聯絡結果、再聯絡日期 | `CRMB004` | 名單要先指派到自己 |
| 追蹤期間 | 業務員 / 主管 | 查自己(或所屬單位)的名單 | `CRMI001` | `CRM001A` / `CRM002A` 要先設好 |
| 平時 | 客服 | 建立 / 維護潛在客戶,記錄通話與索取資料 | `CRMM003` | — |
| 不定期 | 客服主管 | 合併重複的潛在客戶 | `CRMB005` | 潛在客戶要先存在 |
| 期末 | 全體 | 出各式指派與追蹤報表、潛在客戶報表 | `CRMR001`–`CRMR008` | 版控外的 SP 決定 |

**假設**:「期」的長度。依據是 `CRM007A` 的 PK 用 `ASSIGN_NO`(分配序號)而不是日期,而三支 B 畫面的預設值都取「最新一期」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:368-373`)。實際週期要問使用者。

## 2. 資料模型

```text
[圖] CRM 十張表的主明細關係、主鍵組成，以及外部唯讀表
圖中文字:CRMM003 的一主四明細（兩組對稱結構） / CRM003A〔共用〕 / PK PR_NO · 69 欄 / CRM006A / +CALLIN_DATE+SRNO / CRM0061A / 再加 CALLIN_CODE / CRM004A / +REQ_DATE+SRNO / CRM0041A / 再加 REQ_DATA_CODE / CRM006A_HIS CRM004A_HIS / 結果集 非實體表 / CRMM001 多筆版：兩張表都算主檔，沒有明細概念 / CRM001A / PK 員工+機構別+機構 / CRM002A / 再加 INQ_EMP_NO（ALL） / CRM001A_OPTION / 勾選用 來源 OFD068A / CRM002A_OPTION / 勾選用 來源 COD009 / 單表：沒有明細也沒有主明細關係 / CRM008A / PK 四欄 · CRMM002 / CRM004 / PK CUS_LV · vdb 名 CRMM004 / CRM007A / PK ASSIGN_NO+BF_NO / 無 M 畫面 / 四眼欄位有但不走四眼 / 外部唯讀（join 進來，不屬本模組） / COD009 COD006A / 員工／代碼說明 / OFD002 OFD068A / 部門／銷售機構 / OFD081A OFD081V / 基金 兩支各用一個 / BMS001A_V01 TMK_BF_V / SAL051 OFD303A CTL014
```

*圖:圖 2 資料模型。橘框=主檔；橘虛框=取數被限制或不走四眼；灰虛框=非實體結果集；黑框=外部唯讀表。實線箭頭=主明細（同一次 EVA 一起送審）；虛線=同一支畫面內的弱關聯。CRM004A／CRM0041A 的取數被加了 WHERE 1=2，維護頁永遠查不到。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`),但 CRM 這邊有兩種寫法,掃描器只認得其中一種(§0.2)。

| 畫面 | PO 基底 | 主檔宣告 | 明細宣告 | 錨點 |
|---|---|---|---|---|
| `CRMM001` | `BaseMultiRowEVADaoPO` | `MasterTable.Add("CRM001A")` **與** `MasterTable.Add("CRM002A")` | **無此概念** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `CRMM002` | `BaseMultiRowEVADaoPO` | `MasterTable.Add("CRM008A")` | **無此概念** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:40` |
| `CRMM003` | `BaseEVADaoPO` | `CRM003A` | `CRM006A`、`CRM0061A`、`CRM004A`、`CRM0041A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:65-71` |
| `CRMM004` | `BaseEVADaoPO` | `CRM004`(vdb 表名是 `CRMM004`) | **無** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:44` |
| `CRMI001` | **無基底**(裸 DAO) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:36`、`:44`(唯一一行是註解) |
| `CRMB001` | `BaseEVADaoPO`(但完全沒用到四眼) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:36`、`:48-50` |
| `CRMB002`–`CRMB005` | **無基底**(裸 DAO) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:36` |

三件要記住的:

1. **多筆版沒有明細表。**`BaseMultiRowEVADaoPO` 的 `MasterTable` 是 `List<xTableMapping>`,`DetailTable` 這個概念不存在(`architecture.md §3.9`)。所以 `CRMM001` 把 `CRM001A` 與 `CRM002A` **兩張都登記成主檔**,靠 `MasterPKey` 只填 `EMP_NO` 來讓「同一員工的所有列」被當成一批處理(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:51`)。

2. **`CRMM001` 為此付出三個覆寫的代價**(§4.1):`Add` 自己補 `CRM002A` 的 INSERT、`IsChangedByData` 只對第一張表做樂觀鎖、`ApproveDelete` 自己判存在性避免跑多次。三個覆寫的註解都直白寫了原因,是全模組最誠實的一段程式碼。

3. **`CRMM003_PO` 有兩行被註解的明細宣告**:`CRM0061A_HIS` 與 `CRM0041A_HIS`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:69`、`:72`)。這兩張「歷史表」在現行程式裡完全不存在,歷史資料改用 `CRM006A_HIS` / `CRM004A_HIS` 這兩個**非實體結果集**承接(§2.3)。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。CRM 這邊**四支 M 畫面有三支不一致**。

| 表 | 主鍵(xsd) | 主鍵(`App.config`) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `CRM001A` | `EMP_NO` + `AGENT_ID` + `AGENT_CODE` | `EMP_NO` | ✘(設定檔少兩欄) | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd` |
| `CRM002A` | `EMP_NO` + `AGENT_ID` + `AGENT_CODE` + `INQ_EMP_NO` | (未宣告) | — | 同上 |
| `CRM008A` | `AGENT_BELONG_TYPE` + `AGENT_TYPE` + `AGENT_ID` + `AGENT_CODE` | 同左,四欄齊 | ✔ | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM002Model.xsd` |
| `CRM003A` | `PR_NO` | `PR_NO` | ✔ | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| `CRM006A` | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` | (未宣告) | — | 同上 |
| `CRM0061A` | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` + `CALLIN_CODE` | (未宣告) | — | 同上 |
| `CRM004A` | `PR_NO` + `REQ_DATE` + `REQ_SRNO` | (未宣告) | — | 同上 |
| `CRM0041A` | `PR_NO` + `REQ_DATE` + `REQ_SRNO` + `REQ_DATA_CODE` | (未宣告) | — | 同上 |
| `CRM004` | `CUS_LV` | `CUS_LV`(但表名寫成 `CRMM004`) | ✔(表名不同) | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM004Model.xsd` |
| `CRM007A` | `ASSIGN_NO` + `BF_NO` | (無 M 畫面,沒有設定) | — | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |

**`CRM001A` 的 `pkey` 只寫 `EMP_NO` 是刻意的,不是漏。**多筆版用 `MasterPKey` 定義「一批」的範圍,而 `IsExistByMasterPK` 就是靠它判斷(`architecture.md §3.9`);`CRMM001_PO.ApproveDelete` 明確用它來避免同一批跑多次(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:165`)。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 中文名 | 說明 |
|---|---|---|---|
| `CRM003A` | ✔ | **全部有** | 最完整的一張,連 `DATAFLAG` 都有「資料異動碼」 |
| `CRM006A` `CRM0061A` `CRM004A` `CRM0041A` | ✔ | **全部有** | 四張明細一致 |
| `CRM001A` `CRM002A` | ✔ | **全部有** | 同上 |
| `CRM008A` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `CRM004` | ✔ | **一個都沒有** | 同上 |
| `CRM007A` | ✔ | **全部有,但有一個是錯的** | `STATUS` 的 Caption 寫成「資料識別碼」(那是 `DATAID` 的名字);`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |

**結論:10 張表全部有完整四眼欄位,而且 8 張有中文名——比 CAS(10 張只有 2 張有)好得多。**但要注意兩個共通的抄寫錯:`REJECTDATE` 的 Caption 在 `CRMM003Model.xsd` 的五張表裡全部寫成「資料退回**者**」(應為「資料退回日期」),`CRMM001Model.xsd` 那兩張則是對的。

`DATAFLAG` 每張表都有,型別一律 `xs:base64Binary`,是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

以下中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**。空白代表該 xsd 沒有填。四眼的 13 欄 + `DATAID` + `DATAFLAG` 每張表都有,除特別註記外不重複列。

#### `CRM003A` — 潛在客戶主檔(69 欄,`CRMM003` 主檔)〔共用〕

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK,取號見 §4.3 |
| `USAGE` | 用途別 | string(6) | **切 CRM / CAS 兩個世界的那一欄**(§8.1) |
| `BF_NO` | 受益人戶號 | decimal | 已開戶才有 |
| `EMP_NO1` | 業務員員工代碼 | string(10) |  |
| `ID_NO` | 統一編號 | string(10) |  |
| `PR_NAME` | 潛在客戶姓名 | string(100) | 走 `AddNVarCharColumns` 宣告為 NVARCHAR |
| `HM_TEL_AREA` | 公司電話區域碼 | string(4) | **Caption 抄錯**,實際是住家 |
| `HM_TEL` | 住家電話 | string(20) |  |
| `OF_TEL_AREA` / `OF_TEL` | 公司電話區域碼 / 公司電話 | string(4) / string(20) |  |
| `AUTO_FAX_YN` | 自動傳真電話否 | string(6) | 對應 UI 已註解 |
| `FAX_TEL_AREA` / `FAX_TEL` | 傳真電話區域碼 / 傳真電話 | string(4) / string(20) |  |
| `CELL_PHONE` | 行動電話 | string(20) |  |
| `EMAIL` | (無中文名) | string(60) | UI 有格式檢核 |
| `CNT_PERSON` | 聯絡人 | string(24) |  |
| `ADDR_CODE1` … `MAIL_FLOOR` | 通訊地址區分碼 / 郵遞區號 / 通訊中文地址 / 縣市 / 行政區域 / 里名 / 鄰名 / 路名 / 幾巷 / 幾弄 / 起號 / 迄號 / 之幾 / (樓層無名) | string | 共 15 欄,`MAIL_ADDR` 走 NVARCHAR;**14 欄的回填程式全被註解**(§4.3) |
| `MEMO` | 備註說明 | string(500) |  |
| `CUST_CLASS` / `CUST_CLASS1` / `CUST_CLASS2` | 客戶等級代碼 / 總行等級代碼 / 分行等級代碼 | string(7) |  |
| `BF_SOURCE_CODE` | 潛在客戶來源代碼 | string(7) |  |
| `DES_MAKER` | 決策者 | string(24) |  |
| `DM_CODE` / `DM_EMAIL` | DM寄發碼 / 寄發廣告EMAIL | string(6) | **2020-03-30 起兩個下拉都被移除**(§4.3) |
| `REJ_SELL_CHK` / `REJ_SELL_DOC` / `REJ_SELL_WEB` / `REJ_SELL_PHONE` | 拒絕行銷 / 拒絕書面行銷 / 拒絕網路行銷 / 拒絕電訪行銷 | string(6) | **四個勾選框在編輯模式一律 `Enabled = false`**(§4.3) |
| `CUST_STYLE` / `CUST_STYLE_DESC` | (無中文名) | string(7) / string(60) |  |
| `AREA_CODE` / `DEPT_CODE` | 區域別 / 組別 | string(6) |  |
| `SOP_CLASS` | SOP等級代碼 | string(7) |  |
| `POSITION_DESC` / `SOURCE_DESC` | 職稱說明 / 客戶來源說明 | string(20) |  |
| `CUST_TYPE` | 客戶類別代碼 | string |  |
| `SEND_INFO_YN` | 發文通知 | string(6) |  |
| `TEL_STAFF` / `OUTBND_CODE` / `OUTBND_DESCRP` | 電訪人員 / OutBound項目 / OutBound項目說明 | string | **不是 `CRM003A` 的實體欄位**,是 join `TMK_BF_V` 帶回來的(§4.3) |

#### `CRM006A` — 通話紀錄表頭(21 欄,`CRMM003` 明細)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK |
| `CALLIN_DATE` | 通話日期 | string(8) | PK,`YYYYMMDD` 字串 |
| `CALLIN_SRNO` | 批次 | decimal | PK,同日第幾通 |
| `BF_NO` | 受益人戶號 | decimal |  |
| `READY_YN` | 完成碼 | string(6) |  |
| `COMMENT1` | 通話記錄備註 | string(500) |  |

#### `CRM0061A` — 通話種類明細(20 欄,`CRMM003` 明細)

比 `CRM006A` 多一欄 `CALLIN_CODE`(通話種類代碼小類,`string(7)`,入 PK),其餘同上但沒有 `READY_YN` / `COMMENT1`。**一通電話可以勾多個種類,所以才拆表。**

#### `CRM004A` — 索取資料表頭(27 欄,`CRMM003` 明細)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK |
| `REQ_DATE` | 索取日期 | string(8) | PK |
| `REQ_SRNO` | 批次 | decimal | PK |
| `DOC_DVLY_ID` | 寄送方式 | string(6) |  |
| `POST_WAY` | 郵寄方式 | string(6) |  |
| `REQ_QTY` | 需求數量 | decimal |  |
| `FAX_TEL_AREA` / `FAX_TEL` / `EMAIL` | 傳真電話區域碼 / 傳真電話 / (無中文名) | string |  |
| `LABEL_PRINT` | 標籤列印碼 | string(6) |  |
| `PRINT_YN` | 標籤列印否 | string(6) | **由 `CRMR008` 的列印動作寫回**(§7.4) |

#### `CRM0041A` — 索取種類明細(20 欄,`CRMM003` 明細)

比 `CRM004A` 少掉全部業務欄位,多一欄 `REQ_DATA_CODE`(需求資料種類代碼,`string(7)`,入 PK)。與通話那組完全對稱。

#### `CRM001A` — 員工可查機構(20 欄,`CRMM001` 主檔之一)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `EMP_NO` | 員工代碼 | string(10) | PK;`MasterPKey` 只有這一欄 |
| `AGENT_ID` | 銷售機構別 | string(6) | PK |
| `AGENT_CODE` | 銷售機構代碼 | string(9) | PK |
| `EMP_NAME` | 員工姓名 | string | join `COD009` 帶回,非實體欄位 |
| `AGENT_SHNM` | 銷售機構名稱 | string | join `OFD068A` 帶回,非實體欄位 |

#### `CRM002A` — 員工可查員工(19 欄,`CRMM001` 主檔之二)

同 `CRM001A` 的三個 PK 欄再加 `INQ_EMP_NO`(員工代碼,`string(10)`)。**注意 Caption 是對調的**:`EMP_NO` 的 Caption 寫「可查詢員工代碼」、`INQ_EMP_NO` 的 Caption 寫「員工代碼」,但程式裡 `EMP_NO` 是「擁有權限的人」、`INQ_EMP_NO` 是「被查的人」(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:294-305` 的 `A.EMP_NO = '{0}'` 配 `B.INQ_EMP_NO`)。**以程式為準,Caption 這兩欄反了。**

`INQ_EMP_NO` 有一個保留值 **`'ALL'`**,代表「該機構底下全部員工都看得到」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:228`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:488`)。

#### `CRM008A` — 銷售機構部門歸屬(21 欄,`CRMM002` 主檔)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `AGENT_BELONG_TYPE` | 部門歸屬種類 | string | PK;下拉來源代碼 `445` |
| `AGENT_TYPE` | 部門歸屬類別代碼 | string | PK |
| `AGENT_TYPE_NM` | 部門歸屬類別名稱 | string | 由類別代碼的顯示文字自動帶入 |
| `AGENT_ID` | 銷售機構區分碼 | string | PK;下拉來源代碼 `062` |
| `AGENT_CODE` | 銷售機構代碼 | string | PK;有 `'ALL'` 保留值 |
| `AGENT_SHNM` | 銷售機構中文簡稱 | string | join `OFD068A` 帶回,非實體欄位 |

#### `CRM004` — 客戶分級參數(34 欄,`CRMM004` 主檔;vdb 表名 `CRMM004`)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `CUS_LV` | 客戶等級 | string | PK |
| `HASBF_NO` | 是否開戶 | string | `Y` / `N` |
| `HAS_MF` / `HAS_N_MF` / `HAS_PER` | (無中文名) | int | 0/1 旗標:有無貨幣型 / 非貨幣型 / 比率條件 |
| `MF_AUM_S` / `MF_AUM_E` | 貨幣結餘起 / 迄(萬元) | int | **`-1` 是「未填」的哨兵值**(§4.4) |
| `N_MF_AUM_S` / `N_MF_AUM_E` | 非貨幣結餘起 / 迄(萬元) | int | 同上 |
| `MF_PER` / `N_MF_PER` | 貨幣庫存比 / 非貨幣庫存比 | int |  |
| `VISIT_CNT` / `CALL_CNT` / `TOT_CNT` | 應親訪次數 / 應電訪次數 / 應完成總次數 | int |  |
| `NEED_CNT` | (無中文名) | int | 0 代表不需計次,`FREQ` 顯示為空 |
| `FREQ_NUM` / `FREQ_UNIT` / `FREQ` | (無) / (無) / 計算頻率 | int / string / string | `FREQ` 是 `DECODE` 出來的顯示欄,非實體欄位 |
| `MEMO` | 備註 | string | UI 上已註解不用 |

#### `CRM007A` — 直銷分配客戶名單(56 欄,`CRMI001` / `CRMB001`–`CRMB004` 共用)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `ASSIGN_NO` | 分配序號 | string | PK,一期一個 |
| `BF_NO` | 受益人戶號 | double | PK |
| `EXE_DATE` | 執行日期 | string | 名單產生的結算日 |
| `RULE_CODE` | 規則編號 | string | `1`–`6`,`6` 是手動上傳 |
| `SOURCE_CODE` | 資料來源 | string | 下拉來源 `CTL014` 的 `442` |
| `LAST_TRN_SOURCE` / `LAST_TRN_DATE` / `LAST_FUND_ID` | 最後交易來源 / 日期 / 基金代碼 | string |  |
| `LAST_AGENT_ID` / `LAST_AGENT_CODE` / `LAST_AGENT_CODE1` | 最後交易銷售機構區別 / 代碼 / 單位1 | string | `LAST_AGENT_CODE1` 在 CSV 上傳時被塞進 `LAST_AGENT_CODE` 的值(§6.2) |
| `LAST_EMP_NO` | 最後交易員工代碼 | string |  |
| `TOT_ALLOT_AMT` / `BAL_AMT` | 單筆最高申購金額 / 庫存金額 | decimal | 由上游算好寫進來 |
| `LAST_DEPT_TYPE` / `BASE_DEPT_TYPE` | 最後交易單位類別 / 指派交易單位類別 | string |  |
| `ASSIGN_DATE1` / `ASSIGN_USER_ID1` / `ASSIGN_DEPT_NO1` / `ASSIGN_EMP_NO1` | 本次指派日期 / 指派者 / 單位代碼 / 業務代碼 | string | **調撥時整組往 `*2` 推**(§6.3) |
| `ASSIGN_DATE2` / `ASSIGN_USER_ID2` / `ASSIGN_DEPT_NO2` / `ASSIGN_EMP_NO2` | 前次指派日期 / 指派者 / 單位代碼 / 業務代碼 | string |  |
| `SPC_YN` | 特殊名單 | string | `Y` / `N`,查詢時用 `NVL(...,'N')` |
| `LAST_ASSIGN` | 前序號已指派 | string | 本模組無任何程式寫它 |
| `RESULT` | 有無意願申購 | string | `CRMB004` 寫入 |
| `NEXT_CONTACT_DATE` / `CONTACT_CODE` / `CONTACT_COMM` | 再聯絡日期 / 聯絡結果代碼 / 聯絡結果說明 | string | `CRMB004` 寫入 |

另有 9 個 join 帶回來的顯示欄(`BF_NAME`、`FUND_SH_NM`、`AGENT_SHNM`、`SOURCE_CODE_DESCRP`、`LAST_EMP_NAME`、`ASSIGN_DEPT_NO1_DESCRP`、`ASSIGN_DEPT_NO2_DESCRP`、`ASSIGN_EMP_NAME1`、`ASSIGN_EMP_NAME2`、`ASSIGN_USER_NAME1`、`ASSIGN_USER_NAME2`),**不是實體欄位**。

#### 非實體結果集(不是資料表)

| 名稱 | 用途 | 定義在 | 怎麼填 |
|---|---|---|---|
| `CRM001A_OPTION` | `CRMM001` 的全機構勾選清單 | `CRMM001Model.xsd` | `SELECT 0 AS ISCHECK, … FROM OFD068A`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:318-324` |
| `CRM002A_OPTION` | `CRMM001` 的全員工勾選清單(含 `ALL` 那一列) | 同上 | `dual` 併 `COD009` 的 `UNION`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:331-355` |
| `OUTBOUND` | `CRMM003` 的電訪人員帶值 | `CRMM003Model.xsd` | join `TMK_BF_V` / `COD006A` / `TA_AA_USER`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:638-649` |
| `CRM006A_HIS` | `CRMM003` 的通話歷史(6 欄) | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:856-870` |
| `CRM004A_HIS` | `CRMM003` 的索取歷史(12 欄) | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:872-892` |
| `EMP_INFO` | `CRMB003` / `CRMB004` / `CRMR001` / `CRMR002` 的登入者資訊與欄位鎖定旗標 | `CRMB003Model.xsd` 等 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:286-314` |
| `OutPutData` | `CRMB001` 的「產出客戶名單」Excel 資料 | `CRMB001Model.xsd` | `S_TA_CRMB001_GET`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:368-377` |
| `CRMB005_1` | `CRMB005` 的重複潛在客戶清單(12 欄) | `CRMB005Model.xsd` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:66-107` |
| `CRMR003` `CRMR004` `CRMR005` `CRMR006_1` `CRMR006_2` `CRMR007_1` `CRMR008_1` `CRMR008_2` | 八支報表的結果集形狀 | 各 `CRMRnnnModel.xsd` | SP 的 RefCursor(§7) |

### 2.4 與其他模組共用的表

| 表 | 誰也在用 | 讀 / 寫 | 詳見 |
|---|---|---|---|
| `CRM003A` | CAS(`CASM001` 當主檔,增刪改)、TMK(`TMKM001` / `TMKM002` 唯讀 join) | CAS 寫、TMK 讀 | §8.1 |
| `CRM006A` `CRM0061A` | TMK(`TMKM001` / `TMKM002` 唯讀)、OFD(`OFDI011` 唯讀) | 只有 CRM 寫 | §8.3 |
| `CRM004A` `CRM0041A` | 本模組的 `CRMR008` 會 UPDATE `PRINT_YN` | 只有 CRM 寫 | §7.4 |
| `CRM001A` `CRM002A` | **共用 PO** `BasicCRM_PO`、CLS(`CLSM001` / `CLSM002` / `CLSR001` / `CLSR002`)、DSM(`DSMI001` / `DSMR007`)、OFD(`OFDI011`) | 只有 `CRMM001` 寫 | §8.2 |
| `CRM007A` | **共用 PO** `BasicCRM_PO`、共用控件 `ucAssignDeptNo` / `ucAssignEmpNo`、OFD(`OFDI011`) | 只有 CRM 寫 | §8.4 |
| `CRM008A` | **全庫只有 `CRMM002`** | 只有 CRM | — |
| `CRM004` | **全庫只有 `CRMM004`** | 只有 CRM | — |

外部唯讀表(join 進來取說明用,本模組從不寫入):`COD009`(員工)、`COD006A`(代碼說明)、`OFD002`(部門)、`OFD068A`(銷售機構)、`OFD081A` 與 `OFD081V`(基金)、`CTL014`(下拉代碼)、`BMS001A_V01`(受益人檢視表)、`TMK001A` 與 `TMK_BF_V`(電訪)、`SAL051`(直銷職級)、`OFD303A`(基金結帳控制)、`TA_AA_USER` 與 `AA_USER`(平台使用者)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`CRM003A` / `CRM006A` / `CRM0061A` / `CRM004A` / `CRM0041A` / `CRM001A` / `CRM002A` / `CRM008A` / `CRM004` 的 `STATUS` 由框架的 `EVAStatusCode` 常數決定,值域見 `architecture.md §3.10`,CRM 內沒有任何一支程式寫死它。

**唯一的例外是 `CRM007A`,它的 `STATUS` 被寫死成 `'301'` 兩次:**

| 在哪 | 寫法 | 錨點 |
|---|---|---|
| `CRMI001_PO` 查詢時設 `DefaultValue` | `STATUSColumn.DefaultValue = "301"` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480` |
| `CRMB001_PO` 的 CSV 上傳 INSERT | SQL 裡直接寫 `'301'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:163` |

CAS 那邊 `CASB001` 也把 `CLS002A` 的狀態直接寫成 `'301'`(`cas.md §8.3`),**兩個模組寫死同一個值,顯然 `'301'` 就是「已覆核 / 正式生效」**。這是**假設**,依據是兩個模組獨立寫死同一個值,而且 `CRMI001` 把它當成「查出來的資料一律視為已生效」用。要確認得反編譯 `EVAStatusCode` 或直接查資料庫。

**`CRM007A` 從來不走四眼流程。**它的 13 個四眼欄位在 `CRMI001_PO` 被一次設成「同一個人輸入 + 驗證 + 覆核」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480-492`),`REJECTDATE` 的預設值是 `1900/1/1`。這是「有四眼欄位但沒有四眼流程」的典型。

#### 本模組自訂的旗標值

| 值域 | 用在哪 | 語意(反推) | 錨點 |
|---|---|---|---|
| `USAGE` = `'1'` | `CRM003A` | CRM / TMK 的世界(CAS 用 `'3'`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `RULE_CODE` = `'1'`–`'6'` | `CRM007A` | 名單產生規則;`'6'` 是「依條件篩選,手動上傳」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:60`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.Designer.cs:220` |
| `EXECUTE` = `'1'` / `'2'` | `CRMB001` 的動作別 | `1` 產生、`2` 刪除 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128` |
| `SAL_CD` = `'A'` / `'B'` / `'C'` / `'D'` | `SAL051`(外部) | 直銷主管 / 組主管 / 業務員 / 助理 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-348`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:282`〔客戶特定〕 |
| `SORT_ORDER` = `'0'`–`'5'` | `CRMB002`–`CRMB004` 的排序 | 機構+員工 / 受益人類別 / 戶號 / 地址 / 庫存金額 / 最後交易日 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` |
| `REPORT_TYPE` = `'1'` / `'2'` / 其他 | `CRMR006` | 前兩者進 `CRMR006_1`,其餘進 `CRMR006_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:61-63` |
| `REPORT_TYPE` = `'0'` / 其他 | `CRMR008` | `0` 走 `S_TA_CRMR008_GET_1`,其餘走 `_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:57-60` |
| `MERGE_TYPE` = `'1'` / `'2'` | `CRMB005` | 姓名+通訊地址相同 / 姓名+統一編號相同 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:86-107` |
| `INQ_EMP_NO` = `'ALL'` | `CRM002A` | 該機構底下全部員工 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337` |
| `AGENT_CODE` = `'ALL'` | `CRM008A` | 該機構別底下全部機構 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:124` |

#### 代碼分類碼(`CODE_SORT` / `SOURCETYPE`)

| 分類碼 | 屬於 | 用途(取自程式上下文) | 錨點 |
|---|---|---|---|
| `P5` | `COD006A` | OutBound 項目說明 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:647` |
| `1C` | `COD006A` | 通話種類代碼小類 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:868` |
| `11` | `COD006A` | 需求資料種類代碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:890` |
| `442` | `CTL014` | 資料來源(`SOURCE_CODE`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:101` |
| `600` | `CTL014` | 計算頻率單位(`FREQ_UNIT`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:56` |
| `062` | 下拉(`GetDropDownDataSrc`) | 銷售機構區別碼 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:72` |
| `445` | 下拉(`GetDropDown9iDataSrc` / `GetDropDownDataSrc`) | 部門歸屬種類 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335-336` |

`438`(DM寄發碼)與 `439`(寄發廣告EMAIL)在 `CRMM003` 是**被註解掉的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:155`、`:157`),註解寫「2020.03.30 移除DM寄發碼與寄發廣告EMAIL的選項 by hanna 9000008774」——欄位還在表上,只是不再能從畫面設定。

## 3. 畫面清冊

畫面中文名 ATLAS 沒有放進版控(`architecture.md §6`),以下「中文名」欄的來源分三種:**報**=程式裡的報表名字串、**窗**=彈出視窗的 `this.Text`、**推**=由欄位與標籤推測。18 支畫面**六層全齊**。

### 3.1 維護 M

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMM001` | 員工銷售機構查詢權限維護 | 窗+推 | 齊 | `CRM001A` `CRM002A`(兩張都算主檔) | 無 | `BaseMultiRowEVADaoPO` | — | — |
| `CRMM002` | 銷售機構部門歸屬維護 | 推 | 齊 | `CRM008A` | 無 | `BaseMultiRowEVADaoPO` | — | — |
| `CRMM003` | 潛在客戶維護 | 窗+推 | 齊 | `CRM003A`〔共用〕 | `CRM006A` `CRM0061A` `CRM004A` `CRM0041A` | `BaseEVADaoPO` | — | — |
| `CRMM004` | 客戶分級參數維護 | 推 | 齊 | `CRM004`(vdb 名 `CRMM004`) | 無 | `BaseEVADaoPO` | — | — |

### 3.2 查詢 I

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMI001` | 直銷分配客戶名單查詢 | 推 | 齊 | `CRM007A`(只在 SQL 字串裡) | 無 | **無基底**(裸 DAO) | `F_TA_GET_EMPS` | — |

### 3.3 批次 B

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMB001` | 直銷分配客戶名單產生 / 刪除 / 上傳 | 推 | 齊 | `CRM007A` | 無 | `BaseEVADaoPO`(未用四眼) | `S_TA_CRMB001_EXCUTE`(**呼叫被註解**)、`S_TA_CRMB001_GET` | — |
| `CRMB002` | 指派名單單位調撥 | 推 | 齊 | `CRM007A` | 無 | 無基底 | — | — |
| `CRMB003` | 指派名單業務員指派 | 推 | 齊 | `CRM007A` | 無 | 無基底 | `F_TA_GET_EMPS` | — |
| `CRMB004` | 指派名單聯絡結果登錄 | 推 | 齊 | `CRM007A` | 無 | 無基底 | — | — |
| `CRMB005` | 重複潛在客戶合併 | 推 | 齊 | `CRM003A`〔共用〕 | 無 | 無基底 | `S_TA_CRMB005_EXCUTE` | — |

### 3.4 報表 R

| 代號 | 中文名 | 來源 | 六層 | 取數來源 | rpt |
|---|---|---|---|---|---|
| `CRMR001` | 指派單位明細表 | 報 | 齊 | `S_TA_CRMR001_GET` | `CRMR001RPS` |
| `CRMR002` | 指派業務員明細表 | 報 | 齊 | `S_TA_CRMR002_GET` | `CRMR002RPS` |
| `CRMR003` | 指派名單追蹤彙總表-By單位別 | 報 | 齊 | `S_TA_CRMR003_GET` | `CRMR003RPS` |
| `CRMR004` | 指派名單追蹤彙總表-By業務員別 | 報 | 齊 | `S_TA_CRMR004_GET` | `CRMR004RPS` |
| `CRMR005` | 指派名單追蹤明細表-By業務員別 | 報 | 齊 | `S_TA_CRMR005_GET` | `CRMR005RPS` |
| `CRMR006` | 指派名單聯絡結果統計表 / 明細表(三選一) | 報 | 齊 | `S_TA_CRMR006_GET` | `CRMR006RPS1` `CRMR006RPS2` `CRMR006RPS3` |
| `CRMR007` | 客戶通話記錄明細表 | 報 | 齊 | `S_TA_CRMR007_GET` | `CRMR007RPS1` |
| `CRMR008` | 客服潛在客戶索取資料明細表 / 資料表(二選一) | 報 | 齊 | `S_TA_CRMR008_GET_1` `S_TA_CRMR008_GET_2` | `CRMR008RPS1` `CRMR008RPS2` |

### 3.5 一眼看出差別的五件事

1. **五支 B + 一支 I 的 PO 有五種不同的寫法。**`CRMB001_PO` 繼承 `BaseEVADaoPO` 卻一個四眼事件都沒掛(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:48-50` 是空建構子);`CRMB002`–`CRMB005` 與 `CRMI001` 完全沒有基底,自己 `new Database("TA", ...)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:40`)。

2. **兩支 M 用多筆版、兩支用單筆版。**這決定了它們能不能有明細、樂觀鎖比什麼、`ApproveDelete` 會跑幾次(§2.1)。

3. **`CRMM004` 是全模組唯一在伺服器端擋資料的畫面**(`args.Cancel` + `args.CancelMsg`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:100-104`)。其餘所有卡控都在用戶端,繞過 UI 就沒有任何保護。

4. **`CRMI001` 與三支 B 的取數 SQL 有 90% 重複。**`CRMB002` / `CRMB003` / `CRMB004` 的 `Select` 是同一段 join 抄三份,差別只在 `CRMB003` 多掛了 `F_TA_GET_EMPS` 的權限限制、`CRMB002` 多了 `ASSIGN_DEPT_YN` 條件、`CRMB004` 多了一個 `TO_DATE` 顯示欄(§6.2)。

5. **八支報表 PO 的結構一模一樣**,差別只在 SP 名字與參數清單;只有 `CRMR006` / `CRMR008` 多了報表種類分支,`CRMR008` 多了一支寫入方法(§7)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] M 畫面從按鈕到四眼引擎的卡控順序，以及四支畫面各掛了哪些事件
圖中文字:① 用戶端：四支 M 的卡控都在這一層 / Before*ButtonClicked / Add/Modify/Delete/Search / validatorManager1 / 必填與格式 框架決定 / DoValidate() / M004 回傳語意相反 / Pxy 直呼 DB 檢核 / EXIST_EMP_NO IS_EXISTS / ② 回填：把主檔欄位寫進明細／勾選項目轉成資料列 / GetPageValue / M001 差異比對 M003 兩組明細 / SetMasterToDetail / 只有 CRMM002 有 / ProcessVDB / ViewVDB 過 Remoting / ③ 伺服端 Before*：唯一會擋資料的是 CRMM004 / BeforeAdd / M003 取 PR_NO 撞號重取 / BeforeSelect / 整條 SQL 換掉 / BeforeUpdate / M004 區間重疊 Cancel / SetDetailSrNo / 取號失敗寫 -1 進 PK / ④ EVA 引擎：CRMM001 覆寫了三個基底方法 / EVA 引擎 / 無原始碼 DLL 內 / Add 覆寫 / CRM002A 手寫 INSERT / IsChangedByData 覆寫 / CRM002A 樂觀鎖關掉 / ApproveDelete 覆寫 / 存在才做 避免跑多次 / ⑤ After*：只有 CRMM003 有，8 個掛點全是跳號一覽表 / CRMM003 / 8 個 After throw 空訊息 / CRMM001 CRMM002 / 只掛 Before* / CRMM004 / Before* + 伺服端卡控 / BeforeApproveDelete / M003 自己 DELETE 明細
```

*圖:圖 3 卡控與四眼順序。橘框=本模組寫的程式碼；黑框=框架 DLL（無原始碼，從呼叫端反推）；橘虛框=寫死值或會咬人的行為。除了 CRMM004 的區間重疊檢核之外，所有卡控都在用戶端，繞過 UI 就沒有任何保護。*

### 4.1 `CRMM001` — 員工銷售機構查詢權限維護

#### 用途(推測)

**設定「哪個員工可以查到哪些銷售機構、以及那些機構底下哪幾位員工的資料」。**這是一張純授權表,本模組自己完全不讀它——讀的人是共用 PO `BasicCRM_PO` 與 CLS / DSM / OFD 的畫面(§8.2)。

畫面結構:上方一個員工代碼欄(`custEMP_NO`),下方一個機構勾選 grid(`ugrdCRMM001`,資料來源是 `CRM001A_OPTION`)。雙擊某一列機構會開彈出視窗「員工銷售機構權限明細設定」(`CRMM001p0`),在裡面勾這個機構底下要開放哪幾位員工(`CRM002A_OPTION`)。

#### 多筆版的三個覆寫

這支是全模組技術上最特別的一支,因為 `BaseMultiRowEVADaoPO` 原本只支援「一張主表、多筆列」,而這裡要處理兩張表:

| 覆寫 | 為什麼 | 做了什麼 | 錨點 |
|---|---|---|---|
| `BeforeAdd` | 底層對第二張表下 INSERT 會噴 `ORA-01008: not all variables bound`(註解原話) | `args.TableName` 不是第一張表就 `args.Cancel = true`,整段跳過 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:70-78` |
| `Add` | 承上,`CRM002A` 的 INSERT 要自己寫 | 手寫 18 欄的 INSERT,逐列綁參數;**四眼欄位全部抄主檔第一列的值** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:86-137` |
| `IsChangedByData` | 兩張表都做樂觀鎖會比兩次 | 只在 `dbTableName == MasterTable[0]` 時做,其餘直接回 `false` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:146-152` |
| `ApproveDelete` | 主檔多筆會讓底層跑很多次 | 先用 `IsExistByMasterPK` 判斷還在不在,不在就直接回 `true` 忽略 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:160-169` |

**後果要記住三條:**

- `CRM002A` 的樂觀鎖是**關掉的**(`IsChangedByData` 對它一律回 `false`)。兩個人同時改同一個員工的可查員工清單,後存的直接蓋掉前存的,沒有「資料已被您異動」。

- `CRM002A` 的 `DATAID` 取自主檔第一列(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:110`),所以主明細確實綁在同一次 EVA 批次內。

- 手寫的那段 INSERT **把欄位名寫死在字串裡**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:93-101`),xsd 重生不會同步它。`CRM002A` 加欄位一定要手動改這段。

#### 主檔取數的「只取第一筆」把戲

查詢頁的結果 grid 一個員工只顯示一列,做法是在 SQL 裡用 `ROW_NUMBER() OVER (PARTITION BY EMP_NO ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE)` 取 `NUM = 1`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:252-258`)。

**排序欄位用的是三個日期而不是機構代碼**,所以「顯示出來的那一列是哪一個機構」是不確定的——同一批建立的列 `CREATEDATE` 會一樣。不過 grid 的顯示白名單只有 `EMP_NO` / `EMP_NAME` / `STATUS` 三欄(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:55`),使用者看不到差別。`CRMM002` 用同一招但排序多加了機構欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:90-91`),比較嚴謹。

#### 必填與存檔前檢核

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改 | 框架欄位必填(員工代碼) | 空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:529` |
| 按新增(限新增模式) | 機構 grid 至少勾一筆 | 一筆都沒勾 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:535-540` |
| 按新增(限新增模式,且前面都過) | 該員工是否已建過資料 | 已存在 | 阻擋(對話框) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:549-560` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:446-476` |
| 雙擊明細列 | 先跑一次 `DoValidate()`(不帶 `isFinish`) | 失敗 | 阻擋(不開視窗) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:190-194` |
| 雙擊明細列 | 該列沒勾選 | 沒勾 | 過濾(無提示,直接 `return`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:201-202` |

**「該員工已建過資料」這條會靜默放行。**`EXIST_EMP_NO` 的 `catch` 只做 `Result.Clear()`,**沒有再 `AddResultRow`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473`),UI 判斷的是 `Result.Count > 0 && Result[0].ReturnCode == true`,所以 SQL 一出錯 → `Count == 0` → 檢核通過 → 重複建檔(附錄 E.3)。

而且這段 SQL 是字串串接的:`string.Format(@"SELECT COUNT(*) FROM CRM001A WHERE EMP_NO = '{0}'", emp_no)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:452`),`emp_no` 來自畫面欄位。

#### 自動帶值(不是卡控,但會改資料)

| 行為 | 說明 | 錨點 |
|---|---|---|
| 勾了機構但沒勾任何員工 → 自動補一筆 `INQ_EMP_NO = 'ALL'` | 存檔前跑 `DoCheckDetail`,每個被勾的機構都檢查一次 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:478-490` |
| 開明細視窗時,原本沒有任何勾選 → 預設把 `ALL` 那列勾起來 | 只影響視窗內顯示 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:224-229` |
| 編輯模式下員工代碼欄鎖死 | `custEMP_NO.Enabled = false` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:499-507` |

**「自動補 ALL」的意思是:勾了機構卻不指定員工,等於開放該機構全部員工。**這是一個很容易被誤解成「沒設定就是沒權限」的預設值,實際上是相反的。

#### 編輯模式的差異比對

編輯模式不是整批砍掉重建,而是逐列比對(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:388-467`):原本有、現在沒勾 → `row.Delete()`;原本沒有、現在有勾 → `AddXxxRow`;兩邊都有 → 不動。`CRM002A` 的刪除有兩條路(主選項整個沒勾 / 明細單項沒勾),兩條都會 `Delete()`。

#### 四眼各階段附加動作

**一個都沒有。**`CRMM001_PO` 只掛了四個 `Before*`(`BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` / `BeforeAdd`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:46-49`),沒有任何 `After*`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | 員工代碼空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:529` |
| 新增前 | 機構至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:535-540` |
| 新增前 | 員工是否已建檔 | 已存在 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:549-560` |
| 新增前 | 同上,但 SQL 出錯 | 例外 | **記錄不擋**(靜默放行) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473` |
| 雙擊明細 | 該列未勾選 | 未勾 | 過濾(無提示) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:201-202` |
| 存檔前 | 機構有勾但員工零勾 | 成立 | **記錄不擋**(自動補 `ALL`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:484-489` |
| 覆核刪除 | 該批已不存在 | 成立 | 過濾(直接回成功) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:165-166` |

### 4.2 `CRMM002` — 銷售機構部門歸屬維護

#### 用途(推測)

**把銷售機構歸類到「部門歸屬種類 × 部門歸屬類別」兩層分類底下。**主檔 `CRM008A` 的四個 PK 欄位就是這個結構:`AGENT_BELONG_TYPE`(種類,下拉代碼 `445`)+ `AGENT_TYPE`(類別代碼)+ `AGENT_ID`(機構別)+ `AGENT_CODE`(機構代碼)。

畫面是「一個分類 + 一個機構明細 grid」,但因為用的是多筆版,**grid 裡每一列其實都是一筆獨立的主檔**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:94`:`ugrdCRMM002.DataSource = ...UIView.CRM008A`)。查詢結果 grid 用 `ROW_NUMBER() ... PARTITION BY AGENT_BELONG_TYPE, AGENT_TYPE` 取第一筆,製造出「一個分類一列」的假象(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:89-95`)。

主檔語法那段還做了一件事:把 `AGENT_ID` 與 `AGENT_CODE` 兩欄硬寫成一個空白字元(`' ' AGENT_ID, ' ' AGENT_CODE`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:86-87`),讓查詢頁不顯示機構——**查詢與維護是兩套不同的 SQL,欄位語意不同**。

#### 必填與存檔前檢核

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改 | grid 的 `ActiveRow.Update()`(防快速鍵沒寫回) | — | 記錄不擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:125-126`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:138-139` |
| 按新增 / 修改 | 框架必填 + 明細至少一列 | grid 零列 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:175-178` |
| grid 輸入格 | 明細 PK 重複檢查 | 重複 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:229` |
| grid 插入列 / 更新列 | 明細 PK 必填 | 缺 PK | 阻擋 / 標紅 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:234-252` |
| 機構 Searcher 選完之後 | 同一部門歸屬底下機構不可重複 | 已存在 | 警示(清掉剛選的值) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:278-287` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:147-177` |
| 機構 Searcher 開啟前 | 該列要先選機構別 | 沒選 | 阻擋(取消開窗) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:305-308` |

**重複檢查也會靜默放行。**`IS_EXISTS` 的 `catch` 塞了訊息但回傳 `false`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176`),UI 判 `== true` 才擋,所以 SQL 出錯 = 允許重複(附錄 E.3)。

還有一個範圍不一致:`IS_EXISTS` 的條件只有 `AGENT_BELONG_TYPE` + `AGENT_ID` + `AGENT_CODE` 三欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:154-155`),**沒有 `AGENT_TYPE`**,但 PK 有四欄。也就是**同一個「部門歸屬種類」底下,不同「類別」不能放同一個機構**——比 PK 嚴格。這可能是刻意的(一個機構只能歸一類),但訊息寫的是「此類別已重複設定」,容易讓人以為只檢查同一類別。

#### 自動帶值

- 選了 `AGENT_TYPE` 之後,`AGENT_TYPE_NM` 自動填成該代碼的顯示文字(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:360-363`)。

- 改了某一列的 `AGENT_ID`,同列的 `AGENT_CODE` 與 `AGENT_SHNM` 會被清空(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:320-324`)。

- 存檔前 `SetMasterToDetail()` 把畫面上的三個分類欄位寫回 grid 每一列(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:185-194`)。**編輯模式下分類欄位是鎖死的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:107-108`),所以這個回填只在新增時有意義。

#### 四眼各階段附加動作

**一個都沒有。**只掛三個 `Before*`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:33-35`)。這支連 `BeforeAdd` 都沒有,因為 PK 全部由使用者輸入,不需要取號。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | 分類欄位空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:173` |
| 新增 / 修改前 | 明細至少一列 | grid 零列 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:175-178` |
| grid 編輯 | 明細 PK 重複 | 重複 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:229` |
| grid 編輯 | 明細 PK 必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:234-236` |
| 選機構後 | 同種類底下機構重複 | 重複 | 警示 + 清值 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:278-287` |
| 選機構後 | 同上,但 SQL 出錯 | 例外 | **記錄不擋**(靜默放行) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176` |
| 開機構 Searcher | 未先選機構別 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:305-308` |
| grid 內部錯誤 | 任何 grid error | 成立 | **過濾(無提示)**`e.Cancel = true` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:254-257` |

### 4.3 `CRMM003` — 潛在客戶維護

#### 用途(推測)

**建立與維護潛在客戶的基本資料,並且每一次通話、每一次寄送資料都留一筆紀錄。**一主四明細,四張明細其實是兩組對稱的結構:

| 組 | 表頭 | 種類明細 | 一次事件的識別 |
|---|---|---|---|
| 通話 | `CRM006A`(備註、完成碼) | `CRM0061A`(可複選的通話種類) | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` |
| 索取 | `CRM004A`(寄送方式、數量、傳真、Email、標籤) | `CRM0041A`(可複選的資料種類) | `PR_NO` + `REQ_DATE` + `REQ_SRNO` |

這支是全模組最大的一支(UI 1,910 行、PO 1,052 行、Ctl 344 行),也是唯一掛滿 8 個 `After*` 的一支。

#### 主檔取號與 `USAGE`

| 動作 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetPR_NO()` 取號,`do…while (IsExistByData(...))` 撞號重取 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:210-214` |
| `GetPageValue`(新增時) | `USAGE` 硬寫 `"1"` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467` |
| `BuildMasterSQLString` | 查詢一律加 `WHERE CRM003A.USAGE = '1'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |

**CAS 的 `CASM001` 寫的是 `'3'`、查的也是 `'3'`,兩邊資料互不相見**(§8.1,與 `cas.md §8.2` 一致)。

`GetPageValue` 還會把登入者的員工代碼寫進 `EMP_NO1`,取法是「呼叫 `GetEMP_INFO` 回傳的字串用逗號切開取第 2 段」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:456`)——與 `CRMI001`、`CRMB003`、五支 R 畫面同一個寫法,是**位置取參數**的典型(附錄 E.6)。

#### 明細序號(批次)怎麼決定

同一天可以打好幾通電話,用 `CALLIN_SRNO` 區分。序號有**兩套實作**:

| 路徑 | 觸發 | 做法 | 錨點 |
|---|---|---|---|
| 畫面端 | 使用者改了通話日期 / 索取日期(`Leave` 事件),且處於「新增明細」狀態 | 打 `GetSRNO` 拿 `MAX(SRNO) + 1` 回填到畫面欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1383-1417` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:729-785` |
| 伺服器端 | `BeforeAdd` / `BeforeUpdate` 的 `SetDetailSrNo` | 用 `intGetSRNO` 再算一次,**與畫面上那個不一致時整批覆寫** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:228-307`、`:1003-1050` |

兩套算的是同一件事,但**錯誤處理完全不同**:

- `GetSRNO`(畫面路徑)出錯時 `AddResultRow(false, 0, "取得批次失敗,請檢查")`,UI 會跳訊息並 `return`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1392-1397`)。

- `intGetSRNO`(伺服器路徑)出錯時**回傳 `-1`**,錯誤訊息塞進 `ref sErr`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047`)。而呼叫端 `SetDetailSrNo` **完全沒有檢查 `sErr`,也沒有檢查回傳值是不是 `-1`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:234-241`),`-1` 會被當成正常序號寫進 `CALLIN_SRNO` / `REQ_SRNO`。

**這是本模組最容易產生髒資料的一條:DB 一出問題,批次序號變成 `-1` 並且寫進 PK。**嚴重度高(附錄 E.3)。

#### 明細取數:兩張永遠查不到、兩張只看今天

`BuildDetailSQLString` 的四個分支:

| 明細 | 條件 | 效果 | 錨點 |
|---|---|---|---|
| `CRM006A` | `CALLIN_DATE = TO_CHAR(SYSDATE,'YYYYMMDD')`,且只取同日 `MAX(CALLIN_SRNO)` | **只看得到今天的最後一通** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:390-402` |
| `CRM0061A` | 同上 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:408-420` |
| `CRM004A` | **`WHERE 1=2 AND …`** | **永遠零筆** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436` |
| `CRM0041A` | **`WHERE 1=2 AND …`** | **永遠零筆** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:454` |

`1=2` 顯然是刻意加的(兩處都加在同一個位置、同一次改動),但**沒有任何註解說明為什麼**。合理的解釋是「索取資料頁改成一律新增,不載入既有資料」,因為畫面上的索取區塊搭配的是 `IsAddREQ` 狀態機。**這是假設**,依據是 `CRM006A` 那邊沒有 `1=2` 而且有 `CALLIN_DATE = SYSDATE` 的限制,兩者的設計意圖看起來是同一個方向,只是手段不同。要確認得問使用者「開啟舊客戶時索取資料頁應該顯示什麼」。

真正給使用者看的歷史資料走另一條路:`GetHistory_Call_Req` 撈進 `CRM006A_HIS` / `CRM004A_HIS` 兩個結果集,在 `ModifyDataLoad` 時由 `CallInHis()` 觸發(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1149`、`:1736`)。

**`GetHistory_Call_Req` 那段 SQL 是兩句 `SELECT` 用分號串起來的**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:870`、`:892`),然後一次 `LoadDataSet(cmd, ds, "CRM006A_HIS", "CRM004A_HIS")` 期待回兩張表(`:897`)。**Oracle 的 `ExecuteReader` 不接受分號分隔的多句 SQL**,這段**應該**會丟 `ORA-00911: invalid character`。這是**假設**——依據是 Oracle 的語法規則與 ODP.NET 不支援批次語句;無法在本機驗證。若假設成立,後果是「客戶歷史資料」永遠是空的,而且因為 `catch` 只塞了「取得客戶歷史資料失敗,請檢查」的訊息,使用者只看得到一句沒有細節的錯誤(附錄 E.7)。

#### 必填與存檔前檢核(`DoValidate`)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | — | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:279` |
| 新增 / 修改前 | 統一編號與客戶姓名不可同時空白 | 兩個都空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:283-287` |
| 新增 / 修改前 | 主檔 EMAIL 格式 | 有填且格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:290-294` |
| 新增 / 修改前 | 索取資料的 EMAIL 格式 | 有填且格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:296-300` |
| 新增 / 修改前 | 通話有異動時,通聯原因至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:303-314` |
| 新增 / 修改前 | 索取有異動時,資料種類至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:316-328` |
| 上述全過之後 | 通話日期大於系統日 | 成立 | **詢問**(選否就中止) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:341-352` |
| 上述全過之後 | 索取日期大於系統日 | 成立 | **詢問**(選否就中止) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:354-365` |

兩個詢問通過之後都會呼叫 `ByPassAddMessage` 把「使用者已知悉」寫進 VDB(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:351`、`:364`),這是全模組唯一用到繞行紀錄的地方。

**六條檢核的錯誤全部掛在兩個 Email 控件上**(`utxtEMAIL` / `utxtEMAIL_REQ`),包括「統一編號或客戶姓名不可同時空白」與兩個勾選檢核。使用者按訊息會跳到錯誤的欄位(附錄 E.8)。

#### 查詢前檢核(`DoValidateQuery`)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 戶號起迄必須皆填或皆不填 | 只填一邊 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:219-224` |
| 查詢前 | 戶號起 ≤ 戶號迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:225-229` |
| 查詢前 | 通話日期起迄必須皆填或皆不填 / 起 ≤ 迄 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:231-241` |
| 查詢前 | 索取日期起迄必須皆填或皆不填 / 起 ≤ 迄 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:243-253` |
| 查詢前 | 查詢條件不可同時空白 | 全空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:255-265` |

**「不可同時空白」那條漏掉了行動電話。**條件式列了 8 個欄位,其中 `utxtEMAIL_0.Text` **重複寫了兩次**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:260-261`),而送查詢時明明有 `CELL_PHONE` 這個條件(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1054-1057`)。**只填行動電話按查詢會被擋下來說「查詢條件不可同時空白」**,重複的那一行八成本來要寫 `utxtCELL_PHONE_0`(附錄 E.8)。

第一條檢核的錯誤訊息是「戶號(起)(迄) 必須皆(不)填寫」,但掛的控件是通話日期欄(`udatCALLIN_DATE_ST_0`,`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:222`)。

#### 查詢條件怎麼組

`BeforeSearchButtonClicked` 每次都 `QueryVDB.Util.Parameters.Clear()`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1014`)——這點比 CAS 的 `CASM006` 好(那支的 `Clear()` 是被註解的)。

PO 端組 SQL 有兩個特別的:

- **客戶姓名用字串串接**:`AND CRM003A.PR_NAME LIKE N'%{0}%'`,值直接取自參數(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:339`)。這是本模組唯一一處對主檔查詢做字串串接的地方,其餘走 `EVAStringHelper.AddParam`。

- **通話 / 索取日期範圍是子查詢**:`AND CRM003A.PR_NO IN (SELECT DISTINCT PR_NO FROM CRM006A WHERE …)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:344-364`)。只有起日有值才加,迄日是跟著一起進去的。

另外主檔查詢一律 `LEFT JOIN` 一段自組的電訪人員子查詢(`GetOutBoundSQLString`),而那段子查詢的 `BF_NO` 條件也會吃查詢參數(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:687-688`)。**查戶號區間時,條件同時作用在主表與電訪子查詢上**,這是刻意的(避免把整張 `TMK_BF_V` 掃進來)。

#### 新增前的重複統編檢查

開「潛在客戶資料選取視窗」(`CRMM003p1`)之前,新增模式會先檢查該統編有沒有既有的潛在客戶序號:

- PO 的 `IsValidAdd` 用綁定參數查 `CRM003A` join `CRM006A` 的筆數,**出錯回 `-1`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:966-986`)。

- UI 判 `i == 0 ? true : false`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1475-1480`),所以 `-1` → `false` → 跳「此統一編號已有潛在客戶序號,是否要繼續新增?」的詢問。

**這條的錯誤處理方向與其他檢核相反:出錯時是「多問一次」而不是「靜默放行」。**結果安全,但訊息會誤導。

還有一條訊息與行為不符:按統編欄的按鈕時,條件是「長度 ≤ 5」,訊息卻寫「統一編號資料**過多**,請至少key六碼」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530`)——條件是太短,訊息說太多。

#### 自動帶值與被關掉的功能

| 行為 | 說明 | 錨點 |
|---|---|---|
| 選了戶號 → 自動帶電訪人員 | 只有新增模式做;編輯模式保留畫面原值 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1549-1566` |
| 拒絕行銷四個勾選框 → 反寫 `DM_CODE` / `DM_EMAIL` | 勾「拒絕所有」或「拒絕網路」→ `DM_EMAIL = 'N'`;勾「拒絕所有」或「拒絕書面」→ `DM_CODE = 'N'`;否則一律 `'Y'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:527-542` |
| **編輯模式下四個拒絕行銷勾選框全部 disabled** | 新增模式沒有這段,所以只有建檔當下能設 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| DM寄發碼 / 寄發廣告EMAIL 的下拉 | **2020-03-30 移除**,欄位改由上面那條規則反推 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:153-157` |
| 通訊地址 14 個細欄的回填 | **整段被註解**,只剩 `MAIL_ADDR` 由控件直接綁 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:483-496` |

「拒絕行銷只能在新增時設」是一個很硬的限制:**客戶事後表示要拒絕行銷,這支畫面改不了**。要確認這是刻意的還是漏了 `AddDataLoad` 的對應處理。

#### 覆核刪除時的明細處理

`BeforeApproveDelete` 做了一件很特別的事:把 model 裡四張明細全部 `Clear()` + `AcceptChanges()`,然後**自己下四句 `DELETE {表} WHERE PR_NO = '{值}'`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:88-121`)。註解寫的理由是「因為有歷史資料的問題,所以忽略底層處理」。

三件事要注意:

1. **`PR_NO` 是用 `string.Format` 串進 SQL 的**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:109`、`:113`),不是綁定參數。`PR_NO` 由系統取號所以風險低,但寫法是髒的。

2. **刪除的是該客戶的全部明細,不只是畫面上載入的那幾筆。**因為明細取數有 `SYSDATE` 與 `1=2` 的限制,畫面上根本看不到全部,所以**使用者按下覆核刪除時,刪掉的比他看到的多很多**。

3. 迴圈跑的是 `this.DetailTable`,四張表都會刪;`ExecuteNonQuery` 的回傳值被丟掉,刪 0 筆也算成功。

#### 四眼各階段附加動作

八個 `After*` 全部做同一件事:呼叫 `SrNoCommentProcessor.AddCommentHistory(...)` 寫跳號一覽表,失敗就 `throw new ApplicationException("")`(空訊息)。

| 掛點 | 錨點 |
|---|---|
| `AfterGetMaintainData`(讀回跳號歷史) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:915-919` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:920-962` |

每個 handler 第一行都是 `if (args.TableName != this.MasterTable.dbTableName) return;`,因為事件會對主檔 + 每張明細各觸發一次(`architecture.md §3.8`)。**這套與 CAS 的 `CASM001` 完全同構**,連 `throw new ApplicationException("")` 的空訊息都一樣。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 四組起迄的成對與大小 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:219-253` |
| 查詢前 | 條件不可全空(**漏算行動電話**) | 全空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:255-265` |
| 按統編查詢鈕 | 統編長度 ≤ 5 | 成立 | 阻擋(訊息寫反) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530` |
| 開選取視窗前(新增) | 該統編已有潛在客戶 | 成立 | **詢問**(選否清畫面) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1487-1497` |
| 開選取視窗前(新增) | 同上但 SQL 出錯 | 例外 | **詢問**(回 `-1` 當成已存在) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:980-984` |
| 新增 / 修改前 | 統編與姓名不可同時空白 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:283-287` |
| 新增 / 修改前 | 兩個 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:290-300` |
| 新增 / 修改前 | 通話 / 索取種類至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:303-328` |
| 新增 / 修改前 | 通話 / 索取日期大於系統日 | 成立 | 詢問 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:341-365` |
| 新增前(PO) | `PR_NO` 撞號 | 成立 | 記錄不擋(重取號) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:211-214` |
| 存檔前(PO) | 批次序號重算,取號失敗 | 例外 | **記錄不擋**(`-1` 寫進 PK) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047` |
| 編輯模式載入 | 四個拒絕行銷勾選框 | 一律 | 過濾(disabled,無提示) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| 明細取數 | `CRM004A` / `CRM0041A` | 一律 | **過濾(無提示,`1=2`)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454` |
| 明細取數 | `CRM006A` / `CRM0061A` 非今日 | 一律 | 過濾(無提示) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:400`、`:418` |
| 覆核刪除 | 明細一律整批實體刪除 | 一律 | 記錄不擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:111-118` |
| 四眼各階段 | 跳號一覽表寫入失敗 | 失敗 | 阻擋(`throw`,訊息空白) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:924` |

### 4.4 `CRMM004` — 客戶分級參數維護

#### 用途(推測)

**定義客戶等級的判定條件與對應的服務標準。**一列就是一個等級(`CUS_LV`),內容是:要不要開戶、貨幣型 / 非貨幣型基金的庫存金額級距與庫存比、應親訪 / 應電訪 / 應完成總次數、以及計算頻率。

這是本模組唯一一支**單表、無明細、伺服器端有卡控**的維護畫面,也是最小的一支(PO 137 行)。

#### 三個旗標控制四組欄位的可編輯性

| 勾選框 | 控制什麼 | 勾掉時 | 錨點 |
|---|---|---|---|
| `uchkHASBF_NO`(是否開戶) | 連動 `uchkHAS_MF` 的可用性與勾選狀態 | 一併關掉貨幣型 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:220-230` |
| `uchkHAS_N_MF` | 非貨幣結餘起 / 迄 | 兩欄 `ReadOnly` 且清空 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:231-237` |
| `uchkHAS_MF` | 貨幣結餘起 / 迄 | 兩欄 `ReadOnly` 且清空 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:242-248` |
| `uchkHAS_PER` | 兩個庫存比欄位 | 同上 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:251-259` |

必填旗標(`reqv*.IsRequisite`)是**每次 `DoValidate` 時依 `ReadOnly` 動態設定**的(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:36-43`),不是 Designer 寫死的。這比全庫其他畫面的做法都乾淨。

#### `-1` 哨兵值

「起」的欄位空白時寫 `-1` 進 DB(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:66-71`),讀回來時 `>= 0` 才填進畫面(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:132-140`),grid 顯示時 `< 0` 就設成 Null(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:203-207`)。

**三個地方各自處理同一個哨兵值,沒有共用函式。**「迄」的欄位沒有這套(直接 `Convert.ToInt32`),因為它是必填的。

#### 伺服器端的區間重疊檢核

`BeforeUpdate`(`BeforeAdd` 直接轉呼叫它)會下兩段 SQL 檢查新資料的庫存區間與別的等級重疊:

| 段 | 條件 | 錨點 |
|---|---|---|
| 非貨幣 | `HAS_N_MF = 1 AND HAS_MF = :HAS_MF AND CUS_LV <> :CUS_LV AND ((:S > S AND :S < E) OR (:E > S AND :E <= E))` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:88-94` |
| 貨幣 | 同形狀,換成 `MF_*` 欄位 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:109-115` |

兩段都是 `SELECT '與客戶等級' || CUS_LV || '之…區間重疊'`,用 `ExecuteScalar` 取回訊息;非空就 `args.CancelMsg = msg; args.Cancel = true;`。**這是全模組唯一在伺服器端擋下資料的地方。**

**但重疊判斷式漏了一種情形:新區間完全包住既有區間。**

| 既有 | 新輸入 | `:S > S AND :S < E` | `:E > S AND :E <= E` | 判定 | 實際 |
|---|---|---|---|---|---|
| [10, 20] | [15, 25] | 15>10 且 15<20 ✔ | — | 重疊 ✔ | 重疊 |
| [10, 20] | [5, 15] | 5>10 ✘ | 15>10 且 15≤20 ✔ | 重疊 ✔ | 重疊 |
| [10, 20] | **[5, 30]** | 5>10 ✘ | 30>10 但 30≤20 ✘ | **不重疊** ✘ | **完全包住** |
| [10, 20] | [10, 20] | 10>10 ✘ | 20>10 且 20≤20 ✔ | 重疊 ✔ | 相同 |

也就是說**只要新等級的區間比既有等級寬,兩邊就都設得起來**,兩個等級會同時命中同一筆客戶。嚴重度高(附錄 E.4)。

另外兩個小問題:

- 兩段檢核的 `ExecuteScalar` 都沒有把 `cmd` 包在 `using` 裡(原本的 `using` 被註解掉了,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:83-84`、`:128`),命令物件不會被釋放。

- 第二段多了一句 `cmd.Parameters.Clear()`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:116`),但 `cmd` 是上一行剛 `GetSqlStringCommand` 出來的新物件,這句沒有作用。第一段沒有這句。**同一個方法裡兩段對稱的程式碼寫法不一致。**

#### `DoValidate` 的回傳語意與其他畫面相反

`CRMM004.DoValidate()` **回傳 `true` 代表有錯**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:45`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:54`),呼叫端寫 `if (DoValidate()) { e.Cancel = true; }`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:167-171`)。

而 `CRMM001` / `CRMM003` / 五支 B 畫面的 `DoValidate()` **回傳 `true` 代表通過**,呼叫端寫 `if (DoValidate() == false) { e.Cancel = true; }`。**同一個名字、相反的語意,在同一個模組裡並存**(附錄 E.4)。

#### 查詢與顯示

- 查詢只有一個條件 `CUS_LV`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:97-101`),而且每次先 `Parameters.Clear()`。

- 查詢 SQL 會 `LEFT JOIN CTL014`(`SOURCETYPE = '600'`)把 `FREQ_UNIT` 轉成顯示文字,再用 `DECODE(NEED_CNT, 0, '', TO_CHAR(FREQ_NUM) || DISPLAYNAME)` 組成 `FREQ` 欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:52-57`)。**維護頁的取數 SQL 沒有這個 join**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:66-70`),所以 `FREQ` 只在查詢 grid 上看得到。

#### 四眼各階段附加動作

**沒有 `After*`。**只有 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` / `BeforeAdd` / `BeforeUpdate` 五個(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:39-43`),其中 `BeforeGetToDoData` 直接轉呼叫 `BeforeSelect`、`BeforeAdd` 直接轉呼叫 `BeforeUpdate`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填(依旗標動態決定哪些欄必填) | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:36-45` |
| 新增 / 修改前 | 非貨幣結餘起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:47-49` |
| 新增 / 修改前 | 貨幣結餘起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:51-53` |
| **伺服器端** `BeforeAdd` / `BeforeUpdate` | 非貨幣庫存區間與其他等級重疊 | 成立 | 阻擋(`args.Cancel` + 訊息) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:85-105` |
| **伺服器端** 同上 | 貨幣庫存區間與其他等級重疊 | 成立 | 阻擋(訊息串接在前一條後面) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:106-127` |
| 伺服器端 同上 | **新區間完全包住既有區間** | 成立 | **記錄不擋**(判斷式漏掉) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:93-94`、`:114-115` |
| 勾選框連動 | 取消勾選 | 成立 | 記錄不擋(欄位清空且唯讀) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:231-259` |

## 5. 查詢畫面(I)

### 5.1 結構

`CRMI001` 是本模組唯一的 I 畫面,查的是 `CRM007A`(直銷分配客戶名單)。

| 面向 | `CRMM003`(M 型) | `CRMI001`(I 型) |
|---|---|---|
| 介面 | `ICRMM003_PO : IEvaDataAccess` | `ICRMI001_PO`,**不繼承任何東西**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:24` |
| 類別 | `: BaseEVADaoPO, ICRMM003_PO` | `: ICRMI001_PO`,**沒有基底**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:36` |
| 連線 | 由基底管 | **自己 `new` 兩個 `Database`**(`TA` 與 `SWProduct`);`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:38-39` |
| 主明細宣告 | `xTableMapping` | **整行被註解**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:44` |
| 唯一活著的方法 | 一堆 | 只有 `Select`(介面上還有三個宣告被註解);`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:26-30` |

> **與 CAS 一模一樣的掃描器誤判。**`CRMI001_PO.cs:44` 那行註解是 `//this.MasterTable = new TableMapping("OFD701", "SEAL");`,與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41` 逐字相同——兩支都是從同一個樣板複製來的。掃描器的正規式不剝註解(`architecture.md §6.3` 已記),所以全庫的「實體表」計數含有一批來自註解行的假表。本文一律以程式為準。

`CRMI001_PO` 另有兩支 `public` 方法 `GetEmpNo` / `GetUidCode`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:529`、`:560`),**但它們不在介面裡**——Ctl 拿到的是 `ICRMI001_PO` 型別,呼叫不到。**兩支都是死碼**,而且 `GetUidCode` 判了 `ds.Tables.Count > 0` 卻直接取 `Rows[0]`,查無資料時會 `IndexOutOfRange`(被 `catch` 吞成空字串)。

### 5.2 查詢條件

畫面共 20 組條件,分兩類:

| 類 | 條件 | 送出的參數名 |
|---|---|---|
| 起迄成對 | 分配期別、執行日期、受益人戶號、最後交易日期、最後交易員工代碼、單筆最高申購金額、結存金額、本次指派日期、再聯絡日期 | `*_BGN` / `*_END` |
| 單值 | 資料來源、最後交易基金代碼、最後交易銷售機構區別 / 代碼、最後交易單位類別、指派交易單位類別、本次指派者 / 單位 / 業務員、特殊名單、有無意願申購、聯絡結果代碼 | 同欄位名 |

外加一個看不見的:**登入者的員工代碼**(`QUERY_EMP_NO`),見 §5.3。

UI 端的檢核有一個共同的模式:「起有值、迄空白 → 自動把迄填成起」、「起空白、迄有值 → 報錯」、「兩邊都有 → 比大小」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:108-191`)。只有分配期別多一條「兩個都空也要報錯」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:112-113`),所以**分配期別是唯一的必填條件**。

### 5.3 哪些條件會靜默濾掉資料

#### (1) 登入者權限:`F_TA_GET_EMPS` 的 INNER JOIN

查詢 SQL 開頭是一段 `WITH`:

```
WITH MYAGENT_LIST AS
(SELECT RTRIM(SUBSTR(DEPT_EMP_NO, 2)) AS DEPT_EMP_NO
   FROM TABLE(F_TA_GET_EMPS('<登入者員工代號>')))
```

然後在 `WHERE` 裡硬加 `AND (CRM007A.ASSIGN_DEPT_NO1||CRM007A.ASSIGN_EMP_NO1) = RTRIM(Z.DEPT_EMP_NO)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`:107`)。

**這是 INNER JOIN,不是 `LEFT JOIN`,也不是 `EXISTS`。**後果:

| 情形 | 結果 |
|---|---|
| `F_TA_GET_EMPS` 回空集合 | **一筆都查不到**,而且畫面只會說「查無資料」 |
| 名單的 `ASSIGN_DEPT_NO1` 或 `ASSIGN_EMP_NO1` 是空白 | **查不到**(串起來對不上任何一筆) |
| 兩欄串起來的長度與 TVF 回的格式差一個字 | **查不到** |

`F_TA_GET_EMPS` **不在版控內**,回傳格式也只能從 `RTRIM(SUBSTR(DEPT_EMP_NO, 2))` 反推:第一個字元被丟掉、尾端空白被砍。**假設**:那個被丟掉的字元是某種前綴旗標。要確認得看 SP 原始碼。

而且 `QUERY_EMP_NO` 的值是這樣來的(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:200-206`):

```
string data = biz.GetEMP_INFO(this.UserID);
string[] words = data.Split(',');
if (words[1] != "") QueryVDB…AddParametersRow("QUERY_EMP_NO", …, words[1]);
```

**位置取參數**:取逗號切開的第 2 段。回傳格式一改就拿不到值,而且 `data` 是空字串時 `words[1]` 會 `IndexOutOfRange`(沒有長度檢查)。若 `words[1]` 是空字串,參數不會被加,PO 端 `GetParamValue` 回空字串 → `F_TA_GET_EMPS('')` → **多半回空集合 → 查無資料**。

**與 CAS 的差別要特別記住。**`CASI001` 拿不到員工代號時是「條件整個不加 → 看到全部資料」(`cas.md §5.3`),`CRMI001` 是「條件還在但比不到 → 看不到任何資料」。**同一個機制,兩個模組的失效方向相反。**

#### (2) 五處 `> =` / `< =`(中間有空白)

| 條件 | 寫法 | 錨點 |
|---|---|---|
| 分配期別(起) | `CRM007A.ASSIGN_NO > = '…'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140` |
| 分配期別(迄) | `CRM007A.ASSIGN_NO < = '…'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:150` |
| 受益人戶號(起) | `CRM007A.BF_NO > = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:194` |
| 受益人戶號(迄) | `CRM007A.BF_NO < = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:204` |

**假設**:整段 SQL 會語法錯,被 `catch` 吞成「執行失敗,請檢查」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:507-511`)。依據是 SQL 標準與 Oracle 的詞法規則(`>` 與 `=` 之間不得有空白)。與 `cas.md §5.3` 的 8 處同源——**兩個模組的 I 畫面是同一份樣板複製的,連 bug 都一樣**。無法本機驗證,要連 DB 跑一次帶分配期別條件的查詢。

因為**分配期別是必填**,所以只要這條假設成立,`CRMI001` 就是**完全不能用**的。這一點與 CAS 那邊不同(CAS 的起迄條件是選填)。

#### (3) 最後交易日期(迄)與本次指派日期(迄)被無效化

```
if (this.udatLAST_TRN_DATE_BGN_0 != null && this.udatLAST_TRN_DATE_END_0.Value == null)
{ this.udatLAST_TRN_DATE_END_0.Value = this.udatLAST_TRN_DATE_BGN_0.Value; }
```

比較的是**控件物件**而不是 `.Value`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174`)。控件永遠不是 `null`,所以第一個分支永遠成立 → **只要「迄」是空的就被填成「起」的值,而且後面兩個 `else if` 永遠跑不到**。

其他七組起迄都寫 `.Value != null`,只有這兩組漏了。實際效果:**這兩個條件的「迄」欄位只要留空就會變成單日查詢,而不是「起日之後全部」**——但因為「起」空白時也會被複製成空白,所以只有在「填了起、沒填迄」時才看得出差異。嚴重度中(附錄 E.8)。

#### (4) `LAST_TRN_DATE_END` 抓錯參數列

```
DataModelUtility.ParametersRow Row = …Rows.Find("EXE_DATE_END");
String end_date = …FindByName("LAST_TRN_DATE_END").Value;
```

`Row` 找的是 `EXE_DATE_END`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:221`),但實際用的值取自 `LAST_TRN_DATE_END`。`Row` 這個變數在該區塊內**完全沒被用到**,所以目前無害;但如果有人照其他區塊的樣子補上 `if (Row.Opeartor == …)`,就會在 `EXE_DATE_END` 不存在時 `NullReferenceException`。複製貼上沒改乾淨(附錄 E.8)。

#### (5) 全部條件都是字串串接

20 組條件沒有一個用綁定參數,全部是 `strSQL += "AND CRM007A." + Row.Name + " = '" + Row.Value + "'"`。其中**只有一部分做了 `Replace("'", "''")`**:

| 有跳脫 | 沒跳脫 |
|---|---|
| `ASSIGN_NO_BGN` / `ASSIGN_NO_END` / `SOURCE_CODE` / `LAST_FUND_ID` / `LAST_AGENT_ID` / `LAST_AGENT_CODE` / `LAST_EMP_NO_BGN` / `LAST_EMP_NO_END` / `LAST_DEPT_TYPE` / `BASE_DEPT_TYPE` | `EXE_DATE_BGN` / `EXE_DATE_END` / `BF_NO_BGN` / `BF_NO_END` / `LAST_TRN_DATE_BGN` / `LAST_TRN_DATE_END` / `TOT_ALLOT_AMT_*` / `BAL_AMT_*` / `ASSIGN_DATE1_*` / `ASSIGN_USER_ID1` / `ASSIGN_DEPT_NO1` / `ASSIGN_EMP_NO1` / `SPC_YN` / `RESULT` / `NEXT_CONTACT_DATE_*` / `CONTACT_CODE` |

錨點:`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`(有跳脫)vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:161`(沒跳脫)。而且 `QUERY_EMP_NO` 直接串進 `F_TA_GET_EMPS('…')` 也沒跳脫(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`)。**`Replace("'", "''")` 本來就不是正確的防注入手段**,這裡連它都只做一半(附錄 E.7)。

#### (6) `ASSIGN_DEPT_NO1` 是唯一支援 `Like` 的條件

其他所有單值條件只在 `Opeartor == SQLOperator.Equal` 時才加,`ASSIGN_DEPT_NO1` 多寫了一個 `Like` 分支(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:396-399`)。**送了 `Like` 以外運算子的條件會被無聲丟掉**——例如 UI 若送 `GreaterthanEqual`,PO 這邊什麼都不加,使用者以為有限制其實沒有。

#### (7) 九張表的舊式 `(+)` 外連接寫在 `WHERE` 裡

`FROM CRM007A, BMS001A_V01 BMS001A, COD009 COD009_L, COD009 COD009_1, COD009 COD009_2, OFD081A, CTL014 A, OFD068A, OFD002 B, OFD002 C, AA_USER D, AA_USER E, MYAGENT_LIST Z`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:91-94`),外連接一律用 Oracle 的 `(+)` 語法。

注意 `CRM007A.LAST_AGENT_CODE = OFD068A.AGENT_CODE(+)` **只 join 機構代碼、沒有 join 機構區別碼**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:102`),而 `CRMB002` / `CRMB003` / `CRMB004` 的同一段 join **兩個欄位都有**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:88-89`)。**同一張表在 I 畫面與 B 畫面的機構簡稱可能不同**——`OFD068A` 的 PK 若含 `AGENT_ID`,`CRMI001` 這邊會重複列。嚴重度中(附錄 E.4)。

### 5.4 取數之後做的事

`Select` 不是把結果塞回傳進來的 VDB,而是 `xVirtualDataBase.CreateNewVDB(mModel)` 建一個新的再回傳(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:64-65`)。填之前先把 `CRM007A` 的 13 個四眼欄位設成 `DefaultValue`(§2.5),所以**查出來的每一列都帶著「登入者 + 現在時間」的假四眼資訊**。

這段是從別的畫面樣板複製來的死碼——`CRMI001` 是唯讀查詢,不會寫回 DB。但它會影響 grid 顯示:`STATUS` 欄一律顯示 `301`。

### 5.5 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 分配期別必填 | 兩欄都空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:112-113` |
| 查詢前 | 九組起迄的「起空迄有值」 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:108-191` |
| 查詢前 | 九組起迄的大小比較 | 起 > 迄 | 阻擋 | 同上 |
| 查詢前 | 「起有值迄空白」 | 成立 | **記錄不擋**(自動把迄填成起) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:109-110` |
| 查詢前 | 最後交易日期 / 本次指派日期的成對檢核 | 一律 | **過濾(無提示,判斷式錯)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174` |
| 取數 | 登入者權限(`F_TA_GET_EMPS` INNER JOIN) | 對不上 | **過濾(無提示)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:107` |
| 取數 | 五處 `> =` 語法 | 一律 | **阻擋**(假設:語法錯 → 「執行失敗」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`、`:150`、`:194`、`:204` |
| 取數 | `ASSIGN_DEPT_NO1` 以外的條件運算子非 `Equal` | 成立 | **過濾(無提示,條件不加)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:181-184` |
| 取數 | 查無資料 | 零筆 | 記錄不擋(「查無資料」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:498-500` |
| 取數 | 任何例外 | 成立 | 記錄不擋(「執行失敗,請檢查」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:507-511` |

## 6. 批次(B)與 WindowsService

```text
[圖] 五支批次畫面的觸發、檢核、寫入路徑，以及三個共同缺陷
圖中文字:① CRMB001 三條路徑共用一個畫面 / 執行鈕 → Execute / 參數走 Parameters / S_TA_CRMB001_EXCUTE / 呼叫整段被註解 空操作 / DoExp1 上傳 CSV / 事件解掛 全無檢核 / DoExp2 產 Excel / S_TA_CRMB001_GET / ② 執行前檢核（只有產生那條還活著） / DoCheck / 基金結帳／重複產生 / POST_CTL_CODE <> Y / NULL 被靜默放行 / 刪除檢核 / 整段註解 / WARNING 詢問 / UI 還在 但永不觸發 / ③ CRM007A 的一生：產生 → 調撥 → 指派 → 登錄 / CRMB001 INSERT / DATAID 綁成 ASSIGN_NO / CRMB002 UPDATE / 單位 1→2 會動四眼欄 / CRMB003 UPDATE / 業務員 1→2 不動四眼欄 / CRMB004 UPDATE / 聯絡結果 不動四眼欄 / ④ 三支的共同毛病：影響筆數被丟掉 / ExecuteNonQuery / 回傳值沒有接 / i += 1 硬寫 / B004 寫成 i = +1 / if (i == 0) throw / 永遠不成立 死碼 / 更新 0 筆也算成功 / 使用者看到執行成功 / ⑤ CRMB005：唯一會動到 CRMM003 資料的批次 / CRMB005 查重複 / PR_NAME=／MAIL_ADDR= 三值邏輯 / GetMergePrNoList / UI 用 LINQ 另組一次 / S_TA_CRMB005_EXCUTE / 不在版控 內容未知 / CRM003A 與明細 / 合併後 PR_NO 消失
```

*圖:圖 4 批次流。橘框=本模組程式碼；黑框=無原始碼（版控外的 SP）；灰虛框=被影響的資料；橘虛框=會咬人的行為。CRMB001 的「產生／刪除名單」目前是空操作——唯一會下 SQL 的那段被註解掉了。*

**本模組沒有任何 WindowsService。**`Dev/` 底下與 CRM 相關的專案只有 `Dev/ATLAS.CRM` 與 `Dev/ATLAS.CRM.Report` 兩個,沒有服務專案。五支 B 全部是 `formstyle="OneStep"` 的使用者按鈕(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`)。

### 6.1 觸發與按鈕配置

| 畫面 | 查詢鈕 | 執行鈕 | 額外鈕 | 錨點 |
|---|---|---|---|---|
| `CRMB001` | **關閉**(`ButtonSearchEnable = false`) | 開 | `DoExp1` 上傳 CSV、`DoExp2` 產出 Excel | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:63-64`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:170`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:255` |
| `CRMB002` | 開 | 開 | — | — |
| `CRMB003` | 開 | 開 | — | — |
| `CRMB004` | 開 | 開 | — | — |
| `CRMB005` | 開(執行模式下鎖住查詢欄) | 開 | — | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:188-205` |

### 6.2 `CRMB001` — 名單產生 / 刪除 / 上傳

這支有三條互不相干的路徑,共用同一個畫面:

| 路徑 | 入口 | 走哪支 PO 方法 | 現況 |
|---|---|---|---|
| A 產生 / 刪除名單 | 「執行」鈕 | `Execute`(參數走 `Parameters`) | **SP 呼叫整段被註解,什麼都不做** |
| B 上傳 CSV 名單 | `DoExp1` | `Execute`(資料走 `DataEntity.CRM007A`) | 可用 |
| C 產出客戶名單 Excel | `DoExp2` | `GetReportData` → `S_TA_CRMB001_GET` | 可用 |

`Execute` 靠一個 `if` 分流(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:78`):

```
if (model.Utility.Parameters.Count == 0 && model.DataEntity.CRM007A.Count > 0)
```

參數是空的且有資料列 → 走 CSV 上傳的 INSERT;否則**走完 try 區塊什麼都不做**,因為底下那段 SP 呼叫是註解(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`)。而 `Result` 在 `:77` 被 `Clear()` 之後沒有再塞任何一列,所以畫面拿到的是空的結果集合。

**路徑 A 的檢核還完整地留著**,使用者會覺得「有檢核就是有在做事」:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | — | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:84-89` |
| 執行前(PO) | 該結算日有基金尚未結帳 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:261-280` |
| 執行前(PO) | (產生)該結算日已有名單 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296-300` |
| 執行前(PO) | (刪除)該結算日沒有名單可刪 | — | **整段被註解** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-306` |
| 執行前(PO) | (刪除)名單已有聯絡日期,詢問是否全刪 | — | **整段被註解** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:311-332` |
| 執行前(UI) | 上一條的 `WARNING` 參數 | 永遠不存在 | **詢問(死碼)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128-136` |

**「尚未結帳」那條有 Oracle 三值邏輯的問題。**

```
SELECT DISTINCT FUND_ID FROM OFD303A
 WHERE CTL_DATE <= :END_DATE AND POST_CTL_CODE <> 'Y'
```

`POST_CTL_CODE` 是 `NULL` 時,`NULL <> 'Y'` 的結果是 `UNKNOWN` 不是 `TRUE`,該列**被靜默排除**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265`)。也就是**從來沒被設定過結帳旗標的基金,會被當成已結帳放行**。與 `cas.md` 附錄 E.7 記的 `CASB001_PO.cs:214` 是同一類缺陷,嚴重度高(附錄 E.2)。

#### CSV 上傳(路徑 B)

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | `OpenFileDialog`,只接 `*.csv` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:172-177` |
| 2 | **把 `BeforeExecuteButtonClicked` 事件解掛** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:185` |
| 3 | 讀第一行(標題)丟掉;空白就 `return` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:191` |
| 4 | 逐行 `Split(',')`,**欄數 < 17 或第一欄空白就 `break`** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:192-194` |
| 5 | 17 欄依位置對映到 `CRM007A` 的欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:196-230` |
| 6 | 有資料就 `DoExecute()` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:234-237` |
| 7 | `finally` 把事件掛回去 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:246` |

四個要命的地方:

1. **第 2 步解掛事件,等於這條路徑完全沒有檢核。**結帳檢查、重複產生檢查全部跳過。上傳的名單可以撞到同一個 `ASSIGN_NO` + `BF_NO`(靠 PK 才會擋),也可以指到任何結算日。

2. **第 4 步用 `break` 不是 `continue`。**格式壞掉的那一列之後的所有列**全部靜默丟掉**,而且畫面只會說「已上傳 N 筆」,N 是實際寫進去的筆數。使用者不會知道檔案有 500 列只進了 37 列。

3. **`Split(',')` 不處理引號。**欄位值裡有逗號就整列錯位,而錯位之後 `line.Length` 反而 ≥ 17,不會被第 4 步擋下。

4. **兩個 `catch` 只跳訊息就 `return`**,前面已經 `AddCRM007ARow` 的列雖然被 `vdb.UIView.Clear()` 清掉了,但使用者看到的訊息是「戶號欄位格式不正確」——沒有說是第幾列。

INSERT 那段本身也有兩個問題(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:107-175`):

- **`DATAID` 被綁成 `:ASSIGN_NO`。**欄位清單第一個是 `DATAID`,`VALUES` 第一個也是 `:ASSIGN_NO`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:108`、`:142-143`)。**上傳進來的每一筆,`DATAID` 都等於分配序號**,而不是 `Guid`。

- **所有參數一律綁成 `OracleDbType.Varchar2`**,包含金額(`decimal`)與日期(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:184`)。因為是逐欄跑 `Columns` 迴圈,型別資訊整個被丟掉。

還有一個隱形的耦合:INSERT 的參數名來自 `DataTable` 的欄位名,而上面那 26 行 `Columns.Remove(...)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:80-105`)決定了哪些欄位會被綁。**`CRMB001Model.xsd` 加一個欄位,這段 INSERT 就會多綁一個 SQL 裡沒有的參數 → `ORA-01036`。**

### 6.3 `CRMB002` / `CRMB003` / `CRMB004` — 三支調撥 / 指派 / 登錄

三支的結構完全一樣:查詢 → 勾選 → 執行逐列 UPDATE。

| 面向 | `CRMB002` 單位調撥 | `CRMB003` 業務員指派 | `CRMB004` 聯絡結果登錄 |
|---|---|---|---|
| 查詢是否受 `F_TA_GET_EMPS` 限制 | **否** | **是** | **否** |
| 查詢必填 | 分配期別 + 已指派歸類(轉出) | 分配期別 | 分配期別 |
| 執行必填 | 已指派歸類(轉入) + 部門代碼(轉入) | 轉入業務員 + 部門代碼 | 無(欄位在 grid 裡) |
| UPDATE 哪些欄 | `ASSIGN_*1` → `ASSIGN_*2`,`ASSIGN_DEPT_NO1` 換新值,`ASSIGN_USER_ID1` / `ASSIGN_EMP_NO1` 清空 | 同左,但 `ASSIGN_USER_ID1` / `ASSIGN_EMP_NO1` 填新值 | `NEXT_CONTACT_DATE` / `RESULT` / `CONTACT_CODE` / `CONTACT_COMM` |
| 有沒有動四眼欄位 | **有**(`UPDATEID` / `UPDATEDATE` / `VERIFYID` / `VERIFYDATE`) | **沒有** | **沒有** |
| 錨點 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:196-211` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:205-216` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:182-189` |

**三支都繞過 EVA 引擎直接 UPDATE。**`CRM007A` 的資料從頭到尾沒有走過四眼流程(§2.5),所以這不算「破壞狀態機」,但 `CRMB002` 把 `VERIFYID` / `VERIFYDATE` 蓋成執行者、另外兩支完全不動任何時戳,**三支對「誰在什麼時候改了這筆」的紀錄方式不一致**。

#### 三支共同的三個缺陷

| 缺陷 | 說明 | 錨點 |
|---|---|---|
| 影響筆數被丟掉 | `m_db.ExecuteNonQuery(cmd, tran);` 的回傳值沒有接,下一行硬寫 `i += 1`(`CRMB004` 是 `i = +1`),所以 `if (i == 0) throw` 是死碼。**更新 0 筆也算成功** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:226-233`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:207-214` |
| `catch` 直接 `tran.Rollback()` 沒判 null | `BeginTransaction()` 本身失敗時 `tran` 是 `null` → 真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:237`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:243`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:224` |
| 查無資料回空訊息 | `AddResultRow(false, 0, "")`,使用者看到的是空白對話框 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:159`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:168`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:147` |

#### 三支不一致的地方

| 面向 | 差異 | 錨點 |
|---|---|---|
| `BF_NO` 的綁定型別 | `CRMB002` 綁 `Int32`,`CRMB003` / `CRMB004` 綁 `Varchar2`——同一欄三支兩種型別 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:217` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:224` |
| 「已指派」的判斷 | `CRMB002` 用 `DECODE(ASSIGN_DEPT_NO1, NULL,'N', ' ','N', 'Y')`(空白也算未指派);`CRMB003` 用 `DECODE(ASSIGN_EMP_NO1, NULL,'N','Y')`(**空白算已指派**) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:114` |
| 基金表 | `CRMB002` join `OFD081V`,`CRMB003` / `CRMB004` join `OFD081A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:80` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:87` |
| 執行者從哪來 | `CRMB002` 從參數 `USER_ID`(UI 傳);`CRMB003` 從 `model.Utility.PermissionInfo[0].UserID` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:190` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:197` |
| 排序 `switch` 有無 `default` | 三支都**沒有**,`SORT_ORDER` 不是 `0`–`5` 就完全沒有 `ORDER BY` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` |
| 轉入 = 轉出的檢核 | `CRMB002` **被註解**(2016-08-16「轉出與轉入應可為同一部門」);`CRMB003` 還活著 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:258-262` |

#### `CRMB003` / `CRMB004` 的登入者欄位鎖定

兩支的 `GetDefault` 有一段**逐字相同**的 SQL(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:286-314` 與 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:268-296`),用 `COD009` + `SAL051` + `OFD002` 取登入者的員工代號、部門、職級,然後:

| `SAL_CD` | 效果 | 錨點 |
|---|---|---|
| `A` 或 `B`(主管) | 清空員工與部門的預設值,**解鎖兩個欄位** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348-358` |
| `C`(業務員) | `xIS_LOCK_EMP = true`——**但它上面兩行已經是 `true` 了,這個 `if` 什麼都沒做** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345` |
| 空白 / 其他 | 兩個欄位都鎖 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:335-338` |

三個〔客戶特定〕的寫死值:

- `TRANSLATE(NVL(SAL051.SAL_CD,'Z'), 'BCADEFZ', '9876540')` — 把職級碼翻成排序碼,**`B` 最大、`Z` 最小**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:298`)。

- `CASE WHEN LENGTH(OFD002.DEPT_NO) = 3 THEN OFD002.DEPT_NO || '01' ELSE OFD002.DEPT_NO END` — 三碼部門自動補 `'01'`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:291-296`)。

- `SUBSTR(SAL051.SAL_DEPT_NO, 1, 3)` — 取直銷部門前三碼當業務部門(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:305`)。

而且這段 SQL **把登入者代號用 `string.Format` 串了兩次**(`'{0}' AS UID_CODE` 與 `COD009.UID_CODE = '{0}'`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:300`、`:307`)。

`CRMB003` 的 UI 還有一條依職級的檢核:**主管(`SAL_CD == "A"`)查詢時必須填「指派單位別(轉出)」**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:198-201`)。註解列了 8 條應有的檢核(編號 1–8),**實作的只有 1、2、3、5、8,第 4 與第 7 條只留註解**(第 7 條還寫了「PS: Searcher已擋住不給選用,pass」)。

### 6.4 `CRMB005` — 重複潛在客戶合併

#### 查詢

查 `CRM003A`(`USAGE = '1'`)裡「有另一筆同姓名 + 同地址」或「有另一筆同姓名 + 同統編」的潛在客戶:

```
AND EXISTS (SELECT * FROM CRM003A OTHER
             WHERE OTHER.PR_NO <> CRM003A.PR_NO
               AND OTHER.PR_NAME = CRM003A.PR_NAME
               AND OTHER.MAIL_ADDR = CRM003A.MAIL_ADDR)
```

三個問題:

1. **Oracle 三值邏輯。**`PR_NAME`、`MAIL_ADDR`、`ID_NO` 任一為 `NULL` 時,`=` 的結果是 `UNKNOWN`,該組**靜默不算重複**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:91-107`)。在 Oracle 裡空字串就是 `NULL`,所以**地址空白的那一批重複客戶永遠找不出來**。嚴重度高(附錄 E.2)。

2. **`merge_type` 的 `if / else if` 沒有 `else`。**不是 `"1"` 也不是 `"2"` 時,`EXISTS` 條件與 `ORDER BY` **一起消失**,查詢會回傳**全部** `USAGE = '1'` 的潛在客戶,而畫面會把它們全部當成「重複清單」顯示(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:89-107`)。目前 UI 的選項只有 1 / 2,所以踩不到,但沒有任何防護。

3. **查詢前檢核區塊是空的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:80-84`),四個查詢欄位全部可留白 → 掃全表。

#### 合併

UI 端 `GetMergePrNoList` 把勾選那一列當成「存續序號」,在畫面資料裡用 LINQ 分組找出同組的其他序號,組成 `存續|其他1|其他2` 的字串送給 SP(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:213-260`)。

**分組的鍵與 SQL 的條件不是同一套:**

| 層 | 怎麼判「同一組」 | 錨點 |
|---|---|---|
| SQL(挑出重複) | `OTHER.PR_NAME = CRM003A.PR_NAME AND OTHER.MAIL_ADDR = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` |
| UI(組合併清單) | `(PR_NAME + "_" + MAIL_ADDR).Trim()` 當 group key | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:235-241` |

`.Trim()` 只砍整串的頭尾,**中間那個 `_` 前後的空白不會被砍**。姓名尾端有空白時,SQL 的 `=` 在 Oracle 的 `VARCHAR2` 語意下會視為不同(`'A ' <> 'A'`),UI 這邊也是不同——兩邊碰巧一致。但如果哪天 SQL 改成 `TRIM(...) =`,UI 這邊就對不上了。

實際的合併動作全在 `S_TA_CRMB005_EXCUTE` 裡,**不在版控內**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:156`)。CRM 這邊只負責挑名單、組字串。

### 6.5 與 M 畫面的關係

| B 畫面 | 動到哪張表 | 對應的 M 畫面 | 會不會打架 |
|---|---|---|---|
| `CRMB001` / `CRMB002` / `CRMB003` / `CRMB004` | `CRM007A` | **無**(`CRM007A` 沒有 M 畫面) | 不會 |
| `CRMB005` | `CRM003A` 與其明細(由 SP 決定) | `CRMM003` | **會**——合併會讓某些 `PR_NO` 消失或被改掛,而 `CRMM003` 正在編輯的那筆可能就是被合併掉的 |

`CRMB005` 的合併是**唯一一個會動到 `CRMM003` 主檔的批次**,而且它繞過四眼(直接進 SP)。合併之後:

- 被合併掉的 `PR_NO` 在 `CRMM003` 查不到(或查到的是存續那筆)。

- `CRM006A` / `CRM004A` 的明細如果被改掛到存續 `PR_NO`,**`CALLIN_SRNO` / `REQ_SRNO` 可能撞號**——SP 有沒有處理這件事,repo 內看不到。**建議在合併前後各跑一次 `CRM006A` 的 PK 重複檢查。**

### 6.6 卡控總表

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `CRMB001` | 執行前 | 框架必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:84-89` |
| `CRMB001` | 執行前 | 該結算日有基金未結帳 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:274-280` |
| `CRMB001` | 執行前 | 同上,但旗標為 `NULL` | 成立 | **過濾(無提示,三值邏輯)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265` |
| `CRMB001` | 執行前 | 產生:該日已有名單 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296-300` |
| `CRMB001` | 執行前 | 刪除:無名單可刪 / 已有聯絡資訊 | — | **記錄不擋**(整段註解) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-332` |
| `CRMB001` | 執行 | 產生 / 刪除實際動作 | 一律 | **記錄不擋**(SP 呼叫被註解,無任何訊息) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214` |
| `CRMB001` | 上傳 CSV | 全部檢核 | 一律 | **過濾(無提示,事件被解掛)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:185` |
| `CRMB001` | 上傳 CSV | 欄數 < 17 或首欄空白 | 成立 | **過濾(無提示,`break` 丟掉後續全部)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:194` |
| `CRMB001` | 上傳 CSV | 戶號 / 金額格式 | 轉型失敗 | 阻擋(整批放棄) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:199-206`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:218-226` |
| `CRMB002` | 查詢前 | 分配期別 + 已指派歸類(轉出)必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:156-157` |
| `CRMB002` | 查詢前 | 兩組金額起迄成對與大小 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:170-204` |
| `CRMB002` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:214-217` |
| `CRMB002` | 執行前 | 轉入單位不可等於轉出單位 | — | **記錄不擋**(2016 起被註解) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` |
| `CRMB003` | 查詢前 | 分配期別必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:180` |
| `CRMB003` | 查詢前 | 主管(`SAL_CD = 'A'`)必須填轉出單位 | 未填 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:197-202` |
| `CRMB003` | 查詢 | `F_TA_GET_EMPS` 的 INNER JOIN | 對不上 | **過濾(無提示)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:98` |
| `CRMB003` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:252-256` |
| `CRMB003` | 執行前 | 轉入業務員不可等於轉出業務員 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:258-262` |
| `CRMB003` | 執行前 | 轉入業務員不可為離職員工 | — | **記錄不擋**(只有註解,靠下拉擋) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:246-247` |
| `CRMB004` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB004.cs:206-210` |
| `CRMB005` | 查詢前 | (區塊是空的) | — | **記錄不擋** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:80-84` |
| `CRMB005` | 查詢 | 姓名 / 地址 / 統編為 `NULL` | 成立 | **過濾(無提示,三值邏輯)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-105` |
| `CRMB005` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:88-92` |
| `CRMB002`–`CRMB005` | 執行 | 實際影響筆數為 0 | 成立 | **記錄不擋**(硬寫 `i = 1`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227` |

## 7. 報表(R)

### 7.1 一覽

| rpt | 對應畫面 | 取數來源 | 結果集 | 主要參數 |
|---|---|---|---|---|
| `CRMR001RPS` | `CRMR001` | `S_TA_CRMR001_GET` | `CRM007A` | 分配序號、資料來源、最後交易歸屬 / 單位、指派單位 / 業務員、已指派否、受益人類別、特殊名單、兩組金額起迄、排序、**登入者員工代碼** |
| `CRMR002RPS` | `CRMR002` | `S_TA_CRMR002_GET` | `CRM007A` | 同上,但把「已指派否」換成「有無意願申購」(`RESULT`) |
| `CRMR003RPS` | `CRMR003` | `S_TA_CRMR003_GET` | `CRMR003` | 分配序號、資料來源、交易日期起迄、指派單位、**登入者員工代碼** |
| `CRMR004RPS` | `CRMR004` | `S_TA_CRMR004_GET` | `CRMR004` | 同 `CRMR003` 再加指派業務員 |
| `CRMR005RPS` | `CRMR005` | `S_TA_CRMR005_GET` | `CRMR005` | 同 `CRMR004` |
| `CRMR006RPS1` / `RPS2` / `RPS3` | `CRMR006` | `S_TA_CRMR006_GET` | `CRMR006_1` 或 `CRMR006_2` | 報表類型、分配序號、資料來源、指派單位 / 業務員、有無意願申購、再聯絡日期、聯絡結果、**登入者員工代碼** |
| `CRMR007RPS1` | `CRMR007` | `S_TA_CRMR007_GET` | `CRMR007_1` | 通話日期起迄、通話種類、潛在客戶姓名起迄、建立者、**登入者員工代碼** |
| `CRMR008RPS1` / `RPS2` | `CRMR008` | `S_TA_CRMR008_GET_1` 或 `_GET_2` | `CRMR008_1` 或 `CRMR008_2` | 索取日期起迄、索取種類、潛在客戶姓名起迄、建立者(**沒有登入者員工代碼**) |

**母體的 11 支 `.rpt` 與程式裡的 11 個 `ReportClass` 一對一,沒有孤兒、沒有缺件。**這與 CAS 那邊(19 支 rpt 有一支零引用)不同。

### 7.2 八支 PO 的共同骨架

八支 `CRMRnnn_PO.GetData` 逐行對應,只差 SP 名字與參數:

| 步驟 | 做什麼 | 錨點(以 `CRMR003` 為例) |
|---|---|---|
| 1 | `model.Utility.Result.Clear()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:50` |
| 2 | `tran = m_db.BeginTransaction()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54` |
| 3 | `GetStoredProcCommand`,`CommandTimeout = 0` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:55-57` |
| 4 | 逐個 `AddInParameter`,`OutTB` 是 `RefCursor` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:59-66` |
| 5 | `LoadDataSet(cmd, model.DataEntity, tran, 表名)` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:68` |
| 6 | (部分)`TableHelper.SetNumberToZero` 把數值 NULL 補 0 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:72` |
| 7 | `tran.Commit()`,再依筆數 `AddResultRow(true/false, 0, "")` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:74-82` |
| 8 | `catch` → `tran.Rollback()` + `AddResultRow(false, 0, string.Empty)` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:84-89` |
| 9 | `finally` → `m_db.Dispose(tran)` 或 `m_db.Dispose()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:90-95` |

**與 CAS 的三個差別:**

1. **CRM 的報表把 SP 包在明確交易裡**(第 2、7、8 步),CAS 沒有。純讀取的 SP 用交易沒有壞處,但 `tran.Rollback()` 在 `BeginTransaction()` 失敗時會 `NullReferenceException`(與 §6.3 同一類)。

2. **`CRMR001` / `CRMR002` 沒有交易**(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67`),其餘六支有。**八支裡兩支例外。**

3. **`catch` 的訊息全部是 `string.Empty`**(八支皆然,例 `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:103`)。SP 出錯時使用者拿到的是空白對話框,連「查無資料」都不是。與 `cas.md` 附錄 E.3 記的完全同型。

還有一條共同的:**八支全部 `CommandTimeout = 0`**,註解寫「此程式讓它永久跑」。使用者端沒有取消機制。

### 7.3 報表種類的三種分支寫法

| 畫面 | 分支邏輯 | 有沒有 `default` | 錨點 |
|---|---|---|---|
| `CRMR006`(UI) | `switch (rpt_type)` 三個 `case`(`"1"` / `"2"` / `"3"`) | **沒有** | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:193-204` |
| `CRMR006`(PO) | `(rpt_type == "1" \|\| rpt_type == "2") ? CRMR006_1 : CRMR006_2` | 三元式,`"3"` 落到 `_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:61-63` |
| `CRMR008`(UI) | `if (report_type == "0") … else …` | 有 `else` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:120-128` |
| `CRMR008`(PO) | `if (rpt_type == "0") … else …`,兩段各自跑一支 SP | 有 `else` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:57-125` |

**`CRMR006` 的 UI 沒有 `default`,所以報表類型若不是 1/2/3,`SetQueryParameters` 不會被呼叫 → `ReportClass` 是空的 → 伺服器端 `CRReportTransfer.TransferFileByte("")`。**目前 UI 是三選一的選項鈕,踩不到,但沒有防護。

`CRMR006` 的筆數判斷用的是 `CRMR006_1.Count + CRMR006_2.Count`(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:83`),兩張表相加——這是對的,因為只有一張會被填。`CRMR008` 則是兩段各自判各自的(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:80-91`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:112-123`)。

### 7.4 `CRMR008` 的列印後寫回

**這是八支報表裡唯一一支會寫 DB 的。**列印 / 預覽完成後,如果報表類型是 `"1"`(標籤),就把該批索取紀錄標記為已列印:

| 層 | 做什麼 | 錨點 |
|---|---|---|
| UI | `AfterPreviewOrPrintButtonClicked` 判 `REPORT_TYPE == "1"` 就打 `SetPRINT_LABEL` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:212-221` |
| PO | `UPDATE (SELECT … FROM CRM004A WHERE EXISTS (…)) SET PRINT_YN = 'Y'` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:162-188` |

三件事:

1. **這段 SQL 是本模組寫得最乾淨的一段**:全部綁定參數、用 `(:X IS NULL OR 條件)` 的可選條件寫法(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:176-181`)。在 Oracle 裡空字串等於 `NULL`,所以 `GetParamValue` 回空字串時那個條件自動失效——**這個寫法只在 Oracle 成立,換 SQL Server 會全部變成「條件永遠不成立」**。

2. **它更新的範圍與剛才印的那份報表不保證一致。**報表資料來自 SP(`S_TA_CRMR008_GET_2`),而這段 UPDATE 是自己重新算一次「每個 `PR_NO` 的最新一筆索取」。SP 的邏輯看不到,兩邊有沒有對齊無法驗證。**假設**:對齊。依據是參數清單完全相同。

3. **`UPDATE (SELECT …) SET` 這種 updatable view 的寫法要求 Oracle 能判定 key-preserved**。`EXISTS` 子句不影響這一點,所以語法上沒問題,但這是全庫少見的寫法。

`SetPRINT_LABEL` 的 `catch` 同樣是 `tran.Rollback()` 不判 null + 空訊息(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:211-215`)。

### 7.5 畫面端的檢核

| 畫面 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| `CRMR001` / `CRMR002` | 兩組金額起迄成對 + 大小 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:376-419` |
| `CRMR003` | 交易日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:220-235` |
| `CRMR004` / `CRMR005` | 同 `CRMR003` | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR004.cs:238-253` |
| `CRMR006` | **只有框架必填,沒有任何自訂檢核** | — | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:309-318` |
| `CRMR007` | 通話日期區間必填 + 起 ≤ 迄;姓名起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:247-280` |
| `CRMR008` | 索取日期區間必填 + 起 ≤ 迄;姓名起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:238-271` |

`CRMR007` / `CRMR008` 還有一個共同的自動帶值:**姓名(起)有值、姓名(迄)空白時,自動把迄填成起**(`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:95-99`),與 `CRMI001` 的起迄處理同一套。

### 7.6 登入者查詢權限:七支有、一支沒有

七支報表都會送 `QUERY_EMP_NO` 給 SP:

| 畫面 | 值從哪來 | 錨點 |
|---|---|---|
| `CRMR001` / `CRMR002` | `GetEMPInfo` 回來的 `EMP_INFO` 結果集的 `EMP_NO` 欄 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:215-216` |
| `CRMR003` / `CRMR004` / `CRMR005` / `CRMR006` / `CRMR007` | `GetEMP_INFO(this.UserID).Split(',')[1]` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:55-63` |
| **`CRMR008`** | **不送** | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:107-117`(只有 `CREATER`) |

`CRMR008` 是潛在客戶側的報表(不是指派名單側),所以沒有直銷業務員的可見範圍問題——這解釋得通。但 `CRMR007` 也是潛在客戶側的,它**有**送。**兩支同一條業務線的報表,一支有權限限制一支沒有**,要問清楚哪一個才是對的(附錄 E.4)。

`CRMR001` / `CRMR002` 用的是另一套:`GetEMPInfo` 打 PO 拿 `EMP_INFO`,取不到時 `NewEMP_INFORow()` 建一個空列(`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:56-63`),於是 `EMP_NO` 是空字串。**空字串送進 SP 之後會怎樣,取決於 SP;repo 內看不到。**

### 7.7 `.rpt` 檔的取得路徑

與 `architecture.md §6.5` 描述一致:`GetReportObject` 從用戶端傳來的 `ReportParameters[0].ReportClass` 取類別名,直接丟給 `CRReportTransfer.TransferFileByte(rpt)`(`Dev/ATLAS.CRM.Report/Source/Control/ReportControl.CRM/CRMR001_Ctl.cs:77-81`,八支逐字相同)。**伺服器不驗證用戶端傳來的類別名。**

11 支 `.rpt` 全部放在第七個專案 `Dev/ATLAS.CRM.Report/Source/CrystalReports/Report.CRM/`,以 `EmbeddedResource` 編進 `Vendor.Product.TA.Report.CRM` 組件。

### 7.8 與維護資料的關係

| 報表 | 讀的是哪張表 | 誰寫進去的 |
|---|---|---|
| `CRMR001`–`CRMR006` | `CRM007A`(經由 SP) | `CRMB001` 產生 / 上傳、`CRMB002` / `CRMB003` 指派、`CRMB004` 登錄結果 |
| `CRMR007` | `CRM006A` / `CRM0061A`(經由 SP,參數是通話日期與種類) | `CRMM003` |
| `CRMR008` | `CRM004A` / `CRM0041A`(經由 SP + 自己的 UPDATE) | `CRMM003` 寫、`CRMR008` 回寫 `PRINT_YN` |

**因為 SP 不在版控內,「報表上的數字」與「維護畫面存進去的值」之間的關係在 repo 內是斷的。**唯一看得到的一段對應是 `CRMR008` 的 `SetPRINT_LABEL`(§7.4)。

## 8. 跨模組共用

```text
[圖] 改 CRM003A、CRM001A、CRM002A、CRM007A、CRM006A、CRM0061A 會波及哪些畫面
圖中文字:CRM003A：靠 USAGE 切成兩個互不相見的世界 / CRM003A / 69 欄 四眼齊 四份 xsd / CRMM003 USAGE=1 / CRM 增刪改 / CASM001 USAGE=3 / CAS 增刪改 / TMKM001／TMKM002 / 唯讀 一處無 USAGE 條件 / CRM001A／CRM002A：CRM 維護，四個模組使用 / CRM001A CRM002A / 只有 CRMM001 寫 / BasicCRM_PO / 共用 PO SEARCHER 參數 / CLSM001 CLSM002 / CLSR001 CLSR002 唯讀 / DSMI001 DSMR007 / OFDI011 唯讀 / CRM007A：全庫三個下拉的資料來源 / CRM007A / CRMB001 產生／上傳 / GetAssignNo / 分配期別下拉 / ucAssignDeptNo / 指派單位下拉 / ucAssignEmpNo / 指派業務員下拉 / OFDI011 / 唯讀 / CRM006A／CRM0061A：CRM 寫，TMK 與 OFD 讀 / CRM006A CRM0061A / CRMM003 增刪改 / TMKM001 TMKM002 / 查統編的通話種類 / OFDI011 / join 取業務員代碼 / 覆核刪除整批 DELETE / 兩邊歷史一起不見 / 只有 CRM 用（改動只影響本模組） / CRM008A / 只有 CRMM002 / CRM004 / 只有 CRMM004 / CRM004A CRM0041A / CRMM003 + CRMR008 回寫
```

*圖:圖 5 跨模組影響面。橘框=本模組維護的表；灰虛框=本模組以外的入口或共用件；橘虛框=會咬人的行為。左邊的表只要加欄或改型別，箭頭所指的每個入口都要重編與回歸；CRM003A 的欄位定義散在四份 xsd，四份都要一起重生。*

這一章回答一個問題:**改 CRM 的表會打到誰、改別人的表會打到 CRM 哪裡。**

10 張表裡 CRM 自己的有 10 張(全部都是 CRM 開頭),但其中 5 張被別的模組讀:

| 表 | 誰也在用 | 怎麼用 | 詳見 |
|---|---|---|---|
| `CRM003A` | CAS(`CASM001` 增刪改)、TMK(`TMKM001` / `TMKM002` 唯讀) | 靠 `USAGE` 分治 | §8.1 |
| `CRM001A` `CRM002A` | 共用 PO `BasicCRM_PO`、CLS、DSM、OFD | 唯讀,當授權表 | §8.2 |
| `CRM006A` `CRM0061A` | TMK、OFD | 唯讀 join | §8.3 |
| `CRM007A` | 共用 PO `BasicCRM_PO`、共用控件、OFD | 唯讀 | §8.4 |
| `CRM008A` `CRM004` `CRM004A` `CRM0041A` | **無人** | — | — |

### 8.1 `CRM003A`:靠 `USAGE` 切成兩個互不相見的世界

| 誰 | 寫進去的 `USAGE` | 查詢時的條件 | 錨點 |
|---|---|---|---|
| `CRMM003` | `'1'` | `= '1'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `CRMB005` | 不寫(只挑名單給 SP) | `= '1'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:79` |
| `CASM001` | `'3'` | `= '3'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| `TMKM001` | 不寫 | `= '1'`(唯讀 join) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` |
| `TMKM002`(通聯總覽第二路) | 不寫 | `= '1'` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:296` |
| `TMKM002`(取姓名) | 不寫 | **無 `USAGE` 條件**(`LEFT JOIN`) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` |
| `OFDI011` | 不寫 | **無 `USAGE` 條件** | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:232`、`:248` |

**結論與 `cas.md §8.2` 一致:資料層面互不干擾,schema 層面完全共用。**從 CRM 這一側補三點 CAS 那篇沒有的:

1. **`CRMB005` 的合併會動到 `USAGE = '1'` 的資料,但合併動作在 SP 裡。**如果 SP 沒有把 `USAGE` 條件帶進去,**合併可能會誤觸 CAS 的 `USAGE = '3'` 資料**。SP 不在版控內,無法驗證。這是 CRM 這一側最需要確認的跨模組風險。

2. **`CRM003A` 的欄位定義出現在四份 xsd**,不是 `cas.md §8.2` 說的三份:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`、`Dev/ATLAS.CRM/Source/Entity/UIEntity.CRM/CRMM003View.xsd`。**四份都要同步重生。**

3. **CRM 這邊的 xsd 宣告 69 欄,CAS 那邊的 Model xsd 也是 69 欄,但掃描索引記的是 72 欄**——多出來的 3 欄來自 `CASM001View.xsd`(CAS 的畫面多帶了三個顯示欄)。**兩邊的 View 不同構,Model 同構。**

| 改什麼 | 會打到誰 |
|---|---|
| 加欄位 / 改型別 / 改長度 | **四份 xsd 都要重生**,`CRMM003` 與 `CASM001` 兩支畫面都要回歸 |
| 改 PK(`PR_NO`) | `CRMM003` 取號、`CRMM003_PO` 的四句 `DELETE`、`CRMB005` 的合併字串、`CASM001`、`TMKM001` / `TMKM002`、`OFDI011` 全打到 |
| 改 `USAGE` 的值域 | **兩個模組的可見範圍同時翻掉**,而且 `TMKM002` 取姓名那段與 `OFDI011` 根本沒有條件,會突然看到對方的資料 |
| 只改 `USAGE = '1'` 那一批資料 | 只有 CRM 與 TMK 受影響 |

### 8.2 `CRM001A` / `CRM002A`:本模組維護、四個模組使用

**這兩張表是 CRM 對外影響最大的資產,而 CRM 自己一行都不讀。**

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMM001` | **唯一的寫入者**(增刪改) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `BasicCRM_PO.GetAssignEmpNo`(共用 PO) | 有 `SEARCHER` 參數時,加一段 `EXISTS (CRM001A INNER JOIN CRM002A …)` 限制員工下拉的範圍 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:290-306` |
| `CLSM001` / `CLSM002` / `CLSR001` / `CLSR002` | 唯讀 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs` |
| `DSMI001` / `DSMR007` | 唯讀 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs` |
| `OFDI011` | 唯讀 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` |

共用 PO 那段的判定邏輯要看清楚:

```
AND EXISTS (SELECT B.* FROM CRM001A A
             INNER JOIN CRM002A B ON B.EMP_NO = A.EMP_NO
                                 AND B.AGENT_ID = A.AGENT_ID
                                 AND B.AGENT_CODE = A.AGENT_CODE
             WHERE A.EMP_NO = '<登入者>'
               AND A.AGENT_CODE = B.AGENT_CODE
               AND (A.EMP_NO = B.INQ_EMP_NO OR B.INQ_EMP_NO = 'ALL'))
```

**這段有一個怪處:`EXISTS` 子查詢與外層完全沒有關聯欄位。**它只判斷「登入者在 `CRM001A` 有沒有設定,而且該設定的 `CRM002A` 明細裡有自己或 `ALL`」——**成立時外層一筆都不濾,不成立時外層全部濾掉**。也就是這段實際上是一個「有沒有權限」的開關,不是「可以看到誰」的過濾。

**後果:`CRMM001` 裡那個精心設計的「哪個機構的哪幾位員工」在共用 PO 這邊只被當成布林值用。**這可能是刻意簡化,也可能是條件漏寫。**假設**:漏寫。依據是 `CRM002A` 的 `INQ_EMP_NO` 欄位存在的意義就是列舉可查的員工,而這段只拿它跟登入者自己比對。要確認得看 `ucAssignEmpNo` 控件實際的下拉內容。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `CRM001A` `CRM002A` 欄位 | `CRMM001Model.xsd` / `CRMM001View.xsd` 要重生;`BasicCRM_PO` 那段手寫 SQL **不會自動同步** |
| 改 `INQ_EMP_NO` 的 `'ALL'` 保留字 | 共用 PO、`CRMM001` 的自動補值、`CRMM001p0` 的預設勾選三處都要改 |
| 清掉某個員工的 `CRM001A` 資料 | 那個員工在 **CLS / DSM / OFD / CRM 報表的業務員下拉** 會整個看不到資料 |
| 改 `CRMM001` 的「自動補 `ALL`」行為 | 同上,而且是無聲的權限放寬 / 收緊 |

### 8.3 `CRM006A` / `CRM0061A`:TMK 與 OFD 讀,CRM 寫

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMM003` | 增刪改(明細) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:67-68` |
| `CRMM003`(覆核刪除) | **實體 DELETE 該客戶的全部明細** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:111-118` |
| `TMKM001` / `TMKM002` | `CRM0061A` join `CRM003A` join `COD006A`,查某統編的通話種類 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:328-331` |
| `OFDI011` | `CRM006A` / `CRM0061A` join `CRM003A` 取業務員代碼 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:232`、`:248` |
| `CRMR007` | 經由 `S_TA_CRMR007_GET`(版控外) | — |

**要注意的是覆核刪除那段。**它直接 `DELETE CRM006A WHERE PR_NO = '…'`,而 TMK 與 OFD 的畫面是靠 `CRM0061A`.`PR_NO` join 回 `CRM003A` 的。**刪一個潛在客戶會讓 TMK / OFD 那邊的歷史查詢少掉資料,而且沒有任何保護與提示。**

### 8.4 `CRM007A`:共用控件的資料來源

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMB001`–`CRMB004`、`CRMI001`、`CRMR001`–`CRMR006` | 寫 / 讀 | §6、§7 |
| `ucAssignDeptNo`(共用控件) | 「指派部門代碼,將會串接 `CRM007A` 的資料擷取部門欄位」(註解原話) | `Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignDeptNo.cs:49` |
| `ucAssignEmpNo`(共用控件) | 「屬於指派部門,將會串接 `CRM007A` 的部門代碼為查詢條件」 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignEmpNo.cs:35` |
| `BasicCRM_PO`(共用 PO) | `GetAssignDeptNo` / `GetAssignEmpNo` / `GetAssignNo` / `GetLastDeptType` / `GetLastAgentCode` 五支都讀 `CRM007A` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:127-133`、`:249-253`、`:406-413`、`:468-472` |
| `OFDI011` | 唯讀 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` |

**`CRM007A` 是全庫的「分配期別 / 指派單位 / 指派業務員」三個下拉的資料來源。**`GetAssignNo` 直接 `SELECT DISTINCT ASSIGN_NO, SOURCE_CODE, MAX(EXE_DATE) FROM CRM007A GROUP BY …`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:406-411`),所以:

- **`CRMB001` 的刪除功能一旦修好,下拉裡的期別會跟著消失。**

- **CSV 上傳一筆亂資料,分配期別下拉就多一個選項**,而且沒有任何畫面可以刪掉它(`CRMB001` 的刪除是空操作)。

### 8.5 共用的 UI 控件與下拉來源

| 控件 / 來源 | 用在哪 | 說明 |
|---|---|---|
| `ucAssignDeptNo` / `ucAssignEmpNo` | `CRMB002`–`CRMB004`、`CRMR001`–`CRMR006` | 吃 `SEARCHER` 屬性做權限過濾(§8.2) |
| `TrustAgentCodeDataSrc` | `CRMM002` 的機構 Searcher | 無原始碼,從呼叫端反推 |
| `GetDropDownDataSrc` / `GetDropDown9iDataSrc` | 各畫面的代碼下拉 | 兩套並存,`CRMM002` 同一個代碼 `445` 兩種都用到(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335`) |
| `ClientBizUtility.GetEMP_INFO` | `CRMM003`、`CRMI001`、`CRMB003`、`CRMR003`–`CRMR007` | 回傳逗號分隔字串,**全部靠位置取第 2 段**(附錄 E.6) |
| `UltraGridCheckedListManager` | `CRMM003` 的兩組大小類勾選 grid | **本模組自有**,放在 `Dev/ATLAS.CRM/Source/UI/UI.CRM/App_Code/UltraGridCheckedListManager.cs` |
| `SrNoCommentProcessor` | `CRMM003` 的跳號一覽表 | 無原始碼,從呼叫端反推;與 CAS 的 `CASM001` 用同一支 |
| `CRReportTransfer` | 八支報表的 `.rpt` 取得 | 無原始碼,從呼叫端反推 |

## 附錄 A. 資料表總表

| 表 | 欄位數(Model xsd) | 四眼欄位 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `CRM001A` | 20 | 有(全部有中文名) | CRM | `CRMM001` | — | 增刪改 |
| `CRM002A` | 19 | 有 | CRM | `CRMM001`(多筆版,也算主檔) | — | 增刪改;INSERT 是手寫的 |
| `CRM003A` | 69 | 有 | **CRM / CAS / TMK**〔共用〕 | `CRMM003` `CASM001` | — | 增刪改(限 `USAGE = '1'`);`CRMB005` 交給 SP 合併 |
| `CRM004` | 34 | 有(無中文名) | CRM | `CRMM004`(vdb 表名 `CRMM004`) | — | 增刪改 |
| `CRM004A` | 27 | 有 | CRM | — | `CRMM003` | 增刪改;`CRMR008` UPDATE `PRINT_YN` |
| `CRM0041A` | 20 | 有 | CRM | — | `CRMM003` | 增刪改 |
| `CRM006A` | 21 | 有 | CRM〔被 TMK / OFD 讀〕 | — | `CRMM003` | 增刪改 |
| `CRM0061A` | 20 | 有 | CRM〔被 TMK / OFD 讀〕 | — | `CRMM003` | 增刪改 |
| `CRM007A` | 56 | 有(`STATUS` 的 Caption 抄錯) | CRM〔被共用 PO / 控件 / OFD 讀〕 | (無 M 畫面) | — | `CRMB001` INSERT、`CRMB002`–`CRMB004` UPDATE,**全部繞過四眼** |
| `CRM008A` | 21 | 有(無中文名) | CRM | `CRMM002` | — | 增刪改 |

只讀不寫的外部表(join 進來取說明用,本模組從不寫入):

| 表 | 取什麼 | 被誰 join | join 型態 |
|---|---|---|---|
| `COD009` | 員工姓名、部門、`UID_CODE` | `CRMM001` `CRMM003` `CRMI001` `CRMB002`–`CRMB004` | `LEFT`(`CRMI001` 用 `(+)`) |
| `COD006A` | OutBound 項目、通話種類、資料種類說明 | `CRMM003` | `INNER`(OutBound 那段)/ `LEFT`(歷史那段) |
| `OFD002` | 部門名稱 | `CRMM001` `CRMI001` `CRMB002`–`CRMB004` | `LEFT` |
| `OFD068A` | 銷售機構名稱 / 簡稱 | `CRMM001` `CRMM002` `CRMI001` `CRMB002`–`CRMB004` | `LEFT` |
| `OFD081A` | 基金簡稱 | `CRMI001` `CRMB003` `CRMB004` | `LEFT` |
| `OFD081V` | 基金簡稱(**`CRMB002` 用這個,不是 `OFD081A`**) | `CRMB002` | `LEFT` |
| `OFD303A` | 基金結帳控制 | `CRMB001` 的執行前檢核 | 直接 `SELECT` |
| `CTL014` | 資料來源說明(`442`)、頻率單位(`600`) | `CRMI001` `CRMM004` | `LEFT` |
| `BMS001A_V01` | 受益人姓名 / 地址 / 電話 | `CRMI001` `CRMB002`–`CRMB004` | `LEFT`(`(+)`) |
| `TMK001A` / `TMK_BF_V` | 電訪項目與電訪人員 | `CRMM003` | `INNER`(在子查詢內) |
| `SAL051` | 直銷職級與直銷部門 | `CRMB003` `CRMB004` 的 `GetDefault` | `LEFT` |
| `TA_AA_USER` / `AA_USER` | 平台使用者中文名 | `CRMM003` `CRMI001` | `LEFT`(`(+)`) |

非實體結果集(不是資料表)共 15 個,清單見 §2.3 最後一節。

## 附錄 B. SP / Function / Trigger / View

**`DB/` 裡屬於本模組的 SP / Function / Trigger / View 是 0 支。**掃描母體(`docs/_candidates/crm.md` 第 3 節)是空表,`DB/SP/`、`DB/Function/`、`DB/Trigger/`、`DB/View/` 四個資料夾裡沒有任何檔名含 `CRM` 的檔案。

但程式確實呼叫了 **11 支版控外的 DB 物件**:

| 物件 | 類 | 被誰呼叫 | 用途 | 呼叫點錨點 |
|---|---|---|---|---|
| `S_TA_CRMB001_EXCUTE` | SP | `CRMB001` | 依規則產生 / 刪除分配名單 | **呼叫整段被註解**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-205` |
| `S_TA_CRMB001_GET` | SP | `CRMB001` 的「產出客戶名單」 | 產 Excel 用的資料 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:368` |
| `S_TA_CRMB005_EXCUTE` | SP | `CRMB005` | 合併重複潛在客戶 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:156` |
| `S_TA_CRMR001_GET` | SP | `CRMR001` | 指派單位明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67` |
| `S_TA_CRMR002_GET` | SP | `CRMR002` | 指派業務員明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR002_PO.cs:66` |
| `S_TA_CRMR003_GET` | SP | `CRMR003` | 追蹤彙總-單位別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:55` |
| `S_TA_CRMR004_GET` | SP | `CRMR004` | 追蹤彙總-業務員別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR004_PO.cs:55` |
| `S_TA_CRMR005_GET` | SP | `CRMR005` | 追蹤明細-業務員別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR005_PO.cs:55` |
| `S_TA_CRMR006_GET` | SP | `CRMR006` | 聯絡結果統計 / 明細(三合一) | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:55` |
| `S_TA_CRMR007_GET` | SP | `CRMR007` | 客戶通話記錄明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR007_PO.cs:58` |
| `S_TA_CRMR008_GET_1` / `S_TA_CRMR008_GET_2` | SP | `CRMR008` | 索取資料明細 / 標籤 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:64`、`:96` |
| `F_TA_GET_EMPS` | Function(TVF) | `CRMI001`、`CRMB003` | 回傳登入者可見的「部門+員工」清單 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:80` |

另有三個**檢視表**被 join 但不在索引內:`BMS001A_V01`(受益人)、`OFD081V`(基金)、`TMK_BF_V`(電訪戶號)。

**這 11 支 + 3 個檢視表的內容在 repo 內完全看不到。**要知道規則一到規則五怎麼篩客戶、合併怎麼處理明細撞號、`F_TA_GET_EMPS` 回傳的第一個字元是什麼,只能去 Oracle 撈 `USER_SOURCE`,或問 DBA。

**`F_TA_GET_EMPS` 是本模組最關鍵的單一外部相依**:它決定 `CRMI001` 與 `CRMB003` 使用者看得到什麼,而且是用 INNER JOIN 串的——回空集合就等於查無資料(§5.3)。

## 附錄 C. 代碼對照

`STATUS` 與本模組自訂旗標值見 §2.5,不重複。這裡補下拉選單的代碼來源編號。

| 代碼 | 來源 | 用途(取自程式上下文) | 用在哪 |
|---|---|---|---|
| `062` | `GetDropDownDataSrc` | 銷售機構區別碼 | `CRMM001` `CRMM002` |
| `445` | `GetDropDownDataSrc` / `GetDropDown9iDataSrc` | 部門歸屬種類 | `CRMM002`(**同一個代碼兩種 DataSrc**) |
| `442` | `CTL014` 的 `SOURCETYPE` | 資料來源(`SOURCE_CODE`) | `CRMI001` |
| `600` | `CTL014` 的 `SOURCETYPE` | 計算頻率單位(`FREQ_UNIT`) | `CRMM004` |
| `P5` | `COD006A` 的 `CODE_SORT` | OutBound 項目說明 | `CRMM003` |
| `1C` | `COD006A` 的 `CODE_SORT` | 通話種類代碼小類 | `CRMM003` 的歷史查詢 |
| `11` | `COD006A` 的 `CODE_SORT` | 需求資料種類代碼 | `CRMM003` 的歷史查詢 |
| `438` | `GetDropDownDataSrc` | DM寄發碼 | **`CRMM003`,已於 2020-03-30 註解** |
| `439` | `GetDropDownDataSrc` | 寄發廣告EMAIL | **同上** |

**兩件要記住的:**

1. **同一個代碼分類 `445` 在 `CRMM002` 用了兩種 DataSrc。**查詢 grid 與維護下拉用 `GetDropDown9iDataSrc`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64`),查詢條件與維護欄位用 `GetDropDownDataSrc`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335-336`)。**兩個資料來源的選項若不一致,grid 與欄位會顯示不同的文字。**

2. **`CRMM003` 的 `CALLIN_CODE` / `REQ_DATA_CODE` 的下拉不是走代碼分類,而是走自訂的大小類勾選 grid**(`UltraGridCheckedListManager`,`Dev/ATLAS.CRM/Source/UI/UI.CRM/App_Code/UltraGridCheckedListManager.cs`)。歷史查詢那邊才用 `COD006A` 的 `1C` / `11` 去翻中文。**兩邊的代碼來源不同,要一起確認。**

## 附錄 D. 掃描母體與覆蓋率

母體來源:`docs/_candidates/crm.md`(由 `atlas_scan.py --module CRM` 產生)。

| 類別 | 母體 | 本文提及 | 覆蓋率 |
|---|---|---|---|
| 畫面 | 18(B 5 / I 1 / M 4 / R 8) | 18 | 100% |
| 實體表 | 6 | 6 | 100% |
| SP / Fn / Trigger / View | 0 | —(版控外的 11 支另列於附錄 B) | — |
| `.rpt` | 11 | 11 | 100% |
| WindowsService | 0 | — | — |

**沒有未提及的物件。**但母體本身有兩處要註記:

| 項目 | 狀態 | 處置 |
|---|---|---|
| `CRM001A` `CRM002A` `CRM007A` `CRM008A` | **不在**母體的實體表清單內,但它們是本模組確實維護的實體表 | 本文在 §0.2、§2.1、附錄 A 補上,並說明掃描器為何漏掉 |
| `CRM004` 的「欄位 0」 | 母體記 0 欄 | 實際 34 欄。掃描器以 **DB 表名** 去索引 xsd 的表名,而 `CRMM004Model.xsd` 裡那張表叫 `CRMM004`,所以對不上(§0.5) |
| `CRM006A` 記 9 欄、`CRM004A` 記 10 欄 | 母體的欄位數偏低 | 實際 21 / 27 欄。掃描器的 xsd 解析只認 `type=` 屬性的欄位,**用 inline `simpleType` 宣告長度的字串欄位全被漏掉**。可用 `py -V:3.12 docs/tools/atlas_scan.py --table CRM006A` 複驗:列出來的 9 欄全是 `decimal` / `dateTime` / `base64Binary`,一個 `string` 都沒有 |

本文另外提及但不屬於 CRM 母體的物件(唯讀 join、跨模組對照或版控外),列出以免被當成漏網:

- 表 / 檢視表:`COD009` `COD006A` `OFD002` `OFD068A` `OFD081A` `OFD081V` `OFD303A` `CTL014` `BMS001A_V01` `TMK001A` `TMK_BF_V` `SAL051` `TA_AA_USER` `AA_USER`

- 畫面:`CASM001` `TMKM001` `TMKM002` `CLSM001` `CLSM002` `CLSR001` `CLSR002` `DSMI001` `DSMR007` `OFDI011` `CASI001` `CASB001` `CASM006` `DSMM001`

- 彈出視窗:`CRMM001p0` `CRMM003p0` `CRMM003p1`(母體不含 `p` 系列)

- DB 物件:附錄 B 的 11 支

## 附錄 E. 讀本文時要注意的地方

按「讀碼時會被騙的方式」分類。嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 被註解掉但外殼還在的功能

**本模組最大的一類,而且比 CAS 嚴重——這裡被註解掉的不是檢核,是主要功能本身。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| **`CRMB001` 的「產生 / 刪除名單」SP 呼叫整段被註解**,按鈕、檢核、參數組裝全部還在 | 按執行鈕什麼都不會發生,而且**沒有成功也沒有失敗訊息**(`Result` 被 `Clear()` 之後沒再塞) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`、`:77` | **高(本模組最嚴重)** |
| `CRMB001` 的「刪除時檢核有無名單可刪」被註解 | 刪除作業沒有前置檢核 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-306` | 中 |
| `CRMB001` 的「刪除時已有聯絡資訊,詢問是否全刪」被註解,但 UI 端讀 `WARNING` 參數的程式還在 | 那段詢問**永遠不會出現**,是死碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:311-332` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128-136` | 中 |
| `CRMM003` 的 `CRM004A` / `CRM0041A` 取數被加上 `WHERE 1=2` | 索取資料明細**永遠是空的**,而且沒有任何註解說明 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454` | **高** |
| `CRMM003` 的通訊地址 14 個細欄回填整段被註解 | 地址只存 `MAIL_ADDR` 一欄,郵遞區號 / 縣市 / 路名等全部不會被寫入 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:483-496` | 中 |
| `CRMM003` 的 DM寄發碼 / 寄發廣告EMAIL 下拉被註解,欄位改由拒絕行銷勾選反推 | 使用者無法直接設定這兩個欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:153-157`、`:527-542` | 低(有替代邏輯) |
| `CRMM003_PO` 的 `BuildDetailSQLString` 有一整段 130 行的舊版取數被 `/* */` 包起來 | 讀碼時會誤以為明細有「歷史模式 / 一般模式」兩條路 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:460-626` | 中 |
| `CRMM003_PO` 的 `GetOutBoundSQLString` 有一整段舊版 TMK 兩表 join 被註解 | 同上;現行版本改用 `TMK_BF_V` 檢視表 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:650-685` | 低 |
| `CRMM003_PO` 宣告了 `CRM0061A_HIS` / `CRM0041A_HIS` 兩張明細但被註解 | 兩張表在現行系統不存在 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:69`、`:72` | 低 |
| `CRMB002` 的「轉入單位不能等於轉出單位」被註解(2016-08-16) | 可以把名單轉給自己;註解說明了原因,是刻意的 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` | 低 |
| `CRMB003` 的註解列了 8 條檢核,第 4、7 兩條沒有實作 | 「轉入業務員必須輸入」「不可為離職員工」靠框架與下拉擋,程式端沒有 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:184-190`、`:246-247` | 中 |
| `CRMI001_PO` 的介面有三個方法宣告被註解(`ExecuteNonQuery` / `GetEmpNo` / `GetUidCode`),但實作還在 | 兩支 `public` 方法**呼叫不到**,是死碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:26-30`、`:529`、`:560` | 低 |
| `CRMI001` 的員工白名單檢核整段被註解,裡面的 5 個員工代號與 CAS 的 `CASI001_PO.cs:206` **完全相同** | 證明兩支 I 畫面同源;目前 CRM 這邊沒有白名單 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:444-453` | 低〔客戶特定〕 |
| `CRMM001` 的 `AfterModifyButtonClicked` / `AfterDeleteButtonClicked` 兩個事件處理器整個是空的(內容全註解) | 事件有掛但什麼都不做 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:248-277` | 低 |

### E.2 Oracle 三值邏輯造成的靜默過濾

**`欄 <> '值'` 或 `欄 = 欄` 在欄位為 `NULL` 時結果是 `UNKNOWN` 不是 `TRUE`,該列被靜默排除。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CRMB001` 的結帳檢核 `POST_CTL_CODE <> 'Y'` | **結帳旗標從沒被設定過(`NULL`)的基金會被當成已結帳放行**,名單可能在未結帳的資料上產生 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265` | **高** |
| `CRMB005` 的重複判斷 `OTHER.PR_NAME = CRM003A.PR_NAME AND OTHER.MAIL_ADDR = …` | 姓名或地址為空(Oracle 裡空字串就是 `NULL`)的重複客戶**永遠找不出來** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` | **高** |
| `CRMB005` 的第二種合併 `OTHER.ID_NO = CRM003A.ID_NO` | 統編為空的重複客戶同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:102-105` | **高** |
| `CRMM004` 的區間重疊檢核 `CUS_LV <> :CUS_LV` | `CUS_LV` 是 PK 不會為 `NULL`,目前無害;但同一段的 `HAS_MF = :HAS_MF` 若某列的旗標為 `NULL` 就比不到 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:91-92`、`:112-113` | 中 |
| `CRMB005` 的 `OTHER.PR_NO <> CRM003A.PR_NO` | `PR_NO` 是 PK,無害,但寫法同型 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:93` | 低 |

### E.3 `catch` 吞例外 / 回傳值語意錯誤

**這一類最危險,因為它讓「檢核」在系統出問題時自動放行。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `intGetSRNO` 出錯回 `-1` 並把訊息塞進 `ref sErr`,呼叫端 `SetDetailSrNo` **兩個都不檢查** | **`-1` 被當成正常批次序號寫進 `CALLIN_SRNO` / `REQ_SRNO`(PK 欄位)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047` 配 `:234-241`、`:270-276` | **高(本模組最危險)** |
| `EXIST_EMP_NO` 的 `catch` 只 `Result.Clear()` **不再 `AddResultRow`**,UI 判 `Count > 0` | 「員工已建檔」檢核靜默放行 → 重複建檔 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:554-556` | 高 |
| `IS_EXISTS` 出錯塞了訊息但**回傳 `false`**,UI 判 `== true` 才擋 | 「同種類機構重複」檢核靜默放行 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176` | 高 |
| `IsValidAdd` 出錯回 `-1`,UI 判 `i == 0` | 方向相反:出錯時會**多問一次**「是否要繼續新增」,結果安全但訊息誤導 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:980-984` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1475-1480` | 中 |
| `GetUidCode` 判了 `ds.Tables.Count > 0` 卻直接取 `Rows[0]` | 查無資料 → `IndexOutOfRange` → 被 `catch` 吞成空字串(而且這支是死碼) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:575-577` | 低 |
| 八支報表 PO 的 `catch` 都是 `AddResultRow(false, 0, string.Empty)` | **SP 出錯時使用者拿到空訊息**,連「查無資料」都不是 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:101-105` | 高 |
| `CRMB002`–`CRMB005`、六支報表 PO 的 `catch` 直接 `tran.Rollback()` **不判 null** | `BeginTransaction()` 失敗時真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:235-237`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:84-86` | 中 |
| `CRMB002` / `CRMB003` / `CRMB004` 把 `ExecuteNonQuery` 的影響筆數丟掉,硬寫 `i += 1`(`CRMB004` 寫成 `i = +1`) | `if (i == 0) throw` 是死碼,**更新 0 筆也算成功** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:207-214` | 高 |
| `CRMM003` 的覆核刪除四句 `DELETE` 也丟掉影響筆數 | 刪 0 筆也算成功 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:114-117` | 中 |
| `CRMM003` 的八個 `After*` 全部 `throw new ApplicationException("")`(空訊息) | 追不到是哪一步失敗 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:924` | 中 |
| `CRMB001` 的 `finally` 在沒有交易時直接 `m_db.Dispose()` | 釋放的是**共用的欄位物件**,同一個 PO 實例的下一次呼叫會用到已釋放的 `Database` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:222-227` | 中 |

### E.4 同一概念多套實作

| 概念 | 幾套 | 差在哪 | 錨點 |
|---|---|---|---|
| `DoValidate()` 的回傳語意 | 2 | `CRMM004` **回 `true` 代表有錯**;其餘七支畫面回 `true` 代表通過 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:54` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:366` |
| 批次序號取號 | 2 | 畫面端 `GetSRNO`(出錯跳訊息);伺服器端 `intGetSRNO`(出錯回 `-1` 照寫) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:729-785` vs `:1003-1050` |
| 「已指派」的判斷 | 2 | `CRMB002` 把空白也算未指派;`CRMB003` **空白算已指派** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:114` |
| `BF_NO` 的綁定型別 | 2 | `CRMB002` 綁 `Int32`,`CRMB003` / `CRMB004` 綁 `Varchar2` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:217` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:224` |
| 基金表 | 2 | `CRMB002` join `OFD081V`;`CRMB003` / `CRMB004` / `CRMI001` join `OFD081A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:80` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:87` |
| 機構簡稱的 join 條件 | 2 | `CRMI001` **只 join `AGENT_CODE`**;三支 B 畫面 join `AGENT_ID` + `AGENT_CODE` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:102` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:88-89` |
| 執行者身分從哪來 | 2 | `CRMB002` 從 UI 傳的 `USER_ID` 參數;`CRMB003` / `CRMB005` 從 `PermissionInfo[0].UserID` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:190` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:197` |
| 報表交易處理 | 2 | 六支包交易;`CRMR001` / `CRMR002` 不包 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54` vs `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67` |
| 登入者員工代碼怎麼取 | 2 | `CRMR001` / `CRMR002` 走 `GetEMPInfo` 打 PO;其餘六處走 `GetEMP_INFO(...).Split(',')[1]` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:56-63` vs `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:55-63` |
| 報表的查詢權限 | 2 | 七支送 `QUERY_EMP_NO`,`CRMR008` 不送 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:110` vs `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:107-117` |
| 代碼分類 `445` 的 DataSrc | 2 | `GetDropDown9iDataSrc` 與 `GetDropDownDataSrc` 並用 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335` |
| 「一群裡取第一筆」的排序 | 2 | `CRMM001` 只用三個日期;`CRMM002` 日期後再加機構欄 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:253` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:90-91` |
| 重複客戶的分組鍵 | 2 | SQL 用欄位 `=` 比對;UI 用 `(PR_NAME + "_" + MAIL_ADDR).Trim()` 當 group key | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:235-241` |
| 區間重疊的判斷 | 1(但不完整) | **新區間完全包住既有區間時判不出來**,兩個客戶等級會同時命中 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:93-94`、`:114-115` |

### E.5 寫死常數〔客戶特定〕

換站台**一定要逐條確認**。

| 寫死的東西 | 值 | 錨點 |
|---|---|---|
| `CRM003A` 的用途別 | `'1'`(CRM / TMK)/ `'3'`(CAS) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `CRM007A` 寫進去的 `STATUS` | `'301'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:163`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480` |
| 直銷職級分級 | `A` 主管 / `B` 組主管 / `C` 業務員 / `D` 助理 / `Z` 未設定 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-348`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:282` |
| 職級排序對照 | `TRANSLATE(…, 'BCADEFZ', '9876540')` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:298`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:280` |
| 三碼部門補碼規則 | `LENGTH(DEPT_NO) = 3` → 後面補 `'01'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:291-296` |
| 直銷部門取法 | `SUBSTR(SAL_DEPT_NO, 1, 3)` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:305` |
| `F_TA_GET_EMPS` 回傳值的處理 | `RTRIM(SUBSTR(DEPT_EMP_NO, 2))`——固定砍掉第一個字元 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:80` |
| `INQ_EMP_NO` / `AGENT_CODE` 的 `'ALL'` 保留值 | `'ALL'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:124` |
| CSV 上傳的欄位順序與欄數 | 固定 17 欄,依位置對映 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:194-230` |
| 被註解的 I 畫面白名單 | 5 個員工代號,與 CAS 的 `CASI001` 相同 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:448` |
| 代碼分類碼 | `P5` `1C` `11` `442` `600` `062` `445` `438` `439` | 附錄 C |

### E.6 位置取參數

「值不是從資料來的,是從**它在哪裡**推出來的」。改名字、改順序就壞,而且編譯不會報錯。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 八處把 `GetEMP_INFO` 的回傳字串用逗號切開**取第 2 段** | 回傳格式一改,`CRMI001` 與 `CRMB003` 直接查無資料、`CRMM003` 的 `EMP_NO1` 寫空白;而且沒有長度檢查,空字串會 `IndexOutOfRange` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:205`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:456`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:87`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:59` | **高** |
| `F_TA_GET_EMPS` 回傳值固定砍第一個字元 | TVF 的回傳格式改一個字就全部對不上,而且是 INNER JOIN | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79` | **高** |
| CSV 上傳靠 `line[0]`–`line[16]` 的位置對映 | 欄位順序一換就全錯,而且不會報錯(型別轉換失敗的那兩欄才會) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:196-230` | 高 |
| `CRMB001` 的 INSERT 把 `DATAID` 綁成 `:ASSIGN_NO` | 上傳的每一筆 `DATAID` 都等於分配序號,不是 `Guid` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:108`、`:142-143` | 中 |
| `CRMB001` 的 INSERT 參數來自 `DataTable` 的欄位迴圈 | **xsd 加欄位就會多綁一個 SQL 裡沒有的參數 → `ORA-01036`** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:80-105`、`:182-185` | 中 |
| `CRMM001` 手寫的 `CRM002A` INSERT 把欄位名寫死在字串裡 | xsd 重生不同步,改錯只有執行時才會炸 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:93-101` | 中 |

### E.7 SQL 層面的髒寫法

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CRMI001` 的 4 處起迄條件寫成 `> =` / `< =`(中間有空白) | **假設**整段 SQL 語法錯、被 `catch` 吞成「執行失敗」;而分配期別是必填,所以這支可能完全不能用(§5.3) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`、`:150`、`:194`、`:204` | **高** |
| `CRMM003` 的 `GetHistory_Call_Req` 用分號串兩句 `SELECT` 丟給 ODP.NET | **假設** `ORA-00911`;若成立則「客戶歷史資料」永遠是空的 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:870`、`:892`、`:897` | **高** |
| `CRMI001` 的 20 組條件全部字串串接,**只有一半做了 `Replace("'", "''")`** | SQL 注入面;`QUERY_EMP_NO` 串進 TVF 也沒跳脫 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`:161`、`:194` | 高 |
| `CRMM003` 的客戶姓名 `LIKE N'%{0}%'` 字串串接 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:339` | 高 |
| `CRMM001` 的 `EXIST_EMP_NO` 用 `string.Format` 串 `EMP_NO` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:452` | 中 |
| `CRMB003` / `CRMB004` 的 `GetDefault` 把登入者代號串進 SQL 兩次 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:300`、`:307` | 中 |
| `CRMB002` / `CRMB003` 的 `ASSIGN_DEPT_YN` / `SPC_YN` 條件用 `string.Format` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105`、`:112` | 中 |
| `CRMM003` 的覆核刪除 `DELETE {0} WHERE PR_NO = '{1}'` 串表名與值 | `PR_NO` 由系統取號,風險低但寫法髒 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:109`、`:113` | 中 |
| `CRMB002`–`CRMB004` 的 `SORT_ORDER` `switch` 沒有 `default` | 值不在 `0`–`5` 就整個沒有 `ORDER BY` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` | 低 |
| `CRMB005` 的 `merge_type` `if / else if` 沒有 `else` | 值不是 `1` / `2` 就**回傳全部潛在客戶並當成重複清單** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:89-107` | 中 |
| `CRMR006` 的 UI `switch` 沒有 `default` | `ReportClass` 會是空字串 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:193-204` | 低 |
| 十支 SP 全部 `CommandTimeout = 0` | 永不逾時,使用者端沒有取消機制 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:69` | 中 |
| `CRMM004` 的兩段檢核 `cmd` 沒有 `using`(原本的 `using` 被註解) | 命令物件不釋放 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:83-84`、`:128` | 低 |
| `CRMB001` 的 INSERT 把所有參數綁成 `Varchar2` | 金額與日期靠 Oracle 隱式轉型,NLS 設定一改就可能錯 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:184` | 中 |

### E.8 其他讀碼陷阱

| 陷阱 | 說明 | 錨點 |
|---|---|---|
| `CRMI001` 的兩處 `if (控件 != null)` 而不是 `if (控件.Value != null)` | 條件永遠成立,最後交易日期(迄)與本次指派日期(迄)被無聲覆寫 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174` |
| `CRMM003` 查詢檢核裡 `utxtEMAIL_0.Text` 出現兩次 | 應該有一個是 `utxtCELL_PHONE_0`,所以**只填行動電話會被擋** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:260-261` |
| `CRMI001_PO` 的 `LAST_TRN_DATE_END` 區塊 `Find("EXE_DATE_END")` | 複製貼上沒改;`Row` 沒被用到所以目前無害 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:221` |
| `CRMM003` 六條檢核的錯誤全掛在兩個 Email 控件上 | 按訊息會跳到錯誤的欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:285`、`:312`、`:326` |
| `CRMM003` 第一條查詢檢核的訊息講戶號、控件掛通話日期 | 同上 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:222-223` |
| `CRMM003` 的「統一編號資料**過多**」訊息,條件是長度 ≤ 5 | 訊息與行為相反 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530` |
| `CRMM002` 的「此類別已重複設定」訊息,條件其實不含類別欄 | 檢核比 PK 嚴格,訊息看不出來 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:154-155` |
| `CRMB004` 寫 `i = +1;`(一元正號)而不是 `i += 1;` | 結果一樣,但看起來像 typo | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:208` |
| `CRMB003` / `CRMB004` 的 `if (xSAL_CD == "C") { xIS_LOCK_EMP = true; }` | 上兩行已經是 `true`,這個分支什麼都沒做 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345` |
| `CRMM004_PO` 第二段檢核多一句 `cmd.Parameters.Clear()`,第一段沒有 | `cmd` 是剛建出來的新物件,這句沒有作用 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:116` |
| `CRMM003_Ctl` 的 `CustomTransferViewToOracleModel` 的 `default` 分支寫成 `TransferDataSet(model.DataEntity, view.UIView, …)` | **方向反了**(其他分支是 `view → model`)。目前 `Action` 參數一定存在且值在列舉內,所以踩不到 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:220` |
| `CRMM003_Ctl` 在 VDB 轉換方法裡 `new CRMM003_PO()` 直接打 DB | 繞過 `DataAccessPool` 與交易,而且每次 `DataLoad` 都會多一次連線 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:152-156` |
| 十支 `_PO` 的介面註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製沒改,與實際功能無關 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:23-25` |
| `CRMM003_PO` 建構子第一行是 `this.BeforeSelect += CRMM003_PO_BeforeSelect; ;`(多一個分號) | 無害,但顯示這段沒被審過 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:46` |
| `CRMB005_PO` 的 `Execute` 宣告了 `int i = 0` 卻完全沒用 | 死變數 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:155` |
| `CRMM003` 的「拒絕行銷」勾選框在編輯模式全部 disabled | **客戶事後要拒絕行銷,這支畫面改不了** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| `CRM002A` 的 `EMP_NO` / `INQ_EMP_NO` 兩欄 Caption 對調 | 以程式為準:`EMP_NO` 是有權限的人 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd` |
| `CRM007A` 的 `STATUS` Caption 寫成「資料識別碼」 | 那是 `DATAID` 的名字 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |
| `CRMM003Model.xsd` 五張表的 `REJECTDATE` Caption 都是「資料退回**者**」 | 應為「資料退回日期」;`CRMM001Model.xsd` 那兩張是對的 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| `CRM003A` 的 `HM_TEL_AREA` Caption 寫「公司電話區域碼」 | 應為住家 | 同上 |
| 四支 R 的 `CustomTransferSQLModelToView` 全部 `throw new NotImplementedException()` | 只支援 Oracle,沒有 SQL Server 路徑 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:255-263` |

### E.9 標「假設」的地方一覽

本文所有需要現場確認的推論,集中在這裡:

| § | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| §0.3 | 規則一到規則五的篩選邏輯全寫在 `S_TA_CRMB001_EXCUTE` 裡 | 被註解的呼叫只傳結算日與規則代碼兩個參數 | 查 SP;問 DBA |
| §1.5 | 「一期」的長度 | `CRM007A` 用 `ASSIGN_NO` 不用日期當 PK,三支 B 的預設值取最新一期 | 問使用者 |
| §2.5 | `'301'` 就是「已覆核 / 正式生效」 | CRM 與 CAS 兩個模組獨立寫死同一個值 | 反編譯 `EVAStatusCode` 或查資料庫 |
| §4.3 | `CRM004A` / `CRM0041A` 的 `WHERE 1=2` 是為了「索取頁一律新增不載入舊資料」 | 通話那組用 `CALLIN_DATE = SYSDATE` 達到類似效果 | 問使用者「開啟舊客戶時索取頁應該顯示什麼」 |
| §4.3 | `GetHistory_Call_Req` 的分號多句 SQL 會丟 `ORA-00911` | Oracle 語法規則、ODP.NET 不支援批次語句 | 連 DB 跑一次「客戶歷史資料」 |
| §5.3 | 五處 `> =` 會造成 Oracle 語法錯誤 | SQL 標準與 Oracle 詞法規則 | 連 DB 跑一次帶分配期別條件的 `CRMI001` 查詢 |
| §5.3 | `F_TA_GET_EMPS` 回傳值的第一個字元是某種前綴旗標 | 程式固定用 `SUBSTR(..., 2)` 砍掉它 | 看 Function 原始碼 |
| §7.4 | `CRMR008` 的 `SetPRINT_LABEL` 更新範圍與 `S_TA_CRMR008_GET_2` 印出來的一致 | 兩邊參數清單完全相同 | 看 SP 原始碼 |
| §7.6 | `CRMR001` / `CRMR002` 送空字串的 `QUERY_EMP_NO` 給 SP 時 SP 會當成「全部」 | 其餘畫面拿不到值時的行為是查無資料,兩者不一致 | 看 SP 原始碼 |
| §8.1 | `S_TA_CRMB005_EXCUTE` 合併時有帶 `USAGE` 條件 | 若沒帶會誤觸 CAS 的資料 | 看 SP 原始碼(**優先確認**) |
| §8.2 | 共用 PO 的 `EXISTS` 子句漏了與外層的關聯條件 | `CRM002A` 的 `INQ_EMP_NO` 存在的意義就是列舉可查員工,而該段只拿它跟登入者自己比 | 實測 `ucAssignEmpNo` 的下拉內容 |
| §3.1 | 四支 M 畫面的中文名 | 由主表欄位與彈出視窗標題推測,沒有選單表可對 | 看選單表 |
| §3.3 | 五支 B 畫面的中文名 | 由畫面標籤與 UPDATE 的欄位推測 | 看選單表 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純程式碼閱讀彙整,未執行、未連 DB。畫面中文名待選單表回填(報表中文名已取自程式);版控外的 11 支 DB 物件內容未涵蓋;掃描母體漏掉的四張表已在本文補齊。 |

由 build_doc.py v2.0.0 於 2026-09-15 10:48 產生 · 標題 133 · 圖 5 · 表格 94 · 程式錨點 579 · § 連結 84 · 引用檢查：畫面 32（缺 0） · Table 17（缺 0） · Report 11（缺 0） · 結果集 19（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
