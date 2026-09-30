<!-- 由 tools/build_copilot_kb.py 從 modules/ofdi2.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFDI2 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先讀 §0.2 的「三條軌」那張表——本片 38 支橫跨三個專案,不先把軌搞清楚,後面每一節都會看成亂碼。要動手改某支的人查 §3 清冊定位再跳 §5。急著知道哪裡咬人的翻附錄 E,**本片的頭號地雷是 §5.1 那個 `NVL(TRIM(:P), 欄)` 樣板**。

> ⚠ **OFDI2 不是一個業務模組,是一份切片**,承接 `ofdi1.md`。涵蓋 `Dev/ATLAS.OTA.Query` 的 24 支 I 畫面 + `Dev/ATLAS.EC.Query` 的 13 支 I 畫面 + `Dev/ATLAS.OFD` 的孤兒 M 畫面 `OFDM287` 一支,共 **38 支**。名稱 `OFDI2` 為**推測**。

> ⚠ **本片與 `ofdi1.md` 最大的差異**:`ofdi1.md` 那 35 支是「一個專案內的六條業務線」;本片 38 支是**同一段業務被三條技術軌切成三份**。看懂切分方式比看懂任何單一支畫面重要。

> ⚠ **本片有 6 支是死的**(檔案在、不在 csproj、PO 整檔被註解),另有 15 支 PO 是**全檔註解的屍體**仍掛在 csproj 上。不要把它們當現行行為讀,見 §0.4。

> ⚠ **〔客戶特定〕**:基金短線交易費率、通路代碼 `CHANNEL_CD` / `AGENT_CODE` 編碼、電子交易來源碼 `SOURCE_CD`、`CTL014` 的 `SourceType` 編號為本站台的值。

> ⚠ **〔共用〕**:`OFD081` / `OFD081A`(基金主檔)、`OFD062`(基金公司)、`OFD601`(受益人基本資料)、`OFD606A`、`BMS001A`、`FSK003`(幣別)、`CTL014`、`OFD019A`(銀行)幾乎每支都讀,改欄位會同時打到本片十幾支畫面(見 §8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §5`、畫面型別四種看 `architecture.md §6`。**不要整份讀**。 I 畫面與 M 畫面的通則差異看 `ofdi1.md §0`,本文不重複,只寫**本片的例外**(§0.5)。

## 0. 系統邊界與角色

### 0.1 先破除三個會浪費半天的假設

動手前先把三件事釘死,否則檔案都找不到。

**假設一:PO 檔名照代號推。錯。** 本片兩個專案用**兩套命名**,而且資料夾名與組件名還故意不一致:

| 專案 | PO 資料夾 | csproj 檔名 | PO 檔名慣例 | 支數 |
|---|---|---|---|---|
| `ATLAS.OTA.Query` | `Source/PO/QueryPO.OFD/` ← **資料夾叫 OFD** | `QueryPO.OTA.csproj` ← **組件叫 OTA** | `<代號>_PO.cs` | 25 |
| `ATLAS.EC.Query` | `Source/PO/QueryPO.EC/Oracle/` | `QueryPO.EC.csproj` | **`<代號>OracleDao.cs`** | 8 |
| `ATLAS.EC.Query` | `Source/PO/QueryPO.EC/MSSQL/` | 同上 | `<代號>_PO.cs`(**全是屍體**) | 15 |

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/` 這個路徑最會騙人:**資料夾名是 `QueryPO.OFD`,但 csproj 是 `QueryPO.OTA.csproj`、namespace 是 `Vendor.Product.TA.QueryPO.OTA`** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:17`)。 Control / FormProxy / UI / Entity 五層同樣是「資料夾 `.OFD`、csproj `.OTA`」。這是從 `ATLAS.OFD.Query` 複製整棵樹改出來的痕跡,**沒改資料夾名**。

**假設二:`ofdi1.md` 說的「查詢畫面一半在串字串」在本片也成立。錯,而且錯很大。** 本片 `ATLAS.OTA.Query` 的 25 支 PO,`EVAStringHelper.AddParam` 的出現次數是 **0**; `db.AddInParameter` 的出現次數是 **125**。**這一片是全庫目前看過參數化最徹底的一片**(§5.2)。代價是換來另一種缺陷——`NVL(TRIM(:P), 欄)` 這個「空條件不過濾」的樣板本身會**無聲吃掉 NULL 資料列**(§5.1、附錄 E.1)。

**假設三:`OFDI601`~`OFDI615` 這段連號被「切成兩半」。錯,它不是切,是搬家搬到一半。** 見 §0.4,這是本片最大的結構問題。

### 0.2 三條軌:境內分戶 / 境外綜合帳戶 / 電子交易

`ofdb5.md` 與 `misc.md` 已查證 `ATLAS.OFD` 是**境內分戶軌**、`ATLAS.OTA` 是**境外綜合帳戶軌**, 分家方式是「畫面代號加後綴 + 表名去掉 `A`」。本片實測把第三條軌補上:

| 軌 | 專案根 | 業務定位(推測) | 資料表命名 | 本片支數 |
|---|---|---|---|---|
| **境內分戶** | `Dev/ATLAS.OFD` / `Dev/ATLAS.OFD.Query` | 國內基金、分戶式登錄 | 帶 `A`:`OFD081A` | 1(只有 `OFDM287`) |
| **境外綜合帳戶** | `Dev/ATLAS.OTA` / `Dev/ATLAS.OTA.Query` | 境外基金、綜合帳戶(omnibus) | **不帶 `A`**:`OFD081` `OFD651` `OFD652` | 24 |
| **電子交易** | `Dev/ATLAS.EC` / `Dev/ATLAS.EC.Query` | 網路 / 語音下單、對帳與軌跡 | 帶 `A`,且多 `LOG600` 系列軌跡表 | 13 |

**關鍵證據:同一個業務概念在兩條軌上是兩張表。** `OFDI612A`(境外軌)查 `OFD651` / `OFD652`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:127-129`); `IPJI612`(電子交易軌)查 `OFD651A` / `OFD652A` / `OFD653A`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:172-176`)。 **`OFD651` 與 `OFD651A` 就是境外 vs 電子交易的同一張表的兩個版本**,和 `ofdb5.md` 記的「去 `A`」規則方向一致 ——只是那篇寫的是「境內有 `A`、境外無 `A`」,本片證實**電子交易軌也用帶 `A` 的那一套**,也就是說: **帶 `A` 的表是「原本那張」,不帶 `A` 的是境外軌另開的一份。**〔假設〕依據是本片 `OTA.Query` 25 支 PO 完全不碰任何帶 `A` 的 `OFD6xx` 表, 而 `EC.Query` 8 支 live PO 完全不碰任何不帶 `A` 的 `OFD6xx` 表——兩邊表名集合**零交集**,不是巧合。

`IPJI620` 是這條規則最漂亮的一個證明:它一支就讀 `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` 五張表 (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI620OracleDao.cs:39-303`), 而境外軌的 `OFDI601`~`OFDI605` 是**一支畫面查一張 `OFD611`~`OFD615`** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:74-77`)。 **同一組五張表,境外軌切成五支畫面、電子交易軌合成一支多頁籤畫面。**

### 0.3 本片 38 支涵蓋哪些業務線

切片依據是專案資料夾,不是業務,所以本片內部仍是**七條互不相干的業務線**:

| # | 業務線 | 畫面 | 支數 | 主要表 |
|---|---|---|---|---|
| 1 | **境外基金申購 / 贖回 / 轉換 單據查詢** | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 5 | `OFD620` `OFD621` `OFD651` `OFD652` `OFD653` `OFD663` `OFD664` `OFD666` `OFD667` |
| 2 | **境外基金作業參數 / 費率主檔查詢** | `OFDI601` `OFDI602` `OFDI603` `OFDI604` `OFDI605` | 5 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615` |
| 3 | **對帳單 / 通知書 產製紀錄查詢** | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` | 5 | `OFD223` `OFD255` `OFD224` `OFD256` |
| 4 | **客戶 / 帳戶 / 稅務資料查詢** | `OFDI002` `OFDI071A` `OFDI072B` `OFDI283A` | 4 | `OFD105` `OFD309` `OFD303` `OFD281` `OFD283` |
| 5 | **定期定額 / 標的組合查詢** | `OFDI531` `OFDI553` `OFDI554` `OFDI563` `OFDI564` | 5 | `OFD535` `OFD536` `OFD551` `OFD552` `OFD554` `OFD555` `OFD563` `OFD564` |
| 6 | **電子交易(網路 / 語音)軌跡與對帳** | `IPJI612` `IPJI613` `IPJI614` `IPJI620` `IPJI630` `OFDI607` `OFDI608` | 7 | `OFD601` `LOG600` `LOG601` `LOG602` `OFD607A` 與 `OFD6xxA` 全家 |
| 7 | **已停用的電子交易舊查詢** | `OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` | 6 | (無,PO 全註解) |
| — | **孤兒 M 畫面** | `OFDM287` | 1 | 見 §4 |

### 0.4 `OFDI601` 到 `OFDI615`:不是切成兩半,是搬家搬到一半

這是本片最大的結構問題,必答問題 1 的答案。**先看三個事實:**

**事實一:`EC.Query` 有完整的 `OFDI601` 到 `OFDI615` 十五支六層,一支不缺。** UI / Pxy / Ctl / Model.xsd / View.xsd 全在 (`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/`、 `Dev/ATLAS.EC.Query/Source/Entity/QueryDataEntity.EC/`)。 **所以這一段連號原本整段住在 `EC.Query`,不是從一開始就分兩邊。**

**事實二:`EC.Query` 那十五支 PO 全部被整檔註解掉,一行沒留。** `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI601_PO.cs:19`、 `OFDI602_PO.cs:17`、`OFDI603_PO.cs:18`、`OFDI604_PO.cs:19`、`OFDI605_PO.cs:19`、 `OFDI606_PO.cs:18`、`OFDI607_PO.cs:19`、`OFDI608_PO.cs:17`、`OFDI609_PO.cs:17`、`OFDI610_PO.cs:17`、 `OFDI611_PO.cs:17`、`OFDI612_PO.cs:17`、`OFDI613_PO.cs:17`、`OFDI614_PO.cs:15`、`OFDI615_PO.cs:15` ——每一支的 class 宣告行都長這樣(以 `OFDI612` 為例):

```
//    public class OFDI612_PO : BasicEVAPO
```

連 `using` 都被註解(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI612_PO.cs:1-14`)。 **而這十五支屍體仍然全部掛在 csproj 上**(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`), 編譯得過只因為整檔沒有任何有效 token。這是本片第一條缺陷(附錄 E.11)。

**事實三:`EC.Query` 的 Control 層 csproj 只收 8 支,其餘 13 支 Ctl 檔在磁碟上但不編譯。** `Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/QueryControl.EC.csproj:108-115` 只列 `IPJI612` `IPJI613` `IPJI614` `IPJI620` `IPJI630` `OFDI607` `OFDI608` `OFDI641` 八支的 `_Ctl.cs`。 `OFDI601_Ctl.cs` 到 `OFDI615_Ctl.cs`(扣掉 607 / 608)這 13 支**不在 csproj**, 而且它們的內容還在 `new OFDI601_PO()`(`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/OFDI601_Ctl.cs:34`) ——一個已經被註解掉、根本不存在的型別。**放回 csproj 就是編譯錯誤**,不是能跑的程式。

**把三個事實接起來,故事是這樣的(〔假設〕,依據見下):**

| 階段 | 發生什麼 | 證據 |
|---|---|---|
| 1 MSSQL 時代 | `OFDI601` 到 `OFDI615` 十五支住在 `EC.Query`,PO 繼承 `BasicEVAPO`,用 `SystemConfigurationSource` + `DatabaseProviderFactory` 取 `TA` 連線 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI612_PO.cs:17,24-27`(註解內) |
| 2 境外軌分家 | 業務切出「境外綜合帳戶」,這段查詢跟著搬到 `ATLAS.OTA.Query` | `OTA.Query` 的 PO 標頭寫 `Created on: 2023/08/28`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:1-6`) |
| 3 Oracle 改寫 | 新軌整支重寫成 Oracle 語法,加 `PODbType` 屬性與 `Database("TA", DbServerType.Oracle)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:28-30` |
| 4 撞名改後綴 | `OFDI612` / `613` / `614` 在 `EC.Query` 已存在,新軌加 `A` 避開,成為 `OFDI612A` / `613A` / `614A` | 同號三對,見 §5.5 |
| 5 舊軌拆一半 | 舊 PO 整檔註解、Ctl 退出 csproj,但 UI / Pxy / xsd / PO 檔本體**都沒刪** | 事實二 / 三 |
| 6 沒搬完 | `OFDI606` `OFDI609` `OFDI610` **兩邊都沒有活的實作**,功能等於消失 | `OTA.Query` 無此三支;`EC.Query` 三支 PO 全註解 |
| 7 兩支留下 | `OFDI607` `OFDI608` 走**第三條路**:留在 `EC.Query`,但改寫成 `OracleDao` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:15` |

所以**「橫跨兩個專案」的正確描述是:一段連號的查詢群在境外軌分家時被整段搬走,搬到 10 / 15, 剩下 5 支中 2 支原地改寫、3 支直接爛在原地。** 不是設計,是遷移殘留。

**這對維護的意義**:

| 你想做的事 | 實際結果 |
|---|---|
| 改 `OFDI612` 的查詢條件 | 改到屍體,線上完全無感——要改的是 `OFDI612A` |
| 把 `OFDI609` 加回選單 | 加不回來,PO 已註解、Ctl 不在 csproj,得整支重寫 |
| 以為 `OFDI611` 在 `EC.Query` 跑 | 跑的是 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs` |
| 搜尋 `OFDI613` 找不到 bug | 搜到的是 `EC.Query` 那份註解,真正跑的叫 `OFDI613A` |

### 0.5 本片相對 `ofdi1.md` 通則的例外

`ofdi1.md §0` 那張 I vs M 對照表是本片的前提,以下只列**本片打破的格**:

| `ofdi1.md` 的結論 | 本片實測 | 差在哪 |
|---|---|---|
| UI 基底一律 `xOneStepProcessForm` | **成立**,`OTA.Query` 25 支全中(`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI601.cs:16`) | 無例外 |
| PO 基底三派並存(無基底 / `BaseEVADaoPO` / `BasicEVAPO`) | **本片 live 的 33 支全部是「無基底」**,只實作自己的 `I<代號>_PO` 或 `I<代號>` 介面 | **更極端** |
| `BasicEVAPO` 是地雷 | 本片 `BasicEVAPO` 出現 15 次,**全部在被註解的屍體裡**(§0.4) | 地雷已被埋起來 |
| `MasterTable` 宣告 0 支 | **成立**,37 支查詢畫面 0 支 | 無例外 |
| 四眼 13 欄 0 個 | **不成立**,`OFDM287` 是 M 畫面,有完整四眼(§4) | **本片唯一例外** |
| 寫入路徑 0 條 | **不成立**,`OFDM287` 有 `Update`(§4) | **本片唯一例外** |
| xsd 是結果集形狀,根節點等於畫面代號 | 成立於 37 支;`OFDM287` 的 Model 根節點是實體表 | 同上一格 |
| 條件組法四派,字串串接 13 / 35 | **本片字串串接 0 / 33**(§5.2) | **完全相反** |

**一句話**:本片 37 支查詢畫面把 `ofdi1.md` 的通則推到極致(更沒基底、更沒四眼、更參數化), 而 `OFDM287` 那一支是整片唯一的反例,所以它單獨佔 §4。

### 0.6 使用角色與全域開關

| 項 | 內容 | 錨點 |
|---|---|---|
| 使用角色(推測) | 境外基金作業人員(業務線 1 / 2 / 5)、對帳與客服(業務線 3 / 4)、電子交易維運(業務線 6) | 由查詢條件與結果欄位反推 |
| 權限控管 | **本片 37 支查詢 PO 內完全沒有權限檢核**,不像 `ofdi1.md` 的 `OFDI058B_PO.CheckPower()`;權限只靠選單層 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/` 全數無 `CheckPower` |
| 全域開關 | 無。本片沒有任何 `app.config` / 參數表驅動的行為分支 | — |
| 連線 | `OTA.Query` 全部 `new Database("TA", DbServerType.Oracle)`;`EC.Query` live 8 支同樣走 Oracle | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:30` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFDI2 全景:境外綜合帳戶軌 24 支、電子交易軌 13 支、境內分戶軌 1 支
圖中文字:ATLAS.OTA.Query 境外綜合帳戶軌:24 支,全部 Oracle 參數化 / OFDI611 612A 613A 614A 615 / 申購 贖回 轉換 定額 契約異動 / OFDI601 到 OFDI605 / OFD611 到 OFD615 參數主檔 / OFDI051 052 055 056 057 / 對帳單 通知書 產製紀錄 / OFDI002 071A 072B 283A / 客戶 控管 配息 / OFDI531 553 554 563 564 / 定期定額 授權 匯款 / OFD081 OFD062 FSK003 / 基金 公司 幣別(不帶 A) / BMS001A OFD019A CTL014 / 受益人 銀行 代碼(共用) / ATLAS.EC.Query 電子交易軌:7 支活的 + 6 支死的 / IPJI612 613 614 620 630 / 網路下單軌跡與對帳 / OFDI607 OFDI608 / LOG600 到 LOG602 變更軌跡 / OFDI606 609 610 612 613 614 / 不在 csproj,PO 全註解 / OFD6xxA OFD65xA OFD67xA / 電子交易軌的表(帶 A) / ATLAS.OFD 境內分戶軌:本片只收到一支孤兒 M / OFDM287 / OFD283A 配息給付維護 + 四眼 / OFD283A OFD281A OFD081V / 境內軌的表(帶 A) / OFDI283A 查的是 OFD283 / 同名不同物,見 5.6 / 三軌共同的地雷:NVL(TRIM(:P), 欄) 空條件樣板 / 欄位是 NULL 的資料列 / NULL = NULL 得 UNKNOWN / 不進結果集 / 使用者看到「查無資料」 / 沒有任何提示 / 過濾(無提示),22 支中招
```

*圖:圖 1 OFDI2 全景。橘框=本片的畫面;灰虛框=被讀但不歸本片管的上游表;黑框=在磁碟上但不編譯的死碼;紫框=風險點。三條軌之間沒有任何程式呼叫,只靠表名的 A 後綴規則區分彼此。最下面那一列不是某一支的問題,是三軌共用的 SQL 樣板缺陷。*

### 1.2 三條軌的分工與 `OFDI6xx` 跨專案切分

(圖由 `ofdi2.figs.py` 注入,對應 §2)

這張是本片的招牌圖。要一句話帶走的話:**`OFDI601` 到 `OFDI615` 這段連號不是被「切」成兩半,是「搬」到一半。** 細節見 §0.4 的五階段表與 §5.5 的逐對 diff。

### 1.3 四眼、批次報表、一日作業

三節都不畫。`OFDM287` 是本片唯一的 M,它沒有任何客製階段動作,照 `architecture.md §3` 的通用四眼圖讀即可(卡控寫在 §4); 本片無 B 也無 R(§6 §7);查詢畫面不參與排程,沒有時間軸可畫。

### 1.4 依 PO 基底與條件組法分群

(圖由 `ofdi2.figs.py` 注入,對應 §3)

### 1.5 最重的一支:`OFDI553` 的查詢流程與過濾點

(圖由 `ofdi2.figs.py` 注入,對應 §5)

### 1.6 跨模組:本片讀的表是誰建的

(圖由 `ofdi2.figs.py` 注入,對應 §8)

## 2. 資料模型

```text
[圖] 三條軌的分工與 OFDI6xx 跨專案切分的五個階段
圖中文字:第一階段 MSSQL 時代:OFDI601 到 OFDI615 十五支整段住在 EC.Query / EC.Query 六層齊全 / PO 繼承 BasicEVAPO,走 MSSQL / OFDI601 到 OFDI615 / 一支畫面一個業務,連號無缺 / MSSQL 資料庫 / DatabaseProviderFactory 取 TA / 第二階段 2023 年:境外軌分家,整段搬到 OTA.Query 並改寫 Oracle / 搬走 10 支 / 601 到 605 · 611 · 615 / 撞號改後綴 3 支 / 612 613 614 變 612A 613A 614A / 原地改寫 2 支 / OFDI607 OFDI608 變 OracleDao / 第三階段 收尾沒做完:舊軌留下屍體,三支功能直接消失 / PO 整檔註解 15 支 / 仍掛在 QueryPO.EC.csproj 上 / Ctl 退出 csproj 13 支 / 檔案還在,內容 new 一個不存在的型別 / OFDI606 609 610 蒸發 / 兩邊都沒有活的實作 / 結果:同號三對分屬兩專案,但根本不是同一個查詢 / OFDI612A 境外 / 查 OFD651 OFD652 買回單據 / OFDI612 電子交易(死) / 查網路變更生效日,業務無關 / OFD612A 這張表 / 由 IPJI620 讀,跟兩者都無關 / 穩定成立的分身規則:畫面代號加後綴,表名去掉 A / OFDI071 查 OFD309A(境內) / OFDI071A 查 OFD309(境外) / OFDI072A 查 OFD303A(境內) / OFDI072B 查 OFD303(境外) / OFDI283 查 OFD283A(境內) / OFDI283A 查 OFD283(境外)
```

*圖:圖 2 本片招牌圖。上三列是 OFDI601 到 OFDI615 這段連號被切開的時間順序,第四列說明「同號三對」不是同一查詢的兩個軌、只是代號撞號,最後一列是真正穩定成立的境內外分身規則:畫面代號加後綴、表名去掉 A。*

### 2.1 本片沒有 `xTableMapping`,但有一支例外

`ofdi1.md §0` 的結論是「I 畫面的 `MasterTable` 宣告 0 支」。本片實測:

| 專案 | 支數 | `MasterTable` 宣告 | 取數方式 |
|---|---|---|---|
| `ATLAS.OTA.Query` | 24 | **0 支** | `dbTA.LoadDataSet(cmd, model.DataEntity, model.DataEntity.<代號>.TableName)` |
| `ATLAS.EC.Query`(live) | 7 | **0 支** | `db.LoadDataSet(cmd, resultVDB.DataEntity, resultVDB.DataEntity.<表>.TableName)` |
| `ATLAS.OFD`(`OFDM287`) | 1 | **有**:`this.MasterTable = new xTableMapping("OFD283A", "OFDM287")` | 框架代勞 |

`OFDM287` 那一行在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:32`。 **所以「本片有幾張實體主表」這個問題,只有 `OFDM287` 回答得出來,其餘 37 支只能從 `FROM` / `JOIN` 反推。**

### 2.2 結果集的形狀:三種命名,全部不是實體表

| 命名法 | 例 | 意義 | 支數 |
|---|---|---|---|
| **結果集名 = 畫面代號** | `model.DataEntity.OFDI612A.TableName`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:152`) | 最常見,`OTA.Query` 全部這樣 | 23 |
| **結果集名 = 別支畫面的代號** | `model.DataEntity.OFDI562.TableName`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93`) | **`OFDI563` 借用 `OFDI562` 的整套 xsd**,見 §2.4 | 1 |
| **結果集名 = 實體表名** | `resultVDB.DataEntity.OFD618A.TableName`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:109`)、`OFD673A`(`IPJI612OracleDao.cs:863`) | `EC.Query` 的舊寫法殘留 | 3 |
| **結果集名 = 另一個畫面代號 + 用途後綴** | `resultVDB.DataEntity.IPJI621_Master.TableName`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632`) | **`IPJI612` 的七個結果集全叫 `IPJI621_*`**,見 §5.8 | 1 |

最後一列值得單獨記住:**`IPJI612` 這支畫面的所有結果集都叫 `IPJI621_`**—— `IPJI621` 這支畫面在本庫**不存在**(`find Dev -name "IPJI621*"` 為 0 筆)。〔假設〕是 `IPJI621` 被併進 `IPJI612` 時沒改 xsd 的表名,依據是七個結果集(`IPJI621_Master` `IPJI621_Allot` `IPJI621_Redeem` `IPJI621_RSP` `IPJI621_RSPCHG` `IPJI621_STOPSET` `IPJI621_STOPCHG`)全部同一個前綴, 不像是打錯一次。

### 2.3 Model.xsd 與 View.xsd 的欄數(`OTA.Query` 24 支)

xsd 是**結果集形狀**,不是實體表形狀;欄位中文名取自 `msdata:Caption`。本片 **Model 與 View 欄數 24 支全部一致**,沒有 `ofdi1.md` 那種對不上的破口:

| 畫面 | 結果集表名 | Model 欄 | View 欄 | 對齊 |
|---|---|---|---|---|
| `OFDI002` | `OFDI002` | 13 | 13 | 是 |
| `OFDI051` | `OFDI051` | 43 | 43 | 是 |
| `OFDI052` | `OFDI052` | 51 | 51 | 是 |
| `OFDI055` | `OFDI055` | 40 | 40 | 是 |
| `OFDI056` | `OFDI056` | 45 | 45 | 是 |
| `OFDI057` | `OFDI057` | 59 | 59 | 是 |
| `OFDI071A` | `OFDI071A` | 10 | 10 | 是 |
| `OFDI072B` | `OFDI072B` | 12 | 12 | 是 |
| `OFDI283A` | `OFDI283A` | 64 | 64 | 是 |
| `OFDI531` | `OFDI531` | 38 | 38 | 是 |
| `OFDI553` | `OFDI553` | 50 | 50 | 是 |
| `OFDI554` | `OFDI554` | 44 | 44 | 是 |
| **`OFDI563`** | **`OFDI562`** | **25(借)** | **25(借)** | **沒有自己的 xsd** |
| `OFDI564` | `OFDI564` | 13 | 13 | 是 |
| `OFDI601` | `OFDI601` | 10 | 10 | 是 |
| `OFDI602` | `OFDI602` | 9 | 9 | 是 |
| `OFDI603` | `OFDI603` | 9 | 9 | 是 |
| `OFDI604` | `OFDI604` | 8 | 8 | 是 |
| `OFDI605` | `OFDI605` | 8 | 8 | 是 |
| `OFDI611` | `OFDI611` | 61 | 61 | 是 |
| `OFDI612A` | `OFDI612A` | 61 | 61 | 是 |
| `OFDI613A` | `OFDI613A` | 67 | 67 | 是 |
| `OFDI614A` | `OFDI614A` | 50 | 50 | 是 |
| `OFDI615` | `OFDI615` | 61 | 61 | 是 |

同資料夾還有 `OFDI562`(25 欄)與 `TRPI001`(19 欄、**兩張表 `TRPI001` + `TRP001`**), **兩支都不在本片 38 支名單內**,列出來只是避免下一個人以為漏掉。

### 2.4 `OFDI563`:全片唯一的四層畫面

`OFDI563` 在磁碟上**沒有 `OFDI563Model.xsd`,也沒有 `OFDI563View.xsd`**, `Dev/ATLAS.OTA.Query/Source/Entity/QueryDataEntity.OFD/` 與 `.../QueryUIEntity.OFD/` 兩個資料夾內都找不到。它整套借 `OFDI562` 的:

| 位置 | 內容 | 錨點 |
|---|---|---|
| PO 取數 | `model.DataEntity.OFDI562.TableName` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93` |
| Ctl 簽名 | `public OFDI562ViewVDB Select(OFDI562ViewVDB view)` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:42` |
| Ctl 搬資料 | `TransferVDBHelper.TransferTable(view.UIView.OFDI562, model.DataEntity.OFDI562, base.TransferEVAColumn)` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:58` |
| Ctl 委派型別 | `POActionDelegate<OFDI562ModelVDB>` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:87` |

**這不是 bug,是刻意共用**——`OFDI562`(匯款授權書查詢)與 `OFDI563`(授權申請查詢)結果欄位相同, 差別只在 `OFDI562_PO` 查 `OFD562`、`OFDI563_PO` 查 `OFD563` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:73-86`)。 **但它有後遺症**:改 `OFDI562` 的欄位會同時改到 `OFDI563` 的畫面,而 `OFDI563` 的任何檔名都不會出現在 grep 結果裡。嚴重度:中(見附錄 E.7)。

### 2.5 本片讀到的表總覽(依被讀支數排序)

只列 `FROM` / `JOIN` 真實出現的表;`SELECT` 子句內的欄位別名已濾掉。

| 表 | 被幾支讀 | 讀它的畫面 | JOIN 型 | 備註 |
|---|---|---|---|---|
| `OFD081` | 16 | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI071A` `OFDI072B` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | INNER / LEFT 混用 | 境外軌基金主檔,〔共用〕 |
| `OFD062` | 15 | `OFDI051` `OFDI055` `OFDI071A` `OFDI072B` `OFDI283A` `OFDI553` `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` | 多為 `FROM` 起點 | 境外基金公司,〔共用〕 |
| `FSK003` | 13 | `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` | **多為 INNER JOIN** | 幣別主檔,**漏一筆整列消失**(附錄 E.3) |
| `BMS001A` | 10 | `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI563` `OFDI564` `IPJI612` | INNER / LEFT 混用 | 受益人主檔,〔共用〕 |
| `OFD606A` | 10 | `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 全 LEFT JOIN | **境外軌卻用帶 `A` 的表名**,§2.6 的反例 |
| `OFD601` | 9 | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` `OFDI607` `OFDI608` `IPJI612` `IPJI630` | INNER / LEFT 混用 | **兩條軌共讀的唯一一張表** |
| `OFD019A` | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` | LEFT JOIN | 銀行分行 |
| `OFD199` | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` | LEFT JOIN | 活動代碼 `CAMPAIGN_CODE` |
| `OFD081A` | 3 | `IPJI612` `IPJI614` `IPJI620` | INNER / LEFT | 電子交易軌的基金主檔。**grep 會多抓到 `OFDI052`,那是別名不是表**,§2.6 |
| `CTL014` | 3 | `OFDI055` `IPJI612` `IPJI614` | `FROM` / LEFT | 系統代碼對照 |
| `COD006A` | 2 | `OFDI553` `OFDI554` | LEFT JOIN | 以 `CODE_SORT = 'A8'` 過濾 |
| `OFD020V` | 2 | `OFDI283A` `IPJI612` | LEFT JOIN | 分行 View |
| `OFD256` | 2 | `OFDI056` `OFDI057` | `FROM` | 同表兩支畫面,靠 `JOB_CD` 常數分流(§5.3) |
| `OFD551` | 2 | `OFDI553` `OFDI554` | `FROM` / INNER | 定期定額契約主檔 |
| `OFD651` | 2 | `OFDI612A` `OFDI613A` | INNER JOIN | 境外電子單據主檔 |

單支獨讀的表(每張只有一支畫面讀)另列於附錄 A。

### 2.6 表名 `A` 後綴規則的成立範圍與兩個反例

§0.2 提出「帶 `A` 的是境內 / 電子交易軌、不帶 `A` 的是境外軌」。**在 `OFD6xx` 這一段完全成立**:

| 概念 | 境外軌(`OTA.Query`) | 電子交易軌(`EC.Query`) |
|---|---|---|
| 作業參數 1 到 5 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615`(`OFDI601` 到 `OFDI605` 各讀一張) | `OFD611A` 到 `OFD615A`(`IPJI620` 一支全讀) |
| 申購單據 | `OFD620` `OFD621`(`OFDI611`) | `OFD620A` `OFD621A`(`IPJI612`) |
| 贖回單據 | `OFD651` `OFD652`(`OFDI612A`) | `OFD651A` `OFD652A`(`IPJI612`) |
| 轉換單據 | `OFD651` `OFD653`(`OFDI613A`) | `OFD651A` `OFD653A`(`IPJI612`) |
| 定期定額契約 | `OFD663` `OFD664`(`OFDI614A`) | `OFD661A` `OFD662A`(`IPJI612`) |

**六組對照、零交集**,這是 §0.2 那個〔假設〕的全部依據。

**但規則不是全庫通用的,本片就有一個明確反例:**

| 反例 | 事實 | 錨點 |
|---|---|---|
| `OFD606A` | 境外軌的 10 支畫面全部 LEFT JOIN 這張**帶 `A`** 的表取基金簡稱,而全庫沒有 `OFD606` 這張表 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:130` |

所以 §0.2 的規則要縮到「**`OFD6xx` 的單據與參數表這一段成立**」,不能推廣到所有主檔。

### 2.6.1 一個會害你誤判的陷阱:別名長得跟真表一樣

`OFDI052` 看起來像是「境外軌卻讀 `OFD081A`」的反例,**其實不是**。它的 `FROM` 寫的是:

```
FROM OFD255
INNER JOIN OFD081 OFD081A ON OFD255.FUND_ID = OFD081A.FUND_ID
 LEFT JOIN OFD081 OFD081B ON OFD255.SWITCH_FUND_ID = OFD081B.FUND_ID
INNER JOIN FSK003 FSK003A ON OFD255.FUND_CURRENCY = FSK003A.CRNCY_CD
 LEFT JOIN FSK003 FSK003B ON OFD255.SWITCH_FUND_CURRENCY = FSK003B.CRNCY_CD
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:119-123`。 **`OFD081A` / `OFD081B` / `FSK003A` / `FSK003B` 是別名,不是表名**—— 而 `OFD081A` 與 `FSK003A` 剛好是真實存在的別條軌的表名。所以 `grep -rn "OFD081A"` 會在這支檔案裡命中四次,四次全是假的。

同樣的坑還有兩處:

| 檔案 | 別名 | 真表 | 錨點 |
|---|---|---|---|
| `OFDI612A_PO` | `OFD019B` | `OFD019A` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:133` |
| `OFDI553_PO` | `OFD072A` | `MYOFD072A` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:156` |

第二個更惡劣:`LEFT JOIN MYOFD072A OFD072A`,**把一張 `MYOFD` 開頭的表別名成 `OFD072A`**, 而 `OFD072A` 這個代號在別的地方是畫面名(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI072A_PO.cs`)。一個字串同時是表別名與畫面代號,做影響分析時務必先看 `FROM` 再下結論。嚴重度:低(可讀性),但**極易誤判**(附錄 E.4)。

### 2.7 主鍵與四眼欄位

| 項 | 本片 37 支查詢畫面 | `OFDM287` |
|---|---|---|
| 主鍵宣告 | **無**。結果集 xsd 沒有 `xs:key` / `msdata:PrimaryKey` | 有,走框架 `dataid` |
| 四眼 13 欄 | **0 個**,沒有任何 `ENTRYID` / `VERIFYID` / `APPROVEID` 出現在 `SELECT` | **全套**,由 `xEVAStringHelper.AllEVAColumnsForSelect("OFD283A")` 一次帶出(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:121`) |
| `dataid` | 無 | 有,`SELECT OFD283A.dataid` 是第一欄(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:77`) |

### 2.8 狀態碼(從程式反推)

本片只有三處把狀態碼翻成中文,全部寫死在 SQL 的 `CASE WHEN` 裡,**不是查代碼表**:

| 欄位 | 值域 | 中文 | 錨點 |
|---|---|---|---|
| `OFD651.EC_REDEM_PCODE` | `'0'` / `'1'` / `'2'` / `'3'` / `'4'` | 輸入 / 處理中 / 轉入 / **(空字串)** / 刪除 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:100-101` |
| `OFD256.JOB_CD` | `'1'` / `'2'` | 贖回 / 轉換(不翻中文,直接當過濾條件) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123`、`OFDI057_PO.cs:133` |
| `OFD551.STOP_CD` | 走 `COD006A` 的 `CODE_SORT = 'A8'` | 由代碼表帶 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:161-162` |

第一列的 `'3'` 對應到**空字串**(`WHEN OFD651.EC_REDEM_PCODE = '3' THEN ''`), 其餘四個值都翻成「代碼:中文」。**`'3'` 是刻意留白還是漏寫,程式裡看不出來**, `OFDI613A` 同一段 `CASE` 也照抄了這個空字串。嚴重度:低,但畫面上會出現空白欄位(附錄 E.8)。

### 2.9 與其他模組共用的表

見 §8。一句話版本:**本片沒有任何一張「自己的」表**——37 支查詢畫面讀的全部是別的模組維護的資料, 唯一有寫入語意的 `OFDM287` 改的 `OFD283A` 也同時被 `ATLAS.OFD.Query` 的 `OFDI283` 讀。

## 3. 畫面清冊

```text
[圖] 依 PO 基底與查詢條件組法分群
圖中文字:第一派 真參數化 26 支:NVL(TRIM(:P), 欄) + AddInParameter / OTA.Query 全部 24 支 / 無 PO 基底,只實作自己的介面 / IPJI613 IPJI614 / bind 變數 + F_FORMATSTRINGTOTABLE / 風險不是注入 / 是 NULL 欄位被無聲濾掉 / 第二派 混用 2 支:一半 bind 一半串字串 / IPJI612 / 1821 行,七個結果集,部分 bind / IPJI620 / 五個 cmd 併一次 LoadDataSet / 同一支內兩種寫法 / 改的人要逐段判斷 / 第三派 純字串串接 3 支:值與運算子都直接接進 SQL / OFDI607OracleDao / ID_NO 與 BF_NO 接運算子與值 / IPJI630OracleDao / ID_NO BF_NO EMAIL 各兩處,共六處 / OFDM287_PO / M 畫面,八個條件全串字串 / 第四派 全丟 SP 0 支:本片沒有任何一支呼叫預存程序 / 沒有 CommandType.StoredProcedure / 38 支掃描結果為零 / 唯一的外部程式是 TVF / F_FORMATSTRINGTOTABLE 拆多選字串 / 與 ofdi1 的 11 支全丟 SP 相反 / 本片 SQL 全部在 C# 裡 / PO 基底:本片 live 的 33 支全部無基底,BasicEVAPO 只活在註解裡 / 無基底 33 支 / 只實作 I 代號 _PO 或 I 代號 / BaseEVADaoPO 1 支 / 只有 OFDM287,因為它是 M / BasicEVAPO 15 次 / 全在 EC.Query 被註解的屍體內
```

*圖:圖 3 分群。橘框=該派的成員;紫框=該派帶來的風險;黑框=死碼或版控外。ofdi1 那片的四派分佈是「真參數化 9 / 全丟 SP 11 / 字串串接 13 / helper 2」,本片是「真參數化 26 / 混用 2 / 字串串接 3 / 全丟 SP 0」,分佈完全相反。*

### 3.1 維護 M

本片只有一支,`OFDM287`,詳見 §4。

| 代號 | 中文名(由控件標題反推) | 專案 | 六層齊不齊 | PO 基底 | 主表 | 在 csproj |
|---|---|---|---|---|---|---|
| `OFDM287` | 收益分配給付維護(推測) | `ATLAS.OFD` | **六層齊,但 Model 檔名是 `OFDM287Model.xsd.xsd`** | `BaseEVADaoPO` | `OFD283A` | 六層全在 |

### 3.2 查詢 I — `ATLAS.OTA.Query`(24 支)

**欄位說明**:PO 基底是剝掉 `//` 註解後的實際宣告;條件參數化四類取 `ofdi1.md §5.2` 的分法 (真參數化 / 全丟 SP / 直接字串串接 / 走會跳脫的 helper);結果集寫「xsd 表名(欄數)」; 匯出看 UI 有沒有設 `this.ExportGrid`;分頁全片皆無,不另列欄。

| 代號 | 中文名(反推) | PO 基底 | 主要查的表 | 條件參數化 | 結果集(欄數) | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `OFDI002` | 受益人資料變更查詢 | 無基底,`IOFDI002_PO` | `OFD105` | **真參數化**(4 bind) | `OFDI002`(13) | 有 | 六層全在 |
| `OFDI051` | 申購對帳單產製紀錄查詢 | 無基底 | `OFD223` `OFD062` `OFD081` `FSK003` | **真參數化**(5) | `OFDI051`(43) | 有 | 六層全在 |
| `OFDI052` | 贖回對帳單產製紀錄查詢 | 無基底 | `OFD255` `OFD081`×2 `FSK003`×2 | **真參數化**(5) | `OFDI052`(51) | 有 | 六層全在 |
| `OFDI055` | 申購交易通知書查詢 | 無基底 | `OFD224` `OFD062` `OFD081` `OFD012A` `BMS001A` `CTL014` `FSK003` | **真參數化**(4) | `OFDI055`(40) | 有 | 六層全在 |
| `OFDI056` | 贖回交易通知書查詢 | 無基底 | `OFD256` `OFD081` `BMS001A` `FSK003` | **真參數化**(5) | `OFDI056`(45) | 有 | 六層全在 |
| `OFDI057` | 轉換交易通知書查詢 | 無基底 | `OFD256` `OFD081` `BMS001A` `FSK003` | **真參數化**(5) | `OFDI057`(59) | 有 | 六層全在 |
| `OFDI071A` | 基金資料控制查詢(境外) | 無基底 | `OFD309` `OFD062` `OFD081` `SWPRODUCTSDETAIL`(別名 `PROG`) | **真參數化**(5) | `OFDI071A`(10) | 有 | 六層全在 |
| `OFDI072B` | 申贖控制碼查詢(境外) | 無基底 | `OFD303` `OFD062` `OFD081` | **真參數化**(11) | `OFDI072B`(12) | 有 | 六層全在 |
| `OFDI283A` | 收益分配明細查詢(境外) | 無基底 | `OFD281` `OFD283` `OFD062` `OFD081` `BMS001A` `OFD013` `OFD020V` `FSK003` | **真參數化**(9) | `OFDI283A`(64) | 有 | 六層全在 |
| `OFDI531` | 所得認列查詢 | 無基底 | `OFD535` `OFD536` `OFDV531` `OFD081` `BMS001A` `FSK003` | **真參數化**(4) | `OFDI531`(38) | 有 | 六層全在 |
| `OFDI553` | 定期定額契約查詢 | 無基底 | `OFD551` `OFD552` `OFD081` `BMS001A` `COD006A` `COD009` `MYOFD072A` `OFD019A` `OFD068A` `OFD199` `FSK003` `OFD062` `OFD019A` | **真參數化**(11),但 **`AND` / `OR` 缺括號**(§5.7) | `OFDI553`(50) | 有 | 六層全在 |
| `OFDI554` | 定期定額契約異動查詢 | 無基底 | `OFD554` `OFD555` `OFD551` `OFD081` `BMS001A` `COD006A` `OFD199` `FSK003` | **真參數化**(13) | `OFDI554`(44) | 有 | 六層全在 |
| **`OFDI563`** | 授權申請查詢 | 無基底 | `OFD563` `BMS001A` `OFD019A` | **真參數化**(3) | **`OFDI562`(25),借用** | 有 | **只有四層,無 Model / View xsd** |
| `OFDI564` | 匯款處理查詢 | 無基底 | `OFD564` `BMS001A` `OFD019A` | **真參數化**(3) | `OFDI564`(13) | 有 | 六層全在 |
| `OFDI601` | 基金交易付款方式參數查詢 | 無基底 | `OFD611` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI601`(10) | 有 | 六層全在 |
| `OFDI602` | 基金作業參數查詢 2 | 無基底 | `OFD612` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI602`(9) | 有 | 六層全在 |
| `OFDI603` | 基金作業參數查詢 3 | 無基底 | `OFD613` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI603`(9) | 有 | 六層全在 |
| `OFDI604` | 基金作業參數查詢 4 | 無基底 | `OFD614` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI604`(8) | 有 | 六層全在 |
| `OFDI605` | 基金作業參數查詢 5 | 無基底 | `OFD615` `OFD062` `OFD606A` | **真參數化**(4) | `OFDI605`(8) | 有 | 六層全在 |
| `OFDI611` | 境外申購單據查詢 | 無基底 | `OFD620` `OFD621` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD012` `OFD019A` `OFD199` `FSK003` | **真參數化**(6) | `OFDI611`(61) | 有 | 六層全在 |
| `OFDI612A` | 境外買回(贖回)單據查詢 | 無基底 | `OFD651` `OFD652` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD019A`×2 `FSK003` | **真參數化**(6) | `OFDI612A`(61) | 有 | 六層全在 |
| `OFDI613A` | 境外轉換單據查詢 | 無基底 | `OFD651` `OFD653` `OFD601` `OFD606A` `OFD062` `OFD081` `FSK003` | **真參數化**(6) | `OFDI613A`(67) | 有 | 六層全在 |
| `OFDI614A` | 境外定期定額契約查詢 | 無基底 | `OFD663` `OFD664` `OFD601` `OFD606A` `OFD062` `OFD081` `OFD199` `FSK003` | **真參數化**(6) | `OFDI614A`(50) | 有 | 六層全在 |
| `OFDI615` | 境外定期定額契約異動查詢 | 無基底 | `OFD666` `OFD667` `OFD601` `OFD606A` `OFD081` `OFD199` | **真參數化**(6) | `OFDI615`(61) | 有 | 六層全在 |

**這 24 支的一致性高到不像同一個系統的其他部分**:

| 面向 | 24 支的狀況 |
|---|---|
| PO 基底 | 24 / 24 無基底,只實作 `I<代號>_PO` |
| PO 方法簽名 | 24 / 24 是 `T GetData<T>(T mModel, params object[] args)` |
| 連線 | 24 / 24 `new Database("TA", DbServerType.Oracle)` + `[PODbType(DbServerType.Oracle)]` |
| 條件組法 | 24 / 24 真參數化,**零字串串接** |
| 取數 | 24 / 24 一次 `LoadDataSet`,單一結果集 |
| 結果回報 | 24 / 24 `AddResultRow(筆數>0, 筆數, "")`,**訊息一律空字串** |
| 例外處理 | 24 / 24 `AddResultRow(false, 0, ex.Message)` **接著** `CommonExceptionBlocker.HandleBusinessException(ex)` |
| UI 基底 | 24 / 24 `xOneStepProcessForm` |
| 匯出 | 24 / 24 設 `this.ExportGrid = this.ugrdResult` |
| 分頁 | **0 / 24**,全部一次撈完 |
| 作者與日期 | 檔頭 `Original author` 只有 `Jye`(8 支)與 `Kendra`(16 支),`Created on` 落在 2023/02 到 2023/09 |

最後一列是理解這一片的關鍵:**這 24 支是 2023 年同一批人、同一份樣板、七個月內一次做完的**, 所以缺陷也是整批的——不是零星的手滑,是樣板本身的問題(§5.1)。

### 3.3 查詢 I — `ATLAS.EC.Query`(13 支:7 活 6 死)

| 代號 | 中文名(反推) | PO 檔 | PO 基底 | 主要查的表 | 條件參數化 | 結果集(表名) | 匯出 | 在 csproj |
|---|---|---|---|---|---|---|---|---|
| `IPJI612` | 網路交易明細查詢(含退休試算) | `IPJI612OracleDao.cs`(**1821 行**) | 無基底,`IIPJI612` | `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` `OFD656A` `OFD657A` `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` `OFD601` `OFD601CHG` `OFD304A` `OFD138A` `OFD199A` `OFD020A` `OFD020V` `OFD081A` `BMS001A` `COD006` `CTL014` | **混用**(36 bind + 部分字串) | **`IPJI621_Master` 等 7 張 + `OFD673A`** | 無 | 六層在,**Model 叫 `IPJI612_9iModel.xsd`** |
| `IPJI613` | 基金設定查詢 | `IPJI613OracleDao.cs` | 無基底 | `OFD681A` `OFD682A` `OFD683A` `OFD601` `V_FUND` | **真參數化**(4) | `IPJI613` | 無 | 六層全在 |
| `IPJI614` | 拋轉資料查詢 | `IPJI614OracleDao.cs` | 無基底 | `OFD618A` `OFD081A` `CTL014` | **真參數化**(3)+ `F_FORMATSTRINGTOTABLE` TVF | **`OFD618A`**(實體表名) | 無 | 六層全在 |
| `IPJI620` | 網路交易彙總查詢(五類) | `IPJI620OracleDao.cs` | 無基底 | `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` `OFD081A` | **混用**(24 bind) | `IPJI620_Allot` `_Redem` `_RSP` `_BMS_CHG` `_Switch`(5 張) | 無 | 六層全在 |
| `IPJI630` | 網路開戶紀錄查詢 | `IPJI630OracleDao.cs` | 無基底 | `OFD601` `OFD601CHG` `OFD607A` | **直接字串串接**(6 處,0 bind) | `IPJI630_Master` + 裸 `DataSet` 的 `"OFD601"` | 無 | 六層在,**Model 叫 `IPJI630_9iModel.xsd`** |
| `OFDI607` | 受益人資料變更軌跡查詢 | `OFDI607OracleDao.cs` | 無基底,`IOFDI607` | `LOG602` `OFD601` `OFD607A` `CTL014` | **直接字串串接**(2 處 + 2 處日期,0 bind) | `OFDI607` | 無 | 六層全在 |
| `OFDI608` | 登入與密碼紀錄查詢 | `OFDI608OracleDao.cs` | 無基底,`IOFDI608` | `LOG600` `LOG601` `OFD601` `CTL014`(三次子查詢) | **直接字串串接**(2 處 + 2 處日期,0 bind) | `OFDI608` | 有 | 六層全在 |
| **`OFDI606`** | 受益人資料異動查詢(網路) | `MSSQL/OFDI606_PO.cs` | **整檔註解**(原 `BasicEVAPO`) | — | — | `OFDI606` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI609`** | 網路贖回查詢 | `MSSQL/OFDI609_PO.cs` | **整檔註解** | — | — | `OFDI609` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI610`** | 網路贖回查詢(2) | `MSSQL/OFDI610_PO.cs` | **整檔註解** | — | — | `OFDI610` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI612`** | 網路變更生效查詢 | `MSSQL/OFDI612_PO.cs` | **整檔註解** | — | — | `OFDI612` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI613`** | 網路開戶申請查詢 | `MSSQL/OFDI613_PO.cs` | **整檔註解** | — | — | `OFDI613` | 有 | **UI / Pxy / Ctl 不在 csproj** |
| **`OFDI614`** | 網路紀錄查詢 | `MSSQL/OFDI614_PO.cs` | **整檔註解** | — | — | `OFDI614` | 有 | **UI / Pxy / Ctl 不在 csproj** |

**注意兩個不對稱**:

1. 六支死畫面的 **PO 檔仍在 `QueryPO.EC.csproj` 上**(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`), **Model / View xsd 也仍在**,只有 UI / Pxy / Ctl 三層退出。也就是說:編譯產出的 DLL 裡**還帶著這六支的 typed DataSet**,只是沒人用。

2. 五支活的 `IPJI6xx` **一支都沒有匯出**,而六支死的全部有匯出。〔假設〕是 `IPJI6xx` 這批比較新、改走畫面內的明細彈窗(`IPJI612_P0` 到 `IPJI612_P5` 六個 `PopupForm`), 依據是 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI612_P0.cs:17` 起那六個彈窗類別。

### 3.4 批次 B

**本片無 B 畫面。** 原因:切片依據是 `*.Query` 專案,而 `*.Query` 專案底下**只放 I 畫面**—— `Dev/ATLAS.OTA.Query` 與 `Dev/ATLAS.EC.Query` 兩棵樹內沒有任何 `*B[0-9]*` 代號的檔。境外軌的批次在 `Dev/ATLAS.OTA`,不在本片。

### 3.5 報表 R

**本片無 R 畫面。** 同上,報表在 `Dev/ATLAS.OTA.Report` 與 `Dev/ATLAS.EC.Report`, 本片 38 支沒有任何一支產 `.rpt` 或呼叫 Report Service。

### 3.6 條件參數化四派的分佈(必答問題 4 的答案)

`ofdi1.md` 前一片 35 支分四派:真參數化 9 / 全丟 SP 11 / 直接字串串接 13 / 走會跳脫的 helper 2。 **本片 38 支的分佈完全相反:**

| 派別 | 支數 | 是誰 |
|---|---|---|
| **真參數化** | **26** | `OTA.Query` 全部 24 支(含 `OFDI563`)+ `IPJI613` `IPJI614` |
| **混用**(同一支內 bind 與串接並存) | **2** | `IPJI612` `IPJI620` |
| **直接字串串接** | **4** | `IPJI630` `OFDI607` `OFDI608` **`OFDM287`**(唯一的 M 畫面,§4) |
| **全丟 SP** | **0** | 無。本片 38 支沒有任何 `CommandType.StoredProcedure`,也沒有任何 `EXEC` / `CALL` |
| **走會跳脫的 helper** | **0** | 無。`EVAStringHelper.AddParam` 在本片出現 **0 次** |
| (不適用)死碼 | 6 | `OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` |

26 + 2 + 4 = 32,正好是本片 live 的 32 支(24 + 7 + `OFDM287`);另外 6 支是死碼,不分派。 **四支純串接的那一組就是本片全部的 SQL 注入風險面**,三支在 `EC.Query`、一支是 `OFDM287`。

**關於 `EVAStringHelper.AddParam` 的兩個多載**:任務指名要看的那個坑(4 參數版真參數化、3 參數版 `IN` 分支完全不跳脫,`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:346`,`IN` 分支在 `:373-374`) **在本片一次都沒出現**。本片 `OTA.Query` 用的是同一個類別的另一個方法 `SQLHelper.EVAStringHelper.GetParamValue(model, "欄名")`——**它只負責從 `model.Utility.Parameters` 撈字串值, 不組 SQL**,撈出來的值一律交給 `dbTA.AddInParameter` 當 bind 變數 (例:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:146-151`)。 **所以那個坑本片踩不到。** 真正的風險改成 §5.1 那個 `NVL` 樣板。

### 3.7 PO 基底統計(必答問題:幾支繼承 `BasicEVAPO`)

| 基底 | live 支數 | 說明 |
|---|---|---|
| 無基底 | **31** | `OTA.Query` 24 + `EC.Query` live 7 |
| `BaseEVADaoPO` | **1** | 只有 `OFDM287`,因為它是 M 畫面 |
| `BasicEVAPO` | **0 支 live** | 但**檔案內出現 15 次**,全部在 `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/` 那六支死畫面加另外九支同批屍體的註解裡 |
| (無 PO) | 6 | 六支死畫面 |

`ofdi1.md` 記的「繼承 `BasicEVAPO` 連查詢都 NRE」這條缺陷,**在本片不會發作**—— 唯一那 15 個 `BasicEVAPO` 全被 `//` 蓋住了。但反過來說:**如果有人把那些 PO 解除註解重新啟用,15 支會一次全炸**。

## 4. 維護畫面(M)— 本片只有一支

### 4.1 `OFDM287` — 全庫最後一支沒被任何模組篇提到的 M 畫面

必答問題 5 的答案。先講結論:**它不是死的,它是活的、六層齊全、全部在 csproj、有完整四眼, 前 24 篇沒碰到它純粹是因為它的 Model 檔名多了一個 `.xsd`。**

#### 4.1.1 為什麼前面 24 篇都漏掉它

`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/` 底下,它的 Model 叫:

```
OFDM287Model.xsd.xsd
OFDM287Model.xsd.xsc
OFDM287Model.xsd.xss
OFDM287Model.xsd.Designer.cs
```

**多了一層 `.xsd`**。全庫其他畫面一律是 `<代號>Model.xsd`。掃描器用 `*Model.xsd` 這個樣式收 Model,`OFDM287Model.xsd.xsd` 不符合,於是被判成「有 View 沒有 Model」—— `architecture.md` 那份清單正是這樣記的:**它被列在「5 支只有 View 沒有 Model」那一組**, 跟 `CMM_BFTypeList` `OFDI701` 等擺在一起,當成「改名沒改乾淨」的殘骸,**所以沒有人再回頭查它**。

實際上 View 那邊是正常的 `OFDM287View.xsd`(`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/OFDM287View.xsd`), csproj 也把 `OFDM287Model.xsd.xsd` 正常收了 (`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/DataEntity.OFD8.csproj:185-190,422-431`), 所以它編得出來、跑得動。**這是一個檔名 typo 造成的文件盲點,不是程式缺陷**——但代價是這支畫面到今天為止沒有任何文件。

#### 4.1.2 六層與基本事實

| 層 | 檔 | 關鍵事實 |
|---|---|---|
| UI | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:20` | `public partial class OFDM287 : xMaintainForm`,`this.TabPages = 2`(`:87`) |
| FormProxy | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM287_Pxy.cs:12` | `Basic_Pxy`,只覆寫 `Modify` 與 `Query` 兩個動作 |
| Control | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:13` | `BaseController`,`ModifyData` / `GetData` / `GetMaintainData` 三個方法 |
| PO | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:25` | **`BaseEVADaoPO`**,`[PODbType(DbServerType.Oracle)]`,`Database("TA", DbServerType.Oracle)` |
| Model | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM287Model.xsd.xsd` | 根節點是實體表形狀,不是結果集 |
| View | `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/OFDM287View.xsd` | 與 Model 同構 |

`MasterTable` 宣告在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:32`:

```
this.MasterTable = new xTableMapping("OFD283A", "OFDM287"); //主檔資料
```

**沒有 `DetailTable`**——單表維護。

#### 4.1.3 它管什麼(推測)

主表 `OFD283A` 是**境內分戶軌的收益分配(配息)給付明細**。SQL 撈的欄位說明了業務: `BAL_UNIT`(結餘單位)、`TOTAL_ASSIGN_AMT`(分配總額)、`GET_STATUS`(發放進度)、 `GET_WAY`(給付方式)、`BANK_BRH` / `REMIT_ACC_NO`(匯款帳戶)、 `SWITCH_FUND_ID` / `SWITCH_DATE` / `SWITCH_FEE_RATE` / `SWITCH_FEE` / `SWITCH_AMT`(配息轉申購)、 `POST_FEE` / `REMIT_FEE`(郵資與匯費,各拆公司負擔與銀行負擔)、`TOTAL_TAX_AMT`(扣繳稅額)、 `MAIL_ZIP` / `MAIL_ADDR`(寄送地址)、`DIV_PAY_DESK`(給付櫃檯) (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:77-121`)。

**與本片 `OFDI283A` 的關係是最容易搞混的一點**:

|  | `OFDM287`(本節) | `OFDI283A`(§5) |
|---|---|---|
| 專案 | `Dev/ATLAS.OFD`(境內分戶軌) | `Dev/ATLAS.OTA.Query`(境外綜合帳戶軌) |
| 主表 | **`OFD283A`** | **`OFD283`** |
| 搭配表 | `OFD281A` `OFD081V` `OFD020V` `BMS001A` | `OFD281` `OFD081` `OFD013` `OFD020V` `BMS001A` `FSK003` `OFD062` |
| 型別 | M,可改 | I,唯讀 |
| 四眼 | 有 | 無 |

**畫面代號 `OFDI283A` 的 `A` 跟表名 `OFD283A` 沒有任何關係**,`OFDI283A` 查的是不帶 `A` 的 `OFD283`。這是 §5.6 那份 `A` 後綴成因分析的核心證據之一。

#### 4.1.4 四眼與階段動作

`OFDM287_PO` 只掛三個事件,**全部是「取數前組 SQL」,沒有任何寫入階段的附加動作**:

| 事件 | 用途 | 錨點 |
|---|---|---|
| `BeforeSelect` | 查詢頁取數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:33,53-66` |
| `BeforeGetMaintainData` | 維護頁取單筆 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:34,276-289` |
| `BeforeGetToDoData` | 待辦(四眼待覆核清單)取數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:35,290-303` |

三個事件都呼叫同一個 `BuildMasterSQLString(model, isToDoString)`; 差別只在 `BeforeGetToDoData` 傳 `true`,多接一段 `xTableHelper.AppendToDoString("OFD283A", model)` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:266`)。四眼 13 欄由 `xEVAStringHelper.AllEVAColumnsForSelect("OFD283A")` 一次帶進 `SELECT` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:122`)。 `xEVAStringHelper` / `xTableHelper` / `BaseEVADaoPO` 的實作**無原始碼,從呼叫端反推**。

**沒有 `BeforeAdd` / `AfterVerify` / `AfterApprove` / `AfterReject`**—— 寫回完全交給 `BaseEVADaoPO.Update`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:52` 把它當委派丟給框架), PO 自己沒有一行 `UPDATE` 語句。

#### 4.1.5 它實際上只能改一個欄位

畫面上擺了二十幾個控件,但按下「修改」時只有一個欄位被搬回資料列:

```
private void OFDM287_BeforeModifyButtonClicked(object sender, CancelEventArgs e)
{
    OFDM287View.OFDM287Row Row = ((OFDM287ViewVDB)this.ProcessVDB).UIView.OFDM287[0];
    Row.MEMO = this.utxtMEMO.Text;
}
```

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253`。其餘欄位在 `OFDM287_ModifyDataLoad` 是**單向從資料列填進控件** (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:174-231`),沒有反向搬回。 `OFDM287_Ctl.ModifyData` 的 XML 註解也直說是「修改受益分配**備註**」 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM287_Ctl.cs:46`)。

**所以這支 M 畫面的實際能力是:查配息給付明細 + 改備註,其他都是唯讀展示。** 使用者若在畫面上改了金額或帳號欄位再按修改,**不會存進去,也不會有任何提示**—— 結果類型:**過濾(無提示)**。嚴重度:中(附錄 E.9)。

#### 4.1.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 「年度+期別」「分配基準日」「受益人 ID」「戶號」四組必須擇一輸入 | 四組全空 | **阻擋**(`e.Cancel = true` + `ValidateErrList.Show()`) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:124-138` |
| 進維護頁 | 停用刪除鈕 | 一律 | 記錄不擋(功能關閉) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:176` |
| 進新增頁 | 停用新增鈕 | 一律 | 記錄不擋(**等於不能新增**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:233-236` |
| 載入維護頁 | `GET_WAY == "3"`(配息轉申購)才顯示轉換相關金額,否則清空 | 給付方式不是 `'3'` | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:200-212` |
| 按修改前 | 只把 `MEMO` 搬回資料列 | 一律 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253` |
| 組查詢 SQL | 八個條件逐一 `if Rows.Contains(...)`,有才加 | 條件沒填 | 過濾(無提示,合理) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:136-247` |

`GET_WAY == "3"` 這個常數寫死在 UI,**沒有走 `MappingCode`**; 同一支畫面的下拉選單卻是走 `GetDropDownDataSrc("380")` 取的 (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:96`)。也就是說:**下拉的值域可以在代碼表改,但「哪個值代表配息轉申購」寫死在程式裡**。代碼表改了而程式沒改,畫面就會停止顯示轉換金額。嚴重度:中(附錄 E.10)。

#### 4.1.7 `OFDM287` 是本片唯一的字串串接 SQL

八個查詢條件全部長這個樣子:

```
strSQL += " And OFD283A." + Row.Name + " = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:143`,另 15 處散在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:147-262`。 **`Row.Name` 與 `Row.Value` 都直接接進 SQL,沒有任何跳脫**:

| 面向 | 風險 |
|---|---|
| `Row.Value` 直接串 | 畫面輸入 `' OR '1'='1` 可改變語意。但**欄位來源受限**——`Row.Value` 只從八個固定控件填入(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:140-172`),其中六個是遮罩 / 數值 / 日期控件,只有 `custID_NO` 與 `custBF_NO` 是文字。嚴重度:**中高** |
| `Row.Name` 直接串 | `Row.Name` 是程式寫死的八個常數,不是使用者輸入。嚴重度:低 |
| `LIKE` 分支 | `" Like " + "'" + Row.Value + "%'"`,樣式字元 `%` `_` 不跳脫,使用者打 `%` 會變萬用字元(`:147`) |

**與同專案的其他 M 畫面比,這支不算特例**——`ofdi1.md` 與 `ofd123.md` 都記過同樣的樣板。放在本片特別刺眼的原因是:**它旁邊那 24 支 2023 年新寫的境外軌查詢是 100% 參數化的**, 一個專案內兩種年代的寫法差距在這裡看得最清楚。

#### 4.1.8 一個沒被用到的旗標

`private bool CanSave = true;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:28`) 在整支檔案裡**只出現這一次**,沒有任何地方讀它或寫它。〔假設〕是原本規劃過「某些狀態不可存檔」的卡控後來拿掉了,依據是欄位名與初值; 但**程式裡找不到那條卡控,所以不能當成現行行為**。嚴重度:低(死碼,附錄 E.12)。

## 5. 查詢畫面(I)

```text
[圖] OFDI553 的查詢流程與三類過濾點
圖中文字:OFDI553 定期定額契約查詢:一支畫面九張表,七個過濾點 / UI xOneStepProcessForm / 收 11 個條件欄位 / Ctl OFDI553_Ctl / TransferVDBHelper 逐表搬 / PO OFDI553_PO / 一段 SQL,11 個 bind 變數 / 過濾點一 INNER JOIN:對不到就整列消失,無提示 / INNER JOIN OFD552 / 契約沒有明細列就看不到契約 / INNER JOIN OFD081 / 基金主檔沒這檔就看不到 / INNER JOIN BMS001A / 受益人主檔對不到就看不到 / 過濾點二 NVL 樣板:欄位本身是 NULL 時,空條件也會濾掉 / AGENT_ID 是 NULL / NULL = NVL(NULL, NULL) 得 UNKNOWN / AGENT_CODE 是 NULL / 同上,該筆契約永遠查不到 / 例外 SUB_BANK_CODE / 另外補了 OR 參數 IS NULL,是對的 / 過濾點三 AND 與 OR 缺括號:最後一行的 OR 把整個 WHERE 吃掉 / WHERE 1=1 AND 條件群 / 前面十個條件 / OR 契約書號 BETWEEN 起 迄 / 沒有外層括號 / 填了契約書號區間 / 基金公司 基金 日期 戶號全部失效 / 結果:查得到別的基金公司 別的客戶的契約,而畫面不會說 / 嚴重度 高 / 越權看到資料,且無任何提示 / 修法 / 把最後一個 OR 條件整段包進括號 / 孿生畫面 OFDI554 / 沒有這個 OR,所以沒中招
```

*圖:圖 4 本片最重的一支。三類過濾點都屬於「過濾(無提示)」:INNER JOIN 讓對不到的資料無聲消失、NVL 樣板讓 NULL 欄位的資料列永遠查不到、AND 與 OR 缺括號則反過來讓不該出現的資料出現。前兩者使用者會以為「真的沒有」,第三者使用者根本不會發現。*

本章是本片主體。**讀法**:§5.1 是全片共用的樣板與它的地雷,不讀後面看不懂; §5.2 講條件怎麼從畫面走到 SQL;§5.3 到 §5.4 用表格帶過分群; §5.5 到 §5.9 是五個需要深寫的主題。

### 5.1 `OTA.Query` 24 支的共用樣板,以及它內建的過濾陷阱

#### 5.1.1 樣板長什麼樣

24 支 PO 是同一份樣板長出來的,骨架一模一樣:

```
public T GetData<T>(T mModel, params object[] args)
{
    OFDI612AModelVDB model = mModel as OFDI612AModelVDB;
    int i = 0;
    try
    {
        string strSQL = string.Empty;
        strSQL += " SELECT ... ";            // 逐行 += ,每行接 Environment.NewLine
        strSQL += " FROM ... JOIN ... ";
        strSQL += " WHERE 1 = 1 ";
        strSQL += " AND 欄 = NVL(TRIM(:P), 欄) ";
        strSQL += " ORDER BY ... ";
        using (DbCommand cmd = dbTA.GetSqlStringCommand(strSQL))
        {
            dbTA.AddInParameter(cmd, "P", OracleDbType.Varchar2,
                SQLHelper.EVAStringHelper.GetParamValue(model, "P"));
            dbTA.LoadDataSet(cmd, model.DataEntity, model.DataEntity.OFDI612A.TableName);
        }
        i = model.DataEntity.OFDI612A.Rows.Count;
        model.Utility.Result.Clear();
        if (i > 0) model.Utility.Result.AddResultRow(true, i, "");
        else       model.Utility.Result.AddResultRow(false, 0, "");
    }
    catch (Exception ex)
    {
        model.Utility.Result.Clear();
        model.Utility.Result.AddResultRow(false, 0, ex.Message);
        CommonExceptionBlocker.HandleBusinessException(ex);
    }
    return mModel;
}
```

樣本:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:55-177`。 **這份樣板本身是好的**:SQL 全參數化、`using` 有包、例外有處理、筆數有回報。問題出在那一行條件的寫法。

#### 5.1.2 地雷:`欄 = NVL(TRIM(:P), 欄)` 遇到 NULL 欄位會無聲吃掉整列

設計意圖很清楚:**參數沒填就不過濾**。`TRIM(:P)` 在 Oracle 裡空字串等於 `NULL`, `NVL(NULL, 欄)` 回傳欄位自己,於是條件變成 `欄 = 欄` ——恆真。

**但只在欄位有值時恆真。** 當那一列的該欄位是 `NULL`:

| 情境 | 條件展開 | Oracle 三值邏輯結果 | 該列 |
|---|---|---|---|
| 參數有填、欄位有值 | `'A' = 'A'` | TRUE / FALSE | 正確過濾 |
| **參數沒填、欄位有值** | `欄 = 欄` | TRUE | 留下(正確) |
| **參數沒填、欄位是 NULL** | `NULL = NVL(NULL, NULL)` 即 `NULL = NULL` | **UNKNOWN** | **被濾掉** |
| 參數有填、欄位是 NULL | `NULL = 'A'` | UNKNOWN | 被濾掉(正確) |

**第三列就是地雷**。使用者什麼條件都不填按查詢,預期是「全部資料」, 實際拿到的是「**該欄位不為 NULL 的資料**」,而畫面**完全不會提示**—— `AddResultRow(false, 0, "")` 的訊息是空字串,只會顯示框架預設的「查無資料」。

卡控結果類型:**過濾(無提示)**。

#### 5.1.3 中招範圍

`OTA.Query` 24 支全部用這個樣板,`EC.Query` 的 `IPJI613` 也用(`NVL(:ID_NO, OFD601.ID_NO)`, `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:81-82`)。但**不是每個條件都會發作**——只有「該欄位在資料上可能為 NULL」時才會。以下列出風險較高的幾個:

| 畫面 | 條件欄 | 為什麼可能是 NULL | 錨點 |
|---|---|---|---|
| `OFDI553` | `OFD551.AGENT_ID` `OFD551.AGENT_CODE` | 直銷件沒有銷售機構 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:169-170` |
| `OFDI553` | `OFD551.BF_NO` | 契約尚未綁定戶號時 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:171` |
| `OFDI554` | `OFD555.RSP_CHG_NO` | 主檔異動未產生明細時 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:161` |
| `OFDI072B` | `OFD303` 的八個控制碼欄 | **八個條件全部套這個樣板**,任一個是 NULL 就整列消失 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI072B_PO.cs:82-92` |
| `OFDI283A` | `OFD281.DIVIDEND_DATE` `OFD281.PAY_DATE` | 配息尚未發放時這兩個日期是空的 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:168-169` |
| `OFDI071A` | `OFD309.PROG_CODE` `OFD309.UPD_USER` | 系統寫入的控制列沒有更新人員 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI071A_PO.cs:84-85` |

**`OFDI072B` 是最嚴重的一支**:它有八個控制碼條件,只要資料列上任何一個控制碼欄位是 `NULL`, 那一列在**任何查詢條件下都查不到**——包括什麼都不填。 `OFDI283A` 的 `DIVIDEND_DATE` / `PAY_DATE` 次之:**還沒發放的配息一律查不到**, 而「查還沒發放的配息」正是這支畫面最可能的用途。

#### 5.1.4 樣板作者自己知道這件事,但只修了三個地方

同一批程式裡有三處寫法不同,證明作者遇過這個問題:

| 寫法 | 出處 | 效果 |
|---|---|---|
| `AND (欄 = NVL(TRIM(:P), 欄) OR :P IS NULL)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`(`SUB_BANK_CODE`) | **正確**。參數沒填就整條為真,不管欄位是不是 NULL |
| `AND NVL(TRIM(欄), '19000101') BETWEEN NVL(TRIM(:ST), '19000101') AND NVL(TRIM(:END), '29991231')` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:164-165` | **正確**。把欄位的 NULL 也補成預設值 |
| `AND NVL(TRIM(欄), 'N') = :P` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:171` | **正確**,但這條是必填條件,沒有「不過濾」的選項 |

**三處修正全部集中在 `OFDI553` / `OFDI554` 這兩支**(2023/02/24 由 `Jye` 寫), 其餘 22 支沒有任何一處。〔假設〕是這兩支在測試時被抓到,修完沒有回頭套到別支; 依據是修正寫法有三種不同版本,不像是樣板本來就有的。

#### 5.1.5 日期區間的 `BETWEEN` 有同樣的問題但表現不同

日期條件的樣板是:

```
AND 欄 BETWEEN NVL(TRIM(:ST), '19000101') AND NVL(TRIM(:END), '29991231')
```

參數沒填時展開成 `欄 BETWEEN '19000101' AND '29991231'`——**看起來安全,但欄位是 `NULL` 時仍然是 UNKNOWN**, 該列照樣被濾掉。而且這裡多一層問題:**`'19000101'` 與 `'29991231'` 是字串比較**, 所以欄位必須是 `YYYYMMDD` 格式的字串才對得起來。本片的日期欄確實都是字串(`OFD651.APPLY_DATE` 在 `SELECT` 裡要 `TO_DATE(..., 'YYYYMMDD')` 才轉成日期, `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:70`),**所以目前是對的**。但**只要有人把某張表的日期欄改成 `DATE` 型別,這個 `BETWEEN` 會變成隱式轉換**, 結果是全表掃描加上不可預期的比較。屬於「現在沒壞但很脆」的地方。

### 5.2 條件怎麼從畫面走到 SQL

三條軌三種走法,**沒有一條走 SP**:

| 軌 | 畫面端 | 中繼 | PO 端 |
|---|---|---|---|
| `OTA.Query` 24 支 | `QueryVDB.Util.Parameters.AddParametersRow("欄名", SQLOperator.Equal, 值)` | `model.Utility.Parameters` 這個 key-value 袋 | `SQLHelper.EVAStringHelper.GetParamValue(model, "欄名")` 撈出字串 → `dbTA.AddInParameter` 當 bind |
| `EC.Query` 新的(`IPJI613` `IPJI614` `IPJI620`) | 同上 | 同上 | `vdb.Utility.Parameters.Rows.Find(...)` → `db.AddInParameter` |
| `EC.Query` 舊的(`IPJI630` `OFDI607` `OFDI608`) | 同上 | 同上 | `vdb.Utility.Parameters.FindByName("X").Value` **直接串進 SQL 字串** |

**關鍵差別在最後一欄**。前兩種值進 bind 變數,運算子寫死在 SQL; 第三種**連運算子都是從畫面帶過來的**:

```
strSQL += " AND OFD601.ID_NO "
        + vdb.Utility.Parameters.FindByName("ID_NO").Opeartor
        + "'" + vdb.Utility.Parameters.FindByName("ID_NO").Value + "'";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102`。 (`Opeartor` 是框架的拼字,不是筆誤。)詳見 §5.9。

**`EVAStringHelper.AddParam` 那兩個多載在本片一次都沒出現。** `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:198` 是 4 參數版(真參數化)、 `:346` 是 3 參數版(字串串接,`IN` 分支在 `:373-374` 直接 `"(" + strValue + ")"`,完全不跳脫)。本片用的是同一個類別的 `GetParamValue`(`:387`),**它只撈值不組 SQL**,所以那個坑踩不到。

### 5.3 分群帶過(一)— 對帳單與通知書五支

| 畫面 | 查什麼 | 主表 | 條件 | 值得注意 |
|---|---|---|---|---|
| `OFDI051` | 申購對帳單產製紀錄 | `OFD223` | 基金公司 / 基金 / 申購書號 / 更新日區間 | 用 `OFD062.FH_CD` 篩基金公司 |
| `OFDI052` | 贖回對帳單產製紀錄 | `OFD255` | 基金公司 / 基金 / 贖回書號 / 更新日區間 | **用 `OFD081` 的別名 `OFD081A` 篩**,與 `OFDI051` 不同路 |
| `OFDI055` | 申購交易通知書 | `OFD224` | 基金公司 / 基金 / 申購日 / 申購書號 | 唯一讀 `OFD012A` 與 `CTL014` 的一支 |
| `OFDI056` | 贖回交易通知書 | `OFD256` | 基金公司 / 基金 / 贖回書號 / 贖回日區間 | **SQL 寫死 `AND OFD256.JOB_CD = '1'`** |
| `OFDI057` | 轉換交易通知書 | `OFD256` | 同上,但是轉出日 | **SQL 寫死 `AND OFD256.JOB_CD = '2'`** |

`OFDI056` 與 `OFDI057` 是同一張表的兩支孿生畫面,差別只有那個常數 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123` 與 `OFDI057_PO.cs:133`) 與結果欄數(45 對 59)。**`JOB_CD` 的值域沒有走代碼表,兩支各寫死一個字元**; 如果之後多一種 `JOB_CD`,要靠人記得這裡有兩支畫面。嚴重度:低(附錄 E.6)。

**這兩支還是全片唯二沒有 `ORDER BY` 的畫面** (`grep -c "ORDER BY"` 對 `OFDI056_PO.cs` 與 `OFDI057_PO.cs` 都是 0)。 Oracle 不保證回傳順序,所以同一個查詢兩次執行的列序可能不同; 使用者匯出 Excel 對帳時會以為資料變了。嚴重度:低。

### 5.4 分群帶過(二)— 參數主檔、客戶資料、定期定額

**參數主檔五支**(`OFDI601` 到 `OFDI605`)是全片最單純的一組,五支結構完全相同:

| 畫面 | 主表 | 結果欄數 | `ORDER BY` |
|---|---|---|---|
| `OFDI601` | `OFD611` | 10 | `FUND_ID, CTL_DATE, TRAN_PAY_WAY` |
| `OFDI602` | `OFD612` | 9 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI603` | `OFD613` | 9 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI604` | `OFD614` | 8 | `FH_CD, FUND_ID, CTL_DATE` |
| `OFDI605` | `OFD615` | 8 | `FH_CD, FUND_ID, CTL_DATE` |

五支的條件一模一樣(基金公司 / 基金 / 資料控制日區間),各 4 個 bind, `FROM OFD61x LEFT JOIN OFD062 LEFT JOIN OFD606A` 的形狀也一樣 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:74-76`)。 `OFDI601` 的 `ORDER BY` 多了 `TRAN_PAY_WAY` 是唯一的差異。 **這五張表 `OFD611` 到 `OFD615` 在電子交易軌的對應是 `OFD611A` 到 `OFD615A`,由 `IPJI620` 一支全讀**(§5.8)。

**客戶與帳戶四支**:

| 畫面 | 查什麼 | 主表 | 條件數 | 值得注意 |
|---|---|---|---|---|
| `OFDI002` | 受益人資料變更紀錄 | `OFD105` | 3 | **全片唯一單表查詢**,沒有任何 JOIN |
| `OFDI071A` | 基金資料控制紀錄(境外) | `OFD309` | 5 | 境內版是 `OFDI071` 查 `OFD309A` |
| `OFDI072B` | 申贖控制碼(境外) | `OFD303` | **8** | 境內版是 `OFDI072A` 查 `OFD303A`;八個條件全套 NVL 樣板(§5.1.3) |
| `OFDI283A` | 收益分配明細(境外) | `OFD281` `OFD283` | 9 | 境內版是 `OFDI283` 查 `OFD281A` `OFD283A`;`OFD283A` 由 `OFDM287` 維護(§4) |

`OFDI283A` 還有一條與眾不同的條件:

```
AND OFD281.RECORD_DATE LIKE TRIM(:YEAR)||'%'
AND OFD281.RECORD_DATE = NVL(TRIM(:RECORD_DATE), OFD281.RECORD_DATE)
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:165-166`。 **同一個欄位被兩個條件夾擊**:第一個用年度做前綴比對(`:YEAR` 空時 `NULL||'%'` 在 Oracle 等於 `'%'`,恆真,正確), 第二個用完整日期比對。畫面上「年度」與「基準日」兩個欄位同時填時**必須自洽**,不然查不到任何東西—— 而畫面沒有檢查這件事。卡控結果:**過濾(無提示)**。嚴重度:低(使用者多半只填一個)。

**定期定額五支**:

| 畫面 | 查什麼 | 主表 | 條件數 | 值得注意 |
|---|---|---|---|---|
| `OFDI531` | 所得認列明細 | `OFD535` `OFD536` | 4 | 唯一讀 View `OFDV531` 的一支 |
| `OFDI553` | 定期定額契約 | `OFD551` `OFD552` | 11 | **`AND` / `OR` 缺括號**,§5.7 |
| `OFDI554` | 定期定額契約異動 | `OFD554` `OFD555` | 13 | 條件最多的一支;三處 NULL 處理是全片模範 |
| `OFDI563` | 授權申請 | `OFD563` | 3 | **借 `OFDI562` 的 xsd**,§2.4 |
| `OFDI564` | 匯款處理 | `OFD564` | 3 | `OFDI563` 的孿生,但有自己的 xsd |

`OFDI563` / `OFDI564` 是孿生畫面,SQL 骨架一樣,**但一支借 xsd 一支不借**—— 這代表 `OFDI563` 是後來從 `OFDI562` 複製出來的、`OFDI564` 是從 `OFDI563` 複製再補 xsd 的。〔假設〕,依據是三支的 `Created on` 依序是 `OFDI562`(未標)、`OFDI563` 2023/09/04、`OFDI564` 2023/09/05 (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:4`、`OFDI564_PO.cs:4`)。

### 5.5 深寫(一)— `OFDI601` 到 `OFDI615` 逐對比對

§0.4 講了搬家的過程,這一節講**三對同號到底是不是同一個查詢**。結論先講:**不是,是撞號。**

#### 5.5.1 三對逐項比較

| 對 | 電子交易軌那支(死)的條件欄位 | 業務 | 境外軌那支(活)的條件欄位 | 業務 | 主表 | 相似度 |
|---|---|---|---|---|---|---|
| `OFDI612` / `OFDI612A` | 交易途徑 / 變更生效日期起迄 | 網路變更生效查詢 | 基金公司 / 基金代碼 / 申請日期 / 買回日期 | 境外基金買回(贖回)單據查詢 | `OFD651` `OFD652` | **0** |
| `OFDI613` / `OFDI613A` | 受益人 ID / 戶號 / 受益人網路流水號 / 開戶申請日期 / 補件日期 / 交易途徑 | 網路開戶申請查詢 | 基金公司 / 基金代碼 / 申請日期 / 轉申購日期 | 境外基金轉換單據查詢 | `OFD651` `OFD653` | **0** |
| `OFDI614` / `OFDI614A` | 記錄類別 / 受益人 ID / 戶號 / 記錄日期 / 受益人網路流水號 | 網路記錄查詢 | 基金公司 / 基金代碼 / 申請日期 / 契約收件日期 | 境外定期定額契約查詢 | `OFD663` `OFD664` | **0** |

「主表」欄只有境外軌那支填得出來——電子交易軌那三支的 PO 整檔被註解,查不到它們查什麼表。

畫面標題欄位取自 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/OFDI612.Designer.cs` 等三支與 `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI612A.designer.cs` 等三支的控件標題(以 `grep` 取,未 Read Designer)。

**三對的相似度都是零。** 所以答案是: **這三對不是「同一查詢的境外軌與電子交易軌兩個版本」,是兩批人各自從 `OFDI6xx` 這個號段取號,撞在一起。**

#### 5.5.2 那「同一查詢的兩個軌」長什麼樣?本片有,但不是這三對

真正的「同一查詢兩個軌」在本片是**業務對應而非代號對應**:

| 業務 | 境外軌 | 電子交易軌 | 對得上嗎 |
|---|---|---|---|
| 申購單據 | `OFDI611` 查 `OFD620` `OFD621` | `IPJI612` 的 `IPJI621_Allot` 結果集查 `OFD620A` `OFD621A` | **對得上** |
| 贖回單據 | `OFDI612A` 查 `OFD651` `OFD652` | `IPJI612` 的 `IPJI621_Redeem` 查 `OFD651A` `OFD652A` | **對得上** |
| 轉換單據 | `OFDI613A` 查 `OFD651` `OFD653` | `IPJI612` 的 `IPJI621_Redeem` 一併查 `OFD653A` | **對得上,但電子交易軌把贖回與轉換併在同一個結果集** |
| 定額契約 | `OFDI614A` 查 `OFD663` `OFD664` | `IPJI612` 的 `IPJI621_RSP` 查 `OFD661A` `OFD662A` | **對得上,但表號不同** |
| 契約異動 | `OFDI615` 查 `OFD666` `OFD667` | `IPJI612` 的 `IPJI621_RSPCHG` | **對得上,表號不同** |
| 停利設定 | (境外軌無對應畫面) | `IPJI612` 的 `IPJI621_STOPSET` `IPJI621_STOPCHG` | **境外軌沒有** |

**所以境外軌的「五支畫面」對應到電子交易軌的「一支畫面的五個結果集」。** 最後兩列的表號對不起來(`OFD663`/`OFD664` 對 `OFD661A`/`OFD662A`), 所以 §0.2 的「去 `A`」規則在這兩組不成立——**〔假設〕的邊界就在這裡**。

#### 5.5.3 維護時的實務結論

| 情境 | 該動哪裡 |
|---|---|
| 境外基金的單據查詢要改 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs` 到 `OFDI615_PO.cs`(含 `OFDI612A_PO.cs` 等三支帶 `A` 的) |
| 網路下單的單據查詢要改 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs`(1821 行,先找對 region) |
| 有人回報「`OFDI612` 壞了」 | 先問是境外還是網路。境外找 `OFDI612A`,網路那支已停用 |
| 要清死碼 | 六支死畫面的 UI / Pxy / Ctl / PO / xsd 全部可刪,**但 PO 要同步從 `QueryPO.EC.csproj:132-146` 移除** |

### 5.6 深寫(二)— `A` / `B` 後綴的第六種成因

`ofdi1.md` 累積出 `A` 後綴的五種成因,並判定「查詢畫面的 `A` 全是第 (d) 種(畫面代號的一部分、與表無關)」。 **本片的四支後綴畫面驗證了這個判定,但補出一個 `ofdi1.md` 沒有的成因。**

#### 5.6.1 逐支判定

| 畫面 | 有沒有同名的表 | 它實際查的表 | 判定 |
|---|---|---|---|
| `OFDI071A` | 沒有 `OFD071A` | `OFD309` | (d) 與表無關 |
| `OFDI072B` | 沒有 `OFD072B` | `OFD303` | (d) 與表無關 |
| `OFDI283A` | **有 `OFD283A`**,而且是活的表 | **`OFD283`**(不帶 `A`) | (d) 與表無關,**而且是反向的** |
| `OFDI612A` | **有 `OFD612A`**,由 `IPJI620` 讀 | `OFD651` `OFD652` | (d) 與表無關 |
| `OFDI613A` | **有 `OFD613A`**,由 `IPJI620` 讀 | `OFD651` `OFD653` | (d) 與表無關 |
| `OFDI614A` | **有 `OFD614A`**,由 `IPJI620` 讀 | `OFD663` `OFD664` | (d) 與表無關 |

**`ofdi1.md` 的判定在本片成立:六支全是第 (d) 種。** 而且本片提供了比 `ofdi1.md` 的 `OFDI075A` 更強的證據—— `OFDI283A` / `OFDI612A` / `OFDI613A` / `OFDI614A` 這四支,**同名的表確實存在、確實是活的、卻由別的畫面在讀**。不是「剛好沒有那張表」,是「**那張表在,但跟這支畫面毫無關係**」。

#### 5.6.2 但「與表無關」只說了一半:後綴從哪來?

`ofdi1.md` 的 (d) 只說「是畫面代號的一部分」,沒說**為什麼會多這個字母**。本片可以回答,而且分兩種:

**成因 (d1):境內外分身,先到先得。**

| 境內軌(`ATLAS.OFD.Query`) | 它查的表 | 境外軌(`ATLAS.OTA.Query`) | 它查的表 |
|---|---|---|---|
| `OFDI071` | `OFD309A` `OFD081A` | **`OFDI071A`** | `OFD309` `OFD081` |
| **`OFDI072A`** | `OFD303A` `OFD081A` | **`OFDI072B`** | `OFD303` `OFD081` |
| `OFDI283` | `OFD281A` `OFD283A` `OFD081A` | **`OFDI283A`** | `OFD281` `OFD283` `OFD081` |

錨點:`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI071_PO.cs:87-92`、 `OFDI072A_PO.cs:75-76`、`OFDI283_PO.cs:106-112`, 對照 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI071A_PO.cs:74-80`、 `OFDI072B_PO.cs:76-80`、`OFDI283A_PO.cs:140-159`。

**三對完美對稱:畫面代號加一個字母、表名去掉一個 `A`。** 這正是 `ofdb5.md` 記的分家方式, 本片是它在查詢層的第一份三對實證。而 `OFDI072B` 用 `B` 不用 `A`,是因為**境內版自己已經叫 `OFDI072A`**—— 後綴是往後排的,不是語意編碼。

**成因 (d2):同專案線內撞號避讓。**

`OFDI612A` / `OFDI613A` / `OFDI614A` 不屬於 (d1)——它們的「本尊」`OFDI612` / `OFDI613` / `OFDI614` 不在境內軌,而在**電子交易軌**,而且業務完全不同(§5.5.1)。境外軌 2023 年新建這三支時,`OFDI612` 這個代號在全庫已被 `EC.Query` 佔用 (即使那支當時已經被註解),於是加 `A` 避開。

#### 5.6.3 更新後的成因型錄

| 成因 | 說明 | 本片有無 | 出處 |
|---|---|---|---|
| (a) | 境內外,`FUND_TYPE` `'2'` / `'1'`,值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` 的 `SHORE_ID` | 無 | `ofd5.md` `ofd7.md` |
| (b) | MSSQL 到 Oracle 遷移改名 | 無 | `ofd123.md` |
| (c) | 同概念第二張表 | 無 | `OFD017B` |
| (d) | 畫面代號的一部分、與表無關 | **六支全是** | `ofdi1.md` |
| (d1) | ↳ 境內外分身,後綴先到先得 | `OFDI071A` `OFDI072B` `OFDI283A` | **本片新增** |
| (d2) | ↳ 同專案線內撞號避讓 | `OFDI612A` `OFDI613A` `OFDI614A` | **本片新增** |
| (e) | 族名 | 無 | `ofdb5.md`,標〔假設〕且自承有反例 |

**一句話**:`ofdi1.md` 的「查詢畫面的 `A` 全是第 (d) 種」在本片**完全成立**, 本片把 (d) 拆成兩個可辨識的子成因,並提供了「同名表存在但無關」的四個硬證據。

### 5.7 深寫(三)— `OFDI553` 的 `AND` / `OR` 缺括號

本片最嚴重的一條缺陷。`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:165-174`:

```
 WHERE 1 = 1
   AND OFD551.FH_CD = NVL(TRIM(:FH_CD), OFD551.FH_CD)
   AND OFD552.FUND_ID = NVL(TRIM(:FUND_ID), OFD552.FUND_ID)
   AND OFD551.RCV_DATE BETWEEN NVL(TRIM(:RCV_DATE_ST), '19000101') AND NVL(TRIM(:RCV_DATE_END), '29991231')
   AND OFD551.AGENT_ID = NVL(TRIM(:AGENT_ID), OFD551.AGENT_ID)
   AND OFD551.AGENT_CODE = NVL(TRIM(:AGENT_CODE), OFD551.AGENT_CODE)
   AND OFD551.BF_NO = NVL(TRIM(:BF_NO), OFD551.BF_NO)
   AND BMS001A.ID_NO = NVL(TRIM(:ID_NO), BMS001A.ID_NO)
   AND (OFD551.SUB_BANK_CODE = NVL(TRIM(:SUB_BANK_CODE), OFD551.SUB_BANK_CODE) OR :SUB_BANK_CODE IS NULL)
   AND ((NVL(TRIM(:RSP_NO_ST), OFD551.RSP_NO) = OFD551.RSP_NO)) OR (TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END)
 ORDER BY OFD551.RSP_NO, OFD552.RSP_SRNO
```

**看最後一行。** 括號包的是 `NVL(...) = OFD551.RSP_NO` 那一小段, **`OR` 之後的 `BETWEEN` 沒有任何外層括號把它和前面九個條件圈在一起**。

Oracle 的 `AND` 優先於 `OR`,所以整段 `WHERE` 實際上是:

```
WHERE ( 1=1 AND 條件1 AND ... AND 條件9 )
   OR ( TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END )
```

| 使用者行為 | `:RSP_NO_ST` / `:RSP_NO_END` | `OR` 右側 | 實際結果 |
|---|---|---|---|
| 不填契約書號區間 | 兩者皆 NULL | `X BETWEEN NULL AND NULL` → UNKNOWN | 正常,九個條件生效 |
| **填契約書號區間** | 有值 | 區間內的契約為 TRUE | **前面九個條件全部失效** |

**也就是說:只要使用者填了「契約書號(起)」與「契約書號(迄)」, 基金公司、基金代碼、收件日、銷售機構、戶號、受益人 ID、扣款行全部不算**, 查出來的是**全公司該書號區間內的所有契約**,包含其他基金公司、其他客戶的。

| 面向 | 評估 |
|---|---|
| 結果類型 | **不是過濾,是反向洩漏**——該被濾掉的沒被濾掉 |
| 使用者看得出來嗎 | **看不出來**。多查出來的列與正常列長得一樣,沒有任何提示 |
| 嚴重度 | **高**。越權看到其他基金公司 / 其他受益人的定期定額契約 |
| 修法 | 把最後一個條件整段包起來:`AND ( (NVL(TRIM(:RSP_NO_ST), OFD551.RSP_NO) = OFD551.RSP_NO) OR (TRIM(OFD551.RSP_NO) BETWEEN :RSP_NO_ST AND :RSP_NO_END) )` |
| 孿生畫面有沒有中招 | **沒有**。`OFDI554` 的 `RSP_NO` 條件是單純的 `= NVL(...)`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:160`),沒有這個 `OR` |

上一行 `SUB_BANK_CODE` 那條**括號是對的**(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`), 證明作者知道要包括號,只是下一行少包了一層。**這是典型的「改對了一條、漏了下一條」。**

### 5.8 深寫(四)— `EC.Query` 的 `IPJI6xx` 五支

必答問題 2 的答案。`IPJ` 這個模組代號 `misc.md` 已查出是**電子交易**(那篇記的 `IJPR611` 是 `IPJ` 的錯字)。本片這五支是電子交易軌的查詢介面,**與同專案的 `OFDI6xx` 八支的關係是「新舊兩代」,不是「兩個業務」**。

#### 5.8.1 五支各管什麼

| 畫面 | 管什麼(推測) | 主表 | 結果集 | 行數 |
|---|---|---|---|---|
| `IPJI612` | 網路交易明細查詢,含退休金試算紀錄 | `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` 到 `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` | **7 張 `IPJI621_*` + `OFD673A`** | **1821** |
| `IPJI613` | 境外到價通知設定查詢 | `OFD681A` `OFD682A` `OFD683A` | `IPJI613` | 173 |
| `IPJI614` | 拋轉資料查詢 | `OFD618A` | **`OFD618A`** | 137 |
| `IPJI620` | 網路交易彙總查詢(申購 / 買回轉換 / 定額 / 受益人異動 / 停利轉申購) | `OFD611A` 到 `OFD615A` | `IPJI620_Allot` `_Redem` `_RSP` `_BMS_CHG` `_Switch` | 307 |
| `IPJI630` | 網路開戶紀錄查詢 | `OFD601` `OFD601CHG` `OFD607A` | `IPJI630_Master` + 裸 `DataSet` `"OFD601"` | 201 |

#### 5.8.2 它們跟同專案的 `OFDI6xx` 八支是什麼關係

| 面向 | `OFDI6xx`(8 支) | `IPJI6xx`(5 支) |
|---|---|---|
| 存活 | 2 活(`OFDI607` `OFDI608`)+ 6 死 | 5 支全活 |
| PO 檔名 | `OracleDao`(活的)/ `_PO`(死的) | 全部 `OracleDao` |
| 條件組法 | 活的兩支**全串字串** | `IPJI613` `IPJI614` 全 bind;`IPJI612` `IPJI620` 混用;`IPJI630` 全串字串 |
| 匯出 | `OFDI608` 有 | **五支全部沒有** |
| 明細彈窗 | 無 | `IPJI612` 有 `_P0` 到 `_P5` 六個,`IPJI614` 有 `_P0` 一個 |
| Model 檔名 | 正常 | **`IPJI612_9iModel.xsd`** `IPJI613Model.xsd` `IPJI614Model.xsd` `IPJI620Model.xsd` **`IPJI630_9iModel.xsd`** |

**`_9i` 那兩支是關鍵線索**:`9i` 是 Oracle 9i。〔假設〕是這兩支的 typed DataSet 在 Oracle 9i 時代就建好、之後沒重建, 所以檔名保留了當時的版本標記;依據是同資料夾其餘 xsd 沒有這個後綴, 而且這兩支正好是五支裡**條件組法最舊**(`IPJI630` 純字串串接)與**檔案最大**(`IPJI612` 1821 行)的兩支。

**關係的結論**:`IPJI6xx` 與 `OFDI6xx` **管同一條業務線(網路 / 語音下單),但是兩代介面**。 `OFDI6xx` 是分散的單一用途查詢(一支查一件事),`IPJI6xx` 是整合式查詢(一支畫面多頁籤多結果集)。新的把舊的取代掉,舊的六支被拔掉 csproj、兩支(`OFDI607` `OFDI608`)因為查的是 `LOG6xx` 軌跡表、 `IPJI6xx` 沒有涵蓋,所以留下來原地改成 `OracleDao`。

#### 5.8.3 `IPJI612`:全片最大的一支

1821 行、七個結果集、`LoadDataSet` 出現 **15 次** (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632,650,657,664,673,684,695,704,710,716,724,733,741,863,961`)。注意 `632` 到 `695` 與 `704` 到 `741` 是**同一組七張表被載入兩次**——兩段分支, 應該是「有挑基金」與「沒挑基金」兩條路。**兩條路各自維護一份 SQL**, 屬於 `ofd4.md 附錄 E` 記過的「基底版與覆寫版讀不同表」的同型風險:改一條忘了改另一條就會不一致。嚴重度:中。

它的結果集全叫 `IPJI621_*` 而畫面叫 `IPJI612`,見 §2.2。

#### 5.8.4 `IPJI613`:兩個沒有守門員的條件

`IPJI613` 的 SQL 裡有兩個**無條件出現**的 bind 變數:

```
WHERE '1' = NVL(:SET_TYPE,'1')
  AND OFD601.ID_NO = NVL(:ID_NO, OFD601.ID_NO)
  AND OFD601.BF_NO = NVL(:BF_NO, OFD601.BF_NO)
  AND OFD682A.FUND_ID IN (SELECT * FROM TABLE(F_FORMATSTRINGTOTABLE(:FUND_ID)))
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:80-83`(第二段 UNION ALL 在 `:108-111`)。而 PO 端加 bind 是**有條件的**:`if (vdb.Utility.Parameters.Rows.Contains("FUND_ID"))` (`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:122,127,132,137`),四個條件都這樣寫。

| 風險 | 說明 | 目前會不會發作 |
|---|---|---|
| `ORA-01008` 未繫結全部變數 | SQL 固定有四個 `:` 變數,PO 卻可能只加一部分 | **不會**。UI 一律無條件加四個(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:84-88`) |
| 沒挑基金就查不到任何東西 | `FUND_ID` 是空字串時 `F_FORMATSTRINGTOTABLE('')` 回傳空集合,`IN (空)` 永遠為假 | **〔假設〕會**。`IPJI613` 的 `BeforeSearchButtonClicked` **沒有「至少勾選一檔基金」的檢核**(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:75-89`),而同專案的 `IPJI614` 有(`IPJI614.cs:117`)、`IPJI620` 也有(`IPJI620.cs:259`) |

第二列是**過濾(無提示)**:使用者不挑基金直接查,得到「查無資料」,以為真的沒設定到價通知。 `F_FORMATSTRINGTOTABLE` 是資料庫端的 TVF,**版控外,無原始碼,從呼叫端反推**, 所以空字串的實際回傳沒辦法從程式證實,故標〔假設〕。嚴重度:中。

#### 5.8.5 `IPJI614` / `IPJI620` 的守門員寫得比較好

兩支都在 `BeforeSearchButtonClicked` 前面擋:

| 畫面 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| `IPJI614` | 至少勾選一種拋轉類別 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:105` |
| `IPJI614` | 至少勾選一檔基金 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:117` |
| `IPJI620` | 至少勾選一種交易種類 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:233` |
| `IPJI620` | 查無相關基金明細資料 | **警示** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:243,248` |
| `IPJI620` | 至少勾選一筆基金代碼 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:259` |
| `IPJI612` | 交易日期起迄必填、起必須小於迄 | **阻擋** | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI612.cs:442-449` |

**這六條是全片僅有的「阻擋」型卡控**(加上 `OFDM287` 的一條,共七條)。 `OTA.Query` 那 24 支**一條都沒有**——什麼都不填就能查,直接把整張表撈回來。加上 §3.2 記的「分頁 0 / 24」,**這 24 支任何一支都可能一次把整張表拉進 client 記憶體**。嚴重度:中(效能與 client 穩定性,不是正確性)。

`IPJI614` 還有一處值得看:多選基金用的是**字串串接進 `IN`**,

```
AND OFD618A.TRADE_TYPE IN (" + xTRADE_TYPE + @")
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:82`。 `xTRADE_TYPE` 由勾選框組出來(`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:80` 的 `m_TRADE_TYPE`), **值域是程式產生的固定字串、不是自由輸入**,所以注入風險低; 但同一支的基金多選走的是 TVF(`:90` 的 `F_FORMATSTRINGTOTABLE(:FUND_ID)`)—— **同一支畫面兩種多選、兩種做法**。嚴重度:低(一致性)。

### 5.9 深寫(五)— 三支純字串串接的查詢

#### 5.9.1 `OFDI607` 與 `IPJI630`:值與運算子都直接接進 SQL

樣板:

```
strSQL += " AND OFD601.ID_NO "
        + vdb.Utility.Parameters.FindByName("ID_NO").Opeartor
        + "'" + vdb.Utility.Parameters.FindByName("ID_NO").Value + "'";
```

| 畫面 | 處數 | 欄位 | 錨點 |
|---|---|---|---|
| `OFDI607` | 2 | `ID_NO` `BF_NO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102,106` |
| `OFDI608` | 2 | `ID_NO` `BF_NO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:88,92` |
| `IPJI630` | 6 | `ID_NO` `BF_NO` `EMAIL` 各兩處(兩段 SQL) | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:76,79,82,134,137,140` |

**單引號完全沒有跳脫。** 與 `ofdi1.md` 記的 `OFDI481_PO.cs:142`(連引號都沒有)相比, 這三支至少有包引號,所以打 `1 OR 1=1` 不會成立;但打 `' OR '1'='1` 會。

| 面向 | 評估 |
|---|---|
| 輸入來源 | `custID_NO` / `custBF_NO` / `utxtEMAIL` 三個文字控件,**是自由輸入** |
| `Opeartor` 來源 | 畫面端 `AddParametersRow(..., SQLOperator.Equal, ...)` 寫死,不是使用者控制 |
| 嚴重度 | **高**(`IPJI630` 六處)、**中高**(`OFDI607` `OFDI608` 各兩處) |
| 修法 | 換成 `db.AddInParameter`,與同專案的 `IPJI613` 寫法一致 |

`IPJI630` 另外還有兩處寫死的常數過濾: `AND OFD601.CHG_TYPE = 'Y'`(`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:57`)。這是**過濾(無提示)**:只有 `CHG_TYPE = 'Y'` 的開戶紀錄查得到,畫面上沒有任何欄位說明這件事。

#### 5.9.2 全片最會咬人的一處:全形空白

`OFDI607` 與 `OFDI608` 處理「日期(迄)」的方式一模一樣:

```
end_date = end_date.Substring(0, 10) + "　23:59:59";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:118` 與 `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:104`。

**`　` 是全形空白(IDEOGRAPHIC SPACE),不是半形空白。** 組出來的字串接著餵給:

```
to_date(' " + end_date + " ','yyyy-MM-dd hh24:mi:ss')
```

格式樣板 `yyyy-MM-dd hh24:mi:ss` 的日期與時間之間是**半形空白**, 而值裡面那個位置是**全形空白**。

| 面向 | 評估 |
|---|---|
| 會怎樣 | Oracle 的 `TO_DATE` 非 `FX` 模式容忍「多個半形空白」,但全形空白是一般字元,**理論上會 `ORA-01861: literal does not match format string`** |
| 標記 | **〔假設〕**。沒有實際跑過,結論由格式樣板與值的字元比對推得 |
| 同一支的「起日」有沒有同樣問題 | **沒有**。`beg_date` 只取 `Substring(0, 10)` 不接時間(`OFDI607OracleDao.cs:113`),格式也只到 `yyyy-MM-dd` |
| 兩支都中 | 是。同一段程式被複製過去 |
| 嚴重度 | **高**(若成立,使用者一填「日期(迄)」就查不動,例外訊息會被 `AddResultRow(false, 0, ex.Message)` 原文貼到畫面上) |
| 怎麼驗 | 在 Oracle 上跑 `SELECT TO_DATE(' 2024-01-01 23:59:59 ', 'yyyy-MM-dd hh24:mi:ss') FROM DUAL` |

**這是本片建議最優先驗證的一條。** 它不需要看懂任何業務,一條 SQL 就能確認。

#### 5.9.3 `OFDI607` 的另一個小問題:位置取參數

```
strSQL += " AND LOG602.CHG_DATETIME >= to_date(' " + beg_date.Substring(0, 10) + " ','yyyy-MM-dd') ";
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:113`。 `Substring(0, 10)` 假設畫面送來的字串**一定至少 10 個字元**。畫面端送的是 `DateTime.ToString("yyyy/MM/dd")`,長度剛好 10,目前安全; 但**格式一改(例如改成 `yyyy/M/d`)就會 `ArgumentOutOfRangeException`**, 而且這個例外會被 `catch (Exception ex)` 吞成「查無資料 + 例外訊息」。嚴重度:低(現在不會發作),但屬於「位置取參數」這一類的典型寫法。

#### 5.9.4 `OFDI608` 的一個好設計:ID 遮罩

`OFDI608` 是本片唯一主動遮蔽個資的一支:

```
DECODE(OFD601.ID_NO,'','',SUBSTR(OFD601.ID_NO, 1, 2)||'****'||SUBSTR(OFD601.ID_NO, 7, Length(OFD601.ID_NO))) as ID_NO
```

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:43`。 **顯示的是遮罩後的 ID,但查詢條件比對的是完整 ID**(`:87` 的 `AND OFD601.ID_NO = '值'`), 所以功能不受影響。值得其他畫面參考——本片另外 37 支的 `ID_NO` 都是明碼輸出。

### 5.10 例外處理:全片兩段式,錯誤訊息會原文上畫面

`OTA.Query` 24 支的 `catch` 完全一致:

```
catch (Exception ex)
{
    model.Utility.Result.Clear();
    model.Utility.Result.AddResultRow(false, 0, ex.Message);
    CommonExceptionBlocker.HandleBusinessException(ex);
}
```

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:168-173`。

| 面向 | 評估 |
|---|---|
| 好處 | 不吞例外,也有回報 |
| 壞處 | **`ex.Message` 是 Oracle 原文**,`ORA-00904` / `ORA-01861` 這種訊息會直接出現在使用者畫面上,含表名與欄名 |
| 與 `ofdi1.md` 比 | 那片有五支「兩個都做」被當成不一致記在附錄;本片是 **24 支全部兩個都做**,反而是一致的 |
| 結果類型 | 記錄不擋 |
| 嚴重度 | 低(資訊揭露),但排查問題時很好用 |

**沒有任何一支是空 `catch`,也沒有任何一支 `catch (SqlException)`**—— `ofdi1.md` 記的「`catch (SqlException)` 在 Oracle 上是死碼」這條缺陷在本片**不存在**, 因為 24 支都是 2023 年直接照 Oracle 寫的,從來沒有 MSSQL 版本。

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**

原因:本片的切片依據是三個專案資料夾,其中兩個是 `*.Query` 專案。 `Dev/ATLAS.OTA.Query` 與 `Dev/ATLAS.EC.Query` 兩棵樹底下**只放 I 畫面**—— 六層資料夾名一律是 `QueryUI` / `QueryFormProxy` / `QueryControl` / `QueryPO` / `QueryDataEntity` / `QueryUIEntity`, 沒有任何批次進入點、沒有 `Program.cs`、沒有 `ServiceBase`。第三個專案 `Dev/ATLAS.OFD` 有 B 畫面,但本片從那裡只收了 `OFDM287` 一支 M。

本片讀的表由誰寫、什麼時候寫,見 §8。

## 7. 報表(R)

**本片無 R 畫面。**

原因同上:報表住在 `Dev/ATLAS.OTA.Report` 與 `Dev/ATLAS.EC.Report`,是另外兩個專案。本片 38 支沒有任何一支產 `.rpt`、呼叫 Report Service、或寫檔到磁碟。 **唯一的「輸出」是 DevExpress 表格的 Excel 匯出**,由 UI 基底 `xOneStepProcessForm` 提供, 畫面只需要指定 `this.ExportGrid = this.ugrdResult` (例:`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI601.designer.cs:397`,以 `grep` 取得,未 Read Designer)。 `xOneStepProcessForm` **無原始碼,從呼叫端反推**。

## 8. 跨模組共用

```text
[圖] 跨模組:本片讀的表是誰建的、誰在寫
圖中文字:本片只讀不寫:38 支裡 37 支沒有任何寫入路徑 / OFDI6xx 境外單據查詢 / 讀 OFD620 621 651 到 653 663 到 667 / 誰在寫這些表 / ATLAS.OTA 的 M 畫面與 B 批次 / 本片不碰 / 沒有 INSERT UPDATE DELETE / 共用主檔:改一個欄位會同時打到十幾支 / OFD081 OFD081A 基金主檔 / 本片 14 支讀 / OFD062 境外基金公司 / 本片 10 支讀 / BMS001A 受益人主檔 / 本片 9 支讀 / FSK003 幣別 / 本片 9 支 INNER JOIN / CTL014 系統代碼 / 本片 4 支讀 / OFD019A 銀行 / 本片 5 支 LEFT JOIN / 電子交易軌的上游:LOG 系列由 EC 的寫入端產生 / LOG600 LOG601 LOG602 / 網路變更軌跡 / OFDI607 OFDI608 讀 / 只查不寫 / 寫入端在 ATLAS.EC / 不在本片範圍 / 唯一的寫入者:OFDM287 走四眼改 OFD283A / OFDM287 xMaintainForm / BaseEVADaoPO + MasterTable / OFD283A 配息給付 / 境內分戶軌的表 / 與 OFDI283A 無關 / 那支查的是 OFD283
```

*圖:圖 5 跨模組。灰虛框=本片只讀、由別的模組維護的表;紫框=風險或唯一的寫入路徑。要判斷改某張表會不會打到本片,看這張圖的第二第三列就夠:基金主檔與幣別表被最多支讀到,而幣別是 INNER JOIN,漏一筆整列就不見。*

### 8.1 本片一張表都不「擁有」

37 支查詢畫面**沒有任何寫入路徑**(§0.5),唯一寫入的 `OFDM287` 改的 `OFD283A` 也是 `ATLAS.OFD` 的表。所以本片對其他模組的影響面是**單向的**:別人改表,本片會壞;本片改程式,不影響別人。

### 8.2 改哪張表會打到本片幾支

| 表 | 打到本片幾支 | 打到誰 | 改動要注意什麼 |
|---|---|---|---|
| `OFD081` | 16 | 見 §2.5 | 境外軌基金主檔。**16 支裡有 6 支是 `INNER JOIN`**,基金主檔少一筆,對應的交易單據整列消失 |
| `OFD062` | 15 | 見 §2.5 | 境外基金公司。多數是 `FROM` 起點或 `LEFT JOIN`,影響較小 |
| `FSK003` | 13 | 見 §2.5 | 幣別主檔。**幾乎全是 `INNER JOIN`**,是本片最危險的共用表(§8.3) |
| `BMS001A` | 10 | 見 §2.5 | 受益人主檔。`OFDI553` `OFDI554` `OFDI283A` 用 `INNER JOIN` |
| `OFD606A` | 10 | `OFDI601` 到 `OFDI605` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` | 全 `LEFT JOIN`,影響只是基金簡稱顯示空白 |
| `OFD601` | 9 | 跨兩條軌 | **唯一被境外軌與電子交易軌同時讀的表**,改欄位要同時測兩邊 |
| `OFD019A` | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` | 全 `LEFT JOIN` |
| `OFD199` | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` | 活動代碼,全 `LEFT JOIN` |
| `OFD081A` | 3 | `IPJI612` `IPJI614` `IPJI620` | 電子交易軌基金主檔。**注意 `OFDI052` 與 `IPJI613` 用這個字串當別名,不是真的讀它** |
| `CTL014` | 3 | `OFDI055` `IPJI612` `IPJI614`,另 `OFDI607` `OFDI608` 以子查詢方式讀 | `SourceType` 的編號是〔客戶特定〕 |

### 8.3 `FSK003` 是本片最危險的共用表

13 支讀它,**其中 `OFDI051` `OFDI052` `OFDI055` `OFDI056` `OFDI057` `OFDI283A` `OFDI531` `OFDI553` `OFDI554` `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` 幾乎全用 `INNER JOIN`**, 例:`INNER JOIN FSK003 ON OFD652.FUND_CURRENCY = FSK003.CRNCY_CD` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:135`)。

| 情境 | 結果 |
|---|---|
| 交易的幣別在 `FSK003` 裡沒有對應列 | **整筆交易在查詢結果中消失** |
| 有提示嗎 | **沒有**。卡控結果:**過濾(無提示)** |
| 什麼時候會發生 | 新增一個幣別但 `FSK003` 還沒建;或 `FSK003` 的 `CRNCY_CD` 有前後空白對不上 |
| 嚴重度 | **高**——「查不到某一筆交易」在對帳情境下會被當成資料遺失 |

`OFDI052` 對這件事處理得比較好:主幣別用 `INNER JOIN FSK003 FSK003A`、轉換後幣別用 `LEFT JOIN FSK003 FSK003B` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:122-123`)—— **轉換後幣別可能是空的,所以用 LEFT**。同一支畫面裡兩種 JOIN 是有意識的,不是隨手。

### 8.4 本片被誰引用

**沒有。** 查詢畫面是葉節點:沒有別的模組 `new` 本片的任何 PO / Ctl, 本片的六個組件(`QueryUI.OTA` / `QueryFormProxy.OTA` / `QueryControl.OTA` / `QueryPO.OTA` / `QueryDataEntity.OTA` / `QueryUIEntity.OTA`,加 EC 側的六個)只被主程式的選單載入。

### 8.5 三條軌的改動影響傳遞

| 改動 | 會打到 |
|---|---|
| 改境外軌 `OFD6xx`(不帶 `A`)欄位 | `OTA.Query` 的 `OFDI601` 到 `OFDI605` `OFDI611` 到 `OFDI615`,共 10 支 |
| 改電子交易軌 `OFD6xxA`(帶 `A`)欄位 | `EC.Query` 的 `IPJI612` `IPJI620`,共 2 支(但 `IPJI612` 一支就讀 13 張) |
| 改 `OFD283A` 欄位 | `OFDM287`(本片 §4)+ `Dev/ATLAS.OFD.Query` 的 `OFDI283` |
| 改 `OFD283`(不帶 `A`)欄位 | `OFDI283A`(本片) |
| 改 `LOG600` `LOG601` `LOG602` | `OFDI607` `OFDI608` |

**最後一列值得提醒**:`LOG6xx` 是電子交易的軌跡表,由 `Dev/ATLAS.EC` 的寫入端產生, 本片只讀。那個寫入端**不在本片範圍**。

## 附錄 A. 資料表總表

只列本片 live 的 32 支實際 `FROM` / `JOIN` 到的表;別名已排除。「軌」欄:外=境外綜合帳戶、電=電子交易、內=境內分戶、共=三軌共用。

| 表 | 軌 | 被本片幾支讀 | 讀它的畫面 |
|---|---|---|---|
| `OFD081` | 外 | 16 | 見 §2.5 |
| `OFD062` | 外 | 15 | 見 §2.5 |
| `FSK003` | 共 | 13 | 見 §2.5 |
| `BMS001A` | 共 | 10 | 見 §2.5 |
| `OFD606A` | 外 | 10 | `OFDI601` 到 `OFDI605` `OFDI611` 到 `OFDI615` |
| `OFD601` | 共 | 9 | `OFDI611` `OFDI612A` `OFDI613A` `OFDI614A` `OFDI615` `OFDI607` `OFDI608` `IPJI612` `IPJI630` |
| `OFD019A` | 共 | 5 | `OFDI553` `OFDI563` `OFDI564` `OFDI611` `OFDI612A` |
| `OFD199` | 外 | 5 | `OFDI553` `OFDI554` `OFDI611` `OFDI614A` `OFDI615` |
| `OFD081A` | 電 | 3 | `IPJI612` `IPJI614` `IPJI620` |
| `CTL014` | 共 | 5 | `OFDI055` `IPJI612` `IPJI614` `OFDI607` `OFDI608` |
| `COD006A` | 共 | 2 | `OFDI553` `OFDI554` |
| `OFD020V` | 共 | 2 | `OFDI283A` `IPJI612` |
| `OFD256` | 外 | 2 | `OFDI056` `OFDI057` |
| `OFD551` | 外 | 2 | `OFDI553` `OFDI554` |
| `OFD651` | 外 | 2 | `OFDI612A` `OFDI613A` |
| `OFD601CHG` | 電 | 2 | `IPJI612` `IPJI630` |

**以下每張只被一支畫面讀,依讀它的畫面合併列出:**

| 讀它的畫面 | 軌 | 它獨讀的表 |
|---|---|---|
| `IPJI612` | 電 | `COD006` `OFD020A` `OFD138A` `OFD199A` `OFD304A` `OFD620A` `OFD621A` `OFD651A` `OFD652A` `OFD653A` `OFD655A` `OFD656A` `OFD657A` `OFD658A` `OFD661A` `OFD662A` `OFD672A` `OFD673A` |
| `IPJI613` | 電 | `OFD681A` `OFD682A` `OFD683A` |
| `IPJI614` | 電 | `OFD618A` |
| `IPJI620` | 電 | `OFD611A` `OFD612A` `OFD613A` `OFD614A` `OFD615A` |
| `IPJI630` | 電 | `OFD607A` |
| `OFDI607` | 電 | `LOG602` |
| `OFDI608` | 電 | `LOG600` `LOG601` |
| `OFDI002` | 外 | `OFD105` |
| `OFDI051` | 外 | `OFD223` |
| `OFDI052` | 外 | `OFD255` |
| `OFDI055` | 外 | `OFD012A` `OFD224` |
| `OFDI071A` | 外 | `OFD309` `SWPRODUCTSDETAIL`(別名 `PROG`) |
| `OFDI072B` | 外 | `OFD303` |
| `OFDI283A` | 外 | `OFD013` `OFD281` `OFD283` |
| `OFDI531` | 外 | `OFD535` `OFD536` `OFDV531` |
| `OFDI553` | 外 | `COD009` `MYOFD072A`(別名 `OFD072A`) `OFD068A` `OFD552` |
| `OFDI554` | 外 | `OFD554` `OFD555` |
| `OFDI563` | 外 | `OFD563` |
| `OFDI564` | 外 | `OFD564` |
| `OFDI601` 到 `OFDI605` | 外 | `OFD611` `OFD612` `OFD613` `OFD614` `OFD615`(各一支各一張) |
| `OFDI611` | 外 | `OFD012` `OFD620` `OFD621` |
| `OFDI612A` | 外 | `OFD652` |
| `OFDI613A` | 外 | `OFD653` |
| `OFDI614A` | 外 | `OFD663` `OFD664` |
| `OFDI615` | 外 | `OFD666` `OFD667` |
| **`OFDM287`** | **內** | **`OFD283A`(唯一寫入) `OFD281A` `OFD081V`** |
| `IPJI612` `IPJI630` 兩支 | 電 | `OFD601CHG` |

View(名稱帶 `V`):`OFD020V` `OFD081V` `OFDV531` `V_FUND`。 `OFDV531` 只被 `OFDI531` 讀、`V_FUND` 只被 `IPJI613` 讀(別名 `OFD081A`)。

## 附錄 B. SP / Function / Trigger / View

**本片沒有任何 Stored Procedure。** 38 支掃描結果:`CommandType.StoredProcedure` 0 次、 `EXEC` 0 次、`CALL` 0 次。這是本片與 `ofdi1.md`(11 支全丟 SP)最大的差別之一。

| 物件 | 型別 | 被誰用 | 錨點 | 備註 |
|---|---|---|---|---|
| `F_FORMATSTRINGTOTABLE` | Table Function(TVF) | `IPJI613` `IPJI614` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:83`、`IPJI614OracleDao.cs:90` | 把逗號字串拆成表,供 `IN` 使用。**版控外,無原始碼,從呼叫端反推** |
| `OFD020V` | View | `OFDI283A` `IPJI612` `OFDM287` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:152` | 分行資料 |
| `OFD081V` | View | `OFDM287` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:123` | 境內基金主檔 View |
| `OFDV531` | View | `OFDI531` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI531_PO.cs` | 所得認列用 |
| `V_FUND` | View | `IPJI613` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:73` | **別名為 `OFD081A`**,程式註解記著 `2022.05.13 OFD081A -> V_FUND by Becky` |

**Trigger:本片程式不涉及,未掃描。**

## 附錄 C. 代碼對照

全部從程式的 `CASE WHEN` / `DECODE` 反推,**不是查代碼表**,所以改代碼表不會改到這些顯示。

| 代碼 | 值 | 中文 | 出處 |
|---|---|---|---|
| `OFD611.ALLOT_CTL_CODE` | `'0'` / `'1'` / `'2'` | 未處理 / 已轉處理中 / 已拋轉 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI601_PO.cs:73` |
| `OFD651.EC_REDEM_PCODE` | `'0'` / `'1'` / `'2'` / `'3'` / `'4'` | 輸入 / 處理中 / 轉入 / **(空字串)** / 刪除 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:100-101` |
| `OFD256.JOB_CD` | `'1'` / `'2'` | 贖回 / 轉換(當過濾條件用,不顯示) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:123`、`OFDI057_PO.cs:133` |
| `OFD618A.TRADE_TYPE` | `'1'` 等 | 申購拋轉 等 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI614OracleDao.cs:63-68` |
| `OFD682A.INV_CD` | `'1'` / 其他 | 單筆 / 定額 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:69` |
| `OFD681A.ALERT_LIMIT_YN` | `'Y'` / `'N'` | 每次通知 / 一次通知 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:66` |
| `OFD601.CHG_TYPE` | `'Y'` | (寫死過濾,未翻中文) | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:57` |
| `CTL014.Sourcetype` | `'298'` `'299'` `'300'` `'302'` `'346'` | 電子交易的各類代碼群〔客戶特定〕 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:58-59`、`OFDI607OracleDao.cs` |
| `GetDropDownDataSrc` 群組 | `"376"` `"378"` `"380"` `"381"` `"382"` `"419"` | `OFDM287` 的六個下拉〔客戶特定〕 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:94-99` |
| `OFDM287` 的 `GET_WAY` | `'3'` | 配息轉申購(**寫死在 UI,不走代碼表**) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:200` |
| `COD006A.CODE_SORT` | `'A8'` | `OFD551.STOP_CD` 的代碼群 | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:161` |

境內外的 `SHORE_ID` 值域在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291`, **本片 38 支沒有任何一支引用它**——三條軌是用**專案與表名**分的,不是用欄位值分的。這一點與 `ofd5.md` / `ofd7.md` 記的境內外分法不同,是本片的觀察。

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module`**,因為本片橫跨三個專案,沒有單一 module key 對得上。改成逐支列表。

| # | 代號 | 專案 | PO 基底 | 在 csproj | 本文處置 |
|---|---|---|---|---|---|
| 1 | `OFDI002` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 2 | `OFDI051` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.3) |
| 3 | `OFDI052` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§2.6.1 §5.3 §8.3) |
| 4 | `OFDI055` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.3) |
| 5 | `OFDI056` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.3,寫死常數 + 無 ORDER BY) |
| 6 | `OFDI057` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.3,同上) |
| 7 | `OFDI071A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.6.2 境內外分身) |
| 8 | `OFDI072B` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.1.3 最嚴重的 NVL 中招 + §5.6.2) |
| 9 | `OFDI283A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§4.1.3 §5.4 §5.6) |
| 10 | `OFDI531` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 11 | `OFDI553` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.7 全片最嚴重缺陷 + 圖 4) |
| 12 | `OFDI554` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.1.4 三處 NULL 處理模範) |
| 13 | `OFDI563` | `OTA.Query` | 無基底 | **UI/Pxy/Ctl/PO 在,無 Model/View xsd** | **已寫**(§2.4 全片唯一四層) |
| 14 | `OFDI564` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§3.2 §5.4) |
| 15 | `OFDI601` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.4 §0.4) |
| 16 | `OFDI602` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 17 | `OFDI603` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 18 | `OFDI604` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 19 | `OFDI605` | `OTA.Query` | 無基底 | 六層全在 | 表格帶過(§5.4) |
| 20 | `OFDI611` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.2) |
| 21 | `OFDI612A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 22 | `OFDI613A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 23 | `OFDI614A` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.1 §5.6) |
| 24 | `OFDI615` | `OTA.Query` | 無基底 | 六層全在 | **已寫**(§5.5.2) |
| 25 | `IPJI612` | `EC.Query` | 無基底 | 六層全在(Model 叫 `IPJI612_9iModel.xsd`) | **已寫**(§2.2 §5.8.1 §5.8.3) |
| 26 | `IPJI613` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.8.4) |
| 27 | `IPJI614` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.8.5) |
| 28 | `IPJI620` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§0.2 §5.8.5) |
| 29 | `IPJI630` | `EC.Query` | 無基底 | 六層全在(Model 叫 `IPJI630_9iModel.xsd`) | **已寫**(§5.9.1) |
| 30 | `OFDI606` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 31 | `OFDI607` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.9.1 §5.9.2 §5.9.3) |
| 32 | `OFDI608` | `EC.Query` | 無基底 | 六層全在 | **已寫**(§5.9.1 §5.9.2 §5.9.4) |
| 33 | `OFDI609` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 34 | `OFDI610` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §3.3,死) |
| 35 | `OFDI612` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 36 | `OFDI613` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 37 | `OFDI614` | `EC.Query` | **整檔註解** | **UI/Pxy/Ctl 不在 csproj** | **已寫**(§0.4 §5.5.1,死) |
| 38 | `OFDM287` | `ATLAS.OFD` | **`BaseEVADaoPO`** | 六層全在(Model 叫 `OFDM287Model.xsd.xsd`) | **已寫**(§4 全章) |

**統計**:已寫 26 支、表格帶過 12 支;不在 csproj 的 **6 支**(全是 `EC.Query` 那批死畫面的 UI/Pxy/Ctl 三層); 繼承 `BasicEVAPO` 的 **0 支 live**(15 次出現全在註解裡);繼承 `BaseEVADaoPO` 的 **1 支**(`OFDM287`)。

**本片沒有涵蓋但住在同一批專案裡的**(避免下一個人以為漏掉):

| 代號 | 位置 | 為什麼不在本片 |
|---|---|---|
| `OFDI562` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI562_PO.cs` | 不在指派名單。**但 `OFDI563` 借它的 xsd**,所以 §2.4 有提到 |
| `TRPI001` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs` | 不在指派名單;它的 Model 有兩張表(`TRPI001` + `TRP001`),是本專案唯一的多表結果集 |
| `OFDI641` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` | 不在指派名單;`ec.md` 涵蓋 |
| `EC.Query` 的 `OFDI601` 到 `OFDI605` `OFDI611` `OFDI615` | `MSSQL/` 底下 | 不在指派名單,但與名單上那六支死畫面同批、同樣整檔註解(§0.4 事實二) |

## 附錄 E. 讀本文時要注意的地方

每條:缺陷 / 影響 / 錨點 / 嚴重度。**依嚴重度排序。**

### E.1 `NVL(TRIM(:P), 欄)` 樣板讓 NULL 欄位的資料列永遠查不到

- **缺陷**:`欄 = NVL(TRIM(:P), 欄)` 在欄位為 `NULL` 時展開成 `NULL = NULL`,Oracle 三值邏輯得 UNKNOWN,該列被濾掉。參數沒填也一樣。

- **影響**:使用者不填條件按查詢,以為看到全部,實際少了一批。**過濾(無提示)**。

- **錨點**:樣板見 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:138-139`;最嚴重的 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI072B_PO.cs:82-92`(八個條件全中);次之 `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI283A_PO.cs:168-169`。

- **嚴重度**:**高**(範圍最廣,`OTA.Query` 24 支全中 + `IPJI613`)

- **正確寫法就在同一批程式裡**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:173`。

### E.2 `OFDI553` 的 `AND` / `OR` 缺括號,填書號區間就繞過全部條件

- **缺陷**:最後一個條件的 `OR` 沒有外層括號,`AND` 優先於 `OR`,整個 `WHERE` 變成「(九個條件) OR (書號區間)」。

- **影響**:填了契約書號起迄,基金公司 / 基金 / 日期 / 戶號 / 受益人 ID 全部失效,**查得到其他基金公司、其他客戶的契約**,且無任何提示。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:174`

- **嚴重度**:**高**(越權資料揭露)

- **孿生的 `OFDI554` 沒中招**(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI554_PO.cs:160`)。

### E.3 日期(迄)接了一個全形空白,`TO_DATE` 極可能拋 `ORA-01861`

- **缺陷**:`end_date.Substring(0, 10) + "　23:59:59"`,`　` 是全形空白;格式樣板 `'yyyy-MM-dd hh24:mi:ss'` 那個位置要的是半形空白。

- **影響**:使用者一填「日期(迄)」,查詢就丟例外;例外訊息被 `AddResultRow(false, 0, ex.Message)` 原文貼上畫面。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:118`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:104`

- **嚴重度**:**高**,但標**〔假設〕**——沒有實際在 Oracle 上跑過,結論由字元比對推得。

- **怎麼驗**:`SELECT TO_DATE(' 2024-01-01　23:59:59 ', 'yyyy-MM-dd hh24:mi:ss') FROM DUAL`。**這是本片建議最優先驗證的一條。**

### E.4 `INNER JOIN FSK003` 讓沒有幣別對照的交易無聲消失

- **缺陷**:13 支讀 `FSK003`,幾乎全是 `INNER JOIN`;幣別對不到就整列不見。

- **影響**:對帳時被當成資料遺失。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:135`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI611_PO.cs:136`

- **嚴重度**:**中高**

- **同型**:`INNER JOIN BMS001A`(`OFDI283A_PO.cs:144`)、`INNER JOIN OFD081`(`OFDI283A_PO.cs:146`)、`INNER JOIN OFD552`(`OFDI553_PO.cs`)。

### E.5 三支 PO 把畫面輸入直接串進 SQL

- **缺陷**:`" AND 欄 " + Params.FindByName("X").Opeartor + "'" + Params.FindByName("X").Value + "'"`,單引號不跳脫。

- **影響**:`' OR '1'='1` 之類的輸入可改變語意。輸入來源是自由文字控件(受益人 ID / 戶號 / Email)。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI630OracleDao.cs:76,79,82,134,137,140`(6 處)、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:102,106`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI608OracleDao.cs:88,92`

- **嚴重度**:**中高**(`IPJI630` 高)

- **同專案的正確寫法**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:122-137`。

### E.6 `OFDM287` 的八個查詢條件全部字串串接

- **缺陷**:`strSQL += " And OFD283A." + Row.Name + " = " + "'" + Row.Value + "'";`,`LIKE` 分支還不跳脫 `%` `_`。

- **影響**:同 E.5。輸入來源八個控件中六個是遮罩 / 數值 / 日期,只有受益人 ID 與戶號是文字。

- **錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:143,147`,另 15 處在 `:147-262`

- **嚴重度**:**中高**

### E.7 六支死畫面:PO 整檔註解仍掛 csproj,Ctl 退出 csproj 卻還在磁碟上

- **缺陷**:`OFDI606` `OFDI609` `OFDI610` `OFDI612` `OFDI613` `OFDI614` 的 PO 全檔 `//`,仍列在 `QueryPO.EC.csproj`;對應 Ctl 檔在磁碟上但不在 `QueryControl.EC.csproj`,內容還 `new` 一個不存在的型別。

- **影響**:三支功能(`OFDI606` `OFDI609` `OFDI610`)等於消失且無人知道;改 `OFDI612` 等三支會改到屍體;做影響分析時 `grep` 會命中假結果。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/QueryPO.EC.csproj:132-146`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/QueryControl.EC.csproj:108-115`、`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/OFDI601_Ctl.cs:34`

- **嚴重度**:**中**(維護成本與誤判風險)

### E.8 `OFDI563` 借用 `OFDI562` 的 xsd,改一支動到兩支

- **缺陷**:`OFDI563` 沒有自己的 Model / View,整套借 `OFDI562`;PO 的 `LoadDataSet` 目標是 `model.DataEntity.OFDI562.TableName`。

- **影響**:改 `OFDI562` 的結果欄位會同時改到 `OFDI563` 的畫面,而 `grep OFDI563` 找不到任何 xsd。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI563_PO.cs:93`、`Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI563_Ctl.cs:42,58,87`

- **嚴重度**:**中**

### E.9 表別名取成另一張真實存在的表名

- **缺陷**:`INNER JOIN OFD081 OFD081A`、`LEFT JOIN FSK003 FSK003A`、`LEFT JOIN MYOFD072A OFD072A`、`LEFT JOIN OFD019A OFD019B`、`LEFT JOIN V_FUND OFD081A`。

- **影響**:`grep -rn "OFD081A"` 會命中不讀該表的檔案,影響分析容易誤判。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI052_PO.cs:119-123`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI553_PO.cs:156`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:133`、`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:73`

- **嚴重度**:**中**(不影響執行,只影響分析)

### E.10 `OFDM287` 的維護頁只回寫 `MEMO`,其他欄位改了不存也不提示

- **缺陷**:`BeforeModifyButtonClicked` 只做 `Row.MEMO = this.utxtMEMO.Text`。

- **影響**:使用者改了金額 / 帳號 / 日期後按修改,什麼都沒發生,**沒有提示**。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:248-253`

- **嚴重度**:**中**(若那些控件實際上是唯讀,則為低;Designer 未 Read,無法確認)

### E.11 `IPJI613` 沒有「至少挑一檔基金」的守門員

- **缺陷**:SQL 用 `FUND_ID IN (SELECT * FROM TABLE(F_FORMATSTRINGTOTABLE(:FUND_ID)))`,而 UI 不檢查有沒有挑基金;同專案的 `IPJI614` `IPJI620` 都有檢查。

- **影響**:沒挑基金直接查會得到空集合,使用者以為沒有到價通知設定。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs:83`、`Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI613.cs:75-89`(無檢核),對照 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI614.cs:117`

- **嚴重度**:**中**,標**〔假設〕**(`F_FORMATSTRINGTOTABLE` 版控外,空字串的回傳未證實)

### E.12 `OFDM287` 的 `GET_WAY == "3"` 寫死在 UI,下拉卻走代碼表

- **缺陷**:下拉值域走 `GetDropDownDataSrc("380")`,但「哪個值是配息轉申購」寫死。

- **影響**:代碼表改了程式沒改,畫面停止顯示轉換金額。**過濾(無提示)**。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:96,200`

- **嚴重度**:**中**

### E.13 `IPJI612` 同一組七張結果集有兩段各自維護的 SQL

- **缺陷**:`LoadDataSet` 15 次,`:632-695` 與 `:704-741` 是同一組七張表的兩條分支。

- **影響**:改一條忘了改另一條,兩條路的結果會不一致。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI612OracleDao.cs:632,704`

- **嚴重度**:**中**

### E.14 `OFDI056` / `OFDI057` 沒有 `ORDER BY`

- **缺陷**:兩支全片唯二沒有 `ORDER BY` 的畫面。

- **影響**:Oracle 不保證回傳順序,同一查詢兩次執行列序可能不同,匯出對帳會誤判。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI056_PO.cs:128`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI057_PO.cs:138`(`WHERE` 之後直接 `using`)

- **嚴重度**:**低**

### E.15 `OFD651.EC_REDEM_PCODE = '3'` 翻成空字串

- **缺陷**:`CASE WHEN ... = '3' THEN ''`,其餘四個值都翻成「代碼:中文」。

- **影響**:畫面該欄位出現空白,使用者分不出是狀態 `'3'` 還是沒有值。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:101`,`OFDI613A_PO.cs` 同段照抄

- **嚴重度**:**低**

### E.16 `OFDI607` 的 `Substring(0, 10)` 位置取參數

- **缺陷**:假設畫面送來的日期字串長度至少 10;畫面目前送 `yyyy/MM/dd` 剛好 10。

- **影響**:格式一改就 `ArgumentOutOfRangeException`,且會被 `catch (Exception)` 吞成「查無資料」。

- **錨點**:`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI607OracleDao.cs:113`、`OFDI608OracleDao.cs:100`

- **嚴重度**:**低**(目前不會發作)

### E.17 `OFDM287` 的 `CanSave` 是死碼

- **缺陷**:`private bool CanSave = true;` 全檔只出現這一次。

- **影響**:無。但讀碼的人會以為有「不可存檔」的卡控。

- **錨點**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM287.cs:28`

- **嚴重度**:**低**

### E.18 `OFDM287` 的 `BF_NO` 條件被複製貼上兩次

- **缺陷**:同一段 `if (model.Utility.Parameters.Rows.Contains("BF_NO"))` 出現兩次,第二次完全重複。

- **影響**:SQL 多一條完全相同的 `AND`,結果不變,但 SQL 變長。

- **錨點**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM287_PO.cs:207-219` 與 `:221-233`

- **嚴重度**:**低**

### E.19 錯誤訊息把 Oracle 原文貼上畫面

- **缺陷**:`AddResultRow(false, 0, ex.Message)`,24 支一致。

- **影響**:`ORA-xxxxx` 含表名欄名的訊息會顯示給一般使用者。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/OFDI612A_PO.cs:171`

- **嚴重度**:**低**(排查很好用,但屬資訊揭露)

### E.20 `OTA.Query` 24 支沒有任何必填檢核,也沒有分頁

- **缺陷**:UI 端沒有 `ValidateErrList.AddError`,PO 端沒有 `ROWNUM` / `FETCH FIRST`。

- **影響**:什麼都不填按查詢就會把整張表撈回 client。

- **錨點**:`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/` 全數無必填檢核;對照 `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/IPJI620.cs:233`

- **嚴重度**:**低到中**(效能與 client 穩定性)

### E.21 沒有出現的缺陷(本片體檢結果)

為了讓後面的人不用重查,以下型別**掃過但本片沒有**:

| 型別 | 本片狀況 |
|---|---|
| bind 變數漏冒號(`= FUND_GROUP` 被當欄名) | **無**。24 支的 bind 名與 `AddInParameter` 名逐一核對過 |
| 欄名串兩次(`Row.Name + Row.Name`) | **無** |
| 繼承 `BasicEVAPO` 導致查詢 NRE | **無 live**,15 次全在註解裡 |
| `catch (SqlException)` 在 Oracle 上是死碼 | **無**。`OTA.Query` 24 支從沒有 MSSQL 版本 |
| 空 `catch` / fail-open | **無**。38 支的 `catch` 都有 `AddResultRow` |
| `LIKE` 樣式餵給 `=` | **無** |
| 迴圈 `break` 吞掉後續資料列 | **無**。本片沒有任何逐列迴圈 |
| 非 UTF-8 來源檔 | **無**。38 支全部讀得起來 |
| Model 與 View 欄數對不上 | **無**。24 支逐支比對,全部一致(§2.3) |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `ATLAS.OTA.Query` 24 支 + `ATLAS.EC.Query` 13 支 + `ATLAS.OFD` 的 `OFDM287`,共 38 支 |

由 build_doc.py v2.0.0 於 2026-09-15 21:04 產生 · 標題 110 · 圖 5 · 表格 63 · 程式錨點 164 · § 連結 139 · 引用檢查：畫面 47（缺 0） · Table 27（缺 0） · 結果集 23（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
