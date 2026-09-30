<!-- 由 tools/build_copilot_kb.py 從 modules/ofd6.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
