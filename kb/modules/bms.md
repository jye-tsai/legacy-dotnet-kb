<!-- 由 tools/build_copilot_kb.py 從 modules/bms.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS BMS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先翻 §1 的圖抓全貌,再讀 §2 把 `CHG` 配對表的機制搞清楚(這是本模組最容易誤解的地方),之後 §3 的清冊配 §4 起的畫面章節就讀得動了。

> ⚠ **本模組的業務意義**(§0)由表名、欄位 `msdata:Caption`、`Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:56-67` 的常數與兩支 Trigger 的內容**推測**,待選單表回填。 ⚠ **〔客戶特定〕**:機構代碼(`'039'` 澳盛 / `'810'` 星展)、日期字面量(`'20171207'` / `'20171219'`)、外部檔案格式(星展 O 檔固定欄位位移)為本站台的值。 ⚠ **〔共用〕**:`OFD601` `OFD607A` `OFD374A` `OFD272A` `OFD206` 同時服務 OFD / DSM / RSP(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這個模組管什麼(推測)

**BMS = 受益人(Beneficiary)主檔與受益人資料變更**。三條證據:

| 證據 | 內容 | 錨點 |
|---|---|---|
| 常數字典直接寫出兩支畫面的角色 | `BMS_FUNC_NAME.New = "BMSM001"`(新戶)、`BMS_FUNC_NAME.Old = "BMSM006"`(舊戶) | `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:56-67` |
| 流水號字典把「受益人戶號」掛在 `BMS001A`、「受益人資料變更書號」掛在 `BMS001ACHG` | `SrNo.BfNo = "BMS001A"` / `SrNo.BfChangeNo = "BMS001ACHG"` | `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:53-84` |
| 兩支 Trigger 掛在 `BMS001A`,處理集保綜合帳戶與集保異動 Log | 見 `change-sp-fn-trigger.md §6.1`,本文不重述 | `DB/Trigger/BMS001A_TDCC_BF_NO.SQL:230`、`DB/Trigger/BMS001A_TSCDLOG.SQL:13-16` |

再往下拆,11 支畫面實際落在**四塊互不相干的業務**上:

| 塊 | 畫面 | 在管什麼(推測) |
|---|---|---|
| A 受益人開戶與資料變更 | `BMSM001` `BMSM004` `BMSM006` | 新戶建檔;受益人資料變更單的開單與內容維護 |
| B 專案註記 | `BMSM007` | 受益人掛在哪個專案(`PROJECT_CD`)、是否結案 |
| C FATCA / CRS 稅務遵循 | `BMSM924` `BMSM925` `BMSM926` `BMSM927` `BMSB925` | GIIN 與自我證明、CRS 盡職審查結果、CRS 匯率、高資產客戶名單 |
| D 一次性資料搬遷 | `BMSB901` `BMSB901A` | 匯款帳號整批換號;澳盛(`'039'`)轉星展(`'810'`)的印鑑與扣款帳戶搬遷 |

C 與 D 兩塊跟「受益人基本資料維護」只有 `BF_NO` / `ID_NO` 的關聯,**共用模組前綴而不是共用流程**。讀 BMS 的人如果預期整個模組是一條流程,會在 §4.5 之後完全對不上——先知道這件事比較省時間。

### 0.2 不管什麼

| 不在 BMS | 在哪 | 依據 |
|---|---|---|
| **把已覆核的變更單真正寫回 `BMS001A`** | OFD 模組的批次 `OFDB003`,呼叫 SP `s_TA_OFDB003_Excute` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:64` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:94` |
| 綜合帳戶集保戶號的產生與檢核碼 | 資料庫 Trigger | `DB/Trigger/BMS001A_TDCC_BF_NO.SQL:230` |
| 缺件主檔維護 | `OFDM221A` / `OFDM231A`(BMS 只寫 `OFD272A` 的 `TRN_CD='5'` 那批) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:531` |
| 受益人歸屬業務員維護 | `DSMM060`(`OFD374A` 的主檔在那裡) | 見 §8 |
| 定期定額扣款人主檔 | `RSPM004` / `RSPM005`(BMS 只讀 `OFD701` 做警示) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:593` |

### 0.3 使用角色

全部 8 支 M 畫面都走標準四眼(輸入 / 驗證 / 覆核),角色由平台的 ToDo 機制指派,BMS 自己不定義角色——所有 PO 都只是把 `xTableHelper.AppendToDoString(...)` 接到查詢字串尾巴(例:`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:175`)。詳見 `architecture.md §3`。

3 支 B 畫面(`BMSB901` `BMSB901A` `BMSB925`)繼承 `xOneStepProcessForm`(無原始碼,從呼叫端反推),**沒有四眼**:按下「執行」就直接改正式表。`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:22`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:22`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:28`。

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游 | EC(電子商務) | `BMSM006` 的「帶入 EC 資料」把 `OFD601` / `OFD607A` 的網路戶資料搬進變更單;覆核後寄歡迎信 `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:103-135` |
| 上游 | 星展銀行 O 檔(定長文字檔) | `BMSB901A` 以寫死的欄位位移解析 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:171-174`〔客戶特定〕 |
| 下游 | OFD 生效批次 `OFDB003` | 讀 `BMS001ACHG`,把 `AFT_*` 寫回本表並蓋 `CHG_UPD_DTTM` |
| 下游 | OFD 印鑑 / 扣款批次 `OFDB701` `OFDB702` `OFDB705` `OFDB707` `OFDB310` | 全部以 `NVL(BMS001ACHG.CHG_UPD_DTTM,' ') = ' '` 篩「尚未生效」的變更單 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:275` |
| 下游 | DSM | `OFD374A`(受益人歸屬業務員),主檔在 `DSMM060` |
| 旁支 | RSP(定期定額) | `BMSB901` / `BMSB901A` 直接 UPDATE / MERGE `RSP006A`、`RSP005A` |

### 0.5 全域開關

只有一個,而且**兩支畫面寫死成相反值**:

| 開關 | 位置 | 現值 | 效果 |
|---|---|---|---|
| `AUTO_BELONG_EMP` 是否把 `OFD374A` 掛成明細 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1912` | `bool IsAUTO = false;` | `BMSM001` **永遠不**載入歸屬業務員 |
| 同上 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2203-2214` | `bool IsAUTO = true;` | `BMSM006` **永遠**載入歸屬業務員 |

兩處的註解都寫「以 CTL015 判斷是否自動加業務員資料」(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:161`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:180`),但讀設定的那行已被註解掉,只剩一個寫死的布林。**這不是設定,是兩個方向相反的常數**。細節見 §8.3 與附錄 E7。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] BMS 四塊互不相干的業務:開戶與變更、專案註記、稅務遵循、一次性搬遷
圖中文字:A 受益人開戶與資料變更(四眼) / BMSM001 / 新戶 · 直接寫本表 / BMSM004 / 姓名統編變更單 / BMSM006 / 一般資料變更單 / BMS001A / 受益人主檔 / BMS001ACHG / 變更申請單 + 11 張配對表 / OFDB003 / OFD 生效批次 / B 專案註記 / BMSM007 / BMS007A · 專案與結案 / C FATCA 與 CRS 稅務遵循 / BMSM924 / BMS924 · GIIN / BMSM925 / BMS925A 自我證明 / BMSB925 / 產生 CRSDTL 母體 / BMSM927 / 匯率 / BMSM926 / CRSDTL 盡職審查 / D 一次性資料搬遷(無四眼) / BMSB901 / CSV 整批換匯款帳號 / BMSB901A / 星展 O 檔 印鑑搬遷 / RSP006A 等正式表 / 直接 UPDATE 或 MERGE
```

*圖:圖 1 全景。BMS 的 11 支畫面落在四塊彼此獨立的業務上,只有 A 塊是一條完整流程。橘色=開單或會改正式表的關鍵節點;黑箱=無原始碼或不在 BMS;注意 A 塊的回寫箭頭是 OFDB003 畫的,不是 BMS 自己畫的。*

### 1.2 資料表關係

`CHG` 配對表與本表的對應關係、主鍵串接方式,見下方插圖與 §2.1。一句話版:**`BF_CHG_NO`(受益人資料變更書號)是整組 `CHG` 表的共同主鍵頭**,`BMS001ACHG` 是單,其餘 `CHG` 表是單上的明細。

### 1.3 主要維護畫面的四眼與卡控順序

`BMSM006` 是全模組唯一會同時碰 12 張 `CHG` 表的畫面,它的四眼推進與 `CHG` 寫入時機見下方插圖與 §4.3。

### 1.4 批次資料流

3 支 B 畫面各走各的路:`BMSB901` 先塞暫存表再叫 SP、`BMSB901A` 全程在自己的 `_T1` / `_T2` / `_LOG` 三張暫存表上做 MERGE、`BMSB925` 只是 SP 的薄殼。見下方插圖與 §6。

### 1.5 跨模組影響

改 `OFD601` / `OFD607A` / `OFD374A` / `OFD272A` 會波及誰,見下方插圖與 §8。

## 2. 資料模型

```text
[圖] CHG 配對表與本表的對應,以及只有 OFDB003 能把值寫回本表
圖中文字:本表(正式資料) / BMS001A / 受益人主檔 / BMS004A / BMS005A / 授權帳號 / OFD130A / OFD131A / 配息帳號 / OFD137A / OFD138A / 停利買回 / OFD272A / 缺件 / 配對表 · 共同主鍵是變更書號 BF_CHG_NO / BMS001ACHG / 單頭 · BEF 與 AFT 成對 / BMS004ACHG / BMS005ACHG / OFD130ACHG / OFD131ACHG / OFD137ACHG / OFD138ACHG / OFD272ACHG / 生效:只有批次能把變更後的值寫回本表 / OFDB003 / s_TA_OFDB003_Excute / CHG_UPD_DTTM / 空 = 尚未生效 / BMS001A / 寫回的是開單當下的快照 / 例外 CRSDTLCHG / 無單號 · 覆核即回寫
```

*圖:圖 2 表關係。上下兩排是一一配對的本表與變更列,虛線箭頭代表「同一份業務資料的兩種形態」,不是外鍵。整組配對表靠變更書號串起來;`CRSDTLCHG` 名字像卻不屬於這套機制(§2.2 例外 1)。*

### 2.1 `CHG` 是什麼:12 張配對表的機制(本篇核心)

先給結論,再給證據。

> **`CHG` 表不是「四眼的異動暫存表」,也不是單純的「異動歷史 log」。它是一張「受益人資料變更申請單」**, 每一列同時帶著 `BEF_*`(變更前)與 `AFT_*`(變更後)兩份值,用 `BF_CHG_NO`(受益人資料變更書號)當單號, 帶生效日 `CHG_EFFECT_DATE`,**四眼是掛在這張單上的,不是掛在 `BMS001A` 上**。覆核通過之後資料**還不會進本表**;要等 OFD 模組的生效批次 `OFDB003` 跑, 由 SP `s_TA_OFDB003_Excute` 把 `AFT_*` 寫回本表並蓋上 `CHG_UPD_DTTM`。蓋了 `CHG_UPD_DTTM` 的單就退化成歷史資料,永久留在 `CHG` 表裡。

這解釋了 `architecture.md §3` 的一個矛盾:框架內的雙表四眼實作 `Basic4EyesPO` 是死碼(零繼承零實例化), 但 BMS 確實有成對的表 —— 因為這一套**完全是業務程式自己用 `BaseEVADaoPO` 手寫的**, 跟 `Basic4EyesPO` 的 `_Edit` 命名慣例毫無關係。

#### 證據鏈

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `BMSM006_PO` 的主檔就是 `BMS001ACHG`,不是 `BMS001A`;四眼事件全部掛在它身上 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:80-81` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:32-47` |
| 2 | 欄位成對:`BEF_ACC_NO_TYPE` 的 `msdata:Caption` 是「變更前帳戶種類」、`AFT_ACC_NO_TYPE` 是「變更後帳戶種類」 | `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd:3122-3129` |
| 3 | 開單時 `BMSM004_PO` 把 `BMS001A` 的現值**同時**填進 `BEF_*` 與 `AFT_*`,再由使用者改 `AFT_*` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:105-116` |
| 4 | 單號由 `SerialNo.GetBF_Change()` 取,撞號就重取 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:100-104` |
| 5 | `AfterApprove` **沒有**任何把 `AFT_*` 寫回 `BMS001A` 的 SQL,只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:984-1039` |
| 6 | 真正的回寫在 OFD 的生效批次:`s_TA_OFDB003_Excute` 吃 `CHG_EFFECT_DATE` / `CHG_DATE` / `BF_CHG_NO` 三個參數,訊息是「執行成功,共變更 N 筆受益人資料」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:64-78` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:124` |
| 7 | 「是否已生效」的判準全庫一致:`TRIM(CHG_UPD_DTTM) IS NULL` 代表尚未生效 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1363`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:781`、`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB701_PO.cs:275` |
| 8 | 生效前 `OFDB003` 會先數「還有幾筆沒覆核」,用 `Status NOT IN (SELECT Status FROM TABLE(f_TA_GetEVAStatus('A')))` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:315-318` |
| 9 | UI 直接用 `CHG_UPD_DTTM` 鎖按鈕,訊息是「資料已經生效,無法進行刪除」 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:495-501`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:541` |

**`s_TA_OFDB003_Excute` 的原始碼不在 repo**(`DB/SP/` 下沒有任何 BMS 或 OFDB003 相關檔案), 所以「回寫時到底把哪些 `AFT_*` 欄位搬到哪些本表欄位」這件事,**從 repo 無法確認**。本文把它標成 **〔假設〕缺:DB 連線** —— 結構上只能推到「`OFDB003` 負責回寫」為止。

#### 一張單的生命週期

| 階段 | 誰做 | `STATUS` | `CHG_UPD_DTTM` | 資料在哪 |
|---|---|---|---|---|
| 開單 | `BMSM004`(只改 ID / 姓名 / 缺件)或 `BMSM006`(改全部) | `Entry*` 系 | 空 | 只在 `CHG` 表 |
| 驗證 | `BMSM004` / `BMSM006` 的 Verify | `Verify*` 系 | 空 | 只在 `CHG` 表 |
| 覆核 | 同上的 Approve | `Approve*` 系 | **仍為空** | 只在 `CHG` 表 |
| 生效 | **`OFDB003` 批次** | 不變 | 被蓋上時戳 | 已寫回本表 |
| 歷史 | — | 不變 | 有值 | `CHG` 列變唯讀,UI 鎖住修改與刪除 |

`STATUS` 的值域見 `architecture.md §3.10`,本文不重述。

### 2.2 12 張 `CHG` 表與本表的配對

| `CHG` 表 | 本表 | 本表主檔畫面 | `CHG` 表的 PK(xsd `msdata:PrimaryKey`) | 在哪支畫面當明細 |
|---|---|---|---|---|
| `BMS001ACHG` | `BMS001A` | `BMSM001` | `BF_CHG_NO` | **主檔**(`BMSM004` 與 `BMSM006`) |
| `BMS004ACHG` | `BMS004A` | `BMSM001` | `BF_CHG_NO` | `BMSM006` |
| `BMS005ACHG` | `BMS005A` | `BMSM001` | `BF_CHG_NO`, `DATA_SEQ` | `BMSM006` |
| `OFD130ACHG` | `OFD130A` | `BMSM001` | `BF_CHG_NO` | `BMSM006` |
| `OFD131ACHG` | `OFD131A` | `BMSM001` | `BF_CHG_NO`, `DATA_SEQ` | `BMSM006` |
| `OFD132ACHG` | `OFD132A` | — | `BF_CHG_NO`, `DATA_SEQ` | `BMSM006` |
| `OFD137ACHG` | `OFD137A` | `BMSM001` | `BF_CHG_NO` | `BMSM006` |
| `OFD138ACHG` | `OFD138A` | `BMSM001` | `DATA_SEQ`, `BF_CHG_NO` | `BMSM006` |
| `OFD139ACHG` | `OFD139A` | `BMSM001` | `BF_CHG_NO`, `DATA_SEQ`, `BF_NO` | `BMSM006` |
| `OFD272ACHG` | `OFD272A` | `OFDM221A` 與 `OFDM231A` | `BF_CHG_NO`, `DATA_SEQ` | `BMSM006` |
| `OFD607ACHG` | `OFD607A` | — | `EC_BF_CHG_NO`, `DATA_SEQ`, `SYSTEM_ID` | `BMSM006` |
| `CRSDTLCHG` | `CRSDTL` | `BMSM926` | `BASE_DATE`, `BF_NO` | `BMSM926` |

PK 來源:`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd:12067-12340` 的 `xs:unique` 區塊、`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM004Model.xsd:2864-2880`、 `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM926Model.xsd:200-210`。

**兩個要特別記住的例外**:

1. **`CRSDTLCHG` 不屬於上面那套機制。** 它是 `BMSM926`(CRS 盡職審查)自己的「本次審查結果」表, PK 是 `BASE_DATE` 加 `BF_NO`,沒有 `BEF_*` 與 `AFT_*` 成對欄位,也沒有 `BF_CHG_NO`、沒有 `CHG_UPD_DTTM`。而且它**是唯一會在 `AfterApprove` 當場回寫本表的 `CHG` 表** —— 把 `CRSDTLCHG` 的 `DUE_DILIGENCE_CHK` 寫進 `CRSDTL` 的 `CRS_INDICATOR_M`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:92-119`)。名字長得像,機制完全不同。

2. **`OFD607ACHG` 的 PK 不含 `BF_CHG_NO`**,而是另一支 `EC_BF_CHG_NO`(EC 專屬變更書號,由 `SerialNo.GetEC_BF_CHG_NO()` 取, `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:582-592`)。`BF_CHG_NO` 只是它的一般欄位,由程式在 `BeforeUpdate` 回填 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:594-598`)。所以「同一張變更單」與「EC 異動列」是一對多,而且靠非 PK 欄位串起來。

### 2.3 表的主鍵與四眼欄位

母體列的 25 張表,逐一如下。「四眼」欄看的是 xsd 裡有沒有 `architecture.md §3.5` 那組 EVA 欄位。

| 表 | PK(來源 xsd) | 四眼欄位 | 母體列的欄位數 | 備註 |
|---|---|---|---|---|
| `BMS001ACHG` | `BF_CHG_NO` | 齊 | **0** | 欄位定義在 `BMSM001Model.xsd` 的 vdb 表 `BMS001CHG` 底下 |
| `BMS004ACHG` | `BF_CHG_NO` | 有 | **0** | vdb 名 `BMS004CHG` |
| `BMS005A` | `REMIT_CFM_NO`, `DATA_SEQ` | 無 | 3 | 母體只看到 `BMSM006` 用的三欄投影;`BMSB901` 另有一份定義 |
| `BMS005ACHG` | `BF_CHG_NO`, `DATA_SEQ` | 有 | **0** | vdb 名 `BMS005CHG` |
| `BMS007A` | `PROJECT_CD`, `BF_NO` | 有 | **0** | vdb 名 `BMS007` |
| `BMS924` | `BF_NO` | 有(只有 `*DATE` 進 xsd) | 55 | FATCA 與 GIIN |
| `BMS925A` | `IN_DATE`, `ID_NO` | 有(只有 `*DATE`) | 21 | CRS 自我證明主檔 |
| `BMS926A` | `IN_DATE`, `ID_NO`, `SRNO` | 有(只有 `*DATE`) | 9 | 無法取得稅籍編號的理由 |
| `BMS927A` | `IN_DATE`, `ID_NO`, `SRNO` | 有(只有 `*DATE`) | 19 | 控制人清單 |
| `CRSDTL` | `BASE_DATE`, `BF_NO` | 有 | **0** | vdb 名 `BMSM926` |
| `CRSDTLCHG` | `BASE_DATE`, `BF_NO` | 有 | **0** | vdb 名 `BMSM926CHG` |
| `OFD130ACHG` | `BF_CHG_NO` | 有 | **0** | vdb 名 `OFD130CHG` |
| `OFD131ACHG` | `BF_CHG_NO`, `DATA_SEQ` | 有 | **0** | vdb 名 `OFD131CHG` |
| `OFD132A` | `BF_NO`, `STATEMENT_CODE` | 有 | **0** | vdb 名 `OFD132` |
| `OFD132ACHG` | `BF_CHG_NO`, `DATA_SEQ` | 有 | **0** | vdb 名 `OFD132CHG` |
| `OFD137ACHG` | `BF_CHG_NO` | 只有 `*DATE` | 15 | 表名與 vdb 名相同,所以掃得到 |
| `OFD138ACHG` | `DATA_SEQ`, `BF_CHG_NO` | 只有 `*DATE` | 35 | 同上 |
| `OFD139ACHG` | `BF_CHG_NO`, `DATA_SEQ`, `BF_NO` | 只有 `*DATE` | 15 | 同上 |
| `OFD206` | `BF_SRNO`, `CAMPAIGN_CODE` | 只有 `*DATE` | 12 | 主檔在 `OFDM206` |
| `OFD272A` | `TRN_CD`, `SHORE_ID`, `ORG_COPY_CD`, `TRN_NO` | 有 | **0** | vdb 名 `OFD272`;`BMSM004` 另取名 `BMSM004_Lack` |
| `OFD272ACHG` | `BF_CHG_NO`, `DATA_SEQ` | 有 | **0** | vdb 名 `OFD272CHG` |
| `OFD374A` | `BF_NO` | **齊(唯一被母體判為 Y 的)** | 21 | 主檔在 `DSMM060` |
| `OFD601` | `BF_SRNO` | 只有 `*DATE` | 100 | 欄位數是跨 xsd 聯集,見下方警告 |
| `OFD607A` | `BF_SRNO` | 只有 `*DATE` | 50 | EC 網路戶 |
| `OFD607ACHG` | `EC_BF_CHG_NO`, `DATA_SEQ`, `SYSTEM_ID` | 有 | 71 |  |

> ⚠ **母體裡 13 張表顯示「欄位 0」,不等於「欄位定義不在 repo」。** `architecture.md 附錄 A` 說全庫有 208 張表(367 張裡的 57%)沒有任何 xsd 定義,**BMS 這 13 張不屬於那一類**。它們的欄位定義就在 `BMSM001Model.xsd` 裡,只是 **xsd 的 DataTable 名跟實體表名不同**: `new xTableMapping("BMS001ACHG", "BMS001CHG")`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:80`)。掃描器以實體表名去 xsd 找,自然找不到。要查 `BMS001ACHG` 的欄位,得去 `BMSM001Model.xsd` 找 `BMS001CHG`。對應表見附錄 A.2。**BMS 真正「repo 內查不到欄位」的只有批次用的四張暫存表** (`BMSB901_T1`、`BMSB901A_T1`、`BMSB901A_T2`、`BMSB901A_LOG`),它們只出現在 SQL 字串裡。

> ⚠ **`OFD601` 的「100 欄」有雜訊。** 這個數字是跨 xsd 的聯集,其中 `TagNumber` 與 `age` 兩欄來自 EC 模組的 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB610Model.xsd:1127`,在 BMS 側的 `BMSM001Model.xsd` 並不存在。拿這個欄位清單去改 `OFD601` 之前,先確認欄位屬於哪一份定義。

### 2.4 欄位中文名:只有一半的表填了 `msdata:Caption`

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。BMS 的實況:

| 表 | 中文名狀況 |
|---|---|
| `BMS924` / `BMS925A` / `BMS926A` / `BMS927A` / `OFD137ACHG` / `OFD138ACHG` / `OFD139ACHG` / `OFD206` / `OFD374A` | 業務欄大多有填 |
| `BMS001CHG`(即 `BMS001ACHG`)的**單頭欄位** | **全部沒填**:`BF_CHG_NO`、`BF_NO`、`CHG_DATE`、`CHG_EFFECT_DATE`、`CHG_UPD_DTTM`、`AUTO_NUM` 在 `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd:5472-5530` 都沒有 `msdata:Caption` |
| `BMS001CHG` 的 `BEF_*` 與 `AFT_*` 欄 | 零星有填,而且**成對的兩欄常常寫同一個中文名**:`AFT_MKT_ID` 與 `BEF_MKT_ID` 都叫「行銷身份別」(`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd:5495-5502`) |
| `OFD601` | 除了 EC 帶進來的兩欄,其餘 98 欄全空 |

「受益人資料變更書號」這幾個字是有出處的:`OFD138ACHG` 的 `BF_CHG_NO` 填了這個 Caption (`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd:11476`);`BMSM004Model.xsd` 的缺件表也填了「缺件種類」「缺件編號」「缺件代碼」「境內外基金識別碼」(`Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM004Model.xsd:957-994`)。本文用到的中文名一律出自這些 Caption。

### 2.5 三張沒有同名實體表的 vdb 表

`BMSM004Model.xsd` 有三張 DataTable,其中兩張不是實體表:

| vdb 表 | 實體表 | 用途 | 錨點 |
|---|---|---|---|
| `BMSM004` | `BMS001ACHG` | 變更單本體 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:38` |
| `BMSM004_Lack` | `OFD272A` | 只收 `SHORE_ID='2'` 且 `TRN_CD='5'` 的缺件列 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:39` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:531` |
| `BMSM004_Cer` | **無**,是 `BMS001A` 的即時快照 | 開單時把 `BMS001A` 現值撈進來,好填 `BEF_*` 與 `AFT_*` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:541-582` |

`BMSM004_Cer` 用 `xTableHelper.GetNonWhereSelectString(dbProduct, "BMS001A")` 再字串接 `AND BF_NO = <值>` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:554-556`)—— 這是附錄 E 要記一筆的字串串接。

### 2.6 狀態碼

BMS 沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`), BMS 只在三處直接比對:

| 比對 | 意義 | 錨點 |
|---|---|---|
| `STATUS == EVAStatusCode.VerifyDelete` | 「刪除待覆核」,按覆核鍵要走刪除流程而不是一般覆核 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:726-731`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:680-684` |
| `!strStatus.EndsWith("3")` | 「不是刪除類動作」(推測:狀態碼尾數 3 等於 Delete 系) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1474-1477` |
| `row.STATUS != "203"` | 覆核刪除的 EC 列不發歡迎信 | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:114` |
| 寫死 `STATUS ='201'` 到 `OFD601` | 覆核刪除受益人時把 EC 戶打回某個狀態 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3608-3613` |

第二、三條互相佐證:`"203"` 結尾是 `3`,語意是「覆核刪除」。**這與 `architecture.md §3.10` 的「單字元」推測不一致** —— BMS 給出的是三位數字面量。兩邊至少有一邊要修正,本文標**假設**,待 DB 或反編譯 `Vendor.Product.Utility.MappingCode` 確認。

## 3. 畫面清冊

全模組 11 支:B 3 支、M 8 支、**I 0 支、R 0 支**。

### 3.1 維護 M(8 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | 繼承 |
|---|---|---|---|---|---|---|
| `BMSM001` | 受益人開戶(新戶)(推測) | 齊 | `BMS001A` | `OFD132A` `BMS004A` `BMS005A` `OFD130A` `OFD131A` `OFD137A` `OFD138A` `OFD139A` `OFD272A` `OFD607A` `OFD601` `OFD206` | **無**(`s_ta_bms001_delec` 的呼叫已被註解,見附錄 E) | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM004` | 受益人姓名 ID 變更開單(推測) | 齊 | `BMS001ACHG` | `OFD272A` | — | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM006` | 受益人資料變更(舊戶)(推測) | **缺 model / view** | `BMS001ACHG`(查詢 / 維護)或 `BMS001A`(帶值) | 16 張,見 §4.3 | `s_TA_BMSM006_Get` | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM007` | 受益人專案註記(推測) | 齊 | `BMS007A` | — | — | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM924` | FATCA 與 GIIN 自我證明(推測) | 齊 | `BMS924` | — | — | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM925` | CRS 自我證明(推測) | 齊 | `BMS925A` | `BMS926A` `BMS927A` | — | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM926` | CRS 盡職審查結果(推測) | 齊 | `CRSDTL` | `CRSDTLCHG` | — | `BaseEVADaoPO` / `xMaintainForm` |
| `BMSM927` | CRS 匯率維護(推測) | 齊 | `CRSEXRATE` | —(多筆主檔) | — | **`BaseMultiRowEVADaoPO`** / `xMaintainForm` |

`BMSM927` 是全模組唯一的多筆主檔畫面:`this.MasterTable.Add(new xTableMapping("CRSEXRATE", "BMSM927"))` 加上 `this.MasterPKey.Add("BASE_DATE")`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:33-34`)。多筆與單筆的差別見 `architecture.md §3.9`。

### 3.2 查詢 I

**本模組無此類畫面。** 原因是查詢功能被併進 M 畫面的查詢頁:8 支 M 畫面全部繼承 `xMaintainForm`, 框架本身就給一個查詢頁(`this.TabPages = 2`,例:`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:28`), 每支都實作了 `Before…SearchButtonClicked` 把查詢條件塞進 `QueryVDB.Util.Parameters`。詳見 §5。

### 3.3 批次 B(3 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 讀 / 寫的表 | SP | 繼承 |
|---|---|---|---|---|---|
| `BMSB901` | 匯款帳號整批換號(推測) | 齊 | 寫 `BMSB901_T1`;更新 `BMS005A` `OFD610A` `RSP006A` | `S_TA_BMSB901_GET` | `xOneStepProcessForm`,PO 不繼承任何 EVA 基底 |
| `BMSB901A` | 澳盛轉星展印鑑與扣款帳戶搬遷(推測) | 齊 | 寫 `BMSB901A_T1` `BMSB901A_T2` `BMSB901A_LOG`;MERGE `RSP006A` `RSP005A`;讀 `BMS001A` | —(全部 inline SQL) | 同上 |
| `BMSB925` | CRS 高資產客戶名單產生與匯出(推測) | 齊 | 由 SP 決定;讀回 `CRSDTL01` / `CRSDTL02` 兩個結果集 | `S_TA_BMSB925_EXECUTE`、`S_TA_BMSB925_Get` | 同上 |

三支的 PO **都沒有繼承 `BaseEVADaoPO`**,而是自己宣告一個小介面再直接開 `Database dbTA = new Database("TA", DbServerType.Oracle)` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:37`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:37`、 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:34`)。這符合 `architecture.md §6.4` 說的「B 跟 I 是同一份程式碼」。

### 3.4 報表 R

**本模組無此類畫面,也沒有任何 `.rpt`。** 兩支需要輸出的畫面改用 Excel:

| 畫面 | 輸出方式 | 錨點 |
|---|---|---|
| `BMSB925` | `ExcelCreator.CreateExcelDocument(dt, sFileName)`,個人與法人各存一個 xlsx | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:120-127` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:148-155` |
| `BMSB901` | `DoExp1()` 只輸出一行 CSV 標題列當範本檔,不輸出資料 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:211-228` |

`BMSB925` 匯出前會把 `DataColumn.ColumnName` 整批改成 `Caption` (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:107-108`)—— 也就是 §2.4 說的 Caption 在這裡是**輸出檔的欄位標題**, 沒填 Caption 的欄位匯出後會是英文欄名。

### 3.5 一個不在清冊上的檔案:`BMSM006_1`

`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006_1.cs` 有 4,098 行,類別宣告是 `public partial class BMSM006_1 : BMSM001` (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006_1.cs:34`)。它是 `BMSM006` 的第二套實作,而且走的是**繼承** `BMSM001` 的路線, 跟現役的 `BMSM006`(`public partial class BMSM006 : xMaintainForm`,`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:33`)完全不同。

全 repo 除了它自己的兩個檔(`.cs` 與 `.Designer.cs`)以外,**沒有任何地方引用 `BMSM006_1`**。 `architecture.md §2.1` 說畫面代號固定 7 碼,`BMSM006_1` 是 9 碼,走不了標準的代號啟動路徑。 **假設**:這是一份沒刪掉的平行實作,現在是死碼。依據是零引用 + 代號不合鐵律;要否定這個假設只能查選單表。它與 `BMSM006` 的關係見附錄 E1。

## 4. 維護畫面(M)— 一支一節

```text
[圖] 受益人資料變更單從開單、驗證、覆核、OFDB003 生效到變成歷史的五個階段
圖中文字:① 開單(BMSM004 或 BMSM006) / 取變更書號 / SerialNo.GetBF_Change / 本表現值填入 / BEF 與 AFT 都填一樣 / 使用者只改 AFT / M004 三欄 / M006 全部 / 生效時戳是空的 / 資料只在 CHG 表 / ② 驗證 → ③ 覆核(四眼掛在單子上,不是掛在本表) / Verify / 只寫跳號註記 / Approve / 只寫跳號註記 / 生效時戳仍是空的 / 資料還是只在 CHG 表 / AfterApprove 不碰本表 / §2.1 的證據 5 / ④ 生效(OFD 的批次,不是 BMS) / OFDB003 排程 / 先數還有幾筆沒覆核 / s_TA_OFDB003_Excute / 原始碼不在 repo〔假設〕 / AFT 寫回 BMS001A / Trigger 也會跟著跑 / 蓋上生效時戳 / 單子變歷史 / ⑤ 歷史 / CHG 列永久保留 / UI 鎖住修改與刪除 / 風險 / 開單後本表仍可被 BMSM001 改,生效時被舊快照蓋回
```

*圖:圖 3 一張變更單的生命週期(本篇最重要的一張)。要記住的是第②③階段 —— 覆核通過資料仍然只在 CHG 表,本表沒有任何變化;真正動到本表的是第④階段的 OFD 批次。橘色虛框是兩個陷阱:寫回去的是開單當下的快照,而開單之後本表並沒有被鎖住(附錄 E15)。*

8 支 M 畫面分屬 §0.1 的四塊業務,**彼此不是一條流程**。先看一眼誰對誰:

| 畫面 | 誰按 | 開的是什麼單 | 改哪些欄位 | 覆核通過後資料進哪 |
|---|---|---|---|---|
| `BMSM001` | 開戶櫃台 | **沒有單**,直接建 `BMS001A` 正式資料 | 全部受益人欄位 | 覆核當下就在 `BMS001A` |
| `BMSM004` | 櫃台(姓名 / ID 變更) | `BMS001ACHG` 一張變更單 | 只有變更後統編 / 中文姓名 / 英文姓名 + 缺件 | **不進**,等 `OFDB003` |
| `BMSM006` | 櫃台(一般資料變更) | `BMS001ACHG` 一張變更單 + 11 張 `CHG` 明細 | 幾乎所有 `AFT_` 開頭的欄位 | **不進**,等 `OFDB003` |
| `BMSM007` | 專案人員 | 沒有單,直接建 `BMS007A` | 專案代碼 / 備註 / 是否結案 | 覆核當下 |
| `BMSM924` | 稅務遵循 | 沒有單,直接建 `BMS924` | GIIN 與 FATCA 欄位 | 覆核當下 |
| `BMSM925` | 稅務遵循 | 沒有單,直接建 `BMS925A` | 自我證明 + 兩張明細 | 覆核當下 |
| `BMSM926` | 稅務遵循 | 明細 `CRSDTLCHG` 是「本次審查結果」 | 盡職審查結果 | 覆核當下回寫 `CRSDTL` |
| `BMSM927` | 稅務遵循 | 沒有單,多筆主檔 `CRSEXRATE` | 基準日 + 各幣別匯率 | 覆核當下 |

**只有 `BMSM004` 與 `BMSM006` 是「開單」**,其餘 6 支都是直接維護正式表,覆核通過即生效。兩支開單畫面的差別是**能改的欄位範圍**,不是流程 —— 流程完全一樣(見 §2.1 的生命週期表)。

### 4.1 `BMSM001` 受益人開戶(新戶)(推測)

#### 4.1.1 用途與主 / 明細

全模組最大的一支(UI 8,448 行 / PO 4,081 行)。主檔 `BMS001A`,**`MasterTable` 是透過區域變數設定的** (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:85-86`),不是一行式的 `this.MasterTable = new xTableMapping(...)` —— 這就是母體 `docs/_candidates/bms.md` 的主檔欄空白的原因, 不是真的沒有主檔。明細的宣告在 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:100-158`, 其中 11 行被註解掉(`OFD101` 到 `OFD562` 那批),**掛上去的只有還活著的那幾張**。

> **本節寫成當時掃描器認不出這種寫法,現在認得了。**那個缺陷後來編號 D8 (`architecture.md 附錄 D.3` 第三輪),全庫共 6 張主檔、16 張明細受影響, `BMSM001` 與 `BMSM006` 各佔 8 張明細——是全庫受影響最重的兩支。重掃後索引記的是:**`BMSM001` 13 張明細** (`BMS004A` `BMS005A` `OFD130A` `OFD131A` `OFD132A` `OFD137A` `OFD138A` `OFD139A` `OFD206` `OFD272A` `OFD374A` `OFD601` `OFD607A`)、 **`BMSM006` 22 張**(上列同名的 `CHG` 版加上本表版)。其中 `OFD374A` 條件被寫死成 `false` 實際永遠不掛(見下段),所以**索引數字比實際掛上去的多一張**。

還有一張 `OFD374A` 走條件掛載,但條件被寫死成 `false`,實際永遠不掛 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1915`,見 §0.5 與附錄 E7)。

#### 4.1.2 誰開單、誰改什麼

`BMSM001` **不開單**。它直接寫 `BMS001A` 正式表,四眼掛在 `BMS001A` 自己的 EVA 欄位上。所以「新戶」這條線不會出現變更前 / 變更後成對欄位,也不需要等 `OFDB003`。

取號全在 `BeforeAdd`:

| 號 | 取法 | 條件 | 錨點 |
|---|---|---|---|
| 受益人戶號 | `genSrNo.GetBFNo()`,撞號或撞跳號註記就重取 | 使用者沒指定戶號時 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:732-739` |
| 同上(使用者指定) | 不取號,但撞號直接丟 `此戶號已使用，請重新指定` | 使用者指定了戶號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:740-741` |
| 法人分戶號 | `genSrNo.GetBMS001COR()` | 境外開戶且境外身分別為 `05` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:747-753` |
| 集保戶號 | `genSrNo.GetBMS001TDC()` 再過 `GetTSCD_BF_NO` 補檢核碼 | 境外開戶且原本沒有集保戶號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:755-767` |
| EC 自動編號 | `genSrNo.GetAUTO_NUM()`,**無條件取** | 永遠 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:772-774` |

`BeforeUpdate` 只做 `GetNO` 加 `InsertOFD197` 加清舊 KYC,**境外開戶那整段被註解掉** (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:674-703`)—— 也就是**開戶之後才改成境外戶,這支不會補集保戶號**。這件事實際上由 Trigger `BMS001A_TDCC_BF_NO` 補,完整分析見 `change-sp-fn-trigger.md §6.1`。

#### 4.1.3 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 取五種號、寫密碼狀態(取自 `CTL014` 的 `082`)、`GetNO`、`InsertOFD197`、清舊 KYC | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:723-803` |
| `BeforeAdd`(明細) | `OFD206` 先清掉舊的 EC 優惠活動 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:792-802` |
| `AfterAdd` | 送印鑑審核 `SendAuditSeal`,再直接呼叫 `AfterUpdate` 的全部內容 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:256-263` |
| `AfterUpdate` | 流程別為一步完成時當場補 `Confirm`;把 `OFD601` 的受益人戶號從 0 換成新戶號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:265-317` |
| `BeforeUpdate` | `GetNO` / `InsertOFD197` / 清舊 KYC;第一張明細送印鑑審核;`OFD374A` 補業務部門 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:639-721` |
| `AfterVerify` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3554-3559` |
| `AfterApprove` | 見下表(本畫面最重的一段) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:319-637` |
| `BeforeApproveDelete` | 把 KYC 明細的 Row 清空,讓底層不刪 KYC | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:805-815` |
| `AfterApproveDelete` | 寫跳號註記、把 `OFD601` 打回戶號 0 與狀態 `201`、作廢舊印鑑 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3561-3645` |
| `AfterDelete` / `AfterUnDelete` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3539-3552` |
| `AfterReject` / `AfterResend` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3647-3659` |

`AfterApprove` 逐段:

| 段 | 動作 | 條件 | 錨點 |
|---|---|---|---|
| 1 | `OFD607A` 覆核時把處理旗標蓋成 `Y`;傳輸旗標為 `Y` 再補寫一筆 `OFD6072A` | 明細表為 `OFD607A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:321-323` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1560-1602` |
| 2 | 寫跳號註記,寫失敗丟例外 | 主檔 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:371-374` |
| 3 | `Confirm`:把 `BMS001A` 的確認者與確認時間補成覆核者與覆核時間;**更新筆數不是 1 就丟例外**(訊息是空字串) | 狀態尾碼不是 `3`(非刪除系) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1471-1500` |
| 4 | 該統編在 `BMS001A` 只有這一戶時,把 `OFD337A` 中戶號為 `-1` 的同名同統編列補上戶號 | 同上 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1502-1532` |
| 5 | **同步改名**:`OFD701` / `OFD706` / `RSP006A` / `RSP008A` / `RSP013A` 的扣款人姓名一起換成新姓名(以統編對應) | 主檔 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:401-533` |

第 5 段是本畫面對外影響最大的一塊:**改一個受益人姓名會一次動到 5 張別的模組的表**, 其中 `RSP013A` 還只挑「尚未生效」的定額變更單改 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:501-517`,判準與 §2.1 第 7 條同一條)。

#### 4.1.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | 開戶日期(起)(迄)必須皆填或皆不填、起不可大於迄 | 只填一邊 / 起大於迄 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:1030-1037` |
| 查詢 | 戶號(起)(迄)同上 | 同上 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:1038-1041` |
| 查詢 | 客戶統編 / 戶號 / 開戶日期必須擇一 | 三者皆空且非 ToDo 模式 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:1042-1046` |
| 新增 / 修改前 | 受益人本人、法定代理人一與二、負責人逐一查交易列管 | 命中列管 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:617-651` |
| 新增 / 修改前 | 國籍或出生地屬歐盟國家 | 屬歐盟 | 阻擋(`本公司暫不接受歐盟居民開戶 不可存檔!`) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4437-4445` |
| 新增 / 修改前 | 非本國籍或非本國出生地時,英文現行居住地必填 | 空白 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4425-4436` |
| 新增 / 修改前 | 共同持有人統編不得等於受益人統編 | 相同 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4585-4591` |
| 新增 / 修改前 | 出生日期不可大於開戶日、不可大於系統日 | 違反 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4455-4461` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4865-4872` |
| 新增 / 修改前 | 通知書寄發設定勾了 EMAIL 或開戶類別為網路客戶時,EMAIL 必填且格式要對 | 空白 / 格式錯 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4535-4550` |
| 新增 / 修改前 | 有配息帳號就必須填受益人扣繳類別 | 未填 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4636-4639` |
| 新增 / 修改前 | 通知書寄送方式與寄發碼要一致;有自動傳真就要勾傳真寄發碼 | 不一致 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4646-4680` |
| 新增 / 修改前 | 推薦人必須存在於該通路代碼 | 查不到 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:4560-4571` |
| 覆核前 | 狀態為「刪除待覆核」時改走刪除檢核 | 狀態為刪除待覆核 | 轉向(不是卡控) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:726-732` |
| 覆核前 | **正常開戶直接放行,不重跑欄位檢核**;只有簡易開戶才重跑 | 開戶註記為正常開戶 | 過濾(無提示) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:733-740` |
| 刪除前 | 已確認的資料直接取消動作,**沒有任何訊息** | 確認者欄位不為空 | 過濾(無提示) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:942-950` |
| 刪除前 | 有行銷身分別時提醒要去行銷群組系統調整 | 行銷身分別非空且非刪除待覆核 | 詢問(Yes 才繼續,並寫 ByPass 記錄) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:952-964` |
| 刪除前 | 已有交易資料不可刪除 | `IsHasTrans` 大於 0 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:976-989` |
| 存檔(伺服端) | 使用者指定的戶號已存在 | 撞號 | 阻擋(`此戶號已使用，請重新指定`) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:740-741` |
| 覆核(伺服端) | `Confirm` 更新筆數不等於 1 | 不等於 1 | 阻擋(但**例外訊息是空字串**,見附錄 E3) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1496-1498` |

「文件調閱」按鈕會把戶號帶去開 `OFDM053`(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM001.cs:8428-8441`); 沒填戶號只有一句警示,不是卡控。

### 4.2 `BMSM004` 受益人姓名與統編變更開單(推測)

#### 4.2.1 用途與主 / 明細

**這是「開單」畫面,而且只能改三件事**:客戶統編、中文姓名、英文姓名,外加開戶缺件。主檔就是變更單 `BMS001ACHG`,唯一明細是缺件 `OFD272A` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:39-40`)。查詢只撈來源別為 `1` 的單(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:495-496`)—— **這是一個會把資料濾掉而不提示的條件**,見 §5.2。

#### 4.2.2 誰開單、誰改什麼

開單全在 `BeforeAdd` 這一支方法裡(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:86-438`),順序是:

1. 用畫面上的戶號去撈 `BMS001A` 現值,放進不是實體表的暫存 DataTable `BMSM004_Cer` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:544-582`;取 SQL 用字串接條件,見附錄 E5)

2. 取變更書號:`SerialNo.GetBF_Change()`,撞號就重取(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:100-105`)

3. **把 `BMS001A` 的每一個欄位同時塞進變更前與變更後兩份**,長達 320 行的逐欄指派 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:108-434`)。三個關鍵欄位(統編 / 中文姓名 / 英文姓名) 只在使用者沒填時才覆蓋(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:110-119`)

4. 把缺件明細的交易編號全部改成剛取到的變更書號,讓缺件掛在這張單上 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:435-436`)

**使用者只改那三欄**,其餘變更後欄位一律等於變更前 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:511-528`)。這解釋了為什麼 `OFDB003` 生效時「整列搬回去」不會誤改其他欄位 ——〔假設〕依據是這裡的成對指派,SP 本身不在 repo。

#### 4.2.3 四眼各階段附加動作

八個 `After` 事件**做的事完全一樣**:呼叫 `SrNoCommentProcessor.AddCommentHistory` 寫一筆跳號一覽表, 差別只有傳進去的 `EVAType`;寫失敗一律 `throw new ApplicationException("")`(空訊息) (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:856-910`)。 **沒有任何一個階段把變更後的值寫回 `BMS001A`** —— 這是 §2.1 證據 5 的來源。

覆核或修改成功後,若統編或姓名真的被改過,寄一封「受益人姓名及ID變更作業通知信」 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:169-173`),信件內容是變更前後對照 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:558-570`)。

#### 4.2.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | 收件日期(起)(迄)必須皆填或皆不填、起不可大於迄 | 違反 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:108-111` |
| 查詢 | 戶號(起)(迄)同上 | 違反 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:112-115` |
| 查詢 | 收件日期 / 戶號 / 變異前後統編必須擇一填寫 | 全空且非 ToDo | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:116-120` |
| 挑受益人時 | 該戶號還有未生效的變更單 | 有 | 詢問(Yes 才繼續,寫 ByPass 記錄) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:656-676` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:773-800` |
| 挑受益人時 | 該統編存在 `OFD701`(有定期定額扣款人或約定扣款帳號) | 有 | 警示(按 OK 才繼續) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:678-697` |
| 新增 / 修改前 | 變更後的統編已經開過戶 | 已存在 | 詢問(Yes 才繼續) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:699-719` |
| 新增 / 修改前 | 變更後統編不符台灣身分證或統一編號邏輯 | 不符 | 詢問(No 就擋,Yes 寫 ByPass 記錄) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:369-382` |
| 新增 / 修改前 | 有變更前值就一定要有變更後值(三組欄位各查一次) | 缺 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:579-584` |
| 新增 / 修改前 | 三欄都沒改而且缺件也沒增減 | 都沒改 | 阻擋(`資料未變更`) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:586-602` |
| 新增 / 修改前 | 變更生效日期不可小於收件日期 | 小於 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:603-604` |
| 新增 / 修改前 | 收件日期必須是公司營業日 | 非營業日 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:605-607` |
| 新增 / 修改前 | 收件日期不可大於缺件的到件日期 | 大於 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:608-610` |
| 新增 / 修改前 | 中文姓名不可含特殊字元 | 含 | 警示(只提示,不擋) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:251-270` |
| 載入既有單 | 已生效的單鎖掉修改與刪除鍵 | 已生效 | 阻擋(按鈕 disable) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:211-216` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:500-504` |
| 載入既有單 | 缺件已有到件人員時鎖掉刪除鍵 | 有 | 阻擋(按鈕 disable) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:505-506` |

### 4.3 `BMSM006` 受益人資料變更(舊戶)(推測)

#### 4.3.1 用途與主 / 明細

全模組最複雜的一支:UI 8,026 行 / PO 2,844 行 / Control 5,801 行,而且六層缺 model 與 view (它**共用 `BMSM001` 的 typed DataSet**,結論在 §3.1)。它是 `BMSM004` 的超集:同樣開 `BMS001ACHG` 這張單,但明細掛了 11 張配對表加 `OFD601` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:80-117`),因此**幾乎所有受益人欄位都能改**。

這支 PO 有兩套 `Initial`,靠切換主檔在兩種形狀之間跳:

| 方法 | 主檔 | 明細 | 用途 | 錨點 |
|---|---|---|---|---|
| `Initial006` | `BMS001ACHG` | 11 張配對表加 `OFD607ACHG` 加 `OFD601`,旗標為真再加 `OFD272A` | 查詢 / 維護變更單 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:78-134` |
| `Initial` | `BMS001A` | 與 `BMSM001` 相同的那批正式表 | **「帶值」**:開新單時把現值撈進畫面 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:136-181` |

切換點在 `GetMaintainData`:參數沒有變更書號就走 `Initial`(帶值),有就走 `Initial006`(讀單) (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:857-877`)。 `Add` / `Update` / `Verify` / `Approve` / `Reject` / `Resend` / `Delete` 每一支都先呼叫 `ResetTable` 把形狀切回配對表 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:804-902` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1338-1348`)。 **漏掉任何一支就會寫錯表**,這是改這支 PO 時最容易踩的地方。

#### 4.3.2 誰開單、誰改什麼

`BeforeAdd`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:299-444`):

| 序 | 動作 | 條件 | 錨點 |
|---|---|---|---|
| 1 | 取變更書號,撞號重取 | 永遠 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:305-312` |
| 2 | `GetNO` 取各帳戶的授權書號 | 永遠 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:313-314` |
| 3 | 取 EC 自動編號 | **只有**全方位帳戶旗標有變,或原本是 `01` 型而被改掉時 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:316-323` |
| 4 | 有 EC 異動列而 `OFD601` 還沒有這一戶時,**用 `BMS001A` 的現值整列複製出一筆 `OFD601`**,註冊別設 `N`、來源設 `2` | EC 異動列存在且查不到網路戶流水號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:365-411` |
| 5 | 取 EC 專屬變更書號,再把網路戶流水號、變更書號、EC 變更書號回填到每一列 `OFD607ACHG` | EC 異動列存在 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:412-432` |

第 4 步是整個模組裡最隱晦的一段:**在 BMS 的變更單上按存檔,會在 EC 的 `OFD601` 生一筆新網路戶**。複製時對日期欄位做型別轉換、對國別欄位把字元 `0` 全部拿掉 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:391-400`)。這個取代是字面上的字串取代, `01` 會變成 `1`、`10` 也會變成 `1` ——〔假設〕原意是去前導零,但寫法會誤傷,見附錄 E9。

「帶入 EC 資料」按鈕(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:1089-1798`)是使用者主動按的: 用統編去 `EC_BF_NODataSrc` 找網路戶,把 `OFD601` 與 `OFD607A` 的資料整批搬進畫面的變更後欄位與明細; 成功後鎖住開戶類別欄位並寫一筆 ByPass 記錄(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:1784-1790`); 查無網路戶只提示「無符合資料」(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:1793-1796`)。

#### 4.3.3 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `Add` / `Update`(伺服端收尾) | 呼叫 SP `s_TA_BMSM006_Get` 數這張單有沒有欄位真的變了,**數到 0 就丟 `受益人資料未變動`** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:816-836` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1132-1142` |
| `AfterAdd` | 主檔送印鑑審核 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:637-643` |
| `AfterVerify` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:977-982` |
| `AfterApprove` | **只寫跳號註記**;回寫 EC 覆核者的那段整塊被註解 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:984-1039` |
| `Approve`(Control 層) | 覆核成功後對符合條件的 EC 異動列寄歡迎信 | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:101-143` |
| `AfterApproveDelete` | 寫跳號註記,並用一段 `BEGIN` 匿名區塊作廢舊印鑑 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1041-1076` |
| `AfterDelete` / `AfterUnDelete` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:963-975` |
| `AfterReject` / `AfterResend` | 只寫跳號註記 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1078-1090` |

寄歡迎信的條件(`Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:116-132`): 該列覆核者為空(第一次覆核)、異動別非空且不是 `D`、狀態不是 `203`, 再加上「異動別為 `A` 且註冊別為 `4` 且開戶進度為 `A0` 或 `B0`」或「開戶進度為 `B2`」。 **同一件事 `BMSM001` 的判斷不一樣**(註冊別比的是 `8`,而且前面那組條件被註解掉了), 見 `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs:136-157` 與附錄 E2。

#### 4.3.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢 | 開戶日期 / 境外開戶日期 / 收件日期 / 戶號的(起)(迄)成對與大小 | 違反 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:616-631` |
| 查詢 | 收件日期 / 客戶統編 / 戶號必須擇一填寫 | 全空且非 ToDo | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:632-636` |
| 挑受益人時 | 該戶號還有未生效的變更單 | 有 | 詢問 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:2440-2486` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1355-1380` |
| 新增 / 修改前 | 受益人本人與相關人查交易列管 | 命中 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:692-700` |
| 新增 / 修改前 | 客戶統編必填、收件日期必填 | 空 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:2806-2814` |
| 新增 / 修改前 | 變更資料異動說明必填 | 空 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3504-3506` |
| 新增 / 修改前 | 戶籍與通訊地址郵遞區號必填;非本國籍時英文現行居住地必填 | 空 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3446-3466` |
| 新增 / 修改前 | 同一受益人另有尚未生效的 EC 權限異動單 | 有 | 阻擋(`尚有新增電子交易權限異動申請未生效，不可存檔`) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3577-3583` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1387-1415` |
| 新增 / 修改前 | 變更生效日期不可小於收件日期 | 小於 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3585-3586` |
| 新增 / 修改前 | 收件日期必須是公司營業日 | 非營業日 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3601-3603` |
| 新增 / 修改前 | 收件日期不可大於缺件的到件日期 | 大於 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3599-3600` |
| 新增 / 修改前 | 由未註銷改成註銷時提醒先確認在途交易 | 狀態轉換成立且無其他錯誤 | 警示(不擋) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3605-3609` |
| 新增 / 修改前 | 密碼重發:尚未開 EC 戶 / 已停權 / 尚未發送 | 成立 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:1974-2057` |
| 存檔(伺服端) | 整張單沒有任何欄位變動 | SP 回 0 | 阻擋(`受益人資料未變動`) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1140-1141` |
| 覆核前 | **除了「刪除待覆核」轉向刪除流程以外,不做任何欄位檢核** | 一律 | 過濾(無提示) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:680-684` |

最後一條要特別記住:**`BMSM006` 的覆核鍵不會重跑欄位檢核**。輸入階段擋掉的東西, 如果在覆核前被別的管道改掉(例如 `OFD601` 的狀態變了),覆核不會再擋一次。 `BMSM001` 至少對簡易開戶還會重跑(§4.1.4),`BMSM006` 連那層都沒有。

### 4.4 `BMSM007` 受益人專案註記(推測)

#### 4.4.1 用途與主 / 明細

全模組最小的 M 畫面(PO 186 行 / UI 215 行),主檔 `BMS007A`,**沒有明細** (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:39`)。一列代表「某受益人被掛在某個專案底下」,欄位只有專案代碼、受益人戶號、備註、是否結案四個業務欄。

專案代碼的中文名來自 `COD006A` 裡分類為 `HO` 的那批代碼 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:116-123`),查詢時左外接帶出說明; 受益人姓名與統編由 `BMS001A` 左外接帶出(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:119-120`)。

#### 4.4.2 誰開單、誰改什麼

不開單。使用者在畫面上挑專案代碼與受益人(統編與戶號互相帶值, `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:110-143`),填備註與結案勾選,存檔直接寫 `BMS007A`。修改模式下專案代碼、統編、戶號三個欄位變唯讀 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:53-60`)—— **要換專案只能刪掉重開**。

#### 4.4.3 四眼各階段附加動作

**一個都沒有。** PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三支, 而且三支的內容一模一樣,都是呼叫同一個 `BuildMasterSQLString` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:55-91`)。四眼流程完全交給框架。

一個要注意的細節:三支都傳 `false` 給 `isToDoString`,連 `BeforeGetToDoData` 也一樣 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:86-90`),所以 ToDo 專用的 `xTableHelper.AppendToDoString` 那段(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:172-177`) **永遠不會被接上去**。這是附錄 E8 的一筆。

#### 4.4.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 只有 `validatorManager1` 的宣告式必填檢核 | 必填欄位空白 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:159-164` |
| 查詢 | 三個條件(專案代碼 / 戶號 / 統編)有填才進 SQL,**全空就整表撈** | 全空 | 過濾(無提示,反向:不過濾) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:94-100` |

**沒有任何業務卡控。** 同一個受益人可以被重複掛進不同專案,靠主鍵(專案代碼加戶號)擋重複而已。

### 4.5 `BMSM924` FATCA 與 GIIN 自我證明(推測)

#### 4.5.1 用途與主 / 明細

主檔 `BMS924`,沒有明細(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:29`)。一列代表某受益人在某個開立日期的 FATCA 自我證明:FATCA 代碼、W 表別、GIIN 號碼與取得日、 W 表是否永久有效與到期日、同意與拒絕旗標,再加上**十組**外國稅籍資料(英文姓名 / 英文地址 / 稅籍編號) (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM924.cs:182-224`)。

那十組是**逐欄寫死的控制項對應**,不是明細 grid;要支援第十一組必須改 xsd 加欄位再改 UI,見附錄 E10。

#### 4.5.2 誰開單、誰改什麼

不開單,直接寫 `BMS924`。查詢條件只認戶號與開立日期兩個 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:109-136`),兩個都用 `Like` 或 `Equal`。主檔 SQL 是 `SELECT BMS924.*` 加 `JOIN BMS001A` 帶姓名 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:100-103`)—— 注意是 `JOIN` 不是 `LEFT JOIN`, **受益人主檔被刪掉的話,這裡的 FATCA 資料會整筆查不到**(過濾,無提示)。

#### 4.5.3 四眼各階段附加動作

**一個都沒有**,形狀與 `BMSM007` 完全相同:三支 `Before` 事件、同一支 `BuildMasterSQLString`、 `isToDoString` 一律傳 `false`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:45-82`)。

#### 4.5.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 只有 `validatorManager1` 的宣告式檢核;`DoValidate` 本身沒有任何業務規則 | 必填空白 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM924.cs:160-165` |
| 查詢 | 受益人主檔不存在時整筆查不到(內部 `JOIN`) | 主檔被刪 | 過濾(無提示) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:100-103` |

### 4.6 `BMSM925` CRS 自我證明(推測)

#### 4.6.1 用途與主 / 明細

主檔 `BMS925A`(以開立日期加統編為鍵),兩張明細: `BMS926A`(無法取得稅籍編號的理由)與 `BMS927A`(法人具控制權人清單) (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:37-39`)。

#### 4.6.2 誰開單、誰改什麼

不開單。使用者挑統編,畫面自動帶出姓名、出生日期、出生地、英文通訊地址與受益人境內外別 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:206-234`),再填 CRS 代碼、是否排除申報帳戶與排除原因, 兩張明細各自在 grid 上加列。

GIIN 號碼不是手key:按專用按鈕去 `BMS924` 撈該戶最新一筆 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:114-129` 的 `row_number()` 取最新)。 **這是 BMS 內部 CRS 與 FATCA 兩塊唯一的資料連結。**

#### 4.6.3 四眼各階段附加動作

**四個事件全是空殼。** `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` / `BeforeAdd` 各自只有一行 `strSQL = args.DbCmd.CommandText;`(註解直說是 for debug), 指派完就沒有下文(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:58-109`)。所以這支畫面的 SQL **完全由框架自動組**,PO 只是掛在那裡,見附錄 E8。

#### 4.6.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按 GIIN 帶入鍵 | 戶號必填 | 空 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:268-275` |
| 按 GIIN 帶入鍵 | 該戶在 `BMS924` 查不到 GIIN | 查不到 | 警示(**用原生 `MessageBox` 顯示英文 `No GiinNo Data`**,見附錄 E4) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:279-284` |
| 新增 / 修改前 | 勾了「是否為排除申報帳戶」就要填排除原因 | 沒填 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:299-304` |
| 新增 / 修改前 | 排除原因要與 CRS 代碼相符:`B2` 只能配 `1`、`B3` 只能配 `2` / `3` / `4`、`A1` 與 `A2` 只能配 `5` | 不符 | 阻擋(訊息有錯字,見附錄 E11) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:306-341` |
| 新增 / 修改前 | 受益人稅務身份(`BMS926A`)至少一列 | 零列 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:345-353` |
| 新增 / 修改前 | 境內外別為 `02` 或 `03` 時,法人具控制權人(`BMS927A`)至少一列 | 零列 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:354-357` |
| 輸入稅籍編號 | 長度要落在 `TA_COUNTRY_ISO` 裡該國的上下限之間;查不到該國就回「輸入的稅籍編號檢核有誤!」 | 不符 | 阻擋 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:155-205` |

那組 CRS 代碼與排除原因的對應是**寫死在 UI 的 if 串**,不是查表 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:310-335`);法規改了要改程式重新部署。

### 4.7 `BMSM926` CRS 盡職審查結果(推測)

#### 4.7.1 用途與主 / 明細

主檔 `CRSDTL`(以基準日加戶號為鍵,由批次 `BMSB925` 產生), 明細 `CRSDTLCHG`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:34-35`)。

**`CRSDTLCHG` 雖然叫 `CHG`,跟 §2.1 那套機制毫無關係**:沒有變更書號、沒有變更前後成對欄位、沒有生效時戳,它就是「這一期審查的人工判定結果」。§2.2 的例外 1 已經講過,這裡不重述。

#### 4.7.2 誰開單、誰改什麼

不開單。母體由批次產生,人工只在明細上填「盡職審查結果」與備註 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM926.cs:142-160`),一筆主檔對一筆明細。

#### 4.7.3 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `AfterApprove` | **覆核當場把明細的判定結果回寫主檔** `CRSDTL`,同時更新異動者與異動時間 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:93-118` |
| `BeforeApproveDelete` | **整支是空的**,只剩註解與被註解掉的程式碼 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:120-132` |

`AfterApprove` 是全模組唯一「覆核即回寫本表」的地方,判定值的四種語意 (`1` 無外國身分指標 / `2` 無外國稅務居民身分 / `3` 有外國稅務居民身分 / `4` 無資訊帳戶) 在查詢 SQL 裡用 `CASE` 寫死兩次 —— 主檔一份、明細一份 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:152-155` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:194-197`)。代碼值見附錄 C。

還有一個要留意的寫法:解構子 `~BMSM926_PO` 用的是 `+=` 而不是 `-=` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:37-45`),等於在物件要死的時候**又掛一次事件**。見附錄 E6。

#### 4.7.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 只有 `validatorManager1` 的宣告式檢核 | 必填空白 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM926.cs:197-201` |
| 載入既有資料 | 主檔標記為「無外國身分指標」時鎖掉修改鍵 | 標記為 `Y` | 阻擋(按鈕 disable) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM926.cs:76-80` |
| 新增載入 | 進新增模式時把新增 / 修改 / 刪除三個鍵全部關掉 | 一律 | 阻擋(按鈕 disable) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM926.cs:51-61` |

### 4.8 `BMSM927` CRS 匯率維護(推測)

#### 4.8.1 用途與主 / 明細

**全模組唯一的多筆主檔畫面**,繼承 `BaseMultiRowEVADaoPO`:主檔 `CRSEXRATE`, 主鍵只宣告基準日一欄(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:33-34`)。一個基準日底下有多列(每個幣別一列),四眼是**整組一起**推進的,單筆與多筆的差別見 `architecture.md §3.9`。

#### 4.8.2 誰開單、誰改什麼

不開單。使用者填一個基準日,再在 grid 上一列一列填幣別與匯率;存檔前程式把畫面上的基準日一次寫進每一列(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM927.cs:35-42`,註解直接寫「一定要這樣寫」)。

查詢與維護走兩段不同的 SQL:

| 用途 | SQL 形狀 | 錨點 |
|---|---|---|
| 查詢清單 | 用 `ROW_NUMBER() OVER (PARTITION BY BASE_DATE ...)` 每個基準日只取第一列,幣別塞空字串、匯率塞 `-1` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:55-76` |
| 進維護頁 | 撈該基準日的全部列 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:82-97` |

查詢那段的幣別與匯率是**假值**(`' '` 與 `-1`),純粹為了讓清單一個基準日只出現一列。看到清單上匯率是 `-1` 不是資料壞掉。

#### 4.8.3 四眼各階段附加動作

**一個都沒有。** 三支 `Before` 事件各自只呼叫對應的 SQL 組裝方法 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:100-115`),四眼推進整個交給 `BaseMultiRowEVADaoPO`。

#### 4.8.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | grid 至少要有一列 | 零列 | 阻擋(`明細資料 必須輸入`) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM927.cs:54-57` |
| 新增 / 修改前 | grid 每一列的主鍵欄位必填 | 缺 | 阻擋 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM927.cs:48-53` |
| 查詢 | 基準日只用「大於等於」比對,填了就只看那天以後 | 有填 | 過濾(無提示) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM927.cs:131-134` |

**沒有匯率合理性檢核**:匯率可以填 0 或負數,程式不擋。

## 5. 查詢畫面(I)

### 5.1 本模組無此類畫面

母體掃到 0 支 I 畫面(`docs/_candidates/bms.md` 第 1 節),讀完 8 支 M 畫面之後可以確認**這不是漏掃**: 查詢功能全部被併進 M 畫面的第一個頁籤。三個佐證:

| 佐證 | 內容 | 錨點 |
|---|---|---|
| 每支 M 畫面都宣告兩頁 | `this.TabPages = 2;`(查詢頁加維護頁) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM007.cs:26-35`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM926.cs:34-42` |
| 每支都實作查詢前事件,把條件塞進查詢用 VDB | `AddParametersRow(...)` | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:127-143`、`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM924.cs:104-112` |
| PO 端的 `BeforeSelect` 與 `BeforeGetMaintainData` 共用同一支 SQL 組裝 | 查詢與維護讀的是同一份語法 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:45-69` |

`architecture.md §6.3` 說 I 畫面的 PO 會退化成裸 DAO;BMS 這邊連退化的機會都沒有, 因為根本沒有獨立的 I 畫面。三支 B 畫面(§6)反而比較接近 I 的形狀 —— 它們的 PO 也不繼承任何 EVA 基底。

### 5.2 會把資料濾掉而不提示的條件

這一節是本章的重點。M 畫面的查詢頁有幾條**寫死在 SQL 裡、畫面上看不到、使用者也關不掉**的條件:

| 畫面 | 條件 | 後果 | 錨點 |
|---|---|---|---|
| `BMSM004` | 主檔固定加 `AND SOURCE_CD='1'` | **`BMSM006` 開的單在 `BMSM004` 查不到** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:495-496` |
| `BMSM006` | 主檔固定加 `AND BMS001ACHG.SOURCE_CD = '2'` | **`BMSM004` 開的單在 `BMSM006` 查不到** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1633-1634` |
| `BMSM004` | 明細固定加 `WHERE SHORE_ID= '2' AND TRN_CD='5'` | 只看得到境內開戶缺件,其他缺件種類看不到 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:531` |
| `BMSM004` | 查詢時**無條件**加一條姓名 `Like` 參數,即使畫面上姓名欄是空的 | 變更後中文姓名為 NULL 的單查不出來 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:141` |
| `BMSM924` | 主檔用內部 `JOIN BMS001A` | 受益人主檔被刪掉,FATCA 資料整筆消失 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:100-103` |
| `BMSM927` | 查詢清單用 `ROW_NUMBER()` 每個基準日只留第一列,且幣別與匯率被換成 `' '` 與 `-1` | 清單上看到的匯率不是真值 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:58-70` |
| `BMSM927` | 基準日只用「大於等於」比對 | 填了基準日就看不到更早的資料 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM927.cs:131-134` |

第一與第二條是這一節最要記住的:**`BMS001ACHG` 這張表被 `SOURCE_CD` 切成兩半**, `1` 是姓名與統編變更單(`BMSM004`)、`2` 是一般資料變更單(`BMSM006`)。兩支畫面各看各的一半,**任何一支都不會顯示完整的變更單清單**。要看全部只能下 SQL,或走 OFD 那邊的查詢畫面。

`BMSM001` 另外有三個**由畫面勾選才生效**的過濾,勾了才加條件,不算靜默過濾,但值得記一筆: 未成年(以 18 歲為界,寫死在 SQL 兩處)、非本國籍、姓名以英文字母開頭 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:829-837`)。年齡門檻寫死見附錄 E12。

### 5.3 查詢條件一覽

| 畫面 | 可查條件 | 錨點 |
|---|---|---|
| `BMSM001` | 統編、戶號(含起迄)、系統別、帳戶別、境內外別、姓名、國籍、開戶日期(起迄)、境外開戶日期(起迄)、三個勾選式過濾 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:838-839` |
| `BMSM004` | 變更書號、戶號(起迄)、變更前後統編、變更後姓名、收件日期(起迄)、變更生效日期 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:497-500` |
| `BMSM006` | 變更前統編、戶號(含起迄)、收件日期(起迄)、變更生效日期、變更前開戶日期(起迄) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1635-1638` |
| `BMSM007` | 專案代碼、戶號、統編 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:130-171` |
| `BMSM924` | 戶號、開立日期 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:109-136` |
| `BMSM925` | 戶號、開立日期 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:148-153` |
| `BMSM926` | 戶號、統編、基準日 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:163-165` |
| `BMSM927` | 基準日 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:71` |

`BMSM007` 與 `BMSM924` 的條件是**用字串串接**組進 SQL 的(`" And BMS007A." + Row.Name + " = '" + Row.Value + "'"`), 不是參數化,見附錄 E5 與 `architecture.md §4.3`。

## 6. 批次(B)與 WindowsService

```text
[圖] 三支批次各自的資料流:暫存表、SP 與最後寫入的正式表
圖中文字:BMSB901 匯款帳號整批換號 / 使用者 CSV / 5 欄 · 會靜默截斷 / BMSB901_T1 / 只 INSERT 不清 / S_TA_BMSB901_GET / SP 比出四個結果集 / BMS005A / OFD610A / RSP006A / 逐列 UPDATE / BMSB901A 澳盛轉星展〔客戶特定〕 / 星展 O 檔 / 定長 · 位移寫死 / BMSB901A_T1 與 _T2 / DELETE 不帶批號 / BMSB901A_LOG / 稽核軌跡 / RSP006A / RSP005A / MERGE 039 改 810 / BMSB925 CRS 高資產客戶名單 / 畫面參數 / 作業別與基準日 / S_TA_BMSB925_EXECUTE / 寫哪些表未知〔假設〕 / CRSDTL / BMSM926 的母體 / S_TA_BMSB925_Get / 兩個結果集 兩個 xlsx / 共同點:人工按鍵觸發 · 無四眼 · 直接改正式表
```

*圖:圖 4 批次資料流。三支各走各的路,唯一的共同點是都由人按鍵觸發而且沒有四眼。橘色虛框標的是會咬人的地方:CSV 靜默截斷、暫存表不清、DELETE 不帶批號(附錄 E14 與 E19)。*

三支 B 畫面**都不是排程跑的**,是人在畫面上按「執行」鍵跑的一次性作業; 三支的 PO 都不繼承 `BaseEVADaoPO`,而是自己 `new Database("TA", DbServerType.Oracle)` (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:37`、 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:37`、 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:35`),**沒有四眼**。本模組**沒有任何 WindowsService**(母體第 5 節為空)。

三支共用一組操作節奏:先按「查詢」預跑一次(`Select`),看結果無誤再按「執行」(`Execute`)。兩段是分開的交易,中間隔著使用者的判斷。

### 6.1 `BMSB901` 匯款帳號整批換號(推測)

| 項 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工:選 CSV 檔上傳 → 按查詢 → 按執行 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:148-209` |
| 輸入 | CSV 五欄:戶號、舊分行代碼、舊帳號、新分行代碼、新帳號 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:211-228` 的範本標題列 |
| 查詢階段寫哪 | 把每一列 `INSERT INTO BMSB901_T1`(自帶一個 `Guid` 當批號),然後呼叫 SP `S_TA_BMSB901_GET` 取回四個結果集 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:51-86` |
| 執行階段寫哪 | 逐列 `UPDATE`:`BMS005A`(授權帳號明細)、`OFD610A`(EC 匯款確認)、`RSP006A`(定額扣款) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:113-165` |
| 失敗處理 | 整段包在一個交易裡,任何例外就 `catch` 住不 rollback(靠 `using` 離開時自動回滾),結果列填「執行失敗，請檢查」 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:172-177` |
| 與 M 畫面的關係 | 無。它直接改正式表,不經過 `BMSM006` 的變更單,也不留跳號註記 | — |

**三個要注意的地方**:

1. `BMSB901_T1` **只 INSERT 不 DELETE**(對照 `BMSB901A` 每次都先清),資料靠批號區隔, 表會一直長大(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:51-75`)。

2. CSV 解析遇到欄數不足或戶號空白就 `break` 跳出迴圈,**不提示、不報錯**, 後面的資料整段被吃掉(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:165-168`)。過濾(無提示),見附錄 E19。

3. 查詢階段失敗時結果訊息被寫成空字串(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:93-98`), 使用者只會看到查無資料,不知道是出錯。

### 6.2 `BMSB901A` 澳盛轉星展印鑑與扣款帳戶搬遷(推測)〔客戶特定〕

這是一支**一次性資料搬遷**程式,整支寫死了機構代碼與日期,見下表。

| 項 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工:選星展 O 檔(定長文字檔)→ 按查詢 → 按執行 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:131-192` |
| 輸入格式 | 定長,靠寫死的位移切欄:分行代碼在第 13 位起 7 碼、帳號第 20 位起 16 碼、統編第 47 位起 11 碼、狀態碼第 74 位起 2 碼 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:169-172` |
| 尾筆檢查 | 長度不足 78 且以 `3` 開頭、長度剛好 46 的列視為尾筆,取第 37 位起 9 碼當筆數與實際筆數比對 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:151-167` |
| 查詢階段寫哪 | **先 `DELETE BMSB901A_T1` 與 `BMSB901A_T2`(沒有任何 WHERE)**,再把檔案內容寫進 `_T1`,以 `SUB_BANK_CODE = '039'` 比對 `RSP006A` 產生 `_T2` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:51-116` |
| 執行階段寫哪 | 先把要改的列存一份到 `BMSB901A_LOG`,再 `MERGE` 更新 `RSP006A`(分行代碼換成 `'810'`、核印方式 `'3'`、核印日 `'20171207'`、回件日 `'20171219'`),再 `MERGE` 更新 `RSP005A` 的備註,最後清掉兩張暫存表 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:138-204` |
| 失敗處理 | 寫 LOG 的筆數與 `MERGE` 的更新筆數不一致就中止並回「更新筆數不符」,交易不 commit | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:182-186` |
| 與 M 畫面的關係 | 無 | — |

〔客戶特定〕寫死值:來源機構 `'039'`、目的機構 `'810'`、核印日 `'20171207'`、回件日 `'20171219'`、備註文字「澳盛(039)由ACH票交所平台已改為星展(810)財金扣款平台;」 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:163-196`)。 **這支程式只對 2017 年那一次搬遷有意義**,現在跑會把日期蓋成 2017 年。

**併發風險**:批號是 Form 上的 `static` 欄位(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:23`), 而暫存表的 `DELETE` 沒有帶批號條件(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:51-56`)。 **兩個人同時跑,後按的人會把前一個人的暫存資料整個刪掉**,前一個人按執行時會查不到自己的資料。這是附錄 E14。

### 6.3 `BMSB925` CRS 高資產客戶名單產生與匯出(推測)

| 項 | 內容 | 錨點 |
|---|---|---|
| 觸發 | 人工:選作業別與基準日 → 按執行 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:58-84` |
| 輸入 | 作業別(產生 / 刪除,`D` 代表刪除)與基準日 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:71-82` |
| 寫哪些表 | **由 SP `S_TA_BMSB925_EXECUTE` 決定,repo 內查不到**。從 `BMSM926` 的主檔推測是寫 `CRSDTL` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:79-87` |
| 匯出 | 另一支 SP `S_TA_BMSB925_Get` 回兩個結果集(個人與法人),各存一個 xlsx | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:151-159` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:96-163` |
| 失敗處理 | SP 的輸出參數有訊息就 rollback 並把訊息原樣回給使用者;否則 commit | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:88-102` |
| 與 M 畫面的關係 | **產生 `BMSM926` 的母體**:先跑這支產出 `CRSDTL`,人工再到 `BMSM926` 逐筆填盡職審查結果 | — |

刪除作業有一道確認:作業別選到 `D` 時跳「是否確定要執行刪除?」,按 Yes 才送出 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:71-79`)。詢問類卡控,這是三支 B 畫面裡唯一的一道。

匯出前會把 DataColumn 的名字整批換成 Caption (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:110-111` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:137-138`), 所以 §2.4 說的「沒填 Caption 的欄位」在這裡會以英文欄名輸出到 Excel。

兩個缺陷:`catch (SqlException)` 這一段在 Oracle 環境**永遠不會被觸發** (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:114-120`,見附錄 E13); `DoValidate()` 的內容整個被註解掉但仍被呼叫(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:52-64`,見附錄 E8)。

### 6.4 三支批次的資料流對照

| 項 | `BMSB901` | `BMSB901A` | `BMSB925` |
|---|---|---|---|
| 輸入來源 | CSV(使用者自製) | 星展 O 檔(外部定長檔) | 畫面參數 |
| 暫存表 | `BMSB901_T1` | `BMSB901A_T1` / `BMSB901A_T2` / `BMSB901A_LOG` | 無 |
| 暫存表清理 | **不清** | 每次全清(不帶批號) | — |
| 主要邏輯在哪 | SP 加 C# 各一半 | **全部 inline SQL** | 全部在 SP |
| 寫入方式 | 逐列 `UPDATE` | `MERGE` | SP 內部 |
| 寫入的表 | `BMS005A` / `OFD610A` / `RSP006A` | `RSP006A` / `RSP005A` | 推測為 `CRSDTL` |
| 有沒有留稽核軌跡 | 沒有 | 有(`BMSB901A_LOG`) | 由 SP 決定,未知 |
| 可重跑嗎 | 可(冪等,改成同樣的新值) | 可,但會再寫一次 LOG | 有刪除作業別可先清 |

**四張暫存表的欄位定義不在 repo 內**(只出現在 SQL 字串裡),見 §2.3 的警告與附錄 A.3。

## 7. 報表(R)

### 7.1 本模組無 R 畫面,也沒有任何 rpt

母體掃到 0 支 R 畫面、0 個 `.rpt` 檔(`docs/_candidates/bms.md` 第 1 與第 4 節)。 `architecture.md §6.5` 說 R 畫面是命名鐵律的正式例外、報表另有 `.Report` 專案; BMS 連那個專案都沒有 —— `Dev/` 底下沒有 `ATLAS.BMS.Report`。

### 7.2 原因:兩支需要輸出的畫面都改用 Excel

| 畫面 | 輸出什麼 | 怎麼輸出 | 錨點 |
|---|---|---|---|
| `BMSB925` | CRS 高資產客戶名單,個人與法人各一個 xlsx | `ExcelCreator.CreateExcelDocument(dt, sFileName)`,由使用者挑存檔路徑 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:120-131` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:148-159` |
| `BMSB901` | **只有一行 CSV 標題列**,當作使用者填資料的範本檔,不輸出任何資料 | `StreamWriter` 直接寫字串 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:211-228` |

`BMSB925` 的 UI 檔頂端還留著被註解掉的 `using CrystalDecisions.CrystalReports.Engine;` (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:22`)——〔假設〕這支原本打算走 Crystal Reports, 後來改成 Excel;依據是那行註解加上全模組零個 `.rpt`。

其餘畫面的「輸出」都是把 grid 交給框架的匯出機制處理 (例:`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:200-205` 只是決定匯出哪一個 grid), 不算報表。

### 7.3 受益人相關的正式報表在哪

**不在 BMS。** 用 `atlas_scan.py --table` 反查 `BMS001A` 的使用者可以看到報表都掛在別的模組 (例 `Dev/ATLAS.NFD.Report/Source/PO/ReportPO.NFD/NFDR813_PO.cs` 用到 `OFD272A`)。要找「受益人基本資料表」這類報表,往 `ATLAS.OFD.Report` 與 `ATLAS.NFD.Report` 找,不要在 BMS 裡找。

## 8. 跨模組共用

```text
[圖] 四張共用表被哪些模組使用,以及改動時的守則
圖中文字:BMS 這一側 / BMSM001 / 明細掛 OFD601 與 OFD607A / BMSM006 / 明細掛 OFD607ACHG / BMSM004 / 明細掛 OFD272A / BMSM001 與 BMSM006 / 條件掛載 實際為 false / 四張共用表 / OFD601 / EC 網路戶主檔 / OFD607A / EC 交易權限 / OFD272A / 缺件 / OFD374A / 歸屬業務員 BMS 不掛 / 誰還在用(依 .cs 檔數) / EC 三個專案 共 40 檔 / OFD601 最高風險 / Common 共用資料源 / BasicEC_PO 等 / OFD 與 OFDB 與 OFDI / 批次與查詢 / DSM 與 RSP 與 NFD / DSMM060 是 OFD374A 主檔 / 改動守則 / 改欄位 / 兩邊 xsd 都要改 否則靜默失敗 / 改 OFD272A / 確認別的 TRN_CD 分區有沒有用到 / 改 OFD607A / 先確認 OFDB003 那段是否又打開
```

*圖:圖 5 跨模組影響。BMS 只是這四張表的使用者之一,`OFD601` 與 `OFD607A` 的主人是 EC、`OFD374A` 的主人是 DSM、`OFD272A` 的主人是 OFD。虛線箭頭代表那條掛載被寫死成 false,實際不成立(§8.3)。*

BMS 自有的表只有 9 張 `BMS` 開頭的(`BMS001ACHG` `BMS004ACHG` `BMS005A` `BMS005ACHG` `BMS007A` `BMS924` `BMS925A` `BMS926A` `BMS927A`),其餘 16 張是**借別的模組的表來當明細**。改這些表要先知道還有誰在用。

### 8.1 四張重點共用表的反查結果

以 `atlas_scan.py --table <表>` 反查,再用檔案層級的全 repo 搜尋補上索引沒收錄的引用:

| 表 | 主檔畫面 | 也在哪些模組出現(依 `.cs` 檔數) | 改動風險 |
|---|---|---|---|
| `OFD601` | **沒有主檔畫面** | EC 25 · EC.Query 15 · Common 15 · BMS 6 · OTA.Query 5 · OTA 3 · OFDI 3 · OFD 3 · EC.Report 2 · TMK 1 | 最高 |
| `OFD607A` | **沒有主檔畫面** | EC 18 · BMS 10 · Common 4 · EC.Query 3 · OFDB 2 · 其餘各 1 | 高 |
| `OFD374A` | `DSMM060` | OFDI 4 · DSM 3 · BMS 2 · RSP 1 | 中 |
| `OFD272A` | `OFDM221A` / `OFDM231A` | OFD 4 · BMS 3 · RSP 2 · OFDI 1 · OFDB 1 · OFD.Query 1 · NFD.Report 1 · Common 1 | 中 |

### 8.2 逐張說明

#### `OFD601` EC 網路戶主檔

**這張表的主人是 EC,不是 BMS。** BMS 只是在三個時機碰它:

| 時機 | 動作 | 錨點 |
|---|---|---|
| `BMSM001` 覆核 / 存檔後 | 把 `OFD601` 裡該統編、戶號還是 0 的那一列補上新戶號與 EC 自動編號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:275-311` |
| `BMSM001` 覆核刪除後 | 把戶號打回 0、狀態蓋成 `201` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3598-3624` |
| `BMSM006` 開單時 | 有 EC 異動列而 `OFD601` 沒有這一戶時,**整列複製 `BMS001A` 新增一筆** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:365-411` |

改 `OFD601` 的欄位要一起看的:EC 模組的一整排 `OFDB6xx` 批次 (例 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB610OracleDao.cs`)、 Common 的共用資料源(`Common/Source/DataSource/PO.DataSource/Basic/BasicEC_PO.cs`、 `Common/Source/DataSource/UI.DataSource/TableSrc/EC_BF_NODataSrc.cs`)、以及 OTA / OFDI / TMK 的查詢。 **特別注意 §2.3 的警告**:母體算出的 100 欄是跨 xsd 聯集,其中兩欄只存在於 EC 側的定義。

#### `OFD607A` EC 交易權限

BMS 這邊碰它的方式:

| 時機 | 動作 | 錨點 |
|---|---|---|
| `BMSM001` 覆核 | 把處理旗標蓋成 `Y`;傳輸旗標為 `Y` 時再補一筆 `OFD6072A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1560-1602` |
| `BMSM006` | 不直接改,改的是配對表 `OFD607ACHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:115` |
| `BMSM006` 帶入 EC 資料 | 讀回畫面 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:1312-1320` |

下游最重要的是 OFD 的生效批次 `OFDB003`:它原本也會更新 `OFD607A` 的密碼欄位, 但 2022-10-14 起整段被註解掉,理由寫在檔頭 (`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:26` 與 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:176`)。 **改 `OFD607A` 前先確認那段是不是又被打開了。**

#### `OFD374A` 受益人歸屬業務員

主檔在 DSM 的 `DSMM060`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:33`)。 BMS 這邊是**唯讀加條件掛載**,而且條件永遠為假(§8.3)。其他使用者:`OFDI011` 有一支 `CheckOFD374A` 專門檢查歸屬 (`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:5980-5994`), `RSPM004` 會直接 `INSERT OFD374A`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700`)。

**改 `OFD374A` 的欄位要同時改 `DSMM060` 的 xsd 與 `BMSM001Model.xsd`** —— BMS 側有一份自己的定義,兩邊不同步就會出現 `architecture.md §5.4` 講的那種靜默失敗。

#### `OFD272A` 缺件資料

主檔在 OFD 的 `OFDM221A` 與 `OFDM231A`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM221A_PO.cs:69`)。 BMS 只寫「境內開戶缺件」那一批(`SHORE_ID = '2'` 且 `TRN_CD = '5'`), 而且交易編號借用變更書號(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:435-436`)。其他使用者:`RSPM004` / `RSPM005` 也拿它當明細 (`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:80`)、 `OFDB310` 批次會讀(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB310_PO.cs:1025-1030`)、 `NFDR813` 報表會讀。

**這張表是靠 `TRN_CD` 分區使用的**:每個模組只認自己那個代碼,改欄位要確認別的 `TRN_CD` 分區有沒有用到。

### 8.3 `AUTO_BELONG_EMP`:一個開關寫成兩個相反的常數

`BMSM001` 與 `BMSM006` 各有一支同名方法,決定要不要把 `OFD374A` 掛成明細:

| 畫面 | 寫死的值 | 效果 | 錨點 |
|---|---|---|---|
| `BMSM001` | `bool IsAUTO = false;` | **永遠不**載入歸屬業務員,`BeforeAdd` 裡補業務部門那段也不會跑 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1915` |
| `BMSM006` | `bool IsAUTO = true;` | **永遠**載入 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2203-2214` |

兩處的原始註解都是「以 CTL015 判斷是否自動加業務員資料」 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:161`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:180`), 讀設定的那一行被註解掉,只留下註解裡的 `Convert.ToString(i) == YES_NO.Yes` 殘骸。

判設定的方法 `IsCheckCTL015` **六層全都還在**(PO / Control / FormProxy 各一份), 唯一的呼叫點在 `BMSM006` 而且被註解掉:

| 層 | 錨點 |
|---|---|
| PO | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3717` |
| Control | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs:907-911` |
| FormProxy | `Dev/ATLAS.BMS/Source/FormProxy/FormProxy.BMS/BMSM001_Pxy.cs:487-493` |
| 唯一呼叫點(已註解) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3774` |

**要恢復這個開關,四層都要改**;只把 `IsAUTO` 改成讀設定還不夠, 還要處理 `BMSM001` 的 `BeforeAdd` 拿錯表名的問題(附錄 E16)。

## 附錄 A. 資料表總表

### A.1 母體的 25 張表

配對關係與主鍵見 §2.2 與 §2.3,這裡只列歸屬與用途。

| 表 | 誰的 | 用途(推測) | 在 BMS 的角色 |
|---|---|---|---|
| `BMS001ACHG` | BMS | 受益人資料變更申請單 | `BMSM004` / `BMSM006` 的主檔 |
| `BMS004ACHG` | BMS | 授權帳號主檔的變更列 | `BMSM006` 明細 |
| `BMS005A` | BMS | 授權帳號明細 | `BMSM006` 明細;`BMSB901` 更新對象 |
| `BMS005ACHG` | BMS | 授權帳號明細的變更列 | `BMSM006` 明細 |
| `BMS007A` | BMS | 受益人專案註記 | `BMSM007` 主檔 |
| `BMS924` | BMS | FATCA 與 GIIN 自我證明 | `BMSM924` 主檔;`BMSM925` 取 GIIN |
| `BMS925A` | BMS | CRS 自我證明主檔 | `BMSM925` 主檔 |
| `BMS926A` | BMS | 無法取得稅籍編號的理由 | `BMSM925` 明細 |
| `BMS927A` | BMS | 法人具控制權人清單 | `BMSM925` 明細 |
| `CRSDTL` | BMS | CRS 盡職審查母體 | `BMSM926` 主檔;`BMSB925` 產生 |
| `CRSDTLCHG` | BMS | 本期審查判定結果 | `BMSM926` 明細 |
| `OFD130ACHG` | OFD | 配息帳號主檔的變更列 | `BMSM006` 明細 |
| `OFD131ACHG` | OFD | 配息帳號明細的變更列 | `BMSM006` 明細 |
| `OFD132A` | OFD | 通知書寄發途徑 | `BMSM001` / `BMSM006` 明細 |
| `OFD132ACHG` | OFD | 同上的變更列 | `BMSM006` 明細 |
| `OFD137ACHG` | OFD | 停利買回帳號主檔的變更列 | `BMSM006` 明細 |
| `OFD138ACHG` | OFD | 停利買回帳號明細的變更列 | `BMSM006` 明細 |
| `OFD139ACHG` | OFD | 資產證明資料的變更列 | `BMSM006` 明細 |
| `OFD206` | OFD | EC 優惠活動 | `BMSM001` 明細 |
| `OFD272A` | OFD | 缺件資料 | `BMSM001` / `BMSM004` / `BMSM006` 明細 |
| `OFD272ACHG` | OFD | 缺件的變更列 | `BMSM006` 明細 |
| `OFD374A` | DSM | 受益人歸屬業務員 | 條件掛載,實際不掛(§8.3) |
| `OFD601` | EC | 網路戶主檔 | `BMSM001` / `BMSM006` 明細 |
| `OFD607A` | EC | 網路戶交易權限 | `BMSM001` 明細 |
| `OFD607ACHG` | EC | 交易權限的變更列 | `BMSM006` 明細 |

### A.2 實體表名與 xsd DataTable 名的對照

§2.3 的警告說過:母體顯示「欄位 0」是因為 xsd 裡的 DataTable 名與實體表名不同, 掃描器以實體表名去找自然找不到。對照如下(來源:各 PO 的 `xTableMapping` 宣告)。

| 實體表 | xsd DataTable 名 | 錨點 |
|---|---|---|
| `BMS001A` | `BMS001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:85` |
| `BMS001ACHG` | `BMS001CHG`(`BMSM006`)/ `BMSM004`(`BMSM004`) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:80` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:39` |
| `BMS004ACHG` | `BMS004CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:82` |
| `BMS005ACHG` | `BMS005CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:83` |
| `BMS005A` | `TARemitConfirmDetail_O` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:86` |
| `BMS007A` | `BMS007` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:39` |
| `OFD130ACHG` | `OFD130CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:96` |
| `OFD131ACHG` | `OFD131CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:97` |
| `OFD132A` | `OFD132` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:100` |
| `OFD132ACHG` | `OFD132CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:98` |
| `OFD272A` | `OFD272`(`BMSM001` / `BMSM006`)/ `BMSM004_Lack`(`BMSM004`) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:147` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:40` |
| `OFD272ACHG` | `OFD272CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:100` |
| `OFD374A` | `OFD374` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1908` |
| `CRSDTL` | `BMSM926` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:34` |
| `CRSDTLCHG` | `BMSM926CHG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:35` |
| `CRSEXRATE` | `BMSM927` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:33` |

`OFD137ACHG` / `OFD138ACHG` / `OFD139ACHG` / `OFD607ACHG` / `BMS924` / `BMS925A` / `BMS926A` / `BMS927A` 的兩邊名字相同,所以掃得到欄位。

### A.3 母體之外、BMS 實際也會動到的表

這些表沒有出現在 `docs/_candidates/bms.md`,因為它們不是 `xTableMapping` 宣告的主 / 明細, 而是在 `After*` 事件裡用 inline SQL 直接改的。**做影響分析時不能漏掉這一張表**。

| 表 | BMS 對它做什麼 | 觸發畫面 | 錨點 |
|---|---|---|---|
| `BMS001A` | 建檔 / 更新 / 補確認者 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1471-1500` |
| `OFD337A` | 覆核時把戶號 `-1` 的列補上戶號 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1502-1532` |
| `OFD197A` | 開戶 / 更新時視行銷身分別補一筆 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1604-1620` |
| `OFD701` | 覆核時同步扣款人姓名 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:404-426` |
| `OFD706` | 同上 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:428-446` |
| `RSP006A` | 同上;`BMSB901` / `BMSB901A` 另會改帳號與印鑑 | `BMSM001` / `BMSB901` / `BMSB901A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:448-468` |
| `RSP008A` | 覆核時同步扣款人姓名 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:470-488` |
| `RSP013A` | 只改尚未生效的定額變更單上的姓名 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:501-533` |
| `RSP005A` | 加一段搬遷備註 | `BMSB901A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:188-197` |
| `OFD610A` | 換匯款帳號 | `BMSB901` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:131-147` |
| `OFD6072A` | 覆核時視傳輸旗標補一筆 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1584-1599` |
| `OFD624` / `OFD625` | 覆核刪除時**保留不刪**(把 Row 清掉讓底層跳過) | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:805-815` |
| `OFD041A` | 讀帳戶備註範本 | `BMSM006` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:906-928` |
| `COD009` | 讀業務員的部門代碼 | `BMSM001` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1886-1899` |
| `COD006A` | 讀專案代碼的中文說明 | `BMSM007` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:121-123` |
| `CRSEXRATE` | CRS 匯率主檔 | `BMSM927` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM927_PO.cs:33` |
| `TA_COUNTRY_ISO` | 讀各國稅籍編號的長度上下限 | `BMSM925` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:164-172` |

### A.4 四張只存在於 SQL 字串裡的暫存表

| 表 | 誰建的 | 欄位(從 `INSERT` 反推) | 清理 | 錨點 |
|---|---|---|---|---|
| `BMSB901_T1` | `BMSB901` | 批號、戶號、舊分行、舊帳號、新分行、新帳號 | **不清** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:56-62` |
| `BMSB901A_T1` | `BMSB901A` | 批號、統編、分行、帳號、印鑑狀態、狀態碼 | 每次全清 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:60-67` |
| `BMSB901A_T2` | `BMSB901A` | 批號、戶號、統編、姓名、定額編號、定額序號、扣款行、扣款帳號 | 每次全清 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:82-92` |
| `BMSB901A_LOG` | `BMSB901A` | 批號加更新前後的印鑑與機構欄位共 13 欄 | 不清(這是稽核軌跡) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:138-163` |

**這四張表的 DDL 不在 `DB/Table/`,也沒有 xsd。** 要改它們只能照著 SQL 字串裡的欄位順序推, 或連進資料庫看。〔假設〕缺:DB 連線。

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:只有兩支 Trigger

| 類 | 名稱 | 檔 | 行數 | 內容 |
|---|---|---|---|---|
| Trigger | `BMS001A_TDCC_BF_NO` | `DB/Trigger/BMS001A_TDCC_BF_NO.SQL` | 262 | 綜合帳戶開關切換時產生或清除集保戶號(含檢核碼);找不到集保總公司代號丟 `-20001` |
| Trigger | `BMS001A_TSCDLOG` | `DB/Trigger/BMS001A_TSCDLOG.SQL` | 82 | 綜合帳戶異動時寫一筆集保異動 Log |

兩支都掛在 `BMS001A` 上,完整分析在 `change-sp-fn-trigger.md §6.1`,本文不重述。要留意的是:**這兩支 Trigger 會在 `BMSM001` 與 `OFDB003` 兩條路徑上都被觸發** —— `OFDB003` 把變更單的值寫回 `BMS001A` 時,Trigger 一樣會跑。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

`DB/SP/` 與 `DB/Function/` 底下沒有任何 BMS 相關檔案(母體第 3 節為空表)。以下全部只看得到呼叫端。

| 類 | 名稱 | 誰呼叫 | 參數與回傳(從呼叫端反推) | 錨點 |
|---|---|---|---|---|
| SP | `S_TA_BMSB901_GET` | `BMSB901` | 吃批號;回四個 refcursor(授權帳號 / 定額 / EC 匯款 / 比對不到的) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:78-85` |
| SP | `S_TA_BMSB925_EXECUTE` | `BMSB925` | 吃作業別、基準日、異動者;回一個訊息字串,非空即代表失敗 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:79-91` |
| SP | `S_TA_BMSB925_Get` | `BMSB925` | 吃基準日;回兩個 refcursor(個人 / 法人) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:151-158` |
| SP | `s_TA_BMSM006_Get` | `BMSM006` | 吃變更書號;回一個 refcursor,只用其中的筆數欄位判斷「有沒有變動」 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1134-1141` |
| SP | `s_TA_OFDB003_Excute` | OFD 的 `OFDB003` | 吃生效日、變更日、變更書號;**把變更單寫回本表的就是它** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:64-78` |
| SP | `s_ta_bms001_delec` | `BMSM001`(**呼叫已註解**) | 原本吃網路戶流水號,刪 EC 資料 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3602-3604` |
| SP | `s_OFDR043_Get` | `BMSM006`(**呼叫已註解**,標示 debug 用) | — | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1145-1156` |
| Function | `F_TA_SPLITWORDS` | `BMSM004` 的 `AddParam` | 把逗號字串切成表,供 `IN` 條件用 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:716` |
| Function | `F_TA_GETAGENT` | `BMSM926` 的主檔查詢 | 回銷售機構清單,用來帶出機構簡稱 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:161` |
| Function | `f_TA_GetEVAStatus` | OFD 的 `OFDB003` | 回某個階段對應的狀態碼集合;`OFDB003` 用它數「還有幾筆沒覆核」 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:315-318` |

**View:本模組零支。**

`s_TA_OFDB003_Excute` 查不到原始碼這件事是本文最大的空白: 「哪些變更後欄位搬到本表的哪些欄位」只能推到「由它負責」為止,已在 §2.1 標〔假設〕缺:DB 連線。

## 附錄 C. 代碼對照

以下代碼值全部**從程式的字面量反推**,不是查代碼表得來的;中文語意取自程式裡的訊息或 `CASE` 敘述, 沒有訊息可佐證的標「推測」。

### C.1 變更單來源別

| 值 | 語意 | 依據 |
|---|---|---|
| `1` | 姓名與統編變更單(`BMSM004` 開的) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:495-496` |
| `2` | 一般資料變更單(`BMSM006` 開的) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1633-1634` |

### C.2 CRS 盡職審查結果

| 值 | 語意 | 依據 |
|---|---|---|
| `1` | 無外國身分指標 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:152-155` |
| `2` | 無外國稅務居民身分 | 同上 |
| `3` | 有外國稅務居民身分 | 同上 |
| `4` | 無資訊帳戶 | 同上 |

### C.3 CRS 代碼與排除申報原因的對應

| CRS 代碼 | 允許的排除原因 | 依據 |
|---|---|---|
| `B2` | `1` | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:310-317` |
| `B3` | `2` / `3` / `4` | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:319-326` |
| `A1` / `A2` | `5` | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:328-335` |

其餘 CRS 代碼不檢查(預設放行)。**這組對應寫死在 UI,不是查表。**

### C.4 其他在程式裡出現的字面量

| 欄位概念 | 值 | 語意(推測) | 依據 |
|---|---|---|---|
| 開戶型態 | `2` | 境外開戶 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:744` |
| 境外身分別 | `05` | 法人,要取法人分戶號 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:747-753` |
| 國籍 | `0001` | 本國籍 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:835` |
| 受益人境內外別 | `01` | 本國自然人 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:829` |
| 受益人境內外別 | `02` / `03` | 法人類,要填具控制權人 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:354-357` |
| EC 開戶進度 | `A0` / `B0` / `B2` | 會觸發歡迎信的三種進度 | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:120-121` |
| EC 異動別 | `A` / `D` / `U` | 新增 / 刪除 / 修改 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1397` |
| EC 註冊別 | `4` / `8` / `N` | 兩支畫面對「已開通」的判斷不一致,見附錄 E2 | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:120` 與 `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs:143` |
| 四眼狀態 | `201` | 覆核刪除後 `OFD601` 被打回的狀態 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3613` |
| 四眼狀態 | `203` | 覆核刪除(尾碼 `3` 為刪除系) | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:118` |
| 缺件 | `SHORE_ID = '2'` 加 `TRN_CD = '5'` | 境內開戶缺件 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:531` |
| 專案代碼分類 | `HO` | `COD006A` 裡專案代碼的分類 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:122` |
| 機構代碼〔客戶特定〕 | `039` / `810` | 澳盛 / 星展 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:174-178` |
| 核印方式〔客戶特定〕 | `3` | 搬遷後統一設定的核印方式 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:175` |
| 密碼狀態來源 | `CTL014` 的 `082` | 新戶預設密碼狀態 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:776-777` |

`STATUS` 的完整值域不在 BMS,見 `architecture.md §3.10`;§2.6 已經記下 BMS 給的三位數字面量與該節「單字元」推測不一致這件事。

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

`atlas_scan.py --module BMS` 的母體:畫面 11(B 3 / I 0 / M 8 / R 0)· 表 25 · SP 0 · Function 0 · Trigger 0 · View 0 · rpt 0 · Service 0。

| 類 | 母體 | 本文提及 | 覆蓋率 |
|---|---|---|---|
| 畫面 | 11 | 11 | 100% |
| 表 | 25 | 25 | 100% |
| SP / Fn / Trigger / View / rpt / Service | 0 | — | 不適用 |

畫面逐支落點:`BMSM001` §4.1 · `BMSM004` §4.2 · `BMSM006` §4.3 · `BMSM007` §4.4 · `BMSM924` §4.5 · `BMSM925` §4.6 · `BMSM926` §4.7 · `BMSM927` §4.8 · `BMSB901` §6.1 · `BMSB901A` §6.2 · `BMSB925` §6.3。表全部落在 §2.2 與 §2.3,附錄 A.1 再列一次歸屬。

### D.2 母體沒列到、但本文寫了的東西

母體是結構推測,以下是本文額外納入的,逐項交代來源:

| 項 | 來源 | 為什麼母體沒有 |
|---|---|---|
| `BMS001A` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:85-86` | 主檔是先指派給區域變數再掛上去,不是掃描器認得的一行式 |
| 附錄 A.3 的 16 張表 | 各 `After` 事件的 inline SQL | 不是 `xTableMapping` 宣告的主 / 明細 |
| 附錄 A.4 的 4 張暫存表 | 批次 PO 的 SQL 字串 | 只以字串形式存在,沒有 xsd 也沒有 DDL |
| 兩支 Trigger | `DB/Trigger/` | 掃描器把 Trigger 歸在 `BMS001A` 名下,而 `BMS001A` 不在母體表清單裡 |
| 十支 SP / Function | 各 PO 的呼叫端 | `DB/SP/` 與 `DB/Function/` 內沒有這些檔 |
| `BMSM006_1` | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006_1.cs:34` | 代號 9 碼,不符 7 碼鐵律,掃描器不認 |

### D.2.1 放進 meta `refcheck-ignore` 的名字

這些是**真實存在但索引收不到**的物件,不是本文編造的。放進 `refcheck-ignore` 只是讓引用檢查過關, 名字本身有程式出處:

| 名字 | 類 | 出處 | 索引收不到的原因 |
|---|---|---|---|
| `BMS004A` / `OFD130A` / `OFD131A` / `OFD041A` / `OFD6072A` | 表 | 各 PO 的 `xTableMapping` 或 inline SQL | 沒有 xsd 定義,也沒有同名 DataTable |
| `CTL015` | 設定表 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:161` 的註解 | 只出現在註解裡 |
| `BMSB901_T1` | 暫存表 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:56` | 只以 SQL 字串存在;名字長得像畫面代號,被誤判 |
| `BMSM006_1` | 畫面(死碼) | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006_1.cs:34` | 代號 9 碼 |
| 十支 SP 與 Function | DB 物件 | 附錄 B.2 | `DB/SP/` 與 `DB/Function/` 內沒有這些檔 |

### D.3 母體列了、本文交代不足的

**沒有。** 25 張表與 11 支畫面都有專節或專列。比較弱的是 `OFD601` 的 100 欄:本文只說明了 BMS 會動的那幾欄(戶號、EC 自動編號、狀態、註冊別), 其餘欄位屬於 EC 的職權範圍,不在本文範圍內(§8.2)。

### D.4 標〔假設〕的地方總表

| 項 | 假設內容 | 依據 | 要怎麼否證 |
|---|---|---|---|
| §2.1 | `s_TA_OFDB003_Excute` 把變更後欄位寫回本表 | 呼叫端的參數與訊息、`CHG_UPD_DTTM` 的用法 | 連 DB 看 SP 原始碼 |
| §2.6 | 狀態碼尾數 `3` 等於刪除系 | `203` 與 `!EndsWith("3")` 互相佐證 | 反編譯 `EVAStatusCode` 或查 DB |
| §3.5 | `BMSM006_1` 是沒刪掉的平行實作 | 零引用加代號 9 碼 | 查選單表 |
| §4.2.2 | 生效時整列搬回去不會誤改其他欄位 | 開單時變更前後成對指派、UI 只改三欄 | 同上,看 SP |
| §4.3.2 | 國別欄的字元取代原意是去前導零 | 只有這個解釋說得通;沒有註解 | 問原作者或查規格 |
| §7.2 | `BMSB925` 原本打算走 Crystal Reports | 被註解的 using 加全模組零個 rpt | 查版控歷史 |
| 附錄 A.4 | 四張暫存表的欄位順序 | `INSERT` 沒有欄位清單,只能照值的順序推 | 連 DB 看 DDL |
| 附錄 C | 全部代碼值的中文語意 | 程式訊息與 `CASE` 敘述 | 查代碼表 |
| §0.1 | 模組中文名與四塊業務的切分 | 常數字典、表名、Trigger 內容 | 查選單表 |

## 附錄 E. 讀本文時要注意的地方

嚴重度:**高**=會造成資料錯誤或作業中斷 · **中**=會誤導維護者或讓功能默默失效 · **低**=品質問題。

### E1 `BMSM006_1`:4,098 行的平行實作,零引用

| 項 | 內容 |
|---|---|
| 缺陷 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006_1.cs:34` 宣告 `BMSM006_1 : BMSM001`,是 `BMSM006` 的另一套實作,走繼承路線;現役的 `BMSM006` 走 `xMaintainForm`(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:33`) |
| 影響 | 搜尋 `BMSM006` 相關邏輯時會同時命中兩份程式碼,改錯邊完全沒有效果也不會編譯失敗 |
| 判別方式 | 檔名 9 碼;全 repo 除了它自己的兩個檔以外零引用 |
| 嚴重度 | 中 |

### E2 歡迎信的觸發條件有兩套,而且不一致

| 項 | 內容 |
|---|---|
| 缺陷 | `BMSM001` 判 EC 註冊別等於 `8`,`BMSM006` 判等於 `4`;`BMSM001` 那邊「第一次覆核且非覆核刪除」的前置條件被整段註解掉 |
| 錨點 | `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs:136-157` 與 `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM006_Ctl.cs:116-132` |
| 影響 | 同一個客戶走新戶或走變更單,收不收得到歡迎信不一樣;`BMSM001` 因為前置條件被拿掉,覆核刪除也可能發信 |
| 嚴重度 | 高 |

### E3 空訊息的例外:`throw new ApplicationException("")`

| 項 | 內容 |
|---|---|
| 缺陷 | 跳號註記寫失敗、`Confirm` 更新筆數不對,一律丟訊息為空字串的例外 |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1496-1498`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:867`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1037` |
| 影響 | 使用者只看到通用錯誤畫面,沒有任何線索;查問題只能翻 log |
| 出現次數 | `BMSM001_PO` 6 處、`BMSM004_PO` 8 處、`BMSM006_PO` 7 處 |
| 嚴重度 | 中 |

### E4 繞過框架對話框,用原生 `MessageBox` 顯示英文訊息

| 項 | 內容 |
|---|---|
| 缺陷 | `BMSM925` 查不到 GIIN 時跳 `MessageBox.Show("No GiinNo Data")`;上面兩行走框架的寫法被註解掉了 |
| 錨點 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:279-284` |
| 影響 | 樣式與其他訊息不一致、中文語系下出現英文、不會進 ByPass 記錄 |
| 嚴重度 | 低 |

### E5 SQL 用字串串接,沒有參數化

| 項 | 內容 |
|---|---|
| 缺陷 | 查詢條件直接串進 SQL:`" And BMS007A." + Row.Name + " = '" + Row.Value + "'"` |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:130-171`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:109-136`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:554-556`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1398` |
| 影響 | 值裡有單引號就語法錯誤;`architecture.md §4.3` 已經把這個當成全庫共通問題記過 |
| 嚴重度 | 中 |

### E6 解構子用 `+=` 而不是 `-=`

| 項 | 內容 |
|---|---|
| 缺陷 | `~BMSM926_PO()` 裡五個事件全部用 `+=`,等於在解構時又掛一次 |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:37-45` |
| 影響 | 同一份 PO 若被重複使用,事件可能被觸發多次;實務上 PO 是每次 new 一個,所以目前看不出症狀 |
| 嚴重度 | 低(但是一顆定時炸彈) |

### E7 `AUTO_BELONG_EMP`:設定變常數,而且兩支畫面方向相反

| 項 | 內容 |
|---|---|
| 缺陷 | 讀 `CTL015` 的那一行被註解,只剩 `bool IsAUTO = false;`(`BMSM001`)與 `= true;`(`BMSM006`) |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1915` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2203-2214` |
| 連帶 | 判設定的 `IsCheckCTL015` 六層都在,唯一呼叫點被註解(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3774`) |
| 影響 | 新戶不會載入歸屬業務員、舊戶變更會;要恢復開關得改四層 |
| 嚴重度 | 中 |

### E8 空殼:有事件沒內容、有檢核沒規則、有分支到不了

| 項 | 內容 | 錨點 |
|---|---|---|
| `BMSM925_PO` 的四支 `Before` 事件 | 各自只有一行 `strSQL = args.DbCmd.CommandText;`,指派完就結束(註解寫 for debug) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM925_PO.cs:58-109` |
| `BMSB925` 的 `DoValidate` | 內容整個被註解,但仍被呼叫 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:52-64` |
| `BMSM924` 的 `DoValidate` | 只有 `ValidateErrList.Clear()` 加框架檢核,末尾 `if (...) return;` 沒有作用 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM924.cs:160-165` |
| `BMSM007` / `BMSM924` 的 ToDo 語法 | `BeforeGetToDoData` 傳 `false` 給 `isToDoString`,`AppendToDoString` 那段永遠接不上 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM007_PO.cs:82-91` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM924_PO.cs:71-82` |
| `BMSM926` 的 `BeforeApproveDelete` | 整支只有註解 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM926_PO.cs:120-132` |
| `BMSM006` 的「請先帶入EC資料」檢核 | 條件與訊息都還在,整段被 `/* */` 包起來,只留下上面那行 `BMSM006_Pxy pxy` 給別的檢核用 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM006.cs:3562-3576` |

嚴重度:**中**。最後一條特別要注意 —— 註解外面還留著說明用的中文註解, 不細看會以為這條檢核還在跑。

### E9 國別欄的 `Replace("0","")`

| 項 | 內容 |
|---|---|
| 缺陷 | `BMSM006` 從 `BMS001A` 複製到 `OFD601` 時,對境內外別欄位做字面上的字元取代 |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:396-397` |
| 影響 | `01` 變 `1`(可能是原意),但 `10` 也會變 `1`、`20` 會變 `2`;若該欄位值域超過個位數就會對應錯 |
| 嚴重度 | 中(取決於該欄位的實際值域,repo 內查不到) |

### E10 `BMSM924` 的十組稅籍欄位逐欄寫死

| 項 | 內容 |
|---|---|
| 缺陷 | 外國稅籍資料(英文姓名 / 地址 / 稅籍編號)做成 10 組獨立欄位與控制項,不是明細表 |
| 錨點 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM924.cs:182-224` |
| 影響 | 客戶有第 11 個稅籍國就填不下,要改 xsd 加欄位、改 Designer、改 UI、改 DDL |
| 嚴重度 | 中 |

### E11 訊息錯字:「排捈」

| 項 | 內容 |
|---|---|
| 缺陷 | `請檢查[是否為排捈申報帳戶]欄設定是否正確!` —— 應為「排除」 |
| 錨點 | `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM925.cs:339` |
| 影響 | 只是錯字,但同一支檔案裡其他地方寫的是「排除」,搜尋訊息時會漏 |
| 嚴重度 | 低 |

### E12 未成年門檻 18 歲寫死在 SQL 裡,而且寫兩次

| 項 | 內容 |
|---|---|
| 缺陷 | 顯示欄位與過濾條件各寫一次 `DATEDIFF('Y', ...) >= 18` / `< 18` |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:829` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:831-832` |
| 影響 | 法定成年年齡改了要改兩處,漏改一處就出現「顯示已成年但被未成年過濾器撈出來」 |
| 嚴重度 | 中 |

### E13 `catch (SqlException)` 在 Oracle 環境永遠不會被觸發

| 項 | 內容 |
|---|---|
| 缺陷 | `BMSB925_PO` 用 `using System.Data.SqlClient;` 再 `catch (SqlException sqlex)`,但這支 PO 連的是 Oracle,丟出來的是 `OracleException` |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB925_PO.cs:114-120` |
| 影響 | 想給使用者看的資料庫原始錯誤訊息永遠走不到,一律掉進下面的通用 `catch` |
| 嚴重度 | 低(下面的 `catch` 有接,不會漏掉例外) |

### E14 `BMSB901A` 的暫存表清理沒帶批號,批號還是 `static`

| 項 | 內容 |
|---|---|
| 缺陷 | 查詢階段一開頭 `DELETE BMSB901A_T1; DELETE BMSB901A_T2;` **沒有 WHERE**;批號是 Form 的 `static` 欄位 |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901A_PO.cs:51-56` 與 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901A.cs:23` |
| 影響 | 兩個人同時操作,後按查詢的人會清掉前一個人的暫存資料;前一個人按執行會查無資料或更新筆數不符 |
| 嚴重度 | 高 |

### E15 `CHG` 與本表的欄位不同步:本文最會咬人的一條

這是整個模組風險最高的結構性問題,分兩層。

**第一層:欄位對應是手寫的,加欄位會漏。** `BMSM004` 開單時把 `BMS001A` 的值搬進變更單,是**逐欄手寫的 320 行指派** (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:108-434`),不是泛型複製。程式裡留著每次加欄位的痕跡:「2013/01/16 因BMS001CHG的欄位增加而調整程式」 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:413`)、「20151224 銷售地代號」 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:425-427`)、「20160129 全方位理財帳戶」 (`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM004_PO.cs:428-430`)。 **`BMS001A` 加一個欄位,這裡沒跟著加,變更單上那一欄就永遠是空的**; 生效時 `s_TA_OFDB003_Excute` 把空值寫回去,本表的值就被清掉 ——〔假設〕,取決於 SP 怎麼寫。

**第二層:開單之後本表沒有鎖。** `BMSM004` 與 `BMSM006` 開新單時會問「尚有未生效的受益人異動資料,是否新增?」 (`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSM004.cs:656-676`),但**`BMSM001` 完全不檢查 `BMS001ACHG`** (全檔沒有任何一處提到這張表)。所以這個順序是可能的:

1. 櫃台在 `BMSM006` 開一張變更單,生效日設在三天後;此時單上帶著今天的快照

2. 隔天有人用 `BMSM001` 直接改了 `BMS001A` 的電話

3. 第三天 `OFDB003` 跑,把變更單上**前天的快照**寫回 `BMS001A`

4. 昨天改的電話被蓋掉,而且**沒有任何警示或記錄**

第二層的推論鏈完全由程式碼支撐(步驟 1、2 有錨點;步驟 3 依賴 `s_TA_OFDB003_Excute` 的行為,標〔假設〕)。 **要驗證只需要看 SP 是不是「整列 `AFT_` 欄位無條件寫回」。** 如果是,這個情境一定會發生。

| 項 | 內容 |
|---|---|
| 嚴重度 | **高** |
| 建議的驗證動作 | 連 DB 撈 `s_TA_OFDB003_Excute` 原始碼,確認是整列覆蓋還是只寫有變動的欄位 |

### E16 表名比對用錯:`OFD374` 與 `OFD374A`

| 項 | 內容 |
|---|---|
| 缺陷 | `BeforeAdd` 比對 `args.TableName == "OFD374"`(這是 xsd 的 DataTable 名),`BeforeUpdate` 比對 `"OFD374A"`(實體表名);其他所有比對都用實體表名 |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:791` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:717-720` |
| 影響 | **新增歸屬業務員時不會補業務部門代碼與歸屬日期**,修改時才會補 |
| 目前看不出症狀的原因 | `BMSM001` 因為 E7 根本不掛 `OFD374A`,這條路徑跑不到;**一旦把 E7 的開關打開,這個 bug 就會現形** |
| 嚴重度 | 中(潛伏) |

### E17 `Check601BFNO` 整支被停用,而且 `throw` 後面還有不可到達的 `return`

| 項 | 內容 |
|---|---|
| 缺陷 | 方法還在,唯一呼叫點被註解;方法內 `throw new ApplicationException("戶號有誤，請聯絡資訊室人員");` 下一行是 `return true;` |
| 錨點 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1167-1192` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:604` |
| 影響 | 「更新 `OFD601` 前確認戶號」這道保護現在沒有在跑;§8.2 說的 `OFD601` 戶號覆寫因此沒有防線 |
| 嚴重度 | 中 |

### E18 `BMSM001_Ctl.cs` 是全模組唯一的 Big5 檔

| 項 | 內容 |
|---|---|
| 缺陷 | BMS 底下所有非 Designer 的 `.cs` 都是 UTF-8 with BOM,只有 `Dev/ATLAS.BMS/Source/Control/Control.BMS/BMSM001_Ctl.cs` 是 CP950 |
| 影響 | 用 UTF-8 開會看到亂碼中文註解;用一般文字工具批次取代會把整檔毀掉 |
| 怎麼確認 | 讀檔時指定 `cp950`;或用 `docs/tools/atlas_scan.py` 內的 `read_text` |
| 嚴重度 | 中(改這支檔案前一定要先確認編碼) |

### E19 `BMSB901` 的暫存表不清、CSV 靜默截斷

| 項 | 內容 |
|---|---|
| 缺陷 1 | `BMSB901_T1` 只 INSERT 從不 DELETE(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:51-75`) |
| 缺陷 2 | CSV 解析遇到欄數不足或戶號空白就 `break`,後面整段不讀也不提示(`Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB901.cs:165-168`) |
| 缺陷 3 | 查詢失敗時把結果訊息寫成空字串(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSB901_PO.cs:93-98`) |
| 影響 | 檔案中間有一列格式不對,後面幾百列被吃掉而使用者以為全做完了 |
| 嚴重度 | 高(缺陷 2) |

### E20 大量被註解掉、但外殼還在的程式碼

除了 E8 列的幾處,還有這些整段被註解的區塊。**共同特徵是註解與 `#region` 標題還在**, 不細看會誤以為功能存在:

| 區塊 | 標題寫的是 | 錨點 |
|---|---|---|
| `BMSM001` 覆核時寫 `OFD607A` 的覆核者 | `寫入OFD607A的ECAPPROVEID,ECAPPROVEDATE` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:325-346` |
| `BMSM001` 覆核時把 KYC 的代碼設為 `1` | `寫入OFD624的EC_PCODE覆核後設為"1"` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:349-368` |
| `BMSM001` 覆核時更新 `OFD601` 的註冊別 | `更新OFD601` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:381-399` |
| `BMSM001` 寫集保傳檔記錄 | `寫一筆新資料進 BMS001_TSCDLOG` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:537-608` |
| `BMSM001` 覆核刪除時清 `OFD607A` 的覆核欄位 | `清空OFD607A的ECAPPROVEID,ECAPPROVEDATE...等欄位` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3566-3590` |
| `BMSM001` 判斷要不要重送印鑑 | `判斷是否執行CallBfSeal()` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:649-672` |
| `BMSM006` 覆核時寫 EC 覆核者 | `寫入OFD607ACHG的ECApproveID,ECApproveDate` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:989-1011` |
| `BMSM006` 覆核刪除時回復 `OFD601` 註冊別並刪除 | (在 SQL 字串中間被註解) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:1050-1065` |
| `BMSM001` / `BMSM006` 掛 11 張帳戶明細 | `OFD101` 到 `OFD562` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:103-121` |

嚴重度:**中**。做影響分析時**一定要確認目標區塊是不是註解**, 本模組被註解的程式碼量大約佔 PO 層的兩成。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。§0 到 §3 與 §2.1 的 `CHG` 機制證據鏈為第一階段產出;§4 到 §8 與附錄 A 到 F 為第二階段續寫 |

由 build_doc.py v2.0.0 於 2026-09-21 10:52 產生 · 標題 131 · 圖 5 · 表格 80 · 程式錨點 445 · § 連結 64 · 引用檢查：畫面 26（缺 0） · Table 41（缺 0） · Trigger 2（缺 0） · 結果集 24（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
