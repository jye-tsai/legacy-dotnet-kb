<!-- 由 tools/build_copilot_kb.py 從 modules/ofdb.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFDB 模組(OFD 批次片)全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:只涵蓋 `Dev/ATLAS.OFDB` 專案裡的 **18 支 B 批次畫面**(見 §3)。OFD 前綴全庫 550 支,本篇是其中一片;`OFDB050` / `OFDB284` / `OFDB701` 等其餘支不在本篇。 **建議讀法**:趕時間只讀三段 —— **§6.1 `OFDB003`(本篇頭號重點,BMS 模組整套變更單的生效引擎)**、§0.2(這 18 支分成三個世代,其中一整組是未移轉的 SQL Server 死碼)、附錄 E(踩雷)。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、Designer 內的中文標籤字串、SQL 註解與訊息字串**推測**。ATLAS 沒有把畫面中文名放進版控,本片 18 支沒有任何一支有 `this.Text`。⚠ **〔客戶特定〕**:機構代碼 `A0901`(股務代理)/ `OP101`、CRS 公司識別碼 `TW-86385617`、`SEND_TYPE` 代碼 `4` / `11`、寫死年度 `'2019'`、外部檔案副檔名 `.mon` / `.101` / `.xml`、LDAP API 端點為本站台的值。⚠ **〔共用〕**:`BMS001ACHG` 由 BMS 開單、本片 `OFDB003` 生效;`OFD081A` / `OFD303A` / `OFD085A` / `OFD283A` 同時服務 OFD 其他片與 RSP / DSM(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、資料存取看 `architecture.md §4`、畫面型別看 `architecture.md §6`、WindowsService 看 `architecture.md §8.4`、SP 覆蓋率看 `architecture.md 附錄 B`。**不要整份讀**。`CHG` 配對表機制看 `bms.md §2`,本篇 §6.1 直接接在它後面,不重述證據鏈。

## 0. 系統邊界與角色

### 0.1 這 18 支批次管什麼(推測)

**一句話:這 18 支不是一條流程,是「OFD 前綴底下、被丟進 `ATLAS.OFDB` 專案的批次雜燴」—— 唯一的共同點是型別(B)與專案位置,業務上至少分成七群互不相干的事。**

| 群 | 管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| **A 受益人資料生效** | BMS 開的「受益人資料變更申請單」到期後整批回寫本表、同步外部 LDAP | **`OFDB003`**、`OFDB005` | `BMS001ACHG`、`OFD195`、`CTL016` |
| **B 基金主檔衍生設定** | 新基金上線時把既有基金的 16 張設定表整包複製過去;基金鎖定 / 淨值鎖定 | **`OFDB004`**、`OFDB040`、`OFDB041` | `OFD081A` 與 16 張明細、`FND001`、`OFD302A` |
| **C 收益分配(配息)** | 產生配息受益人清冊 → 退匯 → 重匯 | **`OFDB281`**、`OFDB286`、`OFDB287` | `OFD281A` / `OFD287A` / `OFD283A` / `OFD292A` |
| **D 帳務關卡** | 逐基金逐銷售機構的申購 / 贖回關帳與取消關帳 | `OFDB222` | `CTL022`、`OFD303A` |
| **E 法遵申報** | CRS(共同申報準則)資料產出與 XML 下載 | **`OFDB019A`**、**`OFDB019B`** | `CRSP001` ~ `CRSP006` |
| **F 對外申報 / 憑證 / 列印** | 主管機關申報檔、總額憑證、資料索取信封與地址條、受益人名條 | `OFDB001`、`OFDB002`、`OFDB007`、`OFDB008`、`OFDB011` | `OFD312`、`OFD297A`、`OFD342`、`BMS001A` |
| **G 定期買回 / 銷售機構換號** | 定期買回處理;銷售機構代碼整批置換 | `OFDB161`、`OFDB223` | `OFD163` / `OFD165` / `OFD166`、七張交易表 |

「OFDB」不是模組,是 **`OFD` 模組 + 型別 `B`** 的字面拼接(`architecture.md §2.1` 的三段結構)。repo 裡沒有任何地方把 OFDB 定義成一個業務單位;`Dev/ATLAS.OFDB/Source/Vendor.ATLAS.OFDB.sln` 只是把 OFD 的批次層抽成一個 sln。所以本篇標題寫「OFD 模組批次片」,不寫「OFDB 模組」。

### 0.2 最反直覺的四件事

**一、四支畫面的 PO 是未移轉的 SQL Server 程式碼,在 Oracle 上不可能跑起來。**

`OFDB001` / `OFDB005` / `OFDB011` / `OFDB161` 這四支的 PO 全部繼承舊世代的 `BasicEVAPO`,而且整支用 T-SQL 語法與 `SqlDbType`:

| 證據 | 錨點 |
|---|---|
| `EXEC s_OFDB001_Excute @striFUND_ID=@xstriFUND_ID,...` —— Oracle 沒有 `EXEC ... @x=@y` 這種語法 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:41` |
| 參數一律 `@` 前綴 + `SqlDbType`(Oracle 走 `:` 與 `OracleDbType`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:44-47`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:49-50`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:58-70` |
| `SELECT TOP 1` / `ISNULL()` / `[OFD342]` 中括號識別字 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:174`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:179`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:65` |
| 全片統計:這四支 `SqlDbType` 出現 9 / 2 / 30 / 7 次、`OracleDbType` **0 次**;其餘 14 支剛好相反(0 次 / 2~53 次) | 見 §0.3 |

**更致命的是連線物件本身是 null。** `BasicEVAPO` 宣告 `protected Database dbTA = null;` (`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`),而建構子裡唯一會賦值的兩行**被註解掉**(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:169-172`)。這四支 PO 的原始碼裡**沒有任何一行**給 `dbTA` 或 `dbPTPF` 賦值。所以 `dbTA.CreateConnection()`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:33`)一執行就是 `NullReferenceException`。

它們仍然被編譯進組件(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:130`、`:135`、`:138`、`:144`),Ctl 也還在 `new` 它們(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB001_Ctl.cs:43`)。 **結論(假設,依據是上述三條交叉)**:這四支是 SQL Server 時代的遺留,遷 Oracle 時被跳過,現況等同死碼; 畫面還在,按下去會拿到 `ExceptionMessage.ServerSideError`。要用得先整支重寫。

**二、`OFDB003` 不是「OFD 自己的批次」,它是 BMS 整個模組的生效引擎。** `bms.md §2` 已經證明:BMS 的 12 張 `CHG` 配對表,覆核通過之後資料**仍然沒有進本表**,要等 `OFDB003` 跑,由 SP `s_TA_OFDB003_Excute` 回寫並蓋 `CHG_UPD_DTTM`。本篇 §6.1 把呼叫端能確定的事全部攤開,並明確標出哪些只能是假設。

**三、這 18 支沒有任何一支是排程,全部要人按按鈕。** 18 支的 UI 全部繼承 `xOneStepProcessForm`(`architecture.md §6.4`),`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:15` 是代表。`architecture.md §8.4` 列的四支 WindowsService(`OFDB600` / `OFDB609` / `OFDB680` / `RSPB008`) **一支都不在本片**(前三支住 `Dev/ATLAS.EC/`,`RSPB008` 住 `Dev/ATLAS.RSP/`), `Dev/ATLAS.OFDB/` 底下也沒有 `WindowsService.*` 資料夾。唯一像排程的東西是 `CTL016` 裡的「處理時間」欄位,但它只被讀出來顯示,不觸發任何東西(見 §6.1)。

**四、12 支畫面的 PO 完全不宣告主明細,而且理由分成三種,不是同一種寫法。** 裸 DAO、EVA 基底但不填 `xTableMapping`、以及舊世代基底。§0.3 拆開。

### 0.3 三個世代、四種資料存取路徑

| 世代 | PO 基底 | 連線 | 有沒有宣告 `xTableMapping` | 畫面 | SQL 方言 |
|---|---|---|---|---|---|
| **新世代 A:EVA 滿血** | `BaseEVADaoPO` | 基底管(部分再自建一個 `dbTA`) | **有主明細** | `OFDB002`、`OFDB004`、`OFDB281` | Oracle |
| **新世代 B:EVA 空殼** | `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` | 同上 | **不宣告**(或只宣告主檔,不走 `Add`) | `OFDB019A`、`OFDB019B`、`OFDB041`、`OFDB286`、`OFDB287` | Oracle |
| **新世代 C:裸 DAO** | **無基底** | 自己 `new Database("TA", DbServerType.Oracle)` | 無 | `OFDB003`、`OFDB007`、`OFDB008`、`OFDB040`、`OFDB222`、`OFDB223` | Oracle |
| **舊世代:`BasicEVAPO`** | `BasicEVAPO` | **`dbTA` 恆為 null** | `TableMapping`(舊型別) | `OFDB001`、`OFDB005`、`OFDB011`、`OFDB161` | **SQL Server(未移轉)** |

逐支錨點:

| 畫面 | PO 類別宣告 | 錨點 |
|---|---|---|
| `OFDB001` | `: BasicEVAPO`,主檔 `OFD312` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:14-19` |
| `OFDB002` | `: BaseEVADaoPO, IOFDB002_PO`,主檔 `OFD081A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:31-36` |
| `OFDB003` | `: IOFDB003_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:32-36` |
| `OFDB004` | `: BaseEVADaoPO, IOFDB004_PO`,主檔 `OFD081A` + 16 張明細 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:36`、`:54-77` |
| `OFDB005` | `: BasicEVAPO`,主檔 `OFD195` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:15-20` |
| `OFDB007` | `: IOFDB007_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB007_PO.cs:21-24` |
| `OFDB008` | `: IOFDB008_PO`(裸,**兩個** `Database`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:31-34` |
| `OFDB011` | `: BasicEVAPO`,主檔 `OFD342` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:15-20` |
| `OFDB019A` | `: BaseEVADaoPO, IOFDB019A_PO`,建構子是空的 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:32-38` |
| `OFDB019B` | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:32` |
| `OFDB040` | `: IOFDB040_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:34-36` |
| `OFDB041` | `: BaseMultiRowEVADaoPO, IOFDB041_PO`,主檔 `OFD302A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:27`、`:32-33` |
| `OFDB161` | `: BasicEVAPO`,**連 `MasterTable` 都不宣告** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:17-25` |
| `OFDB222` | `: IOFDB222_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:34-36` |
| `OFDB223` | `: IOFDB223_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:33-35` |
| `OFDB281` | `: BaseEVADaoPO, IOFDB281_PO`,主 `OFD281A` 明細 `OFD287A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:32`、`:41`、`:46` |
| `OFDB286` | `: BaseEVADaoPO, IOFDB286_PO`,建構子不宣告任何表 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:25-31` |
| `OFDB287` | `: BaseEVADaoPO, IOFDB287_PO`,同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:30-36` |

> **對「12 支沒宣告主明細」的正式回答**:掃描器說缺,分成三類,**沒有一類是真的少一層** ——18 支的六層檔案全部齊全(見 §3.3)。(1)**裸 DAO 6 支**(`OFDB003` `OFDB007` `OFDB008` `OFDB040` `OFDB222` `OFDB223`)——完全繞過 `BaseEVADaoPO`,自己 `new Database("TA", DbServerType.Oracle)` 開連線、自己管交易,正是 `architecture.md §6.3` 與 `architecture.md §6.4` 講的 I/B 型樣板。沒有四眼、沒有 `xTableMapping`,因為它們的輸出是 DB 狀態改變或外部檔案,不是回傳資料集。(2)**EVA 空殼 5 支**(`OFDB019A` `OFDB019B` `OFDB041` `OFDB286` `OFDB287`)——掛了 `BaseEVADaoPO` 卻不填 `MasterTable`,純粹為了借 `dbProduct` / `dbPTPF` 兩個連線與`SetSecurityData` 這類 helper;真正的寫入是自己組的 `UPDATE` / `INSERT` 或 SP。`OFDB041` 是唯一有填主檔的(`OFD302A`),它的 `Execute` 直接轉呼叫 `base.Update`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:61-72`)。(3)**舊世代 1 支**(`OFDB161`)—— 連 `MasterTable` 都沒有,而且 `dbTA` 是 null,見上面第一件事。

### 0.4 不管什麼

| 不管 | 誰在管 |
|---|---|
| 受益人資料變更的**開單與四眼** | BMS 的 `BMSM004` / `BMSM006`(`bms.md §4`);`OFDB003` 只負責到期生效 |
| 基金主檔本身的建檔與覆核 | OFD 的 M 片(不在本篇);`OFDB004` 只複製衍生設定,而且要求來源與目的基金都已覆核 |
| 收益分配的**結算確認** | `OFDB284`(不在本篇);`OFDB281` 一看到 `PROCESS_CODE = '4'` 就整個擋掉 |
| 淨值本身怎麼算出來 | OFD 其他片;`OFDB041` 只切 `NAV_LOCK` 旗標 |
| CRS 的受益人自我證明原始資料 | BMS 的 `BMSM925` / `BMSM926` / `BMSM927`(`bms.md §4`);`OFDB019A` 只把它們彙總成申報檔 |
| 真正的 LDAP 帳號系統 | 外部 API,經 `LDAPAPIHelper`(無原始碼,從呼叫端反推) |
| 郵件寄送 | `GenXMLHelper`(無原始碼,從呼叫端反推),批次只組資料 |
| 所有 SP 的內部邏輯 | Oracle 端。本片呼叫 21 支 SP,**repo 內一支腳本都沒有**(見附錄 B) |

### 0.5 使用角色(推測)

本片 18 支**沒有任何一支做角色 / 權限檢查**。全片 grep `MGM_CD` / `MANGR_CODE` 這類權限旗標:0 命中。唯一跟人有關的是把 `PermissionInfo[0].UserID` 塞進 SP 參數或 `UpdateID` 欄位(例 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:78`)。

| 角色(推測) | 依據 | 用哪些畫面 |
|---|---|---|
| 受益人資料維護人員 | `OFDB003` 訊息「共變更 N 筆受益人資料」 | `OFDB003`、`OFDB005`、`OFDB007` |
| 基金設定人員 | `OFDB004` 畫面上列出 13 支要接手覆核的 `OFDM*` 畫面(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:93-108`) | `OFDB004`、`OFDB040`、`OFDB041` |
| 帳務人員 | `OFDB222` 的「關帳 / 取消關帳」 | `OFDB222`、`OFDB001` |
| 配息作業人員 | `OFDB281` 訊息提到要先跑 `OFDR287` 確認配息帳號 | `OFDB281`、`OFDB286`、`OFDB287` |
| 法遵 / 申報人員 | CRS 與主管機關申報檔 | `OFDB019A`、`OFDB019B`、`OFDB008`、`OFDB002` |
| 客服 / 文件人員 | 名條、地址條、信封 | `OFDB007`、`OFDB011` |

**畫面層級的存取控制交給框架的選單與 `UseCaseSecurity`(無原始碼,從呼叫端反推),不在本片程式內。**

### 0.6 全域開關

| 開關 | 位置 | 效果 | 錨點 |
|---|---|---|---|
| `CTL016.BF_PROC_TIME` | `CTL016` 單列設定 | 受益人變更生效批次的「應執行時間」,**只讀出來顯示,不觸發任何排程** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:363-365` |
| `CTL016.REL_PROC_TIME` | 同上 | `OFDB005` 的對應時間欄,一樣只顯示 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:174-176` |
| `OFD163.PERIOD_REDEM_PROCESS_TIME` | `OFD163` | 定期買回處理時間,同樣只顯示 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:122` |
| `OFD681.SEND_TYPE` / `OFD681A.SEND_TYPE` | 通知信收件名單 | 分類碼:`'4'` 給 `OFDB003`、`'11'` 給 `OFDB161`〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:408`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:170` |
| `OFD303A.POST_CTL_CODE` | 基金過帳控制檔 | `'Y'` = 已過帳。`OFDB281` / `OFDB041` / `OFDB001` 都拿它當前置條件 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:80` |
| `OFD081A.FUND_LOCK` + `FND001.FUND_LOCK` | 基金主檔 | 基金鎖定旗標,`OFDB040` 是唯一寫入點,而且一次寫兩張表 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:92`、`:97` |
| `OFD302A.NAV_LOCK` | 淨值檔 | 淨值鎖定旗標,`OFDB041` 切換 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB041Model.xsd` |
| `OFD281A.PROCESS_CODE` | 收益分配主檔 | `'0'` 未產生 / `'1'` 已產生 / `'4'` 已結算確認。`'4'` 之後 `OFDB281` 三種功能全擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:114`、`:153`、`:191` |
| `CRSP001.PROC_CODE` / `REPORT_STATUS` | CRS 申報控制檔 | `PROC_CODE` 空白 = 正常、`'D'` = 取消;`REPORT_STATUS` `'0'` 未申報 / `'1'` 已申報 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170`、`:243` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDB 批次片全景:七群業務、三個世代的資料存取路徑、OFDB003 的對外生效線，以及全片沒有排程這件事
圖中文字:① 這 18 支不是一條流程，是七群互不相干的批次 / A 受益人資料生效 / OFDB003 OFDB005 / B 基金設定 / OFDB004 OFDB040 OFDB041 / C 收益分配 / OFDB281 OFDB286 OFDB287 / D 帳務關卡 / OFDB222 / E 法遵申報 / OFDB019A OFDB019B / F 申報 憑證 列印 / OFDB001 002 007 008 011 / G 定期買回 換號 / OFDB161 OFDB223 / ② 三個世代四種資料存取路徑 —— 決定一支能不能跑 / EVA 滿血 3 支 / BaseEVADaoPO 有主明細 / EVA 空殼 5 支 / 掛基底不填 xTableMapping / 裸 DAO 6 支 / 自建 Database 自管交易 / 舊世代 4 支 SQL Server / dbTA 恆為 null 跑不起來 / ③ 本片最重要的一條對外線:OFDB003 是 BMS 整套變更單的生效引擎 / BMSM004 BMSM006 / BMS 開單 + 四眼 / BMS001ACHG / 覆核完仍未生效 / OFDB003 / s_TA_OFDB003_Excute / BMS001A 等 12 張本表 / 蓋 CHG_UPD_DTTM / OFDB609 補推 LDAP / ATLAS.EC 的服務 / ④ 全片沒有排程:18 支都是 xOneStepProcessForm，要人按執行 / CTL016 BF_PROC_TIME / 有設定值但沒人讀 / WindowsService / 四支全都不在本片 / 21 支 SP / repo 內腳本 0 支 / LDAPAPIHelper GenXMLHelper / 無原始碼
```

*圖:圖 1 全景。橘框=本片主要入口;橘虛框=要留意的行為(跑不起來、跨專案補償、設定值沒人讀);灰虛框=本片以外的畫面或表;黑框=無原始碼。第②列決定一支能不能跑 —— 最右邊那四支是 SQL Server 時代的遺留。*

### 1.2 資料表關係

七群批次各自吃自己的表,交集只有三張:`OFD081A`(基金主檔)、`OFD303A`(過帳控制)、`OFD085A`(境內基金轉換設定)。下圖把「誰寫、誰只讀」分開;跨模組的讀取端見 §8。

### 1.3 主要維護畫面的四眼與卡控順序

**本片沒有 M 畫面**(見 §4),所以沒有這張圖。四眼真正發生的地方在 BMS 與 OFD 的 M 片; 本片與四眼唯一的接點有兩處:`OFDB003` 執行前會數「還有幾筆沒覆核」(§6.1)、`OFDB222` 關帳前會數「交易資料中有沒有未覆核」(§6.10)。兩者都只是**詢問**,不是阻擋。

### 1.4 批次 / 報表資料流

兩張圖:`OFDB003` 的生效接力(§6.1)與 `OFDB004` 的基金複製寫入順序(§6.2)。

### 1.5 一日作業泳道

本片 18 支**沒有固定的一日順序**,因為它們分屬七群互不相干的業務。有明確先後相依的只有三條,細節在 §6.13:

| 條 | 順序 | 卡在哪 |
|---|---|---|
| 配息 | `OFDB281` 產生 →(`OFDB284` 結算確認,不在本篇)→ `OFDB286` 退匯 → `OFDB287` 重匯 | `OFD281A.PROCESS_CODE` |
| 受益人變更 | BMS `BMSM004` / `BMSM006` 開單與四眼 → **`OFDB003`** 生效 →(LDAP 失敗時)`OFDB609` 補推 | `CHG_UPD_DTTM` 與 `f_TA_GetEVAStatus('A')` |
| CRS 申報 | `OFDB019A` 產出資料 → `OFDB019B` 下載 XML | `CRSP001.REPORT_STATUS` / `PROC_CODE` |

## 2. 資料模型

```text
[圖] OFDB 批次片動到的資料表分成四群，以及六支畫面的表名只存在於 SQL 字串裡這件事
圖中文字:受益人群:本片寫、BMS 與五個專案讀 / BMS001ACHG / 變更申請單 CHG_UPD_DTTM / BMS001A / 受益人主檔 / OFD131A / 配息帳號 PAUSE_PAY / RSP013A / RSP 也有同一套 CHG / 基金群:OFD081A 是交會點，OFDB004 一次寫 16 張衍生設定 / OFD081A / 基金主檔 FUND_LOCK / FND001 / 第二份鎖定旗標 repo 無定義 / OFD302A / 淨值檔 NAV_LOCK / 16 張基金設定表 / OFD038A 070A 074 …261A / 配息群:OFDB281 產生 → OFDB286 退匯 → OFDB287 重匯 / OFD281A / 主檔 PROCESS_CODE / OFD287A / 明細 / OFD283A / 付款 GET_STATUS / OFD292A / 退匯重匯明細 / OFD085A / 收益分配專戶在自轉自那列 / 控制與代碼群(全部唯讀) / OFD303A / 過帳與結轉控制碼 / CTL014 / 代碼值域 690 016 027 … / CTL016 / 處理時間 沒人讀 / OFD681 OFD681A / 通知信名單 SEND_TYPE / 只存在於 SQL 字串裡的表 —— 改欄位時 xsd 找不到 / CTL022 / OFDB222 關帳 / 七張交易表 / OFDB223 整批換號 / OFD342 OFD343 / OFDB011 地址條 / AA_Customer OFD0813 / OFDB008 申報檔
```

*圖:圖 2 資料表關係。橘框=本片會寫的核心表;橘虛框=要留意(repo 內查不到定義、或表名躲在 SQL 字串裡);灰虛框=別的模組維護;黑框=唯讀控制表。最後一列的表在 xsd 裡完全查不到，改欄位只能 grep。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

18 支裡**只有 3 支真的宣告了主明細**,其中 `OFDB004` 一支就佔了 16 張明細。

| 畫面 | 主表(實體) | vdb 名 | 明細(實體) | 錨點 |
|---|---|---|---|---|
| `OFDB001` | `OFD312` | `OFDB001` | — | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:19` |
| `OFDB002` | `OFD081A`(查詢時換成 `OFD297A`) | `OFDB002` / `OFDB002_Get` | — | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:36`、`:68` |
| **`OFDB004`** | `OFD081A` | `OFDB004` | **16 張**,見 §2.2 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:54-77` |
| `OFDB005` | `OFD195` | `OFDB005` | — | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:20` |
| `OFDB011` | `OFD342` | `OFDB011` | — | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:20` |
| `OFDB041` | `OFD302A` | `OFDB041` | —(`BaseMultiRowEVADaoPO`,`MasterTable` 是 `List`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:32-33` |
| **`OFDB281`** | `OFD281A` | `OFDM281` | `OFD287A` → `OFDM281_Detail` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:41`、`:46` |

> ⚠ **`OFDB002` 的主檔在執行期會被換掉。** 建構子宣告 `OFD081A`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:36`),但查詢方法一開頭就把`this.MasterTable` 改成 `OFD297A`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:68`)。PO 是連線池裡共用的實例(`InitializeDataAccessPool`,`architecture.md §6.2`),這種在方法裡改共用狀態的寫法**不是執行緒安全的**;附錄 E 記一筆。

> ⚠ **`OFDB281` 的主表與 `OFDM281`(維護畫面,不在本篇)是同一張 `OFD281A`。**vdb 名也叫 `OFDM281`,所以從 vdb 名反查會撞在一起。`OFDB281` 對這張表**不走四眼**,它只讀 `PROCESS_CODE` 當前置條件,真正的寫入交給 SP `s_TA_OFDB281_Excute`(見 §6.3)。

### 2.2 `OFDB004` 的 16 張明細(本片最大的一組宣告)

建構子一次掛滿,順序就是檔案裡的順序:

| # | 實體表 | vdb 名 | 對應的維護畫面(從 `OFDB004` 畫面上的提示文字反推) |
|---|---|---|---|
| 1 | `OFD129A` | `OFDM129` | 特定受益人申贖限制維護作業 |
| 2 | `OFD038A` | `OFDM038` | 基金群組設定作業 |
| 3 | `OFD070A` | `OFDM070A` | 銷售機構承銷境內基金設定維護作業 |
| 4 | `OFD074` | `OFDM074` | 代扣款行基本資料維護作業 |
| 5 | `OFD075` | `OFDM075` | (`OFD074` 的明細) |
| 6 | `OFD076` | `OFDM076` | 代理行基本資料維護作業 |
| 7 | `OFD077` | `OFDM077` | (`OFD076` 的明細,只收 `SEAL_TYPE = '3'`) |
| 8 | `OFD193A` | `OFDM193` | 自訂銷售手續費設定維護作業 |
| 9 | `OFD194A` | `OFDM194` | 特定受益人銷售手續費優惠設定維護作業 |
| 10 | `OFD196A` | `OFDM196` | 關係人銷售手續費優惠設定維護作業 |
| 11 | `OFD085A` | `OFDM085A` | 境內基金轉換設定維護作業 |
| 12 | `OFD213A` | `OFDM213` | 贖回匯款不收匯費銀行設定作業 |
| 13 | `OFD214A` | `OFDM214` | 特定受益人贖回 / 收益分配匯費設定作業 |
| 14 | `OFD215A` | `OFDM215` | 特定受益人不收短線交易費設定作業 |
| 15 | `OFD260A` | `OFDM260` | 短線交易費設定作業(畫面代號寫 `OFDM233`) |
| 16 | `OFD261A` | `OFDM261` | 同上的明細 |

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:55-77`;中文名出處:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:95-107` 那 13 行 `AppendLine`,以及 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:120-267` 逐表檢核的訊息字串。

第 17 張 `OFD233`(`OFDM233` 指定扣款資料回覆確認檔)**被註解掉,不複製**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:73-74` 與 `:648-649`),但它的 DataTable 還留在 `OFDB004Model.xsd` 裡 —— 讀 xsd 會以為有 17 張。

### 2.3 母體裡的「表」大半不是實體表,是查詢結果集形狀

`architecture.md §5.5` 說 xsd 是 repo 內唯一的 schema 來源,但也警告 xsd 裡有大量「查詢結果集形狀」。本片這個比例特別高 —— 18 份 `*Model.xsd` 宣告的 DataTable,有實體表對應的只有 §2.1 那 7 張,其餘全部是 SP 的 refcursor 輸出或自組 SQL 的投影。

| 畫面 | Model.xsd 裡的 DataTable | 其中有實體表對應的 |
|---|---|---|
| `OFDB001` | `OFDB001`、`RESULT` | `OFDB001` → `OFD312` |
| `OFDB002` | `OFDB002`、`OFDB002_Get` | `OFDB002_Get` → `OFD297A` |
| `OFDB003` | `OFDB003`、`OFDB003_TIMES`、`OFDB003_LDAP`、`OFDB003_LDAPSTATUS`、`OFDB003_EC`、`OFDB003_FILL`、`OFDB606`、`BMS001CHG`、`OFD681`、`LOG602` | `BMS001CHG` → `BMS001ACHG`、`LOG602`、`OFD681` |
| `OFDB004` | `OFDB004` + 17 張 `OFDM*` | 全部(見 §2.2) |
| `OFDB005` | `OFDB005_TIMES`、`OFD681` | `OFD681` |
| `OFDB007` | `BMS001` | `BMS001A` |
| `OFDB008` | `OFDB008_EBF` / `_FNH` / `_BOT` / `_SHT` / `_DSR` / `_BFP` / `_CLB` / `_FSA` / `_NAV` / `_FUND` / `_CO` | **零**,全部是 SP 輸出 |
| `OFDB011` | `OFDB011`、`OFDB011_Get`、`OFDB011_Ck` | `OFDB011` → `OFD342` |
| `OFDB019A` | `CRSP001`、`CRSP001_TEMP`、`CRSP001_TEMP2`、`CSRP001_COUNT` | `CRSP001` |
| `OFDB019B` | `CRSP001`、`CRSP002`、`CRSP002_1`、`CRSP002_2`、`CRSP004`、`CRSP006`、`CRSP001_006_DATA` | `CRSP001` ~ `CRSP006` |
| `OFDB040` | `OFDB040_FundData` | **零**(寫入目標 `OFD081A` / `FND001` 只出現在 SQL 字串) |
| `OFDB041` | `OFDB041` | `OFD302A` |
| `OFDB161` | `OFDB161_TIMES`、`OFDB161_Check`、`OFD681` | `OFD681` |
| `OFDB222` | `OFDB222` | **零**(寫入目標 `CTL022` 只在 SQL 字串) |
| `OFDB223` | `OFDB223` | **零**(七張交易表只在 SQL 字串) |
| `OFDB281` | `OFDM281`、`OFDM281_Detail`、`OFDB281` | `OFD281A`、`OFD287A` |
| `OFDB286` | `OFDB286` | **零**(`OFD283A` / `OFD131A` / `OFD292A` 只在 SQL 字串) |
| `OFDB287` | `OFDB287` | **零**(同上) |

> **實務結論:改本片任何一張實體表的欄位,光改 xsd 是不夠的 —— 有六支畫面的表名完全躲在 SQL 字串裡, 要靠 grep 表名才找得到。** 名單:`OFDB008`、`OFDB040`、`OFDB222`、`OFDB223`、`OFDB286`、`OFDB287`。

### 2.4 主鍵與四眼欄位

本片只有兩支的 Model 帶完整 EVA 欄位(`EntryID` / `VerifyID` / `ApproveID` / `RejectID` 四支都在):`OFDB003` 與 `OFDB281`。其餘 16 支的 Model 一個 EVA 欄位都沒有 —— 這正是`architecture.md §6.1` 講的「B 型四眼欄位少」。

| 畫面 | Model 的 `xs:unique` 主鍵 | EVA 欄位 | `Status` 欄 |
|---|---|---|---|
| `OFDB001` | `OFDB001`:`FUND_ID` + `ISSUE_DATE` | 無 | 無 |
| `OFDB004` | 18 組,例 `OFDM085A`:`FUND_ID` + `SWITCH_FUND_ID`;`OFDM214`:`FUND_ID` + `BF_NO` | 無(但 SQL 端有,見下) | 有 |
| `OFDB011` | 2 組 | 無 | 無 |
| `OFDB040` | 1 組 | 無 | 有(只用來判 `LIKE '3%'`) |
| `OFDB041` | 1 組 | 無 | 有 |
| `OFDB281` | `OFDM281`:`FUND_ID` + `YEARS` + `ISSUE_CODE`;`OFDM281_Detail`:`DIV_TYPE` | **有** | 有 |
| `OFDB003` | 1 組 | **有**(在 `LOG602` 上) | 有 |
| 其餘 11 支 | **沒有任何 `xs:unique`** | 無 | 部分有 |

錨點:`Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB004Model.xsd`、`Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB281Model.xsd`。

**`OFDB004` 是例外中的例外**:Model 裡沒有 EVA 欄位,但程式在複製時**逐列手動清空 13 個 EVA 欄位** (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:750-765` 的 `SetDataRowSysParam`),證明實體表上這些欄位是存在的 —— xsd 沒宣告而已。這也是「複製過去的資料必須重新覆核」的機制(見 §6.2)。

### 2.5 欄位中文名(來自 xsd `msdata:Caption`)

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。本片填得比 BMS 完整,但仍有整支畫面全空的情況。

| 畫面 | 有 Caption 的欄位(節錄) |
|---|---|
| `OFDB002` | `RESULT`「結果」、`MSG`「錯誤訊息」、`FUND_ID`「基金代碼」、`FUND_SH_NM`「基金中文簡稱」、`EXE_STATUS`「執行狀態」 |
| `OFDB003` | `result`「結果」、`msg`「錯誤訊息」、`BF_NO`「受益人ID」、`BF_NAME`「受益人中文姓名」、`CELL_PHONE`「行動電話」、`OF_TEL`「公司電話」、`HM_TEL`「住家電話」、`MAIL_ADDR`「通訊中文地址」、`PERM_ADDR`「戶籍中文地址」 |
| `OFDB005` | `CHG_EFFECT_DATE`「變更生效日期」、`APPLY_DATE`「申請日期」、`REL_PROC_TIME`「BF_PROC_TIME」(填錯,填成欄名) |
| `OFDB040` | `IsCheck`「註記」、`FUND_ID`「基金代碼」、`FUND_SHNM`「基金中文簡稱」、`STATUS_DESCRP`「狀態」、`STATUS`「Status」(同樣填成欄名) |
| `OFDB041` | `IsCheck`「是否選取」、`NAV_B`「正式淨值」、`BID_NAV`「申購淨值」、`OFFER_NAV`「贖回淨值」、`FH_CD`「基金公司代碼」 |
| `OFDB161` | `PERIOD_REDEM_PROCESS_TIME`「定期買回處理時間」、`PERIOD_REDEM_DATE`「LOCK_GAIN_DATE」(又一個填成欄名) |
| `OFDB222` | `AGENT_ID`「銷售機構區別碼」、`AGENT_CODE`「銷售機構代碼」、`AGENT_SHNM`「銷售機構」、`TX_DATE`「交易日期」 |
| `OFDB223` | `BF_AGENT_ID`「異動前銷售機構區碼」、`AF_AGENT_CODE`「異動後銷售機構」 |
| `OFDB286` | `BF_NAME`「受益人姓名」、`TOTAL_PAY_AMT`「總實付金額」、`RET_REMIT_DATE`「退匯日期」、`RREMIT_REASON`「退匯原因」、`ACT_PAY_DATE`「實際付款日期」 |
| `OFDB287` | `YEARS`「年度」、`ISSUE_CODE`「期別」、`ORG_ACT_PAY_AMT`、`RREMIT_FEE`、`RREMIT_MEMO` |
| `OFDB001` / `OFDB007` / `OFDB008` / `OFDB011` / `OFDB019A` / `OFDB019B` / `OFDB281` | 幾乎全空,中文名只能從 Designer 的標籤字串或 SQL 註解推 |

> ⚠ **有八處 `msdata:Caption` 填錯,填成英文欄名、甚至填成別的欄位的名字。**填成自己英文欄名的三處:`OFDB005Model.xsd` 的 `REL_PROC_TIME` → 「BF_PROC_TIME」、`OFDB040Model.xsd` 的 `STATUS` → 「Status」、`OFDB161Model.xsd` 的 `PERIOD_REDEM_DATE` → 「LOCK_GAIN_DATE」。 **`OFDB003Model.xsd` 更嚴重,填成了別的欄位**:`ORG_ID_TYPE` 的 Caption 是「ORG_CELL_PHONE」、 `NEW_ID_TYPE` 的是「NEW_CELL_PHONE」、`NEW_ALLIN3` 的是「NEW_ID_NO」,而 `ORG_ID_NO` 與 `ORG_ALLIN3` **兩個不同欄位共用同一個 Caption「ID_NO」**。照 `architecture.md §5.5`, Caption 是全庫唯一的中文名來源 —— 這幾欄的中文名等於是錯的。附錄 E 記一筆。

### 2.6 與其他模組共用的表

| 表 | 本片誰動 | 誰也在用 | 風險 |
|---|---|---|---|
| `BMS001ACHG` | **`OFDB003` 透過 SP 回寫並蓋 `CHG_UPD_DTTM`** | BMS `BMSM004` / `BMSM006` 開單與四眼(`bms.md §2`) | **本片最高**,見 §6.1 與 §8.1 |
| `BMS001A` | `OFDB003` 間接(SP 內)、`OFDB007` 只讀 | BMS 全模組、OFD 大半 | 高 |
| `OFD081A` | `OFDB040` 寫 `FUND_LOCK`;`OFDB002` / `OFDB004` 只讀 | OFD 基金主檔全線、RSP、DSM | 高 |
| `OFD303A` | 只讀(過帳控制) | 全 TA 的日結 / 關帳 | 高 |
| `OFD085A` | `OFDB004` 寫、`OFDB281` 只讀 | OFD 轉換相關、`OFDM085A` | 中 |
| `OFD283A` / `OFD292A` | `OFDB286` / `OFDB287` 寫 | 配息相關報表 | 中 |
| `OFD131A` | `OFDB286` 寫 `PAUSE_PAY`(`OFDB287` 只讀) | BMS `BMSM006` 的 `OFD131ACHG` 配對表(`bms.md §2`) | **中高**,見 §8.2 |
| `CTL022` | `OFDB222` 寫 | 交易關帳 | 中 |
| `FND001` | `OFDB040` 寫 | 基金主檔的另一份(名字不同前綴,來源不明) | 中 |
| `OFD607A` | `OFDB003` 的密碼回寫段**已整段註解** | EC 模組 | 低(現已不動) |

### 2.7 狀態碼(從程式反推,標來源)

本片沒有自己的四眼狀態機。真正被本片當旗標用的是七組業務碼:

| 欄位 | 值 | 意義(反推) | 錨點 |
|---|---|---|---|
| `BMS001ACHG.CHG_UPD_DTTM` | 空 / 有值 | **空 = 尚未生效**;有值 = 已被 `OFDB003` 生效。判準全庫一致:`SUBSTR(NVL(TRIM(CHG_UPD_DTTM),'19000101'),1,8) = '19000101'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:318` |
| `OFD081A.STATUS` | `LIKE '3%'` | 已覆核。`OFDB004` / `OFDB040` 都用這個判準 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:317-321`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:60` |
| `OFD281A.PROCESS_CODE` | `'0'` / `'1'` / `'4'` | 未產生 / 已產生 / 已結算確認 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:114`、`:153`、`:191` |
| `OFD283A.GET_STATUS` | `'4'` | 退匯(`OFDB286` 寫入的值) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:65` |
| `OFD303A.POST_CTL_CODE` | `'Y'` / `'N'` | 已過帳 / 未過帳 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:80`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:246` |
| `OFD303A.ALLOT_CTL_CODE` / `REDEM_CTL_CODE` / `RSP_CTL_CODE` | `'3'` / `'4'` 以上 | 已結轉。申購看 `>= '3'`、贖回看 `>= '4'`、定時定額看 `>= '3'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:244-246`、`:274-276` |
| `CTL022.ALLOT_CLS` / `REDEM_CLS` | `'Y'` / `'N'` | 關帳 / 未關帳。`OFDB222` 唯一寫入點 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:56-59`、`:82`、`:89` |
| `CRSP001.MESSAGE_TYPE` | `CRS701` / `CRS702` / `CRS703` | 新增資訊 / 刪除已申報資訊 / 無(應申報帳戶及無資訊帳戶),值域 `CTL014` 的 `690` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:41` |
| `CRSP001.PROC_CODE` | 空白 / `'D'` | 正常 / 取消 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170` |
| `CRSP001.REPORT_STATUS` | `'0'` / `'1'` | 未申報 / 已申報 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:245` |
| `OFD131A.PAUSE_PAY` | `'Y'` / `'N'` | 暫停配息 / 正常 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:74`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:365` |

`architecture.md §3.10` 講的 `EVAStatusCode` 值域在本片**只有 `OFDB222` 間接用到**(透過 `SetSecurityData(row, vdb, EVAType.Add)`,`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:135`),其餘畫面一律用上表的業務碼。

## 3. 畫面清冊

本片 **18 支全部是 B 批次**:M 0 支、I 0 支、R 0 支(§4 / §5 / §7 各有說明)。

### 3.1 維護 M

(本片無此類畫面。維護 `OFD081A` / `BMS001A` / `OFD281A` 的 M 畫面住在 OFD 的 M 片與 BMS 專案,不在 `Dev/ATLAS.OFDB/`。)

### 3.2 查詢 I

(本片無此類畫面。18 支都有寫入或檔案輸出的動作,沒有純唯讀的;最接近的是 `OFDB007`,它的 `AfterExecuteButtonClicked` 直接 `e.Cancel = true`——`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:124-127`——但它仍歸類為 B,因為代號第四碼是 `B` 而且有報表輸出。)

### 3.3 批次 B(18 支)

**六層全齊:18 支每一支的 UI / Pxy / Ctl / PO / Model.xsd / View.xsd 都在** (`find Dev/ATLAS.OFDB -iname "OFDB00*"` 等逐支確認)。掃描器若回報缺層,是主明細宣告的問題,不是檔案缺。

| 代號 | 中文名(推測,待選單表) | 六層 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `OFDB001` | 基金總額憑證產生 / 刪除 | 齊 | `OFD312` | — | `s_OFDB001_Excute`、`s_OFDR001A_Get` | 無 |
| `OFDB002` | 基金淨值區間重算(執行狀態回報型) | 齊 | `OFD081A` / `OFD297A` | — | `s_TA_OFDB002_Excute` | 無 |
| **`OFDB003`** | **受益人異動批次轉入作業** | 齊 | (裸 DAO) | — | `s_TA_OFDB003_Excute`、`f_TA_GetEVAStatus` | 無 |
| **`OFDB004`** | **基金複製** | 齊 | `OFD081A` | **16 張** | 無(全自組 SQL + EVA 基底) | 無 |
| `OFDB005` | 受益人資料變更申請生效(申請日期版) | 齊 | `OFD195` | — | `s_OFDB005_Excute` | 無 |
| `OFDB007` | 受益人名條 / 標籤列印 | 齊 | (裸 DAO) | — | 無 | `OFDB007RPS.rpt` |
| `OFDB008` | 主管機關申報檔產出(八種檔) | 齊 | (裸 DAO,兩個 `Database`) | — | 9 支 `S_TA_OFDB008_*` + `s_TA_NFDR005_Get` / `s_TA_NFDR006_Get` | 無(輸出 `.mon` / `.101`) |
| `OFDB011` | 資料索取信封 / 地址條列印 | 齊 | `OFD342` | — | `s_OFDB011_Get` | `OFDB011RPS.rpt` |
| **`OFDB019A`** | **CRS 申報資料產出 / 刪除** | 齊 | (EVA 空殼) | — | `S_TA_OFDB019A_EXECUTE` | 無 |
| **`OFDB019B`** | **CRS 申報 XML 下載 / 刪除** | 齊 | (EVA 空殼) | — | `S_TA_OFDB019B_EXECUTE` | 無(輸出 `.xml`) |
| `OFDB040` | 基金鎖定 / 取消鎖定 | 齊 | (裸 DAO) | — | 無(匿名 PL/SQL 區塊) | 無 |
| `OFDB041` | 淨值鎖定 / 取消鎖定 | 齊 | `OFD302A` | — | 無(走 `base.Update`) | 無 |
| `OFDB161` | 定期買回處理 | 齊 | **無宣告** | — | `s_OFDB161_Excute` | 無 |
| `OFDB222` | 交易關帳 / 取消關帳 | 齊 | (裸 DAO) | — | `f_TA_GetFNBusinessDay` | 無 |
| `OFDB223` | 銷售機構代碼整批置換 | 齊 | (裸 DAO) | — | 無 | 無(`OFDB223p0` 彈出視窗) |
| **`OFDB281`** | **收益分配受益人資料產生 / 重新產生 / 刪除** | 齊 | `OFD281A` | `OFD287A` | `s_TA_OFDB281_Excute` | 無 |
| `OFDB286` | 配息退匯 / 取消退匯 | 齊 | (EVA 空殼) | — | 無 | 無 |
| `OFDB287` | 配息重匯 / 取消重匯 | 齊 | (EVA 空殼) | — | `s_TA_OFDB287_Get` | `OFDB287RPS.rpt` |

中文名的來源全部標在 §6 各節開頭,沒有任何一個來自猜測以外的官方文件 —— 所以**一律標「推測」**。

### 3.4 報表 R

(本片無 R 型畫面。`OFDB007` / `OFDB011` / `OFDB287` 三支各自帶一個 `*RPS.rpt`,但 `.rpt` 直接躺在 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/` 底下,不是 `architecture.md §6.5` 講的 `ATLAS.<模組>.Report` 七層結構 ——它們是 B 畫面自帶的列印輸出,不是獨立報表畫面。)

## 4. 維護畫面(M)

**本片無 M 畫面。** 原因很單純:`Dev/ATLAS.OFDB` 這個 sln 是照**型別**切的,只收 `OFD` 前綴的 `B` 畫面; 所有 `OFDM*` 住在 `Dev/ATLAS.OFD/`。本片會動到的表(`OFD081A` / `OFD281A` / `BMS001ACHG` …)的維護入口全部在那裡或 BMS 專案裡,見 §8。

## 5. 查詢畫面(I)

**本片無 I 畫面**,原因同 §4。

不過「會把資料濾掉而不提示」這件事在批次身上一樣會發生,而且後果更大 —— 批次濾掉的是**要被處理的資料**。本片的過濾條件(卡控結果都是「過濾(無提示)」)集中在這幾處:

| 畫面 | 被靜默濾掉的 | 錨點 |
|---|---|---|
| `OFDB003` | `Check` 只數「未覆核」筆數,**但真正要處理哪些單完全由 SP 決定** —— 呼叫端傳的三個參數和 `Check` 用的 SQL 條件是各寫各的(見 §6.1) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:72-78` 對照 `:315-322` |
| `OFDB004` | `OFD193A` / `OFD194A` / `OFD196A` 只複製 `FEE_TYPE = '1'` 的列;`OFD077` 只複製 `SEAL_TYPE = '3'` 的列 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:979-996` |
| `OFDB004` | `OFD070A` 的 `ACP_DATE` 一律改成今天、`DUE_BANK` / `DUE_ACC_NO` / `DUE_CODE` / `ACC_MEMO` 一律清空 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:420`、`:428-431` |
| `OFDB007` | 匯入 Excel 時只要前面任何一列有格式錯誤,`ValidateErrList.ErrorCount < 1` 就不成立,**後面所有列全部不進 DataTable** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:176-193` |
| `OFDB019A` / `OFDB019B` | 幾乎每一段 SQL 都帶 `NVL(PROC_CODE,' ') <> 'D'`,已取消的申報批次一律不出現 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170`、`:193` |
| `OFDB040` / `OFDB041` / `OFDB222` / `OFDB286` / `OFDB287` | 只處理 Grid 上 `IsCheck = true` 的列;沒勾的靜默跳過 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:105`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:76` |
| `OFDB041` | `IS_UNLOCK = false` 的列在 UI 被 disable,但**伺服端的同名檢核恆為 true**(見附錄 E) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB041.cs:239-241` 對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:333-336` |

## 6. 批次(B)與 WindowsService

```text
[圖] OFDB004 基金複製的前置檢核、記憶體整理與六段寫入順序，以及它不是日結批次的依據
圖中文字:① 前置:兩檔基金都要已覆核、幣別相同、目的基金 13 張表都還是空的 / STATUS LIKE 3% / 來源與目的各檢一次 / FUND_CURRENCY 相同 / 不同就擋 / 13 張表已有資料就擋 / 逐張列訊息 / OFD074 OFD076 OFD261A / 會寫入卻沒被檢核 / ② 記憶體整理:撈來源基金 → 換 FUND_ID → 清 STATUS 與 13 個 EVA 欄位 / GetMaintainData / OFD081A 用 dual 騙過 evapo / BeforeGetMaintainData / 七張表改寫 SQL / SetDataRowSysParam / 清 STATUS 與 EVA 13 欄 / 複製出來的資料未覆核 / 要到 13 支 OFDM 重新覆核 / ③ 寫 DB:兩個交易、六段，順序有意義 / 1 MultiRow 更新 / OFD038A 070A 214A 215A / 2 MultiRow 新增 / OFD193A 194A 196A 213A / 3 逐列新增 / OFD129A / 4 短線費 只在恰好 1 列時 / OFD260A + OFD261A / 5 OFD085A 特別處理 / 先移走再 Update 再 ImportRow 回來 / 6 CopyDetail 兩組 / OFD076+077 OFD074+075 / commit 兩個交易 / dbProduct 與 dbPTPF / 兩次 commit 之間不是原子的 / 一邊成功一邊失敗就不一致 / ④ 它不是日結 —— 沒有任何日期參數，只有來源基金與目的基金 / 參數只有四個 / FromFund ToFund D_Type AFEE_TYPE / 畫面上列 13 支 OFDM / 執行完請去增修或覆核 / 日結在 OFD303A 那條線 / 本片只讀不寫
```

*圖:圖 4 OFDB004 基金複製。橘框=關鍵步驟;橘虛框=要留意的行為(沒被檢核的三張表、寫死的 1 列條件、兩次 commit 不原子);灰虛框=本片以外。第③列六段不能交換順序 —— OFD085A 那段依賴前面五段已經寫完。*

```text
[圖] BMS 開單與四眼走完之後資料仍未生效，要等 OFDB003 呼叫版控外的 SP 回寫並蓋 CHG_UPD_DTTM，commit 之後才推外部 LDAP
圖中文字:① BMS 側:開單 → 四眼。走完這三關，本表仍然沒有變 / BMSM004 / BMSM006 / 開單 BEF_* 與 AFT_* 同時填 / Entry 輸入 / CHG_UPD_DTTM 空 / Verify 驗證 / CHG_UPD_DTTM 空 / Approve 覆核 / CHG_UPD_DTTM 仍然空 / ② OFDB003 側:人工按執行。Check 只是詢問，不是阻擋 / 輸入三個條件 / 生效日 收件日 變更書號 / DoValidate / 生效日不可大於系統日 / PXY.Check / 數未覆核筆數 / 尚有 N 筆未覆核 是否繼續 / 按 OK 就繼續 詢問不阻擋 / ③ 執行:交易由 C# 開，SP 在同一個交易裡跑 —— 所以真的可以整批回滾 / BeginTransaction / C# 端 CommandTimeout 0 / s_TA_OFDB003_Excute / 無原始碼 5 個 refcursor / T_MSG 0 筆 / rollback 查無可執行之資料 / 任一列 result 不等於 1 / rollback 執行失敗 / ④ 回寫(假設:SP 內部，repo 查不到) / commit / 執行成功 共變更 N 筆 / AFT_* 寫回本表 / 哪些欄位對哪些 查不到 / 蓋上 CHG_UPD_DTTM / 全庫沒有任何 C# 在寫它 / 單子變唯讀 / BMSM004 006 鎖住修改與刪除 / ⑤ commit 之後才推 LDAP —— 失敗會把成功訊息蓋掉，但資料已經生效 / UpdateLDAPStatus / 寄信那行被註解 / UpdateLDAPCustomer / ID EMAIL 手機 三種變更 / 失敗 訊息換成執行LDAP更新失敗 / DB 早就 commit 了 / OFDB609 更新LDAP資料 / 另一個專案的服務
```

*圖:圖 3 OFDB003 的生效接力(本篇最重要的一張)。橘框=本片入口;橘虛框=要留意的行為;灰虛框=本片以外;黑框=無原始碼。第②列那道「尚有 N 筆未覆核」只是詢問 —— 按 OK 就繼續，而那個條件沒有傳給 SP，所以未覆核的單會不會被一起生效，從呼叫端無法判斷。第⑤列是最容易咬人的地方:LDAP 失敗時畫面說失敗，資料其實已經生效了。*

**本章是全篇主體。** 18 支逐一或分群展開,每支固定回答六件事: 觸發方式 · 參數 · 寫哪些表 · 失敗怎麼處理(會不會 rollback)· 可不可以重跑 · 與其他批次的順序相依。

### 6.0 先看總表

| 畫面 | 觸發 | 寫入方式 | 交易由誰管 | 失敗會 rollback 嗎 | 可重跑 |
|---|---|---|---|---|---|
| **`OFDB003`** | 人工按「執行」 | SP(5 個 refcursor) | **C# 端 `BeginTransaction`**,SP 參與同一交易 | **會**(兩條失敗路徑各一次 `Rollback`) | 假設可以,見 §6.1 |
| **`OFDB004`** | 人工按「執行」 | EVA 基底 `Add` / `Copy` + 自組 SQL | C# 端,**雙交易**(`dbProduct` + `dbPTPF`) | **會**(兩個交易一起 rollback) | **不建議**,見 §6.2 |
| `OFDB281` | 人工按「執行」 | SP | C# 端 | **會** | 有「重新產生」與「刪除」兩個功能專門處理重跑 |
| `OFDB001` | 人工按「執行」 | SP(T-SQL `EXEC`) | C# 端 | 會 | **跑不起來**(§0.2) |
| `OFDB002` | 人工按「執行」 | SP(1 個 refcursor) | C# 端 | **會** | 未知 |
| `OFDB005` | 人工按「執行」 | SP(T-SQL `EXEC`) | C# 端 | 會 | **跑不起來** |
| `OFDB007` | 人工按「執行」 | **不寫 DB**,只列印 / 匯出 | 無 | 不適用 | 可 |
| `OFDB008` | 人工按「執行」 | **不寫 DB**,SP 取數後由 UI 寫檔 | 無寫入 | 不適用 | 可(會覆蓋同名檔) |
| `OFDB011` | 人工按「執行」 | 自組 `UPDATE`(T-SQL) | C# 端 | 會 | **跑不起來** |
| `OFDB019A` | 人工按「執行」 | SP(`strMsg` 出參) | C# 端 | **會** | 有「刪除資料」功能 |
| `OFDB019B` | 人工按「執行」 | SP(6 個 refcursor)+ UI 寫 XML | C# 端 | **會** | 有「刪除 XML 檔案」功能 |
| `OFDB040` | 人工按「執行」 | 匿名 PL/SQL 區塊,逐列 | C# 端 | 會 | 可(冪等,設同一值) |
| `OFDB041` | 人工按「執行」 | `base.Update`(EVA 多筆) | 基底管 | 基底管 | 可 |
| `OFDB161` | 人工按「執行」 | SP(T-SQL 參數) | C# 端 | 會 | **跑不起來** |
| `OFDB222` | 人工按「執行」 | 自組 `UPDATE` + `INSERT`,逐列 | C# 端 | 會 | 可(有取消關帳) |
| `OFDB223` | 人工按「執行」 | 自組 `UPDATE` × 7 張表,逐列 | C# 端 | 會 | **危險**,見 §6.11 |
| `OFDB286` | 人工按「執行」 | 匿名 PL/SQL 區塊,逐列 | C# 端 | 會 | 有「取消退匯」 |
| `OFDB287` | 人工按「執行」 | 匿名 PL/SQL 區塊,逐列 | C# 端 | **部分**,見 §6.12 | 有「取消重匯」 |

**沒有任何一支配 WindowsService。** `architecture.md §8.4` 的四支服務都不在 `Dev/ATLAS.OFDB/`。

### 6.1 `OFDB003` 受益人異動批次轉入作業(推測)—— 本篇頭號重點

**這支是 BMS 整套「受益人資料變更申請單」的生效引擎。** `bms.md §2` 已經用九條證據鏈證明:BMS 的 12 張 `CHG` 配對表,覆核通過之後資料**仍然沒有進本表**,判準是 `TRIM(CHG_UPD_DTTM) IS NULL`;真正的回寫由本支呼叫的 SP `s_TA_OFDB003_Excute` 完成。本節不重述那條證據鏈,只回答一件事:**站在呼叫端,我們到底能確定什麼、什麼只能標假設。**

中文名出處:`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:111` 與 `:177` 兩處 mail 主旨「OFDB003 受益人異動批次轉入作業 - LDAP更新失敗通知」——**這是 repo 內唯一一處把本支的中文名寫出來的地方**。

#### 6.1.1 六層與呼叫路徑

| 層 | 檔 | 重點 |
|---|---|---|
| UI | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:15` | `: xOneStepProcessForm`,`TabPages = 1`,只有三個輸入控件 |
| Pxy | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:34`、`:56` | 只開放 `Execute` 與 `Check`;`Query` 是空殼,永遠回 `(true, 0, "")` |
| Ctl | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:52-70` | 先 `Execute`,**commit 之後**再推兩趟 LDAP |
| PO | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:57-155` | 裸 DAO,自己 `new Database("TA", DbServerType.Oracle)`(`:36`) |
| Model | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd` | 10 張 DataTable,其中 5 張對應 SP 的 5 個 refcursor |

#### 6.1.2 觸發方式

**人工。** 畫面上只有標準的「執行」鈕(`xOneStepProcessForm` 提供), `OFDB003_RefreshPage` 把查詢鈕關掉、執行鈕打開,並把「變更生效日期」預設成 **AP Server 的系統日**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:99-104`)。

**沒有排程、沒有 WindowsService、沒有 timer。** PO 裡確實有一支 `GetExecTime()` 讀 `CTL016.BF_PROC_TIME`(「應執行時間」)(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:358-393`),Ctl 也包了一層(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:516-526`),但 **`OFDB003_Pxy` 沒有對應的方法,UI 也從來沒呼叫它** —— 這條路從用戶端不可達。`CTL016.BF_PROC_TIME` 在本片等於一個**沒有人讀的設定值**(`OFDB005` 的 `REL_PROC_TIME` 同病,見 §6.5)。

> 〔假設〕現場的作法**可能**是「排程系統在 `BF_PROC_TIME` 那個時間提醒人去按」,或由外部排程工具驅動 UI。依據:欄位名叫「處理時間」且有 UI 以外的讀取碼但未接線。repo 內**查不到任何證據**支持它會自動跑。

#### 6.1.3 參數:三個,全部從畫面來

| 參數 | UI 控件 | `SQLOperator` | 送進 SP 的型別 | 空值時 |
|---|---|---|---|---|
| `CHG_EFFECT_DATE` 變更生效日期 | `udatCHG_EFFECT_DATE`(必填) | **`SmallerthanEqual`** | `datiCHG_EFFECT_DATE` `OracleDbType.Date` | 不可能為空(必填) |
| `CHG_DATE` 收件日期 | `udatCHG_DATE`(選填) | `Equal` | `datiCHG_DATE` `OracleDbType.Date` | **代成 `'19000101'`** |
| `BF_CHG_NO` 資料變更書號 | `custBF_CHG_NO_0`(選填) | `Equal` | `striBF_CHG_NO` `OracleDbType.Varchar2` | 空字串 |
| (自動)`iUpdateID` | — | — | `OracleDbType.NVarchar2` | `PermissionInfo[0].UserID` |

錨點:UI 組參數 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:43-48`;PO 綁參數 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:72-78`。

這與 `bms.md §2` 說的「吃 `CHG_EFFECT_DATE` / `CHG_DATE` / `BF_CHG_NO` 三個」完全吻合,本節再補三個細節:

1. **`CHG_EFFECT_DATE` 的語意是「小於等於」,不是「等於」。** UI 用 `SQLOperator.SmallerthanEqual` 塞參數(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:44`)。但送進 SP 的只有一個 `Date` 值,**運算子本身沒有傳給 SP** —— SP 怎麼用這個日期,呼叫端管不著。運算子只在同一支 PO 的 `Check()` 與 `BMS001Chg()` 兩段自組 SQL 裡生效。 **所以「本次會生效哪些單」這件事,呼叫端無法保證與 `Check()` 數出來的一致。**

2. **`CHG_DATE` 為空時代成 `'19000101'`** 而不是 NULL: `DateTimeHelper.StringToDate(strParam == String.Empty ? "19000101" : strParam)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:75`)。`DateTimeHelper.DateToString` 又規定「1900/01/01 回空字串」(`Dev/Common/Source/Utility/TA.Utility/DateTimeHelper.cs:281`),所以 1900/01/01 是全庫公認的「沒有值」。SP 必須自己認得這個哨兵值,呼叫端不另外標記。

3. **`iUpdateID` 用 `NVarchar2`,其他三個用 `Varchar2` / `Date`。** 同一支 SP 混用兩種字元型別; 若 SP 端宣告成 `VARCHAR2`,Oracle 會做隱含轉換。屬觀察,不是錯誤。

#### 6.1.4 生效前會不會檢查「還有沒有沒覆核的」?會,但只是**詢問**,不是阻擋

`DoValidate()`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:33-59`)按下執行前一定會跑:

```
1. validatorManager1.DataValidate()          → 必填檢核
2. 變更生效日期 > AP Server 系統日 ?          → 阻擋:「變更生效日期 不可大於 系統日」
3. 組三個 Parameters
4. PXY.Check(ProcessVDB)                      → 數未覆核筆數
5. 若有例外 → return false(阻擋)
6. 若 ReturnRowCount > 0 → 跳 Warn02 對話框「尚有 N 筆資料未覆核，是否繼續」
      按 OK  → 繼續執行
      按其他 → return false
```

`Check()` 的 SQL(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:315-322`):

```
SELECT COUNT(1) FROM BMS001ACHG
WHERE 1=1
AND BMS001ACHG.Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))
AND SUBSTR(NVL(TRIM(CHG_UPD_DTTM), '19000101'), 1, 8) = '19000101'
-- 再串上 CHG_EFFECT_DATE / CHG_DATE / BF_CHG_NO 三個條件
```

| 卡控 | 時點 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 變更生效日期必填 | 按執行 | 不給執行 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:36` |
| 變更生效日期 > AP 系統日 | 按執行 | 不給執行 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:37-40` |
| `Check` 丟例外 | 按執行 | 不給執行 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:51` |
| 尚有 N 筆未覆核 | 按執行 | 跳 `Warn02`,使用者可按 OK 繼續 | **詢問** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:52-54` |
| SP 回 0 筆 | 執行中 | rollback + 「查無可執行之資料」 | **記錄不擋**(已經跑完了) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:96-104` |
| SP 任一列 `result <> 1` | 執行中 | rollback + 「執行失敗!」 | **阻擋**(整批不生效) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:106-114` |
| LDAP 推送失敗 | **commit 之後** | 訊息改成「執行LDAP更新失敗,請檢查」,**DB 已經生效了** | **記錄不擋** | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:172-180` |

> ⚠ **「未覆核」的判準有兩套,而且對不起來。**`Check()` 用 `Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))`,`'A'` 假設是 Approve 系狀態群(`f_TA_GetEVAStatus` 是 table function,**原始碼不在 repo**,`architecture.md 附錄 B.0`)。但**這個條件只用在計數,沒有傳給 SP** ——SP 收到的只有三個日期 / 單號參數。所以: **使用者在對話框按下 OK 之後,那 N 筆未覆核的單會不會被一起生效,從呼叫端無法判斷,取決於 SP 內部。** 這是本節最重要的一條未解項,標 **〔假設〕缺:DB 連線**。

#### 6.1.5 執行主體:能確定的事

`Execute<T>()`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:57-155`)逐行拆:

| # | 動作 | 錨點 |
|---|---|---|
| 1 | `dbTA.GetStoredProcCommand("s_TA_OFDB003_Excute")`;`CommandTimeout = 0`(**永不逾時**) | `:64-65` |
| 2 | 清空 `Utility.Result` | `:67` |
| 3 | 綁 4 個 IN 參數(§6.1.3) | `:72-78` |
| 4 | 宣告 **5 個 OUT refcursor**:`T_MSG`、`T_BMS001`、`T_OFDB606`、`T_LDAPCHG`、`T_LDAPSTATUSCHG` | `:81-87` |
| 5 | **C# 端開交易** `dbTA.BeginTransaction()` | `:89` |
| 6 | 框架的 log 參數 `AppendLogParameterUpdate` / `AppendLogParameterApprove` **被註解掉** | `:91-92` |
| 7 | `LoadDataSet(cmd, DataEntity, tran, ["OFDB003","BMS001CHG","OFDB606","OFDB003_LDAP","OFDB003_LDAPSTATUS"])` —— 五個 cursor 依序落到五張 DataTable | `:94` |
| 8 | `OFDB003` 表 0 筆 → rollback +「查無可執行之資料」 | `:96-104` |
| 9 | `OFDB003.Select("result<>1")` 有任一列 → rollback +「執行失敗!」 | `:106-114` |
| 10 | 否則 commit,訊息「執行成功,共變更 N 筆受益人資料」,N = `OFDB003` 的列數 | `:118-123` |
| 11 | `finally` 釋放交易 / 連線 | `:148-153` |

**所以下面這幾件事是確定的,不是推測**:

1. **SP 的 DML 跑在呼叫端開的交易裡。** 交易是 C# 用 `dbTA.BeginTransaction()` 開的(`:89`), `LoadDataSet` 把它傳下去(`:94`),commit / rollback 全由 C# 決定。 **這代表 `OFDB003` 真的可以整批回滾** —— 本片大多數批次做不到這點。

2. **成功 / 失敗協定是第一個 cursor。** SP 必須回一個帶 `result` 與 `msg` 兩欄的結果集; `result` 不等於 1 就算失敗。欄名與型別見 `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd`的 `result`「結果」與 `msg`「錯誤訊息」兩個 `msdata:Caption`。

3. **「共變更 N 筆受益人資料」的 N 是第一個 cursor 的列數,不是 SP 回報的影響列數。** 也就是說,SP 每處理一筆就要在 `T_MSG` 吐一列;若 SP 改成只吐一列摘要,畫面上的數字會變成 1。

4. **`T_BMS001`(→ `BMS001CHG` 表)與 `T_OFDB606`(→ `OFDB606` 表)目前無人消費。** 兩者唯一的讀取端是 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:176-303` 的 `EMAIL()` 方法,以及 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:243-500` 的 `EMail()` / `GetOFD681()`—— **這兩大段全部包在 `/* */` 裡**,2022.10.14 由 `Becky(9000011434)` 標註「因新EC已改為自行申請密碼, 故不再更新OFD607A, OFD607相關密碼欄位」。SP 仍然被要求吐這兩個 cursor(否則參數數量對不上),資料撈回來直接丟掉。

5. **`T_LDAPCHG` / `T_LDAPSTATUSCHG` 是活的**,見下一段。

6. **交易沒有逾時保護**(`CommandTimeout = 0`)。一筆大量的生效跑到天荒地老也不會斷, 期間整條 WCF / Remoting 執行緒與 `BMS001ACHG` 的鎖都被佔住。

#### 6.1.6 commit 之後才做的事:同步外部 LDAP

`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:52-70` 的順序是:

```
ExecPOActionToViewVDB(view, m_PO.Execute)   ← DB 交易在這裡就 commit 了
   ↓
UpdateLDAPStatus(result)                     ← 逐列打外部 API
   ↓
UpdateLDAPCustomer(result)                   ← 逐列打外部 API
```

| 方法 | 吃哪個 cursor | 打哪支 API | 失敗時 |
|---|---|---|---|
| `UpdateLDAPStatus` | `OFDB003_LDAPSTATUS` | `LDAPAPIHelper.updatePasswordState(ID_NO, "OFDB003", uid, STATUS)`(無原始碼,從呼叫端反推) | 寫 `INSERT_CALLAPI_FailLog`,累積訊息,**但寄信那行被註解掉**(`:111`) |
| `UpdateLDAPCustomer` | `OFDB003_LDAP` | `updateCustomerIDNumber`(ID 變更)、`updateCustomerInfo`(email / mobile 變更) | 寫失敗 log,**並且真的寄信**(`:177`) |

`UpdateLDAPCustomer` 的失敗信裡有一句很關鍵的作業指引:「更新失敗資料請於OFDB609-網路交易後續處理作業執行『更新LDAP資料』按鈕,若仍執行失敗請洽IT進行查詢。」(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:176`)—— **`OFDB609` 是 `OFDB003` 的補償批次**,住在 `Dev/ATLAS.EC/`,不在本篇範圍,但相依關係要記住(見 §8.3)。

> ⚠ **最容易咬人的一點:LDAP 失敗會把「成功」訊息蓋掉,但 DB 早就 commit 了。**兩支 LDAP 方法失敗時都做 `result.Util.Result.Clear()` 再塞「執行LDAP更新失敗,請檢查」(`:112-113`、`:178-179`)。使用者看到的是一個看起來像失敗的訊息,**但受益人資料已經生效、`CHG_UPD_DTTM` 已經蓋上去了**。這時再按一次執行只會拿到「查無可執行之資料」。正確處置是去跑 `OFDB609`,不是重跑 `OFDB003`。

另外 `UpdateLDAPCustomer` 的三個比較全部是 `row.NEW_XXX != row.ORG_XXX` 的直接字串比較(`:137`、`:147`、`:156`)。typed DataSet 的字串欄位若為 DBNull,取值會丟 `StrongTypingException`;這裡沒有任何 `IsXxxNull()` 保護,只有外層一個 `catch (Exception ex)` 吞掉(`:165-168`)—— **單一列的 null 會讓那一列靜默跳過,不進失敗 log、不進錯誤訊息**。

#### 6.1.7 只能標假設的部分

`s_TA_OFDB003_Excute` 的原始碼**不在 repo**。`architecture.md 附錄 B.0` 說得很清楚:程式呼叫 380 支相異 SP,`DB/SP` + `DB/Function` 只有 106 支腳本,319 支查不到定義。本支就是那 319 支之一(全庫 `DB/` 底下 grep `OFDB003`:0 命中)。

**下面每一條都是〔假設〕,依據列在右邊,要確認只能連 DB 查 `ALL_SOURCE`:**

| # | 假設 | 依據 | 風險 |
|---|---|---|---|
| 1 | SP 會把 `BMS001ACHG` 的 `AFT_*` 欄位寫回 `BMS001A` 與另外 11 張本表 | `bms.md §2` 的證據鏈第 5、6 條:`BMSM006.AfterApprove` 完全沒有回寫 SQL,而 UI 用 `CHG_UPD_DTTM` 判「已生效」 | **哪些欄位對哪些欄位,完全查不到** |
| 2 | SP 會蓋 `CHG_UPD_DTTM` | 同上第 7、9 條:全庫一致用 `TRIM(CHG_UPD_DTTM) IS NULL` 判未生效,而本片以外沒有任何一支程式寫這個欄位 | 高 —— 這是整套機制的關鍵欄位 |
| 3 | SP 自己會過濾「已覆核 + 尚未生效」 | 呼叫端只傳三個日期 / 單號參數,沒傳狀態;而 `Check()` 的條件沒有下放 | **高**,見 §6.1.4 的警告 |
| 4 | 重跑是安全的(第二次會回「查無可執行之資料」) | 若假設 2、3 成立,第一次跑完 `CHG_UPD_DTTM` 已有值,第二次撈不到列 → 第一個 cursor 0 筆 → rollback + 「查無可執行之資料」 | 中 —— **假設 3 若不成立,重跑可能重複生效** |
| 5 | SP 不會自己 commit | C# 端的 commit / rollback 有效 這件事隱含 SP 沒有 `COMMIT`。Oracle 的 SP 若自己 commit,`:118` 的 commit 是空轉、`:101` 的 rollback 也救不回來 | **高** —— 這條錯的話「會 rollback」整個不成立 |
| 6 | `T_OFDB606` 仍然被 SP 填 | 呼叫端還在宣告這個 OUT 參數(`:83`),Oracle 端不填的話參數數量對不上會報錯 | 低 |
| 7 | `CHG_EFFECT_DATE` 在 SP 內是「小於等於」 | UI 用 `SmallerthanEqual`,但運算子沒傳給 SP | 中 |

**明確不能說的話**:不能說「`OFDB003` 只生效已覆核的單」、不能說「`OFDB003` 只生效當日到期的單」、不能說「重跑不會重複生效」。這三句都要 SP 原始碼或 DB 實測才能下結論。

#### 6.1.8 與 `BMSM004` / `BMSM006` 的關係

| 階段 | 誰做 | `BMS001ACHG.STATUS` | `CHG_UPD_DTTM` | 本表(`BMS001A` 等) |
|---|---|---|---|---|
| 開單 | `BMSM004`(只改 ID / 姓名 / 缺件)或 `BMSM006`(改全部) | `Entry*` | 空 | 未動 |
| 驗證 | 同上 | `Verify*` | 空 | 未動 |
| 覆核 | 同上 | `Approve*` | **仍為空** | **仍未動** |
| **生效** | **`OFDB003`** | 不變 | **被蓋上時戳** | **已回寫**〔假設 1〕 |
| 補推 LDAP | `OFDB609`(不在本篇) | 不變 | 不變 | 不變 |

三支的分工用一句話講:**`BMSM004` / `BMSM006` 決定「要改成什麼」,`OFDB003` 決定「什麼時候真的改」。**`bms.md §4` 那兩節的四眼流程走完,資料還躺在 `CHG` 表裡;`BMSM004` / `BMSM006` 的 UI 也是拿 `CHG_UPD_DTTM` 有沒有值來鎖修改與刪除鈕(`bms.md §2` 證據 9),所以 **`OFDB003` 一跑,那張單就再也改不動了**。

反過來,`OFDB003` 對 BMS 的唯一輸入是三個篩選參數,**它不知道也不檢查單子是誰開的、走過幾眼**——`Check()` 那個計數只是給人看的對話框。

#### 6.1.9 缺陷清單(本支)

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `catch (SqlException)` / `catch (Exception)` 直接讀 `tranUpdate.Connection`,而 `tranUpdate` 在 `try` 內才賦值 | `BeginTransaction()` 之前(例如綁參數、取 `PermissionInfo[0]`)丟例外時,真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:132-147` | 高 |
| 2 | `catch (SqlException sqlex)` 在 Oracle 連線上永遠不會命中(`System.Data.SqlClient`) | 死碼,誤導讀者以為有分流 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:132` | 中 |
| 3 | `CommandTimeout = 0` | 無逾時保護,長跑會佔住執行緒與資料表鎖 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:65` | 中 |
| 4 | LDAP 失敗把成功訊息清掉,但 DB 已 commit | 使用者以為整批失敗,實際已生效;重按只會拿到「查無可執行之資料」 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:112-113`、`:178-179` | **高** |
| 5 | `UpdateLDAPCustomer` 逐列 `catch` 後什麼都不做 | 單列的 null / 例外靜默跳過,不進 log 也不進訊息 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:165-168` | 高 |
| 6 | `UpdateLDAPStatus` 的寄信被註解,只留 `result` 訊息 | 密碼狀態同步失敗沒有人會收到通知 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:111` | 中 |
| 7 | `Check()` 與 `BMS001Chg()` 對同兩個參數用不同的 `IsDate` 旗標(`false` vs `true`),產生的 SQL 一個是字串比較、一個是 `TO_CHAR(...,'YYYYMMDD')` 比較 | 同一組輸入在兩支方法裡的語意不同;`Check()` 那條拿 `DATE` 欄位直接跟 `'yyyyMMdd'` 字串比,靠 Oracle 隱含轉換 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:320-322` 對照 `:169-170` | 中 |
| 8 | `AddParam()` 把參數值直接字串串接進 SQL(`"'" + strValue + "'"`) | `BF_CHG_NO` 來自畫面輸入,是字串串接進 SQL 的路徑 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:466-481` | 中 |
| 9 | `BMS001Chg()`、`GetOFD681()`、`GetExecTime()` 三支方法沒有任何可達的呼叫端 | 死碼;`GetExecTime` 讓人以為 `CTL016.BF_PROC_TIME` 有作用 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:164-174`、`:358-393`、`:400-437` | 中 |
| 10 | `Ctl.Execute` 裡 `OFDB003ModelVDB model = TransferViewToModel(result);` 取了值卻不用 | 每次執行多做一次整包 VDB 轉換 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:57` | 低 |
| 11 | 把 `AddResultRow(true, ...)` 包在自己的 `try/catch` 裡再 `HandleBusinessException` | 沒有意義的防禦,讀者會以為這行會失敗 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:121-128` | 低 |
| 12 | 127 行的密碼產生 / 回寫 `OFD607A` 程式碼以 `/* */` 留在 PO,258 行留在 Ctl | 兩處加起來近 400 行死碼,且含明碼密碼處理邏輯 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:176-303`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:243-500` | 中 |

### 6.2 `OFDB004` 基金複製(推測)—— 16 張明細,本片第二重

**先回答最常被問的一題:`OFDB004` 不是日結。**

它是「**新基金上線時,把一檔既有基金的 16 張衍生設定表整包複製到新基金**」的一次性工具。四條互相獨立的證據:

| # | 證據 | 錨點 |
|---|---|---|
| 1 | PO 的 XML 註解直接寫 `/// 基金複製`,方法註解寫「複製基金或受益人(依傳入 model 內是基金或受益人決定)」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:31-34`、`:353-357` |
| 2 | 畫面只有兩個輸入:`custFromFund_ID_0` 與 `custToFund_ID_0`,兩者相同就擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:39-42` |
| 3 | 畫面上一整段固定說明文字:「執行完成後請至下列程式,增修或覆核已複製的各項資料」+ 13 支 `OFDM*` 畫面清單 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:93-108` |
| 4 | 執行前逐表檢核「目的基金在這 13 張表上**已經有資料**」並把每一張都列成警示 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:102-284` |
| 5 | 沒有任何日期參數。日結批次不可能沒有作業日 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:129-134` 只塞四個參數 |

日結(過帳)在 ATLAS 是 `OFD303A.POST_CTL_CODE` 那條線,由別的批次負責;本片只有 `OFDB001` / `OFDB041` / `OFDB281` 讀它當前置條件,沒有任何一支在寫它。

#### 6.2.1 觸發與參數

**人工按「執行」。** `TabPages = 1`,無查詢頁(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:85`)。

| 參數 | 來源 | 用途 |
|---|---|---|
| `FromFund_ID` | `custFromFund_ID_0` | 來源基金 |
| `ToFund_ID` | `custToFund_ID_0` | 目的基金 |
| `D_Type` | 目的基金下拉的 `DIVIDEND_TYPE` | 收益分配方式,只在建自轉自的 `OFD085A` 列時用 |
| `AFEE_TYPE` | 目的基金下拉的 `AFEE_TYPE`(2021.06.21 由 `Hanna 9000008847` 加) | CDSC 判斷 |

錨點:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:129-134`;PO 取值 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:366-370`。

#### 6.2.2 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選來源基金後 | `OFD081A.STATUS LIKE '3%'`(已覆核) | 訊息「來源基金尚未覆核」+ 清掉選擇 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:173-193`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:317-334` |
| 選目的基金後 | 同上 | 訊息「複製基金尚未覆核」+ 清掉選擇 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:195-215` |
| 按執行 | 來源 = 目的 | 「From基金 和 To基金 相同」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:39-42` |
| 按執行 | 兩檔基金 `FUND_CURRENCY` 不同 | 「複製的基金其計價幣別必須相同」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:46-52` |
| 按執行 | 目的基金在 13 張表任一張已有資料 | 逐張列出「本基金[X]於 (OFDMnnn)… 已有資料」 | **阻擋**(進 `ValidateErrList`,`Show()` 後 `e.Cancel = true`) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:54-74`、`:119-128` |
| 執行中 | `ApplicationException`(EVA 基底丟的) | 訊息把「新增」改成「執行」 | **阻擋** + 雙交易 rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:715-721` |

> **13 張檢核表與 16 張複製表不是同一組。** 檢核跑 `OFD038A` / `OFD070A` / `OFD075` / `OFD077` / `OFD085A` / `OFD129A` / `OFD193A` / `OFD194A` / `OFD196A` / `OFD213A` / `OFD214A` / `OFD215A` / `OFD260A`共 13 張(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:113-270`);複製寫 16 張。**`OFD074` / `OFD076` / `OFD261A` 三張會被寫入,卻不在檢核清單裡**—— 目的基金在這三張表上已有資料時不會被擋。附錄 E 記一筆。

> ⚠ **兩個下拉的「只列已覆核基金」過濾器被註解掉了。**`custFromFund_ID_BeforeGetDataSource` 與 `custToFund_ID_BeforeGetDataSource` 兩個事件的本體各只剩一行註解 `//this.custFromFund_ID_0.Filter = "[Status] LIKE '3%' ";`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:159-171`), 2009.04.09 由 `lichyu` 改成「不過濾,改成選了之後跳錯誤訊息」。事件還掛著、方法還在,但**是空方法** —— 讀 code 的人會以為有過濾。

#### 6.2.3 寫入順序(這是本支最難懂的部分)

`Execute<T>` 的前半段(`:358-619`)在記憶體裡把 `tofundmodel` 整包改好:先用 `GetMaintainData` 把來源基金的主明細撈進來(`:376`),再逐表把 `FUND_ID` 換成目的基金、`STATUS` 與 13 個 EVA 欄位清空(`SetDataRowSysParam`,`:750-765`)。後半段(`:621-736`)才真正寫 DB,**分成六段,順序有意義**:

| 段 | 動作 | 表 | 方法 | 錨點 |
|---|---|---|---|---|
| 0 | 開**兩個**交易:`dbProduct`(TA 庫)與 `dbPTPF`(權限 / 待辦庫) | — | `BeginTransaction` × 2 | `:628-629` |
| 1 | MultiRow **更新舊有資料**(`CopyPKey = FUND_ID`,把同批其他列一起更新) | `OFD038A`、`OFD070A`、`OFD214A`、`OFD215A` | `ExecUpdate` → `OFDB004_PO1.Copy` | `:633-638` |
| 2 | MultiRow **新增**(dataid 相同) | `OFD193A`、`OFD194A`、`OFD196A`、`OFD213A` | `ExecAddMultiRows` → `OFDB004_PO1.Add` | `:641-650` |
| 3 | 非 MultiRow 新增(dataid 各不相同) | `OFD129A` | `ExecAdd` → `base.Add` 逐列 | `:653-656` |
| 4 | 短線費主明細,**只有在 `OFDM260` 恰好 1 列時才做** | `OFD260A` + 明細 `OFD261A` | `base.Add` | `:659-668` |
| 5 | `OFD085A` 特別處理:先把目的基金的列**從記憶體移走**、用 `ExecUpdate` 寫「其他基金指向本基金」的列;再把移走的列 `ImportRow` 回來、用 `ExecAddMultiRows` 寫入 | `OFD085A`(兩次) | `ExecUpdate` + `ExecAddMultiRows` | `:670-693` |
| 6 | 主明細複製 | `OFD076` + `OFD077`、`OFD074` + `OFD075` | `CopyDetail` × 2 | `:695-708` |
| 7 | 兩個交易一起 commit | — | — | `:710-711` |

`OFDB004_PO1` 是一個只有 36 行的內部類別,唯一的作用是借 `BaseMultiRowEVADaoPO.Copy`:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO1.cs:15-34`。它在建構子裡依表名決定 `CopyPKey`:一般表用 `FUND_ID`,**只有 `OFD085A` 用 `SWITCH_FUND_ID`**(`:30-33`)。

> **段 4 的 `if (OFDM260.Rows.Count == 1)` 是寫死的。** 來源基金若在 `OFD260A` 上有 0 列或 2 列以上, 短線費設定**整段不複製,而且不提示** —— 卡控結果屬「過濾(無提示)」。錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:660`。

> **段 4 拿 `"OFDM233"` 當權限識別字去呼叫 `UseCaseSecurity.SetPermissionInfo`, 但實際寫的表是 `OFD260A` / `OFD261A`。** 註解說明這是 2008.12.15 `Howard` 為 ID:6189 加的,沿用舊畫面代號。錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:662`。

#### 6.2.4 撈來源資料時改寫的 SQL

`BeforeGetMaintainData` 事件(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:967-1013`)對七張表換掉框架產生的 SQL:

| 表 | 改寫方式 | 錨點 |
|---|---|---|
| `OFD081A` | **整個換成 `SELECT '<來源基金>' AS FUND_ID FROM dual`**,註解寫「此 MasterTABLE 只用來騙過 evapo 用的」 | `:976-978` |
| `OFD193A` / `OFD194A` / `OFD196A` | 原 SQL 後面加 `AND FEE_TYPE = '1'` | `:979-983` |
| `OFD077` | 原 SQL 後面加 `AND SEAL_TYPE = '3'` | `:994-996` |
| `OFD085A` | 原 SQL 後面 `OR SWITCH_FUND_ID = '<來源>'`,再 `UNION` 一段撈「任何指向來源基金的基金,其全部 `OFD085A` 列」 | `:998-1007` |
| `OFD038A` / `OFD070A` / `OFD074` / `OFD076` / `OFD213A` / `OFD214A` / `OFD215A` / `OFD260A` | 交給 `BuildSQLString()` 完全重組 | `:984-993`、`:1021-1141` |

`BuildSQLString()` 裡有幾條值得記:

- `OFD038A`:撈的是「來源基金所屬**基金群組**底下的全部列」,不是只有來源基金自己 (`WHERE FUND_GRPCD IN (SELECT FUND_GRPCD FROM OFD038A WHERE FUND_ID = …)`,`:1031`)。

- `OFD070A`:同理,撈「同一組 `AGENT_ID || AGENT_CODE`」的全部列(`:1041`)。

- `OFD213A`:**不是單純複製**。它 `UNION` 兩段:一段從 `OFD094A` 取來源基金保管銀行的 `SUBSTR(CUS_BANK_BRH,1,3)` 前三碼當 `NON_FEE_BANK`,另一段取 `OFD213A` 既有列但排除前一段已涵蓋的(`:1077-1103`)。幣別 `CRNCY_CD` 直接取目的基金的 `OFD081A.FUND_CURRENCY`。

- 上述每一條都是 `string.Format` 把 `m_FromFundID` / `m_ToFundID` **字串串接**進 SQL,沒有參數化 (`:1031`、`:1041`、`:1077`、`:1088`、`:1100-1103`)。同樣情形在 `Check()` 的`GetSQLByCheckFund()`(`:293-302`)與 `:161-164` 的 `OFD085A` 檢核。

#### 6.2.5 `OFD085A` 為什麼「難搞」

`OFD085A` 是「境內基金轉換設定」,一列代表「從 `FUND_ID` 轉到 `SWITCH_FUND_ID`」。複製一檔基金時要同時處理三種列:

| 種類 | 處理 | 錨點 |
|---|---|---|
| 來源基金當**轉出方**(`FUND_ID = 來源`) | 複製一份,`FUND_ID` 換成目的基金;若原本是自己轉自己,`IS_SHORT_FEE` 強制 `'Y'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:469-519` |
| 來源基金當**轉入方**(`SWITCH_FUND_ID = 來源`) | 複製一份,`SWITCH_FUND_ID` 換成目的基金,`dataid` 保持與原列相同 | `:520-554` |
| **自己轉自己**(目的 → 目的) | 若不存在就新建一列,`CreateOFD085Row` 給一整組寫死預設值 | `:564-584`、`:886-918` |

`CreateOFD085Row` 的寫死預設值(`:905-914`)是本支最集中的一批魔術常數:

| 欄位 | 寫死值 | 註解裡的值域 |
|---|---|---|
| `SWITCH_DATE_TYPE` | `"2"` | 1 交易日 / 2 付款日 / 3 淨值日(`CTL014` 192) |
| `SWITCH_DAY` | `0` | T+N 的 N |
| `ST_REMIT_TYPE` | `"1"` | 1 匯費+金資 / 2 金資 / 3 匯費(`CTL014` 027) |
| `ST_REMIT_CD` | `"1"` | 1 公司 / 2 保管銀行 / 3 受益人(`CTL014` 165) |
| `IS_SHORT_FEE` | `"N"` | Y 收 / N 不收(`CTL014` 016) |
| `SWITCH_DISC` / `EC_SWITCH_DISC` | `-1M` | 折數 |
| `SWITCH_RATE` / `EC_SWITCH_RATE` | `0M` | 固定費率 |
| `SWITCH_OPEN_MRK` | `"Y"` | 開放轉入 |
| `DIV_REMIT_TYPE` / `DIV_REMIT_CD` | `"1"` / `"1"`,**只有在 `FUND_ID == SWITCH_FUND_ID` 且 `DIVIDEND_TYPE <> '4'` 時** | `:892-901` |

最後一條很重要,`OFDB281` 直接依賴它:**收益分配專戶資料 `DIV_ACC_NO` / `DIV_REMIT_TYPE` / `DIV_REMIT_CD`放在「自己轉自己」那一列上**。這解釋了 §6.3 為什麼 `OFDB281` 會用同一個基金代碼當兩個參數呼叫檢核。

`CDSC_TRAN_CD` 一律設成一個空白字元 `" "`(`:514`,2021.06.17 `hanna 9000008847`),`SWITCH_ACC_NM_E` / `DIV_ACC_NM_E` 為 null 時代成 `" "`(`:502`、`:508`)—— 不是空字串,是一個空白。

#### 6.2.6 失敗處理、rollback 與重跑

| 面向 | 行為 | 錨點 |
|---|---|---|
| 失敗處理 | 兩層 `catch`:`ApplicationException`(EVA 基底的業務例外)訊息把「新增」換成「執行」;其他例外訊息「執行失敗,請檢查 / 訊息:{0}」 | `:715-730` |
| rollback | **兩個交易一起 rollback**(`tran` 與 `tranptpf`) | `:717-718`、`:724-725` |
| **rollback 的破口** | `catch` 直接 `tran.Rollback()`,而 `tran` 在 `try` 內第一行才賦值。**`dbProduct.BeginTransaction()` 本身失敗(DB 不通)時是 `NullReferenceException`**,真正的錯誤被蓋掉;`finally` 的 `tran.Dispose()` 也會再炸一次 | `:623-628`、`:717`、`:733` |
| 重跑 | **技術上可以按第二次,但一定會被 §6.2.2 的「已有資料」檢核擋下來** —— 除非目的基金剛好落在那三張沒被檢核的表(`OFD074` / `OFD076` / `OFD261A`) | `:113-270` |
| 順序相依 | 與本片其他批次**無相依**。與外部的相依是「兩檔基金都要先在 OFD 的 M 畫面建好並覆核」 | — |
| 執行後 | 複製出來的資料 `STATUS` 與 13 個 EVA 欄位全被清空,**必須人工到 13 支 `OFDM*` 畫面重新覆核** | `:750-765` + `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:93` |

> ⚠ **`Execute<T>` 回傳的是 `mModelTo`(新 new 出來的那顆),不是傳進來的 `mModel`。**`T mModelTo = (T)Activator.CreateInstance(typeof(T));`(`:363`)之後所有結果都寫在 `tofundmodel` 上,最後 `return mModelTo;`(`:738`)。呼叫端 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB004_Ctl.cs:50-54`走 `ExecPOActionToViewVDB`,吃的是回傳值,所以行為正確 —— 但這是全片唯一一支這樣寫的 PO,任何人照別支的習慣改成 `return mModel;` 就會靜默吃掉所有結果訊息。

### 6.3 `OFDB281` 收益分配受益人資料產生作業 —— 與 `OFDM281` 同一張表

中文名有明確出處:UI 檔的類別註解直接寫「受益分配受益人資料產生作業」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:13-15`),PO 的類別註解寫「受益分配受益人資料產生作業」(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:29-31`)。 **本片 18 支裡唯一有官方中文名的一支。**

> ⚠ **`OFDB281.cs` 與 `OFDB281.Designer.cs` 是 UTF-16LE 編碼**(BOM `FF FE`),整個 `Dev/ATLAS.OFDB/` 底下只有這兩個檔如此。用 UTF-8 或 cp950 開會看到亂碼。附錄 E 記一筆。

#### 6.3.1 與 `OFDM281` 的關係

`OFDB281_PO` 的 `xTableMapping` 是 `new xTableMapping("OFD281A", "OFDM281")`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:41`),明細是 `new xTableMapping("OFD287A", "OFDM281_Detail")`(`:46`)—— **實體表與 vdb 名都跟維護畫面 `OFDM281` 撞名**。

| 面向 | `OFDM281`(維護,不在本篇) | `OFDB281`(本篇) |
|---|---|---|
| 對 `OFD281A` 做什麼 | 建檔與四眼 | **只讀 `PROCESS_CODE` 當前置條件**;寫入交給 SP |
| 對 `OFD287A` 做什麼 | 明細維護 | 透過 SP 產生 / 刪除 |
| 四眼 | 走 | **不走**。`OFDB281_PO` 雖然繼承 `BaseEVADaoPO`,只掛了三個 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 事件去換 SQL,從不呼叫 `Add` / `Update` |

**實務影響:改 `OFD281A` 的欄位要同時看 `OFDM281Model.xsd` 與 `OFDB281Model.xsd` 兩份 xsd。**

#### 6.3.2 三種執行功能

`uoptExecuteType` 單選鈕,值 `"0"` / `"1"` / `"2"`:

| 值 | 功能 | 前置檢核 | 檢核方法 |
|---|---|---|---|
| `0` | 產生分配資料 | `PROCESS_CODE` 不可已是 `'1'`,否則「該收益分配資料已產生,請執行 "重新產生分配資料" 功能或 "刪除分配資料" 功能。」 | `QueryIsExist` |
| `1` | 重新產生分配資料(刪除後重新產生) | `PROCESS_CODE` 必須是 `'0'` 以外,否則「該收益分配資料尚未產生,請執行 "產生分配資料" 功能。」 | `QueryDeleteData` |
| `2` | 刪除分配資料 | 同上 | `QueryDeleteData` |

三種功能都會再跑一次 `Check_PROCESS_CODE`:`PROCESS_CODE = '4'` 就整個擋掉,訊息「該收益分配資料已結算確認(OFDB284),不得再［產生／重新產生／刪除］分配資料。」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:66-70`)。

#### 6.3.3 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢 | `PROCESS_CODE` 與功能別不符 | `Warn01` 訊息 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:45-70` |
| 按查詢 | 已結算確認(`'4'`) | `Warn01` 訊息 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:66-70` |
| 按執行(功能 1 / 2) | `Check_DIV_ACC_NO` 查 `OFD085A` 的 `DIV_ACC_NO` / `DIV_REMIT_TYPE` / `DIV_REMIT_CD` 三欄是否都有值 | `Warn03`「請先確認「境內基金轉換設定維護作業(OFDM085A) 」已輸入收益分配專戶資料,請確定仍要繼續?」按 Yes 才繼續 | **詢問** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:132-140` |
| 按執行 | 固定提醒 | `Warn03`「請務必先執行「無配息帳號受益人名冊列印作業(OFDR287)」確認受益人均已提供有效之配息帳號,請確定仍要繼續產生本次收益分配資料?」 | **詢問** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:144` |
| 按執行 | `Check_CTL_CODE` 查 `OFD303A.POST_CTL_CODE` | `Error01`「分配基準日尚未完成「申購／贖回／定額」日結轉作業,不得產生收益分配資料。」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:174-177`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:247-273` |
| 按執行 | 執行功能未選 | 「執行功能 為必填欄位」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:213-215` |
| 執行中 | SP 的 `strMsg` 出參有值 | rollback + 把 SP 訊息原樣顯示 | **阻擋** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:413-418` |

> ⚠ **`Check_DIV_ACC_NO` 被呼叫時把同一個基金代碼傳了兩次**:`pxy.Check_DIV_ACC_NO(this.custFUND_ID_0.Value.Trim(), this.custFUND_ID_0.Value.Trim())`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:134`),而方法簽名是`Check_DIV_ACC_NO(string FUND_ID, string SWITCH_FUND_ID)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:212`)。看起來像 bug,**但交叉 §6.2.5 之後可以確定是刻意的** ——收益分配專戶資料就是放在 `OFD085A` 的「自己轉自己」那一列上(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:892-901` 只在 `FUND_ID == SWITCH_FUND_ID` 時才填`DIV_REMIT_TYPE` / `DIV_REMIT_CD`)。**不要「修」這一行。**

> ⚠ **三支檢核方法的 `catch` 全部 `return true`(放行)。**`IsClose`(`:88-92`)、`Check_PROCESS_CODE`(`:124-128`)、`QueryIsExist`(`:163-167`)、`QueryDeleteData`(`:200-205`)、`Check_DIV_ACC_NO`(`:235-239`)、`Check_CTL_CODE`(`:268-272`)—— 六支都是「查詢炸了就當通過」。`Check_CTL_CODE` 更進一步:**查不到 `OFD303A` 的列也回 `true`**(`:259-266` 只有 `POST_CTL_CODE == "N"` 才回 `false`),也就是「基金在那天根本沒有過帳控制列」等於「已過帳」。附錄 E 記兩筆。

#### 6.3.4 執行主體

`Execute<T>`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:381-456`)呼叫`s_TA_OFDB281_Excute`,八個 IN 參數 + 一個 `strMsg` OUT:

| 參數 | 來源 |
|---|---|
| `iFUND_ID` / `iYEARS` / `iISSUE_CODE` / `iBASE_DATE` | 畫面 |
| `iExecuteType` | 0 產生 / 1 重新產生 / 2 刪除 |
| `iUser` | `UpdateID` |
| `iPROVIDE_DATE` / `iSWITCH_DATE` | 畫面(給付日 / 轉申購日) |
| `strMsg`(OUT,`Varchar2(1000)`) | SP 的錯誤訊息;非 null 就 rollback |

`CommandTimeout = 0`,註解直接寫「此程式讓它永久跑」(`:391`)。交易由 C# 開(`:392`),SP 參與同一交易 —— 與 `OFDB003` 同型,**可以 rollback**〔同樣假設 SP 不自己 commit〕。

> ⚠ **`ExecuteNonQuery` 的回傳值收了卻不檢查。** `int i = dbTA.ExecuteNonQuery(cmd, tran);`(`:411`)之後原本的 `if (i <= 0) { rollback … }` **整段被註解掉**(`:419-426`,連 `//i = 1;` 這行都留著),現在只靠 `strMsg` 判成敗。SP 若忘了設 `strMsg`,不管影響幾列都算成功,`i` 還被當成`AddResultRow(true, i, …)` 的筆數回給畫面(`:430`)。

失敗處理與 rollback:`catch (SqlException)` 是死碼(Oracle 不會丟);`catch (Exception)` 的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉**(`:446`)—— 例外不會進框架 log,只剩畫面上一行 `ex.Message`。而且兩個 `catch` 都直接 `tran.Rollback()`,`tran` 可能是 null(同 §6.2.6 的破口)。

#### 6.3.5 重跑與順序相依

| 面向 | 行為 |
|---|---|
| 重跑 | **設計上就支援**:功能 1「重新產生」等於刪除後重跑,功能 2「刪除」把資料清掉。三種都靠 `OFD281A.PROCESS_CODE` 當閘門 |
| 上游 | `OFD303A` 的日結轉(申購 / 贖回 / 定額)必須完成;`OFD085A` 的收益分配專戶必須設好;建議先跑報表 `OFDR287` 確認配息帳號 |
| 下游 | `OFDB284` 結算確認(不在本篇)→ 一旦 `PROCESS_CODE = '4'`,本支三種功能全部鎖死 |
| 再下游 | `OFDB286` 退匯 → `OFDB287` 重匯(§6.12) |

> 被註解掉的 `WITHHOLD_CODE` 檢核值得單獨記一筆:PO 裡有一支 `WITHHOLD_CODE(FUND_ID, BASE_DATE)`(`:280-320`)與一支 `ChkWITHHOLD_CODE<T>`(`:321-…`),兩支都查「`OFD287A` join `BMS001A` 且 `TRIM(BMS001A.WITHHOLD_CODE) IS NULL`」(`:299`、`:343`),Ctl 與 Pxy 也都包好了(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB281_Ctl.cs:157-167`、`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB281_Pxy.cs:90`), **但 UI 的呼叫整段被註解**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:150-156`, 訊息「該收益分配資料中,有未輸入[受益人扣繳類別]之受益人,不得［產生／重新產生］分配資料。」還留著)。 **完整的六層都在、只有最上面那一行被 mark 掉 —— 這條卡控現在不存在。** 同一支 UI 的 `:103-129` 另有 27 行被註解的 `PROCESS_CODE` / `IsClose` 前置檢核。

### 6.4 `OFDB019A` / `OFDB019B` CRS 申報(推測)—— 成對命名的一對,差別比想像中小

兩支的命名是同一組數字加上 `A` / `B` 後綴,`architecture.md §2.1` 說這種後綴通常代表同一個功能的兩個階段。實際比對完全吻合:**`A` 產出資料進 DB,`B` 把 DB 的資料轉成 XML 檔下載。**

CRS = Common Reporting Standard(共同申報準則)。依據:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:41` 的註解「訊息類型[CRS701: 新增資訊 CRS702: 刪除已申報資訊 CRS703: 無(應申報帳戶 及 無資訊帳戶) CTL014(690)]」,以及 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:163` 輸出的`<CRS_OECD version="2.0" xmlns="urn:oecd:ties:crs:v2" …>`。

#### 6.4.1 兩支的差異(逐行比對結果)

把兩支 PO 的畫面代號正規化後做 diff,**結構完全相同,實質差異只有五處**:

| # | 差異 | `OFDB019A` | `OFDB019B` | 錨點 |
|---|---|---|---|---|
| 1 | 呼叫的 SP | `S_TA_OFDB019A_EXECUTE` | `S_TA_OFDB019B_EXECUTE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:66` / `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:73` |
| 2 | 執行前先清 DataSet | 無 | 清 `CRSP001_006_DATA` / `CRSP001` / `CRSP002` / `CRSP002_1` / `CRSP002_2` / `CRSP004` / `CRSP006` 七張 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:63-69` |
| 3 | SP 的輸出 | 只有 `strMsg`(OUT `Varchar2 3000`),用 `ExecuteNonQuery` | `strMsg` + **6 個 refcursor** `C_RES`~`C_RES5`,用 `LoadDataSet` 落到 6 張表 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:85`、`:91` / `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:93-98`、`:103` |
| 4 | 訊息編號的年度 | 取畫面的 `YEARS` 參數 | **寫死 `'2019'`** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:147-148` / `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:159-160` |
| 5 | 一處參數綁定名 | `AddInParameter(cmd91, "YEARS", …)` | `AddInParameter(cmd91, ":YEARS", …)`(**多一個冒號**) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:247` / `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:260` |

其餘上百行差異全部是**空白**(`NVL(PROC_CODE,' ')` 後面一個空格 vs 兩個空格)。兩支 PO 各 552 / 565 行,**是複製貼上的分身**,與 `architecture.md §3.2` 講的`MultiRow4EyesPO` / `MultiRowEVAPO` 同一種病。

> ⚠ **差異 4 是本片最直接的一顆地雷。** `OFDB019B` 產生「訊息編號」(`MESSAGE_REF_ID`)的字串是`'TW' || '2019' || 'TW-86385617-' || TO_CHAR(SYSDATE,'YYYY-MM-DD') || '-T' || TO_CHAR(SYSDATE,'HH24:MI:SS')`—— 年度寫死 `'2019'`,而同一段在 `OFDB019A` 是 `GetParamValue(mModel,"YEARS")`。2020 年以後在 `OFDB019B` 這一段產出來的訊息編號年度永遠是 2019。`TW-86385617` 是公司識別碼〔客戶特定〕。

> ⚠ **差異 5:`AddInParameter(cmd91, ":YEARS", …)` 多了一個冒號。**其他 30 幾處綁定一律不帶冒號。Oracle 端要不要冒號取決於 `Database`(無原始碼,從呼叫端反推)怎麼處理;**若它不幫忙去掉,這個參數就綁不上,那段 `FUNC = 91` 的查詢會丟 `ORA-01008 未繫結所有變數`**。標**假設**,要實測才能確定。

#### 6.4.2 `OFDB019A`:產出 / 刪除 CRS 申報資料

觸發:人工按執行。參數五個,全部從畫面來:

| 參數 | 控件 | 說明 |
|---|---|---|
| `EXE_TYPE` | `uoptEXE_TYPE`(0 產出資料 / 1 刪除資料) | 預設 0 |
| `YEARS` | `umskYEARS` | 申報年度 |
| `MESSAGE_REF_ID` | `ucomMSG_NO` | 訊息編號 |
| `MESSAGE_TYPE` | `ucomMSG_TYPE` | `CRS701` / `CRS702`(`CRS703` 被隱藏) |
| `CORR_MESSAGE_REF_ID` | `ucomSRC_MSG_NO` | 原訊息編號(`CRS702` 用) |

錨點:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:116-121`;`CRS703` 被隱藏的那一行:`this.ucomMSG_TYPE.Rows[3].Hidden = true;`(`:42`)—— **用位置索引 `[3]` 取下拉列,下拉的來源是 `CTL014` 的 `690`,順序一改就隱藏錯的那一項**。附錄 E 記一筆。

`GetCRSP001<T>` 是一支巨大的 `switch`,用 `FUNC` 參數切十幾種查詢(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:133-483`),UI 依情境呼叫 `FUNC` =`91` / `92` / `94` / `95` / `96` / `97` / `98` 等。這些是前置卡控:

| FUNC | 查什麼 | 擋什麼 | 錨點 |
|---|---|---|---|
| `98` | 該年度 `CRS701` 的資料是否已存在 | 「{年度}年申報資料已存在,不可重複產出」 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:166-215` |
| `92` / `97` | 最後一筆是否為未取消、且 `MESSAGE_TYPE = 'CRS702'` 且 `REPORT_STATUS = '1'` | 同上分支 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:180-215` |
| `96` | 該年度 `CRS701` / `CRS703` 的最後一筆狀態 | 「{年度}年尚無已申報資料,不可執行刪除」 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:233-252` |
| `91` | 是否已有「刪除已申報」的未申報資料 | 「已有刪除已申報資料之資料,不可重複新增!!」 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:256-270` |
| — | `MSG_TYPE = CRS702` 但原訊息編號空白 | 「[訊息類型]選擇 CRS702(刪除已申報資訊),[原訊息編號]不可空白」 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:229` |

全部是 **阻擋**(進 `ValidateErrList`)。

> ⚠ **`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:194-199` 的規格註解裡留了一段 T-SQL**:`SELECT TOP 1 MESSAGE_REF_ID FROM CRSP001 WHERE YEARS = '2020' ORDER BY …`。註解而已,不影響執行,但它與註解下方實際跑的 Oracle 查詢**不是同一條**(實際是 `MAX(MESSAGE_REF_ID)`),而且年度寫死 `'2020'`。讀規格會被誤導。

執行主體(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:57-126`):`CommandTimeout = 0`;C# 端開交易;`strMsg` 非 null 就 rollback + 把 SP 訊息顯示,否則 commit + `AddResultRow(true, 1, "")`。**`ExecuteNonQuery` 的回傳值直接丟掉**(`:91`),成功筆數固定寫 `1`(`:102`)—— 畫面上永遠看不到實際處理幾筆。

#### 6.4.3 `OFDB019B`:下載 / 刪除 XML

執行功能三選一,但程式用的是 `CheckedIndex + 2`:

| `CheckedIndex` | `+2` 之後 | 功能 |
|---|---|---|
| 0 | 2 | 下載 xml 檔案 |
| 1 | 3 | 刪除 xml 檔案 |

錨點 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:78`、`:149`、`:666`。 **`+2` 是寫死的偏移,只因為 SP 的 `EXE_TYPE` 值域接在 `OFDB019A` 的 0/1 後面。** 單選鈕再多一項,整段判斷就錯位。

XML 產生在 **UI 層**,`AfterExecuteButtonClicked` 逐列 `StreamWriter` 寫檔(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:136-674`):

| 面向 | 行為 | 錨點 |
|---|---|---|
| 輸出路徑 | `utxtFilePath` 使用者自選,程式只把結尾的 `\` 正規化,**不檢查目錄是否存在** | `:140-144` |
| 檔名 | `CRSP001.XML_FILE_NAME` + `.xml`,一張基金訊息編號一個檔 | `:157-158` |
| 編碼 | `Encoding.UTF8` | `:158` |
| 格式 | `<CRS_OECD version="2.0" xmlns="urn:oecd:ties:crs:v2" xmlns:cfc="…TWcommontypesfatcacrs:v2" xmlns:stf="…crsstf:v5">`(2021.04.08 `tain_you` 調整) | `:162-163` |
| 刪除 | `File.Exists` 後 `File.Delete`,但 `strXML_FILE_NAME` 在這條分支上**是空字串** | `:666-670` |
| 覆寫 | `new StreamWriter(path, false, …)` —— **同名檔直接覆蓋,不提示** | `:158` |

> ⚠ **「刪除 xml 檔案」這條分支是壞的。** `strXML_FILE_NAME` 宣告在方法開頭初始化為 `""`(`:138`),只有在「下載」那條分支的迴圈裡才會被賦值。走「刪除」分支時它永遠是空字串,`File.Exists(path + "" + ".xml")` 找的是一個叫 `.xml` 的檔 —— **永遠刪不到東西,而且不報錯**。錨點 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:138`、`:666-670`。嚴重度:中。

> ⚠ **`XOFDB019B_AfterExecuteButtonClicked`:670 行的死碼。**`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:675-1344` 是一整支以 `X` 開頭的處理常式,內容是 CRS XML v1.0 格式的完整產生邏輯(`urn:oecd:ties:crs:v1`)。`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.designer.cs:500` 只掛了不帶 `X` 的那支, **這 670 行沒有任何呼叫端**。整個檔 1,348 行,一半是死的。活的那支裡面另有 `:468-664` 共 197 行被 `/* */` 包住(同樣是 v1.0 版本),以及 `:823-844`、`:882-904`、`:1002-1026` 三段被註解的 `ControllingPerson` / `PaymentAmnt` 欄位。

#### 6.4.4 兩支的共同問題

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `NVL(PROC_CODE,' ') <> 'D'` —— 用 `NVL` 包起來是對的,但同檔另有多處直接寫 `PROC_CODE = ' '` 的比較 | 語意不一致;若欄位存 NULL 而非空白,兩種寫法結果不同 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170` 對照 `:243` | 中 |
| `GetCRSP001` 的 `switch` 超過 350 行、十幾個 `FUNC` 分支,分支值散在 UI 各處 | 沒有任何常數定義,`FUNC` 是字面字串;改一處要全檔對 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:133-483` | 中 |
| 兩支的 `catch` 都先 `tranUpdate.Rollback()` 再判 null | `BeginTransaction` 失敗時 `NullReferenceException` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:104-109` | 高 |
| 兩支 552 / 565 行,實質差異五處 | 任何修正要記得改兩份 | 見 §6.4.1 | 高 |

### 6.5 四支未移轉的 SQL Server 批次:`OFDB001` / `OFDB005` / `OFDB011` / `OFDB161`

§0.2 已經證明這四支的 `dbTA` 恆為 null、SQL 是 T-SQL。這裡只補各自的業務意圖與參數, **因為它們現況跑不起來,卡控與失敗處理都不具實務意義**。

| 畫面 | 業務意圖(推測) | 主表 | SP | 參數 | 錨點 |
|---|---|---|---|---|---|
| `OFDB001` | 基金總額憑證的產生與刪除 | `OFD312` | `s_OFDB001_Excute`(`@striTYPE` 分產生 / 刪除) | `FUND_ID`、`ISSUE_DATE` / `B_ISSUE_DATE`、`Exc_TYPE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:41-47` |
| `OFDB005` | 受益人資料變更申請的生效(以「申請日期」為準) | `OFD195` | `s_OFDB005_Excute` | `APPLY_DATE`、`UpdateID` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:45-50` |
| `OFDB011` | 資料索取的信封 / 地址條列印與寄送註記 | `OFD342` | `s_OFDB011_Get`(取數) | `PrintType`、`CusType`、`REQ_DATE_ST/END`、`PR_NO`、`REQ_DATA_CODE`、`ID_NO`、`SPACE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:532`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB011.cs:146-165` |
| `OFDB161` | 定期買回(定期贖回)處理 | **無宣告** | `s_OFDB161_Excute` | `EXEC_DATE`、`EXE_TYPE`、`CreateID` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:51-71` |

#### 6.5.1 `OFDB001` 的業務卡控(UI 層,這一層還活著)

UI 的檢核不碰 DB 連線的那幾條是活的,值得記下來 —— 它們描述了「總額憑證」的業務規則:

| 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 本次憑證日期 <= 上次憑證日期 | 「本次總額憑證日期 不可小於等於 上次總額憑證日期」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:61` |
| 基金尚未成立 | 「此基金尚未成立,不可製作大憑證」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:69` |
| 憑證日期 < 基金成立日 | 「本次總額憑證日期 不可小於 該基金成立日期」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:73` |
| 憑證日期非該基金營業日 | 「本次總額憑證日期 必須為該基金的營業日」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:83` |
| `OFD303A.POST_CTL_CODE <> 'Y'` | 「此基金尚未過帳,不可產生總額憑證」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:102` |
| 上次憑證未送簽 | 「上次憑證未送簽,不可產生」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:109` |
| 憑證日期 >= 集保無實體上線日 | 「本次總額憑證日期 不可大於等於 集保無實體上線日期」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:136` |
| 刪除時憑證已送簽 | 「此憑證已送簽,不可刪除」 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB001.cs:150` |

另外 `CheckOFDR001` 會呼叫 `s_OFDR001A_Get` 比對三個單位數,不相等就報「該基金帳未平」並列出本日在外發行單位數 / 交易彙總單位數 / 受益人餘額單位數(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:193-201`)。

#### 6.5.2 `OFDB005` 與 `OFDB003` 的關係

兩支長得很像:都跟受益人資料變更生效有關,都讀 `CTL016` 的一個「處理時間」欄位、都讀 `OFD681`(`SEND_TYPE = '4'` / 由 `GenXMLHelper.Gen48` 寄信)。差別在**主表與參數**:

|  | `OFDB003` | `OFDB005` |
|---|---|---|
| 主表 | 無(裸 DAO,實際打 `BMS001ACHG`) | `OFD195` |
| 時間設定欄 | `CTL016.BF_PROC_TIME` | `CTL016.REL_PROC_TIME` |
| 參數 | 生效日 / 收件日 / 變更書號 | **只有申請日期** |
| SP | `s_TA_OFDB003_Excute`(Oracle) | `s_OFDB005_Excute`(**T-SQL**) |
| 通知信 | 讀 `OFD681A WHERE SEND_TYPE = '4'` 的 `GetOFD681()` **存在但不可達**(Ctl 的呼叫端在 `/* */` 裡) | 讀 `OFD681`,Ctl 有 `GetOFD681(msg)` → `GenXMLHelper.Gen48`,**但 Pxy 沒開放、UI 也沒呼叫,一樣不可達** |
| 現況 | **活的** | **跑不起來** |

`OFD195` 在 repo 的其他地方只出現在 `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1049` 的一行註解「`OFD195A : CHANNEL_CD => AGENT_ID, CHANNEL_CODE => AGENT_CODE`」,無法據此判斷業務意義。 **`OFDB005` 到底在生效什麼,repo 內查不到,標〔假設〕缺:DB 連線。**

#### 6.5.3 `OFDB161` 的業務輪廓

雖然跑不起來,PO 裡的查詢把它的資料流講得很清楚:

| 方法 | 查 / 寫 | 用途(推測) | 錨點 |
|---|---|---|---|
| `Execute` | SP `s_OFDB161_Excute` | 主處理 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:51-73` |
| `GetEXEC_TIMES` | `OFD163` | 讀「定期買回處理時間」 | `:115-122` |
| `GetOFD681` | `OFD681 WHERE SEND_TYPE = '11'` | 取通知信名單〔客戶特定〕 | `:162-175` |
| `GetAftExecRowCount` | `OFD165` | 執行後筆數 | `:200-207` |
| `CheckOFD166` / `CheckOFD166ByAuto` | `OFD166` | 前置檢核 | `:253-260`、`:298-307` |
| `CheckBusinessDay` | `OFD003` | 營業日判斷 | `:338-346` |

`Execute` 一開頭就先 `GetOFD681(model)`,註解寫「先取得 OFD681 資料 (ST 丟出錯誤訊息時要使用)」(`:40-41`)—— 先把收件者撈好,SP 失敗時才有人可以通知。`int i = base.ExecuteNonQuery(dbTA, cmd, tran);` 之後**沒有任何 `i` 的檢查就直接 `tran.Commit()`**(`:73-76`)—— 又一支「一律回報成功」。

#### 6.5.4 四支共同的缺陷

| 缺陷 | 錨點 | 嚴重度 |
|---|---|---|
| `dbTA` / `dbPTPF` 恆為 null,執行必爆 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`:169-172` | **高** |
| T-SQL 語法在 Oracle 連線上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:41`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:65` | **高** |
| Ctl 不繼承 `BaseController`,直接 `new PO()`,不走 `DataAccessPool` | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB001_Ctl.cs:14`、`:43`;`OFDB005_Ctl.cs:15`;`OFDB011_Ctl.cs:15`;`OFDB161_Ctl.cs:15` | 中 |
| `CommandTimeout = 0`,註解直接寫「此程式讓它永久跑」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:177`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:47` | 中 |
| `catch` 直接 `tran.Rollback()`,`tran` 可能為 null | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:71-77` | 高 |
| `CheckCTL_DATE` 例外時回傳 `-1`,呼叫端當成筆數用 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:152-161` | 中 |

### 6.6 `OFDB002` 依傳票號執行淨值更正(推測)

中文名無出處,只能從欄位推。主檔查詢是`SELECT VOC_NO, OFD297A.FUND_ID, OFD081A.FUND_SH_NM, BEF_NAV_DATE, AFT_NAV_DATE, PICK_TYPE, PICK_VALUE, VOC_YN, EXE_STATUS FROM OFD297A LEFT JOIN OFD081A … WHERE VOC_YN = 'Y' AND VOC_NO = N'…'`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:155-167`)。`BEF_NAV_DATE` / `AFT_NAV_DATE`(變更前 / 變更後淨值日)加上 `EXE_STATUS`「執行狀態」的 Caption, **推測**是「淨值更正傳票的批次執行」。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工。先用傳票號 `VOC_NO` 查出一批基金,再按執行 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB002.cs:149` |
| 參數 | `datiB_NAV_DATE`、`datiA_NAV_DATE`、`striFUND_ID`(**Grid 上全部基金代碼用逗號串成一個字串**)、`striUpdateID` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB002.cs:102-110`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:94-103` |
| 寫入 | SP `s_TA_OFDB002_Excute`,1 個 refcursor `outTB` → `OFDB002` 表(欄位 `RESULT` / `MSG` / `FUND_ID` / `EXE_STATUS`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:86`、`:104` |
| 卡控 | Grid 0 筆 → 「至少需要一筆資料」(**阻擋**) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB002.cs:93-100` |
| 成敗判定 | `j < 1 |  |
| rollback | **會**(C# 端交易) | `:113`、`:118` |
| 重跑 | 由 `OFD297A.EXE_STATUS` 控制(值域未知);`VOC_YN = 'Y'` 才撈得到 | — |
| 順序相依 | 無本片內相依 | — |

> ⚠ **`if (j < 1 || !mVDB.DataEntity.OFDB002[0].RESULT)` 的下一行讀 `OFDB002[0].MSG`。**短路運算讓 `j < 1`(0 筆)先成立,然後**立刻去取 `[0]`** ——SP 回 0 筆時是 `IndexOutOfRangeException`,不是「查無資料」訊息。錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:110-114`。嚴重度:高。

> ⚠ **`striFUND_ID` 是把 Grid 上**所有**列的 `FUND_ID` 用逗號串起來丟給 SP,沒有勾選概念、沒有筆數上限**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB002.cs:107-110`)。基金一多,這個參數會很長;`Varchar2` 綁定有 4000 bytes 上限,超過就是 `ORA-01461` 之類的錯。

> ⚠ **`VOC_NO` 直接字串串接進 SQL**:`… AND VOC_NO = " + this.GetParamValue(model, "VOC_NO", true)`,而 `GetParamValue(..., true)` 只是把值包成 `N'值'`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:167` 與 `:228-231`)。值來自畫面輸入框。嚴重度:中。

> ⚠ **`MasterTable` 在方法裡被換掉**(`OFD081A` → `OFD297A`,`:68`),PO 是連線池共用實例。見 §2.1 的警告。

### 6.7 `OFDB007` 受益人名條列印(推測)

| 面向 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工。兩條路:(a) 用條件查 `BMS001A`、(b) **匯入 Excel** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:74-104`、`:129-226` |
| 參數(查詢) | `BF_NO_START` / `BF_NO_END` / `OPEN_ACC_DATE_START` / `OPEN_ACC_DATE_END` / `BF_COUNTRY_X`(受益人類別)/ `TRUST_CODE`(帳戶類別)/ `ID_NO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB007_PO.cs:59-77` |
| 讀 | `BMS001A` 的 `BF_NO` / `ID_NO` / `BF_NAME` / `CNT_PERSON` / `MAIL_ZIP` / `MAIL_ADDR` / `PERM_ZIP` / `PERM_ADDR` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB007_PO.cs:49-57` |
| **寫入** | **完全不寫 DB**。`AfterExecuteButtonClicked` 第一行就 `e.Cancel = true` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:124-127` |
| 輸出 | Crystal Report `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007RPS.rpt` | — |
| rollback | 不適用 | — |
| 重跑 | 可,無副作用 | — |

Excel 匯入走 `ExcelQueryFactory`(LinqToExcel,無原始碼,從呼叫端反推),只接 `*.xls`、**欄數必須剛好 6**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:133`、`:146-150`)。

| 卡控 | 條件 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 欄數 | `cols.Count() != 6` | 「匯入的資料欄位格式不正確,請檢查」 | **阻擋** | `:146-150` |
| 戶號 | 非空且(長度 > 10 或非數字) | 「第 N 筆 戶號資料格式有誤,請檢查」 | **阻擋** | `:160-166` |
| 姓名 | 長度 0 或 > 100 | 「第 N 筆 姓名資料格式有誤,請檢查」 | **阻擋** | `:167-170` |
| 地址 | 長度 0 或 > 80 | 「第 N 筆 地址資料格式有誤,請檢查」 | **阻擋** | `:171-174` |
| 轉全形 | 第 5 欄(index 4)一律 `StringConvert.ConvertToFull` | — | 記錄不擋 | `:182-185` |

> ⚠ **匯入迴圈的「壞列」處理:一旦前面任何一列有錯,後面所有列都不會進資料表。**條件是 `if (this.ValidateErrList.ErrorCount < 1) { …AddRow… }`(`:176-193`)——`ErrorCount` 一旦 > 0 就再也回不到 0,迴圈**繼續跑完但每一列都跳過新增**。表面上會把所有錯誤列出來(好事),但若使用者只看第一條訊息就去修,修完重匯仍會被後面的錯誤擋住。屬「迴圈遇壞列後全部吃掉」的變形。錨點 `:176-193`。嚴重度:中。

> ⚠ **整個匯入包在一個 `catch { ShowMessage("匯入的檔案格式不正確,請檢查"); }` 裡,沒有例外變數、沒有 log**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:221-224`)。檔案鎖住、Excel driver 沒裝、資料型別錯 —— 一律變成同一句話。嚴重度:中。

### 6.8 `OFDB008` 主管機關申報檔產出(推測)

一支畫面產八種申報檔,每種一個核取方塊、一個年月 / 日期。中文名的來源是 Designer 裡的標籤字串(用 `grep` 取得,未開啟 Designer):「SDD:基金配息申報檔」「FSA:基金銷售地資料彙總」「CLB:大陸人士單筆大額申購檔」「BOT 的申報年月」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.Designer.cs:180`、`:268`、`:292`、`:316`)。

| 檔別 | SP | 畫面參數 | 副檔名 |
|---|---|---|---|
| `EBF` | `S_TA_OFDB008_GET_EBF` | 年月 | `.mon` |
| `FNH` | `s_TA_NFDR005_Get` / `s_TA_NFDR006_Get` | `FNH_FUND_ID` + 年月 | `.101` |
| `BOT` | (同上一組) | 年月 | `.101` |
| `SHT` | `s_TA_OFDB008_Get_SHT` | 年月 | `.101` |
| `FET` | `s_TA_OFDB008_Get_FET` | 年月 | — |
| `DSR` | `s_TA_OFDB008_Get_DSR` | `DSR_DATE`(日) | `.mon` |
| `BFP` | `s_TA_OFDB008_Get_BFP` | `BFP_YM` → **當月最後一天** | — |
| `CLB` | `S_TA_OFDB008_Get_CLB` | `CLB_YM` → 當月最後一天 | — |
| `FSA` | `S_TA_OFDB008_Get_FSA` | `FSA_YM` → 當月最後一天 | — |
| `SDD` | `S_TA_OFDB008_GET_SDD` | `SDD_YM` | — |

SP 錨點集中在 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:79-252`;「當月最後一天」的算法是 `DateTime.AddMonths(1).AddDays(-1)`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:92`、`:98`、`:103`)。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工 | — |
| 寫入 DB | **零**。PO 只跑 SP 取數,全部是 `LoadDataSet` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:53-260` |
| 輸出 | UI 的 `AfterExecuteButtonClicked` 逐檔 `StreamWriter(..., false, Encoding.Default)` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:188-360` |
| 卡控 | 一種檔都沒勾 → 「請至少選擇一種申報檔案」(**阻擋**);轉出路徑不存在 → 「轉出路徑無效,請檢查」(**阻擋**) | `:114`、`:166-167` |
| rollback | 不適用(不寫 DB) | — |
| 重跑 | 可,**同名檔直接覆蓋** | `:213` 等處的 `StreamWriter(..., false, …)` |
| 順序相依 | 無 | — |

> ⚠ **檔案編碼用 `Encoding.Default`**(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:213`、`:246`、`:296`、`:321`、`:348` …)。`Encoding.Default` 在 .NET Framework 上是**作業系統目前的 ANSI 字碼頁** ——本站台是 cp950,換一台系統語系不同的機器產出來的申報檔編碼就變了。主管機關申報檔要求固定編碼,這是一顆定時炸彈。〔客戶特定〕。嚴重度:中。

> ⚠ **`FNH` 那段有一個「補空列」邏輯**:先把有寫入的基金收進 `fundHave`,再對 `OFDB008_FUND` 裡沒寫過的基金各補兩列(`string.Format(line, 1)` 與 `(line, 2)`)(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:270-282`)。補的是寫死的樣板列,不是真實資料。要改申報格式時務必一起看。

> ⚠ **`OFDB008_PO` 自己開了兩個連線**:`Database dbTA = new Database("TA", …)` 與`Database dbPTPF = new Database("SWProduct", …)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:33-34`),但它是裸 DAO,`dbPTPF` 在整支檔裡沒有任何使用點。死欄位。

### 6.9 `OFDB040` 基金鎖定 / `OFDB041` 淨值鎖定 —— 兩支看起來像、實際差很多

|  | `OFDB040` | `OFDB041` |
|---|---|---|
| 鎖什麼 | `OFD081A.FUND_LOCK` + `FND001.FUND_LOCK` | `OFD302A.NAV_LOCK` |
| PO 型態 | 裸 DAO | `BaseMultiRowEVADaoPO` |
| 寫入方式 | 自組**匿名 PL/SQL 區塊**(`BEGIN … END;`)逐列執行 | `base.Update`(走 EVA 多筆更新) |
| 前置檢核 | 只在 UI:狀態必須 `LIKE '3%'`、不可重複設同一值 | UI + **伺服端 `Is_UnLock`(但它壞了)** |
| 錨點 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:83-137` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:61-72`、`:203-337` |

#### 6.9.1 `OFDB040`

執行功能兩選一:`"1"` 鎖定 → `FUND_LOCK = 'Y'`、`"2"` 取消鎖定 → `'N'`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:76`)。

| 卡控 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 一筆都沒勾 | 「至少勾選一筆基金代碼」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:85-89` |
| 勾到的基金已經是目標狀態 | 「基金已經是{鎖定/未鎖定}狀態,不可執行」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:92-97` |
| `STATUS` 前一碼 ≠ `'3'`(未覆核) | Grid 的勾選格 `Activation.NoEdit`,**不給勾也不提示** | **過濾(無提示)** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:58-64` |

> ⚠ **`FUND_LOCK` 的值是字串串接進 SQL 的,不是綁參數**:`string.Format(" UPDATE OFD081A SET FUND_LOCK = '{0}', …", mModel.Utility.Parameters.FindByName("FUND_LOCK").Value)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:92`、`:97`)。同一段 SQL 的 `FUND_ID` 與 `UPDATEID` 反而有綁參數(`:108-109`)—— 一半綁一半不綁。值本身來自單選鈕(只會是 `Y`/`N`),風險有限,但寫法是錯的。嚴重度:中。

> ⚠ **成功時完全不塞 `Result` 列。** `Execute` 只在兩個 `catch` 裡 `AddResultRow(false, …)`,成功路徑走完直接 `return model`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:83-137`)。呼叫端 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB040_Ctl.cs:47-51` 走`ExecPOActionToViewVDB`,框架若沒補一列,UI 讀 `Result[0]` 就是 index out of range—— 與 `architecture.md §6` 提到的 `CASM001_Ctl.AddData()` 同一種病。嚴重度:高。

> ⚠ **`FND001` 這張表在 repo 內只出現在這一支**(全庫 grep `FND001`:僅 `OFDB040_PO.cs:96`)。它與 `OFD081A` 的關係、由誰維護、欄位定義,**repo 內查不到**。標〔假設〕缺:DB 連線。兩張表同時被 `UPDATE` 且在同一個 PL/SQL 區塊裡,代表它們必須同步 —— 這是一條隱性不變量。

#### 6.9.2 `OFDB041` 的伺服端卡控失效(本片最隱蔽的一顆雷)

`Is_UnLock(BasicModelVDB model)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:203-337`)的職責註解寫得很清楚:「True:可以解Lock / False:不可以解Lock」,而且「1. 需檢核 OFD303A, OFD081;2. PO.Select 會用到;3. Control.Not_UnLock 會用到」(`:194-202`)。

它的實作:

```
model.Utility.Result.Clear();                    ← :209
foreach (每一列) {
    查 OFD303A 申購側 (ALLOT_CTL_CODE >= '3' OR RSP_CTL_CODE >= '3' OR POST_CTL_CODE = 'Y')
    查 OFD303A 贖回側 (REDEM_CTL_CODE >= '4' OR RSP_CTL_CODE >= '3' OR POST_CTL_CODE = 'Y')
    if  (申購側有列) { 依欄位值設 row.IS_UNLOCK = false 與 row.MEMO }
    else if (贖回側有列) { 同上 }
    else { row.IS_UNLOCK = true }
}
return model.Utility.Result.Count != 0 ? false : true;    ← :333-336
```

**`Result` 在 `:209` 被清空,整個迴圈裡沒有任何一行 `AddResultRow` —— 原本會塞訊息的那三行在 `:287-291` 被註解掉了。所以 `Is_UnLock` 的回傳值恆為 `true`。**

`Execute<T>` 的第一件事就是 `if (!Is_UnLock(model)) return mModel;`(`:65-68`)——這道伺服端閘門**永遠不會關**,`base.Update` 一定會被呼叫。

擋住使用者的只剩前端:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB041.cs:239-241`把 `IS_UNLOCK == false` 的列的勾選格設成 `Activation.Disabled`。 **任何繞過 UI 的呼叫端(重送 VDB、未來的服務化、自動化測試)都不會被擋。** 嚴重度:高。

同一支還有兩個邏輯落差:

1. **SQL 用 `>=`,C# 用 `==`。** SQL 撈 `ALLOT_CTL_CODE >= '3'`(`:244`), C# 只判 `allot_Allot_Ctl == "3"`(`:298`)。控制碼若是 `'5'` / `'6'`,SQL 撈得到但 C# 三個分支都不成立 → `IS_UNLOCK` 停在 typed DataSet 的預設值,`MEMO` 也不填。

2. **`else if` 讓贖回側被跳過。** 申購側只要有列,贖回側整段不判(`:293`、`:309`)。「申購未結轉但贖回已結轉」的基金會被判成可解鎖。

### 6.10 `OFDB222` 交易關帳 / 取消關帳(推測)

| 面向 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工 | — |
| 參數 | `EXE_TYPE`(`"1"` 關帳 → `'Y'` / `"2"` 取消關帳 → `'N'`)、`TRAN_TYPE`(`"1"` 申購 / `"2"` 贖回) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:53-65` |
| 寫入 | `CTL022.ALLOT_CLS`(申購)或 `CTL022.REDEM_CLS`(贖回),逐列 `UPDATE` | `:81-90`、`:104` |
| 額外寫入 | 關帳成功且符合條件時,**自動 `INSERT` 次一營業日的 `CTL022` 列**(`ALLOT_CLS='N'` / `REDEM_CLS='N'`) | `:107-176` |
| 次一營業日 | `f_TA_GetFNBusinessDay(:FUND_ID, '2', TO_DATE(:TX_DATE,'yyyymmdd'), 1)`(無原始碼,從呼叫端反推) | `:117` |
| 卡控 | 「交易資料中有未覆核資料,不可關帳」 | `:457` |
| rollback | 會(C# 端交易),但**中途 `CheckCTL022` 失敗時是 `tran.Rollback(); … return model;`**,前面已寫的列一起回滾 | `:136-143` |
| 重跑 | 可(有取消關帳) | — |
| 順序相依 | 與 `OFD303A` 的日結流程相依,但本片內無相依 | — |

自動建次一日關帳列的條件寫死:

```
if (CheckCTL022(row, tran) && strEXE_TYPE == "Y" &&
    (row.AGENT_ID == "0" && (row.AGENT_CODE != "A0901" && row.AGENT_CODE != "OP101")))
```

註解:「20151016 銷售機構區別碼為公司且代碼不為 OP101 股務代理 A0901 代銷業務,關帳後自動產生次一交易日的關帳控制檔資料」(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:107-109`)。`"0"` / `"A0901"` / `"OP101"` 三個都是寫死字面值〔客戶特定〕。

> ⚠ **`strTRAN_TYPE` 不是 `"1"` 也不是 `"2"` 時,`strUpdate` 會是空字串。**兩個分支是 `if` / `else if`,沒有 `else`(`:79-91`),之後直接 `dbTA.GetSqlStringCommand(strUpdate)`(`:93`)。目前 UI 只會給 1 或 2,但這是一顆沒有防護的空指令。嚴重度:低。

> ⚠ **`i += dbTA.ExecuteNonQuery(cmdExecute, tran);` 的 `i` 從頭到尾沒有被檢查過。**`:104` 與 `:170` 兩處只累加,最後 `AddResultRow(true, i, "執行成功")`(`:179`)。更新 0 列(例如 `CTL022` 上根本沒有那一列)也算成功,只是筆數變 0。`i` 為 0 時走的是 `else` 分支「執行失敗,請檢查」(`:181-185`),所以**部分成功會被報成全部成功**。嚴重度:中。

### 6.11 `OFDB223` 銷售機構代碼整批置換(推測)

畫面上只有「匯入銷售機構檔路徑」與「文字檔檔名」兩個輸入(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB223.Designer.cs:122`、`:136`),Model 的四個欄位 Caption 是「異動前銷售機構區碼 / 異動前銷售機構 / 異動後銷售機構區碼 / 異動後銷售機構」。

**這支是本片破壞力最大的一支:一次 `UPDATE` 七張交易表。**

```
string strTbName = "OFD220A,OFD221A,OFD251A,OFD253A,RSP005A,RSP006A,RSP070A";
…
strSQL = @"UPDATE " + split[i] + @"
              SET AGENT_ID = :AF_AGENT_ID,
                  AGENT_CODE = :AF_AGENT_CODE
            WHERE AGENT_ID = :BF_AGENT_ID
              AND AGENT_CODE = :BF_AGENT_CODE ";
```

錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:119` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:129-133`。

| 面向 | 內容 |
|---|---|
| 觸發 | 人工 |
| 參數 | 每一列的 `BF_AGENT_ID` / `BF_AGENT_CODE` / `AF_AGENT_ID` / `AF_AGENT_CODE`,來源是匯入的文字檔 |
| 寫入 | `OFD220A`、`OFD221A`、`OFD251A`、`OFD253A`、`RSP005A`、`RSP006A`、`RSP070A` |
| rollback | 會(單一交易涵蓋七張表 × 全部列) |
| 重跑 | **危險** —— 見下 |
| 順序相依 | 無 |

> ⚠ **`UPDATE` 的 `WHERE` 只有 `AGENT_ID` + `AGENT_CODE`,沒有任何日期或交易單號範圍。**一列設定會把七張交易表上**歷史上所有**該銷售機構的交易一次改掉。這是 `architecture.md §4.7` 那類「無鍵 / 寬鍵 UPDATE」的極端案例,只是這裡是**刻意的整批換號**。錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:129-133`。嚴重度:高(設計如此,但要知道)。

> ⚠ **`ExecuteNonQuery` 的回傳值完全丟掉,最後固定 `AddResultRow(true, 1, "")`。**錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:141`、`:145`。不論實際改了 0 列還是 100 萬列,畫面都顯示成功、筆數 1。這是型錄裡「一律回報成功」的標準形,與 DSM `DSMB001_PO.cs:75`、CRM `CRMB002` 同型。嚴重度:**高**。

> ⚠ **重跑會做什麼?** 第二次跑時 `WHERE AGENT_ID = 舊碼` 已經找不到列(都改成新碼了),所以是 0 列更新 —— **但畫面仍然回報成功**。使用者無法分辨「第一次成功」與「第二次空跑」。若換號設定檔裡有 A→B 與 B→C 兩列,第一列跑完後第二列會把剛改成 B 的也一起改成 C——**迴圈順序決定結果**,而且沒有任何防護(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:123-139`)。嚴重度:高。

> `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:41-95` 的 `Check<T>` 只對 `DUAL` 做查詢組裝,用來把匯入檔的內容比對成 Grid 資料;`CheckCTL022` 那類實質前置檢核在本支**不存在**。

### 6.12 `OFDB286` 退匯 / `OFDB287` 重匯 —— 配息付款的後段兩支

兩支共用 `OFD283A`(配息主檔)與 `OFD292A`(退匯 / 重匯明細),是一組。

#### 6.12.1 `OFDB286` 退匯 / 取消退匯

| `ExeType` | 功能 | 寫入 |
|---|---|---|
| `"0"` | 退匯 | `OFD283A.RET_REMIT_DATE` + `GET_STATUS = '4'`;`OFD131A.PAUSE_PAY = 'Y'`;`INSERT OFD292A` 一列 |
| `"1"` | 取消退匯 | `UPDATE OFD283A` + `UPDATE OFD131A`(回復) |

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:59-103`(退匯的匿名 PL/SQL 區塊)、`:240-262`(取消退匯)。

| 卡控 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 一筆都沒勾 | 「至少需勾選一筆明細資料!」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB286.cs:104` |
| 退匯原因空白 | 「退匯原因必須輸入」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB286.cs:113` |
| 退匯日期空白 | 「退匯日期必須輸入」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB286.cs:127` |
| 退匯日期 < 發放日期 | 「受益人:{姓名} 退匯日期不可小於發放日期」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB286.cs:154` |
| 退匯日期 < 上次重匯日期 | 「受益人:{姓名} 退匯日期不可小於上次重匯日期」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB286.cs:160` |

`OFD131A` 的 `UPDATE` 條件值得單獨記:

```
WHERE (FUND_ID = :FUND_ID OR FUND_ID = 'ALL FUNDS')
  AND BF_NO = :BF_NO
  AND TERMINATE_DATE = ' '
  AND BANK_BRH = :BANK_BRH
  AND REMIT_ACC_NO = :REMIT_ACC_NO
```

(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:73-79`)。括號有加,`OR` 沒有洩漏 —— 這一支沒有中 `AND`/`OR` 缺括號的雷。`'ALL FUNDS'` 是一個寫死的萬用基金代碼〔客戶特定〕;`TERMINATE_DATE = ' '` 是**一個空白字元**的比較,不是 `IS NULL`、也不是 `TRIM(...) = ''`—— 若欄位存的是 NULL 或多個空白,這一列不會被更新,而且不會有任何提示。

> ⚠⚠ **同一支 PO 的「取消退匯」段用的是另一種寫法:`AND trim(TERMINATE_DATE) IS NULL`**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:257`,對照退匯段的`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:79`)。兩段命中的列集不一樣:欄位存 NULL 時只有「取消退匯」撈得到,存單一空白時兩段都撈得到,存多個空白時只有「取消退匯」撈得到。 **意思是「退匯」改到的 `OFD131A` 列,「取消退匯」不保證改得回來,反之亦然** —— 而且兩段都不會提示。這是本片對稱操作不對稱的唯一一例。

> ⚠ **`OFD131A` 是 BMS 那套 `CHG` 配對表的本表之一**(`bms.md §2` 的 12 張配對表清單裡有 `OFD131ACHG`)。`OFDB286` 直接 `UPDATE OFD131A.PAUSE_PAY`(`OFDB287` 只讀它),**繞過了 `BMSM006` 的四眼與 `OFDB003` 的生效機制**。如果同一個受益人同時有一張未生效的 `OFD131ACHG` 變更單,`OFDB003` 之後回寫時會不會把 `PAUSE_PAY` 蓋回去,**從 repo 無法判斷**(SP 不在版控)。這是本篇與 `bms.md` 之間最值得追的一條交互作用。標〔假設〕缺:DB 連線。

`OFDB286` 的成敗判定比多數支嚴謹:`i = ExecuteNonQuery(...)`,`i` 不對就 rollback + `AddResultRow(false, …)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:164-170`、`:194-200`);最後依 `j`(處理列數)決定 commit 或 rollback(`:282-289`)。

#### 6.12.2 `OFDB287` 重匯 / 取消重匯

| `ExeType` | 功能 | 寫入 |
|---|---|---|
| `"0"` | 重匯 | `UPDATE OFD283A` + `UPDATE OFD292A`(填 `RREMIT_DATE` / 匯費 / 實付金額 / 實際付款日) |
| `"1"` | 取消重匯 | `UPDATE OFD292A` + `UPDATE OFD283A` 回復 |
| `"2"` | (查詢 / 報表用,不寫入) | — |

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:42-146`(重匯)、`:217-267`(取消重匯)。

| 卡控 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 基準日期(起)> (迄) | 「基準日期(起) 不可大於 基準日期(迄)」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:165` |
| 基準日期只填一邊 | 「基準日期(起)(迄) 必須皆(不)填寫」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:170` |
| 功能 ≠ 2 時基準日期必填 | 「基準日期(起) 為必填欄位」/「(迄) 為必填欄位」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:182`、`:186` |
| 功能 = 0 時實際付款日必填 | 「實際付款日 為必填欄位」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:193` |
| 實際付款日 < 系統日 | 「實際付款日 必須大於等於系統日」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:199` |
| 一筆都沒勾 | 「至少勾選一筆明細資料!」 | **阻擋** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:218` |

> ⚠⚠ **本片最經典的「一律回報成功」就在這裡:**

```
i = dbTA.ExecuteNonQuery( cmd, tran);
i = 1;                      // ← 下一行直接覆蓋
if (i == 0)
{
    tran.Rollback();
    model.Utility.Result.Clear();
    model.Utility.Result.AddResultRow(false, 0, "");
}
j += 1;
```

> 錨點 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:124-132`。`i = 1;` 讓下面的 `if (i == 0)` 成為死碼,**更新 0 列也算成功**。與 DSM `DSMB001_PO.cs:75` 完全同型。

> **而且就算 `i == 0` 真的成立,那段也只是 `tran.Rollback()` 之後 `j += 1` 繼續跑迴圈,沒有 `return`** —— 迴圈跑完 `j > 0` 就走 `tran.Commit()`(`:136-140`),在一個已經 rollback 的交易上 commit。這是「有訊息無 return」加「一律回報成功」的複合體。嚴重度:**高**。

`GetReportData<T>` 走 SP `s_TA_OFDB287_Get`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:691`)供 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287RPS.rpt` 使用。`CheckAcctNo<T>`(`:595-663`)檢查配息帳號,`QueryFee<T>`(`:541-583`)算匯費。

### 6.13 順序相依總表

| 相依 | 前置 | 後續 | 卡在哪個欄位 | 強制嗎 |
|---|---|---|---|---|
| BMS 開單 → `OFDB003` | `BMSM004` / `BMSM006` 的四眼走完 | `OFDB003` 生效 | `BMS001ACHG.CHG_UPD_DTTM` | **不強制** —— `Check()` 只詢問(§6.1.4) |
| `OFDB003` → `OFDB609` | `OFDB003` 的 LDAP 推送失敗 | `OFDB609`「更新LDAP資料」 | 無欄位,靠失敗通知信 | 不強制,人工判斷 |
| 日結轉 → `OFDB281` | `OFD303A.POST_CTL_CODE = 'Y'` | `OFDB281` 產生配息資料 | `OFD303A.POST_CTL_CODE` | **強制**(`Check_CTL_CODE`),但查無列時放行 |
| `OFDM085A` → `OFDB281` | 收益分配專戶三欄填好 | `OFDB281` | `OFD085A.DIV_ACC_NO` 等 | **詢問**,可以硬闖 |
| `OFDR287` → `OFDB281` | 無配息帳號名冊確認 | `OFDB281` | 無欄位 | **詢問**,純提醒 |
| `OFDB281` → `OFDB284` | 產生完成 | 結算確認 | `OFD281A.PROCESS_CODE` `'1'` → `'4'` | 強制 |
| `OFDB284` → `OFDB281` | 一旦 `'4'` | `OFDB281` 三種功能全鎖 | 同上 | **強制** |
| 配息付款 → `OFDB286` | 有實付資料 | 退匯 | `OFD283A.GET_STATUS` | 資料面相依 |
| `OFDB286` → `OFDB287` | 已退匯 | 重匯 | `OFD292A` 有列 | 資料面相依 |
| `OFDB019A` → `OFDB019B` | 產出資料 | 下載 XML | `CRSP001` 有列 | 資料面相依 |
| 基金覆核 → `OFDB004` | 來源 / 目的都 `STATUS LIKE '3%'` | 基金複製 | `OFD081A.STATUS` | **強制** |
| `OFDB004` → 13 支 `OFDM*` | 複製完成 | 逐張重新覆核 | 各表 EVA 欄位被清空 | **強制**(否則資料是未覆核狀態) |
| 過帳 → `OFDB001` | `OFD303A.POST_CTL_CODE = 'Y'` | 產生總額憑證 | 同上 | 強制(但整支跑不起來) |

## 7. 報表(R)

**本片無 R 型畫面**,也沒有 `ATLAS.OFDB.Report` 專案 —— `architecture.md §6.5` 講的七層 `ReportUI.*` / `ReportPO.*` / `Report.*` 結構在 `Dev/ATLAS.OFDB/` 底下完全不存在。

不過有三支 B 畫面自帶 Crystal Report:

| `.rpt` | 位置 | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|---|
| `OFDB007RPS.rpt` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007RPS.rpt` | `OFDB007` | `BMS001A` 的自組 SQL 或匯入的 Excel | 查詢條件七項(§6.7) |
| `OFDB011RPS.rpt` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB011RPS.rpt` | `OFDB011` | SP `s_OFDB011_Get` | `PrintType` / `CusType` / 日期區間 / `SPACE`(空白標籤數) |
| `OFDB287RPS.rpt` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287RPS.rpt` | `OFDB287` | SP `s_TA_OFDB287_Get` | 基金 / 受益人 / 年度 / 基準日 / 重匯日區間 |

**它們與 R 型畫面的差別**(對照 `architecture.md §6.5`):

| 面向 | R 型畫面 | 本片這三支 |
|---|---|---|
| `.rpt` 放哪 | `Report.<模組>` 專案,`EmbeddedResource` | **直接躺在 `UI.OFDB` 資料夾** |
| 誰載入 | Ctl 的 `GetReportObject()` 把 byte 回傳給用戶端,`CRReportTransfer` 處理 | UI 端的 `OFDB007RPS.cs` / `OFDB011RPS.cs` / `OFDB287RPS.cs` wrapper 類別 |
| 組件 | `Vendor.Product.TA.Report.<模組>` | `Vendor.Product.TA.UI.OFDB`(同一個) |
| 畫面代號 | `<模組>R###` | 沿用 B 代號 + `RPS` 後綴 |

`architecture.md §6.5` 提到「`.rpt` 有兩條交付路徑」與 25 個 csproj 帶 PostBuild xcopy 的問題;本片這三支屬於「檔案系統」那一條。

## 8. 跨模組共用

```text
[圖] BMS 對 OFDB003 的依賴、CHG_UPD_DTTM 只由版控外的 SP 寫入，以及本片寫入的表被哪些模組讀取
圖中文字:BMS 依賴 OFDB003:覆核不等於生效 / OFDB003 / 本片唯一的對外生效引擎 / BMS 12 張 CHG 配對表 / bms.md 已證明 / ucBfChgNo 共用控件 / Common 全系統掛 / OFDI011 客戶綜合查詢 / 顯示未生效變更 / CHG_UPD_DTTM:全庫沒有任何 C# 在寫它，只有版控外的 SP / 全庫 grep 結果 / 只有讀 沒有 UPDATE / 三種哨兵寫法並存 / 19000101 空白 1900/01/01 / RSP013A 也有同一套 / RSPM005 RSPM022 RSPR038 / 誰讓 RSP 生效 未解 / 標假設 缺 DB 連線 / 本片寫入、別的模組讀取 —— 改動前要問的對象 / OFD302A NAV_LOCK / 八個專案在讀 / OFD081A FND001 / OFD RSP DSM EC / 七張交易表 OFDB223 / 無日期範圍的整批換號 / OFD131A PAUSE_PAY / OFDB286 直寫 vs BMS 四眼 / 跨專案的補償與下游 / OFDB609 / ATLAS.EC 的 WindowsService / OFDB284 結算確認 / PROCESS_CODE 變 4 就鎖死 / OFDB701 OFDB702 / 同專案但不在本片 / 21 支 SP / repo 內腳本 0 支
```

*圖:圖 5 跨模組影響面。橘框=本片的對外接點;橘虛框=改動時要一起看或仍未解的部分;灰虛框=本片以外的畫面 / 服務;黑框=無原始碼。第②列是本篇對 bms.md 的最大補強:全庫掃過之後可以確定沒有任何 .NET 程式寫 CHG_UPD_DTTM，寫它的只能是資料庫端。*

### 8.1 `BMS001ACHG`:本片對外最重要的一條線

**`OFDB003` 是全庫唯一會讓 `BMS001ACHG.CHG_UPD_DTTM` 產生值的路徑**〔假設,依據見下〕。

決定性的一條掃描結果:**全庫所有 `.cs`(排除 `*.Designer.cs`)裡,`CHG_UPD_DTTM` 只被「讀」,沒有被「寫」。**唯二看起來像賦值的兩處是 BMS 在**記憶體 DataRow** 上塞初值(`Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:292` 塞 `""`、`:1687` 與 `:5512` 塞 `1900/1/1`),以及 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:238`、`:242`、`:276` 在 SELECT 裡用 `TO_CHAR(SYSDATE,'yyyymmddhh24miss') CHG_UPD_DTTM` 造一個**同名的輸出欄位**(不是 UPDATE)。 **沒有任何一行 C# 產生 `UPDATE … SET CHG_UPD_DTTM = …`。**

這就把 `bms.md §2` 的結論從「推測」推進到「程式面已排除其他可能」:既然沒有任何 .NET 程式寫它,而全庫又一致拿它判「生效了沒」,寫它的一定是資料庫端 —— 也就是 `s_TA_OFDB003_Excute`(或它呼叫的其他 SP)。 **但「是不是只有它」仍然是假設**,因為版控外還有 318 支 SP(`architecture.md 附錄 B.0`)。

讀 `BMS001ACHG.CHG_UPD_DTTM` 的專案:

| 專案 | 用途 |
|---|---|
| `ATLAS.BMS` | `BMSM004` / `BMSM006` 用它鎖修改與刪除鈕 |
| `ATLAS.OFDB` | **`OFDB003` 的 `Check()`**、`OFDB701`、`OFDB702`(後兩支不在本篇) |
| `ATLAS.OFDI` | `OFDI011`(客戶綜合查詢)顯示未生效變更 |
| `ATLAS.RSP` | `RSPM005` / `RSPM022`(見 §8.2) |
| `ATLAS.EC` | `OFDB605` |
| `Common` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucBfChgNo.cs`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicBMS_PO.cs`、`Dev/Common/Source/DataSource/PO.DataSource/RSP_PO.cs` |

**改 `OFDB003` 的影響面 = 上面整張表。** 尤其 `Dev/Common/Source/CustomControl/UI.CustomControl/ucBfChgNo.cs` 是一個共用控件(「受益人資料變更書號」選擇器),全系統的畫面都可能掛它。

### 8.2 `CHG` 機制不只在 BMS —— RSP 也有一套

`bms.md §2` 列的是 BMS 的 12 張配對表。掃 `CHG_UPD_DTTM` 會發現 **RSP 有自己的 `RSP013A`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:148` 宣告成 `RSPM005` 的明細),判準寫法一模一樣:`RSP013A.CHG_UPD_DTTM = '1900/01/01'` 代表未生效(`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2050`),`NVL(RSP013A.CHG_UPD_DTTM, ' ') = ' '`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:236`)。

> 〔假設〕**`RSP013A` 的生效可能也是 `OFDB003` 做的,也可能是 RSP 自己的批次。**依據:兩者共用同一組欄位命名與同一個 `1900/01/01` 哨兵值,而且 `OFDB701` 同時查兩張表(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:236` 與 `:275`)。`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs` 與 `RSPB052_PO.cs` 也讀這個欄位,但本篇沒有核對它們是否寫入 —— **`rsp` 那一片的文件應該接手這條線**。注意三個不同的哨兵寫法並存:`= '1900/01/01'`、`NVL(...,' ') = ' '`、`SUBSTR(NVL(TRIM(...),'19000101'),1,8) = '19000101'`(後者是 `OFDB003` 用的)。欄位若存成 `'1900/1/1'`(單位數月日)三種寫法會得到不同答案。

### 8.3 `OFDB003` → `OFDB609`:跨專案的補償相依

`OFDB003` 的 LDAP 失敗通知信直接寫明:「更新失敗資料請於OFDB609-網路交易後續處理作業執行『更新LDAP資料』按鈕」(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:176`)。

`OFDB609` 住在 `Dev/ATLAS.EC/`,而且是 `architecture.md §8.4` 列的四支 WindowsService 之一(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:40`)。也就是說:**本片這支手動批次的失敗補償,跑在另一個專案的 Windows 服務裡。**改 `LDAPAPIHelper` 的行為要兩邊一起看。

### 8.4 本片寫入、別的模組讀取的表

| 表 | 本片誰寫 | 誰讀 | 改動要一起看 |
|---|---|---|---|
| `BMS001ACHG` + 11 張配對表 | `OFDB003`(透過 SP) | BMS / OFD / OFDI / RSP / EC / Common | **最高** |
| `OFD131A`(`PAUSE_PAY`) | **只有 `OFDB286`**(`OFDB287` 只讀) | BMS(`OFD131ACHG` 配對表)、OFD、OFD.Query、OFDI、RSP、Common | **高**,見下 |
| `OFD081A`(`FUND_LOCK`) | `OFDB040` | OFD 全線、RSP、DSM、EC | 高 |
| `FND001`(`FUND_LOCK`) | `OFDB040` | Common、EC、EC.Query、OFD | 高(且 repo 內查不到定義) |
| `OFD302A`(`NAV_LOCK`) | `OFDB041` | CLS.Report、EC.Report、NFD.Report、OFD、OFDI、OTAB、RSP | **高**(八個專案在讀) |
| `CTL022` | `OFDB222` | OFD | 中 |
| `OFD283A` / `OFD292A` | `OFDB286`、`OFDB287` | OFD、OFD.Query、OFDI | 中 |
| `OFD281A` / `OFD287A` | `OFDB281`(透過 SP) | OFD、OFD.Query、OFD.Report、OFDI | 中 |
| `OFD220A` / `OFD221A` / `OFD251A` / `OFD253A` / `RSP005A` / `RSP006A` / `RSP070A` | **`OFDB223` 整批換號** | OFD / RSP 全線 | **高**(無日期範圍的 UPDATE) |
| 16 張基金設定表 | `OFDB004` | 對應的 13 支 `OFDM*` 維護畫面 | 高(複製後必須重新覆核) |
| `CRSP001` ~ `CRSP006` | `OFDB019A` / `OFDB019B`(透過 SP) | Common、OFD.Query | 中 |

> ⚠ **`OFD131A` 是兩套機制的交會點。** `OFDB286` 直接 `UPDATE OFD131A.PAUSE_PAY`(`OFDB287` 只讀它),而 BMS 那邊 `OFD131A` 有配對表 `OFD131ACHG`,走 `BMSM006` 的四眼 + `OFDB003` 生效(`bms.md §2` 的 12 張配對表清單)。 **同一個欄位有兩條寫入路徑,一條即時、一條要等批次**,而且沒有任何程式碼協調它們。這是本篇與 BMS 交界處最值得現場驗證的一點。標〔假設〕缺:DB 連線。

### 8.5 本片讀取、別的模組維護的表

| 表 | 維護者 | 本片誰讀 |
|---|---|---|
| `BMS001A` | BMS `BMSM001`(`bms.md §4`) | `OFDB007`、`OFDB281`(`WITHHOLD_CODE` 檢核) |
| `OFD303A` | OFD 的日結流程 | `OFDB001`、`OFDB041`、`OFDB281` |
| `OFD085A` | `OFDM085A` | `OFDB004`(寫)、`OFDB281`(讀) |
| `OFD081A` | OFD 基金主檔 M 片 | `OFDB002`、`OFDB004`、`OFDB040`、`OFDB041` |
| `OFD094A` | OFD | `OFDB004`(`OFD213A` 的資料來源) |
| `OFD681` / `OFD681A` | 不明(通知名單) | `OFDB003`、`OFDB005`、`OFDB161` |
| `CTL014` | 系統代碼表 | `OFDB019A` / `OFDB019B`(`690` 訊息類型)、`OFDB004` 註解引用 `016` / `027` / `165` / `192` / `290` / `449` |
| `CTL015` / `CTL016` | 系統設定 | `OFDB003`、`OFDB005`、`OFDB041`(透過 `ServerNfdBizUtility.GetControlDate`) |
| `COD009` | COD 員工檔 | `OFDB011`、`OFDB222` |
| `OFD163` / `OFD165` / `OFD166` / `OFD003` | OFD 定期買回 | `OFDB161` |
| `OFD297A`(傳票,維護者不明)、`OFD019` / `OFD020`(銀行分行)、`AA_Customer` / `OFD0813` / `OFD0813A`(不明) | — | `OFDB002` / `OFDB287` / `OFDB008` |

### 8.6 共用 helper

| helper | 無原始碼? | 本片誰用 |
|---|---|---|
| `LDAPAPIHelper`(`updatePasswordState` / `updateCustomerIDNumber` / `updateCustomerInfo` / `INSERT_CALLAPI_FailLog` / `SendMail`) | **是**,從呼叫端反推 | `OFDB003`(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:84`、`:129`) |
| `GenXMLHelper`(`Gen47` / `Gen48`) | **是** | `OFDB005`(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB005_Ctl.cs:61-62`);`OFDB003` 的用法在註解裡 |
| `ServerNfdBizUtility.GetControlDate` | **是** | `OFDB041`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:208`、`:221-222`) |
| `xTableHelper` / `xEVAStringHelper` / `xEVAUtility` | **是**(`architecture.md §3.1`) | `OFDB004`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:1083`、`:1095`)、`OFDB222` |
| `UseCaseSecurity.SetPermissionInfo` | **是** | `OFDB004`(`:662`、`:698`、`:704`、`:775`)、`OFDB222`(`:135`) |
| `EVAStringHelper.GetParamValue` | 有(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs`) | `OFDB281`(`:394-406`) |
| `DateTimeHelper` | 有(`Dev/Common/Source/Utility/TA.Utility/DateTimeHelper.cs`) | `OFDB003`、`OFDB041` |
| `ExcelQueryFactory`(LinqToExcel) | **是**,第三方 | `OFDB007`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:140`) |
| `StringConvert.ConvertToFull` | 有 | `OFDB007`(`:184`) |
| `SystemDateTime.GetSystemDate(APServer)` | **是** | `OFDB003`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:37`、`:103`)、`OFDB287` |

### 8.7 改動影響面速查

| 改什麼 | 至少要一起看 |
|---|---|
| `s_TA_OFDB003_Excute` | BMS 12 張配對表、`ucBfChgNo` 共用控件、`OFDI011`、`OFDB609`、RSP 的 `RSP013A`(§8.2) |
| `OFDB003` 的三個參數 | `Check()` 的 SQL、`BMS001Chg()` 的 SQL、SP 簽名 —— **三處各寫各的** |
| `OFD131A.PAUSE_PAY` | `OFDB286` 的直寫路徑 + `OFDB287` 的讀取 + BMS 的 `OFD131ACHG` 四眼路徑 |
| `OFD085A` 的欄位 | `OFDB004`(複製,含 `CreateOFD085Row` 的 12 個寫死預設值)+ `OFDB281`(`Check_DIV_ACC_NO`)+ `OFDM085A` |
| `OFD081A.STATUS` 的值域 | `OFDB004`(`LIKE '3%'`)、`OFDB040`(`Substring(0,1) != "3"`) |
| `OFD303A` 的控制碼值域 | `OFDB041`(SQL 用 `>=`、C# 用 `==`,§6.9.2)、`OFDB281`、`OFDB001` |
| 銷售機構代碼 | `OFDB222`(寫死 `A0901` / `OP101`)、`OFDB223`(七張表整批換號) |
| `CTL014` 的 `690` 順序 | `OFDB019A` / `OFDB019B` 用 `Rows[3].Hidden = true` 位置取值 |

## 附錄 A. 資料表總表

### A.1 本片會動到的實體表(依群分類)

「動」欄:W = 本片有寫入、R = 只讀。

| 表 | 動 | 誰 | 說明(推測) |
|---|---|---|---|
| `BMS001ACHG` | W(SP) | `OFDB003` | 受益人資料變更申請單,見 `bms.md §2` |
| `BMS001A` | W(SP,假設)/ R | `OFDB003` / `OFDB007`、`OFDB281` | 受益人主檔 |
| `OFD195` | W(SP) | `OFDB005` | 未知〔假設〕缺:DB 連線 |
| `OFD081A` | W / R | `OFDB040` / `OFDB002`、`OFDB004`、`OFDB041` | 基金主檔 |
| `FND001` | W | `OFDB040` | 基金鎖定的第二份來源,repo 內無定義 |
| `OFD038A` `OFD070A` `OFD074` `OFD075` `OFD076` `OFD077` `OFD085A` `OFD129A` `OFD193A` `OFD194A` `OFD196A` `OFD213A` `OFD214A` `OFD215A` `OFD260A` `OFD261A` | W | `OFDB004` | 基金衍生設定 16 張,見 §2.2 |
| `OFD094A` | R | `OFDB004` | 基金保管銀行,`OFD213A` 的資料來源 |
| `OFD302A` | W | `OFDB041` | 淨值檔 |
| `OFD303A` | R | `OFDB001`、`OFDB041`、`OFDB281` | 基金過帳 / 結轉控制 |
| `OFD281A` | W(SP)/ R | `OFDB281` | 收益分配主檔 |
| `OFD287A` | W(SP) | `OFDB281` | 收益分配明細 |
| `OFD283A` | W | `OFDB286`、`OFDB287` | 配息付款主檔 |
| `OFD292A` | W | `OFDB286`、`OFDB287` | 退匯 / 重匯明細 |
| `OFD292` | R | `OFDB286`、`OFDB287` | 同上的歷史版(只在註解與查詢裡) |
| `OFD131A` | W / R | `OFDB286` 寫 `PAUSE_PAY` / `OFDB287` 只讀 | 受益人配息帳號 / 暫停配息 |
| `OFD019` `OFD020` | R | `OFDB287` | 銀行 / 分行 |
| `CTL022` | W | `OFDB222` | 逐基金逐銷售機構的關帳控制;`OFD221A` `OFD251A` `COD009` 同支只讀 |
| `OFD220A` `OFD221A` `OFD251A` `OFD253A` `RSP005A` `RSP006A` `RSP070A` | W | `OFDB223` | 整批換號的七張交易表 |
| `OFD312` | W(SP) | `OFDB001` | 總額憑證;同支只讀 `OFD303A`(過帳檢核)與 `OFD721`(憑證狀態) |
| `OFD297A` | R | `OFDB002` | 傳票 |
| `OFD342` `OFD343` | W | `OFDB011` | 資料索取單與寄送註記;同支只讀 `OFD361`(客戶名稱 / 地址)與 `COD009` |
| `CRSP001` `CRSP002` `CRSP004` `CRSP005` `CRSP006` | W(SP) | `OFDB019A`、`OFDB019B` | CRS 申報 |
| `CTL016` | R | `OFDB003`、`OFDB005` | 處理時間設定 |
| `OFD163` `OFD165` `OFD166` `OFD003` | R / W(SP) | `OFDB161` | 定期買回 |
| `OFD681` `OFD681A` | R | `OFDB003`、`OFDB005`、`OFDB161` | 通知信名單 |
| `OFD607A` `OFD607` `LOG602` | (**已註解,現不動**) | `OFDB003` | EC 密碼 |
| `AA_Customer` `OFD0813` `OFD0813A` | R | `OFDB008` | 申報檔取數 |

### A.2 vdb 表名與實體表名不同的對照

`architecture.md §5` 說過掃描器以實體表名找 xsd。本片的對照:

| 實體表 | vdb / DataTable 名 | 出處 |
|---|---|---|
| `OFD312` | `OFDB001` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:19` |
| `OFD081A` | `OFDB002` / `OFDB004` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:36`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:54` |
| `OFD297A` | `OFDB002_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:68` |
| `BMS001ACHG` | `BMS001CHG` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:94`(與 `bms.md §2` 的對照一致) |
| `OFD195` | `OFDB005` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:20` |
| `BMS001A` | `BMS001` | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB007Model.xsd` |
| `OFD342` | `OFDB011` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:20` |
| `OFD302A` | `OFDB041` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:32` |
| `OFD281A` | `OFDM281` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:41` |
| `OFD287A` | `OFDM281_Detail` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:46` |
| 16 張基金設定表 | `OFDM038` / `OFDM070A` / … | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:55-77`,見 §2.2 |

### A.3 只存在於 SQL 字串裡的表(xsd 查不到)

`FND001`、`CTL022`、`OFD343`、`OFD361`、`OFD721`、`OFD094A`、`OFD019`、`OFD020`、`OFD220A`、`OFD253A`、`RSP005A`、`RSP006A`、`RSP070A`、`AA_Customer`、`OFD0813`、`OFD0813A`。要查它們的欄位,只能 grep SQL 字串或連 DB。

## 附錄 B. SP / Function / Trigger / View

### B.1 本片呼叫的 SP:21 支,repo 內腳本 0 支

`architecture.md 附錄 B.0` 說全庫 380 支 SP 只有 61 支有腳本。**本片 21 支,一支都沒有。**(`DB/` 底下 grep `OFDB0` / `OFDB1` / `OFDB2`:0 命中。)

| SP | 呼叫端 | 傳什麼 | 回什麼 |
|---|---|---|---|
| `s_TA_OFDB003_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:64` | 4 IN | **5 refcursor** |
| `s_TA_OFDB002_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:86` | 4 IN | 1 refcursor |
| `s_TA_OFDB281_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:389` | 8 IN | `strMsg` OUT |
| `s_TA_OFDB287_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:691` | 查詢條件 | refcursor |
| `S_TA_OFDB019A_EXECUTE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:66` | 6 IN | `strMsg` OUT |
| `S_TA_OFDB019B_EXECUTE` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:73` | 6 IN | `strMsg` + **6 refcursor** |
| `s_OFDB001_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:41` | 4 IN(**T-SQL `EXEC`**) | 結果集 |
| `s_OFDR001A_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:175` | 2 IN | 結果集 |
| `s_OFDB005_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:45` | 2 IN(**T-SQL `EXEC`**) | 影響列數 |
| `s_OFDB011_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:532` | 查詢條件 | 結果集 |
| `s_OFDB161_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:51` | 3 IN | 影響列數 |
| `S_TA_OFDB008_GET_EBF` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:79` | 年月 | refcursor |
| `s_TA_NFDR005_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:113` | 基金 + 年月 | refcursor |
| `s_TA_NFDR006_Get` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:130` | 同上 | refcursor |
| `s_TA_OFDB008_Get_SHT` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:150` | 年月 | refcursor |
| `s_TA_OFDB008_Get_FET` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:161` | 年月 | refcursor |
| `s_TA_OFDB008_Get_DSR` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:175` | 日期 | refcursor |
| `s_TA_OFDB008_Get_BFP` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:188` | 月底日 | refcursor |
| `S_TA_OFDB008_Get_CLB` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:207` | 月底日 | refcursor |
| `S_TA_OFDB008_Get_FSA` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:223` | 月底日 | refcursor |
| `S_TA_OFDB008_GET_SDD` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:252` | 年月 | refcursor |

### B.2 Function

| Function | 呼叫端 | 用途 |
|---|---|---|
| `f_TA_GetEVAStatus('A')` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:317` | table function,回傳「已覆核」狀態群 |
| `f_TA_GetFNBusinessDay(FUND_ID, '2', 日期, 1)` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:117` | 取次一營業日 |
| `f_Round` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:92-96`(**在註解裡**) | 舊 SQL Server 時代的四捨五入,已改在前端做 |

三支都**不在版控**。

### B.3 Trigger / View

本片沒有任何 Trigger 或 View 的呼叫。

## 附錄 C. 代碼對照

| 代碼群 | 值 | 意義 | 來源 |
|---|---|---|---|
| `OFDB003` 無自有代碼 | — | 全部沿用 BMS 的 EVA 狀態 | — |
| `OFDB019A/B` `EXE_TYPE` | `0` 產出資料 / `1` 刪除資料 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:159-161` | 單選鈕標籤 |
| `OFDB019B` `EXE_TYPE` | `CheckedIndex + 2`:`2` 下載 xml / `3` 刪除 xml | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:78`、`:149`、`:666` | 程式 |
| `MESSAGE_TYPE` | `CRS701` 新增資訊 / `CRS702` 刪除已申報資訊 / `CRS703` 無(**被隱藏**) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:41-42` | `CTL014` 的 `690` |
| `PROC_CODE` | 空白 正常 / `D` 取消 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170` | 程式註解 |
| `REPORT_STATUS` | `0` 未申報 / `1` 已申報 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:245` | 程式註解 |
| `OFDB040` `EXE_TYPE` | `1` 鎖定 → `FUND_LOCK='Y'` / `2` 取消鎖定 → `'N'` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB040.cs:76` | 程式 |
| `OFDB222` `EXE_TYPE` | `1` 關帳 → `'Y'` / `2` 取消關帳 → `'N'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:56-59` | 程式 |
| `OFDB222` `TRAN_TYPE` | `1` 申購(寫 `ALLOT_CLS`)/ `2` 贖回(寫 `REDEM_CLS`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:79-91` | 程式 |
| `OFDB281` `ExecuteType` | `0` 產生 / `1` 重新產生 / `2` 刪除 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:45`、`:57`、`:132` | 程式 |
| `OFD281A.PROCESS_CODE` | `0` 未產生 / `1` 已產生 / `4` 已結算確認 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:114`、`:153`、`:191` | 程式 |
| `OFDB286` / `OFDB287` `ExeType` | `0` 退匯 / 重匯 · `1` 取消 · `2`(僅 `OFDB287`)查詢 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:59`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB287.cs:175` | 程式 |
| `OFD283A.GET_STATUS` · `OFD131A.PAUSE_PAY` | `4` = 退匯 · `Y` 暫停 / `N` 正常 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:65` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:74` | 程式 |
| `OFD303A.POST_CTL_CODE` | `Y` 已過帳 / `N` 未過帳 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:259-261` | 程式 |
| `OFD303A.ALLOT_CTL_CODE` / `REDEM_CTL_CODE` / `RSP_CTL_CODE` | 申購 `>= '3'` 已結轉;贖回 `>= '4'`;定時定額 `>= '3'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:244-246`、`:274-276` | 程式註解 |
| `OFD081A.STATUS` | `LIKE '3%'` = 已覆核 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:321` | 程式 |
| `OFD681.SEND_TYPE` | `4` → `OFDB003` · `11` → `OFDB161`〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:408`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:170` | 程式 |
| `OFDB004` 的 `OFD085A` 預設值 | 見 §6.2.5 的 12 欄表 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:905-914` | 程式註解引用 `CTL014` |
| `OFD297A.VOC_YN` | `'Y'` 才撈得到 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:167` | 程式 |
| 銷售機構〔客戶特定〕 | `AGENT_ID = '0'` 公司 · `AGENT_CODE = 'A0901'` 代銷業務 · `'OP101'` 股務代理 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:107-109` | 程式註解 |
| `'ALL FUNDS'` | `OFD131A.FUND_ID` 的萬用值〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:77` | 程式 |
| CRS 公司識別碼〔客戶特定〕 | `TW-86385617` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:147` | 程式 |

## 附錄 D. 掃描母體與覆蓋率

`architecture.md 附錄 D.1` 的覆蓋率工具是以**整個模組**為單位;OFD 有 550 支,本篇只寫其中 18 支,跑 `--module OFD` 得到的數字對本篇沒有意義。改用下面這張逐支對照表。

| # | 代號 | 處置 | 寫在哪一節 | 深度 |
|---|---|---|---|---|
| 1 | `OFDB001` | **已寫** | §6.5、§6.5.1 | 中(含 8 條 UI 卡控) |
| 2 | `OFDB002` | **已寫** | §6.6 | 中 |
| 3 | **`OFDB003`** | **已寫** | §6.1(九個小節) | **深** |
| 4 | **`OFDB004`** | **已寫** | §6.2(六個小節) | **深** |
| 5 | `OFDB005` | **已寫** | §6.5、§6.5.2 | 中 |
| 6 | `OFDB007` | **已寫** | §6.7 | 中 |
| 7 | `OFDB008` | **已寫** | §6.8 | 中 |
| 8 | `OFDB011` | **已寫** | §6.5 | 淺(表格帶過 + 專屬缺陷) |
| 9 | **`OFDB019A`** | **已寫** | §6.4、§6.4.2 | **深** |
| 10 | **`OFDB019B`** | **已寫** | §6.4、§6.4.3 | **深** |
| 11 | `OFDB040` | **已寫** | §6.9.1 | 中 |
| 12 | `OFDB041` | **已寫** | §6.9.2 | 中(伺服端卡控失效深寫) |
| 13 | `OFDB161` | **已寫** | §6.5、§6.5.3 | 中 |
| 14 | `OFDB222` | **已寫** | §6.10 | 中 |
| 15 | `OFDB223` | **已寫** | §6.11 | 中 |
| 16 | **`OFDB281`** | **已寫** | §6.3(五個小節) | **深** |
| 17 | `OFDB286` | **已寫** | §6.12.1 | 中 |
| 18 | `OFDB287` | **已寫** | §6.12.2 | 中 |

**18 / 18 全部寫到,沒有「表格帶過」以外的遺漏。**

### D.1 本片沒有涵蓋、但相鄰的東西

| 對象 | 為什麼沒寫 |
|---|---|
| `Dev/ATLAS.OFDB/` 底下其他 70 幾支 `OFDB*`(`OFDB050` / `OFDB2xx` / `OFDB3xx` / `OFDB4xx` / `OFDB5xx` / `OFDB7xx`) | 不在本片的 18 支名單 |
| `OFDB284`(收益分配結算確認) | 同上,但它是 `OFDB281` 的直接下游,§6.3.5 有標 |
| `OFDB609`(網路交易後續處理) | 住 `Dev/ATLAS.EC/`,是 `OFDB003` 的補償批次,§8.3 有標 |
| `OFDB701` / `OFDB702` | 同專案但不在名單;它們也讀 `CHG_UPD_DTTM`,§8.1 / §8.2 有標 |
| `s_TA_OFDB003_Excute` 等 21 支 SP 的內容 | 不在版控(附錄 B.1) |
| `BMSM004` / `BMSM006` 的四眼細節 | 已在 `bms.md §4` |

### D.2 怎麼自己查

```
py -V:3.12 /docs/tools/atlas_scan.py --screen OFDB003
```

會列出該代號的六層路徑。本片 18 支逐一跑過,**六層全齊**。`DB/` 編碼混用,要讀 `DB/` 底下的檔請用:

```
import sys; sys.path.insert(0, '/docs/tools')
from atlas_scan import read_text
text, enc = read_text(path)
```

## 附錄 E. 讀本文時要注意的地方

前十篇實測撈到的缺陷型錄,**批次類特別容易中的排前面**。每條:缺陷 / 影響 / 錨點 / 嚴重度。同一支畫面出現多次的,以缺陷種類為準分開列。

### E.1 一律回報成功(批次第一大坑)

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | **`i = dbTA.ExecuteNonQuery(cmd, tran); i = 1;`** —— 回傳值收下來,下一行硬寫成 1,底下的 `if (i == 0)` 成為死碼 | `OFDB287` 重匯更新 0 列也算成功,畫面回報成功筆數 `j` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:124-126` | **高** |
| E1.2 | 同上那段 `if (i == 0)` 就算成立,也只是 `tran.Rollback()` 之後 `j += 1` 繼續跑迴圈,**沒有 `return`**;迴圈結束又 `tran.Commit()` | 在已 rollback 的交易上 commit;錯誤訊息被後面的成功訊息 `Clear()` 掉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:126-140` | **高** |
| E1.3 | `OFDB223` 七張表逐列 `UPDATE`,`ExecuteNonQuery` 回傳值完全丟掉,最後固定 `AddResultRow(true, 1, "")` | 改 0 列與改 100 萬列都顯示「成功、1 筆」;重跑空轉看不出來 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:141`、`:145` | **高** |
| E1.4 | `OFDB161` `int i = base.ExecuteNonQuery(...)` 之後直接 `tran.Commit()`,`i` 從未被檢查 | 定期買回 SP 影響 0 列照樣報成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:73-76` | 高 |
| E1.5 | `OFDB019A` `dbProduct.ExecuteNonQuery(cmd, tranUpdate);` 回傳值不接,成功筆數寫死 `AddResultRow(true, 1, "")` | CRS 產出畫面永遠顯示 1 筆 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:91`、`:102` | 中 |
| E1.6 | `OFDB281` 原本的 `if (i <= 0) { rollback … }` **整段被註解**,只靠 SP 的 `strMsg` 判成敗 | SP 忘了設 `strMsg` 就一律成功;`i` 還被當筆數回給畫面 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:411`、`:419-426` | 高 |
| E1.7 | `OFDB222` `i += ExecuteNonQuery(...)` 只累加不檢查;部分列更新 0 筆時整批仍報「執行成功」 | 關帳漏掉某些 `CTL022` 列不會被發現 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:104`、`:170`、`:179` | 中 |
| E1.8 | `OFDB040` 成功路徑**完全不塞 `Result` 列**,只有 `catch` 裡才有 | 呼叫端讀 `Result[0]` 會 index out of range;與 `architecture.md §6` 的 `CASM001_Ctl.AddData()` 同型 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:83-137` | **高** |
| E1.9 | `OFDB003` 的成功筆數 N 取自第一個 refcursor 的**列數**,不是 SP 回報的影響列數 | SP 若改成只吐一列摘要,畫面上「共變更 N 筆受益人資料」會變成 1 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:123` | 中 |

### E.2 執行鈕 / 卡控是空操作

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | **`OFDB041.Is_UnLock()` 恆回 `true`** —— 方法開頭 `Result.Clear()`,迴圈裡原本的三行 `AddResultRow` 被註解,結尾卻用 `Result.Count != 0` 判斷 | 伺服端「不可取消淨值鎖定」的閘門完全失效,只剩前端 Grid disable 在擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:209`、`:287-291`、`:333-336`;`Execute` 的用法在 `:65-68` | **高** |
| E2.2 | `OFDB281` 的「受益人扣繳類別未輸入不得產生」檢核:PO / Ctl / Pxy 六層都在,**只有 UI 的呼叫被註解** | 這條卡控現在不存在,但訊息字串還留著,讀 code 會以為有 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:150-156`,對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:280-320` | **高** |
| E2.3 | `OFDB281` UI 另有 27 行被註解的 `PROCESS_CODE` / `IsClose` 前置檢核,訊息含「基準日未完成日結轉作業,不得產生受益分配資料」 | 同上 —— 外殼還在,實際不跑 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs:103-129` | 中 |
| E2.4 | `OFDB004` 兩個下拉的「只列已覆核基金」過濾器被註解,事件方法變成空方法 | 事件還掛著,讀 code 會以為有過濾 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB004.cs:159-171` | 低 |
| E2.5 | `OFDB003` 的 `GetExecTime()` / `BMS001Chg()` / `GetOFD681()` 三支方法沒有可達呼叫端 | 讓人以為 `CTL016.BF_PROC_TIME` 有作用(它沒有) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:164-174`、`:358-393`、`:400-437` | 中 |
| E2.6 | `OFDB005` 的 `GetOFD681` / `GetExecTime` 同樣不可達(Pxy 沒開放) | 同上 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB005_Ctl.cs:57`、`:70` | 中 |
| E2.7 | **`OFDB019B` 的「刪除 xml 檔案」分支永遠刪不到東西** —— `strXML_FILE_NAME` 在該分支恆為空字串 | 使用者按了沒反應,也不報錯 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:138`、`:666-670` | 中 |
| E2.8 | `OFDB003` 的密碼補發段(PO 127 行 + Ctl 258 行)全部 `/* */` 註解,`OFD607A` 相關 refcursor 仍在宣告 | 近 400 行死碼,SP 仍被要求吐兩個沒人用的 cursor | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:176-303`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:243-500` | 中 |
| E2.9 | **`OFDB019B` 有一支 670 行的 `XOFDB019B_AfterExecuteButtonClicked`,Designer 沒掛** | 整個 UI 檔 1,348 行有一半是死的;裡面是 CRS XML v1.0 的完整實作 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:675-1344`,對照 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.designer.cs:499-500` | **高** |
| E2.10 | 活著的那支 `OFDB019B_AfterExecuteButtonClicked` 裡另有 197 行 `/* */`(v1.0 版) + 三段被註解的 `ControllingPerson` / `PaymentAmnt` 欄位 | 申報欄位到底有沒有出,要逐段確認 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:468-664`、`:823-844`、`:882-904`、`:1002-1026` | 中 |
| E2.11 | `OFDB003_Pxy.Query()` 是空殼,永遠回 `(true, 0, "")` | 任何人呼叫它會拿到「成功、0 筆」 | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:77-82` | 低 |

### E.3 整支跑不起來的死碼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | **`OFDB001` / `OFDB005` / `OFDB011` / `OFDB161` 四支的 `dbTA` 恆為 null** —— `BasicEVAPO` 的建構子賦值被註解,子類也沒補 | 四支畫面按執行必定 `NullReferenceException`,被 Pxy 包成 `ServerSideError` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26`、`:169-172`;用法 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:33` | **高** |
| E3.2 | 同四支的 SQL 是 T-SQL(`EXEC @x=@y`、`SqlDbType`、`TOP 1`、`ISNULL()`、`[OFD342]`),連線卻是 Oracle | 就算 `dbTA` 修好也跑不起來,要整支重寫 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:41`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:45`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:65`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB161_PO.cs:58` | **高** |
| E3.3 | 同四支的 Ctl **不繼承 `BaseController`**,直接 `new PO()`,不走 `DataAccessPool` / VDB 轉換框架 | 與其餘 14 支的行為模型完全不同;框架的例外處理與 log 都不會生效 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB001_Ctl.cs:14`、`:43` | 中 |

### E.4 交易與 rollback 的破口

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E4.1 | `catch` 直接讀 / 呼叫 `tran`,而 `tran` 在 `try` 內才賦值 —— 本片**至少八支**都這樣寫 | `BeginTransaction()` 之前或當下失敗(DB 不通)時,真正的錯誤被 `NullReferenceException` 蓋掉;`finally` 的 `Dispose()` 再炸一次 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:132-147`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:715-735`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:104-109`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:435-447`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:148-160`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:117-131` | **高** |
| E4.2 | `catch (SqlException)` 在 Oracle 連線上永遠不會命中,但本片**七支**都寫了 | 死碼 + 誤導;真正的 `OracleException` 走的是後面的泛型 catch | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:132`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:117`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:148`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:364`、`:435` | 中 |
| E4.3 | **`OFDB003` 的 LDAP 推送在 commit 之後**,失敗時把成功訊息 `Clear()` 換成失敗訊息 | 使用者以為整批失敗,實際 `CHG_UPD_DTTM` 已經蓋上;重按只會拿到「查無可執行之資料」 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:60-61`、`:112-113`、`:178-179` | **高** |
| E4.4 | `OFDB287` 在 rollback 之後繼續迴圈並 commit(見 E1.2) | 交易狀態不一致 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:126-140` | 高 |
| E4.5 | `OFDB281` 的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉** | 例外不進框架 log,只剩畫面一行 `ex.Message` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:446` | 中 |
| E4.6 | `OFDB004` 開兩個交易(`dbProduct` + `dbPTPF`),中間任何一段失敗兩邊一起 rollback,但兩次 commit 之間不是原子的 | 第一個 commit 成功、第二個失敗時,TA 庫已寫、PTPF 庫沒寫 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:710-711` | 中 |

### E.5 Oracle 三值邏輯與比較寫法

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | `NVL(PROC_CODE,' ') <> 'D'` 有包 `NVL`(**正確**),但同檔另有多處寫 `NVL(PROC_CODE,' ') = ' '`,兩種語意不同 | 欄位存 NULL 與存空白的情形被混在一起判 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:170` 對照 `:243` | 中 |
| E5.2 | **`OFDB286` 同一支 PO 對 `OFD131A.TERMINATE_DATE` 用了兩種寫法:退匯段是 `TERMINATE_DATE = ' '`(一個空白字元的等值比較),取消退匯段是 `trim(TERMINATE_DATE) IS NULL`** | 兩段命中的列集不一樣 —— 退匯改到的列,取消退匯可能改不回來(反之亦然)。欄位若存 NULL 或多個空白,退匯段靜默不更新且不提示 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:79` 對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:257` | **高** |
| E5.3 | `CHG_UPD_DTTM` 的「未生效」判準全庫有**三種寫法**:`SUBSTR(NVL(TRIM(x),'19000101'),1,8) = '19000101'`、`NVL(x,' ') = ' '`、`x = '1900/01/01'` | 資料若存成 `'1900/1/1'` 或含前導空白,三種寫法答案不同 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:318`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:236`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2050` | **高** |
| E5.4 | `OFDB041` SQL 用 `ALLOT_CTL_CODE >= '3'` 撈,C# 卻用 `== "3"` 判 | 控制碼 `'5'` / `'6'` 時 SQL 撈到、C# 三個分支都不成立,`IS_UNLOCK` 停在預設值 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:244-246` 對照 `:298`、`:314` | 高 |
| E5.5 | `OFDB041` 申購側與贖回側用 `if` / `else if` | 申購側有列時贖回側整段不判 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:293`、`:309` | 高 |
| E5.6 | `OFDB003.Check()` 拿 `DATE` 欄位直接跟 `'yyyyMMdd'` 字串比(`IsDate = false`),同支的 `BMS001Chg()` 卻用 `TO_CHAR(...,'YYYYMMDD')`(`IsDate = true`) | 兩支方法對同一組參數的語意不同;前者靠 Oracle 隱含轉換,NLS 設定一改就爆 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:320-322` 對照 `:169-170` | 中 |

### E.6 `AND` / `OR` 括號、無鍵 UPDATE

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | **`OFDB223` 的 `UPDATE` 只用 `AGENT_ID` + `AGENT_CODE` 當條件,七張交易表、沒有任何日期或單號範圍** | 一列設定改掉歷史上全部該銷售機構的交易。設計如此,但威力等同無鍵 UPDATE | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:129-133` | **高** |
| E6.2 | `OFDB223` 的換號迴圈沒有防「鏈式置換」:設定檔有 A→B 與 B→C 兩列時,第二列會把剛改成 B 的也改成 C | 結果取決於迴圈順序,而且回報一律成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:123-139` | **高** |
| E6.3 | `OFDB286` 的 `OFD131A` 更新條件 `(FUND_ID = :FUND_ID OR FUND_ID = 'ALL FUNDS') AND …` —— **括號有加,沒有中雷**,但 `'ALL FUNDS'` 是寫死值 | 換站台若不用這個萬用值,語意會變 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:77` | 低〔客戶特定〕 |
| E6.4 | `OFDB041` 的兩段 SQL 用 `(A >= x OR B >= y OR C = 'Y')` 包在 `AND` 後面 —— **括號也有加**,無雷 | — | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:244-246` | — |

### E.7 `CommandTimeout = 0`(無逾時保護)

本片**十二支**把 `CommandTimeout` 設成 0,其中四支還加了註解「此程式讓它永久跑」。

| 畫面 | 錨點 |
|---|---|
| `OFDB003` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:65` |
| `OFDB001` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:177` |
| `OFDB002` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:106` |
| `OFDB005` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB005_PO.cs:47` |
| `OFDB019A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:87` |
| `OFDB019B` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:102` |
| `OFDB040` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:103` |
| `OFDB222` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:94`、`:146` |
| `OFDB223` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:135` |
| `OFDB281` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:391` |
| `OFDB011` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB011_PO.cs:534` |
| `OFDB008` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:80` 等十處 |

影響:長跑期間 Remoting 執行緒與資料表鎖都被佔住,沒有任何自動中斷。嚴重度:中。與 `architecture.md §6` 提到的 CAS 報表、TMK 報表同一種病,但本片的是**寫入型**批次,後果更大。

### E.8 字串串接進 SQL

| # | 位置 | 值的來源 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | `OFDB002` 的 `VOC_NO`(只包成 `N'值'`) | **畫面輸入框** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:167`、`:226-236` | 中 |
| E8.2 | `OFDB003` / `OFDB004` / `OFDB019A` / `OFDB019B` 共用的 `AddParam()` 把值包成 `'值'` 直接串 | 畫面參數(含 `BF_CHG_NO`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:466-481`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:843-856` | 中 |
| E8.3 | `OFDB004` 的 `GetSQLByCheckFund()` 與 `BuildSQLString()` 用 `string.Format` 串 `FUND_ID` | 基金代碼下拉(值域受控) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:295`、`:1031`、`:1041`、`:1077-1103` | 中 |
| E8.4 | `OFDB040` 的 `FUND_LOCK` 用 `string.Format` 串進 `UPDATE`,同段的 `FUND_ID` 卻有綁參數 | 單選鈕(只會是 `Y`/`N`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:92`、`:97` | 中 |
| E8.5 | `OFDB223` 的表名用 `"UPDATE " + split[i]` 串接 | 程式內寫死的七張表名 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB223_PO.cs:129` | 低 |
| E8.6 | `OFDB019A` / `OFDB019B` 的 `MESSAGE_REF_ID` 組字串把 `YEARS` 串進 SQL | 畫面年度輸入 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:147-148` | 中 |

### E.9 寫死常數與位置取參數

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E9.1 | **`OFDB019B` 的申報年度寫死 `'2019'`**(同一段在 `OFDB019A` 是取畫面參數) | 2020 年以後產出的訊息編號年度永遠是 2019 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:159-160` | **高**〔客戶特定〕 |
| E9.2 | `OFDB019A` / `OFDB019B` 用 `ucomMSG_TYPE.Rows[3].Hidden = true` **以位置索引**隱藏 `CRS703` | 下拉來源是 `CTL014` 的 `690`,順序一改就隱藏錯的那一項 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:42`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:44` | 中 |
| E9.3 | `OFDB019B` 的執行功能用 `CheckedIndex + 2` 換算 SP 參數 | 單選鈕多一項就整組錯位 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:78`、`:149`、`:666` | 中 |
| E9.4 | CRS 公司識別碼 `TW-86385617` 寫死在 SQL 字串裡 | 換站台要改程式 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019A_PO.cs:147` | 中〔客戶特定〕 |
| E9.5 | `OFDB222` 自動建次一日關帳列的條件寫死 `AGENT_ID == "0" && AGENT_CODE != "A0901" && AGENT_CODE != "OP101"` | 新增銷售機構要改程式 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:107-109` | 中〔客戶特定〕 |
| E9.6 | `OFDB004` 的 `CreateOFD085Row()` 有 12 個寫死的業務預設值(轉換日期基準、匯費收取方式、折數 `-1M` …) | 業務規則藏在程式碼裡,不在 `CTL014` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:905-914` | 中 |
| E9.7 | `OFDB004` 短線費只在 `OFDM260.Rows.Count == 1` 時才複製 | 0 列或 2 列以上靜默不複製,不提示 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:660` | 中 |
| E9.8 | `OFDB004` 用 `"OFDM233"` 當權限識別字,實際寫的是 `OFD260A` / `OFD261A` | 權限稽核軌跡對不上實際動的表 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:662` | 中 |
| E9.9 | `OFDB003` 的 `CHG_DATE` 空值哨兵寫死 `'19000101'` | 與 `DateTimeHelper` 的 `1900/01/01` 約定綁在一起,SP 端必須認得 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:75` | 低 |
| E9.10 | `OFDB003` 把 `iUpdateID` 綁成 `NVarchar2`,其餘字串參數用 `Varchar2` | 型別不一致,靠 Oracle 隱含轉換 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:78` | 低 |
| E9.11 | `OFDB019B` 一處參數名多一個冒號:`AddInParameter(cmd91, ":YEARS", …)` | 若框架不幫忙去掉,該段查詢會 `ORA-01008` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB019B_PO.cs:260` | 中(需實測) |

### E.10 檔案處理與編碼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E10.1 | **`OFDB281.cs` 與 `OFDB281.Designer.cs` 是 UTF-16LE**(BOM `FF FE`),`Dev/ATLAS.OFDB/` 底下唯二 | 用 UTF-8 / cp950 開是亂碼;grep 工具預設抓不到內容 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.cs`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB281.Designer.cs` | 中 |
| E10.2 | `OFDB008` 申報檔用 `Encoding.Default`(作業系統 ANSI 字碼頁) | 換一台系統語系不同的機器,主管機關申報檔編碼就變了 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:213`、`:246`、`:296`、`:321`、`:348` | 中〔客戶特定〕 |
| E10.3 | `OFDB008` / `OFDB019B` 寫檔一律 `new StreamWriter(path, false, …)`,同名檔直接覆蓋不提示 | 重跑會蓋掉前一次的產出 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:213`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:158` | 中 |
| E10.4 | `OFDB019B` 不檢查輸出目錄是否存在(`OFDB008` 有檢查) | `DirectoryNotFoundException` 直接冒到框架 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:140-144` 對照 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:166-167` | 中 |
| E10.5 | `OFDB007` 匯入 Excel 整段包在 `catch { ShowMessage(…) }`,沒有例外變數、沒有 log | 檔案鎖住 / driver 沒裝 / 型別錯,一律同一句話 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:221-224` | 中 |
| E10.6 | `OFDB007` 匯入迴圈:第一列出錯之後,後面所有列都因 `ErrorCount < 1` 不成立而**不進資料表** | 「迴圈遇壞列後全部吃掉」的變形;錯誤有顯示,但資料靜默流失 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB007.cs:176-193` | 中 |

### E.11 例外被吞、fail-open

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E11.1 | **`OFDB281` 六支檢核方法的 `catch` 全部 `return true`(放行)** | 查詢一炸,前置卡控全部通過 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:88-92`、`:124-128`、`:163-167`、`:200-205`、`:235-239`、`:268-272` | **高** |
| E11.2 | `OFDB281.Check_CTL_CODE` 查不到 `OFD303A` 的列時也回 `true`(只有 `POST_CTL_CODE == "N"` 才擋) | 「那天根本沒有過帳控制列」等於「已過帳」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:259-266` | **高** |
| E11.3 | `OFDB003` 的 `UpdateLDAPCustomer` / `UpdateLDAPStatus` 逐列 `catch` 後什麼都不做 | 單列的 null / API 例外靜默跳過,不進失敗 log、不進錯誤訊息 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:99-102`、`:165-168` | 高 |
| E11.4 | `OFDB003` 的 `UpdateLDAPStatus` 失敗通知信被註解,只剩畫面訊息 | 密碼狀態同步失敗沒有人會收到通知 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:111` | 中 |
| E11.5 | `OFDB001.CheckCTL_DATE` 例外時回傳 `-1`,呼叫端當成筆數用 | `-1` 會被當成「有資料」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB001_PO.cs:152-161` | 中 |
| E11.6 | `OFDB004.Check()` 例外時 `AddResultRow(false, 0, "")` —— **空訊息** | 使用者看到空白錯誤;與 `architecture.md §3.11` 記的 `CASM001_PO` 七處空訊息同型 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:278-282` | 中 |
| E11.7 | `OFDB286` / `OFDB287` 多處 `AddResultRow(false, 0, "")` 空訊息 | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:170`、`:200`、`:288`、`:295`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:130`、`:144`、`:267`、`:276` | 中 |

### E.12 索引 / 陣列越界

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12.1 | **`OFDB002`:`if (j < 1 |  | !OFDB002[0].RESULT)` 成立後立刻讀 `OFDB002[0].MSG`** | SP 回 0 筆時 `IndexOutOfRangeException`,不是「查無資料」 |
| E12.2 | `OFDB040` 成功不塞 `Result`,上層讀 `Result[0]`(見 E1.8) | 同型 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB040_PO.cs:83-137` | 高 |
| E12.3 | `OFDB019A` / `OFDB019B` 多處 `vdb.UIView.CRSP001_TEMP.Rows[0]["…"]` 未先檢查列數 | 查無資料時越界 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:84`、`:244-245` | 中 |
| E12.4 | `OFDB008` 讀 `view.UIView.OFDB008_CO[0].CO_LID` 前有做 `Rows.Count > 0` 判斷(**沒中雷**) | — | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB008.cs:195` | — |

### E.13 複製貼上的分身

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E13.1 | `OFDB019A_PO`(552 行)與 `OFDB019B_PO`(565 行)實質差異只有五處,其餘全是空白 | 任何修正要記得改兩份;`'2019'` 這顆雷就是漂移出來的 | 見 §6.4.1 | **高** |
| E13.2 | `AddParam()` / `GetParamValue()` 這兩個私有方法在本片至少**四支 PO** 裡逐字重複(`OFDB003` / `OFDB004` / `OFDB019A` / `OFDB019B`),而且 `IsDate` 分支的行為還不一樣 | 同一個名字在不同 PO 有不同語意 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:447-504`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:824-879` | 中 |
| E13.3 | `OFDB286` 與 `OFDB287` 的 `Execute` 結構幾乎一致(匿名 PL/SQL + 逐列 + `ExeType` 分流),但 `OFDB286` 有檢查 `i`、`OFDB287` 把 `i` 寫死成 1 | 兩支行為不一致,維護時容易照錯的那支改 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB286_PO.cs:164-170` 對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB287_PO.cs:124-131` | 中 |

### E.14 中文名 / 中繼資料錯誤

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E14.1 | `OFDB003Model.xsd` 的 `ORG_ID_TYPE` Caption 填成「ORG_CELL_PHONE」、`NEW_ID_TYPE` 填成「NEW_CELL_PHONE」、`NEW_ALLIN3` 填成「NEW_ID_NO」 | Caption 是全庫唯一中文名來源,這幾欄的名字是錯的 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd` | 中 |
| E14.2 | 同檔 `ORG_ID_NO` 與 `ORG_ALLIN3` **共用同一個 Caption「ID_NO」** | 兩個不同欄位在 UI 上同名 | 同上 | 中 |
| E14.3 | `OFDB005Model.xsd` 的 `REL_PROC_TIME`、`OFDB040Model.xsd` 的 `STATUS`、`OFDB161Model.xsd` 的 `PERIOD_REDEM_DATE` 的 Caption 填的是英文欄名 | UI 上顯示英文 | 見 §2.5 | 低 |
| E14.4 | `OFDB004Model.xsd` 還留著 `OFDM233` 的 DataTable,但程式已不複製 | 讀 xsd 會以為有 17 張明細 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:73-74` | 低 |
| E14.5 | `OFDB002` 在方法裡改共用 PO 實例的 `MasterTable` | 連線池共用實例,非執行緒安全 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB002_PO.cs:68` | 中 |
| E14.6 | `OFDB008_PO` 宣告了 `dbPTPF` 卻從未使用 | 死欄位,每次 new PO 多開一個連線設定 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB008_PO.cs:34` | 低 |
| E14.7 | `OFDB003_Ctl.Execute` 取了 `model` 卻不用 | 每次執行多一次整包 VDB 轉換 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:57` | 低 |
| E14.8 | `OFDB019A_Ctl.Execute` 同樣取了 `model` 不用 | 同上 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB019A_Ctl.cs:55` | 低 |
| E14.9 | `OFDB019A.cs` 的規格註解裡留了一段 T-SQL(`SELECT TOP 1 … WHERE YEARS = '2020'`),與下方實際執行的 Oracle 查詢不同 | 讀規格會被誤導 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:194-199` | 低 |
| E14.10 | `OFDB004.Execute<T>` 回傳的是新 new 的 `mModelTo` 而非傳入的 `mModel`,全片唯一 | 有人照別支習慣改成 `return mModel;` 會靜默吃掉所有結果 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:363`、`:738` | 中 |
| E14.11 | `OFDB222` 的 `strTRAN_TYPE` 沒有 `else`,非 1 非 2 時 `strUpdate` 是空字串 | 直接拿空字串去 `GetSqlStringCommand` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB222_PO.cs:79-93` | 低 |
| E14.12 | `OFDB004` 的 13 張檢核表 ≠ 16 張複製表:`OFD074` / `OFD076` / `OFD261A` 會被寫入但不在檢核清單 | 目的基金在這三張表已有資料時不會被擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:113-270` 對照 `:55-77` | 中 |

### E.15 這些看起來像 bug,其實不是

| 觀察 | 為什麼不是 bug |
|---|---|
| `OFDB281` 呼叫 `Check_DIV_ACC_NO(FUND_ID, FUND_ID)` 兩個參數一樣 | 收益分配專戶資料就放在 `OFD085A` 的「自己轉自己」那一列上,由 `OFDB004.CreateOFD085Row` 的 `FUND_ID == SWITCH_FUND_ID` 分支建立(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:892-901`)。**不要改** |
| `OFDB004` 的 `OFD081A` 查詢是 `SELECT '<基金>' AS FUND_ID FROM dual` | 註解直接說「此 MasterTABLE 只用來騙過 evapo 用的」(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:976-977`),是刻意的 |
| `OFDB286` 的 `(FUND_ID = :FUND_ID OR FUND_ID = 'ALL FUNDS')` | 括號有加,`AND`/`OR` 沒有洩漏 |
| `OFDB007` 按「執行」什麼都不做 | `AfterExecuteButtonClicked` 第一行 `e.Cancel = true` 是刻意的,這支只列印 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `Dev/ATLAS.OFDB` 的 18 支 B 批次。重點:`OFDB003`(BMS 變更單生效引擎,接上 `bms.md §2`)、`OFDB004`(基金複製,非日結)、`OFDB019A`/`OFDB019B` 成對比較、`OFDB281`(與 `OFDM281` 同表)、四支未移轉的 SQL Server 死碼。 |

由 build_doc.py v2.0.0 於 2026-09-15 11:53 產生 · 標題 114 · 圖 5 · 表格 94 · 程式錨點 495 · § 連結 87 · 引用檢查：畫面 53（缺 0） · Table 45（缺 0） · 結果集 43（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
