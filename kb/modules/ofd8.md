<!-- 由 tools/build_copilot_kb.py 從 modules/ofd8.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFD8 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這一片最反直覺的三件事)、§4.3(`OFDM221A` 與 `OFDM231A` 的分工)、§8(跨模組)、附錄 E(踩雷)。

> ⚠ **範圍**:OFD 模組全庫 550 支畫面,本文**只寫 `DataEntity.OFD8` 這一片的 24 支 M 畫面**。同一張表若另有主檔畫面落在其他片(例如 `OFD724` 的 `OFDM723` / `OFDM724`),本文只從這 24 支的角度描述,並在 §8 指路。 ⚠ **本模組的業務意義**(§0)由表名、欄位 `msdata:Caption` 與程式註解**推測**,待選單表 / 對照表回填。 ⚠ **〔客戶特定〕**:機構代碼、境內外識別碼 `'2'`、券商代碼、銀行代碼為本站台的值。 ⚠ **〔共用〕**:標記的表同時服務 BBS / BMS / RSP / SDM / NFD 與 OFD 其他片(見 §8),改動要一起看。

## 0. 系統邊界與角色

### 0.1 這 24 支管什麼(推測)

24 支全部是 **M(維護)** 型別,全部落在 `Dev/ATLAS.OFD/` 這一個專案,六層檔名完全照鐵律(`architecture.md §2`)。 entity 兩層集中在 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/` 與 `Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/` —— **`OFD8` 是 entity 專案的分片編號,不是模組碼**;UI / Ctl / PO 三層仍在同一個 `*.OFD` 專案裡,沒有分片。所以「第 8 片」是 entity 的分卷,不是業務上的分群 —— 這一點會影響你找檔案的直覺,先記住。

把 24 支依主檔的業務語意歸類,可以分成**六條業務線**(全部標推測):

| 業務線 | 畫面 | 主檔 | 一句話 |
|---|---|---|---|
| ① 境內基金申購 / 買回交易主線 | `OFDM221A` `OFDM231A` `OFDM242` | `OFD220A` `OFD251A` | 開申購書、開買回書、投資組合契約贖回 |
| ② 交易的周邊登錄 | `OFDM243A` `OFDM271` `OFDM337` `OFDM270` | `OFD243A` `OFD724` `OFD337A` `OFD270A` | 券商配單、缺件到件、退件、退郵戶 |
| ③ 基金費率與參數 | `OFDM091` `OFDM233` `OFDM285` `OFDM321` | `OFD091A` `OFD260A` `OFD290A` `OFD321` | 遞延手續費率、短線交易費率、匯費、銷售額度 |
| ④ 每日行情與彙總 | `OFDM300` `OFDM301` `OFDM302` `OFDM297` `OFDM220` `OFDM232` | `OFD300` `OFD301` `OFD302A` `OFD297A` `OFD232A` `OFD259A` | 匯率、交叉匯率、淨值、臨時放假、申購/買回銷售機構彙總 |
| ⑤ 配息作業 | `OFDM281` `OFDM284` `OFDM286` | `OFD281A` `OFD286A` `OFD291` | 配息設定、受益人支付方式、受益人配息期間 |
| ⑥ 檔案格式與雜項客戶設定 | `OFDM264` `OFDM331` `OFDM344` `OFDM361` | `OFD264A` `OFD331` `OFD344` (無) | 付款媒體檔格式、客訴、資料保密設定、未完成的空殼 |

**分片不等於分業務**:同一條業務線的畫面散在不同 `OFD` 片(例如買回主檔 `OFD251A` 的批次 `OFDB321`–`OFDB331` 都不在本片), 反過來本片內部六條線之間的程式呼叫也很少 —— 幾乎全靠表相連。這與 DSM 的情形一致(`dsm.md §1`)。

### 0.2 這一片最反直覺的三件事

**(1) 「覆核才生效」在這一片完全不成立。** `OFDM221A` 與 `OFDM231A` 的 `AfterVerify` / `AfterApprove` 主體**只有一行跳號紀錄,零業務 SQL** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2701-2717`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3975-3989`)。真正的跨表副作用 —— 更新過帳控制檔 `OFD303A`、櫃台控制檔 `CTL012` / `CTL022`、回寫申購明細 `OFD221A` 的贖回中單位數 —— 全部掛在 `AfterAdd` / `AfterUpdate` / `BeforeAdd` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:231-303`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2200-2236`)。 **輸入按下去,帳上就動了**;四眼只是軌跡。這正是 `architecture.md §3` 那條「不能假設覆核前資料還沒動」的第三個實證。

**(2) 六支畫面掛在已經跑不動的舊世代基底上。** `OFDM242` `OFDM284` `OFDM285` 繼承 `MultiRowEVAPO`,`OFDM321` `OFDM331` `OFDM344` 繼承 `BasicEVAPO` (`OFDM361` 的 PO 也是 `BasicEVAPO`,但整個類別是空的)。這兩支基底的 `dbTA` / `dbPTPF` 建構子賦值**整段被註解** (`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:167-175`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175`), 而 `Add` 第一行就是 `cn = dbTA.CreateConnection()`(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187`)。佐證:這六支的 SQL 裡還留著 SQL Server 的方括號識別字 `[OFD321]` / `[BMS001]`,`OFDM242` 更是整段 T-SQL 批次(`DECLARE @x` / `@@FETCH_STATUS`)。 **假設**:這批畫面在 SQL Server → Oracle 遷移時被放著沒動,現況不可執行。依據見附錄 E-1;要推翻只需在現場按一次新增。

**(3) 掃描器報的主檔不一定是真主檔。** `OFDM271` 宣告 `MasterTable = OFD724`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32`), 但**整支程式只有這一行提到 `OFD724`** —— 它實際維護的是缺件檔 `OFD272A`(§4.8)。 `OFDM361` 則是連 `MasterTable` 都沒宣告,因為 Ctl / PO 是空類別(§4.12)。

### 0.3 不管什麼

| 不在這 24 支裡 | 由誰管 |
|---|---|
| 申購 / 買回的**結帳、過帳、對帳批次** | `OFDB302` `OFDB304` `OFDB306` `OFDB310` `OFDB321`–`OFDB331`(OFD 其他片) |
| 受益人基本資料、受益人異動 | BMS 模組(`bms.md`);本片只 join `BMS001` 唯讀 |
| 受益憑證的換發 / 掛失 / 質設 / 轉讓 | BBS 模組(`bbs.md`);轉讓會反過來寫本片的 `OFD220A`(§8.1) |
| 定期定額(小額契約)本身 | RSP 模組;只在缺件檔 `OFD272A` 上交會(§8.2) |
| 報表與查詢 | 本片一支都沒有(§5 §6 §7) |
| 收益分配的**計算與發放批次** | `OFDB281` 等;本片只設定參數(`OFDM281`)與受益人選項(`OFDM284` `OFDM286`) |

### 0.4 使用角色

程式裡沒有角色表,只能從四眼欄位與畫面行為反推,全部標**推測**:

| 角色 | 做什麼 | 依據 |
|---|---|---|
| 交易輸入人員 | 開申購書 / 買回書、登錄缺件與退件 | `ENTRYID` 由 `EVAType.Add` 寫入(`architecture.md §3`) |
| 覆核人員(兩眼) | 驗證 + 覆核 | `VERIFYID` / `APPROVEID`;本片除 `OFDM271` 外全部有四眼 13 欄 |
| 基金 / 商品管理 | 維護費率、額度、匯率、淨值 | ③ ④ 兩條線的畫面沒有交易欄位,只有參數 |
| 客服 | 客訴 `OFDM331`、退郵 `OFDM270`、保密設定 `OFDM344` | 欄位帶 `COMPLAIN_*` / `REJ_*` / `QT_RSN` |

### 0.5 全域開關

沒有集中式開關。實際會整片改變行為的三個東西:

| 開關 | 在哪 | 影響 |
|---|---|---|
| 過帳控制檔 `OFD303A` 的 `ALLOT_CTL_CODE` / `REDEM_CTL_CODE` | 由 `OFDM221A` `OFDM231A` `OFDM220` `OFDM232` 四支一起寫 | 控制某基金某控制日的申購 / 買回是否已結轉;結轉後多數畫面禁止刪改 |
| 櫃台關帳 `CTL022` | `OFDM221A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1580`)、`OFDM231A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2522`) | 關帳後不可再建檔 |
| 境內外識別碼 `SHORE_ID = '2'` | `OFDM221A` 寫死(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:924`) | 這一片的申購缺件只看境內基金〔客戶特定〕 |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD8 全景:交易主線、周邊登錄、費率參數、行情彙總、配息、檔案格式六條線
圖中文字:① 交易主線:本片四成程式量在這三支,而且「輸入當下帳就動了」 / OFDM221A / 申購 主檔 OFD220A / OFDM231A / 買回/轉換 主檔 OFD251A / OFDM242 / 投資組合贖回 舊世代 / OFD303A CTL012 CTL022 / 過帳與櫃台控制檔 手寫SQL / ② 交易的周邊登錄:缺件、退件、退郵、券商配單 / OFDM271 / 缺件到件 直接UPDATE / OFDM337 / 退件 主檔 OFD337A / OFDM270 / 退郵戶 主檔 OFD270A / OFDM243A / 券商配單 主檔 OFD243A / ③ 基金費率與參數:被 ① 讀去計費,但額度只警示不擋 / OFDM091 / CDSC費率 OFD091A/092A / OFDM233 / 短線交易費率 OFD260A / OFDM285 / 基金匯費 OFD290A / OFDM321 / 銷售額度 舊世代 / ④ 每日行情與彙總:全庫金額計算的基礎,卡控卻最少 / OFDM300 / 幣別匯率 OFD300 / OFDM301 / 交叉匯率 OFD301 / OFDM302 / 基金淨值 OFD302A / OFDM297 / 臨時放假 OFD297A / OFDM220 OFDM232 / 申購/買回彙總 / ⑤ 配息作業:只設定參數,計算在 OFDB281 / OFDM281 / 配息設定 三張表 / OFDM284 / 支付方式 舊世代 / OFDM286 / 配息期間 OFD291 / OFDB281〔別片〕 / 配息計算批次 / ⑥ 檔案格式與雜項:含一支從未接上資料庫的空殼 / OFDM264 / 付款媒體檔格式 三張表 / OFDM331 / 客訴 舊世代 四張明細 / OFDM344 / 資料保密設定 舊世代 / OFDM361 / 三層空類別 無主明細
```

*圖:圖 1 OFD8 全景。橘框=值得先讀的主角;白框=一般維護畫面;橘虛框=舊世代基底或有風險的做法;灰虛框=別片的畫面;黑框=不在掃描母體的控制檔。六條線之間幾乎沒有程式呼叫,全靠表相連——尤其 ① 的三支在輸入當下就寫控制檔,四眼只留軌跡。*

### 1.2 資料表關係

圖 2 畫的是 24 支畫面的主明細配對,以及 `OFDM221A` / `OFDM231A` 共用的五張表 (`OFD136A` `OFD220A` `OFD221A` `OFD243A` `OFD272A`)。三個要點:

1. **主檔與明細不是一對一的樹。** `OFD220A` 在 `OFDM221A` 是主檔,在 `OFDM231A` 卻是明細; `OFD251A` 在 `OFDM231A` / `OFDM242` 都是主檔,兩支都會建它。

2. **本片有兩張「沒有任何畫面是它主檔」的表**:`OFD272A`(缺件)與 `OFD136A`(交易指示代理人)。它們永遠以明細身分被寫(§2.4、§8.2)。

3. **實體表名與 vdb 別名常常不同名。** `OFD251A` 在 `OFDM231A` 的 vdb 名是 `OFDM231A_Master`, 在 `OFDM242` 是 `OFD251A`。查 xsd 要認 vdb 名,查 SQL 要認實體表名(`architecture.md §5`)。

### 1.3 主要維護畫面的四眼與卡控順序

圖 3 拆的是 `OFDM221A` / `OFDM231A` 兩大支的卡控分層。順序固定四層:

| 層 | 誰 | 這一片的實況 |
|---|---|---|
| ① 欄位驗證 | `validatorManager1.DataValidate()` | 24 支全部有,錯誤塞 `ValidateErrList` |
| ② 畫面業務檢核 | UI 的 `DoValidate()` / `Chk*()` | 卡控幾乎全在這層;`OFDM221A` 一支就有 8 個 `Chk*` |
| ③ 伺服端檢核 | PO 的 `Check*<T>()` 公開方法 | **不是 EVA 掛點**,是 UI 主動呼叫的 RPC;繞過 UI 就完全不會跑 |
| ④ EVA 掛點 | `BeforeAdd` / `AfterUpdate` … | 這一片拿來**寫跨表副作用**,不是拿來擋 |

**最重要的一句**:③ 的 `Check*` 方法(例如 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-2646` 共 12 支) 雖然在伺服端執行,但它是 UI 主動叫的。真正的「第二道防線」(`BeforeAdd` 內部否決)在這一片**只有取號與副作用,沒有業務否決**。所以 §4 各節卡控總表裡標「阻擋」的,絕大多數是 UI 層阻擋。

### 1.4 批次 / 報表資料流

**本片無 B 與 R 畫面**(§6 §7)。但這 24 支是批次的上游,關係如下:

| 本片寫什麼 | 下游批次讀什麼 |
|---|---|
| `OFDM221A` 寫 `OFD220A` / `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDB310` 結帳與過帳 |
| `OFDM231A` / `OFDM242` 寫 `OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` | `OFDB321`–`OFDB331` 買回結帳、付款 |
| `OFDM302` 寫淨值 `OFD302A`、`OFDM300` / `OFDM301` 寫匯率 | 幾乎所有金額計算 |
| `OFDM281` 寫配息參數 `OFD281A` | `OFDB281` 配息計算 |
| `OFDM264` 寫媒體檔格式 `OFD264A` / `OFD265A` / `OFD266A` | 付款媒體檔產檔程式 |

### 1.5 一日作業泳道

依欄位語意推測的一天(**推測**,程式內沒有排程表):

| 時段 | 誰 | 做什麼 | 畫面 |
|---|---|---|---|
| 開盤前 | 商品管理 | 建當日匯率、交叉匯率;必要時設臨時放假 | `OFDM300` `OFDM301` `OFDM297` |
| 營業中 | 交易輸入 | 收件 → 開申購書 / 買回書 → 缺件登錄 | `OFDM221A` `OFDM231A` `OFDM242` `OFDM271` |
| 營業中 | 覆核 | 驗證 + 覆核(但帳已經動了,見 §0.2) | 同上 |
| 收盤後 | 商品管理 | 建當日淨值 | `OFDM302` |
| 收盤後 | 代銷組 | 建銷售機構申購 / 買回彙總 | `OFDM220` `OFDM232` |
| 隔日 | 客服 | 退件 / 退郵 / 客訴後續 | `OFDM337` `OFDM270` `OFDM331` |

## 2. 資料模型

```text
[圖] OFD8 四十五張表的主明細配對,以及 OFDM221A 與 OFDM231A 共用的五張表
圖中文字:申購側:OFDM221A 是 OFD220A 的主檔,外加六張明細 / OFD220A〔共用〕 / 申購書 PK ALLOT_NO / OFD221A〔共用〕 / + ALLOT_SRNO 125欄 / OFD234A OFD235A / 支票/匯款 無主檔畫面 / OFD220A_AGENT / 意定代理人 PK同主檔 / 買回側:OFDM231A 是 OFD251A 的主檔,外加九張明細 / OFD251A / 買回書 PK REDEM_NO / OFD252A OFD253A / 付款 / 轉換明細 / OFD254A OFD258A / 指定沖銷 / 憑證明細 / OFD251A_AGENT / vdb名叫 OFD231A_AGENT / 兩大支共用的五張表——本篇最需要記住的一列 / OFD136A / 交易指示代理人 無主檔 / OFD220A / 221A主檔 / 231A明細 / OFD221A / 兩支都寫 RDMING_UNIT / OFD243A / 主檔在 OFDM243A / OFD272A / 缺件 無主檔 / 費率與參數:兩組結構相同的主明細 / OFD091A / OFD092A / CDSC 主檔+區間 / OFD260A / OFD261A / 短線費率 主檔+區間 / OFD321 / OFD322 / 額度 主檔+通路明細 / OFD281A 287A 288A / 配息 主檔+兩明細 / 單表畫面:七張沒有明細的表 / OFD232A OFD259A / 申購/買回彙總 / OFD300 OFD301 / 匯率/交叉匯率 / OFD302A / 基金淨值 / OFD286A OFD290A / 支付方式/匯費 / OFD291 OFD344 / 配息期間/保密 / 外部唯讀或手寫 SQL(不在 xTableMapping,改欄位沒有 xsd 提醒) / OFD303A OFD304A / 過帳控制檔 / CTL012 CTL022 / 櫃台/代扣款控制 / OFD130A OFD131A / 匯款授權書 / OFD721 OFD039A / 憑證餘額/缺件代碼 / BMS001 / 受益人 唯讀
```

*圖:圖 2 資料模型。橘框=主檔或兩大支共用的表;白框=一般明細與單表;灰虛框=沒有主檔畫面、被別的模組共同寫入;黑框=不在掃描母體、只靠手寫 SQL 觸碰。中間那一排五張是本篇的重點:OFD220A 在一支是主檔、在另一支是明細,OFD272A 則誰都不是它的主檔。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

24 支畫面一共宣告 **45 張實體表**(去重),分佈如下。「vdb 名」是 `xTableMapping` 的第二個參數, 也就是 xsd 裡的 DataTable 名 —— **兩者常常不同名,查 xsd 要用 vdb 名**。

| 畫面 | 主檔(實體表 / vdb 名) | 明細(實體表 → vdb 名) | 錨點 |
|---|---|---|---|
| `OFDM091` | `OFD091A` / `OFDM091_Master` | `OFD092A` → `OFDM091_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091_PO.cs:39-40` |
| `OFDM220` | `OFD232A` / `OFDM220` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:49` |
| `OFDM221A` | `OFD220A` / `OFDM221A` | `OFD221A` → `OFDM221A_Detail`;`OFD272A` → `OFD272`;`OFD234A` → `OFD234`;`OFD235A` → `OFD235`;`OFD243A` → `OFD243`;`OFD220A_AGENT`;`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67-76` |
| `OFDM231A` | `OFD251A` / `OFDM231A_Master` | `OFD252A` → `OFDM231A_Redem`;`OFD253A` → `OFDM231A_Switch`;`OFD272A` → `OFD272`;`OFD254A` → `OFDM231A_Offset`;`OFD258A` → `OFDM231A_CerData`;`OFD220A` → `OFDM231A_Allot`;`OFD251A_AGENT` → `OFD231A_AGENT`;`OFD221A` → `OFDM231A_AllotDetail`;`OFD243A` → `OFD243`;`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70-82` |
| `OFDM232` | `OFD259A` / `OFDM232` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:50` |
| `OFDM233` | `OFD260A` / `OFDM233_Master` | `OFD261A` → `OFDM233_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:43-44` |
| `OFDM242` | **三個主檔**:`OFD251A` `OFD252A` `OFD254A`(多筆型) | —(`MultiRowEVAPO` 沒有明細概念) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:33-35` |
| `OFDM243A` | `OFD243A` / `OFDM243A` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:42` |
| `OFDM264` | `OFD264A` / `OFDM264_Master` | `OFD266A` → `OFDM264_FileRule`;`OFD265A` → `OFDM264_Field` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:35-37` |
| `OFDM270` | `OFD270A` / `OFDM270` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM270_PO.cs:44` |
| `OFDM271` | `OFD724` / `OFDM271`(**名義上**,見 §4.8) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32` |
| `OFDM281` | `OFD281A` / `OFDM281` | `OFD287A` → `OFDM281_Detail`;`OFD288A` → `OFDM281_Rate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:43-49` |
| `OFDM284` | `OFD286A` / `OFDM284`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:38` |
| `OFDM285` | `OFD290A` / `OFDM285`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM285_PO.cs:20` |
| `OFDM286` | `OFD291` / `OFDM286`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM286_PO.cs:35` |
| `OFDM297` | `OFD297A` / `OFDM297`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM297_PO.cs:39` |
| `OFDM300` | `OFD300` / `OFDM300`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM300_PO.cs:41` |
| `OFDM301` | `OFD301` / `OFDM301`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM301_PO.cs:41` |
| `OFDM302` | `OFD302A` / `OFDM302`(多筆型) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| `OFDM321` | `OFD321` / `OFDM321` | `OFD322` → `OFDM321_Detail` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:30-31` |
| `OFDM331` | `OFD331` / `OFDM331` | `OFD332` → `OFDM331_Complain`;`OFD333` → `OFDM331_Complain_K`;`OFD334` → `OFDM331_Solve`;`OFD335` → `OFDM331_Solve_K` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:32-37` |
| `OFDM337` | `OFD337A` / `OFDM337` | `OFD346A` → `OFDM337_REJ_ITEM` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:46-47` |
| `OFDM344` | `OFD344` / `OFDM344` | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:31` |
| `OFDM361` | **未宣告**(PO 是空類別) | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10` |

三個要留意的地方:

1. **`OFDM331` 的 `_K` 後綴語意是反的。** `OFDM331_Complain`(`OFD332`)存的是**客訴代碼**、`OFDM331_Complain_K`(`OFD333`)存的是**客訴內容文字**; 反過來 `OFDM331_Solve`(`OFD334`)存**處理說明文字**、`OFDM331_Solve_K`(`OFD335`)存**處理種類代碼**。同一個 `_K` 在兩組裡分別代表「文字」與「代碼」—— 命名沒有一致規則,別靠後綴猜。

2. **`OFDM242` 的 xsd DataTable 全部叫 `OFDM643` 系列。** `OFDM242Model.xsd` 裡是 `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`,而全庫**沒有 `OFDM643` 這支畫面** (`atlas_scan.py --screen OFDM643` 回「找不到畫面」)。三層一共 56 處引用這個名字 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM242_Ctl.cs:56`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:200`)。 **用 `OFDM242` 當關鍵字 grep 會漏掉它真正的資料表。**

3. **`OFDM221A` 與 `OFDM231A` 共用五張明細表**:`OFD136A` `OFD220A` `OFD221A` `OFD243A` `OFD272A`。這五張的 vdb 名在兩支之間有的相同(`OFD272` `OFD243` `OFD136A`)、有的不同(`OFD220A` 在後者叫 `OFDM231A_Allot`)。細節見 §4.3。

### 2.2 主鍵與四眼欄位

從各 `Model.xsd` 的 `msdata:PrimaryKey="true"` 宣告抄出來(`architecture.md §5`)。「四眼欄位」指 `STATUS` / `CREATEID` / `UPDATEID` / `ENTRYID` / `VERIFYID` / `APPROVEID` / `REJECTID` / `DATAFLAG` 這 8 個檢查欄 (完整 13 欄見 `architecture.md §3`)。

| 實體表 | vdb 名 | 主鍵 | 四眼欄位 | 欄數 |
|---|---|---|---|---|
| `OFD091A` | `OFDM091_Master` | `FUND_ID` | 有 | 18 |
| `OFD092A` | `OFDM091_Detail` | `FUND_ID` + `BNG_DAY` | 有 | 19 |
| `OFD232A` | `OFDM220` | `FUND_ID` + `AGENT_ID` + `AGENT_CODE` + `ALLOT_DATE` | 有 | 48 |
| `OFD220A` | `OFDM221A` | `ALLOT_NO` | 有 | 77 |
| `OFD221A` | `OFDM221A_Detail` | `ALLOT_NO` + `ALLOT_SRNO` | 有 | 125 |
| `OFD234A` | `OFD234` | `ALLOT_NO` + `ALLOT_SRNO` + `CHECK_NO` | 有 | 21 |
| `OFD235A` | `OFD235` | `ALLOT_NO` + `ALLOT_SRNO` + `DATA_SEQ` | 有 | 22 |
| `OFD243A` | `OFD243` | `FUND_ID` + `ALLOT_NO` + `TRAN_DATE` + `STK_BRK` | 有 | 34 |
| `OFD272A` | `OFD272` | `SHORE_ID` + `ORG_COPY_CD` + `TRN_NO` + `TRN_CD` | 有 | 24 |
| `OFD220A_AGENT` | `OFD220A_AGENT` | `ALLOT_NO` | 有 | 17 |
| `OFD136A` | `OFD136A` | `TRADE_NO` + `TRADE_TYPE` | 有 | 19 |
| `OFD251A` | `OFDM231A_Master` | `REDEM_NO` | 有 | 93 |
| `OFD252A` | `OFDM231A_Redem` | `REDEM_NO` + `REDEM_SRNO` | 有 | 71 |
| `OFD253A` | `OFDM231A_Switch` | `REDEM_NO` + `REDEM_SRNO` | 有 | 92 |
| `OFD254A` | `OFDM231A_Offset` | `REDEM_NO` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | 44 |
| `OFD258A` | `OFDM231A_CerData` | `REDEM_NO` + `BF_CER_ISSUE_CODE` + `BF_CER_NO` | 有 | 35 |
| `OFD251A_AGENT` | `OFD231A_AGENT` | `REDEM_NO` | 有 | 17 |
| `OFD259A` | `OFDM232` | `FUND_ID` + `AGENT_ID` + `AGENT_CODE` + `REDEM_DATE` | 有 | 41 |
| `OFD260A` | `OFDM233_Master` | `FUND_ID` | 有 | 23 |
| `OFD261A` | `OFDM233_Detail` | `FUND_ID` + `BNG_DAY` | 有 | 23 |
| `OFD264A` | `OFDM264_Master` | `PAY_BANK` + `FILE_FORMAT` + `FILE_ID` | 有 | 25 |
| `OFD266A` | `OFDM264_FileRule` | 上列 + `DATA_SEQ` | 有 | 22 |
| `OFD265A` | `OFDM264_Field` | 上列 + `DATA_SEQ` | 有 | 29 |
| `OFD270A` | `OFDM270` | `REJ_NO` | 有 | 43 |
| `OFD281A` | `OFDM281` | `FUND_ID` + `YEARS` + `ISSUE_CODE` | 有 | 37 |
| `OFD287A` | `OFDM281_Detail` | 上列 + `DIV_TYPE` | 有 | 24 |
| `OFD288A` | `OFDM281_Rate` | 上列 + `DIV_TYPE` + `BF_CODE` | 有 | 24 |
| `OFD286A` | `OFDM284` | `DIV_NO` + `BF_NO` + `FUND_ID` | 有 | 36 |
| `OFD290A` | `OFDM285` | `FUND_ID` + `BANK_BRH` | 有 | 22 |
| `OFD291` | `OFDM286` | `BF_NO` + `FUND_ID` + `DIV_DATE_ST` | 有 | 23 |
| `OFD297A` | `OFDM297` | `VOC_NO` + `FUND_ID` | 有 | 27 |
| `OFD300` | `OFDM300` | `CDATE` + `EX_CD` + `CRNCY_CD` | 有 | 23 |
| `OFD301` | `OFDM301` | `CDATE` + `CRNCY_IN` + `CRNCY_OUT` | 有 | 24 |
| `OFD302A` | `OFDM302` | `FUND_ID` + `NAV_DATE` | 有 | 31 |
| `OFD321` | `OFDM321` | `FUND_ID` + `DATA_SEQ` | 有 | 22 |
| `OFD322` | `OFDM321_Detail` | 上列 + `AGENT_TYPE` + `DEPT_NO` + `CHANNEL_CD` + `CHANNEL_CODE` | 有 | 24 |
| `OFD331` | `OFDM331` | `COMPLAIN_NO` | 有 | 42 |
| `OFD332` | `OFDM331_Complain` | `COMPLAIN_NO` + `COMPLAIN_CODE` | 有 | 18 |
| `OFD333` | `OFDM331_Complain_K` | `COMPLAIN_NO` | 有 | 17 |
| `OFD334` | `OFDM331_Solve` | `COMPLAIN_NO` | 有 | 17 |
| `OFD335` | `OFDM331_Solve_K` | `COMPLAIN_NO` + `SOLVE_CODE` | 有 | 18 |
| `OFD337A` | `OFDM337` | `REJ_NO` | 有 | 36 |
| `OFD346A` | `OFDM337_REJ_ITEM` | `REJ_NO` + `REJ_ITEM` | 有 | 18 |
| `OFD344` | `OFDM344` | `BF_NO` + `CHG_DATE` | 有 | 22 |
| `OFD724` | `OFDM271` | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID`(見下) | 有 | 28 |

**四眼 8 欄全員到齊,一張不缺。**這一片沒有 DSM `BMS906` 那種「只有 7 欄、不走四眼」的表(`dsm.md §2`)。

三個例外要講清楚:

- **`OFDM271` 的 vdb `OFDM271` 帶的其實是 `OFD272A` 的欄位。** 28 欄裡有 `TRN_CD` `TRN_NO` `ORG_COPY_CD` `SHORE_ID` `LACK_DATE` `GET_COPY_UID` `GET_COPY_DATE`, PK 宣告與 `OFD272A` 一模一樣,另外多兩個純畫面欄 `ISCHECK`(註記)、`CANCHECK`(可否勾選), 以及一個 join 來的 `STOP_PAY`。`OFD724` 只是 `xTableMapping` 的裝飾(§4.8)。

- **`OFDM361` 的 vdb `OFDM361` 是 103 欄的潛在客戶表**,主鍵 `PR_NO`,與 `CRM003A` 同形(§4.12)。

- **`OFD221A` 有兩種形狀。** 本片 `OFDM221A` 的 `OFDM221A_Detail` 是 125 欄, 但 `OFDM243A` 的 xsd 裡同名表只有 7 欄、**沒有四眼欄位** (`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM243AModel.xsd`),掃描器索引拿到的更是 EC 專案那份 13 欄版。 **同一張實體表在三個 xsd 裡有三種形狀**,加欄位要三邊一起改(§8.1)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列各畫面**識別用**與**卡控會用到**的欄位;完整欄位請直接開對應 xsd(路徑見 §3.1)。中文名一律抄 `msdata:Caption`,沒有 Caption 的留空白。

#### 申購側(`OFD220A` / `OFD221A`)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `ALLOT_NO` | 申購書號 | PK;由 `SerialNo.GetAllotNoForNfd()` 取號 |
| `ALLOT_SRNO` | 序號 | 明細 PK 第二段 |
| `RCV_DATE` | 收件日期 | 必須是公司營業日 |
| `ALLOT_DATE` | 申購日期 | 不可小於收件日期 |
| `ALLOT_CODE` | — | 交易別;`1` 申購 / `2` 轉申購 / `4` 定期定額 |
| `ALLOT_PROC_CODE` | — | 處理碼;`0` 輸入 / `1` 已算單位數 / `2` 已結轉 / `D` 作廢 |
| `ETD_ALLOT_AMT` | 計價幣別申購金額 |  |
| `ALLOT_AMT` | 申購金額 | 中心幣別 |
| `ALLOT_FEE_RATE` | 申購手續費率 |  |
| `ALLOT_FEE` | 申購手續費 |  |
| `RDMING_UNIT` | — | 贖回中單位數;由 `OFDM231A` 回寫(§4.3) |
| `R_UNIT` | — | 剩餘單位數 |
| `FREEZE_UNIT` | — | 凍結單位數 |
| `COMPARE_NO` | — | 匯款比對流水號;有值就不可刪 |
| `REMIT_CTL_NO` | — | 匯款比對控制號;有值就不可刪 |
| `SUB_STATUS` | — | 代扣款狀態;`0` 尚未 / `1` 扣款中 / `2` 成功 / `3` 失敗 |
| `SOURCE_CD` | — | 來源;`1` 一般 / `2` TDCC 指託 / `3` 績效費轉入 |
| `FAVORED_REL_TYPE` | — | 優惠身份別;`BeforeAdd` 由 `ServerBizUtility.GetFavoredRelType` 算 |

#### 買回側(`OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` / `OFD258A`)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `REDEM_NO` | 買回書號 | PK;由 `SerialNo.GetRdmNoForNfd()` 取號 |
| `REDEM_TYPE` | 買回方式 |  |
| `REDEM_DATE` | 買回日期 |  |
| `REDEM_NAV_DATE` | 買回淨值日期 |  |
| `REDEM_UNIT` | 買回單位數 |  |
| `REDEM_PROC_CODE` | — | 買回處理碼;`3` = 已結帳(**無對應常數類別,程式寫死**) |
| `SHORT_ARTI_CTL` | — | 短線交易控管 |
| `SHORT_FEE_RATE` | — | 短線交易費率;來源是 `OFDM233` 維護的 `OFD261A` |
| `SWITCH_FUND_ID` | 轉入基金 | `OFD253A`;轉申購的目標基金 |
| `SWITCH_DATE` | 轉入日期 |  |
| `SWITCH_FEE_R` | 轉換費率(%) |  |
| `SWITCH_FEE_ALLOWANCE` | 轉申購拆帳比 |  |
| `CAN_REDEM_UNIT` | 可買回單位數 | `OFD254A`;指定沖銷時算 |
| `BF_CER_ISSUE_CODE` | 憑證期別號碼 | `OFD258A`;實體憑證買回 |
| `DOC_NID` | — | 缺件註記;`Y` 代表仍缺件 |
| `DOC_ADATE` | — | 缺件到齊日;由 `OFDM271` 回寫 |
| `STOP_PAY_YN` | — | 暫停付款 |

#### 缺件檔 `OFD272A`(本片最多人共用的表)

| 欄位 | 中文名 | 說明 |
|---|---|---|
| `TRN_CD` | 缺件種類 | 值域見 §2.5 |
| `TRN_NO` | 缺件編號 | 對應的交易書號 —— 申購放 `ALLOT_NO`、買回放 `REDEM_NO` |
| `ORG_COPY_CD` | 缺件代碼 | 對 `OFD039A` 的 `LACK_CODE` |
| `SHORE_ID` | 境內外基金識別碼 | `1` 境外 / `2` 境內 |
| `BF_NO` | 受益人戶號 |  |
| `LACK_DATE` | 缺件日期 |  |
| `GET_COPY_UID` | 到件更新人員 |  |
| `GET_COPY_DATE` | 到件日期 | 空值哨兵是**一個空白字元**,不是 NULL(§2.5) |
| `TRN_MEMO` | 備註 |  |

#### 其餘畫面的識別欄位

| 畫面 | 關鍵欄位(中文名) |
|---|---|
| `OFDM091` | `FUND_ID`(基金代碼)、`RANGE_TYPE`(贖回區間)、`BNG_DAY`(起算日／月)、`END_DAY`(終止日／月)、`CDSC_FEE_RATE`(遞延手續費率%) |
| `OFDM220` | `AGENT_ID`(銷售機構區別碼)、`AGENT_CODE`(銷售機構代碼)、`ALLOT_AMT`(銷售總金額)、`ALLOT_FEE`(銷售總手續費)、`AGENT_ALLOT_FEE`(銷售機構手續費) |
| `OFDM232` | `AGENT_ID`(買回機構區分碼)、`AGENT_RUNIT`(銷售機構買回單位數)、`RTOT_AMT`(買回總金額)、`TOT_RFEE`(總買回費) |
| `OFDM233` | `SHORT_FEE_RATE`(短線交易費率)、`MAX_AMT_YN`(是否判斷上限)、`MIN_AMT_YN`(是否判斷下限)、`DAY_TYPE`(行事曆認定)、`FEE_TYPE`(計算規則) |
| `OFDM243A` | `STK_BRK`(原始券商代碼)、`NSTK_BRK`(目前券商代碼)、`REBATE_AMT`(配單金額)、`REBATE_MULT`(配單倍數) |
| `OFDM264` | `PAY_BANK`、`FILE_FORMAT`(資料格式)、`FILE_DESC`(檔案格式說明)、`DIVIDE_UP`(是否分割筆數)、`IS_MULTI_CRY`(外幣適用)、`OUTPUT_FILED`(是否產生至磁片檔案) |
| `OFDM270` | `REJ_NO`(退郵單號)、`REJ_OBJ`(退郵項目代碼)、`REJ_CD`(退郵原因代碼)、`REJ_STATUS`(處理狀態)、`REJ_STOP_DATE`(永久失聯戶註記日期) |
| `OFDM281` | `YEARS`(年度)、`ISSUE_CODE`(期別)、`BASE_DATE`(分配基準日)、`VALUE_DEDUCT_DATE`(權值扣除日)、`PROVIDE_DATE`(發放日期)、`SWITCH_DATE`(再投資日期)、`PROCESS_CODE`(作業處理碼) |
| `OFDM284` | `DIV_NO`(收益分配支付方式書號)、`GET_WAY`(支付方式) |
| `OFDM285` | `BANK_BRH`(銀行代碼)、`CUS_BANK_BRH`(保管銀行代碼)、`REMIT_FEE`(匯費金額) |
| `OFDM286` | `DIV_DATE_ST`、`DIV_DATE_END`、`DIV_TYPE` |
| `OFDM297` | `VOC_NO`(臨時放假設定編號)、`BEF_NAV_DATE`(變更前淨值日期)、`AFT_NAV_DATE`(變更後淨值日期)、`EXE_STATUS` |
| `OFDM300` | `CDATE`(日期)、`EX_CD`(匯率屬性)、`CRNCY_CD`(幣別代碼)、`EX_RATE`(匯率) |
| `OFDM301` | `CRNCY_IN`(兌換入幣別代碼)、`CRNCY_OUT`(兌換出幣別代碼)、`EX_RATE`(匯率) |
| `OFDM302` | `NAV_DATE`(淨值日期)、`NAV_B`(正式淨值)、`BID_NAV`(申購淨值)、`OFFER_NAV`(贖回淨值)、`NAV_LOCK`(淨值鎖定)、`FUND_SIZE`(資產規模) |
| `OFDM321` | `DATA_SEQ`(資料流水號)、`BNG_DATE`(控管起始日期)、`END_DATE`(控管終止日期)、`TOT_QUOTA`(控管總額度)、`EQUAL_CHECK`(明細額度是否要等於總額度)、`QUOTA_AMT`(銷售機構額度金額) |
| `OFDM331` | `COMPLAIN_NO`(客訴序號)、`COMPLAIN_TYPE`(客訴對象種類)、`ASN_SOLVE_DEPT_NO`(客訴指定處理部門)、`SOLVE_HF_DATE`(客戶希望完成日期) |
| `OFDM337` | `REJ_NO`(退件單號)、`REJ_CD`(退件原因代碼)、`REJ_ITEM`、`OK_DATE`(文件補期日期)、`REJ_AGENT_CODE`(退件單位) |
| `OFDM344` | `CHG_DATE`(異動日期)、`BEF_BF_QT`(變更前客戶資料保密設定碼)、`AFT_BF_QT`(變更後客戶資料保密設定碼)、`QT_RSN`(保密原因) |

### 2.4 與其他模組共用的表

| 表 | 本片誰用 | 別的模組誰用 | 說明 |
|---|---|---|---|
| `OFD220A`〔共用〕 | `OFDM221A`(主檔)、`OFDM231A`(明細,會 INSERT) | `OFDB310`(主檔)、`OFDB331`(明細)、`BBSM013` `BBSM113`(明細,會 INSERT) | 申購書主檔;§8.1 |
| `OFD221A`〔共用〕 | `OFDM221A` `OFDM231A` `OFDM243A` | `OFDB302` `OFDB304` `OFDB306` `OFDI059` `SDMB001`(主檔)、`OFDB310` `OFDB331` `BBSM013` `BBSM113`(明細) | 申購明細;**三種 xsd 形狀**(§2.2) |
| `OFD234A`〔共用〕 | `OFDM221A`(明細) | `BBSM013` `BBSM113`(明細,會 INSERT) | 申購支票;**沒有任何畫面是它的主檔** |
| `OFD235A`〔共用〕 | `OFDM221A`(明細) | `BBSM013` `BBSM113`(明細,會 INSERT) | 申購匯款;同上 |
| `OFD243A`〔共用〕 | `OFDM243A`(主檔)、`OFDM221A` `OFDM231A`(明細) | — | 券商配單;三支都在本片 |
| `OFD272A`〔共用〕 | `OFDM221A` `OFDM231A`(明細)、`OFDM271`(直接 UPDATE) | `BMSM004` `BMSM006` `RSPM004` `RSPM005`(明細)、`BMSM001` `OFDB310` `OFDI011` `NFDR813`(唯讀) | 缺件檔;**沒有主檔畫面**;§8.2 |
| `OFD136A`〔共用〕 | `OFDM221A` `OFDM231A`(明細) | — | 交易指示代理人;**沒有主檔畫面**,兩支各寫各的一半(`TRADE_TYPE` 區分) |
| `OFD251A` | `OFDM231A` `OFDM242`(主檔) | `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` `SDMB002`(主檔) | 買回主檔;本片兩個入口 |
| `OFD724` | `OFDM271`(名義主檔) | `OFDB327` `OFDM723` `OFDM724`(主檔,**在 OFD9 那一片**) | §8.4;另見 `ofd9.md` |
| `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232`(手寫 SQL) | 全 OFD 批次 | 過帳控制檔;**不在任何 `xTableMapping` 裡,四支各寫各的 SQL** |
| `CTL012` `CTL022` | `OFDM221A` `OFDM231A`(手寫 SQL) | 櫃台關帳 | 同上,不在掃描母體 |
| `BMS001` | `OFDM221A` `OFDM284`(唯讀 join) | BMS 模組主檔 | 受益人基本資料 |
| `OFD039A` | `OFDM231A` `OFDM271`(唯讀 join) | 全庫缺件代碼表 | `LACK_CODE` / `STOP_PAY` / `LIMIT_ALLOT` 等 |
| `OFD721` | `OFDM231A`(直接 UPDATE) | BBS 憑證 | 實體憑證餘額 |
| `OFD130A` `OFD131A` | `OFDM221A` `OFDM231A`(INSERT / SELECT) | 匯款授權書 | 不在掃描母體 |
| `OFD607A` `OFD601` | `OFDM271`(UPDATE) | 網路交易受益人權限 | 缺件到齊後解鎖網路交易 |
| `OFD199A` | `OFDM221A`(唯讀) | 行銷活動 | `CheckCampignCodeData` 用 |

### 2.5 狀態碼(從程式反推,標來源)

除了四眼引擎自己的 `STATUS`(`architecture.md §3`),本片自己的代碼都放在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs`。 **有常數類別的照抄,沒有的標「程式寫死」。**

| 代碼 | 常數類別與錨點 | 值域 |
|---|---|---|
| 缺件種類 `TRN_CD` | `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:26-52` | `1` 開戶 / `2` 申購 / `3` 贖回轉換 / `4` 小額契約 / `5` 受益人異動 / `6` 定期定額異動 |
| 境內外 `SHORE_ID` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` | `1` 境外基金 / `2` 境內基金 |
| 是否 `YES_NO` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-20` | `Y` / `N` |
| 交易別 `ALLOT_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1830-1866` | `1` 申購 / `2` 轉申購 / `3` 除息 / `4` 定期定額 / `5` 轉讓 / `6` 合併 / `9` 調整 |
| 資料來源 `SOURCE_CD` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1929-1945` | `1` 一般 / `2` TDCC 指託 / `3` 績效費轉入 |
| 申購處理碼 `ALLOT_PROC_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1950-1971` | `0` 輸入 / `1` 已算單位數 / `2` 已結轉 / `D` 作廢 |
| 代扣款狀態 `SUB_STATUS` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2071-2092` | `0` 尚未 / `1` 扣款中 / `2` 成功 / `3` 失敗 |
| 申購資料控制碼 `ALLOT_CTL_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2194-2212` | `0` 無資料 / `1` 有資料 / `2` 已單位數計算 / `3` 已結轉 |
| 贖轉資料控制碼 `REDEM_CTL_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2216-2238` | `0` 無資料 / `1` 有資料 / `2` 已預估價金計算 / `3` 已價金計算 / `4` 已結轉 |
| 短線註記 `SHORT_RMK` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2925-2935` | `Y` / `N` |
| **買回處理碼 `REDEM_PROC_CODE`** | **無常數類別** | 程式只用到 `3` = 已結帳,寫死在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` |
| **退郵處理狀態 `REJ_STATUS`** | **無常數類別** | 由畫面下拉來源決定,程式內沒有比較字面量 |

**三個陷阱**:

1. **「已結轉」在申購側是 `3`、在買回側是 `4`。** `ALLOT_CTL_CODE.Tranfer` = `'3'`、`REDEM_CTL_CODE.Tranfer` = `'4'`,兩個常數**同名**(原文就少一個 `s`),值卻不同。 copy-paste 一定踩。

2. **`OFD272A` 的 `GET_COPY_DATE` 沒到件有兩種寫法並存。** `GET_COPY_DATE IS NULL OR GET_COPY_DATE = ' '`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:179`) 與 `NVL(GET_COPY_DATE, ' ') = ' '`(`Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:87`)。寫入端回復到件時塞的是一個空白字元而不是 NULL(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:93-94`), 所以這一欄實務上是「空白字元」,新寫查詢只寫 `IS NULL` 會撈不到。

3. **`REDEM_PROC_CODE` 沒有常數類別,三處各自寫死 `'3'`**,其中兩處還寫成 `<> '3'` —— 這一欄如果為 NULL,Oracle 三值邏輯會讓那兩處靜默過濾掉資料(附錄 E-2)。

## 3. 畫面清冊

### 3.1 維護 M(24 支,本片全部)

六層路徑一律是這個形狀,下表不再重複:

```
Dev/ATLAS.OFD/Source/UI/UI.OFD/<代號>.cs
Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/<代號>_Pxy.cs
Dev/ATLAS.OFD/Source/Control/Control.OFD/<代號>_Ctl.cs
Dev/ATLAS.OFD/Source/PO/PO.OFD/<代號>_PO.cs
Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/<代號>Model.xsd
Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD8/<代號>View.xsd
```

| 代號 | 中文名(推測) | 六層齊不齊 | 主表 | 明細 | PO 基底 | UI 基底 |
|---|---|---|---|---|---|---|
| `OFDM091` | 基金遞延手續費(CDSC)費率維護 | 齊 | `OFD091A` | `OFD092A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM220` | 銷售機構申購彙總維護 | 齊 | `OFD232A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM221A` | 境內基金申購交易維護 | 齊 | `OFD220A` | 7 張 | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM231A` | 境內基金買回／轉換交易維護 | 齊 | `OFD251A` | 10 張 | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM232` | 銷售機構買回彙總維護 | 齊 | `OFD259A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM233` | 短線交易費率維護 | 齊 | `OFD260A` | `OFD261A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM242` | 投資組合(契約)贖回維護 | 齊 | `OFD251A` `OFD252A` `OFD254A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM243A` | 券商配單維護 | 齊 | `OFD243A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM264` | 付款媒體檔格式設定 | 齊 | `OFD264A` | `OFD265A` `OFD266A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM270` | 退郵戶維護 | 齊 | `OFD270A` | — | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM271` | 缺件到件／回復登錄 | 齊 | `OFD724`(名義) | — | `BaseEVADaoPO` | **`xOneStepProcessForm`** |
| `OFDM281` | 基金收益分配(配息)設定 | 齊 | `OFD281A` | `OFD287A` `OFD288A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM284` | 受益人收益分配支付方式維護 | 齊 | `OFD286A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM285` | 基金匯費設定維護 | 齊 | `OFD290A` | — | **`MultiRowEVAPO`** | `xMaintainForm` |
| `OFDM286` | 受益人配息期間／類別維護 | 齊 | `OFD291` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM297` | 臨時放假淨值日期變更 | 齊 | `OFD297A` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM300` | 幣別匯率維護 | 齊 | `OFD300` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM301` | 交叉匯率維護 | 齊 | `OFD301` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM302` | 基金淨值維護 | 齊 | `OFD302A` | — | `BaseMultiRowEVADaoPO` | `xMaintainForm` |
| `OFDM321` | 基金銷售額度控管維護 | 齊 | `OFD321` | `OFD322` | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM331` | 客訴案件維護 | 齊 | `OFD331` | `OFD332` `OFD333` `OFD334` `OFD335` | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM337` | 交易退件維護 | 齊 | `OFD337A` | `OFD346A` | `BaseEVADaoPO` | `xMaintainForm` |
| `OFDM344` | 客戶資料保密設定異動 | 齊 | `OFD344` | — | **`BasicEVAPO`** | `xMaintainForm` |
| `OFDM361` | (未完成的潛在客戶維護空殼) | 齊(檔在,內容空) | 未宣告 | — | **`BasicEVAPO`**(空類別) | `xMaintainForm` |

中文名全部是**推測**,依據是主檔欄位的 `msdata:Caption` 與程式內註解。只有兩支有程式內的明確中文:`OFDM221A`(「境內基金申購交易維護作業」,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:38`) 與 `OFDM302`(「基金淨值維護作業」,`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM302_Ctl.cs:15`)。

### 3.2 查詢 I

**本片無 I 畫面。**原因見 §5 —— OFD 的查詢畫面集中在 `ATLAS.OFD.Query` 與 `ATLAS.OFDI` 兩個專案, 不在 `DataEntity.OFD8` 這一片的 entity 分卷裡。

### 3.3 批次 B

**本片無 B 畫面,也沒有任何 WindowsService。**原因見 §6 —— OFD 的批次全部落在 `ATLAS.OFDB`(`OFDB3xx` 結帳過帳)與 `ATLAS.EC`(`OFDB6xx` 服務型),entity 也在別的分卷。

### 3.4 報表 R

**本片無 R 畫面,也沒有任何 `.rpt`。**原因見 §7 —— 報表依鐵律住在 `ATLAS.OFD.Report`(`architecture.md §6`), 是另一個專案,不會出現在 `DataEntity.OFD8`。

### 3.5 一眼看出差別的六件事

1. **PO 基底分成四代並存。** 12 支新世代單筆(`BaseEVADaoPO`)、5 支新世代多筆(`BaseMultiRowEVADaoPO`)、 3 支舊世代多筆(`MultiRowEVAPO`)、4 支舊世代單筆(`BasicEVAPO`,含空殼 `OFDM361`)。 **舊世代那 7 支的連線欄位從來沒有被賦值**(§0.2、附錄 E-1)。

2. **只有 `OFDM271` 不是 `xMaintainForm`。** 它繼承 `xOneStepProcessForm` (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28`),也就是 B / I 型畫面用的基底 —— 一個查詢頁 + 一顆執行鈕,沒有四眼送審流程。代號是 `M` 但行為是 B(§4.8)。

3. **`OFDM221A` 與 `OFDM231A` 加起來佔了本片 40% 的程式量。** UI 3,137 + 5,659 行、PO 2,769 + 4,006 行,其餘 22 支全部加起來才 8,000 行上下。

4. **沒有任何一支用 Stored Procedure 做主要取數。** 全片只出現三個 DB 物件名: `S_TA_OFDM221A_Get`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2410`,取四條規則文字)、 `S_TA_UPD_REDEM_SHORT_RMK`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2463`,更新短線註記)、 `f_TA_GetEmpLockUnitsOnTheDay`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:200`,員工閉鎖單位數)。三個都在版控外,repo 內看不到內容。**其餘全部是 PO 內手寫 SQL。**

5. **查詢條件全部走同一段字串串接樣板。** 十幾支 PO 都有這樣一段: `strSQL += " And OFD243A." + Row.Name + " = " + "'" + Row.Value + "'";` (例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:168`)。 **欄位名與值都來自用戶端**,沒有綁參數(附錄 E-5)。

6. **四支的 SQL 還是 SQL Server 方言。** `OFDM284` `OFDM321` `OFDM331` `OFDM344` 的 live 程式碼用方括號識別字 `[OFD321]` / `[BMS001]`,`OFDM242` 更是整段 T-SQL 批次。Oracle 不吃(附錄 E-1)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFD8 其餘二十二支畫面依 PO 基底世代與行為分成四群
圖中文字:A 群:新世代單筆 BaseEVADaoPO(12 支,可正常運作) / OFDM091 OFDM233 / 費率主明細 兩支同形 / OFDM220 OFDM232 / 彙總 成對只改一邊 / OFDM243A OFDM264 / 配單 / 媒體檔格式 / OFDM270 OFDM281 OFDM337 / 退郵 / 配息 / 退件 / B 群:新世代多筆 BaseMultiRowEVADaoPO(5 支) / OFDM300 OFDM301 / 匯率成對 一支用double / OFDM302 / 淨值 鎖定才擋刪 / OFDM286 / 配息期間 唯一性檢核兩份 / OFDM297 / 臨時放假 逐列回報 / C 群:舊世代 MultiRowEVAPO / BasicEVAPO(7 支,推測跑不動) / OFDM242 OFDM284 OFDM285 / MultiRowEVAPO / OFDM321 OFDM331 OFDM344 / BasicEVAPO / dbTA 從未被賦值 / 建構子整段註解 / SQL 還是 T-SQL / 方括號 / DECLARE @x / D 群:兩支不照規矩的畫面 / OFDM271 / 代號M 行為B 主檔是假的 / OFDM361 / 三層空類別 從未接上DB / xOneStepProcessForm / 271 不是 xMaintainForm / Designer 653行 / 361 的畫面其實畫完了 / 共同形狀:卡控條數與資料重要性不成比例 / OFDM300 / OFDM301 / 全庫金額基礎 各1~2條 / OFDM264 / 媒體檔格式 二十餘條 / OFDM344 / 完全沒有業務檢核 / OFDM243A / 只有一條 金額不得為0
```

*圖:圖 4 其餘畫面分群。白框=可正常運作;橘虛框=有風險、不對稱或推測跑不動;黑框=框架層或方言殘留;灰虛框=存在但沒被接上。C 群那七支的 UI 檢核是活的、PO 是死的——使用者會走到按下存檔那一刻才失敗。*

```text
[圖] OFDM221A 與 OFDM231A 的四層卡控,以及已結帳買回書的靜默失敗路徑
圖中文字:① 用戶端 UI:兩大支的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / 221A 約480行 20條 / Chk*() 八支 / 額度/KYC/關帳/關係人 / ByPassAddMessage / 詢問過了就記錄不擋 / ② 伺服端 PO 的 Check* 方法:是 UI 主動叫的 RPC,不是掛點 / 221A 十二支 Check* / 戶號/帳號/關帳/活動 / 231A 十一支 Check* / 憑證/短線/CDSC/單位數 / 繞過 UI = 零卡控 / 批次直接叫 Ctl 就過 / S_TA_OFDM221A_Get / 版控外 只取規則文字 / ③ EVA 掛點:這一片拿來寫副作用,不拿來擋 / BeforeAdd / 取書號 無重試上限 / AfterAdd / AfterUpdate / 寫 OFD303A CTL012 CTL022 / BeforeSave 822行 / 231A 回寫 OFD221A 單位數 / AfterApproveDelete / 唯一會回沖的掛點 / ④ 四眼引擎:驗證與覆核在這一片只留軌跡 / 輸入 → 帳已經動了 / AfterAdd 已寫控制檔 / 驗證 AfterVerify / 只寫跳號一覽表 / 覆核 AfterApprove / 只寫跳號一覽表 / 15 處 throw 空訊息 / 使用者看到空白錯誤 / ⑤ 靜默失敗的一條路:已結帳的買回書 / REDEM_PROC_CODE=3 / 寫死字面量 無常數 / BeforeUpdate 抽掉明細 / DetailTable.Clear() / 只剩 OFD272A 被寫 / 付款/轉換改動不見 / 畫面仍回「成功」 / 過濾(無提示)
```

*圖:圖 3 兩大支的四眼與卡控順序。橘框=真的會擋或真的會寫資料的關卡;橘虛框=風險、寫死值或靜默失敗;黑框=版控外。最重要的一件事在第 ④ 排:驗證與覆核的 handler 主體只有一行跳號紀錄,帳在輸入當下就動了。*

**讀法**:§4.1 §4.2 是兩大支,§4.3 是它們的分工(本篇最有價值的一節), §4.4–§4.12 是其餘值得單獨寫的九支,§4.13 是剩下 12 支的表格群組。每節末的卡控總表,結果類型一律五類:**阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋**。

「記錄不擋」在本片有個具體實作:`ByPassAddMessage(訊息, ProcessVDB, 畫面名, true)` —— 使用者在確認框按了「是」之後,把原本的警告字串當作 bypass 理由塞進 VDB 一併送出,四眼覆核者看得到。 `OFDM221A` 與 `OFDM337` 都大量使用這一招。

### 4.1 `OFDM221A` 境內基金申購交易維護

用途(推測):**建立一張境內基金申購書**,連同它的支票、匯款、券商配單、缺件、代理人資料一次送四眼。是本片的第一大支,也是 `OFD220A` 的主檔持有者(§8.1)。

#### 4.1.1 結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseEVADaoPO, IOFDM221_PO`(介面名少一個 `A`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:25`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:55` |
| 主檔 | `OFD220A` → vdb `OFDM221A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:67` |
| 明細(7) | `OFD221A` 申購明細、`OFD272A` 缺件、`OFD234A` 支票、`OFD235A` 匯款、`OFD243A` 券商配單、`OFD220A_AGENT` 意定代理人、`OFD136A` 交易指示代理人 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:68-76` |
| EVA 掛點 | `BeforeSelect` `BeforeGetMaintainData` `BeforeGetToDoData` `BeforeAdd` `BeforeUpdate` `AfterAdd` `AfterUpdate` + 8 個跳號用 After | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:60-87` |
| 伺服端檢核方法 | 12 支公開 `Check*` / `Get*`,由 UI 主動呼叫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-2646` |

明細的取數走一個**不尋常的寫法**:`BeforeGetMaintainData` 只在 `DetailTable[0]`(也就是 `OFD221A`) 那一次進來時組一段 **`;` 串起來的多段 SQL**,一次 `LoadDataSet` 灌 7 張表,然後 `args.Cancel = true` 讓框架不要再各跑一次(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:127-136`)。 **後果**:7 張明細的載入順序與欄位對應由 `LoadDataSet` 的參數順序決定,加一張明細一定要同時改三處 (`DetailTable.Add`、`BuildDetailSQLString` 的 `case`、`LoadDataSet` 的表名清單)。

#### 4.1.2 必填與存檔前檢核

UI 的 `DoValidate(bool isFinalCheck)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:652`)是主戰場,約 480 行。主要條目:

| 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 受益人戶號存在且可交易 | 依 `Check_NO` 回傳 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:730-733` |
| 明細申購日期 ≥ 收件日期 | 明細資料的 申購日期 不可小於 收件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:753` |
| 有通路區分碼就必須有通路代碼 | 有挑選 通路區分碼 時,通路代碼 必須輸入! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:787` |
| 收件日期須為公司營業日 | 收件日期 不為公司營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:819` |
| 付款方式為代扣款 → 扣款行 / 扣款帳號必填 | 付款方式為 代扣款,扣款行 必須輸入! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:827-829` |
| 扣款方式 / 匯款類別必填 | 扣款方式 為必填欄位 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:831-839` |
| 至少一筆明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:846` |
| 基金該申購日是否禁止交易 | 申購日 yyyy/MM/dd + 限制說明 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:880`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:913` |
| 匯款比對已關帳 | 基金 X 滙款比對已關帳,不可再執行「要匯款比對」之資料建檔! | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:953` |
| 傳真委扣同意書 / 扣款帳號有效性 | 申購日期 [X] 無有效傳真委扣同意書資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1011-1016` |
| 交易方式不可為線上交易 | 交易方式不可為線上交易 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1028` |
| KYC 風險屬性不符 | 依 `ChkKYC_RISK_ATTR` | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1079-1096` |
| 不得主動推薦高風險基金 | 此受益人「不得主動推薦高風險基金」 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1132` |
| 櫃台關帳 | 依 `ChkKeyIN_ALLOT_CLS` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1144-1212` |
| 關係人交易 | 依 `ChkIsRelTrade` | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1234-1264` |
| OBU 檢核 | 依 `ChkIsOBU` | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1265-1277` |
| 身分證 / 統編格式 | 依 `ChkID_NO` | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1278-1298` |
| **基金銷售額度** | 基金[X]申購金額 已超過基金銷售額度,是否繼續? | **詢問 → 記錄不擋** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1299-1335` |
| 一般申購只能一筆明細 | 申購只可輸入一筆基金明細資料。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2171` |
| 註銷戶不可交易 | 此 受益人 為註銷戶不可執行交易 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2483` |

`ChkFundQuota` 這一條要特別記:它是 `OFDM321`(基金銷售額度控管)唯一的下游消費者, 透過 `m_nfdBiz.IsOverFundQuota(...)` 比對(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1314`)。超額只是**詢問**,按「是」就用 `ByPassAddMessage` 記錄後照樣送出 —— **額度不是硬上限**。

#### 4.1.3 刪除卡控(五條,全在 UI)

刪除按鈕與 grid 刪列各有一套幾乎相同的檢核,兩邊各五條:

| 條件 | 訊息 | 結果 | 按鈕層錨點 | 列層錨點 |
|---|---|---|---|---|
| TDCC 指託來源 | 此為 TDCC 指託平台下單資料,不可刪除。請執行基金集保指託下單資料刪除作業(OFDB757) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2022-2029` | — |
| 有比對流水號 | 已有比對流水號資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2044` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2084` |
| 傳真委扣交易截止 | 已有資料做傳真委扣交易截止設定,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2050` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2090` |
| 已作廢 | 已有作廢資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2056` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2096` |
| 已結轉 | 已結轉資料,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2062` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2102` |
| 已匯款比對 | 明細資料已執行過匯款比對,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2069` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2109` |

**兩邊的判斷方式不一樣**:按鈕層用 `DataTable.Select("COMPARE_NO<>''")` 字串運算式, 列層用 `row.COMPARE_NO != ""` 直接比欄位值。前者對 `DBNull` 會判 false(過濾掉),後者對 `DBNull` 會丟例外。同一條規則兩種寫法,是附錄 E-3 的一例。

#### 4.1.4 四眼各階段附加動作

| 掛點 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd`(主檔) | 取申購書號 `GetAllotNoForNfd()`,撞號重取;逐筆明細算優惠身份別 `FAVORED_REL_TYPE`;接著 `BeforeSave` / `AddOFD130A` / `GetUnitCode` / `GetDataCenter` / `RealSubDate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:157-203` |
| `BeforeUpdate`(主檔) | 同上五支,但**不取號** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:211-223` |
| `AfterAdd`(明細 `OFD221A`) | 逐筆更新 `OFD303A` / `CTL012` / `CTL022`(`EnumAction.Add`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:286-303` |
| `AfterUpdate`(明細 `OFD221A`) | 依 Added / Modified / Deleted 三批分別更新同三張控制檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:231-284` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterResend` / `AfterReject` | **只寫跳號一覽表**(`SrNoCommentProcessor.AddCommentHistory`),零業務 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2678-2741` |
| `AfterApproveDelete` | 跳號紀錄 + `ChkCTL_FILE`:重讀明細後把 `OFD303A` / `CTL012` / `CTL022` 全部以 `EnumAction.Delete` 回沖 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2719-2726`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2743-2767` |

**結論:驗證與覆核不改任何業務資料。**帳上的控制碼在「新增 / 修改」當下就動了, 只有「覆核刪除」才回沖。這對排查「為什麼還沒覆核帳就變了」是關鍵。

#### 4.1.5 跨表更新

| 表 | 動作 | 時機 | 錨點 |
|---|---|---|---|
| `OFD303A` | UPDATE 申購控制碼,不存在則 INSERT | `AfterAdd` / `AfterUpdate` / `AfterApproveDelete` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1012-1377` |
| `CTL012` | 代扣款控制檔 UPDATE / INSERT / DELETE | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1378-1579` |
| `CTL022` | 櫃台控制檔 UPDATE / INSERT / DELETE | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1580-1759` |
| `OFD130A` | 匯款授權書:沒有就新增一筆 | `BeforeAdd` / `BeforeUpdate` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:365-450` |

#### 4.1.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前(UI) | `ChkID_NO` 統編格式 | 詢問是否忽略 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1920-1923` |
| 新增前(UI) | `DoValidate(true)` 全部欄位與業務檢核 | 列出錯誤清單 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1927-1941` |
| 新增前(UI) | `ChkFundQuota` 銷售額度 | 詢問是否繼續 | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1943-1947` |
| 新增前(UI) | `CheckEmpNo` 業務員銷售機構不符 | 此員工代碼無相對應之銷售機構 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1949`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2635` |
| 修改前(UI) | 同新增,另加來源碼檢核 |  | 阻擋 / 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1963-2008` |
| 刪除前(UI) | 五條狀態檢核 | 見 §4.1.3 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2009-2077` |
| 查詢前(UI) | 四個條件擇一 | 申購書號, 收件日期, 客戶統編, 戶號 必須擇一填寫 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1861` |
| 伺服端(PO) | `CheckSameAllotData` 同日同基金重複申購 | 由 UI 決定呈現 | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1849-1925` |
| 伺服端(PO) | `Check_NO` 戶號 / 統編 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:1926-2028` |
| 伺服端(PO) | `Check_Remit_Compare` 匯款比對關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2029-2082` |
| 伺服端(PO) | `CheckACC_NO` 扣款帳號有效性 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2083-2163` |
| 伺服端(PO) | `CheckCampignCodeData` 行銷活動代碼 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2164-2304` |
| 伺服端(PO) | `CheckBF_NO_StopAllot` 受益人停止申購 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2475-2530` |
| 伺服端(PO) | `CheckALLOT_CLS` 櫃台關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2531-2592` |
| 伺服端(PO) | `CheckSubAcct` CDSC 子帳戶 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2593-2646` |
| 存檔時(PO) | 申購書號撞號 | 重新取號,無次數上限 | 記錄不擋(有無窮迴圈風險) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:172-177` |

**沒有任何一條卡控落在 `BeforeAdd` / `BeforeUpdate` 裡做否決。** 所有 PO 端檢核都是 UI 主動呼叫的 RPC。繞過 UI(例如另寫一支批次直接叫 `_Ctl`)= 零卡控。

### 4.2 `OFDM231A` 境內基金買回／轉換交易維護

用途(推測):**建立一張境內基金買回書**,涵蓋三種形態 —— 純買回(付款)、轉換(轉申購)、實體憑證買回; 並把要沖銷的原申購書逐筆挑出來。本片第二大支,也是全片最複雜的一支。

#### 4.2.1 結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseEVADaoPO, IOFDM231A_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:65` |
| 主檔 | `OFD251A` → vdb `OFDM231A_Master`(93 欄) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:70` |
| 明細(10) | `OFD252A` 付款、`OFD253A` 轉換、`OFD272A` 缺件、`OFD254A` 指定沖銷、`OFD258A` 憑證、`OFD220A` 申購主檔、`OFD251A_AGENT`、`OFD221A` 申購明細、`OFD243A` 券商配單、`OFD136A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:71-82` |
| 解構子 | **逐一 `-=` 解除 14 個事件**(全片唯一這樣做的) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:106-123` |
| 伺服端檢核方法 | 11 支 `Check*` / `Get*` + 12 支非泛型工具方法 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:34-59` |

#### 4.2.2 三種形態,三條明細線

| 形態 | 使用者填什麼 | 寫哪些表 |
|---|---|---|
| 純買回 | 買回單位數 / 金額 + 付款明細 | `OFD251A` + `OFD252A` + `OFD254A`(沖銷) |
| 轉換(轉申購) | 轉入基金 / 轉入日期 / 轉換費率 | `OFD251A` + `OFD253A` + `OFD254A` + **新開 `OFD220A` / `OFD221A`** |
| 實體憑證買回 | 憑證期別 + 憑證號碼 | `OFD251A` + `OFD258A` + UPDATE `OFD721` |

**第二列是這一支最容易被忽略的事**:轉換會在同一次送審裡**產生一張全新的申購書**(§4.3)。

#### 4.2.3 必填與存檔前檢核(UI)

| 檢核 | 訊息 / 行為 | 結果類型 | 錨點 |
|---|---|---|---|
| 受控管基金 | 伺服端回傳訊息,首字 `1` 警示 / `2` 錯誤 | 警示 或 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:974-990`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:186-190` |
| 缺件尚未到齊 | grid 內 `GET_COPY_UID<>''` 判斷 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` |
| 匯費 / 郵費試算 | 取回後才填 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:4692`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:4723` |
| 帳號 / 憑證 / 受益人 / 短線費 | 走 PO 的 `CheckACC_NO` `CheckCER_R_ID` `CheckBF_NO` `IsShortFee` | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:36-50` |

#### 4.2.4 四眼各階段附加動作

| 掛點 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd`(主檔) | 取買回書號 `GetRdmNoForNfd()`,撞號重取;`UpateOFD313`(叫 SP 更新短線註記)、`AddOFD130A`、`UpdateCTL022` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3492-3510` |
| `BeforeAdd`(明細 `OFD252A`) | `BeforeSave` —— 這一支真正做事的地方(下表)+ `BeforSaveOFD272` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3511-3516` |
| `BeforeUpdate`(主檔) | **若 `REDEM_PROC_CODE == "3"`(已結帳)就把 `DetailTable` 清空、只留 `OFD272A`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3519-3547` |
| `AfterUpdate`(明細 `OFD221A`) | 跑完最後一張明細後,對被刪除的轉換列回沖 `OFD303A`(`Del303aAllot`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3548-3558` |
| `AfterApproveDelete` | 整張買回書的反向處理(約 300 行) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3640-3949` |
| `AfterDelete` | 跳號紀錄:主檔一筆 + **每一張轉換產生的申購書各一筆** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3953-3966` |
| `AfterVerify` / `AfterApprove` / `AfterReject` / `AfterResend` / `AfterUnDelete` | **只寫跳號一覽表,零業務 SQL** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3968-4003` |

`BeforeSave`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1563-2385`,822 行)是本片最長的方法,做八件事:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | UPDATE / INSERT `OFD303A` 贖轉控制碼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1576-1632` |
| 2 | UPDATE `OFD304A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1633-1678` |
| 3 | 以 `OFD252A` 每筆 INSERT 匯款授權 `BMS004A` / `BMS005A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1679-1832` |
| 4 | **以 `OFD253A` 每筆新增 / 刪除 `OFD220A` + `OFD221A`(轉申購)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1833-2115` |
| 5 | 同步券商配單 `OFD243A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2116-2181` |
| 6 | **以 `OFD254A` 每筆 UPDATE `OFD221A` 的 `RDMING_UNIT`(贖回中單位數)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2200-2236` |
| 7 | 以 `OFD258A` 每筆 UPDATE `OFD721`(實體憑證餘額)與相關 `OFD258A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2238-2385` |
| 8 | 缺件 `OFD272A` 補書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2445-2457` |

第 6 步的算式值得抄下來,因為它是「重算而非累加」:

```
SET RDMING_UNIT = R_UNIT - FREEZE_UNIT + :RDMING_UNIT
    參數 :RDMING_UNIT = (變更後 REDEM_UNIT) - CAN_REDEM_UNIT
```

程式註解把推導寫在 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2201-2205`: 先扣掉變更前的 `REDEM_UNIT` 再加回變更後的,避免重複累加。影響筆數不是 1 就 `throw new ApplicationException("更新境內基金申購明細檔失敗,請檢查")` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2227-2228`)—— 這是本片少數**有訊息**的 throw。

#### 4.2.5 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| UI | 受控管基金 | 首字 `1` 警示 / `2` 阻擋 | 警示 / 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:974-990` |
| UI | 仍有缺件 | 不可贖回 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` |
| PO | `CheckREDEM_CLS` 買回關帳 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:40` |
| PO | `CheckRedemAll` 全部買回 |  | 詢問 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:42` |
| PO | `IsRedemDataExist` 同日同基金重複買回 |  | 警示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:49` |
| PO | `IsShortFee` / `IsNonShortFee` 短線交易費 | 依 `OFDM233` 設定 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:50-52` |
| PO | `CHK_UNIT_CHG` 單位數異動 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:55` |
| PO | `CheckCdscSwitch` CDSC 基金轉申購限制 |  | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:59` |
| PO | `GetRemainRedemUnits` 可買回單位數 | 不足則算式為負 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:54` |
| PO 存檔 | `REDEM_PROC_CODE = '3'`(已結帳) | **只允許改缺件,其餘明細靜默不寫** | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522-3529` |
| PO 存檔 | `OFD221A` 更新筆數 ≠ 1 | 更新境內基金申購明細檔失敗,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2227-2228` |
| PO 存檔 | `OFD721` 更新筆數 ≠ 1 | 更新境內基金買回受益憑證檔失敗,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3939-3940` |

**「已結帳就只更新缺件」這一條要特別小心**:它不是提示、不是阻擋,是**把明細清單抽掉**。使用者在畫面上改了付款明細按存檔,系統回「成功」,但那些改動根本沒送進 SQL。這是本片最典型的「過濾(無提示)」。

### 4.3 `OFDM221A` 與 `OFDM231A` 到底怎麼分工

這一節回答三個問題:**它們是不是一對?共用的五張表各自在做什麼?改一邊會不會影響另一邊?**

#### 4.3.1 是一對,但不是對稱的一對

| 面向 | `OFDM221A` | `OFDM231A` |
|---|---|---|
| 交易方向 | 申購(錢進來、單位數出去) | 買回 / 轉換(單位數回來、錢出去) |
| 主檔 | `OFD220A` 申購書(PK `ALLOT_NO`) | `OFD251A` 買回書(PK `REDEM_NO`) |
| 取號 | `SerialNo.GetAllotNoForNfd()` | `SerialNo.GetRdmNoForNfd()` |
| 明細張數 | 7 | 10 |
| 缺件種類 `TRN_CD` | `'2'` 申購(`TRN_CD.Allot`) | `'3'` 贖回轉換(**寫死 `'3'`,沒用常數**) |
| 會不會建對方的主檔 | **不會** | **會** —— 轉換時建 `OFD220A` / `OFD221A` |
| 程式規模 | UI 3,137 / PO 2,769 | UI 5,659 / PO 4,006 |

**不對稱的關鍵在最後兩列。**`OFDM231A` 的轉換(switch)在業務上等於「贖一檔、買另一檔」, 所以它必須在同一筆交易裡替轉入基金開一張申購書。`OFDM221A` 沒有反向需求。

#### 4.3.2 五張共用表各自的角色

| 表 | 在 `OFDM221A` | 在 `OFDM231A` | 誰是寫入者 |
|---|---|---|---|
| `OFD220A` | **主檔**,INSERT / UPDATE / DELETE | 明細 vdb `OFDM231A_Allot`,**轉換時 INSERT、取消轉換時 DELETE** | 兩支都寫 |
| `OFD221A` | 明細 vdb `OFDM221A_Detail`,INSERT / UPDATE / DELETE | 明細 vdb `OFDM231A_AllotDetail`,轉換時 INSERT;另外**用手寫 SQL UPDATE `RDMING_UNIT`** | 兩支都寫 |
| `OFD243A` | 明細 vdb `OFD243`,跟著申購書走 | 明細 vdb `OFD243`,跟著轉申購走 | 兩支都寫(主檔畫面是 `OFDM243A`) |
| `OFD272A` | 明細 vdb `OFD272`,`TRN_CD='2'`、`SHORE_ID='2'` | 明細 vdb `OFD272`,`TRN_CD='3'` | 兩支都寫(另有四支外部畫面,§8.2) |
| `OFD136A` | 明細 vdb `OFD136A`,`TRADE_NO` = 申購書號 | 明細 vdb `OFD136A`,`TRADE_NO` = 買回書號 | 兩支都寫,靠 `TRADE_TYPE` 分流 |

三個實務上的後果:

1. **`OFD220A` / `OFD221A` 有兩個建檔入口(本片內)加兩個外部入口(BBS)。** 本片:`OFDM221A` 正常開單、`OFDM231A` 轉換開單。外部:`BBSM013` / `BBSM113` 轉讓過戶開單(§8.1)。 **任何「申購書一定從 `OFDM221A` 來」的假設都是錯的。**

2. **`OFD221A` 的 `RDMING_UNIT` 只有 `OFDM231A` 會寫,而且是繞過四眼引擎的手寫 UPDATE。** `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2207-2236` 不更新 `UPDATEID`(程式註解明講「不更新 UpdateID」)。所以看到 `OFD221A` 的單位數變了但 `UPDATEID` 沒變,不是資料異常,是設計。

3. **`OFD272A` 的 `TRN_NO` 是「多型外鍵」。** 同一欄在 `TRN_CD='2'` 時放 `ALLOT_NO`、`TRN_CD='3'` 時放 `REDEM_NO`、 `TRN_CD='1'/'5'` 時放 BMS 的異動書號。**沒有 FK,只能靠 `TRN_CD` 判斷要 join 哪張表。**

#### 4.3.3 轉換是怎麼變成一張申購書的

`OFDM231A_PO.BeforeSave` 的第 4 步(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1833-2115`):

| 情境 | 做什麼 | 錨點 |
|---|---|---|
| 轉換列被**刪除** | 找出對應的 `OFDM231A_Allot` 列 → 寫一筆 `EVAType.Modify` 跳號紀錄 → `row220.Delete()` → 連帶刪掉該申購書的券商配單 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1834-1852` |
| 轉換列是**新增** | `NewOFDM231A_AllotRow()` + **逐欄手寫 156 個指派**填出 `OFD220A` 與 `OFD221A` 兩筆,然後 `AddOFDM231A_AllotDetailRow` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1931-2106` |
| 轉換列是**修改** | **只同步一個欄位** `FAVORED_REL_TYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2110-2112` |

**最後一列是本片最會咬人的缺陷。**新增走 156 個指派、修改只走 1 個。使用者若在同一張買回書上把轉換的金額、日期、通路、業務員改掉, `OFD253A`(轉換明細)會更新,但它的影子 `OFD221A`(申購明細)**除了優惠身份別以外全部維持舊值**。而且 `FindByALLOT_NOALLOT_SRNO(row1.ALLOT_NO, 1)` 把 `ALLOT_SRNO` 寫死成 `1`、回傳值沒有 null 檢查 —— 找不到就 `NullReferenceException`(附錄 E-4)。

#### 4.3.4 改一邊會不會影響另一邊

| 你要改什麼 | 一定要一起看的地方 |
|---|---|
| `OFD220A` / `OFD221A` 加欄位 | `OFDM221A` 的 Model + View xsd、`OFDM231A` 的 Model + View xsd(vdb 名不同)、`OFDM243A` 的 xsd(7 欄縮減版)、BBS 兩支的 xsd、EC 的 `OFDB672` / `OFDB673` xsd;再加 `OFDM231A_PO` 那 156 行手寫指派 |
| `OFD272A` 加欄位 | 本片 2 支 + BMS 2 支 + RSP 2 支的 xsd,共 6 份;還有 `OFDM271` 的 `OFDM271` vdb |
| 缺件邏輯 | `OFDM221A`(`TRN_CD.Allot`)、`OFDM231A`(寫死 `'3'`)、`OFDM271`(到件登錄)、`Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130`(交易限制判斷) |
| 申購書取號 | `OFDM221A`(`SrNo.AllotNoForNfd`)與 `OFDM231A`(`SrNo.AllotNoForNfdS`,**S 結尾是另一組號**) |

最後一列值得單獨記:轉換產生的申購書用的是 **`SrNo.AllotNoForNfdS`** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1843`),與正常申購的 `SrNo.AllotNoForNfd` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2683`)**不是同一組流水號**。從書號就看得出來這張申購書是不是轉換來的 —— 但程式裡沒有任何地方把這件事寫成文件。

### 4.4 `OFDM264` 付款媒體檔格式設定

用途(推測):定義**某家付款銀行的某一種媒體檔**長什麼樣 —— 檔名怎麼編、每一欄放什麼、長度對齊補位小數位數怎麼設。它是產檔程式的設定來源,自己不產檔。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD264A`(`PAY_BANK` + `FILE_FORMAT` + `FILE_ID`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:35` |
| 明細 1 | `OFD266A` 檔名編立規則(vdb `OFDM264_FileRule`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:36` |
| 明細 2 | `OFD265A` 欄位定義(vdb `OFDM264_Field`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:37` |
| EVA 掛點 | **只有 `BeforeSelect` 與 `BeforeGetMaintainData`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:32-33` |

**這一支沒有任何 `Before*Add` / `After*` 掛點** —— 存檔完全交給四眼引擎的通用 INSERT / UPDATE, 沒有跨表副作用。卡控 100% 在 UI。

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 資料格式為明細(`FILE_FORMAT='2'`)時,檔名規則必填 | 資料格式為明細時,檔名規則必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:232` |
| 存檔前 | 檔名規則至少一筆 | 自訂檔名編立方式:請至少輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:237` |
| 存檔前 | 每筆序號 / 資料形式 / 基準日期 / 資料內容必填 | 自訂檔名編立方式:第 N 筆的… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:245-276` |
| 存檔前 | 固定檔名時資料形式不得為年編 / 批號 | 因檔名規則為固定檔名,第 N 筆的資料形式不得為… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:261` |
| 存檔前 | 批號只能一筆 | 批號的資料形式只能有一筆 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:283` |
| 存檔前 | 檔名內容長度 ≤ 10(中文算 2) | …資料內容長度必須 <=10 (一個中文字的長度為2) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:306` |
| 存檔前 | 下載格式至少一筆 | 下載格式設定資料:請至少輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:316` |
| 存檔前 | 每筆序號 / 欄位名稱 / 欄位型態 / 長度 / 對齊方式必填 | 下載格式設定資料:第 N 筆的… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:322-351` |
| 存檔前 | 非首筆 / 尾筆時欄位型態限制 | 資料格式不為首筆或尾筆,第 N 筆的欄位型態不可為… | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:338` |
| 存檔前 | 日期型欄位長度只能 6/7/8/10 | 第 N 筆的長度必須為 6,7,8,10 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:373` |
| 存檔前 | 小數位數 ≥ 0、小數補位字元必填 | 第 N 筆的小數位數必須大於等於零 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:384-390` |

**兩個被註解掉的檢核**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:288`(檔名資料內容必填) 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:356`(補位字元必填)外殼還在,實際不檢核。

**一個結構上的怪處**:`OFDM264_Ctl` 自己定義了一支私有的 `ExecPOActionToViewVDB` (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM264_Ctl.cs:284`),而不是用 `BaseController` 的版本 —— 全片只有這一支這樣做。改 Control 基底時不會改到它。

### 4.5 `OFDM281` 基金收益分配(配息)設定

用途(推測):設定某檔基金某年度某期別的**配息參數** —— 分配基準日、權值扣除日、發放日、再投資日、配息基準單位數、總分配權值、匯費郵費收取方式、再投資手續費率; 外加兩張明細:配息來源別(`OFD287A`)與各扣繳類別的可扣抵稅率(`OFD288A`)。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD281A`(`FUND_ID` + `YEARS` + `ISSUE_CODE`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:43` |
| 明細 | `OFD287A` 配息來源、`OFD288A` 扣抵稅率 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:48-49` |
| 唯讀結果集 | `OFDM281_Before`(上一期參數,帶預設值用)、`OFDM281_RateBase`(受益人扣繳類別清單) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM281Model.xsd` |
| EVA 掛點 | 只有 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:44-46` |

#### 日期先後鏈(這一支最實質的卡控)

```
最後過戶日 ≤ 分配基準日 < 權值扣除日
                 分配基準日 < 發放日期 ≤ 再投資日期
```

| 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|
| 分配基準日 ≥ 最後過戶日期 | 分配基準日 必須大於等於 最後過戶日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:66` |
| 權值扣除日 > 分配基準日 | 權值扣除日 必須大於 分配基準日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:82` |
| 發放日期 > 分配基準日 | 發放日期 必須大於 分配基準日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:90` |
| 再申購日期 ≥ 發放日期 | 再申購日期 必須大於等於 發放日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:97` |
| 年度格式 | 年度 輸入格式錯誤 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:111` |
| 配息基準 > 0 | 配息基準 必須大於0 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:117` |
| 至少一筆配息來源明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:58` |
| `ValidateBASE_DATE` 伺服端複核 | 依回傳 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:105`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM281_Ctl.cs:827` |
| **作業處理碼 ≠ 0(已產生配息資料)時不得修改** | 已產生配息資料,不得修改 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399-403` |
| **作業處理碼 ≠ 0 時不得刪除** | 已產生配息資料,不得刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776-780` |

**最後兩列是一個「成對路徑只改一邊」的實例。**兩段做同一件事,寫法卻不同:

|  | 修改路徑 | 刪除路徑 |
|---|---|---|
| 取值 | `Int32.TryParse(this.ucomPROCESS_CODE.Value.ToString(), out r) && r != 0` | `Convert.ToInt32(this.ucomPROCESS_CODE.Value) != 0` |
| 值為空 / null 時 | `TryParse` 失敗 → 不擋,正常往下 | `Convert.ToInt32` 丟 `FormatException` / `InvalidCastException` |
| 錨點 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776` |

而且兩段上方都各留了一份**被註解掉的舊版檢核**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:389`、 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:767`),訊息是「作業處理碼 不為尚未處理時,不得修改／刪除」。修改路徑被硬化成 `TryParse`,刪除路徑沒跟上。

### 4.6 `OFDM331` 客訴案件維護

用途(推測):登錄一件客訴 —— 對象(受益人 / 潛在客戶 / 通路推薦人)、客訴代碼與內容、指定處理部門、處理說明與處理種類、確認時間。四張明細分成「客訴側」與「處理側」各兩張。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | **`BasicEVAPO`**(舊世代) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:22` |
| 主檔 | `OFD331`(PK `COMPLAIN_NO`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:32` |
| 明細 | `OFD332` 客訴代碼、`OFD333` 客訴內容、`OFD334` 處理說明、`OFD335` 處理種類代碼 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:34-37` |
| live / 註解比 | 全檔 808 行,其中 **391–805 行包在 `/* */` 裡**(舊的 `Add` / `Select` override) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:390-806` |

#### 依客訴對象種類分支的必填(UI)

| `COMPLAIN_TYPE` | 必填欄位 | 訊息 | 錨點 |
|---|---|---|---|
| 受益人 | `BF_NO` + `ID_NO` | 若'客訴對象'為'受益人',戶號為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:293`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:298` |
| 潛在客戶 | `PR_NO` | 若'客訴對象'為'潛在客戶',潛在客戶序號為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:305` |
| 通路推薦人 | `SPONSOR_CODE` + `CHANNEL_CD` + `CHANNEL_CODE` | 若'客訴對象'為'通路推薦人',推薦人代碼為必輸 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:312-322` |
| 任何 | 沒選指定處理部門就要填處理內容 | 若無選擇指定客訴處理部門,請輸入'客訴處理內容' | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM331.cs:287` |

全部是**阻擋**。

#### `BeforeAdd` 取客訴序號:四個問題疊在 60 行裡

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:98-157`:

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | 三個明細 row 建了卻沒加進 DataTable | `NewOFDM331_ComplainRow()` 等三個新 row 從頭到尾沒有 `Add*Row`,`COMPLAIN_NO` 設在孤兒物件上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:103-105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:135-140` |
| 2 | 條件寫成同一式 OR 兩次 | `if (row.COMPLAIN_NO != string.Empty \|\| row.COMPLAIN_NO != "")` —— 兩邊完全相同,等於只寫一次;看得出原意是 null 檢查 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:118` |
| 3 | 在 `Before*` 掛點裡 `args.DbTran.Rollback()` 後再 `throw` | 違反掛點規約(`architecture.md §3`);引擎外層還會再 rollback 一次 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:122-123` |
| 4 | `catch` 吞掉例外後**正常返回** | `HandleBusinessException(ex)` + `ptpfTX.Rollback()`,方法照樣 return,引擎會帶著空的 `COMPLAIN_NO` 繼續 INSERT | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:143-148` |
| 5 | 取號無次數上限 | `while (IsExistComplain_No(...)) { 重取 }` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:130-133` |

問題 1 值得展開。**被註解掉的舊版是對的**:它在取號前先判斷 `Rows.Count > 0`, 把 `row_D` 重新指向 `Rows[0]`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:459-474`), 而且處理四張明細(含 `OFDM331_Solve_K`)。live 版只剩三張、也不再重新指向。 **假設**:新客訴案件的明細 `COMPLAIN_NO` 會拿到 UI 送過來的空字串,與主檔對不上。依據是上述兩段的差異,以及 `OFDM331_Ctl` 的 view→model 搬移是逐表複製、不從主檔補鍵 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM331_Ctl.cs:205-215`)。這一條沒有現場驗證,但同一支畫面正確的寫法就在旁邊的 `OFDM337`(§4.7),可以對照。

### 4.7 `OFDM337` 交易退件維護

用途(推測):登錄一筆**退件**(文件不齊或不符而退回給客戶),含退件原因、退件項目(可複選)、退件地址、文件補齊日期。`OFD346A` 明細是勾選出來的退件項目清單。

| 項目 | 內容 | 錨點 |
|---|---|---|
| 主檔 | `OFD337A`(PK `REJ_NO`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:46` |
| 明細 | `OFD346A` 退件項目(PK `REJ_NO` + `REJ_ITEM`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:47` |
| 唯讀 | `OFD041` 範本內容(勾選帶入備註) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM337Model.xsd` |
| EVA 掛點 | `BeforeAdd` + 三個 Before 取數 + 8 個跳號 After | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:41-60` |

#### `BeforeAdd` 取號 —— 這一支做對了

```
if (row.REJ_NO == string.Empty)
    do {
        row.REJ_NO = genSrNo.GetRejNo();
        foreach (明細 row_dtl)
            if (row_dtl.RowState != DataRowState.Deleted)
                row_dtl.REJ_NO = row.REJ_NO;     // 真的寫回 DataTable 裡的列
    } while (IsExistByData(...));
```

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:111-131`。與 §4.6 的 `OFDM331` 對照: **同一個需求(主檔取號後把號碼灌進明細),`OFDM337` 走的是真正在 DataTable 裡的列,`OFDM331` 走的是孤兒列。** `OFDM337` 還多做兩件事:`REJ_NO` 已有值就不重取(支援由別的畫面帶入)、跳過已刪除的列。唯一相同的毛病是取號重試沒有次數上限。

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 至少勾選一筆退件項目 | 至少須勾選一筆退件項目 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:83` |
| 存檔前 | 退件日期不可空白 | 退件日期不可為空白 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:93` |
| 存檔前 | 客戶統編邏輯 | X 不符合正常邏輯,是否忽略? | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:44-64` |
| 存檔前 | 聯絡人統編邏輯 | 同上 | 詢問 → 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:89` |
| 執行後 | 伺服端回傳訊息 | 依 `Result[0].ReturnMessage` | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:507-509` |

**一個 copy-paste 漏改**:聯絡人統編那一次呼叫傳的欄位名稱是 `this.custCNT_ID_NO.Text`(**控件自己的內容**)而不是對應的標籤文字 (`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:90`,對照上一行 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM337.cs:89` 傳的是 `this.ulblID_NO.Text`)。訊息會變成「(統編值)不符合正常邏輯,是否忽略?」,使用者看不出是在講聯絡人。

新增成功訊息由 Ctl 組:「新增成功,退件單號:{0}」 (`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM337_Ctl.cs:53-54`)。這一行沒有先檢查 `Result.Count`,直接讀 `Result[0]` —— 與 `architecture.md §6` 記的 `CASM001_Ctl` 同型, 本片另有 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM221A_Ctl.cs:59`、 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:61`、 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM270_Ctl.cs:49` 三處相同寫法。

### 4.8 `OFDM271` 缺件到件／回復登錄

用途(推測):把已到件的缺件打勾、填到件日期,一次執行;或反向把誤登的到件日期**回復**成空白。代號是 `M`,行為是 B。

#### 為什麼它的主檔不是真的

| 事實 | 證據 |
|---|---|
| PO 宣告 `MasterTable = OFD724` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:32` |
| **全支程式只有這一行提到 `OFD724`** | UI / Ctl / PO 三層 grep `OFD724` 只有一處命中 |
| `BeforeSelect` 把 `args.DbCmd` 整個換掉,SQL 打的是 `OFD272A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:363-372`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:243-283` |
| vdb `OFDM271` 的欄位與 PK 完全是 `OFD272A` 的 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM271Model.xsd` |
| UI 繼承 `xOneStepProcessForm`,不是 `xMaintainForm` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28` |
| Ctl 只有 `Execute` 與 `Query` 兩個業務方法,沒有 Add / Modify / Verify / Approve | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM271_Ctl.cs:45`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM271_Ctl.cs:59` |

**結論**:`xTableMapping("OFD724", ...)` 只是為了讓框架有個主檔名可填, `OFD724` 在這一支完全沒有被讀也沒有被寫。掃描器把它列成 `OFDM271` 的主檔是字面比對的結果。 `OFD724` 真正的主檔持有者是 `OFDB327` / `OFDM723` / `OFDM724`,**都在 OFD9 那一片,另見 `ofd9.md`**。

#### 查詢(`BuildMasterSQLString`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:238-361`)

`OFD272A` join `OFD039A`(缺件代碼)join `BMS001`(受益人)left join `OFD251A`(買回書), 再依畫面上的「執行別」單選鈕加條件:

| 執行別 | 加的條件 | 結果類型 | 錨點 |
|---|---|---|---|
| 到件登錄(`ExecType='1'`) | `GET_COPY_DATE` 為空 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:271` |
| 到件回復(`ExecType='2'`) | `TRN_CD<>'3' OR (TRN_CD='3' AND OFD251A.DOC_NID<>'Y')` | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:277` |
| 缺件種類篩選 | `TRN_CD IN ('1','5')` 或 `NOT IN ('1','5')` | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:280-282` |

第二列是 **Oracle 三值邏輯的典型踩法**:`OFD251A.DOC_NID <> 'Y'`,`DOC_NID` 為 NULL 時整條是 UNKNOWN, 那筆買回缺件就從清單上消失。程式作者自己在同一行註解寫「DOC_NID可以是空白或N」—— **知道它可能不是 `'Y'`,但沒想到它可能是 NULL**。而且這是 left join 來的欄位,沒有對應買回書時必定是 NULL。

#### 執行(`Execute`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:50-227`)

| 步 | 條件 | 做什麼 | 錨點 |
|---|---|---|---|
| 1 | `ExecType='2'` | 先查 `OFD251A`,若 `DOC_NID='Y' AND STOP_PAY_YN='Y'` 就整批 rollback | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:77-91` |
| 2 | `ExecType='2'` | `UPDATE OFD272A SET GET_COPY_DATE=' ', GET_COPY_UID=' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113` |
| 3 | `STOP_PAY='Y'` 且 `TRN_CD` 是贖回轉換 | `UPDATE OFD251A SET DOC_ADATE=' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:118-126` |
| 4 | `ExecType='1'` | `UPDATE OFD272A SET GET_COPY_DATE=<畫面值>` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` |
| 5 | `TRN_CD` 是開戶或受益人異動 | `UPDATE OFD607A SET PROCESS_YN='Y'`(解鎖網路交易) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:153-168` |
| 6 | `STOP_PAY='Y'` 且贖回轉換,且該書號已無未到件 | `UPDATE OFD251A SET DOC_ADATE = (SELECT MAX(GET_COPY_DATE) …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:171-199` |

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前(UI) | 至少勾一筆 | 至少須註記一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:76` |
| 執行前(UI) | 到件日期格式 | 到件日期 格式不符 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:91` |
| 執行前(UI) | 到件日期須為公司營業日 | 到件日期 必須為公司的營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:110` |
| 執行前(UI) | 到件日期 ≥ 缺件日期(僅到件登錄) | 到件日期 必須大於等於 缺件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:118` |
| 執行中(PO) | 已通知保管銀行付款 | X 此贖回付款資料已通知保管銀行付款,不可回復到件日期 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:89` |
| 執行中(PO) | `OFD272A` 更新筆數 ≠ 1 | **空字串** | 阻擋(訊息空白) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:112`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:149` |
| 執行中(PO) | 任何例外 | **空字串** | 阻擋(訊息空白) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:210`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:218`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:224` |

**五個失敗出口裡有四個回傳空訊息。**使用者只會看到一個沒有內容的錯誤框。成功時回的筆數 `Convert.ToInt32(j)` 也不是更新筆數,而是**最後一次 `ExecuteScalar` 的結果** (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:205`); 若這次執行沒有走到任何 `ExecuteScalar`,`j` 是 null,回傳 0 筆卻是成功。

### 4.9 `OFDM242` 投資組合(契約)贖回維護

用途(推測):針對**投資組合 / 契約**(畫面標籤「投資組合」`PORTFOLIO_CODE`、「契約書號」`EC_RSP_NO`) 一次建立多筆贖回。是 `OFD251A` 在本片的第二個建檔入口。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | **`MultiRowEVAPO`**(舊世代多筆) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:23` |
| 主檔(三個) | `OFD251A` `OFD252A` `OFD254A` 全部掛 `MasterTable.Add` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:33-35` |
| xsd DataTable 名 | `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`(§2.1) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM242Model.xsd` |
| EVA 掛點 | `BeforeAdd` `BeforeSelect` `BeforeApproveDelete` `AfterApproveDelete` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:37-40` |

#### 這一支跑不動(**假設**,依據如下)

| 依據 | 錨點 |
|---|---|
| `MultiRowEVAPO` 的 `dbTA` / `dbPTPF` 在建構子裡**被註解掉不賦值** | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175` |
| `MultiRowEVAPO.Add` 第一行就 `cn = dbTA.CreateConnection()` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:187` |
| `OFDM242_PO` 自己的 `m_db` 也被註解成 null,卻在 `GetMasterData` 直接 `m_db.CreateConnection()` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:31-32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:188-190` |
| `BeforeApproveDelete` 的 SQL 是**整段 T-SQL 批次**:`DECLARE @FUND_ID VARCHAR(10)`、游標 + `@@FETCH_STATUS`、`SqlDbType.NVarChar` 參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:63-131` |
| 查詢 SQL 用 `CONVERT(VARCHAR(10), …, 111)` 與 `@REDEM_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1192`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1233-1235` |

連線欄位為 null 會先丟 `NullReferenceException`;就算連上了,Oracle 也不吃 T-SQL 批次。 **要推翻這個判斷只需要在現場按一次查詢。**

#### 卡控總表(UI 層,仍完整)

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 收件日期須為營業日 | 收件日期 不為營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:110` |
| 存檔前 | 至少一筆明細 | 明細至少需輸入一筆資料 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:116` |
| 存檔前 | 匯入帳號必填 | 基金 X 匯入帳號 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:132` |
| 查詢前 | 七個條件擇一 | 收件日期、贖回日期、受益人ID、受益人戶號、投資組合、贖回書號、契約書號 必須擇一輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:158` |
| 挑基金時 | 受益人仍有缺件 | 受益人仍有缺件資料,不可贖回 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:502` |
| 挑基金時 | 受益人被列管禁止贖回 | 受益人 X … 被列管禁止贖回基金 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:509` |
| 挑基金時 | 基金停止贖回 | 基金[X]停止贖回!請查 OFDM114 受益人停止申贖設定檔。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:516` |
| 挑基金時 | 基金暫停贖回 | 基金[X]暫停贖回!請查 OFDM087 基金暫停申贖日期設定檔。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:523` |
| 挑基金時 | 無可贖回單位數 | 無可贖回單位數 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:537` |
| 新增前 | 該贖回日該基金已過帳 | 贖回日期[X] 已執行 基金 Y 過帳,無法再新增資料。 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:604` |
| 刪除前 | 已過帳 | 基金 X 已過帳,不可刪除 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:621` |

這些訊息裡直接寫出別的畫面代號(`OFDM114` / `OFDM087`)—— 對使用者友善,但也代表 **這兩支設定畫面改代號的話,訊息字串要一起改**。

### 4.10 `OFDM220` 與 `OFDM232` — 一對只改了一半的彙總畫面

`OFDM220`(申購彙總)與 `OFDM232`(買回彙總)是結構完全對稱的一對: 同樣以「基金 + 銷售機構 + 日期」為主鍵,同樣沒有明細,同樣在存檔時更新過帳控制檔 `OFD303A`。但兩邊的實作有**三處不對稱**:

| 面向 | `OFDM220` | `OFDM232` | 影響 |
|---|---|---|---|
| 掛在哪個事件 | `AfterAdd`,且註解寫明「20090331 by lichyu BeforeAdd改到AfterAdd」,舊的 `BeforeAdd` 訂閱留在註解裡 | **仍然掛 `BeforeAdd`** | 主檔還沒寫入就先動控制檔;失敗時控制檔已改 |
| SQL 參數 | `AddInParameter` 綁 `UPDATEID` / `UPDATEDATE` / `FUND_ID` / `CTL_DATE` | `string.Format` 直接把 `FUND_ID` 與日期串進 SQL | 注入面;且型別轉換靠字串 |
| 更新者欄位 | `SET ALLOT_CTL_CODE='1', UPDATEID=:UPDATEID, UPDATEDATE=:UPDATEDATE` | `SET REDEM_CTL_CODE = '1'`(**沒寫更新者**) | 買回側改動查不到是誰改的 |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:47-48`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:113-131` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:48`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:121-131` |  |

#### 卡控總表(兩支合併)

| 畫面 | 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `OFDM220` | 存檔前 | 銷售總手續費 ≥ 銷售機構手續費 | 銷售總手續費 不得小於 銷售機構手續費 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:200` |
| `OFDM220` | 查詢前 | 申購日期起訖成對且不倒置 |  | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:216-221` |
| `OFDM220` | 存檔前 | 基金已關閉 | 依 `FundCloseMsg` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:379-384` |
| `OFDM220` | 存檔前 | 基金 / 日期相關伺服端檢核 | 依 `strErr` | 阻擋 / 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:239`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM220.cs:284-338` |
| `OFDM232` | 存檔前 | 金額 / 單位數擇一必填 | (單位數買回)總單位數 與 (金額買回)總金額 至少擇一輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:184-192` |
| `OFDM232` | 存檔前 | 短線交易費率未設定 | 短線交易費率 尚未設定 | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:527` |
| `OFDM232` | 存檔前 | 該買回機構不檢核基金彙總 | 此買回機構不檢核基金彙總,是否仍要輸入 | 詢問 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:595` |
| `OFDM232` | 存檔前 | 基金已關閉 | 依 `FundCloseMsg` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM232.cs:475-480` |

「短線交易費率 尚未設定」這條把 `OFDM232` 與 `OFDM233`(§4.13)綁在一起: 沒有先在 `OFDM233` 建好費率,這裡只會**警示**,不會擋。

### 4.11 `OFDM302` 基金淨值維護

用途:每日建立 / 修改基金的正式淨值、申購淨值、贖回淨值、資產規模、發行單位數。多筆型畫面,一次可以貼一整批基金。

| 項目 | 內容 | 錨點 |
|---|---|---|
| PO 基底 | `BaseMultiRowEVADaoPO, IOFDM302_PO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:29` |
| 主檔 | `OFD302A`(`FUND_ID` + `NAV_DATE`) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:39` |
| EVA 掛點 | `BeforeSelect` `BeforeUpdate`(共用 `BeforeUD`)`BeforeGetMaintainData` `BeforeGetToDoData` `BeforeAdd` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM302_PO.cs:34-38` |

#### 卡控總表

| 時點 | 檢核 | 訊息 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 至少一筆明細 | 明細資料 必須輸入 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:41` |
| 存檔前 | 淨值日須為該基金營業日 | yyyy/MM/dd 不為基金[X] 之營業日 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:57` |
| 存檔前 | 基金須屬所選基金公司 | 所挑選的基金代碼[X] 不為該基金公司[Y] 所屬的基金 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:64` |
| 存檔前 | 基金已成立 | 基金代碼[X]尚未成立 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:72` |
| 存檔前 | 淨值日 ≥ 基金成立日 | 淨值日期不可小於基金代碼[X]的成立日期 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:80` |
| 查詢前 | 淨值日期起 ≤ 迄 | 淨值日期(起) 不可大於 淨值日期(迄) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:220` |
| 刪除前(按鈕) | 有鎖定淨值 | 刪除資料中有已鎖定淨值資料,無法刪除,請檢查 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:265-268` |
| 刪除前(刪列) | 有鎖定淨值 | 同上 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:353-357` |

兩處刪除卡控的訊息完全一樣,判斷寫法不同(按鈕層 `DataTable.Select("NAV_LOCK='…'")`、列層 `row.NAV_LOCK == NAV_LOCK.Lock`)。與 §4.1.3 同型:改一邊要記得改兩邊。

有一條**被註解掉的檢核**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:55` (「淨值日 不存在於 基金代碼[X] 之營業日」)。它與下一行 live 的版本語意相同, 只是訊息寫法不同 —— 屬於重寫後忘了刪,不是功能缺口。

### 4.12 `OFDM361` — 一支沒宣告主明細的空殼

`OFDM361` 是本片唯一「六層檔案齊全但沒有主明細宣告」的畫面。**原因不是漏寫,是根本沒實作。**

| 層 | 行數 | 內容 |
|---|---|---|
| UI | 66 | 繼承 `xMaintainForm`,六個生命週期事件**全部空的**,只有 `DoValidate()` 呼叫 `validatorManager1.DataValidate()`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM361.cs:19-56`) |
| FormProxy | 11 | `public class OFDM361_Pxy : Basic_Pxy { }` —— 空類別(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM361_Pxy.cs:8-10`) |
| Control | 10 | `public class OFDM361_Ctl { }` —— **連 `BaseController` 都沒繼承**(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM361_Ctl.cs:7-9`) |
| PO | 11 | `public class OFDM361_PO : BasicEVAPO { }` —— 空類別,沒有 `MasterTable`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10`) |
| DataEntity | 655 | 一張 DataTable `OFDM361`,103 欄,PK `PR_NO` |
| UIEntity | 655 | 與 Model 同構 |

**但 Designer 是完整的。**`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM361.Designer.cs` 有 653 行、 26 個中文標籤,包含「潛在客戶序號」「投資偏好」「每月可投資金額」「年平均所得」「DM寄送碼」「受益人類別」「教育程度」「預期投資時間」「服務業別」等 —— 這是一張**潛在客戶維護**的畫面。

xsd 的欄位清單(`PR_NO` `USAGE` `BF_NO` `EMP_NO` `ID_NO` `PR_NAME` `BIR_DATE` … `INVST_TEND_CD` `MIN_INVEST_CODE` `INVEST_AMT_CODE` `ANNUAL_INCOME`)與 `CRM003A` 高度重疊, 而 `CRM003A` 的主檔畫面是 `CASM001` 與 `CRMM003`(`cas.md §4`)。

**結論(推測)**:`OFDM361` 是從 CAS / CRM 的潛在客戶維護畫面複製過來、 UI 與 entity 做完、Control / PO / Pxy 三層還沒寫就停住的半成品。 **沒有主明細宣告 = 它從來沒有被接上資料庫**,不是設定漏掉。依據:三層都是零成員的空類別,而不是「有成員但沒宣告 MasterTable」; 以及 `OFDM361_Ctl` 連基底類別都沒寫,任何 Pxy 呼叫都編不出來。

實務上的處置建議只有兩條路:**當作死碼移除**,或**補完三層**。在那之前,`atlas_scan.py --screen OFDM361` 回「主檔 —」是正確的,不要去補一個假的 `xTableMapping`。

### 4.13 其餘 12 支(表格帶過)

| 畫面 | 主明細 | 四眼 | 主要卡控(一句話) | 特別之處 |
|---|---|---|---|---|
| `OFDM091` | `OFD091A` / `OFD092A` | 有 | 費率 < 100、起算日 ≤ 終止日、起算日與終止日皆須 > 0、基金代碼必填 | 與 `OFDM233` 是同一張樣板做出來的兩支(主檔皆 `FUND_ID` + `RANGE_TYPE`,明細皆 `BNG_DAY` / `END_DAY` 區間),差別只在費率欄位;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM091.cs:63-92` |
| `OFDM233` | `OFD260A` / `OFD261A` | 有 | 下限 ≤ 上限、費率 < 100、起算日 ≤ 終止日 | 短線交易費率的唯一來源,`OFDM231A` 與 `OFDM232` 都吃它;PO 內 307–466 行整段註解(舊 SQL Server 版);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM233.cs:77-102`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:307-466` |
| `OFDM243A` | `OFD243A` | 有 | **只有一條**:配單金額不得為 0 | `OFD243A` 的主檔持有者,但同一張表被 `OFDM221A` / `OFDM231A` 當明細寫;PO 只有三個取數掛點,零副作用;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM243A.cs:123`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:39-42` |
| `OFDM270` | `OFD270A` | 有 | 處理完成日期必填且 ≥ 退郵日期、永久失聯日期必填、非退郵戶不可設永久失聯 | 有完整 8 個 After 掛點但都只寫跳號;`OFD270A` 實體只有 2 欄(`BF_NO` / `REJ_STOP_DATE`),vdb 43 欄其餘都是 join 來的;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM270.cs:48-59`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM270.cs:464` |
| `OFDM284` | `OFD286A` | 有 | 依伺服端 `Result` 回傳訊息掛在戶號欄位上 | **舊世代 `MultiRowEVAPO`**;SQL 用 `[BMS001]` `[OFD286A]` `[LOG106]` 方括號;xsd 帶一張叫 `LOG` 的表(對 `LOG106`)但 `MasterTable.Add` 那行被註解;錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:38-39`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:415-433` |
| `OFDM285` | `OFD290A` | 有 | **只有一條**:明細資料 必須輸入 | **舊世代 `MultiRowEVAPO`**;PO 只有 217 行、三個取數掛點;`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM285_PO.cs:83` 會檢查 `Result[0].ReturnCode`,是舊世代裡少見的;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM285.cs:38` |
| `OFDM286` | `OFD291` | 有 | 必填欄位、申請日期 ≤ 終止日期、**同一基金僅可有一筆生效中資料** | 最後一條在兩個地方各寫一次(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:307` 與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:328`),分別對應新增列與修改列,兩段判斷各自獨立 —— 又一個「改一邊要改兩邊」 |
| `OFDM297` | `OFD297A` | 有 | 兩個淨值日期必填、變更前 < 變更後、至少勾一檔基金 | `BeforeAdd` + 6 個 After 掛點;失敗訊息由伺服端逐列回傳並掛到 grid 上(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM297.cs:174`),是本片唯一「逐列回報」的畫面;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM297.cs:148-157` |
| `OFDM300` | `OFD300` | 有 | **只有一條**:匯率必須大於 0 | 與 `OFDM301` 成對;用 `Convert.ToDecimal` 判斷;錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM300.cs:147-153` |
| `OFDM301` | `OFD301` | 有 | 兌換入 ≠ 兌換出、匯率必大於 0 | 與 `OFDM300` 成對,但**用 `Convert.ToDouble` 判斷金額類欄位**,訊息也少一個字(「匯率必大於0」);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM301.cs:148-157` |
| `OFDM321` | `OFD321` / `OFD322` | 有 | 總額度 > 0、至少一筆明細、**各通路額度加總須等於控管總額度**、控管起 ≤ 迄 | **舊世代 `BasicEVAPO`** + `[OFD321]` / `[OFD322]` 方括號 SQL;它維護的額度被 `OFDM221A` 的 `ChkFundQuota` 讀去,但那邊只詢問不擋(§4.1.2);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM321.cs:135-173`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163-181` |
| `OFDM344` | `OFD344` | 有 | **UI 沒有任何業務檢核**,只有 `validatorManager1` 的欄位驗證 | **舊世代 `BasicEVAPO`**;`BeforeAdd` / `AfterAdd` 有掛但 live 段只組 SQL;251–459 行整段註解(含另一份 `Add` / `Select` override);錨點 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM344.cs:206`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:250-459` |

#### 這 12 支的共同形狀

1. **卡控條數與資料重要性不成比例。**`OFDM300` / `OFDM301` 是全庫金額計算的基礎, 卻各只有一到兩條檢核;`OFDM264`(媒體檔格式)反而有二十幾條。

2. **`OFD270A` 的 vdb 是個「拼出來的表」。**實體只有 2 欄,畫面上 43 欄裡有 41 欄來自 `BMS001` 等 join, **改這些欄位改不到任何東西**(它們沒有進 `xTableMapping` 的寫入路徑)。

3. **舊世代那幾支的 UI 檢核仍然完整。**`OFDM321` / `OFDM344` / `OFDM284` / `OFDM285` 的 UI 層是活的, 只有 PO 層跑不動。這代表使用者會看到正常的畫面、正常的檢核,然後在按下存檔的那一刻才失敗。

## 5. 查詢畫面(I)

**本片無 I 畫面。**

原因:`DataEntity.OFD8` 是 `ATLAS.OFD` 專案內 entity 的**第八個分卷**,而 OFD 的查詢畫面(`OFDIxxx`) 依鐵律住在 `.Query` 專案 —— `Dev/ATLAS.OFD.Query/Source/` 與 `Dev/ATLAS.OFDI/Source/` (`architecture.md §2`)。那兩個專案有自己的 `QueryDataEntity.OFD` / `DataEntity.OFDI`, 不會出現在本片的 entity 目錄裡。

與本片相關、但住在別處的查詢畫面有兩支值得知道:

| 畫面 | 位置 | 與本片的關係 |
|---|---|---|
| `OFDI011` | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` | 讀 `OFD272A` 做缺件查詢(`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2465-2488`),條件與 `OFDM271` 的清單不同步 |
| `OFDI911` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs` | 用 SP 的 RefCursor 出參名 `RES_OFD272A` 撈缺件(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:79`) |

## 6. 批次(B)與 WindowsService

**本片無 B 畫面,也沒有任何 WindowsService。**

原因同 §5:OFD 的批次畫面(`OFDBxxx`)分散在 `Dev/ATLAS.OFDB/`(結帳、過帳、產檔) 與 `Dev/ATLAS.EC/`(`OFDB6xx` 服務型,含三支 WindowsService),entity 也在各自的分卷。全庫只有四支 B 畫面配了獨立 Windows 服務,沒有一支屬於 OFD8(`architecture.md §6`)。

但這 24 支是**批次的上游**,關係如下(依表推得,不是程式呼叫):

| 本片寫的表 | 讀它的批次(在別的片) |
|---|---|
| `OFD220A` / `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDB310` `OFDB331` |
| `OFD251A` / `OFD252A` / `OFD253A` / `OFD254A` | `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` |
| `OFD272A` | `OFDB310`(申購缺件)、`BMSM004` / `BMSM006`(受益人側) |
| `OFD281A` / `OFD287A` / `OFD288A` | `OFDB281`(配息計算) |
| `OFD297A` | `OFDB002` |
| `OFD337A` | `OFDB002` 之外未見批次讀取 |
| `OFD264A` / `OFD265A` / `OFD266A` | 付款媒體檔產檔程式(repo 內未定位到唯一呼叫端) |
| `OFD724` | `OFDB327`(**在 OFD9 那一片**) |

`OFD303A` / `CTL012` / `CTL022` 三張控制檔是本片與批次之間**真正的握手機制**: M 畫面把控制碼從 `0`(無資料)推到 `1`(有資料),批次跑完再推到 `2` / `3` / `4`。本片只寫 `'1'` 這一段,不會自己把它推到已結轉。

## 7. 報表(R)

**本片無 R 畫面,`Dev/ATLAS.OFD/` 底下也沒有任何 `.rpt`。**

原因:報表依鐵律住在 `ATLAS.<模組>.Report` 專案(`architecture.md §6`), 對 OFD 來說是 `Dev/ATLAS.OFD.Report/`,是另一個 solution 專案,entity 不在 `DataEntity.OFD8`。

本片的資料會出現在別模組的報表裡,實測到一支:

| rpt / 報表畫面 | 位置 | 取本片哪張表 |
|---|---|---|
| `NFDR813` | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:86-97` | `OFD272A`(`TRN_CD = '1'` 且未到件的受益人) |

## 8. 跨模組共用

```text
[圖] OFD8 的跨模組接觸面:申購四張表給 BBS、缺件檔給 BMS 與 RSP、OFD724 掛名主檔
圖中文字:A 組:申購四張表借給 BBS——OFD 這邊有四個建檔入口 / OFDM221A〔OFD8〕 / 正常開單 主檔持有者 / OFD220A OFD221A / OFD234A OFD235A / BBSM013 BBSM113〔BBS〕 / 轉讓過戶 也會 INSERT / bbs.md 對得上 / 差在附屬表與轉換開單 / A 組補充:bbs.md 沒看到的兩件事 / OFDM231A 轉申購 / 也會新開一張申購書 / SrNo.AllotNoForNfdS / 轉換用另一組流水號 / OFD220A_AGENT OFD136A / 兩張附屬表 BBS不建 / OFD221A 四種形狀 / 改欄位要同步四份xsd / B 組:OFD272A 缺件——六個入口寫、一個入口結案、沒有主檔 / OFDM221A OFDM231A / TRN_CD = 2 / 3 / BMSM004 BMSM006〔BMS〕 / TRN_CD = 1 / 5 / RSPM004 RSPM005〔RSP〕 / TRN_CD = 4 / 6 / OFD272A / 沒有主檔畫面 / B 組的結案路徑:唯一出口不走四眼 / OFDM271 / 直接 UPDATE 到件日 / OFD251A.DOC_ADATE / 缺件到齊才放行付款 / OFD607A PROCESS_YN / 解鎖網路交易 / Utility_PO / 缺件超天數就擋交易 / C / D 組:本片內部共用,與一張只是掛名的主檔 / OFD243A〔本片共用〕 / 三支寫 卡控強度不一 / OFD724 / OFDM271 不讀不寫 / OFDM723 OFDM724〔OFD9〕 / 真正的主檔持有者 / 另見 ofd9.md / 本片只能講到這裡
```

*圖:圖 5 跨模組。橘框=本片的主檔或關鍵表;白框=表與連動欄位;灰虛框=別模組或別片的用法;橘虛框=風險與本文修正 bbs.md 的地方;黑框=共用層或版控外。B 組最值得記:OFD272A 有六個寫入入口,卻只有 OFDM271 一個結案入口,而且那一步不走四眼。*

本片對外的接觸面集中在**四組表**,每一組的「借法」都不一樣。

### 8.1 A 組:`OFD220A` / `OFD221A` / `OFD234A` / `OFD235A` 給 BBS

`bbs.md §8` 已經從 BBS 側寫過這四張表。這裡從 OFD 側補完,並對答案。

#### 從 OFD 側看到的事實

| 表 | 本片的角色 | 誰在寫 |
|---|---|---|
| `OFD220A` | `OFDM221A` 的**主檔** | `OFDM221A`(正常開單)、`OFDM231A`(轉換開單)、`OFDB310`(主檔)、`BBSM013` / `BBSM113`(轉讓開單) |
| `OFD221A` | `OFDM221A` 的第一張明細 | 同上 + `OFDM231A` 的 `RDMING_UNIT` 手寫 UPDATE |
| `OFD234A` | `OFDM221A` 的支票明細 | `OFDM221A`、`BBSM013` / `BBSM113` |
| `OFD235A` | `OFDM221A` 的匯款明細 | `OFDM221A`、`BBSM013` / `BBSM113` |

#### 與 `bbs.md` 對得上的部分

| `bbs.md` 的說法 | 從 OFD 側驗證 | 結論 |
|---|---|---|
| 「`OFD220A` 主檔畫面 `OFDB310` / `OFDM221A`」(`bbs.md §8`) | `OFDM221A_PO.cs:67` 宣告 `MasterTable = OFD220A` | **對得上** |
| 「`BBSM013` / `BBSM113` 會 INSERT `OFD220A` / `OFD221A` / `OFD234A` / `OFD235A`,等於在 OFD 的地盤上開了第二個建檔入口」 | OFD 側沒有任何程式碼防止外來 INSERT;`OFDM221A` 查詢時也不分辨書號來源 | **對得上** |
| 「`OFD234A` / `OFD235A` 沒有主檔畫面」 | 掃描器實測「主檔於:—」,本片也只把它們當明細 | **對得上** |
| 「`OFD221A` 在不同模組裡被當成不同形狀的東西,改欄位要同時看 BBS、OFD、EC 三邊的 xsd」 | 本片再加一種形狀:`OFDM243A` 的 `OFD221A` 只有 7 欄 | **對得上,而且要改四邊** |

#### 對不上、或 `bbs.md` 沒說到的部分

| # | 差異 | 說明 |
|---|---|---|
| 1 | **`bbs.md` 沒提到 `OFDM231A` 也會建 `OFD220A` / `OFD221A`。** | `bbs.md §8` 的表把 `OFDM231A` 列在「明細於」,但沒說它會 INSERT。實際上轉申購會新開一張申購書(§4.3.3),**用的是另一組流水號 `SrNo.AllotNoForNfdS`**。所以 `OFD220A` 的建檔入口是四個不是三個。 |
| 2 | **`bbs.md` 說 `OFD221A` 的欄位定義「12 欄,沒有四眼欄位」;掃描器索引實測是 13 欄。** | 索引來源同樣是 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB672Model.xsd`。這是計數差,不影響結論(該 xsd 版本確實沒有四眼欄位)。 |
| 3 | **本片的 `OFD221A` 有四眼欄位。** | `OFDM221A` 的 `OFDM221A_Detail` 125 欄含完整 8 個四眼檢查欄(§2.2)。`bbs.md` 說「BBS 這邊掛在四眼流程上(所以 `BBSM013Model.xsd` 給它補了四眼欄)」—— 實際上**不是 BBS 補的,OFD 這邊本來就有**;EC 的 `OFDB672` 那份才是精簡版。這一條要修正 `bbs.md` 的因果敘述。 |
| 4 | **`OFD220A` 還有一張 `OFD220A_AGENT` 附屬表,`bbs.md` 沒提。** | 意定代理人(`SHOLDER_ID_NO`),PK 就是 `ALLOT_NO`,只有 `OFDM221A` 寫。BBS 轉讓開單時**不會**建這張 —— 轉讓來的申購書沒有意定代理人資料。 |
| 5 | **`OFD136A`(交易指示代理人)也掛在申購書上,`bbs.md` 沒提。** | 2023 年加的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:75-76` 註解 `20230715 … 9000012360`),PK `TRADE_NO` + `TRADE_TYPE`。同樣地,BBS 轉讓不會建。 |

**綜合判斷**:兩份文件的主結論一致(四張表歸 OFD、BBS 是第二入口、改欄位要多邊同步), 差異集中在「OFD 側後來加了兩張附屬表、而且買回畫面也會開申購書」這兩件 BBS 側看不到的事。第 3 點是 `bbs.md` 的因果寫反了,建議回頭修。

### 8.2 B 組:`OFD272A` —— 四個模組六支畫面共用、沒有主檔

`bms.md` 已從 BMS 側寫過。這一節回答:**這張表到底誰在寫、生命週期怎麼走。**

#### 沒有主檔畫面是事實

掃描器實測「主檔於:—」。全庫**沒有任何 PO 把 `OFD272A` 宣告為 `MasterTable`**, 它永遠以 `DetailTable.Add(new xTableMapping("OFD272A", …))` 的身分存在。

#### 誰在寫(實測全庫)

| 模組 | 畫面 / 程式 | 角色 | 寫什麼 | 錨點 |
|---|---|---|---|---|
| OFD | `OFDM221A` | 明細(vdb `OFD272`) | 申購缺件:`TRN_CD='2'`、`SHORE_ID='2'`、`TRN_NO` = 申購書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:69`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:913-928` |
| OFD | `OFDM231A` | 明細(vdb `OFD272`) | 買回缺件:`TRN_CD='3'`、`TRN_NO` = 買回書號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:73`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1155-1176` |
| OFD | **`OFDM271`** | **直接 UPDATE(不走四眼)** | 只改 `GET_COPY_DATE` / `GET_COPY_UID` / `TRN_MEMO` / `UPDATEID` / `UPDATEDATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` |
| OFD | `OFDB310` | 明細 | 申購缺件(與 `OFDM221A` 同一段 SQL 的複製) | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB310_PO.cs:1025-1037` |
| BMS | `BMSM004` | 明細(vdb `BMSM004_Lack`) | 開戶缺件 `TRN_CD='1'` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:40` |
| BMS | `BMSM006` | 明細(vdb `OFD272`) | 受益人異動缺件 `TRN_CD='5'` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:111`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1914` |
| BMS | `BMSM001` | 唯讀 | 查缺件 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1007-1008` |
| RSP | `RSPM004` | 明細(vdb `OFD272`) | 小額契約缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80` |
| RSP | `RSPM005` | 明細(vdb `OFD272`) | 定期定額異動缺件 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM005_PO.cs:149` |
| OFD | `OFDI011` | 唯讀 | 缺件查詢 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:2465-2488` |
| NFD | `NFDR813` | 唯讀 | 報表 | `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs:86-97` |
| 共用 | `Utility_PO.GetLackData`(類) | 唯讀 | **交易限制判斷**:缺件超過 `OFD039A` 設定的天數就限制申購 / 買回 / 轉換 / 小額 | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130` |

**修正一條前情**:任務描述說 `OFD272A` 被四個模組當明細(`BMSM004` `BMSM006` `OFDM221A` `OFDM231A`)。掃描器實測是**六支畫面、三個模組**(多了 `RSPM004` `RSPM005`),再加上 `OFDM271` 的直接 UPDATE 與 `OFDB310` 的第四個明細入口。

#### 生命週期

| 階段 | 誰 | 動作 | 欄位 |
|---|---|---|---|
| ① 產生 | 六支 M 畫面之一(依交易種類) | 四眼 INSERT | `TRN_CD` + `TRN_NO` + `ORG_COPY_CD` + `SHORE_ID` + `LACK_DATE` |
| ② 生效 | 四眼覆核 | **但資料在輸入當下就在了**(§0.2) | `STATUS` |
| ③ 限制 | `Utility_PO` 被各交易畫面呼叫 | 依 `OFD039A` 的 `LIMIT_ALLOT` / `LIMIT_REDEM` / `LIMIT_SWITCH` / `LIMIT_RSP` 與各自的天數,決定是否擋交易 | 讀 `LACK_DATE` |
| ④ 到件 | **`OFDM271`** | 直接 UPDATE,**不經四眼** | `GET_COPY_DATE` / `GET_COPY_UID` |
| ⑤ 連動 | `OFDM271` | 到件後視情況更新 `OFD251A.DOC_ADATE`(買回放行付款)、`OFD607A.PROCESS_YN`(解鎖網路交易) | — |
| ⑥ 回復 | `OFDM271`(執行別 2) | 把 `GET_COPY_DATE` / `GET_COPY_UID` 塞回一個空白字元 | — |
| ⑦ 刪除 | 只能跟著上游交易一起刪(四眼 ApproveDelete) | 沒有獨立的缺件刪除入口 | — |

**三個要記住的結論**:

1. **`OFD272A` 的產生是分散的、消滅是集中的。**六個入口寫進去,只有 `OFDM271` 一個入口把它「結案」。

2. **結案那一步不走四眼。**`OFDM271` 是 `xOneStepProcessForm`,按下執行就直接 UPDATE 落地(§4.8)。所以缺件到件**沒有覆核軌跡**,只有 `UPDATEID` / `UPDATEDATE`。

3. **`TRN_NO` 是多型外鍵,沒有 FK。**要 join 回上游交易,一定要先看 `TRN_CD`。 `OFDM271` 自己就是 left join `OFD251A ON OFD272A.TRN_NO = OFD251A.REDEM_NO` (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:262-263`)—— 對 `TRN_CD` 不是 `'3'` 的列這個 join 永遠落空, 然後 `DOC_NID <> 'Y'` 的條件又把它們過濾掉(§4.8、附錄 E-2)。

### 8.3 C 組:`OFD243A` —— 本片內部的三方共用

| 畫面 | 角色 | 說明 |
|---|---|---|
| `OFDM243A` | **主檔** | 券商配單的正規維護入口,卡控只有「配單金額不得為 0」 |
| `OFDM221A` | 明細(vdb `OFD243`) | 開申購書時一起建配單 |
| `OFDM231A` | 明細(vdb `OFD243`) | 轉申購時一起建配單;取消轉換時連帶刪除(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1848-1852`) |

三支都在本片,沒有跨模組。但**三支的卡控強度差很多**: `OFDM243A` 幾乎沒有檢核、`OFDM231A` 在 `BeforeSave` 裡用 `REBATE_YN == "Y"` 決定要不要建 (`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2116-2130`)。從 `OFDM243A` 改出來的配單不會回頭通知申購書。

### 8.4 D 組:`OFD724` —— 名義主檔,真正的持有者在 OFD9

| 畫面 | 位置 | 角色 |
|---|---|---|
| `OFDM271` | 本片 | `xTableMapping("OFD724", "OFDM271")`,**整支程式只有這一行提到它**(§4.8) |
| `OFDM723` | **OFD9 片** | 主檔 —— **另見 `ofd9.md`** |
| `OFDM724` | **OFD9 片** | 主檔 —— **另見 `ofd9.md`** |
| `OFDB327` | OFD 批次片 | 主檔 |

**從 `OFDM271` 的角度只能講到這裡**:它不讀不寫 `OFD724`。要知道 `OFD724` 真正的欄位、主鍵與業務語意,去看 `ofd9.md` 的 `OFDM723` / `OFDM724` 兩節。 **如果 `ofd9.md` 那邊描述的 `OFD724` 形狀與本片 `OFDM271Model.xsd` 裡的 `OFDM271` DataTable 對不上, 那不是矛盾 —— 是因為本片那張 DataTable 裝的其實是 `OFD272A`。**

### 8.5 本片用到的共用 PO 與工具類

| 類別 | 位置 | 誰用 | 做什麼 |
|---|---|---|---|
| `Utility_PO` | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1096-1130` | 各交易畫面 | 依 `OFD272A` + `OFD039A` 算交易限制 |
| `SerialNo` | 無原始碼,從呼叫端反推 | `OFDM221A` `OFDM231A` `OFDM337` `OFDM331` | 取各式書號(`GetAllotNoForNfd` / `GetRdmNoForNfd` / `GetRejNo`) |
| `SrNoCommentProcessor` | 無原始碼,從呼叫端反推 | 本片 6 支 M 畫面的所有 After 掛點 | 跳號一覽表 |
| `ServerBizUtility` / `ServerNfdBizUtility` | 無原始碼,從呼叫端反推 | `OFDM221A`(優惠身份別)、`OFDM220` / `OFDM232`(控制日期) | 業務計算 |
| `ClientBizUtility` | 無原始碼,從呼叫端反推 | `OFDM271` `OFDM221A` `OFDM242` | 用戶端營業日判斷 |
| `EVAUtility` | `Dev/Common/Source/Utility/TA.ServerUtility/EVAUtility.cs` | `OFDM221A`(**建了沒用**) | 四眼欄位寫入 |
| `xTableHelper` / `xEVAStringHelper` | 無原始碼,從呼叫端反推 | 12 支新世代 PO | 組 SQL 與條件 |
| `TableHelper` / `EVAStringHelper`(舊) | `Dev/Common/Source/Utility/TA.ServerUtility/SQLHelper.cs` | 7 支舊世代 PO | 同上(參數綁定已全數註解,`architecture.md §3`) |

### 8.6 改動影響面速查

| 你要改 | 一定要一起改 / 一起測 |
|---|---|
| `OFD220A` 或 `OFD221A` 的欄位 | 6 份 xsd(`OFDM221A` `OFDM231A` `OFDM243A` `BBSM013` `BBSM113` `OFDB672`)+ `OFDM231A_PO.cs:1936-2105` 的 156 行手寫指派 + `OFDB310` |
| `OFD272A` 的欄位 | 7 份 xsd(`OFDM221A` `OFDM231A` `OFDM271` `BMSM004` `BMSM006` `RSPM004` `RSPM005`)+ `Utility_PO` + `OFDI011` + `NFDR813` |
| `OFD251A` 的欄位 | `OFDM231A`(93 欄版)+ `OFDM242`(71 欄版)+ 7 支 `OFDB3xx` + `SDMB002` |
| 缺件到件的判斷 | `OFDM271`(兩種空值寫法)+ `NFDR813`(`NVL` 寫法)+ `OFDI011` |
| 短線交易費率 | `OFDM233`(維護)+ `OFDM231A`(計費)+ `OFDM232`(警示) |
| 基金銷售額度 | `OFDM321`(維護)+ `OFDM221A`(只詢問不擋) |
| 過帳控制碼 `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232` **四支各寫各的 SQL**,沒有共用方法 |

## 附錄 A. 資料表總表

本片 24 支 PO 一共宣告 **45 張實體表**(去重)。欄位與主鍵見 §2.2,中文名見 §2.3。「共用」欄標 ✓ 者見 §8。

| # | 表 | 主檔於 | 明細於 | 共用 | 一句話 |
|---|---|---|---|---|---|
| 1 | `OFD091A` | `OFDM091` | — |  | 基金遞延手續費主檔 |
| 2 | `OFD092A` | — | `OFDM091` |  | 遞延手續費率區間明細 |
| 3 | `OFD136A` | **無** | `OFDM221A` `OFDM231A` | ✓ | 交易指示代理人 |
| 4 | `OFD220A` | `OFDM221A` `OFDB310` | `OFDM231A` `OFDB331` `BBSM013` `BBSM113` | ✓ | 申購書主檔 |
| 5 | `OFD220A_AGENT` | **無** | `OFDM221A` |  | 申購書意定代理人 |
| 6 | `OFD221A` | `OFDB302` `OFDB304` `OFDB306` `OFDI059` `SDMB001` | `OFDM221A` `OFDM231A` `OFDB310` `OFDB331` `BBSM013` `BBSM113` | ✓ | 申購明細 |
| 7 | `OFD232A` | `OFDM220` | — |  | 銷售機構申購彙總 |
| 8 | `OFD234A` | **無** | `OFDM221A` `BBSM013` `BBSM113` | ✓ | 申購支票明細 |
| 9 | `OFD235A` | **無** | `OFDM221A` `BBSM013` `BBSM113` | ✓ | 申購匯款明細 |
| 10 | `OFD243A` | `OFDM243A` | `OFDM221A` `OFDM231A` | ✓ | 券商配單 |
| 11 | `OFD251A` | `OFDM231A` `OFDM242` `OFDB321` `OFDB322` `OFDB324` `OFDB325` `OFDB326` `OFDB329` `OFDB331` `SDMB002` | — | ✓ | 買回書主檔 |
| 12 | `OFD251A_AGENT` | **無** | `OFDM231A` |  | 買回書意定代理人 |
| 13 | `OFD252A` | `OFDM242` | `OFDM231A` `OFDB331` |  | 買回付款明細 |
| 14 | `OFD253A` | — | `OFDM231A` `OFDB331` |  | 買回轉換(轉申購)明細 |
| 15 | `OFD254A` | `OFDM242` | `OFDM231A` |  | 買回指定沖銷明細 |
| 16 | `OFD258A` | — | `OFDM231A` |  | 買回實體憑證明細 |
| 17 | `OFD259A` | `OFDM232` | — |  | 銷售機構買回彙總 |
| 18 | `OFD260A` | `OFDM233` `OFDB004` | `OFDB004` |  | 短線交易費率主檔 |
| 19 | `OFD261A` | — | `OFDM233` `OFDB004` |  | 短線交易費率區間明細 |
| 20 | `OFD264A` | `OFDM264` | — |  | 付款媒體檔主檔 |
| 21 | `OFD265A` | — | `OFDM264` |  | 媒體檔欄位定義 |
| 22 | `OFD266A` | — | `OFDM264` |  | 媒體檔檔名規則 |
| 23 | `OFD270A` | `OFDM270` | — |  | 永久失聯戶註記(實體僅 2 欄) |
| 24 | `OFD272A` | **無** | `OFDM221A` `OFDM231A` `BMSM004` `BMSM006` `RSPM004` `RSPM005` | ✓ | 缺件檔(§8.2) |
| 25 | `OFD281A` | `OFDM281` `OFDB281` | — |  | 配息設定主檔 |
| 26 | `OFD286A` | `OFDM284` | — |  | 受益人收益分配支付方式 |
| 27 | `OFD287A` | — | `OFDM281` `OFDB281` |  | 配息來源明細 |
| 28 | `OFD288A` | — | `OFDM281` |  | 配息可扣抵稅率明細 |
| 29 | `OFD290A` | `OFDM285` | — |  | 基金匯費設定 |
| 30 | `OFD291` | `OFDM286` | — |  | 受益人配息期間 / 類別 |
| 31 | `OFD297A` | `OFDM297` `OFDB002` | — |  | 臨時放假淨值日期變更 |
| 32 | `OFD300` | `OFDM300` | — |  | 幣別匯率 |
| 33 | `OFD301` | `OFDM301` | — |  | 交叉匯率 |
| 34 | `OFD302A` | `OFDM302` | — |  | 基金淨值 |
| 35 | `OFD321` | `OFDM321` | — |  | 基金銷售額度主檔 |
| 36 | `OFD322` | — | `OFDM321` |  | 各通路額度明細 |
| 37 | `OFD331` | `OFDM331` | — |  | 客訴主檔 |
| 38 | `OFD332` | — | `OFDM331` |  | 客訴代碼明細 |
| 39 | `OFD333` | — | `OFDM331` |  | 客訴內容明細 |
| 40 | `OFD334` | — | `OFDM331` |  | 客訴處理說明明細 |
| 41 | `OFD335` | — | `OFDM331` |  | 客訴處理種類明細 |
| 42 | `OFD337A` | `OFDM337` | — |  | 退件主檔 |
| 43 | `OFD344` | `OFDM344` | — |  | 客戶資料保密設定異動 |
| 44 | `OFD346A` | — | `OFDM337` |  | 退件項目明細 |
| 45 | `OFD724` | `OFDM271`(名義)`OFDB327` `OFDM723` `OFDM724` | — | ✓ | **本片不讀不寫**,見 §8.4 與 `ofd9.md` |

### A.1 不在 `xTableMapping` 裡、但本片會直接下 SQL 的表

這些表不會出現在掃描母體,改它們的欄位不會有任何 xsd 提醒你:

| 表 | 誰動它 | 動作 |
|---|---|---|
| `OFD303A` | `OFDM220` `OFDM221A` `OFDM231A` `OFDM232` | UPDATE / INSERT 過帳控制碼 |
| `OFD304A` | `OFDM231A` | UPDATE |
| `CTL012` | `OFDM221A` | UPDATE / INSERT / DELETE 代扣款控制 |
| `CTL022` | `OFDM221A` `OFDM231A` | UPDATE / INSERT / DELETE 櫃台控制 |
| `OFD130A` | `OFDM221A` `OFDM231A` | INSERT 匯款授權書 |
| `OFD131A` | `OFDM231A` | INSERT |
| `BMS004A` `BMS005A` | `OFDM231A` | INSERT 匯款帳號授權 |
| `OFD721` | `OFDM231A` | UPDATE 實體憑證餘額 |
| `OFD607A` `OFD601` | `OFDM271` | UPDATE 網路交易權限 |
| `OFD039A` | `OFDM231A` `OFDM271` | 唯讀 join(缺件代碼與限制天數) |
| `BMS001` | `OFDM221A` `OFDM284` `OFDM271` | 唯讀 join |
| `OFD199A` | `OFDM221A` | 唯讀(行銷活動) |
| `OFD651A` `OFD656` | `OFDM242` | 唯讀(投資組合贖回處理碼) |
| `LOG106` | `OFDM284` | 唯讀(`MasterTable.Add` 那行被註解) |

## 附錄 B. SP / Function / Trigger / View

本片幾乎不用 DB 物件。全 24 支只出現三個名字,**三個都在版控外,repo 內看不到內容**:

| 物件 | 型別 | 呼叫端 | 用途(從參數反推) |
|---|---|---|---|
| `S_TA_OFDM221A_Get` | Procedure | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2410` | 吃 `striRule='1'`,回一個 RefCursor 灌進 `OFD221A_RULE`(四個欄位 `RULE1`–`RULE4`)—— 畫面上顯示的申購規則文字 |
| `S_TA_UPD_REDEM_SHORT_RMK` | Procedure | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2463` | 更新買回的短線交易註記;呼叫前先用一段 `SELECT COUNT(*) FROM dual WHERE EXISTS(...)` 判斷要不要叫 |
| `f_TA_GetEmpLockUnitsOnTheDay` | Function | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:200` | 吃 `(BF_NO, FUND_ID, 日期, '4')`,回員工 / 員眷閉鎖單位數 |

另外 `f_TA_GetBusinessDay` 出現在共用的 `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:1116-1128` (算缺件超過幾個營業日就限制交易),不是本片自己叫的。

**沒有 Trigger、沒有 View、沒有 `.rpt`。**

## 附錄 C. 代碼對照(狀態碼、型別碼)

完整清單見 §2.5。這裡只補三張本片高頻、但常被搞混的對照:

### C.1 `TRN_CD` 缺件種類 → 上游交易 → `TRN_NO` 放什麼

| `TRN_CD` | 語意 | 由誰建 | `TRN_NO` 放的是 |
|---|---|---|---|
| `1` | 開戶 | `BMSM004` | 受益人開戶書號 |
| `2` | 申購 | `OFDM221A` `OFDB310` | `ALLOT_NO` 申購書號 |
| `3` | 贖回 / 轉換 | `OFDM231A` | `REDEM_NO` 買回書號 |
| `4` | 小額契約 | `RSPM004` | 契約書號 |
| `5` | 受益人異動 | `BMSM006` | 異動書號 |
| `6` | 定期定額異動 | `RSPM005` | 異動書號 |

### C.2 過帳控制碼兩兄弟(值域不同,常數同名)

|  | `ALLOT_CTL_CODE`(申購) | `REDEM_CTL_CODE`(贖轉) |
|---|---|---|
| `0` | 無資料 | 無資料 |
| `1` | 有資料 | 有資料 |
| `2` | 已單位數計算 | 已預估價金計算 |
| `3` | **已結轉** | 已價金計算 |
| `4` | — | **已結轉** |
| 常數名 | `ALLOT_CTL_CODE.Tranfer` = `3` | `REDEM_CTL_CODE.Tranfer` = `4` |

### C.3 「空值」的三種表示法(本片共存)

| 表示法 | 出現在 | 例 |
|---|---|---|
| Oracle NULL | 多數欄位 | `OFD251A.DOC_NID` 無對應買回書時 |
| **一個空白字元 `' '`** | `OFD272A.GET_COPY_DATE` / `GET_COPY_UID`、`OFD251A.DOC_ADATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:93-94`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:121` |
| .NET `string.Empty` | UI / Ctl 層的比較 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2084` |

**查 `OFD272A` 是否到件,三種寫法都要涵蓋**:`GET_COPY_DATE IS NULL OR TRIM(GET_COPY_DATE) IS NULL`。

## 附錄 D. 掃描母體與覆蓋率

覆蓋率工具 `atlas_scan.py --module OFD` 會拿 OFD 全部 550 支畫面來比,對單片沒有意義。以下是本片 24 支的逐支處置表。

| # | 畫面 | 處置 | 寫在哪 |
|---|---|---|---|
| 1 | `OFDM091` | 表格帶過 | §4.13 |
| 2 | `OFDM220` | 已寫(成對) | §4.10 |
| 3 | `OFDM221A` | **深寫** | §4.1、§4.3 |
| 4 | `OFDM231A` | **深寫** | §4.2、§4.3 |
| 5 | `OFDM232` | 已寫(成對) | §4.10 |
| 6 | `OFDM233` | 表格帶過 | §4.13 |
| 7 | `OFDM242` | **深寫** | §4.9 |
| 8 | `OFDM243A` | 表格帶過 | §4.13 |
| 9 | `OFDM264` | **深寫** | §4.4 |
| 10 | `OFDM270` | 表格帶過 | §4.13 |
| 11 | `OFDM271` | **深寫** | §4.8 |
| 12 | `OFDM281` | **深寫** | §4.5 |
| 13 | `OFDM284` | 表格帶過 | §4.13 |
| 14 | `OFDM285` | 表格帶過 | §4.13 |
| 15 | `OFDM286` | 表格帶過 | §4.13 |
| 16 | `OFDM297` | 表格帶過 | §4.13 |
| 17 | `OFDM300` | 表格帶過 | §4.13 |
| 18 | `OFDM301` | 表格帶過 | §4.13 |
| 19 | `OFDM302` | **深寫** | §4.11 |
| 20 | `OFDM321` | 表格帶過 | §4.13 |
| 21 | `OFDM331` | **深寫** | §4.6 |
| 22 | `OFDM337` | **深寫** | §4.7 |
| 23 | `OFDM344` | 表格帶過 | §4.13 |
| 24 | `OFDM361` | **深寫**(說明為何沒有主明細) | §4.12 |

**深寫 12 支、表格帶過 12 支,24 支全數處置,無遺漏。**

母體本身的兩個修正(寫給下一個做 OFD 其他片的人):

| 掃描器說 | 實際 | 影響 |
|---|---|---|
| `OFDM271` 主檔 `OFD724` | `xTableMapping` 有宣告,但程式不讀不寫;真正操作的是 `OFD272A` | 用母體算「`OFD724` 有幾個維護入口」會多算一個 |
| `OFDM361` 主檔 `—` | 正確,但原因是三層空類別,不是漏宣告 | 別去補假的 `xTableMapping` |

## 附錄 E. 讀本文時要注意的地方

以下每條:**缺陷 / 影響 / 錨點 / 嚴重度**。分成十二型,型號沿用前九篇的缺陷型錄。

### E-1 整代基底跑不動:七支畫面掛在未賦值的連線上

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `BasicEVAPO` 與 `MultiRowEVAPO` 的建構子把 `dbTA` / `dbPTPF` 的賦值整段註解,欄位停在 `null`;`Add` 第一行就 `dbTA.CreateConnection()` | 繼承它們的 7 支畫面(`OFDM242` `OFDM284` `OFDM285` `OFDM321` `OFDM331` `OFDM344` `OFDM361`)一按存檔就 `NullReferenceException`;`catch` 裡的 `tran.Rollback()` 對 null 再炸一次,真正的錯被蓋掉 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:167-175`、`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187-229`、`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:167-175` | **高** |
| `OFDM242_PO` 自己的 `m_db` 也被註解成 null,`GetMasterData` 直接 `m_db.CreateConnection()` | 查詢就炸,不用等到存檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:31-32`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:188` | **高** |
| `OFDM242_PO.BeforeApproveDelete` 是整段 **T-SQL 批次**:`DECLARE @FUND_ID VARCHAR(10)`、`DECLARE CURSOR` + `@@FETCH_STATUS`、參數型別用 `SqlDbType.NVarChar` | Oracle 完全不吃;就算連線修好也跑不了 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:63-131` | **高** |
| `OFDM242_PO` 查詢 SQL 用 `CONVERT(VARCHAR(10), …, 111)`、`@REDEM_DATE` 具名參數 | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1192`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:1233-1235` | 高 |
| `OFDM284` `OFDM321` `OFDM331` `OFDM344` 的 live SQL 仍用 SQL Server 方括號識別字 `[BMS001]` `[OFD286A]` `[LOG106]` `[OFD321]` `[OFD322]` `[OFD331]` `[OFD332]` `[OFD335]` `[OFD344]` | Oracle 會回 `ORA-00903 invalid table name` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:222`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:230`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:198` | **高** |

**這一組整體標「假設」。**依據就是上面五列(連線 null + 兩種方言殘留 + 從未被改成 Oracle 綁定語法), 而且這四支的 UI 層卡控仍然完整,代表使用者會走到存檔那一刻才失敗。 **驗證成本極低:在現場對 `OFDM321` 按一次查詢即可。**若實際可用,表示部署的 `TA.DataAccess.dll` 與 repo 內原始碼不同版 —— 那本身就是更嚴重的問題,也要記下來。

### E-2 Oracle 三值邏輯:`欄 <> '值'` 遇 NULL 靜默過濾

CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過,OFD8 也不例外。全部是**過濾(無提示)**。

| 位置 | 條件 | NULL 時會怎樣 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:277` | `(OFD272A.TRN_CD<>'3' OR (OFD272A.TRN_CD='3' AND OFD251A.DOC_NID<>'Y'))` | `DOC_NID` 是 left join 來的,**沒有對應買回書時必為 NULL** → 整條 UNKNOWN → 該筆缺件在「到件回復」清單上消失。同一行的註解還寫「DOC_NID可以是空白或N」,顯示作者只想到空白 | **高** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325` | `AND OFD251A.REDEM_PROC_CODE <> '3'` | 未結帳的買回書若 `REDEM_PROC_CODE` 為 NULL,會被當成「已結帳」排除 | 高 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` | `AND B.REDEM_PROC_CODE<>'3'` | 同上 | 高 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2418` | `AND ALLOT_CTL_CODE <> '0'` | 控制碼為 NULL 的過帳控制列被漏掉 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2955` | `AND BF_NATIONALITY <> '0001'` | 國籍未填的受益人被當成本國人排除 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2316` | `AND BF_NATIONALITY <> '0001'` | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3230` | `AND RSP_TYPE<>'2'` | 定期定額型別未填的契約被漏掉 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3254` | `AND RSP006A.RSP_TYPE <> '2'` | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:915` | `WHERE OFD651A.EC_REDEM_PCODE <> '4'` | 同上(該支本來就跑不動,見 E-1) | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM242_PO.cs:922` | `WHERE OFD656.EC_REDEM_PCODE <> '4'` | 同上 | 低 |

**同型但在 .NET 這一側的變形**:`DataTable.Select("欄<>''")`。ADO.NET 的運算式對 `DBNull` 同樣回 false,所以「有值就不可刪」的檢核對 NULL 欄位一律放行:

| 位置 | 條件 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2042` | `dt.Select("COMPARE_NO<>''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2066` | `dt.Select("REMIT_CTL_NO <> ''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1793` | `UIView.OFD272.Select("GET_COPY_DATE<>''")` | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:891` | `dt.Select("ALLOT_DATE <> '' ")` | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM231A.cs:2777` | `m_view.OFD272.Select("GET_COPY_UID<>''")` | 中 |

### E-3 成對畫面 / 成對路徑只改一邊

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`OFDM231A` 轉申購:新增走 156 行逐欄指派,修改只同步 1 個欄位** | 改了轉換的金額 / 日期 / 通路 / 業務員,它的影子申購明細 `OFD221A` 除 `FAVORED_REL_TYPE` 外全部留舊值 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1936-2105` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2110-2112` | **高** |
| 2 | `OFDM220` 的 `OFD303A` 更新在 2009 年從 `BeforeAdd` 改到 `AfterAdd`,`OFDM232` 沒跟 | 買回彙總在主檔寫入前就動控制檔;主檔失敗時控制檔已改 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:47-48` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:48` | 中 |
| 3 | 同一組 UPDATE,`OFDM220` 綁參數並寫 `UPDATEID` / `UPDATEDATE`,`OFDM232` 用 `string.Format` 串字串且不寫更新者 | 買回側的控制檔改動查不到誰改的;且字串串接 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM220_PO.cs:113-131` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM232_PO.cs:121-131` | 中 |
| 4 | `OFDM281` 的「已產生配息資料不得修改 / 刪除」:修改路徑硬化成 `Int32.TryParse`,刪除路徑仍是 `Convert.ToInt32` | 下拉為空時刪除路徑丟例外,修改路徑靜默放行 —— **兩種錯法** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:399` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:776` | 中 |
| 5 | `OFDM300` 用 `Convert.ToDecimal` 判斷匯率,`OFDM301` 用 `Convert.ToDouble` | 匯率是金額類欄位,`double` 有浮點誤差;兩支成對畫面行為不一致 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM300.cs:149` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM301.cs:153` | 中 |
| 6 | `OFDM221A` 刪除卡控:按鈕層用 `DataTable.Select` 運算式、列層用欄位直接比較 | 同一條規則兩種 NULL 行為(見 E-2) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2041-2071` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2078-2110` | 中 |
| 7 | `OFDM302` 刪除卡控同上:按鈕層 `Select("NAV_LOCK='…'")`、列層 `row.NAV_LOCK == …` | 同上 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:265` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:354` | 低 |
| 8 | `OFDM286` 的「同一基金僅可有一筆生效中資料」在新增列與修改列各寫一次 | 改一邊漏一邊 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:307` 對照 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM286.cs:328` | 低 |
| 9 | `OFDM221A` 與 `OFDB310` 對 `OFD272A` 的取數 SQL 幾乎逐字相同,分別維護 | 缺件查詢條件改一邊漏一邊 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:913-928` 對照 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB310_PO.cs:1025-1037` | 中 |

### E-4 手寫逐欄對應與漏欄

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM231A` 轉申購的 156 行手寫指派(`row220.*` 與 `row221.*`) | `OFD220A` 77 欄、`OFD221A` 125 欄,逐欄手抄;新增欄位時漏抄不會編譯失敗,也不會有任何提示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1936-2105` | **高** |
| 同上的修改分支 `FindByALLOT_NOALLOT_SRNO(row1.ALLOT_NO, 1)` 把 `ALLOT_SRNO` 寫死成 `1`,回傳值**沒有 null 檢查** | 轉申購明細若不是序號 1(或已被刪),下一行直接 `NullReferenceException` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2111-2112` | **高** |
| `OFDM331_PO.BeforeAdd` 建了三個明細 row 卻從未 `Add*Row`,`COMPLAIN_NO` 設在孤兒物件上;被註解掉的舊版反而會重新指向 `Rows[0]` 且處理四張明細 | **假設**:新客訴的明細鍵拿不到主檔序號 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:103-105`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:135-140`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:459-474` | **高** |
| `OFDM221A` 的明細取數靠 `LoadDataSet` 的 7 個表名參數與 SQL 段落順序對齊 | 加一張明細要同時改三處,少改一處會把資料灌到錯的 DataTable | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:127-136` | 中 |

### E-5 字串串接進 SQL

本片 12 支 PO 共用同一段查詢條件樣板,**欄位名與值都來自用戶端、都沒有綁參數**:

```
strSQL += " And <表名>." + Row.Name + " = " + "'" + Row.Value + "'";
strSQL += " And <表名>." + Row.Name + " Like " + "'" + Row.Value + "%'";
```

| 畫面 | 錨點(首見) | 嚴重度 |
|---|---|---|
| `OFDM091` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM091_PO.cs:134` | 高 |
| `OFDM233` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:149` | 高 |
| `OFDM243A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM243A_PO.cs:168` | 高 |
| `OFDM264` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM264_PO.cs:237` | 高 |
| `OFDM281` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM281_PO.cs:164` | 高 |
| `OFDM284` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:222` | 高 |
| `OFDM297` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM297_PO.cs:101` | 高 |
| `OFDM321` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM321_PO.cs:163` | 高 |
| `OFDM331` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:230` | 高 |
| `OFDM344` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:198` | 高 |

另有兩處是**執行面**(UPDATE)的字串串接,風險更高:

| 位置 | 內容 | 嚴重度 |
|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:92-113` | `UPDATE OFD272A SET GET_COPY_DATE=' ', …, TRN_MEMO='<使用者輸入>' WHERE TRN_CD='…' AND TRN_NO='…'`;只有 `TRN_MEMO` 走 `ConvertTo.OracleString` 跳脫,其餘直接串 | **高** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:128-151` | 同上,`GET_COPY_DATE` 直接串畫面輸入值 | **高** |

### E-6 一律回報成功 / 失敗訊息是空字串

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM271_PO.Execute` 五個失敗出口有四個回 `AddResultRow(false, 0, "")` | 使用者看到空白錯誤框,現場無從判斷是哪一步失敗 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:112`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:149`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:210`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:218`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:224` | **高** |
| `OFDM271_PO.Execute` 成功時回的筆數是 `Convert.ToInt32(j)`,`j` 是**最後一次 `ExecuteScalar` 的結果**,不是更新筆數;沒走到 `ExecuteScalar` 時 `j` 為 null → 回 0 筆但標記成功 | 「執行成功,0 筆」會被當成沒資料,其實可能更新了很多筆 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:205` | 中 |
| `OFDM271_PO.Execute` 內外兩層 `catch` 都會 `AddResultRow`,內層已經 rollback + 寫結果,外層再寫一次 | 同一次失敗回兩筆結果;上層只看 `Result[0]` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:207-226` | 中 |
| `OFDM221A` / `OFDM231A` 的 After 掛點共 **15 處** `throw new ApplicationException("")` —— 空訊息 | 跳號紀錄寫失敗時使用者看到空白錯誤;與 `architecture.md §3` 記的 `CASM001_PO` 同型 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2678-2741`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3953-4003` | 中 |
| `OFDM331_PO.BeforeAdd` 的 `catch` 吞掉例外後方法正常返回 | 取號失敗仍然往下 INSERT,`COMPLAIN_NO` 是空的 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:143-148` | **高** |
| 四支 Ctl 直接讀 `result.Util.Result[0]` 組成功訊息,沒檢查 `Count` | PO 沒塞 Result 就 `IndexOutOfRangeException`;與 `architecture.md §6` 記的 `CASM001_Ctl` 同型 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM221A_Ctl.cs:59`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM231A_Ctl.cs:61`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM270_Ctl.cs:49`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM337_Ctl.cs:53` | 中 |

### E-7 被註解掉但外殼還在的檢核與程式

| 位置 | 被註解的東西 | 影響 | 嚴重度 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:806` | 「此 推薦人 不存在該 通路代碼」檢核 | 推薦人與通路代碼的一致性不再檢查 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:1034` | 「交易方式為傳真時,需可傳真交易」檢核 | 同上 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2030-2038` | TDCC 來源原本是「詢問 + bypass」,現改為硬擋,舊分支整段留著 | 讀 code 會誤判可以 bypass | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:288`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM264.cs:356` | 「資料內容必填」「補位字元必填」 | 媒體檔格式可以留空欄位 | 中 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:389`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM281.cs:767` | 舊版「作業處理碼 不為尚未處理時,不得修改／刪除」 | 兩段都有 live 替代品,但訊息與行為都變了 | 低 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM302.cs:55` | 舊版「淨值日 不存在於 基金代碼[X] 之營業日」 | 有 live 替代品 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:2686-2691` | `AfterDelete` 裡回沖 `OFD303A` 的整段 | 刪除送審時不回沖控制檔,要等覆核刪除才回沖 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM233_PO.cs:307-466` | 整段舊 SQL Server 版 PO(160 行) | 死碼 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:390-806` | 整段舊 `Add` / `Select` override(415 行,**比 live 段還長**) | 死碼,且是正確版本(見 E-4) | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM344_PO.cs:250-459` | 整段舊 `Add` / `Select` override(209 行) | 死碼 | 低 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM284_PO.cs:39` | `MasterTable.Add(new TableMapping("LOG106", "LOG"))` | xsd 裡 `LOG` 這張表永遠是空的 | 中 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM270_PO.cs:40-42` | `AfterAdd` / `AfterUpdate` / `AfterUnDelete` 的訂閱 | 退郵戶新增後沒有後續動作 | 中 |

### E-8 寫死常數與位置取參數

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM231A` 用字面量 `'3'` 表示缺件種類「贖回轉換」,同一支的別處卻用 `TRN_CD.RedeemAndSwitch` | 代碼改值時只改常數會漏掉字面量 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1173` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:119` | 中 |
| `OFDM271` 同一支裡兩種寫法並存:`TRN_CD.RedeemAndSwitch` 與字面量 `'3'` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:172` 對照 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:178`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:191` | 中 |
| `REDEM_PROC_CODE == "3"`(已結帳)三處字面量,**全庫沒有對應的常數類別** | 無處可改,改值要 grep 全庫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3522`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1325`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:1445` | 中 |
| `OFDM221A` 的缺件查詢寫死 `SHORE_ID = '2'`(境內)〔客戶特定〕 | 這支永遠只看境內基金缺件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:924` | 中 |
| `FindByALLOT_NOALLOT_SRNO(…, 1)` 寫死序號 `1` | 見 E-4 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:2111` | 高 |
| `OFDM242` / `OFDM302` / `OFDM321` 的訊息字串直接寫入別的畫面代號(`OFDB757` `OFDM114` `OFDM087`) | 代號變更時訊息會誤導 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:516`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM242.cs:523`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM221A.cs:2025` | 低 |

### E-9 無上限重試與死碼

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 四支畫面的取號 `do { 取號 } while (已存在)` **沒有次數上限** | 撞號情境或判斷恆真時變成無窮迴圈,卡住整條遠端執行緒(與 `architecture.md §3` 記的 `CASM001_PO` 同型) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:173-176`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3501-3504`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM337_PO.cs:119-129`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:130-133` | 中 |
| `OFDM221A_PO.BeforeAdd` 建了 `EVAUtility util` 從未使用(建構子還會產生一顆 Guid) | 死碼 + 每次新增多一次無謂配置;讀者會誤以為這裡有 EVA 處理 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:165` | 低 |
| 同一支的 `string bms001_dataid = string.Empty;` 宣告後從未使用 | 死碼;註解「Keep BMSM001 dataid」暗示曾有需求 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:160` | 低 |
| `OFDM361` 三層空類別 + 653 行 Designer + 兩份 655 行 xsd | 半成品進版控;`OFDM361_Ctl` 連 `BaseController` 都沒繼承 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM361_Ctl.cs:7-9`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM361_PO.cs:8-10` | 中 |
| `OFDM331_PO.BeforeAdd` 的條件 `row.COMPLAIN_NO != string.Empty \|\| row.COMPLAIN_NO != ""` 兩邊完全相同 | 邏輯上等於只寫一次;看得出原意是 null 檢查卻寫成同式 OR | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:118` | 低 |

### E-10 交易邊界被掛點打破

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM331_PO.BeforeAdd` 在 `Before*` 掛點裡直接 `args.DbTran.Rollback()` 然後 `throw` | 違反掛點規約(`architecture.md §3` 明載「不能自己 commit / rollback」);引擎外層會對已 rollback 的交易再 rollback 一次,真正的訊息被 `InvalidOperationException` 蓋掉 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:122-123` | **高** |
| `OFDM231A_PO.BeforeUpdate` 在主檔階段 **改動 `this.DetailTable`**(`Clear()` 後只加 `OFD272A`) | 已結帳的買回書按存檔,付款 / 轉換 / 沖銷 / 憑證的改動**靜默不寫入**,畫面仍回成功 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:3527-3528` | **高** |
| `OFDM271_PO.Execute` 自己 `BeginTransaction` / `Commit`,不在 EVA 交易內 | 到件登錄與上游交易不同一個交易;中途失敗時 `OFD251A` / `OFD607A` 的連動可能只做一半 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:65`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM271_PO.cs:204` | 中 |

### E-11 命名與檔案結構的陷阱

| 陷阱 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `OFDM242` 的 xsd DataTable 叫 `OFDM643` / `OFDM643_Detail` / `OFDM643_Chk`,而全庫沒有 `OFDM643` 這支畫面 | 用 `OFDM242` grep 找不到它的資料表;三層共 56 處引用 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM242Model.xsd`、`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM242_Ctl.cs:56` | 中 |
| `OFDM221A_PO` 的介面叫 `IOFDM221_PO`(少一個 `A`) | 用代號搜介面會漏 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:25` | 低 |
| `OFDM231A` 的意定代理人 vdb 叫 `OFD231A_AGENT`,實體表卻是 `OFD251A_AGENT` | 兩個名字差很多,對照時容易看錯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM231A_PO.cs:78` | 低 |
| `OFDM331` 的 `_K` 後綴在「客訴」與「處理」兩組裡語意相反(§2.1) | 改錯表 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM331_PO.cs:34-37` | 中 |
| `OFDM271` 代號是 `M` 但繼承 `xOneStepProcessForm`,行為是 B | 依型別碼分類權限 / 稽核時會分錯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM271.cs:28` | 中 |
| `OFD270A` 實體只有 2 欄,vdb 卻有 43 欄(41 欄是 join 來的) | 改畫面上的欄位改不到任何東西 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD8/OFDM270Model.xsd` | 中 |
| `OFDM264_Ctl` 自己定義私有的 `ExecPOActionToViewVDB`,不用基底版本 | 改 `BaseController` 不會影響它 | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM264_Ctl.cs:284` | 低 |
| 本片所有 `.cs` 實測皆為可解碼的 UTF-8,**無非 UTF-8 來源檔、無 null bytes** | (這一條是「查過沒問題」的紀錄) | — | — |

### E-12 讀這份文件本身要注意的

1. **行號是分析當下(2026-09-15)的版本。**動手前先用 `grep -n` 對一次。

2. **「跑不動」那七支是假設。**E-1 已經寫明驗證方法,不要當事實直接向客戶陳述。

3. **中文畫面名 24 支裡有 22 支是推測。**只有 `OFDM221A` 與 `OFDM302` 在程式註解裡有明確中文。

4. **本文只涵蓋 `DataEntity.OFD8` 這一片。**同一張表在 OFD 其他片可能還有主檔畫面與更強的卡控, `OFD220A` / `OFD221A` / `OFD251A` / `OFD724` 尤其明顯。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD8` 的 24 支 M 畫面、45 張實體表、3 個版控外 DB 物件;12 支深寫、12 支表格帶過;附錄 E 收 12 型共 60 餘條缺陷。 |

由 build_doc.py v2.0.0 於 2026-09-15 11:42 產生 · 標題 111 · 圖 5 · 表格 89 · 程式錨點 517 · § 連結 98 · 引用檢查：畫面 61（缺 0） · Table 54（缺 0） · 結果集 42（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
