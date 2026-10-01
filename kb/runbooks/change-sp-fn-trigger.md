<!-- 由 tools/build_copilot_kb.py 從 runbooks/change-sp-fn-trigger.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

# ATLAS 維護手冊 — 加 / 改 PL/SQL 物件(SP · Function · Trigger · View)

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`DB/SP/X.sql:行號`),行號為分析當下版本,動手前以最新檔案為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是拿不到該輸入(DB 連線 / 版本歷史)只能從結構推論,§13 彙整。前提知識:SQL 怎麼組看 `architecture.md §4`、DB 物件總表與「repo 只涵蓋 16% SP」看 `architecture.md 附錄 B`(**先讀 B.0**),**不要整份讀**;加欄位走 `runbooks/add-column.md`。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 改一支既有的 Oracle Stored Procedure / Function / Trigger / View,或新增一支 |
| 不適用 | 加表 / 加欄位(走 `runbooks/add-column.md`)· 改 PO 內嵌的 SELECT 字串(那不是 DB 物件,走 `architecture.md §4.2`) |
| 前提工具 / 變數 | Oracle 客戶端 · 有 `SW` schema 的部署帳號 · 查 `ALL_SOURCE` 的唯讀帳號 · TFS workspace;`%ATLAS_ROOT%` = ,帳號密碼一律 `***` 不寫進腳本 |
| 執行期資料庫 | **Oracle only**。設定檔裡的 SqlClient 連線字串是另一個客戶的設計期殘留(`architecture.md §4.6` 有六項證據) |
| 新參數佈位符 | 本文一律用 `<NEW_PARAM>` 代表你要加的參數名 |

### 0.1 四類物件在 repo 的規模

| 類別 | 支數 | 資料夾 | 總行數 | 有 `CREATE OR REPLACE` | 有 `EXCEPTION` |
|---|---|---|---|---|---|
| Stored Procedure | 83 | `DB/SP/` | 24,075 | 83 / 83 | 32 |
| Function | 23 | `DB/Function/` | 3,679 | 23 / 23 | 8 |
| Trigger | 13 | `DB/Trigger/` | 2,528 | 13 / 13 | 10 |
| View | 2 | `DB/View/` | 118 | 2 / 2 | — |

以 `atlas_scan.read_text()` 逐檔實測,與 `architecture.md 附錄 B` 的清單一致。

### 0.2 三件事先記住

1. **PL/SQL 沒有「改一行」這回事。**四類物件全部靠 `CREATE OR REPLACE` **整支取代**,你的檔案內容就是上線後的物件全文。

2. **84% 的 SP 不在 repo 裡。**動手前第一步永遠是 §2 的判斷流程,不是打開編輯器。

3. **檔名不是物件名。**部署時 Oracle 認的是 `CREATE OR REPLACE` 後面那個名字。全庫已經有一支對不上(§3.2)。

## 1. 改動點總覽

```text
[圖] 改 PL/SQL 物件的判斷流程:先確認在不在 repo、再依 SP / Function / Trigger / View 分四條路、再判斷呼叫端要不要改、最後部署與 rollback
圖中文字:① 第一個岔路:這支物件在不在 repo 裡 / ls DB/<類>/ + grep / 先查檔名，再查真名 / 找得到 / 改檔，原編碼寫回 / 找不到(SP 佔 84%) / 先撆 ALL_SOURCE 進版控 / ⚠ 不可重寫同名 / 會蓋掉線上邏輯 / ② 依物件別分四條路(全部走 CREATE OR REPLACE 整支取代) / Stored Procedure / 83 支 · §4 / Function / 23 支 · §5 / Trigger / 13 支 · 全 BEFORE ROW / View / 2 支 · §7 / ③ 呼叫端(PO)要不要跟著改 / 參數增減 / 換順序 / AddInParameter 逐行 / 游標增減 / LoadDataSet 表名順序 / 只改內部邏輯 / PO 不用改 / ⚠ Parameters[i] / 位置取值 3 處 / ④ 部署與 rollback / 跑整支 CREATE OR REPLACE / 沒有 ALTER 這種東西 / DB 先 / 程式後 / 簽名變才重編 PO / rollback = 舊版全文 / 沒有 _rollback 慣例 / 版本不可考 / ALL_SOURCE 為準
```

*圖:圖 1 改動點總覽。橘色實框=這一步要做;灰虛框=不用改;橘色虛框=陷阱。第一列沒走完就往下做，會把線上物件整支蓋掉。*

| 順序 | 動作 | 檔 / 位置 | 一定要 / 視條件 | 節 |
|---|---|---|---|---|
| 1 | 確認物件在不在 repo,對齊檔名 / 真名 / 編碼 | `DB/SP/` `DB/Function/` `DB/Trigger/` `DB/View/` | 一定要 | §2 §3 |
| 2 | 改物件本體 | 依類別分四條路 | 一定要 | §4–§7 |
| 3 | 改呼叫端 PO | `Dev/**/*_PO.cs` | **只有簽名或游標變了才要** | §8 |
| 4 | 部署 + rollback + 驗證 | Oracle + `DB/` | 一定要 | §9 §10 |

## 2. 先確認:你要改的物件在不在 repo 裡

**這是全手冊第一個岔路,走錯會把線上邏輯整支蓋掉。**`architecture.md 附錄 B.0`:程式以 `GetStoredProcCommand("…")` 呼叫的相異 SP 有 **380** 支,`DB/SP` + `DB/Function` 只有 106 支腳本,**319 支(84%)在 repo 內完全沒有定義**。全庫呼叫點 657 個、散在 497 個檔。

### 2.1 判斷流程

```
dir /b %ATLAS_ROOT%\DB\SP | findstr /i "<物件名>"                       :: 1. 先用檔名找
findstr /s /i /m "<物件名>" %ATLAS_ROOT%\DB\SP\*.* %ATLAS_ROOT%\DB\Function\*.*  :: 2. 再用真名找
```

| 結果 | 下一步 |
|---|---|
| 找得到檔 | 有進版控,直接改檔,走 §3 → §4–§7 |
| 檔名找不到但真名 grep 到 | 檔名與真名不符,**以真名為準**改那支檔,並在 §13 記一筆 |
| 兩種都找不到 | **只活在資料庫裡**,先做 §2.2 撈出來進版控再改 |

### 2.2 只在資料庫裡的物件:先撈出來再改

```
SELECT text FROM all_source WHERE owner='SW' AND name=UPPER('<物件名>')   -- View 不在這裡,改查 all_views
   AND type IN ('PROCEDURE','FUNCTION','TRIGGER') ORDER BY line;
```

撈回來以後:

1. 前面補 `CREATE OR REPLACE `(`ALL_SOURCE` 存的第一行是 `PROCEDURE SW.XXX`);最後補一行 `/`(SP / Function / Trigger 共 119 支都這樣收尾,View 兩支是 `;`)。

2. 存成 `DB/<類別>/<真名>.SQL`,編碼照 §3.3。

3. **先把這一版原封不動 commit 一次再開始改。**這樣 diff 才看得出你動了什麼,rollback 也才有東西可回。

### 2.3 絕對不要做的事

| 不要 | 為什麼 |
|---|---|
| 憑空重寫一支同名 SP | `CREATE OR REPLACE` 是整支取代。線上那支可能有十幾年的補丁(例 `DB/SP/S_OTA_OFDB553_EXE.sql:6-10` 有 2007 / 2008 / 2011 / 2020 / 2023 五筆修改註解),重寫等於全砍 |
| 拿同名但不同用途的檔當底稿 | `DB/SP/S_OTA_OFDR601_GET.SQL:1` 的真名是 `S_OTA_OFDR051_GET`,內容是它的**舊版**。照檔名以為在改 601,實際會把 051 退版 |
| 只看 `_PO.cs` 就推論 SP 做什麼 | PO 只看得到「呼叫哪支、傳什麼參數」;批次與報表的邏輯大量住在沒進版控的 SP 裡 |

> 例:`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:58` 呼叫的 `S_TA_CASR001_GET`,`DB/SP/` 裡**沒有**。要改它只能先走 §2.2。

## 3. 檔案慣例:命名、檔頭、編碼

### 3.1 全庫共通的五條(121 支實測)

| # | 慣例 | 實測 | 例外 |
|---|---|---|---|
| 1 | 第一行就是 `CREATE OR REPLACE`,**沒有檔頭註解區塊** | SP 83/83、Function 23/23 都在第 1 行 | 無 |
| 2 | 物件名帶 `SW.` schema 前綴 | SP 82/83、Function 22/23、Trigger 13/13 | `DB/SP/S_OTA_OFDR050_GET.SQL:1`、`DB/Function/TTP12ATMP_F1.SQL:1`、`DB/View/FNDV01.SQL:1` 三支裸名 |
| 3 | 大小寫混用,Oracle 不在意 | `SW.` 與 `sw.` 都有;Trigger 兩支寫成 `"SW"."OFD002_T01"` | — |
| 4 | 檔尾一行 `/` | SP / Function / Trigger 全部 119 支 | View 2 支以 `;` 收尾 |
| 5 | 說明寫在物件名或參數右側的 `--` 註解 | SP 69/83、Function 16/23 | 5 支用區塊註解(例 `DB/SP/S_OTA_OFDB600A_EXE.sql:3-5`) |

`_EXE` 型的範本是 `DB/SP/S_OTA_OFDB061_EXE.sql:1-6`(物件名右側 `--銷售日結轉作業`,五個 IN 參數,`IS` 起宣告區);`_GET` 型的範本在 §4.1。

### 3.2 檔名 vs 真名

`architecture.md 附錄 B` 每一列都有「檔名與真名相符」欄。全 121 支只有**一支不符**:`DB/SP/S_OTA_OFDR601_GET.SQL:1` 宣告的真名是 `S_OTA_OFDR051_GET`,與 `DB/SP/S_OTA_OFDR051_GET.SQL:1` 同名同長度(都 320 行),但少了兩處 `TRIM`(`DB/SP/S_OTA_OFDR051_GET.SQL:97` 與 `:206`)——**跑錯那支等於把 051 退版**。

規則:**新檔的檔名一律等於真名**(副檔名 `.SQL` / `.sql` 都有,不強求)。改既有檔時發現不符,**不要順手改檔名**——先確認線上到底有沒有那支物件,再決定是刪檔還是改內容,寫進 §13。

### 3.3 編碼:新檔用哪一個

`DB/` 底下 277 支的實測:**cp950 196 支 · UTF-8 BOM 81 支**。分資料夾:

| 資料夾 | cp950 | UTF-8 BOM | 非 cp950 的是哪幾支 |
|---|---|---|---|
| `DB/SP/` · `DB/View/` | 83 · 2 | 0 · 0 | 無 |
| `DB/Function/` | 20 | 3 | `DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL`、`DB/Function/f_OTA_GetTradeNav.SQL`、`DB/Function/f_OTA_GetTradeNavLock.SQL` |
| `DB/Trigger/` | 12 | 1 | `DB/Trigger/OFD113_T1.sql` |
| `DB/Table/` | 79 | 77 | 票號腳本,見下 |

**結論兩條,不要混:**

| 情境 | 用什麼編碼 | 依據 |
|---|---|---|
| **改既有物件腳本** | **原編碼寫回**(`read_text()` 的第二個回傳值) | 轉編碼會讓整支檔在 diff 裡全紅,真正改的那幾行看不出來 |
| **新增物件腳本 / 新增票號腳本** | **UTF-8 BOM** | `DB/Table/` 內容裡有年份可判讀的 15 支中,2021 年之後的 14 支有 13 支是 UTF-8 BOM(例 `DB/Table/9000010311_update.sql`、`DB/Table/Update_9000010694.sql:1-3`);`DB/Function` / `DB/Trigger` 那 4 支非 cp950 的也是後來加的那批。`runbooks/add-column.md` 對 `DB/Table/` 已下同一結論 |

讀寫一律走 `docs/tools` 的 `atlas_scan.read_text(path)`(回傳 `(內容, 編碼)`),寫回時 `open(path, 'w', encoding=enc, newline='\n')`,**不要用 `utf-8` 硬讀**。存錯編碼的症狀是 §11 第一條:**中文註解變亂碼,錯誤訊息上線後在畫面上是問號**。

### 3.4 參數命名:有慣例但不統一

| 類別 | 分佈 | 說明 |
|---|---|---|
| SP 的 IN 參數首字母 | `i` 150 · `w` 23 · `s` 4 · `c` 4 · `x` 3 · `m` 1 | `i` = in,新寫的一律用 `i`;`W` / `X` 是舊世代 |
| SP 的 OUT 參數 | `o` 61,**其中 61 個是 `OUT SYS_REFCURSOR`** | 名字幾乎都是 `OutTB1`(57 次)/ `OutTB2`(25) |
| Function 的參數首字母 | `x` 15 · `i` 13 · `c` 8 · `s` 4;型別 `VARCHAR2` 109 · `SYS_REFCURSOR` 61 · `%TYPE` 47 · `NUMBER` 18 | 另有匈牙利式 `striXXX` / `datiXXX`(`DB/Function/F_OTA_GETFNBUSINESSDAY.SQL:1`);無長度的 `VARCHAR` 還有 5 處,是舊寫法 |

規則:**新參數用 `i` / `o` 開頭 + `<表>.<欄>%TYPE`**,範本在 `DB/SP/S_OTA_OFDB553_EXE.sql:2-3`。

> 同一支的第 4 行是 `messge out varchar`——參數名拼錯(少一個 `a`)、型別用了無長度的 `VARCHAR`。**呼叫端跟著拼錯才通得過**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB553_PO.cs:118`),所以**不要順手改正拼字**,那是 breaking change。

### 3.5 例外處理慣例

| 慣例 | 實測 | 錨點 |
|---|---|---|
| 業務錯誤一律用 `RAISE_APPLICATION_ERROR`,錯誤碼 `-20001` | 全庫 46 次(`-20001` 41 · `-20000` 5) | `DB/Trigger/OFD002_T01.SQL:42` |
| 訊息開頭 `#@@#`、結尾接兩個 `&` 串接,是給前端解析的框架標記 | SP 3 檔、Trigger 3 檔在用 | `DB/Trigger/BMS001A_TDCC_BF_NO.SQL:230` |
| `WHEN OTHERS` 少用 | SP 2 檔、Function 3 檔、Trigger 1 檔 | — |

原文在 `DB/Trigger/OFD002_T01.SQL:40-43`:`EXCEPTION` → `WHEN ERRORS1 THEN` → 一行 `RAISE_APPLICATION_ERROR`,訊息是「尚有相對應的銷售機構資料，故不能刪除」。

> **〔假設〕缺:PTPFBlock DLL。**`#@@#` 在 `Dev/Common/` 全部 `.cs` 裡搜不到任何解析程式碼,推論是框架 DLL 的例外轉譯器負責剝掉前綴。新訊息**照抄這個格式**就對了。

## 4. 步驟一:改 Stored Procedure

### 4.1 現況

83 支 SP 看名字尾巴分兩種形狀:**`_GET`** 是報表 / 查詢,IN 參數 + `OUT SYS_REFCURSOR`,PO 用 `LoadDataSet` 把游標倒進 typed DataSet;**`_EXE` 與其他**是批次 / 異動,只有 IN 或 IN + OUT 純量,PO 用 `ExecuteNonQuery`。

`_GET` 範本(`DB/SP/S_OTA_OFDR051_GET.SQL:1-13`,省略中間六個同形參數):

```
CREATE OR REPLACE PROCEDURE SW.S_OTA_OFDR051_GET
(
  iTYPE               IN VARCHAR2, -- 印表類別/A:全部, 0:一般, 1:自售
  iALLOT_DATE_ST      IN VARCHAR2, -- 申購日期(起)
  OutTB1              OUT SYS_REFCURSOR
)
```

三個細節照抄:參數右側 `--` 寫**中文欄名 + 值域**、`OutTB1` 放**最後**、宣告區用 `%TYPE`(`DB/SP/S_OTA_OFDR051_GET.SQL:16-23`)。`_EXE` 範本見 §3.1;帶 OUT 純量回訊息的是 `DB/SP/S_OTA_OFDB553_EXE.sql:1-4`。

### 4.2 改法

| 你要改什麼 | 怎麼做 | PO 要不要跟 |
|---|---|---|
| 只改內部邏輯(WHERE、計算式) | 改完整支貼上去跑 | **不用** |
| 加一個 IN 參數 / 改參數型別 | 加在既有 IN 的最後、`OutTB1` 之前(給 `DEFAULT` 也不能省 PO 那一行);型別優先用 `%TYPE`,純量型別變了 PO 的 `OracleDbType` 要一起換 | 要,§8.2 |
| 加一個回傳游標 | 接在 `OutTB1` 後面命名 `OutTB2`,順序就是 PO 收表的順序 | 要,§8.3 |
| 改游標的欄位清單 | 多的欄會被丟掉、少的欄拿不到 | 看 §8.4 |

三條硬規則:

- **不要改參數順序。**PO 是具名綁定(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR051_PO.cs:69-77`),順序理論上不影響;但有 3 個呼叫點**用位置取 OUT 值**(§8.5),順序一變就抓錯參數。

- **不要改參數名的拼字**,即使它拼錯(§3.4 的 `messge`)。名字是綁定的鍵。

- **不要刪參數。**呼叫端還在傳就 `PLS-00306`,而且是**執行期**才炸,編譯 C# 沒有任何警告。

### 4.3 驗證

```
-- 1. 編譯狀態一定要 VALID;2. 有錯看 all_errors;3. 簽名對 PO
SELECT object_name, status, last_ddl_time FROM all_objects  WHERE owner='SW' AND object_name=UPPER('<物件名>');
SELECT line, position, text                FROM all_errors   WHERE owner='SW' AND name=UPPER('<物件名>') ORDER BY sequence;
SELECT position, argument_name, in_out, data_type FROM all_arguments WHERE owner='SW' AND object_name=UPPER('<物件名>') ORDER BY position;
```

第 3 條是 §8 的對照表:`argument_name` 要跟 PO 的 `AddInParameter` 字串**一字不差**。

## 5. 步驟二:改 Function

### 5.1 現況

23 支 Function 與 SP 的差別只有三處:有回傳型別、**沒有 OUT 參數**(23 支全部沒有)、可以直接寫在 SQL 裡當運算式。回傳型別 15 支是純量(`VARCHAR2` / `NUMBER` / `DATE` / `%TYPE`,例 `DB/Function/GETCLASSNAMECHT.SQL:1` 回 `COD006A.CODE_DESCRP%TYPE`),8 支是自訂 nested table 型別(例 `DB/Function/F_OTA_GetDefFeeRate.SQL:11` 回 `T_RateData_TABLE`)。

範本(`DB/Function/F_OTA_GetDefFeeRate.SQL:1-12`,省略中間七個同形參數):

```
CREATE OR REPLACE FUNCTION SW.f_OTA_GetDefFeeRate(
  iFUND_ID                 VARCHAR2,       --基金代碼
  iALLOT_TYPE              VARCHAR2        --申購別(1:一般申購; 2:定期定額; 3:轉申購)
)RETURN T_RateData_TABLE
AS
```

### 5.2 三個 Function 專屬的坑

| 坑 | 說明 |
|---|---|
| **回傳型別是 `CREATE TYPE` 出來的,型別本身不在 repo** | `T_RateData_TABLE` 在 `DB/` 找不到任何 `CREATE TYPE`。改回傳結構要先 `ALTER TYPE`,而那會讓所有相依物件 INVALID |
| **Function 被 SQL 內嵌呼叫,grep 不到 `GetStoredProcCommand`** | 例:`GET_FH_BF_NO(...)` 出現在 `DB/SP/S_OTA_OFDR051_GET.SQL:97`;`GETCLASSNAMECHT` 被 `OFDI011` 與 `OFDI531` 的 SQL 字串用。改簽名前要 grep 整個 `DB/` 與整個 PO 目錄 |
| **`--with encryption` 這種 T-SQL 殘留** | `DB/Function/f_OTA_GetTradeNav.SQL:5` 留著被註解掉的 T-SQL。不要當 Oracle 語法照抄,也不要順手刪 |

### 5.3 改法與驗證

改法同 §4.2,再加兩條:

**加參數一律加在最後**,而且不要以為給了 `DEFAULT` 呼叫端就不用改——內嵌在 SQL 字串裡的呼叫是位置式的,個數對不上就 `PLS-00306`。**改回傳型別等於改介面**,先用 `SELECT owner, name, line, text FROM all_source WHERE owner = 'SW' AND UPPER(text) LIKE '%<函式名>%'` 找出誰在用。

驗證照 §4.3 三條。Function 的回傳值在 `all_arguments` 裡是 `position = 0` 那一列。

> **〔假設〕缺:DB 連線。**自訂型別的欄位定義只能查 `ALL_TYPE_ATTRS`,repo 內查不到;8 支 nested table function 的實際結構待補。

## 6. 步驟三:改 Trigger

### 6.1 現況:13 支全部同一種形狀

**13 支 100% 都是 `BEFORE … FOR EACH ROW`**——沒有 AFTER、沒有 statement level、沒有 INSTEAD OF、沒有 compound trigger。

| Trigger | 掛哪張表 | 事件 | 做什麼 |
|---|---|---|---|
| `BMS001A_TDCC_BF_NO` | `BMS001A` | INSERT / DELETE / UPDATE OF `OMNIBUS_ID` | 綜合帳戶開關切換時產生或清掉集保戶號(內含檢核碼演算法);取消綜合同意書時連帶改掉指定買回帳號。找不到集保總公司代號就丟 `-20001`(`DB/Trigger/BMS001A_TDCC_BF_NO.SQL:230`) |
| `BMS001A_TSCDLOG` | `BMS001A` | INSERT / DELETE / UPDATE OF 19 欄 | 綜合帳戶的異動寫進集保異動 Log;新增 / 修改 / 刪除三種情境各一套「先刪舊 Log 再寫」規則(`DB/Trigger/BMS001A_TSCDLOG.SQL:13-16`) |
| `OFD002_T01` | `OFD002` | DELETE / UPDATE OF 三個名稱欄 | 部門中英文名改了同步到 `OFD068A` 的機構名稱;`OFD068A` 還有資料就不准刪部門(`DB/Trigger/OFD002_T01.SQL:31-43`)。帶 `WHEN (LENGTH(NEW.DEPT_NO) = 5 …)` 條件 |
| `OFD109_T02` | `OFD109` | INSERT / UPDATE / DELETE | INSERT 時自動配 `AUTO_NUM` 流水號;把匯款備註同步成 `OFD609` 一筆(先刪後插),`OFD601` 查不到受益人流水號就跳過(`DB/Trigger/OFD109_T02.SQL:21-44`) |
| `OFD110_T01` | `OFD110` | INSERT / UPDATE / DELETE | 集保資料上傳中一律擋下丟 `-20001`,全檔 14 處;另外維護集保異動 Log 與回寫 `BMS001A`(`DB/Trigger/OFD110_T01.SQL:31`) |
| `OFD113_T1` | `OFD113` | INSERT | 只做一件事:`DATA_ID = '1'` 時把 `ALLOT_NO` 洗成 20 個空白。全檔 11 行(`DB/Trigger/OFD113_T1.sql:1-11`) |
| `OFD253_T01` | `OFD253` | INSERT / DELETE / UPDATE | 全庫最大一支(757 行)。轉換申請的連動:同步寫改刪 `OFD220` `OFD221` `OFD113` `OFD254` `OFD255` `OFD303`,含買回轉申購的付款方式與結算確認狀態機(`DB/Trigger/OFD253_T01.sql:1-9`) |
| `OFD254_T01` | `OFD254` | INSERT / DELETE / UPDATE | 426 行。轉換確認的連動:寫 `OFD220` `OFD221` `OFD113`,更新 `OFD221` `OFD252` `OFD304`(`DB/Trigger/OFD254_T01.SQL:1-10`) |
| `OFD561_T02` | `OFD561` | INSERT / UPDATE / DELETE | 與 `OFD109_T02` 同一個模子:把匯款備註同步成 `OFD661` 一筆,先刪後插(`DB/Trigger/OFD561_T02.SQL:21-40`) |
| `OFD562_T01` | `OFD562` | UPDATE OF `SEAL_PROCESS`, `SEAL_CD` | 印鑑狀態變了就對該受益人的每個 `SYSTEM_ID` 補一筆通知佇列 `TRPM101T1`,先刪後插(`DB/Trigger/OFD562_T01.SQL:28-44`) |
| `OFD562_T02` | `OFD562` | INSERT / UPDATE / DELETE | 同 `OFD561_T02` 的模子,但比對條件是 12 個欄位全部 `NVL(…,'X')` 對齊才刪(`DB/Trigger/OFD562_T02.SQL:21-35`) |
| `OFD607_T02` | `OFD607` | INSERT / UPDATE | 網銀密碼相關欄位異動時寫密碼異動記錄檔;帳號鎖定與密碼失效也算(`DB/Trigger/OFD607_T02.sql:17-34`) |
| `OFD607_T03` | `OFD607` | INSERT / UPDATE | 註冊類別 / 開戶進度 / 應備文件異動時寫前後值記錄檔(`DB/Trigger/OFD607_T03.sql:13-35`) |

三個一眼可見的模式:**五支是「先刪後插」的投影表維護**(`OFD109_T02` `OFD561_T02` `OFD562_T01` `OFD562_T02` `BMS001A_TSCDLOG`,改這類要同時改刪除條件與插入欄位,只改一邊會留孤兒列)· **兩支是純 Log**(`OFD607_T02` `OFD607_T03`,Log 表加欄位要同步這裡的 INSERT 清單)· **三支會擋交易**(`BMS001A_TDCC_BF_NO` `OFD002_T01` `OFD110_T01`,這是「存檔失敗但畫面沒說原因」的來源)。

### 6.2 改法

| 你要改什麼 | 注意 |
|---|---|
| 改 `UPDATE OF` 的欄位清單 | 這是觸發條件不是宣告。漏列一欄等於那一欄改了不會觸發,**完全靜默** |
| 加一張連動表 | `INSERTING` / `UPDATING` / `DELETING` 三個分支都要想過。13 支全部用這組布林,沒有人用 `WHEN` 子句分事件 |
| 加擋交易的檢核 | 照 §3.5 格式丟 `-20001`,訊息開頭要有 `#@@#` |
| 改 `:NEW` 賦值 | 只有 BEFORE 改得動 `:NEW`,**不要順手改成 AFTER**,`OFD113_T1` 那種指派會直接編不過 |

**不要在 trigger 裡查它自己掛的那張表。**`DB/Trigger/OFD109_T02.SQL:22` 在 row-level trigger 裡對自身表下 `SELECT NVL(MAX(AUTO_NUM),0)+1`,多筆同時 INSERT 會撞號,某些路徑還會丟 `ORA-04091`。**這是既有寫法,不要照抄到新 trigger。**

### 6.3 驗證

```
SELECT trigger_name, table_name, trigger_type, triggering_event, status
  FROM all_triggers WHERE owner = 'SW' AND trigger_name = UPPER('<觸發器名>');
```

`status` 要 `ENABLED`、`trigger_type` 要 `BEFORE EACH ROW`,再跑 §10 第 5、6 條。

## 7. 步驟四:改 View

### 7.1 現況:只有兩支,而且兩支長得完全不一樣

`FNDV01` 6 行、無 schema 前綴,被 `OFDM053` `OFDM111` 用,內容是基金清單 `UNION` 一列「所有基金」的假資料。`OFD068A_V02` 112 行、帶 `SW.`,被 `DSMM901` `DSMM903` `OFDI011` 用,是銷售機構六段 `UNION`(直銷 / 銀行總行 / 銀行分行 / 券商 / 投顧 / 投信 / 產壽險)。

`FNDV01` 全文(`DB/View/FNDV01.SQL:1-6`)——小到可以整支貼的那種:

```
CREATE OR REPLACE VIEW FNDV01 AS
SELECT FUND_ID ITEM, FUND_ID, FUND_SH_NM, FH_CD, REPORT_SEQ FROM OFD081
 UNION
SELECT '0', 'ALL FUNDS', '所有基金', OFD062.FH_CD, 0 AS REPORT_SEQ FROM OFD062;
```

`OFD068A_V02`(`DB/View/OFD068A_V02.SQL:1-11`)的呼叫端是 PO 手寫 SQL 直接 join,不走 SP:`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:340-344`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138`。

### 7.2 改法

| 你要改什麼 | 要跟著改的 |
|---|---|
| 只改 `WHERE` 或 join 條件 | 什麼都不用跟 |
| **加一個輸出欄** | 每一段 `UNION` 都要加同一欄(`OFD068A_V02` 有六段,漏一段就 `ORA-01789`);再看 §7.3 決定要不要動 typed DataSet |
| 改欄位順序 | `UNION` 靠位置對齊不靠名字,**改一段就要改六段** |
| 改欄位型別 | 各段型別要能隱含轉換,否則 `ORA-01790` |

最麻煩的是券商那一段(`DB/View/OFD068A_V02.SQL:36-79`):`ROW_NUMBER() OVER (PARTITION BY …)` + `WHERE RNO = 1` 的去重子查詢,裡面還硬寫了一筆常數資料列(`DB/View/OFD068A_V02.SQL:76`)。**加欄位時那個子查詢的兩層 SELECT 都要加。**

### 7.3 View 有 typed DataSet 的話一起改

`OFD068A_V02` 有一組共用 typed DataSet:`Dev/Common/Source/DataSource/DataEntity.DataSource/OFD_AgentCodeOriginalListModel.xsd:15-22`(DataTable 名字就叫 `OFD068A_V02`,但**只宣告 5 欄**,view 實際回 9 欄)與同構的 `Dev/Common/Source/DataSource/UIEntity.DataSource/OFD_AgentCodeOriginalListView.xsd`。

意思是 **view 多回的欄位會被靜默丟掉**(`LoadDataSet` 照欄名對應)。所以:

新欄位只給 PO 手寫 SQL 用就不動 xsd;要進這組 DataSet 就兩份 xsd 都加、欄名一致,並重生 Designer.cs(做法照 `runbooks/add-column.md`)。

### 7.4 驗證

```
SELECT column_name, data_type FROM all_tab_columns
 WHERE owner = 'SW' AND table_name = UPPER('<view名>') ORDER BY column_id;
```

回的欄位順序就是 `UNION` 第一段的順序,跟你的 xsd 對一次。

## 8. 步驟五:呼叫端(PO)要不要跟著改

### 8.1 判斷表

| 你在 SP / Function 改了什麼 | PO 要改嗎 | 改哪一行 |
|---|---|---|
| 內部邏輯、`WHERE`、計算式 | **不用** | — |
| 加 / 刪 IN 參數、改參數名 | 要 | `AddInParameter` 那一區,逐行對應;名字是第二個字串引數 |
| 改參數型別 | 要 | `AddInParameter` 的 `OracleDbType.*` |
| 加 / 刪 OUT 游標 | 要 | `AddOutParameter` **與** `LoadDataSet` 的表名清單,**兩處都要** |
| 改游標回傳的欄位 | 看情況 | 欄位要進畫面才要動 typed DataSet(§8.4) |
| 改 Trigger、改 View 的 `WHERE` | **不用** | Trigger 對 PO 完全透明 |

### 8.2 加 IN 參數:標準寫法

現況(`Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR051_PO.cs:66-82`)——一個參數一行,順序與 SP 宣告相同,值從 `model.Utility.Parameters` 取:

```
using (cmd = m_db.GetStoredProcCommand("S_OTA_OFDR051_GET"))
{   cmd.CommandTimeout = 0;
    m_db.AddInParameter(cmd, "iTYPE", OracleDbType.Varchar2, EVAStringHelper.GetParamValue(model, "TYPE"));
    ...
    m_db.AddOutParameter(cmd, "OutTB1", OracleDbType.RefCursor, int.MaxValue);
    m_db.LoadDataSet(cmd, model.DataEntity, tran, model.DataEntity.OFDR051_1.TableName);   }
```

改法:在最後一個 `AddInParameter` 之後、`AddOutParameter` 之前插一行 `m_db.AddInParameter(cmd, "i<NEW_PARAM>", OracleDbType.Varchar2, EVAStringHelper.GetParamValue(model, "<NEW_PARAM>"));`。三件事注意:**參數名字串要跟 SP 宣告一字不差**;**`GetParamValue` 的鍵是畫面查詢條件的名字不是 SP 參數名**(兩者常差一個 `i` 前綴,別複製貼上時連鍵一起改);批次類 PO 的值不從畫面來,直接傳區域變數,範本 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs:305-315`。

### 8.3 加游標:兩處都要改,而且是位置對應

**這是整節最容易漏的地方。**`AddOutParameter` 的**宣告順序**要對上 `LoadDataSet` 的**表名順序**——參數叫什麼名字不影響對應。範本(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:72-76`):

```
    m_db.AddOutParameter(cmd, "OutTB", OracleDbType.RefCursor, int.MaxValue);
    m_db.AddOutParameter(cmd, "OutTB2", OracleDbType.RefCursor, int.MaxValue);
    m_db.LoadDataSet(cmd, model.DataEntity, tran,
        model.DataEntity.TMKR003_1A.TableName,
        model.DataEntity.TMKR003_1B.TableName);
```

SP 裡把新游標加在 `OutTB1` 之後,PO 就要在對應位置補一行 `AddOutParameter`,**同時**在 `LoadDataSet` 的表名清單補一個表名。全庫命名分佈:`OutTB1` 57 · `OutTB2` 25 · `OutTB3` 9 · `OutTB4` 7 · `OutTB5` 5 · `OutTB6` 4 · 無數字的 `OutTB` 3,新加的照數字往後接。

### 8.4 改游標欄位:typed DataSet 要不要跟

`LoadDataSet` 是照**欄名**把游標倒進 DataTable 的:

SP 多回一欄(或欄名拼錯)而 xsd 沒有 → 那一欄被丟掉;SP 少回一欄而 xsd 有 → 那一欄全部空值。**兩種都不報錯。**所以「新欄位要顯示在報表上」就一定要改 `*Model.xsd` / `*View.xsd` 並重生 Designer.cs——步驟照 `runbooks/add-column.md`,本手冊不重複。

### 8.5 三個用位置取 OUT 值的呼叫點

全庫只有 3 處用 `cmd.Parameters[<數字>]` 取值,其他都用名字。**改到這三支的 SP 簽名時,參數順序一動就抓錯值,而且不報錯:**

| PO | 錨點 | 取的是 |
|---|---|---|
| `OFDM053` | `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM053_PO.cs:526` | `cmd.Parameters[1]`,即 `S_OTA_EC_PROGRESS` 的第 2 個參數(`DB/SP/S_OTA_EC_PROGRESS.SQL:1-3`) |
| `DSMM902` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs` | 同型寫法 |
| `OFDR452` | `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs` | 同型寫法 |

正確寫法是用名字取(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB553_PO.cs:118-122`):`cmd.Parameters["messge"].Value`。**本手冊不要求你順手把那 3 處改成具名取值**——那是獨立重構,不要夾帶在 SP 改動裡。但你改的 SP 若是那三支之一,**參數只能往後加,不能插隊**。

### 8.6 驗證

```
findstr /s /i /n "<SP名>" %ATLAS_ROOT%\Dev\*.cs   :: 全庫有幾個呼叫點?每一個都要對過
```

同一支 SP 被兩處呼叫是常態(例 `S_OTA_OFDB135_EXE` 在 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs:620` 與 `:693` 各一次)。**只改一處是最常見的漏改。**

## 9. 步驟六:部署與 rollback

### 9.1 部署順序

| 順序 | 動作 | 為什麼 |
|---|---|---|
| 1 | 用 `SW` 帳號跑物件腳本(整支 `CREATE OR REPLACE`) | Oracle 沒有「改一行」,只能整支取代 |
| 2 | 跑 §4.3 的三條確認 `VALID` | 語法錯了會建出 INVALID 物件而不是失敗 |
| 3 | 查相依物件有沒有被連坐弄成 INVALID | 改 Function 回傳型別、改 View 欄位都會連坐 |
| 4 | 再佈 PO 的 DLL(**簽名有變才需要**) | **DB 先、程式後**;反過來會在部署空窗期丟 `PLS-00306` |

第 3 步:`SELECT owner, object_name, object_type, status FROM all_objects WHERE owner = 'SW' AND status <> 'VALID';`,逐支 `ALTER PROCEDURE SW.<物件名> COMPILE;`。PO 的 DLL 佈到哪一台照 `architecture.md §8`——PO 屬伺服端,不用碰客戶端。

### 9.2 rollback:物件腳本沒有 `_rollback` 慣例

`DB/SP/` `DB/Function/` `DB/Trigger/` `DB/View/` **一支 rollback 檔都沒有**;只有 `DB/Table/` 的 158 支裡有 11 支檔名含 `rollback`。所以 PL/SQL 物件的 rollback 只有一條路:**部署前先把線上那一版撈出來存檔**(§2.2 的 `ALL_SOURCE` 查詢),要回退就把舊版全文再 `CREATE OR REPLACE` 一次。

### 9.3 `DB/Table/` 的票號腳本配對慣例(對照用)

| 特徵 | 實測 |
|---|---|
| 命名 | 動作開頭 115 支(`Alter_*` / `update_*` / `Insert*`)· 票號開頭 13 支 · 其他 30 支 |
| 副檔名 | `.sql` 156 · **`.slq` 2 支拼錯** |
| rollback | 11 支,命名 `<正向檔名>_rollback.sql` |

**但 rollback 不是逐檔配對。**最大的反例:`DB/Table/11706_InsertOFD115A_1.sql` 那組(`OFD115A` 4 支 + `OFD116A` 4 支 + `DB/Table/11706_InsertOFD907.sql` 1 支,**共 9 支正向**)只對應**一支**票號級的 `DB/Table/11706_rollback.sql:1-10`——內容是先對三張表各下一句 `select count(*)` 當 before/after 對照,再依 `CREATEDATE = '20221227'` 逐表 `delete` 回去,不分正向腳本。

規則:**rollback 以票號為單位寫一支**,檔名 `<票號>_rollback.sql`,內容先寫對照查詢再寫回復動作,編碼照 §3.3 用 UTF-8 BOM。

### 9.4 SP 沒有版本號,怎麼知道線上是哪一版

**沒有可靠答案,只有三個線索,而且前兩個都不可靠:**

| 線索 | 可信度 | 說明 |
|---|---|---|
| 檔內日期修改註解 | 低 | 只有 21 / 83 支 SP、5 / 23 支 Function、4 / 13 支 Trigger 有(範本 `DB/SP/S_OTA_OFDB553_EXE.sql:6-10`),人工維護漏寫沒人發現 |
| `ALL_OBJECTS.LAST_DDL_TIME` | 中 | 只說「最後被取代的時間」,不說內容是哪一版 |
| `ALL_SOURCE` 全文比對 | **高,唯一可靠** | 撈下來跟 repo 的檔逐行 diff |

上線前的標準動作:把 `ALL_SOURCE` 全文撈下來跟 `DB/SP/<物件名>.SQL` diff,**有差異就先停手**——代表線上有 repo 沒有的改動,直接覆蓋會弄丟它。

> **〔假設〕缺:版本歷史。** 本機不是 git working copy(`git` 在此目錄回「not a git repository」),所以「哪一支檔是最近加的」「線上是不是就是 repo 這一版」無法從本機判斷。§3.3 判定新檔用 UTF-8 BOM 的依據是**檔案內容裡的年份**而不是版本歷史。

## 10. 驗證清單

| # | 動作 | 查什麼 |
|---|---|---|
| 1 | 部署腳本 | 自己 `VALID`、`all_errors` 零筆,而且全 schema 沒有被連坐弄成 INVALID 的物件(§4.3 §9.1) |
| 2 | 簽名對照 | `all_arguments` 的名稱 / 模式 / 型別與 PO 的 `AddInParameter` 逐行對(§4.3) |
| 3 | 正常路徑 | 從畫面跑一次,資料筆數與改動前一致(除非你就是要改筆數) |
| 4 | 異常路徑 | 故意送空值 / 不存在的代碼,確認走到你寫的 `RAISE_APPLICATION_ERROR`,**畫面上看得到中文而不是問號**(這條同時驗編碼) |
| 5 | 改 Trigger 時 | INSERT / UPDATE / DELETE 各跑一次,§6.1 列的連動表逐一查有沒有跟著動 |
| 6 | 改 `UPDATE OF` 清單時 | 改**清單內**的欄位要觸發、改**清單外**的欄位不能觸發,兩邊都要驗 |
| 7 | 改 View 時 | `all_tab_columns` 的欄位順序與型別;再跑一次用到它的畫面(§7.1) |
| 8 | 改游標數量時 | 每個 DataTable 都要有資料(§8.3);少一個表就是對應錯位。全部呼叫點都要跑,§8.6 的 `findstr` 命中幾處就跑幾處 |

**第 4 與第 6 條最容易被跳過,而它們對應的正好是兩種靜默失敗。**

## 11. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **中文註解變亂碼 / 畫面錯誤訊息是問號** | 存檔編碼換掉了(cp950 檔用 UTF-8 存,或反過來) | §3.3 |
| **改了半天沒效果 / 另一支報表突然退版** | 檔名不等於真名,你改的檔跑出去蓋到別支物件(`DB/SP/S_OTA_OFDR601_GET.SQL` 的真名是 `S_OTA_OFDR051_GET`) | §2.3、§3.2 |
| **重寫的 SP 上線後少了一堆邏輯** | 物件不在 repo,憑空重寫覆蓋了線上十幾年的補丁 | §2.2 |
| **`PLS-00306` 參數個數或型別錯 / `PLS-00201` 識別碼未宣告** | SP 改了參數但 PO 沒跟,或參數名拼字不一致(含刻意保留的 `messge`) | §3.4、§8.2 |
| **報表某一區塊整個空白,其他區塊正常** | 游標與 `LoadDataSet` 表名的位置對應錯了 | §8.3 |
| **`ORA-24338` statement handle not executed** | `AddOutParameter` 的游標數比 SP 實際回的多 | §8.3 |
| **新欄位查得到但畫面沒有** | typed DataSet 沒有那一欄,`LoadDataSet` 靜默丟掉 | §8.4 |
| **OUT 值抓到別的參數的內容** | 該 PO 用 `cmd.Parameters[數字]` 位置取值,而你把參數插隊了 | §8.5 |
| **改了 Trigger,某些異動就是不觸發** | `UPDATE OF` 沒列到那一欄,**不報錯** | §6.2 |
| **`ORA-04091` mutating table** | Trigger 裡查自己掛的那張表 | §6.2 |
| **`ORA-01789` 欄數不正確 / `ORA-01790` 型態不符** | View 的 `UNION` 只加了一段的欄位,或各段型別對不上 | §7.2 |
| **物件建好了但一叫就 `ORA-06508`;或「我這台跑得動,測試環境不行」** | 物件 INVALID 被連坐弄壞,或 DB 佈了程式沒佈 | §9.1 |
| **要回退卻回不去** | 部署前沒把舊版從 `ALL_SOURCE` 撈下來存檔 | §9.2 |
| **同一支 SP 改完還是有地方壞掉** | 那支 SP 有多個呼叫點,只改了一處 | §8.6 |

**這張表裡有五條是靜默失敗**(欄位被丟掉、`UPDATE OF` 漏欄、位置取值抓錯、游標對應錯位、檔名真名不符),所以 §10 不能跳。

## 12. 附錄 A 本手冊引用的檔案清單

| 檔(同格多檔以 · 分隔) | 錨點 | 用在 |
|---|---|---|
| `DB/SP/S_OTA_OFDR051_GET.SQL` | `:1-13` `:16-23` `:97` `:206` | §3.2 §4.1 §5.2 |
| `DB/SP/S_OTA_OFDB553_EXE.sql` | `:1-4` `:2-3` `:6-10` | §2.3 §3.4 §4.1 §9.4 |
| `DB/SP/S_OTA_OFDB061_EXE.sql` · `DB/SP/S_OTA_OFDR601_GET.SQL` · `DB/SP/S_OTA_EC_PROGRESS.SQL` | `:1-6` · `:1` · `:1-3` | §2.3 §3.1 §3.2 §4.1 §8.5 |
| `DB/SP/S_OTA_OFDB600A_EXE.sql` · `DB/SP/S_OTA_OFDR050_GET.SQL` · `DB/Function/F_OTA_GetDefFeeRate.SQL` · `DB/Function/f_OTA_GetTradeNav.SQL` | `:3-5` · `:1` · `:1-12` `:11` · `:4` `:5` | §3.1 §5.1 §5.2 |
| `DB/Function/GETCLASSNAMECHT.SQL` · `DB/Function/F_OTA_GETFNBUSINESSDAY.SQL` · `DB/Function/TTP12ATMP_F1.SQL` · `DB/Function/F_OTA_GET_CRNCYAMTDEC.SQL` · `DB/Function/f_OTA_GetTradeNavLock.SQL` | `:1` · `:1` · `:1` · — · — | §3.1 §3.3 §3.4 §5.1 |
| `DB/Trigger/OFD002_T01.SQL` · `DB/Trigger/OFD109_T02.SQL` · `DB/Trigger/BMS001A_TDCC_BF_NO.SQL` · `DB/Trigger/BMS001A_TSCDLOG.SQL` · `DB/Trigger/OFD110_T01.SQL` · `DB/Trigger/OFD113_T1.sql` | `:31-43` `:40-43` `:42` · `:21-44` `:22` · `:230` · `:13-16` · `:31` · `:1-11` | §3.3 §3.5 §6.1 §6.2 |
| `DB/Trigger/OFD253_T01.sql` · `DB/Trigger/OFD254_T01.SQL` · `DB/Trigger/OFD561_T02.SQL` · `DB/Trigger/OFD562_T01.SQL` · `DB/Trigger/OFD562_T02.SQL` · `DB/Trigger/OFD607_T02.sql` · `DB/Trigger/OFD607_T03.sql` | `:1-9` · `:1-10` · `:21-40` · `:28-44` · `:21-35` · `:17-34` · `:13-35` | §6.1 |
| `DB/View/FNDV01.SQL` · `DB/View/OFD068A_V02.SQL` | `:1-6` · `:1-11` `:36-79` `:76` | §3.1 §7.1 §7.2 |
| `DB/Table/11706_rollback.sql` · `DB/Table/11706_InsertOFD115A_1.sql` · `DB/Table/11706_InsertOFD907.sql` · `DB/Table/9000010311_update.sql` · `DB/Table/Update_9000010694.sql` | `:1-10` · `:1` · `:1` · `:1` · `:1-3` | §3.3 §9.3 |
| `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs` · `Dev/ATLAS.OTA.Report/Source/PO/ReportPO.OTA/OFDR051_PO.cs` · `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs` · `Dev/ATLAS.OTA/Source/PO/PO.OTA/OFDM053_PO.cs` | `:58-68` · `:66-82` `:69-77` · `:62-77` `:72-76` · `:517-527` `:526` | §2.3 §4.2 §8.2 §8.3 §8.5 |
| `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB061_PO.cs` · `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB135_PO.cs` · `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB553_PO.cs` | `:305-315` · `:620` `:693` · `:112-122` `:118-122` | §3.4 §8.2 §8.5 §8.6 |
| `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs` · `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs` · `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs` · `Dev/ATLAS.OFD.Report/Source/PO/ReportPO.OFD/OFDR452_PO.cs` · `Dev/Common/Source/DataSource/DataEntity.DataSource/OFD_AgentCodeOriginalListModel.xsd` · `Dev/Common/Source/DataSource/UIEntity.DataSource/OFD_AgentCodeOriginalListView.xsd` | `:340-344` · `:138` · — · — · `:15-22` · — | §7.1 §7.3 §8.5 |

## 13. 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **Oracle 唯讀帳號(`ALL_SOURCE` / `ALL_ARGUMENTS` / `ALL_TYPE_ATTRS`)** | §2.2 §4.3 §5.2 §9.4 | 本手冊所有 `all_*` 查詢都未實測。補進來後:(1) 把 319 支只在 DB 的 SP 撈出來建清單 (2) 補齊 8 支 nested table function 的自訂型別定義 (3) 對 121 支腳本與線上全文做一次 diff,列出「線上被手改過」的清單 |
| **TFS / 版本歷史** | §3.3 §9.4 | 本機不是 git working copy,判斷「哪一支是新檔」只能靠檔案內容裡的年份。補上 changeset 日期後把 §3.3 的編碼結論改用實際加入時間佐證 |
| **PTPFBlock DLL** | §3.5 | `#@@#` 在 `Dev/Common/` 全部 `.cs` 搜不到解析程式碼,推論在框架 DLL 裡。補進來後補上它怎麼被剝掉、剝完顯示在哪 |
| **部署程序與 `SW` 帳號歸屬** | §9.1 | 目前只能寫「用 `SW` 帳號跑」,寫不出實際部署管道(SQL*Plus?DBA 代跑?)與審批流程 |
| **`DB/` 以外的 DB 物件版控** | §2 | 若客戶另有一套,§2 的判斷流程要多一層「先查那邊」 |
| **7 個物件不在掃描索引內** | 全篇 | `OFD609` `OFD661` `OFD662` `OFD255` `LOG030` `LOG049` `CTL000` 是 Trigger 原始碼實際寫到的表、`TRPM101T1` 是通知佇列表,但沒有任何 PO 用 `xTableMapping` 宣告過,所以不在 `atlas_index.json`,本手冊 meta 以 `refcheck-ignore` 略過。補上 DB 連線後改用 `ALL_TABLES` 驗證 |

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 48 · 圖 1 · 表格 24 · 程式錨點 56 · § 連結 113 · 引用檢查：畫面 8（缺 0） · Table 18（缺 0） · SP 3（缺 0） · Function 1（缺 0） · Trigger 13（缺 0） · View 2（缺 0） · 結果集 2（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
