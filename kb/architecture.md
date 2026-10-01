<!-- 由 tools/build_copilot_kb.py 從 architecture.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS(Vendor.Product.TA)架構總覽

> 本投信基金事務 / 過戶代理系統。本篇是所有維護手冊(`docs/runbooks/`)與模組知識庫 (`docs/modules/`)的共同前提。**不要整份讀**,用目錄跳到你要的那一節。

> 內容為 2026-09-14 的讀碼快照。**與現行程式不符一律以程式為準**,並回報差異。標「假設」「推測」的地方代表 repo 內找不到權威來源,待回填的輸入見附錄 F。

## 0. 系統邊界與角色

### 0.1 這套系統管什麼

ATLAS(`Vendor.Product.TA`)是本投信的**基金事務 / 過戶代理(Transfer Agency)系統**。它管的是投資人與基金之間每一筆事務的生命週期:開戶、申購、買回、轉換、定期定額、收益分配、對帳單與各式法定報表。

系統自報的名稱與版本可以在設定檔看到:`基金事務系統(VENDOR) (v 1.7.0.1)`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:264`)。

規模一句話帶過:**911 支畫面、437 張實體表、608 支報表範本、252 個專案**。

### 0.2 這篇文件的定位與讀法

這是所有維護手冊(`docs/runbooks/`)與模組知識庫(`docs/modules/`)的**共同前提**。它不教你怎麼改一個欄位——那是 `runbooks/add-column.md` 的事;它讓你知道改欄位的時候,你正在動的是什麼東西。

讀完你應該能回答四件事:

| 問題 | 去哪一章 |
|---|---|
| 拿到一支畫面代號,六層檔在哪、各層做什麼 | §2、§6、§9.2 |
| 一筆資料從新增到核准經過哪些方法、寫了哪些欄位 | §3 |
| schema 真相在哪、欄位中文名怎麼查 | §5、附錄 A |
| 哪些東西是黑箱、邊界在哪 | 附錄 C、§8.1 |

**不要整份讀。**大部分情況你要的是其中一節,用左側目錄跳。

### 0.3 三個貫穿全篇的詞

這三個詞後面不再解釋:

| 詞 | 意思 |
|---|---|
| **六層** | UI → FormProxy → Control → PO → DataEntity / UIEntity。一支畫面的六個檔,§2 |
| **四眼(EVA)** | 經辦送出、另一人覆核、主管核准的三段式流程。引擎共用,§3 |
| **畫面型別** | 代號中間那一碼:`B` 批次 / `I` 查詢 / `M` 維護 / `R` 報表,§6 |

### 0.4 角色與職責分離

四眼流程對應四種人。**同一筆資料的經辦與覆核不能是同一個人**——這是整套 EVA 引擎存在的理由。

| 角色 | 做什麼 | 在資料上留下 |
|---|---|---|
| 經辦(Entry) | 新增 / 修改 / 刪除的送出 | `CREATEID` · `ENTRYID` 及其 `*DATE` |
| 覆核(Verify) | 檢查經辦送出的內容 | `VERIFYID` · `VERIFYDATE` |
| 主管(Approve) | 核准生效,或退回 | `APPROVEID` / `REJECTID` 及其 `*DATE` |
| 批次 / 排程 | 無人值守的日結、扣款、檔案交換 | 依各批次而定 |

`STATUS` 欄記錄目前停在哪一段。欄位語意與狀態轉換的完整規則見 §3;哪些表帶這組欄位見附錄 A。

> **145 / 180 張「有 xsd 欄位定義」的實體表帶四眼欄位(81%,附錄 A)。** 也就是說四眼幾乎是業務表的標準配備,不是少數特例。但另外 257 張表沒有 xsd 欄位定義,**無從判斷**——所以「這張表有沒有四眼」要個別查,不能一概而論。

> **全系統已知缺陷規模(29 篇模組文件附錄 E 彙整,`defects.md` 可查):****1,682 條,高 435 · 中 624 · 低 267 · 未分級 356**。高風險六成集中在 `OFD` 家族(260 / 435),其中批次軌四篇就佔 106 條。兩條死碼線——`BasicEVAPO` / `MultiRowEVAPO` 的 `dbTA`(76 支)與報表派 `Basic_PO` 的 `m_db`(76 支)——聯集 **151 支畫面(17%)一按就 NRE**,是所有缺陷裡最系統性的一組(§3.1.1、附錄 D.3)。「未分級」是來源文件沒標嚴重度(`bbs` `tmk` `ofdi2` 三篇整篇無分級),不是「不嚴重」;嚴重度口徑各篇自訂,`defects.md` 照抄不重評。

### 0.5 主從邊界(先講結論)

.NET Remoting 的邊界在 **UI 與 FormProxy 之間**。客戶端 `new XXX_Pxy()` 拿到的是透明代理,真正的物件跑在伺服端 IIS 上。

實務結論就一句:**改 UI 佈客戶端,改其餘五層佈伺服端,`UIEntity` 兩邊都要。**

證據、通道設定與完整部署拓撲見 §8.1。這件事放在第 0 章講,是因為它決定了後面每一章的閱讀角度——你看到的每一層,都要先問「這層跑在哪台」。

### 0.6 這篇文件不涵蓋什麼

誠實列出來,免得你在裡面找不到又浪費時間:

| 缺什麼 | 為什麼 | 補上需要 |
|---|---|---|
| 911 支畫面的**中文名稱** | 選單 / 權限表不在 repo | 選單表匯出 |
| 模組代碼的**權威業務對照** | 同上,§9.3 全欄是推測 | 模組對照表 |
| 257 / 437 張表的**欄位定義** | 沒有 DDL,xsd 也沒涵蓋 | 唯讀資料庫帳號,或 `ALL_TAB_COLUMNS` 匯出 |
| `Basic_Pxy` 等基底類別的**實作** | PTPFBlock 是編譯好的 DLL | 原廠原始碼(可能拿不到) |
| 主程式的 **Remoting 設定** | 部署產物,不在版控 | 部署機上的 `main.exe.config` |
| **正式環境**的連線與端點 | repo 內只有開發 / UAT 值 | 部署機設定檔 |

---

## 1. 全景與各式流程圖

本篇的圖散在各章,放在它們被討論的地方。這一章給全景圖,並列出其餘各圖的位置,方便直接跳過去。

### 1.1 全景

```text
[圖] 全景圖:UI 與 WindowsService 透過 Remoting 打到伺服端的 FormProxy,再往下經 Control / PO / 四眼引擎到 Oracle
圖中文字:客戶端(桌機 · Citrix) / 畫面 UI / UI.<MOD>/<代號>.cs / 共用控件 / UI.CustomControl · 19.1 / Crystal 檢視器 / .rpt 範本 609 支 / WindowsService 四支 / 也是 Remoting 呼叫端 / Remoting 邊界 / FormProxy 透明代理 / http channel · binary / UIEntity(View) / 邊界上傳的型別,兩端都要 / 伺服端(IIS · ATLAS_TAService) / FormProxy 實體 / FormProxy.<MOD>/*_Pxy.cs / Control / Control.<MOD>/*_Ctl.cs / PO / PO.<MOD>/*_PO.cs / 四眼引擎 TA.DataAccess / 11,944 行 · 908 支共用 / Framework DLL / PTPFBlock · 無原始碼 / 資料與外部 / Billhunter / EC / SOAP〔客戶特定〕 / LDAP · SMTP · 官網 API / TA.ServerUtility / Oracle / ODP.NET 執行期
```

*圖:圖 1 全景。Remoting 邊界在 UI 與 FormProxy 之間——客戶端 new 出來的 _Pxy 是透明代理,實體活在伺服端;WindowsService 走同一條路,不直連資料庫。橘色虛線框為客戶特定,灰框為 PTPFBlock 黑箱。*

三件事先看懂,後面各章才好讀:

1. **豎的那條是六層。**由上而下 UI → FormProxy → Control → PO → DataEntity / UIEntity,細節見 §2。

2. **中間那道是 Remoting 邊界。**它在 UI 與 FormProxy 之間,不在更下面——這決定了改哪一層要部署到哪一台,見 §8.1。

3. **四眼引擎是共用的。**`TA.DataAccess` 一份,911 支畫面全吃它,見 §3。

灰框(`PTPFBlock`)是沒有原始碼的黑箱,清單見附錄 C;橘色虛線框是逐站可能不同的〔客戶特定〕項目。

### 1.2 圖索引

| 圖 | 內容 | 在哪 |
|---|---|---|
| 圖 1 | 全景:客戶端 / Remoting / 伺服端 / Oracle / 外部系統 | 本節 §1.1 |
| 圖 2 | 六層檔案對應、重編順序、繼承自 DLL 的基底 | §2 |
| 圖 3 | 四眼狀態機:Entry → Verify → Approve 及各轉換寫的欄位 | §3 |
| 圖 4 | typed DataSet:xsd → `MSDataSetGenerator` → Designer.cs → 實體表 | §5 |
| 圖 5 | 共用層的多套平行實作 | §7 |
| 圖 6 | 部署拓撲:改哪一層佈哪一台 | §8 |
| 圖 7 | 模組地圖:19 個畫面代號前綴 | §9 |

### 1.3 一支 M 畫面的一日

**(本階段未展開)**——完整的「開畫面 → 查詢 → 修改 → 送出 → 覆核 → 核准」時序需要跨 §3 與 §6 兩章的內容,而且要驗證它在 `CASM001` 以外也成立。目前的替代讀法:先讀 §6 的 M 型別段落知道六層各做什麼,再讀 §3 的 `EVA()` 主流程知道送出之後發生什麼。等階段 4 逐模組驗證過通則,再回頭補這張時序圖。

### 1.4 重編與部署相依

併入 §2(重編順序,圖 2 右半)與 §8(部署拓撲,圖 6),不另立一節,避免同一件事講兩次。

### 1.5 專案相依圖

以 CAS 六個 `.csproj` 的 `ProjectReference` 實證,見 §2。全系統 252 個專案的完整相依圖沒有畫——**在本機無法建置的前提下(缺 PTPFBlock,見附錄 C.1),畫出來的圖無法驗證**,寧可不畫。

### 1.6 資料流(View ↔ Model ↔ 表)

見 §5(圖 4)。`CASM001_Ctl` 的 `CustomTransferOracleModelToView` / `ViewToOracleModel` 兩對方法是這條資料流的實作,細節在 §5。

## 2. 命名與六層鐵律

```text
[圖] 六層檔案對應、由下往上的重編順序,以及來自 PTPFBlock 的基底類別
圖中文字:六層(以 CAS 模組為例) / UI.CAS / CASM001.cs / FormProxy.CAS / CASM001_Pxy.cs / Control.CAS / CASM001_Ctl.cs / PO.CAS / CASM001_PO.cs / DataEntity.CAS / CASM001Model.xsd / UIEntity.CAS / CASM001View.xsd / 重編順序(由下往上) / 1. DataEntity · UIEntity / xsd 先重生 Designer.cs / 2. PO / 3. Control / 4. FormProxy / 伺服端佈版止於此 / 5. UI / 客戶端佈版 / 基底(黑箱) / Basic_Pxy / PTPFBlock / BasicModelVDB / PTPFBlock / BasicViewVDB / PTPFBlock / TA_PO 等四層 / TA.DataAccess(有原始碼)
```

*圖:圖 2 六層與重編順序。左:一支畫面的六個檔;中:改任一層要往上重編到哪裡;右:繼承自框架 DLL 的基底,無原始碼。*

### 2.1 畫面代號:三段結構,全庫 911 個

ATLAS 的一切都掛在「畫面代號」上。代號長度固定 7 碼,拆三段:

| 段 | 位置 | 內容 | 例 |
|---|---|---|---|
| 模組碼 | 前 3 碼 | `CAS` / `OFD` / `IPJ` / `CLS` … | `CAS` |
| 型別碼 | 第 4 碼 | `M` 維護 / `I` 查詢 / `B` 批次 / `R` 報表 | `M` |
| 流水號 | 後 3 碼 | 模組內自編 | `001` |

掃描器實測全庫 **911 個不重複代號**,型別分布 `R` 324 / `M` 285 / `B` 215 / `I` 87。代號一旦決定,六層的**檔名、類別名、namespace、xsd 根節點名**全部由它推導,沒有設計空間—— 這就是「鐵律」的來源:不需要查任何 registry,看到 `CASM001` 就知道六個檔在哪。

### 2.2 六層是哪六層

以 `CASM001`(境內基金潛在客戶維護)走一遍。六個專案、六個檔、六個組件:

| # | 層 | 專案 | 檔案 | 類別 | 行數 |
|---|---|---|---|---|---|
| 1 | UI | `UI.CAS` | `CASM001.cs` | `CASM001 : xMaintainForm` | 783 |
| 2 | FormProxy | `FormProxy.CAS` | `CASM001_Pxy.cs` | `CASM001_Pxy : Basic_Pxy` | 164 |
| 3 | Control | `Control.CAS` | `CASM001_Ctl.cs` | `CASM001_Ctl : BaseController` | 244 |
| 4 | PO | `PO.CAS` | `CASM001_PO.cs` | `CASM001_PO : BaseEVADaoPO, ICASM001_PO` | 636 |
| 5 | DataEntity | `DataEntity.CAS` | `CASM001Model.xsd` + `CASM001ModelVDB.cs` | `CASM001ModelVDB : BasicTAModelVDB` | 142 + 45 |
| 6 | UIEntity | `UIEntity.CAS` | `CASM001View.xsd` + `CASM001ViewVDB.cs` | `CASM001ViewVDB : BasicTAViewVDB` | 142 + 42 |

職責一句話版:

| 層 | 職責 | 不該做的事 |
|---|---|---|
| UI | 擺控件、綁事件、把畫面欄位塞進 `ProcessVDB`;生命週期掛在 `FormInitial` / `*DataLoad` / `Before*ButtonClicked` 事件上 | 不直接碰 DB |
| FormProxy | 遠端門面。每個 public method 都是 `try { new _Ctl(); 呼叫 } catch { CommonExceptionBlocker.HandleFormProxyException(ex); 回傳降級值 }` | 不放商業邏輯 |
| Control | 組 PO、宣告 VDB 型別、做 Model 與 View 互搬、包 `ExecPOActionToViewVDB` | 不寫 SQL |
| PO | 唯一碰資料庫的層;宣告主明細表對應、組 SQL 或叫 SP | 不認識 ViewVDB(只吃 ModelVDB) |
| DataEntity | 伺服器側 typed DataSet(貼近實體表) | 不放邏輯 |
| UIEntity | 用戶端側 typed DataSet(貼近畫面),`[Serializable]` 可跨 Remoting | 不放邏輯 |

關鍵接點,逐個都有錨點:

- UI 在 `FormInitial` 一次綁好兩件事:`this.ProcessVDB = new CASM001ViewVDB(); this.FormProxy = new CASM001_Pxy();` `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:110-111`

- Pxy 用 `InitializeControl()` 覆寫把 Control 掛上:`Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:20-23`

- Ctl 用兩個 `override` 完成註冊:`InitializeDataAccessPool()` 把 PO 加進池、`InitializeVDBTypes()` 宣告三個型別 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:36-39` 與 `:43-48`

- PO 在建構子宣告主明細表(`xTableMapping`),這是全庫「實體表」清單的唯一來源 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:46-47`

- Ctl 的 `CustomTransferOracleModelToView` 與 `CustomTransferViewToOracleModel` 逐表手搬 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:79-96` 與 `:105-121`

`CASM001_PO` 建構子還掛了十個事件(`BeforeSelect` / `AfterVerify` / `AfterApprove` …, `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:42-58`),那是四眼流程的掛鉤點,**見 §3**。

### 2.3 基底類別:哪些看得到、哪些只在 DLL 裡

六層的基底分兩堆。**repo 內有原始碼的只有兩支**:

| 基底 | 位置 | 行數 |
|---|---|---|
| `BasicTAModelVDB` | `Dev/Common/Source/Base/TA.DataEntity/BasicTAModelVDB.cs:8` | 39 |
| `BasicTAViewVDB` | `Dev/Common/Source/Base/TA.UIEntity/BasicTAViewVDB.cs:9` | 40 |

這兩支只做一件事:掛一個共用的 `TAModel` / `TAView` typed DataSet 當工具欄位 (`TaModelUtility` / `TaViewUtility`,`Dev/Common/Source/Base/TA.DataEntity/BasicTAModelVDB.cs:23-27`)。 `CASM001_Ctl` 搬 `SrNoComment` 走的就是它(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:92`)。

**其餘全部無原始碼,只能從呼叫端反推**(以下每個類別第一次提到即標明此點):

| 基底 | 所在組件 | 反推依據 |
|---|---|---|
| `Basic_Pxy`(無原始碼,從呼叫端反推) | `Vendor.Product.FormProxy.dll` | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/FormProxy.CAS.csproj:66-68` 的 `Reference` + `HintPath`;`CASM001_Pxy.cs:15` 繼承它 |
| `BaseController`(無原始碼,從呼叫端反推) | 未直接標示,推測在 `Vendor.Product.Utility.dll` | `CASM001_Ctl.cs:17` 繼承,`using Vendor.Product.Utility;` 於 `CASM001_Ctl.cs:13`;全庫 grep `class BaseController` 零命中 |
| `BasicModelVDB`(無原始碼,從呼叫端反推) | `Vendor.Product.Entity.DataEntity.dll` | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:66-68` |
| `BasicViewVDB`(無原始碼,從呼叫端反推) | `Vendor.Product.Entity.UIEntity.dll` | `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj:66-68` |
| `xMaintainForm` / `xOneStepProcessForm` / `xReportForm` / `xQueryForm` / `yPopUpForm`(皆無原始碼) | `Vendor.Product.UI.dll` | `using Vendor.Product.UI.MiddleForm;`(`CASM001.cs:10`);全庫 grep `class xMaintainForm` 零命中 |

所有 HintPath 指向同一個目錄 **`C:\Program Files\Vendor\PTPFBlock\`**,而且六個 csproj 的 Debug `OutputPath` 也寫死同一個目錄(例:`Dev/ATLAS.CAS/Source/Control/Control.CAS/Control.CAS.csproj:25`)。也就是 **build 產出直接覆蓋框架安裝目錄,框架 DLL 與業務 DLL 混在同一個資料夾**。這條絕對路徑寫死在全庫 csproj 裡,逐開發機必須一致——標 **〔客戶特定〕**。

`BaseEVADaoPO`(PO 的基底)**在 repo 內**:`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17`, 它是四眼引擎的核心,**見 §3**。

### 2.4 六個 csproj 的相依圖與重編順序

從六個 `.csproj` 的 `ProjectReference` 直接畫出來(略去 `Dev/Common` 的共用專案):

```
DataEntity.CAS ──┬──> PO.CAS ──┐
                 │             ├──> Control.CAS ──> FormProxy.CAS ──> UI.CAS
UIEntity.CAS ────┴─────────────┘           ^              ^              ^
      └────────────────────────────────────┘              │              │
      └───────────────────────────────────────────────────┘              │
      └────────────────────────────────────────────────────────────────-─┘
```

逐檔錨點:

| 專案 | 同模組 ProjectReference | 錨點 |
|---|---|---|
| `DataEntity.CAS` | 無(只靠 `TA.BasicDataEntity`) | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:216-219` |
| `UIEntity.CAS` | 無(只靠 `TA.BasicUIEntity`) | `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj:216-219` |
| `PO.CAS` | `DataEntity.CAS` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:111-134` |
| `Control.CAS` | `DataEntity.CAS`、`UIEntity.CAS`、`PO.CAS` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/Control.CAS.csproj:92-127` |
| `FormProxy.CAS` | `Control.CAS`、`UIEntity.CAS` | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/FormProxy.CAS.csproj:88-99` |
| `UI.CAS` | `UIEntity.CAS`、`FormProxy.CAS` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/UI.CAS.csproj:275-318` |

**重編順序**(拓樸排序,手動重編照這個順序走):

| 步 | 專案 | 吃誰 |
|---|---|---|
| 1 | `DataEntity.CAS` | — |
| 2 | `UIEntity.CAS` | —(與 1 無關,可並行) |
| 3 | `PO.CAS` | 1 |
| 4 | `Control.CAS` | 1 + 2 + 3 |
| 5 | `FormProxy.CAS` | 2 + 4 |
| 6 | `UI.CAS` | 2 + 5 |

兩件事值得記住:

- **`PO.CAS` 不認識 `UIEntity.CAS`** —— 刻意的,PO 只吃 ModelVDB,ViewVDB 對它不存在。

- **`UI.CAS` 不認識 `DataEntity.CAS`** —— 用戶端拿不到伺服器側型別。

兩邊唯一交會點是 `Control.CAS`,所以 **Model 與 View 的轉換只能寫在 Control 層**, 這是專案相依圖強制的,不是慣例;想在 PO 或 UI 做轉換會編不過。

### 2.5 Remoting 邊界在哪一層

先排除一個錯誤答案。`CASM001_Pxy.Add()` 裡是 `CASM001_Ctl ctl = new CASM001_Ctl();` (`Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:34`),而且 `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/FormProxy.CAS.csproj:92-95` 直接 `ProjectReference` 到 `Control.CAS`。**Pxy 與 Ctl 之間沒有任何遠端機制,是同 process 直接呼叫。**

邊界在 **UI 與 FormProxy 之間** —— `_Pxy` 這個型別本身就是遠端物件。四條證據:

1. **有 `_Pxy` 明確繼承 `MarshalByRefObject`**: `Dev/Modules/Source/Vendor.Modules.GenFiles/FormProxy/FormProxy.GenFiles/DataProcess_Pxy.cs:11`。這是全 repo 唯一直接繼承的一支,其餘都繼承 `Basic_Pxy`,但兩者結構完全相同 (try / new _Ctl / catch 轉例外),可推定 `Basic_Pxy` 也是 `MarshalByRefObject` 子類。

2. **`app.config` 把 `_Pxy` 註冊成 wellknown 遠端型別**: `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:175-194`,其中 `:189` 是 `<wellknown type="...OFDB600_Pxy, Vendor.Product.TA.FormProxy.EC" url="http://<內網伺服器IP>/ATLAS_TAService/OFDB600_Pxy.rem"/>`。註冊成 wellknown client type 後,用戶端寫 `new OFDB600_Pxy()` 拿到的是透明代理而非本地物件—— 這正好解釋為什麼 UI 到處都是 `new CASM001_Pxy()` (`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:111`、`:374`、`:438`、`:470`、`:694`)卻沒人覺得浪費。

3. **只有 ViewVDB 標 `[Serializable]` 且指定二進位序列化**: `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001ViewVDB.cs:10-11` 與 `:20` (`RemotingFormat = System.Data.SerializationFormat.Binary`)。對照 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001ModelVDB.cs:14` 完全沒有 `[Serializable]`。 **會過線的只有 ViewVDB**,與「邊界在 Pxy 前面」完全一致。

4. **channel 是 http + binary formatter**:同一份 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:178-184`。

**這是推論,不是原始碼證明** —— `Basic_Pxy` 沒有原始碼,無法直接看到 `: MarshalByRefObject`。但四條旁證互相吻合,且沒有反證(repo 內找不到 WCF `ServiceContract`,也找不到 HTTP client 呼叫 Pxy)。

一個現況修正,**寫進來以免誤判**:用戶端那份 remoting 設定是**被整段註解掉的**。 `Dev/Common/Source/CustomControl/TestWindowControls/App.config:102-136` 整個 `<system.runtime.remoting>` 包在註解裡,channel 與 wellknown 清單外殼都還在。 **假設**:主用戶端實際跑的是另一份 config(repo 內找不到主 EXE 專案),或現行部署改由框架在程式內註冊。依據是 repo 內 `RemotingConfiguration.Configure(...)` 的呼叫全部集中在三支 WindowsService (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50-52`、 `.../WindowsService.OFDB609/OFDB609_Service.cs:40-42`、`.../WindowsService.OFDB680/OFDB680_Service.cs:42-44`), 沒有任何用戶端呼叫點。這條要現場確認,不要當事實用。

URL 裡的 `<內網伺服器IP>` 與 `/ATLAS_TAService/` 虛擬目錄逐站一定不同,標 **〔客戶特定〕**。

### 2.6 命名鐵律的例外(除了 `.Report` 那組)

`.Report` 的例外寫在 §6.5。除它之外還有五類,都踩得到:

| # | 例外 | 具體 | 影響 |
|---|---|---|---|
| 1 | **`.Query` 專案也加前綴** | `Dev/ATLAS.EC.Query/Source/` 底下是 `QueryControl.EC` / `QueryUI.EC` / `QueryPO.EC` / `QueryDataEntity.EC` / `QueryUIEntity.EC` / `QueryFormProxy.EC` | 「加前綴」其實有兩組,不是只有 `.Report` |
| 2 | **專案名不等於模組碼** | `ATLAS.EC` 裝 `OFD`+`IPJ`;`ATLAS.OFDB` / `ATLAS.OFDI` 裝 `OFD`;`ATLAS.OTA` / `ATLAS.OTAB` 裝 `OFD`+`OTA`+`TRP`;`ATLAS.COD` 還藏了 `CTL` | 靠代號前三碼找專案會找錯,必須查索引 |
| 3 | **專案名與層資料夾不同名** | `Dev/ATLAS.OTAB/Source/Control/Control.OTA/OFDB562_Ctl.cs`(專案 OTAB、資料夾 OTA);`Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/OFDI601_Ctl.cs` | glob 寫死 `Control.<專案尾碼>` 會漏 |
| 4 | **`Source` 資料夾大小寫不一致** | 36 個專案裡 34 個是 `Source`,`ATLAS.CLS` 與 `ATLAS.CPM` 是 `SOURCE`;例:`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs` | Windows 無感;大小寫敏感工具(Linux CI、Python glob)會整個漏掉這兩個模組 |
| 5 | **模組碼打錯字** | `IJPR611` —— `IPJ` 打成 `IJP`,全庫就這一支:`Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/IJPR611_Ctl.cs` | 依模組聚合的報表 / 權限 / 部署清單會漏 |

另外 **15 個代號同時實作在兩個專案**(掃描器實測):

| 代號群 | 兩處 | 性質 |
|---|---|---|
| `OFDB562`–`OFDB564` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB562.cs` 與 `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB562.cs`(六層全複製) | 真分岔,兩份都在編 |
| `OFDI601`–`OFDI615` | `Dev/ATLAS.EC.Query/Source/UI/QueryUI.EC/OFDI601.cs` 與 `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/OFDI601.cs` | 真分岔 |
| `OFDI016` | `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI016.cs` 與 `Dev/ATLAS.OFD.Query/20220518/OFDI016.cs` | **不是分岔** —— `20220518/` 是日期命名的備份資料夾,直接躺在專案根目錄,全庫 csproj 找不到它,不參與編譯 |

改 `OFDB562` 或 `OFDI601` 這兩群時必須兩邊都改,否則兩個入口行為不一致。

### 2.7 六層不齊的 65 支:掃描器說缺,不等於真的缺

掃描器實測 911 支裡 **52 支六層不齊**,組合分布:

| 缺哪幾層 | 支數 |
|---|---|
| model + view | 28 |
| po + model + view | 20 |
| po | 10 |
| pxy | 3 |
| model | 2 |
| ui + model + view | 1 |
| view | 1 |

依模組:`OFD` 42、**`IPJ` 15(該模組 15 支全不齊)**、`COD` 3,其餘 `BMS` / `CLS` / `DSM` / `IJP` / `TRP` 各 1。

`IPJ` 15/15 全中太整齊,查下去是**兩個假警報**:

**假警報一:entity 檔名帶 `_9i` 後綴。** `IPJB606` 的 xsd 實際叫 `IPJB606_9iModel.xsd` / `IPJB606_9iView.xsd`; `IPJI612`、`IPJI630`、`IPJM614`、`IPJR607`、`IPJR901` 同理。掃描器以「代號 + `Model.xsd`」字面比對,所以判缺。全 repo 有 **807 個 `_9i` 檔名**(323 支 `.cs`、132 組 `.xsd`/`.xsc`/`.xss`、48 支 `.dll`), 是 Oracle 9i 時期平行實作留下來的,規模不小。

**假警報二:PO 層在 `.Query` 專案換了一整套命名。** `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/` 底下不是 `<代號>_PO.cs`,而是拆成三個子資料夾:

| 子資料夾 | 命名 | 例 |
|---|---|---|
| `Interface/` | `I<代號>`,不是 `I<代號>_PO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Interface/IIPJI613.cs` |
| `Oracle/` | `<代號>OracleDao` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs` |
| `MSSQL/` | 又退回舊命名 `<代號>_PO` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/MSSQL/OFDI601_PO.cs` |

`Dev/ATLAS.EC.Query/Source/Control/QueryControl.EC/IPJI613_Ctl.cs:21-25` 就是 `base.DataAccessPool.Add(new IPJI613OracleDao());`,`:40` 是 `this.GetDaoInstance<IIPJI613>()`。所以 PO 存在,只是名字不照鐵律。而且 `MSSQL/` 與 `Oracle/` 並存,是同一概念的兩套實作。

**真缺的那些**大多是 `B` 與 `R`:`OFDB615` / `OFDB616` / `OFDB693` / `OFDM697`–`OFDM699` 這類, Ctl 存在但沒有自己的 entity,原因見 §6.6。

**結論:65 是「命名不合鐵律」與「真缺」的混合,不能當技術債計數直接用。** 保守估計:`IPJ` 15 支是純命名問題;`OFD` 42 支裡至少 6 支 (`OFDB671`–`OFDB673`、`OFDM672`、`OFDM674`、`OFDI641`)是 `*OracleDao` 命名問題。這是**假設**,依據是這 6 支的 Ctl 都在 `.Query` 或 EC 專案內、且缺的恰好只有 `po` 一層。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| build 產出直接寫進框架安裝目錄,業務 DLL 與框架 DLL 混放 | 無法用資料夾區分「我們的」與「框架的」;回滾只能逐檔;多分支並行會互相覆蓋 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/Control.CAS.csproj:25`〔客戶特定〕 | 高 |
| Remoting 邊界的關鍵型別 `Basic_Pxy` 無原始碼,只能反推 | 遠端呼叫的例外、逾時、序列化行為無法查證 | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:15` | 高 |
| 用戶端 remoting 設定整段被註解,外殼還在 | 照 config 讀會得到錯誤結論;實際端點來源不明 | `Dev/Common/Source/CustomControl/TestWindowControls/App.config:102-136` | 中 |
| 遠端 URL 寫死內網 IP | 換站必改,且散在各 service config | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189`〔客戶特定〕 | 中 |
| `_9i` 平行實作 807 檔仍在 repo | 改共用邏輯容易只改一半;搜尋結果永遠雙份 | `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/IPJB606_9iModel.xsd` | 中 |
| 同一支 UI 內 `GetDropDown9iDataSrc` 與 `GetDropDownDataSrc` 混用,同代碼 `467`/`468` 走不同實作 | grid 與 combo 的下拉清單可能不一致 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:120-121` 對照 `:195-197` | 中 |
| 15 個畫面代號兩份實作 | 改一邊漏一邊 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB562.cs` 與 `Dev/ATLAS.OTAB/Source/UI/UI.OTA/OFDB562.cs` | 中 |
| 備份資料夾 `20220518/` 進版控,六層俱全但不編譯 | 搜尋命中誤導;可能改到不會生效的檔 | `Dev/ATLAS.OFD.Query/20220518/OFDI016_Ctl.cs` | 中 |
| `.Query` 專案 PO 命名三套並存(`I<代號>` / `<代號>OracleDao` / `<代號>_PO`) | 任何以命名找層的工具都會誤判「缺 PO」 | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs` | 中 |
| 2 個專案用大寫 `SOURCE` | 大小寫敏感工具漏掃兩個模組 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs` | 低 |
| 模組碼錯字 `IJP` 一支 | 依模組聚合的清單會漏 | `Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/IJPR611_Ctl.cs` | 低 |
| 同一行重複兩次(`m_PkeyNotInMaster.Add("STAFF_NAME")`) | 無功能影響,但顯示此區塊靠複製貼上維護 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:129` 與 `:136` | 低 |

## 3. 四眼(EVA)引擎

```text
[圖] 四眼狀態機:未送審到 Entry、Verify、Approve 三段,加上退回、重送、覆核刪除與還原
圖中文字:三段式主線(STATUS 前綴,見 §3.10) / 未送審 / 尚無 STATUS / Entry* / 輸入完成,待驗證 / Verify* / 驗證完成,待覆核 / Approve* / 已覆核,正式生效 / 四種動作各自有一組 STATUS,共 12 個值 / Add 新增 / EntryAdd → VerifyAdd → ApproveAdd / Modify 修改 / Entry/Verify/ApproveModify / Delete 刪除送審 / Entry/Verify/ApproveDelete / UndoDelete 取消刪除 / Entry/Verify/ApproveUndoDelete / 分支動作 / Reject 退回 / 寫 REJECTID / REJECTDATE / Resend 重送 / 回到 Entry* / ApproveDelete / 覆核刪除 → 實體 DELETE / Recover 還原 / 僅四眼那套在用(死碼) / 每個動作都改寫的欄位 / UPDATEID / UPDATEDATE / 無論哪個 EVAType 都重寫 / 固定送 13 個欄位 / 與 EVAType 無關,由 DLL 決定值 / dataid / 僅 INSERT 時寫,主明細共用
```

*圖:圖 3 四眼狀態機。三段主線 × 四種動作 = 12 個 STATUS 值;實際字面值在 DLL 內,§3.10 的對應是反推。虛線為死碼路徑。欄位寫入規則見 §3.5(標假設)。*

EVA = Entry / Verify / Approve。ATLAS 所有維護畫面的資料異動都不直接生效，必須經過「輸入 → 驗證 → 覆核」三段，每段留下一組 `*ID` / `*DATE`，並推進 `STATUS` 欄位上的狀態機。這一節講引擎本身:誰負責什麼、流程怎麼跑、哪些地方是外殼還在但裡面已經空掉。

Framework DLL(`Vendor.Product.DataAccess` / `Vendor.Product.Utility.MappingCode`) 本機沒有原始碼;凡取自該層的型別都會標注「無原始碼，從呼叫端反推」。

### 3.1 四支 PO 基底的分工

先破除一個直覺:這四支**不是繼承鏈**，是四個平輩，全部直接繼承 `Basic_PO` (無原始碼，從呼叫端反推 —— 提供 `ExecuteNonQuery` / `ExecuteScalar` 兩個吃 `DbTransaction` 的執行入口)。

| 類別 | 錨點 | 職責 | 全庫子類數 |
|---|---|---|---|
| `TA_PO` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:19-19` | 最早一代:SQL 在 code 裡逐行串，欄位清單靠呼叫端傳 `string[] datacolumn` | **0**(僅存 2 處被註解掉的宣告) |
| `BasicEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:24-24` | 單筆主檔 + N 個明細檔;SQL 改由 `TableHelper` 依 table schema 生成 | 66(另 46 處已被註解) |
| `MultiRowEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:16-16` | 多筆主檔(`MasterTable` 是 `List`)，沒有明細概念 | 11(另 5 處已被註解) |
| `Basic4EyesPO` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:28-28` | Edit Table / Real Table 雙表的四眼 | **0** |
| `MultiRow4EyesPO` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2428-2428` | 上一列的多筆版 | **0** |

計數方式:對 `Dev/` 下所有非 `*.Designer.cs` 的 `.cs` 掃 `class X : Base` 取第一個 base 型別，並**排除以 `//` 開頭的行**。這個排除很重要 —— 舊世代有大量 PO 類別是整個被註解掉、檔案還留著的： `TA_PO` 的兩個子類 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs:18-18` 與 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM694_PO.cs:20-20` 都是註解行，所以 **`TA_PO` 整支 2,106 行實際上也是死碼**；`BasicEVAPO` 有 46 處、`MultiRowEVAPO` 有 5 處同樣情況 (例:`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDB600_PO.cs:16-16`、 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:23-23`)。這些檔大多已重寫成 Dao 世代。

實際的 `*_PO.cs` 絕大多數**不繼承上面任何一支**，而是繼承兩支薄殼:

| 薄殼 | 錨點 | 繼承 | 子類數 |
|---|---|---|---|
| `BaseEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17-27` | `BaseEVADao`(無原始碼，從呼叫端反推) | 271 |
| `BaseMultiRowEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:18-31` | `BaseMultiRowEVADao`(無原始碼，從呼叫端反推) | 61 |

`BaseEVADaoPO` 本體只做三件事:建構子鎖死 `base("TA", DbServerType.Oracle)`(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:22-26`)、一個 `AddM` 轉呼叫(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:143-146`)、一個 `CopyDetail`(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:155-227`)。其餘 EVA 動作全在 DLL 裡。

所以現況是**兩個世代並存**:

- **舊世代(有原始碼)**:`TA_PO` / `BasicEVAPO` / `MultiRowEVAPO` / `Basic4EyesPO`，搭配 `TableMapping`、`PrepareSQLEventArgs`，以及 `Vendor.Product.TA.ServerUtility.SQLHelper` 底下的 `TableHelper` / `EVAStringHelper`。

- **新世代(在 DLL)**:`BaseEVADao` / `BaseMultiRowEVADao`，搭配 `xTableMapping`、`xEVAEventArgs`、 `xTableHelper`、`xEVAStringHelper`、`xEVAUtility`(全部無原始碼，從呼叫端反推)。

`CASM001_PO` 屬新世代:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:36-37` 標 `[PODbType(DbServerType.Oracle)]` 並繼承 `BaseEVADaoPO`。

### 3.1.1 ⚠ `BasicEVAPO` 的連線從沒被建立 —— 73 支畫面存檔會 NRE

上表把 `BasicEVAPO` 標成「舊世代、66 個活子類」。**那句話太客氣了。**寫 `ofd8` 模組知識庫時查出, 這條路徑實際上是斷的,證據鏈沒有缺口:

| # | 事實 | 錨點 |
|---|---|---|
| 1 | `dbTA` / `dbPTPF` 宣告就是 `= null` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26-27` |
| 2 | 建構子裡建立連線那四行**整段被註解**,只剩一個沒人用的 `config` 區域變數 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:164-172` |
| 3 | 基底 `Add()` 第一件事就是 `cn = dbTA.CreateConnection();` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187` |
| 4 | 全庫 **77 個活子類,沒有一支自己賦值 `dbTA`** | 實掃 `Dev/` 全部 `*_PO.cs`,剝註解後比對 |
| 5 | 其中 **73 支完全不覆寫 `Add` / `Update` / `Delete`**,直接吃基底 | 同上 |

**推得的結論:繼承 `BasicEVAPO` / `MultiRowEVAPO` 而不覆寫的那 73 支畫面,一按存檔就 `NullReferenceException`。**

> **這是讀碼結論,沒有實跑過**(本機缺 PTPFBlock,見附錄 C.1)。但四個條件同時成立且彼此獨立, 要推翻它得證明 `dbTA` 在別處被賦值 —— 全庫剝註解後掃過,沒有。

旁證:`ofd8.md` 在它那片找到的 7 支這種畫面,SQL 還留著 T-SQL 痕跡 (`[OFD321]` 方括號、`DECLARE @x`、`@@FETCH_STATUS`)—— 它們是 SQL Server 時代沒遷過來的舊畫面。 **合理的解讀是這 73 支早就沒在用**,而不是天天在現場爆錯。

**對維護的意義**:接到「某支畫面壞掉」的單,**第一件事是看它的 PO 繼承誰**。繼承 `BaseEVADaoPO`(271 支)或 `BaseMultiRowEVADaoPO`(61 支)才是現行主線; 繼承 `BasicEVAPO` / `MultiRowEVAPO` 的,先確認它到底有沒有在跑,再談修。查法:`grep -n "class .*_PO *:" <該支 PO>`。

### 3.2 `Basic4EyesPO` 4,257 行，比 `BasicEVAPO` 多出來的 2,000 行是什麼

兩件事，各佔一半。

**(a) 同一個檔裡塞了第二個類別。** `Basic4EyesPO` 類別本體在 `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:28-2417` 就結束; `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2419-4257` 是另一個完全獨立的 `MultiRow4EyesPO`。用非空白行做序列比對， `MultiRow4EyesPO`(1,692 行)與 `MultiRowEVAPO`(1,559 行)相似度 **0.878** —— 它是 `MultiRowEVAPO` 的複製貼上分身，差別只在 table 名稱指向 `_Edit` 表。

**(b) 剩下約 220 行是 Edit / Real 雙表機制。** `Basic4EyesPO` 本體與 `BasicEVAPO` 相似度 **0.668**，多出來的成員是:

| 多出來的成員 | 錨點 | 作用 |
|---|---|---|
| `prefixEditTable = "_Edit"` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:35-35` | 寫死字尾;每張表都要有一張 `<TABLE>_Edit` 雙胞胎 |
| `GetRealData` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:880-880` | 讀已覆核的正式表(其他方法讀 `_Edit`) |
| `Recovery` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:1427-1427` | 正式表資料倒灌回 `_Edit` |
| `Recover` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:1861-1861` | 同一件事的另一套實作 |
| `OnBeforeWriteToEdit` / `OnBeforeWriteToReal` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2301-2310` | 雙表搬移掛點(沒有對應的 `OnAfterWriteTo*`) |

命名規則寫在 `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2419-2427`:Edit Table = `<表名>_Edit`、Log Table = `<表名>_Log`。但 Log Table 從未實作 —— 兩個類別都把 `prefixLogTable` 註解掉並留言「完全沒有用到，故 mark」 (`Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:36-38` 與 `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2434-2437`)。

**最重要的一點:這 4,257 行全是死的。** 全庫沒有任何類別繼承 `Basic4EyesPO` 或 `MultiRow4EyesPO`，也沒有任何地方 `new` 它們;唯一引用是 `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:130-130` 的 `<Compile Include="Basic4EyesPO.cs" />`。連帶讓 `FourEyesHelper`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1229-1229`)整個類別也成為死碼 —— 它的呼叫端全部落在 `Basic4EyesPO.cs` 裡。

### 3.3 `EVAType` 的值域(反推)

`EVAType`(無原始碼，從呼叫端反推)定義在 Framework DLL。用兩條線索交叉反推: (1) 全庫 `EVAType.<X>` 出現統計;(2) `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:63-341` 一整排 `Set<X>Status` 方法 —— 每個動作一支。兩邊得到同一組 **10 個值**:

| 值 | 出現次數 | `EVAUtility` 對應方法錨點 | 語意 |
|---|---|---|---|
| `Add` | 85 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:63-63` | 新增送審 |
| `Modify` | 80 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:117-117` | 修改送審 |
| `Delete` | 79 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:142-142` | 刪除送審(邏輯刪除) |
| `Verify` | 75 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:167-167` | 驗證(第二眼) |
| `Approve` | 79 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:192-192` | 覆核(第三眼) |
| `ApproveDelete` | 102 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:217-217` | 覆核刪除 → 實體 DELETE |
| `UnDelete` | 75 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:242-242` | 取消刪除送審 |
| `Reject` | 73 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:267-267` | 退回 |
| `Resend` | 73 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:292-292` | 退回後重送 |
| `Recover` | 4 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:317-317` | 還原(只有四眼那套在用) |

分派器在 `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:343-363`;它只對 `EVAType.Add` 特判塞 `dataid`，其餘一律丟給 `UseCaseSecurity.SetFunctionSecurityData`(無原始碼，從呼叫端反推)。

`dataid` 來自 `Guid.NewGuid()`，在 `EVAUtility` 建構子產生(`Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:50-55`) —— 同一次 `EVAUtility` 生命週期內所有 row 共用一個 `dataid`，這是主明細綁在一起送審的機制。

另有兩組平行的狀態列舉:`PrepareSQLStatus`(有原始碼，14 個值，給舊世代事件用)在 `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:10-10`; 新世代用 `xEVAStatus`(無原始碼，從呼叫端反推)，實際只看到 `ToDO` / `Insert` / `Update` / `ApproveDelete` / `Select` 五個值被使用。**三套列舉彼此不對應**，§3.11 再算帳。

### 3.4 `EVA()` 主流程

`TA_PO` 兩個 `EVA` overload 的差別只在**有沒有明細表**:

| overload | 錨點 | 參數差異 |
|---|---|---|
| 單表 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:405-558` | 只有 `tb` / `TableName` |
| 主明細 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:566-752` | 多一組 `Detailtb` / `DetailTableName` |

方法註解寫得很清楚:「只針對 Status 及 EntryID/EntryDate 等欄位修改，不修改其他資料欄位」 (`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:399-404`)。也就是 `EVA()` 是**純狀態推進**，不碰業務欄位。單表版步驟:

1. 取主檔 row:`VirtualDataBase.GetMasterRow(tb)`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:416-416`)。

2. `SetTASecurityData` 決定要寫哪些 `*ID` / `*DATE` / `STATUS`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:418-418`); 失敗直接 `SetActionFailed` 收工(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:420-424`)。

3. 串一段固定 UPDATE:`SET` 就是那 13 個 EVA 欄位，`WHERE` 由 `tb.PrimaryKey` 迴圈串出(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:432-454`)。

4. 取 `GetTableDeleted` 與 `GetTableModified` 兩批 row(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:462-463`)，逐筆先做 `IsDataChanged` 樂觀鎖檢查(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:469-473` / `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:507-511`)，再綁參數 + `ExecuteNonQuery` (`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:488-490` / `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:527-529`)。

5. 影響筆數不等於 1 就整批失敗(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:492-496`)。

6. 全成功 → `SetActionSuccess`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:541-545`)。

主明細版多做一件事:進迴圈前先對主檔做一次 `IsDataChanged`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:587-591`);單表版沒有這道前置檢查。

兩個要留意的地方:單表版處理的明明是主檔 row，卻呼叫 `SetDetailParameter` 而非 `SetParameter` (`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:488-490`);而開頭「明細資料已被您異動」的檢查整段被註解掉(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:410-414`)。

### 3.5 `SetTASecurityData` 依 `EVAType` 寫哪些欄位

先講結論:**這支本身什麼都不做。** `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:2044-2047` 整支只有一行 `return UseCaseSecurity.SetFunctionSecurityDataInfo(rrRow, vdb, evaType, Dbtra, DB);` (`UseCaseSecurity` 無原始碼，從呼叫端反推)。它是 `virtual` 擴充點，但全庫沒人覆寫。

真正的欄位清單可從三處反推，三邊完全一致 —— **固定 13 個欄位，與 `EVAType` 無關** (哪個動作都送全部 13 個，由 DLL 決定各欄位的值):

| 反推來源 | 錨點 |
|---|---|
| `SetBasicParameter` 被註解掉的 13 行 `AddInParameter` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:108-138` |
| `EVA()` 串出來的 `UPDATE ... SET` 13 欄 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:435-447` |
| `EVAStringHelper.UpdateString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:110-138` |

| 欄位 | 型別 | 值從哪來(反推) |
|---|---|---|
| `STATUS` | 字串 | `EVAStatusCode` 常數(無原始碼);見 §3.10 |
| `CREATEID` / `CREATEDATE` | 字串 / 日期 | 第一次 `Add` 寫入，之後原樣帶著走 |
| `UPDATEID` / `UPDATEDATE` | 字串 / 日期 | **每個** EVA 動作都改寫成當前使用者 / 當下時間 |
| `ENTRYID` / `ENTRYDATE` | 字串 / 日期 | `Add` / `Modify` / `Delete` / `UnDelete` / `Resend` 寫入 |
| `VERIFYID` / `VERIFYDATE` | 字串 / 日期 | `Verify` 寫入 |
| `APPROVEID` / `APPROVEDATE` | 字串 / 日期 | `Approve` / `ApproveDelete` 寫入 |
| `REJECTID` / `REJECTDATE` | 字串 / 日期 | `Reject` 寫入 |

右欄「哪個動作寫哪一組」標**假設**。依據是 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:177-199` 的待辦事項條件式 —— 它用 `UPDATEDATE = VERIFYDATE` 判斷「最後動作是驗證」、`ENTRYDATE <> VERIFYDATE` 判斷「不是剛輸入完」、`RejectID <> ''` 判斷「被退過」。這些判斷式只有在上表規則成立時才說得通。實際賦值在 DLL 內，本機看不到，也找不到其他呼叫端可以佐證。

第 14 個欄位 `dataid` 只在 INSERT 時寫(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:780-812`);第 15 個 `DataFlag` 由資料庫維護、程式一律排除(見 §4.2)。`EVAStringHelper.SelectString` 一次撈這 15 欄(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:56-77`)。

### 3.6 `IsDataChanged` / `IsDataExit` ——「新增欄位會不會被比到?」

**不會。不管走哪一世代都是 NO。** 這一題直接決定 `add-column.md` 要不要提醒讀者「樂觀鎖不會涵蓋你的新欄位」。

四個並存的實作:

| 方法 | 錨點 | 比什麼 | 回傳 |
|---|---|---|---|
| `TA_PO.IsDataChanged` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:323-354` | `DataFlag = @DataFlag` + 全部 PK | `COUNT(*) == 1` → `false`(沒變);否則 `true` |
| `TA_PO.IsDataExit` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:364-394` | 只有 PK | `COUNT(*) > 0` → `true` |
| `BasicEVAPO.IsChangedByData` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:1844-1858` | 委派 `TableHelper.GetIsChangedString` | 同上 |
| `MultiRowEVAPO.IsChangedByData` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1492-1507` | 同上，但會依 `RemovePK` 把部分 PK 條件字串 `Replace` 掉 | 同上 |

`TableHelper.GetIsChangedString` 本體在 `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:974-989`，產出:

```
SELECT COUNT(*) FROM <table> WHERE DataFlag = @DataFlag AND <每個 PK> = @<PK>
```

**比對的只有 `DataFlag` 這一個 row-version 欄位加上 PK，業務欄位一個都沒進去。** 所以新增欄位不需要、也不可能讓它「自動比到」—— 樂觀鎖靠的是資料庫自己更新 `DataFlag`。反過來說，新表若忘了建 `DataFlag`，這支 SQL 會直接炸 `ORA-00904`，而不是「比不到」。

排除清單同樣寫死:`DataFlag` 在 INSERT / UPDATE / 參數綁定中一律被跳過 (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:496-496`、`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:531-531`、`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1018-1025`)。

呼叫端:`TA_PO` 的 `EVA` / `Update` / `ApproveDelete`(例如 `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:469-473`、`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:587-591`); `BasicEVAPO.Update` 主檔與三種明細狀態各一次(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:411-412`、`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:464-465`、`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:527-528`); 新世代在 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:175-176` 與 `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:142-143`。

`IsDataExit`(原文就少一個 `x`)/ `IsExistByData` 只比 PK，用途是 Add 前擋重複、Update 前確認還在: `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:262-263`(Add)、`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:408-409`(Update)、`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:851-855`(Add)。多筆版另有 `IsExistByMasterPK`(`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1465-1487`)，用自定的 `MasterPKey` 清單而不是 table PK。

### 3.7 `TranData` 與 `TranToDo`、`SetActionSuccess` / `SetActionFailed`

兩個交易打的是**兩個不同的資料庫**:

| 交易 | 連線來源 | 打哪個庫 | 內容 |
|---|---|---|---|
| `TranData` / `tran` | `dbTA` | 業務庫(連線名 `"TA"`) | 業務表 + 那 13 個 EVA 欄位 |
| `TranToDo` / `tran_ToDo` / `tranptpf` | `dbPTPF` | 平台庫(`SWProduct` / PTPF) | 待辦事項(ToDo):誰該來驗證 / 覆核這筆 |

證據:`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187-192` 一次開兩條連線兩個交易;`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-173` 建構子註解裡 `provider.Create("TA")` 與 `provider.Create("SWProduct")` 兩行分別對應 `dbTA` / `dbPTPF`;`Set*StatusToDo` 這類方法吃的就是 PTPF 的連線與交易(`Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:374-374`)。

`SetActionSuccess` / `SetActionFailed` 是**舊世代 `TA_PO` 專用**的收尾:

| 方法 | 錨點 | 做什麼 |
|---|---|---|
| `SetActionSuccess` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:283-297` | 兩個交易各 `Commit()`(null 跳過) → `VDB.Utility.Clear()` → `Result.AddResultRow(true, count, Message)` |
| `SetActionFailed` | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:299-313` | 兩個交易各 `Rollback()` → `Clear()` → `AddResultRow(false, count, Message)` |

寫入位置是 `BasicModelVDB.Utility.Result`(無原始碼，從呼叫端反推)，也就是回傳給 Control 層的結果集。

新世代不用這兩支:`BasicEVAPO` 直接在最外層 `try/catch/finally` 裡 `Commit` / `Rollback` 並自己 `AddResultRow`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:199-218`);`BaseEVADaoPO` / `BaseMultiRowEVADaoPO` 則是 `throw new ApplicationException(...)` 讓 DLL 外層去接(例如 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:176-176`)。 **三種錯誤回報風格並存。**

### 3.8 事件掛點

舊世代每個動作前後各一個事件，型別 `PrepareSQLEventHandler`(`Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:11-11`)，宣告在 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:37-94`(Before 15 個)與 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:100-157`(After 15 個);觸發器都是三行 null-check(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:2045-2199`)。新世代同名事件改吃 `xEVAEventArgs`(無原始碼，從呼叫端反推)。 `CASM001_PO` 在建構子一次訂 12 個(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:40-60`)，handler 在 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77-153` 與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:569-630`。

| 掛點 | 何時觸發 | 拿得到什麼 | 能改什麼 | 不能做什麼 |
|---|---|---|---|---|
| `BeforeAdd` | INSERT 指令組好、**參數還沒綁**之前;主檔一次 + 每個明細表各一次 | `args.ModelVDB` / `args.TableName` / `args.DbCmd` / `args.DbTran` / `args.DbTranPTPF` | 改 model 欄位值(會被後續參數綁定吃進去)、換掉 `args.DbCmd`、`args.Cancel = true` 整段跳過 | 不能假設只跑一次;不能自己 commit |
| `AfterGetMaintainData` | 主檔 / 明細查完、資料已進 model 之後 | 同上 | 往 model 補掛額外資料表 | 不能改 `DbCmd`(已執行完) |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject` | 對應 UPDATE / DELETE 成功、交易**尚未** commit | 同上;`args.DbTran` 還活著，可在同一交易內再下 SQL | 寫稽核軌跡、`throw` 讓整筆回滾 | 不能自己 commit / rollback |

`CASM001_PO` 三個實際用法很有代表性:

- **`BeforeAdd` 改資料**:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:88-95` 在 do-while 裡取流水號 `genSrNo.GetPR_NO()`，用 `IsExistByData` 檢查撞號就重取，接著 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:98-101` 把號碼回填到所有明細 row。這只有在參數綁定之前做才有效。

- **`BeforeSelect` 換 SQL**:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:105-117` 判斷 `args.TableName == this.MasterTable.dbTableName` 之後把 `args.DbCmd` 整個換成自組的查詢;`BeforeGetMaintainData` 則用 `if/else` 分流主檔與明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:119-139`)。

- **`After*` 用 throw 中止**:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:576-630` 七處都是 `if (!SrNoCommentProcessor.AddCommentHistory(...)) throw new ApplicationException("");` —— 拋例外是 After 掛點唯一能否決整筆交易的手段。

每個 handler 第一行都是 `if (args.TableName != this.MasterTable.dbTableName) return;`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:571-571`)，因為事件會對主檔 + 每個明細表各觸發一次。

### 3.8.1 ⚠ 「覆核完資料就生效」不是通則

寫模組知識庫時發現,**同一套四眼引擎底下,資料實際生效的時機每個模組不一樣**, 而且差異大到會影響判斷。兩個已查證的極端:

| 模組 | 覆核通過之後 | 資料何時真的變 |
|---|---|---|
| `BBS` | `AfterVerify` / `AfterApprove` 的主體**只有一行跳號紀錄,零業務 SQL** | **輸入當下就改了**。四眼只留軌跡,不把關資料(`modules/bbs.md §4`) |
| `BMS` | 覆核通過,本表**仍然沒變** | 要等 OFD 的生效批次 `OFDB003` 跑,由版控外的 SP 回寫並蓋 `CHG_UPD_DTTM`(`modules/bms.md §2.1`) |

**所以看到一支畫面有四眼,不能假設「覆核前資料還沒動」。** 要確認,只有一條路:讀該畫面 PO 的 `Before*` 與 `After*` handler,看業務 SQL 落在哪一段。

### 3.9 單筆 vs 多筆

| 面向 | 單筆(`BasicEVAPO` / `BaseEVADaoPO`) | 多筆(`MultiRowEVAPO` / `BaseMultiRowEVADaoPO`) |
|---|---|---|
| 主檔宣告 | `TableMapping MasterTable` 單一;`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:28-28` | `List<TableMapping> MasterTable`;`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:20-20` |
| 明細 | `List<TableMapping> DetailTable`;`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:29-29` | **沒有明細概念** |
| 筆數限制 | Add 時強制主檔恰好 1 筆，否則丟例外;`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:194-196` | 無此限制，整張表逐筆跑 |
| 重複檢查 | `IsExistByData`(table PK) | 多一支 `IsExistByMasterPK`(自定 `MasterPKey`);`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1465-1487` |
| 樂觀鎖 | `IsChangedByData` 原封不動 | 同一支，但依 `RemovePK` 把部分 PK 條件從 SQL 字串 `Replace` 掉;`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1495-1498` |
| 複製 | `CopyDetail`(複製明細、主檔只更 EVA);`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:155-227` | `Copy`(整批複製主檔);`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:49-175` |
| 額外欄位 | — | `CopyPKey`:複製時要被換掉的 PK;`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:21-24` |

多筆版的 `Copy` 還有一招:把 `xEVAStringHelper.UpdateString` 產生的 SQL 拿去字串 `Replace`，把 `= :PK` 換成 `<> :PK`，一次更新「同批但非本筆」的所有 row(`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:105-110`)。這也順帶證實新世代走的是 Oracle 的 `:` 綁定語法。

### 3.10 `STATUS` 的值域(反推)

`STATUS` 的合法值由 `EVAStatusCode`(無原始碼，從呼叫端反推)這組字串常數定義。從全庫 `EVAStatusCode.<X>` 的使用反推出 **12 個**:

| 常數 | 出現次數 | 語意(反推) |
|---|---|---|
| `EntryAdd` / `EntryModify` / `EntryDelete` / `EntryUndoDelete` | 各 39 | 輸入完成、等待驗證 |
| `VerifyAdd` / `VerifyModify` / `VerifyDelete` / `VerifyUndoDelete` | `VerifyDelete` 83、其餘各 39 | 驗證完成、等待覆核 |
| `ApproveAdd` / `ApproveModify` / `ApproveDelete` / `ApproveUndoDelete` | 19 / 18 / 13 / 3 | 已覆核(正式生效) |

它們是**字串**不是 enum —— `Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs:20-34` 拿 `string Status` 直接跟常數做 `==` 比較; 同檔 `Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs:41-61` 有一個吃 `DataRow` 的多載，行為一樣。三段式的分組用法看 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:177-180`(待驗證清單只收 4 個 `Entry*`)與 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:181-195`(待覆核只收 4 個 `Verify*`)。

實際字面值查不到(常數在 DLL)。全庫 SQL 字串裡出現的 `STATUS = '<x>'` 字面量掃出來是 `'0'`~`'6'`、`'8'`、`'9'`(以 `'1'` 97 次、`'0'` 83 次最多)。**假設**這些單字元就是 `EVAStatusCode` 的實際值 —— 依據是位數吻合(12 個值放得進單字元)且這些比較都出現在 EVA 相關查詢裡。無法從原始碼確認對應關係;要確定得反編譯 `Vendor.Product.Utility.MappingCode` 或直接查資料庫。

`EVAActionCode`(同樣無原始碼)只看到 `Entry` / `Verify` / `Approve` / `Resend` 四個值，用途是待辦事項查詢的動作別(`Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:166-175`)。

### 3.11 本章發現的缺陷

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TA_PO`(2,106 行)唯一的兩個子類宣告都已被註解掉 | 該檔沒有任何活的呼叫端，但仍被編譯進 DLL；加上它參數綁定全被註解，實際上已不可執行 | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs:18-18` | 高 |
| `Basic4EyesPO.cs` 4,257 行(含 `MultiRow4EyesPO`)零繼承零實例化，只被 csproj 編進來 | 死碼躺在核心目錄，維護者會誤以為四眼雙表是現行架構而照著改 | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:130-130` | 高 |
| `MultiRow4EyesPO` 與 `MultiRowEVAPO` 非空白行相似度 0.878，是複製貼上的分身 | 任何修正都要記得改兩份;實際只有一份被用到，另一份持續漂移 | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2419-4257` | 中 |
| `TA_PO` 的參數綁定**全部被註解掉**:`SetPKeyParameter`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:71-74`)、`SetDataParameter`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:95-100`)、`SetBasicParameter`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:110-136`)、`SetDetailPKeyParameter`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:208-211`)、`SetDetailDataParameter`(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:232-237`)、`SetBasicParameter`(明細版)`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:248-274` —— 外殼與 `switch` 分派完整保留，但一個參數都不綁 | SQL 裡的 `@dataid` / `@Status` / `@PK` 全是未綁定變數，執行必爆;`TA_PO` 的 `EVA` / `Add` / `Update` / `ApproveDelete` 事實上無法運作 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:34-276` | 高 |
| 上一列被註解的區塊裡，`@dataid` 一處用 `OracleDbType.String`、其餘全用 `DbType.String` | 就算日後解除註解也編不過;顯示這段程式在 SQL Server 轉 Oracle 途中被放棄 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:252-259` | 低 |
| `EVAStringHelper.SetEVAParameters` 整支 13 行 `AddInParameter` 被註解，方法留成空殼 | 舊世代走這支的路徑都不會綁 EVA 13 欄;方法名與 XML 註解仍宣稱有效 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:35-50` | 高 |
| `TableHelper` 的參數綁定同樣全註解:`SetPrimaryKeyParameter`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1000-1007`)、`SetAllColumnsParameter` 只剩 `Trace.WriteLine`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1015-1026`)、`SetIsChangedParameter`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1055-1059`)、含 schema 版的 `SetPrimaryKeyParameter`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1082-1092`)、`SetQueryConditionParameter`(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1183-1196`) | 整個 `SQLHelper` 版本的 `TableHelper` 無法真正綁參數 —— 舊世代 PO 全數受影響 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1000-1196` | 高 |
| `SetNoPKColumnsParameter`:綁定迴圈被註解，底下的 `cmd.Parameters.RemoveAt("@"+PK)` 卻沒註解 | 對空的 Parameters 集合 `RemoveAt`，一叫就丟 `IndexOutOfRangeException` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1034-1046` | 中 |
| `MultiRowEVAPO.IsExistByMasterPK` 組出帶 `@col` 的 SQL，綁定迴圈整段註解 | 「多筆主鍵是否已存在」的檢查永遠無法成功執行 | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1465-1487` | 中 |
| `TA_PO.GetDBType`:`if` 與 `else` 兩條分支跑一模一樣的轉型，`else` 再包一層 `catch { /* Do Nothing */ }` | 轉型失敗時靜默吞掉，回傳 `DbType` 預設值 `AnsiString`;數值 / 日期會被當字串綁 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:2057-2080` | 中 |
| `TableHelper.GetNewDataFlag()` 回傳 `Encoding.Unicode.GetBytes(TimeSpan.TicksPerMillisecond)`，而 `TicksPerMillisecond` 是常數 10000 | 名為「取得新的 DataFlag 值」卻永遠回同一組 bytes;若被接上樂觀鎖等於全面失效。目前**零呼叫端**，屬未爆彈 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1168-1172` | 中 |
| `BasicEVAPO.Add` / `Update` 的 `catch` 直接 `tran.Rollback()`，但 `tran` 在 `try` 內才賦值;`finally` 也無條件 `cn.Close()` | 連線開失敗(DB 不通)時，真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:204-229` | 高 |
| `BasicEVAPO.Update`:`util` 在主檔迴圈內才 new，卻在明細區段與方法尾端無條件使用 | 主檔 0 筆或 `arg.Cancel = true` 時整支 `NullReferenceException` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:387-547` | 高 |
| `BaseMultiRowEVADaoPO.Copy`:只擋「兩個都 null」，卻直接讀 `dtAdded.Rows.Count`;`util` 也只在 `dtAdded` 分支賦值 | 只有修改沒有新增(合法情境)直接 `NullReferenceException` | `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:49-175` | 高 |
| `BasicEVAPO.Add` 明細迴圈:`i = ExecuteNonQuery(...)` 覆寫主檔的 `i`，且**沒有** `i != 1` 檢查(主檔有) | 明細 INSERT 影響 0 筆不會被發現，交易照樣 commit;回傳值變成最後一筆明細的影響數 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:294-317` | 高 |
| `BasicEVAPO.Update` 三個明細區段(刪 / 增 / 改)同樣沒有檢查 `i` | 同上;明細異動靜默失敗 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:446-541` | 高 |
| `CASM001_PO` 七處 `throw new ApplicationException("")` —— 空訊息 | 上層把 `ex.Message` 直接塞進結果集(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:209-209`)，使用者看到空白錯誤;沒有 log 就無從追 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:576-630` | 中 |
| `CASM001_PO_BeforeAdd` 的 `do { ... } while (IsExistByData(...))` 取號重試沒有次數上限 | 撞號情境(或 `IsExistByData` 恆真)變成無窮迴圈，卡住整條 WCF 執行緒 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:88-95` | 中 |
| `CASM001_PO_BeforeAdd` 第一行 new 了 `EVAUtility util` 卻從未使用(建構子還會產生一顆 Guid) | 死碼 + 每次新增多一次無謂配置;讀者會誤以為這裡有 EVA 處理 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:83-83` | 低 |
| `LogType.Update` 與 `LogType.UnDelete` 都是 `"U"` | 兩種動作在 log 上無法區分 | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:25-53` | 中 |
| `PrepareSQLEventArgs` 實作 `IDisposable`，`Dispose()` 卻是空的(連呼叫自己的那行也被註解) | 全庫大量 `using (PrepareSQLEventArgs ...)` 形同裝飾;內含的 `DbCommand` 不會被釋放 | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:267-271` | 中 |
| `TA_PO.EVA` 單表版對主檔 row 呼叫 `SetDetailParameter` 而非 `SetParameter` | 走進明細的 `DetailType` 分派邏輯，語意錯位(目前因參數全註解而看不出症狀) | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:488-490` | 中 |
| `TA_PO.EVA` 開頭「明細資料已被您異動」的前置檢查整段被註解，訊息字串還留著 | 少一道併發保護，且誤導讀者以為有檢查 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:410-414` | 中 |
| `TA_PO.EVA` 的 `catch` 先 `SetActionFailed`(已 rollback 並寫入失敗結果)再 `CommonExceptionBlocker.HandleBusinessException(ex)` 往上丟 | 同一錯誤被回報兩次;上層行為取決於 `HandleBusinessException` 是否 rethrow | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:552-557` | 中 |
| `Basic4EyesPO` 的 `OnBeforeWriteToEdit` / `OnBeforeWriteToReal` 沒有對應的 After | 雙表搬移無法掛後置稽核 | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2301-2310` | 低 |
| 三套狀態列舉並存且互不對應:`PrepareSQLStatus`(14 值)、`xEVAStatus`(DLL)、`EVAType`(10 值) | 讀 code 得先判斷在哪一世代;新舊混用的 PO 很容易對錯 | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:10-10` | 中 |

## 4. 資料存取與 SQL

這一節回答三個實務問題:改一張表的欄位要動哪裡、SQL 是誰組的、參數化到底做了沒。結論先講:**INSERT / UPDATE 的欄位清單來自資料庫的 table schema，不是 SQL 字串也不是 `string[] datacolumn`** —— 但 SELECT 條件那半邊幾乎全是字串串接。

### 4.1 `xTableMapping` / `TableMapping`

`TableMapping` 是一個兩欄位的容器:`dbTableName`(資料庫實體表名)與 `vdbTableName` (ModelVDB 裡 DataTable 的名字)。有原始碼的那份在 `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:55-79`; `xTableMapping`(無原始碼，從呼叫端反推)是 DLL 裡的同名同結構替身,屬性名一模一樣。

兩種寫法就是兩個世代:

|  | 舊世代 `TableMapping` | 新世代 `xTableMapping` |
|---|---|---|
| 定義位置 | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:55-79` | DLL(無原始碼，從呼叫端反推) |
| 全庫 `new` 次數 | 121 | 700 |
| `MasterTable = new ...` | 75 | 290 |
| `MasterTable.Add(new ...)` | 14 | 62 |
| `DetailTable.Add(new ...)` | 23 | 284 |
| 搭配的事件參數 | `PrepareSQLEventArgs` | `xEVAEventArgs` |

(計數用 `grep -rho` 對 `Dev/` 下所有 `.cs`;與規格書給的 575:119 略有出入，以本次實測為準。)

宣告方式取決於單筆或多筆:

| 基底 | `MasterTable` 型別 | `DetailTable` 型別 | 錨點 |
|---|---|---|---|
| `BasicEVAPO` | 單一 `TableMapping` | `List<TableMapping>` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:28-29` |
| `Basic4EyesPO` | 單一 `TableMapping` | `List<TableMapping>` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:32-33` |
| `MultiRowEVAPO` | `List<TableMapping>` | 無 | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:20-25` |
| `BaseEVADaoPO` | 單一 `xTableMapping`(繼承自 DLL) | `List<xTableMapping>`(繼承自 DLL) | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:161-196` |
| `BaseMultiRowEVADaoPO` | `List<xTableMapping>`(繼承自 DLL) | 無 | `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:54-54` |

PO 在建構子裡填,例如 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:46-47`: `MasterTable = new xTableMapping("CRM003A", "CRM003A")`、 `DetailTable.Add(new xTableMapping("CAS003A", "CAS003A"))`。兩個名字給同一個值是常態(VDB DataTable 直接用實體表名命名)。

誰讀它:

- 決定要從 ModelVDB 的哪張 DataTable 取資料 —— `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:250-250`、 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:161-161` 用的是 `vdbTableName`。

- 決定 SQL 要打哪張實體表 —— `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:253-254`、 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:205-206` 用的是 `dbTableName`。

- 事件裡分流主檔 / 明細 —— PO 端一律拿 `args.TableName` 跟 `this.MasterTable.dbTableName` 比對,例如 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:111-111`、`:295-295`。

- 明細迴圈直接 `foreach` 這個 List —— `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:281-281`、 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:194-194`。

### 4.2 SQL 怎麼組 —— INSERT / UPDATE 的欄位清單到底從哪來

**分成兩半，兩半的答案不一樣。**

**(1) 異動類(INSERT / UPDATE / DELETE / 存在檢查 / 異動檢查):PO 完全不寫 SQL。** `TableHelper` 在執行時去資料庫撈 schema，再依 schema 生出全欄位語句:

| 產生器 | 錨點 | 欄位清單來源 | 排除 |
|---|---|---|---|
| `GetTableSchema` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:467-478` | 對資料庫下 `SELECT * FROM <table> WHERE 1=2` 再 `FillSchema` | — |
| `GetInsertString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:486-513` | schema 的**全部**欄位 | `dataid`(另外寫在最前面)、`DataFlag`、`AutoIncrement` 欄 |
| `GetUpdateString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:521-542` | 同上;`WHERE` 由 schema 的 PK 迴圈串出 | 同上 |
| `GetDeleteString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:550-564` | 只有 PK | — |
| `GetIsExistString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:950-966` | 只有 PK | — |
| `GetIsChangedString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:974-989` | `DataFlag` + PK | — |

呼叫端把它接到 `db.GetSqlStringCommand(...)`: `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:253-254`(Add)、 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:396-397`(Update)、 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:449-450`(明細 Delete); 新世代同理但走 DLL 的 `xTableHelper.GetInsertString` / `xEVAStringHelper.UpdateString`(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:169-170`、 `:205-206`)。

**所以加一個欄位到表裡:**

| 要做什麼 | 為什麼 |
|---|---|
| DB 加欄位 | INSERT / UPDATE 語句自動就會帶到它(schema 驅動) |
| typed DataSet(`*Model.Designer.cs`)也要有這個欄位 | 綁參數的是 `SetAllColumnsParameter`，它跑的是**DataRow 的 Columns**(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1015-1026`);少了就會出現「SQL 有 `:NEWCOL` 但沒人綁」→ `ORA-01008` |
| `string[] datacolumn` | **不用管** —— 只有已死的 `TA_PO` 在用(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:780-841`) |
| PO 裡的 `BuildMasterSQLString` | **要手動加** —— SELECT 那半邊是手寫的(見下) |

換句話說:**寫入端 schema 驅動(自動)、讀取端手寫 SQL(不自動)**。漏改的症狀是「新增改成功了，但查回來畫面上永遠是空的」。

**(2) 查詢類(Select / GetMaintainData / GetToDoData):PO 自己手寫 SQL 字串。** `CASM001_PO` 是標準寫法:

| 方法 | 錨點 | 內容 |
|---|---|---|
| `BuildMasterSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:164-281` | 手寫 `SELECT` 欄位清單 + `LEFT JOIN` |
| `BuildDetailSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:290-359` | 同上，用 `if (strTableName == this.DetailTable[0].dbTableName)` 分流 |

固定套路是四段:

1. 手寫業務欄位清單(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:170-212`)。

2. 接 `xEVAStringHelper.AllEVAColumnsForSelect("<表名>")` 補上 EVA 欄位 (`:213-213`、明細在 `:320-320`)。有原始碼的同名版本在 `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:84-104`，一次補 14 欄(13 個 EVA + `DataFlag`)。全庫 `xEVAStringHelper` 版用 391 次、 `EVAStringHelper` 版用 98 次。

3. `FROM` / `JOIN` / `WHERE 1=1` 之後逐條 `if (model.Utility.Parameters.Rows.Contains(...))` 串查詢條件(`:227-266`)。

4. ToDo 查詢再接 `xTableHelper.AppendToDoString(...)`，程式碼旁邊註明「此段不可修改」 (`:269-273`)。

事件負責把組好的字串塞回去:`args.DbCmd = dbProduct.GetSqlStringCommand(strSQL);` (`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:113-114`、`:127-128`、`:135-136`、`:149-150`)。

### 4.3 參數化 —— 做了一半，另一半是字串串接

**做對的地方**:`EVAStringHelper.AddParam` (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:228-337`)是唯一一條完整、 Oracle 型別正確的參數化路徑 —— 依 schema 判斷 `OracleDbType.Date` / `Decimal` / `Int32` / `Varchar2` 再 `AddInParameter`(`:317-331`)，還處理 `_ST` / `_END` 區間參數的命名慣例(`:252-255`)。

**沒做的地方(多數)**:

| 位置 | 錨點 | 狀況 |
|---|---|---|
| `TA_PO.SetParameter` 一整族 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:34-276` | 6 個方法的 `AddInParameter` 全被註解，外殼與 `switch` 還在 |
| `EVAStringHelper.SetEVAParameters` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:35-50` | 13 行全註解，方法變空殼 |
| `TableHelper.SetPrimaryKeyParameter` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1000-1007` | 迴圈跑空 |
| `TableHelper.SetAllColumnsParameter` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1015-1026` | 只剩 `Trace.WriteLine`，綁定被註解 |
| `TableHelper.SetIsChangedParameter` / `SetIsExistsParameter` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1055-1070` | 同上 |
| 使用 schema 的那組多載 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1082-1161` | 同上 |
| `TableHelper.SetQueryConditionParameter` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1183-1196` | 同上 |

新世代的 `xTableHelper.SetAllColumnsParameter` / `SetPrimaryKeyParameter` / `xEVAStringHelper.SetEVAParameters`(無原始碼，從呼叫端反推)在 DLL 裡，從 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:182-184` 與 `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:118-120` 的用法看，它們是真的有在綁 —— 也只有這條路徑撐得起現行系統。

**使用者輸入直接串進 SQL —— 有，而且是主流做法:**

| 位置 | 錨點 | 串的是什麼 |
|---|---|---|
| `CASM001_PO.BuildMasterSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:235-264` | 5 處 `"'" + Row.Value + "'"`，`ID_NO` / `PR_NAME` / `PR_NO` 都是畫面輸入 |
| `CASM001_PO.BuildDetailSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:341-351` | 2 處，同樣寫法 |
| `CASM001_PO` 的四支查詢方法 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:375-375`、`:405-405`、`:438-438`、`:467-467`、`:503-503` | 參數直接進 `WHERE ... = '<值>'` |
| `TableHelper.AppendConditionString` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:776-814` | 全部型別分支都串字串;`:786-786` 還留著被註解掉的參數化版本 |
| `TableHelper.AppendToDoString`(兩份) | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:739-743` 與 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:175-179` | 登入者 ID / 功能代號 / 動作別直接串進 TVF 參數 |

唯一做跳脫的是 `EVAStringHelper.AddParam` 的純字串多載 (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:346-378`) —— 它會 `strValue.Replace("'", "''")`(`:368-368`、`:372-372`)，但 `IN` / `NotIN` 分支 (`:369-370`)是原封不動塞進括號，跳脫直接繞過。

風險評估要打折的地方:這些值來自 WinForms 內網用戶端與登入 session，不是公開端點; 但「內部使用者輸入一個帶單引號的公司名就讓查詢語法壞掉」這件事仍然天天會發生。

### 4.4 `PrepareSQL` 與 `PrepareSQLEventArgs`

`PrepareSQLEventArgs`(`Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:118-263`) 是舊世代事件的載體，本質是一個「把整個執行環境交給 PO 的信封」:

| 屬性 | 錨點 | 用途 |
|---|---|---|
| `DbConn` / `DbTran` | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:120-138` | 業務庫的連線與交易 |
| `DbConnPTPF` / `DbTranPTPF` | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:140-158` | 平台庫(待辦事項)的連線與交易 |
| `DbCmd` | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:160-168` | **可讀可寫** —— PO 換掉它就等於換掉要執行的 SQL |
| `Status` | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:170-179` | `PrepareSQLStatus`，告訴 handler 是哪個動作觸發的 |
| `ModelVDB` / `TableName` | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:181-199` | 資料與「現在在處理哪張表」 |
| `Cancel`(繼承 `CancelEventArgs`) | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:118-118` | 設 `true` 讓引擎跳過這一段 |

四個建構子分別對應「只取消」、「無交易」、「單交易」、「雙交易」四種情境 (`Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:201-263`)。新世代等價物是 `xEVAEventArgs`(無原始碼，從呼叫端反推)，介面看得出來一致 —— `args.DbCmd` / `args.ModelVDB` / `args.TableName` / `args.DbTran` / `args.DbTranPTPF` / `args.Cancel`(見 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:105-153` 與 `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:81-92`)。

同檔還有一個 `PrepareSQL` 類別 (`Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:80-114`)，把 `TableMapping` + SQL 字串 + `DbCommand` 包成一組。**全庫零使用** —— 找不到任何 `new PrepareSQL(`。

### 4.5 交易邊界

三種模式並存，取決於 PO 走哪一代:

| 模式 | 誰開 | 誰關 | 失敗怎麼辦 | 錨點 |
|---|---|---|---|---|
| 舊世代自管 | `BasicEVAPO.Add/Update/Delete` 自己 `CreateConnection` → `Open` → `BeginTransaction`，兩個庫各一組 | 同一個方法的 `try` 尾端 `Commit`、`catch` 裡 `Rollback`、`finally` 裡 `Close` + `Dispose` | `catch (ApplicationException)` 與 `catch (Exception)` 各 rollback 一次並寫失敗結果集 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:177-232` |
| 舊世代外部傳入 | 呼叫端 | 呼叫端(方法註解明寫「呼叫本 Method 者,請記得寫 Try catch,Commit 與 Rollback 並 AddResultRow」) | 直接 `throw ApplicationException`，由呼叫端收 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:233-244` |
| 新世代 | DLL 裡的 `BaseEVADao` | DLL | PO 只負責 `throw`，例如 `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:176-176`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582-582` | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:143-146` |

`TA_PO` 那套則是把 `Commit` / `Rollback` 藏在 `SetActionSuccess` / `SetActionFailed` 裡(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:283-313`)。

要注意的邊界性質:

- **兩個庫兩個交易，沒有分散式交易。** 業務庫 commit 成功、待辦庫 commit 失敗(或反之) 就會不一致。`SetActionSuccess` 是先 commit 業務庫再 commit 待辦庫 (`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:285-292`);`BasicEVAPO.Add` 則相反，先 `tranptpf.Commit()` 再 `tran.Commit()`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:199-200`)。 **順序在兩個世代之間是相反的**，代表沒有人真的想過部分失敗要怎麼收。

- **事件 handler 拿得到 `DbTran` 但不該自己 commit** —— PO 端的正確做法是 `throw` 讓外層 rollback(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:576-584`)。

- **`GetTableSchema` 在交易外另開連線** —— 它自己 `db.CreateConnection()` (`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:472-472`)且用完沒有 `Dispose`。每次 Add / Update / IsExist / IsChanged 都會呼叫一次，等於每個 EVA 動作多好幾趟往返。

### 4.6 Oracle 特有的部分 —— 到底支不支援 SQL Server?

**答案:執行期是 Oracle-only。SQL Server 只剩兩種殘留:一是型別轉換的小工具，二是還沒清乾淨的 T-SQL 語法。**

證據:

| 觀察 | 錨點 | 說明 |
|---|---|---|
| 兩支薄殼建構子把 provider 寫死 | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:22-26`、`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:27-31` | `base("TA", DbServerType.Oracle)` |
| 屬性標註 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:36-36` | 全庫 `[PODbType(DbServerType.Oracle)]` 765 次，`DbServerType.MSSql` 只有 12 次 |
| `GetTableSchema` 硬寫 `OracleDataAdapter` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:469-469` | 就算傳進來的 `Database` 是 MSSql，schema 也用 Oracle adapter 撈 |
| 綁定符號 | `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:238-250`、`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:105-110` | 新世代一律 `:param` |
| `System.Data.SqlClient` 的實際用途 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:2059-2059`、`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:433-433` | 只是 `new SqlParameter()` 借它的 `DbType` 做 `TypeConverter`;沒有任何 `SqlConnection` / `SqlCommand` |
| Ctl 層的 SQL Server 分支 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:140-148` | `CustomTransferSQLModelToView` / `CustomTransferViewToSQLModel` 直接 `throw new NotImplementedException()` |

最後這條可以量化:全庫 `*_Ctl.cs` 裡 `CustomTransferSQLModelToView` 共 755 個實作，其中 **666 個(88%)是 `NotImplementedException`**。也就是框架留了雙資料庫的介面，但 TA 只把 Oracle 那一半填完。剩下的 89 個集中在 `Dev/ATLAS.EC/Source/PO/PO.EC/`，那裡是唯一還維持 `MSSQL/`(30 檔)與 `Oracle/`(48 檔)雙目錄並存的模組; `MSSQL/` 下的舊 PO 類別多半已被整支註解掉(例如 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs:18-18`)。

其他 Oracle 面向:

- **`sysdate` / `to_date`**:全庫 `.cs` 內嵌 SQL 出現 `sysdate` 446 次、`to_date(` 429 次。時間基準是資料庫伺服器，不是 AP 端。

- **序號**:`*_SE` 之類的 Oracle sequence **完全沒有** —— 全庫 `.cs` 內 `NEXTVAL` 出現 0 次。流水號一律走 `SerialNo` 這支表驅動的配號器 (`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:579-582`)， PO 端再用 do-while 重試處理撞號(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:88-95`)。

- **T-SQL 殘留**:`[]` 方括號識別字散布在 `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:59-73`、`:88-101`、`:117-129` 與 `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:435-447`; `CONVERT(NVARCHAR, ...)` 在 `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:794-794`; `SET IDENTITY_INSERT` 在 `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1280-1284`; `dbo.f_GetToDoData(...)` 這個 `dbo.` schema 的 TVF **連 Oracle 版的 helper 裡都還在** (`Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:175-175`)。

- **金額欄位沒有用 float / double**:typed DataSet 裡 `AMT` / `AMOUNT` / `PRICE` / `NAV` / `FEE` 相關屬性宣告為 `decimal` 的有 7,932 個、宣告為 `double` 的 0 個; 程式面 `Convert.ToDecimal` 3,029 次 vs `Convert.ToDouble` 18 次。這一點是乾淨的。

### 4.7 本章發現的缺陷

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 同名類別 `TableHelper` / `EVAStringHelper` 同時存在於 `...ServerUtility.SQLHelper`(T-SQL 版)與 `...ServerUtility.OracleHelper`(Oracle 版)兩個 namespace，另有 DLL 的 `xTableHelper` / `xEVAStringHelper` 第三份 | 呼叫端寫 `TableHelper.AppendToDoString(...)` 綁到哪一份，**完全取決於檔案頂端 `using` 的是哪個 namespace**(387 檔 using SQLHelper、7 檔 using OracleHelper)。改錯一個 using 就換掉整支 SQL 方言，編譯不會有任何警告 | `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:15-20` | 高 |
| Oracle 版的 `AppendToDoString` 仍呼叫 SQL Server 的 `dbo.f_GetToDoData(...)` TVF | 名為 Oracle helper 卻產 T-SQL;要嘛這條路徑沒被走到(死碼)，要嘛待辦查詢有隱藏故障 | `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:175-175` | 高 |
| `AppendConditionString` 只處理 `decimal` / `string` / `int` / `DateTime` 四種型別，其他型別**靜默跳過**不產生任何條件 | 查詢條件被無聲丟棄 → 撈回全表。使用者只會覺得「篩選沒作用」，不會看到錯誤 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:784-812` | 高 |
| 同一支 `AppendConditionString` 內對 `decimal` 只支援 `Like` / `Equal`，其他 operator(`>` / `<` / `IN`)一樣靜默跳過 | 同上 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:791-797` | 高 |
| `AppendConditionString` 全程字串串接使用者輸入，且旁邊留著被註解掉的參數化版本 | SQL injection / 單引號炸語法;註解證明作者知道正確做法但放棄了 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:786-810` | 高 |
| `CASM001_PO` 的查詢條件與五支輔助查詢共 12 處把參數直接串進 `'...'` | 同上;這是全庫 PO 的通用寫法，不是單一檔案的問題 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:229-266` | 高 |
| `EVAStringHelper.AddParam`(純字串版)對 `Like` / `Equal` 有做 `''` 跳脫，但 `IN` / `NotIN` 分支原封不動塞入括號 | 跳脫被繞過;而且同一支方法內兩種安全等級並存，讀者會誤以為整支都安全 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:367-373` | 高 |
| `EVAStringHelper.AddParam`(參數化版)取 schema 失敗時 `catch { }` 空吞 | 之後所有欄位一律降級成 `OracleDbType.Varchar2`;數值 / 日期比對變字串比對，索引失效且結果可能錯 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:233-239` | 高 |
| `GetTableSchema` 每次呼叫都 `db.CreateConnection()` 且從未 `Dispose` | 連線物件只能等 GC 回收;而且每個 Add / Update / IsExist / IsChanged 都多一趟 `SELECT * WHERE 1=2` 往返 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:467-478` | 中 |
| `GetTableSchema` 硬寫 `new OracleDataAdapter()`，卻收一個可為 MSSql 的 `Database` 參數 | 12 處 `DbServerType.MSSql`(例如 `Dev/Common/Source/DataSource/PO.DataSource/MSSQL/BasicEC_PO.cs:29-29`、`Dev/ATLAS.SDM/Source/PO/PO.SDM/SDMB001_PO.cs:58-58`)一旦走到這裡就會拿錯 provider | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:469-469` | 中 |
| 755 個 `CustomTransferSQLModelToView` 中 666 個是 `NotImplementedException` | 雙資料庫抽象層是空的;維護者看到 `SQL` / `Oracle` 兩套 API 會誤判系統支援兩種 DB | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:140-148` | 中 |
| `FourEyesHelper.GetWriteToRealTable` 產 `SET IDENTITY_INSERT [table] ON/OFF` —— 純 T-SQL，而同一支方法用的 `GetTableSchema` 是 Oracle adapter | 同一條呼叫鏈裡混兩種方言，永遠不可能同時成立(目前因整個 `Basic4EyesPO` 是死碼而未爆) | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1280-1284` | 中 |
| `Basic4EyesPO` 呼叫 `GetRecoveryEditTable` 時，有一處傳 `tp.dbTableName + prefixEditTable`，而方法內部又自己加一次 `"_Edit"`;其餘三處傳的是不加前綴的表名 | 會組出 `<TABLE>_Edit_Edit`;四處呼叫兩種寫法，至少有一種是錯的 | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:3772-3772` | 中 |
| `PrepareSQL` 類別全庫零使用 | 死碼 | `Dev/Common/Source/Base/TA.DataAccess/PrepareSQLEventArgs.cs:80-114` | 低 |
| 業務庫與待辦庫兩個獨立交易，沒有分散式交易;且 commit 順序在兩個世代之間相反 | 部分 commit 會造成「資料進去了但沒有待辦」或「有待辦但資料沒進去」;沒有補償機制 | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:285-292` | 高 |
| `EVAStringHelper` 註解一路寫「13 個欄位」，但 `SelectString` 實際列 15 欄、`AllEVAColumnsForSelect` 的註解寫 15 欄卻列 14 欄 | 三處數字互相矛盾;照註解改欄位一定漏 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:51-104` | 低 |
| `TableHelper.GetDBType` 的 `else` 分支把原本的 `try/catch` 註解掉，只留一個 `Byte[]` 特判 | 未知型別現在會直接丟例外而不是靜默降級 —— 行為與 `TA_PO` 版本(`Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:2057-2080`，仍是空 catch)相反。同一個工具在兩個檔裡有兩種錯誤處理策略 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:431-457` | 中 |
| `TableHelper.SetNumberToZero` 把 `decimal` / `int` 欄的 NULL 全改成 0 之後呼叫 `ds.AcceptChanges()` | `AcceptChanges` 會清掉整個 DataSet 的 RowState，之後 `GetTableAdded` / `GetTableModified` 全部取不到東西。目前只有三支報表 PO 在用(例如 `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:72-72`)所以沒出事，一旦被用在維護畫面就會靜默不存檔 | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:1203-1223` | 中 |
| `CASM001_PO.GetCustType` / `GetDeptNo` 直接讀 `ds.Tables[...].Rows[0][...]` 沒有筆數檢查 | 查無資料時丟 `IndexOutOfRangeException`，被外層 `catch` 轉成 business exception，錯誤訊息與真因無關 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:461-521` | 中 |
| `CASM001_PO` 五支查詢方法 `catch` 之後照樣往下走並回傳 `-1` / `string.Empty` / `null` | 呼叫端無法區分「查無資料」與「查詢失敗」;`IsID_NOExsits` 回 `-1` 若被當成筆數判斷就會誤判為「存在」 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:369-389` | 中 |

## 5. typed DataSet 與 schema 真相

```text
[圖] typed DataSet 資料流:設計庫經 Devart 產 xsd,xsd 經 MSDataSetGenerator 產 Designer.cs,執行期寫入端自動讀取端手寫
圖中文字:設計期 / Oracle 設計庫 / ora01 / ATLASDB〔客戶特定〕 / Devart dotConnect / 設計期驅動,開發機要裝 / <代號>Model.xsd / 唯一 schema 真相 / <代號>View.xsd / 89.7% 與 Model 同構 / xsd 的三層:根 = 畫面代號,element = 實體表名,再下才是欄位 / DataSet 根 / = 畫面代號 / element / **= 實體表名** / 欄位 / msdata:Caption = 中文名 / minOccurs=0 / = 可為空 / 編譯期 / MSDataSetGenerator / 存檔即重生 / <代號>Model.Designer.cs / **手改會被覆寫** / <代號>ModelVDB.cs / 45 行薄包裝,加欄位不用動 / 執行期:寫入端自動、讀取端不自動 / TableHelper.GetTableSchema / SELECT * WHERE 1=2 取全欄 / INSERT / UPDATE / **欄位清單自動** / BuildMasterSQLString / **手寫,加欄位要自己加** / 漏改的症狀 / 存得進去,查不回來
```

*圖:圖 4 xsd 是唯一 schema 來源。加欄位時:DB 與 xsd 兩邊都要有(缺一報 ORA-01008),INSERT/UPDATE 的欄位清單自動,但 PO 手寫的查詢 SQL 要自己加——這是「存得進去查不回來」的成因。*

### 5.1 xsd 的三層結構

每支畫面兩份 xsd:`<代號>Model.xsd`(伺服器側)與 `<代號>View.xsd`(用戶端側)。兩份都是同一套 Visual Studio typed DataSet schema,結構固定三層:

| 層 | XML | 命名規則 | 例(`CASM001Model.xsd`) |
|---|---|---|---|
| 1 DataSet 根 | `<xs:element ... msdata:IsDataSet="true">` | **等於畫面代號 + `Model` / `View`** | `CASM001Model`(`:12`) |
| 2 DataTable | `<xs:element name="..." msprop:Generator_TableClassName="...">` | **等於實體表名**(或查詢結果集代稱) | `CAS003A`(`:15`)、`CRM003A`(`:56`) |
| 3 DataColumn | `<xs:element name="..." type="xs:...">` | 等於欄位名 | `PR_NO`(`:19`) |

第三層每個欄位帶三個關鍵屬性:

| 屬性 | 意義 | 例 |
|---|---|---|
| `msdata:Caption="潛在客戶序號"` | **中文名。全 repo 唯一的欄位中文對照來源** | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:19` |
| `type="xs:string"` / `xs:decimal` / `xs:dateTime` / `xs:base64Binary` | 型別。`base64Binary` 是 `DATAFLAG` 那種 RAW 欄位 | 同上 |
| `minOccurs="0"` | **可空**。沒有這個屬性就是 NOT NULL | `PR_NO` 沒有 → 必填 |

DataSet 尾端還有主鍵宣告(`<xs:unique msdata:PrimaryKey="true">`): `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:133-141` 宣告了 `CAS003A(PR_NO, STAFF_NAME)` 與 `CRM003A(PR_NO)`。全庫 2,190 支 xsd 裡 **987 支(45%)有 PK 宣告**,其餘 1,203 支沒有—— 沒宣告的多半是查詢結果集(§5.5),對它們談 PK 本來就沒意義。

### 5.2 `MSDataSetGenerator`:Designer.cs 怎麼來、手改會怎樣

csproj 用一組四行把 xsd 綁到產生器:

```
<None Include="CASM001Model.xsd">
  <SubType>Designer</SubType>
  <Generator>MSDataSetGenerator</Generator>
  <LastGenOutput>CASM001Model.Designer.cs</LastGenOutput>
</None>
```

`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:151-155` (UIEntity 側同樣位置:`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj:151-155`)。

產出的 `.Designer.cs` 反過來以 `DependentUpon` 掛回 xsd,並標 `AutoGen` / `DesignTime`: `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:83-87`。

三件必須知道的事:

1. **`MSDataSetGenerator` 是 Visual Studio 的單檔產生器,不是 MSBuild target。** `.Designer.cs` **已經 commit 進 repo**,`msbuild` 只是編譯它,不會重跑產生器。所以改了 xsd 卻沒在 VS 裡存檔觸發重生,build 會過但行為是舊的。

2. **`.Designer.cs` 非常大。** `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.Designer.cs` 與 `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.Designer.cs` 各 **5,375 行** —— 一支 142 行的 xsd 展開成 5,375 行。全庫 2,190 支 xsd 對應 2,145 支 Model/View Designer.cs。 (2,190 對 2,145 差 45,表示有 45 支 xsd 的 Designer 沒進版控或命名不合;細節未追。)

3. **手改 `.Designer.cs` 一定被蓋掉。** 下一個在 VS 裡碰過該 xsd 的人存檔,你的改動就消失, 而且因為檔案 5 千行、diff 一片紅,review 幾乎抓不到。**加欄位只能改 xsd。**

每支 xsd 旁邊還有 `.xsc` 與 `.xss`(全庫各 2,190 支,與 xsd 數量完全一致)—— VS DataSet 設計工具的版面與註解 sidecar,不影響編譯,但 `DependentUpon` 掛在 xsd 上 (`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:148-150` 與 `:156-158`),刪掉會讓設計工具重建。

### 5.3 `*ModelVDB.cs` / `*ViewVDB.cs`:45 行的薄包裝

每支 xsd 配一支手寫的 45 行左右包裝類別。以 CAS 為例:

| 檔 | 類別 | 基底 | 行數 |
|---|---|---|---|
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001ModelVDB.cs` | `CASM001ModelVDB` | `BasicTAModelVDB` | 45 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001ViewVDB.cs` | `CASM001ViewVDB` | `BasicTAViewVDB` | 42 |

裡面只有三件事:

| # | 做什麼 | ModelVDB 錨點 | ViewVDB 錨點 |
|---|---|---|---|
| 1 | 建構子 new 出 typed DataSet | `CASM001ModelVDB.cs:21-24` | `CASM001ViewVDB.cs:17-21` |
| 2 | 開一個 property 給外面拿(名字不一樣!) | `DataEntity`,`:29-33` | `UIView`,`:26-30` |
| 3 | `Dispose()` 轉呼叫 DataSet 的 Dispose | `:38-43` | `:35-40` |

兩個差異值得記:

- **property 名不對稱**:Model 側叫 `DataEntity`,View 側叫 `UIView`。所以 Control 層的轉換程式碼永遠長這樣: `TransferVDBHelper.TransferTable(view.UIView.CRM003A, model.DataEntity.CRM003A, base.TransferEVAColumn);` (`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:85`)。

- **只有 ViewVDB 標 `[Serializable()]` 並設 `RemotingFormat = Binary`** (`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001ViewVDB.cs:10` 與 `:20`); ModelVDB 兩者皆無(`CASM001ModelVDB.cs:14`)。理由見 §2.5。

**加欄位要不要動這兩支?不用。** 它們不列舉欄位,只持有整個 DataSet 物件; 欄位是 xsd → Designer.cs 產生出來的 property。**加欄位只改 xsd,重生 Designer,兩支包裝不動。** 反過來說,**新增一整張表到既有畫面**時也不用動——`view.UIView.<新表名>` 由 Designer 自動長出來, 要動的是 Control 層的 Transfer 方法(要多加一行 `TransferTable`)與 PO 的 `xTableMapping`。

### 5.4 Model 與 View 什麼時候同構、什麼時候不同構

先看 `CASM001` 這一對(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` 與 `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd`)。全欄位逐一比對的結果:

| 項目 | `CASM001Model.xsd` | `CASM001View.xsd` | 一致? |
|---|---|---|---|
| DataTable 集合 | `CAS003A`、`CRM003A` | `CRM003A`、`CAS003A` | 集合相同,**宣告順序相反** |
| `CRM003A` 欄位 | 69 | 69 | 完全相同(名稱、型別、Caption、`minOccurs`) |
| `CAS003A` 欄位 | 35 | 35 | 完全相同 |
| PK 宣告 | `:133-141` | `:133-141` | 相同,順序跟著表順序反過來 |
| 檔案行數 | 142 | 142 | 相同 |
| Designer.cs 行數 | 5,375 | 5,375 | 相同 |

**`CASM001` 是完全同構的**,差別只有 `<xs:element>` 的排列順序 (Model 先 `CAS003A`(`:15`)後 `CRM003A`(`:56`);View 先 `CRM003A`(`:15`)後 `CAS003A`(`:90`))。順序不影響行為,`TransferTable` 是按名字搬的。

再看全庫。把每支畫面的 `<代號>Model.xsd` 與 `<代號>View.xsd` 逐表逐欄比對,共 1,072 對:

| 分類 | 對數 | 佔比 | 意義 |
|---|---|---|---|
| 完全同構(表集合 + 每表欄位順序全同) | 962 | 89.7% | 預設狀態 |
| 只差欄位/表的排列順序 | 20 | 1.9% | 無害 |
| **表集合不同** | 60 | 5.6% | View 多出畫面專用結果集,或 Model 多出中繼表 |
| **同表但欄位不同** | 30 | 2.8% | **真正的轉換風險,見下** |

另外有 **5 支只有 Model 沒有 View**(`CMM_BFType`、`OFDM381`、`OFDR901A`、`OFD_OFDM019List`、`OFD_OFDM020List`) 與 **5 支只有 View 沒有 Model**(`CMM_BFTypeList`、`CMM_FUND_IDList`、`FileRuleInfo`、`OFDI701`、`OFDM287`)。看名字(`*List` 對 `*`)像是改名沒改乾淨,**這是假設**,依據是 `CMM_BFType` / `CMM_BFTypeList` 這種只差字尾的配對。

**不同構的 30 對,方向幾乎一面倒:View 多欄、Model 沒有。** 抽樣:

| 畫面 | 表 | View 多出來的欄位 |
|---|---|---|
| `BMSB901A` | `BMSB901` | `SEAL_STATUS_NM` |
| `CASR006` | `CASR006` | `ALLOT_FEE_RATE0` |
| `CLSI001` | `CLS001A` | `CUST_WILL_DESCRP`、`CUST_STYLE_DESCRP` |
| `CPMB001` | `CPM004A` | `DATA_TYPE`、`DATA_TYPE_NM` |
| `DSMR004` | `DSMR004_1` | `JAN_RATE0`…`DEC_RATE0`、`Q1_RATE0`…`Q4_RATE0`、`YY_RATE0`(17 欄) |
| `IPJM614_9i` | `OFD607A` | `LACKFLG` |
| `IPJI630_9i` | `IPJI630_Master` | **反向** —— Model 多 `BF_CHG_NO`,View 沒有 |

看得出規律:View 多出來的多半是 `*_NM` / `*_DESCRP`(代碼的中文說明)與 `*_RATE0`(格式化後的顯示值), 也就是**畫面計算欄位**。這在設計上合理——但風險是實際的:

> `TransferVDBHelper.TransferTable(view.UIView.X, model.DataEntity.X, ...)` 是按欄位名搬的。 View 有、Model 沒有的欄位,model→view 方向搬完就是空的,得靠 Control 或 UI 另外填。反過來 `IPJI630_9i` 那種 Model 有、View 沒有的欄位,view→model 方向永遠是 DB default, **使用者在畫面上改不到、也看不到**。

`IPJI630_9i` 的 `BF_CHG_NO` 屬於後者,是這 30 對裡唯一的反向案例,值得單獨追。

### 5.5 為什麼 xsd 是 repo 內唯一的 schema 來源

`DB/` 底下有五個資料夾:`Table` / `SP` / `Function` / `View` / `Trigger`。直覺會以為 `DB/Table/` 是 DDL 基準,**不是**。實測 158 支 `.sql`:

| 內容 | 檔數 |
|---|---|
| 含 `CREATE TABLE` | 58(涵蓋 52 個不重複表名) |
| 含 `ALTER TABLE` | 57 |
| 含 `INSERT INTO` | 15 |
| 檔名帶 `_rollback` | 11 |

對照掃描器實測的 **388 張實體表**(以 PO 的 `xTableMapping` 宣告者為準), `DB/Table/` 只覆蓋 52 張(13%),而且多半是後來新增的表,不是全庫基準。主檔 `CRM003A`、`CAS003A`、`OFD701` 這些核心表在 `DB/Table/` 裡**根本沒有 CREATE 腳本**。

所以現況是:

| 想知道 | 唯一來源 | 可信度 |
|---|---|---|
| 某表有哪些欄位 | `<代號>Model.xsd` | 中——只是「這支畫面用到的欄位」,不是表的全欄位 |
| 欄位中文名 | xsd 的 `msdata:Caption` | 中——實測只有 53% 的欄位有填 |
| 欄位可空 | xsd 的 `minOccurs="0"` | 低——反映的是 DataSet 約束,不保證等於 DB 約束 |
| 表的真實 DDL | **repo 內沒有** | — |

再加上掃描器的兩個實測數字,情況更明確:

- **388 張實體表裡 212 張(55%)完全沒有 xsd 欄位定義** —— 這些表只在 SQL 字串裡出現,沒有任何 typed 定義。

- 有定義的 176 張共 4,057 欄,**只有 53% 有中文名**,**只有 19% 的表帶四眼欄位**(四眼細節見 §3)。

還有一個容易誤導的數字:xsd 裡出現的 DataTable 名稱共 **1,618 個不是實體表**, 它們是查詢結果集的形狀。典型例子是報表:`Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` 宣告了 `CASR001`、`CASR001_3`、`CASR001_5`、`CASR001_6` 四張「表」, 名字是**畫面代號加序號**,DB 裡沒有這些物件——它們是 SP `S_TA_CASR001_GET` 回來的 refcursor 落地容器 (`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58` 與 `:67`)。 **看到 xsd 裡的表名不要直接當 DB 表查。**

### 5.6 `DB/Table/` 的變更腳本怎麼讀

158 支腳本沒有統一命名,但看得出三種慣例並存:

| 慣例 | 樣式 | 例 |
|---|---|---|
| A 票號開頭 | `<票號>_<動作><對象>[_序號].sql` | `DB/Table/11706_InsertOFD115A_1.sql`、`DB/Table/9000010311_update.sql` |
| B 動作開頭 | `<Alter\|Update\|Insert>_<對象>.sql` | `DB/Table/Alter_OFD094A.sql`、`DB/Table/Update_Column_map.sql` |
| C 日期 | `<YYYYMMDD>.sql` | `DB/Table/20221219.sql` |

**`_rollback` 是配對慣例**:同名加 `_rollback` 就是回退腳本。11 支 rollback,配對狀況:

| 正向 | 回退 |
|---|---|
| `DB/Table/11706_InsertOFD115A_1.sql` 等 9 支(同票號一整組) | `DB/Table/11706_rollback.sql`(**一支對多支**) |
| `DB/Table/9000010311_update.sql` | `DB/Table/9000010311_update_rollback.sql` |
| `DB/Table/Update_Column_map.sql` | `DB/Table/Update_Column_map_rollback.sql` |
| `DB/Table/update_ofd607.sql` | `DB/Table/update_ofd607_rollback.sql` |
| `DB/Table/update_OFD304.slq` | `DB/Table/update_OFD304_rollback.slq`(**副檔名打成 `.slq`**) |

讀 rollback 的正確姿勢:`DB/Table/11706_rollback.sql:1-4` 先給 before/after 驗證用的 `select count(*)`, 再接實際回退敘述。也就是**票號級的 rollback 是一整包,不是逐檔對應**—— 只跑其中一支正向腳本又想回退,得自己拆。

三個要注意的:

1. **`.slq` 副檔名**(`DB/Table/update_OFD304.slq` 與其 rollback)—— 任何 `*.sql` 的 glob 都會漏掉這兩支。

2. **腳本內容含具體資料值**,例如 `DB/Table/11706_InsertOFD907.sql:1-2` 直接 insert 特定 `BF_NO`(78821、120675…) 與經手人帳號 `janehuan`。這種腳本**不可重跑**,也不能當範本抄。標 **〔客戶特定〕**。

3. **schema 名寫死 `SW.`**:`DB/Table/Alter_OFD094A.sql:1` 是 `ALTER TABLE SW.OFD094A ADD ...`。逐站 schema 名可能不同,標 **〔客戶特定〕**。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| repo 內沒有完整 DDL;388 張實體表只有 52 張有 CREATE 腳本 | 無法從 repo 得知表的真實結構;上線前的 schema diff 只能靠現場 DB | `DB/Table/`(158 支)對照掃描器 388 表 | 高 |
| 388 張實體表裡 212 張(55%)沒有任何 xsd 欄位定義 | 這些表的欄位只存在於 SQL 字串,改動無型別保護 | 掃描器 `--table` 反查 | 高 |
| 30 對 Model/View 欄位不一致,絕大多數是 View 多出計算欄 | model→view 搬完該欄為空,靠 Control/UI 補;漏補就是畫面空白 | `Dev/ATLAS.DSM.Report/Source/Entity/ReportDataEntity.DSM/DSMR004Model.xsd` 對照 `Dev/ATLAS.DSM.Report/Source/Entity/ReportUIEntity.DSM/DSMR004View.xsd`(17 欄差) | 高 |
| `IPJI630_9i` 反向不一致:Model 有 `BF_CHG_NO`,View 沒有 | 使用者在畫面上改不到也看不到該欄,永遠是 DB default | `Dev/ATLAS.EC.Query/Source/Entity/QueryDataEntity.EC/IPJI630_9iModel.xsd` | 高 |
| `.Designer.cs` 已 commit 且不由 MSBuild 重生 | 改 xsd 沒在 VS 存檔觸發重生 → build 會過但行為是舊的 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:151-155` | 中 |
| 單支 Designer.cs 達 5,375 行 | 任何誤改都無法在 review 中辨識 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.Designer.cs` | 中 |
| xsd 欄位只有 53% 填了 `msdata:Caption` | 中文名反查有近一半失效 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:19`(有填)對照同檔 `DATAID`(未填) | 中 |
| xsd 裡 1,618 個 DataTable 名不是實體表 | 直接拿 xsd 表名去 DB 查會查不到 | `Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd`(`CASR001_3/_5/_6`) | 中 |
| 10 支 xsd 只有 Model 或只有 View | 該畫面的一側轉換無型別可用 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM381Model.xsd` 無對應 View;`Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI701View.xsd` 無對應 Model | 中 |
| 又一個層資料夾命名例外:`DataEntity.OFD9`(§2.6 表格之外) | 以 `DataEntity.<模組>` 為 pattern 的工具會漏 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM381Model.xsd` | 低 |
| 變更腳本副檔名打成 `.slq` | `*.sql` glob 漏檔,上版可能整支沒跑 | `DB/Table/update_OFD304.slq`、`DB/Table/update_OFD304_rollback.slq` | 中 |
| 變更腳本內含正式資料值與經手人帳號 | 不可重跑;誤跑會污染資料 | `DB/Table/11706_InsertOFD907.sql:1-2`〔客戶特定〕 | 中 |
| rollback 是票號級一整包,非逐檔對應 | 只跑部分正向腳本時無法精確回退 | `DB/Table/11706_rollback.sql:1-6` 對應 9 支正向腳本 | 低 |
| schema 名 `SW.` 寫死在腳本 | 換站要全域取代 | `DB/Table/Alter_OFD094A.sql:1`〔客戶特定〕 | 低 |

## 6. 畫面型別四種

四支對照組刻意選同一模組(CAS)、六層都齊,好比較:

| 型別 | 代號 | 主檔 | Ctl 錨點 |
|---|---|---|---|
| M 維護 | `CASM001` | `CRM003A` + 明細 `CAS003A` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs` |
| I 查詢 | `CASI001` | 見 §6.3 的警告 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs` |
| B 批次 | `CASB001` | 見 §6.4 的警告 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASB001_Ctl.cs` |
| R 報表 | `CASR001` | `CASR001`(結果集,非實體表) | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs` |

### 6.1 四種型別一眼表

| 面向 | M 維護 | I 查詢 | B 批次 | R 報表 |
|---|---|---|---|---|
| 全庫支數 | 284 | 87 | 215 | 322 |
| UI 基底 | `xMaintainForm`(271) | `xOneStepProcessForm`(94) | `xOneStepProcessForm`(213) | `xReportForm`(318) |
| PO 基底 | **`BaseEVADaoPO`** | 自訂介面,無基底 | 自訂介面,無基底 | 自訂介面,無基底 |
| PO 宣告主明細 | `xTableMapping`(有) | 幾乎沒有 | 幾乎沒有 | 沒有 |
| Ctl 覆寫 `InitializeVDBTypes()` | 有 | **常常沒有** | **常常沒有** | 有 |
| 四眼欄位 | 有(見 §3) | 幾乎沒有 | 少 | 沒有 |
| 額外專案 | — | — | 部分配 WindowsService | 多一個 `Report.<模組>` 放 `.rpt` |
| 專案位置 | `ATLAS.<模組>` | `ATLAS.<模組>` 或 `.Query` | `ATLAS.<模組>` | **`ATLAS.<模組>.Report`** |

`yPopUpForm` 是第五種基底(全庫 202 支),不是獨立型別——是四種型別各自的彈出子視窗 (M 用了 135 支、B 49 支、I 10 支、R 8 支),代號沿用母畫面。

### 6.2 M 維護:六層滿血版

`CASM001` 是唯一四層都認真用到的型別:

| 層 | 特徵 | 錨點 |
|---|---|---|
| UI | 繼承 `xMaintainForm`;`TabPages = 2`(查詢頁 + 維護頁);掛 `AddDataLoad` / `ModifyDataLoad` / `Before*ButtonClicked` 一整組事件 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:26`、`:107`、`:259`、`:275`、`:358-457` |
| Pxy | 有 `InitializeControl()` 覆寫,也有覆寫 `Add(BasicViewVDB)` | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:20-23`、`:30-46` |
| Ctl | **兩個 Initialize 都覆寫**;`InitializeVDBTypes()` 宣告 `DaoContractType` / `ModelVDBType` / `ViewVDBType` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:36-39`、`:43-48` |
| PO | **`: BaseEVADaoPO, ICASM001_PO`**,介面又 `: IEvaDataAccess`;建構子宣告 `MasterTable` / `DetailTable` 並掛 10 個四眼事件 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:24`、`:37`、`:42-58` |
| Entity | Model 與 View 完全同構(§5.4) | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` / `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd` |

M 型別是「四眼 + 主明細 + typed DataSet」三者齊備的樣板,其他三種都是它的減法版。四眼細節**見 §3**。

值得注意:`CASM001_Ctl.AddData()` 直接把 PO 回傳的結果 downcast 去拿新序號寫進訊息 (`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:62-65`), `result.Util.Result[0]` 沒做長度檢查,PO 若沒塞 Result 就會 index out of range。

### 6.3 I 查詢:PO 退化成裸 DAO

`CASI001` 與 M 型的差距不在多寡,在**種類**:

| 差異 | M(`CASM001_PO`) | I(`CASI001_PO`) |
|---|---|---|
| 介面 | `ICASM001_PO : IEvaDataAccess`(`CASM001_PO.cs:24`) | `ICASI001_PO`,**不繼承任何東西**(`CASI001_PO.cs:21-29`) |
| 類別 | `: BaseEVADaoPO, ICASM001_PO`(`CASM001_PO.cs:37`) | `: ICASI001_PO`,**沒有基底**(`CASI001_PO.cs:33`) |
| 連線 | 由 `BaseEVADaoPO` 管 | **自己 new 兩個 `Database`**(`CASI001_PO.cs:35-36`) |
| 主明細宣告 | `xTableMapping`(`CASM001_PO.cs:46-47`) | **整行被註解掉**(`CASI001_PO.cs:41`) |
| Ctl 的 `InitializeVDBTypes()` | 有(`CASM001_Ctl.cs:43-48`) | **完全沒有**(`CASI001_Ctl.cs:22-31` 只有 `InitializeDataAccessPool`) |

> **警告:掃描器對 `CASI001` 回報「主檔 OFD701」是錯的。** 那個表名只出現在 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41` 的**註解行** `//this.MasterTable = new TableMapping("OFD701", "SEAL");`。掃描器的 `MASTER_RE` 正規式不剝註解(`docs/tools/atlas_scan.py:32`),所以把註解當宣告。 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASI001Model.xsd` 實際只有一張表 `CLS001A`,`CASI001_Ctl.cs:101` 搬的也是 `CLS001A`。 **推論:全庫 388 張「實體表」的計數含有一批來自註解行的假表,實際數字略低。** 這是**假設**,依據是上述正規式與 CASI001 這個實例;要精確化得重掃一次並剝掉 `//` 行。

I 型另一個特徵是**大量被註解卻保留外殼的程式碼**。`CASI001_Ctl.cs` 共 143 行,其中:

| 區段 | 行 | 狀態 |
|---|---|---|
| `DoExecute()` | `:45-51` | 全註解 |
| `GetEmpNo()` / `GetUideCode()` / `GetEMAIL()` | `:60-91` | 全註解 |
| `TransferTable(... CLS002A ...)` | `:102` 與 `:112` | 全註解 |
| 對應的介面成員 | `CASI001_PO.cs:23`、`:25-27` | 全註解 |

也就是說 `CASI001_Ctl` 實際只剩 `GetData()` 一個活方法(`:37-43`)。

### 6.4 B 批次:跟 I 是同一份程式碼

把 `CASI001_Ctl.cs` 與 `CASB001_Ctl.cs` 並排會發現**兩支都是 143 行,結構逐行對應**:

| 內容 | `CASI001_Ctl.cs` | `CASB001_Ctl.cs` | 差異 |
|---|---|---|---|
| class 宣告 | `:15` | `:15` | 只差代號 |
| `InitializeDataAccessPool()` | `:26-29` | `:26-29` | 同 |
| `GetData()` | `:37-43` | `:37-43` | 同 |
| `DoExecute()` | `:45-51` **註解掉** | `:45-51` **活的** | I 不需要寫入 |
| `GetEmpNo` / `GetUideCode` / `GetEMAIL` | `:60-91` **註解掉** | `:60-91` **活的** | — |
| Transfer 兩表 | `:101-102`(第二表註解) | `:101-102`(兩表都活) | I 只用 `CLS001A`,B 用 `CLS001A`+`CLS002A` |

結論:**I 與 B 是同一份樣板複製後刪減出來的**,不是兩種設計。 B 比 I 多的只有 `ExecuteNonQuery`(寫入)這條路徑,PO 側同樣是裸 DAO (`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:22-30` 介面、`:34` 類別、`:36-37` 自建 `Database`), `MasterTable` 那行一樣被註解在 `:42`。

`CASB001_PO.cs:5` 還留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 這個註記, 顯示這批檔案在升 .NET 4.8 時被逐檔手動修過。

**B 與 WindowsService 的關係:** 只有 4 支 B 畫面配了獨立 Windows 服務:

| 服務專案 | 對應 B 畫面 |
|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600` | `OFDB600`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs`) |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609` | `OFDB609` |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680` | `OFDB680` |
| `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008` | `RSPB008` |

關係很單純:**服務不重新實作邏輯,它只是另一個呼叫端**。 `OFDB600_Service.cs:82`、`:115`、`:169`、`:194` 全是 `OFDB600_Pxy pxy = new OFDB600_Pxy();` —— 跟 UI 畫面呼叫的是同一個 Pxy、同一條 Remoting 路徑(§2.5)。服務只多做兩件事:`OnStart` 讀自己的 `.exe.config` 做 `RemotingConfiguration.Configure(...)` (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50-52`), 以及一個 60 秒 timer 比對 `HHmm` 決定要不要跑(`:27-30` 與 `:65-70`)。

`Program.cs` 用 `Environment.UserName == "SYSTEM"` 區分「服務模式」與「手動除錯模式」 (`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28-38`), 所以同一個 exe 雙擊會走 UI 分支。

### 6.5 R 報表:命名鐵律的正式例外

**R 畫面不住在 `ATLAS.<模組>`,而是住在 `ATLAS.<模組>.Report`,而且每一層資料夾與組件名都加 `Report` 前綴。** 這是全庫最系統化的例外,必須背下來:

| 一般模組 | `.Report` 專案 | 組件名 |
|---|---|---|
| `UI.CAS` | **`ReportUI.CAS`** | `Vendor.Product.TA.ReportUI.CAS` |
| `FormProxy.CAS` | **`ReportFormProxy.CAS`** | `Vendor.Product.TA.ReportFormProxy.CAS` |
| `Control.CAS` | **`ReportControl.CAS`** | `Vendor.Product.TA.ReportControl.CAS` |
| `PO.CAS` | **`ReportPO.CAS`** | `Vendor.Product.TA.ReportPO.CAS` |
| `DataEntity.CAS` | **`ReportDataEntity.CAS`** | `Vendor.Product.TA.ReportDataEntity.CAS` |
| `UIEntity.CAS` | **`ReportUIEntity.CAS`** | `Vendor.Product.TA.ReportUIEntity.CAS` |
| —(無對應) | **`Report.CAS`**(第七個專案) | `Vendor.Product.TA.Report.CAS`(`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:11-12`) |

namespace 跟著改:`Vendor.Product.TA.ReportControl.CAS` (`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:10`), 不是 `Vendor.Product.TA.Control.CAS`。**所以 R 是七層,不是六層。**

第七層 `Report.CAS` 只裝 Crystal Reports 檔:`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/` 底下 19 支 `.rpt`, 每支同時以 `EmbeddedResource` 編進組件(`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:225-228`)並生一支 `.cs` wrapper (`DependentUpon` 掛回 `.rpt`,例 `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:121-124`)。

R 的資料流與其他三型不同:

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | UI 繼承 `xReportForm`,`FormProxy = new CASR001_Pxy()` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:27`、`:41` |
| 2 | Ctl `GetReportData()` 取資料 | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:48-53` |
| 3 | Ctl `GetReportObject()` **另外**把 `.rpt` 本體以 byte 回傳給用戶端 | `.../CASR001_Ctl.cs:59-63` |
| 4 | PO 走 SP + refcursor,不組 SQL | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58`(`S_TA_CASR001_GET`)、`:67`(`LoadDataSet`) |

第 3 步用的 `CRReportTransfer.TransferFileByte(rpt)` 沒有原始碼(從呼叫端反推), `rpt` 名稱來自用戶端傳來的 `ClassData.Util.ReportParameters[0].ReportClass`(`CASR001_Ctl.cs:61`)—— **用戶端指定要載入哪個報表類別,伺服器照單全收**,值得注意。

還有兩個 R 專屬的怪處:

1. **`.rpt` 有兩條交付路徑。** 除了 `Report.CAS` 的 `EmbeddedResource`, `ReportUI.CAS` 資料夾裡也直接躺著 `CASR003RPS.rpt` 與 `CASR005RPS11.rpt`, 由 PostBuildEvent xcopy 到 `C:\Program Files\Vendor\PTPFBlock\CrystalReports\` (`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331`; `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:303` 也有同一行)。全庫有 25 個 csproj 帶這條 xcopy。同一支報表可能同時存在於組件資源與檔案系統,**版本不一致時以哪個為準取決於 `CRReportTransfer` 的實作,而它沒有原始碼**。

2. **`ReportUI.CAS` 不 reference `Report.CAS`。** `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:247-286` 的 ProjectReference 清單裡沒有它,只有 sln 把兩者並列 (`Dev/ATLAS.CAS.Report/Source/Vendor.ATLAS.CAS.Report.sln`)。報表本體是**執行期**才透過第 3 步取得,不是編譯期相依。

R 的 Entity 也特別:`Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` 宣告 `CASR001`、`CASR001_3`、`CASR001_5`、`CASR001_6` 四張「表」, 全部不是實體表(§5.5),而且 Ctl 只從 SP 拿一份 `CASR001`,再複製到另外三張 (`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:82-85`)。 View 方向只搬回 `CASR001` 一張(`:104`),另外三張是單向的。

### 6.6 哪一層常缺、為什麼

把 §2.7 的 65 支對回型別:`B` 與 `R` 佔最多。原因分三類,都能對回本章:

| 缺的層 | 支數 | 真實原因 | 佐證 |
|---|---|---|---|
| **`model` + `view`**(28) | 最大宗 | 這些畫面**根本不需要自己的 typed DataSet** —— B 批次只跑 SP 不回資料,或直接借用別支畫面的 entity | `CODB000` / `CODB901` / `CODB902` / `DSMB001` / `CLSB002` 全是 B 型 |
| **`po`**(含組合共 30) | 第二 | **PO 存在但命名不同**:`.Query` 專案用 `<代號>OracleDao` + `I<代號>`;或 entity/PO 檔名帶 `_9i` | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/IPJI613OracleDao.cs`;`Dev/ATLAS.EC/Source/Entity/DataEntity.EC/IPJB606_9iModel.xsd` |
| **`pxy`**(3) | 零星 | **全部是檔名大小寫造成的假警報,沒有一支真缺** | 見下方說明 |
| **`ui`**(1) | 零星 | 沒有畫面入口的純伺服器功能,或被別支畫面代呼叫 | `OFDM913`(缺 ui) |

型別對應的規律很清楚:

- **M 幾乎不缺**(284 支裡 12 支有缺,其中 10 支是 OFD 系列)——因為 M 一定要 `BaseEVADaoPO` + `xTableMapping` + 四眼,缺哪層都跑不起來。

- **B 最常缺 model/view** —— 批次的「輸出」是 DB 狀態改變,不是回傳資料集,typed DataSet 對它沒用。

- **I 與 R 常缺 po** —— 兩者都改用另一套 DAO 命名(`.Query` 的 `*OracleDao`、`.Report` 的 `ReportPO`), 或整支查詢下放到 SP。

> **「缺 pxy 3 支」是假的。**全庫只有三支層別檔的檔名大小寫不合慣例,而它們正好就是這三支: `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM742_pxy.cs`(小寫 `_pxy`)、 `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR452_PXy.cs` 與 `Dev/ATLAS.OFD.Report/Source/FormProxy/ReportFormProxy/OFDR461_PXy.cs`(`_PXy`)。檔案都在、也都編得過(Windows 檔名不分大小寫),是掃描器的字面比對判它缺。 **所以 65 支「六層不齊」裡,缺 FormProxy 的實際是 0 支。**

### 6.7 I 查詢為什麼常沒有四眼

四眼(EVA)是寫入流程的東西:送核、覆核、核准、退回,細節**見 §3**。 I 型別是唯讀,結構上就接不上,三個具體證據:

1. **PO 沒繼承 `BaseEVADaoPO`,介面沒繼承 `IEvaDataAccess`。** `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:21` 與 `:33` 對照 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:24` 與 `:37`。沒有基底就沒有 `BeforeVerify` / `AfterApprove` 那批事件可掛。

2. **Ctl 沒宣告 `DaoContractType`。** `CASI001_Ctl.cs` 只覆寫 `InitializeDataAccessPool()`(`:26-29`), 沒有 `InitializeVDBTypes()`;M 型有(`CASM001_Ctl.cs:43-48`)。

3. **查詢目標表本來就沒有四眼欄位。** 掃描器實測 **388 張實體表只有 19% 帶四眼欄位**。I 型查的多半是明細/歷史表,不在那 19% 裡。

例外是「查詢 + 放行」這種混合畫面:它們會出現在 `.Query` 專案但 PO 仍繼承 EVA 基底。本章對照組裡沒有這種,**假設**這類存在但比例低,依據是 I 型只有 87 支而四眼表佔比 19%, 兩者交集不會大。要確認得逐支查 PO 基底。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| I 與 B 的 PO 完全繞過 `BaseEVADaoPO`,自建 `Database` 連線 | 這兩型不受四眼、交易、連線池的框架治理;安全與稽核路徑不同 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:33-36`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:34-37` | 高 |
| 掃描器把註解行的 `MasterTable` 當成實體表宣告 | 「388 張實體表」偏高;`CASI001` 被誤標主檔 `OFD701` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41` 對照 `docs/tools/atlas_scan.py:32` | 高 |
| 報表類別名由用戶端傳入,伺服器直接載入 | 用戶端可指定任意報表類別 | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:61-62` | 高 |
| `.rpt` 兩條交付路徑並存(EmbeddedResource 與 PostBuild xcopy) | 同一報表可能有兩份不同版本;誰勝出取決於無原始碼的 `CRReportTransfer` | `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:225-228` 對照 `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331` | 高 |
| R 型別是七層不是六層,且各層加 `Report` 前綴 | 任何以六層 pattern 掃描的工具對 322 支 R 全部失準 | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:10` | 中 |
| I 與 B 是同一份 143 行樣板複製刪減 | 修 bug 要記得檢查另一型的同名畫面 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:1-143` 對照 `.../CASB001_Ctl.cs:1-143` | 中 |
| `CASI001_Ctl` 143 行裡約 40 行是註解掉的外殼 | 讀者會誤以為功能存在 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:45-51`、`:60-91`、`:102` | 中 |
| `CASM001_Ctl.AddData()` 未檢查 `Result` 長度就取 `[0]` | PO 未塞 Result 時 index out of range,錯誤被 Pxy 吞成 `ServerSideError` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:62-65` 與 `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:38-44` | 中 |
| Windows 服務用 `Environment.UserName == "SYSTEM"` 判斷執行模式 | 換服務帳號(網域服務帳號)就走錯分支 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28-38`〔客戶特定〕 | 中 |
| `CASR001` 的 Model 有 4 張表但 SP 只填 1 張,Ctl 手動複製到另外 3 張 | 三張衍生表與來源不同步時無從察覺 | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:82-85` 對照 `:104` | 中 |
| 報表 PO 把 `CommandTimeout = 0`(永不逾時) | 慢查詢會一直佔住連線 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` | 中 |
| `ReportPO.CAS` 裡留著空的 `Class1.cs` | 樣板殘留 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` | 低 |

## 7. Common 底層清冊

```text
[圖] Common 共用層四組多套平行實作:共用六層、客戶端輔助、四眼輔助、代碼字典
圖中文字:同一概念的平行複本——改一處要改全列 / 共用六層 / TA.Utility* / Utility_Pxy/Ctl/PO / 主線 / NfdUtility_* / 複本 2 / OTAUtility_* / 複本 3 / 客戶端輔助 / TA.ClientUtility / ClientBizUtility / 主線 / ClientNfdBizUtility / 複本 2 / ClientOTABizUtility / 複本 3 / ClientBiz9iUtility / 複本 4 / 四眼輔助 / 散在兩個專案 / EVAUtility / TA.ServerUtility / FourEyesHelper / TA.ServerUtility / TAEVAUtility / TA.Utility / 代碼值域字典 / TA.MappingCode / CTL014.cs / 187 類別 · 565 值 / CTL014_AGI.cs / partial 擴充 / SysCode_AGI.cs / partial 擴充
```

*圖:圖 5 共用層的平行複本。虛線框都是同一概念的另一份實作,彼此沒有繼承關係;橘色為另一客戶(AGI)的擴充,有納入本站編譯。*

`Dev/Common/` 是全系統共用層,`Dev/Exceptions/` 是例外處理層。兩者合計 23 個專案(計劃書原寫 25,實際清點為 `Common` 22 + `Exceptions` 1)。這一章回答三件事:**每個專案裝什麼**、**哪些是同一概念的多套平行實作**、**改動時的影響半徑**。

> 全系統共 252 個專案(`Dev/Vendor.ATLAS.sln`),其中 23 個在這一章。其餘是 34 個 `ATLAS.*` 業務專案資料夾展開的六層,見 §9。

### 7.1 分組總表

| 分組 | 專案 | 手寫行數 | 角色 |
|---|---|---|---|
| Base | `TA.DataAccess` | 11,944 | 四眼引擎,見 §3 §4 |
| Base | `TA.BasicDataEntity` | 少量 | `TAModel` / `BasicTAModelVDB`,所有 `*ModelVDB` 的祖先 |
| Base | `TA.BasicUIEntity` | 少量 | `TAView` / `BasicTAViewVDB`,所有 `*ViewVDB` 的祖先 |
| MappingCode | `TA.MappingCode` | 5,009 | **代碼值域字典**,§7.2 |
| Utility(客戶端) | `TA.ClientUtility` | 8,299 | UI 輔助:Infragistics 網格 / 下拉快取 / Excel / 郵件 / 壓縮 |
| Utility(伺服端) | `TA.ServerUtility` | 11,357 | 外部系統介接 / 流水號 / 四眼輔助,§7.4 |
| Utility(共用) | `TA.Utility` | 2,176 | `DateTimeHelper` / `FormatHelper` / `DataSetUtility` / `TAEVAUtility` |
| Utility(六層) | `TA.UtilityProxy` · `TA.UtilityControl` · `TA.UtilityPO` · `TA.DataEntity.Utility` · `TA.UIEntity.Utility` | 17,777 | **共用邏輯自己就是一支畫面**,§7.3 |
| Utility | `TA.GlobalProductSetting` | 78 | 單一類別 `GlobalProductSetting` |
| DataSource | `Control/DataEntity/FormProxy/PO/UI/UIEntity.DataSource`(6) | — | 跨模組共用 PO,§7.5 |
| CustomControl | `UI.CustomControl` | 186 支 cs | 約 180 個 `ucXxx` 業務複合控件 |
| CustomControl | `UI.WindowControls` | 18 支 cs | 網格 / 欄位選擇器 / KYC 清單 |
| CustomControl | `TestWindowControls` | 2 支 cs | **只有一個 `Form1`,是控件試跑殼,不是產品程式** |
| Exceptions | `Exceptions` | 835 | 例外政策鏈,§7.6 |

### 7.2 `TA.MappingCode` — repo 內唯一的代碼值域字典

這是全 repo 最被低估的一個專案。它把資料庫代碼欄位的**值與中文意義**寫成靜態類別,`<summary>` 就是中文說明。在沒有 DB 連線、沒有選單表的情況下,**它是判讀代碼欄位語意的唯一來源**。

> ⚠ **但它涵蓋率很低,而且大部分沒人用。**寫 `cod` 模組知識庫時實測(`modules/cod.md §2.4`): 程式實際用到的 `SourceType` 有 **395 個**,`CTL014.cs` 只收錄 186 個,**224 個查不到對應**; `CODCode.cs` 的 `CODE_SORT` 類別(31 個常數)**全庫引用 0 次**,取而代之的是約 190 處直接寫字面值; 真正有在用的只有 `YES_NO`(645 次)與 `EMP_DEPT_TYPE`(68 次)兩支。 **所以正確的期待是:它是唯一的字典,但你要查的代碼多半不在裡面。**

| 檔 | 靜態類別 | 值 | 行 | 內容 |
|---|---|---|---|---|
| `CTL014.cs` | 187 | 565 | 3,593 | 對應代碼檔 `CTL014`,每個類別的註解帶代碼類別編號,如「活動類別[052]」 |
| `SysCode.cs` | 2 | 71 | 375 | 系統層代碼,含 `SrNo` 流水號類別 |
| `OFDCode.cs` | 11 | 24 | 342 | OFD 模組專屬 |
| `CustomerQuery.cs` | 4 | 0 | 241 | 查詢條件組合 |
| `CODCode.cs` | 2 | 37 | 168 | COD 模組 |
| `SQLOperator.cs` | 1 | 12 | 76 | SQL 運算子字串 |
| `BMSCode.cs` | 3 | 10 | 69 | BMS 模組 |
| `LogType.cs` · `CacheManagerName.cs` · `MenuListName.cs` | 3 | 7 | 68 | 基礎設施命名 |
| `CTL014_AGI.cs` · `SysCode_AGI.cs` | 0(partial 擴充) | 9 | 77 | **客戶特定擴充**,§7.2.2 |

典型長相(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-21`):

```
/// <summary>
/// 是/否
/// </summary>
public static class YES_NO
{
    /// <summary>
    /// Y:是
    /// </summary>
    public static string Yes = "Y";
```

#### 7.2.1 這些欄位是 `static string` 不是 `const`

全專案 742 個 `public static string`、只有 73 個 `public const string`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:16` 是典型)。差別有實質後果:

- `static string` 是**可寫的**。任何一行 `YES_NO.Yes = "1";` 就會污染整個 AppDomain,而且編譯期不會擋。

- `const` 會被編譯進呼叫端組件。改 `const` 的值必須**重編所有引用它的專案**,只重編 `TA.MappingCode` 是不夠的——這對 §2 的重編順序有直接影響。

兩種寫法混用,代表這兩個陷阱同時存在。改代碼值時要先確認該欄位是哪一種。

#### 7.2.2 `_AGI` 是另一個客戶的擴充,而且有納入編譯

`CTL014_AGI.cs` 與 `SysCode_AGI.cs` 用 `partial` 補進既有類別:

| 類別 | 本體 | 擴充 |
|---|---|---|
| `PROMT_TYPE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:827` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014_AGI.cs:10` |
| `SrNo` | `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:49` | `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode_AGI.cs:12` |

兩支都列在 `<Compile Include>` 裡(`Dev/Common/Source/MappingCode/TA.MappingCode/TA.MappingCode.csproj:92`、`:100`),**所以 AGI 的代碼值在 ATLAS 版本裡也會編進去**。〔客戶特定〕

這是全 repo 第一個「另一個客戶的東西留在共用層」的證據,後面 §7.4、§8.2 還會再遇到。

### 7.3 `TA.Utility*` 五件套 — 共用邏輯自己就是一支畫面

這件事初看會誤判,寫清楚可以省掉很多時間:**共用工具層不是一堆 static helper,它完整遵守 §2 的六層鐵律**,只是「畫面代號」換成 `Utility`。

| 層 | 專案 | 類別 | 錨點 |
|---|---|---|---|
| FormProxy | `TA.UtilityProxy` | `Utility_Pxy : Basic_Pxy` | `Dev/Common/Source/Utility/TA.UtilityProxy/Utility_Pxy.cs:11` |
| Control | `TA.UtilityControl` | `Utility_Ctl` | `Dev/Common/Source/Utility/TA.UtilityControl/Utility_Ctl.cs:14` |
| PO | `TA.UtilityPO` | `Utility_PO` | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:15` |
| DataEntity | `TA.DataEntity.Utility` | `UtilityModelVDB : BasicModelVDB` | `Dev/Common/Source/Utility/TA.DataEntity.Utility/UtilityModelVDB.cs:8` |
| UIEntity | `TA.UIEntity.Utility` | `UtilityViewVDB : BasicViewVDB` | `Dev/Common/Source/Utility/TA.UIEntity.Utility/UtilityViewVDB.cs:9` |

實務上的意思:**任何畫面要呼叫共用商業邏輯,走的是 `Utility_Pxy`,也就是要過一次 Remoting**(見 §8.1),不是行程內呼叫。

#### 7.3.1 三套平行實作:`Utility` / `NfdUtility` / `OTAUtility`

每一層都有三份:

| 層 | 主線 | Nfd 線 | OTA 線 |
|---|---|---|---|
| Pxy | `Utility_Pxy.cs` 738 行 | `NfdUtility_Pxy.cs` 560 行 | `OTAUtility_Pxy.cs` 215 行 |
| Ctl | `Utility_Ctl.cs` 982 行 | `NfdUtility_Ctl.cs` 747 行 | `OTAUtility_Ctl.cs` 238 行 |
| PO | `Utility_PO` | `NfdUtility_PO` | `OTAUtility_PO` |

三者不是繼承關係,是**各自獨立的複本**,而且會互相呼叫:`NfdUtility_PO` 內部又 `new NfdUtility_PO()`(`Dev/Common/Source/Utility/TA.UtilityPO/NfdUtility_PO.cs:863`)。改共用邏輯時**三份都要確認**,只改主線是常見漏改。

在客戶端輔助層同一個概念還有第四、第五份:`ClientBizUtility` / `ClientNfdBizUtility` / `ClientOTABizUtility` / `ClientBiz9iUtility`,伺服端對應 `ServerBizUtility` / `ServerNfdBizUtility` / `ServerOTABizUtility`(`Dev/Common/Source/Utility/TA.ServerUtility/` 各檔)。

#### 7.3.2 `9i` 是第二代控件的後綴

`Common/Source` 底下有 208 支檔案含 `9i` 命名的類別:`ucAgentCode` / `ucAgentCode_9i`、`DropDownCacheHelper` / `DropDownCache9iHelper`、`CustomColumnChooser` / `CustomColumnChooser9i`。

**假設**:`9i` 是介面改版後的平行版本,舊畫面留舊版、新畫面用 `9i` 版。依據是兩者同名同職責、並存於同一專案且都有被參考。〔待確認〕確切的分界規則要有選單表或改版紀錄才能定,目前只能說「看到 `9i` 就要確認自己這支畫面用的是哪一版」。

### 7.4 `TA.ServerUtility` — 外部系統的介接口都在這

這是所有「往系統外面打」的集中地,做維護時要知道改這裡會牽動外部。

| 檔 | 對外系統 |
|---|---|
| `BillhunterAdapter.cs` · `Billhunter_WebService` | Billhunter 帳單系統(SOAP) |
| `ECAdapter.cs` | EC 網路交易平台(SOAP) |
| `LDAPAPIHelper.cs` | LDAP 帳號驗證 |
| `WEBSITEAPIHelper.cs` | 官網 API |
| `ServerMailUtility.cs` | SMTP 寄信 |
| `SerialNo.cs` · `SerialNo_AGI.cs` | 流水號配號(又一組 `_AGI` 擴充) |
| `OracleHelper.cs` · `SQLHelper.cs` | **兩個資料庫引擎的 helper 並存**,見 §4 |
| `EVAUtility.cs` · `EVAStringHelper.cs` · `FourEyesHelper.cs` | 四眼輔助,見 §3 |

`Web References/` 下有四組產生出來的 SOAP proxy:`BatchBill` / `BillHunterService` / `Billhunter_WebService` / `ECService`。端點寫在設定檔(`Dev/Common/Source/Utility/TA.ServerUtility/App.config:12`、`:16`、`:20`),其中兩個是 `example.com.tw` 的 UAT 位址、一個是 `http://localhost`。〔客戶特定〕

> 四眼輔助分散在兩個專案(`TA.ServerUtility` 的 `EVAUtility` / `FourEyesHelper`,`TA.Utility` 的 `TAEVAUtility`),職責邊界不明。要動四眼相關工具函式前,三個都要看。

### 7.5 `DataSource` 六件套 — 跨模組共用 PO

六個專案照六層命名(`Control` / `DataEntity` / `FormProxy` / `PO` / `UI` / `UIEntity`.DataSource),裝的是**不屬於任何單一模組的共用資料來源**。`PO.DataSource` 裡的 PO 也以 `xTableMapping` 宣告實體表,所以掃描器統計的 413 張實體表裡有一部分來自這裡(見附錄 A)。

### 7.6 `Exceptions` — 例外政策鏈

| 檔 | 行 | 角色 |
|---|---|---|
| `CommonExceptionBlocker.cs` | 563 | 攔截點,唯一有份量的實作 |
| `ELExceptionAgent.cs` | 216 | 走 Enterprise Library 5.1 的政策 |
| `FusionExceptionAgent.cs` | 50 | 走 Fusion 框架的政策 |
| `DoExceptionPolicyHandler.cs` | **6** | **幾乎是空殼** |
| `Handler/*.cs`(10 支) | — | 依層級分政策:`Client` / `Server` / `DevelopServer` / `FormProxy` / `BaseForm` / `Unhandled` / `SQL` |
| `ApplicationLayer/*.cs`(5 支) | — | 例外型別階層:`VendorApplicationException` → `BusinessLayerException` / `PresentationLayerException` / `BaseFormException` |
| `Dialog/*.cs`(3 支) | — | 錯誤對話框呈現 |

兩套例外代理(EL 與 Fusion)並存,選哪一套由設定檔的 `ExceptionHandlingMode` 決定——但該設定在 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` 裡是**被註解掉的**(見 §8.3),所以實際走哪一套要看部署機上的設定檔,repo 判斷不出來。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 代碼值域用 `static string` 可被寫入,742 處 | 任何一行誤指派污染整個 AppDomain,編譯期不擋 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:16` | 中 |
| `const`(73)與 `static`(742)混用 | 改 `const` 值須重編所有引用端,只重編 `TA.MappingCode` 不生效 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-21` | 中 |
| 另一客戶的 `_AGI` 代碼有納入編譯 | ATLAS 版本內含非 ATLAS 的代碼值 | `Dev/Common/Source/MappingCode/TA.MappingCode/TA.MappingCode.csproj:92` | 低 |
| 共用邏輯三套平行複本(主 / Nfd / OTA) | 改一處要改三處,漏改不會編譯失敗 | `Dev/Common/Source/Utility/TA.UtilityControl/NfdUtility_Ctl.cs:1` | **高** |
| 客戶端輔助再分四套(含 `9i`) | 同上,且分界規則無文件 | `Dev/Common/Source/Utility/TA.ClientUtility/ClientBizUtility.cs:1` | 中 |
| 四眼輔助散在三個類別兩個專案 | 改四眼工具函式容易只改到其中一份 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:1` | 中 |
| `DoExceptionPolicyHandler.cs` 只有 6 行 | 命名像政策入口實際是空殼,誤導 | `Dev/Exceptions/DoExceptionPolicyHandler.cs:1` | 低 |
| `TestWindowControls` 只含一個 `Form1` | 試跑殼混在產品方案的 252 個專案裡 | `Dev/Common/Source/CustomControl/TestWindowControls/TestWindowControls.csproj:1` | 低 |

---

## 8. 部署與執行環境

```text
[圖] 部署拓撲:UI 與 WindowsService 在客戶端,其餘五層在伺服端 IIS,只有四眼引擎那層碰資料庫
圖中文字:客戶端(桌機 / Citrix) / main.exe + UI.<MOD> / 改 UI 只佈這裡 / UIEntity.<MOD> / 兩端版本必須一致 / Remoting 設定 / 部署產物,不在版控 / WindowsService 四支 / 也是 Remoting 呼叫端 / Remoting / *.rem 端點 / http + binary / 伺服端 IIS:ATLAS_TAService / FormProxy · Control · PO / 四層改動佈這裡 / DataEntity · UIEntity / UIEntity 兩端都要 / 四眼引擎 TA.DataAccess / 改這裡 908 支全中 / PTPFBlock DLL / C:\Program Files\Vendor / 資料 / 設定 / Oracle ATLASDB / ODP.NET / 設定檔商業參數 / 費率 / 區間寫在這
```

*圖:圖 6 部署拓撲。左欄 = 改了要佈客戶端,右三欄 = 改了要佈伺服端。UIEntity 兩欄都出現,因為 Remoting 序列化要求兩端型別版本一致(此為推論);WindowsService 走同一條 Remoting 路徑,不直連資料庫。*

這一章要回答維護時最實際的問題:**改了哪一層,要部署到哪一台**。

### 8.1 Remoting 邊界在 UI → FormProxy 之間

這是全篇最關鍵的一條,因為它決定部署範圍。證據在 Remoting 設定:

```
<wellknown type="Vendor.Product.TA.FormProxy.EC.OFDB600_Pxy, Vendor.Product.TA.FormProxy.EC"
           url="http://<內網伺服器IP>/ATLAS_TAService/OFDB600_Pxy.rem"/>
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189`

註冊為遠端物件的是 **`_Pxy` 型別本身**,而且這段 `<wellknown>` 位在 `<client>` 區段裡——這是 .NET Remoting 的客戶端註冊,效果是**攔截該型別的 `new`**,回傳透明代理而非本地實例。

三項證據互相對得上:

| 證據 | 錨點 |
|---|---|
| UI 直接 `new` 出 Proxy,沒有任何遠端呼叫語法 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:111` |
| 每支 `_Pxy` 都繼承框架基底 `Basic_Pxy`(黑箱,見附錄 C.2) | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:15` |
| 該型別在 `<client>` 區段註冊為 `.rem` 端點 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189` |

所以真正的 `_Pxy` 實例活在伺服端。這解釋了為什麼 `_Pxy` 內部可以直接 `new XXX_Ctl()` 而不需要任何遠端呼叫語法——它執行時已經在伺服端了。

由此推出的部署規則:

| 改哪一層 | 要部署到 |
|---|---|
| UI | **客戶端** |
| FormProxy / Control / PO / DataEntity / UIEntity | **伺服端**(IIS 的 `ATLAS_TAService`) |
| UIEntity | 兩邊都要(它是 Remoting 傳輸的資料型別,兩端序列化版本必須一致) |

> `UIEntity` 兩邊都要的理由是型別必須兩端可解析,這是 .NET Remoting 二進位序列化的必然要求,不是從某一行程式看出來的,標為**推論**。

通道設定:`http` channel + `binary` formatter(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:179`),`useDefaultCredentials="true"` 走 Windows 整合驗證。伺服端以 IIS 裝載 `.rem` 端點。

〔客戶特定〕伺服器位址 `<內網伺服器IP>`、虛擬目錄 `ATLAS_TAService`,設定檔內註解寫「趴板時請變更 url 屬性中的伺服器位置」。

#### 8.1.1 客戶端的 Remoting 設定檔不在 repo 裡

全 repo 只有三支設定檔含 `<channel>`:兩支 `WindowsService`(`OFDB600` / `OFDB609`)加一支控件試跑殼。而 `.rem` 註冊只有 20 筆,其中 18 筆屬於 `SWEmailService` 與 `SWService` 兩個 Vendor 共用產品,真正的 TA 只有 `OFDB600_Pxy` 與 `OFDB609_Pxy` 兩筆。

911 支畫面顯然不是靠這兩筆在跑。**主程式(`main.exe`)的 Remoting 設定是部署產物,不在版控內。**要完整重現環境,需要部署機上的 `main.exe.config`——這是目前缺的輸入之一。

### 8.2 資料庫:三個 Oracle provider,各有分工

repo 同時參考三個 Oracle 驅動,分佈有清楚規律:

| Provider | 用在 | 判讀 |
|---|---|---|
| `Devart.Data.Oracle`(dotConnect) | `DataEntity.*` / `UIEntity.*` 專案 | **設計期**:typed DataSet 設計工具重生 Designer.cs 時用,見 §5 |
| `Oracle.ManagedDataAccess`(ODP.NET) | `TA.DataAccess` / `PO.DataSource` / `TA.ServerUtility` | **執行期** |
| `System.Data.OracleClient` | `DataEntity.EC` / `UIEntity.EC` / `PO.OTA` / `PO.OTAB` | **遺留**:.NET 內建版,微軟早已標為過時 |

這對「手動加欄位」有直接後果:**要重生 typed DataSet,開發機必須裝 Devart dotConnect for Oracle,並連得到設計期資料庫**(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8`,`Server=ora01.vendor.com.tw;Sid=ATLASDB`)。這台是 Vendor 的開發庫,不是客戶正式庫。

#### 8.2.1 設定檔裡還躺著 SQL Server 的連線字串

`Dev/Common/Source/Base/TA.DataEntity/app.config:6` 是 `System.Data.SqlClient`,指向 `Test002` 的 `PTPF_TA_AGI`。`Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` 有 14 筆同類,命名空間甚至寫 `Vendor.AGI.TA.UIEntity.DataSource`(`Dev/Common/Source/DataSource/UIEntity.DataSource/App.config:6`)。

**這些是 AGI 產品線留下的設計期設定,不是 ATLAS 的執行期連線。**判斷依據有三:(1) 全部落在 `DataEntity` / `UIEntity` 這類設計期專案;(2) 目錄名與命名空間都寫 AGI;(3) 執行期的資料庫型態由框架設定決定為 Oracle(下一節)。標為**推論**,要 100% 確定需要部署機上的設定檔。

#### 8.2.2 執行期資料庫型態由 Fusion 框架設定

```
<add name="TA" dataBaseProvider="Oracle" sqlLogEnable="false"/>
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:65`

六個具名資料庫(`Fusion` / `SWProduct` / `Logging` / `TA` / `SWEMail` / `Scripting`)全部設為 Oracle(`:62-67`)。註解明說合法值是 `MSSQL` 或 `Oracle`——**雙引擎支援是框架層的設計,不是這個專案的**。ATLAS 站台選 Oracle。另有 `appSettings` 的 `DbServerType` 也是 `Oracle`(`:200`)。

### 8.3 框架堆疊與黑箱邊界

執行期依賴的框架不只一套:

| 框架 | 版本 | 證據 |
|---|---|---|
| Vendor Fusion | 1.12.20.85 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:10` |
| Microsoft Enterprise Library | 5.1.0.0 | 同檔 `:3-6` |
| Vendor PTPFBlock | — | 見附錄 C |
| Infragistics WinForms | v19.1 | `Dev/Common/Source/CustomControl/UI.CustomControl/UI.CustomControl.csproj` |
| Crystal Reports | — | 609 支 `.rpt`,見 §6 |

`Dev/Exceptions/` 同時有 EL 與 Fusion 兩套例外代理(§7.6),而切換用的 `ExceptionHandlingMode` 在設定檔裡是註解狀態(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:198` 附近)。同一支設定檔裡大段 `ServiceSettings` / `ExceptionHandling` / `CachingSettings` 也都被註解掉——**設定檔裡「看起來有設」與「實際生效」差很多,讀的時候要先確認有沒有被註解**。

### 8.4 WindowsService 四支

| 服務 | 位置 |
|---|---|
| `OFDB600` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50` |
| `OFDB609` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:40` |
| `OFDB680` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:42` |
| `RSPB008` | `Dev/ATLAS.RSP/Source/WindowsService/` |

**三支 `OFDB*` 是 Remoting 客戶端,`RSPB008` 不是。**這兩種要分開看。

三支 `OFDB*` 用同一個開場:`RemotingConfiguration.Configure(自己的 exe.config)` → `CustomErrorsEnabled(false)` → `CustomErrorsMode = RemoteOnly`,透過 `_Pxy` 打到伺服端,不直接碰資料庫。

`RSPB008_Service` 完全不同(寫 `rsp` 模組知識庫時查出,`modules/rsp.md §6`):

| 項目 | 三支 `OFDB*` | `RSPB008` |
|---|---|---|
| `RemotingConfiguration` | 有 | **0 次** |
| `Environment.UserName` 判執行模式 | 有(見 §8.5.3 的雷) | **0 次**,無條件 `ServiceBase.Run` |
| csproj 參考 | `FormProxy.*` | **`Control.RSP`**,沒有 FormProxy |
| 實際行為 | 過 Remoting 打伺服端 | **同一行程直接 `new RSPB008_Ctl()` 打 DB** |

> 所以「WindowsService 都是 Remoting 客戶端」**不是通則**。這也影響部署:`RSPB008` 那台不需要 Remoting 端點設定,但需要直連資料庫的權限。原本這一節寫成四支一概而論,是從三支 `OFDB*` 推出來的過度概化,已更正。

`OFDB609_Service.cs` 與 `OFDB680_Service.cs` 各出現兩次相同的三行初始化(`:40-42` 與 `:54-56`;`:42-44` 與 `:138-140`)——重複初始化,可能是防禦寫法也可能是複製貼上殘留,無註解可判。

### 8.5 執行期落地路徑與外部相依

全部寫死在設定檔,不是參數化的:

| 用途 | 路徑 |
|---|---|
| 框架 log | `C:\Vendor\VendorProduct\*.log` |
| 加密金鑰 | `C:\Vendor\Keys\DefaultKey.key`(`…OFDB600/App.config:43`) |
| 匯出檔 | `C:\Vendor\ExportFile` |
| TDCC 指託各式資料檔 | `C:\Vendor\TDCC指託\…`(四個 `appSettings` 鍵) |
| 框架 DLL | `C:\Program Files\Vendor\PTPFBlock\` |

還開了 Citrix 支援(`IsSupportCitrix=true`,`…OFDB600/App.config:262`),註解說明在 Citrix 下報表暫存目錄會改放到 log 目錄下。〔客戶特定〕

### 8.6 商業規則被寫在設定檔裡

這一條值得單獨列出,因為它會讓人找錯地方:

```
<add key="OFDM233_SHORT_FEE_RATE" value="0.01"/>
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:207`

同組還有 `OFDM233_BNG_MONTH` / `OFDM233_BNG_DAY` / `OFDM233_END_MONTH` / `OFDM233_END_DAY`。**`OFDM233` 這支畫面的短線費率與計費區間不在程式也不在資料庫,在設定檔。**要改這類參數是改設定檔重啟,不是改 code 重編。至於還有哪些畫面是這樣,只能逐一 grep `appSettings` 的鍵名前綴。

### 8.7 設定檔的安全問題

| 問題 | 錨點 |
|---|---|
| 服務帳號密碼明文 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:142-143` |
| 資料庫密碼明文 | `Dev/Common/Source/Base/TA.DataEntity/app.config:6` 及 `Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` 全部 14 筆 |
| SMTP 密碼明文(在註解區段內) | `…OFDB600/App.config:120` 附近 |
| 對稱加密金鑰路徑明碼指向固定檔 | `…OFDB600/App.config:43` |
| 影像印鑑系統帳密以 `LoginUserID` / `LoginPassword` 明文帶入 | `…OFDB600/App.config:230` 附近 |

這些檔案在版控裡,任何拿得到 repo 的人都拿得到這些密碼。本文一律不重製密碼值,只記位置。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| Remoting 邊界在 UI → FormProxy | 決定改哪層部署哪台,搞錯會出現「改了沒效果」 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189` | **高**(關鍵前提) |
| 主程式 Remoting 設定不在 repo | 無法從 repo 重建客戶端環境 | 全 repo 僅 3 支設定檔含 `<channel>` | **高** |
| 設定檔含多組明文密碼 | 拿到 repo = 拿到資料庫與服務帳密 | `Dev/Common/Source/Base/TA.DataEntity/app.config:6` | **高** |
| 三個 Oracle provider 並存 | 加欄位要裝對工具;遺留 provider 可能行為不同 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` | 中 |
| AGI 的 SQL Server 連線字串留在共用層 | 誤判執行期資料庫型態 | `Dev/Common/Source/DataSource/UIEntity.DataSource/App.config:6` | 中 |
| 商業參數(費率、計費區間)寫在設定檔 | 改規則找錯層,以為要改 code | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:207` | 中 |
| 大段設定被註解,無法從 repo 判斷實際生效值 | 例外處理走 EL 還是 Fusion 判斷不出來 | `…OFDB600/App.config:110-160` | 中 |
| `appSettings` 有重複鍵(`DbServerType`、`EnableExceptionLog` 各兩次) | 值相同所以目前無害,改其一會產生不一致 | `…OFDB600/App.config:200` 與 `:202` | 低 |
| 服務初始化三行重複出現兩次 | 意圖不明,無註解 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:40-42` 與 `:54-56` | 低 |

---

## 9. 模組地圖

```text
[圖] 模組地圖:19 個畫面代號前綴依畫面數分三層,標示 B/I/M/R 型別分佈
圖中文字:畫面數 ≥ 50(佔全系統 82%) / OFD  550 支 / B165 I77 M214 R94 / NFD  136 支 / 全部 R · 223 支 .rpt / RSP  56 支 / B17 M8 R31 / 畫面數 10–29 / DSM 29 / M10 R17 / CRM 18 / M4 R8 / BBS 17 / M10 R7 / CAS 16 / M6 R8 / IPJ 15 / 六層全不齊 / TMK 14 / M3 R11 / CPM 13 / B6 M4 R3 / COD 12 / M8 B4 / BMS 11 / M8 B3 / 畫面數 ≤ 7 / CLS 7 / TRP 6 / 在 OTA 專案 / OTA 3 / SDM 2 / CTL 1 / 在 COD 專案 / FSK 1 / IJP 1 / IPJ 的錯字
```

*圖:圖 7 模組地圖。前三個前綴就佔 742 / 908 支。虛線為整個模組六層都不齊者,橘色為打錯的前綴。前綴不等於專案資料夾,對照見 §9.2。*

### 9.1 先釐清:「模組」有兩種數法

計劃書寫「34 個模組」,實掃後要更正——**34 與 19 都對,但指的是不同東西**:

| 數法 | 數量 | 定義 |
|---|---|---|
| 專案資料夾 | **34** | `Dev/ATLAS.*`,含 `.Report` / `.Query` / `B` / `I` 等變體 |
| 畫面代號前綴 | **19** | 畫面代號前 2–4 碼,即 §2 的模組碼 |

兩者**不是一對一**。最極端的例子是 `OFD`:550 支畫面散在 12 個專案資料夾裡。反過來 `IPJ` 的畫面一支也不在叫 `IPJ` 的資料夾——全在 `ATLAS.EC*` 底下。

**所以拿到一支畫面代號,不能從代號推出它在哪個專案資料夾,要用掃描器查:**

```
py -V:3.12 \docs\tools\atlas_scan.py --screen OFDB562
```

### 9.2 前綴 → 專案資料夾對照

| 前綴 | 畫面數 | 所在專案資料夾(依畫面數排序) |
|---|---|---|
| `OFD` | 550 | `OFD` · `OFDB` · `OFD.Report` · `OFD.Query` · `OTAB` · `EC` · `OTA.Report` · `OTA.Query` · `EC.Report` · `OTA` · `EC.Query` · `OFDI` |
| `NFD` | 136 | `NFD.Report` |
| `RSP` | 56 | `RSP.Report` · `RSP` |
| `DSM` | 29 | `DSM.Report` · `DSM` |
| `CRM` | 18 | `CRM` · `CRM.Report` |
| `BBS` | 17 | `BBS` · `BBS.Report` |
| `CAS` | 16 | `CAS` · `CAS.Report` |
| `IPJ` | 15 | `EC` · `EC.Query` · `EC.Report` |
| `TMK` | 14 | `TMK.Report` · `TMK` |
| `CPM` | 13 | `CPM` · `CPM.Report` |
| `COD` | 12 | `COD` |
| `BMS` | 11 | `BMS` |
| `CLS` | 7 | `CLS` · `CLS.Report` |
| `TRP` | 6 | `OTA` · `OTA.Query` · `OTA.Report` |
| `OTA` | 3 | `OTA` · `OTA.Report` · `OTAB` |
| `SDM` | 2 | `SDM` |
| `CTL` | 1 | `COD` |
| `FSK` | 1 | `FSK` |
| `IJP` | 1 | `EC.Report` |

### 9.3 型別分佈與業務推測

**「推測業務」一欄全部是從表名、`msdata:Caption` 與代碼類別名反推的,沒有一項有權威來源。**選單表不在 repo,拿到對照表後要整欄回填。

| 前綴 | 畫面 | B | I | M | R | `.rpt` | 推測業務 |
|---|---|---|---|---|---|---|---|
| `OFD` | 550 | 165 | 77 | 214 | 94 | 91 | 開放式基金主軸:申購 / 買回 / 轉換 / 帳務,**佔全系統 61%** 〔推測〕 |
| `NFD` | 136 | 0 | 0 | 0 | 136 | 223 | **純報表模組**,無任何維護 / 查詢 / 批次畫面 〔推測〕 |
| `RSP` | 56 | 17 | 0 | 8 | 31 | 39 | 定期定額(Regular Savings Plan),有專屬 WindowsService `RSPB008` 〔推測:代碼註解明寫「定期定額」〕 |
| `DSM` | 29 | 1 | 1 | 10 | 17 | 39 | 通路 / 銷售管理 〔推測〕 |
| `CRM` | 18 | 5 | 1 | 4 | 8 | 11 | 客戶關係;主表 `CRM003A` 帶「潛在客戶序號」 〔推測〕 |
| `BBS` | 17 | 0 | 0 | 10 | 7 | 13 | 帳務 / 單位數相關(`BBSUnits`) 〔推測〕 |
| `CAS` | 16 | 1 | 1 | 6 | 8 | 19 | 客服 / 案件;與 `CRM` 共用主表 〔推測〕 |
| `IPJ` | 15 | 7 | 5 | 1 | 2 | — | 網路交易相關,全部住在 `EC` 專案 〔推測〕 |
| `TMK` | 14 | 0 | 0 | 3 | 11 | 24 | 電話行銷(Telemarketing) 〔推測〕 |
| `CPM` | 13 | 6 | 0 | 4 | 3 | 8 | 活動 / 促銷管理(`CAMPAIGN_*` 代碼群) 〔推測〕 |
| `COD` | 12 | 4 | 0 | 8 | 0 | — | 代碼檔維護 〔推測〕 |
| `BMS` | 11 | 3 | 0 | 8 | 0 | — | 印鑑 / 基本資料維護(`BMSSEAL`) 〔推測〕 |
| `CLS` | 7 | 2 | 1 | 2 | 2 | 22 | 結算 / 清算 〔推測〕 |
| `TRP` | 6 | 0 | 1 | 4 | 1 | — | 信託相關,住在 `OTA` 專案 〔推測〕 |
| `OTA` | 3 | 1 | 0 | 1 | 1 | 67 | 線上交易平台;**專案很大但自有代號只有 3 支**,主要承載 `OFD` 的平行實作 |
| `SDM` | 2 | 2 | 0 | 0 | 0 | — | 〔不明〕 |
| `CTL` | 1 | 1 | 0 | 0 | 0 | — | 控制檔;住在 `COD` 專案 〔推測〕 |
| `FSK` | 1 | 0 | 0 | 1 | 0 | — | 〔不明〕 |
| `IJP` | 1 | 0 | 0 | 0 | 1 | — | **`IPJ` 的錯字**,見 §9.5 |
| 合計 | **911** | 215 | 87 | 285 | 324 | 608 |  |

### 9.4 讀這張表時的三個陷阱

1. **`NFD` 136 支全是 R。** 它沒有 `ATLAS.NFD` 資料夾,只有 `ATLAS.NFD.Report`,而且獨佔 223 支 `.rpt`(全系統 609 支的 37%)。這個模組的維護完全是報表維護。

2. **`OTA` 專案 ≠ `OTA` 模組。** `ATLAS.OTA*` 四個資料夾裝的多半是 `OFD` 與 `TRP` 的畫面。§2 提到的 15 個「同代號兩個專案」全部出自 `OFD` 與 `OTA` / `EC` 的平行變體。

3. **`.rpt` 數與 R 畫面數對不上。** 例 `NFD` 136 支 R 畫面卻有 223 支 `.rpt`,`OFDB` 明明不是 `.Report` 專案卻有 20 支 `.rpt`。一支報表畫面可以掛多份範本,批次專案也可以直接產報表。

### 9.5 `IJPR611` 是打錯的畫面代號

`Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/IJPR611_Ctl.cs` 是全系統唯一前綴為 `IJP` 的畫面,而同一個目錄裡就有 `IPJR607_Ctl.cs` 與 `IPJR901_Ctl.cs`。前綴 `IPJ` 的字母被寫反了。

影響是實質的:任何按模組前綴做的批次處理(掃描、部署、權限設定、本文的 §9.2 表)都會把它分成一個獨立模組。修正要改檔名與類別名,牽動六層,**不在本階段動,先記錄**。

### 9.6 六層不齊的 65 支,分佈集中

| 前綴 | 不齊數 | 佔該模組 |
|---|---|---|
| `OFD` | 42 | 7.6% |
| `IPJ` | 15 | **100%** |
| 其他 | 8 | — |

`IPJ` 15 支**全部**六層不齊,不是零星缺漏而是整個模組就是這樣寫的。詳細缺層型態與原因分類見 §6。

### 本章發現

| 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 畫面代號前綴無法推出所在專案 | 找檔必須靠掃描器,憑代號猜會找錯 | `Dev/ATLAS.EC/Source/Control/Control.EC/IPJB606_Ctl.cs:1` | 中 |
| `IJPR611` 前綴打錯 | 按前綴的批次作業會多算一個模組 | `Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/IJPR611_Ctl.cs:1` | 中 |
| `ATLAS.BO` 只有 1 支 cs 檔 | 空專案掛在 252 個專案的方案裡,增加建置時間與誤解 | `Dev/ATLAS.BO/Source/BO.BMS/BO.BMS.csproj:1` | 低 |
| 34 專案 / 19 前綴的名詞混淆 | 「模組」一詞在不同文件指不同東西 | 本節 §9.1 | 低(本文已統一) |
| 選單 / 權限表不在 repo | 911 支畫面的中文名與業務歸屬全部只能推測 | — | **高**(阻擋項) |

## 附錄 A 實體表總表(413)

> 本表由 `atlas_scan.py` 掃 PO 建構子的 `xTableMapping` / `TableMapping` 宣告產生,再以 `docs/tools/` 的產生器輸出,**不是手打的**。改過原始碼後跑 `--refresh` 重掃即可重產。

> 「欄位」為 0 表示這張表沒有任何 xsd 定義過它的欄位——只有 PO 的 SQL 字串知道它長什麼樣,要改它必須查資料庫。「四眼」欄看的是有沒有出現 §3 那組 EVA 欄位;對只在 xsd 出現部分欄位的表,這一欄可能低估。

| 統計 | 值 |
|---|---|
| 實體表總數 | 437 |
| 有 xsd 欄位定義 | 180(41%) |
| **無任何 xsd 欄位定義** | **257(59%)** |

四眼欄位覆蓋率有三種算法,數字不同但都對,引用時要講清楚是哪一種(分母一律取「有 xsd 欄位定義」的 180 張,因為另外 257 張根本無從判斷):

| 判準 | 張數 | 佔有定義的 | 佔全部 437 |
|---|---|---|---|
| 六個 ID 欄或 `STATUS` 出現任一 | 145 | 81% | 33% |
| 六個 ID 欄出現任一 | 142 | 79% | 32% |
| 六個 ID 欄**全部齊備** | 141 | 78% | 32% |

> 比修 D5 當時報的「158 / 177 = 89%」低,是因為 D6–D11 又補進 24 張表,而且這輪改用 `gen_appendix_ab.py` 的 EVA 欄位集合重算, 而補進來的多半是**批次與報表用的暫存 / 結果表,本來就不該有四眼欄位**。分母變大、分子沒同步變大,比率因此下修。**「四眼是業務表的標準配備」這個結論不變** —— 換成只看有主檔宣告的業務表,比率仍在九成上下。

下表「四眼」欄用的是第一種(最寬鬆)判準。

| 表 | 模組 | 欄位 | 中文名 | 四眼 | 主表於 | 明細於 |
|---|---|---|---|---|---|---|
| `BBS001A` | — | 0 | — | ? | `BBSM001` | — |
| `BBS002A` | — | 0 | — | ? | — | `BBSM001` |
| `BBS003A` | — | 0 | — | ? | `BBSM003` | — |
| `BBS004A` | — | 0 | — | ? | — | `BBSM003` |
| `BBS005A` | — | 0 | — | ? | `BBSM004` | — |
| `BBS006A` | — | 0 | — | ? | — | `BBSM004` |
| `BBS007A` | — | 0 | — | ? | `BBSM005` | — |
| `BBS008A` | — | 0 | — | ? | — | `BBSM005` |
| `BBS009A` | — | 0 | — | ? | `BBSM009` `BBSM109` | — |
| `BBS010A` | — | 0 | — | ? | — | `BBSM009` `BBSM109` |
| `BBS011A` | — | 0 | — | ? | `BBSM010` `BBSM110` | — |
| `BBS012A` | — | 0 | — | ? | — | `BBSM010` `BBSM110` |
| `BBS013A` | — | 0 | — | ? | `BBSM013` `BBSM113` | — |
| `BBS014A` | — | 0 | — | ? | — | `BBSM013` `BBSM113` |
| `BBS015A` | — | 0 | — | ? | — | `BBSM013` `BBSM113` |
| `BBS020A` | — | 0 | — | ? | — | `BBSM003` |
| `BMS001A` | — | 0 | — | ? | `OFDM053` | — |
| `BMS001ACHG` | — | 0 | — | ? | `BMSM004` | — |
| `BMS004ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `BMS005A` | BMS | 8 | 8/8 | — | — | `BMSM006` |
| `BMS005ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `BMS007A` | — | 0 | — | ? | `BMSM007` | — |
| `BMS906` | DSM | 25 | 24/25 | — | `DSMM906` | — |
| `BMS924` | BMS | 62 | 44/62 | ✓ | `BMSM924` | — |
| `BMS925A` | BMS | 30 | 9/30 | ✓ | `BMSM925` | — |
| `BMS926A` | BMS | 22 | 7/22 | ✓ | — | `BMSM925` |
| `BMS927A` | BMS | 33 | 18/33 | ✓ | — | `BMSM925` |
| `BMS999` | OTA OFD | 18 | 3/18 | ✓ | `OTAM901` | — |
| `CAS001A` | CAS | 20 | 5/20 | ✓ | `CASM003` | — |
| `CAS002A` | CAS | 19 | 4/19 | ✓ | — | `CASM003` |
| `CAS003A` | CAS | 35 | 32/35 | ✓ | — | `CASM001` |
| `CAS004A` | CAS | 26 | 11/26 | ✓ | `CASM004` | — |
| `CAS005A` | CAS | 28 | 13/28 | ✓ | `CASM005` | — |
| `CLS001` | CLS | 56 | 41/56 | ✓ | `CLSM001` | — |
| `CLS001A` | CAS CLS | 85 | 84/85 | ✓ | `CASM002` | — |
| `CLS002` | CLS | 40 | 25/40 | ✓ | `CLSM002` | — |
| `CLS002A` | CAS | 26 | 9/26 | ✓ | — | `CASM002` |
| `CLS003` | CLS | 20 | 5/20 | ✓ | — | `CLSM002` |
| `CLS004` | CLS | 22 | 5/22 | ✓ | — | `CLSM002` |
| `CLS005` | CLS | 19 | 2/19 | ✓ | — | `CLSM002` |
| `COD005A` | — | 0 | — | ? | `CODM005` | — |
| `COD006A` | — | 0 | — | ? | `CODM006` | — |
| `COD007A` | — | 0 | — | ? | `CODM007` | — |
| `COD009` | COD | 56 | 45/56 | ✓ | `CODB009` `CODM009` `RSPM037` | — |
| `COD010` | COD | 35 | 10/35 | ✓ | `CODM010` | — |
| `COD016` | COD | 19 | 4/19 | ✓ | `CODM016` | — |
| `COD040A` | — | 0 | — | ? | `CODM036` | — |
| `CPM001A` | CPM | 20 | 5/20 | ✓ | `CPMM001` | — |
| `CPM0031A` | CPM | 18 | 2/18 | ✓ | — | `CPMM003` |
| `CPM003A` | CPM | 29 | 14/29 | ✓ | `CPMM003` | — |
| `CPM004A` | CPM | 69 | 68/69 | ✓ | `CPMB001` `CPMB002` `CPMB003` `CPMB004` …+2 | — |
| `CPM005A` | CPM | 18 | 0/18 | ✓ | — | `CPMB001` `CPMB002` `CPMB003` `CPMB004` …+2 |
| `CPM0061A` | CPM | 18 | 0/18 | ✓ | — | `CPMB001` `CPMB002` `CPMB003` `CPMB004` …+1 |
| `CPM006A` | CPM | 18 | 0/18 | ✓ | — | `CPMB001` `CPMB002` `CPMB003` `CPMB004` …+2 |
| `CPM007A` | CPM OFD | 43 | 42/43 | ✓ | `CPMM005` | — |
| `CRM001A` | CRM | 20 | 20/20 | ✓ | `CRMM001` | — |
| `CRM002A` | CLS CRM | 19 | 19/19 | ✓ | `CRMM001` | — |
| `CRM003A` | CAS CRM TMK | 72 | 71/72 | ✓ | `CASM001` `CRMM003` | — |
| `CRM004` | — | 0 | — | ? | `CRMM004` | — |
| `CRM0041A` | CRM | 20 | 19/20 | ✓ | — | `CRMM003` |
| `CRM004A` | CRM | 27 | 25/27 | ✓ | — | `CRMM003` |
| `CRM0061A` | CRM | 20 | 19/20 | ✓ | — | `CRMM003` |
| `CRM006A` | CRM | 21 | 21/21 | ✓ | — | `CRMM003` |
| `CRM008A` | CRM | 21 | 6/21 | ✓ | `CRMM002` | — |
| `CRSDTL` | — | 0 | — | ? | `BMSM926` | — |
| `CRSDTLCHG` | — | 0 | — | ? | — | `BMSM926` |
| `CRSEXRATE` | — | 0 | — | ? | `BMSM927` | — |
| `CTL006A` | — | 0 | — | ? | — | `RSPB009` |
| `DSM001A` | CAS DSM | 26 | 11/26 | ✓ | `CASM006` `DSMM001` | — |
| `DSM002A` | CAS DSM | 24 | 9/24 | ✓ | — | `CASM006` `DSMM001` |
| `DSM003A` | DSM | 22 | 7/22 | ✓ | `DSMM003` | — |
| `DSM004A` | DSM | 20 | 5/20 | ✓ | — | `DSMM003` |
| `DSM005A` | DSM | 21 | 21/21 | ✓ | `DSMM005` | — |
| `DSM007A` | DSM | 25 | 10/25 | ✓ | `DSMM002` | — |
| `DSM008A` | DSM | 24 | 9/24 | ✓ | — | `DSMM002` |
| `DSM901` | DSM | 23 | 7/23 | ✓ | `DSMM901` | — |
| `DSM902` | DSM | 31 | 13/31 | ✓ | — | `DSMM901` |
| `DSM903` | DSM | 22 | 7/22 | ✓ | `DSMM902` | — |
| `DSM904` | DSM | 40 | 24/40 | ✓ | — | `DSMM902` |
| `DSM905` | DSM | 27 | 12/27 | ✓ | `DSMM903` | — |
| `DSM9051` | DSM | 25 | 10/25 | ✓ | — | `DSMM903` |
| `FSK005` | — | 0 | — | ? | `FSKM004` | — |
| `HIGHRISK_COUNTRY` | OFD | 23 | 23/23 | ✓ | `OFDM157` | — |
| `OFD001` | — | 0 | — | ? | `OFDM001` | — |
| `OFD002` | OFD | 28 | 9/28 | ✓ | `OFDM002` | — |
| `OFD003A` | — | 0 | — | ? | `OFDM003` | — |
| `OFD004` | — | 0 | — | ? | `OFDM004` | — |
| `OFD005` | — | 0 | — | ? | `OFDM005` | — |
| `OFD006A` | — | 0 | — | ? | `OFDM006` | — |
| `OFD007A` | — | 0 | — | ? | `OFDM007` | — |
| `OFD009` | — | 0 | — | ? | `OFDM009` | — |
| `OFD010` | — | 0 | — | ? | `OFDM010` | — |
| `OFD011` | — | 0 | — | ? | `OFDM011` | — |
| `OFD012A` | — | 0 | — | ? | `OFDM012` | — |
| `OFD013A` | — | 0 | — | ? | `OFDM013` | — |
| `OFD014` | — | 0 | — | ? | `OFDM014` | — |
| `OFD015` | OFD | 21 | 3/21 | ✓ | `OFDM015` | — |
| `OFD016` | OFD | 23 | 5/23 | ✓ | — | `OFDM015` |
| `OFD017A` | — | 0 | — | ? | `OFDM017` | — |
| `OFD017B` | — | 0 | — | ? | `OFDM017B` | — |
| `OFD019A` | — | 0 | — | ? | `OFDM019` | — |
| `OFD020` | — | 0 | — | ? | `OFDM383` | — |
| `OFD020A` | — | 0 | — | ? | `OFDM020` | — |
| `OFD022` | — | 0 | — | ? | `OFDM022` | — |
| `OFD023A` | — | 0 | — | ? | `OFDM023` | — |
| `OFD024A` | — | 0 | — | ? | `OFDM024` | — |
| `OFD025A` | — | 0 | — | ? | `OFDM025` | — |
| `OFD026` | — | 0 | — | ? | `OFDM026` | — |
| `OFD027A` | — | 0 | — | ? | `OFDM027` | — |
| `OFD028` | — | 0 | — | ? | `OFDM028` | — |
| `OFD029` | — | 0 | — | ? | `OFDM029` | — |
| `OFD030` | — | 0 | — | ? | `OFDM030` | — |
| `OFD034A` | — | 0 | — | ? | `OFDM034` | — |
| `OFD035A` | — | 0 | — | ? | `OFDM035` `OFDM036` | — |
| `OFD036A` | — | 0 | — | ? | — | `OFDM035` `OFDM036` |
| `OFD038A` | — | 0 | — | ? | `OFDM038` | `OFDB004` |
| `OFD039A` | — | 0 | — | ? | `OFDM039` | — |
| `OFD040A` | — | 0 | — | ? | `OFDM040` | — |
| `OFD041A` | — | 0 | — | ? | `OFDM041` | — |
| `OFD045` | — | 0 | — | ? | `OFDM045` | — |
| `OFD046` | OFD | 19 | 4/19 | ✓ | `OFDM046` | — |
| `OFD047` | OFD | 19 | 3/19 | ✓ | — | `OFDM046` |
| `OFD054A` | BMS OFD | 19 | 4/19 | ✓ | `OFDM054` | — |
| `OFD055A` | — | 0 | — | ? | `OFDM055` | — |
| `OFD061` | OFD | 26 | 21/26 | ✓ | `OFDM061` | — |
| `OFD062` | OFD | 37 | 19/37 | ✓ | `OFDM062` | — |
| `OFD063` | OFD | 33 | 15/33 | ✓ | — | `OFDM062` |
| `OFD064` | — | 0 | — | ? | `OFDM064` | — |
| `OFD065` | — | 0 | — | ? | `OFDM065` | — |
| `OFD066` | OFD | 25 | 7/25 | ✓ | `OFDM066` | — |
| `OFD067` | OFD | 28 | 10/28 | ✓ | — | `OFDM066` |
| `OFD068A` | — | 0 | — | ? | `OFDM068` | — |
| `OFD069A` | — | 0 | — | ? | — | `OFDM068` |
| `OFD070` | — | 0 | — | ? | `OFDM070B` | — |
| `OFD070A` | — | 0 | — | ? | `OFDM070A` | `OFDB004` |
| `OFD071` | — | 0 | — | ? | `OFDM385` | — |
| `OFD071A` | — | 0 | — | ? | `OFDM071` | — |
| `OFD072A` | — | 0 | — | ? | `OFDM072` | — |
| `OFD074` | — | 0 | — | ? | `OFDB004` `OFDM074` | `OFDB004` |
| `OFD075` | — | 0 | — | ? | — | `OFDB004` `OFDM074` |
| `OFD076` | — | 0 | — | ? | `OFDB004` `OFDM076` | `OFDB004` |
| `OFD077` | — | 0 | — | ? | — | `OFDB004` `OFDM076` |
| `OFD078` | — | 0 | — | ? | — | `OFDM074` `OFDM076` |
| `OFD081` | OFD TRP OTA RSP | 26 | 20/26 | — | `OFDM081B` | — |
| `OFD0811A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD0813A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD0814A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD0819A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD081A` | OFD | 2 | 2/2 | — | `OFDB002` `OFDB004` `OFDM081A` | — |
| `OFD082` | — | 0 | — | ? | — | `OFDM081B` |
| `OFD082A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD083` | — | 0 | — | ? | — | `OFDM081B` |
| `OFD084A` | — | 0 | — | ? | `OFDM084` | `OFDM081A` |
| `OFD085` | OFD | 8 | 8/8 | — | `OFDM085B` | — |
| `OFD085A` | — | 0 | — | ? | `OFDM085A` | `OFDB004` |
| `OFD086` | OFD | 4 | 4/4 | — | `OFDM086` | — |
| `OFD088A` | — | 0 | — | ? | `OFDM088` | — |
| `OFD091` | OFD | 21 | 15/21 | ✓ | `OFDM091B` | — |
| `OFD091A` | — | 0 | — | ? | `OFDM091` | — |
| `OFD092A` | — | 0 | — | ? | — | `OFDM091` |
| `OFD094A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD095A` | — | 0 | — | ? | — | `OFDM081A` |
| `OFD104` | BMS OFD | 28 | 10/28 | ✓ | — | `OFDM053` |
| `OFD109` | BMS OFD | 23 | 5/23 | ✓ | `OFDM109` | — |
| `OFD110` | BMS OFD | 58 | 24/58 | ✓ | — | `OFDM109` |
| `OFD111` | BMS OFD | 22 | 4/22 | ✓ | `OFDM111` | — |
| `OFD112` | BMS OFD | 46 | 12/46 | ✓ | — | `OFDM111` |
| `OFD113` | OFD | 31 | 13/31 | ✓ | `OFDM113` | — |
| `OFD114A` | — | 0 | — | ? | `OFDM114` | — |
| `OFD115A` | — | 0 | — | ? | `OFDM115A` | — |
| `OFD116A` | — | 0 | — | ? | — | `OFDM115A` |
| `OFD122A` | — | 0 | — | ? | `OFDM122A` | — |
| `OFD123A` | BMS | 123 | 6/123 | ✓ | `OFDM123A` | — |
| `OFD124` | BMS OFD | 41 | 24/41 | ✓ | `OFDM123` | — |
| `OFD124A` | OFD | 30 | 15/30 | ✓ | — | `OFDM123A` |
| `OFD125` | OFD | 31 | 1/31 | ✓ | — | `OFDM123` |
| `OFD125A` | — | 0 | — | ? | — | `OFDM125A` |
| `OFD125A_M` | — | 0 | — | ? | `OFDM125A` | — |
| `OFD126A` | OFD | 20 | 20/20 | ✓ | `OFDM126` | — |
| `OFD127` | — | 0 | — | ? | `OFDM127` | — |
| `OFD128` | — | 0 | — | ? | `OFDM128` | — |
| `OFD129A` | — | 0 | — | ? | `OFDM129` | `OFDB004` |
| `OFD130ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `OFD131ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `OFD132A` | — | 0 | — | ? | — | `BMSM001` `BMSM006` |
| `OFD132ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `OFD133A` | — | 0 | — | ? | `OFDM133` | — |
| `OFD135A` | — | 0 | — | ? | `OFDM135` | — |
| `OFD136A` | OFD | 19 | 3/19 | ✓ | — | `OFDM221A` `OFDM231A` |
| `OFD137ACHG` | BMS | 23 | 8/23 | ✓ | — | `BMSM006` |
| `OFD138ACHG` | BMS | 45 | 29/45 | ✓ | — | `BMSM006` |
| `OFD139ACHG` | BMS | 23 | 7/23 | ✓ | — | `BMSM006` |
| `OFD151A` | — | 0 | — | ? | `OFDM151` | — |
| `OFD152A` | — | 0 | — | ? | — | `OFDM151` |
| `OFD153A` | — | 0 | — | ? | — | `OFDM151` |
| `OFD154` | — | 0 | — | ? | `OFDM154` | — |
| `OFD155` | — | 0 | — | ? | `OFDM155` | — |
| `OFD156A` | OFD | 30 | 30/30 | ✓ | `OFDM156` | — |
| `OFD157A` | OFD | 18 | 18/18 | ✓ | — | `OFDM156` |
| `OFD161` | — | 0 | — | ? | `OFDM161` | — |
| `OFD163` | — | 0 | — | ? | `OFDM163` | — |
| `OFD164` | — | 0 | — | ? | `OFDM164` | — |
| `OFD190A` | — | 0 | — | ? | — | `OFDI199` |
| `OFD190A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD190A_UPD` | — | 0 | — | ? | — | `OFDM199` |
| `OFD191` | — | 0 | — | ? | `OFDM191` | — |
| `OFD192` | — | 0 | — | ? | `OFDM192` | — |
| `OFD193A` | — | 0 | — | ? | `OFDM193` | `OFDB004` |
| `OFD194` | — | 0 | — | ? | `OFDM194B` | — |
| `OFD194A` | — | 0 | — | ? | `OFDM194` | `OFDB004` |
| `OFD195` | — | 0 | — | ? | `OFDB005` | — |
| `OFD195A` | — | 0 | — | ? | `OFDM195` | — |
| `OFD196A` | — | 0 | — | ? | `OFDM196` | `OFDB004` |
| `OFD197A` | — | 0 | — | ? | `OFDM197` | — |
| `OFD198` | — | 0 | — | ? | `OFDM198` | — |
| `OFD199` | OFD | 27 | 9/27 | ✓ | `OFDM199A` | — |
| `OFD199A` | — | 0 | — | ? | `OFDI199` | — |
| `OFD199A_TMP` | — | 0 | — | ? | `OFDM199A` | — |
| `OFD199A_UPD` | — | 0 | — | ? | `OFDM199` | — |
| `OFD200` | OFD | 26 | 8/26 | ✓ | — | `OFDM199A` |
| `OFD200A` | — | 0 | — | ? | — | `OFDI199` |
| `OFD200A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD200A_UPD` | — | 0 | — | ? | — | `OFDM199` |
| `OFD201A` | — | 0 | — | ? | — | `OFDI199` `OFDM199` |
| `OFD201A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD202A` | — | 0 | — | ? | — | `OFDI199` `OFDM199` |
| `OFD202A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD203A` | — | 0 | — | ? | — | `OFDI199` `OFDM199` |
| `OFD203A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD204` | — | 0 | — | ? | `OFDM204` | — |
| `OFD205` | OFD | 18 | 3/18 | ✓ | — | `OFDM204` |
| `OFD206` | BMS | 21 | 6/21 | ✓ | `OFDM206` | `BMSM001` |
| `OFD213A` | — | 0 | — | ? | `OFDM213` | `OFDB004` |
| `OFD214A` | — | 0 | — | ? | `OFDM214` | `OFDB004` |
| `OFD215A` | — | 0 | — | ? | `OFDM215` | `OFDB004` |
| `OFD220` | OFD | 39 | 20/39 | ✓ | `OFDM221C` | — |
| `OFD220A` | — | 0 | — | ? | `OFDB310` `OFDM221A` | `BBSM013` `BBSM113` `OFDB331` `OFDM231A` |
| `OFD220A_AGENT` | OFD | 17 | 2/17 | ✓ | — | `OFDM221A` |
| `OFD221` | OFD | 147 | 122/147 | ✓ | — | `OFDM221C` |
| `OFD221A` | OFD | 13 | 7/13 | — | `OFDB302` `OFDB304` `OFDB306` `OFDI059` …+1 | `BBSM013` `BBSM113` `OFDB310` `OFDB331` …+2 |
| `OFD232A` | — | 0 | — | ? | `OFDM220` | — |
| `OFD233A` | — | 0 | — | ? | `OFDB303` | — |
| `OFD234A` | — | 0 | — | ? | — | `BBSM013` `BBSM113` `OFDM221A` |
| `OFD235A` | — | 0 | — | ? | — | `BBSM013` `BBSM113` `OFDM221A` |
| `OFD243A` | — | 0 | — | ? | `OFDM243A` | `OFDM221A` `OFDM231A` |
| `OFD251` | OFD | 152 | 129/152 | ✓ | `OFDM231B` | — |
| `OFD251A` | OFD | 73 | 4/73 | ✓ | `OFDB321` `OFDB322` `OFDB324` `OFDB325` …+6 | — |
| `OFD251A_AGENT` | — | 0 | — | ? | — | `OFDM231A` |
| `OFD252` | OFD | 190 | 161/190 | ✓ | — | `OFDM231B` |
| `OFD252A` | OFD | 69 | 0/69 | ✓ | `OFDM242` | `OFDB331` `OFDM231A` |
| `OFD253` | OFD | 174 | 153/174 | ✓ | — | `OFDM231B` |
| `OFD253A` | — | 0 | — | ? | — | `OFDB331` `OFDM231A` |
| `OFD254` | OFD | 54 | 33/54 | ✓ | — | `OFDM231B` |
| `OFD254A` | OFD | 28 | 0/28 | ✓ | `OFDM242` | `OFDM231A` |
| `OFD258A` | — | 0 | — | ? | — | `OFDM231A` |
| `OFD259A` | — | 0 | — | ? | `OFDM232` | — |
| `OFD260A` | — | 0 | — | ? | `OFDB004` `OFDM233` | `OFDB004` |
| `OFD261A` | — | 0 | — | ? | — | `OFDB004` `OFDM233` |
| `OFD264A` | — | 0 | — | ? | `OFDM264` | — |
| `OFD265A` | — | 0 | — | ? | — | `OFDM264` |
| `OFD266A` | — | 0 | — | ? | — | `OFDM264` |
| `OFD270A` | BMS | 2 | 2/2 | — | `OFDM270` | — |
| `OFD272` | BMS OFD RSP | 43 | 13/43 | ✓ | — | `OFDB310` |
| `OFD272A` | — | 0 | — | ? | — | `BMSM004` `BMSM006` `OFDM221A` `OFDM231A` …+2 |
| `OFD272ACHG` | — | 0 | — | ? | — | `BMSM006` |
| `OFD281` | OFD | 35 | 17/35 | ✓ | `OFDM251` | — |
| `OFD281A` | — | 0 | — | ? | `OFDB281` `OFDM281` | — |
| `OFD283A` | — | 0 | — | ? | `OFDM287` | — |
| `OFD286A` | — | 0 | — | ? | `OFDM284` | — |
| `OFD287A` | — | 0 | — | ? | — | `OFDB281` `OFDM281` |
| `OFD288A` | — | 0 | — | ? | — | `OFDM281` |
| `OFD290A` | — | 0 | — | ? | `OFDM285` | — |
| `OFD291` | — | 0 | — | ? | `OFDM286` | — |
| `OFD297A` | — | 0 | — | ? | `OFDB002` `OFDM297` | — |
| `OFD300` | OFD | 7 | 7/7 | — | `OFDM300` | — |
| `OFD301` | OFD | 7 | 7/7 | — | `OFDM301` | — |
| `OFD302` | OFD OTA RSP | 44 | 12/44 | ✓ | `OFDM302B` | — |
| `OFD302A` | NFD | 2 | 0/2 | — | `OFDM302` | — |
| `OFD312` | NFD | 2 | 2/2 | — | `OFDB001` | — |
| `OFD321` | — | 0 | — | ? | `OFDM321` | — |
| `OFD322` | — | 0 | — | ? | — | `OFDM321` |
| `OFD331` | — | 0 | — | ? | `OFDM331` | — |
| `OFD332` | — | 0 | — | ? | — | `OFDM331` |
| `OFD333` | — | 0 | — | ? | — | `OFDM331` |
| `OFD334` | — | 0 | — | ? | — | `OFDM331` |
| `OFD335` | — | 0 | — | ? | — | `OFDM331` |
| `OFD337A` | — | 0 | — | ? | `OFDM337` | — |
| `OFD342` | OFD | 27 | 11/27 | ✓ | `OFDB011` | — |
| `OFD344` | — | 0 | — | ? | `OFDM344` | — |
| `OFD346A` | — | 0 | — | ? | — | `OFDM337` |
| `OFD369A` | OFD | 29 | 14/29 | ✓ | `OFDM369` | — |
| `OFD371` | — | 0 | — | ? | `OFDM371` | — |
| `OFD372` | — | 0 | — | ? | — | `OFDM371` |
| `OFD373` | — | 0 | — | ? | — | `OFDM371` |
| `OFD374` | BMS RSP | 34 | 0/34 | ✓ | `OFDM374` | — |
| `OFD374A` | DSM | 22 | 7/22 | ✓ | `DSMM060` | `BMSM001` `BMSM006` |
| `OFD375A` | — | 0 | — | ? | `OFDM375` | — |
| `OFD376` | — | 0 | — | ? | `OFDM376` | — |
| `OFD377` | — | 0 | — | ? | `OFDM377` | — |
| `OFD381` | — | 0 | — | ? | `OFDM382` | — |
| `OFD391A` | — | 0 | — | ? | `OFDM391` | — |
| `OFD392A` | — | 0 | — | ? | `OFDM392` | — |
| `OFD393A` | — | 0 | — | ? | — | `OFDM392` |
| `OFD394A` | — | 0 | — | ? | — | `OFDM392` |
| `OFD395A` | — | 0 | — | ? | `OFDM395` | — |
| `OFD399A` | — | 0 | — | ? | `OFDM399` | — |
| `OFD429A` | OFD | 19 | 4/19 | ✓ | `OFDM430` | — |
| `OFD431A` | OFD | 20 | 5/20 | ✓ | `OFDM431` `OFDM431bb` | — |
| `OFD432A` | OFD | 29 | 29/29 | ✓ | `OFDB431` `OFDM432` | — |
| `OFD435A` | OFD | 21 | 21/21 | ✓ | `OFDM435` | — |
| `OFD436A` | — | 0 | — | ? | `OFDM433` | — |
| `OFD437A` | OFD | 29 | 29/29 | ✓ | `OFDB433` `OFDM434` | — |
| `OFD440A` | OFD | 20 | 20/20 | ✓ | `OFDM436` | — |
| `OFD484A` | OFD | 31 | 17/31 | ✓ | `OFDM485` | — |
| `OFD494A` | OFD | 31 | 31/31 | ✓ | `OFDM481A` | — |
| `OFD496A` | OFD | 52 | 48/52 | ✓ | `OFDM482A` | — |
| `OFD531` | — | 0 | — | ? | `OFDM531` | — |
| `OFD540A` | OFD | 86 | 85/86 | ✓ | `OFDM540` | — |
| `OFD541A` | — | 0 | — | ? | `OFDM541` `OFDM542` | — |
| `OFD542A` | — | 0 | — | ? | `OFDM543` | — |
| `OFD551` | OFD | 44 | 26/44 | ✓ | `OFDM551` | — |
| `OFD552` | OFD | 73 | 54/73 | ✓ | — | `OFDM551` |
| `OFD554` | OFD | 40 | 21/40 | ✓ | `OFDM554` | — |
| `OFD555` | OFD | 74 | 52/74 | ✓ | — | `OFDM554` |
| `OFD561` | BMS OFD | 23 | 5/23 | ✓ | `OFDM561` | — |
| `OFD562` | BMS OFD | 78 | 39/78 | ✓ | `OFDM562` | `OFDM561` |
| `OFD601` | BMS OFD | 207 | 0/207 | ✓ | — | `BMSM001` `BMSM006` |
| `OFD603` | BMS OFD | 25 | 8/25 | ✓ | — | `OFDM053` |
| `OFD605` | OFD | 23 | 5/23 | ✓ | `OFDM602A` | `OFDM053` |
| `OFD607` | BMS OFD | 60 | 45/60 | ✓ | — | `OFDM053` |
| `OFD607A` | BMS OFD | 74 | 15/74 | ✓ | — | `BMSM001` `BMSM006` |
| `OFD607ACHG` | BMS | 99 | 4/99 | ✓ | — | `BMSM006` |
| `OFD608A` | — | 0 | — | ? | `OFDM607` | — |
| `OFD681` | OFD RSP | 2 | 0/2 | — | `OFDM681` | — |
| `OFD687A` | — | 0 | — | ? | — | `OFDI199` `OFDM199` |
| `OFD687A_TMP` | — | 0 | — | ? | — | `OFDM199A` |
| `OFD694A` | — | 0 | — | ? | `OFDM694B` | — |
| `OFD700` | — | 0 | — | ? | `OFDM700` | — |
| `OFD702` | OFD | 27 | 27/27 | — | `OFDM714` | — |
| `OFD708` | OFD | 31 | 24/31 | ✓ | `OFDB901` | — |
| `OFD710A` | — | 0 | — | ? | `OFDM710` | — |
| `OFD711` | NFD | 2 | 2/2 | — | `OFDM711` | — |
| `OFD712` | — | 0 | — | ? | `OFDM712` | — |
| `OFD713` | OFD | 3 | 3/3 | — | `OFDM713` | — |
| `OFD721` | BBS OFD | 10 | 9/10 | — | `OFDM721` `OFDM725` | — |
| `OFD722` | — | 0 | — | ? | `OFDM722` | — |
| `OFD724` | — | 0 | — | ? | `OFDB327` `OFDM271` `OFDM723` `OFDM724` | — |
| `OFD731` | OFD | 26 | 12/26 | ✓ | `OFDM731` | — |
| `OFD732` | — | 0 | — | ? | — | `OFDM731` |
| `OFD733` | — | 0 | — | ? | `OFDB731` | — |
| `OFD741` | OFD | 4 | 4/4 | — | `OFDM741` | — |
| `OFD742` | — | 0 | — | ? | — | `OFDM741` |
| `OFD743` | OFD | 21 | 6/21 | ✓ | `OFDM742` | — |
| `OFD744` | OFD | 22 | 7/22 | ✓ | — | `OFDM742` |
| `OFD745` | OFD | 22 | 0/22 | ✓ | — | `OFDM742` |
| `OFD746` | — | 0 | — | ? | `OFDM743` | — |
| `OFD747` | OFD | 22 | 7/22 | ✓ | — | `OFDM743` |
| `OFD751` | — | 0 | — | ? | `OFDM751` | — |
| `OFD871` | — | 0 | — | ? | `OFDB871` `OFDM871` | — |
| `OFD872` | — | 0 | — | ? | `OFDB871` `OFDM872` | — |
| `OFD907` | OFD | 21 | 6/21 | ✓ | `OFDM907` `OFDM913` | — |
| `OFD913A_UPD` | OFD | 28 | 13/28 | ✓ | `OFDM913A` | — |
| `OFD931A` | — | 0 | — | ? | `OFDM931A` `OFDM931B` | — |
| `RSP005` | OFD RSP | 88 | 71/88 | ✓ | `RSPM037` | — |
| `RSP005A` | — | 0 | — | ? | `RSPB009` `RSPB020` `RSPM004` | — |
| `RSP006` | — | 0 | — | ? | `RSPM037` | — |
| `RSP006A` | BMS OFD | 10 | 10/10 | — | — | `RSPB009` `RSPB020` `RSPM004` |
| `RSP007A` | RSP | 27 | 8/27 | ✓ | `RSPB008` `RSPM005` | — |
| `RSP008` | RSP | 55 | 1/55 | ✓ | `RSPB010` | — |
| `RSP008A` | — | 0 | — | ? | `RSPB011` `RSPB015` `RSPB016` `RSPB018` | — |
| `RSP008AA` | — | 0 | — | ? | `RSPB019` | — |
| `RSP013A` | — | 0 | — | ? | — | `RSPM005` |
| `RSP041A` | — | 0 | — | ? | `RSPM041` | — |
| `RSP042A` | — | 0 | — | ? | `RSPM042` | — |
| `RSP061A` | — | 0 | — | ? | `RSPM020` | — |
| `RSP062A` | — | 0 | — | ? | — | `RSPM020` |
| `RSP063A` | — | 0 | — | ? | — | `RSPM020` |
| `RSP070A` | — | 0 | — | ? | `RSPB025` `RSPM021` | — |
| `RSP071A` | — | 0 | — | ? | — | `RSPB025` `RSPM021` |
| `RSP072A` | — | 0 | — | ? | — | `RSPB025` `RSPM021` |
| `RSP073A` | — | 0 | — | ? | `RSPM022` | — |
| `RSP074A` | — | 0 | — | ? | — | `RSPM022` |
| `RSP075A` | — | 0 | — | ? | — | `RSPM022` |
| `SAL050` | DSM | 20 | 4/20 | ✓ | `DSMM050` | — |
| `SAL051` | DSM | 22 | 4/22 | ✓ | — | `DSMM050` |
| `SAL908A` | — | 0 | — | ? | `OFDM450` | — |
| `SAL909A` | OFD | 20 | 5/20 | ✓ | — | `OFDM450` |
| `SAL910A` | OFD | 18 | 3/18 | ✓ | — | `OFDM450` |
| `SAL911A` | OFD | 19 | 4/19 | ✓ | — | `OFDM450` |
| `SAL912A` | OFD | 18 | 3/18 | ✓ | — | `OFDM450` |
| `SAL913A` | OFD | 18 | 3/18 | ✓ | — | `OFDM450` |
| `SAL914A` | OFD | 21 | 6/21 | ✓ | — | `OFDM450` |
| `SAL915A` | — | 0 | — | ? | `OFDM458` | — |
| `SAL920A` | — | 0 | — | ? | `OFDM454` | — |
| `SAL921A` | OFD | 20 | 5/20 | ✓ | — | `OFDM454` |
| `SAL922A` | OFD | 18 | 3/18 | ✓ | — | `OFDM454` |
| `SAL923A` | OFD | 18 | 3/18 | ✓ | — | `OFDM454` |
| `SAL924A` | OFD | 18 | 3/18 | ✓ | — | `OFDM454` |
| `SAL925A` | — | 0 | — | ? | `OFDM456` | — |
| `SAL926A` | OFD | 20 | 5/20 | ✓ | — | `OFDM456` |
| `SAL927A` | OFD | 18 | 3/18 | ✓ | — | `OFDM456` |
| `SAL928A` | OFD | 18 | 3/18 | ✓ | — | `OFDM456` |
| `SAL929A` | OFD | 18 | 3/18 | ✓ | — | `OFDM456` |
| `SAL930A` | OFD | 21 | 6/21 | ✓ | — | `OFDM454` `OFDM456` |
| `SAL931A` | OFD | 25 | 9/25 | ✓ | `OFDB459` | — |
| `SAL932A` | OFD | 19 | 4/19 | ✓ | `OFDB459` | — |
| `TMK001A` | TMK | 50 | 49/50 | ✓ | `TMKM001` `TMKM002` | — |
| `TMK002A` | TMK | 32 | 32/32 | ✓ | — | `TMKM001` `TMKM002` |
| `TMK0031A` | TMK | 24 | 24/24 | ✓ | — | `TMKM001` `TMKM002` |
| `TMK003A` | TMK | 24 | 24/24 | ✓ | — | `TMKM001` `TMKM002` |
| `TMK901` | — | 0 | — | ? | `TMKM901` | — |
| `TRP011` | TRP | 36 | 16/36 | ✓ | `TRPM901` | — |
| `TRPARAMS` | OFD TRP | 21 | 3/21 | ✓ | `TRPM005` | — |

## 附錄 B SP / Function / Trigger / View

> 全部來自 `DB/` 底下的腳本檔。「真名」是從 `CREATE OR REPLACE` 抽出來的實際物件名,與檔名不符時要以真名為準。「被誰用」是掃 PO 的 SQL 字串比對出來的,**空白不代表沒人用**——可能由其他 SP 內部呼叫,或由排程直接叫。

| 類別 | 數量 |
|---|---|
| Stored Procedure | 83 |
| Function | 23 |
| Trigger | 13 |
| View | 2 |
| 合計 | 121 |

編碼分佈:`cp950` 117 支 · `utf-8-sig` 4 支。讀寫一律走 `atlas_scan.py` 的 `read_text()`,不要用 `utf-8` 硬讀。

### B.0 先講最重要的:`DB/` 只涵蓋 16% 的 SP

程式裡以 `GetStoredProcCommand("…")` 呼叫的相異 SP 有 **380** 支,而 `DB/SP` + `DB/Function` 合計只有 106 支腳本。**319 支(84%)在 repo 內完全找不到定義。**

這件事的後果比「表沒有 DDL」更嚴重:**批次與報表的商業邏輯大量住在 Oracle 的預存程序裡,而那些程序不在版控內**。看 `_PO.cs` 只看得到「呼叫了哪支 SP、傳了什麼參數」,看不到它做了什麼。要追批次邏輯,一定要連資料庫查 `ALL_SOURCE`。

| 缺口 | 數量 |
|---|---|
| 程式呼叫的相異 SP | 380 |
| repo 有腳本 | 61 |
| **repo 沒有腳本** | **319** |

前 15 支(依名稱排序,附首見呼叫點):

| SP | 首見於 |
|---|---|
| `GET_CPMB005` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:411` |
| `SEND_MAIL` | `Dev/Common/Source/Utility/TA.UtilityPO/CALLAPI_PO.cs:171` |
| `SP_FORTA_BATCH_SEND` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR022_PO.cs:121` |
| `S_CALPORTALLOWUNIT` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:869` |
| `S_CODM016` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:119` |
| `S_ECFUNGETACCOUNTDATA` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:72` |
| `S_EC_DDCT_P01` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:86` |
| `S_EC_IPJB601_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs:238` |
| `S_EC_IPJB602A_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:267` |
| `S_EC_IPJB604_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB624OracleDao.cs:223` |
| `S_EC_IPJB605_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:138` |
| `S_EC_IPJB606_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:192` |
| `S_EC_IPJR601_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR601OracleDao.cs:46` |
| `S_EC_IPJR602_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR602OracleDao.cs:47` |
| `S_EC_IPJR603_GET` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/OFDR603OracleDao.cs:46` |

> 反過來,`DB/` 裡也有腳本是**沒有任何 `_PO.cs` 呼叫**的——那不代表沒用,可能由其他 SP 內部呼叫或由排程直接叫,見下表「被哪些畫面的 PO 引用」欄的空白。

### B.1 Stored Procedure(83)

| 名稱 | 檔 | 編碼 | 檔名與真名相符 | 被哪些畫面的 PO 引用 |
|---|---|---|---|---|
| `S_OTA_EC_PROGRESS` | `DB/SP/S_OTA_EC_PROGRESS.SQL` | cp950 | ✓ | `OFDM053` |
| `S_OTA_OFDB061_EXE` | `DB/SP/S_OTA_OFDB061_EXE.sql` | cp950 | ✓ | `OFDB061` |
| `S_OTA_OFDB062_EXE` | `DB/SP/S_OTA_OFDB062_EXE.sql` | cp950 | ✓ | `OFDB062` |
| `S_OTA_OFDB065_EXE` | `DB/SP/S_OTA_OFDB065_EXE.SQL` | cp950 | ✓ | `OFDB065` `OFDB135` |
| `S_OTA_OFDB091_EXE` | `DB/SP/S_OTA_OFDB091_EXE.sql` | cp950 | ✓ | `OFDB091` |
| `S_OTA_OFDB092_EXE` | `DB/SP/S_OTA_OFDB092_EXE.sql` | cp950 | ✓ | `OFDB092` |
| `S_OTA_OFDB131_EXE` | `DB/SP/S_OTA_OFDB131_EXE.SQL` | cp950 | ✓ | `OFDB131` |
| `S_OTA_OFDB135_EXE` | `DB/SP/S_OTA_OFDB135_EXE.SQL` | cp950 | ✓ | `OFDB135` |
| `S_OTA_OFDB553_EXE` | `DB/SP/S_OTA_OFDB553_EXE.sql` | cp950 | ✓ | `OFDB553` |
| `S_OTA_OFDB600A_EXE` | `DB/SP/S_OTA_OFDB600A_EXE.sql` | cp950 | ✓ | `OFDB600A` |
| `S_OTA_OFDB601A_EXE` | `DB/SP/S_OTA_OFDB601A_EXE.sql` | cp950 | ✓ | `OFDB601A` |
| `S_OTA_OFDB602A_EXE` | `DB/SP/S_OTA_OFDB602A_EXE.sql` | cp950 | ✓ | `OFDB602A` |
| `S_OTA_OFDB603_EXE` | `DB/SP/S_OTA_OFDB603_EXE.sql` | cp950 | ✓ | `OFDB603` |
| `S_OTA_OFDB604A_EXE_ADD` | `DB/SP/S_OTA_OFDB604A_EXE_ADD.sql` | cp950 | ✓ | `OFDB604A` |
| `S_OTA_OFDB604A_EXE_MOD` | `DB/SP/S_OTA_OFDB604A_EXE_MOD.sql` | cp950 | ✓ | `OFDB604A` |
| `S_OTA_OFDB902_EXE` | `DB/SP/S_OTA_OFDB902_EXE.SQL` | cp950 | ✓ | — |
| `S_OTA_OFDB903_EXE` | `DB/SP/S_OTA_OFDB903_EXE.sql` | cp950 | ✓ | `OFDB903` |
| `S_OTA_OFDI011_GetRSPCHG` | `DB/SP/S_OTA_OFDI011_GetRSPCHG.SQL` | cp950 | ✓ | `OFDI011` |
| `S_OTA_OFDM231B_EXE_ADD` | `DB/SP/S_OTA_OFDM231B_EXE_ADD.SQL` | cp950 | ✓ | `OFDM231B` |
| `S_OTA_OFDM231B_EXE_MOD` | `DB/SP/S_OTA_OFDM231B_EXE_MOD.SQL` | cp950 | ✓ | `OFDM231B` |
| `S_OTA_OFDR001_GET` | `DB/SP/S_OTA_OFDR001_GET.SQL` | cp950 | ✓ | `OFDR001B` |
| `S_OTA_OFDR002_GET` | `DB/SP/S_OTA_OFDR002_GET.SQL` | cp950 | ✓ | `OFDR002` |
| `S_OTA_OFDR003_GET` | `DB/SP/S_OTA_OFDR003_GET.SQL` | cp950 | ✓ | `OFDR003` |
| `S_OTA_OFDR042_GET` | `DB/SP/S_OTA_OFDR042_GET.SQL` | cp950 | ✓ | `OFDR042` |
| `S_OTA_OFDR050_EXE` | `DB/SP/S_OTA_OFDR050_EXE.SQL` | cp950 | ✓ | `OFDR050` |
| `S_OTA_OFDR050_GET` | `DB/SP/S_OTA_OFDR050_GET.SQL` | cp950 | ✓ | `OFDR050` |
| `S_OTA_OFDR051_GET` | `DB/SP/S_OTA_OFDR051_GET.SQL` | cp950 | ✓ | `OFDR051` |
| `S_OTA_OFDR052_GET` | `DB/SP/S_OTA_OFDR052_GET.sql` | cp950 | ✓ | `OFDR052` |
| `S_OTA_OFDR054_GET` | `DB/SP/S_OTA_OFDR054_GET.SQL` | cp950 | ✓ | `OFDR054` |
| `S_OTA_OFDR057_GET` | `DB/SP/S_OTA_OFDR057_GET.sql` | cp950 | ✓ | `OFDR057` |
| `S_OTA_OFDR058_GET` | `DB/SP/S_OTA_OFDR058_GET.sql` | cp950 | ✓ | `OFDR058` |
| `S_OTA_OFDR081T1` | `DB/SP/S_OTA_OFDR081T1.sql` | cp950 | ✓ | — |
| `S_OTA_OFDR081_GET` | `DB/SP/S_OTA_OFDR081_GET.sql` | cp950 | ✓ | `OFDR081` |
| `S_OTA_OFDR085_GET` | `DB/SP/S_OTA_OFDR085_GET.sql` | cp950 | ✓ | `OFDR085` |
| `S_OTA_OFDR086_GET` | `DB/SP/S_OTA_OFDR086_GET.sql` | cp950 | ✓ | `OFDR086` |
| `S_OTA_OFDR088_GET` | `DB/SP/S_OTA_OFDR088_GET.sql` | cp950 | ✓ | `OFDR088` |
| `S_OTA_OFDR089_GET` | `DB/SP/S_OTA_OFDR089_GET.SQL` | cp950 | ✓ | `OFDR089` |
| `S_OTA_OFDR090_GET` | `DB/SP/S_OTA_OFDR090_GET.SQL` | cp950 | ✓ | `OFDR090` |
| `S_OTA_OFDR093_GET` | `DB/SP/S_OTA_OFDR093_GET.sql` | cp950 | ✓ | `OFDR093` |
| `S_OTA_OFDR094_GET` | `DB/SP/S_OTA_OFDR094_GET.sql` | cp950 | ✓ | `OFDR094` |
| `S_OTA_OFDR109_GET` | `DB/SP/S_OTA_OFDR109_GET.SQL` | cp950 | ✓ | `OFDR109` |
| `S_OTA_OFDR111_GET` | `DB/SP/S_OTA_OFDR111_GET.SQL` | cp950 | ✓ | `OFDR111` |
| `S_OTA_OFDR131_GET` | `DB/SP/S_OTA_OFDR131_GET.SQL` | cp950 | ✓ | `OFDR131` |
| `S_OTA_OFDR132_GET` | `DB/SP/S_OTA_OFDR132_GET.SQL` | cp950 | ✓ | `OFDR132` |
| `S_OTA_OFDR133_GET` | `DB/SP/S_OTA_OFDR133_GET.SQL` | cp950 | ✓ | `OFDR133` |
| `S_OTA_OFDR134_GET` | `DB/SP/S_OTA_OFDR134_GET.SQL` | cp950 | ✓ | `OFDR134` |
| `S_OTA_OFDR551_GET` | `DB/SP/S_OTA_OFDR551_GET.SQL` | cp950 | ✓ | `OFDR551` |
| `S_OTA_OFDR552_GET` | `DB/SP/S_OTA_OFDR552_GET.SQL` | cp950 | ✓ | `OFDM551` `OFDR552` |
| `S_OTA_OFDR553_GET` | `DB/SP/S_OTA_OFDR553_GET.SQL` | cp950 | ✓ | `OFDR553` |
| `S_OTA_OFDR554_GET` | `DB/SP/S_OTA_OFDR554_GET.sql` | cp950 | ✓ | `OFDR554` |
| `S_OTA_OFDR561_GET` | `DB/SP/S_OTA_OFDR561_GET.SQL` | cp950 | ✓ | `OFDR561` |
| `S_OTA_OFDR562_GET` | `DB/SP/S_OTA_OFDR562_GET.SQL` | cp950 | ✓ | `OFDR562` |
| `S_OTA_OFDR601A_GET` | `DB/SP/S_OTA_OFDR601A_GET.SQL` | cp950 | ✓ | `OFDR601A` |
| `S_OTA_OFDR601_GET` | `DB/SP/S_OTA_OFDR601_GET.SQL` | cp950 | `S_OTA_OFDR051_GET` | `OFDR051` |
| `S_OTA_OFDR602A_GET` | `DB/SP/S_OTA_OFDR602A_GET.SQL` | cp950 | ✓ | `OFDR602A` |
| `S_OTA_OFDR603A_GET` | `DB/SP/S_OTA_OFDR603A_GET.SQL` | cp950 | ✓ | `OFDR603A` |
| `S_OTA_OFDR604A_GET` | `DB/SP/S_OTA_OFDR604A_GET.SQL` | cp950 | ✓ | `OFDR604A` |
| `S_OTA_OFDR605A_GET` | `DB/SP/S_OTA_OFDR605A_GET.SQL` | cp950 | ✓ | `OFDR605A` |
| `S_OTA_OFDR606A_GET` | `DB/SP/S_OTA_OFDR606A_GET.SQL` | cp950 | ✓ | `OFDR606A` |
| `S_OTA_OFDR901A_GET` | `DB/SP/S_OTA_OFDR901A_GET.SQL` | cp950 | ✓ | `OFDR901A` |
| `S_OTA_OFDR904_GET` | `DB/SP/S_OTA_OFDR904_GET.sql` | cp950 | ✓ | `OFDR904` |
| `S_OTA_TRPM901_EXE` | `DB/SP/S_OTA_TRPM901_EXE.SQL` | cp950 | ✓ | `TRPM901` |
| `S_OTA_TRPR001_GET` | `DB/SP/S_OTA_TRPR001_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP019TMP_GET` | `DB/SP/S_OTA_TTP019TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP111TMP_GET` | `DB/SP/S_OTA_TTP111TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP113TMP_GET` | `DB/SP/S_OTA_TTP113TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP114TMP_GET` | `DB/SP/S_OTA_TTP114TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP115TMP_GET` | `DB/SP/S_OTA_TTP115TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP116TMP_GET` | `DB/SP/S_OTA_TTP116TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP117TMP_GET` | `DB/SP/S_OTA_TTP117TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP118TMP_GET` | `DB/SP/S_OTA_TTP118TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP123TMP_GET` | `DB/SP/S_OTA_TTP123TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP124TMP_GET` | `DB/SP/S_OTA_TTP124TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP125TMP_GET` | `DB/SP/S_OTA_TTP125TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP126TMP_GET` | `DB/SP/S_OTA_TTP126TMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP12ATMP_GET` | `DB/SP/S_OTA_TTP12ATMP_GET.SQL` | cp950 | ✓ | — |
| `S_OTA_TTP12CTMP_GET` | `DB/SP/S_OTA_TTP12CTMP_GET.SQL` | cp950 | ✓ | — |
| `S_TA_DSMB001_EXCUTE_P01` | `DB/SP/S_TA_DSMB001_EXCUTE_P01.SQL` | cp950 | ✓ | `DSMB001` |
| `S_TA_IMP_OFD302_RANGE` | `DB/SP/S_TA_IMP_OFD302_RANGE.SQL` | cp950 | ✓ | — |
| `S_TA_NFDR073_1_GET` | `DB/SP/S_TA_NFDR073_1_GET.SQL` | cp950 | ✓ | `NFDR073A` |
| `S_TA_OFDI011_GETOFFFUND` | `DB/SP/S_TA_OFDI011_GETOFFFUND.sql` | cp950 | ✓ | `OFDI011` |
| `S_TA_OPEN_ACC_NOTIFY` | `DB/SP/S_TA_OPEN_ACC_NOTIFY.sql` | cp950 | ✓ | — |
| `s_OTA_GetFNBusinessDay` | `DB/SP/s_OTA_GetFNBusinessDay.SQL` | cp950 | ✓ | — |

### B.2 Function(23)

| 名稱 | 檔 | 編碼 | 檔名與真名相符 | 被哪些畫面的 PO 引用 |
|---|---|---|---|---|
| `F_OTA_GETFNBUSINESSDAY` | `DB/Function/F_OTA_GETFNBUSINESSDAY.SQL` | cp950 | ✓ | — |
| `F_OTA_GET_CRNCYAMTDEC` | `DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL` | utf-8-sig | ✓ | — |
| `F_OTA_GetDefFeeRate` | `DB/Function/F_OTA_GetDefFeeRate.SQL` | cp950 | ✓ | — |
| `GETCLASSNAMECHT` | `DB/Function/GETCLASSNAMECHT.SQL` | cp950 | ✓ | `OFDI011` `OFDI531` |
| `GET_NAV_DATE` | `DB/Function/GET_NAV_DATE.SQL` | cp950 | ✓ | — |
| `GET_REMIT_ACC_NO` | `DB/Function/GET_REMIT_ACC_NO.SQL` | cp950 | ✓ | — |
| `HIDE_PHONE_NO` | `DB/Function/HIDE_PHONE_NO.SQL` | cp950 | ✓ | — |
| `TTP019TMP_F2` | `DB/Function/TTP019TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP111TMP_F1` | `DB/Function/TTP111TMP_F1.SQL` | cp950 | ✓ | — |
| `TTP111TMP_F2` | `DB/Function/TTP111TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP113TMP_F2` | `DB/Function/TTP113TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP116TMP_F2` | `DB/Function/TTP116TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP117TMP_F2` | `DB/Function/TTP117TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP118TMP_F2` | `DB/Function/TTP118TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP124TMP_F1` | `DB/Function/TTP124TMP_F1.SQL` | cp950 | ✓ | — |
| `TTP126TMP_F1` | `DB/Function/TTP126TMP_F1.SQL` | cp950 | ✓ | — |
| `TTP126TMP_F2` | `DB/Function/TTP126TMP_F2.SQL` | cp950 | ✓ | — |
| `TTP12ATMP_F1` | `DB/Function/TTP12ATMP_F1.SQL` | cp950 | ✓ | — |
| `TTP12ATMP_F2` | `DB/Function/TTP12ATMP_F2.SQL` | cp950 | ✓ | — |
| `TTP12ATMP_P2` | `DB/Function/TTP12ATMP_P2.SQL` | cp950 | ✓ | — |
| `f_OTA_GetNavDate` | `DB/Function/f_OTA_GetNavDate.SQL` | cp950 | ✓ | `OFDB135` |
| `f_OTA_GetTradeNav` | `DB/Function/f_OTA_GetTradeNav.SQL` | utf-8-sig | ✓ | `OFDB135` |
| `f_OTA_GetTradeNavLock` | `DB/Function/f_OTA_GetTradeNavLock.SQL` | utf-8-sig | ✓ | `OFDB135` |

### B.3 Trigger(13)

| 名稱 | 檔 | 編碼 | 檔名與真名相符 | 被哪些畫面的 PO 引用 |
|---|---|---|---|---|
| `BMS001A_TDCC_BF_NO` | `DB/Trigger/BMS001A_TDCC_BF_NO.SQL` | cp950 | ✓ | — |
| `BMS001A_TSCDLOG` | `DB/Trigger/BMS001A_TSCDLOG.SQL` | cp950 | ✓ | — |
| `OFD002_T01` | `DB/Trigger/OFD002_T01.SQL` | cp950 | ✓ | — |
| `OFD109_T02` | `DB/Trigger/OFD109_T02.SQL` | cp950 | ✓ | — |
| `OFD110_T01` | `DB/Trigger/OFD110_T01.SQL` | cp950 | ✓ | — |
| `OFD113_T1` | `DB/Trigger/OFD113_T1.sql` | utf-8-sig | ✓ | — |
| `OFD253_T01` | `DB/Trigger/OFD253_T01.sql` | cp950 | ✓ | — |
| `OFD254_T01` | `DB/Trigger/OFD254_T01.SQL` | cp950 | ✓ | — |
| `OFD561_T02` | `DB/Trigger/OFD561_T02.SQL` | cp950 | ✓ | — |
| `OFD562_T01` | `DB/Trigger/OFD562_T01.SQL` | cp950 | ✓ | — |
| `OFD562_T02` | `DB/Trigger/OFD562_T02.SQL` | cp950 | ✓ | — |
| `OFD607_T02` | `DB/Trigger/OFD607_T02.sql` | cp950 | ✓ | — |
| `OFD607_T03` | `DB/Trigger/OFD607_T03.sql` | cp950 | ✓ | — |

### B.4 View(2)

| 名稱 | 檔 | 編碼 | 檔名與真名相符 | 被哪些畫面的 PO 引用 |
|---|---|---|---|---|
| `FNDV01` | `DB/View/FNDV01.SQL` | cp950 | ✓ | `OFDM053` `OFDM111` |
| `OFD068A_V02` | `DB/View/OFD068A_V02.SQL` | cp950 | ✓ | `DSMM901` `DSMM903` `OFDI011` |

### B.5 `DB/Table/` 的變更腳本(156 支)

這裡放的**不是 DDL 定義**,是歷次異動的票號腳本。其中 58 支含 `CREATE TABLE`,其餘是 `INSERT` / `ALTER` / 資料補正。

| 特徵 | 數量 |
|---|---|
| 總數 | 156 |
| 含 `CREATE TABLE` | 58 |
| 檔名含 `rollback` | 10 |
| 編碼 `cp950` | 79 |
| 編碼 `utf-8-sig` | 77 |

**所以 repo 內沒有任何一份可信的完整 schema。**要知道一張表現在長什麼樣,只有兩條路:查資料庫,或看 xsd(而 xsd 只涵蓋 177 / 413 張表)。詳見 §5。

## 附錄 C 黑箱清單(PTPFBlock)

### C.1 規模:118 支

`/CLAUDE.md` 列了六支代表性的 DLL,那是最常用的幾支,不是全部。實掃結果:全 repo 的 `.csproj` 對 `C:\Program Files\Vendor\PTPFBlock\` 底下的檔案共有 **1,347 筆參考,指向 118 個相異 DLL**,其中 65 支是 Vendor 自家的、53 支是第三方。

**這些檔案本機沒有,所以本機編不起來。**這不是設定問題,是缺件。

### C.2 六層基底來自哪一支

| 基底類別 | 出自 | 被誰繼承 |
|---|---|---|
| `Basic_Pxy` | `Vendor.Product.FormProxy.dll`(64 筆參考) | 所有 `*_Pxy`,如 `Dev/Common/Source/Utility/TA.UtilityProxy/Utility_Pxy.cs:11` |
| `BasicModelVDB` | `Vendor.Product.Entity.DataEntity.dll`(107 筆) | 所有 `*ModelVDB`,如 `Dev/Common/Source/Utility/TA.DataEntity.Utility/UtilityModelVDB.cs:8` |
| `BasicViewVDB` | `Vendor.Product.Entity.UIEntity.dll`(141 筆,**參考數第一**) | 所有 `*ViewVDB`,如 `Dev/Common/Source/Utility/TA.UIEntity.Utility/UtilityViewVDB.cs:9` |
| `EVAType` 等型別 | `Vendor.Product.DataAccess.dll`(59 筆) | 四眼引擎,見 §3 |

**以上四項都標「無原始碼,從呼叫端反推」。**本文任何關於它們行為的敘述,都是從繼承鏈、方法呼叫與參數型別推回去的,不是讀過實作。

### C.3 Vendor 自家 DLL(依參考數,前 20)

| DLL(省略 `Vendor.` 前綴與 `.dll`) | 參考數 | 推測用途 |
|---|---|---|
| `Product.Entity.UIEntity` | 141 | UIEntity 基底 |
| `Product.Utility` | 120 | 通用工具 |
| `Product.Entity.DataEntity` | 107 | DataEntity 基底 |
| `Product.Framework.Exceptions` | 90 | 例外框架,**但 repo 內有原始碼**,見 C.5 |
| `Product.FormProxy` | 64 | FormProxy 基底 |
| `Product.DataAccess` | 59 | 資料存取基底 |
| `Product.Utility.MappingCode` | 45 | 代碼對照 |
| `Fusion.Common` | 43 | Fusion 框架核心 |
| `Fusion.DataAccess` | 37 | Fusion 資料層(MSSQL / Oracle 切換在此) |
| `Product.CustomerDefineControl` | 35 | 自訂控件 |
| `Product.DataSource` | 35 | 資料來源 |
| `Product.Utility.ClientUtility` | 33 | 客戶端工具 |
| `Fusion.Logging` | 33 | 記錄 |
| `Product.UI` | 32 | UI 基底 |
| `Product.Dialog` | 29 | 對話框 |
| `Product.Entity.UIEntity.AppAdmin` | 27 | 管理模組 UIEntity |
| `Product.Config` | 26 | 設定 |
| `Product.CMM.UIControl` | 24 | CMM 模組控件 |
| `Product.Utility.WindowControlUtility` | 23 | 視窗控件工具 |
| `Product.CMM.FormProxy` | 18 | CMM 模組 Proxy |

### C.4 第三方(53 支,擇要)

| 套件 | 版本 | 用途 |
|---|---|---|
| Infragistics WinForms | v19.1(11 支) | **UI 控件庫**(不是 DevExpress) |
| Microsoft Enterprise Library | 5.1 | 記錄 / 例外 / 快取 / 資料 |
| Oracle ODP.NET | `Oracle.ManagedDataAccess` | 執行期資料庫 |
| Devart dotConnect | `Devart.Data.Oracle` | **設計期**,xsd 重生要用,見 §8.2 |
| `System.Data.OracleClient` | — | 遺留,微軟已標為過時 |
| Crystal Reports | — | 609 支 `.rpt` |
| NPOI · DocumentFormat.OpenXml · Office Interop | — | Excel 產出(三套並存) |
| Newtonsoft.Json | 6.0 | JSON |
| Ionic.Zip · ICSharpCode.SharpZipLib | — | 壓縮(兩套並存) |
| FileHelpers | 2.0 | 定長 / 分隔檔剖析 |
| `Microsoft.QualityTools.Testing.Fakes` | — | MSTest Fakes |
| `Interop.VGASEALLib` · `AxInterop.VGASEALLib` | — | 影像印鑑系統 COM 介接 |

### C.5 陷阱:25 個組件在 repo 有原始碼,卻被當成 DLL 參考

**這一節是全附錄最重要的部分,它會直接造成「改了沒效果」。**

有 25 個組件同時存在兩種形態:`Dev/` 底下有原始碼專案,而 `C:\Program Files\Vendor\PTPFBlock\` 底下有一份編譯好的 DLL。有 143 筆 `<HintPath>` 綁的是**後者**,不是 `<ProjectReference>`。

| 組件 | 原始碼 | 被當 DLL 參考的 csproj 數 |
|---|---|---|
| `Vendor.Product.Framework.Exceptions` | `Dev/Exceptions/Exceptions.csproj` | **90** |
| `Vendor.Product.TA.FormProxy.EC` | `Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/FormProxy.EC.csproj` | 5 |
| `Vendor.Product.TA.MappingCode` | `Dev/Common/Source/MappingCode/TA.MappingCode/TA.MappingCode.csproj` | 5 |
| `Vendor.Product.TA.DataAccess` | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj` | 5 |
| `Vendor.Product.TA.ServerUtility` | `Dev/Common/Source/Utility/TA.ServerUtility/TA.ServerUtility.csproj` | 4 |
| `Vendor.Product.TA.Utility` | `Dev/Common/Source/Utility/TA.Utility/TA.Utility.csproj` | 4 |
| `Vendor.Product.TA.Control.EC` | `Dev/ATLAS.EC/Source/Control/Control.EC/Control.EC.csproj` | 3 |
| `Vendor.Product.TA.UIEntity.EC` | `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/UIEntity.EC.csproj` | 3 |
| `Vendor.Product.TA.BasicUIEntity` | `Dev/Common/Source/Base/TA.UIEntity/TA.BasicUIEntity.csproj` | 3 |
| `Vendor.Product.TA.BasicDataEntity` | `Dev/Common/Source/Base/TA.DataEntity/TA.BasicDataEntity.csproj` | 3 |
| 其餘 15 個 | `Report*` / `Query*` / `UIEntity.OFD6` / `OFD8` / `DataEntity.OTA` / `FileHelpers` 等 | 各 1–2 |

**後果**:改了 `Dev/Common/Source/Base/TA.DataAccess/`(四眼引擎)重編,只有用 `ProjectReference` 的專案吃得到;那 5 支綁 DLL 的專案仍然編譯並執行**舊版**,直到有人把新 DLL 複製進 `C:\Program Files\Vendor\PTPFBlock\`。

最要命的一組是同一個模組內部互指:`Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj` 以 DLL 方式參考 `Vendor.Product.TA.DataEntity.OTA`,而那支的原始碼就在隔壁 `Dev/ATLAS.OTA/Source/Entity/DataEntity.OTA/`。**在 OTA 模組加欄位,重編 DataEntity 不會傳到 PO。**

> 手冊要寫的動作:改完任一「C.5 名單內」的組件,除了重編,還要更新 PTPFBlock 目錄下的 DLL,否則下游拿到的是舊的。哪些組件在名單內,以本表為準。

### C.6 HintPath 本身也有問題

| 問題 | 實例 | 後果 |
|---|---|---|
| 相對路徑層數自相矛盾 | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:82` 用 7 層 `..`、`:88` 用 10 層 `..`,兩者指向同一個 `PTPFBlock` 目錄 | **不論 repo 放在哪個路徑,兩者不可能同時解析成功** |
| 目錄名打錯 | 7 支 csproj 寫 `\Program\Vendor\PTPFBlock\` 而非 `\Program Files\` | 該筆參考必定解析失敗 |
| 混用絕對與相對路徑 | 同一支 csproj 內兩種並存 | 換機器 / 換磁碟機就壞 |
| 大小寫不一致 | `Vendor` / `Vendor` / `vendor` 三種寫法 | Windows 下無害,但顯示維護紀律 |
| 指向另一個框架版本 | 1 筆指向 `C:\Program Files (x86)\Vendor\PTPFBlock Dev 4.02.0\` | 該專案綁的是不同版本的框架 |

打錯 `\Program\` 的 7 支:

```
Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/ReportUI.CLS.csproj
Dev/ATLAS.OTA/Source/Control/Control.OTA/Control.OTA.csproj
Dev/ATLAS.OTA/Source/FormProxy/FormProxy.OTA/FormProxy.OTA.csproj
Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj
Dev/ATLAS.OTAB/Source/Control/Control.OTA/Control.OTAB.csproj
Dev/ATLAS.OTAB/Source/FormProxy/FormProxy.OTA/FormProxy.OTAB.csproj
Dev/ATLAS.OTAB/Source/PO/PO.OTA/PO.OTAB.csproj
```

**建置環境要能重現,這些都得先解決。**細節留給 `runbooks/build-env.md`,這裡只記錄事實。

---

> ⚠ **本檔與 `docs/_parts/` 已分歧,不要跑 `merge_architecture.py`。** D6–D11 修完後的回填(§0 規模、§2.1 型別分布、§6 六層不齊、附錄 A 統計、D.3、D.4) 是直接改在本檔上的,`_parts/arch_p*.md` 仍是舊版。跑 merge 會把回填整批蓋掉。要重組前先把改動同步回 `_parts/`。

## 附錄 D 掃描母體與覆蓋率

### D.1 母體

| 項目 | 數量 | 來源 |
|---|---|---|
| 專案(`.csproj` 於方案內) | 252 | `Dev/Vendor.ATLAS.sln` |
| 畫面代號(不重複) | 911 | `atlas_scan.py --list` |
| `_Ctl.cs` 檔數 | 923 | 其中 15 個代號實作在兩個專案 |
| **無 `_Ctl.cs` 的孤兒代號** | **51** | 有畫面代號長相、有 2–4 層,但沒有 Control,見 D.4 |
| 共用 Control | 27 | 不屬於任何畫面代號 |
| 實體表 | 413 | PO 的 `xTableMapping` 宣告(已剝註解、已含多筆版 `.Add()` 寫法,見 D.3) |
| xsd 查詢結果集形狀 | 1,644 | 只存在於 xsd,不是實體表 |
| DB 物件 | 121 | SP 83 · Fn 23 · Trigger 13 · View 2 |
| `DB/Table/` 變更腳本 | 156 | 其中 58 支含 `CREATE TABLE` |
| Crystal 報表範本 | 609 | `.rpt` |
| WindowsService | 4 |  |
| PTPFBlock DLL(相異) | 118 | 1,347 筆參考 |

> 兩處數字建議更新 `CLAUDE.md`:§3 的「Crystal 報表 608 支」應為 **609**(快取以報表代號為鍵記 608 筆,檔案實數 609,差在一支同名不同目錄);§1 列的六支 PTPFBlock DLL 可補一句「相異 DLL 共 118 支,清單見 `docs/architecture.md` 附錄 C」。

### D.2 本篇引用的覆蓋率

| 對象 | 母體 | 本篇明確引用 | 覆蓋 |
|---|---|---|---|
| 實體表 | 413 | 413(附錄 A 全列) | 100% |
| DB 物件 | 121 | 121(附錄 B 全列) | 100% |
| 畫面代號前綴 | 19 | 19(§9) | 100% |
| Common 專案 | 23 | 23(§7) | 100% |
| 畫面(逐支讀碼) | 908 | 4(`CASM001` / `CASI001` / `CASB001` / `CASR001`) | 0.4% |
| PTPFBlock DLL | 118 | 20 + 分類統計(附錄 C) | 17% |

**畫面只深讀了 4 支。**這是刻意的:架構篇的目的是建立通則,逐支畫面是 `docs/modules/` 的工作(階段 4)。通則能不能推廣到另外 904 支,要靠階段 4 驗證;目前只能說這 4 支涵蓋了四種型別、六層齊全、含主明細與報表專案變體。

### D.3 「實體表 437」是修過四輪掃描器才得到的

階段 0 最初報的是 **388**。前後查出**十一個**缺陷,分四輪修正,`test_scan.py` 全過。

**第一輪**(寫這一篇時發現):

| 代號 | 缺陷 | 方向 | 修法 |
|---|---|---|---|
| D1 | `//` 註解掉的 `MasterTable` / `DetailTable` 宣告照樣入列——579 筆宣告裡有 **68 筆(11.7%)** 躺在註解裡 | **多算** | 新增 `strip_cs_comments()`,比對前先抹掉行註解(字串字面值裡的 `//` 不動) |
| D2 | `MASTER_RE.search()` 只取第一筆,PO 在方法內重新指派 `MasterTable` 的全丟(如 `RSPM037_PO` 的 `Select_Detail` / `Select_Detail_D`) | **少算** | 改 `finditer()`,`masters` 收全部 |
| D3 | `files['po'][code]` 後者覆蓋前者,同代號雙實作只留一套 PO(如 `OFDM199A` 在 `ATLAS.OFD` 與 `ATLAS.OTA` 各一份) | **少算** | 新增 `po_all`,同代號所有 PO 路徑全掃後聯集 |

淨效果 388 → **367**:32 張表失去唯一宣告(`OFD701`、`BMSSEAL`、`OFD233`、`OFD670` 等只出現在註解裡),11 張表補回(`OFD199A_TMP` 系列、`OFD297A`、`SAL932A`、`RSP005`、`RSP006`)。結果集形狀同步由 1,618 變 1,635。

**第二輪**(寫模組知識庫時,由 `crm` / `cod` / `dsm` 三篇各自獨立撞到):

| 代號 | 缺陷 | 方向 | 修法 |
|---|---|---|---|
| D4 | `MASTER_RE` 只認 `MasterTable = new xTableMapping(...)`,認不出多筆版(`BaseMultiRowEVADaoPO`)的 `MasterTable.Add(new xTableMapping(...))`。實測 **66 支 PO、47 張表**整批漏掉 | **少算** | 正規式同時吃兩種寫法 |
| D5 | `parse_xsd` 跳過用 inline `<xs:simpleType>` 寫的欄位(帶長度限制的欄位沒有 `type=` 屬性)。實測 `DSMM906Model.xsd` 27 個 element 只有 2 個帶 `type=` | **少算** | 型別判斷改為「有 `type=` 就用,否則看直接子節點的 `simpleType` / `restriction base`」 |

淨效果 367 → **413**,而且 D5 連帶修正了兩個重要統計:

| 統計 | 修正前 | 修正後 |
|---|---|---|
| 實體表 | 367 | **413** |
| 結果集形狀 | 1,635 | 1,644 |
| 無 xsd 欄位定義 | 208(57%) | 236(57%) |
| **帶四眼欄位** | **37** | **158** |

抽驗兩例,與撈出缺陷的那兩篇報的數字精準吻合:`BMS906` 2 欄 → **25 欄**、`CRM006A` 9 欄 → **21 欄**。

> **最後這一列改變了結論。**修正前看起來「只有 21% 的表帶四眼」,會讓人以為四眼是少數特例; 實際是 **158 / 177 = 89%**,四眼幾乎是業務表的標準配備。§0.4 已照新數字改寫。

> 修 D5 時自己先踩了一個坑並修掉:型別判斷若用 `el.iter()` 會搜整個子樹, 導致「欄位用 `simpleType`」的**表本身**也被判成欄位而整張跳掉(實測會少 795 張表)。改成只看直接子節點 `el.findall()` 才對。新舊索引逐條比對:**消失 0 筆、新增 55 筆**。

**第三輪**(寫 OFD 各片時撞到):

| 代號 | 缺陷 | 方向 | 修法 |
|---|---|---|---|
| D6 | `--screen` 查詢大小寫敏感,`OFDM431bb` 查不到 | — | 代號比對改大小寫不敏感 |
| D7 | 只掃 `*_PO.cs`,漏掉 `ATLAS.EC.*` 那條線的 `<代號>OracleDao.cs`。實測 **82 個檔、16 張表** | **少算** | 兩種命名都認 |
| D8 | 兩段式宣告——`xTableMapping tp = new xTableMapping("T","vdb"); this.MasterTable = tp;`。實測漏 **6 張主檔、16 張明細**(`OFDM087` / `OFDM381` / `OFDB041` / `OFDB562`–`564`,以及 `BMSM001` / `BMSM006` 各 8 張明細),並讓 `OFDM381` 被誤判成孤兒 | **少算** | 新增 `indirect_tables()`,追區域變數再指派 |

**第四輪**(寫查詢與報表各片、以及建 `query.md` 資料層時撞到):

| 代號 | 缺陷 | 方向 | 修法 |
|---|---|---|---|
| D9 | 檔名副檔名前夾空白:`OFDM084B_Ctl .cs`。csproj 照抄所以編得起來,但 `endswith('_Ctl.cs')` 比不到 | **少算** | `WS_EXT_RE` 正規化 |
| D10 | 副檔名重複:`OFDM287Model.xsd.xsd`(同組還有 `.xsc` / `.xss` / `.Designer.cs`)。該畫面被判「只有 View 沒有 Model」 | **少算** | `DUP_EXT_RE` 正規化 |
| D11 | (a) 層後綴大小寫不照規則:`OFDR452_PXy.cs`(大寫 X)、`OFDM742_pxy.cs`(小寫 p);(b) **畫面母體漏人**——`OFDR461_Ct.cs`(少一個 `l`)與 `NFDR808_Ctlcs.cs`(點跑掉),兩支的類別名都是正確的 `<代號>_Ctl`、csproj 也照抄壞檔名,所以**編得起來、線上是活的** | **少算** | (a) 後綴比對大小寫不敏感;(b) 走完檔後讀 Control 目錄未匹配檔的類別名補回母體 |

第三、四輪的淨效果:

| 統計 | D5 後 | D8 後 | D11 後 |
|---|---|---|---|
| 實體表 | 413 | 437 | 437 |
| **畫面代號** | 908 | 909 | **911** |
| 結果集形狀 | 1,644 | 1,642 | 1,648 |
| 有主檔宣告的畫面 | 299 | 320 | 320 |
| 明細宣告總數 | 241 | 262 | 262 |

每一輪都逐條比對新舊索引,**消失 0 筆**。

**為什麼值得記在文件裡**:這不是掃描器特別爛,而是**這個 repo 保留大量被註解掉的程式碼**——同樣的坑在 §3(`TA_PO` 的子類數 2 → 0、`BasicEVAPO` 112 → 66)與 §6(`CASI001_Ctl` 143 行裡約 40 行是註解掉的方法外殼)各自獨立踩到一次。**任何對這個 repo 做靜態統計的工具,第一件事都是剝註解**,否則數字一律偏高。

> **剝註解要連 `/* */` 一起剝。**前十一個缺陷修完後又發現:`strip_cs_comments()` 只吃 `//`, 而 `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR288_PO.cs:21-23` 把 `m_db = provider.Create("TA");` 包在 `/* */` 裡,只剝 `//` 會把死碼判成活的。另一個同型的坑是**宣告式本身含賦值**:`private Database m_db = null;` 全庫 104 支這樣寫, 判「有沒有指派」時若不連同宣告整句排除,整批死碼會漏光(實測 9 支 → **76 支**)。

**第二條死碼線。**除了 §3.1.1 的 `BasicEVAPO.dbTA`,報表那一派的 `Basic_PO.m_db` 有完全相同的病: 宣告即 `null`(三種變體:`= null` / 無初值 / `readonly`)、建構子初始化被註解、資料方法第一行就 `m_db.CreateConnection()`。全庫實掃 **76 支報表 PO** 中招(NFD 55 · OFD 19 · RSP 6), **按下預覽即 NRE**。三項獨立佐證零例外:同時沒有 `[PODbType(DbServerType.Oracle)]`、沒有 `new Database("TA", …)`、只用 `SqlDbType` 不用 `OracleDbType`。連同 `BasicEVAPO` / `MultiRowEVAPO` 的 **76 支**,全庫共 **151 支畫面(17%)一按就 NRE**(`OFDM242` 兩條線都中,只算一次)。

### D.4 「911」沒有涵蓋到的:48 個沒有 Control 的代號

畫面清單是以 `_Ctl.cs` 為準建的,所以**連 Control 都沒有的東西不會出現在 911 裡**。實掃有 48 個這樣的代號:

| 類 | 數量 | 實情 |
|---|---|---|
| `_9i` 變體 | 45 | `IPJB606_9iModel.xsd` 這種命名,被當成獨立代號 `IPJB606_9i`,只有 model+view |
| **真孤兒** | **3** | `OFDB282` · `OFDM152` · `OFDM381` |

> **這一格原本寫 6 支,查下來有一半是掃描器誤判,不是程式殘骸。** `OFDM084B`(D9,Control 檔名 `OFDM084B_Ctl .cs` 副檔名前夾空白)、 `OFDR461`(D11b,`OFDR461_Ct.cs` 少一個 `l`)、 `NFDR808`(D11b,`NFDR808_Ctlcs.cs` 點跑掉)—— 三支的 csproj 都照抄了壞檔名,所以**編得起來、線上是活的**,只有依檔名比對的工具看不到。修正後畫面母體 908 → **911**,三支都進了清單且六層俱全。

**第一類解釋了 §6 的「65 支六層不齊」有一大半不是真缺。**`IPJB606` 顯示「缺 model+view」與 `IPJB606_9i` 顯示「只有 model+view」是同一件事的兩面——xsd 檔名多了 `_9i`,字面比對就對不上。IPJ 模組 15 支全部不齊,原因就在這裡。

**第二類是真的殘骸。**剩下的三支有 model+view(部分還有 po / pxy)卻沒有 Control 也沒有 UI (`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM381ModelVDB.cs:1` 是其中一例的 Entity 層)。有 FormProxy 代表它曾經是可以被遠端呼叫的完整畫面,現在入口沒了、其餘還在版控裡跟著編譯。

> `OFDM381` 另有一件事被 D8 修正:它的主檔 `OFD381` 用兩段式宣告, 舊掃描器抓不到,一度讓它看起來連主檔都沒有。實際上有,只是畫面入口確實不在。

### D.5 怎麼自己查

```
py -V:3.12 \docs\tools\atlas_scan.py --screen CASM001
py -V:3.12 \docs\tools\atlas_scan.py --table OFD701
py -V:3.12 \docs\tools\atlas_scan.py --module CAS
```

改過原始碼後加 `--refresh` 重掃。**不要 Read `*.Designer.cs`**——一支 5,375 行,全庫 2,190 支。

---

## 附錄 E 讀本文時要注意的地方

讀碼過程發現的缺陷與陷阱,依嚴重度排。每一條都是**現況記錄,不是修改建議**——要不要動、什麼時候動,是另一件事。

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1 | 25 個組件在 repo 有原始碼,卻被 143 筆 `<HintPath>` 綁成 PTPFBlock 的預編 DLL | 改原始碼重編,下游仍執行舊版,症狀是「改了沒效果」 | 附錄 C.5 | **高** |
| E2 | 共用邏輯有三套平行複本(主 / `Nfd` / `OTA`),彼此無繼承關係 | 改一處要改三處,漏改不會編譯失敗 | `Dev/Common/Source/Utility/TA.UtilityControl/NfdUtility_Ctl.cs:1` | **高** |
| E3 | 設定檔含多組明文密碼(資料庫 / 服務帳號 / SMTP / 印鑑系統) | 拿到 repo 即拿到憑證 | `Dev/Common/Source/Base/TA.DataEntity/app.config:6` | **高** |
| E4 | 236 / 413 張實體表沒有任何 xsd 欄位定義(57%) | 過半的表無法從 repo 得知欄位,改欄位必須連資料庫 | 附錄 A | **高** |
| E5 | 主程式的 Remoting 設定不在版控 | 無法從 repo 重建客戶端環境 | 全 repo 僅 3 支 config 含 `<channel>` | **高** |
| E6 | 選單 / 權限表不在 repo | 908 支畫面的中文名與業務歸屬全是推測 | §9.3 | **高** |
| E7 | 同一支 csproj 內相對 HintPath 層數自相矛盾(7 層與 10 層並存) | 不論 repo 置於何處都無法同時解析 | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:82` 與 `:88` | **高** |
| E8 | 7 支 csproj 把 `Program Files` 打成 `Program` | 該筆參考必定解析失敗 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj:1` | 中 |
| E9 | 代碼值域用 `public static string`(742 處)而非 `const` | 可被任意指派污染整個 AppDomain,編譯期不擋 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:16` | 中 |
| E10 | `const`(73)與 `static`(742)混用 | 改 `const` 值須重編所有引用端 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-21` | 中 |
| E11 | 商業參數(短線費率、計費區間)寫在 `appSettings` | 改規則找錯層,以為要改 code | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:207` | 中 |
| E12 | 三個 Oracle provider 並存(ODP.NET / Devart / `System.Data.OracleClient`) | 加欄位要裝對工具;遺留 provider 行為可能不同 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` | 中 |
| E13 | AGI(另一客戶)的 SQL Server 連線字串與代碼擴充留在共用層且納入編譯 | 誤判執行期資料庫;ATLAS 版含非 ATLAS 代碼值 | `Dev/Common/Source/DataSource/UIEntity.DataSource/App.config:6`、`Dev/Common/Source/MappingCode/TA.MappingCode/TA.MappingCode.csproj:92` | 中 |
| E14 | 設定檔大段內容被註解掉(`ServiceSettings` / `ExceptionHandling` / `CachingSettings`) | 無法從 repo 判斷實際生效值,例外走 EL 還是 Fusion 不明 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:110-160` | 中 |
| E15 | 客戶端輔助層有四套平行實作(含 `9i` 後綴),分界規則無文件 | 不知道自己這支畫面該用哪一版 | `Dev/Common/Source/Utility/TA.ClientUtility/ClientBizUtility.cs:1` | 中 |
| E16 | 四眼輔助散在三個類別、兩個專案 | 改四眼工具函式容易只改到其中一份 | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs:1` | 中 |
| E17 | `IJPR611` 前綴打錯(應為 `IPJ`) | 按前綴的批次作業會多算一個模組 | `Dev/ATLAS.EC.Report/Source/Control/ReportControl.EC/IJPR611_Ctl.cs:1` | 中 |
| E18 | 畫面代號前綴無法推出所在專案資料夾 | 憑代號猜路徑會找錯,必須用掃描器 | §9.2 | 中 |
| E19 | 65 支畫面六層不齊,`IPJ` 模組 15 支全部不齊 | 照六層通則找檔會撲空 | §6 | 中 |
| E20 | `DB/` 腳本混用 cp950(196)與 UTF-8 BOM(81) | 用 `utf-8` 硬讀會炸或產生亂碼 | 附錄 B.5 | 中 |
| E21 | `appSettings` 有重複鍵(`DbServerType`、`EnableExceptionLog` 各兩次) | 目前值相同無害,改其一會不一致 | `…OFDB600/App.config:200` 與 `:202` | 低 |
| E22 | WindowsService 三行初始化重複出現兩次 | 意圖不明,無註解 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:40-42` 與 `:54-56` | 低 |
| E23 | `DoExceptionPolicyHandler.cs` 只有 6 行 | 命名像政策入口實際是空殼 | `Dev/Exceptions/DoExceptionPolicyHandler.cs:1` | 低 |
| E24 | `ATLAS.BO` 只含 1 支 cs 檔 | 空專案掛在 252 個專案的方案裡 | `Dev/ATLAS.BO/Source/BO.BMS/BO.BMS.csproj:1` | 低 |
| E25 | `TestWindowControls` 只含一個 `Form1` | 控件試跑殼混在產品方案內 | `Dev/Common/Source/CustomControl/TestWindowControls/TestWindowControls.csproj:1` | 低 |
| E26 | 同一功能有多套第三方套件(Excel 三套、壓縮兩套) | 新增功能不知道該用哪一套 | 附錄 C.4 | 低 |
| E27 | HintPath 大小寫三種寫法並存 | Windows 下無害 | 附錄 C.6 | 低 |
| E32 | **`BasicEVAPO` 的 `dbTA` 從沒被賦值,73 支不覆寫的子類存檔會 NRE** | 接到「這支畫面壞掉」的單,要先確認它到底有沒有在跑;也代表全庫「活畫面」數比 908 少 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` 與 `:187`,詳見 §3.1.1 | **高** |
| E33 | 四支 WindowsService **不是同一種**:三支 `OFDB*` 走 Remoting,`RSPB008` 同行程直連 DB | 部署需求不同(要不要 Remoting 端點 / 要不要 DB 直連權限) | 見 §8.4 | 中 |
| E29 | **程式呼叫 380 支 SP,`DB/` 只有 61 支有腳本(缺 84%)** | 批次與報表的商業邏輯大量在版控外的 Oracle 預存程序裡;看 PO 只看得到呼叫,看不到內容。追邏輯必須連資料庫查 `ALL_SOURCE` | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58`(`S_TA_CASR001_GET` 無腳本) | **高** |
| E30 | 6 個代號有 2–4 層但**沒有 Control**,不在 908 的母體內 | 憑「908」做覆蓋率或影響面評估會漏掉這些;其中兩支還有 FormProxy,是可被遠端呼叫的殘骸 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM381_PO.cs:1` | 中 |
| E31 | 三支層別檔的檔名大小寫不合慣例(`OFDM742_pxy.cs`、`OFDR452_PXy.cs`、`OFDR461_PXy.cs`) | Windows 編得過,但任何大小寫敏感的工具或平台會判它缺層;本篇「缺 FormProxy 3 支」就是這麼來的,實際 0 支真缺 | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM742_pxy.cs:1` | 低 |
| E28 | **全 repo 大量保留被註解掉的程式碼**,且註解掉的與活的混在同一段 | 任何靜態統計不剝註解就偏高;讀碼時「看到」的不等於「會跑的」。本篇三處獨立踩到:主明細宣告 579 筆中 68 筆是註解(附錄 D.3)、`TA_PO` 子類數 2 → 0(§3)、`CASI001_Ctl` 143 行裡約 40 行是註解掉的方法外殼(§6) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41` | **高** |

> 這份清單只涵蓋**架構層級**的發現。畫面內部的邏輯缺陷(被註解的檢核、有訊息無 `return`、寫死常數)在 §2–§6 各章末的「本章發現」表,模組層級的留給階段 4。

---

## 附錄 F 版本紀錄

| 版本 | 日期 | 內容 | 產出方式 |
|---|---|---|---|
| v1 | 2026-09-14 | 首版。§0–§9 + 附錄 A–F | 讀碼 + `atlas_scan.py` 實掃;附錄 A / B 由產生器輸出 |

**待回填的輸入**(拿到就能把推測換成事實):

| 缺的東西 | 能補上什麼 | 影響章節 |
|---|---|---|
| 選單表匯出 | 908 支畫面的中文名與業務歸屬 | §9.3 整欄、附錄 E6 |
| 模組代碼對照表 | 19 個前綴的權威業務定義 | §9.3 |
| Oracle 唯讀帳號或 `ALL_TAB_COLUMNS` / `ALL_CONSTRAINTS` / `ALL_SOURCE` / `ALL_TRIGGERS` 匯出 | 208 張無定義表的欄位、主鍵、索引 | 附錄 A、§5 |
| PTPFBlock DLL(或所在機器) | 反組譯確認 `Basic_Pxy` / `EVAType` 等基底的真實行為 | 附錄 C.2、§3 |
| 部署機的 `main.exe.config` | 正式的 Remoting 端點與生效設定 | §8.1.1、§8.3 |

由 build_doc.py v2.0.0 於 2026-09-21 11:30 產生 · 標題 118 · 圖 7 · 表格 117 · 程式錨點 567 · § 連結 112 · 引用檢查：畫面 392（缺 0） · Table 413（缺 0） · SP 83（缺 0） · Function 23（缺 0） · Trigger 13（缺 0） · View 2（缺 0） · 結果集 11（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
