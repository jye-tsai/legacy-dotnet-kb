<!-- 由 tools/build_copilot_kb.py 從 modules/ofdb4.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
