<!-- 由 tools/build_copilot_kb.py 從 modules/ofd5.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
