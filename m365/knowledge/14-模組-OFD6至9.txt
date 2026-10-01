ATLAS 知識庫 — 14-模組-OFD6至9

本檔合併以下文件:modules/ofd6.md、modules/ofd7.md、modules/ofd8.md、modules/ofd9.md


============================================================
【文件】kb/modules/ofd6.md
============================================================

# ATLAS OFD6 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先看 §0.2 的一句話結論(本片有八支畫面是死的),再翻 §1 的圖抓全貌,§2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。**急著知道哪些畫面不能碰的人直接跳 §3.1 的「PO 基底」欄與附錄 E.1。**

> ⚠ **OFD6 不是一個業務模組,是一份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/` 這個 Entity 專案底下的 **20 支 M 畫面**。切片依據是 Entity 專案資料夾,不是業務;所以本片內部含**四條互不相干的業務線**(§0.1)。名稱 `OFD6` 為**推測**,取自資料夾名。

> ⚠ **本片的業務意義**(§0)由表名、`DB/Table/` 的 `comment on table`、欄位 `msdata:Caption`、`Designer.cs` 內的標籤文字(以 `grep` 取出,未整檔閱讀)與 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的常數字典**推測**,待選單表回填。

> ⚠ **〔客戶特定〕**:`CTL014` 的 `SourceType` 數字碼(`'007'` `'062'` `'063'` `'107'` `'404'` `'455'`)、境內外代碼 `'1'` / `'2'`、`OFD161` 的 `2099/12/31` 上限、`OFD163` 的「00:00 不可任意調整」為本站台的值。

> ⚠ **〔共用〕**:`OFD114A` `OFD115A` `OFD123A` `OFD124` `OFD125A` `OFD126A` `OFD127` `OFD129A` `OFD135A` `OFD152A` `OFD153A` `OFD163` `HIGHRISK_COUNTRY` 同時服務 BMS / CLS / COD / EC / NFD / OFDB / OFDI / OFD.Query / RSP 或 Common 共用 PO(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層與命名看 `architecture.md §2`、四眼(EVA)與 PO 基底看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 20 支畫面管什麼(推測)

先給結論:**本片沒有單一業務主題。它是「受益人與基金的各種例外設定」這個大主題底下的四塊,而且四塊的程式世代差距非常大**——同一個資料夾裡同時放著 SQL Server 時代的遺物與高齡金融消費者條款。

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 客戶身分審查(AML / KYC)** | `OFDM115A` `OFDM122A` `OFDM123` `OFDM123A` `OFDM125A` `OFDM157` | 誰要列管、自主聲明書、KYC 風險屬性問卷、投資屬性調查表、董監事與實質受益人名單、高風險國別 | `DB/Table/Create_OFD122A.sql` 的 `comment on table` 寫「自主聲明書資料檔」、`DB/Table/create_OFD125A_M.sql` 寫「董監事設定主檔資料」、`HIGHRISK_COUNTRY` 的 `RISK_LEVEL` Caption「風險等級」 |
| **B 受益人層交易例外** | `OFDM114` `OFDM127` `OFDM128` `OFDM129` `OFDM133` `OFDM135` | 針對「某一位受益人」開的例外:停止交易、公告金額、個別交易門檻與費率、歸戶、交易指示代理人 | 主鍵一律含 `BF_NO`;`DB/Table/createOFD135A.sql` 寫「交易指示代理人設定資料」 |
| **C 基金層交易控制** | `OFDM154` `OFDM155` `OFDM156` `OFDM161` `OFDM163` `OFDM164` | 針對「某一檔基金」的控制:停止交易、可轉換對應、金額門檻、定期買回排程與買回率 | 主鍵一律含 `FUND_ID`(`OFDM163` 除外,它是全基金共用的一顆時間參數) |
| **D 系統參數與查詢權限** | `OFDM126` `OFDM151` | 行銷說明文字;查詢群組(哪些員工可以查哪些基金) | `OFD126A.ST_MO` Caption「行銷說明」;`OFDM151` 的兩張明細分別掛 `COD009`(員工)與 `OFD081A`(基金) |

四塊之間**沒有任何程式呼叫**。真正把它們接起來的是別的模組:`BMSM001`(開戶)讀 A 塊的 `OFD123A`、Common 的 `BasicOFD_PO` 讀 B 塊的 `OFD125A` / `OFD135A`、`OFDB161`(定期買回計算)吃 C 塊的 `OFD163`。讀 OFD6 的人如果預期整片是一條流程,會在 §4.7 之後完全對不上——先知道這件事比較省時間。

### 0.2 一句話結論:20 支裡有 8 支連查詢都跑不起來

這是本片最重要的一件事,寫在最前面。

`architecture.md §3.1.1` 已查證:`BasicEVAPO` / `MultiRowEVAPO` 的 `dbTA` 宣告即 `= null`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`),建構子裡建立連線那四行**整段被註解**(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:164-172`),而基底 `Add()` 第一行就 `cn = dbTA.CreateConnection();`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`)。

本片有 **8 支**畫面繼承這兩支基底:`OFDM123` `OFDM127` `OFDM128` `OFDM154` `OFDM155` `OFDM161` `OFDM163` `OFDM164`。逐支確認的結果比 `ofd8.md`(7 支)與 `ofdb.md`(4 支)記的更糟:

| 追問 | 本片的情況 |
|---|---|
| 有沒有哪一支自己賦值 `dbTA` / `dbPTPF`? | **一支都沒有**。實掃 8 個檔的 `dbTA *=` 與 `dbPTPF *=`,零命中 |
| 有沒有覆寫 `Add` / `Update` / `Delete`? | 只有 `OFDM127` 覆寫(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:311`、`:503`、`:552`,原始註解就寫「抄EVA PO」),其餘 7 支完全不覆寫 |
| 覆寫了就沒事嗎? | **只擋掉一半。**`OFDM127` 的 `Add`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:568`)與 `Delete`(`:514`)改用 `db` / `db_ToDo`(繼承自 `Basic_PO`,**無原始碼,從呼叫端反推**,是否非 null 無法從 repo 判斷);但 `Update`(`:317`、`:321`)與 `Select`(`:413`)仍然直接用 `dbPTPF` / `dbTA`,`CheckAnnounce` 也是(`:232`)。**修改與查詢照樣 NRE。** |
| 那查詢呢? | **也不行**。8 支的 `BeforeSelect` 第一件事都是 `args.DbCmd = dbTA.GetSqlStringCommand(strSQL);`(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:36`)。`dbTA` 是 null,**按「查詢」就炸,連清單都列不出來** |

**推得的結論:這 8 支不是「存檔會 NRE」,是整支畫面從查詢就進不去。**與 `ofd8.md` / `ofdb.md` 的版本相比,本片多出「連 `BeforeSelect` 都踩到」這一條,因為這 8 支全部都在 `BeforeSelect` 裡用 `dbTA` 組 `DbCommand`(`OFDM163` 例外——它連 `BeforeSelect` 都沒掛,見 §4.19)。

> **這是讀碼結論,沒有實跑過**(同 `architecture.md §3.1.1` 的但書)。要推翻它得證明 `dbTA` 在別處被賦值——本片 8 個檔剝註解後掃過,沒有。

旁證同樣成立:這 8 支的 SQL 幾乎全是 T-SQL,不是 Oracle:

| 畫面 | T-SQL 痕跡(實際命中次數) | 錨點 |
|---|---|---|
| `OFDM123` | `[OFD124]` 50 · `[OFD125]` 34 · `newid()` · `SELECT TOP 1` · `Convert(nvarchar(10),…,111)` · `GetDate()` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:250`、`:447`、`:540`、`:599-600` |
| `OFDM127` | `[OFD127]` 30 · `ISNULL(` 6 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:241` |
| `OFDM128` | `[OFD128]` 40 · `isnull(` 10 · `[OFD081]` 8 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM128_PO.cs:88` |
| `OFDM154` | `[OFD154]` 6 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:100` |
| `OFDM155` | `[OFD155]` 8 · `ISNULL(` 3 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM155_PO.cs:96` |
| `OFDM161` | `SqlDbType` 42 · `INSERT INTO [OFD162]` · `@FUND_ID` 具名參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:129`、`:227` |
| `OFDM163` | 無 SQL(整支 PO 只有 25 行) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM163_PO.cs:8-24` |
| `OFDM164` | `SqlDbType` 3 · `[OFD164]` 2 · `@BNG` / `@END` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:176`、`:190-192` |

ATLAS 現行資料庫是 Oracle(`architecture.md §8.2`:三個 Oracle provider),Oracle 不吃方括號識別字、不吃 `@參數`、沒有 `newid()` / `GetDate()` / `ISNULL()` / `SELECT TOP`。**這 8 支是 SQL Server 時代沒遷過來的舊畫面,合理的解讀是早就沒在用。**

反面對照組就在同一個資料夾:`OFDM125A_PO` 第 28 行留著 `//public class OFDM125A_PO : BasicEVAPO`,第 30 行才是現行的 `public class OFDM125A_PO : BaseEVADaoPO, IOFDM125A_PO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:28-30`)。**這一行註解就是遷移的證物**:同一批畫面,有的被遷走了,有的沒有。

### 0.3 不管什麼

| 不在 OFD6 | 在哪 | 依據 |
|---|---|---|
| KYC 問卷的**題庫與版本維護** | `OFDM741` / `OFDM742` / `OFDM743`(`DataEntity.OFD9`) | `OFDM123_PO` 只讀 `OFD741`~`OFD745`,寫入者是 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM741_PO.cs` 這一組 |
| 受益人主檔建檔 | `BMSM001`(BMS 模組) | `OFD123A` 被 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs` 讀 |
| 定期買回**實際算錢與產生指示** | 批次 `OFDB161` | `OFD163` 的唯一其他引用者是 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs` |
| 受益人交易條件一次建檔 | 批次 `OFDB004` | `OFD129A` 被 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs` 一起建 |
| 高風險國別**實際套用到客戶** | Common 共用 PO,透過 view `V_TA_HIGHRISK_COUNTRY` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69`、`:75` |
| 這 20 支的**查詢版畫面** | `OFDI011` / `OFDI058` / `OFDI907`(`Dev/ATLAS.OFD.Query` 與 `Dev/ATLAS.OFDI`) | 見 §8.2 |
| 報表 | `OFDR285` / `NFDR022` / `NFDR074` | 見 §7 |

### 0.4 使用角色

20 支全部是 M 維護畫面,全部宣告走標準四眼(輸入 / 驗證 / 覆核),角色由平台的 ToDo 機制指派,OFD6 自己不定義角色。詳見 `architecture.md §3`。

**但「全部走四眼」這句話要打三個折**:

| 折扣 | 內容 | 錨點 |
|---|---|---|
| **8 支根本跑不起來** | §0.2 的那 8 支,四眼對它們沒有意義 | 見 §0.2 |
| **`OFDM151` 的 ToDo 查詢字串是死碼** | `BuildMasterSQLString(model, isToDoString)` 兩個呼叫點都傳 `false`,而且 `BeforeGetToDoData` **沒有被訂閱**,所以 `xTableHelper.AppendToDoString` 永遠不會執行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:64`、`:78`、`:192-195`;訂閱清單在 `:35-36` |
| **`OFDM154` 寫了兩個事件處理器卻沒接上** | `OFDM154_PO_BeforeGetMaintainData` 與 `OFDM154_PO_BeforeGetToDoData` 兩個 private 方法都在,建構子只接了 `BeforeSelect` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:18` vs `:40`、`:51` |

本片**沒有**任何繞過四眼的批次匯入入口(對照 `ofd7.md §0.3` 的三個狀態寫死入口),也沒有任何一段程式直接寫 `STATUS` 字面值。

### 0.5 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(讀) | `BMS001A` / `BMS001`(受益人)、`OFD081A` / `OFD081` / `OFD081V`(基金)、`COD009`(員工)、`OFD002`(部門)、`OFD068`(銷售機構)、`CTL014`(代碼字典)、`CTL015`(KYC 有效月數)、`OFD741`~`OFD747`(KYC 題庫) | 幾乎全部是 `LEFT JOIN` 或 `RIGHT OUTER JOIN`,只取說明欄;**唯一例外**是 `OFDM123` 對 `BMS001` 用 `INNER JOIN`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:251`),沒有受益人主檔的 KYC 資料會直接消失(§4.3) |
| 下游(本片的表被誰讀) | `BMSM001` / `BMSM006`、Common 的 `BasicOFD_PO` / `BasicBMS_PO` / `Utility_PO`、`OFDB004` / `OFDB161` / `OFDB331`、`OFDI011` / `OFDI058` / `OFDI907`、`CLSM002` / `CODM006`、`OFDR285` / `NFDR022` / `NFDR074`、EC 的 `IPJB622` / `OFDB602`、`RSPB009` | 見 §8 |
| 平行(同一張表兩個維護入口) | 沒有。本片 20 支各自獨佔自己的主檔 | 對 23 張表逐張跑 `atlas_scan --table`,「主檔於」欄都只有一支 |

### 0.6 全域開關

本片沒有 `App.config` 層級的業務開關:`Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:682-828` 這 20 段只有 `mastertable` / `detailtable` / `ugrdResult` 三種 `PluginData`,全是 UI 綁定設定。真正決定行為的是三個資料欄位:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `FUND_TYPE`(基金資料來源) | `'1'` 境外 · `'2'` 境內 | 只有 `OFDM114` 與 `OFDM156` 兩支用它切基金主檔來源。值域出處 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301`(`SHORE_ID.OffShore = "1"` / `SHORE_ID.OnShore = "2"`) | 兩支畫面的「境內基金 / 境外基金」標籤(以 `grep` 取自 Designer) |
| `SOURCE_CD`(資料來源,`OFDM123A` 專用) | `'1'` 線上 · `'2'` 後台 · `'3'` 郵局(取自 `CTL014` 的 `SourceType='455'`) | `'1'` 時戶號欄唯讀且**禁止刪除**;新增時選 `'1'` 直接擋;`'3'` 時跳過一整組檢核 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:39`、`:105-108`、`:409-411`、`:419`、`:670` |
| `RISK_LEVEL`(高風險國別的風險等級) | 程式未列舉,預設值 `'L'` | Common 端寫 `NVL(V_TA_HIGHRISK_COUNTRY.RISK_LEVEL,'L')`,查不到國別就當低風險 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69` |

**`SOURCE_CD` 在 OFD 模組有兩個完全不同的意思**,這是最容易看錯的一件事:`OFDM123A` 的 `SOURCE_CD` 是「資料來源(線上 / 後台 / 郵局)」,而 `ofd7.md §0.5` 講的 `SOURCE_CD = SHORE_ID.OnShore` 是「境內外」。**同名不同義,不要跨片套用。**

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD6 全景:客戶身分審查、受益人層例外、基金層控制、系統參數四塊二十支畫面,以及八支死畫面的成因
圖中文字:A 客戶身分審查(AML / KYC):六支,兩套問卷並存 / OFDM115A / OFD115A+OFD116A 列管名單 / OFDM122A / OFD122A 自主聲明書 / OFDM123A / OFD123A+OFD124A 投資屬性 / OFDM123 / OFD124+OFD125 舊KYC 死 / OFDM125A / OFD125A_M+OFD125A 董監事 / OFDM157 / HIGHRISK_COUNTRY 高風險國別 / BMS001A / BMS001ACHG / 只有 OFDM123A 會寫回 / B 受益人層交易例外:主鍵一律含 BF_NO / OFDM114 / OFD114A 停止交易 / OFDM129 / OFD129A 交易條件與費率 / OFDM133 / OFD133A 歸戶 / OFDM135 / OFD135A 交易指示代理人 / OFDM127 / OFD127 公告金額 死 / OFDM128 / OFD128 分基金公告金額 死 / Common BasicOFD_PO / 讀 OFD125A OFD127 OFD135A / C 基金層交易控制:六支裡五支是死的 / OFDM156 / OFD156A+OFD157A 金額門檻 / OFDM154 / OFD154 停止交易 死 / OFDM155 / OFD155 可轉換對應 死 / OFDM164 / OFD164 買回率 死 / OFDM161 / OFD161 定期買回排程 死 / OFD162 / 排程展開 無四眼 / OFDM163 / OFD163 自動發送時間 死 / OFDB161 定期買回計算 / 讀 OFD163 畫面卻是死的 / D 系統參數與查詢權限:兩支 / OFDM126 / OFD126A 行銷說明 / OFDM151 / OFD151A+OFD152A+OFD153A / OFDI058 / BasicOFD_PO / 查詢權限判定吃 152A 153A / OFDR285 NFDR074 / 行銷說明報表 / 共同體質:20 支裡 8 支繼承 BasicEVAPO / MultiRowEVAPO,連查詢都 NRE / BasicEVAPO.dbTA = null / 建構子建立連線整段被註解 / 8 支子類無一賦值 / OFDM123 127 128 154 155 161 163 164 / SQL 仍是 T-SQL / 方括號 newid SELECT TOP SqlDbType
```

*圖:圖 1 OFD6 全景。橘框=活的維護入口;橘虛框=繼承 BasicEVAPO 的死畫面或風險;灰虛框=別的模組的用法;黑框=無原始碼或版控外。四塊之間沒有任何程式呼叫,真正把它們接起來的是 BMS、Common 共用 PO 與 OFDB 批次。最下面那一排是本片的核心事實:40% 的畫面從查詢就進不去。*

### 1.2 資料表關係

圖放在 §2 的開頭(`ofd6.figs.py` 的 `h2:2-`)。重點看兩件事:**`OFD123A`/`OFD124A` 與 `OFD124`/`OFD125` 是兩套毫不相干的問卷**(§4.3 與 §4.4 會證明),以及**只有五支畫面真的有明細表**。

### 1.3 主要維護畫面的四眼與卡控順序

圖放在 §3 的開頭(`h2:3-`)。一句話總結:**本片的畫面先照 PO 基底分成「活的 12 支」與「死的 8 支」兩群,再談卡控;死的那群連查詢都進不去,它們的卡控寫得再漂亮也不會被執行。**

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。與批次的關係是單向的:`OFDB161`(定期買回計算)讀 C 塊的 `OFD163`、`OFDB004` 與 `OFDB331` 讀 B 塊的 `OFD129A`。本片沒有任何一支畫面呼叫批次,也沒有任何批次寫回本片的表。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——20 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM161`:它在 `AfterAdd` / `AfterUpdate` 裡**把未來每一期的執行日期全部展開寫進 `OFD162`**(§4.18),但展開的結果要等 `OFDB161` 批次才會被消費,而 `OFDB161` 不在本片,無法畫完整泳道。

## 2. 資料模型

```text
[圖] OFD6 二十三張表的分組、兩套 KYC 問卷的並存,以及「缺四眼欄位」與「死畫面」的完全重合
圖中文字:A1 兩套 KYC 問卷:OFD123A 系與 OFD124 系,相似度不到 12% / OFD123A 123 欄 / PK 訪談日+公司+統編 / OFD124A 30 欄 / 實質受益人 PEP 三問 / BMS001A / BMS001ACHG / AfterApprove 寫回 / Oracle 世代 / BaseEVADaoPO 活 / OFD124 41 欄 / PK 問卷書號 無四眼欄 / OFD125 31 欄 / 逐題答案 無四眼欄 / OFD741~OFD745 題庫 / OFDM741 742 743 維護 / T-SQL 世代 / BasicEVAPO 死 / A2 其餘身分審查:主檔明細各自獨立 / OFD115A + OFD116A / 列管主檔與涵蓋基金 / OFD122A / 自主聲明書 明細宣告被註解 / OFD125A_M + OFD125A / _M 是實體表 PK 只有 BF_NO / HIGHRISK_COUNTRY / 唯一不照 OFDnnn 命名 / B 受益人層:六張表全部以 BF_NO 為鍵 / OFD114A / PK 戶號+基金+交易別+起日 / OFD127 / OFD128 / 公告金額 無四眼欄 / OFD129A 41 欄 / 被 OFDB004 OFDB331 共用 / OFD133A / OFD135A / ROW_NUMBER 抓群首 / C 基金層:OFD162 是唯一沒有四眼、由手寫 SQL 維護的表 / OFD154 / OFD155 / 停交 / 可轉換 無四眼欄 / OFD156A + OFD157A / 門檻類別與適用基金 / OFD161 / PK 基金 無四眼欄 / OFD162 / 排程展開 無四眼 無讀者 / OFD163 / 單列參數 xsd 無 PK 宣告 / OFD164 / PK 起日+基金 無四眼欄 / 八支死畫面的共同特徵 / Model 一律缺四眼 13 欄 / D 與外部唯讀:join 進來取說明,本片從不寫入 / OFD151A + OFD152A + OFD153A / 查詢群組 權限表 / COD009 / OFD002 / 員工 / 部門 / OFD081A / OFD081 / OFD081V / 境內 / 境外 / 檢視 三種取法 / CTL014 / OFD008 / 代碼字典 / 國別
```

*圖:圖 2 資料模型。橘框=活的主檔或維護入口;白框=明細;橘虛框=風險或死掉的那一群;灰虛框=別的模組的用法;黑框=外部唯讀。A1 是本片最容易誤解的地方——OFD123A 系與 OFD124 系不是境內外配對,是兩個世代的兩套問卷。C 區那一排「無四眼欄」與 §3 的「PO 基底標紅」是同一批畫面,零例外。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping` / `TableMapping`)

20 支畫面共宣告 **23 張實體表**。宣告用的類別分成兩派,對應 `architecture.md §3.1` 的兩個世代:

| 派別 | PO 基底 | 宣告用類別 | 本片畫面 |
|---|---|---|---|
| **新世代(活的)** | `BaseEVADaoPO` | `xTableMapping` | `OFDM114` `OFDM115A` `OFDM122A` `OFDM123A` `OFDM125A` `OFDM126` `OFDM129` `OFDM151` `OFDM156` `OFDM157` |
| **新世代多筆(活的)** | `BaseMultiRowEVADaoPO` | `xTableMapping` + `MasterPKey` | `OFDM133` `OFDM135` |
| **舊世代(死的)** | `BasicEVAPO` | `TableMapping` | `OFDM123` `OFDM127` `OFDM128` `OFDM154` `OFDM161` `OFDM163` `OFDM164` |
| **舊世代多筆(死的)** | `MultiRowEVAPO` | `TableMapping` + `MasterPKey` | `OFDM155` |

**`xTableMapping` 還是 `TableMapping`,是一眼分辨死活最快的方法**——比看基底名稱更顯眼,因為它就寫在建構子第一行。

逐支的宣告:

| 畫面 | 基底 | 主檔(實體表 → vdb 名) | 明細(實體表 → vdb 名) | 錨點 |
|---|---|---|---|---|
| `OFDM114` | `BaseEVADaoPO` | `OFD114A` → `OFDM114` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:38` |
| `OFDM115A` | `BaseEVADaoPO` | `OFD115A` → `OFDM115` | `OFD116A` → `OFDM115_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:43-44` |
| `OFDM122A` | `BaseEVADaoPO` | `OFD122A` → `OFDM122A` | —(`OFD124A` 的明細宣告**被註解**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:37-38` |
| `OFDM123` | `BasicEVAPO` | `OFD124` → `OFD124` | `OFD125` → `OFD125` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:37-38` |
| `OFDM123A` | `BaseEVADaoPO` | `OFD123A` → `OFDM123A` | `OFD124A` → `OFD124A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:37-38` |
| `OFDM125A` | `BaseEVADaoPO` | `OFD125A_M` → `OFDM125A_M_Master` | `OFD125A` → `OFDM125A_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:39-40` |
| `OFDM126` | `BaseEVADaoPO` | `OFD126A` → `OFD126A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM126_PO.cs:37` |
| `OFDM127` | `BasicEVAPO` | `OFD127` → `OFDM127` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:27` |
| `OFDM128` | `BasicEVAPO` | `OFD128` → `OFDM128` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM128_PO.cs:29` |
| `OFDM129` | `BaseEVADaoPO` | `OFD129A` → `OFDM129` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:44` |
| `OFDM133` | `BaseMultiRowEVADaoPO` | `OFD133A` → `OFDM133`;`MasterPKey` = `BF_NO` | —(多筆型無明細概念) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM133_PO.cs:26-27` |
| `OFDM135` | `BaseMultiRowEVADaoPO` | `OFD135A` → `OFDM135`;**沒有宣告 `MasterPKey`** | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:30` |
| `OFDM151` | `BaseEVADaoPO` | `OFD151A` → `OFDM151` | `OFD152A` → `OFDM151_EMP`;`OFD153A` → `OFDM151_FUND` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:37-39` |
| `OFDM154` | `BasicEVAPO` | `OFD154` → `OFDM154` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:17` |
| `OFDM155` | `MultiRowEVAPO` | `OFD155` → `OFDM155`;`MasterPKey` = `FUND_ID` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM155_PO.cs:18-19` |
| `OFDM156` | `BaseEVADaoPO` | `OFD156A` → `OFD156A` | `OFD157A` → `OFD157A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM156_PO.cs:29-30` |
| `OFDM157` | `BaseEVADaoPO` | `HIGHRISK_COUNTRY` → `HIGHRISK_COUNTRY` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:37` |
| `OFDM161` | `BasicEVAPO` | `OFD161` → `OFDM161` | —(`OFD162` 由 `After*` 手寫 SQL 維護,見 §4.18) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:20` |
| `OFDM163` | `BasicEVAPO` | `OFD163` → `OFDM163` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM163_PO.cs:13` |
| `OFDM164` | `BasicEVAPO` | `OFD164` → `OFDM164` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:20` |

> ⚠ **`OFD162` 不是宣告出來的明細。** `OFDM161_PO` 只宣告主檔;`OFD162`(定期買回展開後的每期執行日)是在 `AfterAdd` / `AfterUpdate` 裡**自己拼 `DELETE` + `INSERT INTO [OFD162]` 的 SQL 字串**寫進去的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:129`、`:227`)。它**不參與四眼**,xsd 裡也沒有四眼 13 欄。這是本片唯一一張「畫面會寫、但不歸四眼管」的表。

> ⚠ **`OFD124A` 同時是 `OFDM123A` 的明細,也曾經是 `OFDM122A` 的明細。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:38` 的 `//this.DetailTable.Add(new xTableMapping("OFD124A", "OFD124A"));` 整行被註解。**這代表「自主聲明書」與「投資屬性調查表」原本共用同一張實質受益人明細,後來拆開了。** 改 `OFD124A` 的欄位時要記得 `OFDM122A` 的 UI 可能還有殘留控制項。

### 2.2 主鍵與四眼欄位

「PK」欄取自對應 xsd 的 `xs:unique … msdata:PrimaryKey`,是 **DataTable 的鍵**,不保證等於 DB 上的 constraint(`architecture.md §5.5`)。「四眼 13 欄」欄位由 `atlas_scan --table` 判定。

| vdb 表 | 實體表 | PK(來源 xsd) | 四眼 13 欄 | 欄數 |
|---|---|---|---|---|
| `OFDM114` | `OFD114A` | `BF_NO` `FUND_ID` `STOP_TRADE_TYPE` `STOP_BNG_DATE` | 齊 | 24 |
| `OFDM115` | `OFD115A` | `FH_CD` `DATA_SEQ` | 齊 | 30 |
| `OFDM115_Detail` | `OFD116A` | `FH_CD` `DATA_SEQ` `FUND_ID` | 齊 | — |
| `OFDM122A` | `OFD122A` | `SET_DATE` `ID_NO` | 齊 | 22 |
| `OFD124` | `OFD124` | `KYC_ANS_NO` | **無** | 41 |
| `OFD125` | `OFD125` | `KYC_ANS_NO` `DATA_SEQ` | **無** | 31 |
| `OFDM123A` | `OFD123A` | `SET_DATE` `FH_CD` `ID_NO` | 齊 | 123 |
| `OFD124A` | `OFD124A` | `SET_DATE` `SRNO` `ID_NO` `FH_CD` | 齊 | 30 |
| `OFDM125A_M_Master` | `OFD125A_M` | `BF_NO` | 齊 | — |
| `OFDM125A_Detail` | `OFD125A` | `BF_NO` `SRNO` | 齊 | — |
| `OFD126A` | `OFD126A` | `ST_CD` `DATA_SEQ` | 齊 | 20 |
| `OFDM127` | `OFD127` | `BF_NO` `DATA_SEQ` | **無** | 20 |
| `OFDM128` | `OFD128` | `BF_NO` `FUND_ID` `TRAN_TYPE` `ANNOUNCE_AMT` | **無** | 27 |
| `OFDM129` | `OFD129A` | `BF_NO` `FUND_ID` | 齊 | 41 |
| `OFDM133` | `OFD133A` | `RBF_NO` `BF_NO` | 齊 | 23 |
| `OFDM135` | `OFD135A` | `BF_NO` `SRNO` | 齊 | 22 |
| `OFDM151` | `OFD151A` | `QUERY_GRPCD` | 齊 | 17 |
| `OFDM151_EMP` | `OFD152A` | `EMP_NO` `QUERY_GRPCD` | 齊 | 23 |
| `OFDM151_FUND` | `OFD153A` | `FUND_ID` `QUERY_GRPCD` | 齊 | 20 |
| `OFDM154` | `OFD154` | `FUND_ID` `TRAN_TYPE` `STOP_BNG_DATE` | **無** | 20 |
| `OFDM155` | `OFD155` | `FUND_ID` `SWITCH_FUND_ID` | **無** | 19 |
| `OFD156A` | `OFD156A` | `SILL_CODE` | 齊 | 30 |
| `OFD157A` | `OFD157A` | `SILL_CODE` `FUND_ID` | 齊 | 18 |
| `HIGHRISK_COUNTRY` | `HIGHRISK_COUNTRY` | `COUNTRY_CD` `DATA_SEQ` | 齊 | 23 |
| `OFDM161` | `OFD161` | `FUND_ID` | **無** | 21 |
| `OFD162` | `OFD162` | `PERIOD_EXE_DATE` `FUND_ID` | **無** | 17 |
| `OFDM163` | `OFD163` | **沒有宣告 PK** | **無** | 16 |
| `OFDM164` | `OFD164` | `BNG_DATE` `FUND_ID` | **無** | 23 |

**「四眼 13 欄:無」與「PO 基底是 `BasicEVAPO`」是同一群人。** 八支死畫面(§0.2)的 Model xsd 裡**一律沒有四眼 13 欄**;十二支活畫面**一律有**。唯一的例外是 `OFD162`——它屬於活畫面 `OFDM161`⁠…⁠不對,`OFDM161` 也是死的。**實際上是零例外:這條線切得乾乾淨淨。** 這給 §0.2 的推論再加一條獨立旁證:那 8 支不只 PO 沒遷,連 Model 都沒補四眼欄位。

`OFDM163` 的 xsd **完全沒有 PK 宣告**(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM163Model.xsd`),而 `Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:819` 卻宣告 `pkey="LOCK_GAIN_PROCESS_TIME"`。**兩邊不一致**,列入附錄 E。

### 2.3 三張與 `App.config` 對不上的明細宣告

`App.config` 的 `mastertable` / `detailtable` 是 UI 端的綁定設定,理論上該跟 PO 的 `xTableMapping` 一致。實測有三支對不上:

| 畫面 | PO 宣告的明細 | `App.config` 的 `detailtable` | 錨點 |
|---|---|---|---|
| `OFDM115A` | `OFD116A` → `OFDM115_Detail` | **沒有這一行** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:44` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:689-694` |
| `OFDM123` | `OFD125` → `OFD125` | **沒有這一行** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:38` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:697-702` |
| `OFDM151` | `OFD152A` 與 `OFD153A` 兩張 | **兩行都沒有** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:38-39` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:771-776` |

對照組:`OFDM125A` 與 `OFDM156` 兩支**有**把 `detailtable` 寫進 `App.config`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:722`、`:797`)。所以缺的那三支是漏寫,不是設計。**實際影響要看框架怎麼用這段設定(`Vendor.Product.Config.PluginData` 無原始碼,從呼叫端反推),本文只記事實。**

### 2.4 與其他模組共用的表

| 表 | 本片的維護者 | 誰還在用 | 錨點 |
|---|---|---|---|
| `OFD114A` | `OFDM114` | EC 的 `IPJB622` / `OFDB602`、`OFDI011`、`RSPB009` | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs` |
| `OFD115A` | `OFDM115A` | `CLSM002`、`CODM006`、`OFDI907`、`OFDI011` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI907_PO.cs` |
| `OFD123A` | `OFDM123A` | `BasicBMS_PO`、`Utility_PO`、`BMSM001`、`BMSM006` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs` |
| `OFD124` | `OFDM123` | `BMSM001` / `BMSM006`(**引用全被註解**)、`OFD_PO`、`SerialNo_AGI` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:152-153`、`:610-625`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:104`、`:2163-2166` |
| `OFD125A` | `OFDM125A` | `ucTradeAgentData` / `ucTradeDeputyData`(共用控制項)、`BasicOFD_Ctl` / `BasicOFD_PO` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucTradeDeputyData.cs` |
| `OFD126A` | `OFDM126` | `OFDR285`、`NFDR074` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR285_PO.cs` |
| `OFD127` | `OFDM127` | `BasicOFD_Ctl` / `BasicOFD_Pxy` / `MSSQL/BasicOFD_PO` / `GetANNOUNCE_AMTDataSrc` | `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/GetANNOUNCE_AMTDataSrc.cs` |
| `OFD129A` | `OFDM129` | `Utility_PO` / `NfdUtility_PO`、`OFDB004`、`OFDB331`、`NFDR022` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB331_PO.cs` |
| `OFD135A` | `OFDM135` | `BasicOFD_Ctl` / `BasicOFD_PO`、`OFDI011` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` |
| `OFD152A` `OFD153A` | `OFDM151` | `BasicOFD_PO`、`OFDI058` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058_PO.cs` |
| `OFD163` | `OFDM163` | `OFDB161` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs` |
| `HIGHRISK_COUNTRY` | `OFDM157` | `BasicBMS_PO`(透過 view `V_TA_HIGHRISK_COUNTRY`) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69`、`:75` |

**其餘 11 張表(`OFD116A` `OFD122A` `OFD124A` `OFD125A_M` `OFD128` `OFD133A` `OFD151A` `OFD154` `OFD155` `OFD156A` `OFD157A` `OFD161` `OFD162` `OFD164`)在 `Dev/` 全樹只有 `ATLAS.OFD` 自己碰。**

**`OFD127` 與 `OFD129A` 是本片被外部依賴最深的兩張**,偏偏 `OFD127` 的維護畫面 `OFDM127` 是死的(§0.2)。也就是說:Common 端的 `GetANNOUNCE_AMTDataSrc` 天天在讀 `OFD127`,但**已經沒有畫面可以維護它**。這是本片最值得追的一條——見附錄 E.2。

### 2.5 欄位中文名:兩極化

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。本片的填寫狀況兩極:

| 狀況 | 表 | 說明 |
|---|---|---|
| **填得完整** | `HIGHRISK_COUNTRY` `OFD126A` `OFD124A` `OFD124` | 業務欄幾乎每欄都有 Caption,連 `DATAID`(「資料識別碼」)與四眼 13 欄都填了 |
| **只填一半** | `OFD123A` | 123 欄裡只有 8 欄有 Caption(`IN_DATE` `BF_NO` `ID_NO` `BF_NAME` `BF_COUNTRY_X` `SOURCE_CD` 等),`INVEST_TOOL_YN1`~`INFO_SOURCE_OTH_LP` 那六十幾個問卷選項欄**全部空白** |
| **幾乎全空** | `OFD125`(`OFDM123` 的明細) | 31 欄裡只有 `IS_CHK`(「勾選否」)有 Caption |

三個要特別記住的陷阱:

| 陷阱 | 內容 | 錨點 |
|---|---|---|
| **同一張表兩個 `dataid`** | `OFD124` 同時有 `DATAID`(大寫,可空)與 `dataid`(小寫,不可空)兩欄,Caption 都空白 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM123Model.xsd`;PO 端 SELECT 的是小寫的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:210`) |
| **四眼欄大小寫兩套** | 活畫面用 `Status` / `CreateID` / `EntryDate` 這種駝峰(例 `OFD124`),死畫面與 `OFD123A` 用全大寫 `STATUS` / `CREATEID` / `ENTRYDATE` | `OFD124` vs `OFD123A` 的欄位清單,兩者都在 `DataEntity.OFD6` |
| **`_LP` 後綴是第二份問卷答案** | `OFD123A` 的 `INVEST_TOOL_YN1` 與 `INVEST_TOOL_YN1_LP` 成對出現(共 30 組),Caption 都空白。從 UI 的 `utxtBF_NO` / `utxtBF_NO_LP` 成對控制項推測,`_LP` 是**聯名戶第二位受益人**的答案 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:105-106`。**標〔假設〕**,依據只有控制項命名與同頁配對,沒有找到寫死 `LP` 意義的常數 |

### 2.6 狀態碼

本片沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`),本片 20 支 PO **一次都沒有**跟 `EVAStatusCode` 的常數做比較,也**沒有任何一處寫死 `STATUS` 字面值**——這點比 `ofd7.md §2.6` 記的那三個寫死 `'301'` 的入口乾淨。

本片自己定義值域的欄位只有三個,而且值域都在 `CTL014` 而不在程式裡:

| 欄位 | `CTL014.SourceType` | 用在哪 | 錨點 |
|---|---|---|---|
| `KYC_BF_COUNTRY_X`(受益人類別) | `'063'` | `OFDM123` 主檔 join 取中文 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:252` |
| `KYC_AGENT_ID`(銷售機構區別碼) | `'062'` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:253` |
| `KYC_RISK_ATTR`(風險屬性) | `'404'` | 同上,`KYC_RISK_ATTR` 與 `KYC_RISK_ATTR_SELF` 共用同一組 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:254-255` |
| `SYSTEM_ID`(交易途徑) | `'107'` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:256` |
| `FUND_STATUS`(基金狀態) | `'007'` | `OFDM151` 的基金明細 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:133`、`:259` |
| `SOURCE_CD`(資料來源) | `'455'` | `OFDM123A` 的下拉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:39` |

**這六個數字碼〔客戶特定〕**,`CTL014` 是資料表不是程式常數(`architecture.md §7.2` 說 `TA.MappingCode` 才是 repo 內唯一的值域字典,而這六組不在裡面),**實際有哪些值必須查 DB**。標為〔假設〕缺:DB 連線。

## 3. 畫面清冊

```text
[圖] OFD6 二十支畫面依 PO 基底分成活的十二支與死的八支,以及死因的三個獨立條件與兩條旁證
圖中文字:① 活的十二支:xTableMapping + dbProduct,現行主線 / BaseEVADaoPO 十支 / 114 115A 122A 123A 125A 126 129 151 156 157 / BaseMultiRowEVADaoPO 兩支 / OFDM133 OFDM135 / 全部在 csproj / 六層 × 20 支 = 120 項全命中 / ② 死的八支:TableMapping + dbTA,dbTA 永遠是 null / OFDM123 / T-SQL 128 處 最複雜 / OFDM127 / 唯一覆寫 Add Update Delete / OFDM128 / PO 1555 行 最大 / OFDM154 / 兩個事件處理器沒接上 / OFDM155 / MultiRowEVAPO 唯一一支 / OFDM161 / After* 手寫 SQL 寫 OFD162 / OFDM163 / PO 只有 25 行 連事件都沒掛 / OFDM164 / 重疊檢核出錯不擋存檔 / ③ 為什麼死:三個條件同時成立,而且彼此獨立 / dbTA 宣告即 null / BasicEVAPO.cs:26 / 建構子那四行被註解 / BasicEVAPO.cs:164-172 / 八支子類無一賦值 / 實掃 dbTA = 零命中 / BeforeSelect 就用 dbTA / 查詢即 NRE / ④ 旁證兩條:SQL 方言與 Model 欄位,兩條都指同一批人 / T-SQL 痕跡 / [表名] newid SELECT TOP ISNULL SqlDbType / Model 缺四眼 13 欄 / 八支全缺 十二支全有 / 零例外 / 兩條旁證與 PO 基底完全重合 / ⑤ 反面對照:同一個資料夾裡有遷移成功的證物 / OFDM125A_PO.cs:28 / //… : BasicEVAPO 被註解 / OFDM125A_PO.cs:30 / : BaseEVADaoPO 現行 / 改用 dbProduct / 這就是八支缺的那一步 / OFDM152 反例 / 編了卻沒有畫面
```

*圖:圖 3 依 PO 基底分群(讀本片前必看)。橘框=活的或確定的結論;橘虛框=死畫面與風險;黑框=無原始碼的框架內部;灰虛框=歷史痕跡。本片沒有「檔案存在但不在 csproj」的情形——120 個六層項目全部命中;真正的分界線是 PO 基底,不是編譯設定。*

### 3.1 維護 M

20 支**六層全齊**,全部在 `Dev/ATLAS.OFD`(UI / FormProxy / Control / PO)+ `DataEntity.OFD6` / `UIEntity.OFD6`(Model / View)。六個 csproj **全部**都在 `Dev/Vendor.ATLAS.sln` 裡。中文名待選單表回填,「用途」欄為推測。

「PO 基底」欄標紅(**粗體**)= 繼承 `BasicEVAPO` / `MultiRowEVAPO`,依 `architecture.md §3.1.1` 與本文 §0.2,這些畫面**從查詢就會 NRE**。「在 csproj」欄逐支查六個 csproj 的 `<Compile Include>` / `<None Include>`。

| 代號 | 用途(推測) | 塊 | **PO 基底** | **在 csproj** | 主表 | 明細 | 子對話框 | 特別之處 |
|---|---|---|---|---|---|---|---|---|
| `OFDM114` | 受益人 × 基金 停止交易設定 | B | `BaseEVADaoPO` | 六層齊 | `OFD114A` | — | — | 唯一同時有「境內 / 境外」切換與 `BF_NO` 的畫面 |
| `OFDM115A` | 客戶列管名單(警示 / 排除 / 忽略) | A | `BaseEVADaoPO` | 六層齊 | `OFD115A` | `OFD116A` | — | 有伺服端 `BeforeAdd` / `BeforeUpdate`;`App.config` 漏掉 `detailtable` |
| `OFDM122A` | 自主聲明書 | A | `BaseEVADaoPO` | 六層齊 | `OFD122A` | —(宣告被註解) | — | UI 1,963 行,`DoValidate` 有一整頁被註解 |
| `OFDM123` | KYC 風險屬性問卷 | A | **`BasicEVAPO`** | 六層齊 | `OFD124` | `OFD125` | `OFDM123p0`(1,023 行) | 全片最複雜的死畫面;T-SQL 128 處;`INNER JOIN BMS001` |
| `OFDM123A` | 客戶投資屬性調查表 + 實質受益人 | A | `BaseEVADaoPO` | 六層齊 | `OFD123A` | `OFD124A` | `OFDM123Ap0` | UI 2,541 行,全片最大;含高齡與弱勢族群條款 |
| `OFDM125A` | 董監事 / 實質受益人設定 | A | `BaseEVADaoPO` | 六層齊 | `OFD125A_M` | `OFD125A` | `OFDM125Ap0` | 第 28 行留著 `//… : BasicEVAPO` 的遷移證物 |
| `OFDM126` | 行銷說明文字 | D | `BaseEVADaoPO` | 六層齊 | `OFD126A` | — | — | 與 `OFDM157` 是近複製(相似度 0.78 / 0.86) |
| `OFDM127` | 受益人公告金額 | B | **`BasicEVAPO`** | 六層齊 | `OFD127` | — | — | 八支死畫面中**唯一**覆寫 `Add`/`Update`/`Delete`,但覆寫版照樣用 `dbTA` |
| `OFDM128` | 受益人 × 基金 × 交易別 公告金額 | B | **`BasicEVAPO`** | 六層齊 | `OFD128` | — | — | PO 1,555 行,本片最大的 PO,也是死的 |
| `OFDM129` | 受益人專屬交易條件與費率 | B | `BaseEVADaoPO` | 六層齊 | `OFD129A` | — | `OFDM129p0`(複製) | 41 欄,有「複製受益人」;被 `OFDB004` / `OFDB331` / `NFDR022` 共用 |
| `OFDM133` | 受益人歸戶(主要窗口) | B | `BaseMultiRowEVADaoPO` | 六層齊 | `OFD133A` | —(多筆型) | — | PK 是 `RBF_NO`+`BF_NO`,與 `MasterPKey` 的 `BF_NO` 不同層 |
| `OFDM135` | 交易指示代理人 | B | `BaseMultiRowEVADaoPO` | 六層齊 | `OFD135A` | —(多筆型) | — | **沒有宣告 `MasterPKey`**;禁止刪除,只能填終止日 |
| `OFDM151` | 查詢群組(員工 × 基金權限) | D | `BaseEVADaoPO` | 六層齊 | `OFD151A` | `OFD152A` `OFD153A` | — | 本片唯一三表結構;`AppendToDoString` 是死碼 |
| `OFDM154` | 基金 × 交易別 停止交易 | C | **`BasicEVAPO`** | 六層齊 | `OFD154` | — | — | 兩個事件處理器寫了沒接上 |
| `OFDM155` | 基金可轉換對應(轉出 → 轉入) | C | **`MultiRowEVAPO`** | 六層齊 | `OFD155` | —(多筆型) | — | 本片唯一的 `MultiRowEVAPO` |
| `OFDM156` | 交易金額門檻類別 | C | `BaseEVADaoPO` | 六層齊 | `OFD156A` | `OFD157A` | — | 六個門檻欄位(自然人 / 法人 × 申購 / 買回 × 單筆 / 單日) |
| `OFDM157` | 高風險國別 | A | `BaseEVADaoPO` | 六層齊 | `HIGHRISK_COUNTRY` | — | — | 全片唯一不照 `OFDnnn` 命名的主檔;從 `OFDM126` 複製而來 |
| `OFDM161` | 定期買回排程設定 | C | **`BasicEVAPO`** | 六層齊 | `OFD161` | —(`OFD162` 手寫 SQL) | — | 唯一有 `AfterAdd`/`AfterUpdate`/`AfterApprove` 跨表寫入的畫面;兩段檢核被 `/* */` 註解 |
| `OFDM163` | 定期買回自動發送時間(全基金共用) | C | **`BasicEVAPO`** | 六層齊 | `OFD163` | — | — | PO 只有 25 行,**連 `BeforeSelect` 都沒掛**;xsd 無 PK |
| `OFDM164` | 基金買回率設定 | C | **`BasicEVAPO`** | 六層齊 | `OFD164` | — | — | 區間重疊檢核踩 Oracle 三值邏輯;伺服端出錯時**不擋存檔** |

**統計**:20 支裡 **8 支繼承 `BasicEVAPO` / `MultiRowEVAPO`**(`OFDM123` `OFDM127` `OFDM128` `OFDM154` `OFDM155` `OFDM161` `OFDM163` `OFDM164`),占 40%;**0 支缺 csproj**。

> **「0 支缺 csproj」這個結論是逐支查出來的,不是假設。** 對六個 csproj 各跑一次精確字串比對(`"OFDM123.cs"`、`OFDM123_PO.cs`、`OFDM123_Ctl.cs`、`OFDM123_Pxy.cs`、`OFDM123Model.xsd`、`OFDM123View.xsd`),20 支 × 6 層 = 120 個項目全部命中。`ofd7.md §2.3` 記的 `OFDM199A_Pxy.cs` 那種「檔案在但不在 csproj」的情況,**本片沒有**。

> ⚠ **但本片有另一種未編譯殘骸:編了卻沒有畫面的 Entity。** `OFDM152Model.xsd` / `OFDM152ModelVDB.cs` 在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/DataEntity.OFD6.csproj:178-183`、`:381-390`,`OFDM152View.xsd` 在 `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD6/UIEntity.OFD6.csproj:173`,**兩個都有被編譯**;但 `UI.OFD` / `PO.OFD` / `Control.OFD` / `FormProxy.OFD` 四個專案裡**沒有任何 `OFDM152` 檔案**。而且 `OFDM152Model.xsd` 的 PK 是 `FUND_ID` `TRAN_TYPE` `STOP_BNG_DATE`,**與 `OFDM154Model.xsd` 一字不差**。合理推測是 `OFDM154` 開發途中改過代號留下的副本,**標〔假設〕**——依據是 PK 完全相同且 `OFDM152` 在全 repo 只有這兩個 Entity 檔加 `OFDM151` 裡的格子名 `ugrdOFDM152`(那是別的東西,指的是 `OFD152A` 員工明細格)。

### 3.2 查詢 I

**本片無 I 畫面。**原因:`DataEntity.OFD6` 只收 M 型的 Model,同主題的查詢畫面在別的專案(`OFDI011` / `OFDI058` / `OFDI907`,見 §8.2),不屬於本片。

### 3.3 批次 B

**本片無 B 畫面。**`DataEntity.OFD6` 底下沒有任何 B 型 Model,20 支 UI 也沒有任何一支開出 `xOneStepProcessForm` 型的子視窗——四個子對話框(`OFDM123p0` `OFDM123Ap0` `OFDM125Ap0` `OFDM129p0`)全是 M 畫面按鈕開出來的一般對話框。

### 3.4 報表 R

**本片無 R 畫面。**`DataEntity.OFD6` 底下沒有任何 `*R*Model.xsd`。讀本片資料的報表 `OFDR285` / `NFDR022` / `NFDR074` 在 `Dev/ATLAS.OFD.Report` 與 `Dev/ATLAS.NFD.Report`,見 §7。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFDM151 的三表結構與 RIGHT OUTER JOIN 手法,以及全片卡控的三個層次與七條靜默失效路徑
圖中文字:① OFDM151 是本片唯一的三表結構:一個群組,兩張明細 / OFDM151 查詢群組 / OFD151A PK 群組代碼 / OFD152A 員工明細 / RIGHT OUTER JOIN COD009 / OFD153A 基金明細 / RIGHT OUTER JOIN OFD081A / 只掛境內基金 / 境外無法授權 假設 / ② RIGHT OUTER JOIN 的用意:全部列出來,有設定的打勾 / CASE WHEN QUERY_GRPCD IS NULL / THEN 0 ELSE 1 END AS ISCHECK / NVL(QUERY_GRPCD, 群組代碼) / 群組代碼字串串接三次 / 沒帶參數就回空字串 / GetSqlStringCommand("") / ③ 卡控層次:三層,但伺服端那一層幾乎只做流水號 / validatorManager1 / 必填與型別 / DoValidate / 業務檢核 幾乎全部在這 / 伺服端 BeforeAdd / 115A 126 157 只取流水號 / OFDM115A 例外 / 唯一伺服端業務檢核 / ④ 三支明細型畫面的必填檢核長得一樣,訊息也一樣 / OFDM115A / 明細資料 必須輸入 / OFDM125A / 明細資料 必須輸入 / OFDM133 / OFDM135 / 同一句 同一種寫法 / OFDM156 / 明細資料必須輸入！！ / ⑤ 會靜默吃掉資料的四條:全部沒有提示 / OFDM123 INNER JOIN BMS001 / 沒有戶號的答卷消失 / OFDM135 JOIN BMS001A / 沒有主檔的代理人消失 / OFDM157 JOIN OFD008 / 國別檔沒有的國碼消失 / OFDM151 空 SQL / 明細整段撈不到 / ⑥ 會靜默放行的三條:比吃掉資料更危險 / OFDM123A 回傳筆數檢查被註解 / BMS001A 沒更新也算成功 / OFDM164 少 e.Cancel / 伺服端出錯照樣存檔 / OFDM161 檢核被 /* */ 包住 / 跑過的排程可無聲改掉
```

*圖:圖 4 OFDM151 三明細與卡控層次。橘框=正常結構或正確做法;白框=一般步驟;橘虛框=風險寫法。① 與 ② 是 OFDM151 的核心手法:用 RIGHT OUTER JOIN 把全部員工與全部基金列出來再打勾。⑤ 與 ⑥ 是讀本片時最該記住的兩排——⑤ 讓資料看不見,⑥ 讓錯誤資料存得進去。*

本章順序照 §0.1 的四塊業務線排,不照代號順序: **A 客戶身分審查** §4.1~§4.7 · **B 受益人層例外** §4.8~§4.13 · **C 基金層控制** §4.14~§4.19 · **D 系統參數** §4.20。

### 4.0 二十支共同的骨架

先把重複的部分講完,後面各節只寫差異。

| 環節 | 共同做法 | 錨點(以 `OFDM157` 為例) |
|---|---|---|
| UI 基底 | `xMaintainForm`(無原始碼,從呼叫端反推),查詢頁 + 維護頁兩個 TabPage | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM157.cs:23`、`:91` |
| 存檔前檢核 | `BeforeAddButtonClicked` / `BeforeModifyButtonClicked` → `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM157.cs:51-68` |
| 四眼 | 活的 12 支全走框架,PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個取數事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:31-33` |
| ToDo | 新世代寫 `if (args.Status == xEVAStatus.ToDO) strSQL += xTableHelper.AppendToDoString(…)`;舊世代寫 `if (isToDoString)` 再由呼叫端傳 `true` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:108-111` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:139-142` |
| 參數化 | 新世代用 `EVAStringHelper.AddParam(dbProduct, args.DbCmd, …)` 或 `dbProduct.AddInParameter`;**舊世代 8 支一律字串串接** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:104-105` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:100` |

**四件全片通用、值得先記住的事:**

1. **卡控幾乎全在 UI 的 `DoValidate()`。** 伺服端只有三支掛了 `BeforeAdd`(`OFDM115A` `OFDM126` `OFDM157`),而這三支的 `BeforeAdd` 做的都不是業務檢核,是**取流水號**(`DATA_SEQ = MAX + 1`)。唯一真正在伺服端做業務檢核的是 `OFDM115A` 的重複列管檢查(§4.1)。

2. **`if (this.ValidateErrList.Show()) { e.Cancel = true; return; }` 這一段會截斷後面的業務檢核。** 例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:79-83`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:103-108`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:189`。使用者只會先看到必填錯誤,修完再存才會看到業務錯誤——要按兩次以上。這與 `ofd7.md §4.0` 記的是同一個體質。

3. **「新增」與「修改」兩個 handler 常常是整段複製。** `OFDM164` 的 `BeforeModifyButtonClicked`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:76-112`)與 `BeforeAddButtonClicked`(`:114-150`)除了 `ChkOFD164` 的最後一個參數 `"M"` / `"A"` 之外**一字不差**;`OFDM161` 也是(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:101-136` vs `:249-285`)。改一邊忘了改另一邊的風險很高。

4. **`DATA_SEQ` 流水號一律用 `SELECT NVL(MAX(DATA_SEQ),0) + 1`,沒有鎖。** 三支都這樣(`OFDM115A` `OFDM126` `OFDM157`)。同時兩個人新增同一個 `ST_CD` / `COUNTRY_CD`,會拿到同一個號。**併發下會撞 PK。**

---

### 4.1 `OFDM115A` — 客戶列管名單(警示 / 排除 / 忽略)

- **用途(推測)**:把某位客戶或某個身分證號列入管制,指定列管交易別、列管原因與處理方式(警示 / 排除 / 忽略)、列管期間;明細 `OFD116A` 是「這次列管涵蓋哪些基金」。

- **推測依據**:UI 標籤有「列管原因」「列管處理方式」「警示 / 排除 / 忽略」「若列管原因為定期審查未完成,請在原因備註欄加註」「『未提供「辦識及確認公司股東或實質受益人身分」之證明文件』」(以 `grep` 取自 `OFDM115A.Designer.cs`)。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:108`、`:118`、`:183`。

- **明細查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:233-234`,`LEFT JOIN` 一段名為 `MYOFD081A` 的 CTE,把 `OFD081A`(境內,`:216`)與 `OFD081`(境外,`:225`)`UNION` 起來——**跟 `ofd7.md §4.3` 記的 `OFDM193` 用的是同一招**。

**這是本片唯一在伺服端做業務檢核的畫面。** `OFDM115A_PO_BeforeAddUpdate`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:96-148`)同時掛在 `BeforeAdd` 與 `BeforeUpdate`,做兩件事:

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1(僅 `Insert`) | `SELECT NVL(MAX(DATA_SEQ),0)` 全表取號 + 1,同步塞進所有明細列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:105-117` |
| 2 | 查同一個對象 + 同原因 + 同處理方式 + 同交易別、期間有重疊、且 `DATA_SEQ` 不同的既有列管 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:118-137` |

步驟 2 的「對象」判斷會分岔:`CNTL_TRADE == CNTL_TRADE_TYPE.OpenAccount` 時用 `CUS_NAME` + `ID_NO` 比對(還沒有戶號),否則用 `BF_NO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:125-131`)。這是合理的設計,不是 bug。

**但這段 SQL 有三個問題**(附錄 E):

1. **整段字串串接**,`CUS_NAME` 直接進 SQL(`:126`)。客戶姓名帶單引號就炸,而且是伺服端。

2. **期間重疊條件沒有括號**:`AND (A AND B OR C AND D)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:133-136`)。靠 `AND` 優先於 `OR` 才剛好等於原意「起日落在區間內 或 迄日落在區間內」。**語意目前是對的,但完全依賴運算子優先序**,任何人加一個條件就會錯。

3. **`AND DATA_SEQ <> " + row.DATA_SEQ`**(`:138`)。Oracle 三值邏輯:`DATA_SEQ` 若為 `NULL`,`<>` 回 `UNKNOWN`,那一列**不會**被算進重複檢查。`DATA_SEQ` 在 xsd 是不可空,實際 DB 是否 `NOT NULL` 要查 DB(本片 `OFD115A` 沒有 DDL,見附錄 A),**標〔假設〕缺:DB 連線**。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細必填欄有空 | 「(欄名) 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM115A.cs:595` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM115A.cs:598` |
| 存檔前 | 列管日(起) > 列管日(迄) | 「列管日期(起) 不可大於 列管日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM115A.cs:601` |
| 存檔前 | 列管起日條件不符(`ERR_ST_DATE`) | 跳 `Warn03` 問使用者,選 `No` 才 `e.Cancel` | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM115A.cs:160-163`、`:242-245` |
| 存檔前 | 列管迄日條件不符(`ERR_END_DATE`) | 同上 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM115A.cs:178-181`、`:260-263` |
| 伺服端 `BeforeAdd` / `BeforeUpdate` | 同對象同原因同處理同交易別且期間重疊 | 由 `ExecuteScalar` 結果決定 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:118-144` |

**跨表更新**:無。只寫 `OFD115A` 與 `OFD116A`。

---

### 4.2 `OFDM122A` — 自主聲明書

- **用途(推測)**:登錄客戶簽署的「自主聲明書」(`DB/Table/Create_OFD122A.sql` 的 `comment on table` 明寫「自主聲明書資料檔」),主鍵 `SET_DATE` + `ID_NO`,可設終止日。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:66`;另有兩段查 `OFD123A`(`:93`)與 `BMS001A`(`:226`)、一段查 `OFD124A`(`:292`)的輔助 SQL。

- **UI 1,963 行**,是本片第三大的 UI。

**這支畫面最重要的事實:它的 `AfterApprove` / `AfterApproveDelete` 是一個空方法。**

`OFDM122A_PO_AfterAUD` 在建構子被掛上 `AfterApprove` 與 `AfterApproveDelete`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:35-36`),但方法本體 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:56-254` **199 行全部是註解**,執行時什麼都不做。被註解掉的內容是:

| 被註解的動作 | 錨點 |
|---|---|
| 檢查是不是最新一筆(`SELECT COUNT(1) FROM OFD122A WHERE BF_NO = :BF_NO AND SET_DATE > :SET_DATE`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:66` |
| `INSERT INTO BMS001ACHG …`(寫一筆受益人異動記錄) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:120` |
| `UPDATE BMS001A SET TERMINATE_DATE = …, KYC_RISK_ATTR = …` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:241-243` |
| `if (ExecuteNonQuery(...) != 1) throw new ApplicationException("受益人風險屬性及KYC終止日更新失敗")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:249-250` |

**這段程式是從 `OFDM123A_PO_AfterAUD` 複製過來再整段註解掉的**——證據是被註解的 SQL 裡還寫著 `FROM OFD123A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:93`),而不是 `OFD122A`。也就是說:**自主聲明書覆核後不會同步回受益人主檔,投資屬性調查表會**(§4.4)。這兩支是同一塊業務的兩個入口,行為卻不一樣。列入附錄 E。

`DoValidate` 裡另有一整段(實質受益人、投資工具、資金來源、擔任職務)被註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:479-525`),內容與 `OFDM123A.cs:474-531` 一字不差——**同一份檢核在 `OFDM123A` 是活的,在 `OFDM122A` 是死的**。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 客戶統編 / 戶號 / 輸入日期起迄 三者全空 | 「客戶統編、戶號、輸入日期起迄 三者選一 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:154-156` |
| 查詢前 | 輸入日期只填一邊 | 「輸入日期(起)(迄) 必須皆(不)填寫」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:162` |
| 查詢前 | 輸入日期(起) > (迄) | 「輸入日期(起) 不可大於 收件日期(迄)」(**訊息裡的「收件日期」與欄位名「輸入日期」不一致**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:164` |
| 存檔前 | 受益人類別未選 | 「請先選擇受益人類別」 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:299-300` |
| 存檔前 | 此受益人不為自然人 / 不為法人 | 兩句警示 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:307-308`、`:359-360` |
| 存檔前 | 後台不可選線上來源、實質受益人必填、投資工具 / 資金來源 / 擔任職務至少選一 | 六句 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:416`、`:479-525` |

**跨表更新**:**無**(原本設計有,整段被註解,見上)。

---

### 4.3 `OFDM123` — KYC 風險屬性問卷【死畫面】

**這是本片最複雜的一支死畫面:PO 666 行、UI 898 行、子對話框 1,023 行,全部跑不起來。**

- **用途(推測)**:替受益人建立一份 KYC 問卷答卷(`OFD124` 主檔 = 一張答卷,`KYC_ANS_NO` 是問卷書號),逐題答案存 `OFD125`,系統依答案算 `KYC_TOTAL_SCORE` 與 `KYC_RISK_ATTR`(風險屬性),並設生效 / 終止日。

- **推測依據**:欄位 Caption「問卷書號」「問卷總分」「受益人風險屬性」「客戶自訂風險屬性」「填寫日期」「版本號」;明細欄 `QSN_SEQNO` / `ANS_SEQNO` / `ANS_SCORE`。

- **題庫不在本片**:`OFD741`(題目)、`OFD742`、`OFD743`(版本對應)、`OFD744`、`OFD745` 由 `OFDM741` / `OFDM742` / `OFDM743` 維護(`DataEntity.OFD9`),`OFDM123` 只讀。

**為什麼它是死的**:`public class OFDM123_PO : BasicEVAPO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:20`),不覆寫 `Add` / `Update` / `Delete`,`BeforeSelect` 第一行就 `args.DbCmd = dbTA.GetSqlStringCommand(strSQL)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:154`)。詳見 §0.2。

**T-SQL 痕跡是全片最濃的**:

| 痕跡 | 出現處 | 錨點 |
|---|---|---|
| `[表名]` 方括號 | `[OFD124]` 50 次、`[OFD125]` 34 次、`[OFD743]` 20 次… | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:250-258` |
| `newid()` | 產生 `dataid` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:447` |
| `SELECT TOP 1` | 取風險屬性、取 KYC 有效月數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:540`、`:572` |
| `Convert(nvarchar(10), …, 111)` + `GetDate()` | 判斷還有沒有有效問卷 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:599-600` |

Oracle 沒有 `newid()`、沒有 `SELECT TOP`、`Convert(…,111)` 也不是 Oracle 語法。**這支從來沒有被遷移過。**

**主檔 SQL 有一個更硬的問題:`INNER JOIN`。**

```
FROM [OFD124]
INNER JOIN [BMS001] ON [BMS001].[BF_NO] = [OFD124].[BF_NO]
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:250-251`)。本片其他 19 支對外部主檔一律用 `LEFT JOIN`。這裡用 `INNER JOIN` 的後果:**`BF_NO` 對不到 `BMS001` 的答卷會整筆消失,沒有任何提示**。而 KYC 問卷常常是「開戶前先填」的,那時候還沒有 `BF_NO`——`OFDM123` 自己的 `DoValidate` 就寫「新增時 受益人ID、戶號 必填擇一填寫」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:592`),允許只填 ID 不填戶號。**允許存進去,卻查不出來。**

另外五個 `LEFT JOIN [CTL014]` 各帶一個 `SourceType` 常數(`'063'` `'062'` `'404'` `'404'` `'107'`),見 §2.6。

**四眼各階段附加動作:全部接到「跳號一覽表」。**

`OFDM123_PO` 是本片唯一把八個 `After*` 事件全掛滿的 PO:

| 事件 | 動作 | 錨點 |
|---|---|---|
| `AfterGetMaintainData` | `SrNoCommentProcessor.GetCommentHistory(...)` 撈跳號說明 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:613-620` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject` | `SrNoCommentProcessor.AddCommentHistory(EVAType.X, _JumpSrNo, …)`,回 `false` 就 `throw new ApplicationException("")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:622-664` |

> ⚠ **七處 `throw new ApplicationException("")` 的訊息是空字串**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:626`、`:632`、`:638`、`:645`、`:651`、`:657`、`:663`)。使用者端只會看到一個沒有內容的錯誤對話框。列入附錄 E。

**耐人尋味的地方:`SrNoCommentProcessor` 是新世代的共用元件**(`Dev/Common/Source/Utility/TA.UtilityPO/SrNoCommentProcessor_PO.cs`,有 Oracle Dao),卻被掛在一支 T-SQL 的死畫面上。**合理推測是「跳號一覽表」這個橫向需求上線時,開發者對全庫 M 畫面統一加掛,沒有分辨哪些畫面已經不能跑。標〔假設〕**,依據是同一組 `JumpSrNo_After*` 方法在 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs` 等多支畫面都有。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 問卷書號 / 填寫日期 / 受益人ID / 戶號 全空 | 「問卷書號、填寫日期、受益人ID、戶號 必填擇一填寫」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:573` |
| 存檔前(僅新增) | 受益人ID 與戶號都空 | 「新增時 受益人ID、戶號 必填擇一填寫。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:139`、`:592` |
| 存檔前 | 終止日期 < 生效日期 | 「終止日期不可小於生效日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:602` |
| 存檔前 | 查不到版本編號 | 「尚未設定'版本編號'」/「尚未進行'問卷維護'作業」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:146`、`:609` |
| 刪除前 | 刪掉後就沒有有效問卷了(`ChkAfterDEL_HasEFFECTIVE`) | 跳 `Warn03` 問,選 `Yes` 才繼續 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs:659-667`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:592-607` |
| 主檔取數 | `INNER JOIN BMS001` | 無受益人主檔的答卷不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:251` |

`ChkAfterDEL_HasEFFECTIVE` 的 SQL 用 `string.Format(strSQL, strKYC_ANS_NO, Convert.ToString(decBF_NO))`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:602`)——**問卷書號直接進 SQL**,帶單引號就炸。

**跨表更新**:無(除了跳號一覽表的共用元件)。

---

### 4.4 `OFDM123A` — 客戶投資屬性調查表 + 實質受益人【本片最大的活畫面】

- **用途(推測)**:登錄客戶的「投資屬性調查表」(教育程度、職業、年收入、投資工具、資金來源、資訊來源、風險承受度七題),算出 `EFFECT_CODE1` / `EFFECT_CODE2`(風險屬性),並在覆核後**同步回受益人主檔**。明細 `OFD124A` 是這位客戶的股東 / 實質受益人名單(含重要政治性職務人士 PEP 三問)。

- **推測依據**:`OFD124A` 的 Caption 有「是否為重要政治性職務人士」「現任/最近期曾任職單位」「職銜」;UI 訊息含「實質受益人為持股25%以上」「年滿65歲高齡金融消費者」「投資人符合弱勢群體條件,須提供自主申購聲明書」。

- **UI 2,541 行 + 主檔 123 欄**,兩項都是本片第一。

**四眼覆核後的跨表更新(本片最重的一段)**

`OFDM123A_PO_AfterAUD` 同時掛 `AfterApprove` 與 `AfterApproveDelete`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:35-36`),**這次是真的會跑**:

| 步驟 | 動作 | 錨點 |
|---|---|---|
| 1 | `if (!row.ISCHGBMS && args.Status != ApproveDelete) continue;` —— 沒勾「同步 BMS」且不是刪除覆核就跳過 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:64` |
| 2 | 只有「這筆是最新的」才同步:`SELECT COUNT(1) FROM OFD123A WHERE BF_NO = :BF_NO AND SET_DATE > :SET_DATE` 回 0 才往下 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:67-72` |
| 3(一般覆核) | 依 `BF_COUNTRY_X == "01"` 決定取本人欄位還是 `_LP` 欄位,把 `EFFECT_CODE2`(空則 `EFFECT_CODE1`)轉成 `'01'→'1'` / `'02'→'2'` / 其餘 `'3'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:76-86` |
| 3'(刪除覆核) | 找同戶號**前一筆**調查表(`ORDER BY SET_DATE DESC` + `ROWNUM = 1`),用它的值回填;一筆都沒有就填空白 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:88-115` |
| 4 | `INSERT INTO BMS001ACHG (…)` 寫一筆受益人異動記錄,`BF_CHG_KYC` 寫死 `'Y'`、`SOURCE_CD` 寫死 `'2'`、`SYSTEM_ID` 寫死 `'0'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:123`、`:218`、`:242` |
| 5 | `UPDATE BMS001A SET TERMINATE_DATE = :TERMINATE_DATE, KYC_RISK_ATTR = :KYC_RISK_ATTR WHERE BF_NO = '…'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:245-254` |

**步驟 5 有兩個缺陷,一個比一個嚴重**:

1. **`WHERE BF_NO = '" + row.BF_NO + "'`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:248`)。同一段 SQL 的 `SET` 子句用具名參數,`WHERE` 卻用字串串接,而且把數值欄包成字串。**風格不一致之外,`BF_NO` 是 `NUMBER`,加引號會觸發隱式轉換,索引用不到。**

2. **回傳筆數檢查被註解**: `` dbProduct.ExecuteNonQuery(cmdUpdate, args.DbTran); //if (dbProduct.ExecuteNonQuery(cmdUpdate, args.DbTran) != 1) //throw new ApplicationException("受益人風險屬性及KYC終止日更新失敗");`` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:254-256`)。**現在無論更新到幾筆——包含 0 筆——四眼都會回報成功。**KYC 風險屬性沒寫進受益人主檔,現場不會有任何徵兆。這是本片**最會咬人的缺陷**,列為附錄 E 的最高嚴重度。

同一段的 `INSERT INTO BMS001ACHG`(`:242`)也沒檢查回傳值,問題同性質但影響小一點(只是異動記錄漏一筆)。

**UI 端的檢核很密,而且大量依 `SOURCE_CD` 分岔**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 客戶統編 / 戶號 / 輸入日期起迄 三者全空 | 「客戶統編、戶號、輸入日期起迄 三者選一 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:150-152` |
| 存檔前(僅新增) | `SOURCE_CD == "1"`(線上) | 「後台無法選擇線上來源！」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:409-411` |
| 存檔前 | 受益人類別未選 / 不為自然人 / 不為法人 | 三句 | **詢問→阻擋**(`ShowMessage` 後 `e.Cancel = true`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:295-304`、`:347-356` |
| 存檔前 | 持股 25% 以上未填實質受益人 | 「實質受益人為持股25%以上,「實質受益人」為必填！」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:474` |
| 存檔前 | 投資工具 / 資金來源 / 擔任職務 / 資訊來源 各未選 | 四句「請至少選擇一項！」+ 選「其它」時的必填 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:490`、`:500-508`、`:523-531`、`:551-559` |
| 存檔前 | 職業類別非家管 / 學生 / 學齡前 / 無業 時任職機構空白 | 「職業類別不為家管、學生、學齡前及無業者時,任職機構 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:567` |
| 存檔前 | 教育程度國中以下 / 重大傷病 未答所列情形 | 兩句,**訊息把欄位中文名串進去** | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:583`、`:588` |
| 存檔前 | 年滿 65 歲未答三題(生活自理 / 財務狀況 / 理財知識) | 三句「年滿65歲高齡金融消費者,… 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:598-610` |
| 存檔前 | 年齡與生日對不上 | 「年齡層輸入有誤,請確認！」,選 `Cancel` 才擋 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:659` |
| 存檔前 | 符合弱勢群體卻沒勾自主申購聲明書 | 「投資人符合弱勢群體條件,須提供自主申購聲明書！」(**同一句出現 3 處**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:683`、`:706`、`:724` |
| 全程 | `SOURCE_CD == "3"`(郵局)時跳過一整組檢核 | 資料照存 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:419`、`:670`、`:846`、`:2212` |
| 維護頁載入 | `SOURCE_CD != "1"` 時戶號欄可編、可刪;`== "1"`(線上)時唯讀且**刪除鈕停用** | — | 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:105-108` |

**跨表更新**:`BMS001ACHG`(INSERT)、`BMS001A`(UPDATE)。**這是本片唯一會寫別的模組的表的畫面**,見 §8.1。

---

### 4.5 必答問題一:`OFDM123` 與 `OFDM123A` **不是**境內 / 境外的一對

`ofd7.md §4.4` 查證過 OFD 的 `A` 後綴慣例:`OFDM194`(`OFD194A`,境內)與 `OFDM194B`(`OFD194`,境外)是同一業務概念的境內外兩張表,靠 `FUND_TYPE` / `SHORE_ID` 區分,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301`。

**這條慣例套不到 `OFDM123` / `OFDM123A` 身上。** 照 `ofd7.md §4.4` 的四條檢驗法逐條走:

| # | 檢驗 | 結果 |
|---|---|---|
| 1 | **有沒有 `FUND_TYPE` / `SHORE_ID` / 境內外字樣?** | **完全沒有**。對 `OFDM123_PO.cs` / `OFDM123A_PO.cs` / `OFDM123.cs` / `OFDM123A.cs` 四個檔搜 `FUND_TYPE`、`SHORE_ID`,零命中。`OFDM123A` 只有 `SOURCE_CD`,值域是 `CTL014` 的 `'455'`(線上 / 後台 / 郵局),不是 `SHORE_ID` 的 `'018'`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:39`) |
| 2 | **SQL join 哪張基金主檔?** | **兩支都不 join 基金主檔。** `OFDM123` join 的是 `BMS001` + `CTL014`×5 + `OFD068` + `OFD743` + `OFD741`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:250-262`、`:339-340`);`OFDM123A` join 的是 `BMS001A` + `OFD124A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:229`、`:298`)。境內外的判別點(`OFD081A` vs `OFD081`)在兩支裡都不存在 |
| 3 | **欄位形狀有沒有跟著境內外走?** | 沒有,兩張表形狀天差地遠:`OFD124` 41 欄、鍵是 `KYC_ANS_NO`(問卷書號);`OFD123A` 123 欄、鍵是 `SET_DATE` + `FH_CD` + `ID_NO`。**連主鍵維度都不同** |
| 4 | **有沒有共同欄位可以串?** | 交集只有 `BF_NO` / `ID_NO` 這種全庫通用的客戶識別欄,沒有任何一段程式同時讀兩張表 |

**逐層相似度(非空白行序列比對,`difflib.SequenceMatcher`)**:

| 層 | `OFDM123` 側 | 行數 | `OFDM123A` 側 | 行數 | 相似度 |
|---|---|---|---|---|---|
| PO | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs` | 588 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs` | 603 | **0.106** |
| UI | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123.cs` | 771 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs` | 2,383 | **0.023** |
| Control | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM123_Ctl.cs` | 311 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM123A_Ctl.cs` | 210 | **0.088** |
| Model xsd | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM123Model.xsd` | 332 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM123AModel.xsd` | 435 | **0.115** |

對照組:`ofd7.md §4.4` 記的 `OFDM194` / `OFDM194B` 那一對,`FeeTypeValidate` 是「一字不差、只差表名」。**本片這一對連 10% 都不到,四層一致地低。它們不是一對,是兩套系統。**

**那它們到底是什麼關係?** 兩支都在做「認識客戶」,但是**兩個世代的兩套問卷**:

| 面向 | `OFDM123`(`OFD124` / `OFD125`) | `OFDM123A`(`OFD123A` / `OFD124A`) |
|---|---|---|
| PO 基底 | `BasicEVAPO`(死) | `BaseEVADaoPO`(活) |
| SQL 方言 | T-SQL(`[表名]` / `newid()` / `SELECT TOP` / `GetDate()`) | Oracle(`:參數` / `NVL` / `DECODE` / `ROWNUM` / `TO_CHAR`) |
| 資料結構 | 題庫驅動:答卷 + 逐題答案,題目來自 `OFD741`~`OFD745`,可換版本 | 欄位驅動:123 個固定欄位,改題目要改 schema |
| 風險屬性欄 | `KYC_RISK_ATTR` + `KYC_RISK_ATTR_SELF`,值域 `CTL014` `'404'` | `EFFECT_CODE1` / `EFFECT_CODE2`,在 PO 裡硬轉成 `'1'` / `'2'` / `'3'` |
| 覆核後同步受益人主檔 | **沒有**(只寫跳號一覽表) | **有**(`BMS001ACHG` + `BMS001A`) |
| 法遵條款 | 無 | 高齡(65 歲)、弱勢族群、實質受益人 25%、PEP |
| 四眼 13 欄在 Model 裡 | **沒有** | 有 |
| 外部引用 | `BMSM001` / `BMSM006` 的引用**全被註解** | `BasicBMS_PO` / `Utility_PO` / `BMSM001` / `BMSM006` 都在用 |

**結論:`OFDM123` 是被取代的那一代,`OFDM123A` 是現役。** `A` 後綴在這裡代表的是「改版」,不是「境內」。

**佐證(最硬的一條)**:`BMSM001` 與 `BMSM006` 對 `OFD124` 的引用**全部是註解**,而且註解上還留著日期與理由:

| 註解 | 錨點 |
|---|---|
| `//xTableMapping tpOFD124 = new xTableMapping("OFD124", "OFD124");` / `//this.DetailTable.Add(tpOFD124);` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:152-153` |
| `#region OFD124的判斷非聯名戶的最近一筆資料 2013/04/03 注解MainLine版不使用` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:610` |
| `//this.DetailTable.Add(new xTableMapping("OFD124", "OFD124"));` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:104` |
| `#region KYC風險屬性(OFD124)` 底下整段 `//else if (strTableName == "OFD124")` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2163-2166` |

**「2013/04/03 注解 MainLine 版不使用」這一句直接寫出了停用時間點。**

> ⚠ **但有一件事對不上,必須標出來:`OFDM123` 掛著 `SrNoCommentProcessor`(跳號一覽表),那是新世代的共用元件。** 如果這支畫面 2013 年就不用了,後來為什麼還會被加掛新元件?兩種解釋:(a) 跳號一覽表是對全庫 M 畫面無差別加掛的,沒人檢查哪些是死的;(b) `OFD124` 這條線在某個時間點又被啟用過。**本文採 (a),標〔假設〕**,依據是同一組 `JumpSrNo_After*` 在 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs` 等多支畫面出現、寫法完全一致;但**沒有找到決定性證據**,要確認得查版控歷史或問現場。

---

### 4.6 必答問題二:`OFDM125A` 的 `OFD125A_M` 是**實體表**,不是暫存也不是檢視

`OFDM125A` 是全庫少見的寫法:**主檔名帶 `_M` 後綴,明細名反而是不帶後綴的 `OFD125A`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:39-40`)。查證結果:

| 追問 | 答案 | 證據 |
|---|---|---|
| 是實體表嗎? | **是,而且有 DDL** | `DB/Table/create_OFD125A_M.sql`:`create table sw.OFD125A_M (...) tablespace USERDATA` |
| 是暫存表 / 檢視嗎? | **都不是** | 沒有 `create view`、沒有 `GLOBAL TEMPORARY`、有 `tablespace` 與 `storage` 子句,還建了 public synonym:`create public synonym OFD125A_M for SW.OFD125A_M;` |
| 中文名是什麼? | **董監事設定主檔資料** | `DB/Table/create_OFD125A_M.sql` 的 `comment on table sw.OFD125A_M is '董監事設定主檔資料'` |
| 明細呢? | **董監事設定明細資料** | `DB/Table/create_OFD125A.sql` 的 `comment on table` |
| 有 PK 嗎? | 有,**只有 `BF_NO` 一欄** | `alter table sw.OFD125A_M add constraint OFD125A_M_PK primary key (BF_NO)` |
| 有 trigger 嗎? | 有,`DATAFLAG` 自動填 | `DB/Table/create_OFD125A_M_Trigger.sql`:`OFD125A_M_DATAFLAG` before update or insert,`utl_raw.cast_to_raw(sys_guid())` |
| 誰在用? | **只有 `OFDM125A`** | 對 `Dev/` 全樹搜 `OFD125A_M`,唯一命中的 `.cs` 是 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs` |

**所以 `_M` 後綴在這裡就是 `Master` 的縮寫,不是任何機制。** 為什麼要多一張只有 `BF_NO` + 四眼 15 欄的主檔?因為 `OFD125A`(明細)的 PK 是 `BF_NO` + `SRNO`,而四眼引擎的單筆型 PO 需要「一筆主檔」當掛載點(`architecture.md §3.9`)。**`OFD125A_M` 存在的唯一理由就是給四眼一個 `BF_NO` 層級的錨。** 這與 `ofd7.md §2.2` 的 `_UPD`(暫存表機制)完全不同——**別把兩種後綴混為一談**。

**這支畫面還是遷移的活標本。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:28-30`:

```
//public class OFDM125A_PO : BasicEVAPO
…
public class OFDM125A_PO : BaseEVADaoPO, IOFDM125A_PO
```

上下兩行就是遷移前後。遷移後的版本用 `dbProduct`(`:60`、`:73`、`:81`、`:94`)而不是 `dbTA`——**這就是 §0.2 那 8 支缺的那一步**。

- **用途(推測)**:替某位受益人(法人)登錄董監事 / 股東 / 實質受益人名單,每人一列,記統編、中英文姓名、生日、國籍、建檔日、終止日、職務、兩個問項(`SHOLDER_Q1` / `SHOLDER_Q2`)與備註。

- **明細 SQL**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:188-208`,`LEFT JOIN BMS001A`。

- **註解掉的職務中文名**:`//strSQL += " LEFT JOIN (select CODE,CODE_DESCRP from COD006A where code_sort='B3') C6A ON C6A.CODE=OFD125A.SHOLDER_POSITION"`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:207`,對應被註解的 `:202`)。**畫面上的「職務」欄目前只有代碼沒有中文。**

**主檔查詢有一段查詢條件被改寫成子查詢,而且是字串串接**:

原本是兩段註解掉的 `to_char(OFD125A_M.updatedate,'yyyymmdd') >= '…'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:145`、`:153`),現行版本改成:

```
and OFD125A_M.BF_NO IN (select bf_no from ofd125a where (in_date between 'x' AND 'y')
                        or (end_date between 'x' AND 'y') group by bf_no )
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:157`)。三個問題:

1. **`strINDATE` / `strENDDATE` 直接串進 SQL**,沒有參數化。

2. **只檢查 `strINDATE != string.Empty`**(`:155`),沒檢查 `strENDDATE`。使用者只填起日不填迄日 → `between '20260101' AND ''` → **`between` 上界是空字串,Oracle 字串比較下什麼都撈不到,而且不會報錯**。UI 端有擋「起迄必須皆(不)填寫」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:149`),但那是 UI,ToDo 頁與其他入口不一定經過。

3. **語意從「主檔的最後修改日」變成「明細的建檔日或終止日」**,而畫面標籤仍寫「最近更新日期」(grep 自 Designer)。**標籤與實際查的欄位不一致。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:65` |
| 存檔前 | 明細內容有誤 | 「明細資料 輸入有誤」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:69` |
| 存檔前 | 明細必填欄有空 | 「(欄名) 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:76` |
| 查詢前 | 最近更新日期只填一邊 | 「最近更新日期(起)(迄) 必須皆(不)填寫」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:149` |
| 查詢前 | 最近更新日期(起) > (迄) | 「最近更新日期(起) 不可大於 最近更新日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:151` |
| 主檔取數 | 日期條件變成「明細的建檔日或終止日落在區間」 | 主檔的修改日不在區間、但明細有動過的,也會被撈出來 | **過濾語意改變(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:157` |

**跨表更新**:無。

---

### 4.7 必答問題三:`OFDM157` 的 `HIGHRISK_COUNTRY` 是共用參數表,而且這支畫面是從 `OFDM126` 複製的

`HIGHRISK_COUNTRY` 是**本片、也是整個 OFD 模組唯一不照 `OFDnnn` 命名的主檔**(`architecture.md §2.6` 講的命名鐵律例外,這是新的一條)。逐條回答:

| 追問 | 答案 | 證據 |
|---|---|---|
| 是共用參數表嗎? | **是。** 它是「高風險國別」的參數檔,由法遵單位維護,供全系統判斷客戶國籍風險 | 欄位 `COUNTRY_CD` / `RISK_TYPE`(Caption「依法遵通知來源」)/ `RISK_LEVEL`(「風險等級」)/ `BNG_DATE` / `END_DATE` |
| 有四眼嗎? | **有,而且齊。** 23 欄裡 13 欄是四眼欄,`STATUS` 不可空 | `atlas_scan --table HIGHRISK_COUNTRY`;xsd 在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM157Model.xsd` |
| 誰還在讀它? | **Common 的 `BasicBMS_PO`,而且不是直接讀表,是讀 view `V_TA_HIGHRISK_COUNTRY`** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69`:`,NVL(V_TA_HIGHRISK_COUNTRY.RISK_LEVEL,'L') COUNTRY_RISK_LEVEL`;`:75`:`LEFT JOIN V_TA_HIGHRISK_COUNTRY ON BMS001A.BF_NATIONALITY=V_TA_HIGHRISK_COUNTRY.COUNTRY_CD` |
| 那個 view 在 `DB/` 裡嗎? | **不在。** `DB/View/` 底下沒有 `V_TA_HIGHRISK_COUNTRY`,`DB/Table/` 也沒有 `HIGHRISK_COUNTRY` 的建表腳本 | 對 `DB/` 全樹搜 `HIGHRISK`,零命中 |
| 還有別的地方用嗎? | 沒有。`Dev/` 全樹除了 `ATLAS.OFD` 自己的六層加 `BasicBMS_PO`,只剩編譯產物(`obj/Debug/*.dll`) | 全樹搜 `HIGHRISK_COUNTRY` |

**「表與 view 都不在版控」這件事本身是一條缺陷**:`architecture.md §5.6` 說 `DB/Table/` 是變更腳本的落腳處,但這張跨模組共用的法遵參數表**連建表腳本都沒有進版控**。改欄位時沒有任何地方可以對照。已加進本文 meta 的 `refcheck-ignore`。

**這支畫面是 `OFDM126` 的複製品,證據三條:**

| # | 證據 | 數值 / 錨點 |
|---|---|---|
| 1 | 逐層相似度極高 | PO **0.779**、Control **0.858**、UI **0.685**(非空白行序列比對) |
| 2 | **註解沒改** | `OFDM157_PO_BeforeAdd` 上面寫著 `// 取得行銷說明 流水號最大值`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:73`)——「行銷說明」是 `OFDM126` 的業務,`OFDM157` 管的是國別 |
| 3 | 結構一模一樣 | 兩支的 `BuildMasterSQLString` 都是「`SELECT 表.*` + `EVAStringHelper.AddParam` + `if ToDO` + `ORDER BY`」,連 `#region Pirvate Method` 的拼字錯誤都一樣(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM126_PO.cs:90` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:90`) |

**複製帶來兩個真缺陷:**

**(a) 主檔 SQL 用 `JOIN` 而不是 `LEFT JOIN`。**

```
SELECT HIGHRISK_COUNTRY.* ,OFD008.COUNTRY_NAME
  FROM HIGHRISK_COUNTRY JOIN OFD008 ON HIGHRISK_COUNTRY.COUNTRY_CD=OFD008.COUNTRY_CD
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:99-102`)。`OFD008`(國別檔)沒有的國碼,**在 `OFDM157` 查不到、改不到、也刪不掉,而且沒有任何提示**。`OFDM126` 原版沒有 join,所以是加 join 時選錯了寫法。**高風險國別漏一個國家,法遵上是真的會出事的。**

**(b) `COUNTRY_NAME` 在結果集裡出現兩次。** `HIGHRISK_COUNTRY.*` 本身就含 `COUNTRY_NAME`(Caption「國別中文名稱」),再 `SELECT` 一個 `OFD008.COUNTRY_NAME`。**同名欄重複,實際綁到哪一個由 provider 決定。** 畫面上顯示的到底是自己存的還是國別檔的,從程式看不出來。

**其餘與 `OFDM126` 共有的問題:**

| 問題 | 內容 | 錨點 |
|---|---|---|
| 流水號競態 | `SELECT (NVL(MAX(DATA_SEQ),0) + 1) FROM HIGHRISK_COUNTRY WHERE COUNTRY_CD = '{0}'`,沒有鎖 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:76-79` |
| 字串串接 | 同上,`COUNTRY_CD` 走 `string.Format` | 同上 |
| 混世代 | `BaseEVADaoPO`(新)裡用 `EVAStringHelper`(舊世代 helper),而 `ofd7.md §4.0` 記的新世代畫面用 `xEVAStringHelper` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:104` |

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 有效日期(起) > (迄) | 「有效日期(起) 不可大於 有效日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM157.cs:58` |
| 查詢前 | 有效日期(起) > (迄) | 「有效日期(起)不可大於有效日期(迄)」(**同一件事兩句不同寫法**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM157.cs:145-147` |
| 主檔取數 | `JOIN OFD008` | 國別檔沒有的國碼整筆消失 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:101` |
| 伺服端 `BeforeAdd` | 取 `DATA_SEQ` 流水號 | 併發時會撞 PK | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:69-86` |

**沒有任何檢核擋「同一個國別的有效期間重疊」**——`DATA_SEQ` 讓同一個 `COUNTRY_CD` 可以有無限多列,期間要不要重疊完全沒人管。下游 `BasicBMS_PO` 的 `LEFT JOIN` 只用 `COUNTRY_CD` 對,**沒有帶日期條件**(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:75`)——同一個國別有兩列就會**放大 `BMS001A` 的查詢結果筆數**。列入附錄 E。

**跨表更新**:無。

### 4.8 `OFDM114` — 受益人 × 基金 停止交易設定

- **用途(推測)**:針對某位受益人的某一檔基金,在某段期間停止某種交易別,可加附註。

- **推測依據**:UI 標籤「交易別」「停止交易日期(起)/(迄)」「戶號」「基金代碼」「基金資料來源 / 境內基金 / 境外基金」「附註」。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:102-160`。

**它的基金來源 CTE 有三個分支,第三個是寫死的假資料列**:

| 分支 | 來源 | `FUND_TYPE` | 錨點 |
|---|---|---|---|
| 1 | `OFD081A` `LEFT JOIN OFD0811A` | `'2'`(境內) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:111-115` |
| 2 | `OFD081` | `'1'`(境外) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:117-122` |
| 3 | **`FROM DUAL`**,`FUND_ID` 寫死 `'ALL FUNDS'`、名稱寫死 `'所有基金'` | `'0'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:124-129` |

**「全部基金」這個選項是靠 SQL 裡一個 `FROM DUAL` 的假列做出來的,而且 `FUND_ID` 的值是字串 `'ALL FUNDS'`(含空白)。** 任何讀 `OFD114A` 的下游(EC 的 `IPJB622` / `OFDB602`、`OFDI011`、`RSPB009`,見 §8)都必須自己知道這個魔法字串,repo 內沒有任何常數定義它。**寫死常數,嚴重度中**,列入附錄 E。

`FUND_TYPE = '0'` 這個第三個值也**不在 `SHORE_ID` 的值域**(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 只有 `'1'` / `'2'`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 停止交易日期(起)空白 | 「停止交易日期(起)必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:129` |
| 存檔前 | 停止交易日期(迄)空白 | 「停止交易日期(迄)必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:134` |
| 存檔前 | 起 > 迄 | 「'停止交易日期(起)'必需小於等於'停止交易日期(迄)'!!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:295` |
| 存檔**後** | 一律跳一句提醒 | 「請記得查詢設定之停止交易日期間是否已有歷史交易資料」 | **記錄不擋** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:162`、`:209` |
| 存檔前 | 統一編號格式檢核 | 三句「統一編號格式有誤」 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:242-260`、`:274-287` |
| 存檔前 | 期間重疊提示 | `Warn02` 詢問 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM114.cs:150-152`、`:197-199` |

> ⚠ **「停止交易期間是否已有歷史交易」這件事,程式不檢查,只用一句訊息叫使用者自己去查。** 而原本應該自動檢查期間重疊的那段(`:150-152`、`:197-199`)被註解掉了。停止交易是風險控制功能,這兩件事加起來的意思是:**同一個受益人 × 基金 × 交易別可以設出互相重疊的多段停交,系統不擋也不提示。**

**跨表更新**:無。

---

### 4.9 `OFDM127` — 受益人公告金額【死畫面,但下游天天在讀】

- **用途(推測)**:設定某位受益人的「公告金額」門檻(超過就要公告 / 通報),`DATA_SEQ` 讓同一位受益人可以有多筆歷史。

- **推測依據**:UI 標籤只有三個:「公告金額」「受益人ID」「戶號」。

- **這支是本片最矛盾的一支**:畫面是死的(§0.2),但 `OFD127` 被 Common 的四個地方在讀,包含一個下拉資料來源 `GetANNOUNCE_AMTDataSrc`(`Dev/Common/Source/DataSource/UI.DataSource/TableSrc/GetANNOUNCE_AMTDataSrc.cs`)。**沒有畫面可以維護,但值還在被用。**

**它是八支死畫面裡唯一「有人試圖修好」的一支。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:311` 的註解直接寫著 `public override BasicModelVDB Update(BasicModelVDB model)//抄EVA PO`——開發者把基底的四眼流程整段複製進子類再改。四個覆寫:

| 覆寫 | 用哪個連線 | 結論 | 錨點 |
|---|---|---|---|
| `Update` | `dbPTPF`(`:317`)+ `dbTA`(`:321`、`:329`、`:331`、`:340`) | **NRE** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:311` |
| `Select` | `dbTA`(`:413`) | **NRE** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:410` |
| `Delete` | `db`(`:514`) | 無法判斷(`db` 來自 `Basic_PO`,無原始碼) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:503` |
| `Add` | `db` / `db_ToDo`(`:568`、`:572`) | 無法判斷 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:552` |

**「同一支 PO 裡四個方法用兩套連線欄位」本身就是一條缺陷**,不管 `db` 是不是 null。列入附錄 E。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 公告金額 ≤ 0 | 「公告金額必須大於0」(**兩處重複寫**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM127.cs:204`、`:208` |
| 存檔前 | `CheckAnnounce` 回傳訊息 | 訊息由伺服端決定 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM127.cs:222`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:227-310` |
| 存檔前 | 「公告金額 請先變更」 | — | **被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM127.cs:124-126` |
| 存檔前 | 受益人ID 格式 | 六句「受益人ID格式有誤」 | **整段被註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM127.cs:155-204` |

**跨表更新**:無。

---

### 4.10 `OFDM128` — 受益人 × 基金 × 交易別 公告金額【死畫面,PO 1,555 行】

- **用途(推測)**:`OFDM127` 的細緻版——把公告金額拆到「基金 × 交易類別」層級,另記交易金額、交易起訖日與上次公告日期。

- **推測依據**:UI 標籤「公告金額」「交易金額」「交易類別」「交易起始日期」「交易終止日期」「上次公告日期」「基金代碼」「戶號」「受益人ID」。

- **PO 1,555 行是本片最大的 PO**,也是死的(§0.2)。T-SQL 痕跡:`[OFD128]` 40 處、`isnull(` 10 處、`[OFD081]` 8 處、`[OFD081V]` 3 處。

三個公開方法 `GetDEC`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM128_PO.cs:1258`)、`GetFundDEC`(`:1343`)、`SetBF_NO_Data`(`:1418`)都自己開連線(`dbTA.CreateConnection()`,`:1265`、`:1294`),同樣 NRE。

**這支沒有覆寫任何四眼方法**,所以連 `OFDM127` 那種「試圖修好」的痕跡都沒有。**表格帶過。**

---

### 4.11 `OFDM129` — 受益人專屬交易條件與費率

- **用途(推測)**:替某位受益人的某一檔基金,覆寫平台預設的交易條件——最低申購 / 贖回 / 轉申購金額、最低贖回單位數、剩餘最低單位數、定買門檻、收益分配最小配現金額、轉換手續費率與拆帳比、是否檢核牌告費率、人工控管短線交易註記。

- **推測依據**:UI 標籤(grep 自 Designer)全是上面這些,41 欄。

- **是本片被批次依賴最深的表**:`OFDB004`(一次建檔)、`OFDB331`、`NFDR022`(報表)、Common 的 `Utility_PO` / `NfdUtility_PO` 都在讀 `OFD129A`。

**它是本片唯一有「複製」功能的畫面。** `Copy<T>` 定義在介面 `IOFDM129_PO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:30`),實作在 `:587-652`,UI 端由子對話框 `OFDM129p0` 觸發(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM129.cs:340`)。流程:

| 步驟 | 動作 | 錨點 |
|---|---|---|
| 1 | 撈來源受益人的設定,撈不到就 `AddResultRow(false, -1, "來源受益人資料不存在")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:600` |
| 2 | 逐列檢查來源是否已覆核,未覆核就 `AddResultRow(false, -1, "來源受益人資料尚未覆核")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:607-614` |
| 3 | 成功 `AddResultRow(true, 1, "")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:640` |
| 4 | `catch`:兩條交易 `Rollback`、`CommonExceptionBlocker.HandleBusinessException(ex)`、`AddResultRow(false, 0, "複製失敗")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:642-650` |

**這個 `catch` 寫得比 `ofd7.md §4.4` 記的 `FeeTypeValidate` 好:它有 `Rollback`、有補結果列、也有把例外交給 `CommonExceptionBlocker`。** 本片唯一一個寫對的 `catch`,值得對照著看。

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:240-345` 有一整個 `#region Old Code`,裡面是被註解掉的舊 `Select` 覆寫。這是本片最大的一坨註解死碼,約 105 行。

**跨表更新**:`Copy` 會在兩條連線(`tran` + `tranptpf`)的交易裡寫入,其餘無。

**表格帶過的細節**:主檔 SQL `LEFT JOIN OFD081V`(`:139`);`GetFUND_DATA`(`:351`)、`GetFundDec`(`:436`)、`GetUnit_Dec`(`:512`)三個輔助查詢分別查 `OFD081A`(`:383`、`:537`)與 `FSK003`(`:458`);自己寫了一個 `AddParam`(`:179`)與 `GetParamValue`(`:227`),沒用共用 helper。

---

### 4.12 `OFDM133` — 受益人歸戶(主要窗口)

- **用途(推測)**:把數個受益人戶號歸到一個「主要窗口」戶號底下,記關係代碼與備註。

- **推測依據**:UI 標籤「主要窗口」「主要窗口戶號」「被歸戶ID」「被歸戶戶號」「明細資料」。

- **多筆型**(`BaseMultiRowEVADaoPO`),`MasterPKey` = `BF_NO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM133_PO.cs:26-27`),xsd PK 是 `RBF_NO` + `BF_NO`。**上半是「主要窗口」,下半是它底下的被歸戶清單,兩者同一張表。**

**群首用 `ROW_NUMBER()` 抓,比 `ofd7.md §4.1` 的寫死常數乾淨:**

```
FROM (SELECT ROW_NUMBER() OVER (PARTITION BY BF_NO
                                ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE, RBF_NO) NUM
            ,OFD133A.*
      FROM OFD133A) OFD133A
WHERE OFD133A.NUM = 1
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM133_PO.cs:60-68`)。`ORDER BY` 用四個欄位打破平手,不依賴魔法值,**這是本片寫得最好的一段取數**。

兩次 `LEFT JOIN BMS001A`(本人與被歸戶各一次,`:66-67`),別名 `BMS0011`。

**混世代寫法**:同一段裡同時用 `xEVAStringHelper.AllEVAColumnsForSelect`(`:59`,新)與 `EVAStringHelper.AddParam`(`:69-70`,舊)。全片有四支這樣混(`OFDM133` `OFDM135` `OFDM126` `OFDM157`),列入附錄 E。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM133.cs:57` |
| 存檔前 | 明細必填欄有空 | 「(欄名) 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM133.cs:64` |
| 存檔前 | 被歸戶戶號 = 主要窗口戶號 | 「被歸戶戶號 不可與主要窗口戶號相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM133.cs:67` |
| 存檔前 | 主歸戶戶號已被別人歸過 | 「主歸戶戶號 已設定歸屬」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM133.cs:79` |
| 存檔前 | 被歸戶戶號已被別人歸過 | 「被歸戶戶號 已設定歸屬」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM133.cs:84` |

**跨表更新**:無。

---

### 4.13 `OFDM135` — 交易指示代理人

- **用途**:替某位受益人登錄可代為下交易指示的代理人(統編 + 姓名 + 建檔日 + 終止日)。**這次不是推測**:`DB/Table/createOFD135A.sql` 的 `comment on table` 寫「交易指示代理人設定資料」。

- **多筆型**,但 **`MasterPKey` 沒有宣告**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:30` 只有 `MasterTable.Add`),而 SQL 卻用 `PARTITION BY BF_NO`(`:77`)分群。**PO 宣告與 SQL 假設不一致**,列入附錄 E。

**兩個問題:**

**(a) `JOIN BMS001A` 不是 `LEFT JOIN`。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:80`。受益人主檔對不到就整筆消失,與 §4.3 的 `OFDM123`、§4.7 的 `OFDM157` 同一型。

**(b) 日期查詢條件字串串接。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:99`,與 §4.6 的 `OFDM125A:157` 幾乎一字不差(只差大小寫)。**差別是 `OFDM135` 檢查了 `strINDATE != "" && strENDDATE != ""` 兩邊(`:97`),`OFDM125A` 只檢查一邊。這是「成對畫面只改一邊」的活例:同一段程式複製兩份,只有一份補了防呆。**

**這兩支的 UI 也幾乎相同**:`OFDM125A` 與 `OFDM135` 的 Designer 標籤字串完全一樣(「(建檔日、終止日)」「戶號」「明細資料」「最近更新日期」「計算規則」),查詢頁的三句檢核訊息也一字不差(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM135.cs:137`、`:139` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM125A.cs:149`、`:151`)。**它們是同一個模板生出來的兩支畫面**,一支管董監事、一支管代理人。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 有列被刪除 | 「不可刪除資料！如果要取消代理人,請填上終止日」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM135.cs:40` |
| 存檔前 | 代理人統編或姓名空白 | 「代理人統一編號與姓名 為必填」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM135.cs:45` |
| 查詢前 | 最近更新日期只填一邊 | 「最近更新日期(起)(迄) 必須皆(不)填寫」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM135.cs:137` |
| 查詢前 | 最近更新日期(起) > (迄) | 「最近更新日期(起) 不可大於 最近更新日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM135.cs:139` |
| 主檔取數 | `JOIN BMS001A` | 無受益人主檔的代理人設定整筆消失 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:80` |

**「不可刪除,只能填終止日」是本片唯一一支明文禁止刪除的畫面**——代理人是授權性質的資料,刪掉會失去軌跡,這個設計是對的。

**跨表更新**:無。

---

### 4.14 `OFDM154` — 基金 × 交易別 停止交易【死畫面】

- **用途(推測)**:`OFDM114` 的基金層版本——某一檔基金的某種交易別,在某段期間停止。

- **推測依據**:UI 標籤只有四個:「交易類別」「基金代碼」「生效日期」「終止日期」。PK 是 `FUND_ID` + `TRAN_TYPE` + `STOP_BNG_DATE`。

- **PO 151 行,是八支死畫面裡最小的有 SQL 的一支。**

**三個問題疊在一起:**

1. **死畫面**(`BasicEVAPO`,`dbTA` null,§0.2)。

2. **兩個事件處理器寫了沒接上**:建構子只有 `this.BeforeSelect += …`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:18`),但檔案裡另外躺著 `OFDM154_PO_BeforeGetMaintainData`(`:40-49`)與 `OFDM154_PO_BeforeGetToDoData`(`:51-60`)兩個完整的 private 方法,**永遠不會被呼叫**。連帶讓 `AppendToDoString`(`:141`)也成為死碼——`isToDoString` 只有 `BeforeGetToDoData` 會傳 `true`。

3. **字串串接 + T-SQL 方括號**:三個查詢參數(`FUND_ID` / `TRAN_TYPE` / `STOP_BNG_DATE`)都是 `strSQL += " AND [OFD154]." + Row.Name + " = " + "'" + Row.Value + "'"`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:100`、`:114`、`:128`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 終止日期 < 生效日期 | 「終止日期不可小於生效日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM154.cs:124` |

**全片檢核最少的畫面**(整支 UI 只有一條業務檢核)。沒有任何期間重疊檢查——與 `OFDM164`(有檢查,§4.17)形成對比,兩支同樣管「基金 × 期間」。

**跨表更新**:無。

---

### 4.15 `OFDM155` — 基金可轉換對應【死畫面】

- **用途(推測)**:設定某一檔基金(轉出)可以轉換到哪些基金(轉入),上半是轉出基金、下半是轉入基金清單。

- **推測依據**:UI 標籤只有兩個:「轉出基金代碼」「明細資料」;檢核訊息「轉入基金代碼 不可與轉出基金代碼相同」。

- **本片唯一的 `MultiRowEVAPO`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM155_PO.cs:12`),`MasterPKey` = `FUND_ID`(`:19`)。

**T-SQL 證據在這支特別清楚**:主檔 SQL 同時出現 `ISNULL(...)` 與 `FROM OFD155 LEFT JOIN OFD081V AS OFD081V_FUND`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM155_PO.cs:87`、`:91`)。**Oracle 的 `FROM` 子句不接受 `AS` 給表取別名**,這段 SQL 在 Oracle 上會直接語法錯誤,連 NRE 都輪不到。

主檔 SQL 還把 `SWITCH_FUND_ID` 與 `SWITCH_FUND_SHNM` 硬填成空字串 `''`(`:86`、`:88`),對應的 `LEFT JOIN OFD081V AS OFD081V_SWITCH_FUND` 被註解(`:94-95`)。**主檔清單上的「轉入基金」欄永遠是空的。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細必填欄有空 | 「(欄名) 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM155.cs:225` |
| 存檔前 | 轉入基金 = 轉出基金 | 「轉入基金代碼 不可與轉出基金代碼相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM155.cs:228` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM155.cs:234` |

**跨表更新**:無。

---

### 4.16 `OFDM156` — 交易金額門檻類別

- **用途(推測)**:定義一組「門檻類別」(`SILL_CODE`),內含六個金額門檻(自然人 / 法人 × 申購 / 買回,以及單筆 / 單日累計 / 總金額),明細 `OFD157A` 是這個門檻類別套用到哪些基金。

- **推測依據**:UI 標籤「門檻類別代碼」「門檻類別名稱」「單筆交易金額門檻」「單日累計交易金額門檻」「總金額門檻」「自然人申購」「自然人買回」「法人申購」「法人買回」「基金資料來源 / 境內 / 境外」。

**明細 SQL 的基金名稱取法值得一記**:

```
SELECT OFD157A.*, NVL(OFD081V.FUND_SH_NM, OFD081.FUND_SH_NM) AS FUND_SH_NM
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM156_PO.cs:129-134`,兩個 `LEFT JOIN`)。**用 `NVL` 串接境內外兩張基金主檔,不用 CTE**——比 `OFDM114` / `OFDM115A` 的 `UNION ALL` CTE 簡潔,但也代表本片有**三種**取基金名稱的寫法(CTE `UNION ALL`、`NVL` 雙 join、單一 `OFD081V`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 六個金額門檻全空 | 「至少必須輸入一筆金額」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM156.cs:212` |
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入！！」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM156.cs:218` |
| 加基金到明細時 | 基金已在清單中 | 「基金代碼已有選取。」 | **警示**(`Info01`,不 `e.Cancel`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM156.cs:299` |

**「至少必須輸入一筆金額」的錯誤綁在 `unumALLOT_SILL_TAMT_C` 這一個控制項上**(`:212`、`:218`),連「明細資料必須輸入」也綁在它身上。使用者看到的紅框會指向一個跟錯誤無關的欄位。小缺陷,列入附錄 E。

**跨表更新**:無。

---

### 4.17 `OFDM164` — 基金買回率設定【死畫面,但檢核邏輯最值得看】

- **用途(推測)**:設定某一檔基金在某段適用期間的「買回率(%)」與「買回次數(頻率)」,供定期買回計算使用。

- **推測依據**:UI 標籤「買回率(%)」「買回次數(頻率)」「適用期間(起)/(迄)」「基金代碼」「建檔日期」「(計算到小數無限位數)」「÷」。

**這支有本片唯一一個「期間重疊」檢核,而且踩了三個坑。**

`ChkOFD164(string Fund, DateTime BngDay, DateTime EndDay, string Type)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:171-209`):

```
SELECT COUNT(1) FROM OFD164 WHERE OFD164.FUND_ID = @FUND_ID
-- Type == "M" 時多一段:
AND (BNG_DATE <>@BNG OR BNG_DATE ='1900/01/01')
AND (((@BNG BETWEEN BNG_DATE AND END_DATE) OR (@END BETWEEN BNG_DATE AND END_DATE))
  OR (( BNG_DATE BETWEEN @BNG AND @END) OR (END_DATE BETWEEN @BNG AND @END)))
```

| # | 坑 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **Oracle 三值邏輯** | `BNG_DATE <> @BNG` 遇到 `BNG_DATE IS NULL` 回 `UNKNOWN`,那一列不會被算進重疊檢查。`OR BNG_DATE = '1900/01/01'` 也救不了 NULL。`OFD164` 沒有 DDL(附錄 A),`BNG_DATE` 是否可空**標〔假設〕缺:DB 連線** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:180` |
| 2 | **T-SQL 參數 + `SqlDbType`** | `@FUND_ID` / `@BNG` / `@END` 三個參數用 `SqlDbType.NVarChar` / `SqlDbType.DateTime` 宣告(`:190-192`),Oracle provider 吃不到 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:190-192` |
| 3 | **`dbTA.CreateConnection()`** | `:173`,§0.2 的 NRE | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:173` |

**但最會咬人的不在 PO,在 UI:伺服端出錯時不擋存檔。**

```
int i = pxy.ChkOFD164(…, "A");
if (i == -1)
{
    this.DialogWithNoStatusbar.ShowMessage(FunctionDialogStyle.Error01, ExceptionMessage.ServerSideError);
    return;                      // ← 沒有 e.Cancel = true
}
```

(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:132-137`,新增;`:94-99`,修改)。`ChkOFD164` 的 `catch` 回 `-1`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:197-201`),UI 跳一個「伺服端錯誤」對話框然後 `return`——**`e.Cancel` 保持 `false`,框架照樣往下存檔**。這正是缺陷型錄裡的「有訊息無 `return`」的變形:**有訊息、有 `return`,但少了 `e.Cancel = true`**。

**結果:只要區間重疊檢核在伺服端丟例外(以這支的狀態,必然丟),使用者按掉錯誤訊息,重疊的買回率就存進去了。** 嚴重度高,列入附錄 E。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 買回率 = 0 | 「買回率(%)不可為 0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:86`、`:124` |
| 存檔前 | 買回次數 = 0 | 「買回次數(頻率)不可為 0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:90`、`:128` |
| 存檔前 | 適用期間重疊(`i == 1`) | 「該基金設定的買回率適用期間,不可相互重疊。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:102`、`:140` |
| 存檔前 | 伺服端例外(`i == -1`) | 跳 `ServerSideError` 後 `return`,**沒有 `e.Cancel`** | **記錄不擋** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:95-99`、`:133-137` |
| 存檔前 | 適用期間(起) ≥ (迄) | 「'適用期間(起)'必須小於'適用期間(迄)'」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:179` |

**跨表更新**:無。

---

### 4.18 `OFDM161` — 定期買回排程設定【死畫面,但跨表寫入最重】

- **用途(推測)**:設定某一檔基金的定期買回排程——首次執行日、執行週期(每隔 N 個月)、每月的哪幾號執行(28 個核取方塊 + 一個「月底」)、執行迄日;存檔時把未來每一期的實際執行日**展開**寫進 `OFD162`。

- **推測依據**:UI 標籤「定期買回開始日期」「(首次執行日)」「執行週期」「每隔 N 個月」「號執行」「月底」「執行迄日」「1.指於執行定期買回的買回交易日,遇基金非營業日時,則順延。」「2.執行日期不依"公司行事曆"、"基金行事曆"設定。」

**這是本片唯一一支掛 `AfterAdd` / `AfterUpdate` / `AfterApprove` / `AfterApproveDelete` 四個寫入型事件的 PO**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:23-27`):

| 事件 | 動作 | 錨點 |
|---|---|---|
| `AfterAdd` | `DELETE FROM OFD162 WHERE FUND_ID = @FUND_ID`,再依週期與勾選的日期逐日展開,每一期 `INSERT INTO [OFD162]` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:122-289` |
| `AfterUpdate` | **與 `AfterAdd` 幾乎整段複製**(`:291-459`),同樣先 `DELETE` 再展開 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:291` |
| `AfterApprove` | `UPDATE OFD162 … FROM OFD162 …` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:460-484` |
| `AfterApproveDelete` | 清 `OFD162` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:485` |

**四個問題:**

1. **`OFD162` 沒有四眼。** 它不是宣告出來的 `DetailTable`,是手寫 SQL 寫進去的(§2.1),xsd 裡也沒有四眼 13 欄。**主檔在四眼流程中被退回或刪除時,`OFD162` 的清理只靠 `AfterApproveDelete` 一個事件;`AfterReject` 沒掛。**

2. **`AfterAdd` 與 `AfterUpdate` 是 168 行 × 2 的複製貼上。** 兩段的差異只有幾個變數名。改排程演算法要改兩處。

3. **`UPDATE OFD162 … FROM OFD162`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:463-469`)是 **T-SQL 的 `UPDATE … FROM` 語法,Oracle 完全不支援**。

4. **`DataTable.Select` 的條件字串是拼出來的**:`"FUND_ID =" + row.FUND_ID + "AND PERIOD_EXE_DATE =#" + XDay.ToString("yyyy/MM/dd") + "#"`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:201`、`:363`)。注意 `row.FUND_ID` 與 `AND` 之間**沒有空白**——`FUND_ID =F001AND PERIOD_EXE_DATE=#…#`。這條運算式在 `DataTable.Select` 上會丟例外。列入附錄 E。

**兩段檢核被 `/* */` 整段註解:**

`OFDM161_BeforeModifyButtonClicked`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:111-132`)與 `OFDM161_BeforeDeleteButtonClicked`(`:141-162`)裡,「該基金已有"定期買回計算作業(OFDB161)"執行記錄,是否繼續執行?」這個詢問整段被 `/* … */` 包起來。**連帶讓 PO 的 `ChkOFD166`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:551`)變成沒有呼叫者的死碼。**

後果:**已經跑過定期買回的基金,排程可以被無聲改掉或刪掉,不會有任何提醒。** 嚴重度高——這正好是缺陷型錄的「被註解但外殼還在的檢核」。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 指定執行日期一個都沒勾 | 「指定執行日期至少需勾選一筆資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:201` |
| 存檔前 | 執行週期 ≤ 0 | 「執行週期 必須大於0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:206` |
| 存檔前 | 執行迄日 < 首次執行日 | 「執行迄日 不可小於首次執行日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:211` |
| 存檔前 | 執行迄日 > 2099/12/31 | 「執行迄日 不可大於2099/12/31」〔客戶特定〕 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:216` |
| 修改 / 刪除前 | 該基金已有 `OFDB161` 執行記錄 | 詢問「是否繼續執行?」 | **整段被 `/* */` 註解** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:111-132`、`:141-162` |

**跨表更新**:`OFD162`(DELETE + INSERT + UPDATE),見上。

---

### 4.19 `OFDM163` — 定期買回自動發送時間【死畫面,全庫最小的 PO】

- **用途**:一顆全系統共用的時間參數——定期買回計算作業的自動發送時間。**UI 上的說明文字自己講得很清楚**:「提醒說明: 1.設定為00:00,表單已約定定期買回計算基礎,不可任意調整。 2.所有基金共用。」〔客戶特定〕

- **PO 只有 25 行**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM163_PO.cs:8-24`),只做一件事:`this.MasterTable = new TableMapping("OFD163", "OFDM163");`。**沒有掛任何事件、沒有任何 SQL**——是八支死畫面裡唯一連 `BeforeSelect` 都沒有的。它完全靠 `BasicEVAPO` 的預設流程,而那個流程第一行就是 `dbTA.CreateConnection()`。

**UI 端把三顆按鈕停掉,只留「修改」:**

```
this.ButtonClearEnable  = false;  // 清空按鈕不可按
this.ButtonDeleteEnable = false;  // 刪除按鈕不可按
this.ButtonAddEnable    = false;  // 新增按鈕不可按
```

(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:32-34`)。**這是本片唯一一支「單列參數表」的做法**——資料只有一筆,不能新增也不能刪除。

**兩個缺陷:**

**(a) 欄位名前後對不上。** `Dev/ATLAS.OFD/Source/UI/UI.OFD/App.config:819` 宣告 `pkey="LOCK_GAIN_PROCESS_TIME"`,UI 的輸入框叫 `txtLOCK_GAIN_PROCESS_TIME`,**但存檔時寫進去的欄位是 `PERIOD_REDEM_PROCESS_TIME`**:

```
row.PERIOD_REDEM_PROCESS_TIME = arySendTime[0] + arySendTime[1];
```

(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:54`)。而 xsd **完全沒有宣告 PK**(§2.2)。三個地方三種說法。**〔假設〕`LOCK_GAIN_PROCESS_TIME` 是複製別的畫面時沒改到的殘留**,依據是 `OFD163` 的業務是「定期買回」(`PERIOD_REDEM`)而不是「鎖利」(`LOCK_GAIN`),而 `OFDB161` 也是定期買回批次。

**(b) `Split(':')` 沒有檢查結果長度。**

```
arySendTime = this.txtLOCK_GAIN_PROCESS_TIME.Text.Trim().Split(':');
row.PERIOD_REDEM_PROCESS_TIME = arySendTime[0] + arySendTime[1];
```

(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:53-54`)。使用者打 `0900`(沒有冒號)→ `arySendTime.Length == 1` → **`IndexOutOfRangeException`**。`DoValidate`(`:95` 只做 `validatorManager1` 的必填)不檢查格式。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `validatorManager1` 必填 | 由 Designer 設定決定 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:95` |
| 存檔前 | 時間格式不含 `:` | **無檢核,直接例外** | 記錄不擋(實為當掉) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:53-54` |
| 畫面初始 | 新增 / 刪除 / 清空 三鈕停用 | — | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:32-34` |

**跨表更新**:無。**但 `OFD163` 被 `OFDB161` 讀**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs`)——**參數表活著,維護畫面死了**,與 §4.9 的 `OFD127` 同一種處境。

---

### 4.20 D 塊:`OFDM126`(行銷說明)與 `OFDM151`(查詢群組)

這兩支業務上毫無關聯,只因為都不屬於 A / B / C 三塊而放在一起。

#### 4.20.1 `OFDM126` — 行銷說明文字

- **用途(推測)**:維護一組「行銷說明代碼」(`ST_CD`)底下的說明文字與有效期間。`DATA_SEQ` 讓同一個代碼可以有多個版本。

- **推測依據**:欄位 Caption「行銷說明代碼」「行銷說明」「有效日期(起)/(迄)」;UI 標籤「行銷說明文字」。

- **下游**:`OFDR285`(OFD 報表)與 `NFDR074`(NFD 報表)。

- **結構**:見 §4.7——`OFDM157` 就是從這支複製的,兩支的 `BuildMasterSQLString` 只差表名與欄位清單。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 有效日期(起) > (迄) | 「有效日期(起) 不可大於 有效日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM126.cs:57` |
| 存檔前 | 伺服端回傳訊息 | `view.Util.Result[0].ReturnMessage` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM126.cs:69` |
| 查詢前 | 有效日期(起) > (迄) | 「有效日期(起)不可大於有效日期(迄)」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM126.cs:166-168` |
| 伺服端 `BeforeAdd` | 取 `DATA_SEQ` 流水號(`MAX + 1`,無鎖,`string.Format` 串 `ST_CD`) | 併發撞 PK | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM126_PO.cs:69-86` |

**跟 `OFDM157` 一樣,沒有任何檢核擋「同一個 `ST_CD` 的有效期間重疊」。**

#### 4.20.2 `OFDM151` — 查詢群組(員工 × 基金查詢權限)

- **用途(推測)**:定義一個「查詢群組」(`QUERY_GRPCD` + 中文名),勾選哪些員工屬於這個群組(`OFD152A`)、這個群組可以查哪些基金(`OFD153A`)。

- **推測依據**:UI 標籤只有四個:「群組代碼」「群組中文名稱」「使用者資料」「基金資料」;明細 SQL 一邊 `RIGHT OUTER JOIN COD009`(員工)、一邊 `RIGHT OUTER JOIN OFD081A`(境內基金)。

- **下游**:`BasicOFD_PO`(Common)與 `OFDI058`(查詢畫面)讀 `OFD152A` / `OFD153A`。**這是一張權限表,改壞了會讓人看到不該看的基金。**

**本片唯一的三表結構**(主檔 + 兩張明細,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:37-39`)。兩張明細的取數手法一模一樣:

```
SELECT CASE WHEN QUERY_GRPCD IS NULL THEN 0 ELSE 1 END AS ISCHECK
      ,NVL(OFD152A.QUERY_GRPCD,'<群組代碼>') AS QUERY_GRPCD
      ,COD009.…
  FROM OFD152A
 RIGHT OUTER JOIN COD009 ON OFD152A.EMP_NO = COD009.EMP_NO
   AND (OFD152A.QUERY_GRPCD IS NULL OR OFD152A.QUERY_GRPCD = '<群組代碼>')
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:220-235`,基金版在 `:247-260`)。**`RIGHT OUTER JOIN` 是為了「把全部員工都列出來,有設定的打勾」** ——這是這支畫面的核心手法,不是筆誤。

**五個缺陷,一個比一個實際:**

| # | 缺陷 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **群組代碼直接串進 SQL,而且串三次** | `'" + Row.Value + "'` 出現在 `NVL(...)`、`ON` 條件、主檔 `WHERE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:183`、`:221`、`:232`、`:248`、`:256` |
| 2 | **沒有 `QUERY_GRPCD` 參數時回空字串** | `BuildDetailSQLString` 的兩個 `if` 都不成立時回 `string.Empty`,呼叫端照樣 `dbProduct.GetSqlStringCommand("")`(`:86`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:209-265` |
| 3 | **明細表名用硬字串比對** | `if (strTableName == "OFD152A")` / `== "OFD153A"`,不是 `this.DetailTable[0].dbTableName`。改 `xTableMapping` 就會靜默失效 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:214`、`:240` |
| 4 | **`AppendToDoString` 是死碼** | `BuildMasterSQLString(model, false)` 兩處都傳 `false`,且 `BeforeGetToDoData` 沒訂閱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:64`、`:78`、`:192-195` |
| 5 | **`GetAddData` 的 `catch` 把錯誤變成一列結果** | `catch { AddResultRow(false, 0, ex.Message) }`——比不補結果列好,但**把 DB 例外訊息原封不動丟到前端** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:145-149` |

**`OFD153A` 只掛境內基金。** `GetAddData` 與明細 SQL 都只 `FROM OFD081A` / `RIGHT OUTER JOIN OFD081A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:130`、`:254`),**沒有 `OFD081`(境外)**。查詢群組**無法授權境外基金**——這可能是刻意的,也可能是漏的。**標〔假設〕**,依據是同片其他畫面(`OFDM114` `OFDM115A` `OFDM156`)都做了境內外聯集,只有這支沒有。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 員工明細一筆都沒勾 | 「請至少勾選一筆員工資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM151.cs:155` |
| 存檔前 | 基金明細一筆都沒勾 | 「請至少勾選一筆基金資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM151.cs:170` |
| 新增資料載入後 | `GetAddData` 失敗 | 顯示 `ProcessVDB.Util.Result[0].ReturnMessage`(可能是 Oracle 原始錯誤訊息) | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM151.cs:109` |
| 明細取數 | 沒帶 `QUERY_GRPCD` | SQL 為空字串 | **過濾(無提示,或直接例外)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:209-265` |
| 明細取數 | 只 join `OFD081A` | 境外基金不出現在可授權清單 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:254` |

**跨表更新**:無。

## 5. 查詢畫面(I)

**本片無 I 畫面。**`DataEntity.OFD6` 只收 M 型的 Model,查詢型畫面在 `Dev/ATLAS.OFD.Query` 與 `Dev/ATLAS.OFDI` 兩個專案(見 §8.2),不屬於本切片。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**`DataEntity.OFD6` 底下沒有 B 型 Model,20 支 UI 也沒有任何一支開出 `xOneStepProcessForm` 型的子視窗——四個子對話框全是 M 畫面的一般對話框(§3.3)。與批次的關係是單向被讀:`OFDB161` 讀 `OFD163`、`OFDB004` 與 `OFDB331` 讀 `OFD129A`(§8.3)。

## 7. 報表(R)

**本片無 R 畫面。**`DataEntity.OFD6` 底下沒有任何 `*R*Model.xsd`。讀本片資料的報表在別的專案:

| rpt | 對應畫面 | 取數來源 | 錨點 |
|---|---|---|---|
| `OFDR285` | `OFDM126` | `OFD126A` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR285_PO.cs` |
| `NFDR074` | `OFDM126` | `OFD126A` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR074_PO.cs` |
| `NFDR022` | `OFDM129` | `OFD129A` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR022_PO.cs` |

**只有兩張表(`OFD126A` / `OFD129A`)有報表在讀。** 其餘 21 張表在 repo 內沒有任何報表引用。

## 8. 跨模組共用

```text
[圖] OFD6 五組跨模組關係:OFDM123A 寫回 BMS、Common 共用 PO 讀五張表、兩張孤兒參數表、批次與報表、查詢模組
圖中文字:A 唯一一條寫出去的線:OFDM123A 覆核後改 BMS 的表 / OFDM123A 覆核 / AfterApprove / AfterApproveDelete / INSERT BMS001ACHG / 受益人異動記錄 / UPDATE BMS001A / 風險屬性 + KYC 終止日 / 回傳筆數檢查被註解 / 0 筆也算成功 / OFDM122A 覆核 / 同一份程式 199 行全註解 / 什麼都不做 / 自主聲明書不同步回主檔 / 兩個入口行為不一致 / 改一邊要記得看另一邊 / B Common 共用 PO 讀本片五張表 / BasicBMS_PO / V_TA_HIGHRISK_COUNTRY 不在版控 / BasicOFD_PO / Ctl / Pxy / OFD125A OFD127 OFD135A OFD152A OFD153A / ucTradeDeputyData / 共用控制項直接吃 OFD125A / C 兩張表活著,維護畫面卻是死的 / OFD127 公告金額 / 畫面 OFDM127 死 / GetANNOUNCE_AMTDataSrc / 下拉天天在讀 / OFD163 發送時間 / 畫面 OFDM163 死 / OFDB161 批次在讀 / 只能下 SQL 維護 / D 批次與報表:只有兩張表有報表在讀 / OFD129A / OFDB004 OFDB331 NFDR022 / OFD126A / OFDR285 NFDR074 / 其餘 21 張 / 沒有任何報表引用 / OFD162 / 只有寫入者 沒有讀取者 / E 查詢與其他模組:只讀不寫 / OFD114A / OFDI011 RSPB009 IPJB622 OFDB602 / OFD115A / CLSM002 CODM006 OFDI907 OFDI011 / OFD152A / OFD153A / OFDI058 權限表 改壞會越權
```

*圖:圖 5 跨模組。橘框=本片的維護入口或表;白框=動作;灰虛框=別的模組的用法;黑框=Common 共用件或版控外;橘虛框=風險。A 是本片唯一會動到別的模組的地方,C 是最該追的一組——OFD127 與 OFD163 的值天天被讀,卻已經沒有畫面可以維護。*

本片 20 支畫面自己不呼叫任何別的模組,但**它維護的 23 張表有 13 張被別人讀,1 張會被本片寫回別的模組**。

### 8.1 唯一一條寫出去的線:`OFDM123A` → BMS

這是本片**唯一**會動到別的模組的表的地方。`OFDM123A_PO_AfterAUD` 在四眼覆核 / 刪除覆核後:

| 動作 | 目標表 | 屬於 | 錨點 |
|---|---|---|---|
| `INSERT` 一筆受益人異動記錄 | `BMS001ACHG` | BMS | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:123`、`:242` |
| `UPDATE` 風險屬性與 KYC 終止日 | `BMS001A` | BMS | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:245-254` |

**兩個入口做同一件事,只有一個是活的**:`OFDM122A`(自主聲明書)有一份一模一樣的程式,**整段被註解**(§4.2)。改 KYC 同步邏輯時要記得檢查 `OFDM122A_PO.cs:56-254` 那 199 行註解要不要一起改。

而且**回傳筆數檢查被註解**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:255-256`),`BMS001A` 沒更新到也會回報成功(附錄 E.2)。

### 8.2 讀進來:Common 共用 PO 與查詢 / 報表畫面

| 本片的表 | 被誰讀 | 怎麼讀 | 錨點 |
|---|---|---|---|
| `HIGHRISK_COUNTRY` | `BasicBMS_PO` | `LEFT JOIN V_TA_HIGHRISK_COUNTRY ON BMS001A.BF_NATIONALITY = …COUNTRY_CD`,取 `NVL(RISK_LEVEL,'L')` 當 `COUNTRY_RISK_LEVEL` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69`、`:75` |
| `OFD123A` | `BasicBMS_PO`、`Utility_PO`、`BMSM001`、`BMSM006` | 讀客戶風險屬性 | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs` |
| `OFD125A` | `ucTradeAgentData` / `ucTradeDeputyData`(共用控制項)、`BasicOFD_Ctl` / `BasicOFD_PO` | 董監事 / 實質受益人清單 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucTradeDeputyData.cs` |
| `OFD135A` | `BasicOFD_Ctl` / `BasicOFD_PO`、`OFDI011` | 交易指示代理人 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` |
| `OFD127` | `BasicOFD_Ctl` / `BasicOFD_Pxy` / `MSSQL/BasicOFD_PO` / `GetANNOUNCE_AMTDataSrc` | 公告金額下拉 | `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/GetANNOUNCE_AMTDataSrc.cs` |
| `OFD152A` `OFD153A` | `BasicOFD_PO`、`OFDI058` | 查詢權限判定 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI058_PO.cs` |
| `OFD114A` | `OFDI011`、`RSPB009`、EC 的 `IPJB622` / `OFDB602` | 停交檢查 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs` |
| `OFD115A` | `CLSM002`、`CODM006`、`OFDI907`、`OFDI011` | 列管檢查 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs` |
| `OFD124` | `BMSM001` / `BMSM006`(**全被註解**)、`OFD_PO`、`SerialNo_AGI` | 已停用 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:610` |

**最值得注意的兩張:`OFD127` 與 `OFD163`。** 它們的維護畫面(`OFDM127` / `OFDM163`)都在 §0.2 的死畫面名單裡,但表本身被 Common 與批次天天讀。**要改這兩張表的值,現在只能下 SQL。**

### 8.3 批次讀本片的表

| 批次 | 讀哪張 | 錨點 |
|---|---|---|
| `OFDB161`(定期買回計算) | `OFD163` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs` |
| `OFDB004`(一次建檔) | `OFD129A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs` |
| `OFDB331` | `OFD129A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB331_PO.cs` |

**`OFD162`(定期買回展開表)在 repo 內只有 `OFDM161_PO` 一個寫入者,沒有任何讀取者。** 依 `OFDM161` UI 那段被註解的檢核提到「定期買回計算作業(OFDB161)」,**推測 `OFDB161` 是在版控外或以另一種名稱讀它**;實際搜 `Dev/` 全樹,`OFD162` 只出現在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs` 與 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM161Model.xsd`。**標〔假設〕。**

### 8.4 改動影響面速查

| 要改什麼 | 一定要一起看 |
|---|---|
| `OFD123A` 的風險屬性欄(`EFFECT_CODE1/2`、`_LP` 版) | `OFDM123A_PO.cs:76-115`(轉碼邏輯)、`BMS001A.KYC_RISK_ATTR`、`BasicBMS_PO`、`BMSM006` |
| `HIGHRISK_COUNTRY` 的欄位 | view `V_TA_HIGHRISK_COUNTRY`(**不在版控**)、`BasicBMS_PO:69`、`OFD008`(`OFDM157` 的 inner join) |
| `OFD129A` 的任何欄位 | `OFDB004` / `OFDB331` / `NFDR022` / `Utility_PO` / `NfdUtility_PO`,以及 `OFDM129` 自己的 `Copy` |
| `OFD114A` 的 `FUND_ID`(尤其是 `'ALL FUNDS'` 這個魔法值) | `OFDI011` / `RSPB009` / EC 的 `IPJB622` / `OFDB602` |
| `OFD152A` / `OFD153A`(權限表) | `BasicOFD_PO`、`OFDI058`——**改壞會讓人看到不該看的基金** |
| `OFD127` / `OFD163` | **沒有可用的維護畫面**,只能下 SQL;下游是 `GetANNOUNCE_AMTDataSrc` 與 `OFDB161` |

## 附錄 A. 資料表總表

23 張實體表 + 2 張只在 vdb 存在的輔助表。「DDL 在版控」欄列 `DB/` 底下的腳本。

| 實體表 | vdb 名 | 中文名(來源) | 主要維護者 | DDL 在版控 | 四眼 |
|---|---|---|---|---|---|
| `OFD114A` | `OFDM114` | —(待選單表) | `OFDM114` | **無** | 齊 |
| `OFD115A` | `OFDM115` | —;`SHORE_ID` / `FH_CD` 欄由資料腳本反推 | `OFDM115A` | 只有資料腳本 `DB/Table/11706_InsertOFD115A_1.sql` 等 4 支 | 齊 |
| `OFD116A` | `OFDM115_Detail` | — | `OFDM115A` | 只有資料腳本 `DB/Table/11706_InsertOFD116A_1.sql` 等 4 支 | 齊 |
| `OFD122A` | `OFDM122A` | **自主聲明書資料檔** | `OFDM122A` | `DB/Table/Create_OFD122A.sql` + `DB/Table/Trigger_OFD122A_DATAFLAG.sql` + `DB/Table/Createsynonym_11091.sql` | 齊 |
| `OFD123A` | `OFDM123A` | — | `OFDM123A` | 只有 `DB/Table/Alter_OFD123A.sql`、`DB/Table/Alter_OFD123A_11458.sql`(**沒有建表腳本**) | 齊 |
| `OFD124` | `OFD124` | — | `OFDM123`(死) | **無** | **無** |
| `OFD124A` | `OFD124A` | — | `OFDM123A` | **無** | 齊 |
| `OFD125` | `OFD125` | — | `OFDM123`(死) | **無** | **無** |
| `OFD125A_M` | `OFDM125A_M_Master` | **董監事設定主檔資料** | `OFDM125A` | `DB/Table/create_OFD125A_M.sql` + `DB/Table/create_OFD125A_M_Trigger.sql` | 齊 |
| `OFD125A` | `OFDM125A_Detail` | **董監事設定明細資料** | `OFDM125A` | `DB/Table/create_OFD125A.sql`、`DB/Table/create_OFD125A_2.sql`、`DB/Table/create_OFD125A_Trigger.sql` | 齊 |
| `OFD126A` | `OFD126A` | — | `OFDM126` | **無** | 齊 |
| `OFD127` | `OFDM127` | — | `OFDM127`(死) | **無** | **無** |
| `OFD128` | `OFDM128` | — | `OFDM128`(死) | **無** | **無** |
| `OFD129A` | `OFDM129` | — | `OFDM129` | **無** | 齊 |
| `OFD133A` | `OFDM133` | — | `OFDM133` | **無** | 齊 |
| `OFD135A` | `OFDM135` | **交易指示代理人設定資料** | `OFDM135` | `DB/Table/createOFD135A.sql` | 齊 |
| `OFD151A` | `OFDM151` | — | `OFDM151` | **無** | 齊 |
| `OFD152A` | `OFDM151_EMP` | — | `OFDM151` | **無** | 齊 |
| `OFD153A` | `OFDM151_FUND` | — | `OFDM151` | **無** | 齊 |
| `OFD154` | `OFDM154` | — | `OFDM154`(死) | **無** | **無** |
| `OFD155` | `OFDM155` | — | `OFDM155`(死) | **無** | **無** |
| `OFD156A` | `OFD156A` | — | `OFDM156` | **無** | 齊 |
| `OFD157A` | `OFD157A` | — | `OFDM156` | **無** | 齊 |
| `HIGHRISK_COUNTRY` | `HIGHRISK_COUNTRY` | 高風險國別(由欄位 Caption 推測) | `OFDM157` | **無**(連 view `V_TA_HIGHRISK_COUNTRY` 也沒有) | 齊 |
| `OFD161` | `OFDM161` | — | `OFDM161`(死) | **無** | **無** |
| `OFD162` | `OFD162` | — | `OFDM161` 的 `After*` 手寫 SQL | **無** | **無** |
| `OFD163` | `OFDM163` | — | `OFDM163`(死) | **無** | **無** |
| `OFD164` | `OFDM164` | — | `OFDM164`(死) | **無** | **無** |

**只在 vdb 存在、沒有實體表的輔助 DataTable**:

| vdb 表 | 用途 | 錨點 |
|---|---|---|
| `OFDM081` | `OFDM129` 的基金資料暫存(`GetFUND_DATA` 回填) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM129Model.xsd`(PK `FUND_ID`)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM129_PO.cs:351` |
| `OFDM152` | **沒有任何畫面使用**,Model / View 都編了但六層只有兩層 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/OFDM152Model.xsd`,見 §3.1 的警告 |

**23 張實體表裡只有 5 張有建表腳本在版控(22%)**,而且全部集中在 A 塊(`OFD122A` `OFD123A` `OFD125A_M` `OFD125A` `OFD135A`)。B / C / D 三塊**一張都沒有**。改欄位時沒有任何地方可以對照,只能看 xsd(`architecture.md §5.5`)。

## 附錄 B. SP / Function / Trigger / View

| 類型 | 物件 | 屬於 | 錨點 |
|---|---|---|---|
| Trigger | `OFD125A_M_DATAFLAG` | `OFD125A_M`,`before update or insert`,把 `utl_raw.cast_to_raw(sys_guid())` 塞進 `dataflag` | `DB/Table/create_OFD125A_M_Trigger.sql` |
| Trigger | `OFD125A` 的 DATAFLAG trigger | `OFD125A` | `DB/Table/create_OFD125A_Trigger.sql` |
| Trigger | `OFD122A_DATAFLAG` | `OFD122A` | `DB/Table/Trigger_OFD122A_DATAFLAG.sql` |
| Synonym | `OFD125A_M` → `SW.OFD125A_M` | public synonym | `DB/Table/create_OFD125A_M.sql` |
| Synonym | `OFD122A` 相關 | public synonym | `DB/Table/Createsynonym_11091.sql` |
| View | `V_TA_HIGHRISK_COUNTRY` | 供 `BasicBMS_PO` 讀高風險國別 | **不在版控**,已列 meta `refcheck-ignore`;唯一出現處 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69`、`:75` |
| View | `OFD081V` | 基金主檔檢視,被 `OFDM129` / `OFDM155` / `OFDM156` / `OFDM154` 讀 | **不在版控**,已列 `refcheck-ignore` |

**本片 20 支畫面沒有呼叫任何 Stored Procedure 或 Function**——全部是 inline SQL。這與 `architecture.md §4.2` 說的「SQL 由 `TableHelper` 依 schema 生成 + 事件裡手寫」一致。

## 附錄 C. 代碼對照(狀態碼、型別碼)

本片沒有自己的狀態機(§2.6)。以下是程式裡真的出現過的值:

| 代碼 | 值 | 意義 | 來源 | 錨點 |
|---|---|---|---|---|
| `SHORE_ID` / `FUND_TYPE` | `'1'` 境外 · `'2'` 境內 | 基金資料來源 | `TA.MappingCode` 常數 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FUND_TYPE` 的第三個值 | `'0'` | `OFDM114` 的「所有基金」假列,**不在 `SHORE_ID` 值域** | 程式寫死 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:127` |
| `FUND_ID` 魔法值 | `'ALL FUNDS'` | `OFDM114` 的「所有基金」 | 程式寫死,**repo 內無常數定義** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:124` |
| `SOURCE_CD`(`OFDM123A`) | `'1'` 線上 · `'2'` 後台 · `'3'` 郵局 | 資料來源 | `CTL014` `SourceType='455'`〔客戶特定〕 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:39`、`:411`、`:419`、`:670` |
| `BF_COUNTRY_X` | `"01"` = 本人(非 `_LP`) | 受益人類別;決定取本人欄還是 `_LP` 欄 | 程式寫死比較 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:79`、`:99` |
| `EFFECT_CODE` → `KYC_RISK_ATTR` | `'01'`→`'1'` · `'02'`→`'2'` · 其餘→`'3'` | 風險屬性轉碼 | 程式寫死三元運算 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:85` |
| `STATUS`(資料腳本裡的字面值) | `'302'` | 四眼狀態 | `DB/Table/11706_InsertOFD115A_1.sql` 的 `insert … values(… ,'302', …)` | 同左 |
| `CTL014.SourceType` | `'007'` 基金狀態 · `'062'` 銷售機構區別碼 · `'063'` 受益人類別 · `'107'` 交易途徑 · `'404'` 風險屬性 · `'455'` 資料來源 | 六組下拉值域〔客戶特定〕 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:252-256`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:133` |  |
| `CNTL_TRADE_TYPE.OpenAccount` | 常數(值未在本片出現) | 列管交易別「開戶」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:125` |  |
| `RISK_LEVEL` 預設 | `'L'` | 查不到國別時的風險等級 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:69` |  |

> **`'302'` 與 `ofd7.md §2.6` 的 `'301'` 是同一套三位數狀態碼**,而 `architecture.md §3.10` 反推出來的值域是 `'0'`~`'6'` / `'8'` / `'9'` 單字元。**兩邊對不上,值域到底幾位數要查資料庫才能確定。標〔假設〕缺:DB 連線。**

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan --module OFD`**(那會拿 550 支來比)。以下是本片名單的 20 支逐一處置:

| # | 畫面 | 處置 | 章節 | PO 基底 | 在 csproj |
|---|---|---|---|---|---|
| 1 | `OFDM114` | 已寫 | §4.8 | `BaseEVADaoPO` | 六層齊 |
| 2 | `OFDM115A` | 已寫 | §4.1 | `BaseEVADaoPO` | 六層齊 |
| 3 | `OFDM122A` | 已寫 | §4.2 | `BaseEVADaoPO` | 六層齊 |
| 4 | `OFDM123` | 已寫(深) | §4.3、§4.5 | **`BasicEVAPO`** | 六層齊 |
| 5 | `OFDM123A` | 已寫(深) | §4.4、§4.5 | `BaseEVADaoPO` | 六層齊 |
| 6 | `OFDM125A` | 已寫(深) | §4.6 | `BaseEVADaoPO`(第 28 行留著 `//… : BasicEVAPO`) | 六層齊 |
| 7 | `OFDM126` | 已寫 | §4.20.1 | `BaseEVADaoPO` | 六層齊 |
| 8 | `OFDM127` | 已寫 | §4.9 | **`BasicEVAPO`** | 六層齊 |
| 9 | `OFDM128` | **表格帶過** | §4.10 | **`BasicEVAPO`** | 六層齊 |
| 10 | `OFDM129` | 已寫 | §4.11 | `BaseEVADaoPO` | 六層齊 |
| 11 | `OFDM133` | 已寫 | §4.12 | `BaseMultiRowEVADaoPO` | 六層齊 |
| 12 | `OFDM135` | 已寫 | §4.13 | `BaseMultiRowEVADaoPO` | 六層齊 |
| 13 | `OFDM151` | 已寫(深) | §4.20.2 | `BaseEVADaoPO` | 六層齊 |
| 14 | `OFDM154` | 已寫 | §4.14 | **`BasicEVAPO`** | 六層齊 |
| 15 | `OFDM155` | 已寫 | §4.15 | **`MultiRowEVAPO`** | 六層齊 |
| 16 | `OFDM156` | 已寫 | §4.16 | `BaseEVADaoPO` | 六層齊 |
| 17 | `OFDM157` | 已寫(深) | §4.7 | `BaseEVADaoPO` | 六層齊 |
| 18 | `OFDM161` | 已寫(深) | §4.18 | **`BasicEVAPO`** | 六層齊 |
| 19 | `OFDM163` | 已寫 | §4.19 | **`BasicEVAPO`** | 六層齊 |
| 20 | `OFDM164` | 已寫(深) | §4.17 | **`BasicEVAPO`** | 六層齊 |

**統計**:19 支逐節寫、1 支表格帶過;**8 支繼承 `BasicEVAPO` / `MultiRowEVAPO`**(標粗);**0 支缺 csproj**。

**四個子對話框**(不另列節,併在主畫面裡):

| 子對話框 | 屬於 | 行數 | 在 csproj |
|---|---|---|---|
| `OFDM123p0` | `OFDM123` | 1,023 | 是 |
| `OFDM123Ap0` | `OFDM123A` | 137 | 是 |
| `OFDM125Ap0` | `OFDM125A` | 131 | 是 |
| `OFDM129p0` | `OFDM129` | 162 | 是 |

**名單外、但在同一個 Entity 資料夾裡的殘骸**:

| 項目 | 狀態 | 錨點 |
|---|---|---|
| `OFDM152Model.xsd` / `OFDM152ModelVDB.cs` / `OFDM152View.xsd` | **編了,但沒有 UI / PO / Ctl / Pxy**;PK 與 `OFDM154Model.xsd` 一字不差 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD6/DataEntity.OFD6.csproj:178-183`、`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD6/UIEntity.OFD6.csproj:173` |

## 附錄 E. 讀本文時要注意的地方

依嚴重度排序。「嚴重度」= 對現場資料正確性的影響 × 被踩到的機率。

### E.1 【高】八支畫面繼承 `BasicEVAPO` / `MultiRowEVAPO`,連查詢都 NRE

| 項目 | 內容 |
|---|---|
| **缺陷** | `dbTA` 宣告即 `null`、建構子建立連線整段被註解,子類沒有一支自己賦值;8 支的 `BeforeSelect` 第一行就用 `dbTA` 組 `DbCommand` |
| **影響** | `OFDM123` `OFDM127` `OFDM128` `OFDM154` `OFDM155` `OFDM161` `OFDM163` `OFDM164` 整支不可用。其中 `OFD127` 與 `OFD163` 的值仍被 Common 與批次讀取,**只能下 SQL 維護** |
| **錨點** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`:164-172`、`:187`;各支見 §0.2 表 |
| **嚴重度** | **高**(但「早就沒在用」的可能性也高——T-SQL 痕跡 + Model 缺四眼欄兩條旁證都指向同一結論) |

### E.2 【高】`OFDM123A` 覆核後寫回受益人主檔,回傳筆數檢查被註解

| 項目 | 內容 |
|---|---|
| **缺陷** | `dbProduct.ExecuteNonQuery(cmdUpdate, args.DbTran);` 後面緊跟著兩行註解 `//if (… != 1) //throw new ApplicationException("受益人風險屬性及KYC終止日更新失敗");` |
| **影響** | `UPDATE BMS001A` 更新 0 筆(例如 `BF_NO` 對不到)時,四眼仍回報成功。**KYC 風險屬性沒寫進受益人主檔,現場不會有任何徵兆** |
| **錨點** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:254-256` |
| **嚴重度** | **高** |

### E.3 【高】`OFDM164` 伺服端檢核出錯時不擋存檔

| 項目 | 內容 |
|---|---|
| **缺陷** | `if (i == -1) { ShowMessage(…ServerSideError); return; }` —— 有訊息、有 `return`,**但沒有 `e.Cancel = true`** |
| **影響** | 區間重疊檢核一丟例外,使用者按掉錯誤訊息,重疊的買回率照樣存進去 |
| **錨點** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM164.cs:95-99`(修改)、`:133-137`(新增) |
| **嚴重度** | **高** |

### E.4 【高】`OFDM161` 的「已執行過就不能改」檢核整段被 `/* */` 註解

| 項目 | 內容 |
|---|---|
| **缺陷** | `BeforeModifyButtonClicked` 與 `BeforeDeleteButtonClicked` 裡,「該基金已有定期買回計算作業執行記錄,是否繼續執行?」整段被註解;連帶 PO 的 `ChkOFD166` 成為無呼叫者的死碼 |
| **影響** | 已經跑過定期買回的基金,排程可以被無聲改掉或刪掉 |
| **錨點** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM161.cs:111-132`、`:141-162`;死碼在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:551` |
| **嚴重度** | **高**(該畫面本身也是死的,所以實際觸發機率低) |

### E.5 【高】`OFDM157` 的 `HIGHRISK_COUNTRY` 用 `INNER JOIN`,國別檔沒有就整筆消失

| 項目 | 內容 |
|---|---|
| **缺陷** | `FROM HIGHRISK_COUNTRY JOIN OFD008 ON …COUNTRY_CD = …COUNTRY_CD`,不是 `LEFT JOIN`;`OFDM126` 原版沒有這個 join |
| **影響** | `OFD008` 沒有的國碼在 `OFDM157` 查不到、改不到、刪不掉,**且無提示**。高風險國別是法遵資料,漏一個國家會出事 |
| **錨點** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:99-102` |
| **嚴重度** | **高** |

### E.6 【中】三支畫面用 `INNER JOIN` 接外部主檔(同型)

| 畫面 | join | 影響 | 錨點 |
|---|---|---|---|
| `OFDM123` | `INNER JOIN [BMS001]` | 只填 ID 沒填戶號的 KYC 答卷(畫面明文允許)查不出來 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:251` |
| `OFDM135` | `JOIN BMS001A` | 無受益人主檔的代理人設定整筆消失 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:80` |
| `OFDM157` | `JOIN OFD008` | 見 E.5 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:101` |

**嚴重度中**。對照組:本片其他 17 支對外部主檔一律 `LEFT JOIN` 或 `RIGHT OUTER JOIN`。

### E.7 【中】Oracle 三值邏輯:`欄 <> '值'` 遇 NULL

| 位置 | 條件 | 影響 | 錨點 |
|---|---|---|---|
| `OFDM115A` 重複列管檢核 | `AND DATA_SEQ <> " + row.DATA_SEQ` | `DATA_SEQ` 若為 NULL,該列不算進重複檢查 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:138` |
| `OFDM164` 區間重疊檢核 | `AND (BNG_DATE <>@BNG OR BNG_DATE ='1900/01/01')` | `BNG_DATE` 若為 NULL,兩邊都是 UNKNOWN,該列不算進重疊檢查 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM164_PO.cs:180` |

兩張表都**沒有建表腳本在版控**(附錄 A),欄位可不可空**標〔假設〕缺:DB 連線**。這是前十五篇裡**第九個**中這一型的模組。

### E.8 【中】`OFDM122A` 的 `AfterApprove` 是 199 行的空方法

| 項目 | 內容 |
|---|---|
| **缺陷** | 事件有掛(`:35-36`),方法本體 `:56-254` 整段註解。被註解的內容是從 `OFDM123A` 複製來的(註解裡還留著 `FROM OFD123A`) |
| **影響** | 自主聲明書覆核後**不會**同步回 `BMS001A`,投資屬性調查表**會**。同一塊業務兩個入口行為不一致 |
| **錨點** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM122A_PO.cs:35-36`、`:56-254`、`:93` |
| **嚴重度** | **中**(可能是刻意停用,但沒有任何註解說明) |

### E.9 【中】成對畫面只改一邊(本片三組)

| 組 | 相似度 | 差在哪 | 錨點 |
|---|---|---|---|
| `OFDM126` / `OFDM157` | PO 0.779 · Ctl 0.858 · UI 0.685 | `OFDM157` 多了一個 `INNER JOIN OFD008`(E.5),而註解沒改(還寫「取得行銷說明 流水號最大值」) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:73`、`:101` |
| `OFDM125A` / `OFDM135` | UI 標籤與三句檢核訊息一字不差 | 日期查詢的防呆:`OFDM135` 檢查起迄兩邊(`:97`),`OFDM125A` 只檢查起日(`:155`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:97` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:155` |
| `OFDM122A` / `OFDM123A` | `DoValidate` 的六句檢核一字不差 | `OFDM122A` 那份整段被註解 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM122A.cs:479-525` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM123A.cs:474-531` |

另有**同檔內複製**:`OFDM161` 的 `AfterAdd`(`:122-289`)與 `AfterUpdate`(`:291-459`)是 168 行 × 2;`OFDM164` 的 `BeforeAdd` 與 `BeforeModify` 只差一個 `"A"` / `"M"`。

### E.10 【中】字串串接進 SQL(全片 8 處以上)

| 位置 | 串什麼 | 錨點 |
|---|---|---|
| `OFDM115A` `BeforeAddUpdate` | `CUS_NAME`(客戶姓名)、`ID_NO`、五個日期 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM115A_PO.cs:126-138` |
| `OFDM123A` 寫回 BMS | `WHERE BF_NO = '" + row.BF_NO + "'`(同段的 `SET` 卻用具名參數) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:248` |
| `OFDM123` 刪除前檢核 | `string.Format(strSQL, strKYC_ANS_NO, …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:602` |
| `OFDM125A` / `OFDM135` 日期子查詢 | 起迄日 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:157`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM135_PO.cs:99` |
| `OFDM126` / `OFDM157` `BeforeAdd` | `ST_CD` / `COUNTRY_CD` 走 `string.Format` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM126_PO.cs:76-79`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:76-79` |
| `OFDM151` 明細 SQL | `QUERY_GRPCD` 串三次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:221`、`:232`、`:248`、`:256` |
| `OFDM154` 查詢條件 | 三個參數全串 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM154_PO.cs:100`、`:114`、`:128` |

**嚴重度中**:多數是內碼型欄位,但 `CUS_NAME`(中文姓名)是使用者自由輸入。

### E.11 【中】`DATA_SEQ` 流水號 `MAX + 1`,三支畫面都沒有鎖

`OFDM115A`(`:105-117`)、`OFDM126`(`:69-86`)、`OFDM157`(`:69-86`)。併發新增同一個鍵值會拿到同一個號,撞 PK。**嚴重度中**(這三支是活畫面,真的會被用到)。

### E.12 【中】`OFDM114` 的 `'ALL FUNDS'` 是無定義的魔法字串

`FROM DUAL` 造出來的假列,`FUND_ID` 寫死 `'ALL FUNDS'`(含空白)、`FUND_TYPE` 寫死 `'0'`(不在 `SHORE_ID` 值域)。四個下游模組要自己知道這個值。**repo 內沒有任何常數定義它。** 錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM114_PO.cs:124-129`。

### E.13 【中】`OFDM157` / `OFDM126` 沒有期間重疊檢核,下游 join 不帶日期

`HIGHRISK_COUNTRY` 與 `OFD126A` 都靠 `DATA_SEQ` 讓同一個鍵有多列,但**沒有任何檢核擋期間重疊**;`BasicBMS_PO` 的 `LEFT JOIN V_TA_HIGHRISK_COUNTRY` 也**只用 `COUNTRY_CD` 對,不帶日期**(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs:75`)。**同一個國別有兩列有效資料時,`BMS001A` 的查詢結果筆數會被放大。**

### E.14 【中】`OFDM161` 的 `DataTable.Select` 條件字串少一個空白

`"FUND_ID =" + row.FUND_ID + "AND PERIOD_EXE_DATE =#…#"` —— `FUND_ID` 與 `AND` 之間沒有空白,拼出來是 `FUND_ID =F001AND …`。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM161_PO.cs:201`、`:363`(兩段複製各一次)。

### E.15 【中】`OFDM163` 三處欄位名不一致 + `Split(':')` 沒防呆

`App.config:819` 說 pkey 是 `LOCK_GAIN_PROCESS_TIME`、UI 控制項叫 `txtLOCK_GAIN_PROCESS_TIME`、實際寫入的是 `PERIOD_REDEM_PROCESS_TIME`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM163.cs:54`),而 xsd 完全沒宣告 PK。另外 `Split(':')` 後直接取 `[0]` `[1]`,輸入不含冒號就 `IndexOutOfRangeException`(`:53-54`)。

### E.16 【低】`OFDM151` 的 `AppendToDoString` 是死碼;`OFDM154` 有兩個沒接上的事件處理器

`OFDM151`:`BuildMasterSQLString(model, false)` 兩處都傳 `false`,`BeforeGetToDoData` 沒訂閱(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:35-36`、`:64`、`:78`、`:192-195`)。 `OFDM154`:`OFDM154_PO_BeforeGetMaintainData`(`:40-49`)與 `OFDM154_PO_BeforeGetToDoData`(`:51-60`)兩個 private 方法沒有任何呼叫者(`:18` 只訂閱 `BeforeSelect`)。

### E.17 【低】`OFDM151` 的明細 SQL 在沒帶參數時回空字串

`BuildDetailSQLString` 兩個 `if` 都不成立時 `return string.Empty`,呼叫端照樣 `dbProduct.GetSqlStringCommand("")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM151_PO.cs:86`、`:209-265`)。同一支還把明細表名寫成硬字串 `"OFD152A"` / `"OFD153A"` 而不是 `this.DetailTable[i].dbTableName`(`:214`、`:240`)。

### E.18 【低】`OFDM123` 七處 `throw new ApplicationException("")` 訊息是空字串

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123_PO.cs:626`、`:632`、`:638`、`:645`、`:651`、`:657`、`:663`。使用者只會看到一個沒有內容的錯誤框。

### E.19 【低】`OFDM127` 同一支 PO 用兩套連線欄位

`Update` / `Select` 用 `dbTA` / `dbPTPF`,`Add` / `Delete` 用 `db` / `db_ToDo`(繼承自 `Basic_PO`,無原始碼)。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM127_PO.cs:317`、`:413`、`:514`、`:568`。

### E.20 【低】混世代 helper:四支活畫面同時用 `xEVAStringHelper` 與 `EVAStringHelper`

`OFDM133`(`:59` vs `:69-70`)、`OFDM135`(`:74` vs `:83`)、`OFDM126`(`:104`)、`OFDM157`(`:104`)。新世代 `BaseEVADaoPO` 底下卻呼叫舊世代的 `EVAStringHelper`,與 `ofd7.md §4.0` 記的純 `xEVAStringHelper` 寫法不同。

### E.21 【低】`OFDM157` 的 `SELECT` 讓 `COUNTRY_NAME` 出現兩次

`SELECT HIGHRISK_COUNTRY.* ,OFD008.COUNTRY_NAME` —— `HIGHRISK_COUNTRY` 自己就有 `COUNTRY_NAME`。同名欄重複,綁到哪一個由 provider 決定(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM157_PO.cs:100`)。

### E.22 【低】`OFDM155` 主檔清單的「轉入基金」永遠是空的

`'' AS SWITCH_FUND_ID` / `'' AS SWITCH_FUND_SHNM` 硬填空字串,對應的 join 被註解(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM155_PO.cs:86`、`:88`、`:94-95`)。

### E.23 【低】`OFDM156` 的錯誤全綁在同一個無關控制項上

「至少必須輸入一筆金額」與「明細資料必須輸入！！」都 `AddError(unumALLOT_SILL_TAMT_C, …)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM156.cs:212`、`:218`)。使用者看到的紅框指向錯的欄位。

### E.24 【低】檔案存在但沒有畫面:`OFDM152` 那一組 Entity

Model / View 都在 csproj 裡被編譯,但 `UI.OFD` / `PO.OFD` / `Control.OFD` / `FormProxy.OFD` 四個專案沒有任何 `OFDM152` 檔。PK 與 `OFDM154Model.xsd` 一字不差。見 §3.1。**這是本片版本的「檔案存在但不在 csproj」——反過來:在 csproj 但沒有畫面。**

### E.25 【低】`DB/` 腳本編碼混用,同一個變更單裡兩種編碼

| 編碼 | 檔案 |
|---|---|
| `cp950` | `DB/Table/create_OFD125A_M.sql`、`DB/Table/create_OFD125A.sql`、`DB/Table/create_OFD125A_2.sql`、`DB/Table/Create_OFD122A.sql`、`DB/Table/createOFD135A.sql`、`DB/Table/Alter_OFD123A.sql`、`DB/Table/Alter_OFD123A_11458.sql`、`DB/Table/11706_InsertOFD115A_1.sql`(共 4 支) |
| `utf-8-sig` | `DB/Table/create_OFD125A_M_Trigger.sql`、`DB/Table/create_OFD125A_Trigger.sql`、`DB/Table/Trigger_OFD122A_DATAFLAG.sql`、`DB/Table/Createsynonym_11091.sql`、`DB/Table/11706_InsertOFD116A_1.sql`(共 4 支) |

**最刺眼的是 `11706_` 這一組:同一張變更單裡,`InsertOFD115A_*` 四支是 cp950,`InsertOFD116A_*` 四支是 utf-8-sig。** 主檔與明細的腳本編碼不同。 **`Dev/` 底下 20 支畫面的 120 個六層檔案全部是 UTF-8,沒有一支例外**——問題只在 `DB/`。

### E.26 【低】`OFD123A` 的 `_LP` 後綴意義靠推測

30 組 `XXX` / `XXX_LP` 成對欄位,Caption 全空白,repo 內沒有常數或註解說明 `LP` 是什麼。從 `utxtBF_NO` / `utxtBF_NO_LP` 成對控制項與 `BF_COUNTRY_X == "01"` 的分支(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM123A_PO.cs:79-84`)推測是**聯名戶第二位受益人**。**標〔假設〕。**

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD6` 的 20 支 M 畫面;查證 `OFDM123` / `OFDM123A` 非境內外配對、`OFD125A_M` 為實體表、`HIGHRISK_COUNTRY` 為共用參數表三題;逐支標記 PO 基底與 csproj 狀態 |

由 build_doc.py v2.0.0 於 2026-09-15 13:05 產生 · 標題 90 · 圖 5 · 表格 78 · 程式錨點 440 · § 連結 89 · 引用檢查：畫面 23（缺 0） · Table 30（缺 0） · 結果集 7（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofd7.md
============================================================

# ATLAS OFD7 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先翻 §1 的圖抓全貌,再讀 §2 把「一張表同時當主檔與明細」以及 `_UPD` 配對表搞清楚(這兩件事是本片最容易誤解的地方),之後 §3 的清冊配 §4 起的畫面章節就讀得動了。**急著找 `_UPD` 是什麼的人直接跳 §4.10**。

> ⚠ **OFD7 不是一個業務模組,是一份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/` 這個 Entity 專案底下的 **15 支 M 畫面**。切片的依據是 Entity 專案資料夾,不是業務;所以本片內部含**五條互不相干的業務線**(§0.1)。名稱 `OFD7` 為**推測**,取自資料夾名。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs` 的常數字典**推測**,待選單表回填。

> ⚠ **〔客戶特定〕**:基金公司代碼 `'Atlas'`、境內外代碼 `'1'`/`'2'`、四眼狀態字面量 `'301'`、EC 旗標 `etraflg='Y'` 為本站台的值。

> ⚠ **〔共用〕**:`OFD206` `OFD204` `OFD197A` `OFD195A` `OFD193A` `OFD194A` `OFD196A` `OFD213A` `OFD214A` `OFD215A` `OFD201A` `OFD202A` `OFD203A` `OFD687A` 同時服務 BMS / COD / EC / OFDB / OFD.Query(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 15 支畫面管什麼(推測)

先給結論:**本片沒有單一業務主題,是「基金申購手續費率與 EC 促銷優惠」這個大主題底下的五塊設定檔維護**。

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 牌告費率階梯** | `OFDM191` `OFDM192` `OFDM193` | 一檔基金的申購手續費率,依「金額級距」或「年度級距」分段設定,不分對象 | 欄位 `ALLOT_FEE_RATE` Caption 為「申購手續費率(%)」、`BNG_AMT`/`END_AMT` 為「申購起始/終止金額」 |
| **B 對象別優惠費率** | `OFDM194` `OFDM194B` `OFDM196` `OFDM198` | 在牌告之外,針對「某位受益人」「某身分別 × 某銷售機構」「某優惠專案」另外給一組費率 | 主鍵比 A 多掛 `BF_NO` / `REL_TYPE`+`AGENT_ID` / `DISC_CODE` |
| **C 優惠資格名單** | `OFDM195` `OFDM197` | 誰算「優惠關係人」(員工 / 推薦人)、誰屬於哪個「行銷身分別」;**只存資格,不存費率** | `OFD195A` 全表無費率欄;`OFD197A` 只有 `MKT_ID`+`BF_NO`+`BELONG_DATE` |
| **D EC 促銷活動** | `OFDM199` `OFDM204` `OFDM206` | 一檔促銷活動的內容(適用基金、費率、通路、身分群組、銷售機構)、可用次數上限,以及每位受益人的已用次數 | `CAMPAIGN_CODE` Caption 為「促銷活動代碼」;`OFD206` 有 `USED_ALLOT_TIMES` |
| **E 匯費與簡碼** | `OFDM213` `OFDM214` `OFDM215` | 哪些銀行免收匯費、某受益人某基金的匯費收取碼、基金簡碼 | 欄位 Caption「不收匯費銀行代碼」「贖回匯費收取碼」`SHORT_CODE` |

五塊之間**沒有任何程式呼叫**,只有一條真依賴:C 的 `OFD197A` 是 D 的活動對象判定輸入(見 §8.3)。讀 OFD7 的人如果預期整片是一條流程,會在 §4.6 之後完全對不上——先知道這件事比較省時間。

### 0.2 不管什麼

| 不在 OFD7 | 在哪 | 依據 |
|---|---|---|
| **把 `_UPD` 暫存的促銷活動費率搬進正式表** | **repo 內查不到執行者**,推測在版控外(SP / 排程 / Trigger) | 全庫對 `OFD199A_UPD` 的引用只有一處:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40`。詳見 §4.10 |
| 基金主檔建檔 | `OFDM081A`(境內 `OFD081A`)/ `OFDM081B`(境外 `OFD081`) | `architecture.md 附錄 A` 的「主檔於」欄 |
| 一次把六張費率 / 設定表跟基金一起建起來 | 批次 `OFDB004` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:64-71` |
| 促銷活動的**查詢** | `OFDI199`(OFD.Query 專案),讀的是正式表不是 `_UPD` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46` |
| 受益人開戶時順便掛 EC 優惠 | `BMSM001`(把 `OFD206` 當明細) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:158` |
| 員工離職時終止優惠關係人 | 原本設計在 `CODM009`,**整段被註解** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:81-248`,與 `cod.md §4` 記的一致 |
| 費率真正被套用到交易 | 版控外的計價流程 | repo 內只有 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4497-4541` 這類「查得到哪些活動」的 SQL,沒有算費率的程式 |

### 0.3 使用角色

15 支全部是 M 維護畫面,全部走標準四眼(輸入 / 驗證 / 覆核),角色由平台的 ToDo 機制指派,OFD7 自己不定義角色——所有 PO 都只是把 `xTableHelper.AppendToDoString(...)` 接到查詢字串尾巴(例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:101-102`)。詳見 `architecture.md §3`。

**三個例外**,實際上完全不經四眼:

| 入口 | 做什麼 | 錨點 |
|---|---|---|
| `OFDM197` 的匯入小畫面 | 讀 CSV 戶號清單,直接 `delete` + `insert`,狀態寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247` |
| `OFDM206` 的戶號清單匯入 | `insert ... select`,狀態寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206` 的 EC 整批匯入 | 同上,條件寫死 `etraflg='Y'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

這三段把 `ENTRYID` / `VERIFYID` / `APPROVEID` 一次填成同一個使用者、同一個 `SYSDATE`。**四眼的軌跡在,但沒有第二個人看過**。

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(讀) | `OFD081` / `OFD081A`(基金)、`OFD062`(基金公司)、`BMS001A`(受益人)、`OFD068A`(銷售機構)、`OFD072A`(推薦人)、`COD009`(員工)、`OFD601`(EC 網路戶)、`OFD027A`(行銷身分別)、`FSK003`(幣別)、`OFD094A` / `OFD020V`(保管銀行) | 全部是 `LEFT JOIN`,只取說明欄 |
| 下游(本片的表被誰讀 / 寫) | `OFDB004`(六張表當明細一起建)、`BMSM001`(`OFD206` 當明細)、`OFDI199` 與 EC 側(讀正式的促銷活動表)、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs`(判活動對象) | 見 §8 |
| 平行(同一張表兩個維護入口) | `OFD195A` 的第二個入口 `CODM009` **已被註解**;`OFD199A` 的第二個 PO 在 EC 專案 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34-44` |

### 0.5 全域開關

本片沒有 `App.config` 層級的業務開關。真正決定行為的三個「開關」都是資料欄位:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `FUND_TYPE`(基金資料來源) | `'1'` 境外 · `'2'` 境內 | 決定 `OFDM193` / `OFDM196` 開放幾檔費率欄、以及**哪些檢核會被跳過**(附錄 E.1) | 值域出處 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FEE_TYPE`(費率種類) | `'1'` 永久 · `'2'` 某期間 | `'1'` 時起迄日被清空 / 填 `00000000`~`99999999`,`'2'` 才用畫面上的日期 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:187-197`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-108` |
| `CAMPAIGN_TYPE`(活動類型) | `0` 開戶優惠 · 其餘 | `0` 時 `OFDM206` 限制「每位受益人只能一筆」;BMS 端刪舊資料也只刪 `0` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-76`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1859` |

`FUND_TYPE` 的 `'1'`=境外 / `'2'`=境內 這件事**在本片的註解裡是錯的**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-66` 把 `== "1"` 註解成「境內境金」,同一個檔的 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-95` 又把 `== "1"` 註解成「境外基金」。以 `SHORE_ID.OnShore = "2"`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:294-296`)與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:141-144`(「基金資料來源 預設境內基金」後面接 `uoptFUND_TYPE.Value = "2"` 與 `SOURCE_CD = SHORE_ID.OnShore`)為準:**`'1'` 是境外,`'2'` 是境內**。這個註解錯誤直接造成附錄 E.1 的缺陷。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD7 全景：牌告費率、對象別費率、資格名單、EC 促銷活動、匯費與簡碼五條線與下游
圖中文字:① 牌告費率階梯：以基金為鍵，不分對象 / OFDM191 / OFD191 幣別x金額階梯 / OFDM192 / OFD192 年度階梯 / OFDM193 / OFD193A 境內外6檔費率 / OFD081 OFD081A / 境外 / 境內基金主檔 / ② 對象別優惠費率：牌告之外的例外，鍵上多掛一個對象 / OFDM194 / OFD194A 受益人x境內 / OFDM194B / OFD194 受益人x境外 / OFDM196 / OFD196A 身分別x機構 / OFDM198 / OFD198 優惠專案 / ③ 優惠資格名單：只管「誰有資格」，不存費率 / OFDM195 / OFD195A 員工/推薦人 / OFDM197 / OFD197A 行銷身分別歸屬 / CODM009 CODM010 / 寫回段落全被註解 / BasicOFD_PO / 活動對象判定吃 OFD197A / ④ EC 促銷活動：唯一有暫存表的一塊 / OFDM199 / OFD199A_UPD 主檔+6明細 / OFDM204 / OFD204/OFD205 次數設定 / OFDM206 / OFD206 個人可用次數 / OFDI199 / EC 側 / 讀正式表 OFD199A / ⑤ 匯費與簡碼：三支同型，複製功能長得一樣 / OFDM213 / OFD213A 免匯費銀行 / OFDM214 / OFD214A 匯費收取碼 / OFDM215 / OFD215A 基金簡碼 / OFDB004 / 一次建檔批次也寫這些表 / ⑥ 下游：費率與活動最後都由版控外的計價流程取用 / OFDB004〔OFDB〕 / 6 張表當明細一起建 / BMSM001〔BMS〕 / OFD206 當明細 / EC / OFD.Query / 讀 OFD201A~OFD687A / 計價與交易流程 / repo 內查不到執行者
```

*圖:圖 1 OFD7 全景。橘框=本片的維護入口;灰虛框=別的模組或別支畫面用同一張表;黑框=無原始碼或版控外。五條線彼此沒有程式呼叫，全靠表相連——③ 的 OFD197A 決定 ④ 的活動對象成不成立，是唯一一條跨線的真依賴。*

### 1.2 資料表關係

圖放在 §2 的開頭(`ofd7.figs.py` 的 `h2:2-`)。重點看 C 區:**七張明細裡只有三張有 `_UPD` 分身**。

### 1.3 主要維護畫面的四眼與卡控順序

圖放在 §4 的開頭(`h2:4-` 第二張)。一句話總結:**卡控幾乎全在 UI 的 `DoValidate()`,伺服端只有 `OFDM206` 掛了一道 `BeforeAdd`,而三個批次匯入入口連那一道都繞過。**

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。唯一算得上批次的是 `OFDM197` 與 `OFDM206` 掛在 M 畫面上的三個 CSV 匯入小視窗,它們不是 B 型畫面,是 M 畫面的 `DoExp1` / `DoExp2` 按鈕開出來的對話框(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:180-193`)。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——15 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM199` 的 `_UPD` → 正式表生效(§4.10),但**生效的觸發時機在 repo 內查不到**,無法畫泳道。

## 2. 資料模型

```text
[圖] OFD7 二十三張表的分組、主鍵組成，以及 _UPD 暫存表與正式表的配對
圖中文字:A 多筆型：一支畫面一張表，主從都在同一張表上分群 / OFD191 / PK 基金+幣別+起迄+起額 / OFD192 / PK 基金+年度起 / OFD193A / PK +費率種類 / OFD196A / PK +身分別+機構 / OFD194A / PK +戶號+費率種類 / OFD194 / PK +戶號 無費率種類 / OFD198 / PK 專案+基金+戶號 / OFD213A OFD214A OFD215A / PK 基金 或 戶號x基金 / B 單筆型：OFD195A 與 OFD197A 各自獨立，沒有明細 / OFD195A / PK 身分別+代碼+機構+身分證 / OFD197A / PK 行銷身分別+統編 / OFDM197B / 匯入用 DataTable 僅 1 欄 / C 促銷活動：唯一的主明細結構，而且分成 _UPD 與 正式 兩套 / OFD199A_UPD / 主檔 PK 活動代碼 / OFD200A_UPD / 單筆費率明細 / OFD190A_UPD / 定期定額明細 / 三張只有 OFDM199 碰 / 全庫零其他引用 / OFD201A 通路 / 無 _UPD 分身 / OFD202A 身分群組 / 無 _UPD 分身 / OFD203A 銷售機構 / 無 _UPD 分身 / OFD687A 組合基金 / 欄名 COMPAIGN_CODE / D 次數控管：OFD204 設上限，OFD206 記個人，OFD207 記使用明細 / OFD204 / PK 活動代碼 / OFD205 / PK 基金+活動 / OFD206〔共用〕 / PK EC流水號+活動 / OFD207 / 使用記錄 無四眼欄位 / 外部唯讀：join 進來取說明，本片從不寫入 / OFD081 / OFD081A / 基金主檔 境外/境內 / OFD062 / 基金公司 / BMS001A / 受益人 / OFD068A OFD072A / 機構 / 推薦人 / OFD601 OFD027A / EC戶 / 行銷身分別
```

*圖:圖 2 資料模型。橘框=主檔或維護入口;白框=明細;灰虛框=共用;黑框=外部唯讀;橘虛框=陷阱。C 區是本片唯一的主明細結構，而且只有前三張有 _UPD 分身——後四張（OFD201A OFD202A OFD203A OFD687A）由維護畫面直接寫正式表。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

15 支畫面共宣告 **23 張實體表**。宣告方式分兩派,差別很大:

| 派別 | PO 基底 | 特徵 | 本片畫面 |
|---|---|---|---|
| **多筆型** | `BaseMultiRowEVADaoPO` | `MasterTable` 是 `List`,**沒有明細概念**;主從其實是同一張表,靠 `MasterPKey` 分群,畫面上半是「群」下半是「群內各列」 | `OFDM191` `OFDM192` `OFDM193` `OFDM194` `OFDM194B` `OFDM196` `OFDM198` `OFDM213` `OFDM214` `OFDM215` |
| **單筆型** | `BaseEVADaoPO` | `MasterTable` 單一 + `DetailTable` 清單 | `OFDM195` `OFDM197` `OFDM199` `OFDM204` `OFDM206` |

兩派的差別見 `architecture.md §3.9`。**多筆型沒有明細表這件事很容易看錯**——`atlas_scan.py --screen OFDM191` 報「明細 —」不是漏掉,是真的沒有。

逐支的宣告:

| 畫面 | 基底 | 主檔(實體表 → vdb 名) | 明細 | `MasterPKey` / `DetailTable` | 錨點 |
|---|---|---|---|---|---|
| `OFDM191` | 多筆 | `OFD191` → `OFDM191` | — | `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE`;`RemovePK` = `END_AMT` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:40-48` |
| `OFDM192` | 多筆 | `OFD192` → `OFDM192` | — | `FUND_ID`;`RemovePK` = `END_YEAR` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:40-45` |
| `OFDM193` | 多筆 | `OFD193A` → `OFDM193` | — | `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:34-43` |
| `OFDM194` | 多筆 | `OFD194A` → `OFDM194` | — | `FUND_ID` `CRNCY_CD` `BF_NO` `FEE_TYPE` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:38-48` |
| `OFDM194B` | 多筆 | `OFD194` → `OFDM194B` | — | `FUND_ID` `CRNCY_CD` `BF_NO` `BNG_DATE` `END_DATE`(**無 `FEE_TYPE`**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:42-51` |
| `OFDM195` | 單筆 | `OFD195A` → `OFDM195` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:41` |
| `OFDM196` | 多筆 | `OFD196A` → `OFDM196` | — | `FEE_TYPE` `REL_TYPE` `AGENT_CODE` `AGENT_ID` `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:24-36` |
| `OFDM197` | 單筆 | `OFD197A` → `OFDM197` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:44` |
| `OFDM198` | 多筆 | `OFD198` → `OFDM198` | — | `DISC_CODE` `BF_NO` `FUND_ID` `BNG_DATE` `END_DATE`(**無 `FEE_TYPE`**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:42-51` |
| `OFDM199` | 單筆 | `OFD199A_UPD` → `OFDM199` | `OFD200A_UPD` `OFD201A` `OFD202A` `OFD190A_UPD` `OFD203A` `OFD687A` | 六個 `DetailTable` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-48` |
| `OFDM204` | 單筆 | `OFD204` → `OFDM204` | `OFD205` | 一個 `DetailTable` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:40-42` |
| `OFDM206` | 單筆 | `OFD206` → `OFDM206` | — (`OFD207` 另外手動載入) | `AfterGetMaintainData` 補撈 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:44`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:98-106` |
| `OFDM213` | 多筆 | `OFD213A` → `OFDM213` | — | `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:36-37` |
| `OFDM214` | 多筆 | `OFD214A` → `OFDM214` | — | `BF_NO`;`CopyPKey` = `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:33-35` |
| `OFDM215` | 多筆 | `OFD215A` → `OFDM215` | — | `BF_NO`;`CopyPKey` = `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:35-37` |

> ⚠ **`OFD207` 不是宣告出來的明細。** `OFDM206_PO` 只宣告了主檔;`OFD207`(使用記錄)是在 `AfterGetMaintainData` 裡**用同一個 `DbCommand` 改寫 `CommandText` 再 `LoadDataSet`** 撈進來的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:101-105`)。所以它**不會**參與四眼、不會被新增 / 修改 / 刪除,純唯讀顯示。掃描器把它歸為 dataset 不是實體表,原因就在這裡。

### 2.2 `_UPD` 是什麼:三張配對表(本篇核心的一半)

結論寫在 §4.10,這裡只放資料模型面的事實:

| `_UPD` 表 | 正式表 | 誰寫 `_UPD` | 誰讀正式表 |
|---|---|---|---|
| `OFD199A_UPD` | `OFD199A` | 只有 `OFDM199` | `OFDI199`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4499`、`Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:39`、`OFDM204`、`OFDM206` |
| `OFD200A_UPD` | `OFD200A` | 只有 `OFDM199` | `OFDI199`、EC 側 |
| `OFD190A_UPD` | `OFD190A` | 只有 `OFDM199` | `OFDI199`、EC 側 |

「只有 `OFDM199`」是實測結果:對 `Dev/` 全樹搜 `OFD199A_UPD` / `OFD200A_UPD` / `OFD190A_UPD`,命中的 `.cs` 只有 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` 一個檔。

**`_UPD` 不是框架機制。** `architecture.md §3.2` 講的框架雙表四眼(`Basic4EyesPO`,字尾寫死 `_Edit`)是**死碼**,零繼承零實例化;`OFDM199_PO` 繼承的是 `BaseEVADaoPO`,只是把 `xTableMapping` 的實體表名寫成 `OFD199A_UPD` 而已。也就是說**框架完全不知道 `_UPD` 的存在**,它就是一張普通的表。

### 2.3 `_TMP` 是什麼:第三份同形副本,而且是死的

`architecture.md 附錄 D.3` 提過「`OFD199A_TMP` 系列」在修掃描器時被補回母體。查下去的結果:

| 事實 | 錨點 |
|---|---|
| `OFDM199A_PO`(在 `PO.OFD`)宣告 `OFD199A_TMP` + 六張 `*_TMP`,與 `OFDM199_PO` 的結構**完全同形**,只是字尾換成 `_TMP` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199A_PO.cs:39-47` |
| 兩者連 vdb 名都一樣(都叫 `OFDM199` / `OFDM199_Fund` / …),共用同一份 `OFDM199Model.xsd` | 同上 vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-47` |
| 這支 PO **有**被編譯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj:319` |
| 但 `ATLAS.OFD` 裡**沒有** `OFDM199A_Ctl`,`FormProxy.OFD` 有 `OFDM199A_Pxy.cs` 檔案卻**不在 csproj 裡**(`FormProxy.OFD.csproj` 只列 `OFDM199_Pxy.cs`) | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/FormProxy.OFD.csproj:214` |
| 那支 `.cs` 的 `InitializeControl()` 還 `new OFDM199A_Ctl()`,型別在 `Vendor.Product.TA.Control.OFD` 底下——**不存在** | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs:19` |

所以 `_TMP` 那一整套(7 張表 + 1 支 PO + 1 個不編譯的 Pxy)**永遠不會被執行**。

> ⚠ **別跟 OTA 的 `OFDM199A` 搞混。** `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM199A_PO.cs:67-70` 也叫 `OFDM199A_PO`,但它在 `Vendor.Product.TA.PO.OTA` 命名空間,指的是 `OFD199` / `OFD200`(**沒有 A 字尾**的另一組表),而且**有**完整的 `OFDM199A_Ctl` 與 `OFDM199A_Pxy`。`architecture.md 附錄 D.3` 的 D3 缺陷(同代號雙實作)講的就是這一對。本片只負責 OFD 側那份死的。

### 2.4 表的主鍵與四眼欄位

「PK」欄取自對應 xsd 的 `xs:unique … msdata:PrimaryKey`,是 **DataTable 的鍵**,不保證等於 DB 上的 constraint(`architecture.md §5.5`)。

| 表 | vdb 名 | PK(來源 xsd) | 四眼 13 欄 | 欄數 |
|---|---|---|---|---|
| `OFD191` | `OFDM191` | `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 30 |
| `OFD192` | `OFDM192` | `FUND_ID` `BNG_YEAR` | 齊 | 26 |
| `OFD193A` | `OFDM193` | `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 34 |
| `OFD194A` | `OFDM194` | `FUND_ID` `BNG_AMT` `END_DATE` `BNG_DATE` `BF_NO` `CRNCY_CD` `FEE_TYPE` | 齊 | 35 |
| `OFD194` | `OFDM194B` | `FUND_ID` `CRNCY_CD` `BF_NO` `BNG_DATE` `END_DATE` `BNG_AMT`(**無 `FEE_TYPE`**) | 齊 | 34 |
| `OFD195A` | `OFDM195` | `REL_TYPE` `REL_NO` `AGENT_ID` `AGENT_CODE` `REL_IDNO` | 齊 | 28 |
| `OFD196A` | `OFDM196` | `REL_TYPE` `AGENT_ID` `AGENT_CODE` `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 38 |
| `OFD197A` | `OFDM197` | `MKT_ID` `ID_NO` | 齊 | 22 |
| `OFD198` | `OFDM198` | `DISC_CODE` `FUND_ID` `BF_NO` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 35 |
| `OFD199A_UPD` | `OFDM199` | `CAMPAIGN_CODE` `PROMT_SCOPE` | 齊 | 29 |
| `OFD200A_UPD` | `OFDM199_Fund` | `CAMPAIGN_CODE` `FUND_ID` `PROMT_SCOPE` `CRNCY_CD` `FEE_TYPE` `BNG_AMT` | 齊 | 29 |
| `OFD190A_UPD` | `OFDM199_RSP` | 同上六欄 | 齊 | 37 |
| `OFD201A` | `OFDM199_Channel` | `CAMPAIGN_CODE` `PROMT_SCOPE` `CHANNEL_CD` `CHANNEL_CODE` | 齊 | 20 |
| `OFD202A` | `OFDM199_Mkt` | `CAMPAIGN_CODE` `PROMT_SCOPE` `MKT_ID` | 齊 | 19 |
| `OFD203A` | `OFDM199_AGENT` | `CAMPAIGN_CODE` `PROMT_SCOPE` `AGENT_ID` `AGENT_CODE` | 齊 | 20 |
| `OFD687A` | `OFDM199_PROD` | **`COMPAIGN_CODE`** `PRODUCT_ID` | 齊 | 19 |
| `OFD204` | `OFDM204` | `CAMPAIGN_CODE` | 齊 | 24 |
| `OFD205` | `OFD205` | `FUND_ID` `CAMPAIGN_CODE` | 齊 | 18 |
| `OFD206` | `OFDM206` | `BF_SRNO` `CAMPAIGN_CODE` | 齊 | 21(OFD 側 vdb 29,多 8 個 join 欄) |
| `OFD207` | `OFD207` | — | **無** | 12 |
| `OFD213A` | `OFDM213` | `FUND_ID` `CRNCY_CD` `NON_FEE_BANK` | 齊 | 22 |
| `OFD214A` | `OFDM214` | `BF_NO` `FUND_ID` | 齊 | 22 |
| `OFD215A` | `OFDM215` | `BF_NO` `FUND_ID` | 齊 | 21 |

四張沒有實體表的 vdb DataTable:

| vdb 表 | 用途 | 錨點 |
|---|---|---|
| `OFDM197B` | `OFDM197` 匯入畫面的戶號清單,**只有 `BF_NO` 一欄** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:45` |
| `OFDM214_Copy` | `OFDM214` 複製對話框的四個參數欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:58` |
| `OFDM199_Fund_Detail_D` | `GetOFD193` 抓牌告費率回來當「原費率」對照,8 欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:130` |
| `OFDM206A` | `OFDM206_PO.CheckData` 的回傳容器,xsd 內**零欄位** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:254` |

### 2.5 欄位中文名:本片填得相當完整

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。本片 23 張表的業務欄幾乎都有填,只有四眼 13 欄與 `DATAID` 一律留空——這是全庫通則,不是本片的問題。

三個要特別記住的 Caption 陷阱:

| 陷阱 | 內容 | 錨點 |
|---|---|---|
| **兩欄同名** | `OFD206` 的 `USED_ALLOT_TIMES` 與 `USED_RSP_TIMES` Caption **都叫「單筆已用次數」**;`ALLOT_TIMES` 與 `RSP_TIMES` **都叫「單筆可用次數」**。看 Caption 分不出單筆 / 定額 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM206Model.xsd:46-49` |
| **欄名拼錯** | `OFD687A` 的活動代碼欄拼成 `COMPAIGN_CODE`(C-O-M),不是 `CAMPAIGN_CODE`。PO 為此寫了一個 `if` 特例補救 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494` |
| **同名不同義** | `OFD199A_UPD.FEE_TYPE` Caption 是「手續費類型」(`OFDM199_Fund` 的 `CAMP_DISC_TYPE` 才是「費率種類」),而 `OFD191`~`OFD198` 的 `FEE_TYPE` Caption 是「費率種類」(永久 / 某期間) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM199Model.xsd` vs `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM191Model.xsd` |

### 2.6 狀態碼

本片沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`),本片的 PO **一次都沒有**跟 `EVAStatusCode` 的常數做比較。

唯一直接碰 `STATUS` 字面值的地方是三段繞過四眼的批次 SQL,寫死 `'301'`:

| 位置 | SQL 片段 | 錨點 |
|---|---|---|
| `OFDM197.BatchAdd` | `insert into OFD197A(… STATUS …) values(… ,'C','301', …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |
| `OFDM206.BatchAdd` | `select … ,'301',:USERID,SYSDATE,…` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185` |
| `OFDM206.BatchAddEC` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:298` |

**假設**:`'301'` 是 `EVAStatusCode.ApproveAdd`(已覆核新增)。依據是這三段同時把 `ENTRYID` / `VERIFYID` / `APPROVEID` 全部填成同一個使用者,語意上就是「一步到位已覆核」。`architecture.md §3.10` 說全庫掃到的 `STATUS` 字面值是 `'0'`~`'6'`、`'8'`、`'9'` 單字元,**三位數的 `'301'` 不在那個集合裡**——兩邊對不上,值域到底幾位數要查資料庫才能確定。本文把它標為 **〔假設〕缺:DB 連線**。

`OFDM206` 另外有一處把 `CAMPAIGN_TYPE` 當狀態用:`if (row.CAMPAIGN_TYPE > 0) return;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64`),`0` 代表「開戶優惠」。值域出處查不到 `CTL014` 的對應分類,標**推測**。

## 3. 畫面清冊

### 3.1 維護 M

15 支全部六層齊全,全部在 `Dev/ATLAS.OFD`(UI / FormProxy / Control / PO)+ `DataEntity.OFD7` / `UIEntity.OFD7`(Model / View)。中文名待選單表回填,「用途」欄為推測。

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | 子對話框 | 特別之處 |
|---|---|---|---|---|---|---|
| `OFDM191` | 基金牌告費率(幣別 × 金額級距) | 齊 | `OFD191` | — | — | 只有一檔費率;`WHERE BNG_AMT = 1` 抓群首 |
| `OFDM192` | 基金牌告費率(年度級距) | 齊 | `OFD192` | — | — | 費率與固定金額二擇一;`WHERE BNG_YEAR = 1900` 抓群首 |
| `OFDM193` | 基金牌告費率(境內外 × 六檔費率) | 齊 | `OFD193A` | — | — | CTE 把 `OFD081A` 與 `OFD081` union 成一張;逐年遞減檢核掛錯分支(附錄 E.1) |
| `OFDM194` | 受益人專屬費率(境內) | 齊 | `OFD194A` | — | `OFDM194p0` 複製 | 六檔費率;有「複製受益人」 |
| `OFDM194B` | 受益人專屬費率(境外) | 齊 | `OFD194` | — | — | 兩檔費率;**沒有**複製功能 |
| `OFDM195` | 優惠關係人(員工 / 推薦人)名單 | 齊 | `OFD195A` | — | — | 七成程式碼是註解;`CheckData` 三層外殼全在,沒人呼叫(附錄 E.3) |
| `OFDM196` | 身分別 × 銷售機構專屬費率 | 齊 | `OFD196A` | — | — | 多一組轉申購費率;明細 SQL 的日期條件被註解 |
| `OFDM197` | 行銷身分別歸屬受益人 | 齊 | `OFD197A` | — | `OFDM197p0` CSV 匯入 | 整條六層是 Big5;匯入繞過四眼(附錄 E.2 / E.5) |
| `OFDM198` | 優惠專案專屬費率 | 齊 | `OFD198` | — | — | 費率欄 Caption 是「顧問費率」與「手續費率」 |
| `OFDM199` | EC 促銷活動設定 | 齊 | `OFD199A_UPD` | `OFD190A_UPD` `OFD200A_UPD` `OFD201A` `OFD202A` `OFD203A` `OFD687A` | `OFDM199p0`~`OFDM199p3` 六個明細編輯窗 | 本片最大;`_UPD` 機制(§4.10) |
| `OFDM204` | EC 優惠活動次數上限 | 齊 | `OFD204` | `OFD205` | — | 最小的一支 PO(121 行) |
| `OFDM206` | EC 優惠活動個人可用次數 | 齊 | `OFD206` | —(`OFD207` 唯讀補撈) | `OFDM206p0` 戶號匯入 · `OFDM206p1` EC 整批 | 唯一有伺服端 `BeforeAdd`;刪除確認邏輯反了(附錄 E.6) |
| `OFDM213` | 基金免收匯費銀行 | 齊 | `OFD213A` | — | `OFDM213p0` 複製基金 | `IsBfExsits` 查一個不存在的欄(附錄 E.8) |
| `OFDM214` | 受益人 × 基金 匯費收取碼 | 齊 | `OFD214A` | — | `OFDM214p0` 複製戶號 · `OFDM214p1` 複製基金 | `Ctl` 七成是註解 |
| `OFDM215` | 受益人 × 基金 簡碼 | 齊 | `OFD215A` | — | `OFDM215p0` 複製戶號 · `OFDM215p1` 複製基金 | 與 `OFDM214` 幾乎一模一樣,但 `catch` 少一行(附錄 E.9) |

### 3.2 查詢 I

**本片無 I 畫面。**原因:`DataEntity.OFD7` 只收 M 型的 Model,同主題的查詢畫面 `OFDI199` 在另一個專案 `Dev/ATLAS.OFD.Query`,不屬於本片(但它是理解 `_UPD` 的關鍵,見 §4.10)。

### 3.3 批次 B

**本片無 B 畫面。**三個 CSV 匯入入口是 M 畫面的子對話框,不是 `xOneStepProcessForm` 型的 B 畫面(見 §6)。

### 3.4 報表 R

**本片無 R 畫面。**`DataEntity.OFD7` 底下沒有任何 `*R*Model.xsd`,`Dev/ATLAS.OFD.Report` 也沒有對應這 15 支的報表(見 §7)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFD7 其餘十四支維護畫面的分群、卡控層次與共同寫法
圖中文字:① 卡控幾乎全在 UI 的 DoValidate，伺服端只有一支再驗一次 / validatorManager1 / 必填與型別 / DoValidate / 業務檢核 / SetMasterToDetail / 把主鍵塞進明細 / 伺服端 BeforeAdd / 只有 OFDM206 有 / ② 費率階梯群：靠寫死常數抓「群組第一筆」 / OFDM191 / WHERE BNG_AMT = 1 / OFDM192 / WHERE BNG_YEAR = 1900 / OFDM193 194 194B 196 198 / WHERE BNG_AMT = 1 / 起始值不是常數就消失 / 過濾且無提示 / ③ 對象別費率群：同一句 FeeTypeValidate，四支各抄一份 / OFDM194 / OFD194A 字串串接 SQL / OFDM194B / OFD194 同一份程式碼 / OFDM198 / OFD198 換成專案代碼 / catch 不補結果列 / 例外時當成通過 / ④ 匯費簡碼群：ROW_NUMBER 取群組首列，外加複製功能 / OFDM213 / ExecCopy 複製基金 / OFDM214 / ExecCopy 基金或受益人 / OFDM215 / ExecCopy 基金或受益人 / IN 子查詢字串拼接 / 參數值直接進 SQL / ⑤ 批次匯入：三個入口繞過四眼，直接寫入已覆核狀態 / OFDM197 BatchAdd / delete+insert 狀態寫死 / OFDM206 BatchAdd / insert select 狀態寫死 / OFDM206 BatchAddEC / 條件寫死 etraflg=Y / 不經 BeforeAdd / 主畫面卡控全繞過
```

*圖:圖 4 其餘畫面分群。橘框=正常的維護入口;橘虛框=風險寫法;白框=一般步驟。四群十四支畫面的共同體質：卡控幾乎全在 UI，伺服端只有 OFDM206 有一道 BeforeAdd，而三個批次匯入入口連那一道都繞過。*

```text
[圖] OFDM199 的 _UPD 暫存表到正式表的流程，以及未被使用的 _TMP 第三份副本
圖中文字:① 維護端：OFDM199 一支畫面，同時寫兩種表 / OFDM199 維護畫面 / 7 張表掛同一次四眼 / 走 _UPD 的 3 張 / OFD199A_UPD 等 / 直接寫正式的 4 張 / OFD201A OFD202A 等 / 同一顆四眼狀態 / 無法分開送審 / ② 四眼：輸入 → 驗證 → 覆核，全掛在 _UPD 主檔上 / 輸入 Entry / 寫 OFD199A_UPD / 驗證 Verify / 資料仍在 _UPD / 覆核 Approve / 資料仍在 _UPD / OFD199A 仍是舊值 / EC 端看到舊費率 / ③ 生效：repo 內找不到搬運者，無 SP 無批次無 Trigger / OFD199A_UPD / 覆核完的新費率 / 未知搬運程序 / 假設在版控外 / OFD199A OFD200A OFD190A / 正式表 / OFDI199 EC 計價 / 只讀正式表 / ④ 第三份同形副本：_TMP 系列，編得起來但沒有入口 / OFDM199A_PO / PO.OFD 內 有進 csproj / OFD199A_TMP 等 7 張 / 全庫只有這支宣告 / OFDM199A_Pxy / 檔案在 但不在 csproj / 沒有 Ctl 與 UI / 永遠不會被執行 / ⑤ 立即生效的那四張：改完不必等生效，EC 當下就吃到 / OFDM199 存檔 / 四眼狀態只寫在主檔 / OFD201A OFD202A / 通路 / 身分群組 / OFD203A OFD687A / 銷售機構 / 組合基金 / EC 與 Common 直接讀 / 沒有等待期
```

*圖:圖 3 _UPD 機制（本篇核心）。橘框=真的會動的東西;橘虛框=風險或無入口的死碼;黑框=repo 內看不到內容。最要記住的是 ① 與 ⑤：同一次存檔裡，三張費率表進暫存等生效，四張對象表當下就改了正式表——兩半的生效時機不一樣。*

本章順序照 §0.1 的五塊業務線排,不照代號順序: **A 牌告費率** §4.1~§4.3 · **B 對象別費率** §4.4~§4.6 · **C 資格名單** §4.7~§4.8 · **D EC 促銷** §4.9~§4.11 · **E 匯費簡碼** §4.12。

### 4.0 十五支共同的骨架

先把重複的部分講完,後面各節只寫差異。

| 環節 | 共同做法 | 錨點(以 `OFDM191` 為例) |
|---|---|---|
| UI 基底 | `xMaintainForm`(無原始碼,從呼叫端反推),`TabPages = 2`(查詢頁 + 維護頁) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:84` |
| 存檔前檢核 | `OFDM191_BeforeAddButtonClicked` / `BeforeModifyButtonClicked` → `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:155-178` |
| 主檔值下推 | `SetMasterToDetail()` 在檢核通過**之後**才跑,把畫面上半的鍵塞進每一列明細 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:66-77` |
| 四眼 | 全走框架,PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個取數事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:151-164` |
| ToDo | `xTableHelper.AppendToDoString(<表名>, args.ModelVDB)`,只在 `args.Status == xEVAStatus.ToDO` 時接上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:101-102` |
| 分群 | 多筆型畫面的「主檔查詢」都是同一張表再過濾一次,只取群組首列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92` |

**三件全片通用、值得先記住的事:**

1. **`SetMasterToDetail()` 在 `DoValidate()` 之後跑。** 所以 `DoValidate()` 看到的明細列,鍵欄位(`FUND_ID` / `CRNCY_CD` / `BNG_DATE` …)**還是舊值或空的**。`OFDM193` 與 `OFDM196` 的逐年遞減檢核就是踩在這條上出事的(附錄 E.1)。

2. **`if (this.ValidateErrList.ErrorCount != 0) return;` 這一行會截斷後面所有業務檢核。** 例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:50`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:67`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:218-219`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:42`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:39`。使用者只會看到必填錯誤,修完再存才會看到業務錯誤——要按兩次以上。

3. **兩支畫面的「修改」直接呼叫「新增」的 handler**,所以兩者的檢核完全一樣:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:180-183`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:137-140`。

### 4.1 `OFDM191` — 基金牌告費率(幣別 × 金額級距)

- **用途(推測)**:一檔基金 × 一個交易幣別 × 一段申購期間,依「申購金額級距」設定 `ALLOT_FEE_RATE`(申購手續費率 %)。畫面上半選基金 / 幣別 / 費率種類 / 日期,下半是金額級距表。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:74-105`,`LEFT JOIN FSK003`(幣別名)`OFD081`(基金簡稱)`OFD062`(基金公司)。

- **明細查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:119-144`,同樣三個 join,多帶 `BNG_AMT` `END_AMT` `ALLOT_FEE_RATE`。

**「群組首列」是靠寫死常數抓的。** 主檔 SQL 的 `WHERE BNG_AMT = 1`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92`)加上 `SELECT … ,1 BNG_AMT ,1 END_AMT`(`:81-82`)——把金額欄硬塞成 1,讓多筆四眼引擎以為每一群只有一列。這能成立是因為 UI 的階梯控制元件把第一階起始金額鎖死在 1:`LevelGridUtility(this.ugrdOFDM191, "BNG_AMT", "END_AMT", …, 1m, 999999999999m)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:210`,`LevelGridUtility` 無原始碼,從呼叫端反推)。**但凡有一筆資料不是從這支畫面寫進去的(例如 `OFDB004`),而且起始金額不是 1,那一整群在 `OFDM191` 就查不到、也改不到,而且沒有任何提示。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:43-46` |
| 存檔前 | 申購日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:48-51` |
| 存檔前(**僅新增**) | `custCRNCY_CD.Text` 為空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:53-59` |
| 查詢前 | 查詢條件日期(起) > (迄) | 訊息同名,`e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:131-140` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92` |

**欄位轉換**:費率種類 `'1'`(永久)時,起迄日被寫成 `"00000000"` / `"99999999"`,不是畫面上的日期(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:74-75`)。**這跟 `OFDM193` / `OFDM194` 的境內分支寫空字串 `""` 不一樣**,同一個語意在本片有兩種表示法,見附錄 E.11。

**跨表更新**:無。`OFDM191_PO` 只有三個取數事件,沒有任何 `After*`。

### 4.2 `OFDM192` — 基金牌告費率(年度級距)

- **用途(推測)**:同一檔基金,依「持有年度」分段給費率。與 `OFDM191` 的差別是級距軸從金額換成年度,而且多一個 `FIX_ALLOT_FEE`(固定申購手續費),與費率二擇一。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:70-91`;**只 join `OFD081` 與 `OFD062`,沒有幣別**——`OFD192` 整張表沒有 `CRNCY_CD`。

- **群首常數**:`WHERE BNG_YEAR = 1900`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82`),對應 UI 的 `LevelGridUtility(…, "BNG_YEAR", "END_YEAR", …, 1900m, 9999m, 1m)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:166`)。與 `OFDM191` 同型,常數不同。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 逐列:`ALLOT_FEE_RATE = 0` 且 `FIX_ALLOT_FEE = 0` | 「'第 N 列申購手續費率(%)'與'固定申購手續費'必須擇一輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:122-130` |
| 存檔前 | `CheckPKeyRequire()` 不過 | 「年度(起),年度(迄)必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:132-135` |
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:137-140` |
| 格子離開時 | 年度(起)或(迄)為空 | 訊息 + 整列標紅,**故意不 `e.Cancel`** | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:218-231` |
| 格子更新前 | `CheckPKeyDuplicate()` 不過 | 「'年度(起)''年度(迄)'重覆」+ `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:258-264` |
| 主檔取數 | `BNG_YEAR = 1900` | 不是 1900 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82` |

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:226` 留了一行註解說明為什麼不 `e.Cancel`:「不下 e.Cancel , 以免只因為 P_key 未填而把整個 Row 的資料回復」——這是刻意的取捨,不是漏寫。

**跨表更新**:無。

### 4.3 `OFDM193` — 基金牌告費率(境內外 × 六檔費率)

這是 A 塊裡功能最完整的一支,也是本片**兩個「檢核掛錯分支」缺陷**的第一個。

- **用途(推測)**:與 `OFDM191` 同一件事,但(a) 支援境內 / 境外兩種基金主檔,(b) 費率從一檔擴成六檔:單筆申購 `ALLOT_FEE_RATE` / `ALLOT_FEE_RATE1` / `ALLOT_FEE_RATE2` 與定期定額 `RSP_FEE_RATE` / `RSP_FEE_RATE1` / `RSP_FEE_RATE2`,(c) 多一個 `MEMO`。

**境內外怎麼做的**:主檔與明細 SQL 各自用一段 CTE `MYOFD081A`,把 `OFD081A`(標 `'2'`)與 `OFD081`(標 `'1'`)`UNION ALL` 成一張虛擬基金表,再用 `FUND_TYPE` 當條件過濾(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:69-87`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:135-153`)。這比 `dsm.md §4` 記的「`AND :FUND_TYPE = '2'` … `UNION` …」乾淨一點,但**同一段 CTE 在同一個檔裡抄了兩份**,改一邊要改兩邊。

**UI 依 `FUND_TYPE` 切換的三件事**:

| 動作 | 境外(`'1'`) | 境內(`'2'`) | 錨點 |
|---|---|---|---|
| 基金搜尋器來源 | `SHORE_ID.OffShore` | `SHORE_ID.OnShore` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:594-608` |
| 費率 1 / 2 欄 | 隱藏 + 禁止編輯 | 顯示 + 可編輯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:599-612`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:624-643` |
| 存檔前 | 費率 1 / 2 強制歸零,起迄日填 `00000000`/`99999999` | 保留使用者輸入,起迄日填 `""` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-108` |

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:45-48` |
| 存檔前 | 申購日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:50-53` |
| 存檔前(僅新增) | 幣別為空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:55-61` |
| 存檔前(**僅 `FUND_TYPE == "1"`,即境外**) | 六檔費率不符逐年遞減 | 「手續費率需符合逐年遞減原則,請檢查手續費率!!」 | **形同虛設**,見附錄 E.1 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-75` |
| 選基金後(僅境內) | 前收型基金不開放費率 1 / 2;不開放定額的基金不開放定額費率 | 欄位轉唯讀並清值 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:393-430` |
| 格子啟用前 | 境外要編費率 1 / 2 | `Activation.NoEdit` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:624-643` |
| 查詢前 | 查詢日期(起) > (迄) | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:184-192` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:107` |

〔客戶特定〕查詢頁選「境內」時基金公司被寫死成 `"Atlas"` 並鎖住:`this.custFH_CD_0.Value = "Atlas";`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:570-573`)。

**跨表更新**:無。

### 4.4 `OFDM194` 與 `OFDM194B` — 受益人專屬費率(成對,但不是本表/異動表)

**先回答最容易誤會的問題:`OFD194` 與 `OFD194A` 不是「本表 vs 異動表」,不像 BMS 的 `CHG`(`bms.md §2`)。它們是同一個業務概念的境內 / 境外兩張表,各自獨立、各有一支畫面、互不參照。**

證據四條:

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `OFDM194_PO` 的主檔 join `OFD081A`;`OFDM194B_PO` 的主檔 join `OFD081` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:96-97` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:99-100` |
| 2 | `OFDM193` 的 CTE 明寫 `OFD081A` → `FUND_TYPE '2'`(境內)、`OFD081` → `'1'`(境外) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:75`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:85` |
| 3 | 欄位形狀跟著境內外走:`OFD194A` 六檔費率(境內才用得到 1 / 2),`OFD194` 只有 `ALLOT_FEE_RATE` 與 `RSP_FEE_RATE` 兩檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:133-138` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:136-137` |
| 4 | 兩張表沒有任何共同欄位可以串(沒有 `BF_CHG_NO` 這種單號),也沒有任何一段程式同時讀兩張 | 全庫搜 `OFD194A` 與 `OFD194` 的交集為空 |

**兩支的差異總表**(這是「成對畫面只改一邊」的活教材):

| 面向 | `OFDM194`(`OFD194A`,境內) | `OFDM194B`(`OFD194`,境外) | 評註 |
|---|---|---|---|
| `MasterPKey` | 含 `FEE_TYPE` | **不含** `FEE_TYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:45` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:46-50`;與各自 xsd 的 PK 一致,**不是 bug** |
| 費率欄 | 6 檔 | 2 檔 | 與境內外的業務需求一致 |
| 逐年遞減檢核 | 有(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72`) | **無** | 境外只有 1 檔費率,沒得遞減,**合理** |
| `FeeTypeValidate` | 有 | 有,**一字不差** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:350-399` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:191-240`,只差表名 |
| 複製受益人 | 有 `Copy` + `CheckRepeat` + 子畫面 `OFDM194p0` | **完全沒有** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:192-340` |
| 檢核訊息 | 同一句「同一基金+幣別+受益人,只可設定一種費率種類!!」出現 5 處 | 同一句出現 5 處 | 合計 10 處硬編字串 |

**`FeeTypeValidate` 在做什麼**:使用者選了費率種類 A,程式就拿「另一種」B 去查同一個基金 + 幣別 + 受益人有沒有資料;查到就擋。UI 端把「另一種」算好再傳:`(uoptFEE_TYPE.Value == FEE_TYPE.Forever ? FEE_TYPE.Course : FEE_TYPE.Forever)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:110`)。

**這支檢核有三個問題**(附錄 E.4):SQL 全用字串串接;`catch` 只記 log **不補結果列**,而 UI 端 `if (View.Util.Result.Rows.Count > 0) return ReturnCode;` 否則 `return true`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:114-117`)——**資料庫一出錯就當成通過**;而且只在 `ActionMode == Add` 時才跑(`:104`),改成另一種費率種類時不檢查。

**`Copy`(只有 `OFDM194` 有)的四步驟**,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:192-340`:

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 用來源戶號撈設定,撈不到就把「查無資料」換成「From 受益人戶號 + 基金代碼 的設定資料不存在,請重新選擇」 | `:211-222` |
| 2 | 換成目的戶號再撈一次,檢查目的端是否已有資料 | `:229-246` |
| 3 | 目的端有資料就先 `ApproveDelete` 刪掉 | `:254-266` |
| 4 | 把來源列的 `BF_NO` 換成目的戶號、四眼 13 欄全部清空(日期填 `1900/1/1`)、再 `Add` | `:268-327` |

**步驟 4 的分批寫入是為了 ToDo**:`if (source_data.Rows.Count == 1) base.Add(...) else` 逐批 `this.Add(...)`,註解寫「若多批資料的話要分別 Add,因為要分別寫 todo」(`:294-296`)。分批的條件字串用 `String.Format` 拼 `DataTable.Select()`(`:306`、`:311`),基金代碼帶單引號會炸。

**卡控總表(兩支合併,標註哪支有)**

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:48-49`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194B.cs:48-49` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:52-55` |
| 存檔前(僅新增) | 幣別空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:57-63` |
| 存檔前 | 六檔費率不符逐年遞減 | 訊息 | 阻擋 | **只有 `OFDM194`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72` |
| 選基金 / 幣別 / 戶號 / 費率種類後(僅新增) | `FeeTypeValidate` 查到另一種費率種類已存在 | 「同一基金+幣別+受益人,只可設定一種費率種類!!」 | 阻擋 | 兩支各 5 處 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:344`、`:424`、`:579`、`:608`、`:640` |
| 複製前 | From 與 To 戶號相同 | 「戶號與複製戶號不可相同」 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194p0.cs:50` |
| 複製中 | 來源不存在 / 目的已存在 | 兩句不同訊息 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:446-463` |
| 複製中 | 寫入筆數與 `DataRow` 筆數不符 | 丟 `ApplicationException("複製的資料筆數錯誤。")`,交易回滾 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:321-324` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | 兩支 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:100`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:103` |

**跨表更新**:`Copy` 會 `ApproveDelete` 目的戶號的舊資料(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:258`),跨兩個連線的交易(`dbProduct` + `dbPTPF`)一起 commit(`:251-252`、`:328-329`)。其餘無。

### 4.5 `OFDM196` — 身分別 × 銷售機構專屬費率

- **用途(推測)**:針對「某身分別(`REL_TYPE`)× 某銷售機構(`AGENT_ID` + `AGENT_CODE`)」設定一組優惠費率。比 `OFDM193` 多一組轉申購費率 `SWITCH_FEE_RATE` / `1` / `2`,合計九檔。

- **主鍵維度最多**:`MasterPKey` 八欄(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:28-35`),xsd PK 九欄。

- **境內外機制與 `OFDM193` 完全相同**:同一段 `MYOFD081A` CTE 又抄了兩份(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:64-82`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:130-148`),四份 CTE 散在兩個檔裡。

**兩個歷史包袱寫在註解裡**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:61-62` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:127-128` 各留一句「取消欄位:(CHANNEL_CD,CHANNEL_CODE) / 新增欄位:(AGENT_ID,AGENT_CODE)」。UI 端對應的三段「身分別為推薦人時通路必輸」檢核整段被註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:68-78`)。

**明細 SQL 少一個條件。** 主檔 SQL 有 `AddDateTimeParam(..., "BNG_DATE", "END_DATE")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:108-109`),明細 SQL 的同一行**被註解掉**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182`)。後果:使用者在查詢頁下了申購日期區間,主檔清單有濾,點進去看明細時**日期條件不生效**,同一組基金 + 幣別 + 身分別 + 機構下的其他期間資料會一起出現。其他五支同型畫面(`OFDM191` `OFDM193` `OFDM194` `OFDM194B` `OFDM198`)的明細 SQL 都有這一行。**成對(這裡是六胞胎)只改一邊**,列入附錄 E.10。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:62-65` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:98-101` |
| 存檔前 | 有列 `ALLOT_FEE_RATE < 0` | 「單筆申購手續費率 必須大於0」(**訊息說「大於 0」,條件是「小於 0」,0 會過**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:103-104` |
| 存檔前(定額欄可編輯時) | 有列 `RSP_FEE_RATE < 0` | 同上句型 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:105-107` |
| 存檔前(**僅 `FUND_TYPE == "1"`,即境外**) | 有列 `SWITCH_FEE_RATE < 0` | 「轉申購手續費率 必須大於0」 | **形同虛設**,境外此欄被強制歸零 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:112-113` |
| 存檔前(**僅境外**) | 九檔費率不符逐年遞減 | 訊息 | **形同虛設**,見附錄 E.1 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:115-124` |
| 存檔前(**僅境外 + 僅新增**) | 幣別空白 | 「選取的基金不適用此 幣別代碼」 | **境內完全不檢查** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:126-132` |
| 格子啟用前 | 境外要編費率 1 / 2 / 轉申購 | `Activation.NoEdit` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:819-841` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:103` |
| 明細取數 | 日期條件被註解 | 其他期間的列一起出現 | **過濾失效(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182` |

**跨表更新**:無。

### 4.6 `OFDM198` — 優惠專案專屬費率

- **用途(推測)**:以「優惠專案代碼 `DISC_CODE`」為主鍵起頭,針對某基金 + 某受益人設一組費率。與 `OFDM194` 的差別是把「幣別」換成「優惠專案」,而且費率欄的 Caption 特別:`ALLOT_FEE_RATE` 是「顧問費率(%)」、`ORG_ALLOT_FEE_RATE` 是「手續費率(%)」——**兩欄一起存,推測是「原本收多少 / 改成收多少」**。

- **`DISC_CODE` 與 `DISC_NM` 是自由輸入**,不是下拉:`row.DISC_CODE = Convert.ToString(this.utxtDISC_CODE.Text);`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:68-69`)。repo 內找不到 `DISC_CODE` 的代碼字典,所以**沒有任何地方檢查專案代碼存不存在**。

- **join 不含幣別**:`OFD198` 沒有 `CRNCY_CD` 欄,主檔只 join `BMS001A` `OFD081` `OFD062`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:94-100`)。注意它 join 的是 `OFD081`(境外),沒有境內的分支。

**`FeeTypeValidate` 與 `OFDM194` / `OFDM194B` 是同一份程式碼**,只把 `CRNCY_CD` 換成 `DISC_CODE`、表名換成 `OFD198`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:188-237`)。三支的問題完全一樣(附錄 E.4)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:48-49` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:52-55` |
| 選基金 / 專案 / 戶號 / 費率種類後(僅新增) | `FeeTypeValidate` 查到另一種費率種類已存在 | 「同一基金+優惠專案代碼+受益人,只可設定一種費率種類!!」(其中 4 處訊息寫成「同一基金+幣別+受益人」,**文案沒跟著改**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:273`、`:329`、`:447`、`:475`、`:507` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:101` |

**沒有逐年遞減檢核**:`OFD198` 只有一檔費率 + 一檔原費率,不適用。

**跨表更新**:無。

### 4.7 `OFDM195` — 優惠關係人(員工 / 推薦人)名單

本片**程式碼死亡率最高**的一支:`OFDM195_PO.cs` 共 1,724 行,其中 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:506-1722` 是一整塊 `/* … */`,**1,217 行(70%)是 SQL Server 時代的舊實作**(裡面全是 `[OFD195]` 這種中括號語法與 `con.Open()` 自建連線)。活著的只有三段:取數 SQL、`CheckData`、`CheckRspChgDate`。

- **用途(推測)**:登錄誰是「優惠關係人」。`REL_TYPE` 分兩種:`'1'` 員工(對 `COD009.EMP_NO`)、`'2'` 推薦人(對 `OFD072A.SPONSOR_CODE`)。有申請日期 `APPLY_DATE` 與終止日期 `REL_STOP_DATE`。

- **`REL_NO` 是兩個控制項相加**:`Row.REL_NO = this.custEMP_NO.Value + this.custSPONOSR_CODE.Value;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:412`)——靠「其中一個一定是空字串」成立。

- **身分別的姓名與身分證字號是 SQL 裡的 `CASE`**,不是 join 後挑欄:`CASE OFD195A.REL_TYPE WHEN '1' THEN COD009.EMP_NAME WHEN '2' THEN OFD072A.SPONSOR_NAME ELSE N' ' END`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:155-164`)。查詢條件 `ALL_IDNO` 也要把同一段 `CASE` 再寫一次(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:222-233`)。

**`RSP_CHG_DATE` 在畫面上永遠是空的。** 主檔 SQL 把它寫死成空字串:`strSQL += " ,'' RSP_CHG_DATE " …`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:172`),而查詢條件那一段也被註解(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:280-293`)。但 `CheckRspChgDate` 又真的去查 `WHERE RSP_CHG_DATE is not null`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:466-470`)——**欄位有值、刪除時會用到,只是使用者看不到**。xsd 的 Caption 是「產生異動日期」(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM195Model.xsd`)。

**「同一員工只能有一筆未終止資料」這條規則沒有在跑。** 三層外殼都在:

| 層 | 成員 | 錨點 |
|---|---|---|
| PO | `CheckData<T>`,XML doc 寫「檢查同一員工或推薦人是否只存在一筆未終止資料」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:310-449` |
| Control | `CheckData(BasicViewVDB)` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM195_Ctl.cs:109-112` |
| FormProxy | `Check(OFDM195ViewVDB)` | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM195_Pxy.cs:119-125` |

**UI 端唯一的呼叫 `pxy.Check(view)` 被註解**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:163-164`),連同對應的錯誤訊息「此關係人已存在未終止資料,請重新輸入」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:177`)。全 repo 搜 `CheckData` 的呼叫端,`OFDM195` 這條鏈的起點是空的。詳見附錄 E.3。

就算它有在跑,`CheckData` 本身還有兩個問題:條件是 `WHERE REL_STOP_DATE IS NULL`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:332`),而它上一行被註解的舊版是 `REL_STOP_DATE ='1900/01/01'`(`:333`)——**同一個「未終止」語意在這個 repo 有兩種存法**;`REL_STOP_DATE` 是 `xs:string`,Oracle 會把寫入的空字串折成 NULL,所以新資料抓得到,但歷史上用 `'19000101'` 寫進去的抓不到。這與 `cod.md 附錄 E` 記的 `CODM009_PO` 日期哨兵值問題同源。另一個問題是 `ds.Tables["check"].Rows.Count == 0`(正常情況)時**一列結果都不補**(`:416-433`),呼叫端拿到空的 `Result`。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 申請日期為 null 或 `1900/01/01` | 「申請日期 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:118-121` |
| 新增前 | `REL_IDNO` 不是合法身分證也不是合法統編 | 「…不符合正常邏輯,是否忽略?」`No` → 取消;`Yes` → 記 ByPass 訊息後放行 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:310-323` |
| 刪除前 | `CheckRspChgDate` 查到 `RSP_CHG_DATE is not null` 且 `REL_TYPE='1'` | 「該優惠關係人已有系統產生的契約異動資料,是否仍要刪除?」`No` → 取消 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:418-438`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:466-486` |
| 存檔前 | 「同一員工只能一筆未終止」 | **呼叫端被註解,永不觸發** | 記錄不擋(實際等於沒有) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:155-183` |

**`CheckRspChgDate` 是本片唯一寫對的參數化查詢**:`AddInParameter(cmd, "REL_IDNO", OracleDbType.Varchar2, …)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:471-473`)。其餘的 `CheckData` 與主檔 SQL 全是字串串接(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:194-278`、`:345-394`)。

**跨表更新**:無。`OFD195A` 原本應該被 `CODM009` 在員工離職時同步終止,那段**整塊被註解**(見 §8.5)。

### 4.8 `OFDM197` — 行銷身分別歸屬受益人

- **用途(推測)**:把某個受益人(`BF_NO` / `ID_NO`)掛到某個「行銷身分別」(`MKT_ID`,說明來自 `OFD027A.MKT_DESCRP`)底下,附一個 `BELONG_DATE`(歸屬日期)與 `SOURCE_CD`(資料來源碼)。

- **為什麼重要**:`OFD197A` 是 **`OFDM199` 促銷活動「活動對象 = 身分群族」判定的唯一輸入**(見 §8.3)。這張表錯了,EC 上看得到 / 看不到活動就跟著錯。

- **主鍵是 `MKT_ID` + `ID_NO`**,但 2023 年改成用戶號查詢(`// 改用戶號查詢 by Becky 2023.07.25`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:162`),而批次匯入的 delete / insert 也是用 `MKT_ID` + `BF_NO` 當鍵(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:241`)。**寫入用的鍵與表的 PK 不是同一組。**

**〔整條六層是 Big5〕** `OFDM197.cs` / `OFDM197.Designer.cs` / `OFDM197_PO.cs` / `OFDM197_Ctl.cs` / `OFDM197_Pxy.cs` 五個檔都不是合法 UTF-8。用一般編輯器開會看到亂碼,用 `git diff` 看中文也是亂的。詳見附錄 E.7。

**`DoValidate()` 幾乎是空的。** 唯一實質內容(統一編號格式檢查)整段被 `/* */` 包起來(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:56-77`),剩下 `FormvalidatorManager.DataValidate()` 一行。同一個檔裡 `umskID_NO_Validating` 這個事件處理常式**整個方法體都是註解**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:330-349`),註解寫「會跑出多次警告訊息 所以註解」;真正在用的是後來補的 `umskID(bool)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:356-373`)。

**匯入小畫面 `OFDM197p0` 的四個問題**(這是本片最值得盯的一段):

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **重複檢核查錯 DataTable** | `CheckExists` 跑 `Model.DataEntity.OFDM197`(維護頁的資料表),但匯入畫面只填 `OFDM197B`,而且進畫面時 `VDB.UIView.Clear()` 把全部清空。所以 `CheckExists` 永遠回 `false`,「已有資料是否覆寫」的詢問**永遠不會跳** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:204-214` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:107`、`:118-122` |
| 2 | **`*` 記號寫到不存在的欄** | `CheckExists` 把重複的列標成 `row.BF_NAME = "*"`,但匯入用的 `OFDM197B` DataTable **只有 `BF_NO` 一欄**;而 UI 又去 `Columns["BF_NAME"].Hidden = false` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:209`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:85`、`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD7/OFDM197View.xsd:123-142` 的 `OFDM197B` 只宣告 `BF_NO` |
| 3 | **第二次匯入的結果沒被檢查** | 使用者按「是」覆寫後再呼叫一次 `BatchAdd`,回傳值指派給 `vdb1` 卻不再判斷,下一行直接顯示「複製成功」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:88-92` |
| 4 | **CSV 讀到空行就停** | `if (line == string.Empty) break;` 中間有一行空白,後面的戶號全部靜默丟掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |

**`BatchAdd` 的 SQL**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247`)是一段匿名 PL/SQL 區塊:先 `delete OFD197A where MKT_ID = :MKT_ID AND BF_NO = :BF_NO`,再 `insert`,`SOURCE_CD` 寫死 `'C'`、`STATUS` 寫死 `'301'`、`ENTRYID` / `VERIFYID` / `APPROVEID` 全填同一個 `:USERID` 同一個 `SYSDATE`。`ID_NO` 用 `NVL((SELECT ID_NO FROM BMS001A WHERE BF_NO = :BF_NO AND ROWNUM=1),' ')` 反查——**查不到就填一個空白**,而表的 PK 是 `MKT_ID` + `ID_NO`,同一次匯入若有兩個查不到的戶號就會撞 PK。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | `umskID(true)`:`ID_NO` 不是合法身分證 / 統編 | 「…不符合正常邏輯,是否忽略?」`No` → 取消 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:188`、`:356-373` |
| 新增 / 修改前 | 歸屬日期 = `1900/01/01` | 「歸屬日期 不可輸入1900/01/01」+ 清空 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:194-200`、`:232-239` |
| 修改前 | `ID_NO` 格式 | **不檢查**(註解寫「修改時不驗證ID_NO」) | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:242-248` |
| 匯入前 | `MKT_ID` 未選 / 歸屬日期未填 / 清單為空 | 三句必填訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:56-73` |
| 匯入中 | CSV 出現重複戶號 | 「戶號 不可重覆,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:124-129` |
| 匯入中 | CSV 出現空行 | 後面的資料全丟 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |
| 匯入中 | 該行銷身分別已有資料 | 「該行銷身份別已有資料(如清單內*號),是否覆寫資料?」 | **詢問(實際不會觸發)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:232-236` |
| 匯入寫入 | 某列 `ExecuteNonQuery` 回 0 | 「匯入失敗,請檢查資料是否正確」+ 回滾 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:265-270` |
| 匯入全程 | 四眼 | **完全不經過** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |

**匯出範本的編碼是系統 ANSI**:`new StreamWriter(save.FileName, false, Encoding.Default)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:100`)。在 zh-TW 機器上是 Big5,換到別的 locale 產出的檔會不一樣。〔客戶特定〕

**跨表更新**:`BatchAdd` 讀 `BMS001A` 補 `ID_NO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:245`),不寫入。

### 4.9 `OFDM204` — EC 優惠活動次數上限

本片最小的一支 PO(121 行),但它是 D 塊的**判準來源**:`OFD204.CAMPAIGN_TYPE` 決定一檔活動是不是「開戶優惠」,`OFDM206` 與 BMS 兩邊都靠它。

- **用途(推測)**:針對一檔已存在的促銷活動(`OFD199A.CAMPAIGN_CODE`),設定「單筆可用次數」`ALLOT_TIMES` 與「定額可用次數」`RSP_TIMES`、生效 / 有效期限 `BNG_DATE` / `END_DATE`、活動類型 `CAMPAIGN_TYPE`;明細 `OFD205` 列出這檔活動適用哪些基金。

- **主檔 SQL 直接 `SELECT OFD204.*`,再 `left JOIN OFD199A` 補活動簡稱與起迄時間**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:86-92`)。**注意這裡 join 的是正式表 `OFD199A`,不是 `OFD199A_UPD`**——也就是 `OFDM199` 還沒生效的活動,在 `OFDM204` 上是查不到名稱的(§4.10)。

- **日期是字串拼出來再轉**:`to_date(SUBSTR(OFD199A.CAMPAIGN_BNG_DATE||CAMPAIGN_BNG_TIME,1,12),'yyyymmddHH24MI')`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:88`)。`CAMPAIGN_BNG_DATE` 存 `yyyymmdd`、`CAMPAIGN_BNG_TIME` 存 `HHmm`,兩個字串相接取前 12 碼。**任一欄長度不對(例如時間只存 3 碼)就會 `to_date` 失敗整段查詢炸掉**。

- **明細 SQL 的「所有基金」**:`NVL(OFD081A.FUND_SH_NM,'所有基金')`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:111`)——join 不到基金就顯示「所有基金」。這是**用 join 失敗當語意**,如果只是基金代碼打錯、`OFD081A` 查無此筆,畫面一樣顯示「所有基金」,看不出來是設定錯誤。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:43-48` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:49-52` |
| 存檔前 | `ALLOT_TIMES + RSP_TIMES == 0` | 「'單筆可用次數' 或 '定額可用次數' 必須大於0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:53-54` |

> ⚠ 第三條用的是**和**,不是各自檢查。`ALLOT_TIMES = -5`、`RSP_TIMES = 5` 加起來是 0 會被擋;但 `ALLOT_TIMES = -1`、`RSP_TIMES = 2` 加起來是 1 **會過**。repo 內沒有看到欄位層級的非負限制。

**修改走的是新增的 handler**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:180-183`),所以修改與新增的檢核完全一致。

**跨表更新**:無。`OFDM204` 只讀 `OFD199A` 與 `OFD081A`。

### 4.10 `OFDM199` — EC 促銷活動設定(`_UPD` 機制)

本片最大也最重要的一支。**如果你只讀一節,讀這節。**

#### 4.10.1 結論先講

> **`_UPD` 是「暫存 → 生效」的暫存側,但只蓋住七張明細中的三張。** `OFDM199` 一次存檔會同時動到七張表:三張費率相關的寫進 `_UPD` 暫存表, 另外四張對象相關的**直接寫正式表**。四眼狀態只掛在 `_UPD` 主檔上。所以覆核通過之前,「這檔活動給誰用」已經改掉了,「這檔活動費率多少」還沒。 **把 `_UPD` 從正式表搬過去的程式,repo 內找不到**——沒有 SP、沒有批次畫面、沒有 Trigger。

這與 `bms.md §2` 的 `CHG` 機制**同型但不同做法**:BMS 是一張表兩組欄位(`BEF_*` / `AFT_*`)+ 一個生效批次 `OFDB003`;OFD7 是兩張同構的表 + 一個看不到的搬運者。相同點是「覆核通過 ≠ 資料生效」,正好印證 `architecture.md §3` 的警告。

#### 4.10.2 證據鏈

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `OFDM199_PO` 的主檔就是 `OFD199A_UPD`,明細七張裡只有三張帶 `_UPD` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-47` |
| 2 | 查詢畫面 `OFDI199` 的 PO **是同一份程式碼,只把那三張的 `_UPD` 拿掉**,其餘四張一字不差 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46` |
| 3 | EC 專案另有一份 `OFDM199AOracleDao`,讀的也是正式表 + 同樣那四張 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34-43` |
| 4 | 共用 PO 判「這位受益人看得到哪些活動」時,`FROM OFD199A`,而且 `EXISTS` 子查詢分別打 `OFD201A` / `OFD202A` / `OFD200A` / `OFD190A`——**正式表** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4499-4522` |
| 5 | `OFDM204` 與 `OFDM206` 取活動名稱與起迄時,join 的都是 `OFD199A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:126` |
| 6 | 全庫對三張 `_UPD` 表的引用只有 `OFDM199_PO.cs` 一個檔;`DB/SP` / `DB/Trigger` / `DB/View` 底下沒有任何 `_UPD` 相關物件 | 實測 `grep -rl "199A_UPD" Dev/ DB/` 只命中 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` |
| 7 | `OFDM199_PO` 沒有任何 `After*` 事件,`Before*` 也只掛了 `BeforeGetMaintainData` 一個,而且只用來組明細 SQL——**沒有任何把資料搬到正式表的程式** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:39`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:61-82` |

**〔假設〕缺:DB 連線。** 搬運者只能推到「在版控外」為止。三個可能:(a) 一支不在 `DB/SP/` 的 SP(`architecture.md 附錄 B` 說 `DB/` 只涵蓋 16% 的 SP);(b) 一支排程;(c) DBA 手動。**無法從 repo 確認**,也**無法確認搬的是哪些欄位**。

#### 4.10.3 一檔活動的生命週期

| 階段 | 誰做 | `OFD199A_UPD.STATUS` | `OFD199A`(正式) | `OFD201A` `OFD202A` `OFD203A` `OFD687A` |
|---|---|---|---|---|
| 輸入 | `OFDM199` | `Entry*` | 舊值 | **已經是新值** |
| 驗證 | `OFDM199` | `Verify*` | 舊值 | 新值 |
| 覆核 | `OFDM199` | `Approve*` | **仍是舊值** | 新值 |
| 生效 | **未知搬運程序** | 不變 | 變成新值 | 不變 |

第一列的最後一欄是本節最該記住的事:**通路 / 身分群組 / 銷售機構 / 組合基金這四張,輸入當下就改到正式表了**,而 EC 側與共用 PO 直接讀它們(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:39-43`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4502-4513`)。也就是說,**一檔活動的「對象」可以在未覆核狀態下就對外生效,而它的「費率」還停在舊值**——兩半會不一致。列入附錄 E.12。

#### 4.10.4 七張表在畫面上長什麼樣

| 分頁 | vdb 表 | 實體表 | 何時啟用 | 錨點 |
|---|---|---|---|---|
| 基本資料 | `OFDM199` | `OFD199A_UPD` | 永遠 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40` |
| 單筆(轉)申購基金資料 | `OFDM199_Fund` | `OFD200A_UPD` | `PROMT_ITEM` = `'1'` 申購 或 `'3'` 轉申購 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1229-1244` |
| 定期定額資料 | `OFDM199_RSP` | `OFD190A_UPD` | `PROMT_ITEM` = `'2'` 定期定額 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1245-1252` |
| 通路資料 | `OFDM199_Channel` | `OFD201A` | `CAMPAIGN_OBJ` = `'2'` 通路 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1189-1194` |
| 身分群組資料 | `OFDM199_Mkt` | `OFD202A` | `CAMPAIGN_OBJ` = `'3'` 身分群族 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1195-1200` |
| 銷售機構資料 | `OFDM199_AGENT` | `OFD203A` | `CAMPAIGN_OBJ` = `'4'` 銷售機構 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1201-1206` |
| 組合基金資料 | `OFDM199_PROD` | `OFD687A` | `FUND_OPTION` = `'2'` 且 `PROMT_SCOPE` ≠ `'2'`(非臨櫃) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1273-1287` |
| 優惠券資料 | `OFDM199_Coupon` | `OFD670` | **PO 的宣告被註解,只剩畫面** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:48` |

值域出自 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:827-903`(`PROMT_TYPE` / `PROMT_ITEM` / `PROMT_SCOPE` / `CAMPAIGN_OBJ`)與 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014_AGI.cs:10-21`(`PROMT_TYPE` 的 `'3'` 壽星優惠 / `'4'` 優惠券,寫在另一個 `partial class` 裡)。整理在附錄 C。

#### 4.10.5 主檔 PK 含 `PROMT_SCOPE`,但 `OFD687A` 不含

`OFD199A_UPD` 的 PK 是 `CAMPAIGN_CODE` + `PROMT_SCOPE`(活動範圍),所以**同一個活動代碼在不同範圍(臨櫃 / EC / IVR …)是不同列**。六張明細裡有五張跟著帶 `PROMT_SCOPE`,只有 `OFD687A` 的 PK 是 `COMPAIGN_CODE` + `PRODUCT_ID`。

PO 因此要分兩種條件組法:

```
if (strTableName == this.DetailTable[5].dbTableName)
{ strSQL += this.AddParam(model, strTableName, false, "CAMPAIGN_CODE"); }
else
{ strSQL += this.AddParam(model, strTableName, false, new string[] { "CAMPAIGN_CODE", "PROMT_SCOPE" }); }
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:462-465`)

而且 `AddParam` 裡還有一個**針對欄名拼錯的特例**:

```
if (Table == "OFD687A" && c1 == "CAMPAIGN_CODE")
    strName = Table + "." + "COMPAIGN_CODE";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494`)

**這個 `AddParam` 是自己手寫的,不是共用的 `EVAStringHelper.AddParam`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:476-517`),而且**完全不綁參數**——把值用單引號包起來直接串進 SQL(`:500-506`、`:513`)。

#### 4.10.6 `GetOFD193` — 帶出牌告費率當對照

使用者在基金分頁按「帶入牌告費率」時,PO 依 `PROMT_SCOPE` 決定去哪張表撈(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:86-149`):

| `PROMT_SCOPE` | 來源表 | 條件 | 欄位對應 |
|---|---|---|---|
| `'3'`(E/C+IVR)或 `'4'`(EC) | `OFD604A` | `FEE_TYPE='1'` | `ALLOT_FEE_RATE2` → `ALLOT_FEE_RATE1`、`ALLOT_FEE_RATE3` → `ALLOT_FEE_RATE2`(**欄名錯開一位**) |
| 其餘 | `OFD193A` | `FEE_TYPE = FEE_TYPE.Forever` | 一對一 |

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:95-126`。查不到時訊息是 `"查無" + strPROMT_SCOPE_DEC + "牌告手續費率"`,`strPROMT_SCOPE_DEC` 只有 `"EC"` 或空字串兩種(`:97`、`:112`、`:136`)——所以境內情況下訊息會變成「查無牌告手續費率」。

**這裡有一個 Oracle 三值邏輯的入口**:`strPROMT_SCOPE` 由 `GetParamValue` 取得,參數不存在就回空字串(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:526-536`),`"" == "4" || "" == "3"` 為 false 就走 `OFD193A` 那一支。**沒有「參數缺失」的錯誤處理**,直接當成非 EC。

#### 4.10.7 卡控總表

`DoValidate()` 在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:212-328`。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 必填(`validatorManager1`) | 各欄訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:215-219` |
| 存檔前 | `PROMT_TYPE == "2"` 且 `PROMT_SCOPE` 空 | 「'活動範圍'必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:221-223` |
| 存檔前 | 活動起(日+時) > 迄(日+時) | 「'活動日期時間(起)'必需小於'活動日期時間(迄)'」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:225-228` |
| 存檔前(定額頁啟用時) | 有列 `CAMP_DAY_TYPE == "1"` 且活動起日 > 該列 `BNG_DATE` | 「'定時定額 活動優惠日期(起)'必須大於等於'活動日期(起)'」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:236-248` |
| 存檔前(同上) | 有列 `CAMP_DAY_TYPE == "1"` 且活動迄日 > 該列 `END_DATE` | 「…(迄)必須大於等於'活動日期(迄)'」 | 阻擋(**方向存疑**,見下) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:240-253` |
| 存檔前 | 基金頁啟用但無列 / 定額頁啟用但無列 | 「基金資料 必須輸入」/「定時定額資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:258-262` |
| 存檔前 | 通路頁啟用:無列 或 有列 `CHANNEL_DESCRP=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:265-272` |
| 存檔前 | 身分群組頁啟用:無列 / `MKT_ID=''` / 列數與 grid 對不上(代表有重複被 Unique 擋掉) | 三句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:274-287` |
| 存檔前 | 銷售機構頁啟用:無列 或 `AGENT_CODE=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:289-296` |
| 存檔前 | 產品頁啟用:無列 或 `PRODUCT_ID=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:298-305` |
| 存檔前 | `PROMT_ITEM` = 轉申購 且 `PROMT_SCOPE` = 臨櫃 | 「轉申購之活動範圍不適用書面」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:307-311` |
| 存檔前 | `PROMT_ITEM` = 轉申購 時,基金列 `CAMP_DISC_TYPE != "2"` | 「轉申購之申購基金手續費率只能設定固定費率」(**逐列各加一次,錯 N 列就跳 N 條**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:313-324` |
| 存檔前 | 優惠券活動不同基金設不同折數 | **整段被註解** | 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:590-598`、`:614-622`、`:325-327` |
| 存檔前 | 分頁沒啟用 | 該分頁的列**全部清掉**,不提示 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:66-89` |
| 明細取數 | 只帶 `CAMPAIGN_CODE` + `PROMT_SCOPE`(`OFD687A` 只帶前者) | 條件沒帶到的範圍不出現 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:462-465` |

> **「(迄)」那一條的方向存疑。** 兩條檢核都寫 `活動日期 > 該列日期` 就報錯,對「起日」是對的(定額優惠不能比活動早開始),但對「迄日」意思會變成**定額優惠的結束日必須不早於活動結束日**,也就是允許定額優惠比活動晚結束。從業務常識看應該是 `<`(定額優惠不能比活動晚結束)。`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:240` 與 `:236` 的寫法一模一樣,只換了欄位名——典型的複製貼上只改一半。**需求文件不在 repo 內,標「假設」,不改判定**。列入附錄 E.13。

#### 4.10.8 死碼佔 62%

`OFDM199_PO.cs` 1,443 行,其中三大塊是註解:

| 區塊 | 行數 | 內容 | 錨點 |
|---|---|---|---|
| `#region 判斷優惠券之促銷活動是否有匯入名單` | 45 | `Have_COUPON`,查 `OFD671` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:539-583` |
| `#region 複製邏輯mark` | 272 | `GetOFD081` / `GetCampaign` / `CheckCampaign` / `CopyCampaign`,SQL Server 語法 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:586-857` |
| `#region 註解` | 581 | 舊的 `BeforeSelect` / `BeforeGetToDoData` / 主檔 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:861-1441` |

`OFDM199A_Pxy.cs` 也留了對應的四個 Pxy 方法殼在註解裡(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs:45-148`)。xsd 裡 `GetCampaign` / `CheckCampaign` / `OFDM199_Copy` / `OFD081` 四張 DataTable 也還在,都是這批死碼的殘骸。

**主檔查詢也是死的**:`OFDM199_PO_BeforeGetMaintainData` 裡「取得主檔語法」那一段被註解掉(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:66-72`),現在主檔完全交給框架自動生成的 SQL。`BeforeSelect` 與 `BeforeGetToDoData` 根本沒掛(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:39`)。

**刪除前完全沒有卡控。** `OFDM199_BeforeDeleteButtonClicked` 的方法體**整段是註解**,原本要擋的是「此活動已有設定優惠券名單,不可刪除」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1291-1305`)。現在按刪除就直接進四眼刪除流程。

**跨表更新**:無。七張表全部由框架的四眼引擎寫入。

### 4.11 `OFDM206` — EC 優惠活動個人可用次數(BMS 的依賴)

`OFD206` 這張表**主檔持有者是本畫面**,但 `BMSM001`(受益人開戶)把它當明細用(`bms.md §4`)。本節從 OFD 側寫清楚,§8.1 做兩邊對照。

- **用途(推測)**:為某位 EC 網路戶(`BF_SRNO`)在某檔活動(`CAMPAIGN_CODE`)底下,登記單筆 / 定額的可用次數與已用次數。已用次數的明細在 `OFD207`(唯讀顯示)。

- **主檔 SQL**:`SELECT OFD206.*` + 三個 `left JOIN`:`OFD204`(拿 `CAMPAIGN_TYPE` 與 `BNG_DATE`/`END_DATE`)、`OFD199A`(拿活動簡稱與活動起迄)、`OFD601`(拿 `ID_NO` 與 `EC_NAME`)。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:115-132`。

- **`OFD207` 由 `AfterGetMaintainData` 另外撈**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:98-106`),條件是 `CAMPAIGN_CODE` + `BF_SRNO`。

#### 4.11.1 唯一的伺服端卡控

全片 15 支只有這裡掛了 `BeforeAdd`:

```
if (row.CAMPAIGN_TYPE > 0) return;
… select 1 from OFD206 A JOIN OFD204 B ON A.CAMPAIGN_CODE = B.CAMPAIGN_CODE
  WHERE A.BF_SRNO = :BF_SRNO AND A.CAMPAIGN_CODE <> :CAMPAIGN_CODE AND B.CAMPAIGN_TYPE = 0
args.Cancel = Convert.ToInt32(i) > 0;
args.CancelMsg = "每位受益人只能設定一筆開戶優惠";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77`)

兩個要注意的地方:

1. **`A.CAMPAIGN_CODE <> :CAMPAIGN_CODE` 是 Oracle 三值邏輯的典型位置。** `OFD206.CAMPAIGN_CODE` 是 PK 的一部分理論上不會 NULL,所以目前不會出事;但同型寫法在 CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過,改 schema 時要一起看。列入附錄 E.14(嚴重度低)。

2. **這道卡控只在 `Add` 走框架流程時生效。** `BatchAdd` 與 `BatchAddEC` 是自己下 `insert`,**完全不經過 `BeforeAdd`**——整批匯入可以讓同一位受益人掛上兩筆以上的開戶優惠。列入附錄 E.5。

#### 4.11.2 兩個匯入入口

| 入口 | 畫面 | 輸入 | 做什麼 | 錨點 |
|---|---|---|---|---|
| 「戶號清單」 | `OFDM206p0` | `.TXT` / `.CSV`,一行一個戶號 | 對每個戶號 `insert into OFD206 … select … from OFD204 A CROSS JOIN OFD601 B WHERE CAMPAIGN_CODE = :CAMPAIGN_CODE AND B.BF_NO = :BF_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:159-219` |
| 「EC 整批」 | `OFDM206p1` | 無檔案,只選活動 | `insert … select distinct ofd607A.BF_SRNO … from ofd607a,OFD204 where ofd607a.etraflg='Y' and trim(ofd607a.openday) is not null and CAMPAIGN_CODE = :CAMPAIGN_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:271-325` |

**`BF_SRNO` 這一欄在匯入流程裡裝的是戶號,不是 EC 流水號。** `OFDM206p0` 把 CSV 每一行 `Convert.ToDecimal` 之後塞進 `row.BF_SRNO`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106`),而且刻意把欄位標題改掉:`e.Layout.Bands[0].Columns["BF_SRNO"].Header.Caption = "戶號";`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:49`)。PO 端再用 `CROSS JOIN OFD601 B … AND B.BF_NO = :BF_NO`(值傳 `row.BF_SRNO`)把戶號換成真正的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:187-196`)。**這是刻意的、不是 bug,但看程式時極容易誤判**,列入附錄 E.15。

同一個混用在 `CheckExists` 造成一個真的問題:重複檢查組出來的條件是 `BF_NO = {r.BF_SRNO}`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:146-148`,字串串接),但回傳給使用者的訊息卻是 `r.BF_SRNO.ToString()` 且**那是查回來的真 `BF_SRNO`**:訊息寫「此優惠活動已存在戶號:」後面接的其實是 EC 流水號(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:155-157`、`:171`)。使用者拿那串數字回去對戶號會對不上。

#### 4.11.3 `CheckData`:一個從用戶端收 SQL 字串來執行的入口

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:221-269` 做的事:

1. 從 `Model.Utility.Parameters` 取出一個以 DataSet 名為鍵的參數,值是**一整串 SQL**;

2. 再取出一個同名參數當**分隔字元**,把那串 SQL 切成多段;

3. 逐段 `cmd.CommandText = strSQLs[i]` 然後 `ExecuteNonQuery`;

4. 是否 `Commit` 由「有沒有一個叫 `OFDM206_PO` 的參數」決定(`:234`、`:256-259`)。

這條路徑**在 repo 內沒有任何 UI 呼叫端**(全庫搜 `CheckData` 的 UI 層呼叫,`OFDM206` 不在其中),但 `OFDM206_Ctl.CheckData`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM206_Ctl.cs:200-205`)與 `OFDM206_Pxy.CheckData`(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM206_Pxy.cs:48-62`)都在,而 `architecture.md §8` 說 Remoting 邊界就在 UI → FormProxy 之間。**也就是說它是一個對外開放、可以執行任意 SQL 的伺服端入口。** 列入附錄 E.16,嚴重度**高**。

#### 4.11.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選活動後 | `OFD204.CAMPAIGN_TYPE` 是 `DBNull`(該活動沒在 `OFDM204` 設過) | 「請先至EC優惠活動設定檔(OFDM204)進行設定」+ 清空欄位 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:148-157` |
| 存檔前 | 單筆已用 > 單筆可用 | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:40-41` |
| 存檔前 | 定額已用 > 定額可用 | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:42-43` |
| 新增(伺服端) | 該受益人已有另一檔 `CAMPAIGN_TYPE = 0` 的活動 | 「每位受益人只能設定一筆開戶優惠」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77` |
| **刪除前** | 無條件跳「已有使用記錄,是否刪除(Y/N)?」 | **按「是」→ 取消刪除;按「否」→ 執行刪除** | **詢問(方向相反)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:214-217` |
| 戶號匯入前 | 清單為空 / 未選活動 | 兩句必填訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:54-63` |
| 戶號匯入中 | 檔案某行不是數字 | 「戶號(數字)欄位格式不正確,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106-113` |
| 戶號匯入中 | 檔案有重複戶號 | 「戶號不可重覆,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:118-123` |
| 戶號匯入前(伺服端) | `CheckExists` 查到該活動已有這些戶號 | 「此優惠活動已存在戶號:<清單>」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:168-173` |
| EC 整批前(伺服端) | 該活動已有符合條件的資料 | 「此優惠活動已存在 N 筆欲匯入資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:278-291` |
| 兩個匯入 | 「每位受益人只能設定一筆開戶優惠」 | **不檢查** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| 兩個匯入 | 四眼 | **完全不經過**,狀態寫死 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185`、`:298` |

> ⚠ **刪除確認那一條是反的。** `e.Cancel = (ShowMessage(...) == DialogResult.OK);` —— 按「確定(是)」得到 `OK`,`e.Cancel` 變成 `true`,刪除被取消;按「否」才會真的刪。同一份 code base 的其他畫面都是相反的慣例(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:427` 是 `== DialogResult.No` 才 `e.Cancel = true`)。而且這個提示**無條件跳**,不管 `OFD207` 有沒有使用記錄。列入附錄 E.6,嚴重度**高**。

**跨表更新**:兩個匯入直接 `insert` 進 `OFD206`,並讀 `OFD204`(次數上限)、`OFD601`(戶號換流水號)、`OFD607A`(EC 開戶旗標)。`OFD607A` 的條件 `etraflg='Y'` 與 `trim(openday) is not null` 都是寫死的〔客戶特定〕(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:300-301`)。

### 4.12 `OFDM213` `OFDM214` `OFDM215` — 匯費與簡碼三胞胎

三支的骨架幾乎一樣,一起讀最省時間。共同點:

| 共同點 | 內容 | 錨點(以 `OFDM214` 為例) |
|---|---|---|
| 多筆型 + 單一 `MasterPKey` | `OFDM213` 用 `FUND_ID`,`OFDM214` / `OFDM215` 用 `BF_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:34` |
| 群首用 `ROW_NUMBER()` 而不是寫死常數 | `ROW_NUMBER() OVER (PARTITION BY BF_NO ORDER BY CreateDate, UpdateDate, EntryDate, FUND_ID) NUM … WHERE NUM = 1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:249-256` |
| 主檔 SQL 把群內才有意義的欄位填成空白 | `OFDM213` 填 `' ' NON_FEE_BANK, ' ' CRNCY_CD`;`OFDM215` 填 `' ' FUND_ID`;**`OFDM214` 沒填,直接帶 `FUND_ID`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:219-220`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:266`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:244` |
| 有「複製」功能 | `ExecCopy<T>`,由子對話框呼叫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:52-79` |
| 有存在性檢查 | `IsFundExsits(string)` / `IsBfExsits(string)`,例外時回 `-1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:87-134` |
| `DoValidate()` 只有兩條 | PK 欄必填 + 明細不可為空 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:36-48` |

用 `ROW_NUMBER()` 比 A / B 兩塊的 `WHERE BNG_AMT = 1` 乾淨很多——**不依賴任何寫死的哨兵值**。同一套系統同一個問題有兩種解法,改的時候要分清楚在哪一群。

#### 4.12.1 `OFDM213` — 基金免收匯費銀行

- **用途(推測)**:某基金某幣別下,哪一家銀行不收匯費(`NON_FEE_BANK`)。明細 SQL 另外 join `OFD094A`(保管銀行)與 `OFD020V` 兩次(一次查不收匯費銀行名、一次查保管銀行名)(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:258-262`)。

- **`IsBfExsits` 查一個不存在的欄。** `SELECT COUNT(1) FROM OFD213A WHERE BF_NO = '…'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:181-183`),但 `OFD213A` 的欄位只有 `FUND_ID` / `NON_FEE_BANK` / `CRNCY_CD` 加四眼欄,**沒有 `BF_NO`**。執行會 `ORA-00904`,被 `catch` 吃掉回 `-1`。這支方法是從 `OFDM214` / `OFDM215` 複製過來忘了刪,而且 `OFDM213p0` 也沒呼叫它。列入附錄 E.8。

- **解構子沒有解除事件訂閱**:`~OFDM213_PO()` 是空的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:40-43`),另外兩支都有寫 `-=`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:38-43`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:47-52` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:53-56` |
| 格子更新時 | 明細 PK 重複 | 由 `CommonGridHelper.AutoCheckDetailGridCellDuplicatePKeyReturnMsg` 處理 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:368` |
| 複製前 | 來源基金 = 目的基金 | 「基金代碼 與 複製基金 不可相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213p0.cs:46-49` |
| 複製中 | 來源基金在 `OFD213A` 查無資料 | 「來源基金 XXX 不存在,請重新選擇」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:81-85` |
| 複製中 | 目的基金已有資料 | 「複製基金 XXX 己存在,請重新選擇」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:93-97` |

#### 4.12.2 `OFDM214` — 受益人 × 基金 匯費收取碼

- **用途(推測)**:`REMIT_CODE`(贖回匯費收取碼)與 `DIV_REMIT_CODE`(收益分配匯費收取碼),一位受益人一檔基金一組。

- **`FUND_ID` 可以是字面值 `'ALL FUNDS'`**:明細 SQL 用 `CASE OFD214A.FUND_ID WHEN 'ALL FUNDS' THEN CAST('所有基金' AS NVARCHAR2(100)) ELSE OFD081A.FUND_SH_NM END`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:281-283`)。這是寫死的魔術字串,`OFDM215` 也有同一段(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:301-302`),但**兩邊的型別轉換寫法不同**(`CAST(… AS NVARCHAR2(100))` vs `TO_CHAR(…)`)。

- **複製有兩種**:複製受益人(`OFDM214p0`)與複製基金(`OFDM214p1`),分別對應 `CooyBF_NO`(方法名拼錯)與 `CopyFUND_ID`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:142-233`)。

- **複製時 `STATUS` 不清空**:`row.STATUS = row.STATUS;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:149`)是自我指派,等於什麼都沒做。其他四眼欄位全部被清成空字串 + `1900/1/1`,唯獨 `STATUS` 保留來源的值。對照 `OFDM213` 的同一段是 `row.STATUS = string.Empty;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:118`)與 `OFDM194` 的 `row.STATUS = "";`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:273`)。**三支同型功能,兩支清一支不清**。列入附錄 E.9。

- **`CopyFUND_ID` 連 `DATAID` 一起複製**:`newrow.DATAID = row.DATAID;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:183`),註解說「針對每個受益人要寫一個 TODO 和相同的 STATUS,dataid」——是刻意的,但要知道複製出來的列與來源列共用同一個 `DATAID`。

**明細 SQL 的 `IN` 是字串拼出來的:**

```
string strParam = EVAStringHelper.GetParamValue(args.ModelVDB, "BF_NO");
if (strParam != "")//因應複製功能會用子查詢
    strSQL += "AND OFD214A.BF_NO	IN (" + strParam + ")                 \n";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:290-292`)

`ExecCopy` 會把**一整句 `SELECT`** 當成參數值傳進來:`AddParametersRow("BF_NO", SQLOperator.IN, "SELECT BF_NO FROM OFD214A WHERE FUND_ID='" + rowCopy.FROMFUND_ID + "'")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:61-62`)。也就是:**參數值直接當 SQL 片段用,而且那句 SQL 自己又是字串串接出來的**。`OFDM215` 同型(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:73-74`、`:308-310`)。列入附錄 E.17。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:40-45` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:46-49` |
| 複製受益人前 | From = To | 「From 戶號與To 戶號不可相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:58-59` |
| 複製受益人前 | `IsBfExsits` 回 `-1`(查詢本身出錯) | 「檢核失敗,請檢查」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:64-65`、`:69-70` |
| 複製受益人前 | From 戶號查無資料 / To 戶號已有資料 | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:66-72` |
| 複製基金前 | 同上三條,對象換成基金代碼 | 三句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p1.cs:122-137` |
| 複製寫入 | `ApplicationException` | 直接把 `appEx.Message` 當訊息顯示 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:215-221` |
| 複製寫入 | 其他例外 | 「複製失敗,請檢查」+ **附上 `ex.Message`** | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:222-229` |

#### 4.12.3 `OFDM215` — 受益人 × 基金 簡碼

與 `OFDM214` 是同一份程式碼改出來的,只把 `REMIT_CODE` / `DIV_REMIT_CODE` 換成 `SHORT_CODE`。**三個差異值得記**:

| 差異 | `OFDM214` | `OFDM215` | 錨點 |
|---|---|---|---|
| 複製分支判斷 | 看 `OFDM214_Copy` DataTable 的 `FROMFUND_ID` / `FROMBF_NO` 哪個有值 | 看 `Utility.Parameters` **有沒有** `BF_NO` / `FUND_ID` 這個參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:58-76` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:62-80` |
| 一般例外的處理 | `AddResultRow` **後**還呼叫 `CommonExceptionBlocker.HandleBusinessException(ex)` | **沒有呼叫**,例外不進 log | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:228` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:178-184` |
| 主檔 `FUND_ID` | 帶真值 | 填 `' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:244` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:266` |

第二條列入附錄 E.9:**同一段 `catch` 抄了兩份,一份有記 log 一份沒有**。兩份都把 `ex.Message` 串進給使用者看的訊息裡(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:227`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:183`)。

**卡控總表**與 `OFDM214` 同構,錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215.cs:32-45`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215p0.cs:52-68`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215p1.cs:88-104`。

**跨表更新(三支共通)**:複製功能會跨 `dbProduct` 與 `dbPTPF` 兩個連線開交易(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:207-211`),`dbPTPF` 是平台的 ToDo 庫。除此之外不寫別的表。

## 5. 查詢畫面(I)

**本片無此類畫面。**原因:切片的依據是 `DataEntity.OFD7` 這個 Entity 專案,而 ATLAS 的查詢畫面(`*I*`)的 Model / View 一律放在 `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD` 與 `QueryUIEntity.OFD`(`architecture.md §6`),不會出現在 `DataEntity.OFD7` 裡。

同主題的查詢畫面 `OFDI199` 在 OFD.Query 專案。它**不屬於本片**,但對理解 `_UPD` 不可或缺:它的 PO 與 `OFDM199_PO` 是同一份程式碼,差別只在三張表沒有 `_UPD` 字尾(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46`)。**會把資料濾掉而不提示的條件**:它讀的是正式表,所以 `OFDM199` 剛存還沒生效的內容,在 `OFDI199` 上完全看不到,而且沒有任何提示說「有一份未生效的版本」。

## 6. 批次(B)與 WindowsService

**本片無此類畫面。**`DataEntity.OFD7` 底下沒有 `*B*Model.xsd`,`Dev/ATLAS.OFD/Source/UI/UI.OFD/` 底下也沒有繼承 `xOneStepProcessForm` 的 `OFDB*` 畫面——OFD 的批次畫面全在 `Dev/ATLAS.OFDB` 這個獨立專案。

三個**看起來像批次、實際上不是**的東西,放在這裡一起講清楚:

| 入口 | 實際型態 | 有沒有四眼 | 錨點 |
|---|---|---|---|
| `OFDM197p0`(行銷身分別 CSV 匯入) | `OFDM197` 的 `DoExp1` 開出的 `Form` 對話框 | **沒有**,SQL 直接寫 `STATUS = '301'` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:85-91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247` |
| `OFDM206p0`(戶號清單匯入) | `OFDM206` 的 `DoExp1` | **沒有** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:180-186`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206p1`(EC 整批匯入) | `OFDM206` 的 `DoExp2` | **沒有** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:187-193`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

**與 M 畫面的關係**:三個都直接寫 M 畫面的主表,但**跳過 M 畫面所有的伺服端卡控**。`OFDM206` 的「每位受益人只能設定一筆開戶優惠」掛在 `BeforeAdd`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77`),兩個匯入都不會經過。

**失敗處理**:三個都是「某一筆 `ExecuteNonQuery` 回 0 就整批 `Rollback`」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:265-270`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:200-205`)。三個的 `catch` 都是 `tran.Rollback()` 開頭——**如果例外發生在 `BeginTransaction()` 本身,`tran` 是 `null`,`catch` 區塊會再丟一個 `NullReferenceException`,把原始例外蓋掉**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:276-282`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:211-217`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:318-324`)。列入附錄 E.18。

**WindowsService**:本片與四支 WindowsService(`architecture.md §8`)沒有任何關係。

## 7. 報表(R)

**本片無此類畫面。**`DataEntity.OFD7` 底下沒有報表 Model;依 `architecture.md §6` 的命名鐵律,報表的六層在 `.Report` 專案,不會出現在這裡。

| rpt | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| —(本片無) | — | — | — |

要找這 15 支畫面相關的報表,得往 `Dev/ATLAS.OFD.Report` 找,而且 `architecture.md 附錄 C` 提醒過:repo 內的 `.rpt` 檔與程式引用的檔名有一批對不上,查之前先確認。

## 8. 跨模組共用

```text
[圖] OFD7 五組跨模組共用：OFD206 給 BMS、OFD204 判準、OFD197A 餵活動對象、六張表被 OFDB004 共寫、OFD195A 與 COD
圖中文字:A：OFD206 —— 主檔在 OFDM206，BMS 把它當明細 / OFDM206〔OFD7〕 / 主檔持有者 有四眼 / OFD206 / PK EC流水號+活動代碼 / BMSM001〔BMS〕 / 當明細 掛在開戶 / BMS 側先整批刪 / 只用 EC流水號當條件 / B：OFD204 —— OFDM206 與 BMS 都拿它來判活動類型 / OFDM204〔OFD7〕 / 唯一維護入口 / OFD204 OFD205 / 次數上限與適用基金 / CAMPAIGN_TYPE = 0 / 兩邊都用它認開戶優惠 / 兩邊判準一致 / 對得上 / C：OFD197A —— 本片維護，卻是促銷活動對象判定的輸入 / OFDM197〔OFD7〕 / OFD197A 身分別歸屬 / OFD202A / OFDM199 設的身分群組 / BasicOFD_PO / OFD_PO / 兩支共用 PO 各一份 / EC 活動清單 / 有沒有資格看這裡 / D：六張費率與設定表 —— OFDB004 一次建檔批次也在寫 / OFDM193 OFDM194 OFDM196 / 逐支維護 / OFDM213 OFDM214 OFDM215 / 逐支維護 / OFDB004〔OFDB〕 / 六張全當明細一起建 / 兩條寫入路徑 / 卡控完全不同 / E：OFD195A —— COD 原本要同步維護，整段被註解 / OFDM195〔OFD7〕 / 目前唯一寫入者 / OFD195A / 優惠關係人 / CODM009 CODM010 / 只查不寫 跳警示不擋 / 離職不會自動終止 / cod.md 記同一件事
```

*圖:圖 5 跨模組。橘框=本片的維護入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼或共用 PO。A 與 B 兩組與 bms.md 對得上;D 的兩條寫入路徑（畫面與 OFDB004）卡控完全不同，是最容易出事的一組。*

本片 23 張表裡有 14 張被別的模組或別支畫面碰到。五組「借法」完全不同,分開講。

### 8.1 `OFD206` — 主檔在 `OFDM206`,`BMSM001` 當明細(與 `bms.md` 對照)

**兩邊都在寫同一張表,而且寫法不同。**

| 面向 | OFD 側(`OFDM206`) | BMS 側(`BMSM001`) |
|---|---|---|
| 角色 | 主檔持有者,`xTableMapping("OFD206", "OFDM206")` | 明細,`xTableMapping("OFD206", "OFD206")` |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:44` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:158` |
| 寫入前的清理 | 無(靠 `BeforeAdd` 擋重複) | `BeforeAdd` 先 `Delete_OFD206` 整批刪 |
| 清理範圍 | — | `DELETE FROM OFD206 A WHERE A.BF_SRNO = :BF_SRNO AND EXISTS (SELECT 1 FROM OFD204 B WHERE A.CAMPAIGN_CODE = B.CAMPAIGN_CODE AND B.CAMPAIGN_TYPE = 0)`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1859`) |
| 「開戶優惠」的判準 | `OFD204.CAMPAIGN_TYPE = 0`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:70`) | `OFD204.CAMPAIGN_TYPE = 0`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1859`) |

**判準一致,對得上。** 兩邊都用 `OFD204.CAMPAIGN_TYPE = 0` 認定「開戶優惠」,這一點與 `bms.md §4` 記的內容相符;`bms.md §8` 把 `OFD206` 列為「OFD / EC優惠活動 / `BMSM001` 明細」,也與本片一致。

**三處對不上或要補充的:**

| # | 差異 | 說明 |
|---|---|---|
| 1 | **欄數** | `bms.md §2` 的母體表記 `OFD206` **12 欄、四眼「只有 `*DATE`」**;現在跑 `atlas_scan.py --table OFD206` 得到 **21 欄、四眼「有」**,欄位定義來源是 `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd`。OFD 側的 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM206Model.xsd` 也是同樣 21 欄(其中 8 欄是 join 進來的顯示欄,vdb 共 29 欄)。**兩份 xsd 的實體欄位一致,`bms.md` 那個 12 是舊一輪掃描器的數字**(`architecture.md 附錄 D.3` 記過掃描器修過兩輪,`帶四眼欄位` 從 37 修成 158)。建議 `bms.md` 回頭對一次。 |
| 2 | **BMS 載入時只取一筆** | `sb.AppendLine(@" SELECT OFD206.* FROM OFD206,OFD601 WHERE OFD601.BF_SRNO = OFD206.BF_SRNO AND ROWNUM = 1 AND OFD601.BF_NO = " + strBF_NO + ";")`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1129`)——`ROWNUM = 1` 且**不篩 `CAMPAIGN_TYPE`**。另一條載入路徑有篩(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3215-3219`)但也是字串串接。`bms.md` 沒有記到這兩條。 |
| 3 | **刪除只用 `BF_SRNO` 當條件** | `Delete_OFD206` 的 `CAMPAIGN_CODE` 綁定參數那一行**被註解**(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1863`),所以刪的是該受益人**全部**的開戶優惠列,不是某一檔。 |

**#2 + #3 合起來是一條資料流失路徑(〔假設〕,未實測):** 如果一位受益人在 `OFD206` 有兩列以上 `CAMPAIGN_TYPE = 0` 的資料(`OFDM206` 的 `BeforeAdd` 會擋,但 §4.11 說的兩個批次匯入**不會擋**),則 `BMSM001` 載入時只讀到一列,存檔時 `Delete_OFD206` 把兩列都刪掉,再寫回一列 —— **另一列靜默消失**。要確認需要 DB 資料,repo 內無法驗證。列入附錄 E.24。

**BMS 側另外兩處會覆寫 `BF_SRNO`**:`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1398-1402` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1458-1461`,把新產生的 EC 流水號回填到明細列上。OFD 側沒有對應動作。

### 8.2 `OFD204` — 兩個模組共用同一個「活動類型」判準

`OFD204` 的唯一維護入口是 `OFDM204`(§4.9),但它的 `CAMPAIGN_TYPE` 被三個地方讀:

| 讀的人 | 用途 | 錨點 |
|---|---|---|
| `OFDM206` 的 `BeforeAdd` | 只有 `CAMPAIGN_TYPE = 0` 才擋「一人一筆」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-70` |
| `OFDM206` 的主檔 SQL | 帶出 `CAMPAIGN_TYPE` 給畫面顯示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:117` |
| `BMSM001` 的 `Delete_OFD206` | 只刪 `CAMPAIGN_TYPE = 0` 的列 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1856-1859` |

**改 `OFD204.CAMPAIGN_TYPE` 的值域等於同時改 BMS 的行為。** repo 內找不到 `CAMPAIGN_TYPE` 的代碼字典(`CTL014.cs` 沒有這一組),`0` 代表開戶優惠是從程式反推的**推測**。

### 8.3 `OFD197A` — 本片維護,卻是促銷活動對象判定的輸入

這是本片五塊業務線之間唯一的真依賴。共用 PO 判斷「這位受益人 / 這個身分別看得到哪些促銷活動」時,會把 `OFD202A`(`OFDM199` 設的身分群組)join 到 `OFD197A`(`OFDM197` 設的歸屬):

| 共用 PO | 片段 | 錨點 |
|---|---|---|
| `BasicOFD_PO` | `LEFT JOIN OFD197A ON OFD197A.MKT_ID=OFD202A.MKT_ID … AND OFD197A.ID_NO LIKE :ID_NO` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4510-4514` |
| `OFD_PO` | 同樣的 join,另外多一個 `OFD197A.BELONG_DATE <= TO_CHAR(:VALID_DATE,'yyyymmdd')` | `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:127-131` |

**兩份 SQL 的條件不一樣**:`OFD_PO` 那份會比歸屬日期,`BasicOFD_PO` 那份不會。同一個問題兩個答案,呼叫哪一支決定結果。改 `OFDM197` 之前要先確認下游用的是哪一份。

### 8.4 六張費率與設定表 — `OFDB004` 一次建檔批次也在寫

`OFDB004`(主檔 `OFD081A`,即「複製一檔基金的全部設定」)把本片六張表當明細一起建:

| 表 | 本片畫面 | `OFDB004` 的 vdb 名 | 錨點 |
|---|---|---|---|
| `OFD193A` | `OFDM193` | `OFDM193` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:64` |
| `OFD194A` | `OFDM194` | `OFDM194` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:65` |
| `OFD196A` | `OFDM196` | `OFDM196` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:66` |
| `OFD213A` | `OFDM213` | `OFDM213` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:69` |
| `OFD214A` | `OFDM214` | `OFDM214` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:70` |
| `OFD215A` | `OFDM215` | `OFDM215` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:71` |

**兩條寫入路徑的卡控完全不同。** 走 `OFDM193` 進來會被 §4.3 那一整串檢核擋;走 `OFDB004` 進來只有 `OFDB004` 自己的檢核。特別是 A / B 兩塊「群首靠 `WHERE BNG_AMT = 1` 抓」這件事(§4.1):**`OFDB004` 複製出來的資料如果第一階不是從 1 開始,在 `OFDM193` / `OFDM194` / `OFDM196` 上就查不到也改不到**。`OFDB004` 是否保證第一階為 1,要讀 `OFDB004_PO` 的複製邏輯才知道,不在本片範圍。

### 8.5 `OFD195A` — COD 原本要同步維護,整段被註解

`cod.md §4` 已經記過:`CODM009`(員工資料維護)的 `AfterUpdate` 與 `AfterDelete` 裡維護 `OFD195A` 的程式**整塊被 `/* */` 包起來**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:81-248`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:253-274`),只剩「查到有資料就跳 `Warn01` 但不擋」的提示。

**從 OFD7 側確認:`OFD195A` 現在唯一的寫入者就是 `OFDM195`。** 兩邊說法一致。實務後果:員工離職 / 轉非正式時,`OFD195A` 的 `REL_STOP_DATE` **不會自動補**,要人工進 `OFDM195` 改;而 `OFDM195` 那條「一人只能一筆未終止」的檢核又沒在跑(§4.7)——**兩邊的防線同時是空的**。

### 8.6 促銷活動的四張對象表 — EC 與 OFD.Query 直接讀

`OFD201A` `OFD202A` `OFD203A` `OFD687A` 沒有 `_UPD` 分身,由 `OFDM199` 直接寫正式表,而下列三方直接讀:

| 讀的人 | 錨點 |
|---|---|
| `OFDI199`(OFD.Query) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:42-46` |
| EC 專案的 `OFDM199AOracleDao` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:39-43` |
| 共用 PO `BasicOFD_PO`(判活動對象) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4502-4513` |

這是 §4.10 那個「一半立即生效」問題的下游端。

### 8.7 影響面速查

改本片的東西時,要一起看的清單:

| 改什麼 | 要一起看 |
|---|---|
| `OFD206` 的欄位或 PK | `BMSM001`(明細)+ `bms.md §2` 的母體表 |
| `OFD204.CAMPAIGN_TYPE` 的值域 | `OFDM206` 的 `BeforeAdd` + `BMSM001` 的 `Delete_OFD206` |
| `OFD197A` 的 `MKT_ID` / `BELONG_DATE` | `BasicOFD_PO` 與 `OFD_PO` 兩份活動對象 SQL(條件不同) |
| `OFD193A` / `OFD194A` / `OFD196A` / `OFD213A` / `OFD214A` / `OFD215A` 的欄位 | `OFDB004` 的明細宣告 + 各自畫面 |
| `OFD195A` | `CODM009` / `CODM010` 的唯讀檢核(`cod.md §4`) |
| `OFD199A` 系列的欄位 | `OFDI199` + EC 的 `OFDM199AOracleDao` + `BasicOFD_PO` + `OFD_PO` + `OFDM204` + `OFDM206`,**共六處** |
| `OFD201A` / `OFD202A` / `OFD203A` / `OFD687A` | 同上,而且改完立即對外生效 |

## 附錄 A. 資料表總表

### A.1 本片宣告的 23 張實體表

| 表 | 主檔於 | 明細於(本片) | 被誰共用 | 欄位定義 xsd |
|---|---|---|---|---|
| `OFD191` | `OFDM191` | — | — | `OFDM191Model.xsd` 的 `OFDM191` |
| `OFD192` | `OFDM192` | — | OTAB 專案有引用 | `OFDM192Model.xsd` 的 `OFDM192` |
| `OFD193A` | `OFDM193` | — | `OFDB004` 明細、`OFDM199.GetOFD193` 讀、Common | `OFDM193Model.xsd` 的 `OFDM193` |
| `OFD194` | `OFDM194B` | — | `OFDB004` 有引用 | `OFDM194BModel.xsd` 的 `OFDM194B` |
| `OFD194A` | `OFDM194` | — | `OFDB004` 明細、NFD.Report | `OFDM194Model.xsd` 的 `OFDM194` |
| `OFD195A` | `OFDM195` | — | COD 唯讀、RSP、Common | `OFDM195Model.xsd` 的 `OFDM195` |
| `OFD196A` | `OFDM196` | — | `OFDB004` 明細 | `OFDM196Model.xsd` 的 `OFDM196` |
| `OFD197A` | `OFDM197` | — | Common 兩支活動對象 PO、BMS、RSP、OFDB | `OFDM197Model.xsd` 的 `OFDM197` |
| `OFD198` | `OFDM198` | — | — | `OFDM198Model.xsd` 的 `OFDM198` |
| `OFD199A_UPD` | `OFDM199` | — | **無** | `OFDM199Model.xsd` 的 `OFDM199` |
| `OFD200A_UPD` | — | `OFDM199` | **無** | `OFDM199Model.xsd` 的 `OFDM199_Fund` |
| `OFD190A_UPD` | — | `OFDM199` | **無** | `OFDM199Model.xsd` 的 `OFDM199_RSP` |
| `OFD201A` | — | `OFDM199` | `OFDI199`、EC、Common、OFDB | `OFDM199Model.xsd` 的 `OFDM199_Channel` |
| `OFD202A` | — | `OFDM199` | 同上 | `OFDM199Model.xsd` 的 `OFDM199_Mkt` |
| `OFD203A` | — | `OFDM199` | `OFDI199`、EC、Common | `OFDM199Model.xsd` 的 `OFDM199_AGENT` |
| `OFD687A` | — | `OFDM199` | 同上 | `OFDM199Model.xsd` 的 `OFDM199_PROD` |
| `OFD204` | `OFDM204` | — | `OFDM206`、BMS、Common | `OFDM204Model.xsd` 的 `OFDM204` |
| `OFD205` | — | `OFDM204` | — | `OFDM204Model.xsd` 的 `OFD205` |
| `OFD206` | `OFDM206` | — | **`BMSM001` 明細** | 兩份:`OFDM206Model.xsd` 的 `OFDM206` 與 `BMSM001Model.xsd` 的 `OFD206` |
| `OFD207` | — | (唯讀補撈) | — | `OFDM206Model.xsd` 的 `OFD207`;掃描器歸為 dataset |
| `OFD213A` | `OFDM213` | — | `OFDB004` 明細 | `OFDM213Model.xsd` 的 `OFDM213` |
| `OFD214A` | `OFDM214` | — | `OFDB004` 明細、NFD.Report | `OFDM214Model.xsd` 的 `OFDM214` |
| `OFD215A` | `OFDM215` | — | `OFDB004` 明細 | `OFDM215Model.xsd` 的 `OFDM215` |

> ⚠ **「掃描器說欄位 0」不等於沒有定義。** 對 `OFD191` 跑 `atlas_scan.py --table OFD191` 會得到「欄位 0」,原因與 `bms.md §2` 記的一樣:**xsd 的 DataTable 名跟實體表名不同**(`new xTableMapping("OFD191", "OFDM191")`)。本片 23 張表裡有 20 張是這種情形,只有 `OFD205` `OFD206` `OFD207` 三張的 vdb 名與實體表名相同(或另有一份同名定義),掃描器才查得到欄位。要查欄位得照上表最後一欄去對應的 xsd 找。

### A.2 只讀不寫的外部表

`OFD081`(境外基金)、`OFD081A`(境內基金)、`OFD0811A`(基金警語)、`OFD062`(基金公司)、`OFD068A`(銷售機構)、`OFD072A`(推薦人)、`BMS001A`(受益人)、`COD009`(員工)、`OFD027A`(行銷身分別)、`OFD601`(EC 網路戶)、`OFD607A`(EC 權限)、`OFD094A`(保管銀行)、`FSK003`(幣別)、`OFD020V`(銀行分行,用兩次別名 `OFD020V2`)、`OFD604A`(EC 牌告費率)、`OFD199A`(正式促銷活動主檔,被 `OFDM204` / `OFDM206` join)。

`FSK003` `OFD020V` `OFD604A` 三個不在掃描器索引裡(母體沒收),已加進 meta 的 `refcheck-ignore`。

## 附錄 B. SP / Function / Trigger / View

**本片沒有任何自己的 SP、Trigger 或 View。** 23 張表上沒有掛 Trigger(`DB/Trigger/` 13 支裡沒有一支對應),`DB/SP/` 底下也沒有 `OFD19*` / `OFD20*` / `OFD21*` 相關的檔。

用到的 DB 端物件只有一個:

| 物件 | 型別 | 用途 | 呼叫端 | repo 內有原始碼? |
|---|---|---|---|---|
| `F_TA_GETAGENT` | Function(回 table) | `OFDM199` 的銷售機構明細取機構簡稱:`SELECT AGENT_SHNM FROM TABLE(F_TA_GETAGENT()) OFD068A WHERE …` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:329-330` | **無**,已加進 `refcheck-ignore` |

**`_UPD` → 正式表的搬運者不在這張表上,因為 repo 內找不到它**(§4.10)。若它存在,依 `architecture.md 附錄 B` 的說法(`DB/` 只涵蓋 16% 的 SP),很可能是一支沒進版控的 SP。

## 附錄 C. 代碼對照

全部來自 `Dev/Common/Source/MappingCode/TA.MappingCode/`,不是自己翻的。

| 代碼組 | 值 | 意義 | 錨點 |
|---|---|---|---|
| `SHORE_ID` / `FUND_TYPE` | `1` / `2` | 境外基金 / 境內基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FEE_TYPE` | `1` / `2` | 永久費率 / 某期間費率 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:187-197` |
| `RSP_ID` | `Y` / `N` | 可 / 不可作定期定額申購 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277-287` |
| `AFEE_TYPE` | `1` / `2` | 前收 / **後收** | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3533-3544` |
| `PROMT_TYPE` | `1` / `2` / `3` / `4` | EVENT / CAMPAIGN / 壽星優惠 / 優惠券 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:827-838` + `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014_AGI.cs:10-21` |
| `PROMT_ITEM` | `1` / `2` / `3` | 申購 / 定期定額 / 轉申購 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:842-855` |
| `PROMT_SCOPE` | `1` ~ `5` | 所有管道 / 臨櫃 / E/C+IVR / EC / IVR | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:859-881` |
| `CAMPAIGN_OBJ` | `1` ~ `4` | 所有受益人 / 通路 / 身分群族 / 銷售機構 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:885-903` |
| `CAMP_DAY_TYPE` | `1` / `2` / `3` | 優惠日期區間 / 優惠月數 / 優惠次數 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3278-3292` |
| `CAMP_DISC_TYPE` | `1` / `2` / `3` | 優惠折數 / 折扣金額 / 固定優惠費率 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3296-3310` |
| `MKT_SOURCE_CD` | `M` / `C` | 輸入 / 批次轉入 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2586-2596` |
| `REL_TYPE` | `1` / `2` | 員工 / 推薦人 | `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:11-21` |

**兩個查不到字典、只能推測的:**

| 代碼 | 觀察到的值 | 推測 | 依據 |
|---|---|---|---|
| `CAMPAIGN_TYPE` | `0` 與 `> 0` | `0` = 開戶優惠 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-76` 的訊息「每位受益人只能設定一筆開戶優惠」 |
| `STATUS` 的 `'301'` | 批次匯入寫死 | 已覆核新增(`EVAStatusCode.ApproveAdd`) | 三段 SQL 同時填滿 `ENTRYID`/`VERIFYID`/`APPROVEID`;但與 `architecture.md §3` 記的「單字元字面值」不符,**未確認** |

**一個字典與註解打架的地方**:`AFEE_TYPE = "2"` 字典寫「後收」,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:409-410` 的註解寫「混收型」。本文以字典為準,同時把這個差異記在這裡。

## 附錄 D. 掃描母體與覆蓋率

`atlas_scan.py --module OFD` 對單片沒有意義(OFD 有 550 支),所以改成逐支列。

### D.1 15 支畫面的處置

| # | 畫面 | 處置 | 章節 | 深度 |
|---|---|---|---|---|
| 1 | `OFDM191` | 已寫 | §4.1 | 一支一節 |
| 2 | `OFDM192` | 已寫 | §4.2 | 一支一節 |
| 3 | `OFDM193` | 已寫 | §4.3 | **深寫**(境內外機制 + 缺陷) |
| 4 | `OFDM194` | 已寫 | §4.4 | **深寫**(成對比較) |
| 5 | `OFDM194B` | 已寫 | §4.4 | **深寫**(成對比較) |
| 6 | `OFDM196` | 已寫 | §4.5 | **深寫** |
| 7 | `OFDM198` | 已寫 | §4.6 | 一支一節 |
| 8 | `OFDM195` | 已寫 | §4.7 | **深寫**(死碼 + 無呼叫端檢核) |
| 9 | `OFDM197` | 已寫 | §4.8 | **深寫**(匯入 + 編碼) |
| 10 | `OFDM204` | 已寫 | §4.9 | 一支一節 |
| 11 | `OFDM199` | 已寫 | §4.10 | **最深**(`_UPD` 機制) |
| 12 | `OFDM206` | 已寫 | §4.11 | **深寫**(BMS 依賴) |
| 13 | `OFDM213` | 已寫 | §4.12.1 | 群組節 |
| 14 | `OFDM214` | 已寫 | §4.12.2 | 群組節 |
| 15 | `OFDM215` | 已寫 | §4.12.3 | 群組節 |

**15 / 15 = 100%**,沒有「無關」或「停用」需要處置的。

### D.2 表的覆蓋率

| 對象 | 母體 | 本文明確引用 | 覆蓋 |
|---|---|---|---|
| 本片宣告的實體表 | 23 | 23(附錄 A.1 全列) | 100% |
| 外部唯讀表 | 16 | 16(附錄 A.2 全列) | 100% |
| DB 物件 | 1 | 1(附錄 B) | 100% |
| 子對話框 | 14 | 14(§3.1) | 100% |
| 代碼組 | 12 + 2 推測 | 14(附錄 C) | 100% |

### D.3 本文沒做到的事

| 項目 | 原因 |
|---|---|
| `_UPD` → 正式表的搬運程式 | repo 內不存在,需要 DB 連線 |
| `'301'` 是不是 `ApproveAdd` | `EVAStatusCode` 在 DLL 裡,需要反編譯或查 DB |
| `CAMPAIGN_TYPE` 的完整值域 | 沒有代碼字典 |
| `DISC_CODE`(優惠專案)的值域 | 自由輸入,沒有字典也沒有檢核 |
| `LevelGridUtility` / `xMaintainForm` / `BaseEVADaoPO` 的內部行為 | 框架 DLL,無原始碼,從呼叫端反推 |
| `OFDB004` 複製出來的資料第一階是不是從 1 開始 | 不在本片範圍 |

## 附錄 E. 讀本文時要注意的地方

18 + 6 條,依嚴重度排。

### E.1 逐年遞減檢核掛在錯的分支,永遠不會成立 —— 嚴重度 **高**

`OFDM193` 與 `OFDM196` 兩支,寫法一模一樣:

```
if (Convert.ToString(this.uoptFUND_TYPE.Value) == "1")
{
    //境內境金        ← 註解是錯的,"1" 是境外
    … 檢查 ALLOT_FEE_RATE > ALLOT_FEE_RATE1 > ALLOT_FEE_RATE2 …
    this.ValidateErrList.AddError(this.ugrdOFDM193, "手續費率需符合逐年遞減原則，請檢查手續費率!!");
}
```

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-75`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:109-124`。

**為什麼形同虛設:**

| 步驟 | 事實 | 錨點 |
|---|---|---|
| 1 | `"1"` 是境外(`SHORE_ID.OffShore`) | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:298-300`;同檔 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:141-144` 的「預設境內基金」接 `= "2"` |
| 2 | 境外時 `RATE1` / `RATE2` 欄被隱藏 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:599-602` |
| 3 | 境外時 `RATE1` / `RATE2` 格子禁止編輯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:627-636` |
| 4 | 境外時存檔前 `RATE1` / `RATE2` **強制歸零** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:96-101` |
| 5 | 檢核式子是 `(RATE == 0 && RATE1 == 0) \|\| (RATE > RATE1)`。`RATE1` 恆為 0 時,`RATE == 0` 走前半、`RATE > 0` 走後半,**兩邊都成立** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:67-70` |

**影響**:(a) 境外永遠通過;(b) 境內——也就是唯一會用到多階費率的情境——**整段檢核被 `if` 跳過**。訊息「手續費率需符合逐年遞減原則」在任何情況下都不會出現。`OFDM196` 還多兩條跟著陪葬:`SWITCH_FEE_RATE < 0` 與「選取的基金不適用此 幣別代碼」也掛在同一個 `if` 裡(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:112-113`、`:126-132`)。

**對照組**:`OFDM194` 的同一段檢核**沒有包 `if`**,直接跑(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72`)——三支同型畫面,一支對兩支錯。

### E.2 `OFDM197` 匯入的重複檢核查錯 DataTable,永遠不觸發 —— 嚴重度 **高**

`CheckExists` 迭代 `Model.DataEntity.OFDM197`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:204`),但匯入畫面只填 `OFDM197B`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:118-122`),而且開檔前 `VDB.UIView.Clear()` 把兩張都清空(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:107`)。`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM197_Ctl.cs:56-58` 兩張表分別搬,所以 PO 收到的 `OFDM197` 一定是空的,`CheckExists` 恆回 `false`。

**影響**:「該行銷身份別已有資料,是否覆寫資料?」的詢問永遠不跳,直接進 delete + insert。使用者不會知道自己覆寫了什麼。連帶 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:85` 的 `Columns["BF_NAME"]`(`OFDM197B` 根本沒這一欄)那條死路也走不到——**這是唯一讓它不炸的原因**。

### E.3 `OFDM195` 的「一人一筆未終止」檢核三層外殼都在,沒有呼叫端 —— 嚴重度 **高**

PO(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:315`)→ Ctl(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM195_Ctl.cs:109`)→ Pxy(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM195_Pxy.cs:119`)三層都在,UI 的呼叫被註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:155-183`)。

**影響**:同一位員工可以有多筆未終止的優惠關係人資料。配合 §8.5(COD 也不會自動終止),這條業務規則在系統裡**完全沒有守門人**。

### E.4 `FeeTypeValidate` 的 `catch` 不補結果列,例外會被當成通過 —— 嚴重度 **高**

三支各一份,完全相同的程式碼:

```
catch (Exception ex)
{
    CommonExceptionBlocker.HandleBusinessException(ex);
}
return mResult;      ← mResult.Utility.Result 還是空的
```

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:394-398`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:235-239`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:232-236`。

UI 端:`if (View.Util.Result.Rows.Count > 0) return ReturnCode; … return true;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:114-117`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194B.cs:103-106`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:97-100`)——**結果列是空的就當成 `true`(通過)**。

**影響**:資料庫連不上、SQL 語法錯、權限不足,通通變成「檢核通過」。而這支檢核用的又是字串串接的 SQL(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:361-385`),輸入含單引號就會語法錯 → 直接放行。

### E.5 三個批次匯入繞過四眼與伺服端卡控 —— 嚴重度 **高**

| 入口 | 繞過什麼 | 錨點 |
|---|---|---|
| `OFDM197.BatchAdd` | 四眼;`STATUS` 寫死 `'301'`,`ENTRYID`/`VERIFYID`/`APPROVEID` 同人同時 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |
| `OFDM206.BatchAdd` | 四眼 + `BeforeAdd` 的「每位受益人只能設定一筆開戶優惠」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206.BatchAddEC` | 同上,另加寫死條件 `etraflg='Y'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

`OFDM206` 那兩個的後果會傳到 BMS(§8.1 的 #2/#3)。

### E.6 `OFDM206` 刪除確認的判斷方向相反 —— 嚴重度 **高**

```
private void OFDM206_BeforeDeleteButtonClicked(object sender, CancelEventArgs e)
{
    e.Cancel = (DialogWithNoStatusbar.ShowMessage(FunctionDialogStyle.Warn03, "已有使用記錄，是否刪除(Y/N)？") == DialogResult.OK);
}
```

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:214-217`。

按「是」→ `DialogResult.OK` → `e.Cancel = true` → **刪除被取消**;按「否」→ **刪除執行**。同一份 code base 的其他畫面都是反過來寫的(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:427`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:313` 都用 `== DialogResult.No` 才 `e.Cancel = true`)。而且這個提示**無條件跳**,不查 `OFD207` 到底有沒有使用記錄。

### E.7 三支畫面的來源檔不是 UTF-8 —— 嚴重度 **中**

實測(對 `Dev/ATLAS.OFD/Source` 底下這 15 支相關的 `.cs` / `.xsd` 逐檔 `bytes.decode('utf-8')`):

| 畫面 | 非 UTF-8 的檔 |
|---|---|
| `OFDM197` | `UI/UI.OFD/OFDM197.cs`、`UI/UI.OFD/OFDM197.Designer.cs`、`Control/Control.OFD/OFDM197_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM197_Pxy.cs`、`PO/PO.OFD/OFDM197_PO.cs` |
| `OFDM213` | `Control/Control.OFD/OFDM213_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM213_Pxy.cs`、`PO/PO.OFD/OFDM213_PO.cs` |
| `OFDM214` | `Control/Control.OFD/OFDM214_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM214_Pxy.cs`、`PO/PO.OFD/OFDM214_PO.cs` |

`OFDM197` 是整條六層(含 UI);`OFDM213` / `OFDM214` 是 **UI 層 UTF-8、底下三層 Big5**,同一支畫面混兩種編碼。`OFDM197p0` 相關檔反而是 UTF-8。

**影響**:用 UTF-8 編輯器改中文訊息會產生亂碼;`git diff` 看不懂;跨平台工具鏈(本文的掃描與建置就是)必須先偵測編碼。

### E.8 `OFDM213.IsBfExsits` 查一個不存在的欄位 —— 嚴重度 **中**

`SELECT COUNT(1) FROM OFD213A WHERE BF_NO = '…'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:181-183`),但 `OFD213A` 沒有 `BF_NO` 欄(附錄 A.1 / §2.4)。執行會 `ORA-00904`,`catch` 吃掉回 `-1`。目前沒有呼叫端(`OFDM213p0` 不呼叫),所以不會發作;但它掛在 `IOFDM213_PO` 介面上(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:20`),隨時可能被人接起來用。這是從 `OFDM214` / `OFDM215` 複製過來忘了刪的。

### E.9 三胞胎的複製功能三處不一致 —— 嚴重度 **中**

| # | 不一致 | `OFDM213` | `OFDM214` | `OFDM215` |
|---|---|---|---|---|
| 1 | 複製時 `STATUS` | 清成 `string.Empty`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:118`) | **`row.STATUS = row.STATUS;` 自我指派,等於不清**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:149`) | 同 `OFDM214`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:97`) |
| 2 | 一般 `catch` 是否記 log | — | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:228`) | **沒有**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:178-184`) |
| 3 | 解構子是否解除事件訂閱 | **沒有**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:40-43`) | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:38-43`) | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:40-45`) |

#1 的後果:複製出來的列帶著來源的四眼狀態(可能是已覆核),但 `APPROVEID` / `APPROVEDATE` 全被清空 —— **狀態與軌跡不一致**。

### E.10 `OFDM196` 明細 SQL 的日期條件被註解 —— 嚴重度 **中**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182` 被 `//` 掉,而同檔主檔 SQL 的同一行還在(`:108-109`),其他五支同型畫面也都在。查詢日期條件只在主檔生效,點進明細後失效。

### E.11 「永久費率」的日期哨兵值有兩種寫法 —— 嚴重度 **中**

| 畫面 | 費率種類 = 永久 時寫入的起迄日 | 錨點 |
|---|---|---|
| `OFDM191` | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:74-75` |
| `OFDM198` | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:73-74` |
| `OFDM193` 境外 | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:96-97` |
| `OFDM193` 境內 | **`""` / `""`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:106-107` |
| `OFDM194` | **`""` / `""`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:90-91` |
| `OFDM196` 境外 / 境內 | `"00000000"`/`"99999999"` 與 `""`/`""` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:158-172` |
| 舊版(被註解) | `1900/1/1` 與 `9998/12/31` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:88-89` |

三代哨兵值並存,而且 Oracle 會把 `''` 折成 NULL。任何一支 SQL 想用「`BNG_DATE <= :today AND :today <= END_DATE`」去篩永久費率,**對 `''` 那一組會失效**(NULL 比較恆為 UNKNOWN)。同型問題在 `OFDM195.CheckData` 的 `REL_STOP_DATE IS NULL` 上也有(§4.7)。

### E.12 `OFDM199` 一次存檔,七張表兩種生效時機 —— 嚴重度 **中**

見 §4.10.3。三張 `_UPD` 等生效,四張立即寫正式表且立即被 EC 讀到。**四眼只護住一半。**

### E.13 `OFDM199` 定額優惠「迄日」檢核方向存疑 —— 嚴重度 **中**(標「假設」)

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:236` 與 `:240` 兩個條件都是 `活動日期 > 該列日期`,只換了欄位名:

```
if ((this.udatCAMPAIGN_BNG_DATE.DateTime.Date > Convert.ToDateTime(Row.Cells["BNG_DATE"].Value).Date) && …) RspBNG++;
if ((this.udatCAMPAIGN_END_DATE.DateTime.Date > Convert.ToDateTime(Row.Cells["END_DATE"].Value).Date) && …) RspEND++;
```

對「起日」是對的;對「迄日」意思變成「定額優惠不能比活動早結束」,允許優惠期超出活動期。業務上比較合理的應該是 `<`。需求文件不在 repo,**標假設,不改判定**。

### E.14 Oracle 三值邏輯:`<>` 遇 NULL —— 嚴重度 **低**(目前不發作)

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:69` 的 `AND A.CAMPAIGN_CODE <> :CAMPAIGN_CODE`。`CAMPAIGN_CODE` 是 `OFD206` PK 的一部分,理論上不為 NULL,所以目前不會漏抓。但這是 CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過的同型寫法,**改 schema 或改成 outer join 時要一起看**。本片其餘的 `<>` 比對只出現在被註解的程式裡。

### E.15 `OFD206.BF_SRNO` 在匯入流程裡裝的是戶號 —— 嚴重度 **中**(易誤判)

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106` 把 CSV 的戶號塞進 `row.BF_SRNO`,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:49` 把欄位標題改成「戶號」,PO 端再靠 `CROSS JOIN OFD601 … AND B.BF_NO = :BF_NO` 換回真的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:187-196`)。

連帶一個真的錯:`CheckExists` 的錯誤訊息是「此優惠活動已存在戶號:」,後面接的卻是查回來的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:155-157`、`:171`)——**標籤說戶號,值是 EC 流水號**。

### E.16 `OFDM206_PO.CheckData` 是一個可執行任意 SQL 的伺服端入口 —— 嚴重度 **高**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:221-269`:從 `Model.Utility.Parameters` 收一整串 SQL 與一個分隔字元,切開後逐段 `ExecuteNonQuery`,連 `Commit` 與否都由參數存不存在決定(`:234`、`:256-259`)。

repo 內沒有 UI 呼叫端,但 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM206_Ctl.cs:200-205` 與 `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM206_Pxy.cs:48-62` 都在,而 Remoting 邊界就在 UI → FormProxy(`architecture.md §8`)。**這是一個對外開放、沒有任何白名單的 SQL 執行入口。**

### E.17 字串串接進 SQL —— 嚴重度 **高**(範圍廣)

本片 15 支裡有 9 支在組 SQL 時用字串串接,不綁參數。彙整:

| 畫面 | 位置 | 串進去的東西 |
|---|---|---|
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:361-385` | `FUND_ID` `CRNCY_CD` `BF_NO` `FEE_TYPE` |
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:418-436` | `string.Format` 拼 `BF_NO` 與 `FUND_ID` |
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:306`、`:311` | `DataTable.Select()` 的過濾字串 |
| `OFDM194B` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:202-226` | 同 `OFDM194` |
| `OFDM195` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:188-278` | 六個查詢條件 |
| `OFDM195` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:339-394` | 四個查詢條件 |
| `OFDM197` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:134-175` | `MKT_ID` `ID_NO` `BF_NO`,含 `LIKE` |
| `OFDM197` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:200` | `string.Format` 拼 `MKT_ID` |
| `OFDM198` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:203-221` | `FUND_ID` `DISC_CODE` `BF_NO` `FEE_TYPE` |
| `OFDM199` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:500-513` | 自寫的 `AddParam`,全部值直接串 |
| `OFDM206` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:146-148` | `string.Join(" OR ", … string.Format("BF_NO = {0}", r.BF_SRNO))` |
| `OFDM213` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:73`、`:88`、`:148`、`:183` | `FUND_ID` / `BF_NO` |
| `OFDM214` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:62`、`:93`、`:120`、`:176`、`:292` | `FUND_ID` / `BF_NO`,**其中 `:292` 是把整句子查詢串進 `IN ( )`** |
| `OFDM215` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:74`、`:124`、`:211`、`:238`、`:310` | 同上 |

對照 `architecture.md §4`:框架的 `EVAStringHelper.AddParam` 是有綁參數的,這些是繞過它自己手寫的部分。

### E.18 `catch` 內第一行就 `tran.Rollback()`,原始例外可能被蓋掉 —— 嚴重度 **中**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:276-282`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:211-217`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:318-324`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:332-338`:`tran` 宣告成 `null`,若例外發生在 `BeginTransaction()` 之前或之中,`catch` 的 `tran.Rollback()` 會丟 `NullReferenceException`,真正的錯誤訊息就消失了。

### E.19 死碼比例 —— 嚴重度 **中**

| 檔 | 總行數 | 註解掉的區塊 | 佔比 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs` | 1,724 | `:506-1722` | **71%** |
| `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM214_Ctl.cs` | 1,040 | `:313-1038` | **70%** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` | 1,443 | `:539-583` + `:586-857` + `:861-1441` | **62%** |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs` | 152 | `:45-148` | 68%(**而且整個檔不在 csproj**) |

`architecture.md 附錄 D.3` 已經提醒過「對這個 repo 做靜態統計,第一件事是剝註解」。本片是那句話的放大版。

### E.20 `OFDM197p0` 匯入的兩個靜默行為 —— 嚴重度 **中**

| # | 行為 | 錨點 |
|---|---|---|
| 1 | 覆寫確認後的**第二次** `BatchAdd` 回傳值沒被檢查,下一行無條件顯示「複製成功」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:88-92` |
| 2 | CSV 讀到空行就 `break`,後面的戶號全部靜默丟掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |

### E.21 `Result[0]` 未檢查 `Count` 就取用 —— 嚴重度 **低**

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:95`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:79`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p1.cs:69`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213p0.cs:94`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:113`:`else` 分支直接 `vdb.Util.Result[0].ReturnMessage`。PO 的每一條路徑目前都會補結果列,所以不發作;E.4 那種「不補結果列」的寫法一旦出現在這些 PO 上就會變成 `IndexOutOfRangeException`。

### E.22 寫死常數彙整 —— 嚴重度 **中**

| 常數 | 位置 | 意義 |
|---|---|---|
| `BNG_AMT = 1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:107`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:100`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:103`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:103`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:101` | 群組第一列 |
| `BNG_YEAR = 1900` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82` | 同上 |
| `'Atlas'` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:572` | 境內基金公司代碼〔客戶特定〕 |
| `'ALL FUNDS'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:281`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:301` | 「所有基金」的魔術字串 |
| `'C'` / `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:246` | `SOURCE_CD` 批次轉入 / 已覆核 |
| `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185`、`:298` | 已覆核 |
| `etraflg='Y'` + `trim(openday) is not null` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:300-301` | EC 已開戶〔客戶特定〕 |
| `1m` / `999999999999m` / `1900m` / `9999m` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:210`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:166` | 階梯上下界 |

### E.23 `OFD687A` 的欄名拼錯成 `COMPAIGN_CODE` —— 嚴重度 **低**(已被程式繞過)

xsd 宣告的是 `COMPAIGN_CODE`(C-O-M),與其他六張表的 `CAMPAIGN_CODE` 不同。`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494` 寫了一個 `if` 特例把欄名換掉。**這是 DB 欄名的錯字,改不得,只能一直帶著**;任何新寫的 SQL 碰到 `OFD687A` 都要記得拼錯的那個。

### E.24 BMS 側 `OFD206` 的 `ROWNUM = 1` 配上整批 `DELETE` —— 嚴重度 **中**(標「假設」)

見 §8.1。載入只取一列(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1129`),刪除刪全部(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1863`,`CAMPAIGN_CODE` 的條件被註解)。只要 `OFD206` 上有同一位受益人的兩列開戶優惠(批次匯入辦得到,§4.11),存 `BMSM001` 就會少一列。**未實測,需要 DB 資料驗證。**

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD7` 底下 15 支 M 畫面、23 張實體表、24 條缺陷 |

由 build_doc.py v2.0.0 於 2026-09-15 11:53 產生 · 標題 100 · 圖 5 · 表格 68 · 程式錨點 505 · § 連結 66 · 引用檢查：畫面 24（缺 0） · Table 40（缺 0） · 結果集 18（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofd8.md
============================================================

# ATLAS OFD8 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這一片最反直覺的三件事)、§4.3(`OFDM221A` 與 `OFDM231A` 的分工)、§8(跨模組)、附錄 E(踩雷)。

> ⚠ **範圍**:OFD 模組全庫 550 支畫面,本文**只寫 `DataEntity.OFD8` 這一片的 24 支 M 畫面**。同一張表若另有主檔畫面落在其他片(例如 `OFD724` 的 `OFDM723` / `OFDM724`),本文只從這 24 支的角度描述,並在 §8 指路。 ⚠ **本模組的業務意義**(§0)由表名、欄位 `msdata:Caption` 與程式註解**推測**,待選單表 / 對照表回填。 ⚠ **〔客戶特定〕**:機構代碼、境內外識別碼 `'2'`、券商代碼、銀行代碼為本站台的值。 ⚠ **〔共用〕**:標記的表同時服務 BBS / BMS / RSP / SDM / NFD 與 OFD 其他片(見 §8),改動要一起看。

## 0. 系統邊界與角色

### 0.1 這 24 支管什麼(推測)

24 支全部是 **M(維護)** 型別,全部落在 `Dev/ATLAS.OFD/` 這一個專案,六層檔名完全照鐵律(`architecture.md §2`)。 entity 兩層集中在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/` 與 `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/` —— **`OFD8` 是 entity 專案的分片編號,不是模組碼**;UI / Ctl / PO 三層仍在同一個 `*.OFD` 專案裡,沒有分片。所以「第 8 片」是 entity 的分卷,不是業務上的分群 —— 這一點會影響你找檔案的直覺,先記住。

把 24 支依主檔的業務語意歸類,可以分成**六條業務線**(全部標推測):

| 業務線 | 畫面 | 主檔 | 一句話 |
|---|---|---|---|
| ① 境內基金申購 / 買回交易主線 | `OFDM221A` `OFDM231A` `OFDM242` | `OFD220A` `OFD251A` | 開申購書、開買回書、投資組合契約贖回 |
| ② 交易的周邊登錄 | `OFDM243A` `OFDM271` `OFDM337` `OFDM270` | `OFD243A` `OFD724` `OFD337A` `OFD270A` | 券商配單、缺件到件、退件、退郵戶 |
| ③ 基金費率與參數 | `OFDM091` `OFDM233` `OFDM285` `OFDM321` | `OFD091A` `OFD260A` `OFD290A` `OFD321` | 遞延手續費率、短線交易費率、匯費、銷售額度 |
| ④ 每日行情與彙總 | `OFDM300` `OFDM301` `OFDM302` `OFDM297` `OFDM220` `OFDM232` | `OFD300` `OFD301` `OFD302A` `OFD297A` `OFD232A` `OFD259A` | 匯率、交叉匯率、淨值、臨時放假、申購/買回銷售機構彙總 |
| ⑤ 配息作業 | `OFDM281` `OFDM284` `OFDM286` | `OFD281A` `OFD286A` `OFD291` | 配息設定、受益人支付方式、受益人配息期間 |
| ⑥ 檔案格式與雜項客戶設定 | `OFDM264` `OFDM331` `OFDM344` `OFDM361` | `OFD264A` `OFD331` `OFD344` (無) | 付款媒體檔格式、客訴、資料保密設定、未完成的空殼 |

**分片不等於分業務**:同一條業務線的畫面散在不同 `OFD` 片(例如買回主檔 `OFD251A` 的批次 `OFDB321`–`OFDB331` 都不在本片), 反過來本片內部六條線之間的程式呼叫也很少 —— 幾乎全靠表相連。這與 DSM 的情形一致(`dsm.md §1`)。

### 0.2 這一片最反直覺的三件事

**(1) 「覆核才生效」在這一片完全不成立。** `OFDM221A` 與 `OFDM231A` 的 `AfterVerify` / `AfterApprove` 主體**只有一行跳號紀錄,零業務 SQL** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2701-2717`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3975-3989`)。真正的跨表副作用 —— 更新過帳控制檔 `OFD303A`、櫃台控制檔 `CTL012` / `CTL022`、回寫申購明細 `OFD221A` 的贖回中單位數 —— 全部掛在 `AfterAdd` / `AfterUpdate` / `BeforeAdd` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:231-303`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2200-2236`)。 **輸入按下去,帳上就動了**;四眼只是軌跡。這正是 `architecture.md §3` 那條「不能假設覆核前資料還沒動」的第三個實證。

**(2) 六支畫面掛在已經跑不動的舊世代基底上。** `OFDM242` `OFDM284` `OFDM285` 繼承 `MultiRowEVAPO`,`OFDM321` `OFDM331` `OFDM344` 繼承 `BasicEVAPO` (`OFDM361` 的 PO 也是 `BasicEVAPO`,但整個類別是空的)。這兩支基底的 `dbTA` / `dbPTPF` 建構子賦值**整段被註解** (`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:167-175`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175`), 而 `Add` 第一行就是 `cn = dbTA.CreateConnection()`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`)。佐證:這六支的 SQL 裡還留著 SQL Server 的方括號識別字 `[OFD321]` / `[BMS001]`,`OFDM242` 更是整段 T-SQL 批次(`DECLARE @x` / `@@FETCH_STATUS`)。 **假設**:這批畫面在 SQL Server → Oracle 遷移時被放著沒動,現況不可執行。依據見附錄 E-1;要推翻只需在現場按一次新增。

**(3) 掃描器報的主檔不一定是真主檔。** `OFDM271` 宣告 `MasterTable = OFD724`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32`), 但**整支程式只有這一行提到 `OFD724`** —— 它實際維護的是缺件檔 `OFD272A`(§4.8)。 `OFDM361` 則是連 `MasterTable` 都沒宣告,因為 Ctl / PO 是空類別(§4.12)。

### 0.3 不管什麼

| 不在這 24 支裡 | 由誰管 |
|---|---|
| 申購 / 買回的**結帳、過帳、對帳批次** | `OFDB302` `OFDB304` `OFDB306` `OFDB310` `OFDB321`–`OFDB331`(OFD 其他片) |
| 受益人基本資料、受益人異動 | BMS 模組(`bms.md`);本片只 join `BMS001` 唯讀 |
| 受益憑證的換發 / 掛失 / 質設 / 轉讓 | BBS 模組(`bbs.md`);轉讓會反過來寫本片的 `OFD220A`(§8.1) |
| 定期定額(小額契約)本身 | RSP 模組;只在缺件檔 `OFD272A` 上交會(§8.2) |
| 報表與查詢 | 本片一支都沒有(§5 §6 §7) |
| 收益分配的**計算與發放批次** | `OFDB281` 等;本片只設定參數(`OFDM281`)與受益人選項(`OFDM284` `OFDM286`) |

### 0.4 使用角色

程式裡沒有角色表,只能從四眼欄位與畫面行為反推,全部標**推測**:

| 角色 | 做什麼 | 依據 |
|---|---|---|
| 交易輸入人員 | 開申購書 / 買回書、登錄缺件與退件 | `ENTRYID` 由 `EVAType.Add` 寫入(`architecture.md §3`) |
| 覆核人員(兩眼) | 驗證 + 覆核 | `VERIFYID` / `APPROVEID`;本片除 `OFDM271` 外全部有四眼 13 欄 |
| 基金 / 商品管理 | 維護費率、額度、匯率、淨值 | ③ ④ 兩條線的畫面沒有交易欄位,只有參數 |
| 客服 | 客訴 `OFDM331`、退郵 `OFDM270`、保密設定 `OFDM344` | 欄位帶 `COMPLAIN_*` / `REJ_*` / `QT_RSN` |

### 0.5 全域開關

沒有集中式開關。實際會整片改變行為的三個東西:

| 開關 | 在哪 | 影響 |
|---|---|---|
| 過帳控制檔 `OFD303A` 的 `ALLOT_CTL_CODE` / `REDEM_CTL_CODE` | 由 `OFDM221A` `OFDM231A` `OFDM220` `OFDM232` 四支一起寫 | 控制某基金某控制日的申購 / 買回是否已結轉;結轉後多數畫面禁止刪改 |
| 櫃台關帳 `CTL022` | `OFDM221A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1580`)、`OFDM231A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2522`) | 關帳後不可再建檔 |
| 境內外識別碼 `SHORE_ID = '2'` | `OFDM221A` 寫死(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:924`) | 這一片的申購缺件只看境內基金〔客戶特定〕 |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD8 全景:交易主線、周邊登錄、費率參數、行情彙總、配息、檔案格式六條線
圖中文字:① 交易主線:本片四成程式量在這三支,而且「輸入當下帳就動了」 / OFDM221A / 申購 主檔 OFD220A / OFDM231A / 買回/轉換 主檔 OFD251A / OFDM242 / 投資組合贖回 舊世代 / OFD303A CTL012 CTL022 / 過帳與櫃台控制檔 手寫SQL / ② 交易的周邊登錄:缺件、退件、退郵、券商配單 / OFDM271 / 缺件到件 直接UPDATE / OFDM337 / 退件 主檔 OFD337A / OFDM270 / 退郵戶 主檔 OFD270A / OFDM243A / 券商配單 主檔 OFD243A / ③ 基金費率與參數:被 ① 讀去計費,但額度只警示不擋 / OFDM091 / CDSC費率 OFD091A/092A / OFDM233 / 短線交易費率 OFD260A / OFDM285 / 基金匯費 OFD290A / OFDM321 / 銷售額度 舊世代 / ④ 每日行情與彙總:全庫金額計算的基礎,卡控卻最少 / OFDM300 / 幣別匯率 OFD300 / OFDM301 / 交叉匯率 OFD301 / OFDM302 / 基金淨值 OFD302A / OFDM297 / 臨時放假 OFD297A / OFDM220 OFDM232 / 申購/買回彙總 / ⑤ 配息作業:只設定參數,計算在 OFDB281 / OFDM281 / 配息設定 三張表 / OFDM284 / 支付方式 舊世代 / OFDM286 / 配息期間 OFD291 / OFDB281〔別片〕 / 配息計算批次 / ⑥ 檔案格式與雜項:含一支從未接上資料庫的空殼 / OFDM264 / 付款媒體檔格式 三張表 / OFDM331 / 客訴 舊世代 四張明細 / OFDM344 / 資料保密設定 舊世代 / OFDM361 / 三層空類別 無主明細
```

*圖:圖 1 OFD8 全景。橘框=值得先讀的主角;白框=一般維護畫面;橘虛框=舊世代基底或有風險的做法;灰虛框=別片的畫面;黑框=不在掃描母體的控制檔。六條線之間幾乎沒有程式呼叫,全靠表相連——尤其 ① 的三支在輸入當下就寫控制檔,四眼只留軌跡。*

### 1.2 資料表關係

圖 2 畫的是 24 支畫面的主明細配對,以及 `OFDM221A` / `OFDM231A` 共用的五張表 (`OFD136A` `OFD220A` `OFD221A` `OFD243A` `OFD272A`)。三個要點:

1. **主檔與明細不是一對一的樹。** `OFD220A` 在 `OFDM221A` 是主檔,在 `OFDM231A` 卻是明細; `OFD251A` 在 `OFDM231A` / `OFDM242` 都是主檔,兩支都會建它。

2. **本片有兩張「沒有任何畫面是它主檔」的表**:`OFD272A`(缺件)與 `OFD136A`(交易指示代理人)。它們永遠以明細身分被寫(§2.4、§8.2)。

3. **實體表名與 vdb 別名常常不同名。** `OFD251A` 在 `OFDM231A` 的 vdb 名是 `OFDM231A_Master`, 在 `OFDM242` 是 `OFD251A`。查 xsd 要認 vdb 名,查 SQL 要認實體表名(`architecture.md §5`)。

### 1.3 主要維護畫面的四眼與卡控順序

圖 3 拆的是 `OFDM221A` / `OFDM231A` 兩大支的卡控分層。順序固定四層:

| 層 | 誰 | 這一片的實況 |
|---|---|---|
| ① 欄位驗證 | `validatorManager1.DataValidate()` | 24 支全部有,錯誤塞 `ValidateErrList` |
| ② 畫面業務檢核 | UI 的 `DoValidate()` / `Chk*()` | 卡控幾乎全在這層;`OFDM221A` 一支就有 8 個 `Chk*` |
| ③ 伺服端檢核 | PO 的 `Check*<T>()` 公開方法 | **不是 EVA 掛點**,是 UI 主動呼叫的 RPC;繞過 UI 就完全不會跑 |
| ④ EVA 掛點 | `BeforeAdd` / `AfterUpdate` … | 這一片拿來**寫跨表副作用**,不是拿來擋 |

**最重要的一句**:③ 的 `Check*` 方法(例如 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-2646` 共 12 支) 雖然在伺服端執行,但它是 UI 主動叫的。真正的「第二道防線」(`BeforeAdd` 內部否決)在這一片**只有取號與副作用,沒有業務否決**。所以 §4 各節卡控總表裡標「阻擋」的,絕大多數是 UI 層阻擋。

### 1.4 批次 / 報表資料流

**本片無 B 與 R 畫面**(§6 §7)。但這 24 支是批次的上游,關係如下:

| 本片寫什麼 | 下游批次讀什麼 |
|---|---|
| `OFDM221A` 寫 `OFD220A` / `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDB310` 結帳與過帳 |
| `OFDM231A` / `OFDM242` 寫 `OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` | `OFDB321`–`OFDB331` 買回結帳、付款 |
| `OFDM302` 寫淨值 `OFD302A`、`OFDM300` / `OFDM301` 寫匯率 | 幾乎所有金額計算 |
| `OFDM281` 寫配息參數 `OFD281A` | `OFDB281` 配息計算 |
| `OFDM264` 寫媒體檔格式 `OFD264A` / `OFD265A` / `OFD266A` | 付款媒體檔產檔程式 |

### 1.5 一日作業泳道

依欄位語意推測的一天(**推測**,程式內沒有排程表):

| 時段 | 誰 | 做什麼 | 畫面 |
|---|---|---|---|
| 開盤前 | 商品管理 | 建當日匯率、交叉匯率;必要時設臨時放假 | `OFDM300` `OFDM301` `OFDM297` |
| 營業中 | 交易輸入 | 收件 → 開申購書 / 買回書 → 缺件登錄 | `OFDM221A` `OFDM231A` `OFDM242` `OFDM271` |
| 營業中 | 覆核 | 驗證 + 覆核(但帳已經動了,見 §0.2) | 同上 |
| 收盤後 | 商品管理 | 建當日淨值 | `OFDM302` |
| 收盤後 | 代銷組 | 建銷售機構申購 / 買回彙總 | `OFDM220` `OFDM232` |
| 隔日 | 客服 | 退件 / 退郵 / 客訴後續 | `OFDM337` `OFDM270` `OFDM331` |

## 2. 資料模型

```text
[圖] OFD8 四十五張表的主明細配對,以及 OFDM221A 與 OFDM231A 共用的五張表
圖中文字:申購側:OFDM221A 是 OFD220A 的主檔,外加六張明細 / OFD220A〔共用〕 / 申購書 PK ALLOT_NO / OFD221A〔共用〕 / + ALLOT_SRNO 125欄 / OFD234A OFD235A / 支票/匯款 無主檔畫面 / OFD220A_AGENT / 意定代理人 PK同主檔 / 買回側:OFDM231A 是 OFD251A 的主檔,外加九張明細 / OFD251A / 買回書 PK REDEM_NO / OFD252A OFD253A / 付款 / 轉換明細 / OFD254A OFD258A / 指定沖銷 / 憑證明細 / OFD251A_AGENT / vdb名叫 OFD231A_AGENT / 兩大支共用的五張表——本篇最需要記住的一列 / OFD136A / 交易指示代理人 無主檔 / OFD220A / 221A主檔 / 231A明細 / OFD221A / 兩支都寫 RDMING_UNIT / OFD243A / 主檔在 OFDM243A / OFD272A / 缺件 無主檔 / 費率與參數:兩組結構相同的主明細 / OFD091A / OFD092A / CDSC 主檔+區間 / OFD260A / OFD261A / 短線費率 主檔+區間 / OFD321 / OFD322 / 額度 主檔+通路明細 / OFD281A 287A 288A / 配息 主檔+兩明細 / 單表畫面:七張沒有明細的表 / OFD232A OFD259A / 申購/買回彙總 / OFD300 OFD301 / 匯率/交叉匯率 / OFD302A / 基金淨值 / OFD286A OFD290A / 支付方式/匯費 / OFD291 OFD344 / 配息期間/保密 / 外部唯讀或手寫 SQL(不在 xTableMapping,改欄位沒有 xsd 提醒) / OFD303A OFD304A / 過帳控制檔 / CTL012 CTL022 / 櫃台/代扣款控制 / OFD130A OFD131A / 匯款授權書 / OFD721 OFD039A / 憑證餘額/缺件代碼 / BMS001 / 受益人 唯讀
```

*圖:圖 2 資料模型。橘框=主檔或兩大支共用的表;白框=一般明細與單表;灰虛框=沒有主檔畫面、被別的模組共同寫入;黑框=不在掃描母體、只靠手寫 SQL 觸碰。中間那一排五張是本篇的重點:OFD220A 在一支是主檔、在另一支是明細,OFD272A 則誰都不是它的主檔。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

24 支畫面一共宣告 **45 張實體表**(去重),分佈如下。「vdb 名」是 `xTableMapping` 的第二個參數, 也就是 xsd 裡的 DataTable 名 —— **兩者常常不同名,查 xsd 要用 vdb 名**。

| 畫面 | 主檔(實體表 / vdb 名) | 明細(實體表 → vdb 名) | 錨點 |
|---|---|---|---|
| `OFDM091` | `OFD091A` / `OFDM091_Master` | `OFD092A` → `OFDM091_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091_PO.cs:39-40` |
| `OFDM220` | `OFD232A` / `OFDM220` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:49` |
| `OFDM221A` | `OFD220A` / `OFDM221A` | `OFD221A` → `OFDM221A_Detail`;`OFD272A` → `OFD272`;`OFD234A` → `OFD234`;`OFD235A` → `OFD235`;`OFD243A` → `OFD243`;`OFD220A_AGENT`;`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-76` |
| `OFDM231A` | `OFD251A` / `OFDM231A_Master` | `OFD252A` → `OFDM231A_Redem`;`OFD253A` → `OFDM231A_Switch`;`OFD272A` → `OFD272`;`OFD254A` → `OFDM231A_Offset`;`OFD258A` → `OFDM231A_CerData`;`OFD220A` → `OFDM231A_Allot`;`OFD251A_AGENT` → `OFD231A_AGENT`;`OFD221A` → `OFDM231A_AllotDetail`;`OFD243A` → `OFD243`;`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70-82` |
| `OFDM232` | `OFD259A` / `OFDM232` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:50` |
| `OFDM233` | `OFD260A` / `OFDM233_Master` | `OFD261A` → `OFDM233_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:43-44` |
| `OFDM242` | **三個主檔**:`OFD251A` `OFD252A` `OFD254A`(多筆型) | —(`MultiRowEVAPO` 沒有明細概念) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:33-35` |
| `OFDM243A` | `OFD243A` / `OFDM243A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:42` |
| `OFDM264` | `OFD264A` / `OFDM264_Master` | `OFD266A` → `OFDM264_FileRule`;`OFD265A` → `OFDM264_Field` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:35-37` |
| `OFDM270` | `OFD270A` / `OFDM270` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM270_PO.cs:44` |
| `OFDM271` | `OFD724` / `OFDM271`(**名義上**,見 §4.8) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32` |
| `OFDM281` | `OFD281A` / `OFDM281` | `OFD287A` → `OFDM281_Detail`;`OFD288A` → `OFDM281_Rate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:43-49` |
| `OFDM284` | `OFD286A` / `OFDM284`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:38` |
| `OFDM285` | `OFD290A` / `OFDM285`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM285_PO.cs:20` |
| `OFDM286` | `OFD291` / `OFDM286`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM286_PO.cs:35` |
| `OFDM297` | `OFD297A` / `OFDM297`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM297_PO.cs:39` |
| `OFDM300` | `OFD300` / `OFDM300`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM300_PO.cs:41` |
| `OFDM301` | `OFD301` / `OFDM301`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM301_PO.cs:41` |
| `OFDM302` | `OFD302A` / `OFDM302`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| `OFDM321` | `OFD321` / `OFDM321` | `OFD322` → `OFDM321_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:30-31` |
| `OFDM331` | `OFD331` / `OFDM331` | `OFD332` → `OFDM331_Complain`;`OFD333` → `OFDM331_Complain_K`;`OFD334` → `OFDM331_Solve`;`OFD335` → `OFDM331_Solve_K` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:32-37` |
| `OFDM337` | `OFD337A` / `OFDM337` | `OFD346A` → `OFDM337_REJ_ITEM` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:46-47` |
| `OFDM344` | `OFD344` / `OFDM344` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:31` |
| `OFDM361` | **未宣告**(PO 是空類別) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10` |

三個要留意的地方:

1. **`OFDM331` 的 `_K` 後綴語意是反的。** `OFDM331_Complain`(`OFD332`)存的是**客訴代碼**、`OFDM331_Complain_K`(`OFD333`)存的是**客訴內容文字**; 反過來 `OFDM331_Solve`(`OFD334`)存**處理說明文字**、`OFDM331_Solve_K`(`OFD335`)存**處理種類代碼**。同一個 `_K` 在兩組裡分別代表「文字」與「代碼」—— 命名沒有一致規則,別靠後綴猜。

2. **`OFDM242` 的 xsd DataTable 全部叫 `OFDM643` 系列。** `OFDM242Model.xsd` 裡是 `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`,而全庫**沒有 `OFDM643` 這支畫面** (`atlas_scan.py --screen OFDM643` 回「找不到畫面」)。三層一共 56 處引用這個名字 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM242_Ctl.cs:56`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:200`)。 **用 `OFDM242` 當關鍵字 grep 會漏掉它真正的資料表。**

3. **`OFDM221A` 與 `OFDM231A` 共用五張明細表**:`OFD136A` `OFD220A` `OFD221A` `OFD243A` `OFD272A`。這五張的 vdb 名在兩支之間有的相同(`OFD272` `OFD243` `OFD136A`)、有的不同(`OFD220A` 在後者叫 `OFDM231A_Allot`)。細節見 §4.3。

### 2.2 主鍵與四眼欄位

從各 `Model.xsd` 的 `msdata:PrimaryKey="true"` 宣告抄出來(`architecture.md §5`)。「四眼欄位」指 `STATUS` / `CREATEID` / `UPDATEID` / `ENTRYID` / `VERIFYID` / `APPROVEID` / `REJECTID` / `DATAFLAG` 這 8 個檢查欄 (完整 13 欄見 `architecture.md §3`)。

| 實體表 | vdb 名 | 主鍵 | 四眼欄位 | 欄數 |
|---|---|---|---|---|
| `OFD091A` | `OFDM091_Master` | `FUND_ID` | 有 | 18 |
| `OFD092A` | `OFDM091_Detail` | `FUND_ID` + `BNG_DAY` | 有 | 19 |
| `OFD232A` | `OFDM220` | `FUND_ID` + `AGENT_ID` + `AGENT_CODE` + `ALLOT_DATE` | 有 | 48 |
| `OFD220A` | `OFDM221A` | `ALLOT_NO` | 有 | 77 |
| `OFD221A` | `OFDM221A_Detail` | `ALLOT_NO` + `ALLOT_SRNO` | 有 | 125 |
| `OFD234A` | `OFD234` | `ALLOT_NO` + `ALLOT_SRNO` + `CHECK_NO` | 有 | 21 |
| `OFD235A` | `OFD235` | `ALLOT_NO` + `ALLOT_SRNO` + `DATA_SEQ` | 有 | 22 |
| `OFD243A` | `OFD243` | `FUND_ID` + `ALLOT_NO` + `TRAN_DATE` + `STK_BRK` | 有 | 34 |
| `OFD272A` | `OFD272` | `SHORE_ID` + `ORG_COPY_CD` + `TRN_NO` + `TRN_CD` | 有 | 24 |
| `OFD220A_AGENT` | `OFD220A_AGENT` | `ALLOT_NO` | 有 | 17 |
| `OFD136A` | `OFD136A` | `TRADE_NO` + `TRADE_TYPE` | 有 | 19 |
| `OFD251A` | `OFDM231A_Master` | `REDEM_NO` | 有 | 93 |
| `OFD252A` | `OFDM231A_Redem` | `REDEM_NO` + `REDEM_SRNO` | 有 | 71 |
| `OFD253A` | `OFDM231A_Switch` | `REDEM_NO` + `REDEM_SRNO` | 有 | 92 |
| `OFD254A` | `OFDM231A_Offset` | `REDEM_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | 44 |
| `OFD258A` | `OFDM231A_CerData` | `REDEM_NO` + `BF_CER_ISSUE_CODE` + `BF_CER_NO` | 有 | 35 |
| `OFD251A_AGENT` | `OFD231A_AGENT` | `REDEM_NO` | 有 | 17 |
| `OFD259A` | `OFDM232` | `FUND_ID` + `AGENT_ID` + `AGENT_CODE` + `REDEM_DATE` | 有 | 41 |
| `OFD260A` | `OFDM233_Master` | `FUND_ID` | 有 | 23 |
| `OFD261A` | `OFDM233_Detail` | `FUND_ID` + `BNG_DAY` | 有 | 23 |
| `OFD264A` | `OFDM264_Master` | `PAY_BANK` + `FILE_FORMAT` + `FILE_ID` | 有 | 25 |
| `OFD266A` | `OFDM264_FileRule` | 上列 + `DATA_SEQ` | 有 | 22 |
| `OFD265A` | `OFDM264_Field` | 上列 + `DATA_SEQ` | 有 | 29 |
| `OFD270A` | `OFDM270` | `REJ_NO` | 有 | 43 |
| `OFD281A` | `OFDM281` | `FUND_ID` + `YEARS` + `ISSUE_CODE` | 有 | 37 |
| `OFD287A` | `OFDM281_Detail` | 上列 + `DIV_TYPE` | 有 | 24 |
| `OFD288A` | `OFDM281_Rate` | 上列 + `DIV_TYPE` + `BF_CODE` | 有 | 24 |
| `OFD286A` | `OFDM284` | `DIV_NO` + `BF_NO` + `FUND_ID` | 有 | 36 |
| `OFD290A` | `OFDM285` | `FUND_ID` + `BANK_BRH` | 有 | 22 |
| `OFD291` | `OFDM286` | `BF_NO` + `FUND_ID` + `DIV_DATE_ST` | 有 | 23 |
| `OFD297A` | `OFDM297` | `VOC_NO` + `FUND_ID` | 有 | 27 |
| `OFD300` | `OFDM300` | `CDATE` + `EX_CD` + `CRNCY_CD` | 有 | 23 |
| `OFD301` | `OFDM301` | `CDATE` + `CRNCY_IN` + `CRNCY_OUT` | 有 | 24 |
| `OFD302A` | `OFDM302` | `FUND_ID` + `NAV_DATE` | 有 | 31 |
| `OFD321` | `OFDM321` | `FUND_ID` + `DATA_SEQ` | 有 | 22 |
| `OFD322` | `OFDM321_Detail` | 上列 + `AGENT_TYPE` + `DEPT_NO` + `CHANNEL_CD` + `CHANNEL_CODE` | 有 | 24 |
| `OFD331` | `OFDM331` | `COMPLAIN_NO` | 有 | 42 |
| `OFD332` | `OFDM331_Complain` | `COMPLAIN_NO` + `COMPLAIN_CODE` | 有 | 18 |
| `OFD333` | `OFDM331_Complain_K` | `COMPLAIN_NO` | 有 | 17 |
| `OFD334` | `OFDM331_Solve` | `COMPLAIN_NO` | 有 | 17 |
| `OFD335` | `OFDM331_Solve_K` | `COMPLAIN_NO` + `SOLVE_CODE` | 有 | 18 |
| `OFD337A` | `OFDM337` | `REJ_NO` | 有 | 36 |
| `OFD346A` | `OFDM337_REJ_ITEM` | `REJ_NO` + `REJ_ITEM` | 有 | 18 |
| `OFD344` | `OFDM344` | `BF_NO` + `CHG_DATE` | 有 | 22 |
| `OFD724` | `OFDM271` | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID`(見下) | 有 | 28 |

**四眼 8 欄全員到齊,一張不缺。**這一片沒有 DSM `BMS906` 那種「只有 7 欄、不走四眼」的表(`dsm.md §2`)。

三個例外要講清楚:

- **`OFDM271` 的 vdb `OFDM271` 帶的其實是 `OFD272A` 的欄位。** 28 欄裡有 `TRN_CD` `TRN_NO` `ORG_COPY_CD` `SHORE_ID` `LACK_DATE` `GET_COPY_UID` `GET_COPY_DATE`, PK 宣告與 `OFD272A` 一模一樣,另外多兩個純畫面欄 `ISCHECK`(註記)、`CANCHECK`(可否勾選), 以及一個 join 來的 `STOP_PAY`。`OFD724` 只是 `xTableMapping` 的裝飾(§4.8)。

- **`OFDM361` 的 vdb `OFDM361` 是 103 欄的潛在客戶表**,主鍵 `PR_NO`,與 `CRM003A` 同形(§4.12)。

- **`OFD221A` 有兩種形狀。** 本片 `OFDM221A` 的 `OFDM221A_Detail` 是 125 欄, 但 `OFDM243A` 的 xsd 裡同名表只有 7 欄、**沒有四眼欄位** (`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM243AModel.xsd`),掃描器索引拿到的更是 EC 專案那份 13 欄版。 **同一張實體表在三個 xsd 裡有三種形狀**,加欄位要三邊一起改(§8.1)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列各畫面**識別用**與**卡控會用到**的欄位;完整欄位請直接開對應 xsd(路徑見 §3.1)。中文名一律抄 `msdata:Caption`,沒有 Caption 的留空白。

#### 申購側(`OFD220A` / `OFD221A`)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `ALLOT_NO` | 申購書號 | PK;由 `SerialNo.GetAllotNoForNfd()` 取號 |
| `ALLOT_SRNO` | 序號 | 明細 PK 第二段 |
| `RCV_DATE` | 收件日期 | 必須是公司營業日 |
| `ALLOT_DATE` | 申購日期 | 不可小於收件日期 |
| `ALLOT_CODE` | — | 交易別;`1` 申購 / `2` 轉申購 / `4` 定期定額 |
| `ALLOT_PROC_CODE` | — | 處理碼;`0` 輸入 / `1` 已算單位數 / `2` 已結轉 / `D` 作廢 |
| `ETD_ALLOT_AMT` | 計價幣別申購金額 |  |
| `ALLOT_AMT` | 申購金額 | 中心幣別 |
| `ALLOT_FEE_RATE` | 申購手續費率 |  |
| `ALLOT_FEE` | 申購手續費 |  |
| `RDMING_UNIT` | — | 贖回中單位數;由 `OFDM231A` 回寫(§4.3) |
| `R_UNIT` | — | 剩餘單位數 |
| `FREEZE_UNIT` | — | 凍結單位數 |
| `COMPARE_NO` | — | 匯款比對流水號;有值就不可刪 |
| `REMIT_CTL_NO` | — | 匯款比對控制號;有值就不可刪 |
| `SUB_STATUS` | — | 代扣款狀態;`0` 尚未 / `1` 扣款中 / `2` 成功 / `3` 失敗 |
| `SOURCE_CD` | — | 來源;`1` 一般 / `2` TDCC 指託 / `3` 績效費轉入 |
| `FAVORED_REL_TYPE` | — | 優惠身份別;`BeforeAdd` 由 `ServerBizUtility.GetFavoredRelType` 算 |

#### 買回側(`OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` / `OFD258A`)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `REDEM_NO` | 買回書號 | PK;由 `SerialNo.GetRdmNoForNfd()` 取號 |
| `REDEM_TYPE` | 買回方式 |  |
| `REDEM_DATE` | 買回日期 |  |
| `REDEM_NAV_DATE` | 買回淨值日期 |  |
| `REDEM_UNIT` | 買回單位數 |  |
| `REDEM_PROC_CODE` | — | 買回處理碼;`3` = 已結帳(**無對應常數類別,程式寫死**) |
| `SHORT_ARTI_CTL` | — | 短線交易控管 |
| `SHORT_FEE_RATE` | — | 短線交易費率;來源是 `OFDM233` 維護的 `OFD261A` |
| `SWITCH_FUND_ID` | 轉入基金 | `OFD253A`;轉申購的目標基金 |
| `SWITCH_DATE` | 轉入日期 |  |
| `SWITCH_FEE_R` | 轉換費率(%) |  |
| `SWITCH_FEE_ALLOWANCE` | 轉申購拆帳比 |  |
| `CAN_REDEM_UNIT` | 可買回單位數 | `OFD254A`;指定沖銷時算 |
| `BF_CER_ISSUE_CODE` | 憑證期別號碼 | `OFD258A`;實體憑證買回 |
| `DOC_NID` | — | 缺件註記;`Y` 代表仍缺件 |
| `DOC_ADATE` | — | 缺件到齊日;由 `OFDM271` 回寫 |
| `STOP_PAY_YN` | — | 暫停付款 |

#### 缺件檔 `OFD272A`(本片最多人共用的表)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `TRN_CD` | 缺件種類 | 值域見 §2.5 |
| `TRN_NO` | 缺件編號 | 對應的交易書號 —— 申購放 `ALLOT_NO`、買回放 `REDEM_NO` |
| `ORG_COPY_CD` | 缺件代碼 | 對 `OFD039A` 的 `LACK_CODE` |
| `SHORE_ID` | 境內外基金識別碼 | `1` 境外 / `2` 境內 |
| `BF_NO` | 受益人戶號 |  |
| `LACK_DATE` | 缺件日期 |  |
| `GET_COPY_UID` | 到件更新人員 |  |
| `GET_COPY_DATE` | 到件日期 | 空值哨兵是**一個空白字元**,不是 NULL(§2.5) |
| `TRN_MEMO` | 備註 |  |

#### 其餘畫面的識別欄位

| 畫面 | 關鍵欄位(中文名) |
|---|---|
| `OFDM091` | `FUND_ID`(基金代碼)、`RANGE_TYPE`(贖回區間)、`BNG_DAY`(起算日／月)、`END_DAY`(終止日／月)、`CDSC_FEE_RATE`(遞延手續費率%) |
| `OFDM220` | `AGENT_ID`(銷售機構區別碼)、`AGENT_CODE`(銷售機構代碼)、`ALLOT_AMT`(銷售總金額)、`ALLOT_FEE`(銷售總手續費)、`AGENT_ALLOT_FEE`(銷售機構手續費) |
| `OFDM232` | `AGENT_ID`(買回機構區分碼)、`AGENT_RUNIT`(銷售機構買回單位數)、`RTOT_AMT`(買回總金額)、`TOT_RFEE`(總買回費) |
| `OFDM233` | `SHORT_FEE_RATE`(短線交易費率)、`MAX_AMT_YN`(是否判斷上限)、`MIN_AMT_YN`(是否判斷下限)、`DAY_TYPE`(行事曆認定)、`FEE_TYPE`(計算規則) |
| `OFDM243A` | `STK_BRK`(原始券商代碼)、`NSTK_BRK`(目前券商代碼)、`REBATE_AMT`(配單金額)、`REBATE_MULT`(配單倍數) |
| `OFDM264` | `PAY_BANK`、`FILE_FORMAT`(資料格式)、`FILE_DESC`(檔案格式說明)、`DIVIDE_UP`(是否分割筆數)、`IS_MULTI_CRY`(外幣適用)、`OUTPUT_FILED`(是否產生至磁片檔案) |
| `OFDM270` | `REJ_NO`(退郵單號)、`REJ_OBJ`(退郵項目代碼)、`REJ_CD`(退郵原因代碼)、`REJ_STATUS`(處理狀態)、`REJ_STOP_DATE`(永久失聯戶註記日期) |
| `OFDM281` | `YEARS`(年度)、`ISSUE_CODE`(期別)、`BASE_DATE`(分配基準日)、`VALUE_DEDUCT_DATE`(權值扣除日)、`PROVIDE_DATE`(發放日期)、`SWITCH_DATE`(再投資日期)、`PROCESS_CODE`(作業處理碼) |
| `OFDM284` | `DIV_NO`(收益分配支付方式書號)、`GET_WAY`(支付方式) |
| `OFDM285` | `BANK_BRH`(銀行代碼)、`CUS_BANK_BRH`(保管銀行代碼)、`REMIT_FEE`(匯費金額) |
| `OFDM286` | `DIV_DATE_ST`、`DIV_DATE_END`、`DIV_TYPE` |
| `OFDM297` | `VOC_NO`(臨時放假設定編號)、`BEF_NAV_DATE`(變更前淨值日期)、`AFT_NAV_DATE`(變更後淨值日期)、`EXE_STATUS` |
| `OFDM300` | `CDATE`(日期)、`EX_CD`(匯率屬性)、`CRNCY_CD`(幣別代碼)、`EX_RATE`(匯率) |
| `OFDM301` | `CRNCY_IN`(兌換入幣別代碼)、`CRNCY_OUT`(兌換出幣別代碼)、`EX_RATE`(匯率) |
| `OFDM302` | `NAV_DATE`(淨值日期)、`NAV_B`(正式淨值)、`BID_NAV`(申購淨值)、`OFFER_NAV`(贖回淨值)、`NAV_LOCK`(淨值鎖定)、`FUND_SIZE`(資產規模) |
| `OFDM321` | `DATA_SEQ`(資料流水號)、`BNG_DATE`(控管起始日期)、`END_DATE`(控管終止日期)、`TOT_QUOTA`(控管總額度)、`EQUAL_CHECK`(明細額度是否要等於總額度)、`QUOTA_AMT`(銷售機構額度金額) |
| `OFDM331` | `COMPLAIN_NO`(客訴序號)、`COMPLAIN_TYPE`(客訴對象種類)、`ASN_SOLVE_DEPT_NO`(客訴指定處理部門)、`SOLVE_HF_DATE`(客戶希望完成日期) |
| `OFDM337` | `REJ_NO`(退件單號)、`REJ_CD`(退件原因代碼)、`REJ_ITEM`、`OK_DATE`(文件補期日期)、`REJ_AGENT_CODE`(退件單位) |
| `OFDM344` | `CHG_DATE`(異動日期)、`BEF_BF_QT`(變更前客戶資料保密設定碼)、`AFT_BF_QT`(變更後客戶資料保密設定碼)、`QT_RSN`(保密原因) |

### 2.4 與其他模組共用的表

| 表 | 本片誰用 | 別的模組誰用 | 說明 |
|---|---|---|---|
| `OFD220A`〔共用〕 | `OFDM221A`(主檔)、`OFDM231A`(明細,會 INSERT) | `OFDB310`(主檔)、`OFDB331`(明細)、`BBSM013` `BBSM113`(明細,會 INSERT) | 申購書主檔;§8.1 |
| `OFD221A`〔共用〕 | `OFDM221A` `OFDM231A` `OFDM243A` | `OFDB302` `OFDB304` `OFDB306` `OFDI059` `SDMB001`(主檔)、`OFDB310` `OFDB331` `BBSM013` `BBSM113`(明細) | 申購明細;**三種 xsd 形狀**(§2.2) |
| `OFD234A`〔共用〕 | `OFDM221A`(明細) | `BBSM013` `BBSM113`(明細,會 INSERT) | 申購支票;**沒有任何畫面是它的主檔** |
| `OFD235A`〔共用〕 | `OFDM221A`(明細) | `BBSM013` `BBSM113`(明細,會 INSERT) | 申購匯款;同上 |
| `OFD243A`〔共用〕 | `OFDM243A`(主檔)、`OFDM221A` `OFDM231A`(明細) | — | 券商配單;三支都在本片 |
| `OFD272A`〔共用〕 | `OFDM221A` `OFDM231A`(明細)、`OFDM271`(直接 UPDATE) | `BMSM004` `BMSM006` `RSPM004` `RSPM005`(明細)、`BMSM001` `OFDB310` `OFDI011` `NFDR813`(唯讀) | 缺件檔;**沒有主檔畫面**;§8.2 |
| `OFD136A`〔共用〕 | `OFDM221A` `OFDM231A`(明細) | — | 交易指示代理人;**沒有主檔畫面**,兩支各寫各的一半(`TRADE_TYPE` 區分) |
| `OFD251A` | `OFDM231A` `OFDM242`(主檔) | `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` `SDMB002`(主檔) | 買回主檔;本片兩個入口 |
| `OFD724` | `OFDM271`(名義主檔) | `OFDB327` `OFDM723` `OFDM724`(主檔,**在 OFD9 那一片**) | §8.4;另見 `ofd9.md` |
| `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232`(手寫 SQL) | 全 OFD 批次 | 過帳控制檔;**不在任何 `xTableMapping` 裡,四支各寫各的 SQL** |
| `CTL012` `CTL022` | `OFDM221A` `OFDM231A`(手寫 SQL) | 櫃台關帳 | 同上,不在掃描母體 |
| `BMS001` | `OFDM221A` `OFDM284`(唯讀 join) | BMS 模組主檔 | 受益人基本資料 |
| `OFD039A` | `OFDM231A` `OFDM271`(唯讀 join) | 全庫缺件代碼表 | `LACK_CODE` / `STOP_PAY` / `LIMIT_ALLOT` 等 |
| `OFD721` | `OFDM231A`(直接 UPDATE) | BBS 憑證 | 實體憑證餘額 |
| `OFD130A` `OFD131A` | `OFDM221A` `OFDM231A`(INSERT / SELECT) | 匯款授權書 | 不在掃描母體 |
| `OFD607A` `OFD601` | `OFDM271`(UPDATE) | 網路交易受益人權限 | 缺件到齊後解鎖網路交易 |
| `OFD199A` | `OFDM221A`(唯讀) | 行銷活動 | `CheckCampignCodeData` 用 |

### 2.5 狀態碼(從程式反推,標來源)

除了四眼引擎自己的 `STATUS`(`architecture.md §3`),本片自己的代碼都放在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs`。 **有常數類別的照抄,沒有的標「程式寫死」。**

| 代碼 | 常數類別與錨點 | 值域 |
|---|---|---|
| 缺件種類 `TRN_CD` | `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:26-52` | `1` 開戶 / `2` 申購 / `3` 贖回轉換 / `4` 小額契約 / `5` 受益人異動 / `6` 定期定額異動 |
| 境內外 `SHORE_ID` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` | `1` 境外基金 / `2` 境內基金 |
| 是否 `YES_NO` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-20` | `Y` / `N` |
| 交易別 `ALLOT_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1830-1866` | `1` 申購 / `2` 轉申購 / `3` 除息 / `4` 定期定額 / `5` 轉讓 / `6` 合併 / `9` 調整 |
| 資料來源 `SOURCE_CD` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1929-1945` | `1` 一般 / `2` TDCC 指託 / `3` 績效費轉入 |
| 申購處理碼 `ALLOT_PROC_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1950-1971` | `0` 輸入 / `1` 已算單位數 / `2` 已結轉 / `D` 作廢 |
| 代扣款狀態 `SUB_STATUS` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2071-2092` | `0` 尚未 / `1` 扣款中 / `2` 成功 / `3` 失敗 |
| 申購資料控制碼 `ALLOT_CTL_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2194-2212` | `0` 無資料 / `1` 有資料 / `2` 已單位數計算 / `3` 已結轉 |
| 贖轉資料控制碼 `REDEM_CTL_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2216-2238` | `0` 無資料 / `1` 有資料 / `2` 已預估價金計算 / `3` 已價金計算 / `4` 已結轉 |
| 短線註記 `SHORT_RMK` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2925-2935` | `Y` / `N` |
| **買回處理碼 `REDEM_PROC_CODE`** | **無常數類別** | 程式只用到 `3` = 已結帳,寫死在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` |
| **退郵處理狀態 `REJ_STATUS`** | **無常數類別** | 由畫面下拉來源決定,程式內沒有比較字面量 |

**三個陷阱**:

1. **「已結轉」在申購側是 `3`、在買回側是 `4`。** `ALLOT_CTL_CODE.Tranfer` = `'3'`、`REDEM_CTL_CODE.Tranfer` = `'4'`,兩個常數**同名**(原文就少一個 `s`),值卻不同。 copy-paste 一定踩。

2. **`OFD272A` 的 `GET_COPY_DATE` 沒到件有兩種寫法並存。** `GET_COPY_DATE IS NULL OR GET_COPY_DATE = ' '`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:179`) 與 `NVL(GET_COPY_DATE, ' ') = ' '`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:87`)。寫入端回復到件時塞的是一個空白字元而不是 NULL(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:93-94`), 所以這一欄實務上是「空白字元」,新寫查詢只寫 `IS NULL` 會撈不到。

3. **`REDEM_PROC_CODE` 沒有常數類別,三處各自寫死 `'3'`**,其中兩處還寫成 `<> '3'` —— 這一欄如果為 NULL,Oracle 三值邏輯會讓那兩處靜默過濾掉資料(附錄 E-2)。

## 3. 畫面清冊

### 3.1 維護 M(24 支,本片全部)

六層路徑一律是這個形狀,下表不再重複:

```
Dev/ATLAS.OFD/Source/UI/UI.OFD/<代號>.cs
Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/<代號>_Pxy.cs
Dev/ATLAS.OFD/Source/Control/Control.OFD/<代號>_Ctl.cs
Dev/ATLAS.OFD/Source/PO/PO.OFD/<代號>_PO.cs
Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/<代號>Model.xsd
Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/<代號>View.xsd
```

| 代號 | 中文名(推測) | 六層齊不齊 | 主表 | 明細 | PO 基底 | UI 基底 |
|---|---|---|---|---|---|---|
| `OFDM091` | 基金遞延手續費(CDSC)費率維護 | 齊 | `OFD091A` | `OFD092A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM220` | 銷售機構申購彙總維護 | 齊 | `OFD232A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM221A` | 境內基金申購交易維護 | 齊 | `OFD220A` | 7 張 | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM231A` | 境內基金買回／轉換交易維護 | 齊 | `OFD251A` | 10 張 | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM232` | 銷售機構買回彙總維護 | 齊 | `OFD259A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM233` | 短線交易費率維護 | 齊 | `OFD260A` | `OFD261A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM242` | 投資組合(契約)贖回維護 | 齊 | `OFD251A` `OFD252A` `OFD254A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM243A` | 券商配單維護 | 齊 | `OFD243A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM264` | 付款媒體檔格式設定 | 齊 | `OFD264A` | `OFD265A` `OFD266A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM270` | 退郵戶維護 | 齊 | `OFD270A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM271` | 缺件到件／回復登錄 | 齊 | `OFD724`(名義) | — | `BaseEVADaoPO` | **`xOneStepProcessForm`** |
| `OFDM281` | 基金收益分配(配息)設定 | 齊 | `OFD281A` | `OFD287A` `OFD288A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM284` | 受益人收益分配支付方式維護 | 齊 | `OFD286A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM285` | 基金匯費設定維護 | 齊 | `OFD290A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM286` | 受益人配息期間／類別維護 | 齊 | `OFD291` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM297` | 臨時放假淨值日期變更 | 齊 | `OFD297A` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM300` | 幣別匯率維護 | 齊 | `OFD300` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM301` | 交叉匯率維護 | 齊 | `OFD301` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM302` | 基金淨值維護 | 齊 | `OFD302A` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM321` | 基金銷售額度控管維護 | 齊 | `OFD321` | `OFD322` | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM331` | 客訴案件維護 | 齊 | `OFD331` | `OFD332` `OFD333` `OFD334` `OFD335` | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM337` | 交易退件維護 | 齊 | `OFD337A` | `OFD346A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM344` | 客戶資料保密設定異動 | 齊 | `OFD344` | — | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM361` | (未完成的潛在客戶維護空殼) | 齊(檔在,內容空) | 未宣告 | — | **`BasicEVAPO`**(空類別) | `xMaintainForm` |

中文名全部是**推測**,依據是主檔欄位的 `msdata:Caption` 與程式內註解。只有兩支有程式內的明確中文:`OFDM221A`(「境內基金申購交易維護作業」,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:38`) 與 `OFDM302`(「基金淨值維護作業」,`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM302_Ctl.cs:15`)。

### 3.2 查詢 I

**本片無 I 畫面。**原因見 §5 —— OFD 的查詢畫面集中在 `ATLAS.OFD.Query` 與 `ATLAS.OFDI` 兩個專案, 不在 `DataEntity.OFD8` 這一片的 entity 分卷裡。

### 3.3 批次 B

**本片無 B 畫面,也沒有任何 WindowsService。**原因見 §6 —— OFD 的批次全部落在 `ATLAS.OFDB`(`OFDB3xx` 結帳過帳)與 `ATLAS.EC`(`OFDB6xx` 服務型),entity 也在別的分卷。

### 3.4 報表 R

**本片無 R 畫面,也沒有任何 `.rpt`。**原因見 §7 —— 報表依鐵律住在 `ATLAS.OFD.Report`(`architecture.md §6`), 是另一個專案,不會出現在 `DataEntity.OFD8`。

### 3.5 一眼看出差別的六件事

1. **PO 基底分成四代並存。** 12 支新世代單筆(`BaseEVADaoPO`)、5 支新世代多筆(`BaseMultiRowEVADaoPO`)、 3 支舊世代多筆(`MultiRowEVAPO`)、4 支舊世代單筆(`BasicEVAPO`,含空殼 `OFDM361`)。 **舊世代那 7 支的連線欄位從來沒有被賦值**(§0.2、附錄 E-1)。

2. **只有 `OFDM271` 不是 `xMaintainForm`。** 它繼承 `xOneStepProcessForm` (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28`),也就是 B / I 型畫面用的基底 —— 一個查詢頁 + 一顆執行鈕,沒有四眼送審流程。代號是 `M` 但行為是 B(§4.8)。

3. **`OFDM221A` 與 `OFDM231A` 加起來佔了本片 40% 的程式量。** UI 3,137 + 5,659 行、PO 2,769 + 4,006 行,其餘 22 支全部加起來才 8,000 行上下。

4. **沒有任何一支用 Stored Procedure 做主要取數。** 全片只出現三個 DB 物件名: `S_TA_OFDM221A_Get`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2410`,取四條規則文字)、 `S_TA_UPD_REDEM_SHORT_RMK`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2463`,更新短線註記)、 `f_TA_GetEmpLockUnitsOnTheDay`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:200`,員工閉鎖單位數)。三個都在版控外,repo 內看不到內容。**其餘全部是 PO 內手寫 SQL。**

5. **查詢條件全部走同一段字串串接樣板。** 十幾支 PO 都有這樣一段: `strSQL += " And OFD243A." + Row.Name + " = " + "'" + Row.Value + "'";` (例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:168`)。 **欄位名與值都來自用戶端**,沒有綁參數(附錄 E-5)。

6. **四支的 SQL 還是 SQL Server 方言。** `OFDM284` `OFDM321` `OFDM331` `OFDM344` 的 live 程式碼用方括號識別字 `[OFD321]` / `[BMS001]`,`OFDM242` 更是整段 T-SQL 批次。Oracle 不吃(附錄 E-1)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFD8 其餘二十二支畫面依 PO 基底世代與行為分成四群
圖中文字:A 群:新世代單筆 BaseEVADaoPO(12 支,可正常運作) / OFDM091 OFDM233 / 費率主明細 兩支同形 / OFDM220 OFDM232 / 彙總 成對只改一邊 / OFDM243A OFDM264 / 配單 / 媒體檔格式 / OFDM270 OFDM281 OFDM337 / 退郵 / 配息 / 退件 / B 群:新世代多筆 BaseMultiRowEVADaoPO(5 支) / OFDM300 OFDM301 / 匯率成對 一支用double / OFDM302 / 淨值 鎖定才擋刪 / OFDM286 / 配息期間 唯一性檢核兩份 / OFDM297 / 臨時放假 逐列回報 / C 群:舊世代 MultiRowEVAPO / BasicEVAPO(7 支,推測跑不動) / OFDM242 OFDM284 OFDM285 / MultiRowEVAPO / OFDM321 OFDM331 OFDM344 / BasicEVAPO / dbTA 從未被賦值 / 建構子整段註解 / SQL 還是 T-SQL / 方括號 / DECLARE @x / D 群:兩支不照規矩的畫面 / OFDM271 / 代號M 行為B 主檔是假的 / OFDM361 / 三層空類別 從未接上DB / xOneStepProcessForm / 271 不是 xMaintainForm / Designer 653行 / 361 的畫面其實畫完了 / 共同形狀:卡控條數與資料重要性不成比例 / OFDM300 / OFDM301 / 全庫金額基礎 各1~2條 / OFDM264 / 媒體檔格式 二十餘條 / OFDM344 / 完全沒有業務檢核 / OFDM243A / 只有一條 金額不得為0
```

*圖:圖 4 其餘畫面分群。白框=可正常運作;橘虛框=有風險、不對稱或推測跑不動;黑框=框架層或方言殘留;灰虛框=存在但沒被接上。C 群那七支的 UI 檢核是活的、PO 是死的——使用者會走到按下存檔那一刻才失敗。*

```text
[圖] OFDM221A 與 OFDM231A 的四層卡控,以及已結帳買回書的靜默失敗路徑
圖中文字:① 用戶端 UI:兩大支的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / 221A 約480行 20條 / Chk*() 八支 / 額度/KYC/關帳/關係人 / ByPassAddMessage / 詢問過了就記錄不擋 / ② 伺服端 PO 的 Check* 方法:是 UI 主動叫的 RPC,不是掛點 / 221A 十二支 Check* / 戶號/帳號/關帳/活動 / 231A 十一支 Check* / 憑證/短線/CDSC/單位數 / 繞過 UI = 零卡控 / 批次直接叫 Ctl 就過 / S_TA_OFDM221A_Get / 版控外 只取規則文字 / ③ EVA 掛點:這一片拿來寫副作用,不拿來擋 / BeforeAdd / 取書號 無重試上限 / AfterAdd / AfterUpdate / 寫 OFD303A CTL012 CTL022 / BeforeSave 822行 / 231A 回寫 OFD221A 單位數 / AfterApproveDelete / 唯一會回沖的掛點 / ④ 四眼引擎:驗證與覆核在這一片只留軌跡 / 輸入 → 帳已經動了 / AfterAdd 已寫控制檔 / 驗證 AfterVerify / 只寫跳號一覽表 / 覆核 AfterApprove / 只寫跳號一覽表 / 15 處 throw 空訊息 / 使用者看到空白錯誤 / ⑤ 靜默失敗的一條路:已結帳的買回書 / REDEM_PROC_CODE=3 / 寫死字面量 無常數 / BeforeUpdate 抽掉明細 / DetailTable.Clear() / 只剩 OFD272A 被寫 / 付款/轉換改動不見 / 畫面仍回「成功」 / 過濾(無提示)
```

*圖:圖 3 兩大支的四眼與卡控順序。橘框=真的會擋或真的會寫資料的關卡;橘虛框=風險、寫死值或靜默失敗;黑框=版控外。最重要的一件事在第 ④ 排:驗證與覆核的 handler 主體只有一行跳號紀錄,帳在輸入當下就動了。*

**讀法**:§4.1 §4.2 是兩大支,§4.3 是它們的分工(本篇最有價值的一節), §4.4–§4.12 是其餘值得單獨寫的九支,§4.13 是剩下 12 支的表格群組。每節末的卡控總表,結果類型一律五類:**阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋**。

「記錄不擋」在本片有個具體實作:`ByPassAddMessage(訊息, ProcessVDB, 畫面名, true)` —— 使用者在確認框按了「是」之後,把原本的警告字串當作 bypass 理由塞進 VDB 一併送出,四眼覆核者看得到。 `OFDM221A` 與 `OFDM337` 都大量使用這一招。

### 4.1 `OFDM221A` 境內基金申購交易維護

用途(推測):**建立一張境內基金申購書**,連同它的支票、匯款、券商配單、缺件、代理人資料一次送四眼。是本片的第一大支,也是 `OFD220A` 的主檔持有者(§8.1)。

#### 4.1.1 結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseEVADaoPO, IOFDM221_PO`(介面名少一個 `A`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:25`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:55` |
| 主檔 | `OFD220A` → vdb `OFDM221A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67` |
| 明細(7) | `OFD221A` 申購明細、`OFD272A` 缺件、`OFD234A` 支票、`OFD235A` 匯款、`OFD243A` 券商配單、`OFD220A_AGENT` 意定代理人、`OFD136A` 交易指示代理人 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:68-76` |
| EVA 掛點 | `BeforeSelect` `BeforeGetMaintainData` `BeforeGetToDoData` `BeforeAdd` `BeforeUpdate` `AfterAdd` `AfterUpdate` + 8 個跳號用 After | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:60-87` |
| 伺服端檢核方法 | 12 支公開 `Check*` / `Get*`,由 UI 主動呼叫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-2646` |

明細的取數走一個**不尋常的寫法**:`BeforeGetMaintainData` 只在 `DetailTable[0]`(也就是 `OFD221A`) 那一次進來時組一段 **`;` 串起來的多段 SQL**,一次 `LoadDataSet` 灌 7 張表,然後 `args.Cancel = true` 讓框架不要再各跑一次(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:127-136`)。 **後果**:7 張明細的載入順序與欄位對應由 `LoadDataSet` 的參數順序決定,加一張明細一定要同時改三處 (`DetailTable.Add`、`BuildDetailSQLString` 的 `case`、`LoadDataSet` 的表名清單)。

#### 4.1.2 必填與存檔前檢核

UI 的 `DoValidate(bool isFinalCheck)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:652`)是主戰場,約 480 行。主要條目:

| 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 受益人戶號存在且可交易 | 依 `Check_NO` 回傳 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:730-733` |
| 明細申購日期 ≥ 收件日期 | 明細資料的 申購日期 不可小於 收件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:753` |
| 有通路區分碼就必須有通路代碼 | 有挑選 通路區分碼 時,通路代碼 必須輸入! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:787` |
| 收件日期須為公司營業日 | 收件日期 不為公司營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:819` |
| 付款方式為代扣款 → 扣款行 / 扣款帳號必填 | 付款方式為 代扣款,扣款行 必須輸入! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:827-829` |
| 扣款方式 / 匯款類別必填 | 扣款方式 為必填欄位 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:831-839` |
| 至少一筆明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:846` |
| 基金該申購日是否禁止交易 | 申購日 yyyy/MM/dd + 限制說明 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:880`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:913` |
| 匯款比對已關帳 | 基金 X 滙款比對已關帳,不可再執行「要匯款比對」之資料建檔! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:953` |
| 傳真委扣同意書 / 扣款帳號有效性 | 申購日期 [X] 無有效傳真委扣同意書資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1011-1016` |
| 交易方式不可為線上交易 | 交易方式不可為線上交易 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1028` |
| KYC 風險屬性不符 | 依 `ChkKYC_RISK_ATTR` | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1079-1096` |
| 不得主動推薦高風險基金 | 此受益人「不得主動推薦高風險基金」 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1132` |
| 櫃台關帳 | 依 `ChkKeyIN_ALLOT_CLS` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1144-1212` |
| 關係人交易 | 依 `ChkIsRelTrade` | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1234-1264` |
| OBU 檢核 | 依 `ChkIsOBU` | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1265-1277` |
| 身分證 / 統編格式 | 依 `ChkID_NO` | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1278-1298` |
| **基金銷售額度** | 基金[X]申購金額 已超過基金銷售額度,是否繼續? | **詢問 → 記錄不擋** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1299-1335` |
| 一般申購只能一筆明細 | 申購只可輸入一筆基金明細資料。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2171` |
| 註銷戶不可交易 | 此 受益人 為註銷戶不可執行交易 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2483` |

`ChkFundQuota` 這一條要特別記:它是 `OFDM321`(基金銷售額度控管)唯一的下游消費者, 透過 `m_nfdBiz.IsOverFundQuota(...)` 比對(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1314`)。超額只是**詢問**,按「是」就用 `ByPassAddMessage` 記錄後照樣送出 —— **額度不是硬上限**。

#### 4.1.3 刪除卡控(五條,全在 UI)

刪除按鈕與 grid 刪列各有一套幾乎相同的檢核,兩邊各五條:

| 條件 | 訊息 | 結果 | 按鈕層錨點 | 列層錨點 |
|---|---|---|---|---|
| TDCC 指託來源 | 此為 TDCC 指託平台下單資料,不可刪除。請執行基金集保指託下單資料刪除作業(OFDB757) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2022-2029` | — |
| 有比對流水號 | 已有比對流水號資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2044` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2084` |
| 傳真委扣交易截止 | 已有資料做傳真委扣交易截止設定,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2050` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2090` |
| 已作廢 | 已有作廢資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2056` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2096` |
| 已結轉 | 已結轉資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2102` |
| 已匯款比對 | 明細資料已執行過匯款比對,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2069` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2109` |

**兩邊的判斷方式不一樣**:按鈕層用 `DataTable.Select("COMPARE_NO<>''")` 字串運算式, 列層用 `row.COMPARE_NO != ""` 直接比欄位值。前者對 `DBNull` 會判 false(過濾掉),後者對 `DBNull` 會丟例外。同一條規則兩種寫法,是附錄 E-3 的一例。

#### 4.1.4 四眼各階段附加動作

| 掛點 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd`(主檔) | 取申購書號 `GetAllotNoForNfd()`,撞號重取;逐筆明細算優惠身份別 `FAVORED_REL_TYPE`;接著 `BeforeSave` / `AddOFD130A` / `GetUnitCode` / `GetDataCenter` / `RealSubDate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:157-203` |
| `BeforeUpdate`(主檔) | 同上五支,但**不取號** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:211-223` |
| `AfterAdd`(明細 `OFD221A`) | 逐筆更新 `OFD303A` / `CTL012` / `CTL022`(`EnumAction.Add`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:286-303` |
| `AfterUpdate`(明細 `OFD221A`) | 依 Added / Modified / Deleted 三批分別更新同三張控制檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:231-284` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterResend` / `AfterReject` | **只寫跳號一覽表**(`SrNoCommentProcessor.AddCommentHistory`),零業務 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2678-2741` |
| `AfterApproveDelete` | 跳號紀錄 + `ChkCTL_FILE`:重讀明細後把 `OFD303A` / `CTL012` / `CTL022` 全部以 `EnumAction.Delete` 回沖 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2719-2726`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2743-2767` |

**結論:驗證與覆核不改任何業務資料。**帳上的控制碼在「新增 / 修改」當下就動了, 只有「覆核刪除」才回沖。這對排查「為什麼還沒覆核帳就變了」是關鍵。

#### 4.1.5 跨表更新

| 表 | 動作 | 時機 | 錨點 |
|---|---|---|---|
| `OFD303A` | UPDATE 申購控制碼,不存在則 INSERT | `AfterAdd` / `AfterUpdate` / `AfterApproveDelete` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1012-1377` |
| `CTL012` | 代扣款控制檔 UPDATE / INSERT / DELETE | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1378-1579` |
| `CTL022` | 櫃台控制檔 UPDATE / INSERT / DELETE | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1580-1759` |
| `OFD130A` | 匯款授權書:沒有就新增一筆 | `BeforeAdd` / `BeforeUpdate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:365-450` |

#### 4.1.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前(UI) | `ChkID_NO` 統編格式 | 詢問是否忽略 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1920-1923` |
| 新增前(UI) | `DoValidate(true)` 全部欄位與業務檢核 | 列出錯誤清單 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1927-1941` |
| 新增前(UI) | `ChkFundQuota` 銷售額度 | 詢問是否繼續 | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1943-1947` |
| 新增前(UI) | `CheckEmpNo` 業務員銷售機構不符 | 此員工代碼無相對應之銷售機構 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1949`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2635` |
| 修改前(UI) | 同新增,另加來源碼檢核 |  | 阻擋 / 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1963-2008` |
| 刪除前(UI) | 五條狀態檢核 | 見 §4.1.3 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2009-2077` |
| 查詢前(UI) | 四個條件擇一 | 申購書號, 收件日期, 客戶統編, 戶號 必須擇一填寫 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1861` |
| 伺服端(PO) | `CheckSameAllotData` 同日同基金重複申購 | 由 UI 決定呈現 | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-1925` |
| 伺服端(PO) | `Check_NO` 戶號 / 統編 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1926-2028` |
| 伺服端(PO) | `Check_Remit_Compare` 匯款比對關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2029-2082` |
| 伺服端(PO) | `CheckACC_NO` 扣款帳號有效性 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2083-2163` |
| 伺服端(PO) | `CheckCampignCodeData` 行銷活動代碼 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2164-2304` |
| 伺服端(PO) | `CheckBF_NO_StopAllot` 受益人停止申購 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2475-2530` |
| 伺服端(PO) | `CheckALLOT_CLS` 櫃台關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2531-2592` |
| 伺服端(PO) | `CheckSubAcct` CDSC 子帳戶 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2593-2646` |
| 存檔時(PO) | 申購書號撞號 | 重新取號,無次數上限 | 記錄不擋(有無窮迴圈風險) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:172-177` |

**沒有任何一條卡控落在 `BeforeAdd` / `BeforeUpdate` 裡做否決。** 所有 PO 端檢核都是 UI 主動呼叫的 RPC。繞過 UI(例如另寫一支批次直接叫 `_Ctl`)= 零卡控。

### 4.2 `OFDM231A` 境內基金買回／轉換交易維護

用途(推測):**建立一張境內基金買回書**,涵蓋三種形態 —— 純買回(付款)、轉換(轉申購)、實體憑證買回; 並把要沖銷的原申購書逐筆挑出來。本片第二大支,也是全片最複雜的一支。

#### 4.2.1 結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseEVADaoPO, IOFDM231A_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:65` |
| 主檔 | `OFD251A` → vdb `OFDM231A_Master`(93 欄) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70` |
| 明細(10) | `OFD252A` 付款、`OFD253A` 轉換、`OFD272A` 缺件、`OFD254A` 指定沖銷、`OFD258A` 憑證、`OFD220A` 申購主檔、`OFD251A_AGENT`、`OFD221A` 申購明細、`OFD243A` 券商配單、`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:71-82` |
| 解構子 | **逐一 `-=` 解除 14 個事件**(全片唯一這樣做的) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:106-123` |
| 伺服端檢核方法 | 11 支 `Check*` / `Get*` + 12 支非泛型工具方法 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:34-59` |

#### 4.2.2 三種形態,三條明細線

| 形態 | 使用者填什麼 | 寫哪些表 |
|---|---|---|
| 純買回 | 買回單位數 / 金額 + 付款明細 | `OFD251A` + `OFD252A` + `OFD254A`(沖銷) |
| 轉換(轉申購) | 轉入基金 / 轉入日期 / 轉換費率 | `OFD251A` + `OFD253A` + `OFD254A` + **新開 `OFD220A` / `OFD221A`** |
| 實體憑證買回 | 憑證期別 + 憑證號碼 | `OFD251A` + `OFD258A` + UPDATE `OFD721` |

**第二列是這一支最容易被忽略的事**:轉換會在同一次送審裡**產生一張全新的申購書**(§4.3)。

#### 4.2.3 必填與存檔前檢核(UI)

| 檢核 | 訊息 / 行為 | 結果類型 | 錨點 |
|---|---|---|---|
| 受控管基金 | 伺服端回傳訊息,首字 `1` 警示 / `2` 錯誤 | 警示 或 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:974-990`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:186-190` |
| 缺件尚未到齊 | grid 內 `GET_COPY_UID<>''` 判斷 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` |
| 匯費 / 郵費試算 | 取回後才填 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:4692`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:4723` |
| 帳號 / 憑證 / 受益人 / 短線費 | 走 PO 的 `CheckACC_NO` `CheckCER_R_ID` `CheckBF_NO` `IsShortFee` | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:36-50` |

#### 4.2.4 四眼各階段附加動作

| 掛點 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd`(主檔) | 取買回書號 `GetRdmNoForNfd()`,撞號重取;`UpateOFD313`(叫 SP 更新短線註記)、`AddOFD130A`、`UpdateCTL022` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3492-3510` |
| `BeforeAdd`(明細 `OFD252A`) | `BeforeSave` —— 這一支真正做事的地方(下表)+ `BeforSaveOFD272` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3511-3516` |
| `BeforeUpdate`(主檔) | **若 `REDEM_PROC_CODE == "3"`(已結帳)就把 `DetailTable` 清空、只留 `OFD272A`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3519-3547` |
| `AfterUpdate`(明細 `OFD221A`) | 跑完最後一張明細後,對被刪除的轉換列回沖 `OFD303A`(`Del303aAllot`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3548-3558` |
| `AfterApproveDelete` | 整張買回書的反向處理(約 300 行) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3640-3949` |
| `AfterDelete` | 跳號紀錄:主檔一筆 + **每一張轉換產生的申購書各一筆** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3953-3966` |
| `AfterVerify` / `AfterApprove` / `AfterReject` / `AfterResend` / `AfterUnDelete` | **只寫跳號一覽表,零業務 SQL** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3968-4003` |

`BeforeSave`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1563-2385`,822 行)是本片最長的方法,做八件事:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | UPDATE / INSERT `OFD303A` 贖轉控制碼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1576-1632` |
| 2 | UPDATE `OFD304A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1633-1678` |
| 3 | 以 `OFD252A` 每筆 INSERT 匯款授權 `BMS004A` / `BMS005A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1679-1832` |
| 4 | **以 `OFD253A` 每筆新增 / 刪除 `OFD220A` + `OFD221A`(轉申購)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1833-2115` |
| 5 | 同步券商配單 `OFD243A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2116-2181` |
| 6 | **以 `OFD254A` 每筆 UPDATE `OFD221A` 的 `RDMING_UNIT`(贖回中單位數)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2200-2236` |
| 7 | 以 `OFD258A` 每筆 UPDATE `OFD721`(實體憑證餘額)與相關 `OFD258A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2238-2385` |
| 8 | 缺件 `OFD272A` 補書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2445-2457` |

第 6 步的算式值得抄下來,因為它是「重算而非累加」:

```
SET RDMING_UNIT = R_UNIT - FREEZE_UNIT + :RDMING_UNIT
    參數 :RDMING_UNIT = (變更後 REDEM_UNIT) - CAN_REDEM_UNIT
```

程式註解把推導寫在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2201-2205`: 先扣掉變更前的 `REDEM_UNIT` 再加回變更後的,避免重複累加。影響筆數不是 1 就 `throw new ApplicationException("更新境內基金申購明細檔失敗,請檢查")` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2227-2228`)—— 這是本片少數**有訊息**的 throw。

#### 4.2.5 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI | 受控管基金 | 首字 `1` 警示 / `2` 阻擋 | 警示 / 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:974-990` |
| UI | 仍有缺件 | 不可贖回 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` |
| PO | `CheckREDEM_CLS` 買回關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:40` |
| PO | `CheckRedemAll` 全部買回 |  | 詢問 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:42` |
| PO | `IsRedemDataExist` 同日同基金重複買回 |  | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:49` |
| PO | `IsShortFee` / `IsNonShortFee` 短線交易費 | 依 `OFDM233` 設定 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:50-52` |
| PO | `CHK_UNIT_CHG` 單位數異動 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:55` |
| PO | `CheckCdscSwitch` CDSC 基金轉申購限制 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:59` |
| PO | `GetRemainRedemUnits` 可買回單位數 | 不足則算式為負 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:54` |
| PO 存檔 | `REDEM_PROC_CODE = '3'`(已結帳) | **只允許改缺件,其餘明細靜默不寫** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522-3529` |
| PO 存檔 | `OFD221A` 更新筆數 ≠ 1 | 更新境內基金申購明細檔失敗,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2227-2228` |
| PO 存檔 | `OFD721` 更新筆數 ≠ 1 | 更新境內基金買回受益憑證檔失敗,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3939-3940` |

**「已結帳就只更新缺件」這一條要特別小心**:它不是提示、不是阻擋,是**把明細清單抽掉**。使用者在畫面上改了付款明細按存檔,系統回「成功」,但那些改動根本沒送進 SQL。這是本片最典型的「過濾(無提示)」。

### 4.3 `OFDM221A` 與 `OFDM231A` 到底怎麼分工

這一節回答三個問題:**它們是不是一對?共用的五張表各自在做什麼?改一邊會不會影響另一邊?**

#### 4.3.1 是一對,但不是對稱的一對

| 面向 | `OFDM221A` | `OFDM231A` |
|---|---|---|
| 交易方向 | 申購(錢進來、單位數出去) | 買回 / 轉換(單位數回來、錢出去) |
| 主檔 | `OFD220A` 申購書(PK `ALLOT_NO`) | `OFD251A` 買回書(PK `REDEM_NO`) |
| 取號 | `SerialNo.GetAllotNoForNfd()` | `SerialNo.GetRdmNoForNfd()` |
| 明細張數 | 7 | 10 |
| 缺件種類 `TRN_CD` | `'2'` 申購(`TRN_CD.Allot`) | `'3'` 贖回轉換(**寫死 `'3'`,沒用常數**) |
| 會不會建對方的主檔 | **不會** | **會** —— 轉換時建 `OFD220A` / `OFD221A` |
| 程式規模 | UI 3,137 / PO 2,769 | UI 5,659 / PO 4,006 |

**不對稱的關鍵在最後兩列。**`OFDM231A` 的轉換(switch)在業務上等於「贖一檔、買另一檔」, 所以它必須在同一筆交易裡替轉入基金開一張申購書。`OFDM221A` 沒有反向需求。

#### 4.3.2 五張共用表各自的角色

| 表 | 在 `OFDM221A` | 在 `OFDM231A` | 誰是寫入者 |
|---|---|---|---|
| `OFD220A` | **主檔**,INSERT / UPDATE / DELETE | 明細 vdb `OFDM231A_Allot`,**轉換時 INSERT、取消轉換時 DELETE** | 兩支都寫 |
| `OFD221A` | 明細 vdb `OFDM221A_Detail`,INSERT / UPDATE / DELETE | 明細 vdb `OFDM231A_AllotDetail`,轉換時 INSERT;另外**用手寫 SQL UPDATE `RDMING_UNIT`** | 兩支都寫 |
| `OFD243A` | 明細 vdb `OFD243`,跟著申購書走 | 明細 vdb `OFD243`,跟著轉申購走 | 兩支都寫(主檔畫面是 `OFDM243A`) |
| `OFD272A` | 明細 vdb `OFD272`,`TRN_CD='2'`、`SHORE_ID='2'` | 明細 vdb `OFD272`,`TRN_CD='3'` | 兩支都寫(另有四支外部畫面,§8.2) |
| `OFD136A` | 明細 vdb `OFD136A`,`TRADE_NO` = 申購書號 | 明細 vdb `OFD136A`,`TRADE_NO` = 買回書號 | 兩支都寫,靠 `TRADE_TYPE` 分流 |

三個實務上的後果:

1. **`OFD220A` / `OFD221A` 有兩個建檔入口(本片內)加兩個外部入口(BBS)。** 本片:`OFDM221A` 正常開單、`OFDM231A` 轉換開單。外部:`BBSM013` / `BBSM113` 轉讓過戶開單(§8.1)。 **任何「申購書一定從 `OFDM221A` 來」的假設都是錯的。**

2. **`OFD221A` 的 `RDMING_UNIT` 只有 `OFDM231A` 會寫,而且是繞過四眼引擎的手寫 UPDATE。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2207-2236` 不更新 `UPDATEID`(程式註解明講「不更新 UpdateID」)。所以看到 `OFD221A` 的單位數變了但 `UPDATEID` 沒變,不是資料異常,是設計。

3. **`OFD272A` 的 `TRN_NO` 是「多型外鍵」。** 同一欄在 `TRN_CD='2'` 時放 `ALLOT_NO`、`TRN_CD='3'` 時放 `REDEM_NO`、 `TRN_CD='1'/'5'` 時放 BMS 的異動書號。**沒有 FK,只能靠 `TRN_CD` 判斷要 join 哪張表。**

#### 4.3.3 轉換是怎麼變成一張申購書的

`OFDM231A_PO.BeforeSave` 的第 4 步(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1833-2115`):

| 情境 | 做什麼 | 錨點 |
|---|---|---|
| 轉換列被**刪除** | 找出對應的 `OFDM231A_Allot` 列 → 寫一筆 `EVAType.Modify` 跳號紀錄 → `row220.Delete()` → 連帶刪掉該申購書的券商配單 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1834-1852` |
| 轉換列是**新增** | `NewOFDM231A_AllotRow()` + **逐欄手寫 156 個指派**填出 `OFD220A` 與 `OFD221A` 兩筆,然後 `AddOFDM231A_AllotDetailRow` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1931-2106` |
| 轉換列是**修改** | **只同步一個欄位** `FAVORED_REL_TYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2110-2112` |

**最後一列是本片最會咬人的缺陷。**新增走 156 個指派、修改只走 1 個。使用者若在同一張買回書上把轉換的金額、日期、通路、業務員改掉, `OFD253A`(轉換明細)會更新,但它的影子 `OFD221A`(申購明細)**除了優惠身份別以外全部維持舊值**。而且 `FindByALLOT_NOALLOT_SRNO(row1.ALLOT_NO, 1)` 把 `ALLOT_SRNO` 寫死成 `1`、回傳值沒有 null 檢查 —— 找不到就 `NullReferenceException`(附錄 E-4)。

#### 4.3.4 改一邊會不會影響另一邊

| 你要改什麼 | 一定要一起看的地方 |
|---|---|
| `OFD220A` / `OFD221A` 加欄位 | `OFDM221A` 的 Model + View xsd、`OFDM231A` 的 Model + View xsd(vdb 名不同)、`OFDM243A` 的 xsd(7 欄縮減版)、BBS 兩支的 xsd、EC 的 `OFDB672` / `OFDB673` xsd;再加 `OFDM231A_PO` 那 156 行手寫指派 |
| `OFD272A` 加欄位 | 本片 2 支 + BMS 2 支 + RSP 2 支的 xsd,共 6 份;還有 `OFDM271` 的 `OFDM271` vdb |
| 缺件邏輯 | `OFDM221A`(`TRN_CD.Allot`)、`OFDM231A`(寫死 `'3'`)、`OFDM271`(到件登錄)、`Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130`(交易限制判斷) |
| 申購書取號 | `OFDM221A`(`SrNo.AllotNoForNfd`)與 `OFDM231A`(`SrNo.AllotNoForNfdS`,**S 結尾是另一組號**) |

最後一列值得單獨記:轉換產生的申購書用的是 **`SrNo.AllotNoForNfdS`** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1843`),與正常申購的 `SrNo.AllotNoForNfd` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2683`)**不是同一組流水號**。從書號就看得出來這張申購書是不是轉換來的 —— 但程式裡沒有任何地方把這件事寫成文件。

### 4.4 `OFDM264` 付款媒體檔格式設定

用途(推測):定義**某家付款銀行的某一種媒體檔**長什麼樣 —— 檔名怎麼編、每一欄放什麼、長度對齊補位小數位數怎麼設。它是產檔程式的設定來源,自己不產檔。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD264A`(`PAY_BANK` + `FILE_FORMAT` + `FILE_ID`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:35` |
| 明細 1 | `OFD266A` 檔名編立規則(vdb `OFDM264_FileRule`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:36` |
| 明細 2 | `OFD265A` 欄位定義(vdb `OFDM264_Field`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:37` |
| EVA 掛點 | **只有 `BeforeSelect` 與 `BeforeGetMaintainData`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:32-33` |

**這一支沒有任何 `Before*Add` / `After*` 掛點** —— 存檔完全交給四眼引擎的通用 INSERT / UPDATE, 沒有跨表副作用。卡控 100% 在 UI。

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 資料格式為明細(`FILE_FORMAT='2'`)時,檔名規則必填 | 資料格式為明細時,檔名規則必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:232` |
| 存檔前 | 檔名規則至少一筆 | 自訂檔名編立方式:請至少輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:237` |
| 存檔前 | 每筆序號 / 資料形式 / 基準日期 / 資料內容必填 | 自訂檔名編立方式:第 N 筆的… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:245-276` |
| 存檔前 | 固定檔名時資料形式不得為年編 / 批號 | 因檔名規則為固定檔名,第 N 筆的資料形式不得為… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:261` |
| 存檔前 | 批號只能一筆 | 批號的資料形式只能有一筆 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:283` |
| 存檔前 | 檔名內容長度 ≤ 10(中文算 2) | …資料內容長度必須 <=10 (一個中文字的長度為2) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:306` |
| 存檔前 | 下載格式至少一筆 | 下載格式設定資料:請至少輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:316` |
| 存檔前 | 每筆序號 / 欄位名稱 / 欄位型態 / 長度 / 對齊方式必填 | 下載格式設定資料:第 N 筆的… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:322-351` |
| 存檔前 | 非首筆 / 尾筆時欄位型態限制 | 資料格式不為首筆或尾筆,第 N 筆的欄位型態不可為… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:338` |
| 存檔前 | 日期型欄位長度只能 6/7/8/10 | 第 N 筆的長度必須為 6,7,8,10 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:373` |
| 存檔前 | 小數位數 ≥ 0、小數補位字元必填 | 第 N 筆的小數位數必須大於等於零 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:384-390` |

**兩個被註解掉的檢核**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:288`(檔名資料內容必填) 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:356`(補位字元必填)外殼還在,實際不檢核。

**一個結構上的怪處**:`OFDM264_Ctl` 自己定義了一支私有的 `ExecPOActionToViewVDB` (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM264_Ctl.cs:284`),而不是用 `BaseController` 的版本 —— 全片只有這一支這樣做。改 Control 基底時不會改到它。

### 4.5 `OFDM281` 基金收益分配(配息)設定

用途(推測):設定某檔基金某年度某期別的**配息參數** —— 分配基準日、權值扣除日、發放日、再投資日、配息基準單位數、總分配權值、匯費郵費收取方式、再投資手續費率; 外加兩張明細:配息來源別(`OFD287A`)與各扣繳類別的可扣抵稅率(`OFD288A`)。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD281A`(`FUND_ID` + `YEARS` + `ISSUE_CODE`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:43` |
| 明細 | `OFD287A` 配息來源、`OFD288A` 扣抵稅率 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:48-49` |
| 唯讀結果集 | `OFDM281_Before`(上一期參數,帶預設值用)、`OFDM281_RateBase`(受益人扣繳類別清單) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM281Model.xsd` |
| EVA 掛點 | 只有 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:44-46` |

#### 日期先後鏈(這一支最實質的卡控)

```
最後過戶日 ≤ 分配基準日 < 權值扣除日
                 分配基準日 < 發放日期 ≤ 再投資日期
```

| 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 分配基準日 ≥ 最後過戶日期 | 分配基準日 必須大於等於 最後過戶日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:66` |
| 權值扣除日 > 分配基準日 | 權值扣除日 必須大於 分配基準日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:82` |
| 發放日期 > 分配基準日 | 發放日期 必須大於 分配基準日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:90` |
| 再申購日期 ≥ 發放日期 | 再申購日期 必須大於等於 發放日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:97` |
| 年度格式 | 年度 輸入格式錯誤 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:111` |
| 配息基準 > 0 | 配息基準 必須大於0 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:117` |
| 至少一筆配息來源明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:58` |
| `ValidateBASE_DATE` 伺服端複核 | 依回傳 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:105`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM281_Ctl.cs:827` |
| **作業處理碼 ≠ 0(已產生配息資料)時不得修改** | 已產生配息資料,不得修改 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399-403` |
| **作業處理碼 ≠ 0 時不得刪除** | 已產生配息資料,不得刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776-780` |

**最後兩列是一個「成對路徑只改一邊」的實例。**兩段做同一件事,寫法卻不同:

|  | 修改路徑 | 刪除路徑 |
|---|---|---|
| 取值 | `Int32.TryParse(this.ucomPROCESS_CODE.Value.ToString(), out r) && r != 0` | `Convert.ToInt32(this.ucomPROCESS_CODE.Value) != 0` |
| 值為空 / null 時 | `TryParse` 失敗 → 不擋,正常往下 | `Convert.ToInt32` 丟 `FormatException` / `InvalidCastException` |
| 錨點 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776` |

而且兩段上方都各留了一份**被註解掉的舊版檢核**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:389`、 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:767`),訊息是「作業處理碼 不為尚未處理時,不得修改／刪除」。修改路徑被硬化成 `TryParse`,刪除路徑沒跟上。

### 4.6 `OFDM331` 客訴案件維護

用途(推測):登錄一件客訴 —— 對象(受益人 / 潛在客戶 / 通路推薦人)、客訴代碼與內容、指定處理部門、處理說明與處理種類、確認時間。四張明細分成「客訴側」與「處理側」各兩張。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | **`BasicEVAPO`**(舊世代) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:22` |
| 主檔 | `OFD331`(PK `COMPLAIN_NO`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:32` |
| 明細 | `OFD332` 客訴代碼、`OFD333` 客訴內容、`OFD334` 處理說明、`OFD335` 處理種類代碼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:34-37` |
| live / 註解比 | 全檔 808 行,其中 **391–805 行包在 `/* */` 裡**(舊的 `Add` / `Select` override) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:390-806` |

#### 依客訴對象種類分支的必填(UI)

| `COMPLAIN_TYPE` | 必填欄位 | 訊息 | 錨點 |
|---|---|---|---|
| 受益人 | `BF_NO` + `ID_NO` | 若'客訴對象'為'受益人',戶號為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:293`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:298` |
| 潛在客戶 | `PR_NO` | 若'客訴對象'為'潛在客戶',潛在客戶序號為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:305` |
| 通路推薦人 | `SPONSOR_CODE` + `CHANNEL_CD` + `CHANNEL_CODE` | 若'客訴對象'為'通路推薦人',推薦人代碼為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:312-322` |
| 任何 | 沒選指定處理部門就要填處理內容 | 若無選擇指定客訴處理部門,請輸入'客訴處理內容' | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:287` |

全部是**阻擋**。

#### `BeforeAdd` 取客訴序號:四個問題疊在 60 行裡

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:98-157`:

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | 三個明細 row 建了卻沒加進 DataTable | `NewOFDM331_ComplainRow()` 等三個新 row 從頭到尾沒有 `Add*Row`,`COMPLAIN_NO` 設在孤兒物件上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:103-105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:135-140` |
| 2 | 條件寫成同一式 OR 兩次 | `if (row.COMPLAIN_NO != string.Empty \|\| row.COMPLAIN_NO != "")` —— 兩邊完全相同,等於只寫一次;看得出原意是 null 檢查 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:118` |
| 3 | 在 `Before*` 掛點裡 `args.DbTran.Rollback()` 後再 `throw` | 違反掛點規約(`architecture.md §3`);引擎外層還會再 rollback 一次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:122-123` |
| 4 | `catch` 吞掉例外後**正常返回** | `HandleBusinessException(ex)` + `ptpfTX.Rollback()`,方法照樣 return,引擎會帶著空的 `COMPLAIN_NO` 繼續 INSERT | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:143-148` |
| 5 | 取號無次數上限 | `while (IsExistComplain_No(...)) { 重取 }` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:130-133` |

問題 1 值得展開。**被註解掉的舊版是對的**:它在取號前先判斷 `Rows.Count > 0`, 把 `row_D` 重新指向 `Rows[0]`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:459-474`), 而且處理四張明細(含 `OFDM331_Solve_K`)。live 版只剩三張、也不再重新指向。 **假設**:新客訴案件的明細 `COMPLAIN_NO` 會拿到 UI 送過來的空字串,與主檔對不上。依據是上述兩段的差異,以及 `OFDM331_Ctl` 的 view→model 搬移是逐表複製、不從主檔補鍵 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM331_Ctl.cs:205-215`)。這一條沒有現場驗證,但同一支畫面正確的寫法就在旁邊的 `OFDM337`(§4.7),可以對照。

### 4.7 `OFDM337` 交易退件維護

用途(推測):登錄一筆**退件**(文件不齊或不符而退回給客戶),含退件原因、退件項目(可複選)、退件地址、文件補齊日期。`OFD346A` 明細是勾選出來的退件項目清單。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD337A`(PK `REJ_NO`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:46` |
| 明細 | `OFD346A` 退件項目(PK `REJ_NO` + `REJ_ITEM`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:47` |
| 唯讀 | `OFD041` 範本內容(勾選帶入備註) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM337Model.xsd` |
| EVA 掛點 | `BeforeAdd` + 三個 Before 取數 + 8 個跳號 After | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:41-60` |

#### `BeforeAdd` 取號 —— 這一支做對了

```
if (row.REJ_NO == string.Empty)
    do {
        row.REJ_NO = genSrNo.GetRejNo();
        foreach (明細 row_dtl)
            if (row_dtl.RowState != DataRowState.Deleted)
                row_dtl.REJ_NO = row.REJ_NO;     // 真的寫回 DataTable 裡的列
    } while (IsExistByData(...));
```

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:111-131`。與 §4.6 的 `OFDM331` 對照: **同一個需求(主檔取號後把號碼灌進明細),`OFDM337` 走的是真正在 DataTable 裡的列,`OFDM331` 走的是孤兒列。** `OFDM337` 還多做兩件事:`REJ_NO` 已有值就不重取(支援由別的畫面帶入)、跳過已刪除的列。唯一相同的毛病是取號重試沒有次數上限。

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 至少勾選一筆退件項目 | 至少須勾選一筆退件項目 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:83` |
| 存檔前 | 退件日期不可空白 | 退件日期不可為空白 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:93` |
| 存檔前 | 客戶統編邏輯 | X 不符合正常邏輯,是否忽略? | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:44-64` |
| 存檔前 | 聯絡人統編邏輯 | 同上 | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:89` |
| 執行後 | 伺服端回傳訊息 | 依 `Result[0].ReturnMessage` | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:507-509` |

**一個 copy-paste 漏改**:聯絡人統編那一次呼叫傳的欄位名稱是 `this.custCNT_ID_NO.Text`(**控件自己的內容**)而不是對應的標籤文字 (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:90`,對照上一行 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:89` 傳的是 `this.ulblID_NO.Text`)。訊息會變成「(統編值)不符合正常邏輯,是否忽略?」,使用者看不出是在講聯絡人。

新增成功訊息由 Ctl 組:「新增成功,退件單號:{0}」 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM337_Ctl.cs:53-54`)。這一行沒有先檢查 `Result.Count`,直接讀 `Result[0]` —— 與 `architecture.md §6` 記的 `CASM001_Ctl` 同型, 本片另有 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM221A_Ctl.cs:59`、 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:61`、 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM270_Ctl.cs:49` 三處相同寫法。

### 4.8 `OFDM271` 缺件到件／回復登錄

用途(推測):把已到件的缺件打勾、填到件日期,一次執行;或反向把誤登的到件日期**回復**成空白。代號是 `M`,行為是 B。

#### 為什麼它的主檔不是真的

| 事實 | 證據 |
|---|---|
| PO 宣告 `MasterTable = OFD724` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32` |
| **全支程式只有這一行提到 `OFD724`** | UI / Ctl / PO 三層 grep `OFD724` 只有一處命中 |
| `BeforeSelect` 把 `args.DbCmd` 整個換掉,SQL 打的是 `OFD272A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:363-372`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:243-283` |
| vdb `OFDM271` 的欄位與 PK 完全是 `OFD272A` 的 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM271Model.xsd` |
| UI 繼承 `xOneStepProcessForm`,不是 `xMaintainForm` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28` |
| Ctl 只有 `Execute` 與 `Query` 兩個業務方法,沒有 Add / Modify / Verify / Approve | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM271_Ctl.cs:45`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM271_Ctl.cs:59` |

**結論**:`xTableMapping("OFD724", ...)` 只是為了讓框架有個主檔名可填, `OFD724` 在這一支完全沒有被讀也沒有被寫。掃描器把它列成 `OFDM271` 的主檔是字面比對的結果。 `OFD724` 真正的主檔持有者是 `OFDB327` / `OFDM723` / `OFDM724`,**都在 OFD9 那一片,另見 `ofd9.md`**。

#### 查詢(`BuildMasterSQLString`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:238-361`)

`OFD272A` join `OFD039A`(缺件代碼)join `BMS001`(受益人)left join `OFD251A`(買回書), 再依畫面上的「執行別」單選鈕加條件:

| 執行別 | 加的條件 | 結果類型 | 錨點 |
|---|---|---|---|
| 到件登錄(`ExecType='1'`) | `GET_COPY_DATE` 為空 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:271` |
| 到件回復(`ExecType='2'`) | `TRN_CD<>'3' OR (TRN_CD='3' AND OFD251A.DOC_NID<>'Y')` | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:277` |
| 缺件種類篩選 | `TRN_CD IN ('1','5')` 或 `NOT IN ('1','5')` | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:280-282` |

第二列是 **Oracle 三值邏輯的典型踩法**:`OFD251A.DOC_NID <> 'Y'`,`DOC_NID` 為 NULL 時整條是 UNKNOWN, 那筆買回缺件就從清單上消失。程式作者自己在同一行註解寫「DOC_NID可以是空白或N」—— **知道它可能不是 `'Y'`,但沒想到它可能是 NULL**。而且這是 left join 來的欄位,沒有對應買回書時必定是 NULL。

#### 執行(`Execute`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:50-227`)

| 步 | 條件 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | `ExecType='2'` | 先查 `OFD251A`,若 `DOC_NID='Y' AND STOP_PAY_YN='Y'` 就整批 rollback | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:77-91` |
| 2 | `ExecType='2'` | `UPDATE OFD272A SET GET_COPY_DATE=' ', GET_COPY_UID=' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113` |
| 3 | `STOP_PAY='Y'` 且 `TRN_CD` 是贖回轉換 | `UPDATE OFD251A SET DOC_ADATE=' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:118-126` |
| 4 | `ExecType='1'` | `UPDATE OFD272A SET GET_COPY_DATE=<畫面值>` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` |
| 5 | `TRN_CD` 是開戶或受益人異動 | `UPDATE OFD607A SET PROCESS_YN='Y'`(解鎖網路交易) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:153-168` |
| 6 | `STOP_PAY='Y'` 且贖回轉換,且該書號已無未到件 | `UPDATE OFD251A SET DOC_ADATE = (SELECT MAX(GET_COPY_DATE) …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:171-199` |

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前(UI) | 至少勾一筆 | 至少須註記一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:76` |
| 執行前(UI) | 到件日期格式 | 到件日期 格式不符 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:91` |
| 執行前(UI) | 到件日期須為公司營業日 | 到件日期 必須為公司的營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:110` |
| 執行前(UI) | 到件日期 ≥ 缺件日期(僅到件登錄) | 到件日期 必須大於等於 缺件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:118` |
| 執行中(PO) | 已通知保管銀行付款 | X 此贖回付款資料已通知保管銀行付款,不可回復到件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:89` |
| 執行中(PO) | `OFD272A` 更新筆數 ≠ 1 | **空字串** | 阻擋(訊息空白) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:112`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:149` |
| 執行中(PO) | 任何例外 | **空字串** | 阻擋(訊息空白) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:210`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:218`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:224` |

**五個失敗出口裡有四個回傳空訊息。**使用者只會看到一個沒有內容的錯誤框。成功時回的筆數 `Convert.ToInt32(j)` 也不是更新筆數,而是**最後一次 `ExecuteScalar` 的結果** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:205`); 若這次執行沒有走到任何 `ExecuteScalar`,`j` 是 null,回傳 0 筆卻是成功。

### 4.9 `OFDM242` 投資組合(契約)贖回維護

用途(推測):針對**投資組合 / 契約**(畫面標籤「投資組合」`PORTFOLIO_CODE`、「契約書號」`EC_RSP_NO`) 一次建立多筆贖回。是 `OFD251A` 在本片的第二個建檔入口。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | **`MultiRowEVAPO`**(舊世代多筆) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:23` |
| 主檔(三個) | `OFD251A` `OFD252A` `OFD254A` 全部掛 `MasterTable.Add` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:33-35` |
| xsd DataTable 名 | `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`(§2.1) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM242Model.xsd` |
| EVA 掛點 | `BeforeAdd` `BeforeSelect` `BeforeApproveDelete` `AfterApproveDelete` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:37-40` |

#### 這一支跑不動(**假設**,依據如下)

| 依據 | 錨點 |
|---|---|
| `MultiRowEVAPO` 的 `dbTA` / `dbPTPF` 在建構子裡**被註解掉不賦值** | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175` |
| `MultiRowEVAPO.Add` 第一行就 `cn = dbTA.CreateConnection()` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:187` |
| `OFDM242_PO` 自己的 `m_db` 也被註解成 null,卻在 `GetMasterData` 直接 `m_db.CreateConnection()` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:31-32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:188-190` |
| `BeforeApproveDelete` 的 SQL 是**整段 T-SQL 批次**:`DECLARE @FUND_ID VARCHAR(10)`、游標 + `@@FETCH_STATUS`、`SqlDbType.NVarChar` 參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:63-131` |
| 查詢 SQL 用 `CONVERT(VARCHAR(10), …, 111)` 與 `@REDEM_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1192`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1233-1235` |

連線欄位為 null 會先丟 `NullReferenceException`;就算連上了,Oracle 也不吃 T-SQL 批次。 **要推翻這個判斷只需要在現場按一次查詢。**

#### 卡控總表(UI 層,仍完整)

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 收件日期須為營業日 | 收件日期 不為營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:110` |
| 存檔前 | 至少一筆明細 | 明細至少需輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:116` |
| 存檔前 | 匯入帳號必填 | 基金 X 匯入帳號 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:132` |
| 查詢前 | 七個條件擇一 | 收件日期、贖回日期、受益人ID、受益人戶號、投資組合、贖回書號、契約書號 必須擇一輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:158` |
| 挑基金時 | 受益人仍有缺件 | 受益人仍有缺件資料,不可贖回 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:502` |
| 挑基金時 | 受益人被列管禁止贖回 | 受益人 X … 被列管禁止贖回基金 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:509` |
| 挑基金時 | 基金停止贖回 | 基金[X]停止贖回!請查 OFDM114 受益人停止申贖設定檔。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:516` |
| 挑基金時 | 基金暫停贖回 | 基金[X]暫停贖回!請查 OFDM087 基金暫停申贖日期設定檔。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:523` |
| 挑基金時 | 無可贖回單位數 | 無可贖回單位數 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:537` |
| 新增前 | 該贖回日該基金已過帳 | 贖回日期[X] 已執行 基金 Y 過帳,無法再新增資料。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:604` |
| 刪除前 | 已過帳 | 基金 X 已過帳,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:621` |

這些訊息裡直接寫出別的畫面代號(`OFDM114` / `OFDM087`)—— 對使用者友善,但也代表 **這兩支設定畫面改代號的話,訊息字串要一起改**。

### 4.10 `OFDM220` 與 `OFDM232` — 一對只改了一半的彙總畫面

`OFDM220`(申購彙總)與 `OFDM232`(買回彙總)是結構完全對稱的一對: 同樣以「基金 + 銷售機構 + 日期」為主鍵,同樣沒有明細,同樣在存檔時更新過帳控制檔 `OFD303A`。但兩邊的實作有**三處不對稱**:

| 面向 | `OFDM220` | `OFDM232` | 影響 |
|---|---|---|---|
| 掛在哪個事件 | `AfterAdd`,且註解寫明「20090331 by lichyu BeforeAdd改到AfterAdd」,舊的 `BeforeAdd` 訂閱留在註解裡 | **仍然掛 `BeforeAdd`** | 主檔還沒寫入就先動控制檔;失敗時控制檔已改 |
| SQL 參數 | `AddInParameter` 綁 `UPDATEID` / `UPDATEDATE` / `FUND_ID` / `CTL_DATE` | `string.Format` 直接把 `FUND_ID` 與日期串進 SQL | 注入面;且型別轉換靠字串 |
| 更新者欄位 | `SET ALLOT_CTL_CODE='1', UPDATEID=:UPDATEID, UPDATEDATE=:UPDATEDATE` | `SET REDEM_CTL_CODE = '1'`(**沒寫更新者**) | 買回側改動查不到是誰改的 |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:47-48`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:113-131` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:48`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:121-131` |  |

#### 卡控總表(兩支合併)

| 畫面 | 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `OFDM220` | 存檔前 | 銷售總手續費 ≥ 銷售機構手續費 | 銷售總手續費 不得小於 銷售機構手續費 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:200` |
| `OFDM220` | 查詢前 | 申購日期起訖成對且不倒置 |  | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:216-221` |
| `OFDM220` | 存檔前 | 基金已關閉 | 依 `FundCloseMsg` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:379-384` |
| `OFDM220` | 存檔前 | 基金 / 日期相關伺服端檢核 | 依 `strErr` | 阻擋 / 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:239`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:284-338` |
| `OFDM232` | 存檔前 | 金額 / 單位數擇一必填 | (單位數買回)總單位數 與 (金額買回)總金額 至少擇一輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:184-192` |
| `OFDM232` | 存檔前 | 短線交易費率未設定 | 短線交易費率 尚未設定 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:527` |
| `OFDM232` | 存檔前 | 該買回機構不檢核基金彙總 | 此買回機構不檢核基金彙總,是否仍要輸入 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:595` |
| `OFDM232` | 存檔前 | 基金已關閉 | 依 `FundCloseMsg` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:475-480` |

「短線交易費率 尚未設定」這條把 `OFDM232` 與 `OFDM233`(§4.13)綁在一起: 沒有先在 `OFDM233` 建好費率,這裡只會**警示**,不會擋。

### 4.11 `OFDM302` 基金淨值維護

用途:每日建立 / 修改基金的正式淨值、申購淨值、贖回淨值、資產規模、發行單位數。多筆型畫面,一次可以貼一整批基金。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseMultiRowEVADaoPO, IOFDM302_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:29` |
| 主檔 | `OFD302A`(`FUND_ID` + `NAV_DATE`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| EVA 掛點 | `BeforeSelect` `BeforeUpdate`(共用 `BeforeUD`)`BeforeGetMaintainData` `BeforeGetToDoData` `BeforeAdd` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:34-38` |

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 至少一筆明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:41` |
| 存檔前 | 淨值日須為該基金營業日 | yyyy/MM/dd 不為基金[X] 之營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:57` |
| 存檔前 | 基金須屬所選基金公司 | 所挑選的基金代碼[X] 不為該基金公司[Y] 所屬的基金 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:64` |
| 存檔前 | 基金已成立 | 基金代碼[X]尚未成立 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:72` |
| 存檔前 | 淨值日 ≥ 基金成立日 | 淨值日期不可小於基金代碼[X]的成立日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:80` |
| 查詢前 | 淨值日期起 ≤ 迄 | 淨值日期(起) 不可大於 淨值日期(迄) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:220` |
| 刪除前(按鈕) | 有鎖定淨值 | 刪除資料中有已鎖定淨值資料,無法刪除,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:265-268` |
| 刪除前(刪列) | 有鎖定淨值 | 同上 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:353-357` |

兩處刪除卡控的訊息完全一樣,判斷寫法不同(按鈕層 `DataTable.Select("NAV_LOCK='…'")`、列層 `row.NAV_LOCK == NAV_LOCK.Lock`)。與 §4.1.3 同型:改一邊要記得改兩邊。

有一條**被註解掉的檢核**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:55` (「淨值日 不存在於 基金代碼[X] 之營業日」)。它與下一行 live 的版本語意相同, 只是訊息寫法不同 —— 屬於重寫後忘了刪,不是功能缺口。

### 4.12 `OFDM361` — 一支沒宣告主明細的空殼

`OFDM361` 是本片唯一「六層檔案齊全但沒有主明細宣告」的畫面。**原因不是漏寫,是根本沒實作。**

| 層 | 行數 | 內容 |
|---|---|---|
| UI | 66 | 繼承 `xMaintainForm`,六個生命週期事件**全部空的**,只有 `DoValidate()` 呼叫 `validatorManager1.DataValidate()`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM361.cs:19-56`) |
| FormProxy | 11 | `public class OFDM361_Pxy : Basic_Pxy { }` —— 空類別(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM361_Pxy.cs:8-10`) |
| Control | 10 | `public class OFDM361_Ctl { }` —— **連 `BaseController` 都沒繼承**(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM361_Ctl.cs:7-9`) |
| PO | 11 | `public class OFDM361_PO : BasicEVAPO { }` —— 空類別,沒有 `MasterTable`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10`) |
| DataEntity | 655 | 一張 DataTable `OFDM361`,103 欄,PK `PR_NO` |
| UIEntity | 655 | 與 Model 同構 |

**但 Designer 是完整的。**`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM361.Designer.cs` 有 653 行、 26 個中文標籤,包含「潛在客戶序號」「投資偏好」「每月可投資金額」「年平均所得」「DM寄送碼」「受益人類別」「教育程度」「預期投資時間」「服務業別」等 —— 這是一張**潛在客戶維護**的畫面。

xsd 的欄位清單(`PR_NO` `USAGE` `BF_NO` `EMP_NO` `ID_NO` `PR_NAME` `BIR_DATE` … `INVST_TEND_CD` `MIN_INVEST_CODE` `INVEST_AMT_CODE` `ANNUAL_INCOME`)與 `CRM003A` 高度重疊, 而 `CRM003A` 的主檔畫面是 `CASM001` 與 `CRMM003`(`cas.md §4`)。

**結論(推測)**:`OFDM361` 是從 CAS / CRM 的潛在客戶維護畫面複製過來、 UI 與 entity 做完、Control / PO / Pxy 三層還沒寫就停住的半成品。 **沒有主明細宣告 = 它從來沒有被接上資料庫**,不是設定漏掉。依據:三層都是零成員的空類別,而不是「有成員但沒宣告 MasterTable」; 以及 `OFDM361_Ctl` 連基底類別都沒寫,任何 Pxy 呼叫都編不出來。

實務上的處置建議只有兩條路:**當作死碼移除**,或**補完三層**。在那之前,`atlas_scan.py --screen OFDM361` 回「主檔 —」是正確的,不要去補一個假的 `xTableMapping`。

### 4.13 其餘 12 支(表格帶過)

| 畫面 | 主明細 | 四眼 | 主要卡控(一句話) | 特別之處 |
|---|---|---|---|---|
| `OFDM091` | `OFD091A` / `OFD092A` | 有 | 費率 < 100、起算日 ≤ 終止日、起算日與終止日皆須 > 0、基金代碼必填 | 與 `OFDM233` 是同一張樣板做出來的兩支(主檔皆 `FUND_ID` + `RANGE_TYPE`,明細皆 `BNG_DAY` / `END_DAY` 區間),差別只在費率欄位;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM091.cs:63-92` |
| `OFDM233` | `OFD260A` / `OFD261A` | 有 | 下限 ≤ 上限、費率 < 100、起算日 ≤ 終止日 | 短線交易費率的唯一來源,`OFDM231A` 與 `OFDM232` 都吃它;PO 內 307–466 行整段註解(舊 SQL Server 版);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM233.cs:77-102`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:307-466` |
| `OFDM243A` | `OFD243A` | 有 | **只有一條**:配單金額不得為 0 | `OFD243A` 的主檔持有者,但同一張表被 `OFDM221A` / `OFDM231A` 當明細寫;PO 只有三個取數掛點,零副作用;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM243A.cs:123`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:39-42` |
| `OFDM270` | `OFD270A` | 有 | 處理完成日期必填且 ≥ 退郵日期、永久失聯日期必填、非退郵戶不可設永久失聯 | 有完整 8 個 After 掛點但都只寫跳號;`OFD270A` 實體只有 2 欄(`BF_NO` / `REJ_STOP_DATE`),vdb 43 欄其餘都是 join 來的;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM270.cs:48-59`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM270.cs:464` |
| `OFDM284` | `OFD286A` | 有 | 依伺服端 `Result` 回傳訊息掛在戶號欄位上 | **舊世代 `MultiRowEVAPO`**;SQL 用 `[BMS001]` `[OFD286A]` `[LOG106]` 方括號;xsd 帶一張叫 `LOG` 的表(對 `LOG106`)但 `MasterTable.Add` 那行被註解;錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:38-39`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:415-433` |
| `OFDM285` | `OFD290A` | 有 | **只有一條**:明細資料 必須輸入 | **舊世代 `MultiRowEVAPO`**;PO 只有 217 行、三個取數掛點;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM285_PO.cs:83` 會檢查 `Result[0].ReturnCode`,是舊世代裡少見的;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM285.cs:38` |
| `OFDM286` | `OFD291` | 有 | 必填欄位、申請日期 ≤ 終止日期、**同一基金僅可有一筆生效中資料** | 最後一條在兩個地方各寫一次(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:307` 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:328`),分別對應新增列與修改列,兩段判斷各自獨立 —— 又一個「改一邊要改兩邊」 |
| `OFDM297` | `OFD297A` | 有 | 兩個淨值日期必填、變更前 < 變更後、至少勾一檔基金 | `BeforeAdd` + 6 個 After 掛點;失敗訊息由伺服端逐列回傳並掛到 grid 上(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM297.cs:174`),是本片唯一「逐列回報」的畫面;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM297.cs:148-157` |
| `OFDM300` | `OFD300` | 有 | **只有一條**:匯率必須大於 0 | 與 `OFDM301` 成對;用 `Convert.ToDecimal` 判斷;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM300.cs:147-153` |
| `OFDM301` | `OFD301` | 有 | 兌換入 ≠ 兌換出、匯率必大於 0 | 與 `OFDM300` 成對,但**用 `Convert.ToDouble` 判斷金額類欄位**,訊息也少一個字(「匯率必大於0」);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM301.cs:148-157` |
| `OFDM321` | `OFD321` / `OFD322` | 有 | 總額度 > 0、至少一筆明細、**各通路額度加總須等於控管總額度**、控管起 ≤ 迄 | **舊世代 `BasicEVAPO`** + `[OFD321]` / `[OFD322]` 方括號 SQL;它維護的額度被 `OFDM221A` 的 `ChkFundQuota` 讀去,但那邊只詢問不擋(§4.1.2);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM321.cs:135-173`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163-181` |
| `OFDM344` | `OFD344` | 有 | **UI 沒有任何業務檢核**,只有 `validatorManager1` 的欄位驗證 | **舊世代 `BasicEVAPO`**;`BeforeAdd` / `AfterAdd` 有掛但 live 段只組 SQL;251–459 行整段註解(含另一份 `Add` / `Select` override);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM344.cs:206`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:250-459` |

#### 這 12 支的共同形狀

1. **卡控條數與資料重要性不成比例。**`OFDM300` / `OFDM301` 是全庫金額計算的基礎, 卻各只有一到兩條檢核;`OFDM264`(媒體檔格式)反而有二十幾條。

2. **`OFD270A` 的 vdb 是個「拼出來的表」。**實體只有 2 欄,畫面上 43 欄裡有 41 欄來自 `BMS001` 等 join, **改這些欄位改不到任何東西**(它們沒有進 `xTableMapping` 的寫入路徑)。

3. **舊世代那幾支的 UI 檢核仍然完整。**`OFDM321` / `OFDM344` / `OFDM284` / `OFDM285` 的 UI 層是活的, 只有 PO 層跑不動。這代表使用者會看到正常的畫面、正常的檢核,然後在按下存檔的那一刻才失敗。

## 5. 查詢畫面(I)

**本片無 I 畫面。**

原因:`DataEntity.OFD8` 是 `ATLAS.OFD` 專案內 entity 的**第八個分卷**,而 OFD 的查詢畫面(`OFDIxxx`) 依鐵律住在 `.Query` 專案 —— `Dev/ATLAS.OFD.Query/Source/` 與 `Dev/ATLAS.OFDI/Source/` (`architecture.md §2`)。那兩個專案有自己的 `QueryDataEntity.OFD` / `DataEntity.OFDI`, 不會出現在本片的 entity 目錄裡。

與本片相關、但住在別處的查詢畫面有兩支值得知道:

| 畫面 | 位置 | 與本片的關係 |
|---|---|---|
| `OFDI011` | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` | 讀 `OFD272A` 做缺件查詢(`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2465-2488`),條件與 `OFDM271` 的清單不同步 |
| `OFDI911` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs` | 用 SP 的 RefCursor 出參名 `RES_OFD272A` 撈缺件(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:79`) |

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**

原因同 §5:OFD 的批次畫面(`OFDBxxx`)分散在 `Dev/ATLAS.OFDB/`(結帳、過帳、產檔) 與 `Dev/ATLAS.EC/`(`OFDB6xx` 服務型,含三支 WindowsService),entity 也在各自的分卷。全庫只有四支 B 畫面配了獨立 Windows 服務,沒有一支屬於 OFD8(`architecture.md §6`)。

但這 24 支是**批次的上游**,關係如下(依表推得,不是程式呼叫):

| 本片寫的表 | 讀它的批次(在別的片) |
|---|---|
| `OFD220A` / `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDB310` `OFDB331` |
| `OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` | `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` |
| `OFD272A` | `OFDB310`(申購缺件)、`BMSM004` / `BMSM006`(受益人側) |
| `OFD281A` / `OFD287A` / `OFD288A` | `OFDB281`(配息計算) |
| `OFD297A` | `OFDB002` |
| `OFD337A` | `OFDB002` 之外未見批次讀取 |
| `OFD264A` / `OFD265A` / `OFD266A` | 付款媒體檔產檔程式(repo 內未定位到唯一呼叫端) |
| `OFD724` | `OFDB327`(**在 OFD9 那一片**) |

`OFD303A` / `CTL012` / `CTL022` 三張控制檔是本片與批次之間**真正的握手機制**: M 畫面把控制碼從 `0`(無資料)推到 `1`(有資料),批次跑完再推到 `2` / `3` / `4`。本片只寫 `'1'` 這一段,不會自己把它推到已結轉。

## 7. 報表(R)

**本片無 R 畫面,`Dev/ATLAS.OFD/` 底下也沒有任何 `.rpt`。**

原因:報表依鐵律住在 `ATLAS.<模組>.Report` 專案(`architecture.md §6`), 對 OFD 來說是 `Dev/ATLAS.OFD.Report/`,是另一個 solution 專案,entity 不在 `DataEntity.OFD8`。

本片的資料會出現在別模組的報表裡,實測到一支:

| rpt / 報表畫面 | 位置 | 取本片哪張表 |
|---|---|---|
| `NFDR813` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:86-97` | `OFD272A`(`TRN_CD = '1'` 且未到件的受益人) |

## 8. 跨模組共用

```text
[圖] OFD8 的跨模組接觸面:申購四張表給 BBS、缺件檔給 BMS 與 RSP、OFD724 掛名主檔
圖中文字:A 組:申購四張表借給 BBS——OFD 這邊有四個建檔入口 / OFDM221A〔OFD8〕 / 正常開單 主檔持有者 / OFD220A OFD221A / OFD234A OFD235A / BBSM013 BBSM113〔BBS〕 / 轉讓過戶 也會 INSERT / bbs.md 對得上 / 差在附屬表與轉換開單 / A 組補充:bbs.md 沒看到的兩件事 / OFDM231A 轉申購 / 也會新開一張申購書 / SrNo.AllotNoForNfdS / 轉換用另一組流水號 / OFD220A_AGENT OFD136A / 兩張附屬表 BBS不建 / OFD221A 四種形狀 / 改欄位要同步四份xsd / B 組:OFD272A 缺件——六個入口寫、一個入口結案、沒有主檔 / OFDM221A OFDM231A / TRN_CD = 2 / 3 / BMSM004 BMSM006〔BMS〕 / TRN_CD = 1 / 5 / RSPM004 RSPM005〔RSP〕 / TRN_CD = 4 / 6 / OFD272A / 沒有主檔畫面 / B 組的結案路徑:唯一出口不走四眼 / OFDM271 / 直接 UPDATE 到件日 / OFD251A.DOC_ADATE / 缺件到齊才放行付款 / OFD607A PROCESS_YN / 解鎖網路交易 / Utility_PO / 缺件超天數就擋交易 / C / D 組:本片內部共用,與一張只是掛名的主檔 / OFD243A〔本片共用〕 / 三支寫 卡控強度不一 / OFD724 / OFDM271 不讀不寫 / OFDM723 OFDM724〔OFD9〕 / 真正的主檔持有者 / 另見 ofd9.md / 本片只能講到這裡
```

*圖:圖 5 跨模組。橘框=本片的主檔或關鍵表;白框=表與連動欄位;灰虛框=別模組或別片的用法;橘虛框=風險與本文修正 bbs.md 的地方;黑框=共用層或版控外。B 組最值得記:OFD272A 有六個寫入入口,卻只有 OFDM271 一個結案入口,而且那一步不走四眼。*

本片對外的接觸面集中在**四組表**,每一組的「借法」都不一樣。

### 8.1 A 組:`OFD220A` / `OFD221A` / `OFD234A` / `OFD235A` 給 BBS

`bbs.md §8` 已經從 BBS 側寫過這四張表。這裡從 OFD 側補完,並對答案。

#### 從 OFD 側看到的事實

| 表 | 本片的角色 | 誰在寫 |
|---|---|---|
| `OFD220A` | `OFDM221A` 的**主檔** | `OFDM221A`(正常開單)、`OFDM231A`(轉換開單)、`OFDB310`(主檔)、`BBSM013` / `BBSM113`(轉讓開單) |
| `OFD221A` | `OFDM221A` 的第一張明細 | 同上 + `OFDM231A` 的 `RDMING_UNIT` 手寫 UPDATE |
| `OFD234A` | `OFDM221A` 的支票明細 | `OFDM221A`、`BBSM013` / `BBSM113` |
| `OFD235A` | `OFDM221A` 的匯款明細 | `OFDM221A`、`BBSM013` / `BBSM113` |

#### 與 `bbs.md` 對得上的部分

| `bbs.md` 的說法 | 從 OFD 側驗證 | 結論 |
|---|---|---|
| 「`OFD220A` 主檔畫面 `OFDB310` / `OFDM221A`」(`bbs.md §8`) | `OFDM221A_PO.cs:67` 宣告 `MasterTable = OFD220A` | **對得上** |
| 「`BBSM013` / `BBSM113` 會 INSERT `OFD220A` / `OFD221A` / `OFD234A` / `OFD235A`,等於在 OFD 的地盤上開了第二個建檔入口」 | OFD 側沒有任何程式碼防止外來 INSERT;`OFDM221A` 查詢時也不分辨書號來源 | **對得上** |
| 「`OFD234A` / `OFD235A` 沒有主檔畫面」 | 掃描器實測「主檔於:—」,本片也只把它們當明細 | **對得上** |
| 「`OFD221A` 在不同模組裡被當成不同形狀的東西,改欄位要同時看 BBS、OFD、EC 三邊的 xsd」 | 本片再加一種形狀:`OFDM243A` 的 `OFD221A` 只有 7 欄 | **對得上,而且要改四邊** |

#### 對不上、或 `bbs.md` 沒說到的部分

| # | 差異 | 說明 |
|---|---|---|
| 1 | **`bbs.md` 沒提到 `OFDM231A` 也會建 `OFD220A` / `OFD221A`。** | `bbs.md §8` 的表把 `OFDM231A` 列在「明細於」,但沒說它會 INSERT。實際上轉申購會新開一張申購書(§4.3.3),**用的是另一組流水號 `SrNo.AllotNoForNfdS`**。所以 `OFD220A` 的建檔入口是四個不是三個。 |
| 2 | **`bbs.md` 說 `OFD221A` 的欄位定義「12 欄,沒有四眼欄位」;掃描器索引實測是 13 欄。** | 索引來源同樣是 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB672Model.xsd`。這是計數差,不影響結論(該 xsd 版本確實沒有四眼欄位)。 |
| 3 | **本片的 `OFD221A` 有四眼欄位。** | `OFDM221A` 的 `OFDM221A_Detail` 125 欄含完整 8 個四眼檢查欄(§2.2)。`bbs.md` 說「BBS 這邊掛在四眼流程上(所以 `BBSM013Model.xsd` 給它補了四眼欄)」—— 實際上**不是 BBS 補的,OFD 這邊本來就有**;EC 的 `OFDB672` 那份才是精簡版。這一條要修正 `bbs.md` 的因果敘述。 |
| 4 | **`OFD220A` 還有一張 `OFD220A_AGENT` 附屬表,`bbs.md` 沒提。** | 意定代理人(`SHOLDER_ID_NO`),PK 就是 `ALLOT_NO`,只有 `OFDM221A` 寫。BBS 轉讓開單時**不會**建這張 —— 轉讓來的申購書沒有意定代理人資料。 |
| 5 | **`OFD136A`(交易指示代理人)也掛在申購書上,`bbs.md` 沒提。** | 2023 年加的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:75-76` 註解 `20230715 … 9000012360`),PK `TRADE_NO` + `TRADE_TYPE`。同樣地,BBS 轉讓不會建。 |

**綜合判斷**:兩份文件的主結論一致(四張表歸 OFD、BBS 是第二入口、改欄位要多邊同步), 差異集中在「OFD 側後來加了兩張附屬表、而且買回畫面也會開申購書」這兩件 BBS 側看不到的事。第 3 點是 `bbs.md` 的因果寫反了,建議回頭修。

### 8.2 B 組:`OFD272A` —— 四個模組六支畫面共用、沒有主檔

`bms.md` 已從 BMS 側寫過。這一節回答:**這張表到底誰在寫、生命週期怎麼走。**

#### 沒有主檔畫面是事實

掃描器實測「主檔於:—」。全庫**沒有任何 PO 把 `OFD272A` 宣告為 `MasterTable`**, 它永遠以 `DetailTable.Add(new xTableMapping("OFD272A", …))` 的身分存在。

#### 誰在寫(實測全庫)

| 模組 | 畫面 / 程式 | 角色 | 寫什麼 | 錨點 |
|---|---|---|---|---|
| OFD | `OFDM221A` | 明細(vdb `OFD272`) | 申購缺件:`TRN_CD='2'`、`SHORE_ID='2'`、`TRN_NO` = 申購書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:69`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:913-928` |
| OFD | `OFDM231A` | 明細(vdb `OFD272`) | 買回缺件:`TRN_CD='3'`、`TRN_NO` = 買回書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:73`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1155-1176` |
| OFD | **`OFDM271`** | **直接 UPDATE(不走四眼)** | 只改 `GET_COPY_DATE` / `GET_COPY_UID` / `TRN_MEMO` / `UPDATEID` / `UPDATEDATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` |
| OFD | `OFDB310` | 明細 | 申購缺件(與 `OFDM221A` 同一段 SQL 的複製) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB310_PO.cs:1025-1037` |
| BMS | `BMSM004` | 明細(vdb `BMSM004_Lack`) | 開戶缺件 `TRN_CD='1'` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:40` |
| BMS | `BMSM006` | 明細(vdb `OFD272`) | 受益人異動缺件 `TRN_CD='5'` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:111`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1914` |
| BMS | `BMSM001` | 唯讀 | 查缺件 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1007-1008` |
| RSP | `RSPM004` | 明細(vdb `OFD272`) | 小額契約缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80` |
| RSP | `RSPM005` | 明細(vdb `OFD272`) | 定期定額異動缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149` |
| OFD | `OFDI011` | 唯讀 | 缺件查詢 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2465-2488` |
| NFD | `NFDR813` | 唯讀 | 報表 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:86-97` |
| 共用 | `Utility_PO.GetLackData`(類) | 唯讀 | **交易限制判斷**:缺件超過 `OFD039A` 設定的天數就限制申購 / 買回 / 轉換 / 小額 | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130` |

**修正一條前情**:任務描述說 `OFD272A` 被四個模組當明細(`BMSM004` `BMSM006` `OFDM221A` `OFDM231A`)。掃描器實測是**六支畫面、三個模組**(多了 `RSPM004` `RSPM005`),再加上 `OFDM271` 的直接 UPDATE 與 `OFDB310` 的第四個明細入口。

#### 生命週期

| 階段 | 誰 | 動作 | 欄位 |
|---|---|---|---|
| ① 產生 | 六支 M 畫面之一(依交易種類) | 四眼 INSERT | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID` + `LACK_DATE` |
| ② 生效 | 四眼覆核 | **但資料在輸入當下就在了**(§0.2) | `STATUS` |
| ③ 限制 | `Utility_PO` 被各交易畫面呼叫 | 依 `OFD039A` 的 `LIMIT_ALLOT` / `LIMIT_REDEM` / `LIMIT_SWITCH` / `LIMIT_RSP` 與各自的天數,決定是否擋交易 | 讀 `LACK_DATE` |
| ④ 到件 | **`OFDM271`** | 直接 UPDATE,**不經四眼** | `GET_COPY_DATE` / `GET_COPY_UID` |
| ⑤ 連動 | `OFDM271` | 到件後視情況更新 `OFD251A.DOC_ADATE`(買回放行付款)、`OFD607A.PROCESS_YN`(解鎖網路交易) | — |
| ⑥ 回復 | `OFDM271`(執行別 2) | 把 `GET_COPY_DATE` / `GET_COPY_UID` 塞回一個空白字元 | — |
| ⑦ 刪除 | 只能跟著上游交易一起刪(四眼 ApproveDelete) | 沒有獨立的缺件刪除入口 | — |

**三個要記住的結論**:

1. **`OFD272A` 的產生是分散的、消滅是集中的。**六個入口寫進去,只有 `OFDM271` 一個入口把它「結案」。

2. **結案那一步不走四眼。**`OFDM271` 是 `xOneStepProcessForm`,按下執行就直接 UPDATE 落地(§4.8)。所以缺件到件**沒有覆核軌跡**,只有 `UPDATEID` / `UPDATEDATE`。

3. **`TRN_NO` 是多型外鍵,沒有 FK。**要 join 回上游交易,一定要先看 `TRN_CD`。 `OFDM271` 自己就是 left join `OFD251A ON OFD272A.TRN_NO = OFD251A.REDEM_NO` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:262-263`)—— 對 `TRN_CD` 不是 `'3'` 的列這個 join 永遠落空, 然後 `DOC_NID <> 'Y'` 的條件又把它們過濾掉(§4.8、附錄 E-2)。

### 8.3 C 組:`OFD243A` —— 本片內部的三方共用

| 畫面 | 角色 | 說明 |
|---|---|---|
| `OFDM243A` | **主檔** | 券商配單的正規維護入口,卡控只有「配單金額不得為 0」 |
| `OFDM221A` | 明細(vdb `OFD243`) | 開申購書時一起建配單 |
| `OFDM231A` | 明細(vdb `OFD243`) | 轉申購時一起建配單;取消轉換時連帶刪除(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1848-1852`) |

三支都在本片,沒有跨模組。但**三支的卡控強度差很多**: `OFDM243A` 幾乎沒有檢核、`OFDM231A` 在 `BeforeSave` 裡用 `REBATE_YN == "Y"` 決定要不要建 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2116-2130`)。從 `OFDM243A` 改出來的配單不會回頭通知申購書。

### 8.4 D 組:`OFD724` —— 名義主檔,真正的持有者在 OFD9

| 畫面 | 位置 | 角色 |
|---|---|---|
| `OFDM271` | 本片 | `xTableMapping("OFD724", "OFDM271")`,**整支程式只有這一行提到它**(§4.8) |
| `OFDM723` | **OFD9 片** | 主檔 —— **另見 `ofd9.md`** |
| `OFDM724` | **OFD9 片** | 主檔 —— **另見 `ofd9.md`** |
| `OFDB327` | OFD 批次片 | 主檔 |

**從 `OFDM271` 的角度只能講到這裡**:它不讀不寫 `OFD724`。要知道 `OFD724` 真正的欄位、主鍵與業務語意,去看 `ofd9.md` 的 `OFDM723` / `OFDM724` 兩節。 **如果 `ofd9.md` 那邊描述的 `OFD724` 形狀與本片 `OFDM271Model.xsd` 裡的 `OFDM271` DataTable 對不上, 那不是矛盾 —— 是因為本片那張 DataTable 裝的其實是 `OFD272A`。**

### 8.5 本片用到的共用 PO 與工具類

| 類別 | 位置 | 誰用 | 做什麼 |
|---|---|---|---|
| `Utility_PO` | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130` | 各交易畫面 | 依 `OFD272A` + `OFD039A` 算交易限制 |
| `SerialNo` | 無原始碼,從呼叫端反推 | `OFDM221A` `OFDM231A` `OFDM337` `OFDM331` | 取各式書號(`GetAllotNoForNfd` / `GetRdmNoForNfd` / `GetRejNo`) |
| `SrNoCommentProcessor` | 無原始碼,從呼叫端反推 | 本片 6 支 M 畫面的所有 After 掛點 | 跳號一覽表 |
| `ServerBizUtility` / `ServerNfdBizUtility` | 無原始碼,從呼叫端反推 | `OFDM221A`(優惠身份別)、`OFDM220` / `OFDM232`(控制日期) | 業務計算 |
| `ClientBizUtility` | 無原始碼,從呼叫端反推 | `OFDM271` `OFDM221A` `OFDM242` | 用戶端營業日判斷 |
| `EVAUtility` | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs` | `OFDM221A`(**建了沒用**) | 四眼欄位寫入 |
| `xTableHelper` / `xEVAStringHelper` | 無原始碼,從呼叫端反推 | 12 支新世代 PO | 組 SQL 與條件 |
| `TableHelper` / `EVAStringHelper`(舊) | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs` | 7 支舊世代 PO | 同上(參數綁定已全數註解,`architecture.md §3`) |

### 8.6 改動影響面速查

| 你要改 | 一定要一起改 / 一起測 |
|---|---|
| `OFD220A` 或 `OFD221A` 的欄位 | 6 份 xsd(`OFDM221A` `OFDM231A` `OFDM243A` `BBSM013` `BBSM113` `OFDB672`)+ `OFDM231A_PO.cs:1936-2105` 的 156 行手寫指派 + `OFDB310` |
| `OFD272A` 的欄位 | 7 份 xsd(`OFDM221A` `OFDM231A` `OFDM271` `BMSM004` `BMSM006` `RSPM004` `RSPM005`)+ `Utility_PO` + `OFDI011` + `NFDR813` |
| `OFD251A` 的欄位 | `OFDM231A`(93 欄版)+ `OFDM242`(71 欄版)+ 7 支 `OFDB3xx` + `SDMB002` |
| 缺件到件的判斷 | `OFDM271`(兩種空值寫法)+ `NFDR813`(`NVL` 寫法)+ `OFDI011` |
| 短線交易費率 | `OFDM233`(維護)+ `OFDM231A`(計費)+ `OFDM232`(警示) |
| 基金銷售額度 | `OFDM321`(維護)+ `OFDM221A`(只詢問不擋) |
| 過帳控制碼 `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232` **四支各寫各的 SQL**,沒有共用方法 |

## 附錄 A. 資料表總表

本片 24 支 PO 一共宣告 **45 張實體表**(去重)。欄位與主鍵見 §2.2,中文名見 §2.3。「共用」欄標 ✓ 者見 §8。

| # | 表 | 主檔於 | 明細於 | 共用 | 一句話 |
|---|---|---|---|---|---|
| 1 | `OFD091A` | `OFDM091` | — |  | 基金遞延手續費主檔 |
| 2 | `OFD092A` | — | `OFDM091` |  | 遞延手續費率區間明細 |
| 3 | `OFD136A` | **無** | `OFDM221A` `OFDM231A` | ✓ | 交易指示代理人 |
| 4 | `OFD220A` | `OFDM221A` `OFDB310` | `OFDM231A` `OFDB331` `BBSM013` `BBSM113` | ✓ | 申購書主檔 |
| 5 | `OFD220A_AGENT` | **無** | `OFDM221A` |  | 申購書意定代理人 |
| 6 | `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDI059` `SDMB001` | `OFDM221A` `OFDM231A` `OFDB310` `OFDB331` `BBSM013` `BBSM113` | ✓ | 申購明細 |
| 7 | `OFD232A` | `OFDM220` | — |  | 銷售機構申購彙總 |
| 8 | `OFD234A` | **無** | `OFDM221A` `BBSM013` `BBSM113` | ✓ | 申購支票明細 |
| 9 | `OFD235A` | **無** | `OFDM221A` `BBSM013` `BBSM113` | ✓ | 申購匯款明細 |
| 10 | `OFD243A` | `OFDM243A` | `OFDM221A` `OFDM231A` | ✓ | 券商配單 |
| 11 | `OFD251A` | `OFDM231A` `OFDM242` `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` `SDMB002` | — | ✓ | 買回書主檔 |
| 12 | `OFD251A_AGENT` | **無** | `OFDM231A` |  | 買回書意定代理人 |
| 13 | `OFD252A` | `OFDM242` | `OFDM231A` `OFDB331` |  | 買回付款明細 |
| 14 | `OFD253A` | — | `OFDM231A` `OFDB331` |  | 買回轉換(轉申購)明細 |
| 15 | `OFD254A` | `OFDM242` | `OFDM231A` |  | 買回指定沖銷明細 |
| 16 | `OFD258A` | — | `OFDM231A` |  | 買回實體憑證明細 |
| 17 | `OFD259A` | `OFDM232` | — |  | 銷售機構買回彙總 |
| 18 | `OFD260A` | `OFDM233` `OFDB004` | `OFDB004` |  | 短線交易費率主檔 |
| 19 | `OFD261A` | — | `OFDM233` `OFDB004` |  | 短線交易費率區間明細 |
| 20 | `OFD264A` | `OFDM264` | — |  | 付款媒體檔主檔 |
| 21 | `OFD265A` | — | `OFDM264` |  | 媒體檔欄位定義 |
| 22 | `OFD266A` | — | `OFDM264` |  | 媒體檔檔名規則 |
| 23 | `OFD270A` | `OFDM270` | — |  | 永久失聯戶註記(實體僅 2 欄) |
| 24 | `OFD272A` | **無** | `OFDM221A` `OFDM231A` `BMSM004` `BMSM006` `RSPM004` `RSPM005` | ✓ | 缺件檔(§8.2) |
| 25 | `OFD281A` | `OFDM281` `OFDB281` | — |  | 配息設定主檔 |
| 26 | `OFD286A` | `OFDM284` | — |  | 受益人收益分配支付方式 |
| 27 | `OFD287A` | — | `OFDM281` `OFDB281` |  | 配息來源明細 |
| 28 | `OFD288A` | — | `OFDM281` |  | 配息可扣抵稅率明細 |
| 29 | `OFD290A` | `OFDM285` | — |  | 基金匯費設定 |
| 30 | `OFD291` | `OFDM286` | — |  | 受益人配息期間 / 類別 |
| 31 | `OFD297A` | `OFDM297` `OFDB002` | — |  | 臨時放假淨值日期變更 |
| 32 | `OFD300` | `OFDM300` | — |  | 幣別匯率 |
| 33 | `OFD301` | `OFDM301` | — |  | 交叉匯率 |
| 34 | `OFD302A` | `OFDM302` | — |  | 基金淨值 |
| 35 | `OFD321` | `OFDM321` | — |  | 基金銷售額度主檔 |
| 36 | `OFD322` | — | `OFDM321` |  | 各通路額度明細 |
| 37 | `OFD331` | `OFDM331` | — |  | 客訴主檔 |
| 38 | `OFD332` | — | `OFDM331` |  | 客訴代碼明細 |
| 39 | `OFD333` | — | `OFDM331` |  | 客訴內容明細 |
| 40 | `OFD334` | — | `OFDM331` |  | 客訴處理說明明細 |
| 41 | `OFD335` | — | `OFDM331` |  | 客訴處理種類明細 |
| 42 | `OFD337A` | `OFDM337` | — |  | 退件主檔 |
| 43 | `OFD344` | `OFDM344` | — |  | 客戶資料保密設定異動 |
| 44 | `OFD346A` | — | `OFDM337` |  | 退件項目明細 |
| 45 | `OFD724` | `OFDM271`(名義)`OFDB327` `OFDM723` `OFDM724` | — | ✓ | **本片不讀不寫**,見 §8.4 與 `ofd9.md` |

### A.1 不在 `xTableMapping` 裡、但本片會直接下 SQL 的表

這些表不會出現在掃描母體,改它們的欄位不會有任何 xsd 提醒你:

| 表 | 誰動它 | 動作 |
|---|---|---|
| `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232` | UPDATE / INSERT 過帳控制碼 |
| `OFD304A` | `OFDM231A` | UPDATE |
| `CTL012` | `OFDM221A` | UPDATE / INSERT / DELETE 代扣款控制 |
| `CTL022` | `OFDM221A` `OFDM231A` | UPDATE / INSERT / DELETE 櫃台控制 |
| `OFD130A` | `OFDM221A` `OFDM231A` | INSERT 匯款授權書 |
| `OFD131A` | `OFDM231A` | INSERT |
| `BMS004A` `BMS005A` | `OFDM231A` | INSERT 匯款帳號授權 |
| `OFD721` | `OFDM231A` | UPDATE 實體憑證餘額 |
| `OFD607A` `OFD601` | `OFDM271` | UPDATE 網路交易權限 |
| `OFD039A` | `OFDM231A` `OFDM271` | 唯讀 join(缺件代碼與限制天數) |
| `BMS001` | `OFDM221A` `OFDM284` `OFDM271` | 唯讀 join |
| `OFD199A` | `OFDM221A` | 唯讀(行銷活動) |
| `OFD651A` `OFD656` | `OFDM242` | 唯讀(投資組合贖回處理碼) |
| `LOG106` | `OFDM284` | 唯讀(`MasterTable.Add` 那行被註解) |

## 附錄 B. SP / Function / Trigger / View

本片幾乎不用 DB 物件。全 24 支只出現三個名字,**三個都在版控外,repo 內看不到內容**:

| 物件 | 型別 | 呼叫端 | 用途(從參數反推) |
|---|---|---|---|
| `S_TA_OFDM221A_Get` | Procedure | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2410` | 吃 `striRule='1'`,回一個 RefCursor 灌進 `OFD221A_RULE`(四個欄位 `RULE1`–`RULE4`)—— 畫面上顯示的申購規則文字 |
| `S_TA_UPD_REDEM_SHORT_RMK` | Procedure | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2463` | 更新買回的短線交易註記;呼叫前先用一段 `SELECT COUNT(*) FROM dual WHERE EXISTS(...)` 判斷要不要叫 |
| `f_TA_GetEmpLockUnitsOnTheDay` | Function | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:200` | 吃 `(BF_NO, FUND_ID, 日期, '4')`,回員工 / 員眷閉鎖單位數 |

另外 `f_TA_GetBusinessDay` 出現在共用的 `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1116-1128` (算缺件超過幾個營業日就限制交易),不是本片自己叫的。

**沒有 Trigger、沒有 View、沒有 `.rpt`。**

## 附錄 C. 代碼對照(狀態碼、型別碼)

完整清單見 §2.5。這裡只補三張本片高頻、但常被搞混的對照:

### C.1 `TRN_CD` 缺件種類 → 上游交易 → `TRN_NO` 放什麼

| `TRN_CD` | 語意 | 由誰建 | `TRN_NO` 放的是 |
|---|---|---|---|
| `1` | 開戶 | `BMSM004` | 受益人開戶書號 |
| `2` | 申購 | `OFDM221A` `OFDB310` | `ALLOT_NO` 申購書號 |
| `3` | 贖回 / 轉換 | `OFDM231A` | `REDEM_NO` 買回書號 |
| `4` | 小額契約 | `RSPM004` | 契約書號 |
| `5` | 受益人異動 | `BMSM006` | 異動書號 |
| `6` | 定期定額異動 | `RSPM005` | 異動書號 |

### C.2 過帳控制碼兩兄弟(值域不同,常數同名)

|  | `ALLOT_CTL_CODE`(申購) | `REDEM_CTL_CODE`(贖轉) |
|---|---|---|
| `0` | 無資料 | 無資料 |
| `1` | 有資料 | 有資料 |
| `2` | 已單位數計算 | 已預估價金計算 |
| `3` | **已結轉** | 已價金計算 |
| `4` | — | **已結轉** |
| 常數名 | `ALLOT_CTL_CODE.Tranfer` = `3` | `REDEM_CTL_CODE.Tranfer` = `4` |

### C.3 「空值」的三種表示法(本片共存)

| 表示法 | 出現在 | 例 |
|---|---|---|
| Oracle NULL | 多數欄位 | `OFD251A.DOC_NID` 無對應買回書時 |
| **一個空白字元 `' '`** | `OFD272A.GET_COPY_DATE` / `GET_COPY_UID`、`OFD251A.DOC_ADATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:93-94`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:121` |
| .NET `string.Empty` | UI / Ctl 層的比較 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2084` |

**查 `OFD272A` 是否到件,三種寫法都要涵蓋**:`GET_COPY_DATE IS NULL OR TRIM(GET_COPY_DATE) IS NULL`。

## 附錄 D. 掃描母體與覆蓋率

覆蓋率工具 `atlas_scan.py --module OFD` 會拿 OFD 全部 550 支畫面來比,對單片沒有意義。以下是本片 24 支的逐支處置表。

| # | 畫面 | 處置 | 寫在哪 |
|---|---|---|---|
| 1 | `OFDM091` | 表格帶過 | §4.13 |
| 2 | `OFDM220` | 已寫(成對) | §4.10 |
| 3 | `OFDM221A` | **深寫** | §4.1、§4.3 |
| 4 | `OFDM231A` | **深寫** | §4.2、§4.3 |
| 5 | `OFDM232` | 已寫(成對) | §4.10 |
| 6 | `OFDM233` | 表格帶過 | §4.13 |
| 7 | `OFDM242` | **深寫** | §4.9 |
| 8 | `OFDM243A` | 表格帶過 | §4.13 |
| 9 | `OFDM264` | **深寫** | §4.4 |
| 10 | `OFDM270` | 表格帶過 | §4.13 |
| 11 | `OFDM271` | **深寫** | §4.8 |
| 12 | `OFDM281` | **深寫** | §4.5 |
| 13 | `OFDM284` | 表格帶過 | §4.13 |
| 14 | `OFDM285` | 表格帶過 | §4.13 |
| 15 | `OFDM286` | 表格帶過 | §4.13 |
| 16 | `OFDM297` | 表格帶過 | §4.13 |
| 17 | `OFDM300` | 表格帶過 | §4.13 |
| 18 | `OFDM301` | 表格帶過 | §4.13 |
| 19 | `OFDM302` | **深寫** | §4.11 |
| 20 | `OFDM321` | 表格帶過 | §4.13 |
| 21 | `OFDM331` | **深寫** | §4.6 |
| 22 | `OFDM337` | **深寫** | §4.7 |
| 23 | `OFDM344` | 表格帶過 | §4.13 |
| 24 | `OFDM361` | **深寫**(說明為何沒有主明細) | §4.12 |

**深寫 12 支、表格帶過 12 支,24 支全數處置,無遺漏。**

母體本身的兩個修正(寫給下一個做 OFD 其他片的人):

| 掃描器說 | 實際 | 影響 |
|---|---|---|
| `OFDM271` 主檔 `OFD724` | `xTableMapping` 有宣告,但程式不讀不寫;真正操作的是 `OFD272A` | 用母體算「`OFD724` 有幾個維護入口」會多算一個 |
| `OFDM361` 主檔 `—` | 正確,但原因是三層空類別,不是漏宣告 | 別去補假的 `xTableMapping` |

## 附錄 E. 讀本文時要注意的地方

以下每條:**缺陷 / 影響 / 錨點 / 嚴重度**。分成十二型,型號沿用前九篇的缺陷型錄。

### E-1 整代基底跑不動:七支畫面掛在未賦值的連線上

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `BasicEVAPO` 與 `MultiRowEVAPO` 的建構子把 `dbTA` / `dbPTPF` 的賦值整段註解,欄位停在 `null`;`Add` 第一行就 `dbTA.CreateConnection()` | 繼承它們的 7 支畫面(`OFDM242` `OFDM284` `OFDM285` `OFDM321` `OFDM331` `OFDM344` `OFDM361`)一按存檔就 `NullReferenceException`;`catch` 裡的 `tran.Rollback()` 對 null 再炸一次,真正的錯被蓋掉 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:167-175`、`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187-229`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175` | **高** |
| `OFDM242_PO` 自己的 `m_db` 也被註解成 null,`GetMasterData` 直接 `m_db.CreateConnection()` | 查詢就炸,不用等到存檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:31-32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:188` | **高** |
| `OFDM242_PO.BeforeApproveDelete` 是整段 **T-SQL 批次**:`DECLARE @FUND_ID VARCHAR(10)`、`DECLARE CURSOR` + `@@FETCH_STATUS`、參數型別用 `SqlDbType.NVarChar` | Oracle 完全不吃;就算連線修好也跑不了 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:63-131` | **高** |
| `OFDM242_PO` 查詢 SQL 用 `CONVERT(VARCHAR(10), …, 111)`、`@REDEM_DATE` 具名參數 | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1192`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1233-1235` | 高 |
| `OFDM284` `OFDM321` `OFDM331` `OFDM344` 的 live SQL 仍用 SQL Server 方括號識別字 `[BMS001]` `[OFD286A]` `[LOG106]` `[OFD321]` `[OFD322]` `[OFD331]` `[OFD332]` `[OFD335]` `[OFD344]` | Oracle 會回 `ORA-00903 invalid table name` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:222`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:230`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:198` | **高** |

**這一組整體標「假設」。**依據就是上面五列(連線 null + 兩種方言殘留 + 從未被改成 Oracle 綁定語法), 而且這四支的 UI 層卡控仍然完整,代表使用者會走到存檔那一刻才失敗。 **驗證成本極低:在現場對 `OFDM321` 按一次查詢即可。**若實際可用,表示部署的 `TA.DataAccess.dll` 與 repo 內原始碼不同版 —— 那本身就是更嚴重的問題,也要記下來。

### E-2 Oracle 三值邏輯:`欄 <> '值'` 遇 NULL 靜默過濾

CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過,OFD8 也不例外。全部是**過濾(無提示)**。

| 位置 | 條件 | NULL 時會怎樣 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:277` | `(OFD272A.TRN_CD<>'3' OR (OFD272A.TRN_CD='3' AND OFD251A.DOC_NID<>'Y'))` | `DOC_NID` 是 left join 來的,**沒有對應買回書時必為 NULL** → 整條 UNKNOWN → 該筆缺件在「到件回復」清單上消失。同一行的註解還寫「DOC_NID可以是空白或N」,顯示作者只想到空白 | **高** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325` | `AND OFD251A.REDEM_PROC_CODE <> '3'` | 未結帳的買回書若 `REDEM_PROC_CODE` 為 NULL,會被當成「已結帳」排除 | 高 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` | `AND B.REDEM_PROC_CODE<>'3'` | 同上 | 高 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2418` | `AND ALLOT_CTL_CODE <> '0'` | 控制碼為 NULL 的過帳控制列被漏掉 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2955` | `AND BF_NATIONALITY <> '0001'` | 國籍未填的受益人被當成本國人排除 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2316` | `AND BF_NATIONALITY <> '0001'` | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3230` | `AND RSP_TYPE<>'2'` | 定期定額型別未填的契約被漏掉 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3254` | `AND RSP006A.RSP_TYPE <> '2'` | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:915` | `WHERE OFD651A.EC_REDEM_PCODE <> '4'` | 同上(該支本來就跑不動,見 E-1) | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:922` | `WHERE OFD656.EC_REDEM_PCODE <> '4'` | 同上 | 低 |

**同型但在 .NET 這一側的變形**:`DataTable.Select("欄<>''")`。ADO.NET 的運算式對 `DBNull` 同樣回 false,所以「有值就不可刪」的檢核對 NULL 欄位一律放行:

| 位置 | 條件 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2042` | `dt.Select("COMPARE_NO<>''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2066` | `dt.Select("REMIT_CTL_NO <> ''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1793` | `UIView.OFD272.Select("GET_COPY_DATE<>''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:891` | `dt.Select("ALLOT_DATE <> '' ")` | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` | `m_view.OFD272.Select("GET_COPY_UID<>''")` | 中 |

### E-3 成對畫面 / 成對路徑只改一邊

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`OFDM231A` 轉申購:新增走 156 行逐欄指派,修改只同步 1 個欄位** | 改了轉換的金額 / 日期 / 通路 / 業務員,它的影子申購明細 `OFD221A` 除 `FAVORED_REL_TYPE` 外全部留舊值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1936-2105` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2110-2112` | **高** |
| 2 | `OFDM220` 的 `OFD303A` 更新在 2009 年從 `BeforeAdd` 改到 `AfterAdd`,`OFDM232` 沒跟 | 買回彙總在主檔寫入前就動控制檔;主檔失敗時控制檔已改 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:47-48` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:48` | 中 |
| 3 | 同一組 UPDATE,`OFDM220` 綁參數並寫 `UPDATEID` / `UPDATEDATE`,`OFDM232` 用 `string.Format` 串字串且不寫更新者 | 買回側的控制檔改動查不到誰改的;且字串串接 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:113-131` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:121-131` | 中 |
| 4 | `OFDM281` 的「已產生配息資料不得修改 / 刪除」:修改路徑硬化成 `Int32.TryParse`,刪除路徑仍是 `Convert.ToInt32` | 下拉為空時刪除路徑丟例外,修改路徑靜默放行 —— **兩種錯法** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776` | 中 |
| 5 | `OFDM300` 用 `Convert.ToDecimal` 判斷匯率,`OFDM301` 用 `Convert.ToDouble` | 匯率是金額類欄位,`double` 有浮點誤差;兩支成對畫面行為不一致 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM300.cs:149` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM301.cs:153` | 中 |
| 6 | `OFDM221A` 刪除卡控:按鈕層用 `DataTable.Select` 運算式、列層用欄位直接比較 | 同一條規則兩種 NULL 行為(見 E-2) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2041-2071` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2078-2110` | 中 |
| 7 | `OFDM302` 刪除卡控同上:按鈕層 `Select("NAV_LOCK='…'")`、列層 `row.NAV_LOCK == …` | 同上 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:265` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:354` | 低 |
| 8 | `OFDM286` 的「同一基金僅可有一筆生效中資料」在新增列與修改列各寫一次 | 改一邊漏一邊 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:307` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:328` | 低 |
| 9 | `OFDM221A` 與 `OFDB310` 對 `OFD272A` 的取數 SQL 幾乎逐字相同,分別維護 | 缺件查詢條件改一邊漏一邊 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:913-928` 對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB310_PO.cs:1025-1037` | 中 |

### E-4 手寫逐欄對應與漏欄

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM231A` 轉申購的 156 行手寫指派(`row220.*` 與 `row221.*`) | `OFD220A` 77 欄、`OFD221A` 125 欄,逐欄手抄;新增欄位時漏抄不會編譯失敗,也不會有任何提示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1936-2105` | **高** |
| 同上的修改分支 `FindByALLOT_NOALLOT_SRNO(row1.ALLOT_NO, 1)` 把 `ALLOT_SRNO` 寫死成 `1`,回傳值**沒有 null 檢查** | 轉申購明細若不是序號 1(或已被刪),下一行直接 `NullReferenceException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2111-2112` | **高** |
| `OFDM331_PO.BeforeAdd` 建了三個明細 row 卻從未 `Add*Row`,`COMPLAIN_NO` 設在孤兒物件上;被註解掉的舊版反而會重新指向 `Rows[0]` 且處理四張明細 | **假設**:新客訴的明細鍵拿不到主檔序號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:103-105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:135-140`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:459-474` | **高** |
| `OFDM221A` 的明細取數靠 `LoadDataSet` 的 7 個表名參數與 SQL 段落順序對齊 | 加一張明細要同時改三處,少改一處會把資料灌到錯的 DataTable | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:127-136` | 中 |

### E-5 字串串接進 SQL

本片 12 支 PO 共用同一段查詢條件樣板,**欄位名與值都來自用戶端、都沒有綁參數**:

```
strSQL += " And <表名>." + Row.Name + " = " + "'" + Row.Value + "'";
strSQL += " And <表名>." + Row.Name + " Like " + "'" + Row.Value + "%'";
```

| 畫面 | 錨點(首見) | 嚴重度 |
|---|---|---|
| `OFDM091` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091_PO.cs:134` | 高 |
| `OFDM233` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:149` | 高 |
| `OFDM243A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:168` | 高 |
| `OFDM264` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:237` | 高 |
| `OFDM281` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:164` | 高 |
| `OFDM284` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:222` | 高 |
| `OFDM297` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM297_PO.cs:101` | 高 |
| `OFDM321` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163` | 高 |
| `OFDM331` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:230` | 高 |
| `OFDM344` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:198` | 高 |

另有兩處是**執行面**(UPDATE)的字串串接,風險更高:

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113` | `UPDATE OFD272A SET GET_COPY_DATE=' ', …, TRN_MEMO='<使用者輸入>' WHERE TRN_CD='…' AND TRN_NO='…'`;只有 `TRN_MEMO` 走 `ConvertTo.OracleString` 跳脫,其餘直接串 | **高** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` | 同上,`GET_COPY_DATE` 直接串畫面輸入值 | **高** |

### E-6 一律回報成功 / 失敗訊息是空字串

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM271_PO.Execute` 五個失敗出口有四個回 `AddResultRow(false, 0, "")` | 使用者看到空白錯誤框,現場無從判斷是哪一步失敗 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:112`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:149`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:210`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:218`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:224` | **高** |
| `OFDM271_PO.Execute` 成功時回的筆數是 `Convert.ToInt32(j)`,`j` 是**最後一次 `ExecuteScalar` 的結果**,不是更新筆數;沒走到 `ExecuteScalar` 時 `j` 為 null → 回 0 筆但標記成功 | 「執行成功,0 筆」會被當成沒資料,其實可能更新了很多筆 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:205` | 中 |
| `OFDM271_PO.Execute` 內外兩層 `catch` 都會 `AddResultRow`,內層已經 rollback + 寫結果,外層再寫一次 | 同一次失敗回兩筆結果;上層只看 `Result[0]` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:207-226` | 中 |
| `OFDM221A` / `OFDM231A` 的 After 掛點共 **15 處** `throw new ApplicationException("")` —— 空訊息 | 跳號紀錄寫失敗時使用者看到空白錯誤;與 `architecture.md §3` 記的 `CASM001_PO` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2678-2741`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3953-4003` | 中 |
| `OFDM331_PO.BeforeAdd` 的 `catch` 吞掉例外後方法正常返回 | 取號失敗仍然往下 INSERT,`COMPLAIN_NO` 是空的 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:143-148` | **高** |
| 四支 Ctl 直接讀 `result.Util.Result[0]` 組成功訊息,沒檢查 `Count` | PO 沒塞 Result 就 `IndexOutOfRangeException`;與 `architecture.md §6` 記的 `CASM001_Ctl` 同型 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM221A_Ctl.cs:59`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:61`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM270_Ctl.cs:49`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM337_Ctl.cs:53` | 中 |

### E-7 被註解掉但外殼還在的檢核與程式

| 位置 | 被註解的東西 | 影響 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:806` | 「此 推薦人 不存在該 通路代碼」檢核 | 推薦人與通路代碼的一致性不再檢查 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1034` | 「交易方式為傳真時,需可傳真交易」檢核 | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2030-2038` | TDCC 來源原本是「詢問 + bypass」,現改為硬擋,舊分支整段留著 | 讀 code 會誤判可以 bypass | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:288`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:356` | 「資料內容必填」「補位字元必填」 | 媒體檔格式可以留空欄位 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:389`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:767` | 舊版「作業處理碼 不為尚未處理時,不得修改／刪除」 | 兩段都有 live 替代品,但訊息與行為都變了 | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:55` | 舊版「淨值日 不存在於 基金代碼[X] 之營業日」 | 有 live 替代品 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2686-2691` | `AfterDelete` 裡回沖 `OFD303A` 的整段 | 刪除送審時不回沖控制檔,要等覆核刪除才回沖 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:307-466` | 整段舊 SQL Server 版 PO(160 行) | 死碼 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:390-806` | 整段舊 `Add` / `Select` override(415 行,**比 live 段還長**) | 死碼,且是正確版本(見 E-4) | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:250-459` | 整段舊 `Add` / `Select` override(209 行) | 死碼 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:39` | `MasterTable.Add(new TableMapping("LOG106", "LOG"))` | xsd 裡 `LOG` 這張表永遠是空的 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM270_PO.cs:40-42` | `AfterAdd` / `AfterUpdate` / `AfterUnDelete` 的訂閱 | 退郵戶新增後沒有後續動作 | 中 |

### E-8 寫死常數與位置取參數

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM231A` 用字面量 `'3'` 表示缺件種類「贖回轉換」,同一支的別處卻用 `TRN_CD.RedeemAndSwitch` | 代碼改值時只改常數會漏掉字面量 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1173` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:119` | 中 |
| `OFDM271` 同一支裡兩種寫法並存:`TRN_CD.RedeemAndSwitch` 與字面量 `'3'` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:172` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:178`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:191` | 中 |
| `REDEM_PROC_CODE == "3"`(已結帳)三處字面量,**全庫沒有對應的常數類別** | 無處可改,改值要 grep 全庫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` | 中 |
| `OFDM221A` 的缺件查詢寫死 `SHORE_ID = '2'`(境內)〔客戶特定〕 | 這支永遠只看境內基金缺件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:924` | 中 |
| `FindByALLOT_NOALLOT_SRNO(…, 1)` 寫死序號 `1` | 見 E-4 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2111` | 高 |
| `OFDM242` / `OFDM302` / `OFDM321` 的訊息字串直接寫入別的畫面代號(`OFDB757` `OFDM114` `OFDM087`) | 代號變更時訊息會誤導 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:516`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:523`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2025` | 低 |

### E-9 無上限重試與死碼

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 四支畫面的取號 `do { 取號 } while (已存在)` **沒有次數上限** | 撞號情境或判斷恆真時變成無窮迴圈,卡住整條遠端執行緒(與 `architecture.md §3` 記的 `CASM001_PO` 同型) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:173-176`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3501-3504`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:119-129`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:130-133` | 中 |
| `OFDM221A_PO.BeforeAdd` 建了 `EVAUtility util` 從未使用(建構子還會產生一顆 Guid) | 死碼 + 每次新增多一次無謂配置;讀者會誤以為這裡有 EVA 處理 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:165` | 低 |
| 同一支的 `string bms001_dataid = string.Empty;` 宣告後從未使用 | 死碼;註解「Keep BMSM001 dataid」暗示曾有需求 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:160` | 低 |
| `OFDM361` 三層空類別 + 653 行 Designer + 兩份 655 行 xsd | 半成品進版控;`OFDM361_Ctl` 連 `BaseController` 都沒繼承 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM361_Ctl.cs:7-9`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10` | 中 |
| `OFDM331_PO.BeforeAdd` 的條件 `row.COMPLAIN_NO != string.Empty \|\| row.COMPLAIN_NO != ""` 兩邊完全相同 | 邏輯上等於只寫一次;看得出原意是 null 檢查卻寫成同式 OR | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:118` | 低 |

### E-10 交易邊界被掛點打破

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM331_PO.BeforeAdd` 在 `Before*` 掛點裡直接 `args.DbTran.Rollback()` 然後 `throw` | 違反掛點規約(`architecture.md §3` 明載「不能自己 commit / rollback」);引擎外層會對已 rollback 的交易再 rollback 一次,真正的訊息被 `InvalidOperationException` 蓋掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:122-123` | **高** |
| `OFDM231A_PO.BeforeUpdate` 在主檔階段 **改動 `this.DetailTable`**(`Clear()` 後只加 `OFD272A`) | 已結帳的買回書按存檔,付款 / 轉換 / 沖銷 / 憑證的改動**靜默不寫入**,畫面仍回成功 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3527-3528` | **高** |
| `OFDM271_PO.Execute` 自己 `BeginTransaction` / `Commit`,不在 EVA 交易內 | 到件登錄與上游交易不同一個交易;中途失敗時 `OFD251A` / `OFD607A` 的連動可能只做一半 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:65`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:204` | 中 |

### E-11 命名與檔案結構的陷阱

| 陷阱 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM242` 的 xsd DataTable 叫 `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`,而全庫沒有 `OFDM643` 這支畫面 | 用 `OFDM242` grep 找不到它的資料表;三層共 56 處引用 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM242Model.xsd`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM242_Ctl.cs:56` | 中 |
| `OFDM221A_PO` 的介面叫 `IOFDM221_PO`(少一個 `A`) | 用代號搜介面會漏 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:25` | 低 |
| `OFDM231A` 的意定代理人 vdb 叫 `OFD231A_AGENT`,實體表卻是 `OFD251A_AGENT` | 兩個名字差很多,對照時容易看錯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:78` | 低 |
| `OFDM331` 的 `_K` 後綴在「客訴」與「處理」兩組裡語意相反(§2.1) | 改錯表 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:34-37` | 中 |
| `OFDM271` 代號是 `M` 但繼承 `xOneStepProcessForm`,行為是 B | 依型別碼分類權限 / 稽核時會分錯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28` | 中 |
| `OFD270A` 實體只有 2 欄,vdb 卻有 43 欄(41 欄是 join 來的) | 改畫面上的欄位改不到任何東西 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM270Model.xsd` | 中 |
| `OFDM264_Ctl` 自己定義私有的 `ExecPOActionToViewVDB`,不用基底版本 | 改 `BaseController` 不會影響它 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM264_Ctl.cs:284` | 低 |
| 本片所有 `.cs` 實測皆為可解碼的 UTF-8,**無非 UTF-8 來源檔、無 null bytes** | (這一條是「查過沒問題」的紀錄) | — | — |

### E-12 讀這份文件本身要注意的

1. **行號是分析當下(2026-09-15)的版本。**動手前先用 `grep -n` 對一次。

2. **「跑不動」那七支是假設。**E-1 已經寫明驗證方法,不要當事實直接向客戶陳述。

3. **中文畫面名 24 支裡有 22 支是推測。**只有 `OFDM221A` 與 `OFDM302` 在程式註解裡有明確中文。

4. **本文只涵蓋 `DataEntity.OFD8` 這一片。**同一張表在 OFD 其他片可能還有主檔畫面與更強的卡控, `OFD220A` / `OFD221A` / `OFD251A` / `OFD724` 尤其明顯。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD8` 的 24 支 M 畫面、45 張實體表、3 個版控外 DB 物件;12 支深寫、12 支表格帶過;附錄 E 收 12 型共 60 餘條缺陷。 |

由 build_doc.py v2.0.0 於 2026-09-15 11:42 產生 · 標題 111 · 圖 5 · 表格 89 · 程式錨點 517 · § 連結 98 · 引用檢查：畫面 61（缺 0） · Table 54（缺 0） · 結果集 42（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofd9.md
============================================================

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
