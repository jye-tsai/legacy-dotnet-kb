ATLAS 知識庫 — 15-模組-OFDB批次

本檔合併以下文件:modules/ofdb.md、modules/ofdb3.md、modules/ofdb4.md、modules/ofdb5.md


============================================================
【文件】kb/modules/ofdb.md
============================================================

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

============================================================
【文件】kb/modules/ofdb3.md
============================================================

# ATLAS OFDB3 模組(OFD 批次第 3 片)全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:OFD 前綴的 B 批次全庫 165 支,拆多片;本篇只涵蓋指定的 **35 支**(清單見 §3.3)。`OFDB003` / `OFDB004` / `OFDB281` 等另外 18 支在 `ofdb.md`,不重述。 **建議讀法**:趕時間只讀四段 —— **§0.2(本片最反直覺的六件事,其中兩件會直接害你查錯地方)**、§6.1(`OFDB600`:排程表在資料庫不在 Windows 排程器)、§6.2(`A` 後綴在批次上的真相)、附錄 E(踩雷)。

> ⚠ **本片的業務意義**(§0)由表名、Designer 內的中文標籤字串、SQL 註解與訊息字串**推測**。ATLAS 沒有把畫面中文名放進版控,本片 35 支沒有任何一支有 `this.Text`。 ⚠ **〔客戶特定〕**:Remoting 端點主機位址、落地路徑 `C://Vendor//WindowService//`、`SourceType='107'` 交易途徑代碼、`SYSTEM_ID='1'`/`'2'` 網路/語音、`EC_SYSTEM_TYPE='1'`、`FN_CLASS_TYPE='2'` 為本站台的值。 ⚠ **〔共用〕**:`BMS001A` / `BMS001CHG` 由 BMS 維護;`OFD081A`(基金主檔)、`CTL014`(代碼值域)、`COD009`(員工)、`OFD068`(銷售機構)同時服務多模組(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層與命名例外看 `architecture.md §2`、四眼看 `architecture.md §3`、畫面型別看 `architecture.md §6`、Remoting 與 WindowsService 看 `architecture.md §8.4`。**不要整份讀**。本片與 `ofdb.md` 有 5 支重疊(`OFDB600` `OFDB605` `OFDB606` `OFDB609` `OFDB680`),那 5 支在 §6.9 只寫補充,不重抄。

## 0. 系統邊界與角色

### 0.1 這 35 支管什麼(推測)

**一句話:這 35 支跟 `ofdb.md` 那 18 支一樣不是一條流程,但散開的方式不同 —— `ofdb.md` 那片是「同一個專案裡的業務雜燴」,本片是「同一組代號散在三個不同專案裡」。**

代號前三碼都是 `OFD`、第四碼都是 `B`,但實體檔案分屬三個專案:

| 專案 | 支數 | 業務線(推測) | 代號 |
|---|---|---|---|
| `Dev/ATLAS.EC/` | **19** | **網路 / 語音下單(電子交易)的後台批次** | `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` `OFDB606` `OFDB607` `OFDB608` `OFDB609` `OFDB610` `OFDB611` `OFDB612` `OFDB615` `OFDB616` `OFDB671` `OFDB672` `OFDB673` `OFDB680` `OFDB690` |
| `Dev/ATLAS.OTAB/` | **10** | **境外基金交易平台(OTA)的對外資料產生批次** | `OFDB553` `OFDB561` `OFDB562` `OFDB563` `OFDB564` `OFDB600A` `OFDB601A` `OFDB602A` `OFDB603` `OFDB604A` |
| `Dev/ATLAS.OFDB/` | **9** | **檔案匯入匯出 / 集保媒體 / 統計初始化** | `OFDB540` `OFDB560` `OFDB562` `OFDB563` `OFDB564` `OFDB565` `OFDB566` `OFDB570` `OFDB580` |

(合計 38 > 35,因為 `OFDB562` / `OFDB563` / `OFDB564` **三支同時存在於 `ATLAS.OFDB` 與 `ATLAS.OTAB`**,六層各一份,兩份都在編譯 —— `architecture.md §2.6` 已列為「真分岔」。本片把它們當一支算,但兩份都讀。)

再往下切成六群業務:

| 群 | 管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| **A 電子交易截止與拋轉** | 網路 / 語音委託到了截止時間後整批截單、產生正式交易單、拋轉到帳務 | **`OFDB600`**、`OFDB601`、`OFDB602`、`OFDB604`、**`OFDB605`**、`OFDB611` | `OFD620A` `OFD651A` `OFD655A` `OFD657A` `OFD658A` `OFD661A` `OFD601CHG` `OFD615A` |
| **B 網路開戶與密碼** | 網路開戶資料處理、密碼函寄發、LDAP 帳號同步、停用與解鎖 | `OFDB606`、`OFDB607`、`OFDB608`、**`OFDB609`**、`OFDB610`、`OFDB615`、`OFDB616` | `OFD600` `OFD601` `OFD607` `OFD607A` `LOG602` `BMS001A` |
| **C 手續費與員工交易** | 扣款手續費彙總、員工及員工關係人交易審核、審核人員設定、換員編換機構 | `OFDB612`、`OFDB671`、`OFDB672`、`OFDB673`、`OFDB690` | `OFD621A` `OFD678A` `OFDB672` `COD009` `OFD068` |
| **D 基金警示發送** | 基金事件警示逐日發送 | **`OFDB680`** | `OFD680A` `OFD681A` `OFD682A` `OFD683A` `OFD684A` |
| **E 境外基金平台對外資料** | 對境外基金公司產生申購 / 贖回 / 轉換 / 定期定額的交換資料 | `OFDB600A`、`OFDB601A`、`OFDB602A`、`OFDB603`、`OFDB604A`、`OFDB553`、`OFDB561` | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615` `OFD663` `OFD664` `OFD666` `OFD667` |
| **F 集保媒體與檔案交換** | 扣款授權書核印的送核 / 退件 / 註銷、傳檔收檔媒體、月報與基金基本資料匯入、統計初始化、股東會名單 | `OFDB562`、`OFDB563`、`OFDB564`、`OFDB565`、`OFDB566`、`OFDB560`、`OFDB570`、`OFDB580`、`OFDB540` | `OFD562` `OFD562_TSCDLOG` `OFD564` `FND003` `MON001` `OFD570A` `OFD541A` |

### 0.2 最反直覺的六件事

**一、本片 35 支在索引裡一張主檔都沒宣告 —— 這不是缺陷,是批次的通例。**

`atlas_scan.py --screen <代號>` 對這 35 支全部印「主檔 —」「明細 —」。查下去原因很單純: `xTableMapping` 是給 `BaseEVADaoPO` 的四眼存檔機制用的(`architecture.md §4.1`), **批次不走四眼、不走 `base.Update`,所以不填。** 本片 35 支的 PO 一律自己 `new Database("TA", DbServerType.Oracle)`、自己組 SQL 或呼叫 SP、自己管交易。 `architecture.md §6.4` 講的「B 跟 I 是同一份程式碼」在本片 100% 成立。抽樣反推見 §2.1。 **副作用要記住:`atlas_scan --table <表名>` 反查「誰在用這張表」時,本片 35 支一支都不會出現**(§2.6)。

**二、四支畫面的六層檔案全在,但整組不在 csproj 裡 —— 根本沒被編譯。**

`OFDB606` / `OFDB610` / `OFDB611` / `OFDB690` 的 UI、Designer、FormProxy、Control、Interface、OracleDao **五層全部**不在對應的 csproj:

| 層 | csproj | 缺的檔 |
|---|---|---|
| UI | `Dev/ATLAS.EC/Source/UI/UI.EC/UI.EC.csproj` | `OFDB606.cs` `OFDB610.cs` `OFDB611.cs` `OFDB690.cs` 與各自 `.Designer.cs` |
| FormProxy | `Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/FormProxy.EC.csproj` | `OFDB606_Pxy.cs` `OFDB610_Pxy.cs` `OFDB611_Pxy.cs` `OFDB690_Pxy.cs` |
| Control | `Dev/ATLAS.EC/Source/Control/Control.EC/Control.EC.csproj` | `OFDB606_Ctl.cs` `OFDB610_Ctl.cs` `OFDB611_Ctl.cs` `OFDB690_Ctl.cs` |
| PO(Oracle) | `Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj` | `Oracle/OFDB606OracleDao.cs` `Oracle/OFDB610OracleDao.cs` `Oracle/OFDB611OracleDao.cs` `Oracle/OFDB690OracleDao.cs` |
| PO(Interface) | 同上 | `Interface/IOFDB606.cs` `Interface/IOFDB610.cs` `Interface/IOFDB611.cs` `Interface/IOFDB690.cs` |

**不是漏掉一兩個檔,是整組一起被拿掉**,同一批被拿掉的還有 `OFDM681` / `OFDM691` / `OFDM692` / `OFDM693`(不在本片)。 `MSSQL\OFDB606_PO.cs` 等舊檔反而**還留在 csproj 裡**(`Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj:169`、`:173`、`:176`), 但那些檔案整支被註解掉(下一條),所以留著也編不出東西。

**為什麼拿掉?** 這四支的 Control 還停在舊寫法,直接 `new <代號>_PO()`: `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB606_Ctl.cs:43`、 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB610_Ctl.cs:126`、 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB690_Ctl.cs:35`。而那個 `<代號>_PO` 類別**已經不存在了**(整支註解掉),所以只要把這四組加回 csproj,建置就會紅。

〔假設〕**它們是 Oracle 移轉時沒改完、乾脆整組從建置排除的殘留。** 依據:(a) 四支的 Ctl 都沒有 `InitializeDataAccessPool` + `DataAccessPool.Add(new *OracleDao())` 這一組新寫法, 而 EC 專案其餘 15 支 `OFDB6*_Ctl` 全部有(見 §3.3);(b) `OFDB611_Ctl` 是半套 —— `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB611_Ctl.cs:37` 用舊的 `OFDB611_PO`、 `:59` 用新的 `OFDB611OracleDao`,改到一半停手的形狀最明顯。

**三、`MSSQL\` 底下 15 支 PO,每一行都被 `//` 註解掉,但全在 csproj 裡。**

實測 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/` 的 15 個 `OFDB6*_PO.cs`(`OFDB600` `601` `602` `604` `605` `606` `607` `608` `609` `610` `611` `612` `680` `690` `691`): 非空行合計 **4,614 行,被註解 4,614 行,100%**。 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB600_PO.cs:1` 第一行就是 `//using System;`。

要查「這支批次以前在 SQL Server 上怎麼寫」還讀得到,**但不要拿它當現行邏輯讀** —— 現行的是 `Oracle\<代號>OracleDao.cs`。這跟 `ofdb.md §0.2` 第一件事(四支 `BasicEVAPO` 未移轉)是同一個時代的殘骸,但處置不同: 那邊留著會 NRE,這邊留著只是佔 4,600 行空間與每次全文搜尋的雜訊。

**四、`600` 系列的 `A` 後綴在批次上不是境內 / 境外,是「不同專案的不同程式」。**

`ofd7.md` 查證過 OFD 的 `A` 後綴在**畫面**上多半是 `FUND_TYPE` 境內(`'2'`)/ 境外(`'1'`)之分, 值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`。 **批次上不成立。**`OFDB600` / `OFDB601` / `OFDB602` / `OFDB604` 住 `Dev/ATLAS.EC/`, `OFDB600A` / `OFDB601A` / `OFDB602A` / `OFDB604A` 住 `Dev/ATLAS.OTAB/`, namespace 分別是 `Vendor.Product.TA.PO.EC` 與 `Vendor.Product.TA.PO.OTAB`。逐對做行級相似度,四對全部落在 11%~20%,等於只有 `using` 與樣板骨架相同。數據與逐對比較見 §6.2。

**五、本片有排程,而且排程表在資料庫裡,不在 Windows 工作排程器。**

`ofdb.md §0.2` 第三件事說「那 18 支沒有任何一支是排程」。本片不一樣: `OFDB600` / `OFDB609` / `OFDB680` 三支各有一個 WindowsService 專案, 服務內掛一個 60 秒的 `System.Timers.Timer`,每分鐘把 `DateTime.Now.ToString("HHmm")` 跟一個**從資料庫讀來的時刻字串**比對, 相等就跑一次。所以「幾點跑」是資料表欄位,改排程不用碰 Windows 排程器也不用重編:

| 服務 | 時刻來源 | 錨點 |
|---|---|---|
| `OFDB600` | `OFD606A.EC_BUC_LIMIT_TIME` / `EC_REMIT_LIMIT_TIME` / `EC_REDEM_LIMIT_TIME` / `EC_RSP_LIMIT_TIME` 四欄 UNION `OFD600A.MEMBER_CHG_LIMIT_TIME`,再各自加 `OFD600A.LIMIT_TIME_BUFFER` 分鐘 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292` |
| `OFDB609` | `OFD600A.OPEN_ACC_PROCESS_TIME`(`SYSTEM_ID='1' AND EC_SYSTEM_TYPE='1'` 寫死) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:569-574` |
| `OFDB680` | `OFD680A.ALERT_LIMIT_TIMES`(**整張表沒有 WHERE**,取第一列) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:704` |

其餘 32 支沒有服務程式,只能人工按「執行」。 **repo 內沒有任何 `.bat` / `.cmd`,`Main()` 也沒有 `string[] args`** (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13`), 所以缺陷型錄裡「位置取參數傳錯資料」那一型在本片**不成立**。完整觸發方式見 §3.3 與 §6.1.2。

**六、`OFDB680` 那支服務宣告要走 Remoting,設定檔卻沒有 Remoting 區段,但有明文資料庫連線字串。**

`ofdb.md` 已經查證 `OFDB680` 的 `App.config` **0 個** `system.runtime.remoting`,而 `OFDB600` / `OFDB609` **各 2 個**且含 `<wellknown>`。本片把它擴大查證,並補上關鍵的另一半:**`OFDB680` 的 `App.config` 反過來多了 `<connectionStrings>`**, `OFDB600` / `OFDB609` 那兩份**沒有**。三支服務的部署形態因此完全不同 —— 完整的表與推論在 §3.4。

### 0.3 四種資料存取路徑

| 路徑 | 特徵 | 畫面 | 支數 |
|---|---|---|---|
| **EC 新世代:`*OracleDao` + DAO 池** | Ctl `InitializeDataAccessPool` → `DataAccessPool.Add(new <代號>OracleDao())`,PO 自建 `Database("TA", DbServerType.Oracle)`,不繼承任何 PO 基底,只實作 `I<代號>PO` | `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` `OFDB607` `OFDB608` `OFDB609` `OFDB612` `OFDB615` `OFDB616` `OFDB671` `OFDB672` `OFDB673` `OFDB680` | 15 |
| **EC 舊世代:`new <代號>_PO()` 直接 new** | Ctl 不建池,直接 new;被 new 的類別已整支註解 → 不可編譯 → 整組退出 csproj | `OFDB606` `OFDB610` `OFDB611` `OFDB690` | 4 |
| **OFDB / OTAB:裸 DAO + 介面** | PO 掛 `[PODbType(DbServerType.Oracle)]`,自建 `Database`,Ctl 走 `DataAccessPool` | `OFDB540` `OFDB560` `OFDB562`(兩份)`OFDB563`(兩份)`OFDB564`(兩份)`OFDB565` `OFDB570` `OFDB580` `OFDB553` `OFDB561` `OFDB600A` `OFDB601A` `OFDB602A` `OFDB603` `OFDB604A` | 15 |
| **舊基底 `BasicEVAPO`(但只借外部元件)** | 繼承 `BasicEVAPO` 卻完全不用它的連線,純粹為了掛 `ImportFileEngine` | `OFDB566` | 1 |

> `OFDB566` 值得單獨講:它繼承 `BasicEVAPO`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB566_PO.cs:17`), 而 `architecture.md §3.1.1` 已證明 `BasicEVAPO` 的 `dbTA` 恆為 null、73 支畫面存檔會 NRE。 **但 `OFDB566` 沒事** —— 它整支沒有碰過任何 `dbTA` / `dbPTPF`,寫入完全交給 `ImportFileEngine`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB566_PO.cs:63`,無原始碼,從呼叫端反推)。這是本片唯一「繼承了壞基底但不用它」的一支,跟 `ofdb.md §0.2` 那四支跑不起來的要分開看。

### 0.4 不管什麼

| 不管 | 誰在管 |
|---|---|
| 網路 / 語音下單的**前台**(客戶怎麼下單) | EC 的對外系統,不在 repo;本片只處理後台落地的 `OFD620A` / `OFD651A` 等 |
| 交易的**四眼覆核** | OFD 的 M 片;本片沒有一支呼叫 `EVA()`(全片 grep `EVAType`:0 命中) |
| 淨值怎麼算 | OFD 其他片;`OFDB601` / `OFDB602` 只吃 NAV 日期當參數 |
| 受益人資料變更的**生效** | `OFDB003`(`ofdb.md §6.1`);`OFDB609` 只補推 LDAP |
| 境外基金公司端怎麼收檔 | 對方系統;`OFDB60*A` 只負責把資料寫進 `OFD66*` 交換表 |
| 郵件實際寄送 | `ServerMailUtility` / `GenXMLHelper`(無原始碼,從呼叫端反推) |
| 集保 / Hi-Trust 端的核印 | 外部;`OFDB562`~`OFDB564` 只切 `OFD562` 的狀態並寫 `OFD562_TSCDLOG` |
| 所有 SP 的內部邏輯 | Oracle 端。本片呼叫 **26 支 SP + 2 支 Function**,**repo 內腳本 0 支**(附錄 B) |

### 0.5 使用角色(推測)

本片 35 支**沒有任何一支做角色 / 權限檢查**。全片 grep `MGM_CD` / `MANGR_CODE`:0 命中。跟人有關的只有把 `PermissionInfo[0].UserID` 塞進 SP 參數或 `CREATEID` 欄 (例 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:83`),以及服務端寫死的 `"AutoJob"` (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:86`)。

| 角色(推測) | 依據 | 用哪些畫面 |
|---|---|---|
| 電子交易作業人員 | `OFDB605` 的訊息「尚未執行交易截止時間，請先執行OFDB600程式」(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:52`) | `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` `OFDB611` |
| 網路開戶 / 客服人員 | `OFDB610` 的「僅列出『請客服郵寄開戶表格』名單」核取方塊(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB610.Designer.cs:456`) | `OFDB606` `OFDB607` `OFDB608` `OFDB609` `OFDB610` `OFDB615` `OFDB616` |
| 法遵 / 員工交易審核人員 | `OFDB671` 的「審核人員設定」群組框(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB671.Designer.cs:144`)、`OFDB600` 寄的「員工及員工關係人交易【審核結果】通知信」 | `OFDB671` `OFDB672` `OFDB673` `OFDB690` `OFDB600` |
| 境外基金作業人員 | `OFDB601A` 的「境外基金公司代碼」查詢條件(`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB601A.designer.cs:232`) | `OFDB600A` `OFDB601A` `OFDB602A` `OFDB603` `OFDB604A` `OFDB553` `OFDB561` |
| 集保 / 扣款作業人員 | `OFDB564` 的「注意：執行註銷時，同時修改 1)Hi-Trust 開戶主檔之扣款狀態」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB564.designer.cs:164`) | `OFDB562` `OFDB563` `OFDB564` `OFDB565` `OFDB566` |
| 統計 / 報表人員 | `OFDB580` 的「結帳交易 / 月庫存」執行項目(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB580.designer.cs:136`) | `OFDB560` `OFDB570` `OFDB580` `OFDB540` |

**畫面層級的存取控制交給框架選單與 `UseCaseSecurity`(無原始碼,從呼叫端反推),不在本片程式內。**

### 0.6 全域開關

| 開關 | 位置 | 效果 | 錨點 |
|---|---|---|---|
| `OFD600A.LIMIT_TIME_BUFFER` | `OFD600A` | 截止時間的緩衝分鐘數,同時決定 `OFDB600` 服務下次觸發時刻與送給 SP 的 `CHECK_DATE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:85` |
| `OFD606A.EC_BUC_YN` / `EC_REMIT_YN` / `EC_REDEM_YN` / `EC_RSP_ALLOT_YN` | `OFD606A` | 逐基金逐交易別的「網路可交易」旗標;`'Y'` 才會進 `OFDB600` 的排程時刻 UNION | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:272`、`:278`、`:284`、`:290` |
| `OFD600A.OPEN_ACC_PROCESS_TIME` | `OFD600A` | `OFDB609` 服務的每日觸發時刻 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:569-574` |
| `OFD680A.ALERT_LIMIT_TIMES` | `OFD680A` | `OFDB680` 服務的每日觸發時刻 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:704` |
| `EC_ALLOT_PCODE` / `EC_REDEM_PCODE` / `EC_RSP_PCODE` / `EC_RSP_CHG_PCODE` / `EC_RSP_TRN_CODE` / `EC_RSP_TRN_CHG_CODE` / `EC_CHG_PCODE` | `OFD620A` `OFD651A` `OFD655A` `OFD661A` `OFD657A` `OFD658A` `OFD601CHG` | 七張表各自的處理碼:`'0'` 未處理 / `'1'` 已處理。`OFDB600` 的執行前後筆數就是數這個 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:367`、`:434` |
| `OFD615A.BMS_CTL_CODE` | `OFD615A` | 拋轉控制碼:`'1'` 未拋轉 / `'2'` 已拋轉。`OFDB605` 的功能切換全看它 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:121`、`:293` |
| `SYSTEM_ID` | `OFD600A` `OFD615A` `OFD601CHG` | 交易途徑:`'1'` 網路 / `'2'` 語音。值域在 `CTL014` 的 `SourceType='107'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:64`、`:102-113` |
| `Environment.UserName == "SYSTEM"` | 三支服務的 `Program.cs` | **不是設定檔而是執行帳號**:等於 `SYSTEM` 才跑 `ServiceBase.Run`,否則進 Console 偵錯模式 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/Program.cs:18`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/Program.cs:14` |
| `OFDB560` 的 `FILE_TYPE` | 畫面選項 | `'1'` = 投信公司基金基本資料(寫 `FND003`)、其餘 = 每月資料(寫 `MON001`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:59`、`:110` |
| `OFDB580` 的 `EXEC_ITEM` | 畫面選項 | `'1'` = 結帳交易(`S_TRADE_INITIAL`,日期 `yyyyMMdd`)、其餘 = 月庫存(`S_MONTH_INITIAL`,日期 `yyyyMM`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB580_PO.cs:80`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB580.cs:47` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDB3 片全景:35 支散在三個專案、六群業務、四種資料存取路徑，三支有服務排程，26 支 SP 全在版控外
圖中文字:① 同一組代號 OFDB，散在三個不同專案裡 / ATLAS.EC 19 支 / 網路 / 語音下單後台 / ATLAS.OTAB 10 支 / 境外基金平台對外資料 / ATLAS.OFDB 9 支 / 檔案匯入匯出 集保媒體 / OFDB562 563 564 / OFDB 與 OTAB 各一份 / ② 六群業務，彼此不相干 / A 交易截止與拋轉 / 600 601 602 604 605 611 / B 開戶與密碼 / 606 607 608 609 610 615 616 / C 手續費與員工交易 / 612 671 672 673 690 / D 基金警示 / 680 / E 境外平台對外資料 / 553 561 600A 601A 602A 603 604A / F 集保媒體與檔案交換 / 540 560 562 563 564 565 566 570 580 / ③ 四種資料存取路徑 —— 決定一支能不能跑 / EC 新世代 15 支 / OracleDao + DAO 池 / EC 舊世代 4 支 / 606 610 611 690 整組不在 csproj / OFDB / OTAB 裸 DAO 15 支 / 自建 Database 自管交易 / BasicEVAPO 1 支 / OFDB566 但不用它的連線 / ④ 本片有排程，而且排程時刻在資料庫欄位裡，不在 Windows 排程器 / OFDB600 服務 / OFD606A / OFD600A 的時刻欄 / OFDB609 服務 / OFD600A OPEN_ACC_PROCESS_TIME / OFDB680 服務 / OFD680A ALERT_LIMIT_TIMES / 其餘 32 支 / 只能人工按執行 / ⑤ 全片 26 支 SP，repo 內腳本 0 支 —— C# 端看不到資料被改成什麼 / 26 支 SP / 版控外 / GenXMLHelper / 信件，無原始碼 / LDAPAPIHelper / 外部帳號 API / Import / ExportFileEngine / 檔案收送 / SerialNo / 流水號
```

*圖:圖 1 全景。橘框=本片主要入口或重點;橘虛框=要留意的行為(未編譯、跨專案重複);灰虛框=不受影響或本片以外;黑框=無原始碼。第③列決定一支能不能跑 —— 第二格那四支根本沒被編譯。*

### 1.2 批次讀寫的表

本片三個專案各吃各的表,交集只有四張:`BMS001A`(受益人主檔)、`OFD081A`(基金主檔)、 `CTL014`(代碼值域)、`OFD068` / `OFD068A`(銷售機構)。下圖把「誰寫、誰只讀」分開;跨模組的讀取端見 §8。要注意 **EC 那 19 支幾乎不直接 UPDATE**, 寫入全丟給 SP,C# 端只負責前置檢核與撈結果集 —— 所以掃 `UPDATE` / `INSERT` 找不到它們動了什麼。

### 1.3 依觸發方式 / 有無 Remoting 分群

三支有 WindowsService 的(`OFDB600` / `OFDB609` / `OFDB680`)跟其餘 32 支的部署形態完全不同, 而且這三支彼此之間又分成兩種(兩支走 Remoting、一支直連 DB)。圖見 §3.4 前面那張。

### 1.4 主要維護畫面的四眼與卡控順序

**本片沒有 M 畫面**(見 §4),所以沒有這張圖。四眼真正發生的地方在 OFD / BMS 的 M 片。本片與四眼唯一的接點是 `OFDB612` 讀了 `EVASTATUS_V` 這個檢視 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs`),用途是過濾掉未覆核的資料 —— **過濾(無提示)**,不是阻擋。

### 1.5 一日作業泳道

本片 35 支**沒有一條貫穿的一日順序**,但 A 群(電子交易)有一條硬相依鏈,而且是本片唯一「上游沒跑下游會被明確擋下」的一條:

| 順序 | 卡在哪 | 擋法 |
|---|---|---|
| **`OFDB600` 截止** → `OFDB601` / `OFDB602` / `OFDB604` 產單 → **`OFDB605` 拋轉** | `OFD615A` 當日有沒有列 | `OFDB605` 查不到當日 `OFD615A` 就回「尚未執行交易截止時間，請先執行OFDB600程式」→ **阻擋**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:50-54`) |
| `OFDB672` 申請換員編 → `OFDB673` 審核 | `OFDB672` 表有沒有同 key 的未審資料 | `OFDB672` 查到就回「同銷售機構及員編變更已在OFDB673審核中，不可重覆執行」→ **阻擋**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:33-37`) |
| `OFDB601A` 產生申購資料 → 下單確認 → (要回覆才能刪) | 四段確認旗標 | `OFDB601A` 八個 `Check_*` 逐一 **阻擋**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:135-170`、`:200-233`) |
| `OFDB562` 送集保 → `OFDB563` 退件 / `OFDB564` 註銷 | `OFD562.SEAL_PROCESS` 狀態碼 | 靠 SQL 的 `SEAL_PROCESS = '01'` / `'02'` 條件 **過濾(無提示)**,不是阻擋(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:122`) |

## 2. 資料模型

```text
[圖] OFDB3 片動到的資料表分成五群，以及有一整批表名只存在於 SQL 字串或畫面標籤裡
圖中文字:EC 交易群:OFDB600 把七張表的處理碼從 0 推到 1，OFDB605 再拋轉 / OFD620A 申購 / EC_ALLOT_PCODE / OFD651A 買回 / EC_REDEM_PCODE / OFD655A 657A 658A 661A / 定額四張 / OFD601CHG 受益人變更 / EC_CHG_PCODE / OFD615A / BMS_CTL_CODE 拋轉碼 / EC 開戶與密碼群:OFD607A 是交會點，四支都寫它 / OFD607A / 密碼 狀態 寄發日 / OFD607 / 同步用 / LOG602 / 稽核軌跡 四眼欄是假的 / OFD600 OFD601 / 網路主檔 / BMS001A / BMS 維護 唯讀 / 員工交易群:OFDB672 寫申請、OFDB673 審核，OFDB671 整表洗掉重寫 / OFDB672 表 / 畫面代號同時也是表名 / OFDB672_T1 T2 T3 / 對應 OFD221A OFD251A RSP006A / OFD678A / 審核人員 Status 寫死 301 / COD009 OFD068 / 員工 銷售機構 唯讀 / 集保與檔案群:OFD562 是狀態機的核心，兩個專案各有一份程式在動它 / OFD562 / SEAL_PROCESS 01 / 02 / OFD562_TSCDLOG / 本片產生的軌跡表 / FND003 MON001 / OFDB560 匯入 / OFD570A / 12 個泛用 FIELD 欄 / OFD541A / OFDB540 名單 / 只存在於 SQL 字串或畫面標籤裡的表 —— xsd 完全查不到 / tbl_SA_LOG 等五張 / 只出現在 OFDB580 的畫面標籤 / OFDB680_XML / OFDB680 寄信用 / AA_Customer Z_OPACT / repo 內無定義 / V_FUND EVASTATUS_V / View 定義不在版控
```

*圖:圖 2 批次讀寫的表。橘框=本片會寫的核心表;橘虛框=要留意(表名躲在字串裡、四眼欄是假的、跨專案兩份程式);灰虛框=別的模組維護;黑框=定義不在版控。最後一列改欄位時 xsd 查不到，只能 grep。*

### 2.1 主表與明細:35 支全空,而且這是對的

`atlas_scan.py --screen` 對本片 35 支全部印「主檔 —」「明細 —」。抽五支逐一反推,結論一致:

| 抽樣 | 有沒有 `xTableMapping` | 實際怎麼動資料 | 錨點 |
|---|---|---|---|
| `OFDB560` | 無(PO 只實作 `IOFDB560_PO`,不繼承任何基底) | 自建 `Database("TA")`,自己寫 `INSERT INTO fnd003` / `DELETE MON001` + `INSERT INTO MON001`,自己 `BeginTransaction` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:31-33`、`:61`、`:114`、`:121` |
| `OFDB600` | 無(只實作 `IOFDB600PO`) | 全部交給 SP `S_EC_IPJB600_EXCUTE`,C# 端只 `LoadDataSet` 收一個 refcursor 進 `OFDB600_EMAIL` 這張**非實體表** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:18`、`:44`、`:71-73` |
| `OFDB672` | 無 | 自己組 `insert into OFDB672 values(...)`(**沒有欄位清單**) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:43-52` |
| `OFDB580` | 無 | 只呼叫 `S_TRADE_INITIAL` 或 `S_MONTH_INITIAL`,一行 SQL 都沒有 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB580_PO.cs:83`、`:90` |
| `OFDB601A` | **有基底沒宣告** —— 繼承 `BaseEVADaoPO` 但建構子的 `Initial()` 是空的 | 八個 `Check_*` 用 `dbProduct` 自己查,寫入交給 SP `S_OTA_OFDB601A_EXE` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:67`、`:87-89`、`:175` |

**正式回答:批次不宣告主檔是通例,不是異常。** `xTableMapping` 的唯一消費者是 `BaseEVADaoPO` / `MultiRowEVAPO` 的 `Add` / `Update` / `Delete` 四眼流程 (`architecture.md §4.1`、`architecture.md §4.2`)。批次的輸出是「DB 狀態被 SP 改掉」或「產生一個檔案」, 不是「把一個 typed DataSet 存回去」,所以那條路徑整個用不到,宣告了也沒人讀。 `ofdb.md §0.3` 那片 18 支只有 3 支宣告,本片 35 支 0 支 —— **比例一路往下,方向一致。**

三支唯一「掛了 EVA 基底」的(`OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` / `OFDB562`(OTAB) / `OFDB563`(OTAB) / `OFDB564`(OTAB))掛基底的理由只有一個:**借 `dbProduct` 這個現成連線**, 不是為了四眼。判準很直接 —— 它們的 `Execute` 從頭到尾沒有一行 `base.Add` / `base.Update`。

### 2.2 因此 `atlas_scan --table` 反查會漏掉什麼

這是本片最實用的一條操作結論:

| 你想查 | 用 `atlas_scan --table <表>` 會得到 | 為什麼 | 正確做法 |
|---|---|---|---|
| 「誰在寫 `OFD620A`?」 | **本片 35 支一支都不會出現** | 反查靠的是 PO 的 `xTableMapping` 宣告,本片 0 宣告 | grep 表名字串;但 EC 那 19 支表名多半躲在 SP 裡,grep 也查不到 |
| 「誰在寫 `OFD562`?」 | 只會出現 `Dev/ATLAS.OFDB` 那份(它有 `TableMapping("OFD562","OFD562")`) | 舊世代 `MultiRowEVAPO` 才宣告 | 兩份都要看,而且那份**跑不起來**(§2.5) |
| 「改 `OFD615A` 影響誰?」 | 空 | 同上 | 讀本篇 §3.3 的「寫入」欄 |

> ⚠ **更麻煩的一層:EC 那 19 支的表名有一半不在 .NET 程式裡。** 例如 `OFDB600` 的 `Execute` 只有一行 `GetStoredProcCommand("S_EC_IPJB600_EXCUTE")` (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:48`),它到底 UPDATE 了哪些表, **repo 內完全查不到**(SP 腳本 0 支,附錄 B)。本篇附錄 A 只能列出「C# 端看得到的表」, 另外從同支的 `GetBefExecRowCount` / `GetAftExecRowCount` 反推 SP 動了哪七張表(§6.1.4)。

### 2.3 「表」的三種形狀

| 形狀 | 例 | 怎麼認 |
|---|---|---|
| **實體表** | `OFD562` `OFD570A` `FND003` `MON001` `OFDB672` | SQL 裡 `FROM` / `INSERT INTO` 直接出現 |
| **查詢結果集的形狀名**(不是表) | `OFDB600_EMAIL` `OFDB600_TIMES` `OFDB600_COUNT` `OFDB609_TIMES` `OFDB680_TIMES` `OFDB680_COUNT` `DOWNFILE` | 只出現在 `LoadDataSet(cmd, ds, "<名字>")` 的第三個參數,對應 xsd 裡的一張 DataTable |
| **同名但意義不同** | `OFDB672` | **既是畫面代號也是實體表名**。`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:67` 的 `FROM OFDB672 A` 查的是表,不是畫面 |

`OFDB672` / `OFDB672_T1` / `OFDB672_T2` / `OFDB672_T3` 這一組是本片唯一「用畫面代號當表名」的例子。 `_T1` / `_T2` / `_T3` 三張明細分別餵給 `OFD221A`(申購單)、`OFD251A`(買回單)、`RSP006A`(定額契約)三張 DataTable —— **表名與 DataTable 名完全對不起來**,`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:99-106` 是唯一的對照來源。

### 2.4 主鍵與四眼欄位

本片沒有一支走四眼,所以沒有 `STATUS` / `EVASTATUS` / `VERIFY_*` / `APPROVE_*` 的寫入。會被本片寫進去的「人跟時間」欄位只有三組:

| 欄位 | 值從哪來 | 錨點 |
|---|---|---|
| `CREATEID` | `PermissionInfo[0].UserID`,或服務端寫死的 `"AutoJob"` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:90`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:86` |
| `CREATEDATE` | Oracle `sysdate`,不是 C# 的時間 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:51` |
| SP 的 `wCreateID` / `wUPD_USER` / `iUSER_ID` | 同上 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:68`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:184`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:83` |

> ⚠ `OFDB673` 的 `USERID` 參數**不是按鈕的操作人,是被審核那筆資料的申請人**: `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:88` 把 grid 裡的 `CREATEID` 欄當 `USERID` 傳下去。所以 SP 拿到的「使用者」是申請人,審核人是誰在 repo 內查不到。

### 2.5 `OFDB562` / `OFDB563` / `OFDB564` 兩個專案的兩份,不是分岔,是新舊世代

`architecture.md §2.6` 把這三支列為「真分岔,兩份都在編」。本片可以把它講得更精確: **兩份確實都在編,但只有 `ATLAS.OTAB` 那份能跑。**

| 項目 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/` |
|---|---|---|
| PO 基底 | `MultiRowEVAPO`(`OFDB562_PO.cs:14`) | `BaseEVADaoPO`(`OFDB562_PO.cs:56`) |
| SQL 方言 | **T-SQL**:`[OFD562]` 中括號、`ISNULL()`、`SUBSTRING()`、`@BF_NO` 參數 | Oracle:`NVL()`、`:BF_NO` |
| `SqlDbType` / `OracleDbType` 次數 | 562:46 / 0 · 563:21 / 0 · 564:15 / 0 | 562:0 / 62 · 563:0 / 56 · 564:0 / 28 |
| 連線 | `dbTA.CreateConnection()`(`OFDB562_PO.cs:28`) | `dbProduct`(基底管) |
| 有沒有宣告主檔 | **有**,`TableMapping("OFD562","OFD562")`(`OFDB562_PO.cs:18-19`) | 無 |

**致命的是連線物件本身是 null。**`MultiRowEVAPO` 宣告 `protected Database dbTA = null;` (`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:18`),建構子裡唯一會賦值的兩行**被註解掉** (`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:169-174`), 而 `Dev/ATLAS.OFDB/` 那三份 PO **沒有任何一行**給 `dbTA` 賦值。所以 `dbTA.CreateConnection()`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:28`)一執行就是 `NullReferenceException`。

這跟 `architecture.md §3.1.1` 講的 `BasicEVAPO` 是**同一顆雷的另一個基底** —— `architecture.md` 那一節只點名 `BasicEVAPO`,本片補上 `MultiRowEVAPO` 也是同一個寫法, 而且 `ofdb.md §0.2` 第一件事講的四支(`OFDB001` / `OFDB005` / `OFDB011` / `OFDB161`)是 `BasicEVAPO`, 本片這三支是 `MultiRowEVAPO`,病因一樣、基底不同。

> 〔假設〕**`Dev/ATLAS.OFDB/` 那三份是 SQL Server 時代的原版,Oracle 移轉時整組複製到 `ATLAS.OTAB` 重寫, 原版忘了刪。**依據三條交叉:(a) 方言統計 46/0 vs 0/62 乾淨得不像巧合;(b) 舊版用舊基底、新版用新基底; (c) 新版多查了 `BMS001A` / `OFD019A` 兩張 Oracle 側的表,舊版查的是 `BMS001` / `OFD020V` / `OFD030` (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:56-60` vs `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:119-120`)。 **沒有直接證據說選單指到哪一份**,repo 內查不到選單表。要確認只能到站台看 `xOneStepProcessForm` 實際載入的組件。

### 2.6 與其他模組共用的表

| 表 | 本片怎麼用 | 誰維護 |
|---|---|---|
| `BMS001A` | 唯讀,取 `BF_NAME` / `ID_NO` / `MAIL_ADDR` / `CELL_PHONE` | BMS(`bms.md §2`) |
| `BMS001CHG` | `OFDB605` 唯讀 | BMS 開單,`OFDB003` 生效(`ofdb.md §6.1`) |
| `OFD081A` / `OFD081V` | 唯讀,取基金名稱 / 幣別 / 小數位 | OFD 的 M 片 |
| `CTL014` | 唯讀,代碼值域(`SourceType='107'` 交易途徑) | COD / CTL |
| `COD006A` / `COD009` | 唯讀,代碼說明與員工主檔 | COD |
| `OFD068` / `OFD068A` | 唯讀,銷售機構;`OFDB540` 走 `table(f_TA_GetAgent())` 這個 TVF | OFD |
| `FSK003` | `OFDB612` 唯讀 | FSK |
| `AA_Customer` | `OFDB612` 唯讀 —— **`ofdb.md 附錄 A.3` 已標「只存在於 SQL 字串裡的表」,本片再中一次** | 外部 / 未知 |
| `LOG602` | `OFDB609` / `OFDB615` / `OFDB616` **寫入**,操作軌跡 | 共用 log 表 |
| `RSP006A` | `OFDB672` / `OFDB673` 唯讀(定額契約) | RSP(`rsp.md`) |

### 2.7 狀態碼(從程式反推,標來源)

| 欄位 | 值 | 意義(推測) | 來源 |
|---|---|---|---|
| `EC_ALLOT_PCODE` 等七個 `*_PCODE` | `'0'` / `'1'` | 未處理 / 已處理。`OFDB600` 跑完會把 `'0'` 變 `'1'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:367` 與 `:434` 兩段 SQL 的差別只在這個值 |
| `OFD601CHG.EC_CHG_PCODE` | `'0'` / `'1'` / `'2'` | `'2'` 是 `OFDB605` 判斷「已拋轉」的值 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:233` |
| `OFD615A.BMS_CTL_CODE` | `'1'` / `'2'` | 未拋轉 / 已拋轉 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:121`、`:293` |
| `SYSTEM_ID` | `'1'` / `'2'` | 網路 / 語音〔客戶特定〕 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:102`、`:106`;顯示名在 `CTL014` `SourceType='107'`(`:64`) |
| `OFD562.SEAL_PROCESS` | `'01'` / `'02'` | 待送核 / 已送核(推測) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:122`;舊版同值 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:67-69` |
| `OFDB601A` 的 `StrXEC` | `'1'` / `'2'` | 產生資料 / 整批刪除 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:129`、`:193` |
| SP 的 `WCODE` | `'I'` / `'D'` | 新增 / 刪除,**程式碼裡寫死** | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:182`、`:245` |
| `TRAN_PAY_WAY` | `'01'` / `'02'` | 單筆申購-匯款 / 單筆申購-扣款(程式註解自己寫的) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:183` |
| `OFDB600_EMAIL.TRADE_TYPE` | `'1'` / `'2'` / `'3'` | 申購 / 買回 / 轉申購 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:134`、`:177`、`:216` |
| `ReturnRowCount == 99` | 99 | 三支服務共用的「這不是錯,不要寫 EventLog」哨兵值 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:91`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:88`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:83` |

> `ReturnRowCount == 99` 這個哨兵值**在 repo 內找不到任何寫入端** —— 三支服務都只讀不寫, 寫它的只能是版控外的 SP。意思是「99 代表沒資料可跑,屬正常」,但這是從三處一致的用法推的,**標假設**。

## 3. 畫面清冊

```text
[圖] 35 支依觸發方式與有無 Remoting 分成三群:手動 28 支、手動加服務 3 支、不可執行 4 支
圖中文字:① 手動 28 支:UI 繼承 xOneStepProcessForm，按執行鈕才跑 / xOneStepProcessForm / 28 支唯一的觸發來源 / 無自有 App.config / Remoting 設定走主程式 / 主程式設定不在 repo / architecture 8.1 / ② 手動 + 服務 3 支:60 秒 Timer 比對 HHmm，時刻來自資料庫 / OFDB600 服務 / Remoting 2 區段 + wellknown / OFDB600_Pxy / 真的是遠端代理 / 應用伺服器 / Control + PO 跑在那邊 / OFDB609 服務 / Remoting 2 區段 + wellknown / OFDB609_Pxy / 真的是遠端代理 / 應用伺服器 / 同上 / OFDB680 服務 / config 0 個 remoting 區段 / OFDB680_Pxy / 沒有 wellknown 就是本機物件 / 服務自己這台直連 DB / config 有明文連線字串 / ③ 不可執行 4 支:六層檔案都在，但五個 csproj 都沒有它們 / OFDB606 610 611 690 / UI Pxy Ctl Interface Dao 全缺 / Ctl 還在 new 舊 PO / 而舊 PO 整支被註解 / 加回 csproj 會編不過 / 要先改 Ctl 的取得方式 / ④ 三支服務共通的兩顆雷 / Environment.UserName 要等於 SYSTEM / 否則卡在 Console.ReadLine 不報錯 / 排程時刻在 DB 欄位 / 改設定不用重編也不碰排程器 / log 路徑寫死 C 槽 / 整檔讀再整檔覆寫
```

*圖:圖 3 觸發方式與 Remoting 分群。橘框=真的走 Remoting 的;橘虛框=要留意(設定與程式不一致、整組沒被編譯);灰虛框=跑在別台或別處;黑框=不在 repo。第②群裡 OFDB680 那一列跟上面兩列部署方式完全不同。*

### 3.1 維護 M

**本片無 M 畫面。**35 支代號第四碼全部是 `B`,而且 UI 全部繼承 `xOneStepProcessForm` (`architecture.md §6.4`),沒有四眼工具列、沒有 `Add` / `Update` / `Delete` 入口。

### 3.2 查詢 I

**本片無 I 畫面。**不過要留意:12 支 B 批次的 PO 同時實作了 `Query` / `Select` 方法 (`OFDB605` `OFDB607` `OFDB612` `OFDB615` `OFDB616` `OFDB671` `OFDB672` `OFDB673` `OFDB561` `OFDB562` `OFDB563` `OFDB564`),讓使用者先查出清單、勾選、再按執行。 `architecture.md §6.4` 說「B 跟 I 是同一份程式碼」在這裡是字面成立的 —— 它們是「查詢畫面 + 一顆執行鈕」。

### 3.3 批次 B(35 支)

四個附加欄的定義:

- **觸發方式**:`手動` = 只能在 `xOneStepProcessForm` 按「執行」;`手動+服務` = 另有 WindowsService,時刻取自資料庫欄位。

- **Remoting**:指該支**自己的** `App.config` 有沒有 `system.runtime.remoting`。32 支沒有自己的設定檔(走主程式的,而主程式設定檔不在 repo,`architecture.md §8.4` 已標)。

- **交易邊界**:`C#` = C# 開 `BeginTransaction`、SP 或 SQL 跑在其中、C# `Commit`;`C#×2` = 分兩段各自 commit;`無` = 不開交易。

- **重跑安全**:`阻擋` = 有明確前置檢查會擋第二次;`覆蓋` = 先 DELETE 再 INSERT;`不保護` = 重跑會重複或再動一次;`只讀` = 無副作用;`不可執行` = 未編譯或必 NRE。

| 代號 | 專案 | 中文名(推測) | SP / Fn | 觸發方式 | Remoting | 交易邊界 | 重跑安全 |
|---|---|---|---|---|---|---|---|
| `OFDB540` | OFDB | 專案名單產生(股東會 / 投票)〔推測〕 | `s_TA_OFDB540` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB553` | OTAB | 契約異動轉入(收件日次一營業日)〔推測〕 | `S_OTA_OFDB553_EXE` | 手動 | 無自有 config | C# | 阻擋(SP 回訊息則 rollback) |
| `OFDB560` | OFDB | 投信公司基金每月資料 / 基金基本資料匯入 | — | 手動 | 無自有 config | C# | `MON001` 覆蓋 / `FND003` **不保護** |
| `OFDB561` | OTAB | 集保上傳確認 / 回復 | — | 手動 | 無自有 config | C# | 不保護(靠勾選) |
| `OFDB562` | OTAB + **OFDB** | 扣款授權書:已送集保確認 | — | 手動 | 無自有 config | C# | 不保護;**OFDB 那份不可執行** |
| `OFDB563` | OTAB + **OFDB** | 扣款授權書:退件處理(取消申請 / 重新送核) | — | 手動 | 無自有 config | C# | 不保護;**OFDB 那份不可執行** |
| `OFDB564` | OTAB + **OFDB** | 扣款授權書:註銷處理 | — | 手動 | 無自有 config | C# | 不保護;**OFDB 那份不可執行** |
| `OFDB565` | OFDB | 傳送檔案(扣款授權書核印 / 客戶資料傳檔) | — | 手動 | 無自有 config | C#×2(TA + PTPF) | 不保護 |
| `OFDB566` | OFDB | 接收檔案(扣款授權書核印收檔) | — | 手動 | 無自有 config | **無**(交給 `ImportFileEngine`) | 不保護 |
| `OFDB570` | OFDB | 匯入 / 匯出檔案(日期批號) | `S_TA_OFDB570_GET` | 手動 | 無自有 config | C#×2 | 覆蓋(先 `DELETE ... WHERE Data_ID`) |
| `OFDB580` | OFDB | 結帳交易 / 月庫存初始化 | `S_TRADE_INITIAL` / `S_MONTH_INITIAL` | 手動 | 無自有 config | C# | 不保護(SP 內未知) |
| **`OFDB600`** | EC | **網路交易時限截止處理作業(手動 / 自動)** | `S_EC_IPJB600_EXCUTE` | **手動+服務**(`OFD606A` / `OFD600A` 的時刻欄) | **有,2 個區段 + `<wellknown>`** | C# | 靠 `*_PCODE = '0'` 過濾 |
| `OFDB600A` | OTAB | 境外平台:資料處理日期批次〔推測〕 | `S_OTA_OFDB600A_EXE` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB601` | EC | 網路申購資料產生 / 拋轉 | `S_EC_IPJB601_EXCUTE` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB601A` | OTAB | 境外平台:產生申購資料 / 整批刪除 | `S_OTA_OFDB601A_EXE` | 手動 | 無自有 config | C# | **阻擋(8 個 `Check_*`)** |
| `OFDB602` | EC | 網路贖回資料產生 / 拋轉 | `S_EC_IPJB602A_EXCUTE` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB602A` | OTAB | 境外平台:產生贖回資料 | `S_OTA_OFDB602A_EXE` | 手動 | 無自有 config | C# | 阻擋(同 601A 家族) |
| `OFDB603` | OTAB | 境外平台:產生轉換資料 | `S_OTA_OFDB603_EXE` | 手動 | 無自有 config | C# | 阻擋(同 601A 家族) |
| `OFDB604` | EC | 網路定期定額收件 / 異動拋轉 | `S_EC_IPJB604_EXCUTE` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB604A` | OTAB | 境外平台:產生定期定額申請 / 異動資料 | `S_OTA_OFDB604A_EXE_ADD` / `S_OTA_OFDB604A_EXE_MOD` | 手動 | 無自有 config | C# | 阻擋(同 601A 家族) |
| **`OFDB605`** | EC | **拋轉 / 拋轉回復(資料處理日期)** | `S_EC_IPJB605_EXCUTE`、`F_EC_GETOFD615AREMARK` | 手動 | 無自有 config | C# | **阻擋(要求先跑 `OFDB600`)** |
| **`OFDB606`** | EC | 網路開戶資料處理(含 e-mail / 地址維護)〔推測〕 | — | **不可執行** | 無自有 config | C# | **不可執行(整組不在 csproj)** |
| `OFDB607` | EC | 網路開戶資料處理 | `S_EC_OFDB607_Excute` | 手動 | 無自有 config | C# | 不保護 |
| `OFDB608` | EC | 受益人網路資料處理(單筆) | `S_EC_OFDB608_Excute` | 手動 | 無自有 config | C#(**開在 try 外**) | 不保護 |
| **`OFDB609`** | EC | **網路交易後續處理作業(含「更新 LDAP 資料」)** | `S_EC_OFDB609_Excute` | **手動+服務**(`OFD600A.OPEN_ACC_PROCESS_TIME`) | **有,2 個區段 + `<wellknown>`** | C# | 不保護 |
| **`OFDB610`** | EC | 開戶表格 / 自黏標籤列印名單 | `s_OFDB610_Get`、`s_ECFunGetAccountData` | **不可執行** | 無自有 config | C# | **不可執行(整組不在 csproj)** |
| **`OFDB611`** | EC | 申購付款方式處理〔推測〕 | `s_OFDB611_Excute` | **不可執行** | 無自有 config | C# | **不可執行(整組不在 csproj)** |
| `OFDB612` | EC | 扣款手續費 / 扣款結果維護 | — | 手動 | 無自有 config | C# | 不保護(勾選逐列 UPDATE) |
| `OFDB615` | EC | 網路交易 / 查詢密碼與停用維護 | — | 手動 | 無自有 config | C# | 不保護 |
| `OFDB616` | EC | 密碼函寄送名單與 Excel 匯出 | — | 手動 | 無自有 config | C# | 不保護 |
| `OFDB671` | EC | 員工交易審核人員設定 | — | 手動 | 無自有 config | C#×2(TA + PTPF) | 覆蓋(先 `DELETE OFD678A`) |
| `OFDB672` | EC | 員工代碼 / 銷售機構整批換號 —— 申請 | `S_TA_OFDB672_GET`(查詢) | 手動 | 無自有 config | C# | **阻擋(同 key 已在審核中)** |
| `OFDB673` | EC | 員工代碼 / 銷售機構整批換號 —— 審核 | `S_TA_OFDB673_EXE` | 手動 | 無自有 config | C# | 不保護 |
| **`OFDB680`** | EC | **基金警示資料發送** | `S_EC_OFDB680_GET` | **手動+服務**(`OFD680A.ALERT_LIMIT_TIMES`) | **宣告要走,但 config 0 個區段** | C# | 覆蓋(先 `DELETE OFDB680_XML WHERE DATACHECK`) |
| **`OFDB690`** | EC | 取消員工交易(依日期) | `s_OFDB690_Get` | **不可執行** | 無自有 config | C# | **不可執行(整組不在 csproj)** |

小計:

| 欄 | 分布 |
|---|---|
| 觸發方式 | 手動 **28** · 手動+服務 **3** · 不可執行 **4** |
| Remoting | 無自有 config **32** · 有(2 區段 + wellknown)**2** · 宣告要走但 config 沒有 **1** |
| 交易邊界 | C# 單一交易 **28** · C# 兩段交易 **3** · 無交易 **1** · 不可執行但程式碼寫了交易 **3**(`OFDB606` / `OFDB610` / `OFDB690`;`OFDB611` 也算在四支裡) |
| 重跑安全 | 阻擋 **6** · 覆蓋 **4** · 不保護 **19** · 不可執行 **4**(`OFDB562`~`OFDB564` 的 OFDB 那三份另計) |

### 3.4 `App.config` 與 Remoting 的全面查證

`ofdb.md` 已經查證 `OFDB680` 的 `App.config` **沒有** `system.runtime.remoting`(0 個), 而 `OFDB600` / `OFDB609` **各有 2 個**且含 `<wellknown>`。本片把它擴大到三個專案的**全部 20 個 `App.config`**:

| `App.config` | `system.runtime.remoting` | `<wellknown>` | `<connectionStrings>` | 行數 |
|---|---|---|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | **2** | **1** | 無 | 349 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` | **2** | **1** | 無 | 349 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config` | **0** | 0 | **有(3 筆)** | 385 |
| `Dev/ATLAS.EC/Source/UI/UI.EC/App.config` | 0 | 0 | 無 | 419 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/App.config` | 0 | 0 | 無 | 3 |
| `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/app.config` | 0 | 0 | 無 | 13 |
| `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/app.config` | 0 | 0 | 無 | 11 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config` | 0 | 0 | 無 | 786 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config` | 0 | 0 | 無 | 63 |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/App.config`、`FormProxy/FormProxy.OFDB/App.config` | 0 | 0 | 無 | 各 3 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB{,1,2,3}/App.config`、`UIEntity.OFDB{,1,2,3}/App.config` | 0 | 0 | 無 | 各 12 |
| `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config` | 0 | 0 | 無 | 308 |

**統計:20 個 `App.config` 裡只有 2 個含 Remoting 區段,全在 `ATLAS.EC` 的 WindowsService 專案底下。** `ATLAS.OTAB` 底下只有一個 `App.config`(UI 層),`ATLAS.OFDB` 有 11 個但全是空殼。

**`OFDB680` 那支的矛盾要單獨講。**三支服務的程式碼都呼叫 `RemotingConfiguration.Configure(自己的 exe.config)` (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:42`), `architecture.md §8.4` 因此把三支一概歸為「Remoting 客戶端」。但 `OFDB680` 的 config 裡**沒有任何 `<wellknown>`**,而 `<wellknown>` 正是讓 `new OFDB680_Pxy()`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:65`) 變成遠端代理的那一行。沒有它,`new` 出來的就是一個**本機物件**, 於是 `FormProxy → Control → PO` 全部跑在服務自己的行程裡 —— 這也正好解釋為什麼只有它的 config 需要 `<connectionStrings>`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config:246-262`, `Logging` / `SWProduct` / `TA` 三筆,**含明文帳密,本文只記位置不抄值**)。

> **結論(把 `architecture.md §8.4` 講細一層)**:三支 `OFDB*` 服務**不是同一種部署**。 `OFDB600` / `OFDB609` 是真的 Remoting 客戶端,那台機器不需要資料庫權限; **`OFDB680` 是直連資料庫的行程**,跟 `architecture.md §8.4` 描述的 `RSPB008` 同型, 那台機器需要 `TA` / `SWProduct` / `Logging` 三個帳號的連線權限。部署或搬機器時這兩類要分開處理。〔假設〕**這是設定檔漏了 Remoting 區段,不是刻意設計** —— 依據:三支的 `OnStart` 程式碼幾乎逐字相同、都呼叫 `RemotingConfiguration.Configure`,若本來就要直連,那三行是多餘的。但 config 裡的 `<connectionStrings>` 又不像意外多出來的,所以兩種解釋都成立,**沒有註解可判**。

其餘 32 支沒有自己的 `App.config`,它們的 Remoting 邊界跟主程式一樣落在 UI → FormProxy 之間 (`architecture.md §8.1`),而主程式的 Remoting 設定**不在 repo**。

### 3.5 六層齊不齊

| 狀況 | 支數 | 代號 |
|---|---|---|
| 六層齊 | 28 | 見 §3.3 其餘 |
| **缺 DataEntity + UIEntity** | 4 | `OFDB603`(OTAB)、`OFDB615` `OFDB616` `OFDB671`~`OFDB673`(部分) |
| **掃描器說缺 PO,其實是命名不合鐵律** | 5 | `OFDB615` `OFDB616` `OFDB671` `OFDB672` `OFDB673` —— PO 在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/<代號>OracleDao.cs`,不叫 `<代號>_PO.cs` |
| **掃描器說缺 entity,其實是 `_9i` 後綴** | 6 | `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` `OFDB612` `OFDB615` `OFDB680` 的 xsd 實際叫 `<代號>_9iModel.xsd` / `<代號>_9iView.xsd` |

> **這正好驗證 `architecture.md §2.7` 的兩條假設。**那一節說: 「`OFD` 42 支裡至少 6 支(`OFDB671`–`OFDB673`、`OFDM672`、`OFDM674`、`OFDI641`)是 `*OracleDao` 命名問題, 這是**假設**」。本片實測 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs`、 `OFDB672OracleDao.cs`、`OFDB673OracleDao.cs` 三個檔都在,而且 Ctl 確實走 `base.DataAccessPool.Add(new OFDB671OracleDao())`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB671_Ctl.cs:30`)。 **`OFDB671`~`OFDB673` 那三支的假設可以升級成已證實**,而且 `OFDB615` / `OFDB616` 也是同一型 (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB615_Ctl.cs:25`、 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB616_Ctl.cs:27`), 那一節原本把這兩支歸在「真缺」,應該改歸命名問題。

### 3.6 報表 R

**本片無 R 畫面。**但有兩支會產出檔案給人看:`OFDB616` 匯出「寄送名單核對檔(EXCEL 格式)」 (`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB616.Designer.cs:272`)、`OFDB565` 產出傳檔媒體。兩者都是 UI 層自己寫檔,不走 `.Report` 那一套(`architecture.md §6.5`)。

## 4. 維護畫面(M)

**本片無 M 畫面** —— 35 支代號第四碼全是 `B`,UI 全部繼承 `xOneStepProcessForm`, 沒有四眼工具列,也沒有任何一支呼叫 `EVA()`。

唯一要注意的例外是 `OFDB671`:它雖然是 B,卻直接往 `OFD678A` 寫入**四眼欄位** (`Status`、`CreateID`/`CreateDate`、`UpdateID`/`UpdateDate`、`EntryID`/`EntryDate`、 `VerifyID`/`VerifyDate`、`RejectID`/`RejectDate`、`ApproveID`/`ApproveDate`), 而且 `Status` 寫死 `'301'`、四組人員欄全部塞同一個 `CreateID`、`RejectDate` 寫死 `DATE'1900-01-01'` (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:54-82`)。 **也就是這張表看起來走過四眼,其實是批次一次填滿的。** 查 `OFD678A` 的核准軌跡會被誤導,詳見 §6.7。

## 5. 查詢畫面(I)

**本片無 I 畫面**(代號第四碼全是 `B`)。

不過 §3.2 提到的 12 支「查詢 + 執行」型批次裡,有幾條**會把資料濾掉而不提示**的條件,列在這裡:

| 畫面 | 濾掉什麼 | 結果類型 | 錨點 |
|---|---|---|---|
| `OFDB562`(OTAB) | 只撈 `OFD562.SEAL_PROCESS = '01'`;`'02'` 的看不到 | 過濾(無提示) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:122` |
| `OFDB605` | 只撈 `OFD615A.CTL_DATE = 當日`;沒跑 `OFDB600` 就整個空 | **阻擋**(有訊息) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:50-54`、`:65` |
| `OFDB600` | `GetBefExecRowCount` 只數 `*_PCODE = '0'` 的,已處理的不計 | 過濾(無提示) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:367` |
| `OFDB673` | `Select` **完全沒有 WHERE**,整張 `OFDB672` 都撈出來 | 不濾(反向問題) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:66-75` |
| `OFDB612` | 只更新 `IsCheck = 1` 的列,沒勾的靜靜跳過 | 過濾(無提示) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs:180` |
| `OFDB561` | 只處理 `IsCheck=true` 的列 | 過濾(無提示) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB561_PO.cs:202` |
| `OFDB680`(服務端) | 只送 `EXE_TYPE='1'`、`BF_SRNO='-1'`,兩個值**寫死在服務程式裡** | 過濾(無提示) | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:76`、`:80` |

## 6. 批次(B)與 WindowsService

```text
[圖] OFDB600 的排程、執行主體、兩處失敗處理缺陷，以及它與 OFDB605 的下游相依
圖中文字:① 服務端:每分鐘比對一次時刻字串 / Timer 60 秒 / sTIMES 等於 HHmm 才跑 / GetTIMES / 五段 UNION 取最近時刻 / OFD606A 四個截止時間欄 / EC_xxx_YN 等於 Y 才算 / OFD600A / MEMBER_CHG_LIMIT_TIME / ② 雷:PadLeft 回傳值沒接 + 空 catch，時刻不足四碼就整個消失 / PadLeft 沒接回傳值 / 字串不可變 等於沒做 / Substring 丟例外 / 例 930 取成 93 時 / catch 大括號是空的 / 沒有 log 沒有訊息 / 那個時刻當天不跑 / 沒人會發現 / ③ 執行主體:一支 SP，七張表的處理碼 0 變 1 / BeginTransaction / CommandTimeout 設 0 / S_EC_IPJB600_EXCUTE / 名字裡是 IPJB 不是 OFDB / LoadDataSet 收 refcursor / OFDB600_EMAIL / 七張交易表 / 處理碼 0 推到 1 / ④ 雷:信在 commit 之前寄 / SendMail 逐列寄信 / 申購 買回 轉申購 三段 / tran.Commit / 在寄信之後才做 / commit 失敗 / 信已寄出 資料回滾 / Ctl 的三種通知信 / Gen36 Gen39 Gen46 已被註解 / ⑤ 雷:執行前筆數那段 SQL 是兩個 SELECT 黏在一起 / region old sql 不是註解 / 38 行仍然是活的 / 新版再接在後面 / 兩個完整 SELECT 相連 / Oracle 一定拒絕 / 落到 catch 訊息是空字串 / BefExec 沒有呼叫端 / 所以沒人發現 / ⑥ 出口與下游 / OFDB601 602 604 / 產生正式交易單 / OFDB605 拋轉 / 查不到 OFD615A 就阻擋 / 帳務 / 本片之外
```

*圖:圖 4 OFDB600 的執行流程與失敗處理。橘框=主要步驟或下游入口;橘虛框=缺陷鏈;灰虛框=本片以外或沒人跑的;黑框=版控外。第②與第⑤兩條鏈都是「壞了但沒人知道」的形狀。*

### 6.0 先看總表

35 支的「出口」(執行完到底改變了什麼)分五類,每支都有:

| 出口 | 畫面 | 幾支 |
|---|---|---|
| **呼叫 SP,DB 狀態被改**(C# 端看不到改了什麼) | `OFDB540` `OFDB553` `OFDB580` `OFDB600` `OFDB600A` `OFDB601` `OFDB601A` `OFDB602` `OFDB602A` `OFDB603` `OFDB604` `OFDB604A` `OFDB605` `OFDB607` `OFDB608` `OFDB609` `OFDB673` `OFDB680` | 18 |
| **C# 自己組 SQL 寫表** | `OFDB560`(`FND003` / `MON001`)`OFDB561`(`OFD562`)`OFDB562`~`OFDB564`(`OFD562` + `OFD562_TSCDLOG`)`OFDB570`(`OFD570A`)`OFDB612`(`OFD621A`)`OFDB615` / `OFDB616`(`OFD607` / `OFD607A` / `LOG602`)`OFDB671`(`OFD678A`)`OFDB672`(`OFDB672`) | 12 |
| **產生 / 讀取外部檔案** | `OFDB560`(讀 CSV)`OFDB565`(產傳檔媒體)`OFDB566`(讀收檔媒體)`OFDB570`(讀寫檔)`OFDB616`(產 Excel)`OFDB610`(產標籤,未編譯) | 6 |
| **寄信** | `OFDB600`(`ServerMailUtility.SendMailTo`)`OFDB609`(`LDAPAPIHelper.SendMail` + `GenXMLHelper.Gen38` / `Gen41`)`OFDB680`(`Gen33` / `Gen90`)`OFDB615`(`Gen30` / `Gen34`)`OFDB690`(`Gen34`,未編譯)`OFDB606`(`Gen30` / `Gen31`,未編譯)`OFDB611`(`Gen22`,未編譯) | 7 |
| **呼叫外部系統 API** | `OFDB609`(`LDAPAPIHelper`,無原始碼) | 1 |

(有些支同時有多個出口,所以相加大於 35。)

### 6.1 `OFDB600` 網路交易時限截止處理作業 —— 本片頭號重點

程式碼裡唯一一處中文名稱在 Ctl 的 XML 註解:「網路交易時限截止處理作業(手動/自動)」 (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:137`)。這是全片唯一自報中文名的一支。

#### 6.1.1 六層與呼叫路徑

| 層 | 檔 |
|---|---|
| UI | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB600.cs`(88 行,`xOneStepProcessForm`) |
| FormProxy | `Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/OFDB600_Pxy.cs` |
| Control | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs`(前 135 行是整段註解掉的舊版) |
| PO(現行) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs` |
| PO(死碼) | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB600_PO.cs`(313 行,**100% 被註解**) |
| entity | `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd` / `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/OFDB600_9iView.xsd`(`_9i` 後綴) |
| **服務** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs` |

`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:153` 只掛一個 DAO:`new OFDB600OracleDao()`。 **`MSSQL\OFDB600_PO.cs` 沒有任何呼叫端**,而且整支註解,查邏輯不要看它。

#### 6.1.2 觸發方式:手動一種、自動一種,自動那種的時刻在資料庫

手動:UI 的執行鈕。自動:`OFDB600_Service`。

服務的排程機制是本片最值得記住的東西:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 建構子掛一個 `Interval = 60000`(60 秒)的 `System.Timers.Timer` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:27-30` |
| 2 | `OnStart` 讀自己的 `exe.config` 設定 Remoting,然後 `GetTIMES()` | `:45-56` |
| 3 | `GetTIMES()` 透過 Pxy 撈 `OFDB600_TIMES`,把所有候選時刻換算成今天的 `DateTime`、各自加 `LIMIT_TIME_BUFFER` 分鐘,已過的推到明天,取**最近的一個**存進 `sTIMES`(`"HHmm"` 字串) | `:109-155` |
| 4 | 每分鐘 `_timer_Elapsed` 比對 `sTIMES == DateTime.Now.ToString("HHmm")`,相等就跑 | `:65-75` |
| 5 | 跑完 `finally` 再 `GetTIMES()` 算下一次 | `:103-106` |

候選時刻的 SQL 是五段 UNION(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292`): `OFD606A` 的申購 / 匯款 / 贖回 / 定額四個截止時間欄(各自被對應的 `*_YN = 'Y'` 過濾) 再 UNION `OFD600A.MEMBER_CHG_LIMIT_TIME`。

> ⚠ **要改排程不用重編也不用碰 Windows 排程器,改 `OFD606A` / `OFD600A` 的欄位就好。** 反過來說,**排錯時間查不到「誰設的」** —— 這幾個欄位由哪支 M 畫面維護,本片查不到。

> ⚠ **服務啟不啟動不看設定檔,看執行帳號。**`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28` 是 `if (Environment.UserName == "SYSTEM")` 才 `ServiceBase.Run`,否則進 `Console.ReadLine()` 偵錯模式。用**非 LocalSystem 的服務帳號**(例如網域帳號)安裝這支服務,它會走 else 分支、在 `Console.ReadLine()` 卡住不動,而且**不會有任何錯誤訊息**。`architecture.md §8.5` 已標過這顆雷,本片再中一次。

#### 6.1.3 參數:兩個,沒有位置取參數

| 參數 | 來源 | 錨點 |
|---|---|---|
| `CHECK_DATE` | 手動時是畫面「資料處理日期」;自動時是 `ExeCDt.AddMinutes(-LIMIT_TIME_BUFFER)` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:85` |
| `CreateID` | 手動時是登入者;自動時寫死 `"AutoJob"` | `:86` |

`Main()` 沒有 `string[] args`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13`), repo 內也沒有 `.bat`。**缺陷型錄的「位置取參數」在本片不成立。**

#### 6.1.4 執行主體:一支 SP,加一輪寄信

```
tran = db.BeginTransaction()
cmd = GetStoredProcCommand("S_EC_IPJB600_EXCUTE")   ← Dao:44、:48
CommandTimeout = 0                                   ← :51(無逾時保護)
AddInParameter wCHECKDATE / wCreateID                ← :60、:68
AddOutParameter oCUR (RefCursor)                     ← :71
LoadDataSet → OFDB600_EMAIL                          ← :73
if (OFDB600_EMAIL.Count > 0) SendMail(resultVDB)     ← :75-76   ★ 在 commit 之前
tran.Commit()                                        ← :84
```

`SendMail` 依 `TRADE_TYPE` 分三段(`'1'` 申購 / `'2'` 買回 / `'3'` 轉申購), 每段對每一列呼叫一次 `ServerMailUtility.SendMailTo("員工及員工關係人交易【審核結果】通知信", ...)` (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:172`、`:211`、`:249`)。

**SP 動了哪些表?** repo 內查不到腳本,但同支的前後筆數 SQL 攤開了七張表(這是唯一可靠的反推):

| 表 | 日期欄 | 處理碼欄 | 業務(推測) |
|---|---|---|---|
| `OFD620A` | `ALLOT_DATE` | `EC_ALLOT_PCODE` | 網路申購 |
| `OFD651A` | `REDEM_DATE` | `EC_REDEM_PCODE` | 網路買回 |
| `OFD655A` | `RCV_DATE` | `EC_RSP_PCODE` | 定額申購 |
| `OFD661A` | `CHG_DATE` | `EC_RSP_CHG_PCODE` | 定額異動 |
| `OFD657A` | `RCV_DATE` | `EC_RSP_TRN_CODE` | 定額轉申購 |
| `OFD658A` | `RCV_DATE` | `EC_RSP_TRN_CHG_CODE` | 定額轉申購異動 |
| `OFD601CHG` | `CHG_EFFECT_DATE` | `EC_CHG_PCODE` | 受益人變更 |

錨點:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:361-398`(執行前)與 `:428-492`(執行後)。 **`'0'` → `'1'` 就是這支 SP 做的事**,這是從「執行前數 `'0'`、執行後數 `'1'`」反推的,標假設但依據很硬。

後五張表的 `WHERE` 有一段值得記住的寫法:

```
WHERE RCV_DATE = CASE WHEN SUBSTR(TO_CHAR(SYSDATE,'HH24MISS'),1,2) < '02'
                      THEN :CHECK_DATE-1 ELSE :CHECK_DATE END
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:376`。註解寫「2012.06.22 modify by wenju 修改定額/定額異動/受益人異動因執行時間在隔一天而導致未抓出筆數問題」(`:14`)。意思是:**跨午夜零點到兩點之間執行,日期要往回推一天。**

> ⚠ 這個 `'02'` 是字串比較,而且只改了後五張,`OFD620A` / `OFD651A` 兩張**沒改** (`:366`、`:371` 仍然是直接 `= :CHECK_DATE`)。凌晨一點跑這支,申購與買回的筆數會是 0, 定額那五張才會對 —— **成對邏輯只改一半**的典型。

#### 6.1.5 執行前筆數那段 SQL 是壞的(本片最會咬人的一顆)

`GetBefExecRowCount` 組 SQL 時,把**舊版**與**新版**兩段完整的 `SELECT ... FROM (...) A` **接在同一個字串上**:

- 舊版:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:321-358`, 外面包的是 `#region old sql` / `#endregion old sql`(`:320`、`:359`)

- 新版:`:361-398`

`#region` **不是註解**,那 38 行是活的。所以最後送進 Oracle 的是 `SELECT ... ) A SELECT ... ) A` —— 兩個 SELECT 直接黏在一起,**任何 Oracle 都會拒絕**。

對照組是同一個檔的 `GetAftExecRowCount`:那邊的舊版是用 `//` **逐行註解掉**的 (`:443-466`),所以執行後筆數是對的。

**效果**:`BefExec()` 永遠拿不到資料 → catch → `AddResultRow(false, 0, string.Empty)` (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:410`)→ **空訊息**。而且 `OFDB600_Service` 裡 `BefExec()` 這個方法**根本沒有任何呼叫端** (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:164`, `_timer_Elapsed` 只叫 `DoExecute()` 與 `AftExec()`,`:72-73`)—— **壞掉的程式碼剛好沒人跑,所以沒人發現。**手動畫面若有按鈕呼叫 `GetBefExecRowCount`,就會踩到。

#### 6.1.6 其他缺陷

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `catch (SqlException sqlex)` 掛在 Oracle 連線上 | 永遠不會進去,**死碼**;真正的 Oracle 例外落到下面那個 `catch (Exception)`,訊息被換成 `string.Empty` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:89-95`、`:100` | 中 |
| 2 | `tran.Rollback()` 沒有 null 檢查 | `BeginTransaction` 自己失敗時,catch 裡再噴一個 `NullReferenceException`,**把原始例外蓋掉** | `:91`、`:98` | 中 |
| 3 | **信在 commit 之前寄** | SP 成功但 commit 失敗 → 信已經寄出去、資料卻回滾。`SendMailTo` 也沒有任何回傳值檢查 | `:75-76` 與 `:84` | **高** |
| 4 | `CommandTimeout = 0` 且註解寫「此程式讓它永久跑」 | 卡住的 SP 不會超時,只會一直佔連線 | `:51` | 中 |
| 5 | Ctl 裡整段寄信邏輯被註解 | `GenXMLHelper.Gen36` / `Gen39` / `Gen46` 三種通知信**已經不再寄**,但方法還在、`OFD681` / `OFD681_EMP` / `OFD681_Err` 三張 DataTable 還在填 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:172-196` 與 `:282-289` | **高** |
| 6 | `sEXEC_TIMES.PadLeft(4, '0');` **回傳值沒接** | 字串是不可變的,這行等於沒做。時刻欄若存成 `"930"`,`Substring(0,2)` 會取到 `"93"` → `Convert.ToDateTime` 丟例外 → 被 `:149` 的**空 catch** 吞掉 → 那個時刻整個消失,批次當天不跑 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:130`、`:149-151` | **高** |
| 7 | `AddInParameter(cmd, ":CHECK_DATE", ...)` 多一個冒號 | 同檔另一處寫 `"CHECK_DATE"`(`:404`),兩種寫法並存;能不能跑取決於 provider 的容錯 | `:498` | 低 |
| 8 | `MaskName` 用 `val.Replace(舊, 星號)` | 姓名裡重複出現的字會被**多遮**;單字姓名會讓 `Substring(1, 0)` 得到空字串,`Replace("", "*")` 直接丟 `ArgumentException` | `:510-526` | 中 |
| 9 | `WriteLog` 先整檔讀進記憶體再整檔覆寫 | 檔案愈寫愈大、複雜度 O(n²);寫到一半當掉整天的 log 就沒了 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:239-252` | 低 |
| 10 | log 路徑寫死 `"C://Vendor//WindowService//OFDB600//"`、編碼 `Encoding.Default` | 換機器 / 換語系會出事〔客戶特定〕 | `:220`、`:241`、`:247` | 低 |

### 6.2 `600` 系列的 `A` 後綴:逐對比對的結果

`ofd7.md` 查證過 OFD 的 `A` 後綴在**畫面**上多半是境內(`FUND_TYPE='2'`)/ 境外(`'1'`), 值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID`。 **批次上完全不成立。**四對逐行比對(忽略空行與縮排,`difflib.SequenceMatcher`):

| 對 | 無 `A` 那支 | 有 `A` 那支 | 相似度 | SP |
|---|---|---|---|---|
| 600 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs`(483 行) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB600A_PO.cs`(149 行) | **11.4%** | `S_EC_IPJB600_EXCUTE` vs `S_OTA_OFDB600A_EXE` |
| 601 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs`(340 行) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs`(655 行) | **15.3%** | `S_EC_IPJB601_EXCUTE` vs `S_OTA_OFDB601A_EXE` |
| 602 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs`(488 行) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs`(477 行) | **19.5%** | `S_EC_IPJB602A_EXCUTE` vs `S_OTA_OFDB602A_EXE` |
| 604 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs`(341 行) | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB604A_PO.cs`(780 行) | **13.2%** | `S_EC_IPJB604_EXCUTE` vs `S_OTA_OFDB604A_EXE_ADD` / `_MOD` |

11%~20% 就是「兩個 C# 檔都有 `using`、`try` / `catch` / `finally`、`AddInParameter`」的底噪。 **它們不是同一支程式的兩個值域分支,是兩個專案各寫各的。**

**真正成對的是另一組。**`A` 後綴的那四支彼此之間才像:

| 對 | 相似度 |
|---|---|
| `OFDB602A_PO` ↔ `OFDB603_PO` | **72.2%** |
| `OFDB601A_PO` ↔ `OFDB602A_PO` | 53.5% |
| `OFDB601A_PO` ↔ `OFDB603_PO` | 52.9% |
| `OFDB602A_Ctl` ↔ `OFDB603_Ctl` | **93.8%** |
| `OFDB601A_Ctl` ↔ `OFDB602A_Ctl` | 82.5% |
| `OFDB603_Ctl` ↔ `OFDB604A_Ctl` | 82.5% |

也就是說 **`OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 是同一個樣板複製四次**, 差別只在「申購 / 贖回 / 轉換 / 定期定額」四種交易別:

| 畫面 | 交易別 | 日期參數 | 前置檢查看哪張表 | `Check_*` 個數 |
|---|---|---|---|---|
| `OFDB601A` | 申購 | `ALLOT_NAV_DATE` | `OFD620` / `OFD621` / `OFD611` | **8** |
| `OFDB602A` | 贖回 | `REDEM_DATE` | `OFD651` / `OFD652` / `OFD612` | **5** |
| `OFDB603` | 轉換 | `REDEM_NAV_DATE` | `OFD651` / `OFD653` / `OFD613` | **5** |
| `OFDB604A` | 定期定額 | `CTL_DATE` | `OFD551` `OFD552` `OFD554` `OFD555` `OFD614` `OFD663`~`OFD667` | **9** |

錨點:`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:34-57`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:35-49`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB603_PO.cs:35-49`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB604A_PO.cs:37-61`。

> ⚠ **複製貼上留下的痕跡:`OFDB602A` 與 `OFDB603` 裡都有一個變數叫 `CheckOFD561Transfer`, 但它接的是 `Check_OFD651_Transfer` 的回傳值** —— `651` 打成 `561`,兩支都錯, 因為是同一份複製出去的(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:154`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB603_PO.cs:153`)。無功能影響,但這是「改一邊沒改另一邊」的反面證據 —— 改**兩邊都改了**,連錯字一起改。

> ⚠ **`OFDB603` 是唯一沒有 `A` 後綴卻屬於這個樣板家族的一支**,而且它**沒有 entity 層** (`atlas_scan --screen OFDB603` 印 `DataEntity —(缺)` / `UIEntity —(缺)`)。也就是說「有沒有 `A`」在 OTAB 這一組裡連命名一致性都談不上。

#### 6.2.1 這四支共用的卡控樣板

樣板長這樣(以 `OFDB601A` 為例,`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:129-192`):

| # | 檢查 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 1 | 上一營業日還有申購資料沒轉入 | 回「上一營業日尚有申購資料未轉入!」 | **阻擋** | `:135-142` |
| 2 | `OFD611` 還沒做截止轉處理中 | 回「請至截止轉處理中狀態作業後,再進行拋轉!」 | **阻擋** | `:145-152` |
| 3 | 該 NAV 日期還有資料沒做截止轉處理中 | 回「該NAV日期，尚有申購資料未做截止轉處理中作業!」 | **阻擋** | `:155-161` |
| 4 | 該 NAV 日期資料已轉入 | 回「該NAV日期，申購資料已轉入,不可重複轉入!」 | **阻擋**(這條就是重跑保護) | `:164-170` |
| 5 | (刪除功能)EC 申購資料尚未拋轉 | 回「該基金EC申購資料尚未拋轉，不可回覆!」 | **阻擋** | `:200-206` |
| 6 | (刪除功能)已執行個人帳戶下單確認 | 回「該基金已執行個人帳戶申購下單確認，不可回覆!」 | **阻擋** | `:209-215` |
| 7 | (刪除功能)已執行綜合帳戶下單確認 | 回「該基金已執行綜合帳戶申購下單確認，不可回覆!」 | **阻擋** | `:218-224` |
| 8 | (刪除功能)已執行集保下單確認 | 回「該基金已執行集保下單確認，不可回覆!」 | **阻擋** | `:227-233` |

**這是本片卡控最完整的一組,也是唯一有明確重跑保護的一組。**

**但這八個檢查全部 fail-open。**每個 `Check_*` 的骨架都是:

```
bool boolvalue = true;
try   { ... 查到資料就 boolvalue = false; }
catch (Exception ex) { CommonExceptionBlocker.HandleBusinessException(ex); }
return boolvalue;          // ← 例外時回 true = 「檢查通過」
```

`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:284`、`:313-319`。 **資料庫連不上 / 表被改名 / 權限不足 → 八個檢查全部「通過」→ SP 照跑。** `OFDB602A` / `OFDB603` / `OFDB604A` 的每一個 `Check_*` 都是同一份骨架 (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:247`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:292`、 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:332`),所以是 **27 個 fail-open 檢查**。

> 另一個共通問題:八個檢查裡任何一個不過,程式是 `return modelVDB` **直接從 try 裡跳出去** (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:141`), 這時 `tran` 已經 `BeginTransaction` 但**既沒 Commit 也沒 Rollback**, 只靠 `finally` 的 `dbProduct.Dispose(tran)`(`:266-270`)收尾。缺陷型錄的「交易只 Commit 不 Rollback」在這裡是「連 Rollback 都沒寫,靠 Dispose」。

### 6.3 `OFDB605` 拋轉 / 拋轉回復 —— 本片唯一有跨批次硬相依的一支

#### 6.3.1 與 `OFDB600` 的關係:明確的阻擋

`Query` 一進來第一件事就是 `ValidateCtlData(CTL_DATE)`, 不過就回 **「尚未執行交易截止時間，請先執行OFDB600程式」** (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:50-54`)。

`ValidateCtlData` 做的事是:`SELECT OFD615A.CTL_DATE FROM OFD615A WHERE CTL_DATE = TO_DATE(...) AND ROWNUM = 1`, 查不到就 `return false`(`:192-203`)。也就是 **`OFD615A` 當日有沒有列,等於「`OFDB600` 今天跑過沒有」。** 這條相依在 repo 內沒有任何文件,只有這一行訊息字串。

> ⚠ **`ValidateCtlData` 也是 fail-open**:`catch` 只呼叫 `HandleBusinessException`, 然後走到函式最後一行 `return true`(`:206-210`)。 **查不到表 / 連線壞掉 = 「`OFDB600` 跑過了」= 放行。**

#### 6.3.2 三段卡控

| 時點 | 檢查 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | `OFD615A` 當日無資料 | 「尚未執行交易截止時間，請先執行OFDB600程式」 | **阻擋** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:50-54` |
| 執行前(只在 `BMS_CTL_CODE = '2'` 拋轉回復時) | `OFD601CHG` 有 `CHG_DATE > CTL_DATE` 且 `EC_CHG_PCODE = '2'` 的列 | 「尚有大於此資料處理日期的拋轉資料，請先回覆後再執行拋轉回復。」 | **阻擋** | `:121-129`、`:218-257` |
| (另一支方法)`CheckBMS_CTL_CODE_1` | `OFD615` 有 `BMS_CTL_CODE = '1'` 的列 | 「尚有未拋轉資料，不可執行」 | **阻擋**(語意反向,見下) | `:291-318` |

> ⚠ **`CheckBMS_CTL_CODE_1` 的回傳語意是反的**:擋下來時它 `AddResultRow(**true**, 1, "尚有未拋轉資料，不可執行")` (`:318`),放行時才 `AddResultRow(false, 0, "")`(`:323`)。而且它吃的是 `OFDB605ModelVDB`(舊 entity),不是現行的 `OFDB605_9iModelVDB` (`:276`、`:279`)—— **很可能是沒清乾淨的舊方法**。標假設,依據是全 EC 專案的 `OFDB605_Ctl` 並沒有呼叫這個方法名。

#### 6.3.3 SQL 字串串接:本片最大的一處

`OFDB605` 有三處把值直接串進 SQL,不走參數:

| 處 | 串了什麼 | 錨點 |
|---|---|---|
| `Query` 的 `F_EC_GETOFD615AREMARK('" + Row_BMS_CTL_CODE.Value + "', ...)` | 畫面上的拋轉控制碼 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:62` |
| `Query` 的 `CTL_DATE = TO_DATE('" + Row.Value + "','yyyy/mm/dd')` | 畫面上的資料處理日期 | `:65` |
| `ValidateCtlData` 的 `TO_DATE('" + strCTL_DATE + @"','yyyy/mm/dd')` | 同上 | `:194` |
| `CheckBMS_CTL_CODE_1` 的 `MAX(" + Row.Name + ")` 與 `< '" + Row.Value + "'` | **欄位名**與值都串 | `:301` |

值來自 `xOneStepProcessForm` 的日期控件與選項鈕,正常操作不會塞奇怪字元, 但 `FormProxy` 是 Remoting 端點,參數是可以被構造的 —— `architecture.md §4.3` 講的「參數化只做了一半」在這裡完整重現。

#### 6.3.4 `ExecuteNonQuery` 的回傳值被常數蓋掉

```
int i = 0;                       // :97
...
db.ExecuteNonQuery(cmd, tran);   // :158   ← 回傳值丟掉
i = 1;                           // :159   ← 直接指定 1
tran.Commit();                   // :161
AddResultRow(true, i, "");       // :162   ← 永遠回「成功，1 筆」
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:97`、`:158-162`。 **SP 一筆都沒動也會回「執行成功」。**這是缺陷型錄裡「`ExecuteNonQuery` 回傳值被常數蓋掉」的教科書版本。

### 6.4 `OFDB560` / `OFDB570`:兩支檔案匯入,重跑安全性剛好相反

兩支都是「UI 讀檔 → 塞進 DataTable → PO 寫表」,但寫法差很多。

| 項目 | `OFDB560` | `OFDB570` |
|---|---|---|
| 讀檔 | `StreamReader(path, Encoding.Default)`,逗號切欄 | 同型 |
| 目標表 | `FND003`(基金基本資料)或 `MON001`(每月資料) | `OFD570A`(12 個泛用 `FIELD_*` 欄) |
| 先刪再寫 | **只有 `MON001` 分支有**(`DELETE MON001 WHERE YYMM=:YYMM`) | **有**(`DELETE OFD570A WHERE Data_ID=:Data_ID`) |
| 重跑 | `MON001` 安全 / **`FND003` 會一直長** | 安全 |
| 交易 | 一段 | **兩段**,第一段寫完就 commit,第二段才跑 SP |

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:114`(`MON001` 的 DELETE)、 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:64`(`OFD570A` 的 DELETE)、 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:95-108`(兩段交易)。

`FND003` 那一段更麻煩 —— 它的流水號是自己算的:

```
INSERT INTO fnd003 (CO_ID, FUND_ID, SEQ, ...)
SELECT :CO_ID, :FUND_ID, NVL(MAX(TO_NUMBER(seq,'99999')),1)+1, ... FROM fnd003 WHERE co_id=:CO_ID
```

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:61-79`。三個問題: (a) 同一批次的迴圈裡每一列都重跑一次 `MAX+1`,但都在同一個未 commit 的交易內 —— 能不能看到前一列要看隔離等級;(b) `NVL(MAX(...), 1) + 1` 表示**空表時第一筆的 `SEQ` 是 2 不是 1**; (c) 重跑整個檔會再長一批。

**兩支共同的問題:兩段檢核都被註解掉了。**

```
/*if (dbTA.ExecuteNonQuery(Cmd, tran) <= 0)
{
    tran.Rollback();
    mModel.Utility.Result.AddResultRow(false, 0, "執行失敗");
    return model;
}*/
dbTA.ExecuteNonQuery(Cmd, tran);
```

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:101-107` 與 `:143-149`。外殼還在、註解裡的邏輯很清楚,**但現在一律不檢查,寫 0 筆也算成功**。

**還有一條會直接 NRE 的路徑。**`OFDB560_PO.Execute` 的 `tran` 只在兩個 `if` 分支裡被 `BeginTransaction`(`:81`、`:112`),而 `tran.Commit()` 在分支外面(`:152`)。如果 `FILE_TYPE != "1"` 而且 `MON001.Count == 0`(空檔案),兩個分支都不進, `tran` 還是 null → `tran.Commit()` 直接 `NullReferenceException` → 掉進 `catch` → **`tran.Rollback()` 再 NRE 一次**(`:157`)。使用者看到的是框架的一般錯誤,不是「檔案是空的」。

UI 那邊也有同型的坑:

| 缺陷 | 影響 | 錨點 |
|---|---|---|
| `if (SRD.ReadLine() == string.Empty) return;` —— **`return` 前沒設 `e.Cancel = true`** | 第一行是空的就直接回,批次照跑,接著踩上面那條 NRE | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs:57` |
| `if (strData.Length == 0 \|\| strData[0] == "") break;` | 檔案中間有一列空的,**後面所有資料列被吞掉**,而且沒有任何提示 | `:61` |
| `Encoding.Default` | 依機器語系而定,換語系會亂碼 | `:55` |
| `FN_CLASS_TYPE` 寫死 `'2'`、`COL_TYPE` 寫死 `'D'`、`TRAN_TYPE` 寫死 `'C'`、`TRN_CODE` 寫死 `'00'` | 業務規則埋在 SQL 字串裡〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:69`、`:71`、`:76`、`:122` |
| `OFD570A` 的 `BF_NO` 寫死 `0` | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:72` |

### 6.5 `OFDB560`–`OFDB566` 這組連號:**不是同一個業務**

這七支(`560` `561` `562` `563` `564` `565` `566`)代號連號,但查下來分成三件事:

| 支 | 專案 | 管什麼 | 跟誰同組 |
|---|---|---|---|
| `OFDB560` | OFDB | 投信公司基金每月資料 / 基金基本資料 **CSV 匯入** | **誰都不像**;跟 `OFDB570` 同型(檔案匯入) |
| `OFDB561` | **OTAB** | 集保上傳**確認 / 回復** | `562`~`564` |
| `OFDB562` | OTAB + OFDB | 扣款授權書:**已送集保確認** | `561` `563` `564` |
| `OFDB563` | OTAB + OFDB | 扣款授權書:**退件處理**(取消申請 / 重新送核) | 同上 |
| `OFDB564` | OTAB + OFDB | 扣款授權書:**註銷處理** | 同上 |
| `OFDB565` | OFDB | **傳檔**媒體產生(扣款授權書核印建檔傳檔 / 客戶資料傳檔) | `566` |
| `OFDB566` | OFDB | **收檔**媒體匯入(扣款授權書核印資料收檔) | `565` |

證據:

- `561`~`564` 四支都吃 `OFD562` 這張表,而且 `562` / `563` / `564` 的執行功能字串分別是「已送集保確認(S.送核)」、「退件處理(C.取消申請/R.重新送核)」、「註銷處理(E.註銷)」 (`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB562.designer.cs:131`、 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB563.designer.cs:283`、 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB564.designer.cs:323`)。 **括號裡的 `S` / `C` / `R` / `E` 就是狀態機。**

- `565` / `566` 的 UI 群組框分別叫「傳送檔案List」與「接收檔案List」 (`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB565.designer.cs:94`、 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB566.designer.cs:155`), 而且兩支的核取方塊名字一樣(`uchkTTP10A` / `uchkTTP101`),一送一收。

- `560` 跟其他六支**沒有任何一張共用表**,只是代號剛好落在中間。

**所以「連號 = 同一業務」在這裡是錯的,而且錯得很典型。** `561`~`564` 是一組四步的狀態機,`565` / `566` 是一組傳收對,`560` 自己一支。

#### 6.5.1 `562`~`564` 三支的兩份程式

`architecture.md §2.6` 列這三支為「真分岔,兩份都在編」。§2.5 已經說明: `Dev/ATLAS.OFDB/` 那三份是 SQL Server 時代的原版,而且因為 `MultiRowEVAPO.dbTA` 恆為 null, `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:28` 的 `dbTA.CreateConnection()` **一執行就 NRE**。

`Dev/ATLAS.OFDB/` 那份還有一條 SQL 字串串接:

```
strSQL += " AND OFD562.BF_NO " + model.Utility.Parameters.FindByName("BF_NO").Opeartor + " @BF_NO ";
```

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:75` —— **把比較運算子本身串進 SQL**。值是參數化的,運算子不是。因為那份跑不起來,影響是零,但要是有人把它救活就會變成活的洞。

#### 6.5.2 `562`~`564` 的狀態流(以 OTAB 那份為準)

| 畫面 | 撈什麼 | 寫什麼 | 錨點 |
|---|---|---|---|
| `OFDB562` | `OFD562.SEAL_PROCESS = '01'` | `UPDATE OFD562` + `INSERT INTO OFD562_TSCDLOG` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:122` |
| `OFDB563` | `OFD562` 加 `OFD564` | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB563_PO.cs`(舊版)/ `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB563_PO.cs` |
| `OFDB564` | `OFD562` 加 `COD006A` | 同上,另外改 Hi-Trust 開戶主檔的扣款狀態(由 SP 或外部,C# 端只有畫面提示) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB564.designer.cs:153-164` |

`OFDB562`(OTAB)裡有四個判斷方法名字幾乎一樣: `IsOFD562_TSCDLOG_UPLOADING_COMFIRMED` / `IsOFD562_TSCDLOG_EXIST_COMFIRMED` / `IsOFD562_TSCDLOG_UPLOADING_CANCEL` / `IsOFD562_TSCDLOG_EXIST_CANCEL` (`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:36-45`)。 `COMFIRMED` 是 `CONFIRMED` 的拼錯,四個方法一起錯,同樣是複製貼上的痕跡。

### 6.6 `OFDB671` / `OFDB672` / `OFDB673`:員工交易的三支,兩兩相依

#### 6.6.1 `OFDB671` 審核人員設定 —— 整表洗掉再重寫

```
tran     = dbTA.BeginTransaction()        ← :38
tranPTPF = dbPTPF.BeginTransaction()      ← :39     ★ 兩個連線兩個交易
DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN      ← :43-49
foreach (grid 每一列) INSERT INTO OFD678A ...      ← :85-
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:38-49`、`:85`。

`INV_DEP_YN` 的值來自這一行:

```
dbTA.AddInParameter(cmdExecute, "INV_DEP_YN", OracleDbType.Varchar2,
                    strFunctionID == "OFDB671_A" ? "Y" : "N");
```

`:48`。`strFunctionID` 是 `PermissionInfo[0].FunctionID`(`:36`)。 **寫死的 `"OFDB671_A"` 這個字串決定要洗掉哪一半的設定檔。** FunctionID 若因選單設定改變而不再等於 `"OFDB671_A"`,這支會去洗 `'N'` 那一半 —— 畫面上看不出任何差別,直到有人發現審核人員不見了。

> ⚠ **grid 空的時候會把那一半整個清空。**`DELETE` 是無條件先執行的,`foreach` 沒有資料就不 INSERT, 最後照樣 `Commit`。沒有「至少要有一列」的檢核。

四眼欄位全是假的(§4 已提):`Status` 寫死 `'301'`、`Entry` / `Verify` / `Approve` 三組人員時間全部塞同一個 `CreateID` / `CreateDate`、`RejectID` 寫死一個空白、`RejectDate` 寫死 `DATE'1900-01-01'` (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:70-82`)。

#### 6.6.2 `OFDB672` 申請 → `OFDB673` 審核

`OFDB672`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs`):

| # | 步驟 | 錨點 |
|---|---|---|
| 1 | `select createid from OFDB672 where agent_code_o=:agent_code_o and emp_no_o=:emp_no_o` | `:27-31` |
| 2 | `if (userid != "")` → **阻擋**「同銷售機構及員編變更已在OFDB673審核中，不可重覆執行」 | `:33-37` |
| 3 | `insert into OFDB672 values(:dataid, :agent_code_o, :emp_no_o, :agent_code, :emp_no, :createid, sysdate)` | `:43-52` |

> ⚠ **第 3 步是位置式 INSERT,沒有欄位清單。**`OFDB672` 這張表只要加一個欄位或調換順序, 這支就會插錯欄或直接報錯。`:43-52`。 ⚠ **第 2 步的檢查可以被 NULL 繞過。**`ExecuteScalar` 查不到列時回 null, `Convert.ToString(null)` 是 `""`,判斷正確;但**查得到列而 `createid` 本身是 NULL** 時也是 `""`,於是重複的申請會被放行。這是 Oracle 三值邏輯在 C# 端的變體。 ⚠ `OFDB672` 的 `select` 沒有排除「已審核完成」的舊資料 —— 如果 `S_TA_OFDB673_EXE` 審完不刪列, 那同一組 `agent_code_o` + `emp_no_o` 就**永遠不能再申請第二次**。SP 不在 repo,無法確認,**標假設**。

`OFDB673`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs`):

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `wAPPROVE` 傳的是 `FindByName("Approve") != null ? 1 : 0` —— **判斷參數存不存在,不是判斷值** | 目前剛好能動(UI 只在按「是」時才加這個參數),但任何人日後改成「一律加、用值區分」就會變成全部核准 | `:36` 與 `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89-92` | **高** |
| 對話框寫「是否同意變更？」,按**「否」也會照樣執行**(只是 `wAPPROVE=0` 走退件路徑),沒有 `e.Cancel = true` | 使用者以為按「否」是取消,實際是退件 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89-93` | **高** |
| `row = ugrdOFDB672.ActiveRow` 沒有 null 檢查 | 沒選任何列就按執行 → `NullReferenceException` | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:83-85` | 中 |
| `Select` 的 SQL **完全沒有 WHERE** | 整張 `OFDB672` 全撈,資料多了會很慢;也看得到別人的申請 | `:66-75` | 中 |
| `catch` 直接把 `ex.Message` 回給畫面 | 內部錯誤訊息外洩到 UI | `:45`、`:86`、`:115` | 低 |
| `USERID` 參數塞的是 grid 裡那一列的 `CREATEID`(申請人),不是審核者 | SP 記錄到的「使用者」是申請人 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:88` | 中 |

### 6.7 `OFDB615` / `OFDB616`:密碼處理的一對,55.8% 相同

兩支的 PO 行級相似度 **55.8%**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs` 614 行 vs `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs` 554 行), 是同一段「更新 `OFD607A` → 同步 `OFD607` → 補寫有效期限 → 寫 `LOG602`」邏輯的兩個版本: `OFDB615` 單筆處理(畫面上是一位受益人),`OFDB616` 逐列跑 (`foreach (OFDB616_9iModel.OFDB616Row row in vdb.DataEntity.OFDB616.Rows)`, `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:205`)。

#### 6.7.1 寫入順序

| 步 | 做什麼 | `OFDB615` | `OFDB616` |
|---|---|---|---|
| 1 | `UPDATE OFD607A` 設密碼、狀態、提示、寄發日、錯誤次數歸零 | `:171`、`:209`、`:239` | `:226`、`:261`、`:285` |
| 2 | `UPDATE OFD607` 同步 | `:292` | `:318` |
| 3 | `UPDATE OFD607A SET EC_PSW_TRAN_DATE = sysdate+2, ES_PSW_TRAN_DATE = sysdate+2` —— 註解說「因UPDATE會變成9999/12/31，強制再重新更新有效期限一次」 | `:322-326` | `:343` |
| 4 | `INSERT INTO LOG602`,最多跑兩輪(`for (int j = 0; j < 2; j++)`) | `:335-404` | `:356` |

第 3 步值得記住:**有一個地方會把密碼有效期限設成 `9999/12/31`,程式不知道是誰做的,只好事後再蓋一次。** 註解沒說是哪裡,repo 內也找不到(很可能在 trigger 或 SP 裡)。`sysdate+2` 的 `2` 天是寫死的〔客戶特定〕。

#### 6.7.2 兩支共有的三個嚴重缺陷

**(1) `ExecuteNonQuery` 的回傳值被常數蓋掉,所以結果一律成功。**

```
int i = db.ExecuteNonQuery(cmd, con_tran);   // :285
i = 1;                                        // :286   ← 蓋掉
...
if (i == 1) { con_tran.Commit();  AddResultRow(true,  0, ""); }   // :405-409
else        { con_tran.Rollback(); AddResultRow(false, 0, ""); }  // :410-414
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:285-286` 與 `:405-414`。 **`else` 分支永遠到不了**,`UPDATE` 影響 0 列也會 Commit 並回成功。 `OFDB616` 是同一件事的另一種寫法:`int i = 0;`(`:202`)在迴圈裡被 `i = 1;`(`:309`)無條件設定。

**(2) 例外時訊息寫到錯的物件。**

```
T result = xVirtualDataBase.CreateNewVDB(modelVDB);   // :127 建了一個新的
...
catch (Exception ex)
{
    vdb.Utility.Result.AddResultRow(false, 0, string.Empty);   // :420 寫進「輸入」那個
    ...
}
return result;                                                 // :429 回傳「新的」那個
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:127`、`:420`、`:429`; `OFDB616` 同型(`:184`、`:435`、`:444`)。 **呼叫端拿到的 `Result` 是空的**,而 `OFDB615_Ctl` / `OFDB616_Ctl` 與服務端都用 `Result.Rows.Count > 0 && Result[0].ReturnCode == false` 判斷成敗 —— Rows.Count 是 0,第一個條件就不成立,於是**例外被當成「沒有失敗」**。

**(3) `OFDB616` 的 `BeginTransaction()` 在 `try` 外面。** `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:187`。開交易本身失敗(連線滿了 / DB 掛了)時,例外直接穿過 PO 打到 FormProxy, 使用者看到的是框架的一般錯誤而不是業務訊息。`OFDB608` 有同樣寫法 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB608OracleDao.cs:50`)。

#### 6.7.3 寫死的常數

| 常數 | 意思 | 錨點 |
|---|---|---|
| `strNewES_Psw = "N/A"` | 「密碼改由LDAP處理 故填N/A」 —— 密碼欄不再存真值 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:169-170` |
| `LOG602.EC_SYSTEM_TYPE = '3'` | 註解「2022.03.17 EC_SYSTEM_TYPE由'1'改為'3' 境內外合併 by Becky」 | `:348-349` |
| `LOG602.SYSTEM_ID = '1'` | 註解「因只剩補發網路密碼, 故固定寫入'1' 網路交易 2022.08.24 by Becky」,原本從參數來的那行被註解掉 | `:384-386` |
| `LOG602.CHG_TYPE = '4'`、`Status = '301'` | 直接寫在 SQL 字串裡 | `:350`、`:351` |
| `RejectID = ' '`、`RejectDate = to_date('1900/01/01',...)` | 同 §4 講的假四眼 | `:355` |
| `sysdate+2` | 密碼有效兩天 | `:324-325` |

> `LOG602` 的 `Status = '301'` 與四眼欄全填同一人,跟 `OFDB671` 寫 `OFD678A` 是完全一樣的手法。 **本片有兩張表(`OFD678A`、`LOG602`)的四眼欄是批次一次填滿的,查核准軌跡時會被誤導。**

> ⚠ **SQL 裡的參數用 `@` 前綴,但這是 Oracle 連線。** 例:`SET ES_PSW=@ES_PSW, ...`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:172`), 而 `AddInParameter` 傳的名字沒有前綴(`:328`)。同專案其他支(例 `OFDB612`)用的是 Oracle 的 `:` 前綴 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs:170`)。〔假設〕**框架的 `Database` 包裝層有做前綴轉換,所以現在跑得起來** —— 依據是這兩支還在 csproj 裡、也還在 DAO 池裡註冊(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB615_Ctl.cs:25`), 不太可能整支跑不動都沒人反映。但**沒有原始碼可證**(`Vendor.Product.DataAccess` 無原始碼,從呼叫端反推), 所以標假設。要確認就在站台跑一次 `OFDB616` 的執行鈕。

### 6.8 `OFDB612` 扣款手續費:本片寫得最乾淨的一支

```
tran = db.BeginTransaction();                                   // :167
strSQL = @" UPDATE OFD621A SET SUB_STATUS = :SUB_STATUS
                              ,NONSUCS_CODE = :NONSUCS_CODE
                              ,SEAL_RTN_TYPE = 'M'
                              ,UPDATEID = :UPDATEID
                              ,UPDATEDATE = SYSDATE
             WHERE EC_ALLOT_NO = :EC_ALLOT_NO
               AND EC_ALLOT_SRNO = :EC_ALLOT_SRNO ";            // :169-176
foreach (勾選的列) i += db.ExecuteNonQuery(cmd, tran);          // :180-191
if (i > 0) { tran.Commit();  AddResultRow(true,  i, ""); }      // :194-198
else       { tran.Rollback(); AddResultRow(false, 0, ""); }     // :199-203
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs:167-203`。

**這是本片唯一一支把 `ExecuteNonQuery` 的回傳值真的累加起來、並且拿它決定 Commit 或 Rollback 的批次。** 拿它當對照組讀 §6.3.4 與 §6.7.2 會很清楚差在哪。

剩下兩個小問題:`SEAL_RTN_TYPE = 'M'` 寫死在 SQL 裡(`:172`); 失敗時 `AddResultRow(false, 0, "")` 訊息是空字串(`:202`、`:209`),使用者看不到原因。

### 6.9 已在 `ofdb.md` 出現過的五支:只寫補充

這五支 `ofdb.md` 已有記載,以下只補 `ofdb.md` **沒寫**的部分。

#### 6.9.1 `OFDB600`

已見 `ofdb.md §0.2`(列為 `architecture.md §8.4` 的四支 WindowsService 之一、明確說「一支都不在本片」) 與 `ofdb.md 附錄 E`(App.config 有 2 個 remoting 區段)。**本片補充**:

- 它的中文名、五段 UNION 的排程 SQL、`LIMIT_TIME_BUFFER` 的雙重用途 —— §6.1.2

- SP `S_EC_IPJB600_EXCUTE` 實際動到的七張表(反推)與那個 `< '02'` 的跨午夜補丁只改了五張 —— §6.1.4

- `GetBefExecRowCount` 的 `#region old sql` 不是註解,兩段 SQL 黏在一起,永遠跑不起來 —— §6.1.5

- Ctl 裡三種通知信(`Gen36` / `Gen39` / `Gen46`)整段被註解、但 `OFD681` 三張 DataTable 還在填 —— §6.1.6 第 5 條

- `PadLeft` 回傳值沒接 + 空 catch,時刻字串不足四碼會讓當天整個不跑 —— §6.1.6 第 6 條

- **它與 `OFDB605` 的硬相依**(沒跑 `OFDB600` 就不能跑 `OFDB605`)—— §6.3.1。這條 `ofdb.md` 沒有, 因為 `OFDB605` 不在它的範圍。

#### 6.9.2 `OFDB605`

已見 `ofdb.md §8.4`(只在「本片寫入、別的模組讀取的表」那張表裡被列為 `ATLAS.EC` 的一支)。**本片補充**:

- 它就是「拋轉 / 拋轉回復」,吃 `OFD615A.BMS_CTL_CODE`,`'1'` 未拋轉 / `'2'` 已拋轉 —— §6.3

- 三段卡控與其中兩段 fail-open —— §6.3.1、§6.3.2

- 四處 SQL 字串串接(含把**欄位名**串進去)—— §6.3.3

- `i = 1` 蓋掉 `ExecuteNonQuery` —— §6.3.4

- `CheckBMS_CTL_CODE_1` 的回傳語意是反的,而且吃舊 entity,疑似殘留 —— §6.3.2

#### 6.9.3 `OFDB606`

`ofdb.md §2.1` 提過 `OFDB606` 這個**名字**,但那是 `OFDB003` 的 SP 回傳的一張 DataTable 名 (`s_TA_OFDB003_Excute` 的 `T_OFDB606` OUT refcursor,`ofdb.md §6.1.5`),而且 `ofdb.md §6.1.7` 已經查證「`T_OFDB606`(→ `OFDB606` 表)目前無人消費」。**本片補充的是同名的那支畫面**:

- `OFDB606` 是網路開戶資料處理畫面(欄位有「交易密碼寄發日期」「登入密碼寄發日期」「開戶進度」「註冊類別」與一整組通訊資料,`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB606.Designer.cs:303-358`、`:658-767`)

- **它整組不在 csproj,沒有被編譯** —— §0.2 第二件事

- 它的 Ctl 還在呼叫 `GenXMLHelper.Gen30` / `Gen31`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB606_Ctl.cs`), 而那個 Ctl 也沒被編譯

- 它與 `OFDB607` 是同一個畫面的兩個世代:兩者的 Designer 標籤幾乎一字不差 (`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB606.Designer.cs:303-358` 對 `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB607.Designer.cs:320-375`,連順序都一樣), 差別只在 `OFDB606` 的 e-mail 欄叫「E-mail1」/「E-mail2」而 `OFDB607` 叫「e-mail」。 **〔假設〕`OFDB607` 是 `OFDB606` 的接班人**,依據是這組逐欄對應 + 只有 `OFDB607` 有 `*OracleDao` 與 SP。

> 所以 `ofdb.md` 講的「`T_OFDB606` 無人消費」現在有了更完整的解釋: **連對應的畫面本身都沒在編譯。**兩件事合起來才是完整的圖。

#### 6.9.4 `OFDB609`

已見 `ofdb.md §6.1.6` / `§8.3`(`OFDB003` 的 LDAP 補償批次、住 `Dev/ATLAS.EC/`、 `architecture.md §8.4` 的四支服務之一、App.config 有 2 個 remoting 區段)。**本片補充**:

- **它的服務排程時刻來自 `OFD600A.OPEN_ACC_PROCESS_TIME`,而且 `SYSTEM_ID='1' AND EC_SYSTEM_TYPE='1'` 是寫死的** (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:569-574`)。也就是「網路交易後續處理」與「開戶處理時間」共用同一個欄位。

- `ofdb.md §6.1.6` 引的那句作業指引(「更新失敗資料請於OFDB609…執行『更新LDAP資料』按鈕」) **在 `OFDB609` 自己的 Ctl 裡也有一份一模一樣的** (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:139`)。 **也就是 `OFDB609` 失敗時,信裡叫使用者去跑 `OFDB609`** —— 自我指涉的作業指引,複製貼上沒改。

- `ofdb.md §6.1` 標為「最容易咬人的一點」的那個行為(LDAP 失敗會 `Result.Clear()` 再塞失敗訊息, 把 DB 已 commit 的事實蓋掉)**在 `OFDB609` 完全重現** (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:141-142`)。兩支是同一份寫法。

- 它另外寄兩種信:`GenXMLHelper.Gen38`(三處呼叫,`:363`、`:373`、`:398`)與 `Gen41`(`:406`), 這兩種 `OFDB003` 沒有。

- 兩個**空 catch**:`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:427`、`:439`。

- 服務端的三行 Remoting 初始化在 `Start()` 與 `OnStart()` 各出現一次 (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:40-42` 與 `:54-56`)—— `architecture.md §8.4` 已標為「意圖不明,無註解可判」,本片確認 `OFDB600` / `OFDB680` 也一樣 (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50-52` 與 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:42-44` / `:138-140`)。 **三支全部如此,所以是樣板,不是個案。**

#### 6.9.5 `OFDB680`

已見 `ofdb.md §0.2` 與 `ofdb.md 附錄 E`(App.config **0 個** remoting 區段,與 `OFDB600` / `OFDB609` 對照)。**本片補充**:

- **它的 config 反過來有 `<connectionStrings>`(`Logging` / `SWProduct` / `TA` 三筆,含明文帳密,只記位置)** (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config:246-262`), 而 `OFDB600` / `OFDB609` 兩份沒有。 **推論:它是直連資料庫的行程,不是 Remoting 客戶端** —— 完整論證在 §3.4。

- 排程時刻來自 `SELECT ALERT_LIMIT_TIMES FROM OFD680A`,**沒有 WHERE**,取第一列 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:704`, 服務端 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:120` 取 `[0]`)。 `OFD680A` 若有第二列,第二列永遠不生效。

- 服務端把兩個參數**寫死在程式裡**:`EXE_TYPE = '1'`、`BF_SRNO = '-1'` (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:76`、`:80`), 而手動畫面那兩個值可以選 —— 註解就在旁邊 (`//if (this.custEC_BF_SRNO.Value != "") ...`,`:77-79`)。**自動跑與手動跑的行為不一樣。**

- `DATACHECK` 這個重跑鍵是服務端用字串拼出來的:`sFund + DateTime.Now.Date.ToString("yyyy/MM/dd") + "-1"` (`:83`),PO 端靠它 `DELETE OFDB680_XML WHERE DATACHECK = :DATACHECK` 再重寫 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:410-411`)。 **重跑安全,但前提是基金清單 `sFund` 完全一樣** —— 中途有基金上下架,`DATACHECK` 就變了,舊資料刪不掉。

- 兩個 `catch (SqlException)` 在 Oracle 連線上,死碼 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:285`、`:560`)。

- 出口是 `GenXMLHelper.Gen90(OFDB680_XML)` 與 `Gen33(OFD681, ...)` (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:73`、`:80`、`:84`)。

- log 寫到 `"C://Vendor//WindowService//OFDB680//"`,與 `OFDB600` 同一套「先整檔讀再整檔覆寫」 (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:175`、`:194-207`)。

### 6.10 四支未編譯的:`OFDB606` / `OFDB610` / `OFDB611` / `OFDB690`

§0.2 第二件事已經證明它們整組不在 csproj。這裡補各自的業務輪廓(從 Designer 標籤與 SQL 反推), 因為**它們的畫面代號還可能出現在選單與交接文件裡**,被問到要答得出來。

| 代號 | 業務(推測) | 依據 | SP |
|---|---|---|---|
| `OFDB606` | 網路開戶資料處理(密碼寄發日、開戶進度、註冊類別、通訊資料) | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB606.Designer.cs:303-358` | 無(自組 `OFD607A` 的 SQL) |
| `OFDB610` | 開戶表格 / 自黏標籤列印名單,可只列「請客服郵寄開戶表格」者 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB610.Designer.cs:229-467` | `s_OFDB610_Get`、`s_ECFunGetAccountData` |
| `OFDB611` | 依申購日期與付款方式處理申購資料 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB611.Designer.cs:110-144` | `s_OFDB611_Excute` |
| `OFDB690` | 取消員工交易(依「取消員工交易日期」) | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB690.Designer.cs:91` | `s_OFDB690_Get` |

**要救活它們得做三件事,缺一不可**:

1. 把 UI / Designer / Pxy / Ctl / Interface / OracleDao 六個檔加回五個 csproj;

2. **把 Ctl 從 `new <代號>_PO()` 改成 DAO 池寫法** —— 因為 `MSSQL\<代號>_PO.cs` 整支被註解, 那個類別不存在(§0.2 第三件事);

3. `OFDB611_Ctl` 還要把半新半舊的兩種寫法統一(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB611_Ctl.cs:37` 舊 / `:59` 新)。

`OFDB610` 另外還有一個獨立問題:它的 `Oracle\OFDB610OracleDao.cs` 與 `MSSQL\OFDB610_PO.cs` 呼叫的 SP 名字**完全一樣**(`s_OFDB610_Get` / `s_ECFunGetAccountData`),沒有改成 `S_EC_*` 命名 —— 其他移轉完成的支都改了(`S_EC_IPJB600_EXCUTE` / `S_EC_OFDB607_Excute` …)。 **〔假設〕這表示 `OFDB610` 的 Oracle 版只改了語法沒改 SP,移轉沒走完。**依據是命名慣例的落差。

### 6.11 其餘各支速寫

| 畫面 | 做什麼 | 值得記住的一點 | 錨點 |
|---|---|---|---|
| `OFDB540` | 依專案代碼 / 基金 / 截止日產生名單,並用 `f_TA_GetAgent()` 這個 TVF 帶出銷售機構;畫面上另有「產生名單」選項 | 用 `VOTE_UNIT11`~`VOTE_UNIT15` 五欄相加算單位數,**所以這是投票 / 股東會性質的名單**(推測) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:137`、`:144` |
| `OFDB553` | 契約異動轉入,日期是「契約收件日之下一個公司營業日」 | **本片唯一讓 SP 回訊息決定 rollback 的一支**:`strMsgX.Value` 非空就 `tran.Rollback()` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB553_PO.cs:126-128` |
| `OFDB561` | 集保上傳確認 / 回復 | 查詢結果每列有一個 `IsCheck` 欄,執行時只處理 `Select("IsCheck=true")` 的;沒勾的**靜靜跳過** | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB561_PO.cs:202` |
| `OFDB565` | 產生傳檔媒體(扣款授權書核印建檔 / 客戶資料 / 客戶指定外幣帳戶 / 客戶扣款帳戶四種) | **開兩個交易**(`TA` 與 `PTPF`),而且兩個各自 `Commit` / `Rollback`;中間任一段失敗只回滾自己那一邊 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB565_PO.cs:50`、`:54`、`:223-231` |
| `OFDB566` | 收檔媒體匯入 | **全片唯一不開交易的一支**,寫入完全交給 `ImportFileEngine`(無原始碼);而且格式檢查的旗標邏輯是反的,見附錄 E | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB566_PO.cs:60-81` |
| `OFDB570` | 依「日期批號」匯入 12 個泛用 `FIELD_*` 欄,再呼叫 `S_TA_OFDB570_GET` 產出下載檔 | **兩段交易**:第一段 DELETE+INSERT 完就 `Commit`,第二段才跑 SP。SP 失敗時前半段已經落地 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:95-108` |
| `OFDB580` | 結帳交易 / 月庫存資料初始化,依 `EXEC_ITEM` 二選一 | 畫面自己把產出物列出來:`tbl_ALLOT_CLOSE` / `tbl_REDEM_CLOSE` / `tbl_BALANCE_MONTHLY` / `tbl_BALANCE_ACCU` / `tbl_SA_LOG`。**這五張表只出現在畫面標籤,程式與 xsd 都查不到** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB580.designer.cs:298`、`:311`、`:323` |
| `OFDB600A` | 境外平台:依「資料處理日期」跑 `S_OTA_OFDB600A_EXE` | 149 行,是 OTAB 這組裡最薄的一支,**完全沒有前置檢查**,跟 `OFDB601A` 的八個檢查形成強烈對比 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB600A_PO.cs:94-148` |
| `OFDB601` / `OFDB602` / `OFDB604` | 網路申購 / 贖回 / 定額的產生與拋轉 | 三支都是「畫面選日期 + 付款方式 + 交易途徑 → 呼叫一支 SP」,C# 端幾乎沒有業務邏輯。`OFDB602` 的畫面有「凍結戶筆數」欄,是本片唯一提到凍結戶的地方 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB602.Designer.cs:184` |
| `OFDB607` | 網路開戶資料處理(`OFDB606` 的接班人) | 它的 `Execute` 裡有一整段 `if/else` 的 Commit / Rollback **被註解掉**,只剩上面那一組還活著 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB607OracleDao.cs:266-283` |
| `OFDB608` | 依受益人戶號 / ID 處理單筆網路資料 | 只有 106 行,**「0 筆就 rollback 並回『無可執行之資料』」那段被整段註解**,現在一律 Commit 並回成功 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB608OracleDao.cs:69-85` |

### 6.12 順序相依總表

| 條 | 順序 | 卡在哪 | 擋不擋 |
|---|---|---|---|
| 電子交易 | `OFDB600` → `OFDB601` / `OFDB602` / `OFDB604` → `OFDB605` | `OFD615A` 當日有無資料 | **阻擋**,但檢查 fail-open(§6.3.1) |
| 受益人 LDAP | `OFDB003`(`ofdb.md §6.1`)→ `OFDB609` 補推 | 無欄位,靠失敗通知信 | 不強制 |
| 員工換號 | `OFDB672` 申請 → `OFDB673` 審核 | `OFDB672` 表有無同 key | **阻擋** |
| 境外申購 | `OFDB601A` 產生 → 下單確認 → 回覆才能刪 | 四段確認旗標 | **阻擋**,全部 fail-open |
| 集保授權書 | `OFDB562` 送核 → `OFDB563` 退件 / `OFDB564` 註銷 → `OFDB561` 上傳確認 | `OFD562.SEAL_PROCESS` | 過濾(無提示) |
| 傳收檔 | `OFDB565` 傳 → (外部)→ `OFDB566` 收 | 檔名與媒體編號 | 不強制 |
| 密碼 | `OFDB615` / `OFDB616` 補發 → LDAP | `OFD607A.ES_PSW_STATUS` | 不強制 |

## 7. 報表(R)

**本片無 R 畫面。**35 支代號第四碼全是 `B`,`Dev/ATLAS.EC.Report/` 與 `Dev/ATLAS.OTA.Report/` 底下沒有對應的 `OFDB6*` / `OFDB5*` 報表。

要注意的是本片有兩支會產出「給人看的檔案」,但走的不是 `.Report` 那一套(`architecture.md §6.5`):

| 畫面 | 產什麼 | 誰產的 | 錨點 |
|---|---|---|---|
| `OFDB616` | 寄送名單核對檔(Excel) | UI 層自己寫檔 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB616.Designer.cs:246-279`、`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB616.cs` |
| `OFDB565` | 四種傳檔媒體 | `ExportFileEngine`(無原始碼,從呼叫端反推) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB565_PO.cs:88`、`:133`、`:184` |
| `OFDB610` | 自黏標籤 / 開戶表格(**未編譯**) | UI 層 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB610.Designer.cs:326-385` |

## 8. 跨模組共用

```text
[圖] 本片與 ofdb.md 共用的 LDAP 線、對外讀寫的表、對 architecture.md 的三處修正，以及相鄰值得一起追的東西
圖中文字:① 本片與 ofdb.md 那片共用同一條 LDAP 線 / BMS 開單與四眼 / bms.md / OFDB003 生效 / ofdb.md 6.1 / LDAPAPIHelper / 無原始碼 兩支共用 / OFDB609 補推 / 本片 6.9.4 / 失敗信叫人去跑 OFDB609 / 文案沒改 自我指涉 / ② 本片寫入、別的模組讀取 / OFD607A OFD607 / EC 前台登入驗證 / LOG602 / ofdb.md 那片的 SP 也寫它 / OFD621A / 扣款與手續費結算 / OFD562 OFD562_TSCDLOG / 集保介接 / ③ 本片讀取、別的模組維護 —— 改欄位要回頭看本片十幾支 / BMS001A / BMS / OFD081A OFD081V / OFD 的 M 片 / CTL014 / 代碼值域 SourceType 107 / COD009 OFD068 / 員工 銷售機構 / RSP006A / rsp.md / ④ 與 architecture.md 的三處修正 / MultiRowEVAPO 也是 null 連線 / architecture 3.1.1 只點名 BasicEVAPO / OFDB562 564 兩份不是分岔 / 是新舊世代 舊那份跑不起來 / OFDB680 不是 Remoting 客戶端 / architecture 8.4 要分兩類 / ⑤ 相鄰但不在本片、值得一起追的 / OFDM681 691 692 693 / 跟本片四支一起退出 csproj / IPJB 那八支 OracleDao / 也全部不在 csproj / OFDB691 OFDB693 / 同專案同命名 不在名單 / OFDB731 871 901 / 有宣告主檔的反例
```

*圖:圖 5 跨模組影響面。橘框=本片的對外接點;橘虛框=要留意或本片對既有文件的修正;灰虛框=本片以外的畫面 / 模組;黑框=無原始碼。第④列是本篇對 architecture.md 最直接的三處補強。*

### 8.1 本片對外最重要的一條線:`OFDB600` → `OFDB605` → 帳務

`OFDB600` 把七張 EC 交易表的 `*_PCODE` 從 `'0'` 推到 `'1'`, `OFDB601` / `OFDB602` / `OFDB604` 把它們變成正式交易單, `OFDB605` 再依 `OFD615A.BMS_CTL_CODE` 把整批拋轉給帳務。 **這條線的三段全部由版控外的 SP 完成,C# 端只做前置檢核與參數傳遞。**

實務上的意義:**要追「網路下的一筆單為什麼沒進帳務」,在 .NET 程式裡查不到答案**, 只能沿 `*_PCODE` / `BMS_CTL_CODE` 的值往下走,再去 Oracle 端看 SP。本片能提供的是那些欄位叫什麼、值域是什麼(§2.7),以及哪一支批次負責推哪一段。

### 8.2 `OFDB609` 與 `ofdb.md` 的 `OFDB003` 是同一條線的兩半

`ofdb.md §8.3` 已經標出 `OFDB003` → `OFDB609` 的跨專案補償相依。本片補一個方向相反的觀察:**`OFDB609` 自己的失敗通知信也叫使用者去跑 `OFDB609`** (`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:139`,與 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:176` 一字不差)。兩支共用 `LDAPAPIHelper`(無原始碼,從呼叫端反推),**改它的行為要兩個專案一起看**。

### 8.3 本片寫入、別的模組讀取的表

| 表 | 本片誰寫 | 誰讀(推測) |
|---|---|---|
| `OFD607` / `OFD607A` | `OFDB615` `OFDB616` `OFDB606`(未編譯)`OFDB607` | EC 前台登入驗證、`OFDB609` / `OFDB610` |
| `LOG602` | `OFDB615` `OFDB616` `OFDB609` | 稽核查詢;`ofdb.md §2.1` 也列 `OFDB003` 的 SP 會寫它 —— **兩片都寫同一張 log 表** |
| `OFD621A` | `OFDB612` | 扣款作業、手續費結算 |
| `OFD678A` | `OFDB671` | 員工交易審核流程(誰讀未查到) |
| `OFDB672` / `OFDB672_T1`~`_T3` | `OFDB672` 寫、`OFDB673` 讀後清 | 只有這兩支 |
| `OFD562` / `OFD562_TSCDLOG` | `OFDB561`~`OFDB564` | 集保介接;`OFD562_TSCDLOG` 是本片產生的軌跡表 |
| `FND003` / `MON001` | `OFDB560` | 投信公會申報 / 月報(推測) |
| `OFD570A` | `OFDB570` | `S_TA_OFDB570_GET` 產檔用 |
| `OFDB680_XML` | `OFDB680` | `GenXMLHelper.Gen90` 寄信用 |

### 8.4 本片讀取、別的模組維護的表

見 §2.6。最要注意的是 `BMS001A`(BMS)與 `OFD081A` / `OFD081V`(OFD 的 M 片)—— 這兩張改欄位,本片有十幾支要跟著看。

### 8.5 共用 helper 與黑箱

| 元件 | 用途 | 誰用 | 有沒有原始碼 |
|---|---|---|---|
| `ServerMailUtility` | 直接寄信 | `OFDB600` | **無**,從呼叫端反推 |
| `GenXMLHelper` | 產生信件 XML 再寄 | `OFDB609`(`Gen38` `Gen41`)`OFDB680`(`Gen33` `Gen90`)`OFDB615`(`Gen30` `Gen34`)`OFDB690`(`Gen34`)`OFDB606`(`Gen30` `Gen31`)`OFDB611`(`Gen22`)`OFDB600`(`Gen36` `Gen39` `Gen46`,**已註解**) | **無** |
| `LDAPAPIHelper` | 外部帳號系統 API + 失敗通知信 | `OFDB609`(與 `ofdb.md` 的 `OFDB003` 共用) | **無** |
| `ImportFileEngine` / `ExportFileEngine` | 設定驅動的檔案收送 | `OFDB565` `OFDB566` | **無** |
| `ServerOTABizUtility` | OTAB 的共用業務工具 | `OFDB601A` 家族 | **無**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:72` 只看得到 `new`) |
| `SerialNo` | 流水號產生器,吃 `PTPF` 連線 | `OFDB671`(`GetEC_EMP_TRAN_NO()`) | **無**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:40`、`:89`) |
| `CommonExceptionBlocker` | 例外政策鏈(`architecture.md §7.6`) | 全片每一支 | **無** |

### 8.6 改動影響面速查

| 你要改 | 要一起看 |
|---|---|
| `OFD600A` / `OFD606A` 的任何 `*_TIME` 欄 | **三支服務的排程會跟著變**(§0.2 第五件事) |
| `OFD607A` 的密碼相關欄 | `OFDB615` `OFDB616` `OFDB607`,以及未編譯的 `OFDB606` |
| `OFDB672` 這張表加欄位 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:43-52` 是**位置式 INSERT**,一定要改 |
| `OFD562` 加欄位 | `ATLAS.OTAB` 與 `ATLAS.OFDB` **兩份**都要看(即使後者跑不起來) |
| `LDAPAPIHelper` 的行為 | `OFDB609`(本片)+ `OFDB003`(`ofdb.md §6.1.6`),兩個專案 |
| `LOG602` 的欄位 | `OFDB615` `OFDB616` `OFDB609`(本片)+ `OFDB003` 的 SP(`ofdb.md §2.1`) |
| 把 `OFDB606` / `OFDB610` / `OFDB611` / `OFDB690` 加回建置 | 要先改 Ctl 的 DAO 取得方式,見 §6.10 |

## 附錄 A. 資料表總表

### A.1 本片會動到的實體表(依群分類)

| 群 | 表 | 誰寫 | 誰只讀 |
|---|---|---|---|
| **EC 交易** | `OFD620A` `OFD621A` `OFD651A` `OFD655A` `OFD657A` `OFD658A` `OFD661A` `OFD601CHG` | `OFDB600`(經 SP)`OFDB612`(`OFD621A`) | `OFDB600` 的前後筆數、`OFDB605` |
| **EC 控制** | `OFD600` `OFD600A` `OFD606` `OFD606A` `OFD615` `OFD615A` `OFD611A` | `OFDB605`(經 SP) | `OFDB600` `OFDB601` `OFDB604` |
| **EC 開戶 / 密碼** | `OFD601` `OFD607` `OFD607A` `LOG602` | `OFDB606`(未編譯)`OFDB607` `OFDB609` `OFDB615` `OFDB616` | `OFDB610`(未編譯) |
| **員工交易** | `OFD678A` `OFDB672` `OFDB672_T1` `OFDB672_T2` `OFDB672_T3` `OFD221A` `OFD251A` `RSP006A` | `OFDB671` `OFDB672` `OFDB673`(經 SP) | `OFDB673` |
| **基金警示** | `OFD680A` `OFD681A` `OFD682A` `OFD683A` `OFD684` `OFD684A` `OFD696A` `OFDB680` `OFDB680_3` `OFDB680_XML` | `OFDB680` | — |
| **集保授權書** | `OFD562` `OFD562_TSCDLOG` `OFD564` | `OFDB561`~`OFDB564` | — |
| **境外平台交換** | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615` `OFD663` `OFD664` `OFD666` `OFD667` `OFD551` `OFD552` `OFD554` `OFD555` `OFD620` `OFD621` `OFD651` `OFD652` `OFD653` `OFD220` `OFD221` | `OFDB601A` 家族(經 SP) | 同左的 `Check_*` |
| **檔案匯入 / 統計** | `FND003` `MON001` `OFD570A` `OFD541A` `tbl_ALLOT_CLOSE` `tbl_REDEM_CLOSE` `tbl_BALANCE_MONTHLY` `tbl_BALANCE_ACCU` `tbl_SA_LOG` | `OFDB560` `OFDB570` `OFDB540`(經 SP)`OFDB580`(經 SP) | — |
| **共用唯讀** | `BMS001` `BMS001A` `BMS001CHG` `BMS081` `BMS914` `OFD081` `OFD081A` `OFD081V` `OFD068` `CTL014` `COD006` `COD006A` `COD009` `FSK003` `AA_Customer` `OFD074` `OFD309` `OFD114A` `OFD0811A` `EVASTATUS_V` `V_FUND` `Z_OPACT` `SWMAILCLASS` `SWMAILTEMPLATE` | — | 全片 |

### A.2 只存在於 SQL 字串或畫面標籤裡的表(xsd 查不到)

| 表 | 出現在哪 | 怎麼發現的 |
|---|---|---|
| `tbl_ALLOT_CLOSE` `tbl_REDEM_CLOSE` `tbl_BALANCE_MONTHLY` `tbl_BALANCE_ACCU` `tbl_SA_LOG` | **只有畫面標籤**,程式與 xsd 完全沒有 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB580.designer.cs:298`、`:311`、`:323` |
| `AA_Customer` | `OFDB612` 的 SQL 字串 | `ofdb.md 附錄 A.3` 也列過同一張 |
| `OFDB672` `OFDB672_T1`~`_T3` | `OFDB672` / `OFDB673` 的 SQL 字串 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:67`、`:99`、`:103`、`:105` |
| `OFDB680` `OFDB680_3` `OFDB680_XML` | `OFDB680` 的 SQL 字串 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:410-411`、`:655-656` |
| `Z_OPACT` | `OFDB609` 的 SQL 字串 | 表名前綴 `Z_` 全庫僅此一處 |
| `V_FUND` `EVASTATUS_V` | `OFDB680` / `OFDB612` 的 SQL 字串;是 View 不是表 | — |
| `SWMAILCLASS` `SWMAILTEMPLATE` | `OFDB615` 的 SQL 字串 | 信件樣板,推測由框架維護 |

### A.3 `_9i` 後綴的 entity

本片有 8 支的 xsd 檔名帶 `_9i`(`architecture.md §2.7` 稱為「假警報一」): `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` `OFDB612` `OFDB615` `OFDB680`。例:`Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd`。 **用 `<代號>Model.xsd` 去找會找不到。**

## 附錄 B. SP / Function / Trigger / View

### B.1 本片呼叫的 SP:26 支,repo 內腳本 0 支

| SP | 誰呼叫 | 命名世代 |
|---|---|---|
| `S_EC_IPJB600_EXCUTE` | `OFDB600` | EC 新 |
| `S_EC_IPJB601_EXCUTE` | `OFDB601` | EC 新 |
| `S_EC_IPJB602A_EXCUTE` | `OFDB602` | EC 新 |
| `S_EC_IPJB604_EXCUTE` | `OFDB604` | EC 新 |
| `S_EC_IPJB605_EXCUTE` | `OFDB605` | EC 新 |
| `S_EC_OFDB607_Excute` | `OFDB607` | EC 新 |
| `S_EC_OFDB608_Excute` | `OFDB608` | EC 新 |
| `S_EC_OFDB609_Excute` | `OFDB609` | EC 新 |
| `S_EC_OFDB680_GET` | `OFDB680` | EC 新 |
| `s_OFDB610_Get`、`s_ECFunGetAccountData` | `OFDB610`(未編譯) | **舊,沒改名** |
| `s_OFDB611_Excute` | `OFDB611`(未編譯) | **舊,沒改名** |
| `s_OFDB690_Get` | `OFDB690`(未編譯) | **舊,沒改名** |
| `S_TA_OFDB540` | `OFDB540` | TA |
| `S_TA_OFDB570_GET` | `OFDB570` | TA |
| `S_TA_OFDB672_GET` | `OFDB672` | TA |
| `S_TA_OFDB673_EXE` | `OFDB673` | TA |
| `S_TRADE_INITIAL`、`S_MONTH_INITIAL` | `OFDB580` | **無模組前綴** |
| `S_OTA_OFDB553_EXE` | `OFDB553` | OTA |
| `S_OTA_OFDB600A_EXE` | `OFDB600A` | OTA |
| `S_OTA_OFDB601A_EXE` | `OFDB601A` | OTA |
| `S_OTA_OFDB602A_EXE` | `OFDB602A` | OTA |
| `S_OTA_OFDB603_EXE` | `OFDB603` | OTA |
| `S_OTA_OFDB604A_EXE_ADD`、`S_OTA_OFDB604A_EXE_MOD` | `OFDB604A` | OTA |

> **`S_EC_IPJB600_EXCUTE` 的名字裡是 `IPJB600` 不是 `OFDB600`。** `OFDB601` / `OFDB602` / `OFDB604` / `OFDB605` 也一樣(`IPJB601` / `IPJB602A` / `IPJB604` / `IPJB605`)。五支的 SP 名字用的是另一個模組碼。`architecture.md §2.6` 已記 `ATLAS.EC` 同時裝 `OFD` 與 `IPJ`, **所以這五支的 SP 很可能是 `IPJ` 那一半共用的**。〔假設〕,依據是命名 + 同專案共存;無腳本可證。實務影響:**去 Oracle 端找 `S_EC_OFDB600_*` 會找不到。**

### B.2 Function

| Fn | 誰呼叫 | 錨點 |
|---|---|---|
| `F_EC_GETOFD615AREMARK` | `OFDB605` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:62` |
| `f_TA_GetAgent()`(TVF,用 `table(...)` 包) | `OFDB540` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:144` |

### B.3 Trigger / View

repo 內查不到本片相關的 Trigger。View 只有兩個名字:`EVASTATUS_V`(`OFDB612`)、`V_FUND`(`OFDB680`), 兩者都只出現在 SQL 字串裡,定義不在版控。

> ⚠ **`OFDB615` 的註解間接證明有個看不見的 Trigger 或 SP 在動密碼有效期限:** 「因UPDATE會變成9999/12/31，強制再重新更新有效期限一次」 (`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:321`)。 **誰把它設成 9999/12/31,repo 內查不到。**標假設:很可能是 `OFD607A` 上的 Trigger。

## 附錄 C. 代碼對照

見 §2.7。這裡補三組本片特有的:

| 代碼 | 值 | 意義 | 來源 |
|---|---|---|---|
| `SEAL_PROCESS` 的操作碼 | `S` 送核 / `C` 取消申請 / `R` 重新送核 / `E` 註銷 | **只寫在畫面選項的文字裡**,程式裡是 `'01'` / `'02'` 這種另一套值 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB562.designer.cs:131`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB563.designer.cs:283`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB564.designer.cs:323` |
| `LOG602.CHG_TYPE` | `'4'` | 寫死,推測是「密碼補發」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:350` |
| `LOG602.EC_SYSTEM_TYPE` | `'1'` → `'3'` | 註解「2022.03.17 由'1'改為'3' 境內外合併」 | `:348-349` |
| `Status = '301'` | `'301'` | 四眼的「已核准」(`architecture.md §3.10` 的值域);本片是批次直接填 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:70`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:351` |
| `ReturnRowCount = 99` | 99 | 三支服務共用的「不是錯誤,不要寫 EventLog」哨兵;**寫入端在版控外** | §2.7 |

## 附錄 D. 掃描母體與逐支處置

**不跑 `--module OFD` 覆蓋率**(那會拿 550 支來比)。以下是本片 35 支的逐一處置:

| # | 代號 | 處置 | 觸發方式 | Remoting |
|---|---|---|---|---|
| 1 | `OFDB540` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 2 | `OFDB553` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 3 | `OFDB560` | **已寫**(§6.4、§6.5) | 手動 | 無自有 config |
| 4 | `OFDB561` | 表格帶過(§6.11、§6.12) | 手動 | 無自有 config |
| 5 | `OFDB562` | **已寫**(§2.5、§6.5) | 手動 | 無自有 config |
| 6 | `OFDB563` | **已寫**(§2.5、§6.5) | 手動 | 無自有 config |
| 7 | `OFDB564` | **已寫**(§2.5、§6.5) | 手動 | 無自有 config |
| 8 | `OFDB565` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 9 | `OFDB566` | 表格帶過(§6.11、附錄 E) | 手動 | 無自有 config |
| 10 | `OFDB570` | **已寫**(§6.4) | 手動 | 無自有 config |
| 11 | `OFDB580` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 12 | `OFDB600` | **已見 `ofdb.md §0.2`,本片補充**(§6.1、§6.9.1) | 手動+服務 | **有(2 區段 + wellknown)** |
| 13 | `OFDB600A` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 14 | `OFDB601` | 表格帶過(§6.11)+ `A` 對照(§6.2) | 手動 | 無自有 config |
| 15 | `OFDB601A` | **已寫**(§6.2、§6.2.1) | 手動 | 無自有 config |
| 16 | `OFDB602` | 表格帶過(§6.11)+ `A` 對照(§6.2) | 手動 | 無自有 config |
| 17 | `OFDB602A` | **已寫**(§6.2) | 手動 | 無自有 config |
| 18 | `OFDB603` | **已寫**(§6.2) | 手動 | 無自有 config |
| 19 | `OFDB604` | 表格帶過(§6.11)+ `A` 對照(§6.2) | 手動 | 無自有 config |
| 20 | `OFDB604A` | **已寫**(§6.2) | 手動 | 無自有 config |
| 21 | `OFDB605` | **已見 `ofdb.md §8.4`,本片補充**(§6.3、§6.9.2) | 手動 | 無自有 config |
| 22 | `OFDB606` | **已見 `ofdb.md §2.1` / `§6.1.7`(指的是同名 DataTable),本片補充畫面本身**(§6.9.3、§6.10) | **不可執行** | 無自有 config |
| 23 | `OFDB607` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 24 | `OFDB608` | 表格帶過(§6.11) | 手動 | 無自有 config |
| 25 | `OFDB609` | **已見 `ofdb.md §6.1.6` / `§8.3`,本片補充**(§6.9.4) | 手動+服務 | **有(2 區段 + wellknown)** |
| 26 | `OFDB610` | **已寫**(§6.10) | **不可執行** | 無自有 config |
| 27 | `OFDB611` | **已寫**(§6.10) | **不可執行** | 無自有 config |
| 28 | `OFDB612` | **已寫**(§6.8) | 手動 | 無自有 config |
| 29 | `OFDB615` | **已寫**(§6.7) | 手動 | 無自有 config |
| 30 | `OFDB616` | **已寫**(§6.7) | 手動 | 無自有 config |
| 31 | `OFDB671` | **已寫**(§6.6.1) | 手動 | 無自有 config |
| 32 | `OFDB672` | **已寫**(§6.6.2) | 手動 | 無自有 config |
| 33 | `OFDB673` | **已寫**(§6.6.2) | 手動 | 無自有 config |
| 34 | `OFDB680` | **已見 `ofdb.md §0.2` / 附錄 E,本片補充**(§6.9.5、§3.4) | 手動+服務 | **宣告要走,config 0 個區段** |
| 35 | `OFDB690` | **已寫**(§6.10) | **不可執行** | 無自有 config |

### D.1 本片沒有涵蓋、但相鄰的東西

| 東西 | 為什麼沒寫 |
|---|---|
| `OFDB691` / `OFDB693` | 同專案、同命名、六層齊全(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs`、`OFDB693OracleDao.cs`),但不在本片名單 |
| `OFDM600`~`OFDM699` 那一整組 | 是 M 不是 B;但 `OFDM681` / `OFDM691` / `OFDM692` / `OFDM693` 跟本片四支一起被移出 csproj,值得一起追 |
| `IPJB6*` 那一組 | 住同一個 `PO.EC`,`Oracle\` 底下八個 `IPJB*OracleDao.cs` **全部不在 csproj** —— 跟本片四支是同一型問題,規模更大 |
| `OFDB731` / `OFDB871` / `OFDB901` | 索引裡**有宣告主檔**的三支,可以拿來當「批次也可以宣告主檔」的反例對照 |
| `OFDB003` / `OFDB004` / `OFDB281` 等 18 支 | 在 `ofdb.md` |

### D.2 怎麼自己查

```
py -V:3.12 /docs/tools/atlas_scan.py --screen OFDB605
```

要注意三件事:

1. **`OFDB562` / `OFDB563` / `OFDB564` 掃出來的六層會混兩個專案** —— 掃描器只印一份,實際各有兩份(§2.5)。

2. **`OFDB615` / `OFDB616` / `OFDB671`~`OFDB673` 會印「PO —(缺)」**, 那是命名問題,PO 在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/<代號>OracleDao.cs`。

3. **`OFDB600` 那組會印 entity 路徑,但實際檔名有 `_9i`**(附錄 A.3)。

## 附錄 E. 讀本文時要注意的地方

31 條,依型分群。嚴重度:**高** = 會造成資料錯誤或功能靜默失效;中 = 特定條件才發作;低 = 維護性。

### E.1 整組沒被編譯

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | `OFDB606` / `OFDB610` / `OFDB611` / `OFDB690` 的六層檔案都在,但 UI / Pxy / Ctl / Interface / OracleDao **五個 csproj 全部沒有它們** | 這四支根本不存在於執行檔裡。選單若還指著它們,使用者會拿到「找不到型別」 | `Dev/ATLAS.EC/Source/UI/UI.EC/UI.EC.csproj`、`Dev/ATLAS.EC/Source/Control/Control.EC/Control.EC.csproj`、`Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/FormProxy.EC.csproj`、`Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj` | **高** |
| E1.2 | `MSSQL\` 底下 15 支 `OFDB6*_PO.cs` **每一行都被 `//` 註解**,卻全部留在 csproj | 4,614 行死碼;更糟的是 `OFDB606` / `OFDB610` / `OFDB611` / `OFDB690` 的 Ctl 還在 `new` 這些不存在的類別,所以它們**再也加不回建置** | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB600_PO.cs:1`、`Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj:165-177` | **高** |
| E1.3 | `Oracle\` 底下八個 `IPJB*OracleDao.cs` 也全部不在 csproj | 不在本片範圍,但同型、規模更大 | `Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj` | 中 |

### E.2 整支跑不起來的死碼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | `Dev/ATLAS.OFDB/` 的 `OFDB562` / `OFDB563` / `OFDB564` 三份 PO 繼承 `MultiRowEVAPO`,而 `MultiRowEVAPO.dbTA` 恆為 null | `dbTA.CreateConnection()` 一執行就 NRE。這三份還是 T-SQL 方言,在 Oracle 上本來也跑不了 | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:18`、`:169-174`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:28` | **高** |
| E2.2 | `OFDB600` 的 `GetBefExecRowCount` 把舊版與新版兩段完整 SQL 接在同一個字串上(`#region` 不是註解) | 送出去的是兩個 SELECT 黏在一起,Oracle 必定拒絕。剛好沒有呼叫端所以沒人發現 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:320-398` | **高** |
| E2.3 | `OFDB600_Service.BefExec()` 定義了但沒有任何呼叫端 | 「批次執行前筆數」這條 log 永遠不會寫 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:164`(定義)、`:72-73`(只叫 `DoExecute` 與 `AftExec`) | 中 |
| E2.4 | `OFDB605.CheckBMS_CTL_CODE_1` 吃的是舊 entity `OFDB605ModelVDB`,而現行是 `OFDB605_9iModelVDB`;Ctl 也沒呼叫它 | 殘留方法,改邏輯時容易改到沒人跑的那份 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:272-279` | 中 |
| E2.5 | `catch (SqlException)` 掛在 Oracle 連線上,全片 6 處 | 永遠進不去;真正的 Oracle 例外落到下一個 catch,訊息被換成空字串 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:89`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:285`、`:560`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:90`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB580_PO.cs:101`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB600A_PO.cs:153` | 中 |

### E.3 一律回報成功

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | `OFDB605`:`int i = 0; ... ExecuteNonQuery(...); i = 1;` 回傳值丟掉 | SP 一筆都沒動也回「成功 1 筆」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:97`、`:158-162` | **高** |
| E3.2 | `OFDB615`:`int i = db.ExecuteNonQuery(...); i = 1;`,而 `if (i == 1)` 決定 Commit | `else` 永遠到不了,UPDATE 0 列照樣 Commit 並回成功 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:285-286`、`:405-414` | **高** |
| E3.3 | `OFDB616`:`int i = 0;` 在迴圈裡被 `i = 1;` 無條件設定 | 同上 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:202`、`:309` | **高** |
| E3.4 | `OFDB608`:「0 筆就 rollback 並回『無可執行之資料』」整段被註解 | 現在一律 Commit 回成功,筆數寫死 1 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB608OracleDao.cs:69-85` | **高** |
| E3.5 | `OFDB560` / `OFDB570`:`if (ExecuteNonQuery(...) <= 0) { rollback; 執行失敗 }` 被 `/* */` 註解,外殼還在 | 寫 0 筆也算成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:101-107`、`:143-149` | **高** |
| E3.6 | `OFDB540` / `OFDB580` / `OFDB600A` / `OFDB672` / `OFDB673`:成功訊息寫死「執行成功」,不看 `ExecuteNonQuery` | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:85-87`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB580_PO.cs:96-98`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB600A_PO.cs:147-148`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:58-61`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:37-40` | 中 |
| E3.7 | `OFDB566`:註解寫「格式正確 寫入temp檔」,但 `bl` 只在 `IsImportRecFormatError(...)` **回 true** 時被設為 true;而且 `AddResultRow(bl, ...)` 直接把它當成功旗標 | 若方法名字是字面意思(有格式錯就回 true),等於**只有格式錯才匯入,而且回報成功**。方法無原始碼,從呼叫端反推 —— 標**假設**,但兩種解釋都表示這裡的旗標語意沒人講清楚 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB566_PO.cs:60`、`:69-80` | **高** |

### E.4 例外被吞、fail-open

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E4.1 | `OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 的 **27 個 `Check_*` 全部 fail-open**(`bool boolvalue = true;` + catch 不改值 + `return boolvalue`) | DB 連不上 / 表改名 / 權限不足 → 所有前置卡控「通過」→ SP 照跑 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:284`、`:313-319`;`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:247`、`:292`、`:332` | **高** |
| E4.2 | `OFDB605.ValidateCtlData` 例外時 `return true` | 「`OFDB600` 跑過沒有」查不出來 = 當作跑過了 = 放行 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:206-210` | **高** |
| E4.3 | `OFDB605.ValidatePCode` 例外時 `return true` | 「還有大於此日期的拋轉資料」查不出來 = 放行拋轉回復 | `:259-263` | **高** |
| E4.4 | `OFDB600_Service.GetTIMES` 裡的 `catch { }`(完全空) | 某個時刻字串格式壞掉,那個時刻直接消失,**沒有任何 log** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151` | **高** |
| E4.5 | `OFDB609_Ctl` 兩個空 `catch { }` | 同上 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:427`、`:439` | 中 |
| E4.6 | `OFDB615` / `OFDB616` 例外時把訊息寫進**輸入**的 `vdb`,回傳的卻是新建的 `result` | 呼叫端拿到空的 `Result`,`Rows.Count > 0` 不成立 → **例外被當成沒失敗** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:420` 對 `:429`;`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:435` 對 `:444` | **高** |
| E4.7 | 多支在 `catch` 裡 `AddResultRow(false, 0, string.Empty)` | 使用者看到「失敗」但沒有原因 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:100`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:169`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs:209` | 中 |
| E4.8 | `OFDB672` / `OFDB673` 在 `catch` 裡把 `ex.Message` 直接回給畫面 | 內部錯誤外洩;與 E4.7 是相反方向的同一類問題 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:66`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:45` | 低 |

### E.5 交易與 rollback 的破口

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | `tran.Rollback()` 沒有 null 檢查,全片多處 | `BeginTransaction` 自己失敗時,catch 裡再噴 NRE,**原始例外被蓋掉** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:91`、`:98`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:157`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB540_PO.cs:92`、`:99` | 中 |
| E5.2 | `OFDB560`:`tran` 只在兩個 `if` 分支裡被建立,`tran.Commit()` 在分支外 | 空檔案(兩分支都不進)→ `tran.Commit()` NRE → catch 裡 `tran.Rollback()` 再 NRE | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:81`、`:112`、`:152`、`:157` | **高** |
| E5.3 | `OFDB570`:`mModel.DataEntity.OFD570A[0]` 在沒檢查 Count 的情況下取用 | 空檔案 → `IndexOutOfRangeException` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:103` | 中 |
| E5.4 | `OFDB570` 分兩段交易,第一段寫完就 Commit | 第二段 SP 失敗時,第一段的 DELETE+INSERT 已經落地 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:95-108` | 中 |
| E5.5 | `OFDB565` 開兩個連線兩個交易(`TA` + `PTPF`),各自 Commit / Rollback | 沒有兩階段提交,一邊成功一邊失敗就對不起來 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB565_PO.cs:50`、`:54`、`:223-231` | 中 |
| E5.6 | `OFDB671` 同型:`tran`(TA)+ `tranPTPF`(PTPF) | 同上,而且 `SerialNo` 在 PTPF 那邊發號 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:38-40` | 中 |
| E5.7 | `OFDB601A` 家族:檢查不過時 `return modelVDB` 直接從 try 跳出,**既沒 Commit 也沒 Rollback**,只靠 `finally` 的 `Dispose(tran)` | 行為取決於 `Dispose` 的實作(無原始碼);正常應該明確 Rollback | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:141`、`:266-270` | 中 |
| E5.8 | `OFDB608` / `OFDB616` 的 `BeginTransaction()` 寫在 `try` **外面** | 開交易失敗時例外穿過 PO 打到 FormProxy,使用者看到框架錯誤 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB608OracleDao.cs:50`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:187` | 中 |
| E5.9 | `OFDB600`:`SendMail` 在 `tran.Commit()` **之前**呼叫 | commit 失敗時信已寄出、資料卻回滾 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:75-76` 與 `:84` | **高** |

### E.6 無鍵 / 位置式 / 串接的 SQL

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | `OFDB672`:`insert into OFDB672 values(...)` **沒有欄位清單** | 表加欄位或調順序就插錯欄 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:43-52` | **高** |
| E6.2 | `OFDB671`:`DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN`,而該值由寫死字串 `"OFDB671_A"` 比對 FunctionID 決定 | FunctionID 一變就洗錯半邊;grid 空的時候會把那半邊整個清空 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:43-49` | **高** |
| E6.3 | `OFDB605`:四處把值(甚至欄位名)串進 SQL | 參數化只做一半(`architecture.md §4.3`) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:62`、`:65`、`:194`、`:301` | **高** |
| E6.4 | `OFDB562`(OFDB 那份):把**比較運算子**串進 SQL | 那份跑不起來所以影響為零,但救活就會變成活的洞 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:75` | 低 |
| E6.5 | `OFDB673.Select` **完全沒有 WHERE** | 整張 `OFDB672` 全撈,看得到別人的申請 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:66-75` | 中 |
| E6.6 | `OFDB680`:`SELECT ALERT_LIMIT_TIMES FROM OFD680A` **沒有 WHERE**,服務端取 `[0]` | 表有第二列就永遠不生效 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:704`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:120` | 中 |

### E.7 成對邏輯只改一邊

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E7.1 | `OFDB600` 的跨午夜補丁(`< '02'` 就把日期減一)只加在 `OFD655A` / `OFD661A` / `OFD657A` / `OFD658A` / `OFD601CHG` 五張,`OFD620A` / `OFD651A` 兩張**沒加** | 凌晨 0~2 點執行時,申購與買回筆數會少算 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:366`、`:371` 對 `:376`、`:381`、`:386`、`:391`、`:396` | **高** |
| E7.2 | `GetBefExecRowCount` 的舊 SQL 用 `#region` 包(還是活的),`GetAftExecRowCount` 的用 `//` 註解(真的死了) | 同一支的兩個方法處理方式不一致,見 E2.2 | `:320-359` 對 `:442-467` | **高** |
| E7.3 | `OFDB600` 的 `AddInParameter` 一處用 `"CHECK_DATE"`、另一處用 `":CHECK_DATE"` | 能不能跑取決於 provider 容錯 | `:404` 對 `:498` | 低 |
| E7.4 | `OFDB615` / `OFDB616` 的 SQL 用 `@` 前綴參數,但連線是 Oracle;同專案其他支用 `:` | 〔假設〕框架有做轉換,否則整支跑不動。**無原始碼可證** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:172` 對 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB612OracleDao.cs:170` | 中 |
| E7.5 | `OFDB602A` / `OFDB603` 兩支都有變數 `CheckOFD561Transfer` 接 `Check_OFD651_Transfer` 的回傳(`651` 打成 `561`) | 無功能影響;是複製貼上的證據 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB602A_PO.cs:154`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB603_PO.cs:153` | 低 |
| E7.6 | `OFDB562`(OTAB)四個方法名把 `CONFIRMED` 拼成 `COMFIRMED` | 同上 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB562_PO.cs:36-45` | 低 |

### E.8 被註解但外殼還在的檢核 / 功能

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | `OFDB600_Ctl` 的三種通知信(`Gen36` / `Gen39` / `Gen46`)整段被註解,但 `OFD681` / `OFD681_EMP` / `OFD681_Err` 三張 DataTable 還在填 | **通知信已經不再寄**,但看程式會以為有寄 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:172-196`、`:282-289` | **高** |
| E8.2 | `OFDB607` 的第二組 Commit / Rollback 被註解 | 只剩上面那一組,兩段邏輯的意圖不明 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB607OracleDao.cs:266-283` | 中 |
| E8.3 | `OFDB615` 的密碼加解密(`AtlasEncrypt.Encrypt`)被註解,理由寫「Sharon無法執行先註解」 | 密碼欄現在填 `"N/A"`,靠 LDAP。**若有人以為 `OFD607A.ES_PSW` 還存得到密碼就會找錯地方** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:135`、`:162-170` | 中 |
| E8.4 | `OFDB615` 的語音密碼(`IVR_VICODE`)分支整段被註解 | 「只剩補發網路密碼」,而 `SYSTEM_ID` 因此寫死 `'1'` | `:150-154`、`:364-382`、`:384-386` | 中 |
| E8.5 | `OFDB680_Service` 的 `BF_SRNO` 由畫面決定那段被註解,改成寫死 `-1` | **自動跑與手動跑行為不同** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:77-80` | 中 |
| E8.6 | `OFDB680_Service` 的整個 `DoExecute()` 舊版(直接 `new OFDB680_Ctl()` 不走 Pxy)被註解留在檔尾 | 讀的人會以為它直連 Control | `:211-239` | 低 |

### E.9 迴圈 break / 位置取值 / 檔案處理

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E9.1 | `OFDB560` UI:`if (strData.Length == 0 \|\| strData[0] == "") break;` | 檔案中間有空列,**後面所有資料靜靜被吞掉** | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs:61` | **高** |
| E9.2 | `OFDB560` UI:第一行是空的就 `return`,**沒設 `e.Cancel = true`** | 批次照跑,接著踩 E5.2 的 NRE | `:57` | **高** |
| E9.3 | `OFDB560` UI 用 `strData[0]`~`strData[14]` 位置取欄 | 上游調欄序就整批對錯,只檢查長度不檢查內容 | `:64`、`:72-84`、`:89`、`:97-110` | 中 |
| E9.4 | `Encoding.Default` 讀寫檔,多處 | 依機器語系而定 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs:55`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:241`、`:247`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:196`、`:202` | 中 |
| E9.5 | `WriteLog` 先整檔讀進記憶體再整檔覆寫 | O(n²),寫到一半當掉整天 log 就沒了 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:239-252`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:194-207` | 低 |
| E9.6 | `OFDB600_Service`:`sEXEC_TIMES.PadLeft(4, '0');` **回傳值沒接** | 字串不可變,這行等於沒做;不足四碼的時刻會丟例外並被 E4.4 的空 catch 吞掉 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:130` | **高** |
| E9.7 | `MaskName` 用 `Replace(舊, 星號)` 而不是依位置遮 | 重複字會多遮;單字姓名讓 `Substring(1,0)` 產生空字串,`Replace("", ...)` 丟 `ArgumentException` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:510-526` | 中 |
| E9.8 | `OFDB673` UI:`ugrdOFDB672.ActiveRow` 沒有 null 檢查 | 沒選列就按執行 → NRE | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:83-85` | 中 |

### E.10 寫死常數與假四眼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E10.1 | `OFDB671` 把 `OFD678A` 的 `Status` 寫死 `'301'`、四組四眼人員時間全塞同一個 `CreateID`、`RejectDate` 寫死 `1900-01-01` | **這張表的核准軌跡是假的**,查稽核會被誤導 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:70-82` | **高** |
| E10.2 | `OFDB615` / `OFDB616` 對 `LOG602` 做同一件事 | 同上,而且 `LOG602` 是稽核用的 log 表 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:351`、`:355` | **高** |
| E10.3 | `OFDB560` 的 `FND003` INSERT 寫死 `COL_TYPE='D'`、`TRAN_TYPE='C'`、`TRN_CODE='00'`;`MON001` 寫死 `FN_CLASS_TYPE='2'` | 業務規則埋在 SQL 字串裡〔客戶特定〕 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:69`、`:71`、`:76`、`:122` | 中 |
| E10.4 | `OFDB570` 的 `BF_NO` 寫死 `0` | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:72` | 低 |
| E10.5 | `OFDB601A` 家族的 SP `WCODE` 寫死 `'I'` / `'D'` | 可讀性尚可(有註解),但值域不在 `CTL014` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:182`、`:245` | 低 |
| E10.6 | `OFDB615` 的 `sysdate+2`(密碼有效兩天)、`EC_SYSTEM_TYPE='3'`、`SYSTEM_ID='1'`、`CHG_TYPE='4'` | 全部寫死在 SQL 字串〔客戶特定〕 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:324-325`、`:349`、`:350`、`:386` | 中 |
| E10.7 | `OFDB609` 的排程 SQL 寫死 `SYSTEM_ID='1' AND EC_SYSTEM_TYPE='1'` | 換代碼就抓不到時刻,服務靜靜不跑 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:573` | 中 |
| E10.8 | 三支服務的 log 路徑寫死 `"C://Vendor//WindowService//<代號>//"` | 〔客戶特定〕 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:220`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:175` | 低 |
| E10.9 | `OFDB560` 的 `FND003` 流水號用 `NVL(MAX(TO_NUMBER(seq,'99999')),1)+1` | 空表時第一筆是 2 不是 1;同批多列在同一未 commit 交易內取號,結果取決於隔離等級 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:64`、`:79` | 中 |

### E.11 使用者介面上的誤導

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E11.1 | `OFDB673` 的「是否同意變更？」按**「否」也會執行**(走退件路徑),沒有 `e.Cancel = true` | 使用者以為按「否」是取消 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89-93` | **高** |
| E11.2 | `OFDB673` 的 `wAPPROVE` 判斷的是**參數存不存在**,不是值 | 目前靠 UI 的寫法剛好正確,任何人改成「一律加參數、用值區分」就會變成全部核准 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:36` | **高** |
| E11.3 | `OFDB673` 傳給 SP 的 `USERID` 是那筆資料的 `CREATEID`(申請人),不是審核者 | SP 記到的「使用者」是申請人,審核者是誰在 repo 內查不到 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:88` | 中 |
| E11.4 | `OFDB609` 的 LDAP 失敗訊息叫使用者「去 `OFDB609` 按『更新LDAP資料』」—— 而那就是他剛按的畫面 | 複製貼上 `OFDB003` 的文案沒改 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:139` | 中 |
| E11.5 | `OFDB609` LDAP 失敗時 `Result.Clear()` 再塞失敗訊息,把 DB 已 commit 的事實蓋掉 | 與 `ofdb.md §6.1` 記的 `OFDB003` 行為一模一樣:**看起來失敗,資料其實已生效** | `:141-142` | **高** |

### E.12 其他

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12.1 | `CommandTimeout = 0` 且註解「此程式讓它永久跑」,全片 9 處 | 卡住的 SP 不會超時,只會一直佔連線 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:51`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:135`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB560_PO.cs:85`、`:126`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB570_PO.cs:75`、`:102`、`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:176`、`:239`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:46` | 中 |
| E12.2 | `OFDB680` 服務的 config 含三組明文資料庫帳密 | 拿到 repo 就拿到 `TA` / `SWProduct` / `Logging` 的連線(`architecture.md §8.7` 已標同型);**本文只記位置不抄值** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config:246-262` | **高** |
| E12.3 | 三支服務靠 `Environment.UserName == "SYSTEM"` 決定跑不跑 | 用非 LocalSystem 帳號安裝 → 卡在 `Console.ReadLine()`,**沒有任何錯誤訊息** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/Program.cs:18`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/Program.cs:14` | **高** |
| E12.4 | 三支服務的 Remoting 三行初始化在 `Start()` 與 `OnStart()` 各出現一次 | `architecture.md §8.4` 標為「意圖不明」;本片確認三支全一樣,是樣板不是個案 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:42-44` 與 `:138-140` | 低 |
| E12.5 | `OFDB672` 的重複檢查用 `Convert.ToString(ExecuteScalar(...)) != ""` | 查得到列但 `createid` 是 NULL 時也是 `""`,重複申請會被放行 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:32-37` | 中 |
| E12.6 | `OFDB680` 的重跑鍵 `DATACHECK` 是字串拼的(`基金清單 + 日期 + "-1"`) | 中途基金上下架 → 鍵值變了 → 舊資料刪不掉,重跑會重複 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:83`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:410` | 中 |

### E.13 看起來像 bug,其實不是

| 觀察 | 為什麼不是 bug |
|---|---|
| `OFDB566_PO` 繼承 `BasicEVAPO`(`architecture.md §3.1.1` 說那個基底的連線恆為 null) | 它整支沒碰過 `dbTA` / `dbPTPF`,寫入交給 `ImportFileEngine`,所以不受影響(§0.3) |
| 35 支全部沒宣告 `xTableMapping` | 批次不走四眼,宣告了也沒人讀(§2.1) |
| `S_EC_IPJB600_EXCUTE` 的名字裡是 `IPJB600` | `ATLAS.EC` 同時裝 `OFD` 與 `IPJ`(`architecture.md §2.6`),SP 很可能兩邊共用(附錄 B.1,標假設) |
| `OFDB612` 的 `i += ExecuteNonQuery(...)` 看起來多此一舉 | 它是本片唯一真的用回傳值決定 Commit / Rollback 的一支,是**正確**寫法(§6.8) |
| `OFDB603` 沒有 `A` 後綴卻在 OTAB | `A` 後綴在批次上本來就沒有一致意義(§0.2 第四件事) |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 35 支(EC 19 / OTAB 10 / OFDB 9,其中 `OFDB562`~`OFDB564` 跨兩專案)。 |

由 build_doc.py v2.0.0 於 2026-09-15 14:38 產生 · 標題 103 · 圖 5 · 表格 69 · 程式錨點 358 · § 連結 104 · 引用檢查：畫面 55（缺 0） · Table 26（缺 0） · SP 7（缺 0） · 結果集 13（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofdb4.md
============================================================

# ATLAS OFDB4 模組(OFD 批次第 4 片)全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:OFD 前綴的 B 批次全庫 165 支,拆成多片;本片只涵蓋指定的 **35 支**(見 §3.3)。`OFDB001`–`OFDB287` 那 18 支在 `ofdb.md`,`OFDB540`–`OFDB690` 在另一片,都不在本篇。 **建議讀法**:趕時間只讀四段 —— §0.2(本片最反直覺的六件事)、§6.1(`700` 系列是真流水線)、§6.3(`731`–`734` 整組是 SQL Server 死碼而且掛著外部加密程式)、附錄 E(踩雷,本片挖到 69 條)。

> ⚠ **本片的業務意義**(§0)由表名、Designer 內的中文標籤字串、SQL 註解與訊息字串**推測**。ATLAS 沒有把畫面中文名放進版控;本片 35 支沒有任何一支有 `this.Text`,中文名全部是從 `.Designer.cs` 的控件標籤 grep 出來再反推的。 ⚠ **〔客戶特定〕**:媒體代號 `1201` / `Z1` / `R`、集保機構欄位命名(`FUY3` / `FUS21` / `STF673S3` / `SIN4` / `STFBOK1`)、批號前綴 `FIS`、報表標題「元富證券基金申購明細表」、加密程式的 `參數設定.ini` 協定、`OFD700.PARA_ID = 'DDCT_R'`、扣款行代碼 `'700'`(郵局)為本站台的值。 ⚠ **〔共用〕**:`BMS001A` / `BMS005A` / `RSP006A` / `RSP013A` / `OFD081A` 同時服務 BMS、RSP 與 OFD 其他片(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、`BasicEVAPO` 連線為 null 那條看 `architecture.md §3.1.1`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、WindowsService 與 Remoting 看 `architecture.md §8.4`。**不要整份讀**。同為 OFD 批次篇的 `ofdb.md` 講的是另外 18 支,本篇只在 §6.2 與 §8.2 接它,不重述證據鏈。

## 0. 系統邊界與角色

### 0.1 這 35 支批次管什麼(推測)

**一句話:這 35 支涵蓋六條業務線。其中三條是真的連號流水線(核印扣款、集保上傳、結匯申報),另外三條只是代號相鄰。**

| 群 | 業務線(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| **A 核印與扣款媒體交換** | 受益人扣款帳號送銀行核印 → 收核印回覆 → 產扣款檔 → 收扣款回覆 → 補送 / 人工改狀態 / 退件 | **`OFDB701`**、**`OFDB702`**、**`OFDB703`**、`OFDB704`、`OFDB705`、`OFDB706`、`OFDB707` | `OFD700` `OFD701` `OFD703` `OFD704` `OFD705` `OFD706` `OFD707`、`BMS005A` `RSP006A` |
| **B 集保(TDCC)上傳與回收** | 基金受益權資料上傳集保、加減項轉檔、回收檔匯入,以及「把上傳整批作廢」的兩支回收程式 | `OFDB715`、**`OFDB716`**、**`OFDB717`**、**`OFDB718`**、`OFDB719`、`OFDB720`、**`OFDB721`**、`OFDB722` | `CTL017`、`TRP801A` `TRP802A` `TRP803A` `TRP804A` `TRP805A` `TRP806A` `TRP810A`、`OFD081A` |
| **C 結匯申報與 ID 加密** | 銀行結匯申報收檔匯入 → 送外部程式把身分證字號加密 → 產結匯申報檔與明細 | **`OFDB731`**、**`OFDB732`**、**`OFDB733`**、**`OFDB734`** | `OFD733` `OFD734` `OFD735` `OFD736`、`OFD0813`、`OFDB732_TMP` |
| **D 對外轉檔六支** | 下單 / 短線 / 淨值 / 配息 / 結餘 各自產一份給外部平台的檔案 | `OFDB751`、**`OFDB752`**、`OFDB753`、`OFDB755`、`OFDB756`、`OFDB757` | `OFD751`、`ORDP01DTL` `ORDR01`、`OFD302A`、`OFD281A` `OFD283A` |
| **E 期間計算與申報** | 月結 / 年度計算與主管機關申報資料產生 | **`OFDB871`**、`OFDB911`、`OFDB912`、`OFDB913`、`OFDB921` | `OFD871` `OFD872`、`OFD921A` `OFD922A`、`OFD913A_UPD` |
| **F 單支雜項(彼此無關)** | 員工交易審核、基金設定、FIS 授權檔、定期定額扣款、券商申購買回報表 | `OFDB691`、`OFDB693`、**`OFDB901`**、**`OFDB903`**、`OFDB950` | `OFD620A` `OFD621A`、`OFD688A`、`OFD708`、`OFD904` `OFD9041`、(無表) |

「OFDB4」不是系統裡存在的東西,是本次分片的編號(`OFD` 模組 + 型別 `B` + 第 4 片)。repo 裡沒有任何地方把這 35 支綁成一個單位;它們散在 **三個不同的專案**(見 §0.4)。

### 0.2 最反直覺的六件事

**一、`700` 系列七支是真的一條流水線,而 `715`–`722` 不是「一條」,是「四對」。**

`ofdb.md` 那 18 支被證明是雜燴,所以拿到連號很容易先假設它們無關。本片相反:`OFDB701`→`OFDB702`→`OFDB703`→`OFDB704` 有明確的先後,靠 `OFD701.SEAL_STATUS` / `OFD706` 的狀態接力(§6.1)。但 `715`–`722` 八支拆開來看是 **`716`↔`721`**、**`717`↔`718`**、**`719`↔`720`** 三組「產出 ↔ 回收」的配對,加上 `OFDB715`(只改基金設定)與 `OFDB722`(淨值上傳)兩支獨立的。`751`–`757` 六支則完全無關,只是代號相鄰(§6.4)。

**二、全片 35 支沒有一支有排程,也沒有一支有 Remoting 設定。**

三個 UI 專案的 `App.config` 裡,本片 35 支**每一支**都是 `formstyle="OneStep"`: `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:587-785`(32 支)、 `Dev/ATLAS.EC/Source/UI/UI.EC/App.config:235-246`(2 支)、 `Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:287-292`(1 支)。 `system.runtime.remoting` 區段在這三個 `App.config` 裡**一個都沒有**;整個 repo 只有 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` 與 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` 有(那兩支是 `ofdb.md` 的範圍)。 `static void Main(string[] args)` 在這三個專案裡也是 0 支(只有那三個 WindowsService 有無參數的 `Main()`)。repo 全域找 `.bat` / `.cmd`:只有 `Dev/Modules/Source/Lib/FileHelper/` 底下第三方函式庫的建置腳本,與 ATLAS 業務無關。 **結論與 `ofdb.md` 對 `OFDB003` 的結論一致:本片 35 支全部是人工在選單點開、按「執行」鈕。**

**三、五支的 PO 是未移轉的 SQL Server 程式碼,在 Oracle 上不可能跑起來。**

`OFDB706` / `OFDB731` / `OFDB732` / `OFDB733` / `OFDB734` 全部繼承 `BasicEVAPO`,而且整支用 T-SQL:

| 證據 | 錨點 |
|---|---|
| `SqlDbType` 共 132 次、`OracleDbType` **0 次**(其餘 30 支剛好相反) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:454-455`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:49` |
| `dbo.f_FormatStringToTable(@ID)` —— Oracle 沒有 `dbo` schema 也沒有這個函式 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:436` |
| `EXEC s_OFDB733_Excute @strDECLARE_YM=@xstrDECLARE_YM,...` —— Oracle 不接受這種呼叫語法 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:49` |
| `ISNULL(MAX(DATA_SEQ),0)` / `dbo.f_Nvl(...)` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:558`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:146` |

**而且連線物件本身是 null。** 依 `architecture.md §3.1.1`:`BasicEVAPO` 的 `dbTA` 宣告就是 `= null`,建構子裡建立連線那四行整段被註解,全庫沒有任何子類自己賦值。這五支都直接 `dbTA.CreateConnection()` (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:34`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:430`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:29`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:40`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:42`), 執行到那一行就 `NullReferenceException`。它們仍然在 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj` 裡被編譯,`App.config` 也還有 section,Ctl 也還在 `new` 它們(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB731_Ctl.cs:30`)。 **結論(依據是上述三條交叉,與 `ofdb.md §0.2` 同型):這五支是 SQL Server 時代的遺留,現況等同死碼。**

**四、`OFDB901` 的主檔是 `OFD708`,但它跟 `OFDB707` 一點關係都沒有。**

指派任務時特別點名這條跨號。實際查完的答案是 **代號 `901` 吃 `OFD708` 純屬命名巧合,不是重跑版也不是補檔版**:

| 判準 | `OFDB707` | `OFDB901` |
|---|---|---|
| 動的表 | `OFD706` `OFD701`(讀 `BMS001A` `RSP013A`) | `OFD708` 一張 |
| 做什麼 | 核印退件,呼叫 `s_TA_SealProof_ReturnProcess` | 產生 / 匯入「授權檔」,批號前綴 `FIS` |
| PO 基底 | 裸 PO(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:29`) | `BaseMultiRowEVADaoPO`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:29`) |
| 有沒有四眼 | 沒有 | 有,走 `BeforeAdd` / `AfterAdd`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:39-40`) |
| 畫面標籤 | 「送件批號 / 核印方式 / 送核日期 / 全部失敗 / 全部成功」 | 「客戶種類 / 產生授權檔 / 匯入結果 / 授權資料」 |

全庫 grep `OFD708`,只有四個檔在碰:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901.cs`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901p0.cs`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`(唯讀)。 **`OFDB707` 完全沒出現。** 兩支之間沒有資料相依、沒有呼叫、沒有共用 SP。詳見 §6.6。

**五、掃描器說的「32 支沒有宣告主檔」,實際有五張表被漏掉。**

索引只認得三支:`OFDB731`→`OFD733`、`OFDB871`→`OFD871`、`OFDB901`→`OFD708`。逐支翻 PO 原始碼之後,漏掉的有:

| 漏掉的表 | 為什麼漏 | 錨點 |
|---|---|---|
| `OFD688A`(`OFDB693` 的主檔) | 宣告在 `OFDB693OracleDao.cs`,不是 `*_PO.cs`,檔名規則對不上 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:30` |
| `OFD872`(`OFDB871` 的第二張主檔) | `MasterTable` 在 `Execute` **執行中途被重新指派**,不在建構子 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:190` |
| `OFD871` 的第二個 vdb 名 `OFDB871_CLB` | 同上,`Execute` 內第一次重指派 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:73` |
| `TTP901`(日日定期定額扣款傳檔) | 只出現在 SP 腳本裡,C# 完全沒提 | `DB/SP/S_OTA_OFDB903_EXE.sql:530` |
| `OFD062`(交易別對照) | 同上 | `DB/SP/S_OTA_OFDB903_EXE.sql:22` |

任務裡提醒的「兩段式 `xTableMapping`」(`xTableMapping tp = new xTableMapping(...); this.MasterTable = tp;`)寫法,**本片 35 支一支都沒有**。本片的盲點是另外兩種:**檔名不合規則**(`OracleDao.cs` / `_9iModel.xsd`)與 **執行期重新指派 `MasterTable`**。

**六、同一段 20 行的「匯入檔案格式檢核」被複製了四份,而且四份的判斷都是反的。**

`OFDB702` / `OFDB704` / `OFDB719` / `OFDB751` 的 `PrepareExecute` 逐字相同:

```
if (ImportFileEng.IsImportRecFormatError(ErrMsg, cmdpms)) { bl = true; }
//格式正確 寫入temp檔
if (bl == true) { ImportFileEng.ImportFile(); }
model.Utility.Result.AddResultRow(bl, ...);
```

註解寫「格式正確 寫入 temp 檔」,程式卻是 **格式錯誤時才匯入**,而且把「格式錯誤」當成 `ReturnCode = true`(成功)回傳。錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2337-2350`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:62-73`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:121-160`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:66-77`。 **這是本片最會咬人的一條**(附錄 E1.1),詳細討論在 §6.1.4。

### 0.3 四個世代、四種資料存取路徑

| 世代 | PO 基底 | 連線 | 有沒有宣告 `xTableMapping` | 畫面 | SQL 方言 |
|---|---|---|---|---|---|
| **裸 PO(本片主流)** | 無基底,只實作 `IOFDBxxx_PO` | 自己 `new Database("TA", DbServerType.Oracle)` | 無 | 22 支(`701` `702` `703` `704` `705` `707` `715`–`722` `751` `752` `753` `755` `756` `757` `911` `912` `913` `921` `950`) | Oracle |
| **EVA 滿血** | `BaseEVADaoPO` | 基底管(`dbProduct`) | 有 | `OFDB693`、`OFDB871`、`OFDB903` | Oracle |
| **MultiRow EVA** | `BaseMultiRowEVADaoPO` | 基底管 | 有,`MasterTable.Add(...)` | `OFDB901` | Oracle |
| **舊世代** | `BasicEVAPO` | **`dbTA` 恆為 null** | `OFDB731` 有(舊型別 `TableMapping`),其餘無 | `OFDB706`、`OFDB731`、`OFDB732`、`OFDB733`、`OFDB734` | **SQL Server(未移轉)** |

逐支 PO 類別宣告錨點:

| 畫面 | 類別宣告 | 錨點 |
|---|---|---|
| `OFDB691` | `OFDB691OracleDao : IOFDB691`(另有一份 `OFDB691_PO : BasicEVAPO` 整支被註解) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:14`、`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB691_PO.cs:13` |
| `OFDB693` | `OFDB693OracleDao : BaseEVADao, IOFDB693PO`,主檔 `OFD688A` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:18`、`:30` |
| `OFDB701` | `OFDB701_PO : IOFDB701_PO`(裸,兩個 `Database`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:42`、`:44-45` |
| `OFDB702` | `OFDB702_PO : IOFDB702_PO`(裸,一個 `Database`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:41`、`:43` |
| `OFDB703` | `OFDB703_PO : IOFDB703_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:40`、`:42-43` |
| `OFDB704` | `OFDB704_PO : IOFDB704_PO`(裸,一個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:31`、`:33` |
| `OFDB705` | `OFDB705_PO : IOFDB705_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB705_PO.cs:32`、`:34-35` |
| `OFDB706` | `OFDB706_PO : BasicEVAPO`,**連 `MasterTable` 都不宣告** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:14` |
| `OFDB707` | `OFDB707_PO : IOFDB707_PO`(裸) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:29` |
| `OFDB715` | `OFDB715_PO : IOFDB715_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:25` |
| `OFDB716` | `OFDB716_PO : IOFDB716_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:33`、`:35-36` |
| `OFDB717` | `OFDB717_PO : IOFDB717_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:31` |
| `OFDB718` | `OFDB718_PO : IOFDB718_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:34` |
| `OFDB719` | `OFDB719_PO : IOFDB719_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:34` |
| `OFDB720` | `OFDB720_PO : IOFDB720_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB720_PO.cs:23` |
| `OFDB721` | `OFDB721_PO : IOFDB721_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:34` |
| `OFDB722` | `OFDB722_PO : IOFDB722_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB722_PO.cs:37` |
| `OFDB731` | `OFDB731_PO : BasicEVAPO`,主檔 `OFD733`(舊型別) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:22`、`:27` |
| `OFDB732` | `OFDB732_PO : BasicEVAPO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:19` |
| `OFDB733` | `OFDB733_PO : BasicEVAPO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:15` |
| `OFDB734` | `OFDB734_PO : BasicEVAPO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:17` |
| `OFDB751` | `OFDB751_PO : IOFDB751_PO`(**完全沒有 `Database` 欄位**) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:30` |
| `OFDB752` | `OFDB752_PO : IOFDB752_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB752_PO.cs:34` |
| `OFDB753` | `OFDB753_PO : IOFDB753_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB753_PO.cs:27` |
| `OFDB755` | `OFDB755_PO : IOFDB755_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB755_PO.cs:35` |
| `OFDB756` | `OFDB756_PO : IOFDB756_PO`(裸,兩個) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB756_PO.cs:34` |
| `OFDB757` | `OFDB757_PO : IOFDB757_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB757_PO.cs:32` |
| `OFDB871` | `OFDB871_PO : BaseEVADaoPO, IOFDB871_PO`,主檔 `OFD871`(執行中途再換兩次) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:28`、`:36`、`:73`、`:190` |
| `OFDB901` | `OFDB901_PO : BaseMultiRowEVADaoPO, IOFDB901_PO`,主檔 `OFD708`,PK `BATCH_ID` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:29`、`:38`、`:41` |
| `OFDB903` | `OFDB903_PO : BaseEVADaoPO, IOFDB903_PO`,**不宣告主檔** | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:53`、`:57` |
| `OFDB911` | `OFDB911_PO : IOFDB911_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:30` |
| `OFDB912` | `OFDB912_PO : IOFDB912_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB912_PO.cs:30` |
| `OFDB913` | `OFDB913_PO : IOFDB913_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:32` |
| `OFDB921` | `OFDB921_PO : IOFDB921_PO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:25` |
| `OFDB950` | `OFDB950_PO : IOFDB950_PO`,**`Execute` 是空的** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB950_PO.cs:29`、`:56-64` |

> **對「32 支沒宣告主明細」的正式回答**:掃描器說缺,但沒有一支是真的少一層 —— 35 支的六層檔案全部齊全(見 §3.3)。22 支裸 PO 完全繞過 `BaseEVADaoPO`,自己開連線、自己管交易,正是 `architecture.md §6.4` 講的 B 型樣板:輸出是 DB 狀態改變或外部檔案,不是回傳資料集,所以不需要 `xTableMapping`。另外五支(`OFDB693` `OFDB871` `OFDB901` `OFDB903` `OFDB731`)其實有宣告,只是掃描器抓不到(§0.2 第五件事)。

### 0.4 一個代號、三個專案

本片 35 支**不在同一個專案**。這件事在改動與重編時會咬人(`architecture.md §2.4` 的重編順序):

| 專案 | 支數 | 畫面 | Entity 資料夾 |
|---|---|---|---|
| `Dev/ATLAS.OFDB` | 32 | 除下面三支以外全部 | `DataEntity.OFDB3` / `UIEntity.OFDB3` |
| `Dev/ATLAS.EC` | 2 | `OFDB691`、`OFDB693` | `DataEntity.EC` / `UIEntity.EC` |
| `Dev/ATLAS.OTAB` | 1 | `OFDB903` | `DataEntity.OTA` / `UIEntity.OTA`(組件名 `DataEntity.OTAB`) |

`Dev/ATLAS.OFDB/Source/Entity/` 底下有 **四組** Entity 專案(`DataEntity.OFDB` / `OFDB1` / `OFDB2` / `OFDB3`),本片 32 支的 Model / View 全部住在第四組 `OFDB3`。`ofdb.md` 那 18 支住在第一組。這是為了避開 typed DataSet 專案過大的分拆,不是業務分群。

### 0.5 不管什麼

| 不管 | 誰在管 |
|---|---|
| 扣款帳號本身的建檔與四眼 | BMS 的 `BMSM001` 那條線;本片 `OFDB701`–`OFDB707` 只讀 `BMS005A` / `BMS005ACHG` 來組送件名單 |
| 受益人變更單的生效 | `OFDB003`(見 `ofdb.md §6.1`);本片五支只是用 `CHG_UPD_DTTM` 判斷「這筆變更生效了沒」 |
| 集保媒體檔的欄位格式 | `ExportFileEngine` / `ImportFileEngine`(無原始碼,從呼叫端反推),格式定義在 `TRP001A` / `TRPARAMS` |
| 身分證字號怎麼加密 | 外部加密程式(無原始碼),本片 `OFDB732` / `OFDB733` 只負責寫 `參數設定.ini` 與讀回結果檔 |
| 基金主檔建檔 | OFD 的 M 片;`OFDB715` / `OFDB721` 只改 `OFD081A` 的兩個集保相關欄位 |
| 定期定額契約 | OTA 模組;`OFDB903` 只負責產扣款資料與確認 |
| 所有 SP 的內部邏輯 | Oracle 端。本片呼叫 **21 支 SP**,repo 內只有 **1 支** 有腳本(`DB/SP/S_OTA_OFDB903_EXE.sql`),見附錄 B |

### 0.6 使用角色(推測)

本片 35 支**沒有任何一支做角色 / 權限檢查**。全片 grep `MGM_CD` / `MANGR_CODE`:0 命中。跟人有關的只有兩件事:把 `PermissionInfo[0].UserID` 塞進 SP 參數或 `CreateID` / `UpdateID` 欄位(例 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:856`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:106-108`),以及 `OFDB691` 用 `EMAIL` 欄位寄通知信(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:145`)。

| 角色(推測) | 依據 | 用哪些畫面 |
|---|---|---|
| **扣款作業人員** | `OFD703.EXEC_USERID` 只記執行者,不分權 | `OFDB701`–`OFDB707` |
| **集保申報人員** | `CTL017` 的 `SOURCE_ID` 只分資料來源,不分人 | `OFDB715`–`OFDB722` |
| **結匯申報人員** | `OFD733.DECLARE_ID` 是申報單位不是人 | `OFDB731`–`OFDB734` |
| **法遵 / 會計** | `OFD871` / `OFD872` 的 `CLB` / `FSA` 是申報類別 | `OFDB871`、`OFDB911`、`OFDB912`、`OFDB921` |
| **業務主管** | `OFDB913` 直接寫 `ApproveID` / `Confirm_ID`,但沒檢查執行者是不是主管 | `OFDB913` |

### 0.7 全域開關

| 開關 | 在哪 | 效果 |
|---|---|---|
| `formstyle = "OneStep"` | 三份 `App.config` 的每個 section | 決定畫面長成一步式批次;35/35 都是 |
| `SelectedPlugin` | 同上 | `OFDB691` 的值寫成 `OFDB690`(`Dev/ATLAS.EC/Source/UI/UI.EC/App.config:235`),見附錄 E14.1 |
| `OFD700.PARA_ID = 'DDCT_R'` | DB 設定表 | 決定扣款回覆檔的媒體代號;`OFDB704` 寫死查這個值(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:97`) |
| `sEncodeID_Path` / `sENCODE_ID_FILENAME` | `OFDB732` / `OFDB733` 的 Ctl | 外部加密程式的交換目錄;不存在就整支不做事(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:84-89`) |
| `CTL017` 有沒有資料 | DB | `OFDB716` / `OFDB717` 產出後才會有;`OFDB718` / `OFDB721` 靠它決定要不要回收 |
| `TargetFramework` | 三個 UI 專案的 `App.config` | 全部 `.NETFramework,Version=v4.8`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:786`) |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD 批次第 4 片全景:六條業務線、四個世代的 PO 基底、35 支全是人工觸發且沒有任何 Remoting 設定,以及五種出口
圖中文字:① 這 35 支分成六條業務線,只有前三條真的是「連號 = 一條線」 / A 核印與扣款媒體交換 / OFDB701~707 七支 / B 集保 TDCC 上傳與回收 / OFDB715~722 八支 / C 結匯申報與 ID 加密 / OFDB731~734 四支 / D 對外轉檔六支 / OFDB751~757 / E 期間計算與申報 / OFDB871 911 912 913 921 / F 單支雜項 / OFDB691 693 901 903 950 / 跨專案三支 / EC 二支 OTAB 一支 / OFDB701 OFDB702 / 已見 ofdb.md 只補充 / ② 四個世代決定一支能不能跑 —— 最右邊五支是 SQL Server 遺留 / 裸 PO 22 支 / 自建 Database 自管交易 / BaseEVADaoPO 3 支 / OFDB693 871 903 / MultiRow 1 支 / OFDB901 吃 OFD708 / BasicEVAPO 5 支 SQL Server / 706 731 732 733 734 dbTA 恆 null / ③ 觸發方式:35 支全部 formstyle=OneStep,repo 內沒有排程也沒有 .bat / App.config 三份 / UI.OFDB UI.EC UI.OTA / formstyle OneStep 35/35 / 人按執行鈕 / system.runtime.remoting 0 支 / 三個 UI 專案都沒有 / Main(string[] args) 0 支 / 沒有命令列入口 / ④ 出口:四種,沒有一支寄信以外的通知(寄信只有 OFDB691) / ExportFileEngine / 媒體檔 1201 / Z1 / R / 外部加密程式 / 參數設定.ini 交換 / 呼叫 SP 13 支 / repo 內腳本 0 支 / Crystal 報表 / OFDB950 OFDB701 / 寄信 OFDB691 / MailUtility 無原始碼
```

*圖:圖 1 全景。橘框=本片主要入口或已確認的結論;橘虛框=要留意(跑不起來、跨專案);灰虛框=本片以外或已被 ofdb.md 寫過;黑框=無原始碼。第②列決定一支能不能跑,第③列是本片對「排程從哪來」的答案 —— 三個 UI 專案的 App.config 全部只有 OneStep,一個排程都沒有。*

### 1.2 資料表關係

見圖 2。五群表:核印扣款(`OFD700`–`OFD707`)、集保(`CTL017` + 七張 `TRP80xA`)、結匯申報(`OFD733`–`OFD736`)、轉檔計算(各自獨立)、以及只存在於 SQL 字串裡的暫存表(`SEALTMP` / `TRP810ATMP` / `OFDB732_TMP` / `DELETETEMPFILE`)。

### 1.3 觸發方式與批次特性分群

見圖 3。本片對「排程從哪來」的完整答案:35/35 人工觸發、0/35 有 Remoting、22 支自己開交易、16 支 `CommandTimeout = 0`。

### 1.4 連號系列的執行順序與失敗處理

見圖 4。`700` 系列七支是流水線;`715`–`722` 是四對;`751`–`757` 無關。

### 1.5 結匯申報與外部加密程式

見圖 5。本片唯一一組跟 repo 外程式的同步協定(`參數設定.ini` + 三個 `.txt`),沒有逾時、沒有重試。

### 1.6 跨模組影響面

見圖 6。

## 2. 資料模型

```text
[圖] OFD 批次第 4 片動到的資料表分成五群:核印扣款、集保上傳、結匯申報、轉檔計算,以及只存在於 SQL 字串裡的暫存表
圖中文字:核印扣款群:OFD700 是設定、OFD701 是帳號主檔、OFD703~707 是批次與送件 / OFD700 / 媒體與路徑設定 PARA_ID / OFD701 / 扣款帳號核印檔 / OFD703 / 核印扣款處理 Log / OFD704 OFD705 / 送件批次與扣款明細 / OFD706 OFD707 / 篩選申請書與回覆 / 集保群:CTL017 是本次上傳的關卡表,TRP80xA 是七張集保媒體表 / CTL017 / 上傳批次控制 SOURCE_ID 1/2 / TRP801A 802A 804A / FUY FUS2 STF673S / TRP803A 805A 806A / 699S SIN BOK 各帶 _Detail / TRP810A / 集保回收檔 / OFD081A / FUND_ID_TDCC 對照 / 結匯申報群:全部是 SQL Server 語法,OFD733~736 在 xsd 內查不到 Oracle 版 / OFD733 / 結匯申報收檔 DECLARE_YM / OFD734 / 結匯明細 / OFD735 OFD736 / 轉出與暫存 / OFDB732_TMP / 加密前後暫存表 / OFD0813 OFD081 / 基金統編對照 / 轉檔與計算群:各自獨立,沒有共用主檔 / OFD751 / 下單資料 / ORDP01DTL ORDR01 / OFDB752 寫入 / OFD871 OFD872 / CLB 與 FSA 申報 / OFD921A OFD922A / 計算結果與關卡碼 / OFD913A_UPD / 業務員異動待審 / 只存在於 SQL 字串裡或跨專案的表 —— 改欄位時 xsd 找不到 / SEALTMP / OFDB702 OFDB719 共用暫存 / TRP810ATMP / OFDB719 收檔暫存 / DELETETEMPFILE / OFDB732 清檔旗標 / OFD904 OFD9041 / OTAB 定期定額扣款 / OFD688A / EC OFDB693 主檔
```

*圖:圖 2 資料表關係。橘框=本片會寫的核心表;橘虛框=要留意(SQL Server 遺留、或表名只躲在 SQL 字串裡);灰虛框=別的模組維護的唯讀對照表。最後一列的五張表在本片 xsd 裡完全查不到,改欄位只能 grep。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

本片只有 **5 支** 真的宣告了 `xTableMapping` / `TableMapping`,而且其中兩支的宣告不在建構子裡:

| 畫面 | 主檔(實體表) | vdb 表名 | 宣告位置 | 備註 |
|---|---|---|---|---|
| `OFDB693` | `OFD688A` | `OFDB693` | 建構子 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:30`;掃描器抓不到 |
| `OFDB731` | `OFD733` | `OFDB731` | 建構子,**舊型別 `TableMapping`** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:27` |
| `OFDB871` | `OFD871` | `OFDB871_FSA` | 建構子 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:36` |
| `OFDB871` | `OFD871` | `OFDB871_CLB` | **`Execute` 內重指派** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:73` |
| `OFDB871` | `OFD872` | `OFDB871_FSA` | **`Execute` 內再重指派** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:190` |
| `OFDB901` | `OFD708` | `OFD708` | 建構子,`MasterTable.Add(...)` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:38` |

> **`OFDB871` 這三行是本片最容易讀錯的地方。** 建構子填 `OFD871`/`OFDB871_FSA`,`Execute` 開頭改成 `OFD871`/`OFDB871_CLB`,寫完 CLB 再改成 `OFD872`/`OFDB871_FSA`。也就是說 **建構子那一行的 vdb 名從頭到尾沒被用過**,而且 `MasterTable` 是實例欄位 —— 同一個 PO 實例被 `DataAccessPool` 重用時,第二次進 `Execute` 拿到的是上一次留下的值。實際上 `Execute` 一開頭就重設(`:73`),所以不會出錯,但這是靠巧合而不是設計。

### 2.2 核印扣款群的七張表(本片最完整的一組)

| 表 | 角色(推測) | 誰寫 | 誰讀 | 依據 |
|---|---|---|---|---|
| `OFD700` | 媒體 / 路徑設定,`PARA_ID` 分類 | 本片沒有一支寫 | `OFDB703` `OFDB704` `OFDB705` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:88-97` |
| `OFD701` | 扣款帳號核印檔(核印狀態的本體) | `OFDB702`(經 SP) | `OFDB701` `OFDB703` `OFDB705` `OFDB706` `OFDB707` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1069` |
| `OFD703` | 核印 / 扣款處理 Log,一次執行一筆 | `OFDB701` | 本片無人讀 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1010-1013` |
| `OFD704` | 送件批次(批號 × 扣款總行) | `OFDB701` `OFDB703` | `OFDB701` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:864` |
| `OFD705` | 扣款明細 | **沒有人寫** —— `OFDB703` 的 INSERT 整段被註解,只剩 `#region OFD705` 外殼 | `OFDB703`(讀) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1090-1095` |
| `OFD706` | 核印篩選申請書檔(這一批送了誰) | `OFDB701` | `OFDB701` `OFDB702` `OFDB705` `OFDB707` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:904-916` |
| `OFD707` | 核印回覆明細 | 本片只在被註解的程式碼裡寫 | `OFDB702` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2260` |

### 2.3 集保群:`CTL017` 是關卡,`SOURCE_ID` 分兩條線

`CTL017` 是本片唯一一張被「產出」與「回收」兩支同時當關卡用的表。它的 `SOURCE_ID` 把八支分成兩條互不干擾的線:

| `SOURCE_ID` | 產出 | 回收 | 媒體代號 | 集保表 |
|---|---|---|---|---|
| `'1'` | `OFDB716` | `OFDB721` | `TRP805`(SIN)、`TRP806`(BOK)、`TRP803`(699S) | `TRP805A` `TRP805A_Detail` `TRP806A` `TRP806A_Detail` `TRP803A` |
| `'2'` | `OFDB717` | `OFDB718` | `TRP801`(FUY)、`TRP802`(FUS2)、`TRP804`(STF673S) | `TRP801A` `TRP802A` `TRP804A` |

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:73`(`SOURCE_ID = '2'`)、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:79`(`SOURCE_ID = '1'`)、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:156`、`:207`、`:257`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:326`、`:443`。

集保表的欄位名是集保端的代號,不是 ATLAS 命名:`TRP801A.FUY3`、`TRP802A.FUS21`、`TRP804A.STF673S3`、`TRP805A.SIN4`、`TRP806A.STFBOK1`、`TRP803A.STF3` 都是「基金的集保代號」欄位,對應 `OFD081A.FUND_ID_TDCC`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:101`)。〔客戶特定〕

### 2.4 主鍵與四眼欄位

本片只有四支真的走 EVA 四眼,其餘 31 支要嘛沒有四眼欄位、要嘛自己手寫:

| 畫面 | 四眼怎麼來 | 錨點 |
|---|---|---|
| `OFDB693` | 基底 `BaseEVADao` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:18` |
| `OFDB871` | 基底 `BaseEVADaoPO`,但 INSERT 自己列 24 個欄位含 `VerifyID` / `ApproveID` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:91-103` |
| `OFDB901` | 基底 `BaseMultiRowEVADaoPO` + `BeforeAdd` / `AfterAdd` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:39-40` |
| `OFDB903` | 基底,但 `Execute` 完全走自己的 SQL,沒用基底的 `Add` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:105` |

**`OFDB701` 是本片唯一一支自己把四眼欄位全部填滿的裸 PO**,而且填得有問題(見附錄 E2.1):它把 `CreateID` / `EntryID` / `VerifyID` / `ApproveID` **全部填成執行者本人**,`RejectID` 填空白、`RejectDate` 填 `'1900/01/01'`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:880-894`)。也就是「送件即視為已覆核」,四眼形同虛設。

**`OFDB913` 直接 `UPDATE` 主檔的四眼欄位,完全繞過 EVA 引擎**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:79-83`),與 `ofd5.md` 在 `OFDM082B_PO.cs:66-70` 發現的是同一型缺陷(附錄 E2.2)。

### 2.5 狀態碼(從程式反推,標來源)

| 表 / 欄位 | 值 | 意義(推測) | 來源 |
|---|---|---|---|
| `OFD704.STATUS` | `301` | 送件批次已建立 | 寫死於 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:882` |
| `OFD703.STATUS` | `302` | 處理 Log 已建立 | 寫死於 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:996` |
| `OFD703.JOB_ID` | `1` / `5` | `1` = 核印送件(要寫 `OFD706`);`5` = 補送件(不檢查匯出筆數就 commit) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:902`、`:1050` |
| `OFD701.SEAL_TYPE` | `1` / 其他 | `1` = 一般(不產檔,走 SP);其他 = ACH / 財金(產媒體檔) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1021` |
| `OFD701.SEAL_STATUS` | `1` / `2` / `3` | 核印中 / 成功 / 失敗(從被註解的 SQL 反推,現行由 SP 寫) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:999-1004`(註解) |
| `TRP80xA.DEL_YN` | `N` / `Y` | 有效 / 已作廢(軟刪除) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:99`、`:102` |
| `CTL017.SOURCE_ID` | `1` / `2` | `716`/`721` 那條線 / `717`/`718` 那條線 | §2.3 |
| `OFD913A_UPD.STATUS` | `201` `202` `203` `204` → `301` `302` — `304` | 待審 → 已審;`203` 是「刪除待覆核」,執行時直接 DELETE | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:72`、`:90-101` |
| `OFD904.CFM_CD` | `Y` / `N` | 已確認 / 取消確認 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:214`、`:219` |
| `OFD922A.CTL_CODE` | `1` | 該年度該期已計算完成 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:112` |
| `OFD708.BATCH_ID` | `FIS` + `yyyyMMdd` + 4 碼流水 / `-` | 已編批號 / 匯入結果暫用 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:65`、`:71`、`:96` |
| `OFDB903` `Job_Type` | `0` / `1` | 扣款作業 / 確認作業 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:132`、`:208` |
| `OFDB903` `TYPE1` | `0` / `1` / `2` | 產生 / 重作 / 刪除 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:155`、`:203`、`DB/SP/S_OTA_OFDB903_EXE.sql:3` |

### 2.6 與其他模組共用的表

| 表 | 本片怎麼用 | 誰維護 |
|---|---|---|
| `BMS001A` / `BMS001ACHG` | 唯讀,組核印送件名單並判斷變更生效沒 | BMS(見 `bms.md §2`) |
| `BMS005A` / `BMS005ACHG` | 唯讀,取扣款帳號與銀行分行 | BMS |
| `RSP006A` / `RSP013A` | 唯讀,取定期定額扣款帳號與其變更 | RSP |
| `OFD081A` / `OFD081V` | 讀基金主檔;`OFDB715` / `OFDB721` **會寫**兩個集保欄位 | OFD 的 M 片 |
| `OFD020V` / `OFD074` / `OFD076` | 唯讀,銀行別與總行對照 | OFD 的 M 片 |
| `OFD302A` / `OFD303A` | 唯讀,淨值與過帳控制 | OFD 的 M 片 |
| `CTL012` / `CTL015` | 唯讀,關帳與代碼 | 共用控制表 |
| `OFD281A` / `OFD283A` | 唯讀,`OFDB755` 產配息檔 | `ofdb.md` 的 `OFDB281` 那條線 |

### 2.7 欄位中文名(來自 Designer 標籤,不是 xsd Caption)

本片 35 支的 `Model.xsd` 幾乎沒有 `msdata:Caption`,所以中文名只能從 `.Designer.cs` 的控件標籤反推。以下是反推出來、跨多支共用的欄位:

| 欄位 | 中文名 | 出現在 |
|---|---|---|
| `SEAL_TYPE` | 核印方式 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB705.designer.cs:424` |
| `SEAL_DATE` | 送核日期 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB705.designer.cs:232` |
| `BATCH_ID` | 送件批號 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB705.designer.cs:205` |
| `AGENT_BANK` | 代理(扣款)銀行 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB707.designer.cs:406` |
| `SUB_ACC_NO` | 扣款帳號 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB707.designer.cs:312` |
| `SUB_ID_NO` | 扣款人ID | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB707.designer.cs:324` |
| `ACT_DDCT_DATE` | 實際扣款日期 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.designer.cs:1118` |
| `BAL_DATE` | 結餘日期 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB716.designer.cs:241` |
| `TRANS_DATE` | 上傳集保日期 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB716.designer.cs:394` |
| `FUND_ID_TDCC` | 集保受益憑證代號 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB716.designer.cs:430` |
| `DECLARE_YM` | 年月 / 申報日期 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB731.designer.cs:348`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB733.designer.cs:334` |
| `CP_ORDER_NO` | 下單編號 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB757.designer.cs:216` |
| `TDCC_ID_NO_IT` | 集保機構統編(受益人開戶統編) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB757.designer.cs:559` |
| `ALLOT_DATE` | 分配基準日 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB755.designer.cs:224` |
| `DEF_SUB_DATE` | 契約扣款日 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB903.designer.cs:163` |
| `REAL_SUB_DATE` | 實際扣款日 | `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB903.designer.cs:321` |

### 2.8 只存在於 SQL 字串裡的表(xsd 查不到)

| 表 | 誰用 | 錨點 |
|---|---|---|
| `SEALTMP` | `OFDB702` 寫、`OFDB719` 也有同名方法 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2362`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:214` |
| `TRP810ATMP` | `OFDB719` 收檔暫存 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs`(`IsExistsData`) |
| `OFDB732_TMP` | `OFDB732` 加密前後暫存 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs` |
| `DELETETEMPFILE` | `OFDB732` 清檔旗標 | 同上 |
| `CTL017` | `OFDB716`–`OFDB722` 六支 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:71` |
| `TRP805A_Detail` / `TRP806A_Detail` | `OFDB721` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:91`、`:101` |
| `ORDP01DTL` / `ORDR01` | `OFDB752` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB752_PO.cs` |
| `TTP901` / `OFD062` | 只在 SP 腳本裡 | `DB/SP/S_OTA_OFDB903_EXE.sql:530`、`:22` |

### 2.9 `OFD081A` 的兩個集保欄位:xsd 查得到,但不在本片的 xsd 裡

建置工具會對 `OFD081A` 報一句「欄位在 xsd 找不到:`FUND_ID_TDCC`, `TDCC_START_BAL_DATE`」。**這不是欄位不存在,是本片沒有任何一份 xsd 宣告它們。**

| 事實 | 錨點 |
|---|---|
| 兩個欄位真的存在,宣告在 `OFD081A` 自己的維護畫面 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD5/OFDM081AModel.xsd`、`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD5/OFDM081AView.xsd` |
| `FUND_ID_TDCC` 在本片有一份 xsd 宣告(但 table 名不是 `OFD081A`) | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB3/OFDB715Model.xsd` |
| `TDCC_START_BAL_DATE` 在本片 **一份 xsd 都沒有** —— `OFDB721` 是用手寫 SQL 直接 `UPDATE` 它 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:126-128` |
| `DB/Table/` 底下也查不到這兩個欄位的 DDL | 全目錄 grep:0 命中 |

**對維護的意義**:要改 `TDCC_START_BAL_DATE` 的型別或長度,唯一能看到它的地方是 `OFDM081AModel.xsd`(在 `ATLAS.OFD` 專案),而寫它的程式在 `ATLAS.OFDB` 專案而且完全不經過 typed DataSet。兩邊沒有任何編譯期關聯,改一邊不會讓另一邊編不過。依 `architecture.md §5.5`,xsd 是 repo 內唯一的 schema 來源 —— 這種「寫入端完全不出現在 schema 裡」的欄位,就是那條規則的破口。

## 3. 畫面清冊

```text
[圖] 35 支依觸發方式與 Remoting 分群的結果:全部人工觸發、零個 Remoting 區段,以及交易邊界、重跑安全、失敗處理的三種分佈
圖中文字:① 觸發方式只有一種:使用者在選單點開畫面,按「執行」。35/35 / UI.OFDB App.config / 32 支 section 全 OneStep / UI.EC App.config / OFDB691 OFDB693 / UI.OTA App.config / OFDB903 / OFDB691 的 SelectedPlugin 指到 OFDB690 / 設定值抄錯 / ② Remoting:三個 UI 專案的 App.config 都沒有 system.runtime.remoting / 本片 35 支 0 個 remoting 區段 / 與 ofdb.md 的 OFDB600/609 對照 / WindowsService.OFDB600 / 2 個含 wellknown / WindowsService.OFDB609 / 2 個含 wellknown / WindowsService.OFDB680 / 0 個 / ③ 交易邊界:22 支自己 BeginTransaction,SP 跑在 C# 開的交易裡 / 雙交易 dbTA + dbPTPF / 12 支 兩次 commit 不原子 / 單交易 dbTA / 10 支 / 交易在 EVA 基底裡 / OFDB693 871 901 903 / 完全沒有交易 / OFDB704 751 950 / CommandTimeout = 0 / 16 支 無逾時保護 / ④ 重跑安全:三種做法,兩種不安全 / 先 DELETE 再 INSERT / OFDB871 OFDB731 OFDB732 / 檢查已處理旗標 / OFDB718 OFDB921 OFDB716 / 無任何保護 直接追加 / OFDB701 每按一次多一批 / DEL_YN 軟刪除 / OFDB718 OFDB721 只翻旗標 / ⑤ 失敗處理:全片沒有 log 表,最終出口只有畫面訊息 / catch 後轉成 Result 訊息 / 31 支 不 rethrow / catch 後訊息是空字串 / OFDB911 912 921 950 / catch 連 log 都沒有 / OFDB913 / catch 內 tran 是 null / OFDB921 BeforeExecuteCheck
```

*圖:圖 3 觸發方式與批次特性分群。橘框=已用設定檔證實的結論;橘虛框=要留意的行為;灰虛框=本片以外(ofdb.md 已寫的三支 WindowsService,拿來對照 Remoting 有無)。第③④⑤列就是 §3 清冊那三欄的來源。*

### 3.1 維護 M

(本片無此類畫面)—— 指派的 35 支全部是型別 `B`。本片沒有任何一支畫面提供新增 / 修改 / 刪除主檔的四眼流程;唯一接近的是 `OFDB901`,它走 `BaseMultiRowEVADaoPO.Add`,但畫面型別仍是 `OneStep` 批次。

### 3.2 查詢 I

(本片無此類畫面)—— 同上。`OFDB706` / `OFDB707` / `OFDB752` / `OFDB757` 的畫面有查詢區塊,但那是批次執行前的挑選名單,不是獨立的 I 型畫面。

### 3.3 批次 B(35 支)

七個必查欄位一次列完。**「在 csproj」欄全部是 ✓ —— 逐支比對三個專案的六個 `.csproj`,35 支的六層檔案沒有一個漏編譯。**

| 代號 | 中文名(推測,來源=Designer 標籤) | 六層 | 觸發方式 | Remoting | 交易邊界 | 重跑安全 | 失敗處理 | 出口 | 在 csproj |
|---|---|---|---|---|---|---|---|---|---|
| `OFDB691` | 員工及員工關係人交易審核 | 齊 | 人工 OneStep | 無 | `OracleDao` 內單交易 | 無保護 | catch 轉訊息 | 寫 6 張交易表 + 寄 3 封信 | ✓ |
| `OFDB693` | 基金設定挑選 | 齊(掃描器誤判缺 3 層) | 人工 OneStep | 無 | **雙交易** `db` + `dbPTPF` | 無保護 | catch 轉訊息 | `INSERT OFD688A` | ✓ |
| `OFDB701` | 核印送件 | 齊 | 人工 OneStep | 無 | **雙交易** `dbTA` + `dbPTPF` | **無保護,每按一次多一批** | catch 轉訊息 | 媒體檔 `1201` + `OFD703/704/706` + Crystal 報表 | ✓ |
| `OFDB702` | 核印回報收檔 | 齊 | 人工 OneStep | 無 | 單交易 `dbTA` | 靠 SP 內部 | catch 轉訊息(含死碼 `SqlException`) | SP 回寫 `OFD701` + `SEALTMP` | ✓ |
| `OFDB703` | 扣款送件 | 齊 | 人工 OneStep | 無 | **雙交易** | `HasExecute` 擋重出 | catch 轉訊息 | 媒體檔 `1201` + `OFD703/704`(`OFD705` 那段已註解)+ Crystal 報表 | ✓ |
| `OFDB704` | 扣款回覆收檔 | 齊 | 人工 OneStep | 無 | **完全沒有交易** | 無保護 | 無 catch(只有 Ctl 有) | `ImportFileEngine` 寫 temp | ✓ |
| `OFDB705` | 核印補送件 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `1201` + SP `_Process_5` | ✓ |
| `OFDB706` | 核印狀態人工調整 | 齊 | 人工 OneStep | 無 | 單交易(**`dbTA` 為 null**) | 無保護 | catch 轉訊息 | SP `s_SealProof_ChangeStatus` | ✓ |
| `OFDB707` | 核印退件 | 齊 | 人工 OneStep | 無 | 單交易 | 無保護 | catch 轉訊息(含死碼 `SqlException`) | SP `s_TA_SealProof_ReturnProcess` | ✓ |
| `OFDB715` | 集保上線日期設定 | 齊 | 人工 OneStep | 無 | 單交易 | SP 內部 | catch 轉訊息 | SP `s_TA_OFDB715_Excute` | ✓ |
| `OFDB716` | 集保 SIN/BOK/699S 轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | `CheckCTL017` 擋重出 | catch 轉訊息 | 三個媒體檔 `Z1` + `CTL017` | ✓ |
| `OFDB717` | 集保 FUY/FUS2/STF673S 轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 三個媒體檔 `Z1` + `CTL017` | ✓ |
| `OFDB718` | 集保加減項上傳回收 | 齊 | 人工 OneStep | 無 | 單交易 | **先查 `CTL017` 再刪** | catch **不 rollback** | `DELETE CTL017` + 三張表 `DEL_YN=Y` | ✓ |
| `OFDB719` | 集保回收檔匯入 | 齊 | 人工 OneStep | 無 | 單交易 | `IsExistsData` 擋重收 | catch 轉訊息 | `TRP810A` / `TRP810ATMP` | ✓ |
| `OFDB720` | 集保回收檔刪除 | 齊 | 人工 OneStep | 無 | 單交易 | 無保護 | catch 轉訊息 | `UPDATE TRP810A` | ✓ |
| `OFDB721` | 集保結餘上傳回收 | 齊 | 人工 OneStep | 無 | 單交易 | 無保護(**沒有 `718` 的前置檢查**) | catch 轉訊息 | `DELETE CTL017` + 五張表 `DEL_YN=Y` + 重設 `OFD081A` | ✓ |
| `OFDB722` | 集保淨值上傳 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `Z1` | ✓ |
| `OFDB731` | 結匯申報收檔匯入 | 齊 | 人工 OneStep | 無 | 單交易(**`dbTA` 為 null**) | 先 `DELETE OFD733` | catch 轉訊息 | `OFD733` + 兩個子畫面清單 | ✓ |
| `OFDB732` | 結匯申報轉檔 | 齊 | 人工 OneStep | 無 | 單交易(**null**) | 先刪 `OFD734` / `OFD736` | catch 轉訊息 | 加密檔案 + GZip + SP | ✓ |
| `OFDB733` | 結匯申報產檔 | 齊 | 人工 OneStep | 無 | 單交易(**null**) | SP 內部 | catch 轉訊息 | 加密檔案 + SP `s_OFDB733_Excute` | ✓ |
| `OFDB734` | 結匯明細轉出 | 齊 | 人工 OneStep | 無 | 單交易(**null**) | 先刪 `OFD736` | catch 轉訊息 | SP `s_OFDB734_Excute` + 轉檔 | ✓ |
| `OFDB751` | 下單 / 短線資料收檔 | 齊 | 人工 OneStep | 無 | **完全沒有交易** | 無保護 | 無 catch(只有 Ctl 有) | `ImportFileEngine` 媒體 `R` | ✓ |
| `OFDB752` | 申購 / 買回 / 轉申購轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `Z1` + `ORDP01DTL` | ✓ |
| `OFDB753` | 淨值轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `Z1` | ✓ |
| `OFDB755` | 收益分配轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `Z1` | ✓ |
| `OFDB756` | 結餘資料轉檔 | 齊 | 人工 OneStep | 無 | **雙交易** | 無保護 | catch 轉訊息 | 媒體檔 `Z1` + SP `s_TA_ORDP04_Get` | ✓ |
| `OFDB757` | 下單資料處理 | 齊 | 人工 OneStep | 無 | 單交易 | SP 內部 | catch 轉訊息 | SP `s_TA_OFDB757_Excute` | ✓ |
| `OFDB871` | CLB / FSA 申報資料產生 | 齊 | 人工 OneStep | 無 | 單交易 `dbProduct` | **先 DELETE 再 INSERT** | catch 轉訊息 | `OFD871` / `OFD872` | ✓ |
| `OFDB901` | FIS 授權檔產生 / 匯入 | 齊 | 人工 OneStep | 無 | EVA 基底管 | 匯入靠 `BATCH_ID='-'` 暫存 | 基底管 | `OFD708` + 用戶端寫 `.txt` | ✓ |
| `OFDB903` | 定期定額扣款作業 | 齊 | 人工 OneStep | 無 | 單交易 `dbProduct` | SP 內部先 DELETE | catch 轉訊息 | SP `S_OTA_OFDB903_EXE` → `OFD904/9041/TTP901` | ✓ |
| `OFDB911` | 期間計算 | 齊 | 人工 OneStep | 無 | 單交易 | SP 內部 | catch **訊息為空字串** | SP `s_TA_OFDB911_Exe` | ✓ |
| `OFDB912` | 月結計算 | 齊 | 人工 OneStep | 無 | 單交易 | SP 內部 | catch **訊息為空字串** | SP `s_TA_OFDB912_Exe` | ✓ |
| `OFDB913` | 業務員異動審核 | 齊 | 人工 OneStep | 無 | 單交易 | 無保護 | catch **連 log 都沒有** | `UPDATE` / `DELETE OFD913A_UPD` | ✓ |
| `OFDB921` | 年度 / 期別計算 | 齊 | 人工 OneStep | 無 | 單交易 | `BeforeExecuteCheck` 問過才重算 | catch **訊息為空 + NRE** | SP `S_TA_OFDB921_EXECUTE` | ✓ |
| `OFDB950` | 券商基金申購 / 買回報表 | 齊 | 人工 OneStep | 無 | **完全沒有交易** | 不寫 DB | Ctl catch 回空 VDB | **只有 Crystal 報表,不碰 DB** | ✓ |

### 3.4 報表 R

(本片無此類畫面)—— 但有兩支 B 會叫 Crystal:`OFDB701`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701RPS.cs`)與 `OFDB950`(`OFDB950RPS` / `RPS1` / `RPS2` / `RPS3` 四份)。這是 `architecture.md §6.5` 講的「命名鐵律的正式例外」在批次層的延伸:報表類別掛在 UI 專案裡,不走 `.Report` 專案。

## 4. 維護畫面(M)

**本片無 M。** 原因:指派範圍是 OFD 前綴的 B 批次第 4 片,35 支的型別碼全是 `B`(`architecture.md §2.1` 的三段結構:模組 `OFD` + 型別 `B` + 序號)。對應的 M 畫面(例如扣款帳號的 `BMSM001`、基金主檔的 `OFDM081`)不在本片。

## 5. 查詢畫面(I)

**本片無 I。** 原因同 §4。本片七支畫面(`OFDB702` `OFDB706` `OFDB707` `OFDB752` `OFDB757` `OFDB716` `OFDB717`)有「先查再挑再執行」的兩段式操作,但它們的 `formstyle` 仍然是 `OneStep`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:593`、`:623`),查詢只是執行前的挑選步驟。不過這些查詢條件裡有 **會把資料濾掉而不提示** 的寫法,對維護的意義跟 I 畫面一樣重要,集中列在附錄 E5。

## 6. 批次(B)與 WindowsService

```text
[圖] OFDB731 到 OFDB734 的結匯申報收檔、外部加密程式的檔案交換協定與轉出,以及這四支整組是 SQL Server 遺留這件事
圖中文字:① 收檔線:OFDB731 把銀行給的 txt 拆進 OFD733 / 使用者選 txt / SaveFile 存到伺服器 TagPath / ImportDataToVDB / 逐檔 StreamReader 拆欄 / ImportDatabBefDeleteFirst / 同年月先刪再插 / OFD733 / DECLARE_YM + DATA_SEQ / p0 錯誤清單 p1 成功清單 / 兩個子畫面 / ② 申報線:OFDB733 產申報檔,中途要把身分證字號送去外部程式加密 / OFDB733 選基金與申報日 / s_OFDB733_Excute / Ctl 寫 xxx_加密前.txt / Encoding.Default / 寫 參數設定.ini / 加密前/加密後/處理結果 三行 / 外部加密程式 / 無原始碼 靠檔案輪詢 / 讀 xxx_處理結果.txt / 找不到就當加密未完成 / ③ 加密完成才輪到轉出:OFDB732 出結匯檔、OFDB734 出結匯明細 / OFDB732 結匯日期 + 結匯銀行 / s_OFDB732_Query / _Excute / 刪 OFD734 與 OFD736 再重建 / 重跑安全靠這兩行 / GZip 壓縮再改副檔名 / File.Copy 後 File.Delete / OFDB734 結匯明細轉出 / s_OFDB734_Excute 刪 OFD736 / ④ 這四支的共同前提:整組是 SQL Server 語法,在 Oracle 上跑不起來 / BasicEVAPO / dbTA 宣告就是 null / SqlDbType 111 次 / OracleDbType 0 次 / dbo.f_FormatStringToTable / Oracle 沒有這個函式 / EXEC sp @x=@y / Oracle 不接受這種語法 / ISNULL GETDATE / 共 9 次 / ⑤ 但畫面與設定都還在 —— 按下去會拿到 NullReferenceException / App.config 四個 section / formstyle OneStep / PO.OFDB.csproj 有編譯 / 四支都在 / Ctl 還在 new 它們 / InitializeDataAccessPool / 結論:等同死碼 / 要用得先整組重寫
```

*圖:圖 5 結匯申報四支與外部加密程式。橘框=主要步驟;橘虛框=要留意的行為與證據;灰虛框=雖然還掛著但不代表會跑;黑框=無原始碼。第②列那個「參數設定.ini + 三個 txt」是本片唯一一組跟 repo 外程式的同步協定,而且沒有逾時、沒有重試、找不到檔就當作未完成。*

```text
[圖] 700 系列七支確實構成一條核印與扣款的流水線,而 715 到 722 八支其實是四對產出/回收的配對,751 到 757 只是代號相鄰
圖中文字:① 700 系列:真的是一條流水線,靠 OFD701 / OFD706 的狀態接力 / OFDB701 核印送件 / 寫 OFD704 OFD706 OFD703 / 匯出媒體檔 1201 / ExportFileEngine / 銀行核印 / 外部作業 / OFDB702 核印回報收檔 / ImportFileEngine 1201 / s_TA_SealProof_ReturnProcess / 回寫 OFD701 / ② 核印成功之後才輪到扣款:OFDB703 出扣款檔、OFDB704 收回覆 / OFDB703 扣款送件 / 寫 OFD704 OFD705 / HasExecute 擋重出 / 同批已產生就不給再產 / CheckALLOT_CLS / CTL012 未關帳就擋 / OFDB704 扣款回覆收檔 / 只有 PrepareExecute / ③ 三支尾巴:補送、人工改狀態、退件。共用同一組 SP 家族 / OFDB705 補送件 / s_TA_SealProof_Process_5 / OFDB706 人工改核印狀態 / 成功→失敗/核印中 / OFDB707 退件 / s_TA_SealProof_ReturnProcess / OFDB706 是 BasicEVAPO / dbTA 恆 null 跑不起來 / ④ 715~722:不是一條線,是「四對」加兩支獨立的 / OFDB716 產 SIN BOK 699S / SOURCE_ID 1 / OFDB721 回收上面三種 / DEL_YN=Y + 清 CTL017 / OFDB717 產 FUY FUS2 STF673S / SOURCE_ID 2 / OFDB718 回收上面三種 / DEL_YN=Y + 清 CTL017 / OFDB719 收集保回檔 / TRP810A + TRP810ATMP / OFDB720 刪回檔 / UPDATE TRP810A / OFDB715 集保上線日 / 只改 OFD081A 設定 / OFDB722 淨值上傳 / 獨立 讀 OFD302A / 751~757 六支彼此無關 / 只是代號相鄰
```

*圖:圖 4 連號系列的真實相依。橘框=有先後相依的節點;橘虛框=要留意(跑不起來、或看似成組其實無關);黑框=無原始碼的媒體引擎與 SP。第①②列的接力靠資料狀態而不是程式呼叫 —— 沒有任何一支 Process.Start 另一支,順序完全靠人記得。*

### 6.0 先看總表

35 支的執行入口與輸出一次看完。`WindowsService` 欄全部是「無」—— `Dev/ATLAS.OFDB/`、`Dev/ATLAS.OTAB/` 底下沒有 `WindowsService.*` 資料夾,`Dev/ATLAS.EC/Source/WindowsService/` 底下那三支(`OFDB600` / `OFDB609` / `OFDB680`)都是 `ofdb.md` 的範圍。

| 群 | 畫面 | 執行入口(PO 方法) | 主要輸出 |
|---|---|---|---|
| A | `OFDB701` | `ExecuteNonQuery` → `ExportDataList` | 媒體檔 + `OFD703/704/706` |
| A | `OFDB702` | `ExecuteNonQuery` / `PrepareExecute` / `InsertSEALTMP` | SP 回寫 + `SEALTMP` |
| A | `OFDB703` | `ExecuteNonQuery` → `ExportDataList` | 媒體檔 + `OFD703/704` |
| A | `OFDB704` | **只有 `PrepareExecute`** | `ImportFileEngine` temp |
| A | `OFDB705` | `ExecuteNonQuery` | 媒體檔 + SP |
| A | `OFDB706` | `Execute` | SP `s_SealProof_ChangeStatus` |
| A | `OFDB707` | `ExecuteNonQuery` | SP `s_TA_SealProof_ReturnProcess` |
| B | `OFDB715` | `Execute` | SP `s_TA_OFDB715_Excute` |
| B | `OFDB716` `OFDB717` `OFDB722` | `ExecuteNonQuery` → `ExportDataList` | 媒體檔 `Z1` |
| B | `OFDB718` `OFDB720` `OFDB721` | `Execute` | 匿名 PL/SQL 區塊 |
| B | `OFDB719` | `Execute` / `PrepareExecute` | `TRP810A` |
| C | `OFDB731` | `ImportDataToVDB` / `DeleteData` | `OFD733` |
| C | `OFDB732` `OFDB733` `OFDB734` | `Execute` + Ctl 的檔案交換 | 加密檔 + SP |
| D | `OFDB751` | **只有 `PrepareExecute`** | `ImportFileEngine` temp |
| D | `OFDB752` `OFDB753` `OFDB755` `OFDB756` | `ExecuteNonQuery` → `ExportDataList` | 媒體檔 `Z1` |
| D | `OFDB757` | `Execute` | SP |
| E | `OFDB871` | `Execute` | `OFD871` / `OFD872` |
| E | `OFDB911` `OFDB912` `OFDB921` | `Execute` | SP |
| E | `OFDB913` | `Execute` | `UPDATE` / `DELETE` |
| F | `OFDB691` | `Execute` | 六張交易表 + 三封信 |
| F | `OFDB693` | `Execute` | `INSERT OFD688A` |
| F | `OFDB901` | `Add`(EVA 基底) | `OFD708` |
| F | `OFDB903` | `Execute` | SP → `OFD904` / `OFD9041` / `TTP901` |
| F | `OFDB950` | `Execute`(**空的**) | Crystal 報表 |

### 6.1 `700` 系列七支 —— 本篇第一個必答題

> **結論:是一條流水線,但接力靠資料狀態而不是程式呼叫。** 沒有任何一支 `Process.Start` 另一支(全片 grep `Process.Start`:0 命中),也沒有 `.bat` 把它們串起來。順序完全靠人記得,以及靠下一支查不到資料時自然做不下去。

#### 6.1.1 執行順序與相依證據

| 步 | 畫面 | 讀誰產生的 | 寫給誰 | 相依證據 |
|---|---|---|---|---|
| 1 | `OFDB701` 核印送件 | `BMS005A` / `RSP006A`(別的模組) | `OFD706`(這批送了誰)、`OFD704`(批次)、`OFD703`(Log)、媒體檔 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:904-916`、`:864`、`:1010` |
| 2 | `OFDB702` 核印回報收檔 | **`OFD706` 的批號 + `OFD701`** | SP 回寫 `OFD701.SEAL_STATUS` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:413-414`(`WHERE OFD706.CHG_UPD_DTTM ...`)、`:959` |
| 3 | `OFDB703` 扣款送件 | **`OFD701` 且核印成功者** | `OFD703` / `OFD704` + 媒體檔(`OFD705` 那段已註解) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1015`(`ExportDataList`)、`:1254`、`:1090` |
| 4 | `OFDB704` 扣款回覆收檔 | **`OFDB703` 產出的媒體檔的回覆檔** | `ImportFileEngine` temp | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:56`(媒體 `1201`、`OFD700.PARA_ID='DDCT_R'`) |
| 旁 | `OFDB705` 補送件 | `OFD706`(同一批) | 媒體檔 + SP `_Process_5` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB705_PO.cs:529` |
| 旁 | `OFDB706` 人工改狀態 | `OFD701` | SP `s_SealProof_ChangeStatus` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:278` |
| 旁 | `OFDB707` 退件 | `OFD706` + `OFD701` | SP `s_TA_SealProof_ReturnProcess`(**與 `OFDB702` 同一支**) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:286`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:959` |

最硬的一條證據是 **SP 家族共用**:`s_TA_SealProof_Process_1`(`OFDB701`)、`s_TA_SealProof_Process_5`(`OFDB705`)、`s_TA_SealProof_ReturnProcess`(`OFDB702` 與 `OFDB707` 共用)、`s_TA_ReSeal_Process` / `s_TA_CancelReSeal_Process`(`OFDB702` 的重核印分支,`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:1246`、`:1871`)、`s_SealProof_ChangeStatus`(`OFDB706`)。**六支畫面共用同一組 SP 前綴,而且 `Process_1` / `Process_5` 的數字就是 `OFD703.JOB_ID`。**

#### 6.1.2 `OFDB701` 核印送件 —— 本群最重的一支(1,532 行 PO)

**觸發**:人工。`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:587-592`,`formstyle="OneStep"`。

**參數**(從 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:846-853` 反推):

| 參數 | 來源 | 用途 |
|---|---|---|
| `striSEAL_TYPE` | 畫面「核印方式」 | `1` = 一般 → 不產檔;其他 → 產媒體檔 |
| `striAGENT_BANK` | 畫面「代理(扣款)銀行」 | 送件對象 |
| `striISAGENTBANK` | 畫面「代扣款行設定」 | 指定行 / 代理行 / 非代理行 |
| `striBATCH_ID` | 空的話由 `SerialNo.GetSEAL_Batch_ID` 編 | 送件批號 |
| `striJOB_ID` | 畫面「執行功能」 | `1` = 核印送件(寫 `OFD706`);`5` = 補送 |
| `striMEDIA_NO` | 查 `OFD700` | 媒體格式代號 |

**執行主體**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:828-1180`):

1. `:832` `dbTA.BeginTransaction()`;`:836` 另開 `dbPTPF.BeginTransaction()` —— **兩個交易,commit 時不是原子的**。

2. `:864-897` 逐筆 `INSERT INTO OFD704`。

3. `:902-918` `JOB_ID == "1"` 才寫 `OFD706`,而且只寫 `ISCHECK` 勾選的列。

4. `:930-1013` 組一筆 `OFD703` Log,四眼欄位全部自填(§2.4)。

5. `:1021` **分岔**:`SEAL_TYPE != "1"` 或(`= "1"` 且扣款行是 `'700'` 郵局)→ 產媒體檔;否則走 SP `s_TA_SealProof_Process_1`。

6. `:1026-1033` `ExportFileEngine(dbTA, tran, "1201", strMEDIA_NO)` —— **媒體引擎吃 C# 的交易**,所以檔案產出與 DB 寫入在同一個交易裡。

7. `:1054-1079` 依 `JOB_ID` 與匯出筆數決定 commit / rollback。

8. `:1096-1152` SP 分支。

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 畫面 | `DoValidate` 必填檢查 | 缺欄位 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.cs:810` |
| 畫面 | `VerirfyAccount` 檢查帳號是否有送核後的異動 | 有異動 | 詢問 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1329` |
| 畫面 | `CheckApprove` | 未覆核 | 詢問 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1234` |
| 執行 | `ExportFileEng.GetCheckErrorDataSet` 有錯誤列 | 有 | 過濾(無提示)—— **不產檔但也不報錯,直接往下走** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1029-1033` |
| 執行 | `ExportFileEng.IsSuccess == false` | 是 | 阻擋 + rollback | `:1083-1089` |
| 執行 | 匯出 0 筆且 `JOB_ID != "5"` | 是 | **記錄不擋** —— rollback 但回報 `true`「無檔案匯出」 | `:1059-1065` |
| 執行 | SP 回傳 `IsSuccess` / `MSG` | **不論回什麼** | **無** —— 讀出來就丟掉,一律 commit 報成功 | `:1128-1152` |

> **`:1128-1152` 是本支最嚴重的一條。** 程式把 SP 的 OUT 參數 `IsSuccess` 與 `MSG` 讀進區域變數,然後 **從此再也沒用過它們**,直接 `tran.Commit()` 並 `AddResultRow(true, 0, "執行成功,送件批號…")`。也就是說 **SP 內部判定失敗時,畫面照樣說成功,而且資料已經 commit**。與 `ofdb.md` 附錄 E1「一律回報成功」同型,但本支更明確:失敗訊號有拿到,只是沒接。

**`OFD704` 的 INSERT 是壞的**(`:864-894`):欄位清單 15 個、`VALUES` 卻有 16 個佔位符(多一個 `:dataid`),而且 `AddInParameter` 把 `VERIFYDATE` 綁了兩次(`:890`、`:892`,第二次本來應該是 `APPROVEDATE`),`REJECTID` / `REJECTDATE` 被打成 `REJCETID` / `REJCETDATE`(`:893-894`)。Oracle 會在 `ExecuteNonQuery` 直接丟 `ORA-00913: too many values`。詳見附錄 E3.1。

#### 6.1.3 `OFDB702` 核印回報收檔 —— 已見 `ofdb.md`,本片補充四件事

`ofdb.md §8.1`、`§8.2`、`附錄 D.1`、`附錄 E5.3` 已經提到 `OFDB702`,但只寫到「它也讀 `CHG_UPD_DTTM`」與「`OFDB702_PO.cs:238/242/276` 用 `TO_CHAR(SYSDATE,…) CHG_UPD_DTTM` 造同名輸出欄位而不是 UPDATE」。**本片補充以下四件 `ofdb.md` 沒寫的:**

**補充一:它的執行功能只認得兩個值,其餘值會靜默 commit。** `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:945` 是 `if (exec_opt == "0" || exec_opt == "3")`;整個 `try` 裡再也沒有別的 `if`。若 `ExecOption` 是其他值(畫面上還有重核印 / 取消重核印分支,見 `:1246`、`:1871`),流程直接落到 `:2276` `tran.Commit()` 與 `:2279` `AddResultRow(true, 0, "")` —— **什麼都沒做,回報成功**。

**補充二:`catch (SqlException)` 是死碼。** `:2281` 攔 `System.Data.SqlClient.SqlException`,但這支 PO 標了 `[PODbType(DbServerType.Oracle)]`(`:40`)且 `dbTA = new Database("TA", DbServerType.Oracle)`(`:43`),Oracle 端丟的是 `OracleException`。這個 catch 永遠不會進去。同型的還有 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:335`。

**補充三:`s_TA_SealProof_ReturnProcess` 的 OUT 參數在這支有接,在 `OFDB707` 也有接 —— 兩支共用同一支 SP。** `:975` 宣告 `vstrTempMsg`,`:981-988` 只要不是 NULL 就 rollback 並回報失敗。這比 `OFDB701` 對 `s_TA_SealProof_Process_1` 的處理正確。**同一個專案裡對 OUT 參數的處理方式不一致**,是本片的系統性問題(附錄 E1.3)。

**補充四:`OFDB702.designer.cs` 有 6,319 行,其中約 4,800 行跟這支畫面無關。** `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB702.designer.cs:2985-5495` 是一整組基金主檔的頁籤:保本型基金碼、存續期間碼、大額贖回金額、收益分配設定、手續費率下限(內控用)、郵匯費設定…… 這些控件確實被 `Controls.Add` 掛上去(`:2985`、`:4682`、`:5128`、`:5358`、`:5495`),只是畫面上被 `ultraTabPageControl` 藏著。對照 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.designer.cs` 只有 969 行。**這是從基金主檔維護畫面整份複製過來沒清乾淨的結果**(附錄 E13.1)。

#### 6.1.4 四支共用的「匯入檔案格式檢核」是反的

這是 §0.2 第六件事的細節。四支的 `PrepareExecute` 完全一樣:

| 畫面 | 媒體類型 | 錨點 |
|---|---|---|
| `OFDB702` | `1201` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2331-2350` |
| `OFDB704` | `1201` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:56-73` |
| `OFDB719` | `Z1` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:115-160` |
| `OFDB751` | `R` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:60-77` |

三件事同時錯:

1. **`bl` 的語意跟名字相反。** `IsImportRecFormatError` 回 `true` 代表「格式有錯」,程式卻用它當「可以匯入」的旗標。

2. **註解與程式相反。** 註解寫「格式正確 寫入 temp 檔」。

3. **回傳值把錯誤當成功。** `AddResultRow(bl, ...)` 的第一個參數是 `ReturnCode`;`bl = true`(有格式錯誤)會被上層當成執行成功。

`OFDB719` 稍微好一點:它在 `:141-161` 多做了 `IsExistsData` 與 `IsFundColse` 兩層檢查,兩層任一成立就改回 `false`。但格式檢核那一層仍然是反的。

> **無法從呼叫端判斷的部分(標「假設」)**:`ImportFileEngine` 沒有原始碼(`architecture.md 附錄 C`),所以 `IsImportRecFormatError` 的回傳語意是從方法名推的。**如果它實際上回 `false` 代表有錯**,那這四支就是對的、註解也是對的。依據方法名 `IsXxxError` 的通用慣例以及 `ErrMsg` 是 `ref` 輸出參數這兩點,本文採「`true` = 有錯」的解讀,但這一條需要跑起來才能定案。

#### 6.1.5 `OFDB703` 扣款送件的兩道檢核,一道是 fail-open

**`HasExecute`**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1377`):判斷同一批扣款檔資料是否已經產生過,在 `:1254` 被 `ExportDataList` 呼叫。這是本群唯一一道真正的重跑保護。但它組 SQL 的方式有兩個問題:

- `:1406` `" AND SUB_BANK_CODE IN (SELECT WORDS FROM TABLE(F_TA_SPLITWORDS('" + strSubBank + "')))"` —— 銀行代碼串接進 SQL。

- `:1411` `" AND SUB_BANK_CODE = " + strAgentBank`、`:1416` `" AND SUB_BANK_CODE <> " + strAgentBank` —— **連引號都沒有**。若 `strAgentBank` 不是純數字會直接語法錯。而 `:1416` 的 `<>` 遇到 `SUB_BANK_CODE` 為 NULL 時結果是 UNKNOWN,那些列會被**靜默濾掉**(Oracle 三值邏輯,本缺陷型錄的頭號項目)。

**`CheckALLOT_CLS`**(`:1551`):查 `CTL012` 有沒有當日未關帳的傳真委扣資料,有的話要擋。呼叫端在 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.cs:968-972`,**只有 `ReturnCode == true` 才加錯誤**。而 PO 的 `catch` 在 `:1589-1590` 把 `ReturnCode` 設成 `false`。

> **後果:`CTL012` 查詢一旦丟例外(表被鎖、欄位改名、連線斷),這道關帳檢核就整個消失,扣款送件照跑。** 這是缺陷型錄「`catch` 吞例外 → DB 出錯等於通過」的標準形。嚴重度高(附錄 E11.1)。

順帶一提:`:1583` 的訊息寫死了另一支畫面的代號「請先執行『傳真委扣－交易截止設定作業(`OFDB301`)』」。`OFDB301` 不在本片。

#### 6.1.5a `OFDB701` 與 `OFDB703` 是複製貼上的一對,只有一邊壞掉

兩支的 `ExportDataList` 是同一份樣板改出來的 —— 開兩個交易、取批號、寫 `OFD704`、寫 `OFD703` Log、叫 `ExportFileEngine("1201", …)`、依匯出筆數 commit / rollback,連變數名都一樣。**但四個地方不一致,而且每一處都是 `OFDB701` 比較差:**

| 差異 | `OFDB701` | `OFDB703` |
|---|---|---|
| `INSERT INTO OFD704` 的欄位 / 值個數 | **15 欄 vs 16 值**(多一個 `:dataid`),Oracle 直接 `ORA-00913`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:864-872`) | **15 欄 vs 15 值,正確**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1051-1059`) |
| 參數綁定 | `VERIFYDATE` 綁兩次、`APPROVEDATE` 沒綁、`REJCETID` / `REJCETDATE` 拼錯(`:889-894`) | 15 個全部正確,拼法也對(`:1069-1083`) |
| 匯出 0 筆的回報 | `AddResultRow(**true**, 0, "無檔案匯出")`(`:1062`) | `AddResultRow(**false**, 0, "無檔案匯出")`(`:1218`) |
| 寫 `OFD704` 的前提 | 無條件逐列寫 | 只有 `striISAGENTBANK == "9"`(全部銀行)時才寫(`:1062`) |

> **這是缺陷型錄「成對批次只改一邊」的最乾淨案例**:同一段 SQL 在 `OFDB703` 是對的,在 `OFDB701` 是壞的。合理的解讀(**假設**)是 `OFDB703` 後改、`OFDB701` 沒跟上;修 `OFDB701` 時可以直接照抄 `OFDB703` 那 15 行。

另外兩支共用一個真正的空殼:`OFDB703_PO.cs:1090-1095` 的 `#region OFD705` 裡,`INSERT INTO OFD705 (BATCH_ID, FUND_ID)` 整段被註解。**全片沒有任何一支寫 `OFD705`**,但它在 `OFDB703` 的取數 SQL 裡還被讀。

#### 6.1.6 `OFDB706` 是這群裡唯一跑不起來的

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:14` 繼承 `BasicEVAPO`,`:272` 直接 `dbTA.CreateConnection()`。依 `architecture.md §3.1.1`,`dbTA` 恆為 null。而且 `:296-300` 用 `@SOURCE_CD` / `SqlDbType.NVarChar` 呼叫 SP,`:113` 與 `:146` 的 SQL 用 `dbo.f_Nvl(...)` 與 `CHG_UPD_DTTM = '1900/1/1'`。

**`'1900/1/1'` 是本片對 `ofdb.md 附錄 E5.3` 的補強**:那邊列了三種「未生效」哨兵寫法(`SUBSTR(NVL(TRIM(x),'19000101'),1,8) = '19000101'`、`NVL(x,' ') = ' '`、`x = '1900/01/01'`),本片在 `OFDB706` 找到 **第四種:`x = '1900/1/1'`(單位數月日)**。四種寫法對同一份資料會給出不同答案。

`OFDB706` 的畫面標籤是「成功→失敗/核印中」「全部核印失敗」「全部核印中」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB706.Designer.cs:330`、`:623`、`:633`),所以它的業務意義是 **人工把已回報成功的核印結果改回失敗或核印中**。這是整條流水線裡權限最大的一支 —— 而它沒有任何權限檢查,也沒有寫 log 表。

### 6.2 `OFDB701` / `OFDB702` 與 `ofdb.md` 的分工

| 主題 | `ofdb.md` 寫了 | 本片補充 |
|---|---|---|
| `CHG_UPD_DTTM` 只被讀不被寫 | `ofdb.md §8.1` 全庫掃描結論 | 無補充,直接引用 |
| `OFDB702_PO.cs:238/242/276` 是造同名輸出欄位 | `ofdb.md §8.1` | 無補充 |
| `RSP013A` 也有一套 CHG 機制 | `ofdb.md §8.2` | 本片 `OFDB701_PO.cs:236`、`OFDB705_PO.cs:135`、`OFDB707_PO.cs:140` 也在用同一組哨兵 |
| 三種哨兵寫法 | `ofdb.md 附錄 E5.3` | **補到四種**(`OFDB706_PO.cs:113`、`:146` 的 `'1900/1/1'`) |
| `OFDB701` / `OFDB702` 的業務內容 | 明確標示「不在本篇」 | **本片 §6.1.2 / §6.1.3 首次完整攤開** |

### 6.3 `731`–`734` 結匯申報四支 —— 本片第二個深寫重點

> **一句話:這是一條完整的三段流程(收檔 → 加密 → 產檔轉出),掛著一個 repo 外的加密程式,而且整組是 SQL Server 語法,在 Oracle 上一行都跑不動。**

#### 6.3.1 四支的分工

| 畫面 | 中文名(Designer 標籤) | 做什麼 | 主要錨點 |
|---|---|---|---|
| `OFDB731` | 「執行功能 / 匯入 / 刪除 / 年月 / 基金代碼」,子畫面「結匯申報收檔錯誤清單」「結匯申報收檔匯入成功清單」 | 把銀行給的 `.txt` 拆進 `OFD733` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB731.designer.cs:307`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB731p0.designer.cs:162`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB731p1.designer.cs:162` |
| `OFDB732` | 「結匯日期 / 結匯銀行 / 基金明細資料 / 轉出明細資料 / 收檔明細資料 / 轉檔路徑」 | 產結匯檔,含 GZip 壓縮 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB732.designer.cs:301` |
| `OFDB733` | 「申報日期 / 基金明細資料 / 轉檔路徑」,子畫面「加密處理未完成」 | 產申報檔 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB733.designer.cs:334`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB733p1.designer.cs:142` |
| `OFDB734` | 「結匯日期(起)/(迄)、結匯銀行、轉出明細資料」 | 產結匯明細轉出 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB734.designer.cs:226` |

#### 6.3.2 `OFDB731` 收檔:檔案先上伺服器,再逐檔拆解

1. `SaveFile`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:495-523`)把使用者選的檔案 byte 陣列寫到伺服器端 `TagPath`,檔名是 `mID + ".txt"`。

2. `ImportDataToVDB`(`:532`)用 `DirectoryInfo.GetFiles("*.txt")` 列出目錄下**所有** `.txt`,逐檔 `StreamReader` 讀。

3. `ImportDatabBefDeleteFirst`(`:749`)判斷同一年月是否已匯入過,是的話先刪。

4. `DeleteData`(`:423`)是「刪除」功能:`DELETE FROM OFD733 WHERE DECLARE_YM = @YM AND DECLARE_ID IN (SELECT * FROM dbo.f_FormatStringToTable(@ID))`。

**三個問題:**

- `:536-546` 取檔案清單時 **不篩本次上傳的檔名**,而是把 `TagPath` 目錄下所有 `.txt` 都吃進來。多人同時操作或前一次留下殘檔,資料就混進來了。而且 `:540` 與 `:546` 各呼叫一次 `mDir.GetFiles("*.txt")`,兩次之間目錄若變動會越界。

- `:446-448` `"AND UNI_CD IN (SELECT UNI_CD FROM OFD0813 WHERE FUND_ID='" + mFundId + "')"` —— 基金代碼串接進 SQL。

- `:514-517` `catch { return false; }` —— **完全空的 catch,連例外物件都不接**。磁碟滿、權限不足、路徑太長都會被吞成「存檔失敗」而沒有任何線索。

#### 6.3.3 `OFDB732` / `OFDB733` 與外部加密程式的交換協定

這是本片唯一一組跟 repo 外程式的同步機制,全部靠檔案。協定在 Ctl 層(不在 PO):

| 步 | 動作 | 錨點 |
|---|---|---|
| 0 | 檢查交換目錄與旗標檔存在;不存在就整支不做事 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:84-89`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:46-51` |
| 1 | 寫 `<檔名>_加密前.txt` | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:154`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:373` |
| 2 | 寫 `參數設定.ini`,三行:`加密前檔案=` / `加密後檔案=` / `處理結果=` | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:439-443`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:512-516` |
| 3 | 外部程式讀 ini、加密、寫 `_加密後.txt` 與 `_處理結果.txt`(**無原始碼**) | — |
| 4 | 讀 `_處理結果.txt`;讀不到就當「加密處理未完成」 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:198-203`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:401-406` |
| 5 | 讀 `_加密後.txt`;不存在就 **退回讀 `_加密前.txt`** | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:225-231`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:429-434` |
| 6 | 搬走 / 刪除三個 txt | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:469-479`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:551-556` |

**第 5 步是最會咬人的一行。** `if (File.Exists(加密後)) 用加密後; else 用加密前;` —— 加密程式沒跑或跑失敗時,**未加密的身分證字號會直接進申報檔**。程式不會報錯,因為第 4 步只在找不到「處理結果」時才提示。兩支都是這樣寫(附錄 E1.2)。

其他:

- `Encoding.Default` 用在寫 ini 與讀處理結果(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:512`、`:406`)—— 隨作業系統語系變,不是固定編碼。

- `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:398-423`:用 `GZipStream` 壓成 `.zip`,再 `File.Copy(strFileName + ".zip", strFileName, true)` 蓋回原檔名、`File.Delete` 刪掉 `.zip`。**副檔名說謊**:收到的人看到的是原副檔名,內容卻是 gzip。

- `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:253`、`:278` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:273`:`DELETE FROM OFD736` / `DELETE FROM OFD734` —— 這是它們的重跑保護,寫在 `Execute` 開頭。

#### 6.3.4 這四支整組跑不起來的完整證據

| # | 事實 | 錨點 |
|---|---|---|
| 1 | 四支的 PO 全部 `: BasicEVAPO` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:22`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:19`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:15`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:17` |
| 2 | 四支都直接 `dbTA.CreateConnection()`,而 `dbTA` 恆為 null | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:430`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:29`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:40`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:42`;`architecture.md §3.1.1` |
| 3 | `SqlDbType` 111 次 / `OracleDbType` 0 次 | 逐檔統計 |
| 4 | `dbo.` 前綴 14 次、`ISNULL` 8 次、`GETDATE()` 1 次 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:436`、`:558`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs` |
| 5 | `EXEC sp @x=@y` 呼叫語法 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:49` |

**但畫面與設定都還在**:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:678-701` 四個 section 俱全,`PO.OFDB.csproj` 有編譯,`Ctl` 還在 `new` 它們。**結論(假設,依據上述五條交叉):整組是 SQL Server 時代的遺留,現況等同死碼,要用得先整組重寫。** 與 `ofdb.md §0.2` 對 `OFDB001` / `OFDB005` / `OFDB011` / `OFDB161` 的結論同型。

### 6.4 `715`–`722` 八支 —— 本篇第一個必答題的下半

> **結論:不是一條流水線,是「三對 + 兩支獨立」。** 三對的配對關係靠 `CTL017.SOURCE_ID` 與媒體代號確定(§2.3),兩支獨立的跟任何人都沒有資料相依。

#### 6.4.1 配對關係

| 配對 | 產出 | 回收 | 共同關卡 |
|---|---|---|---|
| 第一對 | `OFDB716`(SIN `TRP805` / BOK `TRP806` / 699S `TRP803`) | `OFDB721` | `CTL017.SOURCE_ID = '1'` |
| 第二對 | `OFDB717`(FUY `TRP801` / FUS2 `TRP802` / STF673S `TRP804`) | `OFDB718` | `CTL017.SOURCE_ID = '2'` |
| 第三對 | `OFDB719`(收集保回檔 → `TRP810A`) | `OFDB720`(`UPDATE TRP810A`) | `TRP810A` |
| 獨立 | `OFDB715` | — | 只改 `OFD081A` 的集保上線日 |
| 獨立 | `OFDB722` | — | 淨值上傳,讀 `OFD302A` / `OFD303A` |

#### 6.4.2 成對批次只改一邊 —— 兩對之間的三個不對稱

這正是缺陷型錄「成對批次只改一邊」的具體案例:

| 差異 | `OFDB718`(回收 `SOURCE_ID='2'`) | `OFDB721`(回收 `SOURCE_ID='1'`) |
|---|---|---|
| 執行前檢查 | **有**:先查 `CTL017` 的 `MAX(BAL_DATE)` 是否還等於畫面帶的值,不等就擋「上次上傳結餘基準日有異動,請重新查詢再執行」(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:71-88`) | **沒有** |
| 重設基金設定 | **沒有** | **有**:`UPDATE OFD081A SET TDCC_START_BAL_DATE = ' ' WHERE FUND_ID = :FUND_ID`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:126-128`) |
| catch 有沒有 rollback | **沒有**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:155-159`) | **有**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:155-160`) |

`OFDB721` 那條 `UPDATE OFD081A` 的 `WHERE` 只有 `FUND_ID`,沒有 `TRANS_DATE` —— **回收任何一批都會把該基金的集保起算結餘日整個清成空白**,即使還有其他批次有效。無鍵 UPDATE 的變形(附錄 E6.1)。

#### 6.4.3 兩支的 `ExecuteNonQuery` 回傳值被常數蓋掉

`OFDB718` 與 `OFDB721` 的迴圈裡:

```
k = Convert.ToInt32(dbTA.ExecuteNonQuery(cmd, tran));
k = 1;
if (k > 0) { j = j + k; }
```

錨點:`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:134-139`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:134-139`。 **實際影響數被 `1` 蓋掉。** 後面 `:143-152` 用 `j > 0` 決定 commit 還是 rollback —— 只要畫面上勾了至少一列,`j` 就一定大於 0,**即使 PL/SQL 區塊一列都沒更新到也照樣 commit 並回報「成功,N 筆」**。這是缺陷型錄「`ExecuteNonQuery` 回傳值被常數蓋掉」的兩份複本。

(補充:Oracle 對匿名 PL/SQL 區塊的 `ExecuteNonQuery` 本來就回 `-1`,所以就算不蓋掉也不能直接當筆數用。正確做法是在區塊裡用 `SQL%ROWCOUNT` 累加到 OUT 參數。這條標「假設」—— 沒跑過,依據是 ODP.NET 的通則。)

#### 6.4.4 `OFDB716` / `OFDB717`:三段匯出,前兩段失敗不會停

兩支都是「連產三個媒體檔」。問題在失敗處理不一致:

| 段 | `OFDB716` | `OFDB717` |
|---|---|---|
| 第一段 0 筆 | `AddResultRow(false, …, "SIN無檔案匯出")` 但 **不 return、不 rollback**,繼續跑第二段(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:182-186`) | 同樣不 return,而且 rollback 那兩行被註解掉(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:353-358`) |
| 第二段 0 筆 | 同上(`:230-234`) | 同上(`:411-412` 被註解) |
| 第三段 0 筆 | `AddResultRow(false, …, "699S無檔案匯出")` 然後 **`tran.Commit()`**(`:280-286`) | `AddResultRow(false, …, "STF673S無檔案匯出")` 然後 **`tran.Commit()`**(`:468-476`) |
| 第三段有檔 | `Result.Clear()` 再 `AddResultRow(true, …)` —— **把前兩段的失敗訊息蓋掉**(`:287-294`) | `:479-483` 明文寫「若前面是 false 就改成 true」 |

> **後果:第一段與第二段的媒體檔沒產出來,操作員只會看到最後一段的結果。** `OFDB717` 更直白 —— `:479-483` 是刻意把前面的失敗改寫成成功。這是本片「一律回報成功」的第二種形態:不是沒判斷,是判斷完把結果覆蓋掉。

另外 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:127` `DbConnection cnptpf = dbTA.CreateConnection();` —— 變數名說是 PTPF,卻從 `dbTA` 建,而且**建完之後整個方法再也沒用到它**,也沒有 `Dispose`。每執行一次洩一條連線。

#### 6.4.5 `OFDB715` 與 `OFDB722`:兩支獨立的

`OFDB715`「集保上線日期」:兩道檢核 —— `CheckIssueDate`(集保上線日不可小於最大憑證日,`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:133`)與 `CheckIsFundClose`(基金是否已過帳,`:185`,走 table function `f_TA_IsFundClose(:FUND_ID, TO_DATE(:ISSUE_DATE,'yyyymmdd'), '2', '0')`)。後兩個位置參數 `'2'` / `'0'` 是寫死的魔術值,沒有註解說明(附錄 E9.1)。

`OFDB722`「集保淨值上傳」:讀 `OFD302A` / `OFD303A` / `OFD0811A`,產媒體 `Z1`。它的 `Execute` 裡有 **一大段被完整註解掉的 rollback / commit 邏輯**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB722_PO.cs:320-337`、`:438-486`),現行只剩 `:377-395` 那一組。被註解的那段裡還有第二次 `ExportFileEngine(dbTA, tran, "Z", ...)`(媒體 `Z` 不是 `Z1`,`:290`、`:407`)。**這支曾經產兩種媒體,現在只產一種,而外殼還在。**

### 6.5 `751`–`757` 六支 —— 只是代號相鄰,彼此無關

逐支查過讀寫的表與呼叫的 SP,**沒有任何一對之間有資料相依**:

| 畫面 | 中文名(Designer) | 讀 | 寫 / 輸出 | 與其他五支的關係 |
|---|---|---|---|---|
| `OFDB751` | 「資料種類 / 下單資料 / 短線資料 / 轉檔路徑」 | — | `ImportFileEngine("TA","R",…)` | 無 |
| `OFDB752` | 「轉申購 / 買回 / 單筆申購 / 傳輸平台 / 檔案格式」 | `OFD220A` `OFD221A` `OFD251A`–`254A` `OFD068A` `OFD070A` `FSK003` | `ORDP01DTL` + 媒體 `Z1` | 無 |
| `OFDB753` | 「資料日期 / 存檔路徑 /(小於等於此日期的最新淨值日期)」 | `OFD302A` `OFD081V` | 媒體 `Z1` | 無 |
| `OFDB755` | 「分配基準日 / 期別 / 年度 / 發放日期 / 再申購日期」 | `OFD281A` `OFD283A` `OFD221A` `OFD751` | 媒體 `Z1` | 無 |
| `OFDB756` | 「結餘日期 / 戶號 / 受益人ID / 存檔路徑」 | SP `s_TA_ORDP04_Get`、`s_ORDP04_ChkRdm` | 媒體 `Z1` | 無 |
| `OFDB757` | 「下單日期 / 交易日期 / 下單編號 / 含No Order」 | SP `s_TA_OFDB757_Get` | SP `s_TA_OFDB757_Excute` | 無 |

唯一的交集是 **`OFD751` 這張表被 `OFDB755` 讀**,以及五支都用同一個媒體類型 `Z1`(跟 `716`–`722` 共用媒體類型,不共用媒體代號)。`OFDB751` 用的是媒體類型 `R`,跟另外五支都不同。

> **回答:`751`–`757` 只是代號相鄰,彼此無關。** 它們像是同一批「對外平台轉檔」需求分批交付的結果,共用 `ExportFileEngine` / `ImportFileEngine` 的程式碼樣板(`ExportDataList` 那一段五支幾乎逐字相同),但業務上互不相干。

`OFDB752` 是這群裡唯一有實質商業邏輯的(909 行 PO),它依「資料來源 / 檔案格式 / 傳輸平台」三個下拉組出不同的取數 SQL(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB752_PO.cs:165`、`:272`、`:381`),三段都用 `F_TA_SPLITWORDS(:FUND_ID)` 拆多基金。

### 6.6 `OFDB901` 與 `OFDB707` —— 本篇第二個必答題

> **結論:沒有關係。`OFDB901` 不是 `OFDB707` 的重跑版,也不是補檔版。代號 `901` 吃 `OFD708` 純屬命名巧合。**

#### 6.6.1 判定依據

除了 §0.2 第四件事列的六條差異,還有三條決定性的:

1. **全庫 grep `OFD708` 只有四個 `.cs` 命中**,`OFDB707` 相關檔案一個都沒有。`OFDB707` 碰的是 `OFD706` / `OFD701`。

2. **沒有共用 SP。** `OFDB707` 用 `s_TA_SealProof_ReturnProcess`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:286`);`OFDB901` 一支 SP 都不用,全部走 EVA 基底的 `Add`。

3. **批號格式完全不同。** `OFDB707` 的批號來自 `OFD706.BATCH_ID`(由 `SerialNo.GetSEAL_Batch_ID` 編);`OFDB901` 自己在 `BeforeAdd` 編 `FIS` + `yyyyMMdd` + 4 碼流水(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:65`、`:71`、`:73`)。

#### 6.6.2 `OFDB901` 實際在做什麼(推測)

畫面標籤:「客戶種類」「產生授權檔」「匯入結果」「授權資料」「檔案路徑」「戶號」「受益人ID」「授權帳戶」 (`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901.Designer.cs:274`、`:293`、`:260`、`:189`、`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901p0.Designer.cs:71`、`:83`、`:95`)。

兩個模式,由 `OFD708[0].TRADE_NO` 是否為空決定(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:59`):

**模式一 產生授權檔**(`export == true`):

- `:62-65` 查當日最大批號 `WHERE BATCH_ID LIKE 'FIS{yyyyMMdd}%'`。

- `:70-73` 沒有就用 `FIS{yyyyMMdd}0001`;有就把第 12–15 碼 +1。

- `:77-78` 另外查 `MAX(TRADE_NO)`,逐列 `+1` 給 `D7` 格式。

- 寫完之後,UI 層把資料輸出成定長文字檔:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901.cs:184-196`,最後一行是寫死的 trailer `"3########V011100008160170158"` + 9 碼筆數。〔客戶特定〕

**模式二 匯入結果**(`BATCH_ID == "-"`,`:96`):

- `:98-100` `UPDATE OFD708 SET BATCH_ID = (SELECT MAX(BATCH_ID) FROM OFD708 A WHERE A.Trade_No = OFD708.Trade_No AND BATCH_ID <> '-') WHERE BATCH_ID = '-'`。

#### 6.6.3 `OFDB901` 的四個問題

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `BATCH_ID <> '-'` 遇到 `BATCH_ID` 為 NULL 時是 UNKNOWN,那些列不會被子查詢選中 → `MAX` 可能回 NULL → 把 `BATCH_ID` 更新成 NULL | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:99` | **高** |
| 2 | `TRADE_NO` 直接串接進 SQL | `:67` | 中 |
| 3 | 批號用 `Substring(0,11)` + `Substring(11,4)` 位置取值;格式一變就越界 | `:73` | 中 |
| 4 | `MAX(TRADE_NO)` + 1 在同一個交易裡算,但兩個使用者同時按會拿到同一個值(沒有序列、沒有 `FOR UPDATE`) | `:77-78`、`:86` | 中 |

### 6.7 `OFDB871` CLB / FSA 申報 —— 三支有宣告主檔的其中之一

**畫面**:「資料種類 / CLB資料 / FSA資料 / 執行年月」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB871.Designer.cs:181`、`:206`、`:217`、`:229`)。

**寫入順序**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:58-389`):

1. `:70` `dbProduct.BeginTransaction()`(單交易,走 EVA 基底的連線)。

2. `:73` `MasterTable` 改成 `OFD871` / `OFDB871_CLB`。

3. `:79-135` 組 CLB 的 `INSERT INTO OFD871 ... SELECT ... FROM BMS001A WHERE ID_NO = :CLB_ID_NO` —— 24 個欄位,四眼欄位全部從畫面帶。

4. `:140-185` 逐列:`ID_NO` 一變就先 `DELETE OFD871 WHERE CLB_DATE = :CLB_DATE AND CLB_ID_NO = :CLB_ID_NO`,再 INSERT。**這就是它的重跑保護。**

5. `:190` `MasterTable` 再改成 `OFD872` / `OFDB871_FSA`。

6. `:195-359` 同樣手法寫 `OFD872`。

7. `:363-374` 兩邊筆數都是 0 才 rollback,否則 commit。

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 畫面 | `Check_DATA` 申報資料是否已存在 | 已存在 | 詢問(回 `-1`) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:401-438` |
| 執行 | CLB + FSA 筆數皆為 0 | 是 | 阻擋 + rollback | `:363-368` |

**三個問題**:

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `Check_DATA` 的 `catch` 吞掉例外後直接 `return -1`(= 已存在)。**DB 出錯 = 一律判定已申報過**,而且畫面不會知道為什麼 | `:432-437` | **高** |
| 2 | `DELETE` 綁 `CLB_DATE` 用 `OracleDbType.Date`(`:177`),同一個欄位在 `INSERT` 卻綁 `Varchar2`(`:149`),而 `dr.CLB_DATE` 是字串 | `:149` vs `:177` | **高** |
| 3 | Oracle PO 裡用 `SqlDbType.VarChar` 綁參數 | `:426-427` | 中 |

### 6.8 `OFDB903` 定期定額扣款 —— 本片唯一一支 SP 有腳本的

`DB/SP/S_OTA_OFDB903_EXE.sql` 是本片 21 支 SP 裡**唯一**在版控裡的(582 行,編碼 cp950)。它同時回答了「交易邊界在哪一層」:

> **SP 本體從頭到尾沒有 `COMMIT` 也沒有 `ROLLBACK`**(全檔 grep 兩個關鍵字:0 命中),只有 `RAISE is_someting_error` 往上丟(`DB/SP/S_OTA_OFDB903_EXE.sql:68`、`:113`、`:132`、`:157`、`:176`、`:252`、`:276`)。**交易由 C# 端開、C# 端收**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:130` `dbProduct.BeginTransaction()`)。與 `ofdb.md` 對 `OFDB003` 的結論一致。

**SP 動到的表比 C# 看得到的多兩張**:`TTP901`(日日定期定額扣款傳檔,`DB/SP/S_OTA_OFDB903_EXE.sql:530`)與 `OFD062`(交易別,`:22`)。C# 端完全沒提到這兩張 —— 掃描器只讀 `.cs`,所以這兩張在任何以 C# 為母體的清單裡都查不到。

**兩個分支**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:132`、`:208`):

| `Job_Type` | 做什麼 | 參數 | 卡控 |
|---|---|---|---|
| `0` 扣款作業 | 逐基金呼叫 SP,`TYPE1` = 產生 / 重作 / 刪除;產生後查 `OFD9041.SUB_CNT` 統計筆數 | `TYPE1`、`FUND_ID`、`DEF_SUB_DATE`、`REAL_SUB_DATE` | 無 |
| `1` 確認作業 | `UPDATE OFD904` 與 `OFD9041` 的 `CFM_CD` | `TYPE2` = 確認 / 取消 | 影響 0 筆就 rollback |

**確認作業那兩條 `UPDATE` 的 `WHERE` 只有 `DEF_SUB_DATE`,沒有 `FUND_ID`**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:230`、`:257`)。畫面明明讓使用者挑基金(`Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB903.designer.cs:201` 有「基金代碼」),確認時卻把**該契約扣款日的所有基金**一起確認掉。近乎無鍵 UPDATE(附錄 E6.2)。

而且 `xFlag` 初值是 `string.Empty`(`:126`),只在 `TYPE2` 為 `"0"` 或 `"1"` 時才被賦值。**若 `TYPE2` 是其他值,`CFM_CD` 會被更新成空字串**,所有資料變成「既非已確認也非未確認」。

### 6.9 `OFDB911` / `OFDB912` / `OFDB921` —— 三支同形的 SP 包裝

三支的 `Execute` 幾乎逐字相同:開交易 → 取 SP → `CommandTimeout = 0` → 綁 4 個 IN + 1 個 OUT 訊息 → 依 OUT 是否為 NULL 決定 commit / rollback。

| 畫面 | SP | 參數 | 錨點 |
|---|---|---|---|
| `OFDB911` | `s_TA_OFDB911_Exe` | `iSDATE` `iEDATE` `iEXE_KIND` `iUSER` + OUT `oMSG`(4000) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:67-97` |
| `OFDB912` | `s_TA_OFDB912_Exe` | `iCAL_YM` `iEXE_KIND` `iUSER` + OUT `oMSG`(1000) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB912_PO.cs:67-95` |
| `OFDB921` | `S_TA_OFDB921_EXECUTE` | `iUPD_TYPE` `iYEARS` `iQDATE` `iUpdateID` + OUT `strMsg`(1000) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:52-77` |

三支共同的問題:`catch` 裡 `AddResultRow(false, 0, "")` —— **訊息是空字串**,操作員只看到「失敗」兩個字沒有任何線索(`OFDB911_PO.cs:113`、`OFDB912_PO.cs:111`、`OFDB921_PO.cs:83`)。

**`OFDB921` 另外有兩條本片最精緻的雷:**

**雷一:`LastData` 的 SQL 裡有一個全形空白。** `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:169` 是 `YEARS=:YEARS　AND QDATE=:QDATE`,`:YEARS` 與 `AND` 之間那個字元是 **U+3000 IDEOGRAPHIC SPACE**,不是半形空白。Oracle 會在剖析時丟 `ORA-00911: invalid character`。這個方法是用來填畫面上「上次執行計算日期:」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB921.Designer.cs:313`)的,而 `:190-194` 的 `catch` 把例外吞掉、訊息設成空字串。**結果是那個欄位永遠空白,而且沒有人會知道為什麼。** 嚴重度中(不影響計算,只影響顯示),但診斷難度極高 —— 肉眼看不出全形空白。

**雷二:`BeforeExecuteCheck` 的 `catch` 裡對 null 做 `Rollback`。** `:104` 宣告 `DbTransaction tran = null;`,整個方法**沒有任何一行給它賦值**(這個方法不開交易),但 `:139` 的 `catch` 第一件事就是 `tran.Rollback();`。一旦查詢丟例外,`catch` 自己再丟一個 `NullReferenceException`,**原始例外被完全遮蔽**,而且不會走到 `:140-142` 的訊息設定。嚴重度高。

另外 `:131-135`:查不到資料時 `Result` 被 `Clear()` 之後**沒有再 `AddResultRow`**,回傳一個空的 `Result` 集合。呼叫端若直接讀 `Result[0]` 會 `IndexOutOfRangeException`。

### 6.10 `OFDB913` 業務員異動審核 —— 繞過四眼直接改狀態

**畫面**:「業務員 /(空白表全部)/ 異動日期 / 戶號 / 未審核 / 審核狀態」(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB913.Designer.cs:274`、`:286`、`:382`、`:397`、`:462`、`:477`)。

**狀態轉換**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:90-101`):

| 原 `STATUS` | 動作 | 新 `STATUS` |
|---|---|---|
| `201` | UPDATE | `301` |
| `202` | UPDATE | `302` |
| `203`(刪除待覆核) | **DELETE** | — |
| `204` | UPDATE | `304` |
| 其他 | UPDATE | **上一輪迴圈留下的值** |

**`strStatus` 宣告在迴圈外**(`:65` `string strUpdate, strStatus = "";`),而 `:90-101` 的 `if / else if` 鏈**沒有 `else`**。所以當 `row.STATUS` 不是 `201` / `202` / `203` / `204` 時,`strStatus` 保留上一筆的值,那一列會被寫成**別人的狀態**。第一筆碰到未知狀態時寫成空字串。嚴重度高(附錄 E12.1)。

**這支同時是「繞過四眼直接 UPDATE 主檔」的案例**:`:79-83` 直接把 `Status` / `UpdateID` / `ApproveID` / `ApproveDate` / `Confirm_ID` / `ConfirmDate` 用手寫 SQL 塞進 `OFD913A_UPD`,完全沒有經過 EVA 引擎,也沒有檢查執行者是不是有覆核權限。與 `ofd5.md` 在 `OFDM082B_PO.cs:66-70` 發現的同型。

**而且 `catch` 連 log 都沒有**:`:133-138` 只設訊息「執行失敗,請檢查」,**沒有呼叫 `CommonExceptionBlocker.HandleBusinessException`**。本片 35 支裡只有這一支這樣。

### 6.11 `OFDB950` —— PO 是空的,整支業務邏輯在 UI 層

這是本片結構最特別的一支。

**`Execute` 什麼都不做**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB950_PO.cs:56-64`):建一個空的 VDB 就回傳。`Ctl` 仍然照呼叫(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB950_Ctl.cs:50-56`)。

**真正的工作全部在 UI**:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:68-210` 用 `FileStream` 開使用者選的定長文字檔,依「種類」下拉逐列解析:

| 種類 | 記錄長度(寫死) | 目標 DataTable | 錨點 |
|---|---|---|---|
| `0` 申購明細 | 170 | `OFDB950_Allot` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:86` |
| `1` 申購彙總 | 119 | `OFDB950_Allot` | `:120` |
| `2` 買回明細 | 248 | `OFDB950_Redem` | `:146` |
| `3` 買回彙總 | 135 | `OFDB950_Redem` | `:183` |

欄位一律用 `Encoding.Default.GetString(incomingbyties, <起始>, <長度>)` 位置取值(例 `:102` 的 `117, 13`、`:163` 的 `131, 14`)。然後把解析結果餵給 Crystal 報表(`:247-260`),報表名寫死「元富證券基金申購明細表」等四個(`:248`、`:252`、`:256`、`:260`)。〔客戶特定〕

**整支不碰資料庫。** PO 有宣告 `Database dbTA`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB950_PO.cs:31`)但從未使用。

> **對維護的意義**:這支實際上是一個「報表」,卻被編成 B 型批次,而且解析邏輯放在用戶端 —— 檔案格式一改就要重新部署整個 UI 組件。如果要改格式,`architecture.md §6.5` 講的 `.Report` 那條路才是該走的。

### 6.12 `OFDB691` / `OFDB693` —— 住在 `ATLAS.EC` 的兩支

**`OFDB691` 員工及員工關係人交易審核**(畫面標籤:「申購交易 / 贖回交易 / 轉換交易 / 定額申購 / 定額異動 / 全部通過 / 全部不通過」,`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB691.Designer.cs:288`–`:1015`)。

- **兩套實作並存**:`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB691_PO.cs` 整個類別宣告被註解(`:13`),`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs` 是現行版。兩份都在 `PO.EC.csproj` 裡編譯。

- 寫四張交易表,全部用 `sb.AppendFormat(" UPDATE ... SET x='{0}' ", ...)` **把值直接串進 SQL**: `OFD620A`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:173`)、`OFD621A`(`:200`)、`OFD641A`(`:203`、`:275`、`:347`)、`OFD651A`(`:248`、`:320`)。

- **`RSP605` / `RSP607` 那兩段被整段註解掉**(`:367`、`:382`),但畫面上「定額申購」「定額異動」兩個頁籤還在(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB691.Designer.cs:522`、`:600`)。而 `SendMail` 也只處理申購 / 買回 / 轉申購三類(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:88`、`:149`、`:209`),沒有定額。也就是說 **定額申購與定額異動兩個頁籤按下去既不寫表也不寄信,是純粹的空操作**。這是本片最隱蔽的一顆雷(附錄 E2.4)。

- **本片唯一會寄信的一支**:`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:145`、`:205`、`:262` 三處 `mailutl.SendMailTo("員工及員工關係人交易【審核結果】通知信", strBody, row.EMAIL)`。`:92`、`:153`、`:213` 都有 `if (row.EMAIL == "") continue;` —— **沒有 Email 的人直接跳過,不留任何記錄**(過濾,無提示)。

- `:109` `catch` 後 `AddResultRow(false, 0, string.Empty)` —— 又是空訊息。

**`OFDB693` 基金設定挑選**(畫面標籤「選取基金 / 已設定基金」):

- **掃描器把它判成缺 PO / DataEntity / UIEntity 三層,實際三層都在**,只是檔名不合規則:`OFDB693OracleDao.cs`(不是 `OFDB693_PO.cs`)、`OFDB693_9iModel.xsd`(不是 `OFDB693Model.xsd`)、`OFDB693_9iView.xsd`。`_9i` 後綴依 `architecture.md §7.3.2` 是第二代控件的標記。

- 它是本片 35 支裡 **唯一一支主檔宣告被掃描器完全漏掉** 的:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:30` `this.MasterTable = new xTableMapping("OFD688A", "OFDB693")`。

- 雙交易(`:106-107` `db` 與 `dbPTPF` 各開一個),六組 rollback / commit 配對(`:138`–`:190`),**兩次 commit 之間不是原子的**。

- `:222`–`:247` 六個 `throw new NotImplementedException()` —— `Select` / `Update` / `Delete` 等基底介面方法全部沒實作。這支只能新增。

### 6.13 順序相依總表

把本片所有「必須先跑 A 才能跑 B」的關係列完。**沒有任何一條是程式強制的**,全部靠資料查不到時自然做不下去:

| 先 | 後 | 靠什麼接 | 有沒有程式擋 |
|---|---|---|---|
| `OFDB701` | `OFDB702` | `OFD706.BATCH_ID` + `OFD701` | 沒有(查不到就空清單) |
| `OFDB702` | `OFDB703` | `OFD701.SEAL_STATUS` | 沒有 |
| `OFDB703` | `OFDB704` | 媒體檔的回覆檔 | 沒有 |
| `OFDB701` | `OFDB705` / `OFDB707` | `OFD706` | 沒有 |
| `OFDB716` | `OFDB721` | `CTL017 SOURCE_ID='1'` | 沒有 |
| `OFDB717` | `OFDB718` | `CTL017 SOURCE_ID='2'` | **有**:`OFDB718_PO.cs:71-88` 檢查結餘基準日 |
| `OFDB719` | `OFDB720` | `TRP810A` | 沒有 |
| `OFDB731` | `OFDB733` | `OFD733` | 沒有 |
| `OFDB733`(加密) | `OFDB732` / `OFDB734` | `_加密後.txt` 存在與否 | **有,但會退回用未加密檔**(§6.3.3 第 5 步) |
| `OFDB903` 產生 | `OFDB903` 確認 | `OFD904.CFM_CD` | 沒有 |
| `OFDB921` 計算 | `OFDB921` 重算 | `OFD922A.CTL_CODE='1'` | **有**:`BeforeExecuteCheck` 詢問 |
| 別的模組 `OFDB301` | `OFDB703` | `CTL012.ALLOT_CLS` | **有,但 fail-open**(§6.1.5) |

### 6.14 全片卡控總表(五類)

把 35 支的所有卡控攤在一張表,依五類結果分。**本片最值得注意的是「阻擋」只有 9 條,而「記錄不擋」與「過濾(無提示)」加起來有 11 條。**

| 時點 | 畫面 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| 畫面 | `OFDB701` | 必填與日期合理性 | 缺欄位 | 阻擋 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.cs:810` |
| 畫面 | `OFDB701` | 帳號在送核後有異動 | 有 | 詢問 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1329` |
| 畫面 | `OFDB701` | 是否還有未覆核 | 有 | 詢問 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1234` |
| 執行 | `OFDB701` | 媒體引擎回報格式錯誤列 | 有 | **過濾(無提示)** —— 不產檔但往下走 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1029-1033` |
| 執行 | `OFDB701` | 匯出 0 筆 | 是 | **記錄不擋**(rollback 但回報成功) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1059-1065` |
| 執行 | `OFDB701` | SP 的 `IsSuccess` / `MSG` | 任何值 | **無**(讀了不用) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1128-1152` |
| 執行 | `OFDB702` | SP 的 `vstrTempMsg` 非 NULL | 是 | 阻擋 + rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:981-988` |
| 執行 | `OFDB702` `OFDB704` `OFDB719` `OFDB751` | 匯入檔案格式 | **反的**(見 E1.1) | **記錄不擋** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:62-73` |
| 執行 | `OFDB703` | 同批扣款檔已產生 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1254` |
| 畫面 | `OFDB703` | `CTL012` 傳真委扣未關帳 | 是 | 阻擋(**查詢出錯時整條消失**) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1581-1583` + `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.cs:969-972` |
| 執行 | `OFDB703` | 指定非代理行時 `SUB_BANK_CODE <> …` | NULL 值 | **過濾(無提示)** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1416` |
| 畫面 | `OFDB715` | 集保上線日不可小於最大憑證日 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:133` |
| 畫面 | `OFDB715` | 基金是否已過帳 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:185` |
| 畫面 | `OFDB716` | `CTL017` 已有同基金資料 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:381` |
| 畫面 | `OFDB716` | 該基金該結餘日期存在 | 否 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:412` |
| 執行 | `OFDB716` `OFDB717` | 前兩段匯出 0 筆 | 是 | **記錄不擋**(訊息隨後被覆蓋) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:182-186` |
| 執行 | `OFDB718` | 上次上傳結餘基準日有異動 | 是 | 阻擋 + rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:82-88` |
| 執行 | `OFDB718` `OFDB721` | 影響筆數 | **被常數蓋掉** | **無** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:134-135` |
| 執行 | `OFDB719` | 該收檔日期已收過 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:141-145` |
| 執行 | `OFDB719` | 基金已過帳 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:151-157` |
| 畫面 | `OFDB732` `OFDB733` | 加密交換目錄 / 旗標檔不存在 | 是 | 阻擋 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:84-89` |
| 執行 | `OFDB732` `OFDB733` | `_處理結果.txt` 不存在 | 是 | 警示(「加密處理未完成」子畫面) | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:401-406` |
| 執行 | `OFDB732` `OFDB733` | `_加密後.txt` 不存在 | 是 | **過濾(無提示)** —— 改用未加密檔 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:429-434` |
| 執行 | `OFDB871` | 申報資料已存在 | 是 | 詢問(**DB 出錯時也判成已存在**) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:401-438` |
| 執行 | `OFDB871` | CLB + FSA 筆數皆 0 | 是 | 阻擋 + rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:363-368` |
| 執行 | `OFDB903` | 確認作業影響 0 筆 | 是 | 阻擋 + rollback | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:241-247` |
| 執行 | `OFDB903` | `TYPE2` 非 `0`/`1` | 是 | **無** —— `CFM_CD` 被寫成空字串 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:126`、`:212-221` |
| 畫面 | `OFDB921` | 該年度該期已計算完成 | 是 | 詢問(「確定要刪除後重新計算嗎?」) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:132-135` |
| 執行 | `OFDB911` `OFDB912` `OFDB921` | SP 的 OUT 訊息非 NULL | 是 | 阻擋 + rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:87-97` |
| 執行 | `OFDB913` | 影響筆數為 0 | 是 | 阻擋 + rollback | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:124-130` |
| 執行 | `OFDB913` | `STATUS` 不是 `201`/`202`/`203`/`204` | 是 | **無** —— 寫成上一筆的狀態 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:90-101` |
| 執行 | `OFDB691` | 受益人沒有 Email | 是 | **過濾(無提示)** | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:92` |
| 執行 | `OFDB691` | 定額申購 / 定額異動 | 任何 | **無** —— 整段被註解 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:367`、`:382` |
| 執行 | `OFDB950` | 記錄長度不符 | 是 | 阻擋(跳過該列) | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:86`、`:120`、`:146`、`:183` |

**分佈**:阻擋 15 · 警示 1 · 詢問 5 · 過濾(無提示)5 · 記錄不擋 4 · 完全無(該有而沒有)5。

### 6.15 三個必答題的結論一次看

| 問題 | 答案 | 最硬的證據 |
|---|---|---|
| `700` 系列七支是不是一條流水線? | **是。** 執行順序 `701 → 702 → 703 → 704`,另外 `705` / `706` / `707` 掛在 `701` 之後當支線。接力靠 `OFD701.SEAL_STATUS` 與 `OFD706.BATCH_ID` 的資料狀態,**不是程式呼叫** | 六支共用 `s_TA_SealProof_*` SP 家族;`OFDB702` 與 `OFDB707` 呼叫同一支 `s_TA_SealProof_ReturnProcess` |
| `715`–`722` 八支呢? | **不是一條線,是三對配對 + 兩支獨立。** `716`↔`721`(`SOURCE_ID='1'`)、`717`↔`718`(`SOURCE_ID='2'`)、`719`↔`720`(`TRP810A`);`715` 與 `722` 獨立 | `CTL017.SOURCE_ID` 與六個媒體代號的對應(§2.3) |
| `751`–`757` 六支呢? | **只是代號相鄰,彼此無關。** 唯一交集是 `OFD751` 被 `OFDB755` 讀,以及五支共用媒體類型 `Z1` | 逐支比對讀寫的表與 SP,沒有任何一對有資料相依(§6.5) |
| `OFDB901` 跟 `OFDB707` 什麼關係? | **沒有關係。** 不是重跑版也不是補檔版。`OFD708` 全庫只有 `OFDB901` 與唯讀的 `OFDI011` 在碰,`OFDB707` 碰的是 `OFD706` / `OFD701` | §0.2 第四件事 + §6.6 的三條決定性判準 |
| 排程從哪來? | **repo 內找不到任何排程。** 35/35 是 `formstyle="OneStep"` 的人工批次;三個 UI 專案的 `App.config` 都沒有 `system.runtime.remoting`;沒有 `Main(string[] args)`;沒有業務用的 `.bat`;沒有一支被別的程式 `Process.Start` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:587-785`、`Dev/ATLAS.EC/Source/UI/UI.EC/App.config:235-246`、`Dev/ATLAS.OTAB/Source/UI/UI.OTA/App.config:287-292` |

## 7. 報表(R)

**本片無 R。** 原因:35 支的型別碼全是 `B`。但有兩支批次自己掛 Crystal 報表類別,依 `architecture.md §6.5` 這是命名鐵律的正式例外:

| 報表類別檔 | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701RPS.cs` | `OFDB701` 的 `DoExp1`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.cs:1102`) | `PrintReport`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1418`) | `BATCH_ID` |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950RPS.cs`、`OFDB950RPS1.cs`、`OFDB950RPS2.cs`、`OFDB950RPS3.cs` | `OFDB950` 的四個「種類」 | **用戶端解析出來的 DataTable,不查 DB** | `Report_Name`、`CompanyName`、`LoginName` |

`OFDB703` 原本也有一份(`OFDB703RPS`,報表名「扣款送件查核表」),但呼叫那一整段在 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.cs:114-215` **全部被註解掉**,外殼(`if (業務別 == "2" && ...)` 判斷)還在。這是缺陷型錄「被註解但外殼還在的檢核」的變形(附錄 E2.3)。

## 8. 跨模組共用

```text
[圖] 本片讀寫的表被哪些模組共用、與 ofdb.md 那片的接點,以及三支住在別的專案與五組版控外相依
圖中文字:本片讀取、別的模組維護的表 —— 改動前要問的對象 / BMS001A BMS005A / 受益人與帳號主檔 / BMS001ACHG BMS005ACHG / 未生效變更 由 OFDB003 生效 / RSP006A RSP013A / 定期定額帳號與變更 / OFD081A OFD081V / 基金主檔與檢視 / OFD020V OFD074 / 銀行別與總行對照 / 本片與 ofdb.md 那片的接點:同一組 CHG 哨兵、同一張基金主檔 / OFDB003 / ofdb.md 的頭號重點 / CHG_UPD_DTTM 哨兵 / 本片 701 702 705 706 707 都在讀 / 第四種寫法 = '1900/1/1' / OFDB706 單位數月日 / ofdb.md E5.3 說三種 / 本片補到四種 / 本片寫入、別的模組讀取的表 / OFD701 核印狀態 / BMSM001 也讀 / OFD708 授權檔 / OFDI011 客戶綜合查詢在讀 / OFD081A TDCC_START_BAL_DATE / OFDB721 無鍵重設 / TRP80x 七張集保表 / OFD 報表片在讀 / 跨專案的三支 —— 代號是 OFDB 但住在別的專案 / OFDB691 OFDB693 / Dev/ATLAS.EC / OFDB903 / Dev/ATLAS.OTAB / PO.EC 有 MSSQL 與 Oracle 兩份 / OFDB691 兩套實作 / 掃描器把 OFDB693 判成缺三層 / 實際是 _9i 與 OracleDao 命名 / 版控外的相依 —— 改動時查不到的部分 / SP 13 支 / repo 內腳本 0 支 / ExportFileEngine ImportFileEngine / 媒體格式定義在 TRP001A / 外部加密程式 / 只靠檔案交換 / MailUtility / OFDB691 寄三封通知信 / CRReportTransfer / OFDB950 四張報表
```

*圖:圖 6 跨模組影響面。橘框=本片自己的結論;橘虛框=改動時要一起看的部分;灰虛框=本片以外的畫面或表;黑框=無原始碼。第②列是本片對 ofdb.md 的補強:那邊列了三種 CHG_UPD_DTTM 哨兵寫法,本片在 OFDB706 找到第四種。*

### 8.1 本片讀取、別的模組維護的表

改這些表的欄位之前,要一起看本片:

| 表 | 誰維護 | 本片誰在讀 | 讀什麼 |
|---|---|---|---|
| `BMS001A` / `BMS001ACHG` | BMS(`bms.md §2`) | `OFDB701` `OFDB702` `OFDB703` `OFDB705` `OFDB706` `OFDB707` `OFDB731` `OFDB733` `OFDB734` `OFDB752` `OFDB755` `OFDB871` `OFDB913` | 受益人主檔與未生效變更 |
| `BMS005A` / `BMS005ACHG` | BMS | `OFDB701` `OFDB702` `OFDB705` `OFDB706` `OFDB707` | 扣款帳號與銀行分行 |
| `RSP006A` / `RSP013A` | RSP | `OFDB701` `OFDB702` `OFDB705` `OFDB706` `OFDB707` | 定期定額扣款帳號與變更 |
| `OFD081A` / `OFD081V` | OFD 的 M 片 | `OFDB703` `OFDB715` `OFDB716` `OFDB717` `OFDB718` `OFDB720` `OFDB721` `OFDB722` `OFDB733` `OFDB734` `OFDB752` `OFDB753` `OFDB755` `OFDB871` `OFDB903` | 基金主檔、`FUND_ID_TDCC` 集保對照 |
| `OFD020V` / `OFD074` / `OFD076` | OFD 的 M 片 | `OFDB701` `OFDB702` `OFDB703` `OFDB705` `OFDB706` `OFDB707` | 銀行別 / 總行對照,`f_TA_GetBankHQ` 的來源 |
| `OFD302A` / `OFD303A` | OFD 的 M 片 | `OFDB716` `OFDB717` `OFDB719` `OFDB722` `OFDB752` `OFDB753` | 淨值與過帳控制 |
| `CTL012` | 共用控制 | `OFDB703` | 傳真委扣關帳(§6.1.5) |
| `CTL015` | 共用控制 | `OFDB702` `OFDB707` | 代碼值域 |
| `OFD281A` / `OFD283A` | `ofdb.md` 的 `OFDB281` 那條線 | `OFDB755` | 收益分配明細 |
| `TRP001A` / `TRPARAMS` | 媒體引擎的設定表(無 M 畫面) | `OFDB701` `OFDB703` `OFDB704` `OFDB716` `OFDB717` `OFDB722` | 媒體格式與輸出路徑 |

### 8.2 與 `ofdb.md` 那片的接點

| 接點 | `ofdb.md` | 本片 |
|---|---|---|
| `CHG_UPD_DTTM` 生效機制 | `OFDB003` 是生效引擎(`ofdb.md §6.1`) | 本片五支只讀不寫,用哨兵判斷生效沒 |
| 哨兵寫法 | 三種(`ofdb.md 附錄 E5.3`) | **補到四種**,新增 `= '1900/1/1'` |
| `OFDB701` / `OFDB702` | 明確標「不在本篇」(`ofdb.md 附錄 D.1`) | §6.1.2 / §6.1.3 完整攤開 |
| `BasicEVAPO` 死碼群 | 四支(`ofdb.md §0.2`) | 本片再找到五支 |
| 「一律回報成功」 | `ofdb.md 附錄 E1` | 本片找到四種新形態(附錄 E1) |
| 排程有無 | `OFDB003` 手動、無排程 | 本片 35/35 手動、無排程、無 Remoting |

### 8.3 本片寫入、別的模組讀取的表

| 表 | 本片誰寫 | 誰讀 | 改動影響 |
|---|---|---|---|
| `OFD701` | `OFDB702`(經 SP) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs`(全庫 grep `OFD706` 的命中之一) | 核印狀態改動會影響 BMS 的帳號維護畫面顯示 |
| `OFD708` | `OFDB901` | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`(唯讀) | 授權資料改欄位要一起改客戶綜合查詢 |
| `OFD081A.TDCC_START_BAL_DATE` | `OFDB721`(無鍵重設) | OFD 的 M 片與報表 | §6.4.2 |
| `OFD871` / `OFD872` | `OFDB871` | 申報報表(不在本片) | 先 DELETE 再 INSERT,重跑會清掉同一天同一人的資料 |
| `TRP801A`–`TRP810A` | `OFDB716`–`OFDB721` | OFD 報表片 | `DEL_YN` 軟刪除,讀取端必須自己加 `DEL_YN='N'` |
| `OFD904` / `OFD9041` / `TTP901` | `OFDB903`(經 SP) | OTA 模組 | `TTP901` 只出現在 SP 腳本裡 |

### 8.4 共用 helper 與黑箱

| Helper | 用途 | 有無原始碼 | 本片誰用 |
|---|---|---|---|
| `ExportFileEngine` | 產媒體檔 | **無**(從呼叫端反推) | `OFDB701` `OFDB703` `OFDB705` `OFDB716` `OFDB717` `OFDB722` `OFDB752` `OFDB753` `OFDB755` `OFDB756` |
| `ImportFileEngine` | 收媒體檔 | **無** | `OFDB702` `OFDB704` `OFDB719` `OFDB751` |
| `SerialNo` | 各種批號 | **無** | `OFDB701` `OFDB716` `OFDB717` |
| `EVAUtility` | 四眼欄位填值 | **無** | `OFDB701`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:840`) |
| `ServerMailUtility` | 寄信 | **無** | `OFDB691` |
| `CRReportTransfer` | 取報表二進位 | **無** | `OFDB950`(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB950_Ctl.cs:73`) |
| `CommonExceptionBlocker` | 例外轉譯 | **無** | 34 支(只有 `OFDB913` 沒用) |
| `SQLHelper.EVAStringHelper` | 取參數 | **無** | `OFDB903` |
| `xTableHelper` | 產 INSERT 語句與綁參數 | **無** | `OFDB701` |

### 8.5 改動影響面速查

| 要改什麼 | 一定要一起看 |
|---|---|
| `OFD701` 的欄位 | `OFDB701` `OFDB702` `OFDB703` `OFDB705` `OFDB706` `OFDB707` + `BMSM001` + 五支 SP |
| `CTL017` 的欄位 | `OFDB716` `OFDB717` `OFDB718` `OFDB719` `OFDB721` `OFDB722` |
| 集保媒體格式 | `TRP001A` / `TRPARAMS` 設定 + `OFDB716` `OFDB717` 的 `AddParameters` |
| `OFD081A.FUND_ID_TDCC` | `OFDB715` `OFDB716` `OFDB717` `OFDB718` `OFDB721`(五支都在 join 它) |
| 加密程式的 ini 格式 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:439-443` 與 `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:512-516` **兩份要一起改** |
| `OFD733` 的欄位 | `OFDB731` `OFDB733` `OFDB734` + `OFD733` 在 `DB/Table/` 沒有腳本 |
| 任何一支 SP 的參數 | 沒有腳本可查(附錄 B),只能從呼叫端反推 |

## 附錄 A. 資料表總表

### A.1 本片會寫的實體表(依群分類)

| 群 | 表 | 寫入者 | 寫入方式 |
|---|---|---|---|
| A 核印扣款 | `OFD703` | `OFDB701` | INSERT |
| A | `OFD704` | `OFDB701` `OFDB703` | INSERT(`OFDB701` 那條是壞的,附錄 E3.1) |
| A | `OFD705` | **沒有人寫**(`OFDB703` 的 INSERT 整段被註解,只剩 `#region` 外殼,`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1090-1095`) | — |
| A | `OFD706` | `OFDB701` | INSERT |
| A | `OFD701` | `OFDB702` `OFDB706` `OFDB707` | 經 SP |
| A | `OFD702` `OFD707` `OFD711` | `OFDB702` | 只在被註解的程式碼裡 |
| A | `SEALTMP` | `OFDB702` `OFDB719` | INSERT |
| B 集保 | `CTL017` | `OFDB716` `OFDB717`(寫)、`OFDB718` `OFDB721`(DELETE) | 直接 SQL |
| B | `TRP801A` `TRP802A` `TRP804A` | `OFDB717`(經媒體引擎)、`OFDB718`(`DEL_YN='Y'`) |  |
| B | `TRP803A` `TRP805A` `TRP805A_Detail` `TRP806A` `TRP806A_Detail` | `OFDB716`(經媒體引擎)、`OFDB721`(`DEL_YN='Y'`) |  |
| B | `TRP810A` `TRP810ATMP` | `OFDB719` `OFDB720` |  |
| B | `OFD081A` | `OFDB715`(集保上線日)、`OFDB721`(`TDCC_START_BAL_DATE` 清空) | UPDATE |
| C 結匯 | `OFD733` | `OFDB731` | INSERT / DELETE |
| C | `OFD734` `OFD736` | `OFDB732` `OFDB734` | DELETE + SP |
| C | `OFDB732_TMP` `DELETETEMPFILE` | `OFDB732` |  |
| D 轉檔 | `ORDP01DTL` | `OFDB752` | INSERT |
| E 計算 | `OFD871` `OFD872` | `OFDB871` | DELETE + INSERT |
| E | `OFD913A_UPD` | `OFDB913` | UPDATE / DELETE |
| E | `OFD921A` `OFD922A` | `OFDB921`(經 SP) |  |
| F | `OFD688A` | `OFDB693` | INSERT |
| F | `OFD708` | `OFDB901` | EVA `Add` + UPDATE |
| F | `OFD904` `OFD9041` `TTP901` | `OFDB903`(經 SP) |  |
| F | `OFD620A` `OFD621A` `OFD641A` `OFD651A` | `OFDB691` | UPDATE(字串串接) |

### A.2 只讀不寫的表

`OFD700` `OFD713` `OFD735` `OFD076` `OFD020V` `OFD074` `OFD038A` `OFD068A` `OFD070A` `OFD006A` `OFD220A` `OFD221A` `OFD251A` `OFD252A` `OFD253A` `OFD254A` `OFD281A` `OFD283A` `OFD302A` `OFD303A` `OFD305A` `OFD312A` `OFD0811A` `OFD0813` `OFD0813A` `OFD751` `OFD676A` `OFD616` `OFD654A` `OFD304A` `OFD002` `OFD003A` `OFD904`(讀的部分) `OFD9041`(讀的部分) `OFD606A` `COD006A` `COD009` `CTL012` `CTL014` `CTL015` `FSK003` `ORDR01` `BMS001` `BMS001A` `BMS001CHG` `BMS001ACHG` `BMS005` `BMS005A` `BMS005CHG` `BMS005ACHG` `RSP005A` `RSP006` `RSP006A` `RSP007A` `RSP008A` `RSP013` `RSP013A` `TRP001A` `TRPARAMS`

### A.3 vdb 表名與實體表名不同的對照

| vdb 名 | 實體表 | 出處 |
|---|---|---|
| `OFDB693` | `OFD688A` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:30` |
| `OFDB731` | `OFD733` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:27` |
| `OFDB871_FSA` | `OFD871`(建構子)/ `OFD872`(執行期) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:36`、`:190` |
| `OFDB871_CLB` | `OFD871` | `:73` |
| `OFD708` | `OFD708`(同名) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:38` |

### A.4 `MYOFD` / `MYDATE` / `MYOFD003` / `MYOFD9041`

`OFDB903` 的 SQL 裡出現這四個名字(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs`)。它們不是實體表,是 `WITH` 子句的 inline view 別名(從命名前綴 `MY` 與上下文推斷)。**標「假設」** —— 沒有在 `DB/Table/` 或任何 xsd 裡找到同名物件。

## 附錄 B. SP / Function / Trigger / View

### B.1 本片呼叫的 SP:21 支,repo 內腳本 1 支

| SP | 誰呼叫 | 錨點 | 腳本在 repo? |
|---|---|---|---|
| `s_TA_SealProof_Process_1` | `OFDB701` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1096` | 否 |
| `s_TA_SealProof_Process_5` | `OFDB705` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB705_PO.cs:529` | 否 |
| `s_TA_SealProof_ReturnProcess` | `OFDB702`、`OFDB707` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:959`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:286` | 否 |
| `s_TA_ReSeal_Process` | `OFDB702` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:1246` | 否 |
| `s_TA_CancelReSeal_Process` | `OFDB702` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:1871` | 否 |
| `s_SealProof_ChangeStatus` | `OFDB706` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:278` | 否 |
| `s_TA_OFDB715_Excute` | `OFDB715` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:57` | 否 |
| `s_OFDB732_Query` | `OFDB732` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:36` | 否 |
| `s_OFDB732_Excute` | `OFDB732` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB732_PO.cs:149` | 否 |
| `s_OFDB733_Excute` | `OFDB733` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:49` | 否 |
| `s_OFDB734_Excute` | `OFDB734` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB734_PO.cs:206` | 否 |
| `s_TA_ORDP04_Get` | `OFDB756` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB756_PO.cs:58` | 否 |
| `s_ORDP04_ChkRdm` | `OFDB756` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB756_PO.cs:216` | 否 |
| `s_TA_OFDB757_Get` | `OFDB757` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB757_PO.cs:57` | 否 |
| `s_TA_OFDB757_Excute` | `OFDB757` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB757_PO.cs:131` | 否 |
| `s_TA_OFDB911_Exe` | `OFDB911` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:67` | 否 |
| `s_TA_OFDB912_Exe` | `OFDB912` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB912_PO.cs:67` | 否 |
| `S_TA_OFDB921_EXECUTE` | `OFDB921` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:52` | 否(只有 `DB/Table/createSynonym.sql:15` 建同義字) |
| `S_OTA_OFDB903_EXE` | `OFDB903` | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:140` | **是** `DB/SP/S_OTA_OFDB903_EXE.sql` |
| `s_OFDB691_Booking` | `OFDB691` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:640` | 否 |
| `S_EC_OFDB691_SENDBACK` | `OFDB691` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:727`、`:740` | 否 |

覆蓋率 **1 / 21 = 4.8%**,比 `architecture.md 附錄 B.0` 全庫的 16% 還低。

### B.2 Function

| Function | 用途(推測) | 誰用 |
|---|---|---|
| `f_TA_GetBankHQ` | 由分行代碼求總行代碼 | `OFDB701` `OFDB702` `OFDB703` `OFDB705` `OFDB707` |
| `f_TA_GetEVAStatus` | 回傳某階段的 `STATUS` 值集合(table function) | `OFDB701` `OFDB705` |
| `F_TA_SPLITWORDS` | 逗號字串拆成資料列(table function) | `OFDB701` `OFDB703` `OFDB715` `OFDB752` `OFDB753` |
| `f_TA_IsFundClose` | 基金是否已過帳(table function) | `OFDB715`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:205`) |
| `F_TA_STRTODATE` | 字串轉日期 | `OFDB701`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1434`) |
| `dbo.f_FormatStringToTable` | **SQL Server 版**的字串拆列 | `OFDB731`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:436`) |
| `dbo.f_Nvl` | **SQL Server 版**的 NVL | `OFDB706`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:146`) |

repo 內 `DB/Function/` 沒有以上任何一支的腳本。

### B.3 Trigger / View

本片沒有任何一支明確呼叫 Trigger。View 只有 `OFD081V` / `OFD020V` / `OFD303A`(名稱像 View,但 repo 內查不到定義,從命名後綴 `V` 推斷,**標「假設」**)。

## 附錄 C. 代碼對照

見 §2.5。此處補三組本片特有、`architecture.md 附錄 C` 沒有的:

| 代碼組 | 值 | 意義 | 來源 |
|---|---|---|---|
| 媒體類型 `TRP_TYPE` | `1201` / `Z1` / `Z` / `R` | 核印扣款 / 集保與轉檔 / 舊淨值(已停用) / 下單短線 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1026`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:157`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB722_PO.cs:290`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:60` |
| 媒體代號 `MEDIA_NO` | `TRP801` FUY / `TRP802` FUS2 / `TRP803` 699S / `TRP804` STF673S / `TRP805` SIN / `TRP806` BOK | 集保六種媒體 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:156`、`:207`、`:257`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:326`、`:443` |
| `AgentBankType` | `AssignBank` / `AgentBank` / `NonAgentBank` | 指定行 / 代理行 / 非代理行 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1397`、`:1409`、`:1414` |

## 附錄 D. 掃描母體與覆蓋率

**不跑 `--module OFD`** —— 那會拿 550 支來比。以下是本片 35 支的逐支處置表。

| # | 代號 | 處置 | 觸發方式 | Remoting | 在 csproj |
|---|---|---|---|---|---|
| 1 | `OFDB691` | 已寫(§6.12) | 人工 OneStep | 無 | ✓ |
| 2 | `OFDB693` | 已寫(§6.12) | 人工 OneStep | 無 | ✓ |
| 3 | `OFDB701` | 已寫(§6.1.2),**`ofdb.md` 只提過名字,本片首次攤開** | 人工 OneStep | 無 | ✓ |
| 4 | `OFDB702` | 已寫(§6.1.3),**已見 `ofdb.md §8.1` / `§8.2` / `附錄 E5.3`,本片補充四件事** | 人工 OneStep | 無 | ✓ |
| 5 | `OFDB703` | 已寫(§6.1.5) | 人工 OneStep | 無 | ✓ |
| 6 | `OFDB704` | 已寫(§6.1.4) | 人工 OneStep | 無 | ✓ |
| 7 | `OFDB705` | 表格帶過(§6.1.1) | 人工 OneStep | 無 | ✓ |
| 8 | `OFDB706` | 已寫(§6.1.6) | 人工 OneStep | 無 | ✓ |
| 9 | `OFDB707` | 已寫(§6.1.1、§6.6.1) | 人工 OneStep | 無 | ✓ |
| 10 | `OFDB715` | 已寫(§6.4.5) | 人工 OneStep | 無 | ✓ |
| 11 | `OFDB716` | 已寫(§6.4.4) | 人工 OneStep | 無 | ✓ |
| 12 | `OFDB717` | 已寫(§6.4.4) | 人工 OneStep | 無 | ✓ |
| 13 | `OFDB718` | 已寫(§6.4.2、§6.4.3) | 人工 OneStep | 無 | ✓ |
| 14 | `OFDB719` | 已寫(§6.1.4、§6.4.1) | 人工 OneStep | 無 | ✓ |
| 15 | `OFDB720` | 表格帶過(§6.4.1) | 人工 OneStep | 無 | ✓ |
| 16 | `OFDB721` | 已寫(§6.4.2、§6.4.3) | 人工 OneStep | 無 | ✓ |
| 17 | `OFDB722` | 已寫(§6.4.5) | 人工 OneStep | 無 | ✓ |
| 18 | `OFDB731` | 已寫(§6.3.2) | 人工 OneStep | 無 | ✓ |
| 19 | `OFDB732` | 已寫(§6.3.3) | 人工 OneStep | 無 | ✓ |
| 20 | `OFDB733` | 已寫(§6.3.3) | 人工 OneStep | 無 | ✓ |
| 21 | `OFDB734` | 表格帶過(§6.3.1、§6.3.3) | 人工 OneStep | 無 | ✓ |
| 22 | `OFDB751` | 已寫(§6.1.4、§6.5) | 人工 OneStep | 無 | ✓ |
| 23 | `OFDB752` | 已寫(§6.5) | 人工 OneStep | 無 | ✓ |
| 24 | `OFDB753` | 表格帶過(§6.5) | 人工 OneStep | 無 | ✓ |
| 25 | `OFDB755` | 表格帶過(§6.5) | 人工 OneStep | 無 | ✓ |
| 26 | `OFDB756` | 表格帶過(§6.5) | 人工 OneStep | 無 | ✓ |
| 27 | `OFDB757` | 已寫(§6.5) | 人工 OneStep | 無 | ✓ |
| 28 | `OFDB871` | 已寫(§6.7) | 人工 OneStep | 無 | ✓ |
| 29 | `OFDB901` | 已寫(§6.6) | 人工 OneStep | 無 | ✓ |
| 30 | `OFDB903` | 已寫(§6.8) | 人工 OneStep | 無 | ✓ |
| 31 | `OFDB911` | 已寫(§6.9) | 人工 OneStep | 無 | ✓ |
| 32 | `OFDB912` | 已寫(§6.9) | 人工 OneStep | 無 | ✓ |
| 33 | `OFDB913` | 已寫(§6.10) | 人工 OneStep | 無 | ✓ |
| 34 | `OFDB921` | 已寫(§6.9) | 人工 OneStep | 無 | ✓ |
| 35 | `OFDB950` | 已寫(§6.11) | 人工 OneStep | 無 | ✓ |

**統計:已寫 28 支、表格帶過 7 支、已見 `ofdb.md` 1 支(`OFDB702`,本片補充);觸發方式 35/35 人工 OneStep;Remoting 0/35;不在 csproj 0 支。**

### D.1 本片沒有涵蓋、但相鄰的東西

| 東西 | 為什麼不在本片 |
|---|---|
| `OFDB001`–`OFDB287` 18 支 | `ofdb.md` 的範圍 |
| `OFDB540`–`OFDB690` | 另一片的範圍 |
| `OFDB301` 傳真委扣交易截止設定 | 被 `OFDB703` 的訊息提到,但不在名單 |
| `OFDB690` | `OFDB691` 的 `SelectedPlugin` 指到它,但它不在名單 |
| `OFDB902` | `App.config` 有 section(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/App.config:750`),但不在名單 |
| `Dev/ATLAS.EC/Source/WindowsService/` 三支 | `ofdb.md §8.3` 已處理 |

### D.2 怎麼自己查

```
py -V:3.12 /docs/tools/atlas_scan.py --screen OFDB716
```

注意三件事:(1) 掃描器認不得 `OracleDao.cs` 與 `_9iModel.xsd` 這兩種命名,`OFDB693` 會被誤報成缺三層;(2) 掃描器只看建構子,`OFDB871` 在 `Execute` 裡重指派的兩張表抓不到;(3) 掃描器只讀 `.cs`,SP 腳本裡的 `TTP901` / `OFD062` 永遠不會出現。

## 附錄 E. 讀本文時要注意的地方

本片讀碼發現 **69 條**。依型錄分組,每條附錨點與嚴重度。嚴重度「高」的有 26 條。

### E1 一律回報成功 / 判斷結果被覆蓋(本片第一大坑)

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | 匯入檔案格式檢核四份複本,`bl` 語意與註解相反:**格式錯誤時才匯入,而且回報成功** | 壞檔進 temp 表,操作員看到「成功」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2337-2350`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:62-73`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB719_PO.cs:121-130`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:66-77` | **高** |
| E1.2 | 加密後檔案不存在就退回讀加密前檔案 | **未加密的身分證字號進申報檔**,不報錯 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB732_Ctl.cs:225-231`、`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB733_Ctl.cs:429-434` | **高** |
| E1.3 | `s_TA_SealProof_Process_1` 的 OUT 參數 `IsSuccess` / `MSG` 讀出來後完全沒用,一律 commit 報成功 | SP 判失敗,畫面說成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1128-1152` | **高** |
| E1.4 | `OFDB716` / `OFDB717` 前兩段匯出 0 筆只寫訊息不中斷,第三段把訊息 `Clear()` 後改寫成成功 | 兩個媒體檔沒產出,操作員不知道 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:182-186`、`:230-234`、`:287-294`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:353-358`、`:479-483` | **高** |
| E1.5 | `OFDB702` 的 `ExecOption` 只認 `"0"` / `"3"`,其他值什麼都沒做但照樣 commit 報成功 | 靜默空轉 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:945`、`:2276-2279` | **高** |
| E1.6 | `OFDB701` 匯出 0 筆時 rollback,但 `AddResultRow(true, …)` | 訊息說「無檔案匯出」而 `ReturnCode` 是成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1059-1065` | 中 |
| E1.7 | `OFDB757` commit 之後一律 `AddResultRow(true, 1, "執行成功")`,不看 SP 影響筆數 | 0 筆也說成功 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB757_PO.cs:156-160` | 中 |

### E2 空操作 / 被註解但外殼還在

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | `OFDB701` 寫 `OFD704` 時把 `CreateID` / `EntryID` / `VerifyID` / `ApproveID` 全填成執行者本人 | 四眼形同虛設 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:883-891` | **高** |
| E2.2 | `OFDB913` 直接手寫 SQL 改 `Status` / `ApproveID` / `ApproveDate`,繞過 EVA 引擎,也不檢查權限 | 繞過四眼(與 `ofd5.md` 的 `OFDM082B_PO.cs:66-70` 同型) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:79-83` | **高** |
| E2.3 | `OFDB703` 的「扣款送件查核表」整段被註解,外層 `if (業務別=="2" && …)` 判斷還在 | 條件成立時什麼都不會發生 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.cs:107-215` | 中 |
| E2.4 | `OFDB691` 的 `RSP605` / `RSP607` 更新整段被註解,畫面上「定額申購」「定額異動」兩個頁籤還在,`SendMail` 也不處理這兩類 | **定額類審核是純空操作** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:367`、`:382`;`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB691.Designer.cs:522`、`:600` | **高** |
| E2.5 | `OFDB950` 的 `Execute` 建一個空 VDB 就回傳 | PO 層完全沒作用,`Database dbTA` 宣告了從未用 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB950_PO.cs:31`、`:56-64` | 中 |
| E2.6 | `OFDB722` 的第二組媒體匯出(`"Z"`)與整段交易控制被註解,只剩一組 | 曾經產兩種媒體,現在只產一種 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB722_PO.cs:290`、`:320-337`、`:407`、`:438-486` | 中 |
| E2.7 | `OFDB693` 六個基底介面方法全是 `throw new NotImplementedException()` | 這支只能新增,不能查 / 改 / 刪 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:222-247` | 低 |
| E2.8 | `OFDB703` 的 `INSERT INTO OFD705` 整段被註解,只剩 `#region OFD705` 外殼;全片沒有任何一支寫 `OFD705`,但取數 SQL 還在讀它 | 扣款明細表永遠是空的 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1090-1095` | **高** |

### E3 SQL 語句本身壞掉

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | `INSERT INTO OFD704` 欄位 15 個、`VALUES` 16 個(多一個 `:dataid`);`AddInParameter` 把 `VERIFYDATE` 綁兩次,`APPROVEDATE` 從未綁;`REJECTID` / `REJECTDATE` 打成 `REJCETID` / `REJCETDATE` | Oracle 直接 `ORA-00913`,整支 `OFDB701` 送件不了 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:864-894` | **高** |
| E3.2 | `OFDB921.LastData` 的 SQL 裡有一個 **U+3000 全形空白**(`:YEARS AND`) | `ORA-00911`;例外被吞,畫面「上次執行計算日期」永遠空白,肉眼看不出原因 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:169` | 中 |
| E3.3 | `OFDB871` 的 `DELETE` 把 `CLB_DATE` 綁成 `OracleDbType.Date`,`INSERT` 綁成 `Varchar2`,而來源是字串 | 型別轉換失敗或刪不到,重跑保護失效 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:149` vs `:177` | **高** |
| E3.4 | `OFDB871.Check_DATA` 在 Oracle PO 裡用 `SqlDbType.VarChar` 綁參數 | 型別列舉混用 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:426-427` | 中 |
| E3.5 | 同一段 `INSERT INTO OFD704` 在 `OFDB703` 是正確的 15 欄 15 值,在 `OFDB701` 卻是 15 欄 16 值 —— **成對程式只改一邊** | 修 `OFDB701` 可直接照抄 `OFDB703_PO.cs:1051-1083` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1051-1059` vs `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:864-872` | **高** |

### E4 `catch (SqlException)` 在 Oracle 上是死碼

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| E4.1 | `OFDB702` 的 `catch (SqlException sqlex)` 永遠不會進去 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:2281` | 低 |
| E4.2 | `OFDB707` 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB707_PO.cs:335` | 低 |

### E5 Oracle 三值邏輯與會靜默濾掉資料的條件

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | `OFDB703.HasExecute` 的 `" AND SUB_BANK_CODE <> " + strAgentBank` | `SUB_BANK_CODE` 為 NULL 的列被靜默濾掉(UNKNOWN);而且值沒加引號 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1416` | **高** |
| E5.2 | `OFDB901.AfterAdd` 的 `BATCH_ID <> '{0}'` 子查詢 | `BATCH_ID` 為 NULL 的列不會被 `MAX` 選中 → 可能把 `BATCH_ID` 更新成 NULL | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:99` | **高** |
| E5.3 | `CHG_UPD_DTTM` 的「未生效」判準全庫有 **四種** 寫法:`SUBSTR(NVL(TRIM(x),'19000101'),1,8)='19000101'`、`NVL(x,' ')=' '`、`x='1900/01/01'`、**`x='1900/1/1'`** | 資料存成單位數月日時四種寫法答案不同 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB706_PO.cs:113`、`:146`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:236`;`ofdb.md 附錄 E5.3` | **高** |
| E5.4 | `OFDB691` 的 `if (row.EMAIL == "") continue;` | 沒有 Email 的人**不寄信也不留記錄**(過濾,無提示) | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:92`、`:153`、`:213` | 中 |
| E5.5 | `OFDB718` 的 `HAVING MAX(BAL_DATE) = :BAL_DATE` 沒有 `GROUP BY` | 依賴 Oracle 對「無 `GROUP BY` 的 `HAVING`」的隱含整體彙總行為;`CTL017` 該基金一筆都沒有時回 0 列,被判成「基準日有異動」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:71-88` | 中 |

### E6 無鍵 / 少鍵的 UPDATE

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | `OFDB721` 的 `UPDATE OFD081A SET TDCC_START_BAL_DATE = ' ' WHERE FUND_ID = :FUND_ID` 沒有 `TRANS_DATE` | 回收任一批就把該基金的起算結餘日整個清空 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:126-128` | **高** |
| E6.2 | `OFDB903` 確認作業的兩條 `UPDATE` 只有 `DEF_SUB_DATE`,沒有 `FUND_ID` | 畫面挑了基金,卻把當日所有基金一起確認 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:229-230`、`:256-257` | **高** |
| E6.3 | `OFDB903` 的 `xFlag` 初值空字串,`TYPE2` 非 `"0"`/`"1"` 時 `CFM_CD` 被寫成空字串 | 資料變成既非已確認也非未確認 | `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB903_PO.cs:126`、`:212-221` | **高** |

### E7 `ExecuteNonQuery` 回傳值被常數蓋掉

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E7.1 | `OFDB718`:`k = Convert.ToInt32(...); k = 1;` | 實際影響 0 列也會 commit 並回報「成功 N 筆」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:134-135` | **高** |
| E7.2 | `OFDB721`:同一行寫法 | 同上 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB721_PO.cs:134-135` | **高** |

### E8 交易與 rollback 的破口

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | `OFDB718` 的 `catch` 沒有 `tran.Rollback()`,只靠 `finally` 的 `Dispose` | 與配對的 `OFDB721` 不一致(`:157` 有 rollback) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB718_PO.cs:155-159` | 中 |
| E8.2 | `OFDB921.BeforeExecuteCheck` 的 `catch` 對 **恆為 null** 的 `tran` 呼叫 `Rollback()` | `catch` 自己丟 NRE,原始例外被完全遮蔽 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:104`、`:139` | **高** |
| E8.3 | 12 支同時開 `dbTA` 與 `dbPTPF` 兩個交易,commit 分兩次 | 一邊成功一邊失敗就資料不一致 | 例 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1054-1055`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:174-175` | 中 |
| E8.4 | `OFDB704` / `OFDB751` / `OFDB950` 完全沒有交易 | 匯入中途失敗會留半筆 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:50-75`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB751_PO.cs:54-79` | 中 |
| E8.5 | `OFDB716` 建了一條 `cnptpf` 連線(而且是從 `dbTA` 建的)之後從未使用也未關閉 | 每執行一次洩一條連線 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:127` | 中 |
| E8.6 | `CommandTimeout = 0`(無限等)出現在 16 支 | 大量資料時整個 client 卡死,使用者只能砍行程 | 例 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:68`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:53`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB733_PO.cs:52` | 中 |

### E9 寫死常數與位置取參數

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E9.1 | `f_TA_IsFundClose(:FUND_ID, …, '2', '0')` 後兩個位置參數是魔術值,無註解 | 改函式語意時找不到呼叫端 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB715_PO.cs:205` | 中 |
| E9.2 | `OFDB704.GetMEDIA_NO` 把 `FUND_ID` 寫死成 `"ALL FUNDS"` | 單一基金的媒體設定永遠取不到 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB704_PO.cs:106` | 中 |
| E9.3 | `OFDB701` 對郵局的特例寫死銀行代碼 `"700"` | 換代碼要改程式 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1021` | 低〔客戶特定〕 |
| E9.4 | `OFDB901` 用 `Substring(0,11)` + `Substring(11,4)` 拆批號 | 格式一變就越界 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:73` | 中 |
| E9.5 | `OFDB901` 輸出檔的 trailer 寫死 `"3########V011100008160170158"` | 外部格式一改就要改程式 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB901.cs:196` | 中〔客戶特定〕 |
| E9.6 | `OFDB950` 四種記錄長度(170 / 119 / 248 / 135)與所有欄位位移全部寫死在 UI | 檔案格式一改要重新部署 UI 組件 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:86`、`:120`、`:146`、`:183`、`:102`、`:163` | 中 |
| E9.7 | `OFDB703` 的錯誤訊息寫死另一支畫面代號 `OFDB301` | 畫面改號要 grep 訊息字串 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1583` | 低 |

### E10 字串串接進 SQL

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| E10.1 | `OFDB701` 兩處 `"... WHERE BATCH_ID = '" + strBATCH_ID + "'"` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:1069`、`:1141` | 中 |
| E10.2 | `OFDB701` / `OFDB702` 的 `f_TA_GetBankHQ(...) = '" + strAgentBank + "'` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:346`、`:352`;`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB702_PO.cs:442`、`:448` | 中 |
| E10.3 | `OFDB703` 銀行代碼串接,而且 `=` / `<>` 兩處連引號都沒有 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1406`、`:1411`、`:1416` | **高** |
| E10.4 | `OFDB731` 基金代碼串接 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:446-447` | 中 |
| E10.5 | `OFDB753` 的 `F_TA_SPLITWORDS('" + strFUND_ID + "')` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB753_PO.cs:76` | 中 |
| E10.6 | `OFDB901` 的 `TRADE_NO='{0}'` 與 `BATCH_ID <> '{0}'` 用 `string.Format` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:67`、`:99` | 中 |
| E10.7 | `OFDB691` 全部的 `UPDATE` 都用 `sb.AppendFormat(" UPDATE ... SET x='{0}' ", …)` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:173`、`:200`、`:203`、`:248`、`:275`、`:320`、`:347` | **高** |

### E11 例外被吞 / fail-open / fail-closed

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E11.1 | `OFDB703.CheckALLOT_CLS` 的 `catch` 把 `ReturnCode` 設成 `false`,而 UI 只在 `true` 時擋 | **`CTL012` 查詢一出錯,關帳檢核整個消失,扣款送件照跑** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1587-1591` + `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB703.cs:969-972` | **高** |
| E11.2 | `OFDB871.Check_DATA` 的 `catch` 吞掉例外後 `return -1`(= 已存在) | DB 出錯 = 一律判定已申報過,而且不說為什麼 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:432-437` | **高** |
| E11.3 | `OFDB731.SaveFile` 是 `catch { return false; }` —— 完全空的 catch | 磁碟滿 / 權限不足 / 路徑太長全部被吞成「存檔失敗」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:514-517` | **高** |
| E11.4 | `OFDB913` 的 `catch` 連 `CommonExceptionBlocker.HandleBusinessException` 都沒有 | 例外不進任何 log | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:133-138` | **高** |
| E11.5 | `OFDB911` / `OFDB912` / `OFDB921` / `OFDB691` 的 `catch` 把訊息設成空字串 | 使用者看到「失敗」兩個字沒有任何線索 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB911_PO.cs:113`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB912_PO.cs:111`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:83`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:109` | 中 |
| E11.6 | `OFDB921.BeforeExecuteCheck` 查無資料時 `Result` 被清空而不補列 | 呼叫端讀 `Result[0]` 會越界 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB921_PO.cs:131-135` | 中 |

### E12 迴圈與狀態機

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12.1 | `OFDB913` 的 `strStatus` 宣告在迴圈外,`if/else if` 鏈沒有 `else` | 未知狀態的列會被寫成**上一筆的狀態** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:65`、`:90-101` | **高** |
| E12.2 | `OFDB871` 的 `strPreID` 用來判斷「換人了就先 DELETE」,但兩個迴圈共用同一個變數且中間沒重設 | FSA 迴圈第一筆若 `FSA_ID_NO` 剛好等於 CLB 最後一筆的 `CLB_ID_NO`,那筆的 DELETE 會被跳過 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB871_PO.cs:75`、`:174`、`:347` | 中 |
| E12.3 | `OFDB731.ImportDataToVDB` 兩次呼叫 `mDir.GetFiles("*.txt")`,而且不篩本次上傳的檔名 | 目錄殘檔會被一起匯入;兩次之間目錄變動會越界 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:540`、`:546` | **高** |

### E13 複製貼上的分身

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E13.1 | `OFDB702.designer.cs` 有 6,319 行,其中約 4,800 行是基金主檔維護畫面的頁籤(保本型 / 手續費 / 收益分配 / 郵匯費) | 開這支畫面要建上千個用不到的控件;改基金主檔畫面的人不會知道這裡有一份 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB702.designer.cs:2985`、`:4682`、`:5128`、`:5358`、`:5495`(對照 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.designer.cs` 只有 969 行) | **高** |
| E13.2 | `PrepareExecute` 四份逐字複本 | 修一份不會修到另外三份 | 見 E1.1 | **高** |
| E13.3 | `ExportDataList` 樣板在 `716` `717` `722` `752` `753` `755` `756` 七支裡幾乎逐字相同,但失敗處理各不相同 | 同一段邏輯七種行為 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB716_PO.cs:124`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB717_PO.cs:305`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB753_PO.cs:141` | 中 |
| E13.4 | `OFDB691` 同時存在 `MSSQL/OFDB691_PO.cs`(整支註解)與 `Oracle/OFDB691OracleDao.cs`,兩份都編譯 | 找程式時容易看錯版本 | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB691_PO.cs:13`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:14` | 中 |

### E14 中繼資料 / 編碼

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E14.1 | `OFDB691` 的 `App.config` section 裡 `SelectedPlugin="OFDB690"` | 設定值指到另一支畫面 | `Dev/ATLAS.EC/Source/UI/UI.EC/App.config:235` | 中 |
| E14.2 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB701.cs` 與 `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB702.cs` 是 **cp950**,同專案其餘 `.cs` 都是 UTF-8 with BOM | 用 UTF-8 工具開會亂碼;git diff 全檔變動 | 逐檔偵測結果 | 中 |
| E14.3 | `DB/SP/S_OTA_OFDB903_EXE.sql` 是 cp950 | 同上 | 逐檔偵測結果 | 低 |
| E14.4 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config` 裡有明碼連線字串(含帳號與密碼)與主機名 | **設定檔洩漏憑證** —— 本文只記位置不抄值;這是 `architecture.md §8.7` 那條的另一個實例 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:10-11` | **高** |
| E14.5 | 同一支檔案裡 `dataConfiguration defaultDatabase` 被設成 `Logging` 而不是 `TA` | 若真的被讀到,預設資料庫是錯的 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/App.config:61` | 低 |

### E15 整組跑不起來的死碼

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| E15.1 | `OFDB706` / `OFDB731` / `OFDB732` / `OFDB733` / `OFDB734` 五支繼承 `BasicEVAPO`,`dbTA` 恆為 null,且整支是 T-SQL | §0.2 第三件事、§6.3.4;`architecture.md §3.1.1` | **高** |

### E16 這些看起來像 bug,其實不是

| 觀察 | 為什麼不是 bug |
|---|---|
| 22 支 PO 不宣告 `xTableMapping` | B 型批次的正常寫法(`architecture.md §6.4`),輸出是 DB 狀態或檔案,不是資料集 |
| `OFDB871` 在 `Execute` 裡重指派 `MasterTable` | 雖然醜,但每次進 `Execute` 都會先重設,不會吃到上一次的值 |
| `S_OTA_OFDB903_EXE` 沒有 `COMMIT` | 這是正確的 —— 交易由 C# 端管(§6.8) |
| `TRP80xA` 用 `DEL_YN` 軟刪除而不是真刪 | 集保媒體要保留歷史,是刻意的 |
| `OFDB950` 不碰資料庫 | 它的資料來源是外部檔案,設計如此;問題在它被歸成 B 而不是 R |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 OFD 批次第 4 片 35 支,回答三個必答題(`700` 系列是流水線、`715`–`722` 是四對、`751`–`757` 無關;`OFDB901` 與 `OFDB707` 無關;35/35 人工觸發無排程無 Remoting),補 `ofdb.md` 的 `CHG_UPD_DTTM` 第四種哨兵寫法,附錄 E 收 69 條缺陷(高 26 條)。 |

由 build_doc.py v2.0.0 於 2026-09-15 14:52 產生 · 標題 107 · 圖 6 · 表格 74 · 程式錨點 444 · § 連結 78 · 引用檢查：畫面 38（缺 0） · Table 39（缺 0） · SP 1（缺 0） · Report 1（缺 0） · 結果集 23（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/ofdb5.md
============================================================

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
