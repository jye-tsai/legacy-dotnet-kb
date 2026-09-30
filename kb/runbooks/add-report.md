<!-- 由 tools/build_copilot_kb.py 從 runbooks/add-report.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊 — 加 / 改 Crystal 報表

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。

> 前提知識在 `architecture.md §6`(畫面型別)與 `architecture.md §5`(typed DataSet)。**不要整份讀**。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在既有報表上加 / 改欄位;替既有 R 畫面加一個新報表版型 |
| 範例 | `CASR001`,`Dev/ATLAS.CAS.Report`——七層齊全,而且一支畫面掛六個版型,對照方便 |
| 不適用 | 從零建一支 R 畫面(骨架同 `runbooks/add-screen.md`,再加本手冊的第七層) |
| 前提工具 | Visual Studio 2022 + **Crystal Reports for VS**(版本見 `runbooks/build-env.md §2`,**13.0.4000.0 與 13.0.2000.0 兩版並存**) |
| 變數 | `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock` |

### 0.1 R 畫面是七層不是六層

`architecture.md §6` 講過的命名例外,這裡要用到全部細節。`CASR001` 的七層:

| 層 | 專案 | 檔 |
|---|---|---|
| UI | `ReportUI.CAS` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs` |
| FormProxy | `ReportFormProxy.CAS` | `Dev/ATLAS.CAS.Report/Source/FormProxy/ReportFormProxy.CAS/CASR001_Pxy.cs` |
| Control | `ReportControl.CAS` | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs` |
| PO | `ReportPO.CAS` | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs` |
| DataEntity | `ReportDataEntity.CAS` | `Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` |
| UIEntity | `ReportUIEntity.CAS` | `Dev/ATLAS.CAS.Report/Source/Entity/ReportUIEntity.CAS/CASR001View.xsd` |
| **報表** | **`Report.CAS`** | `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.rpt` |

**六層全部加 `Report` 前綴、住在 `<模組>.Report` 專案資料夾裡。**任何按六層命名寫的工具對 322 支 R 畫面都會失準。

### 0.2 一支畫面可以掛多個版型

`CASR001` 有六個:`CASR001RPS.rpt` · `RPS2` · `RPS3` · `RPS4` · `RPS5` · `RPS6`。

**選哪一個是客戶端決定的**(§3.3)。所以「加一個新版型」不用改伺服端邏輯,只要多一支 `.rpt` 加上客戶端能選到它。

### 0.3 R 畫面沒有四眼

`CASR001_PO` **沒有宣告 `MasterTable` 或 `DetailTable`**(`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen CASR001` 回報主檔明細皆空),也不繼承 EVA 基底。報表是唯讀的,不走 `architecture.md §3` 的四眼流程。

## 1. 資料流總覽

```text
[圖] 報表的兩條路:資料經 SP 的 RefCursor 進結果集 xsd,版型是獨立的 rpt 檔由伺服端傳給客戶端,執行時才合併
圖中文字:① 資料這條路 / Oracle SP / 84% 不在 repo,要先撈 / RefCursor C_RES / AddOutParameter / LoadDataSet / 填進結果集那張表 / Model.xsd 結果集 / 不是實體表,免 ALTER / ② Model → View 逐欄照名複製 / View.xsd / 欄名必須與 Model 一致 / Control 轉換 / 不用改(泛型逐欄) / ⚠ 只加一邊 / 靜默失敗,不報錯 / FormProxy / 不用改 / ③ 版型這條路 —— 與資料完全分開 / .rpt 版型檔 / 一支畫面可掛多個 / 伴生 .cs / AutoGen,不要手改 / PostBuild xcopy / build 時複製,不是部署時 / PTPFBlock CrystalReports / 609 支範本 / ④ 執行時才會合 / 客戶端指定版型類別名 / ReportParameters[0].ReportClass / CRReportTransfer / PTPFBlock,無原始碼 / 回傳 .rpt 位元組 / Crystal 檢視器合併 / 資料 + 版型
```

*圖:圖 1 報表資料流。上兩排=資料,第三排=版型,兩條路各走各的,只在客戶端的檢視器裡合併。橘實框=加欄位要改的四處;灰虛框=不用改;橘虛框=陷阱。*

一句話:**資料走 SP,版型走檔案傳輸,兩條路各走各的。**

## 2. 動工前先分辨:你要改哪一條

| 需求 | 要改 | 節 |
|---|---|---|
| 報表**多印一個欄位** | SP + `Model.xsd` + `View.xsd` + `.rpt` **四處** | §3 §4 §5 |
| 只改**版面**(位置、字體、群組、小計) | 只改 `.rpt` | §5 |
| 加一個**新版型**(同資料不同排版) | 新增 `.rpt` + csproj + 客戶端選項 | §6 |
| 改**查詢條件** | SP + PO 的參數 + UI 的條件控件 | §3.2 §7 |

**最常見的是第一種,而且四處漏一處就會出錯,症狀各不相同(§9)。**

## 3. 資料端:SP 回 RefCursor

### 3.1 現況

`CASR001_PO.GetData` 的全部邏輯(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:46-79`):

```
using (DbCommand cmd = m_db.GetStoredProcCommand("S_TA_CASR001_GET"))
{
    cmd.CommandTimeout = 0; //此程式讓它永久跑  
    m_db.AddInParameter(cmd, "iSDATE",   OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "SDATE"));
    m_db.AddInParameter(cmd, "iEDATE",   OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "EDATE"));
    m_db.AddInParameter(cmd, "iEMP_NO",  OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "EMP_NO"));
    m_db.AddInParameter(cmd, "iRPT_KIND",OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "RPT_KIND"));

    m_db.AddOutParameter(cmd, "C_RES", OracleDbType.RefCursor, int.MaxValue);
    m_db.LoadDataSet(cmd, model.DataEntity, tran, new string[] { model.DataEntity.CASR001.TableName });
}
```

四個慣例,加報表欄位時要照著:

| 慣例 | 說明 |
|---|---|
| 參數前綴 `i` | `iSDATE` / `iEDATE` / `iEMP_NO` / `iRPT_KIND`,都是 `Varchar2` |
| 回傳走 `RefCursor` | 固定名為 `C_RES`,Oracle 的游標回傳法 |
| 值從 model 取 | `SQLEVAHelper.GetParamValue(model, "<條件欄名>")` |
| `LoadDataSet` 指定表名 | 填進 `model.DataEntity.CASR001` 這一張 |

查無資料時寫 `model.Utility.Result.AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:75`),不是丟例外。

### 3.2 改法

**多印一個欄位 = 改 SP 的 `RefCursor` 查詢,把欄位加進 SELECT。**

⚠ **`S_TA_CASR001_GET` 不在 repo 裡。**`DB/SP/` 沒有這支。全庫程式呼叫 380 支 SP,repo 只有 61 支有腳本(`architecture.md 附錄 B.0`)。

所以第一步是**先從資料庫把它撈出來**:

```
SELECT text FROM all_source
 WHERE name = 'S_TA_CASR001_GET' ORDER BY line;
```

撈出來、存成檔案進版控、再改。**不要憑空重寫一支同名 SP**,會覆蓋線上邏輯。完整流程見 `runbooks/change-sp-fn-trigger.md`。

改查詢條件則要三處一起:SP 的參數、PO 的 `AddInParameter`、UI 的條件控件。

### 3.3 ⚠ `CommandTimeout = 0`

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` 註解寫「此程式讓它永久跑」。

**這代表報表查詢沒有逾時保護。**SP 寫壞、條件給太寬,連線會一直掛著不放。加欄位如果讓查詢變重,先自己估一下資料量。

## 4. 結果集:`Model.xsd` 與 `View.xsd`

### 4.1 `CASR001` 是結果集形狀不是實體表

`model.DataEntity.CASR001` 這張表**只存在於 xsd 裡**,資料庫沒有這張表。全庫有 1,635 個這種形狀(`architecture.md §5`)。

判斷方法:

```
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --table CASR001
```

掃描器會標示它不是實體表(`physical` 為否)。

### 4.2 改法

**SP 的 SELECT 多回一欄,xsd 就要多一個 `<xs:element>`,兩邊欄名必須一致。**

加法完全照 `runbooks/add-column.md §3.2`(Model)與 `§4.2`(View),包括:四個 `msprop:Generator_*` 屬性、`msdata:Caption` 給中文名、`minOccurs="0"`、**改完要重生 `Designer.cs`**。

差別只有兩點:

|  | 一般 M 畫面 | 報表 |
|---|---|---|
| 要不要 `ALTER TABLE` | 要(實體欄) | **不用**,結果集不是實體表 |
| 四眼欄位 | 有 15 個 | **沒有**,結果集不帶四眼 |

### 4.3 Model → View 的轉換

`CASR001_Ctl` 的轉換方法同樣走 `TransferVDBHelper` 的泛型逐欄複製,所以**兩邊欄名一致就不用改 Control**——理由與 `runbooks/add-column.md §6.1` 完全相同,包括只加一邊會**靜默失敗**的代價。

## 5. 版型:`.rpt`

### 5.1 `.rpt` 有一支自動產生的伴生 `.cs`

`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:120-125`:

```
<Compile Include="CASR001RPS.cs">
  <AutoGen>True</AutoGen>
  <DesignTime>True</DesignTime>
  <DependentUpon>CASR001RPS.rpt</DependentUpon>
  <SubType>Component</SubType>
</Compile>
```

伴生 `.cs` 是 `CrystalDecisions.CrystalReports.Engine.ReportClass` 的子類(`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.cs:19`),檔頭寫明「這段程式碼是由工具產生的…變更將會遺失」。

**這與 xsd / Designer.cs 是同一種關係:改 `.rpt`,伴生 `.cs` 由 Crystal 設計工具重生,不要手改 `.cs`。**

### 5.2 改法

1. VS 內開 `.rpt`(Crystal 設計檢視)。

2. 報表的資料來源接的是 typed DataSet——**先做完 §4,`.rpt` 的欄位清單裡才看得到新欄位**。

3. 把欄位拉到版面上,設好格式、群組、小計。

4. 存檔,確認伴生 `.cs` 時間戳有更新。

> **〔假設〕缺:Crystal 設計工具。**本機沒裝,`.rpt` 是二進位檔讀不了內容,所以上述步驟未實測。依據是伴生 `.cs` 的 `AutoGen` / `DependentUpon` 設定與 `ReportClass` 繼承關係——這是 Crystal for VS 的標準運作方式。

### 5.3 部署:範本是 build 出來的

`Report.<模組>` 專案帶 PostBuild(25 支都有):

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

所以 **`.rpt` 在 build 時就被複製到 `%PTPF%\CrystalReports\`**,不是部署時才搬。細節見 `runbooks/build-env.md §5.3` 與 `runbooks/deploy.md §7`。

**改了 `.rpt` 一定要編 `Report.<模組>` 專案**,否則新版型不會進到那個目錄。

## 6. 加一個新版型

`CASR001` 掛了六個版型,加第七個:

1. 在 `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/` 新增 `CASR001RPS7.rpt`(照現有那六支的命名)。

2. csproj 加一段,照 `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:120-125` 的樣板,把 `CASR001RPS` 換成 `CASR001RPS7`。

3. 客戶端要能選到它——見 §7。

**不用改 PO、Control、xsd**,因為資料來源沒變。

## 7. 版型是客戶端選的,伺服端只負責傳檔

`CASR001_Ctl.GetReportObject`(`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:59-63`):

```
string rpt = Convert.ToString(ClassData.Util.ReportParameters[0].ReportClass); // 取得前端所傳的報表類別名稱
return CRReportTransfer.TransferFileByte(rpt); // 呼叫報表傳送器傳回報表物件
```

流程:

| 步 | 誰做 | 做什麼 |
|---|---|---|
| 1 | 客戶端 | 把版型類別名放進 `Util.ReportParameters[0].ReportClass` |
| 2 | 客戶端 | `this.FormProxy.GetReportData(...)`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:220`)取資料 |
| 3 | 伺服端 | `GetReportObject` 依名字回傳 `.rpt` 的**檔案位元組** |
| 4 | 客戶端 | Crystal 檢視器把資料與版型組起來顯示 |

所以「加新版型」在客戶端要做的是:讓使用者能選到 `CASR001RPS7` 這個名字,並把它填進 `ReportParameters[0].ReportClass`。

> `CRReportTransfer` 在 PTPFBlock 裡(**無原始碼,從呼叫端反推**),repo 內找不到 `class CRReportTransfer`。它怎麼解析名字到檔案、找不到時回傳什麼,都看不到。

> ⚠ **版型類別名是客戶端傳來、伺服端直接拿去載入的。**這是一個由客戶端控制的字串進到伺服端檔案存取路徑,`architecture.md 附錄 E` 已記錄。加新版型時照現有機制走即可,但**不要**擴大成「讓使用者自由輸入檔名」。

## 8. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 直接在資料庫跑改過的 SP | 回傳的游標**有新欄位**且值正確 |
| 2 | `grep -c "<NEW_COL>" …/CASR001Model.Designer.cs` | 大於 0(驗 xsd 重生了) |
| 3 | 同上,`CASR001View.Designer.cs` | 大於 0 |
| 4 | 編 `Report.CAS` 專案 | 成功,且 `%PTPF%\CrystalReports\` 的 `.rpt` 時間戳有更新 |
| 5 | 開 R 畫面、給條件、預覽 | 新欄位印得出來 |
| 6 | 換一個版型再印一次 | 其他版型不受影響 |
| 7 | 給一組**查無資料**的條件 | 出現「查無資料」而不是空白報表或例外 |
| 8 | 給一組資料量大的條件 | 跑得完(注意 §3.3 沒有逾時保護) |

## 9. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **`.rpt` 設計檢視裡看不到新欄位** | xsd 沒加或沒重生 Designer.cs | §4.2 |
| **報表印出來該欄空白** | SP 沒回這一欄(xsd 有、資料沒有) | §3.2 |
| **資料有、報表沒印** | `.rpt` 版面沒把欄位拉上去 | §5.2 |
| **改了 `.rpt` 但印出來還是舊的** | 沒編 `Report.<模組>` 專案,`%PTPF%\CrystalReports\` 沒更新 | §5.3 |
| **手改了伴生 `.cs`,下次開 `.rpt` 就不見了** | 那支是 `AutoGen`,由設計工具重生 | §5.1 |
| **只加了 Model 沒加 View(或反之)** | `TransferVDBHelper` 逐欄比對,對不上就靜默跳過 | §4.3 |
| **報表跑很久不回來也不逾時** | `CommandTimeout = 0` | §3.3 |
| **找不到 SP 可以改** | 84% 的 SP 不在 repo | §3.2 |
| **新版型選不到** | csproj 沒加,或客戶端沒提供選項 | §6 §7 |
| **按六層去找 R 畫面的檔卻找不到** | R 是七層,而且各層加 `Report` 前綴 | §0.1 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs` | `:46-79` `:60` `:75` | §3 |
| `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs` | `:48-53` `:59-63` | §4.3 §7 |
| `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs` | `:220` | §7 |
| `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj` | `:120-125` | §5.1 §6 |
| `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.cs` | `:1-19` `:19` | §5.1 |
| `Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` | `:1` | §4 |
| `Dev/ATLAS.CAS.Report/Source/Entity/ReportUIEntity.CAS/CASR001View.xsd` | `:1` | §4 |
| `Dev/ATLAS.CAS.Report/Source/FormProxy/ReportFormProxy.CAS/CASR001_Pxy.cs` | `:1` | §0.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **Crystal Reports for VS** | §5 全節 | `.rpt` 是二進位檔,本機讀不了也開不了。裝好後把設計工具的實際操作步驟、欄位清單長相回填 |
| **`S_TA_CASR001_GET` 的原始碼** | §3.2 | 目前只知道它吃 4 個參數回一個 RefCursor;撈出來後可以貼出實際的 SELECT 當範本 |
| **PTPFBlock DLL** | §7 | `CRReportTransfer` 怎麼解析版型名、找不到時的行為都看不到 |
| **選單 / 權限表** | §6 §7 | 新版型要怎麼出現在使用者的選項裡,查不到 |

## 附錄 C 本手冊的驗證程度

| 節 | 依據 | 程度 |
|---|---|---|
| §0.1 七層 · §0.3 無四眼 | 實際檔案結構 + 掃描器 | **已驗證** |
| §3 SP / RefCursor / 參數慣例 | 讀 `CASR001_PO.cs` 原文 | **已驗證** |
| §4 結果集 xsd | 同 `runbooks/add-column.md` 的機制 | **已驗證** |
| §5.1 伴生 `.cs` 由工具產生 | csproj 的 `AutoGen` / `DependentUpon` + 檔頭註解 | **已驗證** |
| §5.2 設計工具操作步驟 | Crystal 標準做法 | **未實測**,缺工具 |
| §5.3 build 時複製範本 | csproj 的 PostBuild 原文 | **已驗證**(但未實跑) |
| §7 版型傳輸 | 讀 `CASR001_Ctl.cs` 原文;`CRReportTransfer` 本身無原始碼 | 呼叫端已驗證,被呼叫端是黑箱 |

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 26 · 圖 1 · 表格 11 · 程式錨點 23 · § 連結 46 · 引用檢查：畫面 1（缺 0） · Report 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
