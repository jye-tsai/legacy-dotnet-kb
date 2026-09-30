<!-- 由 tools/build_copilot_kb.py 從 modules/ec.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS EC 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀五段:§0.2(這片最反直覺的七件事)、§0.4(八支畫面根本沒進編譯)、§6.1(28 支批次的四種家族)、§6.2 ~ §6.4(三支 WindowsService)、附錄 E(踩雷)。

> ⚠ **本片的業務意義**(§0)由表名、`msdata:Caption`、Designer 內的標籤文字與 `_Pxy` / `_Ctl` 的 XML 註解**推測**,待選單表 / 對照表回填。畫面中文名不在版控內,本文的畫面名稱一律標「推測」。 ⚠ **〔客戶特定〕**:Remoting 端點 `http://<內網伺服器IP>/ATLAS_TAService/`、EC Web Service 端點 `http://localhost/ECService/TAService.asmx`、Billhunter 端點 `<客戶UAT主機>`、落地路徑 `C://Vendor//WindowService//OFDB60x//`、`SYSTEM_ID` 值域 `1`(網路)/ `2`(語音)為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`OFD601`(受益人網路戶基本資料)與 `OFD607A`(網路戶註冊檔)兩張表的**主檔擁有者在 BMS 不在 EC**,EC 只用裸 `UPDATE` 改欄位;`RSP006A` / `OFD221A` / `OFD251A` 被 `OFDB672` / `OFDB673` 直接改寫(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、SQL 與 Oracle 現況看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`TA.ServerUtility` 的外部介接口看 `architecture.md §7`、WindowsService 與部署看 `architecture.md §8`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這片管什麼(推測)

**一句話:EC 管「客戶自己在網路或語音(IVR)下的單,怎麼變成 TA 核心系統認得的交易」——從網路開戶、發密碼、客戶下單、員工交易審核、把單子拋轉進核心帳務、到價通知、扣款送件與核印,全部在這 50 支畫面裡。**

「EC」三個字母在 repo 內沒有定義文字,但五條線索指向同一件事,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 框架自己這樣寫 | `ECAdapter` 的類別註解寫「連結EC系統專門提供給TA系統使用的Web Service」,`remarks` 寫「Boundary Class /EC系統之間的介面」 | `Dev/Common/Source/Utility/TA.ServerUtility/ECAdapter.cs:11-15` |
| 畫面標題 | `OFDB600_Pxy` 的類別註解直接寫「網路交易時限截止處理作業(手動)」 | `Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/OFDB600_Pxy.cs:12-15` |
| 畫面上的選項 | 每一支拋轉批次都有「交易途徑:全部 / 網路 / 語音」三選一的選項組 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJB621.Designer.cs`(以 `grep -n` 取得,未 Read Designer) |
| 欄位中文名 | `OFDM601Model.xsd` 的 `SYSTEM_ID` 的 `msdata:Caption` 就是「交易途徑」 | `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDM601Model.xsd` |
| 密碼兩套 | 所有開戶類畫面都成對出現「登入密碼 / 交易密碼」與 `EC_PSW` / `ES_PSW` 兩個欄位 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:897-954` |

所以本片可以拆成**六條業務線**,50 支畫面全部落在其中一條:

| # | 業務線 | 畫面 | 一句話 |
|---|---|---|---|
| ① | **交易拋轉**(本片主體) | `IPJB606` `IPJB621` `IPJB622` `IPJB624` `IPJB625` · `OFDB600` `OFDB601` `OFDB602` `OFDB604` `OFDB605` | 把客戶在網路 / 語音下的申購、買回、轉申購、定額異動、受益人資料變更,批次拋進核心交易檔;可「拋轉回復」倒回去 |
| ② | **網路開戶與密碼** | `OFDB606` `OFDB607` `OFDB608` `OFDB609` `OFDB610` `OFDB615` `OFDB616` · `IPJM614` `OFDM602` `OFDM607` `OFDM694` | 開戶進度推進、登入 / 交易密碼產生與寄發、LDAP 帳號同步、實體密碼函列印與標籤、文件需求清單 |
| ③ | **員工交易審核** | `OFDB671` `OFDB672` `OFDB673` `OFDB690` `OFDB691` · `OFDM604` | 員工本人的網路單要先給投管部審;通過才放行,不通過要填原因;還能整批改掛員工代碼與銷售機構 |
| ④ | **到價通知** | `OFDB680` `OFDB693` · `OFDM680` `OFDM681` | 客戶設的基金到價提示,每天定時算一次,命中就發信 |
| ⑤ | **扣款與核印** | `IPJB613` `IPJB614` · `OFDB611` `OFDB612` | 網路定額扣款的送件批號、扣款檔產生與回覆、印鑑核印結果回寫 |
| ⑥ | **參數維護** | `OFDM600` `OFDM601` `OFDM603` `OFDM670` `OFDM672` `OFDM674` `OFDM690` `OFDM691` `OFDM692` `OFDM693` `OFDM695` `OFDM696` `OFDM697` `OFDM698` `OFDM699` | 全站限額 / 時限、逐檔基金的網路交易參數、手續費率、促銷與理財活動、網頁呈現(顏色 / 轉址 / 分類 / 產品)、IVR 音檔、節日 |

### 0.2 這片最反直覺的七件事

寫在最前面,因為每一條都會讓「照直覺改」出事。

1. **`IPJB6xx` 與 `OFDB60x` 是同一支批次的兩份複本。** 兩邊呼叫**完全同一支 SP**:`IPJB621` 與 `OFDB601` 都打 `S_EC_IPJB601_EXCUTE`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs:238` 與 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:230`)。差別只有畫面上「交易途徑」能不能選語音:`IPJB6xx` 給三個選項(全部 / 網路 / 語音),`OFDB60x` 只給「網路」。**改 SP 會同時影響兩支畫面**,改其中一支的 Dao 不會影響另一支。四組配對見 §6.1。

2. **`MasterTable` 的統計是假的。** 掃描器只認 `*_PO.cs`,而本片 90% 的 PO 改名叫 `*OracleDao.cs` 放在 `PO/PO.EC/Oracle/` 下。實際有活的 `xTableMapping` 宣告的是 **17 支**,不是 2 支。逐支見 §2.1。

3. **`PO/PO.EC/MSSQL/` 30 個檔裡只有 2 個類別是活的。** 其餘 28 個檔案從 `public class` 那行開始整段被 `//` 註解掉,卻全部還掛在 `PO.EC.csproj` 的 `<Compile Include>` 裡。這 28 個檔合計約 9,700 行死碼。`architecture.md §3` 記的「`TA_PO` 僅存兩個被註解的宣告」是這批的兩個樣本,不是全貌。見 §2.6。

4. **八支畫面的六層檔案都在,但沒有任何一層進編譯。** `OFDB606` `OFDB610` `OFDB611` `OFDB690` `OFDM681` `OFDM691` `OFDM692` `OFDM693` —— UI / FormProxy / Control / PO 四個 csproj 一致地把它們排除掉,只有 xsd 那兩層還留著。見 §0.4。

5. **`OFDB680` 的服務不是 Remoting 客戶端。** 程式碼寫得跟 `OFDB600` / `OFDB609` 一模一樣(`RemotingConfiguration.Configure` 加 `new OFDB680_Pxy()`),但它的 `App.config` **整個 `<system.runtime.remoting>` 區段不存在**。沒有 `<wellknown>` 註冊,`new OFDB680_Pxy()` 就是一個普通的本地物件 —— 這支服務其實是**同一行程直接打資料庫**。見 §6.4。

6. **「網路開戶」的主檔 `OFD601` / `OFD607A` 不歸 EC 管。** 全庫唯一把這兩張表宣告成 `xTableMapping` 的是 BMS 的 `BMSM001` 與 `BMSM006`,而且都掛在 `DetailTable`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:156-157`)。EC 這邊七支程式改它,全部走裸 `UPDATE` 字串,不經四眼。見 §8.1。

7. **`OFDM601` / `OFDM607` 的名字跟 `OFD601` / `OFD607A` 沒有關係。** `OFDM601` 的主檔是 `OFD606A`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:38`)、`OFDM607` 的主檔是 `OFD608A`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:31`)。名字對得上是巧合,**不要拿 `OFDM601` 去找 `OFD601` 的維護入口**。

### 0.3 「48 支沒有主檔」怎麼回事 —— 三層原因拆開看

派工單上寫「50 支裡有 48 支沒宣告 `MasterTable`」。實測後這個數字要拆成三塊,結論也不同。

**先給正確數字:**

| 狀況 | 支數 | 說明 |
|---|---|---|
| 有活的 `MasterTable` / `MasterTable.Add` | **17** | 16 支 M 加 1 支 B(`OFDB693`) |
| 宣告存在但整行被 `//` 註解 | **2** | `OFDM602` `OFDM603` |
| 連 PO 檔都沒有活類別 | **3** | `OFDM691` `OFDM692` `OFDM693`(只剩註解掉的 MSSQL 檔) |
| 真的沒有、也不需要 —— 裸 DAO | **28** | 27 支 B 批次加 `IPJM614` |

**第一層:掃描器只認 `*_PO.cs`。** `atlas_scan.py --screen OFDB600` 對 50 支全部回報「PO 缺」,但 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs` 明明在。本片的 PO 層命名是 `<代號>OracleDao.cs`,不是 `<代號>_PO.cs`。這一層是**純命名造成的假警報**,跟 `architecture.md §9` 記的 `_9i` 假警報是同一類問題的另一個變種。

**第二層:B 批次本來就沒有主檔,這是設計不是缺陷。** `architecture.md §6` 已經說明:I / B 兩型的 PO 「退化成裸 DAO」,不繼承 `BaseEVADaoPO`、自己 `new Database`、`MasterTable` 那行被註解。本片 28 支 B 裡有 27 支完全符合這個型:

```
public class OFDB600OracleDao : IOFDB600PO        // 沒有基底
{
    private Database db = null;
    public OFDB600OracleDao() { db = new Database("TA", DbServerType.Oracle); }
```

(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:18-30`)

兩個例外:`OFDB693OracleDao` 繼承 `BaseEVADao` 且有 `MasterTable = new xTableMapping("OFD688A", "OFDB693")`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:18` 與 `:30`) —— 它其實是一支長得像 B 的維護畫面;`IPJM614OracleDao` 繼承 `BaseEVADao` 卻**沒有**任何 `MasterTable` 宣告(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:18`),是本片唯一一支「有四眼基底、沒有四眼表映射」的 M 畫面,全靠自己寫 SQL。

**第三層:那資料模型要怎麼看?** 既然 28 支沒有 `xTableMapping` 可讀,唯一的來源就是**程式裡的 SQL 字串與 `GetStoredProcCommand` 的 SP 名**。實際操作三步:

| 步驟 | 做什麼 | 工具 |
|---|---|---|
| 1 | 找出這支打哪一支 SP | `grep -n GetStoredProcCommand <Dao>.cs` —— 本片 21 個檔共 26 處 |
| 2 | 找出這支直接寫哪些表 | `grep -nE 'INSERT INTO |
| 3 | 找出這支回傳哪些結果集 | 讀 `<代號>Model.xsd` 的 `msprop:Generator_TableClassName`,那就是 vdb 上的 DataTable 名,通常直接用實體表名命名 |

第 3 步是本片最有價值的一條:**xsd 的 DataTable 名就是實體表名**。`IPJB621_9iModel.xsd` 的 DataTable 叫 `OFD611A`,`IPJB622_9iModel.xsd` 叫 `OFD612A` —— 這就是四支拋轉批次各自處理哪張交易檔的答案,不必去讀版控外的 SP。完整對照在 §2.2。

**這一層的結論很直接:本片絕大多數業務邏輯不在版控裡。** 26 處 `GetStoredProcCommand` 指到的 18 支 SP(附錄 B)沒有一支在 `DB/` 底下,`architecture.md §8` 記的「`DB/` 只涵蓋一小部分 SP」在 EC 這片是 0%。C# 這端只做三件事:組參數、開交易、把結果集塞回 vdb。**要判斷一支拋轉批次到底做了什麼,得去資料庫拿 SP 原始碼,repo 裡沒有。**

### 0.4 八支畫面整組沒進編譯

這是掃描時最意外的一件事,而且四個 csproj 的排除清單**完全一致**,不像是誤刪。

| 畫面 | UI | FormProxy | Control | PO(Dao 加 Interface) | Model / View xsd |
|---|---|---|---|---|---|
| `OFDB606` | 排除 | 排除 | 排除 | 排除 | 仍在 |
| `OFDB610` | 排除 | 排除 | 排除 | 排除 | 仍在 |
| `OFDB611` | 排除 | 排除 | 排除 | 排除 | 仍在 |
| `OFDB690` | 排除 | 排除 | 排除 | 排除 | 仍在 |
| `OFDM681` | 排除 | 排除 | 排除 | 排除 | 仍在 |
| `OFDM691` | 排除 | 排除 | 排除 | 排除(只剩註解掉的 MSSQL 檔) | 仍在 |
| `OFDM692` | 排除 | 排除 | 排除 | 同上 | 仍在 |
| `OFDM693` | 排除 | 排除 | 排除 | 同上 | 仍在 |

驗證方式:把四個 csproj 的 `<Compile Include>` 全部取出來,跟磁碟上的檔案逐一比對。`Control.EC.csproj` 磁碟有 51 個 `_Ctl.cs`、csproj 只收 43 個;`PO.EC.csproj` 少收 5 個 `OracleDao.cs` 與 8 個 `I*PO.cs`;`FormProxy.EC.csproj` 對這八個代號**一個字都沒有**。

**兩個殘留物值得記下來:**

- `OFDB606RPS.cs` 與 `OFDB610RPS.cs`(Crystal Report 的包裝類別)**還在編譯**(`Dev/ATLAS.EC/Source/UI/UI.EC/UI.EC.csproj:415` 與 `:440`),但它們的宿主畫面已經不在了。等於編出兩個沒有入口的報表殼。

- `UI.EC.csproj:900-904` 還留著 `OFDM681View` / `OFDM691View` / `OFDM692View` / `OFDM693View` 的 `.datasource` 設計期檔案。

**對讀者的意義:** 這八支的程式碼在本文裡**只當史料引用,不要當現行邏輯**。§4 與 §6 會照樣寫它們(因為 50 支要全覆蓋),但每一節開頭都會標「**未進編譯**」。要判斷正式環境到底跑不跑得到,得看部署機上的 DLL,repo 判斷不出來 —— 這是**假設**,依據是四個 csproj 的一致排除。

### 0.5 不管什麼

| 不管 | 誰管 | 依據 |
|---|---|---|
| 受益人主檔的開戶 / 變更四眼 | BMS(`BMSM001` / `BMSM006`) | `bms.md §8`;EC 只改 `OFD601` / `OFD607A` 的欄位 |
| 定期定額契約本身 | RSP | `rsp.md §4`;`OFDB672` / `OFDB673` 只改 `RSP006A` 的員工代碼欄 |
| 基金主檔 / 淨值 | OFD 本體(不在本片) | 本片一律 join 進來唯讀 |
| 交易的真正帳務入帳 | 核心 TA(拋轉後的下游) | 拋轉批次只把單子推進 `OFD611A` / `OFD612A` 等交易檔,入帳由 SP 內部或下游批次完成 |
| 對帳單 / 報表輸出 | `Dev/ATLAS.EC.Report/`(**不在本片**) | 另片處理 |
| 查詢畫面 | `Dev/ATLAS.EC.Query/`(**不在本片**) | 另片處理,這也是本片為什麼一支 I 畫面都沒有(§5) |
| 網路前台頁面本身 | EC 系統(外部,SOAP) | `architecture.md §7`;ATLAS 只透過 `ECAdapter` 呼叫 |

### 0.6 使用角色(推測)

程式裡沒有任何權限判斷式(跟 `rsp.md §7` 的觀察一致),以下由畫面內容推測:

| 角色 | 碰哪些畫面 | 推測依據 |
|---|---|---|
| 交易室 / 作業人員 | ① 拋轉、⑤ 扣款核印 | 畫面上是「拋轉 / 拋轉回復」與日期參數,屬日終作業 |
| 客服 | ② 開戶密碼(`OFDB606` `OFDB607` `OFDB615` `OFDB616`) | 按鈕文字是「重發登入密碼」「補發網路密碼」「列印實體密碼函」 |
| 投管部 | ③ 員工審核(`OFDB691` `OFDM604`) | `OFDM604` 的欄位標籤有「是否為投管部」 |
| 系統管理 / 產品企劃 | ⑥ 參數維護 | 全部是設定檔性質,且全走四眼 |
| **AutoJob(非人)** | `OFDB600` `OFDB609` `OFDB680` | 三支服務都把 `CreateID` / `USERID` / `USER` 參數寫死成字串 `AutoJob`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:86`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:74`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:81`) |

### 0.7 全域開關

| 開關 | 位置 | 影響 |
|---|---|---|
| `SYSTEM_ID` | 畫面上的「交易途徑」選項,傳進每一支拋轉 SP | `1` = 網路、`2` = 語音(**假設**,依據是畫面上只有這兩個選項且 `OFDB60x` 系列固定送網路那個值);`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:519` 的 `WHERE … AND SYSTEM_ID='1'` 寫死網路 |
| `wBMS_CTL_CODE` | 拋轉 / 拋轉回復的模式旗標 | `2` 代表拋轉回復,會先跑 `ValidatePCode` 擋「還有更晚的拋轉資料」(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:215-223`) |
| `OFDM600` 的全站參數 | 一張單列設定表 | 當日申購 / 買回金額上限(自然人 / 法人分開)、密碼累計錯誤次數上限、受益人異動截止時限、自動處理網路開戶後續流程時限 |
| `EXEC_TIMES` / `OPEN_ACC_PROCESS_TIME` / `ALERT_LIMIT_TIMES` | 三支服務各自的排程時間,都存在資料庫不是設定檔 | 見 §6.2 至 §6.4 |
| `ExceptionHandlingMode` | 三支服務的 `App.config` 內**全部被註解掉** | 走 EL 還是 Fusion 由部署機決定,repo 判斷不出來(與 `architecture.md §7` 一致) |

---

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] EC 模組全景:交易拋轉、網路開戶與密碼、員工交易審核、到價通知與扣款核印、參數維護六條線
圖中文字:① 交易拋轉:OFDB600 先跑,五組拋轉才能動 / OFDB600 / 時限截止 Service / IPJB621 OFDB601 / 申購 OFD611A / IPJB622 OFDB602 / 買回 OFD612A / IPJB624 OFDB604 / 定額異動 OFD614A / IPJB625 OFDB605 / 受益人變更 OFD615A / IPJB606 / 轉申購 OFD616A / ② 網路開戶與密碼:七支 B 加三支 M 共用 OFD607A / OFDB609 / 開戶後續 Service / OFDB606 OFDB615 / 重發密碼 未編/編 / OFDB616 OFDB610 / 密碼函 標籤 / OFDB607 OFDB608 / 權限停復 / IPJM614 / 資料變更 四眼 / OFDM602 OFDM607 / 文件需求 繳交 / OFD607A / 主檔在 BMS / ③ 員工交易審核:擋住買回與轉申購拋轉 / OFDB671 / 審核人員 OFD678A / OFDB691 / 逐筆審核 / OFDB690 / 取消 未編 / OFDB672 OFDB673 / 員編變更 送審覆核 / ④ 到價通知   ⑤ 扣款核印 / OFDB680 / 到價計算 Service / OFDB693 OFDM680 / 白名單 發送時間 / IPJB613 / 扣款送件 檔案 / OFDB611 OFDB612 / 扣款發送 回覆 / IPJB614 / 核印 OFD655A / ⑥ 參數維護 15 支 M:全走四眼,PO 端零跨表副作用 / OFDM600 OFDM601 / 全站 逐檔基金參數 / OFDM603 OFDM674 / 手續費 促銷 / OFDM690 694 695 / 基金分類三角 / OFDM69x 其餘 / 四支未編譯
```

*圖:圖 1 EC 全景。橘框=關鍵入口或四眼畫面;白框=一般批次;橘虛框=含寫死值或 Service〔客戶特定〕;黑虛框=唯讀、主檔在別的模組、或整組未編譯。虛線箭頭=卡控相依(員工交易沒審完,買回與轉申購拋不了);六條線之間幾乎不互相呼叫,全靠表與卡控訊息相連。*

六條業務線的地基是**兩張交易暫存檔家族**:客戶在 EC 前台下的單先落在 `OFD611A`(申購)/ `OFD612A`(買回)/ `OFD614A`(定額異動)/ `OFD615`(受益人資料變更)/ `OFD616A`(轉申購),拋轉批次把它們推進核心;而客戶身分的地基是 `OFD601`(網路戶基本資料)與 `OFD607A`(網路戶註冊檔),**這兩張表的主檔在 BMS 不在這裡**(§8.1)。

### 1.2 資料表關係

圖在 `ec.figs.py` 的 `h2:2-`。四個要點:

1. **交易檔五兄弟不是主明細**,是五種交易別各一張,共同點是都有 `BMS_CTL_CODE`(拋轉狀態)與 `SYSTEM_ID`(交易途徑)兩欄。

2. **`OFD607A` 是所有開戶 / 密碼畫面的共同焦點**,七支程式改它但沒有一支擁有它。

3. **`OFDB680` 有一組同名暫存表**(`OFDB680` / `OFDB680_3` / `OFDB680_XML`),不是實體業務表而是到價計算的中繼表(§6.4)。

4. **`OFDM69x` 那一群幾乎都是「一張表一支畫面」的小設定檔**,彼此無外鍵,只有 `OFDM690`(基金對類別)與 `OFDM694` / `OFDM695`(類別字典)構成一組三角。

### 1.3 主要維護畫面的四眼與卡控順序

本片 22 支 M 裡有 16 支走標準四眼(`BaseEVADao` 加 `xTableMapping`),流程完全照 `architecture.md §3`,PO 端**沒有覆寫任何 `After*` 事件**。這一點跟 CAS / BMS 很不一樣:

| 層 | 本片 M 畫面做了什麼 | 錨點樣本 |
|---|---|---|
| UI | 必填與格式檢核(`DoValidate` 加 `validatorManager1`),以及少數業務檢核 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM602.cs:273-287` |
| Ctl | 只做 View 與 Model 的搬運,沒有邏輯 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDM690_Ctl.cs:46` |
| PO | 只在 `BeforeSelect` / `BeforeGetMaintainData` 掛自組 SQL;`Add` / `Update` / `Delete` 全交給 DLL | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:34-35` |
| DLL | 四眼狀態機、`STATUS` 推進、待辦寫入 | 無原始碼,從呼叫端反推 |

只有 7 支 PO 掛了事件(`OFDM601` `OFDM607` `OFDM672` `OFDM674` `OFDM681` `OFDM690` 加非本片的 `OFDM199A`),清單見 §4.1。**其餘 9 支 M 的 PO 檔只有建構子加一行 `MasterTable`,整支 24 到 46 行**(例:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM699OracleDao.cs` 只有 27 行)。

### 1.4 批次 / 報表資料流

圖在 `ec.figs.py` 的 `h2:6-`(本片最重要的一張)。文字版的執行順序:

```
OFDB600(時限截止)──必須先跑────┐
                                ├─> IPJB621 / OFDB601  申購拋轉    -> OFD611A
                                ├─> IPJB622 / OFDB602  買回拋轉    -> OFD612A
                                ├─> IPJB624 / OFDB604  定額異動拋轉 -> OFD614A
                                ├─> IPJB625 / OFDB605  受益人變更拋轉 -> OFD615
                                └─> IPJB606            轉申購拋轉   -> OFD616A
```

這條相依**是硬檢核**,不是文件約定:五支拋轉批次的 PO 在 `Execute` 之前都會先問一次「今天跑過 `OFDB600` 沒有」,沒跑就**阻擋**並回「尚未執行交易截止時間,請先執行OFDB600程式」(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:112`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:115`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs:109`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:52`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:97`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs:112`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:115`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB624OracleDao.cs:109`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:52`)。

另外三條獨立的批次線,彼此無相依:

```
OFDB609(網路開戶後續處理,Service)─> OFD607A / OFD607 / LOG602 / Z_OPACT + LDAP
OFDB680(到價通知,Service)────────> OFDB680* 暫存 -> OFD682A/683A/684A/696A + 發信
OFDB671 -> OFDB672 -> OFDB673 (員工代碼變更的送審三段)
```

### 1.5 一日作業泳道

| 時點 | 誰 | 做什麼 | 錨點 |
|---|---|---|---|
| 盤中隨時 | 客戶(EC 前台) | 下單,資料落進 `OFD611A` 等交易檔,`BMS_CTL_CODE` 為未拋轉 | 外部系統,ATLAS 只讀 |
| 每天定時(資料庫設定) | `OFDB600_Service` | 依 `OFD681` 的 `EXEC_TIMES` 跑網路交易時限截止,並寄審核取消通知信 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:65-75` |
| 截止之後 | 交易室 | 依交易別逐支跑拋轉(五組畫面) | §6.5 |
| 每天定時 | `OFDB609_Service` | 依 `OPEN_ACC_PROCESS_TIME` 自動推進網路開戶、發密碼、同步 LDAP | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:65-101` |
| 每天定時 | `OFDB680_Service` | 依 `ALERT_LIMIT_TIMES` 逐檔基金算到價提示並發信 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:57-104` |
| 白天不定時 | 客服 | 補發密碼、列印密碼函與標籤(`OFDB615` `OFDB616` `OFDB610`) | §6.7 |
| 白天不定時 | 投管部 | 員工交易審核(`OFDB691`)、取消員工交易(`OFDB690`) | §6.8 |
| 扣款日 | 交易室 | `IPJB613` 送件、`OFDB611` / `OFDB612` 扣款結果、`IPJB614` 核印 | §6.9 |

---

## 2. 資料模型

```text
[圖] EC 的交易檔五兄弟、網路戶身分表、參數與字典、到價通知暫存表,以及四組跨模組共用表
圖中文字:交易檔五兄弟:不是主明細,是五種交易別各一張,共用 BMS_CTL_CODE 與 SYSTEM_ID / OFD611A / 單筆申購 / OFD612A / 買回 / OFD614A / 定額異動 / OFD615A / 受益人變更 / OFD616A / 轉申購 / OFD618A / 拋轉記錄 僅 IPJ 版寫 / 網路戶身分:主檔在 BMS,EC 七支裸 UPDATE / OFD601 / BMS 明細 唯讀 join / OFD607A / BMS 明細 EC 改欄位 / OFD601CHG OFD607ACHG / 變更單 IPJM614 / OFD608A / 文件繳交 OFDM607 / 參數與字典:一張表一支畫面,只有分類那組有三角 / OFD600A / 全站 OFDM600 / OFD606A / 逐檔基金 OFDM601 / OFD690A / 基金對類別 OFDM690 / OFD691A OFD695A / 類別 區域字典 / 到價通知:三張暫存表跟畫面代號同名 / OFD680A / 發送時間 OFDM680 / OFD688A / 白名單 OFDB693 四眼 / OFDB680 _3 _XML / 暫存 中繼 / OFD682A 683A 684A / 結果 加 OFD696A / 跨模組:改這四組要一起看別的模組 / OFD681 / 通知名單 RSP 也用 / RSP006A / 定額契約 OFDB673 改 / OFD221A OFD251A / 申購單 買回單 / LOG602 Z_OPACT / 密碼異動 作業記錄
```

*圖:圖 2 EC 資料表關係。橘框=本片擁有(有 xTableMapping 或唯一維護入口);黑虛框=主檔在別的模組或唯讀 join;橘虛框=暫存表。OFD601 與 OFD607A 那一組是本片最大的陷阱:EC 天天改,擁有權卻在 BMS。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

**17 支有活的宣告**,全部在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/` 下:

| 畫面 | 實體表 `dbTableName` | vdb DataTable | 明細 | 錨點 |
|---|---|---|---|---|
| `OFDB693` | `OFD688A` | `OFDB693` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:30` |
| `OFDM600` | `OFD600A` | `OFDM600` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM600OracleDao.cs:40` |
| `OFDM601` | `OFD606A` | `OFDM601` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:38` |
| `OFDM604` | `OFD676A` | `OFD616` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM604OracleDao.cs:14` |
| `OFDM607` | `OFD608A` | `OFDM607` | 無(多筆主檔) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:31` |
| `OFDM670` | `OFD670A` | `OFDM670A` | `OFD671A` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM670OracleDao.cs:30-31` |
| `OFDM672` | `ivr_map_wav` | `OFDM672` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM672OracleDao.cs:31` |
| `OFDM674` | `OFD674A` | `OFDM674` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM674OracleDao.cs:29` |
| `OFDM680` | `OFD680A` | `OFDM680` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM680OracleDao.cs:20` |
| `OFDM681` | `OFD681` | `OFDM681` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:22` |
| `OFDM690` | `OFD690A` | `OFDM690` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM690OracleDao.cs:28` |
| `OFDM694` | `OFD695A` | `OFDM694` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM694OracleDao.cs:30` |
| `OFDM695` | `OFD691A` | `OFDM695` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM695OracleDao.cs:31` |
| `OFDM696` | `LOG616A` | `LOG616` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM696OracleDao.cs:31` |
| `OFDM697` | `OFD685A` | `OFDM697` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM697OracleDao.cs:23` |
| `OFDM698` | `OFD686A` | `OFDM698_Master` | 無(明細靠自組 SQL) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM698OracleDao.cs:35` |
| `OFDM699` | `OFD699A` | `OFDM699` | 無 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM699OracleDao.cs:23` |

**三個要注意的地方:**

1. **`OFDM604` 的兩個名字對不上。** `dbTableName` 是 `OFD695A` 家族外的 `OFD676A`,`vdbTableName` 卻叫 `OFD616` —— 而 `OFD616` 同時是 `OFDB690` / `OFDB691` 的 vdb DataTable 名。同一個字串在不同 vdb 上指涉不同東西,`grep OFD616` 會撈到三支無關的畫面。

2. **`OFDM672` 的表名是小寫底線 `ivr_map_wav`**,全庫唯一不照 `OFDxxxA` 命名的實體表。從畫面標籤「基金代碼 / 音檔代碼」判斷,它是語音系統的基金播音檔對照表〔客戶特定〕。

3. **`OFDM681` 的表名 `OFD681` 沒有 `A` 字尾**,而且跟 `OFDB600` / `OFDB680` 讀的 `OFD681` 是**同一張表**(`OFDB600Model.xsd` 與 `OFDB680Model.xsd` 都有 `OFD681` 這個 DataTable)。所以 `OFDM681`(Email 發送名單維護)維護的就是兩支服務用來決定「寄給誰」的那張表 —— 但 `OFDM681` **沒有進編譯**(§0.4),表示這張表現在只能用別的方式維護。這是本片最值得追問的一條。

**兩支被註解掉的宣告:**

| 畫面 | 被註解的內容 | 錨點 |
|---|---|---|
| `OFDM602` | `//this.MasterTable = new xTableMapping("OFD605A", "OFDM602_Master");` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:36` |
| `OFDM603` | `//this.MasterTable = new xTableMapping("OFD604A", "OFDM603_Master");` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM603OracleDao.cs:29` |

這兩支的 Dao 分別是 1,172 與 1,345 行,**全部的 SQL 自己寫**,四眼動作也全部自己實作(`EVAType.Add` / `Modify` / `Verify` / `Approve` / `Delete` / `ApproveDelete` / `UnDelete` / `Reject` / `Resend` 九個值在這兩支裡各出現一輪,例 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:573-606`)。它們是本片唯二「自己重寫一遍四眼」的畫面,詳見 §4.9 與 §4.10。

### 2.2 B 批次的「主檔」怎麼看 —— xsd DataTable 對照

28 支 B 沒有 `xTableMapping`,改看 `<代號>Model.xsd` 的 `msprop:Generator_TableClassName`。這張表是本片反查表用途最高的一張:

| 畫面 | xsd 的 DataTable | 推測意義 |
|---|---|---|
| `IPJB606` | `OFD616A` | 轉申購交易檔 |
| `IPJB613` | `FILEList` `REPORT_DATA` | 無實體表,純檔案清單與報表資料 |
| `IPJB614` | `OFD655A` | 核印申請檔 |
| `IPJB621` / `OFDB601` | `OFD611A`(加 `OFD041`) | 單筆申購交易檔 |
| `IPJB622` / `OFDB602` | `OFD612A`(加 `OFD041`) | 買回交易檔 |
| `IPJB624` / `OFDB604` | `OFD614A`(加 `OFD041`) | 定額異動檔 |
| `IPJB625` / `OFDB605` | `OFD615`(加 `OFD041`) | 受益人資料變更檔 |
| `OFDB600` | `OFD681` `OFD681_EMP` `OFD681_Err` `OFDB600_COUNT` `OFDB600_TIMES` `OFDB600_EMAIL` | 通知名單加排程時間加前後筆數 |
| `OFDB606` | `OFDB606` `LOG602` | 密碼重發清單加密碼異動 log |
| `OFDB607` | `OFDB607` | 查詢 / 交易權限停復 |
| `OFDB608` | (無 DataTable) | 只吃參數不回結果集 |
| `OFDB609` | `OFDB609` `OFDB609_FILL` `OFDB609_LDAP` `OFDB609_TIMES` `OFD609_EMP` | 開戶後續處理的五個結果集 |
| `OFDB610` | `OFD601` `OFD607A` `OFD610A` `OFD610A_Temp` `OFD623A` `GetBF_SRNO` `Query` `Tag` | 實體密碼函列印 |
| `OFDB611` / `OFDB612` | `OFDB611` / `OFDB612` | 扣款發送與扣款結果 |
| `OFDB615` | `OFDB615` `OFDB615_LDAP` `OFDB615_MAIL` | 重發網路密碼 |
| `OFDB616` | `OFDB616` | 補發密碼函與匯出名單 |
| `OFDB671` | `OFDB671` | 審核人員設定 |
| `OFDB672` | `OFD221A` `OFD251A` `RSP006A` | 員工代碼 / 銷售機構整批變更(**跨模組**,§8.2) |
| `OFDB673` | `OFD221A` `OFD251A` `RSP006A` `OFDB672` | 上一支的覆核 |
| `OFDB680` | `OFD681` `OFDB680` `OFDB680_3` `OFDB680_4` `OFDB680_COUNT` `OFDB680_Check` `OFDB680_Fund` `OFDB680_NAV` `OFDB680_TIMES` `OFDB680_XML` | 到價通知的十個結果集 |
| `OFDB690` | `OFD616` `OFD681` `OFDB690_ALLOT` `OFDB690_REDEM` `OFDB690_RSP` `OFDB690_RSP_CHG` `OFDB690_SWITCH` | 取消員工交易,五種交易別各一張 |
| `OFDB691` | `OFD616` `OFDB691_ALLOT` `OFDB691_REDEM` `OFDB691_RSP` `OFDB691_RSP_CHG` `OFDB691_SWITCH` | 員工交易審核,同上五種 |
| `OFDB693` | `OFDB693_Master` `OFDB693_Fund` | 到價通知的基金白名單 |
| `IPJM614` | `IPJM614` `IPJM614_Master` `OFD601CHG` `OFD607A` `OFD607ACHG` | 網路開戶資料變更(唯一的 IPJ 型 M) |

> **`OFD041` 出現在四支拋轉批次的 `Model.xsd`(非 `_9i` 版)但不在 `_9i` 版**(`OFDB602_9iModel.xsd` 與 `OFDB604_9iModel.xsd` 只剩交易檔一張)。程式實際用的是 `_9i` 版(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs` 全檔用 `OFDB602_9iModelVDB`),所以 `OFD041` 那半邊已經不在執行路徑上。**這是假設**,依據是 Dao 只 `cast` 到 `_9i` 型別。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

本片的 xsd **絕大多數沒有填 `msdata:Caption`** —— 68 個 `*Model.xsd` 裡只有 10 個有。有填的整理如下(這是全部,沒有省略):

| 表 / vdb | 欄位 | Caption |
|---|---|---|
| `OFDM601`(`OFD606A`) | `SYSTEM_ID` | 交易途徑 |
|  | `SYSTEM_NM` | 交易途徑 |
|  | `FUND_ID` | 基金代碼 |
|  | `FUND_SH_NM` | 基金簡稱 |
|  | `INTRO_FILE_URL` | 網頁公開說明書網址 |
| `OFDM607`(`OFD608A`) | `NECESSARY_YN` | 是否為必要文件 |
| `OFDM670`(`OFD670A`) | `FINANCIAL_CODE` | 理財活動代碼 |
|  | `FINANCIAL_DESC` | 理財活動說明 |
|  | `FINANCIAL_SHNM` | 理財活動簡稱 |
|  | `FINANCIAL_BNG_DATE` | 理財活動起始日期 |
|  | `FINANCIAL_END_DATE` | 理財活動終止日期 |
| `OFDM671A`(明細) | `PARAM_NAME` / `PARAM_VALUE` / `PARAM_DESC` | 參數名稱 / 參數值 / 參數描述 |
| `OFDM680`(`OFD680A`) | `ALERT_TIMES` | 到價提示發送次數設定 |
|  | `ALERT_LIMIT_TIMES` | 到價提示自動發送時間 |
| `OFDM681`(`OFD681`) | `SEND_TYPE` | Email發送類型 |
|  | `EMAIL` | 通知Email帳號 |
|  | `EMAIL_NAME` | 中文姓名 |
| `OFDM690`(`OFD690A`) | `FUND_ID` / `FUND_SH_NM` | 基金代碼 / 基金簡稱 |
|  | `INV_AREA_TYPE` / `INV_AREA_TYPE_NM_C` | 基金投資區域代碼 / 基金投資區域名稱 |
|  | `FUND_TYPE` / `FUND_TYPE_NM_C` | 基金所屬類別代碼 / 基金所屬類別名稱 |
| `OFDM694`(`OFD695A`) | `INV_AREA_TYPE` | 基金投資區域代碼 |
|  | `INV_AREA_TYPE_NM_C` / `_NM_E` | 基金投資區域中文 / 英文名稱 |
| `OFDM695`(`OFD691A`) | `FUND_TYPE` | 基金所屬類別代碼 |
|  | `FUND_TYPE_NM_C` / `_NM_E` | 基金所屬類別中文 / 英文名稱 |
| `OFDM697`(`OFD685A`) | `PRODUCT_ID` / `DESCRIPTION` | 產品代碼 / 產品名稱說明 |
|  | `COMPAIGN_CODE` | 促銷活動代碼(**原文就拼錯**,正確拼法是 `CAMPAIGN`) |
|  | `CRNCY_CD` / `DISC_RATE` | 幣別代碼 / 優惠折數 |
|  | `BNG_AMT` / `END_AMT` | 申購起始金額 / 申購終止金額 |
|  | `ALLOT_FEE_RATE` | 申購手續費率 |
| `OFDM698`(`OFD686A`) | `FUND_ID` / `FUND_SH_NM` / `PRODUCT_ID` | 基金代碼 / 基金中文簡稱 / 產品代碼 |
| `OFDB693`(`OFD688A`) | `FUND_ID` / `FUND_SH_NM` | 基金代碼 / 基金中文簡稱 |

**其餘畫面的欄位中文名只能從 Designer 的標籤文字反推**(本文 §4 / §6 各節的欄位說明就是這樣來的,一律用 `grep -n 'Text = "'` 取得,**沒有 Read 任何 `*.Designer.cs`**)。

### 2.4 主鍵與四眼欄位

有 `msdata:Caption` 的 xsd 裡,四眼欄位的完整集合長這樣(取自 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDM697_9iModel.xsd`,是本片唯一一份把四眼欄位全部標中文的):

| 欄位 | Caption | 屬於哪一眼 |
|---|---|---|
| `DATAID` | 資料識別碼 | 送審批次識別(`Guid.NewGuid()`,見 `architecture.md §3`) |
| `STATUS` | 資料狀態碼 | 狀態機 |
| `CREATEID` / `CREATEDATE` | 資料建立者 / 日期 | 第零眼 |
| `UPDATEID` / `UPDATEDATE` | 最後修改者 / 日期 | 第零眼 |
| `ENTRYID` / `ENTRYDATE` | 資料輸入者 / 日期 | 第一眼 Entry |
| `VERIFYID` / `VERIFYDATE` | 資料確認者 / 日期 | 第二眼 Verify |
| `APPROVEID` / `APPROVEDATE` | 資料覆核者 / 日期 | 第三眼 Approve |
| `REJECTID` / `REJECTDATE` | 資料退回者 / 日期 | 退回 |

這組欄位由 `EVAStringHelper.AllEVAColumnsForSelect("<表名>")` 統一產生,PO 只要在 SELECT 尾端接一行就好(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:112`)。**主鍵欄位在 xsd 裡沒有標 `msdata:PrimaryKey`**,只能從 SQL 的 `WHERE` 反推,逐支列在 §4。

### 2.5 狀態碼(從程式反推,標來源)

**本片的四眼 `STATUS` 值完全沒有寫死在 C# 裡** —— 全庫 `STATUS = '<值>'` 的字面量只有四處,而且都不是四眼狀態:

| 字面量 | 出處 | 語意(推測) |
|---|---|---|
| `STATUS = '0'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:398` | 扣款檔的「未送件」 |
| `STATUS = '1'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:251` | 「已送件」 |
| `STATUS = '2'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:307` | 「重送 / 取消」 |
| `STATUS='0'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:919` | 密碼狀態的「正常」 |

四眼狀態的推進全在 DLL 裡(`architecture.md §3` 已反推出 10 個 `EVAType` 與狀態值域),本片不重複。

**真正在本片被當狀態用的是這三個欄位:**

| 欄位 | 值 | 語意(推測) | 依據 |
|---|---|---|---|
| `BMS_CTL_CODE` | `1` = 拋轉、`2` = 拋轉回復 | 拋轉方向旗標,同時也存在交易檔上代表「已拋轉否」 | 畫面 `uoptBMS_CTL_CODE` 兩個選項,PO 用 `wBMS_CTL_CODE == "2"` 分流(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:215`);`OFDB605OracleDao.cs:301` 的 SQL 用 `where BMS_CTL_CODE='1'` 找已拋轉 |
| `SYSTEM_ID` | `1` = 網路、`2` = 語音 | 交易途徑 | `OFDB610OracleDao.cs:519` 寫死 `SYSTEM_ID='1'`;畫面只有兩個實際選項 |
| `EXE_TYPE` | `1` | 到價通知的執行別 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:76` 寫死 |
| `RunType` | `01` | 到價通知的執行模式(自動) | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:82` 寫死 |
| `ReturnRowCount` | `99` | 三支服務共用的「不算錯誤」魔術值 | `OFDB600_Service.cs:91`、`OFDB609_Service.cs:83`、`OFDB680_Service.cs:88` 三處一致 |

> ⚠ `ReturnRowCount == 99` 這個魔術值在三支服務裡都是「即使 `ReturnCode == false` 也不寫 EventLog」。**repo 內找不到任何地方產生 99 這個值** —— 產生它的一定是版控外的 SP 或 DLL。要知道什麼情況會回 99,得去問資料庫。這是**假設**,依據是三處一致的比對式與 repo 內零個賦值點。

### 2.6 `PO/PO.EC/MSSQL/` —— 30 個檔,2 個活的

這一節回答派工單的「`MSSQL/` 目錄還有多少東西活著」。

**逐檔掃過的結果:**

| 狀態 | 檔數 | 合計行數(概估) |
|---|---|---|
| 有活的 `public class` | **2** | 364 |
| 整支類別被 `//` 註解掉 | **28** | 約 9,700 |

兩個活的:

| 檔 | 類別與基底 | `MasterTable` | 錨點 |
|---|---|---|---|
| `OFDM607_PO.cs` | `OFDM607_PO : MultiRowEVAPO` | `MasterTable.Add(new TableMapping("OFD608A", "OFDM607"))` | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM607_PO.cs:15` 與 `:20` |
| `OFDM681_PO.cs` | `OFDM681_PO : BasicEVAPO` | `MasterTable = new TableMapping("OFD681", "OFDM681")` | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM681_PO.cs:12` 與 `:17` |

**但這兩個活類別也沒有人用:**

- `OFDM607` 的 Control 走的是 `IOFDM607PO` 介面,實作方是 `OFDM607OracleDao`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:21`),`OFDM607_PO` 沒有實作那個介面,是舊世代遺留。

- `OFDM681` 的整條六層**都沒有進編譯**(§0.4),所以 `OFDM681_PO` 編得出來但呼叫不到。

**結論:`MSSQL/` 這個目錄實際貢獻 0 行執行期邏輯,但 30 個檔全部掛在 `PO.EC.csproj:165-194` 裡照樣編譯。** 這解釋了 `architecture.md §3` 為什麼會在這裡找到 `TA_PO` 僅存的兩個被註解宣告(`OFDM603_PO.cs:18` 與 `OFDM694_PO.cs:20`)—— 那只是這 28 個死檔裡的兩個。

**`OFDM603` 與 `OFDM694` 現在走哪條路?**

| 畫面 | 死掉的舊路 | 活著的新路 |
|---|---|---|
| `OFDM603` | `MSSQL/OFDM603_PO.cs:18` 的 `//public class OFDM603_PO : TA_PO`,整檔 853 行全註解 | `Oracle/OFDM603OracleDao.cs:23` 的 `OFDM603OracleDao : BaseEVADao, IOFDM603PO`,1,345 行,`MasterTable` 也被註解,SQL 與四眼全自己寫 |
| `OFDM694` | `MSSQL/OFDM694_PO.cs:20` 的 `//public class OFDM694_PO : TA_PO`,整檔 935 行全註解 | `Oracle/OFDM694OracleDao.cs:23` 的 `OFDM694OracleDao : BaseEVADao, IOFDM694PO`,只有 34 行,`MasterTable = new xTableMapping("OFD695A", "OFDM694")` |

兩支的重寫方向完全相反:`OFDM603` 從 935 行的 `TA_PO` 換成 1,345 行的手寫 Dao(更肥),`OFDM694` 從 935 行縮成 34 行的標準四眼 Dao(更瘦)。**同一批重構,兩種結果**。

### 2.7 與其他模組共用的表

| 表 | 本片怎麼用 | 主檔擁有者 | 影響面 |
|---|---|---|---|
| `OFD601` | 七支開戶類程式裸 `UPDATE`;`OFDB610Model.xsd` 拿來 join 取地址與姓名 | **BMS**(`BMSM001` / `BMSM006` 的 `DetailTable`) | §8.1 |
| `OFD607A` | 同上,加上 `PROCESS_YN` / `DOC_SEND_DT` / `EC_PSW` / `ES_PSW` 的直接改寫 | **BMS**(同上) | §8.1 |
| `OFD607ACHG` / `OFD601CHG` | `IPJM614` 的變更單明細 | BMS 的 `BMSM006` 也寫 | §8.1 |
| `RSP006A` | `OFDB672` / `OFDB673` 改員工代碼與銷售機構 | **RSP**(`rsp.md §2`) | §8.2 |
| `OFD221A` / `OFD251A` | 同上(申購單 / 買回單) | OFD 本體 | §8.2 |
| `OFD681` | `OFDB600` 與 `OFDB680` 讀它決定寄信名單;`OFDM681` 維護它(但未編譯) | 本片(`OFDM681`) | §8.3 |
| `OFD616` | `OFDB690` / `OFDB691` 的員工交易檔;`OFDM604` 的 vdb 也叫這名字但指 `OFD676A` | 待查(本片只讀寫不宣告) | §2.1 註 1 |
| `LOG602` | `OFDB606` / `OFDB609` / `OFDB615` / `OFDB616` 寫密碼異動記錄 | 待查 | 附錄 A |
| `Z_OPACT` | `OFDB609` 寫(名稱像作業記錄檔) | 待查 | 附錄 A |

---

## 3. 畫面清冊

本片 50 支:**28 支 B、22 支 M、0 支 I、0 支 R**。

「六層」欄位的三種值:**齊** = 檔在且進 csproj;**未編** = 檔在但四個 csproj 一致排除(§0.4);**缺** = 檔不存在。「xsd」欄位:**`_9i`** = 只有 `_9i` 命名那份;**雙份** = `XxxModel.xsd` 與 `Xxx_9iModel.xsd` 並存;**單份** = 只有非 `_9i` 那份。

> **`_9i` 的假警報在本片是「兩層假警報疊在一起」。** `architecture.md §9` 記過 IPJ 的 15 支畫面「六層不齊」全部是 `_9i` 命名造成的。本片的 8 支 `IPJ*` 確實同樣是 `_9i`(`IPJB606_9iModel.xsd` / `IPJB606_9iView.xsd` 都在),**但掃描器對它們還多報一個「PO 缺」** —— 那是第二層假警報,原因是 PO 檔叫 `IPJB606OracleDao.cs` 不叫 `IPJB606_PO.cs`(§0.3 第一層)。所以 `atlas_scan.py --screen IPJB606` 會回報「缺 PO / Model / View」三層,實際上**一層都不缺**。

> 而且 `_9i` 不是 IPJ 專利:本片 `OFDB615` `OFDB616` `OFDB693` `OFDM670` `OFDM697` `OFDM698` `OFDM699` 也只有 `_9i` 版,另有 16 支是新舊**雙份並存**。雙份時程式實際用哪一份,要看 Dao 裡 `cast` 到哪個型別 —— 本片一律是 `_9i` 版(見 §2.2 註)。

### 3.1 維護 M(22 支)

| 代號 | 中文名(推測,待選單表) | UI | Pxy | Ctl | PO | xsd | 主表 | 明細 | 備註 |
|---|---|---|---|---|---|---|---|---|---|
| `IPJM614` | 網路開戶資料變更 | 齊 | 齊 | 齊 | 齊 | `_9i` | 無宣告 | `OFD601CHG` `OFD607A` `OFD607ACHG` | 唯一有四眼基底卻無 `xTableMapping` |
| `OFDM600` | 網路交易全站參數設定 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD600A` | 無 | PO 只有 46 行 |
| `OFDM601` | 基金網路交易參數維護 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD606A` | 無 | 本片欄位最多的一支 |
| `OFDM602` | 網路交易文件需求清單設定 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD605A`(**註解**) | 無 | 1,172 行,自寫四眼 |
| `OFDM603` | 網路交易手續費設定 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD604A`(**註解**) | 無 | 1,345 行,自寫四眼 |
| `OFDM604` | 員工交易審核不核准原因維護 | 齊 | 齊 | 齊 | 齊 | 單份 | `OFD676A` | 無 | PO 只有 24 行 |
| `OFDM607` | 網路開戶文件繳交維護 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD608A` | 無(多筆主檔) | 唯一 `BaseMultiRowEVADao` |
| `OFDM670` | 理財活動設定 | 齊 | 齊 | 齊 | 齊 | `_9i` | `OFD670A` | `OFD671A` | 唯一有明細表的 M |
| `OFDM672` | IVR 基金音檔對照維護 | 齊 | 齊 | 齊 | 齊 | 單份 | `ivr_map_wav` | 無 | 表名小寫〔客戶特定〕 |
| `OFDM674` | 基金促銷設定 | 齊 | 齊 | 齊 | 齊 | 單份 | `OFD674A` | 無 |  |
| `OFDM680` | 到價提示發送時間設定 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD680A` | 無 | 餵 `OFDB680_Service` |
| `OFDM681` | 通知 Email 名單維護 | **未編** | **未編** | **未編** | **未編** | 單份 | `OFD681` | 無 | 餵 `OFDB600` / `OFDB680` 的寄信名單 |
| `OFDM690` | 基金所屬類別設定 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD690A` | 無 |  |
| `OFDM691` | 投資收益顯示顏色設定 | **未編** | **未編** | **未編** | **只剩註解** | 單份 | 無 | 無 |  |
| `OFDM692` | 網頁轉址設定 | **未編** | **未編** | **未編** | **只剩註解** | 單份 | 無 | 無 |  |
| `OFDM693` | 核印不成功原因代碼維護 | **未編** | **未編** | **未編** | **只剩註解** | 單份 | 無 | 無 |  |
| `OFDM694` | 基金投資區域代碼維護 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD695A` | 無 | 舊 `TA_PO` 版死在 `MSSQL/` |
| `OFDM695` | 基金所屬類別代碼維護 | 齊 | 齊 | 齊 | 齊 | 雙份 | `OFD691A` | 無 |  |
| `OFDM696` | 網路瀏覽 LOG 代碼維護 | 齊 | 齊 | 齊 | 齊 | 雙份 | `LOG616A` | 無 |  |
| `OFDM697` | 產品代碼維護 | 齊 | 齊 | 齊 | 齊 | `_9i` | `OFD685A` | 無 |  |
| `OFDM698` | 產品組合設定 | 齊 | 齊 | 齊 | 齊 | `_9i` | `OFD686A` | 無(自寫) | 1,109 行 |
| `OFDM699` | 節日設定維護 | 齊 | 齊 | 齊 | 齊 | `_9i` | `OFD699A` | 無 |  |

> `OFDM691` / `OFDM692` / `OFDM693` 的 PO 欄位寫「只剩註解」:`MSSQL/OFDM691_PO.cs` 等三個檔**有**掛在 `PO.EC.csproj` 裡,所以嚴格說是「進編譯」,但檔案內的 `public class` 那行從 `//` 開始 —— 編出來是空的。而它們的 `_Ctl.cs` 裡明寫 `OFDM691_PO po = new OFDM691_PO();`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDM691_Ctl.cs:38`),**如果 Ctl 有進編譯就會編譯失敗**。這反過來證明 §0.4 的排除是刻意的,不是誤刪。

### 3.2 查詢 I

**本片無 I 畫面。**原因見 §5。

### 3.3 批次 B(28 支)

| 代號 | 中文名(推測) | UI | Pxy | Ctl | PO | xsd | SP(版控外) | 主要寫入表 |
|---|---|---|---|---|---|---|---|---|
| `IPJB606` | 轉申購拋轉(含語音) | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_IPJB606_EXCUTE` | (SP 內) |
| `IPJB613` | 網路定額扣款送件 | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_DDCT_P01` | (SP 內) |
| `IPJB614` | 核印資料處理 | 齊 | 齊 | 齊 | 齊 | `_9i` | 無 | `OFD655A` |
| `IPJB621` | 單筆申購拋轉(含語音) | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_IPJB601_EXCUTE` | `OFD618A` |
| `IPJB622` | 買回拋轉(含語音) | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_IPJB602A_EXCUTE` | `OFD618A` |
| `IPJB624` | 定額異動拋轉(含語音) | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_IPJB604_EXCUTE` | `OFD618A` |
| `IPJB625` | 受益人資料變更拋轉(含語音) | 齊 | 齊 | 齊 | 齊 | `_9i` | `S_EC_IPJB605_EXCUTE` | `OFD618A` |
| `OFDB600` | 網路交易時限截止處理 | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_IPJB600_EXCUTE` | (SP 內)加寄信 |
| `OFDB601` | 單筆申購拋轉(純網路) | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_IPJB601_EXCUTE` | (SP 內) |
| `OFDB602` | 買回拋轉(純網路) | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_IPJB602A_EXCUTE` | (SP 內) |
| `OFDB604` | 定額異動拋轉(純網路) | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_IPJB604_EXCUTE` | (SP 內) |
| `OFDB605` | 受益人資料變更拋轉(純網路) | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_IPJB605_EXCUTE` | (SP 內) |
| `OFDB606` | 重發登入 / 交易密碼 | **未編** | **未編** | **未編** | **未編** | 單份 | 無 | `OFD607A` |
| `OFDB607` | 網路查詢 / 交易權限停復 | 齊 | 齊 | 齊 | 齊 | 單份 | `S_EC_OFDB607_Excute` | (SP 內) |
| `OFDB608` | 受益人網路資料處理 | 齊 | 齊 | 齊 | 齊 | 單份 | `S_EC_OFDB608_Excute` | (SP 內) |
| `OFDB609` | 網路開戶後續自動處理 | 齊 | 齊 | 齊 | 齊 | 單份 | `S_EC_OFDB609_Excute` | `OFD607A` `OFD607` `LOG602` `Z_OPACT` |
| `OFDB610` | 實體密碼函列印與標籤 | **未編** | **未編** | **未編** | **未編** | 單份 | `s_OFDB610_Get` `s_ECFunGetAccountData` | `OFD607A` |
| `OFDB611` | 扣款資料發送 | **未編** | **未編** | **未編** | **未編** | 單份 | 無 | `OFD621A` |
| `OFDB612` | 扣款結果回覆 | 齊 | 齊 | 齊 | 齊 | 雙份 | 無 | `OFD621A` |
| `OFDB615` | 重發網路密碼(含 LDAP) | 齊 | 齊 | 齊 | 齊 | `_9i` | 無 | `OFD607A` `OFD607` `LOG602` |
| `OFDB616` | 補發密碼函與寄送名單匯出 | 齊 | 齊 | 齊 | 齊 | `_9i` | 無 | `OFD607A` `OFD607` `LOG602` |
| `OFDB671` | 員工交易審核人員設定 | 齊 | 齊 | 齊 | 齊 | 單份 | 無 | `OFD678A` |
| `OFDB672` | 員工代碼 / 銷售機構整批變更(送審) | 齊 | 齊 | 齊 | 齊 | 單份 | `S_TA_OFDB672_GET` | `OFDB672` |
| `OFDB673` | 員工代碼 / 銷售機構整批變更(覆核) | 齊 | 齊 | 齊 | 齊 | 單份 | `S_TA_OFDB673_EXE` | (SP 內) |
| `OFDB680` | 到價提示計算與發送 | 齊 | 齊 | 齊 | 齊 | 雙份 | `S_EC_OFDB680_GET` | `OFD682A` `OFD683A` `OFD684A` `OFD696A` 加暫存 |
| `OFDB690` | 取消員工交易 | **未編** | **未編** | **未編** | **未編** | 單份 | `s_OFDB690_Get` | (SP 內) |
| `OFDB691` | 員工交易審核 | 齊 | 齊 | 齊 | 齊 | 單份 | `S_EC_OFDB691_SENDBACK` `s_OFDB691_Booking` | `OFD620A` `OFD621A` `OFD641A` `OFD651A` |
| `OFDB693` | 到價通知基金白名單設定 | 齊 | 齊 | 齊 | 齊 | `_9i` | 無 | `OFD688A`(四眼) |

### 3.4 報表 R

**本片無 R 畫面。**原因見 §7。但 `Dev/ATLAS.EC/Source/UI/UI.EC/` 下有 **5 個 `.rpt`**,掛在 B 畫面上而不是獨立的 R 畫面:

| `.rpt` | 掛在哪 | 進編譯 |
|---|---|---|
| `ApplyForm.rpt` | `ApplyForm.cs`(不屬於任何代號) | 是 |
| `IPJB613RPS.rpt` | `IPJB613RPS.cs` | 是 |
| `OFDB606RPS.rpt` | `OFDB606RPS.cs` | 是,但**宿主畫面 `OFDB606` 未編**(§0.4) |
| `OFDB610RPS.rpt` | `OFDB610RPS.cs` | 是,但**宿主畫面 `OFDB610` 未編** |
| `OFDB616RPS.rpt` | `OFDB616RPS.cs` | 是 |

這是 `architecture.md §6` 說的「R 是命名鐵律的正式例外」在本片的另一種變形:**本片連 R 代號都沒有,報表直接掛在 B 畫面上用 `<代號>RPS` 命名**。

### 3.5 一眼看出差別的五件事

| # | 觀察 | 數字 |
|---|---|---|
| 1 | 50 支裡 **8 支整組未編譯** | 16% |
| 2 | 28 支 B 裡 **只有 1 支走四眼**(`OFDB693`) | 3.6% |
| 3 | 22 支 M 裡 **16 支是「建構子加一行 MasterTable」的標準型** | 73% |
| 4 | PO 層檔名 **`*OracleDao.cs` 49 個、`*_PO.cs` 30 個**,後者只有 2 個活著 | — |
| 5 | 26 處 `GetStoredProcCommand` 指到 **18 支 SP,`DB/` 底下一支都沒有** | 0% 覆蓋 |

---

## 4. 維護畫面(M)— 22 支

```text
[圖] EC 的 22 支維護畫面依 PO 寫法分成三型,加上一支不屬於任何型的 IPJM614
圖中文字:A 標準型 14 支:建構子加一行 MasterTable,四眼全交 DLL,PO 端零卡控 / OFDM600 604 680 / 24 到 46 行 / OFDM694 695 696 / 34 到 35 行 / OFDM697 699 / 27 行 / OFDM698 / 1109 行 SQL 自組 / OFDM691 692 693 / 未編譯 PO 已死 / OFDM670 / 唯一有明細 OFD671A / B 掛事件型 6 支:在建構子掛 Before 事件自組 SQL / OFDM601 / BeforeSelect 加 1 / OFDM607 / 多筆主檔 加 ToDo / OFDM672 / 掛 6 個 最多 / OFDM674 690 / 掛 5 個 加 1 個 / OFDM681 / 未編譯 介面還宣告錯 / C 自寫四眼型 2 支:MasterTable 被註解,xAdd xModify xApprove 全部重寫 / OFDM602 / 1172 行 OFD605A / OFDM603 / 1345 行 OFD604A / STATUS Substring 2 1 / 第三碼 3 等於刪除 / 唯二會判 j 小於等於 0 / 28 支 B 一支都沒有 / 不屬於上面三型:有四眼基底卻沒有 xTableMapping / IPJM614 / 1124 行 SQL 全自寫 / OFD601CHG OFD607A / OFD607ACHG 三張 / FATCA 卡控寫死 UI / 訊息出現兩次
```

*圖:圖 3 M 畫面分群。橘框=標準四眼或關鍵參數;白框=一般;黑虛框=未編譯或主檔在別處;橘虛框=自寫四眼或含寫死值;黑框=無原始碼、從呼叫端反推。全片 22 支 M 沒有任何一支掛 After 事件,也就是沒有任何跨表副作用 —— 跟 BMS 與 RSP 很不一樣。*

### 4.1 共同模式:三種寫法,數量差很多

22 支 M 分成三型,**選錯型去讀會白花時間**:

| 型 | 支數 | 特徵 | PO 行數 | 代表 |
|---|---|---|---|---|
| **A 標準型** | 14 | `: BaseEVADao` 加一行 `MasterTable`,四眼全交給 DLL,PO 只有建構子 | 24 到 205 | `OFDM699`(27 行) |
| **B 掛事件型** | 6 | 同上,但在建構子掛 `BeforeSelect` / `BeforeAdd` 等事件自組 SQL | 93 到 391 | `OFDM601`(391 行) |
| **C 自寫四眼型** | 2 | `MasterTable` 被註解,`xAdd` / `xModify` / `xApprove` / `xApproveDelete` 全部自己重寫一遍 | 1,172 與 1,345 | `OFDM602` `OFDM603` |

B 型掛的事件逐支列(這是全部,沒有省略):

| 畫面 | 掛的事件 | 錨點 |
|---|---|---|
| `OFDM601` | `BeforeSelect` `BeforeGetMaintainData` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:34-35` |
| `OFDM607` | `BeforeSelect` `BeforeGetMaintainData` `BeforeGetToDoData` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:38-40` |
| `OFDM672` | `BeforeSelect` `BeforeGetMaintainData` `BeforeGetToDoData` `BeforeUpdate` `BeforeAdd` `AfterGetMaintainData` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM672OracleDao.cs:26-32` |
| `OFDM674` | `BeforeGetMaintainData` `BeforeGetToDoData` `BeforeAdd` `BeforeUpdate` `BeforeSelect` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM674OracleDao.cs:23-28` |
| `OFDM681` | `BeforeSelect` `BeforeGetMaintainData` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:23-24`(**未編**) |
| `OFDM690` | `BeforeSelect` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM690OracleDao.cs:26` |

**全片 22 支 M 沒有任何一支掛 `After*` 事件。** 意思是「覆核之後還要順手改別張表」這種跨表副作用,在 EC 的維護畫面裡**一個都沒有** —— 跟 BMS(`bms.md §4`)與 RSP(`rsp.md §4`)差很大。EC 的 M 畫面全部是純設定檔維護。

### 4.2 `OFDM601` — 基金網路交易參數維護

**用途(推測):** 逐檔基金逐個交易途徑,設定它在網路 / 語音上能不能買、能不能賣、最低金額、截止時間。本片最關鍵的一張參數表 —— 客戶在前台看到「這檔基金不開放線上申購」就是這裡設的。

- **主表** `OFD606A`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:38`),vdb 叫 `OFDM601`,另有一張查詢用 `OFDM601_Get`。

- **主鍵(從 SQL 反推)**:`SYSTEM_ID` 加 `FUND_ID`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:128-146` 的參數組合)。

- **join 進來唯讀的表**:`OFD062`(基金公司)、`OFD081A`(基金幣別)、`FSK003`(幣別名稱)—— 見 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:112`。

**欄位家族(從 SELECT 清單讀出,`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:88-110`):**

| 家族 | 欄位 | 管什麼 |
|---|---|---|
| 開關 | `EC_ALLOT_YN` `EC_BUC_YN` `EC_REMIT_YN` `EC_REDEM_YN` `EC_SWITCHIN_YN` `EC_SWITCHOUT_YN` `EC_RSP_ALLOT_YN` `EC_UNRSP_YN` `EC_CHG_AMT_YN` | 申購 / 扣款 / 匯款 / 買回 / 轉入 / 轉出 / 定額申購 / 不定額 / 可改金額 |
| 金額下限 | `EC_ALLOT_MIN_AMT_NTD` `EC_ALLOT_MIN_AMT_ORG` `EC_RSP_MIN_AMT_NTD` `EC_RSP_MIN_AMT_ORG` | 台幣 / 原幣兩套 |
| 金額上限 | `EC_RSP_MAX_AMT_NTD` `EC_RSP_MAX_AMT_ORG` `EC_T_ALLOT_LMT` |  |
| 倍數單位 | `EC_AMT_BASE_NTD` `EC_AMT_BASE_ORG` `EC_RSP_AMT_BASE_NTD` `EC_RSP_AMT_BASE_ORG` |  |
| 可銷售額度 | `EC_ALLOT_LMT_AMT` `EC_RSP_LMT_AMT` 加 `ALLOT_LMT_DATE_BNG/END` `RSP_LMT_DATE_BNG/END` | 畫面標籤註明「0表示不控管」 |
| 截止時間 | `EC_BUC_LIMIT_TIME` `EC_REMIT_LIMIT_TIME` `EC_REDEM_LIMIT_TIME` `EC_RSP_LIMIT_TIME` `EC_RSP_CHG_LIMIT_TIME` |  |
| 基準日 | `EC_BUC_BAS_DAY` `EC_REMIT_BAS_DAY` `EC_REDEM_BAS_DAY` `EC_MIN_AMT_BAS_DAY` `EC_BUC_TRADE_DAY` `BOOKING_DAY` `ALERT_NAV_BASE_DATE` | T 加減 N |
| 買回下限 | `EC_REDEM_MIN_UNIT` `EC_REDEM_MIN_REM_UNIT` `EC_REDEM_MIN_AMT` `EC_REDEM_MIN_REM_AMT` | 單位數與金額、餘額兩套 |
| 網頁 | `INTRO_FILE_URL`(公開說明書)`RISK_FILE_URL` `SHOW_ORDER` `RWD_ADDR` |  |
| 境外(2021 新增) | `FH_CD` `SALE_SOP_FEE_YN` `FUND_CATEGORY` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:110` 的註解寫「2021.08.23 EC改版專案 新增境外欄位 by hanna」 |

**卡控總表:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 同一交易途徑內 `SHOW_ORDER` 不可重覆 | 有重覆 | **阻擋**「同一交易途徑，顯示順序不可重覆。」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:306` |
| 四眼各階段 | 全部交給 DLL | — | — | 無自寫 |

**要注意的寫法:** 六個日期欄位在 SELECT 裡被包成 `to_date(decode(<欄>,'','1900/01/01', …))`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM601OracleDao.cs:91-94`)。這是把 NULL 日期換成 `1900/01/01` 帶回畫面 —— **畫面上看到 1900/01/01 等於資料庫是 NULL**,不是真的有人設了那一天。Oracle 的 `decode(x,'',y)` 對 `DATE` 欄位判的是 `x IS NULL`(空字串在 Oracle 等同 NULL),所以這個寫法會成立;但同樣的寫法用在 `VARCHAR2` 欄位就會踩到三值邏輯(附錄 E4)。

### 4.3 `OFDM607` — 網路開戶文件繳交維護

**用途(推測):** 針對某一位網路開戶客戶,勾選他該補哪些文件、哪些已經收到。`NECESSARY_YN` 的 Caption 是「是否為必要文件」。

- **主表** `OFD608A`,**多筆主檔**(`MasterTable.Add`,`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:31`),基底是 `BaseMultiRowEVADao`(`:21`)。全片 22 支 M 只有這一支是多筆型。

- 畫面欄位:受益人 ID、戶號、網路流水號、開戶日期、中文姓名、英文姓名,加一個明細資料 Grid。

- **跨表副作用(唯一的一支):** 存檔時另外下一句裸 SQL 把 `OFD607A` 的處理旗標打成 `Y`:

```
string strSQL = "UPDATE OFD607A SET PROCESS_YN='Y' WHERE BF_SRNO=@BF_SRNO AND SYSTEM_ID='1'";
```

錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM607_PO.cs:213`。**注意這行在 `MSSQL/` 的死路徑上** —— 活著的 `Oracle/OFDM607OracleDao.cs` 也有等價的寫法(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:194-198` 的字串串接段)。兩份並存,改一份不會同步另一份。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 補件代碼必填 | 空白 | **阻擋**「請輸入補件代碼」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM607p0.cs:98` |
| 帶資料 | Grid 點選列不可為 null | null | **阻擋**「請傳入Grid中點選的該筆資料，不可為Null」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM607p0.cs:37` |
| 修改 | SQL 執行失敗 | 例外 | **阻擋**「修改失敗，請檢查」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:268` 與 `:284` |

### 4.4 `OFDM602` — 網路交易文件需求清單設定(自寫四眼之一)

**用途(推測):** 定義「哪一種開戶情境要附哪些文件」。`REQ_DOC_KIND`(文件需求種類)對 `DOC_CD`(文件代碼)的一對多。

- **主表宣告被註解**:`//this.MasterTable = new xTableMapping("OFD605A", "OFDM602_Master");`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:36`)。

- **主鍵(從 SQL 參數反推)**:`REQ_DOC_KIND` 加 `DOC_CD`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:425-426`)。

- **自己重寫的四眼方法**(全片只有這支與 `OFDM603` 這樣做):

| 方法 | 行 | 做什麼 |
|---|---|---|
| `xQuery` | `:39` | 自組 SQL 查詢 |
| `xGetMaintainData` | `:108` | 帶維護資料 |
| `xAdd` | `:235` | 先 `IsDataExit` 擋重覆,再逐列 INSERT 加 `SetUseCaseSecurity(…, EVAType.Add, dataid, …)` |
| `xModify` | `:349` | 分 Delete / Add / Update 三段,每段前先 `IsDataChange` |
| `xDelete` | `:559` | 依 `EVAFlowKind == 1` 決定直接實刪還是只推狀態 |
| `xUnDelete` `xResend` `xVerify` `xReject` | `:578` `:583` `:588` `:593` | 一行轉呼叫 `SetEVAStatus` |
| `xApprove` | `:598` | **看 `STATUS` 第三個字元決定要不要實刪** |
| `xApproveDelete` | `:609` | 實體 DELETE 加 `EVAType.ApproveDelete` |
| `SetEVAStatus` | `:751` | 共用的狀態推進 |

**`STATUS` 的內部結構(反推,這是全片唯一看得到 `STATUS` 被拆字元的地方):**

```
if (vdb.DataEntity.OFDM602_Master[0].STATUS.Substring(2, 1) == "3") //刪除動作
    return xApproveDelete(modelVDB);
```

錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:603-606`。**推論:`STATUS` 至少三碼,第三碼(索引 2)代表動作別,`3` = 刪除。** 這是**假設**,依據是這一處 `Substring(2,1)` 與 `OFDM603OracleDao.cs` 的同款寫法;`architecture.md §3` 反推的 `STATUS` 值域可以跟這條交叉驗證。

**卡控總表:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | `IsDataExit` 同鍵已存在 | 存在 | **阻擋**「此筆資料已存在，請檢查後重新執行」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:252` |
| 修改 / 刪除 / 覆核前 | `IsDataChange` 別人先改過 | 改過 | **阻擋**「此筆資料已異動，請檢查後重新執行」(四處) | `:412` `:486` `:624` `:768` |
| 存檔前(UI) | 文件代碼必填 | 空白 | **阻擋**「文件代碼 必須輸入」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM602.cs:273` |
| 存檔前(UI) | 是否為必要文件必填 | 空白 | **阻擋**「是否為必要文件 必須輸入」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM602.cs:281` |
| 存檔前(UI) | 是否需要核印必填 | 空白 | **阻擋**「是否需要核印,必須輸入!」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDM602.cs:287` |
| 每一次 `ExecuteNonQuery` 後 | `j <= 0`(沒有異動到任何列) | 成立 | **阻擋**加 rollback | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:430-434` |

> 最後一條值得特別記:**`OFDM602` 與 `OFDM603` 是本片唯二會檢查 `ExecuteNonQuery` 回傳值的程式**。28 支批次裡一支都沒有(附錄 E1)。

### 4.5 `OFDM603` — 網路交易手續費設定(自寫四眼之二,兼死碼基底的僅存宣告之一)

**用途(推測):** 逐檔基金、逐交易途徑、逐幣別設定網路申購手續費率,可設「永久費率」或「某期間費率」。

- **舊路已死:** `MSSQL/OFDM603_PO.cs` 整檔 853 行,第 18 行的 `//public class OFDM603_PO : TA_PO` 是 `architecture.md §3` 記的 `TA_PO` 僅存兩個宣告之一,**整行被註解**。

- **新路:** `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM603OracleDao.cs:23` 的 `OFDM603OracleDao : BaseEVADao, IOFDM603PO`,1,345 行,`MasterTable` 也被註解(`:29`,原本指 `OFD604A`)。

- **所以「`OFDM603` 現在走哪條路」的答案是:走 `Oracle/OFDM603OracleDao.cs`,而且它跟 `OFDM602` 一樣把整套四眼自己重寫了一遍。**

**畫面欄位(從 Designer 標籤反推):** 費率種類(永久費率 / 某期間費率)、申購日(起)/(迄)、幣別代碼、基金代碼、交易途徑、手續費類型(前收 / 後收)、備註。

**卡控總表:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 同鍵已存在 | 存在 | **阻擋**「此筆資料已存在，請檢查後重新執行」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM603OracleDao.cs:322` |
| 修改 / 刪除 / 覆核前 | `IsDataChange` | 改過 | **阻擋**「此筆資料已異動，請檢查後重新執行」(四處) | `:488` `:578` `:722` `:858` |

**費率期間沒有重疊檢核。** 畫面允許同一檔基金設多筆「某期間費率」,但 1,345 行裡找不到任何「新的期間不可與既有期間重疊」的判斷 —— **兩筆期間重疊時哪一筆生效,由版控外的取價邏輯決定,repo 判斷不出來**。這是**假設**,依據是全檔搜尋 `BNG` / `END` 的比較式只出現在 SQL 的 `WHERE` 條件裡,沒有出現在檢核段。

### 4.6 `OFDM694` — 基金投資區域代碼維護(死碼基底的僅存宣告之二)

**用途(推測):** 維護「亞洲 / 歐洲 / 新興市場」這類投資區域的代碼與中英文名。

- **舊路已死:** `MSSQL/OFDM694_PO.cs` 整檔 935 行,`:20` 的 `//public class OFDM694_PO : TA_PO` 被註解。

- **新路:** `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM694OracleDao.cs:23`,**只有 34 行**,`MasterTable = new xTableMapping("OFD695A", "OFDM694")`(`:30`),不掛任何事件,四眼全交 DLL。

- **跟 `OFDM603` 對照:同一批重寫,`OFDM603` 變成 1,345 行的手寫怪物,`OFDM694` 變成 34 行的標準型。** 這說明「重寫成 Dao」並不是統一的做法,而是逐支各憑本事。

| 欄位 | Caption |
|---|---|
| `INV_AREA_TYPE` | 基金投資區域代碼 |
| `INV_AREA_TYPE_NM_C` | 基金投資區域中文名稱 |
| `INV_AREA_TYPE_NM_E` | 基金投資區域英文名稱 |

**卡控:PO 端一條都沒有**,全靠 UI 的 `validatorManager1` 與四眼 DLL。

### 4.7 `OFDM681` — 通知 Email 名單維護(有主檔,但未編譯)

**用途(推測):** 維護「系統要寄通知信給誰」的名單,按 `SEND_TYPE`(Email發送類型)分群。

- **主表** `OFD681`,vdb `OFDM681`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:22`)。掛 `BeforeSelect` 與 `BeforeGetMaintainData`(`:23-24`)。

- **同時有兩份 PO:** `MSSQL/OFDM681_PO.cs:12` 的 `OFDM681_PO : BasicEVAPO` 是本片 30 個 `MSSQL/` 檔裡**唯二活著的類別之一**(§2.6),而且**它才是進編譯的那一份** —— `Oracle/OFDM681OracleDao.cs` 沒有掛在 `PO.EC.csproj` 裡。

- **但整條六層都未編譯**(§0.4),所以兩份都呼叫不到。

**為什麼這支特別重要:** `OFD681` 是 `OFDB600_Service` 與 `OFDB680_Service` 兩支服務**用來決定寄信名單的那張表**(`OFDB600Model.xsd` 與 `OFDB680Model.xsd` 都把它列為 DataTable)。維護入口沒進編譯,代表**現在要改通知名單只能直接下 SQL** —— 這是本片最值得追問維運的一條。這是**假設**,依據是全庫再無其他畫面宣告 `OFD681` 為主檔。

| 類別介面宣告有誤 | `public class OFDM681OracleDao : BaseEVADao , IOFDM680` —— 實作的是 **`IOFDM680`** 不是 `IOFDM681` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:15` |
|---|---|---|

上表那一行不是筆誤:`OFDM681OracleDao` 宣告實作 `IOFDM680`(`OFDM680` 的介面)。因為這支沒進編譯,編譯器不會抱怨。要復活這支畫面,這是第一個會爆的地方。

### 4.8 `OFDM670` — 理財活動設定(唯一有明細表的 M)

**用途(推測):** 設定一檔「理財活動」(活動代碼、起訖日、說明),下面掛任意組參數名 / 參數值。

- **主表** `OFD670A`(vdb `OFDM670A`),**明細** `OFD671A`(vdb `OFDM671A`),錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM670OracleDao.cs:30-31`。明細那行後面還留了一個 `//0` 的註記。

- 1,346 行,是 B 型裡最肥的一支,但只掛了 `BeforeSelect` 以外的事件在別處,SQL 幾乎全自組。

| 欄位 | Caption |
|---|---|
| `FINANCIAL_CODE` | 理財活動代碼 |
| `FINANCIAL_DESC` / `FINANCIAL_SHNM` | 理財活動說明 / 簡稱 |
| `FINANCIAL_BNG_DATE` / `FINANCIAL_END_DATE` | 理財活動起始 / 終止日期 |
| `PARAM_NAME` / `PARAM_VALUE` / `PARAM_DESC`(明細) | 參數名稱 / 參數值 / 參數描述 |

**卡控總表:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 同鍵已存在 | 存在 | **阻擋**「此筆資料已存在，請檢查後重新執行」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM670OracleDao.cs:393` |
| 修改 / 覆核前 | `IsDataChange`(六處) | 改過 | **阻擋**「此筆資料已異動，請檢查後重新執行」 | `:240` `:312` `:613` `:620` `:782` `:789` |

**沒有「活動起日不可大於迄日」的檢核**,1,346 行裡找不到 `BNG_DATE` 與 `END_DATE` 的比較。〔待確認 UI 端的 `validatorManager1` 有沒有設定,這部分在 `*.Designer.cs` 裡,本文不 Read〕

### 4.9 `IPJM614` — 網路開戶資料變更(唯一沒有 `MasterTable` 的 M)

**用途(推測):** 客戶在網路上申請變更基本資料(地址、電話、Email、法定代理人、國籍…),這支負責收單、送四眼、生效後回寫。

- **基底** `BaseEVADao`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:18`),1,124 行,**但完全沒有 `xTableMapping` 宣告** —— 全片唯一。所有 SQL 自己寫。

- **vdb 上的五張表:** `IPJM614` `IPJM614_Master` `OFD601CHG` `OFD607A` `OFD607ACHG`(`IPJM614_9iModel.xsd`)。

- **實際寫的三張表:**

| 表 | 動作 | 錨點 |
|---|---|---|
| `OFD607ACHG` | `UPDATE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:1032` |
| `OFD607A` | `UPDATE … SET PROCESS_YN = 'Y'` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:1086` |
| `OFD601CHG` | 由 vdb 帶入 | `IPJM614_9iModel.xsd` |

**這三張表的主檔擁有者是 BMS**(`bms.md §8`),`OFD607ACHG` 的主鍵是 `EC_BF_CHG_NO` 加 `DATA_SEQ` 加 `SYSTEM_ID`,由 `SerialNo.GetEC_BF_CHG_NO()` 取號 —— 那支取號程式在 `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs`,不在本片。

**卡控總表(全部在 UI):**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 輸入中 | 中文姓名必須是中文字 | 非中文 | **阻擋**「必須輸入中文字」 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:908` |
| 輸入中 | 中文姓名至少 2 字 | 少於 2 | **阻擋**「至少輸入2個中文字」 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:918` 與 `:972` |
| 輸入中 | 英文姓名必須是英文字 | 非英文 | **阻擋**「必須輸入英文字」 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:937` |
| 輸入中 | 不可輸入特殊字元 | 命中黑名單 | **阻擋**(訊息含全形與半形兩套符號清單) | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:962` |
| 存檔前 | 美國納稅義務人 | 是 | **阻擋**「於本公司政策規定，目前無法受理美國納稅義務人之開戶申請，請重新確認受益人資料。」〔客戶特定〕 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:988` 與 `:1003` |

> 最後一條是 FATCA 相關的政策卡控,**寫死在 UI 的 C# 裡而不是參數表**,換客戶要改程式。訊息出現兩次代表兩個入口各判一次,兩處要一起改。

### 4.10 其餘 13 支 M 的分群表

這 13 支都是 A 標準型:PO 只有建構子加一行 `MasterTable`,四眼全交 DLL,PO 端零卡控。合併成一張表。

| 代號 | 中文名(推測) | 主表 | PO 行數 | 畫面主要欄位(從 Designer 標籤反推) | 特別的地方 |
|---|---|---|---|---|---|
| `OFDM600` | 網路交易全站參數設定 | `OFD600A` | 46 | 系統識別碼、交易途徑、當日申購 / 買回金額限制(自然人 / 法人各一)、密碼累計錯誤次數上限、買回與轉申購額度計算 NAV 基準日、受益人異動截止時限、自動處理網路開戶後續流程時限、單筆申購限額(每次,含手續費)、定額異動生效日、停利點累積扣款金額限制、境外定額扣款準備日 T-N | **全站只有一列**;「自動處理網路開戶後續流程時限」就是 `OFDB609_Service` 的閘門 |
| `OFDM604` | 員工交易審核不核准原因維護 | `OFD676A` | 24 | 員工交易審核不核准原因代碼 / 說明、是否為投管部 | vdb 名叫 `OFD616` 與主表名不一致(§2.1) |
| `OFDM672` | IVR 基金音檔對照維護 | `ivr_map_wav` | 111 | 基金代碼、音檔代碼 | 表名小寫底線;掛最多事件(6 個) |
| `OFDM674` | 基金促銷設定 | `OFD674A` | 205 | 促銷日期起迄、基金代碼、促銷類型(特色推薦)、轉申購手續費率%、適用優惠最低金額、備註說明、顯示順序 | 兩處回 `AddResultRow(false, 0, string.Empty)` 空訊息(`:127` `:133`) |
| `OFDM680` | 到價提示發送時間設定 | `OFD680A` | 24 | 自動發送時間 | 餵 `OFDB680_Service` 的 `ALERT_LIMIT_TIMES` |
| `OFDM690` | 基金所屬類別設定 | `OFD690A` | 93 | 基金代碼、類別代碼 | 掛 `BeforeSelect`;把基金掛到 `OFDM694` / `OFDM695` 的兩本字典上 |
| `OFDM691` | 投資收益顯示顏色設定 | 無(PO 已死) | — | 投資收益顯示顏色上限 / 下限 %,說明文字寫「超過上限以紅色、超過下限以綠色、其餘灰色」 | **未編譯** |
| `OFDM692` | 網頁轉址設定 | 無(PO 已死) | — | 轉址位置、是否需要轉址 | **未編譯** |
| `OFDM693` | 核印不成功原因代碼維護 | 無(PO 已死) | — | 核印不成功原因代碼 | **未編譯**;對應 `IPJB614` 的核印流程 |
| `OFDM695` | 基金所屬類別代碼維護 | `OFD691A` | 35 | 基金所屬類別代碼、中文 / 英文名稱 | 與 `OFDM694` 是姊妹字典 |
| `OFDM696` | 網路瀏覽 LOG 代碼維護 | `LOG616A` | 35 | 網路瀏覽 LOG 代碼、紀錄說明、是否需要記錄 | 唯一主表在 `LOG*` 命名空間的 M |
| `OFDM697` | 產品代碼維護 | `OFD685A` | 27 | 產品代碼、產品名稱說明,xsd 另有促銷活動代碼 / 幣別 / 優惠折數 / 申購起訖金額 / 申購手續費率 | xsd 欄位比畫面多,推測有隱藏頁 |
| `OFDM698` | 產品組合設定 | `OFD686A` | 1,109 | 產品代碼、資料明細(掛基金) | 行數是 A 型的 40 倍,但沒掛事件 —— SQL 全寫在私有方法裡;五處 `IsDataChange` 阻擋 |

**`OFDM698` 例外說明:** 它形式上是 A 型(有 `MasterTable`、不掛事件),但 1,109 行裡自己組了整套主明細 SQL,明細那半邊沒有宣告成 `DetailTable`。五處「此筆資料已異動，請檢查後重新執行」在 `:397` `:467` `:597` `:726`,新增重覆檢核在 `:248`。

---

## 5. 查詢畫面(I)

**本片無 I 畫面。**

原因很明確:**EC 的查詢畫面全部放在另一個專案** `Dev/ATLAS.EC.Query/`,不在 `Dev/ATLAS.EC/` 底下。這跟 `architecture.md §2` 記的「`.Report` 那組是命名鐵律的正式例外」是同一件事的另一個例子 —— EC 這條產品線把 M / B 放主專案、I 放 `.Query`、R 放 `.Report`,共三個 csproj。

**一個容易誤判的地方:** 本片有幾支 B 畫面「只查不寫」,長得很像 I:

| 畫面 | 為什麼看起來像 I | 為什麼它是 B |
|---|---|---|
| `OFDB673` | 主要動作是看清單然後按「是否同意變更?」 | 有 `Execute` 走 `S_TA_OFDB673_EXE` 實際寫回 |
| `OFDB690` | 只有一個「取消員工交易日期」輸入框 | 有 `s_OFDB690_Get` 加寫入 |
| `OFDB671` | 只有「審核人員設定」一區 | 寫 `OFD678A` |

`architecture.md §6` 已經說明 I 與 B 「是同一份樣板複製後刪減出來的」,所以形似是預期內的,判別標準是**有沒有 `ExecuteNonQuery` 那條路徑**。

---

## 6. 批次(B)與 WindowsService

```text
[圖] EC 的 28 支批次分成五群,以及三支 WindowsService 的觸發關係與 Remoting 差異
圖中文字:三支 WindowsService:同樣的 60 秒 Timer,但只有兩支真的走 Remoting / OFDB600 Service / EXEC_TIMES 加 buffer / OFDB609 Service / OPEN_ACC_PROCESS_TIME / OFDB680 Service / ALERT_LIMIT_TIMES / 排程時間全存資料庫 / 不是設定檔 / wellknown OFDB600_Pxy / Remoting 打 AP / wellknown OFDB609_Pxy / Remoting 打 AP / App.config 無 remoting / 本機直打資料庫 / ① 拋轉家族 10 支:IPJB6xx 與 OFDB60x 共用同一支 SP / OFDB600 / S_EC_IPJB600_EXCUTE / IPJB621 OFDB601 / S_EC_IPJB601_EXCUTE / IPJB622 OFDB602 / S_EC_IPJB602A_EXCUTE / IPJB624 OFDB604 / S_EC_IPJB604_EXCUTE / IPJB625 OFDB605 / S_EC_IPJB605_EXCUTE / IPJB606 / S_EC_IPJB606_EXCUTE / 未跑 OFDB600 就阻擋 / 九處同一句訊息 / ② 開戶密碼 7 支   ③ 員工審核 5 支 / OFDB609 / 密碼 LDAP 開戶進度 / OFDB606 610 611 690 / 四支整組未編譯 / OFDB615 616 607 608 / 補發 權限停復 / OFDB671 691 / 審核人員 逐筆審 / OFDB672 OFDB673 / 員編變更 兩段式 / ④ 到價 2 支   ⑤ 扣款核印 4 支   唯一走四眼的 B / OFDB680 / 暫存表三張 加發信 / OFDB693 / 唯一四眼 B OFD688A / IPJB613 IPJB614 / 送件 核印 / OFDB611 OFDB612 / 扣款 發送 回覆 / 共同骨架:寫死 i 等於 1、catch SqlException 死碼、例外訊息空字串 / 七支寫死處理筆數 / ExecuteNonQuery 丟掉 / catch SqlException 六處 / Oracle 永不進入 / AddResultRow 空訊息 / 三十八處 / OFDB605 IPJB625 / 四道檢核全被註解
```

*圖:圖 4 批次分群與 Service 觸發。橘虛框=Service 或含寫死值〔客戶特定〕;橘框=關鍵批次或本片共通缺陷;黑虛框=整組未編譯;黑框=無原始碼、從呼叫端反推。虛線箭頭=服務觸發它同名的批次。最上排右邊那格是本文的核心更正:OFDB680 的 App.config 沒有 remoting 區段,它不是 Remoting 客戶端,是本機直打資料庫。*

28 支 B 加 3 支 WindowsService,是本片的主體。先看共同骨架,再看三支服務,最後分群看批次。

### 6.1 共同骨架:每一支 B 都長一樣

`architecture.md §6` 說 I 與 B 是同一份樣板複製刪減出來的。本片 28 支把這句話演到極致 —— **連例外處理的寫法都一字不差**:

```
try
{
    tran = db.BeginTransaction();
    cmd  = db.GetStoredProcCommand("<SP 名>");
    cmd.CommandTimeout = 0;            // 此程式讓它永久跑
    ... AddInParameter 逐個 ...
    db.ExecuteNonQuery(cmd, tran);
    i = 1;                             // <= 回傳值丟掉,寫死 1
    tran.Commit();
    resultVDB.Utility.Result.AddResultRow(true, i, string.Empty);
}
catch (SqlException sqlex)             // <= Oracle 上永遠不會進來
{
    tran.Rollback();
    resultVDB.Utility.Result.AddResultRow(false, 0, sqlex.Message);
}
catch (Exception ex)
{
    tran.Rollback();
    resultVDB.Utility.Result.AddResultRow(false, 0, string.Empty);  // <= 空訊息
    CommonExceptionBlocker.HandleBusinessException(ex);
}
finally
{
    if (tran != null) { db.Dispose(tran); } else { db.Dispose(); };  // 20230428 DB 釋放
}
```

樣本 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:225-284`。四個共同特徵各自的影響寫在附錄 E。

**`cmd.CommandTimeout = 0` 在 20 支以上出現,註解一律寫「此程式讓它永久跑」。** 意思是拋轉 SP 卡住時前端不會 timeout,使用者只會看到畫面沒反應。

**交易邊界:** 每支自己 `BeginTransaction`,`Commit` 71 處、`Rollback` 294 處、`BeginTransaction` 70 處(全 EC 的 `.cs` 統計,已剝註解)。`Rollback` 比 `Commit` 多四倍是因為每個 `catch` 分支都寫一次。**沒有跨支批次的交易** —— 一支 B 一個交易,失敗只回滾自己那一支。

### 6.2 `OFDB600` 與 `OFDB600_Service` — 網路交易時限截止處理

**畫面中文名(有明確出處):** 「網路交易時限截止處理作業(手動)」—— `Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/OFDB600_Pxy.cs:13`。括號裡的「手動」是關鍵:**這支畫面是服務的手動備援,正常情況由服務跑。**

**這支做什麼:** 每天到了設定時間,把當天「還沒送到交易時限」的網路單一次截止掉,之後拋轉批次才能跑。畫面上列出六種交易別各自用哪個日期算(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB600.Designer.cs`,以 `grep -n 'Text = "'` 取得):

| 交易別 | 截止基準 |
|---|---|
| 單筆申購 | 以申購日期計算 |
| 買回 | 以買回日期計算 |
| 轉申購 | 以買回日期計算 |
| 定額申購 | 以定額收件日計算 |
| 定額異動 | 以定額異動生效日計算 |
| 受益人資料變更 | 以受益人變更生效日期計算 |

| 項目 | 內容 |
|---|---|
| **觸發方式** | 服務(`OFDB600_Service`)為主,畫面手動為輔 |
| **參數** | `CHECK_DATE`(資料處理日期)、`CreateID` |
| **SP** | `S_EC_IPJB600_EXCUTE`(**注意 SP 名是 `IPJB600` 不是 `OFDB600`**),錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:48` |
| **寫哪些表** | C# 端不直接寫,全在 SP 內。C# 只額外寄信 |
| **失敗處理** | `catch` 內 `tran.Rollback()`,回 `AddResultRow(false, 0, string.Empty)` —— **訊息是空的** |
| **會不會 rollback** | 會,單一交易涵蓋整支 SP |
| **可不可以重跑** | 程式沒有擋重跑;**能不能重跑取決於 SP 的冪等性,repo 判斷不出來** |
| **順序相依** | **它是五支拋轉批次的前置**,沒跑過就跑拋轉會被阻擋(§1.4) |
| **往外部打** | 會 —— `SendMail`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:112` 起的「寄審核取消通知信」) |

**`SendMail` 的收件名單來自 `OFD681`**(`OFDB600_9iModel.xsd` 有 `OFD681` 與 `OFD681_EMP` 兩張 DataTable),而 `OFD681` 的維護畫面 `OFDM681` **沒進編譯**(§4.7)。

#### `OFDB600_Service` 的內部

| 項目 | 內容 | 錨點 |
|---|---|---|
| Timer | 60 秒一跳,比對 `DateTime.Now.ToString("HHmm")` 等不等於 `sTIMES` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:27-30` 與 `:65-75` |
| 排程時間來源 | `pxy.GetExecTime()` 取 `OFDB600_TIMES` 的 `EXEC_TIMES` 與 `LIMIT_TIME_BUFFER`,**存在資料庫不是設定檔** | `:114-153` |
| Remoting | `OnStart` 讀自己的 exe.config,`App.config:189` 有 `<wellknown … OFDB600_Pxy … url="http://<內網伺服器IP>/ATLAS_TAService/OFDB600_Pxy.rem"/>`〔客戶特定〕 | `:50-52` |
| 執行 | `pxy.Execute(query)`,參數 `CHECK_DATE` 帶 `ExeCDt.AddMinutes(-iLIMIT_TIME_BUFFER)`、`CreateID` 帶 `"AutoJob"` | `:84-88` |
| 執行後 | `AftExec()` 取執行後筆數寫檔 | `:73` 與 `:189-213` |
| Log | 落地 `C://Vendor//WindowService//OFDB600//OFDB600_yyyyMMdd.txt`,`Encoding.Default` | `:220` 與 `:247` |

**這支服務有五個實作問題**(逐條進附錄 E):

1. **`BefExec()` 定義了但沒有人呼叫。** `_timer_Elapsed` 只呼 `DoExecute()` 與 `AftExec()`(`:72-73`),`BefExec()`(`:164-187`)整支是死碼 —— 所以 log 檔裡永遠只有「批次執行後」,沒有「批次執行前」,**無法比對批次到底處理了幾筆**。

2. **`sEXEC_TIMES.PadLeft(4, '0')` 的回傳值被丟掉。** `:130` 寫 `if (sEXEC_TIMES.Length < 4) sEXEC_TIMES.PadLeft(4, '0');` —— `PadLeft` 不會改原字串。所以資料庫存 `930` 這種三碼時間時,下一行的 `Substring(0,2)` 會取到 `93`、`Substring(2,2)` 取到 `0` 加越界,**直接丟例外被 `:149` 的空 `catch` 吃掉,這一列靜默跳過**。

3. **`iLIMIT_TIME_BUFFER` 在只有一列設定時永遠是 0。** 第一列走 `:135-138` 的分支只設 `dtExec`,不設 `iLIMIT_TIME_BUFFER`;只有第二列以後走 `:139-147` 的 `else` 才會設(`:144`)。**設定表只有一列時,時間緩衝完全失效。**

4. **`catch { }` 空的**(`:149-151`),每一列的轉換錯誤都靜默。

5. **log 是「整檔讀出再整檔覆寫」**(`:239-252`),檔案越大越慢,而且兩個執行緒同時寫會互相蓋掉。

### 6.3 `OFDB609` 與 `OFDB609_Service` — 網路開戶後續自動處理

**這支做什麼:** 網路開戶送出後,系統要自動往下走 —— 產生登入密碼與交易密碼、加密存檔、同步到 LDAP、推進開戶進度、寄通知信。畫面上的欄位是「受益人ID / 受益人戶號 / 變更ID / 變更客戶聯絡資料(手機) / 變更客戶聯絡資料(EMALI) / LDAP資料種類 / 變更前受益人ID / 變更後受益人ID」(原文 `EMALI` 就是拼錯的)。

| 項目 | 內容 |
|---|---|
| **觸發方式** | 服務(`OFDB609_Service`)為主,畫面手動為輔(畫面上有「更新LDAP資料」按鈕) |
| **參數** | `USERID`(服務端固定 `"AutoJob"`)、`BF_SRNO`(單筆補跑用,預設 `-1`) |
| **SP** | `S_EC_OFDB609_Excute`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:86`) |
| **寫哪些表** | `OFD607A`、`OFD607`、`LOG602`(密碼異動記錄)、`Z_OPACT`;C# 端 11 處 `ExecuteNonQuery` |
| **失敗處理** | SQL 失敗 rollback;**LDAP 失敗不 rollback**(見下) |
| **可不可以重跑** | 可以,帶 `BF_SRNO` 單筆重跑;畫面上的「更新LDAP資料」就是重跑 LDAP 那一段 |
| **順序相依** | 無,獨立一條線 |
| **往外部打** | **會,而且是本片唯一還活著的兩條外部路徑**:LDAP API 與 EC Web Service |

#### 非營業日的處理有陷阱

```
DateTime Execdate = biz.GetBusinessDay(COMP_CALENDER_TYPE.Company, Sysdate, 0);
if (DateTimeHelper.DateToString(Sysdate) != DateTimeHelper.DateToString(Execdate) & decBF_SRNO == -1m)
{
    adminviewVDB.Util.Result.Clear();
    adminviewVDB.Util.Result.AddResultRow(true, 0, "");
    return adminviewVDB;
}
```

錨點 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:61-67`。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進 PO 前 | 今天是不是公司營業日(且不是單筆補跑) | 非營業日 | **過濾(無提示)** —— 回 `true, 0, ""`,服務端會判成「成功執行 0 筆」 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:61-67` |

**這條要特別小心:** 服務端 `OFDB609_Service.cs:86-89` 對 `ReturnCode == true` 的處理是寫一筆 Information 的 EventLog「Success:」加**空訊息**。所以「今天是假日所以沒跑」與「跑了但一筆都沒有」在 EventLog 上**完全看不出差別**。要判斷服務有沒有真的做事,只能去看 `C://Vendor//WindowService//OFDB609//` 的 log 檔。

另外 `&` 是**非短路的 bitwise AND**,不是 `&&`。兩邊都是 `bool` 所以結果一樣,但 `GetBusinessDay` 已經先算過了,沒有效能差異 —— 純粹是寫法不一致。

#### LDAP 同步:失敗不回滾,只發信

`UpdateLDAPCustomer`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:79-145`)在 PO 的資料庫交易**已經 commit 之後**才跑,逐列比對三種變更:

| 變更 | 條件 | 呼叫 | 失敗時 |
|---|---|---|---|
| ID 變更 | `row.NEW_ID_NO != row.ORG_ID_NO` | `APICTL.updateCustomerIDNumber(舊, 新, "OFDB609", uid)` | 寫 `INSERT_CALLAPI_FailLog`,累積訊息 |
| Email 變更 | `row.NEW_EMAIL1 != row.ORG_EMAIL1` | `APICTL.updateCustomerInfo(id, "OFDB609", uid, "email", 新值)` | 同上 |
| 手機變更 | `row.NEW_CELL_PHONE != row.ORG_CELL_PHONE` | `…, "mobile", 新值` | 同上 |

全部跑完後,若 `strERR` 非空就寄一封「OFDB609 受益人異動批次轉入作業 - LDAP更新失敗通知」,並把結果改成 `AddResultRow(false, 0, "執行LDAP更新失敗，請檢查")`(`:140-143`)。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| DB commit 之後 | LDAP 三種更新任一失敗 | 失敗 | **記錄不擋** —— 資料庫已經改了,LDAP 沒改,只寄信通知 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:134-143` |

**這是本片最會咬人的設計:資料庫與 LDAP 之間沒有任何補償機制,靠人看信去按「更新LDAP資料」按鈕。** 訊息本身也這樣寫:「更新失敗資料請於OFDB609-網路交易後續處理作業執行『更新LDAP資料』按鈕，若仍執行失敗請洽IT進行查詢。」

三個比較式 `NEW_ID_NO != ORG_ID_NO` 都是 C# 的字串比較,不是 SQL,**所以沒有 Oracle 三值邏輯問題**;但若 `ORG_*` 是 `DBNull` 而 typed DataSet 欄位是 `AllowDBNull`,讀 `row.ORG_ID_NO` 會丟 `StrongTypingException` —— 被 `:127` 的 `catch (Exception ex)` 接住,**這一列的 LDAP 同步就靜默跳過**(`CommonExceptionBlocker.HandleBusinessException` 不 rethrow)。

#### 密碼產生:兩個空 `catch` 包住整條外部呼叫

```
private string GenPassword()
{
    string sPwd = string.Empty;
    ECAdapter ctl = new ECAdapter();
    int iLen = ran.Next(7, 11);          // 改為7-10碼  2010/3/8 william
    try { sPwd = ctl.MakeECPassword(iLen); }
    catch { }
    return sPwd;
}
```

錨點 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:412-427`,`EncodePass` 同款在 `:429-441`。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 產生密碼 | EC Web Service 不通 | 不通 | **記錄不擋(而且連記錄都沒有)** —— `sPwd` 留在 `string.Empty`,**空密碼會一路寫進 `OFD607A`** | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:424-425` |
| 加密密碼 | 同上 | 同上 | 同上,加密後字串為空 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:437-438` |

`Random ran = new Random()` 在方法內 `new`(`:419`),連續呼叫時種子相同 —— 但這裡只影響密碼長度不影響密碼內容(內容由外部服務產生),影響有限。

#### `OFDB609_Service` 的內部

| 項目 | 內容 | 錨點 |
|---|---|---|
| Timer | 60 秒,比對 `HHmm` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:24-27` 與 `:67` |
| 排程時間來源 | `OFDB609_TIMES[0].OPEN_ACC_PROCESS_TIME` —— 對應 `OFDM600` 畫面上的「自動處理網路開戶後續流程時限」 | `:116` |
| Remoting | `App.config:189` 有 `<wellknown … OFDB609_Pxy … OFDB609_Pxy.rem/>` | `:40-42` 與 `:54-56` |
| 重複初始化 | `Start()`(`:35-45`)與 `OnStart()`(`:49-57`)各寫一次同樣三行 —— `architecture.md §8` 已記過 |  |
| Log | `C://Vendor//WindowService//OFDB609//` | `:154` |

**`GetTIMES` 讀 `[0]` 沒有先檢查列數**(`:116`):設定表空的時候會丟 `IndexOutOfRangeException`,被 `:120` 的 `catch` 接住寫 EventLog,`sTIMES` 維持上一次的值或空字串 —— **空字串時 `_timer_Elapsed` 的 `sTIMES != string.Empty` 為假,服務就再也不會執行,而且不會再有任何 EventLog**(因為 `GetTIMES` 只在執行完才被呼叫一次)。這是一條「服務靜悄悄停掉」的路徑。

**2021 年修過一個沒寫 log 的 bug:** `:75` 的註解寫「2021.10.05 抓到bug:修改沒寫log的問題，Matt建議改寫如下 by hanna」,把 `var view = Pxy.Execute(query);` 提前並補上 `AftExec((OFDB609ViewVDB)view);`。舊寫法留在 `:78-80` 的註解裡。

### 6.4 `OFDB680` 與 `OFDB680_Service` — 到價提示計算與發送(不是 Remoting 客戶端)

**這支做什麼:** 客戶在網站上對某檔基金設「淨值到 X 元通知我」或「報酬率到 Y% 通知我」,這支每天定時算一次,命中就發信並累計發送次數。

| 項目 | 內容 |
|---|---|
| **觸發方式** | 服務(`OFDB680_Service`)為主,畫面手動為輔 |
| **參數** | `FUND_ID`(逗號串起的基金清單)、`ALERT_DATE`、`EXE_TYPE`(寫死 `"1"`)、`BF_SRNO`(寫死 `"-1"`)、`USER`(寫死 `"AutoJob"`)、`RunType`(寫死 `"01"`)、`DATACHECK` |
| **SP** | `S_EC_OFDB680_GET`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:…` 的 `GetStoredProcCommand`) |
| **寫哪些表** | `OFD682A` `OFD683A` `OFD684A` `OFD696A`,加三張同名暫存表 `OFDB680` / `OFDB680_3` / `OFDB680_XML`;C# 端 14 處 `ExecuteNonQuery` |
| **失敗處理** | rollback,回「執行失敗，請檢查」加 SP 訊息;**兩處 `catch (SqlException)` 是死碼**(`:285` `:560`) |
| **可不可以重跑** | 服務端帶 `DATACHECK` 參數做重複防護(見下),畫面手動則無 |
| **順序相依** | 無 |
| **往外部打** | 發信(走 `OFD696A` 與 XML 組信,不是 `ECAdapter`) |

#### ⚠ `OFDB680_Service` 不是 Remoting 客戶端

派工單問「`OFDB680` 是哪一種」。答案是:**程式碼寫成 Remoting 客戶端,設定檔沒有配套,所以實際是本地執行。**

| 比對項 | `OFDB600` | `OFDB609` | **`OFDB680`** |
|---|---|---|---|
| `using System.Runtime.Remoting` | 有 | 有 | 有 |
| `RemotingConfiguration.Configure(...)` | `OFDB600_Service.cs:50` | `OFDB609_Service.cs:40` 與 `:54` | `OFDB680_Service.cs:42` 與 `:138` |
| `new <代號>_Pxy()` | 有 | 有 | 有(`:65` `:111` `:150`) |
| csproj 參考 `FormProxy.EC` | 有 | 有 | 有 |
| **`App.config` 有 `<system.runtime.remoting>`** | **有**(`:175-194`) | **有**(`:175-194`) | **完全沒有** |
| **`<wellknown>` 註冊** | **有**(`:189`,`OFDB600_Pxy.rem`) | **有**(`:189`,`OFDB609_Pxy.rem`) | **沒有** |
| `App.config` 總行數 | 349 | 349 | **385** |
| `Program.cs` 的 `Environment.UserName == "SYSTEM"` | 有 | 有 | 有 |

驗證方式:`grep -n 'system.runtime.remoting\|wellknown' <各服務>/App.config`。`OFDB680` 那份零命中,而且它的設定檔比另外兩份**多 36 行**(多的是 appSettings,不是 remoting)。

**推論:** `RemotingConfiguration.Configure` 讀到一份沒有 `<client>` 區段的設定檔,不會丟例外,只是什麼都沒註冊。之後 `new OFDB680_Pxy()` 產生的是**本地 `Basic_Pxy` 子類實例**,`pxy.Execute(view)` 直接在服務行程內 `new OFDB680_Ctl()` 並打資料庫(`Dev/ATLAS.EC/Source/FormProxy/FormProxy.EC/OFDB680_Pxy.cs:31-46`)。

**所以三支服務其實是兩種,不是一種:**

|  | `OFDB600` / `OFDB609` | `OFDB680` | `RSPB008`(`rsp.md §6`) |
|---|---|---|---|
| 走 Remoting | **是** | **否(設定缺)** | 否(設計如此) |
| 打 DB 的行程 | AP Server | **服務機本身** | 服務機本身 |
| 部署時需要 | Remoting 端點可達 | **資料庫直連權限** | 資料庫直連權限 |
| 是有意的嗎 | 是 | **看不出來** | 是(csproj 直接參考 `Control.RSP`) |

`RSPB008` 是「csproj 根本不參考 `FormProxy`、程式直接 `new Ctl`」的乾淨設計;`OFDB680` 是「程式照 Remoting 寫、設定檔漏配」。**`architecture.md §8` 記的「三支 `OFDB*` 是 Remoting 客戶端」對 `OFDB680` 需要修正。** 這是**假設**,依據是設定檔缺整個區段;要確認得看部署機上的 `Vendor.Product.TA.WindowsService.OFDB680.exe.config`(部署時 `App.config` 會被改名複製過去),repo 判斷不出來。

#### 服務的執行流程

```
每 60 秒 -> HHmm == ALERT_LIMIT_TIMES ?
   -> pxy.SelectFund()                     取今天要算的基金清單
   -> sFund = string.Join(",", FUND_ID)    逗號串起來
   -> 塞 7 個參數 -> pxy.Execute(view)
   -> AftExec()                            取執行後筆數寫 log
   -> GetTIMES()                           重新取下一次時間
```

錨點 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:57-104`。

**四個要注意的地方:**

1. **`sFund` 是把全部基金串成一個字串用 `SQLOperator.Equal` 送出去**(`:70-74`)。`FUND_ID = 'A001,A002,A003'` 這種條件只有在 SP 內部把它拆開才有意義。**SP 怎麼拆,repo 看不到。**

2. **`SelectFund` 回零列時 `sFund` 是空字串**(`:72` 的 `if (sFund.Length > 0)` 只負責去掉開頭逗號),接著仍然照常送出 `FUND_ID = ''` 與 `DATACHECK = '' + 日期 + '-1'` 去執行 —— **空跑一輪,沒有任何提示**。

3. **`DATACHECK` 是「基金清單 加 日期 加 -1」串起來的指紋**(`:83`),推測是 SP 用來擋重複執行的 key。**基金清單順序變了指紋就變**,所以「同一天基金清單順序不同」會被當成不同批次 —— 這是**假設**,依據是參數名與組成方式。

4. **`BF_SRNO` 寫死 `"-1"`**,原本應該從畫面控件取(`:77-80` 的註解還留著 `this.custEC_BF_SRNO.Value`)—— 服務模式下沒有畫面,所以寫死。

#### `OFDB680` 的到價判斷邏輯(這段在 Ctl 不在 SP)

`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:130-175` 逐列跑 `switch (row.ALERT_SET)`:

| `ALERT_SET` | `ALERT_TYPE` | 拿什麼比 | 錨點 |
|---|---|---|---|
| `1` | `1` | `NAV_B`(淨值)比 `ALERT_H` / `ALERT_L` | `:138` |
| `1` | `2` | `PERT`(報酬率)比上下限 | `:143` |
| `1` | `3` | `PAL`(損益)比上下限 | `:147` |
| `2` | (不分) | 一律用 `NAV_B` | `:155` |
| `3` | — | **整段被註解,`#region 用不到`** | `:160-175` |

命中時 `ALERT_TIMES_H` 或 `ALERT_TIMES_L` 加一(`:149-150` 與 `:157-158`),對應 `OFDM680` 的「到價提示發送次數設定」上限。

**`switch` 沒有 `default` 分支**:`ALERT_SET` 出現 `1` / `2` 以外的值(包括 `3`,因為那段被註解了)時,`strALERT_RES` 留在 `string.Empty`,兩個次數都不加,**這一列靜默不處理**。

`:153` 與 `:159` 各有一個 `break`,那是 `switch` 的 `break` 不是迴圈的 —— 本片 76 處 `break` 裡大多屬這一類,**真正「遇壞列跳出迴圈」的樣式在本片沒有找到**(附錄 E 有記)。

### 6.5 五組拋轉批次 —— `IPJB6xx` 與 `OFDB60x` 的雙胞胎關係

這是本片最大的一群,也是最容易改錯的一群。

| 交易別 | 含語音版 | 純網路版 | **共用的 SP** | 交易檔 | 額外寫 |
|---|---|---|---|---|---|
| 單筆申購 | `IPJB621` | `OFDB601` | `S_EC_IPJB601_EXCUTE` | `OFD611A` | `OFD618A`(僅 IPJ 版) |
| 買回 | `IPJB622` | `OFDB602` | `S_EC_IPJB602A_EXCUTE` | `OFD612A` | `OFD618A`(僅 IPJ 版) |
| 定額異動 | `IPJB624` | `OFDB604` | `S_EC_IPJB604_EXCUTE` | `OFD614A` | `OFD618A`(僅 IPJ 版) |
| 受益人資料變更 | `IPJB625` | `OFDB605` | `S_EC_IPJB605_EXCUTE` | `OFD615` | `OFD618A`(僅 IPJ 版) |
| 轉申購 | `IPJB606` | (無對應) | `S_EC_IPJB606_EXCUTE` | `OFD616A` | — |
| 時限截止 | (無對應) | `OFDB600` | `S_EC_IPJB600_EXCUTE` | — | — |

**證據:** SP 名一模一樣,錨點成對 ——

| SP | 含語音版錨點 | 純網路版錨點 |
|---|---|---|
| `S_EC_IPJB601_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs:238` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:230` |
| `S_EC_IPJB602A_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:267` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:261` |
| `S_EC_IPJB604_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB624OracleDao.cs:223` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs:217` |
| `S_EC_IPJB605_EXCUTE` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:138` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:134` |

**兩邊的差別(逐項比對):**

| 差別 | `IPJB6xx` | `OFDB60x` |
|---|---|---|
| 畫面「交易途徑」選項 | 全部 / 網路 / 語音 三個 | 只有「網路」 |
| xsd | 只有 `_9i` 版 | `Model.xsd` 與 `_9iModel.xsd` 雙份(程式用 `_9i`) |
| 額外 `INSERT INTO OFD618A` | **有**(`IPJB621:296`、`IPJB622:285` 與 `:306`、`IPJB624:250` 與 `:274`、`IPJB625:185`) | **沒有** |
| 拋轉回復的前置檢核 | 有 | 有 |
| 副畫面 | `IPJB621_P0.cs` 等(`_P0` 大寫) | `OFDB601p0.cs` 等(`p0` 小寫) |

**`OFD618A` 只有 IPJ 版會寫,這是兩邊唯一的實質差異。** 從欄位名推測它是拋轉的批次記錄或差異檔 —— 但沒有讀到寫入的欄位清單全貌,**不做進一步推測**。

#### 共同的卡控總表(五組通用)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點(以 `OFDB601` 為例) |
|---|---|---|---|---|
| 按執行前 | 今天有沒有跑過 `OFDB600` | 沒跑過 | **阻擋**「尚未執行交易截止時間，請先執行OFDB600程式」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:112` |
| 拋轉回復前 | `ValidatePCode` 檢查有沒有更晚日期的拋轉資料 | 有 | **阻擋**「尚有大於此申購日期的拋轉資料，請先回覆後再執行拋轉回復。」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:215-223` |
| 買回專屬 | 員工交易件是否已比對 | 未比對 | **阻擋**「員工交易件尚未作比對，不可產生執行{0}。」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:255` 與 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:261` |
| 轉申購專屬 | 同上 | 未比對 | **阻擋** | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:97` 的前置 |
| 執行 | SP 失敗 | 例外 | **阻擋**,訊息為空(買回那兩支例外,會回「執行失敗，請檢查:」加明細) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:298` |

「員工交易件尚未作比對」把 ① 拋轉線與 ③ 員工審核線綁在一起:**`OFDB691` 沒審完,買回與轉申購就拋不了。**

#### ⚠ `OFDB605` 與 `IPJB625` 的四道檢核全是死碼

這兩支的 PO 各實作了四個檢核方法,Pxy 與 Ctl 也都有對應的轉呼叫,介面也宣告了 —— **但 UI 的呼叫點全部被註解掉**:

| 檢核 | PO 實作 | Ctl | Pxy | 介面 | UI 呼叫點 |
|---|---|---|---|---|---|
| `CheckBMS_CTL_CODE_1`「尚有未拋轉資料，不可執行」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:272` | `:78` | `:85` | `IOFDB605PO.cs:12` | **註解** `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB605.cs:370` |
| `CheckBMS_CTL_CODE_2`「尚有已拋轉資料，不可拋轉回復」 | `:347` | `:93` | `:107` | `:13` | **註解** `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB605.cs:385` |
| `CheckBMSCHG_DATE`「已有批次生效資料，不可再執行拋轉回復作業」 | `:422` | `:110` | `:128` | `:14` | **註解** `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB605.cs:423` |
| `CheckSYSTEM_ID`「OFD600中有語音交易資料」 | `:506` | `:125` | `:149` | `:15` | **註解** `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB605.cs:214` |

`IPJB625` 完全相同的四處:`Dev/ATLAS.EC/Source/UI/UI.EC/IPJB625.cs:212` `:368` `:383` `:421`。`IPJB606` 也註解掉一處 `CheckSYSTEM_ID`(`Dev/ATLAS.EC/Source/UI/UI.EC/IPJB606.cs:201`)。

**所以受益人資料變更拋轉這支,現在只剩「有沒有跑過 OFDB600」一道防線。** 這是本片最嚴重的「被註解掉但外殼還在」案例:四層程式碼都還在、都還編譯、介面還宣告,唯獨最上面那一行呼叫沒了。任何靠 `grep CheckBMS_CTL_CODE_1` 判斷「這個檢核有沒有在跑」的人都會判錯。

**而且這四個檢核方法本身還有一個反向缺陷:結果碼的語意跟主流程相反。**

```
if (j > 0)   { AddResultRow(true,  1, "尚有未拋轉資料，不可執行"); }   // 有問題 -> true
else         { AddResultRow(false, 0, ""); }                          // 沒問題 -> false
...
catch (Exception ex) { AddResultRow(false, 0, ""); }                  // 例外   -> false = 沒問題
```

錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:313-330`。`Execute` 那條路徑是 `true` = 成功,這四個方法是 `true` = 有問題。**而且 `catch` 回的是「沒問題」** —— 檢核時資料庫出錯會變成放行。就算把 UI 的註解拿掉,這四道檢核也是不可靠的。

### 6.6 `OFDB612` / `OFDB611` — 扣款結果與扣款發送

|  | `OFDB611`(**未編譯**) | `OFDB612` |
|---|---|---|
| 用途(推測) | 扣款資料發送 | 扣款結果回覆與統計 |
| 觸發 | 人工 | 人工 |
| 參數 | 付款方式(全部 / 匯款 / 扣款)、申購日期 | 扣款方式(一般 / 財金)、扣款行、申購日期、代理扣款機構、排序方式 |
| 寫哪些表 | `OFD621A` | `OFD621A` |
| SP | 無,自己寫 SQL | 無,自己寫 SQL |
| `ExecuteNonQuery` | `:170` 有累加 `j +=` | `:190` 有累加 `i +=` |
| 失敗 | rollback,回空訊息(`:74`) | rollback |
| 重跑 | 有詢問:「該申購日已有發送紀錄，是否繼續執行」(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB611.cs:49`) | 無防護 |
| 外部 | 無 | 無 |

`OFDB612` 畫面上有三組統計:合計 / 失敗 / 成功 的筆數、金額、手續費金額,加兩個批次按鈕「全部扣款中」「全部扣款成功」。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前(`OFDB611`) | 該申購日已有發送紀錄 | 有 | **詢問** | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB611.cs:49` |
| 查詢後(`OFDB611`) | 沒有可發送的資料 | 零筆 | **阻擋**「無可發送之資料」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB611OracleDao.cs:70` |
| 小數位(`OFDB612`) | 依 `PTPF-AA_Ccustomer.Book_Currency` 決定顯示位數 | — | — | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB612_Ctl.cs:56` |

`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB612.cs:122` 有一處 SQL 字串用 `<> '值'` —— Oracle 三值邏輯風險(附錄 E4)。

### 6.7 開戶與密碼那一群:`OFDB606` `OFDB607` `OFDB608` `OFDB610` `OFDB615` `OFDB616`

六支共同的操作對象是 `OFD607A`(網路戶註冊檔),都走裸 `UPDATE`。

| 畫面 | 編譯 | 用途(推測) | 動作按鈕 | 寫哪些表 | SP | 外部 |
|---|---|---|---|---|---|---|
| `OFDB606` | **未編** | 重發登入 / 交易密碼 | 重發登入密碼、重發交易密碼、MAIL、列印實體密碼函 | `OFD607A` `LOG602` | 無 | `ECAdapter.MakeECPassword` 加 `EncodeString`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB606_Ctl.cs:59`,**空 `catch`** `:74`) |
| `OFDB607` | 齊 | 網路查詢 / 交易權限停復 | 停止、恢復,加備註 | (SP 內) | `S_EC_OFDB607_Excute` | 無 |
| `OFDB608` | 齊 | 受益人網路資料處理 | 只有受益人戶號 / ID 兩個欄位 | (SP 內) | `S_EC_OFDB608_Excute` | 無 |
| `OFDB610` | **未編** | 實體密碼函列印與標籤 | 自黏標籤 / 開窗信封、選擇標籤從第幾格開始印 | `OFD607A`(`DOC_SEND_DT` `DOC_PRINT_UID`) | `s_OFDB610_Get` `s_ECFunGetAccountData` | 無 |
| `OFDB615` | 齊 | 重發網路密碼(含 LDAP) | 重發網路密碼、寄發類型 | `OFD607A` `OFD607` `LOG602` | 無 | `LDAPAPIHelper`(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB615_Ctl.cs:52` 與 `:104`) |
| `OFDB616` | 齊 | 補發密碼函與寄送名單匯出 | 補發網路密碼 / 補發語音密碼 / 新開戶語音密碼、匯出 Excel | `OFD607A` `OFD607` `LOG602` | 無 | 無 |

**卡控:**

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `OFDB607` | 點權限 | 已是該狀態 | 是 | **阻擋**「不可點選查詢權限」/「不可點選交易權限」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB607.cs:212` 與 `:220` |
| `OFDB607` | 執行後 | — | — | **記錄不擋** —— 四種結果訊息(已恢復 / 已停止 查詢 / 交易) | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB607.cs:246-277` |
| `OFDB610` | 更新前 | 資料有誤 | 是 | **阻擋**「資料有誤!已取消更新動作」(三處) | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB610.cs:104` `:111` `:120` |
| `OFDB610` | 查詢後 | 零筆 | 是 | **阻擋**「無可套印資料」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:232` 與 `:324` |
| `OFDB615` | LDAP 查詢 | 帳號不在 LDAP | 不在 | **阻擋**「此帳號不存在LDAP」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB615.cs:303` |
| `OFDB615` | LDAP 更新後 | 更新失敗 | 失敗 | **阻擋**「執行LDAP更新失敗，請檢查」 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB615_Ctl.cs:57` |
| `OFDB616` | 列印前 | — | — | **詢問**「請確認是否列印密碼函？」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB616.cs:164` |

`OFDB615` 與 `OFDB616` 的 `ExecuteNonQuery` 回傳值**有接**(`OFDB615:285` `:318` `:329`,`OFDB616:308` `:340` `:350`),但接完之後有沒有判斷,要逐處看 —— 其中 `OFDB615:392` 與 `OFDB616:401` 兩處是**接都沒接**。

### 6.8 員工交易那一群:`OFDB671` `OFDB672` `OFDB673` `OFDB690` `OFDB691`

**業務邏輯(推測):** 公司員工本人在網路上下單,要先經過投管部與公司的兩層審核才能放行。`OFDB671` 設定誰是審核人,`OFDB691` 逐筆審,`OFDB690` 取消,`OFDB672` 與 `OFDB673` 是「員工離職 / 換部門時整批改掛員工代碼與銷售機構」的送審與覆核。

| 畫面 | 編譯 | 觸發 | 參數 | 寫哪些表 | SP | 重跑 | 相依 |
|---|---|---|---|---|---|---|---|
| `OFDB671` | 齊 | 人工 | 審核人員(投管部 / 公司各一組,含起訖日與起訖時間) | `OFD678A` | 無 | **整批刪除再重建**,天然冪等 | 無 |
| `OFDB672` | 齊 | 人工 | 原員工代碼 / 原銷售機構 / 新員工代碼 / 新銷售機構,勾選申購單 / 買回單 / 定額契約 | `OFDB672`(暫存) | `S_TA_OFDB672_GET` | 有擋重覆 | `OFDB673` 未審完不可再送 |
| `OFDB673` | 齊 | 人工 | 同上三個勾選 | `OFD221A` `OFD251A` `RSP006A`(SP 內) | `S_TA_OFDB673_EXE` | 無防護 | 必須先有 `OFDB672` 送審 |
| `OFDB690` | **未編** | 人工 | 取消員工交易日期 | (SP 內) | `s_OFDB690_Get` | 無 | 無 |
| `OFDB691` | 齊 | 人工 | 申請日期、受益人 ID / 戶號、網路流水號、資料別、交易書號、基金代碼 | `OFD620A` `OFD621A` `OFD641A` `OFD651A` | `S_EC_OFDB691_SENDBACK` `s_OFDB691_Booking` | 無防護 | **買回 / 轉申購拋轉的前置**(§6.5) |

#### `OFDB671` 的 delete-and-reinsert

```
strSQL = @"DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN";
...
dbTA.AddInParameter(cmdExecute, "INV_DEP_YN", OracleDbType.Varchar2,
                    strFunctionID == "OFDB671_A" ? "Y" : "N");
dbTA.ExecuteNonQuery(cmdExecute, tran);
```

錨點 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:43-49`。

| 問題 | 說明 |
|---|---|
| **刪除條件只有一個 Y/N 旗標** | 沒有批號、沒有使用者、沒有時間。兩個人同時開這支畫面,後存檔的會把先存檔的整組審核人員刪掉。這是 `bms.md` 記的「暫存表 `DELETE` 不帶批號」同一個家族的問題,只是這裡刪的是正式表 |
| **行為依 `FunctionID` 分流** | `strFunctionID == "OFDB671_A"` 寫死在程式裡,**同一支畫面掛在兩個選單項目上會有不同行為**。換站台若選單代號不同,這行就失效並一律走 `"N"` 分支〔客戶特定〕 |
| **`ExecuteNonQuery` 回傳值丟掉** | `:49` 與 `:119`,刪了幾列、插了幾列都不知道 |

#### `OFDB672` 與 `OFDB673` 的兩段式

`OFDB672` 執行前先問一次:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 同銷售機構與員編的變更已在 `OFDB673` 審核中 | 是 | **阻擋**「同銷售機構及員編變更已在OFDB673審核中，不可重覆執行」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:35` |
| 查詢後 | 零筆 | 是 | **阻擋**「查無資料」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:104` |
| `OFDB673` 覆核前 | — | — | **詢問**「是否同意變更？」 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89` |

**`OFDB673` 這一端沒有對稱的檢核** —— 沒有「這筆已經審過了」的防護,`S_TA_OFDB673_EXE` 重複執行會怎樣,repo 判斷不出來。兩支的 `ExecuteNonQuery` 回傳值都丟掉(`OFDB672:58`、`OFDB673:37`)。

**跨模組影響最大的就是這兩支:** 它們改的 `RSP006A` 是 RSP 的定期定額契約明細(`rsp.md §2`),`OFD221A` / `OFD251A` 是申購單與買回單。詳見 §8.2。

#### `OFDB691` 員工交易審核

畫面分五個頁籤:申購交易 / 贖回交易 / 轉換交易 / 定額申購 / 定額異動,各對應一張 vdb DataTable(`OFDB691_ALLOT` / `_REDEM` / `_SWITCH` / `_RSP` / `_RSP_CHG`)。有「全部通過 / 全部不通過」兩個批次按鈕。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢後 | 零筆 | 是 | **阻擋**「查無資料」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:103` |
| 執行中 | 買回書號檢核未過 | 未過 | **阻擋**「檢核買回書號時,有資料未檢核通過!!」(三處) | `:485` `:522` `:602` |
| 執行中 | 轉申購書號檢核未過 | 未過 | **阻擋**「檢核轉申購書號時,有資料未檢核通過!」 | `:567` |
| 例外 | — | — | **阻擋**,訊息為空(五處) | `:109` `:416` `:617` `:698` `:754` |

`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:89-90` `:150-151` `:210-211` 六處用 `<> '值'` 組 SQL 條件 —— Oracle 三值邏輯(附錄 E4)。

`OFDB691_Ctl.cs:610-650` 有一整段 `/* … */` 區塊註解(結尾 `#endregion old mark`),裡面是 `ECAdapter.SendRealTimeMail` 的即時發信。**所以 `OFDB691` 現在不發信** —— 用行為單位的 `grep ECAdapter` 會誤判它有發,要看有沒有被區塊註解包住。

### 6.9 扣款與核印:`IPJB613` `IPJB614`

|  | `IPJB613` | `IPJB614` |
|---|---|---|
| 用途(推測) | 網路定額扣款送件 | 核印資料處理 |
| 觸發 | 人工 | 人工 |
| 參數 | 執行功能(送件 / 重送 / 取消)、扣款日期、扣款行、送件批號、文件存放路徑、扣款方式(E/C 扣款 / IVR 扣款 / 傳真委扣扣款)、業務別、挑選基金方式、申購日期 | 核印申請日、受益人 ID、基金代碼、定額書號 |
| SP | `S_EC_DDCT_P01` | 無 |
| 寫哪些表 | (SP 內) | `OFD655A` |
| 產出 | 檔案(`FILEList` DataTable)加報表 `IPJB613RPS.rpt` | — |
| 重跑 | **有三段互斥檢核**(見下) | 無防護 |
| 外部 | 檔案落地到「文件存放路徑」〔客戶特定〕 | 無 |

**`IPJB613` 的三段互斥:**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 送件前 | 已有扣款資料 | 有 | **阻擋**「已有扣款資料，無法執行{0}扣款送件作業」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:66` |
| 送件前 | 尚有扣款資料 | 有 | **阻擋**「尚有扣款資料，無法執行扣款送件作業」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:68` |
| 送件前 | 員工交易件尚未比對 | 未比對 | **阻擋**「員工交易件尚未作比對，不可產生扣款資料」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:77` |

第三條又把扣款線綁到員工審核線上。

`IPJB613` 用 `STATUS = '0' / '1' / '2'` 三個值分別代表未送件 / 已送件 / 重送或取消(`:398` `:251` `:307`)—— 這是本片 C# 端唯一寫死業務狀態值的地方。`Dev/ATLAS.EC/Source/UI/UI.EC/IPJB613.cs:156` 用 `Encoding.Default` 寫檔,**中文語系下是 cp950,換語系會亂碼**〔客戶特定〕。

`IPJB614` 的 `ExecuteNonQuery` 回傳值丟掉並改用 `i += 1` 手動累計(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB614OracleDao.cs:218-219`)—— 也就是說即使 `UPDATE` 影響 0 列,計數仍然加一,**畫面回報「處理 N 筆」跟資料庫實際異動筆數無關**。

### 6.10 `OFDB693` — 到價通知基金白名單(唯一走四眼的 B)

| 項目 | 內容 |
|---|---|
| **基底** | `BaseEVADao`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB693OracleDao.cs:18`) |
| **主表** | `OFD688A`,vdb `OFDB693`(`:30`) |
| **畫面** | 左右兩個清單:「選取基金」與「已設定基金」 |
| **四眼** | 走標準流程,`EVAType.Add` 出現在 `:136` |
| **`ExecuteNonQuery`** | `:213` 回傳值丟掉 |
| **失敗** | 回空訊息(`:70`) |

它是 §6 裡唯一一支會進四眼待辦的批次,形式上是 B、實質上是維護畫面。**改它要按四眼流程走,不能像其他 27 支那樣「按下去就生效」。**

### 6.11 28 支批次的「一律回報成功」逐支檢查

`db.ExecuteNonQuery` 在本片 PO 層共 95 處,**68 處有接回傳值、27 處丟掉**。丟掉的那些裡最嚴重的是「丟掉之後寫死 1 再當成處理筆數回報」:

| 畫面 | 錨點 | 下一行 |
|---|---|---|
| `IPJB606` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:219` | `i = 1;` |
| `IPJB625` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:161` | `i = 1;` |
| `OFDB601` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:265` | `i = 1;` |
| `OFDB602` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:278` | `i = 1;` |
| `OFDB604` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs:244` | `i = 1;` |
| `OFDB605` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:158` | `i = 1;` |
| `IPJB614` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB614OracleDao.cs:218` | `i += 1;`(每列加一) |

**這七支的「處理筆數」是程式自己編的,不是資料庫回的。** 五支拋轉批次(`OFDB601` `OFDB602` `OFDB604` `OFDB605` `IPJB606`)全部中,所以**拋轉完成後畫面顯示的筆數永遠是 1,跟實際拋了幾筆無關**。

另外 20 處純粹不接回傳值也不寫死(例:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:49`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:58`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:37`),影響是「DELETE 條件打錯刪了 0 列也照樣 commit 回成功」。

**唯二會判斷回傳值的是 `OFDM602` 與 `OFDM603`**(§4.4),兩支 M。**28 支 B 一支都沒有。**

---

## 7. 報表(R)

**本片無 R 畫面。**

EC 的報表全部在 `Dev/ATLAS.EC.Report/`,不在本片範圍。本片 `Dev/ATLAS.EC/Source/UI/UI.EC/` 下的 5 個 `.rpt` 是**掛在 B 畫面上的套印格式**,不是獨立報表畫面(清單見 §3.4)。

三點補充:

1. **命名用 `<代號>RPS`**,不是 `architecture.md §6` 描述的 R 型命名。這是本片特有的第三種例外。

2. **兩個 `.rpt` 的宿主畫面已經不編譯了**(`OFDB606RPS` 與 `OFDB610RPS`),但 `.rpt` 與它的包裝類別還在編譯(`Dev/ATLAS.EC/Source/UI/UI.EC/UI.EC.csproj:415` 與 `:440`)。

3. **`ApplyForm.rpt` 不屬於任何畫面代號**,`ApplyForm.cs` 也沒有代號前綴 —— 它是 `architecture.md §9` 講的「沒有 Control 的孤兒」在本片的一個實例,但因為它是 `.rpt` 包裝類別而不是畫面,掃描器的 51 個孤兒清單裡沒有它。

---

## 8. 跨模組共用

```text
[圖] EC 對 BMS 與 RSP 的跨模組寫入,以及 EC Web Service、LDAP、SMTP 三條外部介接
圖中文字:跨模組寫入:EC 改別人的表,而且都不走對方的四眼 / EC 七支程式 / 裸 UPDATE OFD607A / BMSM001 BMSM006 / DetailTable 四眼 / OFD601 OFD607A / 擁有權在 BMS / BMS 覆核刪除 / 直接 DELETE OFD607A / OFDB672 OFDB673 / 員編 銷售機構整批改 / S_TA_OFDB673_EXE / 版控外 看不到 / RSP006A / RSP 定額契約明細 / OFD221A OFD251A / 申購單 買回單 / OFDM681 未編譯 / 唯一維護入口 / OFD681 / SEND_TYPE 分群 / OFDB600 OFDB680 OFDB690 / 讀它決定寄給誰 / RSP 用 SEND_TYPE 6 / 本片用哪些值不明 / 外部介接三條:全部經 TA.ServerUtility〔客戶特定〕 / OFDB609_Ctl / 唯一還活的呼叫端 / ECAdapter / MakeECPassword 加 Encode / ECService TAService / localhost asmx / 空 catch 包住 / 不通就寫空密碼 / OFDB609 OFDB615 / UpdateLDAPCustomer / LDAPAPIHelper / ID Email 手機三種 / LDAP 目錄服務 / 端點在 LDAPAPIPath / DB 已 commit 才打 / 失敗只寄信不回滾 / OFDB600 OFDB680 / SendMail 到價通知 / SMTP 25 埠 / mail.vendor.com.tw / OFDB691 的發信 / 整段區塊註解 已死 / GenBillHunterMail / 零呼叫 回值永遠空
```

*圖:圖 5 跨模組與外部介接。橘框=EC 這一側的寫入點或缺陷;黑虛框=擁有權在別的模組、或已成死碼;黑框=無原始碼、從呼叫端反推;橘虛框=端點與值域〔客戶特定〕。三條外部路徑的失敗處理各不相同:EC Web Service 完全靜默、LDAP 寄信不回滾、SMTP 依各處。*

### 8.1 `OFD601` 與 `OFD607A`:EC 天天改,但主檔在 BMS

這是本片跨模組影響最大的一條,也是派工單特別要求釐清的一條。

**先講結論:全庫沒有任何畫面把 `OFD601` 或 `OFD607A` 宣告成 `MasterTable`。** 唯一的 `xTableMapping` 宣告在 BMS,而且掛在 `DetailTable`:

| 宣告 | 錨點 |
|---|---|
| `this.DetailTable.Add(new xTableMapping("OFD607A", "OFD607A"));` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:156` |
| `this.DetailTable.Add(new xTableMapping("OFD601", "OFD601"));` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:157` |
| `this.DetailTable.Add(new xTableMapping("OFD601", "OFD601"));` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:116` 與 `:177` |
| `this.DetailTable.Add(new xTableMapping("OFD607A", "OFD607A"));` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:176` |

`bms.md §8` 已經從 BMS 那一側寫過這兩張表;本文從 EC 這一側補上另一半。

**所以「誰在寫」的完整答案分兩類:**

| 類別 | 誰 | 怎麼寫 | 走不走四眼 |
|---|---|---|---|
| **擁有者** | BMS `BMSM001`(受益人開戶)、`BMSM006`(受益人變更) | 掛成 `DetailTable`,由四眼引擎依 schema 產生全欄位 INSERT / UPDATE | **走** |
| **改欄位的** | EC 七支程式 | 手寫 `UPDATE OFD607A SET <幾個欄位>` 字串 | **不走** |

EC 這七處逐一列出(已剝註解):

| 畫面 | 錨點 | 改什麼欄位 |
|---|---|---|
| `OFDB606`(**未編**) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB606OracleDao.cs:117` 與 `:131` | 密碼相關 |
| `OFDB609` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:179`、`:456`、`:897`、`:918`、`:942`、`:954` | `EC_PSW` / `ES_PSW` 與開戶進度 |
| `OFDB610`(**未編**) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:519` | `DOC_SEND_DT` / `DOC_PRINT_UID`,條件寫死 `SYSTEM_ID='1'` |
| `OFDB615` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:171`、`:209`、`:239` | 網路密碼 |
| `OFDB616` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs`(三處同款) | 密碼函補發 |
| `IPJM614` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:1086` | `PROCESS_YN = 'Y'` |
| `OFDM607` | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM607_PO.cs:213`(死路徑)與 `Oracle/OFDM607OracleDao.cs:194-198`(活路徑) | `PROCESS_YN = 'Y'`,條件寫死 `SYSTEM_ID='1'` |

**要注意的三件事:**

1. **`BMSM001_PO.cs:1403` 有一句實體刪除:** `DELETE FROM OFD607A WHERE BF_SRNO=:BF_SRNO`。BMS 覆核刪除受益人時會把 EC 的網路戶整筆刪掉,EC 這邊沒有任何對應的處理。

2. **`OFD601` 的欄位數統計在 `bms.md §2` 被標為「跨 xsd 聯集,有雜訊」**,其中 `TagNumber` 與 `age` 兩欄來自 EC 模組 —— 對照回來就是 `OFDB610Model.xsd` 的 `Tag` 那張 DataTable。改 `OFD601` 前要確認欄位屬於哪一份定義。

3. **改 `OFD607A` 的欄位定義要同時看兩邊:** BMS 那邊靠 `TableHelper` 讀資料庫 schema 自動產生全欄位語句(`architecture.md §4`),加欄位不用改程式;EC 這邊是手寫欄位清單的 `UPDATE`,**加欄位不會自動跟上,但也不會壞**。反過來,**刪欄位或改欄位型別會讓 EC 這七處全部報錯,而且是執行期才報**。

### 8.2 `RSP006A` / `OFD221A` / `OFD251A`:`OFDB672` 與 `OFDB673` 直接改 RSP 的契約明細

`OFDB672Model.xsd` 與 `OFDB673Model.xsd` 的 DataTable 是 `OFD221A`(申購單)、`OFD251A`(買回單)、`RSP006A`(定期定額契約明細)。畫面上三個勾選框就是「申購單 / 買回單 / 定額契約」。

| 項目 | 內容 |
|---|---|
| 做什麼 | 員工離職或換部門時,把他名下的申購單 / 買回單 / 定額契約整批改掛到新的員工代碼與銷售機構 |
| 送審 | `OFDB672` 寫暫存表 `OFDB672`,SP `S_TA_OFDB672_GET` |
| 覆核 | `OFDB673` 走 SP `S_TA_OFDB673_EXE` 實際改三張表 |
| 實際 UPDATE 在哪 | **在 SP 裡,repo 看不到** |

**`rsp.md §2` 記 `RSP006A` 是定期定額契約的明細表,PK 是契約書號加契約序號,有「扣款金額」「扣款日1/2/3」「契約手續費率」等欄位。** `OFDB673` 改的是它的員工代碼與銷售機構欄位 —— **這是 EC 對 RSP 唯一的寫入路徑,而且繞過 RSP 自己的四眼**。`rsp.md §8` 從 RSP 側盤點「誰會直接 MERGE 進 `RSP006A`」時列的是 BMS;**EC 的 `OFDB673` 是第三個,本文補上**。

改動影響:動 `RSP006A` 的員工欄位定義,要同時看 `Dev/ATLAS.RSP/`、`Dev/ATLAS.BMS/`、以及本片的 `OFDB672` / `OFDB673` 加版控外的 `S_TA_OFDB673_EXE`。

### 8.3 `OFD681`:兩支服務讀它決定寄信給誰,維護畫面卻沒編譯

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `OFDB600` | `OFDB600_9iModel.xsd` 有 `OFD681` 與 `OFD681_EMP` 兩張 DataTable;`SendMail` 用它組收件人 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:112` 起 |
| `OFDB680` | `OFDB680Model.xsd` 有 `OFD681` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs` |
| `OFDB690`(**未編**) | 也讀 `OFD681` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB690OracleDao.cs` |
| `OFDM681`(**未編**) | 唯一的維護入口 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:22` |

**`rsp.md` 提過 `OFD681.SEND_TYPE = '6'` 是 RSP 的郵件群組〔客戶特定〕** —— 對照本片 `OFDM681Model.xsd` 的 `SEND_TYPE` Caption「Email發送類型」,可以確定 **`OFD681` 是全庫共用的通知信名單表,靠 `SEND_TYPE` 分群給不同模組用**。RSP 用 `6`,EC 用哪些值 repo 裡看不到(畫面上是下拉選單,值域來自資料庫)。

**改動影響:** 這張表跨 EC 與 RSP 兩個模組至少五支程式,而且**唯一的維護畫面沒進編譯**。

### 8.4 用到的共用元件

| 元件 | 位置 | 本片誰用 |
|---|---|---|
| `ECAdapter`(SOAP 到 EC 系統) | `Dev/Common/Source/Utility/TA.ServerUtility/ECAdapter.cs` | `OFDB609_Ctl`(活)、`OFDB606_Ctl` 與 `OFDB690_Ctl`(未編)、`OFDB691_Ctl`(被區塊註解) |
| `LDAPAPIHelper` | `Dev/Common/Source/Utility/TA.ServerUtility/LDAPAPIHelper.cs` | `OFDB609_Ctl:92` `:195`、`OFDB615_Ctl:52` `:104` |
| `LDAPAPIPath` | `Dev/ATLAS.EC/Source/Control/Control.EC/LDAPAPIPath.cs` | 本片自己的 LDAP 路徑常數,**不在 `Common` 下** |
| `SerialNo` | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs` | `OFDB671OracleDao:39` 的 `new SerialNo(tranPTPF, dbPTPF)` |
| `EVAStringHelper.AllEVAColumnsForSelect` | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs` | 16 支 M 的 SELECT 尾端 |
| `ServerBizUtility.GetBusinessDay` | `Dev/Common/Source/Utility/TA.ServerUtility/` | `OFDB609_Ctl:60` 判營業日 |
| `TA.MappingCode`(`CTL014` 等) | `Dev/Common/Source/MappingCode/TA.MappingCode/` | 87 處,`CTL014` 21 處 |

### 8.5 外部介接總表〔客戶特定〕

`architecture.md §7` 說 `TA.ServerUtility` 是「所有往系統外面打的集中地」。本片實際往外打的只有三條:

| 介面 | 端點 | 誰打 | 失敗處理 |
|---|---|---|---|
| **EC Web Service**(`ECService.TAService`) | `http://localhost/ECService/TAService.asmx`(`Dev/Common/Source/Utility/TA.ServerUtility/App.config:12`) | `OFDB609_Ctl:418` `:434` | **空 `catch`,完全靜默** |
| **LDAP API** | 位置在 `Dev/ATLAS.EC/Source/Control/Control.EC/LDAPAPIPath.cs` | `OFDB609_Ctl`、`OFDB615_Ctl` | 累積訊息加寄信,**不 rollback** |
| **SMTP**(寄信) | `mail.vendor.com.tw:25`(三支服務的 `App.config`) | `OFDB600OracleDao.SendMail`、`LDAPAPIHelper.SendMail`、`OFDB680` 的到價通知 | 依各處 |

**`ECAdapter` 的四個方法本片只用到三個**(`MakeECPassword` / `EncodeString` / `SendRealTimeMail`),第四個 `GenBillHunterMail` 在本片零呼叫。那支方法本身也有問題:

```
public string GenBillHunterMail(DataSet insContent)
{
    String a = insContent.Tables["OFDB609"].Rows[0]["ID_NO"].ToString();   // a 從未被使用
    string MailString = string.Empty;
    try { BillHunter_PO po = new BillHunter_PO(); po.GetBillHunterMail(insContent); }
    catch (Exception ex) { CommonExceptionBlocker.HandleBusinessException(ex); }
    return MailString;                                                      // 永遠回空字串
}
```

錨點 `Dev/Common/Source/Utility/TA.ServerUtility/ECAdapter.cs:91-107`。**方法名叫 `OFDB609`、參數表名寫死 `"OFDB609"`,卻放在共用元件裡** —— 這支共用方法其實是為本片的 `OFDB609` 寫的,而 `OFDB609_Ctl:71-72` 呼叫它的那兩行**被註解掉了**。整條路徑現在是死的。

> `localhost` 這個端點意味著 EC Web Service 必須跟 AP Server 裝在同一台機器上。這跟 `OFDB680_Service`「不是 Remoting 客戶端」(§6.4)加起來看,部署拓樸比 `architecture.md §8` 描述的複雜:**`OFDB680` 那台需要資料庫直連權限;`OFDB600` / `OFDB609` 那兩台需要 Remoting 端點,而且 `OFDB609` 走的 `ECAdapter` 是在 AP Server 端執行,localhost 指的是 AP Server 不是服務機。** 這是**假設**,依據是 Remoting 把 Ctl 的執行搬到伺服端。

### 8.6 改動影響面速查

| 你要改 | 一定要一起看 |
|---|---|
| `OFD607A` 的欄位 | BMS `BMSM001` / `BMSM006` 的四眼路徑,加本片七處手寫 `UPDATE`(§8.1) |
| `OFD601` 的欄位 | 同上,加 `bms.md §2` 的「跨 xsd 聯集」警告 |
| `RSP006A` 的員工欄位 | RSP 主線、BMS 的 `MERGE`、本片 `OFDB673` 加 SP `S_TA_OFDB673_EXE`(§8.2) |
| `OFD681` | `OFDB600` `OFDB680` `OFDB690` 加 RSP 的 `SEND_TYPE = '6'`(§8.3) |
| 任何一支 `S_EC_IPJB60x_EXCUTE` | **兩支畫面同時受影響**(§6.5) |
| `OFD606A`(基金網路交易參數) | `OFDM601` 維護、`OFDB600` / `OFDB612` / `OFDB693` / `OFDM690` 讀 |
| `ECAdapter` | 本片只剩 `OFDB609` 的兩處活著,但 `architecture.md §7` 列的其他模組也在用 |
| 三支服務的 `App.config` | **`OFDB680` 那份跟另外兩份結構不同**(§6.4),不要照抄 |

---

## 附錄 A. 資料表總表

掃描方式:對 `Dev/ATLAS.EC/Source/` 下所有非 Designer 的 `.cs`,**剝掉 `//` 開頭的行之後**,抓 `FROM` / `JOIN` / `INTO` / `UPDATE` 後面的識別字,再過濾出 `OFD*` / `LOG*` / `RSP*` / `BMS*` / `FSK*` / `CTL*` / `IVR*` / `Z_*` 前綴。共 **82 個名字**(含暫存表與同名 vdb DataTable)。

### A.1 本片擁有或主要操作的表

| 表 | 被幾個檔碰 | 主要使用者 | 推測用途 |
|---|---|---|---|
| `OFD600A` | 2 | `OFDM600` `OFDB600` `OFDB609` | 網路交易全站參數(單列) |
| `OFD601` | 6 | 見 §8.1 | 受益人網路戶基本資料〔共用,主檔在 BMS〕 |
| `OFD601CHG` | 4 | `IPJM614` `IPJB625` `OFDB605` `OFDB600` | 網路戶基本資料變更單 |
| `OFD604A` | 2 | `OFDM603` | 網路交易手續費率 |
| `OFD605A` | 1 | `OFDM602` | 文件需求清單設定 |
| `OFD606A` | 5 | `OFDM601` 加 4 支讀 | 基金網路交易參數 |
| `OFD607` | 3 | `OFDB609` `OFDB615` `OFDB616` | 網路戶(舊表?與 `OFD607A` 並存) |
| `OFD607A` | 9 | 見 §8.1 | 網路戶註冊檔〔共用,主檔在 BMS〕 |
| `OFD607ACHG` | 1 | `IPJM614` | 網路戶註冊變更單 |
| `OFD608A` | 2 | `OFDM607` | 網路開戶文件繳交明細 |
| `OFD611A` | 2 | `IPJB621` `OFDB601` | 單筆申購交易檔 |
| `OFD612A` | 2 | `IPJB622` `OFDB602` | 買回交易檔 |
| `OFD613A` | 2 | `IPJB622` `OFDB602` | 買回交易明細(推測) |
| `OFD614A` | 2 | `IPJB624` `OFDB604` | 定額異動檔 |
| `OFD615A` | 2 | `IPJB625` `OFDB605` | 受益人資料變更檔 |
| `OFD616A` | 1 | `IPJB606` | 轉申購交易檔 |
| `OFD618A` | 4 | 四支 `IPJB6xx` | 拋轉記錄(推測) |
| `OFD620A` | 7 | 拋轉與扣款群 | 交易主檔(推測) |
| `OFD621A` | 6 | `OFDB611` `OFDB612` `OFDB691` 等 | 扣款檔 |
| `OFD641A` | 1 | `OFDB691` | 員工審核相關 |
| `OFD651A` | 4 | `OFDB600` `OFDB602` `IPJB622` `OFDB691` | 買回書號相關 |
| `OFD654A` | 1 | `OFDB691` | 同上族 |
| `OFD655A` | 4 | `IPJB614` `IPJB624` `OFDB600` `OFDB604` | 核印申請檔 |
| `OFD656A` | 2 | `IPJB624` `OFDB604` | 定額異動相關 |
| `OFD657A` `OFD658A` `OFD661A` | 1 到 2 | `OFDB600` `IPJB606` | 時限截止相關 |
| `OFD670A` / `OFD671A` | 1 | `OFDM670` | 理財活動主檔 / 參數明細 |
| `OFD674A` | 1 | `OFDM674` | 基金促銷設定 |
| `OFD675A` | 1 | `OFDB609` | 開戶後續處理相關 |
| `OFD676A` | 1 | `OFDM604` `OFDB691` | 員工交易審核不核准原因 |
| `OFD678A` | 1 | `OFDB671` | 員工交易審核人員設定 |
| `OFD680A` | 1 | `OFDM680` `OFDB680` | 到價提示發送時間 |
| `OFD681` | 1 | 見 §8.3 | 通知 Email 名單〔共用,RSP 也用〕 |
| `OFD682A` `OFD683A` `OFD684A` `OFD696A` | 各 1 | `OFDB680` | 到價通知的四張結果表 |
| `OFD685A` | 1 | `OFDM697` | 產品代碼 |
| `OFD686A` | 1 | `OFDM698` | 產品組合 |
| `OFD688A` | 1 | `OFDB693` | 到價通知基金白名單(四眼) |
| `OFD690A` | 1 | `OFDM690` | 基金所屬類別設定 |
| `OFD691A` | 1 | `OFDM695` `OFDM690` | 基金所屬類別代碼字典 |
| `OFD695A` | 1 | `OFDM694` | 基金投資區域代碼字典 |
| `OFD699A` | 1 | `OFDM699` | 節日代碼 |
| `LOG602` | 3 | `OFDB609` `OFDB615` `OFDB616` | 密碼異動記錄 |
| `LOG616A` | 1 | `OFDM696` | 網路瀏覽 LOG 代碼 |
| `ivr_map_wav` | 1 | `OFDM672` | IVR 基金音檔對照〔客戶特定〕 |
| `Z_OPACT` | 1 | `OFDB609` | 作業記錄(推測) |

### A.2 唯讀 join 進來的外部表

| 表 | 被幾個檔碰 | 屬於誰(推測) |
|---|---|---|
| `OFD081A` | 13 | 基金主檔 —— 本片被 join 最多次的表 |
| `OFD081` / `OFD0811A` | 3 / 1 | 同族 |
| `CTL014` | 11 | 代碼字典(`architecture.md §7` 記過 `TA.MappingCode` 也有同名類別) |
| `FSK003` | 4 | 幣別名稱(FSK 模組) |
| `OFD062` | (SQL 內) | 基金公司 |
| `BMS001` / `BMS001A` / `BMS001CHG` | 3 / 2 / 1 | 受益人主檔(BMS) |
| `BMS081` / `BMS914` / `BMS025` | 2 / 3 / 1 | BMS |
| `OFD027A` `OFD039A` `OFD068` `OFD071A` `OFD088A` `OFD114A` `OFD304A` | 各 1 到 2 | OFD 本體 |
| `OFD190` `OFD190A` `OFD199` `OFD200` `OFD200A` `OFD201A` `OFD202A` `OFD203A` `OFD670` `OFD671` `OFD687A` | 各 1 | **全部只被 `OFDM199AOracleDao.cs` 碰** —— 那支畫面 `OFDM199A` **不在本片 50 支名單內**(它的六層在 `ATLAS.EC` 底下但代號不屬本片) |
| `OFD221A` / `OFD251A` | 1 | 申購單 / 買回單,被 `OFDB672` `OFDB673` `OFDB691` 改寫(§8.2) |
| `RSP006A` | (xsd) | 定期定額契約明細(RSP)(§8.2) |
| `OFD600` | 2 | `OFDB609` `OFDB690` 讀 |

### A.3 暫存表(不是業務表)

| 表 | 誰建 | 說明 |
|---|---|---|
| `OFDB672` | `OFDB672` | 員工代碼變更送審暫存,`OFDB673` 讀它 |
| `OFDB680` / `OFDB680_3` / `OFDB680_XML` | `OFDB680` | 到價計算中繼;`_XML` 從名字看是組信用的 XML 暫存 |

> ⚠ **`OFDB680` 這個名字同時是畫面代號、vdb DataTable 名、實體暫存表名。** `grep OFDB680` 會同時撈到三種東西,反查時要看上下文。

---

## 附錄 B. SP / Function / Trigger / View

### B.1 Stored Procedure(從呼叫端反推,共 18 支)

**`DB/` 底下一支都沒有。** 全部列進 meta 的 `refcheck-ignore`。

| SP | 被誰呼叫 | 錨點 |
|---|---|---|
| `S_EC_IPJB600_EXCUTE` | `OFDB600` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:48` |
| `S_EC_IPJB601_EXCUTE` | `IPJB621` 加 `OFDB601` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB621OracleDao.cs:238` / `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:230` |
| `S_EC_IPJB602A_EXCUTE` | `IPJB622` 加 `OFDB602` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:267` / `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:261` |
| `S_EC_IPJB604_EXCUTE` | `IPJB624` 加 `OFDB604` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB624OracleDao.cs:223` / `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs:217` |
| `S_EC_IPJB605_EXCUTE` | `IPJB625` 加 `OFDB605` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:138` / `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:134` |
| `S_EC_IPJB606_EXCUTE` | `IPJB606` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:192` |
| `S_EC_DDCT_P01` | `IPJB613` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:86` |
| `S_EC_OFDB607_Excute` | `OFDB607` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB607OracleDao.cs:145` |
| `S_EC_OFDB608_Excute` | `OFDB608` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB608OracleDao.cs:56` |
| `S_EC_OFDB609_Excute` | `OFDB609` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB609OracleDao.cs:86` |
| `S_EC_OFDB680_GET` | `OFDB680` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs` |
| `S_EC_OFDB691_SENDBACK` | `OFDB691` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs` |
| `s_OFDB691_Booking` | `OFDB691` | 同上 |
| `S_TA_OFDB672_GET` | `OFDB672` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs` |
| `S_TA_OFDB673_EXE` | `OFDB673` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs` |
| `s_OFDB610_Get` | `OFDB610`(**未編**) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs` |
| `s_ECFunGetAccountData` | `OFDB610`(**未編**) | 同上 |
| `s_OFDB690_Get` | `OFDB690`(**未編**) | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB690OracleDao.cs` |

**命名不一致有三套:** `S_EC_*`(11 支)、`S_TA_*`(2 支)、`s_*` 小寫(3 支)、`S_EC_*_Excute` 大小寫混用(`Excute` 是拼錯的 `Execute`,而另一批寫成全大寫 `EXCUTE`)。用 `grep -i` 才找得全。

### B.2 Function / Trigger / View

**本片零呼叫。** 全 EC 的 `.cs` 裡沒有任何 `f_TA_*` 或 `F_*` 的函式呼叫,也沒有任何 View 名被直接查詢(所有 `FROM` 後面的都是表)。這跟 `rsp.md 附錄 B` 那邊 30 支 SP 加多支 fn 的規模差很多 —— **EC 的商業邏輯集中在 18 支 SP 裡,沒有再往下拆。**

---

## 附錄 C. 代碼對照

全部從程式反推,**沒有一個來自代碼字典表**。

| 代碼欄 | 值 | 語意(推測) | 來源錨點 |
|---|---|---|---|
| `SYSTEM_ID` | `1` | 網路 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:519` 寫死;畫面選項「網路」 |
|  | `2` | 語音(IVR) | 畫面選項「語音」;`OFDB605` 的檢核訊息「OFD600中有語音交易資料」 |
| `BMS_CTL_CODE` | `1` | 拋轉 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:301` 的 `where BMS_CTL_CODE='1'` |
|  | `2` | 拋轉回復 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:215` 的 `wBMS_CTL_CODE == "2"` |
| `STATUS`(扣款檔) | `0` / `1` / `2` | 未送件 / 已送件 / 重送或取消 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB613OracleDao.cs:398` `:251` `:307` |
| `STATUS`(四眼) | 第三碼 `3` | 刪除動作 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:603` 的 `STATUS.Substring(2, 1) == "3"` |
| `ALERT_SET` | `1` | 依 `ALERT_TYPE` 分流 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:136` |
|  | `2` | 一律用淨值比 | `:154` |
|  | `3` | **被註解,`#region 用不到`** | `:160` |
| `ALERT_TYPE` | `1` / `2` / `3` | 淨值 / 報酬率上下限 / 損益 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:137` `:142` `:146` |
| `ALERT_RES` | `1` / `2` | 觸發上限 / 觸發下限 | `:149-150` 的 `ALERT_TIMES_H` / `ALERT_TIMES_L` 加一條件 |
| `EXE_TYPE` | `1` | 到價通知的執行別 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:76` |
| `RunType` | `01` | 自動執行 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:82` 加 `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:58` 的 `if (sRunType == "01")` |
| `INV_DEP_YN` | `Y` / `N` | 投管部 / 非投管部審核人員 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:48`,由 `FunctionID == "OFDB671_A"` 決定 |
| `PROCESS_YN` | `Y` | 已處理 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJM614OracleDao.cs:1086` |
| `ReturnRowCount` | `99` | 三支服務共用的「不算錯誤」魔術值,**repo 內找不到產生點** | 三支 `*_Service.cs` |
| `USERID` / `CreateID` / `USER` | `AutoJob` | 服務執行的假使用者 | 三支 `*_Service.cs` |
| `BF_SRNO` | `-1` | 「不指定單筆」的哨兵值 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:57` 與 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:80` |
| `FunctionID` | `OFDB671_A` | 投管部版的選單代號〔客戶特定〕 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:48` |
| `SEND_TYPE` | (值域在資料庫) | Email 發送類型;`rsp.md` 記過 RSP 用 `6` | `OFDM681Model.xsd` |

---

## 附錄 D. 掃描母體與覆蓋率

**不跑 `atlas_scan.py --module OFD` 的覆蓋率工具** —— 本片是 OFD 前綴的一小塊,那個數字對單片沒有意義。改成逐支列。

### D.1 50 支逐一處置

| # | 代號 | 型 | 處置 | 在哪一節 |
|---|---|---|---|---|
| 1 | `IPJB606` | B | 表格帶過(§6.5 雙胞胎表加卡控表) | §6.5 |
| 2 | `IPJB613` | B | **已寫** | §6.9 |
| 3 | `IPJB614` | B | **已寫** | §6.9 |
| 4 | `IPJB621` | B | 表格帶過 | §6.5 |
| 5 | `IPJB622` | B | 表格帶過(含買回專屬卡控) | §6.5 |
| 6 | `IPJB624` | B | 表格帶過 | §6.5 |
| 7 | `IPJB625` | B | **已寫**(四道死檢核) | §6.5 |
| 8 | `OFDB600` | B | **已寫**(一支一節加服務) | §6.2 |
| 9 | `OFDB601` | B | 表格帶過加骨架樣本 | §6.1 §6.5 |
| 10 | `OFDB602` | B | 表格帶過 | §6.5 |
| 11 | `OFDB604` | B | 表格帶過 | §6.5 |
| 12 | `OFDB605` | B | **已寫**(四道死檢核) | §6.5 |
| 13 | `OFDB606` | B | 表格帶過(未編) | §6.7 |
| 14 | `OFDB607` | B | 表格帶過 | §6.7 |
| 15 | `OFDB608` | B | 表格帶過 | §6.7 |
| 16 | `OFDB609` | B | **已寫**(一支一節加服務) | §6.3 |
| 17 | `OFDB610` | B | 表格帶過(未編) | §6.7 |
| 18 | `OFDB611` | B | 表格帶過(未編) | §6.6 |
| 19 | `OFDB612` | B | 表格帶過 | §6.6 |
| 20 | `OFDB615` | B | 表格帶過 | §6.7 |
| 21 | `OFDB616` | B | 表格帶過 | §6.7 |
| 22 | `OFDB671` | B | **已寫**(delete-and-reinsert) | §6.8 |
| 23 | `OFDB672` | B | **已寫** | §6.8 |
| 24 | `OFDB673` | B | **已寫** | §6.8 |
| 25 | `OFDB680` | B | **已寫**(一支一節加服務) | §6.4 |
| 26 | `OFDB690` | B | 表格帶過(未編) | §6.8 |
| 27 | `OFDB691` | B | **已寫** | §6.8 |
| 28 | `OFDB693` | B | **已寫**(唯一走四眼的 B) | §6.10 |
| 29 | `IPJM614` | M | **已寫** | §4.9 |
| 30 | `OFDM600` | M | 表格帶過 | §4.10 |
| 31 | `OFDM601` | M | **已寫** | §4.2 |
| 32 | `OFDM602` | M | **已寫** | §4.4 |
| 33 | `OFDM603` | M | **已寫**(死碼基底) | §4.5 |
| 34 | `OFDM604` | M | 表格帶過 | §4.10 |
| 35 | `OFDM607` | M | **已寫** | §4.3 |
| 36 | `OFDM670` | M | **已寫** | §4.8 |
| 37 | `OFDM672` | M | 表格帶過 | §4.10 |
| 38 | `OFDM674` | M | 表格帶過 | §4.10 |
| 39 | `OFDM680` | M | 表格帶過 | §4.10 |
| 40 | `OFDM681` | M | **已寫**(有主檔但未編) | §4.7 |
| 41 | `OFDM690` | M | 表格帶過 | §4.10 |
| 42 | `OFDM691` | M | 表格帶過(未編) | §4.10 |
| 43 | `OFDM692` | M | 表格帶過(未編) | §4.10 |
| 44 | `OFDM693` | M | 表格帶過(未編) | §4.10 |
| 45 | `OFDM694` | M | **已寫**(死碼基底) | §4.6 |
| 46 | `OFDM695` | M | 表格帶過 | §4.10 |
| 47 | `OFDM696` | M | 表格帶過 | §4.10 |
| 48 | `OFDM697` | M | 表格帶過 | §4.10 |
| 49 | `OFDM698` | M | 表格帶過 | §4.10 |
| 50 | `OFDM699` | M | 表格帶過 | §4.10 |

**統計:一支一節 17 支、表格帶過 33 支、漏掉 0 支。**

### D.2 母體與程式不符的五處

| # | 掃描器說 | 實際 | 原因 |
|---|---|---|---|
| 1 | 50 支全部「PO 缺」 | 49 支有 `*OracleDao.cs` | 命名不是 `*_PO.cs`(§0.3) |
| 2 | `IPJ*` 8 支「Model / View 缺」 | 都有 `_9i` 版 | `architecture.md §9` 已記 |
| 3 | 「48 支無 `MasterTable`」 | 實際 33 支(17 支有) | 掃描器只看 `*_PO.cs`(§0.3) |
| 4 | `OFDM691` / `OFDM692` / `OFDM693` 有 PO | 類別整段被 `//` 註解 | 掃描器不剝註解(`architecture.md §9` 的同一個坑) |
| 5 | 50 支都算「有畫面」 | 8 支四層 csproj 排除 | 掃描器只看檔案存在,不看 csproj(§0.4) |

**第 5 條是新發現的掃描盲點。** `architecture.md 附錄 D` 記過「任何對這個 repo 做靜態統計的工具,第一件事都是剝註解」,本片再補一條:**第二件事是比對 csproj**。

### D.3 怎麼自己重跑

```
# 六層加 csproj 比對(本文用的方法)
py -V:3.12 /docs/tools/atlas_scan.py --screen OFDB600

# 找 MasterTable(要剝註解)
grep -rn "MasterTable\s*=\s*new\|MasterTable.Add(new" Dev/ATLAS.EC/Source/PO/ | grep -v "^\S*:\s*//"

# 找 SP
grep -rn "GetStoredProcCommand" Dev/ATLAS.EC/Source/PO/

# 找畫面中文名(不 Read Designer)
grep -o 'Text = "[^"]*"' Dev/ATLAS.EC/Source/UI/UI.EC/<代號>.Designer.cs

# 比對 csproj 與磁碟
grep -o 'Include="[^"]*_Ctl.cs"' Dev/ATLAS.EC/Source/Control/Control.EC/Control.EC.csproj
```

---

## 附錄 E. 讀本文時要注意的地方

前十一篇實測撈到的缺陷型錄,在本片逐條驗證。**批次類特別容易中的排前面。**

### E1 一律回報成功 —— 本片 27 處,最嚴重的 7 處

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `db.ExecuteNonQuery(cmd, tran);` 下一行 `i = 1;`,再 `AddResultRow(true, i, "")` | **五支拋轉批次的「處理筆數」永遠是 1**,SP 實際拋了 0 筆還是 5 萬筆都一樣。拋轉沒拋到東西不會有人發現 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB601OracleDao.cs:265-266`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:278-279`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB604OracleDao.cs:244-245`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:158-159`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB606OracleDao.cs:219-220`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB625OracleDao.cs:161-162` | **高** |
| `IPJB614` 用 `i += 1` 手動累計而不是取 `ExecuteNonQuery` 回傳 | 核印處理即使 `UPDATE` 影響 0 列也計入,回報筆數與實際異動無關 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB614OracleDao.cs:218-219` | **高** |
| `OFDB671` / `OFDB672` / `OFDB673` 的 `ExecuteNonQuery` 回傳值完全不接 | `DELETE` 條件打錯刪了 0 列也照樣 `Commit` 並回「執行成功」 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:49` 與 `:119`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB672OracleDao.cs:58`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:37` | 中 |
| 另 20 處同款(見 §6.11) | 同上 | 逐處見 §6.11 | 中 |

> **對照:`OFDM602` 與 `OFDM603` 兩支 M 是本片唯二會判 `if (j <= 0)` 就 rollback 的**(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:430-434`)。**28 支 B 一支都沒有。**

### E2 `catch (SqlException)` 在 Oracle 是死碼 —— 6 處

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| Oracle 專案裡寫 `catch (SqlException sqlex)` | **這個分支永遠不會進**,Oracle 丟的是 `OracleException`。原本想給使用者看的 `sqlex.Message` 被下一個 `catch (Exception)` 吃掉,改回 `string.Empty` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:89`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB602OracleDao.cs:287`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/IPJB622OracleDao.cs:315`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB680OracleDao.cs:285` 與 `:560`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB690OracleDao.cs:110` | **高** |

跟 `rsp.md 附錄 E` 記的「RSP 六支這樣寫」一模一樣,本片是六處。`architecture.md §4` 說「執行期是 Oracle-only,SQL Server 只剩兩種殘留」,這是第三種殘留:**例外型別**。

### E3 例外訊息是空字串 —— 38 處

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `AddResultRow(false, 0, string.Empty)` | 使用者看到「執行失敗」四個字,**沒有任何原因**。真正的例外送給 `CommonExceptionBlocker.HandleBusinessException(ex)` 寫 log 檔,操作人員看不到 | 38 處,其中 `OFDB616OracleDao.cs:160` `:164` `:168` `:175` 四處連在一起;完整清單用 `grep -n 'AddResultRow(false, 0, string.Empty)'` | **高** |

這是本片最普遍的一條。要 debug 一次拋轉失敗,必須去 `C:\Vendor\VendorProduct\*.log` 撈,而不是看畫面。

### E4 Oracle 三值邏輯:`<> '值'` 遇 NULL 是 UNKNOWN —— 7 處

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| SQL 條件寫 `欄 <> '值'` | 該欄為 NULL 的列**整批被過濾掉而且沒有提示**。員工交易審核少撈幾筆,不會有任何錯誤訊息 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:89` `:90` `:150` `:151` `:210` `:211`、`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB612.cs:122` | **高** |

七個模組都中過(`rsp.md 附錄 E2`、`bms.md`、`cas.md` 等),本片是第八個。`OFDB691` 那六處在同一支審核畫面的三個查詢分支裡各兩處,**影響的是「哪些員工交易要送審」**。

### E5 被註解掉但外殼還在的檢核 —— 最嚴重的一組

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB605` 與 `IPJB625` 的四道檢核,PO / Ctl / Pxy / 介面**四層都在且都編譯**,只有 UI 的呼叫行被 `//` 掉 | 受益人資料變更拋轉**只剩「有沒有跑過 OFDB600」一道防線**。「尚有未拋轉資料」「尚有已拋轉資料」「已有批次生效資料」「OFD600中有語音交易資料」四道全部不會執行 | `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB605.cs:214` `:370` `:385` `:423`、`Dev/ATLAS.EC/Source/UI/UI.EC/IPJB625.cs:212` `:368` `:383` `:421` | **高** |
| `IPJB606` 的 `CheckSYSTEM_ID` 呼叫被註解 | 轉申購拋轉不再檢查語音資料 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJB606.cs:201` | 中 |
| `OFDB691_Ctl` 的 `ECAdapter.SendRealTimeMail` 整段在 `/* */` 區塊註解裡 | 員工交易審核完**不發即時通知信**;用行註解過濾的 grep 會誤判它還在 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:610-650`(`#endregion old mark`) | 中 |
| `OFDB609_Ctl` 的 `ECAdapter.GenBillHunterMail` 呼叫被註解 | Billhunter 通知信不發 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:71-72` | 低 |
| `OFDB680_Ctl` 的 `ALERT_SET == "3"` 整段註解(`#region 用不到`) | 第三種到價設定靜默不處理,`switch` 又沒有 `default` | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB680_Ctl.cs:160-175` | 中 |
| `OFDB680_Service` 的 `DoExecute()` 整支註解 | 舊的執行入口留著,現行走 `_timer_Elapsed` 內嵌的版本 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:211-239` | 低 |
| `PO/PO.EC/MSSQL/` 28 個檔整支註解卻仍編譯 | 約 9,700 行死碼混在 30 個檔裡,`grep` 命中率極低 | `Dev/ATLAS.EC/Source/PO/PO.EC/PO.EC.csproj:165-194` | 中 |

### E6 檢核方法的回傳語意跟主流程相反,而且例外時放行

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB605` 的四個 `Check*` 方法:`true` = 有問題、`false` = 沒問題,跟 `Execute` 的 `true` = 成功相反;**`catch` 回 `false`** | 就算把 E5 的註解拿掉,檢核時資料庫出錯會被當成「檢核通過」而放行 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:313-330`、`:388-405`、`:471-488`、`:537-554` | **高** |

### E7 死方法 / 無效運算 / 空 `catch`

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB600_Service.BefExec()` 定義了但**沒有任何呼叫端** | log 檔只有「批次執行後」,**永遠無法比對批次處理前後的筆數差** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:164-187`(呼叫端只在 `:72-73` 呼 `DoExecute` 與 `AftExec`) | 中 |
| `sEXEC_TIMES.PadLeft(4, '0');` **回傳值丟掉**,字串沒有被補零 | 資料庫存三碼時間(如 `930`)時,下一行 `Substring(2,2)` 越界丟例外,被空 `catch` 吃掉,**這筆排程靜默消失** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:130-131` | **高** |
| `iLIMIT_TIME_BUFFER` 只在 `else` 分支賦值 | **設定表只有一列時,時間緩衝永遠是 0**,`CHECK_DATE` 不會往前推 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:135-147` | 中 |
| 空 `catch { }` 5 處,全部包住外部呼叫 | EC Web Service 不通時 `MakeECPassword` 回空字串,**空密碼寫進 `OFD607A`**;`SendRealTimeMail` 失敗無痕跡 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:427` 與 `:439`、`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB606_Ctl.cs:74`、`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB690_Ctl.cs:476`、`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:646` | **高** |
| `ECAdapter.GenBillHunterMail` 有一個從未使用的區域變數 `String a`,且 `MailString` 永遠回空字串 | 方法簽名騙人 —— 看起來會回信件內容,實際回空 | `Dev/Common/Source/Utility/TA.ServerUtility/ECAdapter.cs:94` 與 `:106` | 低 |
| `GetTIMES` 的 `catch { }`(`OFDB600`)吃掉每一列的轉換錯誤 | 排程時間解析失敗完全無痕跡 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151` | 中 |

### E8 讀 `[0]` 不先檢查列數 —— 服務會靜悄悄停掉

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `view.UIView.OFDB609_TIMES[0].OPEN_ACC_PROCESS_TIME` | 設定表空的時候丟 `IndexOutOfRangeException`,`sTIMES` 停在空字串,`_timer_Elapsed` 的 `sTIMES != string.Empty` 為假 —— **服務之後永遠不會執行,也不會再寫任何 EventLog** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:116` | **高** |
| `view.UIView.OFDB680_TIMES[0].ALERT_LIMIT_TIMES` | 同上 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:120` | **高** |
| `view.Util.Result[0].ReturnCode` 在 `AftExec` 內不先檢查列數 | 同款,但被外層 `catch` 接住只影響 log | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:201` 與 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:158` | 低 |
| `vdb.DataEntity.OFDM602_Master[0].STATUS` | 同款,在四眼覆核路徑上 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM602OracleDao.cs:603` | 中 |

### E9 無鍵或弱鍵的 DELETE

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN` —— 刪除條件只有一個 Y/N 旗標 | 兩個人同時維護審核人員,**後存檔的整組蓋掉先存檔的**;而且刪的是正式表不是暫存表 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:43-49` | **高** |
| `BMSM001_PO.cs:1403` 的 `DELETE FROM OFD607A WHERE BF_SRNO=:BF_SRNO`(BMS 側) | BMS 覆核刪除受益人時把 EC 網路戶整筆刪掉,EC 這邊七支改它的程式沒有任何對應處理 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1403` | 中 |

### E10 字串串接進 SQL —— 88 處

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `+ "'" + 值 + "'"` 的組法 | 使用者輸入帶單引號就讓語法壞掉。跟 `architecture.md §4` 的評估一致:內網 WinForms 不是公開端點,但「輸入一個帶單引號的基金簡稱就查不出來」天天會發生 | 88 處集中在 10 個檔:`OFDM199AOracleDao.cs`(8+)、`OFDM601OracleDao.cs:128` `:132` `:142` `:146` `:217` `:221` `:231` `:235`、`OFDM607OracleDao.cs`(8)、`OFDM607_PO.cs`(8)、`OFDM681OracleDao.cs:78` `:82` `:90` `:94`、`OFDM690OracleDao.cs:53` `:57` `:65` `:69`、`OFDB605OracleDao.cs:301` `:374` `:450`、`IPJM614OracleDao.cs:176` `:397`、`OFDM670OracleDao.cs:56` | 中 |
| `OFDB691_Ctl` 把 XML 裡的 `'` 換成 ` 才送出 | 註解寫「因為'傳到 bill hunter 會有問題 所以用`取代」—— **用替換字元繞過跳脫,信件內容的撇號會變成反引號** | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB691_Ctl.cs:638`、`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB690_Ctl.cs:467` | 低 |

### E11 寫死常數與位置取參數

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 三支服務的 log 路徑寫死 `C://Vendor//WindowService//OFDB60x//` | 換機器或換磁碟要改程式重編〔客戶特定〕 | `OFDB600_Service.cs:220`、`OFDB609_Service.cs:154`、`OFDB680_Service.cs:175` | 中 |
| Remoting 端點寫死 `http://<內網伺服器IP>/ATLAS_TAService/` 在 `App.config` | 換站台必改〔客戶特定〕 | `WindowsService.OFDB600/App.config:189`、`WindowsService.OFDB609/App.config:189` | 低 |
| EC Web Service 端點 `http://localhost/…` | 綁死同機部署〔客戶特定〕 | `Dev/Common/Source/Utility/TA.ServerUtility/App.config:12` | 中 |
| `OFDB671` 依 `FunctionID == "OFDB671_A"` 分流 | 選單代號改了行為就變,而且是靜默走另一個分支〔客戶特定〕 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:48` | 中 |
| `SYSTEM_ID='1'` 寫死在 `UPDATE` 的 `WHERE` | 語音戶的文件寄送日期不會被更新 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs:519`、`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM607_PO.cs:213` | 中 |
| FATCA 卡控訊息寫死在 UI 的 C# 裡,而且出現兩次 | 政策改了要改程式,而且兩處要一起改〔客戶特定〕 | `Dev/ATLAS.EC/Source/UI/UI.EC/IPJM614.cs:988` 與 `:1003` | 中 |
| `ReturnRowCount != 99` 的魔術值 | repo 內找不到 99 的產生點,語意只能問資料庫 | 三支 `*_Service.cs` | 中 |

### E12 非 UTF-8 來源檔 / 編碼

| 檢查 | 結果 |
|---|---|
| `PO/PO.EC/` 129 個檔的編碼 | **全部 `utf-8-sig`(UTF-8 with BOM),零個 cp950** |
| 全 `Dev/ATLAS.EC/Source/` 的 `.cs` | 同上,沒有踩到 `rsp.md` 那邊「40 支 cp950,grep 中文會漏」的坑 |
| `Encoding.Default` 寫檔 | 2 處:`Dev/ATLAS.EC/Source/UI/UI.EC/IPJB613.cs:156`,加三支服務的 log(`OFDB600_Service.cs:241` `:247` 等)。中文語系下是 cp950,**換語系會亂碼**〔客戶特定〕 |

**所以本片 `grep` 中文是安全的**,這跟 RSP 那片不一樣。

### E13 交易與外部系統之間沒有補償

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB609` 的 LDAP 同步在資料庫 commit **之後**才跑,失敗只寄信不回滾 | 資料庫改了 ID / Email / 手機,LDAP 沒改,客戶登不進去。靠人看信去按「更新LDAP資料」按鈕補 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:79-145` | **高** |
| 同上,單列的 `catch (Exception)` 讓某一列靜默跳過 | 這一列連失敗信都不會提到 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:127-131` | 中 |
| `architecture.md §4` 記的「兩個庫兩個交易,沒有分散式交易」 | 本片 `OFDB671` 同時開 `dbTA` 與 `dbPTPF` 兩個交易(`:36-38`),部分失敗會不一致 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:36-38` | 中 |

### E14 非營業日與零筆在 log 上看不出差別

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB609_Ctl` 非營業日直接回 `AddResultRow(true, 0, "")`,服務端寫 EventLog「Success:」加空訊息 | **「今天放假沒跑」與「跑了零筆」在 EventLog 上一模一樣**,要判斷得去看落地 log 檔 | `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:63-67` 與 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs:86-89` | 中 |
| `OFDB680_Service` 在 `SelectFund` 回零列時仍照常送出 `FUND_ID = ''` 執行一輪 | 空跑,無提示 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:66-84` | 中 |

### E15 迴圈遇壞列 `break`

**本片沒有找到這個樣式。** 76 處 `break` 全部是 `switch` 的 `break` 或帶條件的正常提早離開,沒有「`catch` 裡 `break` 把後面整批吃掉」那種(BMS / CRM / DSM / TMK 中過的)。逐處確認方式:`grep -n '^\s*break\s*;'` 之後看上一個非空白行是不是 `catch` 區塊結尾。

### E16 `=` 對 `<=` 導致漏跑一天

**本片沒有找到。** 三支服務的時間比對用的是字串相等 `sTIMES == DateTime.Now.ToString("HHmm")`,不是日期區間比較 —— 但這帶來另一個問題:**如果服務在那一分鐘正好在忙(前一輪還沒跑完),這一次排程就整個錯過,不會補跑**。`_timer_Elapsed` 沒有重入保護,`System.Timers.Timer` 預設會在 ThreadPool 上重入,所以更可能的是**同時跑兩輪**。這兩種行為都沒有被處理。錨點 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:65-75`(三支同款)。

### E17 `AND` / `OR` 缺括號

**本片沒有找到。** 但有一處 `&` 當邏輯 AND 用(非短路):`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB609_Ctl.cs:62`。兩邊都是 `bool` 所以結果正確,只是寫法不一致。

### E18 多套實作並存

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM607` 有兩份活的 PO(`MSSQL/OFDM607_PO.cs` 與 `Oracle/OFDM607OracleDao.cs`),都寫 `UPDATE OFD607A SET PROCESS_YN='Y'` | 改一份不會同步另一份;實際生效的是 Oracle 那份(介面實作方) | `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM607_PO.cs:213` 對 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM607OracleDao.cs:194-198` | 中 |
| `OFDM681OracleDao` 宣告實作 **`IOFDM680`** 不是 `IOFDM681` | 未編譯所以編譯器不抱怨;要復活這支畫面第一個會爆的就是這裡 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM681OracleDao.cs:15` | 中 |
| 16 支畫面有 `Model.xsd` 與 `_9iModel.xsd` 雙份 schema | 改欄位要改兩份;程式只用 `_9i` 那份,改錯那份不會編譯失敗也不會生效 | 例:`Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB601Model.xsd` 與 `OFDB601_9iModel.xsd` | 中 |
| `OFDB609_Service` 的三行 Remoting 初始化在 `Start()` 與 `OnStart()` 各寫一次;`OFDB680_Service` 同款 | `architecture.md §8` 已記 | `OFDB609_Service.cs:40-42` 與 `:54-56`;`OFDB680_Service.cs:42-44` 與 `:138-140` | 低 |

### E19 設定與程式不一致

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDB680_Service` 程式碼是 Remoting 客戶端寫法,`App.config` **沒有 `<system.runtime.remoting>` 區段** | 服務實際在本機行程直打資料庫,部署需求跟另外兩支完全不同(§6.4)。`architecture.md §8` 的「三支 `OFDB*` 都是 Remoting 客戶端」對這支要修正 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs:42` 對該目錄的 `App.config`(385 行,零 remoting) | **高** |
| 三支服務的 `ExceptionHandlingMode` 都被註解掉 | 走 EL 還是 Fusion 由部署機決定 | `WindowsService.OFDB600/App.config:198`(三支同行號) | 低 |
| `Environment.UserName == "SYSTEM"` 決定服務模式 | `architecture.md §8` 已記的雷:同一個 exe 雙擊會走 UI 分支;而且以 gMSA 或網域帳號跑服務時 `UserName` 不是 `SYSTEM`,**服務會走 Console 分支並在 `Console.ReadLine()` 卡住** | `WindowsService.OFDB600/Program.cs:28`、`WindowsService.OFDB609/Program.cs:18`、`WindowsService.OFDB680/Program.cs:14` | **高** |

### E20 掃描與統計會被誤導的四個地方

| 誤導 | 正確做法 |
|---|---|
| `grep MasterTable` 撈到一堆註解行 | 先剝 `//` 開頭的行 |
| `grep -rn ECAdapter` 看起來有四個呼叫端 | 其中一個在 `/* */` 區塊註解裡(`OFDB691_Ctl`),兩個在未編譯的檔裡 |
| 檔案存在就當作畫面存在 | **要比對四個 csproj 的 `<Compile Include>`**(§0.4)—— 這是 `architecture.md 附錄 D` 之外新增的一條 |
| `atlas_scan.py --screen` 說「PO 缺」 | 本片 PO 叫 `*OracleDao.cs`,再找一次 |

---

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `Dev/ATLAS.EC/` 的 50 支畫面(28 B 加 22 M)與三支 WindowsService。修正 `architecture.md §8` 對 `OFDB680_Service` 的 Remoting 描述(§6.4);修正「48 支無主檔」的統計(§0.3);新增「八支畫面整組未編譯」的發現(§0.4);從 EC 側補完 `bms.md §8` 的 `OFD601` / `OFD607A` 擁有權(§8.1);從 EC 側補上 `rsp.md §8` 漏記的 `RSP006A` 第三個寫入者(§8.2)。 |

由 build_doc.py v2.0.0 於 2026-09-15 11:53 產生 · 標題 108 · 圖 5 · 表格 104 · 程式錨點 312 · § 連結 137 · 引用檢查：畫面 52（缺 0） · Table 27（缺 0） · Report 2（缺 0） · 結果集 35（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
