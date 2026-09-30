<!-- 由 tools/build_copilot_kb.py 從 modules/nfdr2.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-21 -->

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
