<!-- 由 tools/build_copilot_kb.py 從 modules/bbs.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

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
