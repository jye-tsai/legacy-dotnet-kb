ATLAS 知識庫 — 10-模組-BBS-BMS-CAS-CLS-COD

本檔合併以下文件:modules/bbs.md、modules/bms.md、modules/cas.md、modules/cls.md、modules/cod.md


============================================================
【文件】kb/modules/bbs.md
============================================================

# ATLAS BBS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型與憑證狀態機搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(三對 `1xx` 平行畫面到底是什麼)、§4 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表中文名與程式註解**推測**,待選單表回填。ATLAS 沒有把畫面中文名放進版控,17 支畫面沒有一支在非 Designer 檔裡寫出自己的中文名。 ⚠ **〔客戶特定〕**:憑證期別 `'99'`(無實體佔位)、下拉代碼分類 `'244'` / `'245'`、憑證狀態碼的值域為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:標記的表同時服務 OFD / EC(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、平行複本的前例看 `architecture.md §7`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:BBS 管「一張受益憑證從換發、掛失、補發到質押、轉讓」的整個生命週期,而且同一套流程做了兩份——實體憑證一份、無實體受益權單位一份。**

推測依據五條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `BBS009A` 的欄位是「質設書號」「質設型態」「質設孳息歸屬」「質權人ID」;`BBS001A` 是「換發書號」「換發種類」「換發張數」;`BBS003A` 是「掛失書號」「掛失總單位數」 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:25-61`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM001Model.xsd:27-55`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:27-44` |
| 報表中文名 | 「受益憑證換發查核表」「受益憑證掛失(撤銷)查核表」「受益憑證掛失中清冊」「受益人質設(質解)查核表」「受益憑證質設中清冊」「轉讓過戶查核表」 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:82`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:112`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR007.cs:64`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR010.cs:101`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR012.cs:102`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR015.cs:71` |
| 流水號種類 | 本模組跟框架要六種書號:換發、掛失、掛撤、補發、質設、轉讓各一種 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:308`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:99`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:177`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:97`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:170`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:110` |
| 共同的外部主檔 | 十支維護畫面全部在改同一張憑證檔 `OFD721` 的狀態欄,與同一張結餘檔 `OFD304A` 的四個單位數欄 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:376`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:169`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:218`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:201`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:237` |
| 共用計算 | 每支畫面存檔前都去問同一支共用工具「這個受益人在這檔基金上有多少單位數」,而且答案分三欄:全部 / 實體 / 無實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:382-408` |

「BBS」三個字母本身的展開在 repo 裡找不到定義,**不要猜**。本文一律用「受益憑證作業」描述它的範圍,這是從上表推出來的,不是官方名稱。

七條業務線與對應畫面:

| 線 | 在管什麼(推測) | 實體版 | 無實體版 | 主 / 明細 |
|---|---|---|---|---|
| A 換發 | 舊憑證換新憑證、憑證換無實體、無實體換憑證 | `BBSM001` | 同一支內用換發種類分 | `BBS001A` / `BBS002A` |
| B 掛失 | 受益人聲明憑證遺失,凍結該批憑證並收掛失文件 | `BBSM003` | — | `BBS003A` / `BBS004A` `BBS020A` |
| C 掛失撤銷 | 憑證找回來了,把掛失狀態解掉 | `BBSM004` | — | `BBS005A` / `BBS006A` |
| D 掛失補發 | 憑證找不回來,註銷舊證、印新證 | `BBSM005` | — | `BBS007A` / `BBS008A` |
| E 質權設定 | 受益人把單位數質押給第三人 | `BBSM009` | `BBSM109` | `BBS009A` / `BBS010A` |
| F 質權解除 | 解除質押 | `BBSM010` | `BBSM110` | `BBS011A` / `BBS012A` |
| G 轉讓過戶 | 出讓人把單位數過戶給受讓人,並產生受讓人的新申購書 | `BBSM013` | `BBSM113` | `BBS013A` / `BBS014A` `BBS015A` `OFD220A` `OFD221A` `OFD234A` `OFD235A` |
| H 報表 | 上面七條線的查核表與清冊 | `BBSR002` `BBSR006` `BBSR007` `BBSR010` `BBSR011` `BBSR012` `BBSR015` | — | 全部來自版控外的 SP |

### 0.2 這模組最反直覺的一件事:`1xx` 不是舊版,是「無實體」

母體掃出三對畫面共用完全相同的主明細表,乍看是「一份程式被複製兩次」。**不是。**三對畫面各自被一個型態欄位切成兩個互不相見的世界:

| 本體(實體憑證) | 平行版(無實體) | 共用主 / 明細 | 切分欄位 | 本體寫入值 | 平行版寫入值 |
|---|---|---|---|---|---|
| `BBSM009` 質設 | `BBSM109` 質設 | `BBS009A` / `BBS010A` | `MOR_TYPE` | `'0'` | `'1'` |
| `BBSM010` 質解 | `BBSM110` 質解 | `BBS011A` / `BBS012A` | `CMOR_TYPE` | `'0'` | `'1'` |
| `BBSM013` 轉讓 | `BBSM113` 轉讓 | `BBS013A` / 六張明細 | `TX_TYPE` | `'0'` | `'1'` |

四條互相獨立的證據(§4.5–§4.7 逐條展開):

1. **新增時寫死型態值。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:166` 寫 `MOR_TYPE = "0"`,`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:104` 寫 `MOR_TYPE = "1"`;`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:187` 寫 `CMOR_TYPE = "0"`,`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:93` 寫 `"1"`;`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:493` 寫 `TX_TYPE = "0"`,`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:176` 寫 `"1"`。

2. **查詢時各自加硬條件。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:350` 是 `AND MOR_TYPE = '0'`,`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:284` 是 `AND MOR_TYPE = '1'`;`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:384` 與 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:210`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1115` 與 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1014` 同理。**在 A 畫面查不到 B 畫面建的單是設計如此,不是資料掉了。**

3. **扣的結餘欄位不同。** 實體版動 `OFD304A` 的 `BAL_MOR_UNIT`(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:231`),無實體版動 `BAL_MOR_UNIT_S`(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:140`)。同一張表、同一個受益人、兩個獨立的水位。

4. **檢核比的庫存欄位不同。** 共用工具 `CalcBBSUnits` 回三個數:全部 / 實體 / 無實體。實體版比實體數(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:402`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:222`),無實體版比無實體數(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:713`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:368`)。`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:538` 的區段標題直接寫著「判斷是否能無實體質設」。

還有一條收尾證據:**無實體版沒有憑證可選,所以自己捏一張假憑證。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:120-133` 與 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:179-185` 都在存檔前塞一列明細,期別固定 `'99'`、號碼 `0`、檢查碼 `0`,單位數等於主檔總數。實體版則是由使用者在憑證 grid 上逐張勾選(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:355`)。

所以三個候選解釋的答案是:

| 候選 | 判定 | 理由 |
|---|---|---|
| (a) 不同幣別 / 不同商品線的平行維護 | **✔ 就是這個** | 切分維度是「實體憑證 vs 無實體受益權單位」,兩邊資料永久共存、各自有效 |
| (b) 舊版與新版並存 | ✘(但程式世代確實不同) | 兩邊都在跑、都在寫同一張表;不過 `1xx` 用的是新世代寫法(泛型方法簽名 + `SQLEVAHelper`,檔案編碼 UTF-8 BOM),本體是舊世代(具名型別簽名,檔案編碼 cp950),見 §4.5 |
| (c) 不同角色權限的入口 | ✘ | 程式內沒有任何權限判斷,兩邊的差異全在型態欄位與結餘欄位上 |

**維護上最重要的一句話:這三對不是同一份程式碼,逐層相似度只有 0.20–0.60(§4.5.1 的量測),所以「改一支要不要改另一支」沒有機械答案——但事實是已經有人只改了一邊(附錄 E1)。**

### 0.3 這模組不管什麼

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 憑證主檔的建立與印製 | OFD | `OFD721` 的主檔畫面是 `OFDM721` / `OFDM725`;BBS 只 UPDATE 它的狀態欄,從不 INSERT |
| 受益人基本資料 | BMS | `BMS001A` 只被 join 取姓名,從無寫入;`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:373` |
| 基金主檔、行事曆、淨值 | OFD / CTL | 全走客戶端共用工具的 `GetFundBusinessDay`,BBS 只讀;`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:321-322` |
| 申購 / 贖回交易本身 | OFD | BBS 只有 `BBSM013` / `BBSM113` 會生申購書,而且是「轉讓造成的過戶」那一種;`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:260` |
| 憑證用印 / 簽核(`OFD724`) | OFD | BBS 只 SELECT 它來判斷「已送簽 / 已註銷」;`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1389` |
| 結帳與過帳 | 不明 | 每支畫面都去問「該基金最大資料控制日期」再比對,但寫那個日期的程式不在 BBS 內。**假設**:在 OFD 的日結批次,依據是 BBS 只讀不寫 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 櫃檯 / 作業人員 | 開單:換發、掛失、掛撤、補發、質設、質解、轉讓 | 十支都是標準四眼維護畫面,`Before*ButtonClicked` 做前端檢核 |
| 覆核者 | 驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |
| 印鑑核對人員 | 每支畫面都有一顆「印鑑」鈕,叫出該受益人的印鑑影像 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:68`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:60`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:60`;轉讓因為有兩造,拆成「出讓人印鑑」與「受讓人印鑑」兩顆(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:342-343`) |

**本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由框架平台庫決定(`architecture.md §3`)。唯一在程式裡看得到的「誰不能動」是四眼自審規則:`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:390` 把登入者自己送出的單從待辦清單排掉。

### 0.5 全域開關

repo 內**沒有**任何 BBS 專屬的設定檔開關。`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔 DataTable 與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:19`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:51`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:81` |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄、順序為何 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:20`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:89` |
| `supportedRuntime` | 宣告 `.NETFramework,Version=v4.8` | `Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:92` |

三件要記住的:

- **十支畫面沒有一支宣告 `detailtable`。** 明細表完全由 PO 的 `xTableMapping` 決定(§2.1),設定檔上看不出來一支畫面有幾張明細。`BBSM013` 有六張,從設定檔完全看不出來。

- **`1xx` 的 section 名稱排在本體後面**(`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:9-12`),順序是 `BBSM013` → `BBSM113` → `BBSM109` → `BBSM110`,不是照代號排。這只是註冊順序,沒有語意,但找的時候會找不到。

- **主檔 DataTable 的命名兩代混用。** 舊的叫 `BBSM001_BBS001`(畫面代號 + 實體表短名),新的直接叫 `BBSM003` / `BBSM109` / `BBSM113`(畫面代號)。同一個設定檔裡兩種都有,寫 SQL 或做欄位搬運時會踩到。

### 0.6 一眼看懂的三個縮寫

| 縮寫 | 展開(推測) | 出現在 |
|---|---|---|
| `CER` | Certificate,受益憑證 | 期別 / 號碼 / 檢查碼 / 單位數 / 狀態 五個欄位前綴 |
| `MOR` / `CMOR` | Mortgage / Cancel Mortgage,質設 / 質解 | `BBS009A` `BBS011A` 的書號、單位數,與 `OFD304A` 的質押水位欄 |
| `LOS` / `RLOS` / `CLOS` | Loss / Revoke Loss / Compensate Loss,掛失 / 掛撤 / 掛補 | `BBS003A` `BBS005A` `BBS007A` 的書號與日期欄 |

憑證的三段式識別碼**永遠是三欄一組**:期別 + 號碼 + 檢查碼。畫面上顯示成「期別-0000123-4」(號碼七位補零),組字串的地方在 `Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM013_Ctl.cs:926-927`。寫 SQL 時漏掉檢查碼不會報錯,只會多撈到別張證——`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:221-225` 就是只用期別 + 號碼去 UPDATE `OFD721`。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] BBS 全景：換發掛失補發四支、質權兩套、轉讓兩套、OFD 的中央狀態機與結餘檔，以及七支報表
圖中文字:① 實體憑證的一生：換發 → 掛失 → 掛撤／補發（四支，沒有無實體版） / BBSM001 換發 / BBS001A BBS002A / BBSM003 掛失 / BBS003A BBS004A BBS020A / BBSM004 掛撤 / BBS005A BBS006A / BBSM005 補發 / BBS007A BBS008A / ② 質權設定與解除：實體一套、無實體一套，靠型態欄切開 / BBSM009 質設 實體 / MOR_TYPE='0' / BBSM010 質解 實體 / CMOR_TYPE='0' / BBSM109 質設 無實體 / MOR_TYPE='1' / BBSM110 質解 無實體 / CMOR_TYPE='1' / ③ 轉讓過戶：也是兩套，而且會生受讓人的申購書 / BBSM013 轉讓 實體 / TX_TYPE='0' / BBSM113 轉讓 無實體 / TX_TYPE='1' / OFD220A OFD221A / 受讓人新申購書 / OFD234A OFD235A / 支票與匯款明細 / ④ 中央狀態機與結餘：全部是 OFD 的表，BBS 只寫不建 / OFD721 憑證檔 / 狀態 1~8 見 2.5 / OFD304A 結餘檔 / 四個水位欄 未宣告 / OFD310A / 基金單位數結餘 / OFD724 OFD0814A / 用印與憑證流水號 / ⑤ 報表七支：資料全部來自版控外的 SP，與上面四排完全脫鉤 / BBSR002 / 換發查核表 / BBSR006 BBSR007 / 掛失查核與清冊 / BBSR010 011 012 / 質設質解查核與清冊 / BBSR015 / 轉讓過戶查核表
```

*圖:圖 1 BBS 全景。橘框=實體憑證流程的維護入口；橘虛框=無實體平行版〔客戶特定〕；灰虛框=借用 OFD 的表；黑框=BBS 只寫不建的外部表。七條線之間沒有程式呼叫，只靠 OFD721 的憑證狀態與 OFD304A 的水位欄相連。*

看圖的四個重點:

1. **七條線之間沒有程式呼叫關係,只靠 `OFD721` 的憑證狀態串起來。** `BBSM003` 把憑證打成「掛失中」,`BBSM004` 與 `BBSM005` 都只收「掛失中」的;`BBSM009` 把「正常」打成「質設中」,`BBSM010` 只收「質設中」的。**狀態機就是介面**,沒有任何一支畫面直接呼叫另一支。

2. **無實體那一路完全繞過 `OFD721`。** `BBSM109` / `BBSM110` / `BBSM113` 三支沒有一行 UPDATE `OFD721`;`BBSM113` 連 `OFD721` 這張 DataTable 都沒有,對比 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:553`。它們只動 `OFD304A` 的無實體質押水位欄。

3. **只有轉讓會生別人的單據。** `BBSM013` / `BBSM113` 會 INSERT `OFD220A` / `OFD221A`(受讓人的新申購書)、`OFD234A`(支票)、`OFD235A`(匯款),等於在 OFD 的地盤上開了第二個建檔入口(§8)。

4. **報表那一排與上面六排完全脫鉤。** 七支 R 畫面沒有一支引用 BBS 的任何維護 PO,資料全部來自版控外的 SP(§7)。

### 1.2 資料表關係

見 §2 節首的圖。三件要記住的:

- **主明細的綁定靠 `dataid`,不是靠外鍵。** 同一次 EVA 生命週期內主檔與所有明細共用一個 `Guid`(`architecture.md §3`),所以主檔與明細一定一起送審、一起覆核。

- **每一組主明細的明細 PK 都含「書號 + 憑證三段碼」。** 例:`BBS010A` 的鍵是質設書號 + 期別 + 號碼 + 檢查碼。無實體版因為憑證三段碼固定是 `'99'` / `0` / `0`,**一張單只會有一列明細**——這是 `1xx` 沒有憑證勾選 grid 的原因。

- **`BBSM013` 的六張明細不是同一層。** `BBS014A`(憑證)、`BBS015A`(申購書轉讓明細)是轉讓自己的;`OFD220A` / `OFD221A` / `OFD234A` / `OFD235A` 是受讓人那一側要生的申購資料。六張全掛在同一個明細清單上(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:48-53`),所以**四眼覆核一按下去,受讓人的申購書也跟著生效**。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。BBS 十支維護畫面的卡控分四層,**沒有一層在伺服器端重驗**:

| 層 | 在哪 | 做什麼 | 例 |
|---|---|---|---|
| ① 框架必填 | `validatorManager.DataValidate()` | 欄位必填 / 格式,由 Designer 上的 validator 決定 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:276` |
| ② 本畫面 `DoValidate()` | UI | 日期、單位數、明細加總、庫存比對——本模組 90% 的卡控在這裡 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:271-430` |
| ③ 經 Pxy 打 DB 的檢核 | UI 呼叫 `IsFreeze` / `GetMaxCtlDate` / `IsRUnit` 等 | 註銷戶、結帳日、沖銷資料 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:188`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:244`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:413` |
| ④ PO 事件內的 SQL 影響列數 | `AfterAdd` / `AfterApproveDelete` | 用「更新列數不等於 1 就 throw」當卡控,不成立就回滾整筆 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:122-125` |

第 ④ 層是本模組的特色:**「更新了幾列」被當成業務檢核用**。例如質設刪除時如果 `OFD721` 那筆已經不在「質設中」,UPDATE 影響 0 列,程式就丟「該憑證號碼 … 不為質設中,不可刪除」。好處是原子;壞處是訊息離真正的原因很遠,而且**一旦有人手動改過 `OFD721`,錯誤訊息會完全誤導**。

### 1.4 批次 / 報表資料流

見 §7 節首的圖。BBS **沒有任何批次(B)畫面、沒有 WindowsService**(§6)。報表鏈固定四段:

R 畫面(收查詢條件)→ Report FormProxy → Report PO(呼叫版控外的 SP)→ `RPS` / `RPS1` 兩份 `.rpt` 擇一。

### 1.5 一日作業泳道

repo 內沒有排程、沒有服務,所以 BBS 的「一日」全是人工觸發的。從程式反推出來的順序:

1. **開單前**:畫面載入時先問該基金最近結帳日與該基金營業日,兩個都拿到才讓使用者輸日期。

2. **開單**:`Before*ButtonClicked` 跑完 ①②③ 三層卡控 → `Add` → PO 在 `BeforeAdd` 配書號、在 `AfterAdd` 改 `OFD721` 與 `OFD304A`。

3. **覆核**:`Verify` → `Approve`。**注意:`AfterVerify` / `AfterApprove` 在本模組只做一件事——寫跳號一覽表,沒有任何業務動作**(例:`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:854-874`)。也就是說**資料在「輸入」那一刻就已經寫進 `OFD721` 與 `OFD304A` 了,不是覆核後才生效**。這是讀本模組最容易誤判的一點。

4. **刪除**:`Delete`(未覆核前刪)只寫跳號;`ApproveDelete`(已覆核後刪)才把第 2 步的副作用整個倒回去。

## 2. 資料模型

```text
[圖] BBS 二十張表的七組主明細關係、主鍵組成，以及四張只存在於 SQL 字串裡的外部表
圖中文字:本模組自有 16 張：七組主明細，主鍵都是「書號」 / BBS001A 換發 / PK CHG_NO / BBS002A / ＋新舊碼＋憑證三段碼 / BBS003A 掛失 / PK LOS_NO / BBS004A BBS020A / 憑證明細＋必備文件 / BBS005A 掛撤 / PK RLOS_NO / BBS006A / ＋憑證三段碼 / BBS007A 補發 / PK CLOS_NO / BBS008A / ＋掛補新舊碼 / BBS009A 質設 / PK MOR_NO ＋型態欄 / BBS010A / ＋憑證三段碼 / BBS011A 質解 / PK CMOR_NO ＋型態欄 / BBS012A / ＋質設書號＋三段碼 / BBS013A 轉讓 / PK TX_NO ＋型態欄 / BBS014A / 被轉讓的憑證 / BBS015A / 申購書銷帳結果 / 借用 OFD 的四張（宣告在 xTableMapping，母體看得到） / OFD220A〔共用〕 / 申購書主檔 / OFD221A〔共用〕 / 申購明細 跨模組 / OFD234A〔共用〕 / 支票明細 / OFD235A〔共用〕 / 匯款明細 / 只出現在 SQL 字串裡的四張（母體看不到，反查工具查不到） / OFD304A / 四個水位欄 十支都寫 / OFD310A / 基金單位數結餘 / OFD0814A / 憑證流水號 無鍵更新 / OFD724 / 用印檔 三值邏輯地雷
```

*圖:圖 2 資料模型。橘框=主檔；白框=明細；灰虛框=借用 OFD 且宣告在主明細清單裡的表；黑框=只出現在 SQL 字串裡、四眼引擎不管、也不會自動回滾的外部表。質設／質解／轉讓三組主檔各帶一個型態欄，那就是實體與無實體的分界。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

十支維護畫面的主明細宣告全部在 PO 建構子裡。**實體表名在左、DataTable 名在右**,兩者不同名是本模組最常見的誤讀來源:

| 畫面 | 主檔實體表 | 主檔 DataTable | 明細實體表 → DataTable | 錨點 |
|---|---|---|---|---|
| `BBSM001` | `BBS001A` | `BBSM001_BBS001` | `BBS002A` → `BBSM001_BBS002` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:54-55` |
| `BBSM003` | `BBS003A` | `BBSM003` | `BBS004A` → `BBSM003_CerData`;`BBS020A` → `BBSM003_DOC` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:60-63` |
| `BBSM004` | `BBS005A` | `BBSM004` | `BBS006A` → `BBSM004_Cer_CK` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:57-58` |
| `BBSM005` | `BBS007A` | `BBSM005_BBS007` | `BBS008A` → `BBSM005_BBS008` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:56-57` |
| `BBSM009` | `BBS009A` | `BBSM009_BBS009` | `BBS010A` → `BBSM009_BBS010` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:64-65` |
| `BBSM109` | `BBS009A` | `BBSM109` | `BBS010A` → `BBSM109_Detail` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:45-46` |
| `BBSM010` | `BBS011A` | `BBSM010_BBS011` | `BBS012A` → `BBSM010_BBS012` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:63-64` |
| `BBSM110` | `BBS011A` | `BBSM110` | `BBS012A` → `BBSM110_BBS012` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:41-42` |
| `BBSM013` | `BBS013A` | `BBSM013` | `BBS014A` → `BBSM013_CerData`;`BBS015A` → `BBSM013_BBS015`;`OFD220A` → `BBSM013_AllotData`;`OFD221A` → `BBSM013_AllotData_D`;`OFD234A` → `OFD234`;`OFD235A` → `OFD235` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:47-53` |
| `BBSM113` | `BBS013A` | `BBSM113` | 同上,DataTable 名的前綴改成畫面代號 113 那一組 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:46-52` |

三件在這張表上看不到、但會咬人的事:

1. **`BBSM003` 的明細宣告在執行期會被換掉。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:122-124` 在 `AfterAdd` 事件裡 `DetailTable.Clear()` 再重新 Add,把 `BBS004A` 對應的 DataTable 從 `BBSM003_CerData` 換成 `BBSM003_CerData_CK`。這是全模組唯一一處「在事件裡改主明細宣告」的寫法,見附錄 E6。

2. **`BBSM004` 的主檔實體表是 `BBS005A`,不是 `BBS004A`。** 命名上差一號,`BBS004A` 是 `BBSM003`(掛失)的明細。查影響面時最容易看錯的一組。

3. **`BBSM013` 的六張明細有四張不是 BBS 的表。** 四眼一次覆核會同時讓 OFD 的四張表生效,見 §8。

### 2.2 主鍵與四眼欄位

主鍵由 `App.config` 的 `pkey` 宣告(只宣告主檔那一層):

| 畫面 | 主檔 PK | 明細 PK(從 SQL 的 WHERE 與 xsd 的 key 反推) |
|---|---|---|
| `BBSM001` | 換發書號 | 換發書號 + 新舊憑證碼 + 期別 + 號碼 + 檢查碼 |
| `BBSM003` | 掛失書號 | 掛失書號 + 期別 + 號碼 + 檢查碼;文件明細為掛失書號 + 文件代碼 |
| `BBSM004` | 掛失撤銷書號 | 掛撤書號 + 期別 + 號碼 + 檢查碼 |
| `BBSM005` | 掛失補發書號 | 補發書號 + 掛補新舊憑證碼 + 期別 + 號碼 + 檢查碼 |
| `BBSM009` / `BBSM109` | 質設書號 | 質設書號 + 期別 + 號碼 + 檢查碼 |
| `BBSM010` / `BBSM110` | 質解書號 | 質解書號 + 質設書號 + 期別 + 號碼 + 檢查碼 |
| `BBSM013` / `BBSM113` | 轉讓書號 | 憑證明細為轉讓書號 + 三段碼;申購明細為申購書號 + 申購序號 |

錨點:`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:19`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:27`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:35`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:43`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:51`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:59`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:67`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:74`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:81`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/App.config:88`。

**四眼欄位在 BBS 是齊的。**本模組所有主檔與明細都帶全套 13 欄,中文名取自 xsd 的 `msdata:Caption`:

| 欄位 | 中文名 | 型別 |
|---|---|---|
| `STATUS` | 資料狀態碼 | string |
| `CREATEID` / `CREATEDATE` | 資料建立者 / 資料建立日期 | string / dateTime |
| `UPDATEID` / `UPDATEDATE` | 最後修改者 / 最後修改日期 | string / dateTime |
| `ENTRYID` / `ENTRYDATE` | 最後輸入者 / 最後輸入日期 | string / dateTime |
| `VERIFYID` / `VERIFYDATE` | 資料確認者 / 資料確認日期 | string / dateTime |
| `APPROVEID` / `APPROVEDATE` | 資料覆核者 / 資料覆核日期 | string / dateTime |
| `REJECTID` / `REJECTDATE` | 資料退回者 / 資料退回日期 | string / dateTime |
| `DATAFLAG` | 資料異動碼 | base64Binary(樂觀鎖) |

錨點以 `BBS009A` 為例:`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:82-137`。

**要注意的是日期欄的兩種型別並存。**業務日期(質設日期、掛失日期、轉讓日期)是 **string**,四眼日期是 **dateTime**。`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:51` 的質設日期是 `string`,同一張表 `:96` 的資料建立日期是 `dateTime`。程式碼到處在 `DateTimeHelper.DateToString` / `StringToDate` 之間轉,而 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:209` 留了註解「20140819 ATLAS ATLAS 修改日期為字串參數」——這是一次改型別的遺跡,不是設計。**後果:業務日期的大小比較在 SQL 裡是字串比較**,只要格式一致(`yyyy/MM/dd`)結果正確,但格式一旦混入 `yyyy-MM-dd` 就會靜默錯。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列業務欄,四眼 13 欄見 §2.2。

#### `BBS001A` — 憑證換發主檔(`BBSM001` 主檔)

| 欄位 | 中文名 | 型別 |
|---|---|---|
| `CHG_NO` | 換發書號 | string |
| `FUND_ID` | 基金代碼 | string |
| `FUND_SH_NM` | 基金中文簡稱 | string |
| `ID_NO` | 統一編號 | string |
| `BF_NO` | 受益人戶號 | decimal |
| `BF_NAME` | 受益人中文姓名 | string |
| `CHG_DATE` | 換發日期 | string |
| `CHG_UNIT` | 換發總單位數 | decimal |
| `CHG_TYPE` | 換發種類 | string |
| `CHG_P` | 換發張數 | int |
| `CHG_NO_O` | 換發書號-舊 | string |
| `UNIT_DEC` | 單位小數位數 | int |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM001Model.xsd:27-62`。

#### `BBS002A` — 憑證換發明細(`BBSM001` 明細)

| 欄位 | 中文名 |
|---|---|
| `CHG_NO` | 換發書號 |
| `NO_ID` | 新舊憑證碼(`'O'` 舊證 / `'N'` 新證) |
| `BF_CER_ISSUE_CODE` | 受益憑證期別 |
| `BF_CER_NO` | 受益憑證號碼 |
| `BF_CER_CHK` | 受益憑證檢查碼 |
| `BF_CER_DATE` | 憑証日期 |
| `CER_UNIT` | 憑證單位數 |
| `CHG_NO_O` | 換發書號-舊 |
| `CER_STATUS` | 憑證狀態(由 `OFD721` join 進來,非本表欄) |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM001Model.xsd:132-230`。

#### `BBS003A` / `BBS004A` / `BBS020A` — 掛失(`BBSM003`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS003A` | `LOS_NO` | 掛失書號(xsd 的 Caption 誤寫成「換發書號」,見附錄 E9) |
| `BBS003A` | `LOS_DT` | 掛失日期 |
| `BBS003A` | `LOS_UNIT` | 掛失總單位數 |
| `BBS003A` | `LOS_PRESS_BNG_DATE` / `LOS_PRESS_END_DATE` | 登報起 / 迄日(Caption 誤寫成 `CreateDate`) |
| `BBS004A` | `LOS_CD` | 掛失狀態碼 |
| `BBS004A` | `BF_CTL_SRNO` | 受益憑證紙張流水號 |
| `BBS004A` | `RLOS_NO` / `RLOS_DT` / `RLOS_MEMO` | 掛撤書號 / 掛撤日期 / 掛撤原因(由 `BBS005A` 回寫) |
| `BBS020A` | `LOS_DOC_CD` | 掛失文件代碼 |
| `BBS020A` | `DOC_ADATE` | 文件到期日期 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:27-52`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:133-217`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:326-341`。

#### `BBS005A` / `BBS006A` — 掛失撤銷(`BBSM004`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS005A` | `RLOS_NO` | 掛失撤銷書號 |
| `BBS005A` | `RLOS_DT` | 掛失撤銷日期 |
| `BBS005A` | `RLOS_UNIT` | 掛失撤銷總單位數 |
| `BBS006A` | `LOS_NO` | 掛失書號(指回 `BBS003A`) |
| `BBS006A` | `CER_UNIT` | 憑證單位數 |
| `BBS006A` | `CER_RUNIT` | 憑證贖回中單位數 |
| `BBS006A` | `RLOS_MEMO` | 撤銷原因 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM004Model.xsd:27-44`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM004Model.xsd:227-317`。

#### `BBS007A` / `BBS008A` — 掛失補發(`BBSM005`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS007A` | `CLOS_NO` | 掛失補發書號 |
| `BBS007A` | `CLOS_DT` | 掛失補發日期 |
| `BBS007A` | `CLOS_UNIT` | 掛失補發總單位數 |
| `BBS007A` | `CLOS_P` | 補發憑證張數 |
| `BBS008A` | `CLOS_NO_ID` | 掛補新舊憑證碼(`'O'` 舊證 / `'N'` 新證) |
| `BBS008A` | `LOS_NO` / `LOS_DT` | 掛失書號 / 掛失日期 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM005Model.xsd:25-46`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM005Model.xsd:123-156`。

#### `BBS009A` / `BBS010A` — 質權設定(`BBSM009` / `BBSM109`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS009A` | `TDCC_NO` | 集保質設書號 |
| `BBS009A` | `MOR_NO` | 質設書號 |
| `BBS009A` | `MOR_TYPE` | 質設型態(**這就是 §0.2 的切分欄位**) |
| `BBS009A` | `MOR_DT` | 質設日期 |
| `BBS009A` | `MOR_UNIT` | 質設總單位數 |
| `BBS009A` | `MOR_INT` | 質設孳息歸屬 |
| `BBS009A` | `MOR_TO_ID` / `MOR_TO` | 質權人ID / 質權人 |
| `BBS009A` | `MOR_DESC` | 質設說明 |
| `BBS010A` | `MOR_CD` | 質設狀態碼(`'M'` = 質設中) |
| `BBS010A` | `CER_UNIT` | 憑證單位數 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:25-75`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:153-178`。

#### `BBS011A` / `BBS012A` — 質權解除(`BBSM010` / `BBSM110`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS011A` | `CMOR_NO` | 質解書號 |
| `BBS011A` | `CMOR_TYPE` | 質解型態(**切分欄位**) |
| `BBS011A` | `CMOR_DT` | 質解日期 |
| `BBS011A` | `CMOR_UNIT` | 質解總單位數 |
| `BBS012A` | `MOR_NO` / `MOR_DT` | 對應的質設書號 / 質設日期 |
| `BBS012A` | `CER_UNIT` | 憑證單位數 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM010Model.xsd:25-53`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM010Model.xsd:124-157`。

#### `BBS013A` / `BBS014A` / `BBS015A` — 轉讓過戶(`BBSM013` / `BBSM113`)

| 表 | 欄位 | 中文名 |
|---|---|---|
| `BBS013A` | `TX_NO` | 轉讓書號 |
| `BBS013A` | `TX_DT` | 轉讓日期 |
| `BBS013A` | `TX_TYPE` | 轉讓型態(**切分欄位**) |
| `BBS013A` | `TX_ID` | 轉讓區分碼 |
| `BBS013A` | `BF_NO` / `BF_NAME` / `ID_NO` | 出讓人戶號 / 姓名 / ID |
| `BBS013A` | `BF_NO_TO` / `BF_NAME_TO` / `ID_NO_TO` | 受讓人戶號 / 姓名 / ID(ID 的 Caption 誤寫成「出讓人ID」) |
| `BBS013A` | `TX_UNIT` / `TX_NAV` / `TX_TAX` | 轉讓單位數 / 轉讓淨值 / 轉讓稅額 |
| `BBS013A` | `WRITEOFF_TYPE` | 銷帳方式 |
| `BBS014A` | 轉讓書號 + 憑證三段碼 + `CER_UNIT` | 被轉讓的實體憑證 |
| `BBS015A` | `ALLOT_NO` / `ALLOT_SRNO` | 出讓人的申購書號 / 序號 |
| `BBS015A` | `ALLOT_NO_TO` / `ALLOT_SRNO_TO` | 受讓人的新申購書號 / 序號 |
| `BBS015A` | `TX_UNIT` | 申購書轉讓單位數 |
| `BBS015A` | `CAN_REDEM_UNIT` | 可轉讓單位數 |

錨點 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:25-167`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:181-269`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:283-307`。

### 2.4 與其他模組共用的表

| 表 | 誰的 | BBS 怎麼用 | 影響面 |
|---|---|---|---|
| `OFD721` | OFD(主檔畫面 `OFDM721` / `OFDM725`) | 只 UPDATE 狀態欄與異動者,從不 INSERT / DELETE | 七條線全靠它,見 §2.5 |
| `OFD304A` | OFD | UPDATE 四個水位欄:掛失、實體質押、無實體質押、實體結餘 | 未宣告在任何 `xTableMapping`,是本模組最大的隱形相依,見附錄 D3 |
| `OFD310A` | OFD | `BBSM013` / `BBSM113` UPDATE 基金單位數結餘(境內) | 同上 |
| `OFD724` | OFD | 只 SELECT,判斷憑證是否已送簽 / 已註銷 | 三支畫面依賴,而且三處有同一個 Oracle 三值邏輯缺陷(附錄 E2) |
| `OFD220A` `OFD221A` | OFD(主檔畫面 `OFDM221A` / `OFDB310`) | `BBSM013` / `BBSM113` 會 INSERT 受讓人的新申購書 | 見 §8 |
| `OFD234A` `OFD235A` | OFD | 同上,支票與匯款明細 | 見 §8 |
| `BMS001A` | BMS | 只 join 取受益人姓名 | 唯讀 |
| `CTL014` | CTL | 掛失文件代碼與各式下拉的代碼說明 | 唯讀;分類碼寫死在 SQL 裡 |

### 2.5 憑證狀態碼 `CER_STATUS`(從程式反推)

`OFD721` 的 `CER_STATUS` 是全模組的中央狀態機。

> **更正(2026-09-15,來源:`ofd9.md` 的交叉驗證)。**本節原本寫「repo 內找不到值域定義檔,以下全部反推」, **那是錯的**——值域定義在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372` 的 `public static class CER_STATUS`,九個值都有中文。下表的「意義」欄已改成官方名稱,其中 `'2'`、`'8'` 與原本的反推**不同**,`'9'` 原本整個漏列。

「誰寫進去」欄仍然是從 UPDATE 語句反推的,那部分不變。

| 值 | 官方意義 | 誰寫進去 | 錨點 |
|---|---|---|---|
| `'1'` | 正常 | `BBSM001` 撤銷換發、`BBSM003` 撤銷掛失、`BBSM009` 撤銷質設 都把狀態還原成 `'1'` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:104`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:378`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:105` |
| `'2'` | **尚未簽証**(原誤作「已印製未交付」) | 沒有任何 BBS 畫面寫入;OFD 側由 `OFDM723` 簽證時 `'2'`→`'1'`(見 `ofd9.md`)。`BBSM005` 只當成「補發新證」的來源狀態讀 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:632`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:652` |
| `'3'` | 掛失中 | `BBSM003` 新增掛失 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:169` |
| `'4'` | 掛失已撤銷 | `BBSM004` 新增掛撤(來源必須是 `'3'`) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:218-225` |
| `'5'` | **掛失註銷**(補發後的舊證) | `BBSM005` 新增補發(來源必須是 `'3'`) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:187-195` |
| `'6'` | 質設中 | `BBSM009` 新增質設 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:201` |
| `'7'` | **質設解除** | `BBSM010` 新增質解(來源必須是 `'6'`) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:237-244` |
| `'8'` | **換發註銷**(原誤作「換發中」,意思相反——是舊證被註銷) | `BBSM001` 新增換發 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:376` |
| `'9'` | **已贖回**(原本整個漏列) | **全庫查不到誰寫**,推測由贖回批次寫入〔假設〕 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372` |

狀態機的兩個不對稱處,寫程式時要特別注意:

1. **質解之後狀態是 `'7'` 不是 `'1'`。** 也就是說一張質設過又解掉的憑證,狀態跟「從沒質設過」不同。`BBSM004` 的撤銷條件 `CER_STATUS IN ('1','4','7')`(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:109`)因此把 `'7'` 也算成「可以被打回掛失中」——這條 IN 清單是全模組唯一一處「多值來源」,對不對要看業務,程式上**確實可以把一張流通中的憑證打回掛失中**(附錄 E5)。

2. **`BBSM110` 的可質解計算只認 `'1'`。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:395` 與 `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:451` 的子查詢是 `WHERE CER_STATUS = '1'`,不含 `'7'`。這是無實體那一路,理論上跟憑證無關,卻依然去查憑證狀態——**假設**這是從實體版複製過來沒刪乾淨,依據是同一支的其餘邏輯完全不碰 `OFD721`。

### 2.6 其他代碼欄的值域

| 欄位 | 值 | 意義(推測) | 錨點 |
|---|---|---|---|
| `MOR_TYPE` / `CMOR_TYPE` / `TX_TYPE` | `'0'` | 實體憑證 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:166` |
| 同上 | `'1'` | 無實體 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:104` |
| `CHG_TYPE` | `'1'` / `'2'` / `'3'` | 一般換發 / 無實體換憑證 / 憑證換無實體 — **程式註解直接寫明** | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:475` |
| `NO_ID`(`BBS002A`) | `'O'` / `'N'` | 舊憑證 / 新憑證 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1395`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1444` |
| `CLOS_NO_ID`(`BBS008A`) | `'O'` / `'N'` | 舊憑證 / 新憑證 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:156`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:217` |
| `LOS_CD`(`BBS004A`) | `'L'` / `'I'` / `'D'` | 掛失中 / 已撤銷 / 已補發(**假設**,由寫入時機反推) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:147`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:244`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:162` |
| `MOR_CD`(`BBS010A`) | `'M'` | 質設中;質解後由 `BBSM010` 改掉 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:197`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:126` |
| `BF_CER_ISSUE_CODE` | `'99'` | 無實體的佔位期別〔客戶特定〕 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:122`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:180` |
| 下拉分類 `'244'` | 質解型態下拉 | 由共用下拉工具依分類碼取 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:51`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:45`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:48` |
| 下拉分類 `'245'` | 轉讓型態下拉 | join 進主檔 SQL 當顯示名 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1108`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1013` |
| `MOR_INT` 預設 | `'2'` | 質設孳息歸屬的預設值,寫死在 UI | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:49` |

**`'244'` 這個分類碼被三支畫面拿來當「質設型態」與「質解型態」的下拉來源**(`BBSM009` 用它顯示 `MOR_TYPE`、`BBSM010` 用它顯示 `CMOR_TYPE`),名稱與用途不完全對齊。要改型態值域,三支都得看。

## 3. 畫面清冊

### 3.1 維護 M(10 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `BBSM001` | 受益憑證換發(推測) | 齊 | `BBS001A` | `BBS002A` | 無 | 無 |
| `BBSM003` | 受益憑證掛失(推測) | 齊 | `BBS003A` | `BBS004A` `BBS020A` | 無 | 無 |
| `BBSM004` | 受益憑證掛失撤銷(推測) | 齊 | `BBS005A` | `BBS006A` | `f_GetToDoData` | 無 |
| `BBSM005` | 受益憑證掛失補發(推測) | 齊 | `BBS007A` | `BBS008A` | 無 | 無 |
| `BBSM009` | 受益憑證質權設定(實體,推測) | 齊 | `BBS009A` | `BBS010A` | 無 | 無 |
| `BBSM109` | 受益權單位質權設定(無實體,推測) | 齊 | `BBS009A` | `BBS010A` | 無 | 無 |
| `BBSM010` | 受益憑證質權解除(實體,推測) | 齊 | `BBS011A` | `BBS012A` | 無 | 無 |
| `BBSM110` | 受益權單位質權解除(無實體,推測) | 齊 | `BBS011A` | `BBS012A` | 無 | 無 |
| `BBSM013` | 受益憑證轉讓過戶(實體,推測) | 齊 | `BBS013A` | `BBS014A` `BBS015A` `OFD220A` `OFD221A` `OFD234A` `OFD235A` | 無 | 無 |
| `BBSM113` | 受益權單位轉讓過戶(無實體,推測) | 齊 | `BBS013A` | 同上 | 無 | 無 |

### 3.2 查詢 I

**本模組無 I 畫面。**原因見 §5。

### 3.3 批次 B

**本模組無 B 畫面,也沒有 WindowsService。**原因見 §6。

### 3.4 報表 R(7 支、13 份 rpt)

| 代號 | 中文名(程式內寫死) | 六層齊不齊 | SP | rpt |
|---|---|---|---|---|
| `BBSR002` | 受益憑證換發查核表 | 齊 | `s_TA_BBSR002_Get` | `BBSR002RPS` `BBSR002RPS1` |
| `BBSR006` | 受益憑證掛失(撤銷)查核表 | 齊 | `s_TA_BBSR006_Get` | `BBSR006RPS` `BBSR006RPS1` |
| `BBSR007` | 受益憑證掛失中清冊 | 齊 | `s_TA_BBSR007_Get` | `BBSR007RPS` `BBSR007RPS1` |
| `BBSR010` | 受益人質設(質解)查核表 | 齊 | `S_TA_BBSR010_GET` | `BBSR010RPS`(只有一份) |
| `BBSR011` | 受益人憑證質設(質解)查核表 | 齊 | `S_TA_BBSR011_GET` | `BBSR011RPS` `BBSR011RPS1` |
| `BBSR012` | 受益憑證質設中清冊 | 齊 | `S_TA_BBSR012_GET` | `BBSR012RPS` `BBSR012RPS1` |
| `BBSR015` | 轉讓過戶查核表 | 齊 | `s_TA_BBSR015_Get` | `BBSR015RPS` `BBSR015RPS1` |

### 3.5 一眼看出差別的五件事

1. **`BBSM001` 沒有 `1xx` 版,因為它把三種換發塞進同一支。** 換發種類 `'1'` / `'2'` / `'3'` 分別是一般換發、無實體換憑證、憑證換無實體(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:475`)。**這說明「實體 / 無實體」在這套系統裡有兩種做法:換發用一支畫面加型別欄,質設 / 質解 / 轉讓用兩支畫面。** 沒有統一。

2. **掛失三兄弟(`BBSM003` / `BBSM004` / `BBSM005`)只有實體版。** 無實體受益權沒有紙,不會遺失,所以沒有掛失流程——這是最合理的解釋,程式內找不到反證。

3. **`BBSM013` 是全模組唯一會建立別模組主檔的畫面。** 六張明細有四張屬於 OFD。

4. **`BBSM010` 的 PO 有 903 行,`BBSM110` 只有 500 行。** 差的不是功能,是寫法:`BBSM110` 用共用的參數組法(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:252`)、`BBSM010` 逐行串 SQL。

5. **報表只有 `BBSR010` 是單一 rpt。** 其餘六支都是「一般版 / 跳頁版」兩份,由畫面上的列印方式選項決定(§7.2)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] 三對平行畫面：型態欄怎麼切、水位欄與庫存檢核怎麼分、明細怎麼來，以及只在單邊存在的五條業務規則
圖中文字:① 三對畫面共用同一組表，靠一個型態欄切成兩個互不相見的世界 / BBSM009 實體質設 / 寫入 MOR_TYPE='0' / BBSM109 無實體質設 / 寫入 MOR_TYPE='1' / BBS009A ＋ BBS010A / 兩支共用的主與明細 / BBSM010 實體質解 / 寫入 CMOR_TYPE='0' / BBSM110 無實體質解 / 寫入 CMOR_TYPE='1' / BBS011A ＋ BBS012A / 兩支共用的主與明細 / BBSM013 實體轉讓 / 寫入 TX_TYPE='0' / BBSM113 無實體轉讓 / 寫入 TX_TYPE='1' / BBS013A ＋ 六張明細 / 含 OFD220A OFD221A / ② 真正的差別一：扣的水位欄不同，同一張表兩個獨立水位 / 實體版動 BAL_MOR_UNIT / OFD304A / 無實體版動 BAL_MOR_UNIT_S / OFD304A / OFD721 只有實體版會動 / 無實體整條繞過憑證檔 / ③ 真正的差別二：檢核比的庫存數不同（共用工具回三個數） / 共用工具算 全部／實體／無實體 / 十支畫面都呼叫它 / 實體版比 實體結餘 / BBSM001 003 009 013 / 無實體版比 無實體結餘 / BBSM109 113 另扣鎖利定額 / ④ 真正的差別三：明細怎麼來 / 實體：使用者逐張勾憑證，存檔比對加總 / 明細可以有很多列 / 無實體：程式塞一列期別 '99' 假憑證 / 一張單永遠只有一列明細 / ⑤ 只在一邊有的業務規則與缺陷 —— 這排才是「改一支要不要同步」的答案 / 質權人不可等於受益人 / 只有 BBSM109 有 / 轉讓稅額與淨值必須大於 0 / 只有 BBSM013 有 / 過帳後不可刪除 / 只有 BBSM113 有 / 撤銷更新結餘失敗不擋 / 只有 BBSM109 這樣 / 刪未覆核單做庫存檢核 / 只有 BBSM110 這樣 / 跳號號別用錯 兩邊各錯一半 / 見附錄 E1
```

*圖:圖 3 三對 1xx 平行畫面。橘框=實體版；橘虛框=無實體版；灰虛框=兩邊共用的表；黑框=無原始碼的外部表或已確認的缺陷。①②③④ 是可從程式判定的差異；⑤ 那六格是單邊才有的行為，程式碼無法判斷哪邊才對，必須問業務。*

本節的共同結構:每支畫面先講用途,再講四層卡控(§1.3),最後一張卡控總表。**卡控結果一律五類:阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋。**

四件全模組共通、不在各節重複的事:

| 共通行為 | 說明 | 錨點(以 `BBSM009` 為例) |
|---|---|---|
| 註銷戶檢核 | 新增與刪除前都問一次 `IsFreeze`,是註銷戶就阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:188`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:226` |
| 結帳日檢核 | 業務日期必須大於該基金最大資料控制日期,否則阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:293-300` |
| 營業日檢核 | 依帳務型態(交易日結帳 / 淨值日)取該基金行事曆,日期不是營業日就阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:314-333` |
| 基金成立 / 發行日檢核 | 業務日期不得小於基金成立日與發行日 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:335-379` |
| 跳號一覽表 | 七個四眼事件全部只做一件事:呼叫跳號紀錄器 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:833-880` |

### 4.1 `BBSM001` — 受益憑證換發

#### 用途(推測)

把受益人手上的舊憑證換成新憑證,或在「實體」與「無實體」之間互換。主檔 `BBS001A` 一張單,明細 `BBS002A` 用新舊憑證碼區分:`'O'` 是繳回的舊證、`'N'` 是發出的新證。

換發種類決定三件事(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:475-513`):

| 換發種類 | 意義 | 要不要舊證明細 | 要不要新證明細 | 單位數要等於誰 |
|---|---|---|---|---|
| `'1'` 一般換發 | 憑證換憑證 | 要 | 要 | 兩邊都要等於換發總單位數 |
| `'2'` 無實體換憑證 | 無實體變成紙 | 不要 | 要 | 新證加總 |
| `'3'` 憑證換無實體 | 紙變成無實體 | 要 | 不要 | 舊證加總 |

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:675-676` 有一處會**把換發種類鎖成 `'3'` 並設唯讀**,是由畫面上的某個入口帶進來的情境(從 Designer 上看是切到某個分頁時),意思是「這條路只做憑證換無實體」。

#### 必填與存檔前檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:376-580` 的 `DoValidate()`,順序是:

1. 換發總單位數必須大於 0(`:387`)。

2. 換發日期必須大於該基金最近結帳日期(`:401`)。

3. 換發日期必須大於該基金最近大憑證日期(`:417`)。**這條只有 `BBSM001` 有**,其餘畫面的同一段都被註解掉了(例:`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:303-312`)。

4. 換發日期必須是該基金營業日(`:427`);基金必須已成立(`:431`);不得小於成立日(`:435`)與發行日(`:515`)。

5. 種類 `'1'` / `'2'` 時原始憑證至少勾一筆(`:452`)。

6. 換發張數必須等於新證明細筆數(`:479`)。

7. 三組單位數加總比對,依種類走不同分支(`:484` / `:499` / `:504` / `:509`)。

8. 每張新證的單位數必須大於 0(`:492`)。

9. 庫存比對:總結餘不足阻擋(`:531`);種類 `'2'` 比無實體結餘(`:541`)、種類 `'1'` / `'3'` 比實體結餘(`:551`)。

10. 沖銷檢核:已被沖銷的憑證不可新增(`:565-570`)。

#### 刪除前的檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:278-360`:結帳日、大憑證日期、是否已送簽、是否已註銷、無實體單位數是否足夠(`:347`)、註銷戶(`:359`)。

**這裡有本模組最嚴重的缺陷:「是否已送簽」那條永遠不會成立。**見附錄 E2。

#### 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 配換發書號,重覆就再配一次 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:296-315` |
| `AfterAdd` | 舊證狀態改「換發中」;新證寫入用印檔;調整實體結餘;回寫受益人憑証檔的憑證號碼 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:316-792` |
| `AfterVerify` / `AfterApprove` / `AfterReject` / `AfterResend` / `AfterDelete` / `AfterUnDelete` | **只寫跳號一覽表** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1621-1665` |
| `AfterApproveDelete` | 把 `AfterAdd` 的四件事全部倒回去 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:82-294` |

#### 跨表更新

| 表 | 動作 | 錨點 |
|---|---|---|
| `OFD721` | 舊證狀態 → 換發中;撤銷時 → 正常 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:375`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:103` |
| `OFD724` | 新證 INSERT 用印資料;撤銷時 UPDATE 回去 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:406`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:145` |
| `OFD304A` | 實體結餘加減淨變動,而且**只在淨變動不為 0 時才下 SQL** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:750-761` |
| `OFD0814A` | 回寫該基金的憑證流水號 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:774-787` |

**`OFD0814A` 那一段的 WHERE 只有基金代碼,沒有任何其他條件**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:778-780`),而後面用「更新列數不等於 1 就 throw」當保護。這代表程式**假設**該表在一檔基金上只會有一列。假設一旦不成立(同基金兩列以上),這支畫面會直接把那些列全改掉、然後丟例外回滾——但如果交易被別的路徑提早提交,就是資料毀損。詳見附錄 E4。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 換發總單位數 ≤ 0 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:387` |
| 新增前 | 換發日期 ≤ 最近結帳日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:401` |
| 新增前 | 換發日期 ≤ 最近大憑證日期 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:417` |
| 新增前 | 換發日期非基金營業日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:427` |
| 新增前 | 基金尚未成立 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:431` |
| 新增前 | 種類 `'1'`/`'2'` 未勾原始憑證 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:452` |
| 新增前 | 換發張數 ≠ 新證筆數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:479` |
| 新增前 | 單位數三方加總不符 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:484-509` |
| 新增前 | 總 / 實體 / 無實體結餘不足 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:531-555` |
| 新增前 | 憑證已有沖銷資料 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:565-570` |
| 新增前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:266` |
| 選受益人時 | 受益人為註銷戶 | 提示後仍可繼續操作 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:641` |
| 選日期時 | 該基金本日期無公告淨值行事曆 | 提示,不阻擋 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:703` |
| 按印鑑時 | 查無印鑑資料 | 提示 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:1141` |
| 刪除前 | 換發日期已過帳 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:293` |
| 刪除前 | 無實體單位數不足 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:347` |
| 刪除前 | **憑證已送簽** | **永遠不成立(缺陷)** | 阻擋(失效) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1397` |
| 刪除前 | 憑證已註銷 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1446` |
| 覆核後刪 | `OFD721` 不在「換發中」 | 回滾 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:112` |
| 覆核後刪 | 無實體單位數不足(SQL 內再驗一次) | 回滾 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:280` |

### 4.2 `BBSM003` — 受益憑證掛失

#### 用途(推測)

受益人聲明憑證遺失。一張掛失單鎖定一批憑證(明細 `BBS004A`),同時記錄要補齊的掛失文件與到件日(明細 `BBS020A`),並登報(主檔有登報起迄日兩欄)。

#### 必填與存檔前檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:550-700` 的 `DoValidate()`:

1. 登報迄日不得小於起日(`:559`)。

2. 掛失總單位數必須大於 0(`:565`)。

3. 掛失日期必須大於最近結帳日(`:579`)、不得小於基金發行日(`:585`)與成立日(`:616`)、必須是營業日(`:598` / `:606`)。

4. 庫存比對:比總結餘(`:649`)與**實體**結餘(`:656`)。無實體那一行被註解掉(`:648`)。

5. 掛失總單位數必須等於明細加總(`:689`);掛失憑證至少勾一筆(`:693`);完全沒有憑證資料時阻擋(`:697`)。

新增鈕上另有三條(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:172-330`):註銷戶(`:191`)、可掛失單位數(`:218`)、鎖利定額扣除後的可掛失單位數(`:230`)、實體庫存單位數(`:244`)、沖銷資料(`:322-327`)。

#### 修改時的額外檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:369`:掛失憑證中若有已補發的資料,文件到件日期不可清空。另外在文件 grid 上,到期日不可小於掛失日(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:1445`)。

#### 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 配掛失書號,並把書號回填到文件明細與憑證明細 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:87-111` |
| `AfterAdd` | **先把明細宣告換掉**,再加掛失結餘、把憑證打成掛失中 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:113-180` |
| 其餘六個 | 只寫跳號一覽表 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1362-1411` |
| `AfterApproveDelete` | 憑證打回正常、掛失結餘扣回 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:362-460` |

#### 跨表更新

| 表 | 動作 | 錨點 |
|---|---|---|
| `OFD304A` | 掛失水位加上掛失總單位數;撤銷時扣回 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:129-130`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:450-451` |
| `OFD721` | 狀態 → 掛失中;撤銷時來源必須是掛失中才改回正常 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:169`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:378-385` |

#### 三支取數方法的口徑各不相同

這支畫面向後端要「可掛失單位數」的方法有三支,三個 SQL 的算法都不一樣:

| 方法 | 算式 | 錨點 |
|---|---|---|
| 取實體庫存 | `BAL_SCRIP_UNIT` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1125` |
| 取可贖回 | `BAL_UNIT - ON_REDEM_UNIT` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1179` |
| 取可掛失 | `BAL_SCRIP_UNIT - BAL_LOSS_UNIT - BAL_MOR_UNIT` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1231` |

三個都被 UI 在不同時點呼叫,**使用者看到的「可掛失單位數」會依觸發路徑不同而不同**。要改口徑,三支都要改。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:191` |
| 新增前 | 掛失總單位數 > 可掛失單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:218` |
| 新增前 | 掛失總單位數 > 扣除鎖利定額後的可掛失數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:230` |
| 新增前 | 掛失總單位數 > 實體庫存 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:244` |
| 新增前 | 憑證已有沖銷資料 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:327` |
| 新增前 | 登報迄日 < 登報起日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:559` |
| 新增前 | 掛失總單位數 ≤ 0 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:565` |
| 新增前 | 掛失日期 ≤ 最近結帳日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:579` |
| 新增前 | 掛失日期非營業日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:598` |
| 新增前 | 明細加總 ≠ 掛失總單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:689` |
| 新增前 | 未勾任何掛失憑證 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:693` |
| 修改前 | 已補發的憑證,文件到件日被清空 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:369` |
| 文件 grid | 文件到期日 < 掛失日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:1445` |
| 文件 grid | 日期格式錯誤 | 提示後清空 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:1461` |
| 刪除前 | 掛失日期已過帳 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:451` |
| 刪除前 | 憑證狀態不為掛失中 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:462` |
| 刪除前 | 掛失日期 ≤ 集保大憑證換發日期 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:498` |
| 刪除前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:538` |
| 覆核後刪 | `OFD721` 不在掛失中 | 回滾 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:385` |
| 查詢 | 明細 SQL 硬加掛失狀態碼不等於已補發 | **過濾(無提示)** | 過濾 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1285` |

### 4.3 `BBSM004` — 受益憑證掛失撤銷

#### 用途(推測)

掛失的憑證找回來了,把掛失狀態解掉。主檔 `BBS005A`,明細 `BBS006A` 列出要撤銷的憑證,並帶著原掛失書號與撤銷原因。

#### 必填與存檔前檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:66-235` 的 `DoValidate()`:

1. 掛撤總單位數必須大於 0(`:77`)。

2. 掛撤日期必須大於最近結帳日(`:91`)、基金必須已成立(`:96`)、不得小於成立日(`:100`)與發行日(`:184`)、必須是營業日(`:131` / `:139`)。

3. 掛撤總單位數必須小於等於可掛撤單位數(`:153`),而且明細至少勾一筆(`:174`)、加總要相等(`:177`)。

4. 逐筆比對:掛撤日期不可小於該筆的掛失日期(`:230`)。

#### 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 配掛撤書號並回填到明細 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:166-183` |
| `AfterAdd` | 掛失水位扣回;憑證由掛失中 → 已撤銷;掛失明細狀態 → 已撤銷 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:186-261` |
| `AfterApproveDelete` | 全部倒回:憑證打回掛失中、掛失水位加回、掛失明細狀態打回掛失中 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:86-164` |
| 其餘六個 | 只寫跳號一覽表 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:1095-1135` |

#### 這支畫面的三個特別之處

1. **主檔 SQL 直接把使用者輸入串進 WHERE。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:373` 與 `:377` 把受益人 ID 用字串串接組進 SQL,沒有參數化。同一支 PO 的其他條件都走 `AddParam` 產生具名參數。見附錄 E3。

2. **待辦清單的自審排除條件括號組法特殊。** `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:390` 是 `AND ((主檔.UpdateID <> '登入者') OR (主檔.RejectID = ''))`。在 Oracle 裡 `RejectID = ''` 恆為 UNKNOWN(空字串就是 NULL),所以這個 OR 的右半永遠不成立;整條等價於只剩 `UpdateID <> '登入者'`,而 `UpdateID` 為 NULL 時又整條 UNKNOWN——**結果是「修改者欄位是空的單」不會出現在任何人的待辦**。見附錄 E2。

3. **Control 層是 1,647 行的手寫逐欄對應。** 全模組唯一沒有用共用搬運工具的 Ctl,而且漏了一欄。見下一段與附錄 E7。

#### 撤銷原因永遠存不進去

| 事實 | 錨點 |
|---|---|
| 明細 SQL 有 SELECT 撤銷原因 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:422` |
| UI 把畫面上的撤銷原因寫進 View | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:413` |
| UI 讀回來也會顯示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:286` |
| **Ctl 的 View → Model 逐欄搬運完全沒有這一欄** | `Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM004_Ctl.cs:691-1028`(整段 `BBSM004_Cer_CK` 的搬運,463 個逐欄指派裡沒有一個是撤銷原因) |

也就是說使用者打的撤銷原因會被靜默丟掉。這正是 BMS 那條「手寫逐欄對應,來源加欄位沒跟著改就永遠空白」的同型缺陷,嚴重度高。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:389` |
| 新增前 | 掛撤總單位數 ≤ 0 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:77` |
| 新增前 | 掛撤日期 ≤ 最近結帳日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:91` |
| 新增前 | 基金尚未成立 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:96` |
| 新增前 | 掛撤日期非營業日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:131` |
| 新增前 | 掛撤總單位數 > 可掛撤單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:153` |
| 新增前 | 未勾任何明細 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:174` |
| 新增前 | 明細加總 ≠ 掛撤總單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:177` |
| 新增前 | 掛撤日期 < 該筆掛失日期 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:230` |
| 刪除前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:488` |
| 刪除前 | 掛撤日期已過帳 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:504` |
| 刪除前 | 憑證已有沖銷資料 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:549` |
| 新增後 | `OFD721` 不在掛失中 | 回滾,訊息「尚未掛失,不可掛失撤銷」 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:234-235` |
| 覆核後刪 | `OFD721` 不在 `'1'`/`'4'`/`'7'` 或已有贖回中單位 | 回滾,訊息「已被沖銷,不可刪除」 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:109-119` |
| 待辦查詢 | 排除自己送的單 | **過濾(無提示),且條件寫法有缺陷** | 過濾 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:390` |
| 存檔 | 撤銷原因 | **靜默丟棄(缺陷)** | 記錄不擋 | `Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM004_Ctl.cs:691` |

### 4.4 `BBSM005` — 受益憑證掛失補發

#### 用途(推測)

掛失的憑證找不回來,註銷舊證並印新證。主檔 `BBS007A`,明細 `BBS008A` 用掛補新舊憑證碼區分:`'O'` 是被註銷的舊證、`'N'` 是補發的新證。補發張數欄位為 0 時代表「補成無實體」,程式用它切開兩套結餘調整(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:457`)。

#### 必填與存檔前檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:429-620` 的 `DoValidate()`:

1. 補發總單位數必須大於 0(`:438`)。

2. 補發日期必須大於最近結帳日(`:455`)、必須是營業日(`:492`)、基金必須已成立(`:507`)、不得小於成立日(`:511`)與發行日(`:614`)。

3. 掛失憑證至少勾一筆(`:527`);補發憑證單位數要等於掛失憑證單位數(`:553`)。

4. 有補發張數時,張數必須等於補發明細筆數(`:560` / `:564`);每張單位數必須大於 0(`:582`)。

5. 兩邊加總都必須等於補發總單位數(`:588` / `:596`)。

新增鈕上另有:註銷戶(`:252`)、逐筆比對「掛補日期應大於掛失日期」(`:274`)。

#### 四眼各階段附加動作

| 階段 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | 配補發書號 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:83-108` |
| `AfterAdd` | 舊證:掛失明細狀態 → 已補發、憑證狀態 由掛失中 → 已註銷;新證:寫入用印檔、回寫受益人憑証檔;調整實體結餘與掛失水位 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:110-491` |
| `AfterApproveDelete` | 全部倒回 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:544-779` |
| 其餘六個 | 只寫跳號一覽表 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:1293` 起 |

#### 兩條失效的刪除卡控

`BBSM005` 有兩支專門的判斷方法,兩支的 SQL 都用 `VISA_NO <> ''` / `VISA_UID_D <> ''`:

| 方法 | 用途 | 錨點 | 問題 |
|---|---|---|---|
| `IsEmit` | 判斷補發資料是否已發行 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:914` | Oracle 空字串即 NULL,條件恆為 UNKNOWN,**永遠 0 筆** |
| `IsCancel` | 判斷補發資料是否已註銷 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:964` | 同上 |

呼叫端 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:352-360` 因此拿到的永遠是「沒有已送簽的憑證」,「憑證號碼 … 已送簽,不可刪除」這條訊息在正式環境不可能出現。見附錄 E2。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:252` |
| 新增前 | 掛補日期 ≤ 該筆掛失日期 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:274` |
| 新增前 | 補發總單位數 ≤ 0 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:438` |
| 新增前 | 補發日期 ≤ 最近結帳日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:455` |
| 新增前 | 補發日期非營業日 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:492` |
| 新增前 | 基金尚未成立 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:507` |
| 新增前 | 未勾任何掛失憑證 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:527` |
| 新增前 | 補發憑證單位數 ≠ 掛失憑證單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:553` |
| 新增前 | 未輸補發張數 / 張數與筆數不符 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:560-564` |
| 新增前 | 單張補發單位數 ≤ 0 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:582` |
| 新增前 | 兩邊加總 ≠ 補發總單位數 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:588-596` |
| 刪除前 | 受益人為註銷戶 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:336` |
| 刪除前 | **憑證已送簽** | **永遠不成立(缺陷)** | 阻擋(失效) | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:357` |
| 刪除前 | 補發日期已過帳 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:395` |
| 刪除前 | 無實體單位數不足 | 阻擋 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:415` |
| 新增後 | 舊證不在掛失中 | 回滾 | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:195` |

### 4.5 `BBSM009` / `BBSM109` — 受益憑證 / 受益權單位 質權設定

這是三對平行畫面的第一對。**同一張主檔 `BBS009A`、同一張明細 `BBS010A`,靠質設型態切開**(§0.2)。

#### 4.5.1 兩支到底有多像:逐層量測

把 `BBSM109` 全檔的代號代換成 `BBSM009` 後做逐行序列比對,結果如下(方法與 `runbooks/add-screen.md` 判斷樣板時用的一樣):

| 層 | 本體行數 | 平行版行數 | 相同行 | 相似度 |
|---|---|---|---|---|
| UI | 848 | 753 | 325 | 0.406 |
| FormProxy | 379 | 118 | 57 | 0.229 |
| Control | 373 | 164 | 93 | 0.346 |
| PO | 891 | 633 | 308 | 0.404 |

**結論:不是複本,是重寫。**代號代換後仍有六成內容對不上,而且對不上的部分不是排版差異,是方法簽名與實作路線不同(下一段)。同一組量測在第三對(`BBSM013` / `BBSM113`)是 0.46–0.60,那一對才真的接近複本。

#### 4.5.2 真的不同的地方

| 面向 | `BBSM009`(實體) | `BBSM109`(無實體) |
|---|---|---|
| 檔案編碼 | PO 是 cp950 | PO 是 UTF-8 with BOM |
| PO 公開方法簽名 | 具名型別 `BBSM009ModelVDB GetXxx(BBSM009ModelVDB)` | 泛型 `T GetXxx<T>(T model, params object[] args)` |
| 公開方法數 | 9 支(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:26-34`) | 4 支(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:24-27`) |
| 明細來源 | 使用者在憑證 grid 逐張勾選,存檔時比對勾選加總 | 程式自動塞一列期別 `'99'` 的假憑證 |
| 明細 SQL | 無(明細靠框架依 mapping 撈) | 自己組(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:377`) |
| 是否動 `OFD721` | 會:狀態 → 質設中、撤銷時 → 正常 | **完全不動** |
| 動的結餘欄 | 實體質押水位 | 無實體質押水位 |
| 庫存檢核 | 比總結餘 + 實體結餘 | 比無實體結餘,而且**先扣掉鎖利定額單位數**(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:700-711`) |
| 解構子 | 空的(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:45-47`) | 逐一 `-=` 解掛事件(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:60-81`) |
| 刪除前額外檢核 | 明細中有已被質解的憑證就阻擋(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:259`) | 該書號已被質解就阻擋(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:227`) |
| 質權人 ID 檢核 | **沒有** | 有:質權人 ID 不可等於受益人 ID(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:740`) |

**最後一列是真正的業務差異,不是寫法差異:實體版沒有「質權人不可是自己」這條卡控。**兩支畫面寫的是同一張表,所以同一條業務規則在實體那一路是放行的。要嘛規則本來就只適用無實體,要嘛實體版漏了——程式碼本身無法分辨,**需要業務確認**。

#### 4.5.3 只差代號的部分

下列項目在兩支之間除了代號以外完全一致,改動時等於同一段程式:

- 七個四眼事件的跳號一覽表寫法(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:833-880` vs `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:581-628`)。

- 註銷戶檢核、最大控制日期檢核、營業日檢核三段(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:184-200` vs `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:151-160`)。

- 印鑑鈕與「查無此客戶的印鑑資料」提示(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:817` vs `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:603`)。

- 撤銷時更新結餘檔的 SQL 骨架(只有欄名不同)。

#### 4.5.4 用途與存檔前檢核(實體版)

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:271-430`:

1. 質設總單位數必須大於 0(`:282`)。

2. 質設日期必須大於最近結帳日(`:299`)、必須是營業日(`:323`)、不得小於基金成立日(`:346`)與發行日(`:372`)。

3. 必須勾選明細(`:356`);質設總單位數必須等於勾選明細加總(`:360`)。

4. 庫存:總結餘不足阻擋(`:394`)、實體結餘不足阻擋(`:402`)。

5. 沖銷檢核:已有沖銷資料的憑證不可新增(`:416-420`)。

**`:286-287` 有一條被註解掉的「質設日期必須小於等於系統日期」**,註解註明 2009/04/28 取消。也就是現在可以開未來日期的質設單,只要日期落在營業日且大於結帳日。

#### 4.5.5 跨表更新

| 表 | `BBSM009` | `BBSM109` |
|---|---|---|
| `OFD721` | 新增時 → 質設中(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:201`);覆核後刪時來源必須是質設中才改回正常(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:105-112`) | 不動 |
| `OFD304A` | 實體質押水位 ±(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:231`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:134`) | 無實體質押水位 ±(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:140`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:229`) |
| `BBS010A` | 明細的質設狀態碼設為質設中 | 同樣設質設中,但只有一列假憑證 |

**兩邊撤銷時的錯誤處理不一致**:`BBSM009` 更新結餘檔失敗會 `throw`(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:148-151`),`BBSM109` 的同一段 `throw` 被註解掉了(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:240-241`),更新 0 列也會當成成功。見附錄 E8。

#### 4.5.6 卡控總表

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 受益人為註銷戶 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:192`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:155` |
| 新增前 | 質設總單位數 ≤ 0 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:283`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:683` |
| 新增前 | 質設日期 ≤ 最近結帳日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:300`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:655` |
| 新增前 | 質設日期非營業日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:325`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:669` |
| 新增前 | 基金尚未成立 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:343`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:726` |
| 新增前 | 未勾選任何憑證 | 只有 `BBSM009` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:357` |
| 新增前 | 總單位數 ≠ 明細加總 | 只有 `BBSM009` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:361` |
| 新增前 | 實體結餘不足 | 只有 `BBSM009` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:404` |
| 新增前 | 無實體結餘不足(已扣鎖利定額) | 只有 `BBSM109` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:715` |
| 新增前 | 質權人 ID = 受益人 ID | **只有 `BBSM109`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:740` |
| 新增前 | 憑證已有沖銷資料 | 只有 `BBSM009` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:420` |
| 刪除前 | 質設日期已過帳 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:251`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:221` |
| 刪除前 | 明細有已質解憑證 / 書號已被質解 | 兩支(判法不同) | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:260`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:227` |
| 選日期時 | 無公告淨值行事曆 | 兩支 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:495`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:395` |
| 選受益人時 | 註銷戶 | 只有 `BBSM009` 在此時點再提醒一次 | 警示 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:673` |
| 輸入 ID 時 | ID 與戶號不符 | 兩支 | 詢問 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:827`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:615` |
| 覆核後刪 | `OFD721` 不在質設中 | 只有 `BBSM009` | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:122-125` |
| 覆核後刪 | 更新結餘檔失敗 | `BBSM009` 阻擋 / `BBSM109` **不擋** | 阻擋 / 記錄不擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:148`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:240` |
| 查詢 | 質設型態硬條件 | 兩支各自 | **過濾(無提示)** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:350`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:284` |

### 4.6 `BBSM010` / `BBSM110` — 受益憑證 / 受益權單位 質權解除

第二對平行畫面,切分欄位是質解型態。

#### 4.6.1 逐層量測

| 層 | 本體行數 | 平行版行數 | 相同行 | 相似度 |
|---|---|---|---|---|
| UI | 837 | 549 | 164 | 0.237 |
| FormProxy | 355 | 65 | 32 | 0.152 |
| Control | 363 | 222 | 88 | 0.301 |
| PO | 919 | 500 | 155 | 0.218 |

**這一對是三對裡差最遠的。**FormProxy 相似度 0.152 意味著兩邊對外暴露的方法幾乎沒有交集:`BBSM010` 有十支取數方法(含取下一營業日、取基金營業日、取發行日、檢核質解日期),`BBSM110` 只有一支(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:311`)。差別在於 `BBSM110` 把大部分檢核搬到 SQL 裡一次做完。

#### 4.6.2 真的不同的地方

| 面向 | `BBSM010`(實體) | `BBSM110`(無實體) |
|---|---|---|
| 明細來源 | 從 `BBS010A` 撈出該受益人所有質設中的憑證,逐張勾選、逐張填質解單位數 | 沒有 grid,整張單一個數字 |
| 是否動 `OFD721` | 會:質設中 → 已質解 | 不動,但**仍有兩處子查詢在讀 `OFD721`**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:395`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:451`) |
| 庫存檢核位置 | 前端逐條 `AddError` | **後端 SQL 一次算**:`BAL_UNIT - BAL_SCRIP_UNIT - 無實體質押 - 本次 - 贖回中 + 憑證贖回中加總 >= 0` |
| `AfterDelete` | 只寫跳號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:867-872`) | **另外做庫存檢核,不足就阻擋刪除**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:387-406`) |
| SQL 組法 | 逐行字串相加 | 集中在 `AddParam` 共用組法(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:252`) |

`AfterDelete` 那一列是行為差異:**同樣是「刪除一張尚未覆核的質解單」,無實體版會擋、實體版不會。**

#### 4.6.3 存檔前檢核(實體版)

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:224-425`:

1. 註銷戶(`:247`)。

2. 逐筆:質解日期不可小於該筆質設日期(`:292`)。

3. 質解日期必須大於最近結帳日(`:308`)、大於該基金大憑證最大日期(`:321`)、必須是營業日(`:336`)、基金必須已成立(`:352`)、不得小於成立日(`:357`)。

4. 質解總單位數必須大於 0(`:364`);明細至少勾一筆(`:379`);加總必須相等(`:393`)。

5. 可質解單位數檢核(`:407`)。

無實體版的對應在 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:225-295`,多了四條 grid 層級的檢核:至少勾一筆(`:275`)、質解單位數必填且不可為 0(`:277`)、不可大於未質解單位數(`:279`)、質解日期不可小於質設日期(`:281`)。

#### 4.6.4 卡控總表

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 受益人為註銷戶 | `BBSM010` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:247` |
| 新增前 | 質解日期 < 質設日期 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:292`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:281` |
| 新增前 | 質解日期 ≤ 最近結帳日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:308`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:237` |
| 新增前 | 質解日期 ≤ 大憑證最大日期 | 只有 `BBSM010` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:321` |
| 新增前 | 質解日期非營業日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:336`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:247` |
| 新增前 | 基金尚未成立 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:352`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:266` |
| 新增前 | 質解總單位數 ≤ 0 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:364`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:259` |
| 新增前 | 未勾任何明細 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:379`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:275` |
| 新增前 | 總數 ≠ 明細加總 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:393`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:288` |
| 新增前 | 質解單位數 > 未質解單位數 | 只有 `BBSM110` | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:279` |
| 新增前 | 超過可質解單位數 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:407`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:292` |
| 刪除前 | 受益人為註銷戶 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:178`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:132` |
| 刪除前 | 質解日期已過帳 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:199`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:140` |
| 刪除時 | 無實體庫存不足 | **只有 `BBSM110`** | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:404-405` |
| 新增後 | `OFD721` 不在質設中 | 只有 `BBSM010` | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:244` |
| 覆核後刪 | 無實體庫存不足 | 只有 `BBSM110` | 阻擋 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:448` |
| 查詢 | 質解型態硬條件 | 兩支各自 | **過濾(無提示)** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:384`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:210` |
| 查詢 | 明細 SQL 另加質設型態 = 實體 | 只有 `BBSM010` | **過濾(無提示)** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:522`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:821` |

### 4.7 `BBSM013` / `BBSM113` — 受益憑證 / 受益權單位 轉讓過戶

第三對平行畫面,也是全模組最重的一支:一張主檔 `BBS013A` 掛六張明細,一次覆核同時在 BBS 與 OFD 兩邊生效。

#### 4.7.1 用途(推測)

出讓人把持有單位數過戶給受讓人。程式做三件事:

1. **銷帳(WriteOff)**:把要轉讓的單位數,從出讓人的各筆申購書上依指定順序扣掉。

2. **產生受讓人的新申購書**:對每一筆被扣到的申購明細,配一個新申購書號,寫入 `OFD220A` / `OFD221A`,並把原本掛在該申購書上的支票(`OFD234A`)與匯款(`OFD235A`)資料一併複製。

3. **調整雙方結餘**:出讓人扣、受讓人加,`OFD304A` 與 `OFD310A` 各一次。實體版另外把 `OFD721` 上那幾張憑證的受益人改成受讓人。

銷帳順序由畫面上的銷帳方式決定(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:292-303`):

| 值 | 意義(程式註解) | 排序鍵 |
|---|---|---|
| `'0'` | 照書號 | `ALLOT_NO, ALLOT_DATE` |
| `'1'` | 先單筆 | `DATA_TYPE, ALLOT_NO, ALLOT_DATE` |
| `'2'` | 先小額 | `DATA_TYPE DESC, ALLOT_NO, ALLOT_DATE` |

`'1'` 與 `'2'` 的差別只有 `DATA_TYPE` 的排序方向,而 `DATA_TYPE` 只有兩個值(`'1'` 一般 / `'2'` 定期定額,`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:266`)。**所以「先單筆」與「先小額」的實際效果是「一般優先」與「定期定額優先」,跟金額大小無關。**這兩個選項的中文名與行為不一致,列進附錄 E。

實際扣數在 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:310-325`:依排序逐筆取 `Math.Min(剩餘轉讓數, 該筆可轉讓數)`,扣完為止,扣不到的填 0,之後由 Control 層把 0 的那幾列刪掉。

#### 4.7.2 逐層量測

| 層 | `BBSM013` 行數 | `BBSM113` 行數 | 相同行 | 相似度 |
|---|---|---|---|---|
| UI | 1,089 | 939 | 605 | 0.597 |
| FormProxy | 350 | 120 | 107 | 0.455 |
| Control | 1,004 | 180 | 116 | 0.196 |
| PO | 1,306 | 1,204 | 708 | 0.564 |

**這一對才是真正的平行複本。**UI 與 PO 各有六成的行在代號代換後完全相同;Control 的 0.196 是假象——`BBSM013_Ctl` 有 706 行(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM013_Ctl.cs:209-914`)是整段被註解掉的舊式手寫逐欄搬運,扣掉之後兩邊的實質內容其實幾乎一樣。

#### 4.7.3 只差代號的部分(改一支必須同步另一支)

下列邏輯在兩支之間只有代號不同,**任何一邊改了另一邊就會行為分歧**:

| 區塊 | `BBSM013` | `BBSM113` |
|---|---|---|
| 抓申購主檔與匯款支票資料 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:118-243` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:135-273` |
| 產生受讓人申購書號 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:252-315` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:274-335` |
| 更新出讓人結餘 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:323-383` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:343-402` |
| 更新基金單位數結餘 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:384-405` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:403-422` |
| 更新受讓人結餘(沒有就新增) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:406-478` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:423-491` |
| 更新出讓人申購明細 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:479-502` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:492-528` |
| 銷帳排序與扣數 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:279-325` | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:435-486` |
| 出讓人 / 受讓人 ID 與戶號連動 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:590-707` | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:501-619` |

#### 4.7.4 真的不同的部分

| 面向 | `BBSM013`(實體) | `BBSM113`(無實體) |
|---|---|---|
| 憑證明細來源 | 使用者勾選實體憑證,`DoValidate` 比對勾選加總(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:199`) | 自動塞一列期別 `'99'` 假憑證(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:179-185`) |
| 庫存檢核 | 比總結餘 + 實體結餘(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:214`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:222`) | 比無實體結餘(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:368`),另在銷帳時再比一次可轉讓無實體單位數(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:409`) |
| `OFD721` | `AfterAdd` 會把憑證的受益人改成受讓人(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:503-536`) | **完全沒有這一段**;連 `OFD721` 這張 DataTable 都沒宣告 |
| 抓快速註記 | 有(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:244`) | **沒有**——同一段在 `BBSM113_PO` 完全不存在 |
| 受讓人限制 | 沒有 | 受讓人不能為集保受益人(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:313`) |
| 刪除前檢核 | 三條(見卡控總表) | 四條,多一條「受讓申購資料已質設,是否刪除」的詢問(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:249`) |
| Control 的表搬運 | 用 `TransferTable` 搬七張,含 `OFD721` | 用 `TransferDetailTable` 搬五張,不含 `OFD721` |
| Control 是否宣告 VDB 型別 | **沒有 `InitializeVDBTypes()` 覆寫** | 有(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM113_Ctl.cs:29-34`) |
| 移除未沖明細的位置 | 在 View 側,用 typed 的 Find 方法(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM013_Ctl.cs:960-964`) | 在 Model 側,用字串串接的篩選式(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM113_Ctl.cs:120-130`) |

#### 4.7.5 兩個彈出視窗

| 代號 | 用途 | 錨點 |
|---|---|---|
| `BBSM013p0` / `BBSM113p0` | 「必備文件」:列出出讓 / 受讓各自的必備文件代碼清單,代碼分類寫死 `"37"` 與 `"38"`〔客戶特定〕 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013p0.cs:32-35` |
| `BBSM013p1` / `BBSM113p1` | 「銷帳資料」:顯示這次轉讓會沖到哪幾筆申購書,讓使用者確認 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013p1.cs` |

兩支彈出視窗**不在掃描母體的畫面清冊裡**(它們不是六層齊的正式畫面,只是 UI 層的表單),見附錄 D2。

#### 4.7.6 存檔前檢核

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:50-133` 的 `DoValidate()` 管銷帳與憑證:

1. 轉讓單位數必須等於申購書轉讓單位數加總(`:57`)。

2. 憑證 grid 上的兩條逐筆檢核(`:76` / `:94`)。

3. 轉讓日期必須大於最近結帳日(`:122`)。

4. 出讓人 / 受讓人不可為註銷戶(`:127` / `:130`)。

`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:134-237` 的 `DoMasterRequireCheck()` 管主檔:

1. 出讓人戶號不可與受讓人戶號相同(`:141`)。

2. 轉讓總單位數 / 稅額 / 淨值都必須大於 0(`:143` / `:146` / `:148`)。

3. 轉讓日期不得小於基金發行日(`:156`)與成立日(`:190`)、必須大於最近結帳日(`:163`)、必須是營業日(`:180`)、基金必須已成立(`:186`)。

4. 轉讓單位數必須等於勾選憑證加總(`:199`)。

5. 總結餘與實體結餘檢核(`:214` / `:222`)。

`BBSM113` 的對應在 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:284-302` 與 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:303-383`,內容對應但少了憑證勾選那兩條、多了集保受益人那條。

**`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:150-162` 有一整段被註解掉的檢核**:「出讓人轉讓基金尚有有效的定期買回同意書,是否繼續執行?」外殼(含 `ByPassAddMessage` 的例外放行紀錄)都還在,只是整段註解。同一段在 `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:451` 與 `:471` 也被註解。兩邊都關,但**關的位置與註解時間不一定一樣**,見附錄 E8。

#### 4.7.7 跨表更新

| 表 | 動作 | `BBSM013` 錨點 | `BBSM113` 錨點 |
|---|---|---|---|
| `OFD220A` | INSERT 受讓人新申購書主檔 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:126` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:148` |
| `OFD221A` | INSERT 受讓人新申購明細;UPDATE 出讓人原申購明細 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:481` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:493` |
| `OFD234A` | 複製支票資料到新申購書 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:179` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:204` |
| `OFD235A` | 複製匯款資料到新申購書 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:207` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:234` |
| `OFD304A` | 出讓人扣、受讓人加(沒有就新增) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:350`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:407` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:370`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:424` |
| `OFD310A` | 基金單位數結餘(境內) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:385` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:404` |
| `OFD721` | 憑證受益人改成受讓人 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:506` | **無** |
| `BBS015A` | 申購書轉讓明細 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:270` | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:291` |

#### 4.7.8 卡控總表

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 轉讓單位數 ≠ 申購書轉讓加總 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:57`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:291` |
| 新增前 | 出讓人 / 受讓人為註銷戶 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:127-130`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:296-299` |
| 新增前 | 出讓人戶號 = 受讓人戶號 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:141`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:310` |
| 新增前 | 受讓人為集保受益人 | **只有 `BBSM113`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:313` |
| 新增前 | 轉讓總單位數 ≤ 0 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:143`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:315` |
| 新增前 | 轉讓稅額 / 淨值 ≤ 0 | **只有 `BBSM013`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:146-148` |
| 新增前 | 轉讓日期 ≤ 最近結帳日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:163`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:321` |
| 新增前 | 轉讓日期非營業日 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:180`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:338` |
| 新增前 | 基金尚未成立 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:186`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:345` |
| 新增前 | 轉讓單位數 ≠ 註記憑證加總 | **只有 `BBSM013`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:199` |
| 新增前 | 總結餘 / 實體結餘不足 | **只有 `BBSM013`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:214-226` |
| 新增前 | 無實體結餘不足 | **只有 `BBSM113`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:368` |
| 新增前 | 定期買回同意書尚有效 | 兩支都**已註解** | 失效 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:451`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:152` |
| 刪除前 | 出讓人 / 受讓人為註銷戶 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:507-510`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:199-202` |
| 刪除前 | 轉讓日期已過帳 | **只有 `BBSM113`** | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:221` |
| 刪除前 | 受讓申購資料已贖回或再轉讓 | 兩支 | 阻擋 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:526`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:232` |
| 刪除前 | 受讓申購資料已質設 | 兩支 | 詢問 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:546`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:249` |
| 刪除前 | 後端呼叫失敗 | 兩支 | 警示(顯示通用伺服器錯誤) | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:521`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:227` |
| 查詢 | 轉讓型態硬條件 | 兩支各自 | **過濾(無提示)** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1115`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1014` |
| 存檔 | 未沖到的申購明細列 | 靜默刪除 | **過濾(無提示)** | `Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM013_Ctl.cs:960`、`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM113_Ctl.cs:120` |

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因有兩條,都能從程式反推:

1. **十支維護畫面本身就是查詢入口。** 每支都是 `xMaintainForm`,第一個分頁就是查詢條件頁,查完直接進維護頁。查詢條件由 `Before*SearchButtonClicked` 塞進參數表(例:`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:64-82`),再由 PO 的主檔 SQL 組出來。

2. **需要跨單據看的資料由 R 報表提供。** `BBSR007`(掛失中清冊)與 `BBSR012`(質設中清冊)就是典型的「查詢用途」報表——它們不是查核表,是現況清單。

### 5.1 查詢條件一覽(從 `Before*SearchButtonClicked` 反推)

| 畫面 | 條件 | 錨點 |
|---|---|---|
| `BBSM001` | 換發書號、受益人ID、戶號、基金代碼、換發日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:72-89` |
| `BBSM003` | 掛失書號、受益人ID、戶號、基金代碼、掛失日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:63-91` |
| `BBSM004` | 掛撤書號、受益人ID、戶號、基金代碼、掛撤日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:237-259` |
| `BBSM005` | 補發書號、受益人ID、戶號、基金代碼、補發日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:83-106` |
| `BBSM009` / `BBSM109` | 質設書號、受益人ID、戶號、基金代碼、質設日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:64-82`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:60-73` |
| `BBSM010` / `BBSM110` | 質解書號、受益人ID、戶號、基金代碼、質解日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM010.cs:57-76`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM110.cs:54-70` |
| `BBSM013` / `BBSM113` | 轉讓書號、出讓人ID / 戶號、基金代碼、轉讓日期 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:365-382`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:74-91` |

### 5.2 會把資料濾掉而不提示的條件

這是本節真正要記的東西。**下列條件寫死在 SQL 裡,畫面上看不到、使用者也不會收到任何提示**:

| # | 條件 | 影響 | 錨點 |
|---|---|---|---|
| 1 | 質設型態 = 實體 / 無實體 | `BBSM009` 與 `BBSM109` 互相看不到對方的單 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:350`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:284` |
| 2 | 質解型態 = 實體 / 無實體 | 同上 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:384`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:210` |
| 3 | 轉讓型態 = 實體 / 無實體 | 同上 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1115`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1014` |
| 4 | `BBSM010` 的明細只撈質設型態為實體的質設單 | 一張無實體質設單永遠不會出現在實體質解畫面上——這是對的,但沒有任何提示 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:522`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:821` |
| 5 | `BBSM003` 的明細硬加「掛失狀態碼不等於已補發」 | **Oracle 三值邏輯**:掛失狀態碼為 NULL 的明細也會被濾掉 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:1285` |
| 6 | `BBSM004` 的可掛撤明細只撈憑證狀態為掛失中的 | 憑證被別的流程改過狀態就不出現 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:534`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:926` |
| 7 | `BBSM004` 的待辦排除條件 | 修改者欄位為 NULL 的單不會出現在任何人的待辦 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:390` |
| 8 | `BBSM110` 的可質解計算只認憑證狀態為正常的 | 無實體流程卻依賴憑證狀態 | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:395` |

## 6. 批次(B)與 WindowsService

**本模組無 B 畫面,也沒有任何 WindowsService。**

原因三條:

1. **BBS 的每一筆異動都要人工判斷。** 換發、掛失、補發、質設、轉讓都需要收件、核對印鑑、確認單位數,不是可以批次跑的東西。程式上的對應證據是:十支畫面全部有印鑑鈕,而且新增前的卡控有一半需要使用者在 grid 上逐筆勾選。

2. **狀態機的推進者是四眼,不是排程。** `OFD721` 的狀態變化全部掛在 `AfterAdd` / `AfterApproveDelete` 上(§2.5),沒有任何一處由時間觸發。

3. **需要跑量的部分在別的模組。** 結帳日的推進、憑證的大量印製、集保資料交換,BBS 只讀結果(最大資料控制日期、大憑證日期),不負責產生。

掃描母體對 BBS 的統計是 `B 0`、`Service 0`,與上述一致。

**要注意的是:這不代表 BBS 的資料不會被批次動到。** `OFD304A`、`OFD310A`、`OFD721` 三張表都是 OFD 的日結批次會碰的,BBS 開的單在盤後被改掉是完全可能的。程式裡唯一的防線是「最大資料控制日期」檢核與 `AfterAdd` 那層「更新列數必須是 1」的樂觀檢查。

## 7. 報表(R)

```text
[圖] BBS 七支報表的四段鏈、對應的版控外 SP 與十三份 rpt，以及列印路徑的參數名缺陷
圖中文字:① 七支 R 畫面，固定四段鏈，全部不碰維護層的 PO / R 畫面 收查詢條件 / 兩條路：預覽與列印 / Report FormProxy / 過一次 Remoting / Report PO / 呼叫版控外的 SP / Crystal Report / RPS 或 RPS1 擇一 / ② 七支 SP 全部不在版控裡，報表口徑在 repo 內查不到 / BBSR002 換發查核表 / SP 帶換發種類 / BBSR006 掛失撤銷查核 / SP 帶資料種類 / BBSR007 掛失中清冊 / 日期＋基金＋戶號 / BBSR010 質設質解查核 / 唯一只有一份 rpt / BBSR011 憑證質設質解 / 新寫法 GetData / BBSR012 質設中清冊 / 新寫法 GetData / BBSR015 轉讓過戶查核 / 唯一帶轉讓型態參數 / 13 份 rpt / 六支各兩份 一支一份 / ③ 兩條路各自組一次參數 —— 其中兩支的列印路壞了 / 預覽路 參數名正確 / 六支都對 / 列印路 參數名多了 '@' / BBSR006 與 BBSR007 / PO 比對不含 @ 的名字 / 條件一個都傳不到 SP
```

*圖:圖 4 報表群。黑框=無原始碼的 SP 或已確認的缺陷；橘框=值得特別記住的一支。BBSR015 是唯一能同時看實體與無實體轉讓單的地方；BBSR006 與 BBSR007 的列印路徑參數名帶了 SQL Server 風格的 @，條件全部失效。*

### 7.1 一覽

七支 R 畫面、13 份 `.rpt`。**全部走同一條鏈**:畫面收條件 → `SetQueryParameters(rpt 名, DB Report_Id, 中文名)` → Report PO 呼叫一支版控外的 SP → 用回傳的 RefCursor 灌 typed DataSet → Crystal Report 出圖。

| rpt | 對應畫面 | 中文名(程式內寫死) | 取數來源 | 何時用這一份 |
|---|---|---|---|---|
| `BBSR002RPS` | `BBSR002` | 受益憑證換發查核表 | `s_TA_BBSR002_Get` | 列印方式 = `'0'` |
| `BBSR002RPS1` | `BBSR002` | 同上 | 同上 | 列印方式 = `'1'`(以換發 / 掛失補發書號排序) |
| `BBSR006RPS` | `BBSR006` | 受益憑證掛失(撤銷)查核表 | `s_TA_BBSR006_Get` | 列印方式 = `'0'` |
| `BBSR006RPS1` | `BBSR006` | 同上 | 同上 | 列印方式 = `'1'`(以基金代碼跳頁) |
| `BBSR007RPS` | `BBSR007` | 受益憑證掛失中清冊 | `s_TA_BBSR007_Get` | 列印方式 = `'0'` |
| `BBSR007RPS1` | `BBSR007` | 同上 | 同上 | 列印方式 = `'1'`(以基金代碼跳頁) |
| `BBSR010RPS` | `BBSR010` | 受益人質設(質解)查核表 | `S_TA_BBSR010_GET` | **唯一一支沒有第二份** |
| `BBSR011RPS` | `BBSR011` | 受益人憑證質設(質解)查核表 | `S_TA_BBSR011_GET` | 列印方式 = `'0'` |
| `BBSR011RPS1` | `BBSR011` | 同上 | 同上 | 列印方式 = `'1'` |
| `BBSR012RPS` | `BBSR012` | 受益憑證質設中清冊 | `S_TA_BBSR012_GET` | 列印方式 = `'0'` |
| `BBSR012RPS1` | `BBSR012` | 同上 | 同上 | 列印方式 = `'1'` |
| `BBSR015RPS` | `BBSR015` | 轉讓過戶查核表 | `s_TA_BBSR015_Get` | 列印方式 = `'0'` |
| `BBSR015RPS1` | `BBSR015` | 同上 | 同上 | 列印方式 = `'1'` |

錨點:`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:82`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:112`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR007.cs:64`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR010.cs:101`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR011.cs:129`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR012.cs:102`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR015.cs:71`。

### 7.2 七支 SP 的參數

**七支 SP 全部不在 repo 內**(`DB/` 底下 BBS 相關的 SP / Function / Trigger / View 是 0 支)。以下參數清單由呼叫端的 `AddInParameter` 反推:

| SP | 參數 | 錨點 |
|---|---|---|
| `s_TA_BBSR002_Get` | 換發日期起迄、基金、受益人ID、戶號、換發書號起迄、掛失補發書號起迄、換發種類 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR002_PO.cs:64-113` |
| `s_TA_BBSR006_Get` | 掛失日期起迄、基金、資料種類、受益人ID、戶號、掛失書號起迄、掛撤書號起迄 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR006_PO.cs:63-115` |
| `s_TA_BBSR007_Get` | 掛失日期起迄、基金、受益人ID、戶號 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR007_PO.cs:65-91` |
| `S_TA_BBSR010_GET` | 質設日期起迄、基金、受益人ID、戶號 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR010_PO.cs:61-65` |
| `S_TA_BBSR011_GET` | 同上(取值方式與 `BBSR010` 相同) | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR011_PO.cs:59` |
| `S_TA_BBSR012_GET` | 同上 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR012_PO.cs:59` |
| `s_TA_BBSR015_Get` | 轉讓日期起迄、基金、出讓人ID / 戶號、受讓人ID / 戶號、轉讓區分碼、轉讓書號起迄、轉讓型態 | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR015_PO.cs:66-123` |

**`s_TA_BBSR015_Get` 有轉讓型態參數**(`Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR015_PO.cs:122`),也就是**這支報表可以同時看實體與無實體的轉讓單**——是全模組唯一能跨 `1xx` 邊界看資料的地方。其餘六支報表沒有型態參數,查出來是哪一邊由 SP 內部決定,repo 內看不到。

### 7.3 兩代寫法並存

| 面向 | 舊寫法(`BBSR002` / `BBSR006` / `BBSR007` / `BBSR015`) | 新寫法(`BBSR010` / `BBSR011` / `BBSR012`) |
|---|---|---|
| 取參數 | `foreach` 掃參數表,逐個 `if (rrRow.Name == "X")` | `SQLEVAHelper.GetParamValue<T>(model, "X")` 一行一個 |
| 方法名 | `GetBBSR002<T>` 之類 | 統一叫 `GetData<T>` |
| SP 名大小寫 | `s_TA_BBSRnnn_Get` | `S_TA_BBSRnnn_GET` |
| 戶號沒填時 | 傳 `-1` | 傳 `-1`(`GetParamValue` 的預設值參數) |
| `using` 包 `DbCommand` | 沒有(`BBSR002`) | 有 |

錨點對照:`Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR002_PO.cs:52-116` 對 `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR010_PO.cs:50-70`。

兩代共通的一點:**`Cmd.CommandTimeout = 0`,也就是永不逾時**(`Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR002_PO.cs:62` 的註解直接寫「此程式讓它永久跑」)。七支報表全部如此。

### 7.4 畫面端的檢核

四支有書號區間的報表(`BBSR002` / `BBSR006` / `BBSR007` / `BBSR015`)都有同一組三段式檢核:

| 檢核 | 結果 | 錨點(以 `BBSR002` 為例) |
|---|---|---|
| 日期期間(起)不可大於(迄) | 阻擋 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:164` |
| 書號起迄必須「都填」或「都不填」 | 阻擋 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:176` |
| 書號必須是 13 碼 | 阻擋 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:185` |
| 書號(起)不可大於(迄) | 阻擋 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:193` |

**書號 13 碼這個長度是寫死的**〔客戶特定〕。`BBSR006` 對掛失與掛撤兩組書號各做一次(`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:216`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:246`)。

另外每支都有一段被註解掉的「未輸入起始日期,請檢查」(`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:156`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:189`),也就是**日期可以完全不填,那時 SP 會收到 1900/01/01 之類的預設值**,查出來是全部資料。

### 7.5 「列印」與「預覽」是兩條不同的路,而且其中兩支的列印路壞了

每支報表都實作兩個事件:`BeforePreviewButtonClicked` 與 `BeforePrintButtonClicked`,而且**兩邊各自重寫一次參數組裝**。四支是複製貼上一致的,兩支不是:

| 報表 | 預覽路的參數名 | 列印路的參數名 | 後果 |
|---|---|---|---|
| `BBSR006` | `LOS_DT_ST` … | **`@LOS_DT_ST` …**(全部加了 `@`) | PO 比對的是不含 `@` 的名字(`Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR006_PO.cs:64-111`),**列印路的條件一個都對不上** |
| `BBSR007` | `LOS_DT_ST` … | **`@LOS_DT_ST` …** | 同上 |

錨點:`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:120-131`(預覽,正確)對 `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:154-165`(列印,全部帶 `@`);`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR007.cs:103-107`。

`@` 前綴是 SQL Server 的參數寫法,這套系統跑的是 Oracle(`architecture.md §4`),所以這是從別的專案抄過來沒改乾淨。**實務影響:直接按「列印」的人拿到的結果與按「預覽」的人不同。**嚴重度高,列進附錄 E。

`BBSR002` 的兩條路則是另一種問題:兩邊完全重複 25 行參數組裝(`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:90-99` 與 `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:126-135`),差別只在預覽路多做了 `.Trim()`。改條件時只改一邊就會分歧。

### 7.6 報表頁首參數是另一組東西

`ReportLoad` 事件裡用 `SetParameterValue` 把查詢條件的「顯示字串」塞進 `.rpt` 的參數(`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:30-70`)。這組參數**跟 SP 的參數是兩套**:SP 拿的是值,`.rpt` 拿的是「全部」或「(代碼)名稱」這種給人看的字串。改查詢條件時兩邊都要動,漏一邊的症狀是「報表頁首寫全部,內容卻只有一檔基金」。

### 7.7 報表與維護資料的關係

**在 repo 內是斷的。**七支 SP 都不在版控裡,所以「報表上的數字怎麼從 `BBS001A`–`BBS015A` 算出來」這件事,程式碼裡沒有答案。能確定的只有參數對應的欄位(§7.2),以及 typed DataSet 宣告的結果集形狀(`Dev/ATLAS.BBS.Report/Source/Entity/ReportDataEntity.BBS/BBSR002Model.xsd` 等七支)。

要追報表口徑,只能去資料庫看 SP。**本文不猜。**

## 8. 跨模組共用

```text
[圖] BBS 跨模組影響面：自有表無外部使用者、轉讓兩支會在 OFD 建資料、三張未宣告的外部表，以及共用的憑證狀態機
圖中文字:① BBS 自己的 16 張表：沒有任何別的模組用，改動只回歸 BBS / BBS001A ~ BBS015A ＋ BBS020A / 只出現在 BBS 的十支畫面上 / 回歸範圍 = BBS 自己 / 反查結果無跨模組 / ② 反過來：轉讓兩支會在 OFD 的地盤上建資料 / BBSM013 BBSM113 / 四眼一次覆核 / OFD220A〔共用〕 / 也服務 OFDB310 OFDM221A / OFD221A〔共用〕 / 掃描器標跨模組 也服務 OFD / OFD234A OFD235A / 也服務 OFDM221A / ③ OFD221A 改欄位要一起看的八支畫面 / BBSM013 BBSM113 / BBS 側 掛四眼欄 / OFDB302 OFDB304 OFDB306 / OFD 側 當主檔 / OFDB310 OFDB331 OFDI059 / OFD 側 主檔或明細 / EC 的 xsd / 欄位定義的來源 / ④ 最危險的三張：沒宣告、四眼不管、只靠手寫反向 UPDATE 回滾 / OFD304A 十支畫面都寫 / 掛失／實體質押／無實體質押／實體結餘 / OFD310A 與 OFD0814A / 轉讓與換發補發會寫 / ⑤ OFD721 是共用的中央狀態機，OFD 那側怎麼改是跨模組回歸第一問 / BBS 只 UPDATE 狀態 / 每次都帶來源狀態條件 / OFD721〔共用〕 / 主檔畫面 OFDM721 OFDM725 / 風險：OFD 側若不帶條件 / BBS 的狀態前提全部失效
```

*圖:圖 5 跨模組。灰虛框=宣告在主明細清單裡的 OFD 表；黑框=沒宣告、四眼引擎不管的外部表。OFD304A／OFD310A／OFD0814A 的異動不會被四眼自動回滾，只靠 AfterApproveDelete 裡手寫的反向 UPDATE，漏寫就永遠對不回來。*

### 8.1 BBS 的表沒有被別的模組用

掃描器對 16 張 BBS 自有表的反查結果:`BBS001A`–`BBS015A` 與 `BBS020A` 全部只出現在 BBS 自己的畫面上,沒有一張被別的模組宣告成主檔或明細。

也就是說:**改 BBS 的表結構,回歸範圍就是 BBS 自己。**但反過來不成立——BBS 大量寫別人的表,見下一節。

### 8.2 BBS 寫別人的表:四張宣告的 + 三張沒宣告的

#### 宣告在 `xTableMapping` 裡的四張(母體看得到)

| 表 | 誰的主檔畫面 | BBS 的角色 | 反查結果 |
|---|---|---|---|
| `OFD220A` | `OFDB310` / `OFDM221A` | `BBSM013` / `BBSM113` 當明細,會 INSERT | 明細於 `BBSM013` `BBSM113` `OFDB331` `OFDM231A` |
| `OFD221A` | `OFDB302` / `OFDB304` / `OFDB306` / `OFDI059` | 同上 | **掃描器標為跨模組(也服務 OFD)**;明細於 `BBSM013` `BBSM113` `OFDB310` `OFDB331` |
| `OFD234A` | 無主檔畫面 | 同上 | 明細於 `BBSM013` `BBSM113` `OFDM221A` |
| `OFD235A` | 無主檔畫面 | 同上 | 明細於 `BBSM013` `BBSM113` `OFDM221A` |

`OFD221A` 的欄位定義來自 EC 專案的 xsd(`Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB672Model.xsd`),12 欄,沒有四眼欄位。**這意味著 `OFD221A` 在不同模組裡被當成不同形狀的東西**:BBS 這邊掛在四眼流程上(所以 `BBSM013Model.xsd` 給它補了四眼欄),EC 那邊是純資料表。改欄位要同時看 BBS、OFD、EC 三邊的 xsd。

**改動影響面(以 `OFD221A` 為例)**:

| 要改什麼 | 要一起看的畫面 | 為什麼 |
|---|---|---|
| 加欄位 | `BBSM013` `BBSM113` `OFDB302` `OFDB304` `OFDB306` `OFDB310` `OFDB331` `OFDI059` | 八支的 xsd 與 Designer 都要重生;BBS 這兩支還要同步 Control 的搬運清單 |
| 改 PK | 同上 | BBS 側的明細鍵是申購書號 + 序號,轉讓會配新書號,改 PK 等於改配號邏輯 |
| 改型別 | 同上 | `BBSM013` 的 `AllotData_D` 有 30 個以上金額 / 單位數欄,全部 decimal |

#### 沒宣告、只出現在 SQL 字串裡的三張(母體看不到)

| 表 | BBS 怎麼動它 | 錨點 |
|---|---|---|
| `OFD304A` | **十支畫面全部會 UPDATE**,動四個水位欄:掛失、實體質押、無實體質押、實體結餘;`BBSM013` / `BBSM113` 還會在受讓人沒有該基金結餘時 INSERT | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:129`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:231`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:140`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:406-478` |
| `OFD310A` | `BBSM013` / `BBSM113` UPDATE 基金單位數結餘(境內) | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:385`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:404` |
| `OFD0814A` | `BBSM001` / `BBSM005` UPDATE 憑證流水號,**WHERE 只有基金代碼** | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:774-780`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:432` |

**這三張是本模組最大的隱形相依。**它們不在任何 `xTableMapping` 裡,所以:

- 掃描母體不會列出來(附錄 D3);

- 用「這張表被哪些畫面用到」的反查工具查不到 BBS;

- 四眼引擎不管它們——**它們的異動不會被四眼回滾,只靠 PO 事件裡手寫的反向 UPDATE**。

換句話說,**如果有人在 `AfterApproveDelete` 裡漏寫一段反向更新,結餘就永遠對不回來,而且沒有任何機制會發現**。§4 各節的「跨表更新」表就是為了這件事而列的。

### 8.3 `OFD721` 是共用的中央狀態機

`OFD721` 被掃描器標為「模組 BBS, OFD」——它的欄位定義同時出現在 `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd` 與 OFD 的 xsd 裡,主檔畫面是 `OFDM721` / `OFDM725`。

BBS 對它的操作全部是 UPDATE,而且**每一次 UPDATE 都帶來源狀態條件**(§2.5)。這是設計上的樂觀鎖:兩個人同時對同一張憑證做掛失與質設,第二個人的 UPDATE 會影響 0 列,然後被「更新列數不等於 1」擋下來。

**風險在 `OFDM721` / `OFDM725` 那一側**:如果 OFD 的維護畫面可以直接改狀態而不走同一套條件,BBS 這邊的所有狀態轉換前提就失效了。repo 內沒有辦法確認 OFD 那兩支怎麼寫——**這是跨模組回歸時第一個要問的問題**。

### 8.4 共用工具:`CalcBBSUnits`

十支維護畫面都呼叫同一支客戶端共用工具算「這個受益人在這檔基金上的可用單位數」,回三個數(全部 / 實體 / 無實體)。

| 畫面 | 用哪幾個數 | 錨點 |
|---|---|---|
| `BBSM001` | 三個都用,依換發種類切 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:528-555` |
| `BBSM003` | 全部 + 實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:646-660` |
| `BBSM005` | 無實體(只在刪除時用) | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:410-415` |
| `BBSM009` | 全部 + 實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:391-407` |
| `BBSM109` | 無實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:698-717` |
| `BBSM013` | 全部 + 實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:212-226` |
| `BBSM113` | 無實體 | `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:365-372` |

**改這支共用工具的算式,十支畫面的卡控會同時變。**它是本模組最集中的單點,而它本身不在 BBS 專案裡(在 `Dev/Common/` 的客戶端共用層,見 `architecture.md §7`)。

### 8.5 共用 UI 控件與下拉來源

| 控件 / 來源 | 用途 | 誰用 |
|---|---|---|
| 受益人 ID / 戶號連動控件 | 輸入其一自動帶出另一,不符時跳詢問 | 十支全部 |
| 基金代碼控件 | 帶出基金簡稱、成立日、發行日、單位數小數位、單位數狀態訊息 | 十支全部 |
| 依分類碼取下拉 | `'244'` 質解型態、`'245'` 轉讓型態、`'37'` / `'38'` 轉讓必備文件 | `BBSM009` `BBSM010` `BBSM109` `BBSM013` `BBSM113` |
| 跳號一覽表工具 | 每支畫面在 `FormInitial` 註冊,在七個四眼事件記錄書號跳號 | 十支全部 |

跳號一覽表是本模組與框架耦合最深的地方:**每支畫面的每一個四眼事件都只做這一件事**,而且用的是各自的書號種類列舉值。用錯種類的後果是跳號紀錄記到別的號別去,`BBSM013` 就踩到了(附錄 E1)。

## 附錄 A. 資料表總表

### A.1 母體的 20 張表

| 表 | 歸屬 | 主檔於 | 明細於 | 說明(推測) |
|---|---|---|---|---|
| `BBS001A` | BBS | `BBSM001` | — | 憑證換發主檔 |
| `BBS002A` | BBS | — | `BBSM001` | 憑證換發明細(新 / 舊證) |
| `BBS003A` | BBS | `BBSM003` | — | 憑證掛失主檔 |
| `BBS004A` | BBS | — | `BBSM003` | 掛失憑證明細 |
| `BBS005A` | BBS | `BBSM004` | — | 掛失撤銷主檔 |
| `BBS006A` | BBS | — | `BBSM004` | 掛失撤銷憑證明細 |
| `BBS007A` | BBS | `BBSM005` | — | 掛失補發主檔 |
| `BBS008A` | BBS | — | `BBSM005` | 掛失補發憑證明細(新 / 舊證) |
| `BBS009A` | BBS | `BBSM009` `BBSM109` | — | 質權設定主檔(實體與無實體共用) |
| `BBS010A` | BBS | — | `BBSM009` `BBSM109` | 質設憑證明細 |
| `BBS011A` | BBS | `BBSM010` `BBSM110` | — | 質權解除主檔(實體與無實體共用) |
| `BBS012A` | BBS | — | `BBSM010` `BBSM110` | 質解憑證明細 |
| `BBS013A` | BBS | `BBSM013` `BBSM113` | — | 轉讓過戶主檔(實體與無實體共用) |
| `BBS014A` | BBS | — | `BBSM013` `BBSM113` | 轉讓憑證明細 |
| `BBS015A` | BBS | — | `BBSM013` `BBSM113` | 轉讓申購書明細(銷帳結果) |
| `BBS020A` | BBS | — | `BBSM003` | 掛失必備文件與到件日 |
| `OFD220A` | OFD〔共用〕 | `OFDB310` `OFDM221A` | `BBSM013` `BBSM113` `OFDB331` `OFDM231A` | 申購書主檔 |
| `OFD221A` | OFD〔共用,掃描器標跨模組〕 | `OFDB302` `OFDB304` `OFDB306` `OFDI059` | `BBSM013` `BBSM113` `OFDB310` `OFDB331` | 申購明細 |
| `OFD234A` | OFD〔共用〕 | — | `BBSM013` `BBSM113` `OFDM221A` | 申購支票明細 |
| `OFD235A` | OFD〔共用〕 | — | `BBSM013` `BBSM113` `OFDM221A` | 申購匯款明細 |

### A.2 實體表名與 xsd DataTable 名對照

一張實體表在不同畫面裡有不同的 DataTable 名,查 xsd 前先用這張表換算:

| 實體表 | DataTable 名 |
|---|---|
| `BBS001A` | `BBSM001_BBS001` |
| `BBS002A` | `BBSM001_BBS002`(xsd 另有 `BBSM001_BBS002N` / `BBSM001_BBS002O` 兩個 View 側的分堆表) |
| `BBS003A` | `BBSM003` |
| `BBS004A` | `BBSM003_CerData`(查詢用)/ `BBSM003_CerData_CK`(存檔用) |
| `BBS005A` | `BBSM004` |
| `BBS006A` | `BBSM004_Cer_CK`(存檔用)/ `BBSM004_CerData`(查詢用) |
| `BBS007A` | `BBSM005_BBS007` |
| `BBS008A` | `BBSM005_BBS008` |
| `BBS009A` | `BBSM009_BBS009`(實體)/ `BBSM109`(無實體) |
| `BBS010A` | `BBSM009_BBS010`(實體)/ `BBSM109_Detail`(無實體) |
| `BBS011A` | `BBSM010_BBS011`(實體)/ `BBSM110`(無實體) |
| `BBS012A` | `BBSM010_BBS012`(實體)/ `BBSM110_BBS012`(無實體) |
| `BBS013A` | `BBSM013`(實體)/ `BBSM113`(無實體) |
| `BBS014A` | `BBSM013_CerData` / `BBSM113_CerData` |
| `BBS015A` | `BBSM013_BBS015` / `BBSM113_BBS015` |
| `BBS020A` | `BBSM003_DOC`(另有 `BBSM003_DOC_S` 是下拉來源) |
| `OFD220A` | `BBSM013_AllotData` / `BBSM113_AllotData` |
| `OFD221A` | `BBSM013_AllotData_D` / `BBSM113_AllotData_D` |
| `OFD234A` | `OFD234`(兩支同名) |
| `OFD235A` | `OFD235`(兩支同名) |

### A.3 母體之外、BBS 實際會動到的表

這四張只出現在 SQL 字串裡,**沒有宣告在任何 `xTableMapping`,所以母體與反查工具都看不到**:

| 表 | 動作 | 誰動 |
|---|---|---|
| `OFD304A` | UPDATE 四個水位欄;`BBSM013` / `BBSM113` 另有 INSERT | 十支維護畫面 |
| `OFD310A` | UPDATE 基金單位數結餘 | `BBSM013` `BBSM113` |
| `OFD0814A` | UPDATE 憑證流水號 | `BBSM001` `BBSM005` |
| `OFD724` | INSERT / UPDATE 憑證用印資料;也被 SELECT 當「已送簽 / 已註銷」判斷 | `BBSM001` `BBSM005` |

另外**只被讀、不被寫**的:`BMS001A`(受益人姓名)、`OFD721`(憑證檔,只 UPDATE 狀態)、`OFD081A`(基金相關,出現在被註解掉的條件裡)、`CTL014`(代碼說明)。

### A.4 只存在於結果集、沒有同名實體表的 DataTable

| DataTable | 用途 | 錨點 |
|---|---|---|
| `BBSM001_IsRUnit` / `BBSM003_IsRUnit` | 沖銷檢核的回傳形狀 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM001Model.xsd:234` |
| `BBSM005_IsEmit` | 已送簽憑證的回傳形狀 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM005Model.xsd:235` |
| `BBSM009_CerData` / `BBSM010_CerData` | 可質設 / 可質解憑證的挑選清單 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:244`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:285` |
| `BBSM010_BBS012_DT` | 質設日期比對用的暫存 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM010Model.xsd:223` |
| `BBSM004_Detail` / `BBSM004_CerData_DT` | 掛撤畫面的中介表 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM004Model.xsd:321`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM004Model.xsd:329` |
| `BBSM003_DOC_S` | 掛失文件代碼的下拉來源 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:408` |
| `OFD721`(在 `BBSM013Model.xsd` 內) | 憑證三段碼的暫存,只有三欄 | `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:553` |

**`BBSM009Model.xsd` 裡有一張叫 `BBSM010_CerData` 的表**(`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM009Model.xsd:285`),名字屬於別支畫面。它是 `BBSM009` 刪除前檢查「明細有沒有被質解」時,用來裝 `CheckMOR_CD` 回傳值的容器(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:259`)。**命名鐵律的例外,查 xsd 時會找錯地方。**

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:**一支都沒有**

掃描器對 `DB/` 的統計:BBS 相關的 SP 0、Function 0、Trigger 0、View 0。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 類 | 名稱 | 被誰呼叫 | 參數見 |
|---|---|---|---|
| SP | `s_TA_BBSR002_Get` | `BBSR002` | §7.2 |
| SP | `s_TA_BBSR006_Get` | `BBSR006` | §7.2 |
| SP | `s_TA_BBSR007_Get` | `BBSR007` | §7.2 |
| SP | `S_TA_BBSR010_GET` | `BBSR010` | §7.2 |
| SP | `S_TA_BBSR011_GET` | `BBSR011` | §7.2 |
| SP | `S_TA_BBSR012_GET` | `BBSR012` | §7.2 |
| SP | `s_TA_BBSR015_Get` | `BBSR015` | §7.2 |
| Function | `f_GetToDoData` | `BBSM004` 的待辦 SQL | `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:391` |

框架層還有一堆(配書號、跳號紀錄、四眼引擎)也是黑箱,見 `architecture.md §3`。

## 附錄 C. 代碼對照

### C.1 憑證狀態(`OFD721`)

見 §2.5。`'1'` 正常 / `'2'` 尚未簽証 / `'3'` 掛失中 / `'4'` 掛失撤銷 / `'5'` 掛失註銷 / `'6'` 質設中 / `'7'` 質設解除 / `'8'` 換發註銷 / `'9'` 已贖回。**值域來自 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:2334-2372`,不是反推的。**

### C.2 實體 / 無實體型態

| 欄位 | `'0'` | `'1'` |
|---|---|---|
| `MOR_TYPE` | 實體憑證質設 | 無實體質設 |
| `CMOR_TYPE` | 實體憑證質解 | 無實體質解 |
| `TX_TYPE` | 實體憑證轉讓 | 無實體轉讓 |

### C.3 換發種類(`CHG_TYPE`)

`'1'` 一般換發 / `'2'` 無實體換憑證 / `'3'` 憑證換無實體。**唯一有官方註解的代碼**(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM001.cs:475`)。

### C.4 新舊憑證碼

| 欄位 | `'O'` | `'N'` |
|---|---|---|
| `NO_ID`(`BBS002A`) | 繳回的舊證 | 發出的新證 |
| `CLOS_NO_ID`(`BBS008A`) | 註銷的舊證 | 補發的新證 |

### C.5 銷帳方式(`WRITEOFF_TYPE`)

`'0'` 照書號 / `'1'` 先單筆 / `'2'` 先小額。**注意名稱與實作不一致**,見 §4.7.1 與附錄 E10。

### C.6 其他在程式裡出現的字面量

| 值 | 出現在 | 意義 |
|---|---|---|
| `'99'` | 無實體明細的憑證期別 | 佔位期別〔客戶特定〕 |
| `'M'` | `MOR_CD` | 質設中 |
| `'L'` / `'I'` / `'D'` | `LOS_CD` | 掛失中 / 已撤銷 / 已補發(假設) |
| `'2'` | `MOR_INT` 的 UI 預設 | 質設孳息歸屬預設值 |
| `"37"` / `"38"` | 轉讓必備文件代碼分類 | 出讓 / 受讓〔客戶特定〕 |
| `'244'` / `'245'` | 下拉代碼分類 | 質解型態 / 轉讓型態〔客戶特定〕 |
| `13` | 報表書號長度檢核 | 書號固定 13 碼〔客戶特定〕 |
| `1900/01/01` | 到處 | 空日期的哨兵值 |

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

母體(`atlas_scan.py --module BBS`):畫面 17(B 0 / I 0 / M 10 / R 7)· 表 20 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 13 · Service 0。

本文覆蓋:10 支 M 畫面各一節(三對平行的合併成一節但逐項對照)、7 支 R 畫面在 §7、20 張表在 §2 與附錄 A、13 份 rpt 在 §7.1。

### D.2 母體沒列到、但本文寫了的東西

| 名字 | 為什麼寫 | 處置 |
|---|---|---|
| `OFD304A` `OFD310A` | 十支畫面都會 UPDATE,是本模組最大的隱形相依 | 放進 meta `refcheck-ignore`,在 §8.2 與附錄 A.3 說明 |
| `CTL014` | 掛失文件代碼的說明來源 | 同上 |
| `BBSM013p0` `BBSM013p1` `BBSM113p0` `BBSM113p1` | 四支彈出視窗,只有 UI 層,不是六層齊的正式畫面 | 同上,在 §4.7.5 說明 |
| 七支報表 SP 與 `f_GetToDoData` | 程式確實呼叫,但 repo 內沒有原始碼 | 同上,在附錄 B.2 列出 |
| `OFD0814A` `OFD724` `OFD081A` `BMS001A` `OFD721` | 有在索引裡,不需 ignore | 在附錄 A.3 說明 |

### D.3 母體列了、本文交代不足的

| 名字 | 交代程度 | 為什麼 |
|---|---|---|
| `BBS014A` | 只講了鍵與用途,沒有逐欄 | xsd 的 `BBSM013_CerData` 只有 7 個業務欄,§2.3 已列 |
| `OFD234A` `OFD235A` | 只講了「支票 / 匯款明細」與被複製的時機 | 兩張表的欄位定義在 BBS 的 xsd 裡沒有 Caption(`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:367-487` 全部空白),中文名要去 OFD 找 |
| 13 份 `.rpt` 的版面 | 沒有讀 | `.rpt` 是二進位,不在純讀碼範圍內;只從 `SetQueryParameters` 取名稱與選用條件 |

### D.4 標「假設」的地方總表

| # | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| 1 | BBS = 受益憑證作業 | 表名、欄位中文名、報表中文名、六種書號種類(§0.1) | 選單表 |
| 2 | `'2'` = 已印製未交付 | 沒有任何 BBS 畫面寫入,只被補發流程當來源狀態讀 | `OFDM721` / `OFDM725` 的程式或 DB 註解 |
| 3 | `LOS_CD` 的 `'L'` / `'I'` / `'D'` | 由寫入時機反推 | 代碼表 |
| 4 | 掛失三支沒有無實體版,是因為無實體不會遺失 | 程式內找不到反證 | 業務確認 |
| 5 | 結帳日由 OFD 的日結批次寫入 | BBS 只讀不寫 | OFD 模組文件 |
| 6 | `BBSM110` 讀憑證狀態是複製殘留 | 該支其餘邏輯完全不碰憑證檔 | 業務確認 |
| 7 | `BBSM013_Ctl` 是從 `BBSM113_Ctl` 複製過來的 | 兩邊 `Add` 方法的註解都寫「新增**無實體**轉讓檔資料」,而 `BBSM013` 是實體版 | 版控歷史 |
| 8 | `BBSM009` 缺「質權人不可是自己」是漏的 | 兩支寫同一張表,規則卻只在一邊 | 業務確認 |

## 附錄 E. 讀本文時要注意的地方

嚴重度定義:**高** = 會產生錯誤資料或讓卡控失效;**中** = 行為與預期不符但可觀察;**低** = 維護性問題。

### E1 平行複本改一支漏另一支:跳號紀錄記到別的號別

**這是本篇最該記住的一條。**`BBSM013` / `BBSM113` 的七個四眼事件都要呼叫跳號紀錄器,而且要傳「這是哪一種書號」。轉讓的書號種類應該是轉讓號,但:

| 事件 | `BBSM013_PO` | `BBSM113_PO` | 誰對 |
|---|---|---|---|
| `AfterDelete`(主檔) | **質解號**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1260`) | 轉讓號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1159`) | `BBSM113` |
| `AfterDelete`(申購書) | 申購號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1264`) | **轉讓號**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1163`) | `BBSM013` |
| `AfterApproveDelete`(主檔) | **質解號**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:582`) | **質解號**(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:546`) | 兩邊都錯 |
| `AfterApproveDelete`(申購書) | 申購號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:588`) | **完全沒有這一段** | `BBSM013` |
| `AfterVerify` / `AfterApprove` / `AfterReject` / `AfterResend` / `AfterUnDelete` | 轉讓號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs:1273-1301`) | 轉讓號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM113_PO.cs:1172-1200`) | 兩邊都對 |

**對照組**:`BBSM010_PO` / `BBSM110_PO`(質解)全部七處都用質解號,那才是質解號的正確用法(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:89`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:385`)。所以 `BBSM013` / `BBSM113` 的質解號是**從質解畫面複製過來忘了改**。

- **影響**:轉讓單刪除時的跳號紀錄被寫進質解書號的跳號清冊;`BBSM113` 的申購書跳號完全沒記錄。稽核上會看到「質解號跳了但找不到對應的質解單」。

- **怎麼修**:四處都要改,而且 `BBSM113` 要補一段。**只改一支等於留一半的錯。**

- **嚴重度**:高。

### E2 Oracle 三值邏輯:四條卡控永遠不成立

Oracle 裡空字串就是 NULL,`欄 <> ''` 永遠是 UNKNOWN,整個 WHERE 不成立。

| 位置 | 條件 | 這條卡控是什麼 | 後果 |
|---|---|---|---|
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1397` | `OFD724.VISA_NO<>''` | 「此換發資料已送簽,不可刪除」 | **永遠不擋**,已送簽的換發單照樣刪得掉 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:914` | `OFD724.VISA_NO <> ''` | 「憑證號碼 … 已送簽,不可刪除」 | **永遠不擋** |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs:964` | `VISA_UID_D <> ''` | 「此補發資料已註銷,不可刪除」 | **永遠不擋** |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:390` | `RejectID = ''` | 待辦清單的自審排除 | OR 的右半永遠不成立,等價於只剩左半;`UpdateID` 為 NULL 的單不會出現在任何人的待辦 |

**同一個檔案裡有正確寫法可以對照**:`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:1446` 寫的是 `NVL(OFD724.VISA_NO, ' ')<>' '`,跟 `:1397` 只差 49 行。所以這不是「當年不知道」,是改了一半。

- **嚴重度**:高。前三條是資料一致性風險(已送簽 / 已註銷的憑證被刪掉,`OFD724` 會留孤兒),第四條是流程風險。

### E3 字串串接進 SQL

| 位置 | 內容 |
|---|---|
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:895-1069` | 18 處把查詢條件值用單引號包起來直接串進 WHERE |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:572-726` | 14 處 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:373-1003` | 20 處,含登入者帳號(`:390`)與功能代碼(`:391`) |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:377` 起 | 12 處 |

值來自畫面欄位(受益人 ID、書號、基金代碼),沒有任何跳脫處理。同一批 PO 的其他條件走 `AddInParameter`,所以是混用而不是全面如此。

- **嚴重度**:高(SQL 注入 + 值含單引號時直接語法錯)。

### E4 沒有鍵的 UPDATE

`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:774-780`:

```
UPDATE OFD0814A
   SET CER_SRNO=:BF_CER_NO, UPDATEID=..., UPDATEDATE=...
 WHERE FUND_ID=:FUND_ID
```

WHERE 只有基金代碼。緊接著用「影響列數不等於 1 就 throw」當保護(`:786`),等於把「這張表每檔基金只有一列」寫成執行期斷言。

- **影響**:假設不成立時,要嘛整批被改、要嘛整筆交易被例外回滾;兩種都不是使用者預期的行為,而且錯誤訊息「更新受益人憑証檔失敗」看不出真正原因。

- **嚴重度**:高。

### E5 過寬的來源狀態清單

`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:109`:撤銷掛失撤銷時,把憑證打回「掛失中」的條件是 `CER_STATUS IN ('1','4','7')`。

正常路徑下來源應該只有 `'4'`(掛失已撤銷)。把 `'1'`(正常)與 `'7'`(已質解)也納入,代表**一張從沒掛失過的憑證,可能因為刪一張掛撤單而被打成掛失中**。

- **嚴重度**:中(要在特定順序下才會發生,而且有 `CER_RUNIT = 0` 這條副條件擋一部分)。

### E6 在四眼事件裡改主明細宣告

`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:122-124`:`AfterAdd` 事件裡 `DetailTable.Clear()` 再重新 Add,把掛失明細對應的 DataTable 從查詢用的換成存檔用的。

PO 實例由 Control 的資料存取池提供(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM003_Ctl.cs`),**同一個實例在同一次請求裡如果再被用來做別的動作,拿到的會是被換過的宣告**。這是全模組唯一一處「執行期改宣告」的寫法。

- **嚴重度**:中(目前流程下每次請求只做一個動作,所以不會發作;但只要有人加一個「新增後順便重查」的路徑就會出事)。

### E7 手寫逐欄對應漏一欄:撤銷原因存不進去

`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM004_Ctl.cs` 有 463 個逐欄指派,全檔只用了 14 次共用搬運工具。掛撤明細那一段(`:691-1028`)搬了憑證三段碼、單位數、掛失書號、四眼 13 欄,**但沒有搬撤銷原因**。

UI 有寫進 View(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:413`)、PO 有 SELECT 出來(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:422`),中間那一層漏了,所以使用者打的撤銷原因會被靜默丟掉。

同一段還有第二個問題:`if (X_Added != null)` 判斷用的是「有沒有新增列」,但迴圈跑的是**全部列**(`Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM004_Ctl.cs:355`、`:469`、`:578`)。只要有一列被新增,所有列都會被當成新增送到 Model 側。

- **嚴重度**:高。

### E8 被註解掉但外殼還在的檢核

| 位置 | 被關掉的檢核 | 外殼還在什麼 |
|---|---|---|
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:150-162` | 「出讓人轉讓基金尚有有效的定期買回同意書,是否繼續執行?」 | 連例外放行的紀錄呼叫都還在 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:451`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:471` | 同上,兩處 | 同上 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:286-287` | 「質設日期必須小於等於系統日期」 | 註明 2009/04/28 取消 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM009.cs:303-312` | 「質設日期必須大於集保大憑證日期」 | 註明 20090216 刪除 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM003.cs:481-490` | 同上 | 三行註解 + 一行 Dialog |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM005.cs:464-478` | 「掛失補發日期必須大於大憑證最大日期」「補發總單位數必須小於等於持有單位數」 | 整段 |
| `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR002.cs:156`、`Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:189` | 「未輸入開始日期,請檢查」 | 每支報表都有 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:241` | 撤銷質設時「更新結餘檔失敗」的 `throw` | 只註解 `throw`,`ExecuteNonQuery` 還在跑 |

最後一條最值得注意:**`BBSM109` 撤銷時更新結餘檔影響 0 列也算成功**,而它的實體版對照(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:148-151`)會 throw。同一個動作、兩支畫面、兩種結果。

- **嚴重度**:高(最後一條)/ 中(其餘)。

### E9 xsd 的欄位中文名有複製貼上錯誤

| 表 | 欄位 | Caption 寫的 | 應該是 |
|---|---|---|---|
| `BBS003A` | 掛失書號 | 「換發書號」 | 掛失書號 |
| `BBS003A` | 登報起 / 迄日 | 「CreateDate」 | 登報起 / 迄日 |
| `BBS004A` | 檢查碼 | 「BF_CER_NO」 | 受益憑證檢查碼 |
| `BBS004A` | 掛失狀態碼(`_CK` 版) | 「掛失書號-舊」 | 掛失狀態碼 |
| `BBS013A` | 受讓人 ID | 「出讓人ID」 | 受讓人 ID |
| `OFD221A`(在 BBS 的 xsd 內) | 申購金額 | 「ETD_ALLOT_AMT」 | 申購金額 |

錨點:`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:27`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:51-52`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:141`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM003Model.xsd:248`、`Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM013Model.xsd:157`。

**影響:框架會用 Caption 當畫面上的欄位標題與錯誤訊息的欄位名。**使用者在掛失畫面上看到「換發書號」是這麼來的。

- **嚴重度**:中。

### E10 選項名稱與行為不一致

`WRITEOFF_TYPE` 的 `'1'` 叫「先單筆」、`'2'` 叫「先小額」,但實作只差 `DATA_TYPE` 的排序方向,而 `DATA_TYPE` 只有「一般」與「定期定額」兩個值(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:266`、`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:292-303`)。**沒有任何一行程式比較金額大小。**

- **嚴重度**:中(使用者會以為選了「先小額」就會先沖小額)。

### E11 報表「列印」路徑的參數名全錯

`BBSR006` 與 `BBSR007` 的 `BeforePrintButtonClicked` 把參數名全部加了 SQL Server 風格的 `@` 前綴,而 Report PO 比對的是不含 `@` 的名字:

| 報表 | 預覽路 | 列印路 | PO 比對的名字 |
|---|---|---|---|
| `BBSR006` | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:120-131` | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR006.cs:154-165` | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR006_PO.cs:64-111` |
| `BBSR007` | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR007.cs:52` 起 | `Dev/ATLAS.BBS.Report/Source/UI/ReportUI.BBS/BBSR007.cs:103-107` | `Dev/ATLAS.BBS.Report/Source/PO/ReportPO.BBS/BBSR007_PO.cs:65-91` |

結果是**列印路的查詢條件一個都傳不到 SP**。Oracle 端會因為缺 IN 參數而報錯,被 catch 吃掉之後只顯示「取得資料失敗」。

- **嚴重度**:高。

### E12 SQL 組字串漏了欄位名

`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM003_PO.cs:726`:

```
SQLSelect += " And BBS020A." + " Like" + "'" + Row.Value + "%'";
```

少了 `Row.Name`,組出來是 `And BBS020A. Like'x%'`,直接語法錯。同一個 if 的等號分支(`:722`)是對的。只有在查詢條件用 Like 運算子時才會走到。

同一族還有八處 `" Like"` 前面少一個空白(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs:546`、`:559`、`:938`、`:951`、`:964`、`:977`、`:990`、`:1003`),組出來是 `欄位 Like'x%'`,Oracle 可以吃,不會錯。

- **嚴重度**:中(觸發條件窄,但一觸發就是例外)。

### E13 空訊息的例外

`throw new ApplicationException("")` 在本模組的 PO 裡出現 **73 次**,全部是跳號紀錄器回傳 false 時丟的。使用者看到的是空白錯誤對話框。

例:`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:89`、`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs:91`。

- **嚴重度**:低(不影響資料,但故障排除會非常痛苦)。

### E14 非 UTF-8 來源檔

16 個檔是 cp950,其餘全是 UTF-8 with BOM:

| 檔 | 行數 |
|---|---|
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM001_PO.cs` | 1,673 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM004_PO.cs` | 1,143 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM005_PO.cs` | 1,333 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs` | 891 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs` | 919 |
| `Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM013_PO.cs` | 1,306 |
| `Dev/ATLAS.BBS/Source/Entity/DataEntity.BBS/BBSM001ModelVDB.cs` 等 10 支薄包裝 | 41–47 |

**規律很清楚:實體版的 PO 是 cp950,`1xx` 的 PO 是 UTF-8。**這是 §0.2 判定「`1xx` 寫得比較晚」的旁證之一。用不認 cp950 的工具讀這六個檔會拿到亂碼中文。

- **嚴重度**:低(編譯不受影響),但做全庫文字掃描時一定要處理。

### E15 大段死碼

| 位置 | 內容 | 行數 |
|---|---|---|
| `Dev/ATLAS.BBS/Source/Control/Control.BBS/BBSM013_Ctl.cs:209-914` | 兩支被註解掉的手寫逐欄搬運方法 | 706 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:1190-1499` | 整段被 `/* */` 包起來的舊版 Form 實作,含第二份 `FormInitial` / `AddDataLoad` / `ModifyDataLoad` / 各式事件 | 310 |
| `Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM004.cs:1520-1599` | 三段標「ole code」的區塊註解 | 約 80 |

`BBSM004.cs` 那一段特別值得注意:**它是一支完整的平行實作,而且用的是不同的 VDB 別名與中介表**。看這支畫面時很容易讀到死碼那一半。

- **嚴重度**:低(不執行),但嚴重拖慢閱讀,而且 `BBSM013_Ctl` 的相似度量測會被它扭曲(§4.7.2)。

### E16 兩支畫面同一件事,錯誤處理不一致

| 動作 | `BBSM009`(實體) | `BBSM109`(無實體) |
|---|---|---|
| 撤銷時更新結餘檔 | 影響列數不等於 1 就 throw(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM009_PO.cs:148-151`) | 不檢查(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM109_PO.cs:240-241`) |
| 刪除未覆核單 | 只寫跳號(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM010_PO.cs:867`) | 另做庫存檢核並可能阻擋(`Dev/ATLAS.BBS/Source/PO/PO.BBS/BBSM110_PO.cs:387-406`) |
| 質權人 ID 檢核 | 沒有 | 有(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM109.cs:740`) |
| 轉讓稅額 / 淨值必須大於 0 | 有(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM013.cs:146-148`) | **沒有** |
| 轉讓日期已過帳不可刪除 | **沒有** | 有(`Dev/ATLAS.BBS/Source/UI/UI.BBS/BBSM113.cs:221`) |

**這五條就是「改一支要不要同步另一支」的答案**:五條全部是業務規則,不是寫法差異,而且五條分散在兩個方向(有的實體版多、有的無實體版多)。**沒有人能從程式碼判斷哪一邊才是對的,必須問業務。**

- **嚴重度**:高。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純讀碼彙整,涵蓋 10 支 M 畫面、7 支 R 畫面、20 張表、13 份 rpt;釐清三對 `1xx` 平行畫面的切分維度為「實體憑證 vs 無實體受益權單位」 |

由 build_doc.py v2.0.0 於 2026-09-15 11:46 產生 · 標題 143 · 圖 5 · 表格 87 · 程式錨點 625 · § 連結 52 · 引用檢查：畫面 28（缺 0） · Table 25（缺 0） · Report 13（缺 0） · 結果集 37（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/bms.md
============================================================

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

============================================================
【文件】kb/modules/cas.md
============================================================

# ATLAS CAS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)目前由表名、欄位中文名(`msdata:Caption`)與少數彈出視窗標題**推測**,待選單表 / 對照表回填。ATLAS 沒有把畫面中文名放進版控,16 支畫面裡只有 4 支彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼(`G3` / `GA` / `G17` / `X01`…)、銷售機構代碼(`A0901`)、員工代號白名單、`USAGE = '3'` 等為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:標記的表同時服務 CRM / TMK / CLS / DSM(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CAS 管「代銷通路」這件事的四個面向——通路上的人、拜訪這些人的紀錄、給業務員的業績目標,以及業績該怎麼分帳。**

推測依據有四條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 表名與欄位中文名 | `CAS003A` 的欄位是「潛在客戶序號」「經辨/理專姓名」「職務」「理專等級代碼」;`CAS004A` / `CAS005A` 是「銷售機構代碼」「業務員代碼」「分配比率％」;`CAS001A` / `CAS002A` 是「業績年度」「境外代銷手續費加項」 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:19-21`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:39-74`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:25-46` |
| 彈出視窗標題 | 「代銷組客戶拜訪主管明細表」「代銷客戶拜訪記錄查詢作業」「業務員複製」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.Designer.cs:2613`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001p0.Designer.cs:2588`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.Designer.cs:557` |
| 報表中文名 | 「訪談報告─親訪」「代銷─客戶拜訪統計表」「銷售機構銷售總表」「銷售機構期間收入統計表」「代銷退休管家庫存明細表」 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:92-109`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:179`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:295`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:191` |
| 郵件主旨 | 「代銷組客戶拜訪主管意見回復作業須回復事項」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:328` |

「CAS」三個字母本身的展開在 repo 裡找不到定義,**不要猜**。本文一律用「代銷通路」描述它的業務範圍,這是從上表推出來的,不是官方名稱。

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 通路與人員 | 銷售機構(銀行分行 / 保經代)及其底下的經辦、理專名單、等級、推薦產品類型 | `CASM001` | `CRM003A`〔共用〕+ `CAS003A` |
| B 拜訪作業 | 業務員去拜訪這些通路的紀錄:預計 / 實際拜訪日、拜訪重點、追蹤事項、主管意見與回覆 | `CASM002`、`CASI001`、`CASB001` | `CLS001A` + `CLS002A`〔共用〕 |
| C 業績目標 | 每位業務員每年 / 每月的目標:境外代銷手續費加項、營業收入、定期定額戶數、百萬戶數 | `CASM003`、`CASM006` | `CAS001A` + `CAS002A`、`DSM001A` + `DSM002A`〔共用〕 |
| D 業績分配 | 同一個銷售機構(甚至同一個受益人戶號)的業績,要按什麼比率分給哪幾位業務員 | `CASM004`、`CASM005` | `CAS004A`、`CAS005A` |
| E 報表 | 上面四條線的統計與明細輸出 | `CASR001`–`CASR008` | 全部來自版控外的 SP |

### 0.2 這模組最反直覺的一件事

**16 支畫面、10 張表,但只有 5 張表是 CAS 自己的;而且三支維護畫面的「主檔」都不是自己的表。**

| 畫面 | 主檔 | 主檔屬於 | 明細 | 明細屬於 |
|---|---|---|---|---|
| `CASM001` | `CRM003A` | **CRM / TMK** | `CAS003A` | CAS |
| `CASM002` | `CLS001A` | **CLS** | `CLS002A` | **CLS** |
| `CASM003` | `CAS001A` | CAS | `CAS002A` | CAS |
| `CASM004` | `CAS004A` | CAS | —(無明細) | — |
| `CASM005` | `CAS005A` | CAS | —(無明細) | — |
| `CASM006` | `DSM001A` | **DSM** | `DSM002A` | **DSM** |

也就是說 **CAS 有一半的維護功能,是在別人的表上開第二個入口**。這件事的後果貫穿全文:

1. **改表要跨模組回歸**。`CRM003A` 同時被 `CRMM003` 當主檔;`DSM001A` / `DSM002A` 同時被 `DSMM001` 當主檔。加欄位、改型別、改 PK,兩邊的 xsd 與 Designer 都要重生(見 §8)。

2. **同一張表,兩個入口的可見範圍不同**。`CASM002` 與 `CASI001` 都硬加 `USAGE = '3'` 過濾,`CASB001` 沒有;`CASM006` 只看 8 個部門,`DSMM001` 沒有這條限制。同一筆資料在 A 畫面看得到、B 畫面看不到是**設計如此**,不是 bug——但沒有任何地方寫下來(見 §5、§6、§8)。

3. **四眼欄位的語意由別的模組決定**。`CLS001A` 的 `STATUS` 被 `CASB001` 直接 UPDATE 成 `'301'`,繞過四眼引擎(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341`)。CLS 模組自己的畫面如果依賴狀態機,會看到不合流程的狀態值。

### 0.3 不管什麼

以下**不在** CAS 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(客戶)基本資料 | BMS | `BMS001A` 只被 join 取 `BF_NAME` 與開戶日,從不寫入;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:299-300` |
| 員工主檔、部門、離職日 | COD | `COD009` 全部是 `LEFT JOIN` 或 `SELECT`,無任何 INSERT/UPDATE;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:221-222` |
| 代碼對照(理專等級、推薦產品類型、拜訪方式) | COD / CTL | `COD006A` 依 `CODE_SORT` 分類、`CTL014` 依 `SOURCETYPE` 分類,都只讀;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 銷售機構名稱主檔 | OFD | `OFD068A` 只被 join 取名稱;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:371-372` |
| 實際的申購 / 贖回交易 | OFD / EC | CAS 的表裡沒有任何交易金額欄位;報表的交易數字全部來自版控外的 SP |
| 業績的實際計算 | **不明** | `CAS001A` / `DSM001A` 只存「目標」,`CAS004A` / `CAS005A` 只存「比率」。真正拿這些比率去分帳的程式不在 CAS 內,repo 裡也找不到。**假設**:在版控外的 SP 或別的模組,依據是本模組沒有任何一支程式讀 `DIV_PCT` 去做計算 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 代銷業務員 | 填拜訪單(`CASM002`)、查自己的拜訪紀錄(`CASI001`) | `CASI001` 用登入者的員工代號當強制條件,只看得到自己的;`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:198-209` |
| 主管 | 批次勾選拜訪單、寫主管意見、寄信要求業務回覆(`CASB001`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342` |
| 5 位特定人員 | 不受「只看自己」限制,看得到全部拜訪紀錄 | 員工代號寫死在 SQL 組字串裡;`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206`〔客戶特定〕 |
| 代銷組管理人員 | 維護通路人員(`CASM001`)、設定業績目標(`CASM003` / `CASM006`)與分配比率(`CASM004` / `CASM005`) | 這幾支都是標準四眼維護畫面,權限由框架的功能權限決定,程式內看不到 |
| 覆核者 | 對上述維護做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |

**注意:除了 `CASI001` 那條寫死的員工白名單之外,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。

### 0.5 全域開關

repo 內**沒有**任何 CAS 專屬的設定檔開關。`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔與主鍵,給框架做 grid 的 PK 檢查用 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:28`(`CASM001`)、`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:37`(`CASM002`)、`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:44-45`(`CASM003`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:30` |
| `formstyle` | `CASB001` / `CASI001` 宣告為 `OneStep`;報表側全部 `Report` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:16`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/App.config:16` |

兩個要記住的:

- **`CASM001` 的 `detailtable` 那行是被註解掉的**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:29`),但 PO 確實宣告了明細表(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:47`)。畫面靠 `m_PkeyNotInMaster` 手動補明細 PK(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:129`),不是靠設定。

- **`CASM002` 根本沒宣告 `detailtable`**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:34-40`),但 PO 有(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:47`)。設定檔與程式不一致,以程式為準。

`TargetFramework` 側只有一個註記值得記:`Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:74` 宣告 `.NETFramework,Version=v4.8`,而 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:5` 留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡——這批檔案在升版時被逐檔改過,不是整批 retarget。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CAS 模組全景：通路主檔、拜訪作業、業績目標與分配、報表四條線，以及十張表的歸屬
圖中文字:① 通路與人員主檔（資料來源在別的模組） / CASM001 / 銷售機構+經辦 CRM003A / CRM003A〔共用〕 / 主檔屬 CRM／TMK / CAS003A / 經辦明細 本模組自有 / COD009 COD006A / 員工／代碼 外部 / ② 拜訪作業（主檔屬 CLS） / CASM002 / 拜訪單維護 CLS001A / CLS001A CLS002A / 〔共用〕主檔屬 CLS / CASI001 / 拜訪紀錄查詢 唯讀 / CASB001 / 主管批次回覆+寄信 / ③ 業績目標與分配比率 / CASM003 / 年月手續費加項 CAS001A / CASM006 / 年月業績目標 DSM001A / CASM004 / 機構×業務員 CAS004A / CASM005 / 再加戶號 CAS005A / ④ 報表（七層，資料全在版控外的 SP） / CASR001 / 訪談報告6式 / CASR002 / 業務人員統計 Excel / CASR003 CASR007 / 機構銷售／定額契約 / CASR004 CASR008 / 機構期間收入／排行 / CASR005 CASR006 / 退休管家／每日申購 / ⑤ 資料來源：10 張表只有 5 張是 CAS 自有 / CAS001A CAS002A / 年／月手續費加項 / CAS003A / 經辦明細 / CAS004A CAS005A / 分配比率 / CRM003A CLS001A CLS002A / DSM001A DSM002A 借用
```

*圖:圖 1 CAS 全景。橘框=本模組的維護入口；灰虛框=借用別模組的表或唯讀來源；黑框=無原始碼的外部代碼表；橘虛框=行為含寫死值〔客戶特定〕。四條線彼此只靠表相連，沒有程式呼叫關係。*

看圖的三個重點:

1. **四條業務線之間沒有程式呼叫關係。** `CASM001` 不會叫 `CASM002`,`CASM003` 不會叫 `CASM004`。它們只透過表相連:`CASM002` 的主檔 SQL 去 join `CRM003A`(`CASM001` 維護的)與 `CAS004A`(`CASM004` 維護的),`CASI001` 也是。所以改 `CASM004` 的欄位,會打到 `CASM002` 的查詢結果(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224`)。

2. **報表那一排與上面三排完全脫鉤。** 8 支 R 畫面沒有一支引用 CAS 的任何 PO,資料全部來自 `S_TA_CASRnnn_GET` 這類版控外的 SP(§7)。也就是說**報表看到的數字,跟維護畫面寫進去的值之間的關係,在 repo 內是斷的**。

3. **只有 `CASB001` 會寫別條線的資料。** 它直接 UPDATE `CLS002A`,而且把四眼欄位一起蓋掉(§6)。

### 1.2 資料表關係

見 §2 節首的圖。三組主明細、兩張非實體結果集、五張外部唯讀表。要記住的是:

- **主明細的綁定靠 `dataid`,不是靠外鍵。** 同一次 EVA 生命週期內主檔與所有明細共用一個 `Guid`(`architecture.md §3.3`),所以主檔與明細一定一起送審、一起覆核。

- **`CAS004A` 與 `CAS005A` 沒有明細表。** 它們是單表四眼畫面,`DetailTable` 完全沒宣告(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:42`)。

- **`CLS002A` 實際上是 1:1 的續頁,不是真明細。** `CASM002` 存檔時只取第一列(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:103-110`),沒有列數概念。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接 `new` 一個 `_Pxy` 打過去 | 對話框(不是訊息清單) |
| 4 主檔欄位回填明細 | `SetMasterToDetail()` | 不會失敗,但漏欄位會讓明細 PK 是空的 |
| 5 PO 的 `Before*` | `BeforeAdd` 取號、`BeforeSelect` 換 SQL | 例外 → 整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `After*` | 只有 `CASM001` / `CASM002` 有 | `throw` → 整筆回滾 |

**第 1 到第 4 階段全部在用戶端。**伺服器端沒有任何一支程式重驗這些規則,所以任何繞過 UI 的呼叫路徑(例如直接 `new CASM001_Pxy()`)都不受這些卡控保護。

### 1.4 批次 / 報表資料流

見 §7 節首的圖。兩件事:

- **報表是兩條獨立往返**:`GetReportData` 拿資料、`GetReportObject` 拿 `.rpt` 檔的 byte。後者的類別名由用戶端傳過來,伺服器照單全收(`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR005_Ctl.cs:61-62`,與 `architecture.md §6.5` 描述一致)。

- **批次只有一支**(`CASB001`),而且沒有 WindowsService。它是使用者按按鈕觸發的「批次」,不是排程(§6)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,所以以下是**推測**的作業順序,依據是資料相依:某張表要有資料,前一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 年度開始前 | 代銷組管理 | 設定各業務員的年度目標與月分配 | `CASM003`、`CASM006` | 員工要先在 `COD009` 存在 |
| 年度開始前 | 代銷組管理 | 設定各銷售機構的業績分配比率 | `CASM004`、`CASM005` | 機構要先在 `OFD068A` 存在 |
| 平時 | 代銷組管理 | 新增 / 維護通路上的經辦與理專 | `CASM001` | — |
| 平時(拜訪後) | 業務員 | 填拜訪單 | `CASM002` | 通路要先在 `CASM001` 建好(`PR_NO`) |
| 平時 | 業務員 | 查自己的拜訪紀錄 | `CASI001` | — |
| 定期(推測每週 / 每月) | 主管 | 批次勾選、寫主管意見、寄信要求回覆 | `CASB001` | 拜訪單要先存在 |
| 月結 / 期間結束後 | 代銷組管理 | 出各式統計與明細報表 | `CASR001`–`CASR008` | 版控外的 SP 決定 |

**假設**:`CASB001` 的頻率。依據是它的查詢條件預設值是「未閱」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:42`),而且每次重整都會重設成「未閱」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:60`)——這是「把積壓的未處理清掉」的用法,不是「查歷史」的用法。實際頻率要問使用者。

## 2. 資料模型

```text
[圖] CAS 十張表的主明細關係、主鍵組成，以及外部唯讀表
圖中文字:本模組自有（5 張） / CAS001A / PK QUO_YEAR+EMP_NO / CAS002A / +QUO_YYMM 月明細 / CAS003A / PK PR_NO+STAFF_NAME / CAS004A / PK YYMM+3 碼機構+人 / CAS005A / 同上再加 BF_NO / CAS004A_OVER / 結果集 非實體表 / 借用他模組（5 張，改動要看 §8） / CRM003A〔共用〕 / PK PR_NO · CRM TMK / CLS001A〔共用〕 / PK CALL_RPT_NO · CLS / CLS002A〔共用〕 / 同單號 1:1 續頁 / DSM001A DSM002A / 年／月目標 · DSM / 四眼欄位齊不齊（見 §2.2） / 有全套 13 欄 / CAS003A CLS001A CLS002A CRM003A / 只有日期欄有 Caption / CAS001A/2A/4A/5A DSM001A/2A / DATAFLAG 每張都有 / 樂觀鎖唯一比對欄 / 外部唯讀（join 進來，不屬本模組） / COD009 / 員工／部門／離職日 / COD006A / CODE_SORT 代碼說明 / CTL014 / SOURCETYPE 下拉 / OFD068A / 銷售機構名稱 / BMS001A / 受益人資料
```

*圖:圖 2 資料模型。橘框=主檔；灰虛框=借用或非實體表；黑框=外部唯讀表。實線箭頭=主明細（同一次 EVA 一起送審）；虛線=同一支畫面內的弱關聯。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`)。CAS 六支 M 畫面的宣告:

| 畫面 | `MasterTable` | `DetailTable` | 錨點 |
|---|---|---|---|
| `CASM001` | `CRM003A` | `CAS003A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:46-47` |
| `CASM002` | `CLS001A` | `CLS002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:46-47` |
| `CASM003` | `CAS001A` | `CAS002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:33-34` |
| `CASM004` | `CAS004A` | **無** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:42` |
| `CASM005` | `CAS005A` | **無** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:39-43` |
| `CASM006` | `DSM001A` | `DSM002A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33` |

`CASI001` 與 `CASB001` 的 `MasterTable` 那行**是被註解掉的**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:42`),兩支都是裸 DAO,不繼承 `BaseEVADaoPO`。掃描器把那行註解當宣告,所以母體會回報一個不存在的主檔 `OFD701`——這個誤判 `architecture.md §6.3` 已經記過,本文一律以程式為準。

八支 R 畫面的 PO 完全沒有 `xTableMapping`,它們的「表」是 SP 回來的結果集形狀(§7)。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源,兩邊一致:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。

| 表 | 主鍵(xsd) | 主鍵(App.config) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `CAS001A` | `QUO_YEAR` + `EMP_NO` | `QUO_YEAR,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:200-204` |
| `CAS002A` | `QUO_YEAR` + `QUO_YYMM` + `EMP_NO` | `QUO_YEAR,EMP_NO,QUO_YYMM` | ✔(順序不同,不影響) | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:205-210` |
| `CAS003A` | `PR_NO` + `STAFF_NAME` | (被註解) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:133-137` |
| `CAS004A` | `YYMM` + `EMP_NO` + `AGENT_CODE` + `AGENT_ID` | `YYMM,AGENT_ID,AGENT_CODE,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:155-161` |
| `CAS005A` | `YYMM` + `EMP_NO` + `AGENT_CODE` + `AGENT_ID` + `BF_NO` | `YYMM,AGENT_ID,AGENT_CODE,EMP_NO,BF_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM005Model.xsd:164-171` |
| `CLS001A` | `CALL_RPT_NO` | `CALL_RPT_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:185-188` |
| `CLS002A` | `CALL_RPT_NO` | (未宣告) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:189-192` |
| `CRM003A` | `PR_NO` | `PR_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:138-141` |
| `DSM001A` | `QUO_YEAR` + `EMP_NO` | `QUO_YEAR,EMP_NO` | ✔ | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:211-215` |
| `DSM002A` | `QUO_YEAR` + `QUO_YYMM` + `EMP_NO` | (未宣告) | — | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:216-221` |

**`CLS002A` 的 PK 只有 `CALL_RPT_NO`,跟主檔一樣。**這證實它是 1:1 續頁而不是明細——一張拜訪單只會有一列主管意見。程式也是這樣寫的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:103-110`)。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 有中文名的欄 | 說明 |
|---|---|---|---|
| `CAS003A` | ✔ | 全部 13 欄都有 Caption | 最完整的一張 |
| `CLS001A` | ✔ | 全部 13 欄都有 Caption | 連 `DATAFLAG` 都有「資料異動碼」 |
| `CRM003A` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `CLS002A` | ✔ | 在 `CASM002Model.xsd` 內沒有 | 同一張表在 `CASB001Model.xsd` 內也沒有 |
| `CAS001A` `CAS002A` `CAS004A` `CAS005A` `DSM001A` `DSM002A` | ✔ | **一個都沒有** | 六張表的四眼欄位全部無中文名 |

**結論:10 張表全部有完整四眼欄位,但只有 2 張表的四眼欄位填了中文名。**這直接對應 `architecture.md §5.5` 說的「只有 53% 的欄位有 Caption」——CAS 這邊的缺口集中在四眼欄位上。

`DATAFLAG` 每張表都有,型別一律 `xs:base64Binary`,而且標了 `msdata:ReadOnly="true"`(例:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:102`)。它是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

以下中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**。空白代表該 xsd 沒有填。

#### `CAS001A` — 年度業績目標主檔(20 欄,`CASM003` 主檔)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y | 四眼批次識別 `Guid` |
| `QUO_YEAR` | 業績年度 | string(4) | — | PK |
| `EMP_NO` | 員工代碼 | string(10) | — | PK |
| `BOUNS_ST_YYMM` | 起算年月 | string(6) | Y | 必須與業績年度同年(§4.3) |
| `OFD_INC_ALLOT_FEE_TOT` | 境外代銷手續費加項 | decimal | Y | 預設 0;必須 > 0 且等於明細總和 |
| `EMP_NAME` | 員工姓名 | string | Y | **衍生欄**,`COD009` join 進來,不落地 |
| 其餘 13 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:15-106`。

#### `CAS002A` — 月業績目標明細(19 欄,`CASM003` 明細)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y |  |
| `QUO_YEAR` | 業績年度 | string(4) | — | PK,由主檔回填 |
| `EMP_NO` | 員工代碼 | string(10) | — | PK,由主檔回填 |
| `QUO_YYMM` | 業績年月 | string(6) | — | PK,由「月分配」鈕產生 |
| `OFD_INC_ALLOT_FEE` | 境外代銷手續費加項 | decimal | Y | 預設 0;必須 > 0 |
| 其餘 14 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |

**沒有 `EMP_NAME`。**明細不 join `COD009`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:216-223`)。

#### `CAS003A` — 通路經辦 / 理專明細(35 欄,`CASM001` 明細)

| 欄位 | 中文名 | 型別 | 可空 |
|---|---|---|---|
| `DATAID` |  | string | Y |
| `PR_NO` | 潛在客戶序號 | string | — |
| `STAFF_NAME` | 經辨/理專姓名 | string | — |
| `STAFF_POST` | 職務 | string | Y |
| `STAFF_POSITION` | 經辨職稱 | string | Y |
| `SEX` | 性別 | string | Y |
| `MGR_NAME` | 主管姓名 | string | Y |
| `MGR_POSITION` | 主管職稱 | string | Y |
| `OF_TEL_AREA` | 電話區域碼 | string | Y |
| `OF_TEL` | 電話號碼 | string | Y |
| `FAX_TEL_AREA` | 傳真電話區域碼 | string | Y |
| `FAX_TEL` | 傳真電話 | string | Y |
| `CELL_PHONE` | 行動電話 | string | Y |
| `EMAIL` |  | string | Y |
| `INVEST_CODE` | 投資特性 | string | Y |
| `STAFF_TYPE` | 理專等級代碼 | string | Y |
| `INTRO_TYPE` | 理專推薦產品類型 | string | Y |
| `SEND_FUND_YN` | 傳送基金相關資料 | string | Y |
| `MEMO` | 備註 | string | Y |
| `STATUS` | 資料識別碼 | string | Y |
| `CREATEID` / `CREATEDATE` | 資料建立者 / 日期 | string / dateTime | Y |
| `UPDATEID` / `UPDATEDATE` | 最後修改者 / 日期 | string / dateTime | Y |
| `ENTRYID` / `ENTRYDATE` | 最後輸入者 / 日期 | string / dateTime | Y |
| `VERIFYID` | 資料確認者 | string | **—** |
| `VERIFYDATE` | 資料確認日期 | dateTime | Y |
| `APPROVEID` / `APPROVEDATE` | 資料覆核者 / 日期 | string / dateTime | Y |
| `REJECTID` / `REJECTDATE` | 資料退回者 / 日期 | string / dateTime | Y |
| `DATAFLAG` |  | base64Binary | Y |
| `STAFF_TYPE_DESCRP` | 理專等級代碼說明 | string | Y |
| `INTRO_TYPE_DESCRP` | 理專推薦產品類型說明代碼 | string | Y |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:15-55`。

三件要注意的:

1. **`STATUS` 的 Caption 寫成「資料識別碼」**,那是 `DATAID` 的意思,不是狀態。這個錯字在 `CLS001A` 也一樣(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:45`)。看 Caption 判斷欄位用途會判錯。

2. **`VERIFYID` 是唯一沒有 `minOccurs="0"` 的四眼欄位**(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:44`),也就是 DataSet 層要求它不可為 null。新增一筆還沒驗證時它是什麼值,程式裡看不到——由框架 DLL 決定(**假設**:空字串,依據是 `architecture.md §3.5` 的 13 欄一律送值)。

3. **末兩欄 `*_DESCRP` 是畫面計算欄**,由 SQL 的 `CODE_DESCRP AS …` 產生(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:317-318`),不落地。

#### `CAS004A` — 機構業務員分配比率(26 欄,`CASM004` 主檔)

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `DATAID` |  | string(38) | Y |  |
| `YYMM` | 業績年月 | string(6) | — | PK |
| `AGENT_ID` | 銷售機構區別碼 | string(6) | — | PK,下拉來源代碼 `062` |
| `AGENT_CODE` | 銷售機構代碼 | string(9) | — | PK |
| `EMP_NO` | 業務員代碼 | string(10) | — | PK |
| `AREA_CODE` | 區域別 | string(6) | Y | 下拉來源代碼 `467` |
| `DEPT_CODE` | 組別 | string(6) | Y | 下拉來源代碼 `468` |
| `MRG_YN` | 組長別 | string(6) | Y | 下拉來源代碼 `473`,新增預設 `N` |
| `DIV_PCT` | 分配比率％ | decimal | Y | 必須 > 0;同組合加總不得 > 100 |
| `START_DATE` | 開始日期 | string(8) | Y | 預設等於業績年月 |
| 其餘 14 欄 |  |  | Y | 四眼欄位 + `DATAFLAG` |
| `AGENT_NAME` | 銷售機構名稱 | string | Y | **衍生欄**,`OFD068A` join |
| `EMP_NAME` | 銷售員姓名 | string | Y | **衍生欄**,`COD009` join |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM004Model.xsd:15-142`。

#### `CAS005A` — 受益人層分配比率(28 欄,`CASM005` 主檔)

與 `CAS004A` 逐欄相同,只多兩欄:

| 欄位 | 中文名 | 型別 | 可空 | 備註 |
|---|---|---|---|---|
| `BF_NO` | 受益人戶號 | string(10) | — | **第 5 個 PK 欄** |
| `BF_NAME` | 受益人姓名 | string | Y | **衍生欄**,`BMS001A` join |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM005Model.xsd:15-150`。注意 `AGENT_NAME` 在這裡取的是 `OFD068A` 的 `AGENT_NAME` 欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:283`),而 `CASM004` 取的是 `AGENT_SHNM` 欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:361`)。**同一個概念兩張畫面取不同來源欄,顯示出來的機構名稱可能不一樣**(附錄 E)。

#### 借用的五張表 — 只列本模組會動到的欄

`CRM003A`(`CASM001` 主檔,xsd 內 69 欄,索引記 72 欄):

| 本模組會寫的欄 | 中文名 | 誰寫 |
|---|---|---|
| `PR_NO` | 潛在客戶序號 | `BeforeAdd` 取流水號 |
| `USAGE` | 用途別 | UI 寫死 `"3"` |
| `ID_NO` `PR_NAME` `EMP_NO1` `CNT_PERSON` `POSITION_DESC` `EMAIL` | 銷售機構金資 / 銷售機構 / 員工編號 / 聯絡人 / 職稱 / — | `SetMasterToDetail` |
| `CUST_CLASS1` `CUST_CLASS2` `DES_MAKER` | 總行等級 / 分行等級 / 決策者 | 同上 |
| `ADDR_CODE1` 與 12 個 `MAIL_*` | 通訊地址各段 | 同上,由 `ucAddress` 控件拆解 |
| `OF_TEL_AREA` `OF_TEL` `FAX_TEL_AREA` `FAX_TEL` | 公司電話 / 傳真 | 同上,`OF_TEL` 會把分機用 `#` 串在一起 |
| `AREA_CODE` `DEPT_CODE` `SEND_INFO_YN` | 區域別 / 組別 / 發文通知 | 同上 |

錨點:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:45-95`。**`CRM003A` 其餘約 50 欄本模組不碰**,包括 `BF_NO`、`CUST_TYPE`、`REJ_SELL_*` 那一整組拒絕行銷旗標——但 `CUST_TYPE` 會被讀來擋刪除(§4.1)。

`CLS001A`(`CASM002` 主檔,xsd 內 59 欄;`CASI001` 版 78 欄、`CASB001` 版 74 欄):**同一張表在三支畫面的 xsd 裡欄位集合不同**,這是 `architecture.md §5.4` 說的「Model/View 不同構」在同模組內的加強版——連 Model 之間都不同構。三份 xsd 的差異:

| 只在某一份出現的欄 | 在哪一份 | 用途 |
|---|---|---|
| `CUST_WILL_DESCRP` `CUST_CLASS_DESCRP` | `CASM002Model` | 畫面計算欄 |
| `QUERY_EMP_NO` `CUST_CLASS` 與 9 個 `*_DESCRP` | `CASI001Model` | 查詢畫面的說明欄 |
| `ISCHECK` `EMP_NAME` 與 10 個 `*_DESCRP` | `CASB001Model` | 批次勾選欄與說明欄 |

`ISCHECK` 是 `xs:boolean` 且 `default="false"`(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:70`),**它不是資料庫欄位**,是批次畫面的勾選狀態。同一個 `ISCHECK` 也出現在 `CLS002A` 的定義裡(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd:123`),但程式從來不用那一個。

`CLS002A`(`CASM002` 明細,25–26 欄):除 `DATAID` / `CALL_RPT_NO` 與 13 個四眼欄外,只有 9 個業務欄:

| 欄位 | 中文名(取自 `CASM002Model`) |
|---|---|
| `MGR_DESC` | 主管意見 |
| `CFM_USER1` | 主管1(小組長)閱 |
| `CFM_USER2` | 主管2(主管)閱 |
| `CONNECT_DESC` | 溝通事項 |
| `CONNECT_RE` | 業務需回覆否 |
| `ERR_DESC` | 異常狀況 |
| `EXEC_DESC` | 處理情形 |
| `SALES_CONNECT_DESC` | 業務回覆溝通事項 |
| `SALES_CONNECT_RE` | 業務已回覆 |

錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd:85-93`。**這 9 欄就是 `CASB001` 批次更新的全部內容**(§6)。

`DSM001A` / `DSM002A`(`CASM006` 主明細,26 / 24 欄):結構與 `CAS001A` / `CAS002A` 完全平行,差別只在業務欄從 1 個變成 6 個。

| `DSM001A` 欄位 | 中文名 | `DSM002A` 對應欄 |
|---|---|---|
| `QUO_MGR_TOT` | 營業收入 | `QUO_MGR` |
| `QUO_RSP_NM_TOT` | 定期(不)定額戶數-目標 | `QUO_RSP_NM` |
| `QUO_RSP_LNM_TOT` | 定期(不)定額戶數-保守 | `QUO_RSP_LNM` |
| `QUO_RSP_AMT_TOT` | 定期(不)定額扣款成功金額 | `QUO_RSP_AMT` |
| `QUO_MIL_NA_TOT` | 新開百萬戶數 | `QUO_MIL_NA` |
| `QUO_MIL_A_TOT` | 單筆申購交易百萬戶數 | `QUO_MIL_A`(Caption 少了「數」) |

`DSM001A` 另有 `DEPT_NO`(部門代碼)一欄,是 `COD009` join 進來的衍生欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113`),不落地。錨點:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:15-208`。

### 2.4 與其他模組共用的表

完整影響面在 §8。這裡只記歸屬:

| 表 | 屬於 | CAS 怎麼用 | 誰還在用 |
|---|---|---|---|
| `CRM003A` | CRM / TMK | `CASM001` 當主檔,增刪改;`CASM002` / `CASI001` / `CASB001` 唯讀 join | `CRMM003` |
| `CLS001A` | CLS | `CASM002` 當主檔增刪改;`CASI001` 唯讀;`CASB001` 讀 | CLS 模組 |
| `CLS002A` | CLS | `CASM002` 當明細;`CASB001` **直接 UPDATE** | CLS 模組 |
| `DSM001A` | DSM | `CASM006` 當主檔 | `DSMM001` |
| `DSM002A` | DSM | `CASM006` 當明細 | `DSMM001` |

外部唯讀(只 join,不寫):`COD009`(員工)、`COD006A`(代碼說明)、`CTL014`(下拉值)、`OFD068A`(銷售機構名)、`BMS001A`(受益人)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`architecture.md §3.10` 從全庫 SQL 字面量反推,**假設** `EVAStatusCode` 的實際值是單字元 `'0'`–`'9'`。**CAS 提供一個直接的反證:**

```
ResultVDB.DataEntity.CLS001A.STATUSColumn.DefaultValue = "301";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406` 與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:229`,以及批次真的寫進 DB 的那一行 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341`。

三邊互相吻合:

| 證據 | 內容 |
|---|---|
| xsd 宣告 | `STATUS` 一律 `xs:string` `maxLength = 3`(例 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:47-52`) |
| 程式寫入 | 三處都寫 `"301"` |
| 對照 `architecture.md §3.10` | 該節的單字元假設與此不符 |

**結論:`STATUS` 是 3 碼字串,不是單字元。**`"301"` 代表什麼語意,repo 內找不到——`EVAStatusCode` 常數在框架 DLL 裡(無原始碼,從呼叫端反推)。從 `CASB001` 的用法(批次把主管已閱的單子設成這個值,同時把 `APPROVEID` / `APPROVEDATE` 一起寫進去)**推測**它屬於 `Approve*` 那一族,也就是「已覆核」。這是**假設**,要確定得查資料庫或反編譯 `Vendor.Product.Utility.MappingCode`。

#### 本模組自訂的旗標值

以下是 CAS 程式碼裡直接比對的字面值,全部沒有常數定義:

| 欄位 | 值 | 語意(反推) | 錨點 |
|---|---|---|---|
| `USAGE` | `'3'` | 「代銷通路」這一類的 `CRM003A` 資料 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`(寫入)、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224`(過濾) |
| `USAGE` | `<> '1'` | 匯出 Excel 時排除的另一類 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:534` |
| `CUST_TYPE` | `'9'` | 代操客戶,原則上不可刪 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442` |
| `DEPT_NO` | `'X01'` | 可以刪代操客戶的特例部門 | 同上〔客戶特定〕 |
| `SEND_FUND_YN` | `'Y'` | 要傳送基金資料 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:535` |
| `SEND_INFO_YN` | `'Y'` / `'N'` | 發文通知 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:92-95` |
| `ADDR_CODE1` | `'1'` / `'0'` | 通訊地址型別 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:300` |
| `CALL_TYPE2` | `'2'` | 實際拜訪方式 = 不需車資的那一種 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:628` |
| `CFM_USER1` / `CFM_USER2` | `'Y'` | 主管已閱 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:211-214` |
| `CONNECT_RE` | `'Y'` | 業務需回覆 → 觸發寄信 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:323` |
| `MRG_YN` | `'N'` | 非組長(新增預設) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:195` |
| `RPT_KIND` | `'RPT'` | 報表格式(否則走 Excel 版 SP) | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |

#### 代碼分類碼(`CODE_SORT` / `SOURCETYPE`)

CAS 用到的代碼分類,全部寫死在 SQL 或 UI 裡:

| 分類碼 | 表 | 用途(反推) | 錨點 |
|---|---|---|---|
| `CODE_SORT = '20'` | `COD006A` | 理專等級 / 客戶等級 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:217`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:236` |
| `CODE_SORT = 'P1'` | `COD006A` | 拜訪重點代碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:154` |
| `CODE_SORT = 'P3'` | `COD006A` | 追蹤事項 / 推薦產品類型 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:157`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:255` |
| `CODE_SORT = 'P6'` | `COD006A` | 經辦職務 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:216` |
| `CODE_SORT = '19'` | `COD006A` | 客戶投資意願 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:227` |
| `SOURCETYPE = '447'` | `CTL014` | 拜訪方式 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:151` |
| `SOURCETYPE = '469'` | `CTL014` | 投資特性 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:573` |

UI 端的下拉來源代碼(`GetDropDownDataSrc` / `GetDropDown9iDataSrc` 的參數)是另一套編號,整理在附錄 C。**兩套編號互不相通**,而且同一支畫面會混用 `GetDropDownDataSrc` 與 `GetDropDown9iDataSrc` 兩種實作(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:116-121`),這點 `architecture.md §2.6` 已經記過。

## 3. 畫面清冊

16 支畫面,**六層全齊**(掃描器實測,無假警報)。分佈:B 1 / I 1 / M 6 / R 8。中文名一律標「待選單表」——repo 內只有 4 支彈出視窗有 `this.Text`,主畫面標題由框架從平台庫取得,程式裡看不到。

### 3.1 維護 M

| 代號 | 中文名(待選單表) | 六層 | 主表 | 明細 | SP / Fn | rpt / 彈出視窗 |
|---|---|---|---|---|---|---|
| `CASM001` | 通路經辦 / 理專維護(推測) | 齊 | `CRM003A`〔共用〕 | `CAS003A` | 無 | 無;有「匯出 Excel」鈕 |
| `CASM002` | 客戶拜訪單維護(推測) | 齊 | `CLS001A`〔共用〕 | `CLS002A`〔共用〕 | 無 | `CASM002RPS`(拜訪記錄單) |
| `CASM003` | 年度境外代銷手續費加項維護(推測) | 齊 | `CAS001A` | `CAS002A` | 無 | 無 |
| `CASM004` | 銷售機構業務員分配比率維護(推測) | 齊 | `CAS004A` | 無 | `S_TA_CASM004_P01` | `CASM004p0`「業務員複製」 |
| `CASM005` | 受益人層分配比率維護(推測) | 齊 | `CAS005A` | 無 | 無(走程式內複製) | `CASM005p0`「業務員複製」 |
| `CASM006` | 年度業績目標維護(推測) | 齊 | `DSM001A`〔共用〕 | `DSM002A`〔共用〕 | 無 | 無 |

六支的共同結構:`xMaintainForm` + `TabPages = 2`(查詢頁 + 維護頁)+ `BaseEVADaoPO`。逐支的 `FormInitial` 錨點: `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:107-183`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:133-160`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:175-190`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:145-161`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:58-90`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:278-293`。

**兩個分組**,差別大到影響維護方式:

| 分組 | 誰 | 特徵 |
|---|---|---|
| 有跳號一覽表 | `CASM001`、`CASM002` | PO 掛 8 個 `After*` 事件寫 `SrNoComment` 稽核軌跡;UI 掛 `AfterComment` / `AfterModifyTabShow` / `DoMnuCus1Click`;PK 由 `BeforeAdd` 取流水號 |
| 沒有 | `CASM003`–`CASM006` | PO 只掛 3 個 `Before*`;PK 由使用者輸入;刪除不留紀錄 |

差異的根源是 PK 的來源:`CRM003A` 的 `PR_NO` 與 `CLS001A` 的 `CALL_RPT_NO` 是系統流水號,會有「跳號」問題(取號後放棄不用),所以要有一覽表交代;其餘四支的 PK 是年月 + 員工代碼這種業務鍵,不會跳號。

### 3.2 查詢 I

| 代號 | 中文名 | 六層 | 主表 | 明細 | SP / Fn | 備註 |
|---|---|---|---|---|---|---|
| `CASI001` | 代銷客戶拜訪記錄查詢作業 | 齊 | (PO 的宣告被註解)實際查 `CLS001A` | `CLS002A` join 進來 | 無 | 彈出視窗 `CASI001p0` 顯示單筆明細 |

中文名來自 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001p0.Designer.cs:2588`,是彈出視窗的標題,主畫面應該同名(**假設**)。 PO 不繼承任何基底、自建兩條 `Database` 連線(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:33-36`),與 `architecture.md §6.3` 描述的 I 型樣板一致。

### 3.3 批次 B

| 代號 | 中文名 | 六層 | 主表 | 寫哪張 | SP / Fn | 備註 |
|---|---|---|---|---|---|---|
| `CASB001` | 代銷組客戶拜訪主管明細表 | 齊 | (PO 的宣告被註解)實際查 `CLS001A` + `CLS002A` | **`CLS002A`** | 無 | 彈出視窗 `CASB001p0` 編輯單筆;有寄信 |

中文名來自 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.Designer.cs:2613`。 **沒有對應的 WindowsService**,全庫只有 4 支 B 畫面配服務,`CASB001` 不在其中(`architecture.md §6.4`)。它是使用者按「執行」鈕觸發的前景作業。

### 3.4 報表 R

| 代號 | 中文名(取自程式內字串) | 六層 | 取數 SP | rpt |
|---|---|---|---|---|
| `CASR001` | 訪談報告(6 種) | 齊 | `S_TA_CASR001_GET` | `CASR001RPS`…`CASR001RPS6`(6 支) |
| `CASR002` | 代銷組業務人員明細統計表 | 齊 | `S_TA_CASR002_GET` | **無**,只出 Excel |
| `CASR003` | 銷售機構銷售總表 | 齊 | `S_TA_CASR003_GET` | `CASR003RPS`、`CASR003RPS1` |
| `CASR004` | 銷售機構期間收入統計表 | 齊 | `S_TA_CASR004_GET` / `S_TA_CASR004_GET_XLS` | `CASR004RPS` |
| `CASR005` | 代銷退休管家庫存明細表 / 統計表 | 齊 | `S_TA_CASR005_GET` | `CASR005RPS`、`CASR005RPS1`(另有孤兒檔 `CASR005RPS11`) |
| `CASR006` | 每日申購信託基金交易明細表 | 齊 | `S_TA_CASR006_GET` | `CASR006RPS`、`CASR006RPS2` |
| `CASR007` | 銷售機構定額契約統計表 | 齊 | `S_TA_CASR007_GET` | `CASR007RPS` |
| `CASR008` | 銷售機構期間銷售統計表 / 排行表 | 齊 | `S_TA_CASR008_GET` | `CASR008RPS`、`CASR008RPS1`、`CASR008RPS2` |

中文名錨點:`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:92-109`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:332`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:179`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:295`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:191`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:178-187`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:138`、`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:347-361`。

**R 是七層不是六層**,各層資料夾與組件都加 `Report` 前綴,細節見 `architecture.md §6.5`。第七層 `Report.CAS` 裝 19 支 `.rpt` 中的 17 支,另外 2 支(`CASR003RPS`、`CASR005RPS11`)躺在 `ReportUI.CAS` 資料夾,靠 PostBuild 的 `xcopy` 交付(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331`)。

### 3.5 一眼看出差別的四件事

| 面向 | M(6 支) | I(1 支) | B(1 支) | R(8 支) |
|---|---|---|---|---|
| PO 基底 | `BaseEVADaoPO` | 無基底,自建 `Database` | 無基底,自建 `Database` | 無基底,自建 `Database` |
| SQL 在哪 | PO 的 `BuildMasterSQLString` | PO 的 `Select` 一整段 | PO 的 `Select` 一整段 | **不在程式裡**,全在 SP |
| 四眼 | 走引擎 | 無 | **繞過引擎直接 UPDATE** | 無 |
| 交易 | 框架管 | 無寫入 | 自己 `BeginTransaction` | 自己 `BeginTransaction`(只為讀) |
| SQL 參數化 | **否**,字串串接 | **否** | 查詢否 / 寫入是 | **是**,全部 bind |

最後一列是本模組最大的技術債:**維護與查詢畫面的查詢條件全部用字串串接組進 SQL**,唯二用綁定參數的地方是 `CASM002` 的報表查詢(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:588`)與 `CASB001` 的批次寫入(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354`)。詳見附錄 E。

## 4. 維護畫面(M)— 一支一節

```text
[圖] M 畫面從按鈕到四眼引擎的卡控順序，以及各畫面掛了哪些事件
圖中文字:① 用戶端（UI）：全部卡控都在這一層，伺服器不重驗 / Before*ButtonClicked / Add/Modify/Delete/Search / validatorManager1 / 必填與格式 框架決定 / DoValidate() / 本畫面自訂檢核 / Pxy 直呼 DB 檢核 / IsID_NOExsits 等 / ② SetMasterToDetail：把主檔欄位回填到每一列明細（漏做＝明細 PK 空） / SetMasterToDetail / USAGE/PR_NO 寫死回填 / ProcessVDB / ViewVDB 過 Remoting / ③ 伺服端：PO 事件掛點（見 architecture 四眼章） / BeforeAdd / 取流水號 撞號重取 / BeforeSelect / 整條 SQL 換掉 / BeforeGetToDoData / 待辦清單語法 / EVA 引擎 / 無原始碼 DLL 內 / ④ After*：唯一能否決整筆的手段是 throw / AfterVerify Approve / 跳號一覽表 AddComment / AfterDelete UnDelete / 同上 / AfterReject Resend / 同上 / throw → 整筆回滾 / 失敗訊息是空字串 / ⑤ 只有 CASM001／CASM002 掛 After*；M003–M006 完全沒有 / CASM001 CASM002 / 8 個 After 掛點 / CASM003 CASM006 / 只掛 3 個 Before / CASM004 CASM005 / 只掛 3 個 Before + 複製 / CASB001 繞過 EVA / 直接 UPDATE 四眼欄
```

*圖:圖 3 卡控與四眼順序。橘框=本模組寫的程式碼；黑框=框架 DLL（無原始碼，從呼叫端反推）；橘虛框=寫死值或會咬人的行為。整條鏈只要任一層 e.Cancel 或 throw，後面全部不執行。*

本章每一節的結構固定:用途 → 必填與存檔前檢核 → 四眼各階段附加動作 → 跨表更新 → 卡控總表。

**卡控結果一律分五類**,全文通用:

| 類型 | 使用者看到什麼 | 程式長相 |
|---|---|---|
| **阻擋** | 錯誤訊息,動作不執行 | `ValidateErrList.AddError(...)` 後 `e.Cancel = true`,或 `throw` |
| **警示** | 訊息視窗,按掉後照樣執行 | `MessageBox.Show(...)` 之後沒有 `e.Cancel` |
| **詢問** | 是 / 否對話框,由使用者決定 | `ShowMessage` 取回傳值再分支 |
| **過濾(無提示)** | 資料默默少了,沒有任何訊息 | SQL 裡的 `WHERE` / `JOIN` 條件 |
| **記錄不擋** | 只寫紀錄 / 寫欄位,流程不變 | `AddCommentHistory` 這類 |

### 4.1 `CASM001` — 通路經辦 / 理專維護

#### 用途(推測)

維護「銷售機構」(銀行分行、保經代)這筆主檔,以及機構底下的經辦 / 理專名單。主檔存進 `CRM003A` 並固定寫 `USAGE = '3'`;名單存進 `CAS003A`,一個機構可以有多位經辦。

推測依據:主檔欄位是「銷售機構金資」「銷售機構」「聯絡人」「決策者」「通訊地址」;明細欄位是「經辨/理專姓名」「理專等級代碼」「理專推薦產品類型」「傳送基金相關資料」。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:358-385`(新增)、`:387-396`(修改)、`:514-562`(`DoValidate`)。

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | grid 目前編輯中的列先 `Update()` | 永遠 | 記錄不擋(防資料沒寫進 DataSet) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:360-361` |
| 2 | 框架的必填 / 格式檢核 | 欄位空或格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:517` |
| 3 | 金資代碼長度 > 7 且首字非英文 → 必須是合法身分證 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:519-528` |
| 4 | 金資代碼長度 > 7 且首字是英文 → 必須是合法統編 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:529-535` |
| 5 | 主檔 EMAIL 格式 | 非空且格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:539-540` |
| 6 | 明細每列 EMAIL 格式 | 非空且格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:543-555` |
| 7 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:557-560` |
| 8 | 金資代碼不可重複 | 同一個 `ID_NO` 在 `CRM003A` 已存在(限 `USAGE = '3'`) | 阻擋(對話框,不是訊息清單) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:374-382` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:369-389` |

**第 3、4 兩條的邊界要記住:長度 ≤ 7 的金資代碼完全不檢查。**這是刻意的(金資代碼本身就是 7 碼),但也代表打錯的 7 碼不會被擋。

**第 8 條只在新增時跑。**修改時(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:387-396`)只跑 `DoValidate()`,不查重複。所以把 A 機構的金資代碼改成 B 機構的值,**不會被擋**。

**第 8 條在 DB 出錯時會靜默放行。**`IsID_NOExsits` 的 `catch` 回傳 `-1`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388`),UI 判斷式是 `if (i > 0)`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:376`),`-1` 不成立 → 當成「沒有重複」放行。

還有一個**被註解掉但外殼還在**的檢核:`ID_NODoValidate()` 這支方法留在檔案裡但內容是空的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:567-571`),呼叫點也被註解(`:363`)。讀碼的人會以為有這道檢核。

#### 刪除前的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:436-456`,三次遠端往返:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 9 | 代操客戶不可刪 | `CUST_TYPE = '9'` 且經辦所屬 `DEPT_NO <> 'X01'` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447`〔客戶特定〕 |
| 10 | 已有拜訪紀錄不可刪 | `CLS001A` 內存在同 `PR_NO` 的資料 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:448-453` |

第 9 條的兩支查詢都會在出錯時吞掉:`GetCustType` 與 `GetDeptNo` 的 `catch` 回傳空字串(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:480-484`、`:516-520`),空字串不等於 `'9'` → 放行。而且兩支都直接取 `Rows[0]` 沒有筆數檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:475`、`:511`),查無資料時會丟 `IndexOutOfRangeException`,被 `CommonExceptionBlocker` 吞掉後一樣回傳空字串。**結論:第 9 條只在一切正常時有效。**

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:398-429`。

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 11 | 至少輸入一個查詢條件 | 金資 / 機構名 / 序號 三個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:405-413` |

**第 11 條在待辦(ToDo)流程被跳過**:`if (this.EVAAction == "")` 才檢查。從待辦清單點進來時 `EVAAction` 有值,條件可以全空。

#### 四眼各階段附加動作

`CASM001_PO` 建構子一次訂 12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:42-58`):

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | do-while 取流水號 `GetPR_NO()`,撞號就重取;取到後回填到每一列明細 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77-103` |
| `BeforeSelect` | 把 `args.DbCmd` 整個換成 `BuildMasterSQLString(model, false)` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:105-117` |
| `BeforeGetMaintainData` | 主檔走 `BuildMasterSQLString`,明細走 `BuildDetailSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:119-139` |
| `BeforeGetToDoData` | 同上但 `isToDoString = true`,多接 `AppendToDoString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:141-153` |
| `AfterGetMaintainData` | 讀跳號一覽表歷史 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:569-574` |
| `AfterDelete` | 寫跳號一覽表(`EVAType.Delete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:576-584` |
| `AfterUnDelete` | 同上(`EVAType.UnDelete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:586-591` |
| `AfterVerify` | 同上(`EVAType.Verify`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:593-598` |
| `AfterApprove` | 同上(`EVAType.Approve`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:600-605` |
| `AfterApproveDelete` | 同上(`EVAType.ApproveDelete`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:611-617` |
| `AfterResend` | 同上(`EVAType.Resend`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:618-623` |
| `AfterReject` | 同上(`EVAType.Reject`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:625-630` |

七個 `After*` 的寫法完全一樣:`if (!SrNoCommentProcessor.AddCommentHistory(...)) throw new ApplicationException("")`。

**三件事要記住:**

1. **`throw` 的訊息是空字串。**使用者看到的錯誤訊息會是框架的預設文字,追不到是哪一步失敗的。

2. **每個 handler 第一行都是 `if (args.TableName != this.MasterTable.dbTableName) return;`**(例 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:571`),因為事件會對主檔 + 每個明細表各觸發一次。少寫這一行就會寫兩次紀錄。

3. **`BeforeAdd` 沒有那道防護**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77-103`)。它只在 `args.TableName == MasterTable` 時取號,但**流水號回填明細那段在 `if` 外面**(`:98-101`),所以明細表觸發時也會跑一次——重複但無害,因為值一樣。

#### 跨表更新

| 動作 | 寫哪張表 | 說明 |
|---|---|---|
| 新增 / 修改 / 刪除 | `CRM003A` + `CAS003A` | 由四眼引擎產生 SQL,程式看不到 |
| 任何四眼動作 | 跳號一覽表(表名在框架內,無原始碼) | `SrNoCommentProcessor.AddCommentHistory` |
| 匯出 Excel | **不寫** | 只讀 |

**唯讀 join 的表**:`COD006A`(兩次,取 `CUST_CLASS1` / `CUST_CLASS2` 的說明)、`COD009`(取員工姓名)。錨點 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:214-222`。

#### 匯出 Excel

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:458-506` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:524-564`。

取數條件(全部寫死在 SQL 裡):

| 條件 | 值 |
|---|---|
| 機構的 `USAGE` | `<> '1'` |
| 明細的 `EMAIL` | `TRIM(...) IS NOT NULL` |
| 明細的 `SEND_FUND_YN` | `= 'Y'` |
| 去重 | 以 `EMAIL` 分組,取 `MAX(PR_NO)` / `MAX(STAFF_NAME)` / `MAX(EMP_NO1)` |

**這是過濾(無提示)的典型**:畫面上看得到的經辦,匯出檔裡可能沒有,而且沒有任何訊息說明為什麼。三個原因都可能:沒填 EMAIL、`SEND_FUND_YN` 不是 `Y`、或同一個 EMAIL 被別列去重掉了。

還有一個會咬人的:`GetExcel()` 出錯時回傳 `null`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:558-562`),UI 拿到後**沒有判 null 就直接改欄位名稱**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:472-479`)→ `NullReferenceException`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:517` |
| 按新增前 | 身分證 / 統編格式(長度 > 7 才驗) | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:519-536` |
| 按新增前 | 主檔 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:539-540` |
| 按新增前 | 明細 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:550-551` |
| 按新增前 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:557-560` |
| 按新增前 | 金資代碼重複 | 已存在 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:374-382` |
| 按新增前 | 金資代碼重複(DB 出錯時) | `catch` 回傳 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388` |
| 按修改前 | 金資代碼重複 | — | **不檢查** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:387-396` |
| 按刪除前 | 代操客戶 | `CUST_TYPE = '9'` 且非 `X01` 部門 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447`〔客戶特定〕 |
| 按刪除前 | 已有拜訪紀錄 | `CLS001A` 有同序號 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:448-453` |
| 按查詢前 | 至少一個條件 | 三個都空且非待辦流程 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:405-413` |
| 查詢時 | 只看 `USAGE = '3'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| grid 編輯時 | 明細 PK 重複 | 同名經辦 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:642-645` |
| grid 新增列時 | 明細 PK 必填 | `STAFF_NAME` 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:647-652` |
| 修改模式 | 明細 PK 不可編輯 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:613-620` |
| 四眼任一階段 | 寫跳號一覽表失敗 | `AddCommentHistory` 回 false | 阻擋(整筆回滾,訊息空白) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` |
| 匯出 Excel | 三道 SQL 條件 + EMAIL 去重 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:533-541` |

### 4.2 `CASM002` — 客戶拜訪單維護

#### 用途(推測)

業務員填寫對銷售機構的拜訪紀錄:預計 / 實際拜訪日與方式、與談者、拜訪重點、三組追蹤事項、車資與人數;以及主管那一段的意見、溝通事項、異常狀況與回覆(存 `CLS002A`)。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:317-326`(新增)、`:328-337`(修改)、`:535-580`(`DoValidate`)。

`DoValidate()` **只有兩件事**:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架的必填 / 格式檢核 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:538` |
| 2 | 與談者 1 / 2 / 3 不可重複(忽略空白) | 有重複 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:541-552` |

**另外三段「主談者資料不存在」的檢核整段被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579`),而且第三段的複製貼上還沒改對——檢查的是 `ucMAIN_CHATER1` 卻報「主談者3資料不存在」(`:574`)。就算解開註解也是錯的。

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:339-422`,是本模組最完整的一套:

| # | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| 3 | 至少一個條件(待辦流程跳過) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:347-359` |
| 4 | 潛在客戶序號起迄要嘛都填要嘛都不填 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:363-364` |
| 5 | 潛在客戶序號起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:365-367` |
| 6 | 銷售機構金資起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:369-373` |
| 7 | 區域別起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:375-379` |
| 8 | 實際拜訪日期起迄同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:381-385` |

4–8 條全部用 `^`(互斥或)寫,而且**不受 `EVAAction` 影響**——待辦流程也會跑。條件本身沒問題,但待辦流程下所有起迄欄位都是空的,`^` 兩邊都 false 不成立,所以實務上不會擋到。

#### 自動帶值(不是卡控,但會改資料)

| 觸發 | 做什麼 | 失敗時 | 錨點 |
|---|---|---|---|
| 潛在客戶序號變更 | 查 `CRM003A` 帶出員工編號 / 金資 / 機構名 | 查無 → 三欄清空,無提示 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:583-601` |
| 金資代碼離開欄位 | 反查 `CRM003A` 帶出序號 / 員工 / 機構名 | 查無 → 三欄清空,無提示 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:642-663` |
| 與談者 1 選定 | 用該經辦的 `PR_NO` 查 `CAS003A`,帶出理專等級 / 投資特性 / 推薦類型 | 查無 → 三欄清空(訊息被註解掉了) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:665-700` |
| 實際拜訪方式 = `'2'` | 清空並鎖住往返與車資 | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:624-640` |

**三處 `pxy.GetXXX(...)` 的回傳值都沒判 null。**PO 端出錯時回傳 `null`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:444-448`),UI 直接 `.Rows.Count` → `NullReferenceException`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:592`、`:650`、`:681`)。

#### 四眼各階段附加動作

與 `CASM001` 逐行對應,連寫法都一樣:12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:42-58`),`BeforeAdd` 取 `GetCALL_RPT_NO()`(`:92`),七個 `After*` 寫跳號一覽表(`:628-682`)。

差別只有兩處:

| 面向 | `CASM001` | `CASM002` |
|---|---|---|
| 流水號 | `GetPR_NO()` | `GetCALL_RPT_NO()` |
| 多一支方法 | — | `GetReport_Data<T>`(拜訪記錄單報表),`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:522-613` |

#### 跨表更新

| 動作 | 寫哪張表 |
|---|---|
| 新增 / 修改 / 刪除 | `CLS001A` + `CLS002A`(都是〔共用〕表) |
| 四眼各階段 | 跳號一覽表 |

**明細只會有一列。**`SetMasterToDetail()` 在新增或 0 列時 `NewCLS002ARow()`,否則 `FirstOrDefault()`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:101-130`)。畫面上沒有明細 grid,那 9 個欄位是直接放在表單上的。

唯讀 join:`CRM003A`(機構名與客戶等級)、`CAS004A`(區域別)、`COD006A`(兩次)。錨點 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:217-230`。

**`CAS004A` 這個 join 值得單獨看**:

```
LEFT JOIN (SELECT CAS004A.EMP_NO, MAX(CAS004A.YYMM) YYMM
                , MIN(CAS004A.AREA_CODE) KEEP (DENSE_RANK FIRST ORDER BY CAS004A.AREA_CODE) AREA_CODE
             FROM CAS004A GROUP BY CAS004A.EMP_NO ) CAS004A
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224`。`MAX(YYMM)` 被算出來但**沒有任何地方用到**;`AREA_CODE` 取的是該員工**所有月份中最小的區域別**,不是最新月份的。名字叫 `MAX(YYMM)` 會讓人以為取的是最新一筆——不是。對照 `CASI001` 的寫法(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:141-144`)用的是 `ROW_NUMBER() OVER(PARTITION BY EMP_NO ORDER BY YYMM DESC)` 取 `RNO = 1`,**那個才是真的取最新**。同一個概念兩套實作、結果不同。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:538` |
| 按新增 / 修改前 | 與談者 1/2/3 不可重複 | 有重複 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:548-551` |
| 按新增 / 修改前 | 與談者存在性 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579` |
| 按查詢前 | 至少一個條件 | 七個都空且非待辦 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:347-359` |
| 按查詢前 | 四組起迄的成對與大小 | 只填一邊或起 > 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:363-385` |
| 查詢時 | 只看 `USAGE = '3'`(內外各一次) | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:232`、`:236` |
| 查詢時 | 區域別取全期間最小值而非最新月 | 永遠 | 過濾(無提示,值會錯) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` |
| 帶值時 | 查無資料 | 查不到機構 / 經辦 | **靜默清空**(訊息被註解) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:698` |
| 選擇拜訪方式 `'2'` | 鎖住車資欄 | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:628-634` |
| 四眼任一階段 | 寫跳號一覽表失敗 | 回 false | 阻擋(訊息空白) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:634` |
| 列印 | 查無資料 | 報表 SQL 0 筆 | 警示(對話框,不改資料) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:486-489` |

### 4.3 `CASM003` — 年度境外代銷手續費加項維護

#### 用途(推測)

替某位員工設定某個業績年度的「境外代銷手續費加項」總額(`CAS001A`),並把總額拆成 12 個月的明細(`CAS002A`)。畫面上有一顆「月分配」鈕做自動拆分。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:60-92`(`DoValidate`),按順序:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:63` |
| 2 | 起算年月必須與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:66-67` |
| 3 | 年度手續費加項 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:69-70` |
| 4 | 明細 PK 必填 | grid 有列但 PK 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:72-77` |
| 5 | 明細至少一列 | grid 0 列 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:78-81` |
| 6 | 每列月分配 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:85-86` |
| 7 | 年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:88-90` |

**第 6、7 兩條有前置條件**:`if (this.ValidateErrList.ErrorCount > 0) return;`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:83`)。前面任何一條錯了,這兩條就不跑——使用者要修兩輪才看得到全部錯誤。

另有一條在欄位離開時觸發的檢核:業績年度必須介於 1900 與今年之間(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:319-342`)。**這條實際上幾乎不會觸發**,因為它的前置是 `this.udatBOUNS_ST_YYMM.Value == null`(`:322`),而只要使用者填過起算年月就不成立。而且它用 `MessageBox.Show` 而不是 `ValidateErrList`,與整個畫面的風格不一致。

#### 「月分配」鈕的行為

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:101-173`。分兩條路:

**路徑 A(grid 已有列)**:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:120-137`。依 `QUO_YYMM` 排序逐列,前 11 列各給 `Math.Floor(總額 / 12)`,第 12 列給剩餘。

**路徑 B(grid 沒有列)**:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:138-172`。從起算月往後產 12 列,前 11 列給均分值,最後一列給剩餘。

兩個會咬人的地方:

1. **路徑 A 假設剛好 12 列。**計數器是 `j`,條件 `if (j < 12)`。列數 < 12 時每列都拿均分值,總和小於年度總額 → 存檔被第 7 條擋下,使用者只能手改。列數 > 12 時第 12 列拿到剩餘,**第 13 列以後每列都拿到同一個剩餘值**(`iOFD_INC_ALLOT_FEE_E` 在 else 分支裡沒有再扣),總和暴增。

2. **路徑 B 跨年時月份格式會壞。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151`: `` else if (iQUO_Month > 12) MRow.QUO_YYMM = Convert.ToString(Convert.ToInt16(umskQUO_YEAR.Value) + 1) + "0" + Convert.ToString(iQUO_Month - 12);`` 補零是寫死的 `"0" +`,沒有判斷位數。起算月 = 11 月時,第 11 列的 `iQUO_Month` 是 21 → `21 - 12 = 9` → `"09"`,還好;起算月 = 12 月時第 11 列 `iQUO_Month = 22` → `22 - 12 = 10` → `"0" + "10"` = `"010"`,**`QUO_YYMM` 變成 7 碼**(如 `2026010`)。而 xsd 宣告 `maxLength = 6`(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM003Model.xsd:131-137`),DataSet 層就會丟例外。 **但第 2 條檢核(起算年月必須與業績年度同年)沒有限制月份**,所以起算月選 12 月是允許的。這條路走得到。

#### 四眼各階段附加動作

**沒有。**`CASM003_PO` 只掛 3 個 `Before*`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:30-32`),沒有任何 `After*`,也沒有 `BeforeAdd`——PK 由使用者輸入,不需要取號。

#### 跨表更新

只寫 `CAS001A` + `CAS002A`。唯讀 join 只有一個 `COD009`,而且是 **`JOIN` 不是 `LEFT JOIN`**:

```
FROM CAS001A JOIN COD009 ON COD009.EMP_NO = CAS001A.EMP_NO
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121`。**員工在 `COD009` 找不到時,這筆業績目標整筆從查詢結果消失,沒有任何提示。**對照 `CASM006` 用的是一樣的 inner join(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:124-126`),而 `CASM004` / `CASM005` 用 `LEFT JOIN`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:373-374`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:297-298`)。**同一件事四支畫面兩種寫法。**

#### 查詢條件的組法

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:127-185`。業績年度與員工代碼都是起迄:

| 參數 | 產生的條件 |
|---|---|
| `QUO_YEAR` | `>= 值` |
| `QUO_YEAR1` | `<= 值`;**沒傳時退回用 `QUO_YEAR` 當上界** |
| `EMP_NO` | `>= 值` |
| `EMP_NO1` | `<= 值`;同樣有退回邏輯 |

退回邏輯的效果是:**只填「起」不填「迄」時,查詢會變成等於**。UI 端已經先幫使用者把「迄」補成「起」了(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:305-315`),所以兩層都在做同一件事。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:219-220` |
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:63` |
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:66-67` |
| 按新增 / 修改前 | 年度總額 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:69-70` |
| 按新增 / 修改前 | 明細至少一列、PK 必填 | 0 列或 PK 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:72-81` |
| 按新增 / 修改前 | 每列 > 0、總和相符 | 不符 | 阻擋(但前面有錯就不跑) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:83-90` |
| 年度欄離開時 | 年度介於 1900~今年 | 只在起算年月為空時判 | 警示改阻擋(`MessageBox` + `e.Cancel`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:319-342` |
| 按查詢前 | 年度 / 員工起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:245-255` |
| 查詢時 | 員工不在 `COD009` → 整筆消失 | 永遠 | **過濾(無提示)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121` |
| 按月分配 | 明細列數不是 12 | 列數 ≠ 12 | 記錄不擋(金額會錯,之後被第 7 條擋) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:120-137` |
| 按月分配 | 起算月 = 12 月 | 跨年月份 ≥ 10 | 記錄不擋(產生 7 碼年月 → 之後丟例外) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151` |
| 修改模式 | 起算年月不可改 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:214` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs` 無 `BeforeDeleteButtonClicked` |

### 4.4 `CASM004` — 銷售機構業務員分配比率維護

#### 用途(推測)

設定某個業績年月、某個銷售機構(區別碼 + 代碼)、某位業務員的分配比率。四個欄位合起來是 PK,同一組機構下多位業務員的比率加總不得超過 100%。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:35-53`(`DoValidate`),只有三件事:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:38` |
| 2 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:40-41` |
| 3 | 同年月 + 機構區別碼 + 機構代碼 的加總比率(排除本人)+ 本次輸入 ≤ 100 | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:49-52` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:273-296` |

第 3 條的 SQL 值得看清楚:

```
SELECT CASE WHEN SUM(DIV_PCT) + To_number('<新值>') > 100 THEN 1 ELSE 0 END
  FROM CAS004A WHERE YYMM = ... AND AGENT_ID = ... AND AGENT_CODE = ... AND EMP_NO <> ...
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:277-282`。三個要注意的:

1. **不分狀態全算。**還在送審中、已退回、甚至邏輯刪除的資料都算在 `SUM` 裡(沒有 `STATUS` 條件)。

2. **同一組合下沒有其他人時 `SUM` 是 NULL**,`NULL + x > 100` 是 unknown,`CASE` 走 `ELSE 0` → 放行。行為正確,但是靠 Oracle 的三值邏輯,不是靠程式。

3. **`catch` 回傳 `-1`**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:291-295`),UI 判 `if (i > 0)` → DB 出錯時**靜默放行**。與 `CASM001` 的第 8 條同一個模式。

另有一條在欄位離開時觸發:分配比率不可為 0(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328`),用 `MessageBox` + `e.Cancel`,與 `DoValidate` 的第 2 條重複但訊息不同(一個說「必須大於 0」,一個說「應介於0.01和100.00之間」)。

#### 查詢條件的檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:227-270`:

| # | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| 4 | 業績年月起迄**必填**(不是擇一) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:231-232` |
| 5 | 業績年月起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:233-235` |
| 6 | 機構區別碼起迄成對 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:237-238` |
| 7 | 機構區別碼起 = 迄(不是範圍!) | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:239-240` |
| 8 | 機構代碼起迄成對且起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:242-246` |

**第 7 條把「區別碼」的起迄降級成單值**,而且 PO 端真的只送一個參數(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:260-263`,「迄」那行是註解掉的)。畫面上擺兩個欄位卻只能填一樣的值,是留下來沒清乾淨的 UI。

#### 業務員下拉的兩層過濾

| 層 | 條件 | 錨點 |
|---|---|---|
| `FormInitial` 設 `Filter` | `(DEPT_NO <> 'G17') AND (LEAVE_DATE >= '<今年>/01/01' OR LEAVE_DATE IS NULL)` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159`〔客戶特定〕 |
| `BeforeGetDataSource` | **整段被註解**(原本要排除 `G3` / `GA` / `G12` / `G13`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:310-316` |

註解裡留了一句「2015/12/25 改為代銷部門可修改」,說明這是刻意放寬的。但**放寬後只剩 `G17` 一個排除條件,而 `G17` 又是 `CASM005` 明確要納入的部門**(§4.5),兩支畫面的部門規則互相矛盾。

#### 「業務員複製」彈出視窗

`CASM004p0`,由主畫面的 `DoExp1()` 開啟(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:114-139`)。修改模式下會把目前這筆的年月 / 區別碼 / 機構代碼 / 業務員當預設值帶進去(`:121-136`)。

複製的檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:63-121`):

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 9 | 框架必填 / 格式 | — | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:66` |
| 10 | 來源業務員在該月份 / 機構有資料 | `GetEmpAgentStartDate` 回空字串 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:97-99` |
| 11 | 目標業務員不可為空 | 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:114-115` |
| 12 | 年月起 ≤ 迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-70` |
| 13 | 來源與目標業務員不可相同 | — | **被註解**(註記「2016.07.29改為不判斷」) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:74-76` |
| 14 | 來源 / 目標業務員存在性 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:103-112` |
| 15 | 複製後比率不超過 100% | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:116-118` |

**七條檢核裡四條被註解。**其中第 15 條有替代路徑:SP 跑完後會回一張 `CAS004A_OVER` 結果集,列出超過 100% 的機構,由 `CheckOverDivPct` 轉成錯誤訊息(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:54-60`)。也就是**事前不擋、事後才報**——但那時候 SP 已經 commit 了(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:117`)。

**第 10 條的回傳值有個陷阱**:`GetEmpAgentStartDate` 在 `catch` 裡 `return ex.Message;`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231`)。DB 出錯時回傳的是例外訊息字串,`string.IsNullOrWhiteSpace` 為 false → **當成「有資料」放行**。把例外訊息當成業務資料回傳,是本模組最危險的一個寫法。

#### 跨表更新

| 動作 | 寫哪張表 | 怎麼寫 |
|---|---|---|
| 新增 / 修改 / 刪除 | `CAS004A` | 四眼引擎 |
| 複製 | `CAS004A` | **`S_TA_CASM004_P01`**,自行 `BeginTransaction` 並 `Commit`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:94-118`) |

**複製完全繞過四眼引擎。**SP 內做了什麼(新資料的 `STATUS` 是什麼、四眼欄位怎麼填)在 repo 內看不到。SP 的參數有 8 個,包含 `iUSER_ID`,**推測**是 SP 自己填四眼欄位(依據是參數裡有使用者代號,而程式端沒有任何地方設四眼欄位)。

`cmd.CommandTimeout = 0`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:99`),永不逾時。

錯誤處理有一條特判:Oracle 的 `ORA-00001`(唯一鍵衝突)會被翻成「執行失敗,已建立資料,無法複製」(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:126-127`),其餘例外原樣把 `ex.Message` 塞進訊息回給前端(`:130`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:38` |
| 按新增 / 修改前 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:40-41` |
| 按新增 / 修改前 | 同機構加總 ≤ 100% | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:49-52` |
| 按新增 / 修改前 | 同機構加總(DB 出錯時) | `catch` 回 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:291-295` |
| 比率欄離開時 | 不可為 0 | `== 0` | 阻擋(`MessageBox`) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328` |
| 按查詢前 | 業績年月起迄必填 | 兩個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:231-232` |
| 按查詢前 | 機構區別碼起 = 迄 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:239-240` |
| 下拉業務員 | 排除 `G17` 部門、排除去年以前離職 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` |
| 複製前 | 來源業務員該月有資料 | 回空字串 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:97-99` |
| 複製前 | 來源業務員該月有資料(DB 出錯時) | 回傳 `ex.Message` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231` |
| 複製前 | 目標業務員不可為空 | 空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:114-115` |
| 複製前 | 年月大小、業務員相同、存在性、比率上限 | — | **四條全被註解** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-118` |
| 複製後 | 比率超過 100% 的機構清單 | SP 回傳有列 | 警示(資料已寫入) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:54-60` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs` 無 `BeforeDeleteButtonClicked` |

### 4.5 `CASM005` — 受益人層分配比率維護

#### 用途(推測)

與 `CASM004` 同一件事,但多一個維度:受益人戶號。也就是「這個受益人在這個機構的業績,要怎麼分給業務員」。PK 從 4 欄變 5 欄。

#### 與 `CASM004` 的差異

| 面向 | `CASM004` | `CASM005` |
|---|---|---|
| PK | 4 欄 | 5 欄(多 `BF_NO`) |
| 複製實作 | SP `S_TA_CASM004_P01` | **程式內逐列 `AddM`**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:81-148`) |
| 查詢預設值 | 無 | 機構區別碼固定 `"0"`、機構代碼固定 `"A0901"`,而且設成 `ReadOnly`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81`)〔客戶特定〕 |
| 業務員下拉 | 排除 `G17` | **同時**設 `DEPT_NO <> 'G17'` 與 `DEPT_NO IN ('G3','GA','G12','G13','G17')` |
| 機構名稱來源欄 | `AGENT_SHNM` | `AGENT_NAME` |
| 複製時的存在性檢核 | 被註解 | **還活著** |

**「查詢條件寫死成單一機構」這件事要特別注意。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81` 把起迄兩組都設成 `"0"` + `"A0901"` 並鎖成唯讀,代表**這支畫面實務上只服務一個銷售機構**。換站台一定要改。

**業務員下拉的兩條規則互相打架**:

| 來源 | 條件 | 錨點 |
|---|---|---|
| `FormInitial` 的 `Filter` | `DEPT_NO <> 'G17'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:87-89`〔客戶特定〕 |
| `BeforeGetDataSource` 加的參數 | `DEPT_NO IN ('G3','GA','G12','G13','G17')` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:240-247`〔客戶特定〕 |

兩條同時送到同一個資料來源。**`G17` 一邊排除一邊納入**,最終行為取決於框架怎麼合併 `Filter` 與 `ConditionVDB`(無原始碼,從呼叫端反推)。**假設**:`Filter` 是用戶端 DataView 的過濾,`ConditionVDB` 是伺服端 SQL 的條件,所以 `G17` 會先被 SQL 撈回來再被 DataView 濾掉,淨效果等於排除。依據是兩者的參數形態不同(一個是 DataTable 的 `Filter` 字串,一個是走 `AddParametersRow`)。這條要現場確認。

#### 複製的實作差異

`CASM005` 走的是舊世代的程式內複製(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:81-148`):

1. 先 `GetMaintainData` 把來源資料撈進 Model(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:68`)

2. 逐列把 `EMP_NO` 換成目標業務員,並把四眼欄位全部清空 / 設成 `1900/01/01`(`:92-109`)

3. 逐列呼叫 `AddM` 寫入(`:110-114`)

4. 兩個交易(業務庫 + 平台庫)一起 commit(`:117-123`)

**第 2 步是本模組唯一直接寫四眼欄位的地方**(除了 `CASB001`)。`row.STATUS = row.STATUS;` 這一行(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96`)是自我賦值,等於什麼都沒做——**複製出來的新資料會帶著來源的狀態**,而不是回到「新輸入待驗證」。

對照 `CASM004` 的 SP 版,同一段邏輯在 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:135-190` **整段被註解保留**,可以逐行對照兩代寫法。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:38` |
| 按新增 / 修改前 | 分配比率 > 0 | `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:40-41` |
| 按新增 / 修改前 | 同年月+機構+**戶號** 加總 ≤ 100% | `> 100` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:49-52` 配 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:195-218` |
| 按新增 / 修改前 | 同上(DB 出錯時) | `catch` 回 `-1` | **靜默放行** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:213-217` |
| 按查詢前 | 業績年月起迄必填且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:174-178` |
| 按查詢前 | 機構區別碼起 = 迄 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:181-183` |
| 按查詢前 | 機構代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:186-189` |
| 進入畫面 | 機構固定為 `A0901` 且不可改 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81` |
| 下拉業務員 | 兩條互相矛盾的部門規則 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:87-89` 與 `:240-247` |
| 複製前 | 來源與目標業務員不可相同 | 相同 | 阻擋(**這支還活著**) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:65` |
| 複製前 | 來源業務員存在 | 回 `0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:84-88` |
| 複製前 | 目標業務員資料已存在 | 回 `> 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:89-93` |
| 複製前 | 檢核失敗(DB 出錯) | 回 `-1` | 阻擋(**有判 `-1`,比 `CASM004` 嚴謹**) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:85-86`、`:90-91` |
| 複製後 | 比率超過 100% 的清單 | SP 回傳有列 | 警示(資料已寫入) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:43-49` |
| 複製時 | 新資料沿用來源狀態 | 永遠 | 記錄不擋(四眼狀態不重置) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs` 無 `BeforeDeleteButtonClicked` |

### 4.6 `CASM006` — 年度業績目標維護

#### 用途(推測)

與 `CASM003` 結構完全平行,但管的是另外六個指標:營業收入、定期(不)定額戶數-目標 / -保守、定期(不)定額扣款成功金額、新開百萬戶數、單筆申購交易百萬戶數。年度總額存 `DSM001A`,月分配存 `DSM002A`。

#### 必填與存檔前檢核

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:68-146`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:71` |
| 2 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:74-75` |
| 3 | 總營業收入 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78` |
| 4 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:90-99` |
| 5 | 每列營業收入 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:103-104` |
| 6–11 | **六個指標**各自的年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:122-144` |

**另外五個指標的「必須大於 0」檢核全部被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88` 與 `:106-119`)。也就是說:**六個指標裡只有「營業收入」不能是 0,其餘五個可以是 0 甚至負數**,但六個都必須總和相符。這個組合允許「年度目標 0、每月目標 0」通過。

#### 「月分配」鈕與 `CASM003` 的關鍵差異

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:155-276`。

| 面向 | `CASM003` | `CASM006` |
|---|---|---|
| 可分配月數 | 固定 12 | `13 - 起算月`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`) |
| 新建列時的餘數處理 | 最後一列給剩餘 | **每列都給均分值,剩餘從不寫回** |
| 跨年 | 會發生(月份可到 23) | 不會(月數已經限制在年內) |

第二列是實質缺陷:`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:233-257` 的迴圈把 `iQUO_MGR` 這類均分值寫進每一列,原本要補剩餘的那段(`:259-274`)**整段被註解掉**。所以只要年度總額不能被月數整除,第一次按「月分配」產出的明細總和就一定小於年度總額 → 存檔被第 6–11 條擋下 → 使用者必須手動改最後一列。

`CASM003` 的同一段是活的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:160-171`),所以兩支畫面的「月分配」按下去結果不一樣。

#### 查詢條件

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:349-385`,只有兩條檢核(員工代碼起迄成對、起 ≤ 迄),業績年月的起迄檢核**整段被註解**(`:353-357`)。

**而且 `QueryVDB.Util.Parameters.Clear()` 也被註解掉了**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370`、`:373`)。其餘五支 M 畫面都有清這一行(例 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:197`),只有 `CASM006` 沒有。參數集合以欄位名為鍵,同一個鍵加第二次的行為由框架決定(無原始碼)——**假設**會丟重複鍵例外或直接覆蓋,依據是它背後是 typed DataSet 的 `Rows.Find(name)`。實務上的表現是「連按兩次查詢可能失敗或條件沒換」,要現場確認。

#### 跨表更新與部門白名單

只寫 `DSM001A` + `DSM002A`。查詢時 join `COD009`(inner join,同 `CASM003` 的過濾問題),而且**主檔 SQL 尾巴寫死一串部門白名單**:

```
AND COD009.DEPT_NO IN('G3','GA','G11','G12','G13','G14','Z2','G17') ORDER BY ...
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210`〔客戶特定〕。上一行的註解寫「20180103 modify by jye 9000006164_ATLAS系統權限調整 G17=GA, G16=GB」(`:209`),說明這串是隨組織調整手動維護的。

**這一條是 `CASM006` 與 `DSMM001` 最大的行為差異**:同樣兩張表,`CASM006` 只看得到這 8 個部門的員工,`DSMM001` 沒有這個限制(§8)。**明細 SQL 沒有這個條件**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:224-273`),所以只要拿得到主檔,明細一定拿得到。

#### 離職員工的處理

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463`:選到已離職的員工時跳 `MessageBox` 說「此員工已離職!」,**但沒有 `e.Cancel`,照樣可以繼續設定他的業績目標**。這是「警示」類的標準例子。對照 `CASM004` / `CASM005` 是直接在下拉的 `Filter` 裡排除離職者(過濾,無提示)——**同一件事三支畫面兩種處理方式**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:327-328` |
| 按新增 / 修改前 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:71` |
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:74-75` |
| 按新增 / 修改前 | 總營業收入 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78` |
| 按新增 / 修改前 | 其餘五個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88` |
| 按新增 / 修改前 | 明細至少一列、PK 必填 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:90-99` |
| 按新增 / 修改前 | 每列營業收入 > 0 | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:103-104` |
| 按新增 / 修改前 | 其餘五個指標每列 > 0 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:106-119` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:122-144` |
| 按查詢前 | 員工代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:358-362` |
| 按查詢前 | 業績年月起迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:353-357` |
| 按查詢前 | 清空上次的查詢參數 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370` |
| 查詢時 | 只看 8 個部門的員工 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` |
| 查詢時 | 員工不在 `COD009` → 整筆消失 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:124-126` |
| 選擇員工時 | 已離職 | `LEAVE_DATE` 非空 | **警示(不擋)** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` |
| 按月分配 | 餘數不寫回最後一列 | 總額不能整除 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:259-274` |
| 修改模式 | 起算年月不可改 | 永遠 | 記錄不擋(鎖 UI) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:322` |
| 刪除 | **完全沒有檢核** | — | — | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs` 無 `BeforeDeleteButtonClicked` |

## 5. 查詢畫面(I)

本模組只有一支:`CASI001`「代銷客戶拜訪記錄查詢作業」。單頁(`TabPages = 1`)、唯讀、不走四眼。

### 5.1 結構

| 層 | 特徵 | 錨點 |
|---|---|---|
| UI | `xOneStepProcessForm`;grid 用 `GridLayoutUpdateOnly`(不可編修) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:32-48` |
| Ctl | **只覆寫 `InitializeDataAccessPool()`**,沒有 `InitializeVDBTypes()`;143 行裡約 40 行是註解掉的外殼 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:26-29` |
| PO | 不繼承任何基底,自己 `new` 兩條 `Database`(業務庫 `"TA"` + 平台庫 `"SWProduct"`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:33-36` |

`architecture.md §6.3` / `§6.4` 已經記過這個樣板與 `CASB001` 是同一份複製刪減出來的。**本節只記 CAS 特有的行為。**

### 5.2 查詢條件

UI 端的 `ProcessQueryCondition`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:55-194`)送出的參數:

| 參數 | 來源欄位 | PO 端產生的條件 | PO 錨點 |
|---|---|---|---|
| `QUERY_EMP_NO` | **登入者的員工代號**(不是畫面欄位) | `AND COD009.EMP_NO = '值'`,但白名單內的 5 人跳過 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:198-209` |
| `CALL_RPT_NO_BGN` / `_END` | 客戶拜訪單號起 / 迄 | `>= 值` / `<= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:213-232` |
| `PR_NO_BGN` / `_END` | 潛在客戶序號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:235-253` |
| `EMP_NO_BGN` / `_END` | 員工代號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:256-274` |
| `BF_NO_BGN` / `_END` | 受益人戶號起 / 迄 | 同上 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:277-295` |
| `ID_NO_BGN` | 銷售機構金資 | **`= 值`(不是 `>=`)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:301-309` |
| `ACT_CALL_DATE_BGN` / `_END` | 實際拜訪日期起 / 迄 | `>= '值'` / `<= '值'`(字串比較) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:323-351` |
| `CALL_TYPE2` | 實際拜訪方式 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:354-362` |
| `TOPIC_CODE` | 拜訪重點 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:364-372` |
| `TRACE_CODE` | 追蹤事項 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:375-383` |
| `INVEST_CODE` | 投資特性 | `= 值` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:385-393` |

UI 端的檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:69-125`):五組起迄,每組三條規則——只填「起」就自動補「迄」、只填「迄」則阻擋、起 > 迄則阻擋。銷售機構金資那一組**整段被註解掉**(`:101-107`),所以畫面上只剩一個欄位有效。

**沒有「至少填一個條件」的檢核。**全部留空按查詢,會撈出該登入者的所有拜訪紀錄。

### 5.3 哪些條件會靜默濾掉資料

這一節是本章重點。`CASI001` 有 **6 個不會提示的過濾**:

#### (1) `USAGE = '3'` 硬條件

```
WHERE 1=1 AND CLS001A.USAGE = '3'
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:185-186`。非 `'3'` 的拜訪單在這支畫面**永遠查不到**,畫面上也沒有任何欄位可以改這個條件。`CASM002` 有同樣的限制(而且是內外各一次),但 `CASB001` 沒有——**同一批資料,三支畫面的可見範圍不同**。

#### (2) 登入者員工代號的強制條件

```
if (iQUERY_EMP_NO != "028039" && iQUERY_EMP_NO != "102736" && iQUERY_EMP_NO != "103771"
    && iQUERY_EMP_NO != "850094" && iQUERY_EMP_NO != "990667")
    strSQL += " AND COD009.EMP_NO = '" + Row.Value + "'";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207`〔客戶特定〕。

**這是全模組唯一一處把權限寫在程式裡的地方**,而且是寫死的 5 個員工代號。要點:

| 面向 | 內容 |
|---|---|
| 效果 | 白名單內的人看得到全部;其餘人只看得到自己的 |
| 維護方式 | 改 code、重編 `PO.CAS`、重新部署 |
| 沒有的東西 | 沒有設定檔、沒有資料表、沒有註解說明這 5 個人是誰 |
| **反向風險** | 取不到員工代號時 `QUERY_EMP_NO` 這個參數根本不會被加(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136`),PO 端的 `if` 不成立 → **條件完全不加 → 看到所有人的資料** |

反向風險那條要展開講。UI 端:

```
ClientBizUtility biz = new ClientBizUtility();
string data = biz.GetEMP_INFO(this.UserID);
string[] words = data.Split(',');
if (words != null && words.Length > 1 && words[1] != "")
    this.QueryVDB.Util.Parameters.AddParametersRow("QUERY_EMP_NO", ...);
```

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136`。`ClientBizUtility`(無原始碼,從呼叫端反推)回傳一串逗號分隔字串,取第 2 段當員工代號。**只要這一段是空的——使用者沒有對應的員工資料、回傳格式改了、服務出錯回空字串——參數就不會被加,而 PO 端沒有「參數不存在就擋下」的分支。**結果是唯讀畫面的資料範圍從「自己」放大到「全部」,而且無聲無息。

#### (3) 起迄比較符號中間有空白

```
strSQL += " AND CLS001A.CALL_RPT_NO > = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219`,同樣寫法出現在 `:230`、`:241`、`:251`、`:262`、`:272`、`:283`、`:293` 共 8 處。

SQL 的 `>=` 是單一 token,中間不能有空白。**假設**:這 8 個條件只要有一個被加進去,整段 SQL 就會在 Oracle 端語法錯誤,被 `catch` 吞成「執行失敗,請檢查」(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:433-438`)。依據是 SQL 標準與 Oracle 的詞法規則;**無法在本機驗證**,要連 DB 才能確認。

這個寫法在全庫只出現在 4 個檔:`CASI001_PO`、`CASB001_PO`、`CLSI001_PO`、`CRMI001_PO`——全部是同一份查詢樣板的後代。如果這些畫面在正式環境是能用的,那代表 Oracle 或 ODP.NET 有容忍這種寫法的行為,**本文的假設就要推翻**。無論哪一邊為真,這 8 處都該修。

#### (4) 實際拜訪日期是字串比較

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` 直接把日期當字串比:`AND CLS001A.ACT_CALL_DATE >= '<值>'`。`ACT_CALL_DATE` 在 xsd 裡是 `xs:string`,存的是 `yyyyMMdd`(從 `DateTimeHelper.DateToString` 推,`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:64`),字串比較剛好等價於日期比較。**但只要有一筆資料存成別的格式(補空白、含分隔符號、空字串),它就會落在區間外而不被查到。**對照 `CASB001` 對同一個欄位用的是 `to_date(NVL(TRIM(...), '19000101'), ...)`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147`)——**同一個欄位,兩支畫面兩種比法。**

#### (5) `CLS002A` 的 `LEFT JOIN` 是對的,但 `CTL014` 那個不是

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:147-151`:

```
LEFT JOIN CLS002A ON CLS001A.CALL_RPT_NO = CLS002A.CALL_RPT_NO
LEFT JOIN CTL014  ON CLS001A.CALL_TYPE2 = CTL014.TEXTVALUE AND CTL014.SOURCETYPE = '447'
```

兩個都是 `LEFT JOIN`,不會濾掉主檔。**但 `CLS002A` 的 PK 是 `CALL_RPT_NO`,理論上 1:1;如果資料庫實際允許一單多列,這個 join 會讓拜訪單重複出現。**xsd 的 PK 宣告只約束 DataSet,不保證 DB(`architecture.md §5.5`)。

#### (6) 代碼說明 join 的分類碼寫死

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` 共 10 個 `COD006A` join,分類碼寫死成 `'P1'` / `'P3'` / `'20'`。分類碼一旦在 `COD006A` 改動,說明欄會整片變空——而且因為是 `LEFT JOIN`,主檔還在,只是說明是空的。**使用者看到的是「代碼有值但說明空白」,不會意識到是設定問題。**

### 5.4 取數之後做的事

PO 在 `LoadDataSet` 之前塞了一整排 `DefaultValue`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406-418`),包括 `STATUS = "301"`、四眼的 ID 欄全部設成當前使用者、日期欄設成當下。

**這對唯讀查詢沒有意義**——這些是 DataColumn 的預設值,只在「新增一列而沒給值」時生效,而查詢不會新增列。它是從 `CASB001` 那份樣板複製過來的(`CASB001` 確實會新增列),留在這裡是死碼。但它同時也是 §2.5 判定 `STATUS` 是 3 碼字串的證據之一。

查無資料時回 `AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:424-427`)。

### 5.5 兩支不在介面上的方法

`GetEmpNo` 與 `GetUidCode` 是 `public` 但**不在 `ICASI001_PO` 介面裡**(介面宣告被註解,`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:25-27`)。Ctl 走 `GetDaoInstance<ICASI001_PO>()` 取實例(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASI001_Ctl.cs:39`),拿到的是介面型別,**呼叫不到這兩支**。它們是死碼。

`GetEmpNo` 還有一個潛在例外:直接取 `Rows[0]` 沒有筆數檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:469`),對照 `CASB001` 的同名方法有檢查(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:408`)——同一份樣板,一支修過一支沒修。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 四組起迄只填「迄」 | 起空迄有值 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:71-72`、`:79-80`、`:87-88`、`:95-96` |
| 按查詢前 | 四組起迄的起 > 迄 | 不符 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:73-75`、`:81-83`、`:89-91`、`:97-99` |
| 按查詢前 | 實際拜訪日期起迄 | 同上 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:110-116` |
| 按查詢前 | 銷售機構金資起迄 | — | **被註解,不執行** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:101-107` |
| 按查詢前 | 至少填一個條件 | — | **沒有這條檢核** | — |
| 查詢時 | `USAGE = '3'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:186` |
| 查詢時 | 只看自己的資料(5 人除外) | 取得到員工代號時 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| 查詢時 | 取不到員工代號 | `GetEMP_INFO` 回空 | **靜默放大到全部資料** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136` |
| 查詢時 | 代碼說明的分類碼寫死 | 分類碼改動 | 過濾(無提示,說明變空) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 查詢時 | 日期用字串比較 | 資料格式不一致 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` |
| 查詢時 | SQL 語法錯(`> =`) | 有帶任一起迄條件 | **假設**整個查詢失敗,訊息「執行失敗,請檢查」 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219` |
| 查詢後 | 0 筆 | 無資料 | 警示 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:424-427` |

## 6. 批次(B)與 WindowsService

本模組只有一支 `CASB001`「代銷組客戶拜訪主管明細表」,**沒有 WindowsService**。

### 6.1 觸發

使用者在畫面上按「執行」鈕。流程是:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 按「查詢」撈出拜訪單清單到 grid | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:66-127` |
| 2 | 逐列勾 `ISCHECK`,或按「全選」/「全不選」 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:245-270` |
| 3 | 雙擊已勾選的列 → 開 `CASB001p0` 編輯主管意見等欄位 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:205-224` |
| 4 | 按「執行」→ `DoExecute` → PO 的 `ExecuteNonQuery` | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASB001_Ctl.cs:45-51` |
| 5 | 執行成功後逐列寄信 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342` |

第 3 步的雙擊有個守門:**沒勾 `ISCHECK` 的列雙擊沒反應**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212`),而且判斷用的欄位名是 `"IsCheck"`(大小寫與其他地方的 `"ISCHECK"` 不同)。Infragistics 的 `Cells[...]` 索引不分大小寫,所以能用,但不一致。

### 6.2 輸入(查詢條件)

| 參數 | PO 端條件 | 錨點 |
|---|---|---|
| `ACT_CALL_DATE_BGN` / `_END` | `to_date(NVL(TRIM(ACT_CALL_DATE),'19000101'),'yyyy-MM-dd') >= to_date(' <值前 10 碼> ','yyyy-MM-dd')` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147`、`:163` |
| `EMP_NO` | `= 值`(值先 `Replace("'","")`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:178` |
| `PR_NAME` | `CRM003A.PR_NAME = 值`(UI 端先把 `'` 換成 `''`) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:188` |
| `AREA_CODE` | **`CRM003A.AREA_CODE = 值`** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:199` |
| `CFM_USER` | `'Y'` → `CFM_USER1 = 'Y' OR CFM_USER2 = 'Y'`;否則 → `CFM_USER1 <> 'Y' AND CFM_USER2 <> 'Y'` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:203-216` |

UI 端只有兩條檢核(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:71-127`、`:229-237`):

| # | 檢核 | 結果 |
|---|---|---|
| 1 | 實際拜訪日期 / 業務員工編號 / 銷售機構關鍵字 必擇一 | 阻擋 |
| 2 | 實際拜訪日期起 ≤ 迄 | 阻擋 |

**三個會咬人的查詢問題:**

1. **「未閱」查不到真正的未閱。**`CFM_USER1 <> 'Y' AND CFM_USER2 <> 'Y'` 在 Oracle 裡碰到 NULL 會得到 unknown,整列被濾掉。而**從沒被主管碰過的拜訪單,這兩欄本來就是 NULL**。所以「未閱」這個預設查詢條件(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:42`、`:60`)**撈不到全新的拜訪單**,只撈得到曾經被寫過非 `'Y'` 值的那些。這是本模組最會咬人的過濾。

2. **`PR_NAME` 是等於不是 like。**UI 的欄位標籤叫「銷售機構關鍵字」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:84` 的訊息文字),但 SQL 是 `=`。使用者按「關鍵字」的習慣輸入會查不到東西。

3. **`AREA_CODE` 取自 `CRM003A` 而不是 `CAS004A`。**`CASM002` 與 `CASI001` 的區域別都是從 `CAS004A`(業務員的機構分配)推出來的,`CASB001` 直接用機構主檔上的欄位。**三支畫面的「區域別」語意不同**,篩選結果不會一致。

另外,**`CASB001` 的查詢沒有 `USAGE` 條件**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:134` 的 `WHERE 1=1` 後面沒有接),所以它看得到 `CASM002` / `CASI001` 看不到的資料。

### 6.3 寫哪些表

**只寫 `CLS002A` 一張表**,用一段固定的 `UPDATE`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:302-323`),逐列跑(`:330-358`)。

被更新的欄位分兩類:

| 類 | 欄位 | 值的來源 |
|---|---|---|
| 業務欄(5 個) | `MGR_DESC` `CFM_USER1` `CFM_USER2` `CONNECT_DESC` `CONNECT_RE` | grid 那一列的值 |
| **四眼欄(13 個)** | `STATUS` `CREATEID` `CREATEDATE` `ENTRYID` `ENTRYDATE` `UPDATEID` `UPDATEDATE` `VERIFYID` `VERIFYDATE` `APPROVEID` `APPROVEDATE` `REJECTID` `REJECTDATE` | **全部由程式直接指定** |

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354`。四眼欄的值:

| 欄位 | 值 |
|---|---|
| `STATUS` | `"301"` |
| `CREATEID` `ENTRYID` `UPDATEID` `VERIFYID` `APPROVEID` | **當前操作者** |
| `CREATEDATE` `ENTRYDATE` `UPDATEDATE` `VERIFYDATE` `APPROVEDATE` | **當下時間** |
| `REJECTID` | `" "`(一個空白) |
| `REJECTDATE` | `1900/01/01` |

**這是本模組最嚴重的治理問題,三層:**

1. **繞過四眼引擎。**一個人按下按鈕,`VERIFYID` 與 `APPROVEID` 同時變成他自己——四眼的「輸入 / 驗證 / 覆核要三個階段」在這裡完全失效。

2. **蓋掉建檔軌跡。**`CREATEID` / `CREATEDATE` 被改成執行批次的人與時間,原本誰建的、何時建的**永久遺失**。

3. **`CLS002A` 是 CLS 模組的表。**CLS 自己的畫面如果依賴四眼狀態機,會看到不符流程的資料(§8)。

`CLS001A`(主檔)**完全不動**,所以主檔與明細的四眼狀態會從此不一致。

### 6.4 寫入實作的四個問題

```
i = dbTA.ExecuteNonQuery(cmd, tran);
i = 1;
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356`。

| # | 問題 | 後果 |
|---|---|---|
| 1 | 實際影響筆數被丟掉,硬設成 `1` | 更新 0 筆(單號不存在於 `CLS002A`)也視為成功 |
| 2 | `if (i > 0) tran.Commit();`(`:359-362`) | **一列都沒勾時 `i` 是 0,既不 commit 也不 rollback**,交易在 `finally` 被 `Dispose`(`:384`),靠 Oracle 隱含回滾 |
| 3 | 成功路徑從不 `AddResultRow` | `model.Utility.Result` 只有失敗時才有列 |
| 4 | 綁定變數寫成 `: STATUS`(冒號後有空白) | 見下 |

第 3 點的連鎖效應在 UI:寄信那段的前置條件是 `this.ProcessVDB.Util.Result.Rows.Count > 0 && this.ProcessVDB.Util.Result[0].ReturnCode`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:315`)。PO 成功時沒塞任何結果列,所以**這個條件能不能成立,完全取決於框架的 `ExecPOActionToViewVDB` 有沒有補一列**(無原始碼,從呼叫端反推)。**假設**:框架會補,依據是若不補則本功能的寄信從來沒運作過,而郵件主旨與內容寫得很完整不像沒用過。這條要現場確認。

第 4 點:`UPDATE` 語句裡 13 個綁定變數寫成 `STATUS = : STATUS`、`WHERE CALL_RPT_NO =: CALL_RPT_NO`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:309-323`),冒號與名稱中間有空白,而前 5 個業務欄寫的是正常的 `:MGR_DESC`(`:304-308`)。同一段 SQL 兩種寫法。ODP.NET 對 `: NAME` 的處理方式沒有原始碼可查,**假設**它能接受(依據是這功能有在用,而且 13 個參數都有 `AddInParameter`),但這是要驗的。

### 6.5 寄信

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:307-342`。逐列判斷:勾選了 **且** `CONNECT_RE = 'Y'`(業務需回覆)才寄。

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 用該列的 `EMP_NO` 查 `UID_CODE` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:320` |
| 2 | 用 `UID_CODE` 查 EMAIL | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:321` |
| 3 | 有 EMAIL → `SendMailTo`,寄件人是操作者的 EMAIL | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:328-330` |
| 4 | 沒 EMAIL → `MessageBox` 警示,繼續下一列 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` |

三個問題:

1. **N+1 次遠端往返。**每一列都打兩次 Pxy(`GetUidCode` + `GetEMAIL`),而且第 3 步又多打一次 `pxy.GetEMAIL(user)` 取操作者信箱(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:330`)——那個值在迴圈裡是固定的,卻每列重算。100 列就是 300 次 Remoting 往返。

2. **`GetUidCode` 的 SQL 缺括號。** `` WHERE EMP_NO = '<值>' AND TRIM(LEAVE_DATE) IS NULL OR LEAVE_DATE >= TO_CHAR(SYSDATE, 'YYYYMMDD')`` `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432`。`AND` 的優先序高於 `OR`,所以實際語意是 `(EMP_NO = 值 AND 未離職) OR (任何人 LEAVE_DATE >= 今天)`。**只要資料庫裡有任何一位未來離職日的員工,這支查詢就會回傳他的 `UID_CODE`**,而程式取 `Rows[0]`(`:443`)。結果是**信可能寄給錯的人**。這是本節最會咬人的一條。

3. **迴圈沒有 try/catch。**任一列寄信失敗就中斷整個迴圈,後面的列不會寄,而且資料已經 commit 了。

### 6.6 與 M 畫面的關係

| 面向 | `CASM002`(維護) | `CASB001`(批次) |
|---|---|---|
| 動到 `CLS002A` 的哪些欄 | 9 個業務欄 | 5 個 + 13 個四眼欄 |
| 四眼 | 走引擎 | **繞過** |
| `USAGE` 過濾 | 有 | **無** |
| 區域別來源 | `CAS004A` | `CRM003A` |
| 對 `CLS001A` | 增刪改 | 只讀 |

**兩支畫面對同一張表的寫法完全不同,而且沒有任何一方知道另一方存在。**在 `CASM002` 送審中的拜訪單,可以同時被 `CASB001` 從背後把明細改掉並蓋成「已覆核」。

### 6.7 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 日期 / 員工 / 機構關鍵字 必擇一 | 三個都空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:79-85` |
| 按查詢前 | 實際拜訪日期起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:233-235` |
| 查詢時 | 「未閱」條件濾掉 NULL | 欄位是 NULL | **過濾(無提示,且違反直覺)** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` |
| 查詢時 | 機構名稱是等於不是 like | 永遠 | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:188` |
| 查詢時 | 沒有 `USAGE` 過濾 | 永遠 | (比 M / I 看得更多) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:134` |
| 雙擊列 | 未勾選不可編輯 | `ISCHECK` 是 false | 阻擋(靜默 return) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212` |
| 按執行前 | 只有「顯示既有錯誤清單」 | 清單非空 | 阻擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:188-197` |
| 按執行前 | 至少勾一列 | — | **沒有這條檢核** | — |
| 執行時 | 未勾選的列跳過 | `ISCHECK` false | 過濾(無提示) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:334` |
| 執行時 | 更新 0 筆也算成功 | 單號不在 `CLS002A` | **靜默視為成功** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356` |
| 執行時 | 一列都沒勾 | `i` 停在 0 | 不 commit 也不 rollback | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:359-362` |
| 執行時 | 四眼欄被直接覆寫 | 永遠 | 記錄不擋(**治理漏洞**) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341-353` |
| 寄信時 | 業務不需回覆 | `CONNECT_RE <> 'Y'` | 過濾(無提示) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:323` |
| 寄信時 | 查無 EMAIL | 空字串 | 警示(不擋,繼續下一列) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` |
| 寄信時 | `UID_CODE` 查詢缺括號 | 有未來離職日的員工存在 | **可能寄給錯的人** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432` |
| 寄信時 | 任一列丟例外 | — | 中斷整個迴圈(資料已 commit) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:317-338` |

## 7. 報表(R)

```text
[圖] CAS 報表的資料流：UI 選種類、Ctl 分兩條路、PO 呼叫版控外的 SP、最後落到 Crystal 或 Excel
圖中文字:① 用戶端挑報表種類 → 決定 ReportClass 與 RPT_KIND / CASRxxx UI / uopt 選項決定種類 / SetQueryParameters / ReportClass 字串 / QueryVDB Parameters / SDATE EDATE RPT_KIND / ② 兩條獨立往返：資料一條、rpt 檔一條 / Ctl GetReportData / 走 PO 取資料 / Ctl GetReportObject / 用戶端指定類別名 / CRReportTransfer / 無原始碼 回傳 byte / ③ PO：SP + RefCursor，SQL 一行都不在程式裡 / GetStoredProcCommand / S_TA_CASRnnn_GET / CommandTimeout = 0 / 永不逾時 / C_RES RefCursor / 落地成結果集表 / SP 不在版控 / 8+2 支全部看不到 / ④ 落地：Crystal 或 Excel 二選一 / CreateCRReportDocument / 寫暫存檔再 Load / CrystalViewForm / 預覽視窗 / ExcelCreator / CASR002 只走這條 / 19 支 rpt / 2 支靠 PostBuild xcopy
```

*圖:圖 4 報表流。橘框=本模組程式碼；黑框=無原始碼（框架或版控外的 SP）；橘虛框=要特別留意的行為。資料與 rpt 檔是兩次獨立的遠端往返，版本不一致時不會有任何錯誤訊息。*

8 支 R 畫面、19 支 `.rpt`。**這一章跟前面幾章幾乎沒有交集**:報表不引用任何 CAS 的維護 PO,資料全部來自版控外的 SP,連表名都看不到(§1.1 的第 2 點)。

所以本章能寫的只有三件事:**哪支畫面吐哪些 `.rpt`、呼叫哪支 SP、送哪些參數**。SP 裡面怎麼算,repo 內查不到,要問 DBA 或去 Oracle 撈 `USER_SOURCE`。

### 7.1 一覽

| 畫面 | 取數 SP | `.rpt` | 挑 rpt 的依據 | 錨點 |
|---|---|---|---|---|
| `CASR001` | `S_TA_CASR001_GET` | `CASR001RPS` `CASR001RPS2` `CASR001RPS3` `CASR001RPS4` `CASR001RPS5` `CASR001RPS6` | 報表種類單選鈕的索引 0~5 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:89-113` |
| `CASR002` | `S_TA_CASR002_GET` | **無** | — | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:247-314` |
| `CASR003` | `S_TA_CASR003_GET` | `CASR003RPS` `CASR003RPS1` | 交易別單選鈕 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:178-182` |
| `CASR004` | `S_TA_CASR004_GET`(列印)/ `S_TA_CASR004_GET_XLS`(匯出) | `CASR004RPS` | 固定一支 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:294-296` 配 `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |
| `CASR005` | `S_TA_CASR005_GET` | `CASR005RPS` `CASR005RPS1`(另有孤兒檔 `CASR005RPS11`) | 報表種類單選鈕的索引 0 / 非 0 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:190-192` |
| `CASR006` | `S_TA_CASR006_GET` | `CASR006RPS` `CASR006RPS2` | 交易別;選「合併」時**連續出兩張** | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:173-189` |
| `CASR007` | `S_TA_CASR007_GET` | `CASR007RPS` | 固定一支 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:138` |
| `CASR008` | `S_TA_CASR008_GET` | `CASR008RPS` `CASR008RPS1` `CASR008RPS2` | 三個獨立勾選框,勾幾個出幾張 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:344-364` |

**19 支 `.rpt` 只有 17 支被程式指名**(上表共 15 支 + `CASM002RPS` 屬 §4.2 的拜訪記錄單 + `CASR005RPS11`)。`CASR005RPS11` 全庫**零引用**,是孤兒;它與 `CASR003RPS` 一起躺在 `ReportUI.CAS` 資料夾,靠 PostBuild 的 `xcopy "$(ProjectDir)*.rpt"` 一起被複製到平台的報表目錄(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331`)。也就是說**它會被交付到正式環境,但沒有任何程式叫得動它**。

### 7.2 八支 SP 的參數

全部走同一個樣板:`GetStoredProcCommand` → `AddInParameter`(一律 `Varchar2`)→ `AddOutParameter`(`RefCursor`)→ `LoadDataSet`。

| 畫面 | 參數(依程式順序) |
|---|---|
| `CASR001` | `iSDATE` `iEDATE` `iEMP_NO` `iRPT_KIND` |
| `CASR002` | `iSDATE` `iEDATE` `iAGENT_ID` `iAGENT_CODE` `iEMP_NO` `iPRI_TYPE` `iFUND_ID` `iPROF_TYPE3` `iBANK_KIND` `iRPT_KIND` |
| `CASR003` | `iSDATE` `iEDATE` `iCRNCY` `iBANK_KIND` `iTRADE_KIND` `iAGENT_ID` `iAGENT_CODE` `iFUNDS` |
| `CASR004` | `iSDATE` `iEDATE` `iAGENT_ID_S` `iAGENT_CODE_S` `iAGENT_ID_E` `iAGENT_CODE_E` `iDEPT_CODE` `iFUNDS` `iFUND_YN` |
| `CASR005` | `iSDATE` `iEDATE` `iDATE_KIND` `iFIRST_NULL` `iAGENT_ID` `iDEPT_CODE` `iFUNDS` `iRPT_KIND` |
| `CASR006` | `iKIND` `iSDATE` `iEDATE` `iFUND` `iALLOT_CODE` |
| `CASR007` | `iSDATE` `iEDATE` `iAGENT_ID` `iAGENT_CODE` |
| `CASR008` | `iSDATE` `iEDATE` `iAGENT_ID_ST` `iAGENT_CODE_ST` `iAGENT_ID_END` `iAGENT_CODE_END` `iDEPT_CODE` `iINV_AREA` `iPROF_TYPE` `iPROF_TYPE3` `iRPT_KIND` `iRPT_FIRST` |

錨點:`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:61-66`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:61-72`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:61-70`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:70-80`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:61-71`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:65-73`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR007_PO.cs:61-66`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:69-82`。

三件跨全部八支的共同事實:

| 事實 | 說明 | 錨點(舉一) |
|---|---|---|
| **參數全部綁定,不串字串** | 與 M / I / B 畫面相反,這裡沒有 SQL 注入風險 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:61-68` |
| **`CommandTimeout = 0`** | 永不逾時。SP 掛住時使用者端會一直轉,沒有取消機制 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` |
| **`catch` 把訊息吃掉** | `AddResultRow(false, 0, string.Empty)`——回傳失敗但**訊息是空字串**,使用者只看得到框架的預設文字 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:81-84` |

最後一條要強調:**八支報表只要 SP 出錯,使用者拿到的訊息都是空的**,連「查無資料」都不是。要知道真正發生什麼事只能看伺服器端的 log。

### 7.3 結果集怎麼挑:三種寫法、三種毛病

八支裡有三支要依畫面選項決定把 RefCursor 灌進哪一張結果集。三支的寫法都不一樣,而且各有一個洞。

#### `CASR002` — 11 選 1 的 if-else 階梯

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-113`。依 `RPT_KIND`(1~6)配 `BANK_KIND`(1 = 總行 / 其他 = 分行)決定表名:

| `RPT_KIND` | `BANK_KIND` = 1 | 其他 |
|---|---|---|
| 1 | `CASR002_ALLOT_HQ` | `CASR002_ALLOT_BRH` |
| 2 | `CASR002_REDEM_HQ` | `CASR002_REDEM_BRH` |
| 3 | `CASR002_STOCK_HQ` | `CASR002_STOCK_BRH` |
| 4 | `CASR002_NET_HQ` | `CASR002_NET_BRH` |
| 5 | `CASR002_HQ` | `CASR002_BRH` |
| 6 | `CASR002_STAS`(不分總分行) | 同左 |

**沒有 `else`。**`RPT_KIND` 不是 1~6 時 `tblName` 停在空字串,下一行 `LoadDataSet(..., new string[] { "" })` 與再下一行 `model.DataEntity.Tables[""].Rows.Count`(`:115`、`:118`)都會炸。UI 端的「下載EXCEL必須選取其中之一」檢核**是註解掉的**(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:94`),所以這條路不是理論上的。

#### `CASR005` — 二選一,但兩個選法各看各的

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:72-75`:`RPT_KIND == "1"` 灌進 `CASR005`,否則灌進 `CASR005_S`。 UI 端挑 `.rpt` 卻是看 `CheckedIndex == 0`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:190-192`),而送給 SP 的是同一組單選鈕的 `Value`(`:188`)。

**假設**:該單選鈕索引 0 的 `Value` 就是 `"1"`,兩邊才對得起來;依據是 `.rpt` 的中文名(索引 0 是「明細表」)與 PO 的結果集(`CASR005` 是明細、`CASR005_S` 是統計)語意一致。`Value` 的實際設定在 `.Designer.cs`,**本文不讀 Designer**,要確認請直接開畫面。**一旦 `Value` 與索引脫鉤,就會出現「拿明細的版面套統計的資料」。**

判斷「有沒有資料」時用的是 `CASR005.Count + CASR005_S.Count > 0`(`:78`),兩張加總——這一段反而是穩的。

#### `CASR008` — 迴圈跑多次,但計數漏掉一種

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:65-89`。`RPT_KIND` 是逗號串,每一段跑一次 SP,表名是:

```
tblName = aRPT_KIND[i] == "0" ? "CASR008" : ("CASR008_" + aRPT_KIND[i]);
```

`:86`。但下面數筆數的迴圈寫的是:

```
if (model.DataEntity.Tables["CASR008_" + s] != null)
    nRow = nRow + model.DataEntity.Tables["CASR008_" + s].Rows.Count;
```

`:93-95`。**`"0"` 那一段灌進 `CASR008`,計數時卻去找 `CASR008_0`**,找不到就跳過。所以使用者只選到 `"0"` 這一類時,即使 SP 撈回一堆資料,`nRow` 仍是 0 → 回「查無資料」(`:103`)。這是本章最會咬人的一條。

`iRPT_FIRST` 參數只有第一圈是 `"Y"`(`:80`),**推測**是給 SP 判斷要不要先清暫存表;依據是參數名與 `i == 0` 的條件,SP 無原始碼無法證實。

#### 另外兩支的分支

`CASR004` 是**換 SP 不是換表**:`RPT_KIND` 等於 `"RPT"` 走 `S_TA_CASR004_GET`,否則走 `S_TA_CASR004_GET_XLS`(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60`)。UI 的列印路徑硬塞 `"RPT"`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:282`)、匯出路徑硬塞 `"XLS"`(`:380`)。**兩支 SP 的欄位必須一致才不會壞版面,而這件事沒有任何程式保證。**

`CASR006` 用 `switch (sAllot_Code)`,三個 case:`"1"` 一般、`"4"` 定期定額、`""` 合併(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:74-94`)。**同樣沒有 `default`**,但這支比較安全:落空時 `nCnt` 留 0 → 回「查無資料」,不會丟例外。三個 case 的 `LoadDataSet` 三行一模一樣,差別只在計數用哪一張表。

### 7.4 一次出多張報表的兩支

`CASR006` 與 `CASR008` 會在一次操作裡連續出多張 `.rpt`,用的是同一套手法:

| 步 | 做什麼 | `CASR006` 錨點 | `CASR008` 錨點 |
|---|---|---|---|
| 1 | 第一次進 `BeforePreview` 時 `e.Cancel = true`,取消框架原本的那一次 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:130-133` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:302-303` |
| 2 | 立一個 `isPrintData` 旗標,把查詢參數存進成員變數 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:135-137` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:305-307` |
| 3 | 用匿名委派 `doAct` 逐張呼叫 `DoPreview()` / `DoPrint()` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:142-161`、`:173-189` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:312-326`、`:344-364` |
| 4 | 每一張進來時走 `else` 分支,只設 `.rpt` 類別名 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:196-207` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:369-375` |
| 5 | 資料只查一次,快取在 `m_ReportData` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:425-435` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:280-288` |

兩個要注意的:

1. **`CASR006` 的兩段註解文字是別支畫面的。**`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:176`、`:185` 寫「既有客戶交易異常表」「既有客戶交易異常表-受益人明細」,但實際設的報表名是「每日申購信託基金交易明細表」。複製樣板時沒改註解,讀碼會被誤導。

2. **`CASR008` 的三個勾選框全不勾時,三個 `if` 都不成立,什麼都不會發生**(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:344-364`),而且第一次的作業已經被 `e.Cancel = true` 取消了。使用者按下預覽,畫面沒有任何反應也沒有訊息。對應的「至少選一項」檢核在 `DoValidate` 裡,是由 `ValidateGroupBoxChecked` 對 `ugrpRPT_KIND` 做的(`:235`),**但那一組是「報表選項」,不是決定出哪幾張 rpt 的那三個勾選框**。

### 7.5 畫面端的檢核

| 畫面 | 檢核 | 結果 | 錨點 |
|---|---|---|---|
| `CASR001` | 拜訪日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:60-61` |
| `CASR001` | 報表種類必選 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:63-64` |
| `CASR001` | 種類 1、2 時員工代碼不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:65-67` |
| `CASR001` | 車資表時起迄必須同年月 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:69-71` |
| `CASR002` | 日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:90-91` |
| `CASR002` | 個別基金時基金不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:97-98` |
| `CASR002` | 報表種類必選 | **被註解,不執行** | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:93-94` |
| `CASR003` | 申購期間起 ≤ 迄 / 機構至少一勾 / 基金至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR003.cs:159-166` |
| `CASR004` | 統計日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:95-96` |
| `CASR004` | 機構別 / 機構代碼起迄成對與大小 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:99-132` |
| `CASR004` | 基金明細至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:134-135` |
| `CASR005` | 日期起 ≤ 迄 / 基金至少一勾 / 機構區分碼至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR005.cs:56-64` |
| `CASR006` | 申購日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:94-95` |
| `CASR007` | 日期起 ≤ 迄 / 機構至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR007.cs:116-120` |
| `CASR008` | 統計日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:163-164` |
| `CASR008` | 機構別 / 機構代碼起迄成對與大小 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:166-191` |
| `CASR008` | 投資地區 / 基金類型 / 管理費率類別 / 報表選項各至少一勾 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:193-243` |
| 全部 | 匯出 Excel 時路徑不得為空 | 阻擋 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR004.cs:370-371`(舉一) |

`CASR008` 那四組勾選的取值方式要單獨記:`ValidateGroupBoxChecked` **把送給 SP 的代碼從控件名稱的最後一個字元切出來**:

```
grp.Controls.OfType<UltraCheckEditor>().Where(c => c.Checked)
   .OrderBy(c => c.TabIndex)
   .Select(c => c.Name.Substring(c.Name.Length - 1));
```

`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:110-118`。也就是說 **`uchkINV_A` 這種控件改個名字,送給 SP 的參數值就變了**,而且沒有任何地方寫下這個約定。投資地區那一組還多一條特例:名稱結尾是 `F` 的會被展開成 `F,G`(`:114`)〔客戶特定〕。這是典型的「位置取參數」。

### 7.6 `CASR001` 的員工代碼有一條特別的預設

`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:119-130`:員工代碼欄空白時,程式會去 `EmployeeDataSrc` 用 `IS_CASB001 = 'Y'` 撈一批員工,把代號用逗號串起來當 `EMP_NO` 送給 SP。

兩件事:

1. **「全部」的定義不是真的全部**,是「`IS_CASB001` 為 `Y` 的那一批」。這個旗標的意義在 CAS 內看不到(它屬於員工資料來源,無原始碼,從呼叫端反推),**推測**是「代銷組客戶拜訪作業的適用人員」,依據是旗標名稱直接引用 `CASB001` 這支畫面。

2. **`sEmp` 是畫面層級的成員變數,只在欄位為空時才重算**。同一次開窗內先指定員工、再清空,第二次的 `sEmp` 用的是前一次算好的值——不影響結果(內容一樣),但這個寫法在別的情境會咬人。

### 7.7 對維護資料的關係

**報表不寫任何表,也不引用任何 CAS 的維護 PO。**八支 `_PO` 全部是「不繼承基底、自己 `new Database`、自己 `BeginTransaction` 只為了讀」的樣板(`architecture.md §6.5`)。

所以下列問題在 repo 內**回答不了**,要去 SP 裡查:

| 問題 | 為什麼查不到 |
|---|---|
| `CASM004` / `CASM005` 設的分配比率,哪一支報表在用? | 沒有任何 `.cs` 讀 `CAS004A` / `CAS005A` 做計算(§0.3) |
| `CASM003` / `CASM006` 設的年度目標,哪一支報表在比達成率? | 同上 |
| 報表數字與畫面數字對不起來時該查哪裡? | 只能查 SP |

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` 是專案樣板留下的空類別,12 行、無任何內容,從沒被引用。

## 8. 跨模組共用

```text
[圖] 改 CRM003A、CLS001A、CLS002A、DSM001A、DSM002A 會波及哪些畫面
圖中文字:改這四張表，要一起看的畫面 / CRM003A / 72 欄 四眼齊 / CASM001 主檔 / 本模組 / CRMM003 主檔 / CRM 模組 / CASM002 CASI001 / join 取機構名 / CLS001A／CLS002A：CAS 三支畫面 + CLS 模組自己 / CLS001A CLS002A / 85+26 欄 四眼齊 / CASM002 維護 / USAGE=3 才看得到 / CASI001 查詢 / 同樣 USAGE=3 / CASB001 批次 / 不濾 USAGE 直接改 / CLS 模組畫面 / 同表另一組入口 / DSM001A／DSM002A：CASM006 與 DSMM001 兩個入口 / DSM001A DSM002A / 年／月業績目標 / CASM006 / 只看 8 個部門 / DSMM001 / DSM 模組 無部門限制 / CAS 自有表被誰用（改動只影響本模組） / CAS001A CAS002A / 只有 CASM003 / CAS003A / CASM001 + CASM002 讀 / CAS004A / CASM004 + M002/I001 取區域別 / CAS005A / 只有 CASM005
```

*圖:圖 5 跨模組影響面。橘框=被共用的表；灰虛框=本模組以外的入口；橘虛框=行為與其他入口不一致的地方。左邊的表只要加欄或改型別，箭頭所指的每個入口都要重編與回歸。*

這一章回答一個問題:**改 `CRM003A` / `CLS001A` / `CLS002A` / `DSM001A` / `DSM002A` 會打到誰。**

10 張表裡 CAS 自己的只有 5 張(`CAS001A` `CAS002A` `CAS003A` `CAS004A` `CAS005A`),另外 5 張都是借來的,而且是當**主檔**在借(§0.2)。

### 8.1 三張借來的主檔,三種借法

| 表 | CAS 怎麼用 | 別人怎麼用 | 兩邊會不會看到同一筆 |
|---|---|---|---|
| `CRM003A` | `CASM001` 當主檔,增刪改 | `CRMM003` 當主檔,增刪改;`TMKM001` / `TMKM002` 唯讀 join | **不會**,靠 `USAGE` 分治(§8.2) |
| `CLS001A` + `CLS002A` | `CASM002` 當主明細;`CASB001` 直接 UPDATE 明細 | `CLSI001` / `CRMI001` / `DSMI001` 三支查詢畫面唯讀 | **會**,`CASM002` / `CASI001` 有 `USAGE` 過濾,另外四支沒有(§8.3) |
| `DSM001A` + `DSM002A` | `CASM006` 當主明細 | `DSMM001` 當主明細 | **會,而且範圍不一樣**(§8.4) |

### 8.2 `CRM003A`:靠 `USAGE` 切成兩個互不相見的世界

| 誰 | 寫進去的 `USAGE` | 查詢時的條件 | 錨點 |
|---|---|---|---|
| `CASM001` | `'3'` | `= '3'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| `CRMM003` | `'1'` | `= '1'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `TMKM001` | 不寫 | `= '1'`(唯讀 join) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` |
| `TMKM002` | 不寫 | **無 `USAGE` 條件**(`LEFT JOIN` 取機構名) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` |

**結論:資料層面互不干擾,schema 層面完全共用。**

| 改什麼 | 會打到誰 |
|---|---|
| 加欄位 / 改型別 / 改長度 | `CASM001Model.xsd` 與 `CRMM003Model.xsd` **兩份 xsd 都要重生**,兩支畫面都要回歸(`architecture.md §5`) |
| 改 PK(`PR_NO`) | `CASM001` 的取號、`CASM002` / `CASI001` / `CASB001` 的 join、`CRMM003`、`TMKM001`、`TMKM002` 全打到 |
| 改 `USAGE` 的值域 | **兩個模組的可見範圍同時翻掉**——這是最危險的一種改動 |
| 只改 `USAGE = '3'` 那一批資料 | 只有 CAS 受影響 |

`CRM003A` 的欄位定義同時出現在三份 xsd(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`),**三份不同步就會出現「某支畫面存得進、另一支讀不出來」**。

另外還有三處唯讀引用不在維護畫面上,改欄位時容易漏:`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs`、`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`,以及共用件 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicOFD_PO.cs`。

### 8.3 `CLS001A` / `CLS002A`:五支畫面、四種可見範圍

| 畫面 | 模組 | 對 `CLS001A` | 對 `CLS002A` | `USAGE` 過濾 |
|---|---|---|---|---|
| `CASM002` | CAS | 主檔,增刪改 | 明細,增刪改 | **有**(內外各一次) |
| `CASI001` | CAS | 唯讀 | 唯讀 `LEFT JOIN` | **有** |
| `CASB001` | CAS | 唯讀 | **直接 UPDATE,繞過四眼** | **無** |
| `CLSI001` | CLS | 唯讀 | 唯讀 | 待查(本文未讀 CLS) |
| `CRMI001` | CRM | 唯讀 | 唯讀 | 待查 |
| `DSMI001` | DSM | 唯讀 | 唯讀 | 待查 |

錨點:`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs`。三支都沒有任何 `INSERT` / `UPDATE` / `DELETE`,**只有 CAS 會寫這兩張表**。

**這裡最要緊的不是「誰讀」,是 `CASB001` 那段 UPDATE(§6.3)。**它把 `CLS002A` 的 13 個四眼欄位直接覆寫成「同一個人輸入 + 驗證 + 覆核」,而 `CLS001A` 主檔不動。後果:

| 現象 | 誰會踩到 |
|---|---|
| 主檔與明細的四眼狀態不一致 | `CASM002` 再開同一筆時,明細已經是 `'301'` 而主檔還在原狀態 |
| `CREATEID` / `CREATEDATE` 被蓋掉 | 任何要追「這筆是誰建的」的稽核需求,包含 CLS 自己 |
| 沒有 `USAGE` 過濾 | `CASB001` 改得到 `CASM002` / `CASI001` 根本看不到的資料 |

**改 `CLS002A` 的欄位時,一定要同時檢查 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:302-323` 那段手寫的 `UPDATE`**——它把欄位名寫死在字串裡,xsd 重生不會同步它,改錯只有在執行時才會炸。

`CLS002A` 的欄位定義出現在三份 CAS 的 xsd(`CASB001Model.xsd` / `CASB001View.xsd` / `CASM002Model.xsd`),CLS 那邊另有一份。

### 8.4 `DSM001A` / `DSM002A`:同一張表,兩支維護畫面,兩種員工範圍

`CASM006` 與 `DSMM001` 都把這兩張當主明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36`),**六個業績指標欄位一模一樣**。差別全在取數 SQL:

| 面向 | `CASM006` | `DSMM001` |
|---|---|---|
| 部門欄從哪來 | `COD009` 的部門欄 | **`SAL051` 的直銷部門欄** |
| 額外 join | 只有 `COD009`(INNER) | `COD009` **加** `SAL051`,兩個都是 INNER |
| 部門限制 | 寫死八個部門的白名單 | 沒有白名單,但被 `SAL051` 的 INNER JOIN 限制成「直銷員工」 |
| 年度查詢 | 只能等於 | 只能等於 |
| 錨點 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113-127`、`:210` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:113-131`、`:144-154` |

`DSMM001_PO` 第 112 行的註解直接寫明:「`SAL051` 為直銷的員工範圍」。

**所以兩支畫面看到的員工集合是兩個不同的集合,不是「一個包含另一個」:**

| 員工 | `CASM006` 看得到 | `DSMM001` 看得到 |
|---|---|---|
| 在八部門白名單內,且在 `SAL051` | ✔ | ✔ |
| 在白名單內,不在 `SAL051` | ✔ | ✘ |
| 不在白名單,在 `SAL051` | ✘ | ✔ |
| 兩者皆非 | ✘ | ✘ |

第二、三列就是「同一筆年度目標,一支畫面查得到、另一支查不到」的來源,而且**兩邊都不會提示**。要改任何一邊的範圍之前,先問清楚業務上這兩個集合是不是刻意分開的。

**`DSMM002` 不算在內。**它的主明細是 `DSM007A` / `DSM008A`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36`),檔案裡出現的 `DSM002A` 全部在註解區塊(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-119`),是從 `DSMM001` 複製樣板留下的。搜尋字串時會誤判,**別被騙**。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `DSM001A` `DSM002A` 欄位 | `CASM006Model.xsd` / `CASM006View.xsd` 與 `DSMM001Model.xsd` 都要重生,兩支畫面都要回歸 |
| 改 `CASM006` 的部門白名單 | 只影響 `CASM006`;`DSMM001` 不受影響 |
| 改 `SAL051` 的內容 | 只影響 `DSMM001` |
| 改 `COD009` | **兩支都影響**,而且因為是 INNER JOIN,刪一個員工等於讓他的目標整筆消失 |

### 8.5 共用的 UI 控件與下拉來源

CAS 沒有用到 `Dev/Common/Source/DataSource/PO.DataSource` 底下的共用 PO,但大量使用共用控件:

| 控件 | 用在哪 | 出現次數 |
|---|---|---|
| `ucFundID` | 報表側的基金選取 | 78 |
| `ucAgentCode` | 銷售機構代碼(靠 `TrustAgentID` 連動區別碼) | 77 |
| `ucEmployeeData` | 員工代碼(`Filter` / `IS_MARKETING` / `LEAVE_DATE` 三種過濾入口) | 53 |
| `ucAddress` | `CASM001` 的通訊地址拆解 | 5 |
| `EmployeeDataSrc` | `CASR001` 的「全部員工」預設值 | 4 |

全部無原始碼,從呼叫端反推。**`ucEmployeeData` 是最需要小心的一個**:它同時吃 `Filter` 字串與 `ConditionVDB` 參數兩種過濾,而 `CASM005` 兩種都設而且互相矛盾(§4.5)。

## 附錄 A. 資料表總表

| 表 | 欄位數 | 四眼欄位 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `CAS001A` | 9 | 無 | CAS | `CASM003` | — | 增刪改 |
| `CAS002A` | 8 | 無 | CAS | — | `CASM003` | 增刪改 |
| `CAS003A` | 35 | 有 | CAS | — | `CASM001` | 增刪改 |
| `CAS004A` | 10 | 無 | CAS | `CASM004` | — | 增刪改 + SP 複製 |
| `CAS005A` | 11 | 無 | CAS | `CASM005` | — | 增刪改 + 程式內複製 |
| `CLS001A` | 85 | 有 | **CLS**〔共用〕 | `CASM002` | — | 增刪改;`CASI001` / `CASB001` 唯讀 |
| `CLS002A` | 26 | 有 | **CLS**〔共用〕 | — | `CASM002` | 增刪改;`CASB001` **直接 UPDATE** |
| `CRM003A` | 72 | 有 | **CRM / TMK**〔共用〕 | `CASM001` `CRMM003` | — | 增刪改(限 `USAGE = '3'`) |
| `DSM001A` | 15 | 無 | **DSM**〔共用〕 | `CASM006` `DSMM001` | — | 增刪改 |
| `DSM002A` | 13 | 無 | **DSM**〔共用〕 | — | `CASM006` `DSMM001` | 增刪改 |

只讀不寫的外部表(join 進來取說明用,本模組從不寫入):

| 表 | 取什麼 | 被誰 join | join 型態 |
|---|---|---|---|
| `COD009` | 員工姓名、部門、離職日 | `CASM001` `CASM003` `CASM004` `CASM005` `CASM006` `CASI001` `CASB001` | `CASM003` / `CASM006` 是 **INNER**,其餘 `LEFT` |
| `COD006A` | 各類代碼說明 | `CASM001`(2 次)`CASM002`(2 次)`CASI001`(10 次) | `LEFT` |
| `CTL014` | 拜訪方式、投資特性說明 | `CASI001` `CASM002` | `LEFT` |
| `OFD068A` | 銷售機構名稱 / 簡稱 | `CASM004` `CASM005` | `LEFT` |
| `BMS001A` | 受益人姓名 | `CASM005` | `LEFT` |
| `SAL051` | (只在 `DSMM001` 用,列出供 §8.4 對照) | `DSMM001` | INNER |

兩張非實體結果集:`CAS004A_OVER`(`CASM004p0` 的超額清單)、`CAS005A_OVER`(`CASM005p0` 的超額清單)。它們不是資料表,是 SP 或程式回傳的暫時結果集(§4.4、§4.5)。

## 附錄 B. SP / Function / Trigger / View

**`DBScript/` 裡屬於本模組的 SP / Function / Trigger / View 是 0 支。**掃描母體(`docs/_candidates/cas.md` 第 3 節)是空表。

但程式確實呼叫了 10 支 SP,**全部不在版控內**:

| SP | 被誰呼叫 | 用途 | 呼叫點錨點 |
|---|---|---|---|
| `S_TA_CASM004_P01` | `CASM004p0` | 複製業務員的機構分配比率 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:97` |
| `S_TA_CASR001_GET` | `CASR001` | 訪談報告 6 種 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58` |
| `S_TA_CASR002_GET` | `CASR002` | 業務人員明細統計(11 種結果集) | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:56` |
| `S_TA_CASR003_GET` | `CASR003` | 銷售機構銷售總表 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR003_PO.cs:58` |
| `S_TA_CASR004_GET` | `CASR004`(列印) | 期間收入統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR004_PO.cs:60` |
| `S_TA_CASR004_GET_XLS` | `CASR004`(匯出) | 同上的 Excel 版 | 同上 |
| `S_TA_CASR005_GET` | `CASR005` | 退休管家庫存明細 / 統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR005_PO.cs:58` |
| `S_TA_CASR006_GET` | `CASR006` | 每日申購信託基金交易明細 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:60` |
| `S_TA_CASR007_GET` | `CASR007` | 定額契約統計 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR007_PO.cs:58` |
| `S_TA_CASR008_GET` | `CASR008` | 期間銷售統計 / 排行 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:61` |

**這 10 支的內容在 repo 內完全看不到。**要知道報表數字怎麼算、複製功能複製了什麼條件,只能去 Oracle 撈 `USER_SOURCE`,或問 DBA。改這些 SP 沒有版控保護,也沒有 code review 流程——這是本模組最大的結構性風險。

## 附錄 C. 代碼對照

`STATUS` 與本模組自訂旗標值見 §2.5,不重複。這裡補下拉選單的代碼來源編號(`GetDropDownDataSrc` / `GetDropDown9iDataSrc` 的參數)。

| 代碼 | 用途(取自程式註解) | 用在哪 |
|---|---|---|
| `062` | 銷售機構區別碼 | `CASM004` `CASM005` `CASM004p0` |
| `418` | 管理費率類別 | `CASR002` `CASR008` |
| `440` | 主管2(主管)閱 | **只有 `CASB001p0`** |
| `447` | 預估 / 實際拜訪方式 | `CASM002` `CASI001` `CASB001` |
| `448` | 往 / 返 | `CASM002` `CASI001` |
| `467` | 區域別 | `CASM004` `CASM005` `CASB001` |
| `468` | 組別 | `CASM004` `CASM005` |
| `469` | 投資特性(1 / 2 / 3) | `CASM002` `CASI001` |
| `470` | 主管閱(`CFM_USER1` / `CFM_USER2`) | `CASB001` `CASB001p0` `CASI001` |
| `471` | 業務需回覆否 | `CASB001` `CASI001` |
| `472` | 總行 / 分行別 | `CASB001` `CASB001p0` `CASI001` `CASI001p0` |
| `473` | 組長別 | `CASM004` `CASM005` |
| `474` | (無註解;對應 `SEND_FUND_YN`,呼叫已被註解) | `CASM001` |
| `494` | 業務已回覆 | `CASB001` `CASI001` |

**兩件要記住的:**

1. **同一個欄位兩個代碼來源。**`CFM_USER2` 在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.cs:207` 用 `440`,在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:293` 與 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:331` 用 `470`。**同一個欄位的下拉,彈出視窗與 grid 的選項可能不一樣。**

2. **註解與程式錯開一行。**`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:279-282` 的註解「總行」底下設的是區域別(`467`)、註解「預估拜訪方式」底下設的是主管閱(`470`)。**這一段的註解不能信**,要看控件名。

`COD006A` 的分類碼(`CODE_SORT`)與 `CTL014` 的 `SOURCETYPE` 對照見 §2.5。

## 附錄 D. 掃描母體與覆蓋率

母體來源:`docs/_candidates/cas.md`(由 `atlas_scan.py --module CAS` 產生)。

| 類別 | 母體 | 本文提及 | 覆蓋率 |
|---|---|---|---|
| 畫面 | 16(B 1 / I 1 / M 6 / R 8) | 16 | 100% |
| 實體表 | 10 | 10 | 100% |
| SP / Fn / Trigger / View | 0 | —(版控外的 10 支 SP 另列於附錄 B) | — |
| `.rpt` | 19 | 19 | 100% |
| WindowsService | 0 | — | — |

**沒有未提及的物件。**兩個要註記的邊界情況:

| 物件 | 狀態 | 處置 |
|---|---|---|
| `CASR005RPS11` | 在母體內,但全庫零引用(§7.1) | 已寫入本文並標為孤兒;**建議確認能否刪除** |
| `CAS004A_OVER` / `CAS005A_OVER` | **不在**母體的實體表清單內 | 它們是結果集不是表,本文在 §4.4 / §4.5 與附錄 A 標明 |

本文另外提及但不屬於 CAS 母體的物件(唯讀 join 或跨模組對照,列出以免被當成漏網): `COD009` `COD006A` `CTL014` `OFD068A` `BMS001A` `SAL051` `CRM006A` `CRM004A` `TMK001A` `DSM007A` `DSM008A`,以及畫面 `CRMM003` `CRMI001` `CRMB005` `CLSI001` `DSMM001` `DSMM002` `DSMI001` `TMKM001` `TMKM002` `OFDI011` `CRMR008`。

## 附錄 E. 讀本文時要注意的地方

按「讀碼時會被騙的方式」分類。嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 被註解掉但外殼還在的檢核

最常見的一類。**方法還在、介面還在、Ctl 還在,只有呼叫點被註解**,讀碼的人會以為這道檢核有效。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASM004p0` 的四條複製前檢核(年月大小、來源≠目標、存在性、100% 上限)全被註解 | 複製可以把資料蓋到不該蓋的地方,超額只能事後才報 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:68-118` | 高 |
| `IsEmpExsits` 三層(PO / 介面 / Ctl)都在,**零呼叫點**,而且它的「迄年月」條件也被註解 | 死碼;解開註解也不會照預期運作 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:241-263`、`:249`、`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM004_Ctl.cs:86-90` | 中 |
| `CASM002` 的三段「主談者資料不存在」檢核被註解,而且第三段複製貼上沒改對 | 解開註解也是錯的 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:554-579` | 中 |
| `CASM001` 的 `ID_NODoValidate()` 方法留著但內容是空的,呼叫點也被註解 | 看起來有一道金資檢核,其實沒有 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:567-571`、`:363` | 中 |
| `CASM006` 的五個年度指標 + 五個明細指標「必須大於 0」全被註解,但六個總和檢核留著 | 允許「年度 0、每月 0」通過;搭配 E.4 的月分配缺陷會讓使用者卡住 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:79-88`、`:106-119` | 中 |
| `CASM006` 的 `QueryVDB.Util.Parameters.Clear()` 被註解(另外三支 M 畫面都有) | 查詢條件累積,清空欄位查不乾淨 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:370` | 高 |
| `CASM006` 的業績年度起迄檢核與 PO 的區間條件同時被註解 | 年度只能精確比對 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:353-357`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:142-160` | 低 |
| `CASM004` 的機構區別碼(迄)在 UI 不送參數、PO 整段註解,但查詢檢核還在驗它 | 畫面上兩個欄位只能填一樣的值 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:262-263`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:419-436` | 中 |
| `CASI001` 的銷售機構金資起迄檢核整段被註解 | 該組條件只剩一個欄位有效 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:101-107` | 低 |
| `CASR002` 的「報表種類必選」檢核被註解,而 PO 沒有 `else` | 沒選種類 → PO 端空表名 → 例外 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR002.cs:93-94` 配 `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-118` | 高 |
| `CASM004` 的員工下拉部門排除整段被註解(留著「2015/12/25 改為代銷部門可修改」的說明) | 與 `CASM005` 的白名單不互斥 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:310-316` | 中 |
| `CASM005_PO` 的 region 名稱結尾多一個 `*/`,沒有對應的開頭 | 讀碼者會誤以為整段檢核是註解掉的(**它是活的**) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:219` | 低 |

### E.2 有訊息但沒有 `return` / 沒有 `Cancel`

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASM006` 選到已離職員工時跳訊息,**但照樣選得下去** | 可以幫離職者設年度目標 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` | 中 |
| `CASM004p0` 選完來源業務員後 `AddError` 但**沒有 `Show()`**,下一次 `DoValidate` 又 `Clear()` | 這則錯誤永遠不會被看到 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:249-262`、`:65` | 中 |
| `CASB001` 寄信時查無 EMAIL 只跳訊息,繼續下一列 | 使用者以為都寄出去了 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:331-332` | 中 |
| `CASM004` 比率欄的訊息寫「應介於0.01和100.00之間」,判斷式只有「等於 0」 | 訊息與行為不符 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:319-328` | 低 |
| `CASM005` 查詢的訊息寫「必須皆(不)填寫」,判斷式是「兩個都空才錯」 | 訊息與行為不符 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:174-175` | 低 |
| `CASR008` 三個報表勾選框全不勾時,按預覽**完全沒有反應也沒有訊息** | 使用者不知道發生什麼事 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:302-303`、`:344-364` | 中 |

### E.3 `catch` 吞例外 / 回傳值語意錯誤

**這一類最危險,因為它讓「檢核」在系統出問題時自動放行。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `GetEmpAgentStartDate` 的 `catch` **回傳 `ex.Message` 當開始日期** | 檢核被當成通過,例外訊息還會被寫進日期欄並傳進 SP | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:227-231` 配 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004p0.cs:98`、`:256-260` | **高(本模組最危險)** |
| `IsDIV_PCTExsits` 出錯回 `-1`,UI 判 `i > 0` | 100% 上限檢核靜默放行 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:295`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:218` | 高 |
| `IsID_NOExsits` 出錯回 `-1`,UI 判 `i > 0` | 金資代碼重複檢核靜默放行 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:384-388` | 高 |
| `GetCustType` / `GetDeptNo` 出錯回空字串,而且取 `Rows[0]` 沒判筆數 | 「代操客戶不可刪」只在一切正常時有效 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:475`、`:480-484`、`:511`、`:516-520` | 高 |
| `GetExcel()` 出錯回 `null`,UI 沒判 null 直接用 | `NullReferenceException` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:558-562`、`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:472-479` | 中 |
| `CASM002` 三處帶值的 `pxy.GetXXX` 都沒判 null | 同上 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM002.cs:592`、`:650`、`:681` | 中 |
| 八支報表 PO 的 `catch` 都是 `AddResultRow(false, 0, string.Empty)` | **SP 出錯時使用者拿到空訊息**,連「查無資料」都不是 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:81-84` | 高 |
| 七個 `After*` 的 `throw new ApplicationException("")` 訊息是空字串 | 追不到是哪一步失敗 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` | 中 |
| `CASM004` / `CASM005` 的複製在 `catch` 直接 rollback、`finally` 直接 `Dispose`,都沒判 null | 開交易失敗時真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:121-123`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:129-130`、`:136-137`、`:141-145` | 中 |
| `CASB001` 寫入後把實際影響筆數丟掉硬設成 `1` | 更新 0 筆也算成功 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:355-356` | 高 |

### E.4 同一概念多套實作

| 概念 | 幾套 | 差在哪 | 錨點 |
|---|---|---|---|
| 取員工姓名的 join | 2 | `CASM003` / `CASM006` 用 **INNER**(查不到員工整筆消失),`CASM004` / `CASM005` 用 `LEFT` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:119-121` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:373-374` |
| 取「最新月份的區域別」 | 2 | `CASM002` 用 `MAX(YYMM)` 配 `MIN(...) KEEP DENSE_RANK` **結果是全期間最小值**;`CASI001` 用 `ROW_NUMBER() ... ORDER BY YYMM DESC` 才是真的最新 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:141-144` |
| 「區域別」的資料來源 | 2 | `CASM002` / `CASI001` 來自 `CAS004A`,`CASB001` 來自 `CRM003A` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:199` |
| 業務員複製 | 2 | `CASM004` 走 SP 繞過四眼;`CASM005` 走程式逐列進四眼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:97-114` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:92-114` |
| 年度的月分配 | 2 | `CASM003` 固定 12 個月會跨年;`CASM006` 只到當年 12 月 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:142-171` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`、`:233-257` |
| 實際拜訪日期的比較 | 2 | `CASI001` 直接字串比;`CASB001` 用 `to_date(NVL(TRIM(...)))` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:147` |
| 離職員工的處理 | 2 | `CASM004` / `CASM005` 在下拉過濾掉(無提示);`CASM006` 跳訊息但不擋 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:456-463` |
| `CFM_USER2` 的下拉代碼 | 2 | 彈出視窗用 `440`,grid 用 `470` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001p0.cs:207` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:293` |
| 年度欄位的合理性檢查 | 2 | `CASM003` 有 1900~今年;`CASM006` 沒有 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:323-329` vs `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:420-428` |
| `GetEmpNo` 的筆數檢查 | 2 | `CASI001` 沒檢查直接取 `Rows[0]`;`CASB001` 有檢查 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:469` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:408` |
| `CAS004A` 的分配比率上限判斷 | 2 | `CASM004` 不含戶號;`CASM005` 含戶號。兩支對「同一組合」的定義不同 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:279-282` vs `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:200-205` |

### E.5 寫死常數〔客戶特定〕

換站台**一定要逐條確認**。

| 寫死的東西 | 值 | 錨點 |
|---|---|---|
| 可看全部拜訪紀錄的員工白名單 | 5 個員工代號 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| `CASM006` 的部門白名單 | `G3` `GA` `G11` `G12` `G13` `G14` `Z2` `G17` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` |
| `CASM005` 的銷售機構 | 區別碼 `0` + 機構代碼 `A0901`,而且**唯讀** | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:70-81`、`:127-130`、`:142-145` |
| `CASM005` 的員工部門白名單 | `G3` `GA` `G12` `G13` `G17` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005.cs:244-246` |
| `CASM005p0` 的員工部門白名單 | 同上**加** `G14` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM005p0.cs:198-200` |
| `CASM004` / `CASM005` 的員工過濾字串 | 排除 `G17` + 今年以前離職 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM004.cs:157-159` |
| 代操客戶不可刪的例外部門 | `X01` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:442-447` |
| `CRM003A` 的用途別 | `'3'`(CAS)/ `'1'`(CRM / TMK) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467` |
| `CASB001` 寫進 `CLS002A` 的狀態 | `'301'` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:341` |
| `CASR008` 投資地區的 `F` 展開成 `F,G` | `F` → `F,G` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:114` |
| `CASR001` 的「全部員工」定義 | `IS_CASB001 = 'Y'` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:122` |

### E.6 位置取參數

「值不是從資料來的,是從**它在哪裡**推出來的」。改名字、改順序就壞,而且編譯不會報錯。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASR008` 把送給 SP 的代碼從**控件名稱的最後一個字元**切出來 | 改控件名 = 改參數值,沒有任何約定文件 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR008.cs:110-118` | 高 |
| `CASI001` 取登入者員工代號:把回傳字串用逗號切開**取第 2 段** | 回傳格式一改就拿不到值,而且拿不到時條件整個不加 → 看到全部資料(§5.3) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:130-136` | **高** |
| `CASR008` 的表名靠 `RPT_KIND` 字串拼,`"0"` 拼出 `CASR008` 但計數找 `CASR008_0` | 只選該類時回「查無資料」 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR008_PO.cs:86`、`:93-95` | 高 |
| `CASM006` 的月分配用 `j < 12` 判斷最後一列,但列數是 `13 - 起算月` | 起算月不是 1 月就一定對不平,而且按幾次都修不好 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:169`、`:201` | **高** |
| `CASM003` 的跨年月份無條件補一個 `"0"` | 11 / 12 月起算會產生 7 碼年月,超過欄位長度 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM003.cs:150-151` | 中 |
| `CASB001` 雙擊判斷用 `"IsCheck"`,其餘地方用 `"ISCHECK"` | 目前能動(索引不分大小寫),但不一致 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:209-212` | 低 |

### E.7 SQL 層面的髒寫法

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CASI001` 的 8 處起迄條件寫成 `> =`(中間有空白) | **假設**整段 SQL 語法錯、被 `catch` 吞成「執行失敗」;無法本機驗證(§5.3) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219`、`:230`、`:241`、`:251`、`:262`、`:272`、`:283`、`:293` | 高 |
| `CASB001` 的 `UPDATE` 裡 13 個綁定變數寫成 `: NAME`(冒號後有空白),同段的前 5 個卻是正常的 | 同一段 SQL 兩種寫法;ODP.NET 的行為要實測 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:309-323` | 中 |
| `GetUidCode` 的 `AND` / `OR` 缺括號 | **信可能寄給錯的人**(§6.5) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:431-432` | **高** |
| `CASB001` 的「未閱」條件 `<> 'Y' AND <> 'Y'` 碰到 NULL 全被濾掉 | **查不到從沒被主管碰過的拜訪單**(§6.2) | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` | **高** |
| 維護與查詢畫面的查詢條件**全部字串串接**,唯二用綁定參數的是 `CASM002` 的報表查詢與 `CASB001` 的批次寫入 | SQL 注入面;報表側反而是乾淨的 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:588`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:336-354` | 高 |
| `CASM002` 的 `MAX(YYMM)` 被算出來卻沒有任何地方用到 | 讓人以為取的是最新一筆 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM002_PO.cs:220-224` | 中 |
| `CASR002` / `CASR006` 的結果集分支都**沒有 `default`** | `CASR002` 會丟例外;`CASR006` 靜默回「查無資料」 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR002_PO.cs:76-118`、`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR006_PO.cs:74-94` | 高 |
| 八支報表 SP 全部 `CommandTimeout = 0` | 永不逾時,使用者端沒有取消機制 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` | 中 |

### E.8 其他讀碼陷阱

| 陷阱 | 說明 | 錨點 |
|---|---|---|
| `CASM005_PO` 的複製有一行 `row.STATUS = row.STATUS;` | 自我賦值,等於沒做。複製出來的資料**沿用來源的四眼狀態** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:96` |
| `CASR006` 的兩段註解寫「既有客戶交易異常表」 | 是別支畫面的文字,實際設的報表名完全不同 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR006.cs:176`、`:185` |
| `CASB001.cs:279-282` 的三行註解與底下的程式各差一行 | 註解不能信,看控件名 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASB001.cs:279-282` |
| 四支 `_PO` 的介面註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製沒改,與實際功能無關 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:16-18` |
| `App.config` 的 `detailtable` 宣告與 PO 不一致(`CASM001` 被註解、`CASM002` 根本沒宣告) | **以程式為準**(§0.5) | `Dev/ATLAS.CAS/Source/UI/UI.CAS/App.config:29`、`:34-40` |
| `CASI001_PO` 在唯讀查詢裡設了一整排四眼欄位的 `DefaultValue` | 從 `CASB001` 樣板複製來的死碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:406-418` |
| `CASI001_PO` 的 `GetEmpNo` / `GetUidCode` 是 `public` 但不在介面裡 | Ctl 拿到的是介面型別,**呼叫不到**,是死碼 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:25-27` |
| `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` | 專案樣板留下的空類別,12 行、零引用 | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/Class1.cs` |
| `CASR005RPS11` | 交付到正式環境但零引用的孤兒報表 | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/ReportUI.CAS.csproj:331` |
| `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs` 裡的 `DSM002A` 全在註解區 | 搜尋字串時會誤判成第三支使用者(§8.4) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-119` |

### E.9 標「假設」的地方一覽

本文所有需要現場確認的推論,集中在這裡:

| § | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| §1.5 | `CASB001` 的執行頻率 | 查詢條件預設值與每次重整都重設為「未閱」 | 問使用者 |
| §4.3 | 進維護頁時框架會把參數換成該筆主鍵 | 主檔與明細共用同一份參數集合,而主檔用區間、明細用等於 | 實測:用區間查多筆,點第二筆看明細對不對 |
| §4.5 | `Filter` 與 `ConditionVDB` 合併後 `G17` 的淨效果是排除 | 兩者形態不同(DataView 過濾 vs SQL 條件) | 實測下拉清單有沒有 `G17` 的人 |
| §4.6 | 參數集合同名重加的行為 | 背後是 typed DataSet 的 `Rows.Find(name)` | 實測:連按兩次查詢換條件 |
| §5.3 | `> =` 會造成 Oracle 語法錯誤 | SQL 標準與 Oracle 詞法規則 | 連 DB 跑一次帶起迄條件的查詢 |
| §6.4 | 框架的 `ExecPOActionToViewVDB` 會補一列成功結果 | 否則寄信功能從來沒運作過,而郵件內容寫得很完整 | 實測:勾一列按執行,看有沒有寄信 |
| §6.4 | ODP.NET 能接受 `: NAME` 這種綁定寫法 | 這功能有在用,而且 13 個參數都有 `AddInParameter` | 同上 |
| §7.3 | `CASR005` 報表種類單選鈕索引 0 的值就是 `"1"` | `.rpt` 中文名與 PO 結果集語意一致 | 開畫面看選項值(本文不讀 `.Designer.cs`) |
| §7.3 | `CASR008` 的 `iRPT_FIRST` 是給 SP 判斷要不要清暫存 | 參數名與 `i == 0` 的條件 | 看 SP 原始碼 |
| §7.6 | `IS_CASB001` 是「代銷組客戶拜訪作業的適用人員」 | 旗標名直接引用 `CASB001` | 問使用者或看員工資料來源 |
| §0.3 | 真正拿分配比率去分帳的程式在版控外的 SP 或別的模組 | 本模組沒有任何一支程式讀分配比率做計算 | 查 SP;問 DBA |
| §3.2 | `CASI001` 主畫面的中文名與彈出視窗同名 | 彈出視窗標題是唯一可見的來源 | 看選單表 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純程式碼閱讀彙整,未執行、未連 DB。畫面中文名待選單表回填;版控外的 10 支 SP 內容未涵蓋。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 135 · 圖 5 · 表格 104 · 程式錨點 637 · § 連結 62 · 引用檢查：畫面 27（缺 0） · Table 20（缺 0） · Report 19（缺 0） · 結果集 16（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/cls.md
============================================================

# ATLAS CLS 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最容易被誤會的事)、§4 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由彈出視窗標題、表名與欄位中文名(`msdata:Caption`)**推測**,待選單表 / 對照表回填。7 支畫面裡只有 5 支彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼樣式(`S____`)、業務屬性碼(`A` / `B` / `C`)、每公里補助 6 元、30 天回補期限、遮罩長度、`USAGE = '2'`、報表編號「`CLSR002-1`~`-12`」的對外名稱為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`CLS001A` / `CLS002A` 名字看起來是 CLS 的,主人卻是 CAS(見 §8),改動要一起看。

> ⚠ **路徑大小寫**:`Dev/ATLAS.CLS/` 底下的子目錄是大寫 `SOURCE`,不是 `Source`(全庫 36 個專案只有 2 個這樣,見 `architecture.md §2.6`)。`Dev/ATLAS.CLS.Report/` 則是一般的 `Source`。本文錨點照實際大小寫寫,不要「順手改成一致」。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CLS 管「直銷業務員手上的潛在客戶名單,以及他們去拜訪這些客戶留下的紀錄」。**

推測依據五條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 彈出視窗標題 | 「**直銷**客戶查詢作業」——全模組唯一直接寫出業務屬性的字串 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:1073` |
| 表名與欄位中文名 | `CLS001` 的欄位是「潛在客戶序號」「潛在客戶來源代碼」「歸屬業務員」「KYC到期日」「境內庫存 / 境外庫存」;`CLS002` 是「拜訪單號」「預計 / 實際拜訪日期」「交通費」「拜訪記錄」 | `Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM001Model.xsd`、`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM002Model.xsd` |
| 明細彈出視窗標題 | 「目的/支援」「推薦基金」「批次新增拜訪重點」「受益人基本資料」 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.Designer.cs:351`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.Designer.cs:352`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.Designer.cs:172`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001p0.Designer.cs:171` |
| 報表中文名 | 「業務員客戶清冊－總表 / 明細表 / 基金別 / 當月壽星」「客戶來源清冊」「客戶拜訪記錄明細表」「客戶拜訪統計表－未過試用期」「交通費明細表」 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.Designer.cs:369-380`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.Designer.cs:608-627` |
| 建檔權限的判斷式 | 只有 `SAL051` 的業務屬性是 `A` 部門主管 / `B` 組長 / `C` 業務員才能建檔,其餘(助理、交割、其他)只能看 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479`、`:504-510` |

「CLS」三個字母本身的展開在 repo 裡找不到定義,**不要猜**。本文一律用「直銷潛在客戶」描述它的業務範圍,這是從上表推出來的,不是官方名稱。

兩條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 潛在客戶 | 業務員自己維護的潛在客戶名單:來源、風險屬性、KYC 期限、決策者、投資意願與上下限、境內外庫存(AUM) | `CLSM001` | `CLS001` |
| B 拜訪單 | 對名單上的人做的每一次拜訪:預計 / 實際日期與方式、主談者、拜訪重點、推薦了哪檔基金、客戶提了什麼新產品需求、交通費 | `CLSM002` | `CLS002` + `CLS003` `CLS004` `CLS005` |
| C 重算與參數 | 把庫存重算進 `CLS001` 並留一版快照;維護交通費上限與應拜訪次數兩個門檻 | `CLSB001`、`CLSB002` | `CLS012` 與 SP |
| D 報表 | 上面兩條線的清冊與統計,共 22 支版型 | `CLSR001`、`CLSR002` | `CLS001H` 快照 + SP |
| E 借來的查詢 | 看 CAS 那套「客戶拜訪單」裡屬於直銷的那一半 | `CLSI001` | `CLS001A`〔共用〕 |

### 0.2 這模組最容易被誤會的兩件事

**第一件:`CLS001`–`CLS005` 與 `CLS001A` / `CLS002A` 是完全不同的兩套東西。**

|  | `CLS001`~`CLS005` | `CLS001A` / `CLS002A` |
|---|---|---|
| 主檔畫面 | `CLSM001` / `CLSM002`(CLS 自己) | **`CASM002`**(CAS 的客戶拜訪單維護) |
| 拜訪單號欄位 | `CLL_NO` | `CALL_RPT_NO` |
| 潛在客戶主檔 | `CLS001`(CLS 自己維護) | `CRM003A`(CRM / TMK 維護) |
| CLS 這一側怎麼用 | 四眼維護、批次、報表全都用 | **只有 `CLSI001` 唯讀查詢**,而且硬加 `USAGE = '2'` |
| 已寫在哪 | 本文 §2–§7 | `cas.md §8`(從 CAS 那側寫過) |

驗證方式:`atlas_scan.py --table CLS001` 回報「主檔於 `CLSM001`、模組 CLS」;`atlas_scan.py --table CLS001A` 回報「主檔於 `CASM002`、模組 CAS, CLS」。掃描器把 `CLS001A` 歸到 CLS 只是因為**名字開頭三碼**,不是因為 CLS 擁有它。`CLSI001` 的 SQL 也證實這點:`FROM CLS001A` 之後 join 的是 `CRM003A` 與 `CAS004A`,沒有一張 CLS 自己的表(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106-112`)。

**第二件:報表看到的客戶名單,不是現在的 `CLS001`,是批次跑完那天的樣子。**

兩支 R 畫面(以及 `CLSM002` 的查詢)都不直接讀 `CLS001`,而是先用一段叫 `ISHIS` 的 CTE 從 `CLSB001` 取最後一次批次日期,再決定要讀 `CLS001H` 歷史快照還是 `CLS001` 現值:

- 查詢區間的迄日**早於**最後一次批次日 → 讀 `CLS001H`(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:73-83`)

- 查詢區間的迄日**就是**最後一次批次日 → 讀 `CLS001`(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:95-104`)

也就是說**同一筆客戶資料,剛改完馬上查報表看到的可能是舊值**,而且畫面上沒有任何提示。詳見 §2.5 與 §7.2。

### 0.3 不管什麼

以下**不在** CLS 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(已開戶客戶)基本資料 | BMS | `BMS001A` 全部是 `LEFT JOIN` 或 `SELECT`,零 INSERT / UPDATE;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:189-190` |
| 員工主檔、離職日、到職日 | COD | `COD009` 只被 join;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:191-192` |
| 業務屬性與部門歸屬 | 不明(`SAL051` 的主人不在 CLS) | CLS 只 `SELECT`;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:490-494` |
| 「誰可以查誰」的權限資料 | CRM | `CRM002A` 只被 `CLSR001_PO.GetInitData` 讀出來當過濾清單;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:118-137` |
| 基金主檔、淨值、匯率 | OFD | `OFD081A` / `OFD300` 只讀;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:317-319` |
| 實際申購 / 贖回交易 | OFD | `OFD221A_V01` / `OFD251A` 等只在報表被 join 加總;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:889`、`:909` |
| 庫存(AUM)怎麼算出來的 | **版控外的 SP** | `CLS001` 的四個 AUM 欄只由 `S_TA_CLSB001_EXE` 寫,原始碼不在 repo;`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:53` |
| 代銷通路的客戶拜訪 | CAS | `cas.md §4.2`;CLS 這側只有 `CLSI001` 讀得到 `USAGE = '2'` 的那一半 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 直銷業務員(`SAL_CD` = `C`) | 建自己的潛在客戶(`CLSM001`)、填拜訪單(`CLSM002`)、印自己的清冊 | 建檔權限判斷在 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:504-510`;拜訪單只看得到自己建的,`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292` |
| 組長 / 部門主管(`SAL_CD` = `A` / `B`) | 同上,另外可以查到底下業務員的資料 | 可查範圍來自 `CRM002A`,`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:120-137`;`INQ_EMP_NO = 'ALL'` 代表整個機構都看得到 |
| 助理 / 交割 / 其他(`SAL_CD` = `D`~`F`) | **只能看不能改**,一進維護頁就跳訊息並鎖住三個鈕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:369-376`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:375-382` |
| 覆核者 | 對 `CLSM001` / `CLSM002` 做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |
| 作業人員 | 跑 `CLSB001` 重算庫存、用 `CLSB002` 調兩個門檻 | 兩支 B 畫面都是人工按「執行」,沒有排程 |

**注意:除了 `SAL_CD` 那條判斷與 `CRM002A` 的可查清單之外,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3`)。

### 0.5 全域開關

repo 內**沒有**任何 CLS 專屬的 `.config` 開關。兩支 `App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:15`(`CLSM001` → `CLS001` / `PR_NO`)、`:22`(`CLSM002` → `CLS002` / `CLL_NO`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:16`、`:23` |
| `formstyle` | `CLSB001` / `CLSB002` / `CLSI001` 宣告為 `OneStep`;兩支 R 宣告為 `Report` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:29`、`:47`、`:53`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/App.config:9` |

三個要記住的:

- **`CLSM002` 沒有宣告 `detailtable`**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:19-25`),但 PO 宣告了三張明細(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:45-47`)。設定檔與程式不一致,**以程式為準**——這跟 CAS 那邊一模一樣(`cas.md §0.5`)。

- **兩支 R 畫面在兩個 `App.config` 裡各宣告一次**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:6-7` 與 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/App.config:3-4`)。R 畫面住在 `.Report` 專案(`architecture.md §6.5`),主專案那兩行是複製殘留。

- **業務參數不在 config,在資料表**:交通費上限 `TRFF_LMT` 與未過試用期應完成次數 `NEED_TM` 存在 `CLS012`,靠 `CLSB002` 畫面改(§6.2)。

`TargetFramework` 側:兩個 `App.config` 都宣告 `.NETFramework,Version=v4.8`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:57`),而五支 PO 檔頭都留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡(例 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:5`)——跟 CAS 同一批逐檔改的。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CLS 模組的四塊:潛在客戶維護、拜訪單維護、兩支批次、兩支報表
圖中文字:A 直銷潛在客戶(四眼) / CLSM001 / CLS001 潛在客戶主檔 / BMS001A / 有戶號就改抓受益人 / SAL051 / SAL_CD 決定能不能建檔 / CRM002A / 可查的機構與員編 / B 拜訪單(四眼 · 一主三明細) / CLSM002 / CLS002 拜訪單 / CLS003 / 拜訪重點與內部支援 / CLS004 / 推薦基金 / CLS005 / 新產品需求 / OFD300 / 匯率換台幣 / C 批次 / CLSB001 / S_TA_CLSB001_EXE 快照 / CLS001H + CLSB001 表 / 每次執行留一版 / CLSB002 / 改 CLS012 兩個門檻 / D 報表(取數全部繞開 A 與 B 的 PO) / CLSR001 / 9 支 rpt · 走 SP / S_TA_CLSR001_GET_n / 原始碼不在 repo / CLSR002 / 13 支 rpt · 自組 SQL / CLS001H 快照當主檔 / 報表看的是批次日的樣子
```

*圖:圖 1 全景。CLS 只有兩條業務線(潛在客戶、拜訪單),兩者靠 `PR_NO` 相連。橘色虛框是會咬人的地方:建檔權限來自別的模組的 `SAL051`、報表讀的是 `CLS001H` 快照而不是現值。黑箱是無原始碼或不屬於 CLS 的東西。*

看圖的三個重點:

1. **兩條業務線靠 `PR_NO` 相連,沒有程式呼叫關係。** `CLSM002` 不會叫 `CLSM001` 的畫面,但它會透過 `CLSM001_Pxy.Query()` 去查 `CLS001`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:159`)——是唯一一處跨畫面呼叫。

2. **報表那一排與維護那一排是斷的。** `CLSR001` 的資料全部來自版控外的 SP;`CLSR002` 自己組 SQL,但主檔讀的是 `CLS001H` 快照。所以**報表數字與維護畫面寫進去的值之間,在 repo 內看不到直接關係**(§7)。

3. **`CLSR001_PO.GetInitData` 是全模組的權限來源。** 兩支 M、兩支 R 一共四個畫面的 `FormInitial` 都去呼叫它拿可查機構與員編(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:289-291`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:237-239`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:150-152`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:143-145`)。**一支報表的 PO 變成了模組的權限服務**,改它會同時影響四個畫面。

### 1.2 資料表關係

見 §2 節首的圖。要記住的是:

- **主明細的綁定靠 `dataid`,不是靠外鍵**(`architecture.md §3.3`),所以 `CLS002` 與三張明細一定一起送審、一起覆核。

- **`CLL_NO` 是在伺服器端才灌進明細的**。`CLSM002_PO_BeforeAdd` 取完單號後,把 `CLL_NO` 迴圈寫進 `model.DataEntity` 的每一張表(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:102-104`);修改時則由 UI 端做同一件事(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:483-485`)。**同一個動作有兩份實作,一份在伺服器一份在用戶端。**

- **`CLS001` 有兩個「入口形狀」**:寫入走 `CLS001`,查詢走 view `CLS001_V01`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188`)。view 的定義不在 repo(`DB/View/` 只有兩支,都不是它)。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。四個階段的分工:① UI 進畫面時決定能不能改、② UI 存檔前檢核、③ PO 的 `BeforeAdd` 取號、④ 框架跑四眼、⑤ PO 的 `After*` 寫跳號註記。**`CLSM001` 只掛了 `AfterAdd` / `AfterUpdate` 兩個事件而且兩個都是空的;`CLSM002` 掛了八個**(§4.2)。

### 1.4 批次 / 報表資料流

見 §6 與 §7 節首的圖。兩張圖合起來看會發現一條隱藏的相依鏈:`CLSB001`(人工按執行)→ `S_TA_CLSB001_EXE` → `CLS001` 的 AUM 欄 + `CLS001H` 快照 + `CLSB001` 表的 `EXEDATE`,而 `CLSR001` / `CLSR002` / `CLSM002` 的查詢**全部從最後那個 `EXEDATE` 起算**。

**沒跑 `CLSB001` 就沒有快照,沒有快照 `ISHIS` 那段 CTE 取不到 `QDATE`,整份報表空白。**這條相依沒有任何地方寫下來,也沒有任何檢查。

### 1.5 一日作業泳道

| 時段 | 誰 | 做什麼 | 畫面 |
|---|---|---|---|
| 隨時 | 業務員 | 新增 / 修改潛在客戶,送出四眼 | `CLSM001` |
| 隨時 | 業務員 | 拜訪回來後 30 天內補拜訪單(含重點、推薦基金、需求、交通費) | `CLSM002` |
| 隨時 | 覆核者 | 驗證 / 覆核 / 退回 | `CLSM001` / `CLSM002` |
| 日終或需要時 | 作業人員 | 指定庫存日期跑重算,產生當日快照 | `CLSB001` |
| 需要時 | 作業人員 | 調整交通費上限與應拜訪次數 | `CLSB002` |
| 需要時 | 業務員 / 主管 | 印清冊、拜訪記錄、統計、交通費明細 | `CLSR001` / `CLSR002` |
| 需要時 | 直銷單位 | 查 CAS 那套拜訪單裡屬於直銷的部分 | `CLSI001` |

**沒有任何時序限制寫在程式裡**——`CLSB001` 的庫存日期只被限制不可大於今天(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33`),其餘全靠人工約定。

## 2. 資料模型

```text
[圖] CLS 自有 5 張表的主明細結構,以及三張不在母體的表與兩張同名不同主的 A 尾表
圖中文字:CLS 自有的 5 張實體表(全部有四眼欄位) / CLS001 / 潛在客戶 · PK PR_NO / CLS002 / 拜訪單 · PK CLL_NO / CLS003 / PK CLL_NO+TOPIC_CODE / CLS004 / PK CLL_NO+FUND_ID / CLS005 / PK CLL_NO+SEQ / 不在母體、但程式會讀的三張 / CLS001H / CLS001 的歷史快照 / CLSB001 / 批次執行日 EXEDATE / CLS012 / 交通費上限與次數門檻 / CLS001_V01 / CLSM001 查詢用的 view / 外部唯讀(CLS 從不寫入) / BMS001A / 受益人主檔 / COD009 / 員工 / SAL051 / 業務屬性 / OFD081A / 基金 / OFD068A / 銷售機構 / CRM002A / 可查範圍 / COD006A / 代碼 / 名字像 CLS 但主檔在 CAS 的兩張(§8) / CLS001A / 客戶拜訪單 · 主檔 CASM002 / CLS002A / 拜訪單續頁 · 明細於 CASM002 / CLSI001 只讀 CLS001A / USAGE = 2 那一半
```

*圖:圖 2 資料表關係。上排是 `CLSM002` 的一主三明細(靠 `CLL_NO` 串,不是外鍵,見 §2.1)。中排三張橘色是掃描母體沒列、但程式一定會讀的表。最底下是本模組最容易誤會的地方:`CLS001A` / `CLS002A` 的主人是 CAS 的 `CASM002`,CLS 只有 `CLSI001` 去讀它,而且只讀 `USAGE` = 2 的那一半。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

兩支 M 畫面的宣告,逐字抄自 PO 建構子:

| 畫面 | 主檔 | 明細 | 錨點 |
|---|---|---|---|
| `CLSM001` | `CLS001` | —(無明細) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:53` |
| `CLSM002` | `CLS002` | `CLS003`、`CLS004`、`CLS005` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:44-47` |

**五張表全部是 CLS 自己的,沒有一張借別人的**——這點跟 CAS 完全相反(`cas.md §0.2` 說 CAS 有一半的維護畫面開在別人的表上)。

三支非 M 畫面的 PO **都沒有 `xTableMapping`**:`CLSI001_PO` 的那行被註解掉(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:41`,而且註解裡寫的是 `OFD701`,跟 CLS 無關,與 `cas.md §5.1` 記的 `CASI001` 同一份樣板);`CLSB001_PO` / `CLSB002_PO` 連註解都沒有,直接自己 `new Database("TA", ...)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:32`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:33`)。這是 I / B 型的通則,見 `architecture.md §6.3`。

另外兩支 M 的 PO 都用 `AddNVarCharColumns` 逐欄宣告哪些是 `NVARCHAR2`(存中文):`CLS001` 六欄(`PR_NAME`、`CMD_PERSON`、`NEED_POC`、`MAIL_ADDR`、`MAIL_ADDR_E`、`CNT_PERSON`,`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:54-59`)、`CLS002` 四欄、`CLS003` 兩欄、`CLS005` 兩欄(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:48-55`)。

**`CLS004` 一欄都沒宣告**,它確實也沒有中文自由輸入欄(基金名稱由 `OFD081A` 帶入)。**加中文欄位時記得補這一行**,否則寫進去會變問號。

### 2.2 主鍵與四眼欄位

五張表**全部有完整的 15 個四眼 / 稽核欄**(`DATAID`、`STATUS`、`CREATEID`/`CREATEDATE`、`UPDATEID`/`UPDATEDATE`、`ENTRYID`/`ENTRYDATE`、`VERIFYID`/`VERIFYDATE`、`APPROVEID`/`APPROVEDATE`、`REJECTID`/`REJECTDATE`、`DATAFLAG`),語意見 `architecture.md §3.5`。

主鍵從 `App.config` 與 xsd 的 `msdata:PrimaryKey` 反推:

| 表 | 主鍵 | 依據 |
|---|---|---|
| `CLS001` | `PR_NO` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:15` 的 `pkey="PR_NO"` |
| `CLS002` | `CLL_NO` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/App.config:22` 的 `pkey="CLL_NO"` |
| `CLS003` | `CLL_NO` + `TOPIC_CODE` | `CLSM002p0` 存檔前用 `TOPIC_CODE` 做重複檢查;`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:53-60`。**假設**:xsd 的 `TOPIC_CODE` 不可空且是單內唯一 |
| `CLS004` | `CLL_NO` + `FUND_ID` | 同理,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:97-104` 用 `FUND_ID` 做重複檢查 |
| `CLS005` | `CLL_NO` + `SEQ` | `SEQ` 是 xsd 內唯一不可空的整數欄,而且 UI 完全不碰它——由框架或 DB 產生。**假設** |

**注意:`CLS003` / `CLS004` / `CLS005` 的重複檢查在用戶端做,不在 PO。**繞過畫面(例如兩個視窗同時開)沒有第二道防線。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

#### `CLS001` — 潛在客戶主檔(56 欄,`CLSM001` 主檔)

| 群 | 欄位 → 中文名 |
|---|---|
| 識別 | `PR_NO` 潛在客戶序號(PK) · `BF_NO` 戶號 · `ID_NO` 統編/ID · `PR_NAME` 客戶姓名 · `PR_TYPE` 客戶來源 · `BF_SOURCE_CODE` 潛在客戶來源代碼 |
| 歸屬 | `AGENT_CODE` 銷售機構 · `EMP_NO` 業務員員工代碼 · `EMP_NAME` 歸屬業務員 |
| 風險與合規 | `RISK` 風險屬性 · `CTL_TRADE` 交易列管 · `IN_DATE` KYC生效日 · `TERMINATE_DATE`(xsd 未填,畫面標題是 KYC到期日期)· `REJ_POST` 失聯戶 · `REJ_SELL_CHK` 拒絕行銷 |
| 投資決策 | `CMD_PERSON` 決策者 · `NEED_POC` 績效要求 · `NEED_SIZE` 規模要求(億)· `INV_LIMIT` 投資比例上限(%)· `STOP_GAIN` 停利點(%)· `STOP_LOSS` 停損點(%)· `CUS_LV` 客戶等級 |
| 關係與聯絡 | `REL_BF_NO` / `REL_NAME` 主要關係戶戶號 / 姓名 · `CNT_PERSON` 聯絡人 · `MAIL_ADDR` / `MAIL_ADDR_E` 通訊 / 英文地址 · `EMAIL` · `OF_TEL` / `HM_TEL` / `FAX_TEL` / `CELL_PHONE` 四組電話(各自另有 `_AREA` 區域碼與 `_EXT` 分機) |
| 庫存(批次寫,畫面唯讀) | `ON_AO_AUM` 歸屬AO境內庫存 · `ON_AUM` 境內庫存 · `OF_AO_AUM` 歸屬AO境外庫存 · `OF_AUM` 境外庫存 |
| 四眼 / 稽核 | 15 欄,見 §2.2 |

四個 AUM 欄只由批次寫(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:491-494` 只塞值不回收)。

#### `CLS002` — 拜訪單主檔(39 欄,`CLSM002` 主檔)

| 群 | 欄位 → 中文名 |
|---|---|
| 識別 | `CLL_NO` 拜訪單號(PK)· `PR_NO` 潛在客戶序號 |
| 客戶屬性快照 | `EMP_NO` / `EMP_NAME` · `BF_NO` 戶號 · `ID_NO` 統編/ID · `PR_NAME` 客戶姓名 · `CUS_LV` 客戶等級 · `RISK` 風險屬性 · `IN_DATE` / `TERMINATE_DATE` KYC 生效 / 到期日 · `CMD_PERSON` 決策者 |
| 拜訪內容 | `MAIN_PERSON` 主談者 · `INT_INV` 客戶投資意願(不可空)· `EST_CALL_DATE` / `EST_CALL_TYPE` 預計拜訪日期 / 方式 · `ACT_CALL_DATE` / `ACT_CALL_TYPE` 實際拜訪日期 / 方式 · `CLL_MEMO` 拜訪記錄 |
| 交通 | `DEPARTURE` 出發地 · `DESTINATION` 目的地 · `TRAFFIC` 交通工具 · `KM` 公里數 · `TRAN_FEE` 交通費 |
| 四眼 / 稽核 | 15 欄 |

**「客戶屬性快照」那一群在畫面上全部唯讀**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:426-435`),值是查 `CLS001` 帶進來的(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:192-212`)。也就是**同一份客戶屬性同時存在 `CLS001` 與 `CLS002`,拜訪單存的是當下的快照,客戶之後改了不會回頭同步**。

#### 三張明細(欄位全部含 `CLL_NO` + 15 個四眼欄)

| 表 | 業務欄位 → 中文名 |
|---|---|
| `CLS003`(20 欄) | `TOPIC_CODE` 拜訪重點(`COD006A` 的 `CODE_SORT` = `D2`)· `TOPIC_OTH` 拜訪重點-其它(代碼 `99` 才開放)· `INTER_SUP` 內部支援(下拉 `603`)· `INTER_SUP_OTH` 內部支援-其他(代碼 `4` 才開放) |
| `CLS004`(22 欄) | `FUND_ID` 基金代碼 · `FUND_SH_NM` 基金名稱 · `FUND_CURRENCY` 計價幣別(兩者由 `OFD081A` 帶入)· `ALLOT_AMT_ORG` / `ALLOT_AMT` 預計申購金額(原幣 / 台幣)· `ALLOT_DATE` 預計申購日 |
| `CLS005`(19 欄) | `SEQ` 序號 · `COMPETITOR` 競爭對手(不可空)· `MEMO` 需求說明(不可空) |

#### 查詢結果集形狀(不是實體表)

`CLSM001Model.xsd` 除了 `CLS001` 之外還宣告五張只在畫面上顯示的表,對應維護頁的五個頁籤:

| DataTable | 內容 | 由誰填 |
|---|---|---|
| `CLS002`(4 欄) | 該客戶的拜訪紀錄一覽 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:147-155` |
| `tab2`(10 欄) | 推薦基金彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:309-331` |
| `tab3`(7 欄) | 新產品需求彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:356-372` |
| `tab4`(7 欄) | 內部支援彙總 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:397-417` |
| `tab5`(7 欄) | 拜訪重點次數統計 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:443-465` |
| `CLS0021`(4 欄) | **零引用**,全庫 grep 不到任何 `.cs` 用它 | 見附錄 E |

報表側的結果集:`CLSR001Model.xsd` 有 `T1` / `T2` / `T3` / `CRM002A`;`CLSR002Model.xsd` 有 `T0` / `T1` / `T3`。這些是「查詢結果集形狀」不是實體表(`architecture.md §5.5`)。

### 2.4 與其他模組共用的表

掃描器對本模組的結論是「**無跨模組共用表**」——`CLS001`~`CLS005` 沒有被任何非 CLS 的畫面當主檔或明細。這個結論是對的,但**不代表改這五張表沒有跨模組影響**,原因見 §8。

反過來,CLS **讀**了很多別人的表:

| 表 | 主人(推測) | CLS 怎麼用 | 錨點 |
|---|---|---|---|
| `BMS001A` | BMS | 有戶號時用它蓋掉 `CLS001` 的姓名 / 統編;查統編是否已開戶 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:263`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:207-208` |
| `COD009` | COD | 員工姓名、到職日、離職日、`UID_CODE` ↔ `EMP_NO` 換算 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:191-192` |
| `SAL051` / `V_SAL051` | 不明 | 業務屬性 `SAL_CD` 與部門 `SAL_DEPT_NO`(決定能不能建檔) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:491`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:57` |
| `CRM002A` | CRM | 「這個員編可以查哪些機構 / 哪些員編」 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:121` |
| `CRM003A` / `CAS004A` / `CLS001A` | CRM / CAS | 只有 `CLSI001` 讀 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106-112` |
| `CRM004` | CRM | 拜訪次數門檻(`NEED_CNT` / `VISIT_CNT` / `CALL_CNT`) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1289` |
| `OFD068A` · `OFD081A` / `OFD081` · `OFD300` | OFD | 銷售機構簡稱 · 基金名稱與幣別與 `PROF_TYPE` · 匯率 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:199-201`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:129-130`、`:318` |
| `OFD115A` · `OFD123A` · `OFD017A_V01` | OFD | 交易列管期間 · KYC 到期日 · 客戶分類(**join 進來但輸出欄位一個都沒用到**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:259-266`、`:270-272` |
| `OFD221A_V01` / `OFD221` / `OFD251A` / `OFD251` / `OFD252` / `OFD253` / `OFD254` | OFD | 第 6 種報表算申購 / 贖回金額 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:883-943` |
| `OFD302` / `OFD302A` / `OFD306` / `OFD306A` | OFD | 第 8 種報表算庫存 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1427` |
| `COD006A` / `CTL014` / `AA_USER` | COD / CTL / 平台 | 代碼說明 · `USERID` → 中文姓名 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:456-458`、`:409-411`、`:149` |

**這 20 幾張表 CLS 一張都不寫**(唯一的例外是 `CLS012`,那是 CLS 自己的,見 §6.2)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`CLS001`~`CLS005` 的 `STATUS` 由四眼引擎寫,值域是 `EVAStatusCode` 那 12 個常數(`architecture.md §3.10`),CLS 自己的程式**完全沒有比對過 `STATUS`**——全庫 grep `STATUS` 在 CLS 五支 PO 內只出現在 xsd 欄位與 `CLSI001` 的 `DefaultValue`。

唯一的字面值是 `CLSI001_PO` 給查詢結果集塞的 `"301"`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:360`)。這跟 `cas.md §2.5` 記的 `CASB001` 寫 `'301'` 是同一個值,可以互相佐證 `STATUS` 是 3 碼字串。**但 `CLSI001` 是唯讀查詢,這行 `DefaultValue` 只在「新增一列而沒給值」時生效,對查詢沒有作用**,是從 `CASB001` 樣板複製過來的死碼(§5.4)。

#### 本模組自己判斷的旗標值

| 欄位 | 值 | 語意(來源) | 錨點 |
|---|---|---|---|
| `SAL_CD` | `A` 部門主管 / `B` 組長 / `C` 業務員 / `D` 助理 / `E` 外交割人員 / `F` 其他 | **XML 註解直接寫出全部六個值**,是本模組唯一有完整值域文件的代碼 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479` |
| `ACT_CALL_TYPE` / `EST_CALL_TYPE` | `1` 親訪 / `2` 電訪 / `3` E-mail | `1` = 親訪由 UI 判斷式反推(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:95`);`2` / `3` 由 `tab5` 的欄位中文名「親訪次數 / 電訪次數 / E-mail次數」對應 `DECODE(ACT_CALL_TYPE, 1/2/3)` 反推(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:447-449`) |  |
| `TRAFFIC` | `2` = 自行開車(其餘不明) | 只有 `2` 會開放輸入公里數 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:713` |
| `TOPIC_CODE` | `99` = 其他 | 選 `99` 才開放「拜訪重點-其他」文字欄 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:94` |
| `INTER_SUP` | `4` = 其他 | 選 `4` 才開放「內部支援-其他」文字欄 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:73` |
| `AUM`(查詢條件,非欄位) | `1` 有庫存 / `2` 無庫存 | 轉成 `ON_AO_AUM + OF_AO_AUM > 0` 或 `= 0` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182` |
| `USAGE`(`CLS001A` 的欄) | `2` = 直銷(CLS)、`3` = 代銷(CAS) | `CLSI001` 硬寫 `'2'`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132`),`CASI001` 硬寫 `'3'`(`cas.md §5.3`)。**假設**:兩個值就是這兩種通路 |  |
| `INT_INV` | `Y` / `N` | 下拉來源是 `YesNoDataSrc` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:306-308` |
| `BF_COUNTRY_X` | `01` = 本國(其餘視為外國) | 只用在報表的姓名遮罩長度 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1489` |

#### 下拉代碼分類碼

CLS 用到 10 組,分類碼**全部寫死在程式裡**(`601` 客戶來源 · `602` 客戶等級 · `603` 內部支援 · `604` 庫存情況 · `605` 交通工具 · `606` 基金範圍 · `447` 拜訪方式 · `448` 往返 · `404` 風險屬性 · `D2` 拜訪重點),逐一對應見附錄 C.3。

**同一組 `447` 在 `CLSI001` 用了兩套下拉實作**:條件區用 `GetDropDownDataSrc`、grid 用 `GetDropDown9iDataSrc`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:284` 對照 `:287-288`)。這與 `architecture.md §2.7` 記的 `CASM001` 是同一個現象。

## 3. 畫面清冊

七支畫面,五支彈出視窗。**七支全部住在 `Dev/ATLAS.CLS/SOURCE/`(大寫 SOURCE),兩支 R 例外住在 `Dev/ATLAS.CLS.Report/Source/`(一般大小寫)。**

### 3.1 維護 M

| 代號 | 中文名(推測) | 六層 | 主表 | 明細 | 彈出視窗 |
|---|---|---|---|---|---|
| `CLSM001` | 潛在客戶維護 | 齊 | `CLS001` | — | `CLSM001p0`「受益人基本資料」(**目前叫不到,見附錄 E**) |
| `CLSM002` | 客戶拜訪單維護 | 齊 | `CLS002` | `CLS003` `CLS004` `CLS005` | `CLSM001p0`、`CLSM002p0`「目的/支援」、`CLSM002p1`「推薦基金」、`CLSM002p2`「批次新增拜訪重點」 |

### 3.2 查詢 I

| 代號 | 中文名 | 六層 | 主表 | 彈出視窗 |
|---|---|---|---|---|
| `CLSI001` | 直銷客戶查詢作業(**視窗標題直接寫在 `CLSI001p0`**) | 齊 | `CLS001A`〔共用 · 主人是 `CASM002`〕 | `CLSI001p0` 同名明細視窗 |

### 3.3 批次 B

| 代號 | 中文名(推測) | 六層 | 寫哪張表 | Service |
|---|---|---|---|---|
| `CLSB001` | 庫存重算與快照 | **齊,但 Model / View 是空的 DataSet** | `CLS001` 的 AUM 欄、`CLS001H`、`CLSB001`(由 SP 寫) | 無 |
| `CLSB002` | 交通費與拜訪次數門檻維護 | **缺 model / view** | `CLS012` | 無 |

#### `CLSB002` 的「六層不齊」是真缺,不是命名

掃描器對 `CLSB002` 回報「缺 model view」。查下去**確實沒有 `CLSB002Model.xsd` / `CLSB002View.xsd`,也沒有 `_9i` 版本**(`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/` 底下只有 `CLSB001Model.xsd`、`CLSI001Model.xsd`、`CLSM001Model.xsd`、`CLSM002Model.xsd` 四支)。這與 `architecture.md 附錄 D` 記的 `_9i` 假警報**不是同一回事**。

真正的原因是它**刻意借用別人的型別**,三層各借一個:

| 層 | 用的型別 | 錨點 |
|---|---|---|
| UI | `new CLSB001ViewVDB()` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:43` |
| Control | `Execute(CLSB001ViewVDB)` / `Query(CLSB001ViewVDB)`,泛型參數 `CLSB001ModelVDB` | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs:37`、`:132`、`:165` |
| PO | `model as BasicModelVDB`,連 CLS 的型別都不用 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:49`、`:180` |

而 `CLSB001Model.xsd` / `CLSB001View.xsd` 本身是**零張表的空 DataSet**(整份只有一個 `<xs:choice>` 空節點,`Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSB001Model.xsd:11-15`)。所以 `CLSB002` 借的其實是「一個什麼都沒有的殼」——它的資料全靠 `Util.Parameters` 進、`Util.Result` 出(§6.2)。

**結論:`CLSB001` 的 model / view 存在但是空的;`CLSB002` 的 model / view 真的不存在,靠借 `CLSB001` 的空殼運作。兩者都不是命名問題,而是「B 型畫面根本不需要 typed DataSet」這條通則的兩種表現**(`architecture.md §6.6`)。

### 3.4 報表 R

| 代號 | 中文名 | 六層(七層) | 取數 | rpt 數 |
|---|---|---|---|---|
| `CLSR001` | 業務員客戶清冊 / 客戶來源清冊 | 齊(`.Report` 七層) | SP `S_TA_CLSR001_GET_<值>` | 9 支 |
| `CLSR002` | 客戶拜訪記錄與統計 | 齊(`.Report` 七層) | 自組 SQL(1,535 行 PO) | 13 支 |

### 3.5 一眼看出差別的五件事

| # | 事實 | 為什麼要記住 |
|---|---|---|
| 1 | 只有兩支 M 有四眼;I / B / R 全部繞過 `BaseEVADaoPO` 自建 `Database` | 這三型不受四眼、交易、連線池治理(`architecture.md §6.7`) |
| 2 | `CLSI001` 查的是**別的模組的表** | 改 `CASM002` 的欄位會打到 `CLSI001`(§8) |
| 3 | 兩支 B 都沒有 WindowsService,也沒有排程 | 全靠人工按鍵;`CLSB001` 沒跑報表就空白(§1.4) |
| 4 | 22 支 rpt 集中在兩支 R 畫面,比例是全庫最高的之一 | 一支畫面十幾種版型,選項與版型的對應只寫在 UI 的兩個 `Dictionary`(§7.1) |
| 5 | `DB/` 底下**零**支 CLS 的 SP / Function / Trigger / View | 所有 SP、`CLS001_V01`、`F_TA_GET_DIRECT_EMPS` 都在版控外(附錄 B) |

## 4. 維護畫面(M)— 一支一節

```text
[圖] 兩支維護畫面從進畫面、UI 檢核、PO 取號到四眼各階段的卡控順序
圖中文字:① 進維護頁之前(兩支 M 共用同一段) / SetEMP_NO / 從 COD009 換員工代碼 / GetSAL_CD / SAL_CD 不是 A/B/C 就鎖三個鈕 / CLSR001 GetInitData / 拿可查機構與員編清單 / Sales 清單 / 空 = 不過濾 / ② 存檔前 UI 檢核(BeforeAdd / BeforeModify → DoValidate) / CLSM001 / 統編與姓名擇一必填 / CLSM002 / 親訪要填目的地與交通工具 / CLSM002 / 實際拜訪日不可未來 / 逾 30 天 / 明細至少一筆 / CLS003 / ③ PO 事件(BeforeAdd) / CLSM001 / GetPR_NO2 取號 · 重號重取 / CLSM002 / GetCALL_RPT_NO 取號 / 把 CLL_NO 灌進所有明細 / 一次寫回四張表 / 無次數上限 / do-while 可能卡死 / ④ 四眼(框架) → ⑤ After 事件 / Entry / 輸入 / Verify / 驗證 / Approve / 覆核 / CLSM002 八個 After / 只寫跳號註記 / CLSM001 沒掛 / 註記只在 M002
```

*圖:圖 3 兩支 M 畫面的四眼與卡控順序。①②在用戶端、③⑤在伺服器、④在框架。橘色虛框是三個要記住的地方:建檔權限由 `SAL051` 決定(§4.1)、拜訪日的 30 天回補期限(§4.2)、以及取號重試沒有次數上限(附錄 E)。*

兩支 M 共用一段「進畫面決定能不能改」的程式(§4.1 的權限段),然後各走各的。

### 4.1 `CLSM001` — 潛在客戶維護

#### 用途(推測)

業務員把還沒開戶(或已開戶但要列入追蹤)的客戶登錄成一筆潛在客戶,填來源、聯絡方式、投資決策條件與客戶等級;送四眼後成為 `CLSM002` 拜訪單的可選對象。**畫面有兩個頁籤(查詢 + 維護)**,維護頁再分五個子頁籤(基本資料 / 推薦基金 / 新產品需求 / 內部支援 / 拜訪重點),後四個是唯讀統計。

#### 進畫面時就決定的三件事

進 `FormInitial` 依序做三件事:(1) 用登入者的 `UserID` 去 `COD009` 換 `EMP_NO` 存進 `EMPNO`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:135-145`、`:277`);(2) 用 `EMPNO` 查 `SAL051` 的業務屬性,不是 `A`/`B`/`C` 就把 `blnCanKeyIn` 設 false(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:281-282` 配 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:482-521`);(3) 呼叫 `CLSR001_Pxy.GetInitData` 拿可查機構 / 員編清單設成下拉的 `Filter`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:289-327`)。

第 2 點的 SQL 值得看一眼:它取的是**部門代碼長度剛好 5 碼**的那些 `SAL051` 列,再用 `MAX(...) KEEP(DENSE_RANK FIRST ORDER BY SAL_CD DESC)` 取 `SAL_CD`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:490-494`)。`LENGTH(SAL_DEPT_NO) = 5` 是**寫死的〔客戶特定〕**,而 `DESC` 取的是字母**最大**的那個(`F` > `C` > `A`),也就是**最沒有權限的那個**;判斷式再用 `Contains` 比對 `A`/`B`/`C`(`:507`)。所以身兼 `C` 業務員與 `F` 其他的人會被判成 `F`,**不能建檔**。這是不是本意,程式裡看不出來。

#### 必填與存檔前檢核

`DoValidate()` 只有兩層(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:120-130`):

| 順序 | 檢核 | 結果 |
|---|---|---|
| 1 | `validatorManager1` 宣告式必填(哪些欄由 Designer 決定) | 阻擋 |
| 2 | 「統編/ID 及客戶姓名 必須擇一填寫」 | 阻擋 |

另外一道在欄位離開焦點時跑:`umskID_NO_Validating` 會拿統編去 `GetBMS001A` 問三件事(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:720-735` 配 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:257-297`):

| 情況 | PO 回什麼 | 使用者看到 |
|---|---|---|
| 這個統編已在 `CLS001` 有資料,而且是**自己**建的 | `AddResultRow(false, 1, "您已維護過此客戶")` | 阻擋 |
| 這個統編已在 `CLS001` 有資料,但是**別人**建的 | `AddResultRow(false, 1, "無維護此客戶權限")` | 阻擋 |
| 統編在 `BMS001A` 查得到戶號 | 把戶號塞進 `tab2`,回成功 | 自動把戶號填進畫面(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:155-162`) |

**注意這裡有個被停用的第四種情況**:原本「有多筆受益人時彈 `CLSM001p0` 讓使用者挑」以及「統編/ID 已存在,不可建為潛在客戶」兩段都被整段註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197`)。結果是 `HasData` 永遠是 false,底下那行 `e.Cancel = IsErr || (HasData && unumBF_NO.Enabled)`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:734`)後半段永遠不成立——註解寫的「不允許有 id 開戶卻沒帶入」這條規則**實際上沒有在擋**。同一支 PO 裡的 `ChkID`(統編重複檢查)也被整塊 `/* */` 註解(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:218-252`)。

還有兩個 `Validating` 整段被註解:戶號(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:707-719`)與客戶姓名(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:736-745`)。

#### 有戶號與沒戶號是兩種不同的資料

`GetData()`(按新增 / 修改前把畫面塞回 row)依戶號分成兩條路(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:51-92`):

| 情況 | 做什麼 |
|---|---|
| **沒填戶號** | 姓名、來源、聯絡人、地址、E-mail、四組電話全部從畫面收 |
| **有填戶號** | 上面那 15 個欄位**全部清成空字串**,改由查詢時 join `BMS001A` 帶出來 |

也就是說**同一張表的同一組欄位,對「已開戶」的客戶是刻意留白的**。看到 `CLS001.PR_NAME` 是空字串不代表資料有問題,要去看 `BF_NO`。

另外,從「沒戶號」變成「有戶號」時(補戶號),UI 會塞一個 `COM` 參數進 `Util.Parameters`,註解寫「補戶號要重算 AUM 和等級」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75`)。**但 PO 端接這個參數的 `AfterAdd` 已整段註解**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:99-123`),所以這個參數現在**送出去沒有人接**——補完戶號的庫存與等級要等下一次 `CLSB001` 才會更新。

#### 查詢條件與「看得到誰」

`BeforeSearchButtonClicked` 收 11 個條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:517-543`),其中三個會影響可見範圍:

| 條件 | 行為 | 錨點 |
|---|---|---|
| 有選業務員 | `EMP_NO = <值>` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:522-523` |
| 沒選業務員但 `Sales` 清單不空 | `EMP_NO IN (<清單>)` | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525` |
| 沒選業務員而且 `Sales` 是空的 | **不加任何員編條件 → 看得到全部** | 同上的 else 不存在 |

PO 端把 `IN` 那條改寫成 `AND (C.LEAVE_DATE IS NOT NULL OR <員編條件> OR CLS001.EMP_NO IS NULL)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:172-173`)——**離職者的客戶與「公單」(`EMP_NO` 為 null)一律看得到**。單選業務員時則走另一段字串串接(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:206-213`),邏輯相同但寫法不同,而且是把值直接串進 SQL(附錄 E)。

「庫存情況」那個條件是全模組唯一會**靜默濾掉資料**的地方:

```
選「有庫存」→ AND ON_AO_AUM + OF_AO_AUM > 0
選「無庫存」→ AND ON_AO_AUM + OF_AO_AUM = 0
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182`)。這兩欄可空,Oracle 裡 `NULL + 0` 還是 `NULL`,`NULL > 0` 與 `NULL = 0` 都是 UNKNOWN,**所以還沒跑過 `CLSB001` 的新客戶無論選哪一個都查不到**,而且沒有提示。詳見附錄 E。

#### 「公單」規則

查到資料進維護頁時,`EMP_NO` 是不是 null 決定兩個鈕(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:426-429`):

```
ButtonDeleteEnable = 明細筆數 == 0 && EMP_NO 不為 null
ButtonModifyEnable = EMP_NO 不為 null
```

註解直接寫「只要有一筆明細就不可刪或公單不可刪除」「公單不可修改」。**「公單」= `EMP_NO` 為 null 的客戶**,所有人都查得到、誰都不能改。這條規則只存在於這兩行,沒有任何 UI 提示。

#### 四眼各階段附加動作

| 事件 | 內容 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetPR_NO2()` 取潛在客戶序號,重號就重取 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:85-89` |
| `BeforeSelect` / `BeforeGetToDoData` / `BeforeGetMaintainData` | 三個都改寫主檔 SQL(同一支 `BuildMasterSQLString`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:126-142` |
| `AfterGetMaintainData` | 另外撈該客戶的拜訪紀錄填進 `CLS002` 頁籤 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:144-156` |
| `AfterAdd` / `AfterUpdate` | **整段被註解,實際什麼都不做** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:92-124` |
| `Verify` / `Approve` / `Reject` / `Delete` | **完全沒掛**——`CLSM001` 沒有跳號註記 | 對照 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:58-65` |

`CLSM001_Ctl.Add()` 覆寫成功訊息為「新增成功,潛在客戶序號:`<PR_NO>`」(`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM001_Ctl.cs:62-65`),**沒有檢查 `Result` 陣列長度**(與 `cas.md 附錄 E` 記的 `CASM001_Ctl` 同一個問題)。

UI 端**仍然掛著跳號一覽表的三個事件**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:569-583`),但 PO 端沒有 `SrNoCommentProcessor.AddCommentHistory`,所以註記只讀不寫。

#### 跨表更新

**沒有。**`CLSM001` 只寫 `CLS001` 一張表。五個頁籤的資料全部是 `SELECT`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:304-476`),而且是在使用者切到該頁籤時才去撈,撈過就不再撈(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:673-706`)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進維護頁 | `SAL051` 業務屬性不是 `A`/`B`/`C` | 永遠判斷 | 阻擋(鎖新增 / 修改 / 刪除三鈕 + 訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:369-376`、`:406-413` |
| 進維護頁 | 取 `SAL_CD` 出錯 | SQL 例外 | 警示(顯示例外訊息,**不擋**) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:284-287` |
| 進維護頁 | `EMP_NO` 為 null(公單) | 查到的是公單 | 阻擋(修改與刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:427-429` |
| 進維護頁 | 已有拜訪明細 | `ugrdCLS002` 有列 | 阻擋(刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:427` |
| 選業務員時 | 選到不在 `Sales` 清單且在職的人 | `Sales` 不空 | 阻擋(訊息「不可查詢此業務員」+ 清空) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:620-630` |
| 選業務員前 | 沒先填銷售機構 | — | 阻擋(訊息「請先輸入 '銷售機構'」) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:611-618` |
| 統編離開焦點 | 統編已被自己維護過 | `CLS001` 查得到且員編相同 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:273-274` |
| 統編離開焦點 | 統編被別人維護過 | `CLS001` 查得到但員編不同 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:275-276` |
| 統編離開焦點 | 有開戶卻沒帶入戶號 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197` |
| 存檔前 | 統編與姓名都空白 | 兩者皆空 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:125-126` |
| 查詢前 | 至少 3 個查詢條件 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:547-551` |
| 查詢時 | 庫存情況 | 選了有 / 無庫存 | 過濾(無提示,**AUM 為 NULL 的一律被濾掉**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182` |
| 查詢時 | 可查員編清單 | `Sales` 不空 | 過濾(無提示;離職者與公單不受限) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:172-173` |
| 查詢時 | `Sales` 是空的 | 取不到可查清單 | **靜默放大到全部資料** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525` |
| 取號時 | 序號重複 | `IsExistByData` 為真 | 記錄不擋(重取,**無次數上限**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:85-89` |

### 4.2 `CLSM002` — 客戶拜訪單維護

#### 用途(推測)

業務員每拜訪一次客戶就開一張拜訪單:記錄預計與實際的日期與方式、主談者、客戶投資意願、交通資訊與費用,以及三組明細(拜訪重點與需要的內部支援、當場推薦了哪幾檔基金與預計申購金額、客戶提出的新產品需求與競爭對手)。

#### 客戶怎麼帶進來

四個欄位(統編、戶號、潛在客戶序號、客戶姓名)任一個離開焦點,都會用同一支 `GetCLS001` 去查 `CLS001`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:660-683`):

| 查到幾筆 | 行為 |
|---|---|
| 1 筆 | 直接把客戶屬性塞進畫面並鎖住那四個欄位(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:192-212`) |
| 多筆 | 彈 `CLSM001p0` 讓使用者挑(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:181-186`)——**這是 `CLSM001p0` 全模組唯一還活著的呼叫點** |
| 0 筆 | `AddResultRow(true, 0, "查無資料")` → 訊息 + `e.Cancel = true` 留在原欄位 |

`GetCLS001` 一律附帶 `EMP_NO = <登入者員編>`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:158`),所以**只能對自己的潛在客戶開拜訪單**。

#### 必填與存檔前檢核

`DoValidate()` 一共七條(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:87-136`):

| # | 檢核 | 訊息 |
|---|---|---|
| 1 | 宣告式必填(含公里數,僅在啟用時) | 由 Designer 決定 |
| 2 | 實際拜訪方式 = 親訪(`1`)時「目的地」必填 | 「實際行程拜訪方式為親訪時「目的地」 為必填欄位」 |
| 3 | 同上,「交通工具」必填 | 「…「交通工具」 為必填欄位」 |
| 4 | 實際拜訪日期 ≥ 預計拜訪日期 | 「實際拜訪日期 必須 >= 預計拜訪日期」 |
| 5 | 實際拜訪日期不可大於 DB 系統日 | 「提醒: 無法預先維護客戶拜訪紀錄」 |
| 6 | 實際拜訪日期不可早於系統日 -30 天(含假日) | 「提醒: 已逾維護期限, 無法再維護客戶拜訪紀錄」 |
| 7 | `CLS003` 至少一筆;`CLS005` 的需求說明不可空白 | 「目的/支援 至少要有一筆資料」「需求說明 為必填欄位」 |

第 5、6 條是本模組最實質的業務規則:**拜訪單不能預先開,也不能補超過 30 天**。`-30` 寫死在程式裡(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:117`)〔客戶特定〕,而且**同一組判斷在 `udatACT_CALL_DATE_Validating` 又寫了一次**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738`),那一份只跳訊息、沒有 `e.Cancel`,屬於提早提醒;真正擋下來的是 `DoValidate`。**兩份判斷必須一起改**。

第 8 條原本有:「拜訪記錄必須再補充」(要求 `CLL_MEMO` 長度大於自動帶入的拜訪重點文字),已被註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134`),連帶產生那段文字的 `UpdMemo()` 整支方法內容也全被註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:141-149`)。

#### 交通費怎麼算

| 步驟 | 規則 | 錨點 |
|---|---|---|
| 1 | 實際拜訪方式選「親訪」才開放出發地 / 目的地 / 交通工具;出發地預設「公司」 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:645-658` |
| 2 | 交通工具選「自行開車」(`2`)才開放公里數;選任何交通工具都開放交通費 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:709-715` |
| 3 | **公里數 × 6 = 交通費**,自動帶出且可覆寫 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:717-723` |

每公里 6 元是**寫死的整數〔客戶特定〕**,而且**上限 `TRFF_LMT` 在這裡完全沒有被檢查**——`CLS012` 的上限值只在 `CLSR002` 的交通費報表被當成一欄印出來(§7.3),畫面不擋。

#### 三組明細怎麼進來

| 明細 | 進入方式 | 重複檢查 | 錨點 |
|---|---|---|---|
| `CLS003` 拜訪重點 | 雙擊 grid 新增列彈 `CLSM002p0`;或按鈕彈 `CLSM002p2` 一次勾選多筆 | `TOPIC_CODE` 不可重覆 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:586-605`、`:700-707`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:53-60` |
| `CLS004` 推薦基金 | 雙擊 grid 彈 `CLSM002p1` | `FUND_ID` 不可重覆 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:612-643`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:97-104` |
| `CLS005` 新產品需求 | grid 直接編輯(`GridLayoutADU`) | 無 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:285-286` |

**`CLS003` 的「修改既有列」被停用**:雙擊既有列的那段 `new CLSM002p0(dt, row)` 整行註解(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:602-603`),所以拜訪重點**只能新增與刪除,不能改**,而且雙擊沒有任何反應。

`CLSM002p1` 的推薦基金另有兩條規則:非台幣時呼叫 `CLSM002_PO.GetEX_RATE` 取 `OFD300` 最新匯率,`原幣 × 匯率` 四捨五入成台幣(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:52-77`、`:86-90`);預計申購日必須 ≥ 實際拜訪日期,而且必須是該基金的營業日(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:131-155`)。

匯率那段有個要注意的寫法:`Convert.ToDecimal(vdb.Util.Result[0].ReturnMessage.PadLeft(1, '1'))`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:65`)。`PadLeft(1, '1')` 只有在字串長度為 0 時才會補——也就是**查不到匯率時匯率靜默變成 1**,台幣金額 = 原幣金額,沒有任何提示。

#### 四眼各階段附加動作

`CLSM002_PO` 掛了 12 個事件,是全模組最完整的一支:

| 事件 | 內容 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetCALL_RPT_NO()` 取拜訪單號(重號重取),然後把 `CLL_NO` 灌進 `model.DataEntity` 的**每一張表的每一列** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:96-104` |
| `BeforeSelect` / `BeforeGetToDoData` | 改寫主檔 SQL | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:109-112`、`:138-141` |
| `BeforeGetMaintainData` | 主檔改寫 SQL;`CLS004` 另外 join `OFD081A` 補基金名稱與幣別 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:115-136` |
| `AfterGetMaintainData` | `SrNoCommentProcessor.GetCommentHistory` 讀跳號註記 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:335-340` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterReject` / `AfterResend` | 七個都只做一件事:`SrNoCommentProcessor.AddCommentHistory(<對應 EVAType>, SrNo.AllotNoForNfd, …)`,失敗就 `throw new ApplicationException("")` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:342-396` |

**七個 `throw` 的訊息全是空字串**,與 `cas.md 附錄 E` 記的 `CASM001_PO` 同一個問題(附錄 E)。

另外,四眼的按鈕在進維護頁時還會再收一次(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:464-466`):

```
ButtonDeleteEnable &= row.EMP_NO == EMPNO && row.CREATEID == this.UserID
ButtonModifyEnable &= 同上
```

也就是**只有「歸屬業務員是我」而且「建檔者也是我」才能改或刪**。`&=` 代表在框架已判定的權限上再收一層。

#### 查詢與「看得到誰」

`CLSM002` 的主檔 SQL 是全模組最複雜的一段(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:149-304`),三層 CTE:

| CTE | 做什麼 |
|---|---|
| `ISHIS` | 從 `CLSB001` 取「不晚於查詢迄日的最後一次批次日」`QDATE` 與「全部批次的最後一日」`MAXDATE` |
| `CLS` | `QDATE < MAXDATE` 時讀 `CLS001H` 快照,`QDATE = MAXDATE` 時讀 `CLS001` 現值,兩段 `UNION ALL` |
| `MYCLS001` | 再 join `BMS001A`,把交易列管(`OFD115A`)與 KYC 到期日(`OFD123A`)算出來 |

最後一段的 `WHERE` 裡有一條**硬條件**:

```
AND CLS002.CREATEID = :CREATEID          -- CREATEID 來自 PermissionInfo 的 UserID
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292`、`:300-301`)。**不管畫面上選了哪個業務員,查出來的永遠只有登入者自己建的拜訪單。**這條不在畫面上、沒有提示,而且與「選業務員」那個條件並存——選了別人只會查到 0 筆。

`MYCLS001` 那層還有一條:`WHERE CUS_LV IS NOT NULL`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:273`)。**客戶等級還沒算出來(沒跑過批次)的客戶,它的拜訪單查不到。**

三個明細條件(基金、拜訪重點、需求說明)是用 `CLL_NO IN (SELECT …)` 子查詢做的(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:153-164`),不會讓主檔重複。

#### 跨表更新

**四張表一起寫,沒有其他跨表動作。**`CLSM002` 不碰 `CLS001`(只讀),也不碰任何外部表。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 進維護頁 | `SAL051` 業務屬性不是 `A`/`B`/`C` | 永遠判斷 | 阻擋(鎖三鈕 + 訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:375-382`、`:408-415` |
| 進維護頁 | 歸屬業務員或建檔者不是自己 | 查到別人的單 | 阻擋(修改 / 刪除鈕 disable,無訊息) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:464-466` |
| 客戶欄離開焦點 | 該客戶不在自己的 `CLS001` 名單 | 查 0 筆 | 阻擋(訊息「查無資料」+ 停在原欄位) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:160-161` |
| 客戶欄離開焦點 | 查到多筆 | — | 詢問(彈 `CLSM001p0` 讓使用者挑) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:179-187` |
| 實際拜訪日離開焦點 | 未來日 / 逾 30 天 | — | 警示(**只跳訊息,不擋**) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738` |
| 存檔前 | 親訪但目的地空白 | `ACT_CALL_TYPE` = `1` | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:95-98` |
| 存檔前 | 親訪但交通工具空白 | `ACT_CALL_TYPE` = `1` | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:101-104` |
| 存檔前 | 實際拜訪日 < 預計拜訪日 | 有填實際日 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:106-110` |
| 存檔前 | 實際拜訪日 > DB 系統日 | 永遠判斷 | 阻擋〔客戶特定〕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:113-115` |
| 存檔前 | 實際拜訪日 < 系統日 - 30 天 | 永遠判斷 | 阻擋〔客戶特定〕 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:117-120` |
| 存檔前 | `CLS003` 一筆都沒有 | — | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:122-123` |
| 存檔前 | `CLS005` 的需求說明空白 | 有 `CLS005` 列 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:125-132` |
| 存檔前 | 拜訪記錄必須再補充 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134` |
| 明細彈窗 | 拜訪重點重覆 | 同 `TOPIC_CODE` 已存在 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:56-60` |
| 明細彈窗 | 推薦基金重覆 | 同 `FUND_ID` 已存在 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:100-104` |
| 明細彈窗 | 預計申購日 < 實際拜訪日 | 有填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:140-143` |
| 明細彈窗 | 預計申購日不是基金營業日 | 有填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:145-148` |
| 明細彈窗 | 未開推薦基金明細前先填實際拜訪日 | 實際拜訪日空白 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:614-620` |
| 明細彈窗 | 批次新增拜訪重點時一個都沒勾 | — | **無回饋**(視窗不關也不提示,見附錄 E) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:101-107` |
| 查詢前 | 實際拜訪日起迄只填一邊 | XOR 成立 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:316-320` |
| 查詢前 | 起 > 迄 | 兩邊都填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:321-325` |
| 查詢前 | 至少 3 個查詢條件 | — | **被註解,不執行** | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:359-363` |
| 查詢時 | 只看自己建的單 | 永遠 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:292` |
| 查詢時 | 客戶等級為 null | 客戶還沒被批次算過 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:273` |
| 查詢時 | 沒有任何批次紀錄 | `CLSB001` 表是空的 | 過濾(無提示,**整頁空白**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-179` |
| 取號時 | 單號重複 | `IsExistByData` 為真 | 記錄不擋(重取,**無次數上限**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:96-99` |

## 5. 查詢畫面(I)

本模組只有一支 `CLSI001`「直銷客戶查詢作業」。

### 5.1 結構:查的是別人的表

| 面向 | `CLSI001` | 對照 `CLSM001` |
|---|---|---|
| 介面 | `ICLSI001_PO`,不繼承任何東西 | `ICLSM001_PO : IEvaDataAccess` |
| 類別 | `: ICLSI001_PO`,沒有基底 | `: BaseEVADaoPO, ICLSM001_PO` |
| 連線 | 自己 `new Database("TA")` 與 `new Database("SWProduct")` | 由 `BaseEVADaoPO` 管 |
| 主檔宣告 | **整行被註解**,而且註解裡寫的是 `OFD701` | `xTableMapping("CLS001", "CLS001")` |
| Ctl 的 `InitializeVDBTypes()` | **完全沒有** | 有 |
| 查的表 | **`CLS001A`〔共用 · 主人是 `CASM002`〕** | `CLS001_V01` |

錨點:`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:21`、`:33`、`:35-36`、`:41`;`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:26-29`。

**這支畫面與 `CASI001` 是同一份樣板的兩個後代。**逐行對照就看得出來:兩支的 `_Ctl` 都只剩 `GetData()` 一個活方法、都把 `CLS002A` 的 `TransferTable` 註解掉(`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:102`、`:112`)、兩支 PO 都用 `" > = "` 這個寫法組起迄條件、都在查詢前塞一整排 `DefaultValue`。差別只有三個:

| 差別 | `CLSI001`(直銷) | `CASI001`(代銷) |
|---|---|---|
| 硬條件 | `USAGE = '2'` | `USAGE = '3'` |
| 員工範圍 | `JOIN TABLE(F_TA_GET_DIRECT_EMPS('<員編>'))` 表值函式 | 5 個員編寫死在 SQL 字串裡 |
| 代碼說明 join | 5 個 `COD006A`(`P3` / `20` / `P3` / `19` / `15`) | 10 個 `COD006A` |

### 5.2 查詢條件

畫面收 13 個條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:115-177`):四組起迄(客戶拜訪單號、潛在客戶序號、員工編號、受益人戶號)+ 實際拜訪日期起迄 + 五個下拉(實際拜訪方式、拜訪重點代碼、客戶等級、客戶投資意願、風險屬性)。五組起迄都有「填起不填迄就自動補成相同」的 UI 行為。

四組起迄在按查詢時都會檢查「只填迄」與「起 > 迄」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:68-107`),成立就阻擋。

### 5.3 會把資料濾掉而不提示的條件

#### (1) `USAGE = '2'` 硬條件

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132`。**`CLS001A` 裡不是直銷的那一半永遠查不到**,畫面上沒有這個欄位、也沒有提示。這是 CLS 與 CAS 分割同一張表的唯一機制(§8.2)。

#### (2) 表值函式決定看得到誰

```
JOIN TABLE(F_TA_GET_DIRECT_EMPS('{0}')) T ON CLS001A.EMP_NO = T.DEPT_EMP_NO
```

(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107-108`)。這是 `JOIN` 不是 `LEFT JOIN`,所以**函式回空集合時整份查詢回 0 筆**。函式本體不在 repo(`DB/Function/` 23 支裡沒有它),名字看起來是「取某員編直屬的員工清單」。

參數來源是 `QUERY_EMP_NO`,由 UI 從 `ClientBizUtility.GetEMP_INFO(UserID)` 回傳的逗號字串取第 2 段(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:118-124`)。**取不到就不加這個參數**,而 PO 端是 `.Rows.Find("QUERY_EMP_NO")).Value.ToString()` 沒有 null 檢查(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136`)——**沒有員工代號的使用者一按查詢就是 `NullReferenceException`,被 `catch` 吞成「執行失敗,請檢查」**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:387-392`),看不出真正原因。

而且參數是用 `string.Format` 串進 SQL 字串的,不是綁參數(附錄 E)。

#### (3) 起迄比較符號中間有空白 —— 8 處

```
strSQL += " AND CLS001A.CALL_RPT_NO > = " + "'" + Row.Value + "'";
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163`,同樣寫法在 `:174`、`:185`、`:195`、`:206`、`:216`、`:227`、`:237`。SQL 的 `>=` 是單一 token,中間不能有空白。**假設**:這 8 個條件只要有一個被加進去,整段 SQL 就會在 Oracle 端語法錯誤,被 `catch` 吞成「執行失敗,請檢查」;依據是 SQL 標準與 Oracle 的詞法規則,**無法在本機驗證**。與 `cas.md §5.3` 的結論一致——全庫只有 4 個檔有這個寫法,四支是同一份樣板的後代。

#### (4)~(6) 其他三個

| # | 現象 | 影響 | 錨點 |
|---|---|---|---|
| 4 | 實際拜訪日期用**字串比較**(`yyyyMMdd`)。注意這兩條沒有 `Opeartor == Equal` 的包裝、符號也是正確的 `>=` / `<=`,所以**只有日期條件會真的生效** | 只要有一筆存成別的格式(補空白、含分隔符號、空字串)就落在區間外 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:250`、`:266` |
| 5 | 五個 `COD006A` 說明 join 的分類碼寫死成 `P3` / `20` / `P3` / `19` / `15`;其中 `TRACE_CODE` 與 `INTRO_TYPE` **共用 `P3`**,要確認是不是複製貼上的錯 | 都是 `LEFT JOIN` 不會濾掉主檔,但分類碼改動時說明欄整片變空,使用者看到「代碼有值、說明空白」 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:115-129`、`:117` 與 `:123` |
| 6 | 五個下拉條件串成 `"AND CLS001A." + Row.Name + …`,**`AND` 前面沒有空白** | 前一段結尾是 `'`,Oracle 詞法可以斷開字串常數與關鍵字,**推測**不會出錯;靠運氣不是靠設計 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:282`、`:292`、`:303`、`:313`、`:323` |

### 5.4 取數之後做的事

PO 在 `LoadDataSet` 之前塞了 13 個 `DefaultValue`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:360-372`),包括 `STATUS = "301"`、四眼的 ID 欄全設成當前使用者、日期設成當下、`REJECTDATE` 設成 `1900/1/1`。

**這對唯讀查詢沒有意義**——這些是 `DataColumn` 的預設值,只在「新增一列而沒給值」時生效,而查詢不會新增列。它是從批次那份樣板複製過來的死碼,與 `cas.md §5.4` 的結論相同。

查無資料時回 `AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:378-381`)。

### 5.5 明細視窗 `CLSI001p0`

雙擊 grid 任一列會開 `CLSI001p0`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:233-248`)。它是**純唯讀展示**——`Load` 裡把 18 個控件全部 `Enabled = false` 或 `ReadOnly = true`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:48-67`),只有一個「離開」鈕。

三個要注意的地方:

1. **它是全模組唯一寫出「直銷」兩個字的檔案**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:1073`),§0.1 的業務推測主要靠它。

2. **塞值時完全沒有 null 檢查**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89`),`row.EST_CALL_DATE` / `row.TRAFFIC_FEE` 這種可空欄位一旦是 NULL,typed DataSet 會丟 `StrongTypingException`。對照 `CLSM001` 每一欄都寫 `if (!row.IsXxxNull())`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:457-490`)——同一個模組兩種寫法。

3. **控件名與塞進去的欄位對不起來**:`ucSTAFF_TYPE`(理專等級)被塞 `row.CUST_CLASS`(客戶等級)(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:87`),而畫面標題確實是「客戶等級」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.Designer.cs:489`)。標題對、控件名錯,改的人很容易搞混。

呼叫端在視窗關閉後會依 `DialogResult` 做 `row.EndEdit()` / `row.CancelEdit()`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:240-247`),但視窗裡沒有任何可編輯的控件,**這兩行是死碼**。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按查詢前 | 四組起迄只填「迄」 | 起空迄有值 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:70-71`、`:78-79`、`:86-87`、`:94-95` |
| 按查詢前 | 四組起迄的起 > 迄 | 兩邊都填 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:72-74`、`:80-82`、`:88-90`、`:96-98` |
| 按查詢前 | 實際拜訪日期起迄 | 同上 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:101-107` |
| 按查詢前 | 至少填一個條件 | — | **沒有這條檢核** | — |
| 查詢時 | `USAGE = '2'` | 永遠 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:132` |
| 查詢時 | 直屬員工清單 | 永遠(`JOIN` 不是 `LEFT JOIN`) | 過濾(無提示,空清單 → 0 筆) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107-108` |
| 查詢時 | 取不到員工代號 | `GetEMP_INFO` 回空 | **例外 → 訊息「執行失敗,請檢查」** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136` |
| 查詢時 | SQL 語法錯(`> =`) | 有帶任一起迄條件 | **假設**整個查詢失敗,訊息「執行失敗,請檢查」 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163` |
| 查詢時 | 日期用字串比較 | 資料格式不一致 | 過濾(無提示) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:250`、`:266` |
| 查詢時 | 代碼說明的分類碼寫死 | 分類碼改動 | 過濾(無提示,說明變空) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:115-129` |
| 查詢後 | 0 筆 | 無資料 | 警示 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:378-381` |
| 雙擊明細 | 欄位為 NULL | 任一可空欄是 NULL | **例外**(無保護) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89` |

## 6. 批次(B)與 WindowsService

```text
[圖] 兩支批次的資料流:CLSB001 叫 SP 重算庫存並留快照,CLSB002 改 CLS012 的兩個門檻
圖中文字:CLSB001 庫存與快照重算 / 畫面只有一個欄位 / 庫存日期 · 不可未來 / S_TA_CLSB001_EXE / WNAV_DATE + WUSERID / CLS001 的 AUM 欄 / 四個庫存欄被重算 / CLS001H + CLSB001 / 當日快照留一版 / 同一支 SP 本來也掛在 CLSM001 存檔後,已整段註解 / CLSM001 AfterAdd / 整段被註解 / 補戶號時的 COM 參數 / UI 還在塞,PO 不再用 / 結果 / 補戶號後庫存要等下次批次 / CLSB002 交通費與拜訪次數門檻 / 畫面兩個數字 / 上限(元) / 應完成次數 / Query 先讀現值 / SELECT * FROM CLS012 / Execute / UPDATE CLS012 無 WHERE / CLSR002 報表 / RPS6 與 RPS9 讀這兩個值 / 共同點:人工按鍵觸發 · 無四眼 · 無 WindowsService · 直接改正式表
```

*圖:圖 4 批次資料流。兩支都沒有排程、沒有 WindowsService,只能由人在畫面上按「執行」。橘色虛框是三個陷阱:`CLSM001` 存檔後重算庫存那段已整段註解、`CLSB002` 的 UPDATE 不帶 WHERE、以及 `CLS012` 的兩個值被報表當常數讀(附錄 E)。*

**本模組兩支 B 畫面,沒有任何 WindowsService,也沒有排程。**`Dev/ATLAS.CLS/` 底下沒有 `WindowsService` 資料夾,掃描母體的 Service 數是 0。兩支都只能由人在畫面上按「執行」。

### 6.1 `CLSB001` — 庫存重算與快照(推測)

#### 觸發與輸入

畫面只有一個欄位「庫存日期」,預設今天,**最大值限制為今天**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33`、`:38`)。按執行時把它轉成 `yyyyMMdd` 放進 `BAL_DATE` 參數(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:41-45`)。

#### 做什麼

PO 的 `Execute` 只做一件事:開交易、叫 SP、commit(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:45-89`):

```
S_TA_CLSB001_EXE(WNAV_DATE => <庫存日期>, WUSERID => <登入者>)
```

**SP 原始碼不在 repo**(`DB/SP/` 83 支裡沒有它),所以它到底寫了哪些表只能從呼叫端與其他 SQL 反推:

| 證據 | 推論 |
|---|---|
| `CLSM001` 的 AUM 四欄畫面唯讀,而且沒有任何 UPDATE 走 PO | `CLS001.ON_AO_AUM` / `ON_AUM` / `OF_AO_AUM` / `OF_AUM` 由這支 SP 寫 |
| `CLSM002` 與兩支 R 都從 `CLSB001` 這張表取 `EXEDATE` | SP 每跑一次就在 `CLSB001` 表插一列執行日 |
| 同樣那段 CTE 在 `EXEDATE < MAXDATE` 時讀 `CLS001H` | SP 每跑一次會把 `CLS001` 整批複製一份到 `CLS001H` |
| `CLSM002` 的查詢有 `WHERE CUS_LV IS NOT NULL` | `CUS_LV`(客戶等級)也是這支 SP 算出來的 |
| `CLSM001` 被註解的 `AfterAdd` 呼叫的也是這支 SP,而且多傳一個 `WBF_NO` | SP 支援「只重算一個戶號」的模式 |

**注意畫面代號 `CLSB001` 同時是一張表的名字。**`FROM CLSB001` 出現在 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:177-178` 與 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:50-51`。這張表不在掃描母體裡(母體只收被 `xTableMapping` 宣告的表),但**它是整個模組查詢與報表的起點**。

#### 失敗處理

`catch` 分兩路(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:69-81`):

| 情況 | 行為 |
|---|---|
| 例外訊息含 `-20001` | 切 `ex.Message.Split(':')[1]`,再截到 `"ORA-"` 之前,當成「執行失敗:<業務訊息>」 |
| 其他 | 把 `ex.ToString()` **整串當成結果訊息**塞給使用者 |

第一路是「SP 用 `RAISE_APPLICATION_ERROR(-20001, …)` 回業務訊息」的慣用寫法,但**兩個字串操作都沒有防呆**:`Split(':')[1]` 假設一定有冒號、`Substring(0, IndexOf("ORA-"))` 假設一定找得到 `ORA-`。任一個不成立就在 `catch` 裡再丟一次例外。同樣的寫法也出現在 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:83-87`。

**沒有 rollback。**`tran.Commit()` 在 try 裡,失敗時 `finally` 只做 `Dispose(tran)`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:82-87`)。這行為依賴 `Database.Dispose(DbTransaction)` 會不會隱含 rollback,而那支沒有原始碼——**要現場確認**。

#### 與 M 畫面的關係

`CLSM001` 的 `AfterAdd` / `AfterUpdate` 原本會在補戶號時就地叫同一支 SP 重算單一戶號(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:99-123`),**整段已被註解**。UI 端塞 `COM` 參數那行還活著(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75`)。**現況是:補完戶號後庫存與客戶等級要等下一次 `CLSB001` 才會出現。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選日期 | 庫存日期不可大於今天 | — | 阻擋(控件 `MaxDate`) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:33` |
| 按執行前 | 有沒有選日期 | — | **沒有檢核**(空值會轉成空字串傳給 SP) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:44` |
| 按執行前 | 同一天重複執行 | — | **沒有檢核** | — |
| 執行時 | SP 回 `-20001` | SP 主動擋 | 警示(訊息由 SP 決定) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:71-75` |
| 執行時 | 其他例外 | — | 警示(**把 `ex.ToString()` 給使用者看**) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:78` |

### 6.2 `CLSB002` — 交通費與拜訪次數門檻(推測)

#### 觸發與輸入

畫面上兩個數字欄:「每人月交通費上限(元)」`TRFF_LMT` 與「未過試用期應完成次數」`NEED_TM`(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.Designer.cs:140`、`:175`),還有一組「變更前 / 變更後」的對照顯示(`:218`、`:230`)。

進畫面會先 `DoSearch()` 把現值讀出來(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:75-78`),讀回來的兩個值用 `Result[0].ReturnRowCount` 與 `Result[1].ReturnRowCount` **靠位置取**(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:52-53`)。

#### 寫哪些表

```
UPDATE CLS012 SET TRFF_LMT = :TRFF_LMT, NEED_TM = :NEED_TM,
                  UPDATEID = :USERID, UPDATEDATE = SYSDATE
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53`。**沒有 `WHERE`**——這是本模組唯一的無條件 UPDATE。如果 `CLS012` 永遠只有一列就沒事,但程式裡沒有任何地方保證這件事;讀取那邊也是 `SELECT * FROM CLS012` 直接取 `Rows[0]`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:92-96`)。

`CLS012` **不在掃描母體**(沒有任何 PO 用 `xTableMapping` 宣告它),但它是兩支報表的參數來源:

| 欄位 | 誰讀 | 怎麼用 |
|---|---|---|
| `NEED_TM` | `CLSR002` 第 6 種報表(未過試用期) | `(SELECT NEED_TM FROM CLS012) NEED_TM` 當一整欄印出來,讓報表比對實際次數是否達標;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1001` |
| `TRFF_LMT` | `CLSR002` 第 9 種報表(交通費) | `(SELECT TRFF_LMT FROM CLS012) NEED_TM` —— **別名還是 `NEED_TM`**;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1504` |

兩個語意不同的值共用同一個結果集欄位名 `NEED_TM`(`CLSR002Model.xsd` 的 `T0` 有這一欄),**因為兩份 rpt 版型不同所以不會混**,但改欄位時很容易改錯邊。

**兩個值都沒有任何地方在「擋」。**交通費超過 `TRFF_LMT` 時 `CLSM002` 不會阻止;拜訪次數不足 `NEED_TM` 時也沒有任何畫面提示。它們純粹是**報表上的參考線**。

#### 失敗處理

`Execute` 的 `catch` 把 `ex.ToString()` 當結果訊息(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:68`),`finally` 一律 `dbTA.Dispose()`。**沒有交易**——`ExecuteNonQuery(cmd)` 不帶 `DbTransaction`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:60`),兩個欄位是一起改的所以影響有限。

輸入值用 `Convert.ToInt32(GetParamValue(...))`(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:56-57`),**空字串會丟 `FormatException`**,被 `catch` 轉成一長串 .NET 例外文字給使用者。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按執行前 | 宣告式必填 | 由 Designer 決定 | 阻擋 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:30-35` |
| 按執行前 | 數值範圍 / 上下限 | — | **沒有檢核**(0 或極大值都存得進去) | — |
| 進畫面 | `CLS012` 一列都沒有 | 表是空的 | **例外**(`Rows[0]` 無保護) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:96` |
| 進畫面 | 讀取失敗 | 例外 | **例外**(`Result[1]` 取不到,見附錄 E) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:53` |
| 執行時 | 輸入非數字 | 空字串 | 警示(`FormatException` 文字) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:56` |
| 執行時 | `CLS012` 有多列 | 資料異常 | **全部被改**(無 `WHERE`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53` |

## 7. 報表(R)

```text
[圖] 兩支報表畫面的選項如何對應到 22 支 rpt 版型,以及取數與取檔的兩條路
圖中文字:CLSR001 業務員客戶清冊(6 個選項 → 9 支 rpt) / 報表種類 6 選 1 / DataValue 6/7/2/3/4/5 / S_TA_CLSR001_GET_ + 值 / SP 名由參數串出來 / 三個 refcursor / T1 / T2 / T3 / RPS2~RPS9 / RPS1 沒有入口 / CLSR002 客戶拜訪記錄(10 個選項 + 兩組 A/B → 13 支 rpt) / 報表種類 10 選 1 / CheckedIndex 0~9 / RptType 字串 / 0A 0B 1 2 3 4 5A 5B 6 7 8 9 / Reflection 叫 GetRpt+值 / NonPublic 也找得到 / 12 個私有方法 / 一個選項可以開多個視窗(MultiPrint) / RptNumber 字典 / 一個 key 對一個陣列 / CLSR001 第 0/1/2 項 / 各開兩個視窗 / CLSR002 第 8 項 / 8B 先開 8A 後開 / 第 2 次不重查 / NeedParam = false / 共同點:rpt 檔名 = 畫面代號 + RPS + 號碼,由用戶端指定,伺服器照收 / SetQueryParameters / report_type 字串 / Util.ReportParameters[0] / 位置取值 / CRReportTransfer / 無原始碼 / 回傳 rpt 位元組
```

*圖:圖 5 報表與 22 支版型的對應。兩支 R 畫面用完全不同的分派方式:`CLSR001` 把選項值串進 SP 名,`CLSR002` 把選項值串進方法名用 Reflection 叫。橘色虛框是四個要注意的地方:`CLSR001RPS1` 沒有畫面入口、SP 名與方法名都由用戶端參數決定、以及多視窗時第二次之後不重新查資料(§7)。*

兩支 R 畫面掛 **22 支 `.rpt`**,是全庫比例最高的模組之一。兩支的分派方式完全不同,要分開讀。

### 7.1 22 支 rpt 掛在哪

#### `CLSR001` — 9 支,一個選項對一支 SP

「報表種類」是 6 選 1 的選項鈕,**選項的 `DataValue` 不等於 `CheckedIndex`**(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.Designer.cs:369-380`),而且取數用 `DataValue`、選 rpt 用 `CheckedIndex`,兩套並行:

| CheckedIndex | 報表中文名 | `DataValue` → SP | rpt(開啟順序) | 對外編號 |
|---|---|---|---|---|
| 0 | 業務員客戶清冊－總表 | `6` → `S_TA_CLSR001_GET_6` | `CLSR001RPS3`、`CLSR001RPS2` | CLSR001-1 |
| 1 | 業務員客戶清冊－明細表 | `7` → `S_TA_CLSR001_GET_7` | `CLSR001RPS3`、`CLSR001RPS4` | CLSR001-2 |
| 2 | 業務員客戶清冊－基金別 | `2` → `S_TA_CLSR001_GET_2` | `CLSR001RPS8`、`CLSR001RPS7` | CLSR001-3 |
| 3 | 業務員客戶清冊－當月壽星 | `3` → `S_TA_CLSR001_GET_3` | `CLSR001RPS9` | CLSR001-4 |
| 4 | 客戶來源清冊(A 總表 / B 明細表) | `4` → `S_TA_CLSR001_GET_4` | `CLSR001RPS5` | CLSR001-5 / -6 |
| 5 | 客戶來源清冊－明細表 | `5` → `S_TA_CLSR001_GET_5` | `CLSR001RPS6` | CLSR001-7 |

錨點:對應表 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:191-204`;rpt 檔名組法 `:323`;SP 名組法 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:57`。

**`CLSR001RPS1` 沒有任何畫面入口。**六個選項的 `RptNumber` 值域是 {2,3,4,5,6,7,8,9},`1` 不在裡面。這支 rpt 仍被編進組件(`Dev/ATLAS.CLS.Report/Source/CrystalReports/Report.CLS/CLSR001RPS1.rpt`),但沒有程式會去載它。**假設**:它是早期版本或給別的入口用的,依據是同目錄的 `S_TA_CLSR001_GET_1` 這支 SP 確實還被 `CLSR002` 用(見下)。

「對外編號」那一欄來自 `RptNumber2` 字典(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:198-204`),註解寫「秀給鳳滿看」,值是 `CLSR001-1`~`-7`,只當成報表上的 `REPORT_NO` 參數印出來〔客戶特定〕。

#### `CLSR002` — 13 支,一個選項對一個私有方法

「報表種類」10 選 1,其中第 0 項與第 5 項各多一組 A / B 子選項,合起來 12 種:

| rptType | 報表中文名 | PO 方法 | rpt(開啟順序) | 對外編號 |
|---|---|---|---|---|
| `0A` | 客戶拜訪記錄明細表－by業務員 | `GetRpt0A` | `CLSR002RPS0A` | CLSR002-1 |
| `0B` | 客戶拜訪記錄明細表－by銷售機構 | `GetRpt0B` | `CLSR002RPS0B` | CLSR002-2 |
| `1` | 客戶拜訪記錄明細表－by客戶 | `GetRpt1` | `CLSR002RPS1` | CLSR002-3 |
| `2` | 客戶拜訪記錄明細表－推薦基金 | `GetRpt2` | `CLSR002RPS2` | CLSR002-4 |
| `3` | 客戶拜訪記錄明細表－新產品需求 | `GetRpt3` | `CLSR002RPS3` | CLSR002-5 |
| `4` | 客戶拜訪記錄明細表－內部支援 | `GetRpt4` | `CLSR002RPS4` | CLSR002-6 |
| `5A` | 拜訪重點－by業務員 | `GetRpt5A` | `CLSR002RPS5A` | CLSR002-7 |
| `5B` | 拜訪重點－by銷售機構 | `GetRpt5B` | `CLSR002RPS5B` | CLSR002-8 |
| `6` | 客戶拜訪統計表－未過試用期 | `GetRpt6` | `CLSR002RPS6` | CLSR002-9 |
| `7` | 客戶拜訪次數及銷售統計表 | `GetRpt7` | `CLSR002RPS7` | CLSR002-10 |
| `8` | 拜訪客戶未完成總表及明細表 | `GetRpt8` | `CLSR002RPS8B`、`CLSR002RPS8A` | CLSR002-11 |
| `9` | 交通費明細表 | `GetRpt9` | `CLSR002RPS9` | CLSR002-12 |

錨點:對應表 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:186-210`;選項中文名 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.Designer.cs:608-627`;rpt 檔名組法 `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:286`。

**分派是用 Reflection 做的:**

```
var RptType = EVAStringHelper.GetParamValue(model, "RptType");
MethodInfo mi = this.GetType().GetMethod("GetRpt" + RptType,
                    BindingFlags.Instance | BindingFlags.NonPublic);
mi.Invoke(this, new object[] { model });
```

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:155-157`。**方法名由用戶端傳來的參數串出來,而且連 `NonPublic` 都找得到。**這與 `cas.md §7.3` 記的 `CASR002` 用 `if-else` 階梯是兩種完全不同的做法。好處是加報表不用改分派,壞處是:(1) 傳一個不存在的值 → `mi` 是 null → `NullReferenceException`,被 `catch` 轉成 `ex.ToString()` 給使用者;(2) 任何未來加進這個類別、簽名相符的私有方法都會變成可從用戶端呼叫。

### 7.2 兩支報表的取數路線完全不同

| 面向 | `CLSR001` | `CLSR002` |
|---|---|---|
| 取數 | 一支 SP,三個 refcursor(`OUTTB1` / `OUTTB2` / `OUTTB3` → `T1` / `T2` / `T3`) | **自組 SQL,1,535 行的 PO** |
| 主檔來源 | SP 內部(看不到) | `strCLS` 這段共用 CTE,讀 `CLS001H` 或 `CLS001` |
| 逾時 | `CommandTimeout = 0`(永不逾時) | 預設 |
| 參數傳法 | 把 `Util.Parameters` 整包迴圈丟進去,全部當 `Varchar2`,再手動把兩個改回 `Int32` | 逐段 `AddParam` |
| 另有 | `GetInitData` 供四個畫面查權限(§1.1) | `GetUidCode`(**不在介面上,死碼**) |

錨點:`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:56-79`;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105`;`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:113-139`。

`CLSR001_PO.GetData` 的參數處理值得看:它先把 `RptType` 從參數表刪掉(因為那是用來組 SP 名的,不是 SP 參數),再把剩下全部當字串綁,最後對 `IROI_S` / `IROI_E` 兩個特判成整數(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:60-69`)。**這兩個參數名寫死在 PO 裡**,UI 那邊只要漏塞任何一個就是 `KeyNotFoundException`;實際上 UI 是無條件塞的(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:309-318`),所以目前不會爆。

#### `CLSR002` 的共用 CTE:`strCLS`

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105` 是一段 `readonly string`,12 支方法有 11 支以它開頭。三層:

| CTE | 內容 |
|---|---|
| `ISHIS` | `SELECT MAX(EXEDATE) QDATE, MAX((SELECT MAX(EXEDATE) FROM CLSB001)) MAXDATE FROM CLSB001 WHERE EXEDATE <= :ACT_CALL_DATE_END` |
| `MYSAL051` | 從 `V_SAL051` 取每個員編的部門(`SAL_DEPT_NO LIKE 'S____'` 且 `SAL_CD IN ('A','B','C')`) |
| `CLS` | `QDATE < MAXDATE` → `CLS001H`;`QDATE = MAXDATE` → `CLS001`,兩段 `UNION ALL` |

**`CLSM002_PO` 有一份幾乎一樣但不完全相同的複製品**(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-273`),差別:

| 差別 | `CLSR002_PO.strCLS` | `CLSM002_PO.BuildMasterSQLString` |
|---|---|---|
| 部門來源 | `V_SAL051` 聚合成 `MYSAL051` | 直接 join `SAL051` |
| `CUS_LV` | `NVL(CUS_LV, ' ')` | 不做 NVL,外層另有 `WHERE CUS_LV IS NOT NULL` |
| 多帶的欄 | — | `CMD_PERSON`、`A.ID_NO`,再接一層 `MYCLS001` |
| `EXEDATE` 上限 | 綁參數 `:ACT_CALL_DATE_END` | **字串串接**,而且沒給日期時寫死 `'29991231'` |

**同一個「要讀快照還是現值」的判斷有兩份實作,改一邊漏一邊查出來的客戶清單就會不一致。**

### 7.3 逐支報表的取數重點

| rptType | 主要 join | 特別的地方 |
|---|---|---|
| `0A` / `0B` | `CLS` + `CLS002` + `CLS003` + `CTL014`(447)+ `COD006A`(D2)+ `OFD068A` | 先查明細再查一次「總計」,用 LINQ join 把總計欄位補回明細列(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:281-291`)。**`0A` 把 `CUS_LV` 條件加了兩次**(附錄 E) |
| `1` | 同上 | 用 `LEAD(B.CLL_NO) OVER (ORDER BY B.CLL_NO)` 判斷是不是同一張單的最後一列來去重計數(`:455-463`) |
| `2` | 多 join `CLS004` + `OFD081A` | 條件多一個 `FUND_ID`(`:572`) |
| `3` | 多 join `CLS005` | — |
| `4` | 多 join `CLS003` + `CTL014`(603) | 硬條件 `AND TRIM(INTER_SUP) IS NOT NULL`(`:680`) |
| `5A` / `5B` | 多 join `CLS003` + `COD006A`(D2) | 兩支差在 `GROUP BY` 的維度 |
| `6` | `OFD081A`+`OFD081`、`OFD300`、`OFD221A_V01`/`OFD221`/`OFD251A`/`OFD251`~`OFD254`、`CRM004` | 全模組最長的一段(約 200 行),算貨幣 / 非貨幣的申購與淨申購,再與 `CLS012.NEED_TM` 比對。硬條件 `COD009.TEST_YN = 'N'`(`:959`) |
| `7` | `CRM004` + `CLS002` | 查完主表**再叫一次 SP** `S_TA_CLSR001_GET_1` 填 `T3` 等級表(`:1258-1263`);硬條件 `AND TRIM(A.EMP_NO) IS NOT NULL`(`:1247`) |
| `8` | `CRM004` + `OFD306A` | 兩段查詢:總表填 `T0`、明細填 `T1`;明細的 `ORDER BY` 尾端接 `SORT` 參數(`:1471-1474`) |
| `9` | `CLS002` + `COD009` + `MYSAL051` + `OFD068A` + `CTL014`(605) | 硬條件 `WHERE TRAN_FEE > 0`;客戶姓名做遮罩;讀 `CLS012.TRFF_LMT`(`:1486-1520`) |

`9` 的遮罩規則寫死在 SQL 裡〔客戶特定〕:

```
CASE WHEN BF_COUNTRY_X = '01'
     THEN SUBSTRB(PR_NAME,1,2) || '＊＊'      || SUBSTRB(PR_NAME,7, LENGTHB(PR_NAME)-6)
     ELSE SUBSTRB(PR_NAME,1,2) || '＊＊＊＊＊' || SUBSTRB(PR_NAME,13,LENGTHB(PR_NAME)-12)
END
```

(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1488-1495`)。本國(`01`)遮 4 個 byte、外國遮 10 個 byte。**姓名 byte 數小於遮罩長度時第二段 `SUBSTRB` 的長度參數會是負數**,Oracle 會回 NULL,整個運算式變成「前 2 byte + 星號」——名字短的人看到的星號比名字還多。

### 7.4 多視窗列印(`MultiPrint`)

兩支畫面都覆寫 `DoPrint` / `DoPreview` 成 `MultiPrint(base.XXX)`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:65-75`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:56-64`)。邏輯:

1. 查字典拿到這個選項對應的 rpt 陣列。

2. 逐支跑 `todoPrint()`,第一支 `NeedParam = true`(真的去查資料),**第二支之後 `NeedParam = false`**。

3. `NeedParam = false` 時 `BeforePreviewOrPrint` 不塞查詢參數,`AfterPreviewOrPrint` 改成把上一次留下的資料 `Merge` 回來(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:316-327`)。

4. 任何一支查到 0 筆就停止,後面的不開。

註解寫「後面的報表先顯示,視窗再往上疊,故最前面的報表要最晚開」(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:184`),所以陣列裡的順序是**倒著寫的**——`{ 3, 2 }` 代表使用者最後看到的是 `RPS2`。

`CLSR001` 多一個變化:`NeedParam = (i == 0 || IsPrint)`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:87`)。**列印時每一支都重查一次,預覽時只查第一次。**同一份報表用預覽與用列印,取數次數不同——如果兩次取數之間資料變了,預覽與列印的內容會不一樣。

### 7.5 畫面端的檢核

#### `CLSR001`

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 生日起迄在選「當月壽星」時必填 | `CheckedIndex == 3` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:109-110` |
| 基金範圍在選「基金別」時必填 | `CheckedIndex == 2` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:111` |
| 報酬率起迄要嘛都填要嘛都不填 | XOR | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:115-117` |
| 生日起迄要嘛都填要嘛都不填 | XOR | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:118-120` |
| 報酬率起 > 迄 | 都填 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:123-125` |
| 生日起 > 迄(只比 `MMdd`) | 都填 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:126-128` |
| 選「境內基金」卻一檔都沒勾 | `ucomFUNDAREA == "1"` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:278-283` |
| 選業務員前要先填銷售機構 | — | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:524-531` |

選項連動:選「當月壽星」時客戶類型被鎖成 `"1"`(自然人)(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:417-424`);排序選項會隨「基金範圍」與報表種類整組換掉(`:429-517`)。

#### `CLSR002`

| 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|
| 戶號在選「by客戶」時必填 | `custBF_NO.Enabled` | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:116` |
| 實際拜訪日起 > 迄 | 有填起 | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:120-122` |
| 選業務員前要先填銷售機構 | — | 阻擋 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:398-405` |

選項連動(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:347-390`):第 0 項開 A/B 子選項、第 1 項開戶號、第 2 項開基金、第 5 項開另一組 A/B;第 6 項(未過試用期)與第 9 項(交通費)**應該**要鎖住客戶等級,但那段程式被包在 `if (RptSort.ContainsKey(CheckedIndex))` 裡面,而 `RptSort` 只有 0/1/2/3/4/8 六個 key ——**第 6 與第 9 項根本走不到那段,鎖不住**(附錄 E)。

日期迄日在第 6 項之後會被 disable,並自動把起日補成當月 1 號、迄日補成當月最後一天(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:72-84`、`:383-385`)。

### 7.6 rpt 檔怎麼送到用戶端

兩支 Ctl 的 `GetReportObject` 都是同一行(`Dev/ATLAS.CLS.Report/Source/Control/ReportControl.CLS/CLSR001_Ctl.cs:67-71`、`Dev/ATLAS.CLS.Report/Source/Control/ReportControl.CLS/CLSR002_Ctl.cs:54-58`):

```
string rpt = Convert.ToString(ClassData.Util.ReportParameters[0].ReportClass);
return CRReportTransfer.TransferFileByte(rpt);
```

`CRReportTransfer`(無原始碼,從呼叫端反推)。**報表類別名由用戶端傳入、用位置 `[0]` 取、伺服器照單全收**——與 `cas.md §7` 記的 `CASR001` 完全一樣,是全庫 R 型的通則(`architecture.md §6.5`)。

### 7.7 與維護資料的關係

| 問題 | 答案 |
|---|---|
| 報表看到的客戶清單是現值嗎? | **不一定**。查詢迄日早於最後一次批次日就是 `CLS001H` 快照(§0.2) |
| 報表看到的拜訪單是現值嗎? | **是**。`CLS002`~`CLS005` 沒有歷史表,永遠讀現值 |
| 報表的權限與維護畫面一致嗎? | **不一致**。維護畫面 `CLSM002` 硬限定 `CREATEID = 登入者`;報表只用 `CRM002A` 的可查清單過濾銷售機構與員編,沒有 `CREATEID` 條件 |
| `CLS012` 的兩個門檻改了報表會變嗎? | **會,立刻變**。它是 `SELECT` 子查詢,不是快照 |

## 8. 跨模組共用

### 8.1 CLS 自有的五張表:沒有人當主明細用

掃描器對 `CLS001`~`CLS005` 的跨模組欄位全部是空的,也就是**沒有任何非 CLS 的畫面把它們宣告成 `xTableMapping` 的主檔或明細**。這點與 CAS(一半的維護畫面開在別人的表上,`cas.md §0.2`)和 BMS(12 張配對表橫跨三個模組,`bms.md §2.2`)都不一樣——**CLS 是這批模組裡資料自主性最高的一個**。

但「沒被當主明細用」不等於「改了沒事」,三條要注意:

| 風險 | 說明 | 怎麼查 |
|---|---|---|
| 版控外的 SP | `S_TA_CLSB001_EXE` 會寫 `CLS001` / `CLS001H`;`S_TA_CLSR001_GET_1`~`_7` 會讀。**加欄位或改型別時這些 SP 不會編譯失敗,會在執行期才爆** | 只能請 DBA 撈 `USER_SOURCE` |
| `CLS001H` 必須同步 | 它是 `CLS001` 的歷史快照,兩張表的欄位一定要同形。`CLS001` 加欄位而 `CLS001H` 沒加,`UNION ALL` 那段會直接語法錯 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:62-104` |
| `CLS001_V01` 必須同步 | `CLSM001` 的查詢讀的是這支 view 不是表,新欄位不在 view 裡查詢就看不到 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` |

### 8.2 `CLS001A` / `CLS002A`:名字像 CLS,主人是 CAS

這是本模組最容易踩的誤會,**掃描母體沒有列出它們,但 `CLSI001` 每天都在讀**。

| 事實 | 證據 |
|---|---|
| `CLS001A` 的主檔畫面是 `CASM002`,不是任何 CLS 畫面 | `atlas_scan.py --table CLS001A` 回報「主檔於 `CASM002`」;`cas.md §4.2` |
| `CLS002A` 是 `CASM002` 的明細 | `atlas_scan.py --table CLS002A` 回報「明細於 `CASM002`」 |
| 兩張表的 xsd 定義在 **CAS 專案**裡 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM002Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASB001Model.xsd` |
| CLS 這側唯一的使用者是 `CLSI001`,而且唯讀 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:106` 只有 `SELECT`,全檔沒有 INSERT / UPDATE |
| CLS 這側連 `CLS002A` 都不用 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:102`、`:112` 的 `TransferTable` 被註解 |

**同一張 `CLS001A` 被五支畫面用,靠 `USAGE` 切成兩個世界**(CAS 那三支的細節見 `cas.md §8.3`):

| 畫面 | 模組 | `USAGE` 條件 | 動作 |
|---|---|---|---|
| `CASM002` | CAS | 由畫面決定 | 維護(四眼) |
| `CASI001` | CAS | 硬寫 `'3'` | 查詢 |
| `CASB001` | CAS | 無條件 | 查詢 + 直接 UPDATE |
| **`CLSI001`** | **CLS** | **硬寫 `'2'`** | **查詢** |

改 `CLS001A` 的欄位時,**`Dev/ATLAS.CAS/Source/Entity/` 與 `Dev/ATLAS.CLS/SOURCE/Entity/` 兩邊的 xsd 都要重生**,漏一邊就是靜默失敗(`architecture.md §5.4`)。

**反過來說:改 `CLS001`~`CLS005` 不會影響 CAS。**兩套是完全獨立的表,只是名字撞在一起。

### 8.3 CLS 依賴別人、別人不依賴 CLS

| 方向 | 內容 |
|---|---|
| CLS → 別人 | 讀 20 幾張外部表(§2.4),其中 `CRM002A`(可查範圍)、`SAL051`(建檔權限)、`CRM004`(拜訪次數門檻)、`CLS012`(兩個參數)是**四個會改變 CLS 行為的外部輸入** |
| 別人 → CLS | **全庫 grep 不到任何非 CLS 的 `.cs` 引用 `CLS001`~`CLS005`**;也沒有 `CLSxxx_Pxy` 被別的模組呼叫 |

唯一的例外是**模組內部的跨畫面依賴**:`CLSR001_Pxy.GetInitData` 被四個畫面呼叫(§1.1),`CLSM001_Pxy.Query` 被 `CLSM002` 呼叫。**改 `CLSR001_PO.GetInitData` 的回傳形狀會同時打到四個畫面的權限**,這是本模組最集中的單點。

### 8.4 共用的 UI 控件與下拉來源

下拉一律走 `GetDropDownDataSrc` / `GetDropDown9iDataSrc`(同一組 `447` 在 `CLSI001` 用了兩套,見 §2.5);拜訪重點走 `CodeDataSrc`,`CLSM002p2` 另外傳 `Dis = "99"` 排除「其他」(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:50-51`)。

四支共用 helper:`UidCodeDateSrc`(`UserID` → `EMP_NO`,`CLSM002` 直接呼叫 `CLSM001.SetEMP_NO` 這個靜態方法,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:225`)、`ClientBizUtility.GetEMP_INFO`(`CLSI001` 取員編,回逗號字串靠位置取)、`ClientBizUtility.GetFundBusinessDay`(`CLSM002p1` 檢查申購日,`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:138`)、`JumpSrNoUtility`(兩支 M 的跳號一覽表,`CLSM001` 只讀不寫)。`CLSM002` 的日期檢核取的是 **DB 端**時間 `SystemDateTime.GetSystemDate(DBServer)`,不是用戶端時間。

## 附錄 A. 資料表總表

### A.1 母體的 5 張實體表

| 表 | 欄位 | 四眼 | 主檔於 | 明細於 | 跨模組 |
|---|---|---|---|---|---|
| `CLS001` | 56 | Y | `CLSM001` | — | 無 |
| `CLS002` | 39(掃描器算 40) | Y | `CLSM002` | — | 無 |
| `CLS003` | 20(掃描器算 16) | Y | — | `CLSM002` | 無 |
| `CLS004` | 22(掃描器算 20) | Y | — | `CLSM002` | 無 |
| `CLS005` | 19(掃描器算 18) | Y | — | `CLSM002` | 無 |

括號內是 `atlas_scan.py --table` 回報的數字,與直接數 `CLSM002Model.xsd` 的 `xs:element` 不同。差異來自掃描器把 Model 與 View 的欄位做了合併去重,而兩邊不完全同形(`architecture.md §5.4`)。**以 Model xsd 為準**,因為那是伺服器側寫入用的形狀。

### A.2 母體之外、CLS 實際會動到的四張表

| 表 | 誰用 | 怎麼用 | 錨點 |
|---|---|---|---|
| `CLS001H` | `CLSM002`、`CLSR002` | `CLS001` 的歷史快照,與現值 `UNION ALL` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:73` |
| `CLSB001`(**表,不是畫面**) | `CLSM002`、`CLSR002` | 每次批次執行留一列 `EXEDATE`,是所有查詢的時間基準 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:50-51` |
| `CLS012` | `CLSB002`、`CLSR002` | 兩個參數 `TRFF_LMT` / `NEED_TM`,單列表 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53` |
| `CLS001_V01` | `CLSM001` | 查詢用的 view(定義不在 repo) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` |

**這四張一個都不在掃描母體裡**,因為母體只收被 `xTableMapping` 宣告的表(`architecture.md §5.5`)。改 `CLS001` 時前三張都要一起看。

### A.3 只讀的外部表(20 張)

`AA_USER`、`BMS001A`、`CAS004A`、`CLS001A`、`COD006A`、`COD009`、`CRM002A`、`CRM003A`、`CRM004`、`CTL014`、`OFD017A_V01`、`OFD068A`、`OFD081`、`OFD081A`、`OFD115A`、`OFD123A`、`OFD221`、`OFD221A_V01`、`OFD251`、`OFD251A`、`OFD252`、`OFD253`、`OFD254`、`OFD300`、`OFD302`、`OFD302A`、`OFD306`、`OFD306A`、`SAL051`、`V_SAL051`。用途見 §2.4。

### A.4 只存在於 SQL 字串裡的 CTE 名稱

`ISHIS`、`CLS`、`CLS2`、`MYCLS001`、`MYCLS002`、`MYSAL051`、`MYBMS001A`、`MYCOD`、`MYOFD081`、`MYOFD081V`、`MYOFD300`、`MYOFD302A`、`MYOFD306A`、`MYTRADE`、`MYTRADE2`、`MYROW_DATA`、`MYTRADE_SUM`。**這些是 `WITH` 子句的別名,不是表**,搜尋表名時會誤中。

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:零支

`DB/` 底下 `Function` 23 支、`SP` 83 支、`Table` 158 支、`Trigger` 13 支、`View` 2 支,**沒有任何一支與 CLS 相關**(檔名與內容都 grep 過)。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 類 | 名稱 | 誰呼叫 | 參數 / 回傳 |
|---|---|---|---|
| SP | `S_TA_CLSB001_EXE` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:53`;另有被註解的呼叫 `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:103` | `WNAV_DATE`、`WUSERID`(註解版多一個 `WBF_NO`);無回傳 |
| SP | `S_TA_CLSR001_GET_2`~`_7` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:57`(名字由參數串出) | 全部參數當 `Varchar2` 綁,除 `IROI_S` / `IROI_E` 改 `Int32`;三個 refcursor `OUTTB1`/`OUTTB2`/`OUTTB3` |
| SP | `S_TA_CLSR001_GET_1` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1258` | `ICUS_LV`;一個 refcursor `OUTTB` |
| Fn | `F_TA_GET_DIRECT_EMPS` · `F_GET_FND_PROF_TYPE` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:107` · `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:843` | 吃員編回 `DEPT_EMP_NO` 集合(表值函式)· 吃 `FUND_ID` 與 `'0'` 回 `PROF_TYPE` |
| View | `CLS001_V01` · `V_SAL051` · `OFD017A_V01` / `OFD221A_V01` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:188` · `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:57` · `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:270` | 各自表的查詢包裝 |
| 框架 | `CRReportTransfer.TransferFileByte` · `SerialNo.GetPR_NO2` / `GetCALL_RPT_NO` · `SrNoCommentProcessor` | 兩支 R 的 Ctl · 兩支 M 的 `BeforeAdd` · `CLSM002_PO` 的八個事件 | 回傳 rpt 位元組 · 取流水號 · 跳號註記(皆無原始碼,從呼叫端反推) |

**整個模組的「業務算式」(庫存怎麼算、客戶等級怎麼定、清冊怎麼組)全部在版控外。**這是讀本文時最大的限制。

## 附錄 C. 代碼對照

### C.1 有完整值域的:只有 `SAL_CD`

`A` 部門主管 / `B` 組長 / `C` 業務員 / `D` 助理 / `E` 外交割人員 / `F` 其他(`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:479`)。前三個可以建檔。

### C.2 從判斷式反推的

| 欄位 | 已知值 | 出處 |
|---|---|---|
| `ACT_CALL_TYPE` / `EST_CALL_TYPE` | `1` 親訪 / `2` 電訪 / `3` E-mail | §2.5 |
| `TRAFFIC` · `TOPIC_CODE` · `INTER_SUP` | `2` 自行開車 · `99` 其他 · `4` 其他 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:713`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p0.cs:94`、`:73` |
| `USAGE`(`CLS001A`) | `2` 直銷 / `3` 代銷 | §2.5 |
| `PR_TYPE` · `FUNDAREA` | `1` 自然人(當月壽星報表鎖住)· `1` 境內 / `2` 境外 / 其他=全部 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:424`、`:264-296` |
| `BF_COUNTRY_X` · `AGENT_ID` · `EX_CD` | `01` 本國 · `0`(`OFD068A` join 寫死)· `1`(匯率種類) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1489`、`:200`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:319` |
| `ALLOT_PROC_CODE` / `REDEM_PROC_CODE` | `2` / `7` / `3` / `5` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:895`、`:905`、`:915`、`:929` |
| `PROF_TYPE` · `TEST_YN` | `3` 貨幣型(其餘非貨幣)· `N` 非測試員工 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:975-980`、`:959` |

### C.3 下拉分類碼

`601` 客戶來源 · `602` 客戶等級 · `603` 內部支援 · `604` 庫存情況 · `605` 交通工具 · `606` 基金範圍 · `447` 拜訪方式 · `448` 往返 · `404` 風險屬性 · `D2` 拜訪重點 · `P3` / `20` / `19` / `15` (`CLSI001` 的五個說明 join)。完整對應見 §2.5。

### C.4 排序參數(報表)

`CLSR001` 的排序值是 `0`~`6`(戶號 / 客戶來源 / 境內歸屬AO / 境內總 / 境外歸屬AO / 境外總 / 生日),當成 `SORTID` 參數送給 rpt(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:207-213`、`:354`)。

`CLSR002` 的排序值是**欄位名字串**(`ACT_CALL_DATE`、`BF_NO`、`B.ACT_CALL_TYPE`、`-ALLOT_AMT`…),直接串進 SQL 的 `ORDER BY`(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:214-226`)。前面加 `-` 代表降冪(Oracle 的數值取負)。

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

`atlas_scan.py --module CLS` 的母體:畫面 7(B 2 / I 1 / M 2 / R 2)· 表 5 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 22 · Service 0。

| 類別 | 母體 | 本文已提及 |
|---|---|---|
| 畫面 | 7 | 7(100%) |
| 資料表 | 5 | 5(100%) |
| SP / Fn | 0 | —(母體是 0,實際有 9 支在版控外,見附錄 B) |
| rpt | 22 | 22(100%,§7.1 逐支列出) |

### D.2 母體沒列到、但本文寫了的東西

放進 meta `refcheck-ignore` 的:四張程式天天讀但沒被 `xTableMapping` 宣告的表(`CLS001H` / `CLSB001` 表 / `CLS012` / `CLS001_V01`)、9 支版控外 SP 與 Function、5 支彈出視窗(`CLSM001p0` / `CLSM002p0` / `CLSM002p1` / `CLSM002p2` / `CLSI001p0`,它們不是獨立畫面代號)、17 個 CTE 別名(避免讀者當表去找)、以及 6 張報表 join 到但不在索引的外部表(`OFD306` / `OFD306A` / `V_SAL051` / `AA_USER` / `OFD017A_V01` / `OFD221A_V01`)。

**`CLS001A` / `CLS002A` 兩張都在索引裡,不用 ignore**——它們是 CAS 的表,本文只是從 CLS 這側交代歸屬(§8.2)。

### D.3 母體列了、本文交代不足的

**沒有。**7 支畫面各有專節,5 張表各有欄位表,22 支 rpt 在 §7.1 逐支對應到畫面選項。

### D.4 標「假設」的地方總表

| # | 假設 | 依據 | 怎麼驗 |
|---|---|---|---|
| 1 | `CLS` 三個字母代表「直銷客戶」 | `CLSI001p0` 的視窗標題「直銷客戶查詢作業」 | 問使用者單位 |
| 2 | `USAGE` 的 `2` = 直銷、`3` = 代銷 | `CLSI001` 寫 `'2'`、`CASI001` 寫 `'3'`,兩支同一份樣板 | 查 `CLS001A` 實際資料分布 |
| 3 | `CLS003` / `CLS004` / `CLS005` 的主鍵 | 彈出視窗的重複檢查欄位 + xsd 的不可空欄 | 查 DB 的 constraint |
| 4 | `S_TA_CLSB001_EXE` 寫 `CLS001` 的 AUM、`CLS001H`、`CLSB001` 表、`CUS_LV` | 五條間接證據(§6.1) | 撈 SP 原始碼 |
| 5 | `> =` 這個寫法會讓整段 SQL 語法錯 | SQL 標準與 Oracle 詞法 | 連 DB 實測(與 `cas.md §5.3` 同一條) |
| 6 | `AND` 前面沒空白不會出錯 | Oracle 詞法可斷開字串常數與關鍵字 | 連 DB 實測 |
| 7 | `CLSR001RPS1` 是早期版本或別的入口用的 | 六個選項的值域不含 `1`,但同號 SP 仍被 `CLSR002` 用 | 問使用者單位 |
| 8 | `EX_RATE <= :ACT_CALL_DATE_END` 這條件實際等於沒作用 | `EX_RATE` 是數值、繫結值是 `yyyyMMdd` 字串,隱含轉型後所有匯率都小於它 | 查 `OFD300.EX_RATE` 的型別與值域 |
| 9 | `CLS012` 只有一列 | `SELECT * … Rows[0]` 與無 `WHERE` 的 UPDATE 都這樣假設 | 查 DB |
| 10 | `Database.Dispose(DbTransaction)` 會隱含 rollback | `CLSB001_PO` 沒有任何 `Rollback()` 呼叫 | 反編譯框架 DLL 或實測 |

## 附錄 E. 讀本文時要注意的地方

按嚴重度由高到低。**每條都是讀碼直接看到的,不是推測**(標「假設」者除外)。

### E1 Oracle 三值邏輯:庫存條件會靜默濾掉新客戶 · 嚴重度 高

```
if (row.Value == "1") strSQL += " AND ON_AO_AUM + OF_AO_AUM > 0";
else if (row.Value == "2") strSQL += " AND ON_AO_AUM + OF_AO_AUM = 0";
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:179-182`。兩個 AUM 欄在 xsd 裡都是可空的,而 Oracle 的 `NULL + 0` 仍是 `NULL`,`NULL > 0` 與 `NULL = 0` 都是 UNKNOWN。

**影響**:還沒跑過 `CLSB001` 的新客戶(AUM 是 NULL),使用者選「有庫存」查不到、選「無庫存」也查不到,而且畫面不會提示。與 `cas.md 附錄 E` 記的 `CASB001_PO` 是同一型錯誤。修法是 `NVL(ON_AO_AUM,0) + NVL(OF_AO_AUM,0)`。

### E2 匯率條件拿數值欄比日期字串 · 嚴重度 高

```
LEFT JOIN OFD300 C ON A.FUND_CURRENCY = C.CRNCY_CD
                  AND C.EX_CD = '1'
                  AND EX_RATE <= :ACT_CALL_DATE_END
```

`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:861-864`。同一段的聚合是 `MAX(EX_RATE) KEEP(DENSE_RANK LAST ORDER BY CDATE)` —— 排序用的是 `CDATE`,可見**原意應該是 `CDATE <= :ACT_CALL_DATE_END`**,寫成了 `EX_RATE`。

**影響**(**假設**,依據見附錄 D.4 第 8 條):繫結值是 `yyyyMMdd` 八位數字字串,隱含轉型成 20250131 這種數字後,任何正常匯率都小於它,條件恆真——**第 6 種報表的匯率永遠取最新,不是取查詢期間的**。跨期間比較的金額會失真,而且完全沒有症狀。

### E3 `UPDATE` 不帶 `WHERE` · 嚴重度 高

```
"UPDATE CLS012 SET TRFF_LMT = :TRFF_LMT, NEED_TM = :NEED_TM, UPDATEID = :USERID, UPDATEDATE = SYSDATE"
```

`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:53`。`CLS012` 若不只一列,全部會被改成同一組值,而且**沒有交易**(`ExecuteNonQuery(cmd)` 不帶 `DbTransaction`)。讀取端也是直接 `Rows[0]`(`:188`),兩邊都假設「只有一列」但沒有人保證。

### E4 字串串接進 SQL(注入面) · 嚴重度 高

| 位置 | 串什麼 | 錨點 |
|---|---|---|
| `CLSI001_PO` | 登入者員編 → 表值函式參數 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:135-136` |
| `CLSI001_PO` | 8 組起迄條件 + 5 個下拉值 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:163`~`:323` |
| `CLSI001_PO` | `GetEmpNo` / `GetUidCode` 的 `UserID` / `EmpNo` | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:415`、`:446` |
| `CLSM001_PO` | 銷售機構 + 員編 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:208`、`:212` |
| `CLSM002_PO` | 銷售機構 + 員編 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:169` |
| `CLSM002_PO` | **實際拜訪日期迄日**串進 CTE | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:183` |
| `CLSR002_PO` | 銷售機構 + 員編(12 支方法各一份) | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:224`、`:229` 等 |
| `CLSR002_PO` | 排序欄位名串進 `ORDER BY` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:238` 等 7 處 |
| `CLSR002_PO` | `GetUidCode` 的 `EmpNo` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:117-119` |

值多半來自下拉或登入者,**不是自由輸入**,所以實際風險比看起來低;但 `CLSM002_PO:183`(日期)與 `CLSR002_PO` 的排序欄位是使用者可控的路徑。**同一支 PO 裡綁參數與串字串兩種寫法並存**(例如 `CLSM002_PO` 的 `:CREATEID` 是綁的、迄日是串的),是最容易誤判的地方。

### E5 可查員編清單沒有加引號,而且空清單會放大範圍 · 嚴重度 高

```
var emp = from CLSR001View.CRM002ARow r in vdb.UIView.CRM002A
          where !r.IsEMP_NONull() select r.EMP_NO;     // 沒有加引號
…
custEMP_NO_0.Filter = string.Format("LEAVE_DATE IS NOT NULL OR EMP_NO IN ({0})",
                                    string.Join(",", Sales.ToArray()));
```

`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:294-303`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:242-252`。**同一份程式在報表側是有加引號的**(`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:157`、`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:150`),兩支 M 沒加。`EMP_NO` 在 DataTable 裡是字串欄,`IN (028039,102736)` 這種寫法在 `DataTable.Filter` 會怎麼解讀要實測,但**兩邊寫法不一致本身就是 bug**。

同一段還有兩個問題:

1. **`OR` 沒有被括號包住**。`LEAVE_DATE IS NOT NULL OR EMP_NO IN (…)` 目前是整條 Filter,但只要框架或後人再 `AND` 一個條件上去,就會變成 `(A AND B) OR C`——與 `cas.md 附錄 E` 記的 `CASB001_PO` 同一型陷阱。

2. **`Sales` 是空的時候整段不執行**,而查詢時的 else 分支也不加員編條件(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:524-525`)——**取不到可查清單的人看得到全部資料**,這是「靜默放大」不是「靜默縮小」。

### E6 被註解掉但外殼還在的檢核 · 嚴重度 中

| 被停用的東西 | 外殼留下什麼 | 錨點 |
|---|---|---|
| `CLSM001` 統編重複檢查 `ChkID` | 整支方法用 `/* */` 包住,訊息「統編/ID 已存在, 不可重覆建檔」還在 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:218-252` |
| `CLSM001` 多筆受益人挑選 + 「不可建為潛在客戶」 | `HasData` 這個 `out` 參數永遠回 false,呼叫端的判斷式留著 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:175-197` 對照 `:734` |
| `CLSM001` 戶號與姓名的 `Validating` | 兩個事件方法整段註解 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:707-719`、`:736-745` |
| 兩支 M 的「至少 3 個查詢條件」 | `ValidateErrList.Clear()` 與 `if (Show())` 都還在,永遠不成立 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:547-551`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:359-363` |
| `CLSM001` 存檔後重算庫存 | `AfterAdd` / `AfterUpdate` 事件仍掛在建構子上,方法體全註解;UI 端仍塞 `COM` 參數 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:92-124` 對照 `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:71-75` |
| `CLSM002` 「拜訪記錄必須再補充」+ `UpdMemo` | 方法留成空殼,四個呼叫點全註解,`lenTopic` 永遠是 0 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:133-134`、`:141-149`、`:595`、`:603`、`:609`、`:705` |
| `CLSM002` 修改既有拜訪重點 | 雙擊既有列進 else 分支後**什麼都不做**,使用者以為壞掉 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:598-604` |
| `CLSI001` 的 5 人員編白名單 | 整段註解,而且註解裡那個判斷式 `A != x \|\| A != y` 恆真(同 `cas.md` 記的錯誤) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:142-153`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:253-275` |
| `CLSI001` 的 `TRACE_CODE` / `INVEST_CODE` 查詢條件 | 兩段註解,畫面上的下拉還在 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:329-347` |
| `CLSI001_Ctl` 的三個取值方法 + `DoExecute` | 全部註解,PO 端對應的介面宣告也註解 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSI001_Ctl.cs:45-91` |
| `CLSR001` 的 `uoptFUND` 選項群 | 控件還在 Designer 裡(`Visible = false`),事件方法整段註解 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:412-415`、`:559-569` |

### E7~E10 例外處理與取值方式 · 嚴重度 中

| # | 缺陷 | 影響 | 錨點 |
|---|---|---|---|
| E7 | `catch` 把 `ex.ToString()` 當成資料值塞進 `Result` 回給使用者:`CLSM001_PO` 五處(`:293`、`:338`、`:379`、`:424`、`:472`)、`CLSM002_PO`(`:328`)、`CLSB001_PO`(`:78`)、`CLSB002_PO`(`:68`、`:104`)、`CLSR001_PO`(`:90`、`:146`)、`CLSR002_PO`(`:162`) | 使用者看到完整 .NET 堆疊字串,真正的錯誤沒被歸類。反過來 `CLSI001_PO` 回固定的「執行失敗,請檢查」又什麼線索都沒有——**同模組兩種極端** | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:293`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSI001_PO.cs:390` |
| E8 | `CLSM002_PO` 七個 `After*` 事件全是 `throw new ApplicationException("")` —— **空訊息** | 跳號註記寫失敗時使用者只看到空白訊息,而且四眼動作整個 rollback,現場查不出原因(同 `cas.md 附錄 E.3` 的 `CASM001_PO`) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:348`、`:356`、`:363`、`:370`、`:381`、`:388`、`:395` |
| E9 | **靠位置取值,沒有長度檢查**:兩支 M 的 Ctl 取 `Result[0]`;`CLSB002` UI 取 `Result[0]` **與 `Result[1]`**(`Query` 失敗時只有 1 列 → 直接爆);`CLSR001_PO` 取 `Parameters[0]` 當 `USERID`;兩支 R 的 Ctl 取 `ReportParameters[0]`;`CLSB002_PO` 取 `row[0]` / `row[1]` **靠欄位順序**;`CLSI001` 取 `GetEMP_INFO` 回傳字串的 `Split(',')[1]` | `CLS012` 改欄位順序兩個參數就對調;參數順序改了就取錯值 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM001_Ctl.cs:62-65`、`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSM002_Ctl.cs:62-65`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:52-53`、`Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB002_PO.cs:97-98`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:139`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001.cs:121-124` |
| E9b | `ex.Message.Split(':')[1]` 再 `Substring(0, msg.IndexOf("ORA-"))`,**兩個字串操作都沒防呆**(沒有冒號、或找不到 `ORA-` 就在 `catch` 裡再爆一次);兩處是複製品 | 真正的 SP 業務訊息被二次例外蓋掉 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSB001_PO.cs:73`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs:85-86` |
| E10 | **有訊息但沒有 `return` / `Cancel`**:`udatACT_CALL_DATE_Validating` 對「預先維護」與「逾 30 天」都跳訊息卻不設 `e.Cancel`;實際靠 `DoValidate` 再擋一次,**同一條規則兩份實作**。另外 `GetSAL_CD` 失敗時只跳訊息、`blnCanKeyIn` 保持 false | 改一邊漏一邊會出現「提醒了卻存得進去」;DB 連不上時所有人都變成不能建檔,訊息是 SQL 例外文字 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:724-738`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:284-287` |

### E11 「第 6 與第 9 項要鎖住客戶等級」這段程式走不到 · 嚴重度 中

```
if (RptSort.ContainsKey(uoptREPORT_TYPE.CheckedIndex))
{
    …
    else
    {
        //要算未過試用期是否達成或交通費, 所以以下條件不能用
        ucomCUS_LV.Enabled = (CheckedIndex != 6) && (CheckedIndex != 9);
        …
    }
}
```

`Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR002.cs:361-379`。`RptSort` 只註冊了 key `0` / `1` / `2` / `3` / `4` / `8`(`:227-232`),**`6` 與 `9` 不在裡面**,所以 `ContainsKey` 為 false,整個區塊被跳過——註解寫得很清楚要鎖住的那兩項,恰好是唯一鎖不住的兩項。

**影響**:選「未過試用期」或「交通費明細」時客戶等級下拉仍可選,選了會被帶進 SQL 當過濾條件(`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:807`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:1471`),算出來的「是否達標」與「交通費合計」會少算。

### E13 停損點永遠顯示不出來 · 嚴重度 中

```
if (!row.IsNEED_SIZENull()  && row.NEED_SIZE  > 0) unumNEED_SIZE.Value  = row.NEED_SIZE;
if (!row.IsINV_LIMITNull()  && row.INV_LIMIT  > 0) unumINV_LIMIT.Value  = row.INV_LIMIT;
if (!row.IsSTOP_GAINNull()  && row.STOP_GAIN  > 0) unumSTOP_GAIN.Value  = row.STOP_GAIN;
if (!row.IsSTOP_LOSSNull()  && row.STOP_LOSS  < 0) unumSTOP_LOSS.Value  = row.STOP_LOSS;
```

`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:463-466`。四行只有最後一行是 `< 0`。而存檔那側(`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs:111-114`)四個欄位一律照畫面值存、空值存 0,**沒有把停損點轉成負數**。

**影響**:停損點存成正數(例如 10 代表 10%)時,再次開啟維護頁該欄位是空白的;使用者若直接存檔就會把它洗成 0。這是「查得到、看不到、一存就掉」的典型。

### E12 · E14~E27 其餘十四條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E12 | `GetRpt0A` 把 `AddParam(…, "A", "CUS_LV")` **呼叫了兩次**(`:218` 與 `:232`);12 支 `GetRpt*` 只有這一支這樣 | `AddParam` 同時會加繫結參數,等於同名參數加兩次、條件在 `strCLS` 的兩個 `{0}` 佔位共出現四次。是否丟 Oracle 錯誤要實測,至少是多餘的 | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:218`、`:232` | 中 |
| E14 | `SetPermissionInfo(this.ProcessVDB)` 在 `this.ProcessVDB = new …` **之前**呼叫,全庫其他地方都是先 new 再設(註解寫「新vdb就要用」) | 兩支 B 的 PO 都讀 `PermissionInfo.Rows[0].UserID`:框架若沒補就是 index out of range,若有補這兩行就是多餘的——兩種情況都該修 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB001.cs:29-32`、`Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSB002.cs:41-44` 對照 `Dev/ATLAS.BMS/Source/UI/UI.BMS/BMSB925.cs:38-40` | 中 |
| E15 | `CLSR002_PO.GetData` 用 Reflection 依用戶端參數叫 `"GetRpt" + RptType`,而且帶 `BindingFlags.NonPublic` | 任何簽名相符的私有方法都成為可呼叫入口;傳不存在的值則是 `NullReferenceException` | `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:155-157` | 中 |
| E16 | `Convert.ToDecimal(Result[0].ReturnMessage.PadLeft(1, '1'))` —— `PadLeft(1,'1')` 只在字串長度為 0 時補,等於「查不到匯率」被寫成「匯率 = 1」 | 預計申購金額(台幣)直接等於原幣金額,沒有任何提示 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p1.cs:65` | 中 |
| E17 | `CLSI001p0` 塞值 19 行**完全沒有 `IsXxxNull()` 保護**,而 `EST_CALL_DATE` / `ACT_CALL_DATE` / `TRAFFIC_FEE` / `BF_NO` 在 xsd 都是可空的 | 任一為 NULL 時雙擊明細就丟 `StrongTypingException`;對照 `CLSM001` 每一欄都有檢查 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSI001p0.cs:71-89` | 中 |
| E18 | `CLSM001p0`「受益人基本資料」在 `CLSM001` 的呼叫點已被註解,只剩 `CLSM002` 一個活呼叫;而且它的 grid 顯示 `ID_NO`/`BF_NO`/`PR_NAME`/`MAIL_ADDR`,資料來源卻是 `vdb.UIView.CLS001`(潛在客戶) | 視窗標題與實際內容對不起來 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001p0.cs:62-63` 對照 `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:181` | 低 |
| E19 | `CLSM002p2` 的 `this.DialogResult = DialogResult.OK;` **寫在 foreach 迴圈裡** | 一個都沒勾時視窗不關、也不提示,使用者以為壞掉 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002p2.cs:101-107` | 低 |
| E20 | `SetParameterValue("FUND", …挑選的基金清單…)` 下一行立刻被 `SetParameterValue("FUND", "境內基金")` 覆蓋 | 報表表頭永遠印「境內基金」,看不到挑了哪幾檔 | `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:359-360` | 低 |
| E21 | 兩支 B 的四個 `CustomTransfer*` 各自 `as` 出 `view` / `model` 兩個區域變數就直接 `return`,沒搬任何資料 | B 型只靠 `Util` 溝通所以是「對的」,但看起來像沒寫完 | `Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB001_Ctl.cs:46-59`、`Dev/ATLAS.CLS/SOURCE/Control/Control.CLS/CLSB002_Ctl.cs:53-66` | 低 |
| E22 | `CLSM001Model.xsd` 的 `CLS0021`(4 欄)全庫零引用,欄位與同檔的 `CLS002` 結果集幾乎一樣 | 改版殘留,搜尋時誤導 | `Dev/ATLAS.CLS/SOURCE/Entity/DataEntity.CLS/CLSM001Model.xsd` | 低 |
| E23 | `CLSR001RPS1` 沒有任何畫面入口(六個選項的 `RptNumber` 值域是 {2,3,4,5,6,7,8,9}) | 22 支 rpt 裡唯一載不到的一支 | §7.1 · `Dev/ATLAS.CLS.Report/Source/UI/ReportUI.CLS/CLSR001.cs:191-196` | 低 |
| E24 | `SetCLS001Data` 的 `if (!row.IsID_NONull()) …` 連續寫兩次 | 無功能影響,顯示這段靠複製貼上維護(同 `architecture.md §2.7` 記的 `CASM001.cs:129`/`:136`) | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM002.cs:202-205` | 低 |
| E25 | **本模組沒有非 UTF-8 的來源檔**:兩個專案底下所有 `.cs`/`.xsd`/`.config`/`.csproj`/`.resx` 逐檔 UTF-8 解碼,0 支失敗 | 對照 `bms.md 附錄 E18` 的 BMS 有一支 Big5,CLS 這邊乾淨 | — | — |
| E26 | 「讀快照還是讀現值」有**兩份實作**,而且已經漂移(部門來源、`NVL` 處理、日期繫結方式都不同,見 §7.2 的表) | 查詢畫面與報表看到的客戶清單可能不一致,而使用者認為兩邊應該一樣 | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:176-273` 對照 `Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR002_PO.cs:49-105` | 中 |
| E27 | 沒給實際拜訪日迄日時,`ISHIS` 的上限寫死 `'29991231'`,而且是字串串接 | 語意正確,但寫死哨兵值與串接並存(同 E4) | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM002_PO.cs:187` | 低 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。7 支畫面、5 張表、22 支 rpt 全數涵蓋;釐清 `CLS001`~`CLS005` 與 `CLS001A`/`CLS002A` 的歸屬、`CLSB002` 六層不齊的真因、`CLS001H` 快照機制。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 125 · 圖 5 · 表格 67 · 程式錨點 401 · § 連結 46 · 引用檢查：畫面 13（缺 0） · Table 29（缺 0） · Report 22（缺 0） · 結果集 15（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/cod.md
============================================================

# ATLAS COD 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:COD 是全系統的代碼值域來源,所以本篇的重心不在畫面而在 §2。趕時間只讀三段:§0.2(這模組最反直覺的事)、**§2.4(代碼表與程式常數字典怎麼對應,哪些查表哪些寫死)**、附錄 E(踩雷)。要查某個代碼欄位的值域從哪來,直接翻附錄 C。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、控件 Label 文字與 DB 腳本的欄位註解**推測**。ATLAS 沒有把畫面中文名放進版控 —— COD 的 13 支 Form **沒有任何一支**有 `this.Text`,連彈出視窗都沒有。 ⚠ **〔客戶特定〕**:部門代碼(`G2` / `G3` / `GA` / `OP1`…)、員工代號黑名單、`CODE_SORT = 'C1'`(列管原因)、作廢原因 `01`–`05`、`FEE_CODE = '07'` 等為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`COD009` 被 12 個專案、121 個檔引用,`COD006A` 被 12 個專案、62 個檔引用(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`TA.MappingCode` 看 `architecture.md §7.2`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:COD 管三件互不相干的事 —— 全系統代碼值域的字典、公司員工與其親屬的主檔、以及受益憑證紙張流水號的發放與作廢。**

推測依據逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 表名與欄位中文名 | `COD006A` 的欄位是「代碼種類說明」「可否異動註記」「有效碼」「顯示順序」;`COD007A` 是「級距代碼說明」「客戶異動註記」 | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:109-124`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:47-55` |
| 控件 Label 文字 | 「代碼種類」「代碼說明」「級距上限」「級距下限」「員工代碼」「親屬關係代碼」「流水號起號」「受益憑證號碼」「作廢原因」「選項類別」「選項說明」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:177`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:262-273`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.Designer.cs:358`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.Designer.cs:201`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.Designer.cs:194-208`、`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.Designer.cs:141-170` |
| 程式訊息 | 「此代碼已存在一般代碼資料或級距代碼資料中,不可刪除!」「該員工代碼仍有親屬資料,不可刪除!」「此區間的流水號已被使用或作廢,不可修改」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:190`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:630`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:113` |
| DB 腳本欄位註解 + 共用 PO 用法 | 「通路職務別\CTL014:701」「職位代號\CTL014:702」;全系統的下拉選單與代碼 Searcher 都去讀 `COD006A` 與 `CTL014` | `DB/Table/updateCOD009.sql:15-17`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197` |

「COD」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「代碼檔」描述它,這是從上表推出來的,不是官方名稱。

三條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 代碼字典 | 代碼種類(哪些代碼類別存在)、該類底下的代碼明細、以及用數值區間表示的級距代碼 | `CODM005`、`CODM006`、`CODM007` | `COD005A`、`COD006A`、`COD007A` |
| A' 下拉選單字典 | 另一套**平行**的代碼表,專門餵 UI 下拉選單 | `CTLB014`〔代號屬 CTL,檔案在本專案內〕 | `CTL014` |
| B 員工與親屬 | 員工基本資料、部門、離職日、系統使用者代號、業務歸屬銷售機構;以及員工親屬(優惠關係人的來源) | `CODM009`、`CODB009`、`CODM010`、`CODB901`、`CODB902` | `COD009`、`COD010` |
| C 憑證流水號 | 每檔基金的紙張流水號區間配發、單張憑證的作廢與取消作廢 | `CODM016`、`CODM017` | `COD016`、`COD017` |
| D 其他 | 待辦事項清除、一張只有兩欄的級距設定 | `CODB000`、`CODM036` | `TODO`、`COD040A` |

### 0.2 這模組最反直覺的一件事

**COD 是代碼檔模組,而它自己的程式常數字典是死碼。**

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 定義了 `CODE_SORT` 類別,31 個常數,每個都附中文註解 ——「語言代碼 = 01」「教育程度代碼 = 02」「客訴內容種類代碼 = 12」。這是 repo 內唯一寫下 `COD006A` 代碼種類語意的地方。

**全庫引用次數:0。**

| 類別 | 檔 | 常數數 | 全庫引用(排除 `TA.MappingCode` 自己與 `*.Designer.cs`) |
|---|---|---|---|
| `CODE_SORT` | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10` | 31 | **0 次** |
| `CTL_SRNO_ID` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993` | 3 | **0 次** |
| `EMP_DEPT_TYPE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:141` | 6 | 74 次 / 19 檔 |
| `EMP_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45` | 5 | 4 次 / 2 檔 |
| `VALID_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81` | 3 | 1 次 / 1 檔 |
| `YES_NO` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11` | 2 | 699 次 / 100 檔 |

取而代之的是**字面值**。`CODE_SORT` 的字面值在全庫 `.cs` 的 SQL 與比較式裡出現約 190 處、涵蓋約 40 個不同的值(逐值清單見附錄 C.2)。最諷刺的兩處都在自己家:

- `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372`:`if (row.CODE_SORT != "C1") return;` —— 「列管原因」這個代碼種類寫死在代碼維護畫面的 PO 裡,而 `C1` 不在 `CODE_SORT` 常數清單中。

- `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109`:`[CTL_SRNO_ID] = '2'` / `= '0'` —— 而 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` 正好有 `CTL_SRNO_ID.Destroy = "2"` 與 `CTL_SRNO_ID.UnUsed = "0"`,就在同一個方案裡,沒被用。

**後果**:看到一個代碼欄位想知道值域,`TA.MappingCode` 只在 `CTL014` 那一半可靠(而且只覆蓋 186 / 395,見 §2.4);`COD006A` 那一半必須**連資料庫**或**grep 字面值**。本文附錄 C 把 grep 得到的部分整理出來,但那不是完整值域。

### 0.3 不管什麼

以下**不在** COD 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 系統使用者帳號本身(密碼、權限、EMAIL) | PTPF 平台(`UC0101`) | `CODB902` 只會改 `AA_USER` 的鎖定與密碼欄,且訊息直接寫「必須先到UC0101設定使用者的〔電子郵件信箱〕」;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:99` |
| 部門主檔 | OFD | `OFD002` 一律 `LEFT JOIN` 取 `DEPT_SH_NM`,COD 內無任何寫入;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:469-470` |
| 銷售機構主檔 | OFD | `OFD068A` 只被 join 取名稱;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:155` |
| 基金主檔 | OFD | `OFD081` 只被 join 取 `FUND_SH_NM`;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:410-411` |
| 優惠關係人(員工與親屬的折扣身分) | OFD(`OFD195A`) | COD 只**查**它決定能不能刪,不寫;寫入的程式碼整段被註解掉;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` |
| 憑證的實際列印與送簽 | OFD(`OFD721`) | `CODM017` 只 join `OFD721` 取 `CER_STATUS` 判斷能不能作廢;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:215-218` |
| 列管(交易管制)本身 | OFD(`OFD115A`) | `CODM006` 只查它決定某個代碼能不能改 / 刪;`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343` |
| 員工資料的來源系統 | 外部 eHR | `DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 兩張介接表做同樣的加欄。這兩張表**沒有任何 `.cs` 引用**,所以匯入程式不在本 repo。**假設**:員工資料由 eHR 定期匯入,`CODM009` 是人工補正的入口 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 系統管理 / 參數維護人員 | 維護代碼種類與代碼明細、級距代碼、下拉選單內容 | `CODM005` / `CODM006` / `CODM007` 是標準四眼維護畫面;`CTLB014` 是 OneStep 無四眼;`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:101-106` |
| 人事 / 行政 | 建立與維護員工資料、親屬資料 | `CODM009` 有身分證格式檢核、離職日不得小於進公司日等人事規則;`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:306-317` |
| 通路 / 業務管理 | 批次把一批員工掛到某個銷售機構底下 | `CODB009` 先查後勾再一次改;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76-137` |
| IT 支援 | 使用者被鎖時解鎖、補發密碼;清掉卡住的待辦事項 | `CODB902` 與 `CODB000`;`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:57-166`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:36-72` |
| 憑證作業人員 / 覆核者 | 配發紙張流水號區間、作廢單張憑證;以及對 `CODM005`–`CODM010`、`CODM016`、`CODM036` 的異動做驗證 / 覆核 / 退回(四眼流程由框架處理,見 `architecture.md §3`) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:92-177` |

**注意:本模組沒有任何一行程式碼在判斷權限。**`CODM009` 那條員工白名單式的邏輯也不存在(那是 CAS 的寫法)。功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。但 `CODB902` 能改任意使用者的密碼,`CTLB014` 能刪掉整個代碼類別 —— 這兩支的權限設定值得單獨確認。

### 0.5 全域開關

repo 內**沒有**任何 COD 專屬的設定檔開關。`Dev/ATLAS.COD/Source/UI/UI.COD/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:47`(`CODM005`)、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:68`(`CODM009`)、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`(`CODM017`) |
| `ugrdResult` 的 `column` / `columnname` 白名單 | 查詢結果 grid 顯示哪些欄位、順序、以及中文抬頭 | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:48`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:55`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:76` |
| `formstyle` | 四支 B 與 `CTLB014` 宣告為 `OneStep`;八支 M 沒有宣告(走預設維護樣式) | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:20-25`、`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:101-106` |

四件要記住的:

- **`CODM017` 的 `mastertable` 寫的是 `CODM017`,不是 `COD017`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`)。那是 typed DataSet 的表名,不是實體表名。實體表是 `COD017`,只在 PO 的 SQL 字串裡出現。

- **`CODM036` 的 `pkey` 寫 `dataid`,而 xsd 的主鍵是 `MIN_VALUE`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:97` 對 `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:98-101`)。兩邊不一致,以 xsd 為準(框架的樂觀鎖與 EVA 比對走 xsd 的 PK)。

- **`CODM017` 沒有宣告 `ugrdResult`**(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:87-93`),因為它是 OneStep 樣式的單筆查詢畫面,沒有結果 grid。

- `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:107` 宣告 `.NETFramework,Version=v4.8`;PO 側每一支都留了 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的逐檔修補痕跡(例:`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:7`),與 CAS 一致。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] COD 模組全景：代碼字典、員工與親屬、憑證流水號三條線，以及全系統讀代碼的三條路徑
圖中文字:① 代碼字典本體：兩套互不相通的代碼表 / CODM005 / 代碼種類 COD005A / CODM006 / 一般代碼 COD006A / CODM007 / 級距代碼 COD007A / CTLB014〔屬 CTL〕 / 下拉選單 CTL014 / ② 員工與親屬：COD009 一批一維護，兩個入口 / CODM009 / 員工主檔維護 COD009 / CODB009 / 批次改銷售機構 COD009 / CODM010 / 員工親屬 COD010 / CODB901 CODB902 / 旗標與帳號解鎖 / ③ 憑證流水號：唯一走 SQL Server 語法的兩支 / CODM016 / 流水號區間 COD016 / CODM017 / 憑證作廢 COD017 / CODM036 / 級距設定 COD040A / CODB000 / 待辦事項清除 TODO / ④ 資料落點（COD009 另有兩張 eHR 介接表，只在 DB 腳本裡） / COD005A COD006A / 代碼種類與明細 / COD007A / 級距代碼 / COD009 COD010 / 員工與親屬 / COD016 COD017 / 憑證流水號 / COD040A / 級距 掃描器漏掉 / ⑤ 全系統怎麼讀它們：三條路，沒有一條經過本模組的 PO / 共用 BasicCOD_PO / 讀 COD005A COD006A COD009 / 共用 BasicCMM_PO / 讀 CTL014 餵所有下拉 / TA.MappingCode / 編譯期常數 不連 DB
```

*圖:圖 1 COD 全景。橘框＝本模組維護入口；橘虛框＝含寫死值或跨模組行為；黑框＝無原始碼或不在本模組的讀取端；灰虛框＝掃描器漏掉的表。三條業務線之間沒有程式呼叫，只靠表相連。*

看圖的四個重點:

1. **三條業務線之間沒有程式呼叫關係。** `CODM005` 不會叫 `CODM009`,`CODM016` 不會叫 `CODM006`。它們只透過表相連,而且連得很少:整個模組內唯一的跨線關聯是 `CODM017` 的「作廢原因」下拉去讀 `COD006A` 的 `CODE_SORT = '17'`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`)。

2. **代碼字典有兩套,而且互不相通。** `COD005A` / `COD006A` 一套(鍵是 `CODE_SORT`),`CTL014` 一套(鍵是 `SourceType`)。兩套的編號**長得很像但不是同一套**:`COD006A` 的 `17` 是作廢原因,`CTL014` 的 `017` 是定期定額註記(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277`)。詳見 §2.3。

3. **本模組的 PO 不是別人讀代碼的入口。** 全系統讀 `COD006A` / `CTL014` 走的是 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs` 兩支共用 PO,完全不經過 `Dev/ATLAS.COD/`。所以「改 COD 的程式」跟「改別人怎麼讀代碼」是兩件事。

4. **`CTLB014` 的代號屬 CTL,檔案卻六層齊全地放在 `Dev/ATLAS.COD/` 底下。** 掃描器把它歸到 CTL 模組(`atlas_scan.py --screen CTLB014`),所以 COD 的母體是 12 支而不是 13 支。但它維護的正是全系統下拉選單的來源表,實務上要跟 COD 一起看(§8.3)。

### 1.2 資料表關係

見 §2 節首的圖。六張實體表加一張掃描器漏掉的 `COD040A`,分成四組:

- **代碼字典三張**(`COD005A` → `COD006A` / `COD007A`):`COD005A` 是種類主檔,另外兩張各自是它的明細,但**不是四眼意義上的主明細** —— 三支畫面各自宣告自己的 `MasterTable`,沒有任何一支宣告 `DetailTable`(§2.1),關聯只存在於 SQL 的 `LEFT JOIN` 與刪除前的存在性檢查。**員工兩張**(`COD009` / `COD010`)也一樣:`COD010` 靠 `EMP_NO` 指回 `COD009`,是兩支獨立的維護畫面。

- **憑證兩張**(`COD016` / `COD017`):唯一真正有寫入關係的一組 —— `CODM016` 存檔時呼叫 SP `s_CODM016` 依區間**產生** `COD017` 的逐筆資料,刪除時把 `COD017` 整批刪掉(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:317-370`)。

- **級距一張**(`COD040A`):`CODM036` 用 `MasterTable.Add(...)` 的多筆寫法宣告,掃描器的正規式只認 `MasterTable = new xTableMapping(...)`,所以這張表**不在母體也不在索引**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36`)。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 本畫面自訂檢核 | 各畫面的 `DoValidate()`,多半**先**於必填檢核 | `ValidateErrList` 訊息清單 |
| 2 需要查 DB 的檢核 | `DoValidate()` 裡直接 `new` 一個 `_Pxy` 打過去 | 訊息清單或對話框 |
| 3 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 4 PO 的 `Before*` | `BeforeSelect` 換 SQL(七支)、`BeforeUpdate` / `BeforeDelete` 擋(只有 `CODM006`) | `args.Cancel = true` + `CancelMsg` |
| 5 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 6 PO 的 `After*` | `CODM009` / `CODM010` / `CODM016` 有掛,但前兩支的內容整段被註解 | `throw` → 整筆回滾 |

**第 1 到第 3 階段全部在用戶端。**伺服器端只重驗兩條:`CODM005` 覆寫 `Delete` 查下層資料(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232`)、`CODM006` 用 `BeforeUpdate` / `BeforeDelete` 查列管(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:336-392`)。其餘六支的卡控只要繞過 UI 就全部失效。

### 1.4 批次資料流

見 §6 節首的圖。三件事:

- **四支 B 全部是使用者按按鈕觸發的 OneStep 畫面**,不是排程。repo 內沒有任何 COD 的 WindowsService 或排程設定(掃描器回報 Service 0)。

- **四支全部繞過四眼引擎直接下 DML**:`CODB000` 刪 `TODO`、`CODB009` 與 `CODB901` 改 `COD009`、`CODB902` 改 `AA_USER`。`CODB009` 的 PO 雖然繼承 `BaseEVADaoPO` 並宣告了 `MasterTable`,但它覆寫的是 `Execute` 而不是 `Update`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76`),所以四眼欄位一個都不會被寫。

- **只有 `CODB902` 有對外副作用**:寄一封含明文亂數密碼的 EMAIL,並把執行歷程寫進一張叫 `CODB902` 的表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:123-149`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,以下是**推測**的作業順序,依據是資料相依:某張表要有資料,後一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期(一次性) | 系統管理 | 先建代碼種類,再建該種類底下的代碼或級距 | `CODM005` → `CODM006` / `CODM007` | `CODM006` 的種類下拉只列**還沒被 `COD007A` 用掉**的種類(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-614`) |
| 建置期 | 系統管理 | 設定各下拉選單的選項與順序 | `CTLB014` | 要先知道 `SourceType` 編號,而編號本身沒有任何維護畫面(§2.4) |
| 平時(人事異動) | 人事 | 新增 / 修改員工,填離職日 | `CODM009` | 部門要先在 `OFD002` 存在 |
| 平時 | 人事 | 維護員工親屬 | `CODM010` | 員工要先在 `COD009` 存在(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:614-630` 的刪除檢核反向證明了這條相依) |
| 通路調整時 | 通路管理 | 一次把多位員工改掛到某銷售機構 | `CODB009` | 機構要先在 `OFD068A` 存在 |
| 需要時 | IT 支援 | 解鎖 / 補發密碼、清待辦 | `CODB902`、`CODB000` | 使用者要先在 `AA_USER` 存在 |
| 憑證印製前 | 憑證作業 | 配發一批紙張流水號給某檔基金 | `CODM016` | 基金要先在 `OFD081` 存在;起號自動接續該基金的最大迄號(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:186-208`) |
| 憑證毀損時 | 憑證作業 | 作廢單張憑證 | `CODM017` | 該號要先由 `CODM016` 產生到 `COD017`,且 `OFD721` 的 `CER_STATUS` 必須是 `2`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:80-88`) |

**假設**:「建置期一次性」這個定位 —— 依據是三支代碼畫面的查詢條件都極簡(只有代碼種類與代碼),沒有日期區間也沒有狀態篩選。實際頻率要問使用者。

## 2. 資料模型

```text
[圖] COD 的四張代碼表與 TA.MappingCode 程式常數的對應關係，以及兩者對不上的地方
圖中文字:① 執行期：值真的存在資料庫，改了立刻生效 / COD005A 代碼種類 / PK CODE_SORT / COD006A 一般代碼 / PK CODE_SORT+CODE / COD007A 級距代碼 / PK CODE_SORT+RANGE / CTL014 下拉選單 / SourceType 分類 / ② 誰維護：四張表四個入口，只有前三張走四眼 / CODM005 四眼 / 刪除前查下層有無資料 / CODM006 四眼 / MOD_FLAG=N 不可改 / CODM007 四眼 / 上限須大於下限 / CTLB014 無四眼 / 整類刪光再寫回 / ③ 編譯期副本：TA.MappingCode 三支檔，跟上面沒有同步機制 / CTL014.cs / 187 類 566 值 對 CTL014 / CODCode CODE_SORT / 31 值 對 COD005A / CODCode EMP_DEPT_TYPE / 6 值 部門所屬 / SysCode SrNo / 流水號代號 / ④ 對不上的地方（本篇最重要的一段，細節見 §2.4） / 程式用 395 個 SourceType / CTL014.cs 只定義 186 個 / CODE_SORT 常數用 0 次 / 全庫都直接寫字面值 / CTL_SRNO_ID 常數 0 次 / CODM017 寫死 0 與 2 / YES_NO 用 699 次 / 唯一被認真用的 / ⑤ 結論：值域來源共五種，讀的人要先知道在讀哪一種 / CTL014 表 / 下拉選單 走 SourceType / COD006A 表 / Searcher 走 CODE_SORT / COD007A 表 / 級距 上下限比大小 / TA.MappingCode / 程式常數 可被寫 / 字面值寫死 / SQL 或 C# 裡
```

*圖:圖 2 代碼表與程式常數字典。橘框＝執行期真值所在的表；黑框＝編譯期常數（無同步機制）；橘虛框＝實測出來對不上的地方。實線＝維護關係；虛線＝照著抄一份，不是程式相依。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`)。COD 十二支畫面的宣告分成四種寫法:

| 畫面 | 宣告方式 | `MasterTable` | `DetailTable` | 錨點 |
|---|---|---|---|---|
| `CODM005` | `xTableMapping` | `COD005A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:52` |
| `CODM006` | `xTableMapping` | `COD006A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:54` |
| `CODM007` | `xTableMapping` | `COD007A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:47` |
| `CODM009` | `xTableMapping` | `COD009` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:39` |
| `CODM010` | `xTableMapping` | `COD010` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:41` |
| `CODB009` | `xTableMapping` | `COD009` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43` |
| `CODM016` | **舊版 `TableMapping`** | `COD016` | **無**(靠 SP 與手寫 SQL 維護 `COD017`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:50` |
| `CODM036` | **`MasterTable.Add(...)`** | `COD040A` | **無** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36` |
| `CODM017` | **完全沒有宣告** | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:20-40` |
| `CODB000` | 不繼承 EVA 基底 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:24-26` |
| `CODB901` | 空建構子 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:37-40` |
| `CODB902` | 空建構子 | —— | —— | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:38-41` |

**全模組沒有任何一支宣告 `DetailTable`。**COD 沒有主明細結構,十二支畫面每一支都是單表(或無表)。

三個掃描器母體看不出來、但會影響維護的點:

- **`CODM017` 沒有主明細,不是漏寫,是它根本不是四眼 PO。** 它繼承的是 `BasicEVAPO` 而不是 `BaseEVADaoPO`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:20`),只實作了自己的 `Set` 與 `Get` 兩支手寫方法(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:47`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:200`),而且**用的是 SQL Server 語法** —— `[COD017]` 方括號識別字、`@` 參數前綴、`GetDate()`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:75-86`)。`App.config` 裡宣告的 `mastertable` 是 typed DataSet 的表名 `CODM017`,不是實體表(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:90`)。實體表是 `COD017`。

- **`CODM036` 有主檔,只是掃描器認不出來。** 它繼承 `BaseMultiRowEVADaoPO`,`MasterTable` 是集合不是屬性,所以寫成 `this.MasterTable.Add(new xTableMapping("COD040A", "CODM036"));`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:36`)。掃描器的正規式只認賦值寫法,於是 `COD040A` 這張表**不在母體、不在索引、也不在 `architecture.md` 附錄 A 的 367 張表裡**。

- **`CODM016` 用的是沒有 `x` 前綴的舊版 `TableMapping`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:50`),搭配舊版 `PrepareSQLEventHandler` 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:47-53`)。整個 COD 只有這一支停在舊世代,連它用的 `TableHelper.AppendToDoString` 也是 SQL Server 版(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:452`);其餘七支 M 都用 `xTableHelper` / `xEVAStringHelper`。這正是 `architecture.md §4.7` 說的「綁到哪一份取決於檔案頂端的 `using`」的實例。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。

| 表 | 主鍵(xsd) | 主鍵(App.config) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `COD005A` | `CODE_SORT` | `CODE_SORT` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM005Model.xsd:100-103` |
| `COD006A` | `CODE_SORT` + `CODE` | `CODE_SORT,CODE` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:130-134` |
| `COD007A` | `CODE_SORT` + `RANGE_CODE` | `CODE_SORT,RANGE_CODE` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:123-127` |
| `COD009`(`CODM009` 版) | `EMP_NO` | `EMP_NO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:197-200` |
| `COD009`(`CODB009` 版) | `EMP_NO` | (B 畫面不宣告) | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd:184-187` |
| `COD010` | `REL_ID_NO` | `REL_ID_NO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM010Model.xsd:160-163` |
| `COD016` | `FUND_ID` + `BNG_CTL_SRNO` | `FUND_ID,BNG_CTL_SRNO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:198-202` |
| `COD017`(在 `CODM016` 的 xsd 內) | `FUND_ID` + `BF_CTL_SRNO` | — | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:203-207` |
| `COD017`(在 `CODM017` 的 xsd 內,表名叫 `CODM017`) | `FUND_ID` + `BF_CTL_SRNO` | `FUND_ID,BF_CTL_SRNO` | ✔ | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM017Model.xsd:114-118` |
| `COD040A`(表名叫 `CODM036`) | `MIN_VALUE` | **`dataid`** | **✘** | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:98-101` 對 `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:97` |
| `CTL014` | **沒有宣告主鍵** | (`CTLB014` 不宣告) | — | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:18-21` |

**`COD010` 的主鍵只有 `REL_ID_NO`(親屬身分證字號),不含 `EMP_NO`。**意思是同一個人不能同時是兩位員工的親屬 —— 這條限制沒有寫在任何地方,是從 xsd 反推的。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 有中文名的欄 | 說明 |
|---|---|---|---|
| `COD009`(`CODB009` 版) | ✔ | **全部 13 欄都有 Caption** | 全模組唯一完整的一份 |
| `COD005A` `COD006A` `COD007A` `COD009`(`CODM009` 版) `COD010` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `COD016` `COD017` | ✔(但**大小寫不同**) | 一個都沒有 | 寫成 `dataid` / `Status` / `CreateID` / `DataFlag`,其餘表全是大寫 |
| `COD040A` | ✔ | 一個都沒有 | 大寫版 |
| `CTL014` | **完全沒有** | — | 四欄而已,沒有 `DATAID`、沒有 `STATUS`、沒有 `DATAFLAG` |

三個後果:(1) **`COD016` / `COD017` 的四眼欄位是混合大小寫**,而且這兩支的 SQL 是 SQL Server 方言用方括號包 —— 改欄位時不能照其他表的大寫習慣寫;(2) **`CTL014` 沒有 `DATAFLAG` 所以沒有樂觀鎖**,兩人同時開 `CTLB014` 改同一類,後存的無聲蓋掉先存的,而且因為寫法是「整類刪光再寫回」(§8.3),先存的那批**整批消失**;(3) **`CTL014` 沒有 `STATUS` 所以沒有四眼**,全系統下拉選單可以被一個人單獨改掉。

`DATAFLAG` 在有它的六張表上型別一律 `xs:base64Binary`,是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 六張表各是什麼代碼、誰在用

這一節是本篇的主要用途:拿到一個代碼欄位,先在這裡對號入座。「誰讀」是全 `Dev` 下 `.cs` 的表名字面比對(排除 `*.Designer.cs`)。

| 表 | 是什麼(一列 = 什麼) | 主要欄位 | 誰維護 | 誰讀(檔數) | 值域寫在哪 |
|---|---|---|---|---|---|
| `COD005A` | 一個代碼種類,例如 `01` 語言代碼、`12` 客訴內容種類代碼 | `CODE_SORT`(2 碼 PK)、`CODE_SORT_DESCRP` + 13 四眼;17 欄 | `CODM005`(四眼) | 4;只有 `CODM006` / `CODM007` 的種類下拉(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:600-666`)與查詢 join(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:251`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:175-176`) | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 的 `CODE_SORT`(31 個,**零引用**);實際值見附錄 C.2 |
| `COD006A`〔共用〕 | 某代碼種類底下的一個代碼值,例如種類 `17`(作廢原因)底下的 `01` | `CODE_SORT` + `CODE`(PK)、`CODE_DESCRP`、`M_CODE`、`MOD_FLAG`、`VALID_CODE`、`SHOW_ORDER` + 13 四眼;23 欄 | `CODM006`(四眼) | **62**、12 個專案;統一入口 `ucCOD006`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:21`)配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257` | **沒有完整清單**;`CODE_SORT` 靠約 190 處字面值 / 40 值(附錄 C.2),`CODE` 只在資料庫 |
| `COD007A` | 一個數值區間級距,例如投資級距的 0–100 萬 | `CODE_SORT` + `RANGE_CODE`(PK)、`RANGE_CODE_DESCRP`、`MIN_VALUE`、`MAX_VALUE`、`MOD_FLAG` + 13 四眼;22 欄 | `CODM007`(四眼) | 4,其中 3 個在 COD 自己家。**沒有任何共用 DataSrc 讀它**;**假設**由版控外的 SP 或報表使用 | 同 `COD006A`,無程式常數 |
| `COD009`〔共用〕 | 一位員工 | `EMP_NO`(PK)、身分證、中英文姓名、部門、進 / 離職日、系統使用者代號、員工類別、是否公單、業務歸屬機構、通路職務別、職位…;xsd 55 欄(掃描器只算 36) | `CODM009`(四眼)、`CODB009` / `CODB901`(繞過四眼) | **121**、12 個專案;`RSPM037` 也把它當 `MasterTable`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`) | 各代碼欄對應 `CTL014` 的 `SourceType`:`EMP_CD` → `002`、`AO_CODE` → `003`、`MANGR_CODE` → `001`、`AGENT_ID` → `062`、`G_JOB_CODE` → `701`、`JOB_CODE` → `702`(附錄 C.1) |
| `COD010` | 一位員工親屬(優惠關係人的來源) | `REL_ID_NO`(PK)、`EMP_NO`、`REL_NAME`、`REL_CODE`、`BIR_DATE`、生效 / 終止 / 停用 / 異動日 + 13 四眼;35 欄 | `CODM010`(四眼) | 8;`CODM009` 刪除員工前會查它(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:614`) | `REL_CODE` 走 `RelCodeDataSrc`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:120-122`),底層是 `COD006A` 的某個 `CODE_SORT` |
| `COD016` | 「某檔基金配發了流水號 M 到 N 這一段」 | `FUND_ID` + `BNG_CTL_SRNO`(PK)、`END_CTL_SRNO`、`FUND_SH_NM`(join)+ 13 四眼(**小寫混合**);19 欄 | `CODM016`(四眼) | 3,全在 COD | 無代碼欄位 |
| `COD017` | 「某檔基金的第 K 號紙張」及其憑證號碼與作廢狀態 | `FUND_ID` + `BF_CTL_SRNO`(PK)、`BF_CER_ISSUE_CODE`、`BF_CER_NO`、`CTL_SRNO_ID`、`CANCEL_CD` + 13 四眼;21 欄 | **沒有四眼入口**:新增靠 `CODM016` 的 `AfterAdd` 呼叫 `s_CODM016`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:119`),刪除靠 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:178` 與 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:348`,狀態改變靠 `CODM017` 直接 UPDATE | 10(COD 4、Common 4、OFD 2) | `CTL_SRNO_ID` → `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007`(`0` 未使用 / `1` 已使用 / `2` 作廢,**程式不用它**);`CANCEL_CD` → `COD006A` 的 `CODE_SORT = '17'`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`) |
| `COD040A` | 一個級距(業務不明) | `MIN_VALUE`、`MAX_VALUE`、`VAL_DESC` + `DATAID` + 13 四眼;18 欄。xsd 表名是 `CODM036`(`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:28-30`) | `CODM036`(四眼多筆版) | 1,只有 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs` | 無代碼欄位 |

每張表的陷阱:

- `COD005A`:一個 `CODE_SORT` **只能二選一** —— 要嘛在 `COD006A` 有明細、要嘛在 `COD007A` 有,不能兩者都有。這條規則實作在下拉的兩段 SQL(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`),不是任何一個檢核。

- `COD006A`:`MOD_FLAG = 'N'` 會鎖住 `CODM006` 的修改與刪除鈕(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83`),但**這個旗標是使用者自己填的**,新增時一律寫 `Y`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`)。

- `COD007A`:唯一的區間檢核是「上限須大於下限」(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185`)。**級距重疊或留空完全沒有檢核。**

- `COD009`:沒有 eHR 以外的權威來源。`DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 做同樣加欄,但兩表在 `.cs` 零引用 —— 匯入程式不在本 repo。

- `COD010`:xsd 有 `AFT_EMP_NO` / `AFT_EMP_CD` / `BEF_REL_NAME` / `BEF_EFFECTIVE_DATE` / `BEF_TERMINATE_DATE` 五個「異動前後」欄,UI 確實在填(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:287-291`),但 PO 端**沒有任何程式讀它們**。

- `COD017`:資料由**不在版控**的 SP `s_CODM016` 產生。要知道區間怎麼展開、`BF_CER_NO` 怎麼給,只能去資料庫看。

- `COD040A`:查詢用的主檔 SQL 寫死 `WHERE ROWNUM < 3`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52`),維護用的明細 SQL 卻是全表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:66-72`)。同一張表兩種取法,查詢頁最多只看得到 2 列。

### 2.4 代碼表與 `TA.MappingCode` 的對應:哪些查表、哪些寫死

見本節首的圖。**這是本篇最有價值的一段。**

#### 2.4.1 四個層次,先分清楚

| 層次 | 東西 | 執行期會不會變 | 錨點 |
|---|---|---|---|
| L1 執行期真值 | `COD005A` / `COD006A` / `COD007A` / `CTL014` 四張表的內容 | **會**,改完立刻生效 | — |
| L2 讀取入口 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs`(讀 COD 三張)、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197`(讀 `CTL014`) | 不會,但換 SQL 就換值域 | — |
| L3 編譯期副本 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs`(187 類 / 566 值)、`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs`(2 類 / 37 值) | **不會**,改了要重編 | `architecture.md §7.2` |
| L4 字面值 | 散在 SQL 字串與 C# 比較式裡的 `'C1'` / `'17'` / `'2'` | 不會,而且找不到 | — |

**L1 與 L3 之間沒有任何同步機制。**沒有產生器、沒有檢查、沒有測試。`CTL014.cs` 是某個時點手抄一份的結果。

#### 2.4.2 `CTL014` 這一半:覆蓋率 47%

`CTL014` 表的結構是 `SourceType` / `TextValue` / `DisplayName` / `DisplayOrder` / `Description` / `IsDefault`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:150-156`)。`SourceType` 就是「這是哪一類代碼」的三碼編號。

`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 的每個類別註解都帶著這個編號,例如「員工類別[002]」(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:44-45`)、「銷售機構區別碼[062]」(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050`)。

實測(掃全 `Dev` 下的 `.cs`,排除 `obj` / `bin`):

| 量 | 數字 | 怎麼算的 |
|---|---|---|
| `CTL014.cs` 帶編號的類別 | **186** | 註解裡出現 `[nnn]` 的 `public static class` |
| 程式實際用到的 `SourceType` | **395** | `new GetDropDownDataSrc("nnn")` 加上 250 個專屬 DataSrc 類別的 `m_sourcetype` 欄位 |
| 用到但 `CTL014.cs` **沒有**對應類別 | **224** | 例如 `063` / `163` / `295` / `404` / `450` / `701` / `702` |
| 有類別但沒有任何地方直接用 | **15** | `022` `032` `033` `034` `086` `112` `120` `121` `122` `123` `132` `135` `136` `147` `247` |

**結論:`CTL014.cs` 只覆蓋了實際在用的 `SourceType` 的 47%。**一個代碼欄位如果在 `CTL014.cs` 裡查得到,那份中文說明可信;查不到(超過一半的情況)就只能去資料庫看 `CTL014` 的 `Description` 欄。

兩個具體例子,都在 `CODM009`:

- `G_JOB_CODE`(通路職務別)走 `new GetDropDownDataSrc("701")`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587`)。`701` 在 `CTL014.cs` 裡沒有類別。值域唯一的線索是 DB 腳本的欄位註解:「1:部門主管;2:組主管/業務員;3:業務助理」(`DB/Table/updateCOD009.sql:15`)。

- `JOB_CODE`(職位代號)走共用控件 `ucCTL014`。該控件**在 repo 內沒有原始碼**(只有 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1900` 的欄位宣告,無原始碼,從呼叫端反推),`702` 在 `CTL014.cs` 裡也沒有類別,值域只寫在 DB 註解「職位代號\CTL014:702」(`DB/Table/updateCOD009.sql:17`)。

#### 2.4.3 `COD005A` / `COD006A` 這一半:覆蓋率 0%

| 量 | 數字 |
|---|---|
| `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10` 的 `CODE_SORT` 常數 | 31 |
| 全庫引用這些常數的次數 | **0** |
| 全庫 `.cs` 內 `CODE_SORT` 的字面值比較 / SQL 條件 | 約 190 處 |
| 涵蓋的相異 `CODE_SORT` 值 | 約 40 個 |
| 其中**在** `CODCode.cs` 裡查得到的 | 10 個(`11` `12` `13` `15` `19` `20` `23` `84` `89` `99`) |
| 其中**查不到**的 | 約 30 個(`00` `17` `1B` `1C` `36` `42` `45` `50` `51` `A7` `A8` `C1` `C5` `C6` `C7` `D2` `E2` `E3` `E4` `E7` `E8` `E9` `HO` `P1` `P3` `P5` `P7` `PC` `PD` `Q2`) |

逐處清單見附錄 C.2。

#### 2.4.4 兩套編號長得一樣但不是同一套

這是最容易踩的坑:

| 編號 | 在 `COD006A`(`CODE_SORT`) | 在 `CTL014`(`SourceType`) |
|---|---|---|
| `17` / `017` | 作廢原因(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`) | 定期定額註記 `RSP_ID`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:277`) |
| `02` / `002` | 教育程度代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:19`) | 員工類別 `EMP_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45`) |
| `03` / `003` | 職業別代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:23`) | 業務員區分碼 `SALES_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:67`) |
| `04` / `004` | 職稱代碼(`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:27`) | 部門 / 通路 / 銷售機構有效碼 `VALID_CODE`(`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81`) |

**判斷方法**:看控件型別。`ucCOD006` 系列的 Searcher → `COD006A` 的 `CODE_SORT`;`UltraCombo` 配 `xxxDataSrc` 或 `GetDropDownDataSrc` → `CTL014` 的 `SourceType`;`ucCOD005ForCODM006` → `COD005A`。三者在 `CODM009` 同一個畫面上並存(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1891-1900`)。

#### 2.4.5 「哪些查表、哪些寫死」一句話總表

| 代碼欄位的取值方式 | 查表還是寫死 | 典型例子 | 錨點 |
|---|---|---|---|
| UI 下拉(`UltraCombo` + `xxxDataSrc`) | **查表**(`CTL014`) | `CODM009` 的員工類別、業務員區分碼 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:571-588` |
| UI Searcher(`ucCOD006`) | **查表**(`COD006A`) | `CODM009` 的職稱、`CODM017` 的作廢原因 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:89-140` |
| UI 預設值 | **寫死** | `AO_CODE = "N"`、`MANGR_CODE = "0"`、`EMP_CD = "1"`、`FEE_CODE = "07"`、`EMP_QUOTA_CODE = "0"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:89-92`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:232-237` |
| UI 分支條件 | **寫死** | `if (row.MOD_FLAG == "N")`、`ucomEMP_CD.Value == "1"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357` |
| UI 過濾字串 | **寫死,而且是 SQL 片段** | `custCANCEL_CD_0.Filter = "CODE NOT IN ('01','02','03','04','05')"` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38` |
| PO 分支條件 | **寫死** | `if (row.CODE_SORT != "C1") return;` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` |
| PO 寫入值 | **寫死** | `[CTL_SRNO_ID] = '2'` / `= '0'` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109` |
| PO 查詢條件 | **寫死** | `AND CTL_SRNO_ID='1'`、`AND CTL_SRNO_ID<>'0'` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672` |
| 共用 PO 的代碼種類 | **寫死** | `WHERE CODE_SORT= '17'` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| 共用 PO 的部門白名單 | **寫死**〔客戶特定〕 | `DEPT_NO IN('G2','G11','G15','GC')` 等四組 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:378`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:392`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:401`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:408` |
| 程式常數 | **有寫但幾乎沒人用** | `YES_NO` 699 次是例外;`CODE_SORT` / `CTL_SRNO_ID` 都是 0 次 | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10`、`Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993` |

**一句話:UI 下拉與 Searcher 查表;其餘全部寫死。**

### 2.5 欄位中文名總表(來自 xsd `msdata:Caption`)

中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**;xsd 沒填的改用控件 Label 或 DB 註解,並在「來源」欄註明。四眼 13 欄與 `DATAID` / `DATAFLAG` 不重複列(全模組只有 `CODB009Model.xsd` 那一份有中文名)。

| 表 | 欄位 | 中文名 | 型別 | 來源 |
|---|---|---|---|---|
| `COD005A` | `CODE_SORT` | 代碼種類 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:177` |
| `COD005A` | `CODE_SORT_DESCRP` | 代碼種類說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.designer.cs:197` |
| `COD006A` | `CODE_SORT` / `CODE` / `CODE_DESCRP` | 代碼種類 / 代碼 / 代碼說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:222`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:253`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.designer.cs:233` |
| `COD006A` | `MOD_FLAG` | **可否異動註記** | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:116` |
| `COD006A` | `VALID_CODE` / `SHOW_ORDER` | 有效碼 / 顯示順序 | string / int | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM006Model.xsd:123-124` |
| `COD006A` | `M_CODE` | (無) | string | —— |
| `COD007A` | `CODE_SORT` / `RANGE_CODE` / `RANGE_CODE_DESCRP` | 代碼種類 / 級距代碼 / 級距代碼說明 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:211-242` |
| `COD007A` | `MIN_VALUE` / `MAX_VALUE` | 級距下限 / 級距上限 | decimal | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.Designer.cs:262-273` |
| `COD007A` | `MOD_FLAG` | **客戶異動註記** | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM007Model.xsd:55` |
| `COD009` | `EMP_NO` / `EMP_ID_NO` | 員工代碼 / 員工身分證字號 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:25`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:32` |
| `COD009` | `EMP_NAME` / `EMP_NAME_ENG` | 員工中文姓名 / 員工英文姓名 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:39-46` |
| `COD009` | `DEPT_NO` / `DEPT_SH_NM` | 部門代碼 / 部門中文簡稱(join) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:53`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:150` |
| `COD009` | `AO_CODE` / `AO_DATE` | 業務員區分碼 / 業務到職日 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:60` |
| `COD009` | `ENTRY_DATE` / `LEAVE_DATE` | 進公司日期 / 離職日期(`yyyyMMdd`) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:67-68` |
| `COD009` | `UID_CODE` / `MANGR_CODE` / `DAM_CODE` | 系統使用者代號 / 基金經理人 / 全委經理人別 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:69`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:76` |
| `COD009` | `EMP_CD` / `EMP_MEMO` / `POSI_CODE` / `EMP_EMAIL` / `TEST_YN` | 員工類別 / 備註說明 / 職稱 / EMAIL / 試用期滿 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:83`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:90` |
| `COD009` | `IS_COMP_FEAT` / `IS_UPDATE_OFD195` / `BEF_EMP_CD` / `BEF_IS_COMP_FEAT` | 是否為公單 / 修改時是否更新優惠關系人資料 / 更改前員工類別 / 更改前是否為公單 | string / boolean | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:160-161` |
| `COD009` | `TO_EMP_NO` / `AGENT_ID` / `AGENT_CODE` | 通知對象員工代碼 / 業務歸屬銷售機構區分碼 / 業務歸屬銷售機構 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:185-187` |
| `COD009` | `G_JOB_CODE` / `PROBATIONENDDATE` / `JOB_CODE` | 通路職務別 / 試用期滿日 / 職位代號 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd:189-191` |
| `COD009` | `SALE_DEPT_NO` `UPD_DATE` `UPD_TIME` `UPD_USER` `EMP_QUOTA1`–`3` `FEE_CODE` `EMP_QUOTA_CODE` `OUTBOUND` `ADD195` | **全部沒有中文名** | —— | —— |
| `COD010` | `EMP_NAME` / `EMP_ID_NO` / `EFFECTIVE_DATE` / `TERMINATE_DATE` | 員工姓名 / 員工ID / 生效日期 / 終止日期 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM010Model.xsd:110-146` |
| `COD010` | `REL_ID_NO` / `REL_NAME` / `REL_CODE` / `BIR_DATE` | 身分證字號 / 姓名 / 親屬關係代碼 / 出生日期 | string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.Designer.cs:301-358` |
| `COD016` | `FUND_SH_NM` | 基金簡稱(join) | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM016Model.xsd:93` |
| `COD016` | `FUND_ID` / `BNG_CTL_SRNO` / `END_CTL_SRNO` | 基金代碼 / 流水號起號 / 流水號迄號 | string / decimal | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.Designer.cs:189-213` |
| `COD017` | `BF_CTL_SRNO` / `BF_CER_NO` / `CANCEL_CD` / `CTL_SRNO_ID` | 紙張流水號 / 受益憑證號碼 / 作廢原因 / 流水號識別碼 | decimal / string | Label `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.Designer.cs:183-377`(**xsd 一個 Caption 都沒有**) |
| `COD040A` | `MIN_VALUE` / `MAX_VALUE` / `VAL_DESC` | 級距下限(Caption 開頭多一個空白)/ 級距上限 / 級距說明 | decimal / string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM036Model.xsd:28-30` |
| `CTL014` | `TEXTVALUE` / `DISPLAYNAME` | 代碼 / 下拉式選單 | string | xsd `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:18-19` |
| `CTL014` | `DISPLAYORDER` | 顯示順序 | Model `string` / **View `int`** | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:20` 對 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:20` |
| `CTL014` | `ISDEFAULT` | Model「是否預設值」/ **View「是否預設值0:是;1:否」** | Model `string` / View `int` | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd:21` 對 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:21` |

四件要記住的:

1. **`MOD_FLAG` 在兩張表的中文名不一樣**(`COD006A`「可否異動註記」/ `COD007A`「客戶異動註記」),而程式的用法完全相同(都是 `== "N"` 就鎖住畫面) —— 至少有一邊的 Caption 是錯的。

2. **`CTL014` 的 Model 與 View 不同構**,兩欄 string 對 int;View 的 Caption 還說 `0` 是、`1` 否,與欄位名 `ISDEFAULT` 的直覺相反。UI 的檢核 `row.ISDEFAULT != 1 && row.ISDEFAULT != 0` 兩個值都收(`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs:125-129`)。

3. **`CTLB014Model.xsd` 內缺了 `SOURCETYPE` / `DESCRIPTION` / `USERID` 三欄**,而 PO 的 `INSERT` 確實會寫它們(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`) —— 這三個值從 `Utility.Parameters` 來,不從 DataSet 來。

4. `COD009` 的 `UPD_DATE` / `UPD_TIME` / `UPD_USER` 與四眼的 `UPDATEDATE` / `UPDATEID` **並存且語意重疊**,`CODM009` 新增時一律填空字串(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:233-235`),修改時完全不碰。

### 2.6 與其他模組共用的表

掃描器回報「無跨模組共用表」,因為它只看 `MasterTable` / `DetailTable` 的宣告。**實際上 COD 的表是全庫被讀最多的一組**(詳細影響面見 §8):

| 表 | 本模組外的引用檔數 | 最大宗的讀取端 |
|---|---|---|
| `COD009` | 113 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536`(共用員工查詢)、`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`(RSP 當主檔用) |
| `COD006A` | 59 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs`(共用 Searcher) |
| `COD017` | 6 | Common 4、OFD 2 |
| `COD010` | 4 | RSP / OFD / EC.Query 各 1、Common 1 |
| `COD005A` | 1 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:104-158` |
| `COD007A` | 1 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`(只用來排除,不取值) |
| `COD016` / `COD040A` | 0 | 只有本模組 |

反過來,COD **借用**別人的是唯讀 join 六張(`OFD002` 部門、`OFD068A` 銷售機構、`OFD081` 基金、`OFD115A` 列管、`OFD195A` 優惠關係人、`OFD721` 憑證),外加會被寫入的平台庫兩張 `AA_USER` 與 `TODO`(§8.5)。

### 2.7 狀態碼(從程式反推,標來源)

| 欄位 | 在哪張表 | 值域 | 來源 |
|---|---|---|---|
| `STATUS` / `Status` | 六張有四眼的表 | 12 個 `EVAStatusCode` 常數,實際字面值查不到 | 見 `architecture.md §3.10`,本模組沒有任何程式直接比對 `STATUS` |
| `CTL_SRNO_ID` | `COD016` / `COD017` | `0` 未使用 / `1` 已使用 / `2` 作廢 | 類別定義在 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007`;程式端全部寫死字面值(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:107`) |
| `CER_STATUS` | `OFD721`(join 來的) | 只知道 `2` 代表「還沒送簽、可以作廢」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:82-84`;其餘值域不在本模組 |
| `MOD_FLAG` | `COD006A` / `COD007A` | `Y` / `N`;`N` 代表畫面鎖定 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110`;新增一律給 `Y`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174`) |
| `VALID_CODE` | `COD006A` | 走 `CTL014` 的 `SourceType = 004` | `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17`;新增預設 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:38`) |
| `IS_COMP_FEAT` | `COD009` | `Y` 公單 / `N` 非公單;非公單時身分證字號變必填 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:467-477` |
| `LEAVE_DATE` | `COD009` | 「在職」有**三種**判斷法,見附錄 E.3 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695` |
| `ISDEFAULT` | `CTL014` | `0` / `1`,語意依 Caption 是「0:是;1:否」 | `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd:21` |

## 3. 畫面清冊

掃描器母體:畫面 12(B 4 / I 0 / M 8 / R 0)· 表 6 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 0 · Service 0。另有一支代號屬 CTL 但檔案在本專案內的 `CTLB014`(§8.3)。

### 3.1 維護 M(8 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `CODM005` | 代碼種類維護(推測) | 齊 | `COD005A` | 無 | 無 | 無 |
| `CODM006` | 一般代碼維護(推測) | 齊 | `COD006A` | 無 | 無 | 無 |
| `CODM007` | 級距代碼維護(推測) | 齊 | `COD007A` | 無 | 無 | 無 |
| `CODM009` | 員工資料維護(推測) | 齊 | `COD009` | 無 | 無 | 無 |
| `CODM010` | 員工親屬維護(推測) | 齊 | `COD010` | 無 | 無 | 無 |
| `CODM016` | 憑證流水號區間維護(推測) | 齊 | `COD016` | 無(另寫 `COD017`) | `s_CODM016`(不在版控) | 無 |
| `CODM017` | 憑證作廢 / 取消作廢(推測) | 齊 | **未宣告**(實體表 `COD017`) | 無 | 無 | 無 |
| `CODM036` | 級距設定(推測,業務不明) | 齊 | `COD040A`(掃描器漏) | 無 | 無 | 無 |

### 3.2 查詢 I

**本模組無 I 畫面。**原因見 §5。

### 3.3 批次 B(4 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 寫哪張表 | 觸發 |
|---|---|---|---|---|---|
| `CODB000` | 待辦事項清除(推測) | **缺 model / view 的 xsd**(有手寫 `.cs`,§3.5) | 無宣告 | `TODO` | 使用者按執行 |
| `CODB009` | 員工銷售機構批次回填(推測) | 齊 | `COD009` | `COD009` | 使用者按執行 |
| `CODB901` | 員工旗標維護(推測) | **缺 model / view**(借 `CODB009` 的) | 無宣告 | `COD009` | 使用者按執行 |
| `CODB902` | 使用者帳號解鎖 / 補發密碼(推測) | **缺 model / view**(借 `CODB009` 的) | 無宣告 | `AA_USER` + `CODB902` | 使用者按執行 |

### 3.4 報表 R

**本模組無 R 畫面、無 `.rpt` 檔。**原因見 §7。

### 3.5 「六層不齊」的三支到底缺不缺

`architecture.md 附錄 D.4` 把「六層不齊」拆成假警報與真缺。COD 的三支兩種情況都有:

| 代號 | 掃描器說 | 實情 | 錨點 |
|---|---|---|---|
| `CODB000` | 缺 model / view | **假警報。**Model 與 View 存在,只是手寫成 `.cs` 而不是由 xsd 產生:`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB000Model.cs` 與 `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CODB000View.cs`。掃描器以「代號 + `Model.xsd`」字面比對,所以判缺 | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB000_Ctl.cs:41-56`(確實在用 `CODB000ModelVDB` / `CODB000ViewVDB`) |
| `CODB901` | 缺 model / view | **真缺,而且是故意的。**Ctl 明白寫著 `base.ViewVDBType = typeof(CODB009ViewVDB);//借codb009的view來用`,Model 端直接用泛用的 `BasicModelVDB` | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB901_Ctl.cs:37-42` |
| `CODB902` | 缺 model / view | 同上 | `Dev/ATLAS.COD/Source/Control/Control.COD/CODB902_Ctl.cs:37-42` |

**借 view 的後果**:`CODB901` / `CODB902` 的 UI 建的是 `new CODB009ViewVDB()`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:36`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:37`),但兩支畫面根本不用它的 `COD009` 資料表 —— 所有輸入都塞在 `Util.Parameters` 裡。所以**改 `CODB009` 的 xsd 會連帶重編這兩支**,即使它們一個欄位都沒用到。

`Dev/ATLAS.COD/Source/Control/Control.COD/CODB901_Ctl.cs:54-63` 的 `CustomTransferOracleModelToView` 也因此是空的:宣告了 `view` 與 `model` 兩個區域變數,一個欄位都沒搬,只 `AcceptChanges()` 就 return。

### 3.6 一眼看出差別的五件事

| 差別 | 哪幾支 |
|---|---|
| PO 基底(錯誤回報風格 / 交易邊界 / 事件簽名三者都不同,`architecture.md §3.1`) | `BaseEVADaoPO` 六支(`CODM005` `CODM006` `CODM007` `CODM009` `CODM010` `CODB009`)、`BasicEVAPO` 兩支(`CODM016` `CODM017`)、`BaseMultiRowEVADaoPO` 一支(`CODM036`)、不繼承兩支(`CODB000` `CTLB014`) |
| SQL 方言(複製貼上會直接炸) | `CODM016` / `CODM017` 是 SQL Server(`[]` `@` `GetDate()` `dbo.`);其餘是 Oracle(`:` `sysdate` `ROWNUM`) |
| 有沒有 `BeforeSelect` | 七支有;`CODM005` **沒有**,查詢 SQL 由框架自動產生,結果只有 `COD005A` 自己的欄位 |
| 四眼完不完整 | `CODM005`–`CODM010` 完整;`CODM016` 靠 `After*` 補;`CODM017` 完全沒有;四支 B 全部繞過 —— 「有沒有被覆核過」在 `COD017` 與 `CTL014` 上沒有意義 |
| 卡控在哪一層 | `CODM005` / `CODM006` 有伺服端卡控;其餘六支 M 的卡控 100% 在用戶端,繞過 UI 就全部失效 |

## 4. 維護畫面(M)— 一支一節

```text
[圖] COD 八支維護畫面從按鈕到四眼引擎的卡控順序，以及各畫面掛了哪些事件
圖中文字:① 用戶端：八支 M 的卡控幾乎全在這一層 / Before*ButtonClicked / Add/Modify/Delete/Search / DoValidate() / 各畫面自寫 / validatorManager1 / 必填格式 框架決定 / Pxy 直呼 DB 檢核 / Check chkExists CHECK / ② 五種卡控結果在本模組的分佈（見各節卡控總表） / 阻擋 / e.Cancel 或 args.Cancel / 詢問 / Warn02 按取消才擋 / 警示不擋 / 顯示訊息但不 Cancel / 過濾無提示 / ROWNUM 與參數分支 / 記錄不擋 / CODB902 寫執行歷程 / ③ 伺服端 PO 事件：八支裡只有四支真的擋得住 / BeforeSelect 換 SQL / M005 以外的七支 / BeforeUpdate 擋修改 / CODM006 列管原因 / BeforeDelete 擋刪除 / CODM006 列管原因 / Delete 覆寫 / CODM005 查有無下層 / ④ After*：掛了但整段被註解的，比真的有動作的多 / CODM009 AfterUpdate / 只清 LEAVE_DATE / CODM009 AfterAdd Delete / 整段被註解 空殼 / CODM010 四個 After / 整段被註解 空殼 / CODM016 三個 After / 呼叫 SP 並刪 COD017 / ⑤ 三支不走一般四眼：兩支手寫 SQL、一支多筆版 / CODM017 BasicEVAPO / 無 MasterTable 手寫 SQL / CODM036 多筆版 / BaseMultiRowEVADaoPO / CODM016 舊世代 / TableMapping 非 x 版
```

*圖:圖 3 卡控與四眼順序。橘框＝本模組寫的程式碼；黑框＝框架（無原始碼，從呼叫端反推）；橘虛框＝寫死值、空殼或會咬人的行為。任一層 Cancel 或 throw，後面全部不執行。*

本節每一支的格式相同:用途 → 畫面結構 → 存檔前檢核 → PO 事件 → 跨表更新 → 卡控總表。卡控結果一律五類:**阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋**。

### 4.1 `CODM005` — 代碼種類維護

**用途(推測)**:維護「有哪些代碼類別」。`COD005A` 一列一個 `CODE_SORT`。

**畫面結構**:`xMaintainForm`,兩個 Tab(查詢 / 明細)。查詢條件只有一個:代碼種類 `LIKE`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:47-52`)。明細頁只有代碼種類與代碼種類說明兩個欄位,新增時代碼種類可輸入、修改時鎖定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:79`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:89`)。兩個輸入框都套 `AsciiOnlyUtility` 限制只能打半形(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:29-30`)。

**存檔前檢核**:新增與修改都只呼叫 `DoValidate()`,而 `DoValidate()` 裡只有框架的必填檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:110-114`)。**沒有任何自訂規則。**

**刪除前檢核 —— 一個活的、一個死的**:

- **死的(UI)**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:116-134` 建了一個 `view2`、塞好參數,然後**呼叫 Proxy 那一行是被註解掉的**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:123`)。接著判斷 `view2.Util.Result.Rows.Count > 0` —— 一個從沒被填過的結果集,永遠是 0,所以底下的錯誤訊息**永遠不會出現**。Proxy 端的 `CheckCodeSort` 方法本身也整支被註解(`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM005_Pxy.cs:134`)。

- **活的(PO)**:同一條規則在伺服端用**覆寫 `Delete`** 的方式實作 —— `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232` 先呼叫 `CHECK_CODE_SORT`,查 `COD007A` 與 `COD006A` 的 `UNION` 有沒有這個 `CODE_SORT`,有就把 `Result` 換成失敗並**直接 return,不進 `base.Delete`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:167-205`)。

也就是說這條卡控**確實擋得住**,只是擋在伺服端、UI 那段是殘骸。兩段訊息文字還不一樣(UI 版多了代碼種類的值)。

**PO 事件**:一個都沒掛。`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:46-54` 的建構子只設 `MasterTable`。因此**查詢 SQL 由框架產生**,`CODM005` 是全模組唯一沒有 `BeforeSelect` 的 M 畫面。

**Control 層**:`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:48-94` 是四支基本動作,`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:100-157` 是六支 EVA 動作(取待辦 / 驗證 / 覆核 / 反刪除 / 退回 / 重送)。`CustomTransferSQLModelToView` 照例是 `NotImplementedException`(`Dev/ATLAS.COD/Source/Control/Control.COD/CODM005_Ctl.cs:179-187`)。

**跨表更新**:無。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填與格式 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:110-114` |
| 刪除前(UI) | 該代碼種類是否已被 `COD006A` / `COD007A` 使用 | **永遠不成立**(Proxy 呼叫被註解) | 阻擋(實際失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:118-128` |
| 刪除(PO) | 同上,`SELECT count(*)` 兩表 `UNION` | 回傳失敗訊息,不執行刪除 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:219-232` |
| 刪除(PO)例外時 | `CHECK_CODE_SORT` 的 `catch` 只呼叫 `HandleBusinessException`,`strResult` 維持空字串 | 檢核**視為通過**,照常刪除 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:195-198` |

**要注意的**:`CHECK_CODE_SORT` 的 SQL 用字串串接 `strCODE_SORT`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:183`),值來自 DataSet 而非直接的使用者輸入,但路徑上沒有任何跳脫。整支 PO 1,188 行裡**只有約 40 行是活的**,其餘全是被註解的舊實作(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:233-1064` 是一整個 `#region 註解`)。

### 4.2 `CODM006` — 一般代碼維護

**用途(推測)**:維護某個代碼種類底下的代碼值與中文說明。`COD006A` 一列一個 `CODE_SORT` + `CODE`。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件:代碼種類(Searcher,`=`)與代碼(`LIKE`)(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:92-102`)。明細頁欄位:代碼種類、代碼、代碼說明、有效碼(下拉)、顯示順序(數值,預設 1)。

**三個下拉 / Searcher 的來源**:

| 控件 | 來源 | 錨點 |
|---|---|---|
| 代碼種類 `custCODE_SORT` | `ucCOD005ForCODM006`,帶 `ProgramID = "CODM006"`,底層 SQL 是「`COD005A` 裡**還沒被 `COD007A` 用掉**的種類」 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:58-59` 配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-637` |
| 有效碼 `ucomVALID_CODE` | `ValidCodeChDataSrc` → `CTL014` 的 `SourceType = 004` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:68` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17` |
| 結果 grid 的 `MOD_FLAG` | `YesNoDataSrc` → `CTL014` 的 `SourceType = 000` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:62` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/YesNoDataSrc.cs:18` |

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:182-223`)** 共三段,順序固定:

1. **只在新增模式**:呼叫 `Check`,查這個代碼種類是不是已經出現在 `COD007A`(級距代碼)裡。是就加錯誤訊息「此'代碼種類',已存在COD007A中,請重新選擇!」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:75-129`)。

2. **新增與修改都做**:`chkExistsOrder` —— 同一種類下有沒有別的代碼用了相同的顯示順序。有就跳 `Warn02` 對話框「此'代碼種類-顯示順序',已存在!確定存入?」,**按取消才擋**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:138-178`)。

3. **同上**:`chkExistsDES` —— 同一種類下有沒有別的代碼用了相同的中文說明。同樣是詢問式(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:187-227`)。

第 2、3 段的 SQL 是**參數化**的(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:153-156`),第 1 段是**字串串接**的(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:99`)。同一支 PO 內兩種安全等級並存。

**`MOD_FLAG` 的鎖定行為**:進修改模式前先看 `MOD_FLAG`,是 `"N"` 就把修改鈕與刪除鈕關掉、代碼說明設唯讀(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:74-90`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:104-134`)。新增時一律寫 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`),所以「不可異動」這件事只能靠直接改資料庫來設定。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:43-48`)**:六個掛點,其中兩個是本模組僅有的伺服端業務卡控。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | 換成自己的 SQL(`COD006A` `LEFT JOIN` `COD005A` 取種類說明) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:394-432` |
| `BeforeUpdate` | **只對 `CODE_SORT = "C1"` 生效**:若這個代碼已被 `OFD115A` 當成列管原因用過,則只允許改中文說明;其他欄位有變就 `args.Cancel = true`,訊息「已作為列管原因,僅可修改列管原因中文說明」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:336-366` |
| `BeforeDelete` / `BeforeApproveDelete` | 同上條件,已被列管用過就完全不准刪,訊息「已作為列管原因,不可刪除」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:368-392` |

**`"C1"` 是寫死的**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372`),而且不在 `CODCode.cs` 的 `CODE_SORT` 清單裡。〔客戶特定〕

`BeforeUpdate` 的實作值得看仔細:它先查 `OFD115A` 有沒有用這個代碼,**沒有就直接 return 放行**;有的話再查 `COD006A` 裡「種類 + 代碼 + 顯示順序 + 有效碼」四個值是否與畫面送來的完全相同,相同才放行。也就是「只准改中文說明」是靠「其他四欄都沒變」反推出來的。兩段 SQL 都是 `string.Format` 串接(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:351-353`)。

**跨表更新**:無(只讀 `OFD115A` 與 `COD005A`、`COD007A`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增前 | 代碼種類已存在於 `COD007A` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:109-113` |
| 新增 / 修改前 | 同種類下顯示順序重複 | `Warn02` 對話框 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:208-211` |
| 新增 / 修改前 | 同種類下代碼說明重複 | `Warn02` 對話框 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:218-221` |
| 進入修改模式 | `MOD_FLAG = "N"` | 修改鈕 / 刪除鈕變灰 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:79-83` |
| 伺服端修改 | `C1` 種類且已被 `OFD115A` 列管,且四欄有變 | `args.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:354-358` |
| 伺服端刪除 / 覆核刪除 | `C1` 種類且已被 `OFD115A` 列管 | `args.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:382-385` |
| 種類下拉取值 | 已被 `COD007A` 用掉的種類不出現在下拉 | 下拉清單少幾筆 | 過濾(無提示) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:614` |
| 上述任一檢核發生例外 | `catch` 只呼叫 `HandleBusinessException`,`Cancel` 不設 | **放行** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:362-365`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:388-391` |

### 4.3 `CODM007` — 級距代碼維護

**用途(推測)**:維護用數值區間表示的代碼。`COD007A` 一列一個 `CODE_SORT` + `RANGE_CODE`,帶 `MIN_VALUE` / `MAX_VALUE`。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件:代碼種類(`=`)與級距代碼(`LIKE`)(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:126-137`)。明細頁:代碼種類、級距代碼、級距代碼說明、級距下限、級距上限。

**種類下拉走的是另一半**:同樣用 `ucCOD005ForCODM006`,但 `ProgramID = "CODM007"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:45-46`)。共用 PO 的分支是 `if (strID == "CODM006")` 走「排除 `COD007A`」那條、`else` 走「排除 `COD006A`」那條(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:634-637`)。**注意這是 `else` 不是 `== "CODM007"`** —— 任何沒帶 `ProgramID` 或帶錯值的呼叫端,都會**靜默拿到 `CODM007` 的清單**。

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:176-201`)** 三段:

1. 級距上限必須大於下限(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185`)。兩邊都不是 `DBNull` 才比,所以**只填一邊時這條不生效**。

2. 呼叫 `Check`,查這個代碼種類是不是已經出現在 `COD006A` 裡(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:233-293`)。

3. 框架必填檢核 `validatorManager1.DataValidate()`,**寫在最後一行**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:199`)。

**沒有任何檢核擋「同一種類下兩個級距重疊」或「級距之間有空隙」。**這是本節最值得記住的一件事。

**`MOD_FLAG` 的鎖定行為**:與 `CODM006` 相同,`"N"` 就鎖死整個明細頁(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110`);新增一律寫 `"Y"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174`)。

**PO 事件**:只有三個 `Before*`,全部只做「換 SQL」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:49-51`)。查詢 SQL 是 `COD007A` `LEFT JOIN` `COD005A`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:156-222`)。

**SQL 裡的兩個毛病**:

- `MOD_FLAG` 被 `SELECT` 了兩次(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:170-171`)。Oracle 允許重複欄名,`DataAdapter` 填進 typed DataSet 時會產生第二個欄位 —— 能不能對上 xsd 取決於框架的 `MissingSchemaAction`,本機看不到。

- 兩個查詢條件都是字串串接,而且 `LIKE` 的 `%` 直接接在使用者輸入後面(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:188-192`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:202-206`)。

**跨表更新**:無。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 上限 ≤ 下限 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182-185` |
| 新增 / 修改前 | 上限或下限只填一邊 | **不檢查** | —— | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:182` |
| 新增 / 修改前 | 同種類下級距重疊 / 有空隙 | **不檢查** | —— | —— |
| 新增 / 修改前 | 代碼種類已存在於 `COD006A` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:269-273` |
| 新增前 | `e.Cancel` 設定後仍繼續存取 `Rows[0]` 並寫 `MOD_FLAG` | 若結果集為空會丟例外 | (缺陷,見附錄 E) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:163-175` |
| 進入修改模式 | `MOD_FLAG = "N"` | 整頁唯讀 + 按鈕變灰 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:101-110` |
| 種類下拉取值 | 已被 `COD006A` 用掉的種類不出現 | 下拉清單少幾筆 | 過濾(無提示) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:619` |
| `Check` 發生例外 | `catch` 把 `Result` 設成 `false` / 空訊息 | 檢核視為通過 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:281-286` |

### 4.4 `CODM009` — 員工資料維護

**用途(推測)**:維護 `COD009`。全模組最大的一支(UI 672 行、PO 758 行),也是全系統最多人 join 的那張表的唯一四眼入口。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件三個:員工代碼(`LIKE`)、中文姓名(`LIKE`)、身分證字號(`=`),後兩者空白就不加條件(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:168-181`)。明細頁二十幾個欄位,下拉與 Searcher 的來源:

| 控件 | 欄位 | 來源 | 錨點 |
|---|---|---|---|
| `ucomAO_CODE` / `ucomMANGR_CODE` / `ucomDAM_CODE` / `ucomEMP_CD` | 業務員區分碼 / 基金經理人 / 全委經理人別 / 員工類別 | `AoCodeDataSrc` `MangrCodeDataSrc` `EmpCdDataSrc` → `CTL014` 的 `003` `001` `002` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:577-583` 配 `Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/EmpCdDataSrc.cs:18` |
| `ucomAGENT_ID` | 銷售機構區分碼 | `GetDropDownDataSrc("062")` → `CTL014` `062` = `TRUST_AGENT_ID` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:585` 配 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050` |
| `ucomG_JOB_CODE` | 通路職務別 | `GetDropDownDataSrc("701")` → `CTL014` `701`,**`CTL014.cs` 無對應類別** | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587` |
| `custPOSI_CODE` | 職稱 | `ucCOD006` → `COD006A` 某個 `CODE_SORT` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1891` |
| `custJOB_CODE` | 職位代號 | `ucCTL014`(**repo 內無原始碼,從呼叫端反推**)→ `CTL014` `702` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1900` 配 `DB/Table/updateCOD009.sql:17` |
| `custTO_EMP_NO` | 通知對象員工代碼 | `ucEmployeeData` → `COD009` 自己 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1893` |
| `custAGENT_CODE` | 業務歸屬銷售機構 | `ucAgentCode` → `OFD068A` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.Designer.cs:1896` |

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:456-497`)**:

1. 先跑框架必填,**有錯就直接 return**,底下四段都不執行(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:462-465`)。

2. 非公單(`IS_COMP_FEAT` 沒勾)時:身分證字號必填;有填就呼叫 `CHECK_ID_EXIST` 查重(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:467-477`)。

3. 英文姓名只能英數(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:479-482`)。

4. 業務到職日不得小於進公司日(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:484-485`)。

5. 系統使用者代號有填時呼叫 `CHECK_UID_CODE` 查重(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:488-496`)。

**兩支查重的行為差很多**:

| 方法 | SQL | 「在職」怎麼定義 | 判斷式 | 錨點 |
|---|---|---|---|---|
| `CHECK_UID_CODE` | 同一個系統使用者代號、不同員工代碼、且在職 | `NVL(LEAVE_DATE, ' ') = ' '` | `> 0` 就擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:389-402` |
| `CHECK_ID_EXIST` | 同一個身分證字號、不同員工代碼、且在職 | `(LEAVE_DATE = '19000101' or LEAVE_DATE = ' ')` | **`== 1` 才擋** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:568-581` |

兩個問題:(1) 同一支 PO 內「在職」有兩種寫法,而且 `CHECK_ID_EXIST` 那種**遇到 `LEAVE_DATE` 是 NULL 會整個條件變 UNKNOWN**,該筆不被算進去(Oracle 三值邏輯);(2) `== 1` 表示**已經有兩筆以上重複時反而放行**。兩條都列在附錄 E。

**身分證與 EMAIL 的格式檢核是「可忽略」的**:`CheckID` / `CheckEMail` 跳 `Warn03` 三選一對話框,按「否」才擋,按其他就用 `ByPassAddMessage` 記一筆放行(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:510-544`)。

**修改時的兩條特別規則**:

- **離職日不得小於進公司日**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:306-317`)。注意它先排除 `1900/1/1`,所以用 `1900/1/1` 當「沒離職」的哨兵值。

- **「是否同步更新優惠關係人資料」的詢問**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:320-331`):五個條件同時成立才跳 —— 原本有離職日、現在清空、員工類別是正式員工、原本也是正式員工、現在與原本都不是公單。按確定就把 `IS_UPDATE_OFD195` 設 `true` 帶到 PO。**但 PO 端沒有任何一行程式讀這個欄位**(整段 `AfterAdd` / `AfterDelete` 被註解,見下)。也就是這個問句問完不會發生任何事。

- 這段條件裡「正式員工」用的是常數 `EMP_CODE.Staff`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:324`),而 40 行之後同一個意思寫成字面值 `"1"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357`)。同一支檔案兩種風格。

**刪除前檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:387-445`)**:

1. `CheckEmpNo` —— 查 `COD010` 還有沒有這位員工的親屬,有就擋(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:602-650`)。

2. 「檢核是否已有契約異動資料」整段被註解(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421`)。PO 端的 `CheckRspChgDate` 還活著,但**沒有任何呼叫端**。

3. `CheckOFD195` —— 查 `OFD195A` 有沒有這位員工的優惠關係人資料,有就跳一個 `Warn01` 訊息「請記得至優惠關係人檔刪除該筆身份資料」,**沒有 `e.Cancel`**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429`)。使用者按掉就繼續刪。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:36-45`)**:掛了六個,其中三個是空的。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetToDoData` | 換 SQL(`COD009` `LEFT JOIN` `OFD002`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:343-368` |
| `BeforeUpdate` | **整支是空的**(只有一對大括號) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:370-373` |
| `AfterUpdate` | 若畫面送來的 `LEAVE_DATE` 是空字串,就下一道 `UPDATE` 把它設成真正的 `NULL` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:63-80` |
| `AfterAdd` | **整段被 `/* */` 註解**(原本要維護 `OFD195A`) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` |
| `AfterDelete` | **整段被 `/* */` 註解**(原本要設 `OFD195A` 的終止日) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:251-274` |

`AfterUpdate` 那一道補救 `UPDATE` 值得說明:四眼引擎寫回去的是畫面送來的空字串,而 `COD009` 的 `LEAVE_DATE` 是字串欄位,空字串與 NULL 在 Oracle 其實同義 —— 但 `CHECK_UID_CODE` 用 `NVL(LEAVE_DATE,' ') = ' '`、`CHECK_ID_EXIST` 用 `LEAVE_DATE = ' '`,兩者對 NULL 的處理不同,所以這道補救**只讓其中一支查重正確**。

**跨表更新**:目前一個都沒有(全被註解)。設計上原本要同步維護 `OFD195A`。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填與格式 | 訊息清單並提前 return | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:460-465` |
| 新增 / 修改前 | 非公單卻沒填身分證字號 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:473-476` |
| 新增 / 修改前 | 身分證字號重複(在職且不同員工代碼,且**恰好一筆**) | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:579-580` |
| 新增 / 修改前 | 身分證 / 統編格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:514-525` |
| 新增 / 修改前 | EMAIL 格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:531-542` |
| 新增 / 修改前 | 英文姓名含非英數 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:479-482` |
| 新增 / 修改前 | 業務到職日 < 進公司日 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:484-485` |
| 新增 / 修改前 | 系統使用者代號已被別的在職員工用 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:401-402` |
| 修改前 | 離職日 < 進公司日 | 訊息清單 + return | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:310-316` |
| 修改前 | 非正式員工 / 改成公單且 `OFD195A` 有資料 | `Warn01` 提示,不擋 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:284-287` |
| 修改前 | 五條件同時成立時問「是否同步更新優惠關係人」 | 設旗標,**但 PO 不讀** | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:323-331` |
| 刪除前 | 該員工在 `COD010` 還有親屬 | 訊息清單 + return | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:627-631` |
| 刪除前 | 該員工在 `OFD195A` 有優惠關係人 | `Warn01` 提示,不擋 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429` |
| 刪除前 | 該員工已有契約異動資料 | **整段被註解,不執行** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421` |
| 查詢 | 查詢條件字串串接進 SQL | 撈到資料或語法錯 | 過濾(無提示) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:526` |
| Proxy 例外 | `CHECK_UID_CODE` / `CHECK_ID_EXIST` 的 `catch` **回傳 `ex.Message`** | 例外訊息被當成檢核失敗理由顯示 | 阻擋(理由錯誤) | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:36`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:101` |

### 4.5 `CODM010` — 員工親屬維護

**用途(推測)**:維護 `COD010`。一列一位親屬,綁在一位員工底下。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件五個:親屬身分證(`=`)、親屬關係代碼(`=`)、員工代碼(`=`)、員工姓名(`LIKE`)、員工身分證(`=`),全部空白就不加(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:221-250`)。明細頁:親屬身分證、姓名、關係代碼、出生日期、員工代碼、生效日期、終止日期。

**員工 Searcher 有兩道隱藏過濾**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:151-153` 把 `custEMP_NO` 的 `LEAVE_DATE` 設成 `1900/01/01`、`IS_COMP_FEAT` 設成 `"N"`,而 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:429-432` 在每次開 Searcher 前又重設一次 `IS_COMP_FEAT = "N"`。意思是**公單員工挑不到**,而且畫面上沒有任何提示。

**存檔前檢核(`DoValidate`,`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:66-109`)** 只剩兩條活的:

1. 出生日期必填,且必須小於 AP 伺服器的系統日(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:70-80`)。

2. 生效日期必填(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:82-83`)。

中間 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` 是**三份被註解掉的舊實作**,內容都是「親屬關係代碼為未成年子女時出生日期必填」。三份寫法互不相同(一份用 `umskBIR_DATE`、兩份用已不存在的 `udatBIR_DATE`),顯示這條規則被改過三次最後整個拿掉。

**新增時多一條**:親屬身分證第一碼若是英文字母,不可小寫(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:297-312`)。身分證格式本身走 `CheckID`,同樣是 `Warn03` 可忽略式(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:398-415`)。

**修改與刪除前的 `OFD195A` 檢核**:兩處寫法一樣,都是查到就跳 `Warn01`「請記得至優惠關係人檔刪除該筆身份資料」然後**不擋**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:273-282`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:453-462`)。刪除前那段的「契約異動資料」檢核與 `CODM009` 一樣被整段註解(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451`)。

**`CheckOFD195` 的 SQL 有一條反直覺的條件**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:692-697`):

```
WHERE REL_TYPE='1' AND REL_NO=:REL_NO AND REL_IDNO=:REL_IDNO
  AND REL_NO NOT IN (SELECT EMP_NO FROM COD009 WHERE IS_COMP_FEAT = 'N' AND EMP_CD = '1')
```

最後一行把「非公單的正式員工」整批排除掉。也就是**正常員工的親屬永遠查不到優惠關係人資料,提示永遠不會跳**;只有公單或非正式員工的親屬才會跳。`CODM009` 的同名方法**沒有**這一行(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:722-725`)。兩支同名方法、兩種語意。

**PO 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:32-42`)**:掛了七個,四個是空的。

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` | 換 SQL(`COD010` `LEFT JOIN` `COD009`),而且**這一支是全模組唯一會綁參數的查詢** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:67-132` |
| `AfterAdd` / `AfterUpdate` / `AfterDelete` / `AfterUnDelete` | **四支的內容全部被註解**,只剩空方法 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:299-624` |

查詢 SQL 混用兩種風格:`REL_ID_NO` / `REL_CODE` 走字串串接的 `AddParam`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:141-175`),`EMP_NO` / `EMP_NAME` / `EMP_ID_NO` 走真正的繫結參數(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:101-118`)。同一條 SQL 兩種安全等級。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 出生日期未填或等於 `1900/01/01` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:70-71` |
| 新增 / 修改前 | 出生日期 ≥ 系統日 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:76-79` |
| 新增 / 修改前 | 生效日期未填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:82-83` |
| 新增前 | 身分證第一碼英文字母小寫 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:303-311` |
| 新增 / 修改前 | 身分證格式不符 | `Warn03`,按否才擋 | 詢問 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:402-414` |
| 新增 / 修改前 | 未成年子女必填出生日期 | **三份實作全被註解** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` |
| 修改 / 刪除前 | `OFD195A` 有該親屬資料(且員工非「非公單正式員工」) | `Warn01` 提示 | 警示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:278-281` |
| 刪除前 | 已有契約異動資料 | **整段被註解** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451` |
| 員工 Searcher | 公單員工不出現 | 挑不到人 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:429-432` |
| 終止日期 | 沒有任何「終止日 ≥ 生效日」的檢核 | —— | —— | —— |

### 4.6 `CODM016` — 憑證流水號區間維護

**用途(推測)**:替某檔基金配發一段紙張流水號(起號到迄號),存檔時由 SP 把區間展開成 `COD017` 的逐筆資料。

**畫面結構**:`xMaintainForm`,兩個 Tab。查詢條件只有基金代碼(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:78-90`)。明細頁三個欄位:基金代碼、流水號起號(唯讀)、流水號迄號。

**起號是自動帶的**:選好基金後觸發 `custFUND_ID_ValueChanged`,呼叫 `FindMaxSrno` 取該基金目前最大的迄號 +1;查不到就給 1(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:186-208` 配 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:821-895`)。**只在新增模式才帶**。

**三條伺服端往返的檢核**:

| 方法 | SQL | 用在哪 | 錨點 |
|---|---|---|---|
| `FindMaxSrno` | `SELECT FUND_ID, MAX(END_CTL_SRNO) FROM COD016 GROUP BY FUND_ID` | 帶起號、判斷是不是最後一批 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:821-895` |
| `ChkUsedData` | `COD016` `LEFT JOIN` `COD017`,區間內有 `CTL_SRNO_ID='1'`(已使用) | **宣告了但 UI 沒有任何呼叫端** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:563-638` |
| `ChkDiscardData` | 同上,條件改成 `CTL_SRNO_ID<>'0'`(已使用**或**作廢) | 修改前、刪除前 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:645-720` |

`CTL_SRNO_ID` 的三個值都寫死在 SQL 裡(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672`),而 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` 正好有對應常數。

**「只能改 / 刪最後一批」是怎麼實作的**:`CODM016_ModifyDataLoad` 在載入時就先算好 `Result = CheckMaxSrno(END_CTL_SRNO)`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:74-75`),之後修改與刪除都只看這個**快取下來的布林值**(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:116-119`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:167-170`)。畫面停留期間別人新增了一批,這裡不會知道。

**存檔的三個 `After*` 事件(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:51-53`)**:

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `AfterAdd` | 呼叫 SP `s_CODM016`,把起訖號、基金、`dataid` 與 13 個四眼欄位全部傳進去,由 SP 產生 `COD017` 的逐筆資料。`CommandTimeout = 0` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:99-143` |
| `AfterUpdate` | **先 `DELETE FROM COD017 WHERE [dataid] = @dataid`,再重跑一次 `s_CODM016`** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:145-315` |
| `AfterApproveDelete` | `DELETE FROM COD017 WHERE [dataid] = @dataid` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:317-370` |

**注意刪除的鍵是 `dataid` 而不是 `FUND_ID` + 流水號區間。**`dataid` 是四眼批次識別碼(`architecture.md §3.3`),所以「同一次 EVA 產生的 `COD017` 全部刪掉」。這是唯一把 `dataid` 當業務鍵用的地方,而 `COD017` 的 PK 是 `FUND_ID` + `BF_CTL_SRNO`。

`s_CODM016` **不在 `DB/` 底下**,`DB/SP/` 完全沒有這個檔。要知道區間怎麼展開、`BF_CER_NO` 怎麼配、有沒有檢查重疊,只能去資料庫看。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 迄號 < 起號 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:217-224` |
| 新增前 | 起號自動帶最大迄號 +1,且欄位唯讀 | 起號不可能重疊 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:56` |
| 修改前 | 區間內有已使用或已作廢的號碼 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:110-114` |
| 修改前 | 不是該基金最後一批 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:116-119` |
| 刪除前 | 區間內有已使用或已作廢的號碼 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:161-165` |
| 刪除前 | 不是該基金最後一批 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:167-170` |
| 查詢條件 | 基金代碼空白時用 `LIKE ''`、非空白用 `=` | **判斷式寫反**(`== ""` 走 `LIKE`) | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:82-89` |
| 存檔後 | SP 回傳 `i < 0` 才視為失敗 | 回 0 筆視為成功 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:139-142` |
| `ChkExsitData` | 宣告了但沒有呼叫端,且查詢條件用錯參數 | —— | (死碼,見附錄 E) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:774` |

### 4.7 `CODM017` — 憑證作廢 / 取消作廢

**用途(推測)**:針對單一張紙張流水號,做作廢或取消作廢。

**這一支不是四眼畫面**。`formstyle` 沒有宣告,但 UI 繼承的是 `xOneStepProcessForm`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:19`),PO 繼承 `BasicEVAPO` 卻沒有宣告 `MasterTable`,只有兩支手寫方法 `Get` 與 `Set`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:47`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:200`)。**它直接 `UPDATE COD017`,沒有 `STATUS`、沒有待辦、沒有覆核。**

**SQL 方言是 SQL Server**:`UPDATE [COD017] SET ... UpdateDate = GetDate()`,參數 `@` 前綴,型別用 `SqlDbType`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:74-86`)。`architecture.md §4.6` 的結論是執行期 Oracle-only —— 若該結論成立,這一支**執行期就是壞的**;若它還在跑,代表 `architecture.md §4.6` 需要修正。這條標**假設**,兩種可能本文無法從原始碼判定。

**畫面流程**:輸入基金代碼與紙張流水號 →「查詢」→ 顯示該號的受益憑證號碼與狀態 →「執行」。作廢 / 取消作廢由 `uoptAction` 單選鈕決定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:188-201`)。

**作廢原因下拉的兩道寫死過濾**:

- `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37`:`custCANCEL_CD_0.Dis = "00"` —— 排除代碼 `00`。

- `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38`:`custCANCEL_CD_0.Filter = "CODE NOT IN ('01','02','03','04','05')"` —— **一段 SQL 片段直接寫在 UI 的屬性裡**。

- 同樣五個值在 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:177-183` 又用 C# 比較寫了一次(當 `CTL_SRNO_ID != 2` 時不准挑這五個)。

作廢原因本身來自 `COD006A` 的 `CODE_SORT = '17'`,而那個 `'17'` 寫死在共用 PO(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555`)。所以「作廢原因有哪些可選」這件事,答案分散在三個檔、兩種語言、三處硬編碼。

**`Get` 的兩條分支**:`Action = "0"` 時查 `CTL_SRNO_ID <> '2'`(還沒作廢的),否則查 `= '2'`(已作廢的)(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:249-252`)。`Action` 由 `uoptAction.CheckedIndex` 直接傳(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:200`) —— 用選項的**位置**當參數值,選項順序一改語意就反。

**`Set` 的結構問題**:`cmdModify` 只在 `act` 參數存在**且**值是 `"Y"` 或 `"N"` 時才會被賦值(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:68-131`);其餘情況走到 `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132` 就對 `null` 呼叫 `AddInParameter`。而 `catch` 區塊裡 `tran.Rollback()` 在 `tran` 可能為 `null` 時執行(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:178-186`),真正的錯誤會被 `NullReferenceException` 蓋掉。

還有一個**綁了但沒用的參數**:`@CTL_SRNO_ID` 有 `AddInParameter`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:136`),但兩段 UPDATE 都是把 `[CTL_SRNO_ID]` 寫死成 `'2'` / `'0'`,SQL 裡沒有這個參數。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 / 執行前 | 共用的 `DoValidate` | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:150-186` |
| 執行前 | 要作廢但沒填作廢原因 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:157-160` |
| 執行前 | 未作廢卻按「取消作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:162-166` |
| 執行前 | 已作廢卻按「作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:167-171` |
| 執行前 | 已有受益憑證號碼卻按「取消作廢」 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:172-175` |
| 執行前 | 非作廢狀態卻挑了 `01`–`05` 的作廢原因 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:177-183` |
| 執行前 | 要作廢且已有憑證號,但 `OFD721` 的 `CER_STATUS` 不是 `2` | `Info01` + `e.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:80-88` |
| 下拉取值 | 作廢原因排除 `00` 與 `01`–`05` | 選項變少 | 過濾(無提示) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37-38` |
| 執行 | `act` 參數不是 `Y` / `N` | `cmdModify` 為 `null` → 例外 | (缺陷,見附錄 E) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132` |
| 執行 | 影響筆數為 0 | 回滾並回傳**空訊息** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:168-176` |

### 4.8 `CODM036` — 級距設定(業務不明)

**用途**:`repo` 內查不到。表叫 `COD040A`,欄位只有級距下限、級距上限、級距說明。沒有任何其他程式讀它,也沒有任何註解說明它是什麼的級距。**本文不猜。**

**這是全模組唯一的多筆(MultiRow)四眼畫面**。PO 繼承 `BaseMultiRowEVADaoPO`,`MasterTable` 是集合(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:29-36`)。UI 用一個可編輯的 grid `ugrdCODM036` 直接綁 DataSet(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:67-72`)。

**畫面行為被改造成「只有一筆資料」的樣子**:切到查詢頁時自動查詢,有資料就雙擊第一列進修改模式、沒資料就進新增模式,然後把查詢頁藏起來、刪除鈕關掉(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:34-47`);按新增鈕之後同樣流程再跑一次並 `e.Cancel = true`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:49-65`);清除鈕在修改模式下也被改成「回到第一列」(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:83-98`)。使用者看到的是一個「永遠在編輯同一組級距」的畫面。

**兩段主檔 SQL,兩種取法**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:44-75`):

| 事件 | SQL | 取到什麼 |
|---|---|---|
| `BeforeSelect` / `BeforeGetToDoData` | `SELECT DATAID, MIN_VALUE, <四眼欄位> FROM COD040A WHERE ROWNUM < 3` | **最多 2 列**,而且沒有 `MAX_VALUE` 與 `VAL_DESC` |
| `BeforeGetMaintainData` | `SELECT DATAID, MIN_VALUE, MAX_VALUE, VAL_DESC, <四眼欄位> FROM COD040A WHERE 1 = 1` | 全表 |

`WHERE ROWNUM < 3` 是寫死的,沒有 `ORDER BY`,所以「那 2 列」是哪 2 列由 Oracle 決定。搭配上面的 UI 行為(只雙擊第一列),實務上等於「隨便撈一列進來當入口」。

**grid 端的檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:102-125`)** 三條:grid 一列都沒有 →「明細資料必須輸入」;任一列上下限是空的 →「級距上限,級距下限必須輸入」並標紅(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:134-148`);編輯儲存格時檢查「上下限完全相同的另一列」並擋下(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:150-164`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:215-243`)。**只擋完全相同,不擋重疊。**

**級距連續性交給共用控件**:`LevelGridUtility`(無原始碼,從呼叫端反推)在 `InitializeLayout` 時以下限欄、上限欄、`0.01` 與 `999999999999` 建立(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:172`),並掛在 `BeforeRowInsert` / `BeforeCellUpdate` / `BeforeRowsDeleted` 三個事件上。下限欄被設成不可編輯(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:179`),推測由該控件自動接續上一列的上限。**這條推測沒有原始碼可佐證。**

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | grid 沒有任何一列 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:106-109` |
| 新增 / 修改前 | 任一列上限或下限空白 | 訊息清單 + 該列標紅 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:118-121` |
| 編輯儲存格時 | 與另一列的上下限完全相同 | 訊息 + `e.Cancel` | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:236-242` |
| 編輯儲存格時 | 級距重疊(不完全相同) | **不檢查** | —— | —— |
| 插入列時 | `LevelGridUtility` 的連續性規則 | 依控件而定 | (無原始碼) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:202-213` |
| 查詢 | `ROWNUM < 3` 且無 `ORDER BY` | 最多 2 列,順序不定 | 過濾(無提示) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` |
| grid 發生錯誤 | `ugrdCODM036_Error` 一律 `e.Cancel = true` | 錯誤被吞掉,畫面無反應 | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:258-261` |
| 刪除 | 刪除鈕在三處被強制關掉 | 這支畫面不能刪資料 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:46`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:63`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:71` |

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因有兩層,都可以從程式看出來:(1) **八支 M 畫面本身就內建查詢頁** —— `xMaintainForm` 的第一個 Tab 就是查詢(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:32`),條件、結果 grid、顯示欄位由 `App.config` 的 `ugrdResult` 宣告(`Dev/ATLAS.COD/Source/UI/UI.COD/App.config:48`),而代碼檔的查詢需求只有「用種類或代碼找一筆」;(2) **需要跨模組查員工的地方都走共用元件** —— `ucEmployeeData` 配 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 提供了三條主分支加六個附加條件的員工查詢,各模組直接嵌控件,開一支 I 畫面反而多一個入口要維護。

**唯一像 I 的畫面是 `CODB009`**:它有查詢頁、有結果 grid、有篩選器(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:39`),只是多了一個「執行」動作,所以型別碼是 `B` 不是 `I`。`architecture.md §6.4` 說的「B 跟 I 是同一份程式碼」在這裡看得很清楚。

## 6. 批次(B)與 WindowsService

```text
[圖] COD 四支批次畫面的觸發、取數、寫入與副作用
圖中文字:① 四支 B 都是 OneStep 畫面，沒有排程也沒有服務 / CODB000 待辦清除 / 查 TODO 勾選後刪 / CODB009 機構回填 / 查 COD009 勾選後改 / CODB901 旗標維護 / 改 OutBound 與代號 / CODB902 帳號解鎖 / 改 AA_USER 並寄密碼 / ② 取數：兩支有自己的 SQL，兩支根本不查 / s_GetToDoData / SP 不在版控 / BuildMasterSQLString / COD009 OFD002 OFD068A / CODB901 CODB902 / 只吃畫面參數 不查主檔 / ③ 寫入：全部繞過四眼引擎，直接下 DML / DELETE TODO / 依待辦識別碼逐筆 / UPDATE COD009 / IN 清單用字串串接 / UPDATE COD009 / 旗標與系統使用者代號 / UPDATE AA_USER / 密碼與鎖定旗標 / ④ 副作用：只有 CODB902 有，而且三件事都值得注意 / 明文亂數密碼寄信 / 寄失敗就顯示在畫面上 / INSERT INTO CODB902 / 沒有欄位清單 / catch 回傳 ex.ToString / CODB901 CODB902 都是 / 沒勾選也能按執行 / CODB000 檢核沒掛上
```

*圖:圖 4 批次流。橘框＝本模組程式碼；黑框＝無原始碼；橘虛框＝要特別留意的行為。四支全部由使用者按鈕觸發，版控內沒有任何排程設定。*

見本節首的圖。

### 6.1 四支的共同結構

| 項目 | 內容 | 錨點 |
|---|---|---|
| 畫面型別 | 四支都是 `xOneStepProcessForm`,`formstyle = "OneStep"`,一個 Tab | `Dev/ATLAS.COD/Source/UI/UI.COD/App.config:20-43` |
| 觸發 | **使用者按「執行」鈕**。repo 內沒有任何 COD 的排程設定或 WindowsService | 掃描器回報 Service 0 |
| 寫入路徑 | 四支全部**繞過四眼引擎**,PO 直接下 DML | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:36-72`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:76-137`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:56-114`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:57-166` |
| 交易與失敗回報 | 四支都自己 `BeginTransaction` / `Commit` / `Rollback`、`finally` 裡 `Dispose`;失敗訊息 `CODB000` 是空的、`CODB009` 是中文、`CODB901` 與 `CODB902` **回傳 `ex.ToString()`** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:104`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:156` |

### 6.2 `CODB000` — 待辦事項清除

**做什麼**:查出登入者名下的待辦事項,勾選後刪掉。

**取數**:呼叫 SP `s_GetToDoData`,只傳一個參數 `v_striUserID`(從 `PermissionInfo[0].UserID` 來),用 RefCursor 回一個結果集落地成 `UC0301` 這張非實體表(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:74-103`)。`CommandTimeout = 0`(永不逾時)。**這支 SP 不在 `DB/` 底下。**

**寫入**:對每一列 `IsCheck` 為真的資料下 `DELETE TODO WHERE TODODATAID = :TODODATAID`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:43-54`)。參數化,一列一次往返。

**這支的檢核沒有掛上去**:`CODB000_BeforeExecuteButtonClicked` 寫了「至少勾選一筆待辦事項」的檢核(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:85-111`),但 `InitializeComponent` 只掛了 `FormInitial` / `ExecuteDataLoad` / `RefreshPage` / `Load` 四個事件(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:254-257`),**沒有掛 `BeforeExecuteButtonClicked`**。所以一筆都沒勾也可以按執行,結果是什麼都不刪、顯示成功。

**這支沒有 Designer 檔**:`Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:143-281` 的 `InitializeComponent` 直接寫在同一個檔案裡,而且變數命名(`appearance2` / `cODB000ModelVDB` / `new string[0]`)是反編譯工具的典型輸出。`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs` 與 `Dev/ATLAS.COD/Source/Control/Control.COD/CODB000_Ctl.cs` 也是同樣的長相。**假設**:這一組的原始碼遺失過,現行版本是從 DLL 反編譯還原的。依據是三個檔同時具備上述特徵,而其餘 COD 檔案都保留了中文註解與 Designer 分離。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 至少勾選一筆 | **事件沒掛上,不執行** | (失效) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:99-105` |
| 執行 | 沒有任何一列 `IsCheck` | 迴圈跑 0 次,`Commit` 後回報成功 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:45-57` |
| 執行 | 例外 | `Rollback` + 空訊息 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:59-64` |

### 6.3 `CODB009` — 員工銷售機構批次回填

**做什麼**:依員工代碼 / 姓名 / 部門查出一批員工,勾選後一次把他們的 `AGENT_ID` 與 `AGENT_CODE` 改成畫面上指定的值。

**取數**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:147-171`):

```
SELECT COD009.*, OFD002.DEPT_SH_NM, OFD068A.AGENT_SHNM
  FROM COD009
  LEFT JOIN OFD002   ON ...DEPT_NO
  LEFT JOIN OFD068A  ON ...AGENT_ID AND ...AGENT_CODE
 WHERE 1 = 1
```

三個查詢條件(員工代碼、姓名、部門)走 `EVAStringHelper.AddParam`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:158-159`),這支 helper 對 `Like` / `Equal` 有做單引號跳脫但對 `IN` 沒有(`architecture.md §4.7`)。

**寫入**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:89-109`):先用 LINQ 把勾選列的 `EMP_NO` 收成陣列,再組成

```
UPDATE COD009 SET AGENT_ID = :AGENT_ID, AGENT_CODE = :AGENT_CODE
 WHERE EMP_NO IN ('A','B','C')
```

**`AGENT_ID` / `AGENT_CODE` 是繫結參數,`EMP_NO` 的 `IN` 清單是 `string.Format` 串接**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:99-100`)。員工代碼來自資料庫而非直接輸入,但路徑上沒有跳脫;而且**陣列為空時會組出 `IN ('')`**,那會更新 `EMP_NO` 為空字串的列(如果有的話)。

**四眼欄位一個都不動**:雖然 PO 繼承 `BaseEVADaoPO` 且宣告了 `MasterTable`(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43`),但覆寫的是 `Execute` 而不是 `Update`。所以這批資料的 `UPDATEID` / `UPDATEDATE` / `STATUS` 全部維持原值 —— **從 `CODM009` 看不出來誰改的**。

**UI 端的三個行為**:`ucomAGENT_ID` 被強制設成 `"0"` 且永遠 `Enabled = false`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:55-57`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:91`),所以只能掛到區分碼 `0` 的機構〔客戶特定〕;「銷售機構代碼」留空時兩個參數都傳空字串,等於**批次清除**且畫面上沒有提示(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:153-157`);「全選」鈕只勾選**沒有被 grid 篩選掉**的列(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:201-209`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 至少勾選一筆 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:257-267` |
| 執行前 | 銷售機構代碼留空 | 兩個參數傳空字串 → 批次清除 | 記錄不擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:153-157` |
| 執行 | 影響筆數為 0 | 回報失敗但**交易照樣 `Commit`** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:112-121` |
| 執行 | 例外 | `Rollback` + 「執行失敗,請檢查」 | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:123-129` |
| 全程 | 不寫四眼欄位 | 異動無痕跡 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:93-109` |

### 6.4 `CODB901` — 員工旗標維護

**做什麼**:針對單一員工,改 `OUTBOUND`(理財中心是否為 OutBound 同仁)與 `UID_CODE`(系統使用者代號)。

**沒有查詢**:畫面上把查詢鈕關掉(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:48`),員工靠 `ucEmployeeData` Searcher 挑,挑完自動把該員工現在的 `OUTBOUND` 與 `UID_CODE` 帶進畫面(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:107-111`)。Searcher 的過濾條件是 `LEAVE_DATE = DateTime.Today`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:50`) —— 這個屬性名與值的關係要看 `ucEmployeeData`,本文不猜。

**寫入**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:66-86`):

```
UPDATE COD009 SET OutBound = :OutBound, UID_CODE = :UID_CODE,
                  UPDATEID = :UpdID, UPDATEDATE = sysdate
 WHERE EMP_NO = :EMP_NO
```

全部繫結參數,這是四支 B 裡 SQL 最乾淨的一支。**而且是唯一會寫 `UPDATEID` / `UPDATEDATE` 的一支**(但不寫 `STATUS`,所以仍然繞過四眼)。

**`OUTBOUND` 的值是 `"Y"` 或空字串**,不是 `"Y"` / `"N"`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:71`)。而讀回來時是 `Convert.ToBoolean(...)`(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:109`) —— 對字串 `"Y"` 做 `Convert.ToBoolean` 會丟 `FormatException`。**假設**:`ucEmployeeData` 回來的那個欄位已經被 `CASE ... THEN 1 ELSE 0 END` 轉成數字(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:361`),所以實際不會炸。依據是共用 PO 確實有這段轉換,但兩邊沒有任何契約保證。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB901.cs:93-104` |
| 執行前 | 沒有任何業務檢核(例如新的使用者代號是否已被別人用) | —— | —— | —— |
| 執行 | 影響筆數為 0 | 回報失敗但**交易已 `Commit`** | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:88-98` |
| 執行 | 例外 | 回傳 `ex.ToString()` 給畫面 | 阻擋(訊息是堆疊) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:101-106` |

**與 `CODM009` 的關係**:`UID_CODE` 在 `CODM009` 有一條查重檢核(§4.4),**這支完全沒有**。同一個欄位兩個入口、一個有卡控一個沒有。

### 6.5 `CODB902` — 使用者帳號解鎖 / 補發密碼

**做什麼**:兩個功能由一組單選鈕決定(`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:70`,用 `CheckedIndex` 當參數值,選項順序一改語意就反):

| `EXEC` | 功能 | 對 `AA_USER` 做什麼 | 錨點 |
|---|---|---|---|
| `"0"` | 解鎖 | `LASTLOGINTYPE = 0`、`HOSTNAME = ' '`、`BANMARK = 1` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:74-89` |
| 其他 | 補發密碼 | 先取該帳號的 EMAIL;產生 `Guid.NewGuid().ToString("N")` 當新密碼、加密後寫入,並設 `ISFORCECHANGEPWD = 1`;然後把**明文密碼**寄到那個 EMAIL | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:93-135` |

**三件要注意的事**:(1) **明文密碼會出現在兩個地方** —— 寄出的信件內文(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:126`),以及寄信失敗時**直接顯示在操作者畫面上**的「密碼發送失敗,密碼為:xxx」(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:134`);(2) **執行歷程寫進一張叫 `CODB902` 的表**,`INSERT` **沒有欄位清單**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:137-149`),欄位順序一改值就全部錯位,而且這張表不在掃描器母體裡;(3) **EMAIL 沒設定時的提前 `return` 沒有處理交易**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101`),`tran` 已開啟卻沒有 `Commit` 也沒有 `Rollback`,只靠 `finally` 的 `Dispose`。

**寄信走 `ServerMailUtility`**(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:123`),產品名從 `StarterProxy().GetProductName()` 取(`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:124`),兩者都無原始碼,從呼叫端反推。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | 訊息清單 | 阻擋 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:89-100` |
| 執行前 | 沒有「這個帳號真的鎖住了嗎」之類的業務檢核 | —— | —— | —— |
| 執行(補發) | 該帳號沒設 EMAIL | 訊息「必須先到UC0101設定使用者的〔電子郵件信箱〕」+ return | 阻擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101` |
| 執行(補發) | 寄信失敗 | 回報**成功**,訊息附明文密碼 | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:131-135` |
| 執行 | 每次執行都寫一列歷程 | —— | 記錄不擋 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:137-149` |
| 執行 | 例外 | 回傳 `ex.ToString()` 給畫面 | 阻擋(訊息是堆疊) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:153-158` |

### 6.6 `CODB009` 與 `CODM009` 的分工

兩支畫面的主檔都是 `COD009`,掃描器也是這樣回報的(`主檔於:CODB009, CODM009, RSPM037`)。差別:

| 面向 | `CODM009` | `CODB009` |
|---|---|---|
| 一次處理幾筆 | 一筆 | 多筆(勾選) |
| 改哪些欄位 | 除了 `OUTBOUND` 與 `UPD_*` 之外幾乎全部 | **只有 `AGENT_ID` 與 `AGENT_CODE`** |
| 走不走四眼 | 走(有 `STATUS`、待辦、覆核) | **不走**,直接 `UPDATE` |
| 四眼欄位 | 由引擎寫 | **完全不動** |
| 檢核 | 十幾條(§4.4) | 只有「至少勾一筆」 |
| 查詢條件與顯示欄位 | 員工代碼 / 姓名 / 身分證;`App.config` 指定 7 欄 | 員工代碼 / 姓名 / **部門**;程式指定 9 欄,含機構三欄 |
| xsd | `CODM009Model.xsd`(55 欄,四眼欄位無中文名) | `CODB009Model.xsd`(**四眼欄位全部有中文名**,多一個 `ISCHECK` 與 `AGENT_SHNM`) |

**兩份 xsd 描述同一張表,欄位集合不一樣。**`CODB009Model.xsd` 少了 `BEF_EMP_CD` / `ADD195` / `IS_UPDATE_OFD195` 這類只有維護畫面用得到的暫存欄,多了 `ISCHECK`(勾選)與 `AGENT_SHNM`(join 來的機構名)。**改 `COD009` 的實體欄位時,三份 xsd 都要重生**:`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd`、以及 RSP 模組的 `Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd`。

實務上的後果:**`CODB009` 改過的資料,在 `CODM009` 的待辦清單裡不會出現,在四眼紀錄上也看不到**。要追「誰把這批人掛到這個機構」,只能靠資料庫稽核或作業紀錄。

## 7. 報表(R)

**本模組無 R 畫面、無 `.rpt` 檔、無報表專案。**

`Dev/ATLAS.COD/Source/Vendor.ATLAS.COD.sln` 底下只有 `Control` / `Entity` / `FormProxy` / `PO` / `UI` 五個資料夾,沒有 `.Report` 對應專案(對照 CAS 有 `Dev/ATLAS.CAS.Report/`)。

原因(推測)有三條:(1) **代碼檔本身沒有報表需求** —— 三張代碼表的內容就是參數設定,要看直接開維護畫面查詢頁;(2) **員工名冊的報表不在 COD** —— `COD009` 被 12 個專案讀,需要員工清單的報表掛在各自模組下(例如 CAS 的 `CASR001` 用員工代碼當參數);(3) **憑證流水號的報表在 OFD** —— `COD017` 被 `Dev/ATLAS.OFD/` 底下兩個檔引用,列印與統計屬於 OFD(`OFD721` 才是憑證主檔)。

這三條都標**推測**:依據是 repo 內沒有任何 `CODR*` 代號、`rpt` 檔零支、`architecture.md §9.3` 的模組型別分佈也顯示 COD 只有 B 與 M。因此本節沒有「rpt 一覽表」可列。

## 8. 跨模組共用

```text
[圖] COD 六張表分別被哪些模組讀取，以及改動前必須一起看的地方
圖中文字:① COD009 員工主檔：121 個檔引用，遍及 12 個專案 / COD009 / 36 欄 無四眼欄位 / BasicCOD_PO / 共用員工查詢 三種部門版本 / RSPM037 / RSP 也拿它當主檔 / OFD RSP DSM CPM CAS / 只 JOIN 取姓名與部門 / ② COD006A 一般代碼：62 個檔，靠 CODE_SORT 字面值取用 / COD006A / PK CODE_SORT+CODE / ucCOD006 Searcher / 共用控件 走 CodeDataSrc / 約 40 個 CODE_SORT 值 / 散在 190 處字面值 / 作廢原因走 17 / 寫死在共用 PO 裡 / ③ CTL014 下拉選單：唯一有 250 個專屬類別的代碼表 / CTL014 / SourceType 分類 / BasicCMM_PO / 唯一讀取入口 / 250 個 DataSrc 類別 / 各綁死一個 SourceType / GetDropDownDataSrc / 呼叫時才給 SourceType / ④ 其餘四張表：本模組以外多半只讀不寫 / COD005A / CODM005 與共用 PO / COD007A / CODM007 與共用 PO / COD010 / CODM010 加 RSP OFD EC / COD016 COD017 / CODM016 017 加 OFD / ⑤ 改這幾張表之前一定要看的地方 / 改 COD009 欄位 / 三份 xsd 要一起重生 / 改 COD006A 代碼值 / 先查 190 處字面值 / 改 CTL014 某一類 / CTLB014 會整類刪光重寫
```

*圖:圖 5 誰在讀這些代碼表。橘框＝本模組的表；黑框＝共用讀取端（原始碼不在本模組）；灰虛框＝其他模組的入口；橘虛框＝改動前必須確認的事。*

見本節首的圖。掃描器對 COD 回報「無跨模組共用表」,那是因為它只比對 `MasterTable` / `DetailTable` 的宣告 —— **讀取方不會出現在主明細統計裡**。實際反查(對全 `Dev` 下的 `.cs` 做表名字面比對,排除 `*.Designer.cs`)結果如下。

### 8.1 六張表被誰讀

| 表 | 引用檔數 | 本模組外的分佈 |
|---|---|---|
| `COD009` | **121** | Common 19、OFD 16、RSP 11、DSM 10、CPM 9、CAS 8、OFDB 6、CRM 6、EC.Query 5、OFD.Query 4、TMK 3、其餘零星;本模組 8 |
| `COD006A` | **62** | OFD 9、CPM 8、RSP 7、OFDB 4、CAS 4、TMK 3、OTA.Query 3、OTA 3、Common 3、OTAB 2、EC 2;本模組 3 |
| `COD017` / `COD010` | 10 / 8 | `COD017`:Common 4、OFD 2、本模組 4;`COD010`:RSP / OFD / EC.Query / Common 各 1、本模組 4 |
| `COD005A` / `COD007A` | 各 4 | 各自 Common 1、本模組 3 |
| `COD016` / `COD040A` | 3 / 1 | 全在本模組 |

### 8.2 `COD009`:三個維護入口、一個共用查詢 PO

**三個維護入口**(全部把它當 `MasterTable`):

| 畫面 | 模組 | 動作 | 走四眼? | 錨點 |
|---|---|---|---|---|
| `CODM009` | COD | 單筆全欄位維護 | ✔ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:39` |
| `CODB009` | COD | 批次改銷售機構兩欄 | ✘ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:43` |
| `RSPM037` | **RSP** | 查離職員工與其員眷 | 只查不寫 | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79` |

`RSPM037` 的宣告寫在 `Select()` 方法內而不是建構子(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM037_PO.cs:75-79`),所以它的 `MasterTable` 是**呼叫時才成立的**。加上 `CODB901` 也會 `UPDATE COD009`(§6.4),實際上有**四個地方**會碰這張表。

**共用查詢 PO 才是最大的讀取端**:`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 的 `GetEmployeeDataSrc` 一支方法裡有**三條主要分支加六個附加條件**,每一條的可見範圍都不一樣:

| 分支 / 條件 | SQL 主體 | 誰觸發 | 錨點 |
|---|---|---|---|
| 直銷部門版 | `COD009` `JOIN` `V_SAL051`(取最新一筆),部門取 `SAL_DEPT_NO` | 傳 `IS_SALE=Y` / `IS_DIRECT_EMPS` / `SEARCHER` / `SAL_DEPT_NO` 任一 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:279-293` |
| CPM 版 | 主檔換成 `V_TA_CPM_USER`,`COD009` 反而變成 `LEFT JOIN` | 傳 `IS_CPM=Y` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:335-346` |
| 一般部門版(預設) | `COD009` `LEFT JOIN` `OFD002` | 其餘 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:359-370` |
| `IS_Mass=Y` | 加 `DEPT_NO IN('G2','G11','G15','GC')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:378` |
| `IS_CASI001=Y` | 把 `FROM COD009` 字串替換成含 `CLS001A` 的 join,且 `USAGE = '3'` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:384` |
| `IS_CASB001=Y` | 加 `DEPT_NO IN('G3','GA','G17','G12','G13')` **且** `EMP_NO NOT IN ('100676','009037','850094','990651')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:392-393` |
| `IS_MARKETING=Y` | 加 `DEPT_NO IN('G3','GA','G17','G12','G13','G14','Z2')` | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:401` |
| `IS_SOLVE_DEPT_NO=Y` | 加 `DEPT_NO IN('OP1','M1','M2','E1')`(兩個分支各寫一次) | 〔客戶特定〕 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:352`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:408` |

**這一支是「同一張員工表在不同畫面看到不同人」的總開關,而它不在 COD 底下。**改 `COD009` 的部門欄位語意、或調整部門代碼,這八處寫死清單全部要重新確認。

`IS_CASB001` 那條的員工代號黑名單(`100676` / `009037` / `850094` / `990651`)是**寫死的四個人**,而 CAS 那邊還有另一份白名單(`architecture.md` 與 CAS 篇都記過)。兩份名單獨立維護。

還有第三種「在職」定義藏在 `GetUidCode`:`AND (TRIM(COD009.LEAVE_DATE) IS NULL OR COD009.LEAVE_DATE >= TO_CHAR(sysdate, 'YYYYMMDD'))`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695`)。連同 §4.4 的兩種,同一個概念在三個地方三種寫法(附錄 E.3)。

### 8.3 `CTL014` 與 `CTLB014`:代號屬 CTL、檔案在 COD

`CTLB014` 六層齊全地放在 `Dev/ATLAS.COD/` 底下:

| 層 | 檔 |
|---|---|
| UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs` |
| FormProxy | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CTLB014_Pxy.cs` |
| Control | `Dev/ATLAS.COD/Source/Control/Control.COD/CTLB014_Ctl.cs` |
| PO | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs` |
| DataEntity | `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CTLB014Model.xsd` |
| UIEntity | `Dev/ATLAS.COD/Source/Entity/UIEntity.COD/CTLB014View.xsd` |

掃描器依代號前三碼把它歸給 CTL 模組,所以它**不在 COD 的母體 12 支裡**;但它是全系統下拉選單來源表 `CTL014` 的唯一維護入口,實務上要跟 COD 一起看。

**這支的行為是本篇最需要提醒的一件事**:

```
DELETE ctl014 WHERE sourcetype = :sourcetype        -- 先把整個代碼類別刪光
INSERT INTO CTL014 VALUES (...)                     -- 再把 grid 上的列一筆一筆寫回
```

`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:28-80`。四個後果:(1) **沒有四眼** —— `CTL014` 沒有 `STATUS` 也沒有 `DATAID`,這支直接 `Execute`,一個人就能改掉全系統某一類下拉選項;(2) **沒有樂觀鎖** —— 沒有 `DATAFLAG`,兩人同時開,後存的把先存的整批刪掉再寫自己的;(3) **`INSERT` 沒有欄位清單**(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`),欄位順序一改七個值全部錯位;(4) **`Description` 整類共用一個值**,從 `Utility.Parameters` 來、每列都寫同一個(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:55`),讀回來時取第一列的當結果訊息(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:95`)。

另外兩個小地方:`SOURCETYPE` 取值用 `vdb.Utility.Parameters[0].Value` —— **靠位置取參數**(`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:38`、`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:89`);UI 端塞參數的順序是 `SOURCETYPE` / `DESCRIPTION` / `USERID`(`Dev/ATLAS.COD/Source/UI/UI.COD/CTLB014.cs:77-81`),順序一調就全錯。而 `SourceType` 這個「代碼類別編號」本身**沒有任何維護畫面**,要新增一個類別只能直接下 SQL。

**讀取端**:全系統經 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCMM_PO.cs:142-197` 一支方法,由 250 個 `xxxDataSrc` 類別各綁死一個 `SourceType`(`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/`),外加 `GetDropDownDataSrc` 讓呼叫端自己傳(`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/GetDropDownDataSrc.cs:35-38`)。`GetDropDownDataSrc("062")` 一種寫法就出現 100 次。

### 8.4 `COD006A`:靠 `CODE_SORT` 字面值切成約 40 個互不相見的世界

讀取端統一走共用控件 `ucCOD006`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:21`),它提供四個屬性:`CODE_SORT`(單一種類)、`CODE_SORT_IN`(多種類)、`CODE_LIKE`、`Dis`(排除某個代碼)、`LENGTH`(限定代碼長度)。這些條件轉成參數送到 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257`。

**兩個要注意的地方**:

- `ucCOD006` 送出的參數名是 `"Dis"`(`Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:108-110`),而 PO 端找的是 `"DIS"`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:188-189`)。`FindByName` 的實作在框架 DLL 內(無原始碼,從呼叫端反推),**若它大小寫敏感,`Dis` 這個排除條件會被靜默丟棄**。`CODM017` 正好用了這個屬性(`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37`)。這條標**假設**,依據是兩邊字面不同且沒有正規化。

- `CODE_SORT_IN` 分支用 `string.Format` 把逗號分隔字串串成 `IN ('a','b')`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:202-211`),其餘條件都是繫結參數。同一支方法內兩種安全等級。

`Filter` 屬性(`CODM017` 用來排除 `01`–`05`)**不在 `ucCOD006` 的原始碼裡**,是基底 `xSimpleSearcher` 的(無原始碼,從呼叫端反推)。也就是那段 SQL 片段會被送到哪一層、有沒有跳脫,repo 內看不到。

### 8.5 COD 借用的表

| 表 | 用途 | 誰用 | 錨點 |
|---|---|---|---|
| `OFD002` / `OFD068A` / `OFD081` | 部門中文簡稱 / 銷售機構簡稱 / 基金簡稱 | `CODM009` `CODM010` `CODB009` / `CODB009` / `CODM016` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:469-470`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:154-155`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:410-411` |
| `OFD115A` | 判斷代碼是否已作為列管原因 | `CODM006` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:341-343` |
| `OFD195A` | 判斷員工 / 親屬是否已是優惠關係人 | `CODM009` / `CODM010` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:722-725`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:692-697` |
| `OFD721` | 憑證狀態,判斷能否作廢 | `CODM017` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:216-218` |
| `AA_USER` / `TODO` | 平台使用者帳號 / 平台待辦事項 | `CODB902` / `CODB000` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:74-80`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:43` |

**全部唯讀,除了 `AA_USER` 與 `TODO`。**COD 會寫平台庫的這兩張表,是本模組唯一跨越業務庫 / 平台庫邊界的地方(`architecture.md §3.7` 說明兩個庫的分工)。

### 8.6 改動影響面速查

| 想改什麼 | 一定要一起看 |
|---|---|
| `COD009` 加 / 改欄位 | 三份 xsd(`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODM009Model.xsd`、`Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB009Model.xsd`、`Dev/ATLAS.RSP/Source/Entity/DataEntity.RSP/RSPM037Model.xsd`)+ `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:426-487` 的欄位清單 + `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:265-536` 的三條 SQL + `DB/Table/updateCOD009.sql` 那兩張 eHR 介接表 |
| `COD009` 的部門代碼語意 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs` 內四組寫死的部門清單 |
| `COD006A` 某個代碼種類的值 | 先 grep 該 `CODE_SORT` 的字面值(附錄 C.2 有清單),190 處裡可能有人硬比對 |
| `COD006A` 加欄位 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:37-96` 與 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:166-257` 兩支共用查詢的欄位清單、`Dev/Common/Source/DataSource/DataEntity.DataSource/` 底下的 `COD_*` typed DataSet |
| `CTL014` 某一類的選項 | 用 `CTLB014` 改會**整類刪光重寫**;同時確認 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs` 有沒有對應類別,有的話那份常數不會跟著變 |
| `CTL014` 加欄位 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49` 的 `INSERT` **沒有欄位清單**,加欄位一定要同步改這裡 |
| `COD016` / `COD017` | `s_CODM016` 這支 SP 不在版控,改欄位要連 DB 一起改;而且這兩張表的四眼欄位是混合大小寫 |
| `COD005A` 的種類 | 兩支下拉 SQL(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:611-619`)的互斥規則 |

## 附錄 A. 資料表總表

| 表 | 欄位數(xsd) | 四眼 13 欄 | 主檔於 | 被誰讀(檔數) | 說明 |
|---|---|---|---|---|---|
| `COD005A` | 17 | ✔(無中文名) | `CODM005` | 4 | 代碼種類主檔 |
| `COD006A` | 23 | ✔(無中文名) | `CODM006` | 62 | 一般代碼明細〔共用〕 |
| `COD007A` | 22 | ✔(無中文名) | `CODM007` | 4 | 級距代碼 |
| `COD009` | 55(`CODM009` 版)/ 47(`CODB009` 版) | ✔(`CODB009` 版有全套中文名) | `CODM009` `CODB009` `RSPM037` | 121 | 員工主檔〔共用〕 |
| `COD010` | 35 | ✔(無中文名) | `CODM010` | 8 | 員工親屬 |
| `COD016` / `COD017` | 19 / 21 | ✔(**小寫混合**) | `CODM016` / 無四眼入口 | 3 / 10 | 憑證流水號區間與逐筆狀態;`COD017` 由 SP 產生 |
| `COD040A` | 18 | ✔ | `CODM036`(掃描器漏) | 1 | 級距設定,業務不明 |
| `CTL014` | **4** | **✘** | `CTLB014`(代號屬 CTL) | 下拉選單的唯一來源 | 無 PK、無四眼、無樂觀鎖 |
| `CODB902` | (無 xsd) | ✘ | —— | 1 | 解鎖 / 補發密碼的執行歷程;`INSERT` 無欄位清單 |
| `COD009_ehr` / `COD009_eHRLOG` | (無 xsd) | ✘ | —— | **0** | 只出現在 `DB/Table/updateCOD009.sql:2-10`;匯入程式不在本 repo |

**非實體結果集**:`UC0301`(`CODB000` 的待辦清單,由 `s_GetToDoData` 回傳,定義在 `Dev/ATLAS.COD/Source/Entity/DataEntity.COD/CODB000Model.cs`)。**外部唯讀表**:`OFD002`、`OFD068A`、`OFD081`、`OFD115A`、`OFD195A`、`OFD721`、`CLS001A`(經共用 PO)、`SAL051`(經 `V_SAL051`)、`AA_USER`、`TODO`。

## 附錄 B. SP / Function / Trigger / View

掃描器對 COD 回報 SP 0 / Fn 0 / Trigger 0 / View 0 —— **因為 `DB/` 底下沒有任何 COD 的物件檔**。但程式確實呼叫了兩支 SP 與兩個 View:

| 類 | 名稱 | 誰呼叫 | 在 `DB/` 裡? | 錨點 |
|---|---|---|---|---|
| SP | `s_CODM016` | `CODM016` 的 `AfterAdd` / `AfterUpdate` | **否** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:119`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:286` |
| SP | `s_GetToDoData` | `CODB000` 的 `Select` | **否** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB000_PO.cs:79` |
| View | `V_SAL051` / `V_TA_CPM_USER` | 共用 `GetEmployeeDataSrc` 的直銷部門版 / CPM 版 | **否** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:291`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:343` |
| Function | `F_TA_GET_DIRECT_EMPS` / `sw.f_ta_chk_cls_auth` | 共用 `GetEmployeeDataSrc` 的 `IS_DIRECT_EMPS` / `SEARCHER` 條件 | **否** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:308`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:327` |

`architecture.md 附錄 B.0` 說 `DB/` 只涵蓋 16% 的 SP;COD 這邊是 0%。`DB/` 底下唯一與 COD 有關的檔是 `DB/Table/updateCOD009.sql`(加三個欄位到 `COD009`、兩個到 `COD009_ehr` 與 `COD009_eHRLOG`),schema 前綴是 `sw.`。

## 附錄 C. 代碼對照

本篇的代碼值來源有五種,每一條都標明是**表**還是**程式常數**:

### C.1 `CTL014` 的 `SourceType`(表 + 程式常數,覆蓋率 47%)

`CTL014.cs` 有 187 個靜態類別 / 566 個值,其中 186 個類別的註解帶著 `SourceType` 編號。以下只列與 COD 直接相關的,完整清單請直接讀 `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs`。

| SourceType | 類別 | 中文 | 值域 | COD 哪裡用 | 錨點 |
|---|---|---|---|---|---|
| `000` | `YES_NO` | 是 / 否 | `Y` `N` | `CODM006` / `CODM007` 的 `MOD_FLAG` grid 下拉 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:11-21`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/YesNoDataSrc.cs:18` |
| `001` | `MGR_CODE` | 基金經理人類別 | `0` 其他 / `1` 基金經理人 / `2` 研究員 | `CODM009` 的 `MANGR_CODE`、`DAM_CODE` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:27-43` |
| `002` | `EMP_CODE` | 員工類別 | `0` 其他 / `1` 正式員工 / `2` 工讀生 / `3` 臨時工 …… | `CODM009` 的 `EMP_CD`;新增預設 `"1"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:45-65`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/EmpCdDataSrc.cs:18` |
| `003` | `SALES_CODE` | 業務員區分碼 | 見類別 | `CODM009` 的 `AO_CODE`;新增預設 `"N"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:67-79`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/AoCodeDataSrc.cs:19` |
| `004` | `VALID_CODE` | 部門 / 通路 / 銷售機構有效碼 | 見類別 | `CODM006` 的 `VALID_CODE`;新增預設 `"Y"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:81-93`、`Dev/Common/Source/DataSource/UI.DataSource/DropDownSrc/ValidCodeChDataSrc.cs:17` |
| `062` | `TRUST_AGENT_ID` | 銷售機構區別碼 | 見類別 | `CODM009` / `CODB009` 的 `AGENT_ID`;`CODB009` 強制鎖成 `"0"` | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:1050`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:56` |
| `701` | **無對應類別** | 通路職務別 | `1` 部門主管 / `2` 組主管或業務員 / `3` 業務助理(**只寫在 DB 註解**) | `CODM009` 的 `G_JOB_CODE` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:587`、`DB/Table/updateCOD009.sql:15` |
| `702` | **無對應類別** | 職位代號 | **repo 內查不到** | `CODM009` 的 `JOB_CODE`(走無原始碼的 `ucCTL014`) | `DB/Table/updateCOD009.sql:17` |
| —— | `CTL_SRNO_ID` | 紙張流水號識別碼 | `0` 未使用 / `1` 已使用 / `2` 作廢 | `COD016` / `COD017`;**程式全部寫死字面值,常數零引用** | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` |

**全庫統計**(掃 `Dev` 下所有 `.cs`,排除 `obj` / `bin`):

| 量 | 數字 |
|---|---|
| `CTL014.cs` 帶編號的類別 | 186 |
| 程式實際用到的 `SourceType`(`GetDropDownDataSrc("nnn")` + 250 個專屬 DataSrc 的 `m_sourcetype`) | 395 |
| 用到但 `CTL014.cs` 沒有對應類別 | **224** |
| 有類別但沒有任何地方直接用 | 15(`022` `032` `033` `034` `086` `112` `120` `121` `122` `123` `132` `135` `136` `147` `247`) |
| 最常被直接呼叫的 SourceType | `062`(100 次)、`107`(36)、`408`(24)、`404`(20)、`000`(20)、`220`(19) |

### C.2 `COD006A` 的 `CODE_SORT`(只有表,程式常數零引用)

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` 的 `CODE_SORT` 類別:

| 值 | 常數名 | 中文 | 值 | 常數名 | 中文 |
|---|---|---|---|---|---|
| `01` | `Language` | 語言代碼 | `31` | `ServiceKind` | 服務類別代碼 |
| `02` | `EducationLevel` | 教育程度代碼 | `32` | `InvestAffinity` | 投資傾向代碼 |
| `03` | `CareerKind` | 職業別代碼 | `33` | `ExpectInvestTime` | 預期投資時間代碼 |
| `04` | `CareerTitle` | 職稱代碼 | `39` | `FundAllotLackDoc` | 基金申購缺件文件代碼 |
| `11` | `CtAskData` | 客戶索取資料代碼 | `40` | `FundRedeemLackDoc` | 基金買回缺件文件代碼 |
| `12` | `CtComplainKind` | 客訴內容種類代碼 | `41` | `RSPLackDoc` | 定時定額缺件文件代碼 |
| `13` | `CtComplainProcess` | 客訴處理代碼 | `60` | `AllotDateRecoveryReason` | 申購日結回復說明代碼 |
| `15` | `CtRiskAnalyze` | 客戶風險分析代碼 | `61` | `RedeemDateRecoveryReason` | 贖回日結回復說明代碼 |
| `19` | `CtInvestExpect` | 客戶投資意願代碼 | `84` | `CallCode` | 來電代碼 |
| `20` | `CtLevel` | 客戶等級代碼 | `89` | `NewBFLackDoc` | 開戶缺件文件代碼 |
| `23` | `TurnBackKind` | 退件類別代碼 | `90` | `AllotProblemReason` | 申購問題件原因代碼 |
| `27` | `PotentialCtDealingWithInvestmentTrust` | 潛在客戶往來投信公司 | `91` | `RedeemProblemReason` | 贖回問題件原因代碼 |
| `28` | `PotentialCtDealingWithFund` | 潛在客戶承購基金資料 | `99` | `ContactKind` | 聯絡人作業別 |
| `29` | `PotentialCtNeedService` | 潛在客戶所需服務項目 | `A1` | `InvestRegionLevel` | 投資級距代碼 |
| `30` | `PotentialCtDealingWithBond` | 潛在客戶承購債券資料 | `A2` | `IncomeRegionLevel` | 收入級距代碼 |
| —— | —— | —— | `A3` | `NowInvestRegionLevel` | 目前可投資級距 |

**這 31 個常數的全庫引用次數是 0。**實際在用的是字面值:

| `CODE_SORT` 字面值 | 出現處數 | 在上表? | 首見 |
|---|---|---|---|
| `42` | 19 | ✘ | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:1684` |
| `P3` | 18 | ✘ | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:108` |
| `17` | 16 | ✘(**作廢原因**) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| `13` | 15 | ✔ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:451` |
| `20` | 14 | ✔ | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:117` |
| `C7` | 9 | ✘ | `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM562_PO.cs:134` |
| `12` | 8 | ✔ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:535` |
| `A7` | 7 | ✘ | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM551_PO.cs:471` |
| `Q2` | 7 | ✘ | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:134` |
| `D2` | 6 | ✘ | `Dev/ATLAS.CLS/SOURCE/PO/PO.CLS/CLSM001_PO.cs:457` |
| `11` `A8` `E2` `E3` `50` `45` `E4` `PC` | 各 4–5 | 只有 `11` ✔ | —— |
| `1C` `C6` `P5` `P7` `1B` `23` `84` `E8` `PD` | 各 2–3 | `23` `84` ✔ | —— |
| `00` `15` `19` `36` `51` `89` `99` `C5` `E7` `E9` `HO` `P1` | 各 1 | `15` `19` `89` `99` ✔ | —— |
| `C1` | 2(**列管原因**;`!=` 比較,不在上面 `=` / `==` 的統計裡) | ✘ | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` |

**約 30 個實際在用的代碼種類,在 `CODCode.cs` 裡查不到中文說明。**要知道它們是什麼,只能連資料庫查 `COD005A` 的 `CODE_SORT_DESCRP`。

### C.3 `EMP_DEPT_TYPE`(程式常數,有在用)

`Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:141-167`,全庫 74 次引用 / 19 個檔。**COD 自己一次都沒用。**

| 值 | 常數名 | 中文 |
|---|---|---|
| `01` | `IsSellAgent` | 代銷 |
| `02` | `IsSales` | 直銷 |
| `03` | `IsKeyIN` | KEYIN 櫃檯 |
| `04` | `IsOther` | 其它(股務等) |
| `05` / `06` | `IsFin` / `IsProFin` | 理財 / 專戶理財 |

### C.4 本模組內寫死的代碼值〔客戶特定〕

| 值 | 意思 | 在哪 | 錨點 |
|---|---|---|---|
| `"C1"` | 列管原因的代碼種類 | `CODM006` 的 `BeforeUpdate` / `BeforeApproveDelete` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:372` |
| `'17'` | 作廢原因的代碼種類 | 共用 PO 的 `GetCancelCdDataSrc` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` |
| `'2'` / `'0'` | `CTL_SRNO_ID` 作廢 / 未使用 | `CODM017` 的兩段 UPDATE、`CODM016` 的兩支檢核、`CODM017` UI 的分支 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:79`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:109`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:672`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:107` |
| `'1'` | `CTL_SRNO_ID` 已使用 | `CODM016` 的 `ChkUsedData` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:590` |
| `"00"` 與 `'01'`–`'05'` | 不可挑選的作廢原因 | `CODM017` UI,一次寫在 `Filter` SQL 片段、一次寫在 C# 比較 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:37-38`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:179` |
| `"07"` | `FEE_CODE` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:232` |
| `"0"` | `EMP_QUOTA_CODE` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:237` |
| `"N"` / `"0"` / `"1"` | `AO_CODE` / `MANGR_CODE` / `EMP_CD` 的新增預設值 | `CODM009` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:89-92` |
| `"Y"` | `MOD_FLAG` 的新增固定值 | `CODM006` / `CODM007` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:161`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:174` |
| `"Y"` | `VALID_CODE` 的新增預設值 | `CODM006` | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:38` |
| `'19000101'` / `' '` | 「沒有離職日」的兩種哨兵值 | `CODM009` 的兩支查重 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395` |
| `"2"` | `OFD721` 的 `CER_STATUS`「可作廢」 | `CODM017` UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:82` |
| `0.01` / `999999999999` | `CODM036` 級距的上下界 | `CODM036` UI | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:172` |
| `ROWNUM < 3` | `CODM036` 查詢頁最多兩列 | `CODM036` PO | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` |

### C.5 四眼 `STATUS`

見 `architecture.md §3.10`。本模組沒有任何程式直接比對 `STATUS`,值域完全由框架決定。`CTL014`、`COD017`(由 SP 產生的部分)、以及四支 B 改過的資料**沒有有意義的 `STATUS`**。

## 附錄 D. 掃描母體與覆蓋率

`py -V:3.12 /docs/tools/atlas_scan.py --module COD --doc /docs/modules/cod.md` 的結果。

母體:畫面 12(B 4 / I 0 / M 8 / R 0)· 表 6 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 0 · Service 0。

**本文對母體的處置**:12 支畫面全部寫進 §3–§6(一支一節)、6 張表全部寫進 §2.3 與附錄 A;SP / Fn / Trigger / View / rpt / Service 各 0 的原因寫在 §7 與附錄 B,並補上程式有呼叫、`DB/` 卻沒有的 6 個 DB 物件。

**母體以外、本文額外納入的**:

| 項目 | 為什麼不在母體 | 本文寫在哪 |
|---|---|---|
| `COD040A` | `CODM036` 用 `MasterTable.Add(...)`,掃描器的正規式只認賦值寫法 | §2.1、§2.3 |
| `CTL014` / `CTLB014` | 代號前三碼是 CTL,掃描器歸給 CTL 模組 | §8.3 |
| `COD017` | 不是任何畫面的 `MasterTable`(只在 `CODM016` 的 xsd 內當第二張表) | §2.3、§4.6 |
| `CODB902`(當表用)/ `COD009_ehr` / `COD009_eHRLOG` | 前者不是任何畫面的 `MasterTable`,後兩者只在 DB 腳本裡、`.cs` 零引用 | §0.3、§6.5、附錄 A |
| `s_CODM016` / `s_GetToDoData` / `V_SAL051` / `V_TA_CPM_USER` / `F_TA_GET_DIRECT_EMPS` | `DB/` 底下沒有這些檔,掃描器只掃 `DB/` | 附錄 B |

上述項目中不在掃描索引裡的名字列在 meta 的 `refcheck-ignore`,因為它們**確實存在於系統中** —— 不是本文編造的。

## 附錄 E. 讀本文時要注意的地方

讀碼過程發現的缺陷與陷阱,依類型分。每一條都是**現況記錄,不是修改建議**。

### E.1 Oracle 三值邏輯與 `AND` / `OR` 條件

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E1.1 | `CheckRspChgDate` 的條件 `WHERE (RSP_CHG_DATE<>'19000101' or RSP_CHG_DATE<>'')` —— 兩個 `<>` 用 `OR` 串,**對任何非 NULL 的值都恆真** | 這條「是否已有契約異動資料」的檢核等於沒有條件,只要該員工在 `OFD195A` 有任何一列就會成立。目前呼叫端被註解掉所以沒發作,一旦解除註解就會**每次都跳警告** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:671` | **高** |
| E1.2 | `CHECK_ID_EXIST` 的在職條件 `AND (LEAVE_DATE = '19000101' or LEAVE_DATE = ' ')` —— **沒有處理 NULL**。而同一支 PO 的 `CHECK_UID_CODE` 用的是 `NVL(LEAVE_DATE, ' ') = ' '` | `LEAVE_DATE` 為 NULL 的在職員工不會被算進重複檢查,身分證字號可以重複輸入。`AfterUpdate` 那道補救 `UPDATE` 正好會把空字串改成 NULL(`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:72-79`),**等於系統自己製造出這個漏洞** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573` | **高** |
| E1.3 | `CheckOFD195` 在 `CODM010` 多了一行 `AND REL_NO NOT IN (SELECT EMP_NO FROM COD009 WHERE IS_COMP_FEAT = 'N' AND EMP_CD = '1')`,`CODM009` 的同名方法沒有 | 「非公單的正式員工」的親屬,刪除時**永遠不會跳**優惠關係人提示。兩支同名方法兩種語意,讀 `CODM009` 那支會誤判 `CODM010` 的行為 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:697` | 中 |
| E1.4 | `CheckRspChgDate` 在 `CODM010` 用 `NVL(RSP_CHG_DATE,' ') <>' '`,在 `CODM009` 用 E1.1 那個恆真式 | 同一個檢核兩份實作,一份正確一份壞掉 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:645` | 中 |

### E.2 `catch` 之後把例外訊息當資料值

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E2.1 | `CODM009_Pxy.CHECK_UID_CODE` 與 `CHECK_ID_EXIST` 的 `catch` **`return ex.Message;`**。呼叫端的判斷是「回傳字串非空 = 檢核不通過」 | 任何 Remoting 中斷或 DB 錯誤,都會變成一則**顯示在欄位旁邊的紅字驗證訊息**,內容是 .NET 例外文字;而且使用者被擋下來的理由與真因無關 | `Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:36`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM009_Pxy.cs:101` | **高** |
| E2.2 | `CODB901` / `CODB902` 的 `catch` **`AddResultRow(false, 0, ex.ToString())`** —— 連堆疊追蹤一起丟到畫面 | 使用者看到完整堆疊(含類別名、行號、伺服器路徑);同一個方案的其他 PO 用的是空字串或固定中文 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:104`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:156` | **高** |
| E2.3 | `CODM005_PO.CHECK_CODE_SORT` 的 `catch` 只呼叫 `HandleBusinessException`,`strResult` 維持空字串 | DB 查不到時檢核**視為通過**,該刪的擋不住 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:195-198` | 中 |
| E2.4 | `CODM006_PO` 的 `BeforeUpdate` / `BeforeApproveDelete` 的 `catch` 不設 `args.Cancel` | 查 `OFD115A` 失敗時,列管保護**自動放行** | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:362-365`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:388-391` | 中 |

### E.3 同一概念多套實作

| # | 概念 | 有幾套 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E3.1 | 「員工在職」 | **三套**:`NVL(LEAVE_DATE,' ')=' '`、`(LEAVE_DATE='19000101' or LEAVE_DATE=' ')`、`(TRIM(LEAVE_DATE) IS NULL OR LEAVE_DATE >= TO_CHAR(sysdate,'YYYYMMDD'))` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:395`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:573`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:695` | **高** |
| E3.2 | 「查詢條件轉 SQL」 | `CODM006` / `CODM009` / `CODM010` 各自有一份 private `AddParam`,三份**逐字相同**;另外還有共用的 `EVAStringHelper.AddParam` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:279-312`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:496-530`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:141-175` | 中 |
| E3.3 | 「取參數值」 | 三份 private `GetParamValue`(逐字相同,而且**全部沒有呼叫端**) | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:321-331`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:539-549`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:185-195` | 低 |
| E3.4 | 「檢核身分證格式」 | `CODM009` 用 `ValidateManager`,`CODM010` 用 `UIValidator`,兩個不同的類別 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:514`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:402` | 低 |

### E.4 被註解掉但外殼還在的檢核

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E4.1 | `CODM005` 刪除前的檢核:UI 端組好了 `view2` 與參數,**呼叫 Proxy 那一行被註解**,底下的 `if` 判斷一個永遠空的結果集 | 讀 UI 會以為卡控在用戶端;實際擋住的是伺服端覆寫的 `Delete`。兩邊訊息文字還不一樣 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM005.cs:123`、`Dev/ATLAS.COD/Source/FormProxy/FormProxy.COD/CODM005_Pxy.cs:134` | 中 |
| E4.2 | `CODM009` / `CODM010` 刪除前的「檢核是否已有契約異動資料」整段被註解,但 PO 端的 `CheckRspChgDate` 兩份實作都還活著、介面也還宣告著 | 兩支**沒有任何呼叫端的公開方法**留在 Remoting 契約上 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:407-421`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:436-451` | 中 |
| E4.3 | `CODM009_PO` 的 `AfterAdd` 與 `AfterDelete` **整段被 `/* */` 包起來**,但建構子仍然掛這兩個事件 | 「新增員工時自動建立優惠關係人」「刪除員工時設終止日」兩條規則**現在不存在**,而事件掛點看起來像有 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:251-274`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:276-341` | **高** |
| E4.4 | `CODM010_PO` 的四個 `After*` 全部只剩空方法 | 同上 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM010_PO.cs:299-624` | **高** |
| E4.5 | `CODM010` 的「未成年子女必填出生日期」有**三份被註解的實作**,寫法互不相同,兩份還引用已不存在的控件 | 這條業務規則被改過三次最後拿掉,但沒有人知道是刻意還是遺漏 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:85-106` | 中 |
| E4.6 | `CODM005_PO` 1,188 行裡只有約 40 行是活的;`CODM006_PO` 1,362 行約 400 行活;`CODM007_PO` 1,236 行約 290 行活;`CODM016_PO` 2,050 行約 900 行活 | 讀碼成本被放大 3–30 倍;`grep` 會撈到大量死碼 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM005_PO.cs:233-1064` | 中 |

### E.5 有訊息但沒有 `return` / 沒有 `Cancel`

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E5.1 | `CODM009` 與 `CODM010` 的 `OFD195A` 檢核:跳 `Warn01`「請記得至優惠關係人檔刪除該筆身份資料」後**沒有 `e.Cancel`** | 使用者按確定就繼續刪 / 改,優惠關係人資料留在 `OFD195A` 變孤兒 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:426-429`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:453-462` | 中 |
| E5.2 | `CODM007_BeforeAddButtonClicked` 在設完 `e.Cancel = true` 之後,**仍然繼續存取 `Rows[0]`** 並寫 `MOD_FLAG` | 若結果集為空會丟例外;而且被取消的動作還在改資料 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM007.cs:163-175` | 中 |
| E5.3 | `CODM006_BeforeAddButtonClicked` 同樣的結構 | 同上 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM006.cs:151-165` | 中 |
| E5.4 | `CODB000_BeforeExecuteButtonClicked` 寫了「至少勾選一筆」,但 `InitializeComponent` **沒有掛這個事件** | 檢核從來沒有執行過 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:254-257` | 中 |
| E5.5 | `CODB009` / `CODB901` 影響筆數為 0 時回報失敗,但 `Commit` **已經執行** | 「失敗」訊息與交易狀態不一致 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:112-121`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB901_PO.cs:88-98` | 低 |
| E5.6 | `CODB902` 寄信失敗時 `AddResultRow(true, ...)` —— 回報**成功** | 操作者以為信寄出去了 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:132-135` | 中 |
| E5.7 | `CODM036` 的 `ugrdCODM036_Error` 一律 `e.Cancel = true` | grid 的所有錯誤被靜默吞掉 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM036.cs:258-261` | 低 |

### E.6 代碼值寫死在 SQL 或程式裡(代碼模組的自我矛盾)

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E6.1 | `CODE_SORT` 的 31 個程式常數**全庫零引用**;實際用的是約 40 個字面值散在 190 處 | 改代碼種類的語意時沒有單一真相來源;`CODCode.cs` 的中文說明只覆蓋其中 10 個 | `Dev/Common/Source/MappingCode/TA.MappingCode/CODCode.cs:10-136` | **高** |
| E6.2 | `CTL_SRNO_ID` 的三個常數同樣零引用,而 `CODM016` / `CODM017` 在五個地方寫死 `'0'` `'1'` `'2'` | 同上;而且這三個值的語意只寫在沒人用的常數註解裡 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:993-1007` | 中 |
| E6.3 | `CODM006_PO` 用 `if (row.CODE_SORT != "C1") return;` 把「列管原因」這個代碼種類寫死在**代碼維護畫面**的 PO 裡 | 換站台或改編號就失效,而且失效時是「保護消失」不是「報錯」 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:340` | **高** |
| E6.4 | `CODM017` 的作廢原因排除清單 `01`–`05` 寫了兩次:一次是 UI 屬性裡的 SQL 片段 `"CODE NOT IN ('01','02','03','04','05')"`,一次是 C# 的五個 `==` 比較 | 兩處要同步改;而且那段 SQL 片段會被送進哪一層、有沒有跳脫,repo 內看不到(`xSimpleSearcher` 無原始碼) | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:38`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:179` | **高** |
| E6.5 | 共用 PO 的 `GetCancelCdDataSrc` 直接 `WHERE CODE_SORT= '17'` | 「作廢原因是 17 號代碼種類」這件事寫在共用層,COD 這邊完全看不到 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:555` | 中 |
| E6.6 | `TA.MappingCode` 的欄位是 `public static string` 不是 `const`(`architecture.md §7.2.1`) | 任何一行 `YES_NO.Yes = "1";` 就污染整個 AppDomain,編譯期不擋 | `Dev/Common/Source/MappingCode/TA.MappingCode/CTL014.cs:16` | 中 |
| E6.7 | `CODM009` 同一支檔案內,「正式員工」一處用常數 `EMP_CODE.Staff`、一處用字面值 `"1"` | 讀碼時會以為是兩件事 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:324` 對 `Dev/ATLAS.COD/Source/UI/UI.COD/CODM009.cs:357` | 低 |

### E.7 SQL 層面的髒寫法

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E7.1 | `CODB009` 的 `UPDATE ... WHERE EMP_NO IN (...)` 用 `string.Format` 串接員工代碼清單;陣列為空時組出 `IN ('')` | 沒有跳脫;空勾選時會更新 `EMP_NO` 為空字串的列 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB009_PO.cs:99-100` | **高** |
| E7.2 | `CODM006` / `CODM007` / `CODM009` / `CODM010` / `CODM016` / `CODM017` 的查詢條件全部用 `'" + value + "'` 串接 | SQL injection / 單引號炸語法。這是全庫的通用寫法(`architecture.md §4.7`),不是單一檔案的問題 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM006_PO.cs:308`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:188`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:232` | **高** |
| E7.3 | `CODM007` 的主檔 SQL 把 `MOD_FLAG` **`SELECT` 了兩次** | 填進 typed DataSet 時會多一個欄位或直接報錯,取決於框架的 `MissingSchemaAction` | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM007_PO.cs:170-171` | 中 |
| E7.4 | `CODM016.ChkExsitData` 的三個條件中,第二個條件比對的是 `BNG_CTL_SRNO`,綁的參數卻是 `@END_CTL_SRNO` | 複製貼上錯誤。這支方法目前**沒有呼叫端**,所以沒發作 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:774` | 中 |
| E7.5 | 同一支方法內 `@BNG_CTL_SRNO` 宣告成 `SqlDbType.Decimal`、`@END_CTL_SRNO` 宣告成 `SqlDbType.NVarChar`,而兩者在 xsd 都是 `decimal` | 型別不一致,一旦被呼叫會出現隱式轉換或錯誤 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:787-789` | 中 |
| E7.6 | `CTLB014` 與 `CODB902` 的 `INSERT` **都沒有欄位清單** | 表的欄位順序一改,值全部錯位,編譯不會有任何警告 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:40-49`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:138-141` | **高** |
| E7.7 | `CODM036` 的主檔查詢 `WHERE ROWNUM < 3` 沒有 `ORDER BY` | 取到哪兩列由 Oracle 決定 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM036_PO.cs:52` | 中 |
| E7.8 | `CODM016` / `CODM017` 用 SQL Server 方言(`[]`、`@`、`GetDate()`、`dbo.`),其餘全模組用 Oracle | 若 `architecture.md §4.6`「執行期 Oracle-only」成立,這兩支執行期就是壞的。**本文無法判定**,標假設 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:75-86`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM016_PO.cs:747-767` | **高** |

### E.8 位置取參數與其他讀碼陷阱

| # | 發現 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| E8.1 | `CTLB014_PO` 兩處用 `Parameters[0].Value` 取 `SOURCETYPE` | UI 端塞參數的順序一改就全錯,而且不會編譯失敗 | `Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:38`、`Dev/ATLAS.COD/Source/PO/PO.COD/CTLB014_PO.cs:89` | 中 |
| E8.2 | `CODM017` 與 `CODB902` 用 `uoptAction.CheckedIndex` / `uoptExec.CheckedIndex` 當參數值 | 用選項的**位置**當代碼值;Designer 裡調一下順序,作廢就變成取消作廢 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM017.cs:200`、`Dev/ATLAS.COD/Source/UI/UI.COD/CODB902.cs:70` | **高** |
| E8.3 | `CODM017_PO.Set` 的 `cmdModify` 只在 `act` 是 `"Y"` 或 `"N"` 時才被賦值,之後無條件 `AddInParameter` | 其他值直接 `NullReferenceException`;`catch` 裡的 `tran.Rollback()` 在 `tran` 為 null 時又蓋掉真因 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:132`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:180` | **高** |
| E8.4 | `CODM017_PO.Set` 綁了 `@CTL_SRNO_ID` 參數,但兩段 UPDATE 都把該欄寫死,SQL 裡沒有這個參數 | 多綁一個沒用的參數;SQL Server 會忽略,但讀碼者會以為值是動態的 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM017_PO.cs:136` | 低 |
| E8.5 | `CODB902` 在「EMAIL 未設定」時 `return model;`,此時交易已開啟但沒有 `Commit` 也沒有 `Rollback` | 只靠 `finally` 的 `Dispose` 收尾;行為取決於框架實作 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:97-101` | 中 |
| E8.6 | `CODB902` 產生的明文密碼會出現在寄出的信件內文,寄失敗時**直接顯示在操作者畫面上** | 明文密碼經過 EMAIL 與畫面兩條路徑 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:126`、`Dev/ATLAS.COD/Source/PO/PO.COD/CODB902_PO.cs:134` | **高** |
| E8.7 | `CODM016` 的「只能改最後一批」用的是進入修改模式時**快取的布林值**,不是存檔當下重查 | 畫面停留期間別人新增了一批,這裡不會知道 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:74-75` | 中 |
| E8.8 | `CODM016` 查詢條件的判斷式寫反:`if (custFUND_ID_0.Value == "")` 走 `LIKE`、`else` 走 `=` | 空白時組出 `LIKE ''`(只比對空字串),等於查不到任何資料 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM016.cs:82-89` | 中 |
| E8.9 | `CODM009` 的 `CHECK_ID_EXIST` 判斷 `Convert.ToInt32(i) == 1` 而不是 `> 0` | 已經有兩筆以上重複時反而放行 | `Dev/ATLAS.COD/Source/PO/PO.COD/CODM009_PO.cs:579` | 中 |
| E8.10 | `ucCOD006` 送出參數名 `"Dis"`,共用 PO 找 `"DIS"` | 若 `FindByName` 大小寫敏感,排除條件會被靜默丟棄(**假設**,`FindByName` 無原始碼) | `Dev/Common/Source/CustomControl/UI.CustomControl/ucCOD006.cs:109` 對 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:188` | 中 |
| E8.11 | 共用 PO 的 `GetCodeSortForCODM006` 用 `if (strID == "CODM006") ... else ...`,`else` 涵蓋「沒帶 `ProgramID`」與「帶錯值」 | 任何新的呼叫端忘記設 `ProgramID`,會**靜默拿到 `CODM007` 的清單** | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:634-637` | 中 |
| E8.12 | `CODB000` 的 UI / PO / Ctl 三個檔具備反編譯輸出的特徵(無 Designer 分離、`appearance2` 式命名、`new string[0]`、無中文註解) | **假設**:這一組原始碼曾遺失,現行版本由 DLL 反編譯還原。若成立,改這三個檔要特別小心行為差異 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB000.cs:143-281` | 中 |
| E8.13 | `CODB009` 的 `AGENT_ID` 下拉被強制鎖成 `"0"` 且永遠 disabled | 這支批次只能掛區分碼 `0` 的機構,畫面上看不出來〔客戶特定〕 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODB009.cs:55-57` | 中 |
| E8.14 | `CODM010` 的員工 Searcher 永遠帶 `IS_COMP_FEAT = "N"` | 公單員工挑不到,無提示 | `Dev/ATLAS.COD/Source/UI/UI.COD/CODM010.cs:431` | 低 |

### E.9 標「假設」的地方一覽

| # | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| A1 | 員工資料由外部 eHR 定期匯入,`CODM009` 是人工補正入口 | `DB/Table/updateCOD009.sql:2-10` 對 `COD009_ehr` / `COD009_eHRLOG` 做同樣加欄,但兩表在 `.cs` 零引用 | 問 DBA 或找 ETL 排程 |
| A2 | 代碼三張表是「建置期一次性」設定,不是日常大量作業 | 查詢條件極簡,無日期區間、無狀態篩選 | 問使用者 |
| A3 | `CODM016` / `CODM017` 的 SQL Server 方言在執行期會不會壞 | `architecture.md §4.6` 說執行期 Oracle-only,但這兩支確實在版控裡且有完整六層 | 實機測一次 |
| A4 | `COD007A` 的級距代碼由版控外的 SP 或報表使用 | 本模組外零引用,但表有完整維護畫面與四眼 | 查資料庫的相依 |
| A5 | `COD040A` 是什麼業務的級距 | **完全查不到**,本文不猜 | 問使用者或查資料庫內容 |
| A6 | `CODB000` / `CODB901` / `CODB902` 這幾支的原始碼曾遺失、由反編譯還原 | 三個檔的命名與結構特徵(E8.12) | 查版控歷史 |
| A7 / A8 | `ucEmployeeData` 回傳的 `OUTBOUND` 已被轉成數字(所以 `CODB901` 的 `Convert.ToBoolean` 不會炸);`FindByName` 大小寫敏感(所以 `Dis` 排除條件失效) | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:361` 有 `CASE ... THEN 1 ELSE 0 END`;`Dis` 兩邊字面不同且沒有正規化 | 實機測一次 |
| A9 / A10 | `CODM036` 的下限欄由 `LevelGridUtility` 自動接續上一列的上限;全模組的權限由 PTPF 平台功能權限決定 | 下限欄被設成 `NoEdit` 且控件建構子帶了上下界;程式內零權限判斷(`architecture.md §3.7`) | 實機測 / 查平台設定 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純讀碼彙整,涵蓋 12 支畫面 + `CTLB014`、6 張母體表 + `COD017` / `COD040A` / `CTL014`,重點在 §2.4 的代碼字典對應與附錄 C 的代碼值清單 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 78 · 圖 5 · 表格 73 · 程式錨點 722 · § 連結 36 · 引用檢查：畫面 15（缺 0） · Table 14（缺 0） · 結果集 4（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
