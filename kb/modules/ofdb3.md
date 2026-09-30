<!-- 由 tools/build_copilot_kb.py 從 modules/ofdb3.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

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
