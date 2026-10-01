<!-- 由 tools/build_copilot_kb.py 從 modules/ofd7.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS OFD7 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本。 **建議讀法**:先翻 §1 的圖抓全貌,再讀 §2 把「一張表同時當主檔與明細」以及 `_UPD` 配對表搞清楚(這兩件事是本片最容易誤解的地方),之後 §3 的清冊配 §4 起的畫面章節就讀得動了。**急著找 `_UPD` 是什麼的人直接跳 §4.10**。

> ⚠ **OFD7 不是一個業務模組,是一份切片。** OFD 模組有 550 支畫面,本文只涵蓋 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/` 這個 Entity 專案底下的 **15 支 M 畫面**。切片的依據是 Entity 專案資料夾,不是業務;所以本片內部含**五條互不相干的業務線**(§0.1)。名稱 `OFD7` 為**推測**,取自資料夾名。

> ⚠ **本片的業務意義**(§0)由表名、欄位 `msdata:Caption`、`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs` 的常數字典**推測**,待選單表回填。

> ⚠ **〔客戶特定〕**:基金公司代碼 `'Atlas'`、境內外代碼 `'1'`/`'2'`、四眼狀態字面量 `'301'`、EC 旗標 `etraflg='Y'` 為本站台的值。

> ⚠ **〔共用〕**:`OFD206` `OFD204` `OFD197A` `OFD195A` `OFD193A` `OFD194A` `OFD196A` `OFD213A` `OFD214A` `OFD215A` `OFD201A` `OFD202A` `OFD203A` `OFD687A` 同時服務 BMS / COD / EC / OFDB / OFD.Query(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼(EVA)看 `architecture.md §3`、SQL 組法與參數化看 `architecture.md §4`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這 15 支畫面管什麼(推測)

先給結論:**本片沒有單一業務主題,是「基金申購手續費率與 EC 促銷優惠」這個大主題底下的五塊設定檔維護**。

| 塊 | 畫面 | 在管什麼(推測) | 推測依據 |
|---|---|---|---|
| **A 牌告費率階梯** | `OFDM191` `OFDM192` `OFDM193` | 一檔基金的申購手續費率,依「金額級距」或「年度級距」分段設定,不分對象 | 欄位 `ALLOT_FEE_RATE` Caption 為「申購手續費率(%)」、`BNG_AMT`/`END_AMT` 為「申購起始/終止金額」 |
| **B 對象別優惠費率** | `OFDM194` `OFDM194B` `OFDM196` `OFDM198` | 在牌告之外,針對「某位受益人」「某身分別 × 某銷售機構」「某優惠專案」另外給一組費率 | 主鍵比 A 多掛 `BF_NO` / `REL_TYPE`+`AGENT_ID` / `DISC_CODE` |
| **C 優惠資格名單** | `OFDM195` `OFDM197` | 誰算「優惠關係人」(員工 / 推薦人)、誰屬於哪個「行銷身分別」;**只存資格,不存費率** | `OFD195A` 全表無費率欄;`OFD197A` 只有 `MKT_ID`+`BF_NO`+`BELONG_DATE` |
| **D EC 促銷活動** | `OFDM199` `OFDM204` `OFDM206` | 一檔促銷活動的內容(適用基金、費率、通路、身分群組、銷售機構)、可用次數上限,以及每位受益人的已用次數 | `CAMPAIGN_CODE` Caption 為「促銷活動代碼」;`OFD206` 有 `USED_ALLOT_TIMES` |
| **E 匯費與簡碼** | `OFDM213` `OFDM214` `OFDM215` | 哪些銀行免收匯費、某受益人某基金的匯費收取碼、基金簡碼 | 欄位 Caption「不收匯費銀行代碼」「贖回匯費收取碼」`SHORT_CODE` |

五塊之間**沒有任何程式呼叫**,只有一條真依賴:C 的 `OFD197A` 是 D 的活動對象判定輸入(見 §8.3)。讀 OFD7 的人如果預期整片是一條流程,會在 §4.6 之後完全對不上——先知道這件事比較省時間。

### 0.2 不管什麼

| 不在 OFD7 | 在哪 | 依據 |
|---|---|---|
| **把 `_UPD` 暫存的促銷活動費率搬進正式表** | **repo 內查不到執行者**,推測在版控外(SP / 排程 / Trigger) | 全庫對 `OFD199A_UPD` 的引用只有一處:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40`。詳見 §4.10 |
| 基金主檔建檔 | `OFDM081A`(境內 `OFD081A`)/ `OFDM081B`(境外 `OFD081`) | `architecture.md 附錄 A` 的「主檔於」欄 |
| 一次把六張費率 / 設定表跟基金一起建起來 | 批次 `OFDB004` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:64-71` |
| 促銷活動的**查詢** | `OFDI199`(OFD.Query 專案),讀的是正式表不是 `_UPD` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46` |
| 受益人開戶時順便掛 EC 優惠 | `BMSM001`(把 `OFD206` 當明細) | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:158` |
| 員工離職時終止優惠關係人 | 原本設計在 `CODM009`,**整段被註解** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:81-248`,與 `cod.md §4` 記的一致 |
| 費率真正被套用到交易 | 版控外的計價流程 | repo 內只有 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4497-4541` 這類「查得到哪些活動」的 SQL,沒有算費率的程式 |

### 0.3 使用角色

15 支全部是 M 維護畫面,全部走標準四眼(輸入 / 驗證 / 覆核),角色由平台的 ToDo 機制指派,OFD7 自己不定義角色——所有 PO 都只是把 `xTableHelper.AppendToDoString(...)` 接到查詢字串尾巴(例:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:101-102`)。詳見 `architecture.md §3`。

**三個例外**,實際上完全不經四眼:

| 入口 | 做什麼 | 錨點 |
|---|---|---|
| `OFDM197` 的匯入小畫面 | 讀 CSV 戶號清單,直接 `delete` + `insert`,狀態寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247` |
| `OFDM206` 的戶號清單匯入 | `insert ... select`,狀態寫死 `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206` 的 EC 整批匯入 | 同上,條件寫死 `etraflg='Y'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

這三段把 `ENTRYID` / `VERIFYID` / `APPROVEID` 一次填成同一個使用者、同一個 `SYSDATE`。**四眼的軌跡在,但沒有第二個人看過**。

### 0.4 上下游模組

| 方向 | 對象 | 介面 |
|---|---|---|
| 上游(讀) | `OFD081` / `OFD081A`(基金)、`OFD062`(基金公司)、`BMS001A`(受益人)、`OFD068A`(銷售機構)、`OFD072A`(推薦人)、`COD009`(員工)、`OFD601`(EC 網路戶)、`OFD027A`(行銷身分別)、`FSK003`(幣別)、`OFD094A` / `OFD020V`(保管銀行) | 全部是 `LEFT JOIN`,只取說明欄 |
| 下游(本片的表被誰讀 / 寫) | `OFDB004`(六張表當明細一起建)、`BMSM001`(`OFD206` 當明細)、`OFDI199` 與 EC 側(讀正式的促銷活動表)、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs`(判活動對象) | 見 §8 |
| 平行(同一張表兩個維護入口) | `OFD195A` 的第二個入口 `CODM009` **已被註解**;`OFD199A` 的第二個 PO 在 EC 專案 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34-44` |

### 0.5 全域開關

本片沒有 `App.config` 層級的業務開關。真正決定行為的三個「開關」都是資料欄位:

| 開關 | 值域 | 影響 | 錨點 |
|---|---|---|---|
| `FUND_TYPE`(基金資料來源) | `'1'` 境外 · `'2'` 境內 | 決定 `OFDM193` / `OFDM196` 開放幾檔費率欄、以及**哪些檢核會被跳過**(附錄 E.1) | 值域出處 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FEE_TYPE`(費率種類) | `'1'` 永久 · `'2'` 某期間 | `'1'` 時起迄日被清空 / 填 `00000000`~`99999999`,`'2'` 才用畫面上的日期 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:187-197`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-108` |
| `CAMPAIGN_TYPE`(活動類型) | `0` 開戶優惠 · 其餘 | `0` 時 `OFDM206` 限制「每位受益人只能一筆」;BMS 端刪舊資料也只刪 `0` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-76`、`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1859` |

`FUND_TYPE` 的 `'1'`=境外 / `'2'`=境內 這件事**在本片的註解裡是錯的**:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-66` 把 `== "1"` 註解成「境內境金」,同一個檔的 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-95` 又把 `== "1"` 註解成「境外基金」。以 `SHORE_ID.OnShore = "2"`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:294-296`)與 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:141-144`(「基金資料來源 預設境內基金」後面接 `uoptFUND_TYPE.Value = "2"` 與 `SOURCE_CD = SHORE_ID.OnShore`)為準:**`'1'` 是境外,`'2'` 是境內**。這個註解錯誤直接造成附錄 E.1 的缺陷。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] OFD7 全景：牌告費率、對象別費率、資格名單、EC 促銷活動、匯費與簡碼五條線與下游
圖中文字:① 牌告費率階梯：以基金為鍵，不分對象 / OFDM191 / OFD191 幣別x金額階梯 / OFDM192 / OFD192 年度階梯 / OFDM193 / OFD193A 境內外6檔費率 / OFD081 OFD081A / 境外 / 境內基金主檔 / ② 對象別優惠費率：牌告之外的例外，鍵上多掛一個對象 / OFDM194 / OFD194A 受益人x境內 / OFDM194B / OFD194 受益人x境外 / OFDM196 / OFD196A 身分別x機構 / OFDM198 / OFD198 優惠專案 / ③ 優惠資格名單：只管「誰有資格」，不存費率 / OFDM195 / OFD195A 員工/推薦人 / OFDM197 / OFD197A 行銷身分別歸屬 / CODM009 CODM010 / 寫回段落全被註解 / BasicOFD_PO / 活動對象判定吃 OFD197A / ④ EC 促銷活動：唯一有暫存表的一塊 / OFDM199 / OFD199A_UPD 主檔+6明細 / OFDM204 / OFD204/OFD205 次數設定 / OFDM206 / OFD206 個人可用次數 / OFDI199 / EC 側 / 讀正式表 OFD199A / ⑤ 匯費與簡碼：三支同型，複製功能長得一樣 / OFDM213 / OFD213A 免匯費銀行 / OFDM214 / OFD214A 匯費收取碼 / OFDM215 / OFD215A 基金簡碼 / OFDB004 / 一次建檔批次也寫這些表 / ⑥ 下游：費率與活動最後都由版控外的計價流程取用 / OFDB004〔OFDB〕 / 6 張表當明細一起建 / BMSM001〔BMS〕 / OFD206 當明細 / EC / OFD.Query / 讀 OFD201A~OFD687A / 計價與交易流程 / repo 內查不到執行者
```

*圖:圖 1 OFD7 全景。橘框=本片的維護入口;灰虛框=別的模組或別支畫面用同一張表;黑框=無原始碼或版控外。五條線彼此沒有程式呼叫，全靠表相連——③ 的 OFD197A 決定 ④ 的活動對象成不成立，是唯一一條跨線的真依賴。*

### 1.2 資料表關係

圖放在 §2 的開頭(`ofd7.figs.py` 的 `h2:2-`)。重點看 C 區:**七張明細裡只有三張有 `_UPD` 分身**。

### 1.3 主要維護畫面的四眼與卡控順序

圖放在 §4 的開頭(`h2:4-` 第二張)。一句話總結:**卡控幾乎全在 UI 的 `DoValidate()`,伺服端只有 `OFDM206` 掛了一道 `BeforeAdd`,而三個批次匯入入口連那一道都繞過。**

### 1.4 批次 / 報表資料流

**本片沒有 B 或 R 畫面**(§6、§7)。唯一算得上批次的是 `OFDM197` 與 `OFDM206` 掛在 M 畫面上的三個 CSV 匯入小視窗,它們不是 B 型畫面,是 M 畫面的 `DoExp1` / `DoExp2` 按鈕開出來的對話框(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:180-193`)。

### 1.5 一日作業泳道

本片沒有時序性的日常作業——15 支全是設定檔維護,使用者想改才進來。唯一有「時間感」的是 `OFDM199` 的 `_UPD` → 正式表生效(§4.10),但**生效的觸發時機在 repo 內查不到**,無法畫泳道。

## 2. 資料模型

```text
[圖] OFD7 二十三張表的分組、主鍵組成，以及 _UPD 暫存表與正式表的配對
圖中文字:A 多筆型：一支畫面一張表，主從都在同一張表上分群 / OFD191 / PK 基金+幣別+起迄+起額 / OFD192 / PK 基金+年度起 / OFD193A / PK +費率種類 / OFD196A / PK +身分別+機構 / OFD194A / PK +戶號+費率種類 / OFD194 / PK +戶號 無費率種類 / OFD198 / PK 專案+基金+戶號 / OFD213A OFD214A OFD215A / PK 基金 或 戶號x基金 / B 單筆型：OFD195A 與 OFD197A 各自獨立，沒有明細 / OFD195A / PK 身分別+代碼+機構+身分證 / OFD197A / PK 行銷身分別+統編 / OFDM197B / 匯入用 DataTable 僅 1 欄 / C 促銷活動：唯一的主明細結構，而且分成 _UPD 與 正式 兩套 / OFD199A_UPD / 主檔 PK 活動代碼 / OFD200A_UPD / 單筆費率明細 / OFD190A_UPD / 定期定額明細 / 三張只有 OFDM199 碰 / 全庫零其他引用 / OFD201A 通路 / 無 _UPD 分身 / OFD202A 身分群組 / 無 _UPD 分身 / OFD203A 銷售機構 / 無 _UPD 分身 / OFD687A 組合基金 / 欄名 COMPAIGN_CODE / D 次數控管：OFD204 設上限，OFD206 記個人，OFD207 記使用明細 / OFD204 / PK 活動代碼 / OFD205 / PK 基金+活動 / OFD206〔共用〕 / PK EC流水號+活動 / OFD207 / 使用記錄 無四眼欄位 / 外部唯讀：join 進來取說明，本片從不寫入 / OFD081 / OFD081A / 基金主檔 境外/境內 / OFD062 / 基金公司 / BMS001A / 受益人 / OFD068A OFD072A / 機構 / 推薦人 / OFD601 OFD027A / EC戶 / 行銷身分別
```

*圖:圖 2 資料模型。橘框=主檔或維護入口;白框=明細;灰虛框=共用;黑框=外部唯讀;橘虛框=陷阱。C 區是本片唯一的主明細結構，而且只有前三張有 _UPD 分身——後四張（OFD201A OFD202A OFD203A OFD687A）由維護畫面直接寫正式表。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

15 支畫面共宣告 **23 張實體表**。宣告方式分兩派,差別很大:

| 派別 | PO 基底 | 特徵 | 本片畫面 |
|---|---|---|---|
| **多筆型** | `BaseMultiRowEVADaoPO` | `MasterTable` 是 `List`,**沒有明細概念**;主從其實是同一張表,靠 `MasterPKey` 分群,畫面上半是「群」下半是「群內各列」 | `OFDM191` `OFDM192` `OFDM193` `OFDM194` `OFDM194B` `OFDM196` `OFDM198` `OFDM213` `OFDM214` `OFDM215` |
| **單筆型** | `BaseEVADaoPO` | `MasterTable` 單一 + `DetailTable` 清單 | `OFDM195` `OFDM197` `OFDM199` `OFDM204` `OFDM206` |

兩派的差別見 `architecture.md §3.9`。**多筆型沒有明細表這件事很容易看錯**——`atlas_scan.py --screen OFDM191` 報「明細 —」不是漏掉,是真的沒有。

逐支的宣告:

| 畫面 | 基底 | 主檔(實體表 → vdb 名) | 明細 | `MasterPKey` / `DetailTable` | 錨點 |
|---|---|---|---|---|---|
| `OFDM191` | 多筆 | `OFD191` → `OFDM191` | — | `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE`;`RemovePK` = `END_AMT` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:40-48` |
| `OFDM192` | 多筆 | `OFD192` → `OFDM192` | — | `FUND_ID`;`RemovePK` = `END_YEAR` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:40-45` |
| `OFDM193` | 多筆 | `OFD193A` → `OFDM193` | — | `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:34-43` |
| `OFDM194` | 多筆 | `OFD194A` → `OFDM194` | — | `FUND_ID` `CRNCY_CD` `BF_NO` `FEE_TYPE` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:38-48` |
| `OFDM194B` | 多筆 | `OFD194` → `OFDM194B` | — | `FUND_ID` `CRNCY_CD` `BF_NO` `BNG_DATE` `END_DATE`(**無 `FEE_TYPE`**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:42-51` |
| `OFDM195` | 單筆 | `OFD195A` → `OFDM195` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:41` |
| `OFDM196` | 多筆 | `OFD196A` → `OFDM196` | — | `FEE_TYPE` `REL_TYPE` `AGENT_CODE` `AGENT_ID` `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:24-36` |
| `OFDM197` | 單筆 | `OFD197A` → `OFDM197` | — | — | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:44` |
| `OFDM198` | 多筆 | `OFD198` → `OFDM198` | — | `DISC_CODE` `BF_NO` `FUND_ID` `BNG_DATE` `END_DATE`(**無 `FEE_TYPE`**) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:42-51` |
| `OFDM199` | 單筆 | `OFD199A_UPD` → `OFDM199` | `OFD200A_UPD` `OFD201A` `OFD202A` `OFD190A_UPD` `OFD203A` `OFD687A` | 六個 `DetailTable` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-48` |
| `OFDM204` | 單筆 | `OFD204` → `OFDM204` | `OFD205` | 一個 `DetailTable` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:40-42` |
| `OFDM206` | 單筆 | `OFD206` → `OFDM206` | — (`OFD207` 另外手動載入) | `AfterGetMaintainData` 補撈 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:44`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:98-106` |
| `OFDM213` | 多筆 | `OFD213A` → `OFDM213` | — | `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:36-37` |
| `OFDM214` | 多筆 | `OFD214A` → `OFDM214` | — | `BF_NO`;`CopyPKey` = `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:33-35` |
| `OFDM215` | 多筆 | `OFD215A` → `OFDM215` | — | `BF_NO`;`CopyPKey` = `FUND_ID` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:35-37` |

> ⚠ **`OFD207` 不是宣告出來的明細。** `OFDM206_PO` 只宣告了主檔;`OFD207`(使用記錄)是在 `AfterGetMaintainData` 裡**用同一個 `DbCommand` 改寫 `CommandText` 再 `LoadDataSet`** 撈進來的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:101-105`)。所以它**不會**參與四眼、不會被新增 / 修改 / 刪除,純唯讀顯示。掃描器把它歸為 dataset 不是實體表,原因就在這裡。

### 2.2 `_UPD` 是什麼:三張配對表(本篇核心的一半)

結論寫在 §4.10,這裡只放資料模型面的事實:

| `_UPD` 表 | 正式表 | 誰寫 `_UPD` | 誰讀正式表 |
|---|---|---|---|
| `OFD199A_UPD` | `OFD199A` | 只有 `OFDM199` | `OFDI199`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4499`、`Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:39`、`OFDM204`、`OFDM206` |
| `OFD200A_UPD` | `OFD200A` | 只有 `OFDM199` | `OFDI199`、EC 側 |
| `OFD190A_UPD` | `OFD190A` | 只有 `OFDM199` | `OFDI199`、EC 側 |

「只有 `OFDM199`」是實測結果:對 `Dev/` 全樹搜 `OFD199A_UPD` / `OFD200A_UPD` / `OFD190A_UPD`,命中的 `.cs` 只有 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` 一個檔。

**`_UPD` 不是框架機制。** `architecture.md §3.2` 講的框架雙表四眼(`Basic4EyesPO`,字尾寫死 `_Edit`)是**死碼**,零繼承零實例化;`OFDM199_PO` 繼承的是 `BaseEVADaoPO`,只是把 `xTableMapping` 的實體表名寫成 `OFD199A_UPD` 而已。也就是說**框架完全不知道 `_UPD` 的存在**,它就是一張普通的表。

### 2.3 `_TMP` 是什麼:第三份同形副本,而且是死的

`architecture.md 附錄 D.3` 提過「`OFD199A_TMP` 系列」在修掃描器時被補回母體。查下去的結果:

| 事實 | 錨點 |
|---|---|
| `OFDM199A_PO`(在 `PO.OFD`)宣告 `OFD199A_TMP` + 六張 `*_TMP`,與 `OFDM199_PO` 的結構**完全同形**,只是字尾換成 `_TMP` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199A_PO.cs:39-47` |
| 兩者連 vdb 名都一樣(都叫 `OFDM199` / `OFDM199_Fund` / …),共用同一份 `OFDM199Model.xsd` | 同上 vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-47` |
| 這支 PO **有**被編譯 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/PO.OFD.csproj:319` |
| 但 `ATLAS.OFD` 裡**沒有** `OFDM199A_Ctl`,`FormProxy.OFD` 有 `OFDM199A_Pxy.cs` 檔案卻**不在 csproj 裡**(`FormProxy.OFD.csproj` 只列 `OFDM199_Pxy.cs`) | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/FormProxy.OFD.csproj:214` |
| 那支 `.cs` 的 `InitializeControl()` 還 `new OFDM199A_Ctl()`,型別在 `Vendor.Product.TA.Control.OFD` 底下——**不存在** | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs:19` |

所以 `_TMP` 那一整套(7 張表 + 1 支 PO + 1 個不編譯的 Pxy)**永遠不會被執行**。

> ⚠ **別跟 OTA 的 `OFDM199A` 搞混。** `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM199A_PO.cs:67-70` 也叫 `OFDM199A_PO`,但它在 `Vendor.Product.TA.PO.OTA` 命名空間,指的是 `OFD199` / `OFD200`(**沒有 A 字尾**的另一組表),而且**有**完整的 `OFDM199A_Ctl` 與 `OFDM199A_Pxy`。`architecture.md 附錄 D.3` 的 D3 缺陷(同代號雙實作)講的就是這一對。本片只負責 OFD 側那份死的。

### 2.4 表的主鍵與四眼欄位

「PK」欄取自對應 xsd 的 `xs:unique … msdata:PrimaryKey`,是 **DataTable 的鍵**,不保證等於 DB 上的 constraint(`architecture.md §5.5`)。

| 表 | vdb 名 | PK(來源 xsd) | 四眼 13 欄 | 欄數 |
|---|---|---|---|---|
| `OFD191` | `OFDM191` | `FUND_ID` `CRNCY_CD` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 30 |
| `OFD192` | `OFDM192` | `FUND_ID` `BNG_YEAR` | 齊 | 26 |
| `OFD193A` | `OFDM193` | `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 34 |
| `OFD194A` | `OFDM194` | `FUND_ID` `BNG_AMT` `END_DATE` `BNG_DATE` `BF_NO` `CRNCY_CD` `FEE_TYPE` | 齊 | 35 |
| `OFD194` | `OFDM194B` | `FUND_ID` `CRNCY_CD` `BF_NO` `BNG_DATE` `END_DATE` `BNG_AMT`(**無 `FEE_TYPE`**) | 齊 | 34 |
| `OFD195A` | `OFDM195` | `REL_TYPE` `REL_NO` `AGENT_ID` `AGENT_CODE` `REL_IDNO` | 齊 | 28 |
| `OFD196A` | `OFDM196` | `REL_TYPE` `AGENT_ID` `AGENT_CODE` `FUND_ID` `CRNCY_CD` `FEE_TYPE` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 38 |
| `OFD197A` | `OFDM197` | `MKT_ID` `ID_NO` | 齊 | 22 |
| `OFD198` | `OFDM198` | `DISC_CODE` `FUND_ID` `BF_NO` `BNG_DATE` `END_DATE` `BNG_AMT` | 齊 | 35 |
| `OFD199A_UPD` | `OFDM199` | `CAMPAIGN_CODE` `PROMT_SCOPE` | 齊 | 29 |
| `OFD200A_UPD` | `OFDM199_Fund` | `CAMPAIGN_CODE` `FUND_ID` `PROMT_SCOPE` `CRNCY_CD` `FEE_TYPE` `BNG_AMT` | 齊 | 29 |
| `OFD190A_UPD` | `OFDM199_RSP` | 同上六欄 | 齊 | 37 |
| `OFD201A` | `OFDM199_Channel` | `CAMPAIGN_CODE` `PROMT_SCOPE` `CHANNEL_CD` `CHANNEL_CODE` | 齊 | 20 |
| `OFD202A` | `OFDM199_Mkt` | `CAMPAIGN_CODE` `PROMT_SCOPE` `MKT_ID` | 齊 | 19 |
| `OFD203A` | `OFDM199_AGENT` | `CAMPAIGN_CODE` `PROMT_SCOPE` `AGENT_ID` `AGENT_CODE` | 齊 | 20 |
| `OFD687A` | `OFDM199_PROD` | **`COMPAIGN_CODE`** `PRODUCT_ID` | 齊 | 19 |
| `OFD204` | `OFDM204` | `CAMPAIGN_CODE` | 齊 | 24 |
| `OFD205` | `OFD205` | `FUND_ID` `CAMPAIGN_CODE` | 齊 | 18 |
| `OFD206` | `OFDM206` | `BF_SRNO` `CAMPAIGN_CODE` | 齊 | 21(OFD 側 vdb 29,多 8 個 join 欄) |
| `OFD207` | `OFD207` | — | **無** | 12 |
| `OFD213A` | `OFDM213` | `FUND_ID` `CRNCY_CD` `NON_FEE_BANK` | 齊 | 22 |
| `OFD214A` | `OFDM214` | `BF_NO` `FUND_ID` | 齊 | 22 |
| `OFD215A` | `OFDM215` | `BF_NO` `FUND_ID` | 齊 | 21 |

四張沒有實體表的 vdb DataTable:

| vdb 表 | 用途 | 錨點 |
|---|---|---|
| `OFDM197B` | `OFDM197` 匯入畫面的戶號清單,**只有 `BF_NO` 一欄** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:45` |
| `OFDM214_Copy` | `OFDM214` 複製對話框的四個參數欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:58` |
| `OFDM199_Fund_Detail_D` | `GetOFD193` 抓牌告費率回來當「原費率」對照,8 欄 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:130` |
| `OFDM206A` | `OFDM206_PO.CheckData` 的回傳容器,xsd 內**零欄位** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:254` |

### 2.5 欄位中文名:本片填得相當完整

規則照 `architecture.md §5.5`:中文名唯一來源是 xsd 的 `msdata:Caption`,**不自己翻**。本片 23 張表的業務欄幾乎都有填,只有四眼 13 欄與 `DATAID` 一律留空——這是全庫通則,不是本片的問題。

三個要特別記住的 Caption 陷阱:

| 陷阱 | 內容 | 錨點 |
|---|---|---|
| **兩欄同名** | `OFD206` 的 `USED_ALLOT_TIMES` 與 `USED_RSP_TIMES` Caption **都叫「單筆已用次數」**;`ALLOT_TIMES` 與 `RSP_TIMES` **都叫「單筆可用次數」**。看 Caption 分不出單筆 / 定額 | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM206Model.xsd:46-49` |
| **欄名拼錯** | `OFD687A` 的活動代碼欄拼成 `COMPAIGN_CODE`(C-O-M),不是 `CAMPAIGN_CODE`。PO 為此寫了一個 `if` 特例補救 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494` |
| **同名不同義** | `OFD199A_UPD.FEE_TYPE` Caption 是「手續費類型」(`OFDM199_Fund` 的 `CAMP_DISC_TYPE` 才是「費率種類」),而 `OFD191`~`OFD198` 的 `FEE_TYPE` Caption 是「費率種類」(永久 / 某期間) | `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM199Model.xsd` vs `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM191Model.xsd` |

### 2.6 狀態碼

本片沒有自己的狀態機。`STATUS` 完全交給框架的 `EVAStatusCode`(無原始碼,從呼叫端反推,見 `architecture.md §3.10`),本片的 PO **一次都沒有**跟 `EVAStatusCode` 的常數做比較。

唯一直接碰 `STATUS` 字面值的地方是三段繞過四眼的批次 SQL,寫死 `'301'`:

| 位置 | SQL 片段 | 錨點 |
|---|---|---|
| `OFDM197.BatchAdd` | `insert into OFD197A(… STATUS …) values(… ,'C','301', …)` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |
| `OFDM206.BatchAdd` | `select … ,'301',:USERID,SYSDATE,…` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185` |
| `OFDM206.BatchAddEC` | 同上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:298` |

**假設**:`'301'` 是 `EVAStatusCode.ApproveAdd`(已覆核新增)。依據是這三段同時把 `ENTRYID` / `VERIFYID` / `APPROVEID` 全部填成同一個使用者,語意上就是「一步到位已覆核」。`architecture.md §3.10` 說全庫掃到的 `STATUS` 字面值是 `'0'`~`'6'`、`'8'`、`'9'` 單字元,**三位數的 `'301'` 不在那個集合裡**——兩邊對不上,值域到底幾位數要查資料庫才能確定。本文把它標為 **〔假設〕缺:DB 連線**。

`OFDM206` 另外有一處把 `CAMPAIGN_TYPE` 當狀態用:`if (row.CAMPAIGN_TYPE > 0) return;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64`),`0` 代表「開戶優惠」。值域出處查不到 `CTL014` 的對應分類,標**推測**。

## 3. 畫面清冊

### 3.1 維護 M

15 支全部六層齊全,全部在 `Dev/ATLAS.OFD`(UI / FormProxy / Control / PO)+ `DataEntity.OFD7` / `UIEntity.OFD7`(Model / View)。中文名待選單表回填,「用途」欄為推測。

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | 子對話框 | 特別之處 |
|---|---|---|---|---|---|---|
| `OFDM191` | 基金牌告費率(幣別 × 金額級距) | 齊 | `OFD191` | — | — | 只有一檔費率;`WHERE BNG_AMT = 1` 抓群首 |
| `OFDM192` | 基金牌告費率(年度級距) | 齊 | `OFD192` | — | — | 費率與固定金額二擇一;`WHERE BNG_YEAR = 1900` 抓群首 |
| `OFDM193` | 基金牌告費率(境內外 × 六檔費率) | 齊 | `OFD193A` | — | — | CTE 把 `OFD081A` 與 `OFD081` union 成一張;逐年遞減檢核掛錯分支(附錄 E.1) |
| `OFDM194` | 受益人專屬費率(境內) | 齊 | `OFD194A` | — | `OFDM194p0` 複製 | 六檔費率;有「複製受益人」 |
| `OFDM194B` | 受益人專屬費率(境外) | 齊 | `OFD194` | — | — | 兩檔費率;**沒有**複製功能 |
| `OFDM195` | 優惠關係人(員工 / 推薦人)名單 | 齊 | `OFD195A` | — | — | 七成程式碼是註解;`CheckData` 三層外殼全在,沒人呼叫(附錄 E.3) |
| `OFDM196` | 身分別 × 銷售機構專屬費率 | 齊 | `OFD196A` | — | — | 多一組轉申購費率;明細 SQL 的日期條件被註解 |
| `OFDM197` | 行銷身分別歸屬受益人 | 齊 | `OFD197A` | — | `OFDM197p0` CSV 匯入 | 整條六層是 Big5;匯入繞過四眼(附錄 E.2 / E.5) |
| `OFDM198` | 優惠專案專屬費率 | 齊 | `OFD198` | — | — | 費率欄 Caption 是「顧問費率」與「手續費率」 |
| `OFDM199` | EC 促銷活動設定 | 齊 | `OFD199A_UPD` | `OFD190A_UPD` `OFD200A_UPD` `OFD201A` `OFD202A` `OFD203A` `OFD687A` | `OFDM199p0`~`OFDM199p3` 六個明細編輯窗 | 本片最大;`_UPD` 機制(§4.10) |
| `OFDM204` | EC 優惠活動次數上限 | 齊 | `OFD204` | `OFD205` | — | 最小的一支 PO(121 行) |
| `OFDM206` | EC 優惠活動個人可用次數 | 齊 | `OFD206` | —(`OFD207` 唯讀補撈) | `OFDM206p0` 戶號匯入 · `OFDM206p1` EC 整批 | 唯一有伺服端 `BeforeAdd`;刪除確認邏輯反了(附錄 E.6) |
| `OFDM213` | 基金免收匯費銀行 | 齊 | `OFD213A` | — | `OFDM213p0` 複製基金 | `IsBfExsits` 查一個不存在的欄(附錄 E.8) |
| `OFDM214` | 受益人 × 基金 匯費收取碼 | 齊 | `OFD214A` | — | `OFDM214p0` 複製戶號 · `OFDM214p1` 複製基金 | `Ctl` 七成是註解 |
| `OFDM215` | 受益人 × 基金 簡碼 | 齊 | `OFD215A` | — | `OFDM215p0` 複製戶號 · `OFDM215p1` 複製基金 | 與 `OFDM214` 幾乎一模一樣,但 `catch` 少一行(附錄 E.9) |

### 3.2 查詢 I

**本片無 I 畫面。**原因:`DataEntity.OFD7` 只收 M 型的 Model,同主題的查詢畫面 `OFDI199` 在另一個專案 `Dev/ATLAS.OFD.Query`,不屬於本片(但它是理解 `_UPD` 的關鍵,見 §4.10)。

### 3.3 批次 B

**本片無 B 畫面。**三個 CSV 匯入入口是 M 畫面的子對話框,不是 `xOneStepProcessForm` 型的 B 畫面(見 §6)。

### 3.4 報表 R

**本片無 R 畫面。**`DataEntity.OFD7` 底下沒有任何 `*R*Model.xsd`,`Dev/ATLAS.OFD.Report` 也沒有對應這 15 支的報表(見 §7)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] OFD7 其餘十四支維護畫面的分群、卡控層次與共同寫法
圖中文字:① 卡控幾乎全在 UI 的 DoValidate，伺服端只有一支再驗一次 / validatorManager1 / 必填與型別 / DoValidate / 業務檢核 / SetMasterToDetail / 把主鍵塞進明細 / 伺服端 BeforeAdd / 只有 OFDM206 有 / ② 費率階梯群：靠寫死常數抓「群組第一筆」 / OFDM191 / WHERE BNG_AMT = 1 / OFDM192 / WHERE BNG_YEAR = 1900 / OFDM193 194 194B 196 198 / WHERE BNG_AMT = 1 / 起始值不是常數就消失 / 過濾且無提示 / ③ 對象別費率群：同一句 FeeTypeValidate，四支各抄一份 / OFDM194 / OFD194A 字串串接 SQL / OFDM194B / OFD194 同一份程式碼 / OFDM198 / OFD198 換成專案代碼 / catch 不補結果列 / 例外時當成通過 / ④ 匯費簡碼群：ROW_NUMBER 取群組首列，外加複製功能 / OFDM213 / ExecCopy 複製基金 / OFDM214 / ExecCopy 基金或受益人 / OFDM215 / ExecCopy 基金或受益人 / IN 子查詢字串拼接 / 參數值直接進 SQL / ⑤ 批次匯入：三個入口繞過四眼，直接寫入已覆核狀態 / OFDM197 BatchAdd / delete+insert 狀態寫死 / OFDM206 BatchAdd / insert select 狀態寫死 / OFDM206 BatchAddEC / 條件寫死 etraflg=Y / 不經 BeforeAdd / 主畫面卡控全繞過
```

*圖:圖 4 其餘畫面分群。橘框=正常的維護入口;橘虛框=風險寫法;白框=一般步驟。四群十四支畫面的共同體質：卡控幾乎全在 UI，伺服端只有 OFDM206 有一道 BeforeAdd，而三個批次匯入入口連那一道都繞過。*

```text
[圖] OFDM199 的 _UPD 暫存表到正式表的流程，以及未被使用的 _TMP 第三份副本
圖中文字:① 維護端：OFDM199 一支畫面，同時寫兩種表 / OFDM199 維護畫面 / 7 張表掛同一次四眼 / 走 _UPD 的 3 張 / OFD199A_UPD 等 / 直接寫正式的 4 張 / OFD201A OFD202A 等 / 同一顆四眼狀態 / 無法分開送審 / ② 四眼：輸入 → 驗證 → 覆核，全掛在 _UPD 主檔上 / 輸入 Entry / 寫 OFD199A_UPD / 驗證 Verify / 資料仍在 _UPD / 覆核 Approve / 資料仍在 _UPD / OFD199A 仍是舊值 / EC 端看到舊費率 / ③ 生效：repo 內找不到搬運者，無 SP 無批次無 Trigger / OFD199A_UPD / 覆核完的新費率 / 未知搬運程序 / 假設在版控外 / OFD199A OFD200A OFD190A / 正式表 / OFDI199 EC 計價 / 只讀正式表 / ④ 第三份同形副本：_TMP 系列，編得起來但沒有入口 / OFDM199A_PO / PO.OFD 內 有進 csproj / OFD199A_TMP 等 7 張 / 全庫只有這支宣告 / OFDM199A_Pxy / 檔案在 但不在 csproj / 沒有 Ctl 與 UI / 永遠不會被執行 / ⑤ 立即生效的那四張：改完不必等生效，EC 當下就吃到 / OFDM199 存檔 / 四眼狀態只寫在主檔 / OFD201A OFD202A / 通路 / 身分群組 / OFD203A OFD687A / 銷售機構 / 組合基金 / EC 與 Common 直接讀 / 沒有等待期
```

*圖:圖 3 _UPD 機制（本篇核心）。橘框=真的會動的東西;橘虛框=風險或無入口的死碼;黑框=repo 內看不到內容。最要記住的是 ① 與 ⑤：同一次存檔裡，三張費率表進暫存等生效，四張對象表當下就改了正式表——兩半的生效時機不一樣。*

本章順序照 §0.1 的五塊業務線排,不照代號順序: **A 牌告費率** §4.1~§4.3 · **B 對象別費率** §4.4~§4.6 · **C 資格名單** §4.7~§4.8 · **D EC 促銷** §4.9~§4.11 · **E 匯費簡碼** §4.12。

### 4.0 十五支共同的骨架

先把重複的部分講完,後面各節只寫差異。

| 環節 | 共同做法 | 錨點(以 `OFDM191` 為例) |
|---|---|---|
| UI 基底 | `xMaintainForm`(無原始碼,從呼叫端反推),`TabPages = 2`(查詢頁 + 維護頁) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:84` |
| 存檔前檢核 | `OFDM191_BeforeAddButtonClicked` / `BeforeModifyButtonClicked` → `DoValidate()` → `ValidateErrList.Show()` 有錯就 `e.Cancel = true` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:155-178` |
| 主檔值下推 | `SetMasterToDetail()` 在檢核通過**之後**才跑,把畫面上半的鍵塞進每一列明細 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:66-77` |
| 四眼 | 全走框架,PO 只掛 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` 三個取數事件 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:151-164` |
| ToDo | `xTableHelper.AppendToDoString(<表名>, args.ModelVDB)`,只在 `args.Status == xEVAStatus.ToDO` 時接上 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:101-102` |
| 分群 | 多筆型畫面的「主檔查詢」都是同一張表再過濾一次,只取群組首列 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92` |

**三件全片通用、值得先記住的事:**

1. **`SetMasterToDetail()` 在 `DoValidate()` 之後跑。** 所以 `DoValidate()` 看到的明細列,鍵欄位(`FUND_ID` / `CRNCY_CD` / `BNG_DATE` …)**還是舊值或空的**。`OFDM193` 與 `OFDM196` 的逐年遞減檢核就是踩在這條上出事的(附錄 E.1)。

2. **`if (this.ValidateErrList.ErrorCount != 0) return;` 這一行會截斷後面所有業務檢核。** 例:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:50`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:67`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:218-219`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:42`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:39`。使用者只會看到必填錯誤,修完再存才會看到業務錯誤——要按兩次以上。

3. **兩支畫面的「修改」直接呼叫「新增」的 handler**,所以兩者的檢核完全一樣:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:180-183`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:137-140`。

### 4.1 `OFDM191` — 基金牌告費率(幣別 × 金額級距)

- **用途(推測)**:一檔基金 × 一個交易幣別 × 一段申購期間,依「申購金額級距」設定 `ALLOT_FEE_RATE`(申購手續費率 %)。畫面上半選基金 / 幣別 / 費率種類 / 日期,下半是金額級距表。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:74-105`,`LEFT JOIN FSK003`(幣別名)`OFD081`(基金簡稱)`OFD062`(基金公司)。

- **明細查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:119-144`,同樣三個 join,多帶 `BNG_AMT` `END_AMT` `ALLOT_FEE_RATE`。

**「群組首列」是靠寫死常數抓的。** 主檔 SQL 的 `WHERE BNG_AMT = 1`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92`)加上 `SELECT … ,1 BNG_AMT ,1 END_AMT`(`:81-82`)——把金額欄硬塞成 1,讓多筆四眼引擎以為每一群只有一列。這能成立是因為 UI 的階梯控制元件把第一階起始金額鎖死在 1:`LevelGridUtility(this.ugrdOFDM191, "BNG_AMT", "END_AMT", …, 1m, 999999999999m)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:210`,`LevelGridUtility` 無原始碼,從呼叫端反推)。**但凡有一筆資料不是從這支畫面寫進去的(例如 `OFDB004`),而且起始金額不是 1,那一整群在 `OFDM191` 就查不到、也改不到,而且沒有任何提示。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:43-46` |
| 存檔前 | 申購日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:48-51` |
| 存檔前(**僅新增**) | `custCRNCY_CD.Text` 為空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:53-59` |
| 查詢前 | 查詢條件日期(起) > (迄) | 訊息同名,`e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:131-140` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92` |

**欄位轉換**:費率種類 `'1'`(永久)時,起迄日被寫成 `"00000000"` / `"99999999"`,不是畫面上的日期(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:74-75`)。**這跟 `OFDM193` / `OFDM194` 的境內分支寫空字串 `""` 不一樣**,同一個語意在本片有兩種表示法,見附錄 E.11。

**跨表更新**:無。`OFDM191_PO` 只有三個取數事件,沒有任何 `After*`。

### 4.2 `OFDM192` — 基金牌告費率(年度級距)

- **用途(推測)**:同一檔基金,依「持有年度」分段給費率。與 `OFDM191` 的差別是級距軸從金額換成年度,而且多一個 `FIX_ALLOT_FEE`(固定申購手續費),與費率二擇一。

- **主檔查詢**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:70-91`;**只 join `OFD081` 與 `OFD062`,沒有幣別**——`OFD192` 整張表沒有 `CRNCY_CD`。

- **群首常數**:`WHERE BNG_YEAR = 1900`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82`),對應 UI 的 `LevelGridUtility(…, "BNG_YEAR", "END_YEAR", …, 1900m, 9999m, 1m)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:166`)。與 `OFDM191` 同型,常數不同。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 逐列:`ALLOT_FEE_RATE = 0` 且 `FIX_ALLOT_FEE = 0` | 「'第 N 列申購手續費率(%)'與'固定申購手續費'必須擇一輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:122-130` |
| 存檔前 | `CheckPKeyRequire()` 不過 | 「年度(起),年度(迄)必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:132-135` |
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:137-140` |
| 格子離開時 | 年度(起)或(迄)為空 | 訊息 + 整列標紅,**故意不 `e.Cancel`** | 警示 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:218-231` |
| 格子更新前 | `CheckPKeyDuplicate()` 不過 | 「'年度(起)''年度(迄)'重覆」+ `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:258-264` |
| 主檔取數 | `BNG_YEAR = 1900` | 不是 1900 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82` |

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:226` 留了一行註解說明為什麼不 `e.Cancel`:「不下 e.Cancel , 以免只因為 P_key 未填而把整個 Row 的資料回復」——這是刻意的取捨,不是漏寫。

**跨表更新**:無。

### 4.3 `OFDM193` — 基金牌告費率(境內外 × 六檔費率)

這是 A 塊裡功能最完整的一支,也是本片**兩個「檢核掛錯分支」缺陷**的第一個。

- **用途(推測)**:與 `OFDM191` 同一件事,但(a) 支援境內 / 境外兩種基金主檔,(b) 費率從一檔擴成六檔:單筆申購 `ALLOT_FEE_RATE` / `ALLOT_FEE_RATE1` / `ALLOT_FEE_RATE2` 與定期定額 `RSP_FEE_RATE` / `RSP_FEE_RATE1` / `RSP_FEE_RATE2`,(c) 多一個 `MEMO`。

**境內外怎麼做的**:主檔與明細 SQL 各自用一段 CTE `MYOFD081A`,把 `OFD081A`(標 `'2'`)與 `OFD081`(標 `'1'`)`UNION ALL` 成一張虛擬基金表,再用 `FUND_TYPE` 當條件過濾(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:69-87`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:135-153`)。這比 `dsm.md §4` 記的「`AND :FUND_TYPE = '2'` … `UNION` …」乾淨一點,但**同一段 CTE 在同一個檔裡抄了兩份**,改一邊要改兩邊。

**UI 依 `FUND_TYPE` 切換的三件事**:

| 動作 | 境外(`'1'`) | 境內(`'2'`) | 錨點 |
|---|---|---|---|
| 基金搜尋器來源 | `SHORE_ID.OffShore` | `SHORE_ID.OnShore` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:594-608` |
| 費率 1 / 2 欄 | 隱藏 + 禁止編輯 | 顯示 + 可編輯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:599-612`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:624-643` |
| 存檔前 | 費率 1 / 2 強制歸零,起迄日填 `00000000`/`99999999` | 保留使用者輸入,起迄日填 `""` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:93-108` |

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:45-48` |
| 存檔前 | 申購日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:50-53` |
| 存檔前(僅新增) | 幣別為空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:55-61` |
| 存檔前(**僅 `FUND_TYPE == "1"`,即境外**) | 六檔費率不符逐年遞減 | 「手續費率需符合逐年遞減原則,請檢查手續費率!!」 | **形同虛設**,見附錄 E.1 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-75` |
| 選基金後(僅境內) | 前收型基金不開放費率 1 / 2;不開放定額的基金不開放定額費率 | 欄位轉唯讀並清值 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:393-430` |
| 格子啟用前 | 境外要編費率 1 / 2 | `Activation.NoEdit` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:624-643` |
| 查詢前 | 查詢日期(起) > (迄) | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:184-192` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:107` |

〔客戶特定〕查詢頁選「境內」時基金公司被寫死成 `"Atlas"` 並鎖住:`this.custFH_CD_0.Value = "Atlas";`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:570-573`)。

**跨表更新**:無。

### 4.4 `OFDM194` 與 `OFDM194B` — 受益人專屬費率(成對,但不是本表/異動表)

**先回答最容易誤會的問題:`OFD194` 與 `OFD194A` 不是「本表 vs 異動表」,不像 BMS 的 `CHG`(`bms.md §2`)。它們是同一個業務概念的境內 / 境外兩張表,各自獨立、各有一支畫面、互不參照。**

證據四條:

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `OFDM194_PO` 的主檔 join `OFD081A`;`OFDM194B_PO` 的主檔 join `OFD081` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:96-97` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:99-100` |
| 2 | `OFDM193` 的 CTE 明寫 `OFD081A` → `FUND_TYPE '2'`(境內)、`OFD081` → `'1'`(境外) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:75`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:85` |
| 3 | 欄位形狀跟著境內外走:`OFD194A` 六檔費率(境內才用得到 1 / 2),`OFD194` 只有 `ALLOT_FEE_RATE` 與 `RSP_FEE_RATE` 兩檔 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:133-138` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:136-137` |
| 4 | 兩張表沒有任何共同欄位可以串(沒有 `BF_CHG_NO` 這種單號),也沒有任何一段程式同時讀兩張 | 全庫搜 `OFD194A` 與 `OFD194` 的交集為空 |

**兩支的差異總表**(這是「成對畫面只改一邊」的活教材):

| 面向 | `OFDM194`(`OFD194A`,境內) | `OFDM194B`(`OFD194`,境外) | 評註 |
|---|---|---|---|
| `MasterPKey` | 含 `FEE_TYPE` | **不含** `FEE_TYPE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:45` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:46-50`;與各自 xsd 的 PK 一致,**不是 bug** |
| 費率欄 | 6 檔 | 2 檔 | 與境內外的業務需求一致 |
| 逐年遞減檢核 | 有(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72`) | **無** | 境外只有 1 檔費率,沒得遞減,**合理** |
| `FeeTypeValidate` | 有 | 有,**一字不差** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:350-399` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:191-240`,只差表名 |
| 複製受益人 | 有 `Copy` + `CheckRepeat` + 子畫面 `OFDM194p0` | **完全沒有** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:192-340` |
| 檢核訊息 | 同一句「同一基金+幣別+受益人,只可設定一種費率種類!!」出現 5 處 | 同一句出現 5 處 | 合計 10 處硬編字串 |

**`FeeTypeValidate` 在做什麼**:使用者選了費率種類 A,程式就拿「另一種」B 去查同一個基金 + 幣別 + 受益人有沒有資料;查到就擋。UI 端把「另一種」算好再傳:`(uoptFEE_TYPE.Value == FEE_TYPE.Forever ? FEE_TYPE.Course : FEE_TYPE.Forever)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:110`)。

**這支檢核有三個問題**(附錄 E.4):SQL 全用字串串接;`catch` 只記 log **不補結果列**,而 UI 端 `if (View.Util.Result.Rows.Count > 0) return ReturnCode;` 否則 `return true`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:114-117`)——**資料庫一出錯就當成通過**;而且只在 `ActionMode == Add` 時才跑(`:104`),改成另一種費率種類時不檢查。

**`Copy`(只有 `OFDM194` 有)的四步驟**,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:192-340`:

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 用來源戶號撈設定,撈不到就把「查無資料」換成「From 受益人戶號 + 基金代碼 的設定資料不存在,請重新選擇」 | `:211-222` |
| 2 | 換成目的戶號再撈一次,檢查目的端是否已有資料 | `:229-246` |
| 3 | 目的端有資料就先 `ApproveDelete` 刪掉 | `:254-266` |
| 4 | 把來源列的 `BF_NO` 換成目的戶號、四眼 13 欄全部清空(日期填 `1900/1/1`)、再 `Add` | `:268-327` |

**步驟 4 的分批寫入是為了 ToDo**:`if (source_data.Rows.Count == 1) base.Add(...) else` 逐批 `this.Add(...)`,註解寫「若多批資料的話要分別 Add,因為要分別寫 todo」(`:294-296`)。分批的條件字串用 `String.Format` 拼 `DataTable.Select()`(`:306`、`:311`),基金代碼帶單引號會炸。

**卡控總表(兩支合併,標註哪支有)**

| 時點 | 檢核 | 成立時 | 結果類型 | 有的畫面 | 錨點 |
|---|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:48-49`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194B.cs:48-49` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:52-55` |
| 存檔前(僅新增) | 幣別空白 | 「選取的基金不適用此 幣別代碼」 | 阻擋 | 兩支 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:57-63` |
| 存檔前 | 六檔費率不符逐年遞減 | 訊息 | 阻擋 | **只有 `OFDM194`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72` |
| 選基金 / 幣別 / 戶號 / 費率種類後(僅新增) | `FeeTypeValidate` 查到另一種費率種類已存在 | 「同一基金+幣別+受益人,只可設定一種費率種類!!」 | 阻擋 | 兩支各 5 處 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:344`、`:424`、`:579`、`:608`、`:640` |
| 複製前 | From 與 To 戶號相同 | 「戶號與複製戶號不可相同」 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194p0.cs:50` |
| 複製中 | 來源不存在 / 目的已存在 | 兩句不同訊息 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:446-463` |
| 複製中 | 寫入筆數與 `DataRow` 筆數不符 | 丟 `ApplicationException("複製的資料筆數錯誤。")`,交易回滾 | 阻擋 | 只有 `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:321-324` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | 兩支 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:100`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:103` |

**跨表更新**:`Copy` 會 `ApproveDelete` 目的戶號的舊資料(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:258`),跨兩個連線的交易(`dbProduct` + `dbPTPF`)一起 commit(`:251-252`、`:328-329`)。其餘無。

### 4.5 `OFDM196` — 身分別 × 銷售機構專屬費率

- **用途(推測)**:針對「某身分別(`REL_TYPE`)× 某銷售機構(`AGENT_ID` + `AGENT_CODE`)」設定一組優惠費率。比 `OFDM193` 多一組轉申購費率 `SWITCH_FEE_RATE` / `1` / `2`,合計九檔。

- **主鍵維度最多**:`MasterPKey` 八欄(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:28-35`),xsd PK 九欄。

- **境內外機制與 `OFDM193` 完全相同**:同一段 `MYOFD081A` CTE 又抄了兩份(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:64-82`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:130-148`),四份 CTE 散在兩個檔裡。

**兩個歷史包袱寫在註解裡**:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:61-62` 與 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:127-128` 各留一句「取消欄位:(CHANNEL_CD,CHANNEL_CODE) / 新增欄位:(AGENT_ID,AGENT_CODE)」。UI 端對應的三段「身分別為推薦人時通路必輸」檢核整段被註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:68-78`)。

**明細 SQL 少一個條件。** 主檔 SQL 有 `AddDateTimeParam(..., "BNG_DATE", "END_DATE")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:108-109`),明細 SQL 的同一行**被註解掉**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182`)。後果:使用者在查詢頁下了申購日期區間,主檔清單有濾,點進去看明細時**日期條件不生效**,同一組基金 + 幣別 + 身分別 + 機構下的其他期間資料會一起出現。其他五支同型畫面(`OFDM191` `OFDM193` `OFDM194` `OFDM194B` `OFDM198`)的明細 SQL 都有這一行。**成對(這裡是六胞胎)只改一邊**,列入附錄 E.10。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:62-65` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:98-101` |
| 存檔前 | 有列 `ALLOT_FEE_RATE < 0` | 「單筆申購手續費率 必須大於0」(**訊息說「大於 0」,條件是「小於 0」,0 會過**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:103-104` |
| 存檔前(定額欄可編輯時) | 有列 `RSP_FEE_RATE < 0` | 同上句型 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:105-107` |
| 存檔前(**僅 `FUND_TYPE == "1"`,即境外**) | 有列 `SWITCH_FEE_RATE < 0` | 「轉申購手續費率 必須大於0」 | **形同虛設**,境外此欄被強制歸零 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:112-113` |
| 存檔前(**僅境外**) | 九檔費率不符逐年遞減 | 訊息 | **形同虛設**,見附錄 E.1 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:115-124` |
| 存檔前(**僅境外 + 僅新增**) | 幣別空白 | 「選取的基金不適用此 幣別代碼」 | **境內完全不檢查** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:126-132` |
| 格子啟用前 | 境外要編費率 1 / 2 / 轉申購 | `Activation.NoEdit` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:819-841` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:103` |
| 明細取數 | 日期條件被註解 | 其他期間的列一起出現 | **過濾失效(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182` |

**跨表更新**:無。

### 4.6 `OFDM198` — 優惠專案專屬費率

- **用途(推測)**:以「優惠專案代碼 `DISC_CODE`」為主鍵起頭,針對某基金 + 某受益人設一組費率。與 `OFDM194` 的差別是把「幣別」換成「優惠專案」,而且費率欄的 Caption 特別:`ALLOT_FEE_RATE` 是「顧問費率(%)」、`ORG_ALLOT_FEE_RATE` 是「手續費率(%)」——**兩欄一起存,推測是「原本收多少 / 改成收多少」**。

- **`DISC_CODE` 與 `DISC_NM` 是自由輸入**,不是下拉:`row.DISC_CODE = Convert.ToString(this.utxtDISC_CODE.Text);`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:68-69`)。repo 內找不到 `DISC_CODE` 的代碼字典,所以**沒有任何地方檢查專案代碼存不存在**。

- **join 不含幣別**:`OFD198` 沒有 `CRNCY_CD` 欄,主檔只 join `BMS001A` `OFD081` `OFD062`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:94-100`)。注意它 join 的是 `OFD081`(境外),沒有境內的分支。

**`FeeTypeValidate` 與 `OFDM194` / `OFDM194B` 是同一份程式碼**,只把 `CRNCY_CD` 換成 `DISC_CODE`、表名換成 `OFD198`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:188-237`)。三支的問題完全一樣(附錄 E.4)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細列數為 0 | 「明細資料必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:48-49` |
| 存檔前 | 日期(起) > (迄) | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:52-55` |
| 選基金 / 專案 / 戶號 / 費率種類後(僅新增) | `FeeTypeValidate` 查到另一種費率種類已存在 | 「同一基金+優惠專案代碼+受益人,只可設定一種費率種類!!」(其中 4 處訊息寫成「同一基金+幣別+受益人」,**文案沒跟著改**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:273`、`:329`、`:447`、`:475`、`:507` |
| 主檔取數 | `BNG_AMT = 1` | 不是 1 的群不出現 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:101` |

**沒有逐年遞減檢核**:`OFD198` 只有一檔費率 + 一檔原費率,不適用。

**跨表更新**:無。

### 4.7 `OFDM195` — 優惠關係人(員工 / 推薦人)名單

本片**程式碼死亡率最高**的一支:`OFDM195_PO.cs` 共 1,724 行,其中 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:506-1722` 是一整塊 `/* … */`,**1,217 行(70%)是 SQL Server 時代的舊實作**(裡面全是 `[OFD195]` 這種中括號語法與 `con.Open()` 自建連線)。活著的只有三段:取數 SQL、`CheckData`、`CheckRspChgDate`。

- **用途(推測)**:登錄誰是「優惠關係人」。`REL_TYPE` 分兩種:`'1'` 員工(對 `COD009.EMP_NO`)、`'2'` 推薦人(對 `OFD072A.SPONSOR_CODE`)。有申請日期 `APPLY_DATE` 與終止日期 `REL_STOP_DATE`。

- **`REL_NO` 是兩個控制項相加**:`Row.REL_NO = this.custEMP_NO.Value + this.custSPONOSR_CODE.Value;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:412`)——靠「其中一個一定是空字串」成立。

- **身分別的姓名與身分證字號是 SQL 裡的 `CASE`**,不是 join 後挑欄:`CASE OFD195A.REL_TYPE WHEN '1' THEN COD009.EMP_NAME WHEN '2' THEN OFD072A.SPONSOR_NAME ELSE N' ' END`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:155-164`)。查詢條件 `ALL_IDNO` 也要把同一段 `CASE` 再寫一次(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:222-233`)。

**`RSP_CHG_DATE` 在畫面上永遠是空的。** 主檔 SQL 把它寫死成空字串:`strSQL += " ,'' RSP_CHG_DATE " …`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:172`),而查詢條件那一段也被註解(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:280-293`)。但 `CheckRspChgDate` 又真的去查 `WHERE RSP_CHG_DATE is not null`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:466-470`)——**欄位有值、刪除時會用到,只是使用者看不到**。xsd 的 Caption 是「產生異動日期」(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM195Model.xsd`)。

**「同一員工只能有一筆未終止資料」這條規則沒有在跑。** 三層外殼都在:

| 層 | 成員 | 錨點 |
|---|---|---|
| PO | `CheckData<T>`,XML doc 寫「檢查同一員工或推薦人是否只存在一筆未終止資料」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:310-449` |
| Control | `CheckData(BasicViewVDB)` | `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM195_Ctl.cs:109-112` |
| FormProxy | `Check(OFDM195ViewVDB)` | `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM195_Pxy.cs:119-125` |

**UI 端唯一的呼叫 `pxy.Check(view)` 被註解**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:163-164`),連同對應的錯誤訊息「此關係人已存在未終止資料,請重新輸入」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:177`)。全 repo 搜 `CheckData` 的呼叫端,`OFDM195` 這條鏈的起點是空的。詳見附錄 E.3。

就算它有在跑,`CheckData` 本身還有兩個問題:條件是 `WHERE REL_STOP_DATE IS NULL`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:332`),而它上一行被註解的舊版是 `REL_STOP_DATE ='1900/01/01'`(`:333`)——**同一個「未終止」語意在這個 repo 有兩種存法**;`REL_STOP_DATE` 是 `xs:string`,Oracle 會把寫入的空字串折成 NULL,所以新資料抓得到,但歷史上用 `'19000101'` 寫進去的抓不到。這與 `cod.md 附錄 E` 記的 `CODM009_PO` 日期哨兵值問題同源。另一個問題是 `ds.Tables["check"].Rows.Count == 0`(正常情況)時**一列結果都不補**(`:416-433`),呼叫端拿到空的 `Result`。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 申請日期為 null 或 `1900/01/01` | 「申請日期 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:118-121` |
| 新增前 | `REL_IDNO` 不是合法身分證也不是合法統編 | 「…不符合正常邏輯,是否忽略?」`No` → 取消;`Yes` → 記 ByPass 訊息後放行 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:310-323` |
| 刪除前 | `CheckRspChgDate` 查到 `RSP_CHG_DATE is not null` 且 `REL_TYPE='1'` | 「該優惠關係人已有系統產生的契約異動資料,是否仍要刪除?」`No` → 取消 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:418-438`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:466-486` |
| 存檔前 | 「同一員工只能一筆未終止」 | **呼叫端被註解,永不觸發** | 記錄不擋(實際等於沒有) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:155-183` |

**`CheckRspChgDate` 是本片唯一寫對的參數化查詢**:`AddInParameter(cmd, "REL_IDNO", OracleDbType.Varchar2, …)`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:471-473`)。其餘的 `CheckData` 與主檔 SQL 全是字串串接(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:194-278`、`:345-394`)。

**跨表更新**:無。`OFD195A` 原本應該被 `CODM009` 在員工離職時同步終止,那段**整塊被註解**(見 §8.5)。

### 4.8 `OFDM197` — 行銷身分別歸屬受益人

- **用途(推測)**:把某個受益人(`BF_NO` / `ID_NO`)掛到某個「行銷身分別」(`MKT_ID`,說明來自 `OFD027A.MKT_DESCRP`)底下,附一個 `BELONG_DATE`(歸屬日期)與 `SOURCE_CD`(資料來源碼)。

- **為什麼重要**:`OFD197A` 是 **`OFDM199` 促銷活動「活動對象 = 身分群族」判定的唯一輸入**(見 §8.3)。這張表錯了,EC 上看得到 / 看不到活動就跟著錯。

- **主鍵是 `MKT_ID` + `ID_NO`**,但 2023 年改成用戶號查詢(`// 改用戶號查詢 by Becky 2023.07.25`,`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:162`),而批次匯入的 delete / insert 也是用 `MKT_ID` + `BF_NO` 當鍵(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:241`)。**寫入用的鍵與表的 PK 不是同一組。**

**〔整條六層是 Big5〕** `OFDM197.cs` / `OFDM197.Designer.cs` / `OFDM197_PO.cs` / `OFDM197_Ctl.cs` / `OFDM197_Pxy.cs` 五個檔都不是合法 UTF-8。用一般編輯器開會看到亂碼,用 `git diff` 看中文也是亂的。詳見附錄 E.7。

**`DoValidate()` 幾乎是空的。** 唯一實質內容(統一編號格式檢查)整段被 `/* */` 包起來(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:56-77`),剩下 `FormvalidatorManager.DataValidate()` 一行。同一個檔裡 `umskID_NO_Validating` 這個事件處理常式**整個方法體都是註解**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:330-349`),註解寫「會跑出多次警告訊息 所以註解」;真正在用的是後來補的 `umskID(bool)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:356-373`)。

**匯入小畫面 `OFDM197p0` 的四個問題**(這是本片最值得盯的一段):

| # | 問題 | 說明 | 錨點 |
|---|---|---|---|
| 1 | **重複檢核查錯 DataTable** | `CheckExists` 跑 `Model.DataEntity.OFDM197`(維護頁的資料表),但匯入畫面只填 `OFDM197B`,而且進畫面時 `VDB.UIView.Clear()` 把全部清空。所以 `CheckExists` 永遠回 `false`,「已有資料是否覆寫」的詢問**永遠不會跳** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:204-214` vs `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:107`、`:118-122` |
| 2 | **`*` 記號寫到不存在的欄** | `CheckExists` 把重複的列標成 `row.BF_NAME = "*"`,但匯入用的 `OFDM197B` DataTable **只有 `BF_NO` 一欄**;而 UI 又去 `Columns["BF_NAME"].Hidden = false` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:209`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:85`、`Dev/ATLAS.OFD/Source/Entity/UIEntity.OFD7/OFDM197View.xsd:123-142` 的 `OFDM197B` 只宣告 `BF_NO` |
| 3 | **第二次匯入的結果沒被檢查** | 使用者按「是」覆寫後再呼叫一次 `BatchAdd`,回傳值指派給 `vdb1` 卻不再判斷,下一行直接顯示「複製成功」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:88-92` |
| 4 | **CSV 讀到空行就停** | `if (line == string.Empty) break;` 中間有一行空白,後面的戶號全部靜默丟掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |

**`BatchAdd` 的 SQL**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247`)是一段匿名 PL/SQL 區塊:先 `delete OFD197A where MKT_ID = :MKT_ID AND BF_NO = :BF_NO`,再 `insert`,`SOURCE_CD` 寫死 `'C'`、`STATUS` 寫死 `'301'`、`ENTRYID` / `VERIFYID` / `APPROVEID` 全填同一個 `:USERID` 同一個 `SYSDATE`。`ID_NO` 用 `NVL((SELECT ID_NO FROM BMS001A WHERE BF_NO = :BF_NO AND ROWNUM=1),' ')` 反查——**查不到就填一個空白**,而表的 PK 是 `MKT_ID` + `ID_NO`,同一次匯入若有兩個查不到的戶號就會撞 PK。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | `umskID(true)`:`ID_NO` 不是合法身分證 / 統編 | 「…不符合正常邏輯,是否忽略?」`No` → 取消 | **詢問** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:188`、`:356-373` |
| 新增 / 修改前 | 歸屬日期 = `1900/01/01` | 「歸屬日期 不可輸入1900/01/01」+ 清空 + `e.Cancel` | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:194-200`、`:232-239` |
| 修改前 | `ID_NO` 格式 | **不檢查**(註解寫「修改時不驗證ID_NO」) | — | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:242-248` |
| 匯入前 | `MKT_ID` 未選 / 歸屬日期未填 / 清單為空 | 三句必填訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:56-73` |
| 匯入中 | CSV 出現重複戶號 | 「戶號 不可重覆,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:124-129` |
| 匯入中 | CSV 出現空行 | 後面的資料全丟 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |
| 匯入中 | 該行銷身分別已有資料 | 「該行銷身份別已有資料(如清單內*號),是否覆寫資料?」 | **詢問(實際不會觸發)** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:232-236` |
| 匯入寫入 | 某列 `ExecuteNonQuery` 回 0 | 「匯入失敗,請檢查資料是否正確」+ 回滾 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:265-270` |
| 匯入全程 | 四眼 | **完全不經過** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |

**匯出範本的編碼是系統 ANSI**:`new StreamWriter(save.FileName, false, Encoding.Default)`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:100`)。在 zh-TW 機器上是 Big5,換到別的 locale 產出的檔會不一樣。〔客戶特定〕

**跨表更新**:`BatchAdd` 讀 `BMS001A` 補 `ID_NO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:245`),不寫入。

### 4.9 `OFDM204` — EC 優惠活動次數上限

本片最小的一支 PO(121 行),但它是 D 塊的**判準來源**:`OFD204.CAMPAIGN_TYPE` 決定一檔活動是不是「開戶優惠」,`OFDM206` 與 BMS 兩邊都靠它。

- **用途(推測)**:針對一檔已存在的促銷活動(`OFD199A.CAMPAIGN_CODE`),設定「單筆可用次數」`ALLOT_TIMES` 與「定額可用次數」`RSP_TIMES`、生效 / 有效期限 `BNG_DATE` / `END_DATE`、活動類型 `CAMPAIGN_TYPE`;明細 `OFD205` 列出這檔活動適用哪些基金。

- **主檔 SQL 直接 `SELECT OFD204.*`,再 `left JOIN OFD199A` 補活動簡稱與起迄時間**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:86-92`)。**注意這裡 join 的是正式表 `OFD199A`,不是 `OFD199A_UPD`**——也就是 `OFDM199` 還沒生效的活動,在 `OFDM204` 上是查不到名稱的(§4.10)。

- **日期是字串拼出來再轉**:`to_date(SUBSTR(OFD199A.CAMPAIGN_BNG_DATE||CAMPAIGN_BNG_TIME,1,12),'yyyymmddHH24MI')`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:88`)。`CAMPAIGN_BNG_DATE` 存 `yyyymmdd`、`CAMPAIGN_BNG_TIME` 存 `HHmm`,兩個字串相接取前 12 碼。**任一欄長度不對(例如時間只存 3 碼)就會 `to_date` 失敗整段查詢炸掉**。

- **明細 SQL 的「所有基金」**:`NVL(OFD081A.FUND_SH_NM,'所有基金')`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:111`)——join 不到基金就顯示「所有基金」。這是**用 join 失敗當語意**,如果只是基金代碼打錯、`OFD081A` 查無此筆,畫面一樣顯示「所有基金」,看不出來是設定錯誤。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:43-48` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:49-52` |
| 存檔前 | `ALLOT_TIMES + RSP_TIMES == 0` | 「'單筆可用次數' 或 '定額可用次數' 必須大於0」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:53-54` |

> ⚠ 第三條用的是**和**,不是各自檢查。`ALLOT_TIMES = -5`、`RSP_TIMES = 5` 加起來是 0 會被擋;但 `ALLOT_TIMES = -1`、`RSP_TIMES = 2` 加起來是 1 **會過**。repo 內沒有看到欄位層級的非負限制。

**修改走的是新增的 handler**(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM204.cs:180-183`),所以修改與新增的檢核完全一致。

**跨表更新**:無。`OFDM204` 只讀 `OFD199A` 與 `OFD081A`。

### 4.10 `OFDM199` — EC 促銷活動設定(`_UPD` 機制)

本片最大也最重要的一支。**如果你只讀一節,讀這節。**

#### 4.10.1 結論先講

> **`_UPD` 是「暫存 → 生效」的暫存側,但只蓋住七張明細中的三張。** `OFDM199` 一次存檔會同時動到七張表:三張費率相關的寫進 `_UPD` 暫存表, 另外四張對象相關的**直接寫正式表**。四眼狀態只掛在 `_UPD` 主檔上。所以覆核通過之前,「這檔活動給誰用」已經改掉了,「這檔活動費率多少」還沒。 **把 `_UPD` 從正式表搬過去的程式,repo 內找不到**——沒有 SP、沒有批次畫面、沒有 Trigger。

這與 `bms.md §2` 的 `CHG` 機制**同型但不同做法**:BMS 是一張表兩組欄位(`BEF_*` / `AFT_*`)+ 一個生效批次 `OFDB003`;OFD7 是兩張同構的表 + 一個看不到的搬運者。相同點是「覆核通過 ≠ 資料生效」,正好印證 `architecture.md §3` 的警告。

#### 4.10.2 證據鏈

| # | 觀察 | 錨點 |
|---|---|---|
| 1 | `OFDM199_PO` 的主檔就是 `OFD199A_UPD`,明細七張裡只有三張帶 `_UPD` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40-47` |
| 2 | 查詢畫面 `OFDI199` 的 PO **是同一份程式碼,只把那三張的 `_UPD` 拿掉**,其餘四張一字不差 | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46` |
| 3 | EC 專案另有一份 `OFDM199AOracleDao`,讀的也是正式表 + 同樣那四張 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:34-43` |
| 4 | 共用 PO 判「這位受益人看得到哪些活動」時,`FROM OFD199A`,而且 `EXISTS` 子查詢分別打 `OFD201A` / `OFD202A` / `OFD200A` / `OFD190A`——**正式表** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4499-4522` |
| 5 | `OFDM204` 與 `OFDM206` 取活動名稱與起迄時,join 的都是 `OFD199A` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM204_PO.cs:91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:126` |
| 6 | 全庫對三張 `_UPD` 表的引用只有 `OFDM199_PO.cs` 一個檔;`DB/SP` / `DB/Trigger` / `DB/View` 底下沒有任何 `_UPD` 相關物件 | 實測 `grep -rl "199A_UPD" Dev/ DB/` 只命中 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` |
| 7 | `OFDM199_PO` 沒有任何 `After*` 事件,`Before*` 也只掛了 `BeforeGetMaintainData` 一個,而且只用來組明細 SQL——**沒有任何把資料搬到正式表的程式** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:39`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:61-82` |

**〔假設〕缺:DB 連線。** 搬運者只能推到「在版控外」為止。三個可能:(a) 一支不在 `DB/SP/` 的 SP(`architecture.md 附錄 B` 說 `DB/` 只涵蓋 16% 的 SP);(b) 一支排程;(c) DBA 手動。**無法從 repo 確認**,也**無法確認搬的是哪些欄位**。

#### 4.10.3 一檔活動的生命週期

| 階段 | 誰做 | `OFD199A_UPD.STATUS` | `OFD199A`(正式) | `OFD201A` `OFD202A` `OFD203A` `OFD687A` |
|---|---|---|---|---|
| 輸入 | `OFDM199` | `Entry*` | 舊值 | **已經是新值** |
| 驗證 | `OFDM199` | `Verify*` | 舊值 | 新值 |
| 覆核 | `OFDM199` | `Approve*` | **仍是舊值** | 新值 |
| 生效 | **未知搬運程序** | 不變 | 變成新值 | 不變 |

第一列的最後一欄是本節最該記住的事:**通路 / 身分群組 / 銷售機構 / 組合基金這四張,輸入當下就改到正式表了**,而 EC 側與共用 PO 直接讀它們(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:39-43`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4502-4513`)。也就是說,**一檔活動的「對象」可以在未覆核狀態下就對外生效,而它的「費率」還停在舊值**——兩半會不一致。列入附錄 E.12。

#### 4.10.4 七張表在畫面上長什麼樣

| 分頁 | vdb 表 | 實體表 | 何時啟用 | 錨點 |
|---|---|---|---|---|
| 基本資料 | `OFDM199` | `OFD199A_UPD` | 永遠 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:40` |
| 單筆(轉)申購基金資料 | `OFDM199_Fund` | `OFD200A_UPD` | `PROMT_ITEM` = `'1'` 申購 或 `'3'` 轉申購 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1229-1244` |
| 定期定額資料 | `OFDM199_RSP` | `OFD190A_UPD` | `PROMT_ITEM` = `'2'` 定期定額 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1245-1252` |
| 通路資料 | `OFDM199_Channel` | `OFD201A` | `CAMPAIGN_OBJ` = `'2'` 通路 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1189-1194` |
| 身分群組資料 | `OFDM199_Mkt` | `OFD202A` | `CAMPAIGN_OBJ` = `'3'` 身分群族 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1195-1200` |
| 銷售機構資料 | `OFDM199_AGENT` | `OFD203A` | `CAMPAIGN_OBJ` = `'4'` 銷售機構 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1201-1206` |
| 組合基金資料 | `OFDM199_PROD` | `OFD687A` | `FUND_OPTION` = `'2'` 且 `PROMT_SCOPE` ≠ `'2'`(非臨櫃) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1273-1287` |
| 優惠券資料 | `OFDM199_Coupon` | `OFD670` | **PO 的宣告被註解,只剩畫面** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:48` |

值域出自 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:827-903`(`PROMT_TYPE` / `PROMT_ITEM` / `PROMT_SCOPE` / `CAMPAIGN_OBJ`)與 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014_AGI.cs:10-21`(`PROMT_TYPE` 的 `'3'` 壽星優惠 / `'4'` 優惠券,寫在另一個 `partial class` 裡)。整理在附錄 C。

#### 4.10.5 主檔 PK 含 `PROMT_SCOPE`,但 `OFD687A` 不含

`OFD199A_UPD` 的 PK 是 `CAMPAIGN_CODE` + `PROMT_SCOPE`(活動範圍),所以**同一個活動代碼在不同範圍(臨櫃 / EC / IVR …)是不同列**。六張明細裡有五張跟著帶 `PROMT_SCOPE`,只有 `OFD687A` 的 PK 是 `COMPAIGN_CODE` + `PRODUCT_ID`。

PO 因此要分兩種條件組法:

```
if (strTableName == this.DetailTable[5].dbTableName)
{ strSQL += this.AddParam(model, strTableName, false, "CAMPAIGN_CODE"); }
else
{ strSQL += this.AddParam(model, strTableName, false, new string[] { "CAMPAIGN_CODE", "PROMT_SCOPE" }); }
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:462-465`)

而且 `AddParam` 裡還有一個**針對欄名拼錯的特例**:

```
if (Table == "OFD687A" && c1 == "CAMPAIGN_CODE")
    strName = Table + "." + "COMPAIGN_CODE";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494`)

**這個 `AddParam` 是自己手寫的,不是共用的 `EVAStringHelper.AddParam`**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:476-517`),而且**完全不綁參數**——把值用單引號包起來直接串進 SQL(`:500-506`、`:513`)。

#### 4.10.6 `GetOFD193` — 帶出牌告費率當對照

使用者在基金分頁按「帶入牌告費率」時,PO 依 `PROMT_SCOPE` 決定去哪張表撈(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:86-149`):

| `PROMT_SCOPE` | 來源表 | 條件 | 欄位對應 |
|---|---|---|---|
| `'3'`(E/C+IVR)或 `'4'`(EC) | `OFD604A` | `FEE_TYPE='1'` | `ALLOT_FEE_RATE2` → `ALLOT_FEE_RATE1`、`ALLOT_FEE_RATE3` → `ALLOT_FEE_RATE2`(**欄名錯開一位**) |
| 其餘 | `OFD193A` | `FEE_TYPE = FEE_TYPE.Forever` | 一對一 |

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:95-126`。查不到時訊息是 `"查無" + strPROMT_SCOPE_DEC + "牌告手續費率"`,`strPROMT_SCOPE_DEC` 只有 `"EC"` 或空字串兩種(`:97`、`:112`、`:136`)——所以境內情況下訊息會變成「查無牌告手續費率」。

**這裡有一個 Oracle 三值邏輯的入口**:`strPROMT_SCOPE` 由 `GetParamValue` 取得,參數不存在就回空字串(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:526-536`),`"" == "4" || "" == "3"` 為 false 就走 `OFD193A` 那一支。**沒有「參數缺失」的錯誤處理**,直接當成非 EC。

#### 4.10.7 卡控總表

`DoValidate()` 在 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:212-328`。

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 必填(`validatorManager1`) | 各欄訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:215-219` |
| 存檔前 | `PROMT_TYPE == "2"` 且 `PROMT_SCOPE` 空 | 「'活動範圍'必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:221-223` |
| 存檔前 | 活動起(日+時) > 迄(日+時) | 「'活動日期時間(起)'必需小於'活動日期時間(迄)'」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:225-228` |
| 存檔前(定額頁啟用時) | 有列 `CAMP_DAY_TYPE == "1"` 且活動起日 > 該列 `BNG_DATE` | 「'定時定額 活動優惠日期(起)'必須大於等於'活動日期(起)'」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:236-248` |
| 存檔前(同上) | 有列 `CAMP_DAY_TYPE == "1"` 且活動迄日 > 該列 `END_DATE` | 「…(迄)必須大於等於'活動日期(迄)'」 | 阻擋(**方向存疑**,見下) | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:240-253` |
| 存檔前 | 基金頁啟用但無列 / 定額頁啟用但無列 | 「基金資料 必須輸入」/「定時定額資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:258-262` |
| 存檔前 | 通路頁啟用:無列 或 有列 `CHANNEL_DESCRP=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:265-272` |
| 存檔前 | 身分群組頁啟用:無列 / `MKT_ID=''` / 列數與 grid 對不上(代表有重複被 Unique 擋掉) | 三句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:274-287` |
| 存檔前 | 銷售機構頁啟用:無列 或 `AGENT_CODE=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:289-296` |
| 存檔前 | 產品頁啟用:無列 或 `PRODUCT_ID=''` | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:298-305` |
| 存檔前 | `PROMT_ITEM` = 轉申購 且 `PROMT_SCOPE` = 臨櫃 | 「轉申購之活動範圍不適用書面」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:307-311` |
| 存檔前 | `PROMT_ITEM` = 轉申購 時,基金列 `CAMP_DISC_TYPE != "2"` | 「轉申購之申購基金手續費率只能設定固定費率」(**逐列各加一次,錯 N 列就跳 N 條**) | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:313-324` |
| 存檔前 | 優惠券活動不同基金設不同折數 | **整段被註解** | 記錄不擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:590-598`、`:614-622`、`:325-327` |
| 存檔前 | 分頁沒啟用 | 該分頁的列**全部清掉**,不提示 | **過濾(無提示)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:66-89` |
| 明細取數 | 只帶 `CAMPAIGN_CODE` + `PROMT_SCOPE`(`OFD687A` 只帶前者) | 條件沒帶到的範圍不出現 | 過濾(無提示) | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:462-465` |

> **「(迄)」那一條的方向存疑。** 兩條檢核都寫 `活動日期 > 該列日期` 就報錯,對「起日」是對的(定額優惠不能比活動早開始),但對「迄日」意思會變成**定額優惠的結束日必須不早於活動結束日**,也就是允許定額優惠比活動晚結束。從業務常識看應該是 `<`(定額優惠不能比活動晚結束)。`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:240` 與 `:236` 的寫法一模一樣,只換了欄位名——典型的複製貼上只改一半。**需求文件不在 repo 內,標「假設」,不改判定**。列入附錄 E.13。

#### 4.10.8 死碼佔 62%

`OFDM199_PO.cs` 1,443 行,其中三大塊是註解:

| 區塊 | 行數 | 內容 | 錨點 |
|---|---|---|---|
| `#region 判斷優惠券之促銷活動是否有匯入名單` | 45 | `Have_COUPON`,查 `OFD671` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:539-583` |
| `#region 複製邏輯mark` | 272 | `GetOFD081` / `GetCampaign` / `CheckCampaign` / `CopyCampaign`,SQL Server 語法 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:586-857` |
| `#region 註解` | 581 | 舊的 `BeforeSelect` / `BeforeGetToDoData` / 主檔 SQL | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:861-1441` |

`OFDM199A_Pxy.cs` 也留了對應的四個 Pxy 方法殼在註解裡(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs:45-148`)。xsd 裡 `GetCampaign` / `CheckCampaign` / `OFDM199_Copy` / `OFD081` 四張 DataTable 也還在,都是這批死碼的殘骸。

**主檔查詢也是死的**:`OFDM199_PO_BeforeGetMaintainData` 裡「取得主檔語法」那一段被註解掉(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:66-72`),現在主檔完全交給框架自動生成的 SQL。`BeforeSelect` 與 `BeforeGetToDoData` 根本沒掛(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:39`)。

**刪除前完全沒有卡控。** `OFDM199_BeforeDeleteButtonClicked` 的方法體**整段是註解**,原本要擋的是「此活動已有設定優惠券名單,不可刪除」(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:1291-1305`)。現在按刪除就直接進四眼刪除流程。

**跨表更新**:無。七張表全部由框架的四眼引擎寫入。

### 4.11 `OFDM206` — EC 優惠活動個人可用次數(BMS 的依賴)

`OFD206` 這張表**主檔持有者是本畫面**,但 `BMSM001`(受益人開戶)把它當明細用(`bms.md §4`)。本節從 OFD 側寫清楚,§8.1 做兩邊對照。

- **用途(推測)**:為某位 EC 網路戶(`BF_SRNO`)在某檔活動(`CAMPAIGN_CODE`)底下,登記單筆 / 定額的可用次數與已用次數。已用次數的明細在 `OFD207`(唯讀顯示)。

- **主檔 SQL**:`SELECT OFD206.*` + 三個 `left JOIN`:`OFD204`(拿 `CAMPAIGN_TYPE` 與 `BNG_DATE`/`END_DATE`)、`OFD199A`(拿活動簡稱與活動起迄)、`OFD601`(拿 `ID_NO` 與 `EC_NAME`)。錨點 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:115-132`。

- **`OFD207` 由 `AfterGetMaintainData` 另外撈**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:98-106`),條件是 `CAMPAIGN_CODE` + `BF_SRNO`。

#### 4.11.1 唯一的伺服端卡控

全片 15 支只有這裡掛了 `BeforeAdd`:

```
if (row.CAMPAIGN_TYPE > 0) return;
… select 1 from OFD206 A JOIN OFD204 B ON A.CAMPAIGN_CODE = B.CAMPAIGN_CODE
  WHERE A.BF_SRNO = :BF_SRNO AND A.CAMPAIGN_CODE <> :CAMPAIGN_CODE AND B.CAMPAIGN_TYPE = 0
args.Cancel = Convert.ToInt32(i) > 0;
args.CancelMsg = "每位受益人只能設定一筆開戶優惠";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77`)

兩個要注意的地方:

1. **`A.CAMPAIGN_CODE <> :CAMPAIGN_CODE` 是 Oracle 三值邏輯的典型位置。** `OFD206.CAMPAIGN_CODE` 是 PK 的一部分理論上不會 NULL,所以目前不會出事;但同型寫法在 CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過,改 schema 時要一起看。列入附錄 E.14(嚴重度低)。

2. **這道卡控只在 `Add` 走框架流程時生效。** `BatchAdd` 與 `BatchAddEC` 是自己下 `insert`,**完全不經過 `BeforeAdd`**——整批匯入可以讓同一位受益人掛上兩筆以上的開戶優惠。列入附錄 E.5。

#### 4.11.2 兩個匯入入口

| 入口 | 畫面 | 輸入 | 做什麼 | 錨點 |
|---|---|---|---|---|
| 「戶號清單」 | `OFDM206p0` | `.TXT` / `.CSV`,一行一個戶號 | 對每個戶號 `insert into OFD206 … select … from OFD204 A CROSS JOIN OFD601 B WHERE CAMPAIGN_CODE = :CAMPAIGN_CODE AND B.BF_NO = :BF_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:159-219` |
| 「EC 整批」 | `OFDM206p1` | 無檔案,只選活動 | `insert … select distinct ofd607A.BF_SRNO … from ofd607a,OFD204 where ofd607a.etraflg='Y' and trim(ofd607a.openday) is not null and CAMPAIGN_CODE = :CAMPAIGN_CODE` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:271-325` |

**`BF_SRNO` 這一欄在匯入流程裡裝的是戶號,不是 EC 流水號。** `OFDM206p0` 把 CSV 每一行 `Convert.ToDecimal` 之後塞進 `row.BF_SRNO`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106`),而且刻意把欄位標題改掉:`e.Layout.Bands[0].Columns["BF_SRNO"].Header.Caption = "戶號";`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:49`)。PO 端再用 `CROSS JOIN OFD601 B … AND B.BF_NO = :BF_NO`(值傳 `row.BF_SRNO`)把戶號換成真正的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:187-196`)。**這是刻意的、不是 bug,但看程式時極容易誤判**,列入附錄 E.15。

同一個混用在 `CheckExists` 造成一個真的問題:重複檢查組出來的條件是 `BF_NO = {r.BF_SRNO}`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:146-148`,字串串接),但回傳給使用者的訊息卻是 `r.BF_SRNO.ToString()` 且**那是查回來的真 `BF_SRNO`**:訊息寫「此優惠活動已存在戶號:」後面接的其實是 EC 流水號(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:155-157`、`:171`)。使用者拿那串數字回去對戶號會對不上。

#### 4.11.3 `CheckData`:一個從用戶端收 SQL 字串來執行的入口

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:221-269` 做的事:

1. 從 `Model.Utility.Parameters` 取出一個以 DataSet 名為鍵的參數,值是**一整串 SQL**;

2. 再取出一個同名參數當**分隔字元**,把那串 SQL 切成多段;

3. 逐段 `cmd.CommandText = strSQLs[i]` 然後 `ExecuteNonQuery`;

4. 是否 `Commit` 由「有沒有一個叫 `OFDM206_PO` 的參數」決定(`:234`、`:256-259`)。

這條路徑**在 repo 內沒有任何 UI 呼叫端**(全庫搜 `CheckData` 的 UI 層呼叫,`OFDM206` 不在其中),但 `OFDM206_Ctl.CheckData`(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM206_Ctl.cs:200-205`)與 `OFDM206_Pxy.CheckData`(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM206_Pxy.cs:48-62`)都在,而 `architecture.md §8` 說 Remoting 邊界就在 UI → FormProxy 之間。**也就是說它是一個對外開放、可以執行任意 SQL 的伺服端入口。** 列入附錄 E.16,嚴重度**高**。

#### 4.11.4 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選活動後 | `OFD204.CAMPAIGN_TYPE` 是 `DBNull`(該活動沒在 `OFDM204` 設過) | 「請先至EC優惠活動設定檔(OFDM204)進行設定」+ 清空欄位 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:148-157` |
| 存檔前 | 單筆已用 > 單筆可用 | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:40-41` |
| 存檔前 | 定額已用 > 定額可用 | 訊息同名 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:42-43` |
| 新增(伺服端) | 該受益人已有另一檔 `CAMPAIGN_TYPE = 0` 的活動 | 「每位受益人只能設定一筆開戶優惠」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77` |
| **刪除前** | 無條件跳「已有使用記錄,是否刪除(Y/N)?」 | **按「是」→ 取消刪除;按「否」→ 執行刪除** | **詢問(方向相反)** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:214-217` |
| 戶號匯入前 | 清單為空 / 未選活動 | 兩句必填訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:54-63` |
| 戶號匯入中 | 檔案某行不是數字 | 「戶號(數字)欄位格式不正確,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106-113` |
| 戶號匯入中 | 檔案有重複戶號 | 「戶號不可重覆,請修正後重新上傳」+ 清空整份 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:118-123` |
| 戶號匯入前(伺服端) | `CheckExists` 查到該活動已有這些戶號 | 「此優惠活動已存在戶號:<清單>」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:168-173` |
| EC 整批前(伺服端) | 該活動已有符合條件的資料 | 「此優惠活動已存在 N 筆欲匯入資料」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:278-291` |
| 兩個匯入 | 「每位受益人只能設定一筆開戶優惠」 | **不檢查** | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| 兩個匯入 | 四眼 | **完全不經過**,狀態寫死 | 記錄不擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185`、`:298` |

> ⚠ **刪除確認那一條是反的。** `e.Cancel = (ShowMessage(...) == DialogResult.OK);` —— 按「確定(是)」得到 `OK`,`e.Cancel` 變成 `true`,刪除被取消;按「否」才會真的刪。同一份 code base 的其他畫面都是相反的慣例(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:427` 是 `== DialogResult.No` 才 `e.Cancel = true`)。而且這個提示**無條件跳**,不管 `OFD207` 有沒有使用記錄。列入附錄 E.6,嚴重度**高**。

**跨表更新**:兩個匯入直接 `insert` 進 `OFD206`,並讀 `OFD204`(次數上限)、`OFD601`(戶號換流水號)、`OFD607A`(EC 開戶旗標)。`OFD607A` 的條件 `etraflg='Y'` 與 `trim(openday) is not null` 都是寫死的〔客戶特定〕(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:300-301`)。

### 4.12 `OFDM213` `OFDM214` `OFDM215` — 匯費與簡碼三胞胎

三支的骨架幾乎一樣,一起讀最省時間。共同點:

| 共同點 | 內容 | 錨點(以 `OFDM214` 為例) |
|---|---|---|
| 多筆型 + 單一 `MasterPKey` | `OFDM213` 用 `FUND_ID`,`OFDM214` / `OFDM215` 用 `BF_NO` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:34` |
| 群首用 `ROW_NUMBER()` 而不是寫死常數 | `ROW_NUMBER() OVER (PARTITION BY BF_NO ORDER BY CreateDate, UpdateDate, EntryDate, FUND_ID) NUM … WHERE NUM = 1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:249-256` |
| 主檔 SQL 把群內才有意義的欄位填成空白 | `OFDM213` 填 `' ' NON_FEE_BANK, ' ' CRNCY_CD`;`OFDM215` 填 `' ' FUND_ID`;**`OFDM214` 沒填,直接帶 `FUND_ID`** | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:219-220`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:266`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:244` |
| 有「複製」功能 | `ExecCopy<T>`,由子對話框呼叫 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:52-79` |
| 有存在性檢查 | `IsFundExsits(string)` / `IsBfExsits(string)`,例外時回 `-1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:87-134` |
| `DoValidate()` 只有兩條 | PK 欄必填 + 明細不可為空 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:36-48` |

用 `ROW_NUMBER()` 比 A / B 兩塊的 `WHERE BNG_AMT = 1` 乾淨很多——**不依賴任何寫死的哨兵值**。同一套系統同一個問題有兩種解法,改的時候要分清楚在哪一群。

#### 4.12.1 `OFDM213` — 基金免收匯費銀行

- **用途(推測)**:某基金某幣別下,哪一家銀行不收匯費(`NON_FEE_BANK`)。明細 SQL 另外 join `OFD094A`(保管銀行)與 `OFD020V` 兩次(一次查不收匯費銀行名、一次查保管銀行名)(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:258-262`)。

- **`IsBfExsits` 查一個不存在的欄。** `SELECT COUNT(1) FROM OFD213A WHERE BF_NO = '…'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:181-183`),但 `OFD213A` 的欄位只有 `FUND_ID` / `NON_FEE_BANK` / `CRNCY_CD` 加四眼欄,**沒有 `BF_NO`**。執行會 `ORA-00904`,被 `catch` 吃掉回 `-1`。這支方法是從 `OFDM214` / `OFDM215` 複製過來忘了刪,而且 `OFDM213p0` 也沒呼叫它。列入附錄 E.8。

- **解構子沒有解除事件訂閱**:`~OFDM213_PO()` 是空的(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:40-43`),另外兩支都有寫 `-=`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:38-43`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:47-52` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:53-56` |
| 格子更新時 | 明細 PK 重複 | 由 `CommonGridHelper.AutoCheckDetailGridCellDuplicatePKeyReturnMsg` 處理 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213.cs:368` |
| 複製前 | 來源基金 = 目的基金 | 「基金代碼 與 複製基金 不可相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213p0.cs:46-49` |
| 複製中 | 來源基金在 `OFD213A` 查無資料 | 「來源基金 XXX 不存在,請重新選擇」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:81-85` |
| 複製中 | 目的基金已有資料 | 「複製基金 XXX 己存在,請重新選擇」 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:93-97` |

#### 4.12.2 `OFDM214` — 受益人 × 基金 匯費收取碼

- **用途(推測)**:`REMIT_CODE`(贖回匯費收取碼)與 `DIV_REMIT_CODE`(收益分配匯費收取碼),一位受益人一檔基金一組。

- **`FUND_ID` 可以是字面值 `'ALL FUNDS'`**:明細 SQL 用 `CASE OFD214A.FUND_ID WHEN 'ALL FUNDS' THEN CAST('所有基金' AS NVARCHAR2(100)) ELSE OFD081A.FUND_SH_NM END`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:281-283`)。這是寫死的魔術字串,`OFDM215` 也有同一段(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:301-302`),但**兩邊的型別轉換寫法不同**(`CAST(… AS NVARCHAR2(100))` vs `TO_CHAR(…)`)。

- **複製有兩種**:複製受益人(`OFDM214p0`)與複製基金(`OFDM214p1`),分別對應 `CooyBF_NO`(方法名拼錯)與 `CopyFUND_ID`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:142-233`)。

- **複製時 `STATUS` 不清空**:`row.STATUS = row.STATUS;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:149`)是自我指派,等於什麼都沒做。其他四眼欄位全部被清成空字串 + `1900/1/1`,唯獨 `STATUS` 保留來源的值。對照 `OFDM213` 的同一段是 `row.STATUS = string.Empty;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:118`)與 `OFDM194` 的 `row.STATUS = "";`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:273`)。**三支同型功能,兩支清一支不清**。列入附錄 E.9。

- **`CopyFUND_ID` 連 `DATAID` 一起複製**:`newrow.DATAID = row.DATAID;`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:183`),註解說「針對每個受益人要寫一個 TODO 和相同的 STATUS,dataid」——是刻意的,但要知道複製出來的列與來源列共用同一個 `DATAID`。

**明細 SQL 的 `IN` 是字串拼出來的:**

```
string strParam = EVAStringHelper.GetParamValue(args.ModelVDB, "BF_NO");
if (strParam != "")//因應複製功能會用子查詢
    strSQL += "AND OFD214A.BF_NO	IN (" + strParam + ")                 \n";
```

(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:290-292`)

`ExecCopy` 會把**一整句 `SELECT`** 當成參數值傳進來:`AddParametersRow("BF_NO", SQLOperator.IN, "SELECT BF_NO FROM OFD214A WHERE FUND_ID='" + rowCopy.FROMFUND_ID + "'")`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:61-62`)。也就是:**參數值直接當 SQL 片段用,而且那句 SQL 自己又是字串串接出來的**。`OFDM215` 同型(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:73-74`、`:308-310`)。列入附錄 E.17。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 存檔前 | 明細有列但 PK 欄未填 | 「<欄名> 為必填欄位」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:40-45` |
| 存檔前 | 明細列數為 0 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214.cs:46-49` |
| 複製受益人前 | From = To | 「From 戶號與To 戶號不可相同」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:58-59` |
| 複製受益人前 | `IsBfExsits` 回 `-1`(查詢本身出錯) | 「檢核失敗,請檢查」 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:64-65`、`:69-70` |
| 複製受益人前 | From 戶號查無資料 / To 戶號已有資料 | 兩句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:66-72` |
| 複製基金前 | 同上三條,對象換成基金代碼 | 三句訊息 | 阻擋 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p1.cs:122-137` |
| 複製寫入 | `ApplicationException` | 直接把 `appEx.Message` 當訊息顯示 | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:215-221` |
| 複製寫入 | 其他例外 | 「複製失敗,請檢查」+ **附上 `ex.Message`** | 阻擋 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:222-229` |

#### 4.12.3 `OFDM215` — 受益人 × 基金 簡碼

與 `OFDM214` 是同一份程式碼改出來的,只把 `REMIT_CODE` / `DIV_REMIT_CODE` 換成 `SHORT_CODE`。**三個差異值得記**:

| 差異 | `OFDM214` | `OFDM215` | 錨點 |
|---|---|---|---|
| 複製分支判斷 | 看 `OFDM214_Copy` DataTable 的 `FROMFUND_ID` / `FROMBF_NO` 哪個有值 | 看 `Utility.Parameters` **有沒有** `BF_NO` / `FUND_ID` 這個參數 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:58-76` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:62-80` |
| 一般例外的處理 | `AddResultRow` **後**還呼叫 `CommonExceptionBlocker.HandleBusinessException(ex)` | **沒有呼叫**,例外不進 log | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:228` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:178-184` |
| 主檔 `FUND_ID` | 帶真值 | 填 `' '` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:244` vs `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:266` |

第二條列入附錄 E.9:**同一段 `catch` 抄了兩份,一份有記 log 一份沒有**。兩份都把 `ex.Message` 串進給使用者看的訊息裡(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:227`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:183`)。

**卡控總表**與 `OFDM214` 同構,錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215.cs:32-45`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215p0.cs:52-68`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM215p1.cs:88-104`。

**跨表更新(三支共通)**:複製功能會跨 `dbProduct` 與 `dbPTPF` 兩個連線開交易(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:207-211`),`dbPTPF` 是平台的 ToDo 庫。除此之外不寫別的表。

## 5. 查詢畫面(I)

**本片無此類畫面。**原因:切片的依據是 `DataEntity.OFD7` 這個 Entity 專案,而 ATLAS 的查詢畫面(`*I*`)的 Model / View 一律放在 `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD` 與 `QueryUIEntity.OFD`(`architecture.md §6`),不會出現在 `DataEntity.OFD7` 裡。

同主題的查詢畫面 `OFDI199` 在 OFD.Query 專案。它**不屬於本片**,但對理解 `_UPD` 不可或缺:它的 PO 與 `OFDM199_PO` 是同一份程式碼,差別只在三張表沒有 `_UPD` 字尾(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39-46`)。**會把資料濾掉而不提示的條件**:它讀的是正式表,所以 `OFDM199` 剛存還沒生效的內容,在 `OFDI199` 上完全看不到,而且沒有任何提示說「有一份未生效的版本」。

## 6. 批次(B)與 WindowsService

**本片無此類畫面。**`DataEntity.OFD7` 底下沒有 `*B*Model.xsd`,`Dev/ATLAS.OFD/Source/UI/UI.OFD/` 底下也沒有繼承 `xOneStepProcessForm` 的 `OFDB*` 畫面——OFD 的批次畫面全在 `Dev/ATLAS.OFDB` 這個獨立專案。

三個**看起來像批次、實際上不是**的東西,放在這裡一起講清楚:

| 入口 | 實際型態 | 有沒有四眼 | 錨點 |
|---|---|---|---|
| `OFDM197p0`(行銷身分別 CSV 匯入) | `OFDM197` 的 `DoExp1` 開出的 `Form` 對話框 | **沒有**,SQL 直接寫 `STATUS = '301'` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197.cs:85-91`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:240-247` |
| `OFDM206p0`(戶號清單匯入) | `OFDM206` 的 `DoExp1` | **沒有** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:180-186`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206p1`(EC 整批匯入) | `OFDM206` 的 `DoExp2` | **沒有** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:187-193`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

**與 M 畫面的關係**:三個都直接寫 M 畫面的主表,但**跳過 M 畫面所有的伺服端卡控**。`OFDM206` 的「每位受益人只能設定一筆開戶優惠」掛在 `BeforeAdd`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:60-77`),兩個匯入都不會經過。

**失敗處理**:三個都是「某一筆 `ExecuteNonQuery` 回 0 就整批 `Rollback`」(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:265-270`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:200-205`)。三個的 `catch` 都是 `tran.Rollback()` 開頭——**如果例外發生在 `BeginTransaction()` 本身,`tran` 是 `null`,`catch` 區塊會再丟一個 `NullReferenceException`,把原始例外蓋掉**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:276-282`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:211-217`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:318-324`)。列入附錄 E.18。

**WindowsService**:本片與四支 WindowsService(`architecture.md §8`)沒有任何關係。

## 7. 報表(R)

**本片無此類畫面。**`DataEntity.OFD7` 底下沒有報表 Model;依 `architecture.md §6` 的命名鐵律,報表的六層在 `.Report` 專案,不會出現在這裡。

| rpt | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| —(本片無) | — | — | — |

要找這 15 支畫面相關的報表,得往 `Dev/ATLAS.OFD.Report` 找,而且 `architecture.md 附錄 C` 提醒過:repo 內的 `.rpt` 檔與程式引用的檔名有一批對不上,查之前先確認。

## 8. 跨模組共用

```text
[圖] OFD7 五組跨模組共用：OFD206 給 BMS、OFD204 判準、OFD197A 餵活動對象、六張表被 OFDB004 共寫、OFD195A 與 COD
圖中文字:A：OFD206 —— 主檔在 OFDM206，BMS 把它當明細 / OFDM206〔OFD7〕 / 主檔持有者 有四眼 / OFD206 / PK EC流水號+活動代碼 / BMSM001〔BMS〕 / 當明細 掛在開戶 / BMS 側先整批刪 / 只用 EC流水號當條件 / B：OFD204 —— OFDM206 與 BMS 都拿它來判活動類型 / OFDM204〔OFD7〕 / 唯一維護入口 / OFD204 OFD205 / 次數上限與適用基金 / CAMPAIGN_TYPE = 0 / 兩邊都用它認開戶優惠 / 兩邊判準一致 / 對得上 / C：OFD197A —— 本片維護，卻是促銷活動對象判定的輸入 / OFDM197〔OFD7〕 / OFD197A 身分別歸屬 / OFD202A / OFDM199 設的身分群組 / BasicOFD_PO / OFD_PO / 兩支共用 PO 各一份 / EC 活動清單 / 有沒有資格看這裡 / D：六張費率與設定表 —— OFDB004 一次建檔批次也在寫 / OFDM193 OFDM194 OFDM196 / 逐支維護 / OFDM213 OFDM214 OFDM215 / 逐支維護 / OFDB004〔OFDB〕 / 六張全當明細一起建 / 兩條寫入路徑 / 卡控完全不同 / E：OFD195A —— COD 原本要同步維護，整段被註解 / OFDM195〔OFD7〕 / 目前唯一寫入者 / OFD195A / 優惠關係人 / CODM009 CODM010 / 只查不寫 跳警示不擋 / 離職不會自動終止 / cod.md 記同一件事
```

*圖:圖 5 跨模組。橘框=本片的維護入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼或共用 PO。A 與 B 兩組與 bms.md 對得上;D 的兩條寫入路徑（畫面與 OFDB004）卡控完全不同，是最容易出事的一組。*

本片 23 張表裡有 14 張被別的模組或別支畫面碰到。五組「借法」完全不同,分開講。

### 8.1 `OFD206` — 主檔在 `OFDM206`,`BMSM001` 當明細(與 `bms.md` 對照)

**兩邊都在寫同一張表,而且寫法不同。**

| 面向 | OFD 側(`OFDM206`) | BMS 側(`BMSM001`) |
|---|---|---|
| 角色 | 主檔持有者,`xTableMapping("OFD206", "OFDM206")` | 明細,`xTableMapping("OFD206", "OFD206")` |
| 錨點 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:44` | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:158` |
| 寫入前的清理 | 無(靠 `BeforeAdd` 擋重複) | `BeforeAdd` 先 `Delete_OFD206` 整批刪 |
| 清理範圍 | — | `DELETE FROM OFD206 A WHERE A.BF_SRNO = :BF_SRNO AND EXISTS (SELECT 1 FROM OFD204 B WHERE A.CAMPAIGN_CODE = B.CAMPAIGN_CODE AND B.CAMPAIGN_TYPE = 0)`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1859`) |
| 「開戶優惠」的判準 | `OFD204.CAMPAIGN_TYPE = 0`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:70`) | `OFD204.CAMPAIGN_TYPE = 0`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1859`) |

**判準一致,對得上。** 兩邊都用 `OFD204.CAMPAIGN_TYPE = 0` 認定「開戶優惠」,這一點與 `bms.md §4` 記的內容相符;`bms.md §8` 把 `OFD206` 列為「OFD / EC優惠活動 / `BMSM001` 明細」,也與本片一致。

**三處對不上或要補充的:**

| # | 差異 | 說明 |
|---|---|---|
| 1 | **欄數** | `bms.md §2` 的母體表記 `OFD206` **12 欄、四眼「只有 `*DATE`」**;現在跑 `atlas_scan.py --table OFD206` 得到 **21 欄、四眼「有」**,欄位定義來源是 `Dev/ATLAS.BMS/Source/Entity/DataEntity.BMS/BMSM001Model.xsd`。OFD 側的 `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD7/OFDM206Model.xsd` 也是同樣 21 欄(其中 8 欄是 join 進來的顯示欄,vdb 共 29 欄)。**兩份 xsd 的實體欄位一致,`bms.md` 那個 12 是舊一輪掃描器的數字**(`architecture.md 附錄 D.3` 記過掃描器修過兩輪,`帶四眼欄位` 從 37 修成 158)。建議 `bms.md` 回頭對一次。 |
| 2 | **BMS 載入時只取一筆** | `sb.AppendLine(@" SELECT OFD206.* FROM OFD206,OFD601 WHERE OFD601.BF_SRNO = OFD206.BF_SRNO AND ROWNUM = 1 AND OFD601.BF_NO = " + strBF_NO + ";")`(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1129`)——`ROWNUM = 1` 且**不篩 `CAMPAIGN_TYPE`**。另一條載入路徑有篩(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:3215-3219`)但也是字串串接。`bms.md` 沒有記到這兩條。 |
| 3 | **刪除只用 `BF_SRNO` 當條件** | `Delete_OFD206` 的 `CAMPAIGN_CODE` 綁定參數那一行**被註解**(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1863`),所以刪的是該受益人**全部**的開戶優惠列,不是某一檔。 |

**#2 + #3 合起來是一條資料流失路徑(〔假設〕,未實測):** 如果一位受益人在 `OFD206` 有兩列以上 `CAMPAIGN_TYPE = 0` 的資料(`OFDM206` 的 `BeforeAdd` 會擋,但 §4.11 說的兩個批次匯入**不會擋**),則 `BMSM001` 載入時只讀到一列,存檔時 `Delete_OFD206` 把兩列都刪掉,再寫回一列 —— **另一列靜默消失**。要確認需要 DB 資料,repo 內無法驗證。列入附錄 E.24。

**BMS 側另外兩處會覆寫 `BF_SRNO`**:`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1398-1402` 與 `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1458-1461`,把新產生的 EC 流水號回填到明細列上。OFD 側沒有對應動作。

### 8.2 `OFD204` — 兩個模組共用同一個「活動類型」判準

`OFD204` 的唯一維護入口是 `OFDM204`(§4.9),但它的 `CAMPAIGN_TYPE` 被三個地方讀:

| 讀的人 | 用途 | 錨點 |
|---|---|---|
| `OFDM206` 的 `BeforeAdd` | 只有 `CAMPAIGN_TYPE = 0` 才擋「一人一筆」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-70` |
| `OFDM206` 的主檔 SQL | 帶出 `CAMPAIGN_TYPE` 給畫面顯示 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:117` |
| `BMSM001` 的 `Delete_OFD206` | 只刪 `CAMPAIGN_TYPE = 0` 的列 | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1856-1859` |

**改 `OFD204.CAMPAIGN_TYPE` 的值域等於同時改 BMS 的行為。** repo 內找不到 `CAMPAIGN_TYPE` 的代碼字典(`CTL014.cs` 沒有這一組),`0` 代表開戶優惠是從程式反推的**推測**。

### 8.3 `OFD197A` — 本片維護,卻是促銷活動對象判定的輸入

這是本片五塊業務線之間唯一的真依賴。共用 PO 判斷「這位受益人 / 這個身分別看得到哪些促銷活動」時,會把 `OFD202A`(`OFDM199` 設的身分群組)join 到 `OFD197A`(`OFDM197` 設的歸屬):

| 共用 PO | 片段 | 錨點 |
|---|---|---|
| `BasicOFD_PO` | `LEFT JOIN OFD197A ON OFD197A.MKT_ID=OFD202A.MKT_ID … AND OFD197A.ID_NO LIKE :ID_NO` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4510-4514` |
| `OFD_PO` | 同樣的 join,另外多一個 `OFD197A.BELONG_DATE <= TO_CHAR(:VALID_DATE,'yyyymmdd')` | `Dev/Common/Source/DataSource/PO.DataSource/OFD_PO.cs:127-131` |

**兩份 SQL 的條件不一樣**:`OFD_PO` 那份會比歸屬日期,`BasicOFD_PO` 那份不會。同一個問題兩個答案,呼叫哪一支決定結果。改 `OFDM197` 之前要先確認下游用的是哪一份。

### 8.4 六張費率與設定表 — `OFDB004` 一次建檔批次也在寫

`OFDB004`(主檔 `OFD081A`,即「複製一檔基金的全部設定」)把本片六張表當明細一起建:

| 表 | 本片畫面 | `OFDB004` 的 vdb 名 | 錨點 |
|---|---|---|---|
| `OFD193A` | `OFDM193` | `OFDM193` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:64` |
| `OFD194A` | `OFDM194` | `OFDM194` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:65` |
| `OFD196A` | `OFDM196` | `OFDM196` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:66` |
| `OFD213A` | `OFDM213` | `OFDM213` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:69` |
| `OFD214A` | `OFDM214` | `OFDM214` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:70` |
| `OFD215A` | `OFDM215` | `OFDM215` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB004_PO.cs:71` |

**兩條寫入路徑的卡控完全不同。** 走 `OFDM193` 進來會被 §4.3 那一整串檢核擋;走 `OFDB004` 進來只有 `OFDB004` 自己的檢核。特別是 A / B 兩塊「群首靠 `WHERE BNG_AMT = 1` 抓」這件事(§4.1):**`OFDB004` 複製出來的資料如果第一階不是從 1 開始,在 `OFDM193` / `OFDM194` / `OFDM196` 上就查不到也改不到**。`OFDB004` 是否保證第一階為 1,要讀 `OFDB004_PO` 的複製邏輯才知道,不在本片範圍。

### 8.5 `OFD195A` — COD 原本要同步維護,整段被註解

`cod.md §4` 已經記過:`CODM009`(員工資料維護)的 `AfterUpdate` 與 `AfterDelete` 裡維護 `OFD195A` 的程式**整塊被 `/* */` 包起來**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:81-248`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:253-274`),只剩「查到有資料就跳 `Warn01` 但不擋」的提示。

**從 OFD7 側確認:`OFD195A` 現在唯一的寫入者就是 `OFDM195`。** 兩邊說法一致。實務後果:員工離職 / 轉非正式時,`OFD195A` 的 `REL_STOP_DATE` **不會自動補**,要人工進 `OFDM195` 改;而 `OFDM195` 那條「一人只能一筆未終止」的檢核又沒在跑(§4.7)——**兩邊的防線同時是空的**。

### 8.6 促銷活動的四張對象表 — EC 與 OFD.Query 直接讀

`OFD201A` `OFD202A` `OFD203A` `OFD687A` 沒有 `_UPD` 分身,由 `OFDM199` 直接寫正式表,而下列三方直接讀:

| 讀的人 | 錨點 |
|---|---|
| `OFDI199`(OFD.Query) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:42-46` |
| EC 專案的 `OFDM199AOracleDao` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDM199AOracleDao.cs:39-43` |
| 共用 PO `BasicOFD_PO`(判活動對象) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs:4502-4513` |

這是 §4.10 那個「一半立即生效」問題的下游端。

### 8.7 影響面速查

改本片的東西時,要一起看的清單:

| 改什麼 | 要一起看 |
|---|---|
| `OFD206` 的欄位或 PK | `BMSM001`(明細)+ `bms.md §2` 的母體表 |
| `OFD204.CAMPAIGN_TYPE` 的值域 | `OFDM206` 的 `BeforeAdd` + `BMSM001` 的 `Delete_OFD206` |
| `OFD197A` 的 `MKT_ID` / `BELONG_DATE` | `BasicOFD_PO` 與 `OFD_PO` 兩份活動對象 SQL(條件不同) |
| `OFD193A` / `OFD194A` / `OFD196A` / `OFD213A` / `OFD214A` / `OFD215A` 的欄位 | `OFDB004` 的明細宣告 + 各自畫面 |
| `OFD195A` | `CODM009` / `CODM010` 的唯讀檢核(`cod.md §4`) |
| `OFD199A` 系列的欄位 | `OFDI199` + EC 的 `OFDM199AOracleDao` + `BasicOFD_PO` + `OFD_PO` + `OFDM204` + `OFDM206`,**共六處** |
| `OFD201A` / `OFD202A` / `OFD203A` / `OFD687A` | 同上,而且改完立即對外生效 |

## 附錄 A. 資料表總表

### A.1 本片宣告的 23 張實體表

| 表 | 主檔於 | 明細於(本片) | 被誰共用 | 欄位定義 xsd |
|---|---|---|---|---|
| `OFD191` | `OFDM191` | — | — | `OFDM191Model.xsd` 的 `OFDM191` |
| `OFD192` | `OFDM192` | — | OTAB 專案有引用 | `OFDM192Model.xsd` 的 `OFDM192` |
| `OFD193A` | `OFDM193` | — | `OFDB004` 明細、`OFDM199.GetOFD193` 讀、Common | `OFDM193Model.xsd` 的 `OFDM193` |
| `OFD194` | `OFDM194B` | — | `OFDB004` 有引用 | `OFDM194BModel.xsd` 的 `OFDM194B` |
| `OFD194A` | `OFDM194` | — | `OFDB004` 明細、NFD.Report | `OFDM194Model.xsd` 的 `OFDM194` |
| `OFD195A` | `OFDM195` | — | COD 唯讀、RSP、Common | `OFDM195Model.xsd` 的 `OFDM195` |
| `OFD196A` | `OFDM196` | — | `OFDB004` 明細 | `OFDM196Model.xsd` 的 `OFDM196` |
| `OFD197A` | `OFDM197` | — | Common 兩支活動對象 PO、BMS、RSP、OFDB | `OFDM197Model.xsd` 的 `OFDM197` |
| `OFD198` | `OFDM198` | — | — | `OFDM198Model.xsd` 的 `OFDM198` |
| `OFD199A_UPD` | `OFDM199` | — | **無** | `OFDM199Model.xsd` 的 `OFDM199` |
| `OFD200A_UPD` | — | `OFDM199` | **無** | `OFDM199Model.xsd` 的 `OFDM199_Fund` |
| `OFD190A_UPD` | — | `OFDM199` | **無** | `OFDM199Model.xsd` 的 `OFDM199_RSP` |
| `OFD201A` | — | `OFDM199` | `OFDI199`、EC、Common、OFDB | `OFDM199Model.xsd` 的 `OFDM199_Channel` |
| `OFD202A` | — | `OFDM199` | 同上 | `OFDM199Model.xsd` 的 `OFDM199_Mkt` |
| `OFD203A` | — | `OFDM199` | `OFDI199`、EC、Common | `OFDM199Model.xsd` 的 `OFDM199_AGENT` |
| `OFD687A` | — | `OFDM199` | 同上 | `OFDM199Model.xsd` 的 `OFDM199_PROD` |
| `OFD204` | `OFDM204` | — | `OFDM206`、BMS、Common | `OFDM204Model.xsd` 的 `OFDM204` |
| `OFD205` | — | `OFDM204` | — | `OFDM204Model.xsd` 的 `OFD205` |
| `OFD206` | `OFDM206` | — | **`BMSM001` 明細** | 兩份:`OFDM206Model.xsd` 的 `OFDM206` 與 `BMSM001Model.xsd` 的 `OFD206` |
| `OFD207` | — | (唯讀補撈) | — | `OFDM206Model.xsd` 的 `OFD207`;掃描器歸為 dataset |
| `OFD213A` | `OFDM213` | — | `OFDB004` 明細 | `OFDM213Model.xsd` 的 `OFDM213` |
| `OFD214A` | `OFDM214` | — | `OFDB004` 明細、NFD.Report | `OFDM214Model.xsd` 的 `OFDM214` |
| `OFD215A` | `OFDM215` | — | `OFDB004` 明細 | `OFDM215Model.xsd` 的 `OFDM215` |

> ⚠ **「掃描器說欄位 0」不等於沒有定義。** 對 `OFD191` 跑 `atlas_scan.py --table OFD191` 會得到「欄位 0」,原因與 `bms.md §2` 記的一樣:**xsd 的 DataTable 名跟實體表名不同**(`new xTableMapping("OFD191", "OFDM191")`)。本片 23 張表裡有 20 張是這種情形,只有 `OFD205` `OFD206` `OFD207` 三張的 vdb 名與實體表名相同(或另有一份同名定義),掃描器才查得到欄位。要查欄位得照上表最後一欄去對應的 xsd 找。

### A.2 只讀不寫的外部表

`OFD081`(境外基金)、`OFD081A`(境內基金)、`OFD0811A`(基金警語)、`OFD062`(基金公司)、`OFD068A`(銷售機構)、`OFD072A`(推薦人)、`BMS001A`(受益人)、`COD009`(員工)、`OFD027A`(行銷身分別)、`OFD601`(EC 網路戶)、`OFD607A`(EC 權限)、`OFD094A`(保管銀行)、`FSK003`(幣別)、`OFD020V`(銀行分行,用兩次別名 `OFD020V2`)、`OFD604A`(EC 牌告費率)、`OFD199A`(正式促銷活動主檔,被 `OFDM204` / `OFDM206` join)。

`FSK003` `OFD020V` `OFD604A` 三個不在掃描器索引裡(母體沒收),已加進 meta 的 `refcheck-ignore`。

## 附錄 B. SP / Function / Trigger / View

**本片沒有任何自己的 SP、Trigger 或 View。** 23 張表上沒有掛 Trigger(`DB/Trigger/` 13 支裡沒有一支對應),`DB/SP/` 底下也沒有 `OFD19*` / `OFD20*` / `OFD21*` 相關的檔。

用到的 DB 端物件只有一個:

| 物件 | 型別 | 用途 | 呼叫端 | repo 內有原始碼? |
|---|---|---|---|---|
| `F_TA_GETAGENT` | Function(回 table) | `OFDM199` 的銷售機構明細取機構簡稱:`SELECT AGENT_SHNM FROM TABLE(F_TA_GETAGENT()) OFD068A WHERE …` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:329-330` | **無**,已加進 `refcheck-ignore` |

**`_UPD` → 正式表的搬運者不在這張表上,因為 repo 內找不到它**(§4.10)。若它存在,依 `architecture.md 附錄 B` 的說法(`DB/` 只涵蓋 16% 的 SP),很可能是一支沒進版控的 SP。

## 附錄 C. 代碼對照

全部來自 `Dev/Common/Source/MappingCode/TA.MappingCode/`,不是自己翻的。

| 代碼組 | 值 | 意義 | 錨點 |
|---|---|---|---|
| `SHORE_ID` / `FUND_TYPE` | `1` / `2` | 境外基金 / 境內基金 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:291-301` |
| `FEE_TYPE` | `1` / `2` | 永久費率 / 某期間費率 | `Dev/Common/Source/MappingCode/TA.MappingCode/OFDCode.cs:187-197` |
| `RSP_ID` | `Y` / `N` | 可 / 不可作定期定額申購 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277-287` |
| `AFEE_TYPE` | `1` / `2` | 前收 / **後收** | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3533-3544` |
| `PROMT_TYPE` | `1` / `2` / `3` / `4` | EVENT / CAMPAIGN / 壽星優惠 / 優惠券 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:827-838` + `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014_AGI.cs:10-21` |
| `PROMT_ITEM` | `1` / `2` / `3` | 申購 / 定期定額 / 轉申購 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:842-855` |
| `PROMT_SCOPE` | `1` ~ `5` | 所有管道 / 臨櫃 / E/C+IVR / EC / IVR | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:859-881` |
| `CAMPAIGN_OBJ` | `1` ~ `4` | 所有受益人 / 通路 / 身分群族 / 銷售機構 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:885-903` |
| `CAMP_DAY_TYPE` | `1` / `2` / `3` | 優惠日期區間 / 優惠月數 / 優惠次數 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3278-3292` |
| `CAMP_DISC_TYPE` | `1` / `2` / `3` | 優惠折數 / 折扣金額 / 固定優惠費率 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:3296-3310` |
| `MKT_SOURCE_CD` | `M` / `C` | 輸入 / 批次轉入 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2586-2596` |
| `REL_TYPE` | `1` / `2` | 員工 / 推薦人 | `Dev/Common/Source/MappingCode/TA.MappingCode/BMSCode.cs:11-21` |

**兩個查不到字典、只能推測的:**

| 代碼 | 觀察到的值 | 推測 | 依據 |
|---|---|---|---|
| `CAMPAIGN_TYPE` | `0` 與 `> 0` | `0` = 開戶優惠 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:64-76` 的訊息「每位受益人只能設定一筆開戶優惠」 |
| `STATUS` 的 `'301'` | 批次匯入寫死 | 已覆核新增(`EVAStatusCode.ApproveAdd`) | 三段 SQL 同時填滿 `ENTRYID`/`VERIFYID`/`APPROVEID`;但與 `architecture.md §3` 記的「單字元字面值」不符,**未確認** |

**一個字典與註解打架的地方**:`AFEE_TYPE = "2"` 字典寫「後收」,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:409-410` 的註解寫「混收型」。本文以字典為準,同時把這個差異記在這裡。

## 附錄 D. 掃描母體與覆蓋率

`atlas_scan.py --module OFD` 對單片沒有意義(OFD 有 550 支),所以改成逐支列。

### D.1 15 支畫面的處置

| # | 畫面 | 處置 | 章節 | 深度 |
|---|---|---|---|---|
| 1 | `OFDM191` | 已寫 | §4.1 | 一支一節 |
| 2 | `OFDM192` | 已寫 | §4.2 | 一支一節 |
| 3 | `OFDM193` | 已寫 | §4.3 | **深寫**(境內外機制 + 缺陷) |
| 4 | `OFDM194` | 已寫 | §4.4 | **深寫**(成對比較) |
| 5 | `OFDM194B` | 已寫 | §4.4 | **深寫**(成對比較) |
| 6 | `OFDM196` | 已寫 | §4.5 | **深寫** |
| 7 | `OFDM198` | 已寫 | §4.6 | 一支一節 |
| 8 | `OFDM195` | 已寫 | §4.7 | **深寫**(死碼 + 無呼叫端檢核) |
| 9 | `OFDM197` | 已寫 | §4.8 | **深寫**(匯入 + 編碼) |
| 10 | `OFDM204` | 已寫 | §4.9 | 一支一節 |
| 11 | `OFDM199` | 已寫 | §4.10 | **最深**(`_UPD` 機制) |
| 12 | `OFDM206` | 已寫 | §4.11 | **深寫**(BMS 依賴) |
| 13 | `OFDM213` | 已寫 | §4.12.1 | 群組節 |
| 14 | `OFDM214` | 已寫 | §4.12.2 | 群組節 |
| 15 | `OFDM215` | 已寫 | §4.12.3 | 群組節 |

**15 / 15 = 100%**,沒有「無關」或「停用」需要處置的。

### D.2 表的覆蓋率

| 對象 | 母體 | 本文明確引用 | 覆蓋 |
|---|---|---|---|
| 本片宣告的實體表 | 23 | 23(附錄 A.1 全列) | 100% |
| 外部唯讀表 | 16 | 16(附錄 A.2 全列) | 100% |
| DB 物件 | 1 | 1(附錄 B) | 100% |
| 子對話框 | 14 | 14(§3.1) | 100% |
| 代碼組 | 12 + 2 推測 | 14(附錄 C) | 100% |

### D.3 本文沒做到的事

| 項目 | 原因 |
|---|---|
| `_UPD` → 正式表的搬運程式 | repo 內不存在,需要 DB 連線 |
| `'301'` 是不是 `ApproveAdd` | `EVAStatusCode` 在 DLL 裡,需要反編譯或查 DB |
| `CAMPAIGN_TYPE` 的完整值域 | 沒有代碼字典 |
| `DISC_CODE`(優惠專案)的值域 | 自由輸入,沒有字典也沒有檢核 |
| `LevelGridUtility` / `xMaintainForm` / `BaseEVADaoPO` 的內部行為 | 框架 DLL,無原始碼,從呼叫端反推 |
| `OFDB004` 複製出來的資料第一階是不是從 1 開始 | 不在本片範圍 |

## 附錄 E. 讀本文時要注意的地方

18 + 6 條,依嚴重度排。

### E.1 逐年遞減檢核掛在錯的分支,永遠不會成立 —— 嚴重度 **高**

`OFDM193` 與 `OFDM196` 兩支,寫法一模一樣:

```
if (Convert.ToString(this.uoptFUND_TYPE.Value) == "1")
{
    //境內境金        ← 註解是錯的,"1" 是境外
    … 檢查 ALLOT_FEE_RATE > ALLOT_FEE_RATE1 > ALLOT_FEE_RATE2 …
    this.ValidateErrList.AddError(this.ugrdOFDM193, "手續費率需符合逐年遞減原則，請檢查手續費率!!");
}
```

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:64-75`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:109-124`。

**為什麼形同虛設:**

| 步驟 | 事實 | 錨點 |
|---|---|---|
| 1 | `"1"` 是境外(`SHORE_ID.OffShore`) | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:298-300`;同檔 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:141-144` 的「預設境內基金」接 `= "2"` |
| 2 | 境外時 `RATE1` / `RATE2` 欄被隱藏 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:599-602` |
| 3 | 境外時 `RATE1` / `RATE2` 格子禁止編輯 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:627-636` |
| 4 | 境外時存檔前 `RATE1` / `RATE2` **強制歸零** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:96-101` |
| 5 | 檢核式子是 `(RATE == 0 && RATE1 == 0) \|\| (RATE > RATE1)`。`RATE1` 恆為 0 時,`RATE == 0` 走前半、`RATE > 0` 走後半,**兩邊都成立** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:67-70` |

**影響**:(a) 境外永遠通過;(b) 境內——也就是唯一會用到多階費率的情境——**整段檢核被 `if` 跳過**。訊息「手續費率需符合逐年遞減原則」在任何情況下都不會出現。`OFDM196` 還多兩條跟著陪葬:`SWITCH_FEE_RATE < 0` 與「選取的基金不適用此 幣別代碼」也掛在同一個 `if` 裡(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:112-113`、`:126-132`)。

**對照組**:`OFDM194` 的同一段檢核**沒有包 `if`**,直接跑(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:65-72`)——三支同型畫面,一支對兩支錯。

### E.2 `OFDM197` 匯入的重複檢核查錯 DataTable,永遠不觸發 —— 嚴重度 **高**

`CheckExists` 迭代 `Model.DataEntity.OFDM197`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:204`),但匯入畫面只填 `OFDM197B`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:118-122`),而且開檔前 `VDB.UIView.Clear()` 把兩張都清空(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:107`)。`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM197_Ctl.cs:56-58` 兩張表分別搬,所以 PO 收到的 `OFDM197` 一定是空的,`CheckExists` 恆回 `false`。

**影響**:「該行銷身份別已有資料,是否覆寫資料?」的詢問永遠不跳,直接進 delete + insert。使用者不會知道自己覆寫了什麼。連帶 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:85` 的 `Columns["BF_NAME"]`(`OFDM197B` 根本沒這一欄)那條死路也走不到——**這是唯一讓它不炸的原因**。

### E.3 `OFDM195` 的「一人一筆未終止」檢核三層外殼都在,沒有呼叫端 —— 嚴重度 **高**

PO(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:315`)→ Ctl(`Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM195_Ctl.cs:109`)→ Pxy(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM195_Pxy.cs:119`)三層都在,UI 的呼叫被註解(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:155-183`)。

**影響**:同一位員工可以有多筆未終止的優惠關係人資料。配合 §8.5(COD 也不會自動終止),這條業務規則在系統裡**完全沒有守門人**。

### E.4 `FeeTypeValidate` 的 `catch` 不補結果列,例外會被當成通過 —— 嚴重度 **高**

三支各一份,完全相同的程式碼:

```
catch (Exception ex)
{
    CommonExceptionBlocker.HandleBusinessException(ex);
}
return mResult;      ← mResult.Utility.Result 還是空的
```

錨點:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:394-398`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:235-239`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:232-236`。

UI 端:`if (View.Util.Result.Rows.Count > 0) return ReturnCode; … return true;`(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:114-117`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194B.cs:103-106`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:97-100`)——**結果列是空的就當成 `true`(通過)**。

**影響**:資料庫連不上、SQL 語法錯、權限不足,通通變成「檢核通過」。而這支檢核用的又是字串串接的 SQL(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:361-385`),輸入含單引號就會語法錯 → 直接放行。

### E.5 三個批次匯入繞過四眼與伺服端卡控 —— 嚴重度 **高**

| 入口 | 繞過什麼 | 錨點 |
|---|---|---|
| `OFDM197.BatchAdd` | 四眼;`STATUS` 寫死 `'301'`,`ENTRYID`/`VERIFYID`/`APPROVEID` 同人同時 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:242-247` |
| `OFDM206.BatchAdd` | 四眼 + `BeforeAdd` 的「每位受益人只能設定一筆開戶優惠」 | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:182-189` |
| `OFDM206.BatchAddEC` | 同上,另加寫死條件 `etraflg='Y'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:295-302` |

`OFDM206` 那兩個的後果會傳到 BMS(§8.1 的 #2/#3)。

### E.6 `OFDM206` 刪除確認的判斷方向相反 —— 嚴重度 **高**

```
private void OFDM206_BeforeDeleteButtonClicked(object sender, CancelEventArgs e)
{
    e.Cancel = (DialogWithNoStatusbar.ShowMessage(FunctionDialogStyle.Warn03, "已有使用記錄，是否刪除(Y/N)？") == DialogResult.OK);
}
```

錨點:`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206.cs:214-217`。

按「是」→ `DialogResult.OK` → `e.Cancel = true` → **刪除被取消**;按「否」→ **刪除執行**。同一份 code base 的其他畫面都是反過來寫的(`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:427`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM195.cs:313` 都用 `== DialogResult.No` 才 `e.Cancel = true`)。而且這個提示**無條件跳**,不查 `OFD207` 到底有沒有使用記錄。

### E.7 三支畫面的來源檔不是 UTF-8 —— 嚴重度 **中**

實測(對 `Dev/ATLAS.OFD/Source` 底下這 15 支相關的 `.cs` / `.xsd` 逐檔 `bytes.decode('utf-8')`):

| 畫面 | 非 UTF-8 的檔 |
|---|---|
| `OFDM197` | `UI/UI.OFD/OFDM197.cs`、`UI/UI.OFD/OFDM197.Designer.cs`、`Control/Control.OFD/OFDM197_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM197_Pxy.cs`、`PO/PO.OFD/OFDM197_PO.cs` |
| `OFDM213` | `Control/Control.OFD/OFDM213_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM213_Pxy.cs`、`PO/PO.OFD/OFDM213_PO.cs` |
| `OFDM214` | `Control/Control.OFD/OFDM214_Ctl.cs`、`FormProxy/FormProxy.OFD/OFDM214_Pxy.cs`、`PO/PO.OFD/OFDM214_PO.cs` |

`OFDM197` 是整條六層(含 UI);`OFDM213` / `OFDM214` 是 **UI 層 UTF-8、底下三層 Big5**,同一支畫面混兩種編碼。`OFDM197p0` 相關檔反而是 UTF-8。

**影響**:用 UTF-8 編輯器改中文訊息會產生亂碼;`git diff` 看不懂;跨平台工具鏈(本文的掃描與建置就是)必須先偵測編碼。

### E.8 `OFDM213.IsBfExsits` 查一個不存在的欄位 —— 嚴重度 **中**

`SELECT COUNT(1) FROM OFD213A WHERE BF_NO = '…'`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:181-183`),但 `OFD213A` 沒有 `BF_NO` 欄(附錄 A.1 / §2.4)。執行會 `ORA-00904`,`catch` 吃掉回 `-1`。目前沒有呼叫端(`OFDM213p0` 不呼叫),所以不會發作;但它掛在 `IOFDM213_PO` 介面上(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:20`),隨時可能被人接起來用。這是從 `OFDM214` / `OFDM215` 複製過來忘了刪的。

### E.9 三胞胎的複製功能三處不一致 —— 嚴重度 **中**

| # | 不一致 | `OFDM213` | `OFDM214` | `OFDM215` |
|---|---|---|---|---|
| 1 | 複製時 `STATUS` | 清成 `string.Empty`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:118`) | **`row.STATUS = row.STATUS;` 自我指派,等於不清**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:149`) | 同 `OFDM214`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:97`) |
| 2 | 一般 `catch` 是否記 log | — | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:228`) | **沒有**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:178-184`) |
| 3 | 解構子是否解除事件訂閱 | **沒有**(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:40-43`) | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:38-43`) | 有(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:40-45`) |

#1 的後果:複製出來的列帶著來源的四眼狀態(可能是已覆核),但 `APPROVEID` / `APPROVEDATE` 全被清空 —— **狀態與軌跡不一致**。

### E.10 `OFDM196` 明細 SQL 的日期條件被註解 —— 嚴重度 **中**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:181-182` 被 `//` 掉,而同檔主檔 SQL 的同一行還在(`:108-109`),其他五支同型畫面也都在。查詢日期條件只在主檔生效,點進明細後失效。

### E.11 「永久費率」的日期哨兵值有兩種寫法 —— 嚴重度 **中**

| 畫面 | 費率種類 = 永久 時寫入的起迄日 | 錨點 |
|---|---|---|
| `OFDM191` | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:74-75` |
| `OFDM198` | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM198.cs:73-74` |
| `OFDM193` 境外 | `"00000000"` / `"99999999"` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:96-97` |
| `OFDM193` 境內 | **`""` / `""`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:106-107` |
| `OFDM194` | **`""` / `""`** | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:90-91` |
| `OFDM196` 境外 / 境內 | `"00000000"`/`"99999999"` 與 `""`/`""` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM196.cs:158-172` |
| 舊版(被註解) | `1900/1/1` 與 `9998/12/31` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM194.cs:88-89` |

三代哨兵值並存,而且 Oracle 會把 `''` 折成 NULL。任何一支 SQL 想用「`BNG_DATE <= :today AND :today <= END_DATE`」去篩永久費率,**對 `''` 那一組會失效**(NULL 比較恆為 UNKNOWN)。同型問題在 `OFDM195.CheckData` 的 `REL_STOP_DATE IS NULL` 上也有(§4.7)。

### E.12 `OFDM199` 一次存檔,七張表兩種生效時機 —— 嚴重度 **中**

見 §4.10.3。三張 `_UPD` 等生效,四張立即寫正式表且立即被 EC 讀到。**四眼只護住一半。**

### E.13 `OFDM199` 定額優惠「迄日」檢核方向存疑 —— 嚴重度 **中**(標「假設」)

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM199.cs:236` 與 `:240` 兩個條件都是 `活動日期 > 該列日期`,只換了欄位名:

```
if ((this.udatCAMPAIGN_BNG_DATE.DateTime.Date > Convert.ToDateTime(Row.Cells["BNG_DATE"].Value).Date) && …) RspBNG++;
if ((this.udatCAMPAIGN_END_DATE.DateTime.Date > Convert.ToDateTime(Row.Cells["END_DATE"].Value).Date) && …) RspEND++;
```

對「起日」是對的;對「迄日」意思變成「定額優惠不能比活動早結束」,允許優惠期超出活動期。業務上比較合理的應該是 `<`。需求文件不在 repo,**標假設,不改判定**。

### E.14 Oracle 三值邏輯:`<>` 遇 NULL —— 嚴重度 **低**(目前不發作)

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:69` 的 `AND A.CAMPAIGN_CODE <> :CAMPAIGN_CODE`。`CAMPAIGN_CODE` 是 `OFD206` PK 的一部分,理論上不為 NULL,所以目前不會漏抓。但這是 CAS / CLS / DSM / BBS / TMK / CPM 六個模組都中過的同型寫法,**改 schema 或改成 outer join 時要一起看**。本片其餘的 `<>` 比對只出現在被註解的程式裡。

### E.15 `OFD206.BF_SRNO` 在匯入流程裡裝的是戶號 —— 嚴重度 **中**(易誤判)

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:106` 把 CSV 的戶號塞進 `row.BF_SRNO`,`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:49` 把欄位標題改成「戶號」,PO 端再靠 `CROSS JOIN OFD601 … AND B.BF_NO = :BF_NO` 換回真的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:187-196`)。

連帶一個真的錯:`CheckExists` 的錯誤訊息是「此優惠活動已存在戶號:」,後面接的卻是查回來的 `BF_SRNO`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:155-157`、`:171`)——**標籤說戶號,值是 EC 流水號**。

### E.16 `OFDM206_PO.CheckData` 是一個可執行任意 SQL 的伺服端入口 —— 嚴重度 **高**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:221-269`:從 `Model.Utility.Parameters` 收一整串 SQL 與一個分隔字元,切開後逐段 `ExecuteNonQuery`,連 `Commit` 與否都由參數存不存在決定(`:234`、`:256-259`)。

repo 內沒有 UI 呼叫端,但 `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM206_Ctl.cs:200-205` 與 `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM206_Pxy.cs:48-62` 都在,而 Remoting 邊界就在 UI → FormProxy(`architecture.md §8`)。**這是一個對外開放、沒有任何白名單的 SQL 執行入口。**

### E.17 字串串接進 SQL —— 嚴重度 **高**(範圍廣)

本片 15 支裡有 9 支在組 SQL 時用字串串接,不綁參數。彙整:

| 畫面 | 位置 | 串進去的東西 |
|---|---|---|
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:361-385` | `FUND_ID` `CRNCY_CD` `BF_NO` `FEE_TYPE` |
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:418-436` | `string.Format` 拼 `BF_NO` 與 `FUND_ID` |
| `OFDM194` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:306`、`:311` | `DataTable.Select()` 的過濾字串 |
| `OFDM194B` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:202-226` | 同 `OFDM194` |
| `OFDM195` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:188-278` | 六個查詢條件 |
| `OFDM195` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs:339-394` | 四個查詢條件 |
| `OFDM197` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:134-175` | `MKT_ID` `ID_NO` `BF_NO`,含 `LIKE` |
| `OFDM197` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:200` | `string.Format` 拼 `MKT_ID` |
| `OFDM198` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:203-221` | `FUND_ID` `DISC_CODE` `BF_NO` `FEE_TYPE` |
| `OFDM199` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:500-513` | 自寫的 `AddParam`,全部值直接串 |
| `OFDM206` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:146-148` | `string.Join(" OR ", … string.Format("BF_NO = {0}", r.BF_SRNO))` |
| `OFDM213` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM213_PO.cs:73`、`:88`、`:148`、`:183` | `FUND_ID` / `BF_NO` |
| `OFDM214` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:62`、`:93`、`:120`、`:176`、`:292` | `FUND_ID` / `BF_NO`,**其中 `:292` 是把整句子查詢串進 `IN ( )`** |
| `OFDM215` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:74`、`:124`、`:211`、`:238`、`:310` | 同上 |

對照 `architecture.md §4`:框架的 `EVAStringHelper.AddParam` 是有綁參數的,這些是繞過它自己手寫的部分。

### E.18 `catch` 內第一行就 `tran.Rollback()`,原始例外可能被蓋掉 —— 嚴重度 **中**

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:276-282`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:211-217`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:318-324`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:332-338`:`tran` 宣告成 `null`,若例外發生在 `BeginTransaction()` 之前或之中,`catch` 的 `tran.Rollback()` 會丟 `NullReferenceException`,真正的錯誤訊息就消失了。

### E.19 死碼比例 —— 嚴重度 **中**

| 檔 | 總行數 | 註解掉的區塊 | 佔比 |
|---|---|---|---|
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM195_PO.cs` | 1,724 | `:506-1722` | **71%** |
| `Dev/ATLAS.OFD/Source/Control/Control.OFD/OFDM214_Ctl.cs` | 1,040 | `:313-1038` | **70%** |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs` | 1,443 | `:539-583` + `:586-857` + `:861-1441` | **62%** |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM199A_Pxy.cs` | 152 | `:45-148` | 68%(**而且整個檔不在 csproj**) |

`architecture.md 附錄 D.3` 已經提醒過「對這個 repo 做靜態統計,第一件事是剝註解」。本片是那句話的放大版。

### E.20 `OFDM197p0` 匯入的兩個靜默行為 —— 嚴重度 **中**

| # | 行為 | 錨點 |
|---|---|---|
| 1 | 覆寫確認後的**第二次** `BatchAdd` 回傳值沒被檢查,下一行無條件顯示「複製成功」 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:88-92` |
| 2 | CSV 讀到空行就 `break`,後面的戶號全部靜默丟掉 | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:116-117` |

### E.21 `Result[0]` 未檢查 `Count` 就取用 —— 嚴重度 **低**

`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM197p0.cs:95`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p0.cs:79`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM206p1.cs:69`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM213p0.cs:94`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM214p0.cs:113`:`else` 分支直接 `vdb.Util.Result[0].ReturnMessage`。PO 的每一條路徑目前都會補結果列,所以不發作;E.4 那種「不補結果列」的寫法一旦出現在這些 PO 上就會變成 `IndexOutOfRangeException`。

### E.22 寫死常數彙整 —— 嚴重度 **中**

| 常數 | 位置 | 意義 |
|---|---|---|
| `BNG_AMT = 1` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM191_PO.cs:92`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM193_PO.cs:107`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194_PO.cs:100`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM194B_PO.cs:103`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM196_PO.cs:103`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM198_PO.cs:101` | 群組第一列 |
| `BNG_YEAR = 1900` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM192_PO.cs:82` | 同上 |
| `'Atlas'` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM193.cs:572` | 境內基金公司代碼〔客戶特定〕 |
| `'ALL FUNDS'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM214_PO.cs:281`、`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM215_PO.cs:301` | 「所有基金」的魔術字串 |
| `'C'` / `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM197_PO.cs:246` | `SOURCE_CD` 批次轉入 / 已覆核 |
| `'301'` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:185`、`:298` | 已覆核 |
| `etraflg='Y'` + `trim(openday) is not null` | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM206_PO.cs:300-301` | EC 已開戶〔客戶特定〕 |
| `1m` / `999999999999m` / `1900m` / `9999m` | `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM191.cs:210`、`Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM192.cs:166` | 階梯上下界 |

### E.23 `OFD687A` 的欄名拼錯成 `COMPAIGN_CODE` —— 嚴重度 **低**(已被程式繞過)

xsd 宣告的是 `COMPAIGN_CODE`(C-O-M),與其他六張表的 `CAMPAIGN_CODE` 不同。`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM199_PO.cs:493-494` 寫了一個 `if` 特例把欄名換掉。**這是 DB 欄名的錯字,改不得,只能一直帶著**;任何新寫的 SQL 碰到 `OFD687A` 都要記得拼錯的那個。

### E.24 BMS 側 `OFD206` 的 `ROWNUM = 1` 配上整批 `DELETE` —— 嚴重度 **中**(標「假設」)

見 §8.1。載入只取一列(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1129`),刪除刪全部(`Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1854-1863`,`CAMPAIGN_CODE` 的條件被註解)。只要 `OFD206` 上有同一位受益人的兩列開戶優惠(批次匯入辦得到,§4.11),存 `BMSM001` 就會少一列。**未實測,需要 DB 資料驗證。**

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。涵蓋 `DataEntity.OFD7` 底下 15 支 M 畫面、23 張實體表、24 條缺陷 |

由 build_doc.py v2.0.0 於 2026-09-15 11:53 產生 · 標題 100 · 圖 5 · 表格 68 · 程式錨點 505 · § 連結 66 · 引用檢查：畫面 24（缺 0） · Table 40（缺 0） · 結果集 18（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
