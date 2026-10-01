<!-- 由 tools/build_copilot_kb.py 從 runbooks/add-batch.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS 維護手冊 — 新增 / 維護一支 B 批次

> 產出日期:2026-09-15(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 ⚠ 標「**〔假設〕缺:輸入**」的是拿不到輸入(DB 連線 / PTPFBlock DLL / 選單表 / 部署機)只能推論的部分,附錄 B 彙整;標「**〔客戶特定〕**」的是本站台的值。

> 前提知識在 `architecture.md`:六層與重編順序 `architecture.md §2`、交易邊界 `architecture.md §4.5`、畫面型別 `architecture.md §6.4`、Remoting 與服務 `architecture.md §8.4`。**不要整份讀**。六層樣板細節引用 `runbooks/add-screen.md`,部署引用 `runbooks/deploy.md`,都不重複。素材:`modules/ofdb.md`(18 支)、`modules/ofdb3.md`(35 支)、`modules/ofdb4.md`(35 支),合計 88 支已寫深的批次。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | **新建或維護一支 B(批次)畫面**:按一顆執行鈕、跑一段伺服端作業、改 DB 或產檔 |
| 主要範本 | `OFDB003` 受益人異動批次轉入(**沒有** Remoting 設定、沒有服務,交易由 C# 開) |
| 對照範本 | `OFDB600` 網路交易時限截止(**有** Remoting 設定、有 WindowsService、排程時刻在 DB) |
| 不適用 | M 維護畫面(`runbooks/add-screen.md`)· I 查詢畫面(`runbooks/add-query-screen.md`)· R 報表(`runbooks/add-report.md`) |
| 前提工具與變數 | Visual Studio · Oracle 客戶端 · PTPFBlock DLL · TFS workspace;`%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 佈位符 | `<NEW>` = 新代號 · `<MOD>` = 模組 |

### 0.1 一句話版本與八個步驟

**B 就是 M 拔掉四眼、UI 換成一步式表單。**六層一層都不少,csproj 一個都不能漏。 `architecture.md §6.4` 已證明「I 與 B 是同一份 143 行樣板複製刪減出來的」,B 比 I 多的只有寫入那條路徑。所以本手冊只講**批次特有**的五件事:專案怎麼選、怎麼被觸發、要不要 Remoting、交易誰開、失敗怎麼回報。

| # | 步驟 | 樣板程度 | 節 |
|---|---|---|---|
| 1 | 決定代號與**放哪個專案** | **要查** | §2 |
| 2 | 決定觸發方式(四種) | **要決定** | §3 |
| 3 | 決定要不要 Remoting | **要決定** | §4 |
| 4 | Entity 兩份 xsd + 選卷別 | 半樣板 | §5 |
| 5 | PO:交易、參數、SP、出口 | **全篇重點** | §6 |
| 6 | Control 與 FormProxy | 逐字樣板 | §7 |
| 7 | UI,必要時加 WindowsService | 半樣板 | §8 §9 |
| 8 | 六個 csproj + 編譯部署 | 樣板 | §10 |

## 1. 改動點總覽(圖)

```text
[圖] 批次專案結構:三個專案怎麼選、六層、Entity 分卷、選配的 WindowsService
圖中文字:① 先決定放哪個專案 —— 全庫沒有 Batch 資料夾 / ATLAS.OFDB / 108 支 PO,本業批次的家 / ATLAS.EC / 36 支,網路交易與服務 / ATLAS.OTAB / 41 支,境外平台 / 跟著表走 / 讀寫哪張表就住哪 / ② 六層跟 M 完全一樣,只是 UI 基底不同 / UI <NEW>.cs / xOneStepProcessForm / FormProxy <NEW>_Pxy / 覆寫 Execute / Query / Control <NEW>_Ctl / 只覆寫 DataAccessPool / PO 裸 DAO / 自己 new Database / ③ Entity 兩份 xsd —— 選卷別,不要新開專案 / DataEntity 四卷 / OFDB / 1 / 2 / 3 / UIEntity 四卷 / 卷號必須配對 / 放最大卷 / OFDB3 已 41 份 / View 可精簡 / 批次常只放結果 / ④ 選配第五件:WindowsService(全庫只有四支有) / WindowsService 專案 / 獨立 exe,自帶 config / ProjectInstaller / 帳號 LocalSystem / App.config / Remoting 段在這 / 不重寫邏輯 / 只是另一個呼叫端
```

*圖:圖 1 批次放哪裡。橘色實框=這一步要自己決定;灰虛框=照抄樣板;橘色虛框=只有四支批次會用到、而且是〔客戶特定〕的部署件。全庫沒有 Source/Batch 資料夾,B 畫面就住在六層裡。*

三件事先記住:

1. **沒有 `Source/Batch/` 這種資料夾。**`find Dev -maxdepth 4 -type d -iname "Batch*"` 回 0 筆。B 畫面住在跟 M 完全一樣的六層裡,差別只在代號第四碼是 `B`、UI 基底是 `xOneStepProcessForm`。

2. **代號決定不了專案。**`OFDB` 開頭的批次散在三個專案,見 §2。

3. **批次的失敗是靜默的。**沒有使用者盯著、沒有四眼留痕跡,所以 §6.5 的失敗回報比 M 畫面重要得多。

## 2. 步驟一:決定代號與放哪個專案

### 2.1 現況:`OFDB` 代號散在三個專案

先 `ls` 確認,不要照代號猜:`ls Dev/ATLAS.OFDB/Source/` 得到 `Control Entity FormProxy PO UI`——沒有 Batch。再 `find Dev -name "OFDB*_PO.cs" -o -name "OFDB*OracleDao.cs" | grep -v /obj/`,實測分布:

| 專案 | PO 檔數 | 負責什麼 | 依據 |
|---|---|---|---|
| `Dev/ATLAS.OFDB` | 108 | 本業批次:結帳、過帳、產檔、集保、核印扣款 | `ofdb.md §3.3`、`ofdb4.md §0.4` |
| `Dev/ATLAS.EC` | 36 | 網路交易(EC)相關,三支 WindowsService 也在這 | `ofdb3.md §3.3` |
| `Dev/ATLAS.OTAB` | 41 | 境外平台(OTA)那一套 | `ofdb3.md §3.3` |

全庫 B 畫面 UI 檔分布(排除 Designer):`ATLAS.OFDB` 150 · `ATLAS.OTAB` 45 · `ATLAS.EC` 40 · `ATLAS.RSP` 18 · `ATLAS.COD` / `ATLAS.CRM` 各 5 · `ATLAS.BMS` 3 · `ATLAS.CAS` / `ATLAS.SDM` 各 2 · `ATLAS.DSM` 1。

**同一個代號可能在兩個專案各有一份。**`OFDB562` / `OFDB563` / `OFDB564` 在 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/` 與 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/` 各有一份,不是分岔而是新舊世代;`ATLAS.OFDB` 那三份的基底連線恆為 null,實際跑不起來(`ofdb3.md §2.5`)。

### 2.2 改法:三條決定規則 + 取號

依序套,第一條命中就停:

| # | 規則 | 為什麼 |
|---|---|---|
| 1 | **跟著它要寫的表走。**表由哪個模組的 M 畫面維護,批次就放那個模組 | 重編時 Entity 與 PO 的 `ProjectReference` 才不會跨專案(`architecture.md §2.4`) |
| 2 | **跟著同群連號的既有支走。**`OFDB701`–`OFDB707` 全在 `ATLAS.OFDB`、`OFDB6xx` 多半在 `ATLAS.EC` | 同群常共用 helper 與 entity,拆開就要多一組 `ProjectReference` |
| 3 | **要 WindowsService 就放 `ATLAS.EC` 或 `ATLAS.RSP`。**全庫只有這兩處有 `Source/WindowsService/` | `deploy.md §5` 的四支服務全在這兩處 |

**境外平台(OTA)的批次一律放 `Dev/ATLAS.OTAB`**,即使代號叫 `OFDB6xx`(`OFDB600A` / `OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 全在 OTAB,`ofdb3.md §3.3`)。

取號:同模組同型別最大號 +1,避開 `9xx`(慣例保留給對外申報與跨模組工具)。 **`A` 後綴在批次上沒有一致意義**(`ofdb3.md §0.2`:`OFDB600` 與 `OFDB600A` 是不同業務、不同專案),**新批次不要用 `A` 後綴表達任何語意**。

### 2.3 驗證

`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen <NEW>` 回「找不到」才是對的(代號還沒被用)。建完再跑一次,六層要全部列得出來。

## 3. 步驟二:決定觸發方式

```text
[圖] 批次的四種觸發方式:手動、被別支批次呼叫、WindowsService 的 60 秒 Timer、排程時刻存在資料庫欄位
圖中文字:觸發來源 —— 四種,只有前三種在 repo 裡看得到 / ① 手動按執行 / xOneStepProcessForm / ② 被別支批次叫 / Pxy 再包一層 / ③ 服務 60 秒 Timer / 比對 HHmm 字串 / ④ 時刻在 DB / 改欄位不重編 / ④ 的細節:時刻欄由 SQL 五段 UNION 撈出來 / OFD606A 四個時間欄 / 申購 匯款 贖回 定額 / OFD600A 一個時間欄 / MEMBER_CHG_LIMIT / GetTIMES 算最近一次 / 存成 HHmm 字串 / 跑完再算 / finally 重算 / 四種觸發最後都收斂到同一個入口 / FormProxy.Execute / 唯一入口 / Control.Execute / 取 PO 實例 / PO.Execute / 交易 + SP + 出口 / ⚠ 帳號決定跑不跑 / UserName 判斷
```

*圖:圖 2 四種觸發。第四種是本手冊最容易被忽略的一條:排程時刻不在 Windows 排程器、也不在設定檔,而是資料表的欄位;改時間不用重編,但也查不到是誰設的。*

### 3.1 現況:四種,不是三種

| # | 觸發 | 在 repo 裡怎麼看出來 | 幾支 |
|---|---|---|---|
| 1 | **手動**:使用者按「執行」 | UI 繼承 `xOneStepProcessForm`,有 `BeforeExecuteButtonClicked` | 絕大多數 |
| 2 | **被別支批次呼叫** | 另一支的 Ctl / PO 裡 `new <代號>_Pxy()` | 少數 |
| 3 | **WindowsService**:獨立 exe,60 秒 Timer | `Dev/<專案>/Source/WindowsService/WindowsService.<代號>/` 存在 | **4 支** |
| 4 | **排程時刻存在資料庫**:服務每分鐘比對 `HHmm` | 服務的 `GetTIMES()` 去撈時刻欄 | 3 支 |

第 3 與第 4 疊在一起:服務提供「每分鐘檢查一次」的心跳,**真正的排程時間在資料表欄位裡**。

### 3.2 現況:第四種的完整機制(本手冊最值得記住的一段)

以 `OFDB600` 為例:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 建構子掛 `Interval = 60000`(60 秒)的 `System.Timers.Timer` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:24-31` |
| 2 | `OnStart` 先讀自己的 `exe.config` 設 Remoting,再 `GetTIMES()` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:39-58` |
| 3 | `GetTIMES()` 透過 Pxy 撈候選時刻,各加 `LIMIT_TIME_BUFFER` 分鐘,已過的推到明天,取最近一個存成 `"HHmm"` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:109-155` |
| 4 | 每分鐘比對 `sTIMES == DateTime.Now.ToString("HHmm")`,相等才跑 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:65-75` |
| 5 | 跑完 `finally` 再 `GetTIMES()` 算下一次 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:103-106` |

候選時刻的 SQL 是五段 `UNION`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292`):`OFD606A` 的申購 / 匯款 / 贖回 / 定額四個截止時間欄(各被對應的 `*_YN = 'Y'` 過濾)再 `UNION` `OFD600A` 的 `MEMBER_CHG_LIMIT_TIME`。`OFDB609` 讀 `OFD600A`、`OFDB680` 讀 `OFD680A`(`ofdb3.md §3.3`)。

> ⚠ **要改排程時間,不用重編、也不用碰 Windows 排程器,改資料表欄位就好。** 反過來說:**排錯時間時查不到「是誰設的」**——這些欄位由哪支 M 畫面維護,三片批次篇都沒查到。

### 3.3 改法:新批次選哪一種

| 需求 | 選 | 要做什麼 |
|---|---|---|
| 人工決定什麼時候跑 | ① 手動 | 只做六層,不加服務 |
| 固定時間跑,時間**不會改** | ③ 服務 + 時刻寫 `App.config` | 加一個 WindowsService 專案(§9) |
| 固定時間跑,時間**業務會調** | ③ + ④ 服務 + 時刻欄放 DB | 同上,再加設定表欄位與維護它的 M 畫面 |
| 跟在別支批次後面 | ② 被呼叫 | 在前一支的 Ctl 裡 `new <NEW>_Pxy()` |

**預設選 ①。**88 支樣本裡只有 3 支走到第四種;多一支服務就多一台要部署、要監控、要處理帳號的機器(§9.2)。

### 3.4 改法:`Main(string[] args)` 的參數慣例

**先確認現行主流寫法:沒有 `args`。**`ofdb3.md §6.1.3` 實測那 35 支:`Main()` 一律不收 `string[] args`,repo 內也沒有任何 `.bat`;`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13` 的簽名就是 `static void Main()`。

參數有三個來源,**全部按名字取,不是按位置**:

| 來源 | 怎麼取 | 錨點 |
|---|---|---|
| 畫面欄位 | UI 端 `Util.Parameters.AddParametersRow("<名>", SQLOperator.Equal, 值)` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:43-48` |
| 服務自動跑 | 服務端自組同一組 `AddParametersRow`,使用者寫死字串 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:84-86` |
| 設定表 | PO 自己去撈 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292` |

PO 端的樣板(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:55-62`):

```
if (vdb.Utility.Parameters.Rows.Contains("CHECK_DATE"))
{
    DataModelUtility.ParametersRow Row = (DataModelUtility.ParametersRow)vdb.Utility.Parameters.Rows.Find("CHECK_DATE");
    if (!string.IsNullOrEmpty(Convert.ToString(Row.Value)))
        db.AddInParameter(cmd, "wCHECKDATE", OracleDbType.Date, ConvertTo.DateTimeorDBNull(Convert.ToDateTime(Row["Value"])));
}
```

`OFDB003` 用包好的 `GetParamValue`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:72-78`),兩種都可以。

**「位置取參數」是已知缺陷,但它不在 `Main()`,在讀檔與下拉選單:**

| 缺陷型 | 實例與錨點 |
|---|---|
| 用陣列索引取 CSV 欄位 | `OFDB560` 的 `strData[0]`~`strData[14]`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs:64`、`:72-84`),上游調欄序就整批對錯 |
| 用列索引隱藏下拉選項 | `OFDB019A` 的 `ucomMSG_TYPE.Rows[3].Hidden = true`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:42`) |
| 用選鈕索引換算 SP 參數 | `OFDB019B` 的 `CheckedIndex + 2`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:78`) |
| 固定位移拆字串 | `OFDB901` 的 `Substring(0,11)` + `Substring(11,4)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:73`) |

**怎麼避:任何「第 N 個」都要換成「叫什麼名字」。**讀檔用表頭比對欄名、下拉用 `TextValue` 找、拆字串用分隔符。真的是定長檔案格式時,把位移抽成具名常數集中宣告,不要散在四個方法裡(`OFDB950` 的反例:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:86`、`:120`、`:146`、`:183`)。

### 3.5 驗證

手動:執行鈕亮得起來。服務:`sc start <NEW>_Service` 後看事件檢視器有沒有 `Execute Error`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:92`)。第四種:把時刻欄改成「現在 + 2 分鐘」,兩分鐘內應該要跑;不跑先查 §12 的「服務在跑但不動作」。

## 4. 步驟三:要不要 Remoting

### 4.1 現況:同一批批次,有的有有的沒有

`ofdb3.md §3.4` 把三個專案的 **20 個 `App.config` 全部查過**:

| `App.config` | `system.runtime.remoting` | `<wellknown>` | `<connectionStrings>` |
|---|---|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | **有**(`:175-194`) | **1 個**(`:189`) | 無 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` | **有**(`:175-194`) | **1 個**(`:189`) | 無 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config` | **0 個** | 0 | **有(3 筆,`:246-262`)** |
| 其餘 17 個(UI / PO / Control / FormProxy / Entity 各層) | 0 | 0 | 無 |

> ⚠ 那三筆 `<connectionStrings>` **含明文帳密**。本手冊只記位置(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config:246-262`),**不抄值**。`architecture.md §8.7` 已標同型問題。

### 4.2 現況:`OFDB680` 少了 `<wellknown>`,結果是什麼

三支服務的 `OnStart` 幾乎逐字相同,都呼叫 `RemotingConfiguration.Configure(自己的 exe.config)`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50-52`)。但 **`<wellknown>` 才是讓 `new <代號>_Pxy()` 變成遠端代理的那一行**。沒有它,`new` 出來的是本機物件,`FormProxy → Control → PO` 全跑在服務自己的行程裡——這正好解釋為什麼只有它的 config 需要 `<connectionStrings>`。

| 類型 | 誰 | 那台機器需要什麼 |
|---|---|---|
| **真 Remoting 客戶端** | `OFDB600`、`OFDB609` | Remoting 端點設定;**不需要**資料庫權限 |
| **直連資料庫的行程** | `OFDB680`、`RSPB008` | `TA` / `SWProduct` / `Logging` 三個帳號的連線權限 |

> 〔假設〕`OFDB680` 是設定檔漏了 Remoting 區段,不是刻意設計——依據是三支的 `OnStart` 幾乎逐字相同。但 `<connectionStrings>` 又不像意外多出來的,**兩種解釋都成立,沒有註解可判**(`ofdb3.md §3.4`)。

### 4.3 改法:新批次怎麼決定

**只有一個判準:這支批次會不會以「非 UI 的宿主」去打伺服端的 FormProxy。**

| 情境 | 要不要自己的 Remoting 設定 | 做法 |
|---|---|---|
| 只有畫面觸發(①)或被同行程的批次呼叫(②) | **不要** | 什麼都不加。Remoting 邊界由主程式管,落在 UI → FormProxy 之間(`architecture.md §8.1`) |
| 有服務,而且邏輯要跑在伺服端(③④) | **要** | 抄 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:175-194`,把 `<wellknown>` 的 `type` 與 `url` 換成 `<NEW>_Pxy` |
| 有服務,而且就是要在服務那台直連 DB | **不要,但要 `<connectionStrings>`** | 照 `RSPB008` 的形狀(`architecture.md §8.4`):csproj 參考 `Control.<MOD>` 而不是 `FormProxy.<MOD>` |

**不要學 `OFDB680`:程式碼呼叫 `RemotingConfiguration.Configure` 卻沒有 `<wellknown>`。**兩種都合法,混在一起是最難查的那種。

### 4.4 驗證

拿掉 DB 權限後在服務那台跑:走 Remoting 的應照常成功(它不碰 DB);沒走 Remoting 的會在第一個查詢失敗。**〔假設〕缺:部署機**,未實測。

## 5. 步驟四:Entity —— 兩份 xsd 與卷別

### 5.1 現況:批次的 xsd 裝的多半不是實體表

`ofdb.md §2.3` 與 `ofdb4.md §2.8` 都查過:批次 Model 裡的 DataTable **大半是「SP 的 RefCursor 出參形狀」**,不是實體表。`OFDB003` 的 Model 有 10 張 DataTable,其中 5 張對應 SP 的 5 個 RefCursor(`Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd`,352 行);它的 View 只有 79 行(`Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/OFDB003View.xsd`)。

**批次的 View 通常比 Model 精簡很多**,因為只有要顯示的那幾張才需要送回用戶端。這點和 M 相反:M 的兩份幾乎逐字相同(`add-screen.md §4.1`)。

### 5.2 改法:卷別怎麼選,後綴怎麼取

`Dev/ATLAS.OFDB/Source/Entity/` 底下有**四組** Entity 專案,實測 `.xsd` 數:`OFDB` 19 / `OFDB1` 18 / `OFDB2` 27 / `OFDB3` **41**(UIEntity 側 19 / 17 / 27 / 41)。

規則和 M 一樣(`add-screen.md §10.2`):**放進編號最大的那一組**(這裡是 `OFDB3`),**Model 與 View 的卷號必須配對**。分卷是為了避開 typed DataSet 專案過大,不是業務分群(`ofdb4.md §0.4`)。 `ATLAS.EC` 的批次 entity 全在 `DataEntity.EC` / `UIEntity.EC`(不分卷);`ATLAS.OTAB` 在 `DataEntity.OTA` / `UIEntity.OTA`(組件名是 `DataEntity.OTAB`)。

**`_9i` 後綴不要再用。**`OFDB600` 的 xsd 叫 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd` / `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/OFDB600_9iView.xsd`;`_9i` 是第二代控件的後綴(`architecture.md §7.3`),掃描器會因此判「缺 entity」(`ofdb3.md §3.5` 列了 8 支)。**新批次一律 `<NEW>Model.xsd` / `<NEW>View.xsd`。**

### 5.3 現況:可以少建這兩層,但不建議

`architecture.md §6.6` 實測:B 型有 28 支**沒有 DataEntity + UIEntity**,是四型裡唯一常態性少層的,條件是「跑完不回傳任何資料集」。但建 xsd 的成本是十分鐘(全是樣板),省下來換的是「以後要顯示任何東西都得回頭補兩份 xsd 與六個 csproj 段」。**新批次一律建齊。**

### 5.4 驗證

xsd 骨架、10 個 `msprop`、csproj 三段全照 `add-screen.md §3`。批次特有的只有一條:`atlas_scan.py --screen <NEW>` 的 `DataEntity` 與 `UIEntity` 兩列要有路徑;**「主檔 —」是正常的**,批次不宣告 `xTableMapping`(§6.1)。

## 6. 步驟五:PO —— 全篇重點

```text
[圖] 批次的執行流程與失敗處理:UI 驗證、C# 開交易跑 SP、commit 後才做不可回復的動作、三條失敗路徑
圖中文字:① 按下執行之前 —— UI 端,唯一能真的擋住的地方 / DoValidate 必填 / validatorManager1 / 組 Parameters / AddParametersRow / Pxy.Check 前置查詢 / 數一數會動幾筆 / e.Cancel = true / 不設就照跑 / ② PO 裡的交易邊界 —— C# 開、C# 關,SP 跑在裡面 / GetStoredProcCommand / 先建 cmd 再開交易 / BeginTransaction / 一定寫在 try 裡面 / LoadDataSet 帶 tran / SP 參與同一交易 / 看回傳再決定 / 不要寫死 i = 1 / ③ 兩條出口 —— Commit 之後才做不可回復的事 / Commit / 先落地 / 寄信 / 產檔 / 呼外部 / commit 之後才做 / AddResultRow(true, n) / n 要是真筆數 / 換頁顯示結果 / ExecuteDataLoad / ④ 失敗路徑 —— 三條,每一條都要留下原因 / Rollback 前檢查 null / 否則 NRE 蓋掉原因 / 訊息不可空字串 / 空訊息 = 查不到 / 寫 log 表或 EventLog / repo 內無統一 log 表 / 禁止空 catch / 吞了就永遠不知道
```

*圖:圖 3 執行流程與失敗處理。橘色實框=新批次一定要自己寫對的地方;橘色虛框=現存批次最常寫錯、而且錯了不會有人發現的地方。順序不可調換:寄信與產檔一律排在 Commit 之後。*

### 6.1 現況:四種世代,新的只用第一種

`ofdb4.md §0.3` 把 35 支逐支查過:

| 世代 | 基底 | 連線 | 宣告 `xTableMapping` | 支數 |
|---|---|---|---|---|
| **裸 PO(主流)** | 無基底,只實作 `I<代號>_PO` | 自己 `new Database("TA", DbServerType.Oracle)` | 無 | 22 |
| EVA 滿血 | `BaseEVADaoPO` | 基底管(`dbProduct`) | 有 | 3 |
| MultiRow EVA | `BaseMultiRowEVADaoPO` | 基底管 | 有 | 1 |
| **舊世代(禁用)** | `BasicEVAPO` | **`dbTA` 恆為 null** | 多半無 | 5 |

**新批次用裸 PO。**批次的輸出是 DB 狀態改變或外部檔案,不是回傳資料集,不需要 `xTableMapping`,四眼那套也用不上。 **絕對不要繼承 `BasicEVAPO` / `MultiRowEVAPO`**,連查詢都會 NRE(`add-screen.md §5.7`、`architecture.md §3.1.1`)。

### 6.2 改法:骨架五件

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs` 全檔 508 行:

| 件 | 錨點 | 內容 |
|---|---|---|
| 介面 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:20-29` | `public interface IOFDB003_PO { T Execute<T>(T model, params object[] args); … }`——**不繼承 `IEvaDataAccess`** |
| 類別宣告 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:32-33` | `[PODbType(DbServerType.Oracle)]` + `: IOFDB003_PO`,沒有基底 |
| 連線欄位 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:36` | `Database dbTA = new Database("TA", DbServerType.Oracle);` |
| `Execute<T>` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:57-155` | 交易 + SP + 判斷 + Commit / Rollback |
| 前置檢查 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:315-322` | `Check<T>`,給 UI 在按執行前問一次 |

要兩個庫(`TA` + `SWProduct`)就宣告兩個 `Database`,但**沒有分散式交易**,兩邊各自 Commit(`architecture.md §4.5`);一邊成功一邊失敗就對不起來。**能只用一個庫就只用一個。**

### 6.3 改法:交易邊界誰開 —— C# 開,SP 跑在裡面

`ofdb.md §6.0` 的總表:18 支裡 17 支是 **C# 端 `BeginTransaction`,SP 參與同一交易**,只有 1 支走 EVA 基底讓框架管。照抄的順序(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:62-119`):

```
DbTransaction tranUpdate = null;
try
{
    DbCommand cmd = dbTA.GetStoredProcCommand("s_TA_OFDB003_Excute");
    // 綁 IN 參數(按名字取,見 §3.4);綁 OUT 參數:RefCursor 一張表一個
    tranUpdate = dbTA.BeginTransaction();
    dbTA.LoadDataSet(cmd, mModel.DataEntity, tranUpdate, new string[] { "OFDB003", … });
    // 判斷結果,不成立就 Rollback
    if (tranUpdate.Connection != null) { tranUpdate.Commit(); }
}
```

五條規則:

1. **`BeginTransaction()` 一定寫在 `try` 裡面。**寫在外面時,開交易本身失敗的例外會穿過 PO 打到 FormProxy,使用者看到框架錯誤(`OFDB608` / `OFDB616` 的反例,`ofdb3.md` E5.8)。

2. **`Commit` / `Rollback` 之前檢查 `tranUpdate.Connection != null`。**`OFDB003` 有做(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:100-101`、`:118-119`);沒做的會在 catch 裡再噴一個 `NullReferenceException`,**把原始例外蓋掉**。

3. **執行 SP 一定把 `tran` 傳進去**,否則 SP 跑在自己的交易裡,C# 的 Rollback 管不到它。

4. **`finally` 裡釋放**:`if (tranUpdate != null) { dbTA.Dispose(tranUpdate); } else { dbTA.Dispose(); }`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:148-153`)。

5. **不要抄 `CommandTimeout = 0`。**全庫 9 處以上寫著「此程式讓它永久跑」(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:51`),卡住的 SP 不會超時,只會一直佔連線。新批次給一個明確秒數。

### 6.4 改法:重跑安全

`ofdb3.md §3.3` 把 35 支分四類:`阻擋` 6 · `覆蓋` 4 · **`不保護` 19** · `不可執行` 4。 **「不保護」是現況的多數,不是可以照抄的慣例。**新批次二選一:

| 做法 | 怎麼寫 | 適用 | 實例 |
|---|---|---|---|
| **先 DELETE 再 INSERT(覆蓋)** | 用一把能唯一決定本批範圍的鍵先 `DELETE`,同一交易內再寫 | 產出型(產名單、產檔、產申報資料) | `OFDB570` 先 `DELETE … WHERE Data_ID`、`OFDB671` 先 `DELETE OFD678A` |
| **已處理旗標(阻擋)** | 來源列有處理碼欄,只撈 `= '0'` 的,跑完改成 `'1'` | 交易處理型 | `OFDB600` 靠七張表的處理碼欄過濾(`ofdb3.md §6.1`) |

**用「覆蓋」時那把鍵必須是決定性的。**`OFDB680` 的重跑鍵是「基金清單 + 日期 + `-1`」拼出來的字串,中途基金上下架就變了鍵值,舊資料刪不掉、重跑會重複(`ofdb3.md` E12.6)。 **用「旗標」時,旗標與撈取條件要寫在同一支 SQL 裡。** 另外,提供「取消 / 回復」功能是 ATLAS 既有慣例(`OFDB222` 取消關帳、`OFDB286` 取消退匯、`OFDB281` 有「重新產生」與「刪除」,`ofdb.md §6.0`)。**能做就做,它比 rollback 好用。**

### 6.5 改法:失敗回報 —— 不可吞例外

三片批次篇的附錄 E 裡,「一律回報成功」與「例外被吞」合計 20 條以上,是**批次的頭號坑**。規則:

| # | 規則 | 反例 |
|---|---|---|
| 1 | **`catch` 一定要留下原因**,訊息不可是 `string.Empty` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:100` |
| 2 | **不可有空 `catch { }`** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151`,整個時刻消失且無 log |
| 3 | **不要寫 `catch (SqlException)`**,連線是 Oracle,這個 catch 永遠進不去,是死碼 | 全庫 6 處以上(`ofdb3.md` E2.5) |
| 4 | **例外要進 `CommonExceptionBlocker.HandleBusinessException(ex)`** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:133-138` 連這行都沒有 |
| 5 | **回傳的 VDB 要和塞訊息的 VDB 是同一個** | `OFDB615` / `OFDB616` 訊息寫進輸入的 vdb、回傳新建的 result,呼叫端看不到失敗(`ofdb3.md` E4.6) |

**寫哪張 log 表?repo 內沒有統一的批次 log 表。**現況三條各走各的:

| 管道 | 誰在用 | 位置 |
|---|---|---|
| `Utility.Result`(回給畫面) | 全部 | `AddResultRow(bool, int, string)` |
| `CommonExceptionBlocker`(框架 log) | 多數 PO | 落地在 `C:\Vendor\VendorProduct\*.log`(`architecture.md §8.5`)〔客戶特定〕 |
| Windows `EventLog` + 自寫文字檔 | 三支服務 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:92`、`:239-252` |

**新批次三條都走。不要抄那個自寫文字檔的 `WriteLog`**——它先整檔讀進記憶體再整檔覆寫,複雜度 O(n²),寫到一半當掉整天的 log 就沒了(`ofdb3.md` E9.5)。

### 6.6 改法:出口有四種,順序不可調

| 出口 | 幾支(35 支樣本) | 規則 |
|---|---|---|
| 呼叫 SP,DB 狀態被改 | 18 | 一定帶 `tran`;SP 回的 RefCursor 要接進 Model |
| C# 自己組 SQL 寫表 | 12 | 參數化(§14.8);`ExecuteNonQuery` 的回傳值**要用** |
| 產生 / 讀取外部檔案 | 6 | 明確指定編碼,不要 `Encoding.Default` |
| 寄信 / 呼叫外部 API | 8 | **一律排在 `Commit` 之後** |

數字出自 `ofdb3.md §6.0`(同一支可能有多個出口,相加大於 35)。

> ⚠ **最後一條是硬規則。**`OFDB600` 在 `tran.Commit()` **之前**就 `SendMail`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:75-76` 對 `:84`):commit 失敗時信已寄出、資料卻回滾。寄信、產檔、呼叫外部系統都是不可回復的動作,**放在交易裡等於把交易的保證作廢**。

`OFDB003` 做對了這件事:LDAP 同步排在 `Execute` 回來之後(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:59-61`),但它換了另一個問題——LDAP 失敗時把 `Result` 清掉改塞失敗訊息,**使用者看到「失敗」,DB 其實已經生效**(`ofdb.md §6.1`)。正確做法是**兩個結果分開回報**。

### 6.7 驗證

| # | 查什麼 | 怎麼查 |
|---|---|---|
| 1 | 有沒有寫死成功 | `grep -n "AddResultRow(true" <PO>`,每處後面的筆數都要是變數,不可是常數 |
| 2 | 有沒有空訊息 | `grep -n "string.Empty)" <PO>`,出現在 `AddResultRow(false` 那行就是缺陷 |
| 3 | 有沒有空 catch | `grep -n -A2 "catch" <PO>` 逐處看 |
| 4 | 交易有沒有帶進 SP | `grep -n "LoadDataSet" <PO>`,每處都要有 `tran` |
| 5 | 寄信 / 產檔在哪 | `grep -n "SendMail\|StreamWriter\|Commit" <PO>`,行號上 `Commit` 必須在前 |

## 7. 步驟六:Control 與 FormProxy —— 逐字樣板

Control 只覆寫一個初始化方法 + 一個業務入口(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:35-38` 與 `:52-70`):

```
public override void InitializeDataAccessPool() { base.DataAccessPool.Add(new <NEW>_PO()); }

public <NEW>ViewVDB Execute(<NEW>ViewVDB view)
{
    var m_PO = base.GetDaoInstance<I<NEW>_PO>();
    return (<NEW>ViewVDB)this.ExecPOActionToViewVDB(view, m_PO.Execute);
}
```

**批次的 Ctl 不覆寫 `InitializeVDBTypes()`**(那是 M 用來接四眼的),也不覆寫 `CustomTransfer*` 四件套,除非要自己搬表。`OFDB600` 的 Ctl 同形(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:150-154`)。

FormProxy 覆寫 `Execute`,例外一律轉成 `ServerSideError`(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:34-49`)。需要「按執行前先數一數」就多開一個方法(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:56-71` 的 `Check`),UI 端在 `DoValidate` 裡呼叫。 `Query` 在純批次裡是空殼,回 `(true, 0, "")`(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:77-82`)。**想做成「先查清單、勾選、再按執行」就把 `Query` 實作出來**——`ofdb3.md §3.2` 查到 12 支批次是這樣寫的。

**驗證**:`grep -c "InitializeControl" <NEW>_Pxy.cs` 應為 0(那是 M 的樣板);`GetDaoInstance` 的泛型參數必須是介面型別,打錯會在執行期回 `ServerSideError`。

## 8. 步驟七:UI —— `xOneStepProcessForm`

`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs` 全檔 118 行,是最乾淨的批次 UI 範本,三個掛點:

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `<NEW>_FormInitial` | `TabPages` / `ProcessVDB` / `SetPermissionInfo` / `FormProxy` 四件 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:69-76` |
| `<NEW>_RefreshPage` | 關查詢鈕、開執行鈕、帶預設值 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:99-104` |
| `<NEW>_BeforeExecuteButtonClicked` | 驗證,不過就 `e.Cancel = true` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:83-92` |

驗證集中在 `DoValidate`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:33-59`):先 `ValidateErrList.Clear()` → `validatorManager1.DataValidate()` → 自訂檢核 → 有錯就回 → 清空並重組 `Parameters`。三條規則:

1. **參數名要跟 PO 端 `Rows.Contains("…")` 的字串一模一樣**(§3.4)。又一個靠字串對上的跨層綁定,打錯不紅字、條件靜靜不生效。

2. **`BeforeExecuteButtonClicked` 沒設 `e.Cancel = true` 就等於沒擋。**`OFDB673` 的「是否同意變更?」按「否」也照樣執行,就是漏了這一行(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89-93`)。

3. **「還有 N 筆沒處理完」這種前置檢查是詢問不是阻擋。**`OFDB003` 跳 `Warn02` 讓使用者按 OK 繼續(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:52-54`);想真的擋就 `return false`,不要用對話框。

**驗證**:開畫面 → 什麼都不填按執行 → 必填訊息要跳出來且擋住,再把每條自訂檢核各觸發一次。

## 9. 步驟七之一(選配):加一個 WindowsService

**只有 §3.3 判定要走第 ③ 或第 ④ 種觸發時才做這一步。**四支服務的清單與安裝指令在 `deploy.md §5`,本節不重複。

### 9.1 改法:一個服務專案有五個檔

抄 `WindowsService.OFDB600` 換名字:

| 檔 | 內容 | 錨點 |
|---|---|---|
| `<NEW>_Service.cs` | Timer + `OnStart` + `DoExecute` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:24-31` |
| `Program.cs` | `Main()`(不收 `args`)+ 執行模式判斷 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13`、`:28-44` |
| `ProjectInstaller.cs` + Designer | 服務名與帳號 | 見 `deploy.md §5` |
| `App.config` | Remoting 段(§4.3) | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:175-194` |
| `WindowsService.<NEW>.csproj` | `OutputType` `WinExe`、`TargetFrameworkVersion` `v4.8` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj:9`、`:22` |

**csproj 的參考全部是 `HintPath` 指向 `%PTPF%` 的預編 DLL**,不是 `ProjectReference`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj:74-101`)。所以**改了 `FormProxy.<MOD>` 或 `UIEntity.<MOD>` 之後,不更新 `%PTPF%` 的話服務拿到的還是舊的**——正是 `deploy.md §2` 講的 DLL 覆寫陷阱。服務專案**不在任何模組 sln 裡**,要自己開(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.sln`)。

### 9.2 ⚠ 服務帳號不能改成網域帳號

```
if (Environment.UserName == "SYSTEM") { ServiceBase.Run(ServicesToRun); }
else { var DebugToRun = new <NEW>_Service(); DebugToRun.Start(); Console.ReadLine(); }
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28-44`。配合安裝時的 `ServiceAccount.LocalSystem`,`UserName` 才會是 `"SYSTEM"`。**換成網域帳號就走進 else、卡在 `Console.ReadLine()`,SCM 等到逾時判定啟動失敗,而且沒有任何錯誤訊息。**

`deploy.md §5` 已記過這條。**新服務不要抄這個判斷**——要區分除錯模式就用命令列旗標或 `#if DEBUG`,不要用執行帳號。

**驗證**:`sc start <NEW>_Service` → 狀態要停在「執行中」而不是「正在啟動」。停在「正在啟動」直接看上面那段。

## 10. 編譯與部署

### 10.1 六個 csproj,不會多出組件

| 專案 | 加什麼 | 錨點(`OFDB003` 範本) |
|---|---|---|
| `DataEntity.<卷>` | `Compile` × 2 + `None` × 3 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/DataEntity.OFDB.csproj:102-107` 與 `:233-243` |
| `UIEntity.<卷>` | 同上 | `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/UIEntity.OFDB.csproj:102-107` 與 `:233-243` |
| `PO.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:132` |
| `Control.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/Control.OFDB.csproj:140` |
| `FormProxy.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/FormProxy.OFDB.csproj:104` |
| `UI.<MOD>` | `Compile` × 2 + `EmbeddedResource` × 1 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj:321-325` 與 `:1225-1226` |

> ⚠ **`UI.OFDB.csproj:324` 掛的是 `OFDB003.designer.cs`,小寫的 `d`。**同一個專案裡兩種大小寫並存,Windows 編得過,大小寫敏感的工具會判缺。**新批次一律用 Visual Studio 產生的大寫 `.Designer.cs`。**

有服務的話再加第七個 `WindowsService.<NEW>.csproj`(§9.1)。

### 10.2 重編順序與部署到哪

重編順序照 `add-column.md §9.1`(Entity → PO → Control → FormProxy → UI),依據在 `architecture.md §2.4`。部署對照表是 `deploy.md §2`,批次沒有例外:

| 你改了 | 客戶端 | 伺服端 IIS | WindowsService |
|---|---|---|---|
| `UI.<MOD>`(批次畫面) | ✔ |  |  |
| `UIEntity.<卷>`(`View.xsd`) | ✔ | ✔ | ✔(若該服務用到) |
| `FormProxy.<MOD>` / `Control.<MOD>` / `PO.<MOD>` / `DataEntity.<卷>` |  | ✔ |  |

**服務那台要什麼看 `deploy.md §5`**:自己的 exe 與 `exe.config`、`FormProxy.<MOD>.dll`、`UIEntity.<MOD>.dll`、共用層、PTPFBlock。**它要的是「客戶端那一套」加自己的 exe,不是伺服端那一套**(`deploy.md §2` 第 3 條規則)。換伺服器時四支服務的 `exe.config` 都要改。

> **〔假設〕缺:PTPFBlock DLL / 部署機。**整個 §10 未實測(`architecture.md 附錄 C.1`)。csproj 三段來自 `OFDB003` 原文,重編順序來自 `ProjectReference` 相依。

## 11. 驗證清單

第一輪先確認六層接上:

| # | 動作 | 過的條件 | 沒過回去做 |
|---|---|---|---|
| 1 | `atlas_scan.py --screen <NEW>` | 六層都有路徑 | §5 §10.1 |
| 2 | 依 `add-column.md §9.1` 順序重編六個專案 | 六個都成功 | §10.1 |
| 3 | 開畫面、什麼都不填按執行 | 版面出得來;必填訊息跳出來且擋住 | §8 |

第二輪跑真的:

| # | 動作 | 查什麼 |
|---|---|---|
| 4 | 給**查無資料**的條件執行 | 要回「查無可執行之資料」而不是「成功 0 筆」,且已 Rollback(§6.5) |
| 5 | 給**正常**條件執行 | 回報筆數要等於 DB 實際變動筆數(§6.7 第 1 條) |
| 6 | **同樣條件再跑一次** | 依 §6.4 選的策略,要嘛被擋、要嘛結果相同,不可變兩倍 |
| 7 | 執行中**故意讓 SP 失敗**(給不存在的鍵) | DB 完全沒動、訊息有內容、框架 log 有一筆 |
| 8 | 有出口的話:把 Commit 那步中斷 | 信不可已寄出、檔不可已產生(§6.6) |
| 9 | 有服務的話:改時刻欄成「現在 + 2 分鐘」 | 兩分鐘內跑起來;`EventLog` 沒有 Error |

**第 4、6、8 最容易失敗**,而且失敗時不會有人發現——它們對應的正是 §14 的頭幾條反例。

## 12. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **回報成功,DB 一筆都沒動** | `ExecuteNonQuery` 回傳值被常數蓋掉,或成功訊息寫死 | §6.5 §6.7 |
| **回報失敗,但資料其實已經生效** | Commit 之後的動作失敗時把 `Result` 清掉重塞 | §6.6 |
| **使用者看到空白錯誤訊息** | `AddResultRow(false, 0, string.Empty)` | §6.5 |
| **重跑一次資料變兩倍** | 沒有 DELETE 也沒有旗標 | §6.4 |
| **信寄出去了,資料卻沒進去** | 寄信排在 Commit 之前 | §6.6 |
| **服務裝起來,狀態卡在「正在啟動」** | 用非 `LocalSystem` 帳號安裝 | §9.2 |
| **服務在跑,但就是不動作** | 時刻欄格式不足四碼被例外吞掉,或設定表有第二列 | §3.2 §6.5 |
| **改了 `FormProxy` 重編了,服務行為沒變** | 服務走 `HintPath` 綁 `%PTPF%` 的 DLL | §9.1、`deploy.md §2` |
| **執行鈕按下去什麼都沒發生** | `e.Cancel = true` 被無條件執行 | §8 |
| **`ORA-01008` 或參數對不上** | `AddInParameter` 的名字多一個冒號,或與 SP 宣告不符 | §3.4 |
| **例外訊息是「ServerSideError」** | PO 的例外穿過 Ctl 打到 Pxy | §6.3 第 1 條 |
| **凌晨跑跟白天跑結果不同** | 日期補丁只改了一半的表 | §14.6 |

## 13. 接手一支不熟的批次

跑完 `atlas_scan.py --screen <代號>` 之後查這六件事,每件都有固定看法:

| 要知道 | 去哪看 |
|---|---|
| 怎麼被觸發 | `Dev/<專案>/Source/WindowsService/` 底下有沒有同名資料夾;沒有就是純手動 |
| 要不要 Remoting | 該服務的 `App.config` 搜 `system.runtime.remoting` 與 `<wellknown>` |
| 交易誰開 | PO 裡搜 `BeginTransaction`;搜不到就是走 EVA 基底或根本不開 |
| 能不能重跑 | PO 裡搜 `DELETE`;沒有就再搜處理碼欄的 `= '0'` |
| 出口是什麼 | PO + Ctl 裡搜 `SendMail` / `StreamWriter` / `GetStoredProcCommand` |
| 有沒有踩到已知坑 | 直接讀 `ofdb.md 附錄 E` / `ofdb3.md 附錄 E` / `ofdb4.md 附錄 E` 裡有沒有點名它 |

## 14. 反例:新批次不要這樣寫

八條,全部來自三片批次篇的附錄 E。**共同點是「錯了不會有人發現」。**

### 14.1 `catch` 吞例外 / 空 `catch { }`

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151` 是一個完全空的 `catch { }`:時刻字串格式壞掉時,那個時刻整個消失、批次當天不跑,而且**沒有任何 log**(`ofdb3.md` E4.4)。同型:`OFDB731` 的存檔方法是 `catch { return false; }`,磁碟滿 / 權限不足 / 路徑太長全被吞成同一句(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:514-517`);`OFDB913` 連 `HandleBusinessException` 都沒有(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:133-138`)。

**正確寫法:`catch (Exception ex)` → 塞有內容的 `AddResultRow(false, 0, …)` → `CommonExceptionBlocker.HandleBusinessException(ex)`。**

### 14.2 fail-open 檢核:查詢炸掉等於檢核通過

```
bool boolvalue = true;
try { …查 DB… }
catch { }          // ← 不改值
return boolvalue;  // ← 永遠 true
```

`ofdb3.md` E4.1 實測 **`OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 的 27 個檢核方法全部是這個形狀**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:284`、`:313-319`)。效果:DB 連不上、表改名、權限不足 → **所有前置卡控「通過」→ SP 照跑**。同型:`OFDB605` 的兩支驗證方法例外時 `return true`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:206-210`、`:259-263`);`OFDB281` 六支檢核全部 `return true`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:88-92`)。

**正確寫法:檢核方法初值給 `false`,只有真的查到「可以放行」的證據才改 `true`;例外一律往外丟或回 `false`。**

### 14.3 `i = 1;` 蓋掉 `ExecuteNonQuery` 的回傳值

```
int i = db.ExecuteNonQuery(cmd, tran);
i = 1;                       // ← 這一行讓上面那行的結果消失
if (i == 1) tran.Commit();   // ← else 永遠到不了
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:285-286` 與 `:405-414`(`ofdb3.md` E3.2)。同型:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:97` 與 `:158-162`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:202` 與 `:309`。變形:成功訊息寫死「執行成功」不看回傳值,五支(`ofdb3.md` E3.6)。

**正確寫法:`ExecuteNonQuery` 的回傳值就是決定 Commit / Rollback 的那個數字,不要另開變數蓋掉它。**全片唯一寫對的是 `OFDB612` 的 `i += ExecuteNonQuery(…)`(`ofdb3.md §6.8`)。

### 14.4 信在 Commit 之前寄

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:75-76` 呼叫寄信,`:84` 才 `tran.Commit()`(`ofdb3.md` E5.9);寄信方法的回傳值也沒有任何檢查。

**正確寫法見 §6.6:寄信、產檔、呼叫外部 API 一律排在 `Commit` 之後,而且失敗要另外回報,不可蓋掉「DB 已成功」這件事。**

### 14.5 `#region old sql` 不是註解

`OFDB600` 的執行前筆數方法把**舊版**與**新版**兩段完整的 `SELECT … FROM (…) A` 接在同一個字串上:舊版在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:320-359`(外面包的是 `#region old sql` / `#endregion old sql`)、新版在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:361-398`。

**`#region` 不是註解,那 38 行是活的。**送進 Oracle 的是兩個 SELECT 黏在一起,任何 Oracle 都會拒絕。對照組是同一個檔的執行後筆數方法,那邊的舊版是用 `//` 逐行註解掉的(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:443-466`),所以是好的。**壞掉的那支剛好沒有任何呼叫端,所以沒人發現**(`ofdb3.md` E2.2)。

**正確寫法:舊 SQL 要嘛刪掉(版控裡找得回來),要嘛整段 `/* */`。不要用 `#region` 當註解,也不要留在同一個字串串接鏈裡。**

### 14.6 寫死字串決定 `DELETE` 的範圍

`OFDB671` 的 `DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN`,而那個值由寫死字串比對 FunctionID 決定(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:43-49`,`ofdb3.md` E6.2)。FunctionID 一改就洗錯半邊;grid 是空的時候會把那半邊整個清空。同型:`OFDB673` 的查詢**完全沒有 `WHERE`**,整張表全撈(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:66-75`)。另一個變形是**成對邏輯只改一邊**:`OFDB600` 的跨午夜補丁只加在五張表,`OFD620A` / `OFD651A` 兩張沒加,凌晨 0~2 點跑會少算(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:366`、`:371` 對 `:376`,`ofdb3.md` E7.1)。

**正確寫法:`DELETE` / `UPDATE` 的範圍一律由參數決定,而且那個參數要能從畫面或設定表追出來。字面常數只准出現在具名常數的宣告處。**

### 14.7 用 `Environment.UserName == "SYSTEM"` 決定跑不跑

見 §9.2。三支服務都有(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28`,`ofdb3.md` E12.3),`RSPB008` 沒有。

**正確寫法:執行模式用命令列旗標或建置組態決定,不要用執行帳號。**執行帳號是部署決策,綁上去之後資安要求一來就整支不能跑。

### 14.8 SQL 字串串接使用者輸入

`ofdb4.md` E10 列了七處,最嚴重的是 `OFDB703` 的銀行代碼串接——`=` / `<>` 兩處**連引號都沒有**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1406`、`:1411`);`OFDB691` 全部的 `UPDATE` 都走 `sb.AppendFormat` 樣板(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:173`)。`architecture.md §4.3` 已定調:參數化在這套系統裡「做了一半」,另一半就是字串串接。

**正確寫法:值一律 `AddInParameter`,SQL 裡用 `:名稱` 佔位。**表名或欄名真的要動態決定時,先把候選值列成白名單再比對,不要直接串。

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs` | `:33-59` `:43-48` `:52-54` `:69-76` `:83-92` `:99-104` | §3.4 §8 |
| `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs` | `:34-49` `:56-71` `:77-82` | §7 |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs` | `:35-38` `:52-70` `:59-61` | §6.6 §7 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs` | `:20-29` `:32-33` `:36` `:57-155` `:62-119` `:72-78` `:100-101` `:118-119` `:148-153` `:315-322` | §6 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd` · `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/OFDB003View.xsd` | 全檔 | §5.1 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/DataEntity.OFDB.csproj` · `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/UIEntity.OFDB.csproj` | `:102-107` `:233-243` | §10.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj` | `:132` | §10.1 |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/Control.OFDB.csproj` | `:140` | §10.1 |
| `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/FormProxy.OFDB.csproj` | `:104` | §10.1 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj` | `:321-325` `:1225-1226` | §10.1 |
| `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs` | `:137` `:150-154` | §7 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs` | `:51` `:55-62` `:75-76` `:84` `:100` `:268-292` `:320-359` `:361-398` `:366` `:371` `:376` `:443-466` | §3 §6 §14 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs` | `:24-31` `:39-58` `:50-52` `:65-75` `:84-86` `:92` `:103-106` `:109-155` `:149-151` `:239-252` | §3.2 §6.5 §9 §14.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs` | `:13` `:28` `:28-44` | §3.4 §9.2 §14.7 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:175-194` `:189` | §4 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` | `:175-194` `:189` | §4.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config` | `:246-262` | §4.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj` | `:9` `:22` `:74-101` | §9.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.sln` | 全檔 | §9.1 |
| `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd` · `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/OFDB600_9iView.xsd` | 全檔 | §5.2 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs` | `:97` `:158-162` `:206-210` `:259-263` | §14.2 §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs` | `:285-286` `:405-414` | §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs` | `:202` `:309` | §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs` | `:43-49` | §14.6 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs` | `:66-75` | §14.6 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs` | `:173` | §14.8 |
| `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs` | `:89-93` | §8 |
| `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs` | `:284` `:313-319` | §14.2 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs` | `:88-92` | §14.2 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs` | `:1406` `:1411` | §14.8 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs` | `:514-517` | §14.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs` | `:133-138` | §6.5 §14.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs` | `:73` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs` | `:64` `:72-84` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs` · `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs` | `:42` / `:78` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs` | `:86` `:120` `:146` `:183` | §3.4 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **部署機** | §4.4 §9 §10.2 | Remoting 有無的實測、服務安裝與目錄實際內容都未驗證 |
| **PTPFBlock DLL** | §10 §11 | 六層重編與服務建置全未實測;`HintPath` 綁 DLL 的影響只能從 csproj 推 |
| **DB 連線** | §3.2 §6.4 §11 | 排程時刻欄由哪支 M 畫面維護查不到;重跑行為與 SP 內部邏輯無法驗 |
| **SP 腳本(380 支裡 319 支沒有)** | §6.6 §11 | SP 到底動了哪些表只能從呼叫端的前後筆數 SQL 反推(`architecture.md 附錄 B.0`) |
| **統一的批次 log 表** | §6.5 | 目前只能列出三條各走各的管道;若現場其實有一張總表,§6.5 要改寫成單一規則 |
| **選單 / 權限表** | §2.3 §11 | 新批次怎麼掛進選單、怎麼授權,與 `add-screen.md §9` 同一個缺口 |

## 附錄 C 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。以 `OFDB003`(無 Remoting)與 `OFDB600`(有 Remoting + 服務)為兩支範例,素材取自 `modules/ofdb.md` `modules/ofdb3.md` `modules/ofdb4.md` 共 88 支批次 |

由 build_doc.py v2.0.0 於 2026-09-15 17:56 產生 · 標題 55 · 圖 3 · 表格 30 · 程式錨點 128 · § 連結 107 · 引用檢查：畫面 35（缺 0） · Table 3（缺 0） · 結果集 2（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
