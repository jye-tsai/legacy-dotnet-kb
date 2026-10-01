ATLAS 知識庫 — 12-模組-EC-MISC-RSP-NFDR

本檔合併以下文件:modules/ec.md、modules/misc.md、modules/rsp.md、modules/nfdr1.md、modules/nfdr2.md


============================================================
【文件】kb/modules/ec.md
============================================================

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

============================================================
【文件】kb/modules/misc.md
============================================================

# ATLAS MISC 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這一片最反直覺的事)、各畫面節末的卡控總表、附錄 E(踩雷)。

> ⚠ **這不是一個模組,是四個小模組加一組寄生畫面的收尾片。**21 支畫面橫跨 `TRP` / `OTA` / `FSK` / `IJP` 四個畫面代號前綴,再加 11 支代號是 `OFD` 但住在 `ATLAS.OTA` 專案的維護畫面;型別 M / I / R 都有。所以本文沒有單一的「業務主線」,§0 是四份邊界說明並排。 ⚠ **業務意義全部由表名、`msdata:Caption`、彈出視窗標題與報表中文名反推**,選單表不在版控。手法沿用 `cas.md §0`。四個前綴的字母展開在 repo 內都查不到定義,本文一律用業務描述,**不造官方名稱**。 ⚠ **〔客戶特定〕**:傳檔落地路徑、媒體代號 `TTP12A`、信件代碼 `07`、`WebUser%` 這類值是本站台的,換站一定要重新確認。 ⚠ **〔共用〕**:`FSK005`、`BMS999`、`OFD220` / `OFD221`、`OFD302` 這幾張表同時服務其他模組(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別與 R 的七層看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 四個模組各管什麼(推測)

| 前綴 | 支數(本片) | 管什麼(推測) | 反推依據 |
|---|---|---|---|
| `TRP` | 6(M×4 / I×1 / R×1) | **境外基金對集保申報平台的傳檔與收檔**:把 TA 的資料依規格產成媒體檔送出、把對方回來的媒體檔收進來,保存傳收檔紀錄,並維護境外基金月報 | 控件標題「申報平台種類」「週期」「傳檔存放路徑」「收檔媒體格式」;彈出視窗標題「集保傳檔錯誤資料顯示」「集保收檔錯誤資料顯示」;`TRP011` 欄位是「月報年月」「基金投資大陸地區證券市埸有價證券比率%」 |
| `OTA` | 2(M×1 / R×1) | **境外基金交易平台的雜項**:報表行銷說明代碼維護、弱勢族群交易回訪報表 | 控件標題「報表行銷說明代碼」;報表中文名「弱勢族群交易回訪報表(境外)」 |
| `FSK` | 1(M×1) | **證券經紀商(券商)基本資料維護** | 控件標題「券商代碼」「券商中文名稱」「總券商代碼」「券商類別」;PO 內註解「新增證券經紀商基本資料」 |
| `IJP` | 1(R×1) | **網路交易約定書列印**,是 `IPJ` 的錯字,見 §0.4 | 報表選項「全方位理財約定書」「查詢戶約定書」「舊戶轉查詢戶約定書」 |
| `OFD`(住 `ATLAS.OTA`) | 11(M×11) | **境外基金綜合帳戶軌的申購 / 買回 / 定期定額 / 配息 / 淨值 / 授權書維護**,與 `ATLAS.OFD` 的同名系列平行,見 §0.3 | `OMNIBUS_ID` 欄位、`GetSrIdNoForOTA` 取號函式、`S_OTA_*` 專屬 SP 命名空間 |

反推依據的錨點,逐條可查:

| 前綴 | 證據 | 出處 |
|---|---|---|
| `TRP` | 「申報平台種類」「週期」;彈窗「集保傳檔錯誤資料顯示」「集保收檔錯誤資料顯示」;「傳檔存放路徑」;「月報年月」「整批匯入」「月報製作」 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.designer.cs:283` 與 `:372`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001p0.designer.cs:179`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM101p0.designer.cs:179`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.designer.cs:527`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.designer.cs:385` 與 `:518-519` |
| `OTA` | 「報表行銷說明代碼」;報表名「弱勢族群交易回訪報表(境外)」 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.designer.cs:376`、`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:130` |
| `FSK` | 「券商代碼」「券商中文名稱」「總券商代碼」 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.Designer.cs:320`、`:362`、`:501` |
| `IJP` | 報表選項「全方位理財約定書」等五項 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:203-212` |
| `OFD`(OTA 軌) | 方法註解「取得有綜合帳戶交易幣別」+ SQL 條件 `OMNIBUS_ID = 'Y'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453` 與 `:463` |

### 0.2 這一片最反直覺的三件事

**(1)`TRP` 的商業規則不在程式裡,在資料表裡。**

`TRPM001`(傳檔)與 `TRPM101`(收檔)不自己組任何業務 SQL。它們去 `TRP001` 設定檔把**一整串 SQL 文字**讀出來,再送到伺服器執行。 `TRP001` 一列就有 `CHECK_SQL1` 到 `CHECK_SQL4`(檢核)、`SQL11` 到 `SQL14`(異動)、`SQL_OUT`(輸出),外加對應的 `Y/N` 開關與錯誤訊息文字 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582`)。伺服器端 `ExcuteSQLandLoadData` 只負責照收照跑 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:144-207`)。

**後果**:讀程式讀不出任何一條傳檔規則;要知道申報平台到底檢核什麼、寫哪張表,只能去 DB 撈 `TRP001`。收檔端更徹底,連 INSERT 語法都存在 `TR202.INSERTSQL` 欄位裡(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:858-893`)。

**(2)11 支 `OFDM*` 不是「OTA 借用 OFD 的畫面」,是同一件事的第二條帳務軌。**

`ATLAS.OFD` 的 `OFDM221A` 寫 `OFD220A` 與 `OFD221A`;`ATLAS.OTA` 的 `OFDM221C` 寫 `OFD220` 與 `OFD221`。 **表名差一個 `A`,是兩組不同的實體表**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-68` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:81-84`)。詳見 §8.1。

**(3)四支畫面走的是不同世代的資料存取,其中一支已經是死的。**

`FSKM004_PO` 繼承 `BasicEVAPO`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29`),依 `architecture.md §3` 的結論,這條路徑的 `dbTA` 從沒被賦值,**連按查詢都會 NRE**。同一支的 1,272 行裡有 950 行是被註解包起來的上一代實作(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270`)。

### 0.3 十一支 `OFDM*` 的歸屬問題

問題是:代號前三碼是 `OFD`,專案卻是 `ATLAS.OTA`。三個查證結果:

| 查證 | 結果 | 依據 |
|---|---|---|
| (a) 同代號是否也存在於 `ATLAS.OFD` / `ATLAS.OFDB` / `ATLAS.OFDI` / `ATLAS.EC`? | **11 支全部沒有同代號分身。**與 `ofdb3.md` 查到的 `OFDB562` 到 `OFDB564` 兩處各一份六層完全不同 | 全庫搜這 11 個代號,命中只在 `Dev/ATLAS.OTA/` 底下 |
| (b) 是不是「OTA 專用的 OFD 畫面」? | **是,而且分家方式是「代號加後綴 + 表名去掉 A」。**帶後綴的四支都能在 `ATLAS.OFD` 或 `ATLAS.EC` 找到姊妹畫面 | 見下表 |
| (c) 兩軌怎麼區分? | 靠 `OMNIBUS_ID` 欄位與專屬取號 `GetSrIdNoForOTA` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:164`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:463` |

後綴四支與姊妹畫面對照:

| 本片畫面(專案 `ATLAS.OTA`) | 主檔 | 姊妹畫面 | 姊妹的專案 | 姊妹的主檔 |
|---|---|---|---|---|
| `OFDM221C` | `OFD220` + `OFD221` | `OFDM221A` | `ATLAS.OFD` | `OFD220A` + `OFD221A` 再加六張明細 |
| `OFDM231B` | `OFD251` + `OFD252` `OFD253` `OFD254` | `OFDM231A` | `ATLAS.OFD` | `OFD251A` + `OFD252A` `OFD253A` `OFD254A` 再加七張明細 |
| `OFDM302B` | `OFD302` | `OFDM302` | `ATLAS.OFD` | `OFD302A` |
| `OFDM602A` | `OFD605` | `OFDM602` | `ATLAS.EC` | `OFD605`(**整個類別被註解掉,是死的**,`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19`) |

**`C` 後綴不是版本號,是第三個變體。**`ATLAS.OFD` 底下同時有 `OFDM221A` 與 `OFDM221B`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221B.cs`),`OFDM221C` 是第三支。 `OFDM221B` 只有 UI 一層,掃描器查不到它的六層。**假設**:它是 `OFDM221A` 的子視窗或殘留;依據是它不在畫面代號母體內、也沒有自己的 PO / Ctl / Entity。要確認得看 `OFDM221A` 是否在程式裡 new 它。

另外七支(`OFDM109` `OFDM111` `OFDM113` `OFDM251` `OFDM551` `OFDM554` `OFDM561`)**在全庫是唯一實作**,`ATLAS.OFD` 沒有同號畫面,也沒有帶 `A` 的姊妹表。也就是說:**綜合帳戶軌有一部分功能是 OFD 主軌沒有的**,不是單純複製。

### 0.4 `IJP` 對 `IPJ`:是打錯字,而且錯得很徹底

`architecture.md §9` 已經記錄「`IJPR611` 是打錯的畫面代號」。本片的補充查證:

| 查證 | 結果 |
|---|---|
| 錯字範圍 | **不是只錯在檔名,是七層全錯。**`IJPR611_Ctl.cs` / `IJPR611_Pxy.cs` / `IJPR611OracleDao.cs` / `IJPR611.cs` / `IJPR611_9iModel.xsd` / `IJPR611_9iView.xsd` / 七支 `.rpt`,連類別名 `IJPR611_Ctl`、介面名 `IIJPR611PO`、typed DataSet 的表名都是 `IJP` |
| 有沒有 `IPJR611`? | **沒有。**全庫零命中,所以不是兩支畫面,是同一支從頭錯到尾 |
| 同目錄的對照組 | 同一個 `ReportControl.EC` 裡有 `IPJR607_Ctl.cs` 與 `IPJR901_Ctl.cs`,拼法正確 |
| 專案與命名慣例 | 與 `IPJ` 完全一致:住 `ATLAS.EC*`、PO 叫 `<代號>OracleDao.cs`(`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:38`)、entity 帶 `_9i` 後綴、六層不齊 |
| 業務內容 | 電子交易的**約定書列印**,與 `IPJ` 的其他 15 支同一條線 |

**結論:是打錯字,不是兩個模組。**它跟 `IPJ` 共用專案、共用命名慣例、共用 `EC` 的表。修正要動七層的檔名、類別名、namespace、xsd 根節點名與七支 `.rpt` 的名稱,**不在本階段動,只記錄**。

### 0.5 使用角色(推測)

| 角色 | 用哪些畫面 | 依據 |
|---|---|---|
| 申報作業人員 | `TRPM001` 傳檔、`TRPM101` 收檔、`TRPI001` 查紀錄 | 三支的操作對象都是媒體檔與檔名,不是客戶資料 |
| 申報平台管理者 | `TRPM005` 路徑參數、`TRPM901` 月報 | 兩支都是設定或彙總,不處理個別交易 |
| 境外基金作業人員 | `OFDM109` `OFDM111` `OFDM113` `OFDM221C` `OFDM231B` `OFDM251` `OFDM551` `OFDM554` `OFDM561` `OFDM602A` | 全部是交易 / 契約 / 授權書單據維護,走完整四眼 |
| 淨值作業人員 | `OFDM302B` | 匯入淨值並鎖定,**不走四眼**(§4.11) |
| 代碼維護人員 | `OTAM901`、`FSKM004` | 兩支都是純代碼或基本資料檔 |
| 報表使用者 | `TRPR001`、`OTAR901`、`IJPR611` | 三支都只有查詢條件與輸出 |

**權限在哪?**`architecture.md §9` 說選單與權限表不在 repo。本片 21 支畫面裡**沒有任何一支在程式內做角色或權限判斷**。實測搜過 `UserID` / `EmpNo` / `Security` / `Permission` / `Role`,只在寫入稽核欄位時用到 `this.UserID` (例 `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:481`),沒有一處拿來做可視範圍或功能開關。

### 0.6 不管什麼

- **不管境外基金主檔本身。**`OFD062`(基金公司)、`OFD081`(基金)、`OFD068`(銷售機構)都是唯讀 join 進來的。

- **不管排程。**`TRP` 的傳收檔、`OFDM302B` 的淨值匯入全部是使用者按按鈕觸發,repo 內查不到對應的 WindowsService。

- **不管檔案傳輸本身。**`TRPM001` 只把 CSV 寫到本機或網路磁碟(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527`),真正送到集保是另一套工具或人工上傳。

- **本片無 B 型畫面**,原因見 §6。

### 0.7 全域開關

| 開關 | 位置 | 影響 |
|---|---|---|
| `TRP001.FILE_STYLE` | 資料表 | `'T'` 是傳檔、其他是收檔;`TRPM001` 硬鎖 `'T'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594`) |
| `TRP001.TRP_TYPE` | 資料表 | `TRPM001` 硬鎖 `IN ('A','T','R')`,程式註解寫「只處理境外種類」(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`) |
| `TRPARAMS.TRP_PARAMS` | 資料表 | 傳檔落地路徑,格式是 `TSCD_RPT_PATH=` 加路徑,由 `TRPM005` 維護、`TRPM001` 剝前綴使用(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192` 對照 `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356`) |
| `OFD302.NAV_LOCK` | 資料表 | 淨值鎖定碼,`OFDM302B` 依它決定能不能改(§4.11) |
| `OMNIBUS_ID` | 資料表欄位 | 分綜合帳戶軌與分戶軌,**但兩套代碼值並存**,見 §2.5 |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] MISC 全景:TRP 申報平台、11 支綜合帳戶軌 OFDM、OTA 自有 2 支、FSK 1 支、IJP 1 支,以及兩條跨塊呼叫
圖中文字:① TRP 集保申報平台(6 支,本片唯一完整 CRUD 鏈) / TRPM005 / 參數 TRPARAMS / TRPM001 / 傳檔 產 CSV / TRPM101 / 收檔 檢核入帳 / TRPI001 / 傳收檔紀錄查詢 / TRPM901 TRPR001 / 月報維護與報表 / ② ATLAS.OTA 裡的 11 支 OFDM(境外基金綜合帳戶軌) / OFDM109 OFDM111 OFDM561 / 授權書與扣款帳戶 / OFDM113 OFDM251 / 配息設定與公告 / OFDM221C / 申購 OFD220/221 / OFDM231B / 買回轉換 OFD251+3 / OFDM551 OFDM554 / 定期定額契約與變更 / OFDM302B / 淨值匯入與鎖定 繞四眼 / OFDM602A / 文件需求 OFD605 / OFD302 下游 / CLSR002 OFDI058 OFDB322… / ③ OTA 自有代號(2 支)與 FSK(1 支,死畫面) / OTAM901 / 報表行銷說明 BMS999 / OTAR901 / 弱勢族群回訪報表 / FSKM004 / BasicEVAPO 查詢即 NRE / FSK005 下游 / ucStkBrk 餵全庫下拉 / ④ IJP(1 支,是 IPJ 的錯字) / IJPR611 / 電子交易約定書 七式 / 畫面只選得到五式 / RPS6 RPS7 是死碼 / IPJR607 IPJR901 / 同目錄 拼法正確 / ⑤ 唯二的跨塊程式呼叫 / TRPM101 → OFDM053_PO / TTP12A 時寄信 代碼 07 / OFDM551 → S_OTA_OFDR552_GET / 維護畫面借報表的 SP / 其餘只靠表相連 / 沒有程式呼叫關係
```

*圖:圖 1 全景。橘框=本片的主要維護入口;橘虛框=繞過四眼、寫死值或已死的行為;灰虛框=本片以外的下游或對照組。四個模組各自獨立,只有標示的兩條線是真的程式呼叫。*

看圖的四個重點:

1. **四塊之間沒有程式呼叫關係,但有兩條真實的跨塊呼叫。** 第一條:`TRPM101`(收檔)在收到媒體代號 `TTP12A` 時,**直接 new 另一個模組的 PO** 去寄信 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687`,用的是 `OFDM053_PO.SEND_MAIL_PROC`)。第二條:`OFDM551`(定期定額契約)在畫面上叫報表用的 SP `S_OTA_OFDR552_GET` 取契約變更資料 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:509`)。除此之外各塊只靠表相連。

2. **11 支 `OFDM*` 自己構成一條完整的境外基金作業鏈**:開戶周邊(授權書 `OFDM109` / `OFDM111` / `OFDM561`)→ 配息設定(`OFDM113` / `OFDM251`)→ 申購(`OFDM221C`)→ 買回與轉換(`OFDM231B`)→ 定期定額(`OFDM551` / `OFDM554`)→ 淨值(`OFDM302B`)→ 文件需求(`OFDM602A`)。

3. **`TRP` 那條線是唯一一條完整 CRUD 鏈**(設定 → 傳 → 收 → 查 → 報),而且它同時是本片唯一「規則存在資料表裡」的一塊。

4. **`FSKM004` 是孤島而且是死的**,但它維護的 `FSK005` 被共用 PO 讀去餵全庫的券商下拉(§8.3)。

### 1.2 資料表關係

見 §2 節首的圖。要記住三件事:

- **主明細靠 `dataid` 綁定,不是外鍵**(`architecture.md §3`),所以主檔與明細一定一起送審、一起覆核。

- **`OFD220` / `OFD251` 這一組沒有 `A` 後綴,是綜合帳戶軌專用**;`ATLAS.OFD` 用的是同名加 `A` 的另一組表。兩組表結構相近但欄位數差很多(`OFD251` 152 欄、`OFDM231A` 的 `OFD251A` 另計)。

- **`TRP001` / `TR202` / `TR206` / `TR207` 這四張是「設定即程式」的表**,裡面存的是 SQL 文字、欄位對照與 SP 名稱,不是業務資料。它們不在任何一支 PO 的 `xTableMapping` 裡,所以掃描器不會把它們算成本片的實體表。

### 1.3 主要維護畫面的四眼與卡控順序

11 支 `OFDM*` 與 `TRPM005` / `TRPM901` / `OTAM901` 走標準四眼鏈,順序與 `cas.md §1` 描述一致:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼,從呼叫端反推) | 紅框加訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接叫 `_Pxy` 的 `befPostCheck`(只有 `OFDM221C` / `OFDM231B` 有) | 對話框 |
| 4 主檔欄位回填明細 | `SetMasterToDetail()` | 不會失敗,但漏欄位會讓明細主鍵是空的 |
| 5 PO 的 `BeforeAdd` 取號 | `GetTradeId` 取基金公司交易代碼再 `GetSrIdNoForOTA` 產書號 | 取不到 `TRADE_ID` 丟例外,整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `AfterAdd` / `AfterUpdate` | 只有 `OFDM221C` / `OFDM231B` 有,用來同步 `OFD113` 配息設定 | 例外 → 整筆回滾 |

**三支例外不走這條鏈**:

| 畫面 | 為什麼不走 |
|---|---|
| `TRPM001` / `TRPM101` | UI 基底是 `xOneStepProcessForm` 不是 `xMaintainForm`,PO 沒有基底類別、自建 `Database`,沒有四眼概念(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37`) |
| `OFDM302B` 的整批匯入 | `BatchAdd` 自己組 INSERT 並**直接把 `STATUS` 寫成 `'301'`、四眼六個 ID / DATE 一次填滿**,完全繞過引擎(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:208-209`) |
| `TRPM901` 的整批匯入 | 同樣是 `BatchAdd` 先 `DELETE` 再 `INSERT`,把四眼欄位當一般欄位寫(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282`) |

### 1.4 批次 / 報表資料流

本片**沒有 B 型畫面**(§6),所以「批次」全部是使用者按按鈕的一次性作業。三種形態:

| 形態 | 畫面 | 資料流 |
|---|---|---|
| 產檔 | `TRPM001` | 伺服器跑 `TRP001` 裡設定的 SQL 取出 CSV 列 → 回傳到用戶端 → 用戶端 `StreamWriter` 寫到本機路徑 → 回寫 `TRP002` 紀錄 |
| 收檔 | `TRPM101` | 用戶端讀檔案內容塞進 `CSVDATA` → 伺服器逐欄檢核 → 寫暫存表 → 叫 `TR207.UPDSTP` 指定的 SP 正式入帳 |
| 匯入 | `TRPM901`、`OFDM302B` | 用戶端讀 Excel / 檔案 → 伺服器 `DELETE` 再 `INSERT`,不走四眼 |

報表三支都照 `architecture.md §6` 的兩條往返:`GetReportData` 取資料、`GetReportObject` 拿 `.rpt` 的 byte, 後者的類別名由用戶端傳進來,伺服器照單全收(`Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/TRPR001_Ctl.cs:61-62`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,以下是**推測**的順序,依據是資料相依。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期 | 申報平台管理者 | 設定各申報種類 / 週期的傳檔落地路徑 | `TRPM005` | `TRP001` 要先有該種類的設定列 |
| 平時 | 境外基金作業 | 建立受益人的匯款授權書、扣款帳戶 | `OFDM109` `OFDM111` `OFDM561` | 受益人要先在 `BMS001A` 存在 |
| 平時 | 境外基金作業 | 設定配息方式與再投資基金 | `OFDM113` `OFDM251` | 基金要先在 `OFD081` / `OFD086` 存在 |
| 交易日 | 境外基金作業 | 申購、買回、轉換單據 | `OFDM221C` `OFDM231B` | `OFD081` 的最後交易日與 `OFD303` 的結帳狀態(§4.6、§4.7) |
| 交易日 | 境外基金作業 | 定期定額契約與契約變更 | `OFDM551` `OFDM554` | 契約要先有 `RSP_NO` |
| 每日淨值到齊後 | 淨值作業 | 匯入淨值、鎖定 | `OFDM302B` | 基金要在 `OFD081` |
| 每日 / 每週 / 每月 | 申報作業 | 依週期傳檔給集保 | `TRPM001` | `TRP002` 的上次傳檔日決定本次日期(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:541-556`) |
| 收到回檔後 | 申報作業 | 收檔、檢核、轉入 | `TRPM101` | 媒體格式要在 `TR206` / `TR202` / `TR207` 設定好 |
| 隨時 | 申報作業 | 查傳收檔紀錄 | `TRPI001` | — |
| 月結 | 申報平台管理者 | 產月報、出月報報表 | `TRPM901` → `TRPR001` | `TRP011` 要先有資料 |

**假設**:傳檔週期由 `TRP001.PERIOD` 決定(`'M'` 為月、其他為日),依據是 `TRPM001` 對 `'M'` 走 `ADD_MONTHS` 推下一個年月、其他走 `TA_GETBUSINESSDAY` 推下一個營業日 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:549-556`)。實際有哪些週期值要查 DB。

## 2. 資料模型

```text
[圖] MISC 的資料表:TRP 的設定表、綜合帳戶軌的主明細、兩軌表名差一個 A,以及唯讀 join 的外部表
圖中文字:TRP:四張「設定即程式」的表 + 兩張資料表 / TRP001 / 存 13 欄 SQL 文字 / TR202 TR206 TR207 / 收檔 SQL 欄位對照 SP 名 / TRP002 / 傳檔紀錄 / TRPARAMS / 落地路徑 主檔 / TRP011 / 月報 主檔 / 綜合帳戶軌:主明細靠 dataid 綁定,不是外鍵 / OFD109 → OFD110 / 授權書 匯款帳戶 / OFD111 → OFD112 / 授權書 期間 / OFD561 → OFD562 / 扣款授權 扣款帳戶 / OFD551 → OFD552 / 定期定額契約 / OFD554 → OFD555 / 契約變更 / OFD220 → OFD221 / 申購書 39 欄 / OFD251 → OFD252 253 254 / 買回書 152 欄 / OFD113 OFD281 OFD302 OFD605 / 單表主檔四張 / 兩軌對照:ATLAS.OFD 的表多一個 A / OFD220 OFD221 / OTA 綜合帳戶軌 / OFD220A OFD221A / OFD 分戶軌 / OFD251…254 / OTA 軌 / OFD251A…254A / OFD 軌 / 跨模組借用與唯讀 join / BMS999 FSK005 / 表名前綴與歸屬無關 / OFD062 OFD081 OFD303 / 基金公司 基金 結帳控制 / BMS001A OFD601 / TRPM101 寄信名單 / 14 張 TTPxxxTMP / 表名執行期才決定
```

*圖:圖 2 資料模型。橘框=本片維護的主檔;橘虛框=內容是 SQL 文字而不是業務資料的設定表;灰虛框=另一軌或別模組的表;黑框=唯讀 join 或名字在程式裡看不到的表。箭頭=主明細(同一次四眼一起送審);細線=弱關聯。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

| 畫面 | 主檔 | 明細 | 宣告錨點 |
|---|---|---|---|
| `TRPM001` | —(不宣告) | — | PO 沒有 `xTableMapping`,自己組 SQL:`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37` |
| `TRPM005` | `TRPARAMS` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:66` |
| `TRPM101` | —(不宣告) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:42` |
| `TRPM901` | `TRP011`(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:65` |
| `TRPI001` | —(裸 DAO) | — | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:32-34` |
| `TRPR001` | —(SP 結果集) | — | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:31-33` |
| `OTAM901` | `BMS999`〔共用〕 | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:66` |
| `OTAR901` | —(SP 結果集) | — | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OTAR901_PO.cs:24-26` |
| `FSKM004` | `FSK005`〔共用〕 | — | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:39`(舊世代 `TableMapping`,不是 `xTableMapping`) |
| `IJPR611` | —(SP 與長 SQL) | — | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:38` |
| `OFDM109` | `OFD109` | `OFD110` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:78` 與 `:81` |
| `OFDM111` | `OFD111` | `OFD112` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:71` 與 `:74` |
| `OFDM113` | `OFD113` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:69` |
| `OFDM221C` | `OFD220`〔共用〕 | `OFD221`〔共用〕 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:81` 與 `:84` |
| `OFDM231B` | `OFD251` | `OFD252` `OFD253` `OFD254` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:84`、`:87`、`:89`、`:91` |
| `OFDM251` | `OFD281` | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:64` |
| `OFDM302B` | `OFD302`〔共用〕(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:47` |
| `OFDM551` | `OFD551` | `OFD552` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:73` 與 `:76` |
| `OFDM554` | `OFD554` | `OFD555` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:91` 與 `:94` |
| `OFDM561` | `OFD561` | `OFD562` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM561_PO.cs:72` 與 `:75` |
| `OFDM602A` | `OFD605`(多筆) | — | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:68` |

**注意兩個代號與表名對不上的地方**,讀碼時最容易找錯表:

| 畫面 | 直覺會找的表 | 實際的表 |
|---|---|---|
| `OFDM251` | `OFD251` | **`OFD281`**(`OFD251` 是 `OFDM231B` 的主檔) |
| `OFDM602A` | `OFD602` | **`OFD605`** |

### 2.2 主鍵與四眼欄位

本片 12 張實體表**全部帶四眼欄位**(掃描器實測「四眼欄位 有」)。主鍵從 xsd 的 `msdata:Caption` 與 SQL 條件反推:

| 表 | 主鍵(反推) | 欄位數 | 誰維護 |
|---|---|---|---|
| `TRPARAMS` | `TRP_TYPE` + `PERIOD` | 21 | `TRPM005` |
| `TRP011` | `CAL_YM` + `FH_CD` + `FUND_ID` | 36 | `TRPM901` |
| `BMS999` | `ST_CD` | 18 | `OTAM901` |
| `FSK005` | `STK_BRK` | —(xsd 未列出中文名) | `FSKM004`(已死) |
| `OFD109` | `REMIT_CFM_NO` | 23 | `OFDM109` |
| `OFD110` | `REMIT_CFM_NO` + `DATA_SEQ` | — | `OFDM109` 明細 |
| `OFD111` | `REMIT_CFM_NO` | 22 | `OFDM111` |
| `OFD113` | `BF_NO` + `FUND_ID` + `OMNIBUS_ID` + `APPLY_DATE` + `ALLOT_NO` | 31 | `OFDM113`、`OFDM221C`、`OFDM231B` |
| `OFD220` | `ALLOT_NO` | 39 | `OFDM221C` |
| `OFD251` | `REDEM_NO` | **152** | `OFDM231B` |
| `OFD281` | `FUND_ID` + `RECORD_DATE` | 35 | `OFDM251` |
| `OFD302` | `FUND_ID` + `NAV_DATE` | 44 | `OFDM302B` |
| `OFD551` | `RSP_NO` | 44 | `OFDM551` |
| `OFD554` | `RSP_CHG_NO` | 40 | `OFDM554` |
| `OFD561` | `REMIT_CFM_NO` | 23 | `OFDM561` |
| `OFD605` | `REQ_DOC_KIND` + `DOC_CD` | 23 | `OFDM602A` |

`OFD251` 的 **152 欄**是全片最大的一張表,一筆買回單就把買回、轉換、沖銷、付款、代理人資料全塞在同一列。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列業務欄,四眼 13 欄與 `UPD_USER` / `UPD_DATE` / `UPD_TIME` 全表皆有、皆無 Caption,不重複列。

#### `TRPARAMS` — 申報平台參數(`TRPM005` 主檔)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `TRP_TYPE` | 申報平台種類 | 與 `TRP001.TRP_TYPE` 對應 |
| `PERIOD` | 週期 | `'M'` 為月 |
| `TRP_PARAMS` | 參數 | 實際存的是 `TSCD_RPT_PATH=` 加路徑字串 |

#### `TRP011` — 境外基金月報(`TRPM901` 主檔,36 欄)

| 欄位 | 中文名 |
|---|---|
| `CAL_YM` | 月報年月 |
| `FH_CD` / `FH_NM_SH_C` | 基金公司 / 基金公司名稱 |
| `FUND_ID` / `FUND_SH_NM` | 基金公司 / 基金簡稱(**`FUND_ID` 的 Caption 寫成「基金公司」,與 `FH_CD` 撞名,是 xsd 的筆誤**) |
| `FUND_QUO_AMT` / `FUND_QUO_DATE` | 基金規模 / 基金類股規模日期 |
| `GLOBAL_FUND_QUO_AMT` / `GLOBAL_FUND_QUO_DATE` / `GLOBAL_UNIT` | 基金規模 / 基金規模日期 / 已發行基金單位(股)數 |
| `CAL_RATE1` | 從事衍生性商品交易比率%(Caption 後面接「申報平台1.2版取消此欄位」) |
| `CAL_RATE2` | 基金投資組合投資在國內證券市埸比率% |
| `CAL_RATE3` | 基金投資大陸地區證券市埸有價證券比率% |
| `CAL_RATE4` | 基金投資H股及紅籌股比率% |
| `CAL_RATE5` / `CAL_RATE6` | 從事衍生性商品交易比率% 未沖銷多頭 / 空頭部位 |

`CAL_RATE1` 的 Caption 自己就寫了「申報平台1.2版取消此欄位」——**欄位還在、還會被寫,但申報規格已經不要它了**。

#### `BMS999` — 報表行銷說明(`OTAM901` 主檔,18 欄)

| 欄位 | 中文名 |
|---|---|
| `ST_CD` | 行銷說明代碼 |
| `ST_CD_NM` | 報表行銷說明 |
| `ST_MO` | 附註 |

畫面上的標籤寫「報表行銷說明代碼」,xsd 的 Caption 寫「行銷說明代碼」,兩邊不一致但無害。

#### `OFD109` / `OFD110` — 匯款授權書(`OFDM109`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `OFD109` | `REMIT_CFM_NO` / `BF_NO` / `BF_NAME` / `AUTO_NUM` / `ACC_MEMO` | 授權書編號 / 戶號 / 姓名 / 客戶流水號 / 附註 |
| `OFD110` | `DATA_SEQ` / `BANK_BRH` / `REMIT_ACC_NO` / `BANK_BRH_SHNM` | 資料流水號 / 金資代碼 / 匯款帳號 / 分行簡稱 |

`OFD109.ADU_TYPE` 是必填(不可空)但**沒有 Caption**,畫面上也查不到對應標籤,用途不明。

#### 其餘授權書與契約類(`OFDM111` / `OFDM561` / `OFDM551` / `OFDM554` / `OFDM602A`)

| 表 | 關鍵欄位 | 中文名 |
|---|---|---|
| `OFD111` / `OFD112` | `REMIT_CFM_NO` / `BF_NO` / `AUTHORIZE_DATE` / `EFFECTIVE_DATE` / `TERMINATE_DATE` / `FH_CD` | 授權書編號 / 戶號 / 授權申請日期 / 授權生效日期 / 授權終止日期 / 基金公司代碼 |
| `OFD561` / `OFD562` | `REMIT_CFM_NO` / `BF_NO` / `AUTHORIZE_DATE` / `ACC_NO_TYPE` / `SUB_BANK_CODE` | 授權書號 / 受益人戶號 / 授權申請日 / 帳戶種類 / 扣款行 |
| `OFD551` / `OFD552` | `RSP_NO` / `RCV_DATE` / `TDCC_BF_NO` / `AGENT_ID` / `AGENT_CODE` / `CHANNEL_CD` / `STOP_ID` | 定期定額契約書號 / 收件日期 / 集保帳號 / 銷售機構區別碼 / 銷售機構代碼 / 通路區分碼 / 停扣註記 |
| `OFD554` / `OFD555` | `RSP_CHG_NO` / `RSP_NO` / `RSP_CHG_DATE` / `CHG_EFFECT_DATE` | 契約變更書號 / 契約書號 / 異動收件日期 / 變更生效日期 |
| `OFD605` | `REQ_DOC_KIND` / `DOC_CD` / `DOC_CD_DESC` / `NECESSARY_YN` / `SEAL_YN` | 文件需求種類 / 文件代碼 / 文件名稱 / 是否為必須要文件 / 是否需要核印 |

**`OFD109` 與 `OFD561` 的 Caption 只差一個字**(「授權書編號」對「授權書號」),欄位名完全相同,是兩張不同的表。看到 `REMIT_CFM_NO` 要先確認在講哪一張。

#### 三張交易與行情表(`OFDM221C` / `OFDM231B` / `OFDM251` / `OFDM302B`)

| 表 | 關鍵欄位 | 中文名 |
|---|---|---|
| `OFD220` / `OFD221`(申購,主檔 39 欄) | `ALLOT_NO` / `FH_CD` / `FH_NM_SH_C` / `OMNIBUS_ID` / `CRNCY_CD` / `ALLOT_PROC_CODE` | 申購書號 / 境外基金公司代碼 / 基金公司中文簡稱 / 綜合帳戶註記 / 交易幣別 / 申購處理代碼(`'D'` 為作廢,見 §4.6) |
| `OFD251` 到 `OFD254`(買回,主檔 **152 欄**) | `REDEM_NO` / `REDEM_TYPE` / `RCV_DATE` / `REDEM_DATE` / `REDEM_NAV_DATE` / `BF_NO` / `ID_NO` / `BF_NAME` / `AGENT_ID` | 買回書號 / 買回方式 / 收件日期 / 買回日期 / 買回淨值日期 / 戶號 / 受益人ID / 受益人姓名 / 銷售機區別碼(Caption 少一個「構」字) |
| `OFD281`(配息公告,35 欄) | `FUND_ID` / `FUND_SH_NM` / `RECORD_DATE` / `LAST_CALL_DATE` / `DIVIDEND_DATE` / `RD_POST_DATE` / `PAY_DATE` / `DIVIDEND_TYPE` / `PER_SHARE_CASH` | 基金代碼 / 基金中文簡稱 / 基準日 / 最後交易日期 / 配息日期 / RD入帳日期 / 發放日期 / 受益分配方式代碼 / 每單位數配現 |
| `OFD302`(淨值,44 欄) | `FUND_ID` / `NAV_DATE` / `BID_NAV` / `OFFER_NAV` / `NAV_B` / `NAV_LOCK` / `FUND_QUO_AMT` / `IsCheck` | 基金代碼 / 淨值日期 / 申購淨值 / 贖回淨值 / 正式淨值 / 淨值鎖定碼 / 基金規模 / 勾選(**不是實體欄位,是 SQL 裡 `SELECT 'True' AS IsCheck` 產出來的畫面欄**) |

`OFD251` 的 152 欄是全片最大的一張表,一筆買回單就把買回、轉換、沖銷、付款、代理人資料全塞在同一列。明細三張的用途來自 PO 的 region 名稱:`OFD252` 基金贖回付款檔、`OFD253` 轉換、`OFD254` 基金贖回銷售沖銷檔 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:315`、`:438`、`:584`)。 **注意 `:315` 與 `:438` 兩個 region 的標題都寫「基金贖回付款檔(OFD252)」**,但 `:438` 那段組的是 `OFD253` 的 SQL(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:580`)——複製貼上沒改標題。

### 2.4 與其他模組共用的表

| 表 | 本片誰動它 | 別的模組誰動它 | 風險 |
|---|---|---|---|
| `FSK005` | `FSKM004`(已死) | 共用 PO `BasicFSK_PO.GetStkBrkData` 唯讀(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117-139`),餵 `ucStkBrk` / `ucSTK_BRK_GRP` 等控件 | 維護入口是死的但下游一直在讀,§8.3 |
| `BMS999` | `OTAM901` | 表名前綴是 `BMS`,**但全庫只有 `OTAM901` 碰它** | 命名誤導:看到 `BMS999` 會以為歸 BMS 模組 |
| `OFD220` / `OFD221` | `OFDM221C` 寫;`OFDM109` 讀(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:461`);`OFDM551` 讀(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434`) | 綜合帳戶軌內部共用 | 改欄位要一起看三支 |
| `OFD113` | `OFDM113` 是主維護;`OFDM221C` 與 `OFDM231B` 在 `AfterAdd` / `AfterUpdate` 直接寫它 | — | **三個入口寫同一張表**,§8.2 |
| `OFD302` | `OFDM302B` 寫 | `CLSR002`(結算報表)、`OFDI058` / `OFDI058B`、`OFDB322` / `OFDB323` / `OFDB722`、`OFDI011` 讀 | 淨值是結帳源頭,砍掉重建的風險見 §4.11 |
| `OFD562` | `OFDM561` 寫;`OFDM221C` / `OFDM551` / `OFDM554` 讀扣款帳戶 | — | — |
| `BMS001A` / `OFD601` | `TRPM101` 讀(寄信名單) | BMS / EC 模組維護 | `INNER JOIN` 對不到就靜默不寄信,§6 |

### 2.5 狀態碼(從程式反推,標來源)

#### `OMNIBUS_ID` — 同一個概念,兩套值域

這是本片最容易出錯的地方。

| 表 / 用法 | 值域 | 錨點 |
|---|---|---|
| `OFD221.OMNIBUS_ID`、`OFD081` 檢核參數 | `'Y'` / `'N'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001`;`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:463` |
| `OFD113.OMNIBUS_ID` | `'2'`(綜合)/ `'1'`(分戶) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:249` 的三元式 `(row.OMNIBUS_ID == "Y") ? "2" : "1"` |

也就是說 **`OFD113` 的 `OMNIBUS_ID` 跟 `OFD221` 的不是同一組值**,兩邊要靠 `OFDM221C_PO` 這一行轉換。漏掉這行(例如直接拿 `OFD221.OMNIBUS_ID` 去查 `OFD113`)就會查不到資料,而且不會報錯——`GetOFD113` 的 `catch` 是空的 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224`)。

#### `STATUS` — 本片出現的字面值

`architecture.md §3` 從全庫掃出的 `STATUS = '<x>'` 字面量是單字元,並**假設**那就是 `EVAStatusCode` 的值。本片給這個假設一個反例:`OFDM302B` 與 `TRPM901` 的整批匯入寫進去的是 **三碼的 `'301'`**。

| 值 | 出現處 | 語意(反推) |
|---|---|---|
| `'301'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:209`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282` | 已核准。同一個字面值在 `BMSM006` / `CRMB001` / `OFDB609` 的 INSERT 也用(例 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:726`),都是「直接寫成已生效」的場合 |

**假設**:`'301'` 就是 `EVAStatusCode.ApproveAdd` 的實際字面值,依據是四支不同模組都在「繞過四眼直接寫入」時用它。要確認得反編譯 `Vendor.Product.Utility.MappingCode` 或查 DB。

#### 其他從程式反推的旗標

| 欄位 | 值 | 語意 | 錨點 |
|---|---|---|---|
| `TRP001.FILE_STYLE` | `'T'` | 傳檔(相對於收檔) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594` |
| `TRP001.TRP_TYPE` | `'A'` `'T'` `'R'` | 境外種類,`'R'` 時畫面才顯示基金公司欄位 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:218-221` |
| `TRP001.PERIOD` | `'M'` | 月;其他值走營業日 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:226-229` |
| `TRP001.CSQL_YN1` 到 `CSQL_YN4`、`SQL_YN11` 到 `SQL_YN14`、`SQL_YN_OUT` | `'Y'` | 該段 SQL 要不要跑 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:172-188` |
| `OFD221.ALLOT_PROC_CODE` | `'D'` | 作廢(查詢時排除) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |
| `OFD303.ALLOT_CTL_CODE` / `ALLOT_CTL_CODE_O` | `>= '2'` | 已處理到下單確認之後 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1036` 與 `:1043` |
| `OFD551.STOP_ID` | `'Y'` | 停扣 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| `IJPR611` 的 `PrintType` | `'0'` 到 `'6'` | 七種約定書,**畫面只給得出 `'0'` 到 `'4'`**,見 §7.3 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` |

## 3. 畫面清冊

```text
[圖] 21 支畫面依專案、型別、PO 基底三種分群,以及掃描器會誤判的四處
圖中文字:依專案分(5 個專案) / ATLAS.OTA(15) / TRP 4 + OTA 1 + OFD 10 / ATLAS.OTA.Report(2) / TRPR001 OTAR901 / ATLAS.OTA.Query(1) / TRPI001 / ATLAS.FSK(1) / FSKM004 只有它 / ATLAS.EC.Report(1) / IJPR611 / 依型別分:M 16 / I 1 / R 3 / B 0 / M 維護 16 支 / 其中 2 支行為其實是批次 / I 查詢 1 支 / TRPI001 裸 DAO / R 報表 3 支 / 七層 不是六層 / B 批次 0 支 / 批次能力寫進 M 裡 / 依 PO 基底分(剝註解後判定) / BaseEVADaoPO(11) / 現行主線 走完整四眼 / BaseMultiRowEVADaoPO(3) / TRPM901 OFDM302B OFDM602A / BasicEVAPO(1) / FSKM004 查詢即 NRE / 無基底 裸 DAO(6) / 自建 Database 自管交易 / 掃描器會誤判的三處 / TRPR001 報「缺 PO」 / 檔名少一個 R / OFDM113_PO.cs 是 cp950 / 全片唯一非 UTF-8 / 兩支 rpt 不在 csproj / OFDM302BRPS1 RPS2 / IJPR611 缺 model view / 實際是 _9i 後綴檔 / 在 csproj:21 支的六 / 七層全部都在,只有兩支 rpt 例外 / 21 支 × 六 / 七層 / 全部在 csproj / OFDM302BRPS1 RPS2 / 沒有 csproj 的資料夾 / UI 用名字去要它們 / OFDM302B.cs:342 :396
```

*圖:圖 3 清冊分群。橘框=主線;橘虛框=死路徑、誤判來源或會咬人的地方。判斷一支畫面死活的第一個依據是 PO 基底 —— 繼承 BasicEVAPO 的那一支,連按查詢都會 NRE。*

四欄要特別說明:

- **六層齊不齊**:掃描器的判定。「假缺」表示檔案在、只是檔名不照慣例,見註。

- **PO 基底**:判斷前**已剝掉 `//` 註解**(`atlas_scan.strip_cs_comments`),避免被註解行誤導。這是判斷一支畫面死活的第一個依據(`architecture.md §3`)。

- **在 csproj**:該畫面的六 / 七層檔案是否都被對應的 `.csproj` 以 `Compile` / `EmbeddedResource` 收錄。

- **專案與型別**:本片跨四個專案、三種型別,不看這欄會找錯檔。

### 3.1 維護 M(16 支)

| 代號 | 中文名(待選單表) | 專案 | 六層 | 主表 | 明細 | SP / Fn | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|---|
| `TRPM001` | 集保申報平台傳檔 | `ATLAS.OTA` | 齊 | —(`TRP001` 設定驅動) | — | — | **無基底**(`ITRPM001_PO`,自建 `Database`) | 是 |
| `TRPM005` | 申報平台參數維護 | `ATLAS.OTA` | 齊 | `TRPARAMS` | — | — | `BaseEVADaoPO` | 是 |
| `TRPM101` | 集保申報平台收檔 | `ATLAS.OTA` | 齊 | —(`TRP001`/`TR202`/`TR206`/`TR207` 設定驅動) | — | `S_OTA_<表名>_GET`(動態組名) | **無基底**(`ITRPM101_PO`,自建 `Database`) | 是 |
| `TRPM901` | 境外基金月報維護 | `ATLAS.OTA` | 齊 | `TRP011` | — | `S_OTA_TRPM901_EXE` | `BaseMultiRowEVADaoPO` | 是 |
| `OTAM901` | 報表行銷說明代碼維護 | `ATLAS.OTA` | 齊 | `BMS999` | — | — | `BaseEVADaoPO` | 是 |
| `FSKM004` | 證券經紀商基本資料維護 | `ATLAS.FSK` | 齊 | `FSK005` | — | — | **`BasicEVAPO`**(死路徑) | 是 |
| `OFDM109` | 匯款授權書維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD109` | `OFD110` | — | `BaseEVADaoPO` | 是 |
| `OFDM111` | 授權期間維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD111` | `OFD112` | view `FNDV01` | `BaseEVADaoPO` | 是 |
| `OFDM113` | 受益人基金配息設定維護 | `ATLAS.OTA` | 齊 | `OFD113` | — | — | `BaseEVADaoPO` | 是(**來源檔是 cp950,非 UTF-8**) |
| `OFDM221C` | 境外基金申購維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD220` | `OFD221` | — | `BaseEVADaoPO` | 是 |
| `OFDM231B` | 境外基金買回 / 轉換維護(綜合帳戶) | `ATLAS.OTA` | 齊 | `OFD251` | `OFD252` `OFD253` `OFD254` | `S_OTA_OFDM231B_EXE_ADD` `S_OTA_OFDM231B_EXE_MOD` `S_TA_IMP_OFD300_RANGE` | `BaseEVADaoPO` | 是 |
| `OFDM251` | 基金配息公告維護 | `ATLAS.OTA` | 齊 | `OFD281` | — | — | `BaseEVADaoPO` | 是 |
| `OFDM302B` | 境外基金淨值維護與鎖定 | `ATLAS.OTA` | 齊 | `OFD302` | — | — | `BaseMultiRowEVADaoPO` | 六層是;**兩支 `.rpt` 不在任何 csproj**,見註 2 |
| `OFDM551` | 定期定額契約維護 | `ATLAS.OTA` | 齊 | `OFD551` | `OFD552` | `S_OTA_OFDR552_GET` | `BaseEVADaoPO` | 是 |
| `OFDM554` | 定期定額契約變更維護 | `ATLAS.OTA` | 齊 | `OFD554` | `OFD555` | — | `BaseEVADaoPO` | 是 |
| `OFDM561` | 扣款授權書維護 | `ATLAS.OTA` | 齊 | `OFD561` | `OFD562` | — | `BaseEVADaoPO` | 是 |
| `OFDM602A` | 文件需求設定維護 | `ATLAS.OTA` | 齊 | `OFD605` | — | — | `BaseMultiRowEVADaoPO` | 是 |

### 3.2 查詢 I(1 支)

| 代號 | 中文名(待選單表) | 專案 | 六層 | 主表 | SP / Fn | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `TRPI001` | 集保傳收檔紀錄查詢 | `ATLAS.OTA.Query` | 齊 | —(`TRP002` + `TRP001`) | — | **無基底**(`ITRPI001_PO`,自建 `Database`) | 是 |

`TRPI001` 的 PO 檔名是 `TRPI001_PO.cs`,**不是** `.Query` 專案常見的 `<代號>OracleDao.cs`(`architecture.md §2` 列的例外之一)。另外層資料夾叫 `QueryPO.OFD` / `QueryUI.OFD`(前綴是 `OFD`),組件名卻是 `QueryPO.OTA`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/QueryPO.OTA.csproj`)——資料夾名與專案名不一致,是 `architecture.md §2` 記的第 3 類例外。

### 3.3 批次 B(0 支)

本片沒有 B 型畫面,原因見 §6。

### 3.4 報表 R(3 支,七層)

R 是七層不是六層(`architecture.md §6`):六層各自加 `Report` 前綴,再多一個 `Report.<模組>` 專案放 `.rpt`。

| 代號 | 中文名(來自程式字串) | 專案 | 七層 | 取數來源 | `.rpt` | PO 基底 | 在 csproj |
|---|---|---|---|---|---|---|---|
| `TRPR001` | 境外基金月報 | `ATLAS.OTA.Report` | **掃描器報「PO 缺」,實際是檔名錯**,見註 1 | `S_OTA_TRPR001_GET` | `TRPR001RPS1.rpt` | **無基底**(`ITRPR001_PO`,自建 `Database`) | 是(以錯誤檔名收錄) |
| `OTAR901` | 弱勢族群交易回訪報表(境外) | `ATLAS.OTA.Report` | 齊 | `S_OTA_OTAR901_GET`(版控外) | `OTAR901RPS1.rpt` | **無基底**(`IOTAR901_PO`,自建 `Database`) | 是 |
| `IJPR611` | 電子交易約定書(七式) | `ATLAS.EC.Report` | 缺 `DataEntity` / `UIEntity` 的標準檔名(實際是 `_9i` 後綴檔) | Dao 內七段長 SQL | `IJPR611RPS1` 到 `IJPR611RPS7`,共 7 支 | **無基底**(`IIJPR611PO`,自建 `Database`) | 是 |

### 3.5 兩個「掃描器說缺、其實不缺」的註

**註 1:`TRPR001` 的 PO 檔名少了一個 `R`。**

`TRPR001_Ctl` 在 `:29` 與 `:36` 用 `TRPR001_PO` / `ITRPR001_PO`,而這個類別住在 **`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs`**(檔名 `TRP001_PO.cs`,類別 `TRPR001_PO`,`:31`)。檔頭的註解自己還寫著 `TRPR001_PO.cs`(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:2`),所以是存檔時打錯。 csproj 以錯的檔名收錄(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/ReportPO.OTA.csproj:141`), **C# 不在乎檔名,所以編得過、跑得動**,只有依檔名比對的工具(本專案的掃描器就是)會判它缺 PO。

**註 2:`OFDM302B` 有兩支 `.rpt` 躺在專案裡但不在任何 csproj。**

`Dev/ATLAS.OTA/Source/CrystalReports/OFDM302BRPS1.rpt` 與 `Dev/ATLAS.OTA/Source/CrystalReports/OFDM302BRPS2.rpt` 在一個**沒有 csproj 的資料夾**裡(`Dev/ATLAS.OTA/Source/CrystalReports/` 底下只有這兩個檔)。 `OFDM302B.cs` 卻用名字去要它們(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:342` 與 `:396`)。依 `architecture.md §6`,`.rpt` 的另一條交付路徑是 csproj 的 PostBuildEvent xcopy 到框架目錄—— 這兩支**兩條路徑都沒有**(既不是 `EmbeddedResource`,也沒有 xcopy)。 **推論:`OFDM302B` 的兩張報表在目前的建置流程下不會被部署,除非有人手動複製。**這是本片唯一的「檔案存在但不在 csproj」。

### 3.6 一眼看出差別的五件事

| # | 事實 | 為什麼重要 |
|---|---|---|
| 1 | **21 支裡有 6 支的 PO 沒有任何基底類別**(`TRPM001` `TRPM101` `TRPI001` `TRPR001` `OTAR901` `IJPR611`) | 它們自建 `Database`、自管交易,不受四眼、連線池與框架治理(與 `architecture.md §6` 對 I / B / R 的描述一致) |
| 2 | **只有 1 支繼承 `BasicEVAPO`**(`FSKM004`) | 依 `architecture.md §3` 是死路徑,連查詢都會 NRE |
| 3 | **3 支繼承 `BaseMultiRowEVADaoPO`**(`TRPM901` `OFDM302B` `OFDM602A`) | 多筆主檔、沒有明細概念;其中 `TRPM901` 與 `OFDM302B` 另外有繞過四眼的 `BatchAdd`,`OFDM602A` 沒有 |
| 4 | **11 支繼承 `BaseEVADaoPO`** | 現行主線,走完整四眼 |
| 5 | **21 支的六 / 七層檔案全部在 csproj 內**,唯一的例外是 `OFDM302B` 的兩支 `.rpt` | 與 `ofd` 系列前幾片查到的「整支畫面不在 csproj」不同,本片沒有那種情況 |

PO 基底的逐支對照與統計見附錄 D。

## 4. 維護畫面(M)— 一支一節

```text
[圖] TRP 六支的完整鏈:設定表驅動的傳檔與收檔、紀錄查詢、月報與報表
圖中文字:① 設定(規則不在程式裡,在這兩張表) / TRPM005 / 維護落地路徑 TRPARAMS / TRP001〔DB 維護〕 / CHECK_SQL1-4 SQL11-14 SQL_OUT / TR202 TR206 TR207 / 收檔 INSERT 語法與 SP 名 / ② 傳檔 TRPM001:檢核 → 產檔 → 記錄 / Select 取設定 / 硬鎖 TRP_TYPE A T R / Execute 跑 4 段檢核 SQL / 空 catch → 出錯視同無誤 / ExcuteSQLandLoadData / 跑異動 SQL + 取 CSV 列 / 用戶端 StreamWriter / Encoding.Default 每列多一個 tab / UpdateTRP002 / 只在筆數不為 0 時寫 / ③ 收檔 TRPM101:六道欄位檢核 → 暫存表 → SP 入帳 / GetTRP001 GetTR206 / 取媒體格式與欄位對照 / 逐欄六道檢核 / 未定義欄位在第 2 筆以後會炸 / TR202.INSERTSQL / 三層 REPLACE 反跳脫 / Execute 不帶 tran / rollback 收不回 / S_OTA_<表名>_GET / 14 支 由 TRP001 決定 / TR207.UPDSTP 入帳 / 名字在程式裡看不到 / TTP12A → OFDM053_PO / 寄信 代碼 07 兩個 INNER JOIN / ④ 查與報 / TRPI001 查 TRP002 / FILE_STYLE 送了沒用 / INNER JOIN TRP001 / 設定刪了歷史就消失 / TRPM901 月報 / BatchAdd 繞四眼 STATUS 301 / TRPR001 報表 / S_OTA_TRPR001_GET
```

*圖:圖 4 TRP CRUD 鏈。橘框=程式;橘虛框=規則存在資料表裡、或會咬人的實作;黑框=名字在執行期才決定的 SP。整條鏈最關鍵的一點:傳檔與收檔的商業規則都不在程式裡,讀 code 讀不出任何一條檢核。*

節首的圖見 §1.1 與 §3 的分群圖。深寫的六支是:`TRPM001` / `TRPM101`(本片唯一完整 CRUD 鏈的核心)、`FSKM004`(唯一死畫面)、 `OFDM221C` / `OFDM231B`(最重的兩支)、`OFDM302B`(唯一繞過四眼寫主檔的)。其餘表格帶過。

### 4.1 `TRPM001` — 集保申報平台傳檔

#### 用途(推測)

依申報平台種類與週期,把 TA 的資料依 `TRP001` 設定的 SQL 撈出來,逐筆組成一行 CSV, 寫到 `TRPARAMS` 設定的路徑,並把傳檔筆數記進 `TRP002`。

#### 這支畫面的型別是假的

代號第 4 碼是 `M`(維護),但 UI 繼承的是 `xOneStepProcessForm` (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:30`),那是 `architecture.md §6` 歸給 I / B 的基底; PO 沒有任何基底、自己 `new Database("TA", DbServerType.Oracle)`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:36-37`)。 **它的行為完全是 B 批次,只是掛了 M 的代號。**同樣的話適用 `TRPM101`。

#### 規則從哪來:`TRP001` 一列就是一支程式

`Select` 組的 SQL 把 `TRP001` 整列讀出來,包含 13 個 SQL 文字欄位 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582`):

| 欄位群 | 用途 | 誰執行 |
|---|---|---|
| `CSQL_YN1` 到 `CSQL_YN4` + `CHECK_SQL1` 到 `CHECK_SQL4` + `CHECK_MSG1` 到 `CHECK_MSG4` | 傳檔前檢核。SQL 查出有列就算「有錯」,把 `CHECK_MSGn` 顯示到畫面 | `Execute`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:435-506`) |
| `SQL_YN11` 到 `SQL_YN14` + `SQL11` 到 `SQL14` | 傳檔時要跑的異動 SQL(標記已傳等) | `ExcuteSQLandLoadData`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:144-207`) |
| `SQL_YN_OUT` + `SQL_OUT` | 產出 CSV 內容的 SELECT | `GetCSVData`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:217-286`) |
| `FILE_ID` / `FILE_NAME` / `MEDIA_NO` | 檔名與媒體代號 | UI 端組檔名 |

參數綁定是「掃字串決定要不要綁」:`if (strSQL.IndexOf(":TRANS_DATE") > 0) AddInParameter(...)` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:309-322`)。 **注意用的是 `> 0` 不是 `>= 0`**——如果哪天有人把 SQL 寫成以 `:TRANS_DATE` 開頭(索引 0),參數就不會綁,Oracle 直接丟「未繫結變數」。目前的寫法都有 `WHERE` 開頭所以踩不到,但這是一顆未爆彈。

#### 查詢:下一次該傳哪一天

`Select` 用 `TRP002` 的最後一次傳檔日推出本次日期(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:541-556`):

| `PERIOD` | 沒傳過 | 傳過 |
|---|---|---|
| `'M'` | `TO_CHAR(SYSDATE,'YYYYMM')` | 上次年月 `ADD_MONTHS(+1)` |
| 其他 | `TA_GETBUSINESSDAY(NULL, 1)` | `TA_GETBUSINESSDAY(上次日期, 1)` |

兩個寫死的硬條件:`TRP_TYPE IN ('A','T','R')`(`:547` 與 `:593`,註解寫「只處理境外種類」)與 `FILE_STYLE = 'T'`(`:594`)。 **過濾(無提示)**:`TRP001` 裡種類不在這三個值、或 `FILE_STYLE` 不是 `'T'` 的設定列,在這支畫面永遠看不到,也不會有任何訊息。

#### 執行:檢核 → 產檔 → 記錄

`DoProxyExecute` 的順序(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:290-339`):

1. 呼叫 `FormProxy.Execute` 跑伺服器端的四段檢核 SQL。

2. 只有在 `Result[0].ReturnCode == true` **且**回傳列數 > 0 時才往下走(`:311-313`)——**阻擋**。

3. `ConvertToCSV()` 逐列產檔(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:343-425`)。

4. 產檔成功開 `TRPM001p1` 顯示筆數;失敗把結果改成「執行失敗」。

檔名與路徑的組法(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356-380`):

| 項目 | 規則 | 備註 |
|---|---|---|
| 路徑 | `row.FILE_PATH.Replace("TSCD_RPT_PATH=", "")` | 值來自 `TRPARAMS`,由 `TRPM005` 維護 |
| 路徑預設 | 空字串時用 `C:\境外傳檔\` | **寫死**〔客戶特定〕(`:358-360`) |
| SQL 端預設 | `NVL(B.TRP_PARAMS, 'C:\')` | **第二個寫死的預設值,而且與 UI 端不同**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:584`) |
| 自動建資料夾 | `Directory.CreateDirectory` | 沒有例外處理以外的保護,建不出來就整批失敗 |
| 檔名 | `FILE_ID` + `_` + `FH_CD`(有才加)+ `_` + 傳檔日 | **沒有副檔名** |

寫檔本身(`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527-539`):

- `new StreamWriter(strFileName, false, Encoding.Default)` ——**用作業系統預設編碼**(繁中 Windows 是 CP950)。換一台 UTF-8 locale 的機器產出的檔就不一樣。〔客戶特定〕

- 每一列後面都多接一個定位字元:`sb.Append(dr["RowData"].ToString() + "\t")`(`:534`)。集保規格要不要這個 tab,程式裡看不出來。

- 逗號處理在伺服器端:除了 `RESERVE_FIELD_SW` 這個欄名以外,所有值裡的半形逗號都被換成全形(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:259-264`)。**欄名寫死在程式裡**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | `validatorManager1` 必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:138-141` |
| 查詢 SQL | `TRP_TYPE IN ('A','T','R')` 且 `FILE_STYLE='T'` | 不符 | **過濾(無提示)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593-594` |
| 查詢後 | 查無資料 | 0 筆 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:609` |
| 按執行前 | 傳檔日期不可空白 | 空 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:166-169` |
| 按執行前 | 至少勾一筆明細 | 全不勾 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:171-175` |
| 執行 | `TRP001` 設定的四段檢核 SQL 查出資料 | 有列 | **阻擋**(訊息寫到格子的 `CHECK_ERRMSGn` 欄) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:450-490` |
| 執行 | 檢核 SQL 本身出錯 | 例外 | **記錄不擋 → 實際上是放行**,見附錄 E.1 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:418-420` |
| 產檔 | `ExcuteSQLandLoadData` 回傳失敗 | `ReturnCode=false` | 阻擋(丟例外,被 `ConvertToCSV` 的 `catch` 轉成對話框) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:512-516` |
| 產檔 | 沒有 CSV 資料 | 0 列 | **記錄不擋**(回 0,該列標「無資料」,不寫 `TRP002`) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:518-523`、`:399-407` |
| 記錄 | `UpdateTRP002` 失敗 | `ReturnCode=false` | 阻擋(丟 `ArgumentNullException`) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:458-462` |

### 4.2 `TRPM101` — 集保申報平台收檔

#### 用途(推測)

把集保回來的媒體檔(逗號分隔文字)讀進畫面,依 `TRP001` / `TR206` 設定逐欄檢核格式, 通過的寫進暫存表,再叫 `TR207` 指定的 SP 正式入帳;`TTP12A` 這一種還會寄信給受益人。

#### 四張設定表各管什麼

| 表 | 取法 | 內容 |
|---|---|---|
| `TRP001` | `GetTRP001`(依 `MEDIA_NO`) | `CheckSQL`(欄位名與數量)、`StartLine`(資料從第幾行開始)、`NullFieldList`、`DateFieldList`、`TableName`(收檔媒體格式的表名) |
| `TR206` | `GetTR206`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:822-855`) | 寫入暫存檔的欄位對照 `TABLE_FIELD_NAME` 與 `IS_NUMBER` |
| `TR202` | `GetTR202`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:858-893`) | `INSERTSQL` —— **整段 INSERT 語法存在欄位裡**,取出時還要用三層 `REPLACE` 把 `'[` `]'` 拿掉、把 `&` 換成 `:` |
| `TR207` | `GetTR207`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:787-820`) | `QUERYSTP` / `UPDSTP` —— 查詢與入帳用的 SP 名稱 |

`REPLACE(REPLACE(REPLACE(TR202.INSERTSQL, CHR(39)||CHR(91), ''), CHR(93)||CHR(39), ''), CHR(38), ':')` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:868`)——SQL 被以某種跳脫格式存在表裡,取出時反轉。 **改這張表的人必須知道這套跳脫規則,程式裡沒有任何說明。**

另外表 schema 也是查出來的:`GetTableSchema` 去 Oracle 的資料字典取 `COLUMN_NAME` / `DATA_TYPE` / `DATA_LENGTH` / `DATA_SCALE` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:930-980`),再拿來判每一欄的長度與型別。

#### 逐欄檢核的六道

`Execute` 的主迴圈(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:216-368`):

| # | 檢核 | 成立時 |
|---|---|---|
| 1 | 欄位個數 = `CheckSQL` 查出的欄數 | 不等 → 記錯誤 |
| 2 | 欄名含 `DUMMY` → 整欄跳過 | — |
| 3 | 欄位要定義在收檔媒體格式表的 schema 內 | 沒定義 → 記錯誤(**只檢查第一筆**,見下) |
| 4 | 長度不得超過該欄的 `DATA_LENGTH`(有小數再加 1) | 超過 → 記錯誤 |
| 5 | `DATA_TYPE = 'NUMBER'` 的欄要能 `decimal.TryParse` | 不能 → 記錯誤 |
| 6 | 在 `DateFieldList` 內的欄要能解析成日期(先試 `yyyy/` 或 `yyyy-`,不行再用 `Substring` 切 `yyyy/mm/dd`) | 不能 → 記錯誤 |

**第 3 道有一個會炸的洞。**條件寫成 `if (Schemarow.Length == 0 && intRow == 1)` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:248`),`continue` 在 `if` 內(`:253`)。第 2 筆以後若出現未定義欄位,`Schemarow.Length == 0` 但 `intRow != 1`,程式直接往下走到 `Schemarow[0]["COLUMN_CNAME"]`(`:267`)→ `IndexOutOfRangeException`,被最外層的 `catch` 吃掉、只回「例外錯誤, 請檢查」(`:507-512`)。第 6 道的 `Substring(0,4)`/`(4,2)`/`(6,2)` 對長度不足 8 的字串也會直接丟例外(`:329`),同樣被吃成「例外錯誤」。

#### 寫暫存表與入帳

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 產一把 `Guid` 當 `ONLY_KEY` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:433` |
| 2 | 逐列用 `TR202.INSERTSQL` 寫暫存表,參數名就是 `TR206` 給的欄名 | `:442-467` |
| 3 | 叫 `S_OTA_<收檔表名>_GET` 取回正確 / 錯誤兩個結果集 | `:752-785` |
| 4 | (`ImportData` 才有)叫 `TR207.UPDSTP` 正式入帳,參數 `XDATALIST='DEF'`、`XONLY_KEY` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:659-665` |

**這裡有一個真的交易缺口。**`Execute` 在 `:435` 開了 `tran`,失敗時 `tran.Rollback()`, 但第 2 步的寫入用的是 `dbTA.ExecuteNonQuery(cmd)`——**沒有把 `tran` 傳進去**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459`)。對照 `ImportData` 的同一段是 `dbTA.ExecuteNonQuery(cmd, tran)`(`:646`)。也就是說 **`Execute` 寫進暫存表的資料不在交易內,rollback 收不回來**。

#### 寄信:跨模組、寫死兩個常數

`ImportData` 在媒體代號等於 `TTP12A` 時,`new` 一個 `OFDM053_PO` 去寄信 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687`):

| 寫死的值 | 位置 | 意義 |
|---|---|---|
| `"TTP12A"` | `:670` | 核印收檔的媒體代號〔客戶特定〕 |
| `"07"`(兩處) | `:683`(傳給 `SEND_MAIL_PROC`)與 `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:729`(SQL 的 `EMAIL_CODE_EC = '07'`) | 信件代碼〔客戶特定〕 |

名單 SQL 是 `TRPM101T1`(暫存表)`INNER JOIN BMS001A INNER JOIN OFD601`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729`)。 **兩個 `INNER JOIN` 表示只要受益人不在 `BMS001A` 或沒有 `OFD601` 的 `BF_SRNO`,這個人就不會收到信,而且沒有任何提示。** 更糟的是 `GetMailData` 的 `catch` 是空的(`:742-744`),SQL 出錯回 0,程式當成「沒人要寄」繼續往下 commit。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 收檔內容不可空 | 0 列 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:141-144` |
| 執行前 | 取得 `MEDIA_NO` | 空 | 阻擋 | `:146-152` |
| 執行前 | 取得 `TRP001` 設定 | 0 筆 | 阻擋 | `:159-165` |
| 執行前 | 取得檢核欄位(`CheckSQL`) | 0 欄 | 阻擋 | `:177-182` |
| 執行前 | 找得到收檔媒體格式的 schema | 0 筆 | 阻擋 | `:190-195` |
| 執行前 | 取得 `TR206` 欄位對照 | 0 筆 | 阻擋 | `:198-204` |
| 逐列 | 六道欄位檢核(見上) | 任一不過 | 阻擋(整批不寫) | `:212-368` |
| 逐列 | 未定義欄位出現在第 2 筆以後 | — | **例外**(訊息變成「例外錯誤, 請檢查」) | `:248` 配 `:267` |
| 寫入前 | 有可收的資料列 | 0 列 | 阻擋 | `:374-378` |
| 寫入前 | `TR202.INSERTSQL` / `TR207.QUERYSTP` 取得到 | 空 | 阻擋 | `:394-418` |
| 寫入 | 每列 `ExecuteNonQuery` 影響列數 | 0 | 阻擋 + rollback(**但寫入本身不在交易內**) | `:461-467` |
| 寫入後 | 例外 | 有 | **記錄不擋 → 被後面的 `if (i > 0)` 覆蓋成「檢核成功」**,見附錄 E.1 | `:478-484` 配 `:494-505` |
| 入帳 | 媒體代號 `TTP12A` | 是 | 記錄不擋(寄信) | `:669-687` |

### 4.3 `TRPM005` — 申報平台參數維護

`TRPARAMS` 的單表四眼維護,整支只有 180 行,是本片最單純的一支。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `TRPARAMS`(`TRP_TYPE` + `PERIOD`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:66` |
| 查詢硬條件 | `TRP_TYPE IN ('A','T','R')`,註解「只處理境外種類」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:141` |
| 顯示時剝前綴 | SQL 直接 `REPLACE(TRP_PARAMS, 'TSCD_RPT_PATH=', '')` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:137` |
| 存檔時加前綴 | `MasterRow.TRP_PARAMS = "TSCD_RPT_PATH=" + 輸入值` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192` |
| 自訂檢核 | **沒有**。`DoValidate()` 只叫框架的 `DataValidate()` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:143-148` |

**`TSCD_RPT_PATH=` 這個前綴在三個地方各寫一次**(PO 的 SELECT、UI 的存檔、`TRPM001` 的讀取), 三處任一改了字面值,另外兩處就對不上,而且不會報錯——`TRPM001` 只是 `Replace` 不到,拿到整串含前綴的字串當路徑,`Directory.CreateDirectory` 直接丟例外。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:108-119` 與 `:124-130` |
| 查詢 | `TRP_TYPE IN ('A','T','R')` | 不符 | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:141` |

### 4.4 `TRPM901` — 境外基金月報維護

`TRP011` 的多筆主檔維護,加兩個自訂鈕:「整批匯入」(`DoExp1` → `TRPM901p0`)與「月報製作」(`DoExp2` → `TRPM901p1`) (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:490-515`)。

| 功能 | 做什麼 | 錨點 |
|---|---|---|
| 查詢 | 依 `CAL_YM` + `FH_CD`;沒給 `CAL_YM` 時用 `MAX(CAL_YM) KEEP(DENSE_RANK FIRST ORDER BY ROWID DESC)` 取最後一期 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:83-104` |
| 取基金代碼 | 依 `ISIN_CODE` 查 `OFD081` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:206-245` |
| 整批匯入 | `BatchAdd`:先 `DELETE TRP011 WHERE CAL_YM=? AND FH_CD=?`,再逐列 INSERT,`STATUS` 寫死 `'301'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282` |
| 月報製作 | 叫 `S_OTA_TRPM901_EXE`,傳 `iFH_CD` / `iCAL_YM` / `iUPD_USER` / `iUPD_DATE` / `iUPD_TIME` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:355-367` |

三個要注意的地方:

1. **「不開放刪除」的檢核整段被註解。**`TRPM901_BeforeDeleteButtonClicked` 只剩註解,訊息字串「不開放刪除功能, 請使用修改方式調整資料庫」還在 (`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231`)。**現在刪除是開放的。**

2. **`BatchAdd` 的刪除檢核是死的。**`if (i == -1)` 判 `ExecuteNonQuery` 的回傳(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271`), 而 `ExecuteNonQuery` 回的是影響列數,**永遠不會是 -1**。刪 0 筆與刪 500 筆都會通過。

3. **整批匯入完全繞過四眼**:`STATUS='301'`、`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全部塞同一個 `:USERID`、同一個 `SYSDATE` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282`)。**一個人匯入等於一個人送審加覆核加核准。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:205-218` 與 `:233-246` |
| 刪除前 | (原本要擋刪除,**已被註解**) | — | **不擋** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231` |
| 整批匯入 | 刪除影響列數 `== -1` | 永不成立 | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271-276` |
| 整批匯入 | 每列 INSERT 影響列數 `== 0` | 是 | 阻擋 + rollback | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:312-318` |

### 4.5 `FSKM004` — 證券經紀商基本資料維護(**死畫面**)

#### 為什麼說它是死的

| # | 事實 | 錨點 |
|---|---|---|
| 1 | `FSKM004_PO : BasicEVAPO`(**剝掉註解後確認,活的宣告只有這一行**) | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29` |
| 2 | 依 `architecture.md §3`,`BasicEVAPO.dbTA` 宣告即 `= null`,建構子建立連線那四行整段被註解 | `architecture.md §3` |
| 3 | 本支的 `BeforeSelect` 第一件事就是 `dbTA.GetSqlStringCommand(strSQL)` | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:60` |
| 4 | `BeforeGetMaintainData` / `BeforeGetToDoData` 同樣第一行就用 `dbTA` | `:73` 與 `:85` |
| 5 | `CheckStkBrkData` / `CheckDelete` 一開頭就 `dbTA.CreateConnection()` | `:102` 與 `:269` |
| 6 | 本支**不覆寫** `Add` / `Update` / `Delete`,直接吃基底 | 全檔剝註解後只有 `CheckStkBrkData` / `CheckDelete` / `BuildMasterSQLString` 三個方法 |

**推得:按查詢就 NRE,不是存檔才 NRE。**這與 `ofd6.md` 對同型畫面的結論一致。

#### 一半以上的檔案是註解

1,272 行裡,`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270` 是一個 `#region 註解` 包著的 `/* public class FSKM004_PO : Basic_PO { ... } */`——**上一代的完整實作**,包含 `AddSTK_BRK_Data` / `UpdateSTK_BRK_Data` / `DeleteSTK_BRK_Data` / `EVASTK_BRK_Data` / `ApproveDeleteSTK_BRK_Data` 等 14 個方法。那段裡看得到 SQL Server 時代的痕跡:`SELECT * FROM [FSK005]`(方括號)、`UpdateID <> '" + LoginUser + "'`(字串串接) (`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:889`)。

**活的那 320 行裡也還有 T-SQL。**`CheckStkBrkData` 用的是 `SUBSTRING(AGENT_CODE,2,4)` (`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:114`)——Oracle 沒有 `SUBSTRING`,只有 `SUBSTR`。 **就算 `dbTA` 有連線,這段 SQL 在 Oracle 上也會語法錯誤。**這是第二條「它沒在跑」的旁證。

檔案最後一行是 `}//end namespace Adapterusing System;`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:1272`)—— 兩段文字被黏在一起,顯示這個檔曾經被截斷或貼壞過。

#### Ctl 層也不照慣例

`FSKM004_Ctl` **沒有繼承 `BaseController`**(`Dev/ATLAS.FSK/Source/Control/Control.FSK/FSKM004_Ctl.cs:13`), 每個方法自己 `new FSKM004_PO()`(例 `:37-39`),不走 `DataAccessPool`、沒有 `InitializeVDBTypes()`。這是 `architecture.md §2` 說的六層職責的完全例外,全片只有這一支這樣寫。

#### 兩個檢核的回傳值語意是反的

| 方法 | 回 `ReturnCode = true` 代表 | 呼叫端怎麼用 |
|---|---|---|
| `CheckDelete` | **有分公司資料,不可刪** | `if (... == true) AddError(...)`(`Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:257-261`) |
| `CheckStkBrkData` | **已建立銷售機構資料,不可刪** | `if (... ReturnCode) AddError(...)`(`Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:268-274`) |

兩邊一致,所以行為是對的;但 `true = 有問題` 與全庫其他地方的 `true = 成功` 相反,改的時候很容易反過來。而且 `CheckStkBrkData` 的 `catch` 把結果設成 `AddResultRow(false, 0, "")`(`Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186`) ——**SQL 出錯等於「沒問題,可以刪」**,是 fail-open。

#### 誰在用 `FSK005`

維護畫面死了,表卻活著。共用 PO `BasicFSK_PO.GetStkBrkData` 直接讀 `FSK005` (`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117` 與 `:139`),餵給自訂控件 `ucStkBrk` / `ucSTK_BRK_GRP`, 再被 `BMSM001` / `BMSM006` / `NFDR433` / `NFDR435` / `OFDM231Ap1` / `OFDM243` / `OFDM243A` / `OFDM385` / `OFDB331p0` 等畫面用。另外 `OFDM068_PO` / `OFDM221A_PO` / `OFDM243A_PO` / `OFDB310_PO` 與 view `OFD068A_V02` 也直接 join 它。

**推論:`FSK005` 的資料只能靠 DB 直改或別的匯入途徑維護,`FSKM004` 這個入口已經沒在用。** 這是讀碼結論,沒有實跑過;要推翻它得證明 `BasicEVAPO.dbTA` 在別處被賦值(`architecture.md §3` 已經掃過,沒有)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 任何查詢 | (無)——`BeforeSelect` 直接 NRE | 一定 | **整支不可用** | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:60` |
| 刪除前 | 有分公司(`STK_BRK_GRP` 指向本代碼)不可刪 | 有 | 阻擋 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:257-261` |
| 刪除前 | 已在 `OFD068` 建立銷售機構不可刪(限總券商) | 有 | 阻擋 | `Dev/ATLAS.FSK/Source/UI/UI.FSK/FSKM004.cs:264-275` |
| 刪除前 | 上述檢核的 SQL 出錯 | 例外 | **記錄不擋(fail-open)** | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186` |

### 4.6 `OFDM221C` — 境外基金申購維護(綜合帳戶軌)

#### 用途(推測)

建立與維護境外基金的申購單:主檔 `OFD220` 一張申購書、明細 `OFD221` 一到多筆基金申購明細。走完整四眼,是本片第二大的一支(PO 1,086 行)。

#### 申購書號怎麼來

`BeforeAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:144-177`):

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | `GetTradeId(row.FH_CD)` 去 `OFD062` 取 `TRADE_ID`,取不到回 `'X'` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:930-960` |
| 2 | `'X'` 或空字串 → 丟例外「TradeId(OFD062)」——**阻擋** | `:156-157` |
| 3 | `new SerialNo(args.DbTranPTPF, dbPTPF)`,序號類別是 `"OFD220" + TradeId` | `:160-164` |
| 4 | `genSrNo.GetSrIdNoForOTA(strSrId)` 取號 | `:165` |
| 5 | `do { 取號 } while (IsExistByData(...))` —— 撞號就重取,**沒有次數上限** | `:162-167` |
| 6 | 把 `ALLOT_NO` 與 `BF_NO` 回填到每一筆明細 | `:170-174` |

第 5 步的無上限重試與 `architecture.md §3` 記的 `CASM001_PO` 是同一個模式,同樣有無窮迴圈風險。第 4 步的 `GetSrIdNoForOTA`(無原始碼,從呼叫端反推)是 **OTA 軌專用的取號進入點**,`ATLAS.OFD` 那邊用的是別的多載。

#### 存檔後同步 `OFD113`:繞過四眼寫另一張主檔

`AfterAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:237-307`)與 `AfterUpdate`(`:314-440`)對每一筆有 `DIVIDEND_ID` 的明細做同一件事:

1. 把 `OMNIBUS_ID` 從 `'Y'/'N'` 轉成 `'2'/'1'`(`:249`,`AfterUpdate` 在 `:326`)。

2. 用 `GetOFD113` 查現有設定(`:184-228`)。

3. 沒有 → INSERT;有但 `DIVIDEND_ID` 或 `SHARE_DIV_FUND` 不同 → INSERT(`AfterUpdate` 還多一條 UPDATE 路徑,`:390`)。

**這條 INSERT 把四眼全部填滿:** `STATUS` 寫死 `'301'`、`DATA_ID` 寫死 `'2'`、`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全部塞同一個 `model.Utility.PermissionInfo[0].UserID`、日期全是同一個 `DateTime.Now` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276`,`AfterUpdate` 的同一段在 `:353-354`)。

也就是說:**使用者在申購單上改配息方式,`OFD113` 這張表就多一筆「已核准」的設定,不經過任何覆核。** `OFD113` 自己有維護畫面 `OFDM113`(§4.9),那支是走四眼的——**同一張表,兩個入口,兩種治理強度**。

#### 存檔前檢核 `befPostCheck`

UI 在存檔前另外呼叫一支 `befPostCheck`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:967-1078`),兩道:

| 道 | SQL | 成立時的訊息 |
|---|---|---|
| 交易檢核 | `OFD081.LAST_ALLOT_DATE_P`(分戶)或 `LAST_ALLOT_DATE_O`(綜合)`< :ALLOT_DATE` | 「輸入的申購日期大於該基金的申購最後交易日, 故不可輸入此申購日期」 |
| 結帳檢核 | `OFD303.CTL_DATE = :ALLOT_NAV_DATE` 且 `ALLOT_CTL_CODE`(分戶)或 `ALLOT_CTL_CODE_O`(綜合)`>= '2'` | 「此基金該申購日期已處理到下單確認之後, 故不可輸入此申購日期」 |

兩道都用 `UNION ALL` + `AND :OMNIBUS_ID = 'N' / 'Y'` 的寫法在同一段 SQL 裡切兩軌 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001`;`:1036` 與 `:1044`)。 `LAST_ALLOT_DATE_*` 有做 `NVL(TRIM(...), '29991231')`,所以**沒設最後交易日的基金不會被擋**,是刻意的。

#### 其他取數方法

| 方法 | 取什麼 | 注意 |
|---|---|---|
| `GetOFD110` | 受益人匯款帳戶 | — |
| `GetOFD562` | 受益人扣款帳戶 | 與 `OFDM551` / `OFDM554` 的同名方法各寫一份 |
| `GetOFD113` | 配息設定 | `catch` 是空的(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224`) |
| `GetOFD086` | 配現可再投資基金 | — |
| `GetOFD091` | ISHARE 基金申購金額額度 | SQL 裡 `OFD221.OMNIBUS_ID = 'N'` 與 `ALLOT_PROC_CODE <> 'D'` 都寫死(`:900-901`) |

`ALLOT_PROC_CODE <> 'D'` **沒有 `NVL`**。Oracle 三值邏輯:`ALLOT_PROC_CODE` 是 NULL 時 `NULL <> 'D'` 是 UNKNOWN,該列不計入額度。 **已用額度會被低估**,放行原本該擋的申購。這是本片第一條「`欄 <> '值'` 遇 NULL」。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `OFD081` 最後交易日 | 申購日晚於最後交易日 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1017-1022` |
| 存檔前 | `OFD303` 結帳狀態 | 已到下單確認之後 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1061-1066` |
| 存檔前 | 上述兩道的 SQL 出錯 | 例外 | 阻擋(`AddResultRow(false, …, ex.ToString())`,訊息是原始例外字串) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1071-1076` |
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋(丟例外) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:156-157` |
| 新增時 | 取到的書號已存在 | 是 | 重取(**無上限**) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:162-167` |
| 存檔後 | 配息設定有差異 | 是 | **記錄不擋**(直接寫 `OFD113`,`STATUS='301'`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276` |
| 額度查詢 | `ALLOT_PROC_CODE <> 'D'` | NULL 時 UNKNOWN | **過濾(無提示)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |

### 4.7 `OFDM231B` — 境外基金買回 / 轉換維護(綜合帳戶軌)

#### 用途(推測)

買回(贖回)與轉換單據的維護。主檔 `OFD251`(152 欄),三張明細: `OFD252` 基金贖回付款、`OFD253` 轉換、`OFD254` 基金贖回銷售沖銷。PO 1,180 行,是本片最大的一支。

#### 與 `OFDM221C` 對稱的地方

| 面向 | `OFDM221C` | `OFDM231B` |
|---|---|---|
| 書號 | `"OFD220" + TradeId` → `ALLOT_NO` | `"OFD251" + TradeId` → `REDEM_NO`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:151-205`) |
| 存檔前檢核 | `befPostCheck` 兩道 | `befPostCheck` 兩道,**但每道多一個分支**(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:967-1172`) |
| 存檔後 | 同步 `OFD113` | `AfterAdd` / `AfterUpdate` 都只是空殼(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:206-230`) |

#### 獨有的兩件事

**(1)明細 `OFD254` 由 SP 產生,不是使用者輸入。** `GetOFD2541` 依模式叫兩支不同的 SP(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:704-757`):

| 情境 | SP |
|---|---|
| 新增 | `S_OTA_OFDM231B_EXE_ADD`(`:714`) |
| 修改 | `S_OTA_OFDM231B_EXE_MOD`(`:732`) |

兩支都在版控內(`DB/SP/S_OTA_OFDM231B_EXE_ADD.SQL`、`DB/SP/S_OTA_OFDM231B_EXE_MOD.SQL`)。

**(2)匯率取自別的模組的 SP。** `GetOFD300` 叫 `S_TA_IMP_OFD300_RANGE`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:891`)取集保匯率檔。這支 SP **不在 `DB/` 版控內**(`architecture.md §9` 已記 `DB/` 只涵蓋一部分 SP),已列入 meta 的 `refcheck-ignore`。

#### 明細 SQL 的複製貼上痕跡

`BuildDetailSQLString` 用 `switch (strTableName)` 分三段(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:307-643`):

| `case` | region 標題 | 實際組的表 |
|---|---|---|
| `"OFD252"`(`:314`) | 基金贖回付款檔(OFD252) | `OFD252` ✔ |
| `"OFD253"` | **基金贖回付款檔(OFD252)**(`:438`,**標題沒改**) | `OFD253`(`:440`、`:580`) |
| `"OFD254"`(`:583`) | 基金贖回銷售沖銷檔(OFD254) | `OFD254` ✔ |

三段的 WHERE 都用字串串接接書號(`:434`、`:580`、`:631`),不是參數化。書號由伺服器自己產生,注入風險低,但寫法不一致。

#### UI 端的兩處 `Select("FUND_ID <> ''")`

`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488` 與 `:498-499` 各取 `[0]`,**沒有長度檢查**。明細全空(合法情境:只填主檔先存)就 `IndexOutOfRangeException`。而且 `DataTable.Select` 的 `<> ''` 在 .NET 的語意與 Oracle 不同(.NET 的空字串不是 NULL), 所以這裡不會踩到三值邏輯,但**同一支程式裡 `<>` 有兩種語意**,讀碼要分清楚在哪一層。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | `OFD081` 最後交易日(買回) | 買回日晚於最後交易日 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1020-1025` |
| 存檔前 | 同上的第二個分支(轉換) | 是 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1063-1068` |
| 存檔前 | `OFD303` 結帳狀態(買回) | 已結帳 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1108-1113` |
| 存檔前 | `OFD303` 結帳狀態(轉換) | 已結帳 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:1153-1158` |
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:163-168` |
| UI 取值 | 明細第一筆 | 明細 0 筆 | **例外** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488`、`:498-499` |

### 4.8 三支授權書畫面:`OFDM109` / `OFDM111` / `OFDM561`

結構幾乎相同(主檔一張授權書 + 明細一組帳戶 / 期間),PO 都繼承 `BaseEVADaoPO`,都有 `BeforeAdd` 取號。

| 畫面 | 主 / 明細 | 特別的方法 | 注意 |
|---|---|---|---|
| `OFDM109` | `OFD109` / `OFD110` | `GetCRNCY_CD`:查該受益人在綜合帳戶有部位的交易幣別(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453-486`) | SQL 裡 `CRNCY_CD <> 'TWD'` 沒 `NVL`(`:466`)→ 幣別 NULL 的部位被靜默濾掉 |
| `OFDM111` | `OFD111` / `OFD112` | `SetOPEN_ACC_DATE_OFF`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:396-443`);另外 join view `FNDV01` | — |
| `OFDM561` | `OFD561` / `OFD562` | 無 | 與 `OFDM109` 的欄位名完全撞名(`REMIT_CFM_NO`),見 §2.3 |

三支共同的兩個寫法:

- **明細 SQL 的書號用字串串接**:`OFD110.REMIT_CFM_NO = '" + strREMIT_CFM_NO + "'` (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:256`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:237`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM561_PO.cs:249`)。

- **`BeforeAdd` 的 `do/while(IsExistByData)` 沒有次數上限**(`OFDM109_PO.cs:141-182`、`OFDM111_PO.cs:134-175`、`OFDM561_PO.cs:135-176`)。

`OFDM109` 的 UI 另有一條:`Select("ACC_NO_TYPE <> '0'")`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM109.cs:281`)—— 這是 `DataTable.Select`,不是 SQL,語意正常。

#### 卡控總表(三支合併)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增時 | 取到的書號已存在 | 是 | 重取(無上限) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:141-182` |
| 幣別下拉 | `CRNCY_CD <> 'TWD'` | 幣別為 NULL | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:466` |
| 取數失敗 | 任一 `Get*` 方法例外 | 有 | 警示(訊息如「取得有綜合帳戶交易幣別,請檢查」) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:477-481` |

### 4.9 兩支配息畫面:`OFDM113` / `OFDM251`

| 畫面 | 主檔 | 管什麼(推測) |
|---|---|---|
| `OFDM113` | `OFD113` | 受益人層級:某受益人某基金的配息方式與再投資標的 |
| `OFDM251` | `OFD281` | 基金層級:某基金某基準日的配息公告(每單位配現、發放日) |

**`OFDM113_PO.cs` 是本片唯一的非 UTF-8 來源檔**(cp950 / Big5)。用 UTF-8 讀會看到亂碼,例如 `:235` 那則訊息在 UTF-8 下是 `���o�t�Ѱ���N��(OFD086)...`, 用 cp950 讀才是「取得配股基金代號(OFD086),請檢查」。 `architecture.md §5` 的「混編碼」風險在本片就命中這一支;任何用 UTF-8 一刀切的工具(含本文的掃描器)碰它都會出亂碼。

`OFDM251_PO` 的查詢條件有一條字串串接的 `LIKE`:

`strSQL += " AND OFD281.RECORD_DATE LIKE " + "'" + Row.Value + "%'";`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182`)

——**本片唯一一處把使用者輸入直接串進 SQL 的地方**。`RECORD_DATE` 來自畫面的日期欄,值帶單引號就會壞掉(或被利用)。前 21 篇的型錄裡有「`LIKE` 樣式餵給 `=`」(`ofd4.md`),這裡是相反的形態:**`=` 的值被硬改成 `LIKE` 樣式,而且是串接的**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | `RECORD_DATE LIKE '<值>%'` | 值含單引號 | **例外 / 注入風險** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182` |
| 取配股基金 | `OFD086` 查不到 | 0 筆 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:226-229` |

### 4.10 兩支定期定額畫面:`OFDM551` / `OFDM554`

一對成對畫面:`OFDM551` 建契約(`OFD551` / `OFD552`),`OFDM554` 建契約變更(`OFD554` / `OFD555`)。

| 面向 | `OFDM551` | `OFDM554` |
|---|---|---|
| 書號類別 | `"OFD551" + TradeId` → `RSP_NO` | `"OFD554" + TradeId` → `RSP_CHG_NO` |
| 取扣款帳戶 | `GetOFD562`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:385-431`) | `GetOFD562`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:455-497`) |
| 取申購明細 | `GetOFD221`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434-500`) | 無 |
| 取原契約 | `GetOFD555` **走報表 SP** `S_OTA_OFDR552_GET`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:503-537`) | `Get_Origin`(自組 SQL,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:600-680`) |
| 停扣過濾 | 無 | `NVL(OFD551.STOP_ID, 'N') <> 'Y'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543`) |

**兩支各寫一份 `GetOFD562`,SQL 不同。**改扣款帳戶的取數邏輯要記得兩邊都改,這是型錄裡「成對畫面只改一邊」的溫床。

`OFDM554` 的停扣過濾有做 `NVL`,是本片唯一一處把三值邏輯處理對的地方——**同一個團隊、同一個模式,有的寫對有的沒寫**(對照 §4.6 的 `ALLOT_PROC_CODE`)。

`OFDM551` 的 `GetOFD555` 直接叫報表的 SP(`S_OTA_OFDR552_GET`)拿維護畫面要用的資料。報表 SP 的結果集欄位若為了報表需求調整,**維護畫面會跟著壞,而且沒有任何編譯期關聯看得出來**。

#### 卡控總表(兩支合併)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增時 | `OFD062.TRADE_ID` 取不到 | `'X'` 或空 | 阻擋 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:136-180` |
| 查原契約 | `NVL(OFD551.STOP_ID,'N') <> 'Y'` | 已停扣 | 過濾(無提示) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| 取數失敗 | `GetOFD562` / `GetOFD221` / `GetOFD555` 例外 | 有 | 警示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:422-426`、`:491-495`、`:528-532` |

### 4.11 `OFDM302B` — 境外基金淨值維護與鎖定(**本片最危險的一支**)

#### 用途(推測)

匯入 / 維護 `OFD302`(基金代碼 + 淨值日期 → 申購淨值、贖回淨值、正式淨值、基金規模), 並用 `NAV_LOCK` 把某一天的淨值鎖起來,鎖後才能給下游結帳用。

#### 四個自訂鈕

| 鈕 | 方法 | 做什麼 |
|---|---|---|
| `DoExp1` | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:268-278` | 整批匯入(`BatchAdd`) |
| `DoExp2` | `:279-299` | 淨值鎖定(`Update_NAVLOCK`) |
| `DoExp3` | `:300-317` | 列印淨值表(`PrintReportNAV` → `OFDM302BRPS2`) |
| `DoExp4` | `:318-328` | 列印鎖定淨值表(`PrintReportLockNAV` → `OFDM302BRPS1`) |

兩張 `.rpt` 都**不在任何 csproj**(§3.5 註 2)。

#### 整批匯入:三個問題

`BatchAdd`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:177-251`):

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **`DELETE OFD302 WHERE NAV_DATE = :NAV_DATE`** | 刪除條件**只有淨值日期**,不含基金公司也不含基金代碼。匯入某一家基金公司的淨值檔,會把**那一天全部基金的淨值整批刪掉**,再只補回檔案裡有的那幾筆 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:191-192` |
| 2 | **刪除的檢核是死的** | `if (i == -1)`,而 `ExecuteNonQuery` 回的是影響列數,永遠不是 -1 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` |
| 3 | **完全繞過四眼** | `STATUS` 寫死 `'301'`,`CREATEID` / `ENTRYID` / `UPDATEID` / `VERIFYID` / `APPROVEID` 全塞 `row.CREATEID`、日期全是 `SYSDATE` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:208-209` |

再加一條:`catch` 裡的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉** (`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:239-245`),例外不上報,只把 `ex.ToString()` 塞進結果訊息給使用者看。

`OFD302` 的下游很廣(§2.4):`CLSR002` 結算報表、`OFDI058` / `OFDI058B` 查詢、 `OFDB322` / `OFDB323` / `OFDB722` 批次、`OFDI011` 淨值查詢都讀它。 **問題 1 的爆炸半徑是整個結帳。**

#### 淨值鎖定:同一個 UPDATE 跑兩次

`Update_NAVLOCK`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:452-519`)對每一筆勾選的列跑 `UPDATE OFD302 SET NAV_LOCK, UPDATEID, UPDATEDATE WHERE NAV_DATE = ? AND FUND_ID = ?`。

```
dbProduct.ExecuteNonQuery(cmd, tran);          // :493  ← 第一次,回傳值丟掉
i = dbProduct.ExecuteNonQuery(cmd, tran);      // :495  ← 第二次,回傳值才拿來判斷
```

**同一個 `DbCommand` 被執行兩次。**因為 UPDATE 是冪等的,資料結果一樣; 但每一列都多打一次 DB,而且 `:495` 的第二次必然影響同樣的列數,所以 `i == 0` 的檢核實際上檢的是第二次。這是「`ExecuteNonQuery` 回傳值被覆蓋」的變形。

另外它**直接寫 `UPDATEID` / `UPDATEDATE`,不經四眼**——這是型錄裡「繞過四眼直接 UPDATE 主檔」(`ofd5.md` 記過同型)在本片的第二例。

#### UI 端的鎖定保護

`SetControlEnabled()`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:467-483`)把 `ucomNAV_LOCK` 設成 `Enabled = false` 加 `ReadOnly = true`(`:470-471`),新增時強制 `"N"`(`:476`)。 `DoValidate()` 另有一條:雙擊且鎖定碼是 `"1"` 時擋修改(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160`)。

**注意鎖定碼在三處用了三種值:**`SetControlEnabled` 寫 `"N"`、`DoValidate` 比 `"1"`、 `PrintReportLockNAV` 的 SQL 比 `NAV_LOCK = 'Y'`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:282`)。下拉的資料來源是 `YesNoDataSrc`(`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:246`),也就是 `Y`/`N`。 **`"1"` 這個值對不上任何一邊**——`DoValidate` 那道檢核**永遠不會成立**,等於沒有。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 修改前 | 雙擊且 `NAV_LOCK == "1"` 時擋 | **永不成立**(下拉只給 `Y`/`N`) | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160` |
| 新增 / 修改 | 鎖定碼欄位唯讀 | 一律 | 阻擋(UI 層) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:470-471` |
| 整批匯入 | 刪除影響列數 `== -1` | 永不成立 | **記錄不擋(死檢核)** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` |
| 整批匯入 | 每列 INSERT 影響列數 `== 0` | 是 | 阻擋 + rollback | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:228-234` |
| 鎖定 | 每列 UPDATE 影響列數 `== 0` | 是 | 阻擋 + rollback(判的是**第二次**執行的結果) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:495-501` |
| 列印鎖定表 | 有鎖定的淨值 | 0 筆 | 警示「淨值未鎖定」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:319-322` |

### 4.12 `OFDM602A` — 文件需求設定維護

`OFD605`(`REQ_DOC_KIND` + `DOC_CD`)的多筆主檔維護,PO 只有 192 行,是 11 支 `OFDM*` 裡最小的。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `MasterTable.Add(new xTableMapping("OFD605", "OFD605"))` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:68` |
| 查詢條件 | `REQ_DOC_KIND` 用**字串串接** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:177` |
| 事件 | 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData`,**沒有 `BeforeAdd`**(不需要取號) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM602A_PO.cs:76-122` |

它的 `ATLAS.EC` 版姊妹 `OFDM602` 讀寫**同一張 `OFD605`**,但整個 PO 類別被註解掉 (`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19` 是 `// public class OFDM602_PO : MultiRowEVAPO`)。 **推論:`OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品,不是平行軌。** 這也是 11 支裡唯一一支「兩軌讀同一張表」的,其他三對都是各讀各的表(§0.3)。

### 4.13 `OTAM901` — 報表行銷說明代碼維護

`BMS999`(`ST_CD`)的單表四眼維護,PO 185 行,結構與 `TRPM005` 一模一樣。

| 面向 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `BMS999` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:66` |
| 查詢條件 | 只有 `ST_CD` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OTAM901_PO.cs:146` |
| 自訂檢核 | **沒有**,`DoValidate()` 只叫框架的 `DataValidate()`(與 `TRPM005` 一樣) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:140-145` |

**表名前綴誤導**:表叫 `BMS999`,直覺會去 `ATLAS.BMS` 找維護畫面,但全庫只有 `OTAM901` 碰它。 `architecture.md §2` 說「看到代號就知道六個檔在哪」,這條鐵律**不適用於表名**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:101-112` 與 `:118-129` |
| 刪除前 | (無) | — | 不擋 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OTAM901.cs:114-117` |

## 5. 查詢畫面(I)

本片只有一支:`TRPI001`(集保傳收檔紀錄查詢),住在 `ATLAS.OTA.Query`。

### 5.1 結構

完全符合 `architecture.md §6` 對 I 型的描述:PO 退化成裸 DAO。

| 層 | 類別 / 基底 | 錨點 |
|---|---|---|
| UI | `TRPI001 : xOneStepProcessForm`(**不是 `xQueryForm`**;`architecture.md §6` 說 I 型有 94 支用這個基底) | `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:18` |
| Ctl | `TRPI001_Ctl : BaseController`,**有**覆寫 `InitializeDataAccessPool()` 與四個 `CustomTransfer*` | `Dev/ATLAS.OTA.Query/Source/Control/QueryControl.OFD/TRPI001_Ctl.cs:11`、`:22`、`:61-89` |
| PO | `TRPI001_PO : ITRPI001_PO`,**沒有基底**,自己 `new Database("TA", DbServerType.Oracle)` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:32` 與 `:34` |

三個與慣例不同的地方,都在 `architecture.md §2` 的例外清單裡:

1. PO 檔名是 `TRPI001_PO.cs`,不是 `.Query` 專案常見的 `<代號>OracleDao.cs`。

2. 層資料夾叫 `QueryPO.OFD` / `QueryUI.OFD` / `QueryControl.OFD`(前綴 `OFD`),但畫面代號是 `TRP`、組件名是 `QueryPO.OTA`。

3. 專案是 `ATLAS.OTA.Query`,模組是 `TRP`。**三個名字三個模組碼**。

### 5.2 查詢條件

UI 送五個參數(`Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:99-103`):

| 參數 | 控件 | PO 有沒有用 |
|---|---|---|
| `TRP_TYPE` 申報平台種類 | `ucboTRP_TYPE` | 有,`= :TRP_TYPE` |
| `PERIOD` 週期 | `ucboPERIOD` | 有,`= :PERIOD` |
| `FILE_STYLE` 傳檔 / 收檔 | `uoptFILE_STYLE` | **沒有**,見 §5.3 |
| `FILE_NAME` 檔名(值其實是 `MEDIA_NO`) | `ucboFILE_NAME` | 有,`TRP001.MEDIA_NO = NVL(TRIM(:FILE_NAME), TRP001.MEDIA_NO)` |
| `TRANS_DATE` 傳檔日期 | `udatTRANS_DATE` | 有,`TRP002.TRANS_DATE = NVL(TRIM(:TRANS_DATE), TRP002.TRANS_DATE)` |

`FILE_NAME` 這個參數名與它裝的值不一致:UI 的下拉是 `GetFileName` 撈出來的 `TRP001.MEDIA_NO AS CODE, TRP001.FILE_NAME AS CODE_DESC`(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:140`), 所以 `Value` 是 `MEDIA_NO`、顯示才是 `FILE_NAME`。SQL 端也確實拿它去比 `MEDIA_NO`。**參數名騙人,行為是對的。**

### 5.3 哪些條件會靜默濾掉資料

#### (1)`FILE_STYLE` 送了但沒用 — 傳檔與收檔查出來一樣

UI 在 `:101` 把 `FILE_STYLE` 放進 `QueryVDB.Util.Parameters`, 但 `GetData` 的 SQL 與 `AddInParameter` 都**沒有這個欄位** (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:83-96`)。

它唯一有作用的地方是**下拉選單的內容**:`GetFileName` 會拿 `FILE_STYLE` 去篩 `TRP001` (`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:132`)。

**後果**:只要使用者不指定檔名(下拉留空),切「傳檔」與切「收檔」查出來的結果**完全一樣**—— `TRP002` 裡同種類同週期的傳檔與收檔紀錄會混在一起,而且畫面上沒有欄位可以分辨。結果類型:**過濾(無提示)的反面 —— 該濾沒濾**。

#### (2)`INNER JOIN TRP001` 會讓歷史紀錄整筆消失

```
FROM TRP002
INNER JOIN TRP001 ON TRP002.TRP_TYPE = TRP001.TRP_TYPE AND TRP002.FILE_NAME = TRP001.FILE_NAME
```

(`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81`)

`TRP002` 是傳檔紀錄(歷史),`TRP001` 是設定(現況)。 **設定被刪掉、或 `FILE_NAME` 被改過,對應的歷史紀錄就查不到了,而且沒有任何提示。** 這正是型錄裡「`INNER JOIN` 讓對不到的資料無聲消失」(`ofd6.md` 記過同型)。對照下一行的 `LEFT JOIN OFD062`(基金公司名稱)——**同一段 SQL 裡,作者知道要用 `LEFT JOIN`,卻在 `TRP001` 這裡用了 `INNER`**。

#### (3)基金公司欄位的 `DECODE(..., NULL, '所有境外基金公司', ...)`

`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:68-71`: `FH_CD` 是空的(不分基金公司的傳檔)時,`LEFT JOIN OFD062` 對不到,名稱欄顯示「所有境外基金公司」。這個判斷是**用名稱欄是不是 NULL** 來反推,不是用 `FH_CD`。所以 **`FH_CD` 有值但 `OFD062` 查不到那家公司**(代碼被刪或打錯)時,畫面一樣顯示「所有境外基金公司」——**錯的資料長得像對的**。

#### (4)`SUBSTRB(...,1,25)` 硬切 25 位元組

同一行的顯示字串是 `SUBSTRB('(' || FH_CD || ')' || FH_NM_SH_C, 1, 25)`。 `SUBSTRB` 切的是**位元組**不是字元,中文一個字 2 到 3 位元組,長名稱會被切一半,可能切出半個中文字。

### 5.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 框架必填格式 | 有錯 | 阻擋 | `Dev/ATLAS.OTA.Query/Source/UI/QueryUI.OFD/TRPI001.cs:85-97` |
| 查詢 | `FILE_STYLE` 條件 | **永不生效** | **該濾沒濾** | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:83-96` |
| 查詢 | `INNER JOIN TRP001` | 設定已刪 / 改名 | 過濾(無提示) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81` |
| 查詢後 | 查無資料 | 0 筆 | **記錄不擋**(`AddResultRow(false, 0, "")`,**訊息是空字串**,畫面上不會說為什麼) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:105-111` |
| 查詢 | SQL 例外 | 有 | 警示(訊息是 `ex.Message` 原文) | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:113-118` |

## 6. 批次(B)與 WindowsService

**本片無 B 型畫面,也沒有任何 WindowsService。**

原因很具體:這 21 支的批次性工作(傳檔、收檔、淨值匯入、月報製作)**全部設計成「使用者按按鈕」的一次性作業**, 而不是排程。三個佐證:

| 佐證 | 內容 | 錨點 |
|---|---|---|
| 1 | `TRPM001` / `TRPM101` 的 UI 基底是 `xOneStepProcessForm`(B 型常用的基底),但代號是 `M`。也就是說**批次能力被寫進 M 畫面裡了**,沒有再開一支 B | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:30` |
| 2 | 產檔那一步是**用戶端**的 `StreamWriter`,不是伺服器端寫檔——服務跑不了這種流程(服務沒有使用者的磁碟對映) | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:527` |
| 3 | `architecture.md §6` 實測全庫只有 4 支 B 畫面配了獨立 Windows 服務(`OFDB600` / `OFDB609` / `OFDB680` / `RSPB008`),沒有一支屬於本片 | `architecture.md §6` |

**對維護的意義**:要把傳檔改成自動排程,不能只是加一支服務去叫現有的 `_Pxy`—— 產檔落地那段在用戶端,得先把它搬到伺服器側,或改寫成伺服器直接寫檔。

## 7. 報表(R)

### 7.1 七層結構

R 型是**七層不是六層**(`architecture.md §6`):六層各自加 `Report` 前綴,再多一個 `Report.<模組>` 專案只放 `.rpt`。本片三支橫跨兩個 `.Report` 專案:

| 層 | `TRPR001` / `OTAR901` 的專案 | `IJPR611` 的專案 |
|---|---|---|
| 1 UI | `ReportUI.OTA` | `ReportUI.EC` |
| 2 FormProxy | `ReportFormProxy`(**資料夾名沒有 `.OTA`**) | `ReportFormProxy.EC` |
| 3 Control | `ReportControl.OTA` | `ReportControl.EC` |
| 4 PO | `ReportPO.OTA` | `ReportPO.EC/Oracle`(**多一層 `Oracle` 子目錄**) |
| 5 DataEntity | `ReportDataEntity.OTA` | `ReportDataEntity.EC` |
| 6 UIEntity | `ReportUIEntity.OTA` | `ReportUIEntity.EC` |
| 7 CrystalReports | `Report.OTA` | `Report.EC` |

`Dev/ATLAS.OTA.Report/Source/FormProxy/ReportFormProxy/` 這個資料夾**沒有模組後綴**, 與 `architecture.md §6` 舉的 `ReportFormProxy.CAS` 不同;`architecture.md §2` 把它歸在「專案名與層資料夾不同名」那一類例外。用 glob 寫死 `ReportFormProxy.<模組>` 會找不到 `TRPR001_Pxy.cs` 與 `OTAR901_Pxy.cs`。

### 7.2 一覽

| rpt | 對應畫面 | 取數來源 | 參數 | 在版控 |
|---|---|---|---|---|
| `TRPR001RPS1` | `TRPR001` | `S_OTA_TRPR001_GET`(refcursor `OutTB1`) | `iCAL_YM` `iFH_CD` | `DB/SP/S_OTA_TRPR001_GET.SQL` ✔ |
| `OTAR901RPS1` | `OTAR901` | `S_OTA_OTAR901_GET` | `iALLOT_DATE_S` `iALLOT_DATE_E` `iAGENT_ID_S` `iAGENT_ID_E` `iAGENT_CODE_S` `iAGENT_CODE_E` | **不在版控**(已列 `refcheck-ignore`) |
| `IJPR611RPS1` 到 `IJPR611RPS7` | `IJPR611` | Dao 內七段長 SQL,不走 SP | `DATES` `ID_NO` `PrintType` `EMP_NO` | 不適用 |

### 7.3 `IJPR611` — 七支 `.rpt`,畫面只選得到五支

`uoptPrintType` 這個選項組在 Designer 裡**只有五個項目**,`DataValue` 是 `"0"` 到 `"4"` (`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:203-218`):

| 值 | 顯示文字 |
|---|---|
| `0` | 全方位理財約定書 |
| `1` | 查詢戶約定書 |
| `2` | 舊戶轉查詢戶約定書 |
| `3` | 查詢轉全方位理財約定書 |
| `4` | 傳統戶轉全方位理財約定書 |

但 UI 的 `switch` 與 Dao 的 `switch` 都處理 `"0"` 到 `"6"`,共七個分支 (`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:126-155`;`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:66`)。 Dao 的註解直接寫出第 6、7 種是什麼:

`//0:全方位理財約定書 1:查詢戶約定書 2:舊戶轉查詢戶約定書 3:查詢戶轉全方位理財約定書 4:傳統戶轉全方位理財淤定書 5:ACH定額授權書 6:財金定額授權書` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64`)

**結論:`IJPR611RPS6`(ACH 定額授權書)與 `IJPR611RPS7`(財金定額授權書)是死碼。** 兩支 `.rpt` 與對應的 SQL 分支都編進組件、都在 csproj 裡,但**畫面上沒有任何入口選得到它們**。 `VirtualReportFormUtility` 也照樣為它們註冊了七組事件(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:60-115`)。

**假設**:這兩式曾經開放過、後來被從選項組拿掉,或反過來是預留還沒上線。依據是註解把 7 種都寫齊、七層都備好,只有 Designer 的選項少了兩個。要確認得問使用者或查需求單。

### 7.4 `IJPR611` 的三個踩雷點

**(1)預覽有清參數、列印沒有。**

```
IJPR611_BeforePreviewButtonClicked:  … switch … ; this.QueryVDB.Util.Parameters.Clear(); … Add(DATES/ID_NO/PrintType/EMP_NO)
IJPR611_BeforePrintButtonClicked:    … switch … ;  (沒有 Clear)          … Add(DATES/ID_NO/PrintType/EMP_NO)
```

`Clear()` 只出現在預覽那一支(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:157`), 列印那一支從 `:170` 到 `:207` 一路直接 `AddParametersRow`,**沒有清空**。先按預覽再按列印,同一組參數就被加第二次。這是型錄裡「成對路徑只改一邊」的標準形態。

**(2)`ID_NO` 一律補 `%`,再由 SQL 用 `RTRIM` 剝掉。**

UI:`AddParametersRow("ID_NO", SQLOperator.Equal, custECID_NO_0.Value.Trim() + "%")`(`Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:163`)。 SQL:`AND (A.ID_NO = RTRIM(:ID_NO,'%') OR (E.ETRAFLG='N' AND E.DOC_CODE='Y' AND RTRIM(:ID_NO,'%') IS NULL))` (例 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:366`)。

使用者不輸入時 `ID_NO` 是 `"%"`,`RTRIM('%','%')` 在 Oracle 回空字串等同 NULL,走「全部」分支——**設計是這樣**。但這個約定同時表示:**受益人 ID 本身若以 `%` 結尾,尾巴會被吃掉**。而且參數名用的是 `SQLOperator.Equal` 卻裝著 `LIKE` 樣式,與型錄裡 `ofd4.md` 的「`LIKE` 樣式餵給 `=`」是同一個病灶,只是這裡靠 SQL 端補救了。

**(3)`DataTable.Select` 用字串串接組過濾式。**

`resultVDB.DataEntity.IJPR611RPS1Detail.Select("ORDER_Type = 2 AND ID_NO= '" + row.ID_NO + "' AND BANK_HQ_NAME = '" + row.BANK_HQ_NAME + "' …")` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:586`)。銀行名稱裡出現單引號就會丟 `SyntaxErrorException`。不是 SQL 注入,但同一類問題。

另外 Dao 裡有一條寫死的帳號樣式:`AND E.UPD_USER LIKE 'WebUser%'` (`Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:943`)——網路下單的帳號前綴,標〔客戶特定〕。

### 7.5 `OTAR901` — 報表之外還會開 Excel

`DoExp1`(`Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:324-362`)走的是完全不同的路:

| 步 | 做什麼 |
|---|---|
| 1 | `DoValidate(true)` 通過才往下 |
| 2 | `GetReportData` 取同一份資料 |
| 3 | 檔名寫死成 `<輸出路徑>\OTAR901RPS1.xlsx`,報表中文名在 `:335` 又寫一次(`:335-336`) |
| 4 | 0 筆就跳「查無相關資料。」並 return(`:339-345`) |
| 5 | `UIExcelHelper.GenExcelFile` 用 `Microsoft.Office.Interop.Excel` 在**用戶端**產檔(`:349-353`、`:372`) |

兩件事值得記:

- **報表中文名寫死在程式裡兩處**:`SetQueryParameters("OTAR901RPS1","OTAR901RPS1","弱勢族群交易回訪報表(境外)")`(`:130`)與 `new KeyValuePair<string,string>("OTAR901RPS1","弱勢族群交易回訪報表(境外)")`(`:335`)。改名要改兩處。

- **`catch` 把所有例外壓成同一句「商業邏輯異常!」**,原始訊息只丟給 `Console.WriteLine`(`:357-362`)—— WinForms 沒有主控台,**等於訊息直接消失**。這是本片最難除錯的一個 `catch`。

### 7.6 `TRPR001` — PO 檔名錯字與交易用法

取數只有一步:`S_OTA_TRPR001_GET` 加一個 refcursor `OutTB1` (`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:66-75`)。

三個觀察:

1. **PO 住在檔名少一個 `R` 的檔案裡**(§3.5 註 1)。

2. **純查詢卻開了交易**:`tran = m_db.BeginTransaction()`(`:61`)、`tran.Commit()`(`:78`)、`catch` 裡 `tran.Rollback()`(`:91`)。 `catch` 第一行就 `tran.Rollback()`,而 `tran` 是在 `try` 內賦值的——**連線開不起來時會再丟一個 `NullReferenceException` 蓋掉真正的錯誤**, 與 `architecture.md §3` 記的 `BasicEVAPO.Add` 是同一個模式。

3. **`using System.Data.OracleClient;` 與 `Oracle.ManagedDataAccess.Client` 並存**(`:11` 與 `:16`),前者是 .NET 內建的已淘汰 provider。

`GetReportObject` 照 `architecture.md §6` 的寫法,把用戶端傳來的報表類別名直接交給 `CRReportTransfer.TransferFileByte` (`Dev/ATLAS.OTA.Report/Source/Control/ReportControl.OTA/TRPR001_Ctl.cs:61-62`)——**用戶端指定要載入哪個報表類別,伺服器照單全收**。三支報表都是這個寫法。

### 7.7 卡控總表(三支合併)

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `IJPR611` | 預覽 / 列印前 | 「執行日期」與「受益人ID」必需擇一必輸 | 兩個都空 | 阻擋 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:216-228` |
| `IJPR611` | 列印 | 參數未清空 | 連按預覽再列印 | **記錄不擋(參數累積)** | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:170-207` |
| `IJPR611` | 選報表種類 | 第 6、7 式 | **選不到** | 死碼 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:213-218` |
| `OTAR901` | 預覽 / 列印前 | `DoValidate()` | 不過 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:120-127` |
| `OTAR901` | 匯出 Excel | 輸出路徑必填與存在 | 不符 | 阻擋 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:305-322` |
| `OTAR901` | 匯出 Excel | 查無資料 | 0 筆 | 警示 | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:339-345` |
| `OTAR901` | 匯出 Excel | 任何例外 | 有 | **記錄不擋 → 訊息消失**(只 `Console.WriteLine`) | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:357-362` |
| `TRPR001` | 取數 | 0 筆 | 是 | **記錄不擋**(`AddResultRow(false, 0, string.Empty)`,**訊息是空字串**) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:84-87` |

## 8. 跨模組共用

```text
[圖] 十一支 OFDM 與 ATLAS.OFD 的關係:四對兩軌、七支唯一實作、兩軌怎麼區分,以及 OFD113 的三個入口
圖中文字:分家方式:代號加後綴、表名去掉 A(四對) / OFDM221C → OFD220 OFD221 / ATLAS.OTA 綜合帳戶軌 / OFDM221A → OFD220A OFD221A / ATLAS.OFD 分戶軌 / OFDM221B / 只有 UI 一層 推測是子視窗 / OFDM231B → OFD251…254 / OTA 軌 / OFDM231A → OFD251A…254A / OFD 軌 再加七張明細 / OFDM302B → OFD302 / OTA 軌 / OFDM302 → OFD302A / OFD 軌 / OFDM602A → OFD605 / OTA 軌 活的 / OFDM602 → OFD605 / EC 專案 整個類別被註解 / 唯一的反例 / 同一張表 是改版不是分軌 / 另外七支在全庫是唯一實作,OFD 主軌沒有 / OFDM109 OFDM111 OFDM561 / 授權書與扣款帳戶 / OFDM113 OFDM251 / 配息 / OFDM551 OFDM554 / 定期定額 / 綜合帳戶軌有專屬功能 / 不是分戶軌的複製 / 怎麼區分兩軌 / OMNIBUS_ID / Y 綜合 / N 分戶 / OFD113 卻用 2 / 1 / 同概念兩套值域 / GetSrIdNoForOTA / OTA 專屬取號 / S_OTA_* 命名空間 / 與主軌的 S_TA_* 分開 / OFD113:一張表三個入口,兩種治理強度 / OFDM113 / 走四眼 / OFDM221C AfterAdd / 自組 INSERT STATUS 301 / OFDM231B / 只讀 / 資料上分不出來 / 只能看 ALLOT_NO 有沒有值
```

*圖:圖 5 跨模組。橘框=本片(綜合帳戶軌);灰虛框=ATLAS.OFD / ATLAS.EC 的對照組;橘虛框=反例或會咬人的地方;黑框=無原始碼。左右兩欄的表名只差一個 A,改欄位時很容易改錯邊。*

### 8.1 十一支 `OFDM*` 與 `ATLAS.OFD` 的關係

這是本片最重要的一節。結論先講:

> **`ATLAS.OTA` 裡的 11 支 `OFDM*` 是境外基金「綜合帳戶(Omnibus)軌」的實作, 與 `ATLAS.OFD` 的「分戶軌」平行。兩軌的分家方式是:代號加一個後綴字母、表名去掉結尾的 `A`。**

#### 證據鏈

| # | 事實 | 錨點 |
|---|---|---|
| 1 | 11 支在全庫**沒有同代號分身**(與 `ofdb3.md` 查到的 `OFDB562` 到 `OFDB564` 兩份六層不同) | 全庫搜這 11 個代號,只命中 `Dev/ATLAS.OTA/` |
| 2 | 帶後綴的四支各有一支不帶後綴或帶別的後綴的姊妹畫面,**住在別的專案** | §0.3 的對照表 |
| 3 | 姊妹畫面的表名多一個 `A`:`OFD220A` 對 `OFD220`、`OFD251A` 對 `OFD251`、`OFD302A` 對 `OFD302` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-68`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70-74`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| 4 | 本片的 SQL 到處用 `OMNIBUS_ID` 切兩軌,`'Y'` 走綜合、`'N'` 走分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001` |
| 5 | 取號用的是專屬多載 `GetSrIdNoForOTA`(無原始碼,從呼叫端反推) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:165` |
| 6 | SP 命名空間是 `S_OTA_*`,與主軌的 `S_TA_*` 分開 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:714` 對照 `:891` 的 `S_TA_IMP_OFD300_RANGE` |
| 7 | 方法的中文註解直接寫「取得有綜合帳戶交易幣別」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:453` |

#### 唯一的例外:`OFDM602A`

`OFDM602A` 與 `ATLAS.EC` 的 `OFDM602` **讀寫同一張 `OFD605`**,不是兩軌。而 `OFDM602_PO` 整個類別被註解掉(`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM602_PO.cs:19`,注意它住在 `MSSQL` 子目錄)。 **推論:`OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品,`A` 後綴在這裡是「改版」不是「分軌」。** 所以「後綴字母 = 分軌」這條規則**有一個反例**,不能當通則套。

#### 另外七支沒有姊妹

`OFDM109` `OFDM111` `OFDM113` `OFDM251` `OFDM551` `OFDM554` `OFDM561` 在全庫是唯一實作,`ATLAS.OFD` 沒有同號畫面。 **推論:綜合帳戶軌有自己專屬的功能(授權書、扣款帳戶、配息設定、定期定額),不是分戶軌的複製。**

#### 改動影響面

| 要改什麼 | 要一起看誰 |
|---|---|
| `OFD220` / `OFD221` 的欄位 | `OFDM221C`(寫)、`OFDM109`(讀幣別,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:461`)、`OFDM551`(讀申購明細,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:434`) |
| `OFD251` 到 `OFD254` 的欄位 | 只有 `OFDM231B` |
| `OFD302` 的欄位 | `OFDM302B`(寫)+ `CLSR002` / `OFDI058` / `OFDI058B` / `OFDB322` / `OFDB323` / `OFDB722` / `OFDI011`(讀) |
| `OFD113` 的欄位 | **三個入口**:`OFDM113`(四眼)、`OFDM221C`(繞過四眼寫)、`OFDM231B`(讀) |
| `OFD605` 的欄位 | `OFDM602A`(活)與 `OFDM602`(已註解) |
| **`OMNIBUS_ID` 的值域** | `OFD221` / `OFD081` 檢核用 `'Y'/'N'`;`OFD113` 用 `'2'/'1'`。改一邊必炸另一邊(§2.5) |

### 8.2 `OFD113`:一張表、三個入口、兩種治理強度

| 入口 | 怎麼寫 | 走不走四眼 |
|---|---|---|
| `OFDM113` | 標準 `BaseEVADaoPO` 主檔維護 | **走** |
| `OFDM221C` 的 `AfterAdd` / `AfterUpdate` | 自組 `INSERT INTO OFD113 … STATUS='301'`,四眼六欄全塞同一人同一時間 | **不走** |
| `OFDM231B` 的 `GetOFD113` | 只讀 | — |

**後果**:同一張表裡會同時存在「走過覆核的設定」與「申購單一存檔就生效的設定」, 而 `STATUS` 欄位看起來都是已核准。從資料上分不出來,只能看 `ALLOT_NO` 有沒有值 (`OFDM221C` 寫的那筆會帶申購書號,`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275`)。

### 8.3 `FSK005`:維護入口死了,下游還在讀

| 角色 | 誰 | 錨點 |
|---|---|---|
| 唯一維護入口 | `FSKM004` | **已死**(§4.5) |
| 共用唯讀 PO | `BasicFSK_PO.GetStkBrkData` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs:117` 與 `:139` |
| 靠它的自訂控件 | `ucStkBrk`、`ucSTK_BRK_GRP`、`ucTrustAgentCode` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucStkBrk.cs` |
| 用那些控件的畫面 | `BMSM001` `BMSM006` `NFDR433` `NFDR435` `OFDM231Ap1` `OFDM243` `OFDM243A` `OFDM385` `OFDB331p0` | — |
| 直接 join 它的 PO | `OFDM068_PO` `OFDM221A_PO` `OFDM243A_PO` `OFDB310_PO` | — |
| 資料庫物件 | view `OFD068A_V02` | `DB/View/OFD068A_V02.SQL` |

**這是本片影響面最廣的一條**:全系統的券商下拉都靠 `FSK005`,而它的維護畫面跑不起來。資料只能靠 DB 直改或別的途徑進去。

### 8.4 `BMS999`:表名前綴與模組歸屬無關

`BMS999` 前綴是 `BMS`,但全庫**只有 `OTAM901` 碰它**(讀與寫)。 `architecture.md §2` 的命名鐵律講的是**畫面代號**推得出六層檔案位置,**表名沒有這條規則**。在本片還有第二個例子:`OFDM251` 的主檔是 `OFD281` 不是 `OFD251`(§2.1)。

### 8.5 `TRP` 對外的兩條線

| 線 | 內容 | 錨點 |
|---|---|---|
| 寄信 | `TRPM101` 收到 `TTP12A` 時直接 `new OFDM053_PO()` 呼叫 `SEND_MAIL_PROC(BMSRow, "07")` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:669-687` |
| 名單 | 名單 SQL 讀 `TRPM101T1`(暫存)+ `BMS001A`(受益人)+ `OFD601`,兩個都是 `INNER JOIN` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729` |

`TRPM101_PO` 裡還有一個方法的簽名收的是**別支畫面的 ModelVDB**: `private int GetMailData(OFDM053ModelVDB model, DbTransaction tran)`(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:710`)。一支 `TRP` 的 PO 直接依賴 `OFD` 的 typed DataSet 與 PO,**兩個模組的 entity 在同一個組件裡所以編得過**, 但這條相依在專案層看不出來,改 `OFDM053` 的 Model 會打到 `TRPM101`。

### 8.6 用到的共用元件

| 元件 | 用途 | 誰用 |
|---|---|---|
| `BasicFSK_PO`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicFSK_PO.cs`) | 券商 / 幣別下拉 | 全庫 |
| `SerialNo.GetSrIdNoForOTA`(無原始碼,從呼叫端反推) | OTA 軌取號 | `OFDM221C` `OFDM231B` `OFDM551` `OFDM554` |
| `CRReportTransfer.TransferFileByte`(無原始碼,從呼叫端反推) | 回傳 `.rpt` byte | 三支 R |
| `UIExcelHelper` + `Microsoft.Office.Interop.Excel` | 用戶端產 Excel | `OTAR901` |
| `VirtualReportFormUtility`(無原始碼,從呼叫端反推) | 一支畫面掛多張報表 | `IJPR611`(掛七組) |
| `CommonExceptionBlocker.HandleBusinessException` | 例外上報 | 幾乎每一支;`OFDM302B.BatchAdd` 的那一行**被註解掉** |

## 附錄 A. 資料表總表

「宣告處」是 PO 的 `xTableMapping` / `TableMapping`;沒有宣告處的是只在 SQL 裡出現的表。

### A.1 本片畫面直接維護的表(21 張,12 組)

主明細組成與宣告錨點見 §2.1,主鍵與欄位數見 §2.2,欄位中文名見 §2.3。 **21 張全部帶四眼欄位**(掃描器實測)。一句話清單:

`TRPARAMS` · `TRP011` · `BMS999` · `FSK005`(維護入口已死) · `OFD109`+`OFD110` · `OFD111`+`OFD112` · `OFD113` · `OFD220`+`OFD221` · `OFD251`+`OFD252`+`OFD253`+`OFD254` · `OFD281` · `OFD302` · `OFD551`+`OFD552` · `OFD554`+`OFD555` · `OFD561`+`OFD562` · `OFD605`

### A.2 只在 SQL 裡出現的表(讀,或由設定驅動)

| 表 | 用途 | 誰讀 / 寫 |
|---|---|---|
| `TRP001` | **申報平台設定檔,存的是 SQL 文字** | `TRPM001` `TRPM101` `TRPI001` |
| `TRP002` | 傳檔紀錄 | `TRPM001`(寫)、`TRPI001`(讀) |
| `TR202` / `TR206` / `TR207` | 收檔 INSERT 語法 / 欄位對照 / SP 名稱 | `TRPM101` |
| `TRPM101T1` | 收檔暫存,寄信名單來源 | `TRPM101` |
| `OFD062` | 境外基金公司 | 四支取 `TRADE_ID`;`TRPI001` / `OFDM302B` 取名稱 |
| `OFD081` | 境外基金主檔 | `OFDM221C` / `OFDM231B` 交易檢核;`OFDM302B` / `TRPM901` 取基金資料 |
| `OFD085` / `OFD086` / `OFD091` | 基金轉換 / 配現可再投資 / ISHARE 額度 | `OFDM113` `OFDM221C` `OFDM231B` |
| `OFD300` / `OFD303` / `OFD304` | 集保匯率 / 結帳控制 / 受益人結餘 | `OFDM221C` `OFDM231B` |
| `OFD601` / `BMS001A` | 電子交易序號 / 受益人基本資料 | `TRPM101` 寄信名單 |
| `FSK003` / `OFD068` | 幣別 / 銷售機構 | `OFDM302B` / `FSKM004` |
| `LOG041` · `BMS926A` · `OFD123A` 等 `EC` 系列 | 電子交易紀錄、稅務居住地、風險屬性 | `IJPR611` |

### A.3 掃描器不會算進來的兩類

1. **設定即程式的四張表**(`TRP001` / `TR202` / `TR206` / `TR207`)不在任何 `xTableMapping` 裡,掃描器不會把它們列為本片的實體表。

2. **14 張收檔媒體格式表**(`TTP019TMP`、`TTP111TMP`、…、`TTP12ATMP`、`TTP12CTMP`)的表名是**執行期從 `TRP001.TableName` 讀出來的**,程式裡完全看不到字面值。它們的存在只能從 `DB/SP/` 的 SP 檔名反推(附錄 B)。

## 附錄 B. SP / Function / Trigger / View

### B.1 本片明確叫到的 SP

| SP | 誰叫 | 在版控 |
|---|---|---|
| `S_OTA_TRPM901_EXE` | `TRPM901` 月報製作 | `DB/SP/S_OTA_TRPM901_EXE.SQL` ✔ |
| `S_OTA_TRPR001_GET` | `TRPR001` 報表 | `DB/SP/S_OTA_TRPR001_GET.SQL` ✔ |
| `S_OTA_OFDM231B_EXE_ADD` | `OFDM231B` 新增沖銷 | `DB/SP/S_OTA_OFDM231B_EXE_ADD.SQL` ✔ |
| `S_OTA_OFDM231B_EXE_MOD` | `OFDM231B` 修改沖銷 | `DB/SP/S_OTA_OFDM231B_EXE_MOD.SQL` ✔ |
| `S_OTA_OFDR552_GET` | `OFDM551` 取契約變更(**報表的 SP 被維護畫面借用**) | `DB/SP/S_OTA_OFDR552_GET.SQL` ✔ |
| `S_OTA_OTAR901_GET` | `OTAR901` 報表 | **不在**(`refcheck-ignore`) |
| `S_TA_IMP_OFD300_RANGE` | `OFDM231B` 取匯率 | **不在**(`refcheck-ignore`) |

### B.2 執行期才決定名稱的 SP

`TRPM101` 用 `string.Format("S_OTA_{0}_GET", strTableSchemaName)` 組 SP 名 (`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:759`),`strTableSchemaName` 來自 `TRP001.TableName`。

`DB/SP/` 底下剛好有 **14 支**符合這個樣式的 SP,可以反推出收檔媒體格式的完整清單:

`S_OTA_TTP019TMP_GET` · `S_OTA_TTP111TMP_GET` · `S_OTA_TTP113TMP_GET` · `S_OTA_TTP114TMP_GET` · `S_OTA_TTP115TMP_GET` · `S_OTA_TTP116TMP_GET` · `S_OTA_TTP117TMP_GET` · `S_OTA_TTP118TMP_GET` · `S_OTA_TTP123TMP_GET` · `S_OTA_TTP124TMP_GET` · `S_OTA_TTP125TMP_GET` · `S_OTA_TTP126TMP_GET` · `S_OTA_TTP12ATMP_GET` · `S_OTA_TTP12CTMP_GET`

其中 `S_OTA_TTP12ATMP_GET` 對應的就是 §4.2 講的、會觸發寄信的 `TTP12A` 媒體。

`TR207.UPDSTP` 指定的入帳 SP 同樣是資料驅動,**程式裡完全看不到名字**,`DB/SP/` 也沒有可靠的樣式可以反推。

### B.3 Function

| Function | 誰用 | 在版控 |
|---|---|---|
| `TA_GETBUSINESSDAY` | `TRPM001` 推下一個傳檔營業日(`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:556`) | **不在**(`DB/Function/` 只有 `F_OTA_GETFNBUSINESSDAY` 等,名字不同) |
| `TTP12ATMP_F1` / `TTP12ATMP_F2` / `TTP12ATMP_P2` | 沒有任何 `.cs` 叫它們;**推測**由 `TR202.INSERTSQL` 或 `TR207.UPDSTP` 在資料層叫 | `DB/Function/` ✔ |

### B.4 View

| View | 誰用 | 錨點 |
|---|---|---|
| `FNDV01` | `OFDM111` 的明細 SQL `LEFT JOIN` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM111_PO.cs:231`;`DB/View/FNDV01.SQL` ✔ |
| `OFD068A_V02` | 不是本片直接用,但它 join `FSK005`,改 `FSKM004` 的表要一起看 | `DB/View/OFD068A_V02.SQL` |

### B.5 Trigger

本片沒有任何程式提到 trigger。

## 附錄 C. 代碼對照

全部從程式反推,**沒有一項有權威來源**(代碼表不在 repo)。

| 分類 | 值 | 語意(反推) | 來源 |
|---|---|---|---|
| `TRP_TYPE` | `'A'` `'T'` `'R'` | 境外申報種類;`'R'` 時畫面才顯示基金公司欄 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:593`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:218-221` |
| `PERIOD` | `'M'` | 月;其他值走營業日 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:226-229` |
| `FILE_STYLE` | `'T'` | 傳檔;其他為收檔 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:594` |
| `OMNIBUS_ID`(`OFD220` / `OFD221` / `OFD081` 檢核) | `'Y'` / `'N'` | 綜合帳戶 / 分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:994` 與 `:1001` |
| `OMNIBUS_ID`(`OFD113`) | `'2'` / `'1'` | 綜合帳戶 / 分戶 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:249` |
| `STATUS` | `'301'` | 已核准(**三碼,不是 `architecture.md §3` 假設的單字元**) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:209`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:282`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275` |
| `OFD113.DATA_ID` | `'2'` | 寫死,語意不明 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275` |
| `ALLOT_PROC_CODE` | `'D'` | 申購作廢 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` |
| `ALLOT_CTL_CODE` / `ALLOT_CTL_CODE_O` | `>= '2'` | 已處理到下單確認之後 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:1036` 與 `:1044` |
| `STOP_ID` | `'Y'` | 契約已終止 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:543` |
| `NAV_LOCK` | `'Y'` / `'N'` | 淨值鎖定(下拉來源是 `YesNoDataSrc`) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:282`;`Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:246` |
| `IJPR611.PrintType` | `'0'` 到 `'6'` | 七式約定書,畫面只給 `'0'` 到 `'4'` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` |
| `EMAIL_CODE_EC` | `'07'` | 核印收檔通知信 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:729`〔客戶特定〕 |
| `MEDIA_NO` | `'TTP12A'` | 核印收檔媒體 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:670`〔客戶特定〕 |
| `UPD_USER` 樣式 | `'WebUser%'` | 網路下單帳號 | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:943`〔客戶特定〕 |

## 附錄 D. 掃描母體與覆蓋率

本片跨四個模組前綴,**不適用 `atlas_scan.py --module` 的單模組覆蓋率**,改成 21 支逐一列表。

| # | 代號 | 專案 | 型別 | PO 基底 | 在 csproj | 本文處置 | 寫在哪 |
|---|---|---|---|---|---|---|---|
| 1 | `TRPM001` | `ATLAS.OTA` | M | 無基底(裸 DAO) | 是 | **已寫(深)** | §4.1 |
| 2 | `TRPM005` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 已寫 | §4.3 |
| 3 | `TRPM101` | `ATLAS.OTA` | M | 無基底(裸 DAO) | 是 | **已寫(深)** | §4.2 |
| 4 | `TRPM901` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 是 | 已寫 | §4.4 |
| 5 | `TRPI001` | `ATLAS.OTA.Query` | I | 無基底(裸 DAO) | 是 | **已寫(深)** | §5 |
| 6 | `TRPR001` | `ATLAS.OTA.Report` | R | 無基底(裸 DAO) | 是(檔名 `TRP001_PO.cs`) | 已寫 | §7.6 |
| 7 | `OTAM901` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.13 |
| 8 | `OTAR901` | `ATLAS.OTA.Report` | R | 無基底(裸 DAO) | 是 | 已寫 | §7.5 |
| 9 | `FSKM004` | `ATLAS.FSK` | M | **`BasicEVAPO`** | 是 | **已寫(深)** | §4.5 |
| 10 | `IJPR611` | `ATLAS.EC.Report` | R | 無基底(裸 DAO) | 是 | **已寫(深)** | §7.3、§7.4 |
| 11 | `OFDM109` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 12 | `OFDM111` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 13 | `OFDM113` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是(**cp950 來源檔**) | 表格帶過 | §4.9 |
| 14 | `OFDM221C` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | **已寫(深)** | §4.6 |
| 15 | `OFDM231B` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | **已寫(深)** | §4.7 |
| 16 | `OFDM251` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.9 |
| 17 | `OFDM302B` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 六層是,**兩支 `.rpt` 否** | **已寫(深)** | §4.11 |
| 18 | `OFDM551` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.10 |
| 19 | `OFDM554` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.10 |
| 20 | `OFDM561` | `ATLAS.OTA` | M | `BaseEVADaoPO` | 是 | 表格帶過 | §4.8 |
| 21 | `OFDM602A` | `ATLAS.OTA` | M | `BaseMultiRowEVADaoPO` | 是 | 表格帶過 | §4.12 |

統計:

| 項目 | 數 |
|---|---|
| 畫面 | 21(M 16 / I 1 / R 3;**B 0**) |
| 專案 | 5(`ATLAS.OTA` 15 · `ATLAS.OTA.Report` 2 · `ATLAS.OTA.Query` 1 · `ATLAS.FSK` 1 · `ATLAS.EC.Report` 1) |
| 深寫 | 8 |
| 表格帶過 | 13 |
| 繼承 `BasicEVAPO`(死路徑) | **1**(`FSKM004`) |
| 不在 csproj 的檔 | **2 支 `.rpt`**(`OFDM302BRPS1` / `OFDM302BRPS2`);**沒有整支畫面不在 csproj** |
| 非 UTF-8 來源檔 | **1**(`OFDM113_PO.cs`,cp950) |
| 實體表 | 21 張(A.1 的 12 組,展開含明細) |
| 版控內 SP | 5;版控外 2;執行期決定名稱的 1 類(14 支可反推) |

本文另外提到但不屬於這 21 支的物件(列出以免被當成漏網): `OFDM221A` `OFDM221B` `OFDM231A` `OFDM302` `OFDM602` `OFDM053` `OFDM068` `OFDM113`(姊妹對照)、 `CLSR002` `OFDI058` `OFDI058B` `OFDB322` `OFDB323` `OFDB722` `OFDI011`(`OFD302` 的下游)、 `BMSM001` `BMSM006` `NFDR433` `NFDR435` `OFDM243` `OFDM243A` `OFDM385` `OFDB331`(`FSK005` 的下游)、 `IPJR607` `IPJR901`(`IJP` 的拼法對照)。

## 附錄 E. 讀本文時要注意的地方

嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 `catch` 吞例外 / 回傳值語意錯誤(本片最大宗)

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM001.GetErrDATA` 的 `catch` 是**空的**,失敗回 0 | **檢核 SQL 一出錯就等於「沒有錯誤」**,傳檔照傳。整支畫面的檢核機制建立在這個回傳值上 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:418-420` | **高** |
| `TRPM101.Execute` 的 `catch` 設了失敗訊息,但後面的 `if (i > 0)` 又把它蓋成「檢核成功」 | `i` 在例外發生前已被寫入影響列數,**例外被吞掉、畫面顯示成功** | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:478-484` 對照 `:494-505` | **高** |
| `TRPM101` 另有 **8 個空 `catch`**(`GetMailData` / `GetResult` / `GetTR207` / `GetTR206` / `GetTR202` / `GetCheckFields` / `GetTableSchema` / `GetTRP001`) | 任一設定取不到都回 0,上層只說「無法取得 XXX」,真正的 DB 錯誤消失 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:742`、`:778`、`:813`、`:849`、`:885`、`:920`、`:975` | **高** |
| `FSKM004.CheckStkBrkData` 的 `catch` 回 `ReturnCode=false`,而 `false` 在這支的語意是「可以刪」 | **SQL 出錯等於放行刪除**(fail-open) | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:180-186` | **高** |
| `OFDM221C.GetOFD113` 的 `catch` 是空的 | 配息設定查不到與查詢失敗無法區分,後續直接走 INSERT 新增一筆 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:222-224` | 中 |
| `OTAR901.DoExp1` 的 `catch` 把所有例外壓成「商業邏輯異常!」,原文只 `Console.WriteLine` | WinForms 沒有主控台,**錯誤訊息完全消失** | `Dev/ATLAS.OTA.Report/Source/UI/ReportUI.OTA/OTAR901.cs:357-362` | 中 |
| `OFDM302B.BatchAdd` 的 `CommonExceptionBlocker.HandleBusinessException(ex)` **被註解掉** | 匯入失敗不進例外處理鏈,只把 `ex.ToString()` 丟給使用者看 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:239-245` | 中 |
| `TRPR001` / `TRPI001` 的查無資料回 `AddResultRow(false, 0, string.Empty)` | 使用者看到失敗但**沒有任何訊息** | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:84-87`、`Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:105-111` | 中 |
| `TRPR001` 的 `catch` 第一行就 `tran.Rollback()`,而 `tran` 在 `try` 內才賦值 | 連線開不起來時 `NullReferenceException` 蓋掉真正的錯誤(與 `architecture.md §3` 記的 `BasicEVAPO.Add` 同型) | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:91` | 中 |

### E.2 死檢核:外殼在、條件永遠不成立

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM302B.BatchAdd` 的 `if (i == -1)` 判刪除結果 | `ExecuteNonQuery` 回的是影響列數,**永遠不是 -1**;刪 0 筆與刪 500 筆都通過 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:198-203` | **高** |
| `TRPM901.BatchAdd` 同一個 `if (i == -1)` | 同上 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:271-276` | 中 |
| `OFDM302B` 的「鎖定後不可改」檢核比 `NAV_LOCK == "1"`,而下拉只給 `Y` / `N` | **這道檢核永遠不會成立**,等於沒有 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:160` 對照 `:246` | **高** |
| `TRPM901` 的「不開放刪除功能」整段被註解,訊息字串還留著 | 讀碼者會以為刪除被擋,**實際是開放的** | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM901.cs:220-231` | 中 |
| `IJPR611` 的 `PrintType` `'5'` / `'6'` 分支(七層都備好、`.rpt` 都在 csproj) | 選項組只有 `'0'` 到 `'4'`,**兩式永遠選不到**,是死碼 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.designer.cs:213-218` 對照 `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:64` | 中 |

### E.3 繞過四眼直接寫主檔

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM302B.BatchAdd`:`DELETE OFD302 WHERE NAV_DATE = ?` 再 INSERT,`STATUS` 寫死 `'301'`、四眼六欄全塞同一人同一時間 | **刪除條件只有淨值日期**,匯入一家基金公司的檔會把當天所有基金的淨值刪光;而且匯入即生效即核准。`OFD302` 的下游包含結算報表與多支批次 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:191-192` 與 `:208-209` | **高** |
| `OFDM302B.Update_NAVLOCK`:直接 `UPDATE OFD302 SET NAV_LOCK, UPDATEID, UPDATEDATE` | 鎖定 / 解鎖不留四眼軌跡,誰解鎖只看得到 `UPDATEID` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:471-478` | **高** |
| `OFDM221C` 的 `AfterAdd` / `AfterUpdate` 自組 `INSERT INTO OFD113 … STATUS='301'` | `OFD113` 有自己的四眼維護畫面 `OFDM113`;**同一張表兩種治理強度**,資料上分不出來 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:275-276` 與 `:353-354` | **高** |
| `TRPM901.BatchAdd`:`DELETE TRP011 WHERE CAL_YM=? AND FH_CD=?` 再 INSERT,`STATUS='301'` | 刪除條件有兩欄比 `OFDM302B` 安全,但同樣繞過四眼 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM901_PO.cs:261-282` | 中 |

### E.4 交易邊界

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM101.Execute` 開了 `tran`,但寫暫存表那行 `ExecuteNonQuery(cmd)` **沒帶 `tran`** | **rollback 收不回已寫進去的暫存資料**;同一支的 `ImportData` 是帶 `tran` 的 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459` 對照 `:646` | **高** |
| `OFDM302B.Update_NAVLOCK` 對同一個 `DbCommand` 連續 `ExecuteNonQuery` **兩次** | 每列多打一次 DB;`i == 0` 的檢核判的是第二次的結果 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM302B_PO.cs:493` 與 `:495` | 中 |
| `TRPR001` 是純查詢卻開交易 | 報表查詢佔用交易,`CommandTimeout = 0` 時可能長時間卡住 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:61` 與 `:68` | 低 |

### E.5 Oracle 三值邏輯與 JOIN

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM221C.GetOFD091`:`OFD221.ALLOT_PROC_CODE <> 'D'` **沒有 `NVL`** | 處理代碼是 NULL 的申購不計入已用額度,**ISHARE 額度被低估**,該擋的申購放行 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:901` | **高** |
| `OFDM109.GetCRNCY_CD`:`CRNCY_CD <> 'TWD'` 沒有 `NVL` | 幣別為 NULL 的部位被靜默濾掉,幣別下拉少選項 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:466` | 中 |
| `TRPI001`:`INNER JOIN TRP001` | 設定被刪或改名,對應的**歷史傳檔紀錄整筆消失**,無提示。同一段 SQL 的下一行卻用了 `LEFT JOIN` | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:81` | **高** |
| `TRPM101.GetMailData`:`TRPM101T1 INNER JOIN BMS001A INNER JOIN OFD601` | 受益人資料或電子交易序號缺一,**這個人就收不到核印通知信**,而且沒有提示 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:718-729` | **高** |
| `TRPI001` 用「名稱欄是不是 NULL」反推「有沒有指定基金公司」 | `FH_CD` 有值但 `OFD062` 查不到時,畫面顯示「所有境外基金公司」——**錯的資料長得像對的** | `Dev/ATLAS.OTA.Query/Source/PO/QueryPO.OFD/TRPI001_PO.cs:68-71` | 中 |

### E.6 邊界與索引

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM101` 的「欄位未定義在媒體格式」檢核寫成 `Schemarow.Length == 0 && intRow == 1` | **第 2 筆以後出現未定義欄位會直接 `IndexOutOfRangeException`**,訊息變成無意義的「例外錯誤, 請檢查」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:248` 對照 `:267` | **高** |
| `TRPM101` 的日期檢核用 `Substring(0,4)` / `(4,2)` / `(6,2)` | 長度不足 8 的字串直接丟例外,同樣被吃成「例外錯誤」 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:329` | 中 |
| `TRPM001_ExecuteDataLoad` 直接取 `vdb.UIView.TRP001[0]` | 查詢 0 筆時 index out of range | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:270` | 中 |
| `TRPM001.ExcuteSQLandLoadData` 在 `Result.Count == 0` 的分支裡還去讀 `Result[0].ReturnMessage` | 要報錯的時候先自己丟 index out of range | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:512-516` | 中 |
| `OFDM231B` 的 UI 兩處 `Select("FUND_ID <> ''")[0]` 沒有長度檢查 | 明細全空時例外 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM231B.cs:487-488`、`:498-499` | 中 |
| 五支畫面的 `do { 取號 } while (IsExistByData(...))` **沒有次數上限** | 撞號或 `IsExistByData` 恆真時無窮迴圈,卡住整條遠端執行緒(與 `architecture.md §3` 記的 `CASM001_PO` 同型) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM221C_PO.cs:162-166`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:141-182` | 中 |

### E.7 SQL 字串串接與寫死值

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM251` 的查詢條件把使用者輸入串進 `LIKE`:`RECORD_DATE LIKE '" + Row.Value + "%'` | **本片唯一一處使用者輸入直接進 SQL**;值含單引號就壞掉或被利用 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM251_PO.cs:182` | **高** |
| 八支 `OFDM*` 的明細 SQL 都用字串串接接書號 | 書號由伺服器產生,注入風險低,但與同一支裡的參數化寫法不一致 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM109_PO.cs:256`、`Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:434`、`:580`、`:631` | 低 |
| `IJPR611` 用字串串接組 `DataTable.Select` 過濾式 | 銀行名稱含單引號就丟 `SyntaxErrorException` | `Dev/ATLAS.EC.Report/Source/PO/ReportPO.EC/Oracle/IJPR611OracleDao.cs:586` | 中 |
| 傳檔落地路徑有**兩個不同的寫死預設值**:UI 端 `C:\境外傳檔\`、SQL 端 `'C:\'` | 同一個「沒設定」情境,兩邊給出不同的路徑 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:358-360` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:584` | 中 |
| `TSCD_RPT_PATH=` 這個前綴在三個地方各寫一次 | 改字面值要同時改三處,對不上時是例外不是訊息 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM005_PO.cs:137`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM005.cs:192`、`Dev/ATLAS.OTA/Source/UI/UI.OTA/TRPM001.cs:356` | 中 |
| `RESERVE_FIELD_SW` 欄名寫死在逗號轉換邏輯裡 | 媒體格式改欄名,轉換規則就失效 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:259-264` | 低 |
| `TTP12A` / `'07'` / `'WebUser%'` 寫死 | 換站台要逐一確認 | §附錄 C〔客戶特定〕 | 中 |

### E.8 成對路徑只改一邊

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `IJPR611` 的預覽有 `Parameters.Clear()`、列印**沒有** | 先預覽再列印,參數被加第二次 | `Dev/ATLAS.EC.Report/Source/UI/ReportUI.EC/IJPR611.cs:157` 對照 `:170-207` | 中 |
| `TRPM101` 的 `Execute` 不帶 `tran`、`ImportData` 帶 | 同一支畫面兩條路徑的交易語意不同 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:459` 對照 `:646` | 高(已列 E.4) |
| `OFDM551` 與 `OFDM554` 各寫一份 `GetOFD562`,SQL 不同 | 改扣款帳戶取數邏輯要記得兩邊 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:385` 對照 `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM554_PO.cs:455` | 中 |
| `OFDM231B` 的 `OFD253` 分支,region 標題複製自 `OFD252` 沒改 | 讀碼會以為在看 `OFD252`;`case` 的註解是對的、`region` 是錯的 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM231B_PO.cs:437` 對照 `:438` | 低 |

### E.9 檔案與建置

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `FSKM004_PO` 繼承 `BasicEVAPO` 且不覆寫 `Add` / `Update` / `Delete`,`BeforeSelect` 第一行就用 `dbTA` | 依 `architecture.md §3`,**按查詢就 NRE**,整支畫面不可用;而 `FSK005` 的下游遍布全庫 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:29` 與 `:60` | **高** |
| `FSKM004_PO` 的活程式裡還有 T-SQL 的 `SUBSTRING(...)` | 就算連線修好,這段在 Oracle 上也是語法錯誤 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:114` | **高** |
| `FSKM004_PO` 1,272 行裡 950 行是被 `/* */` 包起來的上一代實作 | 讀碼成本;搜尋命中大量死碼 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:321-1270` | 中 |
| `FSKM004_PO` 最後一行是 `}//end namespace Adapterusing System;` | 兩段文字黏在一起,顯示這個檔曾被截斷或貼壞 | `Dev/ATLAS.FSK/Source/PO/PO.FSK/FSKM004_PO.cs:1272` | 低 |
| `FSKM004_Ctl` **沒有繼承 `BaseController`**,每個方法自己 `new` PO | 不走 `DataAccessPool`、沒有 `InitializeVDBTypes()`,全片唯一 | `Dev/ATLAS.FSK/Source/Control/Control.FSK/FSKM004_Ctl.cs:13` 與 `:36-41` | 中 |
| `OFDM302BRPS1.rpt` / `OFDM302BRPS2.rpt` 在一個**沒有 csproj 的資料夾**裡,既不是 `EmbeddedResource` 也沒有 PostBuild xcopy | **兩張報表在現行建置流程下不會被部署**,而 UI 用名字去要它們 | `Dev/ATLAS.OTA/Source/UI/UI.OTA/OFDM302B.cs:342` 與 `:396` | **高** |
| `TRPR001_PO` 住在檔名少一個 `R` 的 `TRP001_PO.cs` | 編得過、跑得動,但依檔名比對的工具全部誤判「缺 PO」 | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:2` 與 `:31` | 中 |
| `OFDM113_PO.cs` 是 **cp950 編碼**,全片唯一 | 用 UTF-8 一刀切的工具讀它會出亂碼;訊息字串在版本比對時也會誤判 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM113_PO.cs:235` | 中 |
| `TRPM101_PO` 有一個方法的參數型別是**別支畫面的 ModelVDB**(`OFDM053ModelVDB`) | `TRP` 的 PO 直接相依 `OFD` 的 typed DataSet 與 PO,專案層看不出來 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:710` | 中 |
| `TRPM001_PO` 與 `TRP001_PO` 的介面 XML 註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製殘留,與實際用途完全無關 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:23` 與 `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:22` | 低 |
| `TRP001_PO` 同時 `using System.Data.OracleClient;` 與 `Oracle.ManagedDataAccess.Client;` | 前者是已淘汰的內建 provider | `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/TRP001_PO.cs:11` 與 `:16` | 低 |

### E.10 商業規則不在程式裡

| 事實 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `TRPM001` 的檢核與異動 SQL 全部存在 `TRP001` 的 13 個欄位裡,程式只負責照跑 | **讀程式讀不出任何一條傳檔規則**;改規則不用改程式、也不會進版控 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM001_PO.cs:557-582` | **高** |
| `TRPM101` 連 INSERT 語法都存在 `TR202.INSERTSQL`,取出時要用三層 `REPLACE` 反跳脫 | 跳脫規則沒有任何文件;改 `TR202` 的人必須知道 | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:868` | **高** |
| 收檔用的表名與 SP 名都是執行期從 `TRP001` / `TR207` 讀出來的 | 程式裡看不到 14 張媒體格式表的名字,只能從 `DB/SP/` 的檔名反推(附錄 B.2) | `Dev/ATLAS.OTA/Source/PO/PO.OTA/TRPM101_PO.cs:759` | 中 |

### E.11 標「假設」的地方一覽

| # | 假設 | 依據 | 在哪 |
|---|---|---|---|
| 1 | 四個前綴的業務範圍 | 表名、`msdata:Caption`、彈出視窗標題、報表中文名 | §0.1 |
| 2 | `OFDM221B` 是 `OFDM221A` 的子視窗或殘留 | 只有 UI 一層,不在畫面代號母體內 | §0.3 |
| 3 | 傳檔週期由 `TRP001.PERIOD` 決定(`'M'` 為月) | 程式對 `'M'` 走 `ADD_MONTHS`、其他走 `TA_GETBUSINESSDAY` | §1.5 |
| 4 | `'301'` 是 `EVAStatusCode.ApproveAdd` 的實際字面值 | 四支不同模組都在「繞過四眼直接寫入」時用它 | §2.5 |
| 5 | `IJPR611` 的第 6、7 式曾開放過或是預留 | 註解把 7 種寫齊、七層都備好,只有 Designer 少兩個選項 | §7.3 |
| 6 | `TTP12ATMP_F1` / `F2` / `P2` 由 `TR202` / `TR207` 在資料層叫 | 沒有任何 `.cs` 引用它們,但名字與 `TTP12A` 媒體一致 | 附錄 B.3 |
| 7 | `OFDM602A` 是 `OFDM602` 的 Oracle 世代替代品 | 兩者讀寫同一張 `OFD605`,而 `OFDM602_PO` 整個類別被註解 | §8.1 |
| 8 | `FSK005` 只能靠 DB 直改或別的途徑維護 | `FSKM004` 這個唯一入口按查詢就 NRE | §4.5 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `TRP` 6 支、`OTA` 2 支、`FSK` 1 支、`IJP` 1 支、`ATLAS.OTA` 裡的 `OFD` 11 支,合計 21 支。 |

由 build_doc.py v2.0.0 於 2026-09-15 20:02 產生 · 標題 147 · 圖 5 · 表格 98 · 程式錨點 372 · § 連結 73 · 引用檢查：畫面 50（缺 0） · Table 40（缺 0） · SP 19（缺 0） · Function 4（缺 0） · View 2（缺 0） · 結果集 5（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/rsp.md
============================================================

# ATLAS RSP 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、§6.3(`RSPB008_Service`)、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、Designer 內的標籤文字與訊息字串**推測**,待選單表 / 對照表回填。畫面中文名不在版控內,本文的畫面名稱一律標「推測」。 ⚠ **〔客戶特定〕**:落地路徑 `C://Vendor//WindowService//RSPB008//`、郵件群組 `OFD681.SEND_TYPE = '6'`、員工註記 `EMP_CD = '1'`、扣款轉申購日固定 6 / 16 / 26 日、郵局總行代碼 `700`、促銷活動 `86A03` 為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`COD009`(主檔在 COD)、`RSP006A`(BMS / OFD 也讀)、`OFD272A`(BMS / OFD 也掛)、`OFD374A`(主檔在 DSM)四組表跨界,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、SQL 與 Oracle 現況看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、WindowsService 看 `architecture.md §8`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:RSP 管「定期定額」這種契約的一生——客戶簽了約要每個月自動從銀行扣款買基金,這條線從立約、變更、每期扣款、核印、單位數計算,一路到停利出場與契約終止,全部在這個模組裡。**

「RSP」三個字母在 repo 內找不到定義,**不要猜**。但主表 `RSP005A` 的主鍵欄位 `RSP_NO` 的 `msdata:Caption` 就是「契約書號」,明細 `RSP006A` 有「扣款金額」「扣款日1/2/3」「契約手續費率」,批次畫面的標籤是「契約扣款日期」「實際扣款日期」。推測依據如下表,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `RSP_NO`=「契約書號」、`RSP_AMT`=「扣款金額」、`RSP_ALLOT_DAYS1`=「扣款日1」、`SER_FAIL_TIMES`=「連續扣款失敗次數」、`FIRST_SUS_DATE`=「首次扣款成功日期」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:28`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:35` |
| 變更檔的前後對照欄 | `RSP007A` / `RSP013A` 整張表就是 `BEF_xxx` / `AFT_xxx` 成對,例如「變更前扣款行」「變更後扣款行」「變更前扣款金額」「變更後扣款金額」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:189`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:584` |
| 批次訊息字串 | 「執行完成 本次有更新失敗資料,請執行(RSPR038)定期定額契約異動資料查核表」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:104` |
| 批次訊息字串 | 「此契約扣款日期已執行過168循環定額投資扣款轉申購產生作業」「此契約扣款日期已執行過定期定額投資停利計算作業」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:249`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:212` |
| 母子基金欄位名 | `RSP061A` 是「母子基金設定書號」「最低申購金額」「最低轉申購金額」,`RSP062A` 是「母基金代碼」,`RSP063A` 是「子基金代碼」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:93`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:183` |
| 停利欄位名 | `RSP041A` 是「停利轉申購契約書號」「約定停利點」「停利機制」「轉申購手續費率」 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17` |
| 服務落地檔 | `C://Vendor//WindowService//RSPB008//RSPB008_yyyyMMdd.txt`,內容寫「處理資料筆數」 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:145` |

本文一律用「定期定額」描述它的範圍,這是從上表推出來的,**不是官方名稱**。

五條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 一般定期定額契約 | 客戶簽約買哪幾檔基金、每檔扣多少、每月哪幾天扣、手續費率與促銷優惠;之後所有變更(換銀行、改金額、暫停、終止)走變更書 | `RSPM004` `RSPB020` `RSPM005` `RSPB008` | `RSP005A`+`RSP006A`(契約)、`RSP007A`+`RSP013A`(變更) |
| B 每期扣款作業 | 產生扣款檔 → 送印鑑核印 → 銀行回覆成功 / 失敗 → 算單位數 → 結轉 → 出錯時淨值回復 → 連續失敗就終止契約 | `RSPB009` `RSPB010` `RSPB011` `RSPB015` `RSPB016` `RSPB018` `RSPB019` `RSPB052` | `RSP008`、`RSP008A`、`RSP008AA`、`CTL006A` |
| C 168 循環定額投資(母子基金) | 先設定哪些母基金可配哪些子基金,再簽 168 契約,每月 6 / 16 / 26 日把母基金贖回轉申購子基金,達停利點就出場 | `RSPM020` `RSPM021` `RSPB025` `RSPM022` `RSPB023` `RSPB021` `RSPB022` `RSPB024` | `RSP061A`/`RSP062A`/`RSP063A`、`RSP070A`/`RSP071A`/`RSP072A`、`RSP073A`/`RSP074A`/`RSP075A` |
| D 定期定額停利轉申購 | 幫既有定期定額契約掛一個「漲到幾成就自動贖回轉申購另一檔」的設定,變更走另一張書號 | `RSPM041` `RSPM042` `RSPB041` `RSPB042` | `RSP041A`、`RSP042A` |
| E 員工 / 員眷契約費率 | 員工離職後,把他與眷屬名下定期定額契約的手續費率改回一般費率 | `RSPM037` | 讀 `COD009`+`COD010`+`BMS001`,只寫 `RSP006` 的 `RSP_CNRT_FEE_RATE` |

另外 31 支 R 報表 / 39 個 `.rpt` 掛在這五條線上(§7)。

### 0.2 這模組最反直覺的六件事

**(1) 17 支「B」畫面裡有兩支根本不是批次,是維護畫面。**

| 畫面 | 基底類別 | 實際行為 |
|---|---|---|
| `RSPB020` | `xMaintainForm` | 跟 `RSPM004` 共用同一組 `RSPM004_Master` / `RSPM004_Detail`,走完整四眼;用來改契約的業務欄位(銷售機構 / 通路 / 推薦人 / 員工 / 介紹人 / 郵局經辦區),存檔時連動更新 `OFD220A` `OFD221A` `OFD306A` |
| `RSPB025` | `xMaintainForm` | 跟 `RSPM021` 共用 `RSPM070_Master` / `RSPM070_Detail`,同樣走四眼 |

錨點:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:23`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB025.cs:24`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:554-610`。其餘 15 支都是 `xOneStepProcessForm`(例:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB009.cs:15`)。**看到 B 就當批次會踩雷**,`architecture.md §6.4` 講的「B 跟 I 是同一份程式碼」在這兩支不成立。

**(2) `RSPM037` 掛的主檔是 `COD009`(員工主檔),但它一個字都沒寫進去。**

`RSPM037_PO` 的 `MasterTable` 在三個方法裡被換三次:`COD009` → `RSP005` → `RSP006`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250`)。`COD009` 只是查詢驅動——輸入「離職日期(起 / 迄)」或「離職員工代碼」,撈出離職員工與其員眷,再帶出他們名下的定期定額契約。**唯一的寫入是 `UPDATE RSP006 SET RSP_CNRT_FEE_RATE`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:271-276`)。掃描母體把它列成「`COD009` 主檔於 `RSPM037`」是照 `MasterTable` 宣告推的,與實際行為不符,詳見 §4.6 與 §8.1。

**(3) `RSPM037` 是整個模組唯一沒有移轉到 Oracle 的畫面。**

同一支 PO 內同時出現 `ISNULL(...)`、`CONVERT(NVARCHAR, x, 111)`、`GetDate()`、方括號識別字、`f_GetAgent()`、`SqlDbType.NVarChar`,而且查的是**沒有 A 尾碼的舊表名** `RSP005` / `RSP006` / `BMS001` / `OFD019` / `OFD071` / `OFD072` / `OFD081` / `OFD199`。其餘 24 支 PO 全是 `[PODbType(DbServerType.Oracle)]` + `OracleDbType` + `NVL`。錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:64`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:152`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:279`。對照 `architecture.md §4.6`(執行期是 Oracle-only)。**假設**:這支畫面在 Oracle 上跑不起來。依據是上述語法在 Oracle 皆非法、且 `RSP005` / `RSP006` 不在本模組任何其他程式的表名清單裡(其他 24 支一律用 `RSP005A` / `RSP006A`)。無法實測,不敢斷言。

**(4) `RSPB008` 有專屬 WindowsService,而且它不是 Remoting 客戶端。**

`architecture.md §8.4` 說四支服務「都是 Remoting 的客戶端,一樣透過 `_Pxy` 打到伺服端,不直接碰資料庫」。**`RSPB008_Service` 不是。** 它直接 `new RSPB008_Ctl()`(Control 層),csproj 參考的是 `Control.RSP` 而不是 `FormProxy.RSP`,全專案 `RemotingConfiguration` 出現 0 次,而它的 `App.config` 自帶五組 `connectionStrings`。錨點:`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:47`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/WindowsService.RSPB008.csproj:116-119`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:72-78`。對照組 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50`、`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:82`(有 `RemotingConfiguration.Configure`,用 `OFDB600_Pxy`)。詳見 §6.3。

**(5) 同一顆「執行」按鈕,畫面按下去會先擋「還有沒覆核的資料」,服務排程跑則不會。**

`RSPB008` 的 UI 在 `BeforeExecuteButtonClicked` 會先呼叫 `CheckStatus`,有未覆核資料就進 `ValidateErrList` 擋下(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:34-53`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:105-115`)。`RSPB008_Service` 的 `_timer_Elapsed` **直接呼叫 `ctl.Execute(view)`,沒有任何 `CheckStatus`**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:40-73`)。同一條卡控在兩條入口只有一條掛著。

**(6) 「執行成功 / 失敗」的判斷散成四種寫法。**

| 寫法 | 誰 | 錨點 |
|---|---|---|
| SP 的 `MSG` OUT 參數為 NULL 才算成功 | `RSPB021` `RSPB022` `RSPB023` `RSPB041` `RSPB042` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:73-83` |
| 讀 RefCursor 第一列的 `UpdateTimes` / `CORRECT` 欄 | `RSPB008` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:85-110` |
| `ExecuteNonQuery` 的回傳筆數 | `RSPB011` `RSPB015` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:176-190` |
| **硬把回傳筆數蓋成 1,失敗分支永遠不會走** | `RSPM037` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-284` |

最後一條是真缺陷,見附錄 E。

### 0.3 不管什麼

以下**不在** RSP 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料的正規維護 | BMS | `BMS001` 在 RSP 只有一處寫入,而且限定「簡易開戶」情境;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:632-809` |
| 員工主檔、員眷、離職日 | COD | `COD009` / `COD010` 只被 `RSPM037` join,零寫入;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:92-111` |
| 基金主檔、淨值、幣別小數位 | OFD | `OFD081` / `OFD081V` 只讀;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:230-233` |
| 銷售機構 / 通路 / 推薦人主檔 | OFD | `f_GetAgent()` / `OFD071` / `OFD072` 只讀;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:181-190` |
| 結帳與關帳控制 | OFD | `OFD303A` 只用來判斷「買回 / 申購關帳是否已結轉」;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119-130` |
| 銀行 / 總行對照與郵局限額 | OFD | `OFD019.DAY_LMT_AMT` 的檢核整段被註解掉,改寫在 SP 裡;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286` |
| 印鑑核印的實際往返 | OFD | `OFD701` 在 RSP 只被讀 / 被判狀態;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| 受益人歸屬業務員的正規維護 | DSM | `OFD374A` 的維護入口在 `DSMM060`(`dsm.md §8`);RSP 只在簡易開戶時補寫一筆,見 §8.4 |
| 缺件主檔的正規維護 | OFD / BMS | `OFD272A` 在 RSP 是掛在契約底下的明細;`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80` |
| **每期扣款的錢怎麼算出來的** | **版控外的 SP** | 13 支 B 畫面全部只負責呼叫 SP,算式在 DB 裡;例 `s_TA_RSPB008_Excute_M`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:65`)、`S_TA_RSPB021_EXCUTE`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:54`) |
| 郵件實際寄送 | 共用 `GenXMLHelper` | `email.Gen49(...)` 只負責產 XML 丟出去;`Dev/ATLAS.RSP/Source/Control/Control.RSP/RSPB008_Ctl.cs:239-240` |

掃描母體列的 SP / Function / Trigger / View 全部是 0 筆——**不是沒有,是全部不在版控內**(附錄 B)。

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 櫃檯 / 作業人員 | 收到契約書輸入 `RSPM004`;客戶要改就開 `RSPM005`;168 開 `RSPM021`、停利開 `RSPM041` | 四支都是標準 `xMaintainForm`,權限在程式內看不到 |
| 覆核人員 | 四眼的 V / A 兩段;`RSP007A` `RSP073A` `RSP042A` 三張變更檔沒覆核完,對應批次就不給跑 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:109-112`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:108-111` |
| 每日作業排程人員 | 依序跑 `RSPB009` → `RSPB010` → `RSPB011` / `RSPB015` → `RSPB016` → `RSPB018`;出錯跑 `RSPB019` 回復 | 訊息字串直接寫出順序:「執行成功!請先從(RSPB016)計算作業開始;如有淨值變動,請先執行淨值回復作業!」`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:92` |
| 排程本身(無人值守) | `RSPB008_Service` 每 60 秒比對一次 `CTL016.RSP_PROC_TIME`,到點就用 `UserID = "AutoJob"` 跑一次契約變更生效 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:42`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:52` |
| 人事 / 作業窗口 | 員工離職後開 `RSPM037` 調整其名下契約手續費率 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:74-114`,查詢條件只有「離職日期起迄」與「離職員工代碼」 |
| 通知信收件人 | `OFD681` 裡 `SEND_TYPE = '6'` 那群人,`RSPB008` 服務每次跑完都寄 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:343-344` |

**本模組所有畫面的功能權限都不在程式碼裡**,由 PTPF 平台庫決定(`architecture.md §3.7`)。報表端也沒有任何白名單或員編寫死的權限判斷(§7.3)。

### 0.5 全域開關

| 開關 | 放哪裡 | 影響 | 錨點 |
|---|---|---|---|
| `formstyle = OneStep` | `UI.RSP/App.config` | 15 支 B 畫面宣告成一步式;`RSPB020` / `RSPB025` / 8 支 M 不宣告 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:35`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:85-92` |
| `mastertable` + `pkey` | `UI.RSP/App.config` | 宣告每支維護畫面的主檔 DataTable 與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:150`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:158`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:166`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:185`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:199`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:207` |
| `ugrdResult` 的 `column` 白名單 | `UI.RSP/App.config` | 查詢結果 grid 顯示哪些欄位 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:152`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:178`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:186` |
| `AUTO_BELONG_EMP` | 系統參數表(`ServerBizUtility.GetSysParam()`) | `= 'Y'` 才會在簡易開戶時補寫 `OFD374A`;`= 'N'` 就不寫。**這是 RSP 碰 DSM 主檔的唯一開關** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-698` |
| `CTL016.RSP_PROC_TIME` | 資料庫 | `RSPB008_Service` 的排程時刻(`HHmm`);取 `rownum = 1`,**全表只認第一列** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302` |
| `CTL014` 預設值 8 組 | 資料庫 | 簡易開戶時 `TRAN_FAX_CD`(081)、`OMNIBUS_ID`(065)、`JOINT_ACC_CD`(066)、`PD_CODE`(069)、`PP_CODE`(070)、`BF_WEB_CD`(078)、`TRAN_PAY_WAY`(079)、`REJ_POST`(083)的來源 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684` |
| `ProductId.TaOfd` / `ProductId.TaNfd` | 授權設定 | 有沒有建置境外 / 境內基金事務系統,決定簡易開戶帶哪組國別碼 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:649-671` |
| 服務落地路徑 | **寫死在程式裡** | `C://Vendor//WindowService//RSPB008//`,不是設定檔 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114`〔客戶特定〕 |
| 服務 timer 間隔 | **寫死在建構子** | `60000` 毫秒 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:25` |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] RSP 模組全景：一般契約、扣款作業、168 循環定額、停利轉申購、員工費率與報表五條線
圖中文字:① 一般定期定額契約：立約 → 變更 → 生效 / RSPM004 / 契約 RSP005A/RSP006A / RSPM005 / 變更書 RSP007A/RSP013A / RSPB008 / 變更生效 SP / RSPB008_Service / 排程 CTL016 / RSPB020 / 只改業務欄位 四眼 / ② 每期扣款作業：八支批次串成一條鏈 / RSPB009 / 產生扣款 RSP008 / RSPB010 / 送件 指定淨值日 / RSPB011 RSPB015 / 扣款回覆確認 / RSPB016 RSPB018 / 單位數計算 結轉 / RSPB019 / 淨值回復 RSP008AA / RSPB052 / 連續失敗終止契約 / ③ 168 循環定額投資：母基金贖回轉申購子基金 / RSPM020 / 母子基金白名單 / RSPM021 RSPB025 / 契約 RSP070A-072A / RSPM022 RSPB023 / 變更 RSP073A-075A / RSPB021 B022 B024 / 轉申購 停利 寄信 / ④ 定期定額停利轉申購 / RSPM041 / 停利設定 RSP041A / RSPM042 / 停利變更 RSP042A / RSPB041 / 變更生效 / RSPB042 / 停利計算 LOG109A / ⑤ 員工契約費率 + 報表 / RSPM037 / 離職員工 只改費率 / COD009 COD010 / 員工與員眷 唯讀 / RSPR008 ~ RSPR071 / 31 支 全走版控外 SP / 39 個 rpt 全對得上 / 另一支只出 Excel
```

*圖:圖 1 RSP 全景。橘框=維護入口或關鍵批次;白框=一般批次;橘虛框=含寫死值或未移轉 Oracle〔客戶特定〕;黑框=唯讀或無原始碼。五條線之間幾乎沒有程式呼叫,全靠表相連——① 的 RSP005A/RSP006A 是 ②④⑤ 的共同地基。*

五條線之間幾乎沒有程式呼叫,全靠表相連。線 A 的 `RSP005A` / `RSP006A` 是所有東西的地基:線 B 的扣款檔從它產、線 D 的停利契約用 `RSP_NO` 掛在它身上、線 E 改的是它的明細費率。線 C(168)自成一套表,跟線 A 只透過 `BF_NO` 與基金代碼相關。

### 1.2 資料表關係

21 張表分成六組,主明細配對與主鍵組成見 §2.1 / §2.2。要先記住三件事:

1. **三組「主檔 + 變更檔」是平行結構**:`RSP005A`+`RSP006A`(契約)對 `RSP007A`+`RSP013A`(變更);`RSP070A`+`RSP071A`+`RSP072A`(168 契約)對 `RSP073A`+`RSP074A`+`RSP075A`(168 變更);`RSP041A`(停利)對 `RSP042A`(停利變更)。變更檔一律是 `BEF_xxx` / `AFT_xxx` 成對欄位,**變更當下不動主檔**,要等對應批次跑過才生效。

2. **扣款那組(`RSP008` / `RSP008A` / `RSP008AA`)不是主明細關係**,是同一批扣款資料在不同階段的三張表,而且沒有任何一支 M 畫面維護它們。

3. **`RSP061A` / `RSP062A` / `RSP063A` 是設定檔不是交易檔**,一張 `RE_RSP_NO`(母子基金設定書號)底下掛 N 個母基金與 N 個子基金,是多對多的白名單。

### 1.3 主要維護畫面的四眼與卡控順序

八支 M 畫面(加上偽裝成 B 的 `RSPB020` / `RSPB025`,共十支維護畫面)全部繼承四眼引擎,但**卡控幾乎全部押在 UI 層**:

| 層 | 誰在這一層擋 | 說明 |
|---|---|---|
| UI `validatorManager1` | 十支都有 | 欄位必輸 / 格式,框架做 |
| UI `DoValidate()` | 十支都有,長度差很多 | `RSPM004` 這一支就 228 行(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2195-2418`) |
| PO `BeforeAdd` / `BeforeUpdate` | **只有 `RSPM004` / `RSPB020` / `RSPM005`** | 其餘七支的 PO 只掛取數事件,伺服端沒有第二道防線 |
| 四眼引擎 | 十支都走 | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:205`,細節看 `architecture.md §3` |
| 批次二次驗證 | `RSPB008` / `RSPB023` / `RSPB041` | 變更檔還有非「已覆核」狀態就不給生效 |

**繞過 UI 就等於沒有卡控**,這條在 RSP 特別嚴重:`RSPM004` 的郵局每日扣款限額檢核整段只存在於 UI(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2253-2344`),而 PO 端同名的 `CheckDayLmtAmt` 被整段註解掉(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:184-285`)。

### 1.4 批次 / 報表資料流

一日扣款作業的鏈(依訊息字串與各 PO 的檢核對象推):

| 順序 | 畫面 | 動作 | 主要表 |
|---|---|---|---|
| 1 | `RSPB009` | 產生 / 重作 / 刪除扣款資料 | `RSP005A` `RSP006A` → `RSP008` `RSP008A`,`CTL006A` 控制 |
| 2 | `RSPB010` | 指定實際扣款日與淨值日、送件 / 重新送件 | `RSP008` |
| 3 | `RSPB011` | 扣款回覆逐筆確認(成功 / 失敗 / 扣款中) | `RSP008A` |
| 4 | `RSPB015` | 扣款回覆確認,依扣款行與核印方式小計 | `RSP008A` |
| 5 | `RSPB016` | 單位數計算 | `RSP008A` |
| 6 | `RSPB018` | 結轉,必要時產法人公告警示表 | `RSP008A`、`OFD303A.RSP_CTL_CODE` |
| 例外 | `RSPB019` | 淨值回復,回復後要從 `RSPB016` 重跑 | `RSP008AA` |
| 收尾 | `RSPB052` | 連續扣款失敗達門檻的契約終止 | `RSP005A` `RSP006A` |

168 那條:`RSPB021`(扣款轉申購產生)→ `RSPB022`(停利計算)→ `RSPB024`(產 Email 資料)。停利那條:`RSPB042`(停利計算)。變更生效那三支:`RSPB008`(一般契約)、`RSPB023`(168 契約)、`RSPB041`(停利契約)。

報表全部走版控外的 SP + Crystal Report,取數與畫面不共用任何 PO(§7)。

### 1.5 一日作業泳道

| 時間(推測) | 誰 | 做什麼 | 動到哪張表 |
|---|---|---|---|
| 日間 | 櫃檯 | `RSPM004` / `RSPM005` / `RSPM021` / `RSPM022` / `RSPM041` / `RSPM042` 輸入與送審 | `RSP005A` `RSP006A` `RSP007A` `RSP013A` `RSP070A` `RSP071A` `RSP072A` `RSP073A` `RSP074A` `RSP075A` `RSP041A` `RSP042A` |
| 日間 | 覆核 | 四眼 V / A | 同上的 `Status` |
| `CTL016.RSP_PROC_TIME` 指定時刻 | `RSPB008_Service` | 契約變更生效(無人值守) | `RSP007A` `RSP013A` → `RSP005A` `RSP006A` |
| 扣款日前 | 作業 | `RSPB009` 產生扣款資料 | `RSP008` `RSP008A` `CTL006A` |
| 扣款日 | 作業 | `RSPB010` 送件 → 銀行回覆 → `RSPB011` / `RSPB015` 確認 | `RSP008` `RSP008A` |
| 扣款日 +N | 作業 | `RSPB016` 算單位數 → `RSPB018` 結轉 | `RSP008A`、`OFD303A` 控制碼 |
| 6 / 16 / 26 日 | 作業 | `RSPB021` 168 扣款轉申購 → `RSPB022` 停利計算 → `RSPB024` 寄信 | `RSP070A` `RSP071A` `RSP072A`、`LOG094A` `LOG095A` |
| 每日 | 作業 | `RSPB042` 定期定額停利計算 | `RSP041A`、`LOG109A` |
| 出錯時 | 作業 | `RSPB019` 淨值回復,再從 `RSPB016` 重跑 | `RSP008AA` |

## 2. 資料模型

```text
[圖] RSP 二十一張表的主明細配對、三組變更檔的平行結構,以及外部唯讀表
圖中文字:三組「主檔 + 變更檔」平行結構:變更當下不動主檔,要等批次 / RSP005A / PK 契約書號 / RSP006A / + 契約序號 / RSP007A / PK 變更書號 / RSP013A / + 變更序號 / RSP070A / PK 契約書號 / RSP071A RSP072A / 子基金 / 申購書 / RSP073A / PK 變更書號 / RSP074A RSP075A / 子基金 / 申購書 / RSP041A / PK 停利書號 / (無明細) / 一張設定一列 / RSP042A / PK 停利異動書號 / RSPB041 生效 / 比對 TX_DATE / 扣款檔三兄弟:不是主明細,是同一批資料的三個階段 / RSP008 / 產生 / 送件 / RSP008A / 回覆 / 計算 / 結轉 / RSP008AA / 淨值回復 / CTL006A / 扣款媒體控制 4 欄 / 168 母子基金白名單:多對多,不是交易檔 / RSP061A / PK 設定書號 / RSP062A / 母基金 N 檔 / RSP063A / 子基金 N 檔 雙 unique / 外部表:唯讀 join 或條件寫入 / COD009 COD010 / 員工 / 員眷 / OFD272A / 缺件 明細 / OFD374A / 歸屬業務員 條件寫 / BMS001 OFD130A OFD131A / 簡易開戶時寫
```

*圖:圖 2 資料模型。橘框=主檔;白框=明細或同族表;灰虛框=別的模組的表;黑框=外部唯讀。實線箭頭=主明細;回頭的長箭頭=變更檔經批次套回主檔。RSP063A 的 xsd 同時宣告單欄與雙欄 unique,一檔子基金只能掛一張設定書。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

25 支 PO 裡有 14 支宣告了主明細,其餘 11 支(`RSPB021`–`RSPB024`、`RSPB041`、`RSPB042`、`RSPB052` 等)完全不宣告——它們不用框架的存檔流程,只呼叫 SP。

| 畫面 | 實體主表 | vdb DataTable | 實體明細 | vdb DataTable | 錨點 |
|---|---|---|---|---|---|
| `RSPM004` | `RSP005A` | `RSPM004_Master` | `RSP006A` · `OFD272A` | `RSPM004_Detail` · `OFD272` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:76-80` |
| `RSPB020` | `RSP005A` | `RSPM004_Master` | `RSP006A` | `RSPM004_Detail` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:50-52` |
| `RSPM005` | `RSP007A` | `RSPM005` | `RSP013A` · `OFD272A` | `RSPM005_Detail` · `OFD272` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:147-149` |
| `RSPB008` | `RSP007A` | `RSP007A` | (宣告被註解) | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:42-44` |
| `RSPB009` | `RSP005A` | `RSPB009` | `RSP006A` · `CTL006A` | `RSPB009_Detail` · `CTL006` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:38-40` |
| `RSPB010` | `RSP008` | `RSPB010` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:21` |
| `RSPB011` | `RSP008A` | `RSPB011` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:33` |
| `RSPB015` | `RSP008A` | `RSPB015` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:41` |
| `RSPB016` | `RSP008A` | `RSPB016` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:39` |
| `RSPB018` | `RSP008A` | `RSPB018` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:32` |
| `RSPB019` | `RSP008AA` | `RSPB019` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:36` |
| `RSPM020` | `RSP061A` | `RSP061` | `RSP062A` · `RSP063A` | `RSP062` · `RSP063` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-38` |
| `RSPM021` · `RSPB025` | `RSP070A` | `RSPM070_Master` | `RSP071A` · `RSP072A` | `RSPM070_Detail` · `RSP072` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:51-53`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB025_PO.cs:37-39` |
| `RSPM022` | `RSP073A` | `RSPM022` | `RSP074A` · `RSP075A` | `RSPM022_Detail` · `RSP075` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM022_PO.cs:48-50` |
| `RSPM037` | `COD009` → `RSP005` → `RSP006` | `RSPM037` / `RSPM037_Detail` / `RSPM037_Detail_D` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| `RSPM041` | `RSP041A` | `RSPM041` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42` |
| `RSPM042` | `RSP042A` | `RSPM042` | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM042_PO.cs:42` |

三件要注意的:

1. **`RSPM037` 的 `MasterTable` 被換三次。** `Select()` 設 `COD009`、`Select_Detail()` 設 `RSP005`、`Select_Detail_D()` 設 `RSP006`。這不是主明細宣告,是「同一支 PO 用三次 `base.Select()` 撈三張不同的表」。掃描器把第一個 `MasterTable` 當主檔,所以母體才會出現「`COD009` 主檔於 `RSPM037`」。

2. **`RSPB008` 的主明細宣告只剩半套。** `this.MasterTable = new xTableMapping("RSP007A", "RSP007A")` 生效,`RSP013` 的明細宣告躺在註解裡(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:44`)。實際 `RSP013A` 是在 SP 內處理,`CheckStatus` 的 SQL 也自己 join(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`)。

3. **`RSPM004` / `RSPB020` 共用同一組 DataTable 名稱**(`RSPM004_Master` / `RSPM004_Detail`),連 `App.config` 的 `mastertable` 都指同一個名字(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:88`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:150`)。`RSPM021` / `RSPB025` 同理(`RSPM070_Master`)。改 xsd 要兩支一起看。

### 2.2 主鍵與四眼欄位

主鍵取自 xsd 的 `xs:unique` 宣告:

| 實體表 | 主鍵 | 四眼 13 欄 | 來源 |
|---|---|---|---|
| `RSP005A` | `RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:836` |
| `RSP006A` | `RSP_NO` + `RSP_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:18` |
| `RSP007A` | `RSP_CHG_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:189` |
| `RSP013A` | `RSP_CHG_NO` + `RSP_CHG_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:584` |
| `RSP008` | `RSP_NO` + `RSP_SRNO` + `DEF_SUB_DATE` + `REAL_SUB_DATE` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:486` |
| `RSP008A` | `RSP_NO` + `RSP_SRNO` + `DEF_SUB_DATE` + `REAL_SUB_DATE`(`RSPB010` / `RSPB011` 視角) `FUND_ID` + `DEF_SUB_DATE` + `REAL_SUB_DATE`(`RSPB016` / `RSPB018` 視角) | 部分 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB011Model.xsd:17`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB016Model.xsd` |
| `RSP008AA` | (xsd 未宣告 unique) | 無 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB019Model.xsd:26` |
| `RSP061A` | `RE_RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15` |
| `RSP062A` | `RE_RSP_NO` + `MOM_FUND_ID` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:93` |
| `RSP063A` | `RE_RSP_NO` + `SON_FUND_ID`,**外加一條只有 `SON_FUND_ID` 的 unique** | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:183` |
| `RSP070A` | `RSP_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:15` |
| `RSP071A` | `RSP_NO` + `RSP_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:283` |
| `RSP072A` | `RSP_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:494` |
| `RSP073A` | `RSP_CHG_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:15` |
| `RSP074A` | `RSP_CHG_NO` + `RSP_CHG_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:302` |
| `RSP075A` | `RSP_CHG_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:553` |
| `RSP041A` | `RSP_TRN_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17` |
| `RSP042A` | `TX_RSP_TRN_NO` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM042Model.xsd:26` |
| `CTL006A` | `DEF_SUB_DATE` | 無 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:721` |
| `OFD272A`〔共用〕 | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID` | 有 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1343` |
| `COD009`〔共用〕 | `EMP_NO` | **RSP 這一側的 xsd 沒宣告四眼欄** | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd:18` |

**`RSP063A` 那兩條 unique 是重點。** xsd 同時宣告了 `SON_FUND_ID`(單欄)與 `RE_RSP_NO,SON_FUND_ID`(兩欄)兩條 unique,單欄那條代表「一檔子基金只能掛在一張母子基金設定書底下」。這是 typed DataSet 層的限制,不保證實體表也這樣建;**改 `RSPM020` 時一定要先確認 DB 端的 unique index 是哪一種**,否則畫面會擋、DB 不擋,或者反過來。

`COD009` 在 RSP 側的 xsd 只宣告 6 欄(`EMP_NO` / `EMP_ID_NO` / `EMP_NAME` / `EMP_NAME_ENG` / `ENTRY_DATE` / `LEAVE_DATE`),而母體說這張表有 56 欄、有四眼——那是從 COD 側掃出來的。**同一張表在兩個模組的 typed DataSet 不同構**,這是 `architecture.md §5.4` 講的情形,不是缺陷。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列各表的識別欄與業務關鍵欄;完整欄位清單請直接看 xsd。

#### `RSP005A` — 定期定額契約主檔(`RSPM004_Master`,57 欄)

| 欄 | 中文名 | 說明 |
|---|---|---|
| `RSP_NO` | 契約書號 | PK,由 `SerialNo.GetRspNoForNfd()` 配號 |
| `RSP_TYPE` | 契約型態 |  |
| `RCV_DATE` | 收件日期 | 必須是營業日(§4.1) |
| `BF_NO` | 受益人戶號 | `-1` 代表要走簡易開戶 |
| `AGENT_ID` / `AGENT_CODE` | 銷售機構區別碼 / 銷售機構代碼 |  |
| `CHANNEL_CD` / `CHANNEL_CODE` | 通路區分碼 / 通路代碼 |  |
| `SPONSOR_CODE` | 推薦人代碼 | 銷售機構標 `SPONSOR_CHK` 時必填 |
| `EMP_NO` / `EMP_DEPT_NO` | 員工代碼 / 員工部門代碼 |  |
| `SER_EMP_NO` | 服務顧問代碼 | Designer 標籤寫「介紹人」 |
| `SUB_ID_TYPE` / `SUB_ID_NO` / `SUB_NAME` | 扣款人身份別 / 身份證字號 / 姓名 |  |
| `SEAL_TYPE` | 核印扣款方式 | 一般 / ACH / 財金三選一 |
| `SUB_BANK_CODE` / `SUB_ACCOUNT_NO` | 扣款行 / 扣款帳號 | `700` = 郵局〔客戶特定〕 |
| `SEAL_MARK` / `SEAL_USER_NO` | 核印註記 / 用戶號碼 |  |
| `STOP_BNG_DATE` / `STOP_END_DATE` | 暫停起始 / 終止日期 |  |
| `STOP_ID` / `STOP_DATE` / `STOP_CD` / `CODE_DESCRP` | 終止碼 / 終止日期 / 終止原因 / 終止原因說明 |  |
| `RSP_ACCT_BY` | 定期定額扣款帳號抓取依據 | 決定扣款資料在主檔還是明細維護(§4.1) |
| `RETIRE_YN` | 退休管家 |  |
| `RSP_NO_O` | 契約書號-舊 | 舊系統移轉來的契約 |

#### `RSP006A` — 定期定額契約基金明細(`RSPM004_Detail`,114 欄)

| 欄 | 中文名 |
|---|---|
| `RSP_NO` + `RSP_SRNO` | 契約書號 + 契約序號(PK) |
| `FUND_ID` / `FUND_SH_NM` / `FH_CD` | 基金代碼 / 基金中文簡稱 / 基金公司代碼 |
| `RSP_AMT` / `RSP_AMT2` / `RSP_AMT3` | 扣款金額 / 申購金額(中) / 申購金額(高) |
| `AMT_RATE_CD` / `HIGH_AMT_RATE` / `LOW_AMT_RATE` | 扣款金額比率 / 扣款金額(高)比率 / 扣款金額(低)比率 |
| `RSP_CNRT_FEE_RATE` / `RSP_CNRT_FEE_RATE2` / `RSP_CNRT_FEE_RATE3` | 契約手續費率 / 申購手續費率1 / 申購手續費率2 |
| `RSP_ALLOT_DAYS1` / `2` / `3` | 扣款日1 / 2 / 3 |
| `CAMPAIGN_CODE` / `CAMPAIGN_SHNM` | 促銷活動代碼 / 活動簡稱 |
| `BNG_DATE` / `END_DATE` / `DISC_TIMES` / `DISC_TIMES1` | 優惠起始 / 終止日期 / 優惠次數 / 已優惠次數 |
| `CAMP_DISC_TYPE` / `DISC_AMT` / `FIX_RATE` / `DISC_RATE` / `FEE_CAL_BASE` | 優惠折扣方式 / 優惠金額 / 優惠固定費率 / 優惠折數 / 手續費折數基準 |
| `FREE_FEE_TIMES` / `FREE_FEE_REASON` | 補償優惠次數 / 補償優惠原因 |
| `LOYAL_MRK` / `LOYAL_MRK1` | 忠實戶註記 / 前忠實戶註記 |
| `DFT_BNG_SUB_DATE` / `FIRST_SUB_DATE` / `FIRST_SUS_DATE` | 可開始扣款日期 / 首次扣款日期 / 首次扣款成功日期 |
| `FAIL_TIMES` / `SER_FAIL_TIMES` / `SUSD_TIMES` / `SER_SUSD_TIMES` | 累積扣款失敗 / 連續扣款失敗 / 累積扣款成功 / 連續扣款成功次數 |
| `SEAL_STATUS` / `SEAL_DATE` / `SEAL_RTN_DATE` / `SEAL_FAIL_ID_CO` / `SEAL_FAIL_ID_BK` | 核印狀態 / 最近送核印日期 / 最近核印回報日期 / 核印失敗原因碼(公司) / (銀行) |
| `INTRO_CODE` / `INTRO_MAIL_ZIP` / `INTRO_MAIL_ADDR` / `INTRO_EMAIL` | 公開說明索取方式 / 寄發地址郵遞區號 / 寄發地址 / 寄發EMAIL |
| `BANK_BRH` / `ACCOUNT_NO` | 收益分配行 / 收益分配帳號 |
| `DEC_LEN` | 幣別小數位數 |

#### `RSP007A` / `RSP013A` — 契約變更主檔 / 明細(`RSPM005` / `RSPM005_Detail`)

整張表的形狀就是 `BEF_xxx` / `AFT_xxx` 成對:「變更前扣款行」/「變更後扣款行」、「變更前扣款金額」/「變更後扣款金額」、「變更前優惠折數」/「變更後優惠折數」…。另有一組控制欄:

| 欄 | 中文名 | 作用 |
|---|---|---|
| `RSP_CHG_NO` / `RSP_CHG_SRNO` | 契約變更書號 / 契約變更序號 | PK |
| `CHG_DATE` | 異動收件日期 |  |
| `ORG_CHG_EFFECT_DATE` / `CHG_EFFECT_DATE` | 原始變更生效日期 / 變更生效日期 | `RSPB008` 用 `CHG_EFFECT_DATE` 挑要生效的資料 |
| `RSP_CHG_CODE` | 變更異動代碼 | 決定這一列改的是哪一組欄位 |
| `CHG_RSP_ALLOT_DAY` / `CHG_CAMP_CODE` / `CHG_STOP_DATE` / `CHG_FAVORED_REL_TYPE` / `CHG_AMT_RATE` | 變更扣款日 / 變更促銷活動代碼 / 變更暫停扣款日 / 變更優惠身份別 / (無 Caption) | 一組「這次有沒有改這一項」的旗標 |
| `RSP_CHG_CD` / `RSP_CHG_FAIL_CD` | 異動成功否 / 異動失敗原因 | **由 `RSPB008` 的 SP 回填**,失敗的要靠 `RSPR038` 撈 |
| `IS_SEAL_YN` | 異動送核否 | 變更扣款帳戶要不要重新送核印 |

#### `RSP070A` / `RSP071A` / `RSP072A` — 168 循環定額投資契約

| 表 | 中文名要點 |
|---|---|
| `RSP070A`(`RSPM070_Master`) | `MOM_FUND_ID` 母基金代碼、`REDEM_DATE` 約定轉申購日期、`REDEM_FEE_RATE1`–`3` 約定轉申購手續費率、`INVEST_TYPE` 投資型態、`GAIN_STOP` 終止停利設定、`STOP_REDEM_NO` 買回書號終止、`RETIRE_YN` 退休管家 |
| `RSP071A`(`RSPM070_Detail`) | `SON_FUND_ID` 子基金、`RSP_AMT1` 約定轉申購金額、`LOCK_POINT` 停利點、`LOCK_FEE_RATE` 停利轉申購手續費率、`GAIN_VALUE` / `GAIN_RATE` |
| `RSP072A`(`RSP072`) | `ALLOT_NO` / `ALLOT_SRNO` / `ALLOT_DATE` / `DATA_TYPE` / `REPRICE_DATE` 加碼生效日——掛在契約下的申購書清單 |

`RSP073A` / `RSP074A` / `RSP075A` 是上面三張的變更版,同樣 `BEF_` / `AFT_` 成對。

#### `RSP041A` / `RSP042A` — 停利轉申購

| 欄 | 中文名 |
|---|---|
| `RSP_TRN_NO` | 停利轉申購契約書號(`RSP041A` PK) |
| `TX_RSP_TRN_NO` | 停利異動書號(`RSP042A` PK) |
| `RSP_NO` | 定時定額契約書號(掛回 `RSP005A`) |
| `MIN_AMT` | 門檻金額(`RSP042A` 的 Caption 是「轉出餘額下限」) |
| `P_RATE` | 約定停利點 |
| `JOB_CD` | 停利機制 |
| `SWITCH_FUND_ID` | 轉出基金代碼 |
| `FEE_RATE` | 轉申購手續費率 |
| `RISK_CFD` | 風險確認 |
| `P_CODE` / `STOP_CODE` | 處理碼 / 終止碼 |

⚠ `RSP041A` 的 `RCV_DATE` 在 xsd 的 Caption 被寫成「門檻金額」,跟下一欄 `MIN_AMT` 撞名(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:17`);Designer 的標籤是「收件日期」。**以 Designer 為準**,這是 xsd 的複製貼上錯誤,列入附錄 E。

#### `RSP008` / `RSP008A` / `RSP008AA` — 扣款檔三兄弟

`RSP008`(`RSPB009` / `RSPB010` 視角,55 欄)是一筆一筆的扣款明細:`DEF_SUB_DATE` 契約扣款日期、`REAL_SUB_DATE` 實際扣款日期、`ALLOT_NAV_DATE` 淨值日、`ETD_RSP_ALLOT_AMT` / `RSP_ALLOT_AMT` 預計 / 實際扣款申購金額、`RSP_ALLOT_FEE` / `AGENT_ALLOT_FEE` / `COMP_ALLOT_FEE` 三段手續費、`TOT_SUB_AMT` 扣款總金額、`BANK_SUB_FEE` 銀行手續費、`NAV_B` 淨值、`RSP_ALLOT_UNIT` 單位數、`SUB_STATUS` 扣款進度、`NONSUCS_CODE` 扣款失敗代碼、`DATA_CENTER` 扣款資料處理中心、`BANK_MEDIA_CODE` 銀行媒體代碼。

`RSP008A` 是同一批資料在「回覆 / 計算 / 結轉」階段的視角,`RSP008AA` 是淨值回復用的。**三張表在 repo 內都沒有 DDL**(`DB/Table/` 只有 `update_rsp006a.sql` 與 `create_LOG_RSP070A.sql` 兩個跟 RSP 有關的檔),欄位定義只能從 xsd 反推。

#### `CTL006A` — 扣款日媒體產生控制(4 欄)

`DEF_SUB_DATE`(契約扣款日期)+ `IS_CRE_DISK_DATA` / `IS_CRE_FIS_DATA` / `IS_CRE_ACH_DATA` 三個旗標,對應「一般 / 財金 / ACH」三種扣款媒體有沒有產過。錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPB009Model.xsd:721`。

### 2.4 與其他模組共用的表

| 表 | 前綴屬於 | 主檔維護入口 | RSP 這側做什麼 | 錨點 |
|---|---|---|---|---|
| `COD009` | COD | `CODM009` / `CODB009` | **只讀**,當 `RSPM037` 的查詢驅動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:92-93` |
| `COD010` | COD | COD 側 | **只讀**,撈員眷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:106-108` |
| `OFD272A` | OFD | OFD / BMS 側(`BMSM004` `BMSM006` `OFDM221A` `OFDM231A`) | 當 `RSPM004` / `RSPM005` 的第二明細,存 / 刪缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149` |
| `OFD374A` | OFD(主檔在 DSM 的 `DSMM060`) | `DSMM060` | 簡易開戶且 `AUTO_BELONG_EMP = 'Y'` 時 `INSERT` 一筆 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698-738` |
| `BMS001` | BMS | `BMSM001` | 簡易開戶時 `INSERT` 一筆;其餘一律 join 取姓名 / ID | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:794-808` |
| `OFD130A` / `OFD131A` | OFD | OFD 側 | `RSPM004` 存檔後補建匯款授權書與帳號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1211-1262` |
| `OFD132A` | OFD | OFD 側 | 簡易開戶時依 `OFD040A` 範本產對帳單寄送設定 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741-791` |
| `OFD220A` / `OFD221A` / `OFD306A` | OFD | OFD 側 | `RSPB020` / `RSPB025` 改契約業務欄位時連動 `UPDATE` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:561-610` |
| `OFD303A` | OFD | OFD 側 | 只讀,判斷關帳 / 結轉控制碼 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119-130` |
| `OFD681` | OFD | OFD 側 | 只讀,取 `SEND_TYPE = '6'` 的通知信收件人 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:343-344` |
| `OFD701` | OFD | OFD 側 | 讀 / 判核印狀態,`RSPM004` 存明細時連動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| `CTL014` / `CTL016` | 共用控制檔 | 未知 | 只讀,取預設值與排程時刻 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302` |
| `LOG094A` / `LOG095A` / `LOG109A` | LOG | 未知 | 只讀,判斷批次有沒有跑過 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:230-231`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:190-192` |

反過來,**RSP 自己的表被誰用**見 §8。母體只標了 `RSP006A`(BMS / OFD 也用)一張。

### 2.5 狀態碼(從程式反推,標來源)

#### 四眼 `Status`

RSP 全模組都吃框架的 `Status` 值域,細節看 `architecture.md §3.10`。本模組只有三個地方直接寫死狀態字串:

| 值 | 用在哪 | 錨點 |
|---|---|---|
| `'301'` | `RSPB052` 產出的終止資料、`RSPM004` 補建的 `OFD130A` / `OFD131A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |

其餘一律走 `f_TA_GetEVAStatus('A')` 這個 TVF 取「已生效」的狀態集合,再用 `NOT IN` 找還沒覆核完的:

```
RSP007A.Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))
```

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:154`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:112`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:111`。`f_TA_GetEVAStatus` 不在版控內。

#### `REDEM_DATE` — 168 契約的約定轉申購日(反推自 `DECODE`)

`RSPB021_PO` 用三段 `DECODE` 把代碼展開成 6 / 16 / 26 日,逆推出來的值域是:

| 代碼 | 6 日 | 16 日 | 26 日 |
|---|---|---|---|
| `1` | ✓ |  |  |
| `2` |  | ✓ |  |
| `3` |  |  | ✓ |
| `4` | ✓ | ✓ |  |
| `5` |  | ✓ | ✓ |
| `6` | ✓ |  | ✓ |
| `7` | ✓ | ✓ | ✓ |

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128`。同一組 `DECODE` 在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:163-165` 又抄了一次(子基金版本),**兩份要一起改**。

#### `OFD303A` 的三個控制碼(只列 RSP 讀到的值)

| 欄 | 值 | 意義(依訊息字串) | 錨點 |
|---|---|---|---|
| `REDEM_CTL_CODE` | `'4'` | 買回 NAV 日之買回關帳作業已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148-149` |
| `ALLOT_CTL_CODE` | `'3'` | 此買回 NAV 日之申購關帳作業已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:150-151` |
| `RSP_CTL_CODE` | `'1'` | 請先執行單位數計算作業 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:81` |
| `RSP_CTL_CODE` | `'3'` | 本日定期定額申購資料已結轉 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:80` |

#### 本模組自訂的旗標〔客戶特定〕

| 欄 | 值 | 意義 | 錨點 |
|---|---|---|---|
| `STOP_ID` | `'N'` / 空 = 未終止 | `NVL(TRIM(STOP_CD),'N') = 'N'` 是 168 契約「還活著」的判斷式 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:125`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:969` |
| `RSP_CHG_CODE` | `'A'` | 168 變更明細的「新增子基金」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945` |
| `ISCHG_STOP_ID` | `'Y'` / `'N'` | 這一列有沒有改終止設定 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:554`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:562` |
| `SEAL_TYPE` | 一般 / ACH / 財金 | 三種扣款媒體,`RSPB009` / `RSPB010` / `RSPB011` / `RSPB015` 都拿它分流 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2282`(`GetSealType`,順序 FIS → ACH → 一般) |
| `SEND_TYPE` | `'6'` | `OFD681` 裡 RSPB008 通知信的收件人群組 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `EMP_CD` | `'1'` | `COD009` 裡「算員工」的判斷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111` |
| 銀行總行 | `'700'` | 郵局;`RSPM004` 的限額檢核與身份別鎖定都認這個值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753` |
| 促銷活動 | `'86A03'` | `RSPM004` 有一支專門檢核這個活動的方法 `Check86A03` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785` |

## 3. 畫面清冊

56 支畫面:B 17、I 0、M 8、R 31。六層(UI / FormProxy / Control / PO / UIEntity / DataEntity)按掃描母體全部「齊」,實際比對後有兩處要修正,見附錄 D.2。

### 3.1 維護 M

| 代號 | 中文名(推測) | 六層 | 主表 | 明細 | 伺服端卡控 | 彈出視窗 |
|---|---|---|---|---|---|---|
| `RSPM004` | 定期定額契約申請 | 齊 | `RSP005A` | `RSP006A` `OFD272A` | `BeforeAdd` / `AfterAdd` / `AfterUpdate` / `AfterApproveDelete` | `RSPM004p0`–`RSPM004p4`(5 支) |
| `RSPM005` | 定期定額契約變更 | 齊 | `RSP007A` | `RSP013A` `OFD272A` | `BeforeAdd` / `BeforeUpdate` 等 | `RSPM005p0`–`RSPM005p3`(4 支) |
| `RSPM020` | 母子基金設定 | 齊 | `RSP061A` | `RSP062A` `RSP063A` | 只掛取數 | 無 |
| `RSPM021` | 168 循環定額投資契約 | 齊 | `RSP070A` | `RSP071A` `RSP072A` | 只掛取數 | `RSPM021p0` |
| `RSPM022` | 168 循環定額投資契約變更 | 齊 | `RSP073A` | `RSP074A` `RSP075A` | 只掛取數 | `RSPM022p0` |
| `RSPM037` | 離職員工契約手續費率維護 | 齊 | `COD009`(只讀) | `RSP005` / `RSP006`(只讀 / 只改費率) | 無 | `RSPM037p0` `RSPM037p1` |
| `RSPM041` | 停利轉申購契約 | 齊 | `RSP041A` | — | 只掛取數 | 無 |
| `RSPM042` | 停利轉申購契約異動 | 齊 | `RSP042A` | — | 只掛取數 | 無 |

加上偽裝成 B 的 `RSPB020`(定期定額契約業務資料維護)與 `RSPB025`(168 契約業務資料維護),實際維護畫面共十支。

### 3.2 查詢 I

**本模組無 I 畫面**,原因見 §5。

### 3.3 批次 B

| 代號 | 中文名(推測) | 基底 | 主表 | SP | 前置檢核 |
|---|---|---|---|---|---|
| `RSPB008` | 定期定額契約變更生效 | `xOneStepProcessForm` | `RSP007A` | `s_TA_RSPB008_Excute_M` | `CheckStatus`(未覆核就擋) |
| `RSPB009` | 產生 / 重作 / 刪除扣款資料 | `xOneStepProcessForm` | `RSP005A` + `RSP006A` + `CTL006A` | `S_TA_RSPB009_Excute` | 契約扣款日有效、註銷戶詢問、是否已有扣款日 |
| `RSPB010` | 扣款送件與實際扣款日 / 淨值日指定 | `xOneStepProcessForm` | `RSP008` | `EXEC s_RSPB010_Excute …`(字串) | 淨值日已過帳 / 已結轉、實際扣款日已算淨值 / 已最後確認 |
| `RSPB011` | 扣款回覆逐筆確認 | `xOneStepProcessForm` | `RSP008A` | 無(直接 SQL) | 小額扣款控制碼四段 |
| `RSPB015` | 扣款回覆確認(依扣款行小計) | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB015_Excute` | 無 |
| `RSPB016` | 單位數計算 | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB016_Excute` | 無符合資料就擋 |
| `RSPB018` | 結轉 | `xOneStepProcessForm` | `RSP008A` | `S_TA_RSPB018_Excute` | `OFD303A.RSP_CTL_CODE` + 淨值一致性 |
| `RSPB019` | 淨值回復 | `xOneStepProcessForm` | `RSP008AA` | `S_TA_RSPB019_Excute` | 無 |
| `RSPB020` | 定期定額契約業務資料維護 | **`xMaintainForm`** | `RSP005A` + `RSP006A` | 無(直接 SQL,含 PL/SQL 區塊) | 四眼 |
| `RSPB021` | 168 扣款轉申購產生 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB021_EXCUTE` | `ValidateOFD303A`;`ValidateLOG095A` **被註解掉** |
| `RSPB022` | 168 停利計算 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB022_EXCUTE` | `ValidateLOG094A` + `ValidateOFD303A` |
| `RSPB023` | 168 契約變更生效 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB023_EXCUTE` | `CheckStatus`(查 `RSP073A`) |
| `RSPB024` | 168 轉申購 Email 資料產生 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB024_EXCUTE` | 只擋「轉申購日須為 6/16/26」 |
| `RSPB025` | 168 契約業務資料維護 | **`xMaintainForm`** | `RSP070A` + `RSP071A` + `RSP072A` | 無 | 四眼 |
| `RSPB041` | 停利契約變更生效 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB041_EXCUTE` | `CheckStatus`(查 `RSP042A`) |
| `RSPB042` | 定期定額停利計算 / 刪除重作 | `xOneStepProcessForm` | 無宣告 | `S_TA_RSPB042_EXCUTE` | `ValidateLOG109A` + `ValidateOFD303A` |
| `RSPB052` | 連續扣款失敗契約終止 | `xOneStepProcessForm` | 無宣告 | 無(直接 SQL) | 無 |

**「無宣告主明細」的 8 支走的路徑**:它們的 PO **不繼承** `BaseEVADaoPO` / `BasicEVAPO`,只實作自己的介面(例 `public class RSPB021_PO : IRSPB021_PO`,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:26`),自己 `new Database("TA", DbServerType.Oracle)`、自己開交易、自己呼叫 SP。沒有 `MasterTable` 是因為**根本沒用到框架的存檔流程**,不是漏寫。`RSPB052` 是唯一的例外:它不宣告主明細,卻自己寫 `INSERT` / `UPDATE`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`)。

### 3.4 報表 R

31 支 R、39 個 `.rpt`。對應關係見 §7.2;這裡只列代號與標題(標題取自 `SetQueryParameters` 的第三個參數,是程式裡寫死的中文字串,不是推測):

| 代號 | 報表標題 | rpt | SP |
|---|---|---|---|
| `RSPR008` | 定期定額異動資料轉入主檔報表 | `RSPR008RPS` | `s_RSPR008_Get` |
| `RSPR011` | 定期定額-申購扣款明細表 | `RSPR011RPS` | `S_TA_RSPR011_GET` |
| `RSPR012` | 定期定額扣款行回覆資料查核表 | `RSPR012RPS` | `S_TA_RSPR012_GET` |
| `RSPR013` | 定期定額扣款銀行查核表 | `RSPR013RPS` / `RSPR013RPS1` | `S_TA_RSPR013_GET` |
| `RSPR017` | 定期定額-受益人申購明細表 | `RSPR017RPS` / `RSPR017RPS1` / `RSPR017RPS2` | `s_TA_RSPR017_Get` |
| `RSPR020` | 定期定額契約資料查核表 | `RSPR020RPS` / `RSPR020RPS1` | `S_TA_RSPR020_GET` |
| `RSPR021` | 定期定額扣款失敗明細表 | `RSPR021RPS` / `RSPR021RPS1` | `S_TA_RSPR021_GET` |
| `RSPR023` | 定期定額-保管銀行傳真表 | `RSPR023RPS` | `s_RSPR023_Get` + `s_RSPR023_Count` + `s_RSPR023_Total` |
| `RSPR024` | 定期定額-申購扣款總表 | `RSPR024RPS` / `RSPR024RPS1` | `S_TA_RSPR024_GET` |
| `RSPR028` | 定期定額扣款失敗項目統計表 | `RSPR028RPS` | `S_TA_RSPR028_GET` |
| `RSPR029` | 定期定額契約異動項目統計表 | `RSPR029RPS` | `S_TA_RSPR029_GET` |
| `RSPR031` | 定期定額投資計畫 - 收件通知書 | `RSPR031RPS` | `s_TA_RSPR031_Get` |
| `RSPR034` | 定期定額首次扣款通知書 | `RSPR034RPS` | `s_RSPR034_1_Get` / `s_RSPR034_2_Get` |
| `RSPR038` | 定期定額契約異動資料查核表 | `RSPR038RPS` | `S_TA_RSPR038_GET` |
| `RSPR041` | 停利轉申購書查核表 | `RSPR041RPS` | `S_TA_RSPR041_GET` |
| `RSPR042` | 停利轉申購異動書查核表 | `RSPR042RPS` | `S_TA_RSPR042_GET` |
| `RSPR043` | 定期定額停利轉申購(含買回)停利核對表 | `RSPR043RPS` | `S_TA_RSPR043_GET` |
| `RSPR046` | 定期定額契約終止原因統計表 | `RSPR046RPS` | `s_RSPR046_Get` |
| `RSPR047` | 定期定額契約終止原因明細表 | `RSPR047RPS` | `s_RSPR047_Get` |
| `RSPR048` | 定期定額契約連續扣款失敗明細表 | `RSPR048RPS` | `s_TA_RSPR048_Get` |
| `RSPR049` | 定期定額扣款檢核表 | **無 rpt(純 Excel)** | `s_RSPR049_Get` |
| `RSPR051` | 定期定額投資計畫 - 扣款失敗通知書 | `RSPR051RPS` | `s_TA_RSPR051_Get` |
| `RSPR060` | 168循環定額投資法契約核對表 | `RSPR060RPS` / `RSPR060RPS1` | `S_TA_RSPR060_GET` |
| `RSPR061` | 168循環定額投資法契約異動報表 | `RSPR061RPS` | `S_TA_RSPR061_GET` |
| `RSPR062` | 168循環定額投資法契約扣款日記錄表 | `RSPR062RPS` | `S_TA_RSPR062_GET` |
| `RSPR063` | 168循環定額投資法停利核對表 | `RSPR063RPS` | `S_TA_RSPR063_GET` |
| `RSPR064` | 168循環定額投資法客戶查詢報表 | `RSPR064RPS` | `S_TA_RSPR064_GET` |
| `RSPR065` | 168標的基金申購金額不足核對表 | `RSPR065RPS` | `S_TA_RSPR065_GET` |
| `RSPR066` | 168投資契約轉帳明細表(成功 / 失敗) | `RSPR066RPS` / `RSPR066RPS1` / `RSPR066RPS2` | `S_TA_RSPR066_GET` |
| `RSPR070` | 業務受益人定額停扣明細報表(四種標題) | `RSPR070RPS` | `S_TA_RSPR070_GET` |
| `RSPR071` | 定期定額申請暫停扣款查核表 | `RSPR071RPS` | `S_TA_RSPR071_GET` |

### 3.5 一眼看出差別的五件事

1. **沒有任何 I 畫面。** 查詢需求全部由 31 支報表吸收,其中 `RSPR064`(168 客戶查詢報表)、`RSPR070`(業務受益人明細)實質上就是查詢畫面披報表的皮(§5)。

2. **8 支 M + 2 支偽 B 的維護畫面裡,只有 3 支在伺服端還有卡控**(`RSPM004` / `RSPB020` / `RSPM005`),其餘 7 支的 PO 只掛 `BeforeSelect` 之類的取數事件。

3. **三條「變更 → 生效」的鏈長得一模一樣**,但實作細節三種:`RSPB008` 讀 RefCursor、`RSPB023` / `RSPB041` 讀 OUT 參數,而且 `RSPB008` 多了一支 WindowsService。

4. **報表 SP 的命名有三種大小寫風格**:`S_TA_RSPRxxx_GET`(18 支)、`s_TA_RSPRxxx_Get`(5 支)、`s_RSPRxxx_Get`(7 支)。Oracle 的物件名不分大小寫,所以這只是可讀性問題,但 grep 時要三種都試。

5. **`RSPR049` 是 31 支裡唯一不出 Crystal Report 的**,直接把 byte 陣列寫成 `.xlsx` 再 `Process.Start` 打開(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84-97`)。`RSPR070` 則是報表與 Excel 兩套都有(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:234-258`)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] RSP 維護畫面的卡控分層:UI 層、PO 層、四眼引擎,以及兩個不走四眼的例外
圖中文字:① 用戶端(UI):十支維護畫面的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / RSPM004 這支 228 行 / 明細彈窗 / RSPM004p0 3089 行 / ByPass 訊息 / 詢問通過就記錄 / ② 伺服端(PO):十支裡只有三支有第二道防線 / RSPM004 BeforeAdd / 簡易開戶 + 配書號 / RSPM005 BeforeAdd / 鎖契約 + 來源檢核 / RSPB020 存檔後 / 連動三張 OFD 表 / 其餘七支 / PO 只掛取數事件 / ③ 四眼引擎(BaseEVADaoPO,無原始碼) / 輸入 / 待驗證 / 驗證 / 待覆核 / 覆核 / Status 進已生效集合 / 覆核完不等於生效 / 要等 RSPB008 / B023 / B041 / ④ 兩個例外 / RSPM037 / xOneStepProcessForm / 手寫 UPDATE RSP006 / 不寫 Status 不走四眼 / RSPB052 / 自己寫 Status=301 / 產出即已覆核 / 不進任何人的待辦
```

*圖:圖 3 卡控順序。橘框=真正會擋下的關卡;橘虛框=風險或例外;黑框=無原始碼的框架層。十支維護畫面(八 M 加 RSPB020 / RSPB025)裡只有三支在伺服端再驗一次;RSPM037 連四眼都不走,RSPB052 自己把狀態寫成已覆核。*

八支 M 加兩支掛 `xMaintainForm` 的 B(`RSPB020` / `RSPB025`)。後兩支的差異寫在 §4.1 與 §4.4 的節內,不另開節。

### 4.1 `RSPM004` — 定期定額契約維護作業

#### 用途

**這支畫面的中文名不是推測**——`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:33` 的 XML 註解直接寫「程式名稱:定期定額契約維護作業」。它是整個模組的入口:輸入一張契約書(`RSP005A`),底下掛 N 檔基金的扣款設定(`RSP006A`),必要時同時登記缺件(`OFD272A`)。

規模:UI 2,899 行 + 主明細彈出視窗 `RSPM004p0` 3,089 行 + PO 2,883 行,加上 `RSPM004p1`–`RSPM004p4` 四支小彈窗,是全模組最大的一支。

#### 五個彈出視窗

| 彈窗 | 行數 | 做什麼 |
|---|---|---|
| `RSPM004p0` | 3,089 | 基金明細的新增 / 修改,所有金額、費率、優惠、扣款帳號的檢核都在這裡 |
| `RSPM004p1` | 25 | 極小,幾乎是空殼 |
| `RSPM004p2` | 145 | 缺件維護(對應 `DoExp2`) |
| `RSPM004p3` | 75 | 扣款次數查詢(對應 `DoExp3`,取 `OFD315`) |
| `RSPM004p4` | 49 | 文件調閱(對應 `DoExp4`) |

四顆自訂鈕的掛點:`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:760`(印鑑 `DoExp1`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:777`(缺件 `DoExp2`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:784`(扣款次數 `DoExp3`)、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:800`(文件調閱 `DoExp4`)。缺件鈕還有自己的前置驗證 `DoExp2Validate`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:767`)。

#### 「扣款帳號抓取依據」是寫死的 `'2'`

主檔取數 SQL 直接 `SELECT … ,'2' AS RSP_ACCT_BY`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212`),UI 的建構期也硬派 `RspAcctBy = "2"`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:166`),原本要讀系統參數的那段被註解掉(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:161-165`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:85-89`)。

檔頭註解說明了原因:「依規格翻修(`CTL015.RSP_ACCT_BY` 設為 1:依主檔扣款帳號的功能未完成)20090605-000」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:35`),`RSPM005_PO` 也有同一句(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:123`)。

**實務意義:扣款行 / 扣款帳號 / 扣款方式一律在「明細」層維護,主檔那一組欄位永遠不顯示**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:609-613` 的 `IsShowSubData(false)`)。如果哪天要打開 `RSP_ACCT_BY = '1'`,要改的不只是那個常數,還有 `SetMasterToDetail()` 內「扣款帳號抓取依據依照主檔時,將扣款資料寫入明細檔」那一段(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2471`)。

#### 簡易開戶:註解說取消了,程式路徑還在

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:36` 寫「2013.01.29 取消簡易開戶功能,若要使用簡易開戶功能,須 REVIEW 受益人相關欄位是否相符」。但程式沒有任何開關把它關掉:在客戶統編欄輸入一個查不到受益人的統編,就會走到 `SetBfDataVisible(true)`,整組開戶欄位打開、`Simple_Open = true`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:902-919`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1917-1940`)。

存檔時 PO 端的 `BeforeAdd` 會:

1. 用 `SerialNo.GetBFNo()` 配戶號,並 do-while 檢查撞號(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:638-643`)

2. 依 `ProductId.TaOfd` / `ProductId.TaNfd` 帶國別碼與 `BF_SORT_CD`(自然人 `140` / 法人 `090`)(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:649-676`)〔客戶特定〕

3. 從 `CTL014` 取八組預設值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684`)

4. 視 `AUTO_BELONG_EMP` 決定要不要 `INSERT OFD374A`(§8.4)

5. 依 `OFD040A` 範本 `INSERT OFD132A`(對帳單寄送設定)

6. `INSERT BMS001`

**六步驟全部串成同一條 SQL 字串再一次 `ExecuteNonQuery`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-803`)。這條字串的形狀是 `;INSERT OFD374A …;INSERT OFD132A …` 再接 `xTableHelper.GetInsertString(dbProduct, "BMS001")` 的產出,**沒有 `BEGIN` / `END`**。同一支 repo 內只要要送多段 DML 都會自己包 PL/SQL 區塊(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:560`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569`),這一段沒包。**假設**:這條 SQL 在 Oracle 會拋 `ORA-00911`,也就是簡易開戶實際上已經不能用,與 2013 那句註解吻合。依據:`xTableHelper.GetInsertString` 產出的是單一 `INSERT INTO … VALUES ( … )` 不帶分號(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:486-511`),`Database.ExecuteNonQuery` 無原始碼(框架 DLL),無法確認它會不會自動包區塊。

#### 必填與存檔前檢核(UI 層)

`DoValidate(bool IsFinalCheck)`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2195-2418`)。順序與短路點:

1. `ValidateErrList.Clear()` → `validatorManager1.DataValidate()`

2. 明細 grid 沒有資料 → 「明細資料必須輸入」,**而且 `if (ErrorCount > 0) return true` 直接短路**,後面所有檢核都不跑(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2202-2207`)

3. 簡易開戶區塊有開才檢核:戶籍地址、開戶日期 ≤ 收件日期、出生日期 ≤ 開戶日期、出生日期 ≠ `1900/01/01`、出生日期 < 系統日、開戶日期須為營業日

4. 只有按「新增 / 修改」才跑(`IsFinalCheck`):暫停交易檢核 + 郵局扣款日限額

5. 只有「新增」才跑:缺件且限制交易(`IsLackDoc`)

6. 推薦人:銷售機構的 `SPONSOR_CHK` 標了就必填

7. 非簡易開戶時,收件日期不可小於受益人的開戶日期

8. 收件日期須為營業日

9. `IsFinalCheck` 時:員工代碼歸屬的銷售機構與畫面不符 → **詢問**,按「是」寫 ByPass 訊息

#### 郵局扣款日限額:一段只活在 UI 的檢核

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2253-2344`。挑出明細裡扣款行是郵局且未終止的列,依「扣款帳號 + 扣款方式 + 扣款日」分組加總 `RSP_AMT`,丟給 `cnbu.CalcLmtAmt` 算限額。

三個要注意的:

- **篩選條件的第二個分支是死的。** `(SUB_BANK_CODE LIKE '700%' OR (SUB_BANK_CODE='' AND SUB_BANK_CODE LIKE '700%'))` —— `= ''` 和 `LIKE '700%'` 不可能同時成立(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255-2257`)。

- **`SetUtilRow` 把扣款行硬寫成 `"700"`**,不管實際值(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`)。因為外層已經篩過只留郵局,所以目前沒事,但兩處耦合。

- **伺服端沒有對應的檢核。** PO 的 `CheckDayLmtAmt` 整段被註解,註解說「改寫在 StoredProcedure 裡檢核」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286`),而那個 SP 不在版控內。UI 這一段被繞過就沒人擋。

#### 明細層(`RSPM004p0`)的檢核總覽

這支彈窗 3,089 行,檢核密度是全模組最高。分類:

| 類 | 內容 | 錨點 |
|---|---|---|
| 必填 | 扣款金額;公開說明書索取方式選「郵寄 / EMAIL」時對應欄位必填 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2076`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2083-2091` |
| 金額 | 定期不定額時「申購金額(低) ≤ (中) ≤ (高)」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2328` |
| 費率下限 | 契約手續費率不可小於該基金的最低手續費率 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2376` |
| 費率上限 | 不可大於牌告手續費率;沒設定自訂費率就報「自訂銷售手續費率尚未設定(OFDM193)」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2395`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2400` |
| 優惠 | 優惠日期(起)不可大於(迄);優惠日期與次數擇一輸入 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2423`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2462` |
| 高收益基金 | 必須勾風險確認;受益人必須先有風險預告書 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2341`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2346` |
| 扣款帳號 | 已送核 / 已啟動重新送核不可修改;扣款行不支援該扣款方式;非本人時扣款人 ID 不可等於客戶統編;受益人已成年時身份別不可為法定代理人 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2542`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2546`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2555`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2573`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2592` |
| 扣款行限額 | 逐筆算 `CalcLmtAmt` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2427-2456` |
| 銷售機構 | 銷售機構是否有效承銷該基金(`cnbu.IsAgentFund`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2469-2473` |

**詢問類**(跳 `Warn03`,按「是」就寫 ByPass 訊息記錄下來):

| 訊息 | 錨點 |
|---|---|
| 此受益人本日已有相同之基金扣款資料,請確定要存檔? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2155-2164` |
| 扣款帳號為核印失敗狀態,請確定要存檔? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2171-2180` |
| 有多筆未終止的契約資料,是否繼續? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2291-2296` |
| 該客戶為優惠關係人,但有輸入促銷活動代碼是否繼續? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2302-2309` |
| 該客戶為優惠關係人,是否仍要輸入促銷活動代碼? | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:1123` |

「此受益人本日已有相同之基金扣款資料」這一條是兩段式:先用 `DataTable.Select` 在畫面上的明細裡找(`RCV_DATE` + `FUND_ID` + 不同 `RSP_SRNO`),沒找到才打 `CheckSameRspData` 去 DB 查其他契約(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2122-2152`)。「有多筆未終止的契約資料」同樣兩段式,DB 那段走 `CheckSameData`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2262-2288`)。

#### 伺服端(PO)做的事

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 簡易開戶(見上)+ 用 `SerialNo.GetRspNoForNfd()` 配契約書號,do-while 防撞號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:623-835` |
| `AfterAdd` / `AfterUpdate` | `BeforeSaveDetail()` 處理明細與核印 + `AddOFD130A()` 補建匯款授權書 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:859-875` |
| `AfterGetMaintainData` | 取跳號一覽表歷史 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2577-2582` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterResend` / `AfterReject` | 六個事件做的是**同一件事**:`SrNoCommentProcessor.AddCommentHistory(對應 EVAType, SrNo.RspNoForNfd, …)`,失敗就 `throw new ApplicationException("")`(**空訊息**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2584-2651` |
| `AfterApproveDelete` | 除了寫跳號紀錄,還要把核印資料收尾:`BuildOldSeal()` 的字串用 `Split(';')` 切成兩段分別執行,再 `CheckOldSeal` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2612-2637` |

`AddOFD130A` 的行為(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1187-1265`):畫面上有填收益分配帳號(`BMS005A_TMP` 有列)才動作;先看 `OFD130A` 有沒有這個受益人的授權書編號,沒有就配一個新的並 `INSERT`,`STATUS` **寫死 `'301'`**、`REJECTDATE` 寫死 `DATE'1900-01-01'`;再把 `BMS005A` 的帳號資料複製一列進 `OFD131A`,`FUND_ID` **寫死字串 `'ALL FUNDS'`**、`PAUSE_PAY` 寫死 `'N'`。

#### 跨表更新一覽

| 表 | 動作 | 條件 | 錨點 |
|---|---|---|---|
| `RSP005A` | INSERT / UPDATE | 框架四眼 | — |
| `RSP006A` | INSERT / UPDATE / DELETE | `BeforeSaveDetail` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:882-1186` |
| `OFD272A` | INSERT / DELETE | 缺件頁籤有資料 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1171-1186` |
| `OFD701` | UPDATE | 核印資料連動 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951-976` |
| `BMS001` | INSERT | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:794-808` |
| `OFD374A`〔共用〕 | INSERT | 簡易開戶 **且** `AUTO_BELONG_EMP = 'Y'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698-738` |
| `OFD132A` | INSERT … SELECT | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741-791` |
| `OFD130A` / `OFD131A` | INSERT | 有填收益分配帳號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1211-1262` |

#### 取數 SQL 與下拉過濾

主檔取數 `BuildMasterSQLString`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:174-427`),六張表全部 `LEFT JOIN`,查不到對照就 `NVL(…,'')`,**不會把主檔資料濾掉**:`BMS001A`(受益人)、`COD009`(員工姓名)、`OFD072A`(推薦人)、`TABLE(F_TA_GetAgent())`(銷售機構)、`OFD071A`(通路)、`OFD002`(部門)、`COD006A`(終止原因,固定 `CODE_SORT='42'`)。

明細取數 `BuildDetailSQLString`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:428-621`)分兩段:`RSP006A` 與 `OFD272A`。

`GetSealType`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2282-2354`)依「FIS → ACH → 一般」的優先序決定扣款方式,`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2824` 有對應的 UI 呼叫。扣款行為郵局(`700`)時身份別鎖成「本人」且不可修改(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753`)〔客戶特定〕。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 存檔 | 明細 grid 無資料 | 無明細 | 阻擋(且短路後續全部檢核) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2202-2207` |
| UI 存檔 | 收件日期 < 開戶日期 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2216-2219` |
| UI 存檔 | 出生日期 > 開戶日期 / 格式錯 / ≥ 系統日 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2222-2235` |
| UI 存檔 | 開戶日期非營業日 | 簡易開戶時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2240-2243` |
| UI 存檔 | 郵局扣款日限額 | 加總超限 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2331-2335` |
| UI 存檔 | `CalcLmtAmt` 回 `ReturnCode == false` | 中間層異常 | 阻擋(顯示通用伺服端錯誤) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2336-2340` |
| UI 存檔(新增) | 受益人有缺件且限制交易 | `IsLackDoc` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2347-2352` |
| UI 存檔 | 銷售機構要求推薦人卻沒填 | `SPONSOR_CHK` = 已標記 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2362-2366` |
| UI 存檔 | 收件日期 < 受益人開戶日期(非簡易開戶且無舊契約書號) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2378-2385` |
| UI 存檔 | 收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2388-2392` |
| UI 存檔 | 員工代碼歸屬的銷售機構與畫面不符 | 成立 | 詢問(按否就 focus 回銷售機構) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2397-2414` |
| UI 存檔 | 受益人為暫停做定期定額交易 | `IsPauseTrade` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2434-2449` |
| UI 統編輸入 | 統編為交易列管 | `CheckIsControl` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:909-913` |
| UI 統編輸入 | 客戶為員工 / 員眷 | `IsRelTrade` | 警示 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1086-1109` |
| UI 明細 | 扣款金額為必填 | 空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2076` |
| UI 明細 | 費率低於基金最低費率 / 高於牌告費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2376`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2395` |
| UI 明細 | 高收益基金未勾風險確認 / 無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2341`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2346` |
| UI 明細 | 扣款帳號已送核 / 已啟動重新送核 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2542`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2546` |
| UI 明細 | 本日已有相同基金扣款資料 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2153-2165` |
| UI 明細 | 有多筆未終止的契約資料 | `CheckSameData` > 0 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2289-2296` |
| UI 明細 | 扣款帳號核印失敗 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2169-2180` |
| UI 明細 | 優惠關係人又輸促銷活動 | 成立 | 詢問 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2300-2309` |
| PO 新增 | 戶號在 `SrNoComment` 已被刪除過 | `CheckSrNoComment` | **形同無效**,見附錄 E | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2356-2372` |
| PO 新增 | 簡易開戶寫 `BMS001` 失敗 | `ExecuteNonQuery <= 0` | 阻擋(`throw`「新增BMS001失敗」) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:805-808` |
| PO 四眼各段 | 跳號紀錄寫入失敗 | `AddCommentHistory` 回 false | 阻擋,但 `throw new ApplicationException("")` **訊息是空的** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2588` |

#### `RSPB020` 與這一支的差別

`RSPB020` 用同一組 DataTable、同一套取數 SQL(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:116-370` 幾乎是 `RSPM004_PO` 的複製),但:

| 面向 | `RSPM004` | `RSPB020` |
|---|---|---|
| 可改什麼 | 全部 | **只有業務欄位**:銷售機構、通路、推薦人、員工、介紹人、郵局經辦區、備註 |
| 明細檢核 | `RSPM004p0` 3,089 行 | 沒有明細彈窗 |
| 存檔後動作 | 核印 + `OFD130A` / `OFD131A` | **PL/SQL 區塊同步更新 `OFD220A` / `OFD221A` / `OFD306A` 的同名業務欄位** |
| 錨點 | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:554-610`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:205-243` |

`OFD221A` 的更新多一條 `AND RSP_TYPE IN ('1','2')`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:587`)〔客戶特定〕;`OFD306A` 用 `WHERE EXISTS` 子查詢掛回申購書(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:599-610`)。**改契約的業務歸屬會連動改三張 OFD 交易表,這是 RSP 對 OFD 影響最大的一條路徑。**

### 4.2 `RSPM005` — 定期定額契約變更

#### 用途

客戶要換扣款銀行、改金額、改扣款日、改促銷活動、暫停、恢復、終止,全部走這支。它**不直接改契約**,而是開一張變更書(`RSP007A` + `RSP013A`),每一列都存「變更前」與「變更後」兩組值,等 `RSPB008` 到了生效日才把值套進 `RSP005A` / `RSP006A`(§6.2)。

規模:UI 1,678 行 + 明細彈窗 `RSPM005p0` 3,909 行(全模組單檔最大)+ PO 2,546 行。

#### 資料何時真的生效 —— 三個時間欄位

| 欄 | 誰寫 | 意義 |
|---|---|---|
| `CHG_DATE` | 畫面 | 異動收件日期。必須是營業日、且不可小於契約收件日期 |
| `ORG_CHG_EFFECT_DATE` | 畫面 | 原始變更生效日期 |
| `CHG_EFFECT_DATE` | 畫面 | 變更生效日期,**`RSPB008` 用它跟「今天」比對挑資料** |
| `CHG_UPD_DTTM` | 未見程式寫入 | 變更資料更新日期時間 |

流程是:輸入(`Status` 進待驗證)→ 驗證 → 覆核(`Status` 進已生效集合)→ **資料還沒生效** → `RSPB008` 在 `CHG_EFFECT_DATE` 當天(或之前)跑,SP 才把值搬進主檔 → 回寫 `RSP_CHG_CD`(異動成功否)與 `RSP_CHG_FAIL_CD`(異動失敗原因)。

**覆核完 ≠ 生效。** 這是這支畫面最容易誤解的地方,也是 `architecture.md §3.8.1`(「覆核完資料就生效」不是通則)在 RSP 的具體案例。要確認一張變更書到底套進去沒有,只能看 `RSP_CHG_CD`,或跑 `RSPR038`(定期定額契約異動資料查核表)。

#### 新增變更書前的兩道伺服端關卡

`RSPM005A_PO_BeforeAdd`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:407-464`):

**第一道:鎖契約。** `UPDATE RSP005A SET RSP_NO = RSP_NO WHERE RSP_NO = :RSP_NO`——一個不改任何值的 UPDATE,純粹為了在交易內鎖住那一列。影響列數 0 就 `throw`「鎖定契約書失敗,請檢查」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:416-420`)。契約書號不存在也會走到這裡,訊息會誤導。

**第二道:來源狀態檢核,但三個條件是 AND 串的。**

```
SELECT COUNT(*) FROM RSP005A
WHERE RSP_NO = :RSP_NO
  AND Status NOT IN (SELECT STATUS FROM TABLE(F_TA_GetEVAStatus('A')))
  AND NOT EXISTS (SELECT 0 FROM RSP008A WHERE RSP_NO = :RSP_NO)
  AND NOT EXISTS (SELECT 0 FROM RSP007A WHERE RSP_NO = :RSP_NO)
```

`> 0` 就 `throw`「契約書已被異動,尚未覆核,不可新增異動資料」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:423-436`)。

三條 AND 的意思是:**只有「契約尚未生效 + 從來沒扣過款 + 從來沒開過變更書」三者同時成立才會擋。** 也就是說,只要這張契約曾經開過任何一張變更書(`RSP007A` 有資料),這道檢核就永遠不成立,即使主檔現在正處於待覆核狀態。程式的區塊註解寫「檢查來源覆核,沒付過款,也沒異動過,也沒覆核的不可新增異動」,與訊息「契約書已被異動,尚未覆核,不可新增異動資料」互相矛盾——**訊息描述的情境(已被異動)正是會讓這條檢核失效的情境**。列入附錄 E。

#### 明細的三種狀態轉換

`BeforeSaveDetail`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:886-1360`)依 `RSP_CHG_CODE` 分流:

| 情境 | 區塊 | 錨點 |
|---|---|---|
| 設終止 | 寫 `STOP_ID` / `STOP_DATE` / `STOP_CD` 回 `RSP006A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:929-948` |
| 取消終止(原本終止,這次改成不終止,且是修改) | 還原 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:949-970` |
| 設暫停(狀態有效) | 寫 `STOP_BNG_DATE` / `STOP_END_DATE` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:971-1005` |
| 取消暫停(修改時) | 還原 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1006-1028` |
| 新明細 | 新增一列 `RSP006A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1029-1061` |
| 核印 | 取用戶號碼 → 處理 `OFD701` → 舊資料收尾 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:1062-1360` |

`AfterApproveDelete`(刪除覆核後)要把終止 / 暫停還原,SQL 是這樣組的:

```
strSQL = "BEGIN " + this.CancelStop(row1);
strSQL += this.CancelStop(row1) == "" ? "" : ";";
strSQL += this.CancelPause(row1) + "END;";
if (strSQL != string.Empty) { … 執行 … }
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-583`。兩個問題:`CancelStop(row1)` 被呼叫兩次(第二次只為了判斷要不要加分號);而 `strSQL` 永遠至少是 `"BEGIN END;"`,所以 `if (strSQL != string.Empty)` **永遠成立**,那個守衛等於沒寫。兩段都空的時候會送一個空的 PL/SQL 區塊給資料庫。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 查詢條件必須擇一填寫 | 全空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:516` |
| UI 查詢 | 異動收件日期(起)(迄)必須皆填或皆不填 | 只填一邊 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:521` |
| UI 查詢 | 異動收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:525` |
| UI 存檔 | 異動收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:135` |
| UI 存檔 | 異動收件日期 < 契約收件日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:140` |
| UI 存檔 | 扣款日限額 | 超限 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:232` |
| UI 存檔 | 主檔沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:644` |
| UI 存檔 | 明細沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:807` |
| UI 存檔 | 不可異動「鎖利定額」契約 | — | **整段被註解,現在不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:248` |
| PO 新增 | 鎖不住契約列 | 影響 0 列 | 阻擋 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:419-420` |
| PO 新增 | 契約未覆核且無扣款且無其他變更書 | 三者同時成立 | 阻擋(條件過嚴,見上) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:435-436` |
| PO 四眼各段 | 跳號紀錄寫入失敗 | 回 false | 阻擋,訊息空白 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:559` |

### 4.3 `RSPM020` — 母子基金設定

#### 用途(推測)

168 循環定額投資法要先知道「哪些母基金可以配哪些子基金」。這支畫面就是那張白名單:一張 `RE_RSP_NO`(母子基金設定書號)底下,`RSP062A` 掛 N 檔母基金、`RSP063A` 掛 N 檔子基金,主檔再放兩個金額門檻。

這是全模組**最小的一支 M**:UI 436 行、PO 200 行、Control 116 行,沒有彈出視窗。

#### 主檔只有兩個業務欄位

| 欄 | 中文名 | 檢核 |
|---|---|---|
| `LOWER_LIMIT_AMT` | 最低申購金額 | 不可為 0 |
| `LOWER_SWITCH_AMT` | 最低轉申購金額 | 不可為 0 |

錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM020Model.xsd:15`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:382`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:390`。

`LOWER_LIMIT_AMT` 就是 `RSPM021` 在「合計金額低於母基金最低申購金額」那條檢核用的門檻(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267`)。

#### 兩個 grid,四條一模一樣的檢核

| grid | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| `ugrdMOM` | 母基金代碼為必填 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:398` |
| `ugrdMOM` | 母基金代碼重覆 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:403` |
| `ugrdMOM` | 母基金資料必須輸入(一列都沒有) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:408` |
| `ugrdSON` | 子基金代碼為必填 / 重覆 / 必須輸入 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:415`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:420`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:425` |

「必填」那兩條在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281` / `:293` 與 `:398` / `:415` 各寫了一次,一次在逐列事件、一次在存檔前,**兩套規則兩個地方**,改一邊會漏。

`App.config` 另外對兩個 grid 下了 `required="true"`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:169-170`),這是框架層的第三道。

#### 「執行類別」是死的

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:82` 有一行被註解掉的下拉設定(`GetDropDownDataSrc("309")` 綁 `EXE_TYPE`),`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` 有一條被註解掉的「執行類別 為必填欄位」。也就是子基金原本要分類別,後來取消了,但**欄位與檢核的外殼都留著**。

#### 伺服端

`RSPM020_PO` 只有 200 行,掛一個 `BeforeGetMaintainData` 組三段取數 SQL,沒有任何 `BeforeAdd` / `BeforeUpdate`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-120`)。**這支畫面在伺服端零卡控**,而它控制的是整條 168 業務線能配哪些基金——繞過 UI 就能塞任意基金代碼進去。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 逐列 | 母 / 子基金代碼未填 | 空 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:281`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:293` |
| UI 存檔 | 最低申購金額 = 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:382` |
| UI 存檔 | 最低轉申購金額 = 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:390` |
| UI 存檔 | 母基金代碼重覆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:403` |
| UI 存檔 | 母基金一列都沒有 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:408` |
| UI 存檔 | 子基金代碼重覆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:420` |
| UI 存檔 | 子基金一列都沒有 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:425` |
| UI 存檔 | 執行類別未填 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` |
| PO | (無) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM020_PO.cs:36-38` |

### 4.4 `RSPM021` — 168 循環定額投資契約

#### 用途(推測)

168 循環定額投資法:客戶拿一筆既有的母基金申購書當本金,約定每月 6 / 16 / 26 日其中幾天,把母基金贖回一部分轉申購到指定的子基金;子基金漲到停利點就自動出場。這支畫面建立那張契約(`RSP070A` 主檔 + `RSP071A` 子基金明細 + `RSP072A` 綁定的申購書清單)。

規模:UI 2,309 行 + 彈窗 `RSPM021p0` 1,109 行 + PO 1,189 行。

#### 三層資料的意思

| 表 | 一筆代表 | 關鍵欄 |
|---|---|---|
| `RSP070A` | 一張 168 契約 | `MOM_FUND_ID` 母基金、`REDEM_DATE` 約定轉申購日(值域見 §2.5)、`RSP_EFFECT_DATE` 契約生效日、`FIRST_SUB_DATE` 首次轉申購日、`REDEM_FEE_RATE1`–`3`、`INVEST_TYPE` 投資型態、`GAIN_STOP` 終止停利設定 |
| `RSP071A` | 契約下的一檔子基金 | `SON_FUND_ID`、`RSP_AMT1` 約定轉申購金額、`LOCK_POINT` 停利點、`LOCK_FEE_RATE` 停利轉申購手續費率 |
| `RSP072A` | 綁定的一張母基金申購書 | `ALLOT_NO` + `ALLOT_SRNO` + `ALLOT_DATE`、`DATA_TYPE`、`REPRICE_DATE` 加碼生效日 |

`RSP_DATA` 是畫面上挑申購書用的暫存 DataTable(不是實體表),欄位有 `ISCHECK` / `ALLOT_AMT` / `PRE_ALLOT` / `ALLOT_PROC_CODE`(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM021Model.xsd:472`)。

#### 挑申購書那一段的四條檢核

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:225-300`(新增時)與 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:340-390`(修改時)是**兩份幾乎一樣的程式碼**:

| 檢核 | 成立時 | 結果 | 錨點(新增 / 修改) |
|---|---|---|---|
| 至少勾一筆申購明細 | 一筆都沒勾 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:253` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:354` |
| 新契約只能勾一筆 | 勾超過一筆 | 阻擋(訊息指路「如有多張申購書需透過異動作業作加碼」) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:256` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:356` |
| 合計金額 ≥ 母基金最低申購金額(`RSPM020` 設的 `LOWER_LIMIT_AMT`) | 低於 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:366` |
| 申購書已被贖回過不可當 168 資金 | `Chk_Allot_Partial` 回 true | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:278` / `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:377` |

**合計金額是用 `Convert.ToInt64` 累加的**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:242`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:246`),不是 `decimal`。`ALLOT_AMT` 為 0 時改抓 `PRE_ALLOT`(預估申購金額)。金額走整數型別在全庫是異數——`architecture.md §4.6` 實測「金額欄位沒有用 float / double,`Convert.ToDecimal` 3,029 次 vs `Convert.ToDouble` 18 次」,這裡是 `ToInt64`,小數會被四捨五入掉。列入附錄 E。

#### 首次轉申購日會被系統改掉,而且只是「通知」

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:282-295`:拿選到的申購書算出受短線交易 / 員工閉鎖限制後的最早可轉申購日,如果比畫面上填的還晚,跳一個 `Info01`:「首次轉申購日期未符合短線交易/員工閉鎖之限制日期,將被變更為 yyyy/MM/dd(次一扣款日)」——**只有訊息,使用者按掉之後值就被改了**,不是詢問也不是阻擋。歸類為「警示」。

另一條相關檢核在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1835`:「首次轉申購日期需大於【境內基金基本資料(OFDM081A)的『基本資料(一)畫面』的『開始買回日期』】!!」——這條是阻擋。

#### 刪除契約的兩道關

| 檢核 | 現況 | 錨點 |
|---|---|---|
| 契約申購明細資料已結轉不可刪除 | **整段被註解掉** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:660-679` |
| 該契約已執行扣款作業不可刪除(`ChkLOG095A`) | 有效 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:683-686` |

#### 其他值得記的檢核

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 查詢條件必須擇一填寫;收件日期(起)(迄)必須皆填或皆不填;(起) 不可大於 (迄) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:163`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:167`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:172` |
| 明細資料必須輸入 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1746` |
| 此推薦人不存在該通路代碼 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1765` |
| 收件日期須為營業日 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1799` |
| 系統未存在有效 KYC | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1809` |
| 子基金與受益人設定風險等級不符 | **被註解掉** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` |
| 高收益基金需先有風險預告書 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1828` |

注意 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` 那條**風險等級檢核在 `RSPM021` 被註解、在 `RSPM022` 卻是有效的**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:556`)。**新增契約時不擋風險等級,改契約時卻擋** —— 這個不一致列入附錄 E。

#### 伺服端

`RSPM021_PO` 掛了完整一套事件(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:40-79`),但 `BeforeAdd` 只做一件事:配契約書號(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:147-154`)。`BeforeUpdate` / `AfterAdd` / `AfterUpdate` 走 `BeforeSaveDetail`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:180-203`)。六個四眼後置事件跟 `RSPM004` 一樣只寫跳號紀錄(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:634-674`)。**沒有任何業務卡控在伺服端。**

#### `RSPB025` 與這一支的差別

`RSPB025` 用同一組 DataTable(`RSPM070_Master` / `RSPM070_Detail` / `RSP072`)、同一個 `App.config` 主檔宣告(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:121` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:177`),PO 也是 `RSPM021_PO` 的平行複製(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB025_PO.cs:37-39`)。差別在可改的欄位範圍與存檔後動作,跟 `RSPM004` / `RSPB020` 的關係一樣。**兩支要一起改。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:163` |
| UI 挑申購書 | 一筆都沒勾 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:253` |
| UI 挑申購書 | 新契約勾超過一筆 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:256` |
| UI 挑申購書 | 合計金額低於母基金最低申購金額 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:267` |
| UI 挑申購書 | 申購書有贖回紀錄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:278` |
| UI 挑申購書 | 首次轉申購日不符短線 / 閉鎖限制 | 成立 | 警示(值被改掉) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:286-291` |
| UI 存檔 | 明細資料必須輸入 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1746` |
| UI 存檔 | 推薦人不屬該通路 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1765` |
| UI 存檔 | 收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1799` |
| UI 存檔 | 無有效 KYC | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1809` |
| UI 存檔 | 高收益基金無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1828` |
| UI 存檔 | 首次轉申購日 ≤ 基金開始買回日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1835` |
| UI 存檔 | 子基金風險等級不符 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` |
| UI 刪除 | 已執行扣款作業 | `ChkLOG095A` | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:683-686` |
| UI 刪除 | 申購明細已結轉 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:676-679` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:138-154` |

### 4.5 `RSPM022` — 168 循環定額投資契約變更

#### 用途(推測)

168 契約的變更書。結構跟 `RSPM005` 對 `RSPM004` 的關係一樣:`RSP073A` 主檔 + `RSP074A` 子基金變更明細 + `RSP075A` 追加的申購書,全部 `BEF_` / `AFT_` 成對,等 `RSPB023` 到了 `CHG_EFFECT_DATE` 才生效。

規模:UI 1,849 行 + 彈窗 `RSPM022p0` 1,329 行 + PO 1,047 行。

#### 可以改什麼

從 `RSP073A` 的 `CHG_xxx` 旗標欄反推,主檔層可改四項:

| 旗標 | 改什麼 | 前後欄 |
|---|---|---|
| `CHG_REDEM_DATE` | 約定轉申購日期 | `BEF_REDEM_DATE` / `AFT_REDEM_DATE` |
| `CHG_INVEST_TYPE` | 投資型態 | `BEF_INVEST_TYPE` / `AFT_INVEST_TYPE` |
| `CHG_AFEE_TYPE` | 手續費類型 | `BEF_AFEE_TYPE` / `AFT_AFEE_TYPE` |
| `CHG_REDEM_FEE_RATE` | 約定轉申購手續費率 1/2/3 | `BEF_REDEM_FEE_RATE1`–`3` / `AFT_REDEM_FEE_RATE1`–`3` |

明細層(`RSP074A`)可改:子基金代碼、約定轉申購金額(`CHG_RSP_AMT`)、停利點(`CHG_LOCK_POINT`)、停利轉申購手續費率(`CHG_LOCK_FEE_RATE`)、手續費類型、終止 / 恢復(`ISCHG_STOP_ID`)。錨點:`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:15`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM022Model.xsd:302`。

#### 主檔與明細的終止狀態要一致

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:714-724` 兩條對稱的檢核:

- 主契約已終止,明細不可有未終止的資料 → 阻擋

- 明細已終止,主契約不可未終止 → 阻擋

而 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945-970` 是寫值的那一段:`RSP_CHG_CODE == "A"`(新增子基金)或 `ISCHG_STOP_ID == "Y"` 時把 `STOP_ID` 清空,`STOP_ID` 是 `"N"` 或空字串都當「未終止」。**注意這裡同時接受空字串與 `'N'`,而 `RSPB021` 的 SQL 用 `NVL(TRIM(STOP_CD),'N') = 'N'` 判斷的是 `STOP_CD` 不是 `STOP_ID`** —— 兩個欄位、兩套判斷,不要混。

#### 加碼(追加申購書)

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:820-900` 是挑申購書的那一段,檢核與 `RSPM021` 同樣有「該筆申購書號有贖回紀錄」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:837`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:894`),多一條「未填附自主申購聲明書,無法申購!」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:853`)。

終止時的額外守衛:「明細資料已含新增資料,請先刪除新增資料後再行終止」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1511`)。

#### 一組被寫壞的訊息

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:350`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:569` 三處都是:

```
string.Format("未填附自主申購聲明書，無法申購!", d_Row.AFT_SON_FUND_ID)
```

格式字串裡**沒有 `{0}`**,所以傳進去的子基金代碼被丟掉。使用者看到的訊息不會告訴他是哪一檔基金出問題。三處都一樣,列入附錄 E。

#### 變更前後不可相同

跟 `RSPM042` 一樣有一支泛型 `Compare()`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 附近),逐欄比對,相同就報「變更前後的 X 不可相同」。主檔層另有「沒有變更任何欄位」的總檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:279`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:527`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:160` |
| UI 查詢 | 異動收件日期(起)(迄)未成對 / 起 > 迄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:165`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:169` |
| UI 存檔 | 沒有變更任何欄位 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:279`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:527` |
| UI 存檔 | 無有效 KYC | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:291`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:537` |
| UI 存檔 | 子基金與受益人風險等級不符 | 成立 | 阻擋(`RSPM021` 同條被註解) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:556` |
| UI 存檔 | 未填附自主申購聲明書 | 成立 | 阻擋(訊息漏基金代碼) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323` |
| UI 存檔 | 異動收件日期非營業日 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:706` |
| UI 存檔 | 異動收件日期 < 契約收件日期 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:711` |
| UI 存檔 | 主契約已終止但明細未終止 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:718` |
| UI 存檔 | 明細已終止但主契約未終止 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:723` |
| UI 挑申購書 | 申購書有贖回紀錄 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:837` |
| UI 終止 | 明細已含新增資料 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1511` |
| UI 存檔 | 變更前後相同 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM022_PO.cs:48-50` |

### 4.6 `RSPM037` — 離職員工契約手續費率維護

#### 用途

員工與員眷享有優惠的契約手續費率。人離職後,這些契約的費率要調回一般水準。這支畫面就是幹這件事:輸入離職日期區間(或員工代碼),列出離職員工與員眷,雙擊某人帶出他名下的定期定額契約與基金明細,改 `RSP_CNRT_FEE_RATE`,按執行。

**它不維護 `COD009`。** 全支 PO 對 `COD009` / `COD010` 只有 `SELECT` 與 `JOIN`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:85-113`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:166-175`),唯一的 DML 是:

```
Update [RSP006]
   SET [RSP006].RSP_CNRT_FEE_RATE=@RSP_CNRT_FEE_RATE
      ,UpdateID=@UpdateID
      ,UpdateDate=GetDate()
 WHERE [RSP006].RSP_NO=@RSP_NO
   AND [RSP006].RSP_SRNO=@RSP_SRNO
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:271-276`。所以 §8.1 對 `cod.md` 那一側的答案是:**`COD009` 在 RSP 只是查詢條件的來源,不是被維護的主檔;母體的「主檔於 `RSPM037`」是照 `MasterTable` 宣告推出來的假象。**

#### 這支畫面是 M 代號、一步式外殼、零四眼

`public partial class RSPM037 : xOneStepProcessForm`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:21`),`App.config` 也宣告 `formstyle = OneStep`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:192`)。其餘七支 M 都是 `xMaintainForm`。

後果:**改費率不走四眼,按下執行就進資料庫。** 更新語句只寫 `UpdateID` / `UpdateDate`,不動 `Status` 也不走 `VerifyID` / `ApproveID`。這跟 `dsm.md §0.2` 記的 `DSMM906` 是同一類例外,但 `DSMM906` 至少 override 了 `Add` / `Update` / `Delete`;`RSPM037` 是連框架流程都沒進去。

#### 查詢:兩段 `UNION`,員工與員眷

```
-- 第一段:員工本人
FROM COD009 JOIN BMS001 ON COD009.EMP_ID_NO = BMS001.ID_NO
            JOIN RSP005 ON RSP005.BF_NO = BMS001.BF_NO
WHERE 1=1 AND EMP_CD='1' <離職日期 / 員工代碼條件>
UNION
-- 第二段:員眷
FROM COD010 JOIN COD009 ON COD010.EMP_NO=COD009.EMP_NO
            JOIN BMS001 ON COD010.REL_ID_NO = BMS001.ID_NO
            JOIN RSP005 ON RSP005.BF_NO = BMS001.BF_NO
WHERE 1=1 AND EMP_CD='1' <同樣的條件>
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:85-113`。三件事:

1. **`EMP_CD='1'` 是寫死的**〔客戶特定〕。

2. 兩段都是 `JOIN`(INNER),所以**沒有任何定期定額契約的離職員工不會出現在清單上**——這是合理的,但屬於「會把資料濾掉而不提示」。

3. 契約主檔查詢(`GetRSP005`)裡,原本有一條 `AND RSP005.RCV_DATE BETWEEN A.ENTRY_DATE AND A.LEAVE_DATE`,被註解掉並附註「user不想要此功能 20090716」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:176-177`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:243-244`)。**現在會列出該員工在職期間之外簽的契約**,包含離職後才簽的。

另有一處 `UNION` 的欄位別名寫錯:`UNION SELECT REL_ID_NO, ENTRY_DATE, LEAVE_DATE AS ID_NO`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:169`)——`AS ID_NO` 掛在 `LEAVE_DATE` 上。因為 `UNION` 取第一段的欄名,實際行為不受影響,但讀起來會誤導。

#### T-SQL 殘留:這支在 Oracle 上跑不起來(假設)

| 語法 | 錨點 |
|---|---|
| `CONVERT(NVARCHAR, x, 111)` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:64` |
| `[方括號]` 識別字 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:51`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:205` |
| `ISNULL(...)` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:152` |
| `f_GetAgent()`(T-SQL TVF,Oracle 版是 `TABLE(F_TA_GetAgent())`) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184` 對照 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:230` |
| `GetDate()` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274` |
| `SqlDbType.NVarChar` / `@參數` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:279-282` |
| 無 `A` 尾碼的表名 `RSP005` / `RSP006` / `BMS001` / `OFD019` / `OFD071` / `OFD072` / `OFD081` / `OFD199` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |
| 沒有 `[PODbType(DbServerType.Oracle)]` 屬性 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:17` |

**假設**:這支畫面在現行 Oracle 環境不可用。依據是上列語法在 Oracle 皆非法、`f_GetAgent()` 的 Oracle 版全庫寫法是 `TABLE(F_TA_GetAgent())`、且沒有任何其他 RSP 程式引用 `RSP005` / `RSP006` 這兩個表名。`architecture.md §4.6` 也記載全庫 `[PODbType(DbServerType.Oracle)]` 765 次、`MSSql` 只有 12 次。**無法實測,不敢斷言**;可能是這支功能早已停用,也可能是資料庫端真的還留著同名的 SQL Server 相容物件。

#### `Execute` 的失敗分支是死的

```
int o = base.ExecuteNonQuery(dbTA, cmd, tran);
o = 1;
if (o <= 0)
{
    tran.Rollback();
    … AddResultRow(false, 0, "執行失敗，請檢查");
    return mModel;
}
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-292`。`o = 1;` 把真實影響列數蓋掉,所以 `if (o <= 0)` 永遠不成立。**更新 0 列(例如 `RSP_NO` 打錯、或那張契約根本不存在)一樣回「執行成功」。** 這是 `dsm.md 附錄 E` 記的「一律回成功」在 RSP 的同型缺陷,而且比 DSM 那支更直接——DSM 是沒有檢查回傳值,這支是主動把回傳值蓋掉。

#### 明細彈窗的費率檢核

`RSPM037p1`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:43-70`):

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 契約手續費率 < 最低手續費率(用 `DataTable.Select` 做欄位對欄位比較) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:45-46` |
| 基金尚未設定牌告永久手續費率 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:61` |
| 契約手續費率 > 牌告永久手續費率 | 阻擋,**而且 `return` 直接中斷整個迴圈** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:63-67` |

最後一條的 `return` 讓使用者一次只看得到第一檔有問題的基金,改完再按一次才看到下一檔。同一個迴圈裡的另一條檢核(「尚未設定牌告費率」)則沒有 `return`,會繼續跑。兩條規則兩種行為。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 離職日期(起) > 離職日期(迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:39-42` |
| UI 查詢 | 員工沒有任何定期定額契約 | 成立 | 過濾(無提示,INNER JOIN) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:93-94` |
| UI 查詢 | `EMP_CD <> '1'` | 成立 | 過濾(無提示) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96` |
| UI 雙擊 | 此員工無契約書資料 | 成立 | 警示 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:125` |
| UI 執行 | 一筆都沒改 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:91-97` |
| UI 明細 | 費率低於最低手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:45-46` |
| UI 明細 | 未設定牌告永久手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:61` |
| UI 明細 | 費率高於牌告永久手續費率 | 成立 | 阻擋(中斷後續檢核) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037p1.cs:65-66` |
| PO 執行 | 更新 0 列 | — | **記錄不擋**(硬寫成功) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-292` |
| PO 查詢 | 契約收件日須在在職期間 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:177` |

### 4.7 `RSPM041` — 停利轉申購契約

#### 用途(推測)

幫一張既有的定期定額契約(`RSP_NO`)加掛「停利」設定:某檔基金的餘額漲到約定停利點(`P_RATE`)且超過門檻金額(`MIN_AMT`)時,自動贖回轉申購到 `SWITCH_FUND_ID`。一張 `RSP041A` 是一個設定,主鍵 `RSP_TRN_NO`(停利轉申購契約書號),沒有明細表。

UI 888 行、PO 481 行,無彈出視窗。

#### 主要欄位與檢核

| 欄 | 中文名 | 檢核 | 結果 | 錨點 |
|---|---|---|---|---|
| `MIN_AMT` | 門檻金額 | **必須 ≥ 10000**(寫死) | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`〔客戶特定〕 |
| `P_RATE` | 約定停利點 | 必須 > 0 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:777` |
| `SWITCH_FUND_ID` | 轉出基金代碼 | 不可與 `FUND_ID` 相同 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:729` |
| `FEE_RATE` | 轉申購手續費率 | ≥ 基金最低費率;≤ 牌告費率;**不可超過牌告費率的對折** | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:816`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:836`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` |
| `FEE_RATE` | 同上 | 沒設自訂費率就報「自訂銷售手續費率尚未設定(OFDM193)」 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:846` |
| `RISK_CFD` | 風險確認 | 高收益基金必勾;受益人必須先有風險預告書 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:745`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:752` |
| — | 同一契約同一基金已有停利設定 | `CheckSameData` > 0 | 阻擋(「已有有相同交易資料,不可新增」,原文如此,多一個「有」) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |

「轉申購手續費率已超過上限之對折」那條寫成 `NoticeFeeRate * Convert.ToDecimal(0.5)`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841`),`0.5` 是 `double` 字面值再轉 `decimal`,值本身沒問題,但**「對折」這個係數寫死在程式裡**,不在任何設定表〔客戶特定〕。

#### 查詢條件

「停利書號, 收件日期(起、迄), 受益人ID, 戶號 必須擇一填寫」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:182`)+「收件日期(起) 不可大於 收件日期(迄)」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:193`)。

#### 伺服端

`RSPM041_PO` 481 行,只有取數與配號,沒有業務卡控(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42`)。`OFD138A`(收益分配行 / 帳號)被當唯讀參考表帶進 xsd(`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:169`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 四個條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:182` |
| UI 查詢 | 收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:193` |
| UI 存檔 | 轉申購基金 = 基金代碼 | 停利機制為 `1` 時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:729` |
| UI 存檔 | 高收益基金未勾風險確認 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:745` |
| UI 存檔 | 高收益基金無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:752` |
| UI 存檔 | 門檻金額 < 10000 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765` |
| UI 存檔 | 約定停利點 ≤ 0 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:777` |
| UI 存檔(新增) | 已有相同交易資料 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |
| UI 存檔 | 費率低於最低 / 高於牌告 / 超過對折 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:816`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:836`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` |
| UI 存檔 | 未設定自訂銷售手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:846` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM041_PO.cs:42` |

### 4.8 `RSPM042` — 停利轉申購契約異動

#### 用途(推測)

`RSP041A` 的變更書,主鍵 `TX_RSP_TRN_NO`(停利異動書號),掛回 `RSP_TRN_NO`。同樣 `xxx_BEF` / `xxx_AFT` 成對,等 `RSPB041` 在 `TX_DATE`(異動生效日期)當天生效。

UI 1,062 行、PO 519 行,無彈出視窗。

#### 三個明確的問題

**(1) 門檻金額的錯誤掛在錯的控制項上。**

```
if (this.unumMIN_AMT_AFT.Value != null)
{
    if (Convert.ToDecimal(this.unumMIN_AMT_AFT.Value) < 10000)
    {
        this.ValidateErrList.AddError(this.unumMIN_AMT_BEF, "門檻金額(變更後)必須大於等於10000");
    }
}
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:824-830`。判斷的是 `unumMIN_AMT_AFT`(變更後),但錯誤掛在 `unumMIN_AMT_BEF`(變更前)。使用者按錯誤清單會被帶到**唯讀的變更前欄位**。

**(2)「已有相同交易資料,不可新增」整段被註解。** `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:836-854`,與 `RSPM041` 的對應檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802`)形成落差:**建立停利設定時會擋重複,改停利設定時不會。**

**(3)「有沒有變更」是數變更前欄位。**

```
int n = 0;
if (this.unumMIN_AMT_AFT.Value != null) n++;
if (this.unumP_RATE_AFT.Value != null) n++;
if (this.custORG_FUND_ID.Value != string.Empty) n++;
if (this.custSWITCH_FUND_ID_BEF.Value != string.Empty) n++;   // BEF
if (this.unumFEE_RATE_BEF.Value != null) n++;                  // BEF
if (this.uoptJOB_CD_AFT.Value != this.uoptJOB_CD_BEF.Value) n++;
if (n == 0) { … "沒有變更任何欄位" … }
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:858-877`。六個條件裡兩個看的是 `_BEF`(變更前)欄位——變更前欄位本來就會有值,所以只要那兩個欄位非空,`n` 就不會是 0,「沒有變更任何欄位」這條**在大多數情況下不會成立**。而且 `if (n == 0)` 之後直接 `this.ValidateErrList.Show()` 卻沒有 `return`(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875-877`),後面的 `Compare()` 還是會跑。

#### `Compare()` 的空值判斷

```
if (befObj == null || aftObj == null)
    IsEquals = (befObj == null ^ aftObj != null);
```

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1018-1019`。用 XOR 表達「兩邊都是 null 才算相同」。真值表算下來結果是對的(兩邊皆 null → `true ^ false` = true),但沒有人讀得懂,而且同一支檔案裡 `RSPM022` 版本的 `Compare()` 是同樣寫法(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 附近)。改的時候兩支都要改。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI 查詢 | 四個條件全空 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:210` |
| UI 查詢 | 異動收件日期(起) > (迄) | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:221` |
| UI 存檔 | 轉申購基金(變更後) = 基金代碼 | 停利機制為 `1` 時 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:816` |
| UI 存檔 | 門檻金額(變更後) < 10000 | 成立 | 阻擋(焦點掛錯欄位) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:828` |
| UI 存檔 | 沒有變更任何欄位 | 六個計數全 0 | 阻擋(條件不可靠,且無 `return`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875` |
| UI 存檔 | 變更前後相同 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1029` |
| UI 存檔 | 費率低於最低 / 高於牌告 / 超過對折 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:924`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:944`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:949` |
| UI 存檔 | 未設定自訂銷售手續費率 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:954` |
| UI 存檔 | 高收益基金未勾風險確認 / 無風險預告書 | 成立 | 阻擋 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:968`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:975` |
| UI 存檔(新增) | 已有相同交易資料 | — | **被註解,不擋** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:852` |
| PO | (無業務卡控) | — | — | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM042_PO.cs:42` |

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

掃描母體 56 支畫面裡 I 是 0,實際比對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/` 也確實沒有任何 `RSPI*`。

原因(推測,三條依據):

1. **查詢需求被 31 支報表吸收了。** 其中至少兩支的行為就是查詢畫面:`RSPR064`「168循環定額投資法客戶查詢報表」(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR064.cs:106`)、`RSPR070`「業務受益人定額停扣明細報表」有四種標題可選並直接出 Excel(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:177-190`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR070.cs:234-258`)。`RSPR049` 更是完全不出 Crystal Report,只吐 `.xlsx`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84`)。

2. **維護畫面自己就有夠強的查詢頁。** 八支 M 都是 `xMaintainForm`,第一個頁籤就是條件查詢 + 結果 grid,`App.config` 還替四支宣告了 `ugrdResult` 的欄位白名單(`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:152`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:160`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:178`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/App.config:186`)。要查契約就開 `RSPM004` 查詢頁,不必另建 I。

3. **兩支掛 `xMaintainForm` 的 B(`RSPB020` / `RSPB025`)補上了「只想改業務欄位」的情境**,那本來也可能被做成 I + 另一支維護。

**要小心的是:因為沒有 I,所有「只想看不想改」的需求都是透過 M 畫面的查詢頁達成的,而 M 畫面的查詢頁沒有任何資料範圍權限**(不像 `dsm.md §5.3` 的 `DSMI001` 有 `CRM002A` 的權限 INNER JOIN)。RSP 的取數 SQL 一律 `LEFT JOIN` 對照表、`WHERE 1=1` 起手,能開畫面的人就看得到全部契約。功能權限由 PTPF 決定(`architecture.md §3.7`),資料權限在程式裡看不到。

## 6. 批次(B)與 WindowsService

```text
[圖] RSP 批次群與 RSPB008_Service 的觸發關係:兩個入口、排程來源、一日扣款鏈、三支變更生效批次
圖中文字:① 兩個入口打同一支 SP,但只有一個會擋未覆核 / RSPB008 畫面 / UI 到 Pxy 走 Remoting / CheckStatus / 未覆核就阻擋 / RSPB008_Ctl / Control 層 / s_TA_RSPB008_Excute_M / 版控外 SP / RSPB008_Service / Timer 60 秒 寫死 / 沒有 CheckStatus / 排程不擋未覆核 / ② 服務怎麼決定什麼時候跑、跑完做什麼 / CTL016.RSP_PROC_TIME / rownum=1 無 ORDER BY / 比對 HHmm / 相等才執行 / UserID = AutoJob / DATE = 今天 / Program.cs 無 UserName 判斷 / 只能當服務跑 / GetOFD681 / SEND_TYPE=6 寄信 / EventLog / Success / Error / C:/Vendor/WindowService/ / RSPB008_yyyyMMdd.txt / finally 再讀一次時刻 / 改設定不用重啟 / ③ 一日扣款鏈:八支批次,前一支沒跑後一支會被擋 / RSPB009 / 產生扣款 / RSPB010 / 送件 / RSPB011 B015 / 回覆確認 / RSPB016 / 單位數計算 / RSPB018 / 結轉 / RSPB019 淨值回復 / 回復後從 B016 重跑 / ④ 三支變更生效批次:結構相同,比較運算子不同 / RSPB008 / CHG_EFFECT_DATE 用 = / RSPB023 / CHG_EFFECT_DATE 用 <= / RSPB041 / TX_DATE 用 <= / 漏跑一天不會被補 / RSPB008 專有風險
```

*圖:圖 4 批次與服務。橘框=真正的關卡;橘虛框=風險或寫死值〔客戶特定〕;黑框=版控外。最重要的一條:RSPB008 畫面會先擋「還有未覆核的變更書」,RSPB008_Service 直接跳過那道檢核,時間到就跑,而且它不是 Remoting 客戶端,直接 new RSPB008_Ctl 在同一個行程裡打資料庫。*

17 支 B 裡:

- **2 支不是批次**(`RSPB020` / `RSPB025`,`xMaintainForm`),已在 §4.1 / §4.4 交代。

- **13 支只是 SP 的外殼**:自己開交易 → 呼叫 SP → 看回傳決定 commit / rollback。

- **2 支自己寫 DML**:`RSPB011`(扣款回覆逐筆確認)與 `RSPB052`(連續扣款失敗契約終止)。

- **1 支有專屬 WindowsService**:`RSPB008`。

### 6.1 共同模式一覽

| 畫面 | 觸發 | 主要輸入 | SP | 寫哪些表 | 執行前檢核 | 失敗處理 |
|---|---|---|---|---|---|---|
| `RSPB008` | 人工按執行 **或** `RSPB008_Service` 排程 | 變更生效日期、異動收件日期、契約變更書號 | `s_TA_RSPB008_Excute_M` | `RSP007A` `RSP013A` → `RSP005A` `RSP006A` | `CheckStatus`:`RSP007A` 還有非已生效狀態就擋(**服務端不跑這段**) | 讀 RefCursor 的 `UpdateTimes` / `CORRECT`;`OracleException` 回原訊息;其他例外回「執行失敗,請檢查」 |
| `RSPB009` | 人工 | 契約扣款日期、實際扣款日期、執行功能(產生 / 重作 / 刪除)、代理扣款機構、三種扣款方式勾選、基金明細逐檔勾選 | `S_TA_RSPB009_Excute`(**逐檔基金呼叫一次**) | `RSP008` `RSP008A` `CTL006A` | 契約扣款日期有效、註銷戶詢問、是否已有扣款日期 | 見 §6.4 |
| `RSPB010` | 人工 | 契約 / 實際扣款日、基金、扣款方式、扣款銀行、更新後實際扣款日與淨值日、需重新送件 | `EXEC s_RSPB010_Excute …`(**T-SQL 字串**) | `RSP008` | 淨值日已過帳 / 已結轉;實際扣款日已算淨值 / 已最後確認;已有扣款資料不做延遲扣款 | `ExecuteNonQuery` 回 0 就 rollback |
| `RSPB011` | 人工 | 逐筆勾選扣款成功 / 失敗 / 扣款中,含失敗原因 | **無**,自己寫 SQL | `RSP008A` | 小額扣款控制碼四段(見 §6.5) | `ExecuteNonQuery` 回 0 就「執行失敗,請檢查」 |
| `RSPB015` | 人工 | 扣款行、基金、確認 | `S_TA_RSPB015_Excute` | `RSP008A` | 無 | SP 的 `strMsg` OUT 非空就 rollback |
| `RSPB016` | 人工 | 基金、契約 / 實際扣款日 | `S_TA_RSPB016_Excute` | `RSP008A` | 「無符合資料可執行」 | 同上 |
| `RSPB018` | 人工 | 基金明細逐檔 | `S_TA_RSPB018_Excute`(**逐檔基金一個交易**) | `RSP008A`、`LOG017A` 讀 | `OFD303A.RSP_CTL_CODE` + 淨值一致性(見 §6.6) | `strMsg` OUT 非空就 rollback 並 `return` |
| `RSPB019` | 人工 | 基金、淨值、申購書號區間、回復說明 | `S_TA_RSPB019_Excute` | `RSP008AA` | 無 | `strMsg` OUT 非空就回訊息 |
| `RSPB021` | 人工 | 執行功能(扣款產生 / 刪除重作)、母基金、契約轉申購日 | `S_TA_RSPB021_EXCUTE` | 版控外 | `ValidateOFD303A`(母 + 子兩段);`ValidateLOG095A` **被註解** | `MSG` OUT 非空就 rollback |
| `RSPB022` | 人工 | 執行功能(停利計算 / 刪除重作)、標的基金、停利日期 | `S_TA_RSPB022_EXCUTE` | 版控外 | `ValidateLOG094A` + `ValidateOFD303A` | 同上 |
| `RSPB023` | 人工 | 異動生效日 | `S_TA_RSPB023_EXCUTE` | `RSP073A` `RSP074A` → `RSP070A` `RSP071A` | `CheckStatus`(查 `RSP073A`) | 同上 |
| `RSPB024` | 人工 | 基金、契約轉申購日 | `S_TA_RSPB024_EXCUTE` | 版控外(產 Email 資料) | 只擋「轉申購日須為 6/16/26」 | RefCursor 第一列 = 0 就回「無資料寄發」 |
| `RSPB041` | 人工 | 變更生效日期 | `S_TA_RSPB041_EXCUTE` | `RSP042A` → `RSP041A` | `CheckStatus`(查 `RSP042A`) | `MSG` OUT 非空就 rollback |
| `RSPB042` | 人工 | 執行功能、原始基金、停利日期 | `S_TA_RSPB042_EXCUTE` | 版控外 | `ValidateLOG109A` + `ValidateOFD303A` | 同上 |
| `RSPB052` | 人工 | 連續扣款失敗次數門檻、基金,逐筆勾選 | **無**,自己寫 SQL | `RSP007A` `RSP013A` `RSP005A` `RSP006A` | 無 | 見 §6.7 |

**「觸發」欄全部是人工**,只有 `RSPB008` 例外。repo 內沒有任何排程設定檔、`sc.exe` 呼叫或 Task Scheduler 匯出檔——除了那一支 WindowsService,RSP 的批次全靠人按按鈕。

### 6.2 `RSPB008` — 定期定額契約變更生效

#### 它到底做什麼

把已覆核的契約變更書(`RSP007A` + `RSP013A`)套用到契約主檔(`RSP005A` + `RSP006A`)。三個輸入參數(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:118-123`):

| 參數 | 畫面欄位 | 給 SP 的名字 | 說明 |
|---|---|---|---|
| `DATE` | 變更生效日期 | `datiDATE` | 挑 `RSP013A.CHG_EFFECT_DATE` 等於這天的 |
| `CHG_DATE` | 異動收件日期 | `datiCHG_DATE`(去掉 `/`) | `19000101` 代表不限 |
| `RSP_CHG_NO` | 契約變更書號 | `striRSP_CHG_NO` | 空字串代表不限 |
| `UserID` | — | `striUserID` | 畫面是 `base.UserID`,服務是字串 `"AutoJob"` |

SP 回一個 RefCursor,程式取第一列的兩個欄位(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:84-110`):

| 欄 | 用途 |
|---|---|
| `UpdateTimes` | 處理筆數。`0` → rollback,回「查無可執行之資料」 |
| `CORRECT` | `'Y'` → 有更新失敗的資料,訊息改成「執行完成 本次有更新失敗資料,請執行(RSPR038)定期定額契約異動資料查核表,查詢明細資料」,**而且 `ReturnCode` 給 `false`** |

`CORRECT = 'Y'` 時 `AddResultRow(false, 0, …)` 但**接著還是 `tran.Commit()`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:102-108`)。也就是「部分成功」被當成失敗回報,資料卻已經寫進去了。畫面端只有 `Result.Count == 2` 時才多跳一個訊息(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:128-131`),而 PO 永遠只 `AddResultRow` 一次,**那段畫面程式是死碼**。

#### 執行前檢核(只有畫面端跑)

```
SELECT COUNT(1)
  FROM RSP007A, RSP013A
 WHERE RSP007A.Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))
   AND (:CHG_DATE = '19000101' OR RSP007A.CHG_DATE = :CHG_DATE)
   AND RSP013A.CHG_EFFECT_DATE = :CHG_EFFECT_DATE
   AND RSP007A.RSP_CHG_NO = RSP013A.RSP_CHG_NO
   AND (:RSP_CHG_NO IS NULL OR RSP007A.RSP_CHG_NO = :RSP_CHG_NO)
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158`。`> 0` 就回訊息「仍有資料未覆核,不可執行」,畫面把它塞進 `ValidateErrList` → 阻擋(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:48-52`)。

三件事:

1. `:RSP_CHG_NO IS NULL OR …` —— 畫面傳的是 `utxtRSP_CHG_NO.Text.Trim()`,沒填就是**空字串不是 NULL**。Oracle 把空字串當 NULL,所以這條碰巧成立;但同一支程式的 `CHG_DATE` 用的是哨兵值 `'19000101'`,兩種寫法混用。

2. 這是 `FROM A, B WHERE A.k = B.k` 的舊式 join 寫法,跟同模組其他地方的 `JOIN … ON` 不一致。

3. **`RSP013A.CHG_EFFECT_DATE = :CHG_EFFECT_DATE` 是等於不是小於等於**,跟 `RSPB023` / `RSPB041` 的 `<=` 不同(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:111`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:110`)。**漏跑一天,那天的變更書就不會被這條檢核看到**,下一次執行也不會被擋——三支同型批次三種比較運算子,列入附錄 E。

畫面另有兩條自己的檢核(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:68-74`):變更生效日期不可為空、不可大於系統日。

#### 被註解掉的郵局限額檢核

`CheckDayLmtAmt` 在 PO 與 UI 兩側都被整段註解,PO 側註解標題寫「檢核郵局每日交易限額(改寫在 StoredProcedure 裡檢核)」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:54-66`)。被註解的那段是 T-SQL(`ISNULL` / `CONVERT(NVARCHAR,…,111)` / `@DATE`),讀 `OFD019.DAY_LMT_AMT`、用 `BankBizHelper.GetBankHQ` 判斷是不是郵局(`700`)。**現在這條規則只存在於版控外的 SP,repo 內查不到門檻值。**

### 6.3 `RSPB008_Service` — 唯一的 WindowsService

安裝方式、服務帳號(`LocalSystem`)、`InstallUtil` 指令與部署要帶的 DLL,`runbooks/deploy.md §5` 已經查過,**直接引用不重做**。這裡只補它做什麼、跟畫面的關係、以及執行模式怎麼判。

#### 它做什麼

| 階段 | 行為 | 錨點 |
|---|---|---|
| 建構 | 建一個 `System.Timers.Timer`,`Interval = 60000`(**寫死 60 秒**),`Enabled = true` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:23-27` |
| `OnStart` | 只做一件事:`GetTIMES()` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:29-33` |
| `GetTIMES` | `ctl.GetExecTime(view)` → PO 跑 `SELECT RSP_PROC_TIME FROM CTL016 where rownum=1`,把值存進欄位 `sTIMES`,並寫一筆 EventLog「Message:Next Execute Time is HHmm」 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:86-107`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:294-330` |
| 每 60 秒 | `if (sTIMES != "" && sTIMES == DateTime.Now.ToString("HHmm"))` 才動作 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:42` |
| 到點時 | 組四個參數 → `ctl.Execute(view)` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:46-54` |
| 執行後 | 不論成敗都呼叫 `ctl.GetOFD681(訊息)` 寄通知信 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:55-62` |
| 執行後 | 寫 EventLog(Success / Error)+ 寫檔到 `C://Vendor//WindowService//RSPB008//RSPB008_yyyyMMdd.txt` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:64-73`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:111-148` |
| `finally` | 再 `GetTIMES()` 一次,重新讀下一次的排程時刻 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:79-82` |
| `OnStop` | **空的** | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:35-38` |

服務固定送的三個參數(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:49-52`):

| 參數 | 值 | 意義 |
|---|---|---|
| `DATE` | `DateTime.Today`(`yyyy/MM/dd`) | 只處理「今天生效」的變更書 |
| `CHG_DATE` | `new DateTime(1900,1,1)` | 哨兵值,不限異動收件日 |
| `RSP_CHG_NO` | `string.Empty` | 不限單一變更書號 |
| `UserID` | **`"AutoJob"`** | 排程身分,會寫進 `RSP005A` / `RSP006A` 的 `UpdateID` |

#### 執行模式怎麼判:它根本不判

`runbooks/deploy.md §5.3` 記三支 `OFDB*` 服務用 `Environment.UserName == "SYSTEM"` 區分「服務模式」與「除錯模式」。**`RSPB008` 沒有這段。** 它的 `Program.cs` 只有:

```
ServicesToRun = new ServiceBase[] { new RSPB008_Service() };
ServiceBase.Run(ServicesToRun);
```

`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/Program.cs:22-24`。全專案 grep `Environment.UserName` 0 次。

實務上的三個結論:

1. **改服務帳號不會讓 `RSPB008` 啟動失敗**(那是三支 `OFDB*` 才有的雷),因為它無條件走 `ServiceBase.Run`。

2. **反過來,它也不能用命令列跑起來除錯。** 直接雙擊 exe 會被 SCM 拒絕(`ServiceBase.Run` 在非服務環境會失敗)。要驗證行為只能裝成服務,或改用 `RSPB008` 畫面手動跑同一支 SP。

3. **「什麼時候該執行」完全由 `CTL016.RSP_PROC_TIME` 決定**,不是由服務或設定檔決定。這張表 `SELECT … where rownum=1`,只認第一列(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:301-302`),表內若有多列,哪一列被拿到取決於 Oracle 的回傳順序——**沒有 `ORDER BY`**。

#### 它跟 `RSPB008` 畫面的關係

同一支 `RSPB008_Ctl` / `RSPB008_PO` / 同一支 SP,兩個入口:

| 面向 | `RSPB008` 畫面 | `RSPB008_Service` |
|---|---|---|
| 呼叫層 | UI → `RSPB008_Pxy`(Remoting)→ Control → PO | **直接 `new RSPB008_Ctl()`,同一個行程** |
| `CheckStatus`(未覆核就擋) | 有 | **沒有** |
| 變更生效日期 | 使用者輸入,且會擋「不可大於系統日」 | 固定今天 |
| 異動收件日期 / 變更書號 | 使用者可縮小範圍 | 固定不限 |
| `UserID` | 登入者 | `"AutoJob"` |
| 寄通知信 | 不寄 | **每次都寄**(`OFD681` 的 `SEND_TYPE = '6'`) |
| 落地 log | 無 | `C://Vendor//WindowService//RSPB008//` + EventLog |
| 錨點 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:105-124` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:40-84` |

**最重要的一條:服務不做未覆核檢核。** 排程時間到了,不管 `RSP007A` 裡還有多少張沒覆核完的變更書,SP 照跑。要確認結果只能看 `RSPR038` 或那個 txt log。

#### 它不是 Remoting 客戶端,而且自帶連線字串

`architecture.md §8.4` 說四支服務都是 Remoting 客戶端、透過 `_Pxy` 打伺服端、不直接碰資料庫。**這句對 `RSPB008` 不成立**,三個證據:

| 證據 | 錨點 |
|---|---|
| 用的是 `RSPB008_Ctl`(Control 層)不是 `RSPB008_Pxy` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:47` |
| csproj 只參考 `Control.RSP` / `UIEntity.RSP` / `TA.MappingCode`,**沒有 `FormProxy.RSP`** | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/WindowsService.RSPB008.csproj:112-123` |
| 全專案 `RemotingConfiguration` 出現 0 次(對照 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50`) | grep 結果 |

它的 `App.config` 自帶五組連線字串,**含明碼帳密**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:72-78`):`SWProduct` / `TA` / `Logging` 指向 `AGITest` 的 `sa` / `sa`,`SWEMail` / `TIPS` 指向 `test002` 的 `TAAdmin`。這些是 `System.Data.SqlClient` 的 SQL Server 連線字串——與 PO 端 `new Database("TA", DbServerType.Oracle)` 不符,**假設**這幾組是舊環境殘留、實際連線由 PTPF 平台的設定接管;依據是 PO 建構子明確指定 Oracle,而這份 config 的值(`AGITest` / `sa` / `sa`)一看就是開發機。〔客戶特定〕

#### 值得寫成 runbook 的三個運維點

1. **改排程時間**:改 `CTL016.RSP_PROC_TIME`,服務**不用重啟**——每次執行完的 `finally` 都會重讀一次(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:79-82`)。但如果從沒執行過,只有 `OnStart` 那一次讀過,**改了要等下一次執行才生效,或重啟服務**。

2. **看它有沒有跑**:先看 EventLog(來源 = 服務名),再看 `C://Vendor//WindowService//RSPB008//RSPB008_<日期>.txt`。那個檔每次寫入會先把整份讀進來再整份重寫(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:133-146`),檔案大了會愈來愈慢,而且**沒有任何清檔機制**。

3. **`WriteLog` 用 `Encoding.Default`**(`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:135`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:141`),不是 UTF-8。中文在非 CP950 的機器上會變亂碼。

### 6.4 `RSPB009` — 產生扣款資料(逐檔基金呼叫 SP)

這支是扣款作業的起點,也是 17 支裡結構最特別的一支:**SP 不是呼叫一次,是對畫面上勾選的每一檔基金各呼叫一次,全部包在同一個交易裡**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:53-94`)。

三種執行功能(Designer 的 `valueListItem`):產生扣款資料 / 重作扣款資料 / 刪除扣款資料,用 `striADMINISTER` 傳給 SP。三種扣款方式(一般 / ACH / 財金)用三個獨立的 `striSEAL_CHK_CODE1`–`3` 傳。

#### 一個永遠不會被執行的 catch

```
catch (SqlException sqlex)
{
    if (Convert.ToString(sqlex.Number) == "2627")
    {
        … AddResultRow(false, 0, "扣款檔key值重覆，請先執行[刪除扣款資料]功能，再執行[產生扣款資料]功能");
    }
    …
}
catch (Exception ex)
{
    … AddResultRow(false, 0, "無符合查詢條件資料可執行。");
}
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109-131`。`SqlException` 是 SQL Server 的例外型別,`2627` 是 SQL Server 的唯一鍵違反錯誤碼。**這支 PO 掛 `[PODbType(DbServerType.Oracle)]`,實際走 Oracle,主鍵重複丟的是 `OracleException`(`ORA-00001`)。** 那個貼心訊息永遠不會出現;主鍵重複會掉進下面的通用 catch,使用者看到的是「無符合查詢條件資料可執行。」——**訊息與真因完全無關,而且會誤導作業人員以為是查詢條件的問題**。

同一個通用 catch 吞掉所有例外(連線斷、SP 不存在、參數型別錯)都回同一句話。列入附錄 E,嚴重度高。

#### 三道執行前檢核

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 契約扣款日期無效 | `GetSubDate` 查不到 | 阻擋 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:744` |
| 受益人為註銷戶 | 有 | **詢問**(「…為註銷戶是否繼續執行」) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:876` |
| 是否已有扣款日期 | 有 | 回筆數給畫面自行判斷 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:933-938` |

#### 成功與否

`sb` 收集回傳 `CORRECT = 'N'` 的基金代碼,最後:

- `sb` 空 → 「執行成功」,`ReturnCode = true`

- `sb` 非空 → 「執行完成。基金[…] 無可<執行功能名稱>」,**`ReturnCode` 還是 `true`**

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:98-107`。也就是「部分基金沒資料」不算失敗——這是合理的設計,但要知道 `ReturnCode = true` 不代表每一檔都處理到了。

### 6.5 `RSPB011` — 扣款回覆逐筆確認(唯一自己寫 SQL 的回覆作業)

畫面提供「全部扣款成功」「全部扣款中」兩顆快速鈕,以及逐筆改 `SUB_STATUS` / `NONSUCS_CODE`(扣款失敗代碼),下方即時顯示成功 / 失敗 / 合計的筆數與金額。

執行前跑 `CheckSmallAmountCode`,四段檢核都回 `ReturnCode = true` 只是訊息不同(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:379-399`):

| 訊息 | 意思 |
|---|---|
| 契約扣款日期、實際扣款日期必須存在境內小額扣款日期控制檔 | 日期組合沒建在控制檔 |
| 基金[…]已做扣款回覆確認,不可再異動 | 已經跑過 `RSPB015` |
| 基金[…]已做單位數計算,不可再異動 | 已經跑過 `RSPB016` |
| 基金[…]已做結轉,不可再異動 | 已經跑過 `RSPB018` |

另有一條「此扣款行已作回覆確認,不可再異動」在 `Execute` 內(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB011_PO.cs:142`)。

**這四段檢核回的 `ReturnCode` 一律是 `true`**,靠訊息非空來判斷有沒有問題。跟 `RSPB008.CheckStatus` 是同一套約定(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:172`),但跟 `RSPB021.ValidateOFD303A`(有問題時回 `false`)相反(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:192`)。**同一個模組兩種相反的約定**,改的時候不要照抄隔壁那支。

### 6.6 `RSPB018` — 結轉(檢核訊息是在 SQL 裡拼出來的)

執行前的檢核不是 C# 寫的,是一大段 `CASE WHEN … THEN '訊息'` 直接在 SQL 裡產出中文訊息(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:78-102`):

| 條件 | 訊息 |
|---|---|
| `OFD303A.RSP_CTL_CODE = '3'` | 本日定期定額申購資料已結轉 |
| `OFD303A.RSP_CTL_CODE = '1'` | 請先執行單位數計算作業 |
| 存在 `RSP008A.NAV_B <> OFD081V.FUND_FACE_AMT` 的資料 | 有部份資料的淨值與目前的淨值不同,請重新執行單位數計算作業 |

執行時對每一檔基金**各開一個交易、各自 commit**,註解寫「20100531, Modify by rgb for 每一檔基金執行完成後即 Commit 以減少 Dead Lock 發生」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:209-241`)。後果:**跑到一半失敗,前面已經結轉的基金不會回滾**,只有當下那一檔 rollback 然後 `return`。這是刻意的取捨,但操作手冊必須寫清楚——重跑之前要先確認哪些基金已經結轉過。

跑完會去 `LOG017A` 查有沒有 `TRAN_TYPE = '1'` 的資料,有就在成功訊息後面加「,請列印法人公告警示表」(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:243-264`)。

### 6.7 `RSPB052` — 連續扣款失敗契約終止(繞過四眼的那一支)

#### 它做什麼

畫面輸入「連續扣款失敗次數」門檻與基金,列出達標的契約明細,勾選後按執行。程式對每一筆(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:113-439`):

1. 用 `SerialNo.GetRspChgNoForNfd()` 配一張**契約變更書號**

2. 讀 `RSP005A` + `BMS001A` 組出主檔資料(`TRAN_TERM` 由 `BMS001A.TRAN_FAX_CD` 用 `DECODE` 轉)

3. `INSERT RSP007A`(變更主檔)

4. `INSERT RSP013A`(變更明細,`RSP_CHG_CODE = 'M'`,`CHG_EFFECT_DATE` = 今天)

5. `UPDATE RSP006A` / `UPDATE RSP005A` 設 `STOP_ID = 'Y'`、`STOP_CD = '01'`、`STOP_DATE` = 今天

#### 它把四眼欄位自己填成「已覆核」

```
UseCaseSecurity.SetFunctionSecurityData(row, mModel, EVAType.Add);
row.STATUS = "301";
row.APPROVEID = row.UPDATEID;
row.APPROVEDATE = row.UPDATEDATE;
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:134-137`。先用框架方法設四眼欄位,**再手動把 `STATUS` 蓋成 `'301'`、把覆核人蓋成自己**。產出的 `RSP007A` / `RSP013A` 一出生就是已覆核狀態,不會進任何人的待辦。

這是刻意的(批次終止不應該還要人覆核),但兩個後果要知道:

1. **`RSPB008` 的「仍有資料未覆核」檢核看不到這些變更書**,因為它們已經是已生效狀態。

2. **`'301'` 是寫死的字串**,如果哪天四眼狀態值域改了,這裡不會跟著改。同一個常數在 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183` 與 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` 各寫了一次。

#### 跟 `RSPM037` 同型的「一律回成功」

```
int RSP005 = dbProduct.ExecuteNonQuery(cmdUpdRSP005, tran);
RSP005 = 1;
if (RSP005 <= 0) { … rollback … return … }
else { … AddResultRow(true, 1, "") … }
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:417-432`。**更新 0 列(契約已被別人終止、`RSP_NO` 不存在)照樣回成功,而且 `RSP007A` / `RSP013A` 的變更書已經寫進去了。** 結果是:資料庫裡有一張「終止」的變更書,主檔卻沒有被終止,兩邊對不起來。這是全模組最會咬人的一條,列入附錄 E。

注意同一支的 `INSERT RSP007A` 那段**沒有**被蓋掉回傳值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:164-172`),所以插入失敗會正確 rollback。**同一個方法裡兩種處理方式**。

#### 兩個交易、沒有分散式交易

`dbProduct`(業務庫)與 `dbPTPF`(配號 / 待辦庫)各開一個交易(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:110-111`),最後各自 commit(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:440-441`)。兩次 commit 之間若掛掉,會出現「號碼配掉了但變更書沒寫進去」。這是 `architecture.md §4.7` 記的全庫性問題,RSP 這支是其中一個實例。

#### 一行寫了兩次的參數

```
dbProduct.AddInParameter(cmdInsertRSP013, "CHG_UPD_DTTM", …); dbProduct.AddInParameter(cmdInsertRSP013, "CHG_UPD_DTTM", …);
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:193` —— 同一個參數在同一行加了兩次。Oracle 的 `ManagedDataAccess` 預設 `BindByName = false` 時會按位置綁,多一個參數就會讓後面所有參數錯位。目前這支能跑代表框架有設 `BindByName = true`(**假設**,依據是全模組大量使用具名參數且順序與 SQL 不一致),但這一行仍是明顯的複製貼上殘留。

### 6.8 三支「變更生效」批次的差異對照

| 面向 | `RSPB008`(一般契約) | `RSPB023`(168 契約) | `RSPB041`(停利契約) |
|---|---|---|---|
| 來源變更檔 | `RSP007A` + `RSP013A` | `RSP073A` | `RSP042A` |
| 生效日欄位 | `RSP013A.CHG_EFFECT_DATE` | `RSP073A.CHG_EFFECT_DATE` | `RSP042A.TX_DATE` |
| 檢核比較運算子 | **`=`** | `<=` | `<=` |
| SP | `s_TA_RSPB008_Excute_M` | `S_TA_RSPB023_EXCUTE` | `S_TA_RSPB041_EXCUTE` |
| 成敗判斷 | RefCursor 的 `UpdateTimes` / `CORRECT` | `MSG` OUT 參數 | `MSG` OUT 參數 |
| 有無 WindowsService | **有** | 無 | 無 |
| 畫面顯示結果 | `AfterExecuteButtonClicked` 判 `Result.Count == 2`(死碼) | 判 `!ReturnCode` 跳訊息 | 判 `!ReturnCode` 跳訊息 |
| 錨點 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:152-158` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:109-112` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:107-111` |

`RSPB023` 與 `RSPB041` 的 `Execute` / `CheckStatus` 是逐行相同的兩份程式碼,只差 SP 名、表名與參數名(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:41-131` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:41-130`),兩支 UI 也一樣(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB023.cs:40-92` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:40-92`)。連 `RSPB041` 的區塊註解都還寫著「檢核是否仍有未覆核的資料(RSP073A)」——**複製時沒改的註解**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:91`),實際查的是 `RSP042A`。

### 6.9 `RSPB021` / `RSPB022` / `RSPB042` 三支「刪除重作」模式

三支都有一個「執行功能」單選鈕:`1` = 正向執行(扣款產生 / 停利計算),其他值 = 刪除重作。UI 的前置檢核長這樣(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB022.cs:70-93`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB042.cs:63-86`):

```
if (TYPE == "1")
{
    … ValidateLOGxxxA(view);
    if (!view.Util.Result[0].ReturnCode)            // 已經跑過 → 擋
        AddError(udatCALC_DATE, view.Util.Result[0].ReturnMessage);
}
else
{
    … ValidateLOGxxxA(view);
    if (view.Util.Result[0].ReturnCode)             // 沒跑過 → 擋
        AddError(udatCALC_DATE, view.Util.Result[0].ReturnMessage);
}
```

意圖是對的(正向執行不能重複跑、刪除重作必須先跑過),**但 `else` 那一支用的訊息是空字串**:PO 在「沒跑過」時回的是 `AddResultRow(true, 0, "")`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:207`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:244`)。使用者選「刪除重作」而當天沒跑過時,錯誤清單會跳出一列**空白訊息**,完全不知道發生什麼事。三支都一樣,列入附錄 E。

`RSPB021` 更徹底:整段 `ValidateLOG095A` 的 UI 呼叫被註解掉,理由寫「SP已有檢核,故取消」(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:67-91`)。PO 的 `ValidateLOG095A` 與 Proxy 的對應方法都還在,**是完整的死碼**;而 SP 內到底有沒有那道檢核,repo 內查不到。

### 6.10 批次的「一律回報成功」逐支檢查

17 支逐支查「呼叫 SP / 執行 DML 之後有沒有硬寫成功」:

| 畫面 | 有無 | 說明 |
|---|---|---|
| `RSPB008` | 否 | 依 `UpdateTimes` / `CORRECT` 判斷,但 `CORRECT='Y'` 時回 `false` 卻仍 commit |
| `RSPB009` | 部分 | 有基金沒資料時仍回 `ReturnCode = true`(設計如此);但 `SqlException` catch 是死的,真錯誤訊息會被換掉 |
| `RSPB010` | 否 | `p > 0` 才 commit |
| `RSPB011` | 否 | `ExecuteNonQuery` 回 0 就報失敗 |
| `RSPB015` | 否 | 依 `strMsg` OUT |
| `RSPB016` | 否 | 依 `strMsg` OUT |
| `RSPB018` | 否 | 依 `strMsg` OUT,但逐檔 commit |
| `RSPB019` | 否 | 依 `strMsg` OUT |
| `RSPB020` | 不適用(維護畫面) | — |
| `RSPB021` | 否 | 依 `MSG` OUT |
| `RSPB022` | 否 | 依 `MSG` OUT |
| `RSPB023` | 否 | 依 `MSG` OUT |
| `RSPB024` | 否 | 依 RefCursor 第一列筆數 |
| `RSPB025` | 不適用(維護畫面) | — |
| `RSPB041` | 否 | 依 `MSG` OUT |
| `RSPB042` | 否 | 依 `MSG` OUT |
| `RSPB052` | **是** | `RSP005 = 1;` 蓋掉 `ExecuteNonQuery` 回傳值(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:418`) |

另外五支 SP 外殼(`RSPB021` / `RSPB022` / `RSPB023` / `RSPB041` / `RSPB042`)有一個共同的**回傳漏洞**:

```
T resultVdb = xVirtualDataBase.CreateNewVDB(mModel);
BasicModelVDB ResultVDB = resultVdb as BasicModelVDB;
…
catch (Exception ex)
{
    tran.Rollback();
    model.Utility.Result.Clear();
    model.Utility.Result.AddResultRow(false, 0, "執行失敗，請檢查");   // 寫進 model
    …
}
return resultVdb;                                                      // 回傳 resultVdb
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:42-98`。成功路徑把結果寫進 `ResultVDB`(會被回傳),**例外路徑卻寫進 `model`(不會被回傳)**。發生例外時呼叫端拿到的 `resultVdb` 裡 `Result` 是空的,畫面存取 `Result[0]` 會丟 `IndexOutOfRangeException`,使用者看到的是框架的通用錯誤,不是「執行失敗,請檢查」。五支一模一樣,列入附錄 E。

同五支的 `catch` 還都無條件 `tran.Rollback()` 而不檢查 `tran != null`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:87`),`BeginTransaction()` 本身失敗時會變成 `NullReferenceException` 蓋掉真因——`finally` 那邊倒是有做 null 檢查(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:95`),同一個方法兩種態度。

## 7. 報表(R)

31 支 R 畫面、39 個 `.rpt`、31 支報表 PO。

### 7.1 共同骨架

31 支長得幾乎一樣,四步:

| 步 | 做什麼 | 典型錨點 |
|---|---|---|
| 1 | `DoValidate()`:日期區間、必填 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:95` |
| 2 | `SetQueryParameters(rpt類別名, rpt檔名, 中文標題)` 決定要印哪一支報表 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:122` |
| 3 | `QueryVDB.Util.Parameters.AddParametersRow(…)` 逐一塞查詢條件 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:70-74` |
| 4 | PO 的 `GetData<T>` 呼叫 SP + `RefCursor` → `LoadDataSet` 進 typed DataSet | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:53-92` |

PO 這一層 31 支幾乎是同一份程式碼,只差 SP 名與參數清單。共同特徵:

| 特徵 | 統計 | 說明 |
|---|---|---|
| `cmd.CommandTimeout = 0` | **31 / 31** | 全部設成永不逾時,註解一律寫「此程式讓它永久跑」(`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:62`) |
| 取數 0 筆就 `AddResultRow(false, 0, "")` | 多數 | 「查無資料」與「執行失敗」用同一個回傳值表達 |
| `catch` 之後 `AddResultRow(false, 0, "")` | **28 / 31** | **例外訊息被吞掉,使用者看到的跟「查無資料」一模一樣** |
| 參數一律走 `SQLEVAHelper.GetParamValue(model, "名稱")` | 多數 | 有參數化,沒有字串串接 |

**28 支報表把例外與查無資料混為一談**,這是本章最大的問題:報表印不出來時,從畫面上分不出是「今天真的沒資料」還是「SP 掛了 / 參數型別錯 / 連線斷」。要判斷只能翻框架 log。

### 7.2 39 個 `.rpt` 與程式引用:完全對得上

實測比對 `Dev/ATLAS.RSP.Report/Source/CrystalReports/Report.RSP/*.rpt` 與 31 支 UI 內非註解的 `"RSPRxxxRPSn"` 字串:

| 項目 | 數量 |
|---|---|
| repo 內的 `.rpt` 檔 | 39 |
| 程式實際引用的報表類別名 | 39 |
| 有檔沒引用 | **0** |
| 有引用沒檔 | **0** |

**這一點跟 `dsm.md §7.2`(40 個檔、13 個引用的不在)完全相反**——RSP 的報表資產是乾淨的,不需要另外清。

31 支畫面對 39 個 rpt 的落差來自「一支畫面多個版型」:

| 畫面 | rpt 數 | 怎麼選 | 錨點 |
|---|---|---|---|
| `RSPR013` | 2 | 依排序方式(`uoptOrderType.CheckedIndex == 0`)二選一 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:76-81` |
| `RSPR017` | 3 | 依排序方式 `0` / `1` / `2` 三選一 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:115-126` |
| `RSPR020` | 2 | 同一組判斷在 `:249` 與 `:301` 寫了兩次 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR020.cs:249-251`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR020.cs:301-303` |
| `RSPR021` | 2 | 預覽 / 列印各一組判斷 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR021.cs:80-84` |
| `RSPR024` | 2 | 同 `RSPR020`,判斷寫兩次 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR024.cs:78-82`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR024.cs:108-112` |
| `RSPR060` | 2 | 依條件二選一,另有一處把報表名包成 `KeyValuePair` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:122-126`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR060.cs:299` |
| `RSPR066` | 3 | 見 §7.4 |  |
| `RSPR049` | **0** | 不出 Crystal Report,直接吐 `.xlsx` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:84-97` |

31 − 1(`RSPR049` 無 rpt)= 30 支有 rpt,其中 7 支各有 2–3 個版型,合計 30 + 9 = 39。**帳是平的。**

### 7.3 權限:程式裡一條都沒有

逐支檢查 31 支報表 UI 與 PO,**沒有任何**:

- 員工代號白名單(對照 `dsm.md §7.3` 的員編 `101722`)

- 列印帳號白名單(對照 `dsm.md` 的 `ntaprt05`–`ntaprt11`)

- 部門 / 銷售機構的資料範圍過濾

- `CRM002A` 之類的權限對照表 join

唯一跟身分有關的是把登入者當**參數**傳給 SP(例:`RSPB024` 的 `striUpdateID` 傳 `PermissionInfo[0].UserID`,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB024_PO.cs:55`),而報表 PO 連這個都沒有。

**結論:RSP 報表的資料範圍完全由版控外的 SP 決定,repo 內看不到任何限制。** 能開報表畫面的人看得到什麼,只能問 DBA。

### 7.4 三支值得展開的

#### `RSPR066` — 一次印三份報表,而且用空 `catch` 包起來

168 投資契約轉帳明細表有「成功 / 失敗」兩種,成功那份又依 `orderRep` 分「一般版(`RSPR066RPS`)」與「子基金合計版(`RSPR066RPS2`)」。畫面提供三種操作(`orderTYPE`):

| `orderTYPE` | 行為 | 錨點 |
|---|---|---|
| `"1"` 成功 | 依 `orderRep` 印 `RSPR066RPS` 或 `RSPR066RPS2` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:223-237` |
| `"2"` 失敗 | 印 `RSPR066RPS1` | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:239-243` |
| 其他(全部) | **連續呼叫兩次自訂的 `doAct()`**:先印成功版,再印失敗版,最後 `e.Cancel = true` 取消框架原本的流程 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:183-218` |

「全部」那條路徑整段包在:

```
catch
{
    // pass
}
```

`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:205-208`。**空 catch,連註解都寫 `pass`。** 印到一半失敗(第二份報表取數炸掉、Crystal 載入失敗)使用者什麼都不會看到,只會覺得「怎麼只印出一份」。這是全模組唯一的空 catch,嚴重度高。

#### `RSPR034` — 「預覽」按鈕的分支被整段註解掉

`RSPR034_PO.GetData` 是一個 `switch ((BUTTON_TYPE)…)`,三個 case:

| case | 狀態 | SP | 錨點 |
|---|---|---|---|
| `PREVIEW` | **整段(約 55 行)被註解** | `s_RSPR034_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:137-192` |
| `MESSAGE` | 有效 | `s_RSPR034_1_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:194-200` |
| (第三個) | 有效 | `s_RSPR034_2_Get` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:245-246` |

被註解的那一段還是 T-SQL(`@striSEND` / `SqlDbType.NVarChar`,`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:153`),代表它是 Oracle 移轉前就停用的。**`switch` 沒有 `default`**,所以 `BUTTON_TYPE` 若真的傳 `PREVIEW` 進來,會直接跳過整個 `switch`,`j` 維持 0,回「查無資料」——使用者看到的是「沒資料」而不是「這個功能已停用」。

#### `RSPR049` — 唯一不出 Crystal Report 的一支

「定期定額扣款檢核表」直接由 `pxy.GetExcelData(view)` 拿回 `byte[]`,存成 `.xlsx` 再 `Process.Start` 開檔(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:58-105`)。兩個要注意的:

1. **輸出前會在 client 端過濾促銷活動**:`RSPR049_SH1` 沒資料就把 `RSPR049_SH3` 整個清空;有資料就逐列用 `DataTable.Select("CAMPAIGN_CODE = '" + dr.CAMPAIGN_CODE + "' OR L_CAMPAIGN_CODE = '" + …)` 比對,對不到就 `dr.Delete()`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:60-76`)。**這是字串串接進 DataTable 的過濾式**,促銷代碼含單引號就會炸語法。

2. **`catch` 把 `ex.ToString()` 整包丟給使用者看**(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:102`),含完整堆疊。跟其他 30 支「什麼都不說」剛好相反。

### 7.5 報表對維護資料的關係

| 報表 | 看的是哪條線的資料 | 什麼時候該印 |
|---|---|---|
| `RSPR020` 契約資料查核表 | `RSP005A` / `RSP006A` | `RSPM004` 建檔後對帳 |
| `RSPR029` 契約異動項目統計表 · `RSPR038` 契約異動資料查核表 · `RSPR008` 異動資料轉入主檔報表 | `RSP007A` / `RSP013A` | **`RSPB008` 跑完必印 `RSPR038`**,那是唯一能看到 `RSP_CHG_CD` 失敗明細的地方(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:104` 的訊息直接指路) |
| `RSPR011` 申購扣款明細表 · `RSPR024` 申購扣款總表 · `RSPR013` 扣款銀行查核表 · `RSPR023` 保管銀行傳真表 | `RSP008` / `RSP008A` | `RSPB009` 產完扣款資料後 |
| `RSPR012` 扣款行回覆資料查核表 · `RSPR021` 扣款失敗明細表 · `RSPR028` 扣款失敗項目統計表 · `RSPR051` 扣款失敗通知書 | `RSP008A` | `RSPB011` / `RSPB015` 回覆確認後 |
| `RSPR048` 連續扣款失敗明細表 · `RSPR046` / `RSPR047` 契約終止原因統計 / 明細表 | `RSP005A` / `RSP006A` | `RSPB052` 終止前後 |
| `RSPR031` 收件通知書 · `RSPR034` 首次扣款通知書 | `RSP005A` | 對客戶寄發 |
| `RSPR060`–`RSPR066` 七支 | 168 那條線(`RSP070A`–`RSP075A`) | `RSPB021` / `RSPB022` / `RSPB023` 前後 |
| `RSPR041` / `RSPR042` / `RSPR043` | 停利那條線(`RSP041A` / `RSP042A`) | `RSPB041` / `RSPB042` 前後 |
| `RSPR070` 業務受益人定額停扣明細 · `RSPR071` 申請暫停扣款查核表 | 跨線 | 業務單位查詢用 |
| `RSPR049` 扣款檢核表 | `RSP008` + 促銷活動 | 對帳用,只出 Excel |
| `RSPR017` 受益人申購明細表 · `RSPR064` 168 客戶查詢報表 | 跨線 | 客服查詢用 |

### 7.6 畫面端的檢核

報表畫面的 `DoValidate()` 普遍只做兩件事:`validatorManager1.DataValidate()` 加日期區間比大小。兩個共同的小行為:

- **日期自動補齊**:填了起日沒填迄日,離開欄位時自動把迄日設成起日(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR013.cs:87-93`、`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:108-113` 附近的 `_Leave` 事件)。

- **`Trim('0')` 處理選項值**:`RSPR017` 把 `RSP_TYPE` 的值做 `Convert.ToString(...).Trim('0')`(`Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:130`)。選項值本身是 `"0"` 時會被 trim 成空字串,SP 收到的就不是「型態 0」而是「不限」。**這是字串處理取代值域對照的典型寫法**,列入附錄 E。

## 8. 跨模組共用

```text
[圖] RSP 四組跨模組關係:COD009 只讀、RSP005A/RSP006A 被 BMS 直接 MERGE、OFD272A 分區共用、OFD374A 條件寫入
圖中文字:A：COD009 —— RSP 是第四個碰它的地方,但只讀 / CODM009 CODB009 / COD 的兩個維護入口 / COD009 / 員工主檔 56 欄 / RSPM037 / RSP 側 xsd 只認 6 欄 / 唯一寫入是 RSP006 費率 / COD009 零寫入 / B：RSP006A / RSP005A —— 不是只有 RSP 在寫 / RSPM004 RSPB020 / RSP 的正規入口 / RSP005A RSP006A / 契約主檔與明細 / BMSB901A〔BMS〕 / MERGE INTO 兩張表 / 寫死 039 到 810 與 2017 日期 / 繞過變更書 / OFDI011 OFDB70x / 唯讀查詢與扣款送件 / C：OFD272A —— 靠 TRN_CD 分區,三個模組各用各的 / OFDM221A OFDM231A / 主檔在 OFD / OFD272A / 缺件資料 / RSPM004 RSPM005 / 當第二明細 / BMSM004 只寫 TRN_CD=5 / 各認各的代碼 / D：OFD374A —— dsm.md 說 RSPM004 會寫,但有兩道閘門 / DSMM060〔DSM〕 / 唯一正規維護入口 / OFD374A / 受益人歸屬業務員 / 閘門1 簡易開戶 / BF_NO = -1 才會走 / 閘門2 AUTO_BELONG_EMP=Y / 兩者都成立才 INSERT / 值來自 BMS001 那一列 / 狀態掛 BMSM001 的四眼
```

*圖:圖 5 跨模組。橘框=RSP 這一側的入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險或寫死值。B 那一組最會咬人:BMS 的 BMSB901A 直接 MERGE 進 RSP005A / RSP006A,不產任何變更書,查「扣款行怎麼被改掉的」時 RSP 這邊完全查不到痕跡。*

RSP 自己的表 19 張(`RSP005A` `RSP006A` `RSP007A` `RSP008` `RSP008A` `RSP008AA` `RSP013A` `RSP041A` `RSP042A` `RSP061A` `RSP062A` `RSP063A` `RSP070A` `RSP071A` `RSP072A` `RSP073A` `RSP074A` `RSP075A`,加上 `CTL006A`),借別人的 2 張(`COD009` / `OFD272A`),另外在程式裡碰到但母體沒列的還有 `OFD374A` `BMS001` `OFD130A` `OFD131A` `OFD132A` `OFD220A` `OFD221A` `OFD306A` `OFD303A` `OFD681` `OFD701` `COD010` `CTL014` `CTL016` `LOG017A` `LOG094A` `LOG095A` `LOG109A` 等。

### 8.1 `COD009`:RSP 是第四個碰它的地方,但只讀

`cod.md §8.2` 列了三個維護入口(`CODM009` / `CODB009` / `RSPM037`)並註明 `RSPM037` 是「只查不寫」,**與本文從 RSP 這側查到的結果一致**。補三件 COD 那側看不到的:

| 事實 | 說明 | 錨點 |
|---|---|---|
| `MasterTable` 換三次 | `RSPM037_PO` 在 `Select()` / `Select_Detail()` / `Select_Detail_D()` 三個方法各設一次,所以 `COD009` 只在第一次查詢時是「主檔」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| RSP 側的 `COD009` 只認 6 欄 | `EMP_NO` / `EMP_ID_NO` / `EMP_NAME` / `EMP_NAME_ENG` / `ENTRY_DATE` / `LEAVE_DATE`,沒有四眼欄;COD 側是 56 欄 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd:18` |
| `RSPM004` / `RSPB020` 也 join `COD009` | 只為了取 `EMP_NAME`,`LEFT JOIN` 不影響筆數 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:222-223` |
| `EMP_CD = '1'` 的過濾只有 RSP 這側有 | `cod.md §8.2` 列的八處寫死清單裡沒有這一條,它是 `RSPM037` 自己加的 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111`〔客戶特定〕 |

**改 `COD009` 要一起看的 RSP 側檔案**:`RSPM037Model.xsd`(6 欄的迷你定義)、`RSPM037_PO.cs`(兩段 `UNION` 的 T-SQL)、`RSPM004_PO.cs` / `RSPB020_PO.cs`(取員工姓名的 `LEFT JOIN`)。

### 8.2 `RSP006A` / `RSP005A`:BMS 會直接 `MERGE` 進來

母體只寫「`RSP006A` 也服務 BMS OFD」。實際反查:

| 模組 | 畫面 / 程式 | 動作 | 錨點 |
|---|---|---|---|
| **BMS** | `BMSB901A` | **`MERGE INTO RSP006A` 改扣款行、核印方式、核印狀態、核印日期;`MERGE INTO RSP005A` 在 `MEMO` 前面串一段說明文字** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169-196` |
| BMS | `BMSB901` | 同族的另一支,讀 `RSP006A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs` |
| BMS | `BMSM001` | 讀 `RSP006A` / `RSP007A` / `RSP008A` 判斷受益人有沒有在途的定期定額 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs` |
| OFDI | `OFDI011` | 讀 `RSP005A` / `RSP007A` / `RSP008A` / `RSP070A` / `RSP072A` / `RSP041A` 做整戶查詢 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:378`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1027-1028`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1050-1071` |
| OFDB | `OFDB050` `OFDB223` `OFDB485` `OFDB501` `OFDB701`–`OFDB705` | 扣款送件 / 核印往返的一整排批次,讀寫 `RSP007A` / `RSP008A` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs` |
| OFD | `OFDM068` `OFDM231A` | 讀 `RSP005A` / `RSP070A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM068_PO.cs` |
| Common | `BasicRSP_PO.GetRspData` | **全庫共用的契約下拉 / 查詢資料源**,`RSP005A JOIN RSP006A` 一次取 40 幾欄 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicRSP_PO.cs:46-70` |
| Common | `RSP_PO` / `RSP_Ctl` / `RSP_Pxy` / `RSP_MomToSonDataSrc` | 168 母子基金的共用資料源 | `Dev/Common/Source/DataSource/PO.DataSource/RSP_PO.cs`、`Dev/Common/Source/DataSource/UI.DataSource/TableSrc/RSP_MomToSonDataSrc.cs` |
| Common | `ucRSP_TRNData` / `ucTX_RSP_TRN_NOData` | 停利書號的共用查詢控件 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucRSP_TRNData.cs` |

#### `BMSB901A` 這一支要單獨講

它是一支**一次性的資料搬遷批次,但程式還留在系統裡**(`bms.md` 從 BMS 側寫過)。從 RSP 這側看,它做的事是:

```
MERGE INTO RSP006A A
  USING (SELECT a.rsp_no, a.rsp_srno, SEAL_STATUS FROM BMSB901A_LOG A WHERE A.DATAID = :DATAID) B
  ON (A.rsp_no = B.rsp_no and A.rsp_srno = B.rsp_srno)
  WHEN MATCHED THEN UPDATE SET A.SUB_BANK_CODE = '810',
                               A.SEAL_TYPE     = '3',
                               A.SEAL_STATUS   = B.SEAL_STATUS,
                               A.SEAL_RTN_DATE = '20171219',
                               A.SEAL_DATE     = '20171207', …
```

`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169-180`。

| 問題 | 說明 |
|---|---|
| **兩個日期是寫死的字串** | `SEAL_RTN_DATE = '20171219'`、`SEAL_DATE = '20171207'`——2017 年那次搬遷的日期。今天再跑一次,會把契約的核印日期寫成 2017 年 |
| 銀行代碼寫死 | 來源 `'039'`(澳盛)、目的 `'810'`(星展)、`SEAL_TYPE = '3'`(財金)全部寫死〔客戶特定〕 |
| `MEMO` 用字串串接 | `A.MEMO = '澳盛(039)由ACH票交所平台已改為星展(810)財金扣款平台;' \|\| nvl(TRIM(MEMO),'')`,重跑會重複串 |
| **暫存表 `DELETE` 不帶批號** | `begin DELETE BMSB901A_T1; DELETE BMSB901A_T2; end;`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:200-203`)——兩個人同時跑會互刪對方的暫存資料,即使前面的 `INSERT` / `SELECT` 都帶了 `DATAID` |

**對 RSP 的意義:`RSP005A` / `RSP006A` 不是只有 RSP 在寫。** 調查「契約的扣款行怎麼變成 810 了、誰改的」時,`RSP005A.UPDATEID` 會指向跑 `BMSB901A` 的那個人,而 RSP 這邊查不到任何變更書(`BMSB901A` 不產 `RSP007A`)。這是 RSP 側唯一一條**繞過變更書直接改主檔**的外部路徑。

### 8.3 `OFD272A`:RSP 是第三種用法

`bms.md §8.2` 已寫:主檔在 `OFDM221A` / `OFDM231A`,BMS 只寫 `SHORE_ID = '2'` 且 `TRN_CD = '5'` 那一批,**這張表靠 `TRN_CD` 分區使用**。

RSP 這側把它當 `RSPM004` / `RSPM005` 的第二明細(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149`),取數 SQL 在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:583-620`,存 / 刪在 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1171-1186`。畫面上是「缺件」頁籤,由 `DoExp2` 開 `RSPM004p2` 維護(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:767-782`)。

RSP 側的 xsd 定義 24 欄(比 BMS 側多 `IsCheck` 與 `ACCOUNT_MEMO` 兩個畫面用欄位,`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1343`),主鍵宣告是 `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID`。**加欄位要同時改 OFD / BMS / RSP 三邊的 xsd**。

### 8.4 `OFD374A`:從 RSP 側驗證 `dsm.md §8.2`

`dsm.md §8.2` 寫「`RSPM004`(RSP)直接 `INSERT OFD374A`」,錨點 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700`。`bms.md §8.2` 也引了同一條。

**從 RSP 這側驗證:這件事成立,但有兩道閘門,`dsm.md` / `bms.md` 都沒寫。**

| 閘門 | 條件 | 錨點 |
|---|---|---|
| 1 | **必須走「簡易開戶」路徑**,也就是 `RSPM004_Master.BF_NO == -1` 或空字串(使用者輸入了一個系統查不到的統編) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:633` |
| 2 | **系統參數 `AUTO_BELONG_EMP` 必須等於 `'Y'`** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-698` |

也就是說:**幫既有受益人建定期定額契約,RSP 不會碰 `OFD374A`;只有「連受益人一起新開」而且開關打開時才會寫一筆。**

再補三件事:

1. **寫入的值從哪來。** `INSERT OFD374A` 的 `BF_NO` / `EMP_NO` / `BELONG_DATE` / 四眼 13 欄全部由 `SetBasicTableColumnAndData` 從 **`BMS001` 那一列** 的同名欄位綁過去(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:798`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2655-2694`),只有 `SAL_DEPT_NO` 被另外指定成 `RSPM004_Detail[0].EMP_DEPT_NO`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:800`)。**歸屬日期 `BELONG_DATE` 用的是 `BMS001.BELONG_DATE`,不是「今天」** ——這跟 `dsm.md §4.6` 記的 `DSMM060`「歸屬日期永遠是今天」不同。

2. **狀態跟著 `BMSM001` 的四眼走。** `Status` 來自 `UseCaseSecurity.SetFunctionSecurityDataInfo(BfRow, model, EVAType.Add, "BMSM001", …)`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:688`),用的是 **`BMSM001` 的功能代號**,不是 `DSMM060` 也不是 `RSPM004`。所以這筆 `OFD374A` 的待辦會掛在 `BMSM001` 的流程底下。

3. **`dsm.md §8.2` 的第 1 點(`DSMM060` 三個 INNER JOIN 查不到不合規的資料)對這批資料成立。** RSP 寫進去的 `SAL_DEPT_NO` 來自 `RSP006A.EMP_DEPT_NO`,只要這個部門不在 `OFD002`,`DSMM060` 就看不到、也改不掉。

**與 `dsm.md` 的結論比對:一致,本文只是把條件補完整。** 要改的話兩篇都要更新——`dsm.md §8.2` 與 `bms.md §8.2` 目前寫的是無條件 `INSERT`。

### 8.5 RSP 用到的共用 PO 與控件

| 共用元件 | 位置 | RSP 怎麼用 |
|---|---|---|
| `BasicRSP_PO` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicRSP_PO.cs:37` | 全庫要查「某受益人的定期定額契約」都走這支,`RSP005A JOIN RSP006A` |
| `RSP_PO` / `RSP_Ctl` / `RSP_Pxy` | `Dev/Common/Source/DataSource/PO.DataSource/RSP_PO.cs` | 168 母子基金與停利書號的共用資料源 |
| `RSP_MomToSonDataSrc` | `Dev/Common/Source/DataSource/UI.DataSource/TableSrc/RSP_MomToSonDataSrc.cs` | 母基金→子基金的下拉連動,吃 `RSP070A` |
| `ucRSP_TRNData` / `ucTX_RSP_TRN_NOData` | `Dev/Common/Source/CustomControl/UI.CustomControl/ucRSP_TRNData.cs` | 停利書號 / 停利異動書號的 searcher 控件,吃 `RSP041A` / `RSP042A` |
| `ClientBizUtility` / `ServerBizUtility` | `Dev/Common/Source/Utility/…` | `GetBusinessDay` / `GetFundBusinessDay` / `GetEMP_AGENT` / `GetSysParam` / `IsAgentFund` / `GetBF_FUND_RISK_ATTR` / `GetIS_PROINVEST`,RSP 幾乎每支畫面都在用 |
| `SerialNo` | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs` | `GetRspNoForNfd` / `GetRspChgNoForNfd` / `GetBFNo` / `GetRDRemitConfirmNo`,一律配 do-while 防撞號 |
| `SrNoCommentProcessor` | 框架 | 跳號一覽表;RSP 有四支畫面(`RSPM004` / `RSPM005` / `RSPM021` / `RSPB052` 間接)掛滿六個四眼後置事件 |
| `GenXMLHelper.Gen49` | `Dev/Common/Source/Utility/…` | `RSPB008_Service` 寄通知信 |
| `xTableHelper` / `xEVAStringHelper` | 框架 DLL,**無原始碼,從呼叫端反推** | `GetInsertString` / `SetEVAParameters` / `AllEVAColumnsForSelect` / `AppendToDoString` |
| `BaseEVADaoPO` / `BasicEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/` | 23 支 PO 走前者(新世代),`RSPB010_PO` / `RSPM037_PO` 走後者(舊世代) |

### 8.6 改動影響面速查

| 要改什麼 | 一定要一起看的 |
|---|---|
| `RSP005A` / `RSP006A` 加欄位 | `RSPM004Model.xsd` + `RSPB020Model.xsd` + `RSPB009Model.xsd` + `RSPB052Model.xsd` + `RSPM037Model.xsd`(五份 xsd,欄位集合都不一樣)、`BasicRSP_PO.GetRspData`、BMS 的 `BMSB901A` / `BMSB901` / `BMSM001`、OFDI 的 `OFDI011` |
| `RSP007A` / `RSP013A` 加欄位 | `RSPM005Model.xsd` + `RSPB008Model.xsd`、`RSPB052_PO`(它自己組 `INSERT`)、OFDB 的 `OFDB050` / `OFDB485` / `OFDB701`–`OFDB705`、`s_TA_RSPB008_Excute_M`(版控外) |
| `RSP008` / `RSP008A` 加欄位 | `RSPB009`–`RSPB019` 六份 xsd、OFDB 的 `OFDB485` / `OFDB501` / `OFDB703`、`OFDI011` |
| `RSP070A`–`RSP075A` 加欄位 | `RSPM021Model.xsd` + `RSPB025Model.xsd` + `RSPM022Model.xsd`、`RSP_MomToSonDataSrc`、`OFDM231A` / `OFDB223` / `OFDI011` |
| `RSP041A` / `RSP042A` 加欄位 | `RSPM041Model.xsd` + `RSPM042Model.xsd`、`ucRSP_TRNData` / `ucTX_RSP_TRN_NOData`、`OFDI011` |
| `COD009` 加欄位 | `cod.md §8.6` 為準;RSP 這側只要確認 `RSPM037Model.xsd` 那 6 欄還在 |
| `OFD272A` 加欄位 | OFD / BMS / RSP 三邊 xsd |
| `OFD374A` 加欄位 | `dsm.md §8.2`(`DSMM060` 的 xsd)+ `BMSM001Model.xsd` + `RSPM004Model.xsd` 的 `OFD374` DataTable |
| 改四眼狀態值域 | RSP 內有三處寫死 `'301'`:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |
| 改 `AUTO_BELONG_EMP` 的語意 | `bms.md §8.3`(BMS 兩支畫面把它寫成兩個相反常數)+ `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:698` |

## 附錄 A. 資料表總表

### A.1 母體的 21 張表

| 表 | 中文名(推測) | 主檔於 | 明細於 | 跨模組 | 四眼 |
|---|---|---|---|---|---|
| `RSP005A` | 定期定額契約主檔 | `RSPM004` `RSPB020`(`RSPB009` 讀) | — | BMS OFD OFDB OFDI Common(§8.2) | 有 |
| `RSP006A` | 定期定額契約基金明細 | — | `RSPM004` `RSPB020` `RSPB009` | BMS OFD Common | 有 |
| `RSP007A` | 契約變更主檔 | `RSPM005` `RSPB008` | — | BMS OFDB OFDI | 有 |
| `RSP013A` | 契約變更明細 | — | `RSPM005` | — | 有 |
| `RSP008` | 扣款檔 | `RSPB010`(`RSPB009` 寫) | — | — | 有 |
| `RSP008A` | 扣款回覆 / 計算 / 結轉檔 | `RSPB011` `RSPB015` `RSPB016` `RSPB018` | — | BMS OFDB OFDI | 部分 |
| `RSP008AA` | 淨值回復檔 | `RSPB019` | — | — | 無 |
| `RSP061A` | 母子基金設定主檔 | `RSPM020` | — | — | 有 |
| `RSP062A` | 母基金清單 | — | `RSPM020` | — | 有 |
| `RSP063A` | 子基金清單 | — | `RSPM020` | — | 有 |
| `RSP070A` | 168 契約主檔 | `RSPM021` `RSPB025` | — | OFD OFDB OFDI Common | 有 |
| `RSP071A` | 168 契約子基金明細 | — | `RSPM021` `RSPB025` | — | 有 |
| `RSP072A` | 168 契約綁定申購書 | — | `RSPM021` `RSPB025` | OFDI | 有 |
| `RSP073A` | 168 契約變更主檔 | `RSPM022` `RSPB023` | — | — | 有 |
| `RSP074A` | 168 契約變更明細 | — | `RSPM022` | — | 有 |
| `RSP075A` | 168 契約變更申購書 | — | `RSPM022` | — | 有 |
| `RSP041A` | 停利轉申購契約 | `RSPM041` | — | OFDI Common | 有 |
| `RSP042A` | 停利轉申購異動 | `RSPM042` `RSPB041` | — | Common | 有 |
| `CTL006A` | 扣款日媒體產生控制 | — | `RSPB009` | 共用控制檔 | 無 |
| `COD009`〔共用〕 | 員工主檔 | COD 的 `CODM009` / `CODB009` | `RSPM037` 只讀 | COD | COD 側有,RSP 側 xsd 無 |
| `OFD272A`〔共用〕 | 缺件資料 | OFD 的 `OFDM221A` / `OFDM231A` | `RSPM004` `RSPM005` | OFD BMS OFDB OFDI NFD | 有 |

### A.2 母體沒列、但本文有提到的表

| 表 | RSP 怎麼碰 | 錨點 |
|---|---|---|
| `RSP005` / `RSP006`(無 A 尾碼) | `RSPM037` 專用的舊表名,只有這一支在用 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |
| `COD010` | 員眷,`RSPM037` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:106` |
| `BMS001` / `BMS001A` | 受益人;簡易開戶時寫,其餘只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:795`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:219` |
| `BMS005A` | 收益分配帳號,`AddOFD130A` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1239` |
| `OFD374A`〔共用〕 | 簡易開戶 + 開關打開時寫一筆 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700` |
| `OFD132A` | 簡易開戶時依 `OFD040A` 範本產 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:741` |
| `OFD040A` | 對帳單寄送範本,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:788` |
| `OFD130A` / `OFD131A` | 匯款授權書與帳號,存檔後補建 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1212`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1228` |
| `OFD701` | 核印檔,讀 / 寫 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:951` |
| `OFD220A` / `OFD221A` / `OFD306A` | `RSPB020` / `RSPB025` 連動更新業務欄位 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:561`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:574`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:588` |
| `OFD303A` | 關帳 / 結轉控制碼,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:119` |
| `OFD315` | 受益人各契約各基金扣款次數(`DoExp3` 用) | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM004Model.xsd:1464` |
| `OFD681` | 通知信收件人,`SEND_TYPE = '6'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `OFD081` / `OFD081A` / `OFD081V` | 基金主檔與 view,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:100` |
| `OFD302` / `OFD302A` | 淨值,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:60` |
| `OFD019` / `OFD019A` | 銀行總行,只讀(限額檢核已註解) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:242` |
| `OFD087` | 暫停扣款的基金 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:349` |
| `OFD041` | 說明範本(`GetPhraseItems`) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:610` |
| `OFD071A` / `OFD072A` / `OFD002` / `COD006A` | 通路 / 推薦人 / 部門 / 代碼說明,`LEFT JOIN` 唯讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:225-248` |
| `OFD138A` | 收益分配行 / 帳號,`RSPM041` / `RSPM042` 唯讀 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM041Model.xsd:169` |
| `OFD190` / `OFD199` | 促銷活動,唯讀 | `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM005Model.xsd:1289` |
| `OFD661A` | EC 契約異動,`CheckRspNO` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2538` |
| `CTL014` / `CTL015` / `CTL016` | 預設值 / 扣款帳號依據 / 排程時刻 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:302` |
| `LOG017A` | 法人公告,`RSPB018` 讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:245` |
| `LOG094A` / `LOG095A` / `LOG109A` | 三支停利 / 轉申購批次的執行紀錄,只讀 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:230`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:190` |
| `SrNoComment` | 跳號一覽表(PTPF 庫) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2360` |
| `LOG_RSP070A` | 168 契約異動 log,**repo 內唯一有 DDL 的 RSP 相關表** | `DB/Table/create_LOG_RSP070A.sql:2` |

`DB/Table/` 內與 RSP 有關的檔只有三個:`create_LOG_RSP070A.sql`(建表)、`update_rsp006a.sql`(一次性資料更新,把 `SUB_BANK_CODE` 從 `815` 改成 `012`)、以及兩支報表暫存表 `TA_RSPR011_BONUS_LIST.sql` / `TA_RSPR011_THREE_TEMP.sql`。**21 張核心表沒有任何一張的 DDL 在版控內。**

## 附錄 B. SP / Function / Trigger / View

掃描母體的 SP / Fn / Trigger / View 全部是 **0 筆**——不是沒有,是**全部不在版控內**。`DB/SP/` 底下唯一跟 RSP 沾邊的是 `S_OTA_OFDI011_GetRSPCHG.SQL`,而且屬於 OTA。

### B.1 Stored Procedure(從呼叫端反推,共 30 支)

| SP | 被誰呼叫 | 錨點 |
|---|---|---|
| `s_TA_RSPB008_Excute_M` | `RSPB008` + `RSPB008_Service` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:65` |
| `S_TA_RSPB009_Excute` | `RSPB009`(逐檔基金呼叫) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:57` |
| `s_RSPB010_Excute` | `RSPB010`(**T-SQL `EXEC` 字串**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:155` |
| `S_TA_RSPB015_Excute` | `RSPB015` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:318` |
| `S_TA_RSPB016_Excute` | `RSPB016` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:199` |
| `S_TA_RSPB018_Excute` | `RSPB018` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:203` |
| `S_TA_RSPB019_Excute` | `RSPB019` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:50` |
| `S_TA_RSPB021_EXCUTE` | `RSPB021` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:54` |
| `S_TA_RSPB022_EXCUTE` | `RSPB022` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB022_PO.cs:62` |
| `S_TA_RSPB023_EXCUTE` | `RSPB023` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:55` |
| `S_TA_RSPB024_EXCUTE` | `RSPB024` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB024_PO.cs:50` |
| `S_TA_RSPB041_EXCUTE` | `RSPB041` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:55` |
| `S_TA_RSPB042_EXCUTE` | `RSPB042` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:57` |
| `s_RSPR008_Get` | `RSPR008` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR008_PO.cs:52` |
| `S_TA_RSPR011_GET` | `RSPR011` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR011_PO.cs:60` |
| `S_TA_RSPR012_GET` | `RSPR012` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR012_PO.cs:48` |
| `S_TA_RSPR013_GET` | `RSPR013` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR013_PO.cs:62` |
| `s_TA_RSPR017_Get` | `RSPR017` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR017_PO.cs:69` |
| `S_TA_RSPR020_GET` | `RSPR020` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR020_PO.cs:60` |
| `S_TA_RSPR021_GET` | `RSPR021` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR021_PO.cs:60` |
| `s_RSPR023_Get` · `s_RSPR023_Count` · `s_RSPR023_Total` | `RSPR023`(**一支報表三支 SP**) | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:54`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:71`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR023_PO.cs:88` |
| `S_TA_RSPR024_GET` | `RSPR024` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR024_PO.cs:61` |
| `S_TA_RSPR028_GET` | `RSPR028` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR028_PO.cs:60` |
| `S_TA_RSPR029_GET` | `RSPR029` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR029_PO.cs:60` |
| `s_TA_RSPR031_Get` | `RSPR031` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR031_PO.cs:57` |
| `s_RSPR034_1_Get` · `s_RSPR034_2_Get` | `RSPR034`(`s_RSPR034_Get` 的分支被註解) | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:199`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:245` |
| `S_TA_RSPR038_GET` | `RSPR038` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR038_PO.cs:55` |
| `S_TA_RSPR041_GET` · `S_TA_RSPR042_GET` · `S_TA_RSPR043_GET` | `RSPR041` / `RSPR042` / `RSPR043` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR041_PO.cs:55`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR042_PO.cs:55`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR043_PO.cs:60` |
| `s_RSPR046_Get` · `s_RSPR047_Get` · `s_TA_RSPR048_Get` · `s_RSPR049_Get` · `s_TA_RSPR051_Get` | `RSPR046`–`RSPR051` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR046_PO.cs:43`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR047_PO.cs:46`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR048_PO.cs:65`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR049_PO.cs:47`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR051_PO.cs:51` |
| `S_TA_RSPR060_GET` – `S_TA_RSPR066_GET` | `RSPR060`–`RSPR066` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:60` 等 |
| `S_TA_RSPR070_GET` · `S_TA_RSPR071_GET` | `RSPR070` / `RSPR071` | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR070_PO.cs:60`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR071_PO.cs:60` |

命名有三種風格:`S_TA_RSPxxx_GET`(大寫)、`s_TA_RSPxxx_Get`(混合)、`s_RSPxxx_Get`(無 `TA_`)。前者是新世代,後兩者是舊的。grep 時三種都要試。

### B.2 Function / View

| 類 | 名稱 | 用途 | 錨點 |
|---|---|---|---|
| TVF | `f_TA_GetEVAStatus('A')` | 取「已生效」的四眼狀態集合 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:154` |
| TVF | `F_FormatStringToTable(:DAY)` | 把逗號字串切成表,`CheckSameData` 用 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2396` |
| TVF | `F_TA_GetAgent()` | 銷售機構(Oracle 版) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:230` |
| TVF | `f_GetAgent()` | 銷售機構(**T-SQL 版,只有 `RSPM037` 用**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:184` |
| Fn | `f_TA_GetBusinessDay(日期,'1',0)` | 營業日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:121` |
| Fn | `f_TA_GetFNBusinessDay(基金,'2'/'3',日期,0)` | 基金營業日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:122` |
| Fn | `f_TA_GetNavDate(基金,日期,'2')` | 淨值日 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:123` |
| Fn | `dbo.f_GetBankHQ(SUB_BANK_CODE)` | 總行代碼(**T-SQL,`dbo.` schema**) | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:425` |
| View | `OFD081V` | 基金主檔 view,取 `FUND_FACE_AMT` / `DEC_LEN` / `FUND_STATUS` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:100` |

**Trigger:repo 內找不到任何 RSP 相關 trigger 的引用。**

## 附錄 C. 代碼對照

| 代碼欄 | 值 | 意義 | 來源 |
|---|---|---|---|
| `Status`(四眼) | 見 `architecture.md §3.10` | — | 框架 |
| `Status` 寫死值 | `'301'` | 已覆核 / 生效 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135` |
| `REDEM_DATE`(168 約定轉申購日) | `1`–`7` | 6 / 16 / 26 日的七種組合,見 §2.5 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128` |
| `RSP_ACCT_BY` | `'1'` 依主檔 / `'2'` 依明細 | **永遠是 `'2'`**,`'1'` 的功能未完成 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:35`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212` |
| `SEAL_TYPE` | 一般 / ACH / 財金 | 三種扣款媒體,`RSPB052` 寫死 `'3'`=財金 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:175` |
| `SUB_STATUS`(扣款進度) | `'0'` / `'1'` 尚未回報 · `'2'` / `'3'` 已回報 | 由 `RSPB015` 的檢核訊息反推 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:69-70` |
| `SUB_STATUS`(OFDI 側) | `'0'` `'1'` `'2'` 走 `CTL014` 對照;`'3'` 走 `COD006A` | 失敗才有原因碼 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1070-1071` |
| `CTL006.RSP_CTL_CODE` | `0` 未處理 · `1` 扣款行皆已回覆 · `2` 已執行單位數計算 · `3` 已結轉 | 由 `RSPB009` 的檢核訊息反推 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:360-362` |
| `OFD303A.RSP_CTL_CODE` | `'1'` 請先執行單位數計算 · `'3'` 本日已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:80-81` |
| `OFD303A.REDEM_CTL_CODE` | `'4'` 買回關帳已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148` |
| `OFD303A.ALLOT_CTL_CODE` | `'3'` 申購關帳已結轉 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:150` |
| `OFD081.FUND_STATUS` | `'0'` 正常,其餘代表已清算或合併 |  | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:65` |
| `STOP_ID` / `STOP_CD` | `'N'` 或空 = 未終止;`'Y'` = 終止 | `RSPB052` 終止時寫 `STOP_CD = '01'` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:412-413` |
| `RSP_CHG_CODE` | `'A'` 新增 · `'M'` 修改 | `RSPB052` 產出的變更明細固定 `'M'` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:945`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:188` |
| `ISCHG_STOP_ID` | `'Y'` / `'N'` | 這列有沒有改終止設定 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022p0.cs:554` |
| `TRAN_TERM` | `BMS001A.TRAN_FAX_CD = 'Y'` → `'2'`,否則 `'1'` | 交易方式 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:127` |
| `SOURCE_CD` / `SYSTEM_ID` | `RSPB052` 寫死 `'1'` / `'0'` | 資料來源碼 / 交易途徑 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:158-159` |
| `OFD681.SEND_TYPE` | `'6'` = RSPB008 通知信群組 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `COD009.EMP_CD` | `'1'` = 算員工 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96` |
| `COD006A.CODE_SORT` | `'42'` = 定期定額終止原因 | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:247` |
| `CTL014` 序號 | `065` `066` `069` `070` `078` `079` `081` `083` | 簡易開戶八個預設值 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:677-684` |
| 銀行代碼 | `'700'` 郵局 · `'039'` 澳盛 · `'810'` 星展 · `'815'` / `'012'` | 〔客戶特定〕 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:174`、`DB/Table/update_rsp006a.sql:1` |
| 促銷活動 | `'86A03'` | `RSPM004` 有專屬檢核 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785`〔客戶特定〕 |
| 門檻金額 | `10000` | `RSPM041` / `RSPM042` 的停利門檻下限 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`〔客戶特定〕 |
| 轉申購日 | `6` / `16` / `26` | 168 的固定三天 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:61`〔客戶特定〕 |

## 附錄 D. 掃描母體與覆蓋率

### D.1 母體

`docs/_candidates/rsp.md`:畫面 56(B 17 / I 0 / M 8 / R 31)· 表 21 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 39 · Service 1。

重跑:

```
py -V:3.12 /docs/tools/atlas_scan.py --module RSP --doc /docs/modules/rsp.md
```

### D.2 母體有五處與程式不符,以程式為準

| 母體說 | 程式實際 | 依據 |
|---|---|---|
| `COD009` 主檔於 `CODB009` `CODM009` **`RSPM037`** | `RSPM037` **只讀不寫**,`MasterTable` 是在 `Select()` 方法內指定的,而且後面還被換成 `RSP005` / `RSP006` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:77`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:197`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:250` |
| `RSPB020` / `RSPB025` 是 B(批次) | 兩支都是 `xMaintainForm`,走完整四眼,是維護畫面 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB020.cs:23`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB025.cs:24` |
| `RSPB008` 主檔 `RSP007A`、無明細 | `RSP013A` 的明細宣告存在但被註解;實際的 `RSP013A` 處理在 SP 內 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:44` |
| `RSP006A` 只服務 BMS / OFD | BMS 的 `BMSB901A` 會 **`MERGE INTO`** 它與 `RSP005A`,不是唯讀 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:169`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:189` |
| `RSPM037` 主檔 `COD009`,沒有提到 `RSP005` / `RSP006` | 這兩張**無 A 尾碼**的表只有 `RSPM037` 在用,掃描器沒把它們算進 21 張 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:163`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:225` |

### D.3 「六層齊」的兩個補充

母體說 56 支全部六層齊。實測補兩件事:

1. **`RSPB010` 與 `RSPM037` 的 PO 層是舊世代基底**(`BasicEVAPO`)而不是新世代的 `BaseEVADaoPO`,而且兩支都沒有 `[PODbType(DbServerType.Oracle)]` 屬性。25 支 PO 裡只有這兩支是這樣。六層數量齊,**世代不齊**。

2. **`RSPM037` 的 UI 層是 `xOneStepProcessForm`**(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:21`),其餘七支 M 都是 `xMaintainForm`。六層齊,**型別不齊**。

### D.4 39 個 rpt 對得上程式

見 §7.2 的實測:有檔沒引用 0、有引用沒檔 0。**這一點跟 DSM 相反**(`dsm.md §7.2` 記 40 個檔有 13 個引用不在)。

### D.5 本篇引用的覆蓋率

`atlas_scan.py --module RSP --doc docs/modules/rsp.md` 的結果貼在下方(重跑時請一併更新):

- 表:母體 21 張,本文全數提及(含 `RSP008AA` 與 `CTL006A`)。

- 畫面:母體 56 支,本文全數提及。8 支 M 一支一節(§4),17 支 B 全列在 §3.3 與 §6.1 的表內並展開 6 支,31 支 R 全列在 §3.4 與 §7 的表內並展開 3 支。

- rpt:39 個全數對應到畫面(§3.4 / §7.2)。

- Service:1 支,§6.3 專節。

### D.6 未被本文展開、但已在清冊裡處置的項目

| 項目 | 處置 |
|---|---|
| `RSPB016` / `RSPB019` | 只在 §6.1 的共同模式表出現;兩支都是單純的 SP 外殼,沒有畫面端業務邏輯 |
| `RSPR008`–`RSPR071` 的 28 支 | 只在 §3.4 與 §7.5 出現;結構與 §7.1 的骨架一致,差別僅在 SP 名與參數 |
| `RSPM004p1`(25 行) | 幾乎是空殼,只有建構子與一個事件 |
| `RSPM005p2` / `RSPM005p3`(84 / 33 行) | 小型彈窗,無業務卡控 |
| `RSPB019p0`(74 行) | 回復說明範本挑選,無業務卡控 |

### D.7 怎麼自己重跑

```
py -V:3.12 /docs/tools/atlas_scan.py --module RSP
py -V:3.12 /docs/tools/atlas_scan.py --module RSP --doc /docs/modules/rsp.md
py -V:3.12 /docs/tools/atlas_build_doc.py /docs/modules/rsp.md --repo-root  --report /docs/modules/rsp.refcheck.md
```

## 附錄 E. 讀本文時要注意的地方

### E1 會直接產生錯誤資料的五條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `RSPB052` 把 `UPDATE RSP005A` 的影響列數硬寫成 `1`(`RSP005 = 1;`) | 契約主檔沒被終止(已被別人終止 / `RSP_NO` 不存在)照樣回成功,而 `RSP007A` / `RSP013A` 的終止變更書已經寫進去。**資料庫出現「有終止變更書、主檔沒終止」的不一致,而且沒有人會知道** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:417-418` | **高** |
| 2 | `RSPM037.Execute` 同樣把 `ExecuteNonQuery` 回傳值蓋成 `1`(`o = 1;`) | 手續費率更新 0 列照樣回成功。離職員工的優惠費率沒被調回,作業人員以為改好了 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:283-284` | **高** |
| 3 | 五支 SP 外殼在 `catch` 裡把錯誤寫進 `model`,卻回傳 `resultVdb` | 例外發生時回傳的 VDB 沒有任何 `Result` 列,畫面讀 `Result[0]` 會 `IndexOutOfRangeException`。**批次失敗時使用者看到的是框架的通用錯誤,不是「執行失敗,請檢查」** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:85-98`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB022_PO.cs:92-103`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:81-95`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB041_PO.cs:80-94`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:87-101` | **高** |
| 4 | `RSPB009` 的 `catch (SqlException)` 在 Oracle 環境永遠不會被觸發 | 主鍵重複(ORA-00001)掉進通用 catch,使用者看到「無符合查詢條件資料可執行。」——與真因完全無關。寫好的指引訊息「請先執行[刪除扣款資料]功能」永遠不會出現 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109-131` | **高** |
| 5 | `RSPB008` 在 `CORRECT = 'Y'`(有更新失敗資料)時回 `ReturnCode = false` **但仍然 `tran.Commit()`** | 「失敗」與「已寫入」同時成立。作業人員看到錯誤訊息可能會重跑一次,造成重複處理 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:102-108` | **高** |

### E2 Oracle 三值邏輯:`<> '值'` 抓不到 NULL

跟 CAS / CLS / DSM / BBS 四個模組一樣的型。RSP 有 **4 處沒有包 `NVL`**:

| 位置 | 判斷式 | 後果 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:338` | `TABLE_NavDate.FUND_STATUS <> '0' THEN '該基金已清算或合併,不可執行'` | `FUND_STATUS` 為 NULL 時整條 `CASE WHEN` 是 UNKNOWN,**已清算的基金會被放行產生扣款資料** | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:65` | 同上,訊息「不可執行單位數計算」 | 同上 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:53` | 同上,訊息「不可執行定期定額申購結轉」 | 同上 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:489` | `WHERE SUB_STATUS <>'0'` | `SUB_STATUS` 為 NULL 的列被靜默濾掉 | 中 |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:531` | `AND RSP013A.RSP_CHG_CODE <>' '` | 同上 | 中 |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:82` | `AND CTL006.RSP_CTL_CODE <> '0'` | 同上 | 中 |

**同一支 `RSPB009` 的其他十幾條判斷都有好好寫 `NVL(x,' ') <> ' '`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:342`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:360-371`),所以上面那三條「基金已清算」是漏網的,不是全域慣例。

### E3 `NVL(x, '') = ''`:在 Oracle 永遠是 UNKNOWN

```
WHEN ((NVL(CTL006.FUND_ID,'')='') AND OFD303A.RSP_CTL_CODE <> '0')
     THEN '本基金於CTL006中，無此實際扣款日期的資料，請洽MIS人員'
```

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:64`。Oracle 把空字串當 NULL,所以 `NVL(x,'')` 等於 `NVL(x, NULL)` 等於 `x`,再跟 `''`(= NULL)比較永遠是 UNKNOWN。**這條訊息永遠不會出現**;同一支 SQL 的其他地方用的是正確的 `NVL(x,' ') <> ' '`(空格不是空字串)。嚴重度中——遺漏的是一個提示訊息,不是卡控。

### E4 被註解掉但外殼還在的檢核(11 處)

| # | 什麼 | 現況 | 錨點 |
|---|---|---|---|
| 1 | `RSPB021` 的「是否已執行過 168 扣款轉申購」 | UI 呼叫整段註解,理由「SP已有檢核,故取消」;PO 的 `ValidateLOG095A` 與 Proxy 方法都還在 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:67-91` |
| 2 | `RSPB008` 的郵局每日交易限額 | UI + PO 兩側各註解一整段,理由「改寫在 StoredProcedure 裡檢核」 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:54-66`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:183-286` |
| 3 | `RSPM004` 的「推薦人必須屬於該銷售機構」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004p0.cs:2367-2372` |
| 4 | `RSPM005` 的「不可異動『鎖利定額』契約」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM005.cs:248` |
| 5 | `RSPM020` 的「執行類別 為必填欄位」+ 對應下拉設定 | 兩處都註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:82`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM020.cs:295` |
| 6 | `RSPM021` 的「子基金與受益人風險等級不符」 | 註解,**而 `RSPM022` 的同一條是有效的** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:1818` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:310` |
| 7 | `RSPM021` 的「契約申購明細資料已結轉,契約不可刪除」 | 註解 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:660-679` |
| 8 | `RSPM042` 的「已有相同交易資料,不可新增」 | 註解,**而 `RSPM041` 的同一條是有效的** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:836-854` 對 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` |
| 9 | `RSPM037` 的「契約收件日須在在職期間」 | 註解,理由「user不想要此功能 20090716」,兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:177`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:244` |
| 10 | `RSPR034` 的「預覽」分支(約 55 行) | 註解,`switch` 沒有 `default`,傳 `PREVIEW` 進來會靜默回「查無資料」 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:137-192` |
| 11 | `RSPM004` / `RSPM005` 的「郵局(700)自動配核印用戶號碼」 | 四段(各兩處 `BeforeAdd` / `BeforeUpdate`)全註解,日期標 `20181119` / `20181120` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:819-856`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:448-486` |

**第 6 與第 8 是同一支業務線上「新增擋、修改不擋」或「新增不擋、修改擋」的落差**,最容易在實務上出事。

### E5 有訊息但沒有 `return` / 訊息與控制項對不上 / 訊息是空的

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPB022` / `RSPB042` / `RSPB021` 的「刪除重作」分支,`AddError` 帶的是 PO 回傳的**空字串** | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB022.cs:90-91`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB042.cs:83-84` | 中 |
| 2 | `RSPM042` 的「門檻金額(變更後)必須大於等於10000」掛在 `unumMIN_AMT_BEF`(變更前、唯讀欄) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:828` | 中 |
| 3 | `RSPM042` 的「沒有變更任何欄位」之後 `ValidateErrList.Show()` 但**沒有 `return`**,後面的 `Compare()` 照跑 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:875-877` | 低 |
| 4 | `RSPM022` 三處 `string.Format("未填附自主申購聲明書，無法申購!", d_Row.AFT_SON_FUND_ID)` —— 格式字串沒有 `{0}`,基金代碼被丟掉 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:323`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:350`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:569` | 低 |
| 5 | `RSPM004` / `RSPM005` / `RSPM021` 的四眼後置事件失敗時 `throw new ApplicationException("")` —— **訊息是空字串** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2588`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:559`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM021_PO.cs:643` | 中 |
| 6 | `RSPM005` 的「鎖定契約書失敗,請檢查」在契約書號不存在時也會跳,訊息誤導 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:419-420` | 低 |
| 7 | `RSPB041` 的區塊註解寫「(RSP073A)」,實際查的是 `RSP042A` —— 從 `RSPB023` 複製沒改 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB041.cs:91` | 低 |
| 8 | `RSPM041` 的「已有**有**相同交易資料,不可新增」—— 多一個字 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:802` | 低 |
| 9 | 28 支報表 PO 的 `catch` 回 `AddResultRow(false, 0, "")`,與「查無資料」的回傳一模一樣 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR060_PO.cs:83-89` | 中 |

### E6 空 `catch` 與吞例外

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR066.cs:205-208` | `catch { // pass }` —— 全模組唯一的空 catch,包住「一次印成功 + 失敗兩份報表」的整段流程 | **高** |
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:100-103` | 反過來把 `ex.ToString()`(含完整堆疊)直接秀給使用者 | 低 |

### E7 六處 `catch (SqlException)` 在 Oracle-only 環境是死碼

`architecture.md §4.6` 已確認執行期是 Oracle-only。RSP 有六支 PO 掛 `catch (SqlException sqlex)`:

`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB009_PO.cs:109`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB015_PO.cs:368`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB016_PO.cs:240`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:276`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB019_PO.cs:95`、`Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR049_PO.cs:72`。

**只有 `RSPB008` 用對了 `catch (OracleException)`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:113`)。後果是這六支永遠拿不到資料庫的原始錯誤訊息,全部掉進下方的通用 catch 變成固定字串。嚴重度高(`RSPB009` 那支尤其,見 E1-4)。

### E8 兩支畫面沒有移轉到 Oracle(假設)

| 畫面 | 證據 | 嚴重度 |
|---|---|---|
| `RSPM037` | `ISNULL` / `CONVERT(NVARCHAR,…,111)` / `GetDate()` / `[]` / `f_GetAgent()` / `SqlDbType` / 無 A 尾碼表名 / 無 `[PODbType]` / 基底是 `BasicEVAPO` | **高** |
| `RSPB010` | `EXEC s_RSPB010_Excute @p=@x…` T-SQL 字串 / `SqlDbType` / `dbo.f_GetBankHQ()` / 無 `[PODbType]` / 基底是 `BasicEVAPO` | **高** |

錨點:`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:17`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:274`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:17`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:155`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB010_PO.cs:425`。

**假設**:這兩支在現行 Oracle 環境不可用。依據是上述語法在 Oracle 皆非法,且其餘 23 支 PO 一律 `[PODbType(DbServerType.Oracle)]` + `OracleDbType` + `NVL`。**無法實測,不敢斷言**——也可能資料庫端留了相容物件,或這兩支功能早已停用。`RSPB010` 是扣款作業鏈上的第二棒(§1.4),如果真的不能用,整條鏈的運作方式跟本文描述的會不一樣,**動手前務必先跟站台確認**。

### E9 簡易開戶:註解說取消,程式路徑還在,而且 SQL 可能組錯

`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:36` 寫「2013.01.29 取消簡易開戶功能」,但 UI 沒有任何開關關掉它(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:902-919`)。

PO 側那段把三個 `INSERT` 用 `;` 串成一條 SQL,**沒有包 `BEGIN` / `END`**(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:696-803`)。同 repo 要送多段 DML 時都有包(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB020_PO.cs:560`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569`),`xTableHelper.GetInsertString` 產的也是不帶分號的單句(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:486-511`)。

**假設**:這條 SQL 在 Oracle 會拋 `ORA-00911`,也就是簡易開戶實際上已經不能用——這跟 2013 那句註解吻合。`Database.ExecuteNonQuery` 無原始碼(框架 DLL),無法確認它會不會自動包區塊。嚴重度中(功能本來就宣稱取消,但**畫面還是會把開戶欄位打開讓使用者輸入一整頁資料,按下存檔才爆**)。

### E10 併發與交易

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPB018` 逐檔基金各自 commit,中途失敗前面不回滾 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB018_PO.cs:209-241` | 中(刻意設計,但操作手冊必須寫) |
| 2 | `RSPB052` 兩個獨立交易(業務庫 + PTPF 庫),沒有分散式交易 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:110-111`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:440-441` | 中(全庫性,見 `architecture.md §4.7`) |
| 3 | 五支 SP 外殼的 `catch` 無條件 `tran.Rollback()` 不檢查 null,而同方法的 `finally` 有檢查 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:87` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:95` | 低 |
| 4 | `RSPB008_Service` 的 `sTIMES` 是執行個體欄位,timer 事件與 `GetTIMES()` 之間沒有同步 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:18`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:99` | 低(60 秒間隔,實務上碰不到) |
| 5 | `RSPB008_Service` 的 log 檔每次寫入先整份讀再整份重寫,而且沒有清檔 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:133-146` | 低 |
| 6 | BMS 的 `BMSB901A` 清暫存表時 `DELETE BMSB901A_T1; DELETE BMSB901A_T2;` **不帶 `DATAID`** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:200-203` | 中(它會 `MERGE` 進 `RSP005A` / `RSP006A`,見 §8.2) |

### E11 字串串接進 SQL / 過濾式

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:56-63` | `AddParam` 把參數值用 `'` 包起來直接串進 SQL,含 `LIKE` / `IN` / `=` 三種 | **高** |
| `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2363-2364` | `CheckSrNoComment` 把 `SrNo.BfNo` 與 `BF_NO` 串進 SQL | 中(值來自系統不是使用者) |
| `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR049.cs:70` | `DataTable.Select("CAMPAIGN_CODE = '" + dr.CAMPAIGN_CODE + "' OR …")` | 低 |
| `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2271-2273` | `string.Format("iSUB_ACCOUNT_NO='{0}' AND iSEAL_TYPE='{1}' AND iSUB_DATE=#2009/1/", …)` 再接扣款日與 `#` | 低 |
| `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM037.cs:114` | `Select("LEAVE_EMP_NO='" + row.EMP_NO + "'")` | 低 |

`architecture.md §4.7` 已把「全庫 PO 的通用寫法」記為高嚴重度;RSP 這邊多數取數已改用具名參數,`RSPM037` 是唯一還整支字串串接的。

### E12 死條件、死分支、寫反的判斷

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `(SUB_BANK_CODE LIKE '700%' OR (SUB_BANK_CODE='' AND SUB_BANK_CODE LIKE '700%'))` —— 第二個分支不可能成立 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255-2257` | 低 |
| 2 | `RSPM005.AfterApproveDelete` 的 `if (strSQL != string.Empty)` —— `strSQL` 至少是 `"BEGIN END;"`,守衛永遠成立 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-573` | 低 |
| 3 | 同一段 `CancelStop(row1)` 被呼叫兩次,第二次只為了判斷要不要加分號 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:569-570` | 低 |
| 4 | `RSPM005` 新增變更書的來源檢核三條 AND 串:**只要該契約曾經開過任何一張變更書,整條檢核就失效** —— 而訊息正是「契約書已被異動,尚未覆核,不可新增異動資料」 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:423-436` | **中高** |
| 5 | `RSPM042` 的「有沒有變更」用六個計數,其中兩個看的是 `_BEF`(變更前)欄位,永遠有值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:858-877` | 中 |
| 6 | `RSPB042.ValidateOFD303A` 迴圈內 `Errmsg = "..."`(不是 `+=`)且用 `else if`,**多檔基金只會留最後一條訊息,而且買回與申購兩種錯誤只報一種** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB042_PO.cs:143-147` 對照正確寫法 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:148-151` | **中高** |
| 7 | `RSPM004.CheckSrNoComment` 用 `ExecuteNonQuery` 去跑 `SELECT COUNT(0)`,拿回來的是「影響列數」不是 count | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2366-2370` | 中(簡易開戶的戶號防撞號守衛形同無效) |
| 8 | `RSPB008` 的 `AfterExecuteButtonClicked` 判 `Result.Count == 2`,而 PO 永遠只 `AddResultRow` 一次 —— 死碼 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB008.cs:128-131` | 低 |
| 9 | `RSPR034` 的 `switch` 沒有 `default`,`PREVIEW` 分支被註解後會靜默落空 | `Dev/ATLAS.RSP.Report/Source/PO/ReportPO.RSP/RSPR034_PO.cs:135-192` | 中 |
| 10 | `RSPM004.SetBfDataVisible(false)` 沒有把 `Simple_Open` 設回 `false`,旗標只會被設成 `true` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:1929-1939` | 低 |

### E13 一個概念多套實作

| 概念 | 幾套 | 說明 |
|---|---|---|
| 「還有沒覆核的資料」的比較運算子 | 3 種 | `RSPB008` 用 `=`、`RSPB023` / `RSPB041` 用 `<=`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:156` / `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB023_PO.cs:111`) |
| 檢核方法的回傳約定 | 2 種相反 | `CheckStatus` / `CheckSmallAmountCode`:有問題時 `ReturnCode = true` 靠訊息判斷;`ValidateOFD303A` / `ValidateLOGxxxA`:有問題時 `ReturnCode = false`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:172` 對 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:192`) |
| 「不限」的表達 | 2 種 | 哨兵值 `'19000101'` 與 `NULL` 判斷,同一支 SQL 內混用(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:155-158`) |
| 主明細宣告 | 2 種 | `xTableMapping`(23 支)與 `TableMapping`(`RSPB010` / `RSPM037`) |
| PO 基底 | 2 種 | `BaseEVADaoPO`(23 支)與 `BasicEVAPO`(2 支) |
| 168 的 `DECODE(REDEM_DATE, …)` 展開表 | 抄了 2 份 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:126-128` 與 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB021_PO.cs:163-165` |
| `Compare()` 變更前後比對 | 抄了 2 份 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM022.cs:1093` 與 `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1011` |
| 「挑申購書」的四條檢核 | 抄了 2 份 | `RSPM021` 新增(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:225-300`)與修改(`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:340-390`) |
| `RSPB023` / `RSPB041` | 整支抄 | PO 與 UI 都是逐行相同,只差表名 |
| `RSPM004` / `RSPB020`、`RSPM021` / `RSPB025` | 整支抄 | 取數 SQL 與 xsd 平行維護 |

### E14 手寫逐欄對應

`RSPB052` 用 `xTableHelper.GetInsertString(dbProduct, "RSP013A")` 產出 `INSERT`,再手動 `AddInParameter` 127 個欄位(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:179-390`)。

`GetInsertString` 的欄位清單來自 **DB schema** 而不是 xsd(`Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs:488-511`),所以**只要有一個實體欄位沒被綁,整段會 `ORA-01008` 失敗**。比對 `RSPM005Model.xsd` 的 `RSPM005_Detail`(153 欄)與實際綁定的 127 個,扣掉四眼 14 欄後還有 11 個沒綁:

`BEF_FUND_NAME` `AFT_FUND_NAME` `BEF_BANK_HQ_SHNM` `AFT_BANK_HQ_SHNM` `BEF_CAMPAIGN_SHNM` `AFT_CAMPAIGN_SHNM` `CODE_DESCRP` `SEAL_FAIL_ID_CO_DESCRP` `BEF_DEC_LEN` `AFT_DEC_LEN` `FIRST_SUB_DATE`

前八個看名字是 join 來的顯示欄(`_NAME` / `_SHNM` / `_DESCRP`),應該不在實體表上。**假設**:`BEF_DEC_LEN` / `AFT_DEC_LEN` / `FIRST_SUB_DATE` 三個也不在實體 `RSP013A` 上,否則 `RSPB052` 每次執行都會失敗。依據是這支程式有被使用的痕跡(2016 年的註解與測試用寫死日期,`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:152`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:191-192`)。**無法實測**——這條是 `bms.md` 記的「手寫逐欄對應漏欄」同型風險,加欄位到 `RSP013A` 時**一定要回來補這 127 行**。

另外 `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:193` 同一行把 `CHG_UPD_DTTM` 加了兩次。

### E15 寫死常數〔客戶特定〕

| 值 | 在哪 | 錨點 |
|---|---|---|
| `'2'`(扣款帳號抓取依據) | `RSPM004` / `RSPB020` 的 UI 與 PO 各一處 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:166`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:212` |
| `'301'`(四眼狀態) | 三處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB052_PO.cs:135`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB052.cs:183`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1216` |
| `'ALL FUNDS'`(`OFD131A.FUND_ID`) | `AddOFD130A` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1234` |
| `DATE'1900-01-01'`(`REJECTDATE`) | `AddOFD130A` 兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1217`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1238` |
| `'140'` / `'090'`(`BF_SORT_CD`) | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:661`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:671` |
| `'0001'`(`BF_NATIONALITY`) | 簡易開戶 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:676` |
| `'700'`(郵局) | `RSPM004` 三處 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2255`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2422`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2753` |
| `10000`(停利門檻下限) | `RSPM041` / `RSPM042` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:765`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:826` |
| `0.5`(手續費率上限對折) | `RSPM041` / `RSPM042` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:949` |
| `6` / `16` / `26`(轉申購日) | `RSPB021` / `RSPB024` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB021.cs:61`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPB024.cs:65` |
| `'86A03'`(促銷活動) | `RSPM004_PO.Check86A03` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:1785` |
| `'1'`(`EMP_CD`) | `RSPM037` 兩處 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:96`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:111` |
| `'42'`(`COD006A.CODE_SORT`) | `RSPM004` 取數 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:247` |
| `'6'`(`OFD681.SEND_TYPE`) | `RSPB008` | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPB008_PO.cs:344` |
| `60000` 毫秒 | 服務 timer | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:25` |
| `C://Vendor//WindowService//RSPB008//` | 服務 log 路徑 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:114` |
| `"AutoJob"` | 服務的 `UserID` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:52` |
| `AGITest` / `sa` / `sa` / `test002` / `TAAdmin` | 服務 `App.config` 的明碼連線字串 | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/App.config:73-77` |
| `'039'` → `'810'` / `'20171207'` / `'20171219'` | BMS 的 `BMSB901A` 寫進 `RSP006A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:174-178` |

### E16 型別與字串處理

| # | 問題 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `RSPM021` 的申購金額合計用 `Convert.ToInt64` 累加,不是 `decimal` —— 小數被四捨五入。全庫金額一律 `decimal`(`architecture.md §4.6`) | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:242`、`Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM021.cs:246` | 中 |
| 2 | `RSPR017` 把 `RSP_TYPE` 做 `Trim('0')`,值本身是 `"0"` 時會變成空字串 | `Dev/ATLAS.RSP.Report/Source/UI/ReportUI.RSP/RSPR017.cs:130` | 中 |
| 3 | `RSPM004` 的限額檢核用 `Convert.ToInt32(row.RSP_ALLOT_DAYS1)`,扣款日為空字串時會丟例外;而它前面的 `DataTable.Select` 過濾式也會變成語法錯的 `iSUB_DATE=#2009/1/#` | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM004.cs:2278-2288` | 中 |
| 4 | `RSPM004` / `RSPM005` 的 `AfterApproveDelete` 用 `BuildOldSeal().Split(';')[0]` / `[1]` 切 SQL —— SQL 內若出現任何分號就錯位 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2623`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:2628`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:590`、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:596` | 中 |
| 5 | `RSPM042.Compare()` 的空值相等判斷寫成 `(befObj == null ^ aftObj != null)` —— 結果正確但沒人讀得懂,且 `RSPM022` 抄了同一份 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM042.cs:1018-1019` | 低 |
| 6 | `RSPM041` 的 `NoticeFeeRate * Convert.ToDecimal(0.5)` —— `0.5` 是 `double` 字面值 | `Dev/ATLAS.RSP/Source/UI/UI.RSP/RSPM041.cs:841` | 低 |
| 7 | 服務的 `WriteLog` 用 `Encoding.Default` 讀寫中文 log | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:135`、`Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008/RSPB008_Service.cs:141` | 低 |

### E17 非 UTF-8 來源檔:40 個

`Dev/ATLAS.RSP/` 與 `Dev/ATLAS.RSP.Report/` 底下的 `.cs` / `.xsd` / `.config` / `.csproj`(排除 `obj/`)共 **40 個是 cp950**,其餘是 UTF-8。集中在兩群:

- `RSPB008` / `RSPB009` / `RSPB016` / `RSPB018` / `RSPB019` 那一整組(UI / Designer / Control / FormProxy / PO 全部)

- `Dev/ATLAS.RSP.Report/Source/Entity/ReportDataEntity.RSP/RSPR060ModelVDB.cs` 那一批共 10 個檔

後果:`grep` / `rg` 直接搜中文字串會漏掉這 40 個檔。本文的所有搜尋都走 `docs/tools/atlas_scan.py` 的 `read_text()`(依序試 `utf-8-sig` / `utf-8` / `cp950`)。**要在這個模組找中文訊息,不要直接用 grep。**

### E18 標「假設」的地方一覽

| # | 假設 | 依據 | 在哪一節 |
|---|---|---|---|
| 1 | `RSPM037` 在現行 Oracle 環境不可用 | T-SQL 語法 + 無 A 尾碼表名 + 無 `[PODbType]` | §0.2、§4.6、E8 |
| 2 | `RSPB010` 同上 | `EXEC` 字串 + `dbo.` TVF + `SqlDbType` | E8 |
| 3 | 簡易開戶的三段 `;` 串接 SQL 在 Oracle 會失敗 | 同 repo 其他多段 DML 都包 `BEGIN`/`END`;`GetInsertString` 產單句 | §4.1、E9 |
| 4 | `RSPB052` 未綁定的 `FIRST_SUB_DATE` / `BEF_DEC_LEN` / `AFT_DEC_LEN` 不是實體欄 | 否則該批次每次執行都會 `ORA-01008` | E14 |
| 5 | 框架的 `Database` 有設 `BindByName = true` | 全模組大量使用具名參數且順序與 SQL 不一致;`RSPB052` 多加一個參數仍能跑 | §6.7 |
| 6 | 服務 `App.config` 的五組 SQL Server 連線字串是舊環境殘留 | PO 建構子明確指定 Oracle;值是開發機 `AGITest` / `sa` | §6.3 |
| 7 | 業務線的劃分(A–E 五條) | 表名、欄位 Caption、Designer 標籤、訊息字串 | §0.1 |
| 8 | 一日作業的先後順序 | `RSPB019` 的訊息字串直接寫出「請先從(RSPB016)計算作業開始」,其餘由各批次的檢核對象反推 | §1.4、§1.5 |
| 9 | 沒有 I 畫面的三個原因 | 報表吸收查詢需求 + M 畫面自帶查詢頁 + 兩支偽 B 補位 | §5 |
| 10 | `SUB_STATUS` / `RSP_CTL_CODE` 的值域 | 全部由檢核訊息字串反推,沒有代碼表佐證 | 附錄 C |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版 |

由 build_doc.py v2.0.0 於 2026-09-15 11:10 產生 · 標題 181 · 圖 5 · 表格 97 · 程式錨點 925 · § 連結 63 · 引用檢查：畫面 77（缺 0） · Table 46（缺 0） · Report 39（缺 0） · 結果集 31（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/nfdr1.md
============================================================

# ATLAS NFDR1 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:`Dev/ATLAS.NFD.Report` 專案 127 支報表中的**前 44 支**(`NFDR001`–`NFDR160`)。`NFDR167` 以後的 83 支在別篇。 **建議讀法**:趕時間只讀三段——§0.1(`NFD` 到底是什麼)、§2.1(它讀誰的表)、附錄 E(踩雷)。要動某支報表再翻 §7 對應小節。

> ⚠ **本模組的業務意義**(§0)由**報表中文名、Crystal 參數名、PO 讀到的表名**三路反推。`NFD` 三個字母的展開在 repo 裡找不到任何定義,**本文不造官方名稱**。 ⚠ **〔客戶特定〕**:機構代碼、基金代碼、`CTL014` / `CTL018` 代碼值、寄件主旨與檔名格式為本站台的值。 ⚠ **〔共用〕**:本模組**一張自有主檔都沒有**,讀到的表全部屬於別的模組(見 §2、§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 `NFD` 是什麼(推測)

**一句話:`NFD` 不是一條業務軌,是一個「純輸出層」——它是境內基金(`OFD` 軌)資料的報表與對外文件產生器,自己不維護任何資料。**

這是全庫**唯一只有 R、沒有任何 M / I / B 畫面的模組**。127 支全部是報表,`Dev/ATLAS.NFD.Report` 之外**沒有** `Dev/ATLAS.NFD` 這個主專案——其他模組都是「主專案 + `.Report` 子專案」成對出現(`ATLAS.CAS` / `ATLAS.CAS.Report`、`ATLAS.CLS` / `ATLAS.CLS.Report`…),`NFD` 只有 `.Report` 一半。

推測依據,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 報表中文名 | 「基金受益人名冊」「資金來源分析表」「股權分散表」「員工及其關係人買賣本公司基金月報表」「債券型基金其他資訊揭露月報表」「各基金餘額比例表」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:47`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR002.cs:36`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR003.cs:43`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR004.cs:34`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR006.cs:87`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR007.cs:71` |
| 報表中文名(對外文件) | 「投資對帳單」「貴 賓 理 財 對 帳 單」「申購交易確認書」「申購交易確認書(郵簡)」「買回轉申購交易確認書」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:247`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:252`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR077.cs:233` |
| 報表中文名(扣款與手續費) | 「指定扣款-申購扣款彙總表」「指定扣款-申購扣款明細表」「指定扣款-申購扣款失敗明細表」「各銷售機構各基金手續費明細表」「各銷售機構手續費通知函」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR102.cs:52`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR103.cs:39`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:125`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:129` |
| 讀到的表 | PO 內寫得出表名的地方,清一色是 `OFD*`:`OFD017A`、`OFD081A`、`OFD081V`、`OFD0811A`、`OFD123A`、`OFD132A`、`OFD221A`、`OFD251A`、`OFD303A`、`OFD306A`、`OFD126`、`OFD002` | 見 §2.1 的逐支對照 |
| 專案不成對 | `Dev/` 下有 `ATLAS.OFD` + `ATLAS.OFD.Report`,但只有 `ATLAS.NFD.Report`,沒有 `ATLAS.NFD` | `Dev/ATLAS.NFD.Report/Source/Vendor.ATLAS.NFD.Report.sln` |

**所以 `NFD` 的業務範圍 =「境內基金 TA 的對外文件與法遵/營運報表」**。本文一律用這個描述,不替 `N` 造字(「國內」「Non-offshore」「New」都查不到依據,**不寫**)。

### 0.2 `NFD` 跟 `OFD` 是什麼關係

已知的三條軌(前篇查證):`ATLAS.OFD*` = 境內分戶軌、`ATLAS.OTA*` = 境外綜合帳戶軌、`ATLAS.EC*` = 電子交易軌。

**`NFD` 不是第四條軌**,依據是它沒有自己的表。切分維度是**「報表歸屬」而不是「業務軌」**:

|  | `ATLAS.OFD.Report` | `ATLAS.NFD.Report` |
|---|---|---|
| 支數 | 40 支 | 127 支 |
| 讀的表 | `OFD*` 為主 | `OFD*` 為主(**同一批表**) |
| 有無配對主專案 | 有(`ATLAS.OFD`) | **無** |
| 內容性質(從報表名推測) | 貼著 `OFD` 畫面的作業型清單 | 對外文件(對帳單、確認書)+ 法遵月報 + 手續費/扣款結算 |

**假設**:兩套報表專案共用同一批 `OFD*` 表,差別在**誰是讀者**——`ATLAS.OFD.Report` 是給 `OFD` 畫面操作員看的作業清單,`ATLAS.NFD.Report` 是給受益人、銷售機構、主管機關看的對外文件。依據是報表名:`NFDR004`「員工及其關係人買賣本公司基金月報表」、`NFDR006`「債券型基金其他資訊揭露月報表」是主管機關格式;`NFDR073`「投資對帳單」、`NFDR076`「申購交易確認書」是寄給客戶的。**這是推論,repo 內沒有文字說明兩套的分工。**

另一條可查的線索:`NFD` 的 44 支裡有 11 支自己建暫存表(`NFDR073T0`~`NFDR073T34`、`NFDR104_T0`、`NFDR106_T1`、`NFDR188_T1`、`NFDR352T1`…,DDL 在 `DB/Table/`),也就是說它**會為了印報表而寫入資料庫**,但寫的都是以報表代號命名的 `*T*` 暫存表,不是業務主檔。這佐證「純輸出層」的定位:它可以落地中繼資料,但不擁有業務事實。

### 0.3 不管什麼

| 不管 | 誰管 | 依據 |
|---|---|---|
| 任何資料的新增 / 修改 / 刪除 | `ATLAS.OFD` 的 M 畫面 | 本專案 127 支全是 `xReportForm`,沒有 `xMaintainForm` / `xQueryForm` / `xBatchForm`;見 §4–§6 |
| 四眼覆核 | `ATLAS.OFD` | 本模組 Ctl 只有 `GetXxxReportData` / `GetXxxReportObject`,無 `Verify` / `Approve` / `Reject`,例:`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:39-76` |
| 排程批次 | `ATLAS.OFDB` / WindowsService | 本模組無 B 畫面 |
| 境外綜合帳戶資料 | `ATLAS.OTA*` | 本片 44 支未讀到任何 `OTA*` 表 |

### 0.4 使用角色

| 角色 | 用哪些 | 依據 |
|---|---|---|
| 主管機關申報窗口 | `NFDR003`(股權分散表)、`NFDR004`(員工及其關係人買賣月報)、`NFDR006`(債券型基金其他資訊揭露月報) | 報表中文名,錨點見 §0.1 |
| 客戶服務 / 寄發作業 | `NFDR073`(投資對帳單)、`NFDR073A`、`NFDR073B`(貴賓理財對帳單)、`NFDR076`(申購交易確認書)、`NFDR077`(買回轉申購確認書) | 報表中文名 + `NFDR073B` 有寄信 SP `S_TA_NFDR073B_EMAIL`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs`) |
| 通路 / 手續費結算 | `NFDR107A`、`NFDR107B`(各銷售機構各基金手續費明細/合計/通知函) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:109-129` |
| 扣款作業 | `NFDR101`–`NFDR105`(指定扣款彙總/明細/失敗明細) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58` |

### 0.5 全域開關與前提

| 開關 | 在哪 | 影響 |
|---|---|---|
| Oracle 連線 `Database("TA", DbServerType.Oracle)` | 每支 PO 建構子,例 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:25` | 全模組走 Oracle;PO 上的 `[PODbType(DbServerType.Oracle)]` 決定執行期選哪個 PO |
| `Cmd.CommandTimeout = 0` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56` | **永不逾時**。SP 卡住時 client 會無限等待,沒有取消機制 |
| `CRReportTransfer.TransferFileByte(rpt)` | 每支 Ctl 的 `GetXxxReportObject`,例 `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:45` | 報表範本以**檔名字串**在執行期取得,不是強型別參考。範本檔不在部署路徑就是執行期錯誤,編譯期查不出來(見 §2.3) |

### 0.6 這模組最反直覺的三件事

**一、它是一個「只有下半身」的模組。** 其他模組都是 `ATLAS.XXX`(主專案)+ `ATLAS.XXX.Report`(報表子專案)成對存在。`NFD` 只有 `.Report`。所以在 `Dev/` 下找 `ATLAS.NFD` 找不到不是漏掉,是本來就沒有。同理,任何「`NFD` 的表」「`NFD` 的維護畫面」「`NFD` 的批次」都不存在(§4、§5、§6)。

**二、它的資料層有 36% 目前是壞的,而且是靜悄悄壞的。** 44 支裡 16 支的 PO 繼承 `Basic_PO`,`m_db` 宣告成 `null` 且建構子裡唯一的指派被註解掉(附錄 E-02)。這 16 支在 Oracle 環境按下預覽會 `NullReferenceException`。其中包括 `NFDR073`(投資對帳單)與 `NFDR154`(贖回交易確認單)這種對外文件。**選單上看不出差別**——它們和能跑的 28 支長得一模一樣。

**三、要查「這張報表讀哪些表」,三分之二的情況查不到。** 44 支點名 60 個 stored procedure,版控裡只有 1 支(§2.2)。29 支的 PO 除了 `AddInParameter` 之外一行 SQL 都沒有(§2.1.2)。這代表**任何 `OFD*` 表的影響面分析,在 `NFD` 這裡一定是不完整的**,而且沒有辦法從 repo 補完。

這三件事合起來解釋了為什麼本文的結構和其他模組的文件不一樣:§4 / §5 / §6 是空的但要展開講「為什麼空」,§2 與 §8 特別厚,§7 的重點不是「這張報表怎麼算」(算法在版控外)而是「這張報表怎麼取數、會在哪裡少印」。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] NFD 報表第 1 片全景：五群 44 支報表、取數路徑、讀到的別模組的表、三條輸出出口，以及本模組不存在的四件事
圖中文字:① 五群報表（本片 44 支，全部是 R，沒有 M／I／B） / NFDR001–007 / 受益人結構+法遵月報 7 支 / NFDR021–024 / 排行+異常清冊 3 支 / NFDR071–077 / 對帳單／確認書 8 支 / NFDR101–123 / 申購側 16 支 / NFDR150–160 / 買回／贖回側 10 支 / ② 取數：29 支完全看不到表名（SQL 在版控外的 SP 裡） / 60 支 SP / 版控內只有 1 支 / PO inline SQL / 只有 15 支有 / NFDR073T0–T34 / NFD 自建暫存 17 張 / Basic_PO 16 支 / m_db 未初始化→NRE / INFDRxxx_PO 28 支 / 已遷 Oracle / ③ 真正的業務資料：全部是別人的表 / OFD 軌 14 張 / OFD081V OFD303A OFD0811A… / BMS001A / 受益人主檔 / COD009 SAL051 FSK003 / 員工／業務員／風險屬性 / CTL014 CTL018 / 代碼表（內容在 DB） / ④ 三條出口 / Crystal .rpt × 79 / 42 支；全在版控+csproj / Excel / NFDR123 / 120 / 121 / 文字檔 + ZIP 加密 / NFDR073A（無 .rpt） / Email 佇列 / NFDR073B 寫 SP / ⑤ 不存在的東西（這是 NFD 最大的特徵） / 無 M 畫面 / 不維護任何資料 / 無 I 畫面 / 不做查詢 / 無 B／Service / 沒有排程 / 無 ATLAS.NFD 主專案 / 只有 .Report 一半
```

*圖:圖 1 NFDR1 全景。橘框=本片深寫的重點；灰虛框=借用別模組的表或「不存在」的事實；黑框=無原始碼的黑箱（版控外 SP、代碼表內容）；橘虛框=行為含寫死值或已知風險〔客戶特定〕。實線=同一支報表內的呼叫；虛線=輸出方向。*

### 1.2 資料表關係

本片 44 支報表**沒有任何一張自有業務主檔**。PO 裡寫得出表名的只有 15 支,其餘 29 支的 SQL 全部埋在版控外的 SP 裡(§2.1)。圖見 §2 的扇入圖。

### 1.3 報表的六層呼叫順序

所有 44 支走同一條路,沒有例外:

| 步 | 在哪一層 | 做什麼 | 錨點範例 |
|---|---|---|---|
| 1 | UI `xReportForm` | `FormInitial` 設定 `ResultVDB` 與 `FormProxy` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:32-34` |
| 2 | UI | `BeforePreviewButtonClicked` 跑 `DoValidate()`,有錯就 `e.Cancel = true` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:75-80` |
| 3 | UI | 把畫面條件塞進 `Utility.Parameters`(Name / Operator / Value 三欄) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:151-163` |
| 4 | FormProxy | 轉呼叫遠端 Control | `Dev/ATLAS.NFD.Report/Source/FormProxy/ReportFormProxy.NFD/NFDR001_Pxy.cs` |
| 5 | Control | `GetXxxReportData` → `ExecPOActionToViewVDB` 打 PO;`GetXxxReportObject` → `CRReportTransfer.TransferFileByte(rpt)` 把 `.rpt` 範本傳回 client | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:45,59-62` |
| 6 | PO | `GetStoredProcCommand(...)` 或 `GetSqlStringCommand(strSQL)` 取數,填進 `ModelVDB` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57` |
| 7 | Control | `CustomTransferOracleModelToView` 把 `ModelVDB` 每張 DataTable 搬到 `ViewVDB` | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:92-96` |
| 8 | UI | `ReportLoad` 用 `m_ReportDocument.SetParameterValue(...)` 把「顯示用」參數餵給 Crystal | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:49-53` |

**第 7 步是本模組最常出錯的地方**:`CustomTransferOracleModelToView` 是逐張 DataTable 手抄。SP 多回一張表、或 `Model.xsd` 加了一張表而 Ctl 沒加對應的 `TransferTable`,結果是**該張表在報表上永遠空白,不會報錯**(見附錄 E-07)。

### 1.4 報表輸出的三條出口

| 出口 | 怎麼做 | 哪些支 |
|---|---|---|
| Crystal 預覽 / 列印 | `SetQueryParameters(ReportClass, ReportID, ReportName)` + `.rpt` 範本 | 42 支 |
| Excel 下載 | `ExcelCreator.CreateExcelDocument(dt, sFileName)` 直接存檔,**不經 Crystal** | `NFDR123`;`NFDR120` / `NFDR121` 為混合(有「下載」選項) |
| 文字檔 / ZIP | `CreateTxtFiles.CreateNFDR073AText(...)`,可加密碼壓縮 | `NFDR073A` |

### 1.5 一日作業泳道(推測)

repo 內沒有排程設定可讀,以下由報表名的期間參數推測,**標「假設」**:

| 時點 | 誰跑 | 跑什麼 |
|---|---|---|
| 日終 | 扣款作業 | `NFDR101` / `NFDR102` / `NFDR103`(指定扣款彙總 / 明細 / 失敗明細) |
| 日終 | 交易作業 | `NFDR105`(申購交易確認單)、`NFDR154`(贖回交易確認單)、`NFDR104`(申購明細表) |
| 月底 | 客服 | `NFDR073` / `NFDR073A` / `NFDR073B`(對帳單,`NFDR073A` 有「月對帳單 / 季對帳單」選項,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.Designer.cs:148-150`) |
| 月底 | 財務 | `NFDR107A` / `NFDR107B`(扣帳費 / 手續費)、`NFDR115` / `NFDR158` / `NFDR159`(申購 / 贖回 / 轉申購統計月報) |
| 月底 | 法遵 | `NFDR004`(員工及其關係人買賣月報)、`NFDR006`(債券型基金其他資訊揭露月報) |

### 1.6 要改這個模組的報表之前

操作步驟走 `add-report.md`(七層結構、Crystal 版本、`.rpt` 加進 csproj 的方式、部署路徑),**本文不重複**。以下只列 `NFD` 與該手冊的範例(`CASR001`,`Dev/ATLAS.CAS.Report`)不一樣的地方:

| 項目 | `add-report.md` 的 `CASR001` | `NFD` 本片 44 支 |
|---|---|---|
| 七層結構 | 相同(六層加 `Report` 前綴 + `CrystalReports/Report.XXX`) | **相同**,44 支全齊,無檔名例外 |
| 一支畫面掛多版型 | `CASR001` 掛 6 個 | `NFDR001` / `NFDR076` 掛 5 個,`NFDR073B` / `NFDR151` / `NFDR160` 掛 4 個;**但版型與選項是多對一**(§7.1.1),改一張會影響多個組合 |
| R 畫面沒有四眼 | 是 | **是**,44 支的 PO 都不宣告 `MasterTable` / `DetailTable`(§4) |
| 資料走 SP | 是 | **是,而且 SP 幾乎全在版控外**(§2.2)。改欄位時 repo 內改不到取數那一半 |
| 選版型在客戶端 | 是 | **是**,`SetQueryParameters(ReportClass, ReportID, ReportName)`;`NFDR151` 例外——**分派寫在 PO**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:70-98`),加版型要同時改 UI 與 PO |
| PO 基底 | 單一 | **兩種並存**:28 支 `INFDRxxx_PO`(Oracle)、16 支 `Basic_PO`(未遷移,附錄 E-02)。動到後者要先處理 `m_db` |
| 輸出一定是 `.rpt` | 是 | **兩支不是**:`NFDR073A`(文字檔)、`NFDR123`(Excel) |

**加一張新版型的最小改動清單(本模組版)**:

1. 新增 `.rpt` 到 `Dev/ATLAS.NFD.Report/Source/CrystalReports/Report.NFD/`,並加進 `Report.NFD.csproj`(本片 79 張全都有加,照抄既有寫法)。

2. UI 加一個 `SetQueryParameters("NFDRxxxRPSn", "NFDRxxxRPSn", "報表中文名")` 分支——**記得補 `else`**,否則落在列舉外就靜默什麼都不做(附錄 E-15)。

3. 若新版型需要新的結果集:`Model.xsd` + `View.xsd` + Ctl 的 `TransferTable` **三處一起改**(附錄 E-07)。

4. 若取數要改,**SP 不在版控**,要另外走資料庫變更流程,repo 內留不下痕跡。

## 2. 資料模型

```text
[圖] NFD 讀誰的表：15 支可見報表扇入到 OFD 軌 14 張表與 4 張共用主檔，NFD 自己的業務表是零張
圖中文字:本片 15 支「看得見表名」的報表 → 各模組的表（另 29 支在 SP 黑箱裡） / NFDR073A / 對帳單文字檔 讀 6 個模組 / NFDR076 NFDR077 / 申購／買回轉申購確認書 / NFDR123 / KYC 到期名單 / NFDR107A NFDR107B NFDR114 / 手續費／扣帳費／印花稅 / NFDR115/154/158/159 / 統計月報＋確認單 / NFDR001/073/073B/101 / 名冊／對帳單／扣款 / OFD081V / 4 支 · view，定義不在版控 / OFD303A / 5 支 · 日結檢核的來源 / OFD0811A OFD081A / 基金屬性 INV_AREA／PROF_TYPE2 / OFD221A OFD251A OFD306A / 申購／買回／異動 / OFD002 017A 123A 126 132A / 其餘 OFD 表各 1 支 / BMS001A / 4 支 · 受益人主檔 / COD009 SAL051 FSK003 / 員工／業務員／風險屬性 / CTL014 CTL018 / 代碼表 / OFD 軌 14 張 / 境內分戶軌 = 真正的業務資料 / BMS／COD／SAL／FSK 4 張 / 共用主檔 / CTL 2 張 / 代碼 / NFDR073T* 17 張 / NFD 唯一自有：暫存 / NFD 自己的業務表：0 張 / 這就是「純輸出層」的定義
```

*圖:圖 2 扇入圖（§2.1）。左=本片看得見表名的 15 支；中=被讀到的表；右=按模組彙總。灰虛框=別模組的表（NFD 只讀不寫）；黑框=無原始碼／內容在 DB；橘虛框=NFD 唯一自有的暫存表。另有 29 支的相依性藏在版控外的 SP 裡，這張圖畫不出來。*

### 2.1 `NFD` 讀誰的表(本文最重要的一節)

**結論:44 支裡有 29 支(66%)完全看不到表名**——SQL 在版控外的 SP 裡。剩下 15 支可以從 PO 的 inline SQL 讀出表,清一色是 `OFD*` 加少數共用代碼表。

`NFD` 沒有任何一張自己的業務表。它唯一「自己的」是以報表代號命名的暫存表(`NFDR073T*`),而且只有 `NFDR073` / `NFDR073A` 在用。

#### 2.1.1 表的歸屬統計(僅計 PO 內看得見的)

| 表 | 歸屬模組 | 被本片幾支用 | 哪幾支 | 在 `atlas_index.json` |
|---|---|---|---|---|
| `OFD081V` | OFD | 5 | `NFDR073A` `NFDR115` `NFDR154` `NFDR158` `NFDR159` | 否(view,索引未收) |
| `OFD303A` | OFD | 5 | `NFDR076` `NFDR077` `NFDR107A` `NFDR107B` `NFDR114` | 否 |
| `BMS001A` | BMS | 4 | `NFDR073A` `NFDR076` `NFDR077` `NFDR123` | 是 |
| `CTL018` | CTL(代碼) | 3 | `NFDR073` `NFDR101` `NFDR107B` | 否 |
| `OFD0811A` | OFD | 3 | `NFDR073A` `NFDR076` `NFDR077` | 是 |
| `COD009` | COD | 2 | `NFDR073B` `NFDR123` | 是 |
| `OFD081A` | OFD | 2 | `NFDR073A` `NFDR077` | 是 |
| `OFD221A` | OFD | 2 | `NFDR076` `NFDR123` | 是 |
| `CTL014` | CTL(代碼) | 1 | `NFDR001` | 否 |
| `FSK003` | FSK | 1 | `NFDR073A` | 否 |
| `OFD002` | OFD | 1 | `NFDR073B` | 是 |
| `OFD017A` | OFD | 1 | `NFDR001` | 是 |
| `OFD123A` + `OFD123A_TMP` | OFD | 1 | `NFDR123` | `OFD123A` 是 |
| `OFD126` | OFD | 1 | `NFDR073` | 否 |
| `OFD132A` | OFD | 1 | `NFDR073A` | 是 |
| `OFD251A` | OFD | 1 | `NFDR077` | 是 |
| `OFD306A` + `OFD306_TMP` | OFD | 1 | `NFDR123` | 否 |
| `SAL051` | SAL | 1 | `NFDR073B` | 是 |
| `MYOFD303A` | ?(同義字 / 別名) | 1 | `NFDR077` | 否 |
| `NFDR073T0` `T5`–`T12` `T16`–`T19` `T24` `T29` `T31` `T33` `T34` | **NFD 自建暫存** | 2 | `NFDR073` `NFDR073A` | 否(DDL 在 `DB/Table/`) |
| `OCRMTMP` | ?(暫存) | 1 | `NFDR073` | 否 |

按模組彙總(去重後 42 張表):

| 模組 | 張數 | 佔比 | 說明 |
|---|---|---|---|
| **NFD 自建暫存** `NFDR073T*` | 17 | 40% | 只為了印 `NFDR073` / `NFDR073A` 而存在 |
| **OFD**(境內分戶軌) | 14 | 33% | **真正的業務資料全在這** |
| CTL(代碼) | 2 | 5% | `CTL014` `CTL018` |
| BMS / COD / FSK / SAL | 4 | 10% | 受益人基本資料、代碼、風險屬性、業務員 |
| 不明(`MYOFD303A` / `OCRMTMP` / `F_FORMATSTRINGTOTABLE`) | 3 | 7% | 同義字、暫存表、Oracle function |
| `OFD*_TMP` | 3 | 7% | `OFD123A_TMP` `OFD221A_TMP` `OFD306_TMP` |

**這張表就是 §0.1 結論的證據**:去掉自己造的暫存表,`NFD` 看得見的業務表 100% 是 `OFD` 軌的。

#### 2.1.2 29 支黑箱

以下 29 支的 PO **完全沒有 inline SQL**,只有 `GetStoredProcCommand` + `AddInParameter`,所以讀哪些表**從 repo 讀不出來**:

`NFDR002` `NFDR003` `NFDR004` `NFDR005` `NFDR006` `NFDR007` `NFDR021` `NFDR023` `NFDR024` `NFDR071` `NFDR072` `NFDR075` `NFDR102` `NFDR103` `NFDR104` `NFDR105` `NFDR108` `NFDR109` `NFDR111` `NFDR120` `NFDR121` `NFDR122` `NFDR150` `NFDR151` `NFDR153` `NFDR155` `NFDR156` `NFDR157` `NFDR160`

要查它們讀誰的表,只能到資料庫撈 SP 原始碼。**這是本模組最大的維護風險**(附錄 E-01)。

### 2.2 SP:60 支,版控裡只有 1 支

44 支報表一共點名 60 個 stored procedure。拿 `atlas_index.json` 的 `sps`(83 支)去比對,**只有 `S_TA_NFDR073_1_GET` 一支在版控**(`DB/SP/S_TA_NFDR073_1_GET.SQL`)。

| 命名樣式 | 支數 | 例 |
|---|---|---|
| `s_TA_NFDRxxx_Get` / `S_TA_NFDRxxx_GET` | 30 | `s_TA_NFDR001_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57`) |
| `s_NFDRxxx_Get`(**少了 `TA_`**) | 22 | `s_NFDR023_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR023_PO.cs:64`) |
| 帶序號 `_1_` / `_2_` / `_T2_` | 8 | `S_TA_NFDR151_GET_1`–`_5`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:81-116`) |

**兩套命名並存**且沒有規則可循:同一支 `NFDR073` 用 `s_NFDR073_Get`,而 `NFDR073A` 用 `S_TA_NFDR073_0_GET`~`_4_GET`。要找某支報表的 SP,**不能用代號硬推名字**,必須開 PO 看(見 §7 逐支)。

大小寫也混:`NFDR024` 寫 `S_TA_NFDR024_GET`,`NFDR001` 寫 `s_TA_NFDR001_Get`。Oracle 不分大小寫所以跑得動,但任何依檔名 / 字串比對的工具都會漏。

### 2.3 `.rpt` 範本:全部在版控,而且全部在 csproj

好消息,這片沒有前幾篇踩過的洞:

| 檢查 | 結果 |
|---|---|
| 44 支引用的 Crystal ReportClass 字串 | 共 79 個 |
| 對應的 `.rpt` 檔在 `Dev/ATLAS.NFD.Report/Source/CrystalReports/Report.NFD/` | **79 / 79 都在** |
| 這些 `.rpt` 有沒有進 `Report.NFD.csproj` | **79 / 79 都在** |
| UI / Ctl / PO 三層 `.cs` 有沒有進各自 csproj | **44 / 44 × 3 都在** |
| 六層(UI / Ctl / Pxy / PO / Model.xsd / View.xsd)齊不齊 | **44 支全齊**,沒有 `misc.md` 那種檔名少一個字母的情況 |

例外兩支,是設計如此不是缺陷:

| 支 | 為什麼沒有 `.rpt` | 錨點 |
|---|---|---|
| `NFDR073A` | 產文字檔不產 Crystal 報表,走 `CreateTxtFiles.CreateNFDR073AText(...)` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:114` |
| `NFDR123` | 產 Excel 不產 Crystal,`ExcelCreator.CreateExcelDocument(dt, sFileName)`,檔名寫死「受益人KYC到期名單.xlsx」 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79,86` |

`.rpt` 的取得方式仍然是**字串比對**:Ctl 拿前端傳來的 `ReportClass` 字串丟給 `CRReportTransfer.TransferFileByte(rpt)`(`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:44-45`)。編譯器不檢查,改 `.rpt` 檔名不改 UI 字串 = 執行期才爆。

### 2.4 `NFDR073T*` 暫存表家族

`NFDR073` / `NFDR073A` 這組對帳單自己建了 17 張以上的暫存表,DDL 在 `DB/Table/`(`NFDR073T16.sql`、`NFDR073T17.sql`、`NFDR073T18.sql`、`NFDR073BT1.sql`、`NFDR073BT2.sql`…)。

用法是**先 `DELETE` 再由 SP 重灌,以 `dataID` 分租**:

```
DELETE FROM NFDR073T6 WHERE dataID = @dataID; DELETE FROM NFDR073T7 WHERE dataID = @dataID
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385`

`dataID` 由 client 端組出來後截斷到 22 碼(`strDATAID.Substring(0, 22).Trim()`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102`)。**兩個使用者同時跑、`dataID` 前 22 碼撞到,兩份對帳單的資料會混在一起**(附錄 E-03)。

### 2.5 沒有狀態碼

本模組不改任何資料的狀態,所以沒有狀態機。畫面上的「選項」值(`uoptRPT_TYPE` / `uoptPrint` / `uoptOrder` / `uoptPurpose`)只影響**選哪支 SP、選哪張 `.rpt`、給 Crystal 什麼顯示字串**,不寫回資料庫。唯一的例外是 `NFDR073` / `NFDR073A` 寫暫存表(§2.4)與 `NFDR073B` 寄信留紀錄(`S_TA_NFDR073B_EMAIL`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160`)。

### 2.6 欄位中文名:`msdata:Caption` 在這個模組不可信

範本規定「欄位中文名以 `Model.xsd` 的 `msdata:Caption` 為準,不自己翻」。**這條規則在 `NFD` 只有一半適用**。

44 個 `Model.xsd` 裡 27 個有 `msdata:Caption`,17 個一個都沒有。而且有 `Caption` 的那 27 個裡,**有 9 個的 `Caption` 值根本不是中文名,是另一個欄位名**:

| 支 | 欄位 | `Caption` 值 | 這是什麼 |
|---|---|---|---|
| `NFDR002` | `PROF_TYPE` | `PROF_TYPE_NM_C` | 另一個欄位名 |
| `NFDR071` / `NFDR072` | `ANNOUNCE_AMT` | `TRAN_AMT1` | 另一個欄位名 |
| `NFDR073` | `NAV_DEC` | `DEC_LEN` | 另一個欄位名 |
| `NFDR073A` / `NFDR073B` | `FUND_SH_NM` | `FUND_SH_NM1` | 另一個欄位名 |
| `NFDR073A` / `NFDR073B` | `REDEM_COST` | `STK_COST` | 另一個欄位名 |
| `NFDR104` | `REMIT_ACC_TYPE` | `SYSTEM_ID` | 另一個欄位名 |
| `NFDR108` | `AGENT_ID_NM` | `AGENT_ID` | 另一個欄位名 |
| `NFDR151` | `SUM_PAID_AMT` | `SUM_RUNIT` | 另一個欄位名 |

錨點:`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR002Model.xsd`、`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR073AModel.xsd`、`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR151Model.xsd`。

**推測**:`Caption` 在這裡被當成「SP 實際回傳的欄位名」在用——DataSet 的欄位叫 `ANNOUNCE_AMT`,SP 回的欄位叫 `TRAN_AMT1`,用 `Caption` 記下對照。**這是 `Caption` 的誤用**,但改掉會影響 `TransferVDBHelper.TransferTable` 的行為,不能隨手動。

**所以在 `NFD` 查欄位中文名,要先看 `Caption` 值是不是中文**;不是中文就當成欄位對照,真正的中文名去 `.rpt` 或 `Designer.cs` 的 label 找。

### 2.7 欄位中文名總表(取自 `Model.xsd` 的 `msdata:Caption`,僅列中文者)

只有 5 支的 xsd 提供了成規模的中文欄位名。

| 支 | 欄位 → 中文名 |
|---|---|
| `NFDR109` | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `CRNCY_CD` 幣別 · `CRNCY_NM` 幣別名稱 · `AGENT_ID` 銷售機構別 · `AGENT_CODE` 銷售機構代碼 · `AGENT_SHNM` 銷售機構名稱 · `AGENT_SHNM_F` 完整銷售機構名稱(共 21 個) |
| `NFDR120` | `BANK_HQ` 總行代碼 · `BANK_HQ_SHNM` 總行名稱 · `BANK_HQ_SHNM_F` 總行完整名稱 · `BANK_BRH` 分行代碼 · `BANK_BRH_SHNM` 分行名稱 · `BANK_BRH_SHNM_F` 分行完整名稱 · `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱(共 29 個) |
| `NFDR121` | `AGENT_ID` 銷售機構別 · `AGENT_CODE` 部門代碼 · `AGENT_SHNM` 部門名稱 · `SPONSOR_CODE` 推薦人代碼 · `SPONSOR_NAME` 推薦人姓名 · `BF_NO` 受益人戶號 · `ID_NO` 統一編號 · `BF_NAME` 受益人戶名(共 38 個) |
| `NFDR122` | `AGENT_CODE` 部門代碼 · `AGENT_SHNM` 部門名稱 · `SPONSOR_CODE` 推薦人代碼 · `SPONSOR_NAME` 推薦人姓名 · `BF_NO` 受益人戶號 · `ID_NO` 受益人編號 · `BF_NAME` 受益人戶名 · `FUND_ID` 基金代碼(共 23 個) |
| `NFDR123` | `AGENT_ID` 銷售機構區別碼 · `AGENT_CODE` 銷售機構代碼 · `AGENT_NM` 銷售機構名稱 · `SPONSOR_CODE` 推薦人代碼 · `EMP_NO` 員工代碼 · `EMP_NAME` 員工姓名 · `BF_NAME` 客戶姓名 · `BF_NO` 戶號(共 12 個) |
| `NFDR150` | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `CRNCY_CD` 幣別 · `CRNCY_NM` 幣別名稱 · `REDEM_DATE` 買回日期 · `AGENT_ID` 銷售機構別 · `AGENT_CODE` 銷售機構代碼 · `AGENT_SHNM` 銷售機構名稱(共 19 個) |

**注意同一個欄位在不同支的中文名不一致**:`AGENT_CODE` 在 `NFDR109` / `NFDR150` 是「銷售機構代碼」,在 `NFDR121` / `NFDR122` 是「部門代碼」;`ID_NO` 在 `NFDR121` 是「統一編號」,在 `NFDR122` 是「受益人編號」,在 `NFDR023` 是「受益人ID」。**同一個欄位,三份報表三個中文名**——這不是 bug,但客服拿兩張報表對帳時會以為是不同欄位。

其餘 17 支完全沒有 `Caption`,欄位中文名只能從 `.rpt` 的欄位標題看,而 `.rpt` 是 Crystal 二進位,**repo 內讀不出來**。

### 2.8 `Model.xsd` 與 `View.xsd` 的關係

每支有兩個 xsd:

| 檔 | 角色 | 誰填 |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR001Model.xsd` | `ModelVDB`——伺服器端,PO 直接 `LoadDataSet` 進去 | PO |
| `Dev/ATLAS.NFD.Report/Source/Entity/ReportUIEntity.NFD/NFDR001View.xsd` | `ViewVDB`——傳回 client,Crystal 綁這一份 | Ctl 的 `CustomTransferOracleModelToView` 逐張手抄 |

**兩份要長得一樣,但沒有任何東西強制**。中間的 `TransferTable` 是一行一行寫的(§1.3 第 7 步、附錄 E-07)。加一張結果集要改四個地方:`Model.xsd`、`View.xsd`、Ctl 的 `TransferTable`、`.rpt` 的資料來源。少改一個不會編譯失敗,只會在報表上少一塊。

## 3. 報表清冊(44 支)

```text
[圖] 44 支報表依 PO 基底、資料來源、輸出型態、有無查無資料提示四種切法的分群
圖中文字:① 依 PO 基底：28 支已遷 Oracle vs 16 支停在 MSSQL / INFDRxxx_PO（28 支） / [PODbType(Oracle)] + 介面 + DataAccessPool / Basic_PO（16 支） / m_db = null，建構子被註解掉 → 一呼叫就 NRE / Ctl 直接 new PO / 沒有替換機會 / ② 依資料來源：SP 黑箱是主流 / 純 SP（29 支） / 讀哪些表查不出來 / SP + inline（14 支） / 部分可見 / 純 inline（1 支） / NFDR123 的 Oracle CTE / 無 SP 無 inline / （本片沒有） / ③ 依輸出：Crystal 為主，兩支例外 / Crystal 42 支 / 79 張 .rpt / 全在版控+csproj（本片零缺） / NFDR123 → Excel / 檔名寫死 / NFDR073A → 文字檔+ZIP / 密碼來自 config / ④ 依有沒有「查無資料」提示 / 有訊息 14 支 / 零筆會跳警示 / 完全沒有 30 支 / 印出只有表頭的空報表 / 有判斷但訊息是空字串 / NFDR151 / NFDR159 / NFDR105
```

*圖:圖 3 四種分群（§3）。橘框=需要留意的少數派；橘虛框=已知風險；黑框=無原始碼或查不到；灰虛框=空集合。第 ① 列是本模組最重要的一條：同一份選單上，有 16 支的資料層目前是壞的。*

欄位說明:**PO 基底**——`INFDRxxx_PO` 表示走介面 + `[PODbType(DbServerType.Oracle)]`,已完成 Oracle 遷移;`Basic_PO` 表示未遷移的舊版(見附錄 E-02,這 16 支的 `m_db` 永遠是 `null`)。**資料來源**——`SP` / `SP+inline` / `純 inline` / `無 DB`。**`.rpt`**——引用的 Crystal 範本數 / 在版控 / 在 csproj。

### 3.1 第 001–007 群:受益人結構與法遵月報(7 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR001` | 基金受益人名冊 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:47` | `INFDR001_PO` | SP+inline | `s_TA_NFDR001_Get` | `CTL014`、`OFD017A` | 5(全在版控+csproj) |
| `NFDR002` | 資金來源分析表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR002.cs:36` | `INFDR002_PO` | SP | `s_TA_NFDR002_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR003` | 股權分散表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR003.cs:43` | `INFDR003_PO` | SP | `s_TA_NFDR003_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR004` | 員工及其關係人買賣本公司基金月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR004.cs:34` | `INFDR004_PO` | SP | `s_TA_NFDR004_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR005` | 基金受益憑證持有者統計表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR005.cs:79` | `INFDR005_PO` | SP | `s_TA_NFDR005_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR006` | 債券型基金其他資訊揭露月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR006.cs:60` | `INFDR006_PO` | SP | `s_TA_NFDR006_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR007` | 各基金餘額比例表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR007.cs:55` | `INFDR007_PO` | SP | `s_TA_NFDR007_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |

### 3.2 第 021–024 群:受益人排行與異常清冊(3 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR021` | 受益人基金持有／申購／贖回單位數排行表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58` | `INFDR021_PO` | SP | `s_TA_NFDR021_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR023` | 受益人異動及定額異動重覆報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR023.cs:73` | `Basic_PO` | SP | `s_NFDR023_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR024` | 受益人統編異常清冊 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR024.cs:60` | `INFDR024_PO` | SP | `S_TA_NFDR024_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |

### 3.3 第 071–077 群:對帳單、確認書與公告(對外文件)(8 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR071` | 法人公告警示表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR071.cs:34` | `Basic_PO` | SP | `s_NFDR071_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR072` | 法人買回／贖回公告明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR072.cs:35-55` | `Basic_PO` | SP | `s_NFDR072_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR073` | 投資對帳單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49` | `Basic_PO` | SP+inline | `s_NFDR073_1_Get`、`s_NFDR073_Get`、`s_NFDR073_ChkRdm` | `CTL018`、`NFDR073T0`、`NFDR073T6`、`NFDR073T7`、`OCRMTMP`、`OFD126` | 1(全在版控+csproj) |
| `NFDR073A` | 月／季對帳單文字檔產生 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.Designer.cs:148-150` | `INFDR073A_PO` | SP+inline | `S_TA_NFDR073_3_GET`、`S_TA_NFDR073_0_GET`、`S_TA_NFDR073_4_GET`、`S_TA_NFDR073_1_GET`**(在版控)**、`S_TA_NFDR073_2_GET` | `BMS001A`、`FSK003`、`NFDR073T10`、`NFDR073T11`、`NFDR073T12`、`NFDR073T16` …共 23 張 | **0**(非 Crystal) |
| `NFDR073B` | 貴賓理財對帳單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123` | `INFDR073B_PO` | SP+inline | `S_TA_NFDR073B_GET`、`S_TA_NFDR073B_EMAIL` | `COD009`、`OFD002`、`SAL051` | 4(全在版控+csproj) |
| `NFDR075` | 傳真委託申購／委扣－扣款失敗通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR075.cs:44-58` | `INFDR075_PO` | SP | `s_TA_NFDR075_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR076` | 申購交易確認書（含郵簡、彙總） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:179` | `INFDR076_PO` | SP+inline | `S_TA_NFDR076_GET` | `BMS001A`、`OFD0811A`、`OFD221A`、`OFD303A` | 5(全在版控+csproj) |
| `NFDR077` | 買回轉申購交易確認書（含郵簡、彙總） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR077.cs:183` | `INFDR077_PO` | SP+inline | `S_TA_NFDR077_GET` | `BMS001A`、`MYOFD303A`、`OFD0811A`、`OFD081A`、`OFD251A`、`OFD303A` | 3(全在版控+csproj) |

### 3.4 第 101–123 群:申購側:扣款、手續費、稅、統計(16 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR101` | 指定扣款／傳真委扣－申購扣款彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR101.cs:58` | `INFDR101_PO` | SP+inline | `S_TA_NFDR101_GET` | `CTL018` | 1(全在版控+csproj) |
| `NFDR102` | 指定扣款／傳真委扣－申購扣款明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR102.cs:52` | `INFDR102_PO` | SP | `S_TA_NFDR102_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR103` | 指定扣款／傳真委扣－申購扣款失敗明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR103.cs:39` | `Basic_PO` | SP | `s_NFDR103_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR104` | 申購明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR104.cs:286` | `INFDR104_PO` | SP | `s_TA_NFDR104_Get` | **看不到(SP 黑箱)** | 3(全在版控+csproj) |
| `NFDR105` | 申購交易確認單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR105.cs:66` | `Basic_PO` | SP | `s_NFDR105_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR107A` | 各代理扣款機構扣帳費合計／明細、銀行單筆扣款彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107A.cs:175-183` | `INFDR107A_PO` | SP+inline | `s_TA_NFDR107A_Get` | `OFD303A` | 3(全在版控+csproj) |
| `NFDR107B` | 各代理扣款機構／銷售機構各基金手續費合計、明細、通知函 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR107B.cs:109-129` | `Basic_PO` | SP+inline | `s_NFDR107B_Get`、`s_NFDR107B_T2_Get` | `CTL018`、`OFD303A` | 3(全在版控+csproj) |
| `NFDR108` | 公司人員銷售彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR108.cs:77` | `Basic_PO` | SP | `s_NFDR108_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR109` | 銷售彙總查核表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR109.cs:266` | `INFDR109_PO` | SP | `S_TA_NFDR109_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR111` | 手續費彙總表／基金手續費彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR111.cs:140-145` | `INFDR111_PO` | SP | `S_TA_NFDR111_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR114` | 印花稅明細表／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR114.cs:49-53` | `Basic_PO` | SP+inline | `s_NFDR114_Get` | `F_FORMATSTRINGTOTABLE`、`OFD303A` | 2(全在版控+csproj) |
| `NFDR115` | 申購統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR115.cs:120` | `Basic_PO` | SP+inline | `s_NFDR115_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR120` | 代銷銀行單筆／定額申購明細表（列印＋下載） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR120.Designer.cs:439-505` | `INFDR120_PO` | SP | `S_TA_NFDR120_GET` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR121` | 券商單筆／定額申購明細表、彙總表（列印＋下載） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR121.Designer.cs:303-581` | `INFDR121_PO` | SP | `S_TA_NFDR121_GET_1`、`S_TA_NFDR121_GET_2` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR122` | 月平均成本餘額明細／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR122.cs:140-260` | `INFDR122_PO` | SP | `S_TA_NFDR122_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR123` | 受益人 KYC 到期名單（Excel） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` | `INFDR123_PO` | 純 inline | (無) | `BMS001A`、`COD009`、`OFD123A`、`OFD123A_TMP`、`OFD221A`、`OFD221A_TMP`、`OFD306A`、`OFD306_TMP` | **0**(非 Crystal) |

### 3.5 第 150–160 群:買回／贖回／轉申購側(10 支)

| 代號 | 報表中文名 | 名稱出處 | PO 基底 | 資料來源 | SP(版控外除非註明) | 讀到的表 | `.rpt` 數 |
|---|---|---|---|---|---|---|---|
| `NFDR150` | 買回彙總查核表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR150.cs:227` | `INFDR150_PO` | SP | `S_TA_NFDR150_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR151` | 買回申請書資料查核表／買回費用查核表／買回轉申購明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR151.cs:156-186` | `INFDR151_PO` | SP | `S_TA_NFDR151_GET_Charge`、`S_TA_NFDR151_GET`、`S_TA_NFDR151_GET_1`、`S_TA_NFDR151_GET_2`、`S_TA_NFDR151_GET_3`、`S_TA_NFDR151_GET_5`、`S_TA_NFDR151_GET_4` | **看不到(SP 黑箱)** | 4(全在版控+csproj) |
| `NFDR153` | 贖回沖銷明細表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR153.cs:100` | `Basic_PO` | SP | `s_NFDR153_Get` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR154` | 贖回交易確認單 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR154.cs:84` | `Basic_PO` | SP+inline | `s_NFDR154_Get` | `OFD081V` | 1(全在版控+csproj) |
| `NFDR155` | 買回暫不付款通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR155.cs:81` | `Basic_PO` | SP | `s_NFDR155_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR156` | 買回補件付款通知書 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR156.cs:36` | `Basic_PO` | SP | `s_NFDR156_Get` | **看不到(SP 黑箱)** | 1(全在版控+csproj) |
| `NFDR157` | 公司支付郵匯費明細／彙總表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR157.cs:196-200` | `INFDR157_PO` | SP | `S_TA_NFDR157_GET` | **看不到(SP 黑箱)** | 2(全在版控+csproj) |
| `NFDR158` | 贖回統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR158.cs:136` | `Basic_PO` | SP+inline | `s_NFDR158_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR159` | 轉申購統計月報表 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR159.cs:115` | `Basic_PO` | SP+inline | `s_NFDR159_Get`、`s_NFDR159_1_Get` | `OFD081V` | 2(全在版控+csproj) |
| `NFDR160` | 轉申購明細／彙總表（轉出＋轉入） | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR160.cs:94-112` | `INFDR160_PO` | SP | `s_TA_NFDR160_Get`、`s_TA_NFDR160_1_Get` | **看不到(SP 黑箱)** | 4(全在版控+csproj) |

## 4. 維護畫面(M)

**本模組無 M 畫面。**

原因:`NFD` 是純輸出層,不擁有任何業務表(§0.1、§2.1)。資料的新增 / 修改 / 刪除全部在 `ATLAS.OFD` 的 M 畫面完成,`NFD` 只負責把結果印出來。

這件事在程式上是可驗證的,不是推測:

| 證據 | 內容 |
|---|---|
| 沒有 `ATLAS.NFD` 主專案 | `Dev/` 下只有 `ATLAS.NFD.Report`,其他模組都是「主專案 + `.Report`」成對 |
| 127 支全部繼承 `xReportForm` | 例 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:21`;沒有一支是 `xMaintainForm` |
| Ctl 沒有四眼方法 | 每支 Ctl 只有 `GetXxxReportData` / `GetXxxReportObject`(+ 少數 `chkXxx`),沒有 `Verify` / `Approve` / `Reject`,例 `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:39-76` |
| PO 沒有繼承四眼基底 | 44 支的基底只有 `INFDRxxx_PO`(介面)或 `Basic_PO`,沒有 `Basic4EyesPO` / `BasicEVAPO` / `MultiRow4EyesPO` |

**這是 `NFD` 最大的特徵,也是讀這個模組時最容易誤判的地方**:看到 `NFDR073` 在 `INSERT` / `DELETE` `NFDR073T*`,不要以為它在維護業務資料——那些是為了印一份對帳單而生的中繼表,列印完就沒有意義(§2.4)。同理 `NFDR073B` 的 `S_TA_NFDR073B_EMAIL` 會寫寄信佇列,那是「輸出」的一部分,不是業務異動。

**維護時的推論**:任何「報表數字不對」的問題,`NFD` 這一層能做的只有三件事——條件傳錯、SP 拿錯、Transfer 漏搬。數字本身錯要回 `OFD` 或 SP 去找。

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因同 §4。不過報表畫面本身帶有**查詢性質的副作用**,讀的時候要當成查詢畫面看待:

| 支 | 查詢性質的副作用 | 錨點 |
|---|---|---|
| `NFDR001` | 畫面上有 `ugrdClass` 類別選擇 grid,由 `GetClassData` 另外取數 | `Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:69-74` |
| `NFDR076` / `NFDR077` | 列印前先打 `chkOFD303A` / `chkOFD221A` 查「這段日期日結了沒」,結果用彈窗問使用者要不要繼續 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:109-131` |
| `NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` | 有 `GetFUND` 取基金下拉清單 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:96-104` |
| `NFDR120` / `NFDR121` / `NFDR123` | 有「下載 Excel」路徑,等同把查詢結果落地 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:75-86` |

## 6. 批次(B)與 WindowsService

**本模組無 B 畫面,也沒有任何 WindowsService。**

但有兩支**在行為上等同批次**,不要因為它們掛在報表清單就當成「印一張紙」:

| 支 | 為什麼像批次 | 錨點 |
|---|---|---|
| `NFDR073A` | 在一個 transaction 內連續跑 5 支 SP(`S_TA_NFDR073_3_GET` / `_0_GET` / `_4_GET` / `_1_GET` / `_2_GET`)灌 17 張暫存表,再產文字檔並可加密壓縮。可選「郵寄」或「E-mail」兩條發送途徑 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:105-150`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:114` |
| `NFDR073B` | 「產生 Email 資料」按鈕跑 `S_TA_NFDR073B_EMAIL`,在 transaction 內寫寄信資料並回傳筆數 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160-190` |

兩支都由**人按按鈕觸發**,沒有排程。所以「這個月對帳單有沒有寄出去」這件事,系統裡沒有任何自動保證——漏按就是漏寄,而且**不會有任何告警**。

## 7. 報表(R)——主體

```text
[圖] NFDR073A 的完整資料流：畫面條件、前置檢核、五支 SP、十七張暫存表、四個模組的表、文字檔與加密壓縮輸出
圖中文字:NFDR073A 月／季對帳單文字檔：條件 → 取數 → 暫存表 → 輸出 / ① 畫面條件 / 淨值日期起迄／戶號／ID／月or季／發送途徑／路徑 / ② 前置檢核 / 路徑必填+Directory.Exists；註銷戶→阻擋 / ③ dataID / Substring(0,22) 截斷 → 併發會撞 / ④ 一個 transaction 內連跑 5 支 SP（全部在版控外，除 _1_GET） / S_TA_NFDR073_3_GET / SEND_TYPE 含 1（郵寄） / S_TA_NFDR073_0_GET / SEND_TYPE 含 2（E-mail）OUT striMSG / S_TA_NFDR073_4_GET / DATA_TYPE 非 1 時走這條 / S_TA_NFDR073_1_GET / **唯一在版控的 SP** / S_TA_NFDR073_2_GET / 最後一支 / ⑤ 灌進 17 張自建暫存表（以 DATAID 分租） / NFDR073T5–T12 / 持股／交易明細 / NFDR073T16–T19 / 彙總 / NFDR073T24 T29 T31 T33 T34 / 格式化後的列 / NFDR073T6 T7 / 與 NFDR073 共用 / ⑥ 再 SELECT 回來（此處才看得到別人的表） / OFD081A OFD081V OFD0811A / 基金名稱／小數位／警語 / OFD132A / — / BMS001A / 受益人 / FSK003 / 風險屬性 / ⑦ 輸出：沒有 .rpt / CreateTxtFiles.CreateNFDR073AText(...) / 文字檔寫到 utxtPath / IsSetZip = Y → 加密壓縮 / 密碼 NFDR073A_PASSWORD 存在 config / 失敗只說「產生檔案失敗」 / 五個字，無細節
```

*圖:圖 4 NFDR073A 資料流（§7.3.3）。這是本片最複雜也最危險的一支：橘虛框=已知風險（dataID 截斷、密碼存 config、錯誤訊息無細節）；黑框=版控外的 SP；灰虛框=別模組的表；橘框=本文重點。注意它沒有任何 .rpt——輸出是文字檔，不是 Crystal 報表。*

### 7.0 怎麼讀這一章

44 支共用同一套骨架(§1.3),所以本章只對**每群最具代表性的一支**、**兩對後綴**、以及**行為異常的那幾支**展開;其餘在 §3 的清冊已經帶過。每節固定四段:**做什麼 / 條件與卡控 / 取數 / 輸出**。

卡控結果一律五類:**阻擋**(不讓印)/ **警示**(印但跳訊息)/ **詢問**(Yes-No 再決定)/ **過濾(無提示)**(悄悄少印)/ **記錄不擋**。

### 7.1 第 001–007 群:受益人結構與法遵月報

七支的共同形狀:**單一 SP、參數走 `Utility.Parameters`、Crystal 出圖**。`NFDR001` 是其中唯一有 grid 與 inline SQL 的,拿它當代表。

#### 7.1.1 `NFDR001` 基金受益人名冊(本群最完整的一支)

**做什麼**:依截止日與申購日期區間,印出某檔基金的受益人名冊,可依不同排序與用途切換版面。

**條件**(全部從 `Utility.Parameters` 傳,無字串串接):

| 參數 | 來源控件 | 傳給 SP 的名字 | 錨點 |
|---|---|---|---|
| `BAL_DATE` | `udatBAL_DATE` | `datiBAL_DATE` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:66-70` |
| `ALLOT_DATE_ST` / `ALLOT_DATE_END` | `udatALLOT_DATE_ST` / `_END` | `datiALLOT_DATE_ST` / `_END` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:71-81` |
| `FUND_ID` | `custFUND_ID_0` | `striFUND_ID` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:83-87` |
| `Purpose` / `Class` / `Class_Code` / `BY_AGENT` | `uoptPurpose` / `uoptClass` / grid / `uoptBY_AGENT` | 同名加 `stri` 前綴 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:88-105` |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按預覽 | `DoValidate()` + `ValidateErrList.Show()` | 有必填未填 | **阻擋**(`e.Cancel = true`) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:75-80` |
| 按預覽 | `uoptOrder` 只認 `"0"`/`"1"`/`"2"`/`"3"`,`uoptPurpose` 只認 `"0"`/`"1"` | 值不在列舉內 | **過濾(無提示)**——整串 `if / else if` 掉出去,**`SetQueryParameters` 一次都沒呼叫**,報表類別是空的 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131` |
| `ReportLoad` | `Purpose` 參數只在 `Purpose=="1"` **且** `Order` 是 `"0"` 或 `"3"` 時才 `SetParameterValue` | 其他組合 | **過濾(無提示)**——Crystal 沿用上一次的值 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:64-68` |
| PO | `Cmd.CommandTimeout = 0` | SP 跑很久 | **記錄不擋**——無限等待 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56` |

**取數**:`s_TA_NFDR001_Get`(**版控外**)。另有一段 inline SQL 取 grid 的類別清單,讀 `CTL014` 與 `OFD017A`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:173`)。

**輸出**:8 種「排序 × 用途」組合對應 5 個 `.rpt`,對應關係**不是一對一**:

| `uoptOrder` | `uoptPurpose` | `.rpt` |
|---|---|---|
| `0` | `0` | `NFDR001RPS2` |
| `0` | `1` | `NFDR001RPS1` |
| `1` | `0` | `NFDR001RPS` |
| `1` | `1` | `NFDR001RPS3` |
| `2` | `0` | `NFDR001RPS` |
| `2` | `1` | `NFDR001RPS4` |
| `3` | `0` | `NFDR001RPS` |
| `3` | `1` | `NFDR001RPS1`(**與 Order=0/Purpose=1 同一張**) |

錨點 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131`。`NFDR001RPS` 被三種排序共用、`NFDR001RPS1` 被兩種共用——**改其中一張會同時影響多個選項組合**,這是本模組改 `.rpt` 最容易踩到的坑。

#### 7.1.2 其餘六支(表格帶過)

| 支 | SP | `.rpt` | 值得注意 |
|---|---|---|---|
| `NFDR002` 資金來源分析表 | `s_TA_NFDR002_Get` | 2 | PO 只有 104 行,純參數轉發 |
| `NFDR003` 股權分散表 | `s_TA_NFDR003_Get` | 1 | 法遵用 |
| `NFDR004` 員工及其關係人買賣本公司基金月報表 | `s_TA_NFDR004_Get` | 1 | 法遵用,PO 96 行 |
| `NFDR005` 基金受益憑證持有者統計表 | `s_TA_NFDR005_Get` | 1 | SP 名直接寫在 `GetStoredProcCommand("…")` 裡,不經變數 |
| `NFDR006` 債券型基金其他資訊揭露月報表 | `s_TA_NFDR006_Get` | 1 | 法遵用 |
| `NFDR007` 各基金餘額比例表 | `s_TA_NFDR007_Get` | 1 | — |

六支**都沒有任何「查無資料」提示**(§附錄 E-05)。SP 回空集合時,使用者看到的是一張只有表頭的 Crystal 報表,分不出「真的沒有」還是「條件打錯」。

### 7.2 第 021–024 群:受益人排行與異常清冊

三支,`NFDR022` 存在於專案內但**不在本片名單**(見 §7.6 跳號說明)。

| 支 | 中文名 | PO 基底 | SP | 特別的地方 |
|---|---|---|---|---|
| `NFDR021` | 受益人基金持有 / 申購 / 贖回單位數排行表、持有餘額排序一覽表 | `INFDR021_PO` | `s_TA_NFDR021_Get` | **一支 SP 服務四種報表名**,由 UI 選項決定標題與 `.rpt`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58`) |
| `NFDR023` | 受益人異動及定額異動重覆報表 | **`Basic_PO`** | `s_NFDR023_Get` | 未遷移,`m_db` 為 `null`(附錄 E-02) |
| `NFDR024` | 受益人統編異常清冊 | `INFDR024_PO` | `S_TA_NFDR024_GET` | SP 名全大寫,與同群 `s_NFDR023_Get` 的小寫風格不一致(§2.2) |

`NFDR021` 的四個報表名共用同一支 SP,代表**四種排行的差異全在 SP 裡的 `ORDER BY`**。想加第五種排行,要改的是版控外的 SP,repo 內只能改標題字串——**這種改動在 code review 時完全看不出風險**。

#### 7.2.1 `NFDR021` 一支 SP 四個報表名的實際寫法

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR021.cs:49-58` 四個 `SetQueryParameters` 分支:

| 報表名 | 意義 |
|---|---|
| 受益人基金持有單位數排行表 | 目前持有 |
| 受益人基金申購單位數的排行表 | 期間申購 |
| 受益人基金贖回單位數的排行表 | 期間贖回 |
| 受益人持有餘額排序一覽表 | 依金額排序 |

四者共用 `s_TA_NFDR021_Get`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR021_PO.cs:58`),差異全在 SP 內部。**repo 內看不到「排行」是怎麼排的、取前幾名、同名次怎麼處理**——這些全部在版控外。

`.rpt` 只有兩張(`NFDR021RPS`、`NFDR021RPS2`),四個報表名對兩張版型,又是一對多(附錄 E-16)。

#### 7.2.2 `NFDR024` 受益人統編異常清冊

唯一一支名字裡帶「異常」的報表。取數走 `S_TA_NFDR024_GET`(**版控外**,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR024_PO.cs:59`),PO 只有 97 行、純參數轉發。

**「統編異常」的判斷規則完全在 SP 裡**——身分證檢查碼?統編檢核碼?重複?repo 內一個字都查不到。這支是「法遵規則藏在版控外」的典型:規則變了(例如新式統編),改的是資料庫,程式碼的 git log 上什麼都看不到。

#### 7.2.3 `NFDR023` 受益人異動及定額異動重覆報表

本群唯一有欄位中文名的一支(`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR023Model.xsd`):

| 欄位 | 中文名 |
|---|---|
| `RCV_DATE` / `CHG_UPD_DTTM` / `CHG_EFFECT_DATE` | **三個欄位的 `Caption` 都是「異動生效日期」** |
| `DATA_TYPE` | 異動類別 |
| `ID_NO` | 受益人ID |
| `BF_NO` | 戶號 |
| `BF_NAME` | 受益人姓名 |
| `RSP_CHG_NO` | 重覆異動交易單號 |

**三個不同的日期欄位掛同一個中文名**,報表上並排出現時分不出誰是誰。`RCV_DATE`(受理日)、`CHG_UPD_DTTM`(異動寫入時間)、`CHG_EFFECT_DATE`(生效日)語意明顯不同,這是複製貼上 `Caption` 的結果。

這支同時是 `Basic_PO`(附錄 E-02),所以目前跑不起來——**中文名寫錯的問題還輪不到被發現**。

### 7.3 第 071–077 群:對帳單、確認書與公告(本模組的核心)

八支裡有五支是**直接寄給客戶的正式文件**,錯一個字就是客訴。本群也是全片唯一有 inline SQL 大量出現的地方。

#### 7.3.1 `NFDR073` 投資對帳單(本群最複雜,674 行 PO)

**做什麼**:產出受益人的投資對帳單,可單戶、可全戶。

**取數**:兩支 SP 二選一,判斷式在一行三元運算子裡:

```
cmd = string.IsNullOrEmpty(GetParamValue(model, "BF_NO")) && string.IsNullOrEmpty(GetParamValue(model, "ID_NO"))
    ? m_db.GetStoredProcCommand("s_NFDR073_1_Get") : m_db.GetStoredProcCommand("s_NFDR073_Get");
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97`

只有 `IsSelected == "0"` 或 `"1"` 兩個分支;**其他值時 `cmd` 保持 `null`,下一行 `cmd.CommandTimeout = 0` 直接 NRE**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:95-107`)。

**暫存表**:`NFDR073T0` / `T6` / `T7` 以 `dataID` / `SEND_NO` 分租,列印前先清:

```
DELETE FROM NFDR073T6 WHERE dataID = @dataID; DELETE FROM NFDR073T7 WHERE dataID = @dataID
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385`

**這段 SQL 是 MSSQL 語法**:`@dataID` 具名參數、一行兩個 statement 用 `;` 分隔。Oracle 兩者都不吃。同檔還有 `IF EXISTS(SELECT * FROM OCRMTMP WHERE SID = @SID) SELECT 1 ELSE SELECT 0`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:539`)——純 T-SQL。配合 `NFDR073_PO` 是 `Basic_PO`(`m_db` 未初始化)的事實,**這支的這幾條路徑目前跑不起來**(附錄 E-02)。

**輸出**:1 張 `.rpt`(`NFDR073RPS`),報表名寫成 `const string ReportName = "投資對帳單"`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073.cs:49`)——全片唯一用 `const` 的,其他支都是字面字串散在各分支。

#### 7.3.2 `NFDR073A` / `NFDR073B` 兩個後綴的成因(必答問題 4 之一)

先給結論表:

|  | `NFDR073` | `NFDR073A` | `NFDR073B` |
|---|---|---|---|
| 有沒有不帶後綴的版本 | **有**(就是它自己) | — | — |
| 中文名 | 投資對帳單 | 月 / 季對帳單(**文字檔**) | 貴賓理財對帳單 |
| 用哪些 SP | `s_NFDR073_Get` / `s_NFDR073_1_Get` / `s_NFDR073_ChkRdm` | **`S_TA_NFDR073_0_GET` ~ `_4_GET`** | **`S_TA_NFDR073B_GET`**、`S_TA_NFDR073B_EMAIL` |
| 輸出 | Crystal `.rpt` × 1 | **文字檔 + 可選 ZIP 加密**,無 `.rpt` | Crystal `.rpt` × 4 |
| PO 基底 | `Basic_PO`(未遷移) | `INFDR073A_PO`(Oracle) | `INFDR073B_PO`(Oracle) |
| PO 行數 | 674 | 651 | 347 |

**`A` 的成因**:`NFDR073A` 的 SP **叫 `S_TA_NFDR073_x_GET`,名字裡沒有 `A`**。也就是說 `A` 只存在於**畫面代號**,資料端仍屬 `NFDR073` 這一家。這對應前 24 篇的第 (d) 類——「`A` 是畫面代號的一部分、與表無關」(`ofdi1.md` 的 `OFDI075A` 查 `OFD304A` 是同一型)。**但成因不完全一樣**:`ofdi1.md` 那例是畫面代號與表代號各走各的;這裡是**同一份對帳單的第二個出口**(螢幕預覽 vs 文字檔批次產出),`A` 表示「同資料、不同交付方式」。這是前 24 篇沒出現過的第六種,本文記為 **(f) 同資料的第二個出口**。

**`B` 的成因**:`NFDR073B` 有自己的 `S_TA_NFDR073B_GET`、自己的 4 張 `.rpt`、自己的暫存表(`DB/Table/NFDR073BT1.sql`、`DB/Table/NFDR073BT2.sql`),報表名也不同(貴賓理財對帳單)。這是標準的第 (c) 類——**同概念的第二份產物**,和 `ofd123.md` 的 `OFD017B` 同型。

**不是境內外(第 (a) 類)**:本組三支都沒有出現 `FUND_TYPE = '1'/'2'` 或 `SHORE_ID` 的分流;`NFDR073A` 的分流參數是 `RPT_TYPE`(月 / 季)與 `SEND_TYPE`(郵寄 / E-mail),不是境內外。**不是 MSSQL→Oracle 改名(第 (b) 類)**:三支同時存在且互不重複。

#### 7.3.3 `NFDR073A` 為什麼是全片最危險的一支

| 風險 | 說明 | 錨點 |
|---|---|---|
| `dataID` 截斷到 22 碼 | `strDATAID.Substring(0, 22).Trim()`。暫存表以 `dataID` 分租,**兩人同時跑且前 22 碼相同時,兩份對帳單的資料會互相污染** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102` |
| 長度沒防呆 | `Substring(0, 22)` 在 `strDATAID` 短於 22 時直接丟 `ArgumentOutOfRangeException` | 同上 |
| 五支 SP 在同一個 transaction | 任一支失敗整批 rollback,但 UI 只顯示「產生檔案失敗」五個字 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:120` |
| 密碼來自 config | `NFDR073A_PASSWORD` 從 `GetConfigSetting` 讀,明文存在設定檔〔客戶特定〕 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:25` |
| 存檔路徑可自由輸入 | `utxtPath` 只檢查 `Directory.Exists`,沒有白名單;對帳單是個資 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:60-67` |
| 註銷戶檢核 | 訊息「此 受益人 為註銷戶!」——**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073A.cs:185,196` |
| `NVL(REJ_POST,' ')<>'Y'` | 這一條寫得**對**:用 `NVL` 包起來,NULL 不會被三值邏輯吃掉。同檔的 `BF_SORT_CD <> '012'` **沒包**,`BF_SORT_CD` 為 NULL 的受益人會被靜默排除 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195,425` |

#### 7.3.4 `NFDR076` / `NFDR077` 申購與買回轉申購交易確認書

這兩支是**全片卡控最完整的一對**,也是唯一會在列印前主動檢查「日結了沒」的。

**`NFDR076` 的卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按預覽 | `DoValidate()` | 必填未填 | **阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:179` 前的驗證區 |
| 按預覽 | `chkOFD303A`——查 `OFD303A` 在日期區間內有沒有 `POST_CTL_CODE = 'N'`(未過帳)的資料 | 有未日結 | **詢問**(`Info03` Yes/No,按 No 就 `e.Cancel`) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:109-117` |
| 按預覽 | `chkOFD221A` | 檢核不過 | **警示**;但若勾了 `uchkData` 則升級為**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs:121-133` |
| 取數後 | `無符合查詢條件的資料` 訊息 | 零筆 | **警示** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR076.cs`(訊息字串,2 處) |

**`chkOFD303A` 的 SQL 有三個要注意的地方**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:141-158`):

1. **`JOIN` 是 INNER**:`FROM OFD303A JOIN OFD0811A ON OFD303A.FUND_ID = OFD0811A.FUND_ID`。`OFD0811A` 沒有對應基金的交易,**這筆未日結資料就查不到,檢核直接放行**——這是「`INNER JOIN` 讓對不到的資料無聲消失」在檢核上的變形,比在報表上更危險(報表少印看得出來,檢核漏掉看不出來)。

2. **`INV_AREA <> 'D'` 判海外**:`INV_AREA` 為 NULL 時整條是 UNKNOWN,該基金被靜默排除。同一段的 `INV_AREA = 'D'`(判境內)沒有這個問題。

3. **`OR (:striFUND_ID IS NOT NULL AND :striFUND_ID = :striFUND_ID)`**:恆真條件。使用者一旦指定了基金代碼,**整段「基金類型」篩選就全部失效**。看起來像是刻意寫的「指定基金時不看類型」,但寫成恆真式而不是註解說明,下一個維護者很容易當成 bug 刪掉。

**`NFDR077` 與 `NFDR076` 的差異**(必答問題 3 的「最相似的一組」):

|  | `NFDR076` | `NFDR077` |
|---|---|---|
| 報表名 | 申購交易確認書 / (郵簡) / (彙總) | 買回轉申購交易確認書 / (郵簡) / 申購交易確認書(彙總) |
| SP | `S_TA_NFDR076_GET` | `S_TA_NFDR077_GET` |
| 讀的表 | `OFD303A` `OFD0811A` `OFD221A` `BMS001A` | `OFD303A` `OFD0811A` `OFD081A` `OFD251A` `BMS001A` `MYOFD303A` |
| `.rpt` | 5 | 3 |
| 日結檢核 | `chkOFD303A` + `chkOFD221A` | 檢 `OFD251A.REDEM_PROC_CODE<>'3'` 與 `A.REDEM_CTL_CODE <> '4'` |
| PO 行數 | 316 | 428 |

**兩支共用同一段「基金類型」條件**——連 `NOT IN ('7A','7B')` 排除兩檔基金的寫死值都一字不差(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:148-150` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:175-177`)。**這是「成對報表只改一邊」的完美溫床**:業務要調整基金分類時,兩支要一起改,而且 `NFDR076` 自己內部還有兩份複本(`:148` 和 `:238`)、`NFDR077` 也有兩份(`:175` 和 `:352`)——**一次改動要同步四個地方**。

`'7A'` / `'7B'` 是〔客戶特定〕的基金代碼,註解只寫「股票型(海外),排除 7A 及 7B」,沒說為什麼。

#### 7.3.5 本群其餘三支

| 支 | 中文名 | PO 基底 | SP | 注意 |
|---|---|---|---|---|
| `NFDR071` | 法人公告警示表 | **`Basic_PO`** | `s_NFDR071_Get` | 未遷移 |
| `NFDR072` | 法人買回公告明細表 / 法人贖回公告明細表 | **`Basic_PO`** | `s_NFDR072_Get` | 未遷移;同一支 SP 兩個報表名,「買回」與「贖回」在本系統是同義詞 |
| `NFDR075` | 傳真委託申購 / 傳真委扣－扣款失敗通知書 | `INFDR075_PO` | `s_TA_NFDR075_Get` | 已遷移;兩個名字差在「委託申購」vs「委扣」 |

`NFDR073B` 的細節:

| 項目 | 內容 | 錨點 |
|---|---|---|
| 報表名 | 「貴 賓 理 財 對 帳 單」(**字間有全形空白**,四處硬寫,改一處會不一致) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123,134,145,157` |
| 零筆訊息 | `【{報表名}{子名}】無符合查詢條件的資料。`——**警示** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:232` |
| Email 產生 | `S_TA_NFDR073B_EMAIL`,`OUT R_CNT` 回筆數,`> 0` 才算成功 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160-190` |
| `catch (OracleException) { … tran.Rollback(); }` | **`tran` 若在 `BeginTransaction` 之前就拋例外,這裡會 NRE,把真正的錯誤蓋掉** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:193-199` |
| 讀的表 | `OFD002`、`COD009`、`SAL051`、`DUAL` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:258,323` |

### 7.4 第 101–123 群:申購側(16 支,本片最大的一群)

這一群是「錢進來之後」的所有輸出:扣款、手續費、印花稅、統計月報、KYC 名單。也是 `Basic_PO` 未遷移比例最高的一群(16 支裡 6 支)。

#### 7.4.1 群內分工

| 子題 | 支 | 共同點 |
|---|---|---|
| 指定扣款 / 傳真委扣 | `NFDR101` `NFDR102` `NFDR103` | 三支是**同一份資料的彙總 / 明細 / 失敗明細**,各自有「指定扣款」與「傳真委扣」兩個報表名 |
| 交易確認與明細 | `NFDR104` `NFDR105` | `NFDR104` 申購明細表(PO 326 行,本群最長);`NFDR105` 申購交易確認單 |
| 手續費 / 扣帳費 | `NFDR107A` `NFDR107B` `NFDR111` | 見 §7.4.3 |
| 銷售統計 | `NFDR108` `NFDR109` `NFDR115` | `NFDR108` 公司人員銷售彙總、`NFDR109` 銷售彙總查核、`NFDR115` 申購統計月報 |
| 稅 | `NFDR114` | 印花稅明細 / 彙總 |
| 通路明細(可下載) | `NFDR120` `NFDR121` | 代銷銀行 / 券商;兩支都有「列印」與「下載 Excel」雙路徑 |
| 成本與 KYC | `NFDR122` `NFDR123` | `NFDR122` 月平均成本餘額;`NFDR123` KYC 到期名單(純 Excel) |

#### 7.4.2 `NFDR123` 受益人 KYC 到期名單(本群最完整的一支,也是全片唯一純 Oracle CTE)

**做什麼**:列出到某個基準日為止、KYC 快到期或已到期、而且仍有持股的受益人,輸出成 Excel 給業務去催。

**取數**:全片唯一**沒有 SP** 的一支。整段 SQL 是一個 100 行的 Oracle `WITH` 查詢,直接寫在 PO 裡(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:60-93`)。四個 CTE:

| CTE | 讀什麼 | 作用 |
|---|---|---|
| `OFD123A_TMP` | `OFD123A` | KYC 主檔篩選 |
| `OFD306_TMP` | `OFD306A` + `TABLE(F_TA_GETFUNDNAV(...))` | 以 `HAVING SUM(CHG_UNIT) > 0` 只留**還有持股**的人 |
| `OFD221A_TMP` | `OFD221A` | 取每人**最後一筆申購**(`MAX(ALLOT_DATE |
| 主查詢 | `BMS001A` `COD009` | 受益人基本資料與員工姓名 |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 主查詢 | `JOIN BMS001A ON T1.BF_NO = BMS001A.BF_NO`(**INNER**) | 受益人主檔缺這筆 | **過濾(無提示)** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:87` |
| 主查詢 | `JOIN OFD306_TMP T2`(**INNER**) | 目前沒有持股 | **過濾(無提示)**——設計如此 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:88` |
| 主查詢 | `JOIN OFD221A_TMP T3`(**INNER**) | **從來沒有申購紀錄** | **過濾(無提示)**——⚠ 這條不見得是刻意的 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:89` |
| 主查詢 | `LEFT JOIN COD009` | 業務員代碼查不到姓名 | 保留該列,姓名為空(`NVL(..., ' ')`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:90` |
| 主查詢 | `NVL(TRIM(BMS001A.FREEZE_CD),'N') = 'N'` | 凍結戶 | **過濾(無提示)**——但 NULL 處理正確 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:92` |
| 輸出 | `saveFileDialog1.FileName = "受益人KYC到期名單.xlsx"` | 永遠 | 檔名寫死,不帶日期 / 條件 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` |

**第三條是本片最會咬人的一處**:KYC 到期名單是**法遵用途**,少列一個人代表少催一個人。一位受益人如果持股是**轉申購轉進來的**(記在 `OFD306A`,不是 `OFD221A`),`JOIN OFD221A_TMP` 就對不到,他會從名單上**無聲消失**。畫面不會有任何提示,Excel 也不會少一行紅字——只是少一行。

`NFDR123` 的 NULL 處理本身寫得很好(`NVL` 用了 8 次),這反而說明作者知道 NULL 的問題;`INNER JOIN` 的取捨是**取數設計**的問題,不是疏忽型 bug——但效果一樣。

#### 7.4.3 `NFDR107A` / `NFDR107B` 兩個後綴的成因(必答問題 4 之二)

|  | `NFDR107A` | `NFDR107B` |
|---|---|---|
| 有沒有 `NFDR107` | **沒有**。`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/` 與 `PO/ReportPO.NFD/` 都查無 `NFDR107` | 同左 |
| 中文名 | 各代理扣款機構**扣帳費**合計表 / 扣帳費用明細 / 銀行單筆扣款彙總表 | 各代理扣款機構 / 各銷售機構各基金**手續費**合計表 / 明細表 / 通知函 |
| SP | `s_TA_NFDR107A_Get` | `s_NFDR107B_Get`、`s_NFDR107B_T2_Get` |
| PO 基底 | `INFDR107A_PO`(Oracle,已遷移) | **`Basic_PO`**(未遷移) |
| 參數風格 | Oracle bind `:start` / `:end` | MSSQL `@datiALLOT_DATE_ST` 等 17 個 |
| 讀的表 | `OFD303A` | `OFD303A`、`CTL018` |
| `.rpt` | `NFDR107ARPS1` ~ `RPS3` | `NFDR107BRPS1` ~ `RPS3` |
| 檔案編碼 | **cp950** | **cp950** |

**結論:這一對屬於前述五種成因的第 (e) 類「族名」**——`A` 與 `B` 是同一個編號底下的兩個**業務主題**(扣帳費 vs 手續費),沒有不帶後綴的基準版,兩者資料來源與 SP 各自獨立,不是境內外、不是遷移改名、不是同概念的第二張表。

**但有一個前 24 篇沒記錄過的佐證**:兩支的 `.rpt` 都**從 `RPS1` 起算,沒有 `RPS`**(對照 `NFDR001` 是 `RPS` / `RPS1` / … / `RPS4`)。這暗示原本存在一個 `NFDR107` + `NFDR107RPS`,後來被拆成 A / B 兩支而基準版被刪掉。**這是推測,repo 內沒有 `NFDR107` 的任何殘跡可佐證**——連 `.rpt` 都沒有 `NFDR107RPS.rpt`。

**維護上要注意的是兩支的落差**:`NFDR107A` 已經遷到 Oracle、用 bind 變數;`NFDR107B` 停在 MSSQL 且 `m_db` 未初始化。**它們在選單上看起來是一對,實際上一支能跑一支不能**。

`NFDR107A` 還有一處:日結檢核 `check()` 在例外時 `return -1`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:186`)。`-1` 不是「0 筆未日結」也不是「有未日結」,呼叫端如果用 `> 0` 判斷,**查詢失敗會被當成「都日結了」放行**——fail-open。

#### 7.4.4 `NFDR114` 印花稅:一段跑不起來的 SQL

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:136-140` 把字串這樣接起來:

```
"SELECT COUNT(*) AS CNT FROM OFD303A "
+ " WHERE CTL_DATE >= @ALLOT_DATE_ST AND CTL_DATE <= @ALLOT_DATE_END"
+ "   AND ALLOT_CTL_CODE <> '3' "
+ "   AND FUND_ID IN (SELECT * FROM dbo.f_FormatStringToTable(@FUND_ID))"
+ "GROUP BY FUND_ID"
```

三個問題疊在一起:

1. **最後一段少一個空白**,接出來是 `…f_FormatStringToTable(@FUND_ID))GROUP BY FUND_ID`,任何資料庫都是語法錯誤。

2. **`dbo.f_FormatStringToTable` 是 MSSQL 的 table-valued function**,Oracle 沒有 `dbo` schema 也沒有這支;`@` 具名參數同理。

3. **`GROUP BY` + `ExecuteScalar`**:就算文法對了,`ExecuteScalar` 只取第一列第一欄,拿到的是**第一檔基金的筆數**,不是總筆數。

再加上 `NFDR114_PO` 是 `Basic_PO`、`m_db` 未初始化(附錄 E-02),這段實際上執行不到就先 NRE 了。**三重失效互相掩蓋,是這個模組最典型的樣子**:錯誤沒被發現,是因為程式根本沒跑到。

#### 7.4.5 `NFDR105` 申購交易確認單:字串串接進 SQL

```
strWhereCode += " AND [OFD006]." + Row.Name + " = " + "'" + Row.Value + "'";
…
strWhereCode += " AND [OFD006]." + Row.Name + " Like " + "'" + Row.Value + "%'";
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180,185`

**欄位名與值都是直接串進去的**,值連跳脫都沒有。`Row.Name` 來自 `Utility.Parameters`,由 UI 填;`Row.Value` 同理。這是本片唯一一處把使用者可控字串直接拼進 SQL 的地方(`ofdi1.md` 的 `OFDI481_PO.cs:142` 是同型)。

`[OFD006]` 用的是 MSSQL 的中括號識別字,這支同樣是 `Basic_PO`。所以現況是「有洞但打不開」——**遷移這支時必須先修這段,不能照抄**。

#### 7.4.6 本群其餘支(表格帶過)

| 支 | PO 基底 | SP | 值得一提 |
|---|---|---|---|
| `NFDR101` | `INFDR101_PO` | `S_TA_NFDR101_GET` | 另有 inline SQL 讀 `CTL018` 取代碼 |
| `NFDR102` | `INFDR102_PO` | `S_TA_NFDR102_GET` | 純轉發 |
| `NFDR103` | **`Basic_PO`** | `s_NFDR103_Get` | 未遷移 |
| `NFDR104` | `INFDR104_PO` | `s_TA_NFDR104_Get` | PO 326 行,本群最長;`DB/Table/Alter_NFDR104_T0.sql` 顯示它有自己的暫存表 `NFDR104_T0` |
| `NFDR108` | **`Basic_PO`** | `s_NFDR108_Get` | 未遷移 + **cp950 編碼**(Ctl / Pxy / PO 三層都是) |
| `NFDR109` | `INFDR109_PO` | `S_TA_NFDR109_GET` | — |
| `NFDR111` | `INFDR111_PO` | `S_TA_NFDR111_GET` | 一支 SP 兩個報表名(手續費彙總 / 基金手續費彙總) |
| `NFDR115` | **`Basic_PO`** | `s_NFDR115_Get` | 未遷移;`GetFUND` 的 inline SQL 讀 `OFD081V` + `[OFD038]`,**MSSQL 中括號** |
| `NFDR120` | `INFDR120_PO` | `S_TA_NFDR120_GET` | 「下載」選項另走 Excel |
| `NFDR121` | `INFDR121_PO` | `S_TA_NFDR121_GET_1` / `_2` | 兩支 SP 分別對應單筆 / 定額 |
| `NFDR122` | `INFDR122_PO` | `S_TA_NFDR122_GET` | UI 內有 `ReportName` 欄位的工作佇列結構,**一次可連印多張**(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR122.cs:130-185`) |

### 7.5 第 150–160 群:買回 / 贖回 / 轉申購側(10 支)

對稱於 §7.4,這一群是「錢出去」的輸出。`Basic_PO` 比例最高:10 支裡 **7 支**(`NFDR153` `NFDR154` `NFDR155` `NFDR156` `NFDR158` `NFDR159`,加上群外相依的),只有 `NFDR150` `NFDR151` `NFDR157` `NFDR160` 已遷移。

#### 7.5.1 `NFDR151` 買回申請書資料查核表(本群最完整的一支)

**做什麼**:一支畫面產四種 Crystal 報表 + 兩種 Excel 附表,共六種輸出。

**取數分派**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:68-122`):

| 觸發 | 值 | SP | 結果集 |
|---|---|---|---|
| Crystal | `NFDR151RPS` | `S_TA_NFDR151_GET` | `NFDR151` + `NFDR151_CER` |
| Crystal | `NFDR151RPS1` | `S_TA_NFDR151_GET_1` | `NFDR151_1` |
| Crystal | `NFDR151RPS2` | `S_TA_NFDR151_GET_2` | `NFDR151_2` |
| Crystal | `NFDR151RPS3` | `S_TA_NFDR151_GET_3` | `NFDR151_3` |
| Excel | `EXCEL01` | `S_TA_NFDR151_GET_5` | `NFDR151_5` |
| Excel | `EXCEL02` | `S_TA_NFDR151_GET_4` | `NFDR151_4` |
| 加選 | `IsPrintOffsetData == "Y"` | `S_TA_NFDR151_GET_Charge` | `NFDR151_Charge` |

**卡控總表**:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| PO 分派 | `reportClass` 不在四個值內 | 打錯 / 新增報表忘了加分支 | **阻擋**(`throw new Exception("未知的報表格式。")`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:98` |
| PO 分派 | `excelClass` 不是 `EXCEL01` / `EXCEL02` | 同上 | **過濾(無提示)**——`switch` 沒有 `default`,`proc` 保持空字串後續才爆 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:105-118` |
| 取數後 | `i > 0` | 零筆 | **記錄不擋**——`AddResultRow(false, 0, "")`,**訊息是空字串** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:165-170` |
| 例外 | `catch (Exception)` | 任何錯 | **記錄不擋**——`AddResultRow(false, 0, string.Empty)` 後交給 `CommonExceptionBlocker` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:197-201` |

**同一支 PO 裡兩種分派風格並存**:Crystal 用 `if / else if` + `throw`(嚴),Excel 用 `switch` 無 `default`(鬆)。**加第三種 Excel 附表時,忘了加 `case` 不會有任何錯誤訊息**。

#### 7.5.2 `NFDR159` 轉申購統計月報表:唯一寫死境內外的一支

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:107` 的基金清單查詢最後一行:

```
strSQL += "    AND SHORE_ID = '2'" + Environment.NewLine;
```

`'2'` 在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:296` 定義為 `SHORE_ID.OnShore` = **境內基金**。

這一行是**本文 §0.1「`NFD` 是境內基金報表模組」最直接的程式證據**——不是從表名推的,是寫死在條件裡的。同樣寫法也出現在不屬於本片的 `NFDR113`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR113_PO.cs:119`)。

三個問題:

| 問題 | 說明 |
|---|---|
| 寫死常數 | 已經有 `CTL014.SHORE_ID.OnShore` 可用,這裡寫字面 `'2'` |
| 只有兩支這樣寫 | 其餘 42 支沒有這條,代表**境內限定是靠 SP 保證的**,repo 內看不到 |
| 與 `[OFD038]` 中括號共存 | 同一段還是 MSSQL 語法(§7.5.3) |

#### 7.5.3 `NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` 四支複製貼上的 `GetFUND`

四支的基金清單查詢幾乎一字不差:

| 支 | 錨點 | 差異 |
|---|---|---|
| `NFDR115` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:96-104` | 多 `AND OFD081V.FUND_ID <> 'ALL FUNDS'` |
| `NFDR154` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:100-106` | 沒有 `<> 'ALL FUNDS'`;參數叫 `@FUND_GRPCD` 不是 `@FUND_GROUP` |
| `NFDR158` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR158_PO.cs:96-104` | 與 `NFDR115` 同 |
| `NFDR159` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:100-108` | 多 `AND SHORE_ID = '2'`,沒有 `<> 'ALL FUNDS'` |

**同一個下拉清單,四支看到的基金不一樣**——`NFDR115` / `NFDR158` 會排除代碼為 `'ALL FUNDS'` 的那筆,另外兩支不會;`NFDR159` 只給境內。這不是刻意設計,是四份複本各自演化的結果。

四支還共同踩到 `AND` / `OR` 括號問題:`NFDR154` 的 `WHERE (@FUNDCODE = '0') OR (…) OR (…)` **整段沒有外層括號**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:103-105`),而 `NFDR115` / `NFDR158` / `NFDR159` 有(`WHERE ((@FUNDCODE = '0') … ))`)。`NFDR154` 後面沒有再接 `AND`,所以目前不會出事——**但只要有人加一條 `AND`,`NFDR154` 的行為會和另外三支不同**。

#### 7.5.4 本群其餘支(表格帶過)

| 支 | 中文名 | PO 基底 | SP | 值得一提 |
|---|---|---|---|---|
| `NFDR150` | 買回彙總查核表 | `INFDR150_PO` | `S_TA_NFDR150_GET` | 純轉發 |
| `NFDR153` | 贖回沖銷明細表 | **`Basic_PO`** | `s_NFDR153_Get` | 未遷移 |
| `NFDR154` | 贖回交易確認單 | **`Basic_PO`** | `s_NFDR154_Get` | 未遷移;另有 inline 讀 `[OFD126].ST_CD = '03'` |
| `NFDR155` | 買回暫不付款通知書 | **`Basic_PO`** | `s_NFDR155_Get` | 未遷移 |
| `NFDR156` | 買回補件付款通知書 | **`Basic_PO`** | `s_NFDR156_Get` | 未遷移;與 `NFDR155` 是一對(暫不付款 / 補件付款) |
| `NFDR157` | 公司支付郵匯費明細 / 彙總表 | `INFDR157_PO` | `S_TA_NFDR157_GET` | 用 `DataTable.Select("REDEM_PROC_CODE<>'3'")` 在**記憶體裡**再過濾一次,`REDEM_PROC_CODE` 為 `null` 的列會被濾掉(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:88`) |
| `NFDR158` | 贖回統計月報表 | **`Basic_PO`** | `s_NFDR158_Get` | 未遷移 |
| `NFDR160` | 轉申購明細 / 彙總表(轉出 + 轉入) | `INFDR160_PO` | `s_TA_NFDR160_Get`、`s_TA_NFDR160_1_Get` | 四張 `.rpt` 對應「明細 / 彙總」×「轉出 / 轉入」,分派在 UI(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR160.cs:94-112`) |

### 7.6 跳號:`NFDR106` / `NFDR110` / `NFDR152` 到哪去了(必答問題 3 的附帶)

本片名單有三個明顯的跳號。**三支都存在,只是不在本片的 44 支裡**:

| 代號 | 在不在 repo | 六層 | `.rpt` | 判定 |
|---|---|---|---|---|
| `NFDR106` | **在** | UI / Ctl / Pxy / PO / Model / View 齊全 | `NFDR106RPS.rpt` 在 | 由別篇涵蓋,**不是缺陷** |
| `NFDR110` | **在** | 齊全 | `NFDR110RPS.rpt` 在 | 同上 |
| `NFDR152` | **在** | 齊全 | `NFDR152RPS2.rpt` / `NFDR152RPS4.rpt` 在 | 同上 |

同理,名單外還有 `NFDR022`(有 3 張 `.rpt`)、`NFDR074`(有 `NFDR074p0` 子視窗)、`NFDR113`(有 `SHORE_ID = '2'`)也都在專案裡。**本片的 44 支是切片,不是「存在的全部」**;寫任何「缺 XXX」之前先 `ls` 一次。

`NFDR152` 的 `.rpt` 只有 `RPS2` 與 `RPS4`,沒有 `RPS1` / `RPS3` — 這種「編號有洞」的情形在 `NFDR107A` 也出現過(§7.4.3),可能是報表格式被砍過。**不在本片範圍,只記一筆待查。**

## 8. 跨模組共用(本片最重的一節)

```text
[圖] NFD 的跨模組依賴：單向只讀、影響面最大的四張表、三種最危險的改動，以及分析為何天生不完整
圖中文字:① 依賴方向：單向，而且只有讀 / ATLAS.OFD（境內分戶軌） / M／I／B 畫面 + 表 / ATLAS.NFD.Report / 127 支全 R，無主專案 / ATLAS.OFD.Report / 40 支（另一篇） / 沒有反向箭頭 / NFD 不被任何人依賴 / ② 改哪些表要回歸 NFD（依受影響支數排序） / OFD303A → 5 支 / 含 4 支日結檢核，不在報表清單上 / OFD081V → 5 支 / view，改底層表查不到誰在用 / BMS001A → 4 支 / 對外文件全靠它 / OFD0811A → 3 支 / INV_AREA 決定境內／海外 / ③ 最危險的三種改動 / INV_AREA 加第三種值或允許 NULL / NFDR076/077 的「海外」組靜默少基金 / OFD221A 改 PK／ALLOT_NO 長度 / NFDR123 取錯「最後一筆申購」，帶錯業務員 / SP 回傳欄位少一欄 / Model.xsd 與 Ctl 的 TransferTable 沒同步 → 該欄永遠空白 / ④ 影響面分析天生不完整 / 15 支可見 / 表名寫在 PO 的 inline SQL 裡 / 29 支不可見 / SQL 在版控外的 SP，repo 內補不完 / 結論：改 OFD 表要另外撈 SP 原始碼 / 否則上線才在報表上爆
```

*圖:圖 5 跨模組依賴（§8）。橘虛框=改動後會靜默出錯的地方；灰虛框=別模組；黑框=查不到的黑箱；橘框=本文結論。「NFD 不被任何人依賴」是好消息；「NFD 依賴所有人而且一半查不到」是壞消息。*

### 8.1 `NFD` 對外的依賴是單向的

`NFD` **只讀不寫**別的模組的表。本片 44 支沒有任何一行 `INSERT` / `UPDATE` / `DELETE` 打在別人的表上——寫入只發生在自己的 `NFDR073T*` 暫存表與 `OCRMTMP`(§2.4)。

| 方向 | 有沒有 | 證據 |
|---|---|---|
| `NFD` → 別模組的表(讀) | **有,而且是全部** | §2.1 的 42 張表 |
| `NFD` → 別模組的表(寫) | **沒有** | PO 內 `INSERT` / `UPDATE` / `DELETE` 的對象只有 `NFDR073T*` / `OCRMTMP` |
| 別模組 → `NFD` 的表 | **沒有** | `NFD` 沒有業務表可被讀 |
| `NFD` → 別模組的程式 | **沒有** | 各層 csproj 的 `ProjectReference` 只指向 `Common/Source/*` 與自己的六層 |

**所以「改 `NFD` 會不會影響別人」的答案是:不會。** 反過來「改別人會不會影響 `NFD`」的答案是:**幾乎一定會,而且看不出來**。

### 8.2 改哪些表要回歸 `NFD`

按「本片有幾支會受影響」排序:

| 表 | 歸屬 | 改它要重測 | 為什麼容易漏 |
|---|---|---|---|
| `OFD303A` | OFD | `NFDR076` `NFDR077` `NFDR107A` `NFDR107B` `NFDR114` | 四支是日結檢核,不是報表本體,不在「報表清單」上 |
| `OFD081V` | OFD(view) | `NFDR073A` `NFDR115` `NFDR154` `NFDR158` `NFDR159` | 它是 **view**,改底層表時 view 定義不在版控,查不到誰在用 |
| `BMS001A` | BMS | `NFDR073A` `NFDR076` `NFDR077` `NFDR123` | 受益人主檔,幾乎所有對外文件都靠它 |
| `OFD0811A` | OFD | `NFDR073A` `NFDR076` `NFDR077` | 基金屬性(`INV_AREA` / `PROF_TYPE2` / `HIGH_RISK_CD`),決定「算不算海外」 |
| `CTL018` / `CTL014` | CTL | `NFDR073` `NFDR101` `NFDR107B` / `NFDR001` | 代碼表,改代碼值會讓報表分類錯而不報錯 |
| `OFD221A` | OFD | `NFDR076` `NFDR123` | 申購檔 |
| `COD009` | COD | `NFDR073B` `NFDR123` | 員工資料,只用來帶姓名 |
| `OFD081A` `OFD002` `OFD017A` `OFD123A` `OFD126` `OFD132A` `OFD251A` `OFD306A` | OFD | 各 1 支 | — |
| `FSK003` | FSK | `NFDR073A` | 風險屬性,對帳單上的警語靠它 |
| `SAL051` | SAL | `NFDR073B` | — |

**以上只涵蓋 15 支**。另外 29 支的相依性在版控外的 SP 裡(§2.1.2),**這份影響面清單天生不完整,而且沒有辦法從 repo 補完**。

### 8.3 最危險的跨模組情境

| 情境 | 後果 | 為什麼沒人會發現 |
|---|---|---|
| `OFD0811A.INV_AREA` 新增第三種值(現在只有 `'D'` / 非 `'D'`) | `NFDR076` / `NFDR077` 的「海外」判斷 `INV_AREA <> 'D'` 會把新值也算成海外 | 確認書照印,數字看起來合理 |
| `OFD0811A.INV_AREA` 允許 NULL | `INV_AREA <> 'D'` 變 UNKNOWN,該基金從海外組**消失** | 同上 |
| 新增基金代碼但忘了同步 `'7A'` / `'7B'` 的排除清單 | `NFDR076` / `NFDR077` 共四處寫死值,改一處漏三處 | 只有比對兩份報表總數才看得出來 |
| `OFD221A` 改 PK 或 `ALLOT_NO` 長度 | `NFDR123` 的 `MAX(ALLOT_DATE \|\| ALLOT_NO)` 排序邏輯失準,取到錯的「最後一筆申購」 | 通路 / 業務員欄位帶錯人,但名單筆數不變 |
| `BMS001A.FREEZE_CD` 語意改變 | `NFDR123` 的 KYC 名單範圍跟著變 | 法遵名單少人 |
| 任何 `OFD*` 表加欄位 | 對 `NFD` **沒影響**(它只 `SELECT` 指名欄位),但若同時改了 SP 的回傳欄位,`Model.xsd` 與 Ctl 的 `TransferTable` 要一起改 | 多回的欄位不會報錯,**少回的欄位會讓報表該欄空白** |

### 8.4 `NFD` 與 `OFD` 兩套報表專案的分工(必答問題 1 的收尾)

| 判準 | 結論 | 依據 |
|---|---|---|
| 是不是第四條業務軌 | **不是**。沒有自己的表、沒有 M/I/B、沒有主專案 | §0.1、§4 |
| 是什麼 | **境內基金軌(`OFD`)的對外文件與法遵 / 營運報表產生器** | `SHORE_ID = '2'`(§7.5.2)、42 張表全屬 `OFD` 與共用模組(§2.1) |
| 為什麼不併進 `ATLAS.OFD.Report` | **repo 內沒有答案。** 可觀察到的差異只有「支數 127 vs 40」與「對外文件 vs 作業清單」 | §0.2,標〔假設〕 |
| 切分維度 | **讀者**(受益人 / 主管機關 / 通路 vs 內部作業),不是業務軌 | 報表中文名,§0.1 |

## 附錄 A. 資料表總表(僅限 PO 內看得見的)

29 支的表名在版控外的 SP 裡,看不到(§2.1.2)。以下 42 個名稱全部來自 15 支 PO 的 inline SQL。

| 名稱 | 歸屬 | 型態 | 被本片幾支用 | 用它的報表 |
|---|---|---|---|---|
| `OFD081V` | OFD | View(推測,尾碼 V) | 5 | `NFDR073A`、`NFDR115`、`NFDR154`、`NFDR158`、`NFDR159` |
| `OFD303A` | OFD | 表 | 5 | `NFDR076`、`NFDR077`、`NFDR107A`、`NFDR107B`、`NFDR114` |
| `BMS001A` | BMS | 表 | 4 | `NFDR073A`、`NFDR076`、`NFDR077`、`NFDR123` |
| `CTL018` | CTL | 表 | 3 | `NFDR073`、`NFDR101`、`NFDR107B` |
| `OFD0811A` | OFD | 表 | 3 | `NFDR073A`、`NFDR076`、`NFDR077` |
| `COD009` | COD | 表 | 2 | `NFDR073B`、`NFDR123` |
| `NFDR073T6` | **NFD 自建** | 暫存 | 2 | `NFDR073`、`NFDR073A` |
| `NFDR073T7` | **NFD 自建** | 暫存 | 2 | `NFDR073`、`NFDR073A` |
| `OFD081A` | OFD | 表 | 2 | `NFDR073A`、`NFDR077` |
| `OFD221A` | OFD | 表 | 2 | `NFDR076`、`NFDR123` |
| `CTL014` | CTL | 表 | 1 | `NFDR001` |
| `FSK003` | FSK | 表 | 1 | `NFDR073A` |
| `F_FORMATSTRINGTOTABLE` | 不明 | Function | 1 | `NFDR114` |
| `MYOFD303A` | 不明 | 同義字(推測) | 1 | `NFDR077` |
| `NFDR073T0` | **NFD 自建** | 暫存 | 1 | `NFDR073` |
| `NFDR073T10` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T11` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T12` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T16` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T17` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T18` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T19` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T24` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T29` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T31` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T33` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T34` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T5` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T8` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `NFDR073T9` | **NFD 自建** | 暫存 | 1 | `NFDR073A` |
| `OCRMTMP` | 不明 | 暫存 | 1 | `NFDR073` |
| `OFD002` | OFD | 表 | 1 | `NFDR073B` |
| `OFD017A` | OFD | 表 | 1 | `NFDR001` |
| `OFD123A` | OFD | 表 | 1 | `NFDR123` |
| `OFD123A_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `OFD126` | OFD | 表 | 1 | `NFDR073` |
| `OFD132A` | OFD | 表 | 1 | `NFDR073A` |
| `OFD221A_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `OFD251A` | OFD | 表 | 1 | `NFDR077` |
| `OFD306A` | OFD | 表 | 1 | `NFDR123` |
| `OFD306_TMP` | OFD | 暫存 | 1 | `NFDR123` |
| `SAL051` | SAL | 表 | 1 | `NFDR073B` |

## 附錄 B. SP / Function / Trigger / View

### B.1 SP 總表(60 支,版控內 1 支)

| SP | 呼叫者 | 在版控 | 錨點 |
|---|---|---|---|
| `s_NFDR023_Get` | `NFDR023` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR023_PO.cs:64` |
| `s_NFDR071_Get` | `NFDR071` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR071_PO.cs:55` |
| `s_NFDR072_Get` | `NFDR072` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR072_PO.cs:54` |
| `s_NFDR073_1_Get` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97` |
| `s_NFDR073_ChkRdm` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:492` |
| `s_NFDR073_Get` | `NFDR073` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:97` |
| `s_NFDR103_Get` | `NFDR103` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR103_PO.cs:48` |
| `s_NFDR105_Get` | `NFDR105` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:55` |
| `s_NFDR107B_Get` | `NFDR107B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107B_PO.cs:65` |
| `s_NFDR107B_T2_Get` | `NFDR107B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107B_PO.cs:67` |
| `s_NFDR108_Get` | `NFDR108` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR108_PO.cs:53` |
| `s_NFDR114_Get` | `NFDR114` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:53` |
| `s_NFDR115_Get` | `NFDR115` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:41` |
| `s_NFDR153_Get` | `NFDR153` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR153_PO.cs:51` |
| `s_NFDR154_Get` | `NFDR154` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:42` |
| `s_NFDR155_Get` | `NFDR155` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR155_PO.cs:53` |
| `s_NFDR156_Get` | `NFDR156` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR156_PO.cs:44` |
| `s_NFDR158_Get` | `NFDR158` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR158_PO.cs:41` |
| `s_NFDR159_1_Get` | `NFDR159` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:51` |
| `s_NFDR159_Get` | `NFDR159` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:47` |
| `s_TA_NFDR001_Get` | `NFDR001` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57` |
| `s_TA_NFDR002_Get` | `NFDR002` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR002_PO.cs:59` |
| `s_TA_NFDR003_Get` | `NFDR003` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR003_PO.cs:59` |
| `s_TA_NFDR004_Get` | `NFDR004` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR004_PO.cs:59` |
| `s_TA_NFDR005_Get` | `NFDR005` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR005_PO.cs:60` |
| `s_TA_NFDR006_Get` | `NFDR006` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR006_PO.cs:61` |
| `s_TA_NFDR007_Get` | `NFDR007` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR007_PO.cs:58` |
| `s_TA_NFDR021_Get` | `NFDR021` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR021_PO.cs:58` |
| `S_TA_NFDR024_GET` | `NFDR024` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR024_PO.cs:59` |
| `S_TA_NFDR073B_EMAIL` | `NFDR073B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:160` |
| `S_TA_NFDR073B_GET` | `NFDR073B` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:76` |
| `S_TA_NFDR073_0_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:119` |
| `S_TA_NFDR073_1_GET` | `NFDR073A` | **是**(`DB/SP/S_TA_NFDR073_1_GET.SQL`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:142` |
| `S_TA_NFDR073_2_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:147` |
| `S_TA_NFDR073_3_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:112` |
| `S_TA_NFDR073_4_GET` | `NFDR073A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:137` |
| `s_TA_NFDR075_Get` | `NFDR075` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR075_PO.cs:53` |
| `S_TA_NFDR076_GET` | `NFDR076` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:64` |
| `S_TA_NFDR077_GET` | `NFDR077` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:65` |
| `S_TA_NFDR101_GET` | `NFDR101` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR101_PO.cs:72` |
| `S_TA_NFDR102_GET` | `NFDR102` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR102_PO.cs:65` |
| `s_TA_NFDR104_Get` | `NFDR104` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR104_PO.cs:73` |
| `s_TA_NFDR107A_Get` | `NFDR107A` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:68` |
| `S_TA_NFDR109_GET` | `NFDR109` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR109_PO.cs:54` |
| `S_TA_NFDR111_GET` | `NFDR111` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR111_PO.cs:58` |
| `S_TA_NFDR120_GET` | `NFDR120` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR120_PO.cs:51` |
| `S_TA_NFDR121_GET_1` | `NFDR121` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR121_PO.cs:57` |
| `S_TA_NFDR121_GET_2` | `NFDR121` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR121_PO.cs:80` |
| `S_TA_NFDR122_GET` | `NFDR122` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR122_PO.cs:59` |
| `S_TA_NFDR150_GET` | `NFDR150` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR150_PO.cs:54` |
| `S_TA_NFDR151_GET` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:74` |
| `S_TA_NFDR151_GET_1` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:81` |
| `S_TA_NFDR151_GET_2` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:87` |
| `S_TA_NFDR151_GET_3` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:93` |
| `S_TA_NFDR151_GET_4` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:116` |
| `S_TA_NFDR151_GET_5` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:111` |
| `S_TA_NFDR151_GET_Charge` | `NFDR151` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:175` |
| `S_TA_NFDR157_GET` | `NFDR157` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:61` |
| `s_TA_NFDR160_1_Get` | `NFDR160` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR160_PO.cs:74` |
| `s_TA_NFDR160_Get` | `NFDR160` | 否 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR160_PO.cs:69` |

### B.2 Function

| 名稱 | 方言 | 用在哪 | 狀態 |
|---|---|---|---|
| `dbo.f_FormatStringToTable` | **MSSQL** | `NFDR114` 的日結檢核 | Oracle 上不存在,見 §7.4.4 |
| `F_TA_GETFUNDNAV` | Oracle | `NFDR123` 取淨值 | 不在版控 |
| `F_TA_STRTODATE` | Oracle | `NFDR123` 字串轉日期 | 不在版控 |
| `F_TA_GETAGENT` | Oracle | `NFDR123` 取通路簡稱 | 不在版控 |

### B.3 Trigger / View

本片未讀到任何 trigger。唯一疑似 view 的是 `OFD081V`(尾碼 `V`,被 4 支當基金清單來源),**定義不在版控**。

## 附錄 C. 代碼對照

| 代碼 | 值 | 意義 | 來源 |
|---|---|---|---|
| `SHORE_ID` | `2` | 境內基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:296` |
| `SHORE_ID` | `1` | 境外基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:300` |
| `OFD0811A.INV_AREA` | `D` / 非 `D` | 境內 / 海外投資區域 | 從 `NFDR076` 的判斷式反推:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:147-150`,**無定義檔可佐證,標假設** |
| `OFD0811A.PROF_TYPE2` | `1` / `2` | 基金屬性(從 `uchkFUND_TYPE1/2/3` 對應推測) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:145-152`,標假設 |
| `OFD303A.POST_CTL_CODE` | `N` | 未過帳 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:154`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:169` |
| `OFD303A.ALLOT_CTL_CODE` | `3` | 被排除的申購狀態(語意不明) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:157`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:138` |
| `OFD251A.REDEM_PROC_CODE` | `3` | 被排除的買回處理狀態 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:339`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR157_PO.cs:88` |
| `REDEM_CTL_CODE` | `4` | 被排除的買回狀態 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:167` |
| `BF_SORT_CD` | `012` | 被排除的受益人分類 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` |
| `REJ_POST` | `Y` | 拒收紙本 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` |
| `BMS001A.FREEZE_CD` | `N` | 未凍結 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:92` |
| `OFD126.ST_CD` | `03` | 某種狀態(語意不明) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:161` |
| 基金代碼 `7A` / `7B` | — | 被排除的兩檔股票型(海外)基金〔客戶特定〕 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:150` |
| `FUND_ID` `ALL FUNDS` | — | 基金清單的彙總列,`NFDR115` / `NFDR158` 會排除 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:103` |

**除 `SHORE_ID` 外,以上代碼值的意義全部是從判斷式反推的,repo 內沒有對照表可查。**`CTL014` / `CTL018` 是代碼表但內容在資料庫裡,不在版控。

## 附錄 D. 本片 44 支處置表

取代覆蓋率掃描(`--module NFD` 會拿 132 支來比,本片只寫 44 支)。

| # | 代號 | 本文處置 | PO 基底 | 資料來源 | 引用 `.rpt` 數 | `.rpt` 在版控 | 在 csproj | SP 在版控 |
|---|---|---|---|---|---|---|---|---|
| 1 | `NFDR001` | **已深寫** | `INFDR001_PO` | SP+inline | 5 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 2 | `NFDR002` | 表格帶過 | `INFDR002_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 3 | `NFDR003` | 表格帶過 | `INFDR003_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 4 | `NFDR004` | 表格帶過 | `INFDR004_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 5 | `NFDR005` | 表格帶過 | `INFDR005_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 6 | `NFDR006` | 表格帶過 | `INFDR006_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 7 | `NFDR007` | 表格帶過 | `INFDR007_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 8 | `NFDR021` | 表格帶過 | `INFDR021_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 9 | `NFDR023` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 10 | `NFDR024` | 表格帶過 | `INFDR024_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 11 | `NFDR071` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 12 | `NFDR072` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 13 | `NFDR073` | **已深寫** | **`Basic_PO`** | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/3 在 |
| 14 | `NFDR073A` | **已深寫** | `INFDR073A_PO` | SP+inline | 0 | —(非 Crystal) | UI+Ctl+PO 全在 | **1/5 在** |
| 15 | `NFDR073B` | **已深寫** | `INFDR073B_PO` | SP+inline | 4 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 16 | `NFDR075` | 表格帶過 | `INFDR075_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 17 | `NFDR076` | **已深寫** | `INFDR076_PO` | SP+inline | 5 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 18 | `NFDR077` | **已深寫** | `INFDR077_PO` | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 19 | `NFDR101` | 表格帶過 | `INFDR101_PO` | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 20 | `NFDR102` | 表格帶過 | `INFDR102_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 21 | `NFDR103` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 22 | `NFDR104` | 表格帶過 | `INFDR104_PO` | SP | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 23 | `NFDR105` | **已深寫** | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 24 | `NFDR107A` | **已深寫** | `INFDR107A_PO` | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 25 | `NFDR107B` | **已深寫** | **`Basic_PO`** | SP+inline | 3 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 26 | `NFDR108` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 27 | `NFDR109` | 表格帶過 | `INFDR109_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 28 | `NFDR111` | 表格帶過 | `INFDR111_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 29 | `NFDR114` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 30 | `NFDR115` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 31 | `NFDR120` | 表格帶過 | `INFDR120_PO` | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 32 | `NFDR121` | 表格帶過 | `INFDR121_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 33 | `NFDR122` | 表格帶過 | `INFDR122_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 34 | `NFDR123` | **已深寫** | `INFDR123_PO` | 純 inline | 0 | —(非 Crystal) | UI+Ctl+PO 全在 | — |
| 35 | `NFDR150` | 表格帶過 | `INFDR150_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 36 | `NFDR151` | **已深寫** | `INFDR151_PO` | SP | 4 | 全在 | UI+Ctl+PO 全在 | 0/7 在 |
| 37 | `NFDR153` | 表格帶過 | **`Basic_PO`** | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 38 | `NFDR154` | **已深寫** | **`Basic_PO`** | SP+inline | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 39 | `NFDR155` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 40 | `NFDR156` | 表格帶過 | **`Basic_PO`** | SP | 1 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 41 | `NFDR157` | **已深寫** | `INFDR157_PO` | SP | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 42 | `NFDR158` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/1 在 |
| 43 | `NFDR159` | **已深寫** | **`Basic_PO`** | SP+inline | 2 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |
| 44 | `NFDR160` | 表格帶過 | `INFDR160_PO` | SP | 4 | 全在 | UI+Ctl+PO 全在 | 0/2 在 |

統計:**深寫 17 支、表格帶過 27 支**;`.rpt` **0 支不在版控**、**0 支不在 csproj**;SP **59/60 不在版控**;PO 未遷移(`Basic_PO`)**16 支**。

## 附錄 E. 讀本文時要注意的地方(缺陷與陷阱)

嚴重度:**高**=會產生錯誤的對外文件或法遵報表 / **中**=功能不可用或維護時必踩 / **低**=整潔性。

### E-01 60 支 SP 只有 1 支在版控 —— 嚴重度 **高**

**缺陷**:44 支報表點名 60 個 stored procedure,比對 `atlas_index.json` 的 83 支,只有 `S_TA_NFDR073_1_GET` 在 `DB/SP/`。

**影響**:29 支報表(66%)**讀哪些表完全查不出來**(§2.1.2)。做任何 `OFD*` 表的異動分析時,`NFD` 這 29 支是黑洞——影響面評估天生不完整,而且沒有辦法從 repo 補完。改表上線後才在報表上爆,是這個模組最可能的故障模式。

**錨點**:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:57`(代表)、附錄 B.1 全表。

### E-02 16 支的 `m_db` 永遠是 `null`,一呼叫就 NRE —— 嚴重度 **高**

**缺陷**:繼承 `Basic_PO` 的 16 支,每支都在自己類別裡宣告 `private Database m_db = null;`,而建構子裡唯一的指派被註解掉:

```
private Database m_db = null;

public NFDR115_PO()
{
    //SystemConfigurationSource config = new SystemConfigurationSource();
    //DatabaseProviderFactory provider = new DatabaseProviderFactory(config);
    //m_db = provider.Create("TA");
}
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:18-25`

下一個方法第一行就是 `DbConnection Dbcon = m_db.CreateConnection();`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:34`)。

**為什麼不是誤判**:

1. `Basic_PO` 在 `Vendor.Product.DataAccess` DLL 裡(**無原始碼,從呼叫端反推**),就算它有自己的 `m_db`,子類別重新宣告的同名 private 欄位會**遮蔽**基底的;子類別內所有 `m_db` 都指到自己那個 `null`。

2. 對照組:已遷移的 28 支寫的是 `private Database m_db = new Database("TA", DbServerType.Oracle);`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:25`),**宣告時就給值**。

3. 這 16 支的 Ctl 是直接 `new NFDR115_PO()`(`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR115_Ctl.cs:34`),不走 `DataAccessPool` / `GetDaoInstance<T>`,**沒有任何機會被 Oracle 版替換掉**。

**三支例外**:`NFDR073` 用 `private readonly Database m_db;`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:21`)、`NFDR108` / `NFDR155` 用 `private Database m_db;`——**沒有初始值,也沒有指派**,結果一樣是 `null`,只是編譯器警告不同。

**受影響的 16 支**:`NFDR023` `NFDR071` `NFDR072` `NFDR073` `NFDR103` `NFDR105` `NFDR107B` `NFDR108` `NFDR114` `NFDR115` `NFDR153` `NFDR154` `NFDR155` `NFDR156` `NFDR158` `NFDR159`。

**影響**:這 16 支在 Oracle 環境下**一按預覽就 `NullReferenceException`**。其中 `NFDR073`(投資對帳單)是對外文件、`NFDR154`(贖回交易確認單)也是。

**注意這是讀碼推論**,沒有在執行環境驗證過。可能的反面解釋只有一個:`Basic_PO` 的建構子用反射或其他方式塞值進子類別的 private 欄位——極不可能,但 DLL 無原始碼,無法排除。**動手修之前先在測試環境按一次**。

### E-03 `NFDR073A` 的 `dataID` 截斷到 22 碼 —— 嚴重度 **高**

**缺陷**:`m_db.AddInParameter(Cmd1, "striDATAID", OracleDbType.Varchar2, strDATAID.Substring(0, 22).Trim());`

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:102`

**影響**:17 張 `NFDR073T*` 暫存表全部以 `DATAID` 分租。兩個使用者同時產對帳單、`DATAID` 前 22 碼相同時,**兩份對帳單的資料會互相污染**——甲的持股印到乙的對帳單上。另外 `strDATAID` 若短於 22 碼直接丟 `ArgumentOutOfRangeException`。

### E-04 `INNER JOIN` 讓法遵名單無聲少人 —— 嚴重度 **高**

| 位置 | JOIN | 少掉誰 |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:89` | `JOIN OFD221A_TMP T3 ON T1.BF_NO = T3.BF_NO` | **從來沒有申購紀錄**(例如持股全來自轉申購)的受益人,從 KYC 到期名單上消失 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR123_PO.cs:87` | `JOIN BMS001A` | 受益人主檔缺這筆時消失 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:143` | `FROM OFD303A JOIN OFD0811A ON OFD303A.FUND_ID = OFD0811A.FUND_ID` | **日結檢核**:`OFD0811A` 對不到的基金,未日結資料查不出來,檢核直接放行 |

第三條最惡劣:**報表少印使用者還有機會發現,檢核漏掉是完全無聲的**。

### E-05 30 支沒有任何「查無資料」提示 —— 嚴重度 **中**

44 支裡只有 14 支的 UI 有「無符合查詢條件的資料 / 查無資料」之類的訊息。其餘 30 支在 SP 回空集合時,直接開一張**只有表頭的 Crystal 報表**。

使用者分不出「真的沒有」與「條件打錯 / SP 掛了」。對 `NFDR004`(員工及其關係人買賣月報)這種法遵報表,「空的」與「沒跑到」的差別很重要。

**有訊息的 14 支**:`NFDR001` `NFDR073` `NFDR073B` `NFDR075` `NFDR076` `NFDR077` `NFDR101` `NFDR102` `NFDR105` `NFDR114` `NFDR115` `NFDR122` `NFDR123` `NFDR151`(部分只有 `Rows.Count == 0` 判斷而無訊息文字)。

**更糟的是 `NFDR151` / `NFDR159` / `NFDR105`**:有判斷、有 `AddResultRow(false, 0, "")`,但**訊息是空字串**——UI 拿到 `ReturnCode = false` 卻沒有話可講(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:169`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:130`)。

### E-06 Oracle 三值邏輯:`<> '值'` 遇 NULL 靜默排除 —— 嚴重度 **中**

13 處 `<> '…'`,只有一處用 `NVL` 包起來:

| 錨點 | 條件 | 有沒有防 NULL |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` | `NVL(REJ_POST,' ')<>'Y'` | **有** |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073A_PO.cs:195` | `BF_SORT_CD <> '012'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:148` | `OFD0811A.INV_AREA <> 'D'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:155` | `OFD303A.ALLOT_CTL_CODE <> '3'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:167` | `A.REDEM_CTL_CODE <> '4'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:339` | `OFD251A.REDEM_PROC_CODE<>'3'` | 沒有 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:103` | `OFD081V.FUND_ID <> 'ALL FUNDS'` | 沒有(`FUND_ID` 應為 NOT NULL,風險低) |

另有 4 處 `NOT IN ('7A','7B')`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:150,240`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:177,352`)——`FUND_ID` 為 NULL 時整條 UNKNOWN。

**同一個作者在同一行裡一個包 `NVL` 一個不包**(`NFDR073A_PO.cs:195`),說明這不是「不知道」,是「漏掉」。

### E-07 `CustomTransferOracleModelToView` 是逐張手抄 —— 嚴重度 **中**

```
TransferVDBHelper.TransferTable(view.UIView.NFDR001, model.DataEntity.NFDR001, base.TransferEVAColumn);
TransferVDBHelper.TransferTable(view.UIView.NFDR001_Detail, model.DataEntity.NFDR001_Detail, base.TransferEVAColumn);
TransferVDBHelper.TransferTable(view.UIView.NFDR001_Grid, model.DataEntity.NFDR001_Grid, base.TransferEVAColumn);
```

`Dev/ATLAS.NFD.Report/Source/Control/ReportControl.NFD/NFDR001_Ctl.cs:92-94`

**SP 多回一張表、或 `Model.xsd` 加了一張表而 Ctl 忘了加一行,該張表在報表上永遠空白,不會報錯。** 改報表欄位時,`Model.xsd` / `View.xsd` / Ctl 的 `TransferTable` / `.rpt` 四者要同步,少一個就是「欄位與 xsd 不同步」。

### E-08 MSSQL 語法殘留在 Oracle 連線上 —— 嚴重度 **中**

除了 E-02 的 16 支整體未遷移之外,還有幾處具體的方言殘留:

| 錨點 | 殘留 |
|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:385` | `DELETE …; DELETE …` 一行兩個 statement + `@dataID` |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073_PO.cs:539` | `IF EXISTS(…) SELECT 1 ELSE SELECT 0` —— 純 T-SQL |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:139` | `dbo.f_FormatStringToTable(@FUND_ID)` |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR115_PO.cs:98` | `LEFT JOIN [OFD038]` —— 中括號識別字 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180` | `[OFD006]` + 字串串接 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:160` | `FROM [OFD126]` |
| 上述各支的 `AddInParameter` | `SqlDbType.NVarChar` / `SqlDbType.DateTime` 而非 `OracleDbType` |

### E-09 `NFDR114` 的日結檢核 SQL 少一個空白 —— 嚴重度 **中**

```
strSQL += "   AND FUND_ID IN (SELECT * FROM dbo.f_FormatStringToTable(@FUND_ID))";
strSQL += "GROUP BY FUND_ID";
```

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR114_PO.cs:139-140`

接出來是 `…(@FUND_ID))GROUP BY FUND_ID`,語法錯誤。再加上 `GROUP BY` 配 `ExecuteScalar` 只會拿到第一組的筆數。**三個錯疊在一起,而且因為 E-02 根本執行不到。**

### E-10 字串串接進 SQL —— 嚴重度 **中**(現況不可觸發)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR105_PO.cs:180,185`:欄位名與值都直接串。值連單引號跳脫都沒有。目前因 E-02 執行不到,**但遷移這支時必須先改寫成 bind 變數**。

### E-11 日結檢核例外時 `return -1` —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:186`:`check()` 在 `catch` 之後 `return -1`。呼叫端若以 `> 0` 判斷「有未日結」,**查詢失敗會被當成「都日結了」而放行**——fail-open。

### E-12 `catch` 內 `tran.Rollback()` 可能自己 NRE —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR073B_PO.cs:193-199`:`catch (OracleException) { … tran.Rollback(); }`。`tran` 在 `try` 中段才 `BeginTransaction`,若之前就拋例外,`tran` 是 `null`,**`Rollback()` 自己 NRE,把原始錯誤蓋掉**。

### E-13 成對報表的條件各有複本 —— 嚴重度 **中**

`NFDR076` / `NFDR077` 的「基金類型 + 排除 `'7A'` `'7B'`」條件**一共有四份複本**:

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:145-152`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:235-242`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:172-179`、 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR077_PO.cs:347-354`

改一處漏三處,結果是**申購確認書與買回轉申購確認書的基金範圍不一致**,對帳時才會發現。

### E-14 四份 `GetFUND` 複本,四種基金清單 —— 嚴重度 **中**

見 §7.5.3。`NFDR115` / `NFDR154` / `NFDR158` / `NFDR159` 的基金下拉清單各自演化:兩支排除 `'ALL FUNDS'`、一支限境內、參數名一支叫 `@FUND_GRPCD` 另三支叫 `@FUND_GROUP`。`NFDR154` 的 `WHERE` 還少一層外層括號(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR154_PO.cs:103-105`)——目前無害,加一條 `AND` 就會出事。

### E-15 `NFDR001` 的選項落在列舉外就什麼都不做 —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:88-131` 是 4×2 的 `if / else if` 巢狀,**沒有 `else`**。`uoptOrder` / `uoptPurpose` 的值只要不在列舉內,`SetQueryParameters` 一次都不會被呼叫,報表類別是空的。同一支的 `ReportLoad`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR001.cs:64-68`)只在特定組合下 `SetParameterValue("Purpose", …)`,其他組合 Crystal 沿用上一次的值。

`NFDR151` 的 Excel 分派也一樣(`switch` 無 `default`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR151_PO.cs:105-118`)。

### E-16 `.rpt` 一對多共用 —— 嚴重度 **中**

`NFDR001` 的 8 種選項組合對應 5 張 `.rpt`,`NFDR001RPS` 被三種排序共用、`NFDR001RPS1` 被兩種共用(§7.1.1 的對照表)。**改一張 `.rpt` 會同時影響多個選項組合**,而 UI 上看起來是不同的功能。

### E-17 恆真條件關掉整段篩選 —— 嚴重度 **低**(但極易誤刪)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR076_PO.cs:152`:

```
OR (:striFUND_ID IS NOT NULL AND :striFUND_ID=:striFUND_ID)
```

指定基金代碼時整段「基金類型」篩選失效。可能是刻意的(指定基金就不看類型),但寫成恆真式而非註解,**下一個維護者會當成 bug 刪掉,刪掉之後行為就變了**。

### E-18 非 UTF-8 來源檔 —— 嚴重度 **低**

9 個檔是 **cp950**(Big5),中文註解在 UTF-8 工具下是亂碼:

`NFDR107A` 的 Ctl / Pxy / PO、`NFDR107B` 的 Ctl / Pxy / PO、`NFDR108` 的 Ctl / Pxy / PO。

例:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR107A_PO.cs:157` 的區段標題在 UTF-8 下讀作亂碼。其餘 123 個檔是 `utf-8-sig`。

### E-19 SP 命名兩套並存 —— 嚴重度 **低**

`s_TA_NFDRxxx_Get` 與 `s_NFDRxxx_Get` 兩套命名並存且沒有規則(§2.2);大小寫也混(`S_TA_NFDR024_GET` vs `s_TA_NFDR001_Get`)。Oracle 不分大小寫所以跑得動,但**任何依名字比對的工具都會漏**。

`NFDR073A` 用的是 `S_TA_NFDR073_x_GET`(名字裡沒有 `A`),**照代號推 SP 名一定推錯**。

### E-20 `CommandTimeout = 0` 遍布全片 —— 嚴重度 **低**

幾乎每支 PO 都有 `Cmd.CommandTimeout = 0; //此程式讓它永久跑`(例 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR001_PO.cs:56`)。SP 卡住時 client 無限等待,使用者只能砍行程。

### E-21 寫死常數 —— 嚴重度 **低**

| 值 | 位置 | 應該用 |
|---|---|---|
| `'2'`(境內) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR159_PO.cs:107` | `CTL014.SHORE_ID.OnShore` |
| `'7A'` `'7B'` | `NFDR076` / `NFDR077` 四處 | 設定或代碼表 |
| `受益人KYC到期名單.xlsx` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR123.cs:79` | 帶日期 / 條件 |
| `貴 賓 理 財 對 帳 單` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR073B.cs:123,134,145,157` 四處 | 常數(對照 `NFDR073` 的 `const string ReportName`) |

### E-22 沒有任何 `.rpt` 或 csproj 問題 —— **本片的好消息**

前幾篇踩過的「`.rpt` 不在版控」「檔案存在但不在 csproj」「六層檔名少一個字母」,**本片 44 支一件都沒有**(§2.3)。79 張 `.rpt` 全在版控且全在 `Report.NFD.csproj`;UI / Ctl / PO 三層 132 個檔全在各自 csproj;六層全齊。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `ATLAS.NFD.Report` 前 44 支(`NFDR001`–`NFDR160`)。 |

由 build_doc.py v2.0.0 於 2026-09-15 21:01 產生 · 標題 99 · 圖 5 · 表格 63 · 程式錨點 280 · § 連結 60 · 引用檢查：畫面 53（缺 0） · Table 12（缺 0） · SP 1（缺 0） · Report 14（缺 0） · 結果集 14（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/nfdr2.md
============================================================

# ATLAS NFDR2 模組 全流程商業邏輯

> 產出日期:2026-09-21(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **範圍**:`Dev/ATLAS.NFD.Report` 專案的**後 82 支**(`NFDR168`–`NFDR933`)。前 44 支(`NFDR001`–`NFDR160`)在 `nfdr1.md`。**這兩片合起來,`NFD` 126 支報表全數涵蓋,全庫 909 支畫面收官。** **建議讀法**:趕時間只讀三段——§0.2(本片補齊哪 7 條業務線)、§0.3(兩群「整群開不了」的報表)、附錄 E(踩雷)。要動某支報表再翻 §7 對應小節。

> ⚠ **接續 `nfdr1.md`,不重寫**。`NFD` 是什麼、為什麼沒有主專案、跟 `OFD` 怎麼切分,結論全部在 `nfdr1.md §0`,本文直接引用。六層呼叫順序在 `nfdr1.md §1`,本片 82 支**完全相同**,不重畫。M / I / B 畫面本模組一支都沒有,見 §4 §5 §6。 ⚠ **〔客戶特定〕**:基金代碼、銷售機構代碼、`NFDR434` 的元富證券、`NFDR210` 的中國信託股務代理部、公會英文報表格式為本站台的值。 ⚠ 本片 82 支同樣**一張自有業務主檔都沒有**,而且比前片更極端:**82 支裡有 72 支(88%)連表名都看不到**——SQL 全埋在 100 支版控外的 SP 裡(§2.1)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。M / I / R / B 對照表看 `ofdr1.md §0.2`,**不重做**。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 本片在 `NFD` 裡的位置

`NFD` 的定位(純輸出層、沒有主專案、只讀不寫 `OFD` 軌的表、零反向依賴)已由 `nfdr1.md §0.1` 與 `nfdr1.md §0.2` 定案,**本文不重複論證**,只補三件前片看不到的事:

| 補充事實 | 內容 | 佐證 |
|---|---|---|
| 本片把「純輸出層」推到極端 | 前片 44 支有 15 支能在 PO 讀到表名;本片 82 支**只有 10 支**能讀到表名,其餘 72 支連一張表名都寫不出來 | §2.1 |
| SP 版控從「幾乎沒有」變成「完全沒有」 | 前片 60 支 SP 只有 1 支在版控;本片 **100 支 SP,版控內 0 支** | §2.2、附錄 B |
| `.rpt` 反而更乾淨 | 本片 122 張 `.rpt` **全部在版控、全部在 csproj、零懸空**,連 csproj 指到不存在檔案的情形都沒有 | §2.3 |

`NFD` 三個字母的展開在 repo 裡仍然找不到定義,本文延續 `nfdr1.md` 的作法,**不造官方名稱**。

### 0.2 `NFD` 126 支的全貌:12 條業務線

把兩片合起來,以**報表中文名**為軸(不是代號連號,見 §0.5),`NFD` 126 支分成 **12 條業務線**。前片 5 條、本片新增 7 條:

| # | 業務線 | 支數 | 代號 | 在哪一片 |
|---|---|---|---|---|
| 1 | 受益人結構與法遵月報 | 7 | `NFDR001`–`NFDR007` | `nfdr1.md §7.1` |
| 2 | 受益人排行與異常清冊 | 3 | `NFDR021`–`NFDR024` | `nfdr1.md §7.2` |
| 3 | 對外文件:對帳單 / 交易確認書 | 8 | `NFDR071`–`NFDR077` | `nfdr1.md §7.3` |
| 4 | 申購側:扣款 / 手續費 / 稅 / 統計 | 16 | `NFDR101`–`NFDR123` | `nfdr1.md §7.4` |
| 5 | 買回 / 贖回 / 轉申購側 | 10 | `NFDR150`–`NFDR160` | `nfdr1.md §7.5` |
| 6 | **AML 洗錢防制與交易監控** | 8 | `NFDR168`–`NFDR170` `NFDR185`–`NFDR188` `NFDR245` | **本文 §7.1** |
| 7 | **實體受益憑證與併戶** | 10 | `NFDR200`–`NFDR207` `NFDR210` `NFDR244` | **本文 §7.2** |
| 8 | **扣款帳號核印(印鑑核對)** | 5 | `NFDR221`–`NFDR225` | **本文 §7.3** |
| 9 | **銷售額度控管 / 匯款比對 / 退匯 / 交易查核** | 9 | `NFDR231`–`NFDR233` `NFDR236` `NFDR237` `NFDR240`–`NFDR243` | **本文 §7.4** |
| 10 | **通路報酬:手續費 / 銷售服務費 / 獎金** | 8 | `NFDR171` `NFDR352` `NFDR431`–`NFDR437` `NFDR933` | **本文 §7.5** |
| 11 | **營運統計與淨銷售** | 39 | `NFDR501`–`NFDR517` `NFDR701`–`NFDR707` `NFDR800`–`NFDR816` | **本文 §7.6 §7.7 §7.8** |
| 12 | **投信投顧公會英文申報** | 3 | `NFDR558`–`NFDR560` | **本文 §7.9** |

三個觀察:

1. **第 11 條線(營運統計與淨銷售)一條就佔 126 支的 31%**,而且是三段不同年代的沉積(§7.6 §7.7 §7.8):`5xx` 用 `Basic_PO` + SQL Server 風格參數(`@Xxx`)、`7xx` 同上、`8xx` 全部用 `INFDRxxx_PO` + Oracle `RefCursor`。同一件事(統計銷售數字)做了三輪,舊的沒有下架。

2. **第 6 條線(AML)是本片唯一「法遵味」的新業務**,而且是後期加的——`NFDR168`–`NFDR188` 全部走 `INFDRxxx_PO` + Oracle,沒有一支是舊 `Basic_PO`。

3. **第 3 條線(對外文件)只在前片**;本片 82 支**沒有任何一支是寄給受益人的文件**,全部是給內部作業、主管機關或通路看的。本片的讀者是「公司內部 + 監理 + 通路」,不是「受益人」。

### 0.3 兩群「整群開不了」的報表(必答問題 2)

本片最重的發現:**`NFDR501`–`NFDR517` 與 `NFDR701`–`NFDR707` 這兩群,合計 22 支,有 22 支裡的 22 支都停在 `Basic_PO` 沒有遷移到 Oracle,其中 22 支的 `m_db` 恆為 `null`。使用者按「預覽」的當下就 `NullReferenceException`,連 SQL 都送不出去。**

精確數字(實測,判準與逐支名單見附錄 E-01、附錄 D):

| 群 | 支數 | `m_db` 死 | 活 | 業務 |
|---|---|---|---|---|
| `NFDR501`–`NFDR517` | 17 | **15** | 2(`NFDR514` `NFDR515`) | 營運統計:銷售機構別 / 開戶 / 戶數 / 申贖 / 定期定額 / 交易量 |
| `NFDR701`–`NFDR707` | 7 | **7** | 0 | 淨銷售統計:直銷部門 / 通路業務部門 / 櫃台部門 / 指定用途 / 通路 / 特殊受益人 / 基金 |

有沒有活的替代品?逐項查過,**分成三種下場**:

| 死掉的業務 | 有沒有活的替代 | 替代品 | 判定 |
|---|---|---|---|
| 各銷售機構別申購統計(`NFDR501`) | 有,部分 | `NFDR812` 預估申、贖基金日報表(活)+ `NFDR805` 業務單位期間報表(活) | 粒度不同(日 vs 期間),**不是同一份** |
| 開戶統計(`NFDR502`) | 有 | `NFDR807` `Open New Account and Data Moving`(活,`NFDR807_PO.cs`) | 英文版、給公會用,中文管理版沒了 |
| 受益人戶數統計(`NFDR503`) | 有 | `NFDR800` 受益人身份統計表 / `NFDR801` 結餘日期受益人別資料分析表(皆活) | 可替代 |
| 各基金申購贖回統計(`NFDR504`) | 有 | `NFDR806` `Subscription & Redemption Summary Report (By ***)`(活) | 軸不同(基金 vs 通路) |
| 申購 N 元以上統計(`NFDR505`) | **沒有** | — | **業務上真的少了一份**:大額申購門檻統計,全庫 126 支沒有第二支做同一件事 |
| **定期定額五支**(`NFDR506`–`NFDR510`:扣款分析彙總 / 扣款金額分析 / 佔基金規模比例 / 銷售分析 / 扣款統計) | **全部沒有** | — | **本片最嚴重的缺口**:定期定額(RSP)的營運分析報表**整組躺著**。`rsp.md` 那邊是 RSP 的維護與批次,不產這五張統計 |
| 交易作業量 / 人員處理交易量 / 各基金交易量(`NFDR511`–`NFDR513`) | 有 | `NFDR514` 作業統計總表(活)、`NFDR515` 交易來源統計表(活) | `NFDR514` / `NFDR515` 就是這三支的「後繼版」,見 §7.6.3 |
| 受益人持有基金比率(`NFDR516`) | **沒有** | — | **少了一份**。`NFDR003` 股權分散表(前片)軸不同 |
| 銷售買回統計(`NFDR517`) | 有 | `NFDR814` 餘額統計表 / `NFDR815` 銷售單位彙總表(皆活) | 可替代 |
| **淨銷售統計七支**(`NFDR701`–`NFDR707`) | **幾乎沒有** | `NFDR805` 業務單位日 / 期間報表(活)可湊「部門別」,其餘四軸(指定用途 / 特殊受益人 / 通路 / 基金淨銷售)**沒有** | **第二嚴重的缺口**:「淨銷售」(申購 − 買回)這個口徑,活著的報表裡只有 `NFDR805` 沾得上邊 |

**要點名的缺口清單(沒有替代品、業務上真的少一份報表)**:

| 缺口 | 代號 | 報表中文名 |
|---|---|---|
| 大額申購門檻統計 | `NFDR505` | 申購 N 元以上統計表 |
| 定期定額扣款分析彙總 | `NFDR506` | 定期定額基金扣款分析彙總表 |
| 定期定額扣款金額分析 | `NFDR507` | 定期定額扣款金額分析表 |
| 定期定額佔基金規模比例 | `NFDR508` | 定期定額佔基金規模之比例表 |
| 定期定額銷售分析 | `NFDR509` | 定期定額銷售分析表 |
| 定期定額扣款統計 | `NFDR510` | 定期定額扣款統計表 |
| 受益人持有基金比率 | `NFDR516` | 受益人持有基金比率表 |
| 指定用途淨銷售 | `NFDR704` | 指定用途淨銷售統計表 |
| 特殊受益人淨銷售 | `NFDR706` | 特殊受益人淨銷售統計表 |
| 通路淨銷售 | `NFDR705` | 通路淨銷售統計表 |
| 基金淨銷售 | `NFDR707` | 基金淨銷售統計表 |

11 支。**這不是「程式有 bug」,是「這 11 份報表現在印不出來,而且沒有別的地方印得出來」。** 嚴重度判斷見附錄 E-01。

> **假設**:上表的「有 / 沒有替代品」是**從報表中文名與參數比對**推的,不是從使用者訪談。SP 在版控外,無法比對兩支報表的實際計算口徑是否一致。要下「可以下架 `NFDR50x`」的結論,必須另外拿 SP 原始碼比對。

### 0.4 `NFDR800`–`NFDR816` 是全庫最長的連號(必答問題 3 預告)

15 支連號(`NFDR808` `NFDR813` 不存在)。`ofdr1.md` 的結論是「連號 ≠ 同系列」,本片**驗出相反的結果**:這群是**全庫目前看過最緊的一組連號**,15 支共用同一個 PO 模板、同一個 `RefCursor` / `OutTB` 取數模式、同一套命名,但是**業務上是 15 份不同的報表**,不是一份報表的 15 個切面。詳細比對(含參數 Jaccard)在 §7.8.1。

### 0.5 這片最反直覺的四件事

| # | 反直覺 | 出處 |
|---|---|---|
| 1 | **連號和業務線幾乎無關**。`NFDR171`(代理收付買回費統計表,通路報酬線)夾在 `NFDR168`–`NFDR170` 三支 AML 報表中間;`NFDR245`(疑似洗錢控管表,AML 線)夾在 `NFDR240`–`NFDR244` 五支交易查核報表最後面 | §7.1、§7.4 |
| 2 | **`NFDR204` 與 `NFDR206` 的報表中文名一模一樣**——都叫「受益憑證(憑證號碼)作廢明細表」,但是兩支不同的畫面、兩支不同的 SP、兩張不同的 `.rpt` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR206.cs:119` |
| 3 | **`NFDR201` 的報表中文名是空字串**,`SetQueryParameters("NFDR201RPS", "NFDR201RPS", "")`,Crystal 標頭印出來是空白 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR201.cs:104` |
| 4 | **`NFDR810` / `NFDR811` 的「執行」鈕按下去只跳一個「此項功能無作用」**,程式碼刻意留著一顆什麼都不做的按鈕 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR810.cs:140`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR811.cs:136` |

### 0.6 使用角色

| 角色 | 用哪些 | 在意什麼 |
|---|---|---|
| 法遵 / 稽核 | §7.1 AML 九支、`NFDR810` 缺件結存比率下載作業-稽核 | 名單完整性。**少印一列就是申報錯誤**,見附錄 E 的過濾類卡控 |
| 股務 / 憑證作業 | §7.2 憑證十一支 | 實體憑證號碼與紙張流水號的對帳 |
| 出納 / 帳務 | §7.3 核印五支、§7.4 匯款比對與退匯 | 扣款帳號能不能用、錢有沒有匯錯 |
| 通路管理 / 財務 | §7.5 通路報酬八支 | 手續費、銷售服務費、獎金結算金額 |
| 管理階層 / 業務單位 | §7.6–§7.8 營運統計 39 支 | 銷售數字。**其中 22 支現在按不下去** |
| 投信投顧公會 | §7.9 英文申報三支 | 格式固定、期間固定 |

### 0.7 全域開關與前提

延續 `nfdr1.md §0.5`:本模組**沒有任何全域開關**,沒有 `CTL` 旗標控制哪支報表能不能跑,也沒有權限判斷。補一條本片限定的:

**`NFDR933` 沒有任何權限控制。** 這支是「通路年度提撥人員銷售獎金報表 / 通路人員銷售獎金報表」——薪酬類資料——`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR933.cs` 全檔沒有出現任何角色 / 權限 / 使用者代號判斷。這與 `ofdi1.md` 對六支 `9xx` 畫面的實測結論一致:**`9xx` 是「後來加的」,不是「管理者專用」**(必答問題 6,詳見 §7.5.4)。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] NFD 126 支的 12 條業務線、本片 82 支的新舊兩個世代、兩群整群失效的報表、四條輸出出口，以及 NFD 會回寫別人的表這件事
圖中文字:① NFD 126 支 = 12 條業務線（前片 5 條 + 本片 7 條） / 1-5 前片 44 支 / 受益人／對帳單／申購／買回 / 6 AML 8 支 / 交易監控 168-188 245 / 7 實體憑證 10 支 / 200-210 244 / 8 核印 5 支 / 221-225 / 9 額度/匯款 9 支 / 231-243 / 10 通路報酬 8 支 / 171 352 431-437 933 / 11 營運統計 39 支 / 5xx 7xx 8xx（本片最大） / 12 公會英文 3 支 / 558-560 / ② 本片 82 支的技術斷層：兩個世代並存 / 舊 Basic_PO 37 支 / m_db 恆 null → 按預覽即 NRE / 新 INFDRxxx_PO 45 支 / Oracle RefCursor，可用 / 判別式 / s_ 後面有沒有 TA_ / SP 100 支 / 版控內 0 支 / ③ 兩群整群死掉（22 支），11 份報表沒有替代品 / 5xx 營運統計 17 支 / 死 15，活 514 515 / 7xx 淨銷售 7 支 / 全死，零替代 / 定期定額 506-510 / 五份分析報表全沒了 / 505 516 704-707 / 大額／比率／四個淨銷售軸 / ④ 四條輸出出口 / Crystal .rpt 125 張 / 全在版控＋csproj，零懸空 / Excel 下載 8 支 / 不經 Crystal / 交換檔 DSR.mon / 只有 NFDR812 / 此項功能無作用 / NFDR810 811 的死按鈕 / ⑤ 本片推翻前片的一件事 / NFD 不是純唯讀 / 會回寫已印旗標 / UPDATE OFD701 / NFDR223 列印後 / UPDATE OFD721 724 / NFDR201 列印後 / 旗標寫在別人的表上 / 改 OFD 要回歸 NFD
```

*圖:圖 1 NFDR2 全景。橘框=本文的主要結論;灰虛框=前片已寫的部分;黑框=無原始碼的黑箱(版控外 SP);橘虛框=已知風險或〔客戶特定〕。實線=推導方向;虛線=歸屬或輸出方向。*

### 1.2 六層呼叫順序:與前片完全相同,不重畫

本片 82 支走的是 `nfdr1.md §1.3` 那條路,一步不差:UI `BeforePreviewOrPrintButtonClicked` → `DoValidate()` → 塞 `Utility.Parameters` → FormProxy → Control `ExecPOActionToViewVDB` → PO `GetStoredProcCommand` → Control `CustomTransferOracleModelToView` → UI `SetParameterValue` 餵 Crystal。**沒有例外,沒有第七層,沒有繞道。**

只有三處與前片的描述需要補充:

| 補充 | 內容 | 錨點 |
|---|---|---|
| **PO 成員變數名有第三種** | 前片只看到 `m_db`;本片多兩支用 `dbTA`(`NFDR431` / `NFDR432`),而且**都有初始化**,是命名變體不是缺陷 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR431_PO.cs:44` |
| **`Basic_PO` 那一半連 `[PODbType]` 都沒有** | 37 支死的 PO **同時**滿足三件事:沒有 `[PODbType(DbServerType.Oracle)]`、沒有 `new Database("TA", …)`、只用 `SqlDbType` 不用 `OracleDbType`。43 支活的則**同時**滿足三件事的反面。**82 支零例外**(§2.4) | 比較 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:16-18` 與 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:25-27` |
| **`RefCursor` 出口有兩種命名** | `OutTB` / `OutTB2` / `OutTB3`(舊)與 `C_RES` / `C_RES_D` / `C_RES_T1`(新)並存,同一群裡也會混用 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR814_PO.cs:77` 用 `OutTB`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:84` 用 `C_RES` |

### 1.3 報表輸出的四條出口(本片比前片多一條)

| 出口 | 怎麼做 | 本片哪些支 |
|---|---|---|
| Crystal 預覽 / 列印 | `SetQueryParameters(ReportClass, ReportID, ReportName)` + `.rpt` 範本 | 77 支,125 張 `.rpt` |
| Excel 下載(`saveFileDialog1` + `ExcelHelper`) | `ExcelHelper.ExcelGenAction` 或 `ExcelCreator`,**不經 Crystal** | `NFDR188` `NFDR352` `NFDR514` `NFDR558`–`NFDR560` `NFDR810` `NFDR811` `NFDR812` |
| **固定檔名的交換檔**(本片獨有) | `saveFileDialog1.FileName = string.Format(@"DSR{0}.mon", …)` ——**副檔名 `.mon`,給外部系統吃的** | `NFDR812`,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:209` |
| 什麼都不做 | 「執行」鈕按下去跳 `MessageBox.Show("此項功能無作用", "執行功能", …)` | `NFDR810` `NFDR811`,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR810.cs:140` |

### 1.4 一日 / 一月作業泳道(推測)

repo 內沒有排程設定可讀,以下由**報表的期間參數型別**推,標「**假設**」:

| 時點 | 判斷依據(參數) | 誰跑 | 跑什麼 |
|---|---|---|---|
| 日中 / 即時 | 單日 `TRAN_DATE` / `DATA_DATE` | 法遵 | `NFDR185` `NFDR186`(單日交易異常表)、`NFDR168`(現金交易監控表) |
| 日終 | `DATA_DATE` 單日 | 業務單位 | `NFDR805`(業務單位日報表)、`NFDR812`(預估申、贖基金日報表 + `.mon` 交換檔) |
| 日終 | `SEAL_DATE` / `RETURN_DATE` | 出納 | `NFDR221`–`NFDR225`(核印五支) |
| 日終 | `REMIT_DATE` / `COMPARDE_DATE` | 帳務 | `NFDR236` `NFDR237`(匯款比對)、`NFDR240`(退匯) |
| 月底 | `CAL_MONTH` / `MONTH_S`–`MONTH_E` / `YM_BNG`–`YM_END` | 財務 / 通路 | `NFDR352`(遞延銷售手續費攤銷)、`NFDR431` `NFDR432`(銷售服務費)、`NFDR816`(手續費收入) |
| 月底 | `datiYYYYMM` | 公會申報 | `NFDR558`–`NFDR560` |
| 月底 / 結帳後 | `BAL_DATE`(**必須各基金皆已結帳**) | 股務 | `NFDR210`(受益憑證中英文持有單位證明)、`NFDR800` `NFDR801` `NFDR814` |
| 年度 | `YEARS` + `QDATE` | 通路 | `NFDR933`(通路年度提撥人員銷售獎金報表) |

`NFDR210` 是本片**唯一一支把「結帳完成」寫成前置卡控**的:「結存日期 各基金必須皆要完成結帳,才可列印」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR210.cs:88`),卡控結果是**阻擋**。其餘吃 `BAL_DATE` 的報表沒有這道檢查——**結帳沒跑完就印,印出來是半套數字,沒有任何提示**(附錄 E-05)。

### 1.5 要改本片的報表之前

`nfdr1.md §1.6` 的七項清單照用。本片要**額外**注意四件事:

1. **先確認這支活不活。** 動 `NFDR501`–`NFDR517` / `NFDR701`–`NFDR707` 之前先看附錄 D 的 `m_db` 欄。對一支已經 NRE 的報表「修 SQL」是白工——它連 SQL 都送不出去。

2. **SP 一支都不在版控。** 本片 100 支 SP,`DB/SP/` 裡**零命中**(§2.2)。改欄位時 repo 內改不到取數那一半,也**沒有任何 diff 可以 review**。

3. **`.rpt` 反而不用擔心。** 125 張全在版控、全在 csproj、零懸空、csproj 也沒有指到不存在的檔(§2.3)。這是本片唯一乾淨的一塊。

4. **`NFDR806` / `NFDR807` 這種「PO 除了代號以外一字不差」的成對檔,改一邊要想另一邊。** 本片有多組(§7.8.1、附錄 E-09)。

## 2. 資料模型

```text
[圖] NFD 兩片合併的扇入圖：25 支看得見表名的報表連到 OFD 軌 25 張表與共用主檔，NFD 自有業務表零張，但會回寫三張別人的表
圖中文字:NFD 126 支合併：25 支看得見表名，101 支在 SP 黑箱裡 / 前片 15 支 / 對帳單／確認書／KYC／手續費 / 本片 NFDR201 / 大憑證＋兩段 UPDATE / 本片 168 210 / 兩支結帳前置檢核 / 本片 241 243 244 / 撈基金下拉清單 / 本片 223 704 933 / 核印／指託戶／獎金前置 / 本片 203 237 / 只在 Model.xsd 看得到 / OFD303A / 日結控制 · 前片5支 本片2支 / OFD721 724 0811 312 / 受益憑證家族 / OFD081V 081A 038 038A / 基金主檔與群組 / OFD701 711 / 核印 / OFD922A LOG_OFD931A / 獎金計算與作業log / BMS001 BMS001A / 受益人主檔 / CTL014 CTL018 SALR905T1 / 代碼表與別人的暫存表 / OFD 軌合計 25 張 / 真正的業務資料 / BMS COD SAL FSK / 共用主檔 5 張 / CTL 2 張 / 內容在 DB / NFDR073T× 17 張 / 只有前片自建 / NFD 自有業務表：0 張 / 126 支都是別人的資料 / NFD 會寫 3 張 / OFD701 721 724 已印旗標
```

*圖:圖 2 126 支合併扇入(§2.1)。左=看得見表名的報表(前片 15 支彙總成一格);中=被讀到的表;右=按模組彙總。灰虛框=別模組的表;黑框=無原始碼;橘虛框=前片自建暫存表與 NFD 的寫入。101 支的相依性在版控外的 SP 裡，畫不出來。*

### 2.1 `NFD` 讀誰的表:126 支合併版(接續 `nfdr1.md §2.1`)

**本片的結論比前片更極端:82 支裡只有 10 支能在 PO 或 `Model.xsd` 讀到外部表名,72 支(88%)完全看不到。**

| 片 | 支數 | 看得到表名 | 完全黑箱 | 黑箱比例 |
|---|---|---|---|---|
| `nfdr1.md`(`NFDR001`–`NFDR160`) | 44 | 15 | 29 | 66% |
| **本片**(`NFDR168`–`NFDR933`) | 82 | **10** | **72** | **88%** |
| **`NFD` 合計** | **126** | **25** | **101** | **80%** |

本片這 10 支看得到的表,逐支列出。**注意:「看得到」不代表那就是全部的表**——這些 inline SQL 大多只用來撈下拉清單或做前置檢核,報表主體的 SQL 仍在 SP 裡:

| 支 | 讀到的表 | 歸屬模組 | 怎麼看到的 | 錨點 |
|---|---|---|---|---|
| `NFDR201` | `OFD724` `OFD721` `OFD0811` `BMS001` | `OFD` 軌 + `BMS` | PO inline SQL(主查詢 + 兩段 `UPDATE`),**T-SQL 語法** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:101`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:201` |
| `NFDR203` | `OFD312` | `OFD` 軌 | PO inline SQL(組憑證號)+ `Model.xsd` 結果集名 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR203_PO.cs:92` |
| `NFDR210` | `OFD303A` | `OFD` 軌 | PO inline SQL(結帳前置檢核,§7.2.3) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:109` |
| `NFDR223` | `OFD711` `OFD701` | `OFD` 軌 | PO inline SQL(讀失敗原因 + **寫已印旗標**) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:70`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:254` |
| `NFDR237` | `OFD0819` | `OFD` 軌 | `Model.xsd` 結果集名,**SQL 仍在 SP 裡** | `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR237Model.xsd` |
| `NFDR241` | `OFD081V` `OFD038` | `OFD` 軌(含 view) | PO inline SQL(撈基金下拉),**T-SQL 方括號** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:53` |
| `NFDR243` | `OFD081V` `OFD038A` | `OFD` 軌 | PO inline SQL(撈基金下拉),已改 Oracle bind | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR243_PO.cs:62` |
| `NFDR244` | `OFD038A` `OFD081A` | `OFD` 軌 | PO inline SQL(撈基金下拉) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR244_PO.cs:104` |
| `NFDR704` | `BMS001` | `BMS` | PO inline SQL(指託戶檢核,§7.7.2) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:120` |
| `NFDR933` | `OFD922A`、`LOG_OFD931A` | `OFD` 軌 + 系統 log | PO inline SQL(前置狀態檢查) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:118`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:156` |
| (`NFDR201` 另見) | `NFER201_CER`、`NFER201_CER_CK` | **不明**(`NFER` 三碼在全庫查不到對應模組) | `Model.xsd` 結果集名 | `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR201Model.xsd` |

**`NFER201_CER` 值得停一下**:`NFER` 這個前綴在 `Dev/` 底下找不到任何對應的專案或模組,而且它出現在 `NFDR201`(大憑證相關)的結果集名裡。**假設**:是 `NFDR` 打成 `NFER` 的錯字,而且錯了兩處(`NFER201_CER` / `NFER201_CER_CK`)。依據是同一個 `NFDR201Model.xsd` 裡同時有 `NFDR201` 與 `NFER201_CER` 兩張,前者拼法正確;**沒有反證,但也沒有正證**。

### 2.2 SP:100 支,版控裡 **0 支**

**本片引用的 100 支 SP,在 `DB/SP/`(83 個檔)裡命中 0 支。** `DB/SP/` 裡放的全部是 `S_OTA_*`——境外綜合帳戶軌(`ofdb5.md` 已經查過那一批)。**`NFD` 沒有被順帶進去任何一支**(必答問題 5)。

| 片 | SP 支數 | 版控內 | 比例 |
|---|---|---|---|
| `nfdr1.md` | 60 | 1 | 1.7% |
| **本片** | **100** | **0** | **0%** |
| **`NFD` 合計** | **160** | **1** | **0.6%** |

SP 的命名分兩代,而且**和 PO 死活完全對齊**:

| 世代 | 命名 | 支數 | 對應 PO | 死活 |
|---|---|---|---|---|
| 舊(SQL Server 時期) | `s_NFDRxxx_Get`(無 `TA`,參數用 `@Xxx`) | 44 | `Basic_PO` | **全死** |
| 新 | `s_TA_NFDRxxx_Get` / `S_TA_NFDRxxx_GET` | 56(含 2 支 `string.Format` 動態組出的 `s_TA_NFDR812_Get_2` / `_3`,見 §7.8.2) | `INFDRxxx_PO` | 全活 |

也就是說:**`s_` 後面接不接 `TA_`,就是這支報表能不能用的判別式**(§2.4)。完整 100 支清單在附錄 B。

### 2.3 `.rpt` 範本:125 張,零缺陷(必答問題 4)

| 檢查項 | 前片(`nfdr1.md`) | **本片** | `ofdr1.md` 對照 | `misc.md` 對照 |
|---|---|---|---|---|
| `.rpt` 在版控 | 79 / 79 | **125 / 125** | 1 個懸空 | 2 支躺在沒 csproj 的資料夾 |
| `.rpt` 在 csproj | 79 / 79 | **125 / 125** | — | — |
| csproj 指到不存在的 `.rpt` | 0 | **0** | 1 | — |

**`NFD` 兩片合計 204 張 `.rpt`,零缺陷。** 這是全庫目前最乾淨的一個模組(在 `.rpt` 這一項上)。

但有兩張**在版控、在 csproj、卻沒有任何程式引用**——UI 裡找不到對應的 `SetQueryParameters`:

| 孤兒 `.rpt` | 所屬 | 判定 |
|---|---|---|
| `NFDR431RPS3_1.rpt` | `NFDR431` | UI 只引用 `RPS` / `RPS1` / `RPS2` / `RPS3` / `RPS4`,**沒有 `RPS3_1`** |
| `NFDR432RPS4.rpt` | `NFDR432` | UI 只引用 `RPS` / `RPS1` / `RPS2` / `RPS3`,**沒有 `RPS4`** |

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR431.cs:112`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR432.cs:100`。這是**反向懸空**——不是「程式指到不存在的檔」,是「檔在但沒人指」,**不會出錯,只會讓人以為某個版型還在用**。嚴重度低,但改 `NFDR431` / `NFDR432` 時容易改錯檔案。

另外五支**一張 `.rpt` 都沒有**:`NFDR224`(純處理作業,無報表輸出)、`NFDR352` / `NFDR810` / `NFDR811`(只出 Excel)、`NFDR437`(用 `MessageBox` 直接回報,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR437.cs:105`)。

### 2.4 `m_db` 死活的判別式(必答問題的核心佐證)

實測 82 支 PO,**三項佐證 100% 成立,零例外**:

| 判準 | 43 支活 | 37 支死 | 2 支變體(`NFDR431` `NFDR432`) |
|---|---|---|---|
| 類別上有 `[PODbType(DbServerType.Oracle)]` | **全有** | **全無** | 有 |
| 成員宣告 | `private Database m_db = new Database("TA", DbServerType.Oracle);` | `private Database m_db = null;`(32 支)或 `private Database m_db;`(5 支) | `private Database dbTA = new Database("TA", DbServerType.Oracle);` |
| 建構子 | 空的(欄位初始化式已建好) | 空的,**而且裡面有一段被註解掉的 `m_db = provider.Create("TA");`** | 空的 |
| 參數型別 | 只用 `OracleDbType` | 只用 `SqlDbType` | 只用 `OracleDbType` |
| PO 基底 | `INFDRxxx_PO`(自宣告介面) | `Basic_PO` | `INFDRxxx_PO` |
| SP 命名 | `s_TA_NFDRxxx_Get` | `s_NFDRxxx_Get` | `s_TA_NFDRxxx_Get` |

**第三種變體要特別小心**:`private Database m_db;`(沒有 `= null`)。C# 欄位預設就是 `null`,效果完全一樣,但 grep `m_db = null` 抓不到。本片有 5 支長這樣:

| 支 | 錨點 |
|---|---|
| `NFDR202` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR202_PO.cs:19` |
| `NFDR204` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR204_PO.cs:19` |
| `NFDR205` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR205_PO.cs:19` |
| `NFDR206` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR206_PO.cs:19` |
| `NFDR207` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR207_PO.cs:18` |

被註解掉的初始化長這樣(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:21`):

```
public NFDR501_PO()
{
    //SystemConfigurationSource config = new SystemConfigurationSource();
    //DatabaseProviderFactory provider = new DatabaseProviderFactory(config);
    //m_db = provider.Create("TA");
}
```

三行都註解掉了,**沒有任何東西補上去**。下一個 method `GetReportData` 第一件事就是 `m_db.CreateConnection()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:43`)。這是 Oracle 遷移時「先把 Enterprise Library 的舊寫法註解掉,之後再改」,然後**之後沒有來**。

### 2.5 結果集(`Model.xsd` 的 DataTable)命名

本片 82 支的 `Model.xsd` 共宣告 119 張結果集(不含 `xxxModel` 根節點)。命名分四類:

| 類型 | 樣式 | 例 |
|---|---|---|
| 同名單張 | `NFDRxxx` | `NFDR800` `NFDR816` |
| 編號多張 | `NFDRxxx_1` / `NFDRxxx_2` | `NFDR240_1` `NFDR240_2` `NFDR240_3`、`NFDR933_1`–`NFDR933_4` |
| 語意多張 | `NFDRxxx_SUM` / `_Detail` / `_ALL` / `_DEPT` | `NFDR431_SUM` `NFDR431_DetailAVG` `NFDR504_DEPT_AMT` |
| **借別人的表名當結果集名** | `OFDxxx` | `OFD312`(`NFDR203`)、`OFD711`(`NFDR223`)、`OFD0819`(`NFDR237`) |

最後一類是本片唯一能反推「這支讀誰的表」的線索(§2.1)。

**`NFDR170` 有一個抄錯**:它的 `Model.xsd` 裡兩張結果集叫 `NFDR169` 和 `NFDR169_1`——用的是**隔壁 `NFDR169` 的名字**(`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR170Model.xsd`)。`NFDR169`(既有客戶交易異常表)與 `NFDR170`(新客戶交易異常表)是成對複製出來的,改名只改了一半。這不會出錯(結果集名只要 PO / Ctl / `.rpt` 三邊一致就行),但**grep `NFDR170` 找不到它的結果集**,會讓影響面分析漏掉。

### 2.6 `msdata:Caption` 在本片同樣不可信

`nfdr1.md §2.6` 已經證明 `NFD` 的 `msdata:Caption` 有 9 處填的是另一個欄位名。本片 82 支的 `Model.xsd` 共有 **842 個 `msdata:Caption`**,分布極不平均:

| 支 | Caption 數 | 觀察 |
|---|---|---|
| `NFDR436` | 152 | 最多 |
| `NFDR437` | 82 |  |
| `NFDR431` | 70 |  |
| `NFDR434` | 66 |  |
| `NFDR512` | 34 | **這支的 PO 是死的**,Caption 卻填得最完整 |
| `NFDR171` `NFDR185` `NFDR186` `NFDR202` `NFDR204` `NFDR205` 等 | 0 | 共 33 支一個 Caption 都沒有 |

**結論照抄前片:`msdata:Caption` 在 `NFD` 不能當欄位中文名的真相來源。** 本片不另外做欄位中文名總表——理由是 72 支連表名都看不到,欄位名的來源(SP 的 `SELECT` 清單)也在版控外,對不起來。要中文名請看 `.rpt` 的欄位標籤,那是唯一與畫面一致的來源。

### 2.7 沒有狀態碼

延續 `nfdr1.md §2.5`:本模組**不定義任何狀態碼**,只讀別人的。本片會被當條件用的外部代碼:

| 代碼 | 值 | 出現在 | 錨點 |
|---|---|---|---|
| `AGENT_ID` 銷售機構區別碼 | `0`=公 `1`=銀 `2`=券 `3`=顧 | `NFDR188` `NFDR240` `NFDR517` 等 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR188.cs:63` |
| `FormType` 核印表單類別 | `0`=全部 `1`=一般 `2`(未命名)`3`=財金 | `NFDR222` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:48` |
| `Seal_Type` 核印類別 | 一般 / 財金 / 全部 | `NFDR221` | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR221.cs:51` |
| `REPORT_TYPE` 報表類別 | 每支自己定義,值域不共用 | `NFDR431` `NFDR432` `NFDR436` `NFDR812` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR431_PO.cs:113` |

`NFDR222` 的 `FormType` 有一個**沒有名字的 `2`**——`0`/`1`/`3` 都有中文,`2` 在 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:48` 起的 if-else 鏈裡沒有分支,但在 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:66` 又被當成有效值判斷。選到 `2` 時 `FORMTYPE` 這個顯示字串是空的,Crystal 標頭印空白。卡控結果:**過濾(無提示)**。

## 3. 報表清冊(82 支)

```text
[圖] 本片 82 支依 m_db 活死與資料來源分群：三項佐證的判別式零例外、三種宣告變體、四類資料來源，以及營運統計做了三輪的沉積
圖中文字:① 判別式：三項佐證同時成立，82 支零例外 / 有 PODbType Oracle / 45 支 / 有 new Database TA / 45 支 / 只用 OracleDbType / 45 支 / → m_db 活 / INFDRxxx_PO / SP 命名 s_TA_ / 新世代 / 無 PODbType / 37 支 / 無 new Database / 37 支 / 只用 SqlDbType / 37 支 / → m_db 死 / Basic_PO 按預覽 NRE / SP 命名 s_ 無 TA / 舊世代 / ② 三種宣告變體（grep m_db = null 會漏 5 支） / m_db = null / 32 支 / private Database m_db; / 5 支 隱式 null / dbTA = new Database / 2 支 431 432 是活的 / 建構子三行註解 / EnterpriseLibrary 舊寫法 / ③ 依資料來源分群（82 支） / 純 SP 取數 72 支 / 完全看不到表名 / SP＋inline SQL 10 支 / 只有前置檢核／下拉可見 / 一支畫面多支 SP / 236 237 431 436 501-504 812 / SP 名動態組出 / NFDR812 string.Format / ④ 同一件事做了三輪，舊的沒下架 / 5xx 第一輪 / Basic_PO ＋ @參數 · 死 15 / 7xx 第二輪 / Basic_PO ＋ @參數 · 死 7 / 8xx 第三輪 / INFDR ＋ RefCursor · 全活 / 514 515 是 511-513 後繼 / 同群內也有新舊
```

*圖:圖 3 分群(§2.4、§3)。橘框=本文的判定結論;橘虛框=已死或有風險的那一半;黑框=版控外的黑箱。第①區的三項佐證在 82 支上同時成立、零例外，所以「看 PO 基底就知道這支能不能用」。*

欄位說明:**PO 基底** 已剝 `//` 註解後判讀;**`m_db`** 「死」= 恆 `null`,按預覽即 `NullReferenceException`(§2.4);**SP 在版控** 一律寫成「命中數 / 引用數」,本片 **82 支全部是 `0 / n`**(§2.2);**讀到的表** 只列 PO inline SQL 或 `Model.xsd` 結果集名能看到的,「黑箱」代表 SQL 全在版控外的 SP 裡;**查詢條件** 「參數化」= 走 `AddInParameter`,「串接」= 有 `strSQL += "…"` 組句(本片的串接都是**組固定句型**,使用者輸入仍走 bind 變數,見 §7 各群註記)。

### 3.1 AML 洗錢防制與交易監控(8 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR168` | 現金交易監控表 | `INFDR168_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR169` | 既有客戶交易異常表(+受益人明細) | `INFDR169_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR170` | 新客戶交易異常表(+受益人明細) | `INFDR170_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR185` | 單日交易異常表-交易次數 | `INFDR185_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR186` | 單日交易異常表-交易累計金額 | `INFDR186_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR187` | 客戶國藉為高風險國家名單及交易清冊 | `INFDR187_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR188` | 弱勢族群交易回訪報表_境內 | `INFDR188_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR245` | 疑似洗錢控管表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |

### 3.2 實體受益憑證與併戶(10 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR200` | 受益人併戶資料查核表 | `INFDR200_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR201` | (空字串,見 §0.5)大憑證明細 | Basic_PO | **死** | SP×1、inline SQL | `OFD724` `OFD721` `OFD0811` `BMS001` | 0 / 1 | 1 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR202` | 總額單位數計算表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR203` | 大憑證總單位數計算附表 | Basic_PO | **死** | SP×1、inline SQL | `OFD312` | 0 / 1 | 1 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR204` | 受益憑證(憑證號碼)作廢明細表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR205` | 受益憑證(紙張流水號)作廢明細表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR206` | 受益憑證(憑證號碼)作廢明細表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR207` | 未領取受益憑證明細表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR210` | 受益憑證中英文持有單位證明 | `INFDR210_PO` | 活 | SP×1、inline SQL | `OFD303A` | 0 / 1 | 2 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR244` | 受益憑證(紙張流水號)明細表 | `INFDR244_PO` | 活 | SP×1、inline SQL | `OFD038A` `OFD081A` | 0 / 1 | 1 張,全在版控+csproj | 參數化+串接 | 全在 |

### 3.3 扣款帳號核印(5 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR221` | 扣款帳號核印未回報明細表 | `INFDR221_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR222` | 核印費請款單彙總表 | `INFDR222_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR223` | 核印失敗通知書 | `INFDR223_PO` | 活 | SP×1、inline SQL | `OFD711` `OFD701` | 0 / 1 | 2 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR224` | 核印回報處理作業(無報表) | `INFDR224_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | **無** | 參數化 | 全在 |
| `NFDR225` | 核印狀態一覽表 | `INFDR225_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |

### 3.4 銷售額度控管 / 匯款比對 / 退匯 / 交易查核(9 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR231` | 基金銷售額度控管表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR232` | 基金額度控管表列印作業 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR233` | 銷售機構基金額控轉申購統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR236` | 匯款比對查核表(申購資料) | Basic_PO | **死** | SP×3 | —(黑箱) | 0 / 3 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR237` | 匯款比對查核表(匯款資料) | Basic_PO | **死** | SP×3 | `OFD0819` | 0 / 3 | 4 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR240` | 退匯通知表 / 客戶買回退匯統計表 / 買回價金退匯尚未完成重匯明細表 | `INFDR240_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 3 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR241` | 快速輸入查核表(基金/銷售機構,分頁/不分頁) | Basic_PO | **死** | inline SQL | `OFD081V` `OFD038` | 0 / 0 | 4 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR242` | 基金申贖每日彙總表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR243` | 短線交易明細表 / 短線交易彙總表 | `INFDR243_PO` | 活 | SP×1、inline SQL | `OFD081V` `OFD038A` | 0 / 1 | 2 張,全在版控+csproj | 參數化+串接 | 全在 |

### 3.5 通路報酬:手續費 / 銷售服務費 / 獎金(8 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR171` | 代理收付買回費統計表 | `INFDR171_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR352` | 銷售機構遞延銷售手續費-合計攤銷總表 / 攤銷明細表 | `INFDR352_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | **無** | 參數化 | 全在 |
| `NFDR431` | 銷售服務費彙總表 / 銷售服務費基金明細表(銷售機構軸) | `INFDR431_PO` | 活(`dbTA` 變體) | SP×1 | —(黑箱) | 0 / 1 | 6 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR432` | 銷售服務費彙總表 / 基金明細表 / 明細表-平均餘額(受益人群組軸) | `INFDR432_PO` | 活(`dbTA` 變體) | SP×1 | —(黑箱) | 0 / 1 | 5 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR434` | 元富證券手續費明細清冊(股票型) / 彙總表〔客戶特定〕 | `INFDR434_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 3 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR436` | 銷售機構/券商手續費報表(四組 SP) | `INFDR436_PO` | 活 | SP×4 | —(黑箱) | 0 / 4 | 5 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR437` | 元富證券手續費統計報表及下載作業〔客戶特定〕 | `INFDR437_PO` | 活 | SP×1 | `SALR905T1`(註解內) | 0 / 1 | **無** | 參數化 | 全在 |
| `NFDR933` | 通路年度提撥人員銷售獎金報表 / 通路人員銷售獎金報表 | `INFDR933_PO` | 活 | SP×1、inline SQL | `OFD922A` `LOG_OFD931A` | 0 / 1 | 2 張,全在版控+csproj | 參數化+串接 | 全在 |

### 3.6 營運統計 `5xx`(17 支,15 支死)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR501` | 各銷售機構別統計表 | Basic_PO | **死** | SP×2 | —(黑箱) | 0 / 2 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR502` | 開戶統計明細表 / 開戶統計彙總表 | Basic_PO | **死** | SP×2 | —(黑箱) | 0 / 2 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR503` | 基金受益人戶數統計表 / 各部門受益人戶數統計表 | Basic_PO | **死** | SP×2 | —(黑箱) | 0 / 2 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR504` | 各基金申購、贖回統計表(明細/彙總) | Basic_PO | **死** | SP×3 | —(黑箱) | 0 / 3 | 6 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR505` | 申購N元以上統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR506` | 定期定額基金扣款分析彙總表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR507` | 定期定額扣款金額分析表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR508` | 定期定額佔基金規模之比例表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR509` | 定期定額銷售分析表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR510` | 定期定額扣款統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR511` | 交易作業量表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR512` | 人員處理交易量表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR513` | 各基金交易量明細表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR514` | 作業統計總表 | `INFDR514_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR515` | 交易來源統計表 / KYC來源統計表 | `INFDR515_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR516` | 受益人持有基金比率表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR517` | 銷售買回統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |

### 3.7 淨銷售統計 `7xx`(7 支,全死)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR701` | 直銷部門淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR702` | 通路業務部門淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR703` | 櫃台部門淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR704` | 指定用途淨銷售統計表 | Basic_PO | **死** | SP×1、inline SQL | `BMS001` | 0 / 1 | 1 張,全在版控+csproj | 參數化+串接 | 全在 |
| `NFDR705` | 通路淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR706` | 特殊受益人淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR707` | 基金淨銷售統計表 | Basic_PO | **死** | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |

### 3.8 結餘 / 餘額 / 業務單位 / 稽核 `8xx`(15 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR800` | 受益人身份統計表 | `INFDR800_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR801` | 結餘日期受益人別資料分析表 | `INFDR801_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR802` | 每月各基金資料變動表 | `INFDR802_PO` | 活 | SP×2 | —(黑箱) | 0 / 2 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR803` | 新基金募集每日銷售表 | `INFDR803_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR804` | 股務作業筆數分攤表 | `INFDR804_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR805` | 業務單位日報表 / 業務單位期間報表 | `INFDR805_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR806` | Subscription & Redemption Summary Report (By ***) | `INFDR806_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR807` | Open New Account and Data Moving | `INFDR807_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR809` | 缺件統計表 | `INFDR809_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR810` | 缺件結存比率下載作業-稽核 | `INFDR810_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | **無** | 參數化 | 全在 |
| `NFDR811` | 客戶明細檔 / 銷售彙總檔(Excel) | `INFDR811_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | **無** | 參數化 | 全在 |
| `NFDR812` | 預估申、贖基金日報表 / Subscription & Redemption Daily Statement / 公會版 | `INFDR812_PO` | 活 | SP(名在 Ctl) | —(黑箱) | 0 / 0 | 3 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR814` | 餘額統計表 / 業務單位餘額統計表 | `INFDR814_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR815` | 銷售單位彙總表 / 每日業務員彙總表 / 業務員贖回統計表 | `INFDR815_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR816` | 手續費收入 / 手續費收入(單筆及定額) | `INFDR816_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |

### 3.9 投信投顧公會英文申報(3 支)

| 代號 | 報表中文名 | PO 基底 | `m_db` | 資料來源 | 讀到的表 | SP 在版控 | `.rpt` | 查詢條件 | csproj |
|---|---|---|---|---|---|---|---|---|---|
| `NFDR558` | Equity / Fix Income / Balance Fund Subscription-Redemption(公會英文) | `INFDR558_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 1 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR559` | Savings Plan Investors of Monthly Subscription / Taiwan Fund Industry Growth Statistics | `INFDR559_PO` | 活 | SP×1 | —(黑箱) | 0 / 1 | 2 張,全在版控+csproj | 參數化 | 全在 |
| `NFDR560` | Taiwan Fund Industry Statistics | `INFDR560_PO` | 活 | SP×2 | —(黑箱) | 0 / 2 | 2 張,全在版控+csproj | 參數化 | 全在 |

## 4. 維護畫面(M)

**本模組沒有 M 畫面。** 82 支全部是 R。理由與前片相同,見 `nfdr1.md §4`:`NFD` 是純輸出層,不維護任何資料。

一個**本片才出現的例外要講清楚**:有 4 支 R 畫面會**寫資料庫**,但它們仍然不是 M 畫面(沒有 EVA 四眼、沒有 `MasterTable` / `DetailTable`、沒有覆核流程):

| 支 | 寫什麼 | 為什麼 | 錨點 |
|---|---|---|---|
| `NFDR223` | `UPDATE OFD701 SET RECEIPT_DOC_ID2='Y'` | 列印核印失敗通知書後回寫「已印」旗標 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:254-266` |
| `NFDR201` | `UPDATE [OFD724]` + `UPDATE [OFD721]` | 列印大憑證後回寫列印註記。**注意方括號是 T-SQL 語法,在 Oracle 上是語法錯誤**,而且這支的 `m_db` 是死的 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:201`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:214` |
| `NFDR224` | `ExecuteNonQuery` 呼叫 `S_TA_NFDR224_GET` | 這支根本不是報表,是核印回報的處理作業(無 `.rpt`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR224_PO.cs:76` |
| `NFDR437` | SP 內寫全域暫存表,PO 用 `Rollback()` 清掉 | 見 §7.5.3 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR437_PO.cs:98` |

**這修正了 `nfdr1.md §0.1` 的「只讀不寫」。** 精確的說法是:**`NFD` 不擁有業務事實,但會回寫「已印」類的旗標,而且會寫到別人的表上**。改 `OFD701` / `OFD721` / `OFD724` 的人要知道 `NFD` 報表會動它們。

## 5. 查詢畫面(I)

**本模組沒有 I 畫面**,理由同 `nfdr1.md §5`。

本片有兩支**長得像 I 畫面的 R 畫面**:`NFDR810`(缺件結存比率下載作業-稽核)與 `NFDR811`(客戶明細檔 / 銷售彙總檔),它們沒有 `.rpt`、只出 Excel、而且「執行」鈕跳「此項功能無作用」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR810.cs:140`)。從畫面型別鐵律(`ofdr1.md §0.2`)看它們是 R,從實際行為看它們是「下載工具」。

## 6. 批次(B)與 WindowsService

**本模組沒有 B 畫面,也沒有任何 WindowsService**,理由同 `nfdr1.md §6`。

本片唯一沾到「批次」的是 `NFDR812` 產生的 `DSR{yyyyMMdd}.mon` 交換檔(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:209`)——**這是人手按出來的,不是排程跑的**,repo 內找不到任何排程設定。誰去撿這個檔、送去哪裡,在 `ATLAS` 之外。

## 7. 報表(R)——主體

```text
[圖] NFDR800 到 NFDR816 這組全庫最長連號：程式層高度相似的模板家族，業務層卻是十二種不同的報表
圖中文字:① 程式層：15 支共用同一個 PO 模板（相似度 difflib ratio） / NFDR800 模板本尊 / 123 行 · C_RES · 三參數 / 806 ↔ 807 = 0.996 / 除代號外一字不差 / 800 ↔ 801 = 0.978 / 參數完全相同 / 810 ↔ 811 = 0.977 / 811 多一個 RefCursor / 805 ↔ 815 = 0.963 / 只差參數名 / 809 ↔ 810 = 0.949 / 11 組配對 > 0.9 / 平均 0.77 / 812 最低 0.40 / 全群唯一異類 / ② 業務層：15 支是 12 種不同的業務 / 800 801 受益人身份 / 結餘日結構分析 / 802 每月資料變動 / 803 新基金募集 / 每日銷售 / 804 股務作業分攤 / 筆數 / 805 815 業務單位 / 日報／期間／業務員 / 806 807 公會英文 / 申贖彙總／開戶轉移 / 809 810 811 缺件 / 統計／比率／明細檔 / 812 預估申贖日報 / ＋DSR.mon 交換檔 / 814 餘額統計 / 816 手續費收入 / ③ 結論：模板相同 ≠ 系列相同（對照 ofdr1 的連號結論） / 連號 = 同一個模板 / 推翻「連號≠同系列」 / 連號 ≠ 同一份報表 / 支持「連號≠同系列」 / 模板缺陷 15 支一起中 / catch 裸 Rollback / 沒有共用基底可一次改 / 只能改 15 個檔
```

*圖:圖 4 800-816 群結構(§7.8.1)。橘框=本文的測量結論;橘虛框=異類或模板層級的缺陷。相似度用 difflib SequenceMatcher 對剝註解後的 PO 全文計算，比 Jaccard 嚴格(它看順序)。*

### 7.0 怎麼讀這一章

**按群寫,不按支寫。** 每一群的結構固定:業務是什麼 → 群內分工表 → 這群特有的寫法 / 陷阱 → 挑 1–3 支深寫 → 其餘表格帶過(清單已在 §3,這裡只補 §3 放不下的東西)。

三個貫穿全章的判準,先講一次,後面不重複:

| 判準 | 一句話 |
|---|---|
| **這支活不活** | 看 §3 的 `m_db` 欄。「死」= 按預覽即 NRE(附錄 E-01)。本片 37 支死 |
| **卡控在哪一層** | `DoValidate()` 在 UI(**阻擋**),SP 內的過濾在版控外(**過濾,無提示**)。本片**看得到的卡控全在 UI**,看不到的全在 SP |
| **查無資料怎麼辦** | 本片 82 支只有 9 支會跳「查無資料」提示,其餘 73 支**靜默印一張空報表**(附錄 E-06) |

### 7.1 AML 洗錢防制與交易監控(8 支)

**業務**:洗錢防制法與投信投顧公會自律規範要求的交易監控名單。這是本片**唯一全新的法遵業務線**,而且是後期加的——8 支全部走 `INFDRxxx_PO` + Oracle,一支舊寫法都沒有,只有 `NFDR245`(疑似洗錢控管表)例外,它停在 `Basic_PO`、`m_db` 是死的。

#### 7.1.1 群內分工

| 支 | 監控什麼 | 主要門檻參數 | 活 |
|---|---|---|---|
| `NFDR168` | 現金交易(大額現金申購) | `CASH_ALLOT_SINGLE`(單筆)、`CASH_ALLOT_TOTAL`(累計) | 活 |
| `NFDR169` | **既有客戶**的交易異常 | `TRAN_DATE` 區間 + 是否含轉申購 | 活 |
| `NFDR170` | **新客戶**的交易異常 | `OPEN_DATE` 區間 + 是否含轉申購 | 活 |
| `NFDR185` | 單日交易**次數**異常 | `TRAN_DATE` 單日 + 是否含定期定額 / 是否含 `NFDR168` 已列者 | 活 |
| `NFDR186` | 單日交易**累計金額**異常 | 同上 | 活 |
| `NFDR187` | 客戶國籍為高風險國家 | `TRAN_DATE` 區間 + 是否只列有交易者 | 活 |
| `NFDR188` | **弱勢族群**交易回訪 | `ALLOT_DATE` 區間 + `AGENT_ID` | 活 |
| `NFDR245` | 疑似洗錢控管 | `DATA_DATE` + `ALLOT_AMT` / `REDEM_UNIT` 門檻 | **死** |

`NFDR185` / `NFDR186` 是同一份報表的兩個口徑(次數 / 金額),PO 幾乎相同;`NFDR169` / `NFDR170` 是同一份報表的兩個客群(既有 / 新),連 `Model.xsd` 的結果集名都共用(§2.5 的抄錯)。

#### 7.1.2 `NFDR168` 現金交易監控表(本群最完整的一支)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs`,155 行,兩個 method:取數 + **一個前置檢核**。

取數(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:55-74`)是本片最標準的寫法:`GetStoredProcCommand("S_TA_NFDR168_GET")` → 五個 `AddInParameter`(`iFUND_ID` / `iALLOT_DATE_ST` / `iALLOT_DATE_ED` / `iCASH_ALLOT_SINGLE` / `iCASH_ALLOT_TOTAL`)→ `AddOutParameter("OutTB", RefCursor)` → `LoadDataSet`。**全部走 bind 變數,沒有字串串接。**

值得記的三件事:

1. **境內外不分**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:65-67` 有一段註解:「2015/10/30 境內外資料一起印,不區分」,`iSOURCE_CD` 參數被註解掉了。這與 `nfdr1.md §0.1` 引用的 `NFDR159_PO.cs:107` 寫死 `SHORE_ID = '2'` **方向相反**——同一個模組裡,有的報表寫死只印境內,有的刻意拿掉境內外區分。**兩種都不是設定,都是寫死在程式裡。**

2. **前置檢核 `ChkAllotDateIsClose` 會放行未結轉的日期**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:106-118`:

```
SELECT COUNT(0) FROM dual WHERE EXISTS (
  SELECT * FROM OFD303A
  WHERE (NVL(:FUND_ID,' ') = ' ' OR OFD303A.FUND_ID = :FUND_ID)
    AND OFD303A.ALLOT_CTL_CODE <> '3'
    AND OFD303A.CTL_DATE BETWEEN :ALLOT_DATE_ST AND :ALLOT_DATE_ED )
```

`ALLOT_CTL_CODE <> '3'` 在 Oracle 是三值邏輯:**`ALLOT_CTL_CODE` 為 `NULL` 的那幾天,`<> '3'` 的結果是 `UNKNOWN`,不算 `TRUE`,那一天就不會被算成「未結轉」**。結果是檢核通過、報表照印,印出來的是還沒結轉的半套資料。要抓 NULL 必須寫 `NVL(ALLOT_CTL_CODE,'X') <> '3'`。卡控結果:**過濾(無提示)**——使用者不會看到任何警告。

1. **`NVL(:FUND_ID,' ') = ' '` 是「全部基金」的慣用寫法**,本片到處都是。它的副作用是:**傳空字串 `''` 進來時,Oracle 把 `''` 當 `NULL`,`NVL` 補成 `' '`,條件成立 → 查全部**。這是刻意的,不是 bug,但換成 SQL Server 就不成立(SQL Server 的 `''` 不是 `NULL`)。遷移過的和沒遷移的混在同一個模組裡,這一點要特別小心。

#### 7.1.3 `NFDR187` 高風險國家名單:唯一一支有「只列有交易者」開關的

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR187.cs:63` 把 `uchkTRAN_YN.Checked` 轉成「是 / 否」餵給 Crystal,同時當成 SP 參數。勾起來 = 只列期間內有交易的高風險國籍客戶,不勾 = 列全部。

**這是法遵報表裡最需要小心的一種開關**:勾錯方向,少印的那一半不會有任何提示。報表標頭會印出「是 / 否」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR187.cs:63`),這是唯一能事後追查的痕跡。卡控結果:**過濾(無提示,但標頭有記錄)**。

#### 7.1.4 本群其餘支(表格帶過)

| 支 | 要記的一件事 | 錨點 |
|---|---|---|
| `NFDR169` / `NFDR170` | 報表名在 `m_ActiveReportName` 而不是 `SetQueryParameters` 的第三參,grep 報表名時兩種都要找 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR169.cs:152`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR170.cs:155` |
| `NFDR170` | `Model.xsd` 的結果集叫 `NFDR169` / `NFDR169_1`(§2.5) | `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR170Model.xsd` |
| `NFDR185` / `NFDR186` | 三個 Y/N 開關(含轉申購 / 含定期定額 / 含 `NFDR168` 已列者)都只是 SP 參數,邏輯在版控外 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR185.cs:71-79` |
| `NFDR188` | 唯一一支報表名寫在 `GetReportFileTitle()` 回傳的 `KeyValuePair` 裡;Excel 檔名也用同一個 Key | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR188.cs:90-95` |
| `NFDR245` | **死**。疑似洗錢控管表現在印不出來,而且本片沒有第二支做同一件事 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR245_PO.cs:19` |

> **`NFDR245` 要單獨點名**:它和 `NFDR168`(現金交易監控)雖然都是 AML,但門檻參數不同(`NFDR245` 吃 `ALLOT_AMT` + `REDEM_UNIT`,`NFDR168` 只吃現金申購金額),**不是同一份報表**。`NFDR245` 死掉等於「疑似洗錢控管表」這份少了。已列入 §0.3 的缺口清單旁註。

### 7.2 實體受益憑證與併戶(10 支)

**業務**:紙本受益憑證的發行、作廢、未領取、持有證明,加上受益人併戶。這一群是**全片最老的一塊**——10 支裡 7 支的 `m_db` 是死的,而且**死的那 7 支的 inline SQL 全部是 T-SQL 語法**(方括號、`ISNULL`、`CONVERT(VARCHAR, …)`、`dbo.PADLeft`、`+` 串字串),在 Oracle 上就算 `m_db` 活了也跑不起來。

#### 7.2.1 群內分工

| 支 | 做什麼 | 軸 | 活 |
|---|---|---|---|
| `NFDR200` | 受益人併戶資料查核表 | 消滅戶號 / 存續戶號 | 活 |
| `NFDR201` | 大憑證明細(**報表名是空字串**) | 憑證 | **死** |
| `NFDR202` | 總額單位數計算表 | 單位數 | **死** |
| `NFDR203` | 大憑證總單位數計算附表 | 單位數 | **死** |
| `NFDR204` | 受益憑證(憑證號碼)作廢明細表 | 憑證號碼 | **死** |
| `NFDR205` | 受益憑證(紙張流水號)作廢明細表 | 紙張流水號 | **死** |
| `NFDR206` | 受益憑證(憑證號碼)作廢明細表(**與 `NFDR204` 同名**) | 憑證號碼 + 憑證日期 | **死** |
| `NFDR207` | 未領取受益憑證明細表 | 憑證 | **死** |
| `NFDR210` | 受益憑證中英文持有單位證明 | 受益人 + 結存日 | 活 |
| `NFDR244` | 受益憑證(紙張流水號)明細表 | 紙張流水號 | 活 |

**`NFDR204` 與 `NFDR206` 同名**(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR204.cs:51` 的註解版、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR206.cs:119`),差別在 `NFDR206` 多了「憑證日期」與「基金代碼擇一輸入」的驗證(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR206.cs:42`)。**使用者從選單上分不出這兩支**——這是本片最容易讓人選錯畫面的一組。

#### 7.2.2 `NFDR201` 大憑證:本片唯一「字串串接 + 寫回 + T-SQL + 死 `m_db`」四殺

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs`,309 行,是本群最長的 PO。四個問題疊在一起:

1. **`m_db` 恆 `null`**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:19`)——按預覽就 NRE。

2. **全檔 56 處 `strSQL += "…"` 字串串接**,組出來的是 T-SQL:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:101-112` 用 `[OFD724]` 方括號、`ISNULL(…)`、`CONVERT(VARCHAR, …)`。**在 Oracle 上是語法錯誤**,不是慢,是跑不起來。

3. **會寫回兩張表**:`UPDATE [OFD724]`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:201`)與 `UPDATE [OFD721]`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:214`),包在一個 `printupdatetrans` 交易裡。

4. **第二段 `ExecuteNonQuery` 的失敗處理被註解掉了**。第一段失敗會 `printupdatetrans.Rollback()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:251`),第二段的同一行**是註解**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:259`),然後直接 `printupdatetrans.Commit()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:266`)。**也就是說:`OFD724` 更新成功、`OFD721` 更新失敗(0 筆)時,交易照 Commit,兩張表的列印註記從此不一致。**

還有第 5 點:兩處 `AddResultRow(true, 1, "")` 的筆數都是**寫死的 `1`**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:265`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:269`),不是實際更新筆數——這是型錄裡「`i = 1;` 蓋掉 `ExecuteNonQuery`」的同型。

第 4 點是**真正會咬人的那個**,因為它與 `m_db` 死不死無關——哪天有人把 `m_db` 補活了,這個半套 Commit 就會生效。

**串接的部分要說公道話**:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs` 的串接組的是**固定句型**,使用者輸入仍然走 `@參數`,**不是 SQL injection**。問題在語法方言,不在安全。

#### 7.2.3 `NFDR210` 受益憑證中英文持有單位證明:一道永遠通過的結帳卡控

這是**本片嚴重度最高的單一缺陷**,而且它發生在一支活的報表上。

UI 端的訊息寫得很清楚:「結存日期 各基金必須皆要完成結帳,才可列印」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR210.cs:88`),卡控結果應該是**阻擋**。實作在 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:101-133` 的 `ChkIsCtl`:

```
string strSQL = "" + Environment.NewLine;
strSQL += " SELECT COUNT(*)                                      " + Environment.NewLine;
strSQL += " FROM OFD303A                                         " + Environment.NewLine;
strSQL += " WHERE CTL_DATE=:BALDATE                              " + Environment.NewLine;
strSQL += "     AND (ALLOT_CTL_CODE <> '3'                       " + Environment.NewLine;
strSQL += "        OR REDEM_CTL_CODE <> '4'                      " + Environment.NewLine;
strSQL += "        OR (RSP_CLS_CD = 'Y' AND RSP_CTL_CODE <> '3') " + Environment.NewLine;

using (DbCommand cmd = m_db.GetSqlStringCommand(strSQL))
```

**第 111 行開的 `(` 沒有人關。** 串接到第 113 行就結束了,下一行直接進 `using`。送到 Oracle 是 `ORA-00907: missing right parenthesis`。

然後看例外處理(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:128-132`):

```
catch (Exception ex) { CommonExceptionBlocker.HandleBusinessException(ex); }
return isChk;
```

`isChk` 在 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:103` 初始化為 `true`,而 `true` 的語意是「檢核通過」。**語法錯誤 → 丟例外 → 被吃掉 → 回傳 `true` → 卡控放行。**

三重問題疊在同一個 method 裡:

| 層 | 問題 | 若單獨存在的後果 |
|---|---|---|
| 1 | `AND (` 缺右括號 | SQL 執行失敗 |
| 2 | `catch (Exception)` 吞例外 | 失敗變成靜默 |
| 3 | `isChk` 預設 `true` = 通過 | 靜默失敗 = **fail-open** |
| 4(即使前三項修好) | `ALLOT_CTL_CODE <> '3'` 對 `NULL` 回 `UNKNOWN` | 沒有結帳記錄的基金**仍然漏抓** |

**結論:「各基金必須皆完成結帳才可列印」這道卡控,從來沒有生效過。** 對外開立的「持有單位證明」可能拿的是還沒結帳的單位數。卡控結果實際上是:**記錄不擋**(連記錄都沒有,例外被 `CommonExceptionBlocker` 吃了)。嚴重度 **高**,附錄 E-02。

修法(不在本文範圍,只列必要條件):補右括號 → `isChk` 預設改 `false` 或在 `catch` 內明確設 `false` → 四個比較全部包 `NVL(…, 'X')`。**四件事要一起做,只補括號會讓一批原本印得出來的證明突然印不出來。**

#### 7.2.4 本群其餘支(表格帶過)

| 支 | 要記的一件事 | 錨點 |
|---|---|---|
| `NFDR200` | 唯一一支在 UI 檢查「消滅戶號 不得等於 存續戶號」的;卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR200.cs:82` |
| `NFDR202` | 只有 4 個 `m_db` 用點,是本群最小的 PO;**有「查無資料」提示**(少數) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR202.cs:204` |
| `NFDR203` | 結果集借用 `OFD312` 表名;inline SQL 用 `dbo.PADLeft(…)` + `'-'` 串接組憑證號,**T-SQL 專用** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR203_PO.cs:90` |
| `NFDR204` / `NFDR206` | 同名兩支,見 §7.2.1 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR206.cs:119` |
| `NFDR205` | UI 有四道「起迄必須皆(不)填寫 / 起不可大於迄」驗證,是本群驗證最完整的;卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR205.cs:42-53` |
| `NFDR207` | 未領取憑證清單,`m_db` 死 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR207_PO.cs:18` |
| `NFDR244` | 活。inline SQL 只用來撈基金下拉清單(`OFD038A` + `OFD081A`),主資料走 `s_TA_NFDR244_Get` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR244_PO.cs:103-114` |

### 7.3 扣款帳號核印(5 支)

**業務**:定期定額扣款帳號要送銀行核對印鑑(核印)。這一群管的是核印的送件、回報、失敗通知與請款。5 支**全活**,是本片唯一一群零死亡的舊業務線。

#### 7.3.1 群內分工

| 支 | 在核印流程的哪一步 | 輸出 |
|---|---|---|
| `NFDR221` | 送出後未回報的追蹤 | 扣款帳號核印未回報明細表 |
| `NFDR222` | 向銀行請款 | 核印費請款單彙總表 |
| `NFDR223` | 回報失敗 → 通知受益人 | 核印失敗通知書(**會回寫已印旗標**) |
| `NFDR224` | 回報資料的處理作業 | **無報表**,純 `ExecuteNonQuery` |
| `NFDR225` | 全流程狀態一覽 | 核印狀態一覽表 |

#### 7.3.2 `NFDR223` 核印失敗通知書:印完就回寫,而且回寫不回報筆數

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs`,307 行,本群最長。它做兩件事:取核印失敗清單(`S_TA_NFDR223_GET`)+ **列印後把 `OFD701.RECEIPT_DOC_ID2` 更新成 `'Y'`**。

回寫的 SQL(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:253-265`)用 **9 個欄位當條件**(`SEAL_TYPE` / `SUB_BANK_CODE` / `SUB_ACC_NO` / `RSP_NO` / `RSP_SRNO` / `RSP_CHG_NO` / `RSP_CHG_SRNO` / `ACC_SUB_ID` / `SUB_ID_NO`),全部走 bind 變數,**沒有 SQL injection 風險**。

三個要記的:

1. **原本還有第 10 個條件,被註解掉了**:`// AND RECEIPT_DOC_ID1 <> 'Y'`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:267`)。拿掉之後,**已經印過第一份文件的那些筆也會被更新**。這是刻意還是忘了,程式裡看不出來。

2. **筆數不回報**。`j` 一路累加 `ExecuteNonQuery` 的回傳值(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:283`),但最後一行是 `AddResultRow(true, 0, "")`——**硬寫 0**;真正帶 `j` 的那一行是註解(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:289`)。使用者印完不知道更新了幾筆。這是型錄裡「`i = 1;` 蓋掉 `ExecuteNonQuery`」的近親。

3. **`trans.Commit()` 被註解掉,`m_db.Rollback()` 卻留著**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:286` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:293`)。正常路徑不 Commit(靠連線關閉時的隱式行為),例外路徑卻對一個**沒有明確開啟的交易**呼叫 `Rollback()`。這正是型錄裡「對已 Commit 的交易 `Rollback()` 吃掉原例外」的變形:`Rollback()` 自己若丟例外,原始的業務例外就被蓋掉,`CommonExceptionBlocker.HandleBusinessException(ex)` 那一行永遠跑不到。

#### 7.3.3 本群其餘支(表格帶過)

| 支 | 要記的一件事 | 錨點 |
|---|---|---|
| `NFDR221` | `Seal_Type` 三值(一般 / 財金 / 全部)直接組中文字串餵 Crystal | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR221.cs:51-57` |
| `NFDR222` | `FormType` 的 `2` 沒有中文名(§2.7);卡控:**過濾(無提示)** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:48-51` |
| `NFDR224` | 無 `.rpt`,是處理作業;成功與否靠 `ReturnMessageColumn` 是不是「無符合的資料」判斷,**用中文字串比對當控制流** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR224.cs:77` |
| `NFDR225` | UI 有三段受益人 ID 格式檢查**全部被註解掉**(統編格式 / 身分證格式 / 兩者皆非),現在什麼都不擋 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR225.cs:57-85` |

`NFDR225` 那三段註解掉的驗證值得記:**原本是「詢問 / 阻擋」,現在是「不擋」**。輸入格式錯誤的 ID 會直接送進 SP,查不到就印空白。

### 7.4 銷售額度控管 / 匯款比對 / 退匯 / 交易查核(9 支)

**業務**:三件不太相干的事被排在同一段代號裡——基金銷售額度(`231`–`233`)、匯款比對與退匯(`236` `237` `240`)、交易查核(`241`–`243`)。9 支裡 6 支死。

#### 7.4.1 群內分工

| 支 | 業務 | 活 | 特徵 |
|---|---|---|---|
| `NFDR231` | 基金銷售額度控管表 | **死** | 84 行,本片最小的 PO 之一 |
| `NFDR232` | 基金額度控管表列印作業 | **死** | 參數名帶 `@`(SQL Server 風格) |
| `NFDR233` | 銷售機構基金額控轉申購統計表 | **死** | 10 個 `@` 參數,含 `@striEC` / `@striIVR` 交易途徑 |
| `NFDR236` | 匯款比對查核表(申購資料) | **死** | 3 支 SP(All / Detail / Excel) |
| `NFDR237` | 匯款比對查核表(匯款資料) | **死** | 3 支 SP,結果集借 `OFD0819` |
| `NFDR240` | 退匯通知表 / 買回退匯統計 / 未完成重匯明細 | 活 | 一支畫面三張 `.rpt` |
| `NFDR241` | 快速輸入查核表 | **死** | 4 張 `.rpt`(基金 / 銷售機構 × 分頁 / 不分頁) |
| `NFDR242` | 基金申贖每日彙總表 | **死** | 只吃一個 `@date` |
| `NFDR243` | 短線交易明細表 / 彙總表 | 活 | 3 個 `RefCursor` 出口 |

#### 7.4.2 `NFDR241` 快速輸入查核表:本片唯一把 `EXEC` 寫進字串的

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:132` 是一行 700 字元的字串:

```
sql = "EXEC s_NFDR241_FUND_Get @striBF_NO = @xstriBF_NO, @striID_NO = @xstriID_NO, …";
```

然後 `m_db.GetSqlStringCommand(sql)`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:140`)。

**這是 T-SQL 的 `EXEC proc @p = @var` 語法,Oracle 沒有。** 就算 `m_db` 補活了,這支也跑不起來——要改寫成 `GetStoredProcCommand` + `AddInParameter`,也就是**整支 PO 重寫**。

同一支的另一段(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:50-64`)撈基金下拉清單,用 `LEFT JOIN [OFD038]` + `@FUND_GROUP` 參數——**方括號、`@` 參數,同樣是 T-SQL**。對照隔壁 `NFDR243` 的同一段(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR243_PO.cs:59-72`),它已經改成 `LEFT JOIN OFD038A` + `:FUND_GROUP`(Oracle bind)。**兩支相鄰的報表,同一段程式碼,一支遷了一支沒遷。**

`LEFT JOIN` 這個選擇是對的——如果寫成 `INNER JOIN`,`OFD038` 裡沒有分類的基金會從下拉清單消失。本片 82 支的 PO 內**沒有任何一處 `INNER JOIN`**(全庫實測),所以 `nfdr1.md` 在 `NFDR123` 抓到的那型缺陷,本片在**看得到的程式裡沒有同型**。**但這不等於沒有**——72 支的 SQL 在版控外的 SP 裡,那裡有沒有 `INNER JOIN` 吃掉法遵名單,repo 內查不到。這一點必須明講。

#### 7.4.3 `NFDR236` / `NFDR237` 成對報表:同一件事的兩個方向

`NFDR236` 是「從申購看匯款」,`NFDR237` 是「從匯款看申購」。兩支的 PO 長度幾乎一樣(277 / 305 行)、SP 命名對稱(`s_NFDR23x_All_Get` / `_Detail_Get` / `_Excel_Get`)、`Model.xsd` 結果集對稱(`NFDR236_ALL` / `_D` / `_SUM` vs `NFDR237_ALL` / `_D` / `_SUM`)。

**不對稱的地方有兩處,兩處都在 `NFDR237`**:

1. `NFDR237` 多一個 `@REMIT_ACC_NO_LIST` 參數(匯款帳號清單),`NFDR236` 沒有。

2. `NFDR237Model.xsd` 有 **30 個 `msdata:Caption`**,`NFDR236Model.xsd` **一個都沒有**。

`.rpt` 也不對稱:`NFDR236` 有 2 張(`RPS` / `RPS1`),`NFDR237` 有 4 張(`RPS` / `RPS1` / `RPS2` / `RPS3`),而**兩支都各有一張 `RPS` 沒被任何程式引用**(UI 只引用 `RPS1` 以上)。這是 §2.3 那兩張孤兒之外的另外兩張,但性質不同:`NFDR236RPS` / `NFDR237RPS` 看起來是「舊版型」,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR236.cs:77-92` 有四行被註解掉的 `SetQueryParameters`,證明它們曾經被用過。

**改一邊要想另一邊**,這是型錄裡「成對報表只改一邊」的標準案例。

#### 7.4.4 本群其餘支(表格帶過)

| 支 | 要記的一件事 | 錨點 |
|---|---|---|
| `NFDR231` | UI 強制先選基金代碼才能印;卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR231.cs:116` |
| `NFDR232` | 同一段 `SetQueryParameters` 出現兩次(兩個分支)但參數完全相同,分支沒有意義 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR232.cs:44`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR232.cs:60` |
| `NFDR233` | 交易途徑(臨櫃 / `EC` / `IVR`)至少要勾一種,卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR233.cs:65` |
| `NFDR240` | 一支畫面三張報表(退匯通知 / 統計 / 未完成重匯),三個結果集 `NFDR240_1`–`_3`;活 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR240.cs:89-97` |
| `NFDR242` | 只有一個參數 `@date`,是本片參數最少的報表;`DATE` 為必填,卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR242.cs:93` |
| `NFDR243` | 活。四個結果集(`_FUND` / `_CNTL` / `_BF` / `_TRADE`)對三個 `RefCursor`,**`_TRADE` 沒有對應的 out 參數** | `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR243Model.xsd` |

`NFDR243` 那個對不起來的結果集要留意:`Model.xsd` 宣告了 `NFDR243_TRADE`,PO 只開 `OutTB` / `OutTB2` / `OutTB3` 三個 `RefCursor`。**多出來的那張表在報表上永遠空白,不會報錯**——這就是 `nfdr1.md` 附錄 E-07 那一型。

### 7.5 通路報酬:手續費 / 銷售服務費 / 獎金(8 支)

**業務**:付給銷售通路的錢。8 支分三小群:代收付費用(`171`)、遞延銷售手續費攤銷(`352`)、銷售服務費與手續費(`431`–`437`),外加獎金(`933`)。**8 支全活**,是本片第二群零死亡的線,而且是**技術上最新的一群**。

#### 7.5.1 `NFDR431` / `NFDR432`:同一份報表的兩個軸,加兩張孤兒 `.rpt`

兩支的報表中文名幾乎一樣(「銷售服務費彙總表」「銷售服務費基金明細表」),差別在**分組的軸**:

|  | `NFDR431` | `NFDR432` |
|---|---|---|
| 主軸參數 | `AGENT_ID` + `AGENT_CODE`(銷售機構) | `BF_GRPCD` + `BFFundGrpcdForRebate`(受益人群組) |
| 期間參數 | `MONTH_S` + `MONTH_E` | `Month` + `Month_E` |
| 結果集 | `_SUM` `_Detail` `_DetailAVG` `_DetailDaily` `_YearsSUM` | **完全相同的五張** |
| `.rpt` | 6 張(含孤兒 `NFDR431RPS3_1`) | 5 張(含孤兒 `NFDR432RPS4`) |
| PO 成員名 | `dbTA`(**不是 `m_db`**) | `dbTA` |

**期間參數命名不一致**(`MONTH_S` vs `Month`)是本片最典型的複製貼上痕跡:兩支是同源,改軸的時候順手改了名字,只改一半。

PO 的分派邏輯寫在 `switch (Convert.ToInt32(REPORT_TYPE))`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR431_PO.cs:113-125`),`case 0`→`_SUM`、`case 1`→`_Detail`…。**`switch` 沒有 `default`**:`REPORT_TYPE` 落在列舉外時,`LoadDataSet` 完全不執行,`j` 維持 `0`,報表印出空白,**沒有任何提示**。卡控結果:**過濾(無提示)**。

`Convert.ToInt32(REPORT_TYPE)` 還有一個前提:`REPORT_TYPE` 必須是數字字串。UI 傳空字串進來時 `Convert.ToInt32("")` 丟 `FormatException`,被外層 `catch (Exception)` 吃掉 → 一樣空白。

兩張孤兒 `.rpt`(`NFDR431RPS3_1.rpt` / `NFDR432RPS4.rpt`)見 §2.3。**改這兩支報表版型時,先確認要改的是不是孤兒那張。**

#### 7.5.2 `NFDR352` 遞延銷售手續費:唯一一支只出 Excel 又有兩個報表名的

`NFDR352` 沒有 `.rpt`,只出 Excel。報表名寫在 `KeyValuePair` 裡,而且**檔名帶年月**:

```
r = new KeyValuePair<string, string>("合計攤銷總表" + this.udatCAL_MONTH_E.DateTime.ToString("yyyyMM"), "銷售機構遞延銷售手續費-合計攤銷總表");
r = new KeyValuePair<string, string>("攤銷明細表" + this.udatCAL_MONTH_E.DateTime.ToString("yyyyMM"), "銷售機構遞延銷售手續費-攤銷明細表");
```

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR352.cs:149`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR352.cs:152`。

兩個要記的:

1. **檔名用的是「迄」月(`CAL_MONTH_E`)**,但查詢條件是「起 ~ 迄」區間(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR352.cs:184` 檢查起不可大於迄)。**跨月查詢時,檔名只反映最後一個月**——存到同一個資料夾會互相覆蓋。

2. **轉出路徑是必填,但只在勾了 Excel 時才檢查**(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR352.cs:193`:「轉 Excel 檔的功能 需要輸入"轉出路徑"。」)。卡控:**阻擋**。

#### 7.5.3 `NFDR434` / `NFDR436` / `NFDR437` 三支手續費:交易處理三種寫法

三支是同一個業務(銷售機構手續費結算),`NFDR434` 與 `NFDR437` 都標明「元富證券」〔客戶特定〕,`NFDR436` 是通用版。**三支對交易的處理完全不同**:

| 支 | 正常路徑 | 例外路徑 | 意思 |
|---|---|---|---|
| `NFDR434` | `tran.Commit()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR434_PO.cs:107`) | `tran.Rollback()` | 標準 |
| `NFDR436` | `tran.Commit()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR436_PO.cs:139`) | `tran.Rollback()` | 標準 |
| `NFDR437` | **`tran.Rollback();//讓暫存table不儲存`**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR437_PO.cs:98`),`Commit` 那行是註解 | `tran.Rollback()` | **刻意不 Commit** |

`NFDR437` 的註解揭露了一件別處看不到的事:**這群報表的 SP 會往實體暫存表寫資料**。被註解掉的清理碼(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR437_PO.cs:80-82`)長這樣:

```
cmd.CommandText = string.Format("DELETE FROM SALR905T1 WHERE USERDOMAIN='{0}'",
                    Convert.ToString(model.DataEntity.Tables[table_name].Rows[0][0]));
```

三個觀察:

1. **`SALR905T1` 是 `SAL` 模組的表**,不是 `NFD` 的。`NFD` 的報表 SP 借別人的暫存表落地中繼資料。

2. **它有 `WHERE USERDOMAIN=…`**,也就是**有做 user 隔離**——這比 `ofdr2.md` 抓到的 `DB/SP/S_OTA_OFDR042_GET.SQL:514` 那個 `DELETE DSMR008T4;`(無 `WHERE`、無 user 欄)好。`NFD` 這一支**沒有踩到「兩人同按互相蓋掉」那型**。

3. **但它是字串串接**,`USERDOMAIN` 的值直接 `string.Format` 進 SQL。雖然整段被註解掉了,**現行的解法(`Rollback()`)更值得注意**:靠交易回滾讓暫存表資料不落地。這在 Oracle 上可行,但代價是 SP 內所有寫入都作廢——如果哪天 SP 需要留下稽核軌跡,這個 `Rollback()` 會把它一起吃掉。

**本片的 `NFDR073T*` 同型檢查結論**:`nfdr1.md §2.4` 那 17 張 `NFDR073T*` 暫存表**全部屬於前片**,本片 82 支**沒有自建任何 `NFDRxxxT*` 實體暫存表**(`NFDR514T2` / `NFDR515T2` / `NFDR811_T1` / `NFDR811_T2` 是 `Model.xsd` 的結果集名,不是資料庫的表)。本片唯一碰到的實體暫存表是別人的 `SALR905T1`,而且有 user 隔離。**「兩人同時按互相蓋掉」在本片查不到同型。**

#### 7.5.4 `NFDR933` 通路人員銷售獎金:為什麼獨自一支(必答問題 6)

`NFDR933` 是本片唯一的 `9xx`,和最近的 `NFDR816` 差 117 號。

**它是什麼**:兩張報表——「通路年度提撥人員銷售獎金報表」與「通路人員銷售獎金報表」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR933.cs:123`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR933.cs:128`),算的是付給通路人員的銷售獎金。

**為什麼獨自一支**——三條可查的線索:

1. **它的 PO 有本片唯一的「前置資料狀態檢查」**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:118` 先 `SELECT COUNT(*) FROM OFD922A`,沒有資料就不往下走;`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:156-158` 再查 `LOG_OFD931A`(`WHERE YEARS=:YEARS AND QDATE=:QDATE`),而且會判斷 `function_id` 是不是 `'OFDM931A'`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:172`)。

2. **`OFD922A` / `OFD931A` / `OFDM931A` 是 `OFD` 軌 `9xx` 的畫面與表**。也就是說 `NFDR933` 的代號是**跟著它所報告的那個作業(`OFDM931A`)走的**,不是跟著 `NFD` 自己的代號序列走。

3. **它有四個 `RefCursor` 出口**(`Out1`–`Out4`,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs`)與四張結果集(`NFDR933_1`–`_4`),是本片出口最多的一支。

**結論(必答問題 6)**:`NFDR933` 是**「後來加的、代號跟著上游作業走」**,不是「管理者專用」。它**沒有任何權限控制**(§0.7),與 `ofdi1.md` 對六支 `9xx` 畫面的實測結論(零權限控制)一致。**`9xx` 在 `ATLAS` 不代表特權,代表「掛在 `9xx` 作業後面的東西」。**

#### 7.5.5 本群其餘支(表格帶過)

| 支 | 要記的一件事 | 錨點 |
|---|---|---|
| `NFDR171` | 代理收付買回費統計表。**業務上屬通路報酬,代號卻夾在 AML 三支中間**(§0.5) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR171.cs:74` |
| `NFDR434` | 畫面開啟時**寫死** `AGENT_ID = "2"`(券商)+ `AGENT_CODE = "K5920"`(元富)〔客戶特定〕 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR434.cs:60-61` |
| `NFDR436` | 四支 SP 依「銷售機構類別 × 銷售類別」選(`_AA1` / `_AB1` / `_BA1` / `_BB1`);結果集名用 `"NFDR436_AA" + 參數` 動態組 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR436_PO.cs:69` |
| `NFDR436` | UI 有一條很長的業務規則:券商(不含元富)+ 申購時,輸出格式不得選定額列印;卡控:**阻擋** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR436.cs:167` |
| `NFDR437` | 唯一一支「查無資料」用 `MessageBox.Show` 而不是 `DialogWithNoStatusbar` 的 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR437.cs:105` |

`NFDR434` 寫死 `K5920` 是**型錄裡「寫死常數」的標準案例**:換一家券商要改程式重編,不是改設定。

### 7.6 營運統計 `5xx`(17 支,15 支死)——**當一組講**

**這一群不逐支寫,因為它們在程式層面幾乎是同一支。** 17 支裡 15 支的 PO 是同一個模板複製出來的:`Basic_PO` 基底、`private Database m_db = null;`、建構子裡三行註解掉的 Enterprise Library 初始化、`GetStoredProcCommand("s_NFDR5xx_Get")`、`@` 開頭的參數名、`SqlDbType`。**差別只在 SP 名字與參數清單。**

#### 7.6.1 這一群的業務(§0.3 的細節)

| 子群 | 支 | 業務 | 活 |
|---|---|---|---|
| 銷售 / 開戶 / 戶數 | `NFDR501`–`NFDR504` | 各銷售機構別統計、開戶統計、受益人戶數統計、各基金申贖統計 | 全死 |
| 大額申購 | `NFDR505` | 申購 N 元以上統計 | 死 |
| **定期定額(RSP)** | `NFDR506`–`NFDR510` | 扣款分析彙總 / 扣款金額分析 / 佔基金規模比例 / 銷售分析 / 扣款統計 | **全死** |
| 交易量 | `NFDR511`–`NFDR513` | 交易作業量 / 人員處理交易量 / 各基金交易量 | 全死 |
| **交易量(新版)** | `NFDR514` `NFDR515` | 作業統計總表 / 交易來源統計表 + KYC 來源統計表 | **活** |
| 比率 / 買回 | `NFDR516` `NFDR517` | 受益人持有基金比率 / 銷售買回統計 | 全死 |

**定期定額那五支是本片最大的缺口**(§0.3)。RSP 的維護與批次在 `rsp.md` 那邊,但那邊**不產這五張統計報表**——`rsp.md` 管的是扣款設定與扣款執行,不是事後分析。所以「定期定額這個月扣了多少、佔基金規模多少、成長趨勢如何」這幾個問題,**現在沒有報表可以回答**。

#### 7.6.2 一支死的長什麼樣:`NFDR501` 各銷售機構別統計表

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs`,124 行。逐行看死因:

| 行 | 內容 | 後果 |
|---|---|---|
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:18` | `private Database m_db = null;` | 欄位永遠 `null` |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:21` 起 | 建構子內三行 `//m_db = provider.Create("TA");` | 沒有人補上初始化 |
| `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:43` | `DbConnection Dbcon = m_db.CreateConnection();` | **在 `try` 之外**,`NullReferenceException` 連 `catch` 都進不去 |

第 3 點是關鍵:`m_db.CreateConnection()` 寫在 `try {` 的**上面一行**。所以這不是「查無資料」,是**整個呼叫堆疊炸回 UI**,使用者看到的是框架的一般錯誤對話框,不是任何業務訊息。

再往下看,`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:50-62` 還有一段**就算 `m_db` 補活也跑不起來**的邏輯:

```
if (FormType == "1") sqlCmd = "s_NFDR501_ALL";   // 合併基金
else                 sqlCmd = "s_NFDR501_ONE";   // 單一基金
```

兩支 SP 都是 `s_NFDR5xx` 舊命名(§2.2),都不在版控,而且參數用 `@AGENT_CODE_ST` 這種 T-SQL 風格。**遷移這一支要同時處理:PO 的 `m_db`、參數型別 `SqlDbType` → `OracleDbType`、參數名 `@x` → `:x` 或 `ix`、以及兩支 SP 本身。** 不是補一行 `new Database(...)` 就好。

#### 7.6.3 兩支活的:`NFDR514` / `NFDR515` 是 `NFDR511`–`NFDR513` 的後繼

`NFDR514`(作業統計總表)與 `NFDR515`(交易來源統計表 + KYC 來源統計表)是這一群唯二活的,而且**技術樣貌與 `8xx` 群一致**:`INFDRxxx_PO` + `S_TA_NFDR5xx_GET` + 雙 `RefCursor`(`OutTB` / `OutTB2`)+ 雙結果集。

從業務名看,它們**吃掉了 `NFDR511`–`NFDR513` 三支**:

| 舊(死) | 新(活) | 對應 |
|---|---|---|
| `NFDR511` 交易作業量表 | `NFDR514` 作業統計總表 | 直接對應 |
| `NFDR512` 人員處理交易量表 | `NFDR514` 的 `NFDR514T2` 第二結果集 | **假設**(依據:`NFDR514` 開兩個 `RefCursor`,UI 有 `PRINT_TYPE` 切換) |
| `NFDR513` 各基金交易量明細表 | `NFDR515` 交易來源統計表 | 軸不同,只是近似 |

`NFDR514` 有兩個值得記的實作細節:

1. **使用者選的「日」被無聲吃掉**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR514_PO.cs:63-66`:

```
if (rrRow.Name == "DATE_ST")
{ m_db.AddInParameter(Cmd, "datDATE_ST", OracleDbType.Varchar2,
    Convert.ToDateTime(rrRow.Value.Substring(0, 8) + "01").ToString("yyyyMMdd")); }
if (rrRow.Name == "DATE_END")
{ m_db.AddInParameter(Cmd, "datDATE_END", OracleDbType.Varchar2,
    Convert.ToDateTime(rrRow.Value.Substring(0,8)+"01").AddMonths(1).AddDays(-1).ToString("yyyyMMdd")); }
```

`Substring(0, 8) + "01"` 把日期強制改成**當月 1 日**,`DATE_END` 再推到**當月最後一天**。UI 標的是「統計年月」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR514.cs:97`),所以這是刻意的。**但畫面上是一個日期控制項,使用者選 3/15 得到的是 3/1–3/31,沒有任何提示。** 卡控結果:**過濾(無提示)**。另外 `Substring(0, 8)` **假設傳進來的字串至少 8 碼**。UI 沒有保證這件事,字串短於 8 碼會丟 `ArgumentOutOfRangeException`,同樣在 `try` 內被 `CommonExceptionBlocker` 吃掉。

1. **`catch` 裡的 `tran.Rollback()` 可能自己再爆一次**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR514_PO.cs:74` 才 `tran = m_db.BeginTransaction();`,但 `catch` 區塊無條件 `tran.Rollback()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR514_PO.cs:93`)。**第 74 行之前發生的任何例外(包含上面那個 `Substring`),進 `catch` 時 `tran` 還是 `null`**,`tran.Rollback()` 丟 `NullReferenceException`,**原始例外被蓋掉**。這是型錄裡「對已 Commit 的交易 `Rollback()` 吃掉原例外」的近親,而且比原型更常觸發。對照 `NFDR800`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:114`)的 `finally` 有 `if (tran != null)` 判斷,**`catch` 裡卻還是裸 `tran.Rollback()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:108`)**——同一支檔案裡,`finally` 記得判斷、`catch` 忘了。這個模式在 `8xx` 群 15 支裡**全部一致地存在**(因為是同一個模板複製的)。

#### 7.6.4 其餘 13 支死的(表格帶過)

| 支 | SP(版控外) | 參數數 | 一句話 |
|---|---|---|---|
| `NFDR502` | `s_NFDR502_Get` / `s_NFDR502_ALL` | 4 | 兩張報表(明細 / 彙總)靠 `@Type` 分派 |
| `NFDR503` | `s_NFDR503_Get` / `s_NFDR503_DEPT_Get` | 2 | 全公司 / 分部門兩個軸 |
| `NFDR504` | `s_NFDR504_Get` / `_ALL_Get` / `_DEPT_Get` | 6 | 六張結果集(筆數 / 金額 × 刪除 / 全部 / 部門) |
| `NFDR505` | `s_NFDR505_Get` | 5 | **無替代品**(§0.3) |
| `NFDR506` | `s_NFDR506_Get` | 4 | **定期定額,無替代品** |
| `NFDR507` | `s_NFDR507_Get` | 4 | **定期定額,無替代品** |
| `NFDR508` | `s_NFDR508_Get` | 1 | **定期定額,無替代品**;只吃 `@BAL_DATE` |
| `NFDR509` | `s_NFDR509_Get` | 3 | **定期定額,無替代品**;三張結果集 |
| `NFDR510` | `s_NFDR510_Get` | 3 | **定期定額,無替代品** |
| `NFDR511` | `s_NFDR511_Get` | 2 | 被 `NFDR514` 取代 |
| `NFDR512` | `s_NFDR512_Get` | 3 | `Model.xsd` 有 34 個 Caption,是死的那群裡最完整的 |
| `NFDR513` | `s_NFDR513_Get` | 2 | 被 `NFDR515` 近似取代 |
| `NFDR516` | `s_NFDR516_Get` | 0 | **無替代品**;UI 有「上限百分比 不可大於 100 / 不可等於 0」驗證,卡控:**阻擋** |
| `NFDR517` | `s_NFDR517_Get` | 0 | 被 `NFDR814` / `NFDR815` 取代 |

`NFDR516` 還有一條本片獨有的業務驗證:「申購日期 不可小於 基金代碼 X 的 基金開始募集日期 Y」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR516.cs:53`),錯誤訊息會把基金代碼與募集日一起印出來。卡控:**阻擋**。這支死掉,連帶這條檢查也沒人跑。

### 7.7 淨銷售統計 `7xx`(7 支,全死)——**當一組講**

**7 支全部死,而且死法一模一樣。** `NFDR701` / `NFDR702` / `NFDR703` / `NFDR705` / `NFDR707` 四支的 PO **連行數都一樣(100–101 行)**,參數清單完全相同(`@datDATE_ST` / `@datDATE_END` / `@striFUND_ID`),SP 只差代號。`NFDR704` / `NFDR706` 換成 `@deciBF_NO`(戶號)而不是基金代碼。

#### 7.7.1 七個軸

| 支 | 淨銷售的軸 | 主要參數 | 有無替代 |
|---|---|---|---|
| `NFDR701` | 直銷部門 | 基金 | `NFDR805` 部分 |
| `NFDR702` | 通路業務部門 | 基金 | `NFDR805` 部分 |
| `NFDR703` | 櫃台部門 | 基金 | `NFDR805` 部分 |
| `NFDR704` | **指定用途(指託戶)** | 戶號 | **無** |
| `NFDR705` | **通路** | 基金 | **無** |
| `NFDR706` | **特殊受益人** | 戶號 | **無** |
| `NFDR707` | **基金** | 基金 | **無** |

「淨銷售」= 申購 − 買回。這個口徑在活著的報表裡只有 `NFDR805`(業務單位日 / 期間報表)沾得上邊,而且它的軸是「業務單位」不是「部門 / 通路 / 基金」。**四個軸真的沒了。**

#### 7.7.2 `NFDR704` 指定用途淨銷售:唯一一支有前置檢核的,而且那道檢核 fail-open

`NFDR704` 比同群其他六支多 40 行,多的部分是一個 `IsBFExsits` 檢核(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:113-138`):

```
SELECT COUNT(1) FROM BMS001 WHERE BF_NO = @BF_NO AND TRUST_CODE IN (1,3)
```

UI 端(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR704.cs:110-121`):

```
int i = pxy.IsBFExsits(Convert.ToString(custBF_NO.Value));
if (i == 0) { this.ValidateErrList.AddError(this.custBF_NO, "戶號" + IsBFNO + "非指託戶"); … }
```

**`IsBFExsits` 在例外時回傳 `-1`**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:137`),而 UI 只擋 `== 0`。所以:

| 情況 | 回傳 | UI 反應 |
|---|---|---|
| 是指託戶 | `>= 1` | 放行(正確) |
| 不是指託戶 | `0` | **阻擋**(正確) |
| **查詢炸掉**(連線失敗 / SQL 錯 / `m_db` 是 `null`) | `-1` | **放行** ← fail-open |

而這支的 `m_db` **就是 `null`**,所以 `m_db.CreateConnection()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:115`)必炸 → `catch` → 回 `-1` → **檢核永遠放行**。不過這個放行沒有實際後果,因為下一步按預覽同樣會 NRE。**修活 `m_db` 之後,這條 fail-open 就會變成真的問題**,要一起修。

另外兩個寫死:`TRUST_CODE IN (1,3)`(什麼是「指託戶」寫在程式裡,不是代碼表)、戶號空白時參數塞 `-1`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:69`)當「全部」的魔術值。

#### 7.7.3 其餘六支(表格帶過)

| 支 | PO 行數 | SP(版控外) | 與 `NFDR701` 的差異 |
|---|---|---|---|
| `NFDR701` | 100 | `s_NFDR701_Get` | 基準 |
| `NFDR702` | 101 | `s_NFDR702_Get` | **只差 SP 名與報表中文名** |
| `NFDR703` | 100 | `s_NFDR703_Get` | **只差 SP 名與報表中文名** |
| `NFDR705` | 100 | `s_NFDR705_Get` | **只差 SP 名與報表中文名** |
| `NFDR706` | 108 | `s_NFDR706_Get` | 參數換成 `@deciBF_NO`,無 `IsBFExsits` |
| `NFDR707` | 100 | `s_NFDR707_Get` | **只差 SP 名與報表中文名** |

**五支 100–101 行的 PO 在業務上是五份不同的報表,在程式上是同一份檔案改了三個字串。** 要遷移這一群,寫一支就等於寫完五支——這是唯一的好消息。

### 7.8 結餘 / 餘額 / 業務單位 / 稽核 `8xx`(15 支)

**全片最長的連號,15 支全活。** `NFDR808` 與 `NFDR813` 不存在(跳號)。

#### 7.8.1 連號 ≠ 同系列?這一群是反例(必答問題 3)

`ofdr1.md` 對 `OFD` 的結論是「連號 ≠ 同系列,Jaccard 多為 0」。本片對 `NFDR800`–`NFDR816` 做同樣的測量,**結果相反**。

測量方式:把 15 支 PO 剝掉 `//` 註解後,兩兩算 `difflib.SequenceMatcher` 的文字相似度(比 Jaccard 嚴格,因為它看順序)。

| 排名 | 配對 | 相似度 | 說明 |
|---|---|---|---|
| 1 | `NFDR806` ↔ `NFDR807` | **0.996** | **除了代號以外一字不差**(下面逐行列) |
| 2 | `NFDR800` ↔ `NFDR801` | 0.978 | 參數完全相同(`BAL_DATE` / `KIND` / `FUND`) |
| 3 | `NFDR810` ↔ `NFDR811` | 0.977 | 參數相同(`DATE_ST` / `DAYS`),`NFDR811` 多一個 `RefCursor` |
| 4 | `NFDR805` ↔ `NFDR815` | 0.963 | 只差參數名 |
| 5 | `NFDR809` ↔ `NFDR810` | 0.949 |  |
| … |  |  |  |
| 最低 | `NFDR812` ↔ `NFDR816` | **0.397** | `NFDR812` 是全群唯一的異類 |

`NFDR806_PO.cs` 與 `NFDR807_PO.cs` 的**完整差異**只有 11 處,全部是代號字串:

| 行 | `NFDR806_PO.cs` | `NFDR807_PO.cs` |
|---|---|---|
| 18 | `public interface INFDR806_PO` | `public interface INFDR807_PO` |
| 20 | `T GetNFDR806<T>(…)` | `T GetNFDR807<T>(…)` |
| 25 | `class NFDR806_PO : INFDR806_PO` | `class NFDR807_PO : INFDR807_PO` |
| 30 / 34 / 50 / 52 | 建構子 / 解構子 / method / 型別轉換 | 同 |
| 61 | `sqlCommand = "s_TA_NFDR806_Get";` | `"s_TA_NFDR807_Get";` |
| 83 | `LoadDataSet(…, "NFDR806")` | `"NFDR807"` |
| 88 | `model.DataEntity.NFDR806.Rows.Count` | `NFDR807` |

**但業務上它們毫不相干**:`NFDR806` 是 `Subscription & Redemption Summary Report (By ***)`(申贖彙總,依通路),`NFDR807` 是 `Open New Account and Data Moving`(開戶與資料轉移)。兩者共用同一個參數組(`DATE_ST` / `DATE_ED`)純屬巧合——都是「一段期間」。

**所以正確的結論是分層的**:

| 層 | `NFDR800`–`NFDR816` | 與 `ofdr1.md` 的關係 |
|---|---|---|
| **程式層** | **高度同系列**。15 支共用同一個 PO 模板,平均相似度 0.77,11 組配對 > 0.9 | **推翻**「連號 ≠ 同系列」 |
| **業務層** | **不同系列**。受益人身份 / 資料變動 / 新基金募集 / 股務分攤 / 業務單位 / 申贖彙總 / 開戶 / 缺件 / 預估申贖 / 餘額 / 業務員 / 手續費收入,**12 種不同的業務** | **支持**「連號 ≠ 同系列」 |

**一句話:`NFDR800`–`NFDR816` 是 15 份不同的報表,用同一個模板長出來的。** 這與「一份報表的 15 個切面」是兩回事——後者會共用 `Model.xsd` 或 `.rpt`,這群**每支都有自己的 `Model.xsd` 與 `.rpt`**。

**維護上的意義**:模板有缺陷,15 支就一起有(例如 §7.6.3 講的 `catch` 裡裸 `tran.Rollback()`,15 支全中)。改模板等於改 15 支,而且**沒有任何共用基底類別可以一次改完**——只能 15 個檔案各改一次。

#### 7.8.2 `NFDR812` 預估申贖基金日報表:全群唯一的異類

相似度 0.40–0.70,全群最低。三個原因:

1. **SP 名是組出來的**。`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR812_PO.cs:63`:

```
sqlCommand = string.Format("s_TA_NFDR812_Get{0}",
    (nRptKind == 2) ? "_2" : ((nRptKind == 3) ? "_3" : ""));
```

**這代表實際存在三支 SP**(`s_TA_NFDR812_Get` / `_2` / `_3`),但 grep 只找得到一個字串。本片的 SP 總數因此是 **98 支寫得出名字 + 2 支只能推出來 = 100 支**(附錄 B)。

1. **四種報表類別對應四組結果集**,`switch (nRptKind)` 分派(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR812_PO.cs:116-136`):`case 0`→`NFDR812_C`、`case 1`→`NFDR812_E`、`case 2`→`NFDR812_C`、`case 3`→ 多開一個 `C_RES_D` 並載 `NFDR812_S` + `NFDR812_D`。**`switch` 沒有 `default`**,`nRptKind` 超出 0–3 時什麼都不載,`j` 維持 `0`,印空白報表。卡控:**過濾(無提示)**。

2. **它是本片唯一產生外部交換檔的**:`DSR{yyyyMMdd}.mon`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:209`),另外還能出兩個 Excel(彙總檔 / 明細檔,`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:261`)。三張 `.rpt` 之外還有三種檔案輸出,是本片出口最多的一支。

`NFDR812` 還有一個參數處理的坑:`FUNDS` 只在 `nRptKind == 0 || nRptKind == 1` 時才送(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR812_PO.cs:101-109`),`nRptKind` 是 2 或 3 時**畫面上勾的基金完全不生效**。UI 的驗證卻是無條件的「基金明細必須勾選!!」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:81`)。**使用者被要求勾基金,勾完之後那個條件被丟掉。** 卡控結果:**過濾(無提示)**,而且是最容易讓人誤會的一種——因為畫面明明要求你勾。

#### 7.8.3 `NFDR800` 受益人身份統計表:模板本尊

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs`,123 行,是這群的原型。結構:

| 段 | 行 | 內容 |
|---|---|---|
| 介面 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:18` | `public interface INFDR800_PO`,只宣告 `GetNFDR800<T>` |
| 屬性 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:25` | `[PODbType(DbServerType.Oracle)]` |
| 成員 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:28` | `private Database m_db = new Database("TA", DbServerType.Oracle);` |
| 取數 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:62-85` | SP + 三個 `AddInParameter`(`iBAL_DATE` / `iKIND` / `iFUND`)+ `C_RES` |
| 載入 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:88` | `LoadDataSet(Cmd, model.DataEntity, tran, "NFDR800")` |
| 例外 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:106-110` | `catch { tran.Rollback(); … }` ← **裸 Rollback** |
| 釋放 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:111-116` | `finally { if (tran != null) … }` ← 這裡有判斷 |

三個模板層級的問題,**15 支全中**:

| # | 問題 | 影響 |
|---|---|---|
| 1 | `catch` 裡裸 `tran.Rollback()`,`finally` 卻有 `if (tran != null)` | `BeginTransaction()` 之前的例外(參數轉型失敗等)會被 `NullReferenceException` 蓋掉,看不到真因 |
| 2 | 只讀報表卻開交易(`BeginTransaction` + `Commit`) | 長時間查詢(`CommandTimeout = 0`)會持有交易,對併發不友善 |
| 3 | 半形 / 全形空白混用 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:73`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:78`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:83` 的 `}` 後面接的是 **U+3000 全形空白**,不是半形。編譯沒事,但 diff / 格式化工具會亂 |

第 3 點在本片有 8 支中獎(附錄 E-08),而且**都集中在 `8xx` 群與 `NFDR201`**——因為是同一個模板複製的。

#### 7.8.4 本群其餘支(表格帶過)

| 支 | SP(版控外) | 參數 | 一句話 |
|---|---|---|---|
| `NFDR801` | `s_TA_NFDR801_Get` | `BAL_DATE` `KIND` `FUND` | 與 `NFDR800` 相似度 0.978,參數完全相同 |
| `NFDR802` | `s_TA_NFDR802_Get` + `_1` | `BAL_Month` `DATE_ST` `DATE_ED` `KIND` `FUND` | 本群唯一有兩支 SP 的;UI 四道必填驗證,卡控:**阻擋** |
| `NFDR803` | `s_TA_NFDR803_Get` | `ALLOT_DATE` `FUND_ID` | 新基金募集每日銷售;全形空白 4 處 |
| `NFDR804` | `s_TA_NFDR804_Get` | `BAL_DATE_ST` `BAL_DATE_ED` | 報表期間字串是 UI 手組的「yyyy/MM/01 至 …」 |
| `NFDR805` | `s_TA_NFDR805_Get` | 6 個 | 日報 / 期間報兩種,**與 `NFDR815` 相似度 0.963** |
| `NFDR806` | `s_TA_NFDR806_Get` | `DATE_ST` `DATE_ED` | 見 §7.8.1 |
| `NFDR807` | `s_TA_NFDR807_Get` | `DATE_ST` `DATE_ED` | 見 §7.8.1 |
| `NFDR809` | `s_TA_NFDR809_Get` | `DATE_ST` | 缺件統計 |
| `NFDR810` | `s_TA_NFDR810_Get` | `DATE_ST` `DAYS` | **無 `.rpt`**,只出 Excel;「執行」鈕跳「此項功能無作用」 |
| `NFDR811` | `s_TA_NFDR811_Get` | `DATE_ST` `DAYS` | **無 `.rpt`**;兩個 `RefCursor`(`C_RES_T1` / `C_RES_T2`)出兩個 Excel |
| `NFDR814` | `s_TA_NFDR814_Get` | 7 個 | 餘額統計;金額區間用 `ToString("C")` 組顯示字串,**吃當下的地區設定** |
| `NFDR815` | `s_TA_NFDR815_Get` | 6 個 | 三張報表共用一支 SP + 一個 `striTYPE` 參數 |
| `NFDR816` | `s_TA_NFDR816_Get` | 3 個 | 手續費收入;`Model.xsd` 24 個 Caption |

`NFDR814` 的 `Convert.ToDecimal(this.unumBAL_AMT1.Value).ToString("C")`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR814.cs:56`)**依賴 client 的 CurrentCulture**。同一份報表在不同語系的機器上印出來的金額符號不一樣(`NT$` vs `$` vs `¥`)。這是顯示字串不是資料,但對外報表的標頭不該隨機器變。

### 7.9 投信投顧公會英文申報(3 支)

**業務**:投信投顧公會的英文統計申報。3 支全活,是本片唯一全英文報表名的一群。

| 支 | 報表(英文名即 Crystal 標題) | 版型數 | SP |
|---|---|---|---|
| `NFDR558` | `Equity Fund(Domestic) / (Oversea) / Fix Income and Money Market / Balance Fund / Others Subscription/Redemption`,共 **8 個標題共用 1 張 `.rpt`** | 1 | `s_TA_NFDR558_Get` |
| `NFDR559` | `Savings Plan Investors of Monthly Subscription (Account) / (customers) / Amount (NT$)` + `Taiwan Fund Industry Growth Statistics` | 2 | `s_TA_NFDR559_Get` |
| `NFDR560` | `Taiwan Fund Industry Statistics` | 2 | `s_TA_NFDR560_Get` + `_2` |

三支的 PO **幾乎相同**(115 / 115 / 118 行,參數都是 `datiYYYYMM` + `striPRT_TYPE`),又是一組模板複製。

`NFDR558` 值得單獨記:**8 個不同的英文報表標題,全部指向同一張 `NFDR558RPS.rpt`**(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR558.cs:67-88`)。也就是說版型只有一種,差別完全靠 SP 回傳的資料與標題字串。**改 `NFDR558RPS.rpt` 的欄位,8 種報表一起變。** 這是 `nfdr1.md §7.1.1` 講的「版型與選項多對一」在本片的極端案例——**8 對 1**。

三支都會出 Excel(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR558.cs:161` 的「匯出成功!」),而且**沒有任何「查無資料」判斷**——查不到就匯出一個空的 Excel 給公會。卡控結果:**不擋**。

## 8. 跨模組共用

```text
[圖] NFD 的跨模組依賴：單向但會回寫三張別人的表、影響面最大的四張表、三種不報錯的危險改動，以及分析為何天生不完整
圖中文字:① 依賴方向：單向，但不再是唯讀 / NFD 82 支報表 / 零反向依賴 / 讀 OFD／BMS／SAL / 16 張表 / 寫 OFD701 721 724 / 已印旗標 / 沒有人依賴 NFD / 改 NFD 不會波及別人 / ② 改哪些表要回歸本片（依風險排序） / OFD303A 日結控制 / 168 210 的前置卡控 / OFD701 核印 / 223 的九欄位 UPDATE / OFD038 vs OFD038A / 兩張都要看 / OFD081V view / 改底層查不到誰在用 / ③ 三種最危險的改動 / CTL_CODE 允許 NULL / 結帳卡控靜默放行 / OFD701 改 PK 或加欄 / 更新 0 筆但筆數寫死 0 / SP 回傳欄位少一欄 / xsd 沒同步 → 欄位永遠空白 / 三種都不報錯 / 只有報表上看得出來 / ④ 影響面分析為何天生不完整 / 10 支可見 / 表名寫在 PO inline SQL / 72 支不可見 / SQL 在版控外的 SP / SP 100 支零版控 / 連 diff 都沒有 / 要先撈 SP 原始碼 / 附錄 B 就是為此準備
```

*圖:圖 5 跨模組依賴(§8)。橘虛框=改動後會靜默出錯的地方;灰虛框=別模組的表;黑框=查不到的黑箱;橘框=本文結論。「沒有人依賴 NFD」是好消息;「NFD 依賴所有人而且 88% 查不到」是壞消息。*

### 8.1 `NFD` 的依賴仍然是單向的,但不再是「唯讀」

`nfdr1.md §8.1` 的結論(`NFD` 只讀別人、沒有任何模組依賴 `NFD`)在本片**一半成立**:

| 方向 | 前片結論 | 本片實測 |
|---|---|---|
| 有沒有別的模組依賴 `NFD` | 零 | **零**(全庫 grep `ReportPO.NFD` / `ReportControl.NFD` 只有 `NFD` 自己用) |
| `NFD` 依不依賴別人 | 是,只讀 | **是,而且會寫**(§4) |

**新增的事實:`NFD` 會 `UPDATE` 別的模組的表。** 已確認三張:

| 表 | 歸屬 | 誰寫 | 寫什麼 |
|---|---|---|---|
| `OFD701` | `OFD` 軌(核印) | `NFDR223` | `RECEIPT_DOC_ID2 = 'Y'`(已印旗標) |
| `OFD721` | `OFD` 軌(憑證) | `NFDR201` | 列印註記(T-SQL,實際跑不起來) |
| `OFD724` | `OFD` 軌(憑證待列印簽證檔) | `NFDR201` | 列印註記(同上) |

再加上 `NFDR224` 透過 `S_TA_NFDR224_GET` 寫的東西(SP 在版控外,寫什麼看不到)與 `NFDR437` 那條 SP 寫 `SALR905T1` 的線索(§7.5.3)。

**所以正確的說法是:`NFD` 不擁有業務事實,但擁有「已印 / 已處理」這類旗標的寫入權,而且旗標寫在別人的表上。**

### 8.2 改哪些表要回歸本片的 `NFD` 報表

**這張表天生不完整**,因為 72 支看不到表名(§2.1)。以下是**看得到的部分**:

| 表 | 歸屬 | 本片誰在用 | 怎麼用 |
|---|---|---|---|
| `OFD303A`(日結控制) | `OFD` 軌 | `NFDR168`(檢核申購日已結轉)、`NFDR210`(檢核各基金已結帳) | **兩支都是前置卡控**,而且兩支的卡控都有缺陷(§7.1.2、§7.2.3) |
| `OFD081V`(基金 view) | `OFD` 軌 | `NFDR241` `NFDR243` | 撈基金下拉清單 |
| `OFD038` / `OFD038A`(基金群組) | `OFD` 軌 | `NFDR241`(`OFD038`)、`NFDR243` `NFDR244`(`OFD038A`) | `LEFT JOIN` 撈群組;**兩支用舊表、兩支用新表** |
| `OFD081A`(基金主檔) | `OFD` 軌 | `NFDR244` | 撈基金簡稱 |
| `OFD701` / `OFD711`(核印) | `OFD` 軌 | `NFDR223` | 讀失敗原因 + **寫已印旗標** |
| `OFD721` / `OFD724` / `OFD0811`(憑證) | `OFD` 軌 | `NFDR201` | 讀 + **寫列印註記** |
| `OFD312`(大憑證) | `OFD` 軌 | `NFDR203` | 結果集借名 |
| `OFD0819`(匯款) | `OFD` 軌 | `NFDR237` | 結果集借名 |
| `OFD922A` / `LOG_OFD931A`(獎金計算) | `OFD` 軌 + 系統 log | `NFDR933` | **前置狀態檢查**,沒跑過 `OFDM931A` 就不給印 |
| `BMS001`(受益人主檔) | `BMS` | `NFDR201` `NFDR704` | 讀姓名 / 檢核指託戶 |
| `SALR905T1`(暫存) | `SAL` | `NFDR437`(SP 內) | SP 寫入,PO `Rollback()` 清掉 |

**`OFD038` vs `OFD038A` 這組不一致要特別記**:`NFDR241`(死)用 `[OFD038]`,`NFDR243` / `NFDR244`(活)用 `OFD038A`。改基金群組表的人,兩張都要看。

### 8.3 最危險的三種跨模組改動

| 改動 | 會發生什麼 | 為什麼查不到 |
|---|---|---|
| **`OFD303A` 的 `ALLOT_CTL_CODE` / `REDEM_CTL_CODE` / `RSP_CTL_CODE` 允許 `NULL`,或改變 `'3'` / `'4'` 的語意** | `NFDR168` 與 `NFDR210` 的結帳前置卡控**靜默放行**,印出未結帳的數字(其中 `NFDR210` 是對外開立的持有單位證明) | 兩支的檢核都是 `<> '常數'`,三值邏輯漏 `NULL`;`NFDR210` 那支還多一個缺括號 + fail-open(§7.2.3) |
| **`OFD701` 加欄位或改 PK** | `NFDR223` 的 9 欄位 `UPDATE` 條件可能對不上 → 更新 0 筆,而**筆數被寫死成 0**,使用者完全看不出來(§7.3.2) | 回寫邏輯藏在報表 PO 裡,不在任何 `OFD` 的維護畫面 |
| **改任何一支 SP 的回傳欄位** | `Model.xsd` 與 Ctl 的 `TransferTable` 沒同步 → 該欄在報表上永遠空白,不報錯 | **SP 全部不在版控**,連 diff 都沒有 |

### 8.4 影響面分析在本片為什麼特別不完整

| 可見度 | 支數 | 比例 |
|---|---|---|
| PO 內看得到表名 | 10 | 12% |
| 完全看不到(SQL 在版控外 SP) | 72 | **88%** |

`nfdr1.md §8.4` 說「改 `OFD` 表要另外撈 SP 原始碼」。**本片的情況更糟:連撈哪幾支 SP 都要先從 PO 讀出 100 個 SP 名字,再一支一支去資料庫抓。** 附錄 B 的 100 支清單就是為了這件事準備的。

## 附錄 A. 資料表總表(僅限 PO / `Model.xsd` 內看得見的)

本片 82 支報表,**自有業務主檔 0 張**。以下 14 張全部屬於別的模組,`NFD` 只是使用者。「寫」欄標 ✓ 的是 `NFD` 會 `UPDATE` 的(§4、§8.1)。

| 表 | 歸屬 | 用途(從 SQL 反推) | 本片誰用 | 讀 | 寫 |
|---|---|---|---|---|---|
| `OFD303A` | `OFD` 軌 | 日結 / 結帳控制(`ALLOT_CTL_CODE` / `REDEM_CTL_CODE` / `RSP_CTL_CODE` / `CTL_DATE`) | `NFDR168` `NFDR210` | ✓ |  |
| `OFD081V` | `OFD` 軌(view) | 基金清單(`FUND_ID` / `FUND_SH_NM` / `PROF_TYPE`) | `NFDR241` `NFDR243` | ✓ |  |
| `OFD081A` | `OFD` 軌 | 基金主檔(`FUND_SH_NM`) | `NFDR244` | ✓ |  |
| `OFD038` | `OFD` 軌 | 基金群組(`FUND_GRPCD`),**舊表** | `NFDR241` | ✓ |  |
| `OFD038A` | `OFD` 軌 | 基金群組,**新表** | `NFDR243` `NFDR244` | ✓ |  |
| `OFD701` | `OFD` 軌 | 核印主檔(`RECEIPT_DOC_ID2` 已印旗標) | `NFDR223` | ✓ | **✓** |
| `OFD711` | `OFD` 軌 | 核印失敗原因(`SEAL_RTN_CD` / `SEAL_RTN_DESCRP` / `STATEMENT_CODE`) | `NFDR223` | ✓ |  |
| `OFD721` | `OFD` 軌 | 受益憑證檔(`CER_SOURCE` / `CER_UNIT`) | `NFDR201` | ✓ | **✓** |
| `OFD724` | `OFD` 軌 | 待列印簽證檔(`BF_CER_ISSUE_CODE` / `BF_CER_NO` / `BF_CER_CHK` / `TASK_ID`) | `NFDR201` | ✓ | **✓** |
| `OFD0811` | `OFD` 軌 | 憑證受益人資料(`BF_CER_ID_NO` / `BF_CER_NAME`) | `NFDR201` | ✓ |  |
| `OFD312` | `OFD` 軌 | 大憑證(`A_UNIT` / `ISSUE_DATE`) | `NFDR203` | ✓ |  |
| `OFD0819` | `OFD` 軌 | 匯款比對 | `NFDR237` | ✓ |  |
| `OFD922A` | `OFD` 軌 | 獎金計算結果 | `NFDR933` | ✓ |  |
| `LOG_OFD931A` | 系統 log | 作業執行記錄(`YEARS` / `QDATE` / `function_id`) | `NFDR933` | ✓ |  |
| `BMS001` | `BMS` | 受益人主檔(`ID_NO` / `BF_NAME` / `BF_NO` / `TRUST_CODE`) | `NFDR201` `NFDR704` | ✓ |  |
| `SALR905T1` | `SAL` | 報表暫存(`USERDOMAIN`);**只出現在註解裡**,實際由 SP 寫入 | `NFDR437` |  |  |

> **這張表天生不完整。** 72 支(88%)的 SQL 在版控外的 SP 裡,它們讀哪些表 repo 內查不到(§2.1、§8.4)。上表已加進 meta `refcheck-ignore` 的部分:所有 `OFD*` / `BMS001` / `LOG_OFD931A` / `SALR905T1` 都不在 `DB/Table/` 內(它們屬於別的 repo 或別的交付)。

## 附錄 B. SP / Function / Trigger / View

### B.1 SP 總表(100 支,版控內 **0 支**)

**全部不在 `DB/SP/`。** `DB/SP/` 只有 `S_OTA_*` 83 個檔(`ofdb5.md`)。命名分兩代:`s_NFDRxxx_*`(舊,對應 `Basic_PO`,**全死**)與 `s_TA_NFDRxxx_*`(新,對應 `INFDRxxx_PO`,全活)。

| 支 | SP(依 PO 內字串原樣,大小寫不統一) | 代 | 在版控 |
|---|---|---|---|
| `NFDR168` | `S_TA_NFDR168_GET` | 新 | 否 |
| `NFDR169` | `S_TA_NFDR169_GET` | 新 | 否 |
| `NFDR170` | `S_TA_NFDR170_GET` | 新 | 否 |
| `NFDR185` | `S_TA_NFDR185_GET` | 新 | 否 |
| `NFDR186` | `S_TA_NFDR186_GET` | 新 | 否 |
| `NFDR187` | `S_TA_NFDR187_GET` | 新 | 否 |
| `NFDR188` | `S_TA_NFDR188_GET` | 新 | 否 |
| `NFDR245` | `s_NFDR245_Get` | 舊 | 否 |
| `NFDR200` | `S_TA_NFDR200_GET` | 新 | 否 |
| `NFDR201` | `s_NFDR201_Get` | 舊 | 否 |
| `NFDR202` | `s_NFDR202_Get` | 舊 | 否 |
| `NFDR203` | `s_NFDR203_Get` | 舊 | 否 |
| `NFDR204` | `s_NFDR204_Get` | 舊 | 否 |
| `NFDR205` | `s_NFDR205_Get` | 舊 | 否 |
| `NFDR206` | `s_NFDR206_Get` | 舊 | 否 |
| `NFDR207` | `s_NFDR207_Get` | 舊 | 否 |
| `NFDR210` | `S_TA_NFDR210_GET` | 新 | 否 |
| `NFDR244` | `s_TA_NFDR244_Get` | 新 | 否 |
| `NFDR221` | `S_TA_NFDR221_GET` | 新 | 否 |
| `NFDR222` | `S_TA_NFDR222_GET` | 新 | 否 |
| `NFDR223` | `S_TA_NFDR223_GET` | 新 | 否 |
| `NFDR224` | `S_TA_NFDR224_GET` | 新 | 否 |
| `NFDR225` | `S_TA_NFDR225_GET` | 新 | 否 |
| `NFDR231` | `s_NFDR231_Get` | 舊 | 否 |
| `NFDR232` | `s_NFDR232_Get` | 舊 | 否 |
| `NFDR233` | `s_NFDR233_Get` | 舊 | 否 |
| `NFDR236` | `s_NFDR236_All_Get`、`s_NFDR236_Detail_Get`、`s_NFDR236_Excel_Get` | 舊 | 否 |
| `NFDR237` | `s_NFDR237_All_Get`、`s_NFDR237_Detail_Get`、`s_NFDR237_Excel_Get` | 舊 | 否 |
| `NFDR240` | `S_TA_NFDR240_GET` | 新 | 否 |
| `NFDR241` | `s_NFDR241_AGENT_Get`、`s_NFDR241_FUND_Get`、`s_NFDR241_MASTER_Get` | 舊 | 否 |
| `NFDR242` | `s_NFDR242_Get` | 舊 | 否 |
| `NFDR243` | `s_TA_NFDR243_Get` | 新 | 否 |
| `NFDR171` | `S_TA_NFDR171_GET` | 新 | 否 |
| `NFDR352` | `S_TA_NFDR352_GET` | 新 | 否 |
| `NFDR431` | `s_TA_NFDR431_Get` | 新 | 否 |
| `NFDR432` | `s_TA_NFDR432_Get` | 新 | 否 |
| `NFDR434` | `S_TA_NFDR434_GET` | 新 | 否 |
| `NFDR436` | `S_TA_NFDR436_GET_AA1`、`S_TA_NFDR436_GET_AB1`、`S_TA_NFDR436_GET_BA1`、`S_TA_NFDR436_GET_BB1` | 新 | 否 |
| `NFDR437` | `S_TA_NFDR437_GET` | 新 | 否 |
| `NFDR933` | `S_TA_NFDR933_GET` | 新 | 否 |
| `NFDR501` | `s_NFDR501_ALL`、`s_NFDR501_ONE` | 舊 | 否 |
| `NFDR502` | `s_NFDR502_ALL`、`s_NFDR502_Get` | 舊 | 否 |
| `NFDR503` | `s_NFDR503_DEPT_Get`、`s_NFDR503_Get` | 舊 | 否 |
| `NFDR504` | `s_NFDR504_ALL_Get`、`s_NFDR504_DEPT_Get`、`s_NFDR504_Get` | 舊 | 否 |
| `NFDR505` | `s_NFDR505_Get` | 舊 | 否 |
| `NFDR506` | `s_NFDR506_Get` | 舊 | 否 |
| `NFDR507` | `s_NFDR507_Get` | 舊 | 否 |
| `NFDR508` | `s_NFDR508_Get` | 舊 | 否 |
| `NFDR509` | `s_NFDR509_Get` | 舊 | 否 |
| `NFDR510` | `s_NFDR510_Get` | 舊 | 否 |
| `NFDR511` | `s_NFDR511_Get` | 舊 | 否 |
| `NFDR512` | `s_NFDR512_Get` | 舊 | 否 |
| `NFDR513` | `s_NFDR513_Get` | 舊 | 否 |
| `NFDR514` | `S_TA_NFDR514_GET` | 新 | 否 |
| `NFDR515` | `S_TA_NFDR515_GET` | 新 | 否 |
| `NFDR516` | `s_NFDR516_Get` | 舊 | 否 |
| `NFDR517` | `s_NFDR517_Get` | 舊 | 否 |
| `NFDR701` | `s_NFDR701_Get` | 舊 | 否 |
| `NFDR702` | `s_NFDR702_Get` | 舊 | 否 |
| `NFDR703` | `s_NFDR703_Get` | 舊 | 否 |
| `NFDR704` | `s_NFDR704_Get` | 舊 | 否 |
| `NFDR705` | `s_NFDR705_Get` | 舊 | 否 |
| `NFDR706` | `s_NFDR706_Get` | 舊 | 否 |
| `NFDR707` | `s_NFDR707_Get` | 舊 | 否 |
| `NFDR800` | `s_TA_NFDR800_Get` | 新 | 否 |
| `NFDR801` | `s_TA_NFDR801_Get` | 新 | 否 |
| `NFDR802` | `s_TA_NFDR802_Get`、`s_TA_NFDR802_Get_1` | 新 | 否 |
| `NFDR803` | `s_TA_NFDR803_Get` | 新 | 否 |
| `NFDR804` | `s_TA_NFDR804_Get` | 新 | 否 |
| `NFDR805` | `s_TA_NFDR805_Get` | 新 | 否 |
| `NFDR806` | `s_TA_NFDR806_Get` | 新 | 否 |
| `NFDR807` | `s_TA_NFDR807_Get` | 新 | 否 |
| `NFDR809` | `s_TA_NFDR809_Get` | 新 | 否 |
| `NFDR810` | `s_TA_NFDR810_Get` | 新 | 否 |
| `NFDR811` | `s_TA_NFDR811_Get` | 新 | 否 |
| `NFDR812` | `s_TA_NFDR812_Get`、`s_TA_NFDR812_Get_2(動態)`、`s_TA_NFDR812_Get_3(動態)` | 新 | 否 |
| `NFDR814` | `s_TA_NFDR814_Get` | 新 | 否 |
| `NFDR815` | `s_TA_NFDR815_Get` | 新 | 否 |
| `NFDR816` | `s_TA_NFDR816_Get` | 新 | 否 |
| `NFDR558` | `s_TA_NFDR558_Get` | 新 | 否 |
| `NFDR559` | `s_TA_NFDR559_Get` | 新 | 否 |
| `NFDR560` | `s_TA_NFDR560_2_Get`、`s_TA_NFDR560_Get` | 新 | 否 |

合計 **100** 個 SP 名(含 `NFDR812` 兩支 `string.Format` 動態組出的),**版控內 0 支**。

### B.2 Function

本片 PO 內出現的 SQL 函式(全部在版控外,`DB/Function/` 無對應檔):

| 函式 | 用在哪 | 方言 | 錨點 |
|---|---|---|---|
| `dbo.PADLeft(欄, 7, '0')` | `NFDR203` 組憑證號 | **T-SQL 專用**(`dbo.` schema 前綴) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR203_PO.cs:90` |
| `ISNULL(欄, '')` | `NFDR201` 空值替換 | **T-SQL 專用**(Oracle 是 `NVL`) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:105` |
| `CONVERT(VARCHAR, 欄)` | `NFDR203` 型別轉換 | **T-SQL 專用** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR203_PO.cs:91` |
| `NVL(:參數, ' ')` | 本片所有活的 PO 的「全部」慣用寫法 | Oracle | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:112` |

### B.3 Trigger / View

| 類型 | 名稱 | 說明 |
|---|---|---|
| View | `OFD081V` | 基金清單 view。**改底層表查不到誰在用**,本片 `NFDR241` / `NFDR243` 靠它撈下拉 |
| Trigger | — | 本片 PO 內沒有任何 trigger 的痕跡 |

## 附錄 C. 代碼對照

本模組**不定義任何代碼**(§2.7),以下全部是讀別人的值,或**寫死在程式裡**的值。

| 代碼 / 常數 | 值 | 意義 | 哪來的 | 錨點 |
|---|---|---|---|---|
| `AGENT_ID` | `0` / `1` / `2` / `3` | 公 / 銀 / 券 / 顧 | UI 內 if-else 鏈,**四支各寫一次** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR188.cs:63` |
| `Seal_Type` | 一般 / 財金 / 全部 | 核印類別 | UI 寫死中文 | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR221.cs:51` |
| `FormType` | `0` 全部 / `1` 一般 / `2` **無名** / `3` 財金 | 核印表單類別 | UI 寫死;`2` 沒有中文(§2.7) | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:48` |
| `ALLOT_CTL_CODE = '3'` | `3` = 申購已結轉 | 日結狀態 | **寫死在 SQL 裡**,不是代碼表 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:113` |
| `REDEM_CTL_CODE = '4'` | `4` = 買回已結轉 | 日結狀態 | **寫死在 SQL 裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:112` |
| `RSP_CTL_CODE = '3'` | `3` = 定期定額已結轉 | 日結狀態 | **寫死在 SQL 裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:113` |
| `TRUST_CODE IN (1,3)` | `1` / `3` = 指託戶 | 受益人類別 | **寫死在 SQL 裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:122` |
| `CER_SOURCE = '5'` | `5` = 憑證來源特例 | 憑證來源 | **寫死在 SQL 裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:105` |
| `AGENT_CODE = "K5920"` | 元富證券〔客戶特定〕 | 券商代碼 | **寫死在 UI 初始化** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR434.cs:61` |
| `AGENT_ID = "2"` | 券商〔客戶特定〕 | 機構類別 | **寫死在 UI 初始化** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR434.cs:60` |
| `"中國信託商業銀行股務代理部"` | 〔客戶特定〕 | 報表落款 | **寫死餵給 Crystal** | `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR210.cs:46` |
| `OFD081V.FUND_ID NOT IN('ALL FUNDS')` | `ALL FUNDS` 是一筆假基金 | 下拉排除 | **寫死在 SQL 裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:57` |
| `function_id = 'OFDM931A'` | 上游作業代號 | `NFDR933` 前置檢查 | **寫死在 SQL 判斷裡** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR933_PO.cs:172` |
| `@deciBF_NO = -1` | `-1` = 全部戶號 | 魔術值 | **寫死在 PO** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:69` |

**`3` / `4` 這兩個日結代碼出現在兩支不同的報表裡,兩支都寫死。** 日結狀態碼一旦調整,要同時改 `NFDR168` 與 `NFDR210` 的 SQL,repo 內沒有任何地方把它們關聯起來。

## 附錄 D. 本片 82 支處置表

**不跑 `--module NFD` 覆蓋率,改用本表逐支交代。** 82 支全部列出,零遺漏。

| # | 代號 | 章節 | 處置 | `m_db` | 資料來源 | `.rpt` 在版控 | 在 csproj |
|---|---|---|---|---|---|---|---|
| 1 | `NFDR168` | §7.1 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 2 | `NFDR169` | §7.1 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 3 | `NFDR170` | §7.1 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 4 | `NFDR185` | §7.1 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 5 | `NFDR186` | §7.1 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 6 | `NFDR187` | §7.1 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 7 | `NFDR188` | §7.1 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 8 | `NFDR245` | §7.1 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 9 | `NFDR200` | §7.2 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 10 | `NFDR201` | §7.2 | **已深寫** | **死** | SP×1 + inline SQL | 1 / 1 | 是 |
| 11 | `NFDR202` | §7.2 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 12 | `NFDR203` | §7.2 | 表格帶過 | **死** | SP×1 + inline SQL | 1 / 1 | 是 |
| 13 | `NFDR204` | §7.2 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 14 | `NFDR205` | §7.2 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 15 | `NFDR206` | §7.2 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 16 | `NFDR207` | §7.2 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 17 | `NFDR210` | §7.2 | **已深寫** | 活 | SP×1 + inline SQL | 2 / 2 | 是 |
| 18 | `NFDR244` | §7.2 | 表格帶過 | 活 | SP×1 + inline SQL | 1 / 1 | 是 |
| 19 | `NFDR221` | §7.3 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 20 | `NFDR222` | §7.3 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 21 | `NFDR223` | §7.3 | **已深寫** | 活 | SP×1 + inline SQL | 2 / 2 | 是 |
| 22 | `NFDR224` | §7.3 | 表格帶過 | 活 | SP×1 | 無 `.rpt` | — |
| 23 | `NFDR225` | §7.3 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 24 | `NFDR231` | §7.4 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 25 | `NFDR232` | §7.4 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 26 | `NFDR233` | §7.4 | 表格帶過 | **死** | SP×1 | 2 / 2 | 是 |
| 27 | `NFDR236` | §7.4 | **已深寫** | **死** | SP×3 | 2 / 2 | 是 |
| 28 | `NFDR237` | §7.4 | **已深寫** | **死** | SP×3 + inline SQL | 4 / 4 | 是 |
| 29 | `NFDR240` | §7.4 | 表格帶過 | 活 | SP×1 | 3 / 3 | 是 |
| 30 | `NFDR241` | §7.4 | **已深寫** | **死** | SP×3 + inline SQL | 4 / 4 | 是 |
| 31 | `NFDR242` | §7.4 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 32 | `NFDR243` | §7.4 | 表格帶過 | 活 | SP×1 + inline SQL | 2 / 2 | 是 |
| 33 | `NFDR171` | §7.5 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 34 | `NFDR352` | §7.5 | **已深寫** | 活 | SP×1 | 無 `.rpt` | — |
| 35 | `NFDR431` | §7.5 | **已深寫** | 活(`dbTA`) | SP×1 | 6 / 6 | 是 |
| 36 | `NFDR432` | §7.5 | **已深寫** | 活(`dbTA`) | SP×1 | 5 / 5 | 是 |
| 37 | `NFDR434` | §7.5 | **已深寫** | 活 | SP×1 | 3 / 3 | 是 |
| 38 | `NFDR436` | §7.5 | **已深寫** | 活 | SP×4 | 5 / 5 | 是 |
| 39 | `NFDR437` | §7.5 | **已深寫** | 活 | SP×1 + inline SQL | 無 `.rpt` | — |
| 40 | `NFDR933` | §7.5 | **已深寫** | 活 | SP×1 + inline SQL | 2 / 2 | 是 |
| 41 | `NFDR501` | §7.6 | **已深寫** | **死** | SP×2 | 2 / 2 | 是 |
| 42 | `NFDR502` | §7.6 | 表格帶過 | **死** | SP×2 | 2 / 2 | 是 |
| 43 | `NFDR503` | §7.6 | 表格帶過 | **死** | SP×2 | 2 / 2 | 是 |
| 44 | `NFDR504` | §7.6 | 表格帶過 | **死** | SP×3 | 6 / 6 | 是 |
| 45 | `NFDR505` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 46 | `NFDR506` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 47 | `NFDR507` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 48 | `NFDR508` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 49 | `NFDR509` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 50 | `NFDR510` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 51 | `NFDR511` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 52 | `NFDR512` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 53 | `NFDR513` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 54 | `NFDR514` | §7.6 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 55 | `NFDR515` | §7.6 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 56 | `NFDR516` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 57 | `NFDR517` | §7.6 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 58 | `NFDR701` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 59 | `NFDR702` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 60 | `NFDR703` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 61 | `NFDR704` | §7.7 | **已深寫** | **死** | SP×1 + inline SQL | 1 / 1 | 是 |
| 62 | `NFDR705` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 63 | `NFDR706` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 64 | `NFDR707` | §7.7 | 表格帶過 | **死** | SP×1 | 1 / 1 | 是 |
| 65 | `NFDR800` | §7.8 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 66 | `NFDR801` | §7.8 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 67 | `NFDR802` | §7.8 | 表格帶過 | 活 | SP×2 | 1 / 1 | 是 |
| 68 | `NFDR803` | §7.8 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 69 | `NFDR804` | §7.8 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 70 | `NFDR805` | §7.8 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 71 | `NFDR806` | §7.8 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 72 | `NFDR807` | §7.8 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 73 | `NFDR809` | §7.8 | 表格帶過 | 活 | SP×1 | 1 / 1 | 是 |
| 74 | `NFDR810` | §7.8 | 表格帶過 | 活 | SP×1 | 無 `.rpt` | — |
| 75 | `NFDR811` | §7.8 | 表格帶過 | 活 | SP×1 | 無 `.rpt` | — |
| 76 | `NFDR812` | §7.8 | **已深寫** | 活 | SP×3 | 3 / 3 | 是 |
| 77 | `NFDR814` | §7.8 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 78 | `NFDR815` | §7.8 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 79 | `NFDR816` | §7.8 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 80 | `NFDR558` | §7.9 | **已深寫** | 活 | SP×1 | 1 / 1 | 是 |
| 81 | `NFDR559` | §7.9 | 表格帶過 | 活 | SP×1 | 2 / 2 | 是 |
| 82 | `NFDR560` | §7.9 | 表格帶過 | 活 | SP×2 | 2 / 2 | 是 |

**統計**:深寫 23 支、表格帶過 59 支;`m_db` 活 45 支(含 `dbTA` 變體 2 支)、**死 37 支**;`.rpt` 125 張 **125 / 125 在版控且在 csproj**;5 支無 `.rpt`;SP 100 支 **版控內 0 支**;**不在 csproj 的檔案:0**。

## 附錄 E. 讀本文時要注意的地方(缺陷與陷阱)

每條附**錨點**與**嚴重度**。嚴重度判準:**高** = 會產生錯的對外文件或錯的法遵數字,或整支功能不可用;**中** = 會給錯的內部數字或讓維護者踩坑;**低** = 不影響正確性,只影響可讀性 / 可維護性。

### E-01 37 支報表按預覽就 `NullReferenceException` —— 嚴重度 **高**

`Basic_PO` 那一半的 `m_db` 恆為 `null`(§2.4)。三種宣告變體:`private Database m_db = null;`(32 支)、`private Database m_db;`(5 支)、建構子內三行註解掉的初始化(全部)。

- 錨點(代表):`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:18`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:21`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR501_PO.cs:43`

- 隱式 `null` 變體(grep `m_db = null` 抓不到):`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR202_PO.cs:19`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR204_PO.cs:19`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR205_PO.cs:19`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR206_PO.cs:19`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR207_PO.cs:18`

- 逐支名單:附錄 D 的 `m_db` 欄

- **業務後果**:11 份報表沒有任何替代品(§0.3),其中五份是定期定額的營運分析

- **不是補一行就好**:還要改參數型別(`SqlDbType`→`OracleDbType`)、參數名(`@x`→`ix` / `:x`)、SP 方言,見 §7.6.2

### E-02 `NFDR210` 的「必須全部結帳才可列印」從來沒有生效 —— 嚴重度 **高**

四個問題疊在同一個 method(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:101-133`):

| # | 問題 | 錨點 |
|---|---|---|
| 1 | `AND (` 開了沒關,SQL 語法錯誤 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:111` |
| 2 | `catch (Exception)` 吞掉例外 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:128-132` |
| 3 | `isChk` 預設 `true` = 通過 → **fail-open** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:103` |
| 4 | 三個 `<> '常數'` 對 `NULL` 回 `UNKNOWN`,漏抓 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR210_PO.cs:111-113` |

**這支印的是對外開立的「受益憑證中英文持有單位證明」。** 卡控結果實際上是 **記錄不擋**(連記錄都沒有)。詳見 §7.2.3。

### E-03 `NFDR168` 的結轉檢核漏掉 `NULL` —— 嚴重度 **高**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR168_PO.cs:113` 的 `OFD303A.ALLOT_CTL_CODE <> '3'`:Oracle 三值邏輯,`NULL` 的那幾天不被算成「未結轉」→ 檢核通過 → 現金交易監控表印的是未結轉的半套資料。卡控結果:**過濾(無提示)**。

與 E-02 是同一型、同一張表(`OFD303A`)、不同報表。**改 `OFD303A` 的欄位語意會同時打到這兩支**(§8.3)。

### E-04 `NFDR704` 的指託戶檢核例外時放行 —— 嚴重度 **中**(修活 `m_db` 後變 **高**)

`IsBFExsits` 例外回 `-1`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:137`),UI 只擋 `== 0`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR704.cs:115`)。查詢炸掉 = 放行。詳見 §7.7.2。

### E-05 `NFDR223` 列印後回寫:條件被拿掉、筆數寫死、交易處理顛倒 —— 嚴重度 **高**

| # | 問題 | 錨點 |
|---|---|---|
| 1 | `AND RECEIPT_DOC_ID1 <> 'Y'` 被註解掉 → **已印過第一份文件的也會被更新** | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:267` |
| 2 | `j` 累加了 `ExecuteNonQuery` 的回傳,最後卻回報 `AddResultRow(true, 0, "")` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:283`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:288` |
| 3 | 正常路徑 `//trans.Commit();` 是註解,例外路徑卻有 `m_db.Rollback()` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:286`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR223_PO.cs:293` |

第 3 點是型錄裡「對已 Commit(或未開啟)的交易 `Rollback()` 吃掉原例外」的變形。詳見 §7.3.2。

### E-06 `NFDR201` 半套 Commit:兩張表的列印註記會不一致 —— 嚴重度 **高**(潛伏)

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:248` 第一段 `ExecuteNonQuery` 失敗會 `Rollback()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:251`);`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:255` 第二段的同樣檢查**整段被註解掉**(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:257-262`),然後直接 `Commit()`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:266`)。

`OFD724` 更新成功、`OFD721` 更新 0 筆時,交易照 Commit。**目前因為 `m_db` 是死的所以不會發生,修活之後立刻生效。**

同一支還有兩處 `AddResultRow(true, 1, "")` 把筆數寫死成 `1`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:265`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:269`)。

### E-07 T-SQL 方言殘留在 Oracle 環境 —— 嚴重度 **高**(潛伏)

37 支死的 PO 全部是 T-SQL 寫法,其中**寫得出具體語法問題的**:

| 語法 | 支 | 錨點 |
|---|---|---|
| `[表名]` 方括號 | `NFDR201` `NFDR241` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:101`、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:54` |
| `ISNULL(…)` | `NFDR201` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:105` |
| `CONVERT(VARCHAR, …)` + `dbo.PADLeft(…)` + `+` 串字串 | `NFDR203` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR203_PO.cs:90-91` |
| `EXEC proc @p = @v` 整句寫在字串裡 | `NFDR241` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:132` |
| `@參數` 命名 + `SqlDbType` | 37 支全部 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR704_PO.cs:54` |

**最刺眼的一組**:`NFDR241`(死,`[OFD038]` + `@FUND_GROUP`)與 `NFDR243`(活,`OFD038A` + `:FUND_GROUP`)是**同一段撈基金下拉的程式碼**,一支遷了一支沒遷(§7.4.2)。

### E-08 全形空白 U+3000 混進程式碼 —— 嚴重度 **低**

8 支中獎,共 49 處。集中在 `8xx` 模板群與 `NFDR201`:

| 支 | 處數 | 代表錨點 |
|---|---|---|
| `NFDR201` | 32 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR201_PO.cs:50` |
| `NFDR803` | 4 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR803_PO.cs:64` |
| `NFDR800` | 3 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:73` |
| `NFDR804` `NFDR805` `NFDR814` `NFDR815` `NFDR816` | 各 2 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR805_PO.cs:65` |

編譯沒事(它在字串外、被當空白),但 diff / 格式化 / 對齊會亂。**`NFDR805` 與 `NFDR815` 連全形空白的位置都一樣**,這是它們相似度 0.963 的證據之一。

### E-09 成對報表只改一邊 —— 嚴重度 **中**

本片有五組:

| 組 | 相似度 | 不對稱在哪 | 錨點 |
|---|---|---|---|
| `NFDR806` / `NFDR807` | 0.996 | 只差代號字串,業務完全不同 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR806_PO.cs:61` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR807_PO.cs:61` |
| `NFDR805` / `NFDR815` | 0.963 | 只差參數名 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR805_PO.cs:64` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR815_PO.cs:63` |
| `NFDR431` / `NFDR432` | — | 期間參數一支叫 `MONTH_S` / `MONTH_E`,一支叫 `Month` / `Month_E` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR431_PO.cs:86` vs `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR432_PO.cs:79` |
| `NFDR236` / `NFDR237` | — | `NFDR237Model.xsd` 有 30 個 Caption,`NFDR236Model.xsd` 0 個;`.rpt` 2 張 vs 4 張 | `Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR237Model.xsd` |
| `NFDR241` / `NFDR243` | — | 同一段程式碼一支 T-SQL 一支 Oracle(E-07) | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR241_PO.cs:54` |
| `NFDR701`–`NFDR707` 五支 | — | 五支 PO 100–101 行,只差 SP 名 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR701_PO.cs:44` |

### E-10 `switch` / if-else 沒有 `default` —— 嚴重度 **中**

報表類別落在列舉外時,`LoadDataSet` 完全不執行,筆數維持 `0`,**印出空白報表,沒有任何提示**。卡控結果:**過濾(無提示)**。

| 支 | 錨點 |
|---|---|
| `NFDR431` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR431_PO.cs:113` |
| `NFDR432` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR432_PO.cs:106` |
| `NFDR812` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR812_PO.cs:116` |
| `NFDR436` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR436_PO.cs:60` |

`NFDR431` / `NFDR432` 還多一層:`Convert.ToInt32(REPORT_TYPE)` 對空字串會丟 `FormatException`,一樣被外層 `catch` 吃掉。

### E-11 `NFDR514` 把使用者選的「日」無聲改成整月 —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR514_PO.cs:63-66` 用 `Substring(0, 8) + "01"` 把起日改成當月 1 日,迄日推到當月最後一天。UI 標「統計年月」,所以語意是對的,但**畫面上是日期控制項,使用者不知道日被忽略**。卡控:**過濾(無提示)**。

附帶:`Substring(0, 8)` 假設字串至少 8 碼,短於 8 碼丟 `ArgumentOutOfRangeException`。

### E-12 `catch` 裡裸 `tran.Rollback()` 蓋掉原例外 —— 嚴重度 **中**

`8xx` 群 15 支 + `NFDR514` + `NFDR515`,共 17 支。模式一樣:`finally` 有 `if (tran != null)` 判斷,`catch` 卻是裸呼叫。`BeginTransaction()` 之前發生的例外(參數轉型、`Substring` 越界)進 `catch` 時 `tran` 還是 `null` → `NullReferenceException` → **真因永遠看不到**。

- 錨點(模板本尊):`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:108` 對照 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:114`

- `NFDR514`:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR514_PO.cs:93`

### E-13 `NFDR812` 要求勾基金,然後把它丟掉 —— 嚴重度 **中**

UI 無條件驗證「基金明細必須勾選!!」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR812.cs:81`,卡控:**阻擋**),PO 卻只在 `nRptKind == 0 || nRptKind == 1` 時才把 `FUNDS` 送進 SP(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR812_PO.cs:101-109`)。選公會版 / 明細版時,勾的基金**完全不生效**。卡控結果:**過濾(無提示)**。

### E-14 零「查無資料」提示:67 支 —— 嚴重度 **中**

82 支裡只有 15 支會告訴使用者查無資料,**67 支靜默印一張空報表或匯出一個空 Excel**。

法遵報表印空白與「這期間真的沒有異常」長得一模一樣。`NFDR558`–`NFDR560`(公會英文申報)完全沒有判斷,查不到就匯出空 Excel 送公會(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR558.cs:161`)。卡控結果:**不擋**。

有提示的 15 支(代表):`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR202.cs:204`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR203.cs:198`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR437.cs:105`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR514.cs:125`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR810.cs:97`。

前片 `nfdr1.md` 是 44 支裡 30 支沒提示;**兩片合計 126 支,97 支沒有「查無資料」提示**。

### E-15 `.rpt` 在版控、在 csproj、卻沒人引用 —— 嚴重度 **低**

| 孤兒 | 所屬 | 說明 |
|---|---|---|
| `NFDR431RPS3_1.rpt` | `NFDR431` | UI 只引用 `RPS`–`RPS4` |
| `NFDR432RPS4.rpt` | `NFDR432` | UI 只引用 `RPS`–`RPS3` |
| `NFDR236RPS.rpt` | `NFDR236` | 舊版型,引用它的四行被註解(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR236.cs:77-92`) |
| `NFDR237RPS.rpt` | `NFDR237` | 同上 |
| `NFDR223RPS.rpt` | `NFDR223` | 註解說「20090319 改用新的報表格式」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR223.cs:90`) |

**這是「反向懸空」**:不是程式指到不存在的檔(`ofdr1.md` 那型),是檔在但沒人指。不會出錯,但改版型時容易改錯檔。

### E-16 `NFDR170` 的結果集用了 `NFDR169` 的名字 —— 嚴重度 **低**

`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR170Model.xsd` 的兩張結果集叫 `NFDR169` / `NFDR169_1`。不會出錯,但 **grep `NFDR170` 找不到它的結果集**,影響面分析會漏。

### E-17 `NFDR243` 有一張結果集永遠是空的 —— 嚴重度 **中**

`Dev/ATLAS.NFD.Report/Source/Entity/ReportDataEntity.NFD/NFDR243Model.xsd` 宣告四張(`_FUND` / `_CNTL` / `_BF` / `_TRADE`),PO 只開三個 `RefCursor`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR243_PO.cs:105`)。`NFDR243_TRADE` 在報表上永遠空白,**不會報錯**。與 `nfdr1.md` 附錄 E-07 同型。

### E-18 `NFDR204` 與 `NFDR206` 報表中文名完全相同 —— 嚴重度 **低**

兩支都叫「受益憑證(憑證號碼)作廢明細表」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR206.cs:119`)。使用者從選單上分不出來。

### E-19 `NFDR201` 的報表名是空字串 —— 嚴重度 **低**

`SetQueryParameters("NFDR201RPS", "NFDR201RPS", "")`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR201.cs:104`)。Crystal 標頭印空白。

### E-20 `NFDR222` 的 `FormType = 2` 沒有名字 —— 嚴重度 **低**

`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:48` 的 if-else 鏈只認 `0` / `1` / `3`,但 `Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR222.cs:66` 又把 `2` 當有效值。選到 `2` 時報表標頭印空白。卡控:**過濾(無提示)**。

### E-21 `NFDR225` 的受益人 ID 格式驗證整組被註解 —— 嚴重度 **中**

三段檢查(統一編號格式 / 身分證字號格式 / 兩者皆非)全部註解掉(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR225.cs:57`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR225.cs:70`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR225.cs:85`)。原本是**詢問 / 阻擋**,現在是**不擋**——格式錯的 ID 直接送 SP,查不到印空白。

### E-22 `NFDR814` 的金額標頭吃 client 的地區設定 —— 嚴重度 **低**

`Convert.ToDecimal(this.unumBAL_AMT1.Value).ToString("C")`(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR814.cs:56`)。同一份報表在不同語系的機器上,金額符號不一樣。

### E-23 100 支 SP 全部不在版控 —— 嚴重度 **高**

§2.2。改欄位時 repo 內改不到取數那一半,**沒有 diff、沒有 review、沒有回溯**。影響面分析天生不完整(§8.4)。

### E-24 寫死的客戶常數 —— 嚴重度 **低**

`NFDR434` 開畫面就寫死 `AGENT_ID = "2"` + `AGENT_CODE = "K5920"`(元富證券)(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR434.cs:60-61`);`NFDR210` 寫死落款「中國信託商業銀行股務代理部」(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR210.cs:46`)。換機構要改程式重編。完整清單在附錄 C。

### E-25 「此項功能無作用」的按鈕 —— 嚴重度 **低**

`NFDR810` / `NFDR811` 的「執行」鈕按下去只跳一個訊息框(`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR810.cs:140`、`Dev/ATLAS.NFD.Report/Source/UI/ReportUI.NFD/NFDR811.cs:136`)。刻意留著的死按鈕。

### E-26 只讀報表卻開交易,而且 `CommandTimeout = 0` —— 嚴重度 **低**

`8xx` 群 15 支 + `NFDR434` / `NFDR436` / `NFDR437` / `NFDR514` / `NFDR812` 都是 `BeginTransaction()` → `LoadDataSet` → `Commit()`,而且全部設 `CommandTimeout = 0`(永久跑)。純查詢不需要交易,長查詢持有交易對併發不友善。

- 錨點:`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:63`(`CommandTimeout = 0`)、`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR800_PO.cs:64`(`BeginTransaction`)

### E-27 本片**沒有**踩到的型(逐條交代,免得下次重查)

| 型錄項目 | 本片查驗結果 |
|---|---|
| **報表 SP 用全域暫存表做權限過濾、兩人同按互相蓋掉**(`ofdr2.md` 的 `DELETE DSMR008T4;`) | **未發現同型**。本片唯一碰到的實體暫存表是 `SALR905T1`,而且清理碼帶 `WHERE USERDOMAIN=…`(有 user 隔離),何況整段已被註解、改用 `Rollback()`(§7.5.3)。`nfdr1.md` 那 17 張 `NFDR073T*` 全屬前片,本片**沒有自建任何實體暫存表** |
| **`INNER JOIN` 無聲吃資料**(`nfdr1.md` 的 `NFDR123_PO.cs:89`) | **PO 內零 `INNER JOIN`**(82 支實測)。看得到的 JOIN 全部是 `LEFT JOIN`。**但 72 支的 SQL 在版控外的 SP 裡,那邊有沒有查不到**(§7.4.2) |
| **`dataID` 截斷造成併發污染**(`nfdr1.md` 的 `Substring(0,22)`) | **未發現**。本片唯一的 `Substring` 是 `NFDR514` 的 `Substring(0,8)`,那是日期處理不是 ID(E-11) |
| **字串串接把使用者輸入接進 SQL** | **未發現**。9 支有 `strSQL +=`,但組的都是固定句型,使用者輸入一律走 bind 變數。**唯一的字串串接帶值**是 `NFDR437` 那段已被註解的 `string.Format("… USERDOMAIN='{0}'", …)`(§7.5.3) |
| **bind 變數漏冒號 / `LIKE` 餵給 `=`** | **未發現**(82 支 PO 全文掃過) |
| **`AND`/`OR` 缺括號** | **有,而且很嚴重** —— `NFDR210` 是缺**右**括號不是缺分組括號(E-02) |
| **`catch (SqlException)` 在 Oracle 是死碼** | **未發現**。本片的 `catch` 全部是 `catch (Exception ex)` |
| **非 UTF-8 來源檔** | **未發現**。82 支的 UI / PO / Ctl 共 246 個 `.cs` 全部是 `utf-8-sig`(UTF-8 with BOM) |
| **不在 csproj 的檔案** | **零**(§2.3) |
| **`.rpt` 不在版控** | **零**,125 / 125 都在(§2.3)。反向的孤兒有 5 張(E-15) |
| **報表欄位與 xsd 不同步** | **有一處可證**:`NFDR243_TRADE`(E-17)。其餘因 SP 在版控外,無法比對 |

## 附錄 F. 版本紀錄

| 版 | 日期 | 內容 |
|---|---|---|
| v1 | 2026-09-21 | 首版。`Dev/ATLAS.NFD.Report` 後 82 支(`NFDR168`–`NFDR933`)。與 `nfdr1.md`(前 44 支)合計涵蓋 `NFD` 全部 126 支,**全庫 909 支畫面模組篇收官** |

**本版的實測基準**(下次重查時對照):

| 項目 | 數字 |
|---|---|
| 畫面 | 82 支,全部是 R |
| `m_db` 活 / 死 | 45 / **37**(含 `dbTA` 變體 2 支算活) |
| SP | **100 支,版控內 0 支** |
| `.rpt` | **125 張,125 在版控、125 在 csproj、0 懸空**;5 支報表無 `.rpt`;5 張孤兒 |
| PO 內看得到表名 | 10 支(12%) |
| 外部表 | 16 張,自有 0 張,**會寫入 3 張** |
| `Model.xsd` 結果集 | 119 張;`msdata:Caption` 842 個(不可信,§2.6) |
| 「查無資料」提示 | 15 支有、**67 支沒有** |
| 全形空白 U+3000 | 8 支,49 處 |
| 來源檔編碼 | 246 個 `.cs` 全部 `utf-8-sig` |
| 不在 csproj | **0** |

由 build_doc.py v2.0.0 於 2026-09-21 10:43 產生 · 標題 119 · 圖 5 · 表格 79 · 程式錨點 268 · § 連結 180 · 引用檢查：畫面 94（缺 0） · Table 1（缺 0） · Report 4（缺 0） · 結果集 11（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
