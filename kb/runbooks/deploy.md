<!-- 由 tools/build_copilot_kb.py 從 runbooks/deploy.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊 — 部署

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。 ⚠ 標「**〔客戶特定〕**」的是本站台的值,其他站台不同。

> **本手冊未實測。**本機沒有 PTPFBlock DLL、拿不到部署機,以下全部從 `.csproj` / `App.config` / `ProjectInstaller` 的設定反推(`architecture.md 附錄 C.1`)。第一次照做的人請把實際結果回填。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 改完程式要送測試 / 正式環境;或新裝一台伺服器 |
| 不適用 | 開發機環境建置(見 `runbooks/build-env.md`)· 資料庫本身的安裝 |
| 變數 | `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 最重要的前提 | **Remoting 邊界在 UI 與 FormProxy 之間**(`architecture.md §8.1`)。這一條決定所有部署分工 |

### 0.1 一句話版本

**改 UI 佈客戶端,改其餘五層佈伺服端,`UIEntity` 兩邊都要。**

其他都是這句話的細節。

## 1. 部署拓撲

```text
[圖] 部署拓撲:客戶端、Remoting 端點、伺服端 IIS、資料與批次服務,各放什麼;四個常見陷阱
圖中文字:① 客戶端(桌機 / Citrix) / main.exe + UI.<MOD> / 改 UI 只佈這裡 / UIEntity.<MOD> / 兩端版本必須一致 / ClientUtility · 控件 · Crystal / Infragistics 19.1 / main.exe.config / 不在版控,端點寫在這 / ② Remoting / *.rem 端點 / http + binary / ATLAS_TAService / < / 內網伺服器IP> / ③ 伺服端 IIS / FormProxy · Control · PO / 四層改動佈這裡 / DataEntity · UIEntity / UIEntity 兩端都要 / TA.DataAccess 四眼引擎 / 改這裡 908 支全中 / PTPFBlock\CrystalReports / 609 支範本 / ④ 資料與批次 / Oracle / 先 DB 後程式 / DB/ 腳本 277 支 / 混編碼 · 票號級 rollback / WindowsService 四支 / 是 Remoting 呼叫端 / 設定檔商業參數 / 要合併不要覆蓋 / ⚠ 四個照直覺做就會錯的地方 / DLL 覆寫名單 25 個組件 / 重編不更新 PTPFBlock = 沒效果 / 服務帳號改網域帳號 / 會掉進 Console.ReadLine 啟動失敗 / rollback 是票號級一整包 / 不能只退一支
```

*圖:圖 1 部署拓撲。橘實框=兩端都要或改了影響全系統;灰虛框=不在版控,要向部署機拿;橘虛框=照直覺做會錯的地方,對應 §2.1 / §5.3 / §6.3。*

## 2. 核心對照表:改了什麼、要部署哪些

**這張表是本手冊的重點,其餘各節是它的展開。**

| 你改了 | 客戶端 | 伺服端 IIS | WindowsService | 資料庫 |
|---|---|---|---|---|
| `UI.<MOD>` | ✔ |  |  |  |
| `UIEntity.<MOD>`(`View.xsd`) | ✔ | ✔ | ✔(若該服務用到) |  |
| `FormProxy.<MOD>` |  | ✔ |  |  |
| `Control.<MOD>` |  | ✔ |  |  |
| `PO.<MOD>` |  | ✔ |  |  |
| `DataEntity.<MOD>`(`Model.xsd`) |  | ✔ |  |  |
| `TA.DataAccess`(四眼引擎) |  | ✔ |  |  |
| `TA.MappingCode`(代碼字典) | ✔ | ✔ | ✔ |  |
| `TA.ClientUtility` | ✔ |  |  |  |
| `TA.ServerUtility` |  | ✔ | ✔ |  |
| `TA.Utility*` 五件套 | ✔ | ✔ | ✔ |  |
| `Exceptions` | ✔ | ✔ | ✔ |  |
| `.rpt` 報表範本 | ✔(檢視) | ✔(產出) |  |  |
| SP / Function / Trigger / View |  |  |  | ✔ |
| 表結構 |  |  |  | ✔ |
| `appSettings` 的商業參數 |  | ✔ | ✔ |  |

三條規則解釋這張表:

1. **`UIEntity` 兩端都要**,因為它是跨 Remoting 序列化的型別,兩端版本不一致會在反序列化時出錯。**此為推論**,依據見 `architecture.md §8.1`。

2. **共用層(`Common/` 底下)一律三邊都佈**,因為客戶端、伺服端、批次服務都參考它。判斷方法:該組件被哪一側的專案 `ProjectReference`,就佈到哪一側;共用層通常三邊都有。

3. **WindowsService 是 Remoting 的呼叫端**(`architecture.md §8.4`),它需要的是「客戶端那一套」加上它自己的 exe,不是伺服端那一套。

### 2.1 ⚠ 先查你改的組件在不在 DLL 覆寫名單裡

`architecture.md 附錄 C.5` 列了 **25 個組件**:repo 有原始碼,但有 **143 筆 `<HintPath>`** 把它們綁成 `%PTPF%` 底下的預編 DLL。

**改了這類組件,只重編不更新 `%PTPF%` 的話,下游拿到的還是舊的。**症狀是「改了沒效果」。

查法:在該組件的 `.csproj` 裡搜 `PTPFBlock`,搜得到就是被綁 DLL 的那種。名單前幾名:

| 組件 | 被幾支 csproj 綁 DLL |
|---|---|
| `Vendor.Product.Framework.Exceptions` | 90 |
| `Vendor.Product.TA.FormProxy.EC` · `TA.MappingCode` · `TA.DataAccess` | 各 5 |
| `Vendor.Product.TA.ServerUtility` · `TA.Utility` | 各 4 |

> 開發機上這件事看不出來,因為 build 產出的落點就是 `%PTPF%`(`runbooks/build-env.md §5.1`)。**到了部署機就會爆。**

## 3. 客戶端

### 3.1 放什麼

| 檔 | 說明 |
|---|---|
| `main.exe` + 設定檔 | 主程式。**不在 repo 內**,見 §3.3 |
| `UI.<MOD>.dll` | 各模組畫面 |
| `UIEntity.<MOD>.dll` | 與伺服端**版本必須一致** |
| `Vendor.Product.TA.ClientUtility.dll` · `UI.CustomControl` · `UI.WindowControls` | 客戶端共用 |
| Infragistics v19.1 執行期 | 11 支 DLL |
| Crystal Reports 執行期 | 檢視報表用,版本見 `runbooks/build-env.md §2` |
| PTPFBlock 客戶端那部分 | `Vendor.Product.UI` / `Dialog` / `CustomerDefineControl` 等 |

### 3.2 Citrix

設定檔開了 Citrix 支援(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:262`):

```
<add key="IsSupportCitrix" value="true"/>
```

註解說明它會改變兩件事:不檢查 `main.exe` 是否重複執行、報表範本的暫存目錄從 `ApplicationData` 換到 log 目錄下的 `CrystalReport`。**部署到 Citrix 環境時這個值要是 `true`。**〔客戶特定〕

版本字串也是分開的(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:264`):`基金事務系統(VENDOR) (v 1.7.0.1)`。

### 3.3 ⚠ 客戶端的 Remoting 設定不在版控裡

全 repo 只有三支設定檔含 `<channel>`,而 `.rem` 註冊只有 20 筆——其中 18 筆屬於 `SWEmailService` / `SWService` 兩個別的 Vendor 產品,真正屬於 TA 的只有 `OFDB600_Pxy` 與 `OFDB609_Pxy` 兩筆(`architecture.md §8.1.1`)。

**908 支畫面顯然不是靠這兩筆在跑。`main.exe.config` 是部署產物,不在版控內。**

> **〔假設〕缺:部署機的 `main.exe.config`。**推論它會用同一種 `<wellknown>` 語法,替每一支 `_Pxy` 型別註冊一個 `.rem` 端點,或用萬用的 `RegisterActivatedClientType`。依據是 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189` 那筆的寫法。**拿到部署機的設定檔才能寫出正確步驟。**

## 4. 伺服端(IIS)

### 4.1 端點

從 WindowsService 的客戶端設定反推(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189`):

```
<wellknown type="Vendor.Product.TA.FormProxy.EC.OFDB600_Pxy, Vendor.Product.TA.FormProxy.EC"
           url="http://<內網伺服器IP>/ATLAS_TAService/OFDB600_Pxy.rem"/>
```

| 項目 | 值 |
|---|---|
| 伺服器 | `<內網伺服器IP>`〔客戶特定〕——設定檔註解寫「趴板時請變更 url 屬性中的伺服器位置」 |
| 虛擬目錄 | `ATLAS_TAService`〔客戶特定〕 |
| 通道 | `http` + `binary` formatter(`…App.config:179`) |
| 驗證 | `useDefaultCredentials="true"`(Windows 整合驗證) |

### 4.2 放什麼

`FormProxy.<MOD>.dll` · `Control.<MOD>.dll` · `PO.<MOD>.dll` · `DataEntity.<MOD>.dll` · `UIEntity.<MOD>.dll` · `TA.DataAccess.dll` · `TA.ServerUtility.dll` · 共用層 · PTPFBlock 伺服端部分。

### 4.3 資料庫型態設定

執行期用哪個資料庫引擎由 Fusion 框架設定決定,不是寫死的(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:62-67`):

```
<add name="TA" dataBaseProvider="Oracle" sqlLogEnable="false"/>
```

六個具名資料庫(`Fusion` / `SWProduct` / `Logging` / `TA` / `SWEMail` / `Scripting`)本站台全設 Oracle。另有 `appSettings` 的 `DbServerType`(`…App.config:200`)。

**這兩處要一致**,而且 `DbServerType` 在同一個檔裡出現兩次(`:200` 與 `:202`),值相同所以目前無害,改的時候兩處都要改(`architecture.md 附錄 E21`)。

## 5. WindowsService 四支

### 5.1 清單

| 服務名 | 專案 | 安裝帳號 |
|---|---|---|
| `OFDB600_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600` | `LocalSystem` |
| `OFDB609_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609` | `LocalSystem` |
| `OFDB680_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680` | `LocalSystem` |
| `RSPB008_Service` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008` | `LocalSystem` |

服務名定義在 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/ProjectInstaller.Designer.cs:42`,帳號在同檔 `:36`。

### 5.2 安裝與啟停

四支都有 `ProjectInstaller.cs`,所以走 `InstallUtil`:

```
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe" Vendor.Product.TA.WindowsService.OFDB600.exe
sc start OFDB600_Service
sc stop  OFDB600_Service
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe" /u Vendor.Product.TA.WindowsService.OFDB600.exe
```

> **〔假設〕缺:部署機。**`InstallUtil` 的路徑與位元版本(Framework vs Framework64)未實測。依據是專案為 .NET Framework 4.8 且含 `ProjectInstaller`,這是標準做法。

### 5.3 ⚠ 服務帳號**不能**改成網域帳號

`Program.cs` 用 `Environment.UserName` 判斷自己是不是以服務身分啟動(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:27`):

```
if (Environment.UserName == "SYSTEM")
{
    ServiceBase.Run(ServicesToRun);      // 服務模式
}
else
{
    OFDB600_Service DebugToRun = new OFDB600_Service();
    DebugToRun.Start();
    Console.ReadLine();                  // 除錯模式
}
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:26-44`

配合安裝時的 `ServiceAccount.LocalSystem`,`Environment.UserName` 才會是 `"SYSTEM"`。

**如果為了資安把服務帳號改成網域帳號,`UserName` 就不是 `"SYSTEM"`,程式會走進除錯分支,呼叫 `Console.ReadLine()`——服務沒有主控台,`ServiceBase.Run` 永遠不會被呼叫,SCM 等到逾時後判定啟動失敗。**

三支 `OFDB*` 都有這個判斷;`RSPB008` 沒有(`Program.cs` 裡沒有 `Environment.UserName`)。要改帳號就得先改這段程式。

### 5.4 服務也要跟著佈的東西

服務是 Remoting 的呼叫端,所以它的目錄要有:自己的 exe 與 `exe.config`、`FormProxy.<MOD>.dll`、`UIEntity.<MOD>.dll`、共用層、PTPFBlock。

**`exe.config` 裡有伺服器位址**(`…App.config:189`),換伺服器時四支都要改。

## 6. 資料庫腳本

### 6.1 順序

**一律先資料庫、後程式。**理由:程式端的 INSERT / UPDATE 欄位清單是執行期跟資料庫要 schema 決定的(`runbooks/add-column.md §5.2`),資料庫還沒有新欄位,程式先上線就會炸。

反過來,刪欄位要先下程式、再改資料庫。

### 6.2 編碼

`DB/` 底下 277 支腳本 **cp950 196 支 + UTF-8 BOM 81 支混用**(`architecture.md 附錄 B.5`)。

- 執行前確認你的工具用對編碼,否則中文註解會變亂碼,**有些工具會連帶把整支腳本解析壞**。

- 要程式化讀取一律走 `atlas_scan.py` 的 `read_text()`。

### 6.3 rollback

`DB/Table/` 的 rollback **不是逐檔配對**。`DB/Table/11706_rollback.sql` 是**票號級一整包**,對應該票號的 9 支正向腳本(`architecture.md 附錄 B.5`)。

所以回退時是「整個票號一起退」,不能只退其中一支。**部署前先確認該票號的 rollback 存在且涵蓋你要上的全部腳本。**

### 6.4 ⚠ 有些腳本不可重跑

`DB/Table/` 內有腳本含正式資料(受益人編號、經手人帳號),重跑會產生重複資料(`architecture.md 附錄 E`)。**執行前先看內容,不要當成冪等腳本無腦重跑。**

### 6.5 SP 大量不在版控

程式呼叫 380 支 SP,repo 只有 61 支有腳本(缺 84%,`architecture.md 附錄 B.0`)。**部署一支 SP 之前,先確認你手上這份是不是線上的最新版**——多數情況要先從資料庫 `ALL_SOURCE` 撈出來比對。細節見 `runbooks/change-sp-fn-trigger.md`。

## 7. Crystal 報表

### 7.1 範本是 build 出來的,不是部署過去的

25 支 `Report.<模組>` 專案帶 PostBuild(`Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj`):

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

所以 609 支範本在建置機上就落到 `%PTPF%\CrystalReports\`。**部署時要把這個目錄一起帶到伺服端。**

### 7.2 客戶端要有 Crystal 執行期

檢視報表在客戶端,所以客戶端要裝 Crystal Reports 執行期。版本見 `runbooks/build-env.md §2`(**13.0.4000.0 與 13.0.2000.0 兩版並存**,裝新的)。

## 8. 設定檔與連線字串

### 8.1 哪裡有連線字串

| 檔 | 用途 |
|---|---|
| `Dev/Common/Source/Base/TA.DataEntity/app.config:6` | SqlClient,**AGI 產品線的設計期殘留,不要照抄** |
| `Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` | 同上,14 筆 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` | Devart,**設計期**用的 Oracle 開發庫 |

**這些都不是執行期連線。**執行期的資料庫由 Fusion 設定決定(§4.3),實際連線字串在部署機的設定檔裡。

> **〔假設〕缺:部署機設定檔。**repo 內找不到正式環境的連線字串。依據是 repo 內的三種連線字串分別對應設計期與另一個客戶,見 `architecture.md §8.2`。

### 8.2 ⚠ 設定檔含明文密碼

`architecture.md 附錄 E3` 列了多處:資料庫密碼、服務帳號密碼、SMTP 密碼、影像印鑑系統帳密。

**部署時不要把開發用的設定檔直接複製到正式環境**,而且這些密碼在版控裡人人看得到,建議另案處理。本文一律不重製密碼值。

### 8.3 商業參數也在設定檔

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:207` 之類的 `appSettings` 放了短線費率、計費區間、TDCC 檔案路徑等**商業規則**。

**改這些不用重編,改設定檔重啟服務即可**——但也代表部署時如果整份覆蓋設定檔,會把站台調過的參數蓋掉。**設定檔要合併不要覆蓋。**

### 8.4 落地路徑

固定寫死在設定檔,部署機上這些目錄要先建好並給權限:

| 用途 | 路徑 |
|---|---|
| 框架 log | `C:\Vendor\VendorProduct\*.log` |
| 加密金鑰 | `C:\Vendor\Keys\DefaultKey.key`(`…App.config:43`) |
| 匯出檔 | `C:\Vendor\ExportFile` |
| TDCC 指託資料檔 | `C:\Vendor\TDCC指託\…` |

〔客戶特定〕

## 9. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 比對伺服端與客戶端的 `UIEntity.<MOD>.dll` 版本 | 兩邊相同 |
| 2 | 查你改的組件在不在 `architecture.md 附錄 C.5` 名單 | 在的話 `%PTPF%` 也更新了 |
| 3 | 開一支該模組的畫面查詢 | 查得出資料(驗 Remoting 通、PO 正常) |
| 4 | 新增 → 覆核 → 核准 一輪 | 四眼狀態正確流轉(`architecture.md §3`) |
| 5 | `sc query <服務名>` 四支 | `RUNNING` |
| 6 | 看服務 log | `C:\Vendor\VendorProduct\` 底下有新紀錄且無例外 |
| 7 | 印一支該模組的報表 | 出得來(驗 `%PTPF%\CrystalReports` 有帶到) |
| 8 | 資料庫腳本 | 對應票號的物件都存在且版本正確 |

## 10. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **改了沒效果** | 改的組件在 DLL 覆寫名單裡,`%PTPF%` 沒更新 | §2.1 |
| **改了沒效果(另一種)** | 只佈了伺服端或只佈了客戶端 | §2 對照表 |
| **反序列化例外 / 型別版本不符** | `UIEntity` 只佈了一端 | §2 規則 1 |
| **服務裝好了但啟動逾時失敗** | 服務帳號不是 `LocalSystem`,程式走進 `Console.ReadLine()` 分支 | §5.3 |
| **`ORA-00904` invalid identifier** | 程式先上線、資料庫腳本還沒跑 | §6.1 |
| **腳本執行後中文全變亂碼** | cp950 / UTF-8 BOM 混用,工具用錯編碼 | §6.2 |
| **回退時退不乾淨** | rollback 是票號級一整包,只退了其中一支 | §6.3 |
| **重跑腳本後資料重複** | 該腳本含正式資料,不可重跑 | §6.4 |
| **報表印不出來 / 找不到範本** | `%PTPF%\CrystalReports` 沒帶到伺服端 | §7.1 |
| **站台調過的費率被打回預設** | 整份覆蓋設定檔 | §8.3 |
| **連得到畫面但存檔報錯** | 資料庫型態設定 `dataBaseProvider` 與 `DbServerType` 不一致 | §4.3 |
| **換伺服器後客戶端連不上** | `main.exe.config` 的 `.rem` 位址沒改 | §3.3 §4.1 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:43` `:62-67` `:179` `:189` `:200` `:202` `:207` `:262` `:264` | §3 §4 §8 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs` | `:26-44` `:27` | §5.3 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/ProjectInstaller.Designer.cs` | `:36` `:42` | §5.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs` | `:40-42` | §5.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs` | `:42-44` | §5.1 |
| `Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj` | `:1` | §7.1 |
| `Dev/Common/Source/Base/TA.DataEntity/app.config` | `:6` | §8.1 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config` | `:8` | §8.1 |
| `Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` | `:7` | §8.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **部署機的 `main.exe.config`** | §3.3 §4.1 | 客戶端 Remoting 註冊方式目前是推論;補進來後寫出實際的端點清單與換機器要改哪幾行 |
| **部署機存取權** | 全篇 | 整本未實測。跑一次完整部署,把實際指令、路徑、耗時回填 |
| **正式環境連線字串與帳號** | §8.1 | 目前只知道設計期的值 |
| **PTPFBlock DLL** | §2.1 §3 §4 | 無法確認伺服端 / 客戶端各要哪幾支;目前只能給「該側專案參考到的就要」這個原則 |
| **IIS 設定(應用程式集區、`.rem` 對應)** | §4 | repo 內沒有 `web.config`,伺服端的裝載設定完全看不到 |

## 附錄 C 本手冊未實測

與 `runbooks/build-env.md 附錄 C` 同樣的狀況:**沒有任何一步實際跑過**。部署分工的結論來自 Remoting 邊界(有三項程式證據,`architecture.md §8.1`),但「複製哪些檔到哪個目錄」這種操作細節,repo 裡沒有答案。

本手冊的定位是:**拿到部署機那天的檢查清單與陷阱提醒**,特別是 §2.1(DLL 覆寫)、§5.3(服務帳號)、§6.3(票號級 rollback)、§8.3(設定檔要合併不要覆蓋)這四條——它們都是「照直覺做就會錯」的地方。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 38 · 圖 1 · 表格 12 · 程式錨點 23 · § 連結 37 · 引用檢查：畫面 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
