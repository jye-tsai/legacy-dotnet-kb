<!-- 由 tools/build_copilot_kb.py 從 modules/ofd4.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
