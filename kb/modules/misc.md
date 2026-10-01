<!-- 由 tools/build_copilot_kb.py 從 modules/misc.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS MISC 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這一片最反直覺的事)、各畫面節末的卡控總表、附錄 E(踩雷)。

> ⚠ **這不是一個模組,是四個小模組加一組寄生畫面的收尾片。**21 支畫面橫跨 `TRP` / `OTA` / `FSK` / `IJP` 四個畫面代號前綴,再加 11 支代號是 `OFD` 但住在 `ATLAS.OTA` 專案的維護畫面;型別 M / I / R 都有。所以本文沒有單一的「業務主線」,§0 是四份邊界說明並排。 ⚠ **業務意義全部由表名、`msdata:Caption`、彈出視窗標題與報表中文名反推**,選單表不在版控。手法沿用 `cas.md §0`。四個前綴的字母展開在 repo 內都查不到定義,本文一律用業務描述,**不造官方名稱**。 ⚠ **〔客戶特定〕**:傳檔落地路徑、媒體代號 `TTP12A`、信件代碼 `07`、`WebUser%` 這類值是本站台的,換站一定要重新確認。 ⚠ **〔共用〕**:`FSK005`、`BMS999`、`OFD220` / `OFD221`、`OFD302` 這幾張表同時服務其他模組(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別與 R 的七層看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 四個模組各管什麼(推測)

| 前綴 | 支數(本片) | 管什麼(推測) | 反推依據 |
|---|---|---|---|
| `TRP` | 6(M×4 / I×1 / R×1) | **境外基金對集保申報平台的傳檔與收檔**:把 TA 的資料依規格產成媒體檔送出、把對方回來的媒體檔收進來,保存傳收檔紀錄,並維護境外基金月報 | 控件標題「申報平台種類」「週期」「傳檔存放路徑」「收檔媒體格式」;彈出視窗標題「集保傳檔錯誤資料顯示」「集保收檔錯誤資料顯示」;`TRP011` 欄位是「月報年月」「基金投資大陸地區證券市埸有價證券比率%」 |
| `OTA` | 2(M×1 / R×1) | **境外基金交易平台的雜項**:報表行銷說明代碼維護、弱勢族群交易回訪報表 | 控件標題「報表行銷說明代碼」;報表中文名「弱勢族群交易回訪報表(境外)」 |
| `FSK` | 1(M×1) | **證券經紀商(券商)基本資料維護** | 控件標題「券商代碼」「券商中文名稱」「總券商代碼」「券商類別」;PO 內註解「新增證券經紀商基本資料」 |
| `IJP` | 1(R×1) | **網路交易約定書列印**,是 `IPJ` 的錯字,見 §0.4 | 報表選項「全方位理財約定書」「查詢戶約定書」「舊戶轉查詢戶約定書」 |
| `OFD`(住 `ATLAS.OTA`) | 11(M×11) | **境外基金綜合帳戶軌的申購 / 買回 / 定期定額 / 配息 / 淨值 / 授權書維護**,與 `ATLAS.OFD` 的同名系列平行,見 §0.3 | `OMNIBUS_ID` 欄位、`GetSrIdNoForOTA` 取號函式、`S_OTA_*` 專屬 SP 命名空間 |

反推依據的錨點,逐條可查:

| 前綴 | 證據 | 出處 |
|---|---|---|
| `TRP` | 「申報平台種類」「週期」;彈窗「集保傳檔錯誤資料顯示」「集保收檔錯誤資料顯示」;「傳檔存放路徑」;「月報年月」「整批匯入」「月報製作」 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.designer.cs:283` 與 `:372`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001p0.designer.cs:179`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM101p0.designer.cs:179`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.designer.cs:527`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.designer.cs:385` 與 `:518-519` |
| `OTA` | 「報表行銷說明代碼」;報表名「弱勢族群交易回訪報表(境外)」 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.designer.cs:376`、`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:130` |
| `FSK` | 「券商代碼」「券商中文名稱」「總券商代碼」 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.Designer.cs:320`、`:362`、`:501` |
| `IJP` | 報表選項「全方位理財約定書」等五項 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:203-212` |
| `OFD`(OTA 軌) | 方法註解「取得有綜合帳戶交易幣別」+ SQL 條件 `OMNIBUS_ID = 'Y'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453` 與 `:463` |

### 0.2 這一片最反直覺的三件事

**(1)`TRP` 的商業規則不在程式裡,在資料表裡。**

`TRPM001`(傳檔)與 `TRPM101`(收檔)不自己組任何業務 SQL。它們去 `TRP001` 設定檔把**一整串 SQL 文字**讀出來,再送到伺服器執行。 `TRP001` 一列就有 `CHECK_SQL1` 到 `CHECK_SQL4`(檢核)、`SQL11` 到 `SQL14`(異動)、`SQL_OUT`(輸出),外加對應的 `Y/N` 開關與錯誤訊息文字 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582`)。伺服器端 `ExcuteSQLandLoadData` 只負責照收照跑 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:144-207`)。

**後果**:讀程式讀不出任何一條傳檔規則;要知道申報平台到底檢核什麼、寫哪張表,只能去 DB 撈 `TRP001`。收檔端更徹底,連 INSERT 語法都存在 `TR202.INSERTSQL` 欄位裡(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:858-893`)。

**(2)11 支 `OFDM*` 不是「OTA 借用 OFD 的畫面」,是同一件事的第二條帳務軌。**

`ATLAS.OFD` 的 `OFDM221A` 寫 `OFD220A` 與 `OFD221A`;`ATLAS.OTA` 的 `OFDM221C` 寫 `OFD220` 與 `OFD221`。 **表名差一個 `A`,是兩組不同的實體表**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-68` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:81-84`)。詳見 §8.1。

**(3)四支畫面走的是不同世代的資料存取,其中一支已經是死的。**

`FSKM004_PO` 繼承 `BasicEVAPO`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29`),依 `architecture.md §3` 的結論,這條路徑的 `dbTA` 從沒被賦值,**連按查詢都會 NRE**。同一支的 1,272 行裡有 950 行是被註解包起來的上一代實作(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270`)。

### 0.3 十一支 `OFDM*` 的歸屬問題

問題是:代號前三碼是 `OFD`,專案卻是 `ATLAS.OTA`。三個查證結果:

| 查證 | 結果 | 依據 |
|---|---|---|
| (a) 同代號是否也存在於 `ATLAS.OFD` / `ATLAS.OFDB` / `ATLAS.OFDI` / `ATLAS.EC`? | **11 支全部沒有同代號分身。**與 `ofdb3.md` 查到的 `OFDB562` 到 `OFDB564` 兩處各一份六層完全不同 | 全庫搜這 11 個代號,命中只在 `Dev/ATLAS.OTA/` 底下 |
| (b) 是不是「OTA 專用的 OFD 畫面」? | **是,而且分家方式是「代號加後綴 + 表名去掉 A」。**帶後綴的四支都能在 `ATLAS.OFD` 或 `ATLAS.EC` 找到姊妹畫面 | 見下表 |
| (c) 兩軌怎麼區分? | 靠 `OMNIBUS_ID` 欄位與專屬取號 `GetSrIdNoForOTA` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:164`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:463` |

後綴四支與姊妹畫面對照:

| 本片畫面(專案 `ATLAS.OTA`) | 主檔 | 姊妹畫面 | 姊妹的專案 | 姊妹的主檔 |
|---|---|---|---|---|
| `OFDM221C` | `OFD220` + `OFD221` | `OFDM221A` | `ATLAS.OFD` | `OFD220A` + `OFD221A` 再加六張明細 |
| `OFDM231B` | `OFD251` + `OFD252` `OFD253` `OFD254` | `OFDM231A` | `ATLAS.OFD` | `OFD251A` + `OFD252A` `OFD253A` `OFD254A` 再加七張明細 |
| `OFDM302B` | `OFD302` | `OFDM302` | `ATLAS.OFD` | `OFD302A` |
| `OFDM602A` | `OFD605` | `OFDM602` | `ATLAS.EC` | `OFD605`(**整個類別被註解掉,是死的**,`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19`) |

**`C` 後綴不是版本號,是第三個變體。**`ATLAS.OFD` 底下同時有 `OFDM221A` 與 `OFDM221B`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221B.cs`),`OFDM221C` 是第三支。 `OFDM221B` 只有 UI 一層,掃描器查不到它的六層。**假設**:它是 `OFDM221A` 的子視窗或殘留;依據是它不在畫面代號母體內、也沒有自己的 PO / Ctl / Entity。要確認得看 `OFDM221A` 是否在程式裡 new 它。

另外七支(`OFDM109` `OFDM111` `OFDM113` `OFDM251` `OFDM551` `OFDM554` `OFDM561`)**在全庫是唯一實作**,`ATLAS.OFD` 沒有同號畫面,也沒有帶 `A` 的姊妹表。也就是說:**綜合帳戶軌有一部分功能是 OFD 主軌沒有的**,不是單純複製。

### 0.4 `IJP` 對 `IPJ`:是打錯字,而且錯得很徹底

`architecture.md §9` 已經記錄「`IJPR611` 是打錯的畫面代號」。本片的補充查證:

| 查證 | 結果 |
|---|---|
| 錯字範圍 | **不是只錯在檔名,是七層全錯。**`IJPR611_Ctl.cs` / `IJPR611_Pxy.cs` / `IJPR611OracleDao.cs` / `IJPR611.cs` / `IJPR611_9iModel.xsd` / `IJPR611_9iView.xsd` / 七支 `.rpt`,連類別名 `IJPR611_Ctl`、介面名 `IIJPR611PO`、typed DataSet 的表名都是 `IJP` |
| 有沒有 `IPJR611`? | **沒有。**全庫零命中,所以不是兩支畫面,是同一支從頭錯到尾 |
| 同目錄的對照組 | 同一個 `ReportControl.EC` 裡有 `IPJR607_Ctl.cs` 與 `IPJR901_Ctl.cs`,拼法正確 |
| 專案與命名慣例 | 與 `IPJ` 完全一致:住 `ATLAS.EC*`、PO 叫 `<代號>OracleDao.cs`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:38`)、entity 帶 `_9i` 後綴、六層不齊 |
| 業務內容 | 電子交易的**約定書列印**,與 `IPJ` 的其他 15 支同一條線 |

**結論:是打錯字,不是兩個模組。**它跟 `IPJ` 共用專案、共用命名慣例、共用 `EC` 的表。修正要動七層的檔名、類別名、namespace、xsd 根節點名與七支 `.rpt` 的名稱,**不在本階段動,只記錄**。

### 0.5 使用角色(推測)

| 角色 | 用哪些畫面 | 依據 |
|---|---|---|
| 申報作業人員 | `TRPM001` 傳檔、`TRPM101` 收檔、`TRPI001` 查紀錄 | 三支的操作對象都是媒體檔與檔名,不是客戶資料 |
| 申報平台管理者 | `TRPM005` 路徑參數、`TRPM901` 月報 | 兩支都是設定或彙總,不處理個別交易 |
| 境外基金作業人員 | `OFDM109` `OFDM111` `OFDM113` `OFDM221C` `OFDM231B` `OFDM251` `OFDM551` `OFDM554` `OFDM561` `OFDM602A` | 全部是交易 / 契約 / 授權書單據維護,走完整四眼 |
| 淨值作業人員 | `OFDM302B` | 匯入淨值並鎖定,**不走四眼**(§4.11) |
| 代碼維護人員 | `OTAM901`、`FSKM004` | 兩支都是純代碼或基本資料檔 |
| 報表使用者 | `TRPR001`、`OTAR901`、`IJPR611` | 三支都只有查詢條件與輸出 |

**權限在哪?**`architecture.md §9` 說選單與權限表不在 repo。本片 21 支畫面裡**沒有任何一支在程式內做角色或權限判斷**。實測搜過 `UserID` / `EmpNo` / `Security` / `Permission` / `Role`,只在寫入稽核欄位時用到 `this.UserID` (例 `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:481`),沒有一處拿來做可視範圍或功能開關。

### 0.6 不管什麼

- **不管境外基金主檔本身。**`OFD062`(基金公司)、`OFD081`(基金)、`OFD068`(銷售機構)都是唯讀 join 進來的。

- **不管排程。**`TRP` 的傳收檔、`OFDM302B` 的淨值匯入全部是使用者按按鈕觸發,repo 內查不到對應的 WindowsService。

- **不管檔案傳輸本身。**`TRPM001` 只把 CSV 寫到本機或網路磁碟(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527`),真正送到集保是另一套工具或人工上傳。

- **本片無 B 型畫面**,原因見 §6。

### 0.7 全域開關

| 開關 | 位置 | 影響 |
|---|---|---|
| `TRP001.FILE_STYLE` | 資料表 | `'T'` 是傳檔、其他是收檔;`TRPM001` 硬鎖 `'T'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594`) |
| `TRP001.TRP_TYPE` | 資料表 | `TRPM001` 硬鎖 `IN ('A','T','R')`,程式註解寫「只處理境外種類」(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`) |
| `TRPARAMS.TRP_PARAMS` | 資料表 | 傳檔落地路徑,格式是 `TSCD_RPT_PATH=` 加路徑,由 `TRPM005` 維護、`TRPM001` 剝前綴使用(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192` 對照 `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356`) |
| `OFD302.NAV_LOCK` | 資料表 | 淨值鎖定碼,`OFDM302B` 依它決定能不能改(§4.11) |
| `OMNIBUS_ID` | 資料表欄位 | 分綜合帳戶軌與分戶軌,**但兩套代碼值並存**,見 §2.5 |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] MISC 全景:TRP 申報平台、11 支綜合帳戶軌 OFDM、OTA 自有 2 支、FSK 1 支、IJP 1 支,以及兩條跨塊呼叫
圖中文字:① TRP 集保申報平台(6 支,本片唯一完整 CRUD 鏈) / TRPM005 / 參數 TRPARAMS / TRPM001 / 傳檔 產 CSV / TRPM101 / 收檔 檢核入帳 / TRPI001 / 傳收檔紀錄查詢 / TRPM901 TRPR001 / 月報維護與報表 / ② ATLAS.OTA 裡的 11 支 OFDM(境外基金綜合帳戶軌) / OFDM109 OFDM111 OFDM561 / 授權書與扣款帳戶 / OFDM113 OFDM251 / 配息設定與公告 / OFDM221C / 申購 OFD220/221 / OFDM231B / 買回轉換 OFD251+3 / OFDM551 OFDM554 / 定期定額契約與變更 / OFDM302B / 淨值匯入與鎖定 繞四眼 / OFDM602A / 文件需求 OFD605 / OFD302 下游 / CLSR002 OFDI058 OFDB322… / ③ OTA 自有代號(2 支)與 FSK(1 支,死畫面) / OTAM901 / 報表行銷說明 BMS999 / OTAR901 / 弱勢族群回訪報表 / FSKM004 / BasicEVAPO 查詢即 NRE / FSK005 下游 / ucStkBrk 餵全庫下拉 / ④ IJP(1 支,是 IPJ 的錯字) / IJPR611 / 電子交易約定書 七式 / 畫面只選得到五式 / RPS6 RPS7 是死碼 / IPJR607 IPJR901 / 同目錄 拼法正確 / ⑤ 唯二的跨塊程式呼叫 / TRPM101 → OFDM053_PO / TTP12A 時寄信 代碼 07 / OFDM551 → S_OTA_OFDR552_GET / 維護畫面借報表的 SP / 其餘只靠表相連 / 沒有程式呼叫關係
```

*圖:圖 1 全景。橘框=本片的主要維護入口;橘虛框=繞過四眼、寫死值或已死的行為;灰虛框=本片以外的下游或對照組。四個模組各自獨立,只有標示的兩條線是真的程式呼叫。*

看圖的四個重點:

1. **四塊之間沒有程式呼叫關係,但有兩條真實的跨塊呼叫。** 第一條:`TRPM101`(收檔)在收到媒體代號 `TTP12A` 時,**直接 new 另一個模組的 PO** 去寄信 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687`,用的是 `OFDM053_PO.SEND_MAIL_PROC`)。第二條:`OFDM551`(定期定額契約)在畫面上叫報表用的 SP `S_OTA_OFDR552_GET` 取契約變更資料 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:509`)。除此之外各塊只靠表相連。

2. **11 支 `OFDM*` 自己構成一條完整的境外基金作業鏈**:開戶周邊(授權書 `OFDM109` / `OFDM111` / `OFDM561`)→ 配息設定(`OFDM113` / `OFDM251`)→ 申購(`OFDM221C`)→ 買回與轉換(`OFDM231B`)→ 定期定額(`OFDM551` / `OFDM554`)→ 淨值(`OFDM302B`)→ 文件需求(`OFDM602A`)。

3. **`TRP` 那條線是唯一一條完整 CRUD 鏈**(設定 → 傳 → 收 → 查 → 報),而且它同時是本片唯一「規則存在資料表裡」的一塊。

4. **`FSKM004` 是孤島而且是死的**,但它維護的 `FSK005` 被共用 PO 讀去餵全庫的券商下拉(§8.3)。

### 1.2 資料表關係

見 §2 節首的圖。要記住三件事:

- **主明細靠 `dataid` 綁定,不是外鍵**(`architecture.md §3`),所以主檔與明細一定一起送審、一起覆核。

- **`OFD220` / `OFD251` 這一組沒有 `A` 後綴,是綜合帳戶軌專用**;`ATLAS.OFD` 用的是同名加 `A` 的另一組表。兩組表結構相近但欄位數差很多(`OFD251` 152 欄、`OFDM231A` 的 `OFD251A` 另計)。

- **`TRP001` / `TR202` / `TR206` / `TR207` 這四張是「設定即程式」的表**,裡面存的是 SQL 文字、欄位對照與 SP 名稱,不是業務資料。它們不在任何一支 PO 的 `xTableMapping` 裡,所以掃描器不會把它們算成本片的實體表。

### 1.3 主要維護畫面的四眼與卡控順序

11 支 `OFDM*` 與 `TRPM005` / `TRPM901` / `OTAM901` 走標準四眼鏈,順序與 `cas.md §1` 描述一致:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼,從呼叫端反推) | 紅框加訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接叫 `_Pxy` 的 `befPostCheck`(只有 `OFDM221C` / `OFDM231B` 有) | 對話框 |
| 4 主檔欄位回填明細 | `SetMasterToDetail()` | 不會失敗,但漏欄位會讓明細主鍵是空的 |
| 5 PO 的 `BeforeAdd` 取號 | `GetTradeId` 取基金公司交易代碼再 `GetSrIdNoForOTA` 產書號 | 取不到 `TRADE_ID` 丟例外,整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `AfterAdd` / `AfterUpdate` | 只有 `OFDM221C` / `OFDM231B` 有,用來同步 `OFD113` 配息設定 | 例外 → 整筆回滾 |

**三支例外不走這條鏈**:

| 畫面 | 為什麼不走 |
|---|---|
| `TRPM001` / `TRPM101` | UI 基底是 `xOneStepProcessForm` 不是 `xMaintainForm`,PO 沒有基底類別、自建 `Database`,沒有四眼概念(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37`) |
| `OFDM302B` 的整批匯入 | `BatchAdd` 自己組 INSERT 並**直接把 `STATUS` 寫成 `'301'`、四眼六個 ID / DATE 一次填滿**,完全繞過引擎(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:208-209`) |
| `TRPM901` 的整批匯入 | 同樣是 `BatchAdd` 先 `DELETE` 再 `INSERT`,把四眼欄位當一般欄位寫(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282`) |

### 1.4 批次 / 報表資料流

本片**沒有 B 型畫面**(§6),所以「批次」全部是使用者按按鈕的一次性作業。三種形態:

| 形態 | 畫面 | 資料流 |
|---|---|---|
| 產檔 | `TRPM001` | 伺服器跑 `TRP001` 裡設定的 SQL 取出 CSV 列 → 回傳到用戶端 → 用戶端 `StreamWriter` 寫到本機路徑 → 回寫 `TRP002` 紀錄 |
| 收檔 | `TRPM101` | 用戶端讀檔案內容塞進 `CSVDATA` → 伺服器逐欄檢核 → 寫暫存表 → 叫 `TR207.UPDSTP` 指定的 SP 正式入帳 |
| 匯入 | `TRPM901`、`OFDM302B` | 用戶端讀 Excel / 檔案 → 伺服器 `DELETE` 再 `INSERT`,不走四眼 |

報表三支都照 `architecture.md §6` 的兩條往返:`GetReportData` 取資料、`GetReportObject` 拿 `.rpt` 的 byte, 後者的類別名由用戶端傳進來,伺服器照單全收(`Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/TRPR001_Ctl.cs:61-62`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,以下是**推測**的順序,依據是資料相依。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期 | 申報平台管理者 | 設定各申報種類 / 週期的傳檔落地路徑 | `TRPM005` | `TRP001` 要先有該種類的設定列 |
| 平時 | 境外基金作業 | 建立受益人的匯款授權書、扣款帳戶 | `OFDM109` `OFDM111` `OFDM561` | 受益人要先在 `BMS001A` 存在 |
| 平時 | 境外基金作業 | 設定配息方式與再投資基金 | `OFDM113` `OFDM251` | 基金要先在 `OFD081` / `OFD086` 存在 |
| 交易日 | 境外基金作業 | 申購、買回、轉換單據 | `OFDM221C` `OFDM231B` | `OFD081` 的最後交易日與 `OFD303` 的結帳狀態(§4.6、§4.7) |
| 交易日 | 境外基金作業 | 定期定額契約與契約變更 | `OFDM551` `OFDM554` | 契約要先有 `RSP_NO` |
| 每日淨值到齊後 | 淨值作業 | 匯入淨值、鎖定 | `OFDM302B` | 基金要在 `OFD081` |
| 每日 / 每週 / 每月 | 申報作業 | 依週期傳檔給集保 | `TRPM001` | `TRP002` 的上次傳檔日決定本次日期(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:541-556`) |
| 收到回檔後 | 申報作業 | 收檔、檢核、轉入 | `TRPM101` | 媒體格式要在 `TR206` / `TR202` / `TR207` 設定好 |
| 隨時 | 申報作業 | 查傳收檔紀錄 | `TRPI001` | — |
| 月結 | 申報平台管理者 | 產月報、出月報報表 | `TRPM901` → `TRPR001` | `TRP011` 要先有資料 |

**假設**:傳檔週期由 `TRP001.PERIOD` 決定(`'M'` 為月、其他為日),依據是 `TRPM001` 對 `'M'` 走 `ADD_MONTHS` 推下一個年月、其他走 `TA_GETBUSINESSDAY` 推下一個營業日 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:549-556`)。實際有哪些週期值要查 DB。

## 2. 資料模型

```text
[圖] MISC 的資料表:TRP 的設定表、綜合帳戶軌的主明細、兩軌表名差一個 A,以及唯讀 join 的外部表
圖中文字:TRP:四張「設定即程式」的表 + 兩張資料表 / TRP001 / 存 13 欄 SQL 文字 / TR202 TR206 TR207 / 收檔 SQL 欄位對照 SP 名 / TRP002 / 傳檔紀錄 / TRPARAMS / 落地路徑 主檔 / TRP011 / 月報 主檔 / 綜合帳戶軌:主明細靠 dataid 綁定,不是外鍵 / OFD109 → OFD110 / 授權書 匯款帳戶 / OFD111 → OFD112 / 授權書 期間 / OFD561 → OFD562 / 扣款授權 扣款帳戶 / OFD551 → OFD552 / 定期定額契約 / OFD554 → OFD555 / 契約變更 / OFD220 → OFD221 / 申購書 39 欄 / OFD251 → OFD252 253 254 / 買回書 152 欄 / OFD113 OFD281 OFD302 OFD605 / 單表主檔四張 / 兩軌對照:ATLAS.OFD 的表多一個 A / OFD220 OFD221 / OTA 綜合帳戶軌 / OFD220A OFD221A / OFD 分戶軌 / OFD251…254 / OTA 軌 / OFD251A…254A / OFD 軌 / 跨模組借用與唯讀 join / BMS999 FSK005 / 表名前綴與歸屬無關 / OFD062 OFD081 OFD303 / 基金公司 基金 結帳控制 / BMS001A OFD601 / TRPM101 寄信名單 / 14 張 TTPxxxTMP / 表名執行期才決定
```

*圖:圖 2 資料模型。橘框=本片維護的主檔;橘虛框=內容是 SQL 文字而不是業務資料的設定表;灰虛框=另一軌或別模組的表;黑框=唯讀 join 或名字在程式裡看不到的表。箭頭=主明細(同一次四眼一起送審);細線=弱關聯。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

| 畫面 | 主檔 | 明細 | 宣告錨點 |
|---|---|---|---|
| `TRPM001` | —(不宣告) | — | PO 沒有 `xTableMapping`,自己組 SQL:`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37` |
| `TRPM005` | `TRPARAMS` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:66` |
| `TRPM101` | —(不宣告) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:42` |
| `TRPM901` | `TRP011`(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:65` |
| `TRPI001` | —(裸 DAO) | — | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:32-34` |
| `TRPR001` | —(SP 結果集) | — | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:31-33` |
| `OTAM901` | `BMS999`〔共用〕 | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:66` |
| `OTAR901` | —(SP 結果集) | — | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OTAR901_PO.cs:24-26` |
| `FSKM004` | `FSK005`〔共用〕 | — | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:39`(舊世代 `TableMapping`,不是 `xTableMapping`) |
| `IJPR611` | —(SP 與長 SQL) | — | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:38` |
| `OFDM109` | `OFD109` | `OFD110` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:78` 與 `:81` |
| `OFDM111` | `OFD111` | `OFD112` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:71` 與 `:74` |
| `OFDM113` | `OFD113` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:69` |
| `OFDM221C` | `OFD220`〔共用〕 | `OFD221`〔共用〕 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:81` 與 `:84` |
| `OFDM231B` | `OFD251` | `OFD252` `OFD253` `OFD254` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:84`、`:87`、`:89`、`:91` |
| `OFDM251` | `OFD281` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:64` |
| `OFDM302B` | `OFD302`〔共用〕(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:47` |
| `OFDM551` | `OFD551` | `OFD552` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:73` 與 `:76` |
| `OFDM554` | `OFD554` | `OFD555` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:91` 與 `:94` |
| `OFDM561` | `OFD561` | `OFD562` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM561_PO.cs:72` 與 `:75` |
| `OFDM602A` | `OFD605`(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:68` |

**注意兩個代號與表名對不上的地方**,讀碼時最容易找錯表:

| 畫面 | 直覺會找的表 | 實際的表 |
|---|---|---|
| `OFDM251` | `OFD251` | **`OFD281`**(`OFD251` 是 `OFDM231B` 的主檔) |
| `OFDM602A` | `OFD602` | **`OFD605`** |

### 2.2 主鍵與四眼欄位

本片 12 張實體表**全部帶四眼欄位**(掃描器實測「四眼欄位 有」)。主鍵從 xsd 的 `msdata:Caption` 與 SQL 條件反推:

| 表 | 主鍵(反推) | 欄位數 | 誰維護 |
|---|---|---|---|
| `TRPARAMS` | `TRP_TYPE` + `PERIOD` | 21 | `TRPM005` |
| `TRP011` | `CAL_YM` + `FH_CD` + `FUND_ID` | 36 | `TRPM901` |
| `BMS999` | `ST_CD` | 18 | `OTAM901` |
| `FSK005` | `STK_BRK` | —(xsd 未列出中文名) | `FSKM004`(已死) |
| `OFD109` | `REMIT_CFM_NO` | 23 | `OFDM109` |
| `OFD110` | `REMIT_CFM_NO` + `DATA_SEQ` | — | `OFDM109` 明細 |
| `OFD111` | `REMIT_CFM_NO` | 22 | `OFDM111` |
| `OFD113` | `BF_NO` + `FUND_ID` + `OMNIBUS_ID` + `APPLY_DATE` + `ALLOT_NO` | 31 | `OFDM113`、`OFDM221C`、`OFDM231B` |
| `OFD220` | `ALLOT_NO` | 39 | `OFDM221C` |
| `OFD251` | `REDEM_NO` | **152** | `OFDM231B` |
| `OFD281` | `FUND_ID` + `RECORD_DATE` | 35 | `OFDM251` |
| `OFD302` | `FUND_ID` + `NAV_DATE` | 44 | `OFDM302B` |
| `OFD551` | `RSP_NO` | 44 | `OFDM551` |
| `OFD554` | `RSP_CHG_NO` | 40 | `OFDM554` |
| `OFD561` | `REMIT_CFM_NO` | 23 | `OFDM561` |
| `OFD605` | `REQ_DOC_KIND` + `DOC_CD` | 23 | `OFDM602A` |

`OFD251` 的 **152 欄**是全片最大的一張表,一筆買回單就把買回、轉換、沖銷、付款、代理人資料全塞在同一列。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列業務欄,四眼 13 欄與 `UPD_USER` / `UPD_DATE` / `UPD_TIME` 全表皆有、皆無 Caption,不重複列。

#### `TRPARAMS` — 申報平台參數(`TRPM005` 主檔)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `TRP_TYPE` | 申報平台種類 | 與 `TRP001.TRP_TYPE` 對應 |
| `PERIOD` | 週期 | `'M'` 為月 |
| `TRP_PARAMS` | 參數 | 實際存的是 `TSCD_RPT_PATH=` 加路徑字串 |

#### `TRP011` — 境外基金月報(`TRPM901` 主檔,36 欄)

| 欄位 | 中文名 |
|---|---|
| `CAL_YM` | 月報年月 |
| `FH_CD` / `FH_NM_SH_C` | 基金公司 / 基金公司名稱 |
| `FUND_ID` / `FUND_SH_NM` | 基金公司 / 基金簡稱(**`FUND_ID` 的 Caption 寫成「基金公司」,與 `FH_CD` 撞名,是 xsd 的筆誤**) |
| `FUND_QUO_AMT` / `FUND_QUO_DATE` | 基金規模 / 基金類股規模日期 |
| `GLOBAL_FUND_QUO_AMT` / `GLOBAL_FUND_QUO_DATE` / `GLOBAL_UNIT` | 基金規模 / 基金規模日期 / 已發行基金單位(股)數 |
| `CAL_RATE1` | 從事衍生性商品交易比率%(Caption 後面接「申報平台1.2版取消此欄位」) |
| `CAL_RATE2` | 基金投資組合投資在國內證券市埸比率% |
| `CAL_RATE3` | 基金投資大陸地區證券市埸有價證券比率% |
| `CAL_RATE4` | 基金投資H股及紅籌股比率% |
| `CAL_RATE5` / `CAL_RATE6` | 從事衍生性商品交易比率% 未沖銷多頭 / 空頭部位 |

`CAL_RATE1` 的 Caption 自己就寫了「申報平台1.2版取消此欄位」——**欄位還在、還會被寫,但申報規格已經不要它了**。

#### `BMS999` — 報表行銷說明(`OTAM901` 主檔,18 欄)

| 欄位 | 中文名 |
|---|---|
| `ST_CD` | 行銷說明代碼 |
| `ST_CD_NM` | 報表行銷說明 |
| `ST_MO` | 附註 |

畫面上的標籤寫「報表行銷說明代碼」,xsd 的 Caption 寫「行銷說明代碼」,兩邊不一致但無害。

#### `OFD109` / `OFD110` — 匯款授權書(`OFDM109`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD109` | `REMIT_CFM_NO` / `BF_NO` / `BF_NAME` / `AUTO_NUM` / `ACC_MEMO` | 授權書編號 / 戶號 / 姓名 / 客戶流水號 / 附註 |
| `OFD110` | `DATA_SEQ` / `BANK_BRH` / `REMIT_ACC_NO` / `BANK_BRH_SHNM` | 資料流水號 / 金資代碼 / 匯款帳號 / 分行簡稱 |

`OFD109.ADU_TYPE` 是必填(不可空)但**沒有 Caption**,畫面上也查不到對應標籤,用途不明。

#### 其餘授權書與契約類(`OFDM111` / `OFDM561` / `OFDM551` / `OFDM554` / `OFDM602A`)

| 表 | 關鍵欄位 | 中文名 |
|---|---|---|
| `OFD111` / `OFD112` | `REMIT_CFM_NO` / `BF_NO` / `AUTHORIZE_DATE` / `EFFECTIVE_DATE` / `TERMINATE_DATE` / `FH_CD` | 授權書編號 / 戶號 / 授權申請日期 / 授權生效日期 / 授權終止日期 / 基金公司代碼 |
| `OFD561` / `OFD562` | `REMIT_CFM_NO` / `BF_NO` / `AUTHORIZE_DATE` / `ACC_NO_TYPE` / `SUB_BANK_CODE` | 授權書號 / 受益人戶號 / 授權申請日 / 帳戶種類 / 扣款行 |
| `OFD551` / `OFD552` | `RSP_NO` / `RCV_DATE` / `TDCC_BF_NO` / `AGENT_ID` / `AGENT_CODE` / `CHANNEL_CD` / `STOP_ID` | 定期定額契約書號 / 收件日期 / 集保帳號 / 銷售機構區別碼 / 銷售機構代碼 / 通路區分碼 / 停扣註記 |
| `OFD554` / `OFD555` | `RSP_CHG_NO` / `RSP_NO` / `RSP_CHG_DATE` / `CHG_EFFECT_DATE` | 契約變更書號 / 契約書號 / 異動收件日期 / 變更生效日期 |
| `OFD605` | `REQ_DOC_KIND` / `DOC_CD` / `DOC_CD_DESC` / `NECESSARY_YN` / `SEAL_YN` | 文件需求種類 / 文件代碼 / 文件名稱 / 是否為必須要文件 / 是否需要核印 |

**`OFD109` 與 `OFD561` 的 Caption 只差一個字**(「授權書編號」對「授權書號」),欄位名完全相同,是兩張不同的表。看到 `REMIT_CFM_NO` 要先確認在講哪一張。

#### 三張交易與行情表(`OFDM221C` / `OFDM231B` / `OFDM251` / `OFDM302B`)

| 表 | 關鍵欄位 | 中文名 |
|---|---|---|
| `OFD220` / `OFD221`(申購,主檔 39 欄) | `ALLOT_NO` / `FH_CD` / `FH_NM_SH_C` / `OMNIBUS_ID` / `CRNCY_CD` / `ALLOT_PROC_CODE` | 申購書號 / 境外基金公司代碼 / 基金公司中文簡稱 / 綜合帳戶註記 / 交易幣別 / 申購處理代碼(`'D'` 為作廢,見 §4.6) |
| `OFD251` 到 `OFD254`(買回,主檔 **152 欄**) | `REDEM_NO` / `REDEM_TYPE` / `RCV_DATE` / `REDEM_DATE` / `REDEM_NAV_DATE` / `BF_NO` / `ID_NO` / `BF_NAME` / `AGENT_ID` | 買回書號 / 買回方式 / 收件日期 / 買回日期 / 買回淨值日期 / 戶號 / 受益人ID / 受益人姓名 / 銷售機區別碼(Caption 少一個「構」字) |
| `OFD281`(配息公告,35 欄) | `FUND_ID` / `FUND_SH_NM` / `RECORD_DATE` / `LAST_CALL_DATE` / `DIVIDEND_DATE` / `RD_POST_DATE` / `PAY_DATE` / `DIVIDEND_TYPE` / `PER_SHARE_CASH` | 基金代碼 / 基金中文簡稱 / 基準日 / 最後交易日期 / 配息日期 / RD入帳日期 / 發放日期 / 受益分配方式代碼 / 每單位數配現 |
| `OFD302`(淨值,44 欄) | `FUND_ID` / `NAV_DATE` / `BID_NAV` / `OFFER_NAV` / `NAV_B` / `NAV_LOCK` / `FUND_QUO_AMT` / `IsCheck` | 基金代碼 / 淨值日期 / 申購淨值 / 贖回淨值 / 正式淨值 / 淨值鎖定碼 / 基金規模 / 勾選(**不是實體欄位,是 SQL 裡 `SELECT 'True' AS IsCheck` 產出來的畫面欄**) |

`OFD251` 的 152 欄是全片最大的一張表,一筆買回單就把買回、轉換、沖銷、付款、代理人資料全塞在同一列。明細三張的用途來自 PO 的 region 名稱:`OFD252` 基金贖回付款檔、`OFD253` 轉換、`OFD254` 基金贖回銷售沖銷檔 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:315`、`:438`、`:584`)。 **注意 `:315` 與 `:438` 兩個 region 的標題都寫「基金贖回付款檔(OFD252)」**,但 `:438` 那段組的是 `OFD253` 的 SQL(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:580`)——複製貼上沒改標題。

### 2.4 與其他模組共用的表

| 表 | 本片誰動它 | 別的模組誰動它 | 風險 |
|---|---|---|---|
| `FSK005` | `FSKM004`(已死) | 共用 PO `BasicFSK_PO.GetStkBrkData` 唯讀(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117-139`),餵 `ucStkBrk` / `ucSTK_BRK_GRP` 等控件 | 維護入口是死的但下游一直在讀,§8.3 |
| `BMS999` | `OTAM901` | 表名前綴是 `BMS`,**但全庫只有 `OTAM901` 碰它** | 命名誤導:看到 `BMS999` 會以為歸 BMS 模組 |
| `OFD220` / `OFD221` | `OFDM221C` 寫;`OFDM109` 讀(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:461`);`OFDM551` 讀(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434`) | 綜合帳戶軌內部共用 | 改欄位要一起看三支 |
| `OFD113` | `OFDM113` 是主維護;`OFDM221C` 與 `OFDM231B` 在 `AfterAdd` / `AfterUpdate` 直接寫它 | — | **三個入口寫同一張表**,§8.2 |
| `OFD302` | `OFDM302B` 寫 | `CLSR002`(結算報表)、`OFDI058` / `OFDI058B`、`OFDB322` / `OFDB323` / `OFDB722`、`OFDI011` 讀 | 淨值是結帳源頭,砍掉重建的風險見 §4.11 |
| `OFD562` | `OFDM561` 寫;`OFDM221C` / `OFDM551` / `OFDM554` 讀扣款帳戶 | — | — |
| `BMS001A` / `OFD601` | `TRPM101` 讀(寄信名單) | BMS / EC 模組維護 | `INNER JOIN` 對不到就靜默不寄信,§6 |

### 2.5 狀態碼(從程式反推,標來源)

#### `OMNIBUS_ID` — 同一個概念,兩套值域

這是本片最容易出錯的地方。

| 表 / 用法 | 值域 | 錨點 |
|---|---|---|
| `OFD221.OMNIBUS_ID`、`OFD081` 檢核參數 | `'Y'` / `'N'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001`;`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:463` |
| `OFD113.OMNIBUS_ID` | `'2'`(綜合)/ `'1'`(分戶) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:249` 的三元式 `(row.OMNIBUS_ID == "Y") ? "2" : "1"` |

也就是說 **`OFD113` 的 `OMNIBUS_ID` 跟 `OFD221` 的不是同一組值**,兩邊要靠 `OFDM221C_PO` 這一行轉換。漏掉這行(例如直接拿 `OFD221.OMNIBUS_ID` 去查 `OFD113`)就會查不到資料,而且不會報錯——`GetOFD113` 的 `catch` 是空的 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224`)。

#### `STATUS` — 本片出現的字面值

`architecture.md §3` 從全庫掃出的 `STATUS = '<x>'` 字面量是單字元,並**假設**那就是 `EVAStatusCode` 的值。本片給這個假設一個反例:`OFDM302B` 與 `TRPM901` 的整批匯入寫進去的是 **三碼的 `'301'`**。

| 值 | 出現處 | 語意(反推) |
|---|---|---|
| `'301'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:209`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282` | 已核准。同一個字面值在 `BMSM006` / `CRMB001` / `OFDB609` 的 INSERT 也用(例 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:726`),都是「直接寫成已生效」的場合 |

**假設**:`'301'` 就是 `EVAStatusCode.ApproveAdd` 的實際字面值,依據是四支不同模組都在「繞過四眼直接寫入」時用它。要確認得反編譯 `Vendor.Product.Utility.MappingCode` 或查 DB。

#### 其他從程式反推的旗標

| 欄位 | 值 | 語意 | 錨點 |
|---|---|---|---|
| `TRP001.FILE_STYLE` | `'T'` | 傳檔(相對於收檔) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594` |
| `TRP001.TRP_TYPE` | `'A'` `'T'` `'R'` | 境外種類,`'R'` 時畫面才顯示基金公司欄位 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:218-221` |
| `TRP001.PERIOD` | `'M'` | 月;其他值走營業日 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:226-229` |
| `TRP001.CSQL_YN1` 到 `CSQL_YN4`、`SQL_YN11` 到 `SQL_YN14`、`SQL_YN_OUT` | `'Y'` | 該段 SQL 要不要跑 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:172-188` |
| `OFD221.ALLOT_PROC_CODE` | `'D'` | 作廢(查詢時排除) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |
| `OFD303.ALLOT_CTL_CODE` / `ALLOT_CTL_CODE_O` | `>= '2'` | 已處理到下單確認之後 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1036` 與 `:1043` |
| `OFD551.STOP_ID` | `'Y'` | 停扣 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| `IJPR611` 的 `PrintType` | `'0'` 到 `'6'` | 七種約定書,**畫面只給得出 `'0'` 到 `'4'`**,見 §7.3 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` |

## 3. 畫面清冊

```text
[圖] 21 支畫面依專案、型別、PO 基底三種分群,以及掃描器會誤判的四處
圖中文字:依專案分(5 個專案) / ATLAS.OTA(15) / TRP 4 + OTA 1 + OFD 10 / ATLAS.OTA.Report(2) / TRPR001 OTAR901 / ATLAS.OTA.Query(1) / TRPI001 / ATLAS.FSK(1) / FSKM004 只有它 / ATLAS.EC.Report(1) / IJPR611 / 依型別分:M 16 / I 1 / R 3 / B 0 / M 維護 16 支 / 其中 2 支行為其實是批次 / I 查詢 1 支 / TRPI001 裸 DAO / R 報表 3 支 / 七層 不是六層 / B 批次 0 支 / 批次能力寫進 M 裡 / 依 PO 基底分(剝註解後判定) / BaseEVADaoPO(11) / 現行主線 走完整四眼 / BaseMultiRowEVADaoPO(3) / TRPM901 OFDM302B OFDM602A / BasicEVAPO(1) / FSKM004 查詢即 NRE / 無基底 裸 DAO(6) / 自建 Database 自管交易 / 掃描器會誤判的三處 / TRPR001 報「缺 PO」 / 檔名少一個 R / OFDM113_PO.cs 是 cp950 / 全片唯一非 UTF-8 / 兩支 rpt 不在 csproj / OFDM302BRPS1 RPS2 / IJPR611 缺 model view / 實際是 _9i 後綴檔 / 在 csproj:21 支的六 / 七層全部都在,只有兩支 rpt 例外 / 21 支 × 六 / 七層 / 全部在 csproj / OFDM302BRPS1 RPS2 / 沒有 csproj 的資料夾 / UI 用名字去要它們 / OFDM302B.cs:342 :396
```

*圖:圖 3 清冊分群。橘框=主線;橘虛框=死路徑、誤判來源或會咬人的地方。判斷一支畫面死活的第一個依據是 PO 基底 —— 繼承 BasicEVAPO 的那一支,連按查詢都會 NRE。*

四欄要特別說明:

- **六層齊不齊**:掃描器的判定。「假缺」表示檔案在、只是檔名不照慣例,見註。

- **PO 基底**:判斷前**已剝掉 `//` 註解**(`atlas_scan.strip_cs_comments`),避免被註解行誤導。這是判斷一支畫面死活的第一個依據(`architecture.md §3`)。

- **在 csproj**:該畫面的六 / 七層檔案是否都被對應的 `.csproj` 以 `Compile` / `EmbeddedResource` 收錄。

- **專案與型別**:本片跨四個專案、三種型別,不看這欄會找錯檔。

### 3.1 維護 M(16 支)

| 代號 | 中文名(待選單表) | 專案 | 六層 | 主表 | 明細 | SP / Fn | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|---|
| `TRPM001` | 集保申報平台傳檔 | `ATLAS.OTA` | 齊 | —(`TRP001` 設定驅動) | — | — | **無基底**(`ITRPM001_PO`,自建 `Database`) | 是 |
| `TRPM005` | 申報平台參數維護 | `ATLAS.OTA` | 齊 | `TRPARAMS` | — | — | `BaseEVADaoPO` | 是 |
| `TRPM101` | 集保申報平台收檔 | `ATLAS.OTA` | 齊 | —(`TRP001`/`TR202`/`TR206`/`TR207` 設定驅動) | — | `S_OTA_<表名>_GET`(動態組名) | **無基底**(`ITRPM101_PO`,自建 `Database`) | 是 |
| `TRPM901` | 境外基金月報維護 | `ATLAS.OTA` | 齊 | `TRP011` | — | `S_OTA_TRPM901_EXE` | `BaseMultiRowEVADaoPO` | 是 |
| `OTAM901` | 報表行銷說明代碼維護 | `ATLAS.OTA` | 齊 | `BMS999` | — | — | `BaseEVADaoPO` | 是 |
| `FSKM004` | 證券經紀商基本資料維護 | `ATLAS.FSK` | 齊 | `FSK005` | — | — | **`BasicEVAPO`**(死路徑) | 是 |
| `OFDM109` | 匯款授權書維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD109` | `OFD110` | — | `BaseEVADaoPO` | 是 |
| `OFDM111` | 授權期間維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD111` | `OFD112` | view `FNDV01` | `BaseEVADaoPO` | 是 |
| `OFDM113` | 受益人基金配息設定維護 | `ATLAS.OTA` | 齊 | `OFD113` | — | — | `BaseEVADaoPO` | 是(**來源檔是 cp950,非 UTF-8**) |
| `OFDM221C` | 境外基金申購維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD220` | `OFD221` | — | `BaseEVADaoPO` | 是 |
| `OFDM231B` | 境外基金買回 / 轉換維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD251` | `OFD252` `OFD253` `OFD254` | `S_OTA_OFDM231B_EXE_ADD` `S_OTA_OFDM231B_EXE_MOD` `S_TA_IMP_OFD300_RANGE` | `BaseEVADaoPO` | 是 |
| `OFDM251` | 基金配息公告維護 | `ATLAS.OTA` | 齊 | `OFD281` | — | — | `BaseEVADaoPO` | 是 |
| `OFDM302B` | 境外基金淨值維護與鎖定 | `ATLAS.OTA` | 齊 | `OFD302` | — | — | `BaseMultiRowEVADaoPO` | 六層是;**兩支 `.rpt` 不在任何 csproj**,見註 2 |
| `OFDM551` | 定期定額契約維護 | `ATLAS.OTA` | 齊 | `OFD551` | `OFD552` | `S_OTA_OFDR552_GET` | `BaseEVADaoPO` | 是 |
| `OFDM554` | 定期定額契約變更維護 | `ATLAS.OTA` | 齊 | `OFD554` | `OFD555` | — | `BaseEVADaoPO` | 是 |
| `OFDM561` | 扣款授權書維護 | `ATLAS.OTA` | 齊 | `OFD561` | `OFD562` | — | `BaseEVADaoPO` | 是 |
| `OFDM602A` | 文件需求設定維護 | `ATLAS.OTA` | 齊 | `OFD605` | — | — | `BaseMultiRowEVADaoPO` | 是 |

### 3.2 查詢 I(1 支)

| 代號 | 中文名(待選單表) | 專案 | 六層 | 主表 | SP / Fn | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `TRPI001` | 集保傳收檔紀錄查詢 | `ATLAS.OTA.Query` | 齊 | —(`TRP002` + `TRP001`) | — | **無基底**(`ITRPI001_PO`,自建 `Database`) | 是 |

`TRPI001` 的 PO 檔名是 `TRPI001_PO.cs`,**不是** `.Query` 專案常見的 `<代號>OracleDao.cs`(`architecture.md §2` 列的例外之一)。另外層資料夾叫 `QueryPO.OFD` / `QueryUI.OFD`(前綴是 `OFD`),組件名卻是 `QueryPO.OTA`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/QueryPO.OTA.csproj`)——資料夾名與專案名不一致,是 `architecture.md §2` 記的第 3 類例外。

### 3.3 批次 B(0 支)

本片沒有 B 型畫面,原因見 §6。

### 3.4 報表 R(3 支,七層)

R 是七層不是六層(`architecture.md §6`):六層各自加 `Report` 前綴,再多一個 `Report.<模組>` 專案放 `.rpt`。

| 代號 | 中文名(來自程式字串) | 專案 | 七層 | 取數來源 | `.rpt` | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `TRPR001` | 境外基金月報 | `ATLAS.OTA.Report` | **掃描器報「PO 缺」,實際是檔名錯**,見註 1 | `S_OTA_TRPR001_GET` | `TRPR001RPS1.rpt` | **無基底**(`ITRPR001_PO`,自建 `Database`) | 是(以錯誤檔名收錄) |
| `OTAR901` | 弱勢族群交易回訪報表(境外) | `ATLAS.OTA.Report` | 齊 | `S_OTA_OTAR901_GET`(版控外) | `OTAR901RPS1.rpt` | **無基底**(`IOTAR901_PO`,自建 `Database`) | 是 |
| `IJPR611` | 電子交易約定書(七式) | `ATLAS.EC.Report` | 缺 `DataEntity` / `UIEntity` 的標準檔名(實際是 `_9i` 後綴檔) | Dao 內七段長 SQL | `IJPR611RPS1` 到 `IJPR611RPS7`,共 7 支 | **無基底**(`IIJPR611PO`,自建 `Database`) | 是 |

### 3.5 兩個「掃描器說缺、其實不缺」的註

**註 1:`TRPR001` 的 PO 檔名少了一個 `R`。**

`TRPR001_Ctl` 在 `:29` 與 `:36` 用 `TRPR001_PO` / `ITRPR001_PO`,而這個類別住在 **`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs`**(檔名 `TRP001_PO.cs`,類別 `TRPR001_PO`,`:31`)。檔頭的註解自己還寫著 `TRPR001_PO.cs`(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:2`),所以是存檔時打錯。 csproj 以錯的檔名收錄(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/ReportPO.OTA.csproj:141`), **C# 不在乎檔名,所以編得過、跑得動**,只有依檔名比對的工具(本專案的掃描器就是)會判它缺 PO。

**註 2:`OFDM302B` 有兩支 `.rpt` 躺在專案裡但不在任何 csproj。**

`Dev/ATLAS.OTA/Source/CrystalReports/OFDM302BRPS1.rpt` 與 `Dev/ATLAS.OTA/Source/CrystalReports/OFDM302BRPS2.rpt` 在一個**沒有 csproj 的資料夾**裡(`Dev/ATLAS.OTA/Source/CrystalReports/` 底下只有這兩個檔)。 `OFDM302B.cs` 卻用名字去要它們(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:342` 與 `:396`)。依 `architecture.md §6`,`.rpt` 的另一條交付路徑是 csproj 的 PostBuildEvent xcopy 到框架目錄—— 這兩支**兩條路徑都沒有**(既不是 `EmbeddedResource`,也沒有 xcopy)。 **推論:`OFDM302B` 的兩張報表在目前的建置流程下不會被部署,除非有人手動複製。**這是本片唯一的「檔案存在但不在 csproj」。

### 3.6 一眼看出差別的五件事

| # | 事實 | 為什麼重要 |
|---|---|---|
| 1 | **21 支裡有 6 支的 PO 沒有任何基底類別**(`TRPM001` `TRPM101` `TRPI001` `TRPR001` `OTAR901` `IJPR611`) | 它們自建 `Database`、自管交易,不受四眼、連線池與框架治理(與 `architecture.md §6` 對 I / B / R 的描述一致) |
| 2 | **只有 1 支繼承 `BasicEVAPO`**(`FSKM004`) | 依 `architecture.md §3` 是死路徑,連查詢都會 NRE |
| 3 | **3 支繼承 `BaseMultiRowEVADaoPO`**(`TRPM901` `OFDM302B` `OFDM602A`) | 多筆主檔、沒有明細概念;其中 `TRPM901` 與 `OFDM302B` 另外有繞過四眼的 `BatchAdd`,`OFDM602A` 沒有 |
| 4 | **11 支繼承 `BaseEVADaoPO`** | 現行主線,走完整四眼 |
| 5 | **21 支的六 / 七層檔案全部在 csproj 內**,唯一的例外是 `OFDM302B` 的兩支 `.rpt` | 與 `ofd` 系列前幾片查到的「整支畫面不在 csproj」不同,本片沒有那種情況 |

PO 基底的逐支對照與統計見附錄 D。

## 4. 維護畫面(M)— 一支一節

```text
[圖] TRP 六支的完整鏈:設定表驅動的傳檔與收檔、紀錄查詢、月報與報表
圖中文字:① 設定(規則不在程式裡,在這兩張表) / TRPM005 / 維護落地路徑 TRPARAMS / TRP001〔DB 維護〕 / CHECK_SQL1-4 SQL11-14 SQL_OUT / TR202 TR206 TR207 / 收檔 INSERT 語法與 SP 名 / ② 傳檔 TRPM001:檢核 → 產檔 → 記錄 / Select 取設定 / 硬鎖 TRP_TYPE A T R / Execute 跑 4 段檢核 SQL / 空 catch → 出錯視同無誤 / ExcuteSQLandLoadData / 跑異動 SQL + 取 CSV 列 / 用戶端 StreamWriter / Encoding.Default 每列多一個 tab / UpdateTRP002 / 只在筆數不為 0 時寫 / ③ 收檔 TRPM101:六道欄位檢核 → 暫存表 → SP 入帳 / GetTRP001 GetTR206 / 取媒體格式與欄位對照 / 逐欄六道檢核 / 未定義欄位在第 2 筆以後會炸 / TR202.INSERTSQL / 三層 REPLACE 反跳脫 / Execute 不帶 tran / rollback 收不回 / S_OTA_<表名>_GET / 14 支 由 TRP001 決定 / TR207.UPDSTP 入帳 / 名字在程式裡看不到 / TTP12A → OFDM053_PO / 寄信 代碼 07 兩個 INNER JOIN / ④ 查與報 / TRPI001 查 TRP002 / FILE_STYLE 送了沒用 / INNER JOIN TRP001 / 設定刪了歷史就消失 / TRPM901 月報 / BatchAdd 繞四眼 STATUS 301 / TRPR001 報表 / S_OTA_TRPR001_GET
```

*圖:圖 4 TRP CRUD 鏈。橘框=程式;橘虛框=規則存在資料表裡、或會咬人的實作;黑框=名字在執行期才決定的 SP。整條鏈最關鍵的一點:傳檔與收檔的商業規則都不在程式裡,讀 code 讀不出任何一條檢核。*

節首的圖見 §1.1 與 §3 的分群圖。深寫的六支是:`TRPM001` / `TRPM101`(本片唯一完整 CRUD 鏈的核心)、`FSKM004`(唯一死畫面)、 `OFDM221C` / `OFDM231B`(最重的兩支)、`OFDM302B`(唯一繞過四眼寫主檔的)。其餘表格帶過。

### 4.1 `TRPM001` — 集保申報平台傳檔

#### 用途(推測)

依申報平台種類與週期,把 TA 的資料依 `TRP001` 設定的 SQL 撈出來,逐筆組成一行 CSV, 寫到 `TRPARAMS` 設定的路徑,並把傳檔筆數記進 `TRP002`。

#### 這支畫面的型別是假的

代號第 4 碼是 `M`(維護),但 UI 繼承的是 `xOneStepProcessForm` (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:30`),那是 `architecture.md §6` 歸給 I / B 的基底; PO 沒有任何基底、自己 `new Database("TA", DbServerType.Oracle)`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37`)。 **它的行為完全是 B 批次,只是掛了 M 的代號。**同樣的話適用 `TRPM101`。

#### 規則從哪來:`TRP001` 一列就是一支程式

`Select` 組的 SQL 把 `TRP001` 整列讀出來,包含 13 個 SQL 文字欄位 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582`):

| 欄位群 | 用途 | 誰執行 |
|---|---|---|
| `CSQL_YN1` 到 `CSQL_YN4` + `CHECK_SQL1` 到 `CHECK_SQL4` + `CHECK_MSG1` 到 `CHECK_MSG4` | 傳檔前檢核。SQL 查出有列就算「有錯」,把 `CHECK_MSGn` 顯示到畫面 | `Execute`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:435-506`) |
| `SQL_YN11` 到 `SQL_YN14` + `SQL11` 到 `SQL14` | 傳檔時要跑的異動 SQL(標記已傳等) | `ExcuteSQLandLoadData`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:144-207`) |
| `SQL_YN_OUT` + `SQL_OUT` | 產出 CSV 內容的 SELECT | `GetCSVData`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:217-286`) |
| `FILE_ID` / `FILE_NAME` / `MEDIA_NO` | 檔名與媒體代號 | UI 端組檔名 |

參數綁定是「掃字串決定要不要綁」:`if (strSQL.IndexOf(":TRANS_DATE") > 0) AddInParameter(...)` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:309-322`)。 **注意用的是 `> 0` 不是 `>= 0`**——如果哪天有人把 SQL 寫成以 `:TRANS_DATE` 開頭(索引 0),參數就不會綁,Oracle 直接丟「未繫結變數」。目前的寫法都有 `WHERE` 開頭所以踩不到,但這是一顆未爆彈。

#### 查詢:下一次該傳哪一天

`Select` 用 `TRP002` 的最後一次傳檔日推出本次日期(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:541-556`):

| `PERIOD` | 沒傳過 | 傳過 |
|---|---|---|
| `'M'` | `TO_CHAR(SYSDATE,'YYYYMM')` | 上次年月 `ADD_MONTHS(+1)` |
| 其他 | `TA_GETBUSINESSDAY(NULL, 1)` | `TA_GETBUSINESSDAY(上次日期, 1)` |

兩個寫死的硬條件:`TRP_TYPE IN ('A','T','R')`(`:547` 與 `:593`,註解寫「只處理境外種類」)與 `FILE_STYLE = 'T'`(`:594`)。 **過濾(無提示)**:`TRP001` 裡種類不在這三個值、或 `FILE_STYLE` 不是 `'T'` 的設定列,在這支畫面永遠看不到,也不會有任何訊息。

#### 執行:檢核 → 產檔 → 記錄

`DoProxyExecute` 的順序(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:290-339`):

1. 呼叫 `FormProxy.Execute` 跑伺服器端的四段檢核 SQL。

2. 只有在 `Result[0].ReturnCode == true` **且**回傳列數 > 0 時才往下走(`:311-313`)——**阻擋**。

3. `ConvertToCSV()` 逐列產檔(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:343-425`)。

4. 產檔成功開 `TRPM001p1` 顯示筆數;失敗把結果改成「執行失敗」。

檔名與路徑的組法(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356-380`):

| 項目 | 規則 | 備註 |
|---|---|---|
| 路徑 | `row.FILE_PATH.Replace("TSCD_RPT_PATH=", "")` | 值來自 `TRPARAMS`,由 `TRPM005` 維護 |
| 路徑預設 | 空字串時用 `C:\境外傳檔\` | **寫死**〔客戶特定〕(`:358-360`) |
| SQL 端預設 | `NVL(B.TRP_PARAMS, 'C:\')` | **第二個寫死的預設值,而且與 UI 端不同**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:584`) |
| 自動建資料夾 | `Directory.CreateDirectory` | 沒有例外處理以外的保護,建不出來就整批失敗 |
| 檔名 | `FILE_ID` + `_` + `FH_CD`(有才加)+ `_` + 傳檔日 | **沒有副檔名** |

寫檔本身(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527-539`):

- `new StreamWriter(strFileName, false, Encoding.Default)` ——**用作業系統預設編碼**(繁中 Windows 是 CP950)。換一台 UTF-8 locale 的機器產出的檔就不一樣。〔客戶特定〕

- 每一列後面都多接一個定位字元:`sb.Append(dr["RowData"].ToString() + "\t")`(`:534`)。集保規格要不要這個 tab,程式裡看不出來。

- 逗號處理在伺服器端:除了 `RESERVE_FIELD_SW` 這個欄名以外,所有值裡的半形逗號都被換成全形(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:259-264`)。**欄名寫死在程式裡**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | `validatorManager1` 必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:138-141` |
| 查詢 SQL | `TRP_TYPE IN ('A','T','R')` 且 `FILE_STYLE='T'` | 不符 | **過濾(無提示)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593-594` |
| 查詢後 | 查無資料 | 0 筆 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:609` |
| 按執行前 | 傳檔日期不可空白 | 空 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:166-169` |
| 按執行前 | 至少勾一筆明細 | 全不勾 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:171-175` |
| 執行 | `TRP001` 設定的四段檢核 SQL 查出資料 | 有列 | **阻擋**(訊息寫到格子的 `CHECK_ERRMSGn` 欄) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:450-490` |
| 執行 | 檢核 SQL 本身出錯 | 例外 | **記錄不擋 → 實際上是放行**,見附錄 E.1 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:418-420` |
| 產檔 | `ExcuteSQLandLoadData` 回傳失敗 | `ReturnCode=false` | 阻擋(丟例外,被 `ConvertToCSV` 的 `catch` 轉成對話框) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:512-516` |
| 產檔 | 沒有 CSV 資料 | 0 列 | **記錄不擋**(回 0,該列標「無資料」,不寫 `TRP002`) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:518-523`、`:399-407` |
| 記錄 | `UpdateTRP002` 失敗 | `ReturnCode=false` | 阻擋(丟 `ArgumentNullException`) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:458-462` |

### 4.2 `TRPM101` — 集保申報平台收檔

#### 用途(推測)

把集保回來的媒體檔(逗號分隔文字)讀進畫面,依 `TRP001` / `TR206` 設定逐欄檢核格式, 通過的寫進暫存表,再叫 `TR207` 指定的 SP 正式入帳;`TTP12A` 這一種還會寄信給受益人。

#### 四張設定表各管什麼

| 表 | 取法 | 內容 |
|---|---|---|
| `TRP001` | `GetTRP001`(依 `MEDIA_NO`) | `CheckSQL`(欄位名與數量)、`StartLine`(資料從第幾行開始)、`NullFieldList`、`DateFieldList`、`TableName`(收檔媒體格式的表名) |
| `TR206` | `GetTR206`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:822-855`) | 寫入暫存檔的欄位對照 `TABLE_FIELD_NAME` 與 `IS_NUMBER` |
| `TR202` | `GetTR202`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:858-893`) | `INSERTSQL` —— **整段 INSERT 語法存在欄位裡**,取出時還要用三層 `REPLACE` 把 `'[` `]'` 拿掉、把 `&` 換成 `:` |
| `TR207` | `GetTR207`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:787-820`) | `QUERYSTP` / `UPDSTP` —— 查詢與入帳用的 SP 名稱 |

`REPLACE(REPLACE(REPLACE(TR202.INSERTSQL, CHR(39)||CHR(91), ''), CHR(93)||CHR(39), ''), CHR(38), ':')` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:868`)——SQL 被以某種跳脫格式存在表裡,取出時反轉。 **改這張表的人必須知道這套跳脫規則,程式裡沒有任何說明。**

另外表 schema 也是查出來的:`GetTableSchema` 去 Oracle 的資料字典取 `COLUMN_NAME` / `DATA_TYPE` / `DATA_LENGTH` / `DATA_SCALE` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:930-980`),再拿來判每一欄的長度與型別。

#### 逐欄檢核的六道

`Execute` 的主迴圈(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:216-368`):

| # | 檢核 | 成立時 |
|---|---|---|
| 1 | 欄位個數 = `CheckSQL` 查出的欄數 | 不等 → 記錯誤 |
| 2 | 欄名含 `DUMMY` → 整欄跳過 | — |
| 3 | 欄位要定義在收檔媒體格式表的 schema 內 | 沒定義 → 記錯誤(**只檢查第一筆**,見下) |
| 4 | 長度不得超過該欄的 `DATA_LENGTH`(有小數再加 1) | 超過 → 記錯誤 |
| 5 | `DATA_TYPE = 'NUMBER'` 的欄要能 `decimal.TryParse` | 不能 → 記錯誤 |
| 6 | 在 `DateFieldList` 內的欄要能解析成日期(先試 `yyyy/` 或 `yyyy-`,不行再用 `Substring` 切 `yyyy/mm/dd`) | 不能 → 記錯誤 |

**第 3 道有一個會炸的洞。**條件寫成 `if (Schemarow.Length == 0 && intRow == 1)` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:248`),`continue` 在 `if` 內(`:253`)。第 2 筆以後若出現未定義欄位,`Schemarow.Length == 0` 但 `intRow != 1`,程式直接往下走到 `Schemarow[0]["COLUMN_CNAME"]`(`:267`)→ `IndexOutOfRangeException`,被最外層的 `catch` 吃掉、只回「例外錯誤, 請檢查」(`:507-512`)。第 6 道的 `Substring(0,4)`/`(4,2)`/`(6,2)` 對長度不足 8 的字串也會直接丟例外(`:329`),同樣被吃成「例外錯誤」。

#### 寫暫存表與入帳

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 產一把 `Guid` 當 `ONLY_KEY` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:433` |
| 2 | 逐列用 `TR202.INSERTSQL` 寫暫存表,參數名就是 `TR206` 給的欄名 | `:442-467` |
| 3 | 叫 `S_OTA_<收檔表名>_GET` 取回正確 / 錯誤兩個結果集 | `:752-785` |
| 4 | (`ImportData` 才有)叫 `TR207.UPDSTP` 正式入帳,參數 `XDATALIST='DEF'`、`XONLY_KEY` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:659-665` |

**這裡有一個真的交易缺口。**`Execute` 在 `:435` 開了 `tran`,失敗時 `tran.Rollback()`, 但第 2 步的寫入用的是 `dbTA.ExecuteNonQuery(cmd)`——**沒有把 `tran` 傳進去**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459`)。對照 `ImportData` 的同一段是 `dbTA.ExecuteNonQuery(cmd, tran)`(`:646`)。也就是說 **`Execute` 寫進暫存表的資料不在交易內,rollback 收不回來**。

#### 寄信:跨模組、寫死兩個常數

`ImportData` 在媒體代號等於 `TTP12A` 時,`new` 一個 `OFDM053_PO` 去寄信 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687`):

| 寫死的值 | 位置 | 意義 |
|---|---|---|
| `"TTP12A"` | `:670` | 核印收檔的媒體代號〔客戶特定〕 |
| `"07"`(兩處) | `:683`(傳給 `SEND_MAIL_PROC`)與 `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:729`(SQL 的 `EMAIL_CODE_EC = '07'`) | 信件代碼〔客戶特定〕 |

名單 SQL 是 `TRPM101T1`(暫存表)`INNER JOIN BMS001A INNER JOIN OFD601`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729`)。 **兩個 `INNER JOIN` 表示只要受益人不在 `BMS001A` 或沒有 `OFD601` 的 `BF_SRNO`,這個人就不會收到信,而且沒有任何提示。** 更糟的是 `GetMailData` 的 `catch` 是空的(`:742-744`),SQL 出錯回 0,程式當成「沒人要寄」繼續往下 commit。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 收檔內容不可空 | 0 列 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:141-144` |
| 執行前 | 取得 `MEDIA_NO` | 空 | 阻擋 | `:146-152` |
| 執行前 | 取得 `TRP001` 設定 | 0 筆 | 阻擋 | `:159-165` |
| 執行前 | 取得檢核欄位(`CheckSQL`) | 0 欄 | 阻擋 | `:177-182` |
| 執行前 | 找得到收檔媒體格式的 schema | 0 筆 | 阻擋 | `:190-195` |
| 執行前 | 取得 `TR206` 欄位對照 | 0 筆 | 阻擋 | `:198-204` |
| 逐列 | 六道欄位檢核(見上) | 任一不過 | 阻擋(整批不寫) | `:212-368` |
| 逐列 | 未定義欄位出現在第 2 筆以後 | — | **例外**(訊息變成「例外錯誤, 請檢查」) | `:248` 配 `:267` |
| 寫入前 | 有可收的資料列 | 0 列 | 阻擋 | `:374-378` |
| 寫入前 | `TR202.INSERTSQL` / `TR207.QUERYSTP` 取得到 | 空 | 阻擋 | `:394-418` |
| 寫入 | 每列 `ExecuteNonQuery` 影響列數 | 0 | 阻擋 + rollback(**但寫入本身不在交易內**) | `:461-467` |
| 寫入後 | 例外 | 有 | **記錄不擋 → 被後面的 `if (i > 0)` 覆蓋成「檢核成功」**,見附錄 E.1 | `:478-484` 配 `:494-505` |
| 入帳 | 媒體代號 `TTP12A` | 是 | 記錄不擋(寄信) | `:669-687` |

### 4.3 `TRPM005` — 申報平台參數維護

`TRPARAMS` 的單表四眼維護,整支只有 180 行,是本片最單純的一支。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `TRPARAMS`(`TRP_TYPE` + `PERIOD`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:66` |
| 查詢硬條件 | `TRP_TYPE IN ('A','T','R')`,註解「只處理境外種類」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:141` |
| 顯示時剝前綴 | SQL 直接 `REPLACE(TRP_PARAMS, 'TSCD_RPT_PATH=', '')` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:137` |
| 存檔時加前綴 | `MasterRow.TRP_PARAMS = "TSCD_RPT_PATH=" + 輸入值` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192` |
| 自訂檢核 | **沒有**。`DoValidate()` 只叫框架的 `DataValidate()` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:143-148` |

**`TSCD_RPT_PATH=` 這個前綴在三個地方各寫一次**(PO 的 SELECT、UI 的存檔、`TRPM001` 的讀取), 三處任一改了字面值,另外兩處就對不上,而且不會報錯——`TRPM001` 只是 `Replace` 不到,拿到整串含前綴的字串當路徑,`Directory.CreateDirectory` 直接丟例外。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:108-119` 與 `:124-130` |
| 查詢 | `TRP_TYPE IN ('A','T','R')` | 不符 | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:141` |

### 4.4 `TRPM901` — 境外基金月報維護

`TRP011` 的多筆主檔維護,加兩個自訂鈕:「整批匯入」(`DoExp1` → `TRPM901p0`)與「月報製作」(`DoExp2` → `TRPM901p1`) (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:490-515`)。

| 功能 | 做什麼 | 錨點 |
|---|---|---|
| 查詢 | 依 `CAL_YM` + `FH_CD`;沒給 `CAL_YM` 時用 `MAX(CAL_YM) KEEP(DENSE_RANK FIRST ORDER BY ROWID DESC)` 取最後一期 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:83-104` |
| 取基金代碼 | 依 `ISIN_CODE` 查 `OFD081` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:206-245` |
| 整批匯入 | `BatchAdd`:先 `DELETE TRP011 WHERE CAL_YM=? AND FH_CD=?`,再逐列 INSERT,`STATUS` 寫死 `'301'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282` |
| 月報製作 | 叫 `S_OTA_TRPM901_EXE`,傳 `iFH_CD` / `iCAL_YM` / `iUPD_USER` / `iUPD_DATE` / `iUPD_TIME` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:355-367` |

三個要注意的地方:

1. **「不開放刪除」的檢核整段被註解。**`TRPM901_BeforeDeleteButtonClicked` 只剩註解,訊息字串「不開放刪除功能, 請使用修改方式調整資料庫」還在 (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231`)。**現在刪除是開放的。**

2. **`BatchAdd` 的刪除檢核是死的。**`if (i == -1)` 判 `ExecuteNonQuery` 的回傳(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271`), 而 `ExecuteNonQuery` 回的是影響列數,**永遠不會是 -1**。刪 0 筆與刪 500 筆都會通過。

3. **整批匯入完全繞過四眼**:`STATUS='301'`、`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全部塞同一個 `:USERID`、同一個 `SYSDATE` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282`)。**一個人匯入等於一個人送審加覆核加核准。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:205-218` 與 `:233-246` |
| 刪除前 | (原本要擋刪除,**已被註解**) | — | **不擋** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231` |
| 整批匯入 | 刪除影響列數 `== -1` | 永不成立 | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271-276` |
| 整批匯入 | 每列 INSERT 影響列數 `== 0` | 是 | 阻擋 + rollback | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:312-318` |

### 4.5 `FSKM004` — 證券經紀商基本資料維護(**死畫面**)

#### 為什麼說它是死的

| # | 事實 | 錨點 |
|---|---|---|
| 1 | `FSKM004_PO : BasicEVAPO`(**剝掉註解後確認,活的宣告只有這一行**) | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29` |
| 2 | 依 `architecture.md §3`,`BasicEVAPO.dbTA` 宣告即 `= null`,建構子建立連線那四行整段被註解 | `architecture.md §3` |
| 3 | 本支的 `BeforeSelect` 第一件事就是 `dbTA.GetSqlStringCommand(strSQL)` | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:60` |
| 4 | `BeforeGetMaintainData` / `BeforeGetToDoData` 同樣第一行就用 `dbTA` | `:73` 與 `:85` |
| 5 | `CheckStkBrkData` / `CheckDelete` 一開頭就 `dbTA.CreateConnection()` | `:102` 與 `:269` |
| 6 | 本支**不覆寫** `Add` / `Update` / `Delete`,直接吃基底 | 全檔剝註解後只有 `CheckStkBrkData` / `CheckDelete` / `BuildMasterSQLString` 三個方法 |

**推得:按查詢就 NRE,不是存檔才 NRE。**這與 `ofd6.md` 對同型畫面的結論一致。

#### 一半以上的檔案是註解

1,272 行裡,`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270` 是一個 `#region 註解` 包著的 `/* public class FSKM004_PO : Basic_PO { ... } */`——**上一代的完整實作**,包含 `AddSTK_BRK_Data` / `UpdateSTK_BRK_Data` / `DeleteSTK_BRK_Data` / `EVASTK_BRK_Data` / `ApproveDeleteSTK_BRK_Data` 等 14 個方法。那段裡看得到 SQL Server 時代的痕跡:`SELECT * FROM [FSK005]`(方括號)、`UpdateID <> '" + LoginUser + "'`(字串串接) (`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:889`)。

**活的那 320 行裡也還有 T-SQL。**`CheckStkBrkData` 用的是 `SUBSTRING(AGENT_CODE,2,4)` (`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:114`)——Oracle 沒有 `SUBSTRING`,只有 `SUBSTR`。 **就算 `dbTA` 有連線,這段 SQL 在 Oracle 上也會語法錯誤。**這是第二條「它沒在跑」的旁證。

檔案最後一行是 `}//end namespace Adapterusing System;`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:1272`)—— 兩段文字被黏在一起,顯示這個檔曾經被截斷或貼壞過。

#### Ctl 層也不照慣例

`FSKM004_Ctl` **沒有繼承 `BaseController`**(`Dev/ATLAS.FSK/Source/Control/Control.FSK/FSKM004_Ctl.cs:13`), 每個方法自己 `new FSKM004_PO()`(例 `:37-39`),不走 `DataAccessPool`、沒有 `InitializeVDBTypes()`。這是 `architecture.md §2` 說的六層職責的完全例外,全片只有這一支這樣寫。

#### 兩個檢核的回傳值語意是反的

| 方法 | 回 `ReturnCode = true` 代表 | 呼叫端怎麼用 |
|---|---|---|
| `CheckDelete` | **有分公司資料,不可刪** | `if (... == true) AddError(...)`(`Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:257-261`) |
| `CheckStkBrkData` | **已建立銷售機構資料,不可刪** | `if (... ReturnCode) AddError(...)`(`Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:268-274`) |

兩邊一致,所以行為是對的;但 `true = 有問題` 與全庫其他地方的 `true = 成功` 相反,改的時候很容易反過來。而且 `CheckStkBrkData` 的 `catch` 把結果設成 `AddResultRow(false, 0, "")`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186`) ——**SQL 出錯等於「沒問題,可以刪」**,是 fail-open。

#### 誰在用 `FSK005`

維護畫面死了,表卻活著。共用 PO `BasicFSK_PO.GetStkBrkData` 直接讀 `FSK005` (`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117` 與 `:139`),餵給自訂控件 `ucStkBrk` / `ucSTK_BRK_GRP`, 再被 `BMSM001` / `BMSM006` / `NFDR433` / `NFDR435` / `OFDM231Ap1` / `OFDM243` / `OFDM243A` / `OFDM385` / `OFDB331p0` 等畫面用。另外 `OFDM068_PO` / `OFDM221A_PO` / `OFDM243A_PO` / `OFDB310_PO` 與 view `OFD068A_V02` 也直接 join 它。

**推論:`FSK005` 的資料只能靠 DB 直改或別的匯入途徑維護,`FSKM004` 這個入口已經沒在用。** 這是讀碼結論,沒有實跑過;要推翻它得證明 `BasicEVAPO.dbTA` 在別處被賦值(`architecture.md §3` 已經掃過,沒有)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 任何查詢 | (無)——`BeforeSelect` 直接 NRE | 一定 | **整支不可用** | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:60` |
| 刪除前 | 有分公司(`STK_BRK_GRP` 指向本代碼)不可刪 | 有 | 阻擋 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:257-261` |
| 刪除前 | 已在 `OFD068` 建立銷售機構不可刪(限總券商) | 有 | 阻擋 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:264-275` |
| 刪除前 | 上述檢核的 SQL 出錯 | 例外 | **記錄不擋(fail-open)** | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186` |

### 4.6 `OFDM221C` — 境外基金申購維護(綜合帳戶軌)

#### 用途(推測)

建立與維護境外基金的申購單:主檔 `OFD220` 一張申購書、明細 `OFD221` 一到多筆基金申購明細。走完整四眼,是本片第二大的一支(PO 1,086 行)。

#### 申購書號怎麼來

`BeforeAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:144-177`):

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | `GetTradeId(row.FH_CD)` 去 `OFD062` 取 `TRADE_ID`,取不到回 `'X'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:930-960` |
| 2 | `'X'` 或空字串 → 丟例外「TradeId(OFD062)」——**阻擋** | `:156-157` |
| 3 | `new SerialNo(args.DbTranPTPF, dbPTPF)`,序號類別是 `"OFD220" + TradeId` | `:160-164` |
| 4 | `genSrNo.GetSrIdNoForOTA(strSrId)` 取號 | `:165` |
| 5 | `do { 取號 } while (IsExistByData(...))` —— 撞號就重取,**沒有次數上限** | `:162-167` |
| 6 | 把 `ALLOT_NO` 與 `BF_NO` 回填到每一筆明細 | `:170-174` |

第 5 步的無上限重試與 `architecture.md §3` 記的 `CASM001_PO` 是同一個模式,同樣有無窮迴圈風險。第 4 步的 `GetSrIdNoForOTA`(無原始碼,從呼叫端反推)是 **OTA 軌專用的取號進入點**,`ATLAS.OFD` 那邊用的是別的多載。

#### 存檔後同步 `OFD113`:繞過四眼寫另一張主檔

`AfterAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:237-307`)與 `AfterUpdate`(`:314-440`)對每一筆有 `DIVIDEND_ID` 的明細做同一件事:

1. 把 `OMNIBUS_ID` 從 `'Y'/'N'` 轉成 `'2'/'1'`(`:249`,`AfterUpdate` 在 `:326`)。

2. 用 `GetOFD113` 查現有設定(`:184-228`)。

3. 沒有 → INSERT;有但 `DIVIDEND_ID` 或 `SHARE_DIV_FUND` 不同 → INSERT(`AfterUpdate` 還多一條 UPDATE 路徑,`:390`)。

**這條 INSERT 把四眼全部填滿:** `STATUS` 寫死 `'301'`、`DATA_ID` 寫死 `'2'`、`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全部塞同一個 `model.Utility.PermissionInfo[0].UserID`、日期全是同一個 `DateTime.Now` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276`,`AfterUpdate` 的同一段在 `:353-354`)。

也就是說:**使用者在申購單上改配息方式,`OFD113` 這張表就多一筆「已核准」的設定,不經過任何覆核。** `OFD113` 自己有維護畫面 `OFDM113`(§4.9),那支是走四眼的——**同一張表,兩個入口,兩種治理強度**。

#### 存檔前檢核 `befPostCheck`

UI 在存檔前另外呼叫一支 `befPostCheck`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:967-1078`),兩道:

| 道 | SQL | 成立時的訊息 |
|---|---|---|
| 交易檢核 | `OFD081.LAST_ALLOT_DATE_P`(分戶)或 `LAST_ALLOT_DATE_O`(綜合)`< :ALLOT_DATE` | 「輸入的申購日期大於該基金的申購最後交易日, 故不可輸入此申購日期」 |
| 結帳檢核 | `OFD303.CTL_DATE = :ALLOT_NAV_DATE` 且 `ALLOT_CTL_CODE`(分戶)或 `ALLOT_CTL_CODE_O`(綜合)`>= '2'` | 「此基金該申購日期已處理到下單確認之後, 故不可輸入此申購日期」 |

兩道都用 `UNION ALL` + `AND :OMNIBUS_ID = 'N' / 'Y'` 的寫法在同一段 SQL 裡切兩軌 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001`;`:1036` 與 `:1044`)。 `LAST_ALLOT_DATE_*` 有做 `NVL(TRIM(...), '29991231')`,所以**沒設最後交易日的基金不會被擋**,是刻意的。

#### 其他取數方法

| 方法 | 取什麼 | 注意 |
|---|---|---|
| `GetOFD110` | 受益人匯款帳戶 | — |
| `GetOFD562` | 受益人扣款帳戶 | 與 `OFDM551` / `OFDM554` 的同名方法各寫一份 |
| `GetOFD113` | 配息設定 | `catch` 是空的(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224`) |
| `GetOFD086` | 配現可再投資基金 | — |
| `GetOFD091` | ISHARE 基金申購金額額度 | SQL 裡 `OFD221.OMNIBUS_ID = 'N'` 與 `ALLOT_PROC_CODE <> 'D'` 都寫死(`:900-901`) |

`ALLOT_PROC_CODE <> 'D'` **沒有 `NVL`**。Oracle 三值邏輯:`ALLOT_PROC_CODE` 是 NULL 時 `NULL <> 'D'` 是 UNKNOWN,該列不計入額度。 **已用額度會被低估**,放行原本該擋的申購。這是本片第一條「`欄 <> '值'` 遇 NULL」。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `OFD081` 最後交易日 | 申購日晚於最後交易日 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1017-1022` |
| 存檔前 | `OFD303` 結帳狀態 | 已到下單確認之後 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1061-1066` |
| 存檔前 | 上述兩道的 SQL 出錯 | 例外 | 阻擋(`AddResultRow(false, …, ex.ToString())`,訊息是原始例外字串) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1071-1076` |
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋(丟例外) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:156-157` |
| 新增時 | 取到的書號已存在 | 是 | 重取(**無上限**) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:162-167` |
| 存檔後 | 配息設定有差異 | 是 | **記錄不擋**(直接寫 `OFD113`,`STATUS='301'`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276` |
| 額度查詢 | `ALLOT_PROC_CODE <> 'D'` | NULL 時 UNKNOWN | **過濾(無提示)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |

### 4.7 `OFDM231B` — 境外基金買回 / 轉換維護(綜合帳戶軌)

#### 用途(推測)

買回(贖回)與轉換單據的維護。主檔 `OFD251`(152 欄),三張明細: `OFD252` 基金贖回付款、`OFD253` 轉換、`OFD254` 基金贖回銷售沖銷。PO 1,180 行,是本片最大的一支。

#### 與 `OFDM221C` 對稱的地方

| 面向 | `OFDM221C` | `OFDM231B` |
|---|---|---|
| 書號 | `"OFD220" + TradeId` → `ALLOT_NO` | `"OFD251" + TradeId` → `REDEM_NO`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:151-205`) |
| 存檔前檢核 | `befPostCheck` 兩道 | `befPostCheck` 兩道,**但每道多一個分支**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:967-1172`) |
| 存檔後 | 同步 `OFD113` | `AfterAdd` / `AfterUpdate` 都只是空殼(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:206-230`) |

#### 獨有的兩件事

**(1)明細 `OFD254` 由 SP 產生,不是使用者輸入。** `GetOFD2541` 依模式叫兩支不同的 SP(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:704-757`):

| 情境 | SP |
|---|---|
| 新增 | `S_OTA_OFDM231B_EXE_ADD`(`:714`) |
| 修改 | `S_OTA_OFDM231B_EXE_MOD`(`:732`) |

兩支都在版控內(`DB/SP/S_OTA_OFDM231B_EXE_ADD.SQL`、`DB/SP/S_OTA_OFDM231B_EXE_MOD.SQL`)。

**(2)匯率取自別的模組的 SP。** `GetOFD300` 叫 `S_TA_IMP_OFD300_RANGE`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:891`)取集保匯率檔。這支 SP **不在 `DB/` 版控內**(`architecture.md §9` 已記 `DB/` 只涵蓋一部分 SP),已列入 meta 的 `refcheck-ignore`。

#### 明細 SQL 的複製貼上痕跡

`BuildDetailSQLString` 用 `switch (strTableName)` 分三段(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:307-643`):

| `case` | region 標題 | 實際組的表 |
|---|---|---|
| `"OFD252"`(`:314`) | 基金贖回付款檔(OFD252) | `OFD252` ✔ |
| `"OFD253"` | **基金贖回付款檔(OFD252)**(`:438`,**標題沒改**) | `OFD253`(`:440`、`:580`) |
| `"OFD254"`(`:583`) | 基金贖回銷售沖銷檔(OFD254) | `OFD254` ✔ |

三段的 WHERE 都用字串串接接書號(`:434`、`:580`、`:631`),不是參數化。書號由伺服器自己產生,注入風險低,但寫法不一致。

#### UI 端的兩處 `Select("FUND_ID <> ''")`

`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488` 與 `:498-499` 各取 `[0]`,**沒有長度檢查**。明細全空(合法情境:只填主檔先存)就 `IndexOutOfRangeException`。而且 `DataTable.Select` 的 `<> ''` 在 .NET 的語意與 Oracle 不同(.NET 的空字串不是 NULL), 所以這裡不會踩到三值邏輯,但**同一支程式裡 `<>` 有兩種語意**,讀碼要分清楚在哪一層。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `OFD081` 最後交易日(買回) | 買回日晚於最後交易日 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1020-1025` |
| 存檔前 | 同上的第二個分支(轉換) | 是 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1063-1068` |
| 存檔前 | `OFD303` 結帳狀態(買回) | 已結帳 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1108-1113` |
| 存檔前 | `OFD303` 結帳狀態(轉換) | 已結帳 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1153-1158` |
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:163-168` |
| UI 取值 | 明細第一筆 | 明細 0 筆 | **例外** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488`、`:498-499` |

### 4.8 三支授權書畫面:`OFDM109` / `OFDM111` / `OFDM561`

結構幾乎相同(主檔一張授權書 + 明細一組帳戶 / 期間),PO 都繼承 `BaseEVADaoPO`,都有 `BeforeAdd` 取號。

| 畫面 | 主 / 明細 | 特別的方法 | 注意 |
|---|---|---|---|
| `OFDM109` | `OFD109` / `OFD110` | `GetCRNCY_CD`:查該受益人在綜合帳戶有部位的交易幣別(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453-486`) | SQL 裡 `CRNCY_CD <> 'TWD'` 沒 `NVL`(`:466`)→ 幣別 NULL 的部位被靜默濾掉 |
| `OFDM111` | `OFD111` / `OFD112` | `SetOPEN_ACC_DATE_OFF`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:396-443`);另外 join view `FNDV01` | — |
| `OFDM561` | `OFD561` / `OFD562` | 無 | 與 `OFDM109` 的欄位名完全撞名(`REMIT_CFM_NO`),見 §2.3 |

三支共同的兩個寫法:

- **明細 SQL 的書號用字串串接**:`OFD110.REMIT_CFM_NO = '" + strREMIT_CFM_NO + "'` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:256`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:237`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM561_PO.cs:249`)。

- **`BeforeAdd` 的 `do/while(IsExistByData)` 沒有次數上限**(`OFDM109_PO.cs:141-182`、`OFDM111_PO.cs:134-175`、`OFDM561_PO.cs:135-176`)。

`OFDM109` 的 UI 另有一條:`Select("ACC_NO_TYPE <> '0'")`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM109.cs:281`)—— 這是 `DataTable.Select`,不是 SQL,語意正常。

#### 卡控總表(三支合併)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增時 | 取到的書號已存在 | 是 | 重取(無上限) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:141-182` |
| 幣別下拉 | `CRNCY_CD <> 'TWD'` | 幣別為 NULL | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:466` |
| 取數失敗 | 任一 `Get*` 方法例外 | 有 | 警示(訊息如「取得有綜合帳戶交易幣別,請檢查」) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:477-481` |

### 4.9 兩支配息畫面:`OFDM113` / `OFDM251`

| 畫面 | 主檔 | 管什麼(推測) |
|---|---|---|
| `OFDM113` | `OFD113` | 受益人層級:某受益人某基金的配息方式與再投資標的 |
| `OFDM251` | `OFD281` | 基金層級:某基金某基準日的配息公告(每單位配現、發放日) |

**`OFDM113_PO.cs` 是本片唯一的非 UTF-8 來源檔**(cp950 / Big5)。用 UTF-8 讀會看到亂碼,例如 `:235` 那則訊息在 UTF-8 下是 `���o�t�Ѱ���N��(OFD086)...`, 用 cp950 讀才是「取得配股基金代號(OFD086),請檢查」。 `architecture.md §5` 的「混編碼」風險在本片就命中這一支;任何用 UTF-8 一刀切的工具(含本文的掃描器)碰它都會出亂碼。

`OFDM251_PO` 的查詢條件有一條字串串接的 `LIKE`:

`strSQL += " AND OFD281.RECORD_DATE LIKE " + "'" + Row.Value + "%'";`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182`)

——**本片唯一一處把使用者輸入直接串進 SQL 的地方**。`RECORD_DATE` 來自畫面的日期欄,值帶單引號就會壞掉(或被利用)。前 21 篇的型錄裡有「`LIKE` 樣式餵給 `=`」(`ofd4.md`),這裡是相反的形態:**`=` 的值被硬改成 `LIKE` 樣式,而且是串接的**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | `RECORD_DATE LIKE '<值>%'` | 值含單引號 | **例外 / 注入風險** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182` |
| 取配股基金 | `OFD086` 查不到 | 0 筆 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:226-229` |

### 4.10 兩支定期定額畫面:`OFDM551` / `OFDM554`

一對成對畫面:`OFDM551` 建契約(`OFD551` / `OFD552`),`OFDM554` 建契約變更(`OFD554` / `OFD555`)。

| 面向 | `OFDM551` | `OFDM554` |
|---|---|---|
| 書號類別 | `"OFD551" + TradeId` → `RSP_NO` | `"OFD554" + TradeId` → `RSP_CHG_NO` |
| 取扣款帳戶 | `GetOFD562`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:385-431`) | `GetOFD562`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:455-497`) |
| 取申購明細 | `GetOFD221`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434-500`) | 無 |
| 取原契約 | `GetOFD555` **走報表 SP** `S_OTA_OFDR552_GET`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:503-537`) | `Get_Origin`(自組 SQL,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:600-680`) |
| 停扣過濾 | 無 | `NVL(OFD551.STOP_ID, 'N') <> 'Y'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543`) |

**兩支各寫一份 `GetOFD562`,SQL 不同。**改扣款帳戶的取數邏輯要記得兩邊都改,這是型錄裡「成對畫面只改一邊」的溫床。

`OFDM554` 的停扣過濾有做 `NVL`,是本片唯一一處把三值邏輯處理對的地方——**同一個團隊、同一個模式,有的寫對有的沒寫**(對照 §4.6 的 `ALLOT_PROC_CODE`)。

`OFDM551` 的 `GetOFD555` 直接叫報表的 SP(`S_OTA_OFDR552_GET`)拿維護畫面要用的資料。報表 SP 的結果集欄位若為了報表需求調整,**維護畫面會跟著壞,而且沒有任何編譯期關聯看得出來**。

#### 卡控總表(兩支合併)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:136-180` |
| 查原契約 | `NVL(OFD551.STOP_ID,'N') <> 'Y'` | 已停扣 | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| 取數失敗 | `GetOFD562` / `GetOFD221` / `GetOFD555` 例外 | 有 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:422-426`、`:491-495`、`:528-532` |

### 4.11 `OFDM302B` — 境外基金淨值維護與鎖定(**本片最危險的一支**)

#### 用途(推測)

匯入 / 維護 `OFD302`(基金代碼 + 淨值日期 → 申購淨值、贖回淨值、正式淨值、基金規模), 並用 `NAV_LOCK` 把某一天的淨值鎖起來,鎖後才能給下游結帳用。

#### 四個自訂鈕

| 鈕 | 方法 | 做什麼 |
|---|---|---|
| `DoExp1` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:268-278` | 整批匯入(`BatchAdd`) |
| `DoExp2` | `:279-299` | 淨值鎖定(`Update_NAVLOCK`) |
| `DoExp3` | `:300-317` | 列印淨值表(`PrintReportNAV` → `OFDM302BRPS2`) |
| `DoExp4` | `:318-328` | 列印鎖定淨值表(`PrintReportLockNAV` → `OFDM302BRPS1`) |

兩張 `.rpt` 都**不在任何 csproj**(§3.5 註 2)。

#### 整批匯入:三個問題

`BatchAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:177-251`):

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **`DELETE OFD302 WHERE NAV_DATE = :NAV_DATE`** | 刪除條件**只有淨值日期**,不含基金公司也不含基金代碼。匯入某一家基金公司的淨值檔,會把**那一天全部基金的淨值整批刪掉**,再只補回檔案裡有的那幾筆 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:191-192` |
| 2 | **刪除的檢核是死的** | `if (i == -1)`,而 `ExecuteNonQuery` 回的是影響列數,永遠不是 -1 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` |
| 3 | **完全繞過四眼** | `STATUS` 寫死 `'301'`,`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全塞 `row.CREATEID`、日期全是 `SYSDATE` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:208-209` |

再加一條:`catch` 裡的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉** (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:239-245`),例外不上報,只把 `ex.ToString()` 塞進結果訊息給使用者看。

`OFD302` 的下游很廣(§2.4):`CLSR002` 結算報表、`OFDI058` / `OFDI058B` 查詢、 `OFDB322` / `OFDB323` / `OFDB722` 批次、`OFDI011` 淨值查詢都讀它。 **問題 1 的爆炸半徑是整個結帳。**

#### 淨值鎖定:同一個 UPDATE 跑兩次

`Update_NAVLOCK`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:452-519`)對每一筆勾選的列跑 `UPDATE OFD302 SET NAV_LOCK, UPDATEID, UPDATEDATE WHERE NAV_DATE = ? AND FUND_ID = ?`。

```
dbProduct.ExecuteNonQuery(cmd, tran);          // :493  ← 第一次,回傳值丟掉
i = dbProduct.ExecuteNonQuery(cmd, tran);      // :495  ← 第二次,回傳值才拿來判斷
```

**同一個 `DbCommand` 被執行兩次。**因為 UPDATE 是冪等的,資料結果一樣; 但每一列都多打一次 DB,而且 `:495` 的第二次必然影響同樣的列數,所以 `i == 0` 的檢核實際上檢的是第二次。這是「`ExecuteNonQuery` 回傳值被覆蓋」的變形。

另外它**直接寫 `UPDATEID` / `UPDATEDATE`,不經四眼**——這是型錄裡「繞過四眼直接 UPDATE 主檔」(`ofd5.md` 記過同型)在本片的第二例。

#### UI 端的鎖定保護

`SetControlEnabled()`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:467-483`)把 `ucomNAV_LOCK` 設成 `Enabled = false` 加 `ReadOnly = true`(`:470-471`),新增時強制 `"N"`(`:476`)。 `DoValidate()` 另有一條:雙擊且鎖定碼是 `"1"` 時擋修改(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160`)。

**注意鎖定碼在三處用了三種值:**`SetControlEnabled` 寫 `"N"`、`DoValidate` 比 `"1"`、 `PrintReportLockNAV` 的 SQL 比 `NAV_LOCK = 'Y'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:282`)。下拉的資料來源是 `YesNoDataSrc`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:246`),也就是 `Y`/`N`。 **`"1"` 這個值對不上任何一邊**——`DoValidate` 那道檢核**永遠不會成立**,等於沒有。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 修改前 | 雙擊且 `NAV_LOCK == "1"` 時擋 | **永不成立**(下拉只給 `Y`/`N`) | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160` |
| 新增 / 修改 | 鎖定碼欄位唯讀 | 一律 | 阻擋(UI 層) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:470-471` |
| 整批匯入 | 刪除影響列數 `== -1` | 永不成立 | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` |
| 整批匯入 | 每列 INSERT 影響列數 `== 0` | 是 | 阻擋 + rollback | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:228-234` |
| 鎖定 | 每列 UPDATE 影響列數 `== 0` | 是 | 阻擋 + rollback(判的是**第二次**執行的結果) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:495-501` |
| 列印鎖定表 | 有鎖定的淨值 | 0 筆 | 警示「淨值未鎖定」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:319-322` |

### 4.12 `OFDM602A` — 文件需求設定維護

`OFD605`(`REQ_DOC_KIND` + `DOC_CD`)的多筆主檔維護,PO 只有 192 行,是 11 支 `OFDM*` 裡最小的。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `MasterTable.Add(new xTableMapping("OFD605", "OFD605"))` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:68` |
| 查詢條件 | `REQ_DOC_KIND` 用**字串串接** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:177` |
| 事件 | 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData`,**沒有 `BeforeAdd`**(不需要取號) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:76-122` |

它的 `ATLAS.EC` 版姊妹 `OFDM602` 讀寫**同一張 `OFD605`**,但整個 PO 類別被註解掉 (`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19` 是 `// public class OFDM602_PO : MultiRowEVAPO`)。 **推論:`OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品,不是平行軌。** 這也是 11 支裡唯一一支「兩軌讀同一張表」的,其他三對都是各讀各的表(§0.3)。

### 4.13 `OTAM901` — 報表行銷說明代碼維護

`BMS999`(`ST_CD`)的單表四眼維護,PO 185 行,結構與 `TRPM005` 一模一樣。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `BMS999` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:66` |
| 查詢條件 | 只有 `ST_CD` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:146` |
| 自訂檢核 | **沒有**,`DoValidate()` 只叫框架的 `DataValidate()`(與 `TRPM005` 一樣) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:140-145` |

**表名前綴誤導**:表叫 `BMS999`,直覺會去 `ATLAS.BMS` 找維護畫面,但全庫只有 `OTAM901` 碰它。 `architecture.md §2` 說「看到代號就知道六個檔在哪」,這條鐵律**不適用於表名**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:101-112` 與 `:118-129` |
| 刪除前 | (無) | — | 不擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:114-117` |

## 5. 查詢畫面(I)

本片只有一支:`TRPI001`(集保傳收檔紀錄查詢),住在 `ATLAS.OTA.Query`。

### 5.1 結構

完全符合 `architecture.md §6` 對 I 型的描述:PO 退化成裸 DAO。

| 層 | 類別 / 基底 | 錨點 |
|---|---|---|
| UI | `TRPI001 : xOneStepProcessForm`(**不是 `xQueryForm`**;`architecture.md §6` 說 I 型有 94 支用這個基底) | `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:18` |
| Ctl | `TRPI001_Ctl : BaseController`,**有**覆寫 `InitializeDataAccessPool()` 與四個 `CustomTransfer*` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/TRPI001_Ctl.cs:11`、`:22`、`:61-89` |
| PO | `TRPI001_PO : ITRPI001_PO`,**沒有基底**,自己 `new Database("TA", DbServerType.Oracle)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:32` 與 `:34` |

三個與慣例不同的地方,都在 `architecture.md §2` 的例外清單裡:

1. PO 檔名是 `TRPI001_PO.cs`,不是 `.Query` 專案常見的 `<代號>OracleDao.cs`。

2. 層資料夾叫 `QueryPO.OFD` / `QueryUI.OFD` / `QueryControl.OFD`(前綴 `OFD`),但畫面代號是 `TRP`、組件名是 `QueryPO.OTA`。

3. 專案是 `ATLAS.OTA.Query`,模組是 `TRP`。**三個名字三個模組碼**。

### 5.2 查詢條件

UI 送五個參數(`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:99-103`):

| 參數 | 控件 | PO 有沒有用 |
|---|---|---|
| `TRP_TYPE` 申報平台種類 | `ucboTRP_TYPE` | 有,`= :TRP_TYPE` |
| `PERIOD` 週期 | `ucboPERIOD` | 有,`= :PERIOD` |
| `FILE_STYLE` 傳檔 / 收檔 | `uoptFILE_STYLE` | **沒有**,見 §5.3 |
| `FILE_NAME` 檔名(值其實是 `MEDIA_NO`) | `ucboFILE_NAME` | 有,`TRP001.MEDIA_NO = NVL(TRIM(:FILE_NAME), TRP001.MEDIA_NO)` |
| `TRANS_DATE` 傳檔日期 | `udatTRANS_DATE` | 有,`TRP002.TRANS_DATE = NVL(TRIM(:TRANS_DATE), TRP002.TRANS_DATE)` |

`FILE_NAME` 這個參數名與它裝的值不一致:UI 的下拉是 `GetFileName` 撈出來的 `TRP001.MEDIA_NO AS CODE, TRP001.FILE_NAME AS CODE_DESC`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:140`), 所以 `Value` 是 `MEDIA_NO`、顯示才是 `FILE_NAME`。SQL 端也確實拿它去比 `MEDIA_NO`。**參數名騙人,行為是對的。**

### 5.3 哪些條件會靜默濾掉資料

#### (1)`FILE_STYLE` 送了但沒用 — 傳檔與收檔查出來一樣

UI 在 `:101` 把 `FILE_STYLE` 放進 `QueryVDB.Util.Parameters`, 但 `GetData` 的 SQL 與 `AddInParameter` 都**沒有這個欄位** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:83-96`)。

它唯一有作用的地方是**下拉選單的內容**:`GetFileName` 會拿 `FILE_STYLE` 去篩 `TRP001` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:132`)。

**後果**:只要使用者不指定檔名(下拉留空),切「傳檔」與切「收檔」查出來的結果**完全一樣**—— `TRP002` 裡同種類同週期的傳檔與收檔紀錄會混在一起,而且畫面上沒有欄位可以分辨。結果類型:**過濾(無提示)的反面 —— 該濾沒濾**。

#### (2)`INNER JOIN TRP001` 會讓歷史紀錄整筆消失

```
FROM TRP002
INNER JOIN TRP001 ON TRP002.TRP_TYPE = TRP001.TRP_TYPE AND TRP002.FILE_NAME = TRP001.FILE_NAME
```

(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81`)

`TRP002` 是傳檔紀錄(歷史),`TRP001` 是設定(現況)。 **設定被刪掉、或 `FILE_NAME` 被改過,對應的歷史紀錄就查不到了,而且沒有任何提示。** 這正是型錄裡「`INNER JOIN` 讓對不到的資料無聲消失」(`ofd6.md` 記過同型)。對照下一行的 `LEFT JOIN OFD062`(基金公司名稱)——**同一段 SQL 裡,作者知道要用 `LEFT JOIN`,卻在 `TRP001` 這裡用了 `INNER`**。

#### (3)基金公司欄位的 `DECODE(..., NULL, '所有境外基金公司', ...)`

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:68-71`: `FH_CD` 是空的(不分基金公司的傳檔)時,`LEFT JOIN OFD062` 對不到,名稱欄顯示「所有境外基金公司」。這個判斷是**用名稱欄是不是 NULL** 來反推,不是用 `FH_CD`。所以 **`FH_CD` 有值但 `OFD062` 查不到那家公司**(代碼被刪或打錯)時,畫面一樣顯示「所有境外基金公司」——**錯的資料長得像對的**。

#### (4)`SUBSTRB(...,1,25)` 硬切 25 位元組

同一行的顯示字串是 `SUBSTRB('(' || FH_CD || ')' || FH_NM_SH_C, 1, 25)`。 `SUBSTRB` 切的是**位元組**不是字元,中文一個字 2 到 3 位元組,長名稱會被切一半,可能切出半個中文字。

### 5.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:85-97` |
| 查詢 | `FILE_STYLE` 條件 | **永不生效** | **該濾沒濾** | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:83-96` |
| 查詢 | `INNER JOIN TRP001` | 設定已刪 / 改名 | 過濾(無提示) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81` |
| 查詢後 | 查無資料 | 0 筆 | **記錄不擋**(`AddResultRow(false, 0, "")`,**訊息是空字串**,畫面上不會說為什麼) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:105-111` |
| 查詢 | SQL 例外 | 有 | 警示(訊息是 `ex.Message` 原文) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:113-118` |

## 6. 批次(B)與 WindowsService

**本片無 B 型畫面,也沒有任何 WindowsService。**

原因很具體:這 21 支的批次性工作(傳檔、收檔、淨值匯入、月報製作)**全部設計成「使用者按按鈕」的一次性作業**, 而不是排程。三個佐證:

| 佐證 | 內容 | 錨點 |
|---|---|---|
| 1 | `TRPM001` / `TRPM101` 的 UI 基底是 `xOneStepProcessForm`(B 型常用的基底),但代號是 `M`。也就是說**批次能力被寫進 M 畫面裡了**,沒有再開一支 B | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:30` |
| 2 | 產檔那一步是**用戶端**的 `StreamWriter`,不是伺服器端寫檔——服務跑不了這種流程(服務沒有使用者的磁碟對映) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527` |
| 3 | `architecture.md §6` 實測全庫只有 4 支 B 畫面配了獨立 Windows 服務(`OFDB600` / `OFDB609` / `OFDB680` / `RSPB008`),沒有一支屬於本片 | `architecture.md §6` |

**對維護的意義**:要把傳檔改成自動排程,不能只是加一支服務去叫現有的 `_Pxy`—— 產檔落地那段在用戶端,得先把它搬到伺服器側,或改寫成伺服器直接寫檔。

## 7. 報表(R)

### 7.1 七層結構

R 型是**七層不是六層**(`architecture.md §6`):六層各自加 `Report` 前綴,再多一個 `Report.<模組>` 專案只放 `.rpt`。本片三支橫跨兩個 `.Report` 專案:

| 層 | `TRPR001` / `OTAR901` 的專案 | `IJPR611` 的專案 |
|---|---|---|
| 1 UI | `ReportUI.OTA` | `ReportUI.EC` |
| 2 FormProxy | `ReportFormProxy`(**資料夾名沒有 `.OTA`**) | `ReportFormProxy.EC` |
| 3 Control | `ReportControl.OTA` | `ReportControl.EC` |
| 4 PO | `ReportPO.OTA` | `ReportPO.EC/Oracle`(**多一層 `Oracle` 子目錄**) |
| 5 DataEntity | `ReportDataEntity.OTA` | `ReportDataEntity.EC` |
| 6 UIEntity | `ReportUIEntity.OTA` | `ReportUIEntity.EC` |
| 7 CrystalReports | `Report.OTA` | `Report.EC` |

`Dev/ATLAS.OTA.Report/Source/FormProxy/ReportFormProxy/` 這個資料夾**沒有模組後綴**, 與 `architecture.md §6` 舉的 `ReportFormProxy.CAS` 不同;`architecture.md §2` 把它歸在「專案名與層資料夾不同名」那一類例外。用 glob 寫死 `ReportFormProxy.<模組>` 會找不到 `TRPR001_Pxy.cs` 與 `OTAR901_Pxy.cs`。

### 7.2 一覽

| rpt | 對應畫面 | 取數來源 | 參數 | 在版控 |
|---|---|---|---|---|
| `TRPR001RPS1` | `TRPR001` | `S_OTA_TRPR001_GET`(refcursor `OutTB1`) | `iCAL_YM` `iFH_CD` | `DB/SP/S_OTA_TRPR001_GET.SQL` ✔ |
| `OTAR901RPS1` | `OTAR901` | `S_OTA_OTAR901_GET` | `iALLOT_DATE_S` `iALLOT_DATE_E` `iAGENT_ID_S` `iAGENT_ID_E` `iAGENT_CODE_S` `iAGENT_CODE_E` | **不在版控**(已列 `refcheck-ignore`) |
| `IJPR611RPS1` 到 `IJPR611RPS7` | `IJPR611` | Dao 內七段長 SQL,不走 SP | `DATES` `ID_NO` `PrintType` `EMP_NO` | 不適用 |

### 7.3 `IJPR611` — 七支 `.rpt`,畫面只選得到五支

`uoptPrintType` 這個選項組在 Designer 裡**只有五個項目**,`DataValue` 是 `"0"` 到 `"4"` (`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:203-218`):

| 值 | 顯示文字 |
|---|---|
| `0` | 全方位理財約定書 |
| `1` | 查詢戶約定書 |
| `2` | 舊戶轉查詢戶約定書 |
| `3` | 查詢轉全方位理財約定書 |
| `4` | 傳統戶轉全方位理財約定書 |

但 UI 的 `switch` 與 Dao 的 `switch` 都處理 `"0"` 到 `"6"`,共七個分支 (`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:126-155`;`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:66`)。 Dao 的註解直接寫出第 6、7 種是什麼:

`//0:全方位理財約定書 1:查詢戶約定書 2:舊戶轉查詢戶約定書 3:查詢戶轉全方位理財約定書 4:傳統戶轉全方位理財淤定書 5:ACH定額授權書 6:財金定額授權書` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64`)

**結論:`IJPR611RPS6`(ACH 定額授權書)與 `IJPR611RPS7`(財金定額授權書)是死碼。** 兩支 `.rpt` 與對應的 SQL 分支都編進組件、都在 csproj 裡,但**畫面上沒有任何入口選得到它們**。 `VirtualReportFormUtility` 也照樣為它們註冊了七組事件(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:60-115`)。

**假設**:這兩式曾經開放過、後來被從選項組拿掉,或反過來是預留還沒上線。依據是註解把 7 種都寫齊、七層都備好,只有 Designer 的選項少了兩個。要確認得問使用者或查需求單。

### 7.4 `IJPR611` 的三個踩雷點

**(1)預覽有清參數、列印沒有。**

```
IJPR611_BeforePreviewButtonClicked:  … switch … ; this.QueryVDB.Util.Parameters.Clear(); … Add(DATES/ID_NO/PrintType/EMP_NO)
IJPR611_BeforePrintButtonClicked:    … switch … ;  (沒有 Clear)          … Add(DATES/ID_NO/PrintType/EMP_NO)
```

`Clear()` 只出現在預覽那一支(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:157`), 列印那一支從 `:170` 到 `:207` 一路直接 `AddParametersRow`,**沒有清空**。先按預覽再按列印,同一組參數就被加第二次。這是型錄裡「成對路徑只改一邊」的標準形態。

**(2)`ID_NO` 一律補 `%`,再由 SQL 用 `RTRIM` 剝掉。**

UI:`AddParametersRow("ID_NO", SQLOperator.Equal, custECID_NO_0.Value.Trim() + "%")`(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:163`)。 SQL:`AND (A.ID_NO = RTRIM(:ID_NO,'%') OR (E.ETRAFLG='N' AND E.DOC_CODE='Y' AND RTRIM(:ID_NO,'%') IS NULL))` (例 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:366`)。

使用者不輸入時 `ID_NO` 是 `"%"`,`RTRIM('%','%')` 在 Oracle 回空字串等同 NULL,走「全部」分支——**設計是這樣**。但這個約定同時表示:**受益人 ID 本身若以 `%` 結尾,尾巴會被吃掉**。而且參數名用的是 `SQLOperator.Equal` 卻裝著 `LIKE` 樣式,與型錄裡 `ofd4.md` 的「`LIKE` 樣式餵給 `=`」是同一個病灶,只是這裡靠 SQL 端補救了。

**(3)`DataTable.Select` 用字串串接組過濾式。**

`resultVDB.DataEntity.IJPR611RPS1Detail.Select("ORDER_Type = 2 AND ID_NO= '" + row.ID_NO + "' AND BANK_HQ_NAME = '" + row.BANK_HQ_NAME + "' …")` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:586`)。銀行名稱裡出現單引號就會丟 `SyntaxErrorException`。不是 SQL 注入,但同一類問題。

另外 Dao 裡有一條寫死的帳號樣式:`AND E.UPD_USER LIKE 'WebUser%'` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:943`)——網路下單的帳號前綴,標〔客戶特定〕。

### 7.5 `OTAR901` — 報表之外還會開 Excel

`DoExp1`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:324-362`)走的是完全不同的路:

| 步 | 做什麼 |
|---|---|
| 1 | `DoValidate(true)` 通過才往下 |
| 2 | `GetReportData` 取同一份資料 |
| 3 | 檔名寫死成 `<輸出路徑>\OTAR901RPS1.xlsx`,報表中文名在 `:335` 又寫一次(`:335-336`) |
| 4 | 0 筆就跳「查無相關資料。」並 return(`:339-345`) |
| 5 | `UIExcelHelper.GenExcelFile` 用 `Microsoft.Office.Interop.Excel` 在**用戶端**產檔(`:349-353`、`:372`) |

兩件事值得記:

- **報表中文名寫死在程式裡兩處**:`SetQueryParameters("OTAR901RPS1","OTAR901RPS1","弱勢族群交易回訪報表(境外)")`(`:130`)與 `new KeyValuePair<string,string>("OTAR901RPS1","弱勢族群交易回訪報表(境外)")`(`:335`)。改名要改兩處。

- **`catch` 把所有例外壓成同一句「商業邏輯異常!」**,原始訊息只丟給 `Console.WriteLine`(`:357-362`)—— WinForms 沒有主控台,**等於訊息直接消失**。這是本片最難除錯的一個 `catch`。

### 7.6 `TRPR001` — PO 檔名錯字與交易用法

取數只有一步:`S_OTA_TRPR001_GET` 加一個 refcursor `OutTB1` (`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:66-75`)。

三個觀察:

1. **PO 住在檔名少一個 `R` 的檔案裡**(§3.5 註 1)。

2. **純查詢卻開了交易**:`tran = m_db.BeginTransaction()`(`:61`)、`tran.Commit()`(`:78`)、`catch` 裡 `tran.Rollback()`(`:91`)。 `catch` 第一行就 `tran.Rollback()`,而 `tran` 是在 `try` 內賦值的——**連線開不起來時會再丟一個 `NullReferenceException` 蓋掉真正的錯誤**, 與 `architecture.md §3` 記的 `BasicEVAPO.Add` 是同一個模式。

3. **`using System.Data.OracleClient;` 與 `Oracle.ManagedDataAccess.Client` 並存**(`:11` 與 `:16`),前者是 .NET 內建的已淘汰 provider。

`GetReportObject` 照 `architecture.md §6` 的寫法,把用戶端傳來的報表類別名直接交給 `CRReportTransfer.TransferFileByte` (`Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/TRPR001_Ctl.cs:61-62`)——**用戶端指定要載入哪個報表類別,伺服器照單全收**。三支報表都是這個寫法。

### 7.7 卡控總表(三支合併)

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `IJPR611` | 預覽 / 列印前 | 「執行日期」與「受益人ID」必需擇一必輸 | 兩個都空 | 阻擋 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:216-228` |
| `IJPR611` | 列印 | 參數未清空 | 連按預覽再列印 | **記錄不擋(參數累積)** | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:170-207` |
| `IJPR611` | 選報表種類 | 第 6、7 式 | **選不到** | 死碼 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:213-218` |
| `OTAR901` | 預覽 / 列印前 | `DoValidate()` | 不過 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:120-127` |
| `OTAR901` | 匯出 Excel | 輸出路徑必填與存在 | 不符 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:305-322` |
| `OTAR901` | 匯出 Excel | 查無資料 | 0 筆 | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:339-345` |
| `OTAR901` | 匯出 Excel | 任何例外 | 有 | **記錄不擋 → 訊息消失**(只 `Console.WriteLine`) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:357-362` |
| `TRPR001` | 取數 | 0 筆 | 是 | **記錄不擋**(`AddResultRow(false, 0, string.Empty)`,**訊息是空字串**) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:84-87` |

## 8. 跨模組共用

```text
[圖] 十一支 OFDM 與 ATLAS.OFD 的關係:四對兩軌、七支唯一實作、兩軌怎麼區分,以及 OFD113 的三個入口
圖中文字:分家方式:代號加後綴、表名去掉 A(四對) / OFDM221C → OFD220 OFD221 / ATLAS.OTA 綜合帳戶軌 / OFDM221A → OFD220A OFD221A / ATLAS.OFD 分戶軌 / OFDM221B / 只有 UI 一層 推測是子視窗 / OFDM231B → OFD251…254 / OTA 軌 / OFDM231A → OFD251A…254A / OFD 軌 再加七張明細 / OFDM302B → OFD302 / OTA 軌 / OFDM302 → OFD302A / OFD 軌 / OFDM602A → OFD605 / OTA 軌 活的 / OFDM602 → OFD605 / EC 專案 整個類別被註解 / 唯一的反例 / 同一張表 是改版不是分軌 / 另外七支在全庫是唯一實作,OFD 主軌沒有 / OFDM109 OFDM111 OFDM561 / 授權書與扣款帳戶 / OFDM113 OFDM251 / 配息 / OFDM551 OFDM554 / 定期定額 / 綜合帳戶軌有專屬功能 / 不是分戶軌的複製 / 怎麼區分兩軌 / OMNIBUS_ID / Y 綜合 / N 分戶 / OFD113 卻用 2 / 1 / 同概念兩套值域 / GetSrIdNoForOTA / OTA 專屬取號 / S_OTA_* 命名空間 / 與主軌的 S_TA_* 分開 / OFD113:一張表三個入口,兩種治理強度 / OFDM113 / 走四眼 / OFDM221C AfterAdd / 自組 INSERT STATUS 301 / OFDM231B / 只讀 / 資料上分不出來 / 只能看 ALLOT_NO 有沒有值
```

*圖:圖 5 跨模組。橘框=本片(綜合帳戶軌);灰虛框=ATLAS.OFD / ATLAS.EC 的對照組;橘虛框=反例或會咬人的地方;黑框=無原始碼。左右兩欄的表名只差一個 A,改欄位時很容易改錯邊。*

### 8.1 十一支 `OFDM*` 與 `ATLAS.OFD` 的關係

這是本片最重要的一節。結論先講:

> **`ATLAS.OTA` 裡的 11 支 `OFDM*` 是境外基金「綜合帳戶(Omnibus)軌」的實作, 與 `ATLAS.OFD` 的「分戶軌」平行。兩軌的分家方式是:代號加一個後綴字母、表名去掉結尾的 `A`。**

#### 證據鏈

| # | 事實 | 錨點 |
|---|---|---|
| 1 | 11 支在全庫**沒有同代號分身**(與 `ofdb3.md` 查到的 `OFDB562` 到 `OFDB564` 兩份六層不同) | 全庫搜這 11 個代號,只命中 `Dev/ATLAS.OTA/` |
| 2 | 帶後綴的四支各有一支不帶後綴或帶別的後綴的姊妹畫面,**住在別的專案** | §0.3 的對照表 |
| 3 | 姊妹畫面的表名多一個 `A`:`OFD220A` 對 `OFD220`、`OFD251A` 對 `OFD251`、`OFD302A` 對 `OFD302` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-68`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70-74`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| 4 | 本片的 SQL 到處用 `OMNIBUS_ID` 切兩軌,`'Y'` 走綜合、`'N'` 走分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001` |
| 5 | 取號用的是專屬多載 `GetSrIdNoForOTA`(無原始碼,從呼叫端反推) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:165` |
| 6 | SP 命名空間是 `S_OTA_*`,與主軌的 `S_TA_*` 分開 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:714` 對照 `:891` 的 `S_TA_IMP_OFD300_RANGE` |
| 7 | 方法的中文註解直接寫「取得有綜合帳戶交易幣別」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453` |

#### 唯一的例外:`OFDM602A`

`OFDM602A` 與 `ATLAS.EC` 的 `OFDM602` **讀寫同一張 `OFD605`**,不是兩軌。而 `OFDM602_PO` 整個類別被註解掉(`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19`,注意它住在 `MSSQL` 子目錄)。 **推論:`OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品,`A` 後綴在這裡是「改版」不是「分軌」。** 所以「後綴字母 = 分軌」這條規則**有一個反例**,不能當通則套。

#### 另外七支沒有姊妹

`OFDM109` `OFDM111` `OFDM113` `OFDM251` `OFDM551` `OFDM554` `OFDM561` 在全庫是唯一實作,`ATLAS.OFD` 沒有同號畫面。 **推論:綜合帳戶軌有自己專屬的功能(授權書、扣款帳戶、配息設定、定期定額),不是分戶軌的複製。**

#### 改動影響面

| 要改什麼 | 要一起看誰 |
|---|---|
| `OFD220` / `OFD221` 的欄位 | `OFDM221C`(寫)、`OFDM109`(讀幣別,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:461`)、`OFDM551`(讀申購明細,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434`) |
| `OFD251` 到 `OFD254` 的欄位 | 只有 `OFDM231B` |
| `OFD302` 的欄位 | `OFDM302B`(寫)+ `CLSR002` / `OFDI058` / `OFDI058B` / `OFDB322` / `OFDB323` / `OFDB722` / `OFDI011`(讀) |
| `OFD113` 的欄位 | **三個入口**:`OFDM113`(四眼)、`OFDM221C`(繞過四眼寫)、`OFDM231B`(讀) |
| `OFD605` 的欄位 | `OFDM602A`(活)與 `OFDM602`(已註解) |
| **`OMNIBUS_ID` 的值域** | `OFD221` / `OFD081` 檢核用 `'Y'/'N'`;`OFD113` 用 `'2'/'1'`。改一邊必炸另一邊(§2.5) |

### 8.2 `OFD113`:一張表、三個入口、兩種治理強度

| 入口 | 怎麼寫 | 走不走四眼 |
|---|---|---|
| `OFDM113` | 標準 `BaseEVADaoPO` 主檔維護 | **走** |
| `OFDM221C` 的 `AfterAdd` / `AfterUpdate` | 自組 `INSERT INTO OFD113 … STATUS='301'`,四眼六欄全塞同一人同一時間 | **不走** |
| `OFDM231B` 的 `GetOFD113` | 只讀 | — |

**後果**:同一張表裡會同時存在「走過覆核的設定」與「申購單一存檔就生效的設定」, 而 `STATUS` 欄位看起來都是已核准。從資料上分不出來,只能看 `ALLOT_NO` 有沒有值 (`OFDM221C` 寫的那筆會帶申購書號,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275`)。

### 8.3 `FSK005`:維護入口死了,下游還在讀

| 角色 | 誰 | 錨點 |
|---|---|---|
| 唯一維護入口 | `FSKM004` | **已死**(§4.5) |
| 共用唯讀 PO | `BasicFSK_PO.GetStkBrkData` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117` 與 `:139` |
| 靠它的自訂控件 | `ucStkBrk`、`ucSTK_BRK_GRP`、`ucTrustAgentCode` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucStkBrk.cs` |
| 用那些控件的畫面 | `BMSM001` `BMSM006` `NFDR433` `NFDR435` `OFDM231Ap1` `OFDM243` `OFDM243A` `OFDM385` `OFDB331p0` | — |
| 直接 join 它的 PO | `OFDM068_PO` `OFDM221A_PO` `OFDM243A_PO` `OFDB310_PO` | — |
| 資料庫物件 | view `OFD068A_V02` | `DB/View/OFD068A_V02.SQL` |

**這是本片影響面最廣的一條**:全系統的券商下拉都靠 `FSK005`,而它的維護畫面跑不起來。資料只能靠 DB 直改或別的途徑進去。

### 8.4 `BMS999`:表名前綴與模組歸屬無關

`BMS999` 前綴是 `BMS`,但全庫**只有 `OTAM901` 碰它**(讀與寫)。 `architecture.md §2` 的命名鐵律講的是**畫面代號**推得出六層檔案位置,**表名沒有這條規則**。在本片還有第二個例子:`OFDM251` 的主檔是 `OFD281` 不是 `OFD251`(§2.1)。

### 8.5 `TRP` 對外的兩條線

| 線 | 內容 | 錨點 |
|---|---|---|
| 寄信 | `TRPM101` 收到 `TTP12A` 時直接 `new OFDM053_PO()` 呼叫 `SEND_MAIL_PROC(BMSRow, "07")` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687` |
| 名單 | 名單 SQL 讀 `TRPM101T1`(暫存)+ `BMS001A`(受益人)+ `OFD601`,兩個都是 `INNER JOIN` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729` |

`TRPM101_PO` 裡還有一個方法的簽名收的是**別支畫面的 ModelVDB**: `private int GetMailData(OFDM053ModelVDB model, DbTransaction tran)`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:710`)。一支 `TRP` 的 PO 直接依賴 `OFD` 的 typed DataSet 與 PO,**兩個模組的 entity 在同一個組件裡所以編得過**, 但這條相依在專案層看不出來,改 `OFDM053` 的 Model 會打到 `TRPM101`。

### 8.6 用到的共用元件

| 元件 | 用途 | 誰用 |
|---|---|---|
| `BasicFSK_PO`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs`) | 券商 / 幣別下拉 | 全庫 |
| `SerialNo.GetSrIdNoForOTA`(無原始碼,從呼叫端反推) | OTA 軌取號 | `OFDM221C` `OFDM231B` `OFDM551` `OFDM554` |
| `CRReportTransfer.TransferFileByte`(無原始碼,從呼叫端反推) | 回傳 `.rpt` byte | 三支 R |
| `UIExcelHelper` + `Microsoft.Office.Interop.Excel` | 用戶端產 Excel | `OTAR901` |
| `VirtualReportFormUtility`(無原始碼,從呼叫端反推) | 一支畫面掛多張報表 | `IJPR611`(掛七組) |
| `CommonExceptionBlocker.HandleBusinessException` | 例外上報 | 幾乎每一支;`OFDM302B.BatchAdd` 的那一行**被註解掉** |

## 附錄 A. 資料表總表

「宣告處」是 PO 的 `xTableMapping` / `TableMapping`;沒有宣告處的是只在 SQL 裡出現的表。

### A.1 本片畫面直接維護的表(21 張,12 組)

主明細組成與宣告錨點見 §2.1,主鍵與欄位數見 §2.2,欄位中文名見 §2.3。 **21 張全部帶四眼欄位**(掃描器實測)。一句話清單:

`TRPARAMS` · `TRP011` · `BMS999` · `FSK005`(維護入口已死) · `OFD109`+`OFD110` · `OFD111`+`OFD112` · `OFD113` · `OFD220`+`OFD221` · `OFD251`+`OFD252`+`OFD253`+`OFD254` · `OFD281` · `OFD302` · `OFD551`+`OFD552` · `OFD554`+`OFD555` · `OFD561`+`OFD562` · `OFD605`

### A.2 只在 SQL 裡出現的表(讀,或由設定驅動)

| 表 | 用途 | 誰讀 / 寫 |
|---|---|---|
| `TRP001` | **申報平台設定檔,存的是 SQL 文字** | `TRPM001` `TRPM101` `TRPI001` |
| `TRP002` | 傳檔紀錄 | `TRPM001`(寫)、`TRPI001`(讀) |
| `TR202` / `TR206` / `TR207` | 收檔 INSERT 語法 / 欄位對照 / SP 名稱 | `TRPM101` |
| `TRPM101T1` | 收檔暫存,寄信名單來源 | `TRPM101` |
| `OFD062` | 境外基金公司 | 四支取 `TRADE_ID`;`TRPI001` / `OFDM302B` 取名稱 |
| `OFD081` | 境外基金主檔 | `OFDM221C` / `OFDM231B` 交易檢核;`OFDM302B` / `TRPM901` 取基金資料 |
| `OFD085` / `OFD086` / `OFD091` | 基金轉換 / 配現可再投資 / ISHARE 額度 | `OFDM113` `OFDM221C` `OFDM231B` |
| `OFD300` / `OFD303` / `OFD304` | 集保匯率 / 結帳控制 / 受益人結餘 | `OFDM221C` `OFDM231B` |
| `OFD601` / `BMS001A` | 電子交易序號 / 受益人基本資料 | `TRPM101` 寄信名單 |
| `FSK003` / `OFD068` | 幣別 / 銷售機構 | `OFDM302B` / `FSKM004` |
| `LOG041` · `BMS926A` · `OFD123A` 等 `EC` 系列 | 電子交易紀錄、稅務居住地、風險屬性 | `IJPR611` |

### A.3 掃描器不會算進來的兩類

1. **設定即程式的四張表**(`TRP001` / `TR202` / `TR206` / `TR207`)不在任何 `xTableMapping` 裡,掃描器不會把它們列為本片的實體表。

2. **14 張收檔媒體格式表**(`TTP019TMP`、`TTP111TMP`、…、`TTP12ATMP`、`TTP12CTMP`)的表名是**執行期從 `TRP001.TableName` 讀出來的**,程式裡完全看不到字面值。它們的存在只能從 `DB/SP/` 的 SP 檔名反推(附錄 B)。

## 附錄 B. SP / Function / Trigger / View

### B.1 本片明確叫到的 SP

| SP | 誰叫 | 在版控 |
|---|---|---|
| `S_OTA_TRPM901_EXE` | `TRPM901` 月報製作 | `DB/SP/S_OTA_TRPM901_EXE.SQL` ✔ |
| `S_OTA_TRPR001_GET` | `TRPR001` 報表 | `DB/SP/S_OTA_TRPR001_GET.SQL` ✔ |
| `S_OTA_OFDM231B_EXE_ADD` | `OFDM231B` 新增沖銷 | `DB/SP/S_OTA_OFDM231B_EXE_ADD.SQL` ✔ |
| `S_OTA_OFDM231B_EXE_MOD` | `OFDM231B` 修改沖銷 | `DB/SP/S_OTA_OFDM231B_EXE_MOD.SQL` ✔ |
| `S_OTA_OFDR552_GET` | `OFDM551` 取契約變更(**報表的 SP 被維護畫面借用**) | `DB/SP/S_OTA_OFDR552_GET.SQL` ✔ |
| `S_OTA_OTAR901_GET` | `OTAR901` 報表 | **不在**(`refcheck-ignore`) |
| `S_TA_IMP_OFD300_RANGE` | `OFDM231B` 取匯率 | **不在**(`refcheck-ignore`) |

### B.2 執行期才決定名稱的 SP

`TRPM101` 用 `string.Format("S_OTA_{0}_GET", strTableSchemaName)` 組 SP 名 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:759`),`strTableSchemaName` 來自 `TRP001.TableName`。

`DB/SP/` 底下剛好有 **14 支**符合這個樣式的 SP,可以反推出收檔媒體格式的完整清單:

`S_OTA_TTP019TMP_GET` · `S_OTA_TTP111TMP_GET` · `S_OTA_TTP113TMP_GET` · `S_OTA_TTP114TMP_GET` · `S_OTA_TTP115TMP_GET` · `S_OTA_TTP116TMP_GET` · `S_OTA_TTP117TMP_GET` · `S_OTA_TTP118TMP_GET` · `S_OTA_TTP123TMP_GET` · `S_OTA_TTP124TMP_GET` · `S_OTA_TTP125TMP_GET` · `S_OTA_TTP126TMP_GET` · `S_OTA_TTP12ATMP_GET` · `S_OTA_TTP12CTMP_GET`

其中 `S_OTA_TTP12ATMP_GET` 對應的就是 §4.2 講的、會觸發寄信的 `TTP12A` 媒體。

`TR207.UPDSTP` 指定的入帳 SP 同樣是資料驅動,**程式裡完全看不到名字**,`DB/SP/` 也沒有可靠的樣式可以反推。

### B.3 Function

| Function | 誰用 | 在版控 |
|---|---|---|
| `TA_GETBUSINESSDAY` | `TRPM001` 推下一個傳檔營業日(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:556`) | **不在**(`DB/Function/` 只有 `F_OTA_GETFNBUSINESSDAY` 等,名字不同) |
| `TTP12ATMP_F1` / `TTP12ATMP_F2` / `TTP12ATMP_P2` | 沒有任何 `.cs` 叫它們;**推測**由 `TR202.INSERTSQL` 或 `TR207.UPDSTP` 在資料層叫 | `DB/Function/` ✔ |

### B.4 View

| View | 誰用 | 錨點 |
|---|---|---|
| `FNDV01` | `OFDM111` 的明細 SQL `LEFT JOIN` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:231`;`DB/View/FNDV01.SQL` ✔ |
| `OFD068A_V02` | 不是本片直接用,但它 join `FSK005`,改 `FSKM004` 的表要一起看 | `DB/View/OFD068A_V02.SQL` |

### B.5 Trigger

本片沒有任何程式提到 trigger。

## 附錄 C. 代碼對照

全部從程式反推,**沒有一項有權威來源**(代碼表不在 repo)。

| 分類 | 值 | 語意(反推) | 來源 |
|---|---|---|---|
| `TRP_TYPE` | `'A'` `'T'` `'R'` | 境外申報種類;`'R'` 時畫面才顯示基金公司欄 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:218-221` |
| `PERIOD` | `'M'` | 月;其他值走營業日 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:226-229` |
| `FILE_STYLE` | `'T'` | 傳檔;其他為收檔 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594` |
| `OMNIBUS_ID`(`OFD220` / `OFD221` / `OFD081` 檢核) | `'Y'` / `'N'` | 綜合帳戶 / 分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001` |
| `OMNIBUS_ID`(`OFD113`) | `'2'` / `'1'` | 綜合帳戶 / 分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:249` |
| `STATUS` | `'301'` | 已核准(**三碼,不是 `architecture.md §3` 假設的單字元**) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:209`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275` |
| `OFD113.DATA_ID` | `'2'` | 寫死,語意不明 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275` |
| `ALLOT_PROC_CODE` | `'D'` | 申購作廢 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |
| `ALLOT_CTL_CODE` / `ALLOT_CTL_CODE_O` | `>= '2'` | 已處理到下單確認之後 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1036` 與 `:1044` |
| `STOP_ID` | `'Y'` | 契約已終止 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| `NAV_LOCK` | `'Y'` / `'N'` | 淨值鎖定(下拉來源是 `YesNoDataSrc`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:282`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:246` |
| `IJPR611.PrintType` | `'0'` 到 `'6'` | 七式約定書,畫面只給 `'0'` 到 `'4'` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` |
| `EMAIL_CODE_EC` | `'07'` | 核印收檔通知信 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:729`〔客戶特定〕 |
| `MEDIA_NO` | `'TTP12A'` | 核印收檔媒體 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:670`〔客戶特定〕 |
| `UPD_USER` 樣式 | `'WebUser%'` | 網路下單帳號 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:943`〔客戶特定〕 |

## 附錄 D. 掃描母體與覆蓋率

本片跨四個模組前綴,**不適用 `atlas_scan.py --module` 的單模組覆蓋率**,改成 21 支逐一列表。

| # | 代號 | 專案 | 型別 | PO 基底 | 在 csproj | 本文處置 | 寫在哪 |
|---|---|---|---|---|---|---|---|
| 1 | `TRPM001` | `ATLAS.OTA` | M | 無基底(裸 DAO) | 是 | **已寫(深)** | §4.1 |
| 2 | `TRPM005` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 已寫 | §4.3 |
| 3 | `TRPM101` | `ATLAS.OTA` | M | 無基底(裸 DAO) | 是 | **已寫(深)** | §4.2 |
| 4 | `TRPM901` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 是 | 已寫 | §4.4 |
| 5 | `TRPI001` | `ATLAS.OTA.Query` | I | 無基底(裸 DAO) | 是 | **已寫(深)** | §5 |
| 6 | `TRPR001` | `ATLAS.OTA.Report` | R | 無基底(裸 DAO) | 是(檔名 `TRP001_PO.cs`) | 已寫 | §7.6 |
| 7 | `OTAM901` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.13 |
| 8 | `OTAR901` | `ATLAS.OTA.Report` | R | 無基底(裸 DAO) | 是 | 已寫 | §7.5 |
| 9 | `FSKM004` | `ATLAS.FSK` | M | **`BasicEVAPO`** | 是 | **已寫(深)** | §4.5 |
| 10 | `IJPR611` | `ATLAS.EC.Report` | R | 無基底(裸 DAO) | 是 | **已寫(深)** | §7.3、§7.4 |
| 11 | `OFDM109` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 12 | `OFDM111` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 13 | `OFDM113` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是(**cp950 來源檔**) | 表格帶過 | §4.9 |
| 14 | `OFDM221C` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | **已寫(深)** | §4.6 |
| 15 | `OFDM231B` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | **已寫(深)** | §4.7 |
| 16 | `OFDM251` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.9 |
| 17 | `OFDM302B` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 六層是,**兩支 `.rpt` 否** | **已寫(深)** | §4.11 |
| 18 | `OFDM551` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.10 |
| 19 | `OFDM554` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.10 |
| 20 | `OFDM561` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 21 | `OFDM602A` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 是 | 表格帶過 | §4.12 |

統計:

| 項目 | 數 |
|---|---|
| 畫面 | 21(M 16 / I 1 / R 3;**B 0**) |
| 專案 | 5(`ATLAS.OTA` 15 · `ATLAS.OTA.Report` 2 · `ATLAS.OTA.Query` 1 · `ATLAS.FSK` 1 · `ATLAS.EC.Report` 1) |
| 深寫 | 8 |
| 表格帶過 | 13 |
| 繼承 `BasicEVAPO`(死路徑) | **1**(`FSKM004`) |
| 不在 csproj 的檔 | **2 支 `.rpt`**(`OFDM302BRPS1` / `OFDM302BRPS2`);**沒有整支畫面不在 csproj** |
| 非 UTF-8 來源檔 | **1**(`OFDM113_PO.cs`,cp950) |
| 實體表 | 21 張(A.1 的 12 組,展開含明細) |
| 版控內 SP | 5;版控外 2;執行期決定名稱的 1 類(14 支可反推) |

本文另外提到但不屬於這 21 支的物件(列出以免被當成漏網): `OFDM221A` `OFDM221B` `OFDM231A` `OFDM302` `OFDM602` `OFDM053` `OFDM068` `OFDM113`(姊妹對照)、 `CLSR002` `OFDI058` `OFDI058B` `OFDB322` `OFDB323` `OFDB722` `OFDI011`(`OFD302` 的下游)、 `BMSM001` `BMSM006` `NFDR433` `NFDR435` `OFDM243` `OFDM243A` `OFDM385` `OFDB331`(`FSK005` 的下游)、 `IPJR607` `IPJR901`(`IJP` 的拼法對照)。

## 附錄 E. 讀本文時要注意的地方

嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 `catch` 吞例外 / 回傳值語意錯誤(本片最大宗)

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM001.GetErrDATA` 的 `catch` 是**空的**,失敗回 0 | **檢核 SQL 一出錯就等於「沒有錯誤」**,傳檔照傳。整支畫面的檢核機制建立在這個回傳值上 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:418-420` | **高** |
| `TRPM101.Execute` 的 `catch` 設了失敗訊息,但後面的 `if (i > 0)` 又把它蓋成「檢核成功」 | `i` 在例外發生前已被寫入影響列數,**例外被吞掉、畫面顯示成功** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:478-484` 對照 `:494-505` | **高** |
| `TRPM101` 另有 **8 個空 `catch`**(`GetMailData` / `GetResult` / `GetTR207` / `GetTR206` / `GetTR202` / `GetCheckFields` / `GetTableSchema` / `GetTRP001`) | 任一設定取不到都回 0,上層只說「無法取得 XXX」,真正的 DB 錯誤消失 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:742`、`:778`、`:813`、`:849`、`:885`、`:920`、`:975` | **高** |
| `FSKM004.CheckStkBrkData` 的 `catch` 回 `ReturnCode=false`,而 `false` 在這支的語意是「可以刪」 | **SQL 出錯等於放行刪除**(fail-open) | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186` | **高** |
| `OFDM221C.GetOFD113` 的 `catch` 是空的 | 配息設定查不到與查詢失敗無法區分,後續直接走 INSERT 新增一筆 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224` | 中 |
| `OTAR901.DoExp1` 的 `catch` 把所有例外壓成「商業邏輯異常!」,原文只 `Console.WriteLine` | WinForms 沒有主控台,**錯誤訊息完全消失** | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:357-362` | 中 |
| `OFDM302B.BatchAdd` 的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉** | 匯入失敗不進例外處理鏈,只把 `ex.ToString()` 丟給使用者看 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:239-245` | 中 |
| `TRPR001` / `TRPI001` 的查無資料回 `AddResultRow(false, 0, string.Empty)` | 使用者看到失敗但**沒有任何訊息** | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:84-87`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:105-111` | 中 |
| `TRPR001` 的 `catch` 第一行就 `tran.Rollback()`,而 `tran` 在 `try` 內才賦值 | 連線開不起來時 `NullReferenceException` 蓋掉真正的錯誤(與 `architecture.md §3` 記的 `BasicEVAPO.Add` 同型) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:91` | 中 |

### E.2 死檢核:外殼在、條件永遠不成立

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM302B.BatchAdd` 的 `if (i == -1)` 判刪除結果 | `ExecuteNonQuery` 回的是影響列數,**永遠不是 -1**;刪 0 筆與刪 500 筆都通過 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` | **高** |
| `TRPM901.BatchAdd` 同一個 `if (i == -1)` | 同上 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271-276` | 中 |
| `OFDM302B` 的「鎖定後不可改」檢核比 `NAV_LOCK == "1"`,而下拉只給 `Y` / `N` | **這道檢核永遠不會成立**,等於沒有 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160` 對照 `:246` | **高** |
| `TRPM901` 的「不開放刪除功能」整段被註解,訊息字串還留著 | 讀碼者會以為刪除被擋,**實際是開放的** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231` | 中 |
| `IJPR611` 的 `PrintType` `'5'` / `'6'` 分支(七層都備好、`.rpt` 都在 csproj) | 選項組只有 `'0'` 到 `'4'`,**兩式永遠選不到**,是死碼 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:213-218` 對照 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` | 中 |

### E.3 繞過四眼直接寫主檔

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM302B.BatchAdd`:`DELETE OFD302 WHERE NAV_DATE = ?` 再 INSERT,`STATUS` 寫死 `'301'`、四眼六欄全塞同一人同一時間 | **刪除條件只有淨值日期**,匯入一家基金公司的檔會把當天所有基金的淨值刪光;而且匯入即生效即核准。`OFD302` 的下游包含結算報表與多支批次 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:191-192` 與 `:208-209` | **高** |
| `OFDM302B.Update_NAVLOCK`:直接 `UPDATE OFD302 SET NAV_LOCK, UPDATEID, UPDATEDATE` | 鎖定 / 解鎖不留四眼軌跡,誰解鎖只看得到 `UPDATEID` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:471-478` | **高** |
| `OFDM221C` 的 `AfterAdd` / `AfterUpdate` 自組 `INSERT INTO OFD113 … STATUS='301'` | `OFD113` 有自己的四眼維護畫面 `OFDM113`;**同一張表兩種治理強度**,資料上分不出來 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276` 與 `:353-354` | **高** |
| `TRPM901.BatchAdd`:`DELETE TRP011 WHERE CAL_YM=? AND FH_CD=?` 再 INSERT,`STATUS='301'` | 刪除條件有兩欄比 `OFDM302B` 安全,但同樣繞過四眼 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282` | 中 |

### E.4 交易邊界

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM101.Execute` 開了 `tran`,但寫暫存表那行 `ExecuteNonQuery(cmd)` **沒帶 `tran`** | **rollback 收不回已寫進去的暫存資料**;同一支的 `ImportData` 是帶 `tran` 的 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459` 對照 `:646` | **高** |
| `OFDM302B.Update_NAVLOCK` 對同一個 `DbCommand` 連續 `ExecuteNonQuery` **兩次** | 每列多打一次 DB;`i == 0` 的檢核判的是第二次的結果 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:493` 與 `:495` | 中 |
| `TRPR001` 是純查詢卻開交易 | 報表查詢佔用交易,`CommandTimeout = 0` 時可能長時間卡住 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:61` 與 `:68` | 低 |

### E.5 Oracle 三值邏輯與 JOIN

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM221C.GetOFD091`:`OFD221.ALLOT_PROC_CODE <> 'D'` **沒有 `NVL`** | 處理代碼是 NULL 的申購不計入已用額度,**ISHARE 額度被低估**,該擋的申購放行 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` | **高** |
| `OFDM109.GetCRNCY_CD`:`CRNCY_CD <> 'TWD'` 沒有 `NVL` | 幣別為 NULL 的部位被靜默濾掉,幣別下拉少選項 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:466` | 中 |
| `TRPI001`:`INNER JOIN TRP001` | 設定被刪或改名,對應的**歷史傳檔紀錄整筆消失**,無提示。同一段 SQL 的下一行卻用了 `LEFT JOIN` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81` | **高** |
| `TRPM101.GetMailData`:`TRPM101T1 INNER JOIN BMS001A INNER JOIN OFD601` | 受益人資料或電子交易序號缺一,**這個人就收不到核印通知信**,而且沒有提示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729` | **高** |
| `TRPI001` 用「名稱欄是不是 NULL」反推「有沒有指定基金公司」 | `FH_CD` 有值但 `OFD062` 查不到時,畫面顯示「所有境外基金公司」——**錯的資料長得像對的** | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:68-71` | 中 |

### E.6 邊界與索引

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM101` 的「欄位未定義在媒體格式」檢核寫成 `Schemarow.Length == 0 && intRow == 1` | **第 2 筆以後出現未定義欄位會直接 `IndexOutOfRangeException`**,訊息變成無意義的「例外錯誤, 請檢查」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:248` 對照 `:267` | **高** |
| `TRPM101` 的日期檢核用 `Substring(0,4)` / `(4,2)` / `(6,2)` | 長度不足 8 的字串直接丟例外,同樣被吃成「例外錯誤」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:329` | 中 |
| `TRPM001_ExecuteDataLoad` 直接取 `vdb.UIView.TRP001[0]` | 查詢 0 筆時 index out of range | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:270` | 中 |
| `TRPM001.ExcuteSQLandLoadData` 在 `Result.Count == 0` 的分支裡還去讀 `Result[0].ReturnMessage` | 要報錯的時候先自己丟 index out of range | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:512-516` | 中 |
| `OFDM231B` 的 UI 兩處 `Select("FUND_ID <> ''")[0]` 沒有長度檢查 | 明細全空時例外 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488`、`:498-499` | 中 |
| 五支畫面的 `do { 取號 } while (IsExistByData(...))` **沒有次數上限** | 撞號或 `IsExistByData` 恆真時無窮迴圈,卡住整條遠端執行緒(與 `architecture.md §3` 記的 `CASM001_PO` 同型) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:162-166`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:141-182` | 中 |

### E.7 SQL 字串串接與寫死值

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM251` 的查詢條件把使用者輸入串進 `LIKE`:`RECORD_DATE LIKE '" + Row.Value + "%'` | **本片唯一一處使用者輸入直接進 SQL**;值含單引號就壞掉或被利用 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182` | **高** |
| 八支 `OFDM*` 的明細 SQL 都用字串串接接書號 | 書號由伺服器產生,注入風險低,但與同一支裡的參數化寫法不一致 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:256`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:434`、`:580`、`:631` | 低 |
| `IJPR611` 用字串串接組 `DataTable.Select` 過濾式 | 銀行名稱含單引號就丟 `SyntaxErrorException` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:586` | 中 |
| 傳檔落地路徑有**兩個不同的寫死預設值**:UI 端 `C:\境外傳檔\`、SQL 端 `'C:\'` | 同一個「沒設定」情境,兩邊給出不同的路徑 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:358-360` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:584` | 中 |
| `TSCD_RPT_PATH=` 這個前綴在三個地方各寫一次 | 改字面值要同時改三處,對不上時是例外不是訊息 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:137`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356` | 中 |
| `RESERVE_FIELD_SW` 欄名寫死在逗號轉換邏輯裡 | 媒體格式改欄名,轉換規則就失效 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:259-264` | 低 |
| `TTP12A` / `'07'` / `'WebUser%'` 寫死 | 換站台要逐一確認 | §附錄 C〔客戶特定〕 | 中 |

### E.8 成對路徑只改一邊

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `IJPR611` 的預覽有 `Parameters.Clear()`、列印**沒有** | 先預覽再列印,參數被加第二次 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:157` 對照 `:170-207` | 中 |
| `TRPM101` 的 `Execute` 不帶 `tran`、`ImportData` 帶 | 同一支畫面兩條路徑的交易語意不同 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459` 對照 `:646` | 高(已列 E.4) |
| `OFDM551` 與 `OFDM554` 各寫一份 `GetOFD562`,SQL 不同 | 改扣款帳戶取數邏輯要記得兩邊 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:385` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:455` | 中 |
| `OFDM231B` 的 `OFD253` 分支,region 標題複製自 `OFD252` 沒改 | 讀碼會以為在看 `OFD252`;`case` 的註解是對的、`region` 是錯的 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:437` 對照 `:438` | 低 |

### E.9 檔案與建置

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `FSKM004_PO` 繼承 `BasicEVAPO` 且不覆寫 `Add` / `Update` / `Delete`,`BeforeSelect` 第一行就用 `dbTA` | 依 `architecture.md §3`,**按查詢就 NRE**,整支畫面不可用;而 `FSK005` 的下游遍布全庫 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29` 與 `:60` | **高** |
| `FSKM004_PO` 的活程式裡還有 T-SQL 的 `SUBSTRING(...)` | 就算連線修好,這段在 Oracle 上也是語法錯誤 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:114` | **高** |
| `FSKM004_PO` 1,272 行裡 950 行是被 `/* */` 包起來的上一代實作 | 讀碼成本;搜尋命中大量死碼 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270` | 中 |
| `FSKM004_PO` 最後一行是 `}//end namespace Adapterusing System;` | 兩段文字黏在一起,顯示這個檔曾被截斷或貼壞 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:1272` | 低 |
| `FSKM004_Ctl` **沒有繼承 `BaseController`**,每個方法自己 `new` PO | 不走 `DataAccessPool`、沒有 `InitializeVDBTypes()`,全片唯一 | `Dev/ATLAS.FSK/Source/Control/Control.FSK/FSKM004_Ctl.cs:13` 與 `:36-41` | 中 |
| `OFDM302BRPS1.rpt` / `OFDM302BRPS2.rpt` 在一個**沒有 csproj 的資料夾**裡,既不是 `EmbeddedResource` 也沒有 PostBuild xcopy | **兩張報表在現行建置流程下不會被部署**,而 UI 用名字去要它們 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:342` 與 `:396` | **高** |
| `TRPR001_PO` 住在檔名少一個 `R` 的 `TRP001_PO.cs` | 編得過、跑得動,但依檔名比對的工具全部誤判「缺 PO」 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:2` 與 `:31` | 中 |
| `OFDM113_PO.cs` 是 **cp950 編碼**,全片唯一 | 用 UTF-8 一刀切的工具讀它會出亂碼;訊息字串在版本比對時也會誤判 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:235` | 中 |
| `TRPM101_PO` 有一個方法的參數型別是**別支畫面的 ModelVDB**(`OFDM053ModelVDB`) | `TRP` 的 PO 直接相依 `OFD` 的 typed DataSet 與 PO,專案層看不出來 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:710` | 中 |
| `TRPM001_PO` 與 `TRP001_PO` 的介面 XML 註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製殘留,與實際用途完全無關 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:23` 與 `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:22` | 低 |
| `TRP001_PO` 同時 `using System.Data.OracleClient;` 與 `Oracle.ManagedDataAccess.Client;` | 前者是已淘汰的內建 provider | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:11` 與 `:16` | 低 |

### E.10 商業規則不在程式裡

| 事實 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM001` 的檢核與異動 SQL 全部存在 `TRP001` 的 13 個欄位裡,程式只負責照跑 | **讀程式讀不出任何一條傳檔規則**;改規則不用改程式、也不會進版控 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582` | **高** |
| `TRPM101` 連 INSERT 語法都存在 `TR202.INSERTSQL`,取出時要用三層 `REPLACE` 反跳脫 | 跳脫規則沒有任何文件;改 `TR202` 的人必須知道 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:868` | **高** |
| 收檔用的表名與 SP 名都是執行期從 `TRP001` / `TR207` 讀出來的 | 程式裡看不到 14 張媒體格式表的名字,只能從 `DB/SP/` 的檔名反推(附錄 B.2) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:759` | 中 |

### E.11 標「假設」的地方一覽

| # | 假設 | 依據 | 在哪 |
|---|---|---|---|
| 1 | 四個前綴的業務範圍 | 表名、`msdata:Caption`、彈出視窗標題、報表中文名 | §0.1 |
| 2 | `OFDM221B` 是 `OFDM221A` 的子視窗或殘留 | 只有 UI 一層,不在畫面代號母體內 | §0.3 |
| 3 | 傳檔週期由 `TRP001.PERIOD` 決定(`'M'` 為月) | 程式對 `'M'` 走 `ADD_MONTHS`、其他走 `TA_GETBUSINESSDAY` | §1.5 |
| 4 | `'301'` 是 `EVAStatusCode.ApproveAdd` 的實際字面值 | 四支不同模組都在「繞過四眼直接寫入」時用它 | §2.5 |
| 5 | `IJPR611` 的第 6、7 式曾開放過或是預留 | 註解把 7 種寫齊、七層都備好,只有 Designer 少兩個選項 | §7.3 |
| 6 | `TTP12ATMP_F1` / `F2` / `P2` 由 `TR202` / `TR207` 在資料層叫 | 沒有任何 `.cs` 引用它們,但名字與 `TTP12A` 媒體一致 | 附錄 B.3 |
| 7 | `OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品 | 兩者讀寫同一張 `OFD605`,而 `OFDM602_PO` 整個類別被註解 | §8.1 |
| 8 | `FSK005` 只能靠 DB 直改或別的途徑維護 | `FSKM004` 這個唯一入口按查詢就 NRE | §4.5 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `TRP` 6 支、`OTA` 2 支、`FSK` 1 支、`IJP` 1 支、`ATLAS.OTA` 裡的 `OFD` 11 支,合計 21 支。 |

由 build_doc.py v2.0.0 於 2026-09-15 20:02 產生 · 標題 147 · 圖 5 · 表格 98 · 程式錨點 372 · § 連結 73 · 引用檢查：畫面 50（缺 0） · Table 40（缺 0） · SP 19（缺 0） · Function 4（缺 0） · View 2（缺 0） · 結果集 5（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
