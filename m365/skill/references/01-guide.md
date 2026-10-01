ATLAS 知識庫 — 01-導覽-索引速查症狀
入口、讀序、速查卡、症狀路由表、模組與手冊索引
本檔合併以下文件:index.md、CHEATSHEET.md、TROUBLESHOOT.md、modules/README.md、runbooks/README.md


============================================================
【文件】kb/index.md
============================================================

# ATLAS 知識庫(去識別化版)

> ⚠ **去識別化版本**(2026-09-21 14:33 產生)。客戶識別字樣已替換為中性名稱、程式錨點改為純文字;但**系統結構、畫面代號、表名、錯誤訊息、已知缺陷位置全部保留**——這些與命名無關,公開前請逐頁審閱。去識別化 ≠ 去風險。

> **一個人維護 ATLAS 的入口。**這一頁不講內容,只負責把你送到對的那一份。全部離線可讀,雙擊 `.html` 即開,不需要起 server、不需要網路。規模:畫面 911 · 實體表 437 · 報表範本 608 · 缺陷 1,682 條 · **兩條死碼線聯集 151 支畫面一按就 NRE**。

## 0. 先讀這份

| 第一份 | 為什麼 |
|---|---|
| **ATLAS 系統介紹(業務軸)** | 接手的人讀的第一份。六條業務線從開戶讀到報表,一日作業時序、角色與四眼、模組地圖都在裡面。**軸線是業務,不是程式。** |

**讀序**:`OVERVIEW` → `CHEATSHEET`(骨幹速查,可列印)→ `architecture`(技術通則)→ 自己負責模組的那一篇 → `runbooks`(要動手時)。

| 接著 | 一句話 |
|---|---|
| 速查卡 CHEATSHEET | 一頁 A4 雙面:代號規則、六層、主明細三處同名、四眼 13 欄、PO 基底黑白名單、部署矩陣、常用指令、已知坑前十型 |
| 症狀路由表 TROUBLESHOOT | 「遇到 X → 先看哪份的哪節」;最後一節列**文件裡還沒有答案**的症狀,省得你白找 |

## 1. 我要查(三個離線查詢頁)

| 頁 | 什麼時候開 |
|---|---|
| 畫面 / 表反查 query | 手上有一個代號或表名:六層檔案路徑、主明細、**PO 基底(死畫面標紅)**、誰在 SQL 裡讀寫這張表、對應的文件章節 |
| 錯誤訊息反查 messages | 線上噴了一句中文訊息:反查是哪支程式哪一行丟的。模組篇引用的訊息有意譯的,**要原文以這頁為準** |
| 缺陷總表 defects | 要動某個模組之前:先看它已知有什麼坑。可依模組 / 畫面 / 嚴重度 / 型別篩選排序 |

## 2. 我要改

### 2.1 我要做 X,看哪本

| 我要… | 看哪本 | 從哪節開始 |
|---|---|---|
| 欄位要多一個 | add-column | `§2–§9` |
| 欄位改型別或長度 | add-column | `§0 不適用,先問` |
| 報表要多印一欄 | add-report | `§2 第一列` |
| 報表版面要調 | add-report | `§5` |
| 要一支全新的畫面 | add-screen | `全篇` |
| 要一支新的查詢畫面 | add-query-screen | `§1 差異表` |
| 要一支新的批次 | add-batch | `全篇` |
| 覆核時要多一條檢核 | change-eva-flow | `§4.1` |
| 新增時要自動帶值 / 流水號 | change-eva-flow | `§4.2` |
| 要加稽核軌跡 | change-eva-flow | `§4.3` |
| 要改 SP / Function / Trigger | change-sp-fn-trigger | `全篇` |
| SP 在資料庫有、repo 沒有 | change-sp-fn-trigger | `§2` |
| 改完了要送測試 / 正式 | deploy | `§2 對照表` |
| WindowsService 要重裝或改帳號 | deploy | `§5` |
| 新人要把環境架起來 | build-env | `§0.1 三個前提` |
| 編不過 / 改了沒效果 | build-env | `§8 症狀表` |

### 2.2 九本手冊

| 手冊 | 一句話 | 行數 |
|---|---|---|
| add-column | 最常用。在既有畫面上加一個欄位 | 591 |
| add-screen | 從零建一支 M 維護畫面 | 752 |
| add-query-screen | 從零建一支 I 查詢畫面(M 的減法版) | 452 |
| add-batch | 從零建一支 B 批次 | 652 |
| change-sp-fn-trigger | 加 / 改 PL/SQL 物件 | 499 |
| add-report | 加 / 改 Crystal 報表 | 292 |
| change-eva-flow | 改四眼流程:加檢核、加稽核、改預設值 | 272 |
| deploy | 部署:改了什麼要佈哪些 | 354 |
| build-env | 建置環境:新人第一天 | 224 |

### 2.3 部署矩陣(縮版)

一句話:**改 UI 佈客戶端,改其餘五層佈伺服端,`View.xsd` 兩端都要。**完整表在 部署手冊 §2,展開說明在 速查卡 §6。

| 改了 | 客戶端 | 伺服端 IIS | WindowsService | DB |
|---|---|---|---|---|
| `UI.<MOD>` | ✔ |  |  |  |
| `UIEntity.<MOD>`(`View.xsd`) | ✔ | ✔ | ✔ |  |
| `FormProxy` / `Control` / `PO` / `DataEntity`(`Model.xsd`) |  | ✔ |  |  |
| `TA.DataAccess`(四眼引擎) |  | ✔ |  |  |
| 共用層(`TA.MappingCode` / `TA.Utility*` / `Exceptions`) | ✔ | ✔ | ✔ |  |
| 報表範本 | ✔ 檢視 | ✔ 產出 |  |  |
| SP / Function / Trigger / View / 表結構 |  |  |  | ✔ |

⚠ 先查你改的組件在不在 **DLL 覆寫名單**裡:在名單裡的話,只重編不更新預編 DLL 落點等於沒改,而且開發機上看不出來(`runbooks/deploy.md §2.1`)。

## 3. 我要懂

### 3.1 技術總覽

| 篇 | 一句話 |
|---|---|
| 架構總覽 architecture | 技術軸的總綱:六層與命名鐵律、四眼引擎、資料存取與 SQL、typed DataSet、Remoting 邊界、掃描母體與十一個掃描器缺陷。**不要整份讀**,用左側目錄跳到你要的那一節 |

### 3.2 模組文件 29 篇

一模組一篇,講**這個模組在做什麼業務**:資料模型、每支畫面的檢核與四眼、批次與報表、改它的表會影響誰。每篇的附錄 E 是該片的踩雷清單。

| 篇 | 管什麼 | 行數 |
|---|---|---|
| bbs | BBS(受益憑證作業,推測) | 1668 |
| bms | BMS(受益人基本資料與資料變更,推測) | 1546 |
| cas | CAS（代銷通路業績管理，推測） | 1916 |
| cls | CLS(直銷潛在客戶與拜訪管理,推測) | 1323 |
| cod | COD（代碼檔與員工主檔，推測） | 1401 |
| cpm | CPM（需求處理件／抱怨記錄件／客訴件的簽核流程，推測） | 1388 |
| crm | CRM（潛在客戶與直銷指派管理，推測） | 1723 |
| dsm | DSM(直銷業務管理,推測) | 2000 |
| ec | EC(網路交易平台,推測) | 1873 |
| misc | MISC(TRP / OTA / FSK / IJP 零星模組,推測) | 1729 |
| nfdr1 | NFDR1（NFD 報表第 1 片，推測） | 1339 |
| nfdr2 | NFDR2(NFD 報表第 2 片,推測) | 1660 |
| ofd123 | OFD1-3(OFD 模組第 1–3 片,推測) | 1490 |
| ofd4 | OFD4(OFD 模組第 4 片,推測) | 1526 |
| ofd5 | OFD5(OFD 模組第 5 片,推測) | 1729 |
| ofd6 | OFD6(OFD 模組第 6 片,推測) | 1543 |
| ofd7 | OFD7(OFD 模組第 7 片,推測) | 1360 |
| ofd8 | OFD8(OFD 模組第 8 片,推測) | 1739 |
| ofd9 | OFD9(OFD 模組第 9 片,推測) | 2119 |
| ofdb | OFDB(OFD 模組批次片,推測) | 1801 |
| ofdb3 | OFDB3(OFD 批次第 3 片,推測) | 1678 |
| ofdb4 | OFDB4(OFD 批次第 4 片,推測) | 1412 |
| ofdb5 | OFDB5(OFD 批次第 5 片:OFDB / OTAB 兩專案,推測) | 1764 |
| ofdi1 | OFDI1(OFD 查詢畫面第 1 片:ATLAS.OFD.Query,推測) | 1483 |
| ofdi2 | OFDI2(查詢畫面第 2 片:OTA.Query / EC.Query,推測) | 1697 |
| ofdr1 | OFDR1(OFD 報表第 1 片:ATLAS.OFD.Report,推測) | 1653 |
| ofdr2 | OFDR2(報表第 2 片:OTA.Report / EC.Report,推測) | 1246 |
| rsp | RSP(定期定額,推測) | 2306 |
| tmk | TMK(電話行銷 Telemarketing / CallOut,推測) | 1457 |

## 4. 用 AI 問(Copilot agent)

同一份知識庫也做成了 Copilot agent:直接問代號、表名、錯誤訊息,它查完附出處回答。

| 要用在 | 怎麼做 |
|---|---|
| **M365 Copilot(Agent Builder)建置清單** | 逐步清單:要貼的名稱、描述、指示、建議提示都有複製鈕;技能檔與知識檔逐一下載 |
| m365/skill/ | Agent Builder「技能」用:`SKILL.md` + `references/` 16 個 .md,下載後自己壓成 zip(SKILL.md 要在 zip 最上層) |
| m365/knowledge/ | Agent Builder「知識」上傳用(16 個 .txt,備援) |
| GitHub Copilot(VS Code / github.com) | 用 VS Code 開這個 repo,Copilot Chat 的 agent 下拉選 `atlas-kb`;定義在 `.github/agents/atlas-kb.agent.md` |

## 5. 這一頁是怎麼來的

| 項 | 值 |
|---|---|
| 產生時間 | 2026-09-21 13:52 |
| 產生者 | `docs/tools/build_site_index.py`(可重跑;行數與一句話從兩份 README 動態抽) |
| 站台規模 | 畫面 911 · 實體表 437 · 報表範本 608 |
| 已知缺陷 | 1,682 條;兩條死碼線聯集 151 支畫面一按就 NRE |
| 文件份數 | 總覽 1 + 架構 1 + 速查卡 1 + 症狀表 1 + 手冊 9 + 模組篇 29 + 查詢頁 3 |

> 數字與文件同步的方法:改過 `Dev/` 之後跑 `atlas_scan.py --index --refresh`,再依序重生查詢頁,最後重跑本支。

由 build_doc.py v2.0.0 於 2026-09-21 13:52 產生 · 標題 11 · 圖 0 · 表格 9 · 程式錨點 0 · § 連結 1 · 引用檢查：停用

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/CHEATSHEET.md
============================================================

# ATLAS 速查卡

> **一頁 A4 雙面,印出來貼旁邊。**只收「不知道就會做錯」的骨幹,每條附出處;細節去出處讀,本卡不展開。讀序 `OVERVIEW.md` → 本卡 → `architecture.md` → 自己的模組篇 → `runbooks/`;症狀查修走 `TROUBLESHOOT.md`。規模:**畫面 911 · 實體表 437 · 報表範本 608 · 缺陷 1,682(高 435)**。

## 1. 畫面代號

**前 3 碼模組(`OFD` / `CAS` / `BMS` …)+ 第 4 碼型別 + 後 3 碼流水號 + 可選後綴**;型別 `M` 維護 285 · `I` 查詢 87 · `B` 批次 215 · `R` 報表 324(`architecture.md §2`)。代號一定案,六層的**檔名 / 類別名 / namespace / xsd 根節點全部由它推導**,不必查任何 registry。 ⚠ **`A`、`B` 後綴至少七種成因**(境內外 · MSSQL 轉 Oracle 改名 · 第二張表 · 代號的一部分 · 族名 · 兩子系統各一份 · 同資料第二出口),**看到必須逐張查,不能套規則**(`OVERVIEW.md 附錄 A`)。

## 2. 六層:哪一層放哪

| # | 層 | 檔名 | 職責 | 不該做 |
|---|---|---|---|---|
| 1 | UI | `<代號>.cs` | 擺控件、綁事件、填 `ProcessVDB` | 不碰 DB |
| 2 | FormProxy | `<代號>_Pxy.cs` | 遠端門面,`try / catch` 包 Control | 不放邏輯 |
| 3 | Control | `<代號>_Ctl.cs` | 組 PO、宣告 VDB 型別、Model 與 View 互搬 | 不寫 SQL |
| 4 | PO | `<代號>_PO.cs` | **唯一碰 DB 的層**:宣告主明細、組 SQL / 叫 SP | 不認識 ViewVDB |
| 5 | DataEntity | `<代號>Model.xsd` | 伺服器側 typed DataSet(貼近實體表) | 不放邏輯 |
| 6 | UIEntity | `<代號>View.xsd` | 用戶端側 typed DataSet,跨 Remoting 序列化 | 不放邏輯 |

- 出處 `architecture.md §2`。**Remoting 邊界在 UI 與 FormProxy 之間**(`architecture.md §8`)——整張部署表都是這一條推出來的。

- **R 報表是七層**,多一層 Crystal(`Source/CrystalReports/Report.<MOD>/` 的 `<代號>RPS.rpt`),報表方案各層資料夾一律加 `Report` 前綴(`ofdr1.md §0.1`)。

- **I 查詢方案**各層資料夾加 `Query` 前綴,PO 檔名仍是 `<代號>_PO.cs`;`<代號>OracleDao.cs` 這個命名**只在 EC 那條線**(`ofdi1.md §0.1`)。

## 3. 主明細:三處同名

```
this.MasterTable = new xTableMapping("DSM001A", "DSM001A");    // 1 實體表名, 2 VDB 裡 DataTable 名
this.DetailTable.Add(new xTableMapping("DSM002A", "DSM002A"));
```

宣告位置是 **PO 建構子**。要一致的三處:`xTableMapping` 第 1 參數(實體表名)、第 2 參數(VDB 裡 DataTable 名)、`Model.xsd` / `View.xsd` 的表名。**對不上的症狀是「存得進去、查不回來」**(`runbooks/add-screen.md §5.2`)。 ⚠ **兩段式寫法 grep 不到**:`xTableMapping tp = new xTableMapping(...); this.MasterTable = tp;`,全庫 6 支。用 `xTableMapping`,不要寫成舊世代的 `TableMapping`。

## 4. 四眼(EVA):三階段 13 欄

Entry(經辦鍵入)→ Verify(覆核)→ Approve(核准);**核准前資料躺在待辦裡,不算正式資料**(`architecture.md §3`)。

13 欄 = `STATUS` + 六組 `*ID` / `*DATE`:`CREATE`(只在第一次 `Add`)· `UPDATE`(**每個** EVA 動作都改寫)· `ENTRY`(`Add` / `Modify` / `Delete` / `UnDelete` / `Resend`)· `VERIFY`(`Verify`)· `APPROVE`(`Approve` / `ApproveDelete`)· `REJECT`(`Reject`)。固定 13 欄與動作無關(每次全送,值由 DLL 決定);第 14 欄 `dataid` 只在 INSERT 寫。 ⚠ 兩個例外:**受益人資料變更走變更申請單,覆核完不生效,要等批次 `OFDB003` 跑**(`bms.md §2.1`);**全庫 36 支繞過四眼直接改正式表**(`OVERVIEW.md §5`)。

## 5. PO 基底:白名單 / 黑名單

| 基底 | 子類 | 新畫面 | 說明 |
|---|---|---|---|
| `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` | 271 / 61 | ✔ 單筆 / 多筆主檔 | 現行主線 |
| `BasicEVAPO` / `MultiRowEVAPO` | 66 / 11 | ✘ | `dbTA` 恆 null,**連查詢都 NRE** |
| 報表派 `Basic_PO` | 76 | ✘ | `m_db` 恆 null,**按預覽即 NRE** |
| `TA_PO` / `Basic4EyesPO` / `MultiRow4EyesPO` | 0 | ✘ | 純死碼,改了沒反應也不報錯 |

**兩條死碼線聯集 151 支畫面(17%)一按就 NRE**(`BasicEVAPO` 派 76 支 + 報表 `m_db` 派 76 支,`OFDM242` 兩條都中只算一次;`architecture.md §3.1.1`、`architecture.md 附錄 D.3`、`runbooks/add-screen.md §5.7`)。所以**接到「某支畫面壞掉」的單,第一件事是查它的 PO 繼承誰**——開 `query.md` 打代號最快。

## 6. 部署矩陣(縮版)

一句話:**改 UI 佈客戶端,改其餘五層佈伺服端,`View.xsd` 兩端都要。**完整表在 `runbooks/deploy.md §2`。

| 改了 | 客戶端 | 伺服端 IIS | WindowsService | DB |
|---|---|---|---|---|
| `UI.<MOD>` | ✔ |  |  |  |
| `UIEntity.<MOD>`(`View.xsd`) | ✔ | ✔ | ✔ |  |
| `FormProxy` / `Control` / `PO` / `DataEntity`(`Model.xsd`) |  | ✔ |  |  |
| `TA.DataAccess`(四眼引擎) |  | ✔ |  |  |
| 共用層(`TA.MappingCode` / `TA.Utility*` / `Exceptions`) | ✔ | ✔ | ✔ |  |
| 報表範本 | ✔ 檢視 | ✔ 產出 |  |  |
| SP / Function / Trigger / View / 表結構 |  |  |  | ✔ |

⚠ 先查你改的組件在不在 **DLL 覆寫名單(25 個組件、143 筆 `HintPath`)**:在名單裡的話,只重編不更新預編 DLL 落點等於沒改,而且開發機上看不出來(`runbooks/deploy.md §2.1`、`architecture.md 附錄 C.5`)。

## 7. 三條軌

**`ATLAS.OFD*` 境內分戶軌 · `OTA*` / `OTAB` 境外綜合帳戶軌 · `EC*` 電子交易(網路 / 語音)軌。** `NFD` **不是第四條軌**,是境內軌的**純輸出層**:沒有自己的表、也沒有主專案(`OVERVIEW.md §1`、`nfdr1.md §0`)。

## 8. 常用指令

```
py -V:3.12 /docs/tools/atlas_scan.py --screen <代號>     # 六層 / 主明細 / PO 基底
py -V:3.12 /docs/tools/atlas_scan.py --table <表名>      # 誰宣告它、誰讀寫它
py -V:3.12 /docs/tools/atlas_build_doc.py <x>.md --repo-root  --report <x>.md.refcheck.md
py -V:3.12 /docs/tools/check_xrefs.py                  # 跨文件 § 引用指不指得到
py -V:3.12 /docs/tools/test_scan.py                    # 掃描器回歸
```

改過 `Dev/` 後照序重生:`atlas_scan.py --index --refresh` → `--export-screens-ext` → `--export-readers` → `--export-messages` → `build_query.py` / `build_defects.py` / `build_messages.py` → `build_site_index.py`。 ⚠ 做任何靜態統計**第一件事是剝註解,`//` 和 `/* */` 都要**(repo 保留大量註解掉的程式碼,不剝數字一律偏高);`Dev/` 有 **241 個 cp950 檔**,讀檔走 `atlas_scan.read_text`,不要直接 `open(encoding='utf-8')`(`architecture.md 附錄 D.3`)。**不要 Read `*.Designer.cs`**(一支 5,375 行,全庫 2,190 支)。

## 9. 已知坑前十型(1,682 條缺陷的型別分佈)

| # | 型 | 條 | 一句話 | 代表出處 |
|---|---|---|---|---|
| 1 | 寫死常數 / 位置取參數 | 230 | 代碼值寫死在 SQL 或程式裡;批次靠參數位置取值 | `cod.md 附錄 E` |
| 2 | 被註解的檢核 | 218 | 檢核整段躺在註解裡,看起來有、其實沒有 | `ofd6.md 附錄 E` |
| 3 | 例外被吞 / 空訊息 | 168 | `catch` 是空的或只塞訊息字串,**fail-open**:錯了照樣往下跑 | `ofdr1.md 附錄 E` |
| 4 | 死碼 / 死條件 / 無呼叫端 | 157 | 方法還在但沒人呼叫;或條件永遠成立 / 永遠不成立 | `ofd7.md 附錄 E` |
| 5 | 成對 / 平行複本只改一邊 | 141 | 同一概念兩份實作(境內外、MSSQL 與 Oracle),改一邊忘另一邊 | `crm.md 附錄 E` |
| 6 | 字串串接進 SQL | 132 | 條件用字串串接進 SQL,不是繫結參數 | `ofd9.md 附錄 E` |
| 7 | 交易 / rollback 破口 | 128 | 多語句沒包同一交易,或例外後沒 rollback | `ofdb3.md 附錄 E` |
| 8 | `ExecuteNonQuery` 回傳值被蓋 | 111 | `i = 1;` 或 `if (i == -1)`,影響列數檢核形同虛設 | `cpm.md 附錄 E` |
| 9 | Oracle 三值邏輯 | 110 | `欄 <> '值'` / `= ''` / `NOT IN` / `NVL(TRIM(:p),欄)` 遇 NULL 是 UNKNOWN,**無聲過濾**;十個模組中過 | `ofd8.md 附錄 E` |
| 10 | 中文名 / 中繼資料錯誤 | 78 | 畫面或欄位中文名與實際不符,照名字找會找錯地方 | `ofdb.md 附錄 E` |

次高兩型也常咬人:**`INNER JOIN` 無聲吃資料** 66 條(報表少印且不提示,`nfdr1.md 附錄 E`)、**全域暫存表併發** 37 條(兩人同時按同一張報表互相蓋掉,`ofdr2.md 附錄 E`)。全部可篩可排序:開 `defects.md`。

## 10. 三個離線查詢頁(雙擊即開,不用起 server)

- `query.md` —— 手上有代號或表名:六層路徑、主明細、**PO 基底(死畫面標紅)**、誰讀寫這張表。

- `messages.md` —— 線上噴了一句中文訊息:反查是哪支程式哪一行丟的(9,440 筆)。

- `defects.md` —— 要動某模組之前:先看它已知有什麼坑(1,682 條,可依模組 / 嚴重度 / 型別篩)。

⚠ 模組篇附錄 E 引用的錯誤訊息**有意譯的**(實測 4 句在原始碼裡根本不存在),要原文一律以 `messages.md` 為準。

由 build_doc.py v2.0.0 於 2026-09-21 13:52 產生 · 標題 11 · 圖 0 · 表格 4 · 程式錨點 0 · § 連結 0 · 引用檢查：畫面 2（缺 0） · 結果集 2（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/TROUBLESHOOT.md
============================================================

# ATLAS 症狀路由表

> **遇到 X → 先看哪份的哪節。**這份不解釋原因,只負責把你三十秒內丟到對的那一頁。 **只收「文件裡已經有答案」的症狀**;查不到答案的另列在 §7,免得你找一整天才發現沒人寫過。骨幹知識在 `CHEATSHEET.md`,業務全貌在 `OVERVIEW.md`,技術通則在 `architecture.md`。

> 三個離線頁雙擊即開:`query.md`(代號 / 表反查)· `messages.md`(錯誤訊息反查)· `defects.md`(1,682 條缺陷)。

## 1. 畫面:開不起來、按了就爆

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 畫面一按查詢就 `NullReferenceException` | `query.md` 打代號看 **PO 基底**;`architecture.md §3.1.1` | 繼承 `BasicEVAPO` / `MultiRowEVAPO` 的 `dbTA` 恆 null,**連查詢都爆**,全庫 76 支 |
| 報表一按預覽就 `NullReferenceException` | `query.md` 看 PO 基底;`architecture.md 附錄 D.3` | 報表派 `Basic_PO` 的 `m_db` 恆 null,全庫 76 支(NFD 55 · OFD 19 · RSP 6) |
| 新建的畫面一按存檔就 NRE | `runbooks/add-screen.md §5.7` | 基底選錯。新畫面只准 `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` |
| 新建的畫面存得進去、查不回來 | `runbooks/add-screen.md §5.2` | 主明細**三處同名**沒對齊:`xTableMapping` 兩個參數 + xsd 表名 |
| 既有畫面加了欄位,存得進去、查不回來 | `runbooks/add-column.md §5.2` | **寫入端自動、讀取端手寫**:`Build*SQLString` 的欄位清單沒加就撈不回來 |
| 加了欄位,維護畫面看得到、待辦清單看不到 | `runbooks/add-column.md §5.3` | `BuildMasterSQLString` 有 `isToDoString` 兩條分支,只加了一邊 |
| 改了 xsd,build 過了但行為還是舊的 | `architecture.md §5` | `.Designer.cs` 已 commit 且**不由 MSBuild 重生**,要在 VS 裡存檔觸發 |
| 查詢畫面(`I`)找不到 `MasterTable` 宣告 | `ofdi1.md §0.2` | 不是漏寫。I 畫面 35 支**全部沒有** `MasterTable` / `DetailTable`,也沒有四眼欄 |
| 同一個代號有兩份 PO,不知道線上跑哪一份 | `architecture.md 附錄 D.3`(D3);`ofd4.md 附錄 E` | 同代號雙實作真實存在(境內 / 境外各一份、MSSQL / Oracle 各一份),**兩版讀不同表**出過事故 |
| 選單點得到的畫面,`atlas_scan` 查不到 | `architecture.md 附錄 D.4` | 畫面母體是以 `_Ctl.cs` 建的,**連 Control 都沒有的代號不在 911 裡**(48 個) |
| `atlas_scan` 說缺某一層,但檔案明明在 | `architecture.md 附錄 D.3`(D9–D11) | 檔名壞掉照樣編得起來:副檔名前夾空白、副檔名重複、層後綴大小寫或少字母 |

## 2. 資料:少了、沒進去、被蓋掉

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 覆核通過了,資料沒進本表 | `bms.md §2.1` | 受益人資料變更走**變更申請單**,覆核≠生效,要等批次 `OFDB003` 把變更後的值寫回 |
| 想判斷某張變更單生效了沒 | `bms.md §2.1` | 全庫一致的判準是變更生效時間欄位為空代表尚未生效 |
| 查詢條件填了值,某些資料就是撈不出來 | `defects.md` 篩「Oracle 三值邏輯」;`ofd8.md 附錄 E` | `欄 <> '值'` / `= ''` / `NOT IN` / `NVL(TRIM(:p),欄)` 碰到 NULL 是 UNKNOWN,**無聲過濾**,十個模組中過 |
| 資料被條件濾掉,畫面卻不提示 | `modules/README.md` 的五類卡控說明 | 「過濾(無提示)」是五類卡控之一,設計如此,不是 bug |
| 某筆資料沒走四眼就進了正式表 | `OVERVIEW.md §5`;`misc.md §2` | 全庫 36 支畫面 / 批次繞過四眼,狀態欄直接寫死核准值 |
| 匯入淨值後,同一天別的基金淨值全不見 | `misc.md §4.11` | 整批匯入的 `DELETE` 條件**只有淨值日期**,不含基金,先刪光再只補回檔案裡有的 |
| 表名長得像、不知道該改哪一張(帶 `A` / `B` 後綴) | `OVERVIEW.md 附錄 A` | `A`、`B` 後綴**至少七種成因**,看到必須逐張查,不能套規則 |
| 文件寫某表幾欄,跟實際對不上 | `modules/README.md` 的警告段;改用 `atlas_scan.py --table` | 前七篇寫於掃描器第二輪修正之前,內文欄位數可能偏低 |
| 改一處生效、另一處沒生效 | `defects.md` 篩「成對 / 平行複本只改一邊」 | 同一概念常有兩份實作(境內外、MSSQL 與 Oracle),141 條缺陷是這一型 |

## 3. 報表

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 報表少印幾列,而且沒有任何提示 | `defects.md` 篩「INNER JOIN」;`nfdr1.md 附錄 E` | `INNER JOIN` 讓對不到的資料無聲消失,66 條缺陷是這一型 |
| 兩個人同時按同一張報表,資料互相蓋掉 | `ofdr2.md §2.4`;`ofdr2.md 附錄 E` | 報表 SP 用**全域、不分使用者的暫存表**做資料權限過濾,沒有使用者鍵、`DELETE` 全表重建 |
| 報表欄位要加 / 版面要調 | `runbooks/add-report.md §2`(加欄)/ `§5`(版面) | 報表是**七層**,多一層 Crystal;範本是 build 出來的不是部署過去的 |
| 報表範本改了但現場沒變 | `runbooks/deploy.md §7` | 範本由 build 產出,不是單獨複製過去的檔案 |
| 報表看不到筆數,按預覽才知道有沒有資料 | `ofdr2.md §7` | 36 支裡只有 1 支保留「查詢」按鈕,其餘按預覽前**什麼都看不到**,是設計如此 |

## 4. 批次與 WindowsService

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 要改批次幾點跑,在 Windows 工作排程器裡找不到 | `ofdb3.md §6` | 時刻存在**資料表欄位**裡,服務每 60 秒比對一次;改排程不用碰排程器也不用重編 |
| 服務裝好了、啟動了,就是不跑 | `ofdb3.md §0.6` | 三支服務的進入點判斷執行帳號,不等於系統帳號就走 Console 偵錯模式,不會進服務迴圈 |
| 批次回報「執行成功」,但一筆都沒動 | `defects.md` 篩「`ExecuteNonQuery` 回傳值被蓋」;`cpm.md 附錄 E` | `i = 1;` 或 `if (i == -1)` 把影響列數檢核蓋掉,111 條缺陷是這一型 |
| 批次中途失敗,前半段的資料留在庫裡 | `runbooks/add-batch.md §6.3`;`defects.md` 篩「交易 / rollback 破口」 | 交易由 C# 端開、SP 跑在裡面;沒包同一交易或例外後沒 rollback,128 條缺陷是這一型 |
| 批次重跑一次,資料變兩份 | `runbooks/add-batch.md §6.4` | 重跑安全要自己做(先 `DELETE` 或用旗標),框架不管 |
| 批次參數給錯位置就跑錯東西 | `runbooks/add-batch.md §3.4` | `Main(string[] args)` 靠**位置**取參數,是已知缺陷;手冊教怎麼避 |
| 批次連不上伺服端 | `runbooks/add-batch.md §4.1` | 同一批批次有的設定檔有 Remoting 區段、有的沒有;要不要設看它打不打伺服端門面 |
| 批次出錯但沒人知道 | `runbooks/add-batch.md §6.5` | 不可吞例外;失敗要寫進 log 表,手冊列了寫哪張 |

## 5. 部署與環境

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 部署後客戶端反序列化錯誤 | `runbooks/deploy.md §2` | `View.xsd`(UIEntity)是跨 Remoting 的型別,**兩端都要佈**,版本不一致就在反序列化時爆 |
| 我這台好了,別人還是舊的 | `runbooks/deploy.md §2`;`architecture.md §8` | Remoting 邊界在 UI 與 FormProxy 之間:改 UI 佈客戶端,改其餘五層佈伺服端 |
| 程式重編了,現場行為完全沒變 | `runbooks/deploy.md §2.1`;`architecture.md 附錄 C.5` | 25 個組件 repo 有原始碼卻被綁成預編 DLL,只重編不更新落點等於沒改,**開發機上看不出來** |
| 新人的機器編不過 / 改了沒效果 | `runbooks/build-env.md §8` | 該本有症狀對照表;前提三件在 `runbooks/build-env.md §0.1` |
| 要重裝服務或改服務帳號 | `runbooks/deploy.md §5` | 服務帳號**不能**改成網域帳號,該節寫了原因 |
| 要改的 SP 資料庫有、repo 沒有 | `runbooks/change-sp-fn-trigger.md §2`;`architecture.md 附錄 B` | 程式呼叫 380 支 SP,repo 只有 61 支有腳本,批次與報表邏輯大量在版控外 |
| 覆核流程要多一條檢核 / 要加稽核軌跡 | `runbooks/change-eva-flow.md §4.1` | 掛在 PO 建構子註冊的四眼事件上 |
| 改了四眼相關的舊基底,完全沒反應 | `runbooks/change-eva-flow.md §0.1` | `TA_PO` 與 `Basic4EyesPO` 共 6,363 行是死碼,零繼承零實例化 |

## 6. 找東西與統計

| 症狀 | 先看哪 | 為什麼 |
|---|---|---|
| 線上跳一句中文訊息,不知道是哪支程式丟的 | `messages.md` | 9,440 筆常值訊息反查程式檔與行號;支援全形半形拉平與 `…` 萬用字元 |
| 模組篇附錄 E 抄的訊息,在原始碼裡 grep 不到 | `messages.md` | 實測 4 句是寫文件的人**意譯**,不是原文;要原文一律以該頁為準 |
| grep 中文字串在某些檔完全沒命中 | `CHEATSHEET.md §8`;`architecture.md 附錄 D.3` | `Dev/` 有 241 個 cp950 檔,用 UTF-8 讀會漏;讀檔走 `atlas_scan.read_text` |
| 自己 grep 出來的統計數字比文件大一截 | `CHEATSHEET.md §8`;`architecture.md 附錄 D.3` | **沒剝註解**。這個 repo 保留大量註解掉的程式碼,`//` 和 `/* */` 都要剝 |
| 要知道改這張表會影響誰 | `query.md` 查表名;`atlas_scan.py --table <表名>` | 反查哪些 PO 宣告它、誰在 SQL 裡讀寫它。**跨模組共用在這套系統是常態不是例外** |
| 要知道某支畫面已知有什麼坑 | `defects.md` 依模組 / 代號篩;該模組篇附錄 E | 1,682 條缺陷總表,高 435 條 |
| 不知道該讀哪一份文件 | `OVERVIEW.md §7`(讀序)· `runbooks/README.md` 的「我要做 X → 看哪本」路由表 | 兩張路由表,一張給讀、一張給改 |

## 7. 文件裡**還沒有**答案的症狀(別白花時間找)

以下都是會真實遇到、但目前 29 篇模組篇 + 架構篇 + 9 本手冊裡**查不到答案**的。原因一律是「輸入拿不到」,不是沒寫。

| 症狀 | 為什麼沒有 | 拿到什麼就能補 |
|---|---|---|
| 「使用者說權限不足 / 看不到某筆資料」——權限怎麼設的 | 選單與角色權限表在資料庫、不在版控 | 一份權限相關表的 dump |
| 「這支 SP 裡到底做了什麼」——查不到腳本 | 380 支被呼叫的 SP 只有 61 支在版控(`architecture.md 附錄 B`) | 資料庫連線,或 SP 全量匯出 |
| 「這個代碼值 `'3'` 是什麼意思」 | 值域主檔在資料庫;版控內的代碼類別檔有 216 個值域類別但**沒有任何訊息碼類別** | 代碼主檔的 dump |
| 「線上還有沒有人在用這支畫面」 | repo 內沒有使用率、沒有存取 log 的分析資料 | 一段時間的系統 log |
| 「這支畫面 / 報表為什麼這麼慢」 | 沒有執行計畫、沒有索引清單、沒有資料量級 | 正式庫的統計資訊 |
| 「昨天那支批次失敗了,log 在哪一張表」 | 各批次各寫各的,沒有全庫彙整 | 逐支批次的 log 表對照(可由 `atlas_scan` 補掃) |
| 「框架 DLL 裡這個方法實際上做什麼」 | 框架組件無原始碼,文件一律標「從呼叫端反推」 | 框架原始碼或反編譯授權 |
| 「正式環境的主機名 / 落地路徑是什麼」 | 手冊標〔客戶特定〕,本站台的值未回填(`runbooks/deploy.md 附錄 B`) | 部署機的存取權 |
| 「這個控件對應哪個欄位」 | 規範上不 Read `*.Designer.cs`(一支 5,375 行、全庫 2,190 支),沒有控件對欄位的彙整 | 一支只抽 Designer 控件對應的掃描器 |
| 「報表範本裡哪一格印哪個欄位」 | 範本是二進位,只彙整到範本與資料集層級 | 範本轉文字的工具 |

> 這張表本身就是**下一輪要補什麼**的清單。補到答案的人,請把該列搬到上面六節去。

由 build_doc.py v2.0.0 於 2026-09-21 13:52 產生 · 標題 8 · 圖 0 · 表格 7 · 程式錨點 0 · § 連結 1 · 引用檢查：畫面 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/README.md
============================================================

# ATLAS 模組知識庫索引

> 一模組一篇,講**這個模組在做什麼業務**:資料模型、每支畫面的檢核與四眼、批次與報表、以及改它的表會影響誰。

> 共同前提在 `architecture.md`,操作步驟在 `runbooks/README.md`。**三者不重複**——架構篇講通則、手冊講怎麼改、模組篇講這裡的業務長什麼樣。

## 1. 已完成

| 模組 | 中文名(推測) | 畫面 | 表 | 行數 | 圖 | 錨點 |
|---|---|---|---|---|---|---|
| [`bbs.md`](bbs.md) | BBS(受益憑證作業,推測) | 17 | 20 | 1668 | — | — |
| [`bms.md`](bms.md) | BMS(受益人基本資料與資料變更,推測) | 11 | 26 | 1538 | — | — |
| [`cas.md`](cas.md) | CAS（代銷通路業績管理，推測） | 16 | 10 | 1916 | — | — |
| [`cls.md`](cls.md) | CLS(直銷潛在客戶與拜訪管理,推測) | 7 | 5 | 1323 | — | — |
| [`cod.md`](cod.md) | COD（代碼檔與員工主檔，推測） | 12 | 7 | 1401 | — | — |
| [`cpm.md`](cpm.md) | CPM（需求處理件／抱怨記錄件／客訴件的簽核流程，推測） | 13 | 8 | 1388 | — | — |
| [`crm.md`](crm.md) | CRM（潛在客戶與直銷指派管理，推測） | 18 | 9 | 1723 | — | — |
| [`dsm.md`](dsm.md) | DSM(直銷業務管理,推測) | 29 | 17 | 2000 | — | — |
| [`ec.md`](ec.md) | EC(網路交易平台,推測) | — | — | 1873 | — | — |
| [`ofd7.md`](ofd7.md) | OFD7(OFD 模組第 7 片,推測) | — | — | 1360 | — | — |
| [`ofd8.md`](ofd8.md) | OFD8(OFD 模組第 8 片,推測) | — | — | 1739 | — | — |
| [`ofd9.md`](ofd9.md) | OFD9(OFD 模組第 9 片,推測) | — | — | 2119 | — | — |
| [`ofdb.md`](ofdb.md) | OFDB(OFD 模組批次片,推測) | — | — | 1801 | — | — |
| [`rsp.md`](rsp.md) | RSP(定期定額,推測) | 56 | 23 | 2306 | — | — |
| [`tmk.md`](tmk.md) | TMK(電話行銷 Telemarketing / CallOut,推測) | 14 | 5 | 1457 | — | — |

## 2. 待撰寫

依 `plans/05-phase4-module-docs.md` 的批次規劃排。畫面數與表數由掃描器即時算出:

| 批 | 模組 | 畫面 | B | I | M | R | 表 |
|---|---|---|---|---|---|---|---|
| 3 | `ofd` | 550 | 165 | 77 | 214 | 94 | 291 |
| 4 | `nfd` | 136 | 0 | 0 | 0 | 136 | 0 |
| 4 | `ota` | 3 | 1 | 0 | 1 | 1 | 1 |
| 5 | `ipj` | 15 | 7 | 5 | 1 | 2 | 0 |
| 5 | `trp` | 6 | 0 | 1 | 4 | 1 | 2 |
| 5 | `sdm` | 2 | 2 | 0 | 0 | 0 | 2 |
| 5 | `ctl` | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 | `fsk` | 1 | 0 | 0 | 1 | 0 | 1 |
| 5 | `ijp` | 1 | 0 | 0 | 0 | 1 | 0 |

進度:**193 / 908 支畫面**(21%)· **15 / 19 個模組**。

> ⚠ **前七篇(`bms` `cas` `cls` `cod` `crm` `dsm` `bbs`)寫於掃描器第二輪修正之前。** 那次修正(`architecture.md 附錄 D.3` 的 D4 / D5)讓實體表由 367 增為 413、並修好 inline `simpleType` 欄位的解析——**所以這七篇內文引用的「某表幾欄」可能偏低**。覆蓋率(哪些表被提到)已全部重驗為 100%,但內文數字未逐一重對。 **欄位數以 `atlas_scan.py --table <表名>` 的即時輸出為準**,不要引用內文的數字。已知一例:`bms.md` 記 `OFD206` 為 12 欄,實際 21 欄(由 `ofd7.md` 交叉驗證發現)。

## 3. 每篇都有什麼

| 章 | 內容 |
|---|---|
| `§0` | 這模組管什麼業務。**目前都是從表名與欄位中文名推測的**,待選單 / 對照表回填 |
| `§1` | 圖群:全景、表關係、四眼與卡控、批次報表流 |
| `§2` | 資料模型:表、主鍵、四眼欄位齊不齊、欄位中文名總表 |
| `§3` | 畫面清冊 B / I / M / R 四張表 |
| `§4`–`§7` | 逐支畫面:M 維護、I 查詢、B 批次、R 報表 |
| `§8` | **跨模組共用**:改這裡的表會影響誰 |
| 附錄 A–F | 表總表 / DB 物件 / 代碼值 / 母體覆蓋率 / 踩雷 / 版本 |

**卡控結果一律分五類**:阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋。「過濾(無提示)」最容易被忽略——資料被條件濾掉而畫面不說,使用者以為沒資料。

## 4. 怎麼查

```
py -V:3.12 \docs\tools\atlas_scan.py --module <MOD>
py -V:3.12 \docs\tools\atlas_scan.py --table <表名>
```

第一支列該模組的畫面、表、SP、報表;第二支反查一張表被哪些畫面用到——**改表之前一定要跑第二支**,跨模組共用在這套系統裡是常態不是例外。

由 build_doc.py v2.0.0 於 2026-09-15 11:53 產生 · 標題 5 · 圖 0 · 表格 3 · 程式錨點 0 · § 連結 0 · 引用檢查：Table 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/README.md
============================================================

# ATLAS 維護手冊索引

> 共 **9** 本。每一本都是「純程式碼閱讀彙整 + 操作步驟」,附程式錨點,未修改任何 ATLAS 原始碼。

> 共同前提在 `architecture.md`——**不要整份讀**,用它的目錄跳到你要的那一節。

## 1. 我要做這件事,該看哪本

| 我要… | 看哪本 | 從哪節開始 |
|---|---|---|
| 欄位要多一個 | [`add-column.md`](add-column.md) | `§2–§9` |
| 欄位改型別或長度 | [`add-column.md`](add-column.md) | `§0 不適用,先問` |
| 報表要多印一欄 | [`add-report.md`](add-report.md) | `§2 第一列` |
| 報表版面要調 | [`add-report.md`](add-report.md) | `§5` |
| 要一支全新的畫面 | [`add-screen.md`](add-screen.md) | `全篇` |
| 要一支新的查詢畫面 | [`add-query-screen.md`](add-query-screen.md) | `§1 差異表` |
| 要一支新的批次 | [`add-batch.md`](add-batch.md) | `全篇` |
| 覆核時要多一條檢核 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.1` |
| 新增時要自動帶值 / 流水號 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.2` |
| 要加稽核軌跡 | [`change-eva-flow.md`](change-eva-flow.md) | `§4.3` |
| 要改 SP / Function / Trigger | [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | `全篇` |
| SP 在資料庫有、repo 沒有 | [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | `§2` |
| 改完了要送測試 / 正式 | [`deploy.md`](deploy.md) | `§2 對照表` |
| WindowsService 要重裝或改帳號 | [`deploy.md`](deploy.md) | `§5` |
| 新人要把環境架起來 | [`build-env.md`](build-env.md) | `§0.1 三個前提` |
| 編不過 / 改了沒效果 | [`build-env.md`](build-env.md) | `§8 症狀表` |

## 2. 手冊清單

| 手冊 | 一句話 | 適用情境 | 行數 | 圖 | 錨點 |
|---|---|---|---|---|---|
| [`add-column.md`](add-column.md) | 最常用。在既有畫面上加一個欄位 | 在一支既有的 **M(維護)畫面**上,替主表或明細表加一個欄位 | 591 | — | — |
| [`add-screen.md`](add-screen.md) | 從零建一支 M 維護畫面 | 在既有模組裡**從零建一支新的 M(維護)畫面**:主檔 + 明細、走四眼、六層全建 | 752 | — | — |
| [`add-query-screen.md`](add-query-screen.md) | 從零建一支 I 查詢畫面(M 的減法版) | 在既有模組裡**從零建一支 I(查詢)畫面**:唯讀、不寫入、不走四眼 | 452 | — | — |
| [`add-batch.md`](add-batch.md) | 從零建一支 B 批次 | **新建或維護一支 B(批次)畫面**:按一顆執行鈕、跑一段伺服端作業、改 DB 或產檔 | 652 | — | — |
| [`change-sp-fn-trigger.md`](change-sp-fn-trigger.md) | 加 / 改 PL/SQL 物件 | 改一支既有的 Oracle Stored Procedure / Function / Trigger / View,或新增一支 | 499 | — | — |
| [`add-report.md`](add-report.md) | 加 / 改 Crystal 報表 | 在既有報表上加 / 改欄位;替既有 R 畫面加一個新報表版型 | 292 | — | — |
| [`change-eva-flow.md`](change-eva-flow.md) | 改四眼流程:加檢核、加稽核、改預設值 | 在四眼流程上加檢核、加稽核軌跡、改新增時的預設值、加自訂動作 | 272 | — | — |
| [`deploy.md`](deploy.md) | 部署:改了什麼要佈哪些 | 改完程式要送測試 / 正式環境;或新裝一台伺服器 | 354 | — | — |
| [`build-env.md`](build-env.md) | 建置環境:新人第一天 | 新人拿到 ATLAS 原始碼,要把它變成「編得起來、跑得動」的開發機 | 224 | — | — |

## 3. 讀之前先知道的四件事

這四條在多本手冊裡重複出現,因為它們是「照直覺做就會錯」的地方:

| # | 事實 | 為什麼會咬人 | 在哪 |
|---|---|---|---|
| 1 | Remoting 邊界在 **UI 與 FormProxy 之間** | 決定改哪層佈哪台;搞錯的症狀是「我這台好了,別人還是舊的」 | `architecture.md §8.1` |
| 2 | **25 個組件在 repo 有原始碼,卻被綁成預編 DLL** | 重編不更新 `PTPFBlock` 就沒效果,而且開發機上看不出來 | `architecture.md 附錄 C.5` |
| 3 | **程式呼叫 380 支 SP,repo 只有 61 支有腳本** | 批次與報表的邏輯大量在版控外 | `architecture.md 附錄 B.0` |
| 4 | **`TA_PO` 與 `Basic4EyesPO` 共 6,363 行是死碼** | 改了完全沒反應,也不會報錯 | `runbooks/change-eva-flow.md §0.1` |

## 4. 共同工具

```
py -V:3.12 \docs\tools\atlas_scan.py --screen <代號>
py -V:3.12 \docs\tools\atlas_scan.py --table <表名>
```

改過 ATLAS 原始碼後加 `--refresh` 重掃。**不要 Read `*.Designer.cs`**(一支 5,375 行,全庫 2,190 支)。

## 5. 每本手冊都標了什麼

| 標記 | 意思 |
|---|---|
| **〔假設〕缺:輸入** | 拿不到該輸入(DB 連線 / PTPFBlock DLL / 選單表),只能從結構推論。各本附錄 B 彙整 |
| **〔客戶特定〕** | 本站台的值(主機名、路徑、機構代碼),其他站台不同 |
| 附錄 A | 該本引用的檔案與錨點清單 |
| 附錄 B | 待輸入回填:補進來之後要改哪幾段 |

由 build_doc.py v2.0.0 於 2026-09-15 17:58 產生 · 標題 6 · 圖 0 · 表格 4 · 程式錨點 0 · § 連結 0 · 引用檢查：

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
