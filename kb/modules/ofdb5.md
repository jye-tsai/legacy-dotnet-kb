<!-- 由 tools/build_copilot_kb.py 從 modules/ofdb5.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFDB5 模組(OFD 批次第 5 片:OFDB / OTAB 兩專案)全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:OFD 前綴的 B 批次全庫拆多片;本篇涵蓋最後未寫過的 **58 支** —— `Dev/ATLAS.OFDB/` 26 支 + `Dev/ATLAS.OTAB/` 32 支(清單見 §3.3)。`ofdb.md` / `ofdb3.md` / `ofdb4.md` 已寫過的不重述。 **建議讀法**:趕時間只讀四段 —— **§0.2(本片最反直覺的七件事,第一件直接決定七支畫面按下去會不會爆)**、§3.3(58 支清冊七欄)、§6.2(`OFDB051`–`OFDB135` 那三條流水線怎麼串)、附錄 E(踩雷)。

> ⚠ **本片的業務意義**(§0)由表名、Designer 內的中文標籤字串、`#region` 中文註解與訊息字串**推測**。ATLAS 沒有把畫面中文名放進版控,本片 58 支沒有任何一支有 `this.Text`。 ⚠ **〔客戶特定〕**:`PO.OFDB` 的 `App.config` 內明文資料庫連線(只記位置不抄值)、`CTL014(953)` 的 API 路徑代碼、`SOURCE_CD='2'` / `SYSTEM_ID='0'` / `TRAN_PAY_WAY='2'` / `Status='302'` 等代碼值為本站台的值。 ⚠ **〔共用〕**:`BMS001A` / `BMS001` 由 BMS 維護;`OFD081A` / `OFD081V`(境內基金主檔與檢視)、`OFD081`(境外基金主檔)、`CTL014`(代碼值域)、`FSK003` 同時服務多模組(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層與命名例外看 `architecture.md §2`、四眼看 `architecture.md §3`、資料存取看 `architecture.md §5`、畫面型別看 `architecture.md §6`、Remoting 與 WindowsService 看 `architecture.md §8.4`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 58 支管什麼(推測)

**一句話:`ATLAS.OFDB` 是「境內基金」的批次專案,`ATLAS.OTAB` 是「境外基金」的批次專案 —— 兩邊都叫 `OFDBnnn`,因為 ATLAS 的代號命名的是「模組 + 型別」(OFD 模組的 B 型畫面),不是「專案」。**

證據鏈四條,逐條可驗:

| # | 證據 | 錨點 |
|---|---|---|
| 1 | repo 裡 `ATLAS.OFD` 與 `ATLAS.OFDB` 成對、`ATLAS.OTA` 與 `ATLAS.OTAB` 成對。`OTAB` 就是 OTA 的 Batch | `Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/PO.OTAB.csproj` |
| 2 | namespace 分兩支:`Vendor.Product.TA.PO.OFDB` 與 `Vendor.Product.TA.PO.OTAB` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:12`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:22` |
| 3 | 交易表的 `A` 後綴分家:`OFDB` 那 26 支動 `OFD220A` / `OFD221A` / `OFD251A` / `OFD303A`(境內);`OTAB` 那 32 支動 `OFD220` / `OFD221` / `OFD251` / `OFD303`(境外) | §2.2 |
| 4 | `OTAB901` 的介面註解直接寫「境外基金主檔」對應 `OFD081`(不帶 A) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:30-33` |

**〔陷阱〕`ATLAS.OTAB` 的資料夾名是 `PO.OTA` / `Control.OTA` / `UI.OTA`(沒有 B),但 csproj、組件名、namespace 全是 `OTAB`。** `Dev/ATLAS.OTAB/Source/UI/UI.OTA/UI.OTAB.csproj`、`Dev/ATLAS.OTAB/Source/Control/Control.OTA/Control.OTAB.csproj`。用資料夾名 grep 會把 `ATLAS.OTA`(維護 / 查詢 / 報表)跟 `ATLAS.OTAB`(批次)混在一起。

**逐支比對代號有無重疊:本片 58 支,重疊 0 支。** 把兩個專案的 PO 檔名全掃一遍(`PO.OFDB` 106 支、`PO.OTA` 43 支),兩邊同名的只有 `OFDB562` / `OFDB563` / `OFDB564` 三支 —— 那三支 `ofdb3.md §2.5` 已經查證過是新舊世代,**不在本片名單內**。本片 58 支在對面專案一支都找不到同名檔。

再往下切成七群業務:

| 群 | 專案 | 管什麼(推測) | 畫面 |
|---|---|---|---|
| **A 境內扣款比對與確認** | OFDB | 傳真委扣 / 匯款入帳檔的上傳、比對、作廢、扣款行確認 | `OFDB221` `OFDB236` `OFDB237` `OFDB239` `OFDB240` `OFDB241` `OFDB242` `OFDB303` `OFDB307` |
| **B 境內日結轉與付款** | OFDB | 申購日結轉、買回日結轉、退匯付款通知、拆單 | `OFDB305` `OFDB323` `OFDB330` `OFDB311` |
| **C 境內檔案 / 報表產出** | OFDB | 受益分配下載檔、扣繳憑單媒體、買回付款媒體、後收級別費用、服務費 | `OFDB285` `OFDB289` `OFDB290` `OFDB328` `OFDB351` `OFDB432` `OFDB434` |
| **D 境內基金清算價金給付** | OFDB | 清算資料產生 → 確認 → 退匯 / 退郵 / 重匯重寄 | **`OFDB481A` `OFDB486A` `OFDB487A` `OFDB489A` `OFDB490A` `OFDB491A`** |
| **E 境外申購流水線** | OTAB | 下單確認 → 試算 → 集保回報 → 結算調整 → 結帳 | **`OFDB051` `OFDB052` `OFDB053` `OFDB054` `OFDB055` `OFDB057` `OFDB058` `OFDB060` `OFDB061` `OFDB062` `OFDB064` `OFDB065`** |
| **F 境外贖回流水線** | OTAB | 下單確認 → 價金試算 → 集保回報 → 付款確認 → 結帳 | **`OFDB081` `OFDB082` `OFDB083` `OFDB084` `OFDB085` `OFDB086` `OFDB087` `OFDB088` `OFDB089` `OFDB090` `OFDB091` `OFDB092` `OFDB094`** |
| **G 境外受益分配** | OTAB | 產生配息 → 配現確認 → 分配確認 → 分配結帳,加明細維護與官網 API 上傳 | **`OFDB131` `OFDB132` `OFDB133` `OFDB134` `OFDB135`**、`OFDM252`、`OTAB901` |

### 0.2 最反直覺的七件事

**一、本片 58 支裡有 7 支按下「執行」必定 `NullReferenceException` —— 而且它們全部在 csproj、全部在選單設定裡。**

`OFDB236` / `OFDB237` / `OFDB239` / `OFDB240` / `OFDB241` / `OFDB242` / `OFDB307` 的 PO 繼承舊世代的 `BasicEVAPO`。 `BasicEVAPO` 把連線物件宣告成 null(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`), 而建構子裡唯一會賦值的兩組行**整段被註解掉**(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-173`)。這 7 支 PO 的原始碼裡**沒有任何一行**給 `dbTA` 或 `dbPTPF` 賦值(逐支比對:用到 `dbTA` 13~84 次,賦值 0 次), 所以第一次碰資料庫就爆:

| 畫面 | 第一次用 `dbTA` 的行 | 用到 `dbTA` 次數 |
|---|---|---|
| `OFDB236` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:38` | 23 |
| `OFDB237` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB237_PO.cs:43` | 74 |
| `OFDB239` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:40` | 13 |
| `OFDB240` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB240_PO.cs:40` | 44 |
| `OFDB241` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB241_PO.cs:40` | 13 |
| `OFDB242` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB242_PO.cs:30` | 52 |
| `OFDB307` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB307_PO.cs:34` | 84 |

`ofdb.md §0.2` 已經對 `OFDB001` / `OFDB005` / `OFDB011` / `OFDB161` 做過同樣的判定。本片再補 7 支 —— **`ATLAS.OFDB` 這個專案裡共有 11 支畫面是這個狀態**,而且不是相鄰代號,是散的。它們同時還帶著 T-SQL 語法(下一條),所以就算把連線補回去也跑不動。

**二、`OFDB236` / `OFDB330` 的 SQL 是 T-SQL,而 `OFDB330` 的 PO 明確宣告跑 Oracle。**

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:410-416` 是活的(不是註解),整段用 `@FUND_ID` 具名參數、`Convert(nvarchar, …, 111)`、`System.Data.SqlDbType`。 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:571` 更直白 —— 這支的類別上有 `[PODbType(DbServerType.Oracle)]`、欄位是 `new Database("TA", DbServerType.Oracle)`,但這一行仍然是 `WHERE REDEM_NO=@REDEM_NO AND convert(varchar,REDEM_ACT_PAY_DATE,111) > convert(varchar,@REDEM_ACT_PAY_DATE,111)`。 **Oracle 會直接拒絕**(`@` 不是 bind 前綴、`convert(…,111)` 不存在)。這一條的下場落到外層 catch,使用者看到的只有「執行失敗」。逐支統計見 §6.8。

**三、`OFDB305_PO.cs` 與 `OFDB323_PO.cs` 各有一份過期副本躺在 UI 資料夾,而且不在任何 csproj。**

| 現行(有編譯) | 殘留副本(沒編譯) | 相似度 | 行數 |
|---|---|---|---|
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:166`) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB305_PO.cs` | 97.4% | 443 vs 442 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB323_PO.cs`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:173`) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB323_PO.cs` | 97.7% | 396 vs 394 |

`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj` 裡沒有這兩個檔名。 **後果是全文搜尋會出現兩份幾乎一樣的結果,行號差 1~2 行**,改錯邊不會有任何編譯錯誤 —— 改完測不出來,上線才發現沒生效。本文所有 `OFDB305` / `OFDB323` 的錨點一律指 `PO/PO.OFDB/` 那份。

**四、`A` 後綴這一次既不是境內外,也不是遷移改名 —— 六支都沒有不帶 `A` 的版本。**

`OFDB481A` / `OFDB486A` / `OFDB487A` / `OFDB489A` / `OFDB490A` / `OFDB491A` 六支在整個 `Dev/` 底下 **找不到任何不帶 `A` 的同號檔案**。六支的 SQL 裡**一個 `FUND_TYPE` 或 `SHORE_ID` 條件都沒有**, 所以 `ofd5.md` / `ofd7.md` 的境內外規則在這裡不成立(`ofdb3.md §6.2` 對批次上的 `A` 已經做過同樣的否定)。同一個 48x 區段裡,`ATLAS.OFD` 的 `OFDM485` **沒有 `A`**,主檔卻是 `OFD484A`(一樣帶 A 的表), 所以「代號的 A 跟著表名走」也講不通。詳細比對與結論見 §6.4。

**五、全片沒有任何排程。零個 `Main()`、零個 `.bat`、零個 WindowsService、零個 `Process.Start`。**

`Dev/ATLAS.OFDB/` 與 `Dev/ATLAS.OTAB/` 底下 18 個 csproj **全部是 `Library`** (例:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:9`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/PO.OTAB.csproj:8`)。整個 repo 只有 4 個 WindowsService 專案(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj`、 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/WindowsService.OFDB609.csproj`、 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/WindowsService.OFDB680.csproj`、 `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/WindowsService.RSPB008.csproj`), **沒有一個對應本片的 58 支**。 `ofdb3.md §6.1.2` 查到的「排程時刻存在 DB 欄位」那條路,在本片**完全不適用**。 58 支的唯一觸發方式是:使用者從主程式選單開畫面,按「執行」鈕。詳細查證見 §3.4。

**六、Remoting 設定:兩個專案 13 個 `App.config`,`system.runtime.remoting` 區段 0 個。**

`ofdb3.md §3.4` 在 EC / OTAB / OFDB 三專案的 20 個 config 裡找到 2 個有 Remoting 區段(都在 WindowsService 專案)。本片重掃兩個專案自己的 13 個 config,**一個都沒有**(見 §3.4 逐檔表)。所有 `_Pxy` 因此都是本機物件,Control + PO 跟 UI 跑在同一個行程。 **但 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:9-11` 有明文 `connectionStrings`,指向一台 SQL Server 與一個 Logging 資料庫**(只記位置,不抄值)。那是 MSSQL 時代的殘留:`providerName` 寫 `System.Data.SqlClient`,而現行 PO 全走 Oracle。

**七、`OFDM252` 代號是 M,但它是徹頭徹尾的 B —— 而且因此繞過四眼直接改資料。**

`OFDM252` 住在 `Dev/ATLAS.OTAB/`(批次專案),UI 繼承 `xOneStepProcessForm` (`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDM252.cs:43` 一帶的 `this.TabPages = 1`), `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:293` 的 `formstyle` 是 `OneStep`,**跟其餘 57 支一模一樣**。它沒有 `Status` 欄流轉、沒有 `Verify` / `Approve` 事件,PO 直接對 `OFD283` 下 `INSERT` / `UPDATE` / `DELETE` (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:397-477`)。 **它是一支穿著 M 外衣的批次維護畫面**,完整分析在 §4.1。

### 0.3 三個 PO 世代 —— 決定一支能不能跑

| 世代 | 基底類別 | 連線來源 | 支數 | 能跑嗎 |
|---|---|---|---|---|
| **舊世代** | `BasicEVAPO` | **`dbTA` 恆為 null** | **7** | **不能** |
| **裸介面世代** | 只實作 `IOFDBnnn_PO`,不繼承任何基底 | 自己 `new Database("TA", DbServerType.Oracle)` | **13** | 能 |
| **新世代** | `BaseEVADaoPO` + `IOFDBnnn_PO` | 基底的 `dbProduct`,部分再自建 `dbTA` | **38** | 能 |

逐支歸屬:

| 世代 | 代號 |
|---|---|
| 舊世代 `BasicEVAPO` | `OFDB236` `OFDB237` `OFDB239` `OFDB240` `OFDB241` `OFDB242` `OFDB307` |
| 裸介面 | `OFDB221` `OFDB290` `OFDB311` `OFDB330` `OFDB351` `OFDB432` `OFDB434` `OFDB481A` `OFDB486A` `OFDB487A` `OFDB489A` `OFDB490A` `OFDB491A` |
| 新世代 `BaseEVADaoPO` | `OFDB285` `OFDB289` `OFDB303` `OFDB305` `OFDB323` `OFDB328` + `ATLAS.OTAB` 全部 32 支 |

三個世代共同的一件事:**58 支沒有一支用 `base.Update` 走四眼**。 `xTableMapping` 在本片只有一支宣告(§2.1),其餘 57 支的主檔在索引裡一律是空的 —— 這是批次的通例,不是缺陷。

### 0.4 不管什麼

- **不管交易單本身怎麼進來**。申購 / 贖回 / 轉換的原始單據由 M 畫面與 EC 前台產生,本片只做「確認 / 試算 / 結算 / 結帳 / 產檔」。

- **不管四眼**。58 支全部沒有 `Status` 流轉,`BMS001A` / `OFD081A` 這些主檔在本片一律唯讀。

- **不管排程**。沒有任何一支能自己跑(§0.2 第五件事)。

- **不管報表格式**。`.rpt` 不在版控,本片只給 RPS 設定鍵名(§7)。

- **不管 SP 內部**。本片呼叫 23 支 SP,其中 **16 支的腳本不在 repo**(附錄 B)。

### 0.5 使用角色(推測)

| 角色 | 會碰哪些 | 依據 |
|---|---|---|
| 境內基金作業人員 | A / B / C / D 群共 26 支 | 畫面條件都是「基金代碼 + 申購日期 / 買回日期」,`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB303.Designer.cs:156`、`:185` |
| 境外基金作業人員 | E / F 群共 25 支 | 畫面條件都是「境外基金公司代碼 + 基金代碼 + 申購日 / 贖回日」,`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB051.designer.cs` 一帶 |
| 清算作業人員 | D 群六支 | 條件是「清算基準日 / 期別 / 發放日期」,`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB486A.Designer.cs:324`、`:352` |
| 資訊人員 | `OTAB901` | 失敗訊息直接寫「請連絡資訊人員」,`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:132`、`:198`、`:203` |

### 0.6 全域開關

本片沒有「一個開關關掉全部」這種東西。實際會左右行為的是四類:

| 開關 | 在哪 | 影響 |
|---|---|---|
| `App.config` 的 `section` 登記 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:5` 起、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:3` 起 | 沒登記就開不了畫面;58 支全部有登記(§3.4) |
| `formstyle="OneStep"` | 同上,每支各一段 | 決定畫面長成「查詢 + 執行鈕」;58 支全部是 `OneStep` |
| `OFD303` / `OFD303A` 的結帳控制碼 | 由 `OFDB061` / `OFDB091` / `OFDB305` / `OFDB323` 讀寫 | 一日作業的閘門(§2.5) |
| `OFD081` 的 `API_URL` / `API_NAME` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:123-124` | 官網 API 端點;沒設定時**不是報錯,是拋 `UriFormatException`**(§6.6) |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDB5 片全景:58 支分屬兩個專案七群業務、三個 PO 世代、唯一手動觸發、Remoting 零個
圖中文字:① 兩個專案，同一種代號 —— 代號命名的是模組加型別，不是專案 / ATLAS.OFDB 26 支 / 境內基金批次 動 OFD220A 221A 303A / ATLAS.OTAB 32 支 / 境外基金批次 動 OFD220 221 303 / ATLAS.OFD / ATLAS.OTA / 各自的 M I R 畫面 本片以外 / 代號重疊 0 支 / 562 563 564 不在本片 / ② 七群業務，彼此不相干 / A 境內扣款比對 / 221 236 237 239 240 241 242 303 307 / B 境內日結轉 / 305 323 330 311 / C 境內產檔報表 / 285 289 290 328 351 432 434 / D 境內基金清算 / 481A 486A 487A 489A 490A 491A / E 境外申購流水線 / 051 052 053 054 055 057 058 060 061 062 064 065 / F 境外贖回流水線 / 081 到 094 共 13 支 / G 境外受益分配 / 131 到 135 加 OFDM252 OTAB901 / ③ 三個 PO 世代 —— 決定一支能不能跑 / 舊世代 BasicEVAPO 7 支 / dbTA 恆為 null 按執行必爆 / 裸介面 13 支 / 自建 Database 走 Oracle / 新世代 BaseEVADaoPO 38 支 / OTAB 全部加 OFDB 六支 / 四眼 0 支 / xTableMapping 只有 OFDB303 / ④ 觸發方式:只有一種。18 個 csproj 全是 Library，沒有 Main 沒有 bat 沒有服務 / 主程式選單 / App.config 登記 58 支 / xOneStepProcessForm / formstyle 全部 OneStep / 使用者按執行鈕 / 唯一入口 / 排程 未在 repo 內找到 / WindowsService 四個都不是本片 / ⑤ Remoting 0 個區段;SP 23 支，只有 OTAB 那 7 支在版控 / 13 個 App.config / system.runtime.remoting 0 個 / PO.OFDB App.config / 明文連線字串 只記位置 / S_OTA_ 七支 / DB/SP 內有腳本 / S_TA_ 十六支 / 腳本不在 repo
```

*圖:圖 1 全景。橘框=本片主要入口或重點;橘虛框=要留意的行為(跑不起來、明文連線、查不到排程);灰虛框=本片以外或唯讀;黑框=無原始碼。第③列第一格那七支按下執行鈕必定 NullReferenceException。*

### 1.2 批次讀寫的表

(圖由 `ofdb5.figs.py` 注入,target `h2:2-`。)

### 1.3 依專案 / 觸發方式 / 有無 Remoting 分群

(圖由 `ofdb5.figs.py` 注入,target `h2:3-`。)

### 1.4 主要維護畫面的四眼與卡控順序

本片只有 `OFDM252` 一支長得像維護畫面,而它**不走四眼**(§4.1),所以這裡沒有四眼流程圖可畫。卡控順序改用「連號系列的執行順序」表達,見 §1.5 與 §6.2。

### 1.5 連號系列的執行順序與失敗處理

(圖由 `ofdb5.figs.py` 注入,target `h2:6-`。)

## 2. 資料模型

```text
[圖] OFDB5 片動到的表分六群:境內帶 A、境外不帶 A、兩邊共用三張、受益分配三張、清算四張、以及一批根本不是表的識別字
圖中文字:① 境內(OFDB 專案):表名帶 A / OFD220A OFD221A / 申購主檔 明細 各 8 支用 / OFD303A / 結帳控制 11 支用 最熱 / OFD251A 252A 253A 254A / 買回 / OFD233A / OFDB303 的主檔 本片唯一宣告 / ② 境外(OTAB 專案):同概念的表不帶 A / OFD220 OFD221 OFD224 / 申購 18 支用 / OFD303 / 結帳控制 15 支用 / OFD251 252 253 254 256 / 贖回 / OFD302 / 境外淨值 19 支用 / ③ 兩邊共用、不分境內外的三張 —— 改欄位要同時看 58 支 / BMS001A / 受益人 OTAB 22 支 JOIN / FSK003 / OTAB 26 支 JOIN 相依最深 / CTL014 CTL000 CTL012 / 代碼與控制 / OFD081A OFD081V OFD081 / 基金主檔 境內外各一 / ④ 受益分配三張表:OFDM252 直接改，沒有四眼 / OFD281 / 受益分配主檔 PROCESS_CODE / OFD282 / 試算檔 CFM_YN / OFD283 / 明細 OFDM252 直接增刪改 / OFD283_TSCDLOG / 集保軌跡 / ⑤ 清算價金給付四張:OFD497A 的四眼欄是假的 / OFD494A OFD495A / 清算主檔 481A 486A 寫 / OFD496A / 給付明細 GET_STATUS 2 4 5 / OFD497A / Status 寫死 302 三組四眼同一人 / OFDM481A OFDM482A / ATLAS.OFD 的維護畫面 / ⑥ 不是表的識別字 —— 別拿去查索引 / MY 開頭八個 / WITH AS 的 CTE 名稱 / dbo / MSSQL schema 在註解裡 / OFD081V OFD020V RSP003V / View 定義不在版控 / AA_REPORTMASTERSCHEMA / repo 內無定義
```

*圖:圖 2 批次讀寫的表。橘框=本片會寫的核心表;橘虛框=要留意(相依最深、四眼造假、名稱其實是 CTE);灰虛框=別的模組維護;黑框=定義不在版控。第①②列並排看，就是境內外分家的全部證據。*

### 2.1 主表與明細:58 支只有一支宣告,而這是對的

`atlas_scan.py --screen <代號>` 對本片 58 支印出來的結果:

| 結果 | 支數 | 代號 |
|---|---|---|
| 有主檔 | **1** | `OFDB303`(主檔 `OFD233A`) |
| 主檔 / 明細皆空 | **57** | 其餘全部 |

唯一那一支寫在建構子裡,而且是一行式:

`this.MasterTable = new xTableMapping("OFD233A", "OFDB303");` —— `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:30`

**為什麼其餘 57 支都空 —— 這是通例不是異常。** `xTableMapping` 是給 `BaseEVADaoPO` 的四眼存檔流程用的,而批次不走四眼、不走 `base.Update`。 `ofdb3.md §2.1` 對另外 35 支得到同一結論。本片 58 支的 PO 一律自己組 SQL(`GetSqlStringCommand`)或呼叫 SP(`GetStoredProcCommand`),自己開自己的交易。 `OFDB303` 之所以宣告,是因為它另外掛了 `BeforeSelect` 事件借用基底的查詢管線 (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:31`、`:39-151`)—— **它用的是「查」那一半,不是「存」那一半**。

**副作用要記住:`atlas_scan --table <表名>` 反查「誰在用這張表」時,本片 58 支有 57 支不會出現。** 要找誰動 `OFD221` / `OFD252` / `OFD303`,只能對 `Dev/ATLAS.OFDB/Source/PO/` 與 `Dev/ATLAS.OTAB/Source/PO/` 做全文搜尋。

### 2.2 `A` 後綴在表名上是境內外分家 —— 兩個專案各走一套

這是本片最重要的一張對照。**同一個業務概念,境內用帶 `A` 的表,境外用不帶 `A` 的表:**

| 業務 | 境內(`ATLAS.OFDB` 用) | 境外(`ATLAS.OTAB` 用) |
|---|---|---|
| 基金主檔 | `OFD081A`(檢視 `OFD081V`) | `OFD081` |
| 申購主檔 / 明細 | `OFD220A` / `OFD221A` | `OFD220` / `OFD221` |
| 申購彙總 | `OFD232A` / `OFD233A` | `OFD224` |
| 買回(贖回)主檔 / 明細 | `OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` | `OFD251` / `OFD252` / `OFD253` / `OFD254` / `OFD256` |
| 淨值 | `OFD302A` | `OFD302` |
| 結帳控制 | `OFD303A` | `OFD303` |
| 受益分配 | `OFD281A` / `OFD283A` | `OFD281` / `OFD282` / `OFD283` |

計數(把 CTE 名稱排除後):`ATLAS.OFDB` 的 26 支碰 **66 個**識別字,`ATLAS.OTAB` 的 32 支碰 **49 個**。最熱的幾張:

| 專案 | 表 | 被幾支用 |
|---|---|---|
| OFDB | `OFD303A` | 11 |
| OFDB | `OFD081V` | 10 |
| OFDB | `OFD220A` / `OFD221A` | 各 8 |
| OTAB | `OFD081` | 28 |
| OTAB | `FSK003` | 26 |
| OTAB | `BMS001A` | 22 |
| OTAB | `OFD302` | 19 |
| OTAB | `OFD221` | 18 |
| OTAB | `OFD303` | 15 |

**兩個例外要記住**(改欄位時會咬人):

1. **`BMS001A` 兩邊都用,而且都帶 `A`。** 受益人主檔沒有境內外之分 —— `ATLAS.OTAB` 的 32 支裡有 22 支 JOIN 它。

2. **`OFD606A` / `OFD611` / `OFD620` / `OFD621` 出現在 `OTAB` 的 `OFDB055`**(電子交易截止時間與拋轉碼), 那是 EC 模組的表(`ofdb3.md §6.1`),被境外流水線借去做「未到 EC 交易截止時間不可下單確認」的檢核。

### 2.3 「表」的三種形狀

跟 `ofdb3.md §2.3` 一樣,本片 SQL 字串裡的大寫識別字不是每一個都是實體表:

| 形狀 | 例 | 怎麼辨認 |
|---|---|---|
| 真的實體表 | `OFD221` `OFD303A` `OFD496A` | 有 `INSERT INTO` / `UPDATE` / `DELETE` 打它 |
| 檢視(View) | `OFD081V` `OFD020V` `RSP003V` | 只出現在 `FROM` / `JOIN`,repo 內無 DDL |
| **CTE(`WITH … AS`),不是表** | `MYROW_DATA` `MYCAL_DATA` `MYOFD253` `MYOFD300` `MYOMNIBUS_LIST` `MYOFD221_P` `MYOFD283` | 前綴 `MY`,定義就在同一段 SQL 裡 |

CTE 那一類的證據: `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB131_PO.cs:312`(`WITH MYROW_DATA AS`)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB088_PO.cs:445`(`WITH MYOFD253 AS`)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:246`(`MYOMNIBUS_LIST AS`)。 **別拿 `MY*` 去 `atlas_scan --table` 查,查不到不是漏建索引。**

另外兩個假表名:

| 識別字 | 真相 | 錨點 |
|---|---|---|
| `dbo` | MSSQL 的 schema 前綴殘留,那段 SQL 已被 `/* */` 註解 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:251` |
| `OFDB065T1` | `OFDB065` 自己的暫存表命名,只在 SQL 字串裡 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB065_PO.cs` |

### 2.4 主鍵與四眼欄位

本片沒有一支走四眼,但**有兩支直接把四眼欄位當一般欄位填**,這是本片最危險的資料模型行為:

| 畫面 | 寫哪些四眼欄 | 填什麼 | 錨點 |
|---|---|---|---|
| `OFDB489A` | `Status` `CreateID/Date` `EntryID/Date` `UpdateID/Date` `VerifyID/Date` `ApproveID/Date` `RejectID/Date` | `Status` 寫死 `'302'`;`Verify` / `Approve` / `Reject` 三組全部填**同一個** `:UserID` + `sysdate` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:100-119` |
| `OFDB490A` | 同上 | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:104-123` 一帶 |

意思是 `OFD497A`(清算退匯 / 退郵記錄)看起來有完整四眼軌跡,實際上**三個人都是同一個人、三個時間都是同一秒**。稽核報表若拿這張表的 `VerifyID` / `ApproveID` 當覆核證據,拿到的是假資料。

`OFDM252` 則是另一種:`OFD283` 有 `CRT_` / `ADJ_` / `CLR_` / `POST_` 四組人員時間欄, `OFDM252` 直接用 SQL 全部寫進去(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:523-537`),沒有任何覆核階段。

主鍵方面,本片的 SQL 有把主鍵寫在註解裡,可以直接抄:

| 表 | 主鍵(取自程式註解) | 錨點 |
|---|---|---|
| `OFD282` / `OFD283` | `FUND_ID, RECORD_DATE, BF_NO, BAL_TYPE, DIVIDEND_ID, CRNCY_CD, BSHARE_ACC_NO, BSHARE_TRADE_NO` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:354`、`:423` |
| `OFD496A` | `FUND_ID, ISSUE_CODE, BF_NO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:75-77` |
| `OFD497A` | `DATA_SEQ`(流水號) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:155-156` |
| `OFD233A` | `FUND_ID, ALLOT_DATE, BANK_HQ, SEAL_TYPE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:99-106`(GROUP BY 反推) |

### 2.5 狀態碼(從程式反推,標來源)

**(一)境外受益分配的作業處理碼 —— 這是本片唯一有完整標示的狀態機。** 畫面上直接印在標籤裡:

| 值 | 意義 | 由誰推到下一階 | 標籤來源 |
|---|---|---|---|
| `0` | 資料維護 | `OFDB131` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB131.designer.cs` 的「作業處理碼流程: 0:資料維護->1:產生配息資料」 |
| `1` | 產生配息資料 | `OFDB133` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB133.designer.cs` 的「1:產生配息資料->1A:配現資料確認->2:受益分配資料確認」 |
| `1A` | 配現資料確認 | `OFDB133` | 同上 |
| `2` | 受益分配資料確認 | `OFDB134` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB134.designer.cs` 的「2:受益分配資料確認->3:受益分配資料分配確認」 |
| `3` | 受益分配資料分配確認 | `OFDB135` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB135.designer.cs` 的「3:受益分配資料分配確認->4:受益分配結帳」 |
| `4` | 受益分配結帳 | (終點) | 同上 |

欄位名是 `OFD281.PROCESS_CODE`(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:594`)。

**(二)境內清算價金給付的 `GET_STATUS`(`OFD496A`)** —— 從 UPDATE 語句反推:

| 值 | 意義(推測) | 由誰寫 | 錨點 |
|---|---|---|---|
| `'2'` | 正常待付 / 取消退匯後復原 | `OFDB489A` 取消退匯 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:180` |
| `'4'` | 已退匯 | `OFDB489A` 退匯 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:72` |
| `'5'` | 已退郵 | `OFDB490A` 退郵 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:113`(`INSERT OFD497A` 的 `GET_STATUS` 常數) |

`OFDB491A`(重匯 / 重寄)寫同一欄的其他值,值域**不在 repo 內**(沒有 `CTL014` 對照,也沒有 DDL)。本文不猜,標「未查到」。

**(三)境內結帳控制碼(`OFD303A` / `OFD303`)** —— 本片只讀不寫,值由 `OFDB305` / `OFDB323` / `OFDB061` / `OFDB091` 判斷:

| 欄位 | 判斷式 | 意義(推測) | 錨點 |
|---|---|---|---|
| `OFD303A.ALLOT_CTL_CODE` | `= '3'` → 已結轉,不可取消確認 | 申購結轉狀態 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:61-62` |
| `OFD303A.POST_CTL_CODE` | `= 'Y'` → 已過帳,不可取消確認 | 過帳旗標 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:59-60` |
| `OFD303.REDEM_CTL_CODE` | `>= '2'` → 已作下單確認 | 境外贖回控制 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:308` |

**(四)`OFD233A.BANK_CFM_CD`(扣款行確認)**:`'Y'` / `'N'` 兩值,`OFDB303` 的執行功能就是在這兩值間切換 (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:86`、`:181`)。

**(五)`OFD221A.SUB_STATUS`(扣款結果)**:

| 值 | 意義(取自程式內的中文訊息) | 錨點 |
|---|---|---|
| `'0'` / `'1'` | 尚有扣款資料未回報扣款結果,不可確認 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:68-73` |
| `'2'` | 成功(計入 `SUS_CNT` / `SUS_AMT`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:75`、`:77` |
| `'3'` | 失敗(計入 `FAL_CNT` / `FAL_AMT`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:76`、`:78` |

### 2.6 與其他模組共用的表

本片會碰到 11 張由別的模組維護的表(`BMS001A` `BMS001` `OFD081A` `OFD081V` `OFD081` `CTL014` `FSK003` `COD006` `COD009` `SDM010A` `LOG017A`), 逐表的維護者、用途與改動影響列在 §8.3,這裡不重複。最需要記住的一條:**`FSK003` 被 `ATLAS.OTAB` 的 32 支裡的 26 支 JOIN,是本片對外相依最深的一張。**

## 3. 畫面清冊

```text
[圖] 58 支的觸發方式只有一種、排程四條查證全零、Remoting 區段零個，真正的分群是 PO 世代
圖中文字:① 觸發方式:58 支同一條路，沒有第二種 / 主程式選單 / UI.OFDB / UI.OTA 的 App.config / section 登記 58 支 / formstyle 全部 OneStep / xOneStepProcessForm / 查詢 勾選 按執行 / Control 加 PO 同行程 / 沒有 Remoting 就是本機物件 / ② 排程:四條都查過，四條都是零 / bat 或 cmd 0 個 / 兩專案全樹 / static void Main 0 個 / 18 個 csproj 全是 Library / Process.Start 1 個 / 而且被註解 而且不在本片 / WindowsService 0 個 / repo 內四個都屬 EC 與 RSP / ③ Remoting:13 個 App.config 掃過，區段 0 個 / UI.OFDB 786 行 / 只有畫面 section / UI.OTA 308 行 / 只有畫面 section / PO.OFDB 63 行 / 明文連線字串 SqlClient 殘留 / 其餘十個 / 空殼或樣板複製 / ④ 依 PO 世代分群 —— 這才是「能不能跑」的分界 / 七支 BasicEVAPO / 236 237 239 240 241 242 307 / dbTA 宣告成 null / 建構子賦值全被註解 / 第一次碰 DB 就 NRE / Pxy 包成 ServerSideError / 同時還帶 T-SQL / 就算補連線也跑不動 / ⑤ 能跑卻仍帶 T-SQL 的兩支 —— 比上面七支危險 / OFDB330 第 571 行 / convert 111 加 @ 參數 Oracle 必拒 / 三個 AddInParameter 被註解 / 整個檢核方法是死的 / OFDB305 第 229 行 / REMIT_FAIL_CODE 等於空字串 / 卡控只擋一半 / 匯款件完全不擋 / ⑥ 在不在 csproj:五層逐檔比對，缺 0;但多出兩個沒人編譯的檔 / 58 支五層全在 / UI Designer Pxy Ctl PO / UI 資料夾的 OFDB305_PO.cs / 97.4% 相似 不在 csproj / UI 資料夾的 OFDB323_PO.cs / 97.7% 相似 不在 csproj / 九個 cp950 檔 / 289 305 323 三支
```

*圖:圖 3 觸發方式與分群。橘框=唯一入口;橘虛框=要留意(查不到、殘留、跑不起來);灰虛框=空殼設定。第②③兩列是「本片沒有排程也沒有 Remoting」的完整查證,第④⑤列才是真正決定一支能不能用的分界。*

### 3.1 維護 M

本片有一支代號是 M 的 —— `OFDM252`。 **但它不是維護畫面**:UI 繼承 `xOneStepProcessForm`、`formstyle="OneStep"`、沒有四眼。判定過程與完整分析放 §4.1。除它以外,本片無 M。

### 3.2 查詢 I

**本片無 I。** 原因:58 支的代號第四碼都是 `B`(唯一例外 `OFDM252` 是 M、`OTAB901` 是 `OTAB` 前綴), 而 `architecture.md §6.4` 講的「B 跟 I 是同一份程式碼」在本片 100% 成立 —— 每一支都是「先查出一張清單 → 勾選 → 按執行」,查詢那一半就長在 B 裡面。真正只查不改的有三支(`OFDB062` / `OFDB092` / `OFDB087`,見 §6.5),但它們掛的仍是 `B` 代號。

### 3.3 批次 B(58 支)

七欄:專案 / 觸發方式 / Remoting / 交易邊界 / 重跑安全 / 失敗處理 / 出口。 **「觸發方式」全欄同值**:手動 —— 主程式選單開畫面、按「執行」鈕(查證見 §3.4)。 **「Remoting」全欄同值**:無(兩專案 13 個 `App.config` 全部沒有 `system.runtime.remoting` 區段)。 **「在 csproj」全欄同值**:在 —— 58 支的 UI / Designer / Pxy / Ctl / PO 五層逐檔比對,**缺 0**。因此下表把這三欄合併成一句話,騰出空間放差異欄。

`交易邊界` 欄的 `B/C/R` = `BeginTransaction` / `Commit` / `Rollback` 出現次數(PO 層)。 `R` 比 `C` 多是常態 —— 多出來的是每個 catch 各寫一次。

| 代號 | 專案 | PO 行數 | PO 世代 | 交易邊界 | 出口 | SP |
|---|---|---|---|---|---|---|
| `OFDB221` | OFDB | 171 | 裸介面 | B1/C1/R3 | 檔案匯入 | — |
| `OFDB236` | OFDB | 544 | **BasicEVAPO(跑不起來)** | B2/C2/R3 | INSERT / DELETE / 檔案 | — |
| `OFDB237` | OFDB | 1,216 | **BasicEVAPO(跑不起來)** | B3/C3/R5 | INSERT / UPDATE / SP | `s_OFDB237_Get` |
| `OFDB239` | OFDB | 204 | **BasicEVAPO(跑不起來)** | B1/C1/R2 | UPDATE | — |
| `OFDB240` | OFDB | 398 | **BasicEVAPO(跑不起來)** | B2/C2/R4 | UPDATE / 報表 | — |
| `OFDB241` | OFDB | 201 | **BasicEVAPO(跑不起來)** | B1/C1/R2 | UPDATE | — |
| `OFDB242` | OFDB | 637 | **BasicEVAPO(跑不起來)** | B1/C1/R3 | UPDATE / 報表 | — |
| `OFDB285` | OFDB | 421 | BaseEVADaoPO | **B0/C0/R0(無交易)** | 產檔 / 報表 | — |
| `OFDB289` | OFDB | 256 | BaseEVADaoPO | **B0/C0/R0(無交易)** | 產檔 / SP | `s_TA_OFDB289_Excute` |
| `OFDB290` | OFDB | 97 | 裸介面 | B1/C1/R1 | 產檔 / SP | `s_TA_OFDB290_Excute` |
| **`OFDB303`** | OFDB | 222 | BaseEVADaoPO | B1/C1/R2 | SP(逐列呼叫) | `s_TA_OFDB303_Excute` |
| `OFDB305` | OFDB | 443 | BaseEVADaoPO | B1/C1/R4 | SP / 報表 | `S_TA_OFDB305_CheckAgent` |
| `OFDB307` | OFDB | 441 | **BasicEVAPO(跑不起來)** | B1/C1/R3 | UPDATE | — |
| `OFDB311` | OFDB | 299 | 裸介面 | B1/C1/R3 | INSERT / SP | `s_TA_OFDB311_Execute` |
| `OFDB323` | OFDB | 396 | BaseEVADaoPO | B1/C1/R4 | SP / 報表 | `S_TA_OFDB323_CheckAgent` |
| `OFDB328` | OFDB | 1,455 | BaseEVADaoPO | **B0/C0/R0(無交易)** | 產檔 / 報表 / SP | `S_TA_OFDB328_EXCUTE_RPS`、`S_TA_OFDB285_EXCUTE_RPS` |
| `OFDB330` | OFDB | 652 | 裸介面 | B1/C1/R2 | UPDATE / SP / 報表 | `s_TA_OFDB330_Get` |
| `OFDB351` | OFDB | 227 | 裸介面 | **B2/C1/R4(開兩次只關一次)** | SP | `S_TA_OFDB351_EXECUTE` |
| `OFDB432` | OFDB | 284 | 裸介面 | B1/C1/R2 | SP | `s_TA_OFDB432_Exe` |
| `OFDB434` | OFDB | 278 | 裸介面 | B1/C1/R2 | SP | `s_TA_OFDB434_Exe` |
| **`OFDB481A`** | OFDB | 251 | 裸介面 | B1/C1/R2 | SP | `S_TA_OFDB481A_EXCUTE` |
| **`OFDB486A`** | OFDB | 346 | 裸介面 | B1/C1/R2 | SP | `S_TA_OFDB486A_EXCUTE` |
| **`OFDB487A`** | OFDB | 281 | 裸介面 | B1/C1/R2 | SP | `S_TA_OFDB487A_EXCUTE` |
| **`OFDB489A`** | OFDB | 426 | 裸介面 | B1/C1/R3 | INSERT / UPDATE / DELETE | — |
| **`OFDB490A`** | OFDB | 416 | 裸介面 | B1/C1/R3 | INSERT / UPDATE / DELETE | — |
| **`OFDB491A`** | OFDB | 761 | 裸介面 | B1/C1/R4 | UPDATE / 報表 | — |
| `OFDB051` | OTAB | 752 | BaseEVADaoPO | B1/C1/R3 | UPDATE | — |
| `OFDB052` | OTAB | 674 | BaseEVADaoPO | B1/C1/R4 | UPDATE | — |
| `OFDB053` | OTAB | 311 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB054` | OTAB | 1,179 | BaseEVADaoPO | B1/C1/R10 | INSERT / UPDATE | — |
| `OFDB055` | OTAB | 807 | BaseEVADaoPO | B1/C1/R6 | INSERT / UPDATE | — |
| `OFDB057` | OTAB | 1,269 | BaseEVADaoPO | B1/C1/R9 | UPDATE | — |
| `OFDB058` | OTAB | 549 | BaseEVADaoPO | B1/C1/R3 | UPDATE | — |
| `OFDB060` | OTAB | 657 | BaseEVADaoPO | B1/C1/R3 | UPDATE | — |
| **`OFDB061`** | OTAB | 1,767 | BaseEVADaoPO | B1/C1/R2 | SP | `S_OTA_OFDB061_EXE` |
| `OFDB062` | OTAB | 626 | BaseEVADaoPO | B1/C1/R2 | INSERT / SP | `S_OTA_OFDB062_EXE` |
| `OFDB064` | OTAB | 304 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB065` | OTAB | 754 | BaseEVADaoPO | B1/C1/R8 | INSERT / UPDATE / DELETE / SP | `S_OTA_OFDB065_EXE` |
| `OFDB081` | OTAB | 1,163 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB082` | OTAB | 1,039 | BaseEVADaoPO | B1/C1/R7 | UPDATE | — |
| `OFDB083` | OTAB | 428 | BaseEVADaoPO | B1/C1/R3 | UPDATE | — |
| **`OFDB084`** | OTAB | 2,063 | BaseEVADaoPO | B1/C1/R15 | INSERT / UPDATE | — |
| `OFDB085` | OTAB | 1,256 | BaseEVADaoPO | B1/C1/R9 | INSERT / UPDATE | — |
| `OFDB086` | OTAB | 903 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB087` | OTAB | 308 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB088` | OTAB | 906 | BaseEVADaoPO | B1/C1/R4 | UPDATE | — |
| **`OFDB089`** | OTAB | 422 | BaseEVADaoPO | B1/C1/R1 | **六段 DELETE** | — |
| `OFDB090` | OTAB | 1,810 | BaseEVADaoPO | B1/C1/R11 | UPDATE | — |
| **`OFDB091`** | OTAB | 1,582 | BaseEVADaoPO | B1/C1/R2 | SP | `S_OTA_OFDB091_EXE` |
| `OFDB092` | OTAB | 656 | BaseEVADaoPO | B1/C1/R2 | INSERT / SP | `S_OTA_OFDB092_EXE` |
| `OFDB094` | OTAB | 423 | BaseEVADaoPO | B1/C1/R3 | UPDATE | — |
| `OFDB131` | OTAB | 692 | BaseEVADaoPO | B1/C1/R2 | SP | `S_OTA_OFDB131_EXE` |
| `OFDB132` | OTAB | 537 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| `OFDB133` | OTAB | 546 | BaseEVADaoPO | B1/C1/R3 | INSERT / UPDATE / DELETE | — |
| `OFDB134` | OTAB | 472 | BaseEVADaoPO | B1/C1/R2 | UPDATE | — |
| **`OFDB135`** | OTAB | 1,256 | BaseEVADaoPO | B1/C1/R15 | INSERT / UPDATE / SP | `S_OTA_OFDB135_EXE` |
| **`OFDM252`** | OTAB | 636 | BaseEVADaoPO | B1/C1/R2 | INSERT / UPDATE / DELETE | — |
| **`OTAB901`** | OTAB | 341 | BaseEVADaoPO | **B3/C3/R3(三個方法各一組)** | SP / **外部 HTTP API** | `S_OTA_OTAB901_Get`、`s_INSERT_CALLAPI_HISTORY` |

**重跑安全**與**失敗處理**兩欄因為需要一句話說明,拆成兩張小表:

| 重跑行為 | 支數 | 代號 | 說明 |
|---|---|---|---|
| **先檢查已處理旗標再動** | 多數 | 境外流水線 25 支、`OFDB303` `OFDB305` `OFDB323` | 每支執行前先查「是否已確認 / 已結轉」,重跑會被自己的檢核擋掉 |
| **先 DELETE 再 INSERT** | 3 | `OFDB065` `OFDB133` `OFDM252` | 重跑會清掉上一次的結果再重做,結果一致但期間有空窗 |
| **整組刪除,無旗標** | 1 | **`OFDB089`** | 六段 DELETE,重跑第二次只會回「無贖回資料可刪除」 |
| **純產檔,無狀態** | 4 | `OFDB285` `OFDB289` `OFDB290` `OFDB328` | 重跑只是重寫檔案,安全 |
| **無法判定(跑不起來)** | 7 | 七支 `BasicEVAPO` | — |

| 失敗處理 | 支數 | 說明 |
|---|---|---|
| **catch 後不 rethrow,改寫 `Result` 回 false** | **58 支全部** | PO 層 `throw` 出現次數合計 **0**。錯誤只會變成畫面上一行訊息 |
| 其中訊息是**空字串** `AddResultRow(false, 0, "")` | **19 支、88 處** | 使用者看到「失敗」但沒有原因(附錄 E) |
| 其中 catch 只寫 `HandleBusinessException` 不改 `Result`(**fail-open**) | **50 個 `bool Check_*` / `Is*` 方法** | DB 出錯 → 卡控放行(§6.3) |

### 3.4 觸發方式與 `App.config` 的全面查證

**(一)有沒有排程?沒有。** 四條都查過:

| 查什麼 | 指令 / 範圍 | 結果 |
|---|---|---|
| `.bat` / `.cmd` | `Dev/ATLAS.OFDB` + `Dev/ATLAS.OTAB` 全樹 | **0 個** |
| `static void Main(` | 同上 | **0 個** |
| `Process.Start` | 同上 | **1 個,而且被註解**:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB540.cs:154`(`OFDB540` 不在本片名單) |
| WindowsService 專案 | 整個 `Dev/` | 4 個,全部對應 `OFDB600` / `OFDB609` / `OFDB680` / `RSPB008`,**沒有一個對應本片** |
| `OutputType` | 兩專案 18 個 csproj | **全部 `Library`** |

結論寫進清冊:**58 支的觸發方式一律是「手動 — 主程式選單 → 開畫面 → 按執行」。**

**(二)`App.config` 逐檔。** 兩個專案合計 13 個:

| config | 行數 | `system.runtime.remoting` | `connectionStrings` | 內容 |
|---|---|---|---|---|
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config` | 786 | **0** | 0 | 每支畫面一個 `section` + 一段 `formstyle` |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config` | 63 | **0** | **2(明文,含帳密)** | Enterprise Library 2.0 的 `dataConfiguration` / `loggingConfiguration` |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/App.config` | 3 | 0 | 0 | 空殼 |
| `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/App.config` | 3 | 0 | 0 | 空殼 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/App.config` 等 8 個 Entity config | 各 12 | 0 | 各 2 | 樣板複製 |
| `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config` | 308 | **0** | 0 | 同 UI.OFDB 的形狀 |

**`ATLAS.OTAB` 只有 UI 一層有 `App.config`**,其餘五層一個都沒有。

**〔客戶特定〕`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:9-11` 有兩組明文連線字串(含使用者與密碼), 指向一台 SQL Server 與一個 Logging 資料庫。本文只記位置,不抄值。** 這是 MSSQL 時代的殘留 —— `providerName` 是 `System.Data.SqlClient`,而現行 PO 全部 `new Database("TA", DbServerType.Oracle)`。 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:61` 的 `dataConfiguration defaultDatabase` 還指著 `Logging`。

**(三)每支畫面在 config 裡的登記。** 58 支 **全部有** `<section name="<代號>">` 宣告 + 一段同名區塊, `formstyle` **全部是 `OneStep`**。抽樣錨點:

| 代號 | section 宣告 | 區塊本體 |
|---|---|---|
| `OFDB303` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:42` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:332` |
| `OFDB481A` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:67` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:485` |
| `OFDB051` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:3` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:47` |
| `OFDM252` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:44` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:293` |
| `OTAB901` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:45` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:299` |

**`OFDM252` 的 `formstyle` 也是 `OneStep`** —— 這是判它是批次的第一條硬證據。

### 3.5 六層齊不齊 / 在不在 csproj

58 支逐支比對 UI / Designer / FormProxy / Control / PO 五層的 csproj `Compile` 項目:

| 層 | csproj | 缺的 |
|---|---|---|
| UI + Designer | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj`(276 個 `Compile`)、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/UI.OTAB.csproj`(97) | **0** |
| FormProxy | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/FormProxy.OFDB.csproj`(107)、`Dev/ATLAS.OTAB/Source/FormProxy/FormProxy.OTA/FormProxy.OTAB.csproj`(43) | **0** |
| Control | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/Control.OFDB.csproj`(107)、`Dev/ATLAS.OTAB/Source/Control/Control.OTA/Control.OTAB.csproj`(43) | **0** |
| PO | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj`(108)、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/PO.OTAB.csproj`(43) | **0** |

**58 支五層全在 csproj,缺 0。** `ofdb3.md §0.2` 在 EC 專案找到四支整組沒編譯、`ofdb4.md` 找到 4 支 —— **本片沒有這種情形**。

反過來,本片有兩個**多出來、不在 csproj 的檔**(§0.2 第三件事): `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB305_PO.cs` 與 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB323_PO.cs`。

### 3.6 來源檔編碼

58 支 × 五層 = 292 個 `.cs`,逐檔偵測編碼:

| 編碼 | 檔數 | 代號 |
|---|---|---|
| UTF-8 with BOM | 283 | 其餘 |
| **cp950(Big5)** | **9** | `OFDB289`(Ctl / Pxy / PO 三層)、`OFDB305`(Ctl / Pxy / PO + UI 資料夾那份殘留,共 4 個)、`OFDB323`(UI + Designer 兩層) |

`OFDB305` 最亂:`PO` 那一層是 cp950,`UI` 那一層是 UTF-8; `OFDB323` 剛好相反 —— **PO 是 UTF-8、UI 與 Designer 是 cp950**。用不看 BOM 的工具批次處理這兩支會把中文訊息弄壞。

### 3.7 報表 R

本片沒有獨立的 R 代號畫面,9 支自己帶報表,RPS 設定鍵見 §7。

## 4. 維護畫面(M)

本片只有 `OFDM252` 一支代號是 M,而它實際上是批次。判定與分析放這裡,不放 §6。

### 4.1 `OFDM252` 受益分配明細維護作業(推測)—— 代號是 M,骨子裡是 B

#### 4.1.1 為什麼它在批次專案裡:四條證據

| # | 證據 | 錨點 |
|---|---|---|
| 1 | 檔案住在批次專案 `ATLAS.OTAB`,不在 `ATLAS.OTA` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs` |
| 2 | `App.config` 的 `formstyle` 是 `OneStep`,跟其餘 57 支一樣 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:293` |
| 3 | UI 是 `xOneStepProcessForm`(`this.TabPages = 1` + `ButtonExecuteEnable`),不是 `EditGridForm` | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDM252.cs:43`、`:130` |
| 4 | PO 沒有 `xTableMapping`、沒有 `BeforeAdd` / `AfterVerify` / `AfterApprove`,`Execute` 自己組 SQL | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:343-567` |

`atlas_scan --screen OFDM252` 印「型別 M」,那是**從代號第四碼推的**,不是從程式推的。**這裡要以程式為準。**

**它有 UI 層嗎?有。** 六層齊全,而且是本片少數會讓使用者逐格編輯的畫面 —— `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDM252.cs:253`、`:279` 兩段「欄位編輯設定」、`:551` 的「編輯明細檔」。 **它走四眼嗎?不走。** 見下。

#### 4.1.2 它在做什麼(推測)

畫面條件:基金代碼 / 基準日 / 配息日 / 發放日 / 最後交易日 / RD 入帳日 / 作業處理碼 (`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDM252.Designer.cs:195`、`:224`、`:253`、`:282`、`:311`、`:340`、`:733`)。

它先從 `OFD281`(基金受益分配基本資料檔)撈出一檔配息案 (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:575-600`,方法名就叫「取得基金受益分配基本資料檔(OFD281)且受益分配作業處理碼1:產生配息資料」), 然後讓使用者在格子裡增 / 刪 / 改 `OFD283`(受益人基金受益分配明細檔)的列。

#### 4.1.3 四眼在哪裡消失的

`OFD283` 有四組人員 / 日期 / 時間欄:`CRT_UID/DATE/TIME`、`ADJ_*`、`CLR_*`、`POST_*` (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:407`、`:414`)。 `OFDM252` 的 `INSERT` 把這四組**全部一次寫滿**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:523-537`), `UPDATE` 只改 `ADJ_*` 與 `UPD_*`(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:443-448`)。 **沒有 `Status` 欄、沒有覆核階段、沒有任何「等人覆核」的中間狀態。** 使用者按下執行,資料就進去了。

這是缺陷型錄裡的「**繞過四眼直接 UPDATE 主檔**」,嚴重度**高** —— `OFD283` 是配息金額的明細,改一列就是改一個受益人拿多少錢。

#### 4.1.4 執行主體:一列一組 SQL,先動 `OFD282` 再動 `OFD283`

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:343-553`,對畫面上的每一列 `OFD283` 做兩步:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | **無條件** `UPDATE OFD282 SET CFM_YN='Y', ADJ_*=…`,用八個 PK 欄定位 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:352-394` |
| 2 | 依 `row.ROW_STATE` 決定對 `OFD283` 下 `INSERT` / `UPDATE` / `DELETE` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:397-477` |

**卡控總表:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行中,每列 | 步 1 的 `UPDATE OFD282` 影響 0 列 | **把這一列的 `ROW_STATE` 改寫成 `"Deleted"`** | **過濾(無提示)** | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:388-393` |
| 執行中,每列 | 步 2 的 `ExecuteNonQuery` 影響 0 列 | rollback 整批 + 回「執行失敗,請檢查資料是否正確」 | 阻擋 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:539-547` |
| 執行中 | 任何例外 | rollback + 回「執行失敗,請檢查 (訊息)」 | 阻擋 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:554-560` |

#### 4.1.5 第一條卡控是本支最會咬人的一顆

`i = dbProduct.ExecuteNonQuery(cmd, tran);` 之後 `if (i == 0) { row.ROW_STATE = "Deleted"; }` —— `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:388-393`

註解寫的原意是「先執行異動 OFD282,若無資料則刪除 OFD283,因無源頭」 (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:353`), 但它**蓋掉的是使用者的意圖**:

| 使用者做的 | `OFD282` 找不到對應列時,實際發生 |
|---|---|
| 新增一列(`ROW_STATE = "Added"`) | 被改成 `"Deleted"` → 跑 `DELETE OFD283`(刪不到東西)→ 但接著 `if (i == 0)` 成立 → **整批 rollback,回「執行失敗,請檢查資料是否正確」** |
| 修改一列(`"Modified"`) | 被改成 `"Deleted"` → **這一列被刪掉**,而使用者以為只是改了金額 |
| 刪除一列(`"Deleted"`) | 不變 |

第二列那一格是真正的資料遺失:**改金額,結果整列不見**,而且畫面回的是「完成」還是「失敗」取決於 `DELETE` 有沒有刪到列。嚴重度 **高**。

另外步 1 是**無條件跑的**,連使用者按「刪除」的列也會先把 `OFD282.CFM_YN` 設成 `'Y'` —— **刪掉明細卻把試算檔標成已確認**。嚴重度 **中**。

#### 4.1.6 重跑安全與失敗處理

- **重跑安全**:第二次跑同一批,`INSERT` 會撞主鍵 → 例外 → rollback。實務上安全,但訊息會是 Oracle 原文。

- **失敗處理**:`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:554-560` 的 catch **不 rethrow**, 只把 `Result` 寫成 false 並呼叫 `CommonExceptionBlocker.HandleBusinessException(ex)`。上層看不到例外型別,只看得到一行中文。

- **出口**:只有 DB(`OFD282` / `OFD283`)。不寄信、不產檔、不呼叫 SP。

## 5. 查詢畫面(I)

**本片無 I 畫面。** 原因見 §3.2 —— 58 支的查詢那一半長在 B 自己身上。

不過有三支實際上**只查不改**,列出來讓人知道按執行鈕不會動到資料:

| 代號 | 實際行為 | 錨點 |
|---|---|---|
| `OFDB062` | 申購結帳前統計:個人帳戶 / 綜合帳戶 / 問題件 / 作廢交易四組筆數金額 + 六道檢核,不寫任何表 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB062_PO.cs:328-607` |
| `OFDB092` | 贖回結帳前統計,結構與 `OFDB062` 對稱 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB092_PO.cs:297-607` |
| `OFDB087` | 只判斷 `OFD256`,`UPDATE` 只有一處且在「欄位檢查與連動」之後 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB087_PO.cs:265` |

**會把資料濾掉而不提示的條件**(這是 I 章該講的事,本片改放這裡):

| 畫面 | 條件 | 後果 | 錨點 |
|---|---|---|---|
| `OFDB303` | `OFD220A.TRAN_PAY_WAY='2'`、`OFD221A.ALLOT_CODE='1'`、`OFD220A.SYSTEM_ID='0'` 三個寫死條件 | 只看「傳真委扣 + 一般申購 + 非電子交易」,其餘一律不出現,畫面不說 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:89-91` |
| `OFDB089` | `OFD252.SOURCE_CD='2'`〔客戶特定〕 | 只處理某一來源的贖回,其餘不刪也不提示 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:307`、`:365` |
| `OFDB061` | `OFD081.ALLOT_NAV_ID <> '3'` | Oracle 三值邏輯:`ALLOT_NAV_ID` 為 NULL 的基金**整批被排除**(§6.3) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:961` |

## 6. 批次(B)與 WindowsService

```text
[圖] 境外三條流水線的執行順序、結帳那一關的 fail-open 鏈、135 跨流水線的接點，以及兩個專案完全不同的失敗處理
圖中文字:① 境外申購流水線 051 到 061 —— 靠 ALLOT_PROC_CODE 串,沒有程式強制順序 / 051 下單確認 / PROC_CODE 0 變 1 / 052 淨值試算 / 順手寫 OFD302 / 054 055 集保與 EC / TSCDLOG 檢核 / 057 集保繳款回報 / OFD551 552 562 / 060 個人帳戶確認 / 申購分配收檔 / ② 結帳那一關:20 個檢核方法全部在 UI 層逐個叫，全部 fail-open / 061 結帳 / 20 個 bool 檢核 / catch 只記錄不改回傳值 / 初始 true 等於放行 / DB 出錯就全部放行 / 畫面什麼都不顯示 / S_OTA_OFDB061_EXE / 在沒把關的狀態下結帳 / ③ 境外贖回流水線 081 到 091 —— 與申購線鏡像對稱 / 081 下單確認 / REDEM_PROC_CODE / 082 價金試算 / 同樣寫 OFD302 / 084 085 086 集保與 EC / 三支 / 090 付款確認 / 091 結帳 / 18 個 bool 檢核 同樣 fail-open / ④ 境外受益分配 131 到 135:狀態機寫在畫面標籤上 / 0 資料維護 / OFDM252 編明細 / 131 推到 1 / 產生配息資料 / 133 推到 1A 再到 2 / 配現確認 分配確認 / 134 推到 3 / 分配確認 / 135 推到 4 / 受益分配結帳 / ⑤ 135 是跨流水線的接點 —— 配息結帳會產生一張新的申購單 / 135 結帳 / INSERT OFD220 加 OFD221 / 流回申購流水線 / 051 那一關重新開始 / 135 取消結帳 / DELETE OFD220 加 OFD221 / 刪的是交易主檔 / 不是自己的中間表 / ⑥ 失敗處理:兩個專案兩種寫法，差很多 / OTAB 樣板 接回傳值 / i 等於 0 就 rollback 並 return / OFDB 清算六支 / i 等於 1 直接蓋掉 12 處 / rollback 分支成死碼 / 任何情況都 Commit 都回成功 / 全片 throw 次數 0 / 例外只變成一行中文
```

*圖:圖 4 連號系列的執行順序與失敗處理。橘框=主要步驟;橘虛框=缺陷鏈或要留意的副作用;灰虛框=一般步驟。第②列是本片最大的一類系統性缺陷,第⑥列右半是最會咬人的一顆。*

**本片沒有 WindowsService。** 查證見 §3.4。以下全部是「使用者按執行鈕」的批次。

### 6.0 先看總表

| 群 | 支數 | 代表支 | 這一群的關鍵句 |
|---|---|---|---|
| A 境內扣款比對與確認 | 9 | `OFDB303` | **7 支裡的 6 支跑不起來**(`BasicEVAPO`),能跑的只有 `OFDB221` `OFDB303` `OFDB311` |
| B 境內日結轉與付款 | 4 | `OFDB305` | 12~13 道阻擋式卡控串在一段 `CASE WHEN`,其中一道 2009 年被註解掉 |
| C 境內檔案 / 報表產出 | 7 | `OFDB328` | 三支完全不開交易;格式由 `OFD264A` / `OFD265A` 的設定驅動 |
| D 境內基金清算價金給付 | 6 | `OFDB489A` | `ExecuteNonQuery` 回傳值被 `i = 1;` 蓋掉 **12 處**;四眼欄位造假 |
| E 境外申購流水線 | 12 | `OFDB061` | 一條 12 關的流水線,關卡邏輯全在 UI 層 |
| F 境外贖回流水線 | 13 | `OFDB089` | 同上對稱;`OFDB089` 是本片唯一的「整組刪除」 |
| G 境外受益分配 | 7 | `OFDB135` | 六階狀態機,`OFDM252` 是它的明細維護入口 |

### 6.1 `OFDB303` 扣款行確認作業 —— 本片唯一有宣告主檔的一支

#### 6.1.1 六層與呼叫路徑

| 層 | 檔 |
|---|---|
| UI | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB303.cs` |
| FormProxy | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB303_Pxy.cs` |
| Control | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB303_Ctl.cs` |
| PO | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs` |
| DataEntity | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB1/OFDB303Model.xsd` |
| UIEntity | `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB1/OFDB303View.xsd` |

`OFDB303_Ctl.cs:37` 的 `#region 一般資料維護` 走基底的查詢管線, `OFDB303_Ctl.cs:131` 的「強型呼叫底層」轉給 `OFDB303_PO.Execute`。

#### 6.1.2 主檔宣告與它真正的用途

建構子兩行:`this.MasterTable = new xTableMapping("OFD233A", "OFDB303");` 與 `this.BeforeSelect += OFDB303_PO_BeforeSelect;`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:30-31`)。

宣告主檔是為了**掛 `BeforeSelect`**,用基底的查詢管線把自己組的 SQL 塞進 `args.DbCmd.CommandText` (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:140`)。 **存檔那一半完全沒用到** —— 寫入走 `Execute` 裡的 SP,不走 `base.Update`。所以「有主檔」在本片的意義是「這支借用了查詢管線」,不是「這支走四眼」。

#### 6.1.3 查詢那段 SQL 在做什麼(推測)

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:42-106`,一段三層巢狀的彙總:

| 層 | 做什麼 |
|---|---|
| 內層 `T` | `OFD233A` JOIN `OFD221A` JOIN `OFD220A`,逐筆算出 `Memo`(擋不擋的原因)、成功 / 失敗筆數金額 |
| 中層 | JOIN `OFD081V`(小數位數、基金簡稱)、`OFD020V`(扣款行簡稱) |
| 外層 | `GROUP BY` 基金 + 扣款行 + 核印類別,`SUM` 出小計 |

**畫面上的六個小計欄位**(合計 / 成功 / 失敗 × 筆數 / 金額, `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB303.Designer.cs:415-475`)就是這一段算出來的。

#### 6.1.4 卡控總表

`OFDB303` 的卡控**全部寫在 SQL 的 `CASE WHEN` 裡,產出一個 `Memo` 欄**,不是 C# 判斷:

| 時點 | 檢核 | 成立時 `Memo` | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | `OFD221A.SUB_STATUS` 是 `'0'` 或 `'1'` | 尚有扣款資料未回報扣款結果,不可確認 | **記錄不擋**(只寫進 `Memo` 欄) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:68-69` |
| 查詢 | `OFD221A.Status` 不在 `f_TA_GetEVAStatus('A')` 的集合 | 尚有未覆核資料 | 記錄不擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:70-71` |
| 查詢 | 取消確認(`BANK_CFM_CD='N'`)且 `SUB_STATUS` 是 `'0'`/`'1'` | 尚有扣款資料未回報扣款結果,不可確認 | 記錄不擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:72-73` |
| 查詢 | 取消確認且 `OFD303A.POST_CTL_CODE='Y'` | 本日申購資料已過帳,不可取消確認 | 記錄不擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:59-60` |
| 查詢 | 取消確認且 `OFD303A.ALLOT_CTL_CODE='3'` | 本日申購資料已結轉,不可取消確認 | 記錄不擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:61-62` |

**五道全部是「記錄不擋」** —— SQL 只把原因塞進 `Memo`。真正要不要讓使用者按下去,取決於 UI 有沒有看那個 `Memo`,以及 SP `s_TA_OFDB303_Excute` 裡面有沒有再擋一次。 **SP 的腳本不在 repo**(附錄 B),所以**本片無法確認這五道最後是不是真的阻擋**。這裡標「未查證」,不猜。

#### 6.1.5 執行主體

`tran = dbTA.BeginTransaction();` → 對 `OFDB303.Select("IsCheck=true")` 的每一列 `GetStoredProcCommand("s_TA_OFDB303_Excute")` + 六個 IN 參數 + `ExecuteNonQuery(Cmd, tran)` → `tran.Commit();` → `AddResultRow(true, 1, "執行成功")`。 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:179-196`

| 特性 | 事實 |
|---|---|
| **交易邊界** | C# 開、C# 關;SP 跑在 C# 的交易裡(跟 `ofdb.md` 的 `OFDB003` 同一種形狀) |
| **粒度** | 每一個勾選的「基金 + 扣款行 + 核印類別」呼叫 SP 一次;一列失敗整批 rollback |
| **重跑安全** | 靠 SP 內部,C# 端**沒有任何已處理旗標檢查**。`BANK_CFM_CD` 由使用者在畫面上選 `'Y'` / `'N'`,重複按同一個值會重複呼叫 SP |
| **出口** | 只有 SP。不寄信、不產檔 |

#### 6.1.6 這一支的四個問題

| # | 問題 | 嚴重度 | 錨點 |
|---|---|---|---|
| 1 | **成功訊息與實際筆數無關**:`AddResultRow(true, 1, "執行成功")` 的筆數寫死 `1`,而且 `ExecuteNonQuery` 的回傳值**根本沒接**。SP 一列都沒改也是「執行成功」 | 高 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:193`、`:196` |
| 2 | **`catch` 裡先 `tran.Rollback()`**:若 `BeginTransaction()` 自己拋例外,`tran` 是 null,catch 內第一行就再拋 `NullReferenceException`,原始錯誤被吃掉 | 中 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:199-212` |
| 3 | **一般例外的訊息被砍成半句**:`"執行失敗,請檢查 : "` 後面什麼都沒接,`ex.Message` 只進 `HandleBusinessException` | 中 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:210-211` |
| 4 | **`ALLOT_DATE` 參數型別是 `Date`,SP 卻收 `yyyyMMdd` 字串**:查詢時用 `OracleDbType.Date`(`:142`),執行時轉成 `date.ToString("yyyyMMdd")` 傳 `Varchar2`(`:188`)。兩邊對同一個概念用兩種型別 | 中 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:142`、`:188` |

補一條不是 bug 的:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:180` 有一行 `DbCommand Cmd;// = dbTA.GetStoredProcCommand("s_TA_OFDB303_Excute");` —— 被註解的那半是搬到迴圈裡去了(`:185`),**不是漏掉的功能**。

### 6.2 `ATLAS.OTAB` 的三條流水線 —— 連號不是巧合

`OTAB` 那 32 支的代號分三段連號,逐支比對後確認**每一段就是一條業務流水線**, 共用同一份程式樣板(`Select` + `Execute` + 一串 `Check_*`),差別只在動哪幾張表、擋哪幾件事。

#### 6.2.1 三段的對應關係

| 段 | 代號 | 主表 | 業務(推測) |
|---|---|---|---|
| **051–065** | 12 支 | `OFD220` / `OFD221` / `OFD224` | 境外**申購**:下單確認 → 試算 → 集保回報 → 結算調整 → 結帳 |
| **081–094** | 13 支 | `OFD251` / `OFD252` / `OFD253` / `OFD254` / `OFD256` | 境外**贖回**:下單確認 → 價金試算 → 集保回報 → 付款確認 → 結帳 |
| **131–135** | 5 支 | `OFD281` / `OFD282` / `OFD283` | 境外**受益分配**:六階狀態機(§2.5) |

兩條主線是**鏡像對稱**的 —— 申購線每一關在贖回線都有對應的一支:

| 關卡(推測) | 申購線 | 贖回線 | 依據(Designer 標籤 / `#region` 名) |
|---|---|---|---|
| 下單確認 / 回復 | `OFDB051` | `OFDB081` | 兩支 UI 都有「執行功能 / 確認」;PO 都有「SQL String 確認 / 回復」成對區段 |
| 淨值試算 | `OFDB052` | `OFDB082` | 「申購NAV日」/「贖回NAV日」+「取淨值」+「NAVB 塞到 OFD302」 |
| 明細維護 | `OFDB053` | `OFDB083` | 只有「欄位不可編輯」「欄位檢查與連動」,無執行功能 |
| 集保(TSCDLOG)確認 | `OFDB054` | `OFDB084` | 兩支都有「檢查新增資料是否存在於 `OFD221_TSCDLOG1` / `OFD252_TSCDLOG1`」 |
| 電子交易(EC)確認 | `OFDB055` | `OFDB085` | 「EC交易資料未確認不可下單確認」/「EC贖回交易資料是否確認」 |
| 集保回報 | `OFDB057` | `OFDB086` | 「檢查是否有未回報或未繳款的資料」/「是否有集保未回報的贖回資料」 |
| 結算調整 | `OFDB058` | `OFDB088` | 「試算前檢查 `OFD221` 是否在結算調整」/「取得 `RTOT_RFEE`」「持年數」 |
| 個人帳戶下單確認 | `OFDB060` | `OFDB090` | 「檢查是否完成申購分配收檔作業」/「檢查指定日期之前是否有未確認的贖回付款資料」 |
| **結帳** | **`OFDB061`** | **`OFDB091`** | 兩支都呼叫自己的 SP(`S_OTA_OFDB061_EXE` / `S_OTA_OFDB091_EXE`),UI 只有「境外基金公司代碼 + 查詢結果」 |
| 結帳前統計 | `OFDB062` | `OFDB092` | 兩支都只查不改(§5) |
| 綜合帳戶調整 | `OFDB064` / `OFDB065` | `OFDB087` / `OFDB089` / `OFDB094` | 申購線多一支「順延交易日 / 取消交易處理」(`OFDB065`);贖回線多一支「贖回資料刪除」(`OFDB089`) |

**沒有對應的三支**:`OFDB064`(自售綜合帳戶彙總申購資料調整)、`OFDB065`(順延 / 取消)、`OFDB089`(整組刪除)。這三支各自獨立,`OFDB089` 最危險(§6.5)。

#### 6.2.2 共用樣板:`StrXEC` 決定「確認」還是「回復」

流水線上每一支的 `Select` 與 `Execute` 都吃同一個參數 `StrXEC`:

| 值 | 意義 | 撈什麼 / 寫什麼 |
|---|---|---|
| `"1"` | 確認 | 撈 `ALLOT_PROC_CODE = '0'` 的列;`UPDATE … SET ALLOT_PROC_CODE='1'` + 三個 `CFM_ORDER_*` 欄 |
| `"2"` | 回復 | 撈 `ALLOT_PROC_CODE IN ('1','4','5')` 的列;`UPDATE … SET ALLOT_PROC_CODE='0'` + 三個 `CFM_ORDER_*` 欄清空 |

錨點(以 `OFDB051` 為準,其餘同型): `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:100`(確認查詢)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:133`(`ALLOT_PROC_CODE = '0'`)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:155`(回復查詢)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:188-190`(`IN ('1','4','5')`)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:360-377`(確認 UPDATE)、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:378-395`(回復 UPDATE)。

**補一組狀態碼到 §2.5:`OFD221.ALLOT_PROC_CODE` / `OFD252.REDEM_PROC_CODE`**

| 值 | 意義(推測) | 依據 |
|---|---|---|
| `'0'` | 未確認 | 確認前的撈取條件 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:133` |
| `'1'` | 已下單確認 | 確認後寫入 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:364` |
| `'4'` / `'5'` | 更後面的階段(可被回復) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:188-190` |
| `'6'` | 已結轉 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:962`(`ALLOT_PROC_CODE = '6'`) |
| `'9'` / `'D'` | 作廢 / 刪除(檢核一律排除) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:614`、`:659`(`NOT IN ('9','D')`) |

#### 6.2.3 這條流水線的失敗處理寫得比境內那邊好

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:410-418`:`i = ExecuteNonQuery(cmd, tran);` 之後 `if (i == 0) { tran.Rollback(); Result.Clear(); AddResultRow(false, 0, "執行失敗，請檢查資料是否正確"); return modelVDB; }`。

**接了回傳值、影響 0 列就整批 rollback、而且 `return` 出去不繼續跑迴圈。** 這是本片唯一寫對的寫法,`OTAB` 那 32 支幾乎每一支都是這個樣板。 `OFDB135` 甚至把訊息細分到哪一段:`"執行失敗，請檢查資料是否正確(UPDATE OFD282)"` (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:567`、`:610`、`:758`、`:786`、`:826`、`:865`、`:904`)。

**跟境內那邊的對照(§6.4)是本片最刺眼的一組差異:** 同一個動作,`OTAB` 接回傳值並 rollback,`OFDB` 的清算六支寫 `i = 1;` 直接蓋掉。

#### 6.2.4 一個副作用:回復會把欄位寫成 NULL 而不是空字串

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:383-385`、`:389-390`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB081_PO.cs:587-592`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB057_PO.cs:543-547` 都是 `SET COL = ''`。 **Oracle 的 `''` 就是 NULL**,所以「回復」之後那些 `CFM_ORDER_UID` / `CFM_FH_DATE` 欄位是 NULL,不是空字串。下游若寫 `WHERE CFM_ORDER_UID = ' '` 或 `<> ''` 一律比不到。實際影響見附錄 E。

#### 6.2.5 `OFDB131`–`OFDB135`:六階狀態機,`OFDB135` 會產生申購單

狀態機定義在 §2.5,推階的是 `OFD281.PROCESS_CODE`。最後一階 `OFDB135`(3 → 4 受益分配結帳)做的事最多:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 執行前檢核:RD 結帳日、`OFD283`、`OFD303`、RD 入帳日、`OFD221`、`OFD251` 六道 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:932-1195` |
| 2 | **新增 `OFD220` + `OFD221`** —— 配息再投資會變成一張新的申購單 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:419`、`:457` |
| 3 | `UPDATE OFD282` / `UPDATE OFD283` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:532`、`:575` |
| 4 | 呼叫 `S_OTA_OFDB135_EXE` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:620` |
| 5 | 取消結帳:反向 —— 再呼叫一次 `S_OTA_OFDB135_EXE`、`DELETE OFD220` / `DELETE OFD221`、回寫 `OFD281` / `OFD282` / `OFD283` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:693`、`:738`、`:764`、`:799`、`:834`、`:873` |

**第 2 步是跨流水線的接點**:受益分配線的結帳會往申購線丟資料。改 `OFD220` / `OFD221` 的 NOT NULL 欄位時,`OFDB135_PO.cs:419` 的那一長串 `INSERT` 欄位清單要一起改, 否則「申購畫面都好好的,一結配息就爆」。

**取消結帳的 `DELETE OFD220` / `DELETE OFD221` 是本片第二危險的刪除**(第一是 `OFDB089`) —— 它刪的是交易主檔,而不是自己的中間表。

### 6.3 50 個 fail-open 的卡控方法 —— 本片最大的一類系統性缺陷

#### 6.3.1 形狀

`OTAB` 的流水線把每一道卡控寫成一個獨立的 `public bool` 方法,樣板長這樣:

`bool boolvalue = true;` → `try { SELECT COUNT(…); if (iCount > 0) boolvalue = false; }` → `catch (Exception ex) { CommonExceptionBlocker.HandleBusinessException(ex); }`(**只記錄,不改 `boolvalue`**) → `return boolvalue;`(**出錯 → 回 `true` → 放行**)。 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:949-990`

呼叫端: `Dev/ATLAS.OTAB/Source/Control/Control.OTA/OFDB061_Ctl.cs:252-255`(Control 直接轉發)、 `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB061.cs:261`(`if (… == false)` 才擋)。 **`true` = 通過。DB 出錯 → 回 `true` → 卡控放行。**

#### 6.3.2 分布

逐支掃「回傳 `bool` 且 `catch` 內沒有 `throw`」的方法:

| 畫面 | 個數 | 這些方法在擋什麼 |
|---|---|---|
| **`OFDB061`** | **20** | 淨值鎖定 / 淨值相符 / 受益分配淨值 / 單位數為 0 / 庫存結餘 / 結帳控制日期 …… |
| **`OFDB091`** | **18** | 贖回側的同一組 |
| `OFDB084` | 5 | 贖回總價金為 0 / 轉入單位數為 0 / 已結轉 |
| `OFDB328` | 3 | 表頭 / 明細 / 表尾組檔 |
| `OFDB089` | 2 | 是否已下單確認 / 是否有資料可刪除 |
| `OFDB081` | 2 | 贖回單位數與實際沖銷比對 |
| **合計** | **50** |  |

`ofdb3.md §0.2` 在 EC 那片找到 27 個 `Check_*` fail-open。**本片 50 個,是目前各片最多的一次。**

#### 6.3.3 為什麼特別嚴重

這 50 個方法擋的是**結帳前的資料一致性** —— 淨值有沒有鎖、單位數是不是 0、庫存有沒有歸零。一旦資料庫在那一瞬間有任何問題(連線斷、逾時、鎖等待),這些檢核**全部靜默放行**, 然後 `S_OTA_OFDB061_EXE` / `S_OTA_OFDB091_EXE` 就在沒有把關的狀態下把整檔基金結帳掉。 **而且 `HandleBusinessException` 只把例外送進共用處理器,畫面上什麼都不會出現。**

#### 6.3.4 同一批方法還有第二個問題:讀取不進交易

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:977` 是 `dbProduct.ExecuteScalar(cmd)`,**沒有傳 `tran`**。同一支裡其他方法(例如 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:334` 的 `LoadDataSet(cmd, ds, "OFD252", Tran)`) 是有傳的。**同一支程式裡兩種寫法並存**,所以「檢核看到的資料」與「執行時改的資料」不保證在同一個一致性快照上。

#### 6.3.5 加上 Oracle 三值邏輯,漏得更多

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:961-964` 這段檢核同時中三條:

`AND OFD081.ALLOT_NAV_ID <> '3'` / `AND OFD221.ALLOT_PROC_CODE = '6'` / `AND OFD221.ALLOT_CODE <> '3'` / `AND OFD221.NAV_B <> :NAVB`。

`ALLOT_NAV_ID`、`ALLOT_CODE`、`NAV_B` 任一為 NULL,該列的比較結果就是 UNKNOWN,**不會被 `COUNT` 到**, 於是「淨值不一致」這件事查不出來 → `boolvalue` 保持 `true` → 放行。 **這是「淨值不同卻結帳成功」最可能的路徑。** 同型寫法在 `OFDB061` / `OFDB091` / `OFDB084` / `OFDB090` 共 106 處(附錄 E)。

### 6.4 `OFDB481A`–`OFDB491A` 六支 —— `A` 後綴的第四種狀況

#### 6.4.1 這六支在做什麼(推測):基金清算的價金給付鏈

從 Designer 的中文標籤反推,六支是一條有順序的鏈:

| 代號 | 畫面上的字 | 動的表 | 位置(推測) |
|---|---|---|---|
| `OFDB481A` | 清算基準日 / 基金代碼 | `OFD081A` `OFD303A` `OFD495A` | ① 設定 / 查詢清算基準日 |
| `OFDB486A` | **產生基金清算資料** / 清算總單位數 / 清算總金額 / 每單位清算分配金額 / 產生累計 | `OFD081V` `OFD303A` `OFD494A` `OFD496A` | ② 產生清算主檔與明細 |
| `OFDB487A` | **確認** / 期別 / 發放日期 / 清算基準日 | `OFD081V` `OFD494A` `OFD496A` | ③ 確認 |
| `OFDB489A` | **退匯 / 取消退匯** / 實際付款日期 / 受益人ID / 戶號 | `OFD496A` `OFD497A` `BMS001A` `OFD020V` `OFD081A` | ④ 匯款退回處理 |
| `OFDB490A` | **退郵 / 取消退郵** | `OFD496A` `OFD497A` `BMS001A` `OFD081A` | ④ 郵寄退回處理(與 ④ 平行) |
| `OFDB491A` | **重匯 / 重寄 / 取消重匯重寄** / 重新付款日期 | `OFD494A` `OFD496A` `OFD497A` `OFD094A` `OFD095A` `OFD020A` `CTL014` `COD006A` | ⑤ 重新給付 |

`#region` 名直接印證: `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:64`(退匯)、`:150`(取消退匯); `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:66`(退郵)、`:159`(取消退郵); `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB491A_PO.cs:269`(重匯/重寄)、`:346`(取消重匯/重寄)。

#### 6.4.2 逐支找不帶 `A` 的版本 —— 六支全部找不到

逐支在 `Dev/` 全樹找同號不帶 `A` 的檔(`OFDB481` / `OFDB486` / `OFDB487` / `OFDB489` / `OFDB490` / `OFDB491`), **六支的命中數全部是 0** —— 回傳的只有它們自己那六層帶 `A` 的檔案。

同時查三種已知成因,三種都不成立:

| 已知成因 | 檢驗 | 結果 |
|---|---|---|
| **境內外**(`ofd5.md` / `ofd7.md`:`FUND_TYPE` `'2'`/`'1'`,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`) | 六支的 PO + UI 全文找 `FUND_TYPE` / `SHORE` | **0 個命中**,不成立 |
| **MSSQL→Oracle 遷移改名**(`ofd4.md` / `ofd123.md`:同一段 SQL 兩版只差表名) | 需要兩份高度相似、只差表名的程式 | 六支彼此最高只有 64.4% 相似(下表),**沒有任何一對是「同一段 SQL 兩版」**,不成立 |
| **同概念第二張表**(`ofd123.md` 的 `OFD017B`) | 需要 `OFDB481` 與 `OFDB481A` 並存 | 不存在,不成立 |

六支兩兩相似度(PO 層,去註解後逐行比):

| 對 | 相似度 |
|---|---|
| `OFDB489A` / `OFDB490A` | **64.4%**(退匯 / 退郵,複製貼上的一對) |
| `OFDB486A` / `OFDB487A` | **56.8%**(產生 / 確認) |
| `OFDB481A` / `OFDB486A` | 43.6% |
| `OFDB481A` / `OFDB487A` | 43.2% |
| 其餘 11 對 | 10.7% ~ 21.1%(只有樣板骨架相同) |

#### 6.4.3 結論:`A` 在這六支上是「清算這一族」的族名,不是境內外也不是遷移

**〔假設〕這六支的 `A` 是清算價金給付系列在建立時就帶著的族名,沒有語意上的對照組。**

依據三條:

1. 六支沒有任何不帶 `A` 的對應版本(上表),所以它不是「兩個版本二選一」的標記。

2. 它們的主表 `OFD494A` / `OFD495A` / `OFD496A` / `OFD497A` 也全部帶 `A`,而且 `ATLAS.OFD` 的維護畫面 `OFDM481A`(主檔 `OFD494A`)、`OFDM482A`(主檔 `OFD496A`)**也帶 `A`** —— 整族(B 畫面、M 畫面、表)一起帶。

3. **但「跟著表名走」也講不通**:同一個 48x 區段的 `OFDM485` 沒有 `A`,主檔卻是 `OFD484A`。

所以本文只敢說「族名」,不說「規則」。**`ofdb3.md §6.2`「批次上的 `A` 對不成境內外」在本片再次成立。**

#### 6.4.4 這六支的核心缺陷:12 處 `ExecuteNonQuery` 回傳值被常數蓋掉

這是本片**最會咬人**的一顆。樣板長這樣(`OFDB486A`):

`i = m_db.ExecuteNonQuery(cmd, tran);` → `//因固定回傳-1 設定1代表成功` → `i = 1;` → `if (i <= 0) { AddResultRow(false, 0, ""); tran.Rollback(); } else { AddResultRow(true, 1, ""); tran.Commit(); }`。 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB486A_PO.cs:131-145`

`i = 1;` 之後 `if (i <= 0)` **永遠不成立** —— rollback 那一支是死碼,**任何情況都 Commit、都回「成功」**。註解「因固定回傳 -1」說明寫的人確實觀察到回傳值不對(Oracle 的 `ExecuteNonQuery` 對 SP 就是回 -1), 但處置方式是**把判斷拿掉**,不是改判斷依據。

全部 12 處:

| 畫面 | 行 |
|---|---|
| `OFDB486A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB486A_PO.cs:131` |
| `OFDB487A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB487A_PO.cs:125` |
| `OFDB489A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:87`、`:136`、`:162`、`:194` |
| `OFDB490A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:91`、`:144` |
| `OFDB491A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB491A_PO.cs:289`、`:333`、`:394`、`:409` |

**`OFDB489A` / `OFDB490A` / `OFDB491A` 三支跑的是自己組的 `UPDATE` / `INSERT` / `DELETE`,不是 SP** —— 那些語句的 `ExecuteNonQuery` 本來就會回真正的影響列數,`i = 1;` 是純粹把可用資訊丟掉。 `OFDB489A` 的例子:

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:87-89`:`UPDATE OFD496A … WHERE FUND_ID/ISSUE_CODE/BF_NO` 的 `ExecuteNonQuery` 回傳值一樣被下一行的 `i = 1;` 蓋掉。

**退匯的那一列如果 PK 對不上、一列都沒更新到,畫面照樣說成功**,而 `OFD497A` 的記錄卻插進去了 —— 資料兩邊對不起來。嚴重度 **高**。

#### 6.4.5 還有一段真的寫錯的錯誤處理

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:136-146`: `i += ExecuteNonQuery(...)` → `i = 1;` → `if (i == 0) { tran.Rollback(); Result.Clear(); AddResultRow(false, 0, "") }` → `j += 1;`。

三個問題疊在一起:

1. `i = 1;` 讓 `if (i == 0)` 成為死碼(同上)。

2. **就算它活著**,`tran.Rollback()` 之後**沒有 `return` 也沒有 `break`**,迴圈會繼續對已 rollback 的交易下語句。

3. 訊息是空字串,使用者只看到「失敗」兩個字。

#### 6.4.6 假四眼

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:100-119` 的 `INSERT INTO OFD497A`:

| 欄位 | 寫什麼 |
|---|---|
| `Status` | 寫死 `'302'`〔客戶特定〕 |
| `CreateID` / `EntryID` / `UpdateID` / `VerifyID` / `ApproveID` | **全部同一個** `:UserID` |
| `CreateDate` / `EntryDate` / `UpdateDate` / `VerifyDate` / `ApproveDate` | **全部 `sysdate`** |
| `RejectID` / `RejectDate` | `' '` / `TO_DATE('1900/01/01','yyyy/mm/dd')` |

**`OFD497A` 的四眼軌跡是假的。** `OFDB490A` 同型。稽核若拿這張表的 `VerifyID` / `ApproveID` 當覆核證據,拿到的是操作者自己。嚴重度 **高**。

### 6.5 `OFDB089` 境外贖回資料刪除 —— 本片唯一的「整組刪除」

#### 6.5.1 它刪什麼

一次交易內連下**六段 `DELETE`**,全部以 `Check_REDEMTrade_CanDelete` 回傳的子查詢 `xDeleteSQl` 當範圍:

| 順序 | 語句 | 表的意義(推測) | 錨點 |
|---|---|---|---|
| 1 | `DELETE OFD255 WHERE REDEM_NO IN (…)` | 調整記錄檔 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:123-126` |
| 2 | `DELETE OFD251 WHERE REDEM_NO IN (…)` | **贖回主檔** | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:146-149` |
| 3 | `DELETE OFD252 WHERE REDEM_NO IN (…)` | 贖回明細 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:168-171` |
| 4 | `DELETE OFD253 WHERE REDEM_NO IN (…)` | 轉申購明細 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:189-192` |
| 5 | `DELETE OFD254 WHERE REDEM_NO IN (…)` | 付款明細 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:210-213` |
| 6 | `DELETE OFD256 WHERE FUND_ID IN (…) AND REDEM_DATE = :REDEM_DATE` | 自售綜合帳戶贖回彙總 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:239-243` |

#### 6.5.2 兩道卡控,兩道都 fail-open

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | `Check_Trade_NeedReply`:有沒有已作下單確認(`OFD303.REDEM_CTL_CODE >= '2'`)的贖回 | 回「尚有基金之贖回資料已作下單確認,請先回復再做此作業!」並 `return` | 阻擋 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:104-111` |
| 執行前 | `Check_REDEMTrade_CanDelete`:有沒有資料可刪 | 回「無贖回資料可刪除!」並 `return` | 阻擋 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:114-116`、`:262-267` |

**兩個方法的 `catch` 都只呼叫 `HandleBusinessException`,不改回傳值,初始值都是 `true`** (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:343-346`、`:353`)。 `Check_Trade_NeedReply` 的 `true` = 「沒有已確認的資料,可以刪」→ **查詢出錯就變成可以刪**。嚴重度 **高**。

#### 6.5.3 第六段的刪除範圍靠 `NVL` 撐著

`DELETE OFD256 WHERE FUND_ID IN (SELECT FUND_ID FROM OFD081 WHERE FH_CD = :FH_CD AND FUND_ID = NVL(:FUND_ID, OFD081.FUND_ID)) AND REDEM_DATE = :REDEM_DATE` —— `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:232-243`

畫面上「基金代碼」**留空**時,`:FUND_ID` 傳的是空字串 → Oracle 視為 NULL → `NVL` 展開成「這家境外基金公司的**所有**基金」。這是設計上的「空白 = 全部」,不是 bug, 但**畫面上沒有任何一句話講這件事**(`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB089.designer.cs` 的標籤只有「贖回日期 / 境外基金公司代碼 / 基金代碼」), 而按下去刪的是整家公司當日的贖回彙總。嚴重度 **中**,列在附錄 E。

#### 6.5.4 重跑與失敗處理

- **重跑安全**:第二次跑時 `Check_REDEMTrade_CanDelete` 找不到列 → 回「無贖回資料可刪除!」。安全。

- **提早 `return` 沒有 `Rollback`**:`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:110`、`:266` 兩個 `return` 都在交易開啟後、只靠 `finally` 的 `dbProduct.Dispose(tran)` 收尾(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:280-284`)。那兩條路徑本來就沒寫過資料,實務上無害,但**這是「交易只 Commit 不 Rollback」型態的一個實例**。

- **六段 `DELETE` 的 `i` 全部沒檢查**(`:139`、`:162`、`:183`、`:204`、`:225`、`:256`,每一段都覆寫上一段的值), 所以「刪了 0 列」跟「刪了 5,000 列」回的訊息一模一樣:「個人帳戶贖回資料刪除完成!!」 (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:269`)。嚴重度 **中**。

### 6.6 `OTAB901` 境外基金資料官網上傳 —— 本片唯一打外部 HTTP API 的一支

#### 6.6.1 它在做什麼

畫面本體只有一句話與兩個功能鍵:「請執行右下方基金主檔或淨值上傳功能鍵」 (`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.Designer.cs:104`、`:91`)。兩個鍵各開一個子對話框:

| 功能 | 子畫面 | 資料來源 | 錨點 |
|---|---|---|---|
| 上傳基金基本資料 | `OTAB901p0` | `OFD081`(境外基金主檔) | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:116-124` |
| 上傳基金淨值資料 | `OTAB901p1` | `OFD302`(境外淨值資料檔) | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:128-146` |

`OTAB901p0` 與 `OTAB901p1` **逐行相似度 92.3%**(260 / 271 行),是複製貼上的一對。流程(以 `OTAB901p0` 為準):

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 以 `FUND_ID` 呼叫 `S_OTA_OTAB901_Get`(`iEX_TYPE='1'`),把 `OFD081` + `OFD302` 兩個 refcursor 收進 Model | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:134-146` |
| 2 | 從回傳的第一列讀 `API_URL` + `API_NAME`,組出端點 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:123-128` |
| 3 | **把 `API_URL` / `API_NAME` 兩欄從 DataTable 刪掉**,再把整張表轉成 JSON | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:137-144` |
| 4 | `HttpClient.PostAsync(...).Result` 同步送出 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:165` |
| 5 | 成功才呼叫 `s_INSERT_CALLAPI_HISTORY` 寫 log | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:180-189` |

#### 6.6.2 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | `validatorManager1.DataValidate()` 欄位檢核 | 取消執行 | 阻擋 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:104-111` |
| 上傳前 | `FUND_ID` 是空的 | **整個方法直接跳過,什麼都不做也不提示** | **過濾(無提示)** | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:106` |
| 上傳前 | SP 回傳 0 列 | 同上,不提示 | 過濾(無提示) | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:115-117` |
| 上傳前 | `strAPI_PATH` 是空字串 | 訊息「API Path 未設定: CTL014(953), 請連絡資訊人員.」 | 阻擋 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:130-134` |
| 回應後 | `myRV.Status != "Success"` | 警示訊息,**但資料已經送出去了** | 警示 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:196-199` |
| 回應後 | HTTP 非 2xx | Fatal 訊息 | 警示 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:201-204` |

#### 6.6.3 六個問題

| # | 問題 | 嚴重度 | 錨點 |
|---|---|---|---|
| 1 | **TLS 憑證驗證被整個行程關掉**:`ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };`。`ServicePointManager` 是 process 層級的靜態物件 —— **按下這個鈕之後,整個主程式往後所有 HTTPS 連線都不驗憑證** | **高** | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:161`、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p1.cs` 同段 |
| 2 | **把所有 `SecurityProtocolType` 列舉值相加當成啟用的協定**:`foreach (var value in Enum.GetValues(typeof(SecurityProtocolType))) result += (int)value;` —— 連 `Ssl3` / `Tls` / `Tls11` 這些已淘汰的協定一起打開,同樣是 process 層級 | **高** | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:34-40` |
| 3 | **「API Path 未設定」那道檢核永遠到不了**:`new Uri(strAPI_URL)` 在第 126 行,空字串或格式不對會先拋 `UriFormatException`,而那一行**不在 try 裡**(try 從 156 行才開始)。使用者看到的是未處理例外,不是那句中文 | 高 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:126` vs `:130-134` vs `:156` |
| 4 | **失敗不寫 log**:`s_INSERT_CALLAPI_HISTORY` 只在 `IsSuccessStatusCode` 成立的分支裡呼叫。HTTP 500、連線逾時、例外,一律**沒有任何 API 呼叫記錄**。事後查「到底送出去沒有」查不到 | 高 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:171-189` |
| 5 | **PO 開的連線與 `finally` 釋放的連線不是同一個**:三個方法都用 `m_db.BeginTransaction()`,`finally` 卻寫 `dbProduct.Dispose(tran)` / `dbProduct.Dispose()`。`m_db` 是這支自己 `new` 的,`dbProduct` 是基底的 —— **`m_db` 的連線沒有被釋放** | 中 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:86`+`:111-115`、`:129`+`:160-164`、`:177` 一帶 |
| 6 | **`InsAPILog` 失敗時的訊息是「取得境外基金主檔(OFD081)失敗,請檢查」** —— 複製貼上沒改。寫 log 失敗會顯示成讀基金主檔失敗 | 中 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:108` |

另外 `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:142-143` 有兩行 `Console.WriteLine` —— WinForms 沒有主控台,**這兩行等於寫進虛空**;而 `DoExp1`(`:116-124`)**連 try 都沒有**, 上傳基本資料時拋例外會直接彈未處理例外對話框。

`BeginTransaction()` 三處都寫在 `try` **外面**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:86`、`:129`), 連線取不到時例外不會被自己的 catch 接到。

### 6.7 `OFDB305` / `OFDB323` 日結轉 —— 12 道 + 11 道阻擋,其中一道 2009 年被關掉

#### 6.7.1 這一對的關係

`OFDB305` 是**申購日結轉**、`OFDB323` 是**買回日結轉**,PO 逐行相似度 **42.2%**。兩支的骨架一樣:一段超長的 `CASE WHEN … THEN '訊息'` 串出「這檔基金今天能不能結轉」, 存進查詢結果的 `Status_DESCRP` 欄,UI 端再逐列把有訊息的挑出來變成錯誤(阻擋)。

UI 端的挑法: `foreach (… OFDB305_Fund.Select("Status_DESCRP<>''")) { ValidateErrList.AddError(ugrdFunds, …); }` —— `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB305.cs:71-75`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB323.cs:69-73`

(這裡的 `"Status_DESCRP<>''"` 是 **ADO.NET `DataTable.Select` 的運算式語法,不是 SQL**, 在 .NET 裡 `''` 就是空字串,**這一行是對的**,不是 Oracle 空字串陷阱。列在附錄 E.13。)

#### 6.7.2 `OFDB305` 的卡控總表(申購日結轉)

全部是**阻擋**,全部寫在同一段 SQL 的 `CASE WHEN`:

| # | 檢核 | 訊息 | 錨點 |
|---|---|---|---|
| 1 | 基金尚未募集 | 此基金尚未募集,不可執行 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:176` |
| 2 | 前一日尚有未結轉資料 | 前一日尚有未結轉資料,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:192` |
| 3 | 指定扣款(傳真委扣)尚未關帳(`CTL012` + `OFD0811A.APPOINT_SUB_YN='Y'`) | 傳真委扣資料尚未關帳,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:201-209` |
| 4 | `OFD233A.BANK_CFM_CD='N'`(扣款行未回覆) | 仍有傳真委扣資料尚未作扣款行回覆,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:211-216` |
| 5 | 部分資料淨值與現行淨值不同 | 有部份資料的淨值與目前的淨值不同,請重新執行單位數計算作業 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:218-230` |
| 6 | 受益人是註銷戶(`BMS001A.FREEZE_CD='Y'`) | 申購資料中有受益人為註銷戶,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:232-243` |
| **7** | **受益人暫停申購** | **(整段被 `/* */` 註解,2009/06/13 起不檢核)** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:245-260` |
| 8 | `OFD221A.Status` 未覆核 | 申購資料中有未覆核資料,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:261-266` |
| 9 | `OFD232A.Status` 未覆核(銷售機構彙總) | 申購銷售機構彙總資料中有未覆核資料,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:268-272` |
| 10 | `OFD611A.ALLOT_CTL_CODE <> '2' AND SYSTEM_ID='1'` | 尚有電子交易資料未拋轉,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:274-279` |
| 11 | `OFD621A.EC_ALLOT_PCODE IN ('0','1')` | 尚有電子交易資料未轉入,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:281-286` |
| 12 | 轉申購對應的贖回未結轉(`OFD251A.REDEM_PROC_CODE<>'3'`) | 轉申購的贖回資料尚未結轉,不可執行申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:288-299` |

另外兩段輔助:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:98`(法人公告歷史檔 `LOG017A` 檢核)、 `:384`(銷售機構贖回明細與彙總是否相符)。

`OFDB323`(買回日結轉)是對稱的 11 道,`#region` 名列在 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB323_PO.cs:184-268`。

#### 6.7.3 第 7 道:被註解掉的「受益人暫停申購」

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:245-260`:`#region` 標題還在、第 246 行寫著「2009/06/13 by Reiko 此段暫不檢核」,整段 `WHEN EXISTS(…) THEN …` 被 `/* */` 包住。

**這是真的被註解(`/* */`),不是 `ofdb3.md` 那種「`#region old` 其實還活著」的假註解。** 影響:自 2009 年起,**暫停申購的受益人不會擋住申購日結轉**。註解只寫「暫不檢核」,沒說什麼時候恢復。另外那一段用的是 MSSQL 的 `dbo.f_IsPauseTrade(…) AS P` 語法(`:251`), 所以就算解除註解也**不能直接用** —— Oracle 的 table function 要寫 `TABLE(f_…)`。嚴重度 **中**(卡控消失,但不是資料損壞)。

#### 6.7.4 第 5 道的其中一半在 Oracle 上是死的

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:229`:

`AND ((OFD220A.TRAN_PAY_WAY = '1' AND REMIT_FAIL_CODE='') OR (OFD220A.TRAN_PAY_WAY = '2' AND OFD221A.SUB_STATUS = '2'))`

**Oracle 的 `REMIT_FAIL_CODE=''` 等同 `= NULL`,結果永遠 UNKNOWN。** 所以 `TRAN_PAY_WAY='1'`(匯款)那一半永遠不成立 —— 匯款件的「淨值與現行淨值不同」**檢查不到**。這一行的註解寫「20090814 By *** 加 OFD220A 條件」,是 SQL Server 時代加的,那時 `= ''` 是對的。遷移到 Oracle 後就死了,而且**沒有任何錯誤訊息**。

**這是本片最會咬人的一顆**:一道存在、看起來有效、實際只擋一半的資料一致性卡控。嚴重度 **高**。

### 6.8 T-SQL 殘留與七支跑不起來的 —— 同一個時代的兩種病

#### 6.8.1 七支 `BasicEVAPO` 的完整證據

證據鏈(§0.2 第一件事已列表,這裡補判定過程):

1. `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`:`protected Database dbTA = null;`

2. `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-173`:建構子裡只 `new SystemConfigurationSource()`, `dbTA = provider.Create("TA")` 與 `dbPTPF = provider.Create("SWProduct")` **四行全部是註解**。

3. 基底自己有 **182 處**用到 `dbTA`。

4. 七支子類**沒有一處**賦值。

第一次碰到的地方(按下執行鈕會走到的最早一行)已列在 §0.2。

#### 6.8.2 這七支同時帶著 T-SQL

它們原本就是 SQL Server 時代的程式,遷移時沒動:

| 症狀 | 支數 | 例 |
|---|---|---|
| `@參數` 具名前綴 | 7 支全部 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:414` |
| `System.Data.SqlDbType` | 7 支全部 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:414-416` |
| `Convert(nvarchar, …, 111)` | `OFDB236` `OFDB240` `OFDB242` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:412`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB240_PO.cs:249`、`:272` |
| `ISNULL(...)` | `OFDB242` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB242_PO.cs:254-262`(在 `#region OLD` 的註解裡) |
| **`欄 = ''` / `欄 <> ''` 在 `WHERE`** | `OFDB236` `OFDB237` `OFDB239` `OFDB240` `OFDB241` `OFDB242` `OFDB307` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:128`、`:130`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB240_PO.cs:245`、`:268`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB307_PO.cs:81` |

**這批 `= ''` 在 SQL Server 上是正確的寫法**(T-SQL 的 `''` 是真的空字串), 搬到 Oracle 才變成恆 UNKNOWN。所以它們不是「寫錯」,是「沒跟著搬」。但因為連線本來就是 null,這些 SQL 一次都沒跑過 —— **兩個問題互相遮蔽**。

#### 6.8.3 兩支能跑、卻仍帶 T-SQL 的

這兩支比上面七支危險,因為它們**會真的執行**:

| 畫面 | 行 | 內容 | 後果 |
|---|---|---|---|
| `OFDB330` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:571` | `WHERE REDEM_NO=@REDEM_NO … convert(varchar,REDEM_ACT_PAY_DATE,111) > convert(varchar,@REDEM_ACT_PAY_DATE,111)` | Oracle 拒絕 → 落到 catch → 訊息是空字串(`:445`、`:452`) |
| `OFDB305` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:229` | `REMIT_FAIL_CODE=''` | 卡控只擋一半(§6.7.4) |

`OFDB330` 那一行所在的方法叫「ui的實際付款日要大於db的實際付款日」 (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:559`), 是退匯付款通知的日期合理性檢核 —— **這道檢核在 Oracle 上一定失敗**。而三個 `AddInParameter` 全部被註解掉(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:575-578`), 所以就算 SQL 語法對了,參數也沒綁。**整個方法是死的。** 嚴重度 **高**。

#### 6.8.4 成對批次只改一邊:`OFDB239` / `OFDB241`

這一對是「匯款比對關帳」與「取消關帳」,PO 逐行相似度 **83.0%**。唯一實質差異在 UPDATE 的條件:

| 畫面 | UPDATE 條件 | 錨點 |
|---|---|---|
| `OFDB239`(關帳) | `WHERE FUND_ID=@FUND_ID AND CTL_DATE=@CTL_DATE AND (OFD303A.REMIT_CLS_CD='Y' AND OFD303A.REMIT_CTL_CODE='N')` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:51-54` |
| `OFDB241`(取消關帳) | `where FUND_ID=@FUND_ID AND REMIT_CTL_CODE='Y' and CTL_DATE=@CTL_DATE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB241_PO.cs:51-52` |

**`OFDB239` 有「本日須執行關帳」(`REMIT_CLS_CD='Y'`)這一道,`OFDB241` 沒有。** 也就是說「本日不須關帳」的基金,關不了帳,但**可以被取消關帳**。 `OFDB239` 的查詢段明明算過 `REMIT_CLS_CD<>'Y' THEN '本日不須執行關帳作業'` (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:132`),`OFDB241` 那一段也照抄了,**但 UPDATE 沒跟上**。 (兩支都跑不起來,所以目前是理論上的不對稱;修好連線之後會變成真的。)

#### 6.8.5 另一對:`OFDB432` / `OFDB434`

「產生服務費資料」的一對,PO 相似度 **79.0%**,差別是分群維度不同,**不是缺陷**:

| 畫面 | 分群維度 | 表 | SP |
|---|---|---|---|
| `OFDB432` | 銷售機構(`AGENT_ID` + `AGENT_CODE`)+ 基金群組 | `OFD431A` `OFD432A` `OFD433A` | `s_TA_OFDB432_Exe` |
| `OFDB434` | 受益人群組(`BF_NO_GRPCD`)+ 基金群組 | `OFD429A` `OFD437A` `OFD438A` | `s_TA_OFDB434_Exe` |

兩支的 `HasTrailerRate` / 「檢核是否已有設定退佣經理費率」/「是否已鎖定」/「是否能產生或刪除」三道卡控結構一致 (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB432_PO.cs:135`、`:182`、`:230`; `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB434_PO.cs:130`、`:173`、`:218`)。兩支都還留著沒用到的 `using System.Data.SqlClient;`,是遷移殘跡,不影響執行。

### 6.9 其餘各支速寫

| 代號 | 做什麼(推測) | 值得記的一件事 |
|---|---|---|
| `OFDB221` | 匯款入帳檔上傳(一般格式 / 郵局格式兩種) | 兩種格式各一段解析,`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB221.cs:80`、`:135`;上傳路徑用 `OpenFileDialog`,無預設 |
| `OFDB236` | 匯款入帳資料匯入 / 刪除 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB236.cs:238` 把預設目錄寫死成 `c:\`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:146` 把 `FUND_ID` 與兩個日期**直接串進 SQL** |
| `OFDB237` | 申購與匯款逐筆比對 → 寫回 `OFD221A` / `OFD236` / `OFD237` | 本群最長的一支(1,216 行);`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB237_PO.cs:74` 把 `FUND_ID` **串進 SQL**,同一行還有 `REMIT_CTL_NO=''` |
| `OFDB239` / `OFDB241` | 匯款比對關帳 / 取消關帳 | §6.8.4 |
| `OFDB240` | 匯款資料作廢 / 取消作廢 | 兩份報表 `OFDB240RPSA` / `OFDB240RPSB`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB240_PO.cs:245`、`:268` 的 `= ''` |
| `OFDB242` | 退匯明細表(`AA_REPORTMASTERSCHEMA` 報表定義) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB242_PO.cs:253` 有 `#region OLD`,但裡面是**真的 `//` 註解**,不是假註解 |
| `OFDB285` | 受益分配資料下載(格式由 `OFD264A` / `OFD265A` 設定驅動) | **完全不開交易**;畫面有「信件主旨 / 信件內容」欄位(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB285.Designer.cs:481`、`:522`),**但程式裡沒有任何寄信程式碼**(全片 `SendMail` / `SmtpClient` 命中 0) |
| `OFDB289` | 扣繳憑單申報媒體檔 | 不開交易;`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB289.cs:315` 有 `#region old`(真註解);三層檔案是 cp950 |
| `OFDB290` | 年度資料轉出(`轉出路徑` 由畫面指定) | 全片最短的 PO(97 行),只呼叫一支 SP |
| `OFDB307` | 匯款比對過帳控制 | 跑不起來;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB307_PO.cs:79` 有 `OR (OFD220A.REMIT_ACC_TYPE='2' AND 1=1)` —— `1=1` 讓這一支永遠成立,等於該分支無條件納入 |
| `OFDB311` | 申購拆單(轉出戶號 / 轉入戶號 + 拆單原因) | 三道檢核集中在 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB311_Ctl.cs:69`「Check 檢核三點」 |
| `OFDB328` | 買回付款媒體檔(表頭 / 明細 / 表尾三段,格式由 `OFD264A` / `OFD265A` 驅動) | 不開交易;報表段**用寫死字串 `"DR"` 決定走哪一支 SP**(下段);`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1398` 有一整段「已停用」的 ACH 付款檢核 |
| `OFDB330` | 退匯付款通知 / 取消 | §6.8.3 |
| `OFDB351` | 後收級別基金費用計算 | **本片寫得最乾淨的一支**:同一支 SP 用 `iCHECK_DATA='Y'/'N'` 分「執行前檢查」與「正式執行」,OUT 參數 `strMsg` 有值就 rollback(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB351_PO.cs:71-84`) |
| `OFDB432` / `OFDB434` | 服務費資料產生 | §6.8.5 |
| `OFDB052` / `OFDB082` | 申購 / 贖回淨值試算 | 兩支都會「NAVB 塞到 `OFD302`」(`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB052.cs:206`、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB082.cs:218`)—— **試算會寫淨值檔** |
| `OFDB062` / `OFDB092` | 結帳前統計 | 相似度 76.6%;只查不改(§5) |
| `OFDB064` / `OFDB065` | 自售綜合帳戶彙總調整 / 順延與取消交易 | `OFDB065` 會 `DELETE` 四處 + 寫 `OFD221_TSCDLOG` |
| `OFDB087` / `OFDB094` | 贖回明細維護 | 只有欄位連動,無執行功能 |
| `OFDB131` ~ `OFDB135` | 受益分配六階狀態機 | §6.2.5 |

**`OFDB328` 的寫死字串**:

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1128-1154`:取勾選的第一列, `if (firstRow.FILE_ID.IndexOf("DR") == 0)` 走 `S_TA_OFDB285_EXCUTE_RPS`(受益分配),否則走 `S_TA_OFDB328_EXCUTE_RPS`(買回)。

**檔案編號前兩碼是不是 `"DR"` 決定走哪一支 SP、帶哪一組參數。** 新增一種以 `DR` 開頭的檔案編號就會被當成受益分配。 `:1129` 的 `if (firstRow == null) return modelVDB;` 也是**靜默結束**,畫面不會有任何訊息。 `:1170` 的 `bool.Parse(…)` 在參數不是 `True`/`False` 時會拋 `FormatException`。

### 6.10 順序相依總表

本片沒有任何程式碼強制順序,**順序全靠各支自己的「前置狀態檢核」擋**。把檢核反推回來,實際的先後是:

| 流程 | 順序 | 誰擋誰 |
|---|---|---|
| 境內扣款 | `OFDB221`/`OFDB236` 上傳 → `OFDB237` 比對 → `OFDB240` 作廢 → `OFDB239` 關帳 → `OFDB303` 扣款行確認 → `OFDB307` 過帳 → `OFDB305` 申購日結轉 | `OFDB239` 擋「尚有未比對完成的申購資料」;`OFDB305` 第 3、4 道擋「傳真委扣未關帳 / 未回覆」 |
| 境內買回 | `OFDB323` 買回日結轉 → `OFDB328` 付款媒體 → `OFDB330` 退匯通知 | `OFDB323` 第 1 道擋「前一日尚有未結轉資料」 |
| 境內清算 | `OFDB481A` → `OFDB486A` → `OFDB487A` → `OFDB489A`/`OFDB490A` → `OFDB491A` | `OFDB487A` 的「檢查 `OFD496A`」「檢查 `OFD494A` 的狀態」(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB487A_PO.cs:175`、`:196`) |
| 境外申購 | `OFDB051` → `OFDB052` → `OFDB054`/`OFDB055` → `OFDB057` → `OFDB058` → `OFDB060` → `OFDB061` | `OFDB061` 的 20 個檢核方法(§6.3) |
| 境外贖回 | `OFDB081` → `OFDB082` → `OFDB084`/`OFDB085` → `OFDB086` → `OFDB088` → `OFDB090` → `OFDB091` | `OFDB091` 的 18 個檢核方法 |
| 境外受益分配 | `OFDB131`(0→1) → `OFDB133`(1→1A→2) → `OFDB134`(2→3) → `OFDB135`(3→4) | `OFD281.PROCESS_CODE`(§2.5) |
| 跨流程 | `OFDB135` 結帳會**產生** `OFD220` / `OFD221`,再流回申購線 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:419`、`:457` |

**沒有任何一支會去檢查「上一支跑完了沒」以外的東西** —— 所有相依都是透過資料狀態(`ALLOT_PROC_CODE` / `REMIT_CTL_CODE` / `PROCESS_CODE` / `GET_STATUS`)間接表達。 `ofdb3.md §6.12` 的 `OFDB600` → `OFDB605` 那種「查不到就直接阻擋」的硬相依,本片沒有。

## 7. 報表(R)

**本片無 R 代號畫面。** 有 7 支批次自己帶報表,走 `ReportDocument` + `ReportParameterUtility`, 資料來源是 PO 裡另外一段查詢或 SP,`.rpt` 檔不在版控。

| 畫面 | RPS 設定鍵 | 取數來源 | 參數(取自 `AddInParameter`) |
|---|---|---|---|
| `OFDB221` | `OFDB221RPS` | PO 的匯入結果 | 檔名 / 格式別 |
| `OFDB240` | `OFDB240RPSA`、`OFDB240RPSB` | `OFD221A` + `BMS001` + `OFD220A` | `FUND_ID` / 作廢日期區間 |
| `OFDB242` | `OFDB242RPS` | `OFD236` + `OFD019` + `OFD020V` + `OFD0819` | `FUND_ID` / 日期 |
| `OFDB285` | `OFDB285RPS` | `S_TA_OFDB285_EXCUTE_RPS` | `iFUND_ID` / `iYEARS` / `iBASE_DATE` |
| `OFDB305` | `NFDR106` / `NFDR106RPS`、`NFDR110` / `NFDR110RPS`、`OFDR001A` / `OFDR001ARPS` | PO 查詢結果 | `FUND_ID` / `ALLOT_DATE` |
| `OFDB323` | `NFDR110` / `NFDR110RPS`、`NFDR152` / `NFDR152RPS2` | PO 查詢結果 | `FUND_ID` / `REDEM_DATE` |
| `OFDB328` | `OFDB328RPS`(以及借用 `OFDB285RPS`) | `S_TA_OFDB328_EXCUTE_RPS` / `S_TA_OFDB285_EXCUTE_RPS` | 見 §6.9 |
| `OFDB330` | `OFDB330RPS`、`OFDB330RPS2` | PO 查詢結果 | `FUND_ID` / 付款日 |
| `OFDB491A` | `OFDB491ARPS1`、`OFDB491ARPS2` | PO 查詢結果 | `FUND_ID` / `ISSUE_CODE` |

**`OFDB305` 與 `OFDB323` 共用 `NFDR110`** —— 改那張報表要同時看申購與買回兩邊。

## 8. 跨模組共用

```text
[圖] 本片與 EC 共用的一日作業線、對外讀寫的表、對既有文件的四處補強，以及相鄰值得一起追的東西
圖中文字:① 境內一日作業的最後兩關 —— EC 沒跑完就結不了帳 / OFDB600 605 電子交易 / ofdb3 那片 / OFD611A OFD621A / 拋轉碼與轉入碼 / OFDB305 第 10 第 11 道 / 查不到就阻擋 / 申購日結轉 / 本片 6.7 / 帳務 / 本片以外 / ② 本片寫入、別的模組讀取 / OFD303A OFD303 / 結帳控制 26 支動它 / OFD496A OFD497A / ATLAS.OFD 的 OFDM482A 讀 / OFD302 / 試算會寫淨值檔 / OFD220 OFD221 / OFDB135 結帳會新增 / ③ 本片讀取、別的模組維護 —— 改欄位要回頭看幾十支 / FSK003 / OTAB 26 支 JOIN / BMS001A / BMS 維護 OTAB 22 支 / OFD081A OFD081V OFD081 / DEC_LEN 決定小數位 / CTL014 CTL000 CTL012 / 代碼與控制 / SDM010A RSP072A / 其他模組 / ④ 本片對既有文件的四處補強 / BasicEVAPO 再加七支 / ofdb 只點名四支 / 批次的 A 後綴第四種狀況 / 族名 沒有對照組 / OTAB 的 SP 在版控裡 / 其他片都是零支 / 本片沒有排程也沒有 Remoting / ofdb3 那條路不適用 / ⑤ 黑箱:全片的例外都流向同一個地方 / CommonExceptionBlocker / 無原始碼 58 支唯一去處 / SQLHelper EVAStringHelper / 組查詢條件 / m_OTABiz / 日期與淨值計算 / UIJsonHelper / OTAB901 轉 JSON / f_TA 系列 / 腳本不在 repo / ⑥ 相鄰但不在本片、值得一起追的 / OFDB903 / 同在 OTAB 未列名單 / OFDM481A OFDM482A OFDM485 / 清算的維護畫面 同表 / OTAM901 / ATLAS.OTA 的同號 M / OFDB001 005 011 161 / 同樣跑不起來 ofdb 已寫
```

*圖:圖 5 跨模組影響面。橘框=本片的對外接點;橘虛框=要留意或本片對既有文件的修正;灰虛框=本片以外的模組;黑框=無原始碼。第④列是本篇對 ofdb.md 與 ofdb3.md 最直接的四處補強。*

### 8.1 本片對外最重要的一條線:境內一日作業的最後兩關

`OFDB303`(扣款行確認)→ `OFDB307`(過帳控制)→ `OFDB305`(申購日結轉)→ 帳務。

`OFDB305` 的 12 道卡控裡有 4 道在檢查**別的模組有沒有做完**:

| 卡控 | 檢查誰 | 屬於哪個模組 |
|---|---|---|
| 第 3 道 `CTL012` + `OFD0811A.APPOINT_SUB_YN` | 指定扣款設定 | OFD 的 M 片 |
| 第 8、9 道 `OFD221A.Status` / `OFD232A.Status` | 四眼覆核 | OFD 的 M 片 |
| 第 10 道 `OFD611A.ALLOT_CTL_CODE` | **電子交易拋轉** | EC(`ofdb3.md §6.3` 的 `OFDB605`) |
| 第 11 道 `OFD621A.EC_ALLOT_PCODE` | **電子交易轉入** | EC(`ofdb3.md §6.1` 的 `OFDB600`) |

**所以 EC 那條線沒跑完,境內申購日結轉就結不了帳。** `ofdb3.md §8.1` 描述的 `OFDB600` → `OFDB605` → 帳務,下游接口就是這裡。

### 8.2 本片寫入、別的模組讀取的表

| 表 | 本片誰寫 | 誰讀 |
|---|---|---|
| `OFD303A`(境內結帳控制) | `OFDB239` `OFDB241` `OFDB307` | OFD 全模組的日結轉與報表 |
| `OFD233A`(扣款行確認) | `OFDB303`(經 SP) | `OFDB305` 第 4 道卡控 |
| `OFD496A` / `OFD497A`(清算給付與退件) | `OFDB486A` `OFDB487A` `OFDB489A` `OFDB490A` `OFDB491A` | `ATLAS.OFD` 的 `OFDM482A` |
| `OFD494A` / `OFD495A`(清算主檔) | `OFDB481A` `OFDB486A` | `ATLAS.OFD` 的 `OFDM481A` |
| `OFD221` / `OFD252` / `OFD253`(境外交易明細) | 境外流水線 25 支 | `ATLAS.OTA` 的查詢與報表、`OFDB062` / `OFDB092` |
| `OFD302`(境外淨值) | **`OFDB052` / `OFDB082` 的「試算」會寫它** | 境外全流程 |
| `OFD281` / `OFD282` / `OFD283`(境外受益分配) | `OFDB131`–`OFDB135`、`OFDM252` | `OTAB901` 官網上傳的下游、`ATLAS.OTA` 報表 |
| `OFD220` / `OFD221`(境外申購) | **`OFDB135` 受益分配結帳會新增** | 境外申購流水線 |

### 8.3 本片讀取、別的模組維護的表

| 表 | 維護者 | 影響面 |
|---|---|---|
| `BMS001A` | BMS(`bms.md`) | `ATLAS.OTAB` 32 支裡 22 支 JOIN;`FREEZE_CD` 值域變動會讓 `OFDB305` 第 6 道失效 |
| `FSK003` | FSK | **`ATLAS.OTAB` 32 支裡 26 支 JOIN,本片對外相依最深的一張** |
| `OFD081A` / `OFD081V` | OFD 的 M 片(`ofd123.md`) | `DEC_LEN` 決定金額小數位;`FUND_SETUP_DATE` 決定 `OFDB305` 第 5 道走哪一支比較 |
| `OFD081` | OTA 的 M 片 | `API_URL` / `API_NAME` 空值 → `OTAB901` 拋 `UriFormatException` |
| `CTL014` | 共用代碼(`ofd4.md`) | `OFDB328` / `OFDB491A` |
| `CTL000` / `CTL012` | 共用控制 | `OFDB061` `OFDB062` `OFDB091` `OFDB092` / `OFDB305` |
| `COD006` / `COD006A` / `COD009` | COD(`cod.md`) | 唯讀 |
| `SDM010A` | SDM(`dsm.md` 相鄰) | `OFDB305` / `OFDB323` |
| `RSP072A` / `RSP003V` | RSP(`rsp.md`) | `OFDB311` / `OFDB057` |
| `LOG017A` | 法人公告歷史 | `OFDB305:98` / `OFDB323:102` |
| `OFD606A` / `OFD611` / `OFD620` / `OFD621` | EC(`ofdb3.md`) | `OFDB055` 的 EC 截止時間與拋轉檢核 |

### 8.4 共用 helper 與黑箱

| 物件 | 有原始碼嗎 | 本片怎麼用 |
|---|---|---|
| `BasicEVAPO` | 有(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs`) | 7 支繼承,`dbTA` 恆 null |
| `BaseEVADaoPO` | 有(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs`) | 38 支繼承 |
| `SQLHelper.EVAStringHelper` | 無原始碼,從呼叫端反推 | `GetParamValue` / `AddParam` 組查詢條件 |
| `CommonExceptionBlocker` | 無原始碼,從呼叫端反推 | **全片 58 支的 catch 唯一去處**;`HandleBusinessException(ex)` 之後就沒有下文 |
| `xTableHelper.GetTableSchema` | 無原始碼,從呼叫端反推 | `OTAB901_PO.cs:261` 用它判欄位型別 |
| `UIJsonHelper` | 無原始碼,從呼叫端反推 | `OTAB901p0` / `p1` 把 DataTable 轉 JSON |
| `m_OTABiz`(`GetFundBusinessDay` / `GetNav` / `GetNavLock`) | 無原始碼,從呼叫端反推 | `OFDB061` / `OFDB091` 的日期與淨值計算 |
| `ReportDocument` / `ReportParameterUtility` | 無原始碼(第三方 + 框架) | 9 支的報表 |
| `f_TA_GetEVAStatus` / `f_TA_GetBankHQ` / `f_TA_GetControlDate` / `f_TA_GetAgent` / `f_TA_StrToDate` / `f_TA_GetRemitFee` / `F_TA_SPLITWORDS` | **腳本不在 repo** | 見附錄 B |

### 8.5 改動影響面速查

| 你要改什麼 | 一定要一起看 |
|---|---|
| `OFD303A` / `OFD303` 加欄位 | 本片 26 支(`OFD303A` 11 支 + `OFD303` 15 支) |
| `OFD081` 的 `API_URL` / `API_NAME` | `OTAB901p0` `OTAB901p1`,以及官網那一端 |
| `FSK003` 主鍵 | `ATLAS.OTAB` 26 支 |
| `OFD221` / `OFD220` 的 NOT NULL 欄位 | 境外申購 12 支 **+ `OFDB135` 的 `INSERT`**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:419`、`:457`) |
| `OFD497A` 欄位 | `OFDB489A` `OFDB490A` `OFDB491A` 三支的 `INSERT` 欄位清單 |
| OTAB 的 7 支 SP 任一支 | 對應的 C# 呼叫端 + `DB/SP/` 腳本(這 7 支**在版控裡**,附錄 B.1) |
| OFDB 的 16 支 SP 任一支 | **腳本不在版控**,只能靠呼叫端參數反推(附錄 B.1) |
| `NFDR110` 報表 | `OFDB305` 與 `OFDB323` 兩邊 |
| `BasicEVAPO` 的 `dbTA` | 一旦補回連線,本片 7 支 + `ofdb.md` 的 4 支會**同時**從「必爆」變成「會跑但 SQL 是 T-SQL」 |

## 附錄 A. 資料表總表

### A.1 `ATLAS.OFDB`(境內)26 支動到的表

| 表 | 被幾支用 | 用途(推測) |
|---|---|---|
| `OFD303A` | 11 | 結帳控制 |
| `OFD081V` | 10 | 基金主檔檢視(小數位、簡稱、募集日) |
| `OFD220A` / `OFD221A` | 各 8 | 申購主檔 / 明細 |
| `OFD020V` | 6 | 銀行分行檢視 |
| `BMS001A` / `OFD081A` / `OFD496A` | 各 5 | 受益人 / 基金主檔 / 清算給付 |
| `BMS001` / `OFD081` / `OFD236` | 各 4 | (`BMS001` 與 `OFD081` 出現在跑不起來的那 7 支裡) |
| `OFD251A` / `OFD281A` / `OFD494A` / `OFD497A` | 各 3 | 買回 / 受益分配 / 清算 |
| `CTL014` `LOG017A` `OFD0811A` `OFD0819` `OFD233A` `OFD302A` `SDM010A` | 各 2 |  |
| `AA_REPORTMASTERSCHEMA` `COD006` `COD006A` `COD009` `CTL012` `FSK003` `MODB002AT1` `OFD002` `OFD019` `OFD020` `OFD020A` `OFD035A` `OFD038A` `OFD068A` `OFD070A` `OFD0813A` `OFD094A` `OFD095A` `OFD232A` `OFD237` `OFD252A` `OFD253A` `OFD254A` `OFD259A` `OFD264A` `OFD265A` `OFD266A` `OFD277A` `OFD283A` `OFD351A` `OFD429A` `OFD431A` `OFD432A` `OFD433A` `OFD437A` `OFD438A` `OFD495A` `OFD611A` `OFD612A` `OFD613A` `OFD621A` `OFD651A` `RSP072A` | 各 1 |  |

### A.2 `ATLAS.OTAB`(境外)32 支動到的表

| 表 | 被幾支用 | 用途(推測) |
|---|---|---|
| `OFD081` | 28 | 境外基金主檔 |
| `FSK003` | 26 | 通路 / 銷售機構 |
| `BMS001A` | 22 | 受益人主檔(**唯一帶 `A` 的共用表**) |
| `OFD302` | 19 | 境外淨值 |
| `OFD221` | 18 | 申購明細 |
| `OFD303` | 15 | 結帳控制 |
| `OFD252` / `OFD253` | 各 13 | 贖回明細 / 轉申購明細 |
| `OFD220` / `OFD251` | 各 10 | 申購主檔 / 贖回主檔 |
| `OFD256` / `OFD283` | 各 9 | 綜合帳戶彙總 / 受益分配明細 |
| `OFD254` `OFD281` `OFD282` | 各 6 | 付款明細 / 受益分配主檔 / 試算 |
| `OFD062` `OFD224` | 各 5 |  |
| `CTL000` | 4 |  |
| `OFD020V` `OFD192` `OFD309` `OFD311` `OFD533` `OFD613` `OFD620` `OFD621` `OFD651` `OFD652` `OFD653` `OFD221_TSCDLOG` | 各 2 |  |
| `COD006A` `OFD019A` `OFD086` `OFD088` `OFD231` `OFD300` `OFD551` `OFD552` `OFD562` `OFD606A` `OFD611` `OFD612` `OFD221_TSCDLOG1` `OFD252_TSCDLOG` `OFD252_TSCDLOG1` `OFD253_TSCDLOG` `OFD253_TSCDLOG1` `OFD283_TSCDLOG` `RSP003V` `OFDB065T1` | 各 1 |  |

### A.3 不是表的識別字(別拿去查索引)

| 識別字 | 真相 | 錨點 |
|---|---|---|
| `MYROW_DATA` | CTE | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB131_PO.cs:312` |
| `MYOFD253` / `MYCAL_DATA` / `MYCAL_DATE` / `MYOFD300` | CTE | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB088_PO.cs:445`、`:467` |
| `MYOMNIBUS_LIST` / `MYOFD221_P` / `MYOFD283` | CTE | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:246` |
| `dbo` | MSSQL schema 前綴(在註解裡) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:251` |
| `EVENTS` | `OFDB490A` SQL 字串裡的別名 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs` |
| `AA_REPORTMASTERSCHEMA` | 報表定義表,repo 內無定義 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB242_PO.cs` |

## 附錄 B. SP / Function / Trigger / View

### B.1 本片呼叫的 SP:23 支,repo 內腳本 7 支

| SP | 誰呼叫 | 腳本在 repo 嗎 |
|---|---|---|
| `S_OTA_OFDB061_EXE` | `OFDB061` | **在**(`DB/SP/S_OTA_OFDB061_EXE.sql`) |
| `S_OTA_OFDB062_EXE` | `OFDB062` | **在** |
| `S_OTA_OFDB065_EXE` | `OFDB065`、`OFDB135` | **在** |
| `S_OTA_OFDB091_EXE` | `OFDB091` | **在** |
| `S_OTA_OFDB092_EXE` | `OFDB092` | **在** |
| `S_OTA_OFDB131_EXE` | `OFDB131` | **在** |
| `S_OTA_OFDB135_EXE` | `OFDB135` | **在** |
| `S_OTA_OTAB901_Get` | `OTAB901` | 不在 |
| `s_INSERT_CALLAPI_HISTORY` | `OTAB901` | 不在 |
| `s_OFDB237_Get` | `OFDB237` | 不在 |
| `s_TA_OFDB289_Excute` | `OFDB289` | 不在 |
| `s_TA_OFDB290_Excute` | `OFDB290` | 不在 |
| `s_TA_OFDB303_Excute` | `OFDB303` | 不在 |
| `S_TA_OFDB305_CheckAgent` | `OFDB305` | 不在 |
| `s_TA_OFDB311_Execute` | `OFDB311` | 不在 |
| `S_TA_OFDB323_CheckAgent` | `OFDB323` | 不在 |
| `S_TA_OFDB285_EXCUTE_RPS` | `OFDB328`(報表段) | 不在 |
| `S_TA_OFDB328_EXCUTE_RPS` | `OFDB328` | 不在 |
| `s_TA_OFDB330_Get` | `OFDB330` | 不在 |
| `S_TA_OFDB351_EXECUTE` | `OFDB351`(執行與執行前檢查共用) | 不在 |
| `s_TA_OFDB432_Exe` | `OFDB432` | 不在 |
| `s_TA_OFDB434_Exe` | `OFDB434` | 不在 |
| `S_TA_OFDB481A_EXCUTE` | `OFDB481A` | 不在 |
| `S_TA_OFDB486A_EXCUTE` | `OFDB486A` | 不在 |
| `S_TA_OFDB487A_EXCUTE` | `OFDB487A` | 不在 |

(合計 25 條呼叫、23 支不重複 SP;`S_OTA_OFDB065_EXE` 被兩支呼叫、`S_TA_OFDB285_EXCUTE_RPS` 屬 `OFDB285` 家族但由 `OFDB328` 呼叫。)

**一條明顯的規律:`ATLAS.OTAB` 的 SP 全部在版控裡,`ATLAS.OFDB` 的一支都不在。** `ofdb3.md §B.1` 在 EC 那片是「26 支 SP,repo 內 0 支」。所以 OTAB 是目前唯一把 SP 進版控的專案。

### B.2 Function

| Function | 誰用 | 在 repo 嗎 |
|---|---|---|
| `f_TA_GetEVAStatus` | `OFDB303` `OFDB305` `OFDB323` | 不在 |
| `f_TA_GetBankHQ` | `OFDB303` `OFDB328` | 不在 |
| `f_TA_GetControlDate` | `OFDB303` | 不在 |
| `f_TA_StrToDate` | `OFDB305` `OFDB323` `OFDB491A` | 不在 |
| `f_TA_GetTradeDate` / `f_TA_GetReckonDate` | `OFDB305` `OFDB323` | 不在 |
| `f_TA_GetRemitFee` / `f_TA_GetRemitFeeByType` | `OFDB328` / `OFDB330` | 不在 |
| `f_TA_GetAgent` | `ATLAS.OTAB` 的申購與贖回流水線 17 支 | 不在 |
| `F_TA_SPLITWORDS` | `OTAB901_PO.cs:288`(`IN` 條件展開) | 不在 |
| `GET_FH_BF_NO` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:109` | 不在 |
| `dbo.f_IsPauseTrade` | `OFDB305`(**已註解**) | 不在,而且是 MSSQL 語法 |

### B.3 Trigger / View

- Trigger:本片一支都沒提到。

- View:`OFD081V`(境內基金主檔)、`OFD020V`(銀行分行)、`RSP003V`,三者定義都**不在版控**。

## 附錄 C. 代碼對照

| 欄位 | 值 | 意義 | 來源 |
|---|---|---|---|
| `OFD281.PROCESS_CODE` | `0` `1` `1A` `2` `3` `4` | 受益分配六階(§2.5) | Designer 標籤 |
| `OFD221.ALLOT_PROC_CODE` | `0` `1` `4` `5` `6` `9` `D` | 境外申購處理碼(§6.2.2) | 程式條件 |
| `OFD252.REDEM_PROC_CODE` | `0` `3` | 境外贖回處理碼(`'3'` = 已結轉) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:295`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB081_PO.cs:586` |
| `OFD221A.SUB_STATUS` | `0` `1` `2` `3` | 扣款結果(§2.5) | 程式訊息 |
| `OFD233A.BANK_CFM_CD` | `Y` / `N` | 扣款行確認 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:86` |
| `OFD303A.ALLOT_CTL_CODE` | `3` = 已結轉 | 申購結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:61` |
| `OFD303A.POST_CTL_CODE` | `Y` = 已過帳 | 過帳 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:59` |
| `OFD303A.REMIT_CTL_CODE` | `Y` / `N` | 匯款比對關帳 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:51-54` |
| `OFD303A.REMIT_CLS_CD` | `Y` = 本日須關帳 | 關帳開關 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:132` |
| `OFD303.REDEM_CTL_CODE` | `>= '2'` = 已下單確認 | 境外贖回控制 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:308` |
| `OFD496A.GET_STATUS` | `2` `4` `5` | 清算給付狀態(§2.5) | `OFDB489A` / `OFDB490A` |
| `OFD497A.Status` | `302` 寫死〔客戶特定〕 | 四眼狀態(假的) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:116`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:123` |
| `OFD220A.TRAN_PAY_WAY` | `1` = 匯款、`2` = 傳真委扣〔客戶特定〕 | 交易付款方式 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:229`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:89` |
| `OFD220A.SYSTEM_ID` | `0` = 非電子交易〔客戶特定〕 | 來源系統 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:91` |
| `OFD221A.ALLOT_CODE` | `1` = 一般申購、`2` = 轉申購、`3` = (排除) | 申購區分 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:228`、`:298` |
| `OFD221.ALLOT_TYPE` | `1` = 金額申購、`2` = 單位數申購 | 境外申購型態 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:106-107` |
| `OFD221.AGENT_ID` | `0` = 公司 | 通路別 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:112` |
| `OFD252.SOURCE_CD` | `2`〔客戶特定〕 | 贖回來源 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:307` |
| `OFD611A.ALLOT_CTL_CODE` | `<> '2'` = 未拋轉 | EC 拋轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:278` |
| `OFD621A.EC_ALLOT_PCODE` | `0` / `1` = 未轉入 | EC 轉入 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:285` |
| `BMS001A.FREEZE_CD` | `Y` = 註銷戶 | 受益人凍結 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:238` |
| `CTL014(953)` | API 路徑代碼〔客戶特定〕 | `OTAB901` 訊息裡提到 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:132` |

## 附錄 D. 掃描母體與逐支處置

**不用 `--module OFD` 覆蓋率**(那會拿全庫 551 支來比)。以下是本片自己的 58 支清單。

欄位說明:**處置** = 已寫(有獨立段落)/ 表格帶過;**觸發** = 全部「手動 · OneStep 執行鈕」; **Remoting** = 全部「無」;**csproj** = 全部「在(五層齊)」。

| # | 代號 | 專案 | 處置 | 寫在哪 |
|---|---|---|---|---|
| 1 | `OFDB221` | OFDB | 表格帶過 | §6.9 |
| 2 | `OFDB236` | OFDB | **已寫** | §0.2 一、§6.8、§6.9 |
| 3 | `OFDB237` | OFDB | **已寫** | §0.2 一、§6.8、§6.9 |
| 4 | `OFDB239` | OFDB | **已寫** | §6.8.4 |
| 5 | `OFDB240` | OFDB | 表格帶過 | §6.8、§6.9 |
| 6 | `OFDB241` | OFDB | **已寫** | §6.8.4 |
| 7 | `OFDB242` | OFDB | 表格帶過 | §6.8、§6.9 |
| 8 | `OFDB285` | OFDB | 表格帶過 | §6.9、§7 |
| 9 | `OFDB289` | OFDB | 表格帶過 | §6.9 |
| 10 | `OFDB290` | OFDB | 表格帶過 | §6.9 |
| 11 | `OFDB303` | OFDB | **已寫(深)** | §6.1 |
| 12 | `OFDB305` | OFDB | **已寫(深)** | §6.7 |
| 13 | `OFDB307` | OFDB | 表格帶過 | §0.2 一、§6.9 |
| 14 | `OFDB311` | OFDB | 表格帶過 | §6.9 |
| 15 | `OFDB323` | OFDB | **已寫** | §6.7 |
| 16 | `OFDB328` | OFDB | **已寫** | §6.9 |
| 17 | `OFDB330` | OFDB | **已寫** | §6.8.3 |
| 18 | `OFDB351` | OFDB | 表格帶過 | §6.9 |
| 19 | `OFDB432` | OFDB | **已寫** | §6.8.5 |
| 20 | `OFDB434` | OFDB | **已寫** | §6.8.5 |
| 21 | `OFDB481A` | OFDB | **已寫(深)** | §6.4 |
| 22 | `OFDB486A` | OFDB | **已寫(深)** | §6.4 |
| 23 | `OFDB487A` | OFDB | **已寫(深)** | §6.4 |
| 24 | `OFDB489A` | OFDB | **已寫(深)** | §6.4 |
| 25 | `OFDB490A` | OFDB | **已寫(深)** | §6.4 |
| 26 | `OFDB491A` | OFDB | **已寫(深)** | §6.4 |
| 27 | `OFDB051` | OTAB | **已寫(深)** | §6.2 |
| 28 | `OFDB052` | OTAB | 表格帶過 | §6.2.1、§6.9 |
| 29 | `OFDB053` | OTAB | 表格帶過 | §6.2.1 |
| 30 | `OFDB054` | OTAB | 表格帶過 | §6.2.1 |
| 31 | `OFDB055` | OTAB | 表格帶過 | §6.2.1、§2.2 |
| 32 | `OFDB057` | OTAB | 表格帶過 | §6.2.1、§6.2.4 |
| 33 | `OFDB058` | OTAB | 表格帶過 | §6.2.1 |
| 34 | `OFDB060` | OTAB | 表格帶過 | §6.2.1 |
| 35 | `OFDB061` | OTAB | **已寫(深)** | §6.3 |
| 36 | `OFDB062` | OTAB | 表格帶過 | §5、§6.9 |
| 37 | `OFDB064` | OTAB | 表格帶過 | §6.2.1、§6.9 |
| 38 | `OFDB065` | OTAB | 表格帶過 | §6.2.1、§6.9 |
| 39 | `OFDB081` | OTAB | 表格帶過 | §6.2.1、§6.2.4 |
| 40 | `OFDB082` | OTAB | 表格帶過 | §6.2.1、§6.9 |
| 41 | `OFDB083` | OTAB | 表格帶過 | §6.2.1 |
| 42 | `OFDB084` | OTAB | 表格帶過 | §6.2.1、§6.3.2 |
| 43 | `OFDB085` | OTAB | 表格帶過 | §6.2.1 |
| 44 | `OFDB086` | OTAB | 表格帶過 | §6.2.1 |
| 45 | `OFDB087` | OTAB | 表格帶過 | §5、§6.9 |
| 46 | `OFDB088` | OTAB | 表格帶過 | §6.2.1 |
| 47 | `OFDB089` | OTAB | **已寫(深)** | §6.5 |
| 48 | `OFDB090` | OTAB | 表格帶過 | §6.2.1 |
| 49 | `OFDB091` | OTAB | **已寫** | §6.3 |
| 50 | `OFDB092` | OTAB | 表格帶過 | §5、§6.9 |
| 51 | `OFDB094` | OTAB | 表格帶過 | §6.2.1、§6.9 |
| 52 | `OFDB131` | OTAB | 表格帶過 | §6.2.5 |
| 53 | `OFDB132` | OTAB | 表格帶過 | §6.2.5 |
| 54 | `OFDB133` | OTAB | 表格帶過 | §6.2.5 |
| 55 | `OFDB134` | OTAB | 表格帶過 | §6.2.5 |
| 56 | `OFDB135` | OTAB | **已寫(深)** | §6.2.5 |
| 57 | `OFDM252` | OTAB | **已寫(深)** | §4.1 |
| 58 | `OTAB901` | OTAB | **已寫(深)** | §6.6 |

**深寫 18 支、表格帶過 40 支,58 支全部有處置。**

### D.1 相鄰但不在本片的

| 東西 | 為什麼相鄰 |
|---|---|
| `OFDB562` / `OFDB563` / `OFDB564` | **兩個專案各一份**,`ofdb3.md §2.5` 已寫 |
| `OFDB553` `OFDB561` `OFDB600A` `OFDB601A` `OFDB602A` `OFDB603` `OFDB604A` | 同在 `ATLAS.OTAB`,`ofdb3.md` 已寫 |
| `OFDB903` | 同在 `ATLAS.OTAB` 的 PO 資料夾,**不在本片名單**,未查 |
| `OFDB001` `OFDB005` `OFDB011` `OFDB161` | 同樣是 `BasicEVAPO` 跑不起來,`ofdb.md §6.5` 已寫 |
| `OFDM481A` / `OFDM482A` / `OFDM485` | `ATLAS.OFD` 的清算維護畫面,與本片 D 群同表 |
| `OTAM901` | `ATLAS.OTA` 的同號 M 畫面,未查 |

### D.2 怎麼自己查

```
py -V:3.12 /docs/tools/atlas_scan.py --screen OFDB303
```

記得三件事:

1. **主檔欄幾乎一定是空的**,那是批次的通例(§2.1),不要當成索引壞掉。

2. **`atlas_scan --table` 反查不到本片 57 支**,要用全文搜尋。

3. **搜到 `OFDB305_PO.cs` / `OFDB323_PO.cs` 會有兩份**,只有 `PO/PO.OFDB/` 那份是活的(§0.2 三)。

## 附錄 E. 讀本文時要注意的地方

嚴重度:**高** = 會造成錯帳 / 資料遺失 / 卡控失效;**中** = 誤導或功能不彰;**低** = 維護困擾。

### E.1 整支跑不起來

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | **7 支 `BasicEVAPO` 的 `dbTA` 恆 null** | `OFDB236` `OFDB237` `OFDB239` `OFDB240` `OFDB241` `OFDB242` `OFDB307` 按執行必 `NullReferenceException` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`:165-173`;用法 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:38` | **高** |
| E1.2 | **`OFDB330` 的日期合理性檢核整個方法是死的** | T-SQL 語法 + 三個 `AddInParameter` 全被註解 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:571`、`:575-578` | **高** |

### E.2 卡控失效

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | **`REMIT_FAIL_CODE=''` 在 Oracle 恆 UNKNOWN** | `OFDB305` 第 5 道「淨值不同」只擋傳真委扣,匯款件完全不擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:229` | **高** |
| E2.2 | **50 個 `bool` 卡控方法 fail-open** | DB 出錯 → 一律放行 → 結帳在沒把關的狀態下完成 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:984-987`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:343-346` | **高** |
| E2.3 | **Oracle 三值邏輯 `欄 <> '值'` 遇 NULL** | 106 處。`OFDB061` 的淨值一致性檢核漏掉 NULL 列 → 淨值不同也能結帳 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:961-964` | **高** |
| E2.4 | **「受益人暫停申購」自 2009 年被 `/* */` 註解** | 暫停申購的受益人不擋申購日結轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB305_PO.cs:245-260` | 中 |
| E2.5 | **`OFDB307` 的 `OR (… AND 1=1)`** | 該分支無條件成立,等於沒有第二個條件 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB307_PO.cs:79` | 中 |

### E.3 一律回成功

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | **`ExecuteNonQuery` 回傳值被 `i = 1;` 蓋掉,共 12 處** | 清算六支的 rollback 分支是死碼,任何情況都 Commit 都回成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB486A_PO.cs:131-145`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:87-89`、`:136-145` | **高** |
| E3.2 | **`OFDB303` 的成功訊息筆數寫死 `1`,而且 `ExecuteNonQuery` 回傳值沒接** | SP 一列沒改也說成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:193`、`:196` | **高** |
| E3.3 | **`OFDB089` 六段 `DELETE` 的影響列數全部沒檢查** | 刪 0 列與刪 5,000 列訊息相同 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:139`、`:162`、`:183`、`:204`、`:225`、`:256`、`:269` | 中 |

### E.4 資料遺失

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E4.1 | **`OFDM252` 把 `ROW_STATE` 改寫成 `"Deleted"`** | 使用者「修改」一列,若 `OFD282` 沒有對應列,該列被刪 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:388-393` | **高** |
| E4.2 | **`OFDM252` 無條件把 `OFD282.CFM_YN` 設 `'Y'`** | 連使用者要刪的列也標成已確認 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:352-394` | 中 |
| E4.3 | **`OFDB089` 第六段 `DELETE OFD256` 的範圍靠 `NVL` 撐** | 基金代碼留空 = 刪整家境外基金公司當日彙總,畫面沒提示 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:232-243` | 中 |
| E4.4 | **`OFDB135` 取消結帳會 `DELETE OFD220` / `DELETE OFD221`** | 刪的是交易主檔不是中間表 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:738`、`:764` | 中 |

### E.5 繞過四眼 / 假四眼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | **`OFDB489A` / `OFDB490A` 的 `INSERT OFD497A` 把 `Verify` / `Approve` / `Reject` 三組四眼欄填成同一人同一秒,`Status` 寫死 `'302'`** | `OFD497A` 的覆核軌跡是假的 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:100-119`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs:107-125` | **高** |
| E5.2 | **`OFDM252` 直接 `INSERT`/`UPDATE`/`DELETE` `OFD283`,完全沒有覆核階段** | 改配息金額不需第二個人 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDM252_PO.cs:397-477`、`:523-537` | **高** |

### E.6 交易與 rollback 的破口

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | **`catch` 第一行就 `tran.Rollback()`** | `BeginTransaction()` 自己失敗時 `tran` 是 null,catch 內再拋 NRE,原始錯誤被吃掉。全片 58 支的樣板都這樣 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:199-212` | 中 |
| E6.2 | **`OFDB489A` rollback 後不 `return` 也不 `break`** | 迴圈繼續對已 rollback 的交易下語句 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:139-146` | 中 |
| E6.3 | **`OFDB089` 提早 `return` 時沒有 `Rollback`,只靠 `finally` 的 `Dispose`** | 那兩條路徑沒寫資料,實務無害,但形態危險 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:110`、`:266`、`:280-284` | 低 |
| E6.4 | **`OTAB901` 開 `m_db` 的交易,`finally` 卻 `Dispose` 基底的 `dbProduct`** | `m_db` 的連線不會被釋放 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:86`+`:111-115` | 中 |
| E6.5 | **`OTAB901` 三處 `BeginTransaction()` 寫在 `try` 外** | 取不到連線時例外不被自己的 catch 接到 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:86`、`:129` | 中 |
| E6.6 | **檢核方法的讀取有的傳 `tran` 有的不傳** | 檢核看到的資料與執行時改的資料不在同一快照 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:977`(不傳)vs `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB089_PO.cs:334`(傳) | 中 |

### E.7 例外被吞

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E7.1 | **全片 58 支 PO 的 `throw` 出現次數合計 0** | 所有錯誤只變成畫面一行字,上層拿不到型別 | 全片 | 中 |
| E7.2 | **88 處 `AddResultRow(false, 0, "")`(19 支)** | 使用者只看到「失敗」沒有原因 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB330_PO.cs:445`、`:452`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB351_PO.cs:91`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB486A_PO.cs:138`、`:150` | 中 |
| E7.3 | **`OFDB303` 的訊息被砍成半句**:`"執行失敗,請檢查 : "` | 冒號後面空的 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB303_PO.cs:210` | 低 |
| E7.4 | **`OTAB901.InsAPILog` 的失敗訊息寫成「取得境外基金主檔(OFD081)失敗」** | 複製貼上沒改,誤導 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OTAB901_PO.cs:108` | 中 |
| E7.5 | **`OTAB901` 的 `Console.WriteLine`** | WinForms 沒有主控台,等於丟掉 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:142-143` | 低 |

### E.8 安全

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | **TLS 憑證驗證被整個行程關掉** | 按下 `OTAB901` 上傳鈕之後,主程式所有 HTTPS 都不驗憑證 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:161` | **高** |
| E8.2 | **把所有 `SecurityProtocolType` 相加,連 SSL3 / TLS1.0 一起啟用** | 同上,process 層級 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:34-40` | **高** |
| E8.3 | **`App.config` 明文連線字串(含帳密)** | 只記位置不抄值 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:9-11` | **高** |
| E8.4 | **字串串接進 SQL** | `OFDB236` 把 `FUND_ID` 與兩個日期直接拼進 SQL;`OFDB237` 把 `FUND_ID` 拼進 SQL | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB236_PO.cs:146`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB237_PO.cs:74` | **高**(目前被 E1.1 遮蔽) |

### E.9 誤導與失去資訊

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E9.1 | **`OFDB285` 畫面有「信件主旨 / 信件內容」欄位,但整片 58 支沒有任何寄信程式碼** | 使用者填了以為會寄 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB285.Designer.cs:481`、`:522` | 中 |
| E9.2 | **`OTAB901` 失敗不寫 API log** | 事後查不到有沒有送出去 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:171-189` | **高** |
| E9.3 | **`OTAB901` 的「API Path 未設定」檢核永遠到不了** | `new Uri()` 先拋例外,而且不在 try 裡 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs:126` vs `:130-134` vs `:156` | 中 |
| E9.4 | **`OFDB328` 報表段沒勾檔案時靜默結束** | 按執行沒反應 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1129` | 低 |
| E9.5 | **`OFDB061` 在日期為空時仍把空字串塞進訊息** | 「申購淨值日期,無結帳控制日期檔資料」 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB061.cs:199-206` | 低 |
| E9.6 | **`OTAB901.DoExp1` 沒有 try** | 上傳基本資料拋例外會彈未處理例外對話框(`DoExp2` 有 try) | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901.cs:116-124` vs `:128-146` | 中 |

### E.10 寫死常數與寫死字串

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E10.1 | **`OFDB328` 用 `FILE_ID.IndexOf("DR") == 0` 決定走哪一支 SP** | 新增 `DR` 開頭的檔案編號會被當成受益分配 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1132` | 中 |
| E10.2 | **`OFDB236` 預設目錄寫死 `c:\`** | 〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB236.cs:238` | 低 |
| E10.3 | **`OFD497A.Status` 寫死 `'302'`、`RejectDate` 寫死 `1900/01/01`** | 見 E5.1 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs:116`、`:119` | 中 |
| E10.4 | **`OFDB351` 兩個方法都把 `iCHECK_TYPE` 寫死 `"Y"`** | 參數形同虛設 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB351_PO.cs:60`、`:125` | 低 |
| E10.5 | **`OFDB328` 的 `bool.Parse(參數)`** | 參數不是 `True`/`False` 會拋 `FormatException` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1170` | 低 |

### E.11 成對批次只改一邊

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E11.1 | **`OFDB239` 的 UPDATE 有 `REMIT_CLS_CD='Y'` 守衛,`OFDB241` 沒有** | 「本日不須關帳」的基金關不了帳卻可以被取消關帳 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB239_PO.cs:51-54` vs `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB241_PO.cs:51-52` | 中(兩支目前都跑不起來) |
| E11.2 | **`OTAB901p0` / `OTAB901p1` 相似度 92.3%** | 改一邊必須改另一邊,E8.1 / E8.2 / E9.2 三個問題兩份都有 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p0.cs`、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OTAB901p1.cs` | 中 |
| E11.3 | **`OFDB489A` / `OFDB490A` 相似度 64.4%** | 退匯 / 退郵的 `i = 1;` 與假四眼兩份都有 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB489A_PO.cs`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB490A_PO.cs` | 中 |

### E.12 維護陷阱

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12.1 | **`OFDB305_PO.cs` / `OFDB323_PO.cs` 各有一份過期副本在 UI 資料夾,不在 csproj** | 全文搜尋出現兩份,行號差 1~2,改錯邊不會編譯錯 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB305_PO.cs`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB323_PO.cs` | 中 |
| E12.2 | **9 個 `.cs` 是 cp950 不是 UTF-8** | `OFDB289` 三層、`OFDB305` 四份、`OFDB323` 兩層;同一支畫面不同層編碼不同 | §3.6 | 中 |
| E12.3 | **`ATLAS.OTAB` 的資料夾叫 `PO.OTA` / `UI.OTA`,但組件與 namespace 是 `OTAB`** | 用資料夾名 grep 會混到 `ATLAS.OTA` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/PO.OTAB.csproj` | 低 |
| E12.4 | **`SET COL = ''` 在 Oracle 寫入的是 NULL** | 「回復」之後 `CFM_ORDER_*` 是 NULL,下游用 `= ''` 比不到 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB051_PO.cs:383-385`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB081_PO.cs:587-592` | 中 |
| E12.5 | **`OFDB432` / `OFDB434` 還留著沒用到的 `using System.Data.SqlClient;`** | 遷移殘跡,不影響執行但誤導 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB432_PO.cs:11` 一帶 | 低 |
| E12.6 | **`OFDB328` 有一整段「已停用」的 ACH 付款檢核** | 是真的 `//` 註解 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB328_PO.cs:1398` | 低 |

### E.13 看起來像 bug,其實不是

| 現象 | 為什麼不是 bug |
|---|---|
| `OFDB305.cs:71` / `OFDB323.cs:69` / `OFDB489A.cs:63` 的 `Select("Status_DESCRP<>''")` | 這是 **ADO.NET `DataTable.Select` 的運算式語法**,不是 SQL。在 .NET 裡 `''` 就是空字串,寫法正確 |
| `OFDB242_PO.cs:253` 的 `#region OLD` | 裡面每一行都是真的 `//` 註解,**不是 `ofdb3.md` 那種假註解** |
| `OFDB289.cs:315` 的 `#region old` | 用 `/* */` 包住,真註解 |
| 57 支的主檔欄是空的 | 批次的通例(§2.1) |
| `OFDB303_PO.cs:180` 被註解的 `DbCommand Cmd;// = …` | 那一句搬進迴圈了(`:185`),不是漏掉 |
| `OFDB351` 的 `BeginTransaction` 出現兩次但 `Commit` 只有一次 | 「執行前檢查」那個方法本來就一律 rollback(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB351_PO.cs:108-160`),設計如此 |
| `OFDB285` / `OFDB289` / `OFDB328` 完全不開交易 | 三支只讀資料、寫本機檔案,沒有寫 DB |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `ATLAS.OFDB` 26 支 + `ATLAS.OTAB` 32 支,共 58 支 |

由 build_doc.py v2.0.0 於 2026-09-15 19:56 產生 · 標題 122 · 圖 5 · 表格 91 · 程式錨點 372 · § 連結 135 · 引用檢查：畫面 88（缺 0） · Table 18（缺 0） · Report 11（缺 0） · 結果集 12（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
