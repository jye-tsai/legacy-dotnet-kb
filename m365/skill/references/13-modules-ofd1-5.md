ATLAS 知識庫 — 13-模組-OFD1至5

本檔合併以下文件:modules/ofd123.md、modules/ofd4.md、modules/ofd5.md


============================================================
【文件】kb/modules/ofd123.md
============================================================

# ATLAS OFD1-3 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:急著要結論的人直接跳三個地方 —— §2.2(`A` 後綴到底是什麼,本片給出十三列判定,終結前兩片的矛盾)、§3.2(五支畫面連按查詢都會 NullReferenceException)、附錄 E.1 ~ E.5(最會咬人的五條缺陷)。要通讀的人照 §1 圖 → §2 資料模型 → §3 清冊 → §4 逐支的順序。

> ⚠ **OFD1-3 不是一個業務模組,是三份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/`、`DataEntity.OFD2/`、`DataEntity.OFD3/` 三個 Entity 專案底下的 **26 支 M 畫面**。切片依據是 Entity 專案資料夾,不是業務。名稱 `OFD1-3` 為**推測**,取自資料夾名。

> ✅ **但這一片比其他片整齊。** 26 支**全部**是 M 型維護畫面,**全部**是「一個代碼 + 一到數個說明欄」的參數主檔,**沒有一支**是查詢、批次或報表。§0.1 會證明「這 26 支是不是參數檔群」這個問題的答案是**是**,而且是整個 OFD 模組最基礎的那一層 —— 別的模組讀它們,它們幾乎不讀別人。

> ⚠ **五支畫面在執行期是死的。** `OFDM017B` `OFDM022` `OFDM026` `OFDM028` `OFDM029` 的 PO 繼承 `BasicEVAPO`,這個基底的 `dbTA` 宣告即 `= null` 且建構子賦值那四行整段被註解,連 `Select()` 第一行就 `dbTA.CreateConnection()`。**這五支不是存檔才炸,是連查詢都炸**(§3.2、附錄 E.1)。它們全在 csproj、編得起來,所以靜態掃描看不出問題。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、各層的 XML 註解與 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的常數字典**推測**,待選單表回填。PO 層的介面註解有 **21 支一字不差寫著「覆核層級管理 PO 共用介面」**,那是複製貼上殘留,引用時要小心(§3.4)。

> ⚠ **〔客戶特定〕**:銷售機構別 `AGENT_ID` 的 `'0'`/`'1'`/`'3'`/`'4'`、通路別 `CHANNEL_CD` 的 `'1'`/`'3'`/`'4'`、銀行類型 `'04'`/`'05'`(農會 / 漁會)、行事曆同步的 MSSQL 資料庫別名 `"FA"` 與該端的 SP,為本站台的值。

> ⚠ **〔共用〕**:`OFD002`(76 個檔案讀)、`OFD019A`(46 個)、`OFD020A`(33 個)是全庫等級的主檔,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 26 支畫面管什麼(推測)

先給結論,而且這個結論比前面幾片乾淨:**本片就是 OFD 的「參數與代碼主檔層」**。26 支全部符合同一個形狀 —— 使用者輸入一個代碼、填一到數個名稱欄、四眼覆核、存檔;然後全公司其他模組拿這個代碼去 join 出中文名。判斷依據有四條,四條都成立:

| 判準 | 觀察 | 錨點 |
|---|---|---|
| 一表一畫面,且表只有代碼 + 名稱 | 26 支宣告 27 張表(`OFDM015` 是唯一帶明細的),其中 **17 張的業務欄位少於 5 欄**,扣掉框架的四眼欄位後只剩代碼與說明 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM026Model.xsd`(17 欄裡 15 欄是四眼欄位) |
| 沒有金額、沒有日期區間、沒有狀態機 | 27 張表裡只有 `OFD016` 有一個 `GRADE_SEQ` 數值欄,其餘全是字串代碼與名稱;沒有任何一張有金額欄或業務日期欄 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM015Model.xsd` |
| 下游遠多於上游 | 26 支合計只 join 四張外部表(`OFD019A` / `FSK003` / `OFD074` / `OFD076`);反過來本片的表被 **18 個以上的專案**讀 | §8 |
| PO 幾乎不寫業務邏輯 | 26 支 PO 有 **11 支活的程式碼在 50 行以內**,純框架掛表名;`OFDM006` / `OFDM007` / `OFDM012` / `OFDM013` / `OFDM017` / `OFDM025` / `OFDM026` / `OFDM028` 的 PO 檔案有 **94 % 以上是被註解掉的舊 MSSQL 實作** | §3.3 |

依業務線分群,26 支落成九塊:

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 公司組織與行事曆**(3) | `OFDM001` `OFDM002` `OFDM003` | 集保分公司代碼、公司內部部門(大 / 中 / 小三級)、營業日行事曆(哪天休市) | Caption「分公司代碼」「部門代碼」「行事曆類別」;`OFD003A` 有 `BUSS_ID`(營業日否) |
| **B 基金屬性代碼 — 集保版**(2) | `OFDM004` `OFDM005` | 集保(TDCC)那一套的基金種類、基金型態 | 欄位全帶 `_TSCD` 後綴:`PROF_TYPE_TSCD` / `FUND_TYPE_TSCD`,Caption 直接寫「(集保)」 |
| **C 基金屬性代碼 — 內部版**(6) | `OFDM006` `OFDM007` `OFDM009` `OFDM010` `OFDM011` `OFDM014` | 本公司自己那一套的基金種類、基金型態、註冊地、投資區域、投資地區、贖回費收取方式 | 與 B 塊欄名相同但無 `_TSCD` 後綴:`PROF_TYPE` / `FUND_TYPE` |
| **D 費用與分配方式**(2) | `OFDM012` `OFDM013` | 申購手續費收取方式(前收 / 後收…)、收益分配方式(配息 / 累積…) | Caption「申購手續費收取方式」「收益分配方式」 |
| **E 信評**(1,唯一帶明細) | `OFDM015` | 信評公司(`OFD015`)與該公司的評等等級表(`OFD016`),一家公司掛多個等級 | 主明細宣告 `OFD015` → `OFD016`,明細 PK 三欄 |
| **F 受益人分類**(2) | `OFDM017` `OFDM017B` | 受益人的公會類別(含大陸人士身分別)、受益人類別 | Caption「受益人公會類別代碼」vs「受益人類別代碼」 |
| **G 金融機構**(3) | `OFDM019` `OFDM020` `OFDM022` | 金融機構總行、金融機構分行、跨國匯款的中間銀行 | `BANK_HQ` / `BANK_BRH` / `REMIT_BANK_SWIFT` |
| **H 外部投信投顧**(2) | `OFDM023` `OFDM024` | 投顧公司、投信公司 | `SICE_CD` / `SITE_CD` |
| **I 客戶與通路分類**(5) | `OFDM025` `OFDM026` `OFDM027` `OFDM028` `OFDM029` | 開戶來源、潛在客戶類別、行銷身份群族、通路區域、帳戶國別 | Caption 逐條對應 |

> 九塊之間**沒有任何程式呼叫**。表層面只有一條真依賴:`OFDM020`(分行)在 `CheckBANK_HQ` / `CheckSWIFT_CODE` / `CheckBANK_VALID_CODE` 三處去讀 `OFD019A`(總行),錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:144`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:186`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:230`;另外 `OFDM022`(中間銀行)join 總行取簡稱,錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:115`。

### 0.2 不管什麼

| 不在 OFD1-3 | 在哪 | 依據 |
|---|---|---|
| 銷售機構主檔 `OFD068A` 的內容維護 | `OFDM068`(不在本片,見 `ofd4.md §4.3`) | 本片有**五支**畫面會 UPDATE 它,但都只改名稱欄,不維護內容 |
| 通路主檔 `OFD071A` 的內容維護 | `OFDM071`(不在本片) | 同上,本片 `OFDM019` / `OFDM020` / `OFDM023` / `OFDM024` 只同步名稱 |
| 代扣款行 `OFD074` / 代理行 `OFD076` | `OFDM074` / `OFDM076`(不在本片) | `OFDM019` 只在刪除與改核印方式時 `COUNT` 它們:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:178`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:237` |
| 基金主檔本身 | `OFDM081B` 等(不在本片) | 本片只維護基金的**屬性代碼**(種類 / 型態 / 註冊地 / 投資區域),不碰基金 |
| 幣別主檔 `FSK003` | FSK 模組 | `OFDM022` 只 `left join` 取幣別名:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:117` |
| 行事曆在下游系統的落地 | MSSQL 端 SP `S_PAM_OFD003A_SWSYS011`(**版控外**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:490` 只負責呼叫 |
| 部門改名同步到銷售機構 | **同時**由 PO 與 Oracle Trigger `OFD002_T01` 做兩份 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1008-1029` 與 `DB/Trigger/OFD002_T01.SQL:10-29`,見附錄 E.6 |
| 代碼值域本身(下拉選單有哪些選項) | `CTL014`(共用下拉代碼)與各 `DataSrc` 類別 | 例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:523` 用 `FiscCdDataSrc` |
| 集保代碼與內部代碼的**對照** | 不在本片任何一支 | B 塊與 C 塊是兩張獨立的表,repo 內找不到把 `PROF_TYPE_TSCD` 對到 `PROF_TYPE` 的維護入口 —— 見附錄 E.14 |

### 0.3 使用角色

26 支全部宣告成四眼(EVA)維護畫面,角色由平台的 ToDo 機制指派,本片自己不定義角色。詳見 `architecture.md §3`。

**四個要注意的例外:**

| 例外 | 內容 | 錨點 |
|---|---|---|
| `OFDM017B` `OFDM022` `OFDM026` `OFDM028` `OFDM029` | 走的是**舊世代** `BasicEVAPO` + `TableMapping`(無 `x` 前綴),而且執行期一定 NRE,四眼形同不存在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:20`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM026_PO.cs:18` |
| `OFDM002` | **自己覆寫 `Add`**,在呼叫基底前先做兩段父部門檢核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1033` |
| `OFDM003` | 除了四眼還有三個自訂動作,**每個都自己開交易、自己跑迴圈分批寫 ToDo** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:73`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:165`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:273` |
| `OFDM002` `OFDM019` `OFDM020` `OFDM023` `OFDM024` | 在 `AfterUpdate` 直接 UPDATE 別的模組的表,**那些異動不經任何四眼** | §8.1 |

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(只讀 join) | `OFD019A`(`OFDM020` / `OFDM022` 讀)、`FSK003`(幣別)、`OFD074`(代扣款行,只 `COUNT`)、`OFD076`(代理行,只 `COUNT`) | 兩張是 `LEFT JOIN` 取說明欄,另兩張只算筆數 |
| 下游(本片的表被誰讀) | `OFD002` 被 76 個檔案讀、`OFD019A` 被 46 個、`OFD020A` 被 33 個、`OFD015` 與 `OFD016` 各 14 個 | 見 §8 |
| 旁寫(本片寫別人的表) | `OFDM002` → `OFD068A`;`OFDM019` → `OFD020A` `OFD068A` `OFD071A`;`OFDM020` → `OFD071A`;`OFDM023` / `OFDM024` → `OFD068A` `OFD071A` | 見 §8.1 |
| 跨資料庫 | `OFDM003` 核准 / 核准刪除後,呼叫 **MSSQL** 端 SP `S_PAM_OFD003A_SWSYS011` 同步行事曆 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:485-520`;連線別名寫死 `"FA"`:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:53` |
| DB 端自主動作 | Oracle Trigger `OFD002_T01` 在 `OFD002` 被改名或刪除時,自行 UPDATE / 擋下 `OFD068A` | `DB/Trigger/OFD002_T01.SQL:1-43` |

### 0.5 全域開關

本片沒有 `App.config` 層級的業務開關。真正決定行為的都是資料欄位或寫死常數:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `DEPT_NO` 長度(5 / 7 / 9) | 字串長度 | **決定部門的階層**:5 碼 = 大部門、7 碼 = 中部門、9 碼 = 小部門。新增 7 / 9 碼時強制檢查上一層存在且有效;只有 5 碼才同步 `OFD068A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1039`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1005` |
| `DEPT_VALID_CODE` | `'Y'` 有效 / `'N'` 無效 | 改值時,**所有下層部門一起被改成同值**(一句用 `LIKE` 前綴比對的 UPDATE) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:990-1003` |
| `BANK_VALID_CODE` | `'Y'` / `'N'`,值域見 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81-91` | 總行改成無效時連動把該總行**所有分行**改成無效;而且總行無效時新分行的有效碼被鎖成 `'N'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:65-80`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:486-496` |
| `FISC_CD`(金資編碼否) | `'Y'` / `'N'` | 決定**總行代碼第一碼的字元集**:`'Y'` 必須 `0~9`、`'N'` 必須 `A~Z`;同時改變輸入遮罩 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:349-362`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:444` |
| `BANK_TYPE`(銀行類型) | `'01'` 本國 · `'02'` 外國 · `'03'` 信合社 · `'04'` 農會 · `'05'` 漁會 | `'04'` / `'05'` 時:一般核印方式被鎖死不可勾;`AfterUpdate` 的分行核印連動**整段跳過** | 值域 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3157-3179`;用法 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:545-551`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:124-125` |
| `AGENT_ID`(銷售機構別) | 程式碰過 `'0'` `'1'` `'3'` `'4'` | 決定哪支畫面改名時要同步 `OFD068A` 的哪一批列:`'0'` 部門(`OFDM002`)、`'1'` 銀行(`OFDM019`)、`'3'` 投顧(`OFDM023`)、`'4'` 投信(`OFDM024`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1015`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:79`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:79` |
| `CHANNEL_CD`(通路別) | 程式碰過 `'1'` `'3'` `'4'` | 同上,決定同步 `OFD071A` 的哪一批列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:111`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:114`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:98` |
| `BUSS_ID`(營業日否) | `'Y'` 營業日 / `'N'` 休市 | 行事曆上每一天一列,`'N'` 在月曆控件上顯示成假日 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:243-248` |
| `SQLDBName = "FA"` | 字面量 | `OFDM003` 核准時要往這個 **MSSQL** 連線寫 —— 寫死,不在設定檔選 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:53-54` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD1-3 全景：公司組織與行事曆、基金屬性代碼、信評與受益人分類、金融機構、客戶分類五條線，加上旁寫與下游讀者
圖中文字:① 公司組織與行事曆：本片唯一有時序感的一塊 / OFDM001 / OFD001 集保分公司 / OFDM002 / OFD002 部門 三級結構 / OFDM003 / OFD003A 營業日行事曆 / MSSQL FA 資料庫 / S_PAM_OFD003A_SWSYS011 / ② 基金屬性代碼：集保版與內部版兩套並存，沒有對照表 / OFDM004 OFDM005 / _TSCD 後綴 集保版 / OFDM006 OFDM007 / 無後綴 內部版 / OFDM009 OFDM010 OFDM011 / 註冊地 / 投資區域 / 地區 / OFDM012 OFDM013 OFDM014 / 手續費 / 分配 / 贖回費 / 兩套欄名鏡像 查無對照 / 附錄 E.14 標假設 / ③ 信評與受益人分類：本片唯一的主明細、唯一的 A / B 成對 / OFDM015 / OFD015 → OFD016 明細 / OFDM017 / OFD017A 公會類別 / OFDM017B / OFD017B 受益人類別 / 017B 是死畫面 / BasicEVAPO 必 NRE / ④ 金融機構與外部機構：下游最廣的兩張表都在這裡 / OFDM019 / OFD019A 總行 46 個檔案讀 / OFDM020 / OFD020A 分行 33 個檔案讀 / OFDM022 / OFD022 中間銀行 / OFDM023 OFDM024 / 投顧 / 投信 逐行鏡像 / ⑤ 客戶與通路分類：五支裡有三支是死畫面 / OFDM025 / OFD025A 開戶來源 / OFDM027 / OFD027A 行銷身份群族 / OFDM026 OFDM028 OFDM029 / 潛在客戶 / 通路區域 / 國別 / 三支都是 BasicEVAPO / 資料只能從 DB 改 / ⑥ 旁寫：五支畫面改別人的表，全部不經對方四眼 / OFDM002 存檔後 / AfterUpdate / OFDM019 OFDM020 / AfterUpdate / OFDM023 OFDM024 / AfterUpdate / OFD068A OFD071A OFD020A / 三值邏輯 NULL 時靜默不同步 / ⑦ 下游：參數檔群被十八個以上的專案讀 / BMS CAS COD CRM DSM / 開戶 / 客戶 / 配息 / EC OTA OTAB OFDB RSP / 電子交易 / 境外 / 批次 / CPM NFD.Report OFDI / 佣金 / 報表 / 查詢 / DB 端 SP 與 View / 11 個物件
```

*圖:圖 1 OFD1-3 全景。橘框=本片的維護入口;橘虛框=有風險或執行期死的;灰虛框=別的模組;黑框=無原始碼或版控外。五條業務線彼此沒有程式呼叫，真正要小心的是 ⑥ 的旁寫——本片有五支畫面會去改別人的表，而且六處都有同一個三值邏輯缺陷。*

### 1.2 資料表關係與 `A` 後綴的三種成因

圖放在 §2 的開頭(`ofd123.figs.py` 的 `h2:2-`)。看圖時抓兩件事:**帶 `A` 的十二張表全部是 MSSQL → Oracle 遷移時改的名,和境內外無關**(§2.2);以及 **`OFD019A` / `OFD020A` 的遷移只做了一半**,同一支 `Basic/BasicOFD_PO.cs` 裡新舊兩個名字並存(§2.3)。

### 1.3 畫面依 PO 基底與編譯狀態分群

圖放在 §3 的開頭(`h2:3-`)。一句話總結:**26 支全部在 csproj、全部編得起來,但其中五支(`OFDM017B` `OFDM022` `OFDM026` `OFDM028` `OFDM029`)的 PO 停在舊世代基底,按查詢的第一行就 NullReferenceException。**

### 1.4 `OFDM015` 的主明細與卡控

圖放在 §4 的開頭(`h2:4-`)。`OFDM015` 是本片唯一的主明細畫面,它把「不可重覆」與「必填」的檢核全部放在 UI 的 grid 事件裡,PO 端一條檢核都沒有 —— 這代表**繞過畫面直接呼叫 PO 的路徑沒有任何保護**。

### 1.5 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。唯一跨系統的資料流是 `OFDM003` 核准後往 MSSQL 端推行事曆(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:485-520`),那是 M 畫面的四眼後置動作,不是批次。

### 1.6 一日作業泳道

本片沒有時序性的日常作業 —— 26 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM003`:每年年底要用「新增年度行事曆」把下一年度建出來,再逐月設定假日(§4.3)。

## 2. 資料模型

```text
[圖] OFD1-3 二十七張表的兩群、A 後綴三種成因的分群，以及兩張表遷移只做一半的證據
圖中文字:A 帶 A 後綴的十二張：判定全部是 MSSQL→Oracle 遷移改名 / OFD003A OFD006A OFD007A / 行事曆 / 基金種類 / 型態 / OFD012A OFD013A OFD017A / 手續費 / 分配 / 公會類別 / OFD023A OFD024A OFD025A / 投顧 / 投信 / 開戶來源 / OFD027A OFD019A OFD020A / 行銷 / 總行 / 分行 / B 決定性證據：同名方法在兩個目錄讀不同表名，欄位一字不差 / MSSQL/BasicOFD_PO.cs / GetFundKind 讀 OFD006 / Basic/BasicOFD_PO.cs / GetFundKind 讀 OFD006A / 十組方法逐段對照 / 只差表名與 @ 換 : / 結論：A = 遷移改名 / 不是境內外 / C 三種互不相干的成因：看到 A 不能直接套任何一種 / 成因一 遷移改名 / 本片 12 張 ofd4 也是 / 成因二 境內外 / ofd7 的費率表群 有 SHORE_ID / 成因三 都不是 / OFD017B 的 B 是第二張表 / 本片 SHORE_ID 命中 0 / 27 張表全查過 / D 不帶 A 的十四張對照組：兩個目錄用同一個名字 沒改過 / OFD001 OFD002 OFD004 OFD005 / 兩邊同名 / OFD009 OFD010 OFD011 OFD014 / 兩邊同名 / OFD015 OFD016 OFD028 / 兩邊同名 / OFD022 OFD026 OFD029 / 兩邊都沒出現 / E 遷移只做一半：同一支 Oracle 檔案裡新舊表名並存 / Basic/BasicOFD_PO.cs / 六支方法讀 OFD019A / 同一支檔案 / 四支方法仍讀 OFD019 / 維護入口只寫 OFD019A / OFDM019_PO.cs:43 / 讀舊名的拿到什麼？ / 無 DDL 無法判定 標假設 / 外部唯讀：join 進來取說明或算筆數，本片從不寫入 / FSK003 / 幣別 / OFD074 OFD076 / 代扣款行 / 代理行 / COD006A / 大陸人士身分別 E9 / CTL014 / 共用下拉代碼值域 / OFD019A / 分行讀總行
```

*圖:圖 2 資料模型與 A 後綴判定。橘框=本片的表或結論;白框=證據;橘虛框=風險;黑框=外部唯讀或無法判定;灰虛框=別片的結論。B 段是本片的招牌產出——十組同名方法的逐段對照，把「A = 遷移改名」從推測升級成事實;E 段則是新發現：OFD019A / OFD020A 的遷移只做了一半。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping` / `TableMapping`)

26 支宣告 27 張表,一支一張,只有 `OFDM015` 有明細:

| 畫面 | 主檔(DB 表名) | VDB 表名 | 明細 | 宣告錨點 |
|---|---|---|---|---|
| `OFDM001` | `OFD001` | `OFDM001` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:45` |
| `OFDM002` | `OFD002` | `OFD002` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:51` |
| `OFDM003` | `OFD003A` | `OFDM003` | — (走 `MasterTable.Add`,多筆型) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:41` |
| `OFDM004` | `OFD004` | `OFDM004` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM004_PO.cs:45` |
| `OFDM005` | `OFD005` | `OFDM005` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM005_PO.cs:45` |
| `OFDM006` | `OFD006A` | `OFDM006` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM006_PO.cs:55` |
| `OFDM007` | `OFD007A` | `OFDM007` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM007_PO.cs:55` |
| `OFDM009` | `OFD009` | `OFDM009` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM009_PO.cs:45` |
| `OFDM010` | `OFD010` | `OFDM010` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM010_PO.cs:45` |
| `OFDM011` | `OFD011` | `OFDM011` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM011_PO.cs:45` |
| `OFDM012` | `OFD012A` | `OFDM012` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM012_PO.cs:47` |
| `OFDM013` | `OFD013A` | `OFDM013` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM013_PO.cs:46` |
| `OFDM014` | `OFD014` | `OFDM014` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM014_PO.cs:45` |
| `OFDM015` | `OFD015` | `OFD015` | **`OFD016`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:45-46` |
| `OFDM017` | `OFD017A` | `OFDM017` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:39` |
| `OFDM017B` | `OFD017B` | `OFDM017B` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017B_PO.cs:13` |
| `OFDM019` | `OFD019A` | `OFDM019` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:43` |
| `OFDM020` | `OFD020A` | `OFDM020` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:52` |
| `OFDM022` | `OFD022` | `OFDM022` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:31` |
| `OFDM023` | `OFD023A` | `OFD023` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:50` |
| `OFDM024` | `OFD024A` | `OFD024` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:50` |
| `OFDM025` | `OFD025A` | `OFDM025` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM025_PO.cs:41` |
| `OFDM026` | `OFD026` | `OFDM026` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM026_PO.cs:25` |
| `OFDM027` | `OFD027A` | `OFDM027` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM027_PO.cs:37` |
| `OFDM028` | `OFD028` | `OFDM028` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM028_PO.cs:26` |
| `OFDM029` | `OFD029` | `OFDM029` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM029_PO.cs:26` |

兩個要注意的地方:

1. **VDB 表名多數等於畫面代號而不是 DB 表名。** 這會讓自動化掃描對不上 —— `atlas_scan.py --screen OFDM019` 抓得到主檔是 `OFD019A`,但抓不到欄位中文名,因為 xsd 裡的 DataTable 叫 `OFDM019`。只有 `OFDM002` / `OFDM015` / `OFDM023` / `OFDM024` 四支的 VDB 表名跟 DB 表名一致。

2. **`OFDM003` 用的是 `MasterTable.Add(...)` 不是 `MasterTable = ...`**,因為它繼承 `BaseMultiRowEVADaoPO`(多筆型),一次寫入一整個月的日期列(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:32`)。

### 2.2 `A` 後綴的判定:十三列逐張過

前面兩片得到互相矛盾的結論 —— `ofd7.md §2` 說費率表那群的 `A` 是**境內**(`FUND_TYPE='2'`)、無後綴是**境外**;`ofd4.md §2.2` 說機構主檔那群的 `A` 是 **MSSQL → Oracle 遷移時的改名**。本片有十二張帶 `A`、十四張不帶,是最好的仲裁樣本,以下逐張跑 `ofd4.md` 那套三條判準。

**判準與操作定義**

| 判準 | 怎麼查 | 判成什麼 |
|---|---|---|
| (a) 全庫有沒有同名不帶 `A` 的表 | `grep -rn 'FROM OFDnnn\b' Dev DB` | 有,且只出現在 `MSSQL/` 目錄或註解裡 → 支持「遷移改名」 |
| (b) `MSSQL/BasicOFD_PO.cs` 與 `Basic/BasicOFD_PO.cs` 的**同名方法**讀哪張表 | 比對方法名相同的兩段 SQL | 欄位清單一字不差、只差表名與參數符號(`@`→`:`) → **決定性證據** |
| (c) 表裡有沒有 `FUND_TYPE` / `SHORE_ID` 欄 | 掃 `DataEntity.OFD1/2/3` 的 xsd | 有 `SHORE_ID` 才可能是境內外(值域 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301`,`OnShore="2"` / `OffShore="1"`) |

**十三列判定表**

| # | 表 | (a) 無 `A` 同名表 | (b) 同名方法對照 | (c) `FUND_TYPE` / `SHORE_ID` | 判定 | 決定性錨點 |
|---|---|---|---|---|---|---|
| 1 | `OFD003A` | 有,4 處(2 支 Oracle SP + 1 支舊世代 PO) | Common 內無同名方法可對照 | 無 | **遷移改名**(證據中等) | 舊名活用:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:346`(同段用 `@CAL_DATE`,是未遷移碼)、`DB/SP/S_OTA_OFDB600A_EXE.sql:172` |
| 2 | `OFD006A` | 有,只在 MSSQL 層與註解 | `GetFundKind`:MSSQL 讀 `OFD006`、Oracle 讀 `OFD006A`,三個欄位一字不差 | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:1419-1422` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2534-2537` |
| 3 | `OFD007A` | 有,只在 MSSQL 層與註解 | `GetFundType`:同上 | 有 `FUND_TYPE`,**但它是本表 PK「基金型態代碼」,不是境內外旗標** | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:1490` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2594`;欄義見 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM007Model.xsd` |
| 4 | `OFD012A` | 有,只在 MSSQL 層與註解 | `GetAfeeTypeDataSrc`:MSSQL `OFD012` / Oracle `OFD012A` | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:3343` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:5194` |
| 5 | `OFD013A` | 有,MSSQL 層 + 4 支 Oracle SP | `GetDividendTypeDataSrc`:MSSQL `OFD013` / Oracle `OFD013A` | 無 | **遷移改名**(SP 端未跟上) | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:3483` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:5308` |
| 6 | `OFD017A` | 有,只在 MSSQL 層與註解 | `GetBFSortCDDataSrc`:MSSQL `OFD017` / Oracle `OFD017A` | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:638` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:746` |
| 7 | `OFD019A` | 有,而且**在 Oracle 層也活著** | 六對同名方法改了(`GetFundWithCusBank` / `GetSubAccountNoDataSrc` / `GetRspSubBankDataSrc` / `DataCenterDataSrc` / `GetConfirmBankHqData` / `GetSealSubBankDataSrc`),**四支沒改**(`GetBankHqData` / `GetBankData` / `GetSubBank` / `GetAgentBankDataSrc`) | 無 | **遷移改名(遷移不完整)** | 改了:`Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:4397` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6119`;沒改:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:355`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6505` |
| 8 | `OFD020A` | 有,而且**在 Oracle 層也活著** | 六對改了,**兩支沒改**(`GetBankBrhData` / `GetBankData`) | 無 | **遷移改名(遷移不完整)** | 改了:`Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:2726` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4441`;沒改:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:254`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:477` |
| 9 | `OFD023A` | 有,只在 MSSQL 層與註解 | `GetSiceData`:MSSQL `OFD023` / Oracle `OFD023A` | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:2088` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:3628` |
| 10 | `OFD024A` | 有,只在 MSSQL 層與註解 | `GetSiteData`:MSSQL `OFD024` / Oracle `OFD024A` | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:2173` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:3700` |
| 11 | `OFD025A` | 有,只在 MSSQL 層與註解 | `GetBF_MCDDataSrc`:MSSQL `OFD025` / Oracle `OFD025A`,兩欄一字不差 | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:579-581` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:698-700` |
| 12 | `OFD027A` | 有,只在 MSSQL 層 | `GetMktIdData`:MSSQL `OFD027` / Oracle `OFD027A` | 無 | **遷移改名** | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:1717` vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2941` |
| 13 | `OFD017B` | 後綴是 `B` 不是 `A`;全庫查無 `OFD017BA`,`OFD017B` 只出現在 2 個檔案 | 無同名方法 | 無 | **都不是** —— `B` 是「同一個業務概念的第二張表」,由獨立的 `OFDM017B` 維護(§4.5) | `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017B_PO.cs:13` |

**統計:遷移改名 12 張(其中 2 張遷移不完整)· 境內外 0 張 · 都不是 1 張 · 無法判定 0 張。**

**十四張不帶 `A` 的表作為對照組同樣一致:** `OFD001` `OFD002` `OFD004` `OFD005` `OFD009` `OFD010` `OFD011` `OFD014` `OFD015` `OFD016` `OFD028` 這十一張在 `MSSQL/BasicOFD_PO.cs` 與 `Basic/BasicOFD_PO.cs` **用的是同一個名字**(例:`GetFundKind` 那段的隔壁,`OFD002` 兩邊皆為 `OFD002`),代表遷移時沒改;`OFD022` `OFD026` `OFD029` 則兩邊都沒出現(只有自己的畫面在用)。**沒有任何一張不帶 `A` 的表在 Oracle 層改用 `A` 名。**

**結論(本片可以下的定論)**

1. `ofd4.md §2.2` 的結論在本片**完全成立**,而且證據強度高一級 —— `ofd4.md` 只有 `OFD034` 一組對照,本片有**十組同名方法的逐段對照**,欄位清單一字不差,只差表名與參數符號。

2. `ofd7.md §2` 那條「`A` = 境內 `FUND_TYPE='2'`」的規則**不能外推到本片**:本片十二張 `A` 表沒有任何一張有 `SHORE_ID` 欄;唯一有 `FUND_TYPE` 欄的 `OFD007A`,那個欄是它自己的 PK「基金型態代碼」,值域是基金型態不是境內外。兩片可以同時為真 —— `ofd7.md` 描述的是**費率表那一群刻意成對設計**的表,本片與 `ofd4.md` 描述的是**遷移工程的產物**。所以 `A` 後綴在 OFD 模組裡**至少有兩種互不相干的成因**,看到 `A` 不能直接套任何一種,要逐張查。

3. 「不是全面規則」這件事本片再度確認:遷移時 26 張表只改了 12 張,`OFD001` / `OFD002` / `OFD015` 這種同樣被大量使用的主檔一個字都沒改。**改不改名沒有規律可循。**

### 2.3 `OFD019A` / `OFD020A`:遷移只做了一半

這是本片最值得警戒的資料模型問題,而且 `ofd4.md` 沒遇過這種形態。

`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` 是 Oracle 版的共用資料來源,理論上應該全用新表名。實際上:

| 方法 | Oracle 版讀的表 | 錨點 |
|---|---|---|
| `GetRspSubBankDataSrc` | `OFD019A` ✅ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6119` |
| `GetConfirmBankHqData` | `OFD019A` ✅ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6880` |
| `GetSealSubBankDataSrc` | `OFD019A` ✅ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:7497` |
| `GetBankHqData` | `OFD019` ❌ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:355` |
| `GetBankData` | `OFD019` + `OFD020` ❌ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:434`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:477` |
| `GetAgentBankDataSrc` | `OFD019` ❌ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6505` |
| `GetBankBrhData` | `OFD020` + `OFD019` ❌ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:254` |
| `GetNfdBankBrhDataSrc` | `OFD020A` ✅ | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4441` |

**維護入口只有一個**:`OFDM019` 寫 `OFD019A`、`OFDM020` 寫 `OFD020A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:43`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:52`)。所以上表打 ❌ 的那六支方法,**讀到的不是使用者剛剛維護的資料**。兩種可能:

- **假設一(較可能)**:Oracle 端建了 `OFD019` / `OFD020` 當成 `OFD019A` / `OFD020A` 的同義詞(SYNONYM)或視圖,所以能跑。依據是這些方法是共用下拉選單來源,若整個壞掉早就被發現。

- **假設二**:Oracle 端真的有兩張獨立的舊表,那六支方法讀到的是遷移當下的快照,之後的異動都沒進去。

**repo 內無法證實哪一種** —— `DB/Table/` 放的是票號變更腳本,沒有這兩張表的 DDL(`ls DB/Table` 共 158 個檔,無 `OFD019*` / `OFD020*` 建表腳本)。這條要到 DB 上下 `SELECT object_type FROM user_objects WHERE object_name IN ('OFD019','OFD019A')` 才能確認。**標假設**,並寫進附錄 E.5。

### 2.4 表的主鍵與四眼欄位

27 張表的 PK 全部來自 xsd 的 `xs:unique` + `msdata:PrimaryKey="true"`:

| 表 | 主鍵 | 欄數 | 四眼欄位 | PK 錨點 |
|---|---|---|---|---|
| `OFD001` | `TSCD_AGENT` | 20 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM001Model.xsd` |
| `OFD002` | `DEPT_NO` | 28 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM002Model.xsd` |
| `OFD003A` | `CALENDER_TYPE` + `CAL_DATE` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM003Model.xsd` |
| `OFD004` | `PROF_TYPE_TSCD` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM004Model.xsd` |
| `OFD005` | `FUND_TYPE_TSCD` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM005Model.xsd` |
| `OFD006A` | `PROF_TYPE` | 18 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM006Model.xsd` |
| `OFD007A` | `FUND_TYPE` | 18 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM007Model.xsd` |
| `OFD009` | `REGIST_CODE` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM009Model.xsd` |
| `OFD010` | `INVEST_AREA` | 20 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM010Model.xsd` |
| `OFD011` | `INVEST_CODE` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM011Model.xsd` |
| `OFD012A` | `AFEE_TYPE` | 17 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM012Model.xsd` |
| `OFD013A` | `DIVIDEND_TYPE` | 17 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM013Model.xsd` |
| `OFD014` | `RFEE_TYPE` | 20 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM014Model.xsd` |
| `OFD015` | `GRADE_CORP_CD` | 21 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM015Model.xsd` |
| `OFD016` | `GRADE_CORP_CD` + `GRADE_CORP_TYPE` + `GRADE_CD` | 23 | 有 | 同上 |
| `OFD017A` | `BF_BOARD_CD` | 19 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM017Model.xsd` |
| `OFD017B` | `BF_BOARD_CD` | 17 | 有(**欄名小寫**:`dataid` / `Status` / `CreateID`…) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM017BModel.xsd` |
| `OFD019A` | `BANK_HQ` | 40 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD2/OFDM019Model.xsd` |
| `OFD020A` | `BANK_BRH` | 41 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM020Model.xsd` |
| `OFD022` | `BANK_HQ` + `CRNCY_CD` | 26 | 有(**欄名小寫**) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM022Model.xsd` |
| `OFD023A` | `SICE_CD` | 27 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM023Model.xsd` |
| `OFD024A` | `SITE_CD` | 27 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM024Model.xsd` |
| `OFD025A` | `BF_MCD` | 17 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM025Model.xsd` |
| `OFD026` | `CUST_TYPE` | 17 | 有(**欄名小寫**) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM026Model.xsd` |
| `OFD027A` | `MKT_ID` | 17 | 有 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM027Model.xsd` |
| `OFD028` | `CHANNEL_AREA_CODE` | 17 | 有(**欄名小寫**) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM028Model.xsd` |
| `OFD029` | `COUNTRY_CD` | 17 | 有(**欄名小寫**) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD3/OFDM029Model.xsd` |

**一個可以拿來當年代標記的線索**:四眼欄位的大小寫。`OFD017B` `OFD022` `OFD026` `OFD028` `OFD029` 這五張表的 xsd 把四眼欄位寫成 `dataid` / `Status` / `CreateID` / `CreateDate`(大小寫混合),其餘二十二張一律全大寫 `DATAID` / `STATUS` / `CREATEID`。**這五張正好就是 §3.2 那五支繼承 `BasicEVAPO` 的畫面** —— 大小寫風格與 PO 基底完全對齊,可以當成「這條鏈沒被遷移過」的第二個獨立指標。

### 2.5 欄位中文名(來自 xsd `msdata:Caption`)

以下只列業務欄位;四眼欄位(`DATAID` / `STATUS` / `CREATEID` / `CREATEDATE` / `UPDATEID` / `UPDATEDATE` / `ENTRYID` / `ENTRYDATE` / `VERIFYID` / `VERIFYDATE` / `APPROVEID` / `APPROVEDATE` / `REJECTID` / `REJECTDATE` / `DATAFLAG`)全表共通,不重覆列,也沒有 Caption。

**A 塊 公司組織與行事曆**

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD001` | `TSCD_AGENT` / `TSCD_AGENT_NAME` | 分公司代碼 / 分公司名稱 |
| `OFD002` | `DEPT_NO` / `DEPT_CH_NAME` / `DEPT_EN_NAME` / `DEPT_SH_NM` / `DEPT_MGR` / `TDCC_AGENT` / `DEPT_VALID_CODE` / `BRH_CODE` / `KEYIN_CODE` | 部門代碼 / 部門中文名稱 / 部門英文名稱 / 部門中文簡稱 / 部門主管 / 集保分公司代碼 / 部門有效碼 / 分公司註記 / KEYIN櫃檯單位 |
| `OFD003A` | `CALENDER_TYPE` / `CAL_DATE` / `CAL_MEMO` / `CAL_MONTH` / `CAL_YEAR` / `BUSS_ID` | 行事曆類別 / (無 Caption,日期 YYYYMMDD) / 備註說明 / 月 / 年 / (無 Caption,營業日否) |

**B / C / D 塊 基金屬性與費用代碼**

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD004` | `PROF_TYPE_TSCD` / `PROF_TYPE_NM_C_TSCD` / `PROF_TYPE_NM_E_TSCD` | 基金種類代碼(集保) / 基金種類中文名稱(集保) / 基金種類英文名稱(集保) |
| `OFD005` | `FUND_TYPE_TSCD` / `FUND_TYPE_NM_C_TSCD` / `FUND_TYPE_NM_E_TSCD` | 基金型態代碼 / 基金型態中文名稱 / 基金型態英文名稱 |
| `OFD006A` | `PROF_TYPE` / `PROF_TYPE_NM_C` / `PROF_TYPE_NM_E` | 基金種類代碼 / 基金種類中文名稱 / 基金種類英文名稱 |
| `OFD007A` | `FUND_TYPE` / `FUND_TYPE_NM_C` / `FUND_TYPE_NM_E` | 基金型態代碼 / 基金型態中文名稱 / 基金型態英文名稱 |
| `OFD009` | `REGIST_CODE` / `REGIST_NM_C` / `REGIST_NM_E` | 註冊地代碼 / 註冊地中文名稱 / 註冊地英文名稱 |
| `OFD010` | `INVEST_AREA` / `INVEST_NM_C` | 投資區域代碼 / 投資區域中文名稱 |
| `OFD011` | `INVEST_CODE` / `INVEST_NM_C` / `INVEST_NM_E` | 投資地區代碼 / 投資地區代碼中文名稱 / (無 Caption) |
| `OFD012A` | `AFEE_TYPE` / `AFEE_TYPE_NM_C` | 申購手續費收取方式 / 申購手續費收取方式中文說明 |
| `OFD013A` | `DIVIDEND_TYPE` / `DIVIDEND_TYPE_NM_C` | 收益分配方式 / 收益分配方式中文說明 |
| `OFD014` | `RFEE_TYPE` / `RFEE_TYPE_NM_C` | 贖回費收取方式碼 / 贖回費收取方式名稱 |

> **B 與 C 的欄名幾乎鏡像**:`PROF_TYPE_TSCD` 對 `PROF_TYPE`、`FUND_TYPE_TSCD` 對 `FUND_TYPE`,只差 `_TSCD` 後綴與 Caption 裡的「(集保)」三個字。這是本片最容易看錯的地方 —— 兩套代碼獨立維護、沒有對照表、也沒有任何程式把兩者兜起來(附錄 E.14)。

**E / F 塊 信評與受益人分類**

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD015` | `GRADE_CORP_CD` / `GRADE_CORP_CNAME` / `GRADE_CORP_ENAME` | 信評公司代碼 / 信評公司中文名稱 / 信評公司英文名稱 |
| `OFD016` | `GRADE_CORP_CD` / `GRADE_CORP_TYPE` / `GRADE_CD` / `GRADE_SEQ` / `GRADE_STATEMENT` | 信評公司代碼 / 評等等級種類 / 評等等級 / 評等等級序號 / 評等等級敍述 |
| `OFD017A` | `BF_BOARD_CD` / `BF_BOARD_DESCRP` / `BF_COUNTRY_CLB` / `BF_COUNTRY_CLB_DESCRP` | 受益人公會類別代碼 / 受益人公會類別說明 / 大陸人士身分別代碼 / 大陸人士身分別 |
| `OFD017B` | `BF_BOARD_CD` / `BF_BOARD_DESCRP` | 受益人類別代碼 / 受益人類別說明 |

**G 塊 金融機構**(`OFD019A` 40 欄、`OFD020A` 41 欄,只列業務欄)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD019A` | `BANK_HQ` / `BANK_HQ_NAME` / `BANK_HQ_SHNM` / `BANK_HQ_NM_E` / `BANK_HQ_SHNM_E` | 金融機構總行代碼 / 總行名稱 / 總行簡稱 / 總行英文名稱 / 總行英文簡稱 |
| `OFD019A` | `BANK_TYPE` / `FISC_CD` / `FISC_ID` / `SWIFT_CODE` / `REMIT_BANK` | 銀行類型 / 金資編碼否 / 金資中心識別碼 / SWIFT代碼 / 中間銀行 |
| `OFD019A` | `DEPOSIT_LENGTH1` / `DEPOSIT_LENGTH2` / `DEPOSIT_LENGTH3` | 帳號長度一 / 帳號長度二 / 帳號長度三 |
| `OFD019A` | `SEAL_CHK_CODE1` / `SEAL_CHK_CODE2` / `SEAL_CHK_CODE3` | 核印扣款方式1 / 核印扣款方式2 / 核印扣款方式3 |
| `OFD019A` | `BANK_VALID_CODE` / `IS_EC_SHOW` / `IS_ACH_PAY` / `BOND_TRD` / `BANK_MEMO` | 銀行有效碼 / 開戶買回行呈現 / ACH代付銀行 / (無 Caption) / (無 Caption) |
| `OFD019A` | `MAIL_ZIP` / `BANK_ADDR` / `BANK_TEL_AREA` / `BANK_TEL` | 郵遞區號 / 銀行地址 / 銀行電話區域碼 / 銀行電話 |
| `OFD020A` | `BANK_BRH` / `BANK_BRH_NAME` / `BANK_BRH_SHNM` / `BANK_BRH_NM_E` / `BANK_BRH_SHNM_E` | 金融機構分行代碼 / 分行名稱 / 分行簡稱 / 分行英文名稱 / 分行英文簡稱 |
| `OFD020A` | `SEAL_CHK_CODE2` / `SEAL_CHK_CODE3` / `ACH_CODE_YN` / `BANK_VALID_CODE` | 核印扣款方式(ACH) / 核印扣款方式(財金) / ACH自編代號否 / 銀行有效碼 |
| `OFD020A` | `BRH_STAFF` / `BRH_MANAGER` / `BRH_FUND_PERSON` / `BRH_OTH_PERSON` / `EMP_NO` | 分行經辦 / 分行經理 / 基金督導 / 其他人員 / 員工代碼 |
| `OFD020A` | `AREA_CODE` / `GRADE` / `SWIFT_CODE` / `FISC_ID` / `BANK_MEMO` | 區域代碼 / 等級 / SWIFT代碼 / 金資中心識別碼 / 備註說明 |
| `OFD022` | `BANK_HQ` / `CRNCY_CD` / `REMIT_BANK_NM_C` / `REMIT_BANK_SHNM_C` / `REMIT_BANK_NM_E` / `REMIT_BANK_SHNM_E` | 金融機構總行代碼 / 幣別代碼 / 中間銀行中文名稱 / 中間銀行中文簡稱 / 中間銀行英文名稱 / 中間銀行英文簡稱 |
| `OFD022` | `REMIT_BANK_SWIFT` / `REMIT_BANK_ABA` / `REMIT_ACCOUNT` | 中間銀行SWIFT / 中間銀行ABA NO / 中間銀行帳號 |

**H / I 塊 外部機構與分類代碼**

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD023A` | `SICE_CD` / `SICE_NM_C` / `SICE_SHNM_C` / `SICE_NM_E` / `SICE_PRESENT` / `SICE_GM` | 投顧公司代碼 / 中文名稱 / 中文簡稱 / 公司英文名稱 / 負責人 / 總經理 |
| `OFD024A` | `SITE_CD` / `SITE_NM_C` / `SITE_SHNM_C` / `SITE_NM_E` / `SITE_PRESENT` / `SITE_GM` | 投信公司代碼 / 中文名稱 / 中文簡稱 / 英文名稱 / 負責人 / 總經理 |
| `OFD025A` | `BF_MCD` / `MCD_DESC` | 開戶來源代碼 / 開戶來源代碼說明 |
| `OFD026` | `CUST_TYPE` / `TYPE_DESC` | 潛在客戶類別代碼 / 潛在客戶類別說明 |
| `OFD027A` | `MKT_ID` / `MKT_DESCRP` | 行銷身份群族代碼 / 行銷身份群族代碼說明 |
| `OFD028` | `CHANNEL_AREA_CODE` / `CHANNEL_AREA_DESC` | 區域代碼 / 區域說明 |
| `OFD029` | `COUNTRY_CD` / `COUNTRY_NAME` | 帳戶國別代碼 / 帳戶國別名稱 |

### 2.6 狀態碼

本片沒有業務狀態機。唯一的狀態欄 `STATUS` 是四眼框架的欄位,由 `xEVAUtility` 寫入,本片 26 支沒有一支自己操作它(全庫 grep `row.STATUS` 在本片只命中 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:84` 一處,而且那是把主檔的值抄給明細,不是自己設值)。語意見 `architecture.md §3`。

業務層的「開關碼」只有四種,全部是 `'Y'` / `'N'`:

| 欄位 | 值域 | 來源 |
|---|---|---|
| `DEPT_VALID_CODE` / `BANK_VALID_CODE` | `'Y'` 有效 / `'N'` 無效 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81-91` |
| `BUSS_ID` | `'Y'` 營業日 / `'N'` 休市 | 由 `OFDM003` 的月曆控件反推:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:82-89` |
| `SEAL_CHK_CODE1/2/3` · `IS_EC_SHOW` · `IS_ACH_PAY` · `BOND_TRD` · `ACH_CODE_YN` · `BRH_CODE` · `KEYIN_CODE` | `'Y'` / `'N'`,由畫面 checkbox 轉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:164-178` |
| `FISC_CD` | `'Y'` 金資編碼 / `'N'` 非金資 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:351-358` |

## 3. 畫面清冊

```text
[圖] OFD1-3 二十六支畫面依 PO 基底與編譯狀態的分群，五支執行期必 NRE 的畫面，以及判斷基底時的註解陷阱
圖中文字:① 現行單筆型 BaseEVADaoPO：20 支，走 xEVAEventArgs / xTableMapping / OFDM001 OFDM002 OFDM004 / 在 csproj 可執行 / OFDM005 OFDM006 OFDM007 / 在 csproj 可執行 / OFDM009 OFDM010 OFDM011 / 在 csproj 可執行 / OFDM012 OFDM013 / 在 csproj / OFDM014 OFDM015 OFDM017 / 在 csproj 可執行 / OFDM019 OFDM020 OFDM023 / 在 csproj 可執行 / OFDM024 OFDM025 OFDM027 / 在 csproj 可執行 / 合計 20 支 / 缺漏 0 / ② 現行多筆型 BaseMultiRowEVADaoPO：1 支，一次寫一整個月 / OFDM003 / MasterTable.Add 多筆 / 三個自訂動作 / 設假日 / 複製 / 新增年度 / 自己開兩條交易分批 commit / 核對寫入筆數 寫法正確 / 跨 DB 寫 MSSQL / 不在交易內 無補償 / ③ 舊世代 BasicEVAPO：5 支，在 csproj 但按查詢就 NRE / OFDM017B OFDM022 / BasicEVAPO / OFDM026 OFDM028 OFDM029 / BasicEVAPO / dbTA 宣告即 null / 建構子賦值整段被註解 / Select 第一行 / dbTA.CreateConnection() / 子類沒覆寫任何一支 / 也沒自行賦值 dbTA / _Ctl 不繼承 BaseController / 直接 new PO 再呼叫 / xsd 四眼欄位小寫 / dataid / Status / CreateID / OFDM022 另有 T-SQL / 中括號 27 處 dbo. 函式 / ④ 判斷基底的坑：先剝掉 // 註解再看 / OFDM017_PO.cs:51 / // class … : Basic_PO / 第 34 行才是現行的 / BaseEVADaoPO / 同型還有四支 / 012 / 013 / 019 / 020 / 直接 grep 會誤判 / 先 strip_cs_comments / ⑤ csproj 核對：26 支 x 6 層 = 156 個檔案項目，逐一確認 / UI / FormProxy / Control / PO / 各 26 支 全在 / DataEntity.OFD1 / 2 / 3 / 各 26 份 Model.xsd 全在 / UIEntity.OFD1 / 2 / 3 / 各 26 份 View.xsd 全在 / 缺漏 0 / 但抓不到死畫面
```

*圖:圖 3 PO 基底分群。橘框=可執行的維護入口;橘虛框=風險或死的;白框=機制;黑框=框架無原始碼。最重要的是 ③ 與 ⑤ 放在一起看：26 支全部在 csproj、全部編得起來，但其中五支連按查詢都會 NullReferenceException——csproj 檢查抓不到執行期的死畫面。*

### 3.1 維護 M(全部 26 支)

「PO 基底」欄:`BaseEVADaoPO` = 現行單筆型 · `BaseMultiRowEVADaoPO` = 現行多筆型 · **`BasicEVAPO` = 舊世代,執行期必 NRE(標紅)**。「在 csproj」欄逐支核對六層 × 6 個 csproj,26 × 6 = **156 個檔案項目全部命中,缺漏 0**(核對方法見附錄 D.2)。

| 代號 | 中文名(推測) | 六層齊不齊 | 主表 | 明細 | PO 基底 | 在 csproj | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|---|---|
| `OFDM001` | 集保分公司基本資料 | 六層齊 | `OFD001` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM002` | 部門基本資料(大 / 中 / 小三級) | 六層齊 | `OFD002` | — | `BaseEVADaoPO`(覆寫 `Add`) | ✅ 六層皆在 | Trigger `OFD002_T01` | — |
| `OFDM003` | 營業日行事曆 | 六層齊 | `OFD003A` | — | `BaseMultiRowEVADaoPO` | ✅ 六層皆在 | MSSQL SP `S_PAM_OFD003A_SWSYS011`(**版控外**) | — |
| `OFDM004` | 基金種類代碼(集保) | 六層齊 | `OFD004` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM005` | 基金型態代碼(集保) | 六層齊 | `OFD005` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM006` | 基金種類代碼(內部) | 六層齊 | `OFD006A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM007` | 基金型態代碼(內部) | 六層齊 | `OFD007A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM009` | 註冊地代碼 | 六層齊 | `OFD009` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM010` | 投資區域代碼 | 六層齊 | `OFD010` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM011` | 投資地區代碼 | 六層齊 | `OFD011` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM012` | 申購手續費收取方式 | 六層齊 | `OFD012A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM013` | 收益分配方式 | 六層齊 | `OFD013A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM014` | 贖回費收取方式 | 六層齊 | `OFD014` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM015` | 信評公司與評等等級 | 六層齊 | `OFD015` | **`OFD016`** | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM017` | 受益人公會類別 | 六層齊 | `OFD017A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM017B` | 受益人類別 | 六層齊 | `OFD017B` | — | 🔴 **`BasicEVAPO`** | ✅ 六層皆在 | — | — |
| `OFDM019` | 金融機構總行 | 六層齊 | `OFD019A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | Oracle Fn `f_TA_GetBankHQ` | — |
| `OFDM020` | 金融機構分行 | 六層齊 | `OFD020A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM022` | 中間銀行(跨國匯款) | 六層齊 | `OFD022` | — | 🔴 **`BasicEVAPO`** | ✅ 六層皆在 | T-SQL Fn `dbo.f_GetToDoData`(**Oracle 上不存在**) | — |
| `OFDM023` | 投顧公司基本資料 | 六層齊 | `OFD023A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM024` | 投信公司基本資料 | 六層齊 | `OFD024A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM025` | 開戶來源代碼 | 六層齊 | `OFD025A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM026` | 潛在客戶類別 | 六層齊 | `OFD026` | — | 🔴 **`BasicEVAPO`** | ✅ 六層皆在 | — | — |
| `OFDM027` | 行銷身份群族代碼 | 六層齊 | `OFD027A` | — | `BaseEVADaoPO` | ✅ 六層皆在 | — | — |
| `OFDM028` | 通路區域代碼 | 六層齊 | `OFD028` | — | 🔴 **`BasicEVAPO`** | ✅ 六層皆在 | — | — |
| `OFDM029` | 帳戶國別代碼 | 六層齊 | `OFD029` | — | 🔴 **`BasicEVAPO`** | ✅ 六層皆在 | — | — |

> 「六層齊不齊」欄全部是「六層齊」不是湊數:26 支逐支跑 `atlas_scan.py --screen`,UI / FormProxy / Control / PO / DataEntity / UIEntity 六個檔一個不缺。本片**沒有**檔案存在但不在 csproj 的死畫面,也沒有缺層的半成品。

### 3.2 五支繼承 `BasicEVAPO` 的畫面 —— 連按查詢都會 NullReferenceException

**先說判斷方法的坑。** 直接 `grep 'class .*_PO :'` 會誤判:本片有四支檔案(`OFDM012` `OFDM013` `OFDM017` `OFDM019` `OFDM020`)在註解區保留著一整段舊版 `//public class OFDMxxx_PO : Basic_PO`,例如 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:51`。判斷基底前要先用 `strip_cs_comments` 把 `//` 抹掉,再看還活著的那一行 —— `OFDM017_PO` 真正的基底在第 34 行,是 `BaseEVADaoPO`。剝完註解後,本片真正繼承 `BasicEVAPO` 的是這五支:

| 畫面 | PO 宣告錨點 | PO 檔案行數 | 活的程式碼 | 有無自行賦值 `dbTA` | 有無覆寫 `Add` / `Select` |
|---|---|---|---|---|---|
| `OFDM017B` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017B_PO.cs:8` | 25 | 22 行 | 無 | 無 |
| `OFDM022` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:20` | 1,255 | 196 行 | 無 | 無(只掛三個組 SQL 的事件) |
| `OFDM026` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM026_PO.cs:18` | 870 | 33 行 | 無 | 無 |
| `OFDM028` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM028_PO.cs:19` | 866 | 33 行 | 無 | 無 |
| `OFDM029` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM029_PO.cs:19` | 41 | 31 行 | 無 | 無 |

**為什麼一定 NRE**(事實已在 `architecture.md §3` 查證,本片複述關鍵四點):

1. `BasicEVAPO` 的 `dbTA` 宣告即 `= null`:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`

2. 建構子裡建立連線那四行**整段被註解**:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-172`

3. `Add()` 第一行就 `cn = dbTA.CreateConnection();`:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`

4. **`Select()` 第一行也是** `DbConnection cn = dbTA.CreateConnection();`:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:795-797` —— 所以不是存檔才炸,是**按查詢就炸**,和 `ofd6.md` 的結論一致

**第五個獨立佐證:`_Ctl` 不繼承 `BaseController`。** 這五支的 Control 層是裸類別,自己 `new` PO 再呼叫,不走 `DataAccessPool`:

| 畫面 | `_Ctl` 宣告 | 呼叫方式 |
|---|---|---|
| `OFDM017B` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM017B_Ctl.cs:11`(無基底) | 直接 `new` |
| `OFDM022` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM022_Ctl.cs:12`(無基底) | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM022_Ctl.cs:37` `new OFDM022_PO()` |
| `OFDM026` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM026_Ctl.cs:13`(無基底) | 直接 `new` |
| `OFDM028` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM028_Ctl.cs:12`(無基底) | 直接 `new` |
| `OFDM029` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM029_Ctl.cs:12`(無基底) | 直接 `new` |

對照組:`OFDM001_Ctl` 繼承 `BaseController` 並把 PO 丟進 `DataAccessPool`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM001_Ctl.cs:15`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM001_Ctl.cs:33`)。

**第六個佐證:T-SQL 痕跡。** 掃 26 支 PO(剝掉註解後)找 `[表名]` / `@變數` / `GetDate()` / `ISNULL` / `SELECT TOP` / `newid()` / `dbo.` 六種痕跡:

| 畫面 | T-SQL 痕跡 | 錨點 |
|---|---|---|
| `OFDM022` | `[OFD022]` / `[OFD019]` / `[FSK003]` 中括號界定符 **27 處**;`dbo.f_GetToDoData(...)` 1 處 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:101`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:166` |
| `OFDM017B` `OFDM026` `OFDM028` `OFDM029` | **無** —— 這四支的 PO 只有建構子掛表名,根本沒寫 SQL | — |
| `OFDM002`(不是 `BasicEVAPO`,但有殘留) | `@DEPT_NO` 出現在一句 Oracle SQL 裡 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1287`,見附錄 E.2 |
| `OFDM020`(不是 `BasicEVAPO`,但有殘留) | `"N'" + value + "'"` 的 T-SQL Unicode 字面量前綴 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:377` |

結論:**`OFDM022` 是五支裡唯一寫過 SQL 的**,而且那段 SQL 就算 `dbTA` 修好也跑不動(中括號與 `dbo.` 在 Oracle 上都是語法錯)。另外四支只是基底沒換,SQL 交給框架組,理論上把 `BasicEVAPO` 換成 `BaseEVADaoPO`、`TableMapping` 換成 `xTableMapping` 就能救活 —— 但那要連四眼欄位大小寫(§2.4)一起處理。

### 3.3 PO 檔案的「註解率」—— 八支超過 94 %

26 支 PO 的檔案行數與剝掉 `//` 註解後剩下的行數:

| 畫面 | 檔案行數 | 非空行 | 活的行 | 註解率 | 備註 |
|---|---|---|---|---|---|
| `OFDM026` | 870 | 717 | 33 | **95 %** | 舊 MSSQL 實作整段留著 |
| `OFDM028` | 866 | 717 | 33 | **95 %** | 同上 |
| `OFDM006` | 908 | 723 | 45 | **94 %** | 同上 |
| `OFDM007` | 916 | 722 | 45 | **94 %** | 同上 |
| `OFDM012` | 907 | 743 | 45 | **94 %** | 同上 |
| `OFDM013` | 909 | 743 | 44 | **94 %** | 同上 |
| `OFDM017` | 891 | 738 | 45 | **94 %** | 同上 |
| `OFDM025` | 882 | 731 | 42 | **94 %** | 同上 |
| `OFDM023` | 1,035 | 874 | 120 | 86 % |  |
| `OFDM024` | 1,038 | 874 | 120 | 86 % |  |
| `OFDM020` | 1,563 | 1,363 | 249 | 82 % | 全片最大的 PO 檔 |
| `OFDM022` | 1,255 | 1,046 | 196 | 81 % |  |
| `OFDM019` | 1,332 | 1,137 | 246 | 78 % |  |
| `OFDM002` | 1,321 | 1,122 | 305 | 73 % |  |
| `OFDM001` `OFDM004` `OFDM005` `OFDM009` `OFDM010` `OFDM011` `OFDM014` `OFDM015` | 70~71 | 56~57 | 45~46 | 19~20 % | 純框架,只有建構子 |
| `OFDM003` | 524 | 487 | 397 | 18 % | 本片邏輯最多的一支 |
| `OFDM027` | 50 | 44 | 40 | 9 % |  |
| `OFDM029` | 41 | 33 | 31 | 6 % |  |
| `OFDM017B` | 25 | 22 | 22 | 0 % |  |

**這張表的用途**:看到 `OFDM006_PO.cs` 有 908 行**不要以為它複雜** —— 它只有 45 行是活的,其餘全是 MSSQL 年代的舊實作。改這類檔案時,`git blame` 與全文檢索都會被註解區干擾,務必先剝註解。

### 3.4 `_PO` 的介面註解 21 支一模一樣,是複製貼上殘留

21 支繼承現行基底的 PO,介面上方的 XML summary **一字不差**都是「覆核層級管理 PO 共用介面」:

| 樣本 | 錨點 | 實際在管什麼 |
|---|---|---|
| `OFDM001_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:26` | 集保分公司 |
| `OFDM015_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:32` | 信評公司 |
| `OFDM017_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:26` | 受益人公會類別 |
| `OFDM019_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:26`(區域略有位移,同段) | 金融機構總行 |

**沒有一支的內容跟「覆核層級管理」有關。** 這 21 支的註解不可作為業務推測依據 —— 本文 §0.1 的推測全部改以欄位 `msdata:Caption` 與 SQL 條件為準。同一模式在 `ofd4.md §3.3` 也出現過,那邊是三支;本片是 21 支,幾乎是全數。

### 3.5 來源檔編碼:13 個檔案不是 UTF-8

掃 26 支 × 5 層(UI / FormProxy / Control / PO / Model.xsd)共 130 個檔,有 13 個只能用 cp950(Big5)解出來:

| 畫面 | 非 UTF-8 的層 | 檔案 |
|---|---|---|
| `OFDM003` | UI、PO | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs` |
| `OFDM004` | UI、PO | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM004.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM004_PO.cs` |
| `OFDM005` | UI、PO | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM005.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM005_PO.cs` |
| `OFDM006` | FormProxy、Control、PO | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM006_Pxy.cs`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM006_Ctl.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM006_PO.cs` |
| `OFDM007` | FormProxy、Control、PO | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM007_Pxy.cs`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM007_Ctl.cs`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM007_PO.cs` |
| `OFDM015` | UI | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs` |

**同一支畫面的六層編碼不一致**(`OFDM003` 的 UI 與 PO 是 Big5、Control 與 FormProxy 是 UTF-8),所以工具不能只探測一次就套用整條鏈。另外 `DB/Trigger/OFD002_T01.SQL` 也是 cp950。讀這些檔一律走 `sys.path.insert(0,'/docs/tools'); from atlas_scan import read_text`。

### 3.6 查詢 I

**本片無 I 型畫面。** 26 支的代號全部是 `OFDM###`,`atlas_scan.py --screen` 逐支確認型別皆為 M。參數主檔的查詢需求由各 M 畫面自己的第一頁(查詢頁)吃掉,不需要獨立查詢畫面。真正讀這些代碼檔的查詢畫面在別的片(例 `OFDI902` 讀 `OFD003A`)。

### 3.7 批次 B

**本片無 B 型畫面。** 唯一跨系統的寫入是 `OFDM003` 核准後往 MSSQL 推行事曆,那是 M 畫面的四眼後置動作,掛在 `AfterApprove` / `AfterApproveDelete` 上(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:464-477`),不是排程。

### 3.8 報表 R

**本片無 R 型畫面,也沒有任何 `.rpt`。** 參數檔本身不出報表;拿這些代碼去出報表的是 OTA / NFD.Report 等別的模組(§8.4)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFDM015 的主明細結構、存檔前的欄位灌值、三組全部落在 UI 的卡控，以及同一條規則三種不等價的寫法
圖中文字:① 本片唯一的主明細：一家信評公司掛多個評等等級 / OFDM015 主檔頁 / 公司代碼 / 中文名 / 英文名 / OFD015 / PK GRADE_CORP_CD / OFD016 明細 / PK 公司 + 種類 + 等級 / ugrdOFD016 grid / 四欄可編輯 / ② 存檔前 SetMasterToDetail：主檔灌 PK 與四眼狀態到每一列明細 / 主檔三欄 ← 畫面控件 / OFDM015.cs:75-77 / 明細 GRADE_CORP_CD ← 主檔 / PK 不由使用者輸入 / 明細 STATUS ← 主檔 STATUS / 註解：Status 也要給 / 跳過已刪的列 / RowState Deleted / ③ 三組卡控全部在 UI，PO 端一條都沒有 / GridCheck1 不可重覆 / 兩組鍵 BeforeCellUpdate / GridCheck2 必填 / BeforeRowInsert / Update / 存檔前總檢 DoValidate / 明細至少一列 + 序號 >= 1 / PO 只有空的 AfterUpdate / //nothing / 繞過 Form 的路徑 / 完全沒有保護 / ④ 同一條規則三種寫法，條件不等價 / 存檔前 GRADE_SEQ < 1 / 有訊息 阻擋 / 插入列 GRADE_SEQ < 1 / 無訊息 只 e.Cancel / 離開列 GRADE_SEQ == 0 / 只標紅 不擋 / 負數序號 / 不標紅 但存檔被擋 / ⑤ 其他無提示的行為 / 修改頁鎖住明細 PK / 兩格 NoEdit 無說明 / grid 錯誤全吞 / ugrdOFD016_Error 一律 Cancel / 序號清空自動填 0 / 再被檢核擋下 / 查詢一律 Like 前綴 / 查不到不提示
```

*圖:圖 4 OFDM015 主明細與卡控。橘框=關鍵步驟;白框=正常機制;橘虛框=風險或無提示的行為。要記住兩件事:① 所有業務檢核都在 UI，PO 端只有一個空的事件——繞過畫面的寫入路徑零保護;② 「序號不可為 0」被寫了三次而且條件不等價，負數序號在畫面上看不出錯。*

### 4.0 二十六支共同的骨架

先把重覆的講完,後面各節只寫差異。

**六層各做什麼**(以最乾淨的 `OFDM001` 為樣本)

| 層 | 做的事 | 錨點 |
|---|---|---|
| UI | 繼承 `xMaintainForm`,兩頁籤(查詢頁 + 維護頁),`FormInitial` 指定 `ProcessVDB` 與 `FormProxy`,`BeforeXxxButtonClicked` 做檢核 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM001.cs` |
| FormProxy | 轉呼叫 Control,無邏輯 | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM001_Pxy.cs` |
| Control | 繼承 `BaseController`,`InitializeDataAccessPool` 把 PO 丟進池,再逐個 `ExecPOActionToViewVDB` 包成 `AddData` / `ModifyData` / `DeleteData` / `GetData` / `GetMaintainData` / `GetToDoData` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM001_Ctl.cs:31-34`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM001_Ctl.cs:47-52` |
| PO | 建構子掛 `xTableMapping`,其餘交給 `BaseEVADaoPO` 自動組 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:43-50` |
| DataEntity / UIEntity | typed DataSet,欄位中文名在 `msdata:Caption` | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/OFDM001Model.xsd` |

**26 支共通的四眼流程**見 `architecture.md §3`,本片沒有任何一支改動它。

**兩個全片通用的骨架瑕疵**

| 瑕疵 | 範圍 | 說明 | 錨點 |
|---|---|---|---|
| `dbProduct = dbProduct;` 自我指派 | 9 支(`OFDM001` `OFDM002` `OFDM004` `OFDM005` `OFDM009` `OFDM010` `OFDM011` `OFDM014` `OFDM015`) | 建構子最後一行把欄位指派給自己,是個 no-op。推測原意是 `dbProduct = base.dbProduct` 或設定連線,結果什麼都沒做 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:49`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:48` |
| 空的 `AfterUpdate` 事件 | 8 支(同上 9 支扣掉 `OFDM002`) | 建構子掛了 `AfterUpdate`,handler 內只有一行 `//nothing` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:63-66`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:64-67` |

這兩項都不影響行為,但代表這 9 支是同一份範本複製出來的 —— 改其中一支的骨架時,要意識到另外 8 支長得一模一樣。

**一個全片通用的卡控**:26 支的「新增 / 修改前」都是同一個形狀 ——

```
this.DoValidate();                        // 跑 validatorManager1 + 自訂檢核
if (this.ValidateErrList.Show())          // 有錯就跳訊息視窗
    e.Cancel = true;                      // 取消動作
```

**但有 11 支在 `e.Cancel = true` 之後沒有 `return`**,而是繼續往下把畫面值抄進 DataRow(例 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:68-73`)。因為 `e.Cancel` 已經成立,那些抄值不會落到 DB,**目前沒有實害**;但只要有人在後面加一行有副作用的程式碼,就會在「使用者已經被擋下」的情況下執行。列在附錄 E.11。

### 4.1 `OFDM015` — 信評公司與評等等級(本片唯一的主明細)

**用途(推測)**:維護信評公司(標普 / 穆迪 / 惠譽…)以及每家公司底下的評等等級表。依據是 Caption「信評公司代碼」「評等等級」「評等等級序號」與主明細結構。

**主明細宣告**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:45-46`,主檔 `OFD015`(PK `GRADE_CORP_CD`)、明細 `OFD016`(PK `GRADE_CORP_CD` + `GRADE_CORP_TYPE` + `GRADE_CD`)。

**PO 端幾乎什麼都沒做。** 整支 PO 只有 71 行,活的 46 行,除了掛表名就只有一個空的 `AfterUpdate`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:64-67` 內容是 `//nothing`)。**所有業務檢核都在 UI**,這是本節最重要的一句話 —— 任何繞過 `OFDM015` 這支 Form 的寫入路徑(例如別的畫面直接 `new OFDM015_PO()`、或 DB 端直接 INSERT)完全沒有保護。

#### 4.1.1 三組檢核,全部在 UI

| 組 | 內容 | 觸發點 | 錨點 |
|---|---|---|---|
| **[GridCheck1] 不可重覆** | 明細裡「評等等級種類 + 評等序號」不可重覆、「評等等級種類 + 評等等級」不可重覆,兩組鍵都檢 | grid 的 `BeforeCellUpdate`(改一格就檢) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:221-226`;鍵的定義在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:106-110` |
| **[GridCheck2] 必填** | 「評等等級種類」「評等等級」「評等等級序號」三欄必填 | grid 的 `BeforeRowInsert`(點空白列)與 `BeforeRowUpdate`(離開列) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:231-241`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:246-262` |
| **存檔前總檢** | 明細必須至少一列;序號不可小於 1 | `BeforeAdd` / `BeforeModify` → `DoValidate()` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:51-67` |

**「評等序號不可為 0」被寫了三次**,而且三次的寫法不同:

| 位置 | 寫法 | 錨點 |
|---|---|---|
| 存檔前總檢 | `view.UIView.OFD016.Select("GRADE_SEQ<1").Length > 0` → 加錯誤訊息 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:58-59` |
| 插入列時 | 同一句 `Select("GRADE_SEQ<1")` → `e.Cancel = true`(**無訊息**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:239-240` |
| 離開列時 | `Convert.ToInt32(e.Row.Cells["GRADE_SEQ"].Value) == 0` → 只把該列標紅,不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:254-257` |

三處的判斷條件其實不等價:前兩處是「小於 1」(含負數),第三處是「等於 0」。**負數序號在離開列時不會被標紅**,但存檔會被擋 —— 使用者看不到是哪一列有問題。列入附錄 E.12。

#### 4.1.2 `SetMasterToDetail()` —— 明細的 PK 與 `STATUS` 由主檔灌進去

存檔前(`BeforeAdd` / `BeforeModify` 的最後一行)呼叫,把主檔的信評公司代碼與四眼狀態抄到每一列明細:

| 動作 | 說明 | 錨點 |
|---|---|---|
| `MasterRow.GRADE_CORP_CD/CNAME/ENAME` ← 畫面控件 | 主檔三欄從 textbox 抄回 DataRow | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:75-77` |
| 明細每列 `GRADE_CORP_CD` ← 畫面的公司代碼 | 明細 PK 的第一欄不由使用者輸入 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:83` |
| 明細每列 `STATUS` ← 主檔 `STATUS` | 註解直接寫「STATUS 也要給」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:84` |
| 跳過 `RowState == Deleted` 的列 | 已刪的列不動 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:81` |

> 這正是 `ofd4.md §4.1.6` 提到的那個坑的**正確版本** —— `ofd4.md` 那對畫面裡有一支漏了 `row.STATUS = MasterRow.STATUS`。`OFDM015` 沒漏,可以拿來當範本。

#### 4.1.3 修改頁把明細 PK 鎖成唯讀

進修改頁時,grid 每一列的 `GRADE_CORP_TYPE` 與 `GRADE_CD` 兩格設成 `Activation.NoEdit`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:145-149`)。所以**明細的 PK 一旦建立就改不了,只能刪掉重加** —— 但畫面上沒有任何提示說明這件事。

#### 4.1.4 `OFDM015` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進畫面 | 公司代碼與明細的評等等級只能輸入半形 | 打全形字自動擋掉 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:93-95` |
| grid 改格 | 「種類 + 序號」或「種類 + 等級」重覆 | 取消該格更新 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:225` |
| grid 插入列 | 「種類」「等級」未填 | `e.Cancel = true`,**無訊息** | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:236-237` |
| grid 插入列 | 有任一列序號 < 1 | `e.Cancel = true`,**無訊息** | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:239-240` |
| grid 離開列 | 「種類」「等級」未填或序號 = 0 | 該列標紅 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:254-257` |
| grid 離開格 | 序號被清空 | 自動回填 0 | 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:278-283` |
| grid 出錯 | 任何 grid 內部錯誤 | `e.Cancel = true` **吞掉** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:216-219` |
| 存檔前 | 明細 0 列 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:65` |
| 存檔前 | 必填欄未填 / 序號 < 1 | 「… 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:56-61` |
| 修改頁 | 明細 PK 兩欄 | 設成不可編輯 | 阻擋(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:147-148` |
| 查詢 | 公司代碼一律用 `Like` 前綴比對 | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:156` |
| **PO 端** | **無** | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:64-67` |

### 4.2 `OFDM019` 與 `OFDM020` — 金融機構總行與分行(下游最廣的兩張表)

這一對是本片最重的兩支:`OFD019A` 被 46 個檔案讀、`OFD020A` 被 33 個,合計覆蓋 BMS / EC / OTA / OTAB / OFDB / RSP / NFD.Report 等十個以上專案(§8.3)。兩支之間是**單向依賴**:分行去讀總行,總行不讀分行,但總行**會寫**分行。

#### 4.2.1 `OFDM019` 的三段旁寫(`AfterUpdate`)

存檔成功後,`OFDM019_PO_AfterUpdate` 會連續打三到四句 UPDATE 到別人的表,全部掛在同一個交易 `args.DbTran` 上(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:59-141`):

| 順序 | 目標表 | 條件 | 內容 | 錨點 |
|---|---|---|---|---|
| ① 有條件 | `OFD020A` | 只有 `m_IsUpVld` 為真時才做 | 把該總行**所有分行**的 `BANK_VALID_CODE` 設成和總行一樣,以 `f_TA_GetBankHQ(OFD020A.BANK_BRH) = :BANK_HQ` 找出屬於這家總行的分行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:67-79` |
| ② 無條件 | `OFD068A` | `AGENT_ID='1'` 且 `SUBSTR(AGENT_CODE,2,3)=:BANK_HQ` | 同步銷售機構的中英文名稱與簡稱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:83-103` |
| ③ 無條件 | `OFD071A` | `CHANNEL_CD='1'`、`SUBSTR(CHANNEL_CODE,2,3)=:BANK_HQ`、`LENGTH(CHANNEL_CODE)=5` | 同步通路說明 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:106-121` |
| ④ 有條件 | `OFD020A` | `BANK_TYPE` 是 `'04'`(農會)或 `'05'`(漁會)就**整段 return 跳過** | 把該總行所有分行的 `SEAL_CHK_CODE2` / `SEAL_CHK_CODE3` 蓋成總行的值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:124-140` |

**三個必須知道的行為**

1. **②③ 的 WHERE 最後一行都是「值不同才更新」,而且用 `<>`。** 例如 ② 的 `AND (AGENT_NAME<>:AGENT_NAME OR AGENT_NAME_E<>:AGENT_NAME_E OR AGENT_SHNM <> :AGENT_SHNM OR AGENT_SHNM_E<>:AGENT_SHNM_E)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:93`)。Oracle 的三值邏輯下,**只要那四個欄位在 `OFD068A` 裡全是 NULL,整個 OR 的結果是 UNKNOWN,那一列就不會被更新** —— 使用者改了總行名稱,銷售機構那邊沒跟著改,而且沒有任何訊息。③ 的 `AND CHANNEL_DESCRP<>:CHANNEL_DESCRP`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:113`)同病。見附錄 E.3。

2. **① 的旗標 `m_IsUpVld` 是 PO 的實例欄位,而且只在一種情況下被寫。** `BeforeUpdate` 只有在 `row.BANK_VALID_CODE == VALID_CODE.Invalid`(即 `'N'`)時才去 `COUNT` 並設值(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:143-160`);把總行從無效改回有效(`'Y'`)時 `BeforeUpdate` **整段不進去**,`m_IsUpVld` 維持上一次的值。宣告時預設 `false`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:37`),所以在「PO 實例每次請求都重建」的前提下行為正確 —— 但如果 `DataAccessPool` 把 PO 快取重用,第二次呼叫就會帶著上一次的旗標。**標假設**:本文沒有查證 `DataAccessPool` 的存活範圍。實務影響是「把總行改回有效時,分行不會跟著變回有效」—— 這一點無論假設成不成立都成立,因為 ① 那段 UPDATE 只有 `m_IsUpVld` 為真才跑。

3. **這四段 UPDATE 完全不經 `OFD020A` / `OFD068A` / `OFD071A` 自己的四眼。** 資料直接生效,對方畫面的 ToDo 清單不會出現這筆。

#### 4.2.2 `OFDM019` 的兩支檢核方法

| 方法 | 用途 | 讀哪些表 | 回傳約定 | 錨點 |
|---|---|---|---|---|
| `CheckBankHqData` | 刪除前確認總行沒被引用 | `OFD074` + `OFD076` + `OFD020A` + `OFD071A` + `OFD068A` 五張 `UNION ALL` 後 `SUM` | 一律 `ReturnCode = true`,筆數放 `ReturnRowCount`;UI 看筆數 ≠ 0 才擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:168-219`;UI 判斷在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:476-490` |
| `IsExistChangeData` | 修改前確認「核印扣款方式」沒被代扣款行用著 | `OFD074`,條件 `SIGN_END_DATE > 今天 OR AGENT_VALID_CODE = 'Y'` | 有衝突回 `false` + 訊息;無衝突回 `true` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:227-299` |

`CheckBankHqData` 的 `catch` 會回 `AddResultRow(false, 0, "")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:206-211`),UI 那邊 `ReturnCode` 為 false 就跳訊息並取消刪除(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:486-490`)—— **DB 出錯時是擋下來的**,方向正確,只是訊息是空字串,使用者會看到一個沒有內容的對話框。

`IsExistChangeData` 的 `catch` 同樣回 false,UI 把訊息掛在核印方式 1 的 checkbox 上再 `ValidateErrList.Show()`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:258-269`),也是擋下來 —— 一樣訊息為空。

#### 4.2.3 `OFDM019` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 總行代碼不足 3 碼 | 「金融機構總行代碼 須至少輸入三碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:153-158` |
| 新增 / 修改前 | `FISC_CD='N'` 但代碼第一碼是數字 | 「'金融機構總行代碼'第一碼必須為A~Z」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:349-355` |
| 新增 / 修改前 | `FISC_CD='Y'` 但代碼第一碼不是數字 | 「'金融機構總行代碼'第一碼必須為0~9」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:356-362` |
| 新增 / 修改前 | SWIFT 代碼有填但不是 8 碼 | 「'SWIFT代碼'必須8碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:363-369` |
| 新增 / 修改前 | 總行英文名稱 / 簡稱含非英數字 | 「…只限輸入英文及數字!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:339-347` |
| 新增 / 修改前 | 三個帳號長度有重覆(0 除外) | 「帳號長度…不能重覆」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:391-419` |
| 修改前 | 要關掉的核印方式已被 `OFD074` 使用 | 「該銀行的扣款方式…已被使用於代扣款行中(OFDM074)」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:275-280` |
| 修改前 | 查 `OFD074` 時 DB 出錯 | 空訊息 + 取消 | 阻擋(訊息為空) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:286-291` |
| 刪除前 | 總行已被五張表之一引用 | 「此總行代碼尚有所屬分行資料[OFDM020]或…故不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:204` |
| 改銀行類型 | 選農會 / 漁會 | 一般核印方式 checkbox 鎖死並取消勾選 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:545-551` |
| 存檔後 | 總行改無效 | 所有分行一起改無效 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:67-79` |
| 存檔後 | 名稱異動 | 同步 `OFD068A` / `OFD071A`;**四欄全 NULL 時靜默不同步** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:93` |
| 存檔後 | 銀行類型是 `'04'` / `'05'` | 分行核印方式**不連動** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:124-125` |
| 查詢 | 總行代碼 `Like` 前綴、銀行類型 `Equal` | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:143-147` |
| 被註解 | 「總行代碼為 700 時每日限額必輸」+「每日限額須大於 0」 | **完全不生效** | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:427-438`(整段包在 `/* */` 裡) |

#### 4.2.4 `OFDM020` 的三支 `Check` 方法,以及 `"-1"` 的兩種意思

`OFDM020_PO` 有三支手寫的檢核方法,**全部用字串回傳值當狀態碼**,而且同一個 `"-1"` 在不同方法裡意思相反:

| 方法 | 正常無問題時回 | 有業務問題時回 | **DB 出錯時回** | 錨點 |
|---|---|---|---|---|
| `CheckBANK_HQ` | `""`(空字串) | 「金融機構分行代碼前三碼須為金融機構總行代碼」 | **`"-1"`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:133-168` |
| `CheckSWIFT_CODE` | `""` | 「SWIFT 代碼前八碼要與總行相同」 | **`"-1"`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:175-211` |
| `CheckBANK_VALID_CODE` | **`"-1"`** | 「若總行為無效時,不可新增分行資料」 | **`"-1"`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:219-258` |

**第三支把「一切正常」和「DB 出錯」用同一個值表示**,而呼叫端是這樣寫的(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:480-497`):

```
strCheck = pxy.CheckBANK_VALID_CODE(this.utxtBANK_BRH.Text);
if (strCheck != "-1") { 有效碼鎖成 "N" 且唯讀 }
else                  { 有效碼開放,預設 "Y" }
```

也就是說 **DB 查不到 / 查爆了的時候,畫面會把新分行當成「總行有效」處理,開放使用者設成有效**。這是「`catch` 回成功 → DB 出錯等於通過」的標準形態,列入附錄 E.4。

另外要注意:`CheckBANK_VALID_CODE` **在新增流程的必檢路徑上被註解掉了**。`DoValidate` 裡呼叫它的那一行連同判斷共 12 行被 `//` 包起來(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:70`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:85-99`),現在只剩 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:483` 這個「取總行核印資料」的事件裡還在呼叫,而且那裡只拿來決定欄位唯讀,**不擋存檔**。所以「總行無效不可新增分行」這條規則四層俱全、訊息字串也還在,但**實際上擋不住任何東西** —— 把訊息當成規則存在的證據會判斷錯。

#### 4.2.5 `OFDM020` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 分行代碼不是 7 碼 | 「金融機構分行代碼 必須為7碼」並直接 `return` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:55-59` |
| 新增前 | 分行代碼前三碼不是既有總行 | 「金融機構分行代碼前三碼須為金融機構總行代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:152` |
| 新增前 | 查總行時 DB 出錯 | 跳 `ServerSideError` 並取消 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:71-76` |
| 新增 / 修改前 | SWIFT 不是 8 或 11 碼 | 「SWIFT代碼 必須為8或11碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:104-105` |
| 新增 / 修改前 | SWIFT 前八碼與總行不同 | 「SWIFT 代碼前八碼要與總行相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:195` |
| 新增 / 修改前 | 分行英文名稱 / 簡稱含非英數字 | 「…只限輸入英文及數字!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:45-53` |
| 輸入分行代碼後 | 總行有效碼 | 依結果把有效碼鎖成 `'N'` 或開放 `'Y'`;**DB 出錯視同有效** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:480-497` |
| 輸入分行代碼後 | 總行是農會 / 漁會 | 核印方式區塊不帶值 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:301-302` |
| 輸入分行代碼後 | 找不到總行核印資料 | 「取得總行核印扣款資料失敗,請檢查」+ 核印區塊全部清空鎖死 | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:307`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:470-477` |
| 刪除前 | 分行已被 `OFD071A` 引用 | 「此金融機構(分行)代碼尚有相對應的通路[OFDM071],故不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:350` |
| 存檔後 | 分行簡稱異動 | 同步 `OFD071A` 的通路說明;**`CHANNEL_DESCRP` 為 NULL 時靜默不同步** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:116` |
| 規則存在但不生效 | 「總行無效不可新增分行」 | — | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:85-99` 整段被註解 |

### 4.3 `OFDM003` — 營業日行事曆(本片邏輯最多、唯一跨資料庫)

**用途(推測)**:維護每年每月每一天是不是營業日。`CALENDER_TYPE`(行事曆類別)讓公司同時維護多套行事曆(例:公司行事曆 vs 各市場行事曆),依據是新增時預設值取自常數 `COMP_CALENDER_TYPE.Company`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:216`)。

**它和其他 25 支最大的不同**:

| 差異 | 說明 | 錨點 |
|---|---|---|
| 多筆型 PO | 繼承 `BaseMultiRowEVADaoPO`,一次寫一整個月(最多 31 列) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:41` |
| 自己組主 / 明細 SQL | 掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個事件,查詢頁只抓每月 1 日當代表列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:381-443` |
| 三個自訂動作 | 產生特定放假日 / 複製行事曆 / 新增年度行事曆,**每個都自己開兩條交易分批 commit** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:73`、`:165`、`:273` |
| 跨資料庫 | 核准後呼叫 **MSSQL** SP | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:485-520` |
| 月曆 UI | 用 `UltraWinSchedule` 的月曆控件,點選日期就是設假日 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:68-94` |

#### 4.3.1 三個自訂動作

| 動作 | 做什麼 | 先做什麼檢核 | 錨點 |
|---|---|---|---|
| `SetHoliday` 產生特定放假日 | 指定一個日期 + 備註 → 撈出當月所有行事曆類別的資料,把該日 `BUSS_ID` 設成 `'N'`,備註**接在原備註後面** | 當月查無資料 → 「查無行事曆資料可設定」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:73-159` |
| `CopyCalender` 複製行事曆 | 把某年(或某年某月)的某個類別整批複製成另一個類別 | 目標類別在該年 / 月**已有資料就擋** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:165-267` |
| `AddAllYear` 新增年度行事曆 | 一次把整年建出來 | 年度必須介於 1900 ~ 9998;該年該類別已存在就擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:273-300` |

**三個動作共用同一套「分批寫 ToDo」機制**:先用 `DefaultView.ToTable(true, 欄位)` 做 DISTINCT 拿到批次鍵(`SetHoliday` 用 `CALENDER_TYPE`、`CopyCalender` 用 `CAL_MONTH`),只有一批就直接呼叫基底的 `Add` / `Update`;多批就自己開 `dbProduct` 與 `dbPTPF` 兩條交易,逐批 `Add(tran, tranptpf, modelVDB)`,並**核對寫入筆數與 DataRow 筆數**,不符就 `throw` 讓整批回滾(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:128-136`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:235-245`)。

> 這是本片唯一有做「影響筆數核對」的地方,寫法正確,可以拿來當範本 —— 對照 `ofd4.md §4.3.3` 那支把三段筆數檢核全部註解掉的畫面。

**兩個瑕疵**:

1. `SetHoliday` 把新備註接在舊備註後面,超過 200 字時 `Memo.Substring(0, 199)` —— 取 199 不是 200,少一個字(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:97-104`)。

2. `CopyCalender` / `AddAllYear` 的前置檢核 SQL 是**字串串接**出來的:`WHERE SUBSTR(CAL_DATE,1,4) = " + intYear + " AND CALENDER_TYPE = '" + strTYPE_TO + "'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:184-187`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:297-300`)。`intYear` 有先 `Convert.ToInt32` 過算安全,`strTYPE_TO` 直接從畫面參數拿,**沒有任何跳脫**。同時 `SUBSTR(CAL_DATE,1,4) = <數字>` 是字串對數字的隱含轉換,會讓索引失效,而且只要有一列 `CAL_DATE` 前四碼不是數字就 ORA-01722 整句爆掉。

#### 4.3.2 核准後同步 MSSQL —— 本片風險最高的一段

`AfterApprove` 與 `AfterApproveDelete` 都呼叫 `UpdateOFD003(model, "A" / "D")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:464-477`),那支方法逐列呼叫 MSSQL 端的 SP:

| 項目 | 內容 | 錨點 |
|---|---|---|
| 連線 | `SQLDb = new Database("FA", DbServerType.MSSql)`,別名 `"FA"` **寫死在建構子** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:53-54` |
| SP | `S_PAM_OFD003A_SWSYS011`,**不在版控**(`grep -rl` 全 repo 只命中呼叫端) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:490` |
| 參數 | `@WCALENDER_TYPE` / `@WCAL_DATE` / `@WTYPE`(`"1"` 確認 · `"2"` 回復) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:500-505` |
| 輸出 | `@WOSTATUS` / `@WMESSAGE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:507-508` |

**兩個嚴重問題:**

1. **成功值的判斷與同一段的註解矛盾。** 程式碼上方的參數說明寫著 `@WOSTATUS nvarchar(1) OUTPUT, --1.資料更新成功　2.失敗`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:498`),但判斷式寫的是 `if (Convert.ToString(cmdAU.Parameters["@WOSTATUS"].Value) != "Y")` 就 `throw`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:512-518`)。註解說回 `'1'` 是成功,程式卻要求回 `'Y'` 才算成功。**兩者必有一方是錯的**:若 SP 真的回 `'1'`,那每一次核准都會 throw,行事曆根本核准不了;若 SP 回 `'Y'`,那註解是舊版殘留。SP 在版控外,**repo 內無法判定**,標假設,列入附錄 E.7。

2. **這段寫入不在 Oracle 的交易裡。** `SQLDb.ExecuteNonQuery(cmdAU)` 沒有帶任何 `DbTransaction`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:509`),而它跑在 `AfterApprove` 裡 —— 如果之後 Oracle 端的四眼交易回滾,MSSQL 那邊的行事曆已經改掉了,而且改了幾列就停在那裡(迴圈是逐列 commit)。**兩邊會不一致,而且沒有補償機制。**

#### 4.3.3 `OFDM003` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 修改前 | 一律先問「備註說明一旦修改,將無法回復」 | 選「否」就取消 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:188-194` |
| 新增前 | 必填欄檢核 | 訊息 + 取消 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:200-205` |
| 複製行事曆 | 目標年 / 月該類別已有資料 | 「XXXX年YY月已設定行事曆類別」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:195` |
| 複製行事曆 | 來源查無資料 | 「複製來源行事曆尚未建立」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:205` |
| 新增年度 | 年度不在 1900 ~ 9998 | 「年度(西元)輸入邏輯異常」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:279-285` |
| 設定假日 | 當月查無行事曆 | 「查無行事曆資料可設定」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:87-88` |
| 分批寫入 | 寫入筆數 ≠ DataRow 筆數 | `throw` → 兩條交易一起回滾 → 「設定失敗」/「複製來源行事曆尚未建立」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:134-135`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:242-243` |
| 核准後 | MSSQL SP 回傳不是 `'Y'` | `throw` → 四眼交易回滾 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:512-518` |
| 備註長度 | 超過 200 字 | 靜默截成 199 字 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:97-100` |
| 修改頁載入 | 某一天在 DB 裡沒有對應列 | `FindByCAL_DATE` 回 null → 下一行 `Row.BUSS_ID` **NullReferenceException** | 阻擋(以例外形式) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:80-84`,見附錄 E.9 |
| 查詢 | 年 / 月 / 類別三個條件都是 `Equal`,空白就不加條件 | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:166-182` |

### 4.4 `OFDM002` — 部門基本資料(本片下游最廣的一張表)

**用途(推測)**:維護公司內部部門,用代碼長度表達三層結構(5 碼大部門 / 7 碼中部門 / 9 碼小部門)。`OFD002` 被 **76 個檔案**引用,是本片乃至整個 OFD 模組最被廣泛讀取的表之一。

#### 4.4.1 覆寫 `Add`:兩段父部門檢核

`OFDM002_PO` 是本片唯一覆寫 `Add` 的 PO(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1033-1103`)。只有代碼長度是 7 或 9 時才進去:

| 段 | SQL | 不通過時 |
|---|---|---|
| 父部門存在 | `SELECT count(*) FROM OFD002 WHERE DEPT_NO = '<自己去掉末兩碼>'` | 「大部門尚未建立」/「中部門尚未建立」 |
| 父部門有效 | 同上再 `AND DEPT_VALID_CODE <> 'N'` | 「大部門無效,不可建立下屬部門」/「中部門無效,不可建立下屬部門」 |

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1046-1063`(第一段)與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1067-1086`(第二段)。

**三個問題,一個比一個嚴重:**

1. **字串串接進 SQL。** 兩段都是 `" where DEPT_NO = '" + strDEPT_NO.Substring(...) + "'"`。值來自畫面,沒有跳脫。

2. **`DEPT_VALID_CODE <> 'N'` 的三值邏輯。** 如果父部門那一列的 `DEPT_VALID_CODE` 是 NULL,`NULL <> 'N'` 在 Oracle 是 UNKNOWN,`COUNT` 得 0,使用者會看到「大部門無效,不可建立下屬部門」—— **父部門明明沒被設成無效,卻建不了下屬部門**。這是本片最容易在正式環境咬人的那一條,見附錄 E.3。

3. **`catch` 之後沒有 `return`。** 兩段檢核包在同一個 `try` 裡,`catch` 只做 `AddResultRow(false, 0, "")` 加寫 log(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1090-1095`),然後**執行流程直接落到 `return base.Add<TModelVDB>(modelVDB, args);`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1102`)。也就是**這兩段檢核在 DB 出錯時等於不存在,資料照樣新增**。見附錄 E.4。

#### 4.4.2 `AfterUpdate`:一句無鍵 UPDATE + 一句旁寫

| 段 | SQL | 說明 | 錨點 |
|---|---|---|---|
| ① 下層部門連動 | `UPDATE OFD002 SET DEPT_VALID_CODE=:v WHERE DEPT_NO LIKE :DEPT_NO \|\| '%' AND DEPT_NO <> :DEPT_NO` | 把所有代碼以本部門為前綴的下層部門,有效碼**一律蓋成本部門的值**。無條件執行 —— 即使這次修改根本沒動有效碼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:990-1003` |
| ② 銷售機構同步 | `UPDATE OFD068A SET AGENT_NAME/AGENT_NAME_E/AGENT_SHNM WHERE AGENT_ID='0' AND AGENT_CODE=:DEPT_NO AND (…<>…)` | 只有 5 碼大部門才做 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1005-1030` |

① 是本片唯一真正意義上的「無鍵 UPDATE」——`LIKE 前綴 || '%'` 沒有任何筆數上限,改一個大部門會一次寫掉底下全部中 / 小部門。② 又是那條 `<>` 三值邏輯,`OFD068A` 三個名稱欄全 NULL 時靜默不同步。

#### 4.4.3 `IsCheck` 與 `IsCheck_M` —— 同一支方法的兩個版本,只有一個是 Oracle 語法

修改時如果要把部門設成有效,UI 會先往上查父層是不是有效(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:155-186`):9 碼要先查大部門(`IsCheck`)再查中部門(`IsCheck_M`);7 碼只查大部門。

兩支方法的內容**逐字相同,只差一個字元**:

| 方法 | SQL | 參數符號 | 錨點 |
|---|---|---|---|
| `IsCheck` | `SELECT DEPT_VALID_CODE FROM OFD002 WHERE DEPT_NO=:DEPT_NO` | **`:`** Oracle 正確 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1243` |
| `IsCheck_M` | `SELECT DEPT_VALID_CODE FROM OFD002 WHERE DEPT_NO=@DEPT_NO` | **`@`** T-SQL 殘留 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1287` |

兩支都用 `dbProduct.AddInParameter(cmd, "DEPT_NO", OracleDbType.Varchar2, …)` 綁參數(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1245`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1289`)。Oracle 的 bind variable 前綴是 `:`,`@DEPT_NO` 在 Oracle 裡不是 bind variable —— **`IsCheck_M` 這句會在 DB 端失敗**,落到 `catch`,回 `AddResultRow(false, 0, "false")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1303-1307`),UI 看到 `ReturnCode != true` 就跳「中部門為無效,下屬部門不能修改為有效」並取消(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:173-177`)。

**推論結果:9 碼小部門永遠無法被改成有效,不管中部門實際上有效與否。** 這是本片最會咬人的一條,列為附錄 E.2,嚴重度高。**標假設** —— 沒有在 DB 上實測 `@` 前綴是否真的被 Oracle 拒絕;但同一支檔案的雙胞胎方法用 `:`、而且 `AddInParameter` 的型別是 `OracleDbType`,足以支持這個推論。

#### 4.4.4 `strDelete` —— 刪除前的兩段檢核

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1180-1229`,回傳「不可刪除訊息」,空字串表示可刪:

| 段 | 內容 | 錨點 |
|---|---|---|
| 有下層部門 | `WHERE DEPT_NO LIKE '<代碼>%' AND DEPT_NO <> '<代碼>'`(**字串串接**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1186-1189` |
| 5 碼大部門已對應銷售機構 | `SELECT COUNT(*) FROM OFD068A WHERE AGENT_ID=0 AND AGENT_CODE='<代碼>'`(**字串串接 + `AGENT_ID=0` 用數字比字元欄**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1206-1213` |

`catch` 回 `ExceptionMessage.ServerSideError`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1228`),UI 判斷到這個值就跳訊息並取消 —— **這一支的失敗方向是對的**(DB 出錯就擋),和 §4.4.1 的 `Add` 相反。同一支 PO 裡兩種失敗策略並存。

#### 4.4.5 `OFDM002` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 部門英文名稱含非英數字 | 「部門英文名稱,只限輸入英文及數字!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:203-205` |
| 新增(PO) | 7 / 9 碼但父部門不存在 | 「大 / 中部門尚未建立」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1059` |
| 新增(PO) | 7 / 9 碼但父部門無效(**NULL 也算無效**) | 「大 / 中部門無效,不可建立下屬部門」 | 阻擋(含誤擋) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1071`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1081` |
| 新增(PO) | 上面兩段查詢 DB 出錯 | **不擋,照樣新增** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1090-1102` |
| 修改前 | 要設成有效且代碼 7 / 9 碼 → 查大部門 | 大部門無效 → 「大部門為無效,下屬部門不能修改為有效」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:180-184` |
| 修改前 | 9 碼再查中部門 | **`@` 參數導致查詢失敗 → 一律當成無效** | 阻擋(誤擋) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:173-177` |
| 刪除前 | 尚有下層部門 | 「尚有所屬的中部門或小部門資料,此筆資料不可刪除!!」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1199-1201` |
| 刪除前 | 5 碼且已建銷售機構 | 「尚有相對應的銷售機構[OFDM068]資料,不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1213` |
| 刪除(DB) | Trigger 再檢一次同一條 | `RAISE_APPLICATION_ERROR(-20001, …)` | 阻擋 | `DB/Trigger/OFD002_T01.SQL:31-42` |
| 存檔後 | 一律連動下層部門有效碼 | 無提示 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:990-1003` |
| 存檔後 | 5 碼時同步 `OFD068A`;**三欄全 NULL 時靜默不同步** | 無提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1017` |
| 存檔後(DB) | Trigger **再同步一次** `OFD068A` | 無提示 | 記錄不擋 | `DB/Trigger/OFD002_T01.SQL:10-29` |
| 查詢 | 部門代碼 `Like`;有效碼有值用 `Equal`、無值用 `Like ''` | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:102-108` |
| 被註解 | 「集保分公司代碼要看 PTPF 的 `FTAS-Off` 產品才顯示」 | 現在寫死 `Visible = false` | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:41-57` |

### 4.5 `OFDM017` 與 `OFDM017B` — 本片唯一的 `A` / `B` 成對畫面

這一對是全片最乾淨的「遷移前 vs 遷移後」對照樣本,兩支管的東西幾乎一樣,但一支活著、一支死了。

#### 4.5.1 兩支的逐項差異

| 項目 | `OFDM017` | `OFDM017B` | 錨點 |
|---|---|---|---|
| 主表 | `OFD017A` | `OFD017B` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:39` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017B_PO.cs:13` |
| 業務語意(推測) | 受益人**公會**類別 + 大陸人士身分別 | 受益人類別 | Caption 見 §2.5 |
| PO 基底 | `BaseEVADaoPO` | 🔴 `BasicEVAPO` | 同上 |
| 表映射型別 | `xTableMapping` | `TableMapping`(舊) | 同上 |
| `_Ctl` 基底 | `BaseController` | 無基底,自己 `new` PO | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM017_Ctl.cs:12` vs `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM017B_Ctl.cs:11` |
| 四眼欄位大小寫 | 全大寫 | 混合(`dataid` / `Status` / `CreateID`) | §2.4 |
| PO 檔案 | 891 行,活 45 行(94 % 是註解掉的舊 MSSQL 實作) | 25 行,零註解 | §3.3 |
| 查詢條件 | `BF_BOARD_CD` 一律 `Like` | `BF_BOARD_CD` 用 `Equal`,而且**空白就不加條件** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:79` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:58-59` |
| 新增時的預設值 | 無 | 呼叫 `xMaintainFormUtility.SetBasicDefaultValue` 補四眼欄位預設值 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:37` |
| 多一個下拉欄 | `BF_COUNTRY_CLB` 大陸人士身分別,值域來自 `COD006A` 的 `"E9"` | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:40` |
| 執行期 | 可用 | **按查詢即 NRE** | §3.2 |

**誰先誰後**:`OFDM017` 的 PO 有 846 行被註解掉的舊 MSSQL 實作(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:50` 起的整個 `#region 註解`),`OFDM017B` 則是一支 25 行的乾淨新檔。合理推論:**`OFDM017B` 是後來新增的畫面,但當時是照著「舊世代範本」寫的** —— 新檔案、舊基底。這比 `ofd4.md §4.1.5` 那組「靠檔案編碼推先後」更直接:`OFDM017B` 沒有任何 MSSQL 殘留可註解,代表它從來沒有過 MSSQL 版本。

#### 4.5.2 兩支的卡控總表

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `OFDM017` | 進畫面 | 代碼只能半形 | 自動擋 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:32-33` |
| `OFDM017` | 新增 / 修改前 | 必填欄 | 訊息 + `e.Cancel`,**但沒有 `return`,後面照抄值** | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:65-74` |
| `OFDM017` | 修改頁 | 代碼設為唯讀 | 不可改 PK | 阻擋(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:61` |
| `OFDM017` | 查詢 | 代碼 `Like` 前綴 | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:79` |
| `OFDM017B` | 新增 / 修改前 | 必填欄 | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:63-76` |
| `OFDM017B` | 修改頁 | 代碼設為唯讀 | 不可改 PK | 阻擋(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:51` |
| `OFDM017B` | 查詢 | 代碼 `Equal`,空白不加條件 | — | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:58-59` |
| `OFDM017B` | **任何動作** | — | **NullReferenceException** | 阻擋(以例外形式) | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:797` |

### 4.6 `OFDM023` 與 `OFDM024` — 投顧 / 投信,逐行鏡像的一對

兩支 PO 的活程式碼**各 120 行,結構完全相同**,只差代碼欄名與四個常數:

| 項目 | `OFDM023`(投顧) | `OFDM024`(投信) |
|---|---|---|
| 主表 | `OFD023A` | `OFD024A` |
| PK 欄 | `SICE_CD` | `SITE_CD` |
| `OFD068A` 的 `AGENT_ID` | `'3'` | `'4'` |
| `OFD071A` 的 `CHANNEL_CD` | `'3'` | `'4'` |
| `AfterUpdate` 位置 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:64-108` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:64-108` |
| `CheckData` 位置 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:116-150` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:116-150` |
| 代碼長度檢核 | 至少 5 碼 | 至少 5 碼 |
| 檢核訊息 | 「投顧公司代碼,輸入長度至少為五碼。」 | 「投信公司代碼,輸入長度至少為五碼。」 |

**行為也一樣:**

1. `AfterUpdate` 打兩句 UPDATE —— 同步 `OFD068A` 的三個名稱欄、同步 `OFD071A` 的通路說明。兩句的 WHERE 最後一行都是 `<>` 比對,同樣有三值邏輯問題(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:81`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:100`)。

2. `CheckData` 刪除前 `UNION ALL` 查 `OFD071A` + `OFD068A`,一律回 `ReturnCode = true` 加筆數;`catch` 回 `false` 讓 UI 擋下(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:143-148`)。

**目前沒有發現「只改一邊」的痕跡** —— 這一對是本片唯一兩邊都同步的成對畫面。做全庫掃描時可以當成對照組:如果哪天 `OFD023A` 多了一條規則而 `OFD024A` 沒有,幾乎可以斷定是漏改。

**兩支共通的卡控總表**(把 `SICE` / `SITE`、`'3'` / `'4'` 互換即為另一支):

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 代碼長度 < 5 | 「投顧公司代碼,輸入長度至少為五碼。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM023.cs:158` |
| 新增 / 修改前 | 公司英文名稱含非英數字 | 「公司英文名稱,只限輸入英文及數字。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM023.cs:162` |
| 刪除前 | 已被 `OFD071A` 或 `OFD068A` 引用 | 「此投顧公司代碼尚有相對應的通路[OFDM071]或已建立銷售機構資料[OFDM068],故不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:141` |
| 刪除前 | 上述查詢 DB 出錯 | 空訊息 + 取消 | 阻擋(訊息為空) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM023.cs:139-140` |
| 存檔後 | 名稱異動 → 同步 `OFD068A` / `OFD071A`;**欄位全 NULL 時靜默不同步** | 無提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:81` |
| 查詢 | 代碼 `Like` 前綴 | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM023.cs:85` |

### 4.7 `OFDM022` — 唯一寫過 SQL 的死畫面

`OFDM022`(中間銀行)是五支 `BasicEVAPO` 畫面裡唯一自己組 SQL 的,也因此留下最多證據,可以拿來還原「這支停在哪個年代」。

| 證據 | 內容 | 錨點 |
|---|---|---|
| 表名用中括號 | `SELECT [OFD022].dataid … FROM [OFD022] left join [OFD019] … left join [FSK003]`,全段 27 處 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:101-118` |
| 讀的是遷移**前**的表名 | join 的是 `OFD019` 不是 `OFD019A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:115` |
| T-SQL schema 限定函式 | ToDo 條件用 `Select ToDoDataID From dbo.f_GetToDoData('user','func','action')` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:166` |
| 查詢條件全部字串串接 | `" And [OFD022]." + Row.Name + " = '" + Row.Value + "'"`,`Like` 版再接 `%` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:130-149` |
| ToDo 條件也串接使用者 ID | `"AND (([OFD022].UpdateID <> '" + loginUser + "') OR …)"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:165` |
| `dbTA` 直接用 | `args.DbCmd = dbTA.GetSqlStringCommand(strSQL)` 三處 + `dbTA.CreateConnection()` 一處 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:45`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:184` |

**結論:就算把 `dbTA` 修好,這支還是跑不動** —— 中括號界定符與 `dbo.` 前綴在 Oracle 上都是語法錯誤。要救 `OFDM022` 等於整支 PO 重寫。

**還有一個獨立的回傳值錯誤。** `GetBankNm`(取總行資料帶到畫面)在三個分支裡都是「清掉 `modelVDB` 的結果、卻把結果寫進另一個物件 `vdb`」:

| 分支 | 程式碼 | 錨點 |
|---|---|---|
| 查到資料 | `modelVDB.Utility.Result.Clear(); vdb.Utility.Result.AddResultRow(true, 0, "");` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:230-231` |
| 沒查到 | `modelVDB.Utility.Result.Clear(); vdb.Utility.Result.AddResultRow(false, 0, "");` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:235-236` |
| 例外 | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:242-243` |

方法最後 `return vdb;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:251`),所以結果其實傳得回去 —— 但 `modelVDB`(呼叫端傳進來的那個物件)的 Result 被清成空的。**如果哪天有人改成 `return modelVDB`,所有分支都會變成「沒有結果列」**。列入附錄 E.15。

**`OFDM022` 卡控總表**(全部在 UI,PO 端的卡控因為 NRE 而不會被執行到):

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 中間銀行英文名稱 / 簡稱含非英文 | 「中間銀行英文名稱,只限輸入英文!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM022.cs:107-111` |
| 新增 / 修改前 | SWIFT 代碼 < 8 碼 | 「'SWIFT代碼'不可小於8碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM022.cs:116` |
| 查詢 | 總行 / 幣別兩個條件都 `Equal`,空白不加 | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM022.cs:70-72` |
| **任何動作** | — | **NullReferenceException** | 阻擋(以例外形式) | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:797` |

### 4.8 `OFDM026` / `OFDM028` / `OFDM029` — 另外三支死畫面

這三支加上 §4.5 的 `OFDM017B` 與 §4.7 的 `OFDM022`,就是那五支。這三支的共通點是:**PO 除了建構子什麼都沒有**,所以「修好 `dbTA` 就能救活」的機會最大。

| 畫面 | 主表 | 業務(推測) | PO 活程式碼 | 註解掉的舊 MSSQL 實作 | 錨點 |
|---|---|---|---|---|---|
| `OFDM026` | `OFD026` | 潛在客戶類別 | 33 行 | 有,`AddCustTypeData` / `UpdateCustTypeData` / `DeleteCustTypeData` / `GetCustTypeData` / `GetToDoCustTypeData` / `Verify` / `Approve` / `UnDelete` / `Reject` / `Resend` 共 10 支 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM026_PO.cs:43-620` |
| `OFDM028` | `OFD028` | 通路區域代碼 | 33 行 | 同上 10 支,方法名換成 `*ChannelAreaCodeData` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM028_PO.cs:44-620` |
| `OFDM029` | `OFD029` | 帳戶國別代碼 | 31 行 | **無**(檔案只有 41 行) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM029_PO.cs:19-35` |

**`OFDM029` 沒有註解掉的舊實作**,這代表它跟 `OFDM017B` 一樣是後來才寫的新畫面,但**同樣照著舊世代範本寫** —— 兩支新畫面、兩支死畫面。這是本片對「為什麼會有人在 2010 年代之後還寫 `BasicEVAPO`」這個問題唯一能給的線索:範本被複製,沒人發現範本本身已經失效。

**三支共通的卡控**(內容幾乎相同,只差欄名):

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點(以 `OFDM026` 為例) |
|---|---|---|---|---|
| 新增 / 修改前 | 必填欄 | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM026.cs:53`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM026.cs:68` |
| 查詢 | 代碼 `Like` 前綴(`OFDM029` 用 `Equal`) | 查不到不提示 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM026.cs:60`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM029.cs:65` |
| **任何動作** | — | **NullReferenceException** | 阻擋(以例外形式) | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:797` |

### 4.9 其餘十三支:純框架或近乎純框架

以下十三支的 PO 活程式碼都在 50 行以內,只掛表名 + 一個空的 `AfterUpdate`,業務檢核全部在 UI 且只有「必填 + 格式」兩類。表格帶過:

| 畫面 | 主表 | 業務(推測) | UI 端額外檢核 | 錨點 |
|---|---|---|---|---|
| `OFDM001` | `OFD001` | 集保分公司 | 無(只有必填) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM001.cs:41-51` |
| `OFDM004` | `OFD004` | 基金種類(集保) | 英文名稱只限英文 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM004.cs:93-95` |
| `OFDM005` | `OFD005` | 基金型態(集保) | 英文名稱只限英文 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM005.cs:88-90` |
| `OFDM006` | `OFD006A` | 基金種類(內部) | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM006.cs:45-56` |
| `OFDM007` | `OFD007A` | 基金型態(內部) | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM007.cs:45-58` |
| `OFDM009` | `OFD009` | 註冊地 | 英文名稱只限英文 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM009.cs:96-98` |
| `OFDM010` | `OFD010` | 投資區域 | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM010.cs:58-76` |
| `OFDM011` | `OFD011` | 投資地區 | 代碼長度須為 3 碼;英文名稱只限英文 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM011.cs:93-97` |
| `OFDM012` | `OFD012A` | 申購手續費收取方式 | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM012.cs:60-78` |
| `OFDM013` | `OFD013A` | 收益分配方式 | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM013.cs:59-76` |
| `OFDM014` | `OFD014` | 贖回費收取方式 | 代碼長度須為 1 碼 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM014.cs:93-94` |
| `OFDM025` | `OFD025A` | 開戶來源 | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM025.cs:61-82` |
| `OFDM027` | `OFD027A` | 行銷身份群族 | 無 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM027.cs:62-80` |

**這十三支共通的卡控形狀**(逐支確認一致,不重覆列錨點):

| 時點 | 檢核 | 成立時 | 結果類型 |
|---|---|---|---|
| 新增 / 修改前 | `validatorManager1` 標記的必填欄 | 錯誤清單視窗 + `e.Cancel` | 阻擋 |
| 新增 / 修改前 | 上表的長度 / 英文格式檢核 | 加進錯誤清單 | 阻擋 |
| 修改頁 | 代碼欄設為唯讀 | 不可改 PK | 阻擋(無提示) |
| 查詢 | 代碼 `Like` 前綴 | 查不到不提示 | 過濾(無提示) |
| PO 端 | **無業務檢核** | — | — |

## 5. 查詢畫面(I)

**本片無 I 型畫面**(§3.6)。原因:26 支全部是參數主檔,查詢需求由各 M 畫面自己的查詢頁滿足,不需要獨立的查詢入口。

不過每一支 M 畫面的**查詢頁都有會靜默濾掉資料的條件**,這裡集中列出,因為它們最常被誤認為「資料不見了」:

| 畫面 | 查詢條件 | 會濾掉什麼(無提示) | 錨點 |
|---|---|---|---|
| `OFDM002` | 有效碼有值用 `Equal`;**無值時走 `Like ''`** | `Like ''` 在 Oracle 是「等於空字串」,而空字串等同 NULL —— 這一支不選有效碼時,理論上一筆都查不到。**標假設**:要看 `EVAStringHelper.AddParam` 對空值的處理才能確定 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:103-108` |
| `OFDM003` | 年 / 月 / 類別三個都 `Equal`,空白就不加條件 | 不填任何條件時撈全部,資料量大 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:166-182` |
| `OFDM015` | 公司代碼一律 `Like` 前綴 | 想用「包含」查中間字串查不到 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:156` |
| `OFDM017` | 代碼 `Like` 前綴 | 同上 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:79` |
| `OFDM017B` | 代碼 `Equal`,空白不加條件 | 打錯一個字就完全查無,不會像 `Like` 那樣退而求其次 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017B.cs:58-59` |
| `OFDM019` | 總行代碼 `Like` 前綴、銀行類型 `Equal` | 銀行類型下拉一旦選了值,沒填該類型的舊資料全部消失 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:143-147` |
| `OFDM020` | 分行代碼 `Like` 前綴 | 想用分行名稱查 —— 沒有這個條件 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:291` |
| `OFDM022` | 總行 + 幣別都 `Equal`,空白不加 | 兩個都不填就撈全部 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM022.cs:70-72` |
| `OFDM023` / `OFDM024` | 代碼 `Like` 前綴 | 同 `OFDM015` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM023.cs:85`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM024.cs:84` |
| `OFDM029` | 代碼 `Equal`,空白不加條件 | 同 `OFDM017B` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM029.cs:65` |
| 其餘 | 代碼 `Like` 前綴 | 同上 | §4.9 |

**一個一致性問題**:`Like` 與 `Equal` 的選擇沒有規律。同樣是「一個代碼欄 + 一個說明欄」的畫面,`OFDM025` / `OFDM026` / `OFDM027` / `OFDM028` 用 `Like`,`OFDM029` 用 `Equal`;同樣是受益人分類,`OFDM017` 用 `Like`、`OFDM017B` 用 `Equal`。使用者在不同畫面之間切換時,輸入同樣的片段會得到不同結果。

## 6. 批次(B)與 WindowsService

**本片無 B 型畫面,也沒有任何 WindowsService**(§3.7)。

最接近批次的東西是 `OFDM003` 的三個自訂動作(設定假日 / 複製行事曆 / 新增年度),它們一次處理整月或整年的資料、自己開交易分批 commit,行為像批次但**掛在 M 畫面的按鈕上,由使用者觸發,沒有排程**(§4.3.1)。

跨系統的寫入只有一處:`OFDM003` 在四眼核准後呼叫 MSSQL SP `S_PAM_OFD003A_SWSYS011`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:485-520`)。那段沒有重試、沒有補償、不在 Oracle 交易內,失敗時只能靠 `throw` 讓 Oracle 端回滾 —— 但**已經寫進 MSSQL 的那幾列不會被回滾**(§4.3.2)。

## 7. 報表(R)

**本片無 R 型畫面,也沒有任何 `.rpt`**(§3.8)。參數主檔本身不產報表。

拿本片的表去出報表的在別的模組,例如 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:356` 用 `OFD019A` 補總行名稱、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR106_PO.cs` 用 `OFD020A`。這些消費端列在 §8。

## 8. 跨模組共用

```text
[圖] OFD1-3 六組跨模組：OFD002 給七十六個讀者、總行分行遷移只做一半、五支旁寫、名稱同步兩份實作、行事曆跨 MSSQL、兩張廢棄表
圖中文字:A：OFD002 部門 —— 76 個檔案讀，本片下游最廣的一張 / OFDM002〔OFD1〕 / 唯一維護入口 有四眼 / OFD002 / PK DEPT_NO 5/7/9 碼三級 / CPM RSP DSM OFDB CRM COD / 10 個以上專案 / BasicOFD_PO 四種 Replace / 視圖 / SAL050 / 表函式 / B：OFD019A 與 OFD020A —— 46 / 33 個檔案讀，且遷移只做一半 / OFDM019 OFDM020 / 總行 / 分行 / OFD019A OFD020A / 維護入口只寫 A 名 / BMS EC OTA RSP OFDB / SUBSTR(x,1,3) 還原總行 / 六支方法讀舊名 / OFD019 / OFD020 / C：五支畫面旁寫三張別人的表，六處同一個三值邏輯缺陷 / OFDM002 OFDM019 OFDM020 / AfterUpdate / OFDM023 OFDM024 / AfterUpdate / OFD068A OFD071A OFD020A / 不經對方四眼 / AND (A<>:A OR B<>:B) / 目標欄全 NULL 就不更新 / D：OFD002 的名稱同步有兩份實作，條件不一樣 / OFDM002_PO AfterUpdate / 三欄 OR 一句 / Trigger OFD002_T01 / 逐欄 IF 三句 / 走畫面時兩份都跑 / 結果相同 看不出問題 / 從 DB 改只有 Trigger 跑 / 兩邊條件不同會不一致 / E：行事曆跨到 MSSQL —— 本片唯一的跨資料庫寫入 / OFDM003 核准 / AfterApprove / Database("FA", MSSql) / 別名寫死在建構子 / S_PAM_OFD003A_SWSYS011 / 版控外 逐列 commit / 不在 Oracle 交易內 / 回滾了也收不回來 / F：兩張表既沒人讀，維護畫面也是死的 / OFD022 中間銀行 / 外部消費端 0 / OFD026 潛在客戶類別 / 外部消費端 0 / 兩支畫面都必 NRE / OFDM022 / OFDM026 / 推測已廢棄 / 標假設
```

*圖:圖 5 跨模組。橘框=本片的維護入口;白框=表或正常機制;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼或版控外的物件。B 與 C 兩組最需要處理:B 是有六支共用方法讀著遷移前的表名，C 是六處複製貼上的三值邏輯——改設定後下游靜默不同步，而且沒有任何提示。*

參數檔群的下游是所有片裡最廣的。本節先講**本片往外寫**的部分(風險最高),再講**本片的表被誰讀**。

### 8.1 本片往外寫:五支畫面、三張別人的表、零個四眼

這是本片最需要被知道的一件事。以下五支畫面在存檔成功之後,會直接 UPDATE 不屬於本片的表,**那些異動不進對方的 ToDo、不需要對方的覆核、對方的畫面也不知道資料被改過**:

| 來源畫面 | 目標表 | 條件 | 改什麼 | 錨點 |
|---|---|---|---|---|
| `OFDM002`(部門) | `OFD002` 自己 | `DEPT_NO LIKE 前綴` 且不等於自己 | 所有下層部門的 `DEPT_VALID_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:990-1003` |
| `OFDM002` | `OFD068A` | `AGENT_ID='0'` + `AGENT_CODE=部門代碼`(限 5 碼) | `AGENT_NAME` / `AGENT_NAME_E` / `AGENT_SHNM` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1008-1029` |
| `OFDM019`(總行) | `OFD020A` | `f_TA_GetBankHQ(BANK_BRH)=總行代碼` | 所有分行的 `BANK_VALID_CODE`(條件式)與 `SEAL_CHK_CODE2/3`(農漁會除外) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:67-79`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:126-140` |
| `OFDM019` | `OFD068A` | `AGENT_ID='1'` + `SUBSTR(AGENT_CODE,2,3)=總行代碼` | 四個名稱欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:83-103` |
| `OFDM019` | `OFD071A` | `CHANNEL_CD='1'` + `SUBSTR(CHANNEL_CODE,2,3)=總行代碼` + `LENGTH=5` | `CHANNEL_DESCRP` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:106-121` |
| `OFDM020`(分行) | `OFD071A` | `CHANNEL_CD='1'` + 拼接 `SUBSTR(CHANNEL_CODE,2,3)\|\|SUBSTR(CHANNEL_CODE,6,4)=分行代碼` | `CHANNEL_DESCRP` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:109-123` |
| `OFDM023`(投顧) | `OFD068A` / `OFD071A` | `AGENT_ID='3'` / `CHANNEL_CD='3'` | 名稱欄 / 通路說明 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:72-107` |
| `OFDM024`(投信) | `OFD068A` / `OFD071A` | `AGENT_ID='4'` / `CHANNEL_CD='4'` | 名稱欄 / 通路說明 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:72-107` |

**共通結構,共通缺陷。** 上面所有往 `OFD068A` / `OFD071A` 的 UPDATE,WHERE 的最後一行都是「新舊值不同才更新」,寫法是 `AND (A<>:A OR B<>:B OR C<>:C)`。Oracle 的三值邏輯下,**目標列那幾欄全為 NULL 時整個條件是 UNKNOWN,那一列不會被更新**。所以:

> 一家銷售機構如果建檔時名稱欄留空(NULL),之後上游改名**永遠不會同步過去**,而且四支來源畫面都一樣。

這條規則被複製了六次(`OFDM002` 一次、`OFDM019` 兩次、`OFDM020` 一次、`OFDM023` 兩次、`OFDM024` 兩次),改的時候要六個地方一起改。列入附錄 E.3。

### 8.2 `OFD002` — 全庫最被廣泛讀取的一張(76 個檔案)

`OFD002`(部門)是本片、也是整個 OFD 模組最外流的表之一。

| 讀它的專案 | 檔案數 | 典型用法 | 錨點 |
|---|---|---|---|
| `Dev/ATLAS.OFD` | 20 | 各種畫面 join 出部門中文名 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6308` |
| `Dev/Common` | 13 | 共用下拉選單與部門權限展開 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:947-972` |
| `Dev/ATLAS.CPM` | 7 | 佣金相關 | — |
| `Dev/ATLAS.RSP` · `Dev/ATLAS.DSM` | 各 6 | 定期定額 / 配息 | — |
| `Dev/ATLAS.OFDB` · `Dev/ATLAS.CRM` | 各 5 | 批次與客戶關係 | — |
| `Dev/ATLAS.COD` | 2 | 業務員與部門對應 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:293`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:369` |
| `Dev/ATLAS.EC.Query` · `Dev/ATLAS.OFDI` · `Dev/ATLAS.NFD.Report` · `Dev/ATLAS.CPM.Report` | 各 2~3 | 報表與查詢補名稱 | — |

**一個容易踩到的地方**:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:947-976` 這段會依參數把 `FROM OFD002` 用 `string.Replace` **換成四種不同的來源** —— 換成視圖 `OFD002_V03`、換成 join `SAL050`、換成 join 表函式 `F_TA_GET_DIRECT_DEPTS(...)`。也就是同一支方法拿到的「部門清單」語意不固定。改 `OFD002` 的欄位時,這段的四個分支都要跟著看。〔客戶特定〕:視圖 `OFD002_V01` / `OFD002_V03` 與表函式 `F_TA_GET_DIRECT_DEPTS` 不在版控,已列 `refcheck-ignore`。

**另外 `OFD002` 是本片唯一有 Trigger 的表**:`DB/Trigger/OFD002_T01.SQL`。它做的事和 `OFDM002_PO_AfterUpdate` **重疊**(§8.6)。

### 8.3 `OFD019A` / `OFD020A` — 金融機構總行與分行(46 / 33 個檔案)

| 讀它的專案 | `OFD019A` | `OFD020A` | 典型用法 |
|---|---|---|---|
| `Dev/ATLAS.OFD` | 10 | 6 | 匯款設定、扣款行、代理行畫面 |
| `Dev/ATLAS.OTA.Query` · `Dev/ATLAS.OTAB` · `Dev/ATLAS.OTA` | 14 | 2 | 境外基金作業 |
| `Dev/Common` | 5 | 3 | 共用下拉選單 |
| `Dev/ATLAS.RSP` | 4 | 4 | 定期定額扣款 |
| `Dev/ATLAS.OFDB` | 2 | 5 | 批次 |
| `Dev/ATLAS.BMS` | 1 | 2 | 開戶時帶出銀行資料:`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:906-908` |
| `Dev/ATLAS.EC` 系列 | 3 | 3 | 電子交易與報表:`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:356` |
| `DB/`(Oracle SP / View) | 7 | 4 | `DB/SP/S_OTA_OFDR551_GET.SQL`、`DB/SP/S_OTA_OFDR081_GET.sql`、`DB/View/OFD068A_V02.SQL` |

**三個要注意的點:**

1. **消費端幾乎都靠字串切割把分行代碼還原成總行代碼** —— `SUBSTR(BANK_BRH,1,3)`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:356`)或 Oracle 函式 `f_TA_GetBankHQ(BANK_BRH)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:72`)。兩種寫法並存,意味著「分行代碼前三碼 = 總行代碼」這條規則被寫死在很多地方。`OFDM020` 新增時也是靠這條規則檢核(§4.2.5)。

2. **`OFD019` / `OFD020`(無 `A`)在 Oracle 層仍有活的讀者**(§2.3),包含 `DB/SP/S_OTA_OFDR052_GET.sql` 與 `DB/SP/S_OTA_OFDR081_GET.sql`。改 `OFD019A` 的欄位時,必須確認這些讀舊名的地方會不會受影響。

3. **`DB/View/OFD068A_V02.SQL` 同時讀 `OFD002` / `OFD019A` / `OFD020A`** —— 這個視圖把本片三張主檔兜在一起餵給銷售機構相關的查詢,是本片三張表之間唯一的「已知交集點」。

### 8.4 `OFD015` / `OFD016` — 信評公司與等級(各 14 個檔案)

集中在 `Dev/ATLAS.OFD`(10)與 `Dev/Common`(4)。共用讀取點是 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:3505`(讀 `OFD015`)與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:3562`(讀 `OFD016`),兩支方法把信評公司與等級做成下拉選單。

**風險不在讀取端,在維護端**:`OFDM015` 的所有檢核都在 UI(§4.1),而 `OFD016` 的三欄複合 PK 只靠 grid 事件擋重覆。任何從 DB 端或別的程式塞進 `OFD016` 的資料都不會經過那些檢核。

### 8.5 其餘表的影響面速查

| 表 | 引用檔案數 | 主要讀者 | 一句話 |
|---|---|---|---|
| `OFD028` | 9 | `Dev/Common`(6)、`Dev/ATLAS.OFD`(3) | 通路區域代碼,維護畫面是死的(§4.8),資料只能從 DB 改 |
| `OFD027A` | 9 | `Dev/ATLAS.OFD`(4)、`Dev/Common`(3)、`Dev/ATLAS.EC`(1) | 行銷身份群族 |
| `OFD003A` | 8 | `Dev/ATLAS.OFD.Query`(3)、`Dev/ATLAS.OFD`(3)、OTA / OTAB | 行事曆;另有讀舊名 `OFD003` 的 Oracle SP 兩支 |
| `OFD001` | 8 | `Dev/Common`(4)、`Dev/ATLAS.OFDI`(2) | 集保分公司 |
| `OFD011` | 7 | 分散 | 投資地區 |
| `OFD017A` · `OFD014` · `OFD010` · `OFD004` | 各 6 | 分散 | 代碼下拉來源 |
| `OFD029` · `OFD012A` · `OFD007A` · `OFD006A` · `OFD005` | 各 5 | 分散 | 同上 |
| `OFD013A` · `OFD009` | 各 4 | 分散 | 同上 |
| `OFD023A` · `OFD024A` | 各 3 | `Dev/ATLAS.OFD` + `Dev/Common` | 投顧 / 投信 |
| `OFD025A` · `OFD017B` | 各 2 | `Dev/Common` + 自己 | 開戶來源 / 受益人類別 |
| `OFD026` · `OFD022` | 各 1 | 只有自己的畫面 | **零外部消費端**,而且維護畫面是死的 —— 這兩張表目前既沒人讀也改不了 |

> `OFD022`(中間銀行)與 `OFD026`(潛在客戶類別)是本片唯二「沒有任何外部讀者」的表。搭配 §4.7、§4.8 的結論(兩支畫面都必 NRE),合理推測**這兩張表在本站台是廢棄的**。標假設 —— 也可能是消費端在版控外的報表或介接程式裡。

### 8.6 一條規則兩份實作:`OFD002` 的名稱同步

`OFD002` 改名時,`OFD068A` 會被同步兩次:

| 實作 | 位置 | 條件 | 更新哪些欄 |
|---|---|---|---|
| C# `AfterUpdate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1008-1029` | `AGENT_ID='0'`、`AGENT_CODE=:DEPT_NO`、且三欄任一不同 | `AGENT_NAME` `AGENT_NAME_E` `AGENT_SHNM` |
| Oracle Trigger | `DB/Trigger/OFD002_T01.SQL:8-30` | `LENGTH(DEPT_NO)=5`,逐欄 `IF :NEW.x <> :OLD.x` | 同三欄,但**分成三個獨立的 UPDATE** |

**兩份實作的差異:**

| 面向 | C# 版 | Trigger 版 |
|---|---|---|
| 觸發時機 | 只有走 `OFDM002` 畫面才會跑 | 任何 UPDATE `OFD002` 都會跑,包含 DBA 手改 |
| 5 碼限制 | 在 C# 判斷 `row.DEPT_NO.Length == 5` | 在 `WHEN` 子句 `LENGTH(NEW.DEPT_NO)=5 OR LENGTH(OLD.DEPT_NO)=5` |
| 三值邏輯 | `AND (A<>:A OR B<>:B OR C<>:C)` 一句,全 NULL 時整列不更新 | `IF (:NEW.x <> :OLD.x)` 三次,**任一邊為 NULL 時該欄不更新** |
| 刪除保護 | 在 `strDelete` 用 `COUNT` 擋 | 在 `DELETING` 分支 `RAISE_APPLICATION_ERROR(-20001, …)` |
| 英文簡稱 `AGENT_SHNM_E` | 不更新 | 不更新 |

走畫面改名時**兩份都會跑**,結果相同所以看不出問題;但只要有人從 DB 端改,只有 Trigger 會跑。維護時兩邊都要改,否則會出現「畫面改得動、DB 改不動」或反過來的不一致。列入附錄 E.6。

### 8.7 改動影響面速查

要改本片的東西之前,先看這張表:

| 想做的事 | 一定要一起看的地方 |
|---|---|
| 給 `OFD002` 加欄位 | `OFDM002` 六層 + `DB/Trigger/OFD002_T01.SQL` + `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:947-976` 的四個 Replace 分支 + 視圖 `OFD068A_V02` |
| 給 `OFD019A` 加欄位 | `OFDM019` 六層 + `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` 裡讀 `OFD019A` 的六支方法 **與讀舊名 `OFD019` 的四支** + 7 支 Oracle SP / View |
| 改「上游改名同步下游」的邏輯 | 六個地方:`OFDM002` / `OFDM019`(×2)/ `OFDM020` / `OFDM023` / `OFDM024`,加 Trigger |
| 修活 `BasicEVAPO` 那五支 | PO 基底 + `_Ctl` 基底 + `TableMapping` → `xTableMapping` + **xsd 的四眼欄位大小寫**(§2.4);`OFDM022` 另外要整段重寫 SQL |
| 改行事曆 | `OFDM003` 六層 + MSSQL 端 SP `S_PAM_OFD003A_SWSYS011`(版控外)+ 讀舊名 `OFD003` 的兩支 Oracle SP |
| 改代碼值域(下拉選項) | 值域不在本片,在 `CTL014` 與各 `DataSrc` 類別 |

## 附錄 A. 資料表總表

### A.1 本片宣告的 27 張實體表

| 表 | 主人畫面 | 業務(推測) | 欄數 | 引用檔案數 | 帶 `A`? |
|---|---|---|---|---|---|
| `OFD001` | `OFDM001` | 集保分公司 | 20 | 8 | — |
| `OFD002` | `OFDM002` | 部門(三級) | 28 | **76** | — |
| `OFD003A` | `OFDM003` | 營業日行事曆 | 21 | 8 | ✔ 遷移改名 |
| `OFD004` | `OFDM004` | 基金種類(集保) | 21 | 6 | — |
| `OFD005` | `OFDM005` | 基金型態(集保) | 21 | 5 | — |
| `OFD006A` | `OFDM006` | 基金種類(內部) | 18 | 5 | ✔ 遷移改名 |
| `OFD007A` | `OFDM007` | 基金型態(內部) | 18 | 5 | ✔ 遷移改名 |
| `OFD009` | `OFDM009` | 註冊地 | 21 | 4 | — |
| `OFD010` | `OFDM010` | 投資區域 | 20 | 6 | — |
| `OFD011` | `OFDM011` | 投資地區 | 21 | 7 | — |
| `OFD012A` | `OFDM012` | 申購手續費收取方式 | 17 | 5 | ✔ 遷移改名 |
| `OFD013A` | `OFDM013` | 收益分配方式 | 17 | 4 | ✔ 遷移改名 |
| `OFD014` | `OFDM014` | 贖回費收取方式 | 20 | 6 | — |
| `OFD015` | `OFDM015` | 信評公司 | 21 | 14 | — |
| `OFD016` | `OFDM015`(明細) | 評等等級 | 23 | 14 | — |
| `OFD017A` | `OFDM017` | 受益人公會類別 | 19 | 6 | ✔ 遷移改名 |
| `OFD017B` | `OFDM017B` | 受益人類別 | 17 | 2 | ✖ `B` 不是 `A` |
| `OFD019A` | `OFDM019` | 金融機構總行 | 40 | **46** | ✔ 遷移改名(不完整) |
| `OFD020A` | `OFDM020` | 金融機構分行 | 41 | **33** | ✔ 遷移改名(不完整) |
| `OFD022` | `OFDM022` | 中間銀行 | 26 | 1 | — |
| `OFD023A` | `OFDM023` | 投顧公司 | 27 | 3 | ✔ 遷移改名 |
| `OFD024A` | `OFDM024` | 投信公司 | 27 | 3 | ✔ 遷移改名 |
| `OFD025A` | `OFDM025` | 開戶來源 | 17 | 2 | ✔ 遷移改名 |
| `OFD026` | `OFDM026` | 潛在客戶類別 | 17 | 1 | — |
| `OFD027A` | `OFDM027` | 行銷身份群族 | 17 | 9 | ✔ 遷移改名 |
| `OFD028` | `OFDM028` | 通路區域 | 17 | 9 | — |
| `OFD029` | `OFDM029` | 帳戶國別 | 17 | 5 | — |

> 「引用檔案數」= `grep -rl '\bTABLE\b' Dev DB` 的檔案數,含自己的六層,所以每張表至少 1。

### A.2 只讀不寫的外部表(join 進來取說明或算筆數)

| 表 | 誰讀 | 用途 | 錨點 |
|---|---|---|---|
| `OFD019A` | `OFDM020` `OFDM022` | 取總行資料做檢核與帶名稱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:144` |
| `FSK003` | `OFDM022` | `left join` 取幣別名稱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:117` |
| `OFD074` | `OFDM019` | 刪除前與改核印方式時 `COUNT` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:178`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:237` |
| `OFD076` | `OFDM019` | 刪除前 `COUNT` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:181` |
| `COD006A` | `OFDM017` | 大陸人士身分別下拉(`"E9"` 群組) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:40` |
| `CTL014` | 全片 | 共用下拉代碼的值域來源 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` |

### A.3 本片會寫、但主人在別處的表

| 表 | 誰寫 | 寫什麼 | 經過四眼? |
|---|---|---|---|
| `OFD068A` | `OFDM002` `OFDM019` `OFDM023` `OFDM024` | 名稱 / 簡稱欄 | **否** |
| `OFD071A` | `OFDM019` `OFDM020` `OFDM023` `OFDM024` | `CHANNEL_DESCRP` | **否** |
| `OFD020A` | `OFDM019` | `BANK_VALID_CODE` `SEAL_CHK_CODE2/3` | **否**(`OFD020A` 的主人是本片的 `OFDM020`) |

### A.4 檢核時讀到、只 `COUNT` 不改的表

`OFD074` · `OFD076` · `OFD071A` · `OFD068A` · `OFD020A` · `OFD002`(自己)。全部集中在 `CheckBankHqData`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:177-194`)、`CheckData`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:338-340`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:124-131`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:124-131`)與 `strDelete`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1186-1214`)五處。

## 附錄 B. SP / Function / Trigger / View

| 物件 | 型別 | 在版控? | 誰用 | 說明 |
|---|---|---|---|---|
| `OFD002_T01` | Oracle Trigger | ✅ `DB/Trigger/OFD002_T01.SQL` | 自動 | `OFD002` 改名時同步 `OFD068A`;刪除時擋下。檔案是 cp950 編碼 |
| `OFD068A_V02` | Oracle View | ✅ `DB/View/OFD068A_V02.SQL` | 銷售機構相關查詢 | 同時讀 `OFD002` / `OFD019A` / `OFD020A`,是本片三張主檔的交集點 |
| `S_PAM_OFD003A_SWSYS011` | **MSSQL** SP | ❌ **版控外** | `OFDM003` 核准 / 核准刪除 | 已列 `refcheck-ignore`;參數與回傳約定只能從呼叫端反推(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:495-508`) |
| `f_TA_GetBankHQ` | Oracle Function | ❌ 版控外 | `OFDM019` 連動分行、`OFDM019` 刪除檢核 | 從分行代碼算出總行代碼,行為等同 `SUBSTR(x,1,3)`;已列 `refcheck-ignore` |
| `F_TA_GET_DIRECT_DEPTS` | Oracle 表函式 | ❌ 版控外 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:972` | 展開部門階層 |
| `OFD002_V01` / `OFD002_V03` | Oracle View | ❌ 版控外 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:116`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:953` | 部門視圖 |
| `dbo.f_GetToDoData` | **T-SQL** Function | ❌ 不存在於 Oracle | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:166` | 舊世代殘留,是 `OFDM022` 跑不動的第二個原因 |
| `S_OTA_OFDR551_GET` `S_OTA_OFDR561_GET` `S_OTA_OFDR562_GET` `S_OTA_OFDR601A_GET` `S_OTA_OFDR602A_GET` `S_OTA_OFDR604A_GET` | Oracle SP | ✅ `DB/SP/` | OTA 報表 | 讀 `OFD019A` |
| `S_OTA_OFDB131_EXE` `S_OTA_OFDR050_EXE` `S_OTA_OFDR081_GET` | Oracle SP | ✅ `DB/SP/` | OTA 批次 / 報表 | 讀 `OFD020A`;`S_OTA_OFDR081_GET` 同時讀舊名 `OFD020` |

**本片沒有自己的 SP。** 26 支畫面全部走 PO 組 SQL,一支 SP 都沒呼叫(唯一的例外是 `OFDM003` 呼叫 MSSQL 端的 SP)。

## 附錄 C. 代碼對照

| 代碼 | 值 | 意義 | 來源 |
|---|---|---|---|
| `VALID_CODE` | `'Y'` / `'N'` | 有效 / 無效 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81-91` |
| `BANK_TYPE` | `'01'` `'02'` `'03'` `'04'` `'05'` | 本國銀行 / 外國銀行 / 信合社 / 農會 / 漁會 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3157-3179` |
| `SHORE_ID` | `'2'` / `'1'` | 境內基金 / 境外基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` —— **本片 27 張表沒有一張有這個欄位**,列在這裡是為了對照 §2.2 |
| `AGENT_ID`〔客戶特定〕 | `'0'` `'1'` `'3'` `'4'` | 部門 / 銀行 / 投顧 / 投信(依同步來源反推,**推測**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1015`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:79`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:79` |
| `CHANNEL_CD`〔客戶特定〕 | `'1'` `'3'` `'4'` | 銀行 / 投顧 / 投信(同上,**推測**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:111`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:98`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:98` |
| `BUSS_ID` | `'Y'` / `'N'` | 營業日 / 休市 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:82-89` |
| `FISC_CD` | `'Y'` / `'N'` | 金資編碼 / 非金資 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:351-358` |
| `@WTYPE`(MSSQL SP 參數) | `"1"` / `"2"` | 確認 / 回復 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:502-505` |
| `@WOSTATUS`(MSSQL SP 回傳) | 註解說 `'1'` 成功 / `'2'` 失敗;程式碼要求 `'Y'` | **矛盾,見附錄 E.7** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:498` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:512` |
| `DEPT_NO` 長度 | 5 / 7 / 9 | 大 / 中 / 小部門 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1039`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1059` |
| `COD006A` 群組 `"E9"` | — | 大陸人士身分別的值域 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:40` |

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module OFD`** —— 那會拿 550 支來比,覆蓋率必然難看且無意義。以下用本片自己的 26 支名單。

### D.1 26 支的處置

| # | 畫面 | 處置 | 本文位置 | PO 基底 | 在 csproj |
|---|---|---|---|---|---|
| 1 | `OFDM001` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 2 | `OFDM002` | **已寫(專節)** | §4.4 | `BaseEVADaoPO`(覆寫 `Add`) | ✅ 六層皆在 |
| 3 | `OFDM003` | **已寫(專節)** | §4.3 | `BaseMultiRowEVADaoPO` | ✅ 六層皆在 |
| 4 | `OFDM004` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 5 | `OFDM005` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 6 | `OFDM006` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 7 | `OFDM007` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 8 | `OFDM009` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 9 | `OFDM010` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 10 | `OFDM011` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 11 | `OFDM012` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 12 | `OFDM013` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 13 | `OFDM014` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 14 | `OFDM015` | **已寫(專節)** | §4.1 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 15 | `OFDM017` | **已寫(專節)** | §4.5 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 16 | `OFDM017B` | **已寫(專節)** | §4.5 | 🔴 `BasicEVAPO` | ✅ 六層皆在 |
| 17 | `OFDM019` | **已寫(專節)** | §4.2 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 18 | `OFDM020` | **已寫(專節)** | §4.2 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 19 | `OFDM022` | **已寫(專節)** | §4.7 | 🔴 `BasicEVAPO` | ✅ 六層皆在 |
| 20 | `OFDM023` | **已寫(專節)** | §4.6 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 21 | `OFDM024` | **已寫(專節)** | §4.6 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 22 | `OFDM025` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 23 | `OFDM026` | **已寫(專節)** | §4.8 | 🔴 `BasicEVAPO` | ✅ 六層皆在 |
| 24 | `OFDM027` | 表格帶過 | §4.9 | `BaseEVADaoPO` | ✅ 六層皆在 |
| 25 | `OFDM028` | **已寫(專節)** | §4.8 | 🔴 `BasicEVAPO` | ✅ 六層皆在 |
| 26 | `OFDM029` | **已寫(專節)** | §4.8 | 🔴 `BasicEVAPO` | ✅ 六層皆在 |

**統計:專節深寫 13 支 · 表格帶過 13 支 · 未提及 0 支。繼承 `BasicEVAPO` 5 支 · 不在 csproj 0 支。**

### D.2 csproj 核對方法

26 支 × 6 層 = 156 個檔案項目,逐一在對應的 csproj 內找 `Include="<檔名>"`:

| csproj | 找什麼 | 命中 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/UI.OFD.csproj` | `"OFDMxxx.cs"` | 26 / 26 |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/FormProxy.OFD.csproj` | `"OFDMxxx_Pxy.cs"` | 26 / 26 |
| `Dev/ATLAS.OFD/Source/Control/Control.OFD/Control.OFD.csproj` | `"OFDMxxx_Ctl.cs"` | 26 / 26 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj` | `"OFDMxxx_PO.cs"` | 26 / 26 |
| `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD1/DataEntity.OFD1.csproj` 等三個 | `OFDMxxxModel.xsd` | 26 / 26 |
| `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD1/UIEntity.OFD1.csproj` 等三個 | `OFDMxxxView.xsd` | 26 / 26 |

**缺漏 0。** 本片沒有「檔案存在但不在 csproj」的死畫面 —— 但這**不代表沒有死畫面**,五支 `BasicEVAPO` 的畫面正是「編得起來、跑不動」的反例(§3.2)。**csproj 檢查抓不到執行期的死畫面。**

### D.3 表的覆蓋率

27 張表全部在 §2.1 / §2.4 / §2.5 / 附錄 A.1 出現,覆蓋率 27 / 27。外部表 6 張、本片會寫的外部表 3 張,也都列出。

### D.4 本文沒做到的事

| 沒做 | 為什麼 | 影響 |
|---|---|---|
| 沒驗證 Oracle 端是否真有 `OFD019` / `OFD020` / `OFD003` 這些舊名物件 | `DB/Table/` 只有票號變更腳本,沒有完整 DDL | §2.3 與附錄 E.5 的結論標假設 |
| 沒驗證 `@DEPT_NO` 在 Oracle 上是否真的失敗 | 需要連 DB 實測 | 附錄 E.2 標假設,但同檔雙胞胎方法的對比足以支持 |
| 沒看到 MSSQL SP `S_PAM_OFD003A_SWSYS011` 的內容 | 版控外 | 附錄 E.7 的成功值判斷無法確定哪一邊是對的 |
| 沒讀 `*.Designer.cs` | 規則禁止 | 畫面上控件的可見性 / 啟用狀態只能從 `.cs` 的事件程式碼推 |
| 沒查證 `DataAccessPool` 內 PO 實例的存活範圍 | 超出本片範圍 | §4.2.1 的 `m_IsUpVld` 分析標假設 |
| 沒追 `CTL014` 每個 `SourceType` 的實際資料 | 值域在 DB | 代碼值域只列程式碰過的值 |

## 附錄 E. 讀本文時要注意的地方

以下依嚴重度排序。每條:缺陷 / 影響 / 錨點 / 嚴重度。

### E.1 五支畫面繼承 `BasicEVAPO` 不覆寫,連查詢都 NRE —— 嚴重度 **高**

**缺陷**:`OFDM017B` `OFDM022` `OFDM026` `OFDM028` `OFDM029` 的 PO 繼承 `BasicEVAPO`,該基底的 `dbTA` 宣告即 `= null`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`),建構子賦值那四行整段被註解(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-172`),五支子類**都沒有自行賦值**。

**影響**:`Select()` 第一行就 `dbTA.CreateConnection()`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:795-797`),`Add()` 第一行同理(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`)。**使用者一按查詢就 NullReferenceException**,不是存檔才炸。五支畫面等於不存在,它們維護的 `OFD017B` `OFD022` `OFD026` `OFD028` `OFD029` 只能靠 DB 直接改。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017B_PO.cs:8`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:20`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM026_PO.cs:18`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM028_PO.cs:19`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM029_PO.cs:19`

**注意**:判斷基底前要先剝 `//` 註解,`OFDM012` `OFDM013` `OFDM017` `OFDM019` `OFDM020` 都在註解區留著一行 `//public class … : Basic_PO`,直接 grep 會誤判(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM017_PO.cs:51`)。

### E.2 `OFDM002.IsCheck_M` 的 SQL 用 T-SQL 參數符號,中部門檢核必定失敗 —— 嚴重度 **高**

**缺陷**:同一支 PO 裡兩支幾乎逐字相同的方法,參數符號不同:

| 方法 | SQL 片段 | 錨點 |
|---|---|---|
| `IsCheck`(檢核大部門) | `WHERE DEPT_NO=:DEPT_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1243` |
| `IsCheck_M`(檢核中部門) | `WHERE DEPT_NO=@DEPT_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1287` |

兩支都用 `OracleDbType` 綁參數(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1289`)。

**影響**:`IsCheck_M` 的 SQL 在 Oracle 端失敗 → `catch` → `AddResultRow(false, 0, "false")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1303-1307`)→ UI 判為「中部門無效」並取消(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:173-177`)。**9 碼小部門永遠無法被改成有效,不論中部門實際狀態。** 而且 UI 給的訊息是「中部門為無效,下屬部門不能修改為有效」,會把人導向去查中部門,查了會發現中部門明明是有效的 —— 這種「訊息指向錯誤方向」的缺陷最難查。

**標假設**:沒有連 DB 實測 `@` 前綴在 Oracle 上的行為;但雙胞胎方法用 `:` 是強證據。

### E.3 Oracle 三值邏輯:`欄 <> '值'` 遇 NULL 是 UNKNOWN —— 嚴重度 **高**(範圍最廣)

**這是前十七篇裡命中九個模組的老問題,本片有七處。**

| # | 位置 | 條件 | NULL 時的後果 |
|---|---|---|---|
| 1 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1071` | `AND DEPT_VALID_CODE <> 'N'` | 父部門的有效碼是 NULL 時,`COUNT` 得 0 → **誤擋**「大 / 中部門無效,不可建立下屬部門」 |
| 2 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1017` | `AND (AGENT_NAME<>:A OR AGENT_NAME_E<>:B OR AGENT_SHNM<>:C)` | `OFD068A` 三欄全 NULL → **不同步**,改了部門名銷售機構還是舊的 |
| 3 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:93` | 同上加 `AGENT_SHNM_E` | 同上 |
| 4 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:113` | `AND CHANNEL_DESCRP<>:CHANNEL_DESCRP` | `OFD071A` 的通路說明是 NULL → 不同步 |
| 5 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:116` | 同上 | 同上 |
| 6 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:81`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:100` | 同 2 / 4 | 同上 |
| 7 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:81`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:100` | 同 2 / 4 | 同上 |

**第 1 條是「誤擋」(使用者做不了該做的事),第 2~7 條是「靜默不做」(使用者以為做了但沒做)。** 兩種都沒有任何提示。修法是把 `A <> :A` 換成 `NVL(A,'@@') <> NVL(:A,'@@')` 或 `A IS DISTINCT FROM` 的 Oracle 等價寫法,**七處要一起改**。

Trigger 端也同病:`DB/Trigger/OFD002_T01.SQL:10`、`DB/Trigger/OFD002_T01.SQL:17`、`DB/Trigger/OFD002_T01.SQL:24` 三個 `IF (:NEW.x <> :OLD.x)`。

### E.4 `catch` 之後沒有 `return`,DB 出錯等於通過 —— 嚴重度 **高**

**兩處,方向都是「放行」:**

| 位置 | 情形 | 後果 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1090-1102` | `Add` 覆寫裡的兩段父部門檢核包在同一個 `try`,`catch` 只寫 log 加設一筆 Result,**沒有 `return`**,流程直接落到 `return base.Add(...)` | **DB 出錯時兩段檢核等於不存在,小部門照樣被建出來** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:247-251` | `CheckBANK_VALID_CODE` 的 `catch` 回 `"-1"`,而 `"-1"` 在這支方法裡的意思是「總行有效」;呼叫端 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:486` 判斷 `strCheck != "-1"` 才鎖成無效 | **DB 出錯時畫面把新分行當成總行有效,開放使用者設有效碼** |

**對照組**:同一支 `OFDM002_PO` 的 `strDelete` 在 `catch` 回 `ExceptionMessage.ServerSideError`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1228`),UI 收到就擋 —— **同一支檔案裡兩種相反的失敗策略並存**。`OFDM019` / `OFDM023` / `OFDM024` 的 `CheckData` 也都是擋(回 `false`),方向正確。

### E.5 `OFD019A` / `OFD020A` 的遷移只做了一半,同一支檔案裡新舊表名並存 —— 嚴重度 **高**(標假設)

**缺陷**:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` 是 Oracle 版共用資料來源,裡面同時有讀 `OFD019A` 的六支方法與讀 `OFD019` 的四支方法(`OFD020` 同型,六對二)。維護入口 `OFDM019` / `OFDM020` 只寫 `A` 名。

**影響**:讀舊名的那六支方法(`GetBankHqData` / `GetBankData` / `GetSubBank` / `GetAgentBankDataSrc` / `GetBankBrhData`)拿到的資料,**不保證是使用者剛剛維護的內容**。它們是共用下拉選單與銀行資料來源,影響面涵蓋 EC / RSP / BMS 等多個模組。

**錨點**:讀新名 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6119`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4441`;讀舊名 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:355`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:254`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6505`。Oracle SP 端也有:`DB/SP/S_OTA_OFDR052_GET.sql`、`DB/SP/S_OTA_OFDR081_GET.sql`。

**標假設**:repo 內沒有 DDL,無法判定 Oracle 上 `OFD019` 是同義詞還是獨立的舊表。**這條要優先到 DB 上確認**,因為兩種可能的處置完全不同 —— 同義詞的話只是命名不一致,獨立舊表的話是正在流失資料。

### E.6 一條規則兩份實作:`OFD002` 的名稱同步 —— 嚴重度 **中**

**缺陷**:`OFD002` 改名同步到 `OFD068A` 這條規則,同時寫在 C#(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1008-1029`)與 Oracle Trigger(`DB/Trigger/OFD002_T01.SQL:8-30`)。刪除保護也是兩份(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1206-1213` 與 `DB/Trigger/OFD002_T01.SQL:31-42`)。

**影響**:走畫面時兩份都跑,看不出問題;從 DB 端改時只有 Trigger 跑。兩份的判斷條件不同(C# 是三欄 OR 一句,Trigger 是逐欄三句),**遇到部分欄位為 NULL 時行為不一致**。維護時只改一邊會造成長期不一致。

### E.7 `OFDM003` 對 MSSQL SP 回傳值的判斷與同段註解矛盾 —— 嚴重度 **高**(標假設)

**缺陷**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:498` 的註解寫 `@WOSTATUS nvarchar(1) OUTPUT, --1.資料更新成功　2.失敗`,但 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:512` 寫 `if (Convert.ToString(...["@WOSTATUS"].Value) != "Y")` 就 `throw`。

**影響**:兩者必有一方錯。若 SP 回 `'1'`,**每一次行事曆核准都會 throw,行事曆根本核准不了**;若 SP 回 `'Y'`,註解是舊版殘留、會誤導後續維護的人。SP 在版控外,repo 內無法判定。

**怎麼確認**:去 MSSQL 的 `FA` 資料庫看 `S_PAM_OFD003A_SWSYS011` 的 `@WOSTATUS` 設值。

### E.8 `OFDM003` 的跨資料庫寫入不在交易內,且逐列 commit —— 嚴重度 **高**

**缺陷**:`SQLDb.ExecuteNonQuery(cmdAU)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:509`)沒有帶任何 `DbTransaction`,而且在 `foreach` 迴圈裡逐列送(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:492-519`)。

**影響**:① Oracle 端的四眼交易若在之後回滾,MSSQL 那邊已經改掉的行事曆不會跟著回來;② 迴圈中途某一列失敗而 `throw`,前面成功的列已經 commit 在 MSSQL,**兩邊停在不一致的中間狀態**。沒有補償機制、沒有重試、也沒有對帳。

### E.9 `OFDM003` 修改頁遇到缺日期的月份會 NRE —— 嚴重度 **中**

**缺陷**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:80` 用 `FindByCAL_DATE(SysDate.Day)` 取明細列,回傳可能是 null;`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM003.cs:84` 立刻 `Row.BUSS_ID = "N"`,中間**沒有 null 檢查**。

**影響**:如果某個月在 `OFD003A` 裡缺了某一天(例如當初新增時中斷、或 DB 端被刪過單列),進修改頁按存檔就 NullReferenceException,而且使用者無從得知缺的是哪一天。

### E.10 字串串接進 SQL —— 嚴重度 **中**(範圍廣)

| 位置 | 串接的值 | 來源 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1049`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1070` | 部門代碼去尾兩碼 | 畫面輸入 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1188`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1209` | 部門代碼 | 畫面輸入 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:184-187`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:297-300` | 年度、行事曆類別 | 畫面參數 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:399`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:436` | 年、月 | 查詢條件 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:145`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:187-188`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:231`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:294` | 分行 / 總行代碼、SWIFT | 畫面輸入 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:130-149`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:165-166`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:212` | 查詢條件值、登入者 ID、功能代碼 | 畫面與登入資訊 |

**這些欄位多數有長度或字元集限制(代碼多為英數),實際被注入的門檻高**,但沒有任何一處做跳脫或參數化。`OFDM003` 的 `SUBSTR(CAL_DATE,1,4) = <數字>` 另外還有隱含型別轉換問題 —— 索引失效,而且只要有一列 `CAL_DATE` 前四碼不是數字就 ORA-01722 整句爆掉。

### E.11 有訊息無 `return`:11 支畫面在 `e.Cancel = true` 後繼續執行 —— 嚴重度 **低**

**缺陷**:形狀是 `if (this.ValidateErrList.Show()) e.Cancel = true;` 之後沒有 `return`,直接往下把畫面值抄進 DataRow。範例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:68-73`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:180-191`。

**影響**:目前無實害(`e.Cancel` 已成立,抄值不會落到 DB)。**風險在未來** —— 只要有人在後面加一行有副作用的程式碼(例如呼叫服務、寫 log、動別的表),就會在「使用者已被擋下」的情況下執行。

**對照組**:`OFDM002` / `OFDM015` / `OFDM020` 寫對了,有 `return`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:115-119`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:162-166`)。同一個 codebase 裡兩種寫法並存。

### E.12 `OFDM015` 同一條規則三種寫法,條件不等價 —— 嚴重度 **中**

**缺陷**:「評等序號不可為 0」被寫在三個地方,兩處判「< 1」、一處判「== 0」:

| 位置 | 條件 | 有無訊息 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:58` | `Select("GRADE_SEQ<1")` | 有 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:239` | `Select("GRADE_SEQ<1")` | **無**,只 `e.Cancel` |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:254` | `Convert.ToInt32(...) == 0` | 標紅,不擋 |

**影響**:負數序號在離開列時不會被標紅(第三處判不到),但存檔會被擋(第一處判得到)—— **使用者看不到是哪一列有問題**。另外第二處 `e.Cancel = true` 完全沒有訊息,使用者只會覺得「這一列插不進去」。

### E.13 檢核四層俱全,呼叫端卻被註解 —— 嚴重度 **中**

**缺陷**:`CheckBANK_VALID_CODE`(「總行無效時不可新增分行」)在 PO / Control / FormProxy 三層都在(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:219`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM020_Ctl.cs:165`、`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM020_Pxy.cs:193`),但 UI 的存檔路徑把它整段註解掉了(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:70`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:85-99`)。

**影響**:錯誤訊息字串還在、四層程式碼還在、看起來規則存在 —— **但實際上擋不住任何東西**。目前僅存的呼叫在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM020.cs:483`,那裡只拿來決定欄位唯不唯讀,而且 DB 出錯時判斷方向是反的(E.4)。

**同型的還有兩處被整段註解的檢核**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:427-438`(總行代碼 700 時每日限額必輸 + 須大於 0)、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM002.cs:41-53`(依 PTPF 產品決定集保分公司欄位是否顯示,現在寫死 `Visible = false`)。

### E.14 集保版與內部版兩套基金屬性代碼,沒有對照表 —— 嚴重度 **中**(標假設)

**現象**:`OFD004` / `OFD005`(欄名帶 `_TSCD`,Caption 標「(集保)」)與 `OFD006A` / `OFD007A`(無後綴)是**同一種業務概念的兩套代碼**,各自獨立維護。repo 內找不到任何把兩者對應起來的表、SP 或程式。

**影響**:集保代碼與內部代碼的對應關係若真的存在,它就在人的腦袋裡或版控外的文件裡 —— 加一個新的基金種類時,兩張表都要記得加,沒有任何機制提醒。

**標假設**:也可能兩套代碼根本不需要對應(集保檔只是上傳下載時用的字典)。要看實際的集保介接程式才能確定,那不在本片範圍。

### E.15 `OFDM022.GetBankNm` 三個分支都把結果寫進錯誤的物件 —— 嚴重度 **低**

**缺陷**:`modelVDB.Utility.Result.Clear(); vdb.Utility.Result.AddResultRow(...);` —— 清掉傳入物件的結果,把結果加到方法內部新建的 `vdb`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:230-231`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:235-236`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:242-243`)。

**影響**:因為方法最後 `return vdb`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM022_PO.cs:251`),目前結果傳得回去。**但傳入物件的 Result 被清空了**,呼叫端若同時持有原物件會拿到空的。而且只要有人把 `return vdb` 改成 `return modelVDB`(這在本片是常見寫法,見 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:149`),三個分支就全部變成「沒有結果列」。反正這支畫面本來就 NRE,實際影響為零 —— 列在這裡是因為修活 `OFDM022` 時會踩到。

### E.16 13 個來源檔不是 UTF-8 —— 嚴重度 **中**

**缺陷**:`OFDM003` `OFDM004` `OFDM005` `OFDM006` `OFDM007` `OFDM015` 六支畫面共 13 個 `.cs` 檔只能用 cp950 解;`DB/Trigger/OFD002_T01.SQL` 也是。清單見 §3.5。

**影響**:① 工具鏈若假設 UTF-8 會讀出亂碼或直接爆掉(本文所有掃描都走 `atlas_scan.read_text`);② **同一支畫面的六層編碼不一致**(`OFDM003` UI / PO 是 Big5,Control / FormProxy 是 UTF-8),不能探測一次就套用整條鏈;③ 這幾支的中文註解在某些編輯器裡會顯示成亂碼,§3.4 那句「覆核層級管理 PO 共用介面」在 `OFDM003` ~ `OFDM007` 的 PO 裡就是亂碼狀態。

### E.17 `m_IsUpVld` 旗標:總行改回有效時分行不跟著回來 —— 嚴重度 **中**

**缺陷**:`OFDM019_PO` 的實例欄位 `m_IsUpVld`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:37`)只在 `BeforeUpdate` 且 `BANK_VALID_CODE == 'N'` 時才被寫(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:146-159`),`AfterUpdate` 的分行有效碼連動只有它為真才跑(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:65`)。

**影響**:① **把總行從無效改回有效時,分行不會跟著變回有效** —— 使用者以為復原了,實際上分行全部還是無效;② 旗標從不重置,若 `DataAccessPool` 快取 PO 實例,第二次呼叫會帶著上一次的值(**標假設**,未查證 Pool 的存活範圍)。

### E.18 寫死常數與魔術字串 —— 嚴重度 **低 ~ 中**

| 常數 | 位置 | 說明 |
|---|---|---|
| `"FA"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:53` | MSSQL 連線別名寫死在建構子,換環境要改程式 |
| `'04'` / `'05'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:124`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:301` | 農會 / 漁會。`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3174-3178` 有 `BANK_TYPE.Farmers` / `Fisherman` 常數,UI 用了(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM019.cs:545`)、**PO 沒用** |
| `'0'` / `'1'` / `'3'` / `'4'` | `AGENT_ID` / `CHANNEL_CD` 共 10 處 | 沒有任何常數類別,全部是字面量 |
| `AGENT_ID=0`(數字,不是字串) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM002_PO.cs:1208` | 拿數字比字元欄,靠 Oracle 隱含轉換;同一支檔案別處寫的是 `'0'` |
| `"-1"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:160`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:203`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:242` | 同一個字面量在三支方法裡兩種相反意思(E.4) |
| `SUBSTR(x,2,3)` / `SUBSTR(x,1,3)` / `SUBSTR(x,6,4)` | `OFDM019` / `OFDM020` / `OFDM002` 共 8 處 | 代碼結構規則(前綴幾碼是什麼)散落在字串裡,沒有集中定義 |
| `"E9"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM017.cs:40` | `COD006A` 的群組代碼 |
| `1900 / 9998` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:279` | 年度上下限 |
| `199` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM003_PO.cs:99` | 備註截斷長度,判斷用 200 卻截 199 |

### E.19 其他小坑彙整 —— 嚴重度 **低**

| 坑 | 位置 | 說明 |
|---|---|---|
| `dbProduct = dbProduct;` 自我指派 | 9 支 PO,例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM001_PO.cs:48` | no-op,推測原意是設連線 |
| 空的 `AfterUpdate` handler | 8 支 PO,例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM015_PO.cs:64-67` | 掛了事件但內容只有 `//nothing` |
| grid 錯誤被整個吞掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM015.cs:216-219` | `ugrdOFD016_Error` 一律 `e.Cancel = true`,任何 grid 內部錯誤都不會顯示 |
| `catch` 後訊息是空字串 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:209`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:146`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:146` | 擋是擋了,但使用者看到空白對話框 |
| 查詢條件 `Like` / `Equal` 不一致 | §5 | 同型畫面之間行為不同 |
| `OFD022` / `OFD026` 零外部消費端 | §8.5 | 搭配維護畫面必 NRE,推測是廢棄的表(標假設) |
| `BANK_TYPE` 借 `BANK_BRH` 欄位傳值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:290` | SQL 裡 `BANK_TYPE BANK_BRH` 別名,註解寫「借BANK_BRH存一下值」,之後 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:301` 拿 `BANK_BRH` 當銀行類型判斷 |
| `SELECT 1` 佔位 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM019_PO.cs:63`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM020_PO.cs:105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM023_PO.cs:68`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM024_PO.cs:68` | 四支 `AfterUpdate` 都先用 `"SELECT 1"` 建 `DbCommand` 再覆寫 `CommandText`,是同一份範本複製出來的 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD1` / `OFD2` / `OFD3` 的 26 支 M 畫面;完成 `A` 後綴十三列判定(§2.2);確認五支畫面執行期必 NRE(§3.2);csproj 核對缺漏 0(附錄 D.2) |

由 build_doc.py v2.0.0 於 2026-09-15 14:48 產生 · 標題 104 · 圖 5 · 表格 79 · 程式錨點 591 · § 連結 91 · 引用檢查：畫面 32（缺 0） · Table 34（缺 0） · SP 9（缺 0） · Trigger 1（缺 0） · View 1（缺 0） · 結果集 5（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofd4.md
============================================================

# ATLAS OFD4 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先翻 §1 的圖抓全貌,再讀 §2.2(`A` 後綴到底是什麼)與 §2.1(同一組表被兩支畫面吃),這兩件事是本片最容易誤解的地方;之後 §3 的清冊配 §4 起的畫面章節就讀得動了。**急著知道 `OFDM035` 跟 `OFDM036` 差在哪的人直接跳 §4.1**;**想知道哪兩支畫面連查詢都會炸的人直接跳 §4.2**。

> ⚠ **OFD4 不是一個業務模組,是一份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/` 這個 Entity 專案底下的 **18 支 M 畫面**。切片依據是 Entity 專案資料夾,不是業務;所以本片內部含**四條互不相干的業務線**(§0.1)。名稱 `OFD4` 為**推測**,取自資料夾名。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、各層 `_Ctl` 的 XML 註解與 `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs` 的常數字典**推測**,待選單表回填。`_Ctl` 的註解有三支被證實是複製貼上沒改的殘留(§3.3),引用時要小心。

> ⚠ **兩支畫面在執行期是死的。** `OFDM045` 與 `OFDM046` 的 PO 繼承 `MultiRowEVAPO` / `BasicEVAPO`,這兩個基底的 `dbTA` 宣告即 `= null` 且建構子賦值那四行整段被註解,連 `Select()` 第一行就 `dbTA.CreateConnection()`。**這兩支不是存檔才炸,是連查詢都炸**(§4.2、附錄 E.1)。它們有進 csproj、編得起來,所以靜態掃描看不出問題。

> ⚠ **〔客戶特定〕**:`BANK_HQ = 'ALL'` 這個哨兵值、銷售機構別 `'1'`/`'2'`/`'5'`、身份別 `'00'`/`'01'`/`'02'`、無總代理代碼 `'0000000000'`、幣別預設 `'TWD'` 為本站台的值。

> ⚠ **〔共用〕**:`OFD068A`(11 個模組讀)、`OFD062`(9 個)、`OFD030`(7 個)、`OFD038A`(6 個)、`OFD041A`(5 個)同時服務 BMS / CAS / COD / CRM / DSM / EC / OTA / OFDB / RSP / SDM / NFD.Report(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 18 支畫面管什麼(推測)

先給結論:**本片沒有單一業務主題,是「基金作業的周邊代碼檔與機構主檔」這個大方向底下的四塊設定檔維護**。18 支全部是 M 型維護畫面,沒有一支是查詢、批次或報表。

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 匯款與費用** | `OFDM030` `OFDM035` `OFDM036` `OFDM064` | 集保申購款要匯進哪個銀行帳戶、贖回款匯出去要收多少匯費(全行通用一組 + 個別銀行一組)、基金公司的境外申購匯款帳戶(SWIFT / BIC / IBAN) | 欄位 Caption「匯款帳號對應碼」「贖回匯款最高金額」「匯費」「金資匯費」;`OFD064` 有 `ALLOT_BANK_SWIFT` 與 `IBAN_CODE` |
| **B 機構主檔** | `OFDM034` `OFDM061` `OFDM062` `OFDM065` `OFDM066` `OFDM068` | 產壽險公司、TA 公司、基金公司(含聯絡人)、基金公司銷售國別、總代理公司(含聯絡人)、銷售機構(含聯絡人) | 各表的 `*_NM_C` / `*_NM_E` / `CNT_*` 欄位群;`_Ctl` 註解「產壽險公司基本資料」「基金公司」「總代理公司」 |
| **C 文件與缺件** | `OFDM039` `OFDM040` `OFDM041` `OFDM046` `OFDM054` `OFDM055` | 缺件代碼與其卡控效果、通知書寄發設定、帳務說明片語範本、作業文件範本(可掛附件)、受益人類別應繳文件、資產證明內容 | `OFD039A` 有 `LIMIT_ALLOT` / `LIMIT_REDEM_DAY` 一整排卡控旗標;`OFD046` / `OFD047` 有 `ATTACHFILE` BLOB |
| **D 基金分類與 KYC** | `OFDM038` `OFDM045` | 基金群組(一個群組掛多檔基金)、KYC 問項(依身份別分自然人 / 法人兩套) | `OFD038A` 的鍵是 `FUND_GRPCD` + `FUND_ID`;`OFD045` 的 `KYC_CODE` 去 `CTL014` 查 `SourceType` `'334'`/`'335'`,由 `BF_COUNTRY_X` 決定 |

四塊之間**沒有任何程式呼叫**。資料表層面只有三條真依賴:

| 依賴 | 內容 | 錨點 |
|---|---|---|
| A ← B | `OFDM064`(基金公司匯款帳戶)主檔查詢 `LEFT JOIN OFD062` 取基金公司簡稱;`OFDM065` 同樣 join | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:132-133`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:122-123` |
| B → B(只讀) | `OFDM062`(基金公司)join `OFD061`(TA 公司)與 `OFD066`(總代理),三張表在同一頁互相帶名稱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:149-152` |
| B → B(寫) | `OFDM034` 存檔後**直接 UPDATE** `OFD068A`(銷售機構)與 `OFD071A`(通路),把產壽險公司改名同步過去 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:64-100` |

讀 OFD4 的人如果預期整片是一條流程,會在 §4.4 之後完全對不上——先知道這件事比較省時間。

### 0.2 不管什麼

| 不在 OFD4 | 在哪 | 依據 |
|---|---|---|
| 把 `OFD030.ACC_NO_CORR` 組成受益人虛擬帳號 | Oracle Function `GET_REMIT_ACC_NO`(版控內,`DB/Function/`) | `DB/Function/GET_REMIT_ACC_NO.SQL:30-33` 讀 `OFD030.ACC_NO_CORR`,再串 `BMS001A` 的統編 / 身分證 |
| 真正算一筆贖回要扣多少匯費 | 版控外的計價流程 | repo 內只有 `OFDM035` / `OFDM036` 在**維護**級距,沒有任何程式讀 `OFD036A` 去算費 |
| 基金主檔建檔 | `OFDM081B`(境外 `OFD081`);境內主檔是 `OFD081A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:247` 也讀 `OFD064` |
| 銷售機構承銷哪些基金 | `OFD070A`(境內)/ `OFD070`(境外),由別的畫面維護 | `OFDM068` 只在改「有效碼」時順手 UPDATE 這兩張,不維護內容:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:229-272` |
| 缺件到底怎麼擋交易 | 交易面各畫面自己讀 `OFD039A` | `OFDM039` 只存旗標;消費端在 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6204` 與 EC / OFDI |
| 通路主檔 `OFD071A` | `OFDM071`(不在本片) | `OFDM034` 只寫入,不維護 |
| 基金公司聯絡人的「作業別」代碼字典 | `COD006A` 的 `CODE_SORT = '99'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:233-235` |
| 銷售機構代碼本身的產生 | 由使用者輸入,無流水號機制 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:44-51` 只檢查非空 |

### 0.3 使用角色

18 支全部宣告成四眼(EVA)維護畫面,角色由平台的 ToDo 機制指派,OFD4 自己不定義角色——所有 PO 都只是把 `xTableHelper.AppendToDoString(...)` 接到查詢字串尾巴(例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:156`)。詳見 `architecture.md §3`。

**三個要注意的例外:**

| 例外 | 內容 | 錨點 |
|---|---|---|
| `OFDM045` / `OFDM046` | 走的是**舊世代** `TableHelper.AppendToDoString`(無 `x` 前綴)與 `MultiRowEVAPO` / `BasicEVAPO`,而且執行期一定 NRE,四眼形同不存在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:59`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:157` |
| `OFDM068` | **自己覆寫 `Add` / `Update`**,四眼狀態靠手動 `xEVAUtility.SetAddStatusToDo` / `SetAddStatus` 逐列寫,不走基底 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:285`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:418` |
| `OFDM034` | 在 `AfterUpdate` 直接 UPDATE 兩張別的模組在用的表,**那兩張表的異動不經任何四眼** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:57-101` |

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(只讀 join) | `OFD019A`(金融機構總行)、`FSK003`(幣別)、`OFD008`(國別)、`OFD081A` / `OFD0811A`(境內基金與警示備註)、`COD006A`(代碼檔)、`CTL014`(共用下拉代碼)、`OFD061` / `OFD062` / `OFD066`(彼此互相 join) | 全部 `LEFT JOIN`,只取說明欄 |
| 下游(本片的表被誰讀) | `OFD068A` 被 11 個模組讀、`OFD062` 被 9 個、`OFD030` 被 7 個(含 `GET_REMIT_ACC_NO`)、`OFD038A` 被 6 個、`OFD041A` 被 5 個 | 見 §8 |
| 旁寫(本片寫別人的表) | `OFDM034` → `OFD068A` `OFD071A`;`OFDM068` → `OFD070A` `OFD070` | 見 §8.1、§8.2 |
| 平行(同一組表兩個維護入口) | `OFD035A` + `OFD036A` 同時被 `OFDM035` 與 `OFDM036` 宣告,靠 `BANK_HQ = 'ALL'` 切開 | §4.1 |

### 0.5 全域開關

本片沒有 `App.config` 層級的業務開關。真正決定行為的「開關」都是資料欄位或寫死常數:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `BANK_HQ = 'ALL'`(哨兵列) | 字面量 `'ALL'` vs 真實銀行代碼 | **決定一筆匯費設定歸 `OFDM035` 還是 `OFDM036` 管**。`OFDM035` 的主檔與明細 SQL 都寫死 `BANK_HQ='ALL'`,`OFDM036` 寫死 `BANK_HQ <>'ALL'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:122`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:127` |
| `AGENT_ID`(銷售機構別) | `CTL014` `SourceType='062'`,**值域在 DB**;程式碰過 `'1'` `'2'` `'5'` | `'2'`(**推測**券商)時 `OFDM068` 的交易檢核改走 `FSK005` 的券商代碼展開;`'1'`/`'2'` 時「銷售機構付款行」變必填;`'5'`(**推測**產壽險)是 `OFDM034` 同步寫入的對象 | `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/TrustAgentIDDataSrc.cs:15`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:594`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:55`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:72` |
| `BF_COUNTRY_X`(身份別) | `'00'` 自然人+法人 · `'01'` · `'02'` | `OFDM040` 用它做「`'00'` 與 `'01'`/`'02'` 不可並存」的互斥檢核;`OFDM045` 用它切 KYC 問項來源(`'01'` → `CTL014` `SourceType='334'`,否則 `'335'`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-271`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:53-54` |
| `AGENT_VALID_CODE`(銷售機構有效碼) | `'Y'` 有效 · `'N'` 無效 | `OFDM068` 存檔時連動 UPDATE `OFD070A` / `OFD070`;境外表的值要反轉成 `'0'`/`'1'` | 值域 `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:123-134`、用法 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:265` |
| `DECLARE_TSCD`(申報集保碼) | `'Y'` / 其他 | `'Y'` 時 `OFDM068` 的「公會核准日期」與「公會核准文號」變必填 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:66-77` |
| `GAGENT_CD = '0000000000'` | 字面量 | `OFDM062` 用 `CASE` 把它翻成「無總代理」旗標 `GAGENT='0'`;`OFDM061` 直接擋「不可新增 TA 公司代碼為 `'0000000000'`」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:138-139`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM061.cs:153` |
| `FH_CD = '0000000000'` | 字面量 | `OFDM062` 用它認「系統公司資料」:不可新增 / 修改 / 刪除,而且免填聯絡人 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:49`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:374`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:417` |
| `CRNCY_CD = 'TWD'` | 字面量 | `OFDM035` / `OFDM036` 新增時預設 TWD;`OFDM036` 查不到該幣別的郵費就 fallback 抓 TWD 的 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:110`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:233` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD4 全景：匯款與費用、機構主檔、文件與缺件、基金分類與 KYC 四條線，加上兩條旁寫與下游讀者
圖中文字:① 匯款與費用：錢進來走哪個帳戶、錢出去收多少匯費 / OFDM030 / OFD030 集保入款銀行 / OFDM035 / OFD035A BANK_HQ='ALL' / OFDM036 / OFD035A BANK_HQ<>'ALL' / OFDM064 / OFD064 境外匯款帳戶 / ② 機構主檔：本片最多人讀的一塊 / OFDM062 / OFD062/OFD063 基金公司 / OFDM066 / OFD066/OFD067 總代理 / OFDM068 / OFD068A/OFD069A 銷售機構 / OFDM034 OFDM061 OFDM065 / 產壽險 / TA / 銷售國別 / ③ 文件與缺件：代碼檔，靠別的模組去解讀 / OFDM039 / OFD039A 缺件代碼與卡控旗標 / OFDM040 / OFD040A 通知書寄發 / OFDM041 / OFD041A 帳務片語範本 / OFDM054 OFDM055 / 應繳文件 / 資產證明 / ④ 基金分類與 KYC：兩支，其中一支執行期是死的 / OFDM038 / OFD038A 基金群組 / OFDM045 / OFD045 KYC 問項 / OFDM046 / OFD046/OFD047 文件範本+附件 / 兩支 PO 繼承舊基底 / dbTA 恆 null 連查詢都 NRE / ⑤ 旁寫：本片有兩支會去改別人的表，而且不經對方的四眼 / OFDM034 存檔後 / AfterUpdate / OFD068A + OFD071A / 名稱同步 三值邏輯會漏 / OFDM068 存檔時 / Add / Update / OFD070A + OFD070 / = 配 '%' 非券商全不中 / ⑥ 下游：主檔外流、聯絡人明細不外流 / BMS / CAS / COD / CRM / DSM / 讀 OFD068A OFD062 / OTA / OTAB / OFDB / RSP / SDM / 讀機構與代碼檔 / GET_REMIT_ACC_NO / 讀 OFD030 組虛擬帳號 / EC / OFDI / NFD.Report / 讀缺件與基金群組
```

*圖:圖 1 OFD4 全景。橘框=本片的維護入口;橘虛框=有風險或執行期死的;灰虛框=別的模組;黑框=無原始碼或版控外。四條線彼此沒有程式呼叫，真正要小心的是 ⑤ 的兩條旁寫——本片會去改別人的表，而且兩條都有缺陷。*

### 1.2 資料表關係

圖放在 §2 的開頭(`ofd4.figs.py` 的 `h2:2-`)。重點看兩件事:**帶 `A` 與不帶 `A` 的兩群不是境內 / 境外**(§2.2),以及 **`OFD035A` + `OFD036A` 這一組被兩支畫面共用**(§4.1)。

### 1.3 畫面依 PO 基底與編譯狀態分群

圖放在 §3 的開頭(`h2:3-`)。一句話總結:**18 支全部在 csproj 裡,但其中兩支(`OFDM045` `OFDM046`)的 PO 停在舊世代基底,執行期第一行就 NRE——編得起來不代表跑得動。**

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。唯一有檔案進出的是 `OFDM046` 的附件上傳 / 下載,那是 M 畫面上的兩個按鈕(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:88`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:123`),不是 B 型畫面——而且那支畫面執行期是死的。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——18 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM068` 把銷售機構改成無效時,同一筆交易裡連動 `OFD070A` / `OFD070`(§4.4),但那是同步的,不構成泳道。

## 2. 資料模型

```text
[圖] OFD4 二十二張表的兩群（帶 A / 不帶 A）、A 後綴的真相，以及同一組表兩支畫面的切分方式
圖中文字:A 帶 A 後綴的 11 張：MSSQL→Oracle 遷移時改過名（不是境內外） / OFD034A / PK 產壽險公司代碼 / OFD035A + OFD036A / PK 銀行+幣別(+起額) / OFD038A / PK 群組+基金 / OFD039A OFD040A OFD041A / 缺件 / 通知書 / 片語 / OFD054A / PK 受益人類別+文件 / OFD055A / PK 資產證明代碼 / OFD068A + OFD069A / PK 機構別+機構代碼 / 對照：MSSQL 層叫 OFD034 / Basic 層叫 OFD034A / B 不帶 A 的 11 張：遷移時沿用原名，兩群都有機構主檔 / OFD030 / PK 金融機構總行 / OFD062 + OFD063 / PK 基金公司代碼 / OFD066 + OFD067 / PK 總代理代碼 / OFD061 OFD064 OFD065 / TA / 匯款帳戶 / 國別 / OFD045 / KYC 問項 小寫四眼欄 / OFD046 + OFD047 / 文件範本+附件 小寫四眼欄 / 查無 OFD062A OFD066A / 配對表命中數 0 / 結論：A 不是境內外 / ofd7 的規則不能外推 / C 唯一的一組表兩支畫面：靠 BANK_HQ 切成互斥兩半 / OFDM035 / WHERE BANK_HQ='ALL' / OFD035A 主檔 / 贖回上限 + 郵寄費 / OFDM036 / WHERE BANK_HQ<>'ALL' / OFD036A 明細 / 匯費級距 起額~迄額 / D 三組「機構 + 聯絡人」：主檔被很多人讀，明細只有自己用 / OFD062 → OFD063 / 明細 PK 只有 FH_CD 一欄 / OFD066 → OFD067 / 明細 PK 兩欄 含 DATAID / OFD068A → OFD069A / 明細 PK 三欄 / 三組結構不一致 / 成對只改一邊 / 外部唯讀：join 進來取說明，本片從不寫入 / OFD019A / 金融機構總行 / FSK003 OFD008 / 幣別 / 國別 / OFD081A OFD0811A / 基金與警示備註 / COD006A / 聯絡人作業別 / CTL014 / 334/335/150/073/062
```

*圖:圖 2 資料模型。橘框=主檔或維護入口;白框=明細;橘虛框=陷阱;黑框=外部唯讀或無原始碼。A / B 兩群的分界不是境內外——兩群裡都有機構主檔，而且找不到任何配對表;真正的分界是 MSSQL→Oracle 遷移時有沒有改名（見 §2.2 的三組對照）。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

18 支畫面共宣告 **22 張實體表**(`OFD035A` 與 `OFD036A` 各被宣告兩次,所以宣告筆數是 24)。宣告方式分三派:

| 派別 | PO 基底 | 特徵 | 本片畫面 |
|---|---|---|---|
| **單筆型(現行)** | `BaseEVADaoPO` | `MasterTable` 單一 + `DetailTable` 清單,走 `xEVAEventArgs` / `xTableHelper` | `OFDM030` `OFDM034` `OFDM035` `OFDM036` `OFDM039` `OFDM040` `OFDM054` `OFDM055` `OFDM061` `OFDM062` `OFDM064` `OFDM065` `OFDM066` `OFDM068` |
| **多筆型(現行)** | `BaseMultiRowEVADaoPO` | `MasterTable` 是 `List`,**沒有明細概念**;主從其實是同一張表,靠 `MasterPKey` 分群,畫面上半是「群」下半是「群內各列」 | `OFDM038` `OFDM041` |
| **舊世代(已無法執行)** | `MultiRowEVAPO` / `BasicEVAPO` | 走 `PrepareSQLEventArgs` / `TableHelper` / `EVAStringHelper`,`dbTA` 恆為 null | `OFDM045` `OFDM046` |

多筆型與單筆型的差別見 `architecture.md §3.9`。**多筆型沒有明細表這件事很容易看錯**——`atlas_scan.py --screen OFDM038` 報「明細 —」不是漏掉,是真的沒有。

逐支的宣告:

| 畫面 | 基底 | 主檔(實體表 → vdb 名) | 明細(實體表 → vdb 名) | `MasterPKey` | 錨點 |
|---|---|---|---|---|---|
| `OFDM030` | 單筆 | `OFD030` → `OFDM030` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:49` |
| `OFDM034` | 單筆 | `OFD034A` → `OFDM034` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:45` |
| `OFDM035` | 單筆 | `OFD035A` → `OFDM035` | `OFD036A` → `OFDM035_Detail` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:30-31` |
| `OFDM036` | 單筆 | `OFD035A` → `OFDM036` | `OFD036A` → `OFDM036_Detail` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:34-35` |
| `OFDM038` | 多筆 | `OFD038A` → `OFDM038` | — | `FUND_GRPCD` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:29-30` |
| `OFDM039` | 單筆 | `OFD039A` → `OFDM039` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:48` |
| `OFDM040` | 單筆 | `OFD040A` → `OFDM040` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:47` |
| `OFDM041` | 多筆 | `OFD041A` → `OFD041` | — | `ACCOUNT_COPY` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM041_PO.cs:33-34` |
| `OFDM045` | 舊多筆 | `OFD045` → `OFDM045` | — | `BF_COUNTRY_X` `KYC_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:14-16` |
| `OFDM046` | 舊單筆 | `OFD046` → `OFD046` | `OFD047` → `OFD047` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:23-24` |
| `OFDM054` | 單筆 | `OFD054A` → `OFD054A` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM054_PO.cs:44` |
| `OFDM055` | 單筆 | `OFD055A` → `OFDM055` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM055_PO.cs:38` |
| `OFDM061` | 單筆 | `OFD061` → `OFDM061` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM061_PO.cs:45` |
| `OFDM062` | 單筆 | `OFD062` → `OFD062` | `OFD063` → `OFD063` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:43-44` |
| `OFDM064` | 單筆 | `OFD064` → `OFDM064` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:42` |
| `OFDM065` | 單筆 | `OFD065` → `OFDM065` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:42` |
| `OFDM066` | 單筆 | `OFD066` → `OFD066` | `OFD067` → `OFD067` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:43-44` |
| `OFDM068` | 單筆 | `OFD068A` → `OFDM068_Master` | `OFD069A` → `OFDM068_Detail` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:38-39` |

> ⚠ **vdb 名有三種命名風格並存**:`OFDM0xx`(照畫面代號)、`OFD0xx`(照實體表名)、`OFDM068_Master` / `OFDM035_Detail`(角色式)。寫程式時 `MasterTable.vdbTableName` 取的是哪一種要逐支看,沒有通則。`OFDM041` 更特別:實體表 `OFD041A`,vdb 名卻叫 `OFD041`——而 `OFD041` **也是一張真的存在、還有人在讀的實體表**(附錄 E.6)。

### 2.2 `A` 後綴的真相:是 MSSQL → Oracle 遷移時的改名,**不是**境內 / 境外

`ofd7.md §4` 查證過 OFD 的 `A` 後綴在**費率表**那一群是境內(`FUND_TYPE='2'`)/ 無後綴是境外(`'1'`),值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`。**本片 18 支剛好分成兩群,但這個解釋在本片完全對不上。**

本片的分群:

| 群 | 表 | 對應畫面 |
|---|---|---|
| **帶 `A`**(11 張) | `OFD034A` `OFD035A` `OFD036A` `OFD038A` `OFD039A` `OFD040A` `OFD041A` `OFD054A` `OFD055A` `OFD068A` `OFD069A` | `OFDM034` `OFDM035` `OFDM036` `OFDM038` `OFDM039` `OFDM040` `OFDM041` `OFDM054` `OFDM055` `OFDM068` |
| **不帶 `A`**(11 張) | `OFD030` `OFD045` `OFD046` `OFD047` `OFD061` `OFD062` `OFD063` `OFD064` `OFD065` `OFD066` `OFD067` | `OFDM030` `OFDM045` `OFDM046` `OFDM061` `OFDM062` `OFDM064` `OFDM065` `OFDM066` |

**三條反證,說明它不是境內 / 境外:**

| # | 觀察 | 錨點 / 依據 |
|---|---|---|
| 1 | **兩群裡都有「不可能有境內外之分」的實體。** 帶 `A` 的 `OFD034A` 是產壽險公司主檔、`OFD068A` 是銷售機構主檔;不帶 `A` 的 `OFD062` 是基金公司主檔、`OFD066` 是總代理主檔。這四張都是機構身分,一家公司不會有「境內版」與「境外版」兩筆 | `OFD034A` PK = `INSU_CD`、`OFD062` PK = `FH_CD`、`OFD066` PK = `GAGENT_CD`、`OFD068A` PK = `AGENT_ID`+`AGENT_CODE`,全部單一鍵,**沒有任何境內外識別欄** |
| 2 | **找不到配對表。** 若真是境內 / 境外成對,應該同時存在 `OFD062` 與 `OFD062A`。實測對 `Dev` 與 `DB` 全樹搜 `OFD030A` `OFD045A` `OFD046A` `OFD061A` `OFD062A` `OFD064A` `OFD065A` `OFD066A`,**命中數全部是 0** | 全庫字串搜尋 |
| 3 | **決定性證據:同一個實體在舊 MSSQL 層叫無後綴,在現行 Oracle 層叫帶 `A`。** `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/` 這個資料夾是遷移前的副本,裡面對同一份業務資料寫的是 `OFD034` / `OFD038` / `OFD039`;`Dev/Common/Source/DataSource/PO.DataSource/Basic/` 這份現行的寫的是 `OFD034A` / `OFD038A` / `OFD039A` | `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:1644`(`FROM OFD034`)vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:2879`(`FROM OFD034A`);`Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:2934`(`FROM OFD038`)vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:1322`(`FROM OFD038A`);`Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicOFD_PO.cs:4496`(`FROM OFD039`)vs `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:6204`(`FROM OFD039A`) |

**結論(標「假設」的部分已標明)**:

- **確定的事**:本片的 `A` 後綴與境內 / 境外無關;`ofd7.md §4` 的境內外規則只適用於費率表那一群(`OFD193A` / `OFD194A` 等),**不能外推到整個 OFD**。

- **假設**:`A` = MSSQL 時代的表在遷移到 Oracle 時被重新命名的那一批,無後綴 = 遷移時沿用原名的那一批。依據是上表第 3 條的三組對照。**缺:DB 連線與遷移文件**,無法證明是全面規則。

- **反例存在**:`OFD030` / `OFD061` / `OFD062` / `OFD066` 這些無後綴的表在現行 `Basic/BasicOFD_PO.cs` 裡也還是無後綴(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:1168`、`:2809`、`:3953`、`Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:448`),所以遷移**不是全部改名**,只有一部分改。

### 2.3 一組表、兩支畫面:`OFD035A` + `OFD036A`

全庫罕見的情形:`OFDM035` 與 `OFDM036` 宣告**完全相同**的主檔 `OFD035A` 與明細 `OFD036A`。

|  | `OFDM035` | `OFDM036` |
|---|---|---|
| 主檔實體表 | `OFD035A` | `OFD035A` |
| 主檔 vdb 名 | `OFDM035` | `OFDM036` |
| 明細實體表 | `OFD036A` | `OFD036A` |
| 明細 vdb 名 | `OFDM035_Detail` | `OFDM036_Detail` |
| 主檔 WHERE | `BANK_HQ='ALL'` | `BANK_HQ <>'ALL'` |
| 明細 WHERE | `BANK_HQ='ALL'`(手寫) | 無(交給 `xTableHelper.GetSelectString` 依參數組) |

兩支的資料是**互斥分割**,不是兩份副本。完整的差異分析在 §4.1。

### 2.4 表的主鍵與四眼欄位

「PK」欄取自對應 xsd 的 `xs:unique … msdata:PrimaryKey`,是 **DataTable 的鍵**,不保證等於 DB 上的 constraint(`architecture.md §5.5`)。

| 表 | vdb 名 | PK(來源 xsd) | 四眼 13 欄 | 欄數 |
|---|---|---|---|---|
| `OFD030` | `OFDM030` | `BANK_HQ` | 齊 | 28 |
| `OFD034A` | `OFDM034` | `INSU_CD` | 齊 | 27 |
| `OFD035A` | `OFDM035` / `OFDM036` | `BANK_HQ` `CRNCY_CD` | 齊 | 20(`OFDM036` 側 21,多 `BANK_HQ_SHNM`) |
| `OFD036A` | `OFDM035_Detail` / `OFDM036_Detail` | `BANK_HQ` `CRNCY_CD` `REMIT_AMT1` | 齊 | 21 |
| `OFD038A` | `OFDM038` | `FUND_GRPCD` `FUND_ID` | 齊 | 19 |
| `OFD039A` | `OFDM039` | `LACK_CODE` | 齊 | 34 |
| `OFD040A` | `OFDM040` | `STATEMENT_CODE` `BF_COUNTRY_X` `OPEN_ACC_TYPE` | 齊 | 27 |
| `OFD041A` | `OFD041` | `DATA_SEQ` `ACCOUNT_COPY` | 齊 | 18 |
| `OFD045` | `OFDM045` | `BF_COUNTRY_X` `KYC_CODE` `KYC_ITEM` | 齊(**小寫欄名**) | 21 |
| `OFD046` | `OFD046` | `DATA_SEQ` | 齊(**小寫欄名**) | 19 |
| `OFD047` | `OFD047` | `DATA_SEQ` `FILENAME` | 齊(**小寫欄名**) | 19 |
| `OFD054A` | `OFD054A` | `BF_SORT_CD` `LACK_CODE` | 齊 | 19 |
| `OFD055A` | `OFDM055` | `ASSET_CODE` | 齊 | 18 |
| `OFD061` | `OFDM061` | `TA_CD` | 齊 | 30 |
| `OFD062` | `OFD062` | `FH_CD` | 齊 | 37 |
| `OFD063` | `OFD063` | **`FH_CD`(只有一欄)** | 齊 | 33 |
| `OFD064` | `OFDM064` | `FH_CD` `CRNCY_CD` | 齊 | 33 |
| `OFD065` | `OFDM065` | `FH_CD` `COUNTRY_CD` | 齊 | 22 |
| `OFD066` | `OFD066` | `GAGENT_CD` | 齊 | 25 |
| `OFD067` | `OFD067` | `GAGENT_CD` `DATAID` | 齊 | 28 |
| `OFD068A` | `OFDM068_Master` | `AGENT_ID` `AGENT_CODE` | 齊 | 48 |
| `OFD069A` | `OFDM068_Detail` | `AGENT_ID` `AGENT_CODE` `DATA_SEQ`(另有 `DATA_SEQ` 單欄 UNIQUE) | 齊 | 29 |

三個 PK 值得單獨記住:

| 表 | 問題 | 錨點 |
|---|---|---|
| `OFD063` | **明細表的 DataTable PK 只有 `FH_CD` 一欄**,而 `OFD063` 是「一家基金公司多位聯絡人」。同一家公司載入第二位聯絡人時,只要 `DataSet.EnforceConstraints` 沒被框架關掉就會拋 `ConstraintException`。對照組 `OFD067`(總代理聯絡人,同樣結構)的 PK 是 `GAGENT_CD` + `DATAID` 兩欄 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM062Model.xsd:397-400` vs `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM066Model.xsd` |
| `OFD045` / `OFD046` / `OFD047` | 四眼 13 欄用**小寫**(`Status` `CreateID` `EntryDate` …),其餘 19 張全部大寫。這是舊世代 xsd 的痕跡,與 §2.2 的遷移故事一致 | `atlas_scan.py --screen OFDM046` 的欄位表 |
| `OFD069A` | PK 三欄之外另有一個 `DATA_SEQ` 單欄 UNIQUE。`DATA_SEQ` 若在不同銷售機構間重複就會撞到那個 UNIQUE | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM068Model.xsd` |

### 2.5 欄位中文名(來自 xsd `msdata:Caption`)

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。本片 22 張表的業務欄大致都有填,四眼 13 欄與 `DATAID` 一律留空——這是全庫通則。

各表的主要業務欄(只列有 Caption 的,四眼欄省略):

| 表 | 業務欄(Caption) |
|---|---|
| `OFD030` | `BANK_HQ`(金融機構總行代碼)`BANK_NAME`(金融機構總行簡稱)`REMIT_ACC_NAME_C`(帳戶名稱(台幣))`REMIT_BANK_NM_C`(匯入銀行名稱(台幣))`REMIT_ACC_NAME_E`(帳戶名稱(外幣))`REMIT_BANK_NM_E`(匯入銀行名稱(外幣))`ACC_NO_CORR`(匯款帳號對應碼)`SEAL_FEE`(核印費)`BANK_TYPE`(扣款行作業別)`EFFECT_YN`(有效銀行帳號 Y/N) |
| `OFD034A` | `INSU_CD`(產壽險公司代碼)`INSU_NM_C`(中文名稱)`INSU_SHNM_C`(中文簡稱)`INSU_NM_E`(英文名稱)`INSU_ZIP`(郵遞區號)`INSU_ADDR`(地址)`INSU_TEL_AREA` / `INSU_TEL`(電話)`INSU_FAX_AREA` / `INSU_FAX`(傳真)`INSU_PRESENT`(負責人)`INSU_GM`(總經理) |
| `OFD035A` | `BANK_HQ`(金融機構總行代碼)`CRNCY_CD`(幣別代碼)`CRNCY_NM`(幣別)`REMIT_MAX`(贖回匯款最高金額)`POST_FEE`(贖回支票郵寄費用);`OFDM036` 側多 `BANK_HQ_SHNM` |
| `OFD036A` | `BANK_HQ`(金融機構總行代碼)`CRNCY_CD`(幣別代碼)`REMIT_AMT1`(起始金額)`REMIT_AMT2`(終止金額)`REMIT_FEE`(匯費)`REMIT_BFEE`(金資匯費) |
| `OFD038A` | `FUND_GRPCD`(基金群組代碼)`FUND_ID`(基金代碼)`GRPCD_DESCRP`(基金群組名稱)`FUND_SH_NM`(基金中文簡稱,join 來的) |
| `OFD039A` | `LIMIT_RSP`(限制下次定額收件否)`LIMIT_RSP_DAY`(限制下次定額收件天數)`STOP_PAY`(暫停付款)`LACK_OPEN_CHG`(適用受益人異動缺件否)`LACK_RSP_CHG`(適用小額異動缺件否);**`LACK_CODE` `CODE_DESCRP` `ON_SHORE` `OFF_SHORE` `LACK_OPEN` `LACK_ALLOT` `LACK_REDEM` `LIMIT_ALLOT` 等 12 欄沒有 Caption** |
| `OFD040A` | `STATEMENT_NAME`(通知書代碼名稱)`SEND_NAME`(寄發碼名稱)`OPEN_ACC_TYPE`(開戶類別);**`STATEMENT_CODE` `BF_COUNTRY_X` `SEND_CODE` `SEND_POST` `SEND_EMAIL` `SEND_FAX` `SEND_EMP_EMAIL` `SEND_COLLECT` `SEND_NEW_FLASH` 沒有 Caption** |
| `OFD041A` | `ACCOUNT_COPY`(範本名稱)`DATA_SEQ`(流水號)`ACCOUNT_MEMO`(範本內容) |
| `OFD045` | **全部沒有 Caption**(`BF_COUNTRY_X` `KYC_CODE` `KYC_ITEM` `KYC_DESCRP` `KYC_ORDER` `DisplayName`) |
| `OFD046` | `DATA_SEQ`(資料序號)`DOC_TITLE`(範本名稱)`PROG_NO`(程式代碼)`MEMO`(備註) |
| `OFD047` | `FILENAME`(檔案名稱)`ATTACHFILE`(下載)`Add`(檔案下載) |
| `OFD054A` | `BF_SORT_CD`(受益人類別)`LACK_CODE`(文件代碼)`CODE_DESCRP`(文件名稱)`BF_BOARD_DESCRP`(受益人類別名稱) |
| `OFD055A` | `ASSET_CODE`(資產證明內容代碼)`ASSET_NAME`(資產證明內容代碼名稱)`EFFECT_MONTH`(有效月份) |
| `OFD061` | `TA_CD`(TA 公司代碼)`TA_NM_C`(中文名稱)`TA_NM_E`(英文名稱)`TA_SYS_ID`(TA 系統處理區分)`CNT_P`(聯絡人姓名)`CNT_DEPT`(部門)`CNT_TITLE`(職稱)`CNT_TEL`(電話號碼)`CNT_FAX`(傳真號碼)`CNT_EMAIL`、`MAIL_ZIP`(郵遞區號)`TA_ADDR`(地址) |
| `OFD062` | `FH_CD`(基金公司代碼)`FH_NM_C` / `FH_NM_SH_C` / `FH_NM_E` / `FH_NM_SH_E`(中英文名稱與簡稱)`COUNTRY_CD`(所在國別)`TA_OP`(TA 處理碼)`TA_CD`(TA 公司代碼)`FH_ADDR`(地址)`BIC_CODE`(BIC 代碼)`FH_TSCD_CODE`(集保公司編號)`TRADE_ID`(交易書號代碼)`GAGENT`(總代理)`GAGENT_CD`(總代理公司代碼)`CORP_CODE`(關貿基金公司代碼)`LAUNCH_CD`(自行發行否) |
| `OFD063` | `CNT_CODE`(聯絡人作業別[代碼])`CNT_DESCRP`(聯絡人作業別)`CNT_WINDOW`(主要聯絡窗口別)`CNT_P`(姓名)`CNT_DEPT`(部門)`CNT_TITLE`(職稱)`CNT_TEL1`~`CNT_TEL3`、`CNT_FAX1`~`CNT_FAX3`、`CNT_EMAIL`、`CNT_MEMO` |
| `OFD064` | `ALLOT_BANK_NM` `ALLOT_BANK_SWIFT` `ALLOT_BANK_BIC` `ALLOT_BANK_ADDR` `ALLOT_REMIT_ACC_NAME` `ALLOT_REMIT_ACC_NO` `ALLOT_REMIT_MEMO` `ALLOT_CORR_NM` `ALLOT_CORR_SWIFT` `ALLOT_CORR_BIC` `IBAN_CODE` |
| `OFD065` | `FH_CD` `COUNTRY_CD`(兩欄構成的純關聯表) |
| `OFD066` | `GAGENT_CD`(總代理公司代碼)`GAGENT_NM_C` / `GAGENT_NM_SH_C` / `GAGENT_NM_E` / `GAGENT_NM_SH_E`(中英文名稱與簡稱)`GAGENT_ADDR`(地址)`TSCD_AGENT_CD`(集保公司編號) |
| `OFD067` | `CNT_WINDOW`(主要聯絡窗口別)`CNT_P`(姓名)`CNT_DEPT`(部門)`CNT_TITLE`(職稱)`CNT_TEL1`(電話號碼(1))`CNT_TEL2`(電話號碼(2))`CNT_FAX`(傳真號碼)`CNT_EMAIL`、`CNT_MEMO` |
| `OFD068A` | 48 欄,主要有 `AGENT_ID` `AGENT_CODE` `AGENT_NAME` `AGENT_NAME_E` `AGENT_SHNM` `AGENT_VALID_CODE` `SIGN_END_DATE` `DECLARE_TSCD` `CO_DATE` `CO_NO` `TSCD_AGENT_CODE` `EC_DEPT_NFD` `IVR_DEPT_NFD` `EC_DEPT_OFD` `IVR_DEPT_OFD` `CHECK_NFD_DETAIL` `SPONSOR_CHK` `KYC_YN` |
| `OFD069A` | `DATA_SEQ` `CNT_P` `CNT_DEPT` `CNT_TITLE` `CNT_TEL1_AREA` `CNT_TEL1` `CNT_TEL2_AREA` `CNT_TEL2` `CNT_FAX_AREA` `CNT_FAX` `CNT_EMAIL` `CNT_MEMO` |

三個 Caption 陷阱:

| 陷阱 | 內容 | 錨點 |
|---|---|---|
| **欄名與語意不符** | `BF_COUNTRY_X` 名字像「國別」,實際是**身份別**(`'00'` 自然人+法人 / `'01'` / `'02'`)。`OFDM040` 的錯誤訊息直接寫「已存在於身份別為'自然人+法人'中」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:83` |
| **同代號不同表** | 掃描索引裡的 `OFD061` 有兩份形狀:本片的 `OFD061` 是 TA 公司主檔(30 欄,PK `TA_CD`);索引另一份 `OFD061` 是別的模組的結果集(26 欄,`FUND_ID` / `NAV_B` / `TOT_UNIT` 那組結帳彙總)。**查資料表時不要只看代號** | 本片形狀 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM061Model.xsd`;另一份見 `atlas_scan.py --screen OFDM061` 輸出的欄位表 |
| **整批留空** | `OFD039A` 有 12 個業務欄、`OFD040A` 有 9 個、`OFD045` 全部 6 個沒有 Caption。這幾支畫面的欄位中文名**只能從 Designer 的 Label 或選單表回填**,本文不猜 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM039Model.xsd`、`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM045Model.xsd` |

### 2.6 狀態碼

本片沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`),本片的 PO **一次都沒有**跟 `EVAStatusCode` 的常數做比較,也**沒有任何一段寫死 `STATUS` 字面值的 SQL**——這點跟 `ofd7.md §2` 記的三個批次匯入不一樣,本片乾淨。

真正被當狀態用的是三個業務欄:

| 欄 | 值域 | 誰在用 | 錨點 |
|---|---|---|---|
| `AGENT_VALID_CODE` | `'Y'` 有效 / `'N'` 無效 | `OFDM068` 存檔時據此 UPDATE `OFD070A`;寫到境外 `OFD070` 時反轉成 `'0'`/`'1'` | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:123-134`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:341`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:265` |
| `EFFECT_YN` | `'Y'` / `'N'`(Caption「有效銀行帳號 Y/N」) | `OFDM030`,程式端**沒有任何檢核或連動**,純欄位 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:128` |
| `BANK_TYPE`(扣款行作業別) | Caption 直接寫明 `0:集保款項收付銀行;1:全國繳稅費銀行` | `OFDM030` 的唯一業務檢核:`BANK_TYPE == "0"` 時「匯款帳號對應碼」必填 | Caption 在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM030Model.xsd`;檢核在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:173-179` |

**假設**:`EFFECT_YN = 'N'` 的銀行帳戶不應再被下游取用。**缺:消費端**——`GET_REMIT_ACC_NO` 撈 `OFD030` 時**沒有過濾 `EFFECT_YN`**(`DB/Function/GET_REMIT_ACC_NO.SQL:30-33` 的 WHERE 只有 `BANK_HQ = XREMIT_BANK_CD`),所以停用一個帳戶並不會讓虛擬帳號停止產生。見附錄 E.12。

## 3. 畫面清冊

```text
[圖] OFD4 十八支畫面依 PO 基底與編譯狀態的分群，以及兩支執行期必 NRE 的畫面
圖中文字:① 現行單筆型 BaseEVADaoPO：14 支，走 xEVAEventArgs / xTableHelper / OFDM030 OFDM034 OFDM035 / 在 csproj 可執行 / OFDM036 OFDM039 OFDM040 / 在 csproj 可執行 / OFDM054 OFDM055 OFDM061 / 在 csproj 可執行 / OFDM062 OFDM064 / 在 csproj / OFDM065 OFDM066 OFDM068 / 在 csproj 可執行 / ② 現行多筆型 BaseMultiRowEVADaoPO：2 支，沒有明細表靠 MasterPKey 分群 / OFDM038 / OFD038A 分群鍵 FUND_GRPCD / OFDM041 / OFD041A 分群鍵 ACCOUNT_COPY / ROW_NUMBER OVER PARTITION / WHERE NUM = 1 抓群首 / 在 csproj / 可執行 / ③ 舊世代 MultiRowEVAPO / BasicEVAPO：2 支，在 csproj 但執行期必 NRE / OFDM045 / MultiRowEVAPO / OFDM046 / BasicEVAPO / dbTA 宣告即 null / 建構子賦值整段被註解 / Add / Select 第一行 / dbTA.CreateConnection() / 子類沒覆寫任何一支 / 只掛三個組 SQL 的事件 / _Ctl 不繼承 BaseController / 直接 new PO 再呼叫 / T-SQL 痕跡 / ISNULL / [表名] / CONVERT / 結論：未遷移 / 修 dbTA 也還是跑不動 / ④ 自行覆寫 Add / Update：1 支，四眼狀態自己寫 / OFDM068 / override Add / Update / 雙交易 dbProduct + dbPTPF / 手動 SetAddStatusToDo / 明細影響筆數檢核 / 三段全被註解 / 連動 OFD070A / OFD070 / = 配 % 非券商不中 / ⑤ csproj 核對：18 支 x 6 層 = 108 個檔，逐一確認 / UI.OFD.csproj / 18 主 Form + 4 子對話框 / FormProxy / Control / PO / 各 18 支 全在 / DataEntity.OFD4 / UIEntity.OFD4 / 各 18 份 xsd 全在 / 缺漏 0 / 本片無未編譯死畫面
```

*圖:圖 3 PO 基底分群。橘框=可執行的維護入口;橘虛框=風險或死的;白框=機制;黑框=框架無原始碼。最重要的是 ③ 與 ⑤ 放在一起看：18 支全部在 csproj、全部編得起來，但 OFDM045 與 OFDM046 連按查詢都會 NullReferenceException——靜態檢查看不出來。*

### 3.1 維護 M

18 支六層檔案全部存在,**而且 18 支的六層全部都有進各自的 csproj**——沒有 `ofd7.md §2` 那種「檔案在但不在 csproj」的整組未編譯情形。但**編得起來不等於跑得動**:`PO 基底` 欄標紅的兩支執行期第一行就 NRE(§4.2)。

「PO 基底」與「在 csproj」兩欄的判讀:

- `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` = 現行世代,`dbProduct` 由框架注入,正常。

- ⛔ `BasicEVAPO` / `MultiRowEVAPO` = 舊世代,`dbTA` 恆為 `null`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:18`),建構子賦值那四行整段被註解(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:164-172`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:171-174`),**繼承而不覆寫 `Add`/`Update`/`Delete`/`Select` 就必 NRE**。

- 「在 csproj」逐支比對六個專案檔:`UI.OFD.csproj` / `FormProxy.OFD.csproj` / `Control.OFD.csproj` / `PO.OFD.csproj` / `DataEntity.OFD4.csproj` / `UIEntity.OFD4.csproj`。

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | PO 基底 | 在 csproj | 子對話框 | 特別之處 |
|---|---|---|---|---|---|---|---|---|
| `OFDM030` | 集保申購款入款銀行設定 | 齊 | `OFD030` | — | `BaseEVADaoPO` | 六層齊 | — | 修改路徑 `e.Cancel` 後沒 `return`(附錄 E.9) |
| `OFDM034` | 產壽險公司基本資料 | 齊 | `OFD034A` | — | `BaseEVADaoPO` | 六層齊 | — | 1192 行裡 1045 行是被註解的舊實作;`AfterUpdate` 跨寫兩張別模組的表 |
| `OFDM035` | 郵匯費基本資料(全行通用 `BANK_HQ='ALL'`) | 齊 | `OFD035A` | `OFD036A` | `BaseEVADaoPO` | 六層齊 | — | 與 `OFDM036` 同表;整條六層是 Big5(附錄 E.8) |
| `OFDM036` | 贖回匯費設定作業(個別銀行 `BANK_HQ<>'ALL'`) | 齊 | `OFD035A` | `OFD036A` | `BaseEVADaoPO` | 六層齊 | — | 與 `OFDM035` 同表;多一支 `Get_POST_FEE` 去抓 `'ALL'` 列的郵費 |
| `OFDM038` | 基金群組設定 | 齊 | `OFD038A` | — | `BaseMultiRowEVADaoPO` | 六層齊 | — | `ROW_NUMBER() … WHERE NUM=1` 抓群首 |
| `OFDM039` | 缺件代碼檔 | 齊 | `OFD039A` | — | `BaseEVADaoPO` | 六層齊 | — | PO 1007 行裡 943 行是註解掉的舊實作;檔尾有 `}//end namespace Adapterusing System;` 這種合併殘留 |
| `OFDM040` | 通知書寄發設定 | 齊 | `OFD040A` | — | `BaseEVADaoPO` | 六層齊 | — | 唯一有「互斥鍵」檢核的一支,而且有三個洞(附錄 E.4) |
| `OFDM041` | 帳務說明片語範本 | 齊 | `OFD041A` | — | `BaseMultiRowEVADaoPO` | 六層齊 | — | vdb 名 `OFD041` 與另一張真表同名(附錄 E.6) |
| `OFDM045` | KYC 問項維護 | 齊 | `OFD045` | — | ⛔ `MultiRowEVAPO` | 六層齊 | `OFDM045p0` 排序 | **執行期必 NRE**;`_Ctl` 不繼承 `BaseController`;`KYC_ITEM` 寫死 `'A'`~`'S'` 19 項 |
| `OFDM046` | 作業文件範本(可掛附件) | 齊 | `OFD046` | `OFD047` | ⛔ `BasicEVAPO` | 六層齊 | — | **執行期必 NRE**;`_Ctl` 不繼承 `BaseController`;SQL 是 T-SQL 語法(`ISNULL` / `[表名]` / `CONVERT(NVARCHAR,…,111)`) |
| `OFDM054` | 受益人應繳交文件代碼 | 齊 | `OFD054A` | — | `BaseEVADaoPO` | 六層齊 | — | UI 只有 91 行,零業務檢核;PO 仍留著一份 T-SQL 風的 `AddParam` |
| `OFDM055` | 資產證明內容代碼 | 齊 | `OFD055A` | — | `BaseEVADaoPO` | 六層齊 | — | PO 只有 49 行、零事件,全靠框架 |
| `OFDM061` | TA 公司基本資料 | 齊 | `OFD061` | — | `BaseEVADaoPO` | 六層齊 | — | PO 有一行 `dbProduct = dbProduct;` 自我指派空操作 |
| `OFDM062` | 基金公司基本資料 | 齊 | `OFD062` | `OFD063` | `BaseEVADaoPO` | 六層齊 | `OFDM062p0` 聯絡人編輯 | 明細 DataTable 的 PK 只有 `FH_CD` 一欄(附錄 E.5);集保編號重複檢核 DB 出錯時不擋 |
| `OFDM064` | 基金公司申購匯款帳戶(境外) | 齊 | `OFD064` | — | `BaseEVADaoPO` | 六層齊 | — | 只檢 SWIFT 長度,無唯一性檢核 |
| `OFDM065` | 基金公司銷售國別 | 齊 | `OFD065` | — | `BaseEVADaoPO` | 六層齊 | — | 純關聯表,「修改」直接擋掉要求先刪再建 |
| `OFDM066` | 總代理公司基本資料 | 齊 | `OFD066` | `OFD067` | `BaseEVADaoPO` | 六層齊 | `OFDM066p0` 聯絡人編輯 | 與 `OFDM062` 同型;集保編號重複檢核**四層外殼全在、沒有呼叫端**(附錄 E.3) |
| `OFDM068` | 銷售機構基本資料 | 齊 | `OFD068A` | `OFD069A` | `BaseEVADaoPO`(自行覆寫 `Add` / `Update`) | 六層齊 | `OFDM068p0` 聯絡人編輯 | 本片最大(UI 1018 行 + PO 787 行);連動 `OFD070A` / `OFD070`;`LIKE` 樣式餵給 `=`(附錄 E.2) |

> ⚠ **四個子對話框(`OFDM045p0` `OFDM062p0` `OFDM066p0` `OFDM068p0`)不在掃描索引裡**,因為它們沒有自己的六層,只是 UI 專案裡的 Form。四個都有進 `UI.OFD.csproj`。

### 3.2 csproj 逐層核對結果

18 支 × 6 層 = 108 個檔案,逐一在對應 csproj 搜過:

| 專案檔 | 涵蓋 | 缺漏 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/UI.OFD.csproj` | 18 支主 Form + 4 支子對話框 | 無 |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/FormProxy.OFD.csproj` | 18 支 `_Pxy` | 無 |
| `Dev/ATLAS.OFD/Source/Control/Control.OFD/Control.OFD.csproj` | 18 支 `_Ctl` | 無 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj` | 18 支 `_PO` | 無 |
| `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/DataEntity.OFD4.csproj` | 18 份 `*Model.xsd` + Designer + VDB | 無 |
| `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD4/UIEntity.OFD4.csproj` | 18 份 `*View.xsd` + Designer + VDB | 無 |

**結論:本片沒有「檔案存在但不在 csproj」的死畫面。** `ofd7.md §2` 在 OFD7 找到的那種情形(`OFDM199A_Pxy.cs` 檔案在、csproj 裡沒有),在 OFD4 一例都沒有。本片的死法是另一種——**編進去了,但執行期第一行就 NRE**(§4.2)。

### 3.3 `_Ctl` 的 XML 註解有三支是複製貼上殘留

各層的中文名主要從 `_Ctl` 的 `/// <summary>` 抽,但有三支對不上實際的表:

| 畫面 | `_Ctl` 註解說 | 表實際在管 | 判定 | 錨點 |
|---|---|---|---|---|
| `OFDM041` | 「基金種類代碼檔(TDCC)」 | `OFD041A` 的欄位是 `ACCOUNT_COPY`(範本名稱)/ `ACCOUNT_MEMO`(範本內容)/ `DATA_SEQ`(流水號),與基金種類無關 | **註解錯**,本文採欄位 Caption:帳務說明片語範本 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM041_Ctl.cs`;欄位見 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM041Model.xsd` |
| `OFDM045` | 「分公司代碼檔」 | `OFD045` 的欄位是 `KYC_CODE` / `KYC_ITEM` / `KYC_DESCRP` / `KYC_ORDER`,而且 SQL 依 `BF_COUNTRY_X` 去 `CTL014` 取 `'334'`/`'335'` 兩套問項 | **註解錯**,本文採欄位:KYC 問項維護 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM045_Ctl.cs:29`;SQL 在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:51-54` |
| 全片 14 支 | 「取得維護頁**境內基金申購**資料」 | 這 14 支沒有一支跟境內基金申購有關 | **模板殘留**,整串是同一句被複製 14 次 | 例:`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM035_Ctl.cs`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM045_Ctl.cs:68` |

對得上的有:`OFDM030`「集保申購款入款銀行設定」、`OFDM034`「產壽險公司基本資料」、`OFDM035`「郵匯費基本資料」、`OFDM036`「贖回匯費設定作業」、`OFDM039`「缺件代碼檔」、`OFDM040`「通知書基本資料」、`OFDM054`「受益人應繳交文件代碼資料」、`OFDM055`「資產證明內容」、`OFDM061`「TA 基本資料」。`OFDM062` / `OFDM064` / `OFDM065` / `OFDM066` / `OFDM068` 的 `_Ctl` **一句業務註解都沒有**,只有「執行 PO 委派」這種框架註解,名稱由表欄位推測。

### 3.4 查詢 I

**本片無 I 畫面。**原因:`DataEntity.OFD4` 底下 18 份 Model 全部是 `OFDM*` 命名的 M 型;OFD 的查詢畫面集中在 `Dev/ATLAS.OFD.Query` 專案,不屬於本片。

### 3.5 批次 B

**本片無 B 畫面。**原因:18 支的 UI 基底全部是 `xMaintainForm`,沒有一支是 `xOneStepProcessForm` 型;`OFDM046` 的檔案上傳 / 下載是 M 畫面上的按鈕,不是批次畫面。

### 3.6 報表 R

**本片無 R 畫面。**原因:`DataEntity.OFD4` 底下沒有任何 `*R*Model.xsd`,`Dev/ATLAS.OFD.Report` 也沒有對應這 18 支的報表。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFDM035 與 OFDM036 吃同一組表的切分方式、單向郵費依賴、卡控差異與只改一邊的三個坑
圖中文字:① 同一對表，兩支畫面，靠 BANK_HQ 切成互斥兩半 / OFDM035 全行通用 / 存檔寫死 BANK_HQ='ALL' / OFD035A + OFD036A / 主檔 + 匯費級距明細 / OFDM036 個別銀行 / 存檔取 custBANK_HQ / 沒有第三支碰這兩張 / 全庫確認 / ② 郵寄費的單向依賴：OFDM036 存檔前先去讀 OFDM035 維護的那一列 / OFDM036 按存檔 / 呼叫 Get_POST_FEE / 撈 BANK_HQ='ALL' 同幣別 / 有參數化 :CRNCY_CD / 撈不到就抓 TWD 那列 / 無提示 fallback / TWD 也沒有就填 0 / 郵費變免費 無提示 / ③ 卡控：五條共用，兩條只有一邊有 / 明細 0 筆 / 迄額最大值 / 兩支都有 阻擋 / REMIT_MAX <= 1 不可加列 / 兩支都有 阻擋 / 改上限自動刪列 / 兩支都有 過濾無提示 / 進修改頁不可刪 / 只有 OFDM035 / 郵費 fallback / 只有 OFDM036 過濾無提示 / 銀行代碼查詢條件 / 只有 OFDM036 / 重複新增檢核 / 兩支都沒有 靠 DB PK / 主檔 WHERE 切分 / 另一半資料看不到 無提示 / ④ 只改一邊留下的三個坑 / OFDM036 補了 row.STATUS / 註解「Status 也要給」 / OFDM035 沒補 / 同一段迴圈 少一行 / OFDM036 SetMasterToDetail / 在 e.Cancel 之後照跑 / handler 拼成 Modity / 只有 OFDM036 / ⑤ 誰先誰後：編碼與相似度是證據 / OFDM035 四層都是 Big5 / cp950 / OFDM036 四層都是 UTF-8 / utf-8-sig / 代號代換後相似度 / Ctl 80.6% / PO 56.1% / 推論：036 由 035 複製 / 改動集中在 PO
```

*圖:圖 4 同表雙畫面（本篇核心）。橘框=維護入口;白框=正常機制;橘虛框=風險或無提示的行為。要記住兩件事:① 兩支的資料互斥不重疊，不是境內外也不是新增與維護;② OFDM036 的郵寄費是從 OFDM035 那一列複製過來的，改 OFDM035 會影響所有銀行。*

本章順序不照代號排,照「要花多少時間讀」排: **先看同表雙畫面** §4.1 · **再看兩支執行期死掉的** §4.2 · **再看兩支主從結構的重頭戲** §4.3~§4.4 · **然後是跨表寫入的** §4.5 · **其餘依業務線分群帶過** §4.6~§4.9。

### 4.0 十八支共同的骨架

先把重複的部分講完,後面各節只寫差異。

| 環節 | 共同做法 | 錨點(以 `OFDM030` 為例) |
|---|---|---|
| UI 基底 | `xMaintainForm`(無原始碼,從呼叫端反推),`TabPages = 2`(查詢頁 + 維護頁) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:25`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:25` |
| 存檔前檢核 | `BeforeAddButtonClicked` / `BeforeModifyButtonClicked` → `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:111-136` |
| 主檔值下推 | `SetMasterToDetail()` 把畫面上半的鍵塞進每一列明細(只有六支有明細的畫面需要) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:92-120` |
| 四眼 | 16 支全走框架,PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個取數事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:45-47` |
| ToDo | `xTableHelper.AppendToDoString(<表名>, model)`,只在 `isToDoString` 為真時接上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:154-157` |
| 查詢條件 | 每支自己手寫 `if (model.Utility.Parameters.Rows.Contains("欄名"))` → **字串串接**成 `And 表.欄 = '值'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:138-151` |

**五件全片通用、值得先記住的事:**

1. **查詢條件一律字串串接,沒有一支用 bind variable。** 18 支裡有 12 支手寫了同一段「`Contains` → `Equal` 就 `= '值'`、`Like` 就 `Like '值%'`」的樣板,值直接串進 SQL。單引號會炸,也是注入面(附錄 E.7)。對照組:`OFDM036.Get_POST_FEE` 與 `OFDM062.IsFH_TSCD_CODExsits` 這種「後來才加的」方法反而**有**用 `:參數`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:211`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:280-281`)。

2. **`if (this.ValidateErrList.ErrorCount != 0) return;` 會截斷後面所有業務檢核。** 例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:48`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:59`。使用者只會先看到必填錯誤,修完再存才看到業務錯誤——要按兩次以上。

3. **「跟伺服端要答案」的檢核共五支,四支在 `catch` 時等於放行。** `OFDM040.CheckData`(回 `IsExit = false`)、`OFDM062.IsFH_TSCD_CODExsits`(回 `-1`,UI 只跳訊息不 `AddError`)、`OFDM068.CheckAgent`、`OFDM068.CheckDept`(都回 `AddResultRow(false, 0, "")`)四支是這樣(附錄 E.10)。唯一的例外是 `OFDM034.CheckData`——它的 UI 端看 `ReturnCode` 為 `false` 就擋住刪除,方向正確,只是訊息是空字串(§4.5.3)。

4. **六支有明細的畫面(`OFDM035` `OFDM036` `OFDM046` `OFDM062` `OFDM066` `OFDM068`)裡,只有三支在 `SetMasterToDetail` 補 `row.STATUS = MasterRow.STATUS`。** 補的是 `OFDM036`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:64`)、`OFDM062`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:117`)、`OFDM066`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:86`);沒補的是 `OFDM035`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:126-132`)。三處都留了一模一樣的註解「STATUS 也要給」,漏的那支連註解都沒有(附錄 E.11)。

5. **`_Pxy` 層純轉呼叫,零邏輯。** 18 支的 `_Pxy` 都是 `new XXX_Ctl()` 再呼叫同名方法,沒有任何判斷。要找邏輯不用翻 FormProxy。

### 4.1 `OFDM035` 與 `OFDM036` — 同一組表的兩支畫面(本片核心)

**先回答最容易誤會的問題:它們不是境內 / 境外,也不是新增 vs 維護,更沒有一支是死碼。兩支都活著,吃同一對表(`OFD035A` 主檔 + `OFD036A` 明細),靠 `BANK_HQ` 這個欄位的值把資料切成互斥的兩半:**

- **`OFDM035` 管「全行通用」那一半**:`BANK_HQ = 'ALL'` 的哨兵列。

- **`OFDM036` 管「個別銀行」那一半**:`BANK_HQ <> 'ALL'` 的真實銀行列。

#### 4.1.1 決定性證據

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `OFDM035_PO` 的主檔 SQL 硬寫 `WHERE BANK_HQ='ALL'`;明細 SQL 也硬寫 `AND BANK_HQ='ALL'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:122`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:176` |
| 2 | `OFDM036_PO` 的主檔 SQL 硬寫 `WHERE OFD035A.BANK_HQ <>'ALL'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:127` |
| 3 | `OFDM035` 存檔時把 `BANK_HQ` **寫死成 `"ALL"`**,畫面上根本沒有銀行選擇器 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:123` |
| 4 | `OFDM036` 存檔時 `BANK_HQ` 取自畫面上的銀行選擇器 `custBANK_HQ` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:137` |
| 5 | `OFDM036` 存檔前會**先去撈 `OFDM035` 維護的那一列**,把它的 `POST_FEE` 複製過來當自己的郵費 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:130-139`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:186-253` |
| 6 | `OFDM036` 的主檔多 `LEFT JOIN OFD019A` 取銀行簡稱 `BANK_HQ_SHNM`;`OFDM035` 不需要(它的 `BANK_HQ` 恆為 `'ALL'`,沒有對應的銀行主檔列) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:117`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:123-124` |

**所以業務語意是**(**推測**,依據上面六條):`OFDM035` 設定「不分銀行、一律適用」的預設贖回匯費級距與支票郵寄費;`OFDM036` 針對特定往來銀行覆寫匯費級距,**但郵寄費不給改,強制沿用 `OFDM035` 的值**(§4.1.4)。

#### 4.1.2 代號代換後的逐行相似度

把 `OFDM035` 側的原始碼整份把 `035` 換成 `036` 之後,與 `OFDM036` 側做逐行 diff(忽略空行):

| 層 | `OFDM035` 側非空行 | `OFDM036` 側非空行 | 相似度 |
|---|---|---|---|
| UI(`OFDM035.cs` vs `OFDM036.cs`) | 232 | 266 | **77.1 %** |
| Control(`OFDM035_Ctl.cs` vs `OFDM036_Ctl.cs`) | 594 | 609 | **80.6 %** |
| PO(`OFDM035_PO.cs` vs `OFDM036_PO.cs`) | 171 | 225 | **56.1 %** |
| FormProxy(`OFDM035_Pxy.cs` vs `OFDM036_Pxy.cs`) | 299 | 272 | **45.5 %** |

Control 層 80.6 % 而 PO 層只有 56.1 %,方向很清楚:**`OFDM036` 是從 `OFDM035` 複製出來的,改動集中在 PO(換 WHERE、加 join、加 `Get_POST_FEE`)與 FormProxy(加一支委派)。**

還有一條旁證:**`OFDM035` 整條六層是 Big5(`cp950`),`OFDM036` 整條六層是 UTF-8**。

| 檔 | `OFDM035` 側 | `OFDM036` 側 |
|---|---|---|
| UI | `cp950` | `utf-8-sig` |
| UI Designer | `cp950` | `utf-8-sig` |
| Control | `cp950` | `utf-8-sig` |
| PO | `cp950` | `utf-8-sig` |

同一個功能的兩支畫面編碼完全相反,只能是「不同年代寫的」。**假設**:`OFDM036` 是後來加的,`OFDM035` 是原版。**缺:版控歷史**(本次分析不讀 git log)。

#### 4.1.3 `Get_POST_FEE` — `OFDM036` 獨有的機制

`OFDM036_PO.Get_POST_FEE`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:186-253`)做三件事:

| 步驟 | 內容 | 錨點 |
|---|---|---|
| 1 | 用畫面上的幣別去撈 `OFD035A` 裡 `BANK_HQ='ALL'` 的那一列(**用 bind 參數 `:CRNCY_CD`,本片少數有參數化的地方**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:204-211` |
| 2 | 撈不到(該幣別沒設全行通用值)就**改抓 `CRNCY_CD = 'TWD'` 的那一列** 當 fallback | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:217-241` |
| 3 | UI 端把撈回來的 `POST_FEE` 寫進自己的主檔列;連 TWD 都撈不到就填 `0` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:139` |

**兩個要注意的地方:**

- **fallback 到 TWD 是無提示的。** 使用者在 USD 的銀行匯費設定頁存檔,拿到的郵寄費其實是台幣那一列的數字,畫面上不會說。歸類為**過濾(無提示)**。

- **撈不到就填 `0`。** `view.UIView.OFDM036.Rows.Count == 0 ? 0 : …`——郵寄費被當成免費存進去,同樣無提示。

- 第 2 步 fallback 的 SQL 把 `'TWD'` **字面量串進字串**,沒有沿用第 1 步的參數化寫法(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:233`)。

#### 4.1.4 逐項差異總表

| 面向 | `OFDM035`(全行通用) | `OFDM036`(個別銀行) | 評註 |
|---|---|---|---|
| 主檔 WHERE | `BANK_HQ='ALL'` | `BANK_HQ <>'ALL'` | 互斥,不重疊 |
| 明細 WHERE | 手寫 `AND BANK_HQ='ALL'` | **沒有** BANK_HQ 條件,整段交給 `xTableHelper.GetSelectString` 依 model 參數組 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:176` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:173` |
| 銀行欄位 | 畫面上沒有,存檔時寫死 `"ALL"` | 畫面上有 `custBANK_HQ` 選擇器,查詢頁也有 `custBANK_HQ_0` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:123` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:137`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:151` |
| 郵寄費 `POST_FEE` | **可輸入**(`unumPOST_FEE`) | **不可輸入**,從 `'ALL'` 列複製;UI 的 `unumPOST_FEE` 指派那行被註解掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:122` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:139`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:102` |
| 銀行簡稱 | 無 | `LEFT JOIN OFD019A` 取 `BANK_HQ_SHNM`,xsd 多這一欄(21 欄 vs 20 欄) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:117` |
| `SetMasterToDetail` | **沒有這支方法**,把三行迴圈寫在 `BeforeAddModify` 裡,而且**不設 `row.STATUS`** | 抽成獨立方法,而且多一行 `row.STATUS = MasterRow.STATUS;`(註解:「Status 也要給」) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:126-132` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:52-68` |
| `SetMasterToDetail` 呼叫位置 | 在 `else`(檢核通過)分支內 | 在 `if/else` **外面**——檢核失敗、`e.Cancel = true` 之後**照樣執行** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:142` |
| 存檔 handler 名稱 | `OFDM035_BeforeAddModifyButtonClicked` | `OFDM036_BeforeAddModityButtonClicked`(**`Modity` 拼錯**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:113` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:123` |
| 刪除鈕 | `ModifyDataLoad` 時 `ButtonDeleteEnable = false`——**進修改頁就不能刪** | 這一行**被移除**,個別銀行的設定可以刪 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:90` |
| 查詢條件 | 只有幣別 | 幣別 + 銀行代碼(銀行用 `Equal`,註解寫明「將查詢條件 Like 改為 Equal」) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:140-141` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:147-156` |
| 查詢結果 Grid 格式化 | 無 | 多一支 `ugrdResult_InitializeLayout` 把 `REMIT_MAX` / `POST_FEE` 設成千分位靠右,並把 `POST_FEE` 從欄位挑選器隱藏 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:272-292` |
| 明細「終止金額最大值」邊界 | `LevelGridUtility(…, 0m, Math.Max(2, decMax))` | `LevelGridUtility(…, 0, Math.Max(2, decMax))`(int 字面量而非 decimal) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:235` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:253` |
| 原始檔編碼 | Big5(`cp950`)四層 | UTF-8 四層 | 見 §4.1.2 |
| PO 解構子 | 空的 | 會 `-=` 解除三個事件訂閱 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:37-42` |

#### 4.1.5 兩支的卡控總表

檢核內容幾乎一樣,差別在誰有、在哪個時點。

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:40-42`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:38-40` |
| 存檔前 | 明細 `MAX(REMIT_AMT2)` ≠ 主檔 `REMIT_MAX` | 「終止金額最大值 必須等於 單次匯款最高金額」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:57-58`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:44-45` |
| 新增明細列前 | `REMIT_MAX <= 1` | 「單次匯款最高金額 必須大於 1,才可新增明細資料」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:181-182`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:196-197` |
| 改 `REMIT_MAX` 後 | 新上限 ≤ 1 | Grid **全列刪光** | 過濾(無提示) | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:236-238`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:254-256` |
| 改 `REMIT_MAX` 後 | 明細 `REMIT_AMT1 >= 新上限` | 那幾列**直接 `row.Delete()`** | 過濾(無提示) | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:242-244` |
| 刪明細列時 | 交給 `LevelGridUtility.LevelGrid_BeforeRowsDeleted` 判(無原始碼,從呼叫端反推) | 由 helper 決定 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:200-203`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:253-219` |
| 主檔取數 | `BANK_HQ='ALL'`(`OFDM035`)/ `BANK_HQ<>'ALL'`(`OFDM036`) | 另一半的資料不出現 | **過濾(無提示)** | 各自 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:122`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:127` |
| 存檔前(只有 `OFDM036`) | 該幣別沒有 `'ALL'` 列 | 郵寄費靜默 fallback 到 TWD;TWD 也沒有就填 `0` | **過濾(無提示)** | 只有 `OFDM036` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:217`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:139` |

**跨表更新**:兩支都只寫 `OFD035A` + `OFD036A`,不動別的表。`OFDM036` 會**讀** `OFD019A`(銀行簡稱)與 `FSK003`(幣別名)。

#### 4.1.6 這一對留下的三個坑

| 坑 | 內容 | 嚴重度 |
|---|---|---|
| **`OFDM035` 的明細不設 `STATUS`** | `OFD036A` 是走四眼的表,主檔的 `STATUS` 沒下推到明細,明細列的四眼狀態靠框架自己補。`OFDM036` 特地補了這一行並加註解——代表這件事被發現過,**但只修了一邊** | 中(附錄 E.11) |
| **`OFDM036` 的 `SetMasterToDetail()` 在 `e.Cancel` 之後照跑** | 檢核失敗時 `MasterRow.BANK_HQ` 還是舊值 / 空值,卻已經被塞進所有明細列。使用者修正欄位再按一次存檔才會被覆寫回來;若中途切頁就留下髒值 | 中(附錄 E.13) |
| **`OFDM036` 完全沒有「該銀行已存在設定」的檢核** | `OFD035A` 的 PK 是 `BANK_HQ` + `CRNCY_CD`,重複新增只會在 DB 端撞 PK,錯誤訊息是框架的泛用訊息 | 低 |

### 4.2 `OFDM045` 與 `OFDM046` — 兩支編得起來但跑不動的畫面

這兩支是本片最嚴重的問題,而且**任何靜態檢查都看不出來**:六層檔案齊全、全部在 csproj、編譯無誤。

#### 4.2.1 為什麼一定 NRE

已查證事實(`architecture.md §3.1.1`):

| 步驟 | 事實 | 錨點 |
|---|---|---|
| 1 | `BasicEVAPO` 的 `dbTA` 宣告即 `= null`;`MultiRowEVAPO` 一樣 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:18` |
| 2 | 兩個基底的建構子裡,真正建立連線的那四行**整段被註解** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:164-172`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:171-174` |
| 3 | 基底的 `Add()` 第一行就 `dbTA.CreateConnection()` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:187` |
| 4 | **`Select()` / `GetMaintainData()` / `Delete()` / `GetToDoData()` 也一樣** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:795-797`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:717-728`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:772-783`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:607-613`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1300-1302` |
| 5 | `OFDM045_PO` / `OFDM046_PO` **沒有覆寫任何一個**,只掛了 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個組 SQL 的事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:6-17`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:14-25` |
| 6 | 兩支的 `_Ctl` 直接 `new XXX_PO()` 再呼叫 `Add` / `Update` / `Delete` / `Select` / `GetMaintainData` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM045_Ctl.cs:32-77`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM046_Ctl.cs:37-106` |

**`ofd8.md` 找到 7 支、`ofdb.md` 找到 4 支同型缺陷,本片再加 2 支。** 但本片這兩支比那些更嚴重:因為**連 `Select()` 都炸**,所以不是「查得到但存不了」,是**畫面按查詢就掛**。

> ⚠ 例外情形值得記一筆:如果框架在別的地方(例如 `Basic_PO` 的某個 initialize hook)有後補 `dbTA`,這兩支就會活。本文查過兩個基底的建構子與欄位宣告,**沒有找到任何賦值點**;`Basic_PO` 的內容無原始碼可讀。所以精確的說法是「**在可讀範圍內 `dbTA` 永遠是 null**」,標為**假設**待實機驗證。

#### 4.2.2 舊世代的其他佐證

這兩支不只 PO 基底舊,整條鏈都是上一個世代的痕跡:

| 佐證 | `OFDM045` | `OFDM046` | 對照組(其餘 16 支) |
|---|---|---|---|
| `_Ctl` 是否繼承 `BaseController` | **否**(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM045_Ctl.cs:8`) | **否**(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM046_Ctl.cs:11`) | 全部都是 `: BaseController` |
| PO 有沒有 `[PODbType(DbServerType.Oracle)]` | **沒有** | **沒有** | 全部都有 |
| 事件參數型別 | `PrepareSQLEventArgs` | `PrepareSQLEventArgs` | `xEVAEventArgs` |
| Helper | `EVAStringHelper` / `TableHelper` | `EVAStringHelper` / `TableHelper` | `xEVAStringHelper` / `xTableHelper` |
| xsd 四眼欄位大小寫 | 小寫(`Status` `CreateID` …) | 小寫 | 大寫 |
| **T-SQL 痕跡** | `[OFD045]` 中括號表名、`ROW_NUMBER() OVER (…) ,*`、`CASE … WHEN … THEN … ELSE … END` | `ISNULL(MAX(DATA_SEQ),0)`、`[OFD046]` 中括號、`CONVERT(NVARCHAR, …, 111)`、`@` 風格的思路 | Oracle 的 `NVL` / `:參數` / `SYSDATE` / `dual` |

T-SQL 痕跡的錨點:

| 痕跡 | 錨點 |
|---|---|
| `[OFD045]` 中括號表名(Oracle 不吃) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:72-79` |
| `ISNULL(MAX(DATA_SEQ),0)`(Oracle 是 `NVL`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:46` |
| `[OFD046]` 中括號表名 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:149` |
| `CONVERT(NVARCHAR, 欄 ,111)`(Oracle 是 `TO_CHAR`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:230` |

**結論:這兩支是 MSSQL 時代寫的,Oracle 遷移時沒有跟著遷。** 就算 `dbTA` 的問題被修好,那些 T-SQL 語法在 Oracle 上仍然跑不起來——`[OFD045]` 這種中括號 Oracle 直接語法錯誤。

#### 4.2.3 `OFDM045`(KYC 問項)還有什麼邏輯值得記

雖然跑不動,程式邏輯還是要記下來,將來要修才有依據。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 分群 | `ROW_NUMBER() OVER (PARTITION BY BF_COUNTRY_X, KYC_CODE ORDER BY CreateDate, UpdateDate, EntryDate, KYC_ORDER)` 取 `NUM = 1` 當群首 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:45-55` |
| 問項名稱來源 | `LEFT JOIN CTL014 ON KYC_CODE = TextValue AND SourceType = (CASE BF_COUNTRY_X WHEN '01' THEN '334' ELSE '335' END)` — **身份別決定去哪一組代碼字典查** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:51-54` |
| `KYC_ITEM` 自動編號 | 迴圈 `for (int i = 65; i < 84; i++)` 找第一個沒用過的 ASCII 字元 → `'A'` ~ `'S'`,共 19 個 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:175-183` |
| 對應的列數上限檢核 | `Rows.Count > 19` → 「項目說明 最多19項說明」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:385-388` |
| 排序子畫面 | `DoExp1()` 開 `OFDM045p0`;開之前檢查每列的 `BF_COUNTRY_X` / `KYC_CODE` 都不為空,否則跳「必須儲存資料後才可排序」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:403-438` |
| 排序子畫面的警示 | 「若確定更改順序,請回主畫面按修改鈕,以完成修改。」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045p0.cs:40` |

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料至少要輸入一筆」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:197-200` |
| 存檔前 | 列數 > 19 | 「項目說明 最多19項說明」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:385-388` |
| 存檔前 | 任一列 `KYC_DESCRP` 為空 | 「項目說明第 N 列不得空值,請'刪除'或'填入'此筆資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:392-398` |
| 按排序鈕 | 任一列 `BF_COUNTRY_X` 或 `KYC_CODE` 為空 | 「必須儲存資料後才可排序」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:411-414`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:437` |
| 存檔時(隱含) | 19 個字母用完 | `KYC_ITEM` **留空字串**,不擋不提示,直接送去撞 PK | **無提示** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:175-185` |
| 主檔取數 | `NUM = 1` | 群內非首列不出現在上半 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:55` |

#### 4.2.4 `OFDM046`(作業文件範本)還有什麼邏輯值得記

| 面向 | 內容 | 錨點 |
|---|---|---|
| 流水號 | `BeforeAdd` 用 `SELECT ISNULL(MAX(DATA_SEQ),0) FROM OFD046` + 1 當新序號,再回填主檔與所有明細列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:38-73` |
| 流水號的例外處理 | 整段包在 `try`,`catch` 只 `HandleBusinessException(ex)` **然後繼續往下走**——`DataSeq` 留在 `0`,主檔與明細都被塞 `0` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:62-66` |
| 附件上傳 | `openFileDialog1` 允許多選(`FileNames`),但程式**只取 `sFileNames[0]`**,其餘靜默丟棄 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:92-103` |
| 附件內容 | `File.ReadAllBytes` 整檔讀進記憶體再存 `OFD047.ATTACHFILE`(BLOB),**沒有大小上限檢查** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:117` |
| 附件下載 | Grid 雙擊 → 選資料夾 → `File.WriteAllBytes`,**同名檔直接覆寫,不問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:123-132` |
| 明細查詢 SQL | `BuildDetailSQLString` 只有 `if (strTableName == "OFD047")` 這一支,若傳進別的表名 `strSQL` 起手是空字串,最後組出 `… FROM 表名 WHERE 1=1`(欄位清單整段缺) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:173-192` |
| 查詢條件組法 | 自己寫了一支 `AddParam`,**值用字串串接**且 `Equal` 時自動包單引號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:201-237` |

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前(新增 / 修改都跑) | 附件列數為 0 | 「匯入檔案至少一個」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:64-73` |
| 加附件時 | 同一 `DATA_SEQ` + `FILENAME` 已存在 | 「檔案重覆」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:105-116` |
| 加附件時 | 一次選了多個檔 | 只加第一個 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:92-103` |
| 取流水號時 | SQL 出錯 | `DATA_SEQ` 留 `0`,繼續存檔 | **記錄不擋** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:62-66` |

> ⚠ 「加附件時的重複檢核」有一個前提:`ActionMode == Add` 時 `row.DATA_SEQ` 被填 `0`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:95-98`),而真正的序號要到伺服端 `BeforeAdd` 才算出來。所以**新增模式下的重複判斷是拿 `0` 去比**,只能擋住同一次編輯裡的同名檔,擋不了跨筆重複。

### 4.3 `OFDM068` — 銷售機構基本資料(本片最大的一支)

UI 1018 行 + PO 787 行,是唯一**自己覆寫 `Add` / `Update`** 的畫面,也是唯一**跨表連動**的畫面。

#### 4.3.1 主從結構與取數

| 項 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD068A` → vdb `OFDM068_Master`,48 欄,PK `AGENT_ID` + `AGENT_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:38` |
| 明細 | `OFD069A` → vdb `OFDM068_Detail`(聯絡人),29 欄,PK 三欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:39` |
| 主檔 SQL | **整段交給框架** `xTableHelper.GetSelectString`,沒有手寫欄位清單,也沒有 join | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:118` |
| 明細 SQL | 手寫 15 欄 + 四眼欄,條件用字串串接 `AGENT_ID` / `AGENT_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:152-203` |
| 子對話框 | `OFDM068p0` 聯絡人編輯,檢核 EMAIL 格式 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068p0.cs:60` |

#### 4.3.2 `Add` 覆寫(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:285-416`)

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 開兩個交易:`dbProduct`(業務庫)與 `dbPTPF`(平台庫) | `:295-296` |
| 2 | `IsExistByData` 判重複,重複就 `throw new Exception("此筆資料已存在,無法新增,請檢查")` | `:300-301` |
| 3 | `xEVAUtility.SetAddStatusToDo` 寫待辦;失敗就 `throw` | `:305-306` |
| 4 | 主檔 INSERT;`i <= 0` 就 `throw new Exception("新增OFD068A失敗")` | `:309-319` |
| 5 | 明細逐列 INSERT,`i +=` 累加 | `:325-333` |
| 6 | 若 `AGENT_VALID_CODE` 是無效 → UPDATE `OFD070A` 設無效 + 迄日;若是有效 → UPDATE `OFD070A` 設有效 + 迄日清空 | `:341-381` |
| 7 | `i > 0` 就雙 commit,否則雙 rollback | `:385-400` |

**兩個問題:**

- **步驟 5 的 `i +=` 讓步驟 7 的判斷失去意義。** 主檔成功時 `i` 已經 ≥ 1,之後明細寫 0 筆也不會讓 `i` 掉回 0,所以「明細一列都沒寫進去」仍然會 commit 並回「新增成功」。

- **步驟 6 的兩個分支 SQL 一字不差,只差參數值。** 92 行程式碼可以用一個三元運算子解決;更重要的是這兩段 UPDATE **不檢查影響筆數**,銷售機構在 `OFD070A` 沒有對應列時靜默通過。

#### 4.3.3 `Update` 覆寫(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:418-578`)

比 `Add` 多一步:先呼叫 `UpdateAGENT_VALID_CODE`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:460`),再改主檔、再逐列處理明細的 D / A / U。

`UpdateAGENT_VALID_CODE`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:218-279`)的註解寫得很清楚:

> 銷售機構有效碼設定為"無效",則更新銷售機構承銷基金設定檔[OFD070]中該銷售機構為無效比對的 rule:(目前只有更新到總行,其相關的分支應一併更新)

**它想做的「連分支一起更新」沒有成功,而且把原本能做的也弄壞了:**

```
dbProduct.AddInParameter(cmd, "AGENT_CODE", OracleDbType.Varchar2,
                         AgentCode + (AgentID == "2" ? "" : "%"));
```

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:239`(境內 `OFD070A`)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:264`(境外 `OFD070`)。

而 SQL 的條件是 **`=` 不是 `LIKE`**:

```
WHERE OFD070A.AGENT_ID = :AGENT_ID
  AND OFD070A.AGENT_CODE = :AGENT_CODE
```

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:232-233`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:257-258`。

| `AGENT_ID` | 傳進去的值 | `=` 比對結果 |
|---|---|---|
| `'2'`(券商) | `AgentCode`(原值) | 正常,總行那一列會被更新 |
| 其他(`'1'` 銀行、`'5'` 產壽險 …) | `AgentCode + "%"` | **`AGENT_CODE = 'A123%'` 永遠找不到任何列**,`OFD070A` 與 `OFD070` 完全不會被更新 |

也就是說:**除了券商以外的銷售機構,改成「無效」時,承銷基金設定檔不會跟著失效。** 這是本片最會咬人的一條(附錄 E.2)。

**同一支方法還有第二個問題**:`catch` 裡第一行就 `tran.Rollback()`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:276`),然後**不重拋**。呼叫端 `Update` 完全不知道出過事,繼續往下改主檔、改明細,最後 `tran.Commit()`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:553`)——對一個已經 rollback 的交易物件 commit。

**第三個問題**:`Update` 的明細段裡,三段「影響筆數不對就丟例外」**全部被註解掉**:

| 段 | 被註解的檢核 | 錨點 |
|---|---|---|
| 刪除明細 | `if (i == 0) throw new ApplicationException("修改明細資料(Action = D)時…")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:502-503` |
| 新增明細 | `if (i != 1) throw new ApplicationException("修改明細資料(Action = A)時…")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:524-525` |
| 修改明細 | `if (i != 1) throw new ApplicationException("修改明細資料(Action = U)時…")` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:544-545` |

主檔那一段的同型檢核**沒有**被註解(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:472-473`)。所以主檔改不到會擋,明細改不到不會。

**第四個問題**:新增明細時強制 `cmd.Parameters["DATAID"].Value = masterdataid;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:520`),把所有明細列的 `DATAID` 設成跟主檔一樣。`OFD069A` 的 PK 是 `AGENT_ID`+`AGENT_CODE`+`DATA_SEQ`,所以 DB 端不會撞;但同樣的寫法若套到 `OFD067`(PK 含 `DATAID`)就會出事——`OFDM066` 沒有這樣寫,算是躲過。

#### 4.3.4 `CheckAgent` — 刪除前查有沒有交易

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:580-656`。一口氣 `SELECT … FROM dual` 把六張交易表的筆數加總:`OFD232A` `OFD220A` `OFD259A` `OFD251A` `OFD253A` `RSP005A`。

| `AGENT_ID` | 條件寫法 | 錨點 |
|---|---|---|
| `'2'`(券商) | 第一張用 `AGENT_CODE LIKE :AGENT_CODE`,其餘五張用 `AGENT_CODE IN (SELECT 'K' \|\| STK_BRK FROM FSK005 WHERE 'K' \|\| STK_BRK_GRP = :AGENT_CODE OR 'K' \|\| STK_BRK = :AGENT_CODE)`——把券商總公司展開成所有分公司 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:596-604` |
| 其他 | 六張全部 `AGENT_CODE LIKE :AGENT_CODE`,參數值尾端補 `%` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:608-616`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:630` |

**這裡的 `LIKE` + `%` 是對的**,對照 §4.3.3 的 `=` + `%` 就知道那邊是漏改。同一支 PO、同一個 `AgentCode + (AgentID == "2" ? "" : "%")` 運算式,一處配 `LIKE`、一處配 `=`——**複製貼上時只搬了值,沒搬運算子**。

UI 端:

```
if (view.Util.Result[0].ReturnRowCount > 0) → AddError("此銷售機構已有交易資料,不可刪除!")
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:982-984`。

`CheckAgent` 的 `catch` 回 `AddResultRow(false, 0, "")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:646-651`)——**DB 出錯 = 查無交易 = 准刪**。

#### 4.3.5 `CheckDept` — 四個「指定部門」的唯一性

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:658-783`。四個欄位各一段幾乎一樣的 SQL:

| 欄 | 訊息 | `ReturnRowCount` 代碼 | 錨點 |
|---|---|---|---|
| `EC_DEPT_NFD` | 「已有境內基金指定網銀部門」 | 1 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:697-715` |
| `IVR_DEPT_NFD` | 「已有境內基金指定語音部門」 | 2 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:717-735` |
| `EC_DEPT_OFD` | 「已有境外基金指定網銀部門」 | 3 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:736-754` |
| `IVR_DEPT_OFD` | 「已有境外基金指定語音部門」 | 4 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:755-773` |

SQL 長這樣(四段都一樣,只換最後一個欄名):

```
select count(*) as count from OFD068A
where AGENT_CODE <> '<字串串接>'
AND AGENT_ID = '<字串串接>'
AND EC_DEPT_NFD = 'Y'
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:700-703`。

**三個問題:**

1. **`AGENT_CODE <> '…'` 的 Oracle 三值邏輯。** 新增一筆銷售機構時,`AGENT_CODE` 參數會是使用者剛輸入的值,正常;但若呼叫端傳進空字串,Oracle 的 `''` 等同 `NULL`,`AGENT_CODE <> NULL` 對每一列都是 UNKNOWN,`count(*)` 回 0,**檢核直接放行**。UI 端在 `CheckDept()` 裡是無條件塞 `custAGENT.Agent_Code`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:148`),而該欄位的必填檢核在更前面就 `return` 掉了(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:48-51`、`:59`),所以走不到——**目前不發作,但只要有人動 `DoValidate` 的順序就會發作**。

2. **字串串接。** `AGENT_CODE` 與 `AGENT_ID` 都直接串進 SQL,沒有參數化。

3. **UI 端 `CheckDept()` 有一個複製貼上的重複區塊:**

```
if (Convert.ToString(this.ucomIVR_DEPT_OFD.Value) == "Y")
{ view.Util.Parameters.AddParametersRow("IVR_DEPT_OFD", …); }
if (Convert.ToString(this.ucomIVR_DEPT_OFD.Value) == "Y")
{ view.Util.Parameters.AddParametersRow("IVR_DEPT_OFD", …); }
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:139-146`。同一個 `Name` 被 `AddParametersRow` 兩次;`Parameters` 這張 DataTable 有以 `Name` 為鍵的主鍵(程式各處都在用 `Rows.Find(欄名)` 與 `FindByName`,例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:209`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:211`),**重複新增會拋 `ConstraintException`**。也就是說「境外基金指定語音部門」勾 `'Y'` 時這支檢核會炸。**標假設**:`Parameters` 的主鍵是 `Name` 這件事由 `Rows.Find` / `FindByName` 的用法反推,`DataModelUtility` 無原始碼。

1. **四個結果全部 `AddError` 到同一個控件 `ucomEC_DEPT_NFD`**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:152-170`),四個 `if` 分支的內容一字不差。使用者勾到「境外語音」重複,畫面紅的卻是「境內網銀」那一格。

#### 4.3.6 `OFDM068` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `AGENT_ID` 為空 | 「銷售機構別 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:44-47` |
| 存檔前 | `AGENT_CODE` 為空 | 「銷售機構代碼 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:48-51` |
| 存檔前 | `AGENT_ID` 是 `'1'` 或 `'2'` | 「銷售機構付款行」轉為必填 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:54-55` |
| 存檔前 | 集保銷售機構代碼有值但長度 ≠ 5 | 「集保銷售機構代碼 長度應為5碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:61-64` |
| 存檔前 | `DECLARE_TSCD == 'Y'` 且公會核准日期空 | 「公會核准日期 必需輸入!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:66-71` |
| 存檔前 | `DECLARE_TSCD == 'Y'` 且公會核准文號空 | 「公會核准文號 必需輸入!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:73-76` |
| 存檔前 | 英文名稱 / 簡稱有非英數字 | 「只限輸入英文及數字!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:79-86` |
| 存檔前 | 必填有錯 | **`return`,後面 5 條業務檢核全部跳過** | 阻擋(但截斷) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:59` |
| 勾指定部門時 | 同一 `AGENT_ID` 下已有別的機構被指定 | 四句「已有…部門」 | 阻擋(但紅錯控件永遠是同一個) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:152-170` |
| 勾指定部門時 | 勾了「境外語音」 | 參數重複新增 → `ConstraintException` | **例外**(標假設) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:143-146` |
| 刪除前 | 六張交易表有資料 | 「此銷售機構已有交易資料,不可刪除!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:982-984` |
| 刪除前 | 查交易的 SQL 出錯 | 當成查無資料 | **記錄不擋** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:646-651` |
| 伺服端新增 | `IsExistByData` 命中 | `throw`「此筆資料已存在,無法新增,請檢查」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:300-301` |
| 伺服端新增 | 主檔 INSERT 影響 0 筆 | `throw`「新增OFD068A失敗」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:316-319` |
| 伺服端新增 | 明細 INSERT 影響 0 筆 | **不檢查** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:325-333` |
| 伺服端修改 | 主檔 UPDATE 影響 ≠ 1 筆 | `throw`「修改時影響筆數超過一筆,修改失敗,請檢查」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:472-473` |
| 伺服端修改 | 明細 D / A / U 影響筆數不對 | **三段檢核全被註解** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:502-503`、`:524-525`、`:544-545` |

**跨表更新**:`OFD070A`(境內承銷基金)與 `OFD070`(境外承銷基金),在同一個 `dbProduct` 交易裡。見 §8.2。

### 4.4 `OFDM062` 與 `OFDM066` — 基金公司 / 總代理(第二對同型畫面)

這兩支不吃同一組表,但**結構完全同型**:主檔是機構、明細是聯絡人、子對話框編輯一列聯絡人。它們是本片「成對畫面只改一邊」的最佳教材。

| 面向 | `OFDM062`(基金公司) | `OFDM066`(總代理) |
|---|---|---|
| 主檔 / 明細 | `OFD062` / `OFD063` | `OFD066` / `OFD067` |
| 明細 DataTable PK | **`FH_CD` 一欄** | `GAGENT_CD` + `DATAID` 兩欄 |
| 新增明細列時填 `DATAID` | **沒有** | 有,`Guid.NewGuid().ToString("N").ToUpper()` |
| 「系統公司」`'0000000000'` 擋新增 | 有,但 `e.Cancel = true` 後**沒有 `return`**,繼續跑 `DoValidate` | 有,而且有 `return` |
| 「系統公司」擋修改 | **沒有** | 有 |
| 「系統公司」擋刪除 | 有 | 有 |
| 「系統公司」擋編明細 | **沒有** | 有(新增明細擋、修改明細把子畫面的 OK 鈕 disable) |
| 明細至少一筆 | 有,但 `FH_CD == '0000000000'` 時豁免 | 有,**無豁免** |
| 「同作業別只能一筆主要窗口」檢核 | 有 `IsDuplicateError()`,**只在 `BeforeModify` 呼叫,`BeforeAdd` 沒呼叫** | 主畫面沒有;改在子對話框 `OFDM066p0` 檢「只可有一筆主要聯絡窗口別為是」 |
| 集保公司編號唯一性 | 有,`IsFH_TSCD_CODExsits`,四層都在且 UI 有呼叫 | 四層都在(`IsTSCD_AGENT_CDxsits`),**UI 完全沒有呼叫**,主畫面只留一個空的 `#region 原檢核集保公司編碼是否重複` |
| `ValidateErrList.ErrorCount != 0` 提早 return | **沒有**(所有檢核都會跑完) | **有**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:48`) |
| 主檔 join | `OFD008`(國別)、`OFD061`(TA)、`OFD066`(總代理) 三個 | 無 join |
| 明細 join | `COD006A`(`CODE_SORT='99'`)取聯絡人作業別說明 | 無 join |
| 檔案編碼 | `cp950` | `cp950` |
| UI 行數 | 513 | 299 |

錨點對照:

| 項 | `OFDM062` | `OFDM066` |
|---|---|---|
| 明細 PK | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM062Model.xsd:397-400` | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM066Model.xsd` |
| 新增明細列 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:450-465` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:236-257` |
| 擋新增 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:370-386` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:173-190` |
| 擋修改 | —(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:388-405` 沒有這段) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:192-207` |
| 擋刪除 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:413-420` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:284-291` |
| 唯一性檢核 PO | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:268-295` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:242-269` |
| 唯一性檢核 UI 呼叫 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:75-86` | **無呼叫端**;空殼在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:61-62` |

#### 4.4.1 `IsFH_TSCD_CODExsits` 與它沒被呼叫的雙胞胎

兩支 PO 的方法內容除了表名與欄名外**一字不差**:

```
SELECT COUNT(1) FROM OFD062 WHERE FH_CD <> :FH_CD AND FH_TSCD_CODE = :FH_TSCD_CODE
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:273-276`;`OFDM066` 版在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:247-250`。

回傳約定:`0` = 沒有重複、`1` = 有重複、`-1` = 例外。

`OFDM066` 側的呼叫鏈 `OFDM066_Pxy.IsTSCD_AGENT_CDxsits`(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM066_Pxy.cs:25`)→ `OFDM066_Ctl.IsTSCD_AGENT_CDxsits`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM066_Ctl.cs:50`)→ PO,**三層完整,但 `OFDM066.cs` 一次都沒叫過**。全庫搜 `IsTSCD_AGENT_CDxsits` 的 `.cs` 命中只有這三個宣告加一個介面宣告(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:29`),沒有任何呼叫端。

主畫面只剩一個空 region:

```
#region 原檢核集保公司編碼是否重複
#endregion
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:61-62`。上一行還留著一個沒用到的區域變數 `OFDM066ViewVDB view = new OFDM066ViewVDB();`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:58`)——**檢核被拆掉了,外殼沒收乾淨**。

`OFDM062` 側有呼叫,但錯誤處理有洞:

```
int i = ((OFDM062_Pxy)this.FormProxy).IsFH_TSCD_CODExsits(this.utxtFH_CD.Text, this.utxtFH_TSCD_CODE.Text);
if (i == -1)      → DialogWithNoStatusbar.ShowMessage(Error01, ServerSideError);   // 只顯示,不 AddError
else if (i == 1)  → ValidateErrList.AddError(…, "xxx 已存在");
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:77-85`。`-1` 那條只跳訊息、**沒有 `AddError`**,所以 `ValidateErrList.Show()` 回 false,存檔照樣進行。歸類為**記錄不擋**。

另外 `FH_CD <> :FH_CD` 是 Oracle 三值邏輯:新增一筆基金公司、`FH_CD` 還沒輸入(空字串 → Oracle 視為 NULL)時,`FH_CD <> NULL` 對每一列都是 UNKNOWN,`COUNT(1)` 回 0 → 回傳 `0` → 放行。不過 UI 端 `FH_CD` 是必填,實際不易踩到,列為**低**(附錄 E.14)。

#### 4.4.2 兩支的卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 聯絡人明細 0 筆(`FH_CD != '0000000000'`) | 「'基金公司聯絡人資料'至少輸入一筆資料」 | 阻擋 | `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:49-52` |
| 存檔前 | 聯絡人明細 0 筆(無豁免) | 「總代理公司聯絡人資料 至少輸入一筆資料」 | 阻擋 | `OFDM066` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:43-46` |
| 存檔前 | 英文名稱 / 簡稱含非英文 | 「只限輸入英文!」 | 阻擋 | 兩支各 2 條 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:54-61`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:50-57` |
| 存檔前 | 總代理為「其他公司」(`'1'`)時總代理公司代碼空 | 必填 | 阻擋 | `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:45` |
| 存檔前 | TA 處理碼為委外時 TA 公司代碼空 | 必填 | 阻擋 | `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:47` |
| 存檔前 | 集保公司編號在別筆已存在 | 「xxx 已存在」 | 阻擋 | **只有 `OFDM062`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:82-85` |
| 存檔前 | 查集保編號的 SQL 出錯 | 跳系統錯誤訊息,但不加進錯誤清單 | **記錄不擋** | 只有 `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:78-81` |
| 修改前 | 同一聯絡人作業別有兩筆主要窗口 | 「同一"聯絡人作業別"只能有一筆"主要聯絡窗口"」 | 阻擋 | **只有 `OFDM062` 的修改路徑** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:392-395` |
| 編聯絡人時 | 同作業別已有主要窗口 | 「只可有一筆'主要聯絡窗口別'為'是'…」 | 阻擋 | 兩支的子對話框 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062p0.cs:57`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066p0.cs:58` |
| 編聯絡人時 | EMAIL 格式錯 | 「EMAIL格式有誤」 | 阻擋 | 兩支的子對話框 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062p0.cs:48`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066p0.cs:49` |
| 新增 / 修改 / 刪除前 | 代碼是 `'0000000000'`(系統公司) | 「此筆資料為系統公司資料,不可…」 | 阻擋 | `OFDM062` 只擋新增與刪除;`OFDM066` 四處都擋 | 見上表 |
| 主檔查詢 | `FH_CD` / `GAGENT_CD` 用 `Like` 且**沒有判斷空字串** | 空值變成 `Like '%'`,等於不過濾 | 過濾(無提示) | `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:366-367` |

**跨表更新**:兩支都只寫自己的主從表,不動別的表。

### 4.5 `OFDM034` — 產壽險公司基本資料(唯一會改別人資料的畫面)

#### 4.5.1 88 % 是死碼

`OFDM034_PO.cs` 共 1192 行。`#region 註解` 從第 144 行開始、`/*` 在第 145 行、`*/` 在第 1188 行,**中間 1043 行整段被註解**——那是遷移前自己開連線、自己下 INSERT / UPDATE / DELETE 的舊實作(`AddINSUData` / `ModifyINSUData` / `DeleteINSUData` / `EVAINSUData` …)。

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:144-145`(起)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:1187-1189`(訖)。

活著的只有三段:建構子(`:40-49`)、`AfterUpdate`(`:57-101`)、`CheckData`(`:109-142`)。

同型情形在 `OFDM039_PO.cs`:1007 行裡 `#region old code` 從 `:60` 到 `:1002`,943 行是**用 `//` 逐行註解掉**的舊實作(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:60-1002`)。活著的部分只有一個建構子,連事件都沒掛。

#### 4.5.2 `AfterUpdate` — 改名字會連動兩張別人的表

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:57-101`。存檔成功後,在**同一個交易**(`args.DbTran`)裡下兩個 UPDATE:

| 目標表 | 條件 | 更新內容 | 錨點 |
|---|---|---|---|
| `OFD068A`(銷售機構) | `AGENT_ID = '5'` AND `AGENT_CODE = :INSU_CD` AND `(AGENT_NAME <> :AGENT_NAME OR AGENT_NAME_E <> :AGENT_NAME_E OR AGENT_SHNM <> :AGENT_SHNM)` | `AGENT_NAME` / `AGENT_NAME_E` / `AGENT_SHNM` / `UPDATEID` / `UPDATEDATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:65-83` |
| `OFD071A`(通路) | `CHANNEL_CD = '5'` AND `CHANNEL_CODE = :INSU_CD` AND `CHANNEL_DESCRP <> :CHANNEL_DESCRP` | `CHANNEL_DESCRP` / `UPDATEID` / `UPDATEDATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:86-100` |

好消息:這兩段**有用 bind 參數**,`OR` 那組也**有加括號**,不是 `AND`/`OR` 缺括號的案例。

壞消息有三個:

1. **Oracle 三值邏輯。** `AGENT_NAME <> :AGENT_NAME` 在 `AGENT_NAME` 為 NULL 時是 UNKNOWN。若 `OFD068A` 那一列的三個名稱欄都是 NULL(新建的銷售機構常見),整個 `(A OR B OR C)` 就是 UNKNOWN,**那一列不會被更新**——名稱永遠補不上。這是「本來想做省事最佳化,結果變成漏更新」的典型。

2. **`ExecuteNonQuery` 的回傳值被丟掉。** 兩段都是 `dbProduct.ExecuteNonQuery(cmd, args.DbTran);` 不接回傳值(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:83`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:100`),所以連動失敗與「本來就沒有對應列」分不出來。

3. **`'5'` 是寫死的。** 銷售機構別 / 通路別 `'5'` = 產壽險,值域在 `CTL014` `SourceType='062'`(DB 裡),程式沒有引用任何常數類別。〔客戶特定〕。

#### 4.5.3 `CheckData` — 刪除前查有沒有被引用

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:109-142`。一句 `SELECT SUM(DATACOUNT) FROM ( … UNION ALL … )` 把 `OFD071A`(`CHANNEL_CD='5'`)與 `OFD068A`(`AGENT_ID='5'`)的筆數加起來,有就回訊息:

> 此產壽險公司代碼尚有相對應的通路[OFDM071]或已建立銷售機構資料[OFDM068],故不可刪除

**注意回傳約定很特別**:成功路徑一律 `AddResultRow(true, 筆數, 訊息)`——第一個參數(`ReturnCode`)恆為 `true`,靠**第二個參數(筆數)**判斷有沒有被引用;`catch` 才會回 `AddResultRow(false, 0, "")`,而且**訊息是空字串**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:135-140`)。

UI 端(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:112-133`):

| `ReturnCode` | `ReturnRowCount` | 行為 | 錨點 |
|---|---|---|---|
| `true` | `!= 0` | `AddError(ReturnMessage)` + `Show()` + `e.Cancel = true` → 擋住 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:120-126` |
| `true` | `0` | 什麼都不做 → 刪除放行 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:118-127` |
| `false`(PO 丟例外) | `0` | `ShowMessage(Info01, "")` + `e.Cancel = true` → **擋住,但跳出來的是一個空訊息框** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:128-132` |

**這支是本片唯一「DB 出錯時偏保守(擋住)」的檢核**,方向是對的——但訊息是空字串,使用者只會看到一個沒有內容的對話框,不知道發生什麼事(附錄 E.15)。

#### 4.5.4 `OFDM034` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 產壽險公司代碼長度 < 5 | 「產壽險公司代碼,輸入長度至少為五碼。」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:155` |
| 存檔前 | 英文名稱含非英數字 | 「公司英文名稱,只限輸入英文及數字!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:159` |
| 刪除前 | `OFD071A` + `OFD068A` 有引用 | 「…故不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:120-126` |
| 刪除前 | 查引用的 SQL 出錯 | 擋住刪除,但訊息框是**空的** | 阻擋(訊息缺失) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:128-132`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:135-140` |
| 存檔後 | 名稱有變 | 連動 UPDATE `OFD068A` / `OFD071A`;三個名稱欄都是 NULL 時**不會更新** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:74`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:93` |

**跨表更新**:`OFD068A`、`OFD071A`。見 §8.1。

### 4.6 `OFDM040` — 通知書寄發設定(唯一有互斥鍵檢核,而且有三個洞)

`OFD040A` 的 PK 是三欄:`STATEMENT_CODE`(通知書代碼)+ `BF_COUNTRY_X`(身份別)+ `OPEN_ACC_TYPE`(開戶類別)。業務規則是「同一張通知書 + 同一開戶類別,不可以同時存在 `'00'`(自然人+法人)與 `'01'`/`'02'`(單一身份別)兩種設定」——這是 DB PK 擋不住的,所以要靠程式。

#### 4.6.1 `CheckData` 的三段式條件

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:241-301`:

```
SELECT COUNT(*) FROM OFD040A
 WHERE STATEMENT_CODE = :STATEMENT_CODE
   AND OPEN_ACC_TYPE  = :OPEN_ACC_TYPE
   [ 依 BF_COUNTRY_X 追加 ]
```

| 傳進來的 `BF_COUNTRY_X` | 追加條件 | 錨點 |
|---|---|---|
| `'00'` | `AND ((BF_COUNTRY_X = '01') OR (BF_COUNTRY_X = '02'))` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-264` |
| `'01'` 或 `'02'` | `AND (BF_COUNTRY_X = '00')` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:266-271` |
| **其他任何值** | **不追加任何條件** | 兩個 `if` 都不成立 |

#### 4.6.2 三個洞

| # | 洞 | 影響 | 錨點 |
|---|---|---|---|
| 1 | **落到 `else` 時條件被整個拿掉。** 沒有 `else` 分支,`BF_COUNTRY_X` 若是 `'00'`/`'01'`/`'02'` 以外的值(例如未來多一種身份別、或使用者沒選就送出),SQL 變成「同 `STATEMENT_CODE` + 同 `OPEN_ACC_TYPE` 的**全部**筆數」——只要那組合有任何一筆就擋,**誤擋** | 阻擋(誤擋) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-271` |
| 2 | **`catch` 吃掉例外,`IsExit` 留在初值 `false`** → DB 出錯 = 沒有衝突 = 放行 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:291-294`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:243` |
| 3 | **第四個參數 `m_SEND_CODE` 完全沒用到。** 方法簽名收了它,body 裡只有兩行被註解掉的用法 | 死參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:241`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:262`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:269`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:279` |

另外一個小問題:UI 端在 `BeforeAddButtonClicked` 裡是**先 `DoValidate()` 再無條件呼叫 `CheckData`**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:77-83`),必填沒過也照樣打一次伺服端。

#### 4.6.3 `OFDM040` 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `SEND_CODE == 'Y'` 但六個寄發途徑都沒勾 | 「寄發途徑必須勾選任一項」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:191-200` |
| 新增前 | 同通知書 + 同開戶類別的身份別互斥 | 「'X'且開戶類別為'Y'之類別,已存在於身份別為'自然人+法人'中」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:80-83` |
| 新增前 | `BF_COUNTRY_X` 不是 `'00'`/`'01'`/`'02'` | 條件被拿掉,同鍵任何一筆都會誤擋 | 阻擋(誤擋) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-271` |
| 新增前 | 查互斥的 SQL 出錯 | 當成沒衝突 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:291-294` |
| 改寄發碼後 | 通知書代碼 ≠ `'01'` 卻選了每月 / 每三個月 / 每六個月寄發 | 三句「通知書代碼為'境內對帳單'時,才可挑選…」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:257-272` |
| 修改頁載入 | 三個 PK 欄位轉唯讀 | 不能改鍵 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:210-212` |
| 主檔取數 | 三個查詢條件字串串接 | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:182-222` |

`STATEMENT_CODE` 與 `SEND_CODE` 的中文名從 `CTL014` 取:`SourceType='150'`(通知書代碼)與 `SourceType='073'`(寄發碼),兩個都是 `LEFT JOIN`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:174-179`)。〔客戶特定〕的 `'150'` / `'073'` 值域在 DB。

### 4.7 `OFDM030` — 集保申購款入款銀行設定

小而典型的一支。主檔 `OFD030`,PK `BANK_HQ`,`LEFT JOIN OFD019A` 取銀行簡稱(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:129-132`)。

業務上最重要的欄是 `ACC_NO_CORR`(匯款帳號對應碼)——它是 Oracle Function `GET_REMIT_ACC_NO` 組受益人虛擬帳號的前綴(`DB/Function/GET_REMIT_ACC_NO.SQL:30-33`)。改錯這一欄,整家銀行的虛擬帳號都會錯。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `BANK_TYPE == "0"`(集保款項收付銀行)且匯款帳號對應碼為空 | 「必須輸入匯款帳號對應碼!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:173-179` |
| 新增前 | 上一條 | 有錯就 `e.Cancel = true` **並 `return`** | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:113-118` |
| 修改前 | 上一條 | 有錯就 `e.Cancel = true`,**但沒有 `return`**,後面 10 行照樣把畫面值寫回 Row | 阻擋(但有副作用) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:140-150` |
| 新增後 | `AfterAddButtonClicked` **再跑一次** `DoValidate()` | 同上 | 重複檢核 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:183-191` |
| 主檔查詢 | 銀行代碼空字串時不加條件(註解寫明「將查詢條件 Like 改為 Equal」) | 全撈 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:105-107` |

「新增有 `return`、修改沒有」這種同一支檔案裡兩條路徑不一致,是本片重複出現的形狀(附錄 E.9)。

### 4.8 多筆型兩支:`OFDM038`(基金群組)與 `OFDM041`(帳務說明片語範本)

兩支都是 `BaseMultiRowEVADaoPO`,**沒有明細表**:上半的「群」與下半的「列」是同一張表,靠 `MasterPKey` 分群,主檔查詢用 `ROW_NUMBER() OVER (PARTITION BY …) … WHERE NUM = 1` 只取群首。

| 面向 | `OFDM038` | `OFDM041` |
|---|---|---|
| 實體表 → vdb | `OFD038A` → `OFDM038` | `OFD041A` → **`OFD041`** |
| `MasterPKey` | `FUND_GRPCD`(基金群組代碼) | `ACCOUNT_COPY`(範本名稱) |
| 群內排序 | `ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE, FUND_ID` | `ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE, DATA_SEQ` |
| 群首列的假欄位 | `' ' FUND_ID`(把基金代碼清成空白) | `0 DATA_SEQ`(把流水號清成 0) |
| 明細 join | `LEFT JOIN OFD081A` 取基金簡稱,再 `LEFT JOIN OFD0811A` 把警示備註 `\|\|` 串在後面 | 無 |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:49-93` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM041_PO.cs:80-120` |

> ⚠ `OFDM038` 的明細把 `OFD081A.FUND_SH_NM || TRIM(OFD0811A.FUND_ALERT_MEMO)` 直接串成同一個 `FUND_SH_NM` 欄(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:84`)。**基金簡稱與警示備註在畫面上是黏在一起的一個字串**,程式端無法分開,下游若要拆會拆錯。

#### 4.8.1 卡控

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `OFDM038` | 存檔前 | 明細 0 筆 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM038.cs:163` |
| `OFDM038` | 存檔前 | 任一列基金代碼空白 | 「基金代碼 不可為空白」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM038.cs:170` |
| `OFDM038` | Grid 離開編輯 | 基金代碼空 | 「'基金代碼'必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM038.cs:242` |
| `OFDM038` | 主檔取數 | `NUM = 1` | 群內非首列不出現在上半 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:64` |
| `OFDM041` | 存檔前 | 任一列範本內容空 | 「範本內容 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM041.cs:109` |
| `OFDM041` | 存檔前 | 明細 0 筆 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM041.cs:113` |
| `OFDM041` | 主檔取數 | `NUM = 1` | 同上 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM041_PO.cs:94` |

**兩支都沒有「群組代碼 / 範本名稱重複」的檢核**,靠 DB 的 PK 擋。

### 4.9 其餘七支:純框架或近乎純框架

這七支沒有值得單獨一節的機制,合併帶過。共同點:PO 只掛三個取數事件(有些連事件都不掛),查詢條件手寫字串串接,UI 只有必填與格式檢核。

| 畫面 | 主表 | PO 行數 | PO 做了什麼 | UI 業務檢核 |
|---|---|---|---|---|
| `OFDM039` | `OFD039A` | 1007(**其中 943 行是註解掉的舊實作**) | **只有建構子宣告主檔,連事件都沒掛**——查詢與存檔完全走框架預設 | 「適用境內/境外 選項,請至少須挑選一項」「適用作業別 選項,請至少須挑選一項」;四個「寬限補件天數 必須輸入」條件式必填 |
| `OFDM054` | `OFD054A` | 184 | 三個取數事件 + 手寫主檔 SQL + 一份自帶的 `AddParam`(T-SQL 風的 `CONVERT(NVARCHAR,…,111)` 分支) | **零業務檢核**,UI 只有 91 行 |
| `OFDM055` | `OFD055A` | 49 | **什麼都沒做**,只有建構子一行宣告主檔 | 「有效月份必須大於零!」(新增與修改各一份,程式碼重複) |
| `OFDM061` | `OFD061` | 69 | 掛了一個 `AfterUpdate`,但 body 只有一行註解 `//nothing`;建構子裡有一行 `dbProduct = dbProduct;` 自我指派 | 「EMAIL格式有誤」、「不可新增TA公司代碼為 '0000000000' 的資料」、「TA公司英文名稱,只限輸入英文!」 |
| `OFDM064` | `OFD064` | 188 | 三個取數事件 + 手寫主檔 SQL(join `OFD062` 取基金公司簡稱、join `FSK003` 取幣別名) | 「收款銀行SWIFT代碼至少輸入八碼!」「中間銀行SWIFT代碼至少輸入八碼!」 |
| `OFDM065` | `OFD065` | 165 | 同上(join `OFD062` 與 `OFD008`) | 「不可修改資料, 請先刪除再新增!!」——整支畫面禁止修改 |
| `OFDM045p0` / `OFDM062p0` / `OFDM066p0` / `OFDM068p0` | —(子對話框) | — | — | EMAIL 格式、主要聯絡窗口唯一、排序確認 |

錨點:

| 項 | 錨點 |
|---|---|
| `OFDM039_PO` 的 943 行註解區 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:60-1002` |
| `OFDM039_PO` 檔尾的合併殘留 `}//end namespace Adapterusing System;` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:1007` |
| `OFDM039` 的兩條「至少挑一項」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM039.cs:299`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM039.cs:302` |
| `OFDM039` 的四條寬限天數必填 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM039.cs:306-312` |
| `OFDM054_PO` 的 T-SQL 風 `AddParam` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM054_PO.cs:147` |
| `OFDM055_PO` 全部內容 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM055_PO.cs:33-48` |
| `OFDM055` 的「有效月份必須大於零」×2 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM055.cs:65`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM055.cs:85` |
| `OFDM061_PO` 的 `dbProduct = dbProduct;` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM061_PO.cs:48` |
| `OFDM061_PO` 的空 `AfterUpdate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM061_PO.cs:63-66` |
| `OFDM061` 擋 `'0000000000'` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM061.cs:153` |
| `OFDM064` 的兩條 SWIFT 長度 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM064.cs:150`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM064.cs:155` |
| `OFDM064_PO` 的主檔 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:113-136` |
| `OFDM065` 的「不可修改」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM065.cs:79` |
| `OFDM065_PO` 的主檔 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:113-126` |

> ⚠ `OFDM039` 值得特別記一筆:它是**本片唯一連取數事件都沒掛的畫面**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:46-49` 建構子裡只有一行 `MasterTable = …`)。所有查詢與存檔 SQL 由 `BaseEVADaoPO` 依 xsd 欄位自動產生。好處是零手寫 SQL、零注入面;代價是畫面上看到的所有「適用境內 / 境外」「限制申購天數」那些欄位**沒有任何 join 帶出中文說明**,Grid 上只會是原始代碼。

## 5. 查詢畫面(I)

**本片無 I 畫面。** 原因:`DataEntity.OFD4` 這個 Entity 專案底下 18 份 Model 全部是 `OFDM*`(M 型)命名,沒有任何 `OFDI*`;OFD 模組的查詢畫面集中在另一個專案 `Dev/ATLAS.OFD.Query`,依切片定義不屬於本片。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。** 原因:18 支的 UI 基底全部是 `xMaintainForm`(查詢頁 + 維護頁的兩頁式維護表單),沒有一支是 `xOneStepProcessForm` 這類批次畫面;`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/` 底下也沒有 `OFDB*` 的 Model。

最接近批次的是 `OFDM046` 的附件上傳 / 下載(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:88-132`),但那是 M 畫面上的兩個按鈕,一次處理一個檔,而且那支畫面執行期是死的(§4.2)。

## 7. 報表(R)

**本片無 R 畫面。** 原因:`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/` 底下沒有任何 `*R*Model.xsd`;本片 18 支也沒有任何一支叫 `rpt` 或 `ReportService`。

本片的表被報表讀到的情形有一例:`OFD038A` 被 `NFDR113` 讀(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR113.cs:262`),但那支報表不屬於本片。

## 8. 跨模組共用

```text
[圖] OFD4 五組跨模組：OFD068A 給十一個讀者、OFD030 給虛擬帳號、OFD054A 給 BMS、OFD041 讀錯邊、OFD045 讀端活維護端死
圖中文字:A：OFD068A —— 本片維護，11 個地方在讀，而且本片另一支畫面也會寫它 / OFDM068〔OFD4〕 / 唯一維護入口 有四眼 / OFD068A / PK 機構別+機構代碼 / CAS COD CRM DSM OTA… / 10 專案 + 2 支報表 SP / OFDM034 直接 UPDATE / 不經 OFDM068 的四眼 / B：OFD030 —— 匯款帳號對應碼被 Oracle Function 拿去組虛擬帳號 / OFDM030〔OFD4〕 / ACC_NO_CORR / GET_REMIT_ACC_NO / 版控內 Function / 受益人虛擬帳號 / 對應碼錯 帳號全錯 / 沒有過濾 EFFECT_YN / 停用帳戶照樣產生 / C：OFD054A —— 本片維護，BMS 開戶畫面當自己的明細吃 / OFDM054〔OFD4〕 / 零業務檢核 / OFD054A / 受益人類別 x 應繳文件 / BMSM001〔BMS〕 / 宣告成自己 Model 的表 / 這裡加一筆 / 開戶畫面立刻多一列 / D：OFD041 vs OFD041A —— 兩張同形表，消費端讀錯邊 / OFDM041 維護 OFD041A / vdb 名卻叫 OFD041 / Utility_PO 讀 OFD041A / 基底 正確 / UtilityOracleDao 讀 OFD041 / 同一支方法 覆寫版 錯 / OFDB238 讀 OFD041 / 還寫死 ACCOUNT_COPY='14' / E：OFD045 —— 讀端活著，維護畫面死了 / OFDM045〔OFD4〕 / 執行期必 NRE / OFD045 KYC 問項 / 資料還在用 / BasicCMM_PO 讀它 / Oracle 與 MSSQL 各一份 / 要改只能動 DB / 沒有可用的維護入口
```

*圖:圖 5 跨模組。橘框=本片的維護入口;白框=表或正常機制;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼或版控外的 DB 物件。D 與 E 兩組最需要處理:D 是改了設定有兩個消費端讀不到，E 是資料還在用但已經沒有維護畫面。*

本片 22 張表裡有 13 張被本專案以外的模組讀到,其中兩張(`OFD068A` `OFD062`)是全庫等級的主檔。另有兩條「本片寫別人的表」的路徑。

### 8.1 `OFDM034` → `OFD068A` + `OFD071A`:本片唯一的旁寫

`OFDM034`(產壽險公司)存檔成功後,在 `AfterUpdate` 裡直接 UPDATE 兩張別的畫面在維護的表:

| 目標 | 誰才是主人 | 本片做了什麼 | 錨點 |
|---|---|---|---|
| `OFD068A` | **`OFDM068`**(也在本片,§4.3) | 把 `AGENT_ID='5'` 且 `AGENT_CODE = 產壽險公司代碼` 的那一列的三個名稱欄改掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:65-83` |
| `OFD071A` | `OFDM071`(不在本片) | 把 `CHANNEL_CD='5'` 且 `CHANNEL_CODE = 產壽險公司代碼` 的那一列的 `CHANNEL_DESCRP` 改掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:86-100` |

**影響面:**

1. 這兩筆異動**不經 `OFDM068` / `OFDM071` 的四眼**。`UPDATEID` / `UPDATEDATE` 會被改,但 `STATUS` / `VERIFYID` / `APPROVEID` 不變——資料變了、覆核軌跡沒變。

2. 三值邏輯導致「名稱欄是 NULL 就不更新」(§4.5.2),所以 `OFD068A` 可能永遠留著空名稱。

3. `'5'` 是寫死的。若站台把產壽險的銷售機構別改成別的碼,這段同步整個失效,而且不會報錯。

### 8.2 `OFDM068` → `OFD070A` + `OFD070`:有效碼連動

`OFDM068` 的 `Add` 與 `Update` 都會連動承銷基金設定檔:

| 路徑 | 條件 | 錨點 |
|---|---|---|
| `Add` | `AGENT_VALID_CODE` 為無效 → `OFD070A` 設無效 + 迄日;為有效 → `OFD070A` 設有效 + 迄日清空。**只動境內 `OFD070A`,不動境外 `OFD070`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:341-381` |
| `Update` | 走 `UpdateAGENT_VALID_CODE`,**境內 `OFD070A` 與境外 `OFD070` 都動**,境外的值要反轉成 `'0'`/`'1'`,還會帶 `DECLARE_TSCD` / `CO_DATE` / `CO_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:218-279`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:460` |

**新增與修改的連動範圍不一致**(新增只動境內、修改動兩張),而且修改那條在 `AGENT_ID != '2'` 時因為 `=` 配 `%` 而完全命不中(§4.3.3)。這一組是本片最需要實機驗證的地方。

### 8.3 `OFD068A` — 全庫等級的銷售機構主檔

**本片的 `OFDM068` 是唯一維護入口**,但至少 11 個地方在讀:

| 讀者 | 用途 | 錨點(舉例) |
|---|---|---|
| `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` | 共用查詢 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4936` |
| `Dev/Common/Source/DataSource/PO.DataSource/Oracle/BasicOFDOracleDao.cs` | 共用查詢(Oracle 版) | `Dev/Common/Source/DataSource/PO.DataSource/Oracle/BasicOFDOracleDao.cs:531` |
| `ATLAS.CRM` | 客訴案件帶「最後銷售機構名稱」 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:79-89` |
| `ATLAS.CAS` / `ATLAS.CLS.Report` / `ATLAS.COD` / `ATLAS.DSM` | 各自的查詢與報表 | 見全庫搜尋 |
| `ATLAS.OFD.Query` / `ATLAS.OFDB` / `ATLAS.OTA` / `ATLAS.OTA.Query` / `ATLAS.OTAB` | 交易與批次 | 同上 |
| `DB/SP/S_OTA_OFDR052_GET.sql`、`DB/SP/S_OTA_OFDR081_GET.sql` | 報表 SP | 兩支 SP |
| 本片的 `OFDM034` | **寫入**(§8.1) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:65-83` |

**改 `OFD068A` 的欄位定義要一起看這 11 處。**

### 8.4 `OFD062` — 基金公司主檔

`OFDM062` 是唯一維護入口,讀者散在 8 個專案外加 DB:

| 讀者 | 用途 |
|---|---|
| `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:1168` | 共用查詢 |
| `ATLAS.BMS` / `ATLAS.EC` / `ATLAS.OFDB` / `ATLAS.OFDI` / `ATLAS.OTA` / `ATLAS.OTA.Query` / `ATLAS.OTAB` | 基金公司名稱 |
| 本片的 `OFDM064` / `OFDM065` | `LEFT JOIN` 取簡稱 |
| `DB/` 底下的多支 SP | 報表 |

### 8.5 `OFD030` — 集保入款銀行,被 Oracle Function 讀

| 讀者 | 用途 | 錨點 |
|---|---|---|
| `DB/Function/GET_REMIT_ACC_NO.SQL` | **用 `ACC_NO_CORR` 組受益人虛擬帳號**;`WHERE` 只有 `BANK_HQ`,**沒有過濾 `EFFECT_YN`** | `DB/Function/GET_REMIT_ACC_NO.SQL:30-33` |
| `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:448` | 共用查詢 | 同左 |
| `ATLAS.BMS` / `ATLAS.OFD.Query` / `ATLAS.OFDB` / `ATLAS.OFDI` / `ATLAS.OTA` | 匯款相關 | 全庫搜尋 |

這是本片對外影響最「直接看得到錢」的一張表:`ACC_NO_CORR` 改錯,受益人匯款進來的虛擬帳號就對不上。

### 8.6 `OFD054A` — 本片維護,BMS 開戶畫面當明細吃

`OFD054A`(受益人類別應繳交文件)由 `OFDM054` 維護,但 `BMSM001`(受益人開戶)把它**宣告成自己 Model 的一張 DataTable**,在開戶流程裡帶出「這個受益人類別要繳哪些文件」:

錨點:`Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs:328`、`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.Designer.cs:352-353`。

**影響面**:`OFDM054` 加一筆文件代碼,BMS 的開戶畫面立即多一列;`OFDM054` 完全沒有業務檢核(§4.9),所以「亂加一筆」不會在本片被擋。

### 8.7 `OFD045` — KYC 問項被 `BasicCMM_PO` 讀

`OFD045` 的維護入口 `OFDM045` **執行期是死的**(§4.2),但讀端活著:

| 讀者 | 錨點 |
|---|---|
| `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:100`(Oracle,現行) | `FROM OFD045` |
| `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicCMM_PO.cs:134`(MSSQL,舊) | `FROM [OFD045]` |

也就是說:**KYC 問項這份資料還在被使用,但已經沒有可用的維護畫面**。要改只能直接動 DB。這是本片最需要回報給業務端的一件事。

### 8.8 其餘表的影響面速查

| 表 | 本片維護入口 | 外部讀者(專案) |
|---|---|---|
| `OFD034A` | `OFDM034` | `Common` |
| `OFD035A` / `OFD036A` | `OFDM035` + `OFDM036` | `ATLAS.OFDB`(只有 `OFD035A`) |
| `OFD038A` | `OFDM038` | `Common` `ATLAS.NFD.Report` `ATLAS.OFD.Query` `ATLAS.OFDB` `ATLAS.RSP` `ATLAS.SDM` |
| `OFD039A` | `OFDM039` | `Common` `ATLAS.EC` `ATLAS.OFDI` |
| `OFD040A` | `OFDM040` | `Common` `ATLAS.BMS` `ATLAS.RSP` |
| `OFD041A` | `OFDM041` | `Common` `ATLAS.BMS` `ATLAS.OFDB` `ATLAS.OFDI` `ATLAS.RSP` |
| `OFD046` / `OFD047` | `OFDM046`(死) | **無**——全庫只有 `OFDM046` 自己碰 |
| `OFD055A` | `OFDM055` | `Common` `ATLAS.BMS` |
| `OFD061` | `OFDM061` | `Common` `ATLAS.OTA` `ATLAS.OTAB` `DB` |
| `OFD063` | `OFDM062` | **無** |
| `OFD064` | `OFDM064` | 本片的 `OFDM081B` 之外無 |
| `OFD065` | `OFDM065` | `Common` |
| `OFD066` | `OFDM066` | `Common` `ATLAS.BMS` `ATLAS.OTA` |
| `OFD067` | `OFDM066` | **無** |
| `OFD069A` | `OFDM068` | **無** |

規律:**主檔外流、聯絡人明細不外流。** 三組「機構 + 聯絡人」(`OFD062`/`OFD063`、`OFD066`/`OFD067`、`OFD068A`/`OFD069A`)都是主檔被很多人讀、明細只有自己用。

## 附錄 A. 資料表總表

### A.1 本片宣告的 22 張實體表

| # | 表 | 中文(推測) | 維護畫面 | 主 / 明細 | 欄數 | PK | 外部讀者數 |
|---|---|---|---|---|---|---|---|
| 1 | `OFD030` | 集保申購款入款銀行 | `OFDM030` | 主 | 28 | `BANK_HQ` | 6 專案 + DB |
| 2 | `OFD034A` | 產壽險公司 | `OFDM034` | 主 | 27 | `INSU_CD` | 1 |
| 3 | `OFD035A` | 贖回匯費主設定(匯款上限 / 郵寄費) | `OFDM035` + `OFDM036` | 主 | 20 / 21 | `BANK_HQ` `CRNCY_CD` | 1 |
| 4 | `OFD036A` | 贖回匯費級距明細 | `OFDM035` + `OFDM036` | 明細 | 21 | `BANK_HQ` `CRNCY_CD` `REMIT_AMT1` | 0 |
| 5 | `OFD038A` | 基金群組 | `OFDM038` | 主(多筆型) | 19 | `FUND_GRPCD` `FUND_ID` | 5 |
| 6 | `OFD039A` | 缺件代碼 | `OFDM039` | 主 | 34 | `LACK_CODE` | 3 |
| 7 | `OFD040A` | 通知書寄發設定 | `OFDM040` | 主 | 27 | `STATEMENT_CODE` `BF_COUNTRY_X` `OPEN_ACC_TYPE` | 3 |
| 8 | `OFD041A` | 帳務說明片語範本 | `OFDM041` | 主(多筆型) | 18 | `DATA_SEQ` `ACCOUNT_COPY` | 4 |
| 9 | `OFD045` | KYC 問項 | `OFDM045`(**死**) | 主(多筆型) | 21 | `BF_COUNTRY_X` `KYC_CODE` `KYC_ITEM` | 1 |
| 10 | `OFD046` | 作業文件範本 | `OFDM046`(**死**) | 主 | 19 | `DATA_SEQ` | 0 |
| 11 | `OFD047` | 作業文件附件 | `OFDM046`(**死**) | 明細 | 19 | `DATA_SEQ` `FILENAME` | 0 |
| 12 | `OFD054A` | 受益人類別應繳交文件 | `OFDM054` | 主 | 19 | `BF_SORT_CD` `LACK_CODE` | 1(BMS 當明細) |
| 13 | `OFD055A` | 資產證明內容代碼 | `OFDM055` | 主 | 18 | `ASSET_CODE` | 2 |
| 14 | `OFD061` | TA 公司 | `OFDM061` | 主 | 30 | `TA_CD` | 3 + DB |
| 15 | `OFD062` | 基金公司 | `OFDM062` | 主 | 37 | `FH_CD` | 8 + DB |
| 16 | `OFD063` | 基金公司聯絡人 | `OFDM062` | 明細 | 33 | `FH_CD`(**只有一欄**) | 0 |
| 17 | `OFD064` | 基金公司申購匯款帳戶 | `OFDM064` | 主 | 33 | `FH_CD` `CRNCY_CD` | 0 |
| 18 | `OFD065` | 基金公司銷售國別 | `OFDM065` | 主 | 22 | `FH_CD` `COUNTRY_CD` | 1 |
| 19 | `OFD066` | 總代理公司 | `OFDM066` | 主 | 25 | `GAGENT_CD` | 3 |
| 20 | `OFD067` | 總代理公司聯絡人 | `OFDM066` | 明細 | 28 | `GAGENT_CD` `DATAID` | 0 |
| 21 | `OFD068A` | 銷售機構 | `OFDM068` | 主 | 48 | `AGENT_ID` `AGENT_CODE` | 10 + DB |
| 22 | `OFD069A` | 銷售機構聯絡人 | `OFDM068` | 明細 | 29 | `AGENT_ID` `AGENT_CODE` `DATA_SEQ` | 0 |

### A.2 只讀不寫的外部表(join 進來取說明)

| 表 | 用途 | 被哪支 join | 錨點 |
|---|---|---|---|
| `OFD019A` | 金融機構總行簡稱 | `OFDM030` `OFDM036` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:132`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:123-124` |
| `FSK003` | 幣別名稱 | `OFDM035` `OFDM036` `OFDM064` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:120-121`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:134-135` |
| `OFD008` | 國別名稱 | `OFDM062` `OFDM065` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:147-148`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:124-125` |
| `OFD081A` | 境內基金簡稱 | `OFDM038` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:87` |
| `OFD0811A` | 基金警示備註 | `OFDM038` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:88` |
| `COD006A` | 聯絡人作業別說明(`CODE_SORT='99'`) | `OFDM062` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:233-235` |
| `CTL014` | 共用下拉代碼(`'334'`/`'335'` KYC、`'150'` 通知書、`'073'` 寄發碼、`'062'` 銷售機構別) | `OFDM040` `OFDM045` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:174-179`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:51-54` |
| `OFD061` | TA 公司名稱 | `OFDM062` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:149-150` |
| `OFD066` | 總代理簡稱 | `OFDM062` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:151-152` |
| `OFD062` | 基金公司簡稱 | `OFDM064` `OFDM065` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:132-133`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:122-123` |

### A.3 本片會寫、但主人在別處的表

| 表 | 主人 | 寫入者 | 錨點 |
|---|---|---|---|
| `OFD071A` | `OFDM071` | `OFDM034` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:86-100` |
| `OFD070A` | 承銷基金設定畫面(不在本片) | `OFDM068` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:229-244`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:345-359` |
| `OFD070` | 同上(境外) | `OFDM068` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:251-272` |
| `OFD068A` | `OFDM068`(同片) | `OFDM034` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:65-83` |

### A.4 檢核時讀到的交易表(只 `COUNT`,不改)

`OFDM068.CheckAgent` 會數這六張的筆數:`OFD232A` `OFD220A` `OFD259A` `OFD251A` `OFD253A` `RSP005A`;`AGENT_ID='2'` 時再多讀 `FSK005`(券商代碼展開)。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:596-616`。

## 附錄 B. SP / Function / Trigger / View

**本片 18 支畫面沒有呼叫任何 SP、Function、Trigger 或 View。** 所有資料存取都是 PO 裡手寫的 inline SQL 或框架產生的 SQL。

唯一與本片有關的 DB 物件是**下游**的:

| 物件 | 類型 | 與本片的關係 | 錨點 |
|---|---|---|---|
| `GET_REMIT_ACC_NO` | Oracle Function | 讀 `OFD030.ACC_NO_CORR` 組虛擬帳號;**不過濾 `EFFECT_YN`** | `DB/Function/GET_REMIT_ACC_NO.SQL:30-33` |

`DB/SP/` 底下有兩支 SP 讀 `OFD068A`(`S_OTA_OFDR052_GET.sql`、`S_OTA_OFDR081_GET.sql`),但它們屬於 OTA 報表,不是本片的呼叫鏈。

## 附錄 C. 代碼對照

| 代碼組 | 值 | 意義 | 來源 | 確定度 |
|---|---|---|---|---|
| `BANK_HQ` 哨兵 | `'ALL'` | 全行通用的贖回匯費設定 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:122`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:123` | 確定 |
| `BANK_TYPE` | `0` / `1` | 集保款項收付銀行 / 全國繳稅費銀行 | xsd Caption 直接寫明 | 確定 |
| `EFFECT_YN` | `Y` / `N` | 有效銀行帳號 | xsd Caption | 確定 |
| `AGENT_VALID_CODE` | `Y` / `N` | 有效 / 無效 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:123-134` | 確定 |
| `AGENT_VALID_CODE`(寫進境外 `OFD070`) | `0` / `1` | `Y` → `0`、`N` → `1`(**反轉**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:265` | 確定(值的意義待查) |
| `AGENT_ID` | `'1'` | 銀行 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:54-55`(`'1'`/`'2'` 時付款行必填) | **推測** |
| `AGENT_ID` | `'2'` | 券商 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:596-604`(`'2'` 時去 `FSK005` 展開 `STK_BRK` 券商代碼) | **推測**(證據強) |
| `AGENT_ID` | `'5'` | 產壽險 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:72`(產壽險公司改名同步到 `AGENT_ID='5'` 的列) | **推測**(證據強) |
| `AGENT_ID` 完整值域 | `CTL014` `SourceType='062'` | 「帳戶歸屬銷售機構區別碼」 | `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/TrustAgentIDDataSrc.cs:11-15` | 值域在 DB,**缺連線** |
| `CHANNEL_CD` | `'5'` | 產壽險通路 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:91` | **推測**(與 `AGENT_ID='5'` 同一批寫死) |
| `BF_COUNTRY_X` | `'00'` / `'01'` / `'02'` | 自然人+法人 / 單一身份別 A / 單一身份別 B | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:83`(訊息寫「身份別為'自然人+法人'」)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-271` | `'00'` 確定;`'01'`/`'02'` 哪個是自然人**推測** |
| KYC 問項來源 | `CTL014` `SourceType='334'` / `'335'` | `BF_COUNTRY_X='01'` 用 `'334'`,其餘用 `'335'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:53-54` | 確定(意義待 DB) |
| `KYC_ITEM` | `'A'` ~ `'S'` | 19 個問項序號,程式自動編 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:175-183` | 確定 |
| `STATEMENT_CODE` | `'01'` = 境內對帳單;其餘在 `CTL014` `SourceType='150'` | 通知書代碼 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:257`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:175` | `'01'` 確定;其餘在 DB |
| `SEND_CODE` | `'Y'` = 寄發;`'1'`/`'2'`/`'3'` = 每月 / 每三個月 / 每六個月;完整值域 `CTL014` `SourceType='073'` | 寄發碼 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:191`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM040.cs:257-272` | 確定 |
| `DECLARE_TSCD` | `'Y'` / 其他 | 申報集保 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:66` | 確定 |
| `TA_OP` | `TA_OP.TAOrder`(常數) | TA 委外 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:47`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:127` | 確定(值在 MappingCode) |
| `GAGENT` | `'0'` / `'1'` | `GAGENT_CD = '0000000000'` → `'0'`(無總代理),否則 `'1'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:138-139` | 確定 |
| `FH_CD` / `GAGENT_CD` / `TA_CD` 哨兵 | `'0000000000'` | 系統公司 / 無總代理 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:372`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:175`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM061.cs:153` | 確定 |
| `COD006A.CODE_SORT` | `'99'` | 聯絡人作業別代碼群 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:234` | 確定 |
| `CNT_WINDOW` | `'Y'` | 主要聯絡窗口 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:173` | 確定 |
| 幣別預設 | `'TWD'` | `OFDM035` / `OFDM036` 新增預設 + `OFDM036` 郵費 fallback | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:110`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:233` | 確定 |

## 附錄 D. 掃描母體與覆蓋率

`atlas_scan.py --module OFD` 對單片沒有意義(OFD 有 550 支),所以改成逐支列。

### D.1 18 支畫面的處置

| # | 畫面 | 處置 | 章節 | 深度 | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|
| 1 | `OFDM030` | 已寫 | §4.7 | 一支一節 | `BaseEVADaoPO` | 六層齊 |
| 2 | `OFDM034` | 已寫 | §4.5 | **深寫**(跨表旁寫 + 88% 死碼) | `BaseEVADaoPO` | 六層齊 |
| 3 | `OFDM035` | 已寫 | §4.1 | **最深**(成對比較) | `BaseEVADaoPO` | 六層齊 |
| 4 | `OFDM036` | 已寫 | §4.1 | **最深**(成對比較) | `BaseEVADaoPO` | 六層齊 |
| 5 | `OFDM038` | 已寫 | §4.8 | 群組節 | `BaseMultiRowEVADaoPO` | 六層齊 |
| 6 | `OFDM039` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 7 | `OFDM040` | 已寫 | §4.6 | **深寫**(互斥鍵檢核三個洞) | `BaseEVADaoPO` | 六層齊 |
| 8 | `OFDM041` | 已寫 | §4.8 | 群組節 | `BaseMultiRowEVADaoPO` | 六層齊 |
| 9 | `OFDM045` | 已寫 | §4.2 | **深寫**(執行期死) | ⛔ `MultiRowEVAPO` | 六層齊 |
| 10 | `OFDM046` | 已寫 | §4.2 | **深寫**(執行期死) | ⛔ `BasicEVAPO` | 六層齊 |
| 11 | `OFDM054` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 12 | `OFDM055` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 13 | `OFDM061` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 14 | `OFDM062` | 已寫 | §4.4 | **深寫**(成對比較) | `BaseEVADaoPO` | 六層齊 |
| 15 | `OFDM064` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 16 | `OFDM065` | 表格帶過 | §4.9 | 分群表格 | `BaseEVADaoPO` | 六層齊 |
| 17 | `OFDM066` | 已寫 | §4.4 | **深寫**(成對比較) | `BaseEVADaoPO` | 六層齊 |
| 18 | `OFDM068` | 已寫 | §4.3 | **最深**(主從 + 覆寫 Add/Update + 跨表) | `BaseEVADaoPO`(覆寫 `Add`/`Update`) | 六層齊 |

**18 / 18 = 100%**。深寫 9 支、群組節 3 支、分群表格帶過 6 支。沒有「無關」或「停用」需要處置——但 2 支(`OFDM045` `OFDM046`)雖然在 csproj 裡,**執行期等同停用**。

四個子對話框另計:`OFDM045p0`(§4.2.3)、`OFDM062p0`(§4.4.2)、`OFDM066p0`(§4.4.2)、`OFDM068p0`(§4.3.1),四個都有進 `UI.OFD.csproj`,不在掃描索引裡(沒有自己的六層)。

### D.2 表的覆蓋率

| 對象 | 母體 | 本文明確引用 | 覆蓋 |
|---|---|---|---|
| 本片宣告的實體表 | 22 | 22(附錄 A.1 全列) | 100% |
| 外部唯讀表 | 10 | 10(附錄 A.2 全列) | 100% |
| 本片會寫的外部表 | 4 | 4(附錄 A.3) | 100% |
| 檢核用的交易表 | 7 | 7(附錄 A.4) | 100% |
| DB 物件 | 1 | 1(附錄 B) | 100% |
| 子對話框 | 4 | 4(§3.1) | 100% |
| 代碼組 | 20 | 20(附錄 C) | 100% |

### D.3 本文沒做到的事

| 項目 | 原因 |
|---|---|
| `dbTA` 是否真的永遠是 null | `Basic_PO` 無原始碼;需要實機跑 `OFDM045` / `OFDM046` 確認(§4.2.1) |
| `AGENT_ID` / `BF_COUNTRY_X` / `STATEMENT_CODE` / `SEND_CODE` 的完整值域 | 在 `CTL014` 表裡,**缺 DB 連線** |
| `A` 後綴的遷移規則是否全面 | 只在 `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/` 找到三組對照,不足以證明全面規則(§2.2) |
| `OFD063` 的 DataTable PK 只有一欄會不會真的拋 `ConstraintException` | 取決於框架有沒有關掉 `EnforceConstraints`,**框架無原始碼** |
| `DataModelUtility.Parameters` 的主鍵是不是 `Name` | 由 `Rows.Find` / `FindByName` 的用法反推,**無原始碼** |
| `OFDM068` 的 `AGENT_CODE + "%"` 配 `=` 到底影響多少筆資料 | 需要 DB 連線統計 `OFD070A` 的實際資料 |
| `OFD041` 與 `OFD041A` 兩張表的實際內容差異 | 需要 DB 連線(§附錄 E.6) |
| `xMaintainForm` / `LevelGridUtility` / `BaseEVADaoPO` / `xTableHelper` 的內部行為 | 框架 DLL,無原始碼,從呼叫端反推 |
| 選單上的正式中文畫面名 | 選單表不在版控內,本文的名稱來自 `_Ctl` 註解與欄位 Caption(§3.3) |

## 附錄 E. 讀本文時要注意的地方

15 條,依嚴重度排。

### E.1 `OFDM045` / `OFDM046` 繼承舊基底不覆寫,連查詢都 NRE —— 嚴重度 **高**

兩支的 PO 分別繼承 `MultiRowEVAPO` 與 `BasicEVAPO`,而這兩個基底的 `dbTA` 宣告即 `= null`、建構子賦值那四行整段被註解,`Add` / `Update` / `Delete` / `Select` / `GetMaintainData` / `GetToDoData` **每一支的第一行都是 `dbTA.CreateConnection()`**。

| 事實 | 錨點 |
|---|---|
| `dbTA = null` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:18` |
| 賦值被註解 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:164-172`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:171-174` |
| `Add` 第一行 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:187` |
| `Select` 第一行 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:795-797`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:717-728` |
| 子類沒覆寫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:6-17`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:14-25` |
| `_Ctl` 直接呼叫 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM045_Ctl.cs:32-66`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM046_Ctl.cs:37-79` |

**影響**:兩支畫面在執行期完全不能用。`OFD045`(KYC 問項)還在被 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:100` 讀,也就是**資料還在用、維護畫面卻壞了**。`OFD046` / `OFD047` 沒有任何外部讀者,壞了也沒人發現。

**佐證是舊世代未遷移**:兩支的 SQL 全是 T-SQL 語法(`[OFD045]` / `[OFD046]` 中括號、`ISNULL`、`CONVERT(NVARCHAR,…,111)`),錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM045_PO.cs:72-79`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:46`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:149`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:230`。就算 `dbTA` 修好,這些語法在 Oracle 上仍然跑不起來。

`ofd8.md` 找到 7 支、`ofdb.md` 找到 4 支同型,本片再加 2 支,**全庫累計至少 13 支**。

### E.2 `OFDM068` 把 `LIKE` 樣式餵給 `=`,非券商的銷售機構停用不會連動 —— 嚴重度 **高**

```
dbProduct.AddInParameter(cmd, "AGENT_CODE", OracleDbType.Varchar2,
                         AgentCode + (AgentID == "2" ? "" : "%"));
```

配上 `WHERE … AND OFD070A.AGENT_CODE = :AGENT_CODE`。

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:239`(值)+ `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:233`(`=`);境外版 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:264` + `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:258`。

**影響**:`AGENT_ID != '2'`(即銀行、產壽險等所有非券商)的銷售機構被改成「無效」時,`OFD070A` 與 `OFD070` 的 `AGENT_VALID_CODE` **完全不會被更新**——承銷基金設定還是有效,下游照樣讓那家機構下單。而且沒有錯誤訊息,`ExecuteNonQuery` 的回傳值也沒被檢查。

**對照組在同一支 PO 裡**:`CheckAgent` 用的是同一個 `AgentCode + (AgentID == "2" ? "" : "%")` 運算式,但那邊的 SQL 寫的是 `AGENT_CODE LIKE :AGENT_CODE`,是對的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:610-615`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:630`)。**複製貼上時搬了值、沒搬運算子**。

**修的時候要注意**:直接把 `=` 改成 `LIKE` 會讓「更新總行同時更新所有分支」這個原本註解裡說要做的行為**真的生效**,影響面比現況大得多,要先跟業務確認。

### E.3 `OFDM066` 的集保編號唯一性檢核四層都在、沒有呼叫端 —— 嚴重度 **高**

| 層 | 存在 | 錨點 |
|---|---|---|
| PO 介面 | 有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:29` |
| PO 實作 | 有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:242-269` |
| Control | 有 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM066_Ctl.cs:50-53` |
| FormProxy | 有 | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM066_Pxy.cs:25-30` |
| UI 呼叫 | **無** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:61-62` 只剩一個空的 `#region 原檢核集保公司編碼是否重複` |

還留了一個沒用到的區域變數 `OFDM066ViewVDB view = new OFDM066ViewVDB();`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:58`)——拆檢核時只拆了呼叫,變數宣告忘了刪。

**影響**:總代理公司的「集保公司編號」可以重複建立,不會被擋。對照組 `OFDM062` 的同一條檢核是有效的(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:75-86`)。**成對畫面只改一邊的教科書案例。**

### E.4 `OFDM040` 的身份別互斥檢核,值域外的值會誤擋、DB 出錯會放行 —— 嚴重度 **高**

`CheckData` 只寫了 `'00'` 與 `'01'`/`'02'` 兩個 `if`,沒有 `else`:值域外的 `BF_COUNTRY_X` 會讓 SQL 退化成「同 `STATEMENT_CODE` + 同 `OPEN_ACC_TYPE` 的全部筆數」,**任何一筆存在就誤擋**。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:259-271`。

`catch` 只記 log,`IsExit` 留在初值 `false`,**DB 出錯 = 沒有衝突 = 放行**。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:243`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:291-294`。

第四個參數 `m_SEND_CODE` 從頭到尾沒用到,三處相關程式被註解(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:262`、`:269`、`:279`)——原本設計是「連寄發碼一起比」,拆掉後簽名沒收。

### E.5 `OFD063` 的 DataTable 主鍵只有一欄 —— 嚴重度 **高**(標假設)

`OFDM062Model.xsd` 把 `OFD063`(基金公司聯絡人)的 `msdata:PrimaryKey` 定成只有 `FH_CD` 一欄:

```
<xs:unique name="OFD063_Constraint1" msdata:ConstraintName="Constraint1" msdata:PrimaryKey="true">
  <xs:selector xpath=".//mstns:OFD063" />
  <xs:field xpath="mstns:FH_CD" />
</xs:unique>
```

錨點 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD4/OFDM062Model.xsd:397-400`。

而這張表的業務是「一家基金公司多位聯絡人」——UI 還特地檢核「同一聯絡人作業別只能有一筆主要窗口」,代表同一家公司本來就會有多列。

**影響(標假設)**:只要框架沒有把 `DataSet.EnforceConstraints` 關掉,載入第二位聯絡人時 `LoadDataSet` 就會拋 `ConstraintException`。**缺:框架原始碼**,無法確定。

**對照組**:同型的 `OFD067`(總代理聯絡人)PK 是 `GAGENT_CD` + `DATAID` 兩欄,而且 `OFDM066` 新增明細列時明確 `row.DATAID = Guid.NewGuid()…`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:249`);`OFDM062` 新增明細列時**完全沒碰 `DATAID`**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:450-465`)。**又一個成對只改一邊。**

### E.6 `OFD041` 與 `OFD041A` 兩張同形表並存,兩個消費端讀到舊的 —— 嚴重度 **高**

`OFDM041` 維護的是 `OFD041A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM041_PO.cs:34`),但 `OFD041`(無 `A`)也是一張真的存在、有人在讀的表:

| 讀者 | 讀哪張 | 錨點 |
|---|---|---|
| `Utility_PO.GetCopyMemo`(基底) | **`OFD041A`** ✓ | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1788-1790` |
| `UtilityOracleDao.GetCopyMemo`(Oracle 覆寫,**同一支方法**) | **`OFD041`** ✗ | `Dev/Common/Source/Utility/TA.UtilityPO/Oracle/UtilityOracleDao.cs:1654-1656` |
| `OFDB238_PO.GetOFD041` | **`OFD041`** ✗,而且 `WHERE ACCOUNT_COPY = '14'` 寫死 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB238_PO.cs:1491-1492` |
| `BMSM006_PO` / `OFDM270_PO` / `OFDM337_PO` / `OFDB306_PO` / `OFDB324_PO` | `OFD041A` ✓ | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:913`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM270_PO.cs:339`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:275`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB306_PO.cs:124`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB324_PO.cs:121` |

**影響**:在 `OFDM041` 改的說明片語,對「載入片語清單」(Oracle 環境走 `UtilityOracleDao`)與 `OFDB238` 的說明帶出**完全不會生效**。基底與 Oracle 覆寫同一支方法讀不同表,是遷移時只改一半的典型。

`OFDM041` 把 vdb 名取成 `OFD041`(實體表卻是 `OFD041A`)讓這件事更難發現——搜 `OFD041` 會撈到一堆 vdb 用法。

### E.7 字串串接進 SQL —— 嚴重度 **高**(範圍廣)

12 支畫面的查詢條件、外加四段檢核 SQL,值都是直接串進字串。清單:

| 位置 | 錨點 |
|---|---|
| `OFDM030` 查詢條件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM030_PO.cs:144`、`:148` |
| `OFDM035` 查詢條件(主檔 + 明細) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM035_PO.cs:130`、`:134`、`:184`、`:188` |
| `OFDM036` 查詢條件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:136`、`:140`、`:147` |
| `OFDM036` 郵費 fallback 的 `'TWD'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:233` |
| `OFDM040` 查詢條件 ×3 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:188`、`:202`、`:216` |
| `OFDM046` 的 `AddParam`(連 `Like` 的 `%` 都自己包) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:220-233` |
| `OFDM054` 的 `AddParam` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM054_PO.cs:147` |
| `OFDM062` 查詢條件(主檔 + 明細) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:165`、`:169`、`:179`、`:183`、`:246`、`:250` |
| `OFDM064` 查詢條件 ×2 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM064_PO.cs:148`、`:152`、`:162`、`:166` |
| `OFDM065` 查詢條件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM065_PO.cs:138`、`:142` |
| `OFDM066` 查詢條件(**同一段重複兩次**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:146`、`:150`、`:160`、`:164` |
| `OFDM068` 明細查詢條件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:183`、`:187`、`:197`、`:201` |
| **`OFDM068.CheckDept` 的四段 SQL** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:701-702`、`:721-722`、`:740-741`、`:759-760` |

`CheckDept` 那四段最值得注意:`AGENT_CODE` 與 `AGENT_ID` 都是從用戶端 VDB 的參數表拿到的值,沒有任何清洗就串進 SQL。

**對照組**:同一批程式裡「後來加的」方法反而有參數化——`OFDM036.Get_POST_FEE`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:211`)、`OFDM034.CheckData`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:128`)、`OFDM040.CheckData`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:276-277`)、`OFDM062.IsFH_TSCD_CODExsits`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:280-281`)、`OFDM068.CheckAgent`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:624-630`)。**同一個檔案裡兩種寫法並存。**

### E.8 三條六層鏈的來源檔不是 UTF-8 —— 嚴重度 **中**

| 畫面 | 哪幾層是 `cp950`(Big5) |
|---|---|
| `OFDM034` | UI |
| `OFDM035` | UI、UI Designer、Control、PO(**整條鏈**) |
| `OFDM041` | PO |
| `OFDM061` | UI、PO |
| `OFDM062` | UI、PO |
| `OFDM066` | UI、PO |

其餘檔案是 `utf-8-sig`。**影響**:任何以 UTF-8 讀檔的工具(包含本文的掃描腳本)若不先偵測編碼,讀到的中文全是亂碼;混編碼也讓 diff 與 merge 容易出錯。`OFDM035`/`OFDM036` 這一對的編碼完全相反,正好變成判斷「誰先誰後」的證據(§4.1.2)。

### E.9 有訊息無 `return`,同一支檔案兩條路徑不一致 —— 嚴重度 **中**

| 位置 | 內容 | 錨點 |
|---|---|---|
| `OFDM030` 修改 | `e.Cancel = true` 後**沒有 `return`**,後面 10 行照樣把畫面值寫回 Row;同檔的新增路徑有 `return` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:140-150` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:113-118` |
| `OFDM034` 新增 / 修改 | 同樣 `e.Cancel = true` 後沒 `return`,繼續把六個欄位寫回 Row | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:100-109` |
| `OFDM062` 新增 | `'0000000000'` 時 `e.Cancel = true` 但沒 `return`,繼續跑 `DoValidate()`;同型的 `OFDM066` 有 `return` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:372-378` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:175-180` |
| `OFDM062` 集保編號查詢出錯 | 只 `ShowMessage`,**不 `AddError`** → `ValidateErrList.Show()` 回 false → 存檔照走 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:78-81` |

### E.10 檢核的 `catch` 把 DB 錯誤當成「沒問題」—— 嚴重度 **中**

| 方法 | `catch` 做什麼 | 結果 | 錨點 |
|---|---|---|---|
| `OFDM040.CheckData` | 只記 log,`IsExit` 留 `false` | 沒有衝突 → 放行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM040_PO.cs:291-294` |
| `OFDM062.IsFH_TSCD_CODExsits` | 回 `-1` | UI 只跳訊息不 `AddError` → 放行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:288-292`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:78-81` |
| `OFDM068.CheckAgent` | `AddResultRow(false, 0, "")` | 筆數 0 → 沒有交易 → 准刪 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:646-651` |
| `OFDM068.CheckDept` | `Result.Clear()` + `AddResultRow(false, 0, "")` | 四個代碼都對不上 → 不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:775-780` |
| `OFDM036.Get_POST_FEE` | `AddResultRow(false, 0, "")` | UI 端不看 `ReturnCode`,只看 `Rows.Count == 0 ? 0 : …` → 郵費填 `0` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM036_PO.cs:245-250`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:139` |
| `OFDM046` 的 `BeforeAdd` 取號 | 只記 log,`DataSeq` 留 `0` | 主檔與所有明細都被塞 `0` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:62-66` |

**唯一的反例**是 `OFDM034.CheckData`:UI 端看 `ReturnCode == false` 就 `e.Cancel = true`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:128-132`),方向對。

### E.11 `OFDM035` 的明細沒設 `STATUS`,成對的另一支有 —— 嚴重度 **中**

`OFDM036` / `OFDM062` / `OFDM066` 三支都在把主檔鍵下推到明細時多寫一行 `row.STATUS = MasterRow.STATUS;`,而且都留了同一句註解「STATUS 也要給」:

| 畫面 | 錨點 |
|---|---|
| `OFDM036` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:64` |
| `OFDM062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:117` |
| `OFDM066` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM066.cs:86` |

`OFDM035` 的對應迴圈只設 `BANK_HQ` 與 `CRNCY_CD`,**沒有 `STATUS`**,也沒有那句註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:126-132`)。

**影響**:`OFD036A` 是有四眼欄位的表,`'ALL'` 那一半的明細列四眼狀態要靠框架自己補,與另一半的行為不一致。實際會不會出事取決於 `xEVAUtility` 的預設,**標假設**。

### E.12 `EFFECT_YN` 設成無效,虛擬帳號照樣產生 —— 嚴重度 **中**

`OFD030.EFFECT_YN` 的 Caption 是「有效銀行帳號 Y/N」,但:

- `OFDM030` 對這個欄位**沒有任何檢核或連動**,純欄位。

- 下游的 `GET_REMIT_ACC_NO` 撈 `OFD030` 時 `WHERE` 只有 `BANK_HQ = XREMIT_BANK_CD`,**沒有過濾 `EFFECT_YN`**(`DB/Function/GET_REMIT_ACC_NO.SQL:30-33`)。

**影響**:把一個入款銀行帳戶標成「無效」,並不會讓該行的受益人虛擬帳號停止產生。**標假設**:`EFFECT_YN` 的業務意圖是停用;若實際意圖只是註記,那就沒問題——**缺:業務規格**。

### E.13 `OFDM036` 的 `SetMasterToDetail()` 在 `e.Cancel` 之後照跑 —— 嚴重度 **中**

```
if (this.ValidateErrList.Show())
    e.Cancel = true;
else
{ … MasterRow.BANK_HQ = …; MasterRow.POST_FEE = …; }
this.SetMasterToDetail();     // ← 在 if/else 外面
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:125-143`。

**影響**:檢核失敗時 `MasterRow` 的值還沒更新,卻已經把舊值 / 空值塞進所有明細列。使用者修正後再存一次會被覆寫回來,但中途切頁 / 取消就留下不一致的暫存資料。對照組 `OFDM035` 把整段放在 `else` 內(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:119-133`)。

### E.14 Oracle 三值邏輯:`欄 <> '值'` 遇 NULL —— 嚴重度 **中**

本片有四處 `<>`,全部有三值邏輯風險:

| 位置 | SQL 片段 | 是否發作 | 錨點 |
|---|---|---|---|
| `OFDM034.AfterUpdate` → `OFD068A` | `(AGENT_NAME <> :AGENT_NAME OR AGENT_NAME_E <> :AGENT_NAME_E OR AGENT_SHNM <> :AGENT_SHNM)` | **會**——`OFD068A` 的名稱欄允許 NULL,三欄都 NULL 時整個 `OR` 是 UNKNOWN,該列不更新 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:74` |
| `OFDM034.AfterUpdate` → `OFD071A` | `CHANNEL_DESCRP <> :CHANNEL_DESCRP` | **會**——同理 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:93` |
| `OFDM062.IsFH_TSCD_CODExsits` | `FH_CD <> :FH_CD` | 目前不發作(`FH_CD` 是 PK,UI 端必填) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM062_PO.cs:275` |
| `OFDM066.IsTSCD_AGENT_CDxsits` | `GAGENT_CD <> :GAGENT_CD` | 不發作(**因為根本沒人呼叫**,見 E.3) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:249` |
| `OFDM068.CheckDept` ×4 | `AGENT_CODE <> '<串接值>'` | 目前不發作(UI 端 `AGENT_CODE` 必填且先 `return`),但順序一改就發作;Oracle 的 `''` 即 NULL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:701`、`:721`、`:740`、`:759` |

「八個模組中過」的這一型,本片前兩條是**實際會發作**的。

### E.15 其他小坑彙整 —— 嚴重度 **低 ~ 中**

| # | 內容 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `OFDM068.CheckDept` 的 UI 端把同一個 `IVR_DEPT_OFD` 參數 `AddParametersRow` 兩次,會撞 `Parameters` 的主鍵 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:139-146` | 中(標假設) |
| 2 | `OFDM068.CheckDept` 四個結果全部 `AddError` 到 `ucomEC_DEPT_NFD`,紅框永遠在同一格 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM068.cs:152-170` | 低 |
| 3 | `OFDM068.Update` 的明細三段「影響筆數」檢核全被註解,主檔那段沒被註解 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:502-503`、`:524-525`、`:544-545` vs `:472-473` | 中 |
| 4 | `OFDM068.UpdateAGENT_VALID_CODE` 的 `catch` 先 `tran.Rollback()` 再吞掉,呼叫端不知情繼續 `Commit()` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:274-278`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:553` | 中 |
| 5 | `OFDM068.Add` 的 `i +=` 累加讓「明細一列都沒寫」也判成成功 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs:325-333`、`:385` | 中 |
| 6 | `OFDM034_PO` 1192 行裡 1043 行是被 `/* */` 註解的舊實作(**87.5 % 死碼**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:144-145`、`:1187-1189` | 中 |
| 7 | `OFDM039_PO` 1007 行裡 943 行是被 `//` 註解的舊實作(**93.6 % 死碼**),而且檔尾是 `}//end namespace Adapterusing System;` 這種合併殘留 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM039_PO.cs:60-1002`、`:1007` | 中 |
| 8 | `OFDM034.CheckData` DB 出錯時擋住刪除**但訊息是空字串**,使用者看到空白對話框 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM034_PO.cs:138`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM034.cs:130` | 中 |
| 9 | `OFDM045` 的 `KYC_ITEM` 自動編號用完 19 個字母後**留空字串**,不擋不提示,直接送去撞 PK | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM045.cs:175-185` | 中 |
| 10 | `OFDM046` 附件多選只取第一個檔,其餘靜默丟棄 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:92-103` | 中 |
| 11 | `OFDM046` 附件下載同名檔直接覆寫,不問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM046.cs:123-132` | 低 |
| 12 | `OFDM062` 的 `IsDuplicateError()`(同作業別只能一筆主要窗口)**只在修改路徑呼叫**,新增路徑沒有 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:392` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:370-386` | 中 |
| 13 | `OFDM062` 主檔查詢用 `Like` 且**不判空字串**,空條件變成 `Like '%'`;同片其他畫面都有判 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM062.cs:366-367` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:106` | 低 |
| 14 | `OFDM061_PO` 有一行 `dbProduct = dbProduct;` 自我指派;`AfterUpdate` body 只有 `//nothing` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM061_PO.cs:48`、`:63-66` | 低 |
| 15 | `OFDM038` 的明細把基金簡稱與警示備註 `\|\|` 串成同一欄,下游拆不開 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM038_PO.cs:84` | 低 |
| 15b | `OFDM066_PO.BuildMasterSQLString` 把「`GAGENT_CD` 查詢條件」整段**原封不動複製了兩次**,同一個條件會被 append 兩遍(`… And OFD066.GAGENT_CD = 'x' And OFD066.GAGENT_CD = 'x'`)。結果不會錯,但多一次比對,也代表這支 PO 沒人再看過 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:140-153` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM066_PO.cs:154-167` | 低 |
| 16 | `OFDM030` 的 `AfterAddButtonClicked` 又跑一次 `DoValidate()`,與 `BeforeAdd` 重複 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM030.cs:183-191` | 低 |
| 17 | `OFDM036` 的存檔 handler 叫 `BeforeAddModityButtonClicked`(`Modity` 拼錯) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:123` | 低 |
| 18 | `OFDM046.BuildDetailSQLString` 若表名不是 `OFD047`,組出來的 SQL 會缺整段欄位清單 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:173-192` | 低 |
| 19 | `OFDM035` / `OFDM036` 改 `REMIT_MAX` 時用 `DataTable.Select("REMIT_AMT1>=" + …)` 字串串接組條件 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM035.cs:242`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM036.cs:260` | 低 |
| 20 | 寫死常數彙整:`'ALL'`、`'0000000000'`、`'TWD'`、`'5'`、`'00'`/`'01'`/`'02'`、`'334'`/`'335'`、`'150'`、`'073'`、`'99'`、`'01'`(境內對帳單)、`'14'`(OFDB238 的片語名稱)、19(KYC 項數)、5(集保代碼長度)、8(SWIFT 長度)。全部沒有走 MappingCode 常數類別 | 見附錄 C | 中 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD4` 的 18 支 M 畫面、22 張實體表、15 條缺陷。重點結論:`A` 後綴在本片是 MSSQL→Oracle 遷移改名而非境內外(§2.2);`OFDM035`/`OFDM036` 靠 `BANK_HQ='ALL'` 切分同一組表(§4.1);`OFDM045`/`OFDM046` 執行期必 NRE(§4.2);`OFDM068` 的 `=` 配 `%` 讓非券商停用不連動(附錄 E.2) |

由 build_doc.py v2.0.0 於 2026-09-15 14:01 產生 · 標題 104 · 圖 5 · 表格 81 · 程式錨點 555 · § 連結 78 · 引用檢查：畫面 23（缺 0） · Table 40（缺 0） · 結果集 7（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofd5.md
============================================================

# ATLAS OFD5 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先翻 §1 的圖抓全貌,再讀 §2.2 把「`A` 字尾 = 境內、無 `A` = 境外」這條規律跟它的三個例外搞清楚(這是本片最容易誤判的地方),之後 §3 的清冊配 §4 起的畫面章節就讀得動了。**急著知道哪支會咬人的直接跳附錄 E**。

> ⚠ **OFD5 不是一個業務模組,是一份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/` 這個 Entity 專案底下、且被指派給本片的 **17 支 M 畫面**。切片的依據是 Entity 專案資料夾,不是業務;所以本片內部含**五條業務線**(§0.1)。名稱 `OFD5` 為**推測**,取自資料夾名。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的常數字典**推測**,待選單表回填。畫面中文名全部**待選單表回填**,本文用「用途(推測)」代替。

> ⚠ **〔客戶特定〕**:境內外代碼 `'1'`/`'2'`、郵局代碼 `'700'`、業務別 `'ALL'`、`FND001` 表、MSSQL 連線名 `"FA"` 與預存程序 `S_PAM_OFD081A_AFIZZ020` 為本站台的值。

> ⚠ **〔共用〕**:`OFD081A` `OFD081` `OFD0811A` `OFD074` `OFD075` `OFD071A` `OFD072A` `OFD085` `OFD086` `OFD091` 同時服務 Common / BMS / RSP / EC / OFDB / OTA(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)與 PO 基底看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 17 支畫面管什麼(推測)

先給結論:**本片沒有單一業務主題,是「基金與它的通路 / 扣款環境」這個大範圍底下的五塊設定檔維護**。17 支全部是 M 型維護畫面,全部在 `Dev/ATLAS.OFD` 專案。

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 基金主檔** | `OFDM081A` `OFDM081B` | 一檔基金的所有靜態屬性:名稱、成立日、幣別、手續費收取方式、贖回方式、定期定額參數、保管銀行、入款帳號… | `OFDM081AModel.xsd` 主表 119 欄、`OFDM081BModel.xsd` 主表 173 欄,Caption 幾乎全填 |
| **B 基金交易參數** | `OFDM084` `OFDM082` `OFDM082B` `OFDM087` `OFDM088` `OFDM091B` | 掛在基金代碼上的六張小設定表:可交易幣別、報表排序、暫停申贖期間、基金行事曆、I Share 額度 | 各表主鍵都以 `FUND_ID` 開頭;Caption「交易別」「報表排序順序」「基金資料來源」「I SHARE額度」 |
| **C 轉換與配息再投資** | `OFDM085A` `OFDM085B` `OFDM086` | 一檔基金可以轉去哪一檔、費率怎麼算、配現要不要再投資、專戶帳號是哪一個 | 主鍵一律 `FUND_ID` + `SWITCH_FUND_ID`;Caption「轉入基金代碼」「內扣轉換費率」「配股基金」 |
| **D 銷售通路與推薦人** | `OFDM070A` `OFDM070B` `OFDM071` `OFDM072` | 銷售機構跟哪一檔基金簽了約、通路的三層樹(大 / 中 / 小)、推薦人與其歸屬 | Caption「銷售機構別」「手續費拆帳比-銷售機構」「通路代碼」「推薦人代碼」;`OFDM071` 用 5 / 9 / 15 碼判層級 |
| **E 扣款機構** | `OFDM074` `OFDM076` | 核印扣款機構與代理扣款機構的簽約內容、可扣款的基金、可扣款的幣別與扣帳手續費 | Caption「扣款機構」「核印扣款方式」「代理扣款機構」「每日扣款限額」;兩支共用同一張幣別明細 `OFD078` |

五塊之間**沒有任何跨塊的程式呼叫**,只有一條共同的鍵:全部掛在 `FUND_ID` 或 `AGENT_ID` 上。讀 OFD5 的人如果預期整片是一條流程,會在 §4.3 之後對不上——先知道這件事比較省時間。

### 0.2 不管什麼

| 不在 OFD5 | 在哪 | 依據 |
|---|---|---|
| 基金手續費率階梯(牌告 / 對象別) | `OFDM191`~`OFDM198`(OFD7 片) | `ofd7.md §0.1` 的 A / B 塊 |
| EC 促銷活動與優惠次數 | `OFDM199` `OFDM204` `OFDM206`(OFD7 片) | `ofd7.md §4.9`~`§4.11` |
| `OFDM084B`(境外可交易幣別) | 檔案在 `Dev/ATLAS.OFD`、Model 在 `DataEntity.OFD5`,但**不在本片指派的 17 支名單內** | 本文在 §4.5 與附錄 D 只做對照,不深寫 |
| `OFDM091`(境內 CDSC 費率區間) | `DataEntity.OFD8` | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM091Model.xsd`;**它不是 `OFDM091B` 的境內版**,見 §2.2.6 |
| 一次把基金與它的六張設定表建起來 | 批次 `OFDB004` | `ofd7.md §8.4` 記的同一支批次 |
| 基金主檔資料拋轉到官網 CMS | 程式碼**整段被註解** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:202-207` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:265-300` |
| `FND001` 這張表本身的定義與其他寫入者 | 版控外(`DB/Table/` 底下沒有這張表的腳本) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:311-784`,repo 內只看得到 `OFDM081A` 在寫 |
| MSSQL 預存程序 `S_PAM_OFD081A_AFIZZ020` 的內容 | 版控外(連線名 `"FA"`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:799-808`,已加進 meta 的 `refcheck-ignore` |
| 基金淨值、交易、庫存 | `OFD221A` / `RSP006A` 等交易表,本片只拿來當「能不能刪」的判準 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:871-879` |

### 0.3 使用角色

17 支全部走標準四眼(輸入 / 驗證 / 覆核),角色由平台的 ToDo 機制指派,OFD5 自己不定義角色——所有走四眼的 PO 都只是把 `xTableHelper.AppendToDoString(...)` 接到查詢字串尾巴(例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:199-202`)。詳見 `architecture.md §3`。

**兩個例外,實際上完全不經四眼**:

| 入口 | 做什麼 | 錨點 |
|---|---|---|
| `OFDM082` 的「排序」按鈕 | 自己開交易,直接 `UPDATE OFD0814A SET REPORT_SEQ` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:63-79` |
| `OFDM082B` 的「排序」按鈕 | 自己開交易,直接 `UPDATE OFD081 SET REPORT_SEQ`,**改的是境外基金主檔本身** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:66-70` |

這兩段只寫 `UPDATEID` / `UPDATEDATE`,**`STATUS` / `ENTRYID` / `VERIFYID` / `APPROVEID` 原封不動**。也就是說:一筆已覆核的基金資料,排序被改過之後看起來還是「已覆核」,而且沒有任何人覆核過那個排序值。詳見 §4.3 與附錄 E.1。

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(讀) | `OFD062`(基金公司)、`FSK003`(幣別)、`OFD020V`(銀行分行)、`OFD064`(基金公司收款銀行)、`OFD027A` 等 | 全部是 `LEFT JOIN`,只取說明欄 |
| 上游(判斷用) | `OFD221A` / `OFD221`(交易)、`RSP006A` / `RSP006`(定額約定) | 只做 `COUNT(1)`,判斷基金能不能刪 |
| 下游(寫,同一個 Oracle 交易內) | **`FND001`** —— 只有 `OFDM081A`(境內)會同步,`OFDM081B`(境外)不會 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:311-784` |
| 下游(寫,**交易外的 MSSQL**) | 預存程序 `S_PAM_OFD081A_AFIZZ020`,由 `OFDM081A_Ctl` 在 PO 回來之後才呼叫 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:66`、`:91`、`:342` |
| 下游(本片的表被誰讀) | Common 共用 PO、`ATLAS.OFDB`、`ATLAS.RSP`、`ATLAS.BMS`、`ATLAS.EC`、`ATLAS.OTA`、`ATLAS.OTAB`、各 `.Query` / `.Report` | 見 §8 |
| 平行(同一張表兩個維護入口) | `OFD0814A`:`OFDM081A` 當明細維護(vdb 名 `OFDM081A_NOEVA`)+ `OFDM082` 直接 UPDATE;`OFD081`:`OFDM081B` 走四眼 + `OFDM082B` 直接 UPDATE;`OFD084A`:`OFDM084` 主維護 + `OFDM081A` 當第 7 張明細 | §8.5 |

### 0.5 全域開關

本片沒有 `App.config` 層級的業務開關。真正決定行為的三個「開關」都是資料欄位或寫死常數:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `FUND_TYPE` / `SHORE_ID`(境內外) | `'1'` 境外 · `'2'` 境內 | 決定一支畫面 join `OFD081` 還是 `OFD081A`;`OFDM087` / `OFDM088` 兩支用它在同一個畫面切換來源 | 值域出處 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FUND_LOCK`(資料鎖定) | `'Y'` / 其他 | `'Y'` 時 `OFDM081A` 不同步 `FND001`,UI 也擋掉修改 / 刪除 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:318-322`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1309-1312` |
| `BANK_SUB_TYPE = 'ALL'`(業務別) | 寫死字串 | `OFDM076` 對共用表 `OFD078` 只看 `'ALL'` 這一種業務別,`OFDM074` 則看實際業務別 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:338` |

`FUND_TYPE` 的 `'1'`=境外 / `'2'`=境內在本片有**三處獨立佐證**,不是靠 `ofd7.md` 的轉述:

| # | 佐證 | 錨點 |
|---|---|---|
| 1 | `SHORE_ID.OnShore = "2"`(註解「2:境內基金」)、`SHORE_ID.OffShore = "1"`(註解「1:境外基金」) | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| 2 | `OFDM087` 的檢核 SQL 明寫 `AND '2' = :FUND_TYPE … FROM OFD081A` / `AND '1' = :FUND_TYPE … FROM OFD081` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:366-380` |
| 3 | `OFDM088` 的 CTE 明寫 `'2' AS FUND_TYPE FROM OFD081A` / `'1' AS FUND_TYPE FROM OFD081` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:60-77` |

另有一處把值域直接寫進下拉清單:`OFDM070A` 的 Grid 下拉 `ValueListItem("1", "境外基金")` / `ValueListItem("2", "境內基金")`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:84-86`),與字典一致。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD5 全景：基金主檔、交易參數、轉換、通路、扣款機構五條線與下游
圖中文字:A 基金主檔：一條業務兩張表，A 字尾=境內、無 A=境外 / OFDM081A 境內 / OFD081A + 8 張明細 / OFDM081B 境外 / OFD081 + OFD082 OFD083 / FND001〔外部〕 / 覆核後同步 只有境內做 / CMS 官網 API / 整段被註解 沒在跑 / B 基金交易參數：掛在基金代碼上的六張設定表 / OFDM084 境內 / OFD084A 可交易幣別 / OFDM087 兩邊都收 / OFD087A 暫停申贖 / OFDM088 兩邊都收 / OFD088A 基金行事曆 / OFDM091B 境外 / OFD091 I Share 額度 / OFDM082 境內 / 寫 OFD0814A 報表排序 / OFDM082B 境外 / 直接寫 OFD081 主檔 / OFDM084B 境外 / OFD084 不在本片名單 / C 轉換與配息再投資：三支同型，085B 與 086 幾乎是同一份程式 / OFDM085A 境內 / OFD085A 轉換+再申購專戶 / OFDM085B 境外 / OFD085 轉換 / OFDM086 境外 / OFD086 配現再投資 / ATLAS.OTA 交易端 / OFD085 OFD086 唯讀取用 / D 銷售通路與推薦人：070A/070B 也是境內外一對 / OFDM070A 境內 / OFD070A 機構x基金簽約 / OFDM070B 境外 / OFD070 機構x基金簽約 / OFDM071 / OFD071A 通路 5/9/15 碼 / OFDM072 / OFD072A 推薦人 / E 扣款機構：兩支畫面共用同一張幣別明細 OFD078 / OFDM074 核印扣款 / OFD074 + OFD075 + OFD078 / OFDM076 代理扣款 / OFD076 + OFD077 + OFD078 / OFD078〔共用〕 / 靠業務別碼分流 076 寫死 ALL / 兩條寫入路徑 / 卡控不同 鍵不同 / 下游：這 17 支全是設定檔，真正用它們的是交易與批次 / ATLAS.OFDB 批次 / OFD074 OFD085A 一起建 / ATLAS.RSP 定額 / OFD071A OFD072A OFD074 / ATLAS.BMS 開戶 / OFD074 扣款行檢核 / Common 共用 PO / OFD081A OFD0811A 常被 join
```

*圖:圖 1 OFD5 全景。橘框=本片的維護入口;橘虛框=風險或寫死;灰虛框=別的模組或不在本片名單;黑框=無原始碼或已被註解。五條線全部掛在「基金代碼」這一個鍵上，A 是源頭、B C 是掛在基金上的參數、D E 是掛在機構上的參數。*

### 1.2 資料表關係與境內外配對

圖放在 §2 的開頭(`ofd5.figs.py` 的 `h2:2-`)。一句話總結:**判準不是表名有沒有 `A` 字尾,是「這支畫面 join 的是 `OFD081A` 還是 `OFD081`」**;五對成立,三支對不上(§2.2)。

### 1.3 主要維護畫面的四眼與卡控順序

圖放在 §4 的開頭(`h2:4-`),以本片最重的 `OFDM081A` 為例。一句話總結:**卡控幾乎全在 UI 的 `DoValidate()`,伺服端只有「查得到 / 查不到」這種 `COUNT(1)` 型的輔助查詢,沒有任何一支掛 `BeforeAdd` / `BeforeUpdate` 攔截。**

另外一張圖(`h2:3-`)按 PO 基底把 17 支分群:`BaseEVADaoPO` 8 支、`BaseMultiRowEVADaoPO` 7 支、掛著 `BaseEVADaoPO` 卻完全不用四眼的 2 支。

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。最接近批次的是三個掛在 M 畫面上的功能鈕:`OFDM088` 的「整年建立行事曆」/「複製行事曆」/「設定假日」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM088.cs:426-464`),它們一次寫一整個月或一整年的資料,走的是 PO 上的自訂方法而不是 B 型畫面。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——17 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM081A` 覆核後同步 `FND001`(§4.1.5),但同步是同一個交易內的同步呼叫,不是排程,畫不出泳道。

## 2. 資料模型

```text
[圖] OFD5 的境內外配對驗證：五對成立、三支對不上，以及其餘表的歸屬
圖中文字:基金主檔兩張：所有配對的真正判準是「這支畫面 join 哪一張」 / OFD081A 境內基金主檔 / FUND_TYPE '2' / SHORE_ID.OnShore / OFD081 境外基金主檔 / FUND_TYPE '1' / SHORE_ID.OffShore / CTL014.cs:291-301 / 值域唯一出處 / OFDM087_PO:371-380 / '2'=OFD081A '1'=OFD081 / 五對同型畫面：左欄掛 OFD081A，右欄掛 OFD081 / OFD081A ← OFDM081A / 8 明細 119 欄 / OFD081 ← OFDM081B / 2 明細 173 欄 / 規律成立 / 但欄位形狀差很多 / PO 相似度 23% / UI 相似度 15% / OFD070A ← OFDM070A / 45 欄 含拆帳與取款 / OFD070 ← OFDM070B / 35 欄 含彙入與公會 / 規律成立 / Ctl 層 100% 相同 / 訊息沒改 / 境外也說「境內」 / OFD0814A ← OFDM082 / 報表排序 掛在明細表 / OFD081 ← OFDM082B / 報表排序 直接寫主檔 / 規律成立 / 但寫入的層級不同 / PO 相似度 85% / 參數物件用錯 db / OFD085A ← OFDM085A / 64 欄 轉換+再申購 / OFD085 ← OFDM085B / 31 欄 只有轉換 / 規律成立 / 境內多一整塊再申購 / PO 相似度 50% / Ctl 相似度 22% / OFD084A ← OFDM084 / 主鍵少了 OPEN_TYPE / OFD084 ← OFDM084B / 主鍵含 OPEN_TYPE / 規律成立 / 084B 不在本片名單 / 明細 INNER JOIN / 境內是 LEFT JOIN / 規律對不上的三支：代號有 A/B 但不是境內外配對 / OFD091 ← OFDM091B / I Share 額度 境外 / OFD091A ← OFDM091 / CDSC 費率區間 境內 / 不成立 / 兩張表業務完全不同 / OFDM091 在 OFD8 / 不在本片 / OFD088A ← OFDM088 / A 字尾卻兩邊都收 / OFD087A ← OFDM087 / A 字尾卻兩邊都收 / 部分成立 / 用 UNION 或 DECODE 併 / OFD074 OFD075 / 無 A 卻是境內 / 本片 21 張實體表的其餘：掛在 081A/081 之下或獨立 / OFD0811A OFD0813A OFD0814A / OFD0819A OFD082A OFD094A OFD095A / OFD082 OFD083 / 境外經理費/保管費階梯 / OFD071A OFD072A / 通路 / 推薦人 獨立 / OFD074~OFD078 / 扣款機構群
```

*圖:圖 2 境內外配對。白框=事實;橘虛框=風險或例外;灰虛框=不在本片。判準不是表名有沒有 A，而是「這支畫面 join 的是 OFD081A 還是 OFD081」——OFD074 OFD075 OFD077 沒有 A 卻只 join OFD081A，是規律的反例。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

17 支畫面共宣告 **21 張實體表**。宣告方式分三派,差別很大:

| 派別 | PO 基底 | 特徵 | 本片畫面 | 支數 |
|---|---|---|---|---|
| **單筆型** | `BaseEVADaoPO` | `MasterTable` 單一 + `DetailTable` 清單 | `OFDM071` `OFDM072` `OFDM074` `OFDM076` `OFDM081A` `OFDM081B` `OFDM087` `OFDM091B` | 8 |
| **多筆型** | `BaseMultiRowEVADaoPO` | `MasterTable` 是 `List`,**沒有明細概念**;主從其實是同一張表,靠 `MasterPKey` 分群,畫面上半是「群」下半是「群內各列」 | `OFDM070A` `OFDM070B` `OFDM084` `OFDM085A` `OFDM085B` `OFDM086` `OFDM088` | 7 |
| **掛四眼基底卻不用四眼** | `BaseEVADaoPO` | 建構子**空的**,既沒宣告 `MasterTable` 也沒掛任何事件;所有事情靠兩支自訂方法自己開交易做 | `OFDM082` `OFDM082B` | 2 |

兩派的差別見 `architecture.md §3.9`。**多筆型沒有明細表這件事很容易看錯**——`atlas_scan.py --screen OFDM070A` 報「明細 —」不是漏掉,是真的沒有。

逐支的宣告:

| 畫面 | 基底 | 主檔(實體表 → vdb 名) | 明細 | `MasterPKey` | 錨點 |
|---|---|---|---|---|---|
| `OFDM070A` | 多筆 | `OFD070A` → `OFDM070A` | — | `AGENT_ID` `AGENT_CODE`(`SHORE_ID` 被註解) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:37-41` |
| `OFDM070B` | 多筆 | `OFD070` → `OFDM070B` | — | `AGENT_ID` `AGENT_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070B_PO.cs:43-45` |
| `OFDM071` | 單筆 | `OFD071A` → `OFDM071` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:41` |
| `OFDM072` | 單筆 | `OFD072A` → `OFDM072` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM072_PO.cs:34` |
| `OFDM074` | 單筆 | `OFD074` → `OFDM074` | `OFD075` → `OFDM074_Detail` · **`OFD078` → `OFDM078`** | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:49-51` |
| `OFDM076` | 單筆 | `OFD076` → `OFDM076` | `OFD077` → `OFDM076_Detail` · **`OFD078` → `OFDM078`** | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:51-53` |
| `OFDM081A` | 單筆 | `OFD081A` → `OFDM081A` | 八張,見 §2.3 | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:43-53` |
| `OFDM081B` | 單筆 | `OFD081` → `OFDM081B` | `OFD082` → `OFDM081B_082` · `OFD083` → `OFDM081B_083` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:47-49` |
| `OFDM082` | **不用四眼** | 無宣告(SQL 內寫死 `OFD0814A`) | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:26-33` |
| `OFDM082B` | **不用四眼** | 無宣告(SQL 內寫死 `OFD081`) | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:32-39` |
| `OFDM084` | 多筆 | `OFD084A` → `OFDM084` | — | `FUND_ID` `TRADE_CD`(`OPEN_TYPE` 被註解) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:29-32` |
| `OFDM085A` | 多筆 | `OFD085A` → `OFDM085A` | — | `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:33-34` |
| `OFDM085B` | 多筆 | `OFD085` → `OFDM085B` | — | `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085B_PO.cs:34-35` |
| `OFDM086` | 多筆 | `OFD086` → `OFDM086` | — | `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM086_PO.cs:34-35` |
| `OFDM087` | 單筆 | `OFD087A` → `OFDM087`(**用區域變數繞一手**) | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:48-49` |
| `OFDM088` | 多筆 | `OFD088A` → `OFDM088` | — | 無(只靠 SQL 分群) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:35` |
| `OFDM091B` | 單筆 | `OFD091` → `OFDM091B` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:49` |

> ⚠ **掃描器對三支畫面報「主檔 —」,其中只有兩支是真的沒有。** `atlas_scan.py --screen OFDM087` 報「主檔 —」是**誤判**:`OFDM087_PO` 先把 `xTableMapping` 指派給區域變數 `tp`,再 `this.MasterTable = tp;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:48-49`),掃描器的樣式比對抓不到這種寫法。真正沒有宣告的只有 `OFDM082` 與 `OFDM082B`,它們是**故意不用四眼管線**(§4.3)。

### 2.2 `A` / `B` 後綴 = 境內 / 境外:逐對驗證

本片有五對「同型畫面」。驗證方法照 `ofd7.md §4`:把 A 側的代號整批代換成 B 側的代號後逐行 diff 算相似度,再看**主檔 SQL join 的是 `OFD081A`(境內)還是 `OFD081`(境外)**。後者才是判準,前者只說明兩支是不是抄來抄去的。

**總結:五對全部成立,而且五對的 join 對象零例外。** 但「表名有沒有 `A` 字尾」這個更粗的規律**有三個反例**(§2.2.6~§2.2.8)。

#### 2.2.1 `OFDM081A` / `OFDM081B` —— 相似度最低的一對

| 面向 | `OFDM081A`(境內) | `OFDM081B`(境外) |
|---|---|---|
| 主檔實體表 | `OFD081A` | `OFD081` |
| 主檔 SQL join | 只有 `OFD081A` 自己 | 只有 `OFD081` 自己 |
| 主表欄數(xsd) | 119 | 173 |
| 明細數 | 8 | 2 |
| PO 行數 / 代號代換後相似度 | 1,808 | 577 / **23.1%** |
| UI 行數 / 相似度 | 3,067 | 2,217 / **15.1%** |
| Ctl 行數 | 1,754 | 366 |

**這一對不是抄的,是兩套獨立實作。** 境內版多了 `FND001` 外部同步、`Copy` 複製基金、八張明細;境外版多了一整批「集保申報 / 核備 / 傘型架構 / SWIFT 匯款資訊」的檢核(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:59-442` 一支 `DoValidate()` 內有 57 條 `AddError`,境內版同一支只有 16 條)。

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:43` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:47`。

#### 2.2.2 `OFDM070A` / `OFDM070B` —— 相似度最高的一對,而且訊息只改了一半

| 面向 | `OFDM070A`(境內) | `OFDM070B`(境外) |
|---|---|---|
| 主檔實體表 | `OFD070A` | `OFD070` |
| 主檔 SQL join | `LEFT JOIN OFD081A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:128-131`) | `LEFT JOIN OFD081`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070B_PO.cs:116-119`) |
| 主表欄數 | 45(多:手續費拆帳、取款分行 / 帳號、特殊期間、CDSC 傳輸方式) | 35(多:交易資料彙入處理三欄、申報集保碼、公會核准日期 / 文號) |
| PO 相似度 | — | **80.7%**(196 / 251 行完全相同) |
| UI 相似度 | — | **83.4%** |
| **Ctl 相似度** | — | **100.0%**(223 / 223 行,代號代換後一字不差) |

**`OFDM070B` 的存檔錯誤訊息沒有跟著改**:境外畫面跳出來的字是「銷售機構承銷**境內**基金設定明細資料 必須輸入」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070B.cs:53`),跟境內版(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:53`)完全同一句。這是本片「成對畫面只改一邊」最乾淨的一個實例(附錄 E.6)。

另一條差異值得記:`OFDM070A` 的 `MasterPKey` 原本還有 `SHORE_ID`,已被註解掉並留下說明「2014/03/18 ATLAS ATLAS SHORE_ID已停用」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:39-40`),主檔 SQL 改成硬塞空字串 `,'' SHORE_ID`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:65`)。但 UI 仍保留 `SHORE_ID` 的下拉清單(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:83-86`)——**欄位停用了,選單還在**。

#### 2.2.3 `OFDM082` / `OFDM082B` —— 規律成立,但寫入的層級不同

| 面向 | `OFDM082`(境內) | `OFDM082B`(境外) |
|---|---|---|
| 讀的 SQL | `FROM OFD081A OFD081 JOIN OFD0814A OFD0814`(把 `OFD081A` 別名成 `OFD081`) | `FROM OFD081` |
| **寫的 SQL** | `UPDATE OFD0814A SET REPORT_SEQ …`(寫在**明細表**上) | `UPDATE OFD081 SET REPORT_SEQ …`(寫在**基金主檔**上) |
| PO 相似度 | — | **85.4%** |
| UI 相似度 | — | **94.4%** |
| Ctl 相似度 | — | **63.8%** |

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:60-64`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:187-189` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:66-70`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:180`。

**境內把「報表排序」放在 `OFD0814A`(`OFDM081A` 的第 3 張明細,vdb 名意味深長地叫 `OFDM081A_NOEVA`),境外直接放在主檔 `OFD081` 的 `REPORT_SEQ` 欄。** 這是境內外兩套資料模型的真實差異,不是誰寫錯。但因為 `OFDM082B` 直接改主檔,它的副作用比 `OFDM082` 大得多(§4.3)。

#### 2.2.4 `OFDM085A` / `OFDM085B` —— 境內多一整塊「再申購」

| 面向 | `OFDM085A`(境內) | `OFDM085B`(境外) |
|---|---|---|
| 主檔實體表 | `OFD085A` | `OFD085` |
| 主檔 SQL join | `LEFT JOIN OFD081A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:66-67`) | `LEFT JOIN OFD081`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085B_PO.cs:67-68`) |
| 主表欄數 | 64 | 31 |
| 境內獨有 | 再申購(配息轉投資)專戶一整組 12 欄、轉申購匯費金額支付方式 4 欄、CDSC 轉申購限制 `CDSC_TRAN_CD` | — |
| 境外獨有 | `NAV_DAY`(贖回基金 NAV 日)、`SWITCH_FEE_OUT`(外加轉換費用)、`SWITCH_TYPE`(轉換 / 轉申購)、`EC_SWITCH_YN` | — |
| PO 相似度 | — | **50.1%** |
| UI 相似度 | — | **43.3%** |
| Ctl 相似度 | — | **21.5%**(540 行 vs 251 行) |

這一對是「規律成立但內容差很大」的代表:business 是同一件事(基金 A 可以轉去基金 B),但境內外的費用結構完全不同,所以只有骨架像。

#### 2.2.5 `OFDM084` / `OFDM084B` —— 規律成立,`OFDM084B` 不在本片名單

`OFDM084B` 的六層檔案都在,Model 也在 `DataEntity.OFD5`,但它**不在本片被指派的 17 支內**,本文只做對照:

| 面向 | `OFDM084`(境內) | `OFDM084B`(境外) |
|---|---|---|
| 主檔實體表 | `OFD084A` | `OFD084` |
| 主檔 SQL join | `LEFT JOIN OFD081A` + `LEFT JOIN OFD0811A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:66-67`) | `LEFT JOIN OFD081`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs:76`) |
| `MasterPKey` | `FUND_ID` `TRADE_CD`(`OPEN_TYPE` 被註解) | `FUND_ID` `OPEN_TYPE` `TRADE_CD` |
| 明細 SQL 的 join 型態 | `LEFT JOIN OFD081A` | **`INNER JOIN OFD081`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs:104-105`) |
| PO 相似度 | — | **73.5%** |

**`INNER JOIN` vs `LEFT JOIN` 是成對畫面只改一邊的另一個實例**:境外的明細列如果對應的基金不在 `OFD081`,那一列會靜靜消失,而境內版會保留並顯示空的基金簡稱(附錄 E.7)。

#### 2.2.6 反例一:`OFDM091B` 沒有境內版,`OFDM091` 是別的東西

代號長得像一對,實際上不是:

|  | `OFDM091B`(本片) | `OFDM091`(不在本片) |
|---|---|---|
| 主檔 | `OFD091` | `OFD091A` |
| 明細 | 無 | `OFD092A` |
| join | `LEFT JOIN OFD081`(境外) | `LEFT JOIN OFD081A`(境內) |
| 業務欄位 | `ISHARE_QUO`(Caption「I SHARE額度」) | `RANGE_TYPE` + 明細 `CDSC_FEE_RATE`(CDSC 後收費率區間) |
| Entity 專案 | `DataEntity.OFD5` | `DataEntity.OFD8` |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:49` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091_PO.cs:39-40` |

**兩張表管的是不同的業務**,不是同一件事的境內外兩版。代號代換後 PO 相似度 67.2%,那是因為兩支都是最精簡的「一張表 + 三個取數事件」骨架,不是因為業務相同。**結論:規律在這一對不成立。**

#### 2.2.7 反例二:`OFD087A` / `OFD088A` 有 `A` 字尾卻兩邊都收

這兩支不做境內外分版,而是在同一支畫面裡把兩張基金主檔併起來:

| 畫面 | 併法 | 錨點 |
|---|---|---|
| `OFDM087` | 主檔 SQL 同時 `LEFT JOIN OFD081A` 與 `LEFT JOIN OFD081`,用 `DECODE(OFD081A.FUND_ID, NULL, '1', '2') AS FUND_TYPE` 反推這一筆是境內還是境外 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:122-136` |
| `OFDM088` | 主檔 SQL 用 CTE `MYOFD081A`,把 `OFD081A`(標 `'2'`)與 `OFD081`(標 `'1'`)`UNION ALL` 成一張虛擬基金表 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:60-88` |

`OFDM088` 的 CTE 手法跟 `ofd7.md §4.3` 記的 `OFDM193` 一模一樣,連 CTE 名字都叫 `MYOFD081A`——這是 OFD 模組內反覆出現的樣板。

**但兩支的做法不一致**:`OFDM087` 的 `FUND_TYPE` 是 `DECODE` 出來的衍生欄(查詢時用 `AND OFD081.FUND_ID IS NOT NULL` 過濾),`OFDM088` 的 `FUND_TYPE` 是 CTE 裡的常數欄(查詢時當一般參數比對)。改其中一支的境內外邏輯時不能照抄另一支。

#### 2.2.8 反例三:`OFD074` `OFD075` `OFD077` 沒有 `A` 字尾卻只服務境內

扣款機構那一組(§4.7)三張表名都沒有 `A`,但明細 SQL **只 join `OFD081A`**:

| 表 | join | 錨點 |
|---|---|---|
| `OFD075`(`OFDM074` 明細) | `LEFT JOIN OFD081A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:182-185` |
| `OFD077`(`OFDM076` 明細) | `LEFT JOIN (SELECT … FROM OFD081A UNION SELECT 'ALL FUNDS' …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:246-248` |

**所以「表名有 `A` = 境內」這條更粗的規律在本片不成立,只有「畫面代號成對時 A=境內、B=境外」成立。** 要判斷一張表是境內還是境外,唯一可靠的方法是看 join。

#### 2.2.9 五對驗證結果一覽

| 對 | 境內側 → 表 | 境外側 → 表 | join 驗證 | PO 相似度 | UI 相似度 | Ctl 相似度 | 結論 |
|---|---|---|---|---|---|---|---|
| 1 | `OFDM081A` → `OFD081A` | `OFDM081B` → `OFD081` | ✔ | 23.1% | 15.1% | — | **成立**(兩套獨立實作) |
| 2 | `OFDM070A` → `OFD070A` | `OFDM070B` → `OFD070` | ✔ | 80.7% | 83.4% | **100%** | **成立**(訊息沒改) |
| 3 | `OFDM082` → `OFD0814A` | `OFDM082B` → `OFD081` | ✔ | 85.4% | 94.4% | 63.8% | **成立**(寫入層級不同) |
| 4 | `OFDM085A` → `OFD085A` | `OFDM085B` → `OFD085` | ✔ | 50.1% | 43.3% | 21.5% | **成立**(境內多再申購) |
| 5 | `OFDM084` → `OFD084A` | `OFDM084B` → `OFD084` | ✔ | 73.5% | — | — | **成立**(084B 不在名單) |
| — | `OFDM091`(OFD8)→ `OFD091A` | `OFDM091B` → `OFD091` | ✘ | 67.2% | — | — | **不成立**(業務不同) |

「相似度」= 把境內側原始碼中的畫面代號與表名整批代換成境外側的寫法之後,用 `difflib.SequenceMatcher` 對兩份檔案逐行比對的 ratio。比對來源是解碼成 UTF-8 後的檔案內容,不含編碼差異的影響。

### 2.3 `OFDM081A` 的八張明細:索引順序是有意義的

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:44-53` 逐行宣告,程式碼本身還在行尾標了索引註解:

| 索引 | 實體表 | vdb 名 | 管什麼(依 xsd Caption) | 欄數 | PK |
|---|---|---|---|---|---|
| 0 | `OFD0811A` | `OFDM081A_Remit` | 匯款 / 募集 / 受益憑證 / 額度控管 | 70 | `FUND_ID` |
| 1 | `OFD0813A` | `OFDM081A_Account` | 銷售款入帳日、放帳日 | 21 | `FUND_ID` |
| 2 | `OFD0814A` | `OFDM081A_NOEVA` | 報表排序順序、下張受益憑證序號、目前結帳日 | 19 | `FUND_ID` |
| 3 | `OFD082A` | `OFDM081A_MgrFee` | 經理費率階梯(生效日 × 金額級距) | 20 | `FUND_ID` `BNG_AMT` `ACP_DATE` |
| 4 | `OFD094A` | `OFDM081A_Custody` | 保管銀行帳戶 | 26 | `FUND_ID` |
| 5 | `OFD095A` | `OFDM081A_CustodyDtl` | 保管銀行聯絡人(可多筆) | 25 | `FUND_ID` `SEQ_NO` |
| 6 | `OFD084A` | `OFDM081A_084` | 可交易幣別(與 `OFDM084` 同一張表) | 18 | `FUND_ID` `TRADE_CD` `CRNCY_CD` |
| 7 | `OFD0819A` | `OFDM081A_ACC_NO` | 入款帳號(可多筆) | 22 | `FUND_ID` `ACC_TYPE` `ACC_NO` |

**索引 2 的 vdb 名 `OFDM081A_NOEVA` 值得記一下**:名字寫著「不走四眼」,但那張表(`OFD0814A`)實際上有完整的四眼 13 欄,`OFDM082` 的查詢 SQL 也把它們一欄一欄撈出來(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:172-186`)。**名字跟結構對不上**,改動時不要相信名字。

**索引 6 與 7 被 `AfterAdd` 與 `AfterUpdate` 當成不同的「最後一張」用**,這是本片最難察覺的一條(§4.1.5、附錄 E.3)。

另外 xsd 裡還有一張沒有對應實體表的 `OFDM081A_CMS`(21 欄),是那段被註解掉的官網拋轉功能留下來的容器(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081AModel.xsd`)。

### 2.4 `OFD078`:一張表兩支畫面寫,鍵欄位一邊有一邊沒有

`OFD078`(扣款機構 × 基金 × 幣別的扣帳手續費)同時被 `OFDM074` 與 `OFDM076` 宣告成明細,而且兩邊的 vdb 名都叫 `OFDM078`:

| 畫面 | 主檔 PK | 對 `OFD078` 的取數條件 | 錨點 |
|---|---|---|---|
| `OFDM074` | `BANK_HQ` `BANK_SUB_TYPE` `SEAL_TYPE` | 帶四個參數 `BANK_HQ` `BANK_SUB_TYPE` `SEAL_TYPE` `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:226` |
| `OFDM076` | `BANK_HQ` `SEAL_TYPE`(**沒有 `BANK_SUB_TYPE`**) | **先寫死 `AND OFD078.BANK_SUB_TYPE = 'ALL'`**,再帶其餘參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:336-338` |

而 `OFD078` 在兩份 xsd 裡的 PK 定義**完全相同**,都是 `BANK_HQ` `SEAL_TYPE` `BANK_SUB_TYPE` `FUND_ID` `CRNCY_CD`(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM074Model.xsd`、`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM076Model.xsd`)。

**所以分流靠的是一個寫死的字串 `'ALL'`**:代理扣款機構(`OFDM076`)的幣別設定一律掛在 `BANK_SUB_TYPE = 'ALL'` 這個虛擬業務別上,核印扣款機構(`OFDM074`)則掛在真實業務別上。程式碼註解把這件事寫出來了:「OFDM076的業務別欄位固定以ALL值JOIN」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:337`)。

這個設計的後果見 §4.12.4 與附錄 E.5。

### 2.5 表的主鍵與四眼欄位

「PK」欄取自對應 xsd 的 `xs:unique … msdata:PrimaryKey`,是 **DataTable 的鍵**,不保證等於 DB 上的 constraint(`architecture.md §5.5`)。

| 表 | vdb 名 | PK(來源 xsd) | 四眼 13 欄 | 欄數 |
|---|---|---|---|---|
| `OFD070A` | `OFDM070A` | `AGENT_ID` `AGENT_CODE` `FUND_ID` | 齊 | 45 |
| `OFD070` | `OFDM070B` | `AGENT_ID` `AGENT_CODE` `FUND_ID` | 齊 | 35 |
| `OFD071A` | `OFDM071` | `CHANNEL_CD` `CHANNEL_CODE` | 齊 | 48 |
| `OFD072A` | `OFDM072` | `AGENT_ID` `AGENT_CODE` `SPONSOR_CODE` | 齊 | 26 |
| `OFD074` | `OFDM074` | `BANK_HQ` `BANK_SUB_TYPE` `SEAL_TYPE` | 齊 | 54 |
| `OFD075` | `OFDM074_Detail` | `BANK_HQ` `BANK_SUB_TYPE` `FUND_ID` `SEAL_TYPE` | 齊 | 31 |
| `OFD078` | `OFDM078` | `BANK_HQ` `SEAL_TYPE` `BANK_SUB_TYPE` `FUND_ID` `CRNCY_CD` | 齊 | 24 |
| `OFD076` | `OFDM076` | `BANK_HQ` `SEAL_TYPE` | 齊 | 39 |
| `OFD077` | `OFDM076_Detail` | `BANK_HQ` `FUND_ID` `SEAL_TYPE` | 齊 | 25 |
| `OFD081A` | `OFDM081A` | `FUND_ID` | 齊 | 119 |
| `OFD0811A` | `OFDM081A_Remit` | `FUND_ID` | 齊 | 70 |
| `OFD0813A` | `OFDM081A_Account` | `FUND_ID` | 齊 | 21 |
| `OFD0814A` | `OFDM081A_NOEVA` | `FUND_ID` | 齊 | 19 |
| `OFD082A` | `OFDM081A_MgrFee` | `FUND_ID` `BNG_AMT` `ACP_DATE` | 齊 | 20 |
| `OFD094A` | `OFDM081A_Custody` | `FUND_ID` | 齊 | 26 |
| `OFD095A` | `OFDM081A_CustodyDtl` | `FUND_ID` `SEQ_NO` | 齊 | 25 |
| `OFD0819A` | `OFDM081A_ACC_NO` | `FUND_ID` `ACC_TYPE` `ACC_NO` | 齊 | 22 |
| `OFD081` | `OFDM081B` | `FUND_ID` | 齊 | 173 |
| `OFD082` | `OFDM081B_082` | `FUND_ID` `BNG_AMT` `ACP_DATE` | 齊 | 23 |
| `OFD083` | `OFDM081B_083` | `FUND_ID` `BNG_AMT` `ACP_DATE` | 齊 | 25 |
| `OFD084A` | `OFDM084` / `OFDM081A_084` | `CRNCY_CD` `TRADE_CD` `FUND_ID` | 齊 | 20 / 18 |
| `OFD085A` | `OFDM085A` | `FUND_ID` `SWITCH_FUND_ID` | 齊 | 64 |
| `OFD085` | `OFDM085B` | `FUND_ID` `SWITCH_FUND_ID` | 齊 | 31 |
| `OFD086` | `OFDM086` | `FUND_ID` `SWITCH_FUND_ID` | 齊 | 26 |
| `OFD087A` | `OFDM087` | `FUND_ID` `STOP_TRADE_TYPE` `STOP_BNG_DATE` | 齊 | 22 |
| `OFD088A` | `OFDM088` | `CALENDER_TYPE` `CAL_DATE` `FUND_ID` | 齊 | 24 |
| `OFD091` | `OFDM091B` | `FUND_ID` | 齊 | 21 |

四張沒有實體表的 vdb DataTable:

| vdb 表 | 用途 | 錨點 |
|---|---|---|
| `OFDM076`(定義在 `OFDM074Model.xsd`) | `OFDM074` 帶出對應代理扣款機構的五個參數欄 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM074Model.xsd` |
| `OFDM081B_064` | `OFDM081B` 用 `GetOFD064` 帶出基金公司收款銀行的 13 欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:225` |
| `OFD081Validate` | `OFDM087` 的 `DoValidate` 回傳成立日與開始贖回日,只有 2 欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:386` |
| `OFDM088_CMS` / `OFDM081A_CMS` | 已註解掉的官網拋轉容器 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM088Model.xsd` |

> ⚠ **「掃描器說欄位 0」不等於沒有定義。** 對 `OFD070A` 跑 `atlas_scan.py --table OFD070A` 會得到「欄位 0」,原因與 `ofd7.md 附錄 A` 記的一樣:**xsd 的 DataTable 名跟實體表名不同**(`new xTableMapping("OFD070A", "OFDM070A")`)。本片 27 組對應裡只有 `OFD081`、`OFD085`、`OFD086`、`OFD091`、`OFD084A`(第二份)這幾個查得到欄位,其餘要照上表去對應的 xsd 找。

### 2.6 欄位中文名:兩塊填得完整,兩塊幾乎空白

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。

| 填寫狀況 | 表 |
|---|---|
| 幾乎全填(業務欄 90% 以上有 Caption) | `OFD070A` `OFD070` `OFD071A` `OFD072A` `OFD074` `OFD075` `OFD078` `OFD081` `OFD081A` `OFD0811A` `OFD085A` `OFD085` `OFD086` `OFD091` |
| **幾乎全空** | `OFD076`(39 欄只有 4 欄有 Caption)、`OFD077`(25 欄只有 2 欄)、`OFD087A`(22 欄只有 3 欄)、`OFD084A`(18 欄全空) |

三個要特別記住的 Caption 陷阱:

| 陷阱 | 內容 | 錨點 |
|---|---|---|
| **兩欄共用一句** | `OFD081` 的 `TSCD_MEMO1`~`TSCD_MEMO7` 七欄 Caption 都以「集保申報說明N\」開頭再接不同說明,而 `OFD081A` 的對應欄 `TDCC_MEMO1`~`TDCC_MEMO7` 只有第 2 與第 7 欄有後段說明,其餘五欄一律「公開說明書內容N」 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081BModel.xsd` vs `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081AModel.xsd` |
| **三欄同名** | `OFD081` 的 `REGIST_CODE` `INVEST_AREA` `INVEST_CODE` Caption **都叫「註冊地代碼」** | 同上 |
| **Caption 被當成欄位用** | `OFDM088_CMS` 的 `DataDT` 欄 Caption 直接寫成 `FUND_SH_NM` | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM088Model.xsd` |

### 2.7 狀態碼

本片沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`),15 支走四眼的畫面**沒有任何一支**自己寫 `STATUS` 的值。

唯一一處直接比對 `EVAStatusCode` 的地方在 `OFDM081A` 的覆核前檢核:

```
if (((OFDM081AViewVDB)this.ProcessVDB).UIView.OFDM081A[0].STATUS == EVAStatusCode.VerifyDelete)
    return;   // 刪除覆核時不做欄位必填的檢核
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1383-1384`。這是本片唯一用具名常數(而不是字面量)判狀態的地方,也是唯一一支在覆核階段重跑整套檢核的畫面。

**兩支不走四眼的畫面(`OFDM082` / `OFDM082B`)完全不碰 `STATUS`**:它們的 `UPDATE` 只寫 `REPORT_SEQ` / `UPDATEID` / `UPDATEDATE`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:60-64`)。這代表排序值改過之後,資料的四眼狀態停在原地,從 ToDo 清單上看不出有東西被改過。

## 3. 畫面清冊

```text
[圖] OFD5 十七支畫面依 PO 基底分群，以及 csproj 收錄狀況
圖中文字:結論先講：本片 17 支沒有一支繼承 BasicEVAPO / MultiRowEVAPO / BasicEVAPO〔死路〕 / dbTA = null 建構子被註解 / ofd8 找到 7 支 · ofdb 找到 4 支 / 本片 0 支 / OFD 專案其他片 / OFDM725_Ctl 等仍有 / 現行主線一：BaseEVADaoPO（單筆主檔＋明細清單）共 8 支 / OFDM081A / OFD081A + 8 明細 / OFDM081B / OFD081 + 2 明細 / OFDM074 / OFD074 + OFD075 OFD078 / OFDM076 / OFD076 + OFD077 OFD078 / OFDM071 / OFD071A 無明細 / OFDM072 / OFD072A 無明細 / OFDM087 / OFD087A 用區域變數宣告 / OFDM091B / OFD091 無明細 / 現行主線二：BaseMultiRowEVADaoPO（主從同一張表，靠 MasterPKey 分群）共 7 支 / OFDM070A / MasterPKey 機構+機構碼 / OFDM070B / MasterPKey 同上 / OFDM084 / ROW_NUMBER 分群 不寫死 / OFDM085A / MasterPKey 基金 / OFDM085B / MasterPKey 基金 / OFDM086 / 與 085B 96.6% 相同 / OFDM088 / MasterPKey 類別+基金 / 第三群：繼承 BaseEVADaoPO 卻完全不用四眼管線的兩支 / OFDM082 / 無 MasterTable 無事件 / OFDM082B / 無 MasterTable 無事件 / 自建 Database TA 連線 / 自己開交易 自己下 UPDATE / 四眼形同不存在 / 狀態原封不動 / csproj：17 支六層全部在編譯清單內，但工具看得見的不只 17 支 / 17 支 x 6 層 / UI Pxy Ctl PO Model View 全中 / OFDM084B_Ctl 檔名 / 副檔名前多一個空白 / csproj 也寫了那個空白 / 編得起來 掃描器找不到 / 假性死畫面 / 實際是活的
```

*圖:圖 3 PO 基底。黑框=框架死路;橘框=本片主力;白框=一般;橘虛框=風險。本片沒有 BasicEVAPO 的存檔必 NRE 問題，真正的洞在第三群：OFDM082 / OFDM082B 掛著四眼基底卻自己開交易改資料，等於繞過覆核。*

### 3.1 維護 M

17 支全部六層齊全,全部在 `Dev/ATLAS.OFD`(UI / FormProxy / Control / PO)+ `DataEntity.OFD5` / `UIEntity.OFD5`(Model / View)。中文名待選單表回填,「用途」欄為推測。

**「PO 基底」欄的判讀**:`BaseEVADaoPO` 與 `BaseMultiRowEVADaoPO` 是現行主線(`architecture.md §3.1`);`BasicEVAPO` / `MultiRowEVAPO` 是 `architecture.md §3.1.1` 記的死路(`dbTA` 宣告即 `= null`、建構子建立連線那四行整段被註解、基底 `Add()` 第一行就 `dbTA.CreateConnection()`),繼承它而不覆寫 `Add`/`Update`/`Delete` 的畫面存檔必 NRE。

**「在 csproj」欄的判讀**:六層各自的 `.csproj` 是否列出該檔。逐層核對過 UI(`Dev/ATLAS.OFD/Source/UI/UI.OFD/UI.OFD.csproj`)、FormProxy(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/FormProxy.OFD.csproj`)、Control(`Dev/ATLAS.OFD/Source/Control/Control.OFD/Control.OFD.csproj`)、PO(`Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj`)、DataEntity(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/DataEntity.OFD5.csproj`)、UIEntity(`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD5/UIEntity.OFD5.csproj`)共 102 個項目。

| 代號 | 用途(推測) | **PO 基底** | **在 csproj** | 主表 | 明細 | 子對話框 | 特別之處 |
|---|---|---|---|---|---|---|---|
| `OFDM070A` | 銷售機構 × **境內**基金簽約(拆帳、取款帳號) | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD070A` | — | `OFDM070Ap0` `OFDM070Ap1` | `SHORE_ID` 已停用但選單還在 |
| `OFDM070B` | 銷售機構 × **境外**基金簽約(彙入、公會核准) | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD070` | — | `OFDM070Bp0` `OFDM070Bp1` | 錯誤訊息仍寫「境內」(附錄 E.6) |
| `OFDM071` | 通路基本資料(大 5 碼 / 中 9 碼 / 小 15 碼三層) | `BaseEVADaoPO` | 六層全在 | `OFD071A` | — | — | 六支伺服端檢核,`catch` 一律回 false(附錄 E.4) |
| `OFDM072` | 推薦人(業務員)基本資料與歸屬 | `BaseEVADaoPO` | 六層全在 | `OFD072A` | — | — | 兩整塊檢核被註解,外殼還在 |
| `OFDM074` | **核印**扣款機構簽約 + 可扣基金 + 可扣幣別 | `BaseEVADaoPO` | 六層全在 | `OFD074` | `OFD075` **`OFD078`** | `OFDM074p0` | 唯一有 `AfterAdd`/`AfterUpdate` 跨列同步的一支 |
| `OFDM076` | **代理**扣款機構簽約 + 可扣基金 + 可扣幣別 | `BaseEVADaoPO` | 六層全在 | `OFD076` | `OFD077` **`OFD078`** | `OFDM076p0` | 對 `OFD078` 寫死 `BANK_SUB_TYPE = 'ALL'` |
| `OFDM081A` | **境內**基金主檔(本片最重) | `BaseEVADaoPO` | 六層全在 | `OFD081A` | 八張(§2.3) | `OFDM081Ap0` `OFDM081Ap1` | 同交易內同步 `FND001`;Ctl 層另打一支 MSSQL 預存程序;`Copy` 複製基金 |
| `OFDM081B` | **境外**基金主檔 | `BaseEVADaoPO` | 六層全在 | `OFD081` | `OFD082` `OFD083` | — | 57 條 `AddError`,本片檢核最密 |
| `OFDM082` | **境內**基金報表排序 | `BaseEVADaoPO`(**不用四眼**) | 六層全在 | 無宣告(寫 `OFD0814A`) | — | — | 自己開交易 `UPDATE`(§4.3) |
| `OFDM082B` | **境外**基金報表排序 | `BaseEVADaoPO`(**不用四眼**) | 六層全在 | 無宣告(寫 `OFD081`) | — | — | 直接改基金主檔(§4.3) |
| `OFDM084` | **境內**基金可交易幣別 | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD084A` | — | — | 用 `ROW_NUMBER()` 分群,不寫死常數 |
| `OFDM085A` | **境內**基金轉換 / 轉申購 / 再申購專戶 | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD085A` | — | `OFDM085Ap0` | CDSC 轉申購限制檢核在子對話框 |
| `OFDM085B` | **境外**基金轉換 | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD085` | — | `OFDM085Bp0` | 與 `OFDM086` PO 相似度 96.6% |
| `OFDM086` | **境外**基金配現可再投資基金 | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD086` | — | `OFDM086p0` | Ctl 與 `OFDM085B` 100% 相同 |
| `OFDM087` | 基金暫停申贖期間(境內外通吃) | `BaseEVADaoPO` | 六層全在 | `OFD087A`(區域變數宣告) | — | — | 有一支只 join 境內的舊查詢方法還留著 |
| `OFDM088` | 基金行事曆(境內外通吃) | `BaseMultiRowEVADaoPO` | 六層全在 | `OFD088A` | — | `OFDM088p0` `OFDM088p1` `OFDM088p2` | 三個批次型按鈕;跨兩個資料庫的交易 |
| `OFDM091B` | **境外**基金 I Share 額度 | `BaseEVADaoPO` | 六層全在 | `OFD091` | — | — | 本片最小的一支;`AfterUpdate` 是空殼 |

**結論一:本片 17 支沒有一支繼承 `BasicEVAPO` 或 `MultiRowEVAPO`,所以沒有「存檔必 NRE」的問題。** 驗證方式:對 `Dev/ATLAS.OFD` 全樹搜 `BasicEVAPO|MultiRowEVAPO`,本片 17 支 PO 的命中全部是 `#region BasicEVAPO Event` 這種區段註解(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:72`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:103`),不是繼承。類別宣告逐支確認過,全部是 `: BaseEVADaoPO` 或 `: BaseMultiRowEVADaoPO`。

也因此,**「查 T-SQL 痕跡佐證是沒遷移的舊世代」這件事在本片幾乎沒有樣本**:17 支 PO 的 SQL 全部是 Oracle 語法(`:參數`、`NVL()`、`SYSDATE`、`DECODE`、`ROWNUM`/`ROW_NUMBER()`、`SUBSTR`),沒有任何 `[表名]` 中括號寫法、`GetDate()` 或 `ISNULL()`。**唯一的 T-SQL 痕跡集中在 `OFDM081A` 的一支方法裡**:`UpdateFND001_NEW` 用 `SqlDbType` 與 `@WFUND_ID` / `@WOSTATUS` / `@WMESSAGE` 三個 `@` 參數去打 MSSQL 預存程序(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:799-808`)。那是刻意的跨庫呼叫,不是沒遷移的殘留;而同一支 PO 內對 `FND001` 的寫入則是純 Oracle(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:325-332`)。詳見 §4.1.6 與附錄 E.9。

**結論二:本片 17 支的六層 102 個檔全部在 csproj 內,沒有「檔案存在但不在 csproj」的死畫面。** 但 OFD 這個專案確實有這類坑,只是形狀不一樣——見 §3.5。

### 3.2 查詢 I

**本片無 I 畫面。**原因:`DataEntity.OFD5` 只收 M 型的 Model,同主題的查詢畫面(例如基金查詢)在另一個專案 `Dev/ATLAS.OFD.Query`,不屬於本片。

### 3.3 批次 B

**本片無 B 畫面。**`OFDM088` 的三個功能鈕(整年建立 / 複製 / 設假日)是 M 畫面的子對話框,不是 `xOneStepProcessForm` 型的 B 畫面(`architecture.md §6.4`);它們透過 `OFDM088_Pxy` 呼叫 PO 上的自訂方法,走的仍是 M 畫面的六層。

### 3.4 報表 R

**本片無 R 畫面。**`DataEntity.OFD5` 底下沒有任何 `*R*Model.xsd`,`Dev/ATLAS.OFD.Report` 也沒有對應這 17 支的報表。

### 3.5 這 17 支之外:`DataEntity.OFD5` 裡還有一支,而且掃描器看不到它

`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/` 底下有 **18 組** Model,比本片的 17 支多一支:`OFDM084B`。

跑 `py -V:3.12 /docs/tools/atlas_scan.py --screen OFDM084B` 會得到「找不到畫面 OFDM084B」,但它其實是活的:

| 層 | 檔案 | 在 csproj? |
|---|---|---|
| UI | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM084B.cs` | ✔(`UI.OFD.csproj:359`) |
| FormProxy | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM084B_Pxy.cs` | ✔(`FormProxy.OFD.csproj:112`) |
| **Control** | **`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM084B_Ctl .cs`** —— **副檔名前多了一個半形空白** | ✔(`Control.OFD.csproj:121` 也照樣寫了那個空白:`<Compile Include="OFDM084B_Ctl .cs" />`) |
| PO | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs` | ✔(`PO.OFD.csproj:144`) |
| DataEntity | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM084BModel.xsd` | ✔ |
| UIEntity | `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD5/OFDM084BView.xsd` | ✔ |

**所以它編得起來、跑得動,只是所有靠檔名樣式比對的工具都會漏掉它。** 這是「檔案存在但不在 csproj」這條缺陷型錄的**變形**:檔案在 csproj 內,但檔名本身壞掉,造成工具層面的假性死畫面。嚴重度低(不影響執行)但影響面廣(每一份自動產生的清冊都會少一支),記在附錄 E.13。

`OFDM084B` 不在本片被指派的 17 支內,本文只在 §2.2.5 做境內外對照,不深寫。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFDM081A 的主檔與八張明細、存檔前卡控順序，以及刪除閘門
圖中文字:主檔與八張明細：DetailTable 的索引順序在兩個事件裡被用成不同意思 / OFD081A 主檔 / 119 欄 PK 基金代碼 / 索引 0 OFD0811A / 匯款/募集/憑證 70 欄 / 索引 1 OFD0813A / 銷售款入帳日 21 欄 / 索引 2 OFD0814A / 報表排序/憑證序號 19 欄 / 索引 3 OFD082A / 經理費階梯 20 欄 / 索引 4 OFD094A / 保管銀行 26 欄 / 索引 5 OFD095A / 保管銀行聯絡人 25 欄 / 索引 6 OFD084A / 可交易幣別 18 欄 / 索引 7 OFD0819A / 入款帳號 22 欄 / AfterAdd 用索引 7 / 最後一張寫完才同步 / AfterUpdate 用索引 6 / 倒數第二張就同步 / 同步對象 FND001 / 外部 MSSQL FA 資料庫 / 存檔前檢核：一條線走到底，中間兩道早退 / 必填旗標 30 餘個 / 依欄位唯讀狀態動態決定 / 保管銀行明細主鍵必填 / 有列才檢查 / 帳號長度對銀行檔 / ClientBizUtility / ACH 匯費不可為 0 / 付款平台=2 才檢 / 早退點一 有錯就回 true / 靠外層再判一次才擋得住 / 六組日期順序檢核 / 四組被註解只剩兩組 / 早退點二 同樣回 true / 同上 / 統編兩段 詢問式 / 按否就擋 按是寫 ByPass / 集保代碼重複 伺服端 / 回 -1 時擋並跳伺服器錯誤 / CDSC 後收年限必填 / 手續費收取方式=4 才檢 / 公募不可選配息方式 1 / 2023 年新增 / 覆核時整套重跑 / 覆核前再呼叫一次 / 刪除閘門：查有沒有交易過，回 -1 時只 return 不還原按鈕狀態 / 進入修改載入 / 每次載入都查一次 / CheckFUND_CURRENCY / OFD221A + RSP006A 有筆數? / 有交易 幣別唯讀+不可刪 / 無交易 可改可刪 / DB 出錯 直接 return / 按鈕停在上一次狀態
```

*圖:圖 4 OFDM081A。白框=一般;橘虛框=風險;黑框=無原始碼或外部系統;橘框=值得學的做法。新增後用明細索引 7、修改後用索引 6，兩者都呼叫同一支 FND001 同步，但觸發時機差一張明細——這是本片最難用肉眼看出來的一條。*

本章順序照 §0.1 的五塊業務線排,不照代號順序: **A 基金主檔** §4.1~§4.2 · **B 交易參數** §4.3~§4.7 · **C 轉換** §4.8 · **D 通路** §4.9~§4.11 · **E 扣款機構** §4.12。

### 4.0 十七支共同的骨架

先把重複的部分講完,後面各節只寫差異。

| 環節 | 共同做法 | 錨點(以 `OFDM087` 為例) |
|---|---|---|
| UI 基底 | `xMaintainForm`(無原始碼,從呼叫端反推),`TabPages = 2`(查詢頁 + 維護頁) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:29` |
| 存檔前檢核 | `Before{Add,Modify}ButtonClicked` → `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:142-149` |
| 取數 | PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個事件,各自組一段 SQL 字串塞進 `args.DbCmd.CommandText` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:53-93` |
| ToDo | `xTableHelper.AppendToDoString(<表名>, model)`,只在組 ToDo 語法時接上,而且程式碼一律留註解「ToDo 此段不可修改」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:198-202` |
| 參數化 | 查詢條件用 `EVAStringHelper.AddParam(...)`(具名參數)或**手寫字串串接**(`" And X = '" + Row.Value + "'"`),兩種混用 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:145`(串接)vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:71-72`(具名) |

**五件全片通用、值得先記住的事:**

1. **沒有任何一支掛 `BeforeAdd` / `BeforeUpdate` / `BeforeDelete`。** 伺服端完全沒有存檔攔截,所有業務卡控都在 UI 的 `DoValidate()` 裡。伺服端 PO 上的自訂方法(`IsFundExsits` / `CheckM_Data` / `Check_Switch_Fund_Id` …)都只是「UI 問、伺服端答」的查詢,擋不擋由 UI 決定。

2. **只有兩支有 `After*` 事件**:`OFDM074`(`AfterAdd` / `AfterUpdate` → 同步其他列)與 `OFDM081A`(`AfterAdd` / `AfterUpdate` / `AfterDelete` / `AfterApproveDelete` → 同步 `FND001`)。`OFDM091B` 掛了一個 `AfterUpdate`,方法本體只有一行註解 `//nothing`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:66-69`)。

3. **`catch` 的回傳約定有兩種,而且在同一支檔案裡混用。** 回 `int` 的方法一律 `return -1`(呼叫端多半有判 `i == -1` 並擋下來);回 VDB 的方法一律 `AddResultRow(false, 0, "")`,而 `false` 在不同呼叫端的意思可能相反(附錄 E.4)。

4. **`Convert.ToInt32(i)` 之前不檢查 `i` 是不是 `null`。** 所有 `COUNT(1)` 型查詢都寫成 `ExecuteScalar(cmd, out i); if (Convert.ToInt32(i) == 0) return 0;`。`COUNT(1)` 保證回一列所以目前不會炸,但同樣的樣板若複製到 `SELECT 欄位` 就會。

5. **四支畫面的 PO / Ctl / Pxy 來源檔不是 UTF-8**(附錄 E.11),`OFDM087` 更是六層裡有四層是 cp950。

### 4.1 `OFDM081A` — 境內基金主檔(本片最重的一支)

1,808 行 PO + 3,067 行 UI + 1,754 行 Ctl,是本片程式量最大的畫面,而且是唯一一支會寫到**本片宣告範圍以外的表**(`FND001`)與**另一個資料庫**(MSSQL 預存程序)的。

#### 4.1.1 用途與資料形狀

- **用途(推測)**:建立與維護一檔境內基金的所有靜態屬性。主檔 `OFD081A` 119 欄,涵蓋名稱(中英文、公開說明書簡稱)、成立 / 發行 / 清算日期、幣別與小數位、申購 / 贖回手續費收取方式、最低申購 / 贖回金額(計價幣別與中心幣別各一組)、定期定額參數、短線交易規定、集保代碼、風險屬性、CDSC 後收年限。

- **八張明細**見 §2.3。畫面用分頁呈現,每一張明細對應一個分頁或一組 Grid。

- **主檔 SQL**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:1086-1237`,只 `FROM OFD081A` 自己,不 join 任何外部表(基金公司名稱等由 UI 的搜尋器元件自己去查)。

#### 4.1.2 存檔前卡控總表

`DoValidate()` 在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:68-346`,278 行。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 30 餘個必填旗標依對應欄位的唯讀狀態動態開關(`reqvXxx.IsRequisite = !uxxx.ReadOnly`) | 由 `FormvalidatorManager` 統一跳訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:70-119` |
| 存檔前 | 保管銀行聯絡人明細有列時,主鍵欄位必填 | 「… 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:126-134` |
| 存檔前 | 保管銀行支存帳號長度不合該銀行的設定 | `ClientBizUtility.IsValidBankAcc` 回的訊息(無原始碼,從呼叫端反推) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:137-143` |
| 存檔前 | 付款平台 = `"2"` 且 ACH 匯費 = 0 | 「ACH匯費不可設定為0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:186-195` |
| 存檔前 | 開始買回日期 < 成立日期(且不是 1900/1/1) | 「開始買回日期 不可小於 成立日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:199-201` |
| 存檔前 | 基金開始扣款日期 < 成立日期 | 同上句型 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:223-225` |
| 存檔前 | 成立日期 < 募集期開始繳款日 | 同上句型 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:227-229` |
| 存檔前 | 私募(`PER_COLLECT = "Y"`)但非合格特定人數為 0 | 「非合格特定人數 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:238-244` |
| 存檔前 | 基金統編不符檢查碼 | 「…不符合正常邏輯,是否忽略?」 | **詢問**(按否擋、按是寫 ByPass) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:248-262` |
| 存檔前 | 大憑證受益人統編不符檢查碼 | 同上 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:264-278` |
| 存檔前 | 集保基金類股代碼已被別檔基金用掉(伺服端 `IsFundTDCCExsits`) | 回 `-1` → 跳伺服器錯誤並中止;回 `1` → 「… 已存在」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:281-292` |
| 存檔前 | 定買之最低買回金額 = 0 | 「定買之最低買回金額不可設定為0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:294-297` |
| 存檔前 | 收益分配方式 = `"4"`(不配)卻填了計息種類 | 「「計息種類」欄位為收益分配基金專用,是否繼續執行?」 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:299-312` |
| 存檔前 | 匯費金額支付方式(自行 / 他行)= `"0"` 卻沒填台幣固定金額 | 「… 台幣固定金額必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:314-324` |
| 存檔前 | 申購手續費收取方式 = `"4"`(後收-成本市價孰低)卻沒填 CDSC 年限 | 「需建入CDSC-後收到期年限」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:326-331` |
| 存檔前 | 公募(`PER_COLLECT = "N"`)卻選了收益分配方式 `"1"` | 「收益分配方式「…」僅限私募基金使用」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:333-337` |
| **覆核前** | 除了刪除覆核之外,**重跑整套 `DoValidate()`** | 有錯就 `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1380-1392` |
| 修改載入 | 該基金在 `OFD221A` 或 `RSP006A` 有交易 → 幣別唯讀 + 刪除鈕停用 | 無提示,直接改按鈕狀態 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1291-1300` |
| 修改載入 | `FUND_LOCK` 勾選 → 修改鈕與刪除鈕都停用 | 無提示 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1309-1313` |

**「覆核前重跑整套檢核」這件事本片只有 `OFDM081A` 做**,其餘 16 支覆核時完全不檢核。以基金主檔的重要性來說是對的做法,但也代表:**同一組欄位在輸入時通過、覆核時卻可能因為別人改了關聯資料而擋下來**,而覆核者看到的錯誤訊息跟輸入者當初看到的不一樣。

#### 4.1.3 兩道「有錯還回 true」的早退

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:197` 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:246` 各有一行:

```
if (this.ValidateErrList.ErrorCount > 0) return true;
```

**讀起來像「有錯誤卻回報通過」,實際上不是漏洞**,因為三個呼叫端都寫成 `if (!this.DoValidate() || this.ValidateErrList.Show())`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1335`、`:1346`、`:1387`),`Show()` 在清單非空時回 `true`,還是會擋。

**但後果是使用者要按兩次以上存檔**:第一次只看到前段的錯,修完再按才看得到後段的錯。這跟 `ofd7.md §4.0` 記的 `if (this.ValidateErrList.ErrorCount != 0) return;` 是同一個現象的不同寫法,而本片這個寫法更危險——它回的是 `true`(通過),只要有人把呼叫端簡化成 `if (!DoValidate()) return;`,整段後半檢核就會失效。記在附錄 E.10。

#### 4.1.4 `Copy` — 複製一檔基金

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:960-1078`,由子對話框 `OFDM081Ap0` 呼叫。

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 用來源基金代碼 `GetMaintainData` 撈全套;撈不到就回「來源基金資料不存在」 | `:966-975` |
| 2 | **檢查來源基金狀態**:`if (!Model.DataEntity.OFDM081A[0].STATUS.StartsWith("3"))` → 「來源基金尚未覆核」 | `:977-982` |
| 3 | 只把 **4 張**表放進要複製的清單:`OFD081A` `OFD0811A` `OFD0813A` `OFD0814A` | `:983-991` |
| 4 | `OFD084A`(可交易幣別)只保留幣別等於基金計價幣別的那些列,其餘 `row.Delete()` | `:992-1002` |
| 5 | 逐列把 `FUND_ID` 換成目的基金代碼,四眼 13 欄清空(日期填 `1900/1/1`) | `:1004-1030` |

**兩件事值得記住:**

1. **`STATUS.StartsWith("3")` 是本片唯一一處用字面量判狀態的地方。** 其餘畫面一律交給框架。這跟 `ofd7.md 附錄 C` 記的 `'301'` 應該是同一個編碼族(3 開頭 = 已覆核),但本片同樣沒有辦法從 repo 內確認完整值域,標**〔假設〕缺:DB 連線**。

2. **`Copy` 沒有複製 `OFD082A`(經理費階梯)、`OFD094A` / `OFD095A`(保管銀行與聯絡人)、`OFD0819A`(入款帳號)。** 八張明細只複製了三張。這是刻意還是漏掉,程式碼沒有註解說明;以「經理費階梯與保管銀行本來就該逐檔設定」來想是合理的,但以「複製」這個動詞給使用者的預期來想會誤導。標**〔假設〕**,記在附錄 E.12。

#### 4.1.5 `FND001` 同步 —— 同一個交易內的 Oracle 同步

**先澄清一件很容易看錯的事:`FND001` 是 Oracle 表,不是外部 MSSQL 表。** `UpdateFND001` 全程用 `dbProduct`(Oracle 產品連線)並帶同一個 `DbTransaction`(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:779-781`),所以它跟四眼的寫入是同一個交易,要嘛一起成功要嘛一起回滾。真正打到 MSSQL 的是另一支 `UpdateFND001_NEW`(§4.1.6)。

同步邏輯在 `UpdateFND001`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:311-784`,474 行),依 `eAction` 分三段:

| `eAction` | 做什麼 | 來源 | 錨點 |
|---|---|---|---|
| `"D"` | `DELETE FROM FND001 WHERE FUND_ID = :FUND_ID` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:323-334` |
| `"U"` | `UPDATE FND001 SET ( … 約 90 欄 … ) = (SELECT … )` | `OFD081A LEFT JOIN OFD0811A LEFT JOIN OFD0813A LEFT JOIN OFD0814A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:335-527`(來源 `:515-521`) |
| `"A"` | `INSERT INTO FND001 ( … ) SELECT …` | 同上四張表 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:529-783`(來源 `:774-777`) |

**來源只讀四張表**:主檔 `OFD081A` 加上明細索引 0(`OFD0811A`)、1(`OFD0813A`)、2(`OFD0814A`)。**不讀** `OFD082A` `OFD094A` `OFD095A` `OFD084A` `OFD0819A`。

**觸發點,兩個事件用了不同的索引**:

| 事件 | 判斷條件 | 索引指向的明細 | 錨點 |
|---|---|---|---|
| `AfterAdd` | `args.TableName == this.DetailTable[7].dbTableName` | **`OFD0819A`**(第 8 張) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:143-159` |
| `AfterUpdate` | `args.TableName == this.DetailTable[6].dbTableName` | **`OFD084A`**(第 7 張) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:165-180` |
| `AfterApproveDelete` | 只在 `args.TableName == MasterTable` 時 | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:187-199` |

`AfterUpdate` 那一行上面留著被註解掉的原版 `//string detail_tableName = this.DetailTable[7].dbTableName;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:171`),註記「2018.12.05 m by Vina 9000006863」。**索引是被刻意從 7 改成 6 的**,`AfterAdd` 沒有跟著改(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:149-150`)。

**資料新舊上不會出事**(索引 6 與 7 都排在來源的三張明細之後),但**「哪一張明細寫完才算全部寫完」這個判準兩邊不一致**,而且判準本身就脆弱:它假設「框架一定會為 `DetailTable[6]` / `[7]` 各觸發一次 `AfterAdd` / `AfterUpdate`」。若某一次存檔那張明細沒有任何異動列、框架因而不觸發事件,`FND001` 就整批不同步、而且不會有任何錯誤。**〔假設〕**:框架 `BaseEVADaoPO` 無原始碼,無法從 repo 確認零列時會不會觸發。記在附錄 E.3。

**另外兩件事:**

- `FUND_LOCK == "Y"` 時整支 `UpdateFND001` 直接 `return`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:317-321`),**不報錯也不記錄**。鎖定的基金在 ATLAS 改了,`FND001` 就對不起來。結果類型:**過濾(無提示)**。

- `OFDM081B`(境外)**完全沒有 `FND001` 同步**。整支 PO 沒有任何 `After*` 事件。境外基金主檔改了之後 `FND001` 不會動;repo 內查不到補償機制,標**〔假設〕缺:版控外**,記在附錄 E.8。

#### 4.1.6 `UpdateFND001_NEW` —— 真正打 MSSQL 的那一支,掛在 Ctl 層而且在交易外

`OFDM081A_PO` 在建構子建了一條 MSSQL 連線:

```
SQLDBName = "FA";
SQLDb = new Database(SQLDBName, DbServerType.MSSql);
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:60-62`。〔客戶特定〕連線名 `"FA"`。**這條連線只被 `UpdateFND001_NEW` 用到。**

`UpdateFND001_NEW` 有兩個多載:

| 多載 | 狀態 | 錨點 |
|---|---|---|
| `public void UpdateFND001_NEW(string FUND_ID)` | **活的**,被 Ctl 層呼叫三次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:787-818` |
| `private void UpdateFND001_NEW(dRow, model, tran, eAction)` | **死碼**:兩個呼叫端都在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:155` 與 `:177` 被註解掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:820-858` |

活的那一支做的事:呼叫 MSSQL 預存程序 `S_PAM_OFD081A_AFIZZ020`,傳入 `@WFUND_ID`,取回 `@WOSTATUS` 與 `@WMESSAGE`;`@WOSTATUS != "Y"` 就 `throw new ApplicationException(訊息)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:799-816`)。這支 SP **不在版控內**(`DB/SP/` 底下沒有),已加進 meta 的 `refcheck-ignore`。

**呼叫端在 Control 層,不在 PO 層**:

| 入口 | 呼叫方式 | 有沒有包 try | 錨點 |
|---|---|---|---|
| `OFDM081A_Ctl.Add` | `new OFDM081A_PO()` 之後直接 `po.UpdateFND001_NEW(mainRow.FUND_ID)` | **沒有** | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:57-73` |
| `OFDM081A_Ctl.Modify` | 同上 | 有 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:80-120` |
| `OFDM081A_Ctl.Copy` | 同上,傳的是 `ToFUND_ID` 參數 | **沒有** | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:333-345` |

**這一段有五個問題:**

| # | 問題 | 影響 | 錨點 |
|---|---|---|---|
| 1 | **在 PO 的交易之外呼叫。** `ExecPOActionToViewVDB(view, m_OFDM081A_PO.Add)` 回來時 Oracle 那邊已經 commit,才去打 MSSQL 的 SP | SP 失敗 → Oracle 已寫入、MSSQL 沒寫入,而且畫面收到例外 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:61-66` |
| 2 | **不檢查 `Add` / `Update` 有沒有成功就打 SP** | Oracle 側失敗時仍然會去更新 MSSQL | 同上 |
| 3 | **`@WOSTATUS` 的預期值與註解對不上。** 程式旁的註解寫 `--1.資料更新成功 2.失敗`,程式判的卻是 `!= "Y"` | 若 SP 真的回 `"1"` 代表成功,這支在**成功時也會丟例外**。**〔假設〕**:SP 不在版控內,無法確認實際回傳值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:805-812` |
| 4 | **公開多載沒有檢查 `FUND_LOCK`。** 死掉的 private 多載有檢查(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:826-830`),活的公開多載只收一個 `FUND_ID`,沒有資料列可查 | 鎖定的基金在 Oracle 側被 `UpdateFND001` 跳過,在 MSSQL 側卻照打 SP,兩邊不一致 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:787-790` |
| 5 | **`new OFDM081A_PO()` 直接 new,不走 `base.GetDaoInstance<IOFDM081A_PO>()`。** 同一支方法上面才剛用 `GetDaoInstance` 拿過一個實例 | 繞過 DAO pool,而且每次都會再建一條 MSSQL `Database` 物件 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:60`(池)vs `:64`(直接 new) |

合起來:**本片唯一的跨系統寫入,發生在交易外、沒有檢查前一步是否成功、判斷成功的值跟註解對不上、而且鎖定旗標失效。** 記在附錄 E.9。

#### 4.1.7 已被註解的官網 CMS 拋轉

`OFDM081A_PO` 內還留著一整組「覆核後把基金資料拋轉到官網」的程式:

| 部位 | 狀態 | 錨點 |
|---|---|---|
| 事件掛載 `this.AfterApprove += …` / `this.BeforeApprove += …` | **兩行都被註解** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:64-68` |
| 第二條 MSSQL 連線 `SQLDBNameCMS = "CMS_ATLAS"` | 被註解 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:69-72` |
| `OFDM081A_PO_AfterApprove` 方法本體 | **存在,但裡面唯一那行呼叫被註解**,方法變成空殼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:202-208` |
| `UpdateCMSFundA(…)` 方法 | 前半(讀 Oracle 資料)**還在執行**,後半(拋轉)整段被註解 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:216-302` |
| xsd 的 `OFDM081A_CMS` 容器表(21 欄) | 還在 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081AModel.xsd` |

這是「被註解但外殼還在」的典型:`UpdateCMSFundA` 是 `public` 且沒有被註解,任何人從別的地方呼叫它都會執行半套。目前 repo 內沒有呼叫端。記在附錄 E.14。

### 4.2 `OFDM081B` — 境外基金主檔

577 行 PO + 2,217 行 UI。與 `OFDM081A` 的關係見 §2.2.1:**不是抄的,是兩套獨立實作**。

#### 4.2.1 資料形狀

- 主檔 `OFD081` 173 欄,是本片欄位最多的一張表。多出來的部分集中在境外特有的事項:註冊地、總代理、集保申報說明七段、SWIFT / BIC / IBAN 匯款資訊、傘型架構、核備、公開說明書檔案路徑、保管機構信用評等。

- 兩張明細:`OFD082`(經理費率階梯,`TRAILER_RATE`)與 `OFD083`(保管費率 / 分銷費率 / 經理費收入分成,`MRT_RATE` / `DFEE_DESC` / `DS_RATE`),鍵都是 `FUND_ID` + `BNG_AMT` + `ACP_DATE`。

- 第三張 vdb 表 `OFDM081B_064` 不是明細,是 `GetOFD064` 從基金公司收款銀行檔帶出來的 13 欄,供使用者「照抄基金公司的預設匯款資訊」用(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:225-276`)。

#### 4.2.2 卡控:本片檢核最密的一支

`DoValidate()` 在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:59-442`,單一方法 383 行、**57 條 `AddError`**。挑會咬人的列:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | ISIN 代碼 + 計價幣別已存在於其他基金(伺服端 `IsISIN_CODEExsits`) | 「ISIN代碼+計價幣別已有資料存在,請重新輸入ISIN代碼!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:75-85` |
| 存檔前 | 手續費收取方式 = `1`(前收)時,內含手續費計算方式必填;不是 `1` 時反而不可填 | 兩句對稱訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:136-146` |
| 存檔前 | 定期定額註記 = `0` 卻勾了「可交易項目:定期定額申購」(以及反向) | 兩句對稱訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:170-183` |
| 存檔前 | 基金贖回方式(單位數 / 金額 / 皆可)決定三組欄位的必填組合 | 七句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:200-233` |
| 存檔前 | 收款銀行 / 中間銀行 SWIFT 不足八碼 | 「…SWIFT代碼至少輸入八碼!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:276-285` |
| 存檔前 | 承作綜合帳戶時集保基金類股代碼必填,且不可與其他基金重複(伺服端 `IsFundTSCDExsits`) | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:290-306` |
| 存檔前 | 手續費 / 經理費 / 保管費各一組「最高 / 最低 / 固定三選一」+「填了固定就不可填最高最低」+「最低不可大於最高」 | 九句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:310-360` |
| 刪除前 | 該基金在 `OFD221` 或 `RSP006` 有交易(伺服端 `IsTradeData`) | 回 `-1` 跳伺服器錯誤 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081B.cs:1281` |

**`IsTradeData` 查的是 `OFD221` / `RSP006`(無 `A`),`OFDM081A` 的 `CheckFUND_CURRENCY` 查的是 `OFD221A` / `RSP006A`(有 `A`)。** 兩支的交易表也是境內外分版的,對照:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:128-135` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:872-879`。這是本片 `A` / 無 `A` 規律在**交易表**上的延伸,與 §2.2 的結論一致。

**跨表更新**:無。`OFDM081B_PO` 沒有任何 `After*` 事件(對照 §4.1.5 的 `FND001` 同步)。

### 4.3 `OFDM082` 與 `OFDM082B` — 報表排序(成對,而且是本片唯一繞過四眼的兩支)

這一對是本片最需要小心的。它們繼承 `BaseEVADaoPO`(四眼基底),**但建構子是空的**:沒有 `MasterTable`、沒有 `DetailTable`、沒有掛任何事件。

```
public class OFDM082_PO : BaseEVADaoPO, IOFDM082_PO
{
    Database dbTA = new Database("TA", DbServerType.Oracle);
    public OFDM082_PO()
    {

    }
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:26-33`(`OFDM082B` 同型:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:32-39`)。

#### 4.3.1 兩支自訂方法就是全部

| 方法 | 做什麼 | `OFDM082`(境內) | `OFDM082B`(境外) |
|---|---|---|---|
| `GetFundSeqData` | 撈出基金清單與目前排序值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:148-246` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:155-235` |
| `SortFundSeq` | 逐列 `UPDATE … SET REPORT_SEQ` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:44-145` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:52-149` |

`SortFundSeq` 的流程一模一樣:自己 `dbTA.BeginTransaction()` → 逐列先 `SELECT COUNT(1)` 確認資料還在 → `UPDATE` → 全部成功才 `Commit()`。

#### 4.3.2 卡控總表(兩支合併)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 排序前逐列 | 該基金代碼在目標表已不存在 | 「此基金代碼:{0} 已不存在,請檢查後重新執行」+ 整筆 Rollback | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:88-95`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:88-95` |
| 排序後逐列 | `ExecuteNonQuery` 回傳 < 1 | **空字串訊息** + Rollback | 阻擋(但畫面上看不到原因) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:105-112`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:105-111` |
| 排序結束 | 一列都沒改到(`i` 仍為 0) | **空字串訊息** + Rollback | 阻擋(看不到原因) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:124-131`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:124-131` |
| 例外 | 任何例外 | `tran.Rollback()` + **空字串訊息** | 阻擋(看不到原因) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:128-141`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:133-140` |

**四條裡有三條的訊息是空字串 `""`。** 使用者按了排序、畫面跳一個沒有內容的失敗訊息,不知道發生什麼事。

#### 4.3.3 這一對的七個問題

| # | 問題 | 影響 | 錨點 |
|---|---|---|---|
| 1 | **完全繞過四眼**:只寫 `REPORT_SEQ` / `UPDATEID` / `UPDATEDATE`,`STATUS` 與四眼人員欄位原封不動 | 排序改過之後,資料的覆核狀態看不出有異動;ToDo 清單不會出現 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:60-64` |
| 2 | **`OFDM082B` 改的是基金主檔 `OFD081` 本身** | 一支「報表排序」畫面可以繞過覆核直接改基金主檔的欄位 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:66-70` |
| 3 | **`i` 是覆寫不是累加**,註解卻寫「累加修改資料筆數」 | 最後那個 `if (i > 0)` 判的是**最後一列**的結果;若明細零列,`i` 維持 0 → 走到 else → Rollback + 空訊息 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:102`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:102` |
| 4 | **`catch` 第一行就 `tran.Rollback()`**,而 `tran` 是在 `try` 內才被賦值 | `BeginTransaction()` 本身失敗時,`catch` 內會再丟一次 `NullReferenceException`,原始例外被蓋掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:128-130`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:133-135` |
| 5 | **字串串接進 SQL**:`strWhereCond += " And FH_CD = " + "'" + Row.Value + "'"` | 基金公司代碼含單引號會炸,也是注入點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:207-213`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:188-194` |
| 6 | **`OFDM082B` 把參數加在錯的 `Database` 物件上**:`dbProduct.AddInParameter(cmdValidate, …)`,但命令是 `dbTA.GetSqlStringCommand(...)` 建的、也是 `dbTA.ExecuteScalar(...)` 執行的。`OFDM082`(境內)全程用 `dbTA`,兩邊不一致 | 目前可能因為兩個 `Database` 都指向同一種 provider 而沒事,但這是成對畫面只改一邊的典型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:83`、`:97-100` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:78`、`:88-91` |
| 7 | **`OFDM082B` 把 `DbCommand` 建在迴圈外、`OFDM082` 建在迴圈內** | 兩種寫法都靠 `Parameters.Clear()` 才正確,但差異沒有理由 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:74-75` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:72-73` |

#### 4.3.4 `OFDM082` 的查詢 SQL 把 `OFD081A` 別名成 `OFD081`

```
From OFD081A OFD081
JOIN OFD0814A OFD0814
       ON OFD081.FUND_ID = OFD0814.FUND_ID
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:187-189`。**在一份「`OFD081` = 境外、`OFD081A` = 境內」的程式庫裡,把境內表別名成境外表的名字,是最容易讓後人讀錯的一種寫法。** 記在附錄 E.15。

同一段的 `WHERE` 條件 `And FH_CD = '…'` **沒有加表別名前綴**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:211`)。若 `OFD0814A` 之後也長出 `FH_CD` 欄位,這條 SQL 會直接因為 column ambiguous 而失敗。目前可跑,標**〔假設〕未確認 `OFD0814A` 的完整欄位**。

### 4.4 `OFDM084` — 境內基金可交易幣別

本片最乾淨的一支多筆型畫面,值得當範本。

- **用途(推測)**:一檔基金 × 一個交易別(`TRADE_CD`)可以用哪些幣別交易。主鍵 `FUND_ID` + `TRADE_CD` + `CRNCY_CD`,畫面上半是「基金 × 交易別」的群,下半是該群下的幣別列。

- **群首怎麼抓**:`ROW_NUMBER() OVER (PARTITION BY FUND_ID, TRADE_CD ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE, CRNCY_CD)` 取 `NUM = 1`,並把 `CRNCY_CD` 硬塞成空白 `,' ' CRNCY_CD`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:53-72`)。

**這比 `ofd7.md §4.1` 記的 `WHERE BNG_AMT = 1` 好得多**:`ofd7` 那幾支靠「第一階起始金額寫死是 1」這個假設抓群首,一旦有資料不是從畫面寫進去的就整群消失;`OFDM084` 用視窗函數,任何資料都抓得到群首。同一個模組裡兩種做法並存。

- **明細 SQL**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:80-96`,`LEFT JOIN OFD081A` 取基金簡稱、`LEFT JOIN FSK003` 取幣別名稱。

- **卡控**:PO 端零卡控(只有三個取數事件)。UI 端的檢核在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM084.cs`。

- **跨表更新**:無。

- **與 `OFDM081A` 的重疊**:`OFD084A` 同時是 `OFDM081A` 的第 7 張明細(vdb 名 `OFDM081A_084`)。**同一張表有兩個維護入口**,而且兩邊的 xsd 欄位定義不同(`OFDM084` 20 欄含 `CRNCY_NM` `FUND_SH_NM`,`OFDM081A_084` 18 欄不含這兩個顯示欄)。改欄位要兩份 xsd 一起改。

`OFDM084B`(境外)的對照見 §2.2.5。

### 4.5 `OFDM087` — 基金暫停申贖(境內外通吃,但留著一支只看境內的舊方法)

- **用途(推測)**:設定一檔基金在某段期間暫停某種交易(`STOP_TRADE_TYPE`)。主鍵 `FUND_ID` + `STOP_TRADE_TYPE` + `STOP_BNG_DATE`。

- **境內外怎麼併**:主檔 SQL 同時 `LEFT JOIN OFD081A` 與 `LEFT JOIN OFD081`,基金簡稱用 `CASE WHEN` 取其中有值的那邊,`FUND_TYPE` 則用 `DECODE(OFD081A.FUND_ID, NULL, '1', '2')` 反推(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:117-136`)。

**查詢條件的境內外過濾是用 `IS NOT NULL` 做的**:

```
if (pRow.Value == "1")  strWhereCond += " And OFD081.FUND_ID IS NOT NULL";   // 境外
else                    strWhereCond += " And OFD081A.FUND_ID IS NOT NULL";  // 境內
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:153-167`。**`else` 分支沒有判 `pRow.Value == "2"`**:只要 `FUND_TYPE` 參數存在而值不是 `"1"`(包括空字串、其他值),就一律當成境內。使用者若在查詢頁把基金資料來源清空,參數仍然存在時會被當境內,境外的暫停設定就看不到。結果類型:**過濾(無提示)**。記在附錄 E.16。

#### 4.5.1 伺服端 `DoValidate` 取基金日期

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:357-402`,用 `UNION` 併兩張基金表,靠 `'2' = :FUND_TYPE` / `'1' = :FUND_TYPE` 這種「常數 = 參數」的寫法讓其中一段整個不回列:

```
FROM OFD081A  WHERE 1 = 1 AND '2' = :FUND_TYPE AND OFD081A.FUND_ID = :FUND_ID
UNION
FROM OFD081   WHERE 1 = 1 AND '1' = :FUND_TYPE AND OFD081.FUND_ID  = :FUND_ID
```

這段是本片對境內外規律**最直接的證據**(§0.5)。

**但這支的成功判定有洞**:不管載回幾列,一律 `model.Utility.Result.AddResultRow(true, 0, "")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:389-390`)。UI 端靠檢查回來的資料表列數自己判「基金基本資料檔 未設定」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:293`),這次接對了;但伺服端的 `ReturnCode` 在「查無基金」時是 `true`,任何新的呼叫端若只看 `ReturnCode` 就會誤判。

#### 4.5.2 舊的 `GetFundStopDateData` 只 join 境內

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:217-350` 是一支跟 `BuildMasterSQLString` 功能重疊的查詢方法,但它**只 `LEFT JOIN OFD081A`**(`:264-265`),境外基金的簡稱會回空白。整支方法裡還有 14 行被註解掉的四眼欄位清單(`:249-262`)——那段已經被 `xEVAStringHelper.AllEVAColumnsForSelect("OFD087A")` 取代,外殼留著。

`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM087_Pxy.cs` 有對應的轉呼叫,所以它不是完全的死碼,但 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs` 走的是四眼管線的 `BeforeSelect`,不走這一支。**「多套實作並存,其中一套跟不上需求」** 記在附錄 E.17。

#### 4.5.3 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前(第二關) | 停止交易日期(起)= `1900/01/01` | 「停止交易日期(起)必須輸入」+ 把值清成 null | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:150-155` |
| 存檔前(第二關) | 停止交易日期(迄)= `1900/01/01` | 「停止交易日期(迄)必須輸入」+ 把值清成 null | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:156-160` |
| 存檔前 | `DoValidate()` 開頭:必填類錯誤已存在就直接 `return`,不跑後面任何業務檢核 | 使用者要按第二次存檔才看得到業務錯誤 | 阻擋(但分兩次顯示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:222-223` |
| 存檔前 | 暫停起始日 > 暫停終止日 | 「暫停起始日期不可大於暫停終止日期」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:225-232` |
| 存檔前 | 境外基金的暫停交易別不在 `"0"` / `"1"` / `"2"` 之內 | 「境外基金不可選擇, 轉申購及定額選項!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:234-241` |
| 存檔前 | 暫停起迄日 < 基金開始買回日 / 成立日(伺服端取日期後在 UI 比) | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:279-290` |
| 存檔前 | 伺服端回來零列(基金不存在) | 「基金基本資料檔 未設定」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:292-293` |
| 存檔前 | 四段「暫停日期不可小於成立 / 發行日期」 | **整段被註解** | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:250-266` |

**跨表更新**:無。

### 4.6 `OFDM088` — 基金行事曆(境內外通吃,三個批次型按鈕,跨兩個資料庫)

- **用途(推測)**:維護某一類行事曆(`CALENDER_TYPE`)在某一檔基金(或全部基金)上的逐日營業 / 非營業註記(`BUSS_ID`)與備註。主鍵 `CALENDER_TYPE` + `CAL_DATE` + `FUND_ID`。

- **境內外怎麼併**:主檔 SQL 用 CTE `MYOFD081A` 把 `OFD081A`(`'2'`)與 `OFD081`(`'1'`)`UNION ALL`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:60-88`),再把 `FUND_TYPE` 當一般查詢參數比對(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:93`)。同一段 CTE 在明細 SQL 又抄了一份(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:123`),**改一邊要改兩邊**。

#### 4.6.1 三個批次型入口

| 入口 | 方法 | 做什麼 | 錨點 |
|---|---|---|---|
| 「整年行事曆」鈕 → `OFDM088p0` | `AddAllYear` | 一次把整年 12 個月的每一天建出來 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:474-577` |
| 「複製」鈕 → `OFDM088p1` | `CopyCalender` | 把某年某月某基金某類別的行事曆複製到另一組 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:362-472` |
| 「假日」鈕 → `OFDM088p2` | `SetHoliday` | 把某一天在該月所有行事曆上標成非營業日,並在備註後面接一行說明 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:271-355` |

**三支都走「分批寫入 + 分別 ToDo」的樣板**,跟 `ofd7.md §4.4` 記的 `OFDM194.Copy` 是同一套做法:`if (dt.Rows.Count == 1) base.Update(modelVDB);` 否則開交易逐批寫,並核對寫入筆數。

#### 4.6.2 兩個資料庫、兩個交易、循序 commit

三支方法都同時開兩條交易:

```
tran     = dbProduct.BeginTransaction();
tranptpf = dbPTPF.BeginTransaction();
…
tran.Commit();
tranptpf.Commit();
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:322-325`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:337-338`(`SetHoliday`);`CopyCalender` 在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:433-435`;`AddAllYear` 在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:519-521`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:560-561`。

`dbPTPF` 是基底 `BaseMultiRowEVADaoPO` 提供的第二條連線(無原始碼,從呼叫端反推;`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:27` 有同名欄位,對應設定名 `"SWProduct"`),ToDo 資料寫在那邊。

**`tran.Commit()` 與 `tranptpf.Commit()` 是兩句話,不是一個分散式交易。** 第一句成功、第二句失敗時,業務資料已經進去、ToDo 沒進去,而 `catch` 會對兩條都呼叫 `Rollback()`——對已 commit 的那條無效。結果是「行事曆建好了但沒有人收到覆核通知」,而畫面顯示「新增失敗」。記在附錄 E.18。

#### 4.6.3 其餘三個問題

| # | 問題 | 錨點 |
|---|---|---|
| 1 | `catch` 第一行 `tran.Rollback()`,`tran` 可能還是 `null`(與 §4.3.3 #4 同型) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:340-347` |
| 2 | 分批條件用 `String.Format("FUND_ID='{0}' AND CALENDER_TYPE='{1}'", …)` 餵 `DataTable.Select()`,基金代碼含單引號會炸 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:330` |
| 3 | 備註長度上限判 `> 200` 但截成 `Substring(0, 199)`,少一個字 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:295-302` |

#### 4.6.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 修改前 | 一律先問一次 | 確認對話框,按否就 `e.Cancel` | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM088.cs:222-229` |
| 存檔前 | 年月格式 | 「須符合日期格式」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM088.cs:356-364` |
| 複製前 | 來源與目的的基金代碼與行事曆類別完全相同 | 「來源及目的的基金代碼與行事曆類別不可皆相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM088p1.cs` |
| 設假日前 | 該月查無行事曆 | 把「查無資料」改寫成「查無行事曆資料可設定」,`ReturnRowCount = 2` | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:283-289` |
| 整年 / 複製後 | 寫入筆數與預期不符 | `throw new ApplicationException("")`(**空訊息**)→ 被 `catch` 接住 → 「新增失敗」 | 阻擋(看不到原因) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:557-558` |

**跨表更新**:無(只寫自己的 `OFD088A` 與框架的 ToDo)。

### 4.7 `OFDM091B` — 境外基金 I Share 額度

本片最小的一支:PO 172 行、UI 130 行。

- **用途(推測)**:設定一檔境外基金的 I Share 額度(`ISHARE_QUO`)。主檔 `OFD091`,PK 只有 `FUND_ID`。

- **境外怎麼固定的**:UI 在初始化時把查詢頁與維護頁的基金搜尋器都寫死成境外:`this.custFUND_IDSide_0.SOURCE_CD = SHORE_ID.OffShore;` / `this.custFUND_IDSide.SOURCE_CD = SHORE_ID.OffShore;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM091B.cs:31-32`),而 PO 的主檔 SQL `LEFT JOIN OFD081`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:135-136`)。兩層都鎖成境外,一致。

- **`AfterUpdate` 是空殼**:`this.AfterUpdate += OFDM091B_PO_AfterUpdate;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:51`),方法本體只有 `//nothing`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:66-69`)。旁邊還有一行被註解的 `BeforeUpdate` 掛載(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:50`)。這代表**曾經有東西要在更新前後做,後來拿掉了但外殼留著**。

- **查詢條件字串串接**:`strSQL += " And OFD091." + Row.Name + " = " + "'" + Row.Value + "'";`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:147`)。

- **卡控**:PO 端零卡控。UI 端只有框架的必填檢核。

- **跨表更新**:無。

`OFD091` 與 `OFDM091`(`OFD091A`)沒有業務關係,見 §2.2.6。

### 4.8 `OFDM085A` / `OFDM085B` / `OFDM086` — 轉換與配息再投資三兄弟

三支的骨架相同:多筆型 PO、`MasterPKey` 只有 `FUND_ID`、明細是「這檔基金可以轉去哪些基金」的清單、真正的編輯在子對話框(`OFDM085Ap0` / `OFDM085Bp0` / `OFDM086p0`)。

#### 4.8.1 三支的差異總表

| 面向 | `OFDM085A`(境內轉換) | `OFDM085B`(境外轉換) | `OFDM086`(境外配現再投資) |
|---|---|---|---|
| 主檔實體表 | `OFD085A` | `OFD085` | `OFD086` |
| join | `OFD081A` + `OFD062` + `OFD020V`(兩次別名) | `OFD081` + `OFD062` | `OFD081` + `OFD062` |
| 主表欄數 | 64 | 31 | 26 |
| 子對話框鎖定的基金來源 | `SHORE_ID.OnShore`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:80`) | `SHORE_ID.OffShore`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Bp0.cs:58-59`) | `SHORE_ID.OffShore`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM086p0.cs:58-59`) |
| 伺服端自訂檢核 | `Check_Switch_Fund_Id`(CDSC 轉申購限制) | 無 | 無 |
| PO 行數 | 224 | 135 | 130 |
| 與 `OFDM085B` 的相似度 | — | — | PO **96.6%** · Ctl **100%** · UI **89.8%** |

**`OFDM085B` 與 `OFDM086` 是本片最極端的複製貼上**:PO 只差 5 行(`OFD086` 少 `NAV_DAY` / `SWITCH_FEE_OUT_CRNCY` / `SWITCH_FEE_OUT` / `SWITCH_TYPE` / `EC_SWITCH_YN` 五個欄位),Ctl 代號代換後一字不差(251 行全同)。錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085B_PO.cs:88-99` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM086_PO.cs:88-94`。

**設定屬性不一樣的地方在子對話框的鎖定寫法**:`OFDM085Ap0` 用 `custSWITCH_FUND_ID.SHORE_ID = …`,`OFDM085Bp0` / `OFDM086p0` 用 `custFUND_IDSide.SOURCE_CD = …`。兩個不同的搜尋器控件、兩個不同的屬性名,做同一件事。改境內外規則時要記得有兩種寫法。

#### 4.8.2 `OFDM085A` 的 CDSC 轉申購限制 —— 三個 `WHEN` 裡有兩個會被 NULL 吃掉

`Check_Switch_Fund_Id` 用一段 `CASE WHEN` 決定要回哪一句錯誤訊息:

```
CASE WHEN NVL(:CDSC_TRAN_CD,' ') = ' ' THEN '後收級別基金，需建入轉申購限制'
     WHEN (SW_OFD081A.AFEE_TYPE = OFD081A.AFEE_TYPE AND OFD081A.CDSC_YEARS<>SW_OFD081A.CDSC_YEARS) THEN '後收級別基金，年限需相同，請重新挑選'
     WHEN NVL(:CDSC_TRAN_CD,' ') = 'N' AND OFD081A.AFEE_TYPE<>SW_OFD081A.AFEE_TYPE THEN '後收級別基金，期滿前只能轉入後收級別基金，請重新挑選'
ELSE 'CheckOK' END AS MSG
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:176-186`。

**第二與第三個 `WHEN` 都踩在 Oracle 三值邏輯上**:`CDSC_YEARS <> …` 與 `AFEE_TYPE <> …`,只要任一邊是 `NULL`,整個比較就是 `UNKNOWN`,`WHEN` 不成立,直接掉到 `ELSE 'CheckOK'` —— **變成放行**。而 `CDSC_YEARS` 在非後收基金上本來就常常是 `NULL`(`OFDM081A` 只在申購手續費收取方式 = `"4"` 時才強制填,見 §4.1.2)。

第一個 `WHEN` 反而用了 `NVL()` 保護,可見寫的人知道 NULL 的問題,只是沒有套到後兩個。記在附錄 E.2。

**呼叫端只在轉出基金是後收時才問**:`if (this.InFundRow.AFEE_TYPE == "4")`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:472-486`),這一層是對的。`catch` 回的是 `AddResultRow(false, 0, "檢核失敗，請檢查")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:212-217`),呼叫端判 `!ReturnCode` 就加錯誤 —— **DB 出錯時是擋下來,不是放行**。這支的例外處理是本片做得對的少數之一。

#### 4.8.3 `OFDM085Ap0` 的下一段檢核少了 null 保護

緊接著上一段的:

```
if (this.InFundRow.AFEE_TYPE != "4" && ((OFD_FUND_IDListView.FUND_IDListRow)this.custSWITCH_FUND_ID.SelectedDataRow).AFEE_TYPE == "4")
```

錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:489-492`。**`SelectedDataRow` 沒有判 `null` 就轉型取值。** 同一支方法的第一段檢核(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:464-465`)明明寫了 `this.custSWITCH_FUND_ID.SelectedDataRow != null &&`,第三段卻沒有。使用者若是直接把基金代碼打進去而沒有從搜尋器挑,`SelectedDataRow` 會是 `null`,存檔時丟 `NullReferenceException`。標**〔假設〕**:未實測 `SelectedDataRow` 在手打代碼時是否一定為 `null`,但同一支方法內兩段寫法不一致這件事是確定的。記在附錄 E.19。

#### 4.8.4 三支的卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料 為必填欄位」 | 阻擋 | 三支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085A.cs:142-148` |
| 明細編輯 | 轉出與轉入基金的計價幣別不同 | 「轉出基金與轉入基金的計價幣別不相同,請重新挑選」 | 阻擋 | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:463-465` |
| 明細編輯 | 轉入基金代碼重複 | 「轉入基金代碼不可重複」 | 阻擋 | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:467-469` |
| 明細編輯 | 後收基金的三條 CDSC 限制(伺服端) | 三句訊息之一 | 阻擋(但兩條會被 NULL 放行) | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:471-486` |
| 明細編輯 | 非後收基金轉入後收基金 | 「非後收級別基金不可轉入後收級別基金,請重新挑選」 | 阻擋 | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:488-492` |
| 明細編輯 | 轉入基金專戶分行有填時,名稱 / 存款類別 / 帳號 / 匯費付款碼四項必填 | 四句訊息 | 阻擋 | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:494-509` |
| 明細編輯 | 書面與 EC 的「轉換手續費折數 / 固定手續費率」各自二擇一 | 兩句訊息 | 阻擋 | `OFDM085A` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:511-525` |

**跨表更新**:三支都無。

### 4.9 `OFDM070A` / `OFDM070B` — 銷售機構 × 基金簽約(成對)

境內外配對的驗證見 §2.2.2。這裡寫兩支的實際內容。

#### 4.9.1 資料形狀與分群

兩支都是多筆型:`MasterPKey` = `AGENT_ID` + `AGENT_CODE`,也就是「一家銷售機構」是一群,群內每一列是「這家機構承作的一檔基金」。

主檔 SQL 的「取群首」做法跟 `OFDM084` 不同,也跟 `ofd7` 的寫死常數不同:直接 `SELECT DISTINCT` 機構層級的欄位,把基金層級的欄位硬塞成空值(例 `OFDM070A` 的 `,'' SHORE_ID`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:65`)。

#### 4.9.2 兩支的業務差異

| 欄位群 | `OFDM070A`(境內) | `OFDM070B`(境外) |
|---|---|---|
| 手續費拆帳 | `ALLOWANCE_ID`(拆帳基礎)+ `ALLOT_FEE_ALLOWANCE`(拆帳比),另有一整組「特殊期間」版本 | 無 |
| 取款 | `COLLECT_ID` / `DUE_BANK` / `DUE_ACC_NO` + 轉申購用的第二組 | 無 |
| CDSC | `CDSC_TYPE`(銷售機構傳輸方式)+ `CDSC_FEE_ALLOWANCE`(分成手續費率) | 無 |
| 交易資料彙入 | 無 | `AGENT_ADATA_ID` / `AGENT_RDATA_ID` / `AGENT_DIVDATA_ID` 三欄 |
| 主管機關 | 無 | `DECLARE_TSCD`(申報集保碼)、`CO_DATE` / `CO_NO`(公會核准日期 / 文號) |
| 有效碼下拉來源 | `ValidCodeChDataSrc()` | `GetDropDownDataSrc("933")`(註解寫「銷售機構有效碼(境外)」) |

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:71-88` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070B.cs:73-87`。

#### 4.9.3 卡控總表(兩支合併,標註哪支有)

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | **兩支都說「銷售機構承銷境內基金設定明細資料 必須輸入」** | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:50-54`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070B.cs:50-54` |
| 明細編輯 | 基金代碼在群內重複 | 「基金代碼 重覆」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Ap0.cs`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Bp0.cs` |
| 明細編輯 | 無效起始日期 < 生效日期 | 「無效起始日期 不可小於 生效日期!」 | 阻擋 | 兩支 | 同上 |
| 明細編輯 | 生效日期 = `1900/01/01` | 「生效日期 不可輸入 1900/01/01!」 | 阻擋 | 兩支 | 同上 |
| 明細編輯 | 特殊期間起迄必須同時填或同時不填;起 > 迄;填了期間就要填拆帳基礎與拆帳比 | 四句訊息 | 阻擋 | **只有 `OFDM070A`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Ap0.cs` |
| 明細編輯 | 拆帳比 > 100 | 「… 不可大於 100」 | 阻擋 | **只有 `OFDM070A`** | 同上 |
| 明細編輯 | CDSC 後收基金要填傳輸方式與分成費率 | 「CDSC後收基金需輸入「銷售機構傳輸方式及銷售機構分成手續費率」」 | 阻擋 | **只有 `OFDM070A`** | 同上 |
| 明細編輯 | 公會核准日期 / 文號必填 | 兩句訊息 | 阻擋 | **只有 `OFDM070B`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Bp0.cs` |
| 複製 | 複製來源不存在 | 「複製來源尚未建立:…」 | 阻擋 | 兩支各有 `p1` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Ap1.cs`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070Bp1.cs` |

**跨表更新**:兩支都無。

### 4.10 `OFDM071` — 通路三層樹

- **用途(推測)**:維護「通路」這個層級樹。通路代碼長度決定層級:**5 碼 = 大通路、9 碼 = 中通路、15 碼 = 小通路**,下層的前綴必須等於上層的完整代碼(`SUBSTR(CHANNEL_CODE,1,5)` / `SUBSTR(CHANNEL_CODE,1,9)`)。

- **主檔** `OFD071A` 48 欄,其中 33 欄是聯絡資訊(電話 / 傳真 / Email 各三組)。

#### 4.10.1 六支伺服端檢核

| 方法 | 問什麼 | 回 `true` 代表 | 錨點 |
|---|---|---|---|
| `CheckM_ChannelData` | 這筆大通路底下有沒有有效的中小通路 | 有 → 不可設為無效 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:105-159` |
| `Check_Middle_ChannelData` | 這筆中通路底下有沒有有效的小通路 | 有 → 不可設為無效 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:167-216` |
| `CheckB_Data` | 這個大通路存不存在 | 存在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:282-333` |
| `CheckData` | 這個中通路存不存在 | 存在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:223-275` |
| `IsExsit_Middle_ChannelData` | 這個大通路底下有沒有任何中小通路 | 有 → 不可刪 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:340-390` |
| `IsExsit_Small_ChannelData` | 這個中通路底下有沒有小通路 | 有 → 不可刪 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:397-447` |

Pxy 層把名字改過(`CheckM_ChannelData` → `CheckM_Data`、`Check_Middle_ChannelData` → `Check_Middle_Data`),六支都有完整的 UI 呼叫端(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:228`、`:243`、`:289`、`:303`、`:317`、`:328`),**沒有死碼**。

#### 4.10.2 同一種 `catch` 在這支檔案裡會造成兩種相反的失敗

六支的 `catch` 寫法一模一樣:

```
catch (Exception ex)
{
    result.Utility.Result.Clear();
    result.Utility.Result.AddResultRow(false, 0, "");
    CommonExceptionBlocker.HandleBusinessException(ex);
}
```

但 UI 對 `ReturnCode` 的解讀分成兩組:

| 組 | 方法 | UI 怎麼判 | DB 出錯時的結果 |
|---|---|---|---|
| **「有子通路就擋」組** | `CheckM_Data` `Check_Middle_Data` `IsExsit_Middle_ChannelData` `IsExsit_Small_ChannelData` | `if (… ReturnCode == true) AddError(...)` | `false` → **不加錯誤 → 檢核通過**,可以把有下層的通路設成無效或刪掉 |
| **「上層必須存在」組** | `CheckB_Data` `CheckData` | `if (… !ReturnCode) AddError("不存在此大通路…")` | `false` → **加錯誤 → 誤擋**,使用者看到「不存在此大通路」但其實只是資料庫有問題 |

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:229-233`(第一組)vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:318-321`(第二組)。

**同一份 `catch` 樣板,一組失效成「該擋沒擋」、一組失效成「不該擋卻擋」。** 這是本片最值得記住的一條。記在附錄 E.4。

#### 4.10.3 其他兩個問題

| # | 問題 | 錨點 |
|---|---|---|
| 1 | 六支全部用 `string.Format` 把通路代碼串進 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:189-192`、`:243-246`、`:299-302`、`:361-364`、`:420-423` |
| 2 | `CheckData` / `CheckB_Data` 的 SQL 是 `SELECT COUNT(*), CHANNEL_CODE … GROUP BY CHANNEL_CODE`,卻用 `ExecuteScalar` 取值 | 分組後只會拿到第一組的筆數。用在「存不存在」的判斷上剛好還是對的,但語意錯了,而且加了一個不必要的 `GROUP BY`。`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:239-256`、`:290-313` |

#### 4.10.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 通路代碼長度不是 5 / 9 / 15 | 「'通路代碼'需為 5,9 或 15碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:274-280` |
| 存檔前(5 碼) | 底下有有效中小通路卻要設為無效 | 「此筆大通路資料已存在有效的中小通路…」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:285-296` |
| 存檔前(9 碼) | 底下有有效小通路卻要設為無效 | 「此筆中通路資料已存在有效的小通路…」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:298-310` |
| 存檔前(9 碼) | 前 5 碼的大通路不存在 | 「不存在此大通路…」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:312-322` |
| 存檔前(15 碼) | 前 9 碼的中通路不存在 | 「尚未存在此中通路'…',請重新輸入!」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:324-333` |
| 刪除前(5 碼) | 底下有中小通路 | 「已存在相關中小通路資料,不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:223-238` |
| 刪除前(9 碼) | 底下有小通路 | 「已存在相關小通路資料,不可刪除」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:239-251` |

**刪除 15 碼的小通路沒有任何檢核**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:219-252` 只有 5 碼與 9 碼兩個分支)。以層級樹來說這是合理的(小通路是葉節點),但如果別的表引用了小通路代碼,這裡不會擋。repo 內 `OFD071A` 被 `ATLAS.RSP` 等 12 個外部檔引用(§8.4),**是否有引用完整性的保護在 repo 內查不到**,標〔假設〕。

**跨表更新**:無。

### 4.11 `OFDM072` — 推薦人

- **用途(推測)**:維護銷售機構底下的推薦人(業務員)與其歸屬推薦人。主鍵 `AGENT_ID` + `AGENT_CODE` + `SPONSOR_CODE`。

- **PO 只有 151 行**,除了三個取數事件之外只有 `ChkUPPER_SPONSOR` 一支檢核。

#### 4.11.1 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 歸屬推薦人 = 推薦人代碼本人 | 「歸屬推薦人 不可與 推薦人代碼相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:130-138` |
| 存檔前 | 離職否 = `"Y"` 但離職日期空白 | 「離職日期 不可空白」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:200-205` |
| **刪除前** | 這個推薦人代碼已被別人當成「歸屬推薦人」 | `ChkUPPER_SPONSOR` 回的訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:207-223` |
| 存檔前(新增 / 修改) | 推薦人 ID 不符統編也不符身分證檢查碼 | 「…不符合正常邏輯,是否忽略?」 | **詢問**(按否擋、按是寫 ByPass) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:232-239`、`:244-262` |

#### 4.11.2 兩整塊被註解的檢核

| 被註解的檢核 | 原本要做什麼 | 錨點 |
|---|---|---|
| ID 格式檢核 | 8 碼走統編檢查碼、10 碼走身分證檢查碼,其餘長度直接報「推薦人ID格式有誤」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:140-164` |
| 同一大通路下推薦人重複 | 兩段:同一身分證在別的通路已有推薦人資料、同一通路下推薦人代碼重複;各自對應 PO 的 `CheckSPONSOR_IDNO` / `CheckSPONSOR` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:166-198` |

**第二塊註解掉的是「推薦人代碼在同一通路下不可重複」這種等級的檢核。** 目前唯一還在跑的 ID 檢核是 `CheckID()`,而它是**詢問式**的(按「是」就放行並寫 ByPass),不是阻擋式。所以現況是:**推薦人 ID 可以是任何字串,只要按一次「是」。** 記在附錄 E.20。

被註解的那兩段還提到 `CheckSPONSOR_IDNO` / `CheckSPONSOR` 兩支 PO 方法,但 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM072_PO.cs` 裡**沒有這兩支方法**——它們連外殼都沒留下,只剩註解裡的呼叫。這代表註解掉的時間點比較早,後來 PO 被清理過。

**跨表更新**:無。

### 4.12 `OFDM074` 與 `OFDM076` — 扣款機構(共用 `OFD078`)

兩支不是境內外配對,是**兩種扣款機構**:`OFDM074` 管「核印扣款機構」(直接跟銀行簽約的),`OFDM076` 管「代理扣款機構」(透過代理行的)。兩支共用同一張幣別明細 `OFD078`(§2.4)。

#### 4.12.1 `OFDM074` — 三層結構 + 唯一的跨列同步

**資料形狀**:主檔 `OFD074`(54 欄,PK `BANK_HQ` + `BANK_SUB_TYPE` + `SEAL_TYPE`)+ 明細 `OFD075`(這家機構可扣哪些基金)+ 明細 `OFD078`(每檔基金可扣哪些幣別與扣帳手續費)。子對話框 `OFDM074p0`(937 行)同時編輯後兩張。

**兩支「同扣款機構其他筆數」查詢**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:307-333` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:344-367`):

| 方法多載 | SQL 條件 | 用途 |
|---|---|---|
| `intBANK_HQ_COUNT(BANK_HQ, BANK_SUB_TYPE, UNIT_CODE)` | `BANK_HQ='{0}' AND BANK_SUB_TYPE<>'{1}' AND SEAL_TYPE='{2}' AND UNIT_CODE<>'{3}'` | 改「轉出單位代碼」時,問同機構其他業務別有幾筆要跟著改 |
| `intBANK_HQ_COUNT(BANK_HQ, BANK_SUB_TYPE, SEAL_TYPE, DATA_CENTER)` | `BANK_HQ='{0}' AND BANK_SUB_TYPE<>'{1}' AND SEAL_TYPE='{2}' AND DATA_CENTER='{3}'` | 改「扣款限額」時,問同機構同代理行其他業務別有幾筆 |

**三個問題**:

1. **`string.Format` 把四個值串進 SQL**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:322`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:358`)。

2. **`UNIT_CODE <> '…'` 與 `BANK_SUB_TYPE <> '…'` 踩 Oracle 三值邏輯**:`UNIT_CODE` 為 `NULL` 的列不會被算進去,所以「還沒設過轉出單位代碼」的那些列不會出現在同步清單裡。這正好是最需要被同步的那一批。記在附錄 E.2。

3. **`catch` 回 `-1`**——但這一支的呼叫端**有好好接**:`if (i < 0) { ShowMessage(Error01, ServerSideError); e.Cancel = true; }`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:439-444`、`:488-492`)。**本片對 `-1` 處理最完整的就是這一支**,可以當範本。

**唯一的跨列同步**:`OFDM074_PO_AfterAddUpdate`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:447-534`)。使用者在畫面上確認「將同步更新相同扣款機構的 … 共 N 筆」之後,PO 在存檔後把同機構其他業務別的列一起改掉:

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 0 | 守門:核印方式 = 一般 且 不是(小額扣款 且 郵局 700)→ 直接 `return` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:455-458` |
| 1 | `IsUpdateUnit` 為真(財金)→ 撈同機構其他業務別的列,把 `UNIT_CODE` 換成新值 | `:462-485` |
| 2 | 呼叫 `UpdateOther(model, args)` 寫回,並用 `IsRunning` 旗標防止事件遞迴 | `:487-495` |
| 3 | `IsUpdateLMT` 為真 → 再撈一次(多帶 `DATA_CENTER` 條件),把兩個限額換成新值 | `:497-534` |

第 0 步那行守門條件是 `if (row.SEAL_TYPE == SEAL_TYPE.Common && (row.BANK_SUB_TYPE != BANK_SUB_TYPE.RSP || row.BANK_HQ != "700")) return;`。**`&&` 與 `||` 混用且只有一層括號**,語意是「核印方式為一般、而且不是(小額扣款且郵局)時不同步」。逐一代值驗過是對的,但這種寫法讀起來要停三秒,而且 `"700"` 是寫死的郵局代碼(註解「2018.3.19 by Mia 郵局判斷方式改為700」)。〔客戶特定〕。

第 2 步之後有一段註解值得留著:「2009.8.3 Howard 賤招.. 若有更新, 則清除ByPass / 若不清除, 則更新LMT_AMT時, ByPass又會寫入相同的dataid」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:491-493`)。

#### 4.12.2 `OFDM074` 的「費用支付種類」檢核:註解掉一半,另一半被那一半的變數綁住

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:378-425`:

```
bool isHasNoData = false;
…
// 檢查(書面)扣帳費必須有幣別明細值
if (strFEE_PAY_ITEM == FEE_PAY_ITEM.Deduct)
{
    isHasNoData = (isHasFundNoData || dt078.Count() == 0 || dt078.Any(o => o.IsNull("SUB_FEE")));
    if (isHasNoData)
    {
        //常使用 by mia
        //this.ValidateErrList.AddError(this.ucomFEE_PAY_ITEM, "…");
    }
}

// 檢查(EC/IVR)扣帳費必須有幣別明細值
if (strFEE_PAY_ITEM_EC == FEE_PAY_ITEM.Deduct && isHasNoData)
{
    …
    this.ValidateErrList.AddError(this.ucomFEE_PAY_ITEM_EC, "…");
}
```

**訊息被註解了,但計算 `isHasNoData` 的那一行沒有被註解,而 EC 那一段的條件裡有 `&& isHasNoData`。** 結果:

| 書面費用支付種類 | 書面資料完整? | `isHasNoData` | EC 檢核會不會跑 |
|---|---|---|---|
| 扣帳費 | 不完整 | `true` | 會 |
| 扣帳費 | **完整** | `false` | **不會**(即使 EC 的 `SUB_FEE_EC` 全空) |
| 不是扣帳費 | — | 維持初值 `false` | **不會** |

**也就是說「EC/IVR 扣帳費要有幣別手續費」這條檢核,只在「書面也是扣帳費、而且書面的手續費有缺」的時候才會跑。** 註解掉一句訊息,順手把另一條檢核也關掉了大半。記在附錄 E.5。

#### 4.12.3 `OFDM076` — 限額必須高於 `OFDM074`,但 DB 出錯就放行

`OFDM076` 的 PO 有五支自訂檢核,其中兩支是跨畫面的:

| 方法 | 問什麼 | 錨點 |
|---|---|---|
| `CHECK_SEAL_CHK_CODE` | 這家代理行允不允許這種核印扣款方式 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:394-497` |
| `CHECK_DATA_CENTER` | 代理扣款機構相關檢核 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:499-594` |
| `CHECK_OFDM075` | 與 `OFD075` 的關聯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:596-674` |
| **`CHECK_OFDM074_DAY_LMT_AMT`** | **`OFD074` 裡有沒有哪一筆的每日扣款限額比現在要存的還高** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:676-718` |
| **`CHECK_OFDM074_ALLOT_LMT_AMT`** | 同上,單筆扣款限額 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:728-770` |

後兩支是 `OFDM074` 與 `OFDM076` 之間唯一的程式關聯:**代理扣款機構的限額不可以低於它底下任何一家核印扣款機構的限額**。SQL 是 `SELECT COUNT(*) FROM OFD074 WHERE DATA_CENTER=:DATA_CENTER AND SEAL_TYPE=:SEAL_TYPE AND DAY_LMT_AMT>:DAY_LMT_AMT`,回 `> 0` 就 `AddResultRow(true, 1, "代理扣款機構(…)的每日扣款限額,低於OFDM074的設定,請檢查")`。

**這兩支用的是具名參數,是本片少數全程參數化的檢核。** 但 `catch` 仍然是 `AddResultRow(false, 0, "")`,而 UI 判的是 `if (View.Util.Result[0].ReturnCode == true) AddError(...)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:86-89`、`:99-102`)——**DB 出錯 → `false` → 不加錯誤 → 限額檢核通過**。與 §4.10.2 的第一組同型。

另外 `View.Util.Result[0]` 沒有先檢查 `Count`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:86`)。目前 PO 的每一條路徑都會 `AddResultRow`,所以不會炸,但這是靠 PO 的實作細節撐著。

#### 4.12.4 `OFDM076` 對 `OFD078` 寫死 `'ALL'`

見 §2.4。程式碼:

```
// OFDM076的業務別欄位固定以ALL值JOIN
strSQL += " AND OFD078.BANK_SUB_TYPE = 'ALL' ";
```

錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:337-338`。

**後果**:`OFD078` 的 PK 含 `BANK_SUB_TYPE`,而 `OFDM076` 的主檔 PK 沒有這一欄。所以

- 從 `OFDM076` 存進去的幣別列,`BANK_SUB_TYPE` 必須被寫成 `'ALL'` 才查得回來;

- 若有任何一筆 `OFD078` 是由 `OFDM074` 用真實業務別寫進去、而扣款機構又剛好同一家,`OFDM076` **看不到也改不到**,沒有任何提示;

- 反過來,`OFDM074` 查 `OFD078` 時帶的是真實業務別,也**看不到 `'ALL'` 那些列**。

兩支畫面各自看到 `OFD078` 的一半,而且都不知道另一半存在。結果類型:**過濾(無提示)**。記在附錄 E.5。

#### 4.12.5 兩支的卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」/「明細資料必須輸入」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:193-196`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:41-44` |
| 存檔前 | 該機構不允許所選的核印扣款方式 | 「扣款機構{0}不允許{1}核印扣款方式」/「代理扣款機構{0}…」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:228-235`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:50-58` |
| 存檔前 | 無效起始日期 = `1900/01/01` | 「無效起始日期 不可輸入'1900/01/01'」 | 阻擋 | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:177-181` |
| 存檔前 | 聯絡人 Email 格式 | 「… 格式有誤,請檢查」 | 阻擋 | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:183-186` |
| 存檔前 | 轉出單位代號長度 ≠ 7 | 「轉出單位代號 輸入長度為 7 碼!!」 | 阻擋 | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:237-241` |
| 存檔前 | 明細內的取款方式未填 | 「明細資料內的取款方式為必填欄位」 | 阻擋 | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:268-272` |
| 存檔前 | EC/IVR 扣帳費缺幣別手續費 | 「【費用支付種類(EC/IVR)】為'扣帳費',幣別明細的手續費必須有值。」 | 阻擋(**條件被前一段綁住**,§4.12.2) | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:412-424` |
| 欄位離開 | 改轉出單位代碼 / 扣款限額時同機構其他筆數 > 0 | 「將同步更新相同扣款機構的 … 共 N 筆,是否繼續?」 | **詢問** | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:445-455`、`:493-503` |
| 欄位離開 | 上述查詢回 `-1` | 跳伺服器錯誤 + `e.Cancel` | 阻擋 | `OFDM074` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:439-444` |
| 存檔前 | 核印費 = 應收但未填或 ≤ 0 | 「核印費 為必填欄位」/「核印費 必須大於0」 | 阻擋 | `OFDM076` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:60-68` |
| 存檔前 | 每日 / 單筆扣款限額 ≤ 0 | 「… 必須大於0」 | 阻擋 | `OFDM076` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:69-76` |
| 存檔前 | 限額低於 `OFD074` 的設定(伺服端) | 「代理扣款機構(…)的每日 / 單筆扣款限額,低於OFDM074的設定,請檢查」 | 阻擋(**DB 出錯就放行**) | `OFDM076` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:80-103` |
| 存檔前 | 核印扣款方式為「財金」時明細的費用代碼未填 | 「核印扣款方式為 '財金' 時,明細資料內的費用代碼 為必填欄位」 | 阻擋 | `OFDM076` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:109-116` |
| 明細編輯 | 取款分行與取款帳號必須同時填或同時不填 | 「取款分行, 取款帳號 必須全(不)填寫」 | 阻擋 | `OFDM076` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076p0.cs` |
| 明細編輯 | 幣別明細為空 / 扣帳手續費未填 | 「幣別明細資料 必須輸入」/「扣帳手續費 為必填欄位」 | 阻擋 | `OFDM076` | 同上 |

**跨表更新**:`OFDM074` 有(同機構其他列);`OFDM076` 無。

## 5. 查詢畫面(I)

**本片無 I 畫面。**原因:`DataEntity.OFD5` 這個 Entity 專案只收 M 型的 Model,同主題的查詢畫面在另一個專案 `Dev/ATLAS.OFD.Query`(例如 `OFDI070` 讀 `OFD070A` / `OFD075` / `OFD077`、`OFDI902` 讀 `OFD088A`),不屬於本片。

不過本片有兩支畫面各自**自帶一個查詢型的方法**,行為上等同 I 畫面,而且各有一條會靜靜濾掉資料的條件:

| 方法 | 所屬 | 會濾掉什麼 | 錨點 |
|---|---|---|---|
| `GetFundSeqData` | `OFDM082` / `OFDM082B` | `INNER JOIN OFD0814A`(境內版):基金主檔有、但還沒建過 `OFD0814A` 的基金**查不到,也就無法設排序** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:187-189` |
| `GetFundStopDateData` | `OFDM087` | 只 `LEFT JOIN OFD081A`:境外基金查得到列,但基金簡稱一律空白 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:263-265` |

另外三條「會把資料濾掉而不提示」的條件分散在 M 畫面的主檔 SQL 裡,整理在這裡:

| 條件 | 所屬 | 後果 | 錨點 |
|---|---|---|---|
| `AND OFD078.BANK_SUB_TYPE = 'ALL'` | `OFDM076` | 業務別不是 `'ALL'` 的幣別設定在這支畫面完全不存在(§4.12.4) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:338` |
| `else → AND OFD081A.FUND_ID IS NOT NULL` | `OFDM087` | `FUND_TYPE` 參數存在但值不是 `"1"` 時一律當境內(§4.5) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:162-166` |
| `INNER JOIN OFD081` | `OFDM084B`(不在本片名單,列出供對照) | 基金已從 `OFD081` 移除時,明細列消失 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs:104-105` |

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**

`DataEntity.OFD5` 底下沒有 `*B*Model.xsd`;17 支畫面的 UI 全部繼承 `xMaintainForm`(M 型),沒有一支繼承 `xOneStepProcessForm`(B 型,`architecture.md §6.4`)。

**最接近批次的是 `OFDM088` 的三個功能鈕**(§4.6.1),它們一次寫一整年或一整月的資料,而且自己開交易、自己核對寫入筆數。它們與 M 畫面的關係:

| 項目 | 說明 |
|---|---|
| 觸發 | 使用者在 `OFDM088` 維護頁按「整年行事曆」/「複製」/「假日」鈕 |
| 輸入 | 子對話框 `OFDM088p0` / `OFDM088p1` / `OFDM088p2` 收年、月、基金代碼、行事曆類別、備註 |
| 寫哪些表 | `OFD088A` 與框架的 ToDo 表(另一個資料庫 `dbPTPF`) |
| 失敗處理 | 寫入筆數不符就 `throw new ApplicationException("")`,`catch` 兩條交易都 `Rollback()` 後回「新增失敗」;跨兩個資料庫的 commit 不是原子的(§4.6.2) |
| 與四眼的關係 | **仍然走四眼**:呼叫的是 `base.Add(...)` / `base.Update(...)`,狀態與 ToDo 都會寫。這點跟 `ofd7.md §0.3` 記的 `OFDM197` / `OFDM206` 那三個「繞過四眼的批次匯入」**不一樣** |

本片真正繞過四眼的是 `OFDM082` / `OFDM082B`(§4.3),而它們不是批次,是單筆的排序更新。

## 7. 報表(R)

**本片無 R 畫面。**

`DataEntity.OFD5` 底下沒有任何 `*R*Model.xsd`,`Dev/ATLAS.OFD.Report` 也沒有對應這 17 支的 rpt。本片的表被報表讀到的只有兩張,而且讀的人在別的專案:

| rpt / 專案 | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| `Dev/ATLAS.NFD.Report/…/NFDR106_PO.cs` | `OFDM081A` 的保管銀行明細 | `OFD094A` `OFD095A` | 未細查,標〔假設〕 |

## 8. 跨模組共用

```text
[圖] OFD5 五組跨模組共用：基金主檔、境外三張給 OTA、OFD074 被 36 檔引用、通路給 RSP、OFD078 與 FND001
圖中文字:A：基金主檔 —— 本片建檔，全公司在讀 / OFDM081A OFDM081B / 唯一維護入口 / OFD081A / OFD081 / 基金主檔 兩張 / Common BMS RSP EC / LEFT JOIN 取基金簡稱 / OFD0811A 29 個外部檔 / 本片最熱的明細 / B：境外設定三張 —— 幾乎只有 ATLAS.OTA 在用 / OFDM085B OFDM086 OFDM091B / 本片維護 / OFD085 OFD086 OFD091 / 境外轉換/配現/額度 / OTA 的三支交易畫面 / 配息再投資取用 / OTAB 批次 / 也在讀 / C：OFD074 扣款機構 —— 本片被引用最廣的一張表 / OFDM074〔OFD5〕 / 唯一維護入口 / OFD074 + OFD075 + OFD078 / 扣款機構三張 / Common 14 檔 OFDB 7 檔 / RSP 6 檔 BMS 6 檔 / 共 36 個外部檔 / 改欄位要全掃 / D：通路與推薦人 —— 定期定額 RSP 是最大客戶 / OFDM071 OFDM072 / OFD071A OFD072A / RSP 共 10 個檔 / 扣款件歸屬通路與推薦人 / OFDB OFDI EC OTA.Query / 各自 join 取名稱 / 刪除有三層連動 / 大→中→小通路 / E：OFD078 與 FND001 —— 兩個最容易出事的接點 / OFD078 / 零個外部檔引用 / 但 074 與 076 同時寫 / 鍵欄位一邊有一邊沒有 / FND001〔外部 MSSQL〕 / 只有境內 081A 會同步 / 境外改主檔不同步 / repo 內查不到補償機制
```

*圖:圖 5 跨模組。橘框=本片維護入口;白框=表或事實;灰虛框=別的模組;橘虛框=風險;黑框=外部系統。C 組的 OFD074 是本片影響面最大的一張表（36 個外部檔），E 組的兩個接點則是最容易踩到的：同一張 OFD078 兩支畫面寫、FND001 只有境內同步。*

### 8.1 `OFD081A` / `OFD081` —— 本片建檔,全公司在讀

這兩張基金主檔是整個 ATLAS 最被廣泛 join 的表之一。本片是**唯一的維護入口**(`OFDM081A` / `OFDM081B`),其餘模組一律是 `LEFT JOIN … 取 FUND_SH_NM` 這種唯讀用法。

跟著它一起熱的是 `OFD0811A`(`OFDM081A` 的第 0 張明細,匯款 / 募集 / 憑證 70 欄):**29 個 `Dev/ATLAS.OFD` 以外的 `.cs` 檔引用它**,包含 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs`。

**影響面**:改 `OFD0811A` 的欄位定義,要同時看 `OFDM081AModel.xsd` 與那 29 個檔各自的 SQL。

### 8.2 `OFD074` / `OFD075` / `OFD077` —— 本片被引用最廣的一組

| 表 | 外部引用檔數 | 主要在哪 |
|---|---|---|
| `OFD074` | **36** | `Dev/Common`(14,含 `SearcherModel.cs`、`ucActingOrSubBank.cs`、`ucSubBank.cs` 三個共用控件)、`ATLAS.OFDB`(7)、`ATLAS.RSP`(6)、`ATLAS.BMS`(6) |
| `OFD075` | 7 | `Dev/Common/…/NfdUtility_PO.cs`、`Dev/ATLAS.OFD.Query/…/OFDI070_PO.cs`、`Dev/ATLAS.OFDB/…/OFDB004_PO.cs` |
| `OFD077` | 4 | 同上一組 |
| `OFD078` | **0** | 只有 `OFDM074` / `OFDM076` 兩支畫面碰 |

**`OFD074` 被三個共用 UI 控件直接吃進去**,代表「扣款機構」這個概念在整個系統的挑選器裡是共用的。改 `OFD074` 的欄位或有效碼邏輯,影響的不只是 `OFDM074` 這一支畫面,而是所有帶扣款機構挑選器的畫面。

**`OFD078` 零外部引用,但這不代表它安全**——它有兩個內部寫入者而且看不到彼此(§4.12.4)。

### 8.3 `OFD085` / `OFD086` / `OFD091` —— 幾乎只有 `ATLAS.OTA` 在用

本片維護的三張**境外**設定表,下游集中在 `ATLAS.OTA`(境外總代理的交易模組)與 `ATLAS.OTAB`:

| 表 | 本片維護入口 | 下游 | 下游在做什麼(推測) |
|---|---|---|---|
| `OFD085` | `OFDM085B` | `Dev/ATLAS.OTA/Source/Control/Control.OTA/OFDM231B_Ctl.cs` 等 6 檔、`ATLAS.OFDB` 2 檔 | 境外基金轉換交易 |
| `OFD086` | `OFDM086` | `Dev/ATLAS.OTA/Source/Control/Control.OTA/OFDM113_Ctl.cs`、`OFDM221C_Ctl.cs`、`OFDM231B_Ctl.cs`(註解寫「基金配現可再投資基金設定檔(OFD086)」)、`ATLAS.OTAB` 1 檔 | 配息再投資 |
| `OFD091` | `OFDM091B` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs` 等 6 檔、`ATLAS.OTAB` 5 檔 | I Share 額度控管 |

**這一組是「`A` / 無 `A` = 境內 / 境外」規律在模組層級的佐證**:無 `A` 的表,下游清一色是 `OTA`;有 `A` 的表(`OFD085A`),下游是 `OFDB` 與 `Common`。

### 8.4 `OFD071A` / `OFD072A` —— 定期定額 RSP 是最大客戶

| 表 | 外部引用檔數 | 主要在哪 |
|---|---|---|
| `OFD071A`(通路) | 12 | `ATLAS.RSP`(4)、`Dev/Common`(3,含 `BasicOFD_PO.cs`)、`ATLAS.OFDB`(2)、`ATLAS.EC`(1,`OFDM199AOracleDao.cs`)、`ATLAS.OFD.Query`(1,`OFDI199_PO.cs`) |
| `OFD072A`(推薦人) | 13 | `ATLAS.RSP`(6)、`ATLAS.OFDB`(3)、`Dev/Common`(2,含共用控件 `ucSponsorData.cs`)、`ATLAS.OFDI`、`ATLAS.OTA.Query` |

**`OFD071A` 同時是 `ofd7.md §8` 記的 EC 促銷活動通路判定的輸入**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs` 都在 join)。也就是說:**本片的 `OFDM071` 改了通路的有效碼,會影響 OFD7 那片的促銷活動對象判定**。這是兩片之間唯一的真依賴。

### 8.5 三張表有兩個維護入口

| 表 | 入口 1(走四眼) | 入口 2 | 風險 |
|---|---|---|---|
| `OFD0814A` | `OFDM081A` 的第 2 張明細(vdb `OFDM081A_NOEVA`) | **`OFDM082` 直接 `UPDATE REPORT_SEQ`,不走四眼** | 排序值被改過,四眼狀態不變(§4.3.3) |
| `OFD081` | `OFDM081B` 主檔,走四眼 | **`OFDM082B` 直接 `UPDATE REPORT_SEQ`,不走四眼** | 同上,而且改的是基金主檔 |
| `OFD084A` | `OFDM084` 主檔 | `OFDM081A` 的第 6 張明細(vdb `OFDM081A_084`) | 兩份 xsd 的欄位定義不同(20 欄 vs 18 欄),改欄位要兩邊一起改 |

`OFD0814A` 還有第三個讀者:`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs` 與 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs`。

### 8.6 `FND001` 與 MSSQL 預存程序 —— 兩條下游,而且都只有半邊

`OFDM081A` 在新增 / 修改 / 覆核刪除時,同時往兩個方向送資料:

| 條 | 目標 | 誰觸發 | 在不在四眼的交易內 | 錨點 |
|---|---|---|---|---|
| 1 | Oracle 的 `FND001` 表 | PO 的 `AfterAdd` / `AfterUpdate` / `AfterApproveDelete` | **在**(帶 `args.DbTran`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:311-784` |
| 2 | MSSQL 預存程序 `S_PAM_OFD081A_AFIZZ020`(連線名 `"FA"`) | **Ctl 的 `Add` / `Modify` / `Copy`**,在 PO 回來之後 | **不在** | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:66`、`:91`、`:342` |

| 事實 | 影響 |
|---|---|
| 兩條都只有 `OFDM081A`(境內)做 | 境外基金主檔的異動兩邊都不會動 |
| 第 1 條在 `FUND_LOCK = 'Y'` 時整段跳過,無提示;第 2 條**沒有這個檢查** | 鎖定的基金:Oracle 側不同步、MSSQL 側照打,兩邊更不一致 |
| 第 2 條在交易外,而且不檢查第 1 步成不成功 | Oracle 成功 / MSSQL 失敗 與 Oracle 失敗 / MSSQL 成功 兩種不一致都可能 |
| `@WOSTATUS` 判 `!= "Y"`,旁邊註解卻寫 `1.資料更新成功 2.失敗` | 〔假設〕SP 不在版控內,無法確認實際回傳值 |
| repo 內查不到 `FND001` 的其他寫入者或補償批次 | 標〔假設〕缺:版控外 |
| 連線名 `"FA"`、表名 `FND001`、SP 名 `S_PAM_OFD081A_AFIZZ020` | 〔客戶特定〕 |

### 8.7 影響面速查

改本片的東西之前,先看這張表。

| 你要改 | 一定要一起看 |
|---|---|
| `OFD081A` 任一欄 | `OFDM081A` 六層 + `FND001` 同步的三段 SQL(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:311-784`)+ MSSQL 預存程序 `S_PAM_OFD081A_AFIZZ020`(版控外)+ `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` + 各模組的 join |
| `OFD081` 任一欄 | `OFDM081B` 六層 + `OFDM082B` 的 `UPDATE` + `ATLAS.OTA` 側 |
| `OFD0811A` 任一欄 | 29 個外部檔 |
| `OFD074` 任一欄 | 36 個外部檔,其中三個是共用 UI 控件 |
| `OFD078` 任一欄 | `OFDM074` 與 `OFDM076` **兩支都要改**,而且要決定 `'ALL'` 這個虛擬業務別怎麼處理 |
| `OFD084A` 任一欄 | `OFDM084Model.xsd` 與 `OFDM081AModel.xsd` **兩份 xsd** |
| `OFD071A` 的有效碼邏輯 | `OFDM071` + `ofd7.md` 那片的促銷活動通路判定 |
| 境內外判斷邏輯 | `OFDM087`(`DECODE`)與 `OFDM088`(`UNION ALL` CTE)**兩種做法**,而且 `OFDM088` 的 CTE 在同一個檔內有兩份 |
| 任何「成對」畫面 | 對照 §2.2.9 的五對表,確認另一邊要不要同步改 |

## 附錄 A. 資料表總表

### A.1 本片宣告的 21 張實體表

| 表 | 主檔於 | 明細於(本片) | 被誰共用(外部檔數) | 欄位定義 xsd |
|---|---|---|---|---|
| `OFD070A` | `OFDM070A` | — | Common / OFDB / OFD.Query(8) | `OFDM070AModel.xsd` 的 `OFDM070A` |
| `OFD070` | `OFDM070B` | — | — | `OFDM070BModel.xsd` 的 `OFDM070B` |
| `OFD071A` | `OFDM071` | — | RSP / Common / OFDB / EC / OFDI / OFD.Query(12) | `OFDM071Model.xsd` 的 `OFDM071` |
| `OFD072A` | `OFDM072` | — | RSP / OFDB / Common / OFDI / OTA.Query(13) | `OFDM072Model.xsd` 的 `OFDM072` |
| `OFD074` | `OFDM074` | — | **Common / OFDB / RSP / BMS / EC.Report / OFD.Query(36)** | `OFDM074Model.xsd` 的 `OFDM074` |
| `OFD075` | — | `OFDM074` | Common / OFD.Query / OFDB(7) | `OFDM074Model.xsd` 的 `OFDM074_Detail` |
| `OFD078` | — | **`OFDM074` 與 `OFDM076` 同時宣告** | **0** | `OFDM074Model.xsd` 與 `OFDM076Model.xsd` 各一份 `OFDM078` |
| `OFD076` | `OFDM076` | — | — | `OFDM076Model.xsd` 的 `OFDM076` |
| `OFD077` | — | `OFDM076` | Common / OFD.Query / OFDB(4) | `OFDM076Model.xsd` 的 `OFDM076_Detail` |
| `OFD081A` | `OFDM081A` | — | 全庫最廣(未逐檔計數) | `OFDM081AModel.xsd` 的 `OFDM081A` |
| `OFD0811A` | — | `OFDM081A`(索引 0) | **Common / BBS / EC / …(29)** | `OFDM081AModel.xsd` 的 `OFDM081A_Remit` |
| `OFD0813A` | — | `OFDM081A`(索引 1) | Common / OFDB / RSP(9) | `OFDM081AModel.xsd` 的 `OFDM081A_Account` |
| `OFD0814A` | — | `OFDM081A`(索引 2)+ **`OFDM082` 直接 UPDATE** | BBS(2) | `OFDM081AModel.xsd` 的 `OFDM081A_NOEVA` |
| `OFD082A` | — | `OFDM081A`(索引 3) | 0 | `OFDM081AModel.xsd` 的 `OFDM081A_MgrFee` |
| `OFD094A` | — | `OFDM081A`(索引 4) | Common / NFD.Report / OFDB(4) | `OFDM081AModel.xsd` 的 `OFDM081A_Custody` |
| `OFD095A` | — | `OFDM081A`(索引 5) | NFD.Report / OFDB(2) | `OFDM081AModel.xsd` 的 `OFDM081A_CustodyDtl` |
| `OFD084A` | `OFDM084` | `OFDM081A`(索引 6) | Common(1) | `OFDM084Model.xsd` 的 `OFDM084`(20 欄)與 `OFDM081AModel.xsd` 的 `OFDM081A_084`(18 欄) |
| `OFD0819A` | — | `OFDM081A`(索引 7) | OFDB(1) | `OFDM081AModel.xsd` 的 `OFDM081A_ACC_NO` |
| `OFD081` | `OFDM081B` | — + **`OFDM082B` 直接 UPDATE** | 全庫廣(未逐檔計數) | `OFDM081BModel.xsd` 的 `OFDM081B` |
| `OFD082` | — | `OFDM081B` | 0 | `OFDM081BModel.xsd` 的 `OFDM081B_082` |
| `OFD083` | — | `OFDM081B` | 0 | `OFDM081BModel.xsd` 的 `OFDM081B_083` |
| `OFD085A` | `OFDM085A` | — | Common / OFDB(6) | `OFDM085AModel.xsd` 的 `OFDM085A` |
| `OFD085` | `OFDM085B` | — | **OTA / OFDB(8)** | `OFDM085BModel.xsd` 的 `OFDM085B` |
| `OFD086` | `OFDM086` | — | **OTA / OTAB(20)** | `OFDM086Model.xsd` 的 `OFDM086` |
| `OFD087A` | `OFDM087` | — | Common / RSP(4) | `OFDM087Model.xsd` 的 `OFDM087` |
| `OFD088A` | `OFDM088` | — | Common / BBS / EC / OFD.Query(5) | `OFDM088Model.xsd` 的 `OFDM088` |
| `OFD091` | `OFDM091B` | — | **OTA / OTAB(11)** | `OFDM091BModel.xsd` 的 `OFDM091B` |

> 上表 27 列,實體表去重後 **21 張**(`OFD084A` 出現兩次、`OFD078` 出現在兩支畫面、`OFD081` / `OFD0814A` 各有兩個寫入者)。

> ⚠ **「掃描器說欄位 0」不等於沒有定義。** 對 `OFD070A` 跑 `atlas_scan.py --table OFD070A` 會得到「欄位 0」,原因與 `ofd7.md 附錄 A` 記的一樣:**xsd 的 DataTable 名跟實體表名不同**(`new xTableMapping("OFD070A", "OFDM070A")`)。要查欄位得照上表最後一欄去對應的 xsd 找。

### A.2 只讀不寫的外部表

| 表 | 用途 | 誰在讀 |
|---|---|---|
| `OFD062` | 基金公司名稱 | `OFDM070A` `OFDM070B` `OFDM074` `OFDM085A` `OFDM085B` `OFDM086` |
| `FSK003` | 幣別名稱 | `OFDM074` `OFDM076` `OFDM084` |
| `OFD020V` | 銀行分行簡稱(`OFDM085A` 用兩次別名) | `OFDM085A` |
| `OFD064` | 基金公司收款銀行預設值 | `OFDM081B.GetOFD064` |
| `OFD221A` / `RSP006A` | 境內交易與定額約定,判斷基金能不能刪 | `OFDM081A.CheckFUND_CURRENCY` |
| `OFD221` / `RSP006` | 境外交易與定額約定,同上 | `OFDM081B.IsTradeData` |
| `FND001` | 基金會計資料,**本片唯一會寫的外部表** | `OFDM081A.UpdateFND001` |

`FSK003` 與 `OFD020V` 不在掃描器索引裡(母體沒收),已加進 meta 的 `refcheck-ignore`;同樣加進去的還有 `OFD084`、`OFD087A`(索引未收)、MSSQL 預存程序 `S_PAM_OFD081A_AFIZZ020`、名單外的 `OFDM084B`,以及 14 個子對話框代號。`OFD064`、`OFD221A`、`OFD221`、`RSP006A`、`RSP006`、`FND001` 則在索引內或未被引用檢查判定為表,不需忽略。

## 附錄 B. SP / Function / Trigger / View

**本片沒有任何自己的 Oracle SP、Trigger 或 View。** 21 張表上沒有掛 Trigger(`DB/Trigger/` 底下沒有對應的檔),`DB/SP/` 底下也沒有 `OFD07*` / `OFD08*` / `OFD09*` 相關的檔。

用到的 DB 端物件只有一個,而且在另一個資料庫:

| 物件 | 型別 | 在哪 | 用途 | 呼叫端 | repo 內有原始碼? |
|---|---|---|---|---|---|
| `S_PAM_OFD081A_AFIZZ020` | Stored Procedure | **MSSQL**(連線名 `"FA"`) | 把一檔境內基金的資料推到基金會計系統;回 `@WOSTATUS` / `@WMESSAGE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:799-808`,由 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:66` / `:91` / `:342` 觸發 | **無**,已加進 `refcheck-ignore` |

`FND001` 這張表本身也不在 `DB/Table/` 內(依 `architecture.md 附錄 B` 的說法,`DB/` 只涵蓋一小部分),但它是 Oracle 表、由本片的 `UpdateFND001` 直接以 SQL 寫入。

## 附錄 C. 代碼對照

全部來自 `Dev/Common/Source/MappingCode/TA.MappingCode/`,不是自己翻的。

| 代碼組 | 值 | 意義 | 用在哪 | 錨點 |
|---|---|---|---|---|
| `SHORE_ID` / `FUND_TYPE` | `1` / `2` | 境外基金 / 境內基金 | 全片 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `YES_NO` | `Y` / `N` | 是 / 否 | `OFDM076` 判核印碼 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-25` |
| `ALLOWANCE_ID` | `1` / `2` / `3` | 前收優惠 / 後收優惠 / 固定 | `OFDM070A` `OFDM074` 手續費拆帳基礎 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1629-1648` |
| `BANK_SUB_TYPE` | `1`~`6` | 小額扣款 / EC / ATM / IVR / 指定 / 信用卡 | `OFDM074` 業務別 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1650-1683` |
| `AGENT_SEAL_TYPE` | `2` / `3` | ACH / 財金 | `OFDM076` 核印扣款方式 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1686-1696` |
| `SEAL_TYPE` | `1` / `2` / `3` | 一般 / ACH / 財金 | `OFDM074` 核印扣款方式 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1702-1717` |
| `SEAL_CHK_CODE` | `1` / `2` | 不核印 / 核印 | `OFDM074` `OFDM076` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1721-1732` |
| `SEAL_FEE_ID` | `N` / `Y` | 不收核印費 / 收核印費 | `OFDM076` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1736-1748` |
| `FEE_PAY_ITEM` | `1` / `2` | 扣帳費 / 手續費 | `OFDM074` 費用支付種類 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1752-1764` |
| `COLLECT_ID` | `1` / `2` | 匯款 / 支票 | `OFDM070A` `OFDM074` `OFDM076` 取款方式 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3063-3074` |
| `STOP_TRADE_TYPE` | `0`~`5` | 全部交易 / 申購 / 贖回 / 轉換 / 定額約定 / 定額扣款 | `OFDM087` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:907-934` |
| `FUND_CALENDER_TYPE` | `1`~ | 公布淨值日 … | `OFDM088` 行事曆類別 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:937-948` |
| `AFEE_TYPE` | `1` / `2` | 前收 / 後收 | `OFDM081A` `OFDM081B` `OFDM085A` 申購手續費收取方式 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3533-3545` |
| `DIVIDEND_TYPE` | `1`~`4` | 可選配 / 配現金 / 配單位數 / 不配 | `OFDM081A` `OFDM085A` 收益分配方式 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:288-307` |

**兩個字典跟不上程式的地方:**

| 代碼 | 程式用到的值 | 字典有的值 | 依據 |
|---|---|---|---|
| `AFEE_TYPE` | `OFDM081A` 判 `"4"`(註解「4後收-成本市價孰低」)、`OFDM085Ap0` 判 `"4"` | 只有 `1` 前收 / `2` 後收 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:326-331`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:472`;`ofd7.md 附錄 C` 也記到同一個字典,而且那裡把 `"2"` 註成「混收型」與「後收」打架 |
| `CDSC_TYPE`(銷售機構傳輸方式) | `OFDM070A` 用 `GetDropDownDataSrc("651")` 從 DB 取值 | 沒有 C# 字典 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:79` |

**四個只能從 DB 下拉表取、repo 內查不到值域的代碼**(全部標〔假設〕缺:DB 連線):

| 代碼 | 取值來源 | 用在哪 |
|---|---|---|
| `GetDropDownDataSrc("651")` | DB 下拉表 651 | `OFDM070A` 的 `CDSC_TYPE` |
| `GetDropDownDataSrc("652")` | DB 下拉表 652 | `OFDM085A` 的 `CDSC_TRAN_CD` |
| `GetDropDownDataSrc("932")` | DB 下拉表 932 | `OFDM070B` 的三個「交易資料彙入處理」 |
| `GetDropDownDataSrc("933")` | DB 下拉表 933 | `OFDM070B` 的銷售機構有效碼(境外) |

**`STATUS` 的值域仍未確認**:本片唯一直接判字面量的地方是 `OFDM081A.Copy` 的 `STATUS.StartsWith("3")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:978`)。與 `ofd7.md 附錄 C` 記的 `'301'` 同屬「3 開頭 = 已覆核」的推測,但 `architecture.md §3.10` 從全庫掃到的是單字元 `'0'`~`'9'`,兩邊對不上。標**〔假設〕缺:DB 連線**。

## 附錄 D. 掃描母體與覆蓋率

`atlas_scan.py --module OFD` 對單片沒有意義(OFD 有 550 支),所以改成逐支列。

### D.1 17 支畫面的處置、PO 基底與 csproj

| # | 畫面 | 處置 | 章節 | 深度 | **PO 基底** | **在 csproj** |
|---|---|---|---|---|---|---|
| 1 | `OFDM081A` | 已寫 | §4.1 | **最深**(八明細 + `FND001` + MSSQL SP) | `BaseEVADaoPO` | 六層全在 |
| 2 | `OFDM081B` | 已寫 | §4.2 | **深寫**(成對比較 + 57 條檢核) | `BaseEVADaoPO` | 六層全在 |
| 3 | `OFDM082` | 已寫 | §4.3 | **深寫**(繞過四眼) | `BaseEVADaoPO`(不用四眼) | 六層全在 |
| 4 | `OFDM082B` | 已寫 | §4.3 | **深寫**(繞過四眼 + 直接改主檔) | `BaseEVADaoPO`(不用四眼) | 六層全在 |
| 5 | `OFDM084` | 已寫 | §4.4 | 一支一節 | `BaseMultiRowEVADaoPO` | 六層全在 |
| 6 | `OFDM087` | 已寫 | §4.5 | **深寫**(境內外併表 + 舊方法並存) | `BaseEVADaoPO` | 六層全在 |
| 7 | `OFDM088` | 已寫 | §4.6 | **深寫**(三個批次鈕 + 跨庫交易) | `BaseMultiRowEVADaoPO` | 六層全在 |
| 8 | `OFDM091B` | 已寫 | §4.7 | 一支一節 | `BaseEVADaoPO` | 六層全在 |
| 9 | `OFDM085A` | 已寫 | §4.8 | **深寫**(CDSC 檢核 + 三值邏輯) | `BaseMultiRowEVADaoPO` | 六層全在 |
| 10 | `OFDM085B` | 已寫 | §4.8 | 群組節(與 `OFDM086` 對照) | `BaseMultiRowEVADaoPO` | 六層全在 |
| 11 | `OFDM086` | 已寫 | §4.8 | 群組節 | `BaseMultiRowEVADaoPO` | 六層全在 |
| 12 | `OFDM070A` | 已寫 | §4.9 | **深寫**(成對比較) | `BaseMultiRowEVADaoPO` | 六層全在 |
| 13 | `OFDM070B` | 已寫 | §4.9 | **深寫**(成對比較 + 訊息沒改) | `BaseMultiRowEVADaoPO` | 六層全在 |
| 14 | `OFDM071` | 已寫 | §4.10 | **深寫**(六支檢核 + `catch` 兩種相反失效) | `BaseEVADaoPO` | 六層全在 |
| 15 | `OFDM072` | 已寫 | §4.11 | 一支一節 | `BaseEVADaoPO` | 六層全在 |
| 16 | `OFDM074` | 已寫 | §4.12.1~2 | **深寫**(共用 `OFD078` + 跨列同步) | `BaseEVADaoPO` | 六層全在 |
| 17 | `OFDM076` | 已寫 | §4.12.3~4 | **深寫**(共用 `OFD078` + 寫死 `'ALL'`) | `BaseEVADaoPO` | 六層全在 |

**17 / 17 = 100%**,沒有「無關」或「停用」需要處置的。**繼承 `BasicEVAPO` / `MultiRowEVAPO` 的:0 支。不在 csproj 的:0 支。**

### D.2 名單外但同屬 `DataEntity.OFD5` 的一支

| 畫面 | 處置 | 章節 | PO 基底 | 在 csproj |
|---|---|---|---|---|
| `OFDM084B` | **表格帶過**(只做境內外對照) | §2.2.5、§3.5 | `BaseMultiRowEVADaoPO` | 六層全在,但 Control 層的檔名是 `OFDM084B_Ctl .cs`(副檔名前多一個空白),掃描器看不到 |

### D.3 其他對象的覆蓋率

| 對象 | 母體 | 本文明確引用 | 覆蓋 |
|---|---|---|---|
| 本片宣告的實體表 | 21 | 21(附錄 A.1 全列) | 100% |
| 外部唯讀 / 外寫表 | 11 | 11(附錄 A.2 全列) | 100% |
| DB 物件(MSSQL SP) | 1 | 1(附錄 B) | 100% |
| 子對話框 | 14 | 14(§3.1 逐支列) | 100% |
| 代碼組 | 14 + 2 跟不上 + 4 查不到 | 20(附錄 C) | 100% |

### D.4 本文沒做到的事

| 項目 | 原因 |
|---|---|
| `S_PAM_OFD081A_AFIZZ020` 實際回傳什麼 | SP 在 MSSQL 且不在版控內,需要 DB 連線 |
| `FND001` 的完整欄位定義與其他寫入者 | 不在 `DB/Table/` |
| `STATUS` 的完整值域、`"3"` 開頭是不是已覆核 | `EVAStatusCode` 在 DLL 內,需要反編譯或查 DB |
| `AFEE_TYPE = "4"` 的正式名稱 | 字典只有 `1` / `2`,只能引用程式註解「後收-成本市價孰低」 |
| DB 下拉表 `651` / `652` / `932` / `933` 的值域 | 需要 DB 連線 |
| 框架在「明細零列」時會不會觸發 `AfterAdd` / `AfterUpdate` | `BaseEVADaoPO` 無原始碼(影響附錄 E.3 的嚴重度判定) |
| `OFD0814A` 是否有 `FH_CD` 欄位(影響 `OFDM082` 的 ambiguous column 風險) | xsd 內的 `OFDM082` vdb 表只有 18 欄,實體表欄位未知 |
| `xMaintainForm` / `LevelGridUtility` / `ClientBizUtility` / `CommonGridHelper` 的內部行為 | 框架 DLL,無原始碼,從呼叫端反推 |

## 附錄 E. 讀本文時要注意的地方

20 條,依嚴重度排。每條格式:缺陷 / 影響 / 錨點 / 嚴重度。

### E.1 `OFDM082` / `OFDM082B` 繞過四眼直接改資料 —— 嚴重度 **高**

**缺陷**:兩支畫面繼承四眼基底 `BaseEVADaoPO`,建構子卻是空的(沒有 `MasterTable`、沒有掛任何事件),排序功能自己 `BeginTransaction()` 後直接下 `UPDATE`,只寫 `REPORT_SEQ` / `UPDATEID` / `UPDATEDATE`。

**影響**:(a) `STATUS` 與 `ENTRYID` / `VERIFYID` / `APPROVEID` 原封不動,資料改過之後四眼狀態顯示「已覆核」,ToDo 清單不會出現任何待辦;(b) `OFDM082B` 改的是**基金主檔 `OFD081`** 本身,等於有一條路徑可以不經覆核改基金主檔的欄位;(c) 沒有任何稽核軌跡指出誰改了排序。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:26-33`(空建構子)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:60-64`(境內 UPDATE)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:66-70`(境外 UPDATE)。

### E.2 Oracle 三值邏輯:`欄 <> '值'` 遇 `NULL` 是 UNKNOWN —— 嚴重度 **高**

**缺陷**:四處把 `<>` 當成「不等於就算數」用,但 Oracle 裡只要有一邊是 `NULL`,整個比較就是 `UNKNOWN`,該列不會被選到。

| 位置 | SQL 片段 | 遇 NULL 的後果 | 錨點 |
|---|---|---|---|
| `OFDM085A.Check_Switch_Fund_Id` 第 2 個 `WHEN` | `OFD081A.CDSC_YEARS <> SW_OFD081A.CDSC_YEARS` | `WHEN` 不成立 → 掉到 `ELSE 'CheckOK'` → **後收年限檢核放行** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:179` |
| 同上第 3 個 `WHEN` | `OFD081A.AFEE_TYPE <> SW_OFD081A.AFEE_TYPE` | 同上 → **期滿前轉入限制放行** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:180` |
| `OFDM074.intBANK_HQ_COUNT`(3 參數) | `BANK_SUB_TYPE<>'{1}' AND UNIT_CODE<>'{3}'` | `UNIT_CODE` 還沒設過(NULL)的列不算進「要同步的筆數」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:315-319` |
| `OFDM074.intBANK_HQ_COUNT`(4 參數) | `BANK_SUB_TYPE<>'{1}' AND DATA_CENTER='{3}'` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:352-356` |

**同一段 SQL 裡的第 1 個 `WHEN` 反而用了 `NVL(:CDSC_TRAN_CD,' ')` 保護**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:178`),可見寫的人知道 NULL 的問題,只是沒套到後面兩條。`CDSC_YEARS` 在非後收基金上本來就常是 `NULL`(`OFDM081A` 只在 `AFEE_TYPE = "4"` 時才強制填)。

另外兩處 `FUND_ID <> :FUND_ID` 的用法(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:936-939`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:165-168`)是**同型但不發作**:`FUND_ID` 是主鍵,不會是 NULL。

### E.3 `OFDM081A` 的 `FND001` 同步靠「哪一張明細寫完」判斷,而且兩個事件用不同索引 —— 嚴重度 **高**

**缺陷**:`AfterAdd` 判 `DetailTable[7]`(`OFD0819A`)、`AfterUpdate` 判 `DetailTable[6]`(`OFD084A`)。索引是 2018 年被刻意從 7 改成 6 的,但只改了 `AfterUpdate` 一邊。

**影響**:(a) 判準本身脆弱——它假設框架一定會為那張明細觸發一次事件,若該次存檔那張明細沒有異動列而框架因此不觸發,`FND001` 整批不同步且無任何錯誤;(b) 兩個事件的判準不同,任何人調整 `DetailTable` 的宣告順序就會同時打壞兩條,而且壞法不一樣。**資料新舊上不會出事**(同步來源只讀索引 0 / 1 / 2 三張明細,都排在 6 / 7 之前)。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:143-159`(Add,索引 7)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:165-180`(Update,索引 6)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:171`(被註解的原版)。**〔假設〕** 框架零列時是否觸發事件,無原始碼可確認。

### E.4 同一份 `catch` 樣板,在不同呼叫端失效成相反的方向 —— 嚴重度 **高**

**缺陷**:`OFDM071` 的六支檢核 PO 方法 `catch` 全部寫成 `AddResultRow(false, 0, "")`,但 UI 對 `ReturnCode` 的解讀分成兩組。

| 組 | 方法 | UI 判法 | DB 出錯時 |
|---|---|---|---|
| 「有子通路就擋」 | `CheckM_Data` `Check_Middle_Data` `IsExsit_Middle_ChannelData` `IsExsit_Small_ChannelData` | `if (ReturnCode) AddError(...)` | **該擋沒擋**:可以把有下層的通路設成無效或刪掉 |
| 「上層必須存在」 | `CheckB_Data` `CheckData` | `if (!ReturnCode) AddError("不存在此大通路…")` | **不該擋卻擋**:使用者看到「不存在此大通路」但其實是 DB 有問題 |

**同型的還有 `OFDM076` 的兩支限額檢核**:`catch` 回 `false`,UI 判 `if (ReturnCode == true) AddError(...)` → **DB 出錯就放行**,代理扣款機構可以設出低於核印扣款機構的限額。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:152-157`(樣板)、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:229-233`(第一組)、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM071.cs:318-321`(第二組)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:712-717` 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:86-89`。

**做對的對照組**:`OFDM085A.Check_Switch_Fund_Id` 的 `catch` 回 `AddResultRow(false, 0, "檢核失敗，請檢查")`,呼叫端判 `!ReturnCode` 就加錯誤 → **失敗時是擋下來**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM085A_PO.cs:212-217`)。

### E.5 共用表 `OFD078`:兩支畫面各看一半,而且都不知道另一半存在 —— 嚴重度 **高**

**缺陷**:`OFD078` 的 PK 是 `BANK_HQ` + `SEAL_TYPE` + `BANK_SUB_TYPE` + `FUND_ID` + `CRNCY_CD`,但 `OFDM076` 的主檔 PK 沒有 `BANK_SUB_TYPE`,所以它對 `OFD078` 寫死 `AND OFD078.BANK_SUB_TYPE = 'ALL'`;`OFDM074` 則帶真實業務別。

**影響**:同一家扣款機構若同時出現在兩支畫面,`OFDM074` 看不到 `'ALL'` 那些列、`OFDM076` 看不到真實業務別那些列,**兩邊都沒有任何提示**。要刪一家機構的所有幣別設定,必須兩支畫面都跑一次。結果類型:**過濾(無提示)**。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:337-338`(寫死 `'ALL'`)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:226`(帶真實業務別)、兩份 xsd 的 `OFDM078` PK 定義。

### E.6 `OFDM074` 的 EC 檢核被一段「已註解掉訊息」的變數綁住 —— 嚴重度 **高**

**缺陷**:「(書面)扣帳費要有幣別手續費」那條檢核的 `AddError` 被註解掉了,但計算 `isHasNoData` 的那一行沒有被註解;而「(EC/IVR)扣帳費要有幣別手續費」那條的條件是 `if (strFEE_PAY_ITEM_EC == FEE_PAY_ITEM.Deduct && isHasNoData)`。

**影響**:EC 那條檢核只在「書面也是扣帳費、而且書面的手續費有缺」時才會跑。書面資料完整、或書面根本不是扣帳費時,`isHasNoData` 是 `false`,**EC 的幣別手續費就算全空也不會擋**。

**錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:398-410`(被註解的那半)、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM074.cs:412-424`(被綁住的那半)。

### E.7 `OFDM081A` 的 MSSQL 同步在交易外、不檢查前一步、判斷值與註解打架 —— 嚴重度 **高**

**缺陷**:五件事疊在一起,見 §4.1.6。

| # | 事實 | 錨點 |
|---|---|---|
| 1 | Ctl 在 `ExecPOActionToViewVDB(...)` 回來(Oracle 已 commit)之後才呼叫 SP | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:61-66` |
| 2 | 不檢查 `Add` / `Update` 的結果就打 SP | 同上 |
| 3 | `@WOSTATUS` 判 `!= "Y"`,旁邊註解寫 `1.資料更新成功 2.失敗` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:805-812` |
| 4 | 公開多載沒有 `FUND_LOCK` 檢查(死掉的 private 多載有) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:787-790` vs `:826-830` |
| 5 | `new OFDM081A_PO()` 繞過 `GetDaoInstance`,每次多建一條 MSSQL `Database` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM081A_Ctl.cs:64` |

**影響**:Oracle 與 MSSQL 兩邊都可能單邊成功;`Add` 與 `Copy` 兩個入口沒有 try,SP 一丟例外就直接往上竄。**〔假設〕** 第 3 點要確認 SP 實際回傳值才知道是不是「成功也丟例外」。

### E.8 `OFDM081B`(境外)沒有任何下游同步 —— 嚴重度 **中**

**缺陷**:`OFDM081B_PO` 整支沒有任何 `After*` 事件,境外基金主檔異動不會進 `FND001`,Ctl 層也沒有呼叫 SP。

**影響**:如果 `FND001` 的設計是「所有基金」,境外那一半永遠缺;如果設計就是只收境內,那 `OFDM081A` 那一套是對的,本條不成立。repo 內查不到 `FND001` 的欄位定義,無法判斷。**〔假設〕缺:版控外**。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081B_PO.cs:42-58`(建構子只掛三個取數事件)。

### E.9 只有一支方法帶 T-SQL 痕跡,而它正好是跨庫那一支 —— 嚴重度 **中**

**缺陷**:17 支 PO 的 SQL 清一色 Oracle 語法,唯一的 `SqlDbType` 與 `@` 參數集中在 `UpdateFND001_NEW`。這不是「沒遷移的舊世代」,是刻意的跨庫呼叫;但它讓「用 `@變數` 判斷舊世代」這條啟發式在本片誤判。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:799-808`。

### E.10 兩道「有錯還回 `true`」的早退 —— 嚴重度 **中**

**缺陷**:`OFDM081A.DoValidate()` 內兩處 `if (this.ValidateErrList.ErrorCount > 0) return true;`。

**影響**:目前不是漏洞(三個呼叫端都寫成 `if (!DoValidate() || ValidateErrList.Show())`),但(a) 使用者要按兩次以上存檔才看得完所有錯誤;(b) 只要有人把呼叫端簡化成 `if (!DoValidate()) return;`,後半段十餘條檢核就全部失效。**同型但方向相反**的寫法在 `OFDM087.DoValidate()` 是 `return;`(void),那支只有「要按兩次」的問題。

**錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:197`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:246`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:222-223`。

### E.11 成對畫面只改一邊 —— 嚴重度 **中**

本片找到五處:

| # | 位置 | 只改了一邊的內容 | 錨點 |
|---|---|---|---|
| 1 | `OFDM070B` 的存檔錯誤訊息 | 境外畫面仍然說「銷售機構承銷**境內**基金設定明細資料 必須輸入」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070B.cs:53` |
| 2 | `OFDM082B` 的參數物件 | `dbProduct.AddInParameter(...)` 配 `dbTA.GetSqlStringCommand(...)` / `dbTA.ExecuteScalar(...)`;境內版全程 `dbTA` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:83`、`:97-100` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:78`、`:88-91` |
| 3 | `OFDM082B` 的 `DbCommand` 建立位置 | 建在迴圈外,境內版建在迴圈內 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:74-75` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:72-73` |
| 4 | `OFDM084B` 的明細 join | `INNER JOIN OFD081`,境內版是 `LEFT JOIN OFD081A` → 基金被移除時明細列靜靜消失 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs:104-105` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:93` |
| 5 | `OFDM084` 的 `MasterPKey` | 少了 `OPEN_TYPE`(被註解),境外版保留 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084_PO.cs:30` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM084B_PO.cs:39` |

### E.12 `catch` 內第一行就 `tran.Rollback()`,`tran` 可能是 `null` —— 嚴重度 **中**

**缺陷**:`tran = dbXxx.BeginTransaction()` 寫在 `try` 內,`catch` 第一行就 `tran.Rollback()`。若 `BeginTransaction()` 本身丟例外,`catch` 內會再丟一次 `NullReferenceException`,原始例外被蓋掉。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:128-130`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:133-135`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:340-347`(這支還一次 rollback 兩條)。

### E.13 `OFDM088` 跨兩個資料庫的 commit 不是原子的 —— 嚴重度 **中**

**缺陷**:`tran.Commit(); tranptpf.Commit();` 是兩句話。第一句成功、第二句失敗時,業務資料已進去、ToDo 沒進去,而 `catch` 會對兩條都呼叫 `Rollback()`(對已 commit 的無效)。

**影響**:行事曆建好了但沒有人收到覆核通知,畫面卻顯示「新增失敗」。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:337-338`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:560-561`。

### E.14 檢核 / 訊息被註解,外殼還在 —— 嚴重度 **中**

| 位置 | 被註解的內容 | 錨點 |
|---|---|---|
| `OFDM072` | ID 格式檢核(8 碼統編 / 10 碼身分證),以及「同一大通路下推薦人重複」兩段;後者呼叫的 `CheckSPONSOR_IDNO` / `CheckSPONSOR` 連方法都不在 PO 裡了 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM072.cs:140-164`、`:166-198` |
| `OFDM087` | 四段「暫停日期不可小於基金成立 / 發行日期」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs:250-266` |
| `OFDM087` | `GetFundStopDateData` 內 14 行手寫四眼欄位清單,已被 `AllEVAColumnsForSelect` 取代 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:249-262` |
| `OFDM081A` | 官網 CMS 拋轉:事件掛載、第二條連線、方法本體呼叫全被註解,`UpdateCMSFundA` 的前半(讀 Oracle)還會執行 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:64-72`、`:202-208`、`:216-302` |
| `OFDM081A` | 六組日期順序檢核裡有四組被註解(發行日、NAV 起算日、短線交易開始日、集保上線日) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:203-220` |
| `OFDM091B` | `BeforeUpdate` 掛載被註解,`AfterUpdate` 掛著但方法本體只有 `//nothing` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:50-51`、`:66-69` |
| `OFDM070A` | `MasterPKey` 的 `SHORE_ID` 被註解(「2014/03/18 ATLAS ATLAS SHORE_ID已停用」),UI 的下拉清單還在 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM070A_PO.cs:39-40` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM070A.cs:83-86` |

**`OFDM072` 那一條後果最大**:目前唯一還在跑的推薦人 ID 檢核是**詢問式**的(按「是」就放行並寫 ByPass),所以推薦人 ID 實際上可以是任何字串。

### E.15 字串串接進 SQL —— 嚴重度 **高**(範圍廣)

17 支 PO 裡有 8 支用字串串接組 SQL 條件,全部是查詢條件而非寫入,但仍是注入點,而且值含單引號時直接語法錯誤。

| 畫面 | 型態 | 錨點 |
|---|---|---|
| `OFDM071` | `string.Format` 串通路代碼,六支方法都有 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:189-192`、`:243-246`、`:299-302`、`:361-364`、`:420-423` |
| `OFDM074` | `string.Format` 串四個值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:322`、`:358` |
| `OFDM076` | 查詢條件 `" And OFD078." + Row.Name + " = '" + Row.Value + "'"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:343-350` |
| `OFDM082` / `OFDM082B` | `" And FH_CD = '" + Row.Value + "'"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:207-213`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:188-194` |
| `OFDM087` | 四組 `" And OFD087A." + pRow.Name + " = '" + pRow.Value + "'"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:145-150`、`:175-180`、`:189-194`、`:277-282` |
| `OFDM091B` | `" And OFD091." + Row.Name + " = '" + Row.Value + "'"` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091B_PO.cs:147-152` |
| `OFDM088` | `String.Format` 餵 `DataTable.Select()`(不是 SQL,但同一個問題) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:330` |

**注意 `Row.Name` 也被串進去**,不只值。查詢參數名若可由用戶端控制,等於可以指定任意欄位名。

### E.16 訊息是空字串,使用者看不到失敗原因 —— 嚴重度 **中**

**缺陷**:`OFDM082` / `OFDM082B` 的四個失敗出口有三個是 `AddResultRow(false, 0, "")`;`OFDM088` 的筆數不符是 `throw new ApplicationException("")`。

**影響**:使用者按了功能鈕、跳一個沒有內容的失敗訊息,無從判斷是資料問題還是系統問題。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:105-112`、`:124-131`、`:128-141`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:557-558`。

### E.17 `ExecuteNonQuery` 的回傳值被當成累加,實際是覆寫 —— 嚴重度 **中**

**缺陷**:`i = dbTA.ExecuteNonQuery(cmdUpdate, tran);` 旁邊的註解寫「累加修改資料筆數」,但用的是 `=` 不是 `+=`。

**影響**:迴圈結束後的 `if (i > 0)` 判的是**最後一列**的結果;若明細零列,`i` 維持 0 → 走 else → Rollback + 空訊息。回報給使用者的「成功筆數」也只會是 1。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:102`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082B_PO.cs:102`。

### E.18 `OFDM085Ap0` 同一支方法內,兩段檢核一段判 `null` 一段不判 —— 嚴重度 **中**

**缺陷**:第一段寫 `if (this.custSWITCH_FUND_ID.SelectedDataRow != null && …)`,第三段直接 `((OFD_FUND_IDListView.FUND_IDListRow)this.custSWITCH_FUND_ID.SelectedDataRow).AFEE_TYPE == "4"`。

**影響**:使用者若手打基金代碼而沒從搜尋器挑,`SelectedDataRow` 為 `null` 時存檔會丟 `NullReferenceException`。**〔假設〕** 未實測手打代碼時 `SelectedDataRow` 是否一定為 `null`;但同一支方法內寫法不一致是確定的。

**錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:464`(有判)vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:489`(沒判)。

### E.19 查詢條件的 `else` 分支吃掉所有非 `"1"` 的值 —— 嚴重度 **中**

**缺陷**:`OFDM087` 的境內外過濾寫成 `if (pRow.Value == "1") …境外… else …境內…`,沒有判 `== "2"`。

**影響**:只要 `FUND_TYPE` 參數存在而值不是 `"1"`(含空字串),就一律加上 `AND OFD081A.FUND_ID IS NOT NULL`,境外的暫停設定查不到。結果類型:**過濾(無提示)**。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:153-167`。

### E.20 三支畫面的來源檔不是 UTF-8 —— 嚴重度 **中**

**缺陷**:本片 68 個六層檔案中有 **21 個是 cp950**(Big5),其餘是 UTF-8 with BOM。

| 畫面 | cp950 的層 |
|---|---|
| `OFDM074` | PO · Control · FormProxy |
| `OFDM076` | PO · Control · FormProxy |
| `OFDM082` | PO · Control · FormProxy |
| `OFDM082B` | PO · Control · FormProxy |
| `OFDM085A` | PO · Control · FormProxy |
| `OFDM085B` | PO · Control · FormProxy |
| `OFDM086` | PO · Control · FormProxy |
| `OFDM087` | **四層全部**(PO · UI · Control · FormProxy) |
| `OFDM088` | PO · UI |
| 子對話框 | `OFDM088p0` `OFDM088p1` `OFDM088p2` |

**影響**:任何以 UTF-8 讀檔的工具(含 `atlas_scan.py` 以外的一般 grep / diff / CI lint)看到的中文是亂碼;改檔時若編輯器另存成 UTF-8,整檔的中文訊息會在其他 Big5 檔的對照下不一致。讀這些檔一律走 `sys.path.insert(0,'/docs/tools'); from atlas_scan import read_text`。

**錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs`(cp950)、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM087.cs`(cp950)、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs`(cp950)。

### E.21 其餘小事彙整 —— 嚴重度 **低**

| # | 事項 | 錨點 |
|---|---|---|
| 1 | `OFDM084B_Ctl .cs` 檔名的副檔名前多一個半形空白,csproj 照抄,所以編得起來但所有檔名比對工具都漏掉它 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/Control.OFD.csproj:121` |
| 2 | `OFDM082` 把 `OFD081A` 別名成 `OFD081`,在一份「`OFD081` = 境外」的程式庫裡最容易讀錯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:187` |
| 3 | `OFDM082` 的 `WHERE … And FH_CD = '…'` 沒有加表別名前綴,`OFD0814A` 若長出同名欄位會 ambiguous | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:211` |
| 4 | `OFDM088.SetHoliday` 判長度 `> 200` 卻截成 `Substring(0, 199)`,少一個字 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:295-302` |
| 5 | `OFDM087_PO.DoValidate` 不管載回幾列一律 `AddResultRow(true, …)`,靠 UI 自己數列數才擋得住 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:389-390` |
| 6 | `OFDM071.CheckData` / `CheckB_Data` 用 `SELECT COUNT(*), CHANNEL_CODE … GROUP BY` 配 `ExecuteScalar`,語意錯但結果剛好對 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:239-256` |
| 7 | `OFDM076` 的 `View.Util.Result[0]` 未檢查 `Count` 就取用 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM076.cs:86` |
| 8 | `OFDM081A.Copy` 八張明細只複製三張(加上有條件的 `OFD084A`),沒有註解說明是否刻意 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:983-1002`。**〔假設〕** |
| 9 | `OFDM081A` 的刪除閘門在伺服端回 `-1` 時只 `return`,`ButtonDeleteEnable` 停在上一次的狀態、`SetData()` 也沒跑 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:1292-1300` |
| 10 | 寫死常數:郵局 `"700"`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM074_PO.cs:455`)、業務別 `'ALL'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM076_PO.cs:338`)、`AFEE_TYPE = "4"`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:326`)、`DIV_PAY_DESK = "2"`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM081A.cs:186`)、`STATUS.StartsWith("3")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:978`) | 〔客戶特定〕 |
| 11 | `OFDM085Ap0` 用 `custSWITCH_FUND_ID.SHORE_ID`,`OFDM085Bp0` / `OFDM086p0` 用 `custFUND_IDSide.SOURCE_CD`,兩種控件兩種屬性做同一件事 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Ap0.cs:80` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM085Bp0.cs:58-59` |
| 12 | `OFDM088` 的 `MYOFD081A` CTE 在同一支 PO 內抄了兩份(主檔與明細各一),改一邊要改兩邊 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM088_PO.cs:60-77` 與 `:123-140` |
| 13 | `OFD081` 的 `REGIST_CODE` / `INVEST_AREA` / `INVEST_CODE` 三欄 Caption 都是「註冊地代碼」 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081BModel.xsd` |
| 14 | `OFD076` 39 欄只有 4 欄有 Caption、`OFD084A` 18 欄全空,查中文名要往別處找 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM076Model.xsd`、`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM084Model.xsd` |
| 15 | `OFDM081A` 的第 2 張明細 vdb 名叫 `OFDM081A_NOEVA`,但 `OFD0814A` 實際上有完整四眼 13 欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM081A_PO.cs:46` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM082_PO.cs:172-186` |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD5` 底下被指派的 17 支 M 畫面,含五對境內 / 境外配對的逐對驗證、`OFD078` 共用明細分析、`OFDM081A` 的 `FND001` 與 MSSQL 預存程序雙下游,以及 21 條缺陷型錄 |

由 build_doc.py v2.0.0 於 2026-09-15 14:05 產生 · 標題 132 · 圖 5 · 表格 87 · 程式錨點 463 · § 連結 87 · 引用檢查：畫面 28（缺 0） · Table 35（缺 0） · 結果集 18（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
