<!-- 由 tools/build_copilot_kb.py 從 modules/ofd9.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFD9 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀五段:§0.2(這一片最反直覺的事)、§4.1(四組共用主檔)、§4.3(受益憑證線)、§8(跨模組,含給 BBS 的 `OFD721`)、附錄 E(踩雷)。

> ⚠ **範圍**:`OFD` 是全庫最大的模組,550 支畫面。本文**只寫 `DataEntity.OFD9` 這一片的 56 支 M 畫面**,其餘在 OFD 的其他片。凡本文說「本片」,指的都是這 56 支。 ⚠ **業務意義是推測**。ATLAS 的選單 / 權限表不在版控(`architecture.md §9`),56 支畫面**沒有一支**在 Designer 裡寫 `this.Text`,所以畫面中文名全部由控件標籤、欄位 `msdata:Caption`、SQL 註解與代碼字典反推,逐條標依據。 ⚠ **〔客戶特定〕**:銷售機構代碼(`'09001'`)、`CTL014` 的 `SOURCETYPE` 代碼(`'130'`–`'136'` / `'238'` / `'701'` / `'705'`)、獎金鎖定碼 `'2'`、報表代碼設定表的內容為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`OFD721`(給 BBS 十支畫面、COD、OFDB、OFDI)、`OFD724`(給 `OFDM271` / `OFDB327`)、`OFD374`(給 BMS / RSP)、`OFD562`(給 BMS)、`OFD907`(給孤兒 `OFDM913`)、`OFD432A` / `OFD437A`(給 `OFDB431` / `OFDB433`)、`SAL915A`(給共用下拉)七組跨界,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、資料存取與 SQL 看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。憑證狀態機的另一半在 `bbs.md §2`,本文 §4.3 與 §8.1 與它對帳。

## 0. 系統邊界與角色

### 0.1 這 56 支在管什麼(推測)

**一句話:`DataEntity.OFD9` 這一片不是一條業務線,是 OFD 模組「編號 369 以後」那一段的雜燴——十四條互不相干的業務線擠在同一個 Entity 專案裡。**

先講清楚「第 9 片」是什麼。`OFD` 模組的 Entity 層被切成編號的子專案(`DataEntity.OFD` 一路到 `DataEntity.OFD9`),切法是**畫面代號的數字區段**,不是業務分類。本片 56 支 M 畫面的 DataEntity 全部落在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/`(例 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM721Model.xsd`), UIEntity 對應 `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD9/`, 其餘四層(UI / FormProxy / Control / PO)則與 OFD 其他片**混在同一個專案** (`Dev/ATLAS.OFD/Source/UI/UI.OFD/`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/` 等)。 **所以「片」只在 Entity 層是實體邊界,在其他四層只是編號習慣。**這一點決定了改動影響面怎麼估:改 xsd 只重編兩個專案,改 PO 會重編整個 OFD。

推測依據四條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 控件中文標籤 | `OFDM725` 有「領取方式」「代領人」「執行功能」;`OFDM450` 有「計算戶號」「排除戶號」「服務費計算規則」;`OFDM931A` 有「年度」「月份」「轉出路徑」 | 三支 Designer,以 `grep -n` 取 `.Text` / `.Caption` 字串,不 Read Designer |
| 欄位 `msdata:Caption` | `OFD721` 是「受益憑證期別」「受益憑證號碼」「憑證單位數」「憑證來源碼」「憑證狀態」;`OFD913A_UPD` 是「新業務員編」「原業務姓名」「是否共耕」 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM721Model.xsd`、`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM913AModel.xsd` |
| 代碼字典的中文 | `CER_STATUS`「憑證狀態[131]」九個值、`CER_SOURCE`「憑證來源碼[130]」五個值、`VISA_ID`「實體憑證簽證代碼[135]」三個值、`TASK_ID`「實體憑證作業碼[134]」六個值 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2305-2478` |
| PO 內的原始註解 | 「(執行功能)為簽證修改時,要更新挑選憑證(OFD721.CER_STATUS = 2)」、「CTL_CODE=2為確認鎖定」、「有憑證贖回中單位數就不撈取」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:88`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:142`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:298` |

十四條業務線與對應畫面(**全部標「推測」**,依據見上表與 §4 各節):

| # | 線(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A | 業務 / 通路歸屬與整批移轉 | `OFDM374` `OFDM375` `OFDM376` `OFDM377` | `OFD374`〔共用〕`OFD375A` `OFD376` `OFD377` |
| B | 業務組織與 KPI 獎金 | `OFDM369` `OFDM371` `OFDM391` `OFDM392` `OFDM395` `OFDM399` `OFDM931A` `OFDM931B` | `OFD369A` `OFD371` `OFD372` `OFD373` `OFD391A` `OFD392A` `OFD393A` `OFD394A` `OFD395A` `OFD399A` `OFD931A` |
| C | 客戶拜訪與通路據點主檔 | `OFDM382` `OFDM383` `OFDM385` | `OFD381` `OFD020` `OFD071` |
| D | 群組與服務費率設定 | `OFDM430` `OFDM431` `OFDM431bb` `OFDM432` `OFDM433` `OFDM434` `OFDM435` `OFDM436` | `OFD429A` `OFD431A` `OFD432A` `OFD436A` `OFD437A` `OFD435A` `OFD440A` |
| E | 銷售機構服務費 / 手續費分成契約 | `OFDM450` `OFDM454` `OFDM456` `OFDM458` | 20 張 `SAL9xx` |
| F | 基金清算與合併 | `OFDM481A` `OFDM482A` `OFDM485` | `OFD494A` `OFD496A` `OFD484A` |
| G | 匯率 | `OFDM531` | `OFD531` |
| H | 受益人大會投票 | `OFDM540` `OFDM541` `OFDM543` | `OFD540A` `OFD541A` `OFD542A` |
| I | 扣款帳號核印 | `OFDM562` `OFDM700` `OFDM710` `OFDM711` `OFDM712` `OFDM713` `OFDM714` | `OFD562`〔共用〕`OFD700` `OFD710A` `OFD711` `OFD712` `OFD713` `OFD702` |
| J | 實體受益憑證 | `OFDM721` `OFDM722` `OFDM723` `OFDM724` `OFDM725` | `OFD721`〔共用〕`OFD722` `OFD724`〔共用〕 |
| K | 結匯銀行 | `OFDM731` | `OFD731` `OFD732` |
| L | KYC / 風險屬性問卷 | `OFDM694B` `OFDM741` `OFDM742` `OFDM743` | `OFD694A` `OFD741` `OFD742` `OFD743` `OFD744` `OFD745` `OFD746` `OFD747` |
| M | 集保 | `OFDM751` | `OFD751` |
| N | 法遵申報與洗錢防制 | `OFDM871` `OFDM872` `OFDM907` `OFDM913A` | `OFD871` `OFD872` `OFD907`〔共用〕`OFD913A_UPD` |

**十四條線之間幾乎沒有程式呼叫。**唯一真正相連的是 J 線內部(`OFDM721` 寫 `OFD724` 與 `OFD722`、`OFDM723` 與 `OFDM724` 寫 `OFD721`)與 B 線的 `OFDM931A` 對 `OFDM931B`(互相查對方的覆核狀態,§4.1.3)。其餘全靠表相連,或者根本不相連。

### 0.2 這一片最反直覺的六件事

**(1) 同一個 PO 目錄裡有兩種資料庫方言,SQL Server 與 Oracle 並存。** `architecture.md §4` 已經指出全庫「支不支援 SQL Server」是個未解問題。本片給出答案:**兩邊都活著**。

| 方言 | 特徵 | 本片哪幾支 |
|---|---|---|
| SQL Server | 中括號表名、`@參數`、`SqlDbType`、`getdate()`、`ISNULL()`、`TOP(1)`、`dbo.PADLeft()` | `OFDM374` `OFDM375` `OFDM376` `OFDM377` `OFDM431bb` `OFDM711` `OFDM712` `OFDM713` `OFDM721` `OFDM722` `OFDM724` `OFDM725` `OFDM731` `OFDM741` `OFDM742` |
| Oracle | `:參數`、`OracleDbType`、`SYSDATE`、`NVL()`、`DECODE()`、`ROW_NUMBER() OVER` | `OFDM369` `OFDM391` `OFDM392` `OFDM395` `OFDM399` `OFDM430` `OFDM432` `OFDM433` `OFDM434` `OFDM435` `OFDM436` `OFDM450` `OFDM454` `OFDM456` `OFDM481A` `OFDM482A` `OFDM485` `OFDM531` `OFDM540` `OFDM541` `OFDM543` `OFDM700` `OFDM723` `OFDM751` `OFDM871` `OFDM872` `OFDM907` `OFDM913A` `OFDM931A` `OFDM931B` |

錨點:SQL Server 那邊看 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:290-301`(`UPDATE` 帶 `getdate()`)與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:207`(`dbo.PADLeft`); Oracle 那邊看 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:74-84`(`SYSDATE` 與 `NVL`)與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:85-90`(`ROW_NUMBER() OVER (PARTITION BY …)`)。 `architecture.md §3` 說 `BaseEVADaoPO` 建構子鎖死 Oracle——**這句話對新世代成立,對本片 22 支舊世代 PO(21 支 `BasicEVAPO` + 1 支 `MultiRowEVAPO`)不成立**。

**這件事最咬人的地方在 `OFDM723` 與 `OFDM724`**:兩支共用主檔 `OFD724`、都會更新 `OFD721`,一支寫 Oracle、一支寫 SQL Server。細節見 §4.1.2。

**(2) `OFD721` 這張 BBS 的核心表,在 OFD 側的主檔畫面完全不改 `CER_STATUS`。** `bbs.md §8` 留了一個問題:「如果 OFD 的維護畫面可以直接改狀態而不走同一套條件,BBS 這邊的所有狀態轉換前提就失效了」。答案是:**`OFDM721` 與 `OFDM725` 這兩支主檔持有者一次都沒碰過 `CER_STATUS`**,真正在 OFD 側改它的是 `OFDM723`(簽證),而且**帶來源狀態條件**,與 BBS 的寫法一致。§8.1 逐條對帳。

**(3) 「共用主檔」有四組,但只有一組是真的雙胞胎。** `OFDM431` 與 `OFDM431bb`、`OFDM723` 與 `OFDM724`、`OFDM931A` 與 `OFDM931B`、`OFDM721` 與 `OFDM725` 四組共用主檔。代號代換後逐行比對,相似度差到天差地遠:`OFDM931A` 與 `OFDM931B` 四層平均 **0.985**(是複製貼上的分身), 其餘三組全部低於 **0.75**(是「剛好用同一張表」而已)。§4.1 有完整矩陣。 **結論先講:只有 `OFDM931A` 與 `OFDM931B` 要「改一支就同步另一支」,而且已經有三處只改了一邊。**

**(4) 20 張 `SAL9xx` 表沒有對應的 SAL 模組,而且與 DSM 的 `SAL050` / `SAL051` 不是同一家族。** `dsm.md §8` 查過:全庫沒有 `ATLAS.SAL` 專案、沒有 SAL 開頭的畫面代號。本片再確認一次(附錄 D.3), 並補上 `dsm.md` 沒查的那一半:`SAL9xx` 是**銷售機構(通路)服務費 / 手續費分成契約**的表, 主鍵是 `SNO`(契約序號)、關聯鍵是 `AGENT_ID` 加 `AGENT_CODE`(銷售機構區別碼 + 代碼), 與 `SAL050` / `SAL051`(業務部門 / 人員編制,主鍵 `SAL_DEPT_NO` 加 `EMP_NO`)**沒有任何欄位或程式關係**。§4.2 展開。

**(5) 「六層齊全」的 56 支裡,有一支同名近親的 PO / Ctl / Pxy 根本沒進 csproj。** 那是 `OFDM913`——**不是**本文負責的 `OFDM913A`。兩者除了代號長得像之外毫無關係: `OFDM913` 的主檔是 `OFD907`(跟 `OFDM907` 同一張),`OFDM913A` 的主檔是 `OFD913A_UPD`。而且 `OFDM913_PO.cs` / `OFDM913_Ctl.cs` / `OFDM913_Pxy.cs` 三個檔都在磁碟上、都沒有被任何 csproj 收進去。§4.6.4 與附錄 E 有完整證據。

**(6) 四眼在本片是「有沒有 13 欄」與「走不走引擎」兩件事,而且兩者不同步。** 掃描器報本片 22 張表「有四眼欄位」;但實際上 `OFDM721` / `OFDM725` / `OFDM723` / `OFDM724` 這四支**繞過四眼引擎自己下 SQL**, 其中 `OFDM721` 更直接在新增時把 `EntryID` / `VerifyID` / `ApproveID` 三欄**全寫成同一個人、狀態直接寫已覆核** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:271-279`)。也就是「表上有四眼欄位」不等於「這筆資料經過四眼」。這正是 `architecture.md §3` 講的那件事,本片是第三個實例。

### 0.3 這一片不管什麼

- **不管交易**。申購 / 贖回 / 轉換的主檔與流程不在本片(在 OFD 的其他片,例如 `OFDM231A` 的 Entity 在 `DataEntity.OFD8`)。本片只在憑證線碰到交易的結果。

- **不管基金主檔**。`OFD081` / `OFD081A` / `OFD081V`(基金基本資料)本片一律唯讀 join,維護畫面在別片。

- **不管受益人主檔**。`BMS001` / `BMS001A` 同樣唯讀 join,維護在 BMS(`bms.md`)。唯一例外是 `OFDM374` 與 `OFDM375` 會更新 `BMS001`(§4.4),這是本片唯一寫別人主檔的地方。

- **不管批次與報表**。本片 56 支全是 M。對應的 B / R 畫面(`OFDB431` `OFDB433` `OFDB459` `OFDB871` `OFDB913` `OFDB921` `OFDB327` 等)在 `ATLAS.OFDB` 與 `ATLAS.OFD.Report`,不在本文範圍(§5 到 §7)。

- **不管代碼字典的維護**。`CTL014` 的值由 CTL 模組維護,本片只讀。

### 0.4 使用角色(推測)

依據是各畫面的檢核對象與 `OFDM931A` 與 `OFDM931B` 那組互卡的訊息文字 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:187` 的「OFDM931B 通路尚未覆核」與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:186` 的「OFDM931A HR尚未覆核」):

| 角色 | 碰哪幾支 | 依據 |
|---|---|---|
| HR / 人資 | `OFDM931A` | 只改 `HR_ADD_AMT` 與 `HR_MEMO`,訊息自稱 HR |
| 通路 / 單位主管 | `OFDM931B` | 只改 `G_ADD_AMT` 與 `G_MEMO`,欄位中文名「單位主管調整原因」 |
| 業務內勤 | A / B / C 線 | 歸屬移轉、拜訪單、據點主檔 |
| 通路業務(機構業務) | D / E 線 | 群組、費率、`SAL9xx` 契約 |
| 基金會計 / 清算 | F / G / H 線 | 清算、合併、匯率、受益人大會 |
| 帳務後檯(實體憑證保管) | I / J 線 | 核印、配號、簽證、送件、領取 |
| 法遵 / 稽核 | N 線 | `OFDM907`(實質受益人)、`OFDM871` 與 `OFDM872`(申報) |

**沒有一支畫面在程式裡檢查使用者身分。**全片 grep 不到任何角色或權限判斷式;權限由框架的選單層控制,而選單表不在版控(`architecture.md §9`)。所以上表只是「誰會用」,不是「誰擋得住」。

### 0.5 全域開關

三個會改變整片行為的外部值:

| 開關 | 在哪 | 影響 | 錨點 |
|---|---|---|---|
| 獎金季鎖定旗標(當季計算已完成) | 資料庫的獎金控制表,由 `OFDB921` 批次寫 | `OFDM369` `OFDM391` `OFDM392` `OFDM395` `OFDM399` `OFDM931A` `OFDM931B` 七支**全部被鎖住不能改** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:143-144` |
| `CTL014` 的 `SOURCETYPE` 代碼表 | 資料庫 `CTL014` | 本片至少 12 個下拉清單的值域,含 `'130'` 到 `'136'`(憑證六組碼)、`'238'`(印鑑種類)、`'701'`(職務別)、`'705'`(季別) | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2305-2478`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM700_PO.cs:71` |
| 基金群組「已覆核」過濾 | 資料庫 `SAL915A` | 全庫的「基金群組」下拉只收已覆核的群組;本片 E 線四支與共用控件都吃它 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2742`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2768` |

第三條特別要記:`architecture.md §3` 說 `STATUS` 的實際字面值查不到,只能從 SQL 的比較反推。本片給了一條硬證據——`STATUS LIKE '3%'` 用來表示「已覆核」,而 `OFDM931A` 的 `STATUS IN ('301','302')` 與 `OFDM931B` 的 `STATUS IN ('201','202')` 剛好對上「2 開頭等於已輸入待覆核、3 開頭等於已覆核」 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:175`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:176`)。 **這是本片對 `architecture.md §3` 那條「假設」的補強證據,但仍不是常數定義本身。**

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD9 全景：歸屬移轉、KPI 獎金、群組費率契約、實體受益憑證，以及其餘八條互不相干的業務線
圖中文字:① 業務與通路歸屬：單筆走四眼、整批不走 / OFDM374 / 受益人歸屬 OFD374 / OFDM375 / 整批移轉 不走四眼 / OFDM376 OFDM377 / 通路歸屬 同一套程式 / BMS001 / 被直接 UPDATE / ② 業務組織與 KPI 獎金：七支被同一個開關鎖住 / OFDM369 OFDM391 / 獎金年月/年度參數 / OFDM392 OFDM395 / KPI 與分配比率 / OFDM399 OFDM371 / 達成數 部門階層 / OFDM931A OFDM931B / 獎金調整 真雙胞胎 / OFD922A / 鎖定旗標 由 OFDB921 寫 / ③ 群組 費率 契約：D 線八支 + E 線四支吃 20 張 SAL9xx / OFDM430 OFDM431 / 受益人/基金群組 / OFDM432 OFDM434 / 服務費率 區間重疊 / OFDM450 OFDM454 / 契約 SAL908A/920A / OFDM456 OFDM458 / SAL925A SAL915A / ④ 實體受益憑證：本片唯一有先後關係的一條線 / OFDM722 / 配紙張流水號 / OFDM723 / 簽證 改 CER_STATUS / OFDM724 / 送件 領回 / OFDM725 / 領取 取消領取 / OFDM721 / 重列 自動覆核 / ⑤ 其餘八條線：彼此沒有程式呼叫 / OFDM382 383 385 / 拜訪 分行 券商 / OFDM481A 482A 485 / 清算 給付 合併 / OFDM531 540 541 543 / 匯率 受益人大會 / OFDM562 700 710 711 / 扣款帳號核印七支 / OFDM712 713 714 / 核印對照三胞胎 / OFDM731 751 / 結匯銀行 集保 / OFDM694B 741 742 743 / KYC 問卷三代並存 / OFDM871 872 907 913A / 申報與洗錢防制
```

*圖:圖 1 OFD9 全景。橘框=值得先看的入口或真雙胞胎；橘虛框=不走四眼或含寫死值〔客戶特定〕；灰虛框=別的模組的表。十四條業務線只有 ① ② ④ 三處有跨畫面關係，其餘全靠表相連或完全獨立——這一片是 Entity 專案的切法，不是業務分類。*

看圖的五個重點:

1. **十四條線之間沒有程式呼叫,只有三處例外。**J 線內部三支互寫、B 線 `OFDM931A` 與 `OFDM931B` 互查、A 線 `OFDM374` 與 `OFDM375` 共寫 `BMS001`。其餘全部靠表相連或完全獨立。

2. **`OFD721` 是全片對外輻射最廣的一張表。**BBS 十支畫面、`CODM017`、`OFDB001`、`OFDI011`、`OFDM231A` 都讀它或寫它,而它的主檔畫面在本片(§8.1)。

3. **`SAL9xx` 是一個封閉的 20 張表小宇宙**,只有 `OFDM450` `OFDM454` `OFDM456` `OFDM458` 四支維護、`OFDB459` 一支批次、三個 Common 共用查詢會碰(§4.2、§8.2)。

4. **B 線七支被同一個開關鎖住。**獎金季鎖定旗標一設,`OFDM369` `OFDM391` `OFDM392` `OFDM395` `OFDM399` `OFDM931A` `OFDM931B` 全部不能改(§0.5)。

5. **兩種 SQL 方言的邊界剛好切在 J 線中間。**`OFDM723` 是 Oracle、`OFDM724` 是 SQL Server,兩支改的是同一張 `OFD724`(§4.1.2)。

### 1.2 資料表關係

七組主明細配對 + 一大群沒有明細的單表:

| 組 | 主檔 | 明細 | 配對欄位(從 PO 的 WHERE 反推) |
|---|---|---|---|
| 部門與主管 | `OFD371` | `OFD372` `OFD373` | 部門代碼 |
| KPI 參數(季 / 年) | `OFD392A` | `OFD393A` `OFD394A` | `YEARS` |
| 銷售服務費契約 | `SAL908A` | `SAL909A` `SAL910A` `SAL911A` `SAL912A` `SAL913A` `SAL914A` | `SNO` |
| 手續費分成契約 | `SAL920A` | `SAL921A` `SAL922A` `SAL923A` `SAL924A` `SAL930A` | `SNO` |
| 手續費契約 | `SAL925A` | `SAL926A` `SAL927A` `SAL928A` `SAL929A` `SAL930A` | `SNO` |
| 結匯銀行 | `OFD731` | `OFD732` | 結匯銀行代碼 |
| KYC 問卷(三代並存) | `OFD741` / `OFD743` / `OFD746` | `OFD742` / `OFD744` 加 `OFD745` / `OFD747` | 銷售機構 + 版本號 |

**`SAL930A` 同時是 `OFDM454` 與 `OFDM456` 兩支的明細**——這是本片唯一一張「一個明細掛兩個主檔」的表,改它兩邊都要看(§4.2)。

### 1.3 主要維護畫面的四眼與卡控順序

四條要記住的:

- **34 支走標準四眼引擎,22 支不走或只走一半。**分界線就是 PO 的基底類別:繼承 `BaseEVADaoPO`(17 支)或 `BaseMultiRowEVADaoPO`(17 支)的走引擎;舊世代 22 支裡有 8 支自己寫了 `Execute()` 手下 SQL(§3.5)。

- **卡控主體在 UI 的 `DoValidate()`。**56 支裡只有 11 支在 PO 掛了業務事件做第二道檢核,其餘全靠客戶端。**繞過 UI 就沒有防線**,這一點與 `dsm.md §1` 的結論一致。

- **`OFDM931A` 與 `OFDM931B` 的兩道伺服端閘門回傳 `ReturnCode = true` 當作「擋下」**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:155`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:187`),UI 端也照這個約定讀(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:56`)。**`true` 在這兩支代表失敗,與全庫其他地方相反**,改的時候不要順手「修正」。

- **J 線四支的「勾選才處理」不一致。**`OFDM723` 與 `OFDM725` 檢查勾選欄,`OFDM724` 的勾選判斷**整段被註解**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:100-101` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:134`),所以它處理畫面上**全部**的列(§4.1.2)。

### 1.4 批次 / 報表資料流

本片沒有 B / R 畫面,但有三條「M 畫面被批次鎖住或餵資料」的關係,寫在這裡以免漏看:

| 方向 | 關係 | 錨點 |
|---|---|---|
| `OFDB921` 到 B 線七支 | 批次算完當季獎金後寫鎖定旗標,七支 M 畫面全部鎖定 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:143-155` |
| `OFDB913` 到 `OFDM913A` | 批次把待確認的業務員異動寫進 `OFD913A_UPD`,`OFDM913A` 只做人工確認 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB3/OFDB913Model.xsd` 與 `OFD913A_UPD` 同表 |
| `OFDM432` 與 `OFDM434` 對 `OFDB431` 與 `OFDB433` | 同一張 `OFD432A` 與 `OFD437A` 分別由 M 維護、由 B 批次再寫一次 | 掃描器 `--table OFD432A` 顯示「主檔於 `OFDB431`, `OFDM432`」 |

### 1.5 一日作業泳道

本片沒有排程程式,以下泳道是**假設**,依據是各畫面的鎖定條件與取數條件:

| 時點 | 誰 | 做什麼 |
|---|---|---|
| 交易日盤中 | 帳務後檯 | `OFDM722` 對新產生的憑證配號(憑證狀態進「尚未簽證」) |
| 交易日盤後 | 帳務後檯 | `OFDM723` 送發行 / 註銷簽證(「尚未簽證」轉「正常」),`OFDM724` 送件 / 領回 |
| 憑證印好之後 | 帳務後檯 | `OFDM721` 重列(只收已列印的資料),`OFDM725` 讓受益人領取 |
| 每日 | 業務內勤 | `OFDM374` 與 `OFDM376` 設新客戶歸屬;整批搬用 `OFDM375` 與 `OFDM377` |
| 每季底 | HR 到通路主管 | `OFDM931A` 先做 HR 調整並覆核,`OFDM931B` 才能做通路調整(§4.1.3) |
| 每季底之後 | 系統 | `OFDB921` 計算完成並寫鎖定旗標,B 線七支全鎖 |
| 不定期 | 通路業務 | `OFDM431` 與 `OFDM430` 維群組,`OFDM432` 與 `OFDM434` 設費率,`OFDM450` `OFDM454` `OFDM456` 簽契約 |
| 不定期 | 法遵 | `OFDM907` 確認實質受益人;`OFDM913A` 確認業務員異動 |

## 2. 資料模型

```text
[圖] OFD9 的表關係：三組 SAL9xx 契約、三張實體憑證表、四組主明細，以及名字交叉錯位的四個例子
圖中文字:三組銷售機構契約：主檔 + 五到六張明細，全部以 SNO 相連 / SAL908A / 通路銷售服務費 主檔 / SAL909A ~ SAL914A / 六張明細 全帶四眼 / SAL920A / 手續費分成 主檔 / SAL921A ~ SAL924A / 四張明細 / SAL925A / 手續費 主檔 / SAL926A ~ SAL929A / 四張明細 / SAL930A / 454 與 456 共用明細 / SAL915A / 基金群組 全庫下拉來源 / 實體憑證三張：主鍵同三欄，OFD724 多一個 DATA_SEQ / OFD721 / 境內受益憑證檔 / OFD724 / 待列印簽證檔 / OFD722 / 重列記錄檔 / COD017 / 空白憑證流水號 / 四組主明細 + 一組 KYC 三代 / OFD371 / OFD372 OFD373 / OFD392A / OFD393A OFD394A / OFD731 / OFD732 / OFD741 OFD743 OFD746 / KYC 三代主檔 / 名字交叉錯位：看到名字要先問是實體表還是 DataTable / OFDM742 / 畫面、也是 DataTable / OFD742 / 實體表 掛在 OFDM741 / OFD743 / 實體表 也是 DataTable / OFD746 / 實體表 掛在 OFDM743 / 外部唯讀（join 進來，不屬本片） / BMS001A / 受益人主檔 / OFD081A / 基金主檔 / COD009 / 員工/離職日 / CTL014 / 代碼字典 / OFD922A / 獎金鎖定旗標
```

*圖:圖 2 資料模型。橘框=主檔；白框=明細或同層的表；橘虛框=名字會讓人誤判或跨兩個主檔；灰虛框=別模組的表；黑框=外部唯讀。虛線箭頭=「這個名字其實指向那張表」。SAL930A 是本片唯一一張掛兩個主檔的明細。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

以 PO 建構子為唯一事實來源。`TableMapping` / `xTableMapping` 的兩個參數是**(實體表名, xsd DataTable 名)**, 本片有六處兩者對不起來,先列出來以免誤判(下表「xsd DataTable」欄):

| 畫面 | 主檔實體表 | xsd DataTable | 明細實體表(xsd DataTable) | 錨點 |
|---|---|---|---|---|
| `OFDM369` | `OFD369A` | `OFD369A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM369_PO.cs:39` |
| `OFDM371` | `OFD371` | `OFDM371` | `OFD372`(`OFDM371_OFDM372`)、`OFD373`(`OFDM371_OFDM373`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM371_PO.cs:28-30` |
| `OFDM374` | `OFD374` | `OFDM374` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:48` |
| `OFDM375` | `OFD375A` | `OFDM375` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:30` |
| `OFDM376` | `OFD376` | `OFDM376` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM376_PO.cs:38` |
| `OFDM377` | `OFD377` | `OFDM377` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM377_PO.cs:30` |
| `OFDM382` | `OFD381` | `OFDM382` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM382_PO.cs:24` |
| `OFDM383` | `OFD020` | `OFDM383` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM383_PO.cs:23` |
| `OFDM385` | `OFD071` | `OFDM385` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM385_PO.cs:23` |
| `OFDM391` | `OFD391A` | `OFDM391_Master` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM391_PO.cs:30` |
| `OFDM392` | `OFD392A` | `OFDM392` | `OFD393A`(`OFDM392Q`)、`OFD394A`(`OFDM392Y`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM392_PO.cs:35-37` |
| `OFDM395` | `OFD395A` | `OFDM395_Master` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM395_PO.cs:30` |
| `OFDM399` | `OFD399A` | `OFDM399_Master` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM399_PO.cs:34` |
| `OFDM430` | `OFD429A` | `OFD429A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM430_PO.cs:38` |
| `OFDM431` | `OFD431A` | `OFD431A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:35` |
| `OFDM431bb` | `OFD431A` | `OFDM431` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:21` |
| `OFDM432` | `OFD432A` | `OFD432A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM432_PO.cs:32` |
| `OFDM433` | `OFD436A` | `OFDM433` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM433_PO.cs:32` |
| `OFDM434` | `OFD437A` | `OFD437A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM434_PO.cs:32` |
| `OFDM435` | `OFD435A` | `OFD435A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM435_PO.cs:29` |
| `OFDM436` | `OFD440A` | `OFD440A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM436_PO.cs:29` |
| `OFDM450` | `SAL908A` | `OFDM450` | `SAL909A` `SAL910A` `SAL911A` `SAL912A` `SAL913A` `SAL914A`(同名) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:49-55` |
| `OFDM454` | `SAL920A` | `OFDM454` | `SAL921A` `SAL922A` `SAL923A` `SAL924A` `SAL930A`(同名) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:49-54` |
| `OFDM456` | `SAL925A` | `OFDM456` | `SAL926A` `SAL927A` `SAL928A` `SAL929A` `SAL930A`(同名) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:49-54` |
| `OFDM458` | `SAL915A` | `OFDM458` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM458_PO.cs:29` |
| `OFDM481A` | `OFD494A` | `OFD494A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM481A_PO.cs:45` |
| `OFDM482A` | `OFD496A` | `OFD496A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM482A_PO.cs:42` |
| `OFDM485` | `OFD484A` | `OFD484A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM485_PO.cs:39` |
| `OFDM531` | `OFD531` | `OFDM531` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM531_PO.cs:49` |
| `OFDM540` | `OFD540A` | `OFD540A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM540_PO.cs:47` |
| `OFDM541` | `OFD541A` | `OFDM541` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM541_PO.cs:36` |
| `OFDM543` | `OFD542A` | `OFDM543` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM543_PO.cs:41` |
| `OFDM562` | `OFD562` | `OFDM562` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM562_PO.cs:21` |
| `OFDM694B` | `OFD694A` | `OFDM694B` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM694B_PO.cs:41` |
| `OFDM700` | `OFD700` | `OFDM700` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM700_PO.cs:34` |
| `OFDM710` | `OFD710A` | `OFDM710` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM710_PO.cs:28` |
| `OFDM711` | `OFD711` | `OFDM711` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM711_PO.cs:54` |
| `OFDM712` | `OFD712` | `OFDM712` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM712_PO.cs:61` |
| `OFDM713` | `OFD713` | `OFDM713` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM713_PO.cs:50` |
| `OFDM714` | `OFD702` | `OFDM714` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM714_PO.cs:32` |
| `OFDM721` | `OFD721` | `OFDM721` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:22` |
| `OFDM722` | `OFD722` | `OFDM722` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:17` |
| `OFDM723` | `OFD724` | `OFDM723` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:34` |
| `OFDM724` | `OFD724` | `OFDM724` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:23` |
| `OFDM725` | `OFD721` | `OFDM725` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:23` |
| `OFDM731` | `OFD731` | `OFDM731_Master` | `OFD732`(`OFDM731_Detail`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:27-29` |
| `OFDM741` | `OFD741` | `OFDM741` | `OFD742`(`OFDM742`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs:24-25` |
| `OFDM742` | `OFD743` | `OFDM742` | `OFD744`、`OFD745`(同名) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:27-29` |
| `OFDM743` | `OFD746` | `OFD743` | `OFD747`(同名) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM743_PO.cs:19-20` |
| `OFDM751` | `OFD751` | `OFDM751` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM751_PO.cs:44` |
| `OFDM871` | `OFD871` | `OFDM871` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM871_PO.cs:35` |
| `OFDM872` | `OFD872` | `OFDM872` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM872_PO.cs:34` |
| `OFDM907` | `OFD907` | `OFD907` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:39` |
| `OFDM913A` | `OFD913A_UPD` | `OFD913A_UPD` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:45` |
| `OFDM931A` | `OFD931A` | `OFDM931A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:34` |
| `OFDM931B` | `OFD931A` | `OFDM931B` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:34` |

**兩個名字交叉錯位的陷阱,務必記住**(這是本片最容易讀錯的地方):

| 名字 | 在 `OFDM741` 裡是 | 在 `OFDM742` / `OFDM743` 裡是 |
|---|---|---|
| `OFDM742` | 明細 DataTable 的名字,裝的是實體表 `OFD742` | `OFDM742` 是畫面代號,它的主檔 DataTable 也叫 `OFDM742`,裝的卻是實體表 `OFD743` |
| `OFD743` | 沒出現 | 既是 `OFDM742` 的**實體主檔**,又是 `OFDM743` **主檔 DataTable 的名字**(裝的是實體表 `OFD746`) |

也就是說:看到 `OFD743` 要先問「這是實體表還是 DataTable」;看到 `OFDM742` 要先問「這是畫面還是 DataTable」。錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs:25`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:27`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM743_PO.cs:19`。

另外 `OFDM431bb` 的主檔 DataTable 叫 `OFDM431`(不是 `OFDM431bb`), 與 `OFDM431` 自己用的 `OFD431A` 不同名,所以兩支雖然共用實體表卻不共用 DataTable 定義。本片因此有 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431Modelbb.xsd` 與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431bbModel.xsd` **兩個不同命名法的 xsd 並存**, 還有 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431ModelVDBbb.cs` 與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431bbModelVDB.cs` 兩支 VDB(§4.1.1)。

### 2.2 主鍵與四眼欄位

xsd 不宣告主鍵,只宣告「可不可空」。以「不可空的非四眼欄位」當主鍵的近似值(**假設**,依據是 `architecture.md §4` 說 SQL 的 WHERE 由 `tb.PrimaryKey` 迴圈串出,而 PO 手寫的 WHERE 條件與這組欄位一致):

| 表 | 近似主鍵 | 四眼 13 欄 | 備註 |
|---|---|---|---|
| `OFD721` | `FUND_ID` + `BF_CER_ISSUE_CODE` + `BF_CER_NO` | 表上有(`OFDM721_PO` 的 SELECT 撈得到),xsd 沒定義 | 掃描器報「四眼欄位 無」是因為 xsd 只列 10 欄 |
| `OFD724` | `FUND_ID` + `BF_CER_ISSUE_CODE` + `BF_CER_NO` + `DATA_SEQ` | 有(`OFDM721_PO` 的 INSERT 逐欄列出) | `DATA_SEQ` 是本片唯一的「同一憑證多筆」鍵 |
| `OFD429A` | `BF_NO_GRPCD` + `BF_NO` | 有(大寫命名) | 受益人群組 |
| `OFD431A` | `FUND_GRPCD` + `FUND_ID` | 有(大寫命名) | 基金群組 |
| `OFD437A` | 見 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM434Model.xsd` | 有 | 與 `OFD432A` 同構 |
| `OFD907` | `BF_NO` | 有(混大小寫命名) | 實質受益人 |
| `OFD913A_UPD` | `BF_NO` + `UPD_DATE` | 有(混大小寫命名),另有 `CONFIRM_ID` / `CONFIRMDATE` **第二套覆核欄位** | 見 §4.6.4 |
| `OFD743` | `BF_COUNTRY_X` + `AGENT_ID` + `AGENT_CODE` + `VERSION_NO` + `MENO` | 有 | `MENO`(說明)被標成不可空,**很可能不是主鍵的一部分**,標「假設」 |
| `OFD731` | `TRAN_BRK` | 有 | 結匯銀行 |
| `SAL909A`–`SAL914A` / `SAL921A`–`SAL924A` / `SAL926A`–`SAL930A` | `SNO` + 各自的業務鍵 | 全部有 | 15 張明細全帶四眼 |

**`OFD374` 的欄位清單有兩套大小寫並存**:`DATAID`/`dataid`、`STATUS`/`Status`、`CREATEID`/`CreateID` … 四眼 13 欄各出現兩次,共 34 欄。原因是它的欄位定義**不來自 OFD 自己的 xsd**, 而是 `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd`(混大小寫)與 `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd`(全大寫)兩邊各定義一次,掃描器做了聯集。 **這不是資料庫真的有 34 欄,是兩個模組對同一張表用了不同大小寫慣例。** Oracle 的識別字大小寫敏感(未加引號時一律轉大寫),所以這兩套在 Oracle 上其實是同一批欄位; 但在 SQL Server 上若 collation 區分大小寫就會出事。列入附錄 E。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列本片自有、且有中文名的表。**沒有中文名的欄位一律留空,不自己翻**。

#### `OFD721` 境內受益憑證檔〔共用〕

| 欄位 | 中文名 | 型別 |
|---|---|---|
| `BF_CER_ISSUE_CODE` | 受益憑證期別 | string |
| `BF_CER_NO` | 受益憑證號碼 | string |
| `BF_CER_CHK` | 受益憑證檢查碼 | int |
| `FUND_ID` | 基金代碼 | string |
| `FUND_SH_NM` | 基金中文簡稱 | string |
| `BF_CTL_SRNO` | 受益憑證紙張流水號 | string |
| `CER_UNIT` | 憑證單位數 | decimal |
| `CER_SOURCE` | 憑證來源碼 | string |
| `CER_STATUS` | 憑證狀態 | string |
| `UNIT_DEC` | (無 Caption,單位數小數位) | int |

xsd 只定義 10 欄,但 PO 的 SQL 另外用到 `BF_NO`(戶號)、`CER_RUNIT`(贖回中單位數)、 `REPRT_CODE`(實體憑證重印碼)、`FIRST_PRT_UID` / `FIRST_PRT_DTTM`(首次列印)、 `BF_CER_DATE`、`VISA_UID_D` / `VISA_DTTM_D`、`VISA_RTN_UID` / `VISA_RTN_DTTM`、 `CER_TAKE_UID` / `CER_TAKE_DTTM` / `CER_TAKE_TYPE` / `CER_TAKE_MAN`、`DEL_DATE`、`DataFlag` 與四眼 13 欄 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:247-278`)。 **這張全片最重要的表,超過一半的欄位在 repo 內沒有中文名。**這正是 `architecture.md` 附錄 E 的 E4 那條。

#### `OFD702` 扣款帳號核印檔(`OFDM714` 主檔)

| 欄位 | 中文名 | 欄位 | 中文名 |
|---|---|---|---|
| `SUB_BANK_CODE` | 扣款行代碼 | `SUB_ACC_NO` | 扣款行帳號 |
| `BANK_BRH_SHNM` | 扣款行簡稱 | `SUB_ID_NO` | 扣款人ＩＤ |
| `SUB_BF_NAME` | 扣款人姓名 | `SEAL_TYPE` | 核印扣款方式 |
| `RSP_NO` | 契約書號 | `RSP_SRNO` | 契約序號 |
| `RSP_CHG_NO` | 契約變更書號 | `RSP_CHG_SRNO` | 契約變更序號 |
| `ACC_SUB_ID` | 帳號用途 | `SEAL_USER_NO` | 用戶號碼 |
| `SOURCE_CD` | 申請書來源 | `NEW_OLD` | 新戶或舊戶 |
| `AGENT_BANK` | 代理扣款行代碼 | `AGENT_BANK_SHNM` | 代理扣款行簡稱 |
| `BATCH_ID` | 批次識別碼 | `BATCH_SRNO` | 次批號 |
| `TRADE_TYPE` | 處理類別 | `TRADE_DATE` | 送核/核回日期 |
| `SEAL_STATUS` | 核印狀態 | `SEAL_FAIL_ID_CO` | 核印回覆代碼(公司) |
| `SEAL_FAIL_ID_BK` | 核印回覆代碼(銀行) | `SEAL_FAIL_MEMO` | 帳號核印備註 |
| `ISRETRY` | 重送碼 | `TRADE_NO` | 交易序號 |
| `UpdateDate` | 作業更新日 |  |  |

#### `OFD731` 結匯銀行主檔(`OFDM731` 主檔)

| 欄位 | 中文名 | 欄位 | 中文名 |
|---|---|---|---|
| `TRAN_BRK` | 結匯銀行代碼 | `BRK_NAME` | 結匯銀行中文名稱 |
| `MAIL_ZIP` | 郵遞區號 | `BRK_ADDR` | 聯絡地址 |
| `CNT_P` | 聯絡人姓名 | `CNT_TEL1_AREA` | 聯絡人電話區域碼１ |
| `CNT_TEL1` | 聯絡人電話1 | `CNT_TEL2_AREA` | 聯絡人電話區域碼2 |
| `CNT_TEL2` | 聯絡人電話2 | `CNT_FAX_AREA` | 聯絡人傳真區域碼 |
| `CNT_FAX` | 聯絡人傳真 | `CNT_EMAIL` | 聯絡人EMAIL |

#### `OFD907` 實質受益人歸屬風險(`OFDM907` 主檔)

| 欄位 | 中文名 |
|---|---|
| `BF_NO` | 戶號 |
| `BF_NAME` | 受益人姓名 |
| `RISK` | 歸屬風險 |
| `UPD_DATE` | 最近更新日期 |
| `UPD_END_DATE` | 最近更新日期(迄) |
| `RISK_CODE` | 不適用應辦識及確認公司股東或實質受益人身分 |

#### `OFD913A_UPD` 業務員異動待確認檔(`OFDM913A` 主檔)

| 欄位 | 中文名 | 欄位 | 中文名 |
|---|---|---|---|
| `BF_NO` | 戶號 | `UPD_DATE` | 上傳日期 |
| `BF_NAME` | 客戶姓名 | `DEPT_SH_NM` | 銷售通路 |
| `EMP_NO` | 新業務員編 | `EMP_NAME` | 新業務姓名 |
| `EMP_NAME_OLD` | 原業務姓名 | `CROSS_SAL` | 是否共耕 |
| `CONFIRMDATE` | 覆核日期 | `CONFIRM_ID` | 覆核者 |
| `IsCheck` | 勾選 | `STATUS` | 資料狀態 |
| `STATUSDESC` | 資料狀態 |  |  |

**`STATUS` 與 `STATUSDESC` 兩欄的 Caption 都是「資料狀態」**,而且同一張表還有框架的 `Status`(無 Caption)。三個名字極像、語意不同的欄位放在同一張表,是本片最容易改錯的欄位組(§4.6.4)。

#### `OFD429A` 受益人群組 / `OFD431A` 基金群組

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD429A` | `BF_NO_GRPCD` | 受益人群組代碼 |
| `OFD429A` | `BF_NO` | 受益人戶號 |
| `OFD429A` | `BF_NO_GRPCD_DESCRP` | 受益人群組名稱 |
| `OFD429A` | `BF_NAME` | 受益人姓名 |
| `OFD431A` | `FUND_GRPCD` | 基金群組代碼 |
| `OFD431A` | `FUND_ID` | 基金代碼 |
| `OFD431A` | `GRPCD_DESCRP` | 基金群組名稱 |
| `OFD431A` | `FEE_CALDT_TYPE` | 服務費起算日類型 |
| `OFD431A` | `FUND_SH_NM` | 基金中文簡稱 |

#### `OFD743` KYC 問卷版本(`OFDM742` 主檔)

| 欄位 | 中文名 |
|---|---|
| `BF_COUNTRY_X` | 受益人類別 |
| `AGENT_ID` | 銷售機構區別碼 |
| `AGENT_CODE` | 銷售機構代碼 |
| `AGENT_NAME` | 銷售機構中文簡稱 |
| `VERSION_NO` | 版本號 |
| `MENO` | 說明 |

其餘 66 張表的欄位中文名散在各自的 xsd,查法是 `py -V:3.12 /docs/tools/atlas_scan.py --table <表名>`。 **本片有 24 張表在 repo 內完全沒有欄位定義**(掃描器報「欄位 0」),清單見附錄 A.2。

### 2.4 與其他模組共用的表

| 表 | 本片誰是主檔 | 誰也在用 | 用法 |
|---|---|---|---|
| `OFD721` | `OFDM721` `OFDM725` | BBS 十支 M 畫面、`CODM017`、`OFDB001`、`OFDI011`、`OFDM231A`、`OFDM723`、`OFDM724` | BBS 全部是帶來源狀態的 UPDATE;OFD 側只有 `OFDM723` 改狀態(§8.1) |
| `OFD724` | `OFDM723` `OFDM724` | `OFDM271`、`OFDB327` | 待列印簽證檔;`OFDM721` 也 INSERT 它 |
| `OFD374` | `OFDM374` | `BMSM001`(當明細)、`RSPM004`(直接 INSERT)、`DSMM060`、`OFDI011` | 見 `dsm.md §8` 與 `bms.md` |
| `OFD562` | `OFDM562` | `BMSM001`(欄位定義來源)、`OFDB562`(`ATLAS.OTAB`) | 扣款帳號;`OFDB562` 是 `architecture.md §2` 列的 15 個雙實作代號之一 |
| `OFD907` | `OFDM907` | 孤兒 `OFDM913`(PO 仍宣告它當主檔,但整支沒進 csproj) | §4.6.4 |
| `OFD432A` | `OFDM432` | `OFDB431` | 同一張表 M 與 B 各一個主檔宣告 |
| `OFD437A` | `OFDM434` | `OFDB433` | 同上 |
| `OFD541A` | `OFDM541` | `OFDM542`(不在本片) | 受益人大會投票明細 |
| `SAL915A` | `OFDM458` | `OFDM450` `OFDM454` `OFDM456`、`BasicOFD_PO` 的兩支共用查詢、`FundGrpcdForSAL915ADataSrc` 下拉 | 全庫的「基金群組」下拉來源(§8.2) |
| `SAL908A` `SAL920A` `SAL925A` | `OFDM450` `OFDM454` `OFDM456` | `BasicBMS_PO` 的三個戶號過濾器、`SerialNo` 的兩支取號 | §8.2 |
| `OFD871` `OFD872` | `OFDM871` `OFDM872` | `OFDB871`(同一支批次同時是兩張表的主檔) | 申報資料 |

### 2.5 狀態碼(從程式反推,標來源)

#### 2.5.1 `CER_STATUS` 憑證狀態——**這一節推翻 `bbs.md` 的兩條推測**

`bbs.md §2` 說:「repo 內找不到值域定義檔,以下全部由 UPDATE 語句的來源狀態到目標狀態反推」。 **這句話需要更正:值域定義檔存在**,在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372`,類別名就叫 `CER_STATUS`, 註解寫「憑證狀態[131]」(`131` 是 `CTL014` 的 `SOURCETYPE`)。九個值全部有中文:

| 值 | 常數名 | 官方中文(來自字典) | `bbs.md` 的推測 | 對不對得上 |
|---|---|---|---|---|
| `'1'` | `Normal` | 正常 | 正常流通中 | ✔ |
| `'2'` | `NotYet` | **尚未簽証** | 已印製未交付(標「假設」) | ✘ **推測錯了**。是「尚未簽證」,不是「已印製未交付」 |
| `'3'` | `Lost` | 掛失中 | 掛失中 | ✔ |
| `'4'` | `CancelLost` | 掛失撤銷 | 掛失已撤銷 | ✔ |
| `'5'` | `LostWriteOff` | 掛失註銷 | 已註銷(補發後的舊證) | ✔(字典更精確:限掛失那一路) |
| `'6'` | `Mortgage` | 質設中 | 質設中 | ✔ |
| `'7'` | `CancelMortgage` | 質設解除 | 已質解 | ✔ |
| `'8'` | `ChangeWriteOff` | **換發註銷** | 換發中 | ✘ **推測錯了**。是換發後**被註銷的舊證**,不是「換發中」 |
| `'9'` | `Redem` | 已贖回 | (`bbs.md` 沒列到這個值) | ✘ **漏了一個值** |

三條更正的影響:

1. **`'2'` 是「尚未簽證」**,所以 `bbs.md` 說「沒有任何 BBS 畫面寫入 `'2'`,只被 `BBSM005` 當補發新證的來源狀態讀」完全合理——寫 `'2'` 的是 OFD 側的 `OFDM722`(配號)與 `OFDM723` 的簽證修改(§4.3)。

2. **`'8'` 是「換發註銷」**,`bbs.md` 記的「`BBSM001` 新增換發時把狀態寫成 `'8'`」動作本身沒錯,但語意是「這張舊證因換發而註銷」,不是「這張證正在換發中」。差別在於:`'8'` 是終態,不會再回到 `'1'`。`bbs.md` 同一節說「`BBSM001` 撤銷換發把狀態還原成 `'1'`」——**那條要重新確認**:如果 `'8'` 是終態,撤銷換發把它打回 `'1'` 就是把一張已註銷的憑證救活。這是**跨模組回歸時第一個要問的問題**(§8.1)。

3. **`'9'` 已贖回**:BBS 完全沒處理這個值。`OFDM723.cs:382` 的 UI 有一條 `CER_STATUS == "8"` 的特判(見下),但沒有任何本片畫面處理 `'9'`。**假設**它由贖回批次寫入,依據是 `OFD721` 有 `CER_RUNIT`(贖回中單位數)欄位且 `OFDM725` 會用 `CER_RUNIT = 0` 過濾(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:299`)。repo 內找不到寫 `'9'` 的程式。

本片實際寫 / 讀 `CER_STATUS` 的位置(**全部列出,沒有遺漏**):

| 畫面 | 動作 | 來源狀態 | 目標狀態 | 錨點 |
|---|---|---|---|---|
| `OFDM722` | 查詢條件(配號畫面只看未簽證的) | `= 2` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:112` |
| `OFDM723` 簽證 | UPDATE | `'2'` | `'1'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:74-77` |
| `OFDM723` 簽證修改 | UPDATE | `'1'` | `'2'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:89-92` |
| `OFDM723` 註銷 / 註銷修改 | 不動 `CER_STATUS` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:101-120` |
| `OFDM723` UI | 「換發註銷的憑證不可做簽證修改」 | 讀 `= "8"` | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:382` |
| `OFDM725` | 查詢條件(領取畫面只看正常的) | `= '1'` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:284` |
| `OFDM721` | **完全不碰** | — | — | 全檔 grep 零命中 |
| `OFDM724` | **完全不碰** | — | — | 全檔 grep 零命中 |

#### 2.5.2 憑證線的其他五組代碼(同一份字典)

| 欄位 | 字典位置 | 值 |
|---|---|---|
| `CER_SOURCE` 憑證來源碼[130] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2308-2330` | `1` 申購 · `2` 贖回餘額 · `3` 換發 · `4` 掛失補發 · `5` 總額憑證 |
| `REPRT_CODE` 實體憑證重印碼[132] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2376-2386` | `N` 無重印 · `Y` 有重印 |
| `CER_TAKE_TYPE` 實體憑證領取方式[133] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2390-2408` | `1` 親領 · `2` 代領 · `3` 郵寄 · `4` 承銷代領 |
| `TASK_ID` 實體憑證作業碼[134] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2412-2438` | `1` 申購 · `2` 贖回餘額 · `3` 換發 · `4` 掛失補發 · `5` 總額憑證 · `6` 重印 |
| `VISA_ID` 實體憑證簽證代碼[135] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2442-2456` | `A` 發行簽證 · `D` 註銷簽證 · `X` 尚未作發行或註銷簽證就被刪除 |
| `DEL_ID` 實體憑證註銷來源碼[136] | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2460-2478` | `1` 贖回註銷 · `2` 換發註銷 · `3` 掛失註銷 · `4` 總額憑證註銷 |

`bbs.md` 附錄 C 列的「換發種類」「新舊憑證碼」「銷帳方式」也在同一份 `CTL014.cs` 裡,格式相同。 **結論:`bbs.md §2` 與附錄 C 那些「從程式反推」的代碼表,大部分可以直接用字典校正。**

#### 2.5.3 `STATUS`(四眼狀態)在本片看到的字面值

| 字面值 | 出現處 | 意義(反推) |
|---|---|---|
| `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:279`、`:394`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM369_PO.cs:231` | 已覆核。三處都是 INSERT 時**直接寫死**,等於自動覆核 |
| `'301'` / `'302'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:175` | 「`OFDM931A` 已覆核」的判定集合 |
| `'201'` / `'202'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:176` | 「`OFDM931B` 尚未覆核(還在輸入 / 修改)」的判定集合 |
| `LIKE '3%'` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2742` | 已覆核(所有 3 開頭) |

**與 `architecture.md §3` 的 12 個 `EVAStatusCode` 常數對照**:架構篇說實際字面值查不到,推測是單字元 `'0'`–`'9'`。本片看到的是**三位數**(`201` / `202` / `301` / `302`)。兩邊不衝突——架構篇掃到的單字元比較幾乎都在 BBS / CAS 的舊 SQL Server 那批, 而本片的三位數全部出現在 Oracle 那批。**假設:兩套狀態編碼並存,舊 SQL Server 世代用單字元、Oracle 世代用三位數。** 依據是本片 `OFDM721_PO`(SQL Server 方言)寫的也是 `'301'`,所以這個假設**有反例**,不要當事實用; 要確定只能查資料庫或反編譯 `Vendor.Product.Utility.MappingCode`。

## 3. 畫面清冊

### 3.1 維護 M(56 支,本片全部)

「六層」欄位:`atlas_scan.py --screen` 的六層檢查結果。**56 支全部六層齊全**,這在 OFD 模組很少見 (掃描器報 OFD 模組 550 支裡有 42 支六層不齊,一支都不在本片)。

| 代號 | 中文名(推測,依據見 §4) | 主表 | 明細 | PO 基底 | 方言 |
|---|---|---|---|---|---|
| `OFDM369` | 獎金年月參數 | `OFD369A` | — | `BaseEVADaoPO` | Oracle |
| `OFDM371` | 業務部門與主管設定 | `OFD371` | `OFD372` `OFD373` | `BasicEVAPO` | 無 SQL 方言特徵 |
| `OFDM374` | 受益人歸屬業務員 | `OFD374` | — | `BasicEVAPO` | SQL Server |
| `OFDM375` | 業務員戶號整批移轉 | `OFD375A` | — | `BasicEVAPO` | SQL Server |
| `OFDM376` | 受益人歸屬通路 | `OFD376` | — | `BasicEVAPO` | SQL Server |
| `OFDM377` | 通路戶號整批移轉 | `OFD377` | — | `BasicEVAPO` | SQL Server |
| `OFDM382` | 客戶拜訪單 | `OFD381` | — | `BasicEVAPO` | 無 |
| `OFDM383` | 金融機構分行主檔 | `OFD020` | — | `BasicEVAPO` | 無 |
| `OFDM385` | 券商公司主檔 | `OFD071` | — | `BasicEVAPO` | 無 |
| `OFDM391` | 年度獎金參數 | `OFD391A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM392` | KPI 參數(季 / 年) | `OFD392A` | `OFD393A` `OFD394A` | `BaseEVADaoPO` | Oracle |
| `OFDM395` | 月份獎金參數 | `OFD395A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM399` | 月份獎金明細 | `OFD399A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM430` | 受益人群組 | `OFD429A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM431` | 基金群組 | `OFD431A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM431bb` | 基金群組(第二套) | `OFD431A` | — | `MultiRowEVAPO` | SQL Server |
| `OFDM432` | 基金群組服務費率 | `OFD432A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM433` | 基金群組(服務費規則用) | `OFD436A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM434` | 受益人群組服務費率 | `OFD437A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM435` | 銷售機構服務費除外設定 | `OFD435A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM436` | 受益人戶號服務費設定 | `OFD440A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM450` | 通路銷售服務費契約 | `SAL908A` | 6 張 | `BaseEVADaoPO` | Oracle |
| `OFDM454` | 手續費分成契約 | `SAL920A` | 5 張 | `BaseEVADaoPO` | Oracle |
| `OFDM456` | 手續費契約 | `SAL925A` | 5 張 | `BaseEVADaoPO` | Oracle |
| `OFDM458` | 契約用基金群組 | `SAL915A` | — | `BaseMultiRowEVADaoPO` | 無 |
| `OFDM481A` | 基金清算 | `OFD494A` | — | `BaseEVADaoPO` | Oracle |
| `OFDM482A` | 清算給付明細 | `OFD496A` | — | `BaseEVADaoPO` | Oracle |
| `OFDM485` | 基金合併 | `OFD484A` | — | `BaseEVADaoPO` | Oracle |
| `OFDM531` | 匯率 | `OFD531` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM540` | 受益人大會專案 | `OFD540A` | — | `BaseEVADaoPO` | 無 |
| `OFDM541` | 受益人大會投票明細 | `OFD541A` | — | `BaseEVADaoPO` | Oracle |
| `OFDM543` | 受益人大會回收目標 | `OFD542A` | — | `BaseEVADaoPO` | 無 |
| `OFDM562` | 扣款帳號核印主檔 | `OFD562` | — | `BasicEVAPO` | 無 |
| `OFDM694B` | 投資人風險屬性對照 | `OFD694A` | — | `BaseMultiRowEVADaoPO` | 無 |
| `OFDM700` | 銀行核印途徑 | `OFD700` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM710` | 核印參數 | `OFD710A` | — | `BaseMultiRowEVADaoPO` | 無 |
| `OFDM711` | 核印結果回覆代碼 | `OFD711` | — | `BasicEVAPO` | SQL Server |
| `OFDM712` | 銀行媒體代碼對照 | `OFD712` | — | `BasicEVAPO` | SQL Server |
| `OFDM713` | 扣款行媒體代碼對照 | `OFD713` | — | `BasicEVAPO` | SQL Server |
| `OFDM714` | 扣款帳號核印明細 | `OFD702` | — | `BasicEVAPO` | 無 |
| `OFDM721` | 受益憑證重列 | `OFD721` | — | `BasicEVAPO` | SQL Server |
| `OFDM722` | 受益憑證配號 | `OFD722` | — | `BasicEVAPO` | SQL Server |
| `OFDM723` | 受益憑證發行 / 註銷簽證 | `OFD724` | — | `BaseEVADaoPO` | Oracle |
| `OFDM724` | 受益憑證送件 / 領回 | `OFD724` | — | `BasicEVAPO` | SQL Server |
| `OFDM725` | 受益憑證領取 | `OFD721` | — | `BasicEVAPO` | SQL Server |
| `OFDM731` | 結匯銀行 | `OFD731` | `OFD732` | `BasicEVAPO` | SQL Server |
| `OFDM741` | KYC 題目與答案 | `OFD741` | `OFD742` | `BasicEVAPO` | SQL Server |
| `OFDM742` | KYC 問卷版本 | `OFD743` | `OFD744` `OFD745` | `BasicEVAPO` | SQL Server |
| `OFDM743` | KYC 問卷版本(第二套) | `OFD746` | `OFD747` | `BasicEVAPO` | 無 |
| `OFDM751` | 集保帳戶 | `OFD751` | — | `BaseEVADaoPO` | Oracle |
| `OFDM871` | 陸資申購申報 | `OFD871` | — | `BaseEVADaoPO` | Oracle |
| `OFDM872` | 銷售機構申報 | `OFD872` | — | `BaseEVADaoPO` | Oracle |
| `OFDM907` | 實質受益人歸屬風險 | `OFD907` | — | `BaseEVADaoPO` | Oracle |
| `OFDM913A` | 業務員異動確認 | `OFD913A_UPD` | — | `BaseEVADaoPO` | Oracle |
| `OFDM931A` | 獎金調整(HR) | `OFD931A` | — | `BaseMultiRowEVADaoPO` | Oracle |
| `OFDM931B` | 獎金調整(通路主管) | `OFD931A` | — | `BaseMultiRowEVADaoPO` | Oracle |

「方言 = 無」表示該 PO 沒有自寫 SQL(全部交給四眼引擎的 `xEVAStringHelper` 產生),或只用參數化片語。

### 3.2 查詢畫面(I)

**本片無 I 畫面。**OFD 的 I 畫面集中在 `ATLAS.OFDI` 與 `ATLAS.OFD.Query` 兩個專案 (例 `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`),Entity 也在各自專案而不在 `DataEntity.OFD9`, 所以按本文的切片定義不屬於本片。與本片關係最深的是 `OFDI011`,它 join `OFD721` 與 `OFD374`(§8.1)。

### 3.3 批次(B)

**本片無 B 畫面。**OFD 的 B 畫面在 `ATLAS.OFDB`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB459_PO.cs` 等)。與本片直接相關的四支列在 §1.4 與 §6。

### 3.4 報表(R)

**本片無 R 畫面。**依 `architecture.md §6` 的命名鐵律,R 畫面一律在 `ATLAS.<模組>.Report` 專案, 本片對應的是 `Dev/ATLAS.OFD.Report/`,不在 `DataEntity.OFD9` 的範圍內。不過本片有三支 M 畫面自己做報表 / 匯出:`OFDM725`(簽收單,呼叫 SP)、 `OFDM931A` 與 `OFDM931B`(匯出 Excel,`GetExcelData`),見 §4.1.3 與 §4.3.5。

### 3.5 一眼看出差別的六件事

1. **PO 基底一分為二。**34 支新世代(`BaseEVADaoPO` 17 支、`BaseMultiRowEVADaoPO` 17 支)、 22 支舊世代(`BasicEVAPO` 21 支、`MultiRowEVAPO` 1 支)。**新世代一律 Oracle,舊世代半數是 SQL Server。**

2. **事件掛點的分布極度一致。**34 支新世代裡有 26 支掛的是同樣三個 (`BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData`),handler 內容也都是「組 SQL 字串塞回 `args.DbCmd`」。全片真正掛了業務事件的只有 11 支:`OFDM374`(10 個事件)、 `OFDM371` / `OFDM450` / `OFDM454` / `OFDM456` / `OFDM540` / `OFDM731` / `OFDM741`(含 `BeforeAdd` / `BeforeUpdate`)、 `OFDM485` / `OFDM541`(`AfterUpdate`)、`OFDM913A`(`AfterApprove`)。

3. **五支 PO 完全沒掛任何事件**:`OFDM375` `OFDM377` `OFDM711` `OFDM721` `OFDM722`。前四支的共同點是**自己寫了 `Execute()` 或整套手寫 EVA**,查詢與寫入都不走引擎。

4. **UI 行數落差 15 倍。**最小 `OFDM485` 90 行、最大 `OFDM450` 1,363 行。 1,000 行以上的三支(`OFDM450` `OFDM454` `OFDM872`)全部是多 grid 畫面。

5. **Ctl 行數最大的是 `OFDM721`(811 行)**,而它的 UI 只有 267 行——Model 與 View 的手搬邏輯佔了 Ctl 的八成。 `architecture.md §2` 說的「Model 與 View 的轉換只能寫在 Control 層」,本片最極端的實例。

6. **只有 3 支呼叫 SP**:`OFDM399`(`S_TA_OFDM399_Get`)、`OFDM723`(`S_TA_OFDM723_GET`)、`OFDM725`(`s_OFDM725_Get`)。其餘 53 支全部是程式組的字串 SQL,而這三支 SP **一支都不在 `DB/SP/` 裡**(附錄 B)。

## 4. 維護畫面(M)

```text
[圖] OFD9 實體受益憑證線的流程、CER_STATUS 九個值的歸屬，以及五支畫面的靜默過濾條件
圖中文字:① 一張實體憑證的一生（CER_STATUS 只在第 2 步改） / 交易產生 / 狀態 2 尚未簽證 / OFDM722 配號 / 寫 BF_CTL_SRNO / OFDM723 簽證 / 狀態 2 轉 1 正常 / OFDM724 送件領回 / 寫 VISA_UID_D 等 / OFDM725 領取 / 寫 CER_TAKE 四欄 / OFDM723 簽證修改 / 狀態 1 轉回 2 / OFDM721 重列 / 作廢舊證 自動覆核 / BBS 十支畫面 / 掛失 質設 換發 轉讓 / ② CER_STATUS 九個值：字典在 CTL014.cs，OFD 側只寫兩個 / 1 正常 / OFDM723 簽證寫 / 2 尚未簽証 / OFDM723 簽證修改寫 / 3 4 5 掛失三態 / BBS 寫 / 6 7 質設兩態 / BBS 寫 / 8 換發註銷 / BBS 寫 可逆回 1 / 9 已贖回 / 全庫查不到誰寫 / bbs.md 推測 2 與 8 / 名稱與字典不符 / bbs.md 漏列 9 / 本文補上 / ③ 五支畫面的四種靜默過濾（查無資料的真正原因） / CER_STATUS = 1 / 只有正常憑證 / VISA_RTN_DTTM / 必須已領回 / CER_SOURCE <> 5 / 排除總額憑證 / CER_RUNIT = 0 / 無贖回中單位數 / OFDM725 一律回查無資料 / 四條疊在一起 使用者分不出
```

*圖:圖 4 憑證線。橘框=OFD 側真正會改狀態的地方；灰虛框=BBS 側；黑框=版控外或查不到來源；橘虛框=靜默過濾或與 bbs.md 對不上的地方。OFD 側九個狀態只寫兩個，其餘七個全在 BBS。*

```text
[圖] OFD9 四組共用主檔畫面的差異，以及 SAL9xx 三胞胎
圖中文字:① OFDM931A / OFDM931B：唯一的真雙胞胎，四層相似度 0.985 / OFDM931A / 只寫 HR_ADD_AMT / OFD931A / 同一張表 無型別欄 / OFDM931B / 只寫 G_ADD_AMT / AND/OR 缺括號 / 931B 閘門形同虛設 / ② OFDM431 / OFDM431bb：兩代並存，相似度 0.23 ~ 0.74 / OFDM431 / Oracle 新世代 / OFD431A / 共用實體表 / OFDM431bb / SQL Server 舊世代 / 各漏一半檢核 / 431 漏重複 bb 漏欄位 / ③ OFDM723 / OFDM724：同一張 OFD724，兩種方言兩套規矩 / OFDM723 / Oracle NVL 防 NULL / OFD724 / 共用實體表 / OFDM724 / SQL Server 裸空字串 / 勾選判斷被註解 / 724 對全部列下 UPDATE / ④ OFDM721 / OFDM725：相似度 0.09，只是剛好用同一張表 / OFDM721 / 重列 寫 REPRT_CODE / OFD721 / 共用實體表 / OFDM725 / 領取 寫 CER_TAKE / 兩支都不改狀態 / CER_STATUS 零命中 / 額外一組：任務書沒點名，卻更像複製貼上 / OFDM450 / 通路服務費契約 / OFDM454 / Ctl 與 456 完全相同 / OFDM456 / PO 相似度 0.954 / 450 少一半檢核 / 計算戶號那段被註解
```

*圖:圖 3 共用主檔的四組(加一組)。橘框=需要同步或值得注意的一側；橘虛框=已經只改了一邊的地方。只有第 ① 組是真雙胞胎；② ③ ④ 三組長得完全不像，改表結構時最容易只想到其中一支。*

56 支不可能一支一節寫到同樣深度,本章分四層:

| 層 | 範圍 | 深度 |
|---|---|---|
| §4.1 | 四組共用主檔的畫面(8 支) | 一組一節,含逐行 diff 與「改一支要不要同步」的結論 |
| §4.2 | `SAL9xx` 契約線(4 支) | 一節,含 20 張表的家族結構 |
| §4.3 | 實體受益憑證線(5 支,含 §4.1 的 4 支再展開) | 一節,狀態機與跨模組對帳 |
| §4.4 | 卡控最複雜的 4 支(`OFDM374` `OFDM375` `OFDM907` `OFDM913A`) | 一支一段 |
| §4.5 / §4.6 | 其餘 38 支 | 依業務線分組,表格帶過 |

**卡控結果一律五類**:阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋。

### 4.0 先讀:本片四眼的三種形態

| 形態 | 支數 | 特徵 | 代表 |
|---|---|---|---|
| 標準引擎 | 37 | PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個取數事件(或更少),寫入完全交給 DLL | `OFDM431` `OFDM432` `OFDM907` |
| 引擎 + 業務掛點 | 11 | 上面再加 `BeforeAdd` / `BeforeUpdate` / `AfterUpdate` / `AfterApprove` | `OFDM450` `OFDM374` `OFDM913A` |
| 自己下 SQL | 8 | PO 有一支 `Execute()`,自己開連線、自己交易、自己寫 `Status` | `OFDM375` `OFDM377` `OFDM531` `OFDM721` `OFDM722` `OFDM723` `OFDM724` `OFDM725` |
| 另有批次匯入 | 3 | PO 有一支 `BatchAdd()`,逐列 INSERT 並寫死已覆核狀態 | `OFDM369` `OFDM907` `OFDM913A` |

第三種是本片的風險集中區。它們的共同特徵:

1. **不經過 `architecture.md §3` 的四眼狀態機**,`Status` 直接寫死字面值。

2. **SQL 全部用字串串接**,使用者輸入的值(基金代碼、憑證號碼、代領人姓名)直接進 SQL。

3. **交易只有一層**,沒有 `architecture.md §3` 講的 `TranToDo`(平台庫待辦事項)那一半—— 所以這幾支的動作**不會產生待辦事項**,覆核者在待辦清單上看不到。

### 4.1 四組共用主檔的畫面

#### 4.1.0 相似度矩陣(代號代換後逐行比對)

方法:把兩支同層的檔讀進來,去掉空白行,把畫面代號字面換成同一個記號,再用序列比對算相似度。與 `bbs.md` 處理 `BBSM009` / `BBSM109` 那組、`tmk.md` 處理 `OUTBND_CODE` 那組同一套做法。

| 組 | 共用主檔 | UI | Pxy | Ctl | PO | 判定 |
|---|---|---|---|---|---|---|
| `OFDM931A` / `OFDM931B` | `OFD931A` | 0.983 | 0.997 | 0.996 | 0.965 | **真雙胞胎,必須同步** |
| `OFDM431` / `OFDM431bb` | `OFD431A` | 0.233 | 0.741 | 0.454 | 0.333 | 兩代並存,不是雙胞胎 |
| `OFDM723` / `OFDM724` | `OFD724` | 0.452 | 0.636 | 0.290 | 0.504 | 兩代並存,不是雙胞胎 |
| `OFDM721` / `OFDM725` | `OFD721` | 0.103 | 0.287 | 0.105 | 0.089 | 只是剛好用同一張表 |

**結論先講**:只有第一組需要「改一支就同步另一支」的紀律。但**另外三組更危險**——它們共用實體表卻長得完全不像,所以改表結構(加欄、改型別)時很容易只想到其中一支。§4.1.1 到 §4.1.4 逐組列出「已經只改了一邊」的地方。

另外補一組本片沒被要求、但實際上更像雙胞胎的:`OFDM454` / `OFDM456` 的 **Ctl 相似度 1.000、PO 0.954**(§4.2)。

#### 4.1.1 `OFDM431` / `OFDM431bb` — 基金群組,兩代並存

兩支共用實體表 `OFD431A`(基金群組代碼 → 基金代碼的多對多明細)。

| 面向 | `OFDM431` | `OFDM431bb` |
|---|---|---|
| PO 類別名 | **`OFDM431AOracleDao`**(不是 `OFDM431_PO`) | `OFDM431bb_PO` |
| PO 基底 | `BaseMultiRowEVADaoPO`(新世代) | `MultiRowEVAPO`(**舊世代,全片唯一一支**) |
| 方言 | Oracle(`ROW_NUMBER() OVER`) | SQL Server(中括號 + `@FUND_ID`) |
| 連線物件 | `dbProduct` | `dbTA` |
| xsd DataTable | `OFD431A` | `OFDM431` |
| 基金主檔 join | `OFD081A` | `OFD081` |
| 主檔 SELECT 的 `FUND_ID` | 真值 | **常數空字串 `'' FUND_ID`** |
| 明細 SELECT 含 `FEE_CALDT_TYPE`(服務費起算日類型) | **有** | **沒有** |
| 「基金已在其他群組」檢核 | **沒有** | **有** |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:24`、`:76-99`、`:108-126` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:13`、`:45-62`、`:71-84`、`:111-138` |

**已經只改了一邊的地方,三處:**

| # | 差異 | 哪一邊漏 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `FEE_CALDT_TYPE`(服務費起算日類型)這個欄位只有 `OFDM431` 的明細 SQL 撈得到,`OFDM431bb` 撈不到 | `OFDM431bb` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:113` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:71-76` | **高**。從 `OFDM431bb` 存檔會把這欄寫成 null / 預設值,等於把 `OFDM431` 設好的值洗掉 |
| 2 | 「基金已存在於其他基金群組中,不可重覆設定」只有 `OFDM431bb` 擋 | `OFDM431` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:187-200` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:140-150` | **高**。同一檔基金可以從 `OFDM431` 掛進兩個群組 |
| 3 | 基金主檔一邊 join `OFD081A`、一邊 join `OFD081` | 不確定哪邊對 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:90` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:79` | 中。兩張表若內容不同步,兩支畫面顯示的基金簡稱會不一樣 |

**卡控總表 `OFDM431`**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| `DoValidate` | 明細 0 筆 | 提示「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:146` |
| 查詢 | 群組名稱用 `LIKE`、群組代碼用 `=` | — | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:101-104` |
| 取數 | 主檔用 `ROW_NUMBER() PARTITION BY FUND_GRPCD … WHERE NUM=1` 只取每群第一筆 | 同群其餘列在查詢頁看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:82-93` |

**卡控總表 `OFDM431bb`**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| `DoValidate` | 明細 0 筆 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:178` |
| `DoValidate` | 明細任一列 `FUND_ID` 空白 | 「基金代碼 不可為空白」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:184` |
| `DoValidate` | **逐列**呼叫 `IsFundExsits` 遠端查 `OFD431A` | 「基金已存在於其他基金群組中,不可重覆設定」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:187-200` |
| grid 離格 | 基金代碼必填 | 「'基金代碼'必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:272` |

**`IsFundExsits` 三個問題**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:111-138`):

1. **方法名與行為不符**。名字說「確認基金代碼是否存在」,SQL 查的卻是 `SELECT COUNT(1) FROM OFD431A WHERE FUND_ID = @FUND_ID` ——查的是「這檔基金是否已經被掛在某個群組」,不是「這檔基金存不存在」。全庫另有六支同名方法(`OFDM081A_Ctl` / `OFDM213_Ctl` / `OFDM214_Ctl` / `OFDM215_Ctl` 等)語意也各不相同。

2. **回傳值三義**:找不到回 `0`;找到回 `-1`;**發生例外也回 `-1`**(`catch` 之後落到最後一行 `return -1`)。呼叫端 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:194` 寫 `if (i != 0)` 就報錯—— **資料庫連不上的時候,使用者看到的訊息是「基金已存在於其他基金群組中」**。

3. **檢核不排除自己**。SQL 沒有 `AND FUND_GRPCD <> 當前群組`,所以**修改既有群組時,原本就在這個群組裡的基金也會被判成重複**。要驗這一條,把同一列的 `RowState` 改成 `Modified` 再存檔就會重現(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:189`)。

另外 UI 那個迴圈是**逐列一次遠端呼叫**(`new OFDM431bb_Pxy()` 寫在 `foreach` 內,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:191`), 明細 200 列就是 200 趟 Remoting。`architecture.md §2` 說 `new *_Pxy()` 拿到的是透明代理,這裡的代價是實打實的。

**Entity 層的命名殘骸**:`OFD431A` 這張表在 `DataEntity.OFD9` 下有**兩組不同命名法的 xsd**—— `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431Modelbb.xsd`(舊命名,後綴在 `Model` 後)與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431bbModel.xsd`(新命名,後綴在代號後), 對應的 VDB 也有兩支(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431ModelVDBbb.cs` 與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431bbModelVDB.cs`)。 `atlas_scan.py --screen OFDM431bb` 會回「找不到畫面 OFDM431BB」,因為掃描器把代號轉大寫比對, 而檔名是小寫 `bb`——**掃描器看不到這支畫面**,它不在 908 的清單裡。列入附錄 D。

#### 4.1.2 `OFDM723` / `OFDM724` — 同一張 `OFD724`,兩種方言、兩套規矩

兩支的主檔都是 `OFD724`(受益憑證待列印簽證檔),而且**兩支都會連帶更新 `OFD721`**。

| 面向 | `OFDM723`(簽證) | `OFDM724`(送件 / 領回) |
|---|---|---|
| PO 基底 | `BaseEVADaoPO`(新世代) | `BasicEVAPO`(舊世代) |
| 方言 | Oracle:`SYSDATE` / `NVL()` / `TO_CHAR` | SQL Server:`getdate()` / 中括號 / `dbo.PADLeft` |
| 連線 | `dbProduct` + `dbPTPF`(兩個交易) | `dbTA`(一個交易) |
| 執行功能 | 1 簽證 · 2 註銷 · 3 簽證修改 · 4 註銷修改 | 1 送件 · 2 取消送件 · 3 領回 · default 取消領回 |
| 改 `OFD721.CER_STATUS` | **會**(1 改 `'2'`→`'1'`;3 改 `'1'`→`'2'`) | **不會** |
| 改 `OFD721` 的哪些欄 | `CER_STATUS` + `UpdateID` / `UpdateDate` | `VISA_UID_D` / `VISA_DTTM_D` / `VISA_RTN_UID` / `VISA_RTN_DTTM` + `UpdateID` / `UpdateDate` |
| 空值判斷 | **`NVL(OFD724.VISA_NO, ' ') = ' '`**(防 NULL) | **`WHERE VISA_UID_D = ''`**(不防 NULL) |
| 只處理勾選列 | **有**(`if (Convert.ToBoolean(drw.ISCHECK))`) | **整段被註解** |
| 取號 | `SerialNo.GetVisaNo()`,走 PTPF 交易 | 不取號 |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:28`、`:70-121`、`:139` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:17`、`:54-80`、`:100-101` |

**三處「只改了一邊」:**

| # | 差異 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | **`OFDM724` 不看勾選欄。**`if (Convert.ToBoolean(drw.IsCheck))` 連同它的大括號被註解成 `//{` / `//}`,所以 `foreach` 對畫面上**每一列**下 UPDATE。UI 側對應的「至少須註記一筆資料」檢核也被註解掉,兩邊一致地拆掉了 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:100-101` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:134`;UI 側 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:56` | **高**。grid 上仍有勾選欄,使用者以為勾了才送,實際全送 |
| 2 | **空值防護只做了一半。**`OFDM723` 四個分支全部用 `NVL(欄, ' ') <> ' '`;`OFDM724` 四個分支全部用裸的 `= ''` / `<> ''` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:84`、`:98`、`:109`、`:118` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:60`、`:66`、`:72`、`:78` | **高**。在 Oracle 上空字串就是 NULL,`= ''` 永遠 UNKNOWN、`<> ''` 也永遠 UNKNOWN,**`OFDM724` 的四個 WHERE 會一列都更新不到**,接著 `if (j != 1)` 成立 → rollback + 「更新境內受益憑證待列印簽證檔(OFD724)失敗」。這支若真的跑在 Oracle 上是全功能失效;若跑在 SQL Server 上則只漏掉 NULL 那些列 |
| 3 | **`OFDM723` case 4(註銷修改)把 `VISA_NO` 設成 `''`,case 3(簽證修改)設成 `' '`(一個空白)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:113` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:93` | 中。同一支檔內不一致:後續所有判斷都用 `NVL(VISA_NO,' ') = ' '`,case 4 寫進去的 `''`(Oracle 視為 NULL)剛好被 `NVL` 救回來,**是巧合不是設計** |

**`OFDM724` 還有一個更根本的問題:SET 子句與 WHERE 子句被串在同一個字串裡,再被套用到兩張不同的表。** `strUpdateCol` 同時含 `SET …` 與 `WHERE …`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:57-60`), 然後 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:106` 組出 `UPDATE [OFD724] SET … WHERE … and FUND_ID=…`, `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:122` 組出 `UPDATE [OFD721] SET … WHERE … and FUND_ID=…`。兩張表被迫共用同一組 SET 欄位名(`VISA_UID_D` / `VISA_DTTM_D` / `VISA_RTN_UID` / `VISA_RTN_DTTM`)。 **所以 `OFD721` 與 `OFD724` 必須永遠有這四個同名欄位,加一欄要兩張一起加。**這是隱形的 schema 耦合。

另外 `OFD721` 的 UPDATE **少了 `DATA_SEQ` 條件**(`OFD721` 沒有這一欄), 所以一張憑證在 `OFD724` 有兩筆(重列會產生第二筆,§4.3.1)時, 處理第二筆會再更新 `OFD721` 一次,而 `if (j != 1)` 會因為第一次已經把條件改掉而失敗回滾。 **假設**:實務上靠 `CanUpdate721`(只有 `VISA_ID = 'A'` 才更新 `OFD721`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:88`)避開。依據是 `OFDM721` 重列時會把舊的 `OFD724` 列的 `VISA_ID` 改成 `'X'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:293`), 所以同一憑證同時只有一列是 `'A'`。**但 `CanUpdate721` 讀的是 grid 第 0 列的 `VISA_ID`,不是迴圈當下那一列** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:88` 用 `mVDB.DataEntity.OFDM724[0]["VISA_ID"]`), **多筆混合 `A` 與 `D` 的情況會整批照第一列決定**。列入附錄 E。

**卡控總表 `OFDM723`**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| `DoValidate` | 執行功能未選 | 「執行功能必填」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:48` |
| `DoValidate` | 一列都沒勾 | 「至少須註記一筆資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:56` |
| grid 勾選 | `CER_STATUS == "8"`(換發註銷)且執行功能為簽證修改 | 不給勾 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:382` |
| grid 勾選 | 「該憑證已產生換發註銷資料, 不可取消送簽」 | — | **被註解,不生效** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:369` |
| 查詢 | 簽證修改 / 註銷修改只收 `NVL(VISA_NO,' ') <> ' '` 的列 | 沒簽證過的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:289-297` |
| 查詢 | 一律加 `BF_CTL_SRNO <> '0'`、`NVL(PRT_UID,' ') <> ' '`、`NVL(PRT_DTTM,' ') <> ' '` | 未配號或未列印的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:272-274` |
| 執行 | `UPDATE OFD724` 影響列數不等於 1 | 「更新境內受益憑證待列印簽證檔(OFD724)失敗」+ 整批 rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:151` |
| 執行 | `UPDATE OFD721` 影響列數不等於 1 | 「更新境內受益憑證檔(OFD721)失敗」+ 整批 rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:168` |

注意 `BF_CTL_SRNO <> '0'`:`BF_CTL_SRNO` 在 xsd 裡是 string、在 `OFDM721_PO` 裡卻用 `SqlDbType.Int` 綁 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:446`),而這裡又拿字串 `'0'` 比。**同一欄三種型別認知**,列入附錄 E。

**卡控總表 `OFDM724`**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| `DoValidate` | 執行功能未選 | 「執行功能必填」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:43` |
| `DoValidate` | 憑證種類未選 | 「憑證種類必填」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:48` |
| `DoValidate` | 一列都沒勾 | — | **被註解,不生效** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:56` |
| 查詢前 | 未選基金代碼 | 「請先選擇基金代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:253` |
| 查詢 | 送件只收 `VISA_UID_D = ''`;取消送件 / 領回收 `VISA_UID_D <> ''` 且 `VISA_RTN_UID = ''`;取消領回收 `VISA_RTN_UID <> ''` | NULL 的列全部看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:184-197` |
| 查詢 | 取消領回時額外加 `OFD721.CER_TAKE_UID = ''`(已領取的不可取消領回) | 已領取的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:194-197` |
| 執行 | `UPDATE OFD724` / `UPDATE OFD721` 影響列數不等於 1 | 對應訊息 + rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:112`、`:128` |

#### 4.1.3 `OFDM931A` / `OFDM931B` — 唯一的真雙胞胎

兩支共用實體表 `OFD931A`(季獎金調整),各自只負責表上的一組欄位:

|  | `OFDM931A` | `OFDM931B` |
|---|---|---|
| 負責欄位 | `HR_ADD_AMT` 調整金額、`HR_MEMO` 調整原因 | `G_ADD_AMT` 調整金額、`G_MEMO` 調整原因 |
| grid 鎖住不給改的欄 | `ADD_AMT`、**`G_ADD_AMT`**(對方的欄) | `ADD_AMT`、**`HR_ADD_AMT`**(對方的欄) |
| 角色(推測) | HR | 通路 / 單位主管 |
| 錨點 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:80-84`、`:217` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931B.cs:82-85`、`:219` |

**不是靠一個型別欄位分流**(不像 `bbs.md` 的 `MOR_TYPE='0'/'1'` 或 `tmk.md` 的 `OUTBND_CODE='A0'`), 而是靠「各自只寫自己那兩欄」+「互相檢查對方的覆核狀態」。也就是說, **表上沒有任何欄位能區分一列是由哪一支畫面建立的**;要知道誰動過只能查 `LOG_OFD931A`(見下)。

**互卡閘門**(這一組是本片最複雜的跨畫面卡控):

| 畫面 | 閘門邏輯 | 訊息 | 錨點 |
|---|---|---|---|
| `OFDM931A` | 查 `LOG_OFD931A` 取每季最新一筆(`RANK() OVER(PARTITION BY QDATE ORDER BY UPDATEDATE DESC)` 取 `RANK=1`);若該筆是 `FUNCTION_ID='OFDM931B'` 且 `STATUS IN ('201','202')`,`COUNT(*) > 0` 就擋 | 「OFDM931B 通路尚未覆核,不可修改。」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:172-188` |
| `OFDM931B` | 同一支查詢,條件改成 `FUNCTION_ID='OFDM931A' AND STATUS IN ('301','302') OR FUNCTION_ID='OFDM931B'`;`COUNT(*)` 等於 `"0"` 就擋 | 「OFDM931A HR尚未覆核,不可修改。」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:171-187` |
| 兩支共用 | 查獎金控制表,當季已鎖定就擋 | 「當季計算已完成鎖定(OFDB921),不可修改。」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:141-156`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:139-155` |

**`OFDM931B` 的閘門有 `AND` / `OR` 缺括號的缺陷**,與 `cas.md` 記的 `CASB001_PO.cs:431` 同型:

```
WHERE B.RANK=1 AND (B.FUNCTION_ID='OFDM931A' AND B.STATUS IN ('301','302') OR B.FUNCTION_ID='OFDM931B')
```

`AND` 的優先序高於 `OR`,所以括號內實際上是 `(FUNCTION_ID='OFDM931A' AND STATUS IN ('301','302')) OR (FUNCTION_ID='OFDM931B')`。後半段**完全不看狀態**——只要最新一筆是 `OFDM931B` 自己寫的,不管它是 `201`(剛輸入)還是 `301`(已覆核), `COUNT(*)` 都大於 0,閘門就放行。結果:**`OFDM931B` 只有在「這一季從來沒有人動過」或「最新一筆是 `OFDM931A` 且尚未覆核」時才會被擋; 只要它自己先動過一次,之後永遠不會再被 HR 的覆核狀態擋住。** 錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:175`。嚴重度 **高**。

**另外三處只改了一邊:**

| # | 差異 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | 判定寫法不對稱:`OFDM931A` 用 `Convert.ToInt32(Rows[0][0]) > 0` 擋,`OFDM931B` 用 `Rows[0][0].ToString() == "0"` 擋。一個是「有就擋」,一個是「沒有就擋」——邏輯本來就相反,但**兩支都沒有檢查 `Rows.Count`**,查詢回空集合會 `IndexOutOfRangeException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:184` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:183` | 中 |
| 2 | 同一個欄位 `G_MEMO` 的 grid 標題:`OFDM931A` 寫「單位主管調整金額原因」,`OFDM931B` 寫「單位主管調整原因」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:355` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931B.cs:357` | 低 |
| 3 | `OFDM931A_PO` 的鎖定查詢寫 `CTL_CODE='2'`(無空白),`OFDM931B_PO` 寫 `CTL_CODE = '2'`(有空白);SQL 註解也一字之差 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:144` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:142` | 低(但證明兩邊是各自手改,不是同步改的) |

**`DoValidate` 的死碼**:兩支的 `DoValidate()` 結尾是

```
if (this.ValidateErrList.ErrorCount > 0) return true;
return true;
```

兩條分支回傳同一個值,`if` 完全沒有作用(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:86-88`、 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931B.cs:88-90`)。真正擋下存檔的是呼叫端 `if ((!this.DoValidate()) || this.ValidateErrList.Show())` (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:161`)裡的 `ValidateErrList.Show()`。 **所以功能沒壞,但 `DoValidate` 的回傳值是假的**——任何人照字面理解「回 true 代表通過」都會判斷錯。

**`GetExcelData` 的字串串接**:兩支都有一個匯出 Excel 的方法,查詢條件用 `strSQL += " AND " + Row.Name + " = " + "'" + Row.Value + "'"` 直接串 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:228`、`:237`)。 `Row.Name` 與 `Row.Value` 都來自畫面,**欄位名與值兩邊都沒有參數化**。同一支檔的其他三個方法全部用 `AddInParameter`,只有這一支例外。

**卡控總表(兩支共用)**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進修改頁 | 對方畫面的覆核狀態 | 對應訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:55-60` |
| 進修改頁 | 當季獎金已鎖定 | 「當季計算已完成鎖定(OFDB921),不可修改。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:63-68` |
| `DoValidate` | grid 0 列 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:72` |
| `DoValidate` | grid 有列但 View 0 列 | 「明細資料 輸入有誤」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:76` |
| `DoValidate` | 調整金額不為 0 但沒填原因 | 「請輸入HR調整原因」/「請輸入單位主管調整原因」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:80-81` |
| `DoValidate` | 員工姓名等於「未到職」卻有調整金額 | 「未到職員工不可調整金額」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:83-84` |
| 按修改 | 獎金合計大於個人獎金 | 「…獎金合計大於個人獎金,確定儲存?」 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:171-172` |
| 按修改 | 獎金合計小於 0 | 「…獎金合計小於0,確定儲存?」 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:174-175` |
| 新增 | 一律不給新增(`ButtonAddEnable = false`) | — | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:97` |

**「未到職」是寫死的中文字串比對**(`EMP_NAME='未到職'`),不是代碼——員工姓名剛好叫這三個字就會被誤判。而且這個判斷是在 `DataTable.Select()` 的 filter 字串裡,不在資料庫。列入附錄 E。

#### 4.1.4 `OFDM721` / `OFDM725` — 只是剛好用同一張 `OFD721`

四層相似度 0.089 到 0.287,**沒有任何複製貼上的痕跡**。兩支的關係是「同一張表的兩種用途」:

|  | `OFDM721` | `OFDM725` |
|---|---|---|
| 用途(推測) | 受益憑證**重列**(重印一張新的實體憑證) | 受益憑證**領取**(受益人來拿紙本) |
| 依據 | UI 標籤「流水號作廢原因」+ 寫 `REPRT_CODE='Y'`(實體憑證重印碼)+ 寫 `TASK_ID` 到 `OFD724` | UI 標籤「領取方式」「代領人」+ 寫 `CER_TAKE_*` 四欄 |
| 動的表 | `OFD724`(INSERT + UPDATE)、`OFD722`(INSERT)、`OFD721`(UPDATE 兩次)、`COD017`(UPDATE) | `OFD721`(UPDATE) |
| `OFD721` 改哪些欄 | `REPRT_CODE`、`BF_CTL_SRNO` | `CER_TAKE_UID` / `CER_TAKE_DTTM` / `CER_TAKE_TYPE` / `CER_TAKE_MAN` |
| 改 `CER_STATUS` | **不改** | **不改** |
| PO 行數 | 744 | 481 |
| Ctl 行數 | **811**(全片最大) | 261 |

兩支唯一的交集是「都會鎖 `OFD721` 的同一列」,而且**沒有任何一方帶樂觀鎖條件**: `OFDM721` 的三個 `UPDATE OFD721` 只用三個主鍵當條件(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:410-413`、`:439-442`), `OFDM725` 的領取 UPDATE 多帶一個 `AND CER_TAKE_UID = ''`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:82`), 取消領取帶 `AND CER_TAKE_UID <> ''`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:106`)。 **只有 `OFDM725` 做了「狀態沒被別人改過」的防護,`OFDM721` 完全沒有。**

兩支的完整卡控與缺陷寫在 §4.3(憑證線一起看比較清楚)。

### 4.2 `SAL9xx` 契約線 — `OFDM450` / `OFDM454` / `OFDM456` / `OFDM458`

#### 4.2.1 `SAL9xx` 到底是什麼

`dsm.md §8` 查 `SAL050` / `SAL051` 時得到的結論是「全庫沒有 `ATLAS.SAL` 專案、沒有 SAL 開頭的畫面代號」。本片重驗一次,結論相同(附錄 D.3),並補上業務意義:

**`SAL9xx` 是銷售機構(通路)的三種收費契約,與 `SAL050` / `SAL051` 完全無關。**

推測依據四條:

| 依據 | 內容 | 出處 |
|---|---|---|
| 主鍵與關聯鍵 | 三張主檔都以 `SNO`(契約序號)當鍵,明細全部用 `SNO` 掛回去;機構用 `AGENT_ID` 加 `AGENT_CODE` 兩段表示 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:137`(`SAL908A.AGENT_ID |
| 取號函式 | Common 的序號產生器有兩支專屬方法 `GetSAL908ANo()` 與 `GetSAL920ANo()`,種類字串就是表名 | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:704-716` |
| 控件中文標籤 | `OFDM450` 是「通路銷售服務費報表」「服務費計算方式」「給付頻率」;`OFDM454` 是「手續費分成費率」「單筆申購」「定額申購」「轉申購」「扣款費(新台幣)」;`OFDM456` 是「手續費(新台幣)」 | 三支 Designer,`grep -n` 取 `.Text` |
| 共用下拉 | `SAL915A` 被包成全庫的「基金群組資料」下拉,類別名就寫「基金群組資料 - SAL915A」 | `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/FundGrpcdForSAL915ADataSrc.cs:15` |

對照 `SAL050` / `SAL051`(`dsm.md §8`):主鍵是 `SAL_DEPT_NO` 加 `EMP_NO`、欄位是「業務部門代碼」「部門主管獎金計算類別」, **兩組表沒有共同欄位、沒有任何一支程式同時碰兩組**。全庫 grep `SAL9` 得 24 個表名, 落在 12 個檔案內(清單見 §8.2),與 DSM 零交集。 **所以「SAL」這三個字母在 ATLAS 裡至少代表兩件不同的事:業務組織(DSM 用)與銷售機構契約(OFD 用)。**

#### 4.2.2 20 張表的家族結構

| 契約 | 主檔 | 計算基金 | 計算群組 | 費率 | 計算戶號 | 排除戶號 | 其他 |
|---|---|---|---|---|---|---|---|
| 通路銷售服務費(`OFDM450`) | `SAL908A` | `SAL909A` | `SAL910A` | `SAL911A` | `SAL912A` | `SAL913A` | `SAL914A` |
| 手續費分成(`OFDM454`) | `SAL920A` | `SAL921A` | `SAL922A` | — | `SAL923A` | `SAL924A` | `SAL930A` |
| 手續費(`OFDM456`) | `SAL925A` | `SAL926A` | `SAL927A` | — | `SAL928A` | `SAL929A` | `SAL930A` |
| 契約用基金群組(`OFDM458`) | `SAL915A` | — | — | — | — | — | — |
| 批次產出(`OFDB459`,不在本片) | `SAL931A` | — | — | — | — | — | `SAL932A` |

欄位對應是從三支 UI 的 grid 名稱與錯誤訊息反推的 (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:876-888`、 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM454.cs:664-673`、 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM456.cs:644-653`),訊息文字「計算基金 / 計算群組 / 費率設定 / 計算戶號 / 排除戶號 必須輸入」與 grid 變數名一一對上。

**`SAL930A` 同時掛在 `OFDM454` 與 `OFDM456` 兩支的明細** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:54`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:54`)。兩支用同一個 `SNO` 序號池嗎?**不是**:`SAL920A` 用 `GetSAL920ANo()`、`SAL925A` 沒有專屬取號方法 (`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:704-716` 只有 908A 與 920A 兩支)。 **假設**`SAL925A` 的 `SNO` 也走 `GetSAL920ANo()`(共用序號池),依據是兩支畫面共用 `SAL930A`; 但 repo 內找不到 `OFDM456` 的取號呼叫,**這一條要現場確認,不要當事實用**。

#### 4.2.3 三胞胎:`OFDM450` / `OFDM454` / `OFDM456`

這三支比 §4.1 任何一組都更像複製貼上:

| 層 | `450` vs `454` | `450` vs `456` | `454` vs `456` |
|---|---|---|---|
| UI | 0.649 | 0.676 | **0.915** |
| Ctl | 0.879 | 0.879 | **1.000** |
| PO | 0.843 | 0.872 | **0.954** |

`OFDM454` 與 `OFDM456` 的 Ctl **代號代換後完全相同**(352 行對 352 行,相似度 1.000)。三支的 PO 介面也是同一組五個方法: `IsExistSameDate` / `IsExistSameData` / `IsExistSameBFData` / `IsExistSameAgent` / `GetSALxxxA` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:30-34`)。

**三胞胎之間「只改了一支」的地方,兩處,都在 `OFDM450`:**

| # | 差異 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | **`OFDM450` 的 `IsExistSameData` 少做一半檢核。**`OFDM454` / `OFDM456` 在這支方法裡做四段查詢(計算戶號、排除戶號、計算基金、計算群組);`OFDM450` 的「計算戶號」那一段**整段被 `/* … */` 註解**,只剩「計算基金」一段。方法名與失敗訊息仍寫「計算戶號、計算基金」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:542-561` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:581-640`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:536-594` | **高**。同一銷售機構的同一個戶號可以被掛進兩份服務費契約而不被擋 |
| 2 | **`OFDM450` 的 `IsExistSameAgent` 多兩段客戶特定分支**(2021 年的機構法人 `'09001'`、2023 年的行銷 `'08001'` / `'08201'`),`OFDM454` / `OFDM456` 沒有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:729-739` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:793-798`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:749-754` | 中。同一條業務規則(哪些機構的客戶可以跨機構掛)在服務費契約上放寬了,在手續費契約上沒有 |

#### 4.2.4 三支共有的四個缺陷

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **戶號 / 基金清單用字串串進 `IN ()`**。程式把 grid 裡的值用逗號接成一串,直接塞進 `IN (" + str + ")` | 值來自畫面,**沒有參數化**;而且明細 0 筆時串出來是 `IN ()`,SQL 直接語法錯誤 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:569`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:638`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:727`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:581`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:536` | **高** |
| 2 | **`IsExistSameData` / `IsExistSameBFData` / `IsExistSameAgent` 三支都沒有 `finally { conn.Close(); }`**。同一支檔裡的 `IsExistSameDate` 有 | 每次存檔前的檢核就漏一條連線;`IsExistSameData` 更誇張——`conn.Open()` 那行剛好在被註解掉的區塊裡(`OFDM450`),連線**建了但沒開也沒關** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:537`、`:628`、`:718` 對照有 finally 的 `:464-499` | **高** |
| 3 | **`BMS001A.TRUST_AGENT_CODE <> :AGENT_CODE`** 判斷「戶號的開戶機構跟契約機構不同」 | Oracle 三值邏輯:`TRUST_AGENT_CODE` 為 NULL 的戶號結果是 UNKNOWN,**不會被算進去,也就不會示警**。`CAS` / `CLS` / `DSM` / `BBS` / `TMK` 五個模組都中過同一條 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:726`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:793`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:749` | **高** |
| 4 | **`catch` 裡 `AddResultRow(false, 0, "檢查…失敗")` 之後仍 `return modelVDB`**,而正常路徑是 `AddResultRow(IsExit, 0, "")` | 呼叫端拿 `ReturnCode` 當「有沒有重複」用:例外時回 `false`,與「沒有重複」同一個值。**資料庫出錯會被當成檢核通過** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:584-591`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:659`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:614` | **高** |

#### 4.2.5 `OFDM450` 卡控總表(`OFDM454` / `OFDM456` 同構,差異見 §4.2.3)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| grid 離格 | 計算戶號重複 | 「戶號重覆」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:353` |
| grid 離格 | 基金群組空白 | 「基金群組不可為空白」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:524` |
| grid 離格 | 基金群組重複 / 基金重複 | 「基金群組重覆」/「基金重覆」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:534`、`:632` |
| grid 離格(排除戶號) | 舊的重複檢核 | — | **整段被註解**,改走 `CommonGridHelper.AutoCheckDetailGridCellDuplicatePKeyReturnMsg`;被註解的那段還留著一個指到**錯誤 grid**(`ugrdSAL912A`,應為 `ugrdSAL913A`)的訊息 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:431-446` |
| `DoValidate` | 五個明細 grid 各自 0 筆 | 「計算基金 / 計算群組 / 費率設定 / 計算戶號 / 排除戶號 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:876-888` |
| `DoValidate` | 起始日期大於終止日期 | 「起始日期必須小於等於終止日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:893` |
| `DoValidate` | 明細基金的計算起訖超出契約起訖 | 「<基金>計算起始日期不可早於起始日期」/「…終止日期不可晚於終止日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:900`、`:906` |
| 查詢頁 | 起始日期起訖只填一個 | 「起始日期(起)(迄) 必須皆(不)填寫」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:1144` |
| `BeforeAdd` / `BeforeUpdate` | 同機構同日期已有契約 | 由 `IsExistSameDate` 回報 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:47-48`、`:464-507` |
| `BeforeAdd` / `BeforeUpdate` | 同機構的計算基金已在別張契約 | 由 `IsExistSameData` 回報 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:563-580` |
| `BeforeAdd` / `BeforeUpdate` | 同機構的計算戶號已在別張契約 | — | **被註解,不生效**(僅 `OFDM450`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:542-561` |
| `BeforeAdd` / `BeforeUpdate` | 計算戶號 / 排除戶號的開戶機構與契約機構不同 | 由 `IsExistSameAgent` 回報 | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:689-763` |
| 取報表代碼 | 查不到報表代碼設定 | 「查無Rebate 需求報表代碼設定[COD006A]」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:439` |

### 4.3 實體受益憑證線 — `OFDM721` `OFDM722` `OFDM723` `OFDM724` `OFDM725`

這五支是本片唯一有明確先後關係的一組,也是唯一與別的模組(BBS)共用狀態機的一組。

#### 4.3.1 五支的位置與一張憑證的一生

| 順序 | 畫面 | 動作(推測) | 改哪些表 | 改 `CER_STATUS` |
|---|---|---|---|---|
| 0 | (不在本片) | 交易產生憑證資料,`CER_STATUS` 進 `'2'` 尚未簽證 | `OFD721` `OFD724` | 寫 `'2'` |
| 1 | `OFDM722` | 配紙張流水號 | `OFD724.BF_CTL_SRNO`、`OFD721.BF_CTL_SRNO`、`COD017.CTL_SRNO_ID='1'` | 不改(只當查詢條件 `= 2`) |
| 2 | `OFDM723` | 發行簽證 / 註銷簽證 / 兩者的修改 | `OFD724.VISA_*`、`OFD721.CER_STATUS` | **`'2'`↔`'1'`** |
| 3 | `OFDM724` | 送件 / 取消送件 / 領回 / 取消領回 | `OFD724.VISA_UID_D` 等四欄、`OFD721` 同四欄 | 不改 |
| 4 | `OFDM725` | 受益人領取 / 取消領取 / 列印簽收單 | `OFD721.CER_TAKE_*` 四欄 | 不改(只當查詢條件 `= '1'`) |
| 旁路 | `OFDM721` | 重列(原憑證作廢重印一張) | `OFD724` INSERT + UPDATE、`OFD722` INSERT、`OFD721.REPRT_CODE` / `BF_CTL_SRNO`、`COD017.CANCEL_CD` | 不改 |

**步驟 0 在 repo 內找不到。**全庫沒有任何程式寫 `CER_STATUS = '2'` 之外的初始值, `OFDM723` 的「簽證修改」是唯一把它寫回 `'2'` 的地方。 **假設**:憑證列是由交易 / 發行批次建立時就帶 `'2'` 進來,依據是 `OFDM722` 的查詢條件假設它已經存在且為 `2` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:112`)。要確認得看 OFD 其他片的發行批次。

#### 4.3.2 `OFDM721` 受益憑證重列

**它是本片風險最集中的一支**:744 行 PO 全部手寫 SQL Server SQL、自動覆核、三處字串串接、一條三值邏輯過濾。

**`Execute()` 的五個步驟**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:145-516`):

| 步 | 動作 | 錨點 | 備註 |
|---|---|---|---|
| 1 | 取 `OFD724` 下一個 `DATA_SEQ`(`SELECT TOP(1) … ORDER BY DATA_SEQ DESC` 然後加 1) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:520-566` | **算出來的值被註解掉不用**(`:248`),實際靠 DB 自動增長 |
| 2 | `INSERT INTO [OFD724]` 一筆新的待列印簽證,`VISA_ID='A'`、`REPRT_CODE='Y'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:169-281` | 四眼 13 欄**全部寫同一個人、`Status` 寫死 `'301'` |
| 3 | `UPDATE [OFD724] SET VISA_ID='X'` 把原來那筆作廢 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:290-313` | 條件帶 `DATA_SEQ` 與 `VISA_ID='A'` |
| 4 | `INSERT INTO [OFD722]` 寫一筆重列記錄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:326-396` | 同樣 `Status='301'` |
| 5 | `UPDATE [OFD721] SET REPRT_CODE='Y'`;若原本有紙張流水號再 `UPDATE [OFD721] SET BF_CTL_SRNO=0` 與 `UPDATE [COD017] SET CANCEL_CD=…, CTL_SRNO_ID='2'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:404-484` | `CTL_SRNO_ID='2'` 是「作廢」 |

**七個缺陷,逐條:**

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **自動覆核**。INSERT 時 `EntryID` / `VerifyID` / `ApproveID` 全部綁同一個 `strUserID`、日期全部 `DateTime.Now`、`Status` 寫死 `'301'` | 這兩筆資料(`OFD724` 與 `OFD722`)**從來沒有經過四眼**,卻在表上長得像已覆核。稽核軌跡失真 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:271-279`、`:386-394` | **高** |
| 2 | **`UpdateID` 用字串串接**。四處 `,UpdateID='" + strUserID + "'`,而 `strUserID` 來自 `Utility.Parameters` | 使用者代號含單引號就注入;而且同一支檔其他 40 個參數都有參數化,只有這四處沒有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:294`、`:408`、`:437`、`:462` | **高** |
| 3 | **`AND OFD724.[PRT_UID] <> ''` 三值邏輯**。查詢與檢核兩支 SQL 都用它「過濾已列印的資料」 | `PRT_UID` 為 NULL 的列一律看不到。而同一支檔的 INSERT 把 `@PRT_UID` 綁成 `string.Empty`(`:253`)——**在 Oracle 上空字串就是 NULL,自己寫進去的資料自己查不到**;在 SQL Server 上空字串不是 NULL,所以 `<> ''` 會把剛寫入的那筆也濾掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:91`、`:700` | **高** |
| 4 | **只用最後一個 `i` 決定 commit 還是 rollback**。五個步驟共用同一個 `int i`,每次 `ExecuteNonQuery` 覆寫,最後 `if (i > 0) tran.Commit(); else tran.Rollback();` | 前面四步任何一步影響 0 列都不會被發現,只要最後一步成功就整批 commit。而「最後一步」還取決於 `BF_CTL_SRNO != 0` 這個 if | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:487-500` | **高** |
| 5 | **`con.Open()` 與 `BeginTransaction()` 在 `try` 外面**,`catch` 裡卻無條件 `tran.Rollback()` | 連線開不起來時丟的是 `NullReferenceException`,真正的資料庫錯誤被蓋掉。與 `architecture.md §3` 記的 `BasicEVAPO.Add` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:152-154` 對照 `:504` | **高** |
| 6 | **`GetOFD724DataSeq` / `GetOFD722DataSeq` 的 `finally` 無條件 `con.Close()`**,而 `con` 在 `try` 內賦值 | 同上,連線建立失敗時 `NullReferenceException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:560-564`、`:610-614` | 中 |
| 7 | **算好的 `DATA_SEQ` 被註解掉不用,但取號的兩支方法仍然每次都跑**(各開一條連線、各查一次 `TOP(1)`) | 兩趟無用的資料庫往返;而且 `iOFD724DATA_SEQ` / `iOFD722DATA_SEQ` 兩個變數宣告後只被賦值不被讀 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:160-162`、`:248`、`:318-320`、`:376` | 中 |

**`OFDM721` 卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 輸入憑證號碼 | 查不到(或已列印發行簽證單) | 「此受益憑證已列印發行簽證單,不可重新列印」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM721.cs:96`、`:140` |
| 選流水號作廢原因 | 代碼不是 `06`(人工註銷) | 「此流水號作廢原因不可使用,請選擇代碼為06/人工註銷為流水號作廢原因」 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM721.cs:158` |
| 按執行 | 未輸入流水號作廢原因 | 「流水號作廢原因必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM721.cs:234` |
| 按執行 | 有紙張流水號 | 「執行後將會作廢原受益憑證紙張流水號,是否要確認?」 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM721.cs:165` |
| 取數 | `OFD724.VISA_ID = 'A'` 且 `PRT_UID <> ''` | 尚未簽證或未列印的查不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:699-700` |
| 執行 | 最後一個 UPDATE 影響列數大於 0 | 否則整批 rollback,**訊息為空字串** | 阻擋(但無訊息) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:487-500` |

「代碼為 `06`」是寫死在 UI 的字面值〔客戶特定〕,`CTL014` 的流水號作廢原因分類碼在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:991-993`(`CTL_SRNO_ID`「憑證流水號識別碼[060]」)。

#### 4.3.3 `OFDM722` 受益憑證配號

配號 = 把實體空白憑證的紙張流水號(`BF_CTL_SRNO`,來源是 `COD017`,由 `CODM016` 維護)指派給一張憑證。

**三段 UPDATE,各自一個 `foreach`,全部檢查勾選**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:201-315`):

| 段 | 更新 | 條件 | 失敗訊息 |
|---|---|---|---|
| 1 | `OFD724.BF_CTL_SRNO` | 三主鍵 + `VISA_ID='A'` | (空字串) |
| 2 | `OFD721.BF_CTL_SRNO` | 三主鍵 + `BF_CTL_SRNO = '0'` | 「憑證號碼:…已配流水號,請重新配號」 |
| 3 | `COD017.BF_CER_ISSUE_CODE` / `BF_CER_NO` / `CTL_SRNO_ID='1'` | `FUND_ID` + `BF_CTL_SRNO` + `CTL_SRNO_ID='0'` | 「流水號:…已被使用或作廢,請重新配號」 |

第 2 段與第 3 段的 WHERE 帶了「還沒被配過」的條件,是**正確的樂觀鎖**;第 1 段沒有。

**缺陷:**

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | **查詢條件把字串欄拿去跟數字比**:`OFD721.CER_STATUS=2`(沒有引號) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:112` | 中。SQL Server 會把整欄轉數字比,索引失效;若欄內有非數字值直接轉型錯誤 |
| 2 | **`TASK_ID` 查詢條件用字串串接**:`strSQL += "AND " + Row1.Name + "=" + Row1.Value;`,欄名與值都沒參數化、值也沒加引號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:131` | **高** |
| 3 | 同一支 `UpdateID = '" + strUserID + "'` 三處字串串接 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:210`、`:250`、`:291` | **高** |
| 4 | `PRT_UID<>''` 與 `PRT_DTTM<>'1900/01/01'` 兩條三值邏輯過濾 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:114`、`:116` | **高** |
| 5 | **`f_GetEVAStatus('A')` 這支 table-valued function 在 repo 內不存在**(`DB/Function/` 沒有它) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:122` | 中。而且它是 SQL Server 的 TVF 語法,Oracle 不支援 |
| 6 | 三段迴圈各自對 `i <= 0` 判斷後 rollback,但三段共用同一個 `i`;第三段成功後 `AddResultRow(true, i, "")` 回報的是最後一列的影響數而不是總數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:317-319` | 低 |

**`OFDM722` 卡控總表(UI 側,共 12 條)**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 自動配號 | 本基金空白流水號用盡 | 「本基金紙張流水號已用盡,但仍有憑證尚待配號,請執行空白憑證流水號輸入作業(CODM016),新增紙張流水號資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:273`、`:374`、`:389` |
| 自動 / 向下配號 | 一列都沒選 | 「至少須選取一筆資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:287`、`:412`、`:500` |
| 向下配號 | 「此筆資料之後的選取資料將會重新配號,是否確認?」 | — | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:238`、`:313` |
| 存檔前 | 流水號欄空白 | 「紙張流水號欄位不可為空白」/「紙張流水號的值不可為空白!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:307`、`:454` |
| 存檔前 | grid 內流水號重複 | 「紙張流水號有重複,請檢查」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:489`、`:514` |
| 輸入流水號 | 該流水號已被使用 | 「請選擇未使用過的流水號,請再重新輸入」/「此流水號已被使用,請重新輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:468`、`:564` |
| 輸入流水號 | 「請重新輸入不重覆且未使用過的流水號」 | — | **被註解,不生效** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:531` |
| 勾選 | 「此筆資料必須勾選」 | — | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM722.cs:404` |

`CODM016` 這支畫面被寫進錯誤訊息裡當作操作指引,但它不在本片(在 COD 模組,見 `cod.md`)。

#### 4.3.4 `OFDM723` / `OFDM724` 的細節

見 §4.1.2。這裡只補一條 `OFDM723` 特有的:

**它是本片唯一一支同時開兩個交易的畫面。** `SerialNo VisaNo = new SerialNo(tranUpdate1, dbPTPF)` 在平台庫開一個交易取簽證序號 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:55-59`),業務更新在 `dbProduct` 另一個交易 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:130`)。這與 `architecture.md §3` 描述的 `TranData` / `TranToDo` 雙交易結構一致,但**用途不同**: 架構篇那組是「業務庫 + 待辦事項」,這裡是「業務庫 + 序號」。兩個交易的 commit 順序、其中一邊失敗怎麼補償,程式裡沒有處理—— **取到號但業務更新失敗,號就跳掉了**。這是簽證序號會出現斷號的原因。

#### 4.3.5 `OFDM725` 受益憑證領取

**三種執行功能**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:63-137`):

| 值 | 功能 | 動作 |
|---|---|---|
| `1` | 領取 | 逐列(勾選者)`UPDATE OFD721 SET CER_TAKE_UID / CER_TAKE_DTTM / CER_TAKE_TYPE / CER_TAKE_MAN`,條件帶 `AND CER_TAKE_UID = ''` |
| `2` | 取消領取 | 逐列(勾選者)把同四欄清空,條件帶 `AND CER_TAKE_UID <> ''` |
| 其他 | 列印簽收單 | **直接回 `AddResultRow(false, 0, "列印請按列印鈕")` 並 return**,不做任何事 |

列印走另一條路:`GetReportData` 呼叫 SP `s_OFDM725_Get`,對每一列各叫一次 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:187-216`)。

**六個缺陷:**

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **整支 `Execute()` 的 SQL 全部字串串接,含使用者輸入的「代領人」姓名** | `CER_TAKE_MAN` 是自由文字欄,單引號直接破壞 SQL;`FUND_ID` / `BF_CER_ISSUE_CODE` 同樣 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:72-82`、`:100-116` | **高** |
| 2 | **取數 SQL 也串**:`CER_TAKE_TYPE` 與 `CER_TAKE_MAN` 用 `GetParamValue(model, …, true)` 包成 `N'值'` 直接進 SELECT 清單 | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:276-277`、`:633` | **高** |
| 3 | **`if (ExecType == "3")` 被註解,但它管的那一行沒被註解** | `AND OFD721.CER_SOURCE <> '5'`(排除總額憑證)**現在對所有執行功能都生效**,不再只有第 3 種。而且它本身是三值邏輯,`CER_SOURCE` 為 NULL 的憑證一律看不到 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:302-303` | **高** |
| 4 | **`AND OFD721.VISA_RTN_DTTM <> '1900/1/1'`**(只收已領回的) | 三值邏輯;而且日期字面值寫成 `'1900/1/1'`(無補零),與同片其他地方的 `'1900/01/01'` 不一致 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:285` | 中 |
| 5 | **`catch { tranUpdate.Rollback(); throw ex; }`** | `throw ex` 重設堆疊,原始出錯位置消失;外層 catch 再 `AddResultRow(false, 0, "")` 給空訊息 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:146-148` | 中 |
| 6 | **「受益憑證已有贖回中單位數,不可取消領回」的整支檢核方法 `CheckCER_RUNIT` 被 `//` 逐行註解** | 外殼 80 行還在(`:399-478`),介面上看得到方法名。實際保護只剩取消領取時的 `CER_RUNIT = 0` 過濾(`:299`),**而那是過濾不是阻擋——有贖回中單位數的憑證直接從清單消失,使用者不會知道為什麼** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:399-478`、`:457` | **高** |

**`OFDM725` 卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| `DoValidate` | 執行功能未選 | 「執行功能 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:97` |
| `DoValidate` | 領取 / 取消領取時受益人 ID 與戶號都沒填 | 「執行功能為[領取]時,受益人ID 或 戶號須擇一輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:103`、`:114` |
| `DoValidate` | 領取 / 列印簽收單時未選領取方式 | 「…領取方式 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:107`、`:121` |
| `DoValidate` | 領取方式為代領 / 承銷代領卻沒填代領人 | — | **被註解,不生效**(改由 grid 逐列檢核,見下) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:131` |
| `DoValidate` | 一列都沒勾 | 「至少須註記一筆資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:141` |
| `DoValidate` | 勾選列未填領取方式 / 代領人 | 「憑證領取方式 為必填欄位」/「代領人 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM725.cs:146`、`:148` |
| 取數 | `CER_STATUS = '1'`(只有正常憑證) | 掛失中 / 質設中 / 尚未簽證的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:284` |
| 取數 | `VISA_RTN_DTTM <> '1900/1/1'`(必須已領回) | 還沒從簽證機構領回的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:285` |
| 取數 | `CER_SOURCE <> '5'`(排除總額憑證) | 總額憑證永遠看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:303` |
| 取數(取消領取) | `CER_RUNIT = 0` | 有贖回中單位數的看不到 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:299` |
| 執行 | `UPDATE OFD721` 影響列數不等於 1 | 「更新境內受益憑證檔(OFD721)失敗」+ rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:89`、`:123` |

**四條「過濾(無提示)」疊在一起**,是這支畫面最常見的客訴來源: 使用者輸入戶號查不到憑證,可能是狀態不對、可能是還沒領回、可能是總額憑證、也可能是有贖回中單位數, 畫面一律只回「查無資料」。

### 4.4 卡控最複雜的四支

#### 4.4.1 `OFDM374` 受益人歸屬業務員〔共用表〕

**1,829 行的 PO,其中 1,222 行(第 604 到 1824 行)是一整塊 `/* */` 註解。** 註解掉的是舊世代自己手寫的 `AddBF_NOData` / `UpdateBF_NOData` / `DeleteBF_NOData` / `VerifyBF_NOData` / `ApproveBF_NOData` / `UnDeleteBF_NOData` / `RejectBF_NOData` / `ResendBF_NOData` 整套 EVA 流程, 包含一個完整的第二份建構子(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:609`)。 **活的只有前 600 行**,改成掛事件交給引擎。 `architecture.md` 附錄 E 的 E28(「全 repo 大量保留被註解掉的程式碼」)在本片的極端值就是這一支: **66.8% 的行數是死的**。

**活的部分做三件事:**

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `AfterAdd` | 呼叫 `UpdateEmpNoForBfNo(args, false)` → `UPDATE BMS001 SET EMP_NO, BELONG_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:259-264` |
| `AfterUpdate` | 業務員有換才 `InsertChangeData`(寫 `OFD375` 異動檔),然後一律 `UpdateEmpNoForBfNo` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:235-250` |
| `AfterApproveDelete` | `InsertChangeData` + `UpdateEmpNoForBfNo(args, true)`(把 `BMS001.EMP_NO` 清空) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:251-258` |

**這裡有一件與 `architecture.md §3` 直接相關的事:資料在「輸入」當下就生效,不等覆核。** `AfterAdd` 在 `architecture.md §3` 的定義是「新增**送審**成功之後」,不是「覆核成功之後」。所以使用者按下新增、送出待覆核的那一刻,`BMS001.EMP_NO`(受益人的歸屬業務員)就已經被改掉了。 **只有刪除那一路等到 `AfterApproveDelete` 才動。** 這與 `bbs.md §4` 記的 BBS 行為、`architecture.md §3` 的警告完全一致——**本片是第三個實例,而且是不對稱的** (新增 / 修改立即生效、刪除要覆核)。

**全域開關 `CTL015.AUTO_BELONG_EMP`**:三個事件都先問 `IsAutoBelEmp()` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:543-555`,`SELECT COUNT(0) FROM CTL015 WHERE AUTO_BELONG_EMP = 'Y'`)。這個旗標若為 `'N'`,**`OFD374` 照樣寫、`BMS001` 完全不動**——兩張表就此分岔,而且沒有任何提示。應該補進 §0.5 的全域開關表。

**其他缺陷:**

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `INSERT INTO [TA].[dbo].[OFD375]` **三段式名稱,資料庫名 `TA` 寫死在 SQL 裡**(註解區內三處);活的那一處寫 `[OFD375]`、另一處寫 `[dbo].[OFD375]` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:458` 對照 `:411`、`:930`、`:1501`、`:1711` | 中〔客戶特定〕 |
| 2 | `InsertChangeData` 把 `@Status` 綁成 `EVAStatusCode.ApproveAdd`,`Entry`/`Verify`/`Approve` 三組 ID 同一人 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:513-523` | 中。異動檔天生已覆核 |
| 3 | `@BF_NO` 綁 `SqlDbType.NVarChar`,而 `BF_NO` 在 xsd 是 `decimal` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:504` | 中 |
| 4 | `IsAutoBelEmp()` **每次事件都查一次資料庫**,沒有快取,而且它自己不開連線(靠 `ExecuteScalar` 隱式開) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:543-555` | 低 |
| 5 | `OFDM374_PO_BeforeDelete` 是空方法但仍然註冊 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:219-221` | 低 |
| 6 | `SELECT * FROM [OFD374] Where ((UpdateID <> 'xxx') OR (RejectID <> ''))` —— 兩條三值邏輯疊在一個 OR 裡,結尾還多一個分號 `;;` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:1238`(註解區) | 低(死碼) |

#### 4.4.2 `OFDM375` 業務員戶號整批移轉

它是 `OFDM374` 的整批版:選一個轉出業務員、選一個轉入業務員、勾一批戶號,一次搬。

| 面向 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BasicEVAPO`,**覆寫 `Select()`** 而不是掛 `BeforeSelect` 事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:22`、`:38` |
| 四眼 | **完全不走**。主檔 `OFD375A` 只當畫面暫存,真正的寫入在 `Execute()` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:158` |
| 寫哪些表 | `UPDATE OFD374`(改歸屬)、`UPDATE [dbo].[OFD375]`(關掉舊區間)、`INSERT INTO [dbo].[OFD375]`(開新區間)、`UPDATE BMS001`(同步歸屬) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:226`、`:237`、`:251`、`:374` |
| 錯誤處理 | `catch` 裡 `AddResultRow(false, 0, string.Format("執行失敗。原因:{0}", ex.Message))` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:413` |

**兩個重點缺陷:**

1. **`ex.Message` 直接當成給使用者的訊息**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:413`,`OFDM377_PO.cs:363` 同樣)。 Oracle / SQL Server 的原始錯誤訊息會含表名、欄名甚至 SQL 片段。`cas.md` 與 `cod.md` 都記過同型。

2. **`OFDM375` 走不走四眼與 `OFDM374` 不一致。**同一張 `OFD374`,單筆維護(`OFDM374`)要送審, 整批移轉(`OFDM375`)**直接落地**。想繞過覆核,用整批畫面搬一筆就行。錨點:`OFDM374` 的 PO 掛 `AfterVerify` 系列事件並由引擎推狀態(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:36-45`); `OFDM375` 的 PO 一個事件都沒掛,只有一支 `Execute()`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:158`)。 **同一組 `OFDM376` / `OFDM377`(通路歸屬)完全同構,同樣的不一致。**

#### 4.4.3 `OFDM907` 實質受益人歸屬風險

法遵用的畫面:標記每個戶號的實質受益人歸屬風險等級,支援 Excel 批次匯入。

| 方法 | 做什麼 | 錨點 |
|---|---|---|
| `CheckExists` | 查 `OFD907` 是否已有同戶號同日期 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:110-134` |
| `CheckBFExists` | 查 `BMS001A` 戶號存不存在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:136-173` |
| `CheckEffective` | 查該戶號在該日期是否已有生效中的設定 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:176-200` |
| `BatchAdd` | 逐列 INSERT,`STATUS` 寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:201-257` |

**五個缺陷:**

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **三支檢核都用 `string.Join("OR", …)` 把每一列組成一段 WHERE**。DataTable 為空時串出來是 `SELECT * FROM OFD907 WHERE `,**直接語法錯誤** | 匯入空檔案或全部被前一關濾掉時,使用者看到的是 `catch` 的「執行失敗,請檢查」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:118-121`、`:145-148`、`:184-187` | **高** |
| 2 | **`CheckBFExists` 用 `COUNT(0)` 對比 grid 列數**。grid 有重複戶號時 `COUNT` 只算一次 | 匯入檔有重複戶號 → 誤報「受益人戶號不存在」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:150-160` | **高** |
| 3 | **`CheckExists` / `CheckEffective` 成功時不寫 Result**,只有 `catch` 會寫 | 呼叫端拿不到「檢核通過」的訊號,只能靠 `DataEntity` 有沒有列判斷;而這兩支還會先 `Clear()` 掉輸入資料 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:122`、`:188` | 中 |
| 4 | **`BatchAdd` 寫死 `STATUS='301'`**,Entry / Verify / Approve 三組欄位全綁同一個 `row.CreateID` | 批次匯入的資料**天生已覆核**,不進待辦事項 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:212-215` | **高** |
| 5 | **查詢的日期區間用字串串接**,而且 `UPD_DATE_ST` 存在時直接讀 `UPD_DATE_END` 不檢查 null | 只填起日不填迄日 → `NullReferenceException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:102-103` | 中 |

**`OFDM907` 卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 匯入 | 戶號不存在於 `BMS001A` | 「受益人戶號不存在」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:159` |
| 匯入 | 同戶號同日期已存在 | 由 `CheckExists` 回傳的資料列數判斷 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:110-134` |
| 匯入 | 該日期已有生效中設定 | 由 `CheckEffective` 回傳的資料列數判斷 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:176-200` |
| 匯入執行 | 任一列 INSERT 影響 0 列 | 「匯入失敗,請檢查資料是否正確」+ rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:238-243` |
| UI | 例外 | `MessageBox.Show(ex.Message)` 已被註解;改走 Dialog | 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM907.cs:233` |

#### 4.4.4 `OFDM913A` 業務員異動確認

`OFDB913` 批次把待確認的業務員異動寫進 `OFD913A_UPD`,`OFDM913A` 做人工確認,確認後寫 `CONFIRM_ID` / `CONFIRMDATE`。

**這支是本片檢核最多的一支:六道業務檢核 + 四眼 + 批次匯入。**

| 檢核 | 內容 | 訊息 | 錨點 |
|---|---|---|---|
| `CheckExists` | 同戶號同上傳日期已存在 | (無訊息,靠回傳列數) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:290-330` |
| `CheckBFExists` | 戶號在 `BMS001A` 且 `NVL(FREEZE_CD,'N') <> 'Y'` | 「戶號{0}-{1}未完成開戶或已註銷無法匯入」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:332-376` |
| `CheckEffective` | 同戶號同日期、或同戶號同業務員已存在 | (無訊息) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:379-406` |
| `CheckConfirmBfno` | 戶號是否已有歸屬的業務員 | 見 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:415-465` | 同左 |
| `CheckEMPRel` | 戶號是否為在職員工或員工眷屬(`COD009` 在職 + `COD010` 眷屬) | 「戶號{0}-{1}是員工或員工員眷」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:471-520` |
| `CheckOFD114S` | 戶號是否在交易控管期間(`OFD114A` 停權、`OFD115A` 控管) | 「戶號{0}-{1}屬交易控管之客戶」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:529-577` |

**`AfterApprove` 的兩段 SQL**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:99-140`):

1. 若狀態不是以 `3` 結尾(非刪除),先 `DELETE OFD913A_UPD WHERE BF_NO = :BF_NO AND nvl(CONFIRM_ID,' ') <> ' '` ——把這個戶號**過去所有已確認的紀錄整批刪掉**。

2. 再 `UPDATE OFD913A_UPD SET CONFIRM_ID = :CONFIRMID, CONFIRMDATE = TO_CHAR(SYSDATE,'yyyymmdd') WHERE BF_NO = :BF_NO AND to_char(UPD_DATE,'yyyyMMdd') = to_char(:UPD_DATE,'yyyyMMdd')`。

**六個缺陷:**

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **第一段是「只保留一筆」的硬刪除**,而且刪的是整個戶號的歷史 | 這張表沒有歷史,只有「最後一次確認」。要追「這個客戶去年換過幾次業務員」查不到 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:109` | **高**(設計面,不是 bug) |
| 2 | **`strSQL.ToUpper()`** 把整段 SQL 轉大寫再送出 | 現在只有 `' '` 與日期格式字串,轉大寫剛好無害;**任何人日後在這兩段 SQL 裡加一個含小寫的字串字面值就會壞掉** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:110`、`:127` | 中(未爆彈) |
| 3 | **`if (j == -1)` 判斷 DELETE 失敗**。`ExecuteNonQuery` 刪 0 列回 0,不是 -1 | 這道檢查**永遠不成立**,等於沒有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:114-118`、`:614` | 中 |
| 4 | **`CheckEffective` 把 `emp_no` 拿去跟未加引號的值比**:`string.Format("… AND emp_no={2}", …, r.EMP_NO)` | `EMP_NO` 是字串欄;Oracle 會做隱式轉型,值含非數字就 `ORA-01722` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:391` | **高** |
| 5 | **五支檢核全部用 `string.Format` 把 `BF_NO` 串進 SQL,且在 `foreach` 內逐列查一次** | 200 列就是 200 次往返;而且全部沒有參數化 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:343`、`:482-488`、`:540-545` | **高** |
| 6 | **`BatchAdd` 寫死 `'301'` 並直接填 `CONFIRM_ID`**,程式註解自己寫明「此批次匯入不需要再經過覆核即完成上傳」 | 批次匯入完全繞過四眼與上面六道檢核中的一部分 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:596-601` | **高**(但是刻意的) |

**`OFD913A_UPD` 的三個 `STATUS`**:表上同時有 `Status`(框架四眼狀態,無 Caption)、 `STATUS`(Caption「資料狀態」)、`STATUSDESC`(Caption 也是「資料狀態」)。 `AfterApprove` 讀的是 `model.DataEntity.OFD913A_UPD[0].Status`(框架那個), 判斷式是 `!strStatus.EndsWith("3")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:105`)。 **三個名字差一個字母大小寫的欄位放在同一張表,是本片最容易改錯的欄位組。**

### 4.5 其餘畫面依業務線分組

以下 37 支用表格帶過。**每一支都讀過 UI 的 `DoValidate()` 與 PO 的全部方法**, 但只列「主要卡控一句話」與「特別之處」;要細節照錨點去看。

#### 4.5.1 A 線 業務 / 通路歸屬(`OFDM376` `OFDM377`)

`OFDM376` / `OFDM377` 與 §4.4.1 / §4.4.2 的 `OFDM374` / `OFDM375` **是同一套程式改代號**: 單筆維護走四眼、整批移轉不走四眼、整批那支把 `ex.Message` 當訊息。差別只在對象從「受益人戶號」換成「通路代碼」。

| 畫面 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|
| `OFDM376` | 新增時查「此通路歸屬業務員已存在」;修改 / 刪除時查「已異動」(樂觀鎖) | PO 1,416 行,與 `OFDM374` 一樣有大段註解區;活的部分**不寫 `BMS001`**(通路沒有對應的受益人主檔) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM376_PO.cs:254`、`:421` |
| `OFDM377` | 轉入業務員不可與轉出相同;查無資料時回「查無資料」 | 不走四眼,直接 `UPDATE OFD376`;`catch` 回 `ex.Message` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM377.cs:130`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM377_PO.cs:363` |

`OFDM376_PO.cs:820` 與 `OFDM374_PO.cs:1238` 是同一行複製出來的死碼: `SELECT * FROM [OFDxxx] Where ((UpdateID <> '" + LoginUser + "') OR (RejectID <> '' ))"; ;` ——**兩個分號、兩條三值邏輯、使用者代號字串串接**,三個問題在同一行。同型的還有 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM711_PO.cs:514`、 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM712_PO.cs:750`、 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM713_PO.cs:712` ——**五支畫面同一行,是複製貼上的家族**。

#### 4.5.2 B 線 業務組織與 KPI 獎金(7 支)

七支全部被同一個開關鎖住(§0.5),而且**鎖定訊息一字不差地複製了七份**。

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM369` | `OFD369A` | 年度 / 月份必填;當季已鎖定不可**匯入** | 唯一一支訊息說「不可匯入」(其餘六支說「不可修改」);`BatchAdd` 的 INSERT 把 `STATUS` 寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM369_PO.cs:204`、`:231` |
| `OFDM371` | `OFD371` + `OFD372` + `OFD373` | 部門主管 / 區域主管不可同時是明細的業務人員;員工已隸屬其他層級部門不可新增;下屬部門還在不可刪除 | **本片唯一有階層(大 / 中 / 小部門)概念的畫面**;三條「已隸屬…不可新增」是伺服端檢核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM371_PO.cs:626-634`、`:688`、`:700` |
| `OFDM391` | `OFD391A` | 淨收入起不可大於迄、兩者都要大於 0;當季鎖定 | 多筆型(`BaseMultiRowEVADaoPO`),PO 只有 134 行 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM391.cs:62-66` |
| `OFDM392` | `OFD392A` + `OFD393A` + `OFD394A` | 獎金提撥比率加總必須為 100;季 / 年兩組 KPI 的佔百分比各自加總必須為 100;KPI 參數名稱必填 | 本片唯一「兩個明細 grid 各自檢查加總 100」的畫面 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM392.cs:127`、`:166`、`:184` |
| `OFDM395` | `OFD395A` | 分配人數必須大於 0;職務名稱必填;分配獎金比率加總必須為 100 | 同上型式 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM395.cs:75`、`:92` |
| `OFDM399` | `OFD399A` | 毛銷售的本季 KPI 實際達成數必須大於 0;**質化目標必須為 0** | 唯一呼叫 SP 的 B 線畫面(`S_TA_OFDM399_Get`);「質化目標」以中文字串比對判斷 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM399.cs:74-76`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM399_PO.cs:216` |
| `OFDM931A` / `OFDM931B` | `OFD931A` | 見 §4.1.3 | — | — |

**`OFDM371` 的兩個回傳約定衝突**:同一支 PO 裡 `AddResultRow(false, 0, "此員工已隸屬大部門不可新增")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM371_PO.cs:626`)是 `false` 代表擋, `AddResultRow(true, 0, "中部門資料尚未建立")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM371_PO.cs:760`)卻是 `true` 帶訊息。 **同一支檔兩種約定**,與 §4.1.3 的 `OFDM931A` 是同一類問題。

#### 4.5.3 C 線 拜訪與據點主檔(3 支)

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM382` | `OFD381` | 預計 / 實際拜訪日期有填則拜訪方式必填;兩個日期須擇一輸入 | PO 674 行,**`AddResultRow` 六處全部被註解**,等於所有結果訊息都不會出現 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM382.cs:112-124`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM382_PO.cs:264`、`:360`、`:497`、`:511`、`:589`、`:665` |
| `OFDM383` | `OFD020` | EMAIL 格式 | 金融機構分行主檔;`OFD020` 也被 `OFDM562` 的查詢用到(`OFD020V` view) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM383.cs:141` |
| `OFDM385` | `OFD071` | 統一編號格式(三處)、EMAIL-A / EMAIL-B 格式 | 券商主檔;`OFD071` 也是 `OFDM376` 的通路來源 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM385.cs:130-158` |

`OFDM382` 那六處被註解的 `AddResultRow` 值得單獨記:**PO 有完整的新增 / 修改 / 刪除流程,但所有成功與失敗訊息都被拿掉**, 畫面上看到的只有框架的預設訊息。「新增失敗,請檢查」這幾個字還留在註解裡誤導讀者。

#### 4.5.4 D 線 群組與服務費率(6 支,`OFDM431` / `OFDM431bb` 已在 §4.1.1)

六支結構高度一致:一個主檔 + 一個明細 grid、多筆型 PO、Oracle 方言、 `ROW_NUMBER() OVER (PARTITION BY 群組代碼)` 取每群第一筆當查詢結果。

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM430` | `OFD429A` | 戶號不能為 `-1`;明細必填;「已存在群組,不得重複設定!」 | PO 類別名是 **`OFDM430AOracleDao`**(與 `OFDM431` 同樣不照命名鐵律) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM430_PO.cs:27`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM430.cs:154`、`:219` |
| `OFDM432` | `OFD432A` | 經理費率須介於 0 到 100;「銷售機構代碼＋基金群組代碼」不可重複;未選銷售機構區別碼不可選代碼 | 費率上限檢核有兩套:grid 離格用 `MessageBox.Show("服務費率不得大於100!!")`(**全片唯一還在用 `MessageBox` 的地方**),存檔前用 `ValidateErrList` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM432.cs:265`、`:332`、`:349` |
| `OFDM433` | `OFD436A` | 明細必填;基金代碼不可空白;「基金群組代碼」不可重複 | 與 `OFDM431` 幾乎同構,但表不同(`OFD436A`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM433.cs:187-203` |
| `OFDM434` | `OFD437A` | 經理費率 0 到 100;「受益人群組代碼＋基金群組代碼＋契約生效日期＋契約終止日期」不可重複**或日期區間重疊** | 唯一做「日期區間重疊」檢核的畫面;SQL 用 `DECODE(EXPIRE_DATE, ' ', '99991231', EXPIRE_DATE)` 把空白視為無限遠 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM434.cs:338`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM434_PO.cs:217` |
| `OFDM435` | `OFD435A` | 明細必填;「銷售機構代碼」不可重複 | 畫面上有一行寫死的說明「(除外設定作業僅適用於:月平均餘額-成本法)」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM435.cs:130-140` |
| `OFDM436` | `OFD440A` | 明細必填;明細「銷售機構代碼」必填;「受益人代碼」不可重複 | 同上型式 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM436.cs:124-141` |

**`OFDM432` 與 `OFDM434` 的 `DECODE(EXPIRE_DATE, ' ', '99991231', EXPIRE_DATE)`** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM432_PO.cs:212`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM434_PO.cs:217`) 把「一個空白」當成「沒有終止日」。**`DECODE` 用 `=` 比對,NULL 比不到**—— `EXPIRE_DATE` 若是 NULL(不是一個空白),`DECODE` 回傳 NULL,整條 `BETWEEN` 變 UNKNOWN,契約就被漏掉。同型缺陷。錨點同上。

#### 4.5.5 F 線 清算與合併(3 支)

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM481A` | `OFD494A` | 發放日期必須大於清算基準日及系統日 | 唯一的卡控就這一條;`OFD495A` 被 join 進來唯讀 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM481A.cs:277` |
| `OFDM482A` | `OFD496A` | 基金代碼必填;期別 / 實際付款日期 / 受益人 ID / 戶號須擇一輸入 | 52 欄的主檔,全片第二大;PO 有一支回傳日期當訊息的方法(`AddResultRow(true, 1, dt.ToString("yyyy/MM/dd"))`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM482A.cs:39`、`:53`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM482A_PO.cs:231` |
| `OFDM485` | `OFD484A` | **UI 裡一條卡控都沒有**(90 行,全片最小的 UI) | 基金合併;PO 掛 `AfterUpdate` 直接 `UPDATE OFD484A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM485.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM485_PO.cs` |

`OFDM482A_PO.cs:231` 那一行把日期字串塞進 `ReturnMessage` 當資料值回傳,呼叫端再 parse 回日期。 **訊息欄位被當成資料通道**,與 `cas.md` / `cod.md` 記的「`catch` 回傳 `ex.Message` 當資料值」是同一類設計問題, 差別在這裡是成功路徑。

#### 4.5.6 G 線 匯率(`OFDM531`)

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD531`,多筆型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM531_PO.cs:49` |
| 卡控 | 買入 / 賣出 / 中價匯率都必須大於 0;日期必填;上傳檔格式不正確擋下 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM531.cs:151`、`:159`、`:167`、`:210`、`:258`、`:271` |
| 特別之處 | **支援「臺銀 CSV 格式整批上傳」**,是本片三支有檔案匯入的畫面之一(另兩支是 `OFDM907` 與 `OFDM913A`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM531.cs:297` |
| 缺陷 | 上傳成功訊息寫成「已上傳{0:#,##0}筆**指派客戶**資料」——**文案是從別的畫面複製來的**,這裡上傳的是匯率不是客戶 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM531_PO.cs:207` |

#### 4.5.7 H 線 受益人大會(3 支)

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM540` | `OFD540A`(86 欄,**全片最大**) | 「不可變更專案狀態為 {0}」 | 三個案由 × 五種投票狀況 × 測試 / 正式 = 欄位爆炸的原因;PO 掛 `BeforeAdd` / `BeforeUpdate` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM540.cs:245` |
| `OFDM541` | `OFD541A` | 一般客戶只可選一個投票狀況;投票單位數不吻合擋下;專案代碼必填 | 掛 `AfterUpdate` 回寫 `OFD540A`(把明細票數彙總回專案) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM541.cs:98-105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM541_PO.cs` |
| `OFDM543` | `OFD542A` | 專案代碼必填;可達成目標比率不得為 0 | 最小的一支(PO 157 行 / UI 129 行) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM543.cs:72`、`:119` |

`OFD541A` 的主檔宣告出現在兩支畫面:`OFDM541` 與 `OFDM542`(後者不在本片)。改它要兩邊看。

#### 4.5.8 I 線 扣款帳號核印(7 支)

這一線是「主檔 + 一堆對照表」的結構,`OFDM711` / `OFDM712` / `OFDM713` 三支是純對照表維護,程式高度雷同。

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM562` | `OFD562`〔共用〕 | 受益人 ID / 戶號 / 扣款行 / 扣款帳號 / 核印進度 / 核印完成日 須擇一填寫 | **唯一一張掛了資料庫 trigger 的表**(`OFD562_T01` / `OFD562_T02`,見 §8.3);78 欄 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM562.cs:248` |
| `OFDM700` | `OFD700` | 參數識別碼 / 參數值必填、識別碼不可重複、明細必填 | 取數 SQL 有一段 `AND (SourceType ='238' AND (:SEAL_TYPE<>'1' OR TextValue LIKE 'DDCT%')` 的三值邏輯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM700_PO.cs:71`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM700.cs:47-58` |
| `OFDM710` | `OFD710A` | 至少需勾選一筆資料 | Designer 抓不到任何中文標籤(全片唯一);UI 378 行、Ctl 430 行 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM710.cs:241` |
| `OFDM711` | `OFD711` | 「核印不成功原因代碼…已存在 / 已異動」 | PO 907 行、**零事件掛點**,自己寫了整套 Add / Update / Delete / EVA | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM711_PO.cs:132`、`:296` |
| `OFDM712` | `OFD712` | 「扣款行核印媒體對應代碼…已存在 / 已異動」 | PO 1,182 行;與 `OFDM711` / `OFDM713` 三支結構逐段對應 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM712_PO.cs:282`、`:450` |
| `OFDM713` | `OFD713` | 「此扣款方式+扣款行對應代碼…已存在 / 已異動」 | PO 1,138 行;四處同一句訊息,其中一處的空白位置不同(`{0} +{1} + {2}`),證明是手改 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM713_PO.cs:272`、`:1079` |
| `OFDM714` | `OFD702` | 批次識別碼 / 扣款行 / 扣款帳號 / 扣款人 ID / 核印方式 / 回覆日期 須擇一填寫 | 27 欄全部有中文名(§2.3),是本片文件最完整的一張表 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM714.cs:103` |

**`OFDM711` / `OFDM712` / `OFDM713` 是本片第二組「三胞胎」**:三支都是 900 到 1,200 行的舊世代 PO、都自己實作整套 EVA(`AddData` / `UpdateData` / `DeleteData` / `VerifyData` / `ApproveData` …)、都有那行 `SELECT * FROM [OFDxxx] Where ((UpdateID <> '…') OR (RejectID <> ''))"; ;`。改其中一支的 EVA 邏輯,另外兩支不會跟著變。

#### 4.5.9 K 線 結匯銀行(`OFDM731`)

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主明細 | `OFD731` + `OFD732` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:27-29` |
| 卡控 | EMAIL 格式有誤;匯入時「匯入的銀行 […] 已有存在資料庫」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM731.cs:133`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:625` |
| **三條被註解的必填檢核** | 結匯銀行代碼、結匯銀行中文名稱、「明細資料至少要輸入一筆」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM731.cs:115`、`:120`、`:126` |
| 缺陷 | `catch` 回 `"執行失敗,請檢查" + 換行 + string.Format("訊息:{0}", ex.Message)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:518` |
| 缺陷 | 匯入流程會 `DELETE` 重複資料;`DELETE OFD731` 與 `DELETE OFD732` 各一次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:717` |

**三條必填檢核全被註解掉**,所以現在可以存一筆沒有銀行代碼、沒有名稱、沒有明細的結匯銀行。這是本片「被註解掉但外殼還在」密度最高的一支 UI。

#### 4.5.10 L 線 KYC 問卷(4 支)

| 畫面 | 主明細 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM694B` | `OFD694A` | **一條卡控都沒有** | 投資人風險屬性對照表;PO 113 行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM694B_PO.cs` |
| `OFDM741` | `OFD741` + `OFD742` | 【適用於自然人】與【適用於法人】至少勾一項;明細必填 | 兩個**詢問型**訊息用 `AddResultRow(false, …)` 送出:「此題目仍存在於有效的問卷版本中…請確認是否仍要修改?」與「題目已被問卷版本所使用,不可刪除」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs:283`、`:336` |
| `OFDM742` | `OFD743` + `OFD744` + `OFD745` | 【境內】/【OMNIBUS】/【境外】至少勾一項;終止日不可小於生效日;問題出題順序必填;答案選項順序不得重複;銷售機構區別碼 / 代碼必填 | 改受益人類別或銷售機構會**自動清空明細**(三處提示);「此問卷版本已被使用,不可修改」**被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM742.cs:47-76`、`:267`、`:518-540` |
| `OFDM743` | `OFD746` + `OFD747` | 分數上限不可小於下限;分數上下限不可重疊(兩處);明細必填 | 主檔 DataTable 名叫 `OFD743`,與 `OFDM742` 的實體主檔同名(§2.1 的交叉錯位) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM743.cs:281-308` |

**KYC 這條線有三代表結構並存**(`OFD741`/`OFD742`、`OFD743`/`OFD744`/`OFD745`、`OFD746`/`OFD747`), 而且 `OFDM742` 會 join `OFD741` `OFD742` `OFD743` `OFD744` `OFD745` `OFD746` 六張 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs`)。**三代之間有引用關係,不是純粹的舊版殘留。**

`OFDM742` 那條被註解的「此問卷版本已被使用,不可修改」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM742.cs:267`) 與 PO 側仍然生效的「此問卷版本已被使用,不可刪除」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:364`) 形成一個不對稱:**已被使用的問卷版本不能刪,但可以改**。

#### 4.5.11 M 線 集保(`OFDM751`)

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD751` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM751_PO.cs:44` |
| 卡控 | 「戶號已存在 請檢查」、「集保機構統編已存在 請檢查」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM751.cs:217`、`:226` |
| 特別之處 | 兩條唯一性檢核都在 UI 端做,伺服端沒有第二道 | 同上 |

#### 4.5.12 N 線 申報(`OFDM871` `OFDM872`)

| 畫面 | 主檔 | 主要卡控 | 特別之處 | 錨點 |
|---|---|---|---|---|
| `OFDM871` | `OFD871` | 申報年月起迄必填、起不可大於迄;「{年月} {基金}已有此受益人資料,是否繼續執行?」 | 那句詢問用 `AddResultRow(false, …)` 送(**詢問型訊息走失敗通道**);表也是 `OFDB871` 的主檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM871_PO.cs:299`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM871.cs:118-127` |
| `OFDM872` | `OFD872` | 申報年月起迄必填、起不可大於迄 | 20 欄的金額矩陣(國內 / 國外 / OSU / OBU × 原幣 / 台幣);UI 991 行(全片第三大) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM872.cs:111-120` |

### 4.6 兩支需要單獨交代的

#### 4.6.1 `OFDM458` — 與 `OFDM431` / `OFDM433` 第三次同構

`OFDM458` 的主檔是 `SAL915A`(契約用基金群組),UI 的三條卡控 (「明細資料必須輸入」「基金代碼 不可為空白」「'基金代碼'必須輸入」) 與 `OFDM431bb` 的前三條**一字不差**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM458.cs:185`、`:192`、`:260` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:178`、`:184`、`:272`), 唯獨**少了「基金已存在於其他基金群組中」那一條**。也就是「基金群組」這個概念在本片有三張表(`OFD431A` / `OFD436A` / `SAL915A`)、四支維護畫面 (`OFDM431` / `OFDM431bb` / `OFDM433` / `OFDM458`),**四支的重複檢核各不相同**。

#### 4.6.2 `OFDM913` — 不在本片、但一定會撞到的孤兒

任務書說 `architecture.md` 附錄 D.4 把 `OFDM913` 列在「6 支有 Entity 沒 Ctl 的孤兒畫面」裡。 **查證結果:不是這樣,兩件事都要更正。**

| 說法 | 實際 | 證據 |
|---|---|---|
| 「`OFDM913` 在附錄 D.4 的 6 支真孤兒名單裡」 | **不在**。D.4 的 6 支是 `NFDR808` · `OFDB282` · `OFDM084B` · `OFDM152` · `OFDM381` · `OFDR461` | `architecture.md` 附錄 D.4 的表格 |
| 「有 Entity 沒 Ctl」 | **完全相反**:`OFDM913` **有** FormProxy / Control / PO,**沒有** UI / DataEntity / UIEntity | `atlas_scan.py --screen OFDM913` |

`OFDM913` 真正的位置是 `architecture.md §2` 那張「65 支六層不齊」的組合分布表裡 **`ui + model + view` 那一列的唯一一支**。

更關鍵的是第三件事,兩邊都沒記到:

**`OFDM913_PO.cs` / `OFDM913_Ctl.cs` / `OFDM913_Pxy.cs` 三個檔都沒有被任何 csproj 收進去。** `grep -c "OFDM913_PO.cs" Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj` 得 `0`, Control 與 FormProxy 兩個 csproj 同樣是 `0`;對照 `OFDM913A_PO.cs` 在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj:320` 有 `<Compile Include>`。 **所以這三個檔在磁碟上、在版控裡、但不參與編譯。** 它們的內容看起來是完整可用的(`OFDM913_PO : BaseEVADaoPO, IOFDM913_PO`,主檔 `OFD907`, 四個檢核方法 `CheckExists` / `CheckBFExists` / `CheckEffective` / `BatchAdd`, `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913_PO.cs:21-43`), 與 `OFDM907_PO` 幾乎同構——**假設**它是 `OFDM907` 開發過程的分身,依據是兩者主檔同為 `OFD907`、介面方法完全相同。

**這件事對掃描器的影響**:`atlas_scan.py` 以 `_Ctl.cs` 存在與否建畫面清單, 所以 `OFDM913` 被算進 908 支;但它既不編譯也沒有入口。 **908 這個數字裡至少有 1 支是完全不存在的畫面。**列入附錄 D。

#### 4.6.3 `OFDM913A` 與 `OFDM913` 的關係:沒有關係

|  | `OFDM913` | `OFDM913A` |
|---|---|---|
| 主檔 | `OFD907` | `OFD913A_UPD` |
| 六層 | 缺 UI / DataEntity / UIEntity | 齊全 |
| 有沒有編譯 | **沒有** | 有 |
| 業務 | 實質受益人歸屬風險(與 `OFDM907` 同) | 業務員異動確認 |
| 上游 | 無 | `OFDB913` 批次 |

**兩者唯一的共同點是代號長得像。**命名上的巧合:`OFDM913A` 的 `A` 不是 `OFDM913` 的變體後綴, 而是照 `OFD913A_UPD` 這張表命名的(表名帶 `A`)。另外還有一張**不同的**表也叫 `OFD913A`(3 欄:`EMP_NO` / `AGENT_CODE` / `EMP_NAME`), 只存在於 `Dev/ATLAS.OFDI/Source/Entity/DataEntity.OFDI/OFDI011Model.xsd` 的查詢結果集裡。 **`OFD913A` 與 `OFD913A_UPD` 不是同一張表的兩個版本,是兩個不相干的東西。**

## 5. 查詢畫面(I)

**本片無 I 畫面。**原因寫在 §3.2:OFD 的 87 支 I 畫面全部在 `Dev/ATLAS.OFDI/` 與 `Dev/ATLAS.OFD.Query/` 兩個專案,它們的 Entity 也在各自專案裡, 不屬於 `DataEntity.OFD9` 這一片。

與本片最相關的是 `OFDI011`(受益人綜合查詢),它 join `OFD721` 讀憑證狀態並做中文轉換 (`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1756`), 取數條件是 `(RTRIM(NVL(OFD721.CER_STATUS,'')) = '1' OR OFD721.CER_STATUS IN ('4','7'))` (`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1932-1933`)。 **這組條件與 `OFDM725` 的 `CER_STATUS = '1'` 不一致**——查詢畫面看得到掛失撤銷(`'4'`)與質設解除(`'7'`)的憑證, 領取畫面看不到。是不是刻意的,程式裡看不出來(§8.1)。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有 WindowsService。**OFD 的 165 支 B 畫面在 `Dev/ATLAS.OFDB/` 與 `Dev/ATLAS.EC/`; 全庫四支 WindowsService 都是 `OFDB6xx` 系列(`architecture.md §8`),與本片無關。

本片被四支批次影響(§1.4),逐條列出讓讀者知道去哪裡找:

| 批次 | 對本片的作用 | 證據 |
|---|---|---|
| `OFDB921` | 算完當季獎金後寫鎖定旗標,鎖住 B 線七支 | 七支 PO 的訊息都直接寫「(OFDB921)」;例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:155` |
| `OFDB913` | 產生 `OFD913A_UPD` 的待確認資料 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB3/OFDB913Model.xsd` 與 `OFDM913A` 共用 `OFD913A_UPD` |
| `OFDB431` / `OFDB433` | 與 `OFDM432` / `OFDM434` 共用 `OFD432A` / `OFD437A`,各自也宣告成主檔 | `atlas_scan.py --table OFD432A` |
| `OFDB459` | 產生 `SAL931A` / `SAL932A`,是 `SAL9xx` 家族唯一的批次 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB459_PO.cs` |
| `OFDB327` | 也宣告 `OFD724` 當主檔 | `atlas_scan.py --table OFD724` |

**本片有三支 M 畫面在做批次該做的事**:`OFDM907` 與 `OFDM913A` 的 `BatchAdd`(Excel 整批匯入,寫死已覆核狀態)、 `OFDM531` 的臺銀 CSV 上傳、`OFDM369` 的 `BatchAdd`。 `architecture.md §6` 說「B 比 I 多的只有寫入這條路徑」,本片顯示**M 也可以走批次寫入,而且繞過四眼**。

## 7. 報表(R)

**本片無 R 畫面。**依 `architecture.md §6` 的命名鐵律,R 一律在 `ATLAS.<模組>.Report`, 本片對應 `Dev/ATLAS.OFD.Report/`,不在 `DataEntity.OFD9` 範圍內。

但有三支 M 畫面自己產出報表或檔案,列在這裡:

| 畫面 | 產出 | 怎麼做 | 錨點 |
|---|---|---|---|
| `OFDM725` | 憑證領取簽收單 | PO 的 `GetReportData` 呼叫 SP `s_OFDM725_Get`,**對每一列各叫一次**,並用 `nVDB.DataEntity.OFDM725_Get.Rows.Count != j` 檢查每次都只回一列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:187-216` |
| `OFDM931A` / `OFDM931B` | 獎金調整 Excel | PO 的 `GetExcelData` 自組 SQL 撈 `OFD931A` join `CTL014` 兩次(季別 `SOURCETYPE='705'`、職務別 `'701'`),UI 側寫檔到「轉出路徑」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:198-247` |
| `OFDM723` | 簽證清單 | PO 的 `GetReportData` 呼叫 SP `S_TA_OFDM723_GET` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:222` |

三支 SP(`s_OFDM725_Get`、`S_TA_OFDM723_GET`、`S_TA_OFDM399_Get`)**都不在 `DB/SP/` 裡**—— `DB/SP/` 有 83 支,沒有一支對應本片(附錄 B)。 `OFDM725` 的那支連命名慣例都不同(小寫 `s_` 開頭、沒有 `_TA_` 段), **假設**它是更早期留下的,依據是同一支 PO 是舊世代 `BasicEVAPO` + SQL Server 方言。

## 8. 跨模組共用

```text
[圖] OFD9 的跨模組面：OFD721 給 BBS、SAL9xx 的三個 Common 共用件、OFD562 的兩支 trigger，以及其他被借走的表
圖中文字:A：OFD721 是本片輻射最廣的表，主要使用者卻在 BBS / OFDM721 OFDM725 / 本片的主檔持有者 / OFD721 / 境內受益憑證檔 / BBS 十支 M 畫面 / 全部帶來源狀態條件 / CODM017 OFDB001 OFDI011 / 唯讀 / B：SAL9xx 沒有 SAL 模組，但三個 Common 共用件會碰 / OFDM450 454 456 458 / 唯一的維護入口 / 20 張 SAL9xx / SNO + AGENT_ID / SerialNo 兩支取號 / 種類字串寫死表名 / BasicBMS_PO 三個過濾器 / 影響全庫受益人查詢 / SAL915A 只收 STATUS LIKE 3% / 沒覆核的群組全庫下拉都看不到 / C：OFD562 是本片唯一掛 trigger 的表 / OFDM562 / 扣款帳號 78 欄 / OFD562_T01 / 寫 TRPM101T1 / OFD562_T02 / 同步 OFD662 / 每次 EVA 都觸發 T02 / 驗證覆核各重寫一次 / D：本片其他被借走的表 / OFD374 / BMS RSP DSM 都用 / OFD724 / OFDM271 OFDB327 / OFD432A OFD437A / OFDB431 OFDB433 / OFD871 OFD872 / OFDB871 一支吃兩張 / E：本片沒有 I / B / R，它們在別的專案 / ATLAS.OFDI / I 查詢 / ATLAS.OFD.Query / I 查詢 / ATLAS.OFDB / B 批次 / ATLAS.OFD.Report / R 報表
```

*圖:圖 5 跨模組。橘框=本片的維護入口；白框=表本身；灰虛框=別的模組的用法；黑框=版控外或資料庫端；橘虛框=風險。A 組的 OFD721 主檔在本片、主要使用者在 BBS，B 組的 SAL915A 透過共用下拉影響全庫，是本片影響面最大的兩張表。*

### 8.1 `OFD721` 給 BBS — 與 `bbs.md` 逐條對帳

`bbs.md §8` 的原話:「風險在 `OFDM721` / `OFDM725` 那一側:如果 OFD 的維護畫面可以直接改狀態而不走同一套條件, BBS 這邊的所有狀態轉換前提就失效了。repo 內沒有辦法確認 OFD 那兩支怎麼寫——這是跨模組回歸時第一個要問的問題。」

**本節回答這個問題。**

#### 8.1.1 結論:對得上,但不是因為 OFD 側守規矩,而是因為 OFD 側幾乎不碰它

| 問題 | 答案 | 證據 |
|---|---|---|
| `OFDM721` 會不會改 `CER_STATUS`? | **不會**。744 行 PO 全檔 grep `CER_STATUS` 零命中 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs` |
| `OFDM725` 會不會改 `CER_STATUS`? | **不會**。只在查詢條件用 `= '1'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:284` |
| 那 OFD 側誰改? | **只有 `OFDM723`**,兩個分支,各一次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:74-77`、`:89-92` |
| `OFDM723` 有沒有帶來源狀態條件? | **有**。`'2'`→`'1'` 帶 `WHERE CER_STATUS='2'`;`'1'`→`'2'` 帶 `WHERE CER_STATUS='1'` | 同上 |
| 有沒有檢查影響列數? | **有**。`if (j != 1)` 就 rollback 並回「更新境內受益憑證檔(OFD721)失敗」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:168` |

**所以 `bbs.md` 講的「樂觀鎖靠來源狀態條件」這個設計,在 OFD 側被遵守了。** `OFDM721` / `OFDM725` / `OFDM724` 三支改 `OFD721` 的其他欄位時雖然沒有帶狀態條件, 但它們改的是 `REPRT_CODE` / `BF_CTL_SRNO` / `CER_TAKE_*` / `VISA_*`,**與 BBS 的狀態機正交**。

#### 8.1.2 對不上的地方:`bbs.md §2` 的值域推測有三處要更正

`bbs.md` 說「repo 內找不到值域定義檔」。**找得到**: `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372`。差異見 §2.5.1 的表,重點三條:

1. **`'2'` 是「尚未簽証」不是「已印製未交付」。**`bbs.md` 標了「假設」,方向對(都是「還沒正式生效」)但名稱錯。 OFD 側的證據很直接:`OFDM723` 的「簽證」動作就是把 `'2'` 改成 `'1'`。

2. **`'8'` 是「換發註銷」不是「換發中」。**這一條影響理解: `bbs.md` 寫「`BBSM001` 新增換發把狀態寫成 `'8'`」——動作正確,但那是**舊證被註銷**,不是「這張證正在換發」。 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:376-377` 同時寫 `CER_STATUS='8'` 與 `DEL_DATE=:CHG_DATE`, `DEL_DATE`(註銷日)這一欄證實了「註銷」的語意。 **補充一條 `bbs.md` 沒寫、但對得上的**:撤銷換發那一路 (`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:104-112`)把 `'8'` 改回 `'1'` 的同時也清掉 `DEL_DATE`, 而且帶 `AND CER_STATUS='8'` 的來源條件。**所以 `'8'` 雖然叫「註銷」,在程式上是可逆的,而且可逆這條路有把關。** 字典的中文容易讓人誤以為 `'8'` 是終態,**讀 `bbs.md` 時要一起看這條**。

3. **`'9'` 已贖回,`bbs.md` 完全沒列。**BBS 十支畫面沒有任何一支處理它。 OFD 側也沒有任何一支寫它。**假設**它由贖回批次(不在本片、也不在 BBS)寫入, 依據是 `OFD721` 有 `CER_RUNIT`(贖回中單位數)與 `DEL_ID`「實體憑證註銷來源碼[136]」的 `1` 贖回註銷 (`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2465`)。 **這是目前兩篇都沒有覆蓋到的一段流程。**

#### 8.1.3 三處值得追的不一致

| # | 不一致 | 兩邊 | 要問誰 |
|---|---|---|---|
| 1 | 「哪些狀態的憑證看得到」三支畫面三種答案 | `OFDM725` 領取只收 `= '1'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:284`);`OFDI011` 查詢收 `'1'` / `'4'` / `'7'`(`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1932-1933`);`BBSM004` 的撤銷來源收 `'1'` / `'4'` / `'7'`(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:109`) | 業務:質設解除(`'7'`)過的憑證可不可以被領取? |
| 2 | `OFDB001` 用常數類別比、其他全用字面值 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:107` 用 `CER_STATUS.Normal` / `CER_STATUS.ChangeWriteOff` / `CER_STATUS.NotYet` 三個常數;本片與 BBS 全部寫 `'1'` / `'2'` / `'8'` 字面值 | 工程:值域常數已經存在,為什麼沒人用?改值時 `OFDB001` 會跟著變、其他不會 |
| 3 | `CODM017` 判斷 `CER_STATUS != "2"` 決定能不能改空白憑證流水號 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:82`;而本片 `OFDM722` 的配號查詢也只收 `CER_STATUS=2`(無引號) | 業務:`COD017`(空白憑證流水號)與 `OFD721` 的狀態耦合,改一邊要看另一邊 |

#### 8.1.4 `OFD721` 的完整使用者清單

| 模組 | 誰 | 讀 / 寫 | 錨點 |
|---|---|---|---|
| OFD9(本片) | `OFDM721` | 寫 `REPRT_CODE` / `BF_CTL_SRNO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:404-452` |
| OFD9(本片) | `OFDM722` | 寫 `BF_CTL_SRNO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:246-256` |
| OFD9(本片) | `OFDM723` | **寫 `CER_STATUS`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:74`、`:89` |
| OFD9(本片) | `OFDM724` | 寫 `VISA_UID_D` / `VISA_RTN_UID` 等四欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:122` |
| OFD9(本片) | `OFDM725` | 寫 `CER_TAKE_*` 四欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:72-81` |
| OFD(別片) | `OFDM231A` | 讀(`CASE … ELSE T.CER_STATUS END`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:408` |
| BBS | 十支 M 畫面 | 全部是帶來源狀態的 UPDATE | 見 `bbs.md §2` |
| COD | `CODM017` | 讀(join 取 `BF_CER_CHK` 與 `CER_STATUS`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:215` |
| OFDB | `OFDB001` | 讀,用常數類別比 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:103` |
| OFDI | `OFDI011` | 讀,`DECODE` 轉中文 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1756` |

**改 `OFD721` 的欄位,要同時看五個模組。**這張表在本片是主檔,但**主要使用者在 BBS**。

### 8.2 `SAL9xx` 的跨模組面

`SAL9xx` 20 張表的使用者**全部在 OFD**,但有三個 Common 層的共用件會碰:

| 共用件 | 用哪些 `SAL9xx` | 做什麼 | 錨點 |
|---|---|---|---|
| `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs` | `SAL908A` `SAL920A` | 兩支專屬取號方法 `GetSAL908ANo()` / `GetSAL920ANo()`,種類字串直接用表名 | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:704-716` |
| `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs` | `SAL908A`+`SAL912A`、`SAL920A`+`SAL923A`、`SAL925A`+`SAL928A` | 三個「依契約過濾戶號」的查詢條件(`SAL912BF_NOFilter` / `SAL923ABF_NOFilter` / `SAL928ABF_NOFilter`),用 `AGENT_ID |  |
| `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` + `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/FundGrpcdForSAL915ADataSrc.cs` | `SAL915A` | 全庫共用的「基金群組」下拉,只收 `STATUS LIKE '3%'`(已覆核) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2742`、`:2768` |
| `Dev/Common/Source/CustomControl/UI.CustomControl/ucBF_NO.cs` | `SAL912A` | 戶號輸入控件內建的過濾 | 同檔 |

**三個影響面:**

1. **`SerialNo` 的兩支專屬方法是硬編碼的**——新增第四種契約(例如 `SAL935A`)要改 Common 層, 而 Common 層一改就影響全庫(`architecture.md §7`)。

2. **`BasicBMS_PO` 那三個過濾器把「戶號屬於哪張契約」這件事帶進了全庫的受益人查詢**。 `OFDM454` / `OFDM456` 改明細戶號,其他模組的受益人下拉會跟著變。

3. **`SAL915A` 的 `STATUS LIKE '3%'` 是全庫唯一一處用 `LIKE` 判斷四眼狀態的地方**。 `OFDM458` 沒覆核的群組在全庫的下拉都看不到,而 `OFDM450` / `OFDM454` / `OFDM456` 的明細卻是直接 join `SAL915A` 沒有這個條件(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs`)。 **下拉選不到但既有資料仍存在**,是這條線最容易被回報成「資料不見了」的地方。

### 8.3 `OFD562` 的兩支 trigger — 本片唯一的資料庫端邏輯

`OFD562`(扣款帳號)是本片**唯一**掛了 trigger 的表,而且有兩支,都在版控裡:

| Trigger | 觸發 | 做什麼 | 錨點 |
|---|---|---|---|
| `OFD562_T01` | `BEFORE UPDATE OF SEAL_PROCESS, SEAL_CD` | 核印進度或核印碼一變,對該受益人在 `OFD607` 登記的每個系統各寫一筆到 `TRPM101T1`(先刪後插) | `DB/Trigger/OFD562_T01.SQL:1-47` |
| `OFD562_T02` | `BEFORE INSERT OR UPDATE OR DELETE` | 把 `OFD562` 的內容同步到 `OFD662`(先刪後插) | `DB/Trigger/OFD562_T02.SQL:1-65` |

**四個要注意的:**

| # | 事 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | **schema 寫死 `SW.`**(`CREATE OR REPLACE TRIGGER SW.OFD562_T01 … ON SW.OFD562`) | `DB/Trigger/OFD562_T01.SQL:1-2`、`DB/Trigger/OFD562_T02.SQL:1-2` | 中〔客戶特定〕 |
| 2 | **`OFD562_T02` 在 `IF (INSERTING OR UPDATING)` 分支裡用 `:OLD.*` 當 DELETE 條件**。INSERT 時 `:OLD` 全部是 NULL,`OFD662.REMIT_CFM_NO = NULL` 永遠 UNKNOWN | `DB/Trigger/OFD562_T02.SQL:38-53` | 中。INSERT 時那段 DELETE 是空轉,不會出錯但也不做事 |
| 3 | **`OFD562_T01` 的 `SELECT … INTO XBF_SRNO` 用 `NVL(:NEW.BF_NO, :OLD.BF_NO)` 查,寫回去卻一律用 `:OLD.BF_NO`** | `DB/Trigger/OFD562_T01.SQL:16` 對照 `:34`、`:37`、`:42` | 中。改戶號時查的是新戶號、寫的是舊戶號 |
| 4 | **兩支檔都是 `cp950` 編碼**(全 `DB/` 196 支 cp950 / 81 支 UTF-8) | `DB/Trigger/OFD562_T01.SQL` | 低。讀檔工具不指定編碼就是亂碼 |

**`OFD562` 的 UPDATE 從 `OFDM562` 走的是四眼引擎,而引擎每次 EVA 都會改那 13 個欄位**—— `SEAL_PROCESS` / `SEAL_CD` 沒變的話 `OFD562_T01` 不會觸發(它有 `OF` 欄位限定), 但 `OFD562_T02` 是**任何 UPDATE 都觸發**,所以**每一次驗證 / 覆核都會重寫一次 `OFD662`**。

### 8.4 本片的表被誰用(反向)

| 本片的表 | 被誰用 | 影響面 |
|---|---|---|
| `OFD721` | BBS 十支、COD 一支、OFDB 一支、OFDI 一支、OFD 其他片一支 | 見 §8.1 |
| `OFD724` | `OFDM271`、`OFDB327`(都不在本片,都宣告它當主檔) | 改欄位要四支畫面一起看 |
| `OFD374` | `BMSM001`(當明細)、`RSPM004`(直接 INSERT)、`DSMM060`(維護入口)、`OFDI011` | `dsm.md §8` 已寫過 BMS / RSP 那一半;**本片補上:`OFDM374` 才是它的 OFD 側主檔,而 `dsm.md` 說主檔在 `DSMM060`**。兩邊都宣告了主檔,是雙主檔 |
| `OFD562` | `BMSM001`(欄位定義來源)、`OFDB562`(`ATLAS.OTAB`,`architecture.md §2` 的 15 個雙實作代號之一) | 改欄位要三處 |
| `OFD907` | 不編譯的 `OFDM913`(§4.6.2) | 無實際影響,但搜尋會命中 |
| `OFD432A` / `OFD437A` | `OFDB431` / `OFDB433` | M 與 B 各一個主檔宣告 |
| `OFD871` / `OFD872` | `OFDB871`(一支批次同時是兩張表的主檔) | 改欄位要三處 |
| `OFD541A` | `OFDM542`(不在本片) | 雙主檔 |
| `SAL915A` | 全庫的基金群組下拉 | 見 §8.2 |

**`OFD374` 的雙主檔問題值得單獨記:** `dsm.md §8` 的標題是「`OFD374A`:DSM 是主檔,BMS 是條件掛載的明細」, 本片查到的是 `OFD374`(沒有 `A`)由 `OFDM374` 宣告為主檔 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:48`), 而掃描器 `--table OFD374` 回報「主檔於 `OFDM374`」、模組標 `BMS, RSP`。 **`OFD374` 與 `OFD374A` 是兩張不同的表**(前者欄位定義來自 BMS / RSP 的 xsd,後者來自 DSM), `dsm.md` 講的是後者。兩篇沒有衝突,但名字只差一個字母,**查的時候要確認是哪一張**。

### 8.5 共用的 UI 控件與下拉來源

| 控件 / 來源 | 用途 | 本片誰用 |
|---|---|---|
| `GetDropDownDataSrc("<代碼>")` | 依 `CTL014.SOURCETYPE` 取下拉 | 全片;`'705'` 季別與 `'701'` 職務別在 `OFDM931A` / `OFDM931B` |
| `GetDropDown9iDataSrc("504")` | 舊版下拉實作,服務費起算日類型 | `OFDM431`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:50`)。`architecture.md §2` 記過「同一支 UI 兩種下拉實作混用」,本片是跨畫面混用:`OFDM431` 用 9i 版、`OFDM431bb` 不用下拉 |
| `FundIDDataSrc` | 基金代碼查詢器 | `OFDM431` 等 D 線六支 |
| `FundGrpcdForSAL915ADataSrc` | 基金群組下拉(只收已覆核) | E 線四支 |
| `ucBF_NO` 戶號控件 | 戶號輸入 + 依契約過濾 | 多支;控件內部碰 `SAL912A` |
| `CerStatusDataSrc` | 憑證狀態下拉 | 本片**沒有一支用它**;用它的是 `OFDM231Ap2`、`OFDI224`、`frmCerData`(都不在本片) |

最後一列值得記:**本片五支憑證畫面沒有一支用官方的憑證狀態下拉**, 狀態值全部寫成字面值。要換值域,這五支要逐支手改。

## 附錄 A. 資料表總表

### A.1 本片 56 支 M 畫面碰到的 111 張表

「角色」:M=主檔 · D=明細 · R=唯讀 join · W=寫入但非主明細。

| 表 | 角色 | 哪幾支碰 |
|---|---|---|
| `BMS001` | R / **W** | `OFDM374` `OFDM375`(W)· `OFDM562` `OFDM721` `OFDM722` `OFDM724` `OFDM725`(R) |
| `BMS001A` | R | `OFDM430` `OFDM435` `OFDM436` `OFDM450` `OFDM454` `OFDM456` `OFDM482A` `OFDM541` `OFDM751` `OFDM871` `OFDM872` `OFDM907` `OFDM913A` |
| `COD006` | R | `OFDM562` `OFDM713` `OFDM871` |
| `COD006A` | R | `OFDM450` `OFDM454` `OFDM456` `OFDM713` |
| `COD009` | R | `OFDM371` `OFDM374` `OFDM376` `OFDM382` `OFDM383` `OFDM541` `OFDM543` `OFDM913A` |
| `COD010` | R | `OFDM913A` |
| `COD017` | **W** | `OFDM721`(作廢流水號)· `OFDM722`(配號) |
| `CTL014` | R | `OFDM700` `OFDM931A` `OFDM931B` + 全片的下拉 |
| `CTL015` | R | `OFDM374` `OFDM375`(全域開關 `AUTO_BELONG_EMP`) |
| `FSK003` | R | `OFDM531` |
| `LOG_OFD931A` | R | `OFDM931A` `OFDM931B` |
| `OFD002` | R | `OFDM371` `OFDM374` `OFDM913A` |
| `OFD019` / `OFD019A` | R | `OFDM700` `OFDM712` `OFDM713` |
| `OFD020` | **M** | `OFDM383` |
| `OFD020V` | R | `OFDM562` `OFDM714` |
| `OFD028` | R | `OFDM383` `OFDM385` |
| `OFD030` | R | `OFDM562` |
| `OFD068` / `OFD068A` / `OFD068A_V01` | R | `OFDM432` `OFDM435` `OFDM436` `OFDM541` `OFDM741` `OFDM871` `OFDM872` |
| `OFD071` | **M** / R | `OFDM385`(M)· `OFDM376` `OFDM377`(R) |
| `OFD081` / `OFD0811` / `OFD0811A` / `OFD081A` / `OFD081V` | R | 20 支 |
| `OFD114A` / `OFD115A` | R | `OFDM913A`(交易控管檢核) |
| `OFD124` | R | `OFDM742` |
| `OFD306A` | R | `OFDM913A` |
| `OFD361` | R | `OFDM382` |
| `OFD369A` | **M** | `OFDM369` |
| `OFD371` / `OFD372` / `OFD373` | **M** / **D** | `OFDM371` |
| `OFD374` | **M**〔共用〕 | `OFDM374`(M)· `OFDM375`(W) |
| `OFD375` / `OFD375A` | **W** / **M** | `OFDM374` `OFDM375` |
| `OFD376` / `OFD377` | **M** | `OFDM376` `OFDM377` |
| `OFD381` / `OFD382` | **M** / R | `OFDM382` |
| `OFD391A` `OFD392A` `OFD393A` `OFD394A` `OFD395A` `OFD399A` | **M** / **D** | B 線五支 |
| `OFD429A` | **M** | `OFDM430`(M)· `OFDM434`(R) |
| `OFD431A` | **M**(兩支) | `OFDM431` `OFDM431bb`(M)· `OFDM432`(R) |
| `OFD432A` | **M**〔共用 `OFDB431`〕 | `OFDM432` |
| `OFD435A` `OFD436A` `OFD437A` `OFD440A` | **M** | `OFDM435` `OFDM433` `OFDM434` `OFDM436` |
| `OFD484A` `OFD494A` `OFD495A` `OFD496A` | **M** / R | F 線三支 |
| `OFD531` | **M** | `OFDM531` |
| `OFD540A` `OFD541A` `OFD542A` | **M** | H 線三支 |
| `OFD562` | **M**〔共用〕 | `OFDM562` |
| `OFD694A` | **M** | `OFDM694B` |
| `OFD700` `OFD702` `OFD710A` `OFD711` `OFD712` `OFD713` | **M** | I 線六支 |
| `OFD721` | **M**〔共用〕 | `OFDM721` `OFDM725`(M)· `OFDM722` `OFDM723` `OFDM724`(W) |
| `OFD722` | **M** / **W** | `OFDM722`(M)· `OFDM721`(W) |
| `OFD724` | **M**〔共用〕 | `OFDM723` `OFDM724`(M)· `OFDM721` `OFDM722`(W) |
| `OFD731` / `OFD732` | **M** / **D** | `OFDM731` |
| `OFD741`–`OFD747` | **M** / **D** | L 線三支 |
| `OFD751` | **M** | `OFDM751` |
| `OFD871` `OFD872` | **M**〔共用 `OFDB871`〕 | `OFDM871` `OFDM872` |
| `OFD907` | **M**〔共用〕 | `OFDM907` |
| `OFD913A` | R(只是結果集形狀) | `OFDM913A` |
| `OFD913A_UPD` | **M**〔共用 `OFDB913`〕 | `OFDM913A` |
| `OFD922A` | R | `OFDM369` `OFDM391` `OFDM392` `OFDM395` `OFDM399` `OFDM931A` `OFDM931B`(全域鎖定開關) |
| `OFD931A` | **M**(兩支) | `OFDM931A` `OFDM931B` |
| `SAL908A`–`SAL915A` `SAL920A`–`SAL930A` | **M** / **D** | E 線四支 |
| `TRPM101T1` / `OFD607` / `OFD601` / `OFD662` | **W**(由 trigger) | `OFD562` 的兩支 trigger(§8.3) |

### A.2 母體報「欄位 0」的 24 張表

以下這些表掃描器查不到欄位定義,因為它們的 xsd DataTable 用的是**畫面代號**而不是表名(§2.1):

`OFD371` `OFD372` `OFD373` `OFD375A` `OFD376` `OFD377` `OFD381` `OFD020` `OFD071` `OFD391A` `OFD392A` `OFD393A` `OFD394A` `OFD395A` `OFD399A` `OFD436A` `OFD531` `OFD541A` `OFD542A` `OFD694A` `OFD700` `OFD710A` `OFD712` `OFD722` `OFD724` `OFD746` `OFD751` `OFD871` `OFD872` `OFD931A` `SAL908A` `SAL915A` `SAL920A` `SAL925A`

查它們的欄位只能讀 PO 的 SQL 字串,或直接查資料庫。**這是 `architecture.md` 附錄 E 的 E4 在本片的實例。**

### A.3 母體沒列到、但本片實際會動到的表

| 表 | 誰動它 | 怎麼動 |
|---|---|---|
| `COD017` | `OFDM721` `OFDM722` | UPDATE `CANCEL_CD` / `CTL_SRNO_ID`,不是任何畫面宣告的主明細 |
| `BMS001` | `OFDM374` `OFDM375` | UPDATE `EMP_NO` / `BELONG_DATE`,受 `CTL015.AUTO_BELONG_EMP` 控制 |
| `OFD375` | `OFDM374` | INSERT 異動檔,不是宣告的明細 |
| `TRPM101T1` `OFD662` | `OFD562` 的 trigger | 由資料庫端寫,程式看不到 |
| `OFD922A` | 七支 B 線畫面 | 只讀,由 `OFDB921` 寫 |

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的

| 類型 | 物件 | 與本片的關係 | 錨點 |
|---|---|---|---|
| Trigger | `OFD562_T01` | `OFD562` 的 `SEAL_PROCESS` / `SEAL_CD` 一變就寫 `TRPM101T1` | `DB/Trigger/OFD562_T01.SQL:1` |
| Trigger | `OFD562_T02` | `OFD562` 任何異動都同步 `OFD662` | `DB/Trigger/OFD562_T02.SQL:1` |

**就這兩支。**`DB/SP/` 83 支、`DB/Function/` 23 支、`DB/View/` 2 支裡,沒有一個與本片 56 支畫面直接相關。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 物件 | 型態 | 呼叫端 | 備註 |
|---|---|---|---|
| `S_TA_OFDM399_Get` | SP | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM399_PO.cs:216` | 命名照慣例 |
| `S_TA_OFDM723_GET` | SP | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:222` | 命名照慣例 |
| `s_OFDM725_Get` | SP | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:187` | **命名不照慣例**(小寫 `s_`、無 `_TA_`),與該 PO 是舊世代 SQL Server 方言一致 |
| `f_GetEVAStatus` | table-valued function | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:122` | SQL Server 語法 `IN (SELECT EVAStatus FROM [f_GetEVAStatus]('A'))`,Oracle 不支援 |
| `dbo.PADLeft` | scalar function | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:207`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:251` | SQL Server,帶 `dbo.` schema |
| `F_GETAGENT` | function | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM743_PO.cs` | 取銷售機構 |
| `OFD068A_V01` | view | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM432_PO.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM436_PO.cs` | `DB/View/` 只有 `OFD068A_V02`,**`_V01` 不在版控** |
| `OFD020V` / `OFD081V` | view | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM562_PO.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM481A_PO.cs` 等 | 都不在版控 |

**`OFD068A_V01` 值得單記**:`dsm.md §8` 分析過 `OFD068A_V02` 的兩個已知缺陷, 本片用的是 `_V01`,而 `_V01` 在 `DB/View/` 裡不存在。**兩個版本的差異無從比較。**

## 附錄 C. 代碼對照

全部來自 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs`,是 repo 內唯一的值域字典 (`architecture.md §7` 講的那一支)。**注意它們是 `public static string` 不是 `const`,可被任意指派污染** (`architecture.md` 附錄 E 的 E9)。

### C.1 憑證狀態 `CER_STATUS`[131]

| 值 | 常數 | 中文 | 本片誰寫 |
|---|---|---|---|
| `1` | `Normal` | 正常 | `OFDM723` 簽證 |
| `2` | `NotYet` | 尚未簽証 | `OFDM723` 簽證修改 |
| `3` | `Lost` | 掛失中 | BBS |
| `4` | `CancelLost` | 掛失撤銷 | BBS |
| `5` | `LostWriteOff` | 掛失註銷 | BBS |
| `6` | `Mortgage` | 質設中 | BBS |
| `7` | `CancelMortgage` | 質設解除 | BBS |
| `8` | `ChangeWriteOff` | 換發註銷 | BBS |
| `9` | `Redem` | 已贖回 | **查不到誰寫** |

錨點 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372`。

### C.2 憑證線其他五組

| 欄位 | 值 | 錨點 |
|---|---|---|
| `CER_SOURCE` 憑證來源碼[130] | `1` 申購 · `2` 贖回餘額 · `3` 換發 · `4` 掛失補發 · `5` 總額憑證 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2308-2330` |
| `REPRT_CODE` 實體憑證重印碼[132] | `N` 無重印 · `Y` 有重印 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2376-2386` |
| `CER_TAKE_TYPE` 實體憑證領取方式[133] | `1` 親領 · `2` 代領 · `3` 郵寄 · `4` 承銷代領 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2390-2408` |
| `TASK_ID` 實體憑證作業碼[134] | `1` 申購 · `2` 贖回餘額 · `3` 換發 · `4` 掛失補發 · `5` 總額憑證 · `6` 重印 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2412-2438` |
| `VISA_ID` 實體憑證簽證代碼[135] | `A` 發行簽證 · `D` 註銷簽證 · `X` 尚未簽證就被刪除 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2442-2456` |
| `DEL_ID` 實體憑證註銷來源碼[136] | `1` 贖回註銷 · `2` 換發註銷 · `3` 掛失註銷 · `4` 總額憑證註銷 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2460-2478` |
| `CTL_SRNO_ID` 憑證流水號識別碼[060] | `0` 未使用 · `1` 已使用 · `2` 作廢(值來自 `OFDM721` 的行內註解) | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:991-993`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:461` |

### C.3 四眼狀態 `Status` 在本片看到的字面值

| 值 | 意義(反推) | 出現處 |
|---|---|---|
| `201` / `202` | 已輸入 / 已修改,待覆核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:176` |
| `301` / `302` | 已覆核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:175` |
| `301`(寫入) | 直接寫死成已覆核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:279`、`:394`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM369_PO.cs:231`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:215`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:600` |
| 以 `3` 結尾 | 刪除類動作 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:105` |
| `LIKE '3%'` | 已覆核 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2742` |

### C.4 其他在程式裡出現的字面量〔客戶特定〕

| 值 | 意義 | 出現處 |
|---|---|---|
| `'09001'` | 機構法人的開戶銷售機構 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:732` |
| `'08001'` / `'08201'` | 行銷的開戶銷售機構 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:738` |
| `'2'`(`CTL_CODE`) | 當季獎金計算已鎖定 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:144` |
| `'238'` | 印鑑種類的 `SOURCETYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM700_PO.cs:71` |
| `'701'` / `'705'` | 職務別 / 季別的 `SOURCETYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:220` |
| `'504'` | 服務費起算日類型的下拉代碼 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:50` |
| `06` | 流水號作廢原因「人工註銷」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM721.cs:158` |
| `'未到職'` | 員工姓名的中文字串比對 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:83` |
| `'質化目標'` | KPI 名稱的中文字串比對 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM399.cs:76` |
| `SW.` | 資料庫 schema | `DB/Trigger/OFD562_T01.SQL:1` |
| `[TA].[dbo].` | 三段式資料庫名 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:930`(註解區) |
| `'1900/01/01'` / `'1900/1/1'` | 空日期哨兵值,**兩種寫法並存** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:63` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:285` |

## 附錄 D. 掃描母體與覆蓋率

### D.1 為什麼不跑 `--module OFD`

`atlas_scan.py --module OFD` 會拿 **550 支** OFD 畫面當母體算覆蓋率,本文只寫其中 56 支, 算出來是 10% 而且沒有意義。**改成自己列一張 56 支的逐支處置表(D.2)。**

母體數字仍然列出來當背景:

| 項目 | 數量 | 來源 |
|---|---|---|
| OFD 模組畫面總數 | 550 | `atlas_scan.py --list` |
| 其中 M | 214 | 同上 |
| **本片(`DataEntity.OFD9`)的 M** | **56** | 任務書清單,逐支以 `--screen` 驗過 |
| 本片碰到的表 | 111 | 附錄 A.1 |
| 本片宣告的主 / 明細表 | 59 | §2.1 |
| 本片有原始碼的 DB 物件 | 2(兩支 trigger) | 附錄 B.1 |
| 本片呼叫但不在版控的 DB 物件 | 8 | 附錄 B.2 |
| OFD 模組六層不齊 | 42 | `atlas_scan.py --list`;**一支都不在本片** |

### D.2 56 支逐支處置

「深度」:**深**=一支一節(§4.1 到 §4.4)· **中**=分組表格 + 特別之處(§4.5)· **表**=只在 §3.1 清冊與分組表出現。

| # | 畫面 | 業務線 | 深度 | 寫在哪 |
|---|---|---|---|---|
| 1 | `OFDM369` | B | 中 | §4.5.2 |
| 2 | `OFDM371` | B | 中 | §4.5.2 |
| 3 | `OFDM374` | A | **深** | §4.4.1 |
| 4 | `OFDM375` | A | **深** | §4.4.2 |
| 5 | `OFDM376` | A | 中 | §4.5.1 |
| 6 | `OFDM377` | A | 中 | §4.5.1 |
| 7 | `OFDM382` | C | 中 | §4.5.3 |
| 8 | `OFDM383` | C | 中 | §4.5.3 |
| 9 | `OFDM385` | C | 中 | §4.5.3 |
| 10 | `OFDM391` | B | 中 | §4.5.2 |
| 11 | `OFDM392` | B | 中 | §4.5.2 |
| 12 | `OFDM395` | B | 中 | §4.5.2 |
| 13 | `OFDM399` | B | 中 | §4.5.2 |
| 14 | `OFDM430` | D | 中 | §4.5.4 |
| 15 | `OFDM431` | D | **深** | §4.1.1 |
| 16 | `OFDM431bb` | D | **深** | §4.1.1 |
| 17 | `OFDM432` | D | 中 | §4.5.4 |
| 18 | `OFDM433` | D | 中 | §4.5.4 |
| 19 | `OFDM434` | D | 中 | §4.5.4 |
| 20 | `OFDM435` | D | 中 | §4.5.4 |
| 21 | `OFDM436` | D | 中 | §4.5.4 |
| 22 | `OFDM450` | E | **深** | §4.2 |
| 23 | `OFDM454` | E | **深** | §4.2 |
| 24 | `OFDM456` | E | **深** | §4.2 |
| 25 | `OFDM458` | E | **深** | §4.2、§4.6.1 |
| 26 | `OFDM481A` | F | 中 | §4.5.5 |
| 27 | `OFDM482A` | F | 中 | §4.5.5 |
| 28 | `OFDM485` | F | 中 | §4.5.5 |
| 29 | `OFDM531` | G | 中 | §4.5.6 |
| 30 | `OFDM540` | H | 中 | §4.5.7 |
| 31 | `OFDM541` | H | 中 | §4.5.7 |
| 32 | `OFDM543` | H | 中 | §4.5.7 |
| 33 | `OFDM562` | I | 中 | §4.5.8、§8.3 |
| 34 | `OFDM694B` | L | 中 | §4.5.10 |
| 35 | `OFDM700` | I | 中 | §4.5.8 |
| 36 | `OFDM710` | I | 中 | §4.5.8 |
| 37 | `OFDM711` | I | 中 | §4.5.8 |
| 38 | `OFDM712` | I | 中 | §4.5.8 |
| 39 | `OFDM713` | I | 中 | §4.5.8 |
| 40 | `OFDM714` | I | 中 | §4.5.8 |
| 41 | `OFDM721` | J | **深** | §4.1.4、§4.3.2 |
| 42 | `OFDM722` | J | **深** | §4.3.3 |
| 43 | `OFDM723` | J | **深** | §4.1.2、§4.3.4 |
| 44 | `OFDM724` | J | **深** | §4.1.2 |
| 45 | `OFDM725` | J | **深** | §4.1.4、§4.3.5 |
| 46 | `OFDM731` | K | 中 | §4.5.9 |
| 47 | `OFDM741` | L | 中 | §4.5.10 |
| 48 | `OFDM742` | L | 中 | §4.5.10 |
| 49 | `OFDM743` | L | 中 | §4.5.10 |
| 50 | `OFDM751` | M | 中 | §4.5.11 |
| 51 | `OFDM871` | N | 中 | §4.5.12 |
| 52 | `OFDM872` | N | 中 | §4.5.12 |
| 53 | `OFDM907` | N | **深** | §4.4.3 |
| 54 | `OFDM913A` | N | **深** | §4.4.4 |
| 55 | `OFDM931A` | B | **深** | §4.1.3 |
| 56 | `OFDM931B` | B | **深** | §4.1.3 |

**深 18 支 · 中 38 支 · 未寫 0 支。**

### D.3 掃描器在本片踩到的三件事

| # | 事 | 影響 | 怎麼驗 |
|---|---|---|---|
| 1 | **`atlas_scan.py --screen OFDM431bb` 回「找不到畫面 OFDM431BB」**。掃描器把代號轉大寫比對,而檔名是小寫 `bb`(`OFDM431bb.cs` / `OFDM431bb_PO.cs` …) | `OFDM431bb` **不在 908 支的清單裡**;依模組聚合的統計、覆蓋率、影響分析全部漏掉它 | `ls Dev/ATLAS.OFD/Source/PO/PO.OFD/ \| grep 431` 看得到檔,`--screen OFDM431bb` 看不到畫面 |
| 2 | **`OFDM913` 被算進 908 支,但它的三個檔都不在 csproj 裡**(§4.6.2) | 908 這個數字至少有 1 支是完全不會編譯、沒有入口的畫面 | `grep -c "OFDM913_PO.cs" Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj` 回 `0` |
| 3 | **`--table SAL908A` / `SAL915A` / `SAL920A` / `SAL925A` 報「欄位 0」**,但它們是四支畫面的主檔 | xsd 的 DataTable 名用畫面代號(`OFDM450` 等),掃描器以表名找不到欄位定義(附錄 A.2 共 34 張表中招) | `--screen OFDM450` 看得到明細欄位,主檔沒有 |

**`SAL` 家族重驗**(回應 `dsm.md §8` 的結論): `ls Dev/ | grep -i sal` 零命中(沒有 `ATLAS.SAL` 專案); `atlas_scan.py --list` 的 19 個模組碼裡沒有 `SAL`; 全庫 grep `SAL9\d\d[A-Z]?` 得 24 個表名、12 個檔案,**全部在 `ATLAS.OFD` / `ATLAS.OFDB` / `Dev/Common`**。 **結論與 `dsm.md` 一致,並補上業務意義(§4.2.1)。**

### D.4 怎麼自己查

```
py -V:3.12 \docs\tools\atlas_scan.py --screen OFDM721
py -V:3.12 \docs\tools\atlas_scan.py --table OFD721
```

`DB/` 底下 196 支檔是 `cp950`、81 支是 UTF-8,讀之前先 `sys.path.insert(0,'/docs/tools'); from atlas_scan import read_text`。 **不要 Read `*.Designer.cs`**——本片最大的一支 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM231AModel.designer.cs` 超過 25,000 行。

## 附錄 E. 讀本文時要注意的地方

讀碼過程發現的缺陷與陷阱,依嚴重度排。**每一條都是現況記錄,不是修改建議。**

### E.1 高

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E01 | **`OFDM931B` 的覆核閘門 `AND` / `OR` 缺括號**:`AND (A='OFDM931A' AND STATUS IN ('301','302') OR A='OFDM931B')`。`AND` 優先序高,後半段完全不看狀態 | 只要 `OFDM931B` 自己動過一次,之後永遠不會被「HR 尚未覆核」擋住。與 `cas.md` 的 `CASB001_PO.cs:431` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:175` | **高** |
| E02 | **`OFDM724` 的四個 WHERE 用裸 `= ''` / `<> ''`**,同組的 `OFDM723` 四個分支全部用 `NVL(欄,' ')` | Oracle 上空字串等於 NULL,四個條件全部 UNKNOWN,`UPDATE` 影響 0 列 → `if (j != 1)` 成立 → 整批 rollback。**這支在 Oracle 上等於全功能失效** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:60`、`:66`、`:72`、`:78` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:84`、`:98`、`:109`、`:118` | **高** |
| E03 | **`OFDM724` 的「只處理勾選列」整段被註解**(`//if (Convert.ToBoolean(drw.IsCheck))` 連同 `//{` `//}`),UI 側「至少須註記一筆資料」也被註解 | grid 上還有勾選欄,使用者以為勾了才送,實際對畫面上每一列都下 UPDATE。同組的 `OFDM723` / `OFDM725` 有檢查 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:100-101`、`:134`;`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM724.cs:56` | **高** |
| E04 | **`OFDM431` 缺「基金已在其他群組」檢核、`OFDM431bb` 缺 `FEE_CALDT_TYPE` 欄位**——同一張 `OFD431A` 的兩支維護畫面各漏一半 | 從 `OFDM431` 可以把同一檔基金掛進兩個群組;從 `OFDM431bb` 存檔會洗掉 `FEE_CALDT_TYPE` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431.cs:140-150` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:187-200`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:113` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:71-76` | **高** |
| E05 | **`OFDM450` 的「同機構計算戶號重複」檢核整段被 `/* */` 註解**,`OFDM454` / `OFDM456` 都有。方法名與失敗訊息仍寫「計算戶號、計算基金」 | 同一機構的同一個戶號可以被掛進兩份服務費契約 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:542-561` | **高** |
| E06 | **`IsExistSameData` / `IsExistSameBFData` / `IsExistSameAgent` 三支各建一條 `DbConnection` 卻沒有 `finally { conn.Close(); }`**(同檔的 `IsExistSameDate` 有) | 每次存檔前的檢核漏 1 到 3 條連線;`OFDM450` 的 `IsExistSameData` 連 `conn.Open()` 都在註解塊裡,連線建了完全沒用 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:537`、`:628`、`:718`(三支畫面各三處) | **高** |
| E07 | **Oracle 三值邏輯:`BMS001A.TRUST_AGENT_CODE <> :AGENT_CODE`** 判斷「開戶機構與契約機構不同」 | `TRUST_AGENT_CODE` 為 NULL 的戶號結果 UNKNOWN,不示警。`CAS` / `CLS` / `DSM` / `BBS` / `TMK` 五個模組都中過同一條,本片是第六個 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:726`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:793`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:749` | **高** |
| E08 | **Oracle 三值邏輯:`OFD724.PRT_UID <> ''`「過濾已列印的資料」**,而同一支檔的 INSERT 把 `@PRT_UID` 綁成 `string.Empty` | 自己寫進去的資料自己查不到(Oracle);SQL Server 上也會把剛寫入的那筆濾掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:91`、`:700` 對照 `:253` | **高** |
| E09 | **Oracle 三值邏輯:`PRT_UID<>''`、`PRT_DTTM<>'1900/01/01'`、`CER_SOURCE<>'5'`、`VISA_RTN_DTTM <> '1900/1/1'`、`CER_TAKE_UID <>''`、`CTL014.IsDefault <> '1'`、`OFD724.BF_CTL_SRNO <> '0'`、`PROJ <> ' '`** 八處 | 全部是「過濾(無提示)」型,NULL 的列靜默消失 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:114`、`:116`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:106`、`:285`、`:303`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM700_PO.cs:76`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:272`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM541_PO.cs:115` | **高** |
| E10 | **`DECODE(EXPIRE_DATE, ' ', '99991231', EXPIRE_DATE)` 把「一個空白」當無限遠**,但 `DECODE` 用 `=` 比對,NULL 比不到 | `EXPIRE_DATE` 為 NULL 的契約整條 `BETWEEN` 變 UNKNOWN,重疊檢核漏掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM432_PO.cs:212`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM434_PO.cs:217` | **高** |
| E11 | **五支畫面在 INSERT 時把 `Status` 寫死 `'301'`(已覆核),`EntryID` / `VerifyID` / `ApproveID` 全綁同一人** | 這些資料從來沒經過四眼,表上卻長得像已覆核;稽核軌跡失真。`architecture.md §3` 那條「覆核完資料才生效不是通則」的第三、四、五個實例 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:271-279`、`:386-394`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM369_PO.cs:231`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:212-215`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:596-601` | **高** |
| E12 | **`OFDM374` 在 `AfterAdd` / `AfterUpdate` 就寫 `BMS001`**,只有刪除等到 `AfterApproveDelete` | 「輸入當下就生效」,與 `bbs.md §4` 的 BBS 行為一樣,但**不對稱**(新增 / 修改立即、刪除要覆核) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:235-264` | **高** |
| E13 | **`OFDM374` / `OFDM375`(及 `OFDM376` / `OFDM377`)對同一張表,一支走四眼、一支不走** | 想繞過覆核,用整批畫面搬一筆就行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:36-45` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:158` | **高** |
| E14 | **字串串接進 SQL,17 處**:`UpdateID='" + strUserID + "'`(`OFDM721` 四處、`OFDM722` 三處)、`IN (" + strBF_NO + ")`(E 線三支各三處)、`" AND " + Row.Name + " = '" + Row.Value + "'"`(`OFDM931A` / `OFDM931B` 各兩處)、`"AND " + Row1.Name + "=" + Row1.Value`(`OFDM722`)、`string.Format` 串 `BF_NO` / `EMP_NO`(`OFDM907` 三處、`OFDM913A` 五處)、`OFDM725` 整支 `Execute()` | 值來自畫面;`CER_TAKE_MAN`(代領人姓名)是自由文字 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:294`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:131`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:74-75`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:569`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:228`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:120`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:391` | **高** |
| E15 | **`string.Join("OR", …)` 組 WHERE,DataTable 為空就產生 `WHERE ` 結尾的語法錯 SQL** | 匯入空檔或前一關全濾掉時,錯誤訊息變成「執行失敗,請檢查」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:118-121`、`:145-148`、`:184-187`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:388-392` | **高** |
| E16 | **`OFDM907.CheckBFExists` 用 `COUNT(0)` 對比 grid 列數** | 匯入檔有重複戶號 → `COUNT` 少算 → 誤報「受益人戶號不存在」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:150-160` | **高** |
| E17 | **`catch` 之後 `AddResultRow(false, …)`,而正常路徑的 `false` 代表「沒有重複」** | 資料庫出錯被當成檢核通過。與 `cas.md` / `cod.md` 記的「`catch` 回 `ex.Message` 當檢核結果」同一家族 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:584-591`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM454_PO.cs:659`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM456_PO.cs:614` | **高** |
| E18 | **`OFDM431bb.IsFundExsits` 回傳值三義**:找不到回 `0`、找到回 `-1`、**例外也回 `-1`**;而且 SQL 沒排除自己所在的群組 | 資料庫連不上時使用者看到「基金已存在於其他基金群組中」;修改既有群組時原本就在群組裡的基金被判重複 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:111-138`、呼叫端 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:194` | **高** |
| E19 | **`OFDM721.Execute()` 五個步驟共用一個 `i`,只用最後一個值決定 commit / rollback** | 前四步任一步影響 0 列不會被發現;而「最後一步」還取決於 `BF_CTL_SRNO != 0` 這個 if | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:487-500` | **高** |
| E20 | **`con.Open()` / `BeginTransaction()` 在 `try` 外,`catch` 無條件 `tran.Rollback()`** | DB 不通時真正的錯誤被 `NullReferenceException` 蓋掉。與 `architecture.md §3` 記的 `BasicEVAPO.Add` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:152-154` 對照 `:504` | **高** |
| E21 | **`OFDM725.CheckCER_RUNIT`(「已有贖回中單位數,不可取消領回」)整支 80 行被逐行註解**,只剩一條 `CER_RUNIT = 0` 的過濾 | 阻擋變成過濾:有贖回中單位數的憑證直接從清單消失,使用者不知道為什麼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:399-478`、`:299` | **高** |
| E22 | **`OFDM725` 的 `//if (ExecType == "3")` 被註解,它管的那一行沒被註解** | `AND OFD721.CER_SOURCE <> '5'` 現在對所有執行功能生效,不再只有第 3 種 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:302-303` | **高** |
| E23 | **`OFDM731` 三條必填檢核全被註解**(結匯銀行代碼、中文名稱、「明細資料至少要輸入一筆」) | 可以存一筆沒有代碼、沒有名稱、沒有明細的結匯銀行 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM731.cs:115`、`:120`、`:126` | **高** |
| E24 | **`OFDM913A.CheckEffective` 把字串欄 `emp_no` 跟未加引號的值比**:`string.Format("… AND emp_no={2}", …, r.EMP_NO)` | Oracle 隱式轉型,值含非數字就 `ORA-01722` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:391` | **高** |
| E25 | **`OFDM913A.AfterApprove` 的第一段是 `DELETE OFD913A_UPD WHERE BF_NO = :BF_NO AND nvl(CONFIRM_ID,' ')<>' '`**——刪掉這個戶號**所有**已確認的歷史 | 這張表沒有歷史,只有最後一次確認。要追「這個客戶換過幾次業務員」查不到 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:109`、`:591` | **高**(設計面) |
| E26 | **`OFDM382` 的六處 `AddResultRow` 全部被註解** | PO 有完整的新增 / 修改 / 刪除流程,但所有成功與失敗訊息都不會出現 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM382_PO.cs:264`、`:360`、`:497`、`:511`、`:589`、`:665` | **高** |

### E.2 中

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E27 | **`ReturnCode = true` 代表「擋下」**,與全庫其他地方相反,出現在 `OFDM931A` / `OFDM931B` 的兩道閘門與 `OFDM371` 的兩句訊息 | 任何人照全庫慣例讀這幾支都會判斷相反 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:155`、`:187`;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM371_PO.cs:760`、`:771` | 中 |
| E28 | **`DoValidate()` 兩條分支回同一個值**:`if (ErrorCount > 0) return true; return true;` | 回傳值是假的;真正擋下的是呼叫端的 `ValidateErrList.Show()` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:86-88`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931B.cs:88-90` | 中 |
| E29 | **`OFDM931A` / `OFDM931B` 讀 `Rows[0][0]` 不檢查 `Rows.Count`** | 查詢回空集合就 `IndexOutOfRangeException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:184`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:183` | 中 |
| E30 | **`OFDM724` 用 grid 第 0 列的 `VISA_ID` 決定整批要不要更新 `OFD721`** | 多筆混合 `A` 與 `D` 時整批照第一列決定 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:88` | 中 |
| E31 | **`OFDM724` 把 SET 與 WHERE 串在同一個字串裡,套用到 `OFD724` 與 `OFD721` 兩張表** | 兩張表被迫永遠有同名的 `VISA_UID_D` / `VISA_DTTM_D` / `VISA_RTN_UID` / `VISA_RTN_DTTM` 四欄;加一欄要兩張一起加 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:57-60`、`:106`、`:122` | 中 |
| E32 | **`OFDM723` 兩個交易(業務庫 + 平台庫序號)沒有補償**:取到簽證號但業務更新失敗,號就跳掉 | 簽證序號斷號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:55-59`、`:130` | 中 |
| E33 | **`BF_CTL_SRNO` 一欄三種型別認知**:xsd 是 string、`OFDM721_PO` 綁 `SqlDbType.Int`、`OFDM723` 拿字串 `'0'` 比 | 隱式轉型;索引失效 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:446`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:272` | 中 |
| E34 | **`OFDM722` 拿字串欄跟數字比**:`OFD721.CER_STATUS=2`(無引號) | SQL Server 全欄轉數字,索引失效;欄內有非數字值直接轉型錯誤 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:112` | 中 |
| E35 | **`OFDM913A` 用 `strSQL.ToUpper()` 送 SQL** | 目前只有 `' '` 與日期格式字串,剛好無害;任何人日後在這兩段加含小寫的字串字面值就會壞 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:110`、`:127` | 中(未爆彈) |
| E36 | **`if (j == -1)` 判斷 DELETE 失敗**,而 `ExecuteNonQuery` 刪 0 列回 `0` | 這道檢查永遠不成立 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:114`、`:614` | 中 |
| E37 | **`OFDM907.CheckExists` / `CheckEffective` 成功時不寫 Result,而且先 `Clear()` 掉輸入資料** | 呼叫端拿不到「檢核通過」的訊號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:122`、`:188` | 中 |
| E38 | **`OFDM907` 的日期區間查詢:有起日就直接讀迄日,不檢查 null** | 只填起日 → `NullReferenceException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM907_PO.cs:102-103` | 中 |
| E39 | **`ex.Message` 直接當使用者訊息** | Oracle / SQL Server 的原始訊息含表名、欄名甚至 SQL 片段。`cas.md` / `cod.md` 記過同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM375_PO.cs:413`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM377_PO.cs:363`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM731_PO.cs:518`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM913A.cs:310`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM531.cs:305` | 中 |
| E40 | **`throw ex;` 重設堆疊** | 原始出錯位置消失,外層再給空訊息 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:147` | 中 |
| E41 | **`OFD562_T02` 在 `IF (INSERTING OR UPDATING)` 裡用 `:OLD.*` 當 DELETE 條件** | INSERT 時 `:OLD` 全 NULL,那段 DELETE 空轉 | `DB/Trigger/OFD562_T02.SQL:38-53` | 中 |
| E42 | **`OFD562_T01` 用 `NVL(:NEW.BF_NO, :OLD.BF_NO)` 查、用 `:OLD.BF_NO` 寫** | 改戶號時查新寫舊 | `DB/Trigger/OFD562_T01.SQL:16` 對照 `:34`、`:37`、`:42` | 中 |
| E43 | **`OFD374` 的欄位清單有兩套大小寫並存**(`DATAID`/`dataid`、`STATUS`/`Status` …,共 34 欄),來源是 BMS 與 RSP 兩個模組的 xsd | Oracle 上是同一批欄位;SQL Server 若 collation 區分大小寫就會出事 | `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd` 與 `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd` | 中 |
| E44 | **`OFD913A_UPD` 有三個名字極像的狀態欄**:`Status`(框架)、`STATUS`(Caption「資料狀態」)、`STATUSDESC`(Caption 也是「資料狀態」) | 最容易改錯的欄位組 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM913AModel.xsd` | 中 |
| E45 | **xsd DataTable 名與實體表名交叉錯位**:`OFDM742` 既是畫面也是 DataTable(裝 `OFD742` 或 `OFD743`);`OFD743` 既是實體表也是 DataTable(裝 `OFD746`) | 看到名字要先問「這是表還是 DataTable」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs:25`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:27`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM743_PO.cs:19` | 中 |
| E46 | **同一張 `OFD431A` 有兩組不同命名法的 xsd 與 VDB 並存** | 搜尋永遠雙份;改 schema 要改兩套 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431Modelbb.xsd` 與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM431bbModel.xsd` | 中 |
| E47 | **`OFDM431bb` 在 `foreach` 內 `new OFDM431bb_Pxy()` 逐列遠端呼叫** | 明細 200 列就是 200 趟 Remoting | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM431bb.cs:191` | 中 |
| E48 | **`OFDM913A` 五支檢核在 `foreach` 內逐列查資料庫** | 同上,而且全部沒參數化 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM913A_PO.cs:340-357`、`:479-501`、`:537-558` | 中 |
| E49 | **`OFDM450` 的 `IsExistSameAgent` 有兩段客戶特定分支,`OFDM454` / `OFDM456` 沒有** | 同一條業務規則在服務費契約放寬了,在手續費契約沒有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM450_PO.cs:729-739` | 中 |
| E50 | **`OFD068A_V01` 這支 view 不在 `DB/View/`**(只有 `_V02`) | 兩版差異無從比較;`dsm.md §8` 分析的是 `_V02` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM432_PO.cs` | 中 |
| E51 | **`f_GetEVAStatus`(SQL Server TVF)與 `dbo.PADLeft`(SQL Server 純量函式)不在版控,且 Oracle 不支援** | 這幾支畫面綁死在 SQL Server | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:122`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:207` | 中 |
| E52 | **`OFDM721` 算好的 `DATA_SEQ` 被註解掉不用,但兩支取號方法仍然每次都跑**(各開一條連線) | 兩趟無用的往返;兩個變數賦值後不被讀 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM721_PO.cs:160-162`、`:248`、`:318-320`、`:376` | 中 |
| E53 | **`OFDM374_PO.cs` 1,829 行裡 1,222 行(66.8%)是一整塊 `/* */` 註解**,含一份完整的第二個建構子 | `architecture.md` 附錄 E 的 E28 在本片的極端值;`OFDM376` / `OFDM711` / `OFDM712` / `OFDM713` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:604-1824` | 中 |
| E54 | **`OFDM531` 的上傳成功訊息寫「已上傳{0}筆指派客戶資料」**,這支傳的是匯率 | 文案從別的畫面複製來的 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM531_PO.cs:207` | 中 |
| E55 | **`OFDM450` 那段被註解的重複檢核裡,訊息指到錯誤的 grid**(`ugrdSAL912A`,應為 `ugrdSAL913A`);`OFDM454` / `OFDM456` 的對應位置指對了 | 死碼,但證明這一段是手改的。與 `bbs.md` 的 `BBSM013_PO.cs:1260` 記錯書號同型 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:439` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM454.cs:354` | 中 |
| E56 | **迴圈遇壞列 `break`**:被註解的重複檢核區塊裡用 `break` 跳出整個 `foreach`,只回報第一筆重複 | 目前是死碼,但同一段若被解除註解就會靜默吃掉後面全部 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM450.cs:442`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM454.cs:357` | 中 |
| E57 | **詢問型訊息走失敗通道**:「…是否繼續執行?」「…請確認是否仍要修改?」「已設定 KYC 問卷分數等級對應,是否刪除?」三處都用 `AddResultRow(false, …)` | 呼叫端要靠訊息文字判斷這是問句還是錯誤 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM871_PO.cs:299`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs:283`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:418` | 中 |
| E58 | **`OFDM482A` 把日期字串塞進 `ReturnMessage` 當資料值回傳** | 訊息欄位被當資料通道 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM482A_PO.cs:231` | 中 |
| E59 | **寫死中文字串當判斷條件**:`EMP_NAME='未到職'`、KPI 名稱含「質化目標」 | 姓名剛好是這三個字就被誤判;KPI 改名就失效 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:83`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM399.cs:76` | 中 |
| E60 | **PO 類別名不照命名鐵律**:`OFDM430AOracleDao` / `OFDM431AOracleDao`(在 `PO.OFD` 而不是 `.Query` 專案) | `architecture.md §2` 說這種命名只在 `.Query` 專案,**本片是反例**;以命名找層的工具會誤判 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM430_PO.cs:27`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431_PO.cs:24` | 中 |
| E61 | **`DB/` 下與本片相關的四支檔都是 `cp950`**(全 `DB/` 196 支 cp950 / 81 支 UTF-8) | 讀檔不指定編碼就是亂碼 | `DB/Trigger/OFD562_T01.SQL`、`DB/Trigger/OFD562_T02.SQL`、`DB/Trigger/OFD561_T02.SQL`、`DB/View/OFD068A_V02.SQL` | 中 |
| E62 | **`OFD562` 的 `OFD562_T02` 任何 UPDATE 都觸發**,而四眼引擎每次 EVA 都會改那 13 欄 | 每一次驗證 / 覆核都重寫一次 `OFD662` | `DB/Trigger/OFD562_T02.SQL:2` | 中 |

### E.3 低

| # | 發現 | 錨點 | 嚴重度 |
|---|---|---|---|
| E63 | 同一句訊息在 `OFDM713` 四處,其中一處空白位置不同(`{0} +{1} + {2}`),證明是手改 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM713_PO.cs:1079` | 低 |
| E64 | 同一欄 `G_MEMO` 的 grid 標題兩支不同:「單位主管調整金額原因」與「單位主管調整原因」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931A.cs:355` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM931B.cs:357` | 低 |
| E65 | 同一段 SQL 兩支寫法差一個空白:`CTL_CODE='2'` 與 `CTL_CODE = '2'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931A_PO.cs:144` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM931B_PO.cs:142` | 低 |
| E66 | 五支畫面同一行死碼:`SELECT * FROM [OFDxxx] Where ((UpdateID <> '…') OR (RejectID <> ''))"; ;`(兩個分號) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:1238`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM376_PO.cs:820`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM711_PO.cs:514`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM712_PO.cs:750`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM713_PO.cs:712` | 低 |
| E67 | 空日期哨兵值兩種寫法並存:`'1900/01/01'` 與 `'1900/1/1'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM724_PO.cs:63` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM725_PO.cs:285` | 低 |
| E68 | `OFDM723` case 3 把 `VISA_NO` 設成 `' '`、case 4 設成 `''`,後續判斷靠 `NVL` 救回來 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM723_PO.cs:93` 對照 `:113` | 低 |
| E69 | `OFDM374_PO_BeforeDelete` 是空方法但仍註冊 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM374_PO.cs:219-221` | 低 |
| E70 | `OFDM432` / `OFDM434` 用 `MessageBox.Show` 而非框架的 Dialog(全片僅此兩處) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM432.cs:265`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM434.cs:255` | 低 |
| E71 | `IsFundExsits` 方法名拼錯(應為 `Exists`),而且全庫六支同名方法語意各不相同 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM431bb_PO.cs:111` | 低 |
| E72 | `OFDM722` 的註解「鉤斷有鉤選」(應為「判斷有勾選」) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM722_PO.cs:243` | 低 |
| E73 | `OFDM742` 的「此問卷版本已被使用,不可修改」被註解,但 PO 側「不可刪除」仍生效 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM742.cs:267` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM742_PO.cs:364` | 低 |
| E74 | 本片五支憑證畫面沒有一支用官方的 `CerStatusDataSrc` 下拉,狀態值全寫字面值 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM723.cs:382` | 低 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD9` 的 56 支 M 畫面;更正 `bbs.md` 的 `CER_STATUS` 值域三處、更正任務書對 `OFDM913` 的兩項描述、補上 `SAL9xx` 的業務意義。 |

由 build_doc.py v2.0.0 於 2026-09-15 11:47 產生 · 標題 112 · 圖 5 · 表格 103 · 程式錨點 623 · § 連結 148 · 引用檢查：畫面 80（缺 0） · Table 98（缺 0） · Trigger 2（缺 0） · View 1（缺 0） · 結果集 17（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
