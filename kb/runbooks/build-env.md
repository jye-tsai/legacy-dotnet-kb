<!-- 由 tools/build_copilot_kb.py 從 runbooks/build-env.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊 — 建置環境

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。 ⚠ 標「**〔客戶特定〕**」的是本站台的值。

> **本手冊未實測。**本機沒有 PTPFBlock DLL 所以整個方案編不起來(`architecture.md 附錄 C.1`), 以下全部從 `.sln` / `.csproj` / `App.config` 的設定反推。拿到 DLL 後照著跑一次,把實際輸出回填。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 新人拿到 ATLAS 原始碼,要把它變成「編得起來、跑得動」的開發機 |
| 不適用 | 部署到測試 / 正式環境(見 `runbooks/deploy.md`)· 建置伺服器 / CI(repo 內沒有任何 CI 設定檔) |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock` |
| 主方案 | `Dev/Vendor.ATLAS.sln`,**299 個 `.csproj`**(方案內掛 252 個) |

### 0.1 先看這張:能不能編起來取決於三件事

| # | 前提 | 沒有的後果 | 怎麼確認 |
|---|---|---|---|
| 1 | **PTPFBlock DLL 在 `%PTPF%`** | 1,347 筆參考全部解析失敗,**整個方案編不起來** | `dir "%PTPF%\Vendor.Product.*.dll"` |
| 2 | **對 `C:\Program Files` 有寫入權** | 275 / 299 個專案的輸出目錄就在那裡(§5.1),沒權限 build 直接失敗 | 用系統管理員身分開 VS |
| 3 | **Devart dotConnect for Oracle** | 編得起來,但 **xsd 設計工具打不開**、Designer.cs 重生不了(`runbooks/add-column.md §3.3`) | VS 的伺服器總管有沒有 dotConnect 資料來源 |

**這三件缺任何一件,後面都不用做。**第 1 件目前就缺,見 §3。

## 1. 環境總覽

```text
[圖] 建置環境:三個前提、原始碼組成、六層建置順序、產出落點;Debug 與 Release 組態落點不同
圖中文字:① 三個前提,缺一不可 / Visual Studio 2022 / 17.5 · 要系統管理員身分 / PTPFBlock 118 支 DLL / 目前缺,本機編不起來 / Devart dotConnect / 10.1 · 開 xsd 設計檢視 / TFS workspace / 位址待確認 / ② 原始碼 299 個 csproj / Dev/Common / 共用層 23 專案 / Dev/ATLAS.* / 34 個業務模組資料夾 / Dev/Exceptions / 例外政策鏈 / DB/ / 277 支腳本 · 混編碼 / ③ 建置(六層由下往上) / DataEntity · UIEntity / xsd 先重生 Designer.cs / PO → Control → FormProxy / UI / Report.<模組> ×25 / PostBuild 複製 .rpt / ④ 產出落點 —— 最容易踩到的地方 / Debug|AnyCPU → PTPFBlock / 275/299 專案 · 與框架混放 / Release|AnyCPU → bin\Release / 落點不同,改動不生效 / PTPFBlock\CrystalReports / 609 支 .rpt
```

*圖:圖 1 建置環境。灰虛框=目前缺的前提;橘虛框=產出直接寫進框架安裝目錄,且 Debug 與 Release 落點不同——選錯組態會出現「改了不生效」。*

## 2. 版本清單

全部從 repo 的設定檔抽出來,不是問來的:

| 項目 | 版本 | 出處 |
|---|---|---|
| **Visual Studio** | **2022**(`17.5.33530.505`) | `Dev/Vendor.ATLAS.sln:3-4` |
| 方案檔格式 | `Format Version 12.00` | `Dev/Vendor.ATLAS.sln:2` |
| .NET Framework | **v4.8**(268 支)· v4.5(5 支)· v2.0(1 支) | 全庫 `<TargetFrameworkVersion>` |
| Oracle(執行期) | `Oracle.ManagedDataAccess` **4.122.21.1** | 全庫 csproj 參考 |
| Oracle(設計期) | `Devart.Data.Oracle` **10.1.134.0** | 同上,見 `architecture.md §8.2` |
| Oracle(遺留) | `System.Data.OracleClient` | 4 支 csproj,微軟已標為過時 |
| UI 控件 | **Infragistics WinForms v19.1** | `%PTPF%\Infragistics4.*.v19.1.dll`,11 支 |
| 報表 | **Crystal Reports 13.0.4000.0**(121 筆)+ **13.0.2000.0**(16 筆) | 全庫 `CrystalDecisions*` 參考 |
| 企業程式庫 | Microsoft Enterprise Library **5.1.0.0** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:3-6` |
| 框架 | Vendor Fusion **1.12.20.85** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:10` |
| 版控 | **TFS**(不是 git),`.vspscc` 綁定 | `architecture.md §0` |

> **Crystal 有兩個版本並存**(13.0.4000.0 與 13.0.2000.0)。安裝時裝新的那個(13.0.4000.0),舊版參考的 16 筆多半靠組件繫結解析。若某支報表專案編不過,先看它參考的是哪一版。

> 計劃書原本從 `.v12.suo` 推測是 VS2013。**那是舊殘留**;方案檔本身寫的是 VS2022,以方案檔為準。

## 3. PTPFBlock:目前最大的缺口

### 3.1 現況

`%PTPF%` 底下應該要有 **118 個相異 DLL**,全庫對它們有 **1,347 筆 `<HintPath>` 參考**(`architecture.md 附錄 C.1`)。其中 65 支是 Vendor 自家的、53 支是第三方(Infragistics、Enterprise Library、Crystal、NPOI、FileHelpers…)。

**本機沒有這個目錄,所以本機編不起來。這不是設定問題,是缺件。**

清單在 `architecture.md 附錄 C.3`(自家前 20 支)與 `附錄 C.4`(第三方擇要)。

### 3.2 取得方式

> **〔假設〕缺:PTPFBlock DLL。**repo 內沒有這些 DLL、沒有安裝程式、沒有還原腳本,也沒有任何文件說它從哪來。三條可能的路,依可行性排:

> 1. **從既有開發機或伺服器整包複製 `C:\Program Files\Vendor\PTPFBlock\`。**最快,而且能確保版本與現行程式一致。

> 2. 向 Vendor 原廠索取對應版本的安裝包。

> 3. 從部署機的 GAC / 應用程式目錄逐支撿——**不建議**,容易撿到版本不一致的組合。

> 依據:所有 `<HintPath>` 都指向一個固定的絕對路徑,代表這是「裝在機器上」而非「隨 repo 帶走」的相依。**待胖虎確認哪台機器有。**

### 3.3 拿到之後先驗這件事

`architecture.md 附錄 C.6` 列了 HintPath 本身的四個問題,其中兩個會讓你就算裝了 DLL 還是編不過:

| 問題 | 影響範圍 | 處理 |
|---|---|---|
| **7 支 csproj 把 `Program Files` 打成 `Program`** | `ATLAS.OTA` / `ATLAS.OTAB` 的 Control/FormProxy/PO,加 `ATLAS.CLS.Report` 的 UI | 該筆參考必定解析失敗,要改 csproj 或建一個 `C:\Program\Vendor\PTPFBlock` 的目錄連結 |
| **同一支 csproj 內相對路徑層數自相矛盾** | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:82` 用 7 層 `..`、`:88` 用 10 層 `..`,指向同一個目錄 | **不論 repo 放在哪個路徑都不可能同時成立**;把相對改成絕對是最省事的解 |

**這兩件事沒解決,`OTA` / `OTAB` / `CLS.Report` / `TA.DataAccess` 這幾個專案編不過。**

## 4. TFS 取檔

repo 內每個專案旁都有 `.vspscc`,代表綁定 TFS 來源控制。

> **〔假設〕缺:TFS 位址與 workspace 設定。**`.vspscc` 只記錄綁定關係,不含伺服器位址;`.vssscc` 與 workspace 對應表不在 repo 內。**待胖虎提供** TFS 集合 URL 與應該對應到哪個 workspace。

> 在那之前可以照現況(檔案系統上的一份複本)開發,但**不能簽入**,而且拿不到別人的變更。

## 5. 建置

### 5.1 ⚠ 建置產出直接寫進框架安裝目錄

**這是本手冊最需要先知道的一件事。**

`299` 個 `.csproj` 裡有 **275** 支的 `<OutputPath>` 直接指向 `C:\Program Files\Vendor\PTPFBlock\`。以 `PO.CAS` 為例:

| 組態 | `OutputPath` | 錨點 |
|---|---|---|
| `Debug\|AnyCPU` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:25` |
| `Release\|AnyCPU` | `bin\Release\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:33` |
| `Debug\|x86` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:40` |
| `Release\|x86` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:49` |

三件後果,每一件都會咬人:

1. **要用系統管理員身分開 VS。**寫入 `C:\Program Files` 需要提權,否則 build 會在寫檔那一步失敗。

2. **業務 DLL 與框架 DLL 混在同一個目錄。**你分不出哪些是原廠的、哪些是自己編出來的。要重建乾淨環境時特別麻煩。

3. **這正是 `architecture.md 附錄 C.5` 那個陷阱在原開發機上看不出來的原因。**那 25 個「repo 有原始碼卻被綁成預編 DLL」的組件,因為 build 產出就落在 `%PTPF%`,所以在原機器上「改了會生效」;**換一台機器、或改用 `Release|AnyCPU` 組態,同樣的改動就不生效了**。

**同一支專案四個組態落點不一致**(`Release|AnyCPU` 是唯一輸出到 `bin\Release\` 的),所以**你選哪個組態 build,決定 DLL 落在哪裡**。要與原機器行為一致就用 `Debug|AnyCPU`。

### 5.2 建置順序

方案內相依由 `ProjectReference` 決定,VS 會自己排。手動編單一模組時照六層順序(`architecture.md §2`):

```
DataEntity.<MOD>、UIEntity.<MOD>  →  PO.<MOD>  →  Control.<MOD>  →  FormProxy.<MOD>  →  UI.<MOD>
```

**改過 `.xsd` 的話,編之前要先重生 `Designer.cs`**(`runbooks/add-column.md §3.3`),否則編出來的是舊 schema。

### 5.3 報表專案會在 build 時複製 `.rpt`

25 支 `Report.<模組>` 專案帶了 PostBuild:

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

`Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj`

所以 **609 支報表範本是「build 出來的」不是「部署過去的」**,落點 `%PTPF%\CrystalReports\`。同樣需要 `C:\Program Files` 的寫入權。

另有 1 支 `ATLAS.BO/Source/BO.BMS/BO.BMS.csproj` 複製到 `C:\Program Files\Vendor\TABlock\`——**另一個目錄**,而且該專案只有 1 支 cs 檔(`architecture.md 附錄 E24`)。

## 6. 資料庫端的開發環境

| 用途 | 需要什麼 | 出處 |
|---|---|---|
| **執行期**連 Oracle | ODP.NET Managed 4.122.21.1(隨 `%PTPF%` 帶) | `architecture.md §8.2` |
| **設計期**開 xsd | **Devart dotConnect for Oracle 10.1.134.0** + 連得到設計庫 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` |
| 設計庫位址 | `Server=ora01.vendor.com.tw;Sid=ATLASDB`〔客戶特定〕 | 同上 |

**設計庫是 Vendor 的開發庫,不是客戶正式庫。**沒有它就不能用 VS 的 xsd 設計工具重生 typed DataSet——這是加欄位、加畫面兩本手冊的必要條件。

> 設定檔裡另有多組 `System.Data.SqlClient` 的連線字串(`Dev/Common/Source/Base/TA.DataEntity/app.config:6` 等 15 筆),那是另一個客戶(AGI)產品線的設計期殘留,**不要照著設**,見 `architecture.md §8.2.1`。

> 這些設定檔含明文密碼(`architecture.md 附錄 E3`)。本文不重製密碼值。

## 7. 驗證清單

照順序做,每一步過了才做下一步:

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | `dir "%PTPF%\*.dll"` | 檔案數接近 118 |
| 2 | 用系統管理員身分開 `Dev/Vendor.ATLAS.sln` | 方案載入無「專案無法載入」 |
| 3 | 單編 `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj` | 成功。**這支是共用最底層,它過了才有意義往上編** |
| 4 | 單編 `PO.CAS` → `Control.CAS` → `FormProxy.CAS` → `UI.CAS` | 依序成功 |
| 5 | 在 VS 開 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | 設計檢視打得開(驗 Devart 裝好了) |
| 6 | 對該 xsd 執行自訂工具 | `CASM001Model.Designer.cs` 時間戳有更新 |
| 7 | 全方案 Rebuild(`Debug\|AnyCPU`) | 0 errors |
| 8 | 編 `ATLAS.OTA` 與 `ATLAS.CLS.Report` | 若失敗,回去做 §3.3 的 HintPath 修正 |

## 8. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **幾百個「找不到型別或命名空間」** | `%PTPF%` 不存在或不完整 | §3.1 §3.2 |
| **「無法寫入檔案 … 存取被拒」** | 沒有 `C:\Program Files` 寫入權 | §5.1——用系統管理員開 VS |
| **只有 `OTA` / `OTAB` / `CLS.Report` 編不過** | 那 7 支 csproj 的 `\Program\` 路徑打錯 | §3.3 |
| **`TA.DataAccess` 編不過,別的都好** | 同一支 csproj 內 7 層 / 10 層 `..` 相對路徑矛盾 | §3.3 |
| **xsd 用設計檢視打不開,只跳 XML 原始碼** | 沒裝 Devart dotConnect | §6 |
| **改了 xsd 但編出來還是舊欄位** | 沒重生 `Designer.cs` | `runbooks/add-column.md §3.3` |
| **改了共用層、重編了,執行起來還是舊行為** | 用了 `Release\|AnyCPU`,DLL 落在 `bin\Release\` 沒進 `%PTPF%` | §5.1 |
| **報表範本沒更新** | 沒編 `Report.<模組>` 專案(範本靠 PostBuild 複製) | §5.3 |
| **簽入時說沒有繫結 / 找不到 workspace** | TFS 綁定資訊不全 | §4 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/Vendor.ATLAS.sln` | `:2` `:3-4` | §2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj` | `:25` `:33` `:40` `:49` | §5.1 |
| `Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj` | `:1` | §5.3 |
| `Dev/ATLAS.BO/Source/BO.BMS/BO.BMS.csproj` | `:1` | §5.3 |
| `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj` | `:82` `:88` | §3.3 §7 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:3-6` `:10` | §2 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config` | `:8` | §6 |
| `Dev/Common/Source/Base/TA.DataEntity/app.config` | `:6` | §6 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | `:1` | §7 |
| `Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj` | `:1` | §3.3 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **PTPFBlock DLL(或哪台機器有)** | §0.1 §3 §5 §7 全部 | 整本手冊都是推論。拿到後跑一次 §7 的八步,把實際輸出、錯誤訊息、耗時貼進來 |
| **TFS 集合 URL 與 workspace 對應** | §4 | 寫出實際的取檔步驟 |
| **設計庫帳密** | §6 §7 第 5–6 步 | 驗證 xsd 設計工具真的打得開 |
| **原開發機的 VS 擴充清單** | §2 | 目前只知道 VS2022 + Devart;Crystal 的 VS 整合套件版本、Infragistics 的設計期授權都還沒確認 |

## 附錄 C 本手冊未實測

`runbooks/add-column.md 附錄 C` 有一份「計劃書假設 vs 實際」對照。本手冊沒有那種對照表,因為**沒有任何一步實際跑過**——缺 PTPFBlock,連第一步都做不了。

所以本手冊的定位是:**拿到 DLL 那天的檢查清單**,不是已驗證的操作紀錄。照著跑第一次的人,請把每一步的實際結果回填,並把版本升成 v2。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 20 · 圖 1 · 表格 10 · 程式錨點 26 · § 連結 32 · 引用檢查：

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
