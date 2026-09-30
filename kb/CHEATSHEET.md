<!-- 由 tools/build_copilot_kb.py 從 CHEATSHEET.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-21 -->

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
