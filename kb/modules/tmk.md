<!-- 由 tools/build_copilot_kb.py 從 modules/tmk.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS TMK 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把四張表的主鍵搞清楚,之後 §3 的清冊配 §4 起的章節就讀得動了。趕時間只讀三段:§0.2(`TMKM001` 與 `TMKM002` 到底差在哪)、§4.1 的差異總表、附錄 E(踩雷)。 **本模組的重心在報表**:14 支畫面裡 11 支是 R,配 24 份 `.rpt`,維護只有 3 支。所以 §7 寫得比 §4 長,這是刻意的。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表中文名與程式註解**推測**,待選單表回填。ATLAS 沒有把畫面中文名放進版控,14 支畫面沒有一支在非 Designer 檔裡寫出自己的中文名;唯一例外是明細 grid 的標題「電話行銷CALL OUT記錄明細檔」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.Designer.cs:1229`)與彈窗的 MessageBox 標題(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:410`)。 ⚠ **〔客戶特定〕**:專案代碼 `'A0'`、代碼分類 `'P5'` `'P9'` `'84'` `'1C'` `'15'` `'20'` `'440'` `'476'` `'482'`、通話種類前三碼 `'001'` `'004'` `'005'` `'007'`、部門 `'08201'` `'G2'` `'G11'`、銷售機構 `'08001'` `'08201'`、日期門檻 `'20200101'` 全是本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:標記的表(`CRM003A` `CRM0061A` `COD006A` `BMS001A`)由別的模組維護,TMK 幾乎只讀不寫;唯一的例外是整批匯入會往 `COD006A` 塞一列(§8.4)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`9xx` 保留段與模組地圖看 `architecture.md §9`。**不要整份讀**。跨模組的另一半在 `crm.md §8`,本文 §8 是從 TMK 這一側做的交叉驗證。平行畫面的分析方法沿用 `bbs.md §4.5`。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:TMK 管「一份外撥名單從進系統、被打電話、留下通聯紀錄,到換人接手、最後被統計成業績與報表」的整段過程。**

「TMK」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「電話行銷 / CallOut」描述它的範圍,這是從下表推出來的,不是官方名稱。

推測依據六條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `TMK001A` 是「OutBound項目」「OutBound序號」「三年內股票型基金最大申購金額」「風險屬性」;`TMK002A` 是「本次服務人員」「上次服務人員」「再聯絡否」「有效之電話行銷」「電訪重點代碼」 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:25-181`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:287-357` |
| 畫面上的中文標題 | 明細 grid 的標題是「電話行銷CALL OUT記錄明細檔」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.Designer.cs:1229` |
| 報表中文名 | 「通話紀錄統計日報表」「電話行銷聯絡結果統計表」「期間各基金業績彙總表(電訪專員別)」「TM專案名單使用狀況及績效表」「電話行銷專員定額彙總表」「電訪專員個人淨銷售月報表」「電話行銷組客戶組成表」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:192`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:234`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:244`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:185`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:214`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:138`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:193` |
| 流水號種類 | 全模組只跟框架要一種號:OutBound 序號,對應的流水號種類就叫 `TMK001A` | `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`、`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-152` |
| 名單怎麼進來 | `TMKM001` 沒有新增按鈕,名單靠一支 CSV 整批匯入(只有兩欄:戶號、員工編號),伺服端從 `BMS001A` 把客戶資料整批複製成名單 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:314-315`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:89`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:523-586` |
| 通聯原因是兩層代碼 | 大類三碼、小類六碼,小類的前三碼就是大類;報表用前三碼分「有意願」「無意願」「無法聯絡」「勿打擾」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:403`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:415`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:427` |

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主 / 明細 |
|---|---|---|---|
| A 專案外撥 | 行銷專案批次匯入名單、指派給電訪專員、逐通電話留紀錄 | `TMKM001` ＋ `TMKM001p0` ＋ `TMKM001p1` | `TMK001A` / `TMK002A` `TMK003A` `TMK0031A` |
| B AO 新開發 | 專員自己開發的客戶,一筆一筆手動建、走四眼 | `TMKM002` ＋ `TMKM002p0` ＋ `TMKM002p1` ＋ `TMKM002p2` | 同上,完全同一組表 |
| C 名單移轉 | 專員離職 / 調動時,把名下名單整批改派給另一位 | `TMKM901` | `TMK901` |
| D 報表 | 通話量、聯絡結果、業績、定額、淨銷售、客戶組成 | `TMKR001`–`TMKR010`、`TMKR901` | 全部來自版控外的 SP |

### 0.2 這模組最反直覺的一件事:`TMKM001` 與 `TMKM002` 共用**全部**的表

母體掃出兩支畫面共用完全相同的主檔 `TMK001A` 與三張明細 `TMK002A` `TMK0031A` `TMK003A`,乍看是「一份程式被複製兩次」。**不完全是。**兩支畫面被主檔上的 `OUTBND_CODE` 欄位切成兩個互不相見的世界,而且被切開的東西不只資料,連「能不能新增」都不一樣:

| 本體 | 平行版 | 共用主 / 明細 | 切分欄位 | 各自的硬條件 |
|---|---|---|---|---|
| `TMKM001` 專案外撥名單 | `TMKM002` AO 新開發客戶 | `TMK001A` / `TMK002A` `TMK003A` `TMK0031A` | `OUTBND_CODE` | `<> 'A0'` vs `= 'A0'` |

五條互相獨立的證據(§4.1 逐條展開):

1. **查詢時各自加硬條件。** `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245` 是 `AND TMK001A.OUTBND_CODE <> 'A0'`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` 是 `WHERE TMK001A.OUTBND_CODE = 'A0'`。**在 A 畫面查不到 B 畫面建的單是設計如此,不是資料掉了。**兩支的 `BuildMasterSQLString` 開頭甚至留著同一句註解「TMKM00x的查詢不會包含A0的項目」——`TMKM002` 那句是從 `TMKM001` 複製過去的,語意剛好相反卻沒改(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:203`)。

2. **新增時寫死型態值。** `TMKM002` 在新增頁把 `OUTBND_CODE` 直接設成 `"A0"` 並鎖成唯讀(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:161`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:299`),送出前再寫一次(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:392`)。`TMKM001` 的 `OUTBND_CODE` 來自整批匯入時選的專案代碼(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:75`)。

3. **能不能新增主檔不一樣。** `TMKM001` 的 `BeforeAdd` 直接 `args.Cancel = true`,註解寫「本功能不支援新增,此段為防線之一」(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:157-161`),前端也把新增 / 刪除 / 清除三顆鈕關掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:313-316`)。`TMKM002` 反過來,`BeforeAdd` 會跟框架要一個 OutBound 序號(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:141-157`)。

4. **只有 `TMKM002` 跑四眼跳號一覽表。** 七個四眼事件(`AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject`)全部掛了 `SrNoCommentProcessor`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`),`TMKM001` 一個都沒掛。

5. **typed DataSet 的形狀不同。** `TMKM001` 的 Model 有七張 DataTable,多了 `OUTBND_TOTAL`(專案總計七個計數)與 `TMK001A1`(CSV 匯入暫存);`TMKM002` 只有六張,多的是 `CRM003A`。見 §2.1。

所以三個候選解釋的答案是:

| 候選 | 判定 | 理由 |
|---|---|---|
| (a) 同一張表兩種用途的平行維護 | **✔ 就是這個** | 切分維度是「名單來源」:`<> 'A0'` 是行銷專案整批匯入的,`= 'A0'` 是專員自己開發的。兩邊資料永久共存、各自有效 |
| (b) 舊版與新版並存 | ✘ | 兩邊都在跑、都在寫同一組表;檔案編碼、語法世代、方法簽名風格也完全一致(六個檔全是 UTF-8 with BOM) |
| (c) 不同角色權限的入口 | ✘(但權限規則確實不同) | 兩支都有主管判斷,只是判斷的來源表不同:`TMKM001` 看 `TMK_MGN_V`、`COD009` 與 `TMK002A` 三路(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`),`TMKM002` 只看 `TMK_MGN_V` 加「服務人員是自己」兩路(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`) |

**維護上最重要的一句話:兩支的逐層相似度從 Control 的 0.91 到 UI 的 0.37 都有(§4.1.1 的量測),所以「改一支要不要改另一支」沒有機械答案——但事實是已經有三個地方只改了一邊(附錄 E1、E2、E3)。**

### 0.3 這模組不管什麼

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料 | BMS | `BMS001A` 只被 `LEFT JOIN` 取姓名、法代與拒絕行銷旗標,從無寫入;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:218-219`。整批匯入那次是 `SELECT … FROM BMS001A` 當來源,也不改它(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:580`) |
| 潛在客戶主檔 | CRM(寫)/ CAS(另一個世界) | `CRM003A` 只被唯讀 join,寫入者是 `CRMM003` 與 `CASM001`,見 `crm.md §8` 與本文 §8.1 |
| 客服進線通聯 | CRM | `CRM0061A` 只在通聯總覽的 `UNION ALL` 裡被讀;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:322-333` |
| 代碼檔維護 | COD | `COD006A` 是 TMK 所有下拉的來源,只讀。**唯一的例外是整批匯入會 INSERT 一列專案代碼**,見 §8.4 |
| 員工與登入者主檔 | 平台 / 人事 | `COD009`、`AA_USER`、`TMK_MGN_V` 只被 join;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:194-200`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68` |
| 申購 / 贖回交易本身 | OFD | TMK 一行都不寫。整批匯入會去 `OFD081A` `OFD221A` `OFD220A` `OFD123A` `OFD601` `OFD607A` 撈六個衍生欄位當名單的參考值(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-584`),之後就不再同步 |
| 業績、手續費、淨銷售的算法 | 版控外的 SP | 11 支報表的口徑全部在 `S_TA_TMKRxxx_GET*` 裡,repo 內查不到。**這是本模組最大的黑箱**,見附錄 B |
| 名單是誰、什麼時候該打 | 不明 | `TMK001A` 有「活動日期(起)/(迄)」與「下次可連絡日期時間」,但沒有任何程式依這兩欄派工或提醒。**假設**:靠報表與人工,依據是 repo 內沒有 B 型畫面也沒有 WindowsService(§6) |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 行銷 / 專案管理 | 用 CSV 整批匯入名單、指定專案代碼與活動日期區間 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:54-90` |
| 電訪專員(CallOut 專員) | 打電話、逐通建項次、勾通聯原因、填是否有效電訪、約下次聯絡時間 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:369-506` |
| 電訪主管 | 在 `TMK_MGN_V` 有一列就是主管:可以看全部名單;報表 `TMKR003` 另外用 `GetMasterEmpNo("G11")` 判斷 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227-228`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:226`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57-71` |
| 覆核者 | `TMKM002` 與 `TMKM901` 走四眼;`TMKM001` 只有修改,沒有新增與刪除 | 四眼流程由框架處理,見 `architecture.md §3` |

**資料層級的權限在程式裡看得到,功能層級的看不到。**功能權限由框架平台庫決定(`architecture.md §3`)。程式裡看得到的「誰不能動」有三條:

1. 主檔查詢:三路 `OR` 條件,主管 / 名單建立者或被指定員工 / 本次服務人員,任一成立才看得到(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`)。

2. 明細刪除:`TMKM001` 只能刪指派給自己的項次(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:475-481`)。

3. 明細編輯:彈窗一開就比對「本次服務人員」是不是登入者,不是就把全部欄位鎖成唯讀並關掉確定鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:281-318`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:146-170`)。

### 0.5 全域開關

repo 內**沒有**任何 TMK 專屬的設定檔開關。`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔 DataTable 與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:11`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:19`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:26` |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄、順序為何 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:12`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:20`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:27` |
| `supportedRuntime` | 宣告 `.NETFramework,Version=v4.8` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:32` |

三件要記住的:

- **三支畫面都沒有宣告 `detailtable`。**明細表完全由 PO 的 `DetailTable` 決定(§2.1),設定檔上看不出來一支畫面有幾張明細。

- **`TMKM001` 與 `TMKM002` 的結果 grid 只差一欄。**`TMKM001` 排 `EMP_NO`(員工代碼),`TMKM002` 排 `USER_ID_T`(本次服務人員)。其餘 13 欄逐字相同。這一欄就是兩支畫面對「誰負責這筆」的不同定義:專案名單綁員工代碼,AO 名單綁登入帳號。

- **`TMKM901` 的主檔 DataTable 叫 `TMKM901`(畫面代號),不是實體表名 `TMK901`。**`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:26` 與 `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36` 的 `xTableMapping("TMK901", "TMKM901")` 對得上,但寫 SQL 或做欄位搬運時兩個名字會打架。

報表側的 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App.config` 有 11 個 section,逐支登記報表畫面,內容只有 `moduleID`,沒有業務開關。

### 0.6 一眼看懂的五個縮寫

| 縮寫 | 展開(推測) | 出現在 |
|---|---|---|
| `OUTBND` | Outbound,外撥。`OUTBND_CODE` 是專案代碼、`OUTBND_NO` 是名單序號、`OUTBND_SRNO` 是同一份名單下的第幾通電話 | `TMK001A` `TMK002A` `TMK003A` `TMK0031A` `TMK901` 的前三欄主鍵 |
| `CALLIN` | 這個字很容易誤會:欄位叫 `CALLIN_DATE` / `CALLIN_CODE`,但它們記的是**外撥這一通**的日期與通聯原因,不是客戶打進來 | `TMK003A` `TMK0031A`;`CRM0061A` 那邊的 `CALLIN_CODE` 才是真的進線 |
| `USER_ID_T` / `USER_ID_L` | This / Last,本次服務人員 / 上次服務人員 | `TMK002A`;新增項次時自動把前一個項次的 `USER_ID_T` 抄成 `USER_ID_L`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:439-443`) |
| `TOPIC` | 電訪重點:`TOPIC_CODE` 取自代碼分類 `'P4'`,`TOPIC_MEMO` 是可以人工改寫的說明 | `TMK002A`;帶出說明的地方在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:269-276` |
| `EFFECT` | 有效電訪:`EFFECT_YN` 是勾選、`EFFECT_CODE` 是種類。**同一份名單只能有一個 `EFFECT_CODE`**,所以改一筆會覆蓋同名單的全部項次 | `TMK002A`;覆蓋邏輯在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447` |

名單的三段式識別碼**永遠是三欄一組**:`OUTBND_CODE` + `OUTBND_NO` + `ID_NO`。四張表的主鍵都從這三欄開始,往下再加 `OUTBND_SRNO`、`CALLIN_DATE`、`CALLIN_SEQ`、`CALLIN_CODE`(§2.2)。寫 SQL 時漏掉任何一段不會報錯,只會多撈到別人的名單。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] TMK 全景：名單的兩個來源、兩支共用同組表的維護畫面、三層通話紀錄、名單移轉，以及十一支報表
圖中文字:① 名單怎麼進來：專案名單靠 CSV 整批匯入，AO 個案靠人工一筆一筆開 / CSV 戶號＋員工編號 / TMKM001p1 整批匯入 / BatchAdd 先刪後插 / 四張表整批清掉重建 / TMKM002 人工開單 / OUTBND_CODE 寫死 A0 / COD006A 代碼檔 / 專案代碼寫進 CODE_SORT P5 / ② 名單怎麼用：兩支維護畫面共用同一組表，靠 OUTBND_CODE 是不是 A0 切開 / TMKM001 專案外撥 / 查詢條件 OUTBND_CODE <> A0 / TMKM002 AO 新開發 / 查詢條件 OUTBND_CODE = A0 / TMK001A 名單主檔 / 兩支完全共用 / ③ 一次通話留三層紀錄：項次、通話、通聯原因小類 / TMK002A 通話項次 / 本次上次服務人員 再聯絡 / TMK003A 一次通話 / 通話日期 完成碼 備註 / TMK0031A 通聯原因 / 小類代碼 COD006A 84 / CRM0061A 客服通聯 / 唯讀 COD006A 1C / ④ 名單轉手：TMKM901 把整批名單從一位專員改派給另一位 / TMKM901 勾要移轉的名單 / TMK901 是工單不是業務表 / 覆核時改 TMK002A 服務人員 / 再 MERGE 回 TMK001A 的 EMP_NO / ⑤ 產出：11 支 R 畫面、24 份 rpt，資料全部來自版控外的 SP / TMKR001 TMKR002 TMKR003 / 通話量與聯絡結果 / TMKR004 TMKR005 TMKR007 / 業績與名單使用狀況 / TMKR006 TMKR008 TMKR009 / 定額 買回 淨銷售 / TMKR010 客戶組成表 / 彙總與明細兩份 / TMKR901 定額促銷成效 / 只有 Excel 路能跑 / 13 支報表 SP / 全部不在 DB 資料夾內
```

*圖:圖 1 TMK 全景。橘框=本模組自己的入口與動作；灰虛框=借用或唯讀的外部表；黑框=沒有原始碼的 SP 或已確認的缺陷。第②排那條線就是本模組最重要的一件事：兩支維護畫面共用全部四張表，只靠 OUTBND_CODE 是不是 A0 分家。*

### 1.2 資料表關係

第二張圖畫的是五張自有表的主明細關係、三張只活在 typed DataSet 裡的結果集,以及唯讀 join 進來與只出現在 SQL 字串裡的外部表。**重點在三段主鍵一路帶到底**,以及 `TMK0031A` 那七欄主鍵——它是全模組最長的,改任何一段都會同時打到 `TMKM001` `TMKM002` `TMKM901` 三支畫面。詳細欄位表在 §2.3。

### 1.3 主要維護畫面的四眼與卡控順序

`TMKM001` 與 `TMKM002` 的四眼掛法完全不同,這是兩支最實質的差別之一:

| 階段 | `TMKM001` | `TMKM002` | `TMKM901` |
|---|---|---|---|
| 新增前 | **直接取消**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:160`) | 取 OutBound 序號並回填三張明細的 Key(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-155`) | 前端先把未勾選的列 `Delete()`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:95-99`) |
| 修改前 | 前端檢核:新增的項次有沒有勾通話記錄(詢問)(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:564-571`) | 只跑 `validatorManager1`,沒有額外檢核(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:646-659`) | 同新增(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:102-105`) |
| 更新前 | 掛了 `BeforeUpdate` 但**函式是空的**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:167-169`) | 沒掛(那一行被註解掉,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:41`) | 沒掛 |
| 覆核前 | 無 | 無 | **整段業務邏輯在這裡**:逐列改 `TMK002A` 的服務人員,再 `MERGE` 回 `TMK001A` 的員工代碼(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:154-239`) |
| 七個 After 事件 | 全部沒掛 | 全部掛 `SrNoCommentProcessor`,寫跳號一覽表(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`) | 沒掛 |

**`TMKM001` 實際上不是一支完整的四眼維護畫面,它是一支「只能改明細」的畫面。**主檔九成欄位在 `SetUIEnable` 裡被鎖成唯讀(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:283-311`),能動的只有 `TMK002A` 項次與它掛的兩張子表。

### 1.4 批次 / 報表資料流

本模組**沒有** B 型畫面也沒有 WindowsService(§5、§6),但有一條實質上的批次:`TMKM001` 工具列第二顆自訂鈕開出來的整批匯入彈窗。它的資料流是:

1. 使用者選 CSV(兩欄:戶號、員工編號)→ 讀進 `TMK001A1` 這張只存在於 typed DataSet 的暫存表(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:104-126`)。

2. 選專案代碼 → 呼叫 `CheckExists` 問伺服器這個專案有沒有資料,有就詢問「是否全數刪除」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:143-150`)。

3. 按確定 → `BatchAdd` 在一個交易裡先把四張表這個專案的資料**全部 DELETE**,再從 `BMS001A` 逐筆 INSERT 回 `TMK001A`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-655`)。

4. 如果專案名稱是新填的,順手往 `COD006A` 塞一列代碼分類 `'P5'` 的新代碼,狀態碼寫死 `'301'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623`)。

報表側固定四段鏈:R 畫面收條件 → `ReportFormProxy` 過一次 Remoting → `ReportPO` 呼叫 SP → Crystal Report 或 Excel。四段鏈的形狀與 `architecture.md §6` 描述的 R 型一致,TMK 沒有例外。

### 1.5 一日作業泳道

| 時點 | 誰 | 做什麼 | 落在哪張表 |
|---|---|---|---|
| 專案開始前 | 行銷 | CSV 整批匯入名單、指定專案代碼與活動日期區間 | `TMK001A` 全刪重建、`COD006A` 可能多一列 |
| 專案期間 | 電訪專員 | 在 `TMKM001` 查自己的名單、雙擊新增一個項次、在彈窗勾通聯原因與電訪重點 | `TMK002A` `TMK003A` `TMK0031A` |
| 專案期間 | 電訪專員 | 自己開發的客戶走 `TMKM002`,一筆一單,需覆核 | 同上,但 `OUTBND_CODE` 固定 `'A0'` |
| 隨時 | 主管 | 專員異動時用 `TMKM901` 把名下名單整批改派 | `TMK901` 當工單,覆核時才真的改 `TMK002A` 與 `TMK001A` |
| 日 / 週 | 主管 | `TMKR001` 通話紀錄統計日報表(迄日固定為起日 +6,所以其實是週報) | 版控外 SP |
| 月 | 主管 | `TMKR002` 月報、`TMKR009` 個人淨銷售月報 | 版控外 SP |
| 期間查詢 | 主管 / 專員 | `TMKR003`–`TMKR008`、`TMKR010`、`TMKR901` | 版控外 SP |

**沒有任何自動排程。**`TMKR004` 是唯一宣告成非同步報表的(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:47-51`),其餘都同步跑,而且每支 PO 都把 `cmd.CommandTimeout = 0` 註解成「此程式讓它永久跑」。

## 2. 資料模型

```text
[圖] TMK 五張自有表的主明細關係與主鍵組成、三張只存在於 typed DataSet 的結果集，以及唯讀與隱藏的外部表
圖中文字:① 本模組五張表：一主三明細，加一張跟業務無關的移轉工單 / TMK001A 名單主檔 / PK 三段 加 50 欄 / TMK002A 通話項次 / PK 三段 加 OUTBND_SRNO / TMK003A 一次通話 / PK 再加 CALLIN_DATE / TMK0031A 通聯原因小類 / PK 七欄 全模組最長 / TMK901 名單移轉工單 / PK 加 DATAID 母體 0 欄 / 三段主鍵一路帶到底 / OUTBND_CODE OUTBND_NO ID_NO / ② 只活在 typed DataSet 裡的三張結果集，沒有同名實體表 / CALLIN_RECORD / 三路 UNION ALL 的通聯總覽 / OUTBND_TOTAL / 七個計數 只有 TMKM001 有 / TMK001A1 / CSV 暫存 只有 TMKM001 有 / ③ 唯讀 join 進來的外部表：TMK 一行都不寫 / BMS001A 受益人主檔 / 姓名 法代 拒絕行銷旗標 / CRM003A〔共用〕 / USAGE 1 才是 TMK 的世界 / CRM0061A〔共用〕 / 客服通聯明細 / COD006A 代碼檔 / P5 P9 84 1C 15 20 / ④ 只出現在 SQL 字串裡的：母體與反查工具都看不到 / COD009 員工檔 / UID_CODE 對 EMP_NO / AA_USER 登入者檔 / USERID 對 USERCNAME / TMK_MGN_V 主管視圖 / 有一列就是主管 / OFD 側五張表 / 只在 BatchAdd 的 INSERT 內
```

*圖:圖 2 資料模型。橘框=主檔；白框=明細；橘虛框=不屬於業務流程的工單表〔客戶特定〕；灰虛框=唯讀 join 或只活在 typed DataSet 裡的東西；黑框=只出現在 SQL 字串內、母體與反查工具都掃不到的表。TMK0031A 的七欄主鍵是全模組最長的，改任何一段都會打到三支畫面。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

三支維護畫面的宣告:

| 畫面 | 主檔宣告 | 明細宣告 | 錨點 |
|---|---|---|---|
| `TMKM001` | `xTableMapping("TMK001A", "TMK001A")` | `TMK002A`、`TMK003A`、`TMK0031A`(注意順序:003 在 0031 前面) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:49-54` |
| `TMKM002` | `xTableMapping("TMK001A", "TMK001A")` | `TMK002A`、`TMK003A`、`TMK0031A`(順序相同) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:56-61` |
| `TMKM901` | `MasterTable.Add(xTableMapping("TMK901", "TMKM901"))` ＋ `MasterPKey.Add("DATAID")` | 無 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36-37` |

**`TMKM001` 與 `TMKM002` 的 `xTableMapping` 四行逐字相同,連 `AddNVarCharColumns` 的五行也一樣**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:56-60` vs `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:63-67`):`TMK001A` 的 `BF_NAME` / `MAIL_ADDR`、`TMK002A` 的 `TOPIC_MEMO` / `REMARK`、`TMK003A` 的 `COMMENT1` 五欄宣告成 NVARCHAR。**改其中一支的 mapping 一定要同步另一支。**

`TMKM901` 用的是 `BaseMultiRowEVADaoPO`(多筆覆核),不是 `BaseEVADaoPO`,而且 `MasterTable` 是 `Add` 不是指派——它一張工單掛 N 列名單,整批一起覆核(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:27`)。

### 2.2 主鍵與四眼欄位

從 xsd 的 `msdata:PrimaryKey` 讀:

| 表 | 主鍵欄位(依 xsd 順序) | 欄數 | 四眼欄 | 錨點 |
|---|---|---|---|---|
| `TMK001A` | `OUTBND_CODE` `OUTBND_NO` `ID_NO` | 3 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:731-736` |
| `TMK002A` | `OUTBND_CODE` `OUTBND_SRNO` `ID_NO` `OUTBND_NO` | 4 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:737-743` |
| `TMK003A` | `OUTBND_CODE` `CALLIN_DATE` `OUTBND_SRNO` `ID_NO` `OUTBND_NO` | 5 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:744-751` |
| `TMK0031A` | `OUTBND_CODE` `OUTBND_NO` `ID_NO` `OUTBND_SRNO` `CALLIN_DATE` `CALLIN_SEQ` `CALLIN_CODE` | 7 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:752-761` |
| `TMK901`(DataTable 名 `TMKM901`) | `OUTBND_SRNO` `ID_NO` `OUTBND_NO` `OUTBND_CODE` `DATAID` | 5 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:133-140` |

三件要注意的:

1. **主鍵欄位順序在四張表之間不一致。**`TMK002A` 把 `OUTBND_SRNO` 排在第二,`TMK0031A` 排在第四。順序對 DataTable 的 `Find()` 有影響,對 SQL 沒有,但讀 code 時很容易看錯。

2. **`TMK003A` 把 `CALLIN_DATE` 放進主鍵。**所以「同一個項次同一天只能有一筆通話記錄」,而且通話日期一旦存檔就不能改——程式也真的這樣做:只有新增模式才讓改通話日期(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:302-307`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:273-278`)。

3. **`TMK0031A` 的主鍵含 `CALLIN_SEQ`,但程式永遠寫 1。**註解直接寫「通訊序號在此暫無義意,固定寫1」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:530-531`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:497-498`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:312-313`)。等於一個永遠不變的主鍵欄。

四眼欄位在五張表上都是同一組 12 欄:`STATUS` `CREATEID` `CREATEDATE` `UPDATEID` `UPDATEDATE` `ENTRYID` `ENTRYDATE` `VERIFYID` `VERIFYDATE` `APPROVEID` `APPROVEDATE` `REJECTID` `REJECTDATE` `DATAFLAG`,值域見 `architecture.md §3`。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

`TMK001A`(49 欄,扣掉 14 欄四眼與稽核欄):

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `DATAID` | 資料識別碼 | string | 框架欄 |
| `OUTBND_CODE` | OutBound項目 | string | **本模組的切分鍵**,`'A0'` 是 AO 新開發 |
| `OUTBND_NO` | OutBound序號 | string | `TMKM002` 取號時填 11 位;整批匯入填 `i.ToString("D11")` |
| `ID_NO` | 統一編號 | string |  |
| `OUTBND_DATE1` | 活動日期(起) | string | 整批匯入時一次帶給整批 |
| `OUTBND_DATE2` | 活動日期(迄) | string | 同上 |
| `BASE_DATE` | 資料基準日 | string | `TMKM002` 新增時預設 AP Server 系統日 |
| `PR_NO` | 潛在客戶序號 | string | 對 `CRM003A`;**只有 `TMKM002` 用得到** |
| `BF_NO` | 受益人戶號 | decimal | 潛在客戶沒有戶號時為 NULL |
| `BF_NAME` | 姓名 | string | 宣告成 NVARCHAR |
| `BIR_DATE` | 出生日期 | string |  |
| `MAIL_ZIP` | 通訊郵遞區號 | string |  |
| `MAIL_ADDR` | 通訊地址 | string | 宣告成 NVARCHAR;`TMKM002` 存檔前會轉全形 |
| `HM_TEL_AREA` / `HM_TEL` | 住家電話區域碼 / 住家電話 | string |  |
| `OF_TEL_AREA` / `OF_TEL` | 公司電話區域碼 / 公司電話 | string |  |
| `CELL_PHONE` | 手機號碼 | string |  |
| `FAX_TEL_AREA` / `FAX_TEL` | 傳真電話區域碼 / 傳真電話 | string | 來源是 `BMS001A` 的 `FAX_TEL_AREA1` / `FAX_TEL1` |
| `EMAIL` | (xsd 沒填中文名) | string |  |
| `EMAIL_DATE` | EMAIL啟用日 | string | 整批匯入時取 `OFD607A.OPENDAY` |
| `MAX_ALLOT_AMT` | 三年內股票型基金最大申購金額 | decimal | 整批匯入時算一次,之後不再更新 |
| `AGENT_CODE` | 銷售單位 | string | 整批匯入時取最近一筆申購書的銷售機構 |
| `CUST_STYLE` | 風險屬性 | string | 代碼分類 `'15'`;整批匯入時取 `OFD123A` 最新一筆,查無給 `'00'` |
| `EMP_NO` | 員工代碼 | string | **`TMKM001` 的負責人欄**;`TMKM901` 覆核時會 `MERGE` 改它 |
| `AGENT_IN_LAW1` / `AGENT_IN_LAW_ID1` | 法定代理人1 / 法定代理人ID1 | string | 只從 `BMS001A` 讀,不落地 |
| `AGENT_IN_LAW2` / `AGENT_IN_LAW_ID2` | 法定代理人2 / 法定代理人ID2 | string | 同上 |
| `REJ_SELL_CHK` | 拒絕行銷查詢 | string | **只在 `TMKM001` 的 Model 上**,見附錄 E1 |
| `REJ_SELL_DOC` | 拒絕書面文宣 | string | 同上 |
| `REJ_SELL_WEB` | 拒絕網路文宣 | string | 同上 |
| `REJ_SELL_PHONE` | 拒絕電訪 | string | 同上。**這一欄是電訪最該看的旗標** |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:18-251`。`TMKM002` 的同一張表多兩欄少四欄:多 `PR_NAME`(潛在客戶名稱)與 `USER_ID_T`(服務人員),少四個 `REJ_SELL_*`(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:244-245`)。

`TMK002A`(33 欄):

| 欄位 | 中文名 | 型別 |
|---|---|---|
| `OUTBND_SRNO` | 項次 | decimal |
| `USER_ID_T` | 本次服務人員 | string |
| `USER_ID_L` | 上次服務人員 | string |
| `MAIL_AGAIN` | 再郵寄否 | string(代碼分類 `'476'`) |
| `RECONTACT` | 再聯絡否 | string |
| `RECONTACT_DTTM` | 再聯絡日期時間 | string(日期 8 碼 + 小時 2 碼) |
| `RECONTACT_DT` | 改聯絡時間於(日期) | string(**衍生欄,不是實體欄**) |
| `RECONTACT_TM` | 改聯絡時間於(時間) | string(同上) |
| `REMARK` | 備註 | string(NVARCHAR) |
| `EFFECT_YN` | 有效之電話行銷 | string |
| `EFFECT_CODE` | 有效代碼 | string |
| `TOPIC_CODE` | 電訪重點代碼 | string(代碼分類 `'P4'`) |
| `TOPIC_MEMO` | 電訪重點說明 | string(NVARCHAR) |
| `CUST_CLASS` | 客戶等級代碼 | string(代碼分類 `'20'`) |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:286-427`。**`RECONTACT_DT` 與 `RECONTACT_TM` 是 SQL 用 `SUBSTR` 或 `TO_CHAR` 從 `RECONTACT_DTTM` 拆出來的**,不是實體欄;兩支畫面拆法不同,見附錄 E4。

`TMK003A`(25 欄)與 `TMK0031A`(25 欄):

| 表 | 欄位 | 中文名 |
|---|---|---|
| `TMK003A` | `CALLIN_DATE` | 通話日期 |
| `TMK003A` | `READY_YN` | 完成碼(代碼分類 `'440'`,程式預設 `"Y"`) |
| `TMK003A` | `COMMENT1` | 通話記錄備註(NVARCHAR) |
| `TMK003A` | `PR_NO` / `BF_NO` | 潛在客戶序號 / 受益人戶號(從主檔抄下來) |
| `TMK0031A` | `CALLIN_DATE` | 通話日期 |
| `TMK0031A` | `CALLIN_SEQ` | 通話記錄序號(decimal,**永遠寫 1**) |
| `TMK0031A` | `CALLIN_CODE` | 通話種類代碼小類(代碼分類 `'84'`,六碼) |
| `TMK0031A` | `PR_NO` / `BF_NO` | 同 `TMK003A` |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:440-667`。

`TMK901`(DataTable `TMKM901`,母體記 0 欄是因為掃描器找不到它的 DDL):

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `Checked` | (無中文名) | boolean | **純 UI 欄**,不落地;`BuildDetailSQLString` 把它的預設值設成 true |
| `DATAID` | 資料識別碼 | string | 主鍵之一,一張工單一個值 |
| `OUTBND_CODE` `OUTBND_NO` `ID_NO` `OUTBND_SRNO` | 同前四表 |  | 指向要移轉的那一筆 `TMK002A` |
| `USER_ID_T` | 原CallOut專員 | string |  |
| `USER_ID_NEW` | 新CallOut專員 | string | 覆核時寫回 `TMK002A.USER_ID_T` |
| `USERCNAME` | Callout專員姓名 | string | join `AA_USER` 來的,不落地 |
| `TOPIC_CODE` | 分配CallOut專案 | string |  |
| `BF_NO` / `BF_NAME` | 戶號 / 客戶姓名 | decimal / string | join `TMK001A` 來的 |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:18-127`。

三張只存在於 typed DataSet、沒有同名實體表的結果集:

| 結果集 | 出現在 | 欄位 | 怎麼來的 |
|---|---|---|---|
| `CALLIN_RECORD` | 兩支 M 畫面 | `ID_NO` `TOPIC_CODE`(專案代碼)`UPDATEDATE`(通話日期)`UPDATETIME`(通話時間)`TOPIC_MEMO`(通話種類)`CREATEID`(建檔人員) | 三路 `UNION ALL`:`TMK002A` / `CRM0061A` / `TMK0031A`,見 §8.2 |
| `OUTBND_TOTAL` | **只有 `TMKM001`** | `OUTBND_CODE` `OUTBND_NUM`(專案人數)`CALL_NUM`(已Call過人數)`WILL_NUM`(有意願申購)`UNWILL_NUM`(無意願申購)`OTHER_PRD_NUM`(其他產品)`NOCONTACT_NUM`(無法聯絡)`THK_NUM`(勿打擾) | 一句 7 個純量子查詢的 SQL,見 §4.2 |
| `TMK001A1` | **只有 `TMKM001`** | `EMP_NO`(員工代碼)`BF_NO`(受益人戶號) | CSV 兩欄讀進來的暫存 |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:671-725`。**`TMKM002` 的 Model 反過來多一張 `CRM003A`(主鍵只有 `PR_NO`),但沒有任何程式填它**(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:699`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:1137-1140`),見附錄 E1。

### 2.4 與其他模組共用的表

| 表 | TMK 這側怎麼用 | 誰維護 | 詳見 |
|---|---|---|---|
| `CRM003A`〔共用〕 | 唯讀:通聯總覽帶 `USAGE = '1'`;`TMKM002` 取姓名不帶條件 | `CRMM003`(`USAGE='1'`)、`CASM001`(`USAGE='3'`) | §8.1 |
| `CRM0061A`〔共用〕 | 唯讀:通聯總覽的第二路 | `CRMM003` | §8.2 |
| `COD006A`〔共用〕 | 讀六種代碼分類;**整批匯入會 INSERT 一列 `'P5'`** | COD | §8.4 |
| `BMS001A`〔共用〕 | 唯讀:姓名、法代、四個拒絕行銷旗標;整批匯入時當名單來源 | BMS | §8.3 |
| `COD009` | 唯讀:登入帳號對員工代碼,並用離職日過濾 | 人事 / 平台 | §8.5 |
| `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 唯讀:只在整批匯入那句 INSERT-SELECT 的六個子查詢裡 | OFD | §4.2.3 |

**沒有任何別的模組讀 TMK 自己的五張表。**母體的「跨模組」欄全空,`crm.md §8` 那側也只列到 TMK 讀 CRM,沒有反向。

### 2.5 狀態碼(從程式反推,標來源)

TMK 沒有自己的業務狀態機——名單沒有「已結案 / 進行中」這種欄位。能當狀態看的只有四組代碼,全部來自 `COD006A`:

| 概念 | 欄位 | 代碼分類 | 值域(從程式反推) | 錨點 |
|---|---|---|---|---|
| 完成碼 | `TMK003A.READY_YN` | `'440'` | 程式只寫死過 `"Y"`;查詢時用 `NVL(...,'N') = 'Y'/'N'` 兩分 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:155`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:274`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:278` |
| 是否含已結案清單 | 查詢條件 `READY_YN` | `'482'` | `'Y'` / `'N'` / 空白(不過濾) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |
| 有效代碼 | `TMK002A.EFFECT_CODE` | 畫面上是 `uoptEFFECT_CODE` 選項組 | 程式只寫死過預設值 `"2"`;`TMKM002` 已註解掉的舊碼註明 `"2"` 是「新戶開發(固定)」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:392`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:456` |
| 通話種類 | `TMK0031A.CALLIN_CODE` | `'84'`(小類)/ `'P9'`(大類) | 六碼;前三碼是大類。報表側用到的前三碼見下表 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416` |

`OUTBND_TOTAL` 那句 SQL 把通話種類前三碼寫死成四個統計口徑,**這是全模組唯一能看到通話種類語意的地方**:

| 前三碼 | 統計欄 | 中文名 | 錨點 |
|---|---|---|---|
| `'001'` | `WILL_NUM` | 有意願申購 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391` |
| `'004'` | `UNWILL_NUM` | 無意願申購 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:403` |
| `'005'` | `THK_NUM` | 勿打擾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:427` |
| `'007'` | `NOCONTACT_NUM` | 無法聯絡 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:415` |
| `'004004'`(整六碼) | `OTHER_PRD_NUM` | 其他產品 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:439` |

**注意 `'004004'` 是 `'004'` 的小類**,所以「其他產品」被算在「無意願申購」裡面,兩個數字會重複計。這不一定是錯,但報表上並排時要知道它們不是互斥的。

### 2.6 兩支 M 畫面的 typed DataSet 差異一覽

| 項目 | `TMKM001` | `TMKM002` | 是否同構 |
|---|---|---|---|
| DataTable 張數 | 7 | 6 | ✘ |
| `TMK001A` 欄數 | 49 | 47 | ✘ |
| `TMK002A` / `TMK003A` / `TMK0031A` / `CALLIN_RECORD` | 33 / 25 / 25 / 7 | 33 / 25 / 25 / 7 | ✔ 逐欄相同 |
| 多出來的 | `OUTBND_TOTAL`(8 欄)、`TMK001A1`(2 欄) | `CRM003A`(69 欄,**沒有程式填它**) | ✘ |
| Model 與 View 是否同構 | ✔ | ✔ | — |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:15-725`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:15-1105`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM001View.xsd:15-729`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM002View.xsd:15-1105`。

**`TMKM002Model.xsd` 的 `CRM003A` 是整個模組最大的一張死表:69 欄、含四個 `REJ_SELL_*`,但 PO 的 `DetailTable` 沒宣告它、`BuildDetailSQLString` 沒有它的分支、UI 沒有任何控件綁它。**它多半是從 `CASM001` 的 xsd 複製過來的(`crm.md §8.1` 記錄 `CRM003A` 的欄位定義分散在四份 xsd,TMK 這份是第五份),改 `CRM003A` 的欄位時很容易漏掉。

## 3. 畫面清冊

### 3.1 維護 M(3 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `TMKM001` | 專案外撥名單維護(推測) | 齊 ＋ 兩支彈窗 | `TMK001A` | `TMK002A` `TMK003A` `TMK0031A` | 無 | 無 |
| `TMKM002` | AO 新開發客戶電話行銷維護(推測) | 齊 ＋ 三支彈窗 | `TMK001A` | `TMK002A` `TMK003A` `TMK0031A` | 無 | 無 |
| `TMKM901` | CallOut 專員名單移轉(推測) | 齊 | `TMK901` | 無 | 無 | 無 |

五支彈窗(母體不列,因為它們不是獨立畫面):

| 彈窗 | 屬於 | 用途 | 錨點 |
|---|---|---|---|
| `TMKM001p0` | `TMKM001` | 通話項次編輯 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:58-65` |
| `TMKM001p1` | `TMKM001` | CSV 整批匯入 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:28-33` |
| `TMKM002p0` | `TMKM002` | 通話記錄編輯(**舊的那一套**) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:46-53` |
| `TMKM002p1` | `TMKM002` | 潛在客戶 / 受益人挑選 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:45-51` |
| `TMKM002p2` | `TMKM002` | 通話項次編輯(**新的那一套**,對應 `TMKM001p0`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:56-63` |

**`TMKM001p1` 與 `TMKM002p1` 名字對仗但功能完全無關**(一個是 CSV 匯入、一個是客戶挑選),這是全模組最容易找錯檔的地方。

### 3.2 查詢 I

**本模組無此類畫面。**母體 `I 0`。原因見 §5。

### 3.3 批次 B

**本模組無此類畫面,也沒有 WindowsService。**母體 `B 0`、`Service 0`。原因見 §6。

### 3.4 報表 R(11 支、24 份 rpt)

| 代號 | 中文名(來自程式字面) | SP | rpt 數 | 結果集 |
|---|---|---|---|---|
| `TMKR001` | 通話紀錄 / 資料需求 / 通話通數 統計**日**報表 | `S_TA_TMKR001_GET` | 3 | `TMKR001_1` `TMKR001_2` `TMKR001_3` |
| `TMKR002` | 通話紀錄 / 資料需求 / 通話通數 統計**月**報表 | `S_TA_TMKR002_GET` | 3 | `TMKR002_1` `TMKR002_2` `TMKR002_3` |
| `TMKR003` | 電話行銷聯絡結果統計表 / 明細表一 / 通話代碼數量期間統計表 | `S_TA_TMKR003_GET_1` `_2` `_3` | 3 | `TMKR003_1A` `TMKR003_1B` `TMKR003_2` `TMKR003_3` |
| `TMKR004` | 期間各基金業績彙總表 / 明細表(電訪專員別) | `S_TA_TMKR004_GET_1` `_2` | 2 | `TMKR004T1` |
| `TMKR005` | TM專案名單使用狀況及績效表(By TM專員 / By 單位別) | `S_TA_TMKR005_GET_1` | 2 | `TMKR005T1` |
| `TMKR006` | 電話行銷專員定額 彙總 / 客戶明細 / 年度配額達成 / 扣款成功統計 | `S_TA_TMKR006_GET_1` `_2` | 5 | `TMKR006T1`–`TMKR006T4` |
| `TMKR007` | 電訪專員期間單筆銷售 手續費明細表 / 彙總表 | `S_TA_TMKR007_GET_1` | 2 | `TMKR007_1` |
| `TMKR008` | 電訪專員各期別基金買回明細表 | `S_TA_TMKR008_GET_1` | 1 | `TMKR008_1` |
| `TMKR009` | 電訪專員個人淨銷售月報表 | `S_TA_TMKR009_GET_1` | 1 | `TMKR009_1` `TMKR009_2` |
| `TMKR010` | 電話行銷組客戶組成表 彙總 / 明細 | `S_TA_TMKR010_GET_1` | 2 | `TMKR010_1` `TMKR010_2` `TMKR010_3` |
| `TMKR901` | 定額促銷活動成效(推測,程式沒給標題) | `S_TA_TMKR901_GET` | **0**(指名的檔不存在) | `TMKR901T0`–`TMKR901T4` |

合計 24 份 `.rpt`,與母體一致。詳細展開在 §7。

### 3.5 一眼看出差別的五件事

1. **11 支 R 對 3 支 M。**這是報表導向的模組:維護只是把資料存起來,價值在統計。

2. **一支 R 畫面不等於一份報表。**`TMKR001` `TMKR002` `TMKR003` 各三份、`TMKR006` 五份,靠畫面上的「報表選項」決定載哪一份 `.rpt`。

3. **每一支 R 都有「轉 Excel」第三條路**,而且 Excel 的版面是手寫在 UI 層的 `GenExcelR1`–`GenExcelR5`,跟 `.rpt` 各寫一次。改報表欄位要改兩個地方。

4. **`TMKR901` 是唯一沒有 `.rpt` 的報表畫面。**它指名 `TMKR901RPS0`,repo 裡沒有這個檔(§7.6)。

5. **查詢權限四種做法並存**:傳 `QUERY_EMP_NO`、傳 `USER_EMP_NO`、前端鎖欄位、什麼都不做(§7.8)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] TMKM001 與 TMKM002 的關係：共用四張表、逐層相似度、真正的行為差異、單邊才有的功能，以及必須同步修改的共同段落
圖中文字:① 兩支共用全部四張表，切分鍵是 OUTBND_CODE 是不是 A0 / TMKM001 專案外撥名單 / SQL 寫死 不等於 A0 / TMKM002 AO 新開發客戶 / SQL 寫死 等於 A0 / TMK001A TMK002A / TMK003A TMK0031A 全共用 / ② 逐層相似度：Control 幾乎同一份，UI 差最遠 / Control 0.91 / 只差兩支自訂方法 / FormProxy 0.72 / 一邊整批匯入一邊取指派人 / PO 0.50 / 主檔 SQL 完全不同 / UI 主檔 0.37 / 1036 行對 597 行 / ③ 真的不同：誰能新增、誰能刪明細、誰跑四眼跳號 / TMKM001 不能新增主檔 / BeforeAdd 直接 Cancel / TMKM002 新增時取序號 / 七個四眼事件寫跳號一覽表 / TMKM001 刪明細會連刪子表 / TMKM002 明細一律不准刪 / ④ 只有一邊有的東西 —— 改一支要不要同步，答案在這排 / 整批 CSV 匯入與範本下載 / 只有 TMKM001 有 / 專案總計七個計數 / 只有 TMKM001 有 / 潛在客戶序號與姓名 / 只有 TMKM002 有 / 拒絕行銷四個旗標 / M001 顯示 M002 撈了沒用 / 通話明細彈窗兩套 / TMKM002 有 p0 與 p2 兩份 / 跳號號別掛成申購書號 / TMKM002 七處全錯 / ⑤ 兩邊一模一樣、改一定要一起改的部分 / 三張明細的組 SQL 與參數拼裝 / 只差一句日期轉換寫法 / 通聯總覽三路 UNION ALL / 逐字相同 含 USAGE 條件 / 再聯絡時間 1 到 24 的檢核 / 兩邊同樣只擋 0 不擋 25 / 查詢條件與姓名 LIKE 串接 / 兩邊同樣把值直接串進 SQL
```

*圖:圖 3 兩支平行畫面。橘框=可從程式判定的差異；橘虛框=只有單邊才有的功能〔客戶特定〕；黑框=已確認的缺陷或兩邊同時錯的地方。第④排下面三格是「有人只改了一邊」的證據，第⑤排是「改一支就一定要改另一支」的清單。*

本章三支:`TMKM001` 與 `TMKM002` 是共用全部四張表的平行畫面,先用 §4.1 一次講清楚它們的關係,再各自展開(§4.2、§4.3),卡控併成一張對照表(§4.4);`TMKM901` 獨立(§4.5)。

### 4.1 `TMKM001` / `TMKM002` — 兩支共用全部四張表的平行畫面

方法沿用 `bbs.md §4.5`:把 `TMKM002` 全檔的代號代換成 `TMKM001` 後做逐行序列比對,再把「只差代號」與「真的不同」分開。

#### 4.1.1 兩支到底有多像:逐層量測

| 層 | `TMKM001` 行數 | `TMKM002` 行數 | 相同行 | 相似度 |
|---|---|---|---|---|
| UI 主檔 | 597 | 1036 | 302 | 0.370 |
| UI 項次彈窗(`p0` vs `p2`) | 574 | 533 | 268 | 0.597 |
| UI 第二彈窗(`p1` vs `p1`) | 173 | 218 | 33 | 0.169 |
| FormProxy | 71 | 56 | 46 | 0.724 |
| Control | 156 | 148 | 139 | 0.914 |
| PO | 700 | 462 | 293 | 0.504 |

**結論:Control 幾乎是同一份、UI 主檔則是兩套不同的東西。**這跟 `bbs.md §4.5.1` 那三對(全層 0.15–0.60)不一樣:BBS 是「重寫」,TMK 是「同一套骨架長出兩種前端」。三個數字要分開解讀:

- **Control 0.914**:兩支的 `BaseController` 樣板逐字相同,差的只有 `TMKM001_Ctl` 多了 `BatchAdd` / `CheckExists` 兩支自訂方法(`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM001_Ctl.cs:52-69`),`TMKM002_Ctl` 多了 `GetLAST_USERID` 與跳號一覽表的兩行 `TransferTable`(`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:52-57`、`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:77`、`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:97`)。

- **PO 0.504**:三張明細的組 SQL 與通聯總覽逐字相同,不同的全在主檔 SQL 與四眼事件。

- **UI 主檔 0.370**:`TMKM002` 多出 439 行,幾乎全是 §4.3 講的「挑客戶 → 回填十幾個欄位」那一段,`TMKM001` 完全沒有(它的客戶資料是整批匯入時就決定的)。

`p1` 那一列(0.169)**不要當成差異**:兩支的 `p1` 根本是不同功能,只是檔名撞號(§3.1)。

#### 4.1.2 真的不同的地方

| 面向 | `TMKM001`(專案外撥) | `TMKM002`(AO 新開發) |
|---|---|---|
| 主檔查詢硬條件 | `OUTBND_CODE <> 'A0'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`) | `OUTBND_CODE = 'A0'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227`) |
| 能不能新增主檔 | **不能**,`BeforeAdd` 直接取消(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:157-161`) | 能,取 OutBound 序號(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-152`) |
| 能不能刪主檔 | **不能**,前端關掉按鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:314-316`) | 能(受權限鎖控制,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:359-364`) |
| 能不能刪明細 | 能,但只能刪自己的,而且會連刪 `TMK003A` 與 `TMK0031A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:321-357`) | **一律不能**,`BeforeRowsDeleted` 無條件 `e.Cancel = true`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1025-1028`) |
| 四眼跳號一覽表 | 沒有 | 七個事件全掛(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`) |
| 主管判斷 | 三路 `OR`:`TMK_MGN_V` / `COD009` 對建立者或指定員工 / `TMK002A` 服務人員(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`) | 兩路 `OR`:`TMK_MGN_V` / 服務人員是自己(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`) |
| 主檔 join 誰 | `BMS001A`、`LAST_TMK003A`(CTE)、`TMK_MGN_V`、`COD009`、`MYTMK002A`(CTE) | `TMK002A`(INNER,限 `OUTBND_SRNO=1`)、`BMS001A`、`COD009`、`CRM003A`、`TMK_MGN_V` |
| 主檔一定要有明細嗎 | 不用(註解明講「不需要一定要有明細」,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:247`) | **要**,`JOIN TMK002A … AND TMK002A.OUTBND_SRNO=1`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:219-222`) |
| 「是否含已結案清單」查詢條件 | 有(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280`) | 沒有 |
| 專案總計七個計數 | 有,`OUTBND_TOTAL`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:354-453`) | 沒有(彈窗上七個欄位還在,但填值那段被註解掉,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:93-100`) |
| 潛在客戶 | 完全沒有 | 主軸之一:`PR_NO`、`PR_NAME`、挑選彈窗 `TMKM002p1` |
| 整批匯入 | 有,三顆自訂鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:66-68`) | 沒有 |
| 通聯記錄 grid | `ugrdCALLIN`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:265`) | `ugrdCALLIN1`,舊的 `ugrdCALLIN` 被註解掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:247-248`) |
| 項次彈窗 | 一套(`TMKM001p0`) | **兩套**(`TMKM002p0` 與 `TMKM002p2`),入口不同 |
| 取得維護資料時載通聯總覽 | 在 `AfterGetMaintainData`,連 `OUTBND_TOTAL` 一起(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:128-151`) | 在 `BeforeGetMaintainData` 的主檔分支內(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:120-126`) |

#### 4.1.3 只差代號的部分 —— 改一支就一定要改另一支

下列項目在兩支之間除了代號以外完全一致:

| 段落 | `TMKM001` | `TMKM002` |
|---|---|---|
| `xTableMapping` 與 `AddNVarCharColumns` 九行 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:49-60` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:56-67` |
| 通聯總覽三路 `UNION ALL`(含 `USAGE = '1'`、`CODE_SORT = '1C'` / `'84'`) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:303-352` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:269-319` |
| `TMK003A` 與 `TMK0031A` 的明細 SQL | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:483-508` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:339-362` |
| 姓名 `LIKE` 與再聯絡日期區間三段字串串接 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:254-263` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:236-245` |
| 被註解掉的「必須擇一填寫」查詢前檢核 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:129-139` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:100-111` |
| 被註解掉的 `AddParam` 多帶 `BF_NAME` 那一行 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:251-252` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:233-234` |
| 下次可連絡日期(起)(迄)的成對檢核與 `Leave` 自動補迄日 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:509-515`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:591-595` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:622-628`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1030-1034` |
| 再聯絡時間 1~24 的 `Validating` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:542-552` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:866-876`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:508-518` |
| 通聯原因管理器的建立(代碼分類 `"P9"` / `"84"`、`IsTopTick2`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61-64` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:62-65` |
| 項次彈窗的存檔流程(更新 `TMK002A` → `TMK003A` → 重算 `TMK0031A` 勾選) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:369-506` |
| 有效代碼覆蓋同名單全部項次 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 被註解掉的「只有第一個項次能設有效代碼」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:374-381` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:345-352` |

#### 4.1.4 已經只改了一邊的三個地方

這一段是本節的重點:程式碼本身可以證明有人只改了一邊。

| # | 現象 | `TMKM001` | `TMKM002` | 影響 |
|---|---|---|---|---|
| 1 | 四個拒絕行銷旗標 | Model 有四欄、畫面四個 checkbox 都填值(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:243-246`) | **SQL 照樣 SELECT 四欄**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:214-217`),但 Model 的 `TMK001A` 沒宣告這四欄(它們被宣告在那張沒人填的 `CRM003A` 上),控件 `Visible = false`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.Designer.cs:2016`),UI 程式一行都沒指派 | **AO 新開發畫面看不到「拒絕電訪」旗標**,但 SQL 每次都白撈四欄 |
| 2 | 再聯絡日期的拆法 | `SUBSTR(RECONTACT_DTTM,1,8)` / `SUBSTR(...,9,2)`,舊的 `TO_DATE` 版被註解掉(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:460-477`) | **還是舊的 `TO_CHAR(TO_DATE(...))` 版**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:326-331`) | `TMKM001` 那邊改過一次是為了避開 `TO_DATE` 對格式不合的值丟 `ORA-01861`;`TMKM002` 沒跟,同一批髒資料在 AO 畫面上會炸 |
| 3 | 通話項次彈窗 | 一套 `TMKM001p0` | **兩套**:`TMKM002p0`(舊,`btnCALLIN` 進去)與 `TMKM002p2`(新,雙擊 grid 進去)。`p0` 撈 `TMK003A` 不帶主鍵條件、刪 `TMK0031A` 不帶篩選(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:255-256`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:269`) | 多項次時走 `p0` 會改到別的項次的通話記錄、刪掉別的項次的通聯原因,見附錄 E3 |

**改一支要不要同步另一支?分三類回答:**

| 類別 | 答案 | 清單 |
|---|---|---|
| 主檔 SQL、四眼事件、能不能新增刪除、潛在客戶、整批匯入、專案總計 | **不用同步**,這些本來就是兩支的差異 | §4.1.2 整張表 |
| `xTableMapping`、三張明細的 SQL、通聯總覽、項次彈窗存檔流程、共同檢核 | **一定要同步**,它們逐字相同 | §4.1.3 整張表 |
| `TMK001A` `TMK002A` `TMK003A` `TMK0031A` 的欄位異動 | **兩份 Model xsd ＋ 兩份 View xsd 共四份都要重生**,兩支畫面都要回歸 | §2.6 |

### 4.2 `TMKM001` — 專案外撥名單維護

#### 4.2.1 用途(推測)

行銷專案把一批客戶整批匯進來,分派給電訪專員;專員在這裡查自己的名單、逐通電話建項次。**主檔完全唯讀**,能動的只有項次與它掛的兩張子表。

#### 4.2.2 查詢條件與「會把資料濾掉而不提示」的部分

| 條件 | 控件 | 傳到 PO 的參數 | 錨點 |
|---|---|---|---|
| OutBound 項目 | `custOUTBND_CODE_0` | `OUTBND_CODE`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:151-154` |
| 是否含已結案清單 | `ucomREADY_YN_0`(代碼分類 `'482'`) | `READY_YN`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:157-160` |
| 統一編號 | `utxtID_NO_0` | `ID_NO`(Like) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:162-165` |
| 姓名 | `utxtBF_NAME_0` | `BF_NAME`(Like) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:168-171` |
| 受益人戶號 | `custBF_NO_0` | `BF_NO`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:174-177` |
| 下次可連絡日期(起)(迄) | `udatNext_DATE_ST` / `_END` | `RECONTACT_DTTM_S` / `_E` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:180-184` |

會靜默濾掉資料的有五條:

| # | 條件 | 為什麼會濾掉 | 錨點 |
|---|---|---|---|
| 1 | `AND TMK001A.OUTBND_CODE <> 'A0'` | 設計如此:AO 名單永遠看不到。**但 Oracle 三值邏輯:`OUTBND_CODE` 若為 NULL,`<> 'A0'` 是 UNKNOWN 不是 TRUE**,那筆會被靜默丟掉。`OUTBND_CODE` 是主鍵所以理論上不會 NULL,但這是全模組唯一的 `<>` 比較,同型缺陷在 CAS / CLS / DSM 都中過 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245` |
| 2 | CTE `MYTMK002A` 裡的 `A.OUTBND_CODE <> 'A0'` | 同上,而且這一層是決定「本次服務人員」那一路權限成不成立 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:206` |
| 3 | 三路 `OR` 權限條件 | 不是主管、不是建立者 / 指定員工、也不是任何一通電話的服務人員 → 整筆看不到,沒有任何提示 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244` |
| 4 | `COD009` 的離職日過濾 `NVL(TRIM(A.LEAVE_DATE), '99991231') >= 今天` | 登入者若已離職,`MYEMP_LIST` 是空的,第二路權限直接失效 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| 5 | `NVL(LAST_TMK003A.READY_YN,'N') = 'Y'` / `= 'N'` | 「是否含已結案清單」選了就是硬過濾;**它比的是該名單最後一通電話的完成碼**,不是整份名單 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |

第 5 條的「最後一通」是用 `MAX(...) KEEP(DENSE_RANK FIRST ORDER BY OUTBND_SRNO DESC)` 算的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:189-190`),**取的是項次最大的那一筆,不是日期最新的那一筆**。項次是人工遞增的,通常一致,但如果有人插號就會不一樣。

#### 4.2.3 整批匯入(`TMKM001p1` ＋ `BatchAdd`)

這是全模組唯一會大量寫資料的地方,也是缺陷最密的一段。

前端流程(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:92-133`):

1. 選 CSV → `StreamReader` 預設編碼開檔,**第一行當標題丟掉**(`:106`)。

2. 逐行 `Split(',')`,**欄數少於 2 就 `break`**(`:111`)——後面所有列靜默消失,連提示都沒有。

3. 戶號轉 `decimal` 失敗 → 跳訊息、清空整份、`return`(`:115-122`)。

4. 員工編號不做任何檢核,直接塞(`:123`)。

**範本下載寫出的檔用 `Encoding.Default`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:87`),讀回來的 `StreamReader` 沒指定編碼(預設 UTF-8)。**兩邊不一致;因為範本只有一行 ASCII 表頭而且會被丟掉,目前不會出事,但只要有人在 CSV 裡放中文就會壞。

選專案代碼時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:135-165`):呼叫 `CheckExists` 問伺服器,有資料就跳「已有該OutBound項目,是否全數刪除?」。**按「否」只是把代碼欄清掉,不會取消整個對話框**;按「是」就進入下一步。

伺服端 `BatchAdd`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:513-674`),一個交易裡做四件事:

1. **先刪**:`TMK001A` `TMK002A` `TMK003A` `TMK0031A` 四張表這個專案的資料全部 DELETE(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-602`)。**四句都包在 `string.Format(...)` 裡但樣板沒有任何 `{0}`**,傳進去的第二個參數完全沒用到——只是沒害,不是對。

2. **可能新增代碼**:專案名稱欄不是空字串就往 `COD006A` INSERT 一列 `CODE_SORT = 'P5'`,狀態碼寫死 `'301'`、四眼六個 ID 全填登入者、六個日期全填 `SYSDATE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623`)。**等於繞過四眼直接生效**,見 §8.4。

3. **逐筆 INSERT**:對 CSV 的每一列,從 `BMS001A` 撈客戶資料 INSERT 進 `TMK001A`,`OUTBND_NO` 用迴圈計數補成 11 位(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:643-655`)。六個衍生欄位用子查詢算:

- `MAX_ALLOT_AMT`:三年內股票型基金最大申購金額,靠 `F_GET_FND_PROF_TYPE(FUND_ID,'0') = '1'` 判斷股票型(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-576`)。

- `AGENT_CODE`:`OFD220A` 最近一筆申購書的銷售機構,查無給 `' '`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:577`)。

- `CUST_STYLE`:`OFD123A` 最新一筆的 `EFFECT_CODE2`,沒有就 `EFFECT_CODE1`,再沒有給 `'00'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:578`)。

- `EMAIL_DATE`:`OFD601` → `OFD607A` 的 `OPENDAY`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:570`、`:581-584`)。

- `STATUS` 寫死 `'301'`,四眼六個 ID / 日期一樣全填登入者與 `SYSDATE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:579`)。**匯入的名單一進來就是已覆核狀態。**

4. **回報**:`Model.Utility.Result.AddResultRow(true, i, "")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657`)。`i` 從 1 起跳當序號用,最後回報的筆數是「實際筆數 + 1」;**CSV 一筆都沒讀到時 `i` 仍是 1,照樣回報成功一筆**。

還有兩個要記住的:

- **子查詢的 alias `A` 蓋掉外層的 `A`**:外層 `FROM BMS001A A`,`MAX_ALLOT_AMT` 子查詢裡又 `FROM OFD081A A, OFD221A B`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:572`)。Oracle 以最內層為準,目前算得出來,但任何人想在子查詢裡引用外層的 `A` 都會拿到錯的表。

- **`CheckExists` 先塞一句假 SQL 佔位**:`GetSqlStringCommand("SELECT 1 = 1")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:679`),那不是合法的 Oracle 語句,只是因為後面立刻被覆蓋掉才沒事。

#### 4.2.4 項次彈窗 `TMKM001p0`

雙擊明細 grid 開啟(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:409-465`)。新增列時自動補三件事:主檔三段 Key、項次 = 現有最大值 + 1、本次服務人員 = 登入者、上次服務人員 = 前一個項次的本次服務人員(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:424-445`)。

彈窗載入時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:71-182`):

1. 帶出主檔五欄與 `OUTBND_TOTAL` 七個計數(唯讀)。

2. 用四段主鍵找對應的 `TMK003A`,找不到就**當場新增一列**,通話日期 = AP Server 系統日、完成碼 = `"Y"`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:133-159`)。

3. 用 `m_callin_mgr.GetDataFilter(m_detail_row)` 組出 `TMK002A` 四段主鍵的 DataTable 篩選字串,拿去篩 `TMK0031A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:170-173`)。

4. 權限:`USER_ID_T` 不是登入者就把十幾個欄位鎖唯讀、兩張 grid 停用、確定鈕關掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`)。

按確定時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539`):

1. 通聯原因大小類**至少勾一項**,否則擋(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:407-413`)。

2. 回寫 `TMK002A` 六欄。

3. **有效代碼變更時,把同一份名單的其他項次全部覆蓋成新值**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`),註解說明「同一檔 `OUTBND_CODE` 只能有一筆有效代碼」。這是一個沒有任何提示的跨列寫入。

4. 再聯絡否為 N 時把三個再聯絡欄位清空(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:451-463`)。

5. 回寫 `TMK003A` 的通話日期與完成碼;**`COMMENT1` 那一行被註解掉**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:477`),所以畫面上的備註只進 `TMK002A.REMARK`,不進 `TMK003A.COMMENT1`。

6. 重算 `TMK0031A`:舊的還勾著就留、沒勾就 `Delete()`;新勾的逐一 `AddTMK0031ARow`,`CALLIN_SEQ` 固定 1(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:480-535`)。

#### 4.2.5 跨表更新

| 表 | 動作 | 時機 | 錨點 |
|---|---|---|---|
| `TMK001A` | INSERT / DELETE(整批) | 整批匯入 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:649` |
| `TMK002A` `TMK003A` `TMK0031A` | DELETE(整批)／四眼 INSERT-UPDATE-DELETE | 整批匯入／畫面維護 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:597-601`、框架 |
| `COD006A`〔共用〕 | **INSERT 一列** | 整批匯入且專案名稱有填 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623` |
| `BMS001A` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只讀 | 整批匯入 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-585` |

### 4.3 `TMKM002` — AO 新開發客戶電話行銷維護

#### 4.3.1 用途(推測)

電訪專員自己開發的客戶,一位客戶一張單、走完整四眼。名單來源不是專案,而是從潛在客戶檔 `CRM003A` 或受益人檔 `BMS001A` 挑一筆進來,因此主檔上多了 `PR_NO` 與 `PR_NAME`。

#### 4.3.2 挑客戶這一段(`TMKM002` 多出來的 439 行)

三個入口都通到同一支 `SetPrNoData`:

| 入口 | 觸發 | 錨點 |
|---|---|---|
| 統一編號欄的「…」鈕 | 開 `TMKM002p1`,同時列潛在客戶與受益人兩張 grid | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:668-679` |
| 姓名欄的「…」鈕 | 同上,用姓名查 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:685-696` |
| 戶號 Searcher 選取後 | 先把受益人列轉成潛在客戶列,再填 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:702-719` |

`TMKM002p1` 兩張 grid 互斥:選了一邊就取消另一邊(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:111-145`)。**兩張 grid 的查詢條件寫法不一樣**:潛在客戶直接傳原值給 `Like`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:66`),受益人要自己在後面加 `%`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:83-84`、`:90-91`),註解說「DataSrc的Where值必須自己處理」。**同一個畫面兩種前置條件,查出來的範圍不一樣。**

`SetPrNoData`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:737-801`)一次填十四個欄位。裡面有一條永遠不成立的判斷:

```
if (string.IsNullOrWhiteSpace(mainRow.PR_NO) && mainRow.PR_NO == "-1")
```

`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759`。**`&&` 應該是 `||`**:一個空白字串不可能同時等於 `"-1"`,所以這條分支是死的,`PR_NO = "-1"` 的哨兵值會被原樣填進畫面。這是 `AND` / `OR` 用錯的同型缺陷(CAS `CASB001_PO.cs:431` 那一類)。

`GetCRM003A_Row`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:807-863`)手寫逐欄搬 30 幾欄,裡面有三組重複的 `HM_TEL_AREA` / `HM_TEL` 指派(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:842-853`),後兩組是純粹的複製貼上殘留。地址別代碼被硬壓成兩種值:`addr_code == "1" ? "1" : "0"`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:822`),註解寫「強制此處代碼只會有 0.長條式 or 1.分段式」。風險屬性那一行被註解掉,理由是「二邊欄位代碼不同,不採用」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:858-859`)。

#### 4.3.3 新增時的取號與前次指派人

`GetPageValue` 在新增模式下(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:390-413`):

1. `OUTBND_CODE = "A0"`、`OUTBND_NO = ""`(序號留給伺服端配)、`ID_NO` 取畫面值。

2. 明細第一列的本次服務人員 = 登入者。

3. 呼叫 `GetLAST_USERID` 問伺服器「這個統編上次是誰服務的」,填進 `USER_ID_L`。

`GetLAST_USERID` 的 SQL 是 `SELECT MAX(USER_ID_L) FROM TMK002A WHERE OUTBND_CODE = 'A0' AND ID_NO = :ID_NO GROUP BY OUTBND_CODE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:433-438`)。**它取的是 `USER_ID_L`(上次服務人員)的最大值,不是 `USER_ID_T`(本次服務人員)。**方法名與註解都說「取得最後指派人員」,但實際拿到的是「歷史上所有紀錄裡,上次服務人員欄位的字典序最大值」——既不是最後一次,也不是本次。這是欄位比錯欄的同型缺陷(CLS `CLSR002_PO.cs:864` 那一類),嚴重度中:它只影響一個顯示欄位,不影響權限。

伺服端 `BeforeAdd` 用 `do { … } while (IsExistByData(...))` 迴圈取號直到不重複(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:149-152`),取到之後把三段 Key 回填給三張明細裡 `OUTBND_NO` 還空著的列(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:165-195`)。

#### 4.3.4 四眼跳號一覽表:七個事件、一個號別,而且號別是錯的

`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415` 七個事件的寫法完全一樣,只差 `EVAType`:

```
if (!SrNoCommentProcessor.AddCommentHistory(EVAType.Xxx, SrNo.AllotNoForNfd, …)) throw new ApplicationException("");
```

**`SrNo.AllotNoForNfd` 的值是 `"OFD220A"`,也就是「境內申購書號」**(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103`)。但這支畫面取的號是 `SrNo.OUTBND_NO`,值是 `"TMK001A"`(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`、`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604`)。**七處全部把 TMK 的跳號紀錄寫到申購書號那一本帳上。**這與 `bbs.md` 附錄 E1 記的 `BBSM013_PO.cs:1260` 是同一型缺陷,差別是 BBS 只錯一處、TMK 是七處一致地錯(所以八成是複製 `CASM001_PO` 的樣板來的——`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` 就是同一行)。

另外 `throw new ApplicationException("")` 丟的是**空訊息例外**,七處都一樣。使用者看到的會是框架的預設字串,沒有任何線索指向跳號一覽表。

#### 4.3.5 兩套通話彈窗

| 彈窗 | 入口 | 怎麼找 `TMK003A` | 怎麼篩 `TMK0031A` | 寫 `COMMENT1` |
|---|---|---|---|---|
| `TMKM002p0` | 「通話記錄」鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:579-602`) | `FirstOrDefault()`,**不帶任何條件**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:74-75`) | `Select()`,**不帶任何篩選**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:269`) | 會寫(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:260`) |
| `TMKM002p2` | 雙擊明細 grid(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:948-1023`) | 四段主鍵比對(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:120-125`) | `GetDataFilter` 組主鍵條件(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:453-454`) | **被註解掉**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:444`) |

**只要這張單有兩個以上的項次,走 `TMKM002p0` 就會改到第一個項次的通話記錄、並把不在本次勾選裡的所有項次的通聯原因全部刪掉。**`TMKM002p0` 的註解自己寫著「此功能對會對應一份通訊記錄,所以不做篩選(全部取出)」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:113`、`:268`)——這個前提在 `TMKM002p2` 允許多項次之後就不成立了,但 `p0` 沒有跟著下架。詳見附錄 E3。

#### 4.3.6 跨表更新

`TMKM002` **不寫任何外部表**。它的寫入面就是四張自有表,全部經由四眼引擎;`TMK901` 不碰、`COD006A` 不碰、`CRM003A` 不碰。

### 4.4 兩支 M 畫面的卡控總表

結果類型五類:阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋。

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 五個條件必須擇一填寫 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:499-507` |
| 查詢前 | 下次可連絡日期(起)(迄)必須同時有值或同時無值 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:509-511`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:622-624` |
| 查詢前 | 下次可連絡日期(起)不可大於(迄) | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:513-515`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:626-628` |
| 查詢 | 專案代碼硬條件(`<> 'A0'` / `= 'A0'`) | 兩支各自 | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` |
| 查詢 | 三路 / 兩路權限條件 | 兩支 | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228` |
| 查詢 | 登入者已離職 → 第二路權限失效 | 只有 `TMKM001` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| 查詢 | 主檔必須有 `OUTBND_SRNO = 1` 的明細 | 只有 `TMKM002` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:219-222` |
| 查詢 | 是否含已結案清單 | 只有 `TMKM001` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |
| 新增主檔 | 一律不支援 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:160` |
| 新增明細 | 新增模式下雙擊 grid | 只有 `TMKM001` | 警示 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:411-416` |
| 存檔前 | 新增的項次沒有勾通話記錄 | 只有 `TMKM001` | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:564-571` |
| 刪明細前 | 選取列含不是自己的項次 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:475-481` |
| 刪明細前 | 一律不准刪 | 只有 `TMKM002` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1027` |
| 修改 | 服務人員不是登入者 → 鎖修改與刪除鈕 | 只有 `TMKM002` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:359-364` |
| 彈窗開啟 | 服務人員不是登入者 → 全鎖、關掉確定鈕 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:281-318` |
| 彈窗確定 | 通聯原因大小類至少勾一項 | 兩支(三個彈窗) | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:407-413`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:372-378`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:241-247` |
| 加通聯原因 | 代碼未選 / 不存在或無效 / 已勾選 | 兩支(三個彈窗) | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:227-249`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:207-229`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:202-224` |
| 離開再聯絡時間欄 | 值等於 0 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:546`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:512` |
| 離開再聯絡時間欄 | **值大於 24** | 兩支都**不擋**,但訊息說「必須介於1~24時之間」 | 記錄不擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:548`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:514` |
| 存有效代碼 | 值變更時覆蓋同名單全部項次 | 兩支 | **記錄不擋(無提示的跨列寫入)** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 匯入前 | 至少要有一筆資料 | 只有 `TMKM001p1` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:56-61` |
| 匯入前 | OutBound 項目與項目名稱必填 | 只有 `TMKM001p1` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:62-73` |
| 匯入前 | 該專案已有資料 → 是否全數刪除 | 只有 `TMKM001p1` | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:147-149` |
| 讀 CSV | 戶號欄不是數字 | 只有 `TMKM001p1` | 阻擋(清空整份) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:115-122` |
| 讀 CSV | **欄數少於 2** | 只有 `TMKM001p1` | **過濾(無提示,而且吃掉後面全部)** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:111` |
| 匯入執行 | `COD006A` INSERT 失敗 | 只有 `TMKM001p1` | 阻擋(回滾) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:625-630` |
| 匯入執行 | 任一列 INSERT 影響 0 列 | 只有 `TMKM001p1` | 阻擋(回滾) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:649-654` |
| 匯入執行 | **CSV 一筆都沒有時** | 只有 `TMKM001p1` | **記錄不擋(回報成功一筆)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:642`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657` |

### 4.5 `TMKM901` — CallOut 專員名單移轉

#### 4.5.1 用途(推測)

專員離職或調動時,把他名下的名單整批改派給另一位。`TMK901` 不是業務表,是一張**移轉工單**:一個 `DATAID` 掛 N 列要移轉的 `TMK002A`,整批走一次四眼。9xx 是保留段的畫面代號,見 `architecture.md §9`。

#### 4.5.2 帶資料進來

在「OutBound 項目」或「原專員」兩個 Searcher 選完值時觸發 `GetTMK002A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:153-161`):

1. 兩個條件都空 → 什麼都不做(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:111-112`)。

2. grid 已經有資料 → **詢問**「是否清除現有明細,並重新帶入資料」,選否就 `e.Cancel = true`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:113-118`)。

3. 呼叫伺服端 `GetTMK002A`,SQL 是 `TMK002A` × `TMK001A` × `AA_USER` 三表內連(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:58-72`)。

4. 把舊列全部 `Delete()`、新列全部 `SetAdded()` 再 `Merge`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:127-131`)。

三件要注意的:

- **`AA_USER` 是 INNER JOIN**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:72`)。原專員的帳號如果已經從 `AA_USER` 刪掉,他名下的名單**一筆都帶不出來**,而且畫面不會說為什麼。這對「離職後要移轉」這個主要使用情境剛好是反的。

- **`BF_NO = -1` 被當成 NULL**:`case TMK001A.BF_NO when -1 then null else TMK001A.BF_NO end`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:63`、`:123`)。`-1` 是潛在客戶沒有戶號時的哨兵值,與 `TMKM002` 那邊的 `"-1"`(§4.3.2)是同一回事。

- **查無資料的 `catch` 把所有例外都翻譯成「查無資料」**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:79-83`)。連線失敗、SQL 語法錯、權限不足,畫面上都只會看到這四個字。

#### 4.5.3 覆核時真正發生的事

`BeforeApprove`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:154-239`)做兩步:

**第一步**:逐列 UPDATE `TMK002A` 的 `USER_ID_T`,用四段主鍵定位(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:160-186`)。

**第二步**:一句 `MERGE INTO TMK001A`,把名單主檔的 `EMP_NO` 從原專員的員工代碼改成新專員的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:188-237`)。註解註明是 2020/06/18 才加的。MERGE 的來源子查詢做三件事:

1. `MYEMP_NO`:從 `COD009` 取每個登入帳號最新的員工代碼,用 `MAX(EMP_NO) KEEP(DENSE_RANK FIRST ORDER BY ENTRY_DATE DESC, LEAVE_DATE DESC)`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:193-200`)。

2. `MYTMK901`:讀本次 `DATAID` 的工單,把原 / 新專員帳號各自對到員工代碼。

3. 用 `OUTBND_CODE` ＋ **`EMP_NO = 原專員員工代碼**` 去 `TMK001A` 找要改的列(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:224-226`)。

**這裡有一個範圍放大的風險**:第一步改的是工單上勾選的那幾筆 `TMK002A`;第二步的 `MERGE` 卻是用「同一個專案 ＋ 同一個原專員」去比對 `TMK001A`,**沒有帶 `OUTBND_NO` 與 `ID_NO` 去限制範圍**。也就是說,只勾了三筆,`TMK001A` 上那位專員在該專案的**全部**名單的 `EMP_NO` 都會被改掉。這是設計意圖還是漏寫,程式碼無法分辨——**需要業務確認**。

三個確認的缺陷:

| # | 現象 | 錨點 |
|---|---|---|
| 1 | `args.Cancel` 在迴圈裡**每一圈都被覆寫**。第 3 列失敗設成 true,第 4 列成功又設回 false,整批照樣覆核成功,而且錯誤訊息也被蓋掉 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185` |
| 2 | `DATAID` 取自迴圈的**最後一圈**。列數為 0 時 `DATAID` 是空字串,MERGE 照樣執行(比對不到就什麼都不做,但交易是成功的) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:180`、`:235` |
| 3 | MERGE 的 `ON` 後面是**全形空白 U+3000**,不是 ASCII 空白 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:230` |

第 3 條要講清楚:全形空白是否被 Oracle 的語彙分析器當成空白,取決於用戶端字元集與版本,repo 內無法驗證。**如果不被接受,整句 MERGE 會丟 `ORA-00920` 之類的錯,而第一步的 `TMK002A` 更新已經做完**——覆核會失敗回滾,但這支畫面的主要功能等於壞的。**這一條務必實測**。

#### 4.5.4 前端的三個問題

| # | 現象 | 錨點 |
|---|---|---|
| 1 | `BeforeAddButtonClicked` 檢核失敗只設 `e.Cancel = true`,**沒有 `return`**,後面照樣把未勾選的列 `Delete()`。使用者按取消或檢核不過,畫面上的資料已經被改掉了 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99` |
| 2 | 「已覆核資料不可修改」判斷寫成 `APPROVEID != string.Empty`。ATLAS 的預設值常是一個空白字元 `' '`(整批匯入那段就寫 `' '`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:623`),那樣的話**還沒覆核的工單也會被當成已覆核而鎖住** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84` |
| 3 | `if (view.Util.Result.Count == 0 \|\| view.Util.Result[0].ReturnCode)` 把「伺服器一個結果列都沒回」當成成功 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:125` |

#### 4.5.5 `TMKM901` 卡控總表

| 時點 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| 帶資料前 | 兩個查詢條件都空 | 過濾(無提示,直接什麼都不做) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:111-112` |
| 帶資料前 | grid 已有資料 | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:113-118` |
| 帶資料 | 原專員不在 `AA_USER` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:72` |
| 全選 / 全不選 | 目前有套篩選 | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:165-169`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:176-180` |
| 新增 / 修改前 | 至少勾選一筆 | 阻擋(但**沒有 return**,資料照改) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:211-215`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99` |
| 載入維護頁 | `APPROVEID` 不是空字串 | 阻擋(判斷式可能誤判,見 §4.5.4) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84-88` |
| 覆核時 | 某列在 `TMK002A` 找不到 | **記錄不擋**(訊息會被下一圈蓋掉) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185` |

## 5. 查詢畫面(I)

**本模組無此類畫面。**

原因:TMK 的查詢需求全部被兩個地方吸收了。

1. **M 畫面本身就是查詢頁 ＋ 維護頁兩頁式**(`this.TabPages = 2`,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:43`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:45`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:38`)。查詢頁的結果 grid 欄位在 `App.config` 裡宣告(§0.5),要「只看不改」直接用查詢頁就好,不需要另開 I 型畫面。

2. **要跨名單、跨期間看的東西一律走 R**。11 支報表把統計與明細都涵蓋了,而且 R 型畫面多了「轉 Excel」這條路,比 I 型的 grid 更符合電訪主管的使用方式。

另外,TMK 的資料也會出現在別的模組的 I 畫面裡:`OFDI011` 讀 `CRM006A` / `CRM0061A` / `CRM003A`(見 `crm.md §8.3`),而 `TMKM001` 工具列第一顆自訂鈕直接開 `OFDI011D`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:581-584`)——**電訪專員要看客戶全貌時是跳到 OFD 的查詢畫面,不是留在 TMK。**這也是 TMK 不需要自己的 I 畫面的原因之一。

## 6. 批次(B)與 WindowsService

**本模組無此類畫面,也沒有 WindowsService。**

原因有三:

1. **名單的產生是人工觸發的,不是排程。**整批匯入做在 `TMKM001` 的自訂鈕上(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:72-78`),使用者自己選檔、自己按確定;沒有任何地方監看目錄或排程。

2. **統計是報表算的,不是批次先算好的。**11 支報表每次都現跑 SP,PO 一律 `cmd.CommandTimeout = 0` 並註解「此程式讓它永久跑」(例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:58`)。所以沒有中介的統計表要靠批次維護。

3. **唯一像批次的 `TMKM901`,被做成 M 型畫面**:它有勾選 grid、有四眼、有工單表 `TMK901`,整批動作發生在覆核那一刻(§4.5.3),而不是在某個排程時點。

要留意的是:`BatchAdd` 雖然掛在 M 畫面上,**行為上它就是一支批次**——一個交易、先刪四張表、再逐筆插入、失敗整批回滾(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:513-674`)。它沒有 B 型畫面該有的東西:沒有執行紀錄、沒有筆數對帳(回報的筆數還多 1,§4.2.3)、沒有重跑保護(重跑就是再刪一次再插一次)。**把它當批次看待,不要當成一般的畫面存檔。**

## 7. 報表(R)

```text
[圖] TMK 十一支報表畫面的四段鏈、兩種選 rpt 的寫法、二十四份 rpt 的分佈、兩個已確認缺陷，以及四種查詢權限做法
圖中文字:① 11 支 R 畫面固定四段鏈，全部不碰維護層的 PO / R 畫面收條件 算登入者員編 / 三條路 預覽 列印 轉 Excel / 報表 FormProxy 過一次遠端 / 報表 PO 只呼叫 SP / 13 支報表 SP / 游標回一到四張結果集 / ② 報表選項怎麼決定要載哪一份 rpt：兩種寫法並存 / 先算出檔名與標題再設定 / R001 R002 R003 R004 R005 R006 R901 / 在判斷式裡直接設定 / R007 R008 R009 R010 / 單一選項對單一 rpt / R001 R002 R003 各三份 / 兩個選項相乘 / R006 兩軸配出五份 / 沒有選項 固定一份 / R008 R009 各一份 / ③ 24 份 rpt 的分佈：畫面數不等於報表數 / R001 R002 R003 各三份 / 共九份 / R006 五份 / 三種計數乘兩種呈現 / R004 R005 R007 R010 各兩份 / 共八份 / R008 R009 各一份 / 共兩份 / ④ 兩個會咬人的地方 / TMKR901 指名一支不存在的 rpt / repo 內找不到這個檔 / 產 Excel 失敗時沒有任何訊息 / 使用者以為成功其實沒存檔 / ⑤ 登入者查詢權限：三種做法，三支完全沒有 / 傳查詢者員編給 SP / R004 R005 R006 / 傳登入者員編給 SP / R007 R008 R009 R010 / 前端鎖專員欄位 / R003 主管才解鎖 / R001 R002 R901 沒有 / R901 算了卻沒傳
```

*圖:圖 4 報表群。黑框=沒有原始碼的 SP 或已確認的缺陷；橘框=值得特別記住的一支。TMKR006 是唯一用兩個選項相乘決定報表檔的；TMKR901 的預覽與列印路徑指到一個不存在的 rpt，只有轉 Excel 那條路能跑。*

**這一章是本模組的重心。**14 支畫面裡 11 支是 R,配 24 份 `.rpt`、13 支版控外的 SP。31 個組合不可能每支深挖,所以先用 §7.1–§7.3 把共同模式講完,再挑三支有特色的展開(§7.4–§7.6),最後兩節講兩條橫向規則(§7.7 Excel、§7.8 查詢權限)。

### 7.1 一覽

| rpt | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| `TMKR001RPS1` `TMKR001RPS2` `TMKR001RPS3` | `TMKR001` | `S_TA_TMKR001_GET`(三個 refcursor 一次回) | `iCAL_DATE` `iCREATEID` `iREPORT_TYPE` |
| `TMKR002RPS1` `TMKR002RPS2` `TMKR002RPS3` | `TMKR002` | `S_TA_TMKR002_GET`(三個 refcursor) | `iCAL_YEAR` `iCREATEID` `iREPORT_TYPE` |
| `TMKR003RPS1` | `TMKR003`(選項 `'0'`) | `S_TA_TMKR003_GET_1`(兩個 refcursor) | `iOUTBND_USER` `iCALLIN_DATE_ST` `iCALLIN_DATE_END` `iOUTBND_CODE` `iCALLIN_CODE` |
| `TMKR003RPS2` | `TMKR003`(選項 `'1'`) | `S_TA_TMKR003_GET_2` | 同上 |
| `TMKR003RPS3` | `TMKR003`(選項 `'2'`) | `S_TA_TMKR003_GET_3` | 同上 |
| `TMKR004RPS1` | `TMKR004`(選項 `'0'`) | `S_TA_TMKR004_GET_1` | `iALLOT_DATE_ST` `iALLOT_DATE_END` `iSAL_EMP_NO` `iFUND_ID` `iHAS_RSP` `iQUERY_EMP_NO` |
| `TMKR004RPS2` | `TMKR004`(選項 `'1'`) | `S_TA_TMKR004_GET_2` | 同上 |
| `TMKR005RPS1` `TMKR005RPS2` | `TMKR005`(選項 `'0'` / `'1'`) | `S_TA_TMKR005_GET_1`(**兩種選項共用一支 SP**) | `iALLOT_DATE_ST` `iALLOT_DATE_END` `iOUTBND_CODE` `iREPORT_TYPE` `iQUERY_EMP_NO` |
| `TMKR006RPS1` `TMKR006RPS2` `TMKR006RPS3` `TMKR006RPS4` | `TMKR006`(類型1 `'1'`/`'2'` × 類型2 `'1'`/`'2'`) | `S_TA_TMKR006_GET_1`(四個 refcursor) | `iRSP_DATE_ST` `iRSP_DATE_END` `iEMP_NO` `iMQ_NUMBER` `iRSP_TYPE` `iREPORT_TYPE1` `iREPORT_TYPE2` `iQUERY_EMP_NO` |
| `TMKR006RPS5` | `TMKR006`(類型1 `'3'`) | `S_TA_TMKR006_GET_2` | `iRSP_DATE_ST` `iRSP_DATE_END` `iRSP_TYPE` `iQUERY_EMP_NO` |
| `TMKR007RPS1` `TMKR007RPS2` | `TMKR007`(選項 `'1'` / `'0'`) | `S_TA_TMKR007_GET_1` | `iUSER_EMP_NO` `iCTL_DATE_ST` `iCTL_DATE_END` `iSAL_EMP_NO` `iFUND_ID` |
| `TMKR008RPS1` | `TMKR008` | `S_TA_TMKR008_GET_1` | `iUSER_EMP_NO` `iALLOT_DATE_ST` `iALLOT_DATE_END` `iEMP_NO` `iFUND_ID` |
| `TMKR009RPS1` | `TMKR009` | `S_TA_TMKR009_GET_1`(兩個 refcursor) | `iUSER_EMP_NO` `iPRINT_YYMM` `iEMP_NO_ST` `iEMP_NO_END` `iFUND_ID` `iRATE_DATE` |
| `TMKR010RPS1` `TMKR010RPS2` | `TMKR010`(選項 `'1'` / `'2'`) | `S_TA_TMKR010_GET_1`(三個 refcursor) | 14 個,含三個可為 `NULL` 的數值參數 |
| (指名 `TMKR901RPS0`,**檔不存在**) | `TMKR901` | `S_TA_TMKR901_GET`(五個 refcursor) | `iCAL_DATE_S` `iCAL_DATE_E` `iAGENT_CODE` `iEMP_NO` `iPROJECT` `iOUTBND_CODE` `iCAMPAIGN_CODE` `iFUND_ID` `iRSP_TYPE` `iSUCCESS_SUB` `iRENEW` |

錨點:每支 PO 的 `GetStoredProcCommand` 那一行,例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:56`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:68`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR010_PO.cs:56`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR901_PO.cs:58`。**13 支 SP 一支都不在 `DB/` 資料夾內**,口徑無法從 repo 確認(附錄 B)。

### 7.2 十一支的共同骨架

每支 R 都長得一樣,只有參數不同。骨架五段:

| 段 | 做什麼 | 範例錨點 |
|---|---|---|
| 1 `FormInitial` | 綁 ViewVDB 與 FormProxy;多數會算登入者員工代碼 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:37-42`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:46-68` |
| 2 `RefreshPage` | 設預設值(報表選項、部門固定 `'08201'`、基金全選) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:85-105` |
| 3 `BeforePreviewOrPrintButtonClicked` | 檢核 → 組查詢參數 → `SetQueryParameters(rpt, rpt, 標題)` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:90-106` |
| 4 PO `GetData` | `BeginTransaction` → 呼叫 SP → `LoadDataSet` → 依筆數寫 `Result` → `Commit` | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:47-98` |
| 5 `ReportLoad` | `SetRptSchemaOnDoc()` 再逐一 `SetParameterValue` 把查詢條件印在報表頁首 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:112-154` |

Ctl 層十一支逐字相同,都是 151 行,`GetReportData` ＋ `GetReportObject` 兩支加樣板(`Dev/ATLAS.TMK.Report/Source/Control/ReportControl.TMK/TMKR001_Ctl.cs:49-64`)。`GetReportObject` 直接把**用戶端傳來的報表類別名稱**交給 `CRReportTransfer.TransferFileByte`(無原始碼,從呼叫端反推),與 `architecture.md §6` 描述的一致:伺服器照單全收。

PO 層有四個共同寫法要記住:

1. **`cmd.CommandTimeout = 0`,註解「此程式讓它永久跑」**,十一支全部有(例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:64`)。查詢條件開太大就是整條連線卡住,沒有逾時保護。

2. **報表只讀卻開交易**:每支都 `BeginTransaction` / `Commit`(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:54`、`:83`)。

3. **`catch` 裡先 `tran.Rollback()`**(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:87`)。如果 `BeginTransaction()` 自己就丟例外,`tran` 是 null,`catch` 裡會再丟一個 `NullReferenceException`,原始錯誤直接消失。十一支全中。

4. **「查無資料」與「執行失敗」在 `Result` 上長得一樣**:兩者都是 `AddResultRow(false, 0, "")`,訊息都是空字串(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:80`、`:88`)。畫面端只好一律顯示「無符合查詢條件的資料。」(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352`)——**SP 掛掉時使用者看到的也是這一句**。

### 7.3 選 rpt 的兩種寫法,加一組對不齊的值域

兩種寫法:

| 寫法 | 畫面 | 錨點 |
|---|---|---|
| 先 `GetReportFileTitle()` 回一個 `KeyValuePair`,再統一 `SetQueryParameters` | `TMKR001` `TMKR002` `TMKR003` `TMKR004` `TMKR005` `TMKR006` `TMKR901` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:186-203` |
| 在判斷式裡直接 `SetQueryParameters` | `TMKR007` `TMKR008` `TMKR009` `TMKR010` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:143-150` |

**報表選項的值域每支都不一樣,而且沒有規律:**

| 畫面 | 選項值 | 對應 | 錨點 |
|---|---|---|---|
| `TMKR001` `TMKR002` | `'1'` `'2'` `'3'` | RPS1 / RPS2 / RPS3 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:190-201` |
| `TMKR003` | `'0'` `'1'` `'2'` | RPS1 / RPS2 / RPS3 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:232-243` |
| `TMKR004` `TMKR005` | `'0'` `'1'` | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:242-249`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:183-190` |
| `TMKR007` | `'1'` `'0'`(**反過來**:`'1'` 是明細、`'0'` 是彙總) | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:143-150` |
| `TMKR010` | `'1'` `'2'` | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:191-198` |
| `TMKR006` | 類型1 `'1'` `'2'` `'3'` × 類型2 `'1'` `'2'` | 見 §7.4 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:205-237` |

**同一個模組裡「彙總 / 明細」在三支報表上用了三組不同的碼(`'0'/'1'`、`'1'/'0'`、`'1'/'2'`)。**改 SP 或改選項時很容易對錯,而且值都是直接傳給版控外的 SP,錯了也不會有編譯錯誤。

另外三支報表的 PO 有「選項沒對上就什麼都不做」的分支:

- `TMKR003_PO` 只認 `'0'` `'1'` `'2'`,其他值三個分支都不進,`Result` 一列都沒有(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:59-146`)。

- `TMKR006_PO` 只認 `'1'` `'2'` `'3'`(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:61`、`:106`)。

- 這時畫面端的 `view.Util.Result[0]` 會**丟 `IndexOutOfRangeException`**(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348`)。目前因為選項組的預設值都落在有效值域內而沒發作。

### 7.4 `TMKR006` — 唯一用兩個選項相乘決定報表檔的

兩個選項組:

| 類型1(`uoptREPORT_TYPE`) | 類型2(`uoptREPORT_TYPE2`) | 載入的 rpt | 標題 |
|---|---|---|---|
| `'1'` 筆數 | `'1'` 彙總表 | `TMKR006RPS1` | 電話行銷專員定額彙總表 |
| `'1'` 筆數 | `'2'` 明細-BY戶數 | `TMKR006RPS2` | 電話行銷專員定額客戶明細表 |
| `'2'` 戶數 | `'1'` 彙總表 | `TMKR006RPS3` | 電話行銷專員定額年度配額達成表--By 戶數(含168) |
| `'2'` 戶數 | `'2'` 明細-BY戶數 | `TMKR006RPS4` | 電話行銷專員定額客戶明細表--By 戶數(含168) |
| `'3'` 連續扣款三次筆數 | (忽略) | `TMKR006RPS5` | 電話行銷專員定額扣款成功統計表--By 戶數(含168) |

錨點:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:205-237`、選項值域在 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.Designer.cs:216-221` 與 `:364-367`。

PO 側對應兩支 SP:類型1 是 `'1'` 或 `'2'` 走 `S_TA_TMKR006_GET_1`(一次回四張表),`'3'` 走 `S_TA_TMKR006_GET_2`(回一張)。**兩個選項都原樣傳給 SP,所以四種組合共用同一支 SP、同一組四張結果集,由 SP 自己決定填哪幾張**——註解把對應關係寫在 PO 裡:「筆數 彙總 = TMKR006T3、筆數 明細 = TMKR006T4、戶數 彙總/明細 = TMKR006T1、TMKR006T2」(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:64-67`)。**這段註解是唯一能知道哪份 rpt 吃哪張結果集的線索,SP 不在版控裡。**

另外兩件事:

- 「每月配額數」預設 2,只有筆數/彙總會用,但**`ReportLoad` 裡把它印在報表頁首那一行被註解掉**(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:157-159`),參數照樣傳給 SP(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:185`)。所以報表上印不出這次用的配額數是多少。

- 業務員條件只有在 `custEMP_NO.Enabled` 時才傳(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:178-182`),而 `Enabled` 由選項變更事件控制(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:396-405`)。**切換選項時畫面上還看得到填過的業務員,但參數不會傳出去**——這是一條過濾(無提示)。

### 7.5 `TMKR003` — 唯一在前端做主管判斷的

`FormInitial` 直接問「你是不是 G11 的主管」:

```
var masters = new List<string>(utility.GetMasterEmpNo("G11"));
if (masters.Contains(empNo)) { 解鎖專員欄位 } else { 鎖成登入者自己 }
```

`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:48-72`。三點要注意:

1. **`"G11"` 是寫死的部門代碼**〔客戶特定〕,與 `TMKR901` 用的 `"G2"`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81`)、`TMKR004`–`TMKR010` 用的 `"08201"`(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:88`)是三組不同的值,三處都沒有註解說明關係。

2. **員工代碼是用位置取的**:`empInfo.Split(',')[1]`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:54`)。`ClientBizUtility.GetEMP_INFO` 沒有原始碼(從呼叫端反推),回傳一個逗號分隔字串,第 2 段被當成員工代碼。**只要那支共用函式多加一欄或換順序,八支報表同時錯。**同型缺陷見 `crm.md` 附錄 E.6。

3. **鎖定是前端做的,後端沒有第二道。**`TMKR003` 的 PO 沒有 `QUERY_EMP_NO` / `USER_EMP_NO` 參數(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:66-70`),SP 收不到登入者是誰。繞過前端就能查全部。

### 7.6 `TMKR901` — 9xx 保留段的報表,而且列印路徑指到一個不存在的檔

`TMKR901` 是唯一在 `9xx` 保留段的報表(`architecture.md §9`),也是全模組最特別的一支:

| 特徵 | 內容 | 錨點 |
|---|---|---|
| 指名的 rpt | `TMKR901RPS0`,標題是空字串 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:194` |
| 這個檔存在嗎 | **不存在。**`Dev/ATLAS.TMK.Report/Source/CrystalReports/Report.TMK/` 底下 24 份 `.rpt` 沒有任何 901 開頭的 | 母體第 4 節 |
| 註解怎麼說 | 「直接指定同一檔案同時產出多個 Sheets,Sheets Name 各自由 GenExcelR 指定」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:193` |
| `ReportLoad` 做什麼 | `SetRptSchemaOnDoc()` 之後就是一行註解 `// nothing` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:131-138` |
| 結果集 | 五張 `TMKR901T0`–`TMKR901T4`,對應 Excel 的五個工作表 | `Dev/ATLAS.TMK.Report/Source/Entity/ReportDataEntity.TMK/TMKR901Model.xsd:15-103` |

**結論:這支報表只有「轉 Excel」那條路能跑。**按預覽或列印時,`CRReportTransfer.TransferFileByte("TMKR901RPS0")` 會找不到檔;它沒有原始碼,回傳 null 還是丟例外無法從 repo 判定,但**無論哪一種,使用者都拿不到報表**。這與 `bbs.md` 附錄 E11 記的「列印路徑壞掉」是同一類,差別是 BBS 錯在參數名、TMK 錯在檔名。

`TMKR901` 另外三個寫死值〔客戶特定〕:

| 值 | 意思 | 錨點 |
|---|---|---|
| `AGENT_CODE IN ('08001', '08201')` | 只看兩個銷售機構 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:79` |
| `DEPT_NO = 'G2'` ＋ 離職日 >= 去年 1/1 | 業務員下拉限 G2 現職或前年度在職 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81-82` |
| `OUTBND_DATE1 = "20200101"` | 專案下拉只取 2020/01/01 之後的 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:87` |

還有一個死變數:`xUserEmpNo` 在 `FormInitial` 算出來了(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`),但 `GetQueryVDB` 從頭到尾沒有把它加進參數(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:143-185`)。**這支報表沒有任何登入者查詢權限過濾**,見 §7.8。

### 7.7 轉 Excel 這條路

十一支都有第三顆鈕「轉 Excel」,共用 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs`(285 行,本模組自有)。流程:

1. `DoValidate(isExcel: true)` 多檢查兩件事:轉出路徑必填、路徑必須存在(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:236-246`)。

2. 呼叫同一支 `GetReportData` 取數(**與預覽走同一條後端路徑**)。

3. 依報表選項挑一支 `GenExcelR1`–`GenExcelR5` 委派,檔名固定是 `<路徑>\<rpt名>.xlsx`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:356`)。

4. `ExcelHelper.GenExcelFile` 開 Excel COM、逐格寫、`SaveAs`、`Quit`、`FinalReleaseComObject`。

四個要注意的:

| # | 內容 | 錨點 |
|---|---|---|
| 1 | **回傳 false 時畫面什麼都不顯示。**只有 `== true` 才跳「執行成功」,`false` 沒有 else | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385` |
| 2 | `GenExcelFile` 用**錯誤訊息字串**判斷要不要吞例外:`e.Message.Contains("0x800A03EC")` 就當成使用者按了取消,回 false;否則 `throw e`(重設堆疊) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs:67-75` |
| 3 | 畫面端的 `catch` 把例外訊息寫到 `Console.WriteLine`(WinForms 看不到),使用者只看到「商業邏輯異常!」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:387-392` |
| 4 | **Excel 版面是手寫在 UI 層的**,跟 `.rpt` 各寫一次。`TMKR006` 有五支 `GenExcelR1`–`GenExcelR5`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:539-639`)。改報表欄位要同時改 `.rpt` 與這裡 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:417-464` |

`GetOutPath()` 在路徑為空時回傳桌面(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:261-266`),但 `DoValidate` 已經先擋掉空路徑,所以這個 fallback 只在選資料夾對話框的初始位置用得到。

### 7.8 登入者查詢權限:四種做法並存

| 做法 | 畫面 | 錨點 |
|---|---|---|
| 算出員工代碼,以 `QUERY_EMP_NO` 傳給 SP | `TMKR004` `TMKR005` `TMKR006` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:231`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:171`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:195` |
| 算出員工代碼,以 `USER_EMP_NO` 傳給 SP | `TMKR007` `TMKR008` `TMKR009` `TMKR010` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:119`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:100`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:100`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:119` |
| 前端鎖專員欄位,後端不知道登入者是誰 | `TMKR003` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57-71` |
| **完全沒有** | `TMKR001` `TMKR002` `TMKR901` | `TMKR001` / `TMKR002` 連 `GetEMP_INFO` 都沒呼叫;`TMKR901` 算了卻沒傳(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`) |

**同一個參數概念用了兩個名字(`QUERY_EMP_NO` / `USER_EMP_NO`),而且兩組 SP 各自定義。**這與 `crm.md §7.6` 記的「七支有、一支沒有」是同一類問題,TMK 這邊更散:四種做法、三支沒有。

`TMKR001` 與 `TMKR002` 沒有權限過濾是可以理解的——它們統計的是「建立者」維度的通話量(參數 `iCREATEID`),本來就是主管看的。**但那是推測,程式裡沒有任何註解說明,而且畫面上也沒有擋誰能開。假設**:功能權限由框架平台庫擋(`architecture.md §3`)。

### 7.9 報表側的卡控總表

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 預覽 / 列印前 | 日期(起)不可大於(迄) | 幾乎全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:227-231`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:283` |
| 預覽 / 列印前 | 日期(起)(迄)必填 | `TMKR004` `TMKR005` `TMKR008` `TMKR901` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:278`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:220`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:206`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:224` |
| 預覽 / 列印前 | 至少勾一檔基金 | `TMKR004` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:298` |
| 預覽 / 列印前 | 基金分類選了群組 / 費率 / 代碼卻沒指定值 | `TMKR008` `TMKR009` `TMKR010` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:223-235`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:231-243`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:347-359` |
| 預覽 / 列印前 | AO 代碼(起)不可大於(迄) | `TMKR009` | 阻擋(**訊息掛在列印年月欄上**) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:216-221` |
| 預覽 / 列印前 | 結餘範圍 / 未交易日期必須成對 | `TMKR010` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:331`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:368` |
| 組參數時 | AO 代碼只填(迄)沒填(起) | `TMKR009` | **過濾(無提示,迄被丟掉)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:109-117` |
| 組參數時 | 業務員欄被停用 | `TMKR006` | **過濾(無提示)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:178-182` |
| 組參數時 | 客戶來源不是「專案」時,專案代碼不傳 | `TMKR901` | **過濾(無提示)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:164-165` |
| 轉 Excel 前 | 轉出路徑必填且必須存在 | 全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:236-246` |
| 離開路徑欄 | 路徑不存在 | 全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:290-300` |
| 取數後 | 一筆資料都沒有 | 全部 | 警示(「無符合查詢條件的資料。」) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352` |
| 取數後 | **SP 執行失敗** | 全部 | 警示,但訊息與「查無資料」**一模一樣** | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:88` |
| 產 Excel 後 | 存檔失敗或使用者取消 | 全部 | **記錄不擋(完全沒有訊息)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385` |
| 日期連動 | `TMKR001` 的迄日固定為起日 +6 且不可輸入 | `TMKR001` | 記錄不擋(自動改值) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:69`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:306-317` |

最後一條值得單獨講:**`TMKR001` 的名字叫「日報表」,但迄日被程式固定成起日 +6,所以它其實是週報表**(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:308-311`),頁首還會印出七天的中文日期標題 `YD1`–`YD7`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:146-153`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:399-409`)。名字與行為不一致,但這一支是刻意的(七欄一週的版面),不是缺陷。

## 8. 跨模組共用

```text
[圖] TMK 跨模組影響面：CRM003A 靠 USAGE 分治、TMK 這側三處讀取的驗證結果、唯讀關係，以及整批匯入寫入代碼檔的副作用
圖中文字:① CRM003A 一張表多個模組共用，靠 USAGE 切成互不相見的世界 / CRMM003 寫入 USAGE 1 / 潛在客戶的唯一寫入者 / CASM001 寫入 USAGE 3 / CAS 的世界 TMK 看不到 / CRM003A〔共用〕 / 主鍵只有一欄 全表唯一 / ② TMK 這一側的三處讀取：兩處帶條件、一處沒帶 / TMKM001 通聯總覽 帶 USAGE / 與 crm.md 記載一致 / TMKM002 通聯總覽 帶 USAGE / 與 crm.md 記載一致 / TMKM002 取姓名 沒有條件 / 只靠潛在客戶序號 join / ③ 沒帶條件為什麼還是不會多撈：那一欄本身就是全表主鍵 / 序號唯一 join 不會多撈列 / 風險是顯示到別模組建的名字 / 若 CRMM003 覆核刪除該客戶 / TMK 的歷史通聯直接少一段 / ④ TMK 唯讀別人的表，沒有任何別的模組讀 TMK 的表 / BMS001A CRM003A CRM0061A / COD006A COD009 AA_USER / TMK 自有五張表 / 反查結果 無外部使用者 / 回歸範圍等於 TMK 自己 / 外加整批匯入會寫 COD006A / ⑤ 唯一的例外：整批匯入會往 COD006A 塞一列專案代碼 / TMKM001p1 填專案名稱 / 沒填就不寫 COD006A / 寫一列代碼分類 P5 / 狀態碼寫死 直接生效 / 全庫的 P5 下拉跟著多一筆 / 沒有任何畫面刪得掉
```

*圖:圖 5 跨模組。灰虛框=唯讀 join 的外部表；黑框=沒有原始碼或已確認的風險；橘虛框=〔客戶特定〕。TMK 對 CRM003A 是純唯讀，寫入者只有 CRMM003 與 CASM001；真正會回頭打到別人的只有整批匯入那一條：它會在共用代碼檔 COD006A 塞一列並直接標成已覆核。*

這一章回答一個問題:**改 TMK 的表會打到誰、改別人的表會打到 TMK 哪裡。**

先講結論:**TMK 的五張表沒有任何別的模組在用**,所以第一個問題的答案是「只打到 TMK 自己」;第二個問題才是重點。

### 8.1 `CRM003A`:從 TMK 這一側驗證 `USAGE` 分治

`crm.md §8.1` 記載 `CRM003A` 靠 `USAGE` 切成互不相見的世界:CRM / TMK 用 `'1'`、CLS 用 `'2'`、CAS 用 `'3'`,並且點名 TMK 這側有三處讀取。逐條從 TMK 這邊對:

| `crm.md §8.1` 記的 | TMK 這側實際看到的 | 對得上嗎 |
|---|---|---|
| `TMKM001` 不寫、查詢 `= '1'`,錨點 `TMKM001_PO.cs:330` | `AND CRM003A.USAGE = '1'` 在通聯總覽第二路的 `UNION ALL` 裡,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` | **✔ 逐字對得上,行號也對** |
| `TMKM002`(重複檢查)不寫、查詢 `= '1'`,錨點 `TMKM002_PO.cs:296` | `AND CRM003A.USAGE = '1'`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:296` | **✔ 對得上。**但它不是「重複檢查」,它是**通聯總覽的第二路**,與 `TMKM001` 那一段逐字相同。`crm.md` 的用途描述要修 |
| `TMKM002`(取姓名)**無 `USAGE` 條件**,`LEFT JOIN`,錨點 `TMKM002_PO.cs:225` | `LEFT JOIN CRM003A ON CRM003A.PR_NO = TMK001A.PR_NO`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` | **✔ 完全對得上** |
| `crm.md §8.3` 說 TMK 讀 `CRM0061A` join `CRM003A` join `COD006A`,錨點 `TMKM001_PO.cs:328-331` | `FROM CRM0061A,CRM003A,COD006A`(`:328`)、`CRM0061A.PR_NO = CRM003A.PR_NO`(`:329`)、`USAGE = '1'`(`:330`)、`CRM003A.ID_NO = '{0}'`(`:331`) | **✔ 對得上** |

**三處以外還有第四處嗎?沒有。**全 TMK(含報表側)只有這三處提到 `CRM003A`,加上 `TMKM002Model.xsd` / `TMKM002View.xsd` 裡那張沒人填的 DataTable(§2.6)。

從 TMK 這側補三點 `crm.md` 沒有的:

1. **「取姓名沒帶 `USAGE`」在資料正確性上不會出事,但在語意上會。**`CRM003A` 的主鍵只有 `PR_NO` 一欄(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:1137-1140`,與 `crm.md §8.1` 一致),所以 join 不會多撈列。**真正的風險是顯示**:如果某個 `PR_NO` 是 `CASM001` 建的(`USAGE = '3'`),`TMKM002` 照樣會把那個名字印在畫面上,而使用者以為那是一筆潛在客戶。

2. **`TMKM002Model.xsd` 是 `CRM003A` 的第五份 schema 副本。**`crm.md §8.1` 列了四份(CAS 的 Model 與 View、CRM 的 Model 與 View),TMK 這裡還有兩份(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:699`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM002View.xsd:699`),而且**沒有任何程式填它**。改 `CRM003A` 的欄位時,這兩份會被漏掉;好消息是漏了也不會壞,因為沒人用。

3. **`CRMM003` 的覆核刪除會讓 TMK 的通聯總覽少一段。**`crm.md §8.3` 已經點出 `CRMM003_PO` 會實體 `DELETE CRM006A`;從 TMK 這側看,後果就是通聯總覽的第二路(`CRM0061A` join `CRM003A`)撈不到東西——**畫面不會報錯,只會少幾列,而且沒有任何提示**。

| 改什麼 | 會打到 TMK 哪裡 |
|---|---|
| `CRM003A` 加欄 / 改型別 | TMK 的兩份 xsd 理論上要重生,但因為沒人填那張表,實務上不改也不會壞 |
| 改 `CRM003A.PR_NO` 的定義 | `TMKM002` 的取姓名 join、通聯總覽的兩路、`TMK001A.PR_NO` 三處都打到 |
| 改 `USAGE` 的值域 | 通聯總覽的兩路會突然看到 / 看不到資料;`TMKM002` 取姓名那一處**完全不受影響**(它本來就不看) |
| 刪掉某個 `USAGE = '1'` 的潛在客戶 | `TMKM002` 上那筆名單的 `PR_NAME` 變空白、通聯總覽少一段歷史 |

### 8.2 通聯總覽:三路 `UNION ALL`,兩個代碼分類

`CALLIN_RECORD` 這張結果集是 TMK 對外最複雜的一段 SQL,兩支 M 畫面逐字相同(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:306-348`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:272-314`):

| 路 | 來源 | 代碼分類 | 專案代碼欄填什麼 | 錨點 |
|---|---|---|---|---|
| 1 | `TMK001A` × `TMK002A` | 無(直接接 `TOPIC_MEMO`) | `TMK001A.OUTBND_CODE` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:309-320` |
| 2 | `CRM0061A` × `CRM003A` × `COD006A` | **`'1C'`**(客服進線通聯種類) | 寫死 `'080'` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:322-333` |
| 3 | `TMK0031A` × `COD006A` | **`'84'`**(電訪通聯原因小類) | `TMK0031A.OUTBND_CODE` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:335-345` |

三件要記住的:

1. **同一個欄位名 `CALLIN_CODE` 在兩張表上用不同的代碼分類**:`CRM0061A` 那邊是 `'1C'`,`TMK0031A` 這邊是 `'84'`。兩本字典,值域不重疊(假設;repo 內沒有 `COD006A` 的資料可以驗)。

2. **第二路的專案代碼寫死 `'080'`**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:327`)。`'080'` 不是任何一個真的 `OUTBND_CODE`,只是讓畫面上那一欄有東西顯示、好跟 TMK 自己的紀錄區分。〔客戶特定〕

3. **第一路有正確處理 NULL**:`AND NOT (TMK002A.TOPIC_MEMO IS NULL OR TMK002A.TOPIC_MEMO = ' ')`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:320`)。這是全模組唯一一處明確處理三值邏輯的地方,值得拿來對照 §4.2.2 的 `<> 'A0'`。

4. 三路的 `ID_NO` 都是用 `string.Format` 串進去的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:351`),不是參數化。

### 8.3 TMK 讀別人的表,沒有人讀 TMK 的表

| 表 | TMK 怎麼用 | 錨點 |
|---|---|---|
| `BMS001A`〔共用〕 | 兩支 M 畫面 `LEFT JOIN` 取法代與四個拒絕行銷旗標;整批匯入時當 INSERT 的來源 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:218-219`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:223`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:580` |
| `CRM003A` `CRM0061A`〔共用〕 | 唯讀,見 §8.1、§8.2 | — |
| `COD006A`〔共用〕 | 六種代碼分類的來源;**整批匯入會 INSERT**,見 §8.4 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:333`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:345`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607` |
| `COD009` | 登入帳號對員工代碼,並用離職日過濾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:194-200`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:224`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:193-200` |
| `AA_USER` | 登入帳號對中文姓名;`TMKM901` 用的是 **INNER JOIN**(§4.5.2) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:105`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:126` |
| `TMK_MGN_V` | 主管判斷:有一列就是主管。**名字結尾是 `_V`,應該是 View,但 `DB/View/` 底下沒有它** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:226` |
| `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只在整批匯入那句 INSERT-SELECT 的六個子查詢裡,只讀 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:570-584` |

**反向:母體的「跨模組」欄全空,`crm.md` 與其他六篇也沒有任何一支畫面讀 TMK 的表。**`TMK001A` `TMK002A` `TMK003A` `TMK0031A` `TMK901` 改欄位時,回歸範圍就是 TMK 自己的三支 M 畫面 ＋ 四份 xsd(§4.1.4)。報表側不受影響,因為報表全走 SP,不吃 typed DataSet 的實體表定義。

### 8.4 唯一的例外:整批匯入會往 `COD006A` 塞一列

`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:603-631`:

```
if (EVAStringHelper.GetParamValue(Model, "OUTBND_NAME") != "")   // 加cod006a
    INSERT INTO cod006a (…) VALUES ('P5', :OUTBND_CODE, :OUTBND_NAME, ' ', 'Y', 'Y', 1, '301', …)
```

四件事:

1. **`CODE_SORT` 寫死 `'P5'`**〔客戶特定〕,與 `TMKM901` 讀專案下拉時用的 `new CodeDataSrc("P5")` 是同一本(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:45`)。

2. **`STATUS` 寫死 `'301'`、四眼六個 ID 全填登入者、六個日期全填 `SYSDATE`、`REJECTID` 填一個空白字元**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:623`)。等於**繞過四眼直接生效**,COD 模組的覆核流程完全不知道有這一列。

3. **觸發條件只看名稱欄是不是空字串**。前端在選了既有代碼時會把名稱欄設成唯讀並填上既有名稱(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:162-163`),送出時只有在 `!utxtOUTBND_NAME.ReadOnly` 才把名稱加進參數(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:76-77`)。**所以「選既有代碼 → 不寫 `COD006A`」「打新代碼 → 寫一列」的判斷是靠前端的唯讀旗標,不是靠伺服端查 `COD006A`。**繞過前端就會重複 INSERT。

4. **沒有任何畫面刪得掉這一列。**`TMKM001p1` 只會新增;`COD006A` 的維護畫面在 COD 模組。這與 `crm.md §8.4` 記的「CSV 上傳一筆亂資料,分配期別下拉就多一個選項,而且沒有任何畫面可以刪掉它」是同一型。

| 改什麼 | 會打到誰 |
|---|---|
| 改 `COD006A` 的 `CODE_SORT` 值域 | TMK 六處下拉(`'P4'` `'P5'` `'P9'` `'84'` `'1C'` `'15'` `'20'`)＋ 整批匯入那句 INSERT |
| 改 `COD006A` 的欄位或 NOT NULL 條件 | 整批匯入那句 INSERT 是手寫欄位清單,**不會自動同步** |
| COD 那邊給 `'P5'` 加覆核規則 | TMK 匯入寫進去的那一列會是繞過規則的髒資料 |

### 8.5 共用控件與黑箱

| 控件 / 來源 | 用在哪 | 說明 |
|---|---|---|
| `UltraGridCheckedListManager` | 三個通話彈窗的大小類勾選 grid | **本模組自有**,放在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs`(570 行)。與 CRM 那支同名但是各自一份(`crm.md §8.5`) |
| `ExcelHelper` | 十一支報表的轉 Excel | **本模組自有**,`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs` |
| `ClientBizUtility.GetEMP_INFO` | 八支報表算登入者員工代碼 | 無原始碼,從呼叫端反推;**全部靠位置取第 2 段**(§7.5) |
| `ClientBizUtility.GetMasterEmpNo` | `TMKR003` 判斷主管 | 無原始碼,從呼叫端反推 |
| `SrNoCommentProcessor` | `TMKM002` 的跳號一覽表 | 無原始碼,從呼叫端反推;與 `CASM001` 用同一支,**號別也一起抄錯了**(§4.3.4) |
| `SerialNo.GetOUTBND_NO` | `TMKM002` 取號 | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604` |
| `CRReportTransfer.TransferFileByte` | 十一支報表取 `.rpt` | 無原始碼,從呼叫端反推 |
| `CodeDataSrc` / `GetDropDownDataSrc` | 各畫面的代碼下拉 | 無原始碼,從呼叫端反推;**兩套並存**,`TMKM001` 同一支畫面裡兩種都用到(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107` vs `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:109`) |
| `PrNoDataSrc` / `BF_NODataSrc` | `TMKM002p1` 兩張 grid | 無原始碼,從呼叫端反推;**前置條件寫法不一致**(§4.3.2) |
| `SystemDateTime.GetSystemDateTime(APServer)` | 三個彈窗的通話日期預設值 | 無原始碼,從呼叫端反推 |
| `F_GET_FND_PROF_TYPE` | 整批匯入判斷股票型基金 | DB 函式,`DB/` 內沒有 |

## 附錄 A. 資料表總表

### A.1 母體的五張表

| 表 | 母體欄數 | xsd 欄數 | 四眼 | 主檔於 | 明細於 | 跨模組 |
|---|---|---|---|---|---|---|
| `TMK001A` | 50 | 49(`TMKM001`)/ 47(`TMKM002`) | Y | `TMKM001` `TMKM002` | — | 無 |
| `TMK002A` | 32 | 33 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK0031A` | 24 | 25 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK003A` | 24 | 25 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK901` | **0** | 26(DataTable 名 `TMKM901`) | Y | `TMKM901` | — | 無 |

母體與 xsd 的欄數差異來源:母體算的是實體表定義,xsd 多了 `DATAID`(框架欄)與畫面用的衍生欄(`TMK002A` 的 `RECONTACT_DT` / `RECONTACT_TM`)。`TMK901` 母體記 0 欄是因為掃描器在 `DB/Table/` 找不到它的 DDL,`architecture.md §9` 的模組地圖也記成 `?`。**`TMK901` 的欄位定義只存在於 xsd 裡**(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:15-127`)。

### A.2 實體表名與 xsd DataTable 名對照

| 實體表 | xsd DataTable | 說明 |
|---|---|---|
| `TMK001A` | `TMK001A` | 同名 |
| `TMK002A` | `TMK002A` | 同名 |
| `TMK003A` | `TMK003A` | 同名 |
| `TMK0031A` | `TMK0031A` | 同名 |
| `TMK901` | **`TMKM901`** | **不同名**,`xTableMapping("TMK901", "TMKM901")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36`) |

### A.3 母體之外、TMK 實際會動到的表

| 表 | 動作 | 出現在 |
|---|---|---|
| `COD006A` | **INSERT** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623` |
| `BMS001A` `CRM003A` `CRM0061A` `COD009` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只讀 | §8.3 |
| `AA_USER` `TMK_MGN_V` | 只讀,**兩者都不在掃描索引裡** | §8.3 |

### A.4 只存在於結果集、沒有同名實體表的 DataTable

| DataTable | 出現在 | 欄數 |
|---|---|---|
| `CALLIN_RECORD` | `TMKM001` `TMKM002` | 7 |
| `OUTBND_TOTAL` | `TMKM001` | 8 |
| `TMK001A1` | `TMKM001` | 2 |
| `CRM003A`(在 `TMKM002Model.xsd` 內) | `TMKM002`,**沒人填** | 69 |
| `TMKR001_1`–`TMKR010_3`、`TMKR901T0`–`TMKR901T4` | 11 支報表 | 見 §3.4 |

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:**一支都沒有**

母體第 3 節是空的。`DB/` 底下找不到任何 TMK 的 SP / Function / Trigger / View。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 類 | 名稱 | 被誰呼叫 | 參數數 |
|---|---|---|---|
| SP | `S_TA_TMKR001_GET` | `TMKR001` | 3 in ＋ 3 refcursor |
| SP | `S_TA_TMKR002_GET` | `TMKR002` | 3 in ＋ 3 refcursor |
| SP | `S_TA_TMKR003_GET_1` `_2` `_3` | `TMKR003` | 5 in ＋ 2 / 1 / 1 refcursor |
| SP | `S_TA_TMKR004_GET_1` `_2` | `TMKR004` | 6 in ＋ 1 refcursor |
| SP | `S_TA_TMKR005_GET_1` | `TMKR005` | 5 in ＋ 1 refcursor |
| SP | `S_TA_TMKR005_GET_2` | **沒有人呼叫**(整段被註解掉,`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR005_PO.cs:94`) | — |
| SP | `S_TA_TMKR006_GET_1` `_2` | `TMKR006` | 8 / 4 in ＋ 4 / 1 refcursor |
| SP | `S_TA_TMKR007_GET_1` | `TMKR007` | 5 in |
| SP | `S_TA_TMKR008_GET_1` | `TMKR008` | 5 in |
| SP | `S_TA_TMKR009_GET_1` | `TMKR009` | 6 in ＋ 2 refcursor |
| SP | `S_TA_TMKR010_GET_1` | `TMKR010` | 14 in ＋ 3 refcursor |
| SP | `S_TA_TMKR901_GET` | `TMKR901` | 11 in ＋ 5 refcursor |
| Fn | `F_GET_FND_PROF_TYPE` | `BatchAdd` 判斷股票型基金 | 2 in |
| View(推測) | `TMK_MGN_V` | 兩支 M 畫面的主管判斷 | — |
| Table(推測) | `AA_USER` | `TMKM901` 與報表 | — |

**這 15 個物件是本模組最大的黑箱。**所有報表口徑、主管的定義、股票型基金的判斷全在裡面。要改報表數字,九成是改 SP 不是改 C#。

## 附錄 C. 代碼對照

### C.1 專案代碼 `OUTBND_CODE`

| 值 | 意義 | 來源 |
|---|---|---|
| `'A0'` | AO 新開發客戶(`TMKM002` 的世界) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:161`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` |
| 其他 | 行銷專案,值來自代碼分類 `'P5'`;整批匯入時可以現場新建 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:617` |
| `'080'` | **不是真的專案代碼**,是通聯總覽第二路(客服進線)的顯示用標記 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:327` |

### C.2 通話種類 `CALLIN_CODE`(前三碼)

| 前三碼 | 統計欄 | 中文名 |
|---|---|---|
| `'001'` | `WILL_NUM` | 有意願申購 |
| `'004'` | `UNWILL_NUM` | 無意願申購 |
| `'004004'` | `OTHER_PRD_NUM` | 其他產品(**是 `'004'` 的小類,會重複計**) |
| `'005'` | `THK_NUM` | 勿打擾 |
| `'007'` | `NOCONTACT_NUM` | 無法聯絡 |

錨點:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391`、`:403`、`:415`、`:427`、`:439`。**這五個值是 repo 內唯一能看到通話種類語意的地方。**

### C.3 代碼分類(`COD006A.CODE_SORT`)

| 分類 | 用途 | 錨點 |
|---|---|---|
| `'P4'` | 電訪重點 `TOPIC_CODE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:44` |
| `'P5'` | 專案代碼 `OUTBND_CODE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:45`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:617` |
| `'P9'` | 通聯原因**大類** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61` |
| `'84'` | 通聯原因**小類** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:345` |
| `'1C'` | 客服進線通聯種類(CRM 那邊的) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:333` |
| `'15'` | 風險屬性 `CUST_STYLE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:109` |
| `'20'` | 客戶等級 `CUST_CLASS` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:113` |
| `'440'` | 完成碼 `READY_YN` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:195` |
| `'476'` | 再郵寄別 `MAIL_AGAIN` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:192` |
| `'482'` | 是否含已結案清單(查詢條件) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107` |

### C.4 報表選項值域

見 §7.3 的表。**三支報表的「彙總 / 明細」用了三組不同的碼。**

### C.5 其他在程式裡出現的字面量〔客戶特定〕

| 值 | 意義 | 錨點 |
|---|---|---|
| `'301'` | 整批匯入寫入的資料狀態碼(已生效) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:579`、`:623` |
| `'00'` | 風險屬性查無時的預設值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:578` |
| `-1` / `"-1"` | 潛在客戶沒有戶號時的哨兵值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:63`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759` |
| `"2"` | 有效代碼預設值(「新戶開發」) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:392`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:456` |
| `1` | `TMK0031A.CALLIN_SEQ` 固定值 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:531` |
| `'08201'` | 電訪部門(六支報表固定) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:88` |
| `'08001'` `'08201'` | `TMKR901` 的銷售機構白名單 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:79` |
| `'G2'` / `'G11'` | `TMKR901` 的業務員部門 / `TMKR003` 的主管部門 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57` |
| `"20200101"` | `TMKR901` 專案下拉的起始日 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:87` |
| `'99991231'` | `COD009` 離職日為空時的代用值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| `"D11"` | 整批匯入的 `OUTBND_NO` 補零位數 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:647` |

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

`atlas_scan.py --module TMK` 的母體:畫面 14(B 0 / I 0 / M 3 / R 11)· 表 5 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 24 · Service 0。

本文逐一交代:14 支畫面全部提及(§3.1、§3.4)、5 張表全部提及(附錄 A.1)、24 份 rpt 全部提及(§7.1)。

### D.2 母體沒列到、但本文寫了的東西

| 項目 | 為什麼寫 |
|---|---|
| `TMKM001p0` `TMKM001p1` `TMKM002p0` `TMKM002p1` `TMKM002p2` 五支彈窗 | 它們不是獨立畫面(沒有六層),但業務邏輯有一半在裡面 |
| `AA_USER` `TMK_MGN_V` | 只出現在 SQL 字串裡,掃描器抓不到;主管權限與姓名顯示都靠它們 |
| `COD009` `BMS001A` `CRM003A` `CRM0061A` `COD006A` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 同上,只出現在 SQL 字串裡 |
| 13 支報表 SP(見附錄 B.2)、`F_GET_FND_PROF_TYPE` | 母體 SP 欄是 0,因為 `DB/` 內沒有;但程式確實在呼叫 |
| `TMKR901RPS0` | 程式指名但檔案不存在,列進來就是為了記錄這個缺陷 |

### D.3 母體列了、本文交代不足的

| 項目 | 交代程度 |
|---|---|
| 24 份 `.rpt` 的**版面內容** | 只寫到檔名、標題、對應選項與 SP。`.rpt` 是二進位,repo 內無法閱讀;欄位配置要開 Crystal Reports 才看得到 |
| `TMK901` 的實體欄位定義 | `DB/` 內沒有 DDL,只能從 xsd 反推(附錄 A.1) |
| 各 SP 的實際口徑 | 完全無法從 repo 得知(附錄 B.2) |

### D.4 標「假設」的地方總表

| # | 假設 | 依據 | 在哪一節 |
|---|---|---|---|
| 1 | TMK = 電話行銷 / CallOut | 欄位中文名、grid 標題「電話行銷CALL OUT記錄明細檔」、報表名 | §0.1 |
| 2 | `TMKM001` 是專案外撥、`TMKM002` 是 AO 新開發 | `'A0'` 切分 ＋ `TMKM002` 註解掉的舊碼寫「新戶開發(固定)」 ＋ `TMKM001` 靠專案代碼整批匯入 | §0.1、§0.2 |
| 3 | `TMKM901` 是名單移轉 | 欄位中文名「原CallOut專員」「新CallOut專員」＋ 覆核時的兩段 UPDATE / MERGE | §4.5.1 |
| 4 | 「名單什麼時候該打」靠人工,不靠系統 | 有活動日期與下次可連絡日期欄,但沒有任何程式讀它們去派工;模組內無 B 型畫面與 Service | §0.3、§6 |
| 5 | `'1C'` 與 `'84'` 兩本代碼字典值域不重疊 | 兩張表的 `CALLIN_CODE` 各自 join 不同的 `CODE_SORT`;`COD006A` 的資料不在 repo 內 | §8.2 |
| 6 | `TMKR001` / `TMKR002` 沒有查詢權限是刻意的 | 它們的維度是「建立者」,像主管報表;但程式無註解 | §7.8 |
| 7 | `TMK_MGN_V` 是一支 View | 名字結尾 `_V` ＋ 用法是「有一列就是主管」;`DB/View/` 內沒有它 | §8.3 |
| 8 | `TMKM901` 的 MERGE 範圍放大是漏寫不是設計 | 第一步逐列精準更新、第二步只用專案＋原專員比對;兩步的粒度不一致 | §4.5.3 |
| 9 | 全形空白會讓 MERGE 整句失敗 | Oracle 語彙分析器是否接受 U+3000 取決於字元集與版本,**repo 內無法驗證,務必實測** | §4.5.3、附錄 E10 |

## 附錄 E. 讀本文時要注意的地方

讀碼發現的缺陷與陷阱。每條:缺陷 / 影響 / 錨點 / 嚴重度。

### E1 平行畫面只改一邊:四個拒絕行銷旗標在 `TMKM002` 是死的

- **缺陷**:`TMKM002` 的主檔 SQL 照樣 `SELECT BMS001A.REJ_SELL_CHK / _DOC / _WEB / _PHONE` 四欄,但 `TMKM002Model.xsd` 的 `TMK001A` 沒有這四欄(它們被宣告在那張沒人填的 `CRM003A` DataTable 上),四個 checkbox 的 `Visible = false`,UI 程式一行都沒指派。

- **影響**:**AO 新開發畫面上看不到「拒絕電訪」旗標。**電訪專員在這支畫面開單時,不會被提醒這位客戶已表示拒絕電訪。`TMKM001` 那邊四個 checkbox 都正常顯示。這是業務層級的差異,不是排版差異。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:214-217`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:949-964`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.Designer.cs:2015-2016`、對照 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:243-246`。

- **嚴重度**:**高**(法遵相關的旗標看不到)。

### E2 平行畫面只改一邊:再聯絡日期的拆法

- **缺陷**:`TMKM001` 的 `TMK002A` 明細 SQL 已經從 `TO_CHAR(TO_DATE(RECONTACT_DTTM,'YYYYMMDDHH24MISS'),…)` 改成 `SUBSTR(RECONTACT_DTTM,1,8)`,舊版留在註解裡;`TMKM002` 還是舊版。

- **影響**:`RECONTACT_DTTM` 只要有一筆格式不合(長度夠 10 但不是合法日期),`TMKM002` 會丟 `ORA-01861`,整個明細撈不回來;`TMKM001` 不會。**同一張表、同一筆資料,兩支畫面一支能開一支不能開。**

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:460-465`(新)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:468-477`(註解掉的舊版)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:326-331`(還是舊版)。

- **嚴重度**:**中高**。

### E3 同一件事兩套實作,而且舊的那套沒有主鍵條件

- **缺陷**:`TMKM002` 有兩支通話彈窗。舊的 `TMKM002p0` 用 `FirstOrDefault()` 抓 `TMK003A`、用 `Select()` 抓 `TMK0031A`,**兩個都不帶任何條件**;新的 `TMKM002p2` 用四段主鍵比對與 `GetDataFilter`。兩支同時存在,入口不同(按鈕 vs 雙擊 grid)。

- **影響**:只要這張單有兩個以上的項次,走 `TMKM002p0` 就會:(1) 改到**第一個**項次的通話記錄,不管你現在編的是哪一個;(2) 把不在本次勾選裡的**所有項次**的通聯原因 `Delete()` 掉。`TMKM002p0` 的註解自己寫「此功能對會對應一份通訊記錄,所以不做篩選(全部取出)」——這個前提在 `p2` 允許多項次之後就不成立了。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:74-75`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:113`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:255-256`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:268-269`;對照 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:120-125`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:453-454`。

- **嚴重度**:**高**(靜默的資料遺失)。

### E4 跳號一覽表記到別人的號別,七處一致

- **缺陷**:`TMKM002` 取的號是 `SrNo.OUTBND_NO`(值 `"TMK001A"`),但七個四眼事件寫跳號紀錄時全部傳 `SrNo.AllotNoForNfd`(值 `"OFD220A"`,境內申購書號)。

- **影響**:TMK 的跳號稽核紀錄全部落在申購書號那一本帳上。查 OFD 申購書跳號時會看到一堆 TMK 的紀錄,查 TMK 的跳號則什麼都查不到。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:378`、`:384`、`:390`、`:396`、`:402`、`:408`、`:414`;號別定義在 `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`;取號在 `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:151`。同型見 `bbs.md` 附錄 E1。

- **嚴重度**:**中**(稽核用,不影響業務資料)。

### E5 有訊息但沒有 `return`:`TMKM901` 檢核失敗照樣改資料

- **缺陷**:`TMKM901_BeforeAddButtonClicked` 檢核失敗只設 `e.Cancel = true`,後面的 `foreach` 照樣執行,把未勾選的列 `Delete()`。

- **影響**:使用者一筆都沒勾就按新增 → 跳「至少勾選一筆資料」→ 存檔被取消,但畫面上的名單**全部被標記成刪除**。再按一次新增就什麼都沒有了。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99`。

- **嚴重度**:**中高**。

### E6 覆核回報永遠成功:`TMKM901` 的 `args.Cancel` 在迴圈裡被覆寫

- **缺陷**:`args.Cancel = dbProduct.ExecuteNonQuery(...) != 1;` 寫在 `foreach` 內,每一圈都覆蓋前一圈的結果。

- **影響**:十列裡第三列在 `TMK002A` 找不到,第四列成功 → `Cancel` 被設回 false、`CancelMsg` 也被蓋掉。**覆核成功,但有一筆沒移轉到,而且沒有任何人知道。**這與 DSM `DSMB001_PO.cs:75` 硬寫 `i = 1` 是同一型。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185`。

- **嚴重度**:**高**。

### E7 CSV 遇壞列 `break`,靜默吃掉後面全部

- **缺陷**:整批匯入讀 CSV 時 `if (line.Length < 2) break;`。

- **影響**:檔案中間有一列少了逗號(或有一個空行),**後面所有列全部消失**,畫面上不會有任何提示,匯入照樣成功。一千筆的名單可能只進去三百筆。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:111`。

- **嚴重度**:**高**。

### E8 匯入筆數回報多一筆,而且空檔也回報成功

- **缺陷**:`int i = 1;` 被同時當成 `OUTBND_NO` 的流水號與回報的筆數。迴圈結束後 `AddResultRow(true, i, "")` 回報的是「實際筆數 + 1」。CSV 一筆都沒有時 `i` 仍是 1,照樣回報成功。

- **影響**:對帳對不起來;而且「匯入 0 筆」與「匯入 1 筆」在畫面上長得一樣(都顯示「複製成功」,因為前端只看 `ReturnCode`)。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:642`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:83-87`。

- **嚴重度**:**中**。

### E9 `AND` 應該是 `OR`:`TMKM002` 的哨兵值判斷是死碼

- **缺陷**:`if (string.IsNullOrWhiteSpace(mainRow.PR_NO) && mainRow.PR_NO == "-1")`。空白字串不可能等於 `"-1"`,條件恆為 false。

- **影響**:潛在客戶序號的哨兵值 `-1` 會被原樣填進畫面的 Searcher,再一路存進 `TMK001A.PR_NO`。同型見 CAS `CASB001_PO.cs:431`。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759-762`。

- **嚴重度**:**中**。

### E10 全形空白混進 SQL:`TMKM901` 的 MERGE

- **缺陷**:`ON　(A.OUTBND_CODE = …` 的 `ON` 後面是 U+3000(全形空白),不是 ASCII 空白。

- **影響**:Oracle 的語彙分析器是否把 U+3000 當成空白,取決於用戶端字元集與版本。**如果不接受,整句 MERGE 會丟語法錯,`TMKM901` 的覆核就等於壞的**(第一步的 `TMK002A` 已經更新,但交易會回滾)。repo 內無法驗證,**務必實測**。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:230`。

- **嚴重度**:**高(待實測)**。

### E11 `TMKM901` 的 MERGE 範圍比工單大

- **缺陷**:第一步逐列用四段主鍵精準更新 `TMK002A`;第二步的 `MERGE INTO TMK001A` 卻只用「專案代碼 ＋ 原專員員工代碼」比對,沒有 `OUTBND_NO` 與 `ID_NO`。

- **影響**:只勾三筆,`TMK001A` 上那位專員在該專案的**全部**名單的 `EMP_NO` 都會被改掉。**是設計還是漏寫,程式碼無法分辨,需要業務確認。**

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:169-186`(第一步)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:224-226`(第二步的比對條件)。

- **嚴重度**:**高**。

### E12 `TMKM901` 帶資料用 INNER JOIN `AA_USER`,離職的人帶不出來

- **缺陷**:`FROM TMK002A,TMK001A, AA_USER WHERE … AND TMK002A.USER_ID_T = AA_USER.USERID`。

- **影響**:這支畫面的主要情境就是「專員離職,把名單轉給別人」。**如果帳號已經從 `AA_USER` 移除,他名下的名單一筆都帶不出來**,畫面上只會顯示空白,不會說為什麼。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68`、`:72`。

- **嚴重度**:**中高**。

### E13 Oracle 三值邏輯:`<> 'A0'` 遇 NULL 是 UNKNOWN

- **缺陷**:`TMKM001` 有兩處 `OUTBND_CODE <> 'A0'`,一處在主檔 `WHERE`、一處在 CTE `MYTMK002A`。

- **影響**:`OUTBND_CODE` 若為 NULL,那筆被靜默濾掉。`OUTBND_CODE` 是主鍵所以理論上不會 NULL,**但這是全模組僅有的兩處 `<>` 比較,而 CAS `CASB001_PO.cs:214`、CLS `CLSM001_PO.cs:179`、DSM `DSMB001_PO.cs:136` 三個模組都因為同一型寫法出過事**。要改 `OUTBND_CODE` 的 NOT NULL 條件前先看這兩行。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:206`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`。

- **嚴重度**:**低(目前)/ 中(改 schema 後)**。

### E14 字串串接進 SQL

- **缺陷**:五處把值直接 `string.Format` 進 SQL:登入者帳號、姓名 `LIKE`、再聯絡日期起訖、通聯總覽的統編、專案總計的專案代碼。

- **影響**:值內含單引號就會語法錯,惡意值可以改變語意。姓名欄是自由文字輸入,風險最高。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:259`、`:261`、`:263`、`:265`、`:351`、`:451`;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`、`:241`、`:243`、`:245`、`:317`。另外 `UltraGridCheckedListManager.GetDataFilter` 也是字串組 DataTable 篩選(`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:538`)。

- **嚴重度**:**中高**。

### E15 `catch` 把所有例外翻譯成一句話

- **缺陷**:四處把不同原因的失敗壓成同一句訊息。

- **影響**:連線失敗、SQL 語法錯、權限不足在畫面上看起來都一樣。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:82`(「查無資料」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:664`(「執行失敗,請檢查」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:693`(「檢核失敗,請檢查」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:454`(「取得批次失敗,請檢查」——**訊息裡的「批次」跟這支方法一點關係都沒有**)。

- **嚴重度**:**中**。

### E16 例外訊息直接丟給使用者看

- **缺陷**:整批匯入彈窗兩處 `ShowMessage(..., ex.ToString())`,顯示完整堆疊。

- **影響**:使用者看到一整面 .NET 堆疊;同時洩漏內部路徑與類別名。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:130`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:159`。同型見 CAS `CASM004_PO.cs:227`、COD `CODM009_Pxy.cs:36`。

- **嚴重度**:**中**。

### E17 「查無資料」與「SP 失敗」在報表上長得一樣

- **缺陷**:十一支報表 PO 的成功零筆與 `catch` 都是 `AddResultRow(false, 0, "")`,訊息都是空字串。

- **影響**:SP 掛掉時使用者看到「無符合查詢條件的資料。」,會以為是條件下錯,不會回報問題。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:80`、`:88`;畫面端 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352`。

- **嚴重度**:**中**。

### E18 報表 PO 的 `catch` 先 `tran.Rollback()`

- **缺陷**:`tran` 在 `try` 的第一行才指派;`BeginTransaction()` 自己丟例外時 `tran` 是 null,`catch` 裡再丟 `NullReferenceException`。

- **影響**:原始錯誤被吃掉,`HandleBusinessException` 收到的是 NRE。十一支報表全中。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:51-54`、`:85-90`。

- **嚴重度**:**中**。

### E19 產 Excel 失敗完全沒有訊息

- **缺陷**:`if (GenExcelFile(...) == true) 顯示成功`,沒有 `else`;`ExcelHelper` 用錯誤訊息字串 `Contains("0x800A03EC")` 判斷要不要吞例外。

- **影響**:存檔被防毒擋掉、路徑沒權限、檔案被開著 → 使用者按完鈕什麼都沒發生,以為還在跑。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs:67-75`。

- **嚴重度**:**中**。

### E20 `TMKR901` 指名一支不存在的 `.rpt`

- **缺陷**:`GetReportFileTitle()` 回 `("TMKR901RPS0", "")`,`Dev/ATLAS.TMK.Report/Source/CrystalReports/Report.TMK/` 底下沒有這個檔。

- **影響**:`TMKR901` 的預覽與列印兩條路都拿不到報表,只有轉 Excel 能用。同型見 `bbs.md` 附錄 E11。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:194`;母體第 4 節的 24 份清單。

- **嚴重度**:**高**。

### E21 `TMKR901` 算了登入者員工代碼卻沒傳

- **缺陷**:`xUserEmpNo` 在 `FormInitial` 算好,`GetQueryVDB` 沒有把它加進參數。

- **影響**:這支報表沒有任何登入者查詢權限過濾,任何能開這支畫面的人都看得到全部資料。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:143-185`。

- **嚴重度**:**中高**。

### E22 `TMKR009` 的錯誤訊息掛在錯的控件上

- **缺陷**:「AO代碼(起) 不可大於 AO代碼(迄)」這條錯誤被 `AddError` 到 `udatPRINT_YYMM`(列印年月)上。

- **影響**:紅框標在列印年月欄,使用者會去改日期,改不好。同型見 CLS `CLSR002_PO.cs:864`。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:216-221`。

- **嚴重度**:**低**。

### E23 `TMKR009` 只填「AO代碼(迄)」時,迄會被靜默丟掉

- **缺陷**:`EMP_NO_END` 的 `AddParametersRow` 巢狀在 `EMP_NO_ST` 的判斷式裡面。

- **影響**:只填迄不填起 → 兩個參數都不傳 → 查全部,使用者以為有過濾。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:109-117`。

- **嚴重度**:**低**。

### E24 被註解掉但外殼還在的六處

| 處 | 內容 | 錨點 |
|---|---|---|
| 1 | 「只有第一個項次能設有效代碼」的整段判斷(兩支彈窗) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:374-381`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:345-352`。**外層的 `first` 變數還在算,但只剩下面那個 `IsAddNew` 分支用得到** |
| 2 | 查詢前「五個條件必須擇一填寫」(兩支 M 畫面) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:129-139`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:100-111`。`TMKM001` 後來在 `DoSearchValidate` 補回來了,`TMKM002` 沒有——註解寫「因需查詢所有,故改為不check」 |
| 3 | `TMK003A.COMMENT1` 的回寫(`TMKM001p0` 與 `TMKM002p2`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:477`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:444`。**只有舊的 `TMKM002p0` 還在寫**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:260`),所以同一張表的同一欄有人寫有人不寫 |
| 4 | `TMKM002` 的整段明細欄位回寫(15 行) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:448-472`。主檔頁上那幾個明細控件現在只是擺設 |
| 5 | `TMKR005_PO` 的 `rpt_type` 分支 | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR005_PO.cs:83-115`。`rpt_type` 變數在 `:58` 算出來後**完全沒用到**;`S_TA_TMKR005_GET_2` 因此是一支沒人呼叫的 SP |
| 6 | `TMKR006` 的每月配額數頁首參數 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:159`。參數照傳給 SP,但報表上印不出來 |

- **嚴重度**:**低到中**(第 3 條會造成資料不一致)。

### E25 其他讀碼陷阱

| # | 內容 | 錨點 |
|---|---|---|
| 1 | 主檔 SQL 有**兩個 `LEFT JOIN` 都叫 `X`**(`TMK_MGN_V X` 與 `MYTMK002A X`)。目前因為兩者沒有同名欄位被引用而能跑,任何一邊加欄位就會 `ORA-00918` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227`、`:231` |
| 2 | `LEFT JOIN MYEMP_LIST Z ON 1 = 1` —— 沒有關聯條件的 join,靠 `WHERE` 裡的 `Z.EMP_NO = TMK001A.EMP_NO` 收尾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:229-230` |
| 3 | 整批匯入的子查詢 alias `A` 蓋掉外層的 `FROM BMS001A A` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:572` |
| 4 | 四句 DELETE 包在 `string.Format` 裡但樣板沒有 `{0}`,傳進去的參數完全沒用 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-602` |
| 5 | `CheckExists` 先塞一句不合法的 `"SELECT 1 = 1"` 佔位,靠後面覆蓋才沒事 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:679` |
| 6 | 再聯絡時間的檢核訊息說「必須介於1~24時之間」,實際只擋 0,25 以上照過(三處都一樣) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:546-551`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:870-875`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:512-517` |
| 7 | 有效代碼變更時無提示覆蓋同名單全部項次 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 8 | `GetLAST_USERID` 取的是 `MAX(USER_ID_L)`(上次服務人員),方法名與註解卻說「最後指派人員」 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:433-438` |
| 9 | `TMKM901` 的「已覆核不可修改」用 `APPROVEID != string.Empty` 判斷;ATLAS 的預設值常是一個空白字元 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84` |
| 10 | `TMKM901` 把「伺服器一列結果都沒回」當成成功 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:125` |
| 11 | `GetCRM003A_Row` 有三組重複的 `HM_TEL_AREA` / `HM_TEL` 指派,後兩組是複製貼上殘留 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:842-853` |
| 12 | `TMKM002p1` 兩張 grid 的 `LIKE` 前置條件寫法不一致(一邊自動加 `%`,一邊要自己加) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:66` vs `:83-84` |
| 13 | `TMKM002` 新增列時 `Convert.ToDecimal(this.custBF_NO.Value)`,潛在客戶沒有戶號時會丟例外 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:969`、`:985` |
| 14 | `TMKM001_Ctl.CheckExists` 的區域變數叫 `m_OFDM907_PO` —— 從 OFD 那支畫面複製過來沒改名 | `Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM001_Ctl.cs:66` |
| 15 | `TMKM001_Pxy` 的兩支自訂方法 `new TMKM001_Ctl()` 而不用 `this.Control`;`GetExceptionResult` 定義了卻沒人呼叫 | `Dev/ATLAS.TMK/Source/FormProxy/FormProxy.TMK/TMKM001_Pxy.cs:30-36`、`:43`、`:59` |
| 16 | 範本下載用 `Encoding.Default` 寫檔,讀回來的 `StreamReader` 用預設 UTF-8 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:87` vs `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:104` |
| 17 | 通聯原因大類是用 `code.Substring(0, 3)` 取的,代碼短於 3 碼會丟例外 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416` |
| 18 | `TMKM001` 的通聯管理器註解說「只建一次」,但每次關掉彈窗都 `Dispose()`,下次靠 `Initialize` 重建 → 每開一次彈窗就重查兩次 `COD006A` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`:464`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:302-327` |
| 19 | `TMKM001` 的主檔 SQL 有兩行 180 個以上的空白把註解推到極右,`TMKM002` 也照抄 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:180`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:203` |
| 20 | `TMKM002` 的七處 `throw new ApplicationException("")` 是**空訊息例外** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:378`、`:384`、`:390`、`:396`、`:402`、`:408`、`:414` |

### E26 編碼:全模組乾淨

TMK 與 TMK.Report 兩個專案底下所有 `.cs` / `.xsd` / `.config` **全部是 UTF-8 with BOM**,沒有 cp950 混編的問題(這在 ATLAS 裡算少見,`bbs.md` 附錄 E14 記的 BBS 那邊是混的)。唯一的編碼問題是 E25 第 16 條的 CSV,以及 E10 那個混進 SQL 的全形空白。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。重點:`TMKM001` / `TMKM002` 的 `'A0'` 分治與逐層相似度量測、11 支 R 與 24 份 rpt 的對應、從 TMK 側驗證 `crm.md §8.1` 的 `USAGE` 分治、26 條讀碼陷阱 |

由 build_doc.py v2.0.0 於 2026-09-15 10:47 產生 · 標題 118 · 圖 5 · 表格 69 · 程式錨點 593 · § 連結 87 · 引用檢查：畫面 17（缺 0） · Table 17（缺 0） · Report 24（缺 0） · 結果集 27（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
