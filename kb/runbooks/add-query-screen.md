<!-- 由 tools/build_copilot_kb.py 從 runbooks/add-query-screen.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS 維護手冊 — 新增一支 I 查詢畫面

> 產出日期:2026-09-15(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 ⚠ 標「**〔假設〕缺:輸入**」的是拿不到輸入(DB 連線 / PTPFBlock DLL / 選單表)只能推論的部分,附錄 B 彙整;標「**〔客戶特定〕**」的是本站台的值。

> **本手冊是 `runbooks/add-screen.md` 的差異版。**凡是與 M 畫面相同的步驟一律引用,不重抄: 代號規則 `add-screen.md §2`、xsd 三層結構與 10 個 `msprop` `add-screen.md §3`、View 抄 Model `add-screen.md §4`、Control 樣板 `add-screen.md §6`、FormProxy `add-screen.md §7`、UI 控件命名 `add-screen.md §8.3`、選單註冊 `add-screen.md §9`、csproj 與重編 `add-screen.md §10`。前提知識在 `architecture.md §6.3`(I 型的退化)與 `architecture.md §6.7`(I 為什麼沒有四眼)。本篇的實測母體:`Dev/ATLAS.OFD.Query/` 的 **43 支 PO、43 支 Control、58 支 UI 檔**,外加 `modules/cas.md §5` 已寫深的 `CASI001`。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在既有模組裡**從零建一支 I(查詢)畫面**:唯讀、不寫入、不走四眼 |
| 主要範本 | `OFDI716`(`BaseEVADaoPO` + 參數化 SQL + 主明細 + 匯出,本篇最推薦照抄的一支) |
| 對照範本 | `OFDI911`(裸 DAO + SP)· `CASI001`(`modules/cas.md §5` 已寫深,反面教材多) |
| 不適用 | M 維護畫面(`add-screen.md`)· B 批次(`add-query-screen` 之外請看 `runbooks/add-batch.md`)· R 報表(`runbooks/add-report.md`) |
| 前提工具 | Visual Studio · Oracle 客戶端 · PTPFBlock DLL · TFS workspace |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 佈位符 | `<NEW>` = 新代號 · `<MOD>` = 模組 |

### 0.1 一句話版本

**I 不是「M 少幾層」,是同樣六層裡有四層退化。**兩份 xsd 與六個 csproj 一個都不能少。省下來的只有:四眼那組欄位、Control 的 `InitializeVDBTypes()`、PO 的 `xTableMapping` 宣告、UI 的四眼工具列。

## 1. M 與 I 的差異總表(圖)

```text
[圖] M 維護畫面與 I 查詢畫面的層級差異:四處退化、兩件不可省、PO 基底三選一
圖中文字:M 維護畫面 —— 六層滿血,四眼全走 / PO : BaseEVADaoPO / xTableMapping 宣告 / Ctl 兩個必覆寫 / Pool + VDBTypes / Pxy 21 行 / 只有 InitializeControl / UI 四眼工具列 / 送核 覆核 核准 / I 查詢畫面 —— 同樣六層,但四處退化 / PO 多半不繼承基底 / 43 支裡 24 支裸 DAO / Ctl 只覆寫 Pool / 沒有 VDBTypes / Pxy 覆寫 Query / 不覆寫 Add / Update / UI 只有查詢鈕 / 執行鈕關掉 / 不變的兩件事 —— 少做會直接壞掉 / Model.xsd 一定要建 / 沒型別就沒 VDB / View.xsd 一定要建 / 跨 Remoting 的型別 / 六個 csproj 照掛 / xsd 三段不可漏 / 四眼 13 欄免了 / 查詢表多半沒有 / PO 基底三選一 —— 第三個是地雷 / 裸 DAO(24 支) / 自己 new Database / BaseEVADaoPO(15 支) / 用 dbProduct / BasicEVAPO(4 支) / dbTA 恆為 null / 新畫面二選一 / 絕不選第三個
```

*圖:圖 1 M 與 I 的差別。I 不是「少幾層」,是同樣六層裡有四層退化;兩份 xsd 與六個 csproj 一個都不能少。橘色虛框=選到就是死畫面。*

這張表是本手冊的主體,其餘各節是它的展開。

| # | 項目 | M(`add-screen.md`) | I | 差在哪一節 |
|---|---|---|---|---|
| 1 | 專案位置 | `Dev/ATLAS.<MOD>/Source/` | **`Dev/ATLAS.<MOD>.Query/Source/`**,每層資料夾加 `Query` 前綴 | §2 |
| 2 | 代號第四碼 | `M` | `I` | §2 |
| 3 | `Model.xsd` 與 `View.xsd` | 兩份都要建 | **兩份都要建**,但不放四眼那組欄位 | §3 |
| 5 | xsd 的四眼欄位 | 主檔明細各 15 欄 | **不放** | §3.2 |
| 6 | PO 基底 | `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` | 裸 DAO 或 `BaseEVADaoPO`,**二選一** | §4 |
| 7 | PO 介面 | `: IEvaDataAccess` | 裸 DAO 不繼承任何東西;`BaseEVADaoPO` 那條仍要 `: IEvaDataAccess` | §4.2 |
| 8 | `xTableMapping` 宣告 | **必要**,兩參數 + xsd 表名三處同名 | **多半不宣告**(43 支裡只有 2 支有) | §5 |
| 9 | PO 的兩支 `BuildXxxSQLString` | `BeforeSelect` 等三個事件觸發 | **沒有事件**,自己寫一支 `GetQuery` | §5 §6 |
| 10 | SQL 的四眼欄位 | 一定 `AllEVAColumnsForSelect` | **不要**加 | §3.2 |
| 11 | 查詢條件 | 多半字串串接(現存缺陷) | **一律參數化** | §6 |
| 12 | Control `InitializeDataAccessPool` | 要 | **要** | §7 |
| 13 | Control `InitializeVDBTypes` | 要 | **不要**(43 支裡只有 1 支有) | §7 |
| 14 | Control `CustomTransfer*` 四件套 | 四個都寫 | 只寫 Oracle 那兩個,SQL 那兩個 `throw NotImplementedException` | §7 |
| 15 | FormProxy 覆寫 | `InitializeControl()` | **`Query()` 與 `GetMaintainData()`** | §7 |
| 16 | UI 基底 | `xMaintainForm` | **`xOneStepProcessForm`**(42/58)或 `xQueryForm`(8/58) | §8 |
| 17 | 四眼工具列 | 有(送核 / 覆核 / 核准 / 退回) | **沒有**,執行鈕直接 `e.Cancel = true` | §8.1 |
| 18 | 分頁與匯出 | 依畫面 | `TabPages = 2`(條件頁 + 結果頁)· `this.ExportGrid = <某個 grid>` | §8.2 §8.3 |
| 20 | 六個 csproj | 要改 | **要改**(在 `.Query` 專案那六個) | §9 |

## 2. 步驟一:代號與專案

### 2.1 現況:I 畫面住在 `.Query` 專案

`architecture.md §2` 的鐵律:`I` 型住在 `Dev/ATLAS.<MOD>.Query/`,六層資料夾與組件名都加 `Query` 前綴:

```
Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/
Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/
Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/
Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/
Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/
Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/
```

**例外要先 `ls` 確認。**OFD 的查詢畫面散在兩個專案:`Dev/ATLAS.OFD.Query/`(43 支)與 `Dev/ATLAS.OFDI/`(1 支,`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`,而且它的層資料夾**沒有** `Query` 前綴)。`ofd8.md §5` 記過這件事。**新畫面放 `.Query`,不要再往 `ATLAS.OFDI` 加。**

### 2.2 改法與驗證

取號規則與 M 相同(`add-screen.md §2.2`):同模組同型別最大號 +1;`Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/` 底下有 36 份 `.xsd`(`QueryUIEntity.OFD` 同為 36 份),**沒有分卷**,直接放進去。驗證:`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen <NEW>` 回「找不到」才是對的。

## 3. 步驟二:兩份 xsd —— 要建,但不放四眼欄位

### 3.1 現況:xsd 一份都不能省

`architecture.md §6.7` 講的是「I 沒有四眼」,不是「I 不用 entity」。實測 `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` 與 `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI716View.xsd` 兩份都在,而且 `*Model.Designer.cs` / `*ModelVDB.cs` / `.xsc` / `.xss` 五件套俱全。 **沒有 xsd 就沒有 `<NEW>ModelVDB` / `<NEW>ViewVDB` 兩個型別**,UI 的 `this.ProcessVDB = new <NEW>ViewVDB();` 連編都編不過。

骨架、三層結構、10 個 `msprop`、主鍵、csproj 三段全部照 `add-screen.md §3` 與 `add-screen.md §4`,**本節只講差異**。

### 3.2 改法:四眼那組欄位不要放

M 的每張表都帶 15 個四眼欄位,清單在 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:114-133`: `STATUS` + `CREATEID` / `CREATEDATE` / `UPDATEID` / `UPDATEDATE` / `ENTRYID` / `ENTRYDATE` / `VERIFYID` / `VERIFYDATE` / `APPROVEID` / `APPROVEDATE` / `REJECTID` / `REJECTDATE`(這 13 欄是四眼的狀態與人時戳)+ `DATAID` / `DATAFLAG`(資料識別)。

**I 的 xsd 不放這一組。**實測對照:

| xsd | 表數 | `DATAID` | `STATUS` | `DATAFLAG` |
|---|---|---|---|---|
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd`(M) | 2 | 2 個 | 2 個 | 2 個 |
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd`(I) | 3 | **0** | **0** | **0** |

`OFDI716Model.xsd` 三張表裡只有一般的 `CreateID` / `CreateDate` 兩個稽核欄——那是**來源表本來就有的業務欄位**,不是四眼機制。

跟著一起省掉的兩件事:

1. **SQL 裡不要呼叫 `AllEVAColumnsForSelect`**(對照 `add-screen.md §5.4` 第 2 條),查詢表多半根本沒有這些欄,加了就 `ORA-00904`。

2. **不需要 `xs:unique` 的四眼主鍵**(`add-screen.md §3.4`);查詢結果集沒有異動,主鍵只影響 DataSet 的去重行為。

**驗證**:`grep -c "Generator_TableClassName" <NEW>Model.xsd` 要等於你打算回傳幾張 DataTable(`OFDI716Model.xsd` 是 3);`grep -c "DATAID" <NEW>Model.xsd` 要回 0。

## 4. 步驟三:PO 基底選哪一個(實查 43 支)

### 4.1 現況:三種並存,第三種是地雷

剝掉 `//` 註解後掃 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/*_PO.cs` 的 43 支,基底分布:

| 基底 | 支數 | 連線從哪來 | 判定 |
|---|---|---|---|
| **裸 DAO**(只實作 `I<代號>_PO`,沒有基底) | **24** | PO 自己 `new Database("TA", DbServerType.Oracle)` | **可用** |
| **`BaseEVADaoPO`** | **15** | 基底管,PO 內用 `dbProduct` | **可用,而且最推薦** |
| **`BasicEVAPO`** | **4** | **`dbTA` 恆為 null** | **禁用,一定 NRE** |

三支實挑確認(**不是從表格推的,是逐檔看過**):

| 支 | 宣告 | 形狀 |
|---|---|---|
| `OFDI716` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:22` `public class OFDI716_PO : BaseEVADaoPO, IOFDI716_PO` | 一支 `GetQuery<T>`,三段參數化 SQL,用 `dbProduct.LoadDataSet` 直接填三張 DataTable |
| `OFDI911` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:28` `public class OFDI911_PO : IOFDI911_PO` | 裸 DAO,自己 `new Database("TA", …)`(`:30`),呼叫 SP + 11 個 RefCursor 出參 |
| `OFDI719` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:11` `public class OFDI719_PO : BasicEVAPO` | **死畫面**:`:30` 第一行就是 `dbTA.CreateConnection()`,而 `dbTA` 恆為 null;SQL 還是 T-SQL 方言(`CONVERT` / `ISNULL`) |

四支 `BasicEVAPO` 的完整名單:`OFDI058B` `OFDI059` `OFDI375` `OFDI719`。理由與證據鏈見 `add-screen.md §5.7` 與 `architecture.md §3.1.1`。

### 4.2 改法:二選一,怎麼選

| 這支畫面 | 選 | 介面怎麼寫 |
|---|---|---|
| 查詢邏輯是 C# 組 SQL,而且要用 typed DataSet 的表名 | **`BaseEVADaoPO`** | `public interface I<NEW>_PO : IEvaDataAccess { T GetQuery<T>(T model, params object[] args); }` |
| 查詢邏輯整包在 SP 裡,C# 只負責綁參數收 RefCursor | **裸 DAO** | `public interface I<NEW>_PO { DataSet GetXxx(…); }`,不繼承任何東西 |

**兩種都要標 `[PODbType(DbServerType.Oracle)]`**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:21`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:27`),否則 `GetDaoInstance` 找不到。

> ⚠ **判斷基底一定先剝 `//` 註解。**`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:28` 留著一行 `//public class OFDM125A_PO : BasicEVAPO`、第 `:30` 行才是現行的 `BaseEVADaoPO`。直接 `grep "class .*_PO *:"` 會誤判成死畫面。同一條坑在 `add-screen.md §5.7` 有完整說明。

### 4.3 ⚠ `.Query` 專案的 PO 命名有兩種

**這是掃描器踩過的坑(D7),接手時一定要知道。**

| 專案 | PO 檔名 | 實例 |
|---|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` | `<代號>_PO.cs` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs` |
| `Dev/ATLAS.OTA.Query/Source/PO/…` | `<代號>_PO.cs` | 同上形狀 |
| **`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/`** | **`<代號>OracleDao.cs`** | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` |
| **`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/`** | **`<代號>OracleDao.cs`** | `ofdb3.md §3.5` 的 `OFDB615` / `OFDB616` / `OFDB671`–`OFDB673` |

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/` 底下還多分三個子資料夾:`Interface/`(`I<代號>.cs`)、`Oracle/`(現行)、`MSSQL/`(舊世代,多半整檔註解)。

**`atlas_scan --screen` 對兩種命名都認得。**實跑對照:

```
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen OFDI716
  PO          Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen OFDI641
  PO          Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs
```

但兩支的「表」區段都印 `主檔 —` / `明細 —`。**那不是缺層,是 I 型本來就不宣告 `xTableMapping`(§5)。**

**新畫面一律用 `<NEW>_PO.cs`。**`OracleDao` 那套是 EC 的歷史包袱,跟著它只會讓下一個人再踩一次。

**驗證**:用 `add-screen.md §5.7` 那支「剝註解取基底」的一行指令查新 PO,印出來的必須含 `BaseEVADaoPO` 或只有 `I<NEW>_PO`。**看到 `BasicEVAPO` 就停手重寫。**

## 5. 步驟四:沒有 `MasterTable` 宣告,那 `xTableMapping` 那一步變成什麼

### 5.1 現況:43 支裡只有 2 支宣告

`grep -rn "MasterTable" Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` 只命中兩個檔: `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI059_PO.cs:17`(舊型別 `TableMapping`,而且那支是 `BasicEVAPO` 死畫面)與 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39`。 `OFDI199` 也是 43 支 Control 裡**唯一**有 `InitializeVDBTypes()` 的一支——它是 `architecture.md §6.7` 講的「查詢 + 放行」混合畫面,不是純 I。

**純 I 畫面不宣告主明細。**`add-screen.md §5.2` 那三條規則在這裡全部不適用。

### 5.2 改法:那一步被拆成三處具名字串

M 靠 `xTableMapping` 的兩個參數把「實體表名」與「VDB 裡的 DataTable 名」綁起來,I 則是**在三個地方各自寫一次表名**:

| 處 | 寫什麼 | 錨點 |
|---|---|---|
| PO 的 SQL | 實體表名(`FROM TRP805A …`) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:64-95` |
| PO 的 `LoadDataSet` 第三參 | **typed DataSet 的表名,從型別取,不要打字串** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:111`、`:160` |
| Control 的 `CustomTransferOracleModelToView` | 逐表 `TransferVDBHelper.TransferTable(view.UIView.X, model.DataEntity.X, …)` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:73-97` |

第二處是關鍵,`OFDI716` 做對了:

```
dbProduct.LoadDataSet(cmd, model.DataEntity, model.DataEntity.TRP805_D.TableName);
```

**用 `model.DataEntity.<表>.TableName` 而不是字串常值**,表名打錯會在編譯期紅字,不會變成執行期的「查詢永遠零筆」。 `add-screen.md §12` 症狀表裡的「查詢永遠零筆,DB 卻有資料」在 I 型就是靠這個寫法擋掉的。

第三處同理:`TransferVDBHelper.TransferTable(view.UIView.TRP805, model.DataEntity.TRP805, base.TransferEVAColumn)` 兩邊都是強型別成員,Model 與 View 的表名對不上會編不過。

**驗證**:`grep -c "LoadDataSet" <NEW>_PO.cs` 要等於 xsd 的表數,而且每處的第三參都必須是 `model.DataEntity.<表>.TableName`,不可以是字串常值。

## 6. 步驟五:查詢條件怎麼組 —— 參數化,禁字串串接

```text
[圖] I 查詢畫面的查詢流程:UI 驗證與組條件、過 Remoting 的三層、PO 參數化查詢、回到 UI 的換頁與匯出
圖中文字:① 按查詢之前 —— 全部在 UI / DoValidate 起迄 / 起大於迄要擋 / 至少一個條件 / 不擋就全表掃 / Parameters 命名 / 與 PO 端字串一致 / 起空補迄 / Leave 事件 / ② 過 Remoting 到伺服端 —— 三層都是薄的 / Pxy.Query / try / catch 包起來 / Ctl.Select / ExecPOActionToViewVDB / PO.GetQuery / 唯一要自己寫的 / 例外回 Result / 不可吞成空字串 / ③ PO 內部 —— 參數化是唯一正確寫法 / SQL 用 :佔位 / 禁止串使用者輸入 / FindByName 再綁 / null 就不加條件 / LoadDataSet 指定表 / 表名取自 DataEntity / 0 筆也要回 / AddResultRow / ④ 回到 UI —— 換頁、明細、匯出 / Ctl 逐表 Transfer / 沒有 MasterTable / ChangeTabPage / 查詢條件頁鎖住 / 明細在前端過濾 / DataTable.Select / ExportGrid / 匯出指哪張
```

*圖:圖 2 查詢流程。橘色實框=自己要寫對的地方。整條路徑上沒有任何寫入,所以出錯的樣子一律是「查不到」或「查太多」,不會報錯 —— 這就是 I 難查的原因。*

### 6.1 現況:兩種寫法並存,舊的那種是全庫最常見的缺陷型

`architecture.md §4.3` 已定調:參數化在 ATLAS「做了一半」。查詢類尤其嚴重——`CASI001` 的 11 個查詢條件**全部是字串串接**(`modules/cas.md §5.2`),而且串出來的 8 處起迄條件寫成 `> =`(中間有空白),`modules/cas.md §5.3` 判定那是壞的 SQL。

`OFDI716` 是對照組,它是參數化的:

```
WHERE TRP805A.TRANS_DATE >=:TRANS_DATE_ST
  AND TRP805A.TRANS_DATE <=:TRANS_DATE_END
  AND (OFD081V.FUND_ID IN (SELECT * FROM TABLE(F_FormatStringToTable(:FUND_ID))))
```

`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:90-95`,綁定在 `:99-108`。

### 6.2 改法:四條規則

1. **SQL 裡一律用 `:名稱` 佔位,值走 `AddInParameter`。** ``csharp if (model.Utility.Parameters.FindByName("TRANS_DATE_ST") != null) dbProduct.AddInParameter(cmd, "TRANS_DATE_ST", OracleDbType.Varchar2, Convert.ToString(model.Utility.Parameters.FindByName("TRANS_DATE_ST").Value));`` `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:101-104`。

2. **多值條件用 TVF 把字串拆開,不要組 `IN ('a','b','c')`。**`F_FormatStringToTable(:FUND_ID)` 收一個逗號分隔字串,UI 端把勾選的代碼串成 `"A,B,C"` 再送(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:86-93`)。

3. **參數名要跟 UI 的 `AddParametersRow` 字串一模一樣**(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:98-102`)。又一個靠字串對上的跨層綁定,打錯不紅字、條件靜靜不生效。

4. **`FindByName(…) != null` 才綁。**參數不存在就不加該條件——但這也是 `CASI001` 那顆雷的來源(§6.3),所以**「條件不存在」的語意要在 SQL 裡先想清楚**。

### 6.3 ⚠ 條件不存在時會靜默放大查詢範圍

`CASI001` 的權限條件靠 UI 端取員工代號:取不到就不加 `QUERY_EMP_NO` 參數,而 PO 端沒有「參數不存在就擋下」的分支,**結果是唯讀畫面的資料範圍從「自己」放大到「全部」,而且無聲無息**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136` 與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207`,`modules/cas.md §5.3`)。

**規則:凡是「限縮資料範圍」的條件(權限、機構、幣別),參數不存在時一律回零筆或丟例外,不可以當成沒有條件。** 只有「使用者選填的篩選條件」才適用第 4 條的 `!= null` 寫法。

### 6.4 現況:五種會靜默濾掉資料的寫法,都不要抄

`modules/cas.md §5.3` 把 `CASI001` 的六個靜默過濾逐一拆過,其中五種是通用的:

| 寫法 | 後果 | 錨點 |
|---|---|---|
| 硬編的 `WHERE X = '3'`,畫面上沒有對應欄位 | 那一類資料**永遠查不到**,而且沒有提示 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:185-186` |
| 權限白名單寫死員工代號 | 換人要改 code 重編重部署〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| 日期當字串比 | 只要有一筆存成別的格式就落在區間外 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` |
| 代碼說明 join 的分類碼寫死 | 分類碼一改,說明欄整片變空但主檔還在 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 比較運算子中間有空白(`> =`) | **假設**整段 SQL 語法錯,被 catch 吞成「執行失敗,請檢查」 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219` |

最後一條標**假設**:依據是 SQL 標準與 Oracle 詞法規則,**無法在本機驗證**,要連 DB 才能確認。同樣寫法在全庫只出現在四個檔,全部是同一份查詢樣板的後代。

### 6.5 改法:查無資料要回得明確

```
i = model.DataEntity.TRP805_D.Rows.Count;
model.Utility.Result.Clear();
model.Utility.Result.AddResultRow(i != 0, i, "");
```

`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:162-173`(原文是 `if / else` 兩段)。例外時 `AddResultRow(false, 0, ex.Message)`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:175-179`)——**訊息不可是空字串**,理由與批次相同(`add-batch.md §6.5`)。

### 6.6 驗證

| # | 查什麼 | 怎麼查 |
|---|---|---|
| 1 | 有沒有字串串接 | `grep -n "+ \"'\"" <NEW>_PO.cs` 應回 0;SQL 裡的 `:名稱` 個數要等於 `AddInParameter` 的個數 |
| 2 | 條件名有沒有對上 | PO 的 `FindByName("X")` 與 UI 的 `AddParametersRow("X", …)` 逐一比對;再查 `AddResultRow(false` 的第三參有沒有內容 |

## 7. 步驟六:Control 與 FormProxy

### 7.1 Control:比 M 少一個覆寫,多兩個 `NotImplementedException`

`Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs` 全檔 123 行,四件:

| 件 | 錨點 | 與 M 的差別 |
|---|---|---|
| `InitializeDataAccessPool()` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:27-30` | 一樣 |
| **沒有 `InitializeVDBTypes()`** | — | **M 有,I 沒有**。43 支 Control 裡只有 `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI199_Ctl.cs` 有 |
| 業務入口 `Select` / `GetMaintainData` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:51-68` | 各一行 `ExecPOActionToViewVDB` |
| `CustomTransfer*` 四件套 | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:73-105` | **Oracle 兩個逐表 `TransferTable`,SQL 兩個 `throw new NotImplementedException()`** |

`CustomTransferSQLModelToView` / `CustomTransferViewToSQLModel` 直接丟 `NotImplementedException` 是**正確做法**,不是缺陷——這套系統的 I 型只跑 Oracle(`architecture.md §4.6`)。

### 7.2 FormProxy:覆寫的是 `Query`,不是 `InitializeControl`

`Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` 全檔 80 行,兩個覆寫:

```
public override BasicViewVDB Query(BasicViewVDB view)
{
    try { … return m_Ctl.Select(m_vdb); }
    catch (Exception ex)
    {
        CommonExceptionBlocker.HandleFormProxyException(ex);
        BasicViewVDB ExceptionVDB = new BasicViewVDB();
        ExceptionVDB.Util.Result.AddResultRow(false, 0, ExceptionMessage.ServerSideError);
        return ExceptionVDB;
    }
}
```

`Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs:36-52`,另一個是 `GetMaintainData`(`:59-74`)。 **不要覆寫 `Add` / `Update` / `Delete`**——沒有寫入就沒有這三個入口,留著等於給人一條繞過設計的路。

**驗證**:`grep -c "InitializeVDBTypes" <NEW>_Ctl.cs` 應回 0;`grep -c "InitializeDataAccessPool" <NEW>_Ctl.cs` 應回 1。

## 8. 步驟七:UI

### 8.1 現況:基底有兩種,執行鈕要自己關掉

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/` 的 58 個 `.cs`(含彈出子視窗,已排除 Designer)基底分布: `xOneStepProcessForm` **42** · `xQueryForm` 8 · `yPopUpForm` 7(彈出挑選視窗)· `xMaintainForm` 1。

**新畫面用 `xOneStepProcessForm`**,跟 B 批次同一個基底(`architecture.md §6.4` 講的「I 與 B 是同一份樣板」)。它自帶查詢鈕與執行鈕,所以 I 要做兩件事:

```
this.ButtonExecuteEnable = false;                  // FormInitial 就關掉
private void <NEW>_BeforeExecuteButtonClicked(object sender, CancelEventArgs e)
{ e.Cancel = true; return; }                       // 保險再擋一次
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:51` 與 `:197-202`。

`FormInitial` 的四件與 M 相同(`add-screen.md §8.2`),差別是**沒有四眼工具列要掛**: `TabPages` / `ProcessVDB` / `FormProxy` / grid 的 `DataSource`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:35-63`)。

grid 一律設成唯讀:`new GridLayoutManager(new GridLayoutReadOnly())`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:43-46`);要讓使用者勾選的那張才用 `GridLayoutUpdateOnly`(`:41-42`)。欄位白名單同 M:`UltraGridInitialHelper.SetupUltraGridShowColumns`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:147`),另外 I 常多掛一個二次篩選 `UltraGridInitialHelper.SetupUltraGridFilter`(`:61-62`)。

### 8.2 改法:分頁 = 條件頁 + 結果頁

```
this.TabPages = 2;                       // FormInitial
base.ChangeTabPage(1);                   // 查完自動翻到結果頁
this.ButtonSearchEnable = false;         // 查詢後鎖住查詢鈕
this.udatTRANS_DATE_ST.Enabled = false;  // 條件欄位一併鎖住
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:37` 與 `:204-220`,解鎖在 `RefreshPage`(`:222-244`)。

**這是 ATLAS 的「分頁」,不是資料庫分頁。**整份結果一次撈回用戶端,沒有 `ROWNUM` / `OFFSET` 這類分批。主明細的「點一列帶明細」也在前端做——`DataTable.Select(...)` 過濾已經撈回來的明細,不再打伺服器(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:110-122` 與 `:306-317`)。

> ⚠ **所以查詢條件一定要能有效限縮筆數。**沒有「至少填一個條件」的檢核時,使用者按下去就是全表撈回用戶端記憶體。`CASI001` 就少了這條檢核(`modules/cas.md §5.2`)。

### 8.3 改法:匯出只要一行

```
private void ugrdMaster_Enter(object sender, EventArgs e) { this.ExportGrid = ugrdMaster; }
private void ugrdDetail_Enter(object sender, EventArgs e) { this.ExportGrid = ugrdDetail; }
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:296-304`。 `ExportGrid` 是基底 `xOneStepProcessForm` 的屬性(**無原始碼,從呼叫端反推**),匯出鈕匯的就是它指到的那張 grid;**兩張 grid 就掛兩個 `Enter` 事件**,讓游標在哪張就匯哪張。

要自己產 Excel 或特殊格式的才寫程式(`OFDI911` 那型:PO 提供 `GetExcelData` 回一整個 `DataSet`,`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:53-94`),**能用 `ExportGrid` 就不要自己寫**。

### 8.4 改法:UI 端的驗證

`DoValidate` 的形狀與 M 相同(`add-screen.md §8.6`),I 特有的兩條:**每組起迄都要檢查「起 > 迄」**(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:260-288`),並在 `Leave` 事件補「只填起就自動帶迄」(`:246-250`、`:319-323`);**要有「至少填一個條件」的檢核**(§8.2 的警告),`OFDI716` 的版本是「至少勾選一筆基金代碼」(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:75-78`、`:280-284`)。

## 9. 編譯與部署

六個 csproj 全部在 `.Query` 專案底下,加什麼與 M 完全相同(`add-screen.md §10.1`),只是專案名多了 `Query` 前綴: `QueryDataEntity.<MOD>` / `QueryUIEntity.<MOD>` 各 `Compile` × 2 + `None` × 3;`QueryPO` / `QueryControl` / `QueryFormProxy` 各 `Compile` × 1;`QueryUI` `Compile` × 2 + `EmbeddedResource` × 1。

重編順序與部署照 `add-column.md §9.1`、`add-column.md §9.2` 與 `deploy.md §2`——`.Query` 的六個組件在部署對照表裡對應到同樣的欄位(`QueryUI.<MOD>` 佈客戶端、`QueryUIEntity.<MOD>` 兩端都佈、其餘佈伺服端)。

> **〔假設〕缺:PTPFBlock DLL。**整個 §9 未實測(`architecture.md 附錄 C.1`)。csproj 段落形狀來自 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/QueryPO.OFD.csproj` 原文; 部署對照表的 `.Query` 那一列是從 `deploy.md §2` 的 `<MOD>` 通則推的,**`deploy.md §2` 本身沒有單獨列 `.Query`**。

## 10. 驗證清單

| # | 動作 | 過的條件 | 沒過回去做 |
|---|---|---|---|
| 1 | `atlas_scan.py --screen <NEW>` | 六層都有路徑;「主檔 —」是正常的 | §3 §9 |
| 2 | 確認 PO 基底 | 印出來是 `BaseEVADaoPO` 或只有 `I<NEW>_PO` | §4.2 |
| 3 | 依 `add-column.md §9.1` 順序重編六個專案 | 六個都成功 | §9 |
| 4 | 開畫面 | 版面出得來、**執行鈕是灰的** | §8.1 |
| 5 | 什麼條件都不填按查詢 | 被擋住並提示「至少…」 | §8.4 |
| 6 | 只填「迄」不填「起」;起 > 迄 | 兩者都被擋住 | §8.4 |
| 8 | 正常條件查詢 | 有資料;自動翻到結果頁;條件欄位鎖住 | §8.2 |
| 9 | 查無資料的條件 | 回「查無資料」而不是空白訊息 | §6.5 |
| 10 | 點主檔某一列,再把游標留在明細 grid 按匯出 | 明細 grid 跟著換;匯出的是明細不是主檔 | §8.2 §8.3 |
| 11 | 條件輸入含單引號的值 | **不可**出現 SQL 語法錯 | §6.2 |

**第 9、11 最容易失敗**:前者驗例外路徑,後者驗參數化。

## 11. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **開畫面就 `NullReferenceException`** | PO 繼承了 `BasicEVAPO`,`dbTA` 恆為 null | §4.1、`add-screen.md §5.7` |
| **編譯過,執行期找不到 `<NEW>ViewVDB`** | xsd 進了資料夾但 csproj 沒掛 `Generator` | §3.1、`add-screen.md §3.5` |
| **查詢永遠零筆,DB 卻有資料** | `LoadDataSet` 的表名打成字串常值且拼錯 | §5.2 |
| **`ORA-00904`,欄名是 `STATUS` 或 `DATAID`** | SQL 抄了 M 的 `AllEVAColumnsForSelect` | §3.2 |
| **查詢條件填了沒作用** | UI 的 `AddParametersRow` 與 PO 的 `FindByName` 字串不同 | §6.2 第 3 條 |
| **某類資料永遠查不到 / 某人看得到全部人的資料** | SQL 裡有畫面上看不到的硬條件;或限縮條件的參數取不到時被當成「沒有條件」 | §6.3 §6.4 |
| **代碼有值但說明欄空白** | `LEFT JOIN` 的分類碼寫死,值域改了 | §6.4 第 4 列 |
| **輸入含單引號的值就「執行失敗,請檢查」** | 字串串接沒跳脫 | §6.2 |
| **匯出永遠匯主檔;筆數一多畫面就卡住** | 只掛了一個 grid 的 `Enter` 事件;或沒有「至少填一個條件」,全表撈回用戶端 | §8.2 §8.3 |
| **掃描器說缺 PO** | 該專案用 `<代號>OracleDao.cs` 命名 | §4.3 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs` | `:21` `:22` `:64-95` `:90-95` `:99-108` `:101-104` `:111` `:160` `:162-173` `:175-179` | §4 §5 §6 |
| `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs` | `:27-30` `:51-68` `:73-97` `:73-105` | §5.2 §7.1 |
| `Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` | `:36-52` `:59-74` | §7.2 |
| `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs` | `:35-63` `:37` `:41-46` `:51` `:61-62` `:75-78` `:86-93` `:98-102` `:110-122` `:147` `:197-202` `:204-220` `:222-244` `:246-250` `:260-288` `:280-284` `:296-304` `:306-317` `:319-323` | §6 §8 |
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` · `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI716View.xsd` | 全檔 | §3 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/QueryPO.OFD.csproj` | 全檔 | §9 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs` | `:27` `:28` `:30` `:53-94` | §4.1 §8.3 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs` | `:11` `:30` | §4.1 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI059_PO.cs` · `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs` · `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI199_Ctl.cs` | `:17` / `:39` / 全檔 | §5.1 §7.1 |
| `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` · `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` | 全檔 | §2.1 §4.3 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs` | `:28` `:30` | §4.2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs` | `:152-183` `:185-186` `:206-207` `:219` `:329` `:345` | §6.1 §6.3 §6.4 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs` · `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd` | `:135-136` / 全檔 | §3.2 §6.3 |
| `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs` | `:114-133` | §3.2 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **DB 連線** | §6.4 §10 | `> =` 那條只能標假設;查詢結果的正確性、日期字串比較的實際資料格式都無法驗 |
| **PTPFBlock DLL** | §9 §10 | 六層重編全未實測 |
| **選單 / 權限表** | §2 §10 | 新查詢畫面怎麼掛進選單、怎麼授權,與 `add-screen.md §9` 同一個缺口;`CASI001` 那種「權限寫死在 SQL」的替代做法也要等這個輸入 |
| **`deploy.md` 的 `.Query` 專用列** | §9 | 目前是從 `<MOD>` 通則推的,補上之後 §9 改成直接引用 |

## 附錄 C 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。以 `add-screen.md` 為底做差異版;PO 基底分布實測 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` 全部 43 支,深讀 `OFDI716` / `OFDI911` / `OFDI719` 三支 |

由 build_doc.py v2.0.0 於 2026-09-15 17:56 產生 · 標題 38 · 圖 2 · 表格 16 · 程式錨點 68 · § 連結 80 · 引用檢查：畫面 12（缺 0） · 結果集 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
