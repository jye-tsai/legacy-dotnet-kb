ATLAS 知識庫 — 04-維護手冊-runbooks
加欄位、加畫面、加查詢、加批次、加報表、改四眼、改 SP、部署、建環境
本檔合併以下文件:runbooks/add-column.md、runbooks/add-screen.md、runbooks/add-query-screen.md、runbooks/add-batch.md、runbooks/add-report.md、runbooks/change-eva-flow.md、runbooks/change-sp-fn-trigger.md、runbooks/deploy.md、runbooks/build-env.md


============================================================
【文件】kb/runbooks/add-column.md
============================================================

# ATLAS 維護手冊 — 加欄位

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入(DB 連線 / PTPFBlock DLL)只能從結構推論,附錄 B 彙整。 ⚠ 標「**〔客戶特定〕**」的是本站台的值。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、 typed DataSet 看 `architecture.md §5`、部署邊界看 `architecture.md §8`。**不要整份讀**。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在一支既有的 **M(維護)畫面**上,替主表或明細表加一個欄位 |
| 範例畫面 | `CASM001`——六層齊全、主明細俱備、有四眼事件,是全庫最乾淨的樣本 |
| 範本欄 | `STAFF_POST`(職務,明細表 `CAS003A`,`xs:string`、`minOccurs="0"`)。每一步都先貼它的現況,新欄照抄 |
| 不適用 | 新建整張表 · 加欄到 `I`/`B`/`R` 畫面(見 §12.3)· 改既有欄位的型別或長度 · 改四眼欄位本身 |
| 前提工具 | Visual Studio(要用 xsd 設計工具)· **Devart dotConnect for Oracle**(重生 Designer.cs 用,見 `architecture.md §8.2`)· Oracle 客戶端 · PTPFBlock DLL · TFS workspace |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock` |
| 新欄佈位符 | 本文一律用 `<NEW_COL>` 代表你要加的欄位名 |

### 0.1 動工前先分辨:你要加的是哪一種欄位

**這是整本手冊的第一個岔路,走錯後面全錯。**xsd 裡的 element 不是每一個都對應到實體表的欄位:

| 種類 | 特徵 | 要不要 `ALTER TABLE` | 例 |
|---|---|---|---|
| **實體欄** | 直接存在主表或明細表裡,SQL 寫成 `<表>.<欄>` | **要** | `CAS003A.STAFF_POST`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:301`) |
| **衍生欄(join 進來的)** | SQL 從別張表 join 後 `AS` 出來 | **不要** | `COD009.EMP_NAME AS EMP_NAME`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:169`) |
| **說明欄** | 代碼欄的中文說明,多半由畫面即時填,不落地 | **不要** | `STAFF_TYPE_DESCRP`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:227`) |

判斷方法:先看你要的資料**有沒有要存進資料庫**。要存 → 實體欄,走完整八步。只是顯示別張表已有的值 → 衍生欄,**跳過 §2**,其餘照走。

### 0.2 八個步驟與該不該做

| # | 步驟 | 實體欄 | 衍生欄 | 節 |
|---|---|---|---|---|
| 1 | Oracle `ALTER TABLE` | ✔ | ✘ | §2 |
| 2 | DataEntity `Model.xsd` | ✔ | ✔ | §3 |
| 3 | UIEntity `View.xsd` | ✔ | ✔ | §4 |
| 4 | PO 的查詢 SQL | ✔ | ✔ | §5 |
| 5 | Control 轉換 | **不用改**(§6 說明為什麼) |  | §6 |
| 6 | FormProxy | **不用改** |  | §7 |
| 7 | UI 顯示 | ✔ | ✔ | §8 |
| 8 | 編譯與部署 | ✔ | ✔ | §9 |

**§6 與 §7 不用改是有原始碼佐證的結論,不是省略。**理由分別在該節。

## 1. 改動點總覽

```text
[圖] 加欄位的八個步驟:資料庫、兩份 xsd、Designer 重生、PO 讀取端、UI 白名單、重編部署;Control 與 FormProxy 不用改
圖中文字:① 資料庫(先做) / Oracle ALTER TABLE / 衍生欄跳過此步 / ② ③ Schema 真相——兩邊欄名必須一致 / CASM001Model.xsd / DataEntity · 加 xs:element / CASM001View.xsd / UIEntity · 貼同一行 / Designer.cs 重生 / MSDataSetGenerator / *VDB.cs / 不用動 / ④ PO —— 只改讀取端 / BuildMasterSQLString / 主表 · 兩條分支都要加 / BuildDetailSQLString / 明細 · 一條 / INSERT / UPDATE / 自動,不用改 / IsDataChanged / 不比業務欄 / ⑤ ⑥ 不用改(有原始碼佐證) / Control 轉換 / 照欄名泛型複製 / FormProxy / 收送整包型別 / ⚠ 只加一邊 xsd / 靜默失敗,不報錯 / ⚠ NULL 變空值 / 空字串 / 0 / 1900 / ⑦ ⑧ UI 與部署 / UI 白名單陣列 / 不加就看不到 / 重編:下→上 / Entity→PO→Ctl→Pxy→UI / 伺服端五層 / IIS ATLAS_TAService / UIEntity 兩端都要 / 客戶端 + 伺服端
```

*圖:圖 1 改動點總覽。橘色實框=這一步要改;灰虛框=不用改(理由見對應節);橘色虛框=兩個靜默失敗的陷阱。由上往下做,反過來每一步都編不過。*

三件事先記住:

1. **順序是由下往上。**先 DB、再 xsd、再 PO、最後 UI。反過來做,中間每一步都編不過。

2. **Model 與 View 兩邊都要加,而且欄名必須一模一樣。**只加一邊不會報錯,資料會**靜默消失**(§6.2)。

3. **加完 xsd 一定要重生 Designer.cs。**不重生的話編譯會過,但執行期取不到那個欄位。

## 2. 步驟一:Oracle 加欄位

### 2.1 現況

`CAS003A` 的欄位定義**不在 repo 裡**。`DB/Table/` 底下 158 支是票號變更腳本不是 DDL,且只涵蓋 52 張表;`CAS003A` 沒有 `CREATE TABLE` 腳本(見 `architecture.md 附錄 B.5`)。

你能拿到的最接近定義,是 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:21` 的這一行:

```
<xs:element name="STAFF_POST" msdata:Caption="職務" ... type="xs:string" minOccurs="0" />
```

**它給你欄名、中文名、大概的型別、可不可空——但沒有長度。**

### 2.2 改法

```
ALTER TABLE CAS003A ADD (<NEW_COL> VARCHAR2(<長度>));
COMMENT ON COLUMN CAS003A.<NEW_COL> IS '<中文名>';
```

三條規則:

- **一律加成可空**(不寫 `NOT NULL`)。既有資料列在這一刻沒有值,加 `NOT NULL` 而不給 `DEFAULT` 會直接失敗;給了 `DEFAULT` 又會把「沒填」與「填了預設值」混在一起。

- **不要動 `DATAFLAG`。**它是 `msdata:ReadOnly="true"` 的 `xs:base64Binary` row-version 欄(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:50`),由資料庫維護,四眼引擎用它判斷資料有沒有被別人改過(§5.4)。

- **不要動四眼欄位。**`STATUS` / `CREATEID` / `CREATEDATE` / `UPDATEID` / `UPDATEDATE` / `ENTRYID` / `ENTRYDATE` / `VERIFYID` / `VERIFYDATE` / `APPROVEID` / `APPROVEDATE` / `REJECTID` / `REJECTDATE` / `DATAID` / `DATAFLAG` 這 15 個由四眼引擎維護,加業務欄跟它們無關(`architecture.md §3.5`)。

- **先 DB 再程式。**程式端的 INSERT / UPDATE 欄位清單是**執行期跟資料庫要 schema** 決定的(§5.2),資料庫還沒有這個欄位,程式先上線就會炸。

### 2.3 腳本放哪、怎麼存

放 `DB/Table/`,檔名照現有票號慣例(`<票號>_<動作><表名>.sql`)。**編碼**:該資料夾 cp950 與 UTF-8 BOM 混用,新檔用 **UTF-8 BOM**;不要用無 BOM 的 UTF-8 存,也不要用 `utf-8` 硬讀既有檔(`architecture.md 附錄 B.5`)。

同時準備 rollback:`ALTER TABLE CAS003A DROP COLUMN <NEW_COL>;`。

### 2.4 驗證

```
SELECT column_name, data_type, data_length, nullable
  FROM all_tab_columns
 WHERE table_name = 'CAS003A' AND column_name = '<NEW_COL>';
```

回一列且 `nullable = 'Y'` 才算過。

> **〔假設〕缺:DB 連線。**本節的長度、精度、是否建索引無法從 repo 判斷。目前只能從 xsd 的 `type` 反推大類(`xs:string` → `VARCHAR2`、`xs:decimal` → `NUMBER`、`xs:dateTime` → `DATE`)。拿到唯讀帳號後,用 `ALL_TAB_COLUMNS` 對照相鄰欄位的實際長度再定。

## 3. 步驟二:DataEntity(`Model.xsd`)

### 3.1 現況

`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` 共 142 行,結構三層(`architecture.md §5.1`):

```
CASM001Model            ← DataSet 根,= 畫面代號
├─ CAS003A              ← element = 實體表名(明細)   :15-54
└─ CRM003A              ← element = 實體表名(主檔)   :56-128
```

主表 `CRM003A` 與明細 `CAS003A` 合計 107 欄(`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen CASM001`)。

範本欄原文(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:21`):

```
<xs:element name="STAFF_POST" msdata:Caption="職務"
            msprop:Generator_ColumnVarNameInTable="columnSTAFF_POST"
            msprop:Generator_ColumnPropNameInRow="STAFF_POST"
            msprop:Generator_ColumnPropNameInTable="STAFF_POSTColumn"
            msprop:Generator_UserColumnName="STAFF_POST"
            type="xs:string" minOccurs="0" />
```

### 3.2 改法

在同一張表的 `<xs:sequence>` 內、**四眼欄位區塊之前**插一行(四眼欄位從 `:37` 的 `STATUS` 開始,業務欄位排在它前面):

```
<xs:element name="<NEW_COL>" msdata:Caption="<中文名>"
            msprop:Generator_ColumnVarNameInTable="column<NEW_COL>"
            msprop:Generator_ColumnPropNameInRow="<NEW_COL>"
            msprop:Generator_ColumnPropNameInTable="<NEW_COL>Column"
            msprop:Generator_UserColumnName="<NEW_COL>"
            type="xs:string" minOccurs="0" />
```

四個 `msprop:Generator_*` 不是裝飾,它們決定產出的 C# 成員名稱。照範本套字即可,**不要自己改命名規則**。

| 屬性 | 填法 |
|---|---|
| `msdata:Caption` | **中文名**。這是全 repo 唯一的欄位中文名來源(`architecture.md §5.1`),不要留空,也不要自己翻譯既有欄位 |
| `type` | `xs:string` / `xs:decimal` / `xs:dateTime` / `xs:int`。**金額一律 `xs:decimal`,不可用 `xs:double`** |
| `minOccurs="0"` | 對應可空。§2.2 規定新欄一律可空,所以這個一定要寫 |

> `STATUS` 的 `msdata:Caption` 在本檔寫成「資料識別碼」(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:37`),語意上應該是「狀態」。既有錯誤,不在本次改動範圍,但引用中文名時要知道。

### 3.3 重生 `Designer.cs`

`CASM001Model.Designer.cs` **5,375 行,由工具產生,手改必被覆寫**。證據在 csproj:

- `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:83-86` — `Designer.cs` 標 `<AutoGen>True</AutoGen>` 且 `<DependentUpon>CASM001Model.xsd</DependentUpon>`

- `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:153-154` — xsd 掛 `<Generator>MSDataSetGenerator</Generator>`、`<LastGenOutput>CASM001Model.Designer.cs</LastGenOutput>`

**路線 A(建議,VS 內)**:方案總管選 `CASM001Model.xsd` → 右鍵 → **執行自訂工具**。存檔通常也會觸發,但不保證,所以手動執行一次。

**路線 B(命令列)**:

```
"%VS%\Common7\IDE\TextTransform.exe"
```

不適用——`MSDataSetGenerator` 是 VS 的自訂工具,沒有對應的獨立 exe。`xsd.exe /d /l:CS` 產出的類別結構與 `MSDataSetGenerator` **不同**(缺 `msprop:Generator_*` 指定的成員名),**不要用它替代**,會編不過。

> **〔假設〕缺:PTPFBlock DLL。**本機沒有框架 DLL 所以編不起來(`architecture.md 附錄 C.1`),上述兩條路線都未實測。路線 A 是 `MSDataSetGenerator` 的標準用法,路線 B 的排除理由來自兩個工具產出的成員命名差異。

### 3.4 `ModelVDB.cs` 不用動

`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001ModelVDB.cs` 只有 45 行,是包住 DataSet 的薄殼,**沒有任何欄位級程式碼**(`architecture.md §5.3`)。加欄位不用碰它。**H1 成立。**

### 3.5 驗證

重生後 `CASM001Model.Designer.cs` 應多出:`<NEW_COL>Column` 屬性、`CAS003ARow.<NEW_COL>` 屬性、`Is<NEW_COL>Null()` / `Set<NEW_COL>Null()` 兩個方法。用 grep 確認,不要整份讀(5,375 行):

```
grep -c "<NEW_COL>" "%ATLAS_ROOT%\Dev\ATLAS.CAS\Source\Entity\DataEntity.CAS\CASM001Model.Designer.cs"
```

數字為 0 = 沒重生成功,回去做 §3.3。

## 4. 步驟三:UIEntity(`View.xsd`)

### 4.1 現況

`CASM001` 的 Model 與 View **完全同構**:同 2 表、逐欄名稱 / 型別 / Caption / `minOccurs` 全同,兩份 xsd 都 142 行(`architecture.md §5.4`)。範本欄在 `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd:96`,與 Model 那行**一字不差**。

全庫 1,072 對 xsd 裡 89.7% 完全同構(`architecture.md §5.4`),`CASM001` 屬於這一類。

### 4.2 改法

把 §3.2 那段**原封不動**貼進 `CASM001View.xsd` 的同一張表內。欄名、型別、`minOccurs` 必須與 Model 完全一致——理由在 §6.2。

然後重生:`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj:86` 與 `:149` 是 Model 那邊完全對應的設定,做法同 §3.3。

`CASM001ViewVDB.cs`(42 行)同樣不用動。

### 4.3 兩邊不同構怎麼辦

如果你改的畫面 Model 與 View 本來就不同構(全庫 5.6% 表集合不同、2.8% 同表但欄位不同),**先確認新欄要不要跨層傳**:

| 情形 | 做法 |
|---|---|
| 要存 DB 也要顯示 | Model 與 View 都加,欄名相同 |
| 只顯示不存(畫面計算欄) | **只加 View**。這正是那 30 對不同構的多數樣態——View 多 `*_NM` / `*_DESCRP` / `*_RATE0` 這類欄 |
| 只存不顯示 | 只加 Model |

### 4.4 驗證

```
grep -c "<NEW_COL>" "%ATLAS_ROOT%\Dev\ATLAS.CAS\Source\Entity\UIEntity.CAS\CASM001View.Designer.cs"
```

同 §3.5,0 就是沒重生。

## 5. 步驟四:PO

### 5.1 現況:查詢 SQL 是手寫字串

`CASM001_PO` 繼承 `BaseEVADaoPO`,建構子宣告主明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:46-47`):

```
this.MasterTable = new xTableMapping("CRM003A", "CRM003A");//主檔資料
this.DetailTable.Add(new xTableMapping("CAS003A", "CAS003A"));//明細資料
```

查詢 SQL 由兩支方法各自串字串:

| 方法 | 錨點 | 管哪張表 |
|---|---|---|
| `BuildMasterSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:164` | 主表 `CRM003A` |
| `BuildDetailSQLString` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:290` | 明細 `CAS003A` |

範本欄在明細那支裡的原文(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:301`):

```
                                    ,CAS003A.STAFF_POST
```

### 5.2 關鍵:寫入端自動、讀取端不自動

**這一節是整本手冊最容易漏的地方。**

- **INSERT / UPDATE 的欄位清單是自動的。**執行期由 `TableHelper.GetTableSchema` 對資料庫下 `SELECT * FROM <table> WHERE 1=2` 取回 schema,再據此列出全部欄位(`architecture.md §4.2`)。所以你**不需要**手動維護寫入欄位清單。

- **SELECT 的欄位清單是手寫的。**就是上面那兩支 `Build*SQLString`。**你不加,查詢就撈不回來。**

漏改的症狀因此非常specific:**存得進去、查不回來**。新增一筆後畫面看不到那個欄位的值,但資料庫裡有。

> 計劃書原本假設(H3)欄位清單來自傳給 `Add()` / `Update()` 的 `string[] datacolumn` 陣列。**H3 不成立**:那個參數只有已成死碼的 `TA_PO` 在用(`architecture.md §3.1`),現行的 `BaseEVADaoPO` 路徑不看它。**不要去找 `datacolumn` 陣列加欄位。**

### 5.3 改法

在對應那支 `Build*SQLString` 的欄位清單裡,**照範本欄的縮排**加一行:

```
                                    ,CAS003A.<NEW_COL>
```

位置放在業務欄位區塊的末尾、四眼欄位之前。加在 `STAFF_POST` 隔壁最省事。

`BuildMasterSQLString` 還有第二個參數 `isToDoString`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:164`),同一支方法產兩種 SQL(一般查詢與待辦查詢)。**確認兩條分支的欄位清單都加到**,只加一邊會變成「維護畫面看得到、待辦清單看不到」。

### 5.4 `IsDataChanged` 不會比到新欄位

計劃書假設(H4)`IsDataChanged` 比對 xsd 全欄位減四眼欄位,所以新欄自動納入。**H4 不成立。**

實情是它產的 SQL 只比 `DataFlag` 這一個 row-version 欄加上主鍵,**業務欄位一個都不比**(`architecture.md §3.6`)。結論:

- 加欄位**不需要**、也不可能讓 `IsDataChanged` 自動比到。

- 但**新表如果忘了建 `DataFlag`,一叫就 `ORA-00904`**。加欄位不會踩到這個,建新表會。

### 5.5 `BeforeAdd` 要不要給預設值

`CASM001_PO` 掛了 `BeforeAdd`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77`)與七個 `After*` 事件(`:569-625`)。如果新欄位需要「新增時自動帶值」,寫在 `CASM001_PO_BeforeAdd` 裡。

**不需要預設值就不要動這支。**它是共用事件,改壞影響整支畫面的新增流程。

### 5.6 驗證

```
grep -n "<NEW_COL>" "%ATLAS_ROOT%\Dev\ATLAS.CAS\Source\PO\PO.CAS\CASM001_PO.cs"
```

明細欄應命中 1 次(`BuildDetailSQLString`);主表欄若兩條分支都加,應命中 2 次。

## 6. 步驟五:Control —— 不用改

### 6.1 為什麼不用改

`CASM001_Ctl` 的兩對轉換方法(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:79` 與 `:105`)**沒有逐欄列名**,它們呼叫的是表級泛型複製:

```
TransferVDBHelper.TransferTable(view.UIView.CRM003A, model.DataEntity.CRM003A, base.TransferEVAColumn);
TransferVDBHelper.TransferDetailTable(view.UIView.CAS003A, model.DataEntity.CAS003A, base.TransferEVAColumn);
```

`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:86` 與 `:89`

而 `TransferVDBHelper` **有原始碼**,核心是照欄名逐欄複製(`Dev/Common/Source/Utility/TA.ServerUtility/TransferVDBHelper.cs:263-267`):

```
foreach (System.Data.DataColumn column in target.Table.Columns)
{
    if (source.Table.Columns.Contains(column.ColumnName) == false) continue;
    target[column.ColumnName] = GetRowValue(source, column);
}
```

**只要 Model 與 View 的欄名一致,新欄位自動被複製。H5 成立,而且比原假設更強——不是「同構欄由基底處理」,是完全按欄名比對,Control 根本不知道有哪些欄。**

### 6.2 代價:只加一邊會靜默失敗

`if (source.Table.Columns.Contains(column.ColumnName) == false) continue;` 這一行沒有記錄、沒有例外。所以:

| 你做了什麼 | 會發生什麼 | 看起來像什麼 |
|---|---|---|
| 只加 Model,沒加 View | 畫面永遠拿不到值 | 「畫面上這欄一直空的」 |
| 只加 View,沒加 Model | 使用者填的值到不了 DB | 「存了沒反應,也不報錯」 |
| 兩邊欄名拼錯一個字 | 同上,而且更難找 | 同上 |

**沒有任何錯誤訊息。**這是本手冊 §11 的第一條。

### 6.3 另一個代價:新的可空欄位拿不到 NULL

`TransferDataRow` 在複製時會把 `DBNull` 轉成對應型別的「空值」(`Dev/Common/Source/Utility/TA.ServerUtility/TransferVDBHelper.cs:226-243`):

| 型別 | NULL 會變成 |
|---|---|
| `string` | `string.Empty` |
| `decimal` / `int` / `double` | `0` |
| `DateTime` | `1900/01/01` |

字串另外會被 `Trim()`(`Dev/Common/Source/Utility/TA.ServerUtility/TransferVDBHelper.cs:247`)。

**後果:你加的可空欄位,在畫面端永遠分不出「沒填」與「填了空字串 / 0 / 1900-01-01」。**如果業務上需要區分,不能靠 NULL,要另外加一個旗標欄,或改用特定的哨兵值並在 §5.3 的 SQL 裡處理。**動工前先確認業務要不要區分。**

### 6.4 什麼時候才要改 Control

只有兩種情況:

1. Model 與 View 的**欄名不同**(例:Model 叫 `EMP_NO1`、View 叫 `EMP_NO`)——要在 `CustomTransferOracleModelToView` / `CustomTransferViewToOracleModel` 裡手動搬。

2. 新欄需要**轉換**(格式化、代碼轉中文)才能顯示。

`CASM001` 兩者皆非,所以不用改。

## 7. 步驟六:FormProxy —— 不用改

`CASM001_Pxy`(`Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:15`,164 行)繼承 `Basic_Pxy`(PTPFBlock,無原始碼)。它的方法簽名收送的是 `BasicViewVDB` 這種**整包型別**,不是欄位。加欄位不改型別,所以簽名不變。

**但它與部署有關**:Remoting 邊界在 UI 與 FormProxy 之間(`architecture.md §8.1`),`UIEntity` 是跨邊界傳輸的型別,所以 §4 改完的 `UIEntity.CAS.dll` **兩端都要更新**。詳見 §9。

## 8. 步驟七:UI

### 8.1 現況:明細走網格,顯示欄位由白名單決定

`CASM001` 的明細直接把 DataTable 綁給 Infragistics 網格(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:264`):

```
this.ugrdCASM001.DataSource = ((CASM001ViewVDB)this.ProcessVDB).UIView.CAS003A;
```

**全 repo 的 `CASM001.Designer.cs` 裡沒有任何 `DataBindings`**——計劃書假設(H6)UI 用 `DataBindings` 綁欄名,**H6 不成立**。

要顯示哪些欄、順序如何,由一個字串陣列決定(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:577`):

```
UltraGridInitialHelper.SetupUltraGridShowColumns(e, new string[] {
    "STAFF_NAME", "STAFF_POST", "STAFF_POSITION", "SEX", "MGR_NAME", ... });
```

這支 helper **先把所有欄位藏起來,再依陣列逐一顯示**(`Dev/Common/Source/Utility/TA.ClientUtility/UltraGridInitialHelper.cs:24-36`):

```
foreach (UltraGridColumn col in band.Columns) { col.Hidden = true; }
foreach (string col in columns)
{
    if (band.Columns.Exists(col))
    {
        band.Columns[col].Hidden = false;
        band.Columns[col].Header.VisiblePosition = i;
        i++;
    }
}
```

**所以新欄位預設是隱藏的。**而且 `if (band.Columns.Exists(col))` 表示陣列裡打錯的欄名會被靜默忽略。

### 8.2 改法(明細欄)

在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:577` 那個陣列裡,把 `"<NEW_COL>"` 加到你要的**顯示位置**——陣列順序就是欄位左右順序。

需要特殊輸入方式的話,照範本欄在下一行設 Style(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:584`):

```
this.ugrdCASM001.DisplayLayout.Bands[0].Columns["STAFF_POST"].Style
    = Infragistics.Win.UltraWinGrid.ColumnStyle.EditButton;
```

要接代碼下拉,參考 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:143` 的 `GridSearch` 用法與 `:195-197` 的 `utility.SetDataSource(..., new GetDropDownDataSrc("<代碼類別>"))`。代碼類別編號查 `TA.MappingCode`(`architecture.md §7.2`)。

### 8.3 改法(主表欄)

主表不走網格,是強型別列 + 具名控件(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:45`):

```
CASM001View.CRM003ARow MasterRow = ((CASM001ViewVDB)this.ProcessVDB).UIView.CRM003A[0];
```

重生 Designer 後,`CRM003ARow` 會多出 `.<NEW_COL>` 屬性。你要:

1. 在 `CASM001.Designer.cs` 加控件(照相鄰欄位的控件型別與命名慣例)。

2. 在讀取處把值放進控件、在存檔處把控件的值寫回 `MasterRow.<NEW_COL>`,參考 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:282` 起那段的寫法。

> `CASM001.Designer.cs` 是 WinForms 設計工具產的,**用 VS 的設計檢視拉控件,不要手打**。它與 §3.3 的 `Model.Designer.cs` 不同——後者由 xsd 重生、絕對不能手改;前者可以透過設計工具改。

### 8.4 驗證

```
grep -n "<NEW_COL>" "%ATLAS_ROOT%\Dev\ATLAS.CAS\Source\UI\UI.CAS\CASM001.cs"
```

明細欄至少命中 1 次(白名單陣列)。命中 0 = 欄位存在但**畫面上看不到**。

## 9. 步驟八:編譯與部署

### 9.1 重編順序

由下往上,缺一不可(`architecture.md §2`):

```
1. DataEntity.CAS  ← 先重生 Designer.cs 再編
2. UIEntity.CAS    ← 同上
3. PO.CAS
4. Control.CAS
5. FormProxy.CAS
6. UI.CAS
```

### 9.2 部署到哪一台

Remoting 邊界在 UI 與 FormProxy 之間(`architecture.md §8.1`),所以:

| 組件 | 客戶端 | 伺服端 |
|---|---|---|
| `UI.CAS.dll` | ✔ |  |
| `UIEntity.CAS.dll` | ✔ | ✔ |
| `FormProxy.CAS.dll` · `Control.CAS.dll` · `PO.CAS.dll` · `DataEntity.CAS.dll` |  | ✔ |

`UIEntity` 兩端都要,因為它是跨 Remoting 序列化的型別,兩端版本不一致會在反序列化時出錯(此為推論,見 `architecture.md §8.1`)。

**只佈一端是最常見的部署錯誤**,症狀是「我這台好了,別人還是舊的」或反序列化例外。

### 9.3 ⚠ 檢查你動到的組件在不在 DLL 覆寫名單裡

`architecture.md 附錄 C.5` 列了 25 個「repo 有原始碼、卻被 143 筆 `<HintPath>` 綁成 PTPFBlock 預編 DLL」的組件。**改了這類組件,重編不會傳到下游**,必須把新 DLL 複製進 `%PTPF%`。

以 `CASM001` 的六層而言,`DataEntity.CAS` / `UIEntity.CAS` / `PO.CAS` / `Control.CAS` / `FormProxy.CAS` / `UI.CAS` **都不在那份名單裡**,所以本手冊的標準流程不需要動 `%PTPF%`。

**但你改的若是別的模組就要先查。**特別是 `EC` 與 `OTA` 兩個模組,它們的六層有多支在名單內(例:`Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj` 以 DLL 方式參考隔壁的 `DataEntity.OTA`)。查法:在該層的 `.csproj` 裡搜 `PTPFBlock`,搜得到就是綁 DLL。

### 9.4 Crystal 報表要不要改

如果有報表要印這個欄位,`.rpt` 要另外改——不在本手冊範圍,見 `runbooks/add-report.md`(尚未撰寫)。查哪些報表用到這張表:

```
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --table CAS003A
```

> **〔假設〕缺:PTPFBlock DLL。**本機沒有框架 DLL,整個 §9 未實測(`architecture.md 附錄 C.1`)。重編順序來自六個 csproj 的 `ProjectReference` 相依,部署分工來自 Remoting 邊界的結論。

## 10. 驗證清單

改完跑一輪四眼,每一步查資料庫確認新欄位有跟著走(狀態語意見 `architecture.md §3`):

| # | 動作 | 查什麼 |
|---|---|---|
| 1 | 新增一筆,填入新欄位,送出 | `SELECT <NEW_COL>, STATUS FROM CAS003A WHERE ...` — 值有進去,`STATUS` 進 `Entry*` |
| 2 | 重開畫面查詢同一筆 | 新欄位**顯示得出來**(這一步驗的是 §5.3 的 SELECT 有加到) |
| 3 | 換一個帳號覆核 | `STATUS` 進 `Verify*`,`VERIFYID` 有值,新欄位值不變 |
| 4 | 主管核准 | `STATUS` 進 `Approve*`,新欄位值不變 |
| 5 | 修改該欄位再送一次 | 值有更新;`UPDATEID` / `UPDATEDATE` 有換 |
| 6 | 退回後重送 | `REJECTID` 有值;新欄位值不受影響 |
| 7 | 待辦清單 | 若改的是主表欄且 `BuildMasterSQLString` 有兩條分支,確認待辦查詢也看得到(§5.3) |

**第 2 步是最容易失敗的一步**,因為 §5.2 的「寫入自動、讀取手寫」不對稱。

## 11. 常見錯誤與症狀

依「症狀 → 病因」排,現場最快找到自己那一條:

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **存得進去,查不回來** | `Build*SQLString` 的 SELECT 沒加欄位 | §5.3 |
| **畫面完全看不到這一欄** | UI 白名單陣列沒加 | §8.2 |
| **畫面上一直是空的,DB 也沒值,但不報錯** | 只加了 Model 沒加 View(或欄名不一致) | §4.2、§6.2 |
| **使用者填了存不進去,也不報錯** | 只加了 View 沒加 Model | §3.2、§6.2 |
| **編譯過,執行期取不到欄位 / 屬性不存在** | xsd 改了但沒重生 `Designer.cs` | §3.3、§4.2 |
| **重生後編譯一堆錯,成員名怪怪的** | 用 `xsd.exe` 代替 `MSDataSetGenerator` | §3.3 路線 B 的說明 |
| **`ORA-00904` invalid identifier** | 程式先上線、DB 還沒 `ALTER TABLE` | §2.2 的「先 DB 再程式」 |
| **`ORA-01008` not all variables bound** | DB 有欄位但 typed DataSet 沒有 | §3.2 |
| **既有資料列違反 NOT NULL** | 加欄位時加了 `NOT NULL` | §2.2 |
| **新欄位永遠不是 NULL,是空字串 / 0 / 1900-01-01** | `TransferDataRow` 的 NULL 轉空值,不是 bug | §6.3——業務要區分就別靠 NULL |
| **維護畫面看得到,待辦清單看不到** | `BuildMasterSQLString` 只加了一條分支 | §5.3 |
| **DB 腳本打開變亂碼** | `DB/Table/` cp950 與 UTF-8 BOM 混用,用錯編碼存 | §2.3 |
| **自己這台好了,別人還是舊的** | `UIEntity` 只佈了一端 | §9.2 |
| **改了共用層卻沒效果** | 該組件在 `architecture.md 附錄 C.5` 的 DLL 覆寫名單裡 | §9.3 |

**這張表裡有六條是靜默失敗**(不報錯、不寫 log),所以 §10 的驗證清單不能跳。

## 12. 明細表加欄位的差異

### 12.1 與主表的差別很小

`CASM001` 主明細都走同一套機制,差別只有三處:

| 面向 | 主表 `CRM003A` | 明細 `CAS003A` |
|---|---|---|
| PO 的 SQL | `BuildMasterSQLString`,**兩條分支**(一般 / 待辦) | `BuildDetailSQLString`,一條 |
| Control 轉換 | `TransferVDBHelper.TransferTable` | `TransferVDBHelper.TransferDetailTable` |
| UI | 具名控件 + 強型別列(§8.3) | 網格 + 白名單陣列(§8.2) |

### 12.2 `TransferDetailTable` 多做的事

它會分別處理新增 / 修改 / 刪除三種 `RowState`(`Dev/Common/Source/Utility/TA.ServerUtility/TransferVDBHelper.cs:159`),因為明細是多筆、要保留每一列的狀態。但**逐欄複製的核心仍是同一支 `TransferDataRow`**,所以 §6.1 到 §6.3 的結論對明細完全適用。

### 12.3 不適用的畫面型別

| 型別 | 為什麼不適用 |
|---|---|
| `I` 查詢 | PO 繞過四眼基底、自建連線(`architecture.md §6`),沒有本手冊的六層路徑 |
| `B` 批次 | 多數沒有 `Model.xsd` / `View.xsd`(`architecture.md §6`),邏輯常在版控外的 SP 裡 |
| `R` 報表 | 七層不是六層,多一個 `Report.<模組>` 專案裝 `.rpt`(`architecture.md §6`) |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | `:15` `:21` `:37` `:50` `:51` `:56` | §3.1 §3.2 §2.2 §0.1 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd` | `:96` | §4.1 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj` | `:83-86` `:153-154` | §3.3 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj` | `:86` `:149` | §4.2 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001ModelVDB.cs` | `:1` | §3.4 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001ViewVDB.cs` | `:1` | §4.2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs` | `:46-47` `:77` `:164` `:169` `:290` `:301` `:569-625` | §5 |
| `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs` | `:79` `:86` `:89` `:105` `:127` `:136` | §6.1 §6.4 |
| `Dev/Common/Source/Utility/TA.ServerUtility/TransferVDBHelper.cs` | `:159` `:208` `:226-243` `:247` `:263-267` | §6.1 §6.3 §12.2 |
| `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs` | `:15` | §7 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs` | `:45` `:143` `:195-197` `:227` `:264` `:282` `:577` `:584` | §8 §0.1 |
| `Dev/Common/Source/Utility/TA.ClientUtility/UltraGridInitialHelper.cs` | `:18` `:24-36` | §8.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **Oracle 唯讀帳號 / `ALL_TAB_COLUMNS`** | §2.2 §2.4 | 欄位長度與精度目前只能從 xsd 的 `type` 反推大類;補進來後可給「照相鄰欄位長度」的具體規則,並補主鍵 / 索引的判斷 |
| **PTPFBlock DLL** | §3.3 §9 | 重生 Designer.cs 的兩條路線與整個編譯部署段都未實測;補進來後跑一次完整流程,把實際指令與輸出貼進去 |
| **部署機的 `main.exe.config`** | §9.2 | 客戶端的 Remoting 設定不在版控(`architecture.md §8.1.1`),目前無法寫出「佈到哪個目錄」 |
| **選單 / 權限表** | §0 | 無法寫「這支畫面叫什麼中文名、誰有權限測」 |

## 附錄 C 計劃書假設的驗證結果

計劃書 §3 列了 H1–H8 八條待驗假設。逐條開檔驗證後:

| # | 假設 | 結論 | 依據 |
|---|---|---|---|
| H1 | `*ModelVDB.cs` 只包 DataSet,加欄不用動 | **成立** | 45 行薄殼無欄位級程式碼,§3.4 |
| H2 | Designer.cs 由 `MSDataSetGenerator` 產,手改必被覆寫 | **成立** | csproj `<AutoGen>` + `<Generator>`,§3.3;View 那邊同樣設定 |
| H3 | INSERT/UPDATE 欄位清單來自 SQL 字串**加上** `string[] datacolumn` | **不成立** | 清單來自執行期跟 DB 要的 schema;`datacolumn` 只有死碼 `TA_PO` 在用。§5.2 |
| H4 | `IsDataChanged` 比 xsd 全欄減四眼欄,新欄自動納入 | **不成立** | 只比 `DataFlag` + 主鍵,業務欄一個都不比。§5.4 |
| H5 | Ctl 的 `CustomTransfer*` 只處理不同構欄,同構由基底泛型複製 | **成立,且更強** | `TransferDataRow` 完全按欄名逐欄複製,Ctl 不知道有哪些欄。§6.1 |
| H6 | UI 綁定用 `DataBindings` 綁 View 欄名 | **不成立** | Designer 裡沒有任何 `DataBindings`;明細走網格 + 白名單陣列,主表走具名控件。§8.1 §8.3 |
| H7 | Remoting 邊界在 UI ↔ FormProxy,Control/PO/DataEntity 是伺服端 | **成立** | 三項證據,見 `architecture.md §8.1` |
| H8 | 四眼欄位不在 xsd,由基底統一處理 | **不成立** | 15 個四眼 / 系統欄位都寫在 xsd 裡(`CASM001Model.xsd:37` 起);由引擎**賦值**但確實**存在於** DataSet。§2.2 |

**四條不成立。**其中 H3、H4、H6 若照原假設寫進手冊,會讓人去改不存在的東西、或漏掉真正要改的地方,所以本手冊在對應章節都直接寫了正確做法並標明推翻。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 53 · 圖 1 · 表格 16 · 程式錨點 47 · § 連結 87 · 引用檢查：畫面 1（缺 0） · Table 2（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/add-screen.md
============================================================

# ATLAS 維護手冊 — 從零加一支 M 維護畫面

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 ⚠ 標「**〔假設〕缺:輸入**」的是拿不到輸入(DB 連線 / PTPFBlock DLL / 選單表)只能推論的部分,附錄 B 彙整;標「**〔客戶特定〕**」的是本站台的值。

> 前提知識在 `architecture.md`:六層與重編順序 `architecture.md §2`、typed DataSet `architecture.md §5`、畫面型別 `architecture.md §6`、部署邊界 `architecture.md §8`、DLL 覆寫陷阱 `architecture.md 附錄 C.5`。**不要整份讀**。加欄位的細節不重複,一律引用 `add-column.md`。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在既有模組裡**從零建一支新的 M(維護)畫面**:主檔 + 明細、走四眼、六層全建 |
| 主要範本 | `CASM006`(CAS 模組最後一支 M,「上一支是怎麼建的」最新樣本) |
| 對照範本 | `CASM001`(`add-column.md` 的範例)。兩支對照才分得出「樣板」與「畫面特有」 |
| 不適用 | 建新模組(要另開六個專案)· 建 `I`/`B`/`R` 畫面(`architecture.md §6`)· 既有畫面加欄位(`add-column.md`) |
| 前提工具 | Visual Studio(xsd 與 WinForms 兩個設計工具都要用)· **Devart dotConnect for Oracle** · Oracle 客戶端 · PTPFBlock DLL · TFS workspace |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 佈位符 | `<NEW>` = 新代號(CAS 模組的下一支會是 `CASM007`);`<T_MASTER>` / `<T_DETAIL>` = 主檔 / 明細表名 |

### 0.1 九個步驟,以及哪幾步要動腦

**六層裡兩層是逐字樣板、兩層是半樣板,只有 UI 真的要自己做。**這是本手冊最重要的一句話。

| # | 步驟 | 動什麼 | 樣板程度 | 憑什麼這樣說 | 節 |
|---|---|---|---|---|---|
| 1 | 決定代號與表 | 不寫程式 | 自己想 | — | §2 |
| 2 | DataEntity `<NEW>Model.xsd` + VDB | 新增 2 檔 + 3 附檔 | 半樣板 | 骨架與四眼 15 欄照抄,業務欄自己列 | §3 |
| 3 | UIEntity `<NEW>View.xsd` + VDB | 新增 2 檔 + 3 附檔 | **抄 Model** | 兩份 xsd 222 行只有 2 行不同(§4.1) | §4 |
| 4 | PO `<NEW>_PO.cs` | 新增 1 檔 | 半樣板 | 建構子與三事件照抄,兩支 SELECT 自己寫 | §5 |
| 5 | Control `<NEW>_Ctl.cs` | 新增 1 檔 | **逐字樣板** | `CASM003_Ctl` 與 `CASM006_Ctl` 換名後逐字相同(§6.1) | §6 |
| 6 | FormProxy `<NEW>_Pxy.cs` | 新增 1 檔 | **逐字樣板** | 全檔 21 行,只有一個 `InitializeControl()` | §7 |
| 7 | UI `<NEW>.cs` + Designer + resx | 新增 3 檔 | **自己做** | 版面、控件、驗證全是這支特有 | §8 |
| 8 | 註冊選單與權限 | DB(不在 repo) | 拿不到輸入 | 見 §9 | §9 |
| 9 | 六個 csproj + 編譯部署 | 改 6 檔 | 樣板 | — | §10 |

工序上先把樣板五分鐘刷完(§3 §4 §6 §7),時間留給 §5 的 SQL 與 §8 的版面。

## 1. 建立點總覽(圖)

```text
[圖] 從零建一支 M 畫面的九個步驟:代號與表、兩份 xsd、PO、Control、FormProxy、UI、選單、六個 csproj 與重編順序
圖中文字:① 決定代號與表(還不寫程式) / 步驟一 代號 <NEW> / 同模組同型別 max+1,避開 9xx / 主檔 / 明細表 / 表要先存在;借別模組的表合法 / 型別碼選 M / 四眼 + 主明細才叫 M / ⚠ 選單表不在 repo / §9 只能給驗法 / ② ③ Entity —— 整支照抄,只換名字 / 步驟二 Model.xsd / DataEntity · 三層 + 主鍵 / 步驟三 View.xsd / UIEntity · Model 的副本 / Designer.cs 重生 / MSDataSetGenerator / *VDB.cs 薄殼 / 40 行照抄 / ④ PO —— 全篇唯一要自己想的一層 / 步驟四 <NEW>_PO.cs / 三事件樣板 + 手寫 SELECT / I<NEW>_PO 空介面 / 照抄兩行 / xTableMapping / 照抄,換表名 / INSERT / UPDATE / 框架自動,不寫 / ⑤ ⑥ Control 與 FormProxy —— 100% 樣板 / 步驟五 <NEW>_Ctl.cs / 與 CASM003_Ctl 逐字相同 / 步驟六 <NEW>_Pxy.cs / 21 行,只覆寫 InitializeControl / 加值方法才另外寫 / 每支 try / catch 包起來 / ⚠ 名字打錯 / 跨層靠字串綁,靜默失敗 / ⑦ ⑧ ⑨ UI、選單、編譯部署 / 步驟七 <NEW>.cs / 唯一要拉版面的一層 / 步驟八 選單 / 權限 / 〔假設〕缺:選單表 / 步驟九 六個 csproj / xsd 要掛三段 / 重編 下 → 上 / Entity→PO→Ctl→Pxy→UI
```

*圖:圖 1 建立點總覽。橘色實框=這一步要自己想或自己拉;灰虛框=照抄樣板換名字;橘色虛框=拿不到輸入或會靜默失敗的地方。由上往下做,反過來每一步都編不過。*

三件事先記住:

1. **順序由下往上。**Entity → PO → Control → FormProxy → UI。不是慣例,是 `ProjectReference` 強制的(`architecture.md §2.4`)。

2. **跨層全靠字串與命名對上,編譯器幫不了你。**PO 的表名字串、Ctl 的欄名比對、UI 的網格白名單都是字串。打錯不紅字,靜默失敗。

3. **檔案建好不等於加進專案。**xsd 在 csproj 裡要掛**三段**(§3.5),漏一段就是「編得過、執行期沒有那個型別」。

## 2. 步驟一:決定代號與確認資料表

### 2.1 現況:代號怎麼編

代號 7 碼三段:模組 2–4 碼 + 型別碼(`B`/`I`/`M`/`R`)+ 三位流水號 + 可選後綴(`architecture.md §2.1`)。 CAS 現有六支 M:`CASM001`–`CASM006`,**沒有跳號**。但不能推論全庫都不跳號——用索引實測 15 個有 M 畫面的模組:

**只有 3 個不跳號**(`CAS` 1–6、`CLS` 1–2、`CRM` 1–4),**12 個有跳號**(`OFD` 最大 913 卻只有 185 支、`COD` 最大 36 只有 8 支)。

另有一個 **9xx 高位保留段**:全庫 **44** 支落在該段、分佈於 **9** 個模組;其中 **M 型 16 支**(`BMSM924`–`BMSM927`、`DSMM901` `DSMM902` `DSMM903` `DSMM906`、`OFDM907` `OFDM913` `OFDM913A` `OFDM931A` `OFDM931B`、`OTAM901`、`TMKM901`、`TRPM901`),跨 6 個模組。**取號時不能撞進去。**

### 2.2 改法:取號規則

```
<NEW> = <模組碼> + M + zfill(3, 排除 9xx 後的同模組同型別最大流水號 + 1)
```

CAS 排除 9xx 後最大是 `006`,所以下一支是 `CASM007`。查法 `py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --module CAS`,看「畫面清冊」的 M 列。三條規則:

- **不要補空號。**跳號的 12 個模組沒有任何補號跡象;補進去等於重用一個可能還躺在選單 / 權限 / 報表對照裡的代號。

- **不要用 9xx。**保留段,見 §2.1。

- **模組碼由業務歸屬決定,不是由你把檔案放哪決定。**`ATLAS.EC` 裝的是 `OFD` 與 `IPJ`、`ATLAS.COD` 還藏了 `CTL`(`architecture.md §2.6`)。

### 2.3 資料表:要先存在,而且不必跟模組同名

建表原則(可空、編碼、腳本放哪)走 `add-column.md §2`,這裡只講新畫面特有的三件:

| # | 規則 | 依據 |
|---|---|---|
| 1 | **主檔一定要有,明細可以沒有** | `CASM004` / `CASM005` 只宣告 `MasterTable`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:39-42`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:36-39`) |
| 2 | **表名不必跟畫面同模組** | `CASM006` 用 `DSM001A` / `DSM002A`,兩張表同時被 `DSMM001` 用(`atlas_scan.py --module CAS` 的實體表段)。合法,但改表會同時影響兩支畫面 |
| 3 | **主檔與明細都要有四眼 15 欄** | 少一個,`BaseEVADaoPO` 組出的 SQL 就 `ORA-00904`;清單見 `add-column.md §2.2` |

驗法:

```
SELECT table_name, column_name FROM all_tab_columns WHERE table_name IN ('<T_MASTER>', '<T_DETAIL>')
   AND column_name IN ('STATUS','CREATEID','CREATEDATE','UPDATEID','UPDATEDATE','ENTRYID','ENTRYDATE',
       'VERIFYID','VERIFYDATE','APPROVEID','APPROVEDATE','REJECTID','REJECTDATE','DATAID','DATAFLAG');
```

兩張表各回 15 列才算過。

> **〔假設〕缺:DB 連線。**上面的 SQL 未實測。15 欄的清單來自 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:115-132` 的 `AllEVAColumnsForSelect`,它逐欄串出來的就是這 15 個。

## 3. 步驟二:DataEntity —— 建 `Model.xsd` 與加進 csproj

### 3.1 現況:xsd 的三層結構

`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd` 共 222 行(`architecture.md §5.1`):

```
CASM006Model  ← DataSet 根 = 代號 + Model :12 │ DSM001A ← 主檔表名 :15-112
xs:unique × 2 ← 每張表一組主鍵 :211-221    │ DSM002A ← 明細表名 :113-208
```

要照抄的骨架四處:`:2`(`id` + `targetNamespace` + 兩個 xmlns,三處代號全換)、`:3-11`(`xs:annotation` 內的 `DataSource` 區塊,**一字不改**)、`:12`(根 element + `Generator_DataSetName` / `Generator_UserDSName`)、`:15` 與 `:113`(表 element)。

### 3.2 改法:表節點的 10 個 `msprop`

表 element(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:15`)的 10 個屬性全是 `<表名>` 套字:

```
<xs:element name="DSM001A" msprop:Generator_TableClassName="DSM001ADataTable" msprop:Generator_TableVarName="tableDSM001A"
  msprop:Generator_TablePropName="DSM001A" msprop:Generator_RowClassName="DSM001ARow" msprop:Generator_UserTableName="DSM001A"
  msprop:Generator_RowChangedName="DSM001ARowChanged" msprop:Generator_RowChangingName="DSM001ARowChanging"
  msprop:Generator_RowDeletedName="DSM001ARowDeleted" msprop:Generator_RowDeletingName="DSM001ARowDeleting"
  msprop:Generator_RowEvHandlerName="DSM001ARowChangeEventHandler" msprop:Generator_RowEvArgName="DSM001ARowChangeEvent">
```

**照抄換表名,不要自己發明命名**——這些屬性決定 `Designer.cs` 產出的成員名,PO 與 UI 都直接吃這些名字。

### 3.3 改法:欄位節點的兩種寫法

| 寫法 | 什麼時候用 | 原文錨點 |
|---|---|---|
| 內含 `xs:simpleType` + `maxLength` | 字串欄,而且知道長度 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:25-31`(`QUO_YEAR`,長度 4) |
| 單行 `type="…"` | 非字串欄,或字串不限長 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:46`(`QUO_MGR_TOT`,decimal) |

`CASM001Model.xsd` 全部用單行(`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd:21`)。**混用是既有現實不是錯**;新畫面跟 `CASM006` 一致(字串帶 `maxLength`),因為那是 repo 內唯一看得到欄位長度的地方。

四個 `msprop:Generator_Column*` 的填法同 `add-column.md §3.2`。三條新畫面特有的規則:

- **`msdata:Caption` 只給業務欄。**`:52` 的 `STATUS` 沒有 Caption、`:25` 的 `QUO_YEAR` 有。

- **金額 / 數量一律 `type="xs:decimal" default="0"`**(`:46-51` 六個 `*_TOT`),不要用 `xs:double`。

- **四眼 15 欄整段複製**,從 `:52` 的 `STATUS` 到 `:205` 的 `DATAFLAG`(含 `msdata:ReadOnly="true"`),一個字都不要改。

### 3.4 改法:主鍵 —— 新畫面才會踩到

`add-column.md` 沒這段,因為加欄不動主鍵。`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:211-221` 每張表各一組:

```
<xs:unique name="Constraint1" msdata:PrimaryKey="true">
  <xs:selector xpath=".//mstns:DSM001A" /> <xs:field xpath="mstns:QUO_YEAR" /> <xs:field xpath="mstns:EMP_NO" />
</xs:unique>
<xs:unique name="DSM002A_Constraint1" msdata:ConstraintName="Constraint1" msdata:PrimaryKey="true">
  <xs:selector xpath=".//mstns:DSM002A" /> <xs:field xpath="mstns:QUO_YEAR" /> <xs:field xpath="mstns:QUO_YYMM" /> <xs:field xpath="mstns:EMP_NO" />
</xs:unique>
```

命名規則兩支範本一致:第一組 `name="Constraint1"`,第二組 `name="<表名>_Constraint1"` 且多一個 `msdata:ConstraintName="Constraint1"`。 `CASM001Model.xsd:133-141` 同一套,但**第一組給的是明細**——所以**順序不是規則,`xpath` 指到哪張表才是**。主鍵欄位填實體表的真實主鍵;明細通常是「主檔主鍵 + 自己的鍵」(`DSM002A` = `QUO_YEAR` + `EMP_NO` + `QUO_YYMM`)。

### 3.5 改法:csproj 要加的三段

**最容易漏、漏了最難查。**`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj` 裡跟一支 xsd 有關的有三段(`:116-121` 與 `:203-213`):

```
<Compile Include="CASM006Model.Designer.cs">                       
  <AutoGen>True</AutoGen><DesignTime>True</DesignTime><DependentUpon>CASM006Model.xsd</DependentUpon>
</Compile>
<Compile Include="CASM006ModelVDB.cs" />
<None Include="CASM006Model.xsd">                                  
  <SubType>Designer</SubType><Generator>MSDataSetGenerator</Generator><LastGenOutput>CASM006Model.Designer.cs</LastGenOutput>
</None>
<None Include="CASM006Model.xsc"><DependentUpon>CASM006Model.xsd</DependentUpon></None>   
<None Include="CASM006Model.xss"><DependentUpon>CASM006Model.xsd</DependentUpon></None>
```

`.xsc` / `.xss` 是 VS 的 DataSet 設計工具附檔(`.xsc` 內容只有一個空的 `<TableUISettings />`),**由 VS 自己產,不用手寫**,但要確認有進 csproj。

### 3.6 `<NEW>ModelVDB.cs`:40 行照抄,但有兩處絕對不能抄錯

`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006ModelVDB.cs` 全檔 40 行:繼承 `BasicModelVDB`(無原始碼,從呼叫端反推)、一個私有 typed DataSet 欄位、一個屬性、一個 `Dispose()`(`:9-19`)。與 ViewVDB 的差別只有三處:

|  | `ModelVDB` | `ViewVDB` |
|---|---|---|
| `[Serializable()]` | **沒有** | **有**(`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM006ViewVDB.cs:9`) |
| `RemotingFormat` | 不設 | `SerializationFormat.Binary`(`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM006ViewVDB.cs:19`) |
| 屬性名 | `DataEntity` | `UIView` |

理由是 Remoting 邊界:只有 ViewVDB 會過線(`architecture.md §8.1`)。**不要把 `[Serializable()]` 加到 ModelVDB,也不要從 ViewVDB 拿掉。**

### 3.7 驗證

重生 Designer.cs(做法同 `add-column.md §3.3`:方案總管對 xsd 右鍵「執行自訂工具」),然後:

```
grep -c "class DSM001ARow" "%ATLAS_ROOT%\Dev\ATLAS.CAS\Source\Entity\DataEntity.CAS\CASM006Model.Designer.cs"
```

回 0 = 沒重生。`CASM006Model.Designer.cs` 實測 166 KB;新畫面產出若小於 10 KB,是 §3.2 的 `msprop` 漏了。

## 4. 步驟三:UIEntity —— 建 `View.xsd`

### 4.1 現況:View 是 Model 的副本,而且可以驗

把 `CASM006Model.xsd` 與 `CASM006View.xsd` 各自的代號代換成同一字串後逐行比對,**222 行只有 2 行不同**:`:15` 與 `:113` 兩個表 element 的 `msprop` **屬性順序**不同,值一字不差。欄位、型別、`maxLength`、`xs:unique` 全同。這比 `architecture.md §5.4` 的「89.7% 同構」更強:**這一組是純副本**。

### 4.2 改法

複製 `<NEW>Model.xsd` 成 `<NEW>View.xsd`,把 `<NEW>Model` 換成 `<NEW>View`,一共三處:`:2` 的 `id` 與兩個 namespace、`:12` 的根 element `name`、`:12` 的 `Generator_DataSetName` 與 `Generator_UserDSName`。

**表名、欄名、型別一律不動**——理由在 `add-column.md §6.2`:`TransferVDBHelper` 按欄名逐欄比對,對不上就靜默丟掉。

csproj 三段照 §3.5,把檔換成 `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj`,**行號一模一樣**(`:116-121` 與 `:203-213`)——兩個 csproj 是對稱維護的。`<NEW>ViewVDB.cs` 照抄 `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM006ViewVDB.cs` 全 41 行,注意 §3.6 那三處。

### 4.3 什麼時候 View 才該跟 Model 不一樣

只有一種:**畫面要顯示但不落地的欄**。但 `CASM006` 示範了更常用的另一條路:`DEPT_NO` 與 `EMP_NAME` 是從 `COD009` join 進來的衍生欄(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113-115`),它**兩邊都加**。

**規則**:衍生欄 Model 與 View **都加**(代價只是 Model 多幾個不落地的欄),`CASM006` 與 `CASM001` 都是這樣;只有真的進不了 SELECT 的畫面計算欄才「只加 View」,而那樣 Control 得手寫搬運(`add-column.md §6.4`)。

### 4.4 驗證

`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen CASM006` —— 新畫面跑同一支:「六層」六行都要有路徑、沒有「—(缺)」,「表」要列出主檔與明細。掃描器讀的就是 xsd 與 PO,這一步同時驗了 §3 §4 §5。

## 5. 步驟四:PO —— 建構子、主明細宣告、事件訂閱、查詢 SQL

### 5.1 現況:骨架四件

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs` 全檔 277 行:

| 件 | 錨點 | 內容 |
|---|---|---|
| 空介面 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:18-20` | `public interface ICASM006_PO : IEvaDataAccess { }` —— 真的是空的 |
| 類別宣告 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:23-24` | `[PODbType(DbServerType.Oracle)]` + `: BaseEVADaoPO, ICASM006_PO` |
| 建構子 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:27-34` | 三個事件 + 主明細宣告 |
| 兩支 SQL | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:105-215` 與 `:224-273` | `BuildMasterSQLString` / `BuildDetailSQLString` |

`BaseEVADaoPO` 有原始碼:`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17`。

### 5.2 主明細宣告

```
this.MasterTable = new xTableMapping("DSM001A", "DSM001A");//主檔資料
this.DetailTable.Add(new xTableMapping("DSM002A", "DSM002A"));//明細資料
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33`。三條規則:

- **兩個參數給同一字串。**第一個是實體表名、第二個是 VDB 裡 DataTable 的名字(`architecture.md §4.1`);與 §3.2 的 xsd 表名共三處要一致,對不上就查不到資料。

- **用 `xTableMapping`(無原始碼,從呼叫端反推),不要寫成 `TableMapping`。**後者是舊世代、搭配 `PrepareSQLEventArgs`(`architecture.md §4.1`)。

- **沒有明細就不宣告 `DetailTable`**(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs:42`)。

**還有第四條:全庫有 6 支用「兩段式」寫法,`grep "MasterTable = new"` 找不到它們。**

```
xTableMapping tp = new xTableMapping("OFD087A", "OFDM087");
this.MasterTable = tp;
```

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:48-49`。語意與上面那種**完全等價**,只是先 `new` 到區域變數再指派。剝掉 `//` 註解後掃全庫 1,022 個 `*_PO.cs` / `*OracleDao.cs`,兩段式共 **6 處**,分兩型:

| 型 | 支數 | 代號與錨點 |
|---|---|---|
| 單主檔 `this.MasterTable = tp;` | **1** | `OFDM087`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs:48-49`) |
| 多筆主檔 `this.MasterTable.Add(tp);` | **5** | `OFDM381`(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM381_PO.cs:16-17`)· `OFDB041`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB041_PO.cs:32-33`)· `OFDB562`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB562_PO.cs:18-19`)· `OFDB563`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB563_PO.cs:18-19`)· `OFDB564`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB564_PO.cs:17-18`) |

對照組:直接式 `MasterTable = new x?TableMapping` 有 253 個檔、`MasterTable.Add(new x?TableMapping` 有 67 個檔。

(`OFDM381` 在本文用雙反引號寫,因為它確實存在於 repo、但目前的 `atlas_index.json` 還沒收錄它 —— 那是掃描器待 refresh 的已知缺口,不是這支畫面不存在。)

**對維護的意義有兩條:**

1. **查「這支畫面的主檔是哪張表」不能只 grep `MasterTable = new`。**六支會漏,`OFDM381` 與 `OFDB041` 都是實際在跑的畫面。正確查法用 §5.8 的一行指令。

2. **新畫面寫直接式**(上面那兩行)。兩段式沒有任何好處,只是讓後面每一個 grep 的人多踩一次。

### 5.3 事件:三個必要,其餘可選

把 CAS 六支 M 的建構子並排,結論很乾淨:

| 事件 | `CASM001` | `CASM002` | `CASM003` | `CASM004` | `CASM005` | `CASM006` | 判定 |
|---|---|---|---|---|---|---|---|
| `BeforeSelect` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **必要** |
| `BeforeGetMaintainData` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **必要** |
| `BeforeGetToDoData` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | **必要** |
| `BeforeAdd` | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | 可選:新增要自動帶值時(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:77`) |
| `After*` 八個 | ✔ | ✔ | ✘ | ✘ | ✘ | ✘ | 可選:四眼狀態轉換後要連動別張表(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:49-58`) |

錨點:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:29-31`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs:30-32`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:36-38`,對照 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:42-45`。**新畫面一律先只掛三個。**

三支實作也是樣板(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:46-94`,合計 49 行),分流固定:

| 事件 | 主檔 | 明細 |
|---|---|---|
| `BeforeSelect`(`:46-58`) | `BuildMasterSQLString(model, false)` | 不處理 |
| `BeforeGetMaintainData`(`:60-80`) | `BuildMasterSQLString(model, false)` | `BuildDetailSQLString(model, args.TableName)` |
| `BeforeGetToDoData`(`:82-94`) | `BuildMasterSQLString(model, true)` | 不處理 |

分流一律拿 `args.TableName` 比 `this.MasterTable.dbTableName`(`architecture.md §4.1`)。

### 5.4 查詢 SQL:全篇唯一要自己寫的東西

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:111-127` 的骨架:

```
strSQL += @"SELECT DSM001A.DATAID ,DSM001A.QUO_YEAR ,NVL(COD009.DEPT_NO,' ') AS DEPT_NO ,DSM001A.QUO_MIL_A_TOT"
         + xEVAStringHelper.AllEVAColumnsForSelect("DSM001A")
         + @"FROM DSM001A JOIN COD009 ON COD009.EMP_NO = DSM001A.EMP_NO WHERE 1=1 ";
```

五條規則:

1. **第一欄一律 `DATAID`**(兩支範本都是:`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:170` 與 `:298`)。

2. **四眼 15 欄不要手打**,呼叫 `AllEVAColumnsForSelect("<表名>")`(`Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:115-132`;類別實名是 `EVAStringHelper`,`Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:20`。PO 端看到的 `xEVAStringHelper` 是 DLL 裡的同名替身,**無原始碼,從呼叫端反推**)。

3. **`WHERE 1=1` 必要**,後面的條件一律 `AND` 串上去。

4. **`isToDoString` 分支不要動。**`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:203-206` 的 `xTableHelper.AppendToDoString(...)` 上面就寫著「ToDo 此段不可修改」。

5. **查詢條件從 `model.Utility.Parameters` 取**,格式固定 `Rows.Contains` → `Rows.Find` → 比 `Row.Opeartor` → 串字串(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:132-140`)。參數名要跟 UI 端 `AddParametersRow` 的字串一致(§8.4),**又一個靠字串對上的跨層綁定**。

`BuildDetailSQLString` 同一套,外面多一層 `if (strTableName == this.DetailTable[0].dbTableName)`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:229`);多張明細就多幾個 `if`。

### 5.5 兩處現存缺陷,不要照抄

| 缺陷 | 錨點 | 為什麼 |
|---|---|---|
| **查詢值字串串接** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:138` | 值沒參數化。異動類走參數化、查詢類沒有(`architecture.md §4.3`);照抄等於複製一個注入面 |
| **部門白名單寫死在 SQL** | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` | `AND COD009.DEPT_NO IN('G3','GA',…)` 是〔客戶特定〕授權規則寫進查詢字串,換站要改程式。新畫面的權限走 §9 |

### 5.6 驗證

`grep -c "AllEVAColumnsForSelect"` 該 PO:主檔一次、每張明細一次。回 0 = 四眼欄位沒進 SELECT,四眼流程整組拿不到狀態。

### 5.7 PO 基底白名單:一律 `BaseEVADaoPO` / `BaseMultiRowEVADaoPO`

**新畫面只准繼承這兩支。繼承 `BasicEVAPO` 或 `MultiRowEVAPO` 的畫面,連查詢都會 `NullReferenceException`。**

證據鏈在 `architecture.md §3.1.1`,四個條件同時成立且彼此獨立:

| # | 事實 | 錨點 |
|---|---|---|
| 1 | `dbTA` / `dbPTPF` **宣告就是 `= null`** | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:26` 與 `:27` |
| 2 | 建構子裡建立連線的那四行**整段被註解**,只剩一個沒人用的區域變數 | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:165-173`,被註解的是 `:169-172`(`architecture.md §3.1.1` 記為 `:164-172`,含註解標頭) |
| 3 | 基底 `Add()` 第一件事就是 `cn = dbTA.CreateConnection();` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:187` |
| 4 | 全庫活子類沒有一支自己賦值 `dbTA`,其中 73 支連 `Add` / `Update` / `Delete` 都不覆寫 | 實掃 `Dev/` 全部 `*_PO.cs` 剝註解後比對(`architecture.md §3.1.1`) |

**而且不只存檔會爆。**`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:11` 繼承 `BasicEVAPO`, 它的查詢方法第一行就是 `DbConnection cn = dbTA.CreateConnection();`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:30`) —— **按查詢就 NRE**。21 篇模組篇累計已經數到 20 支以上這種死畫面。

> 這是讀碼結論,**沒有實跑過**(本機缺 PTPFBlock,`architecture.md 附錄 C.1`)。要推翻它得證明 `dbTA` 在別處被賦值 —— 全庫剝註解後掃過,沒有。

| 基底 | 全庫子類數 | 新畫面 | 接手既有畫面 |
|---|---|---|---|
| `BaseEVADaoPO` | 271 | **✔ 主明細單筆用這個** | 正常 |
| `BaseMultiRowEVADaoPO` | 61 | **✔ 多筆主檔用這個** | 正常 |
| `BasicEVAPO` | 66(另 46 處已被註解) | **✘** | **先確認它到底有沒有在跑,再談修** |
| `MultiRowEVAPO` | 11(另 5 處已被註解) | **✘** | 同上 |
| `TA_PO` / `Basic4EyesPO` / `MultiRow4EyesPO` | 0 | **✘** | 整支是死碼(`architecture.md §3.1`) |

#### ⚠ 判斷基底一定先剝 `//` 註解

`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:28` 留著一行

```
//public class OFDM125A_PO : BasicEVAPO
[PODbType(DbServerType.Oracle)]
public class OFDM125A_PO : BaseEVADaoPO, IOFDM125A_PO
```

—— 第 `:28` 行是註解掉的舊宣告,第 `:30` 行才是現行的。**直接 `grep "class .*_PO *:"` 會把它誤判成死畫面。** 掃描器也踩過同一顆(`architecture.md §6.3` 的 `CASI001` 誤標主檔 `OFD701`,原因就是正規式不剝註解)。

一行可跑的正確查法(把 `OFDM125A` 換成要查的代號):

```
py -V:3.12 -c "import sys,glob;sys.path.insert(0,'/docs/tools');from atlas_scan import read_text;S='OFDM125A';[print(f.split(chr(92))[-1],'->',[l.strip() for l in read_text(f)[0].split(chr(10)) if ' class ' in l and ':' in l and not l.strip().startswith('//')][0]) for f in glob.glob('/Dev/**/'+S+'_PO.cs',recursive=True) if 'obj' not in f]"
```

輸出:`OFDM125A_PO.cs -> public class OFDM125A_PO : BaseEVADaoPO, IOFDM125A_PO`。用 `atlas_scan.read_text` 而不是 `open()`,因為 `Dev/` 有 cp950 檔(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM087_PO.cs` 就是)。

### 5.8 主明細三處同名:一行指令查

§3.2 的 xsd 表名、§5.2 的 `xTableMapping` 兩個參數,**三處要一致**。人工比對會漏,而且 §5.2 說過 grep 抓不到兩段式寫法。下面這一行兩種寫法都吃(把 `CASM006` 換成要查的代號):

```
py -V:3.12 -c "import sys,re,glob;sys.path.insert(0,'/docs/tools');from atlas_scan import read_text;S='CASM006';g=lambda p:[f for f in glob.glob('/Dev/**/'+p,recursive=True) if 'obj' not in f];po=''.join(l for f in g(S+'_PO.cs') for l in read_text(f)[0].split(chr(10)) if not l.strip().startswith('//'));m=re.findall(r'x?TableMapping[(] *\"([^\"]+)\" *, *\"([^\"]+)\"',po);x=set(re.findall(r'name=\"(\w+)\"[^>]*Generator_TableClassName',''.join(read_text(f)[0] for f in g(S+'Model.xsd'))));v={b for a,b in m};print('PO  :',m);print('xsd :',sorted(x));print('缺 xsd 表:',sorted(v-x) or 'OK');print('實體表(自己比 SQL):',sorted({a for a,b in m}))"
```

四支實測輸出:

| 代號 | `PO` 的 `(實體表, vdb 表)` | `xsd` 的表 element | 判定 |
|---|---|---|---|
| `CASM006` | `('DSM001A','DSM001A')` `('DSM002A','DSM002A')` | `DSM001A` `DSM002A` | 缺 xsd 表:OK |
| `OFDM125A` | `('OFD125A_M','OFDM125A_M_Master')` `('OFD125A','OFDM125A_Detail')` | `OFDM125A_Detail` `OFDM125A_M_Master` | 缺 xsd 表:OK |
| `OFDM087`(兩段式) | `('OFD087A','OFDM087')` | `OFD081Validate` `OFDM087` | 缺 xsd 表:OK(xsd 多一張 `OFD081Validate` 是刻意的,不在對映裡) |
| `OFDM381`(兩段式) | `('OFD381','OFDM381')` | `OFDM381` | 缺 xsd 表:OK |

怎麼讀:

- **`缺 xsd 表` 必須是 `OK`。**它比對的是「`xTableMapping` 第二個參數(vdb 表名)有沒有對應的 xsd 表 element」——這一對不上,§12 的「查詢永遠零筆,DB 卻有資料」就會發生。

- **`xsd` 那行可以比 PO 多**(像 `OFDM087` 的 `OFD081Validate`),那是只在 UI 端用、不走 EVA 對映的輔助表,正常。

- **第三處(SQL 裡的實體表名)這支指令查不到**,它印出 `實體表` 清單讓你自己跟 §5.4 手寫的 `FROM` / `JOIN` 比一次。

`atlas_scan --screen <代號>` 的「主檔 / 明細」欄位也讀同一組資訊,但它**不剝註解**(`architecture.md §6.3`),所以註解掉的宣告會被當真。**要精確就用上面這一行。**

## 6. 步驟五:Control —— `InitializeDataAccessPool` / `InitializeVDBTypes`

### 6.1 現況:逐字樣板

把 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM003_Ctl.cs`(136 行)與 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs`(137 行)代換代號與兩張表名後 diff,**差別只有 `using` 的排列順序**,程式碼一行不差。

所以做法就是:**複製 `CASM006_Ctl.cs`,換代號與表名。**下面只解釋你會換到的三塊。

### 6.2 兩個必覆寫

```
public override void InitializeDataAccessPool() { base.DataAccessPool.Add(new CASM006_PO()); }

public override void InitializeVDBTypes()
{
    base.DaoContractType = typeof(ICASM006_PO);  base.ModelVDBType = typeof(CASM006ModelVDB);
    base.ViewVDBType = typeof(CASM006ViewVDB);
}
```

`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:34-37` 與 `:41-46`,與 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:36-39` 與 `:43-48` 同構。漏了的後果:`DataAccessPool.Add` 或 `DaoContractType` 錯 → `GetDaoInstance` 找不到 PO(這也是 §5.1 那個空介面存在的唯一理由);`ModelVDBType` 錯 → 伺服端建不出 ModelVDB;`ViewVDBType` 錯 → 回不了用戶端。`BaseController`(無原始碼,從呼叫端反推)在 `Vendor.Product.Utility`(`architecture.md §2.3`)。

### 6.3 `CustomTransfer*` 四個覆寫:都要寫,都是樣板

| 覆寫 | 錨點 | 內容 |
|---|---|---|
| 泛型 Model → View | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:58-71` | 兩次 `TransferVDBHelper.Transfer*Table` + `view.UIView.AcceptChanges()` |
| 泛型 View → Model | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:80-92` | 同上反向,**沒有** `AcceptChanges()` |
| 非泛型兩支 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:98-101` 與 `:107-110` | 轉型後呼叫泛型版 |
| SQL Server 版兩支 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:111-119` | 一律 `throw new NotImplementedException();`(ATLAS 只跑 Oracle,`architecture.md §4.6`) |

要換的只有表名與「主檔 / 明細用哪一支 helper」:

```
TransferVDBHelper.TransferTable(view.UIView.DSM001A, model.DataEntity.DSM001A, base.TransferEVAColumn);        // 主檔
TransferVDBHelper.TransferDetailTable(view.UIView.DSM002A, model.DataEntity.DSM002A, base.TransferEVAColumn);  // 明細
```

`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:64` 與 `:67`。後者多處理三種 `RowState`(`add-column.md §12.2`);**只有主檔就只寫第一行**。逐欄複製由 `TransferVDBHelper` 按欄名做,Control 根本不知道有哪些欄(`add-column.md §6.1`)——所以 Model 與 View 的名字一致,這四個覆寫就永遠不用再改。

### 6.4 加值方法:先不要寫

`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:130-134` 的私有 `ExecPOActionToViewVDB` 包裝也是樣板,換泛型參數就好。`CASM006` **沒有**任何加值方法;`CASM001` 有(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs:55-65` 的 `AddData`)。四眼的新增 / 修改 / 覆核 / 核准全部走基底,不需要在 Ctl 開洞;要開的時機在 §7.2。

編不過的話 90% 是三件:`typeof` 打錯、四個 `CustomTransfer*` 少一個、`using` 漏了(`Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:1-11` 共 11 行,照抄)。

## 7. 步驟六:FormProxy

### 7.1 現況:最小的一層,21 行

`Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM006_Pxy.cs` **全檔 21 行**:

```
public class CASM006_Pxy : Basic_Pxy
{ protected override void InitializeControl() { this.Control = new CASM006_Ctl(); } }
```

`:10` 是類別宣告、`:15-18` 是唯一的方法。`Basic_Pxy`(無原始碼,從呼叫端反推)在 `Vendor.Product.FormProxy.dll`(`architecture.md §2.3`)。**新畫面直接抄這 21 行,這就是全部。**

### 7.2 什麼時候要多寫

CAS 六支 Pxy 的行數:`CASM006` 21、`CASM003` 22、`CASM005` 87、`CASM004` 97、`CASM002` 141、`CASM001` 164。多出來的都是同一種東西:**UI 需要、但不屬於四眼標準流程的伺服端呼叫**。

| 多寫什麼 | 例 | 何時需要 |
|---|---|---|
| `override Add` | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:30-46` | 新增要走自己的 Ctl 方法(配合 §6.4) |
| 存在性檢查 | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:54` | UI 要即時檢查鍵值重複 |
| 取值 / DataTable | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:149` | UI 要匯出或帶出關聯資料 |

**每一支都必須是同一個 try / catch 樣板**(`Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs:32-45`):`catch` 裡呼叫 `CommonExceptionBlocker.HandleFormProxyException(ex)` 再回一個降級值。理由是這一層是 Remoting 邊界(`architecture.md §8.1`),例外不吞在這裡會以序列化例外炸到用戶端。

**代價寫在這裡以免誤判**:`CASM001_Ctl.AddData()` 沒檢查 `Result` 長度就取 `[0]`,炸出來的 index out of range 就是被這個 catch 吞成 `ServerSideError`(`architecture.md §6.7`)。你多寫的每一支都繼承這個特性——**catch 裡至少要能從回傳值分辨「失敗」與「查無資料」**。

驗證:`grep -n "InitializeControl"` 該檔必須命中 1 次。漏寫的症狀是「畫面開得起來,一按鈕就 `ServerSideError`」,因為 `this.Control` 是 null。

## 8. 步驟七:UI

### 8.1 繼承誰、csproj 怎麼掛

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:21`:`public partial class CASM006 : xMaintainForm`。`xMaintainForm`(無原始碼,從呼叫端反推)在 `Vendor.Product.UI.dll`,`using Vendor.Product.UI.MiddleForm;`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:10`)。**M 型一律 `xMaintainForm`。**

csproj 三段(`Dev/ATLAS.CAS/Source/UI/UI.CAS/UI.CAS.csproj:266-271` 與 `:364-366`):`<Compile Include="<NEW>.cs">` 內含 **`<SubType>UserControl</SubType>`**(漏了 VS 不給開設計檢視)、`<Compile Include="<NEW>.Designer.cs">` 內含 `DependentUpon`、`<EmbeddedResource Include="<NEW>.resx">` 內含 `DependentUpon`。

### 8.2 生命週期:六個事件掛點

Designer 把事件接到方法上(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:980-985`),這是 M 的標準骨架:

| 事件 | 錨點 | 幹什麼 |
|---|---|---|
| `FormInitial` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:278-293` | **必要**:綁 `ProcessVDB` 與 `FormProxy` |
| `AddDataLoad` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:295-303` | 新增模式進場:清明細、綁網格 |
| `ModifyDataLoad` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:305-323` | 修改模式進場:主檔填回控件、綁網格 |
| `BeforeAddButtonClicked` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:325-336` | 送出前驗證 + 主檔鍵灌進明細 |
| `BeforeModifyButtonClicked` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:338-347` | 同上 |
| `BeforeSearchButtonClicked` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:349-385` | 組查詢參數 |

`FormInitial` 的三行是唯一「不寫就一定不會動」的(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:280-282`):`this.TabPages = 2;`、`this.ProcessVDB = new <NEW>ViewVDB();`、`this.FormProxy = new <NEW>_Pxy();`。`CASM001` 一模一樣(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:109-111`),連 `TabPages = 2`(查詢頁 + 維護頁)都相同。

### 8.3 控件命名:前綴決定型別

從 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:1033-1065` 的宣告區反推:

| 前綴 | 控件型別 | 例 |
|---|---|---|
| `ugrd` | `Infragistics.Win.UltraWinGrid.UltraGrid` | `ugrdCASM006`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:1038`) |
| `umsk` | `UltraWinEditors.UltraNumericEditor` | `umskQUO_MGR_TOT`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:1044`) |
| `udat` | `UltraWinEditors.UltraDateTimeEditor` | `udatBOUNS_ST_YYMM`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:1055`) |
| `ubtn` | `Infragistics.Win.Misc.UltraButton` | `ubtnASSIGN_Month`(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs:1045`) |
| `cust` / `uc` | `CustomControl.*`(自家共用控件) | `custEMP_NO`(`:1039`)、`ucDEPT_NO_0`(`:1062`) |

兩條命名規則兩支範本都遵守:**網格叫 `ugrd<畫面代號>`**;**查詢條件控件加 `_0` 後綴**(`custEMP_NO_ST_0` / `umskQUO_YEAR_0`),維護頁同名欄位不加——這是查詢頁與維護頁共用一個 Designer 時區分兩組控件的辦法。控件用 VS 設計檢視拉,**不要手打 Designer.cs**(理由同 `add-column.md §8.3`)。

### 8.4 主檔:具名控件手動雙向搬

主檔不走資料繫結,是兩段對稱的手寫搬運:Row → 控件在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:310-319`;控件 → Row 在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:37-49`。

後者還多做一件**主明細型必做**的事:把主檔鍵值灌進每一列明細(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:55-62`),而且**一定要擋 `RowState`**:

```
foreach (CASM006View.DSM002ARow row in ((CASM006ViewVDB)this.ProcessVDB).UIView.DSM002A.Rows)
    if (row.RowState != DataRowState.Deleted) { row.QUO_YEAR = MasterRow.QUO_YEAR; row.EMP_NO = MasterRow.EMP_NO; }
```

碰已刪除列會丟例外;原始碼上面那句註解「一定要這樣寫」(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:53`)講的就是這件事。

查詢參數在 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:376-383` 塞:`this.QueryVDB.Util.Parameters.AddParametersRow("QUO_YEAR", SQLOperator.Equal, …)`。**第一個字串必須跟 §5.4 的 `Rows.Contains("QUO_YEAR")` 一字不差。**

### 8.5 明細:網格 + 白名單

綁定一行,新增與修改兩個進場點各一次(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:300` 與 `:320`):`this.ugrdCASM006.DataSource = ((CASM006ViewVDB)this.ProcessVDB).UIView.DSM002A;`。顯示哪些欄由白名單陣列決定,機制已在 `add-column.md §8.1` 講完。新畫面要建的是:

| 要建的 | 錨點 | 說明 |
|---|---|---|
| `InitializeLayout` 處理常式 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:392-412` | 開頭一定要 `if (this.ugrdCASM006.DataSource == null) return;` |
| `SetupUltraGridShowColumns` 白名單 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:395` | 陣列順序 = 欄位左右順序 |
| 數字格式 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:396-407` | `Format` 與 `MaskInput` 要**成對**設,只設一個會「顯示有逗號、進編輯沒有」 |
| 對齊 / 唯讀欄 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:409-410` 與 `:411` | `SetTextHAlignColumns` / `SetupUltraGridNoEditColumns` |
| 錯誤事件 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:387-390` | `e.Cancel = true`,吃掉網格自己的錯誤對話框 |
| 版面管理 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:285-286` | `GridLayoutManager` + `GridLayoutUpdateOnly`,寫在 `FormInitial` 裡 |

### 8.6 驗證欄位集中在 `DoValidate`

`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:68-146` 是一支集中的 `DoValidate()`,兩個 `Before*ButtonClicked` 都呼叫它。四種驗證都在裡面:宣告式必填 `validatorManager1.DataValidate()`(`:71`)、跨欄邏輯 `ValidateErrList.AddError(控件, "中文訊息")`(`:74-78`)、明細必填 `CommonGridHelper.AutoCheckPKeyRequireByEssDataReturnMsg`(`:90-99`)、主明細合計對帳 `DataTable.Compute("SUM(欄)", null)`(`:122-144`)。訊息用繁體中文;`AddError` 第一個參數給控件才會標紅並跳焦點。

驗證:`grep -n "ProcessVDB = new\|FormProxy = new\|SetupUltraGridShowColumns"` 三行都要在。少 `ProcessVDB` → 開畫面就 null;少白名單 → 網格會把四眼 15 欄一起顯示出來。

## 9. 步驟八:註冊到選單與權限

> **〔假設〕缺:選單表。**這一節寫不出「改哪張表、下哪句 SQL」,因為選單與權限的定義**不在 repo 裡**。以下是推論與驗法,**沒有一個表名是編造的**。

### 9.1 為什麼查不到

1. **主 EXE(外殼)專案不在 repo。**`architecture.md §2.5` 已記錄:用戶端 remoting 設定整段被註解、找不到主 EXE 專案。選單是外殼在畫的。

2. **repo 內沒有依字串載入畫面的程式。**全庫 `Activator.CreateInstance` 的命中全在 PO 的泛型 VDB 建立(例 `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs:113`),沒有一處是拿代號字串 new Form。

3. **`DB/` 只涵蓋 16% 的 SP、`DB/Table/` 只有變更腳本沒有 DDL**(`architecture.md 附錄 B.0`、`architecture.md 附錄 B.5`),選單表就算存在也不會出現在 repo。

### 9.2 推論:鍵大概長什麼樣

| 推論 | 依據 |
|---|---|
| **以畫面代號當鍵** | 代號是全庫唯一識別,六層檔名 / 類別名 / namespace / xsd 根節點全由它推導(`architecture.md §2.1`);沒有任何 registry 檔,代號本身就是 registry |
| **DB 端欄名很可能叫 `PROG_NO`** | repo 內確實有表把程式代號存成 `PROG_NO`:`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:146`。這是唯一看得到的「畫面代號當資料欄」實例 |
| **權限至少有一部分綁部門** | `CASM006` 的 SQL 直接寫死 `AND COD009.DEPT_NO IN(…)`(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210`) |

**`OFD046` 不是選單表**——它是 `OFDM046` 自己的主檔(`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs:23`),只是剛好有 `PROG_NO` 欄。寫在這裡只是給欄名線索。

### 9.3 拿到輸入後怎麼驗

```
SELECT table_name, column_name FROM all_tab_columns          -- 1. 找出把畫面代號當欄位的表
 WHERE column_name IN ('PROG_NO','PROGRAM_ID','FORM_NO','MENU_NO');
SELECT COUNT(*) FROM <候選表>;                                -- 2. 筆數接近 908 的那張就是全畫面清冊
SELECT * FROM <候選表> WHERE PROG_NO = 'CASM006';             -- 3. 拿已知畫面反查
```

908 來自 `architecture.md §2.1` 的全庫實測。第 2 步對不上就換候選表,不要硬套。權限表用同一招:在第 1 步結果裡找同時有代號欄與 `ROLE` / `GROUP` / `DEPT` 類欄位的那張。

### 9.4 在拿到輸入前怎麼測

不必等選單。M 畫面在 `FormInitial` 裡自己 new 出 `ProcessVDB` 與 `FormProxy`(§8.2),**不依賴選單就能跑**。找一個現成宿主(例如 `Dev/Common/Source/CustomControl/TestWindowControls/`)把 `<NEW>` 掛上去手動開,先把 §11 驗完,選單留到最後補。

> **〔假設〕缺:選單表。**上述 SQL 未實測;`PROG_NO` 之外的三個欄名是常見命名的猜測,**repo 內沒有證據**,放進 `IN` 只為一次撈完。§9.4 的宿主方案也未實測(缺 PTPFBlock DLL)。

## 10. 步驟九:編譯與部署

### 10.1 六個 csproj 都要改,但不會多出組件

新畫面的檔案是**加進既有六個組件**,不是新建六個:

| 專案 | 加什麼 | 錨點(`CASM006` 範本) |
|---|---|---|
| `DataEntity.CAS` | `Compile` × 2 + `None` × 3 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj:116-121` 與 `:203-213` |
| `UIEntity.CAS` | 同上 | `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj:116-121` 與 `:203-213` |
| `PO.CAS` | `Compile` × 1 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:107` |
| `Control.CAS` | `Compile` × 1 | `Dev/ATLAS.CAS/Source/Control/Control.CAS/Control.CAS.csproj:88` |
| `FormProxy.CAS` | `Compile` × 1 | `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/FormProxy.CAS.csproj:84` |
| `UI.CAS` | `Compile` × 2 + `EmbeddedResource` × 1 | `Dev/ATLAS.CAS/Source/UI/UI.CAS/UI.CAS.csproj:266-271` 與 `:364-366` |

檔名在 csproj 裡是**排序插入**的(`CASM005…` 之後、`Properties\AssemblyInfo.cs` 之前)。順序不影響編譯,照著插 diff 才乾淨。

### 10.2 模組有多個 Entity 專案時放哪一個

CAS 只有一個,但大模組會拆:`Dev/ATLAS.OFD/Source/Entity/` 底下是 `DataEntity.OFD1`–`DataEntity.OFD9`(配 `UIEntity.OFD1`–`UIEntity.OFD9`),xsd 支數 8 / 9 / 9 / 18 / 18 / 21 / 15 / 25 / 58。 規則:**放進編號最大的那個**(OFD 是 `9`),它已是最大宗;**Model 與 View 編號必須配對**(`Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM913AModelVDB.cs:11`)。

### 10.3 重編順序與部署

重編順序、部署到哪一端、`UIEntity` 兩端都要,與加欄位完全相同:見 `add-column.md §9.1` 與 `add-column.md §9.2`,依據在 `architecture.md §2.4` 與 `architecture.md §8.1`。 **新畫面多一條檢查**:`architecture.md 附錄 C.5` 的 25 個「有原始碼卻被 `HintPath` 綁成預編 DLL」的組件。CAS 六層都不在名單裡(`add-column.md §9.3` 已查證),**但 `EC` 或 `OTA` 模組要先查**——在該層 csproj 搜 `PTPFBlock`,搜得到就是綁 DLL,重編不會傳到下游。

> **〔假設〕缺:PTPFBlock DLL。**整個 §10 未實測(`architecture.md 附錄 C.1`)。csproj 三段來自 `CASM006` 原文,重編順序來自 `ProjectReference` 相依。

## 11. 驗證清單

第一輪不碰四眼,先確認六層接上:

| # | 動作 | 過的條件 | 沒過回去做 |
|---|---|---|---|
| 1 | `atlas_scan.py --screen <NEW>` | 六層都有路徑、表列得出來 | §3 §4 §5 |
| 2 | 依 `add-column.md §9.1` 順序重編六個專案 | 六個都成功 | §10.1 |
| 3 | 開畫面 | 版面出得來、不 null | §8.2 |
| 4 | 空條件查詢 | 不報錯(沒資料也算過) | §5.4 §7.2 |

第二輪跑完整四眼,每一步查 DB(狀態語意見 `architecture.md §3`):

| # | 動作 | 查什麼 |
|---|---|---|
| 5 | 新增主檔 + 兩列明細,送出 | 主明細都進 DB;`STATUS` 進 `Entry*`;明細的主檔鍵有被灌進去(§8.4) |
| 6 | 重開畫面查同一筆 | 主檔回填控件、明細回填網格(驗 §5.4 的 SELECT) |
| 7 | 待辦清單看得到 | 驗 `BeforeGetToDoData` 與 `isToDoString` 分支(§5.4) |
| 8 | 換帳號覆核 → 主管核准 → 退回後重送 | `STATUS` 依序進 `Verify*` / `Approve*`,`REJECTID` 有值,資料不變 |
| 9 | 修改:改主檔一欄、刪一列明細、加一列明細 | 三種 `RowState` 都對(驗 `TransferDetailTable`,§6.3) |
| 10 | 刪除整筆;再故意觸發每一條 §8.6 的驗證 | 主明細一起走;每條驗證都跳中文訊息且擋住送出 |

**第 6 與第 9 最容易失敗**:前者驗手寫 SELECT,後者驗明細的狀態處理。

## 12. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **編譯過,執行期找不到型別 `<NEW>Model`** | xsd 進了資料夾但 csproj 沒掛 `Generator` | §3.5 |
| **Designer.cs 只有外殼、沒有 Row 類別** | 表 element 的 10 個 `msprop` 漏了 | §3.2 |
| **開畫面就 `NullReferenceException`** | `FormInitial` 沒設 `ProcessVDB` / `FormProxy` | §8.2 |
| **畫面開得起來,按任何鈕都 `ServerSideError`** | `_Pxy` 漏寫 `InitializeControl()`,`Control` 是 null | §7.1 |
| **查詢永遠零筆,DB 卻有資料** | `xTableMapping` 表名、xsd 表 element 名、SQL 表名三者不一致 | §5.2 |
| **查得到主檔,明細永遠空的** | `BuildDetailSQLString` 外層 `if` 的表名對不上 | §5.4 |
| **主檔有值畫面全空,或反過來** | Model 與 View 欄名不一致,`TransferVDBHelper` 靜默丟掉 | §4.2、`add-column.md §6.2` |
| **網格把四眼 15 欄全顯示出來** | 沒呼叫 `SetupUltraGridShowColumns` | §8.5 |
| **明細存進去,主檔鍵值是空的** | `SetMasterToDetail` 沒灌鍵 | §8.4 |
| **查詢條件填了沒作用** | UI 的 `AddParametersRow` 與 PO 的 `Rows.Contains` 字串不同 | §5.4 §8.4 |
| **`ORA-00904`,欄名是 `STATUS` 或 `DATAFLAG`** | 新建的表沒有四眼 15 欄 | §2.3 |
| **四眼走不動,狀態一直不變** | SELECT 漏了 `AllEVAColumnsForSelect` | §5.4 |
| **`GetDaoInstance` 找不到 PO** | `DaoContractType` 打錯或沒 `DataAccessPool.Add` | §6.2 |
| **自己這台好了,別人還是舊的** | `UIEntity` 只佈了一端 | `add-column.md §9.2` |

**其中五條是靜默失敗**(查詢零筆、明細空、Model/View 不一致、網格白名單、參數字串對不上),不報錯不寫 log,所以 §11 不能跳。

## 13. 可以少建哪一層

### 13.1 先看現況,並且知道掃描器會誤報

`architecture.md §2.7` 拆過:全庫 65 支「不齊」裡一大半是 `_9i` 後綴或 `.Query` 專案改命名造成的字面不符。查自己模組:`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --module <MOD>`,「六層」寫「齊」就是齊(CAS 16 支全齊)。

**還有一種假警報是 `architecture.md §2.7` 沒收錄的:大小寫。**`OFDM742` 被判缺 FormProxy,但檔案就在 `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM742_pxy.cs:1` —— 小寫的 `_pxy`;UI 那邊 `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM742.cs:98` 明明白白 `new OFDM742_Pxy()`。Windows 編得過,大小寫敏感的工具判缺。**新畫面一律用大寫 `_Pxy`。**

### 13.2 M 型幾乎不能少

`architecture.md §6.6` 實測:M 型 284 支只有 12 支有缺,10 支集中在 OFD。理由很硬——M 一定要 `BaseEVADaoPO` + `xTableMapping` + 四眼,缺哪層都跑不起來。真能少的只有兩種:

| 少什麼 | 什麼情況 | 實例 |
|---|---|---|
| **少 UI + FormProxy** | 純伺服器功能,沒有畫面入口,由別支畫面或服務代呼叫 | `OFDM913` 只有 Pxy / Ctl / PO(`atlas_scan.py --screen OFDM913`),Pxy 提供的是 `BatchAdd` / `CheckExists` 這類批次方法(`Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM913_Pxy.cs:32`) |
| **少 DataEntity + UIEntity** | 不回傳資料集(跑完只改 DB 狀態),或借用別支畫面的 entity | `architecture.md §6.6` 的 28 支,全是 `B` 型 |

**兩種都不是 M。**在建 M 卻想少一層,先確認型別碼選對了:

想少 UI(沒有畫面)→ 你要的是 `B`;想少四眼(不用送核)→ `I`;只印不寫 → `R`(七層,多一個 `Report.<模組>`)。 **改型別碼比硬拆 M 的六層便宜得多。**

### 13.3 唯一常見的「少建」:沒有明細

這不是少一層,是少一張表,四處連動:

| 處 | 沒有明細時 | 錨點 |
|---|---|---|
| xsd | 只有一個表 element、一組 `xs:unique` | 對照 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd:113` |
| PO | 不宣告 `DetailTable`、不寫 `BuildDetailSQLString`、`BeforeGetMaintainData` 的 `else` 分支拿掉 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs:36-39` |
| Ctl | 四個 `CustomTransfer*` 只留 `TransferTable` | 對照 `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs:67` |
| UI | 不要網格、不要主檔鍵灌明細的迴圈 | 對照 `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:55-62` |

範本:`CASM004` 與 `CASM005`,兩支都是純主檔的 M。

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd` | `:12` `:15` `:25-31` `:46` `:52` `:113` `:205` `:211-221` | §3 §13.3 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006ModelVDB.cs` | `:9-19` | §3.6 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM006ViewVDB.cs` | `:9` `:19` | §3.6 §4.2 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/DataEntity.CAS.csproj` | `:116-121` `:203-213` | §3.5 §10.1 |
| `Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/UIEntity.CAS.csproj` | `:116-121` `:203-213` | §4.2 §10.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs` | `:18-20` `:23-24` `:27-34` `:29-31` `:32-33` `:46-94` `:105-215` `:111-127` `:113-115` `:132-140` `:138` `:203-206` `:210` `:224-273` `:229` | §5 §9.2 |
| `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM006_Ctl.cs` | `:1-11` `:34-37` `:41-46` `:58-71` `:64` `:67` `:80-92` `:98-101` `:107-110` `:111-119` `:130-134` | §6 §13.3 |
| `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM006_Pxy.cs` | `:10` `:15-18` | §7.1 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs` | `:10` `:21` `:37-49` `:53` `:55-62` `:68-146` `:278-293` `:280-282` `:285-286` `:295-303` `:300` `:305-323` `:310-319` `:320` `:325-336` `:338-347` `:349-385` `:376-383` `:387-390` `:392-412` `:395` `:396-407` `:409-410` `:411` | §8 §13.3 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.Designer.cs` | `:980-985` `:1033-1065` `:1038` `:1039` `:1044` `:1045` `:1055` `:1062` | §8.2 §8.3 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/UI.CAS.csproj` | `:266-271` `:364-366` | §8.1 §10.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj` | `:107` | §10.1 |
| `Dev/ATLAS.CAS/Source/Control/Control.CAS/Control.CAS.csproj` | `:88` | §10.1 |
| `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/FormProxy.CAS.csproj` | `:84` | §10.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs` | `:42-45` `:49-58` `:77` `:170` `:298` | §5.3 §5.4 |
| `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM001_Ctl.cs` | `:36-39` `:43-48` `:55-65` | §6.2 §6.4 |
| `Dev/ATLAS.CAS/Source/FormProxy/FormProxy.CAS/CASM001_Pxy.cs` | `:30-46` `:32-45` `:54` `:149` | §7.2 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs` | `:109-111` | §8.2 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | `:21` `:133-141` | §3.3 §3.4 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM003_PO.cs` | `:30-32` | §5.3 |
| `Dev/ATLAS.CAS/Source/Control/Control.CAS/CASM003_Ctl.cs` | `:1-136` | §6.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM004_PO.cs` | `:39-42` `:42` | §2.3 §5.2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM005_PO.cs` | `:36-39` | §2.3 §5.3 §13.3 |
| `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs` | `:17` | §5.1 |
| `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs` | `:20` `:115-132` | §2.3 §5.4 |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM742_pxy.cs` | `:1` | §13.1 |
| `Dev/ATLAS.OFD/Source/UI/UI.OFD/OFDM742.cs` | `:98` | §13.1 |
| `Dev/ATLAS.OFD/Source/FormProxy/FormProxy.OFD/OFDM913_Pxy.cs` | `:32` | §13.2 |
| `Dev/ATLAS.OFD/Source/Entity/DataEntity.OFD9/OFDM913AModelVDB.cs` | `:11` | §10.2 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM046_PO.cs` | `:23` `:146` | §9.2 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM071_PO.cs` | `:113` | §9.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **選單 / 權限表** | §9 整節 | 目前只有推論(代號當鍵、欄名可能是 `PROG_NO`)與三步驗法;補進來後寫成可貼的 INSERT 與授權步驟 |
| **Oracle 唯讀帳號** | §2.3 §3.3 | 四眼 15 欄的檢查 SQL 未實測;xsd 的 `maxLength` 目前只能抄相鄰欄位,補進來後可對 `DATA_LENGTH` 直接填 |
| **PTPFBlock DLL** | §3.7 §6.4 §10 §11 | 編譯與部署段全未實測;Designer.cs 重生、六層 build、四眼實跑都要補實際指令與輸出 |
| **主 EXE / 外殼專案** | §9.1 §9.4 | 目前只能說「不在 repo」;補進來後可寫畫面怎麼被外殼載入,以及 §9.4 的替代宿主 |
| **部署機的 `main.exe.config`** | §10.3 | 客戶端 Remoting 設定不在版控(`architecture.md §8.1`),無法寫出佈到哪個目錄 |

## 附錄 C 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。以 `CASM006` 為主範本、`CASM001` 為對照,拆出「樣板 / 畫面特有」 |

由 build_doc.py v2.0.0 於 2026-09-15 17:56 產生 · 標題 64 · 圖 1 · 表格 28 · 程式錨點 150 · § 連結 128 · 引用檢查：畫面 30（缺 0） · Table 4（缺 0） · 結果集 5（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/add-query-screen.md
============================================================

# ATLAS 維護手冊 — 新增一支 I 查詢畫面

> 產出日期:2026-09-15(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 ⚠ 標「**〔假設〕缺:輸入**」的是拿不到輸入(DB 連線 / PTPFBlock DLL / 選單表)只能推論的部分,附錄 B 彙整;標「**〔客戶特定〕**」的是本站台的值。

> **本手冊是 `runbooks/add-screen.md` 的差異版。**凡是與 M 畫面相同的步驟一律引用,不重抄: 代號規則 `add-screen.md §2`、xsd 三層結構與 10 個 `msprop` `add-screen.md §3`、View 抄 Model `add-screen.md §4`、Control 樣板 `add-screen.md §6`、FormProxy `add-screen.md §7`、UI 控件命名 `add-screen.md §8.3`、選單註冊 `add-screen.md §9`、csproj 與重編 `add-screen.md §10`。前提知識在 `architecture.md §6.3`(I 型的退化)與 `architecture.md §6.7`(I 為什麼沒有四眼)。本篇的實測母體:`Dev/ATLAS.OFD.Query/` 的 **43 支 PO、43 支 Control、58 支 UI 檔**,外加 `modules/cas.md §5` 已寫深的 `CASI001`。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在既有模組裡**從零建一支 I(查詢)畫面**:唯讀、不寫入、不走四眼 |
| 主要範本 | `OFDI716`(`BaseEVADaoPO` + 參數化 SQL + 主明細 + 匯出,本篇最推薦照抄的一支) |
| 對照範本 | `OFDI911`(裸 DAO + SP)· `CASI001`(`modules/cas.md §5` 已寫深,反面教材多) |
| 不適用 | M 維護畫面(`add-screen.md`)· B 批次(`add-query-screen` 之外請看 `runbooks/add-batch.md`)· R 報表(`runbooks/add-report.md`) |
| 前提工具 | Visual Studio · Oracle 客戶端 · PTPFBlock DLL · TFS workspace |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 佈位符 | `<NEW>` = 新代號 · `<MOD>` = 模組 |

### 0.1 一句話版本

**I 不是「M 少幾層」,是同樣六層裡有四層退化。**兩份 xsd 與六個 csproj 一個都不能少。省下來的只有:四眼那組欄位、Control 的 `InitializeVDBTypes()`、PO 的 `xTableMapping` 宣告、UI 的四眼工具列。

## 1. M 與 I 的差異總表(圖)

```text
[圖] M 維護畫面與 I 查詢畫面的層級差異:四處退化、兩件不可省、PO 基底三選一
圖中文字:M 維護畫面 —— 六層滿血,四眼全走 / PO : BaseEVADaoPO / xTableMapping 宣告 / Ctl 兩個必覆寫 / Pool + VDBTypes / Pxy 21 行 / 只有 InitializeControl / UI 四眼工具列 / 送核 覆核 核准 / I 查詢畫面 —— 同樣六層,但四處退化 / PO 多半不繼承基底 / 43 支裡 24 支裸 DAO / Ctl 只覆寫 Pool / 沒有 VDBTypes / Pxy 覆寫 Query / 不覆寫 Add / Update / UI 只有查詢鈕 / 執行鈕關掉 / 不變的兩件事 —— 少做會直接壞掉 / Model.xsd 一定要建 / 沒型別就沒 VDB / View.xsd 一定要建 / 跨 Remoting 的型別 / 六個 csproj 照掛 / xsd 三段不可漏 / 四眼 13 欄免了 / 查詢表多半沒有 / PO 基底三選一 —— 第三個是地雷 / 裸 DAO(24 支) / 自己 new Database / BaseEVADaoPO(15 支) / 用 dbProduct / BasicEVAPO(4 支) / dbTA 恆為 null / 新畫面二選一 / 絕不選第三個
```

*圖:圖 1 M 與 I 的差別。I 不是「少幾層」,是同樣六層裡有四層退化;兩份 xsd 與六個 csproj 一個都不能少。橘色虛框=選到就是死畫面。*

這張表是本手冊的主體,其餘各節是它的展開。

| # | 項目 | M(`add-screen.md`) | I | 差在哪一節 |
|---|---|---|---|---|
| 1 | 專案位置 | `Dev/ATLAS.<MOD>/Source/` | **`Dev/ATLAS.<MOD>.Query/Source/`**,每層資料夾加 `Query` 前綴 | §2 |
| 2 | 代號第四碼 | `M` | `I` | §2 |
| 3 | `Model.xsd` 與 `View.xsd` | 兩份都要建 | **兩份都要建**,但不放四眼那組欄位 | §3 |
| 5 | xsd 的四眼欄位 | 主檔明細各 15 欄 | **不放** | §3.2 |
| 6 | PO 基底 | `BaseEVADaoPO` / `BaseMultiRowEVADaoPO` | 裸 DAO 或 `BaseEVADaoPO`,**二選一** | §4 |
| 7 | PO 介面 | `: IEvaDataAccess` | 裸 DAO 不繼承任何東西;`BaseEVADaoPO` 那條仍要 `: IEvaDataAccess` | §4.2 |
| 8 | `xTableMapping` 宣告 | **必要**,兩參數 + xsd 表名三處同名 | **多半不宣告**(43 支裡只有 2 支有) | §5 |
| 9 | PO 的兩支 `BuildXxxSQLString` | `BeforeSelect` 等三個事件觸發 | **沒有事件**,自己寫一支 `GetQuery` | §5 §6 |
| 10 | SQL 的四眼欄位 | 一定 `AllEVAColumnsForSelect` | **不要**加 | §3.2 |
| 11 | 查詢條件 | 多半字串串接(現存缺陷) | **一律參數化** | §6 |
| 12 | Control `InitializeDataAccessPool` | 要 | **要** | §7 |
| 13 | Control `InitializeVDBTypes` | 要 | **不要**(43 支裡只有 1 支有) | §7 |
| 14 | Control `CustomTransfer*` 四件套 | 四個都寫 | 只寫 Oracle 那兩個,SQL 那兩個 `throw NotImplementedException` | §7 |
| 15 | FormProxy 覆寫 | `InitializeControl()` | **`Query()` 與 `GetMaintainData()`** | §7 |
| 16 | UI 基底 | `xMaintainForm` | **`xOneStepProcessForm`**(42/58)或 `xQueryForm`(8/58) | §8 |
| 17 | 四眼工具列 | 有(送核 / 覆核 / 核准 / 退回) | **沒有**,執行鈕直接 `e.Cancel = true` | §8.1 |
| 18 | 分頁與匯出 | 依畫面 | `TabPages = 2`(條件頁 + 結果頁)· `this.ExportGrid = <某個 grid>` | §8.2 §8.3 |
| 20 | 六個 csproj | 要改 | **要改**(在 `.Query` 專案那六個) | §9 |

## 2. 步驟一:代號與專案

### 2.1 現況:I 畫面住在 `.Query` 專案

`architecture.md §2` 的鐵律:`I` 型住在 `Dev/ATLAS.<MOD>.Query/`,六層資料夾與組件名都加 `Query` 前綴:

```
Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/
Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/
Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/
Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/
Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/
Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/
```

**例外要先 `ls` 確認。**OFD 的查詢畫面散在兩個專案:`Dev/ATLAS.OFD.Query/`(43 支)與 `Dev/ATLAS.OFDI/`(1 支,`Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs`,而且它的層資料夾**沒有** `Query` 前綴)。`ofd8.md §5` 記過這件事。**新畫面放 `.Query`,不要再往 `ATLAS.OFDI` 加。**

### 2.2 改法與驗證

取號規則與 M 相同(`add-screen.md §2.2`):同模組同型別最大號 +1;`Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/` 底下有 36 份 `.xsd`(`QueryUIEntity.OFD` 同為 36 份),**沒有分卷**,直接放進去。驗證:`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen <NEW>` 回「找不到」才是對的。

## 3. 步驟二:兩份 xsd —— 要建,但不放四眼欄位

### 3.1 現況:xsd 一份都不能省

`architecture.md §6.7` 講的是「I 沒有四眼」,不是「I 不用 entity」。實測 `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` 與 `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI716View.xsd` 兩份都在,而且 `*Model.Designer.cs` / `*ModelVDB.cs` / `.xsc` / `.xss` 五件套俱全。 **沒有 xsd 就沒有 `<NEW>ModelVDB` / `<NEW>ViewVDB` 兩個型別**,UI 的 `this.ProcessVDB = new <NEW>ViewVDB();` 連編都編不過。

骨架、三層結構、10 個 `msprop`、主鍵、csproj 三段全部照 `add-screen.md §3` 與 `add-screen.md §4`,**本節只講差異**。

### 3.2 改法:四眼那組欄位不要放

M 的每張表都帶 15 個四眼欄位,清單在 `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs:114-133`: `STATUS` + `CREATEID` / `CREATEDATE` / `UPDATEID` / `UPDATEDATE` / `ENTRYID` / `ENTRYDATE` / `VERIFYID` / `VERIFYDATE` / `APPROVEID` / `APPROVEDATE` / `REJECTID` / `REJECTDATE`(這 13 欄是四眼的狀態與人時戳)+ `DATAID` / `DATAFLAG`(資料識別)。

**I 的 xsd 不放這一組。**實測對照:

| xsd | 表數 | `DATAID` | `STATUS` | `DATAFLAG` |
|---|---|---|---|---|
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd`(M) | 2 | 2 個 | 2 個 | 2 個 |
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd`(I) | 3 | **0** | **0** | **0** |

`OFDI716Model.xsd` 三張表裡只有一般的 `CreateID` / `CreateDate` 兩個稽核欄——那是**來源表本來就有的業務欄位**,不是四眼機制。

跟著一起省掉的兩件事:

1. **SQL 裡不要呼叫 `AllEVAColumnsForSelect`**(對照 `add-screen.md §5.4` 第 2 條),查詢表多半根本沒有這些欄,加了就 `ORA-00904`。

2. **不需要 `xs:unique` 的四眼主鍵**(`add-screen.md §3.4`);查詢結果集沒有異動,主鍵只影響 DataSet 的去重行為。

**驗證**:`grep -c "Generator_TableClassName" <NEW>Model.xsd` 要等於你打算回傳幾張 DataTable(`OFDI716Model.xsd` 是 3);`grep -c "DATAID" <NEW>Model.xsd` 要回 0。

## 4. 步驟三:PO 基底選哪一個(實查 43 支)

### 4.1 現況:三種並存,第三種是地雷

剝掉 `//` 註解後掃 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/*_PO.cs` 的 43 支,基底分布:

| 基底 | 支數 | 連線從哪來 | 判定 |
|---|---|---|---|
| **裸 DAO**(只實作 `I<代號>_PO`,沒有基底) | **24** | PO 自己 `new Database("TA", DbServerType.Oracle)` | **可用** |
| **`BaseEVADaoPO`** | **15** | 基底管,PO 內用 `dbProduct` | **可用,而且最推薦** |
| **`BasicEVAPO`** | **4** | **`dbTA` 恆為 null** | **禁用,一定 NRE** |

三支實挑確認(**不是從表格推的,是逐檔看過**):

| 支 | 宣告 | 形狀 |
|---|---|---|
| `OFDI716` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:22` `public class OFDI716_PO : BaseEVADaoPO, IOFDI716_PO` | 一支 `GetQuery<T>`,三段參數化 SQL,用 `dbProduct.LoadDataSet` 直接填三張 DataTable |
| `OFDI911` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:28` `public class OFDI911_PO : IOFDI911_PO` | 裸 DAO,自己 `new Database("TA", …)`(`:30`),呼叫 SP + 11 個 RefCursor 出參 |
| `OFDI719` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs:11` `public class OFDI719_PO : BasicEVAPO` | **死畫面**:`:30` 第一行就是 `dbTA.CreateConnection()`,而 `dbTA` 恆為 null;SQL 還是 T-SQL 方言(`CONVERT` / `ISNULL`) |

四支 `BasicEVAPO` 的完整名單:`OFDI058B` `OFDI059` `OFDI375` `OFDI719`。理由與證據鏈見 `add-screen.md §5.7` 與 `architecture.md §3.1.1`。

### 4.2 改法:二選一,怎麼選

| 這支畫面 | 選 | 介面怎麼寫 |
|---|---|---|
| 查詢邏輯是 C# 組 SQL,而且要用 typed DataSet 的表名 | **`BaseEVADaoPO`** | `public interface I<NEW>_PO : IEvaDataAccess { T GetQuery<T>(T model, params object[] args); }` |
| 查詢邏輯整包在 SP 裡,C# 只負責綁參數收 RefCursor | **裸 DAO** | `public interface I<NEW>_PO { DataSet GetXxx(…); }`,不繼承任何東西 |

**兩種都要標 `[PODbType(DbServerType.Oracle)]`**(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:21`、`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:27`),否則 `GetDaoInstance` 找不到。

> ⚠ **判斷基底一定先剝 `//` 註解。**`Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs:28` 留著一行 `//public class OFDM125A_PO : BasicEVAPO`、第 `:30` 行才是現行的 `BaseEVADaoPO`。直接 `grep "class .*_PO *:"` 會誤判成死畫面。同一條坑在 `add-screen.md §5.7` 有完整說明。

### 4.3 ⚠ `.Query` 專案的 PO 命名有兩種

**這是掃描器踩過的坑(D7),接手時一定要知道。**

| 專案 | PO 檔名 | 實例 |
|---|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` | `<代號>_PO.cs` | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs` |
| `Dev/ATLAS.OTA.Query/Source/PO/…` | `<代號>_PO.cs` | 同上形狀 |
| **`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/`** | **`<代號>OracleDao.cs`** | `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` |
| **`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/`** | **`<代號>OracleDao.cs`** | `ofdb3.md §3.5` 的 `OFDB615` / `OFDB616` / `OFDB671`–`OFDB673` |

`Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/` 底下還多分三個子資料夾:`Interface/`(`I<代號>.cs`)、`Oracle/`(現行)、`MSSQL/`(舊世代,多半整檔註解)。

**`atlas_scan --screen` 對兩種命名都認得。**實跑對照:

```
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen OFDI716
  PO          Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen OFDI641
  PO          Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs
```

但兩支的「表」區段都印 `主檔 —` / `明細 —`。**那不是缺層,是 I 型本來就不宣告 `xTableMapping`(§5)。**

**新畫面一律用 `<NEW>_PO.cs`。**`OracleDao` 那套是 EC 的歷史包袱,跟著它只會讓下一個人再踩一次。

**驗證**:用 `add-screen.md §5.7` 那支「剝註解取基底」的一行指令查新 PO,印出來的必須含 `BaseEVADaoPO` 或只有 `I<NEW>_PO`。**看到 `BasicEVAPO` 就停手重寫。**

## 5. 步驟四:沒有 `MasterTable` 宣告,那 `xTableMapping` 那一步變成什麼

### 5.1 現況:43 支裡只有 2 支宣告

`grep -rn "MasterTable" Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` 只命中兩個檔: `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI059_PO.cs:17`(舊型別 `TableMapping`,而且那支是 `BasicEVAPO` 死畫面)與 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs:39`。 `OFDI199` 也是 43 支 Control 裡**唯一**有 `InitializeVDBTypes()` 的一支——它是 `architecture.md §6.7` 講的「查詢 + 放行」混合畫面,不是純 I。

**純 I 畫面不宣告主明細。**`add-screen.md §5.2` 那三條規則在這裡全部不適用。

### 5.2 改法:那一步被拆成三處具名字串

M 靠 `xTableMapping` 的兩個參數把「實體表名」與「VDB 裡的 DataTable 名」綁起來,I 則是**在三個地方各自寫一次表名**:

| 處 | 寫什麼 | 錨點 |
|---|---|---|
| PO 的 SQL | 實體表名(`FROM TRP805A …`) | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:64-95` |
| PO 的 `LoadDataSet` 第三參 | **typed DataSet 的表名,從型別取,不要打字串** | `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:111`、`:160` |
| Control 的 `CustomTransferOracleModelToView` | 逐表 `TransferVDBHelper.TransferTable(view.UIView.X, model.DataEntity.X, …)` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:73-97` |

第二處是關鍵,`OFDI716` 做對了:

```
dbProduct.LoadDataSet(cmd, model.DataEntity, model.DataEntity.TRP805_D.TableName);
```

**用 `model.DataEntity.<表>.TableName` 而不是字串常值**,表名打錯會在編譯期紅字,不會變成執行期的「查詢永遠零筆」。 `add-screen.md §12` 症狀表裡的「查詢永遠零筆,DB 卻有資料」在 I 型就是靠這個寫法擋掉的。

第三處同理:`TransferVDBHelper.TransferTable(view.UIView.TRP805, model.DataEntity.TRP805, base.TransferEVAColumn)` 兩邊都是強型別成員,Model 與 View 的表名對不上會編不過。

**驗證**:`grep -c "LoadDataSet" <NEW>_PO.cs` 要等於 xsd 的表數,而且每處的第三參都必須是 `model.DataEntity.<表>.TableName`,不可以是字串常值。

## 6. 步驟五:查詢條件怎麼組 —— 參數化,禁字串串接

```text
[圖] I 查詢畫面的查詢流程:UI 驗證與組條件、過 Remoting 的三層、PO 參數化查詢、回到 UI 的換頁與匯出
圖中文字:① 按查詢之前 —— 全部在 UI / DoValidate 起迄 / 起大於迄要擋 / 至少一個條件 / 不擋就全表掃 / Parameters 命名 / 與 PO 端字串一致 / 起空補迄 / Leave 事件 / ② 過 Remoting 到伺服端 —— 三層都是薄的 / Pxy.Query / try / catch 包起來 / Ctl.Select / ExecPOActionToViewVDB / PO.GetQuery / 唯一要自己寫的 / 例外回 Result / 不可吞成空字串 / ③ PO 內部 —— 參數化是唯一正確寫法 / SQL 用 :佔位 / 禁止串使用者輸入 / FindByName 再綁 / null 就不加條件 / LoadDataSet 指定表 / 表名取自 DataEntity / 0 筆也要回 / AddResultRow / ④ 回到 UI —— 換頁、明細、匯出 / Ctl 逐表 Transfer / 沒有 MasterTable / ChangeTabPage / 查詢條件頁鎖住 / 明細在前端過濾 / DataTable.Select / ExportGrid / 匯出指哪張
```

*圖:圖 2 查詢流程。橘色實框=自己要寫對的地方。整條路徑上沒有任何寫入,所以出錯的樣子一律是「查不到」或「查太多」,不會報錯 —— 這就是 I 難查的原因。*

### 6.1 現況:兩種寫法並存,舊的那種是全庫最常見的缺陷型

`architecture.md §4.3` 已定調:參數化在 ATLAS「做了一半」。查詢類尤其嚴重——`CASI001` 的 11 個查詢條件**全部是字串串接**(`modules/cas.md §5.2`),而且串出來的 8 處起迄條件寫成 `> =`(中間有空白),`modules/cas.md §5.3` 判定那是壞的 SQL。

`OFDI716` 是對照組,它是參數化的:

```
WHERE TRP805A.TRANS_DATE >=:TRANS_DATE_ST
  AND TRP805A.TRANS_DATE <=:TRANS_DATE_END
  AND (OFD081V.FUND_ID IN (SELECT * FROM TABLE(F_FormatStringToTable(:FUND_ID))))
```

`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:90-95`,綁定在 `:99-108`。

### 6.2 改法:四條規則

1. **SQL 裡一律用 `:名稱` 佔位,值走 `AddInParameter`。** ``csharp if (model.Utility.Parameters.FindByName("TRANS_DATE_ST") != null) dbProduct.AddInParameter(cmd, "TRANS_DATE_ST", OracleDbType.Varchar2, Convert.ToString(model.Utility.Parameters.FindByName("TRANS_DATE_ST").Value));`` `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:101-104`。

2. **多值條件用 TVF 把字串拆開,不要組 `IN ('a','b','c')`。**`F_FormatStringToTable(:FUND_ID)` 收一個逗號分隔字串,UI 端把勾選的代碼串成 `"A,B,C"` 再送(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:86-93`)。

3. **參數名要跟 UI 的 `AddParametersRow` 字串一模一樣**(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:98-102`)。又一個靠字串對上的跨層綁定,打錯不紅字、條件靜靜不生效。

4. **`FindByName(…) != null` 才綁。**參數不存在就不加該條件——但這也是 `CASI001` 那顆雷的來源(§6.3),所以**「條件不存在」的語意要在 SQL 裡先想清楚**。

### 6.3 ⚠ 條件不存在時會靜默放大查詢範圍

`CASI001` 的權限條件靠 UI 端取員工代號:取不到就不加 `QUERY_EMP_NO` 參數,而 PO 端沒有「參數不存在就擋下」的分支,**結果是唯讀畫面的資料範圍從「自己」放大到「全部」,而且無聲無息**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs:135-136` 與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207`,`modules/cas.md §5.3`)。

**規則:凡是「限縮資料範圍」的條件(權限、機構、幣別),參數不存在時一律回零筆或丟例外,不可以當成沒有條件。** 只有「使用者選填的篩選條件」才適用第 4 條的 `!= null` 寫法。

### 6.4 現況:五種會靜默濾掉資料的寫法,都不要抄

`modules/cas.md §5.3` 把 `CASI001` 的六個靜默過濾逐一拆過,其中五種是通用的:

| 寫法 | 後果 | 錨點 |
|---|---|---|
| 硬編的 `WHERE X = '3'`,畫面上沒有對應欄位 | 那一類資料**永遠查不到**,而且沒有提示 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:185-186` |
| 權限白名單寫死員工代號 | 換人要改 code 重編重部署〔客戶特定〕 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:206-207` |
| 日期當字串比 | 只要有一筆存成別的格式就落在區間外 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:329`、`:345` |
| 代碼說明 join 的分類碼寫死 | 分類碼一改,說明欄整片變空但主檔還在 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:152-183` |
| 比較運算子中間有空白(`> =`) | **假設**整段 SQL 語法錯,被 catch 吞成「執行失敗,請檢查」 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:219` |

最後一條標**假設**:依據是 SQL 標準與 Oracle 詞法規則,**無法在本機驗證**,要連 DB 才能確認。同樣寫法在全庫只出現在四個檔,全部是同一份查詢樣板的後代。

### 6.5 改法:查無資料要回得明確

```
i = model.DataEntity.TRP805_D.Rows.Count;
model.Utility.Result.Clear();
model.Utility.Result.AddResultRow(i != 0, i, "");
```

`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:162-173`(原文是 `if / else` 兩段)。例外時 `AddResultRow(false, 0, ex.Message)`(`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs:175-179`)——**訊息不可是空字串**,理由與批次相同(`add-batch.md §6.5`)。

### 6.6 驗證

| # | 查什麼 | 怎麼查 |
|---|---|---|
| 1 | 有沒有字串串接 | `grep -n "+ \"'\"" <NEW>_PO.cs` 應回 0;SQL 裡的 `:名稱` 個數要等於 `AddInParameter` 的個數 |
| 2 | 條件名有沒有對上 | PO 的 `FindByName("X")` 與 UI 的 `AddParametersRow("X", …)` 逐一比對;再查 `AddResultRow(false` 的第三參有沒有內容 |

## 7. 步驟六:Control 與 FormProxy

### 7.1 Control:比 M 少一個覆寫,多兩個 `NotImplementedException`

`Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs` 全檔 123 行,四件:

| 件 | 錨點 | 與 M 的差別 |
|---|---|---|
| `InitializeDataAccessPool()` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:27-30` | 一樣 |
| **沒有 `InitializeVDBTypes()`** | — | **M 有,I 沒有**。43 支 Control 裡只有 `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI199_Ctl.cs` 有 |
| 業務入口 `Select` / `GetMaintainData` | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:51-68` | 各一行 `ExecPOActionToViewVDB` |
| `CustomTransfer*` 四件套 | `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs:73-105` | **Oracle 兩個逐表 `TransferTable`,SQL 兩個 `throw new NotImplementedException()`** |

`CustomTransferSQLModelToView` / `CustomTransferViewToSQLModel` 直接丟 `NotImplementedException` 是**正確做法**,不是缺陷——這套系統的 I 型只跑 Oracle(`architecture.md §4.6`)。

### 7.2 FormProxy:覆寫的是 `Query`,不是 `InitializeControl`

`Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` 全檔 80 行,兩個覆寫:

```
public override BasicViewVDB Query(BasicViewVDB view)
{
    try { … return m_Ctl.Select(m_vdb); }
    catch (Exception ex)
    {
        CommonExceptionBlocker.HandleFormProxyException(ex);
        BasicViewVDB ExceptionVDB = new BasicViewVDB();
        ExceptionVDB.Util.Result.AddResultRow(false, 0, ExceptionMessage.ServerSideError);
        return ExceptionVDB;
    }
}
```

`Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs:36-52`,另一個是 `GetMaintainData`(`:59-74`)。 **不要覆寫 `Add` / `Update` / `Delete`**——沒有寫入就沒有這三個入口,留著等於給人一條繞過設計的路。

**驗證**:`grep -c "InitializeVDBTypes" <NEW>_Ctl.cs` 應回 0;`grep -c "InitializeDataAccessPool" <NEW>_Ctl.cs` 應回 1。

## 8. 步驟七:UI

### 8.1 現況:基底有兩種,執行鈕要自己關掉

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/` 的 58 個 `.cs`(含彈出子視窗,已排除 Designer)基底分布: `xOneStepProcessForm` **42** · `xQueryForm` 8 · `yPopUpForm` 7(彈出挑選視窗)· `xMaintainForm` 1。

**新畫面用 `xOneStepProcessForm`**,跟 B 批次同一個基底(`architecture.md §6.4` 講的「I 與 B 是同一份樣板」)。它自帶查詢鈕與執行鈕,所以 I 要做兩件事:

```
this.ButtonExecuteEnable = false;                  // FormInitial 就關掉
private void <NEW>_BeforeExecuteButtonClicked(object sender, CancelEventArgs e)
{ e.Cancel = true; return; }                       // 保險再擋一次
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:51` 與 `:197-202`。

`FormInitial` 的四件與 M 相同(`add-screen.md §8.2`),差別是**沒有四眼工具列要掛**: `TabPages` / `ProcessVDB` / `FormProxy` / grid 的 `DataSource`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:35-63`)。

grid 一律設成唯讀:`new GridLayoutManager(new GridLayoutReadOnly())`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:43-46`);要讓使用者勾選的那張才用 `GridLayoutUpdateOnly`(`:41-42`)。欄位白名單同 M:`UltraGridInitialHelper.SetupUltraGridShowColumns`(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:147`),另外 I 常多掛一個二次篩選 `UltraGridInitialHelper.SetupUltraGridFilter`(`:61-62`)。

### 8.2 改法:分頁 = 條件頁 + 結果頁

```
this.TabPages = 2;                       // FormInitial
base.ChangeTabPage(1);                   // 查完自動翻到結果頁
this.ButtonSearchEnable = false;         // 查詢後鎖住查詢鈕
this.udatTRANS_DATE_ST.Enabled = false;  // 條件欄位一併鎖住
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:37` 與 `:204-220`,解鎖在 `RefreshPage`(`:222-244`)。

**這是 ATLAS 的「分頁」,不是資料庫分頁。**整份結果一次撈回用戶端,沒有 `ROWNUM` / `OFFSET` 這類分批。主明細的「點一列帶明細」也在前端做——`DataTable.Select(...)` 過濾已經撈回來的明細,不再打伺服器(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:110-122` 與 `:306-317`)。

> ⚠ **所以查詢條件一定要能有效限縮筆數。**沒有「至少填一個條件」的檢核時,使用者按下去就是全表撈回用戶端記憶體。`CASI001` 就少了這條檢核(`modules/cas.md §5.2`)。

### 8.3 改法:匯出只要一行

```
private void ugrdMaster_Enter(object sender, EventArgs e) { this.ExportGrid = ugrdMaster; }
private void ugrdDetail_Enter(object sender, EventArgs e) { this.ExportGrid = ugrdDetail; }
```

`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:296-304`。 `ExportGrid` 是基底 `xOneStepProcessForm` 的屬性(**無原始碼,從呼叫端反推**),匯出鈕匯的就是它指到的那張 grid;**兩張 grid 就掛兩個 `Enter` 事件**,讓游標在哪張就匯哪張。

要自己產 Excel 或特殊格式的才寫程式(`OFDI911` 那型:PO 提供 `GetExcelData` 回一整個 `DataSet`,`Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs:53-94`),**能用 `ExportGrid` 就不要自己寫**。

### 8.4 改法:UI 端的驗證

`DoValidate` 的形狀與 M 相同(`add-screen.md §8.6`),I 特有的兩條:**每組起迄都要檢查「起 > 迄」**(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:260-288`),並在 `Leave` 事件補「只填起就自動帶迄」(`:246-250`、`:319-323`);**要有「至少填一個條件」的檢核**(§8.2 的警告),`OFDI716` 的版本是「至少勾選一筆基金代碼」(`Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs:75-78`、`:280-284`)。

## 9. 編譯與部署

六個 csproj 全部在 `.Query` 專案底下,加什麼與 M 完全相同(`add-screen.md §10.1`),只是專案名多了 `Query` 前綴: `QueryDataEntity.<MOD>` / `QueryUIEntity.<MOD>` 各 `Compile` × 2 + `None` × 3;`QueryPO` / `QueryControl` / `QueryFormProxy` 各 `Compile` × 1;`QueryUI` `Compile` × 2 + `EmbeddedResource` × 1。

重編順序與部署照 `add-column.md §9.1`、`add-column.md §9.2` 與 `deploy.md §2`——`.Query` 的六個組件在部署對照表裡對應到同樣的欄位(`QueryUI.<MOD>` 佈客戶端、`QueryUIEntity.<MOD>` 兩端都佈、其餘佈伺服端)。

> **〔假設〕缺:PTPFBlock DLL。**整個 §9 未實測(`architecture.md 附錄 C.1`)。csproj 段落形狀來自 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/QueryPO.OFD.csproj` 原文; 部署對照表的 `.Query` 那一列是從 `deploy.md §2` 的 `<MOD>` 通則推的,**`deploy.md §2` 本身沒有單獨列 `.Query`**。

## 10. 驗證清單

| # | 動作 | 過的條件 | 沒過回去做 |
|---|---|---|---|
| 1 | `atlas_scan.py --screen <NEW>` | 六層都有路徑;「主檔 —」是正常的 | §3 §9 |
| 2 | 確認 PO 基底 | 印出來是 `BaseEVADaoPO` 或只有 `I<NEW>_PO` | §4.2 |
| 3 | 依 `add-column.md §9.1` 順序重編六個專案 | 六個都成功 | §9 |
| 4 | 開畫面 | 版面出得來、**執行鈕是灰的** | §8.1 |
| 5 | 什麼條件都不填按查詢 | 被擋住並提示「至少…」 | §8.4 |
| 6 | 只填「迄」不填「起」;起 > 迄 | 兩者都被擋住 | §8.4 |
| 8 | 正常條件查詢 | 有資料;自動翻到結果頁;條件欄位鎖住 | §8.2 |
| 9 | 查無資料的條件 | 回「查無資料」而不是空白訊息 | §6.5 |
| 10 | 點主檔某一列,再把游標留在明細 grid 按匯出 | 明細 grid 跟著換;匯出的是明細不是主檔 | §8.2 §8.3 |
| 11 | 條件輸入含單引號的值 | **不可**出現 SQL 語法錯 | §6.2 |

**第 9、11 最容易失敗**:前者驗例外路徑,後者驗參數化。

## 11. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **開畫面就 `NullReferenceException`** | PO 繼承了 `BasicEVAPO`,`dbTA` 恆為 null | §4.1、`add-screen.md §5.7` |
| **編譯過,執行期找不到 `<NEW>ViewVDB`** | xsd 進了資料夾但 csproj 沒掛 `Generator` | §3.1、`add-screen.md §3.5` |
| **查詢永遠零筆,DB 卻有資料** | `LoadDataSet` 的表名打成字串常值且拼錯 | §5.2 |
| **`ORA-00904`,欄名是 `STATUS` 或 `DATAID`** | SQL 抄了 M 的 `AllEVAColumnsForSelect` | §3.2 |
| **查詢條件填了沒作用** | UI 的 `AddParametersRow` 與 PO 的 `FindByName` 字串不同 | §6.2 第 3 條 |
| **某類資料永遠查不到 / 某人看得到全部人的資料** | SQL 裡有畫面上看不到的硬條件;或限縮條件的參數取不到時被當成「沒有條件」 | §6.3 §6.4 |
| **代碼有值但說明欄空白** | `LEFT JOIN` 的分類碼寫死,值域改了 | §6.4 第 4 列 |
| **輸入含單引號的值就「執行失敗,請檢查」** | 字串串接沒跳脫 | §6.2 |
| **匯出永遠匯主檔;筆數一多畫面就卡住** | 只掛了一個 grid 的 `Enter` 事件;或沒有「至少填一個條件」,全表撈回用戶端 | §8.2 §8.3 |
| **掃描器說缺 PO** | 該專案用 `<代號>OracleDao.cs` 命名 | §4.3 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI716_PO.cs` | `:21` `:22` `:64-95` `:90-95` `:99-108` `:101-104` `:111` `:160` `:162-173` `:175-179` | §4 §5 §6 |
| `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI716_Ctl.cs` | `:27-30` `:51-68` `:73-97` `:73-105` | §5.2 §7.1 |
| `Dev/ATLAS.OFD.Query/Source/FormProxy/QueryFormProxy.OFD/OFDI716_Pxy.cs` | `:36-52` `:59-74` | §7.2 |
| `Dev/ATLAS.OFD.Query/Source/UI/QueryUI.OFD/OFDI716.cs` | `:35-63` `:37` `:41-46` `:51` `:61-62` `:75-78` `:86-93` `:98-102` `:110-122` `:147` `:197-202` `:204-220` `:222-244` `:246-250` `:260-288` `:280-284` `:296-304` `:306-317` `:319-323` | §6 §8 |
| `Dev/ATLAS.OFD.Query/Source/Entity/QueryDataEntity.OFD/OFDI716Model.xsd` · `Dev/ATLAS.OFD.Query/Source/Entity/QueryUIEntity.OFD/OFDI716View.xsd` | 全檔 | §3 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/QueryPO.OFD.csproj` | 全檔 | §9 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI911_PO.cs` | `:27` `:28` `:30` `:53-94` | §4.1 §8.3 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI719_PO.cs` | `:11` `:30` | §4.1 |
| `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI059_PO.cs` · `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/OFDI199_PO.cs` · `Dev/ATLAS.OFD.Query/Source/Control/QueryControl.OFD/OFDI199_Ctl.cs` | `:17` / `:39` / 全檔 | §5.1 §7.1 |
| `Dev/ATLAS.EC.Query/Source/PO/QueryPO.EC/Oracle/OFDI641OracleDao.cs` · `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` | 全檔 | §2.1 §4.3 |
| `Dev/ATLAS.OFD/Source/PO/PO.OFD/OFDM125A_PO.cs` | `:28` `:30` | §4.2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs` | `:152-183` `:185-186` `:206-207` `:219` `:329` `:345` | §6.1 §6.3 §6.4 |
| `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASI001.cs` · `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM006Model.xsd` | `:135-136` / 全檔 | §3.2 §6.3 |
| `Dev/Common/Source/Utility/TA.ServerUtility/OracleHelper.cs` | `:114-133` | §3.2 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **DB 連線** | §6.4 §10 | `> =` 那條只能標假設;查詢結果的正確性、日期字串比較的實際資料格式都無法驗 |
| **PTPFBlock DLL** | §9 §10 | 六層重編全未實測 |
| **選單 / 權限表** | §2 §10 | 新查詢畫面怎麼掛進選單、怎麼授權,與 `add-screen.md §9` 同一個缺口;`CASI001` 那種「權限寫死在 SQL」的替代做法也要等這個輸入 |
| **`deploy.md` 的 `.Query` 專用列** | §9 | 目前是從 `<MOD>` 通則推的,補上之後 §9 改成直接引用 |

## 附錄 C 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。以 `add-screen.md` 為底做差異版;PO 基底分布實測 `Dev/ATLAS.OFD.Query/Source/PO/QueryPO.OFD/` 全部 43 支,深讀 `OFDI716` / `OFDI911` / `OFDI719` 三支 |

由 build_doc.py v2.0.0 於 2026-09-15 17:56 產生 · 標題 38 · 圖 2 · 表格 16 · 程式錨點 68 · § 連結 80 · 引用檢查：畫面 12（缺 0） · 結果集 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/add-batch.md
============================================================

# ATLAS 維護手冊 — 新增 / 維護一支 B 批次

> 產出日期:2026-09-15(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 ⚠ 標「**〔假設〕缺:輸入**」的是拿不到輸入(DB 連線 / PTPFBlock DLL / 選單表 / 部署機)只能推論的部分,附錄 B 彙整;標「**〔客戶特定〕**」的是本站台的值。

> 前提知識在 `architecture.md`:六層與重編順序 `architecture.md §2`、交易邊界 `architecture.md §4.5`、畫面型別 `architecture.md §6.4`、Remoting 與服務 `architecture.md §8.4`。**不要整份讀**。六層樣板細節引用 `runbooks/add-screen.md`,部署引用 `runbooks/deploy.md`,都不重複。素材:`modules/ofdb.md`(18 支)、`modules/ofdb3.md`(35 支)、`modules/ofdb4.md`(35 支),合計 88 支已寫深的批次。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | **新建或維護一支 B(批次)畫面**:按一顆執行鈕、跑一段伺服端作業、改 DB 或產檔 |
| 主要範本 | `OFDB003` 受益人異動批次轉入(**沒有** Remoting 設定、沒有服務,交易由 C# 開) |
| 對照範本 | `OFDB600` 網路交易時限截止(**有** Remoting 設定、有 WindowsService、排程時刻在 DB) |
| 不適用 | M 維護畫面(`runbooks/add-screen.md`)· I 查詢畫面(`runbooks/add-query-screen.md`)· R 報表(`runbooks/add-report.md`) |
| 前提工具與變數 | Visual Studio · Oracle 客戶端 · PTPFBlock DLL · TFS workspace;`%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 佈位符 | `<NEW>` = 新代號 · `<MOD>` = 模組 |

### 0.1 一句話版本與八個步驟

**B 就是 M 拔掉四眼、UI 換成一步式表單。**六層一層都不少,csproj 一個都不能漏。 `architecture.md §6.4` 已證明「I 與 B 是同一份 143 行樣板複製刪減出來的」,B 比 I 多的只有寫入那條路徑。所以本手冊只講**批次特有**的五件事:專案怎麼選、怎麼被觸發、要不要 Remoting、交易誰開、失敗怎麼回報。

| # | 步驟 | 樣板程度 | 節 |
|---|---|---|---|
| 1 | 決定代號與**放哪個專案** | **要查** | §2 |
| 2 | 決定觸發方式(四種) | **要決定** | §3 |
| 3 | 決定要不要 Remoting | **要決定** | §4 |
| 4 | Entity 兩份 xsd + 選卷別 | 半樣板 | §5 |
| 5 | PO:交易、參數、SP、出口 | **全篇重點** | §6 |
| 6 | Control 與 FormProxy | 逐字樣板 | §7 |
| 7 | UI,必要時加 WindowsService | 半樣板 | §8 §9 |
| 8 | 六個 csproj + 編譯部署 | 樣板 | §10 |

## 1. 改動點總覽(圖)

```text
[圖] 批次專案結構:三個專案怎麼選、六層、Entity 分卷、選配的 WindowsService
圖中文字:① 先決定放哪個專案 —— 全庫沒有 Batch 資料夾 / ATLAS.OFDB / 108 支 PO,本業批次的家 / ATLAS.EC / 36 支,網路交易與服務 / ATLAS.OTAB / 41 支,境外平台 / 跟著表走 / 讀寫哪張表就住哪 / ② 六層跟 M 完全一樣,只是 UI 基底不同 / UI <NEW>.cs / xOneStepProcessForm / FormProxy <NEW>_Pxy / 覆寫 Execute / Query / Control <NEW>_Ctl / 只覆寫 DataAccessPool / PO 裸 DAO / 自己 new Database / ③ Entity 兩份 xsd —— 選卷別,不要新開專案 / DataEntity 四卷 / OFDB / 1 / 2 / 3 / UIEntity 四卷 / 卷號必須配對 / 放最大卷 / OFDB3 已 41 份 / View 可精簡 / 批次常只放結果 / ④ 選配第五件:WindowsService(全庫只有四支有) / WindowsService 專案 / 獨立 exe,自帶 config / ProjectInstaller / 帳號 LocalSystem / App.config / Remoting 段在這 / 不重寫邏輯 / 只是另一個呼叫端
```

*圖:圖 1 批次放哪裡。橘色實框=這一步要自己決定;灰虛框=照抄樣板;橘色虛框=只有四支批次會用到、而且是〔客戶特定〕的部署件。全庫沒有 Source/Batch 資料夾,B 畫面就住在六層裡。*

三件事先記住:

1. **沒有 `Source/Batch/` 這種資料夾。**`find Dev -maxdepth 4 -type d -iname "Batch*"` 回 0 筆。B 畫面住在跟 M 完全一樣的六層裡,差別只在代號第四碼是 `B`、UI 基底是 `xOneStepProcessForm`。

2. **代號決定不了專案。**`OFDB` 開頭的批次散在三個專案,見 §2。

3. **批次的失敗是靜默的。**沒有使用者盯著、沒有四眼留痕跡,所以 §6.5 的失敗回報比 M 畫面重要得多。

## 2. 步驟一:決定代號與放哪個專案

### 2.1 現況:`OFDB` 代號散在三個專案

先 `ls` 確認,不要照代號猜:`ls Dev/ATLAS.OFDB/Source/` 得到 `Control Entity FormProxy PO UI`——沒有 Batch。再 `find Dev -name "OFDB*_PO.cs" -o -name "OFDB*OracleDao.cs" | grep -v /obj/`,實測分布:

| 專案 | PO 檔數 | 負責什麼 | 依據 |
|---|---|---|---|
| `Dev/ATLAS.OFDB` | 108 | 本業批次:結帳、過帳、產檔、集保、核印扣款 | `ofdb.md §3.3`、`ofdb4.md §0.4` |
| `Dev/ATLAS.EC` | 36 | 網路交易(EC)相關,三支 WindowsService 也在這 | `ofdb3.md §3.3` |
| `Dev/ATLAS.OTAB` | 41 | 境外平台(OTA)那一套 | `ofdb3.md §3.3` |

全庫 B 畫面 UI 檔分布(排除 Designer):`ATLAS.OFDB` 150 · `ATLAS.OTAB` 45 · `ATLAS.EC` 40 · `ATLAS.RSP` 18 · `ATLAS.COD` / `ATLAS.CRM` 各 5 · `ATLAS.BMS` 3 · `ATLAS.CAS` / `ATLAS.SDM` 各 2 · `ATLAS.DSM` 1。

**同一個代號可能在兩個專案各有一份。**`OFDB562` / `OFDB563` / `OFDB564` 在 `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/` 與 `Dev/ATLAS.OTAB/Source/PO/PO.OTA/` 各有一份,不是分岔而是新舊世代;`ATLAS.OFDB` 那三份的基底連線恆為 null,實際跑不起來(`ofdb3.md §2.5`)。

### 2.2 改法:三條決定規則 + 取號

依序套,第一條命中就停:

| # | 規則 | 為什麼 |
|---|---|---|
| 1 | **跟著它要寫的表走。**表由哪個模組的 M 畫面維護,批次就放那個模組 | 重編時 Entity 與 PO 的 `ProjectReference` 才不會跨專案(`architecture.md §2.4`) |
| 2 | **跟著同群連號的既有支走。**`OFDB701`–`OFDB707` 全在 `ATLAS.OFDB`、`OFDB6xx` 多半在 `ATLAS.EC` | 同群常共用 helper 與 entity,拆開就要多一組 `ProjectReference` |
| 3 | **要 WindowsService 就放 `ATLAS.EC` 或 `ATLAS.RSP`。**全庫只有這兩處有 `Source/WindowsService/` | `deploy.md §5` 的四支服務全在這兩處 |

**境外平台(OTA)的批次一律放 `Dev/ATLAS.OTAB`**,即使代號叫 `OFDB6xx`(`OFDB600A` / `OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 全在 OTAB,`ofdb3.md §3.3`)。

取號:同模組同型別最大號 +1,避開 `9xx`(慣例保留給對外申報與跨模組工具)。 **`A` 後綴在批次上沒有一致意義**(`ofdb3.md §0.2`:`OFDB600` 與 `OFDB600A` 是不同業務、不同專案),**新批次不要用 `A` 後綴表達任何語意**。

### 2.3 驗證

`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen <NEW>` 回「找不到」才是對的(代號還沒被用)。建完再跑一次,六層要全部列得出來。

## 3. 步驟二:決定觸發方式

```text
[圖] 批次的四種觸發方式:手動、被別支批次呼叫、WindowsService 的 60 秒 Timer、排程時刻存在資料庫欄位
圖中文字:觸發來源 —— 四種,只有前三種在 repo 裡看得到 / ① 手動按執行 / xOneStepProcessForm / ② 被別支批次叫 / Pxy 再包一層 / ③ 服務 60 秒 Timer / 比對 HHmm 字串 / ④ 時刻在 DB / 改欄位不重編 / ④ 的細節:時刻欄由 SQL 五段 UNION 撈出來 / OFD606A 四個時間欄 / 申購 匯款 贖回 定額 / OFD600A 一個時間欄 / MEMBER_CHG_LIMIT / GetTIMES 算最近一次 / 存成 HHmm 字串 / 跑完再算 / finally 重算 / 四種觸發最後都收斂到同一個入口 / FormProxy.Execute / 唯一入口 / Control.Execute / 取 PO 實例 / PO.Execute / 交易 + SP + 出口 / ⚠ 帳號決定跑不跑 / UserName 判斷
```

*圖:圖 2 四種觸發。第四種是本手冊最容易被忽略的一條:排程時刻不在 Windows 排程器、也不在設定檔,而是資料表的欄位;改時間不用重編,但也查不到是誰設的。*

### 3.1 現況:四種,不是三種

| # | 觸發 | 在 repo 裡怎麼看出來 | 幾支 |
|---|---|---|---|
| 1 | **手動**:使用者按「執行」 | UI 繼承 `xOneStepProcessForm`,有 `BeforeExecuteButtonClicked` | 絕大多數 |
| 2 | **被別支批次呼叫** | 另一支的 Ctl / PO 裡 `new <代號>_Pxy()` | 少數 |
| 3 | **WindowsService**:獨立 exe,60 秒 Timer | `Dev/<專案>/Source/WindowsService/WindowsService.<代號>/` 存在 | **4 支** |
| 4 | **排程時刻存在資料庫**:服務每分鐘比對 `HHmm` | 服務的 `GetTIMES()` 去撈時刻欄 | 3 支 |

第 3 與第 4 疊在一起:服務提供「每分鐘檢查一次」的心跳,**真正的排程時間在資料表欄位裡**。

### 3.2 現況:第四種的完整機制(本手冊最值得記住的一段)

以 `OFDB600` 為例:

| 步 | 做什麼 | 錨點 |
|---|---|---|
| 1 | 建構子掛 `Interval = 60000`(60 秒)的 `System.Timers.Timer` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:24-31` |
| 2 | `OnStart` 先讀自己的 `exe.config` 設 Remoting,再 `GetTIMES()` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:39-58` |
| 3 | `GetTIMES()` 透過 Pxy 撈候選時刻,各加 `LIMIT_TIME_BUFFER` 分鐘,已過的推到明天,取最近一個存成 `"HHmm"` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:109-155` |
| 4 | 每分鐘比對 `sTIMES == DateTime.Now.ToString("HHmm")`,相等才跑 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:65-75` |
| 5 | 跑完 `finally` 再 `GetTIMES()` 算下一次 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:103-106` |

候選時刻的 SQL 是五段 `UNION`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292`):`OFD606A` 的申購 / 匯款 / 贖回 / 定額四個截止時間欄(各被對應的 `*_YN = 'Y'` 過濾)再 `UNION` `OFD600A` 的 `MEMBER_CHG_LIMIT_TIME`。`OFDB609` 讀 `OFD600A`、`OFDB680` 讀 `OFD680A`(`ofdb3.md §3.3`)。

> ⚠ **要改排程時間,不用重編、也不用碰 Windows 排程器,改資料表欄位就好。** 反過來說:**排錯時間時查不到「是誰設的」**——這些欄位由哪支 M 畫面維護,三片批次篇都沒查到。

### 3.3 改法:新批次選哪一種

| 需求 | 選 | 要做什麼 |
|---|---|---|
| 人工決定什麼時候跑 | ① 手動 | 只做六層,不加服務 |
| 固定時間跑,時間**不會改** | ③ 服務 + 時刻寫 `App.config` | 加一個 WindowsService 專案(§9) |
| 固定時間跑,時間**業務會調** | ③ + ④ 服務 + 時刻欄放 DB | 同上,再加設定表欄位與維護它的 M 畫面 |
| 跟在別支批次後面 | ② 被呼叫 | 在前一支的 Ctl 裡 `new <NEW>_Pxy()` |

**預設選 ①。**88 支樣本裡只有 3 支走到第四種;多一支服務就多一台要部署、要監控、要處理帳號的機器(§9.2)。

### 3.4 改法:`Main(string[] args)` 的參數慣例

**先確認現行主流寫法:沒有 `args`。**`ofdb3.md §6.1.3` 實測那 35 支:`Main()` 一律不收 `string[] args`,repo 內也沒有任何 `.bat`;`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13` 的簽名就是 `static void Main()`。

參數有三個來源,**全部按名字取,不是按位置**:

| 來源 | 怎麼取 | 錨點 |
|---|---|---|
| 畫面欄位 | UI 端 `Util.Parameters.AddParametersRow("<名>", SQLOperator.Equal, 值)` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:43-48` |
| 服務自動跑 | 服務端自組同一組 `AddParametersRow`,使用者寫死字串 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:84-86` |
| 設定表 | PO 自己去撈 | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:268-292` |

PO 端的樣板(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:55-62`):

```
if (vdb.Utility.Parameters.Rows.Contains("CHECK_DATE"))
{
    DataModelUtility.ParametersRow Row = (DataModelUtility.ParametersRow)vdb.Utility.Parameters.Rows.Find("CHECK_DATE");
    if (!string.IsNullOrEmpty(Convert.ToString(Row.Value)))
        db.AddInParameter(cmd, "wCHECKDATE", OracleDbType.Date, ConvertTo.DateTimeorDBNull(Convert.ToDateTime(Row["Value"])));
}
```

`OFDB003` 用包好的 `GetParamValue`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:72-78`),兩種都可以。

**「位置取參數」是已知缺陷,但它不在 `Main()`,在讀檔與下拉選單:**

| 缺陷型 | 實例與錨點 |
|---|---|
| 用陣列索引取 CSV 欄位 | `OFDB560` 的 `strData[0]`~`strData[14]`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs:64`、`:72-84`),上游調欄序就整批對錯 |
| 用列索引隱藏下拉選項 | `OFDB019A` 的 `ucomMSG_TYPE.Rows[3].Hidden = true`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs:42`) |
| 用選鈕索引換算 SP 參數 | `OFDB019B` 的 `CheckedIndex + 2`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs:78`) |
| 固定位移拆字串 | `OFDB901` 的 `Substring(0,11)` + `Substring(11,4)`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs:73`) |

**怎麼避:任何「第 N 個」都要換成「叫什麼名字」。**讀檔用表頭比對欄名、下拉用 `TextValue` 找、拆字串用分隔符。真的是定長檔案格式時,把位移抽成具名常數集中宣告,不要散在四個方法裡(`OFDB950` 的反例:`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs:86`、`:120`、`:146`、`:183`)。

### 3.5 驗證

手動:執行鈕亮得起來。服務:`sc start <NEW>_Service` 後看事件檢視器有沒有 `Execute Error`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:92`)。第四種:把時刻欄改成「現在 + 2 分鐘」,兩分鐘內應該要跑;不跑先查 §12 的「服務在跑但不動作」。

## 4. 步驟三:要不要 Remoting

### 4.1 現況:同一批批次,有的有有的沒有

`ofdb3.md §3.4` 把三個專案的 **20 個 `App.config` 全部查過**:

| `App.config` | `system.runtime.remoting` | `<wellknown>` | `<connectionStrings>` |
|---|---|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | **有**(`:175-194`) | **1 個**(`:189`) | 無 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` | **有**(`:175-194`) | **1 個**(`:189`) | 無 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config` | **0 個** | 0 | **有(3 筆,`:246-262`)** |
| 其餘 17 個(UI / PO / Control / FormProxy / Entity 各層) | 0 | 0 | 無 |

> ⚠ 那三筆 `<connectionStrings>` **含明文帳密**。本手冊只記位置(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config:246-262`),**不抄值**。`architecture.md §8.7` 已標同型問題。

### 4.2 現況:`OFDB680` 少了 `<wellknown>`,結果是什麼

三支服務的 `OnStart` 幾乎逐字相同,都呼叫 `RemotingConfiguration.Configure(自己的 exe.config)`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:50-52`)。但 **`<wellknown>` 才是讓 `new <代號>_Pxy()` 變成遠端代理的那一行**。沒有它,`new` 出來的是本機物件,`FormProxy → Control → PO` 全跑在服務自己的行程裡——這正好解釋為什麼只有它的 config 需要 `<connectionStrings>`。

| 類型 | 誰 | 那台機器需要什麼 |
|---|---|---|
| **真 Remoting 客戶端** | `OFDB600`、`OFDB609` | Remoting 端點設定;**不需要**資料庫權限 |
| **直連資料庫的行程** | `OFDB680`、`RSPB008` | `TA` / `SWProduct` / `Logging` 三個帳號的連線權限 |

> 〔假設〕`OFDB680` 是設定檔漏了 Remoting 區段,不是刻意設計——依據是三支的 `OnStart` 幾乎逐字相同。但 `<connectionStrings>` 又不像意外多出來的,**兩種解釋都成立,沒有註解可判**(`ofdb3.md §3.4`)。

### 4.3 改法:新批次怎麼決定

**只有一個判準:這支批次會不會以「非 UI 的宿主」去打伺服端的 FormProxy。**

| 情境 | 要不要自己的 Remoting 設定 | 做法 |
|---|---|---|
| 只有畫面觸發(①)或被同行程的批次呼叫(②) | **不要** | 什麼都不加。Remoting 邊界由主程式管,落在 UI → FormProxy 之間(`architecture.md §8.1`) |
| 有服務,而且邏輯要跑在伺服端(③④) | **要** | 抄 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:175-194`,把 `<wellknown>` 的 `type` 與 `url` 換成 `<NEW>_Pxy` |
| 有服務,而且就是要在服務那台直連 DB | **不要,但要 `<connectionStrings>`** | 照 `RSPB008` 的形狀(`architecture.md §8.4`):csproj 參考 `Control.<MOD>` 而不是 `FormProxy.<MOD>` |

**不要學 `OFDB680`:程式碼呼叫 `RemotingConfiguration.Configure` 卻沒有 `<wellknown>`。**兩種都合法,混在一起是最難查的那種。

### 4.4 驗證

拿掉 DB 權限後在服務那台跑:走 Remoting 的應照常成功(它不碰 DB);沒走 Remoting 的會在第一個查詢失敗。**〔假設〕缺:部署機**,未實測。

## 5. 步驟四:Entity —— 兩份 xsd 與卷別

### 5.1 現況:批次的 xsd 裝的多半不是實體表

`ofdb.md §2.3` 與 `ofdb4.md §2.8` 都查過:批次 Model 裡的 DataTable **大半是「SP 的 RefCursor 出參形狀」**,不是實體表。`OFDB003` 的 Model 有 10 張 DataTable,其中 5 張對應 SP 的 5 個 RefCursor(`Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd`,352 行);它的 View 只有 79 行(`Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/OFDB003View.xsd`)。

**批次的 View 通常比 Model 精簡很多**,因為只有要顯示的那幾張才需要送回用戶端。這點和 M 相反:M 的兩份幾乎逐字相同(`add-screen.md §4.1`)。

### 5.2 改法:卷別怎麼選,後綴怎麼取

`Dev/ATLAS.OFDB/Source/Entity/` 底下有**四組** Entity 專案,實測 `.xsd` 數:`OFDB` 19 / `OFDB1` 18 / `OFDB2` 27 / `OFDB3` **41**(UIEntity 側 19 / 17 / 27 / 41)。

規則和 M 一樣(`add-screen.md §10.2`):**放進編號最大的那一組**(這裡是 `OFDB3`),**Model 與 View 的卷號必須配對**。分卷是為了避開 typed DataSet 專案過大,不是業務分群(`ofdb4.md §0.4`)。 `ATLAS.EC` 的批次 entity 全在 `DataEntity.EC` / `UIEntity.EC`(不分卷);`ATLAS.OTAB` 在 `DataEntity.OTA` / `UIEntity.OTA`(組件名是 `DataEntity.OTAB`)。

**`_9i` 後綴不要再用。**`OFDB600` 的 xsd 叫 `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd` / `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/OFDB600_9iView.xsd`;`_9i` 是第二代控件的後綴(`architecture.md §7.3`),掃描器會因此判「缺 entity」(`ofdb3.md §3.5` 列了 8 支)。**新批次一律 `<NEW>Model.xsd` / `<NEW>View.xsd`。**

### 5.3 現況:可以少建這兩層,但不建議

`architecture.md §6.6` 實測:B 型有 28 支**沒有 DataEntity + UIEntity**,是四型裡唯一常態性少層的,條件是「跑完不回傳任何資料集」。但建 xsd 的成本是十分鐘(全是樣板),省下來換的是「以後要顯示任何東西都得回頭補兩份 xsd 與六個 csproj 段」。**新批次一律建齊。**

### 5.4 驗證

xsd 骨架、10 個 `msprop`、csproj 三段全照 `add-screen.md §3`。批次特有的只有一條:`atlas_scan.py --screen <NEW>` 的 `DataEntity` 與 `UIEntity` 兩列要有路徑;**「主檔 —」是正常的**,批次不宣告 `xTableMapping`(§6.1)。

## 6. 步驟五:PO —— 全篇重點

```text
[圖] 批次的執行流程與失敗處理:UI 驗證、C# 開交易跑 SP、commit 後才做不可回復的動作、三條失敗路徑
圖中文字:① 按下執行之前 —— UI 端,唯一能真的擋住的地方 / DoValidate 必填 / validatorManager1 / 組 Parameters / AddParametersRow / Pxy.Check 前置查詢 / 數一數會動幾筆 / e.Cancel = true / 不設就照跑 / ② PO 裡的交易邊界 —— C# 開、C# 關,SP 跑在裡面 / GetStoredProcCommand / 先建 cmd 再開交易 / BeginTransaction / 一定寫在 try 裡面 / LoadDataSet 帶 tran / SP 參與同一交易 / 看回傳再決定 / 不要寫死 i = 1 / ③ 兩條出口 —— Commit 之後才做不可回復的事 / Commit / 先落地 / 寄信 / 產檔 / 呼外部 / commit 之後才做 / AddResultRow(true, n) / n 要是真筆數 / 換頁顯示結果 / ExecuteDataLoad / ④ 失敗路徑 —— 三條,每一條都要留下原因 / Rollback 前檢查 null / 否則 NRE 蓋掉原因 / 訊息不可空字串 / 空訊息 = 查不到 / 寫 log 表或 EventLog / repo 內無統一 log 表 / 禁止空 catch / 吞了就永遠不知道
```

*圖:圖 3 執行流程與失敗處理。橘色實框=新批次一定要自己寫對的地方;橘色虛框=現存批次最常寫錯、而且錯了不會有人發現的地方。順序不可調換:寄信與產檔一律排在 Commit 之後。*

### 6.1 現況:四種世代,新的只用第一種

`ofdb4.md §0.3` 把 35 支逐支查過:

| 世代 | 基底 | 連線 | 宣告 `xTableMapping` | 支數 |
|---|---|---|---|---|
| **裸 PO(主流)** | 無基底,只實作 `I<代號>_PO` | 自己 `new Database("TA", DbServerType.Oracle)` | 無 | 22 |
| EVA 滿血 | `BaseEVADaoPO` | 基底管(`dbProduct`) | 有 | 3 |
| MultiRow EVA | `BaseMultiRowEVADaoPO` | 基底管 | 有 | 1 |
| **舊世代(禁用)** | `BasicEVAPO` | **`dbTA` 恆為 null** | 多半無 | 5 |

**新批次用裸 PO。**批次的輸出是 DB 狀態改變或外部檔案,不是回傳資料集,不需要 `xTableMapping`,四眼那套也用不上。 **絕對不要繼承 `BasicEVAPO` / `MultiRowEVAPO`**,連查詢都會 NRE(`add-screen.md §5.7`、`architecture.md §3.1.1`)。

### 6.2 改法:骨架五件

`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs` 全檔 508 行:

| 件 | 錨點 | 內容 |
|---|---|---|
| 介面 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:20-29` | `public interface IOFDB003_PO { T Execute<T>(T model, params object[] args); … }`——**不繼承 `IEvaDataAccess`** |
| 類別宣告 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:32-33` | `[PODbType(DbServerType.Oracle)]` + `: IOFDB003_PO`,沒有基底 |
| 連線欄位 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:36` | `Database dbTA = new Database("TA", DbServerType.Oracle);` |
| `Execute<T>` | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:57-155` | 交易 + SP + 判斷 + Commit / Rollback |
| 前置檢查 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:315-322` | `Check<T>`,給 UI 在按執行前問一次 |

要兩個庫(`TA` + `SWProduct`)就宣告兩個 `Database`,但**沒有分散式交易**,兩邊各自 Commit(`architecture.md §4.5`);一邊成功一邊失敗就對不起來。**能只用一個庫就只用一個。**

### 6.3 改法:交易邊界誰開 —— C# 開,SP 跑在裡面

`ofdb.md §6.0` 的總表:18 支裡 17 支是 **C# 端 `BeginTransaction`,SP 參與同一交易**,只有 1 支走 EVA 基底讓框架管。照抄的順序(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:62-119`):

```
DbTransaction tranUpdate = null;
try
{
    DbCommand cmd = dbTA.GetStoredProcCommand("s_TA_OFDB003_Excute");
    // 綁 IN 參數(按名字取,見 §3.4);綁 OUT 參數:RefCursor 一張表一個
    tranUpdate = dbTA.BeginTransaction();
    dbTA.LoadDataSet(cmd, mModel.DataEntity, tranUpdate, new string[] { "OFDB003", … });
    // 判斷結果,不成立就 Rollback
    if (tranUpdate.Connection != null) { tranUpdate.Commit(); }
}
```

五條規則:

1. **`BeginTransaction()` 一定寫在 `try` 裡面。**寫在外面時,開交易本身失敗的例外會穿過 PO 打到 FormProxy,使用者看到框架錯誤(`OFDB608` / `OFDB616` 的反例,`ofdb3.md` E5.8)。

2. **`Commit` / `Rollback` 之前檢查 `tranUpdate.Connection != null`。**`OFDB003` 有做(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:100-101`、`:118-119`);沒做的會在 catch 裡再噴一個 `NullReferenceException`,**把原始例外蓋掉**。

3. **執行 SP 一定把 `tran` 傳進去**,否則 SP 跑在自己的交易裡,C# 的 Rollback 管不到它。

4. **`finally` 裡釋放**:`if (tranUpdate != null) { dbTA.Dispose(tranUpdate); } else { dbTA.Dispose(); }`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs:148-153`)。

5. **不要抄 `CommandTimeout = 0`。**全庫 9 處以上寫著「此程式讓它永久跑」(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:51`),卡住的 SP 不會超時,只會一直佔連線。新批次給一個明確秒數。

### 6.4 改法:重跑安全

`ofdb3.md §3.3` 把 35 支分四類:`阻擋` 6 · `覆蓋` 4 · **`不保護` 19** · `不可執行` 4。 **「不保護」是現況的多數,不是可以照抄的慣例。**新批次二選一:

| 做法 | 怎麼寫 | 適用 | 實例 |
|---|---|---|---|
| **先 DELETE 再 INSERT(覆蓋)** | 用一把能唯一決定本批範圍的鍵先 `DELETE`,同一交易內再寫 | 產出型(產名單、產檔、產申報資料) | `OFDB570` 先 `DELETE … WHERE Data_ID`、`OFDB671` 先 `DELETE OFD678A` |
| **已處理旗標(阻擋)** | 來源列有處理碼欄,只撈 `= '0'` 的,跑完改成 `'1'` | 交易處理型 | `OFDB600` 靠七張表的處理碼欄過濾(`ofdb3.md §6.1`) |

**用「覆蓋」時那把鍵必須是決定性的。**`OFDB680` 的重跑鍵是「基金清單 + 日期 + `-1`」拼出來的字串,中途基金上下架就變了鍵值,舊資料刪不掉、重跑會重複(`ofdb3.md` E12.6)。 **用「旗標」時,旗標與撈取條件要寫在同一支 SQL 裡。** 另外,提供「取消 / 回復」功能是 ATLAS 既有慣例(`OFDB222` 取消關帳、`OFDB286` 取消退匯、`OFDB281` 有「重新產生」與「刪除」,`ofdb.md §6.0`)。**能做就做,它比 rollback 好用。**

### 6.5 改法:失敗回報 —— 不可吞例外

三片批次篇的附錄 E 裡,「一律回報成功」與「例外被吞」合計 20 條以上,是**批次的頭號坑**。規則:

| # | 規則 | 反例 |
|---|---|---|
| 1 | **`catch` 一定要留下原因**,訊息不可是 `string.Empty` | `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:100` |
| 2 | **不可有空 `catch { }`** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151`,整個時刻消失且無 log |
| 3 | **不要寫 `catch (SqlException)`**,連線是 Oracle,這個 catch 永遠進不去,是死碼 | 全庫 6 處以上(`ofdb3.md` E2.5) |
| 4 | **例外要進 `CommonExceptionBlocker.HandleBusinessException(ex)`** | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:133-138` 連這行都沒有 |
| 5 | **回傳的 VDB 要和塞訊息的 VDB 是同一個** | `OFDB615` / `OFDB616` 訊息寫進輸入的 vdb、回傳新建的 result,呼叫端看不到失敗(`ofdb3.md` E4.6) |

**寫哪張 log 表?repo 內沒有統一的批次 log 表。**現況三條各走各的:

| 管道 | 誰在用 | 位置 |
|---|---|---|
| `Utility.Result`(回給畫面) | 全部 | `AddResultRow(bool, int, string)` |
| `CommonExceptionBlocker`(框架 log) | 多數 PO | 落地在 `C:\Vendor\VendorProduct\*.log`(`architecture.md §8.5`)〔客戶特定〕 |
| Windows `EventLog` + 自寫文字檔 | 三支服務 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:92`、`:239-252` |

**新批次三條都走。不要抄那個自寫文字檔的 `WriteLog`**——它先整檔讀進記憶體再整檔覆寫,複雜度 O(n²),寫到一半當掉整天的 log 就沒了(`ofdb3.md` E9.5)。

### 6.6 改法:出口有四種,順序不可調

| 出口 | 幾支(35 支樣本) | 規則 |
|---|---|---|
| 呼叫 SP,DB 狀態被改 | 18 | 一定帶 `tran`;SP 回的 RefCursor 要接進 Model |
| C# 自己組 SQL 寫表 | 12 | 參數化(§14.8);`ExecuteNonQuery` 的回傳值**要用** |
| 產生 / 讀取外部檔案 | 6 | 明確指定編碼,不要 `Encoding.Default` |
| 寄信 / 呼叫外部 API | 8 | **一律排在 `Commit` 之後** |

數字出自 `ofdb3.md §6.0`(同一支可能有多個出口,相加大於 35)。

> ⚠ **最後一條是硬規則。**`OFDB600` 在 `tran.Commit()` **之前**就 `SendMail`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:75-76` 對 `:84`):commit 失敗時信已寄出、資料卻回滾。寄信、產檔、呼叫外部系統都是不可回復的動作,**放在交易裡等於把交易的保證作廢**。

`OFDB003` 做對了這件事:LDAP 同步排在 `Execute` 回來之後(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:59-61`),但它換了另一個問題——LDAP 失敗時把 `Result` 清掉改塞失敗訊息,**使用者看到「失敗」,DB 其實已經生效**(`ofdb.md §6.1`)。正確做法是**兩個結果分開回報**。

### 6.7 驗證

| # | 查什麼 | 怎麼查 |
|---|---|---|
| 1 | 有沒有寫死成功 | `grep -n "AddResultRow(true" <PO>`,每處後面的筆數都要是變數,不可是常數 |
| 2 | 有沒有空訊息 | `grep -n "string.Empty)" <PO>`,出現在 `AddResultRow(false` 那行就是缺陷 |
| 3 | 有沒有空 catch | `grep -n -A2 "catch" <PO>` 逐處看 |
| 4 | 交易有沒有帶進 SP | `grep -n "LoadDataSet" <PO>`,每處都要有 `tran` |
| 5 | 寄信 / 產檔在哪 | `grep -n "SendMail\|StreamWriter\|Commit" <PO>`,行號上 `Commit` 必須在前 |

## 7. 步驟六:Control 與 FormProxy —— 逐字樣板

Control 只覆寫一個初始化方法 + 一個業務入口(`Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs:35-38` 與 `:52-70`):

```
public override void InitializeDataAccessPool() { base.DataAccessPool.Add(new <NEW>_PO()); }

public <NEW>ViewVDB Execute(<NEW>ViewVDB view)
{
    var m_PO = base.GetDaoInstance<I<NEW>_PO>();
    return (<NEW>ViewVDB)this.ExecPOActionToViewVDB(view, m_PO.Execute);
}
```

**批次的 Ctl 不覆寫 `InitializeVDBTypes()`**(那是 M 用來接四眼的),也不覆寫 `CustomTransfer*` 四件套,除非要自己搬表。`OFDB600` 的 Ctl 同形(`Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs:150-154`)。

FormProxy 覆寫 `Execute`,例外一律轉成 `ServerSideError`(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:34-49`)。需要「按執行前先數一數」就多開一個方法(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:56-71` 的 `Check`),UI 端在 `DoValidate` 裡呼叫。 `Query` 在純批次裡是空殼,回 `(true, 0, "")`(`Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs:77-82`)。**想做成「先查清單、勾選、再按執行」就把 `Query` 實作出來**——`ofdb3.md §3.2` 查到 12 支批次是這樣寫的。

**驗證**:`grep -c "InitializeControl" <NEW>_Pxy.cs` 應為 0(那是 M 的樣板);`GetDaoInstance` 的泛型參數必須是介面型別,打錯會在執行期回 `ServerSideError`。

## 8. 步驟七:UI —— `xOneStepProcessForm`

`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs` 全檔 118 行,是最乾淨的批次 UI 範本,三個掛點:

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `<NEW>_FormInitial` | `TabPages` / `ProcessVDB` / `SetPermissionInfo` / `FormProxy` 四件 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:69-76` |
| `<NEW>_RefreshPage` | 關查詢鈕、開執行鈕、帶預設值 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:99-104` |
| `<NEW>_BeforeExecuteButtonClicked` | 驗證,不過就 `e.Cancel = true` | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:83-92` |

驗證集中在 `DoValidate`(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:33-59`):先 `ValidateErrList.Clear()` → `validatorManager1.DataValidate()` → 自訂檢核 → 有錯就回 → 清空並重組 `Parameters`。三條規則:

1. **參數名要跟 PO 端 `Rows.Contains("…")` 的字串一模一樣**(§3.4)。又一個靠字串對上的跨層綁定,打錯不紅字、條件靜靜不生效。

2. **`BeforeExecuteButtonClicked` 沒設 `e.Cancel = true` 就等於沒擋。**`OFDB673` 的「是否同意變更?」按「否」也照樣執行,就是漏了這一行(`Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs:89-93`)。

3. **「還有 N 筆沒處理完」這種前置檢查是詢問不是阻擋。**`OFDB003` 跳 `Warn02` 讓使用者按 OK 繼續(`Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs:52-54`);想真的擋就 `return false`,不要用對話框。

**驗證**:開畫面 → 什麼都不填按執行 → 必填訊息要跳出來且擋住,再把每條自訂檢核各觸發一次。

## 9. 步驟七之一(選配):加一個 WindowsService

**只有 §3.3 判定要走第 ③ 或第 ④ 種觸發時才做這一步。**四支服務的清單與安裝指令在 `deploy.md §5`,本節不重複。

### 9.1 改法:一個服務專案有五個檔

抄 `WindowsService.OFDB600` 換名字:

| 檔 | 內容 | 錨點 |
|---|---|---|
| `<NEW>_Service.cs` | Timer + `OnStart` + `DoExecute` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:24-31` |
| `Program.cs` | `Main()`(不收 `args`)+ 執行模式判斷 | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:13`、`:28-44` |
| `ProjectInstaller.cs` + Designer | 服務名與帳號 | 見 `deploy.md §5` |
| `App.config` | Remoting 段(§4.3) | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:175-194` |
| `WindowsService.<NEW>.csproj` | `OutputType` `WinExe`、`TargetFrameworkVersion` `v4.8` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj:9`、`:22` |

**csproj 的參考全部是 `HintPath` 指向 `%PTPF%` 的預編 DLL**,不是 `ProjectReference`(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj:74-101`)。所以**改了 `FormProxy.<MOD>` 或 `UIEntity.<MOD>` 之後,不更新 `%PTPF%` 的話服務拿到的還是舊的**——正是 `deploy.md §2` 講的 DLL 覆寫陷阱。服務專案**不在任何模組 sln 裡**,要自己開(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.sln`)。

### 9.2 ⚠ 服務帳號不能改成網域帳號

```
if (Environment.UserName == "SYSTEM") { ServiceBase.Run(ServicesToRun); }
else { var DebugToRun = new <NEW>_Service(); DebugToRun.Start(); Console.ReadLine(); }
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28-44`。配合安裝時的 `ServiceAccount.LocalSystem`,`UserName` 才會是 `"SYSTEM"`。**換成網域帳號就走進 else、卡在 `Console.ReadLine()`,SCM 等到逾時判定啟動失敗,而且沒有任何錯誤訊息。**

`deploy.md §5` 已記過這條。**新服務不要抄這個判斷**——要區分除錯模式就用命令列旗標或 `#if DEBUG`,不要用執行帳號。

**驗證**:`sc start <NEW>_Service` → 狀態要停在「執行中」而不是「正在啟動」。停在「正在啟動」直接看上面那段。

## 10. 編譯與部署

### 10.1 六個 csproj,不會多出組件

| 專案 | 加什麼 | 錨點(`OFDB003` 範本) |
|---|---|---|
| `DataEntity.<卷>` | `Compile` × 2 + `None` × 3 | `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/DataEntity.OFDB.csproj:102-107` 與 `:233-243` |
| `UIEntity.<卷>` | 同上 | `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/UIEntity.OFDB.csproj:102-107` 與 `:233-243` |
| `PO.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj:132` |
| `Control.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/Control.OFDB.csproj:140` |
| `FormProxy.<MOD>` | `Compile` × 1 | `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/FormProxy.OFDB.csproj:104` |
| `UI.<MOD>` | `Compile` × 2 + `EmbeddedResource` × 1 | `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj:321-325` 與 `:1225-1226` |

> ⚠ **`UI.OFDB.csproj:324` 掛的是 `OFDB003.designer.cs`,小寫的 `d`。**同一個專案裡兩種大小寫並存,Windows 編得過,大小寫敏感的工具會判缺。**新批次一律用 Visual Studio 產生的大寫 `.Designer.cs`。**

有服務的話再加第七個 `WindowsService.<NEW>.csproj`(§9.1)。

### 10.2 重編順序與部署到哪

重編順序照 `add-column.md §9.1`(Entity → PO → Control → FormProxy → UI),依據在 `architecture.md §2.4`。部署對照表是 `deploy.md §2`,批次沒有例外:

| 你改了 | 客戶端 | 伺服端 IIS | WindowsService |
|---|---|---|---|
| `UI.<MOD>`(批次畫面) | ✔ |  |  |
| `UIEntity.<卷>`(`View.xsd`) | ✔ | ✔ | ✔(若該服務用到) |
| `FormProxy.<MOD>` / `Control.<MOD>` / `PO.<MOD>` / `DataEntity.<卷>` |  | ✔ |  |

**服務那台要什麼看 `deploy.md §5`**:自己的 exe 與 `exe.config`、`FormProxy.<MOD>.dll`、`UIEntity.<MOD>.dll`、共用層、PTPFBlock。**它要的是「客戶端那一套」加自己的 exe,不是伺服端那一套**(`deploy.md §2` 第 3 條規則)。換伺服器時四支服務的 `exe.config` 都要改。

> **〔假設〕缺:PTPFBlock DLL / 部署機。**整個 §10 未實測(`architecture.md 附錄 C.1`)。csproj 三段來自 `OFDB003` 原文,重編順序來自 `ProjectReference` 相依。

## 11. 驗證清單

第一輪先確認六層接上:

| # | 動作 | 過的條件 | 沒過回去做 |
|---|---|---|---|
| 1 | `atlas_scan.py --screen <NEW>` | 六層都有路徑 | §5 §10.1 |
| 2 | 依 `add-column.md §9.1` 順序重編六個專案 | 六個都成功 | §10.1 |
| 3 | 開畫面、什麼都不填按執行 | 版面出得來;必填訊息跳出來且擋住 | §8 |

第二輪跑真的:

| # | 動作 | 查什麼 |
|---|---|---|
| 4 | 給**查無資料**的條件執行 | 要回「查無可執行之資料」而不是「成功 0 筆」,且已 Rollback(§6.5) |
| 5 | 給**正常**條件執行 | 回報筆數要等於 DB 實際變動筆數(§6.7 第 1 條) |
| 6 | **同樣條件再跑一次** | 依 §6.4 選的策略,要嘛被擋、要嘛結果相同,不可變兩倍 |
| 7 | 執行中**故意讓 SP 失敗**(給不存在的鍵) | DB 完全沒動、訊息有內容、框架 log 有一筆 |
| 8 | 有出口的話:把 Commit 那步中斷 | 信不可已寄出、檔不可已產生(§6.6) |
| 9 | 有服務的話:改時刻欄成「現在 + 2 分鐘」 | 兩分鐘內跑起來;`EventLog` 沒有 Error |

**第 4、6、8 最容易失敗**,而且失敗時不會有人發現——它們對應的正是 §14 的頭幾條反例。

## 12. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **回報成功,DB 一筆都沒動** | `ExecuteNonQuery` 回傳值被常數蓋掉,或成功訊息寫死 | §6.5 §6.7 |
| **回報失敗,但資料其實已經生效** | Commit 之後的動作失敗時把 `Result` 清掉重塞 | §6.6 |
| **使用者看到空白錯誤訊息** | `AddResultRow(false, 0, string.Empty)` | §6.5 |
| **重跑一次資料變兩倍** | 沒有 DELETE 也沒有旗標 | §6.4 |
| **信寄出去了,資料卻沒進去** | 寄信排在 Commit 之前 | §6.6 |
| **服務裝起來,狀態卡在「正在啟動」** | 用非 `LocalSystem` 帳號安裝 | §9.2 |
| **服務在跑,但就是不動作** | 時刻欄格式不足四碼被例外吞掉,或設定表有第二列 | §3.2 §6.5 |
| **改了 `FormProxy` 重編了,服務行為沒變** | 服務走 `HintPath` 綁 `%PTPF%` 的 DLL | §9.1、`deploy.md §2` |
| **執行鈕按下去什麼都沒發生** | `e.Cancel = true` 被無條件執行 | §8 |
| **`ORA-01008` 或參數對不上** | `AddInParameter` 的名字多一個冒號,或與 SP 宣告不符 | §3.4 |
| **例外訊息是「ServerSideError」** | PO 的例外穿過 Ctl 打到 Pxy | §6.3 第 1 條 |
| **凌晨跑跟白天跑結果不同** | 日期補丁只改了一半的表 | §14.6 |

## 13. 接手一支不熟的批次

跑完 `atlas_scan.py --screen <代號>` 之後查這六件事,每件都有固定看法:

| 要知道 | 去哪看 |
|---|---|
| 怎麼被觸發 | `Dev/<專案>/Source/WindowsService/` 底下有沒有同名資料夾;沒有就是純手動 |
| 要不要 Remoting | 該服務的 `App.config` 搜 `system.runtime.remoting` 與 `<wellknown>` |
| 交易誰開 | PO 裡搜 `BeginTransaction`;搜不到就是走 EVA 基底或根本不開 |
| 能不能重跑 | PO 裡搜 `DELETE`;沒有就再搜處理碼欄的 `= '0'` |
| 出口是什麼 | PO + Ctl 裡搜 `SendMail` / `StreamWriter` / `GetStoredProcCommand` |
| 有沒有踩到已知坑 | 直接讀 `ofdb.md 附錄 E` / `ofdb3.md 附錄 E` / `ofdb4.md 附錄 E` 裡有沒有點名它 |

## 14. 反例:新批次不要這樣寫

八條,全部來自三片批次篇的附錄 E。**共同點是「錯了不會有人發現」。**

### 14.1 `catch` 吞例外 / 空 `catch { }`

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs:149-151` 是一個完全空的 `catch { }`:時刻字串格式壞掉時,那個時刻整個消失、批次當天不跑,而且**沒有任何 log**(`ofdb3.md` E4.4)。同型:`OFDB731` 的存檔方法是 `catch { return false; }`,磁碟滿 / 權限不足 / 路徑太長全被吞成同一句(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs:514-517`);`OFDB913` 連 `HandleBusinessException` 都沒有(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs:133-138`)。

**正確寫法:`catch (Exception ex)` → 塞有內容的 `AddResultRow(false, 0, …)` → `CommonExceptionBlocker.HandleBusinessException(ex)`。**

### 14.2 fail-open 檢核:查詢炸掉等於檢核通過

```
bool boolvalue = true;
try { …查 DB… }
catch { }          // ← 不改值
return boolvalue;  // ← 永遠 true
```

`ofdb3.md` E4.1 實測 **`OFDB601A` / `OFDB602A` / `OFDB603` / `OFDB604A` 的 27 個檢核方法全部是這個形狀**(`Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs:284`、`:313-319`)。效果:DB 連不上、表改名、權限不足 → **所有前置卡控「通過」→ SP 照跑**。同型:`OFDB605` 的兩支驗證方法例外時 `return true`(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:206-210`、`:259-263`);`OFDB281` 六支檢核全部 `return true`(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs:88-92`)。

**正確寫法:檢核方法初值給 `false`,只有真的查到「可以放行」的證據才改 `true`;例外一律往外丟或回 `false`。**

### 14.3 `i = 1;` 蓋掉 `ExecuteNonQuery` 的回傳值

```
int i = db.ExecuteNonQuery(cmd, tran);
i = 1;                       // ← 這一行讓上面那行的結果消失
if (i == 1) tran.Commit();   // ← else 永遠到不了
```

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs:285-286` 與 `:405-414`(`ofdb3.md` E3.2)。同型:`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs:97` 與 `:158-162`、`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs:202` 與 `:309`。變形:成功訊息寫死「執行成功」不看回傳值,五支(`ofdb3.md` E3.6)。

**正確寫法:`ExecuteNonQuery` 的回傳值就是決定 Commit / Rollback 的那個數字,不要另開變數蓋掉它。**全片唯一寫對的是 `OFDB612` 的 `i += ExecuteNonQuery(…)`(`ofdb3.md §6.8`)。

### 14.4 信在 Commit 之前寄

`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:75-76` 呼叫寄信,`:84` 才 `tran.Commit()`(`ofdb3.md` E5.9);寄信方法的回傳值也沒有任何檢查。

**正確寫法見 §6.6:寄信、產檔、呼叫外部 API 一律排在 `Commit` 之後,而且失敗要另外回報,不可蓋掉「DB 已成功」這件事。**

### 14.5 `#region old sql` 不是註解

`OFDB600` 的執行前筆數方法把**舊版**與**新版**兩段完整的 `SELECT … FROM (…) A` 接在同一個字串上:舊版在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:320-359`(外面包的是 `#region old sql` / `#endregion old sql`)、新版在 `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:361-398`。

**`#region` 不是註解,那 38 行是活的。**送進 Oracle 的是兩個 SELECT 黏在一起,任何 Oracle 都會拒絕。對照組是同一個檔的執行後筆數方法,那邊的舊版是用 `//` 逐行註解掉的(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:443-466`),所以是好的。**壞掉的那支剛好沒有任何呼叫端,所以沒人發現**(`ofdb3.md` E2.2)。

**正確寫法:舊 SQL 要嘛刪掉(版控裡找得回來),要嘛整段 `/* */`。不要用 `#region` 當註解,也不要留在同一個字串串接鏈裡。**

### 14.6 寫死字串決定 `DELETE` 的範圍

`OFDB671` 的 `DELETE OFD678A WHERE INV_DEP_YN = :INV_DEP_YN`,而那個值由寫死字串比對 FunctionID 決定(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs:43-49`,`ofdb3.md` E6.2)。FunctionID 一改就洗錯半邊;grid 是空的時候會把那半邊整個清空。同型:`OFDB673` 的查詢**完全沒有 `WHERE`**,整張表全撈(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs:66-75`)。另一個變形是**成對邏輯只改一邊**:`OFDB600` 的跨午夜補丁只加在五張表,`OFD620A` / `OFD651A` 兩張沒加,凌晨 0~2 點跑會少算(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs:366`、`:371` 對 `:376`,`ofdb3.md` E7.1)。

**正確寫法:`DELETE` / `UPDATE` 的範圍一律由參數決定,而且那個參數要能從畫面或設定表追出來。字面常數只准出現在具名常數的宣告處。**

### 14.7 用 `Environment.UserName == "SYSTEM"` 決定跑不跑

見 §9.2。三支服務都有(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:28`,`ofdb3.md` E12.3),`RSPB008` 沒有。

**正確寫法:執行模式用命令列旗標或建置組態決定,不要用執行帳號。**執行帳號是部署決策,綁上去之後資安要求一來就整支不能跑。

### 14.8 SQL 字串串接使用者輸入

`ofdb4.md` E10 列了七處,最嚴重的是 `OFDB703` 的銀行代碼串接——`=` / `<>` 兩處**連引號都沒有**(`Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs:1406`、`:1411`);`OFDB691` 全部的 `UPDATE` 都走 `sb.AppendFormat` 樣板(`Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs:173`)。`architecture.md §4.3` 已定調:參數化在這套系統裡「做了一半」,另一半就是字串串接。

**正確寫法:值一律 `AddInParameter`,SQL 裡用 `:名稱` 佔位。**表名或欄名真的要動態決定時,先把候選值列成白名單再比對,不要直接串。

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB003.cs` | `:33-59` `:43-48` `:52-54` `:69-76` `:83-92` `:99-104` | §3.4 §8 |
| `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/OFDB003_Pxy.cs` | `:34-49` `:56-71` `:77-82` | §7 |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/OFDB003_Ctl.cs` | `:35-38` `:52-70` `:59-61` | §6.6 §7 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB003_PO.cs` | `:20-29` `:32-33` `:36` `:57-155` `:62-119` `:72-78` `:100-101` `:118-119` `:148-153` `:315-322` | §6 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/OFDB003Model.xsd` · `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/OFDB003View.xsd` | 全檔 | §5.1 |
| `Dev/ATLAS.OFDB/Source/Entity/DataEntity.OFDB/DataEntity.OFDB.csproj` · `Dev/ATLAS.OFDB/Source/Entity/UIEntity.OFDB/UIEntity.OFDB.csproj` | `:102-107` `:233-243` | §10.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/PO.OFDB.csproj` | `:132` | §10.1 |
| `Dev/ATLAS.OFDB/Source/Control/Control.OFDB/Control.OFDB.csproj` | `:140` | §10.1 |
| `Dev/ATLAS.OFDB/Source/FormProxy/FormProxy.OFDB/FormProxy.OFDB.csproj` | `:104` | §10.1 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/UI.OFDB.csproj` | `:321-325` `:1225-1226` | §10.1 |
| `Dev/ATLAS.EC/Source/Control/Control.EC/OFDB600_Ctl.cs` | `:137` `:150-154` | §7 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB600OracleDao.cs` | `:51` `:55-62` `:75-76` `:84` `:100` `:268-292` `:320-359` `:361-398` `:366` `:371` `:376` `:443-466` | §3 §6 §14 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/OFDB600_Service.cs` | `:24-31` `:39-58` `:50-52` `:65-75` `:84-86` `:92` `:103-106` `:109-155` `:149-151` `:239-252` | §3.2 §6.5 §9 §14.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs` | `:13` `:28` `:28-44` | §3.4 §9.2 §14.7 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:175-194` `:189` | §4 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/App.config` | `:175-194` `:189` | §4.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/App.config` | `:246-262` | §4.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.csproj` | `:9` `:22` `:74-101` | §9.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/WindowsService.OFDB600.sln` | 全檔 | §9.1 |
| `Dev/ATLAS.EC/Source/Entity/DataEntity.EC/OFDB600_9iModel.xsd` · `Dev/ATLAS.EC/Source/Entity/UIEntity.EC/OFDB600_9iView.xsd` | 全檔 | §5.2 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB605OracleDao.cs` | `:97` `:158-162` `:206-210` `:259-263` | §14.2 §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB615OracleDao.cs` | `:285-286` `:405-414` | §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB616OracleDao.cs` | `:202` `:309` | §14.3 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB671OracleDao.cs` | `:43-49` | §14.6 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB673OracleDao.cs` | `:66-75` | §14.6 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/Oracle/OFDB691OracleDao.cs` | `:173` | §14.8 |
| `Dev/ATLAS.EC/Source/UI/UI.EC/OFDB673.cs` | `:89-93` | §8 |
| `Dev/ATLAS.OTAB/Source/PO/PO.OTA/OFDB601A_PO.cs` | `:284` `:313-319` | §14.2 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB281_PO.cs` | `:88-92` | §14.2 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB703_PO.cs` | `:1406` `:1411` | §14.8 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB731_PO.cs` | `:514-517` | §14.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB913_PO.cs` | `:133-138` | §6.5 §14.1 |
| `Dev/ATLAS.OFDB/Source/PO/PO.OFDB/OFDB901_PO.cs` | `:73` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB560.cs` | `:64` `:72-84` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019A.cs` · `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB019B.cs` | `:42` / `:78` | §3.4 |
| `Dev/ATLAS.OFDB/Source/UI/UI.OFDB/OFDB950.cs` | `:86` `:120` `:146` `:183` | §3.4 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **部署機** | §4.4 §9 §10.2 | Remoting 有無的實測、服務安裝與目錄實際內容都未驗證 |
| **PTPFBlock DLL** | §10 §11 | 六層重編與服務建置全未實測;`HintPath` 綁 DLL 的影響只能從 csproj 推 |
| **DB 連線** | §3.2 §6.4 §11 | 排程時刻欄由哪支 M 畫面維護查不到;重跑行為與 SP 內部邏輯無法驗 |
| **SP 腳本(380 支裡 319 支沒有)** | §6.6 §11 | SP 到底動了哪些表只能從呼叫端的前後筆數 SQL 反推(`architecture.md 附錄 B.0`) |
| **統一的批次 log 表** | §6.5 | 目前只能列出三條各走各的管道;若現場其實有一張總表,§6.5 要改寫成單一規則 |
| **選單 / 權限表** | §2.3 §11 | 新批次怎麼掛進選單、怎麼授權,與 `add-screen.md §9` 同一個缺口 |

## 附錄 C 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。以 `OFDB003`(無 Remoting)與 `OFDB600`(有 Remoting + 服務)為兩支範例,素材取自 `modules/ofdb.md` `modules/ofdb3.md` `modules/ofdb4.md` 共 88 支批次 |

由 build_doc.py v2.0.0 於 2026-09-15 17:56 產生 · 標題 55 · 圖 3 · 表格 30 · 程式錨點 128 · § 連結 107 · 引用檢查：畫面 35（缺 0） · Table 3（缺 0） · 結果集 2（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/add-report.md
============================================================

# ATLAS 維護手冊 — 加 / 改 Crystal 報表

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。

> 前提知識在 `architecture.md §6`(畫面型別)與 `architecture.md §5`(typed DataSet)。**不要整份讀**。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在既有報表上加 / 改欄位;替既有 R 畫面加一個新報表版型 |
| 範例 | `CASR001`,`Dev/ATLAS.CAS.Report`——七層齊全,而且一支畫面掛六個版型,對照方便 |
| 不適用 | 從零建一支 R 畫面(骨架同 `runbooks/add-screen.md`,再加本手冊的第七層) |
| 前提工具 | Visual Studio 2022 + **Crystal Reports for VS**(版本見 `runbooks/build-env.md §2`,**13.0.4000.0 與 13.0.2000.0 兩版並存**) |
| 變數 | `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock` |

### 0.1 R 畫面是七層不是六層

`architecture.md §6` 講過的命名例外,這裡要用到全部細節。`CASR001` 的七層:

| 層 | 專案 | 檔 |
|---|---|---|
| UI | `ReportUI.CAS` | `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs` |
| FormProxy | `ReportFormProxy.CAS` | `Dev/ATLAS.CAS.Report/Source/FormProxy/ReportFormProxy.CAS/CASR001_Pxy.cs` |
| Control | `ReportControl.CAS` | `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs` |
| PO | `ReportPO.CAS` | `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs` |
| DataEntity | `ReportDataEntity.CAS` | `Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` |
| UIEntity | `ReportUIEntity.CAS` | `Dev/ATLAS.CAS.Report/Source/Entity/ReportUIEntity.CAS/CASR001View.xsd` |
| **報表** | **`Report.CAS`** | `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.rpt` |

**六層全部加 `Report` 前綴、住在 `<模組>.Report` 專案資料夾裡。**任何按六層命名寫的工具對 322 支 R 畫面都會失準。

### 0.2 一支畫面可以掛多個版型

`CASR001` 有六個:`CASR001RPS.rpt` · `RPS2` · `RPS3` · `RPS4` · `RPS5` · `RPS6`。

**選哪一個是客戶端決定的**(§3.3)。所以「加一個新版型」不用改伺服端邏輯,只要多一支 `.rpt` 加上客戶端能選到它。

### 0.3 R 畫面沒有四眼

`CASR001_PO` **沒有宣告 `MasterTable` 或 `DetailTable`**(`py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --screen CASR001` 回報主檔明細皆空),也不繼承 EVA 基底。報表是唯讀的,不走 `architecture.md §3` 的四眼流程。

## 1. 資料流總覽

```text
[圖] 報表的兩條路:資料經 SP 的 RefCursor 進結果集 xsd,版型是獨立的 rpt 檔由伺服端傳給客戶端,執行時才合併
圖中文字:① 資料這條路 / Oracle SP / 84% 不在 repo,要先撈 / RefCursor C_RES / AddOutParameter / LoadDataSet / 填進結果集那張表 / Model.xsd 結果集 / 不是實體表,免 ALTER / ② Model → View 逐欄照名複製 / View.xsd / 欄名必須與 Model 一致 / Control 轉換 / 不用改(泛型逐欄) / ⚠ 只加一邊 / 靜默失敗,不報錯 / FormProxy / 不用改 / ③ 版型這條路 —— 與資料完全分開 / .rpt 版型檔 / 一支畫面可掛多個 / 伴生 .cs / AutoGen,不要手改 / PostBuild xcopy / build 時複製,不是部署時 / PTPFBlock CrystalReports / 609 支範本 / ④ 執行時才會合 / 客戶端指定版型類別名 / ReportParameters[0].ReportClass / CRReportTransfer / PTPFBlock,無原始碼 / 回傳 .rpt 位元組 / Crystal 檢視器合併 / 資料 + 版型
```

*圖:圖 1 報表資料流。上兩排=資料,第三排=版型,兩條路各走各的,只在客戶端的檢視器裡合併。橘實框=加欄位要改的四處;灰虛框=不用改;橘虛框=陷阱。*

一句話:**資料走 SP,版型走檔案傳輸,兩條路各走各的。**

## 2. 動工前先分辨:你要改哪一條

| 需求 | 要改 | 節 |
|---|---|---|
| 報表**多印一個欄位** | SP + `Model.xsd` + `View.xsd` + `.rpt` **四處** | §3 §4 §5 |
| 只改**版面**(位置、字體、群組、小計) | 只改 `.rpt` | §5 |
| 加一個**新版型**(同資料不同排版) | 新增 `.rpt` + csproj + 客戶端選項 | §6 |
| 改**查詢條件** | SP + PO 的參數 + UI 的條件控件 | §3.2 §7 |

**最常見的是第一種,而且四處漏一處就會出錯,症狀各不相同(§9)。**

## 3. 資料端:SP 回 RefCursor

### 3.1 現況

`CASR001_PO.GetData` 的全部邏輯(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:46-79`):

```
using (DbCommand cmd = m_db.GetStoredProcCommand("S_TA_CASR001_GET"))
{
    cmd.CommandTimeout = 0; //此程式讓它永久跑  
    m_db.AddInParameter(cmd, "iSDATE",   OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "SDATE"));
    m_db.AddInParameter(cmd, "iEDATE",   OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "EDATE"));
    m_db.AddInParameter(cmd, "iEMP_NO",  OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "EMP_NO"));
    m_db.AddInParameter(cmd, "iRPT_KIND",OracleDbType.Varchar2, SQLEVAHelper.GetParamValue(model, "RPT_KIND"));

    m_db.AddOutParameter(cmd, "C_RES", OracleDbType.RefCursor, int.MaxValue);
    m_db.LoadDataSet(cmd, model.DataEntity, tran, new string[] { model.DataEntity.CASR001.TableName });
}
```

四個慣例,加報表欄位時要照著:

| 慣例 | 說明 |
|---|---|
| 參數前綴 `i` | `iSDATE` / `iEDATE` / `iEMP_NO` / `iRPT_KIND`,都是 `Varchar2` |
| 回傳走 `RefCursor` | 固定名為 `C_RES`,Oracle 的游標回傳法 |
| 值從 model 取 | `SQLEVAHelper.GetParamValue(model, "<條件欄名>")` |
| `LoadDataSet` 指定表名 | 填進 `model.DataEntity.CASR001` 這一張 |

查無資料時寫 `model.Utility.Result.AddResultRow(false, 0, "查無資料")`(`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:75`),不是丟例外。

### 3.2 改法

**多印一個欄位 = 改 SP 的 `RefCursor` 查詢,把欄位加進 SELECT。**

⚠ **`S_TA_CASR001_GET` 不在 repo 裡。**`DB/SP/` 沒有這支。全庫程式呼叫 380 支 SP,repo 只有 61 支有腳本(`architecture.md 附錄 B.0`)。

所以第一步是**先從資料庫把它撈出來**:

```
SELECT text FROM all_source
 WHERE name = 'S_TA_CASR001_GET' ORDER BY line;
```

撈出來、存成檔案進版控、再改。**不要憑空重寫一支同名 SP**,會覆蓋線上邏輯。完整流程見 `runbooks/change-sp-fn-trigger.md`。

改查詢條件則要三處一起:SP 的參數、PO 的 `AddInParameter`、UI 的條件控件。

### 3.3 ⚠ `CommandTimeout = 0`

`Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs:60` 註解寫「此程式讓它永久跑」。

**這代表報表查詢沒有逾時保護。**SP 寫壞、條件給太寬,連線會一直掛著不放。加欄位如果讓查詢變重,先自己估一下資料量。

## 4. 結果集:`Model.xsd` 與 `View.xsd`

### 4.1 `CASR001` 是結果集形狀不是實體表

`model.DataEntity.CASR001` 這張表**只存在於 xsd 裡**,資料庫沒有這張表。全庫有 1,635 個這種形狀(`architecture.md §5`)。

判斷方法:

```
py -V:3.12 %ATLAS_ROOT%\docs\tools\atlas_scan.py --table CASR001
```

掃描器會標示它不是實體表(`physical` 為否)。

### 4.2 改法

**SP 的 SELECT 多回一欄,xsd 就要多一個 `<xs:element>`,兩邊欄名必須一致。**

加法完全照 `runbooks/add-column.md §3.2`(Model)與 `§4.2`(View),包括:四個 `msprop:Generator_*` 屬性、`msdata:Caption` 給中文名、`minOccurs="0"`、**改完要重生 `Designer.cs`**。

差別只有兩點:

|  | 一般 M 畫面 | 報表 |
|---|---|---|
| 要不要 `ALTER TABLE` | 要(實體欄) | **不用**,結果集不是實體表 |
| 四眼欄位 | 有 15 個 | **沒有**,結果集不帶四眼 |

### 4.3 Model → View 的轉換

`CASR001_Ctl` 的轉換方法同樣走 `TransferVDBHelper` 的泛型逐欄複製,所以**兩邊欄名一致就不用改 Control**——理由與 `runbooks/add-column.md §6.1` 完全相同,包括只加一邊會**靜默失敗**的代價。

## 5. 版型:`.rpt`

### 5.1 `.rpt` 有一支自動產生的伴生 `.cs`

`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:120-125`:

```
<Compile Include="CASR001RPS.cs">
  <AutoGen>True</AutoGen>
  <DesignTime>True</DesignTime>
  <DependentUpon>CASR001RPS.rpt</DependentUpon>
  <SubType>Component</SubType>
</Compile>
```

伴生 `.cs` 是 `CrystalDecisions.CrystalReports.Engine.ReportClass` 的子類(`Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.cs:19`),檔頭寫明「這段程式碼是由工具產生的…變更將會遺失」。

**這與 xsd / Designer.cs 是同一種關係:改 `.rpt`,伴生 `.cs` 由 Crystal 設計工具重生,不要手改 `.cs`。**

### 5.2 改法

1. VS 內開 `.rpt`(Crystal 設計檢視)。

2. 報表的資料來源接的是 typed DataSet——**先做完 §4,`.rpt` 的欄位清單裡才看得到新欄位**。

3. 把欄位拉到版面上,設好格式、群組、小計。

4. 存檔,確認伴生 `.cs` 時間戳有更新。

> **〔假設〕缺:Crystal 設計工具。**本機沒裝,`.rpt` 是二進位檔讀不了內容,所以上述步驟未實測。依據是伴生 `.cs` 的 `AutoGen` / `DependentUpon` 設定與 `ReportClass` 繼承關係——這是 Crystal for VS 的標準運作方式。

### 5.3 部署:範本是 build 出來的

`Report.<模組>` 專案帶 PostBuild(25 支都有):

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

所以 **`.rpt` 在 build 時就被複製到 `%PTPF%\CrystalReports\`**,不是部署時才搬。細節見 `runbooks/build-env.md §5.3` 與 `runbooks/deploy.md §7`。

**改了 `.rpt` 一定要編 `Report.<模組>` 專案**,否則新版型不會進到那個目錄。

## 6. 加一個新版型

`CASR001` 掛了六個版型,加第七個:

1. 在 `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/` 新增 `CASR001RPS7.rpt`(照現有那六支的命名)。

2. csproj 加一段,照 `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj:120-125` 的樣板,把 `CASR001RPS` 換成 `CASR001RPS7`。

3. 客戶端要能選到它——見 §7。

**不用改 PO、Control、xsd**,因為資料來源沒變。

## 7. 版型是客戶端選的,伺服端只負責傳檔

`CASR001_Ctl.GetReportObject`(`Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs:59-63`):

```
string rpt = Convert.ToString(ClassData.Util.ReportParameters[0].ReportClass); // 取得前端所傳的報表類別名稱
return CRReportTransfer.TransferFileByte(rpt); // 呼叫報表傳送器傳回報表物件
```

流程:

| 步 | 誰做 | 做什麼 |
|---|---|---|
| 1 | 客戶端 | 把版型類別名放進 `Util.ReportParameters[0].ReportClass` |
| 2 | 客戶端 | `this.FormProxy.GetReportData(...)`(`Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs:220`)取資料 |
| 3 | 伺服端 | `GetReportObject` 依名字回傳 `.rpt` 的**檔案位元組** |
| 4 | 客戶端 | Crystal 檢視器把資料與版型組起來顯示 |

所以「加新版型」在客戶端要做的是:讓使用者能選到 `CASR001RPS7` 這個名字,並把它填進 `ReportParameters[0].ReportClass`。

> `CRReportTransfer` 在 PTPFBlock 裡(**無原始碼,從呼叫端反推**),repo 內找不到 `class CRReportTransfer`。它怎麼解析名字到檔案、找不到時回傳什麼,都看不到。

> ⚠ **版型類別名是客戶端傳來、伺服端直接拿去載入的。**這是一個由客戶端控制的字串進到伺服端檔案存取路徑,`architecture.md 附錄 E` 已記錄。加新版型時照現有機制走即可,但**不要**擴大成「讓使用者自由輸入檔名」。

## 8. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 直接在資料庫跑改過的 SP | 回傳的游標**有新欄位**且值正確 |
| 2 | `grep -c "<NEW_COL>" …/CASR001Model.Designer.cs` | 大於 0(驗 xsd 重生了) |
| 3 | 同上,`CASR001View.Designer.cs` | 大於 0 |
| 4 | 編 `Report.CAS` 專案 | 成功,且 `%PTPF%\CrystalReports\` 的 `.rpt` 時間戳有更新 |
| 5 | 開 R 畫面、給條件、預覽 | 新欄位印得出來 |
| 6 | 換一個版型再印一次 | 其他版型不受影響 |
| 7 | 給一組**查無資料**的條件 | 出現「查無資料」而不是空白報表或例外 |
| 8 | 給一組資料量大的條件 | 跑得完(注意 §3.3 沒有逾時保護) |

## 9. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **`.rpt` 設計檢視裡看不到新欄位** | xsd 沒加或沒重生 Designer.cs | §4.2 |
| **報表印出來該欄空白** | SP 沒回這一欄(xsd 有、資料沒有) | §3.2 |
| **資料有、報表沒印** | `.rpt` 版面沒把欄位拉上去 | §5.2 |
| **改了 `.rpt` 但印出來還是舊的** | 沒編 `Report.<模組>` 專案,`%PTPF%\CrystalReports\` 沒更新 | §5.3 |
| **手改了伴生 `.cs`,下次開 `.rpt` 就不見了** | 那支是 `AutoGen`,由設計工具重生 | §5.1 |
| **只加了 Model 沒加 View(或反之)** | `TransferVDBHelper` 逐欄比對,對不上就靜默跳過 | §4.3 |
| **報表跑很久不回來也不逾時** | `CommandTimeout = 0` | §3.3 |
| **找不到 SP 可以改** | 84% 的 SP 不在 repo | §3.2 |
| **新版型選不到** | csproj 沒加,或客戶端沒提供選項 | §6 §7 |
| **按六層去找 R 畫面的檔卻找不到** | R 是七層,而且各層加 `Report` 前綴 | §0.1 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.CAS.Report/Source/PO/ReportPO.CAS/CASR001_PO.cs` | `:46-79` `:60` `:75` | §3 |
| `Dev/ATLAS.CAS.Report/Source/Control/ReportControl.CAS/CASR001_Ctl.cs` | `:48-53` `:59-63` | §4.3 §7 |
| `Dev/ATLAS.CAS.Report/Source/UI/ReportUI.CAS/CASR001.cs` | `:220` | §7 |
| `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/Report.CAS.csproj` | `:120-125` | §5.1 §6 |
| `Dev/ATLAS.CAS.Report/Source/CrystalReports/Report.CAS/CASR001RPS.cs` | `:1-19` `:19` | §5.1 |
| `Dev/ATLAS.CAS.Report/Source/Entity/ReportDataEntity.CAS/CASR001Model.xsd` | `:1` | §4 |
| `Dev/ATLAS.CAS.Report/Source/Entity/ReportUIEntity.CAS/CASR001View.xsd` | `:1` | §4 |
| `Dev/ATLAS.CAS.Report/Source/FormProxy/ReportFormProxy.CAS/CASR001_Pxy.cs` | `:1` | §0.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **Crystal Reports for VS** | §5 全節 | `.rpt` 是二進位檔,本機讀不了也開不了。裝好後把設計工具的實際操作步驟、欄位清單長相回填 |
| **`S_TA_CASR001_GET` 的原始碼** | §3.2 | 目前只知道它吃 4 個參數回一個 RefCursor;撈出來後可以貼出實際的 SELECT 當範本 |
| **PTPFBlock DLL** | §7 | `CRReportTransfer` 怎麼解析版型名、找不到時的行為都看不到 |
| **選單 / 權限表** | §6 §7 | 新版型要怎麼出現在使用者的選項裡,查不到 |

## 附錄 C 本手冊的驗證程度

| 節 | 依據 | 程度 |
|---|---|---|
| §0.1 七層 · §0.3 無四眼 | 實際檔案結構 + 掃描器 | **已驗證** |
| §3 SP / RefCursor / 參數慣例 | 讀 `CASR001_PO.cs` 原文 | **已驗證** |
| §4 結果集 xsd | 同 `runbooks/add-column.md` 的機制 | **已驗證** |
| §5.1 伴生 `.cs` 由工具產生 | csproj 的 `AutoGen` / `DependentUpon` + 檔頭註解 | **已驗證** |
| §5.2 設計工具操作步驟 | Crystal 標準做法 | **未實測**,缺工具 |
| §5.3 build 時複製範本 | csproj 的 PostBuild 原文 | **已驗證**(但未實跑) |
| §7 版型傳輸 | 讀 `CASR001_Ctl.cs` 原文;`CRReportTransfer` 本身無原始碼 | 呼叫端已驗證,被呼叫端是黑箱 |

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 26 · 圖 1 · 表格 11 · 程式錨點 23 · § 連結 46 · 引用檢查：畫面 1（缺 0） · Report 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/change-eva-flow.md
============================================================

# ATLAS 維護手冊 — 改四眼流程

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。

> 前提知識在 `architecture.md §3`(四眼引擎)與 `architecture.md §4`(資料存取)。**不要整份讀**。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 在四眼流程上加檢核、加稽核軌跡、改新增時的預設值、加自訂動作 |
| **不適用** | **改狀態機本身**(例:跳過覆核直接核准)——見 §5,這件事在 repo 裡做不到 |
| 前提 | 先讀懂 `architecture.md §3` 的狀態機與 `EVAType` 值域 |
| 影響半徑 | 依你改哪一層而定,從「一支畫面」到「908 支全中」,見 §2 |

### 0.1 先看清楚:哪些是活的、哪些是死碼

**這是本手冊最重要的一頁。改錯地方會白做一整天,而且不會有任何錯誤訊息。**

| 類別 | 位置 | 子類數 | 狀態 |
|---|---|---|---|
| `BaseEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:17-27` | **271** | ✅ **現行主線(單筆)** |
| `BaseMultiRowEVADaoPO` | `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:18-31` | **61** | ✅ **現行主線(多筆)** |
| `BasicEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:24-24` | 66 | ⚠ 舊世代,仍有人用 |
| `MultiRowEVAPO` | `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:16-16` | 11 | ⚠ 舊世代,仍有人用 |
| `TA_PO`(2,106 行) | `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs:19-19` | **0** | ❌ **死碼** |
| `Basic4EyesPO`(4,257 行) | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:28-28` | **0** | ❌ **死碼** |
| `MultiRow4EyesPO` | `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs:2428-2428` | **0** | ❌ **死碼** |

`TA_PO` 與 `Basic4EyesPO` 加起來 **6,363 行躺在核心目錄裡,沒有任何東西繼承或實例化它們**。它們僅存的「子類」宣告都是被 `//` 註解掉的行(`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs:18`、`Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM694_PO.cs:20`)。

**動手前先確認你那支畫面的 PO 繼承誰:**

```
grep -n "class .*_PO *:" "%ATLAS_ROOT%\Dev\ATLAS.<MOD>\Source\PO\PO.<MOD>\<代號>_PO.cs"
```

看到 `: BaseEVADaoPO` 或 `: BaseMultiRowEVADaoPO` 才是主線。看到 `TA_PO` 或 `Basic4EyesPO`,那支根本沒在跑。

### 0.2 第二件要先知道的:四眼的主體不在 repo 裡

`BaseEVADaoPO` 本體**只做三件事**(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:22-26`、`:143-146`、`:155-227`):鎖死連線為 `("TA", DbServerType.Oracle)`、一個 `AddM` 轉呼叫、一個 `CopyDetail`。

**`Add` / `Update` / `Verify` / `Approve` / `Reject` 這些 EVA 動作本身,全部在 `BaseEVADao`(PTPFBlock,無原始碼)裡。**

所以本手冊能教你的只有一件事:**在框架留給你的掛點上做文章**。掛點在哪、能做什麼、不能做什麼,就是 §3 與 §4。

## 1. 改動點總覽

```text
[圖] 改四眼流程:活的基底與死碼、四眼主體在無原始碼的 DLL 裡、事件掛點是唯一擴充點、四種改法的影響半徑
圖中文字:① 先確認你改的東西是活的 / BaseEVADaoPO / 271 子類 · 現行主線 / BaseMultiRowEVADaoPO / 61 子類 · 多筆主線 / BasicEVAPO · MultiRowEVAPO / 66 + 11 · 舊世代仍有人用 / TA_PO · Basic4EyesPO / 6,363 行死碼 · 改了沒效 / ② 主體不在 repo 裡 / BaseEVADaoPO 本體 / 只做三件事 / BaseEVADao / PTPFBlock · 無原始碼 / Add / Verify / Approve … / 全在 DLL 裡,改不到 / ③ 唯一的正規擴充點:PO 的事件掛點 / BeforeAdd / 參數綁定前 · 改得到 model / DLL 執行 EVA 動作 / 無原始碼 / After* 七個 / 交易未 commit · throw 可回滾 / commit / ④ 影響半徑 —— 選錯不是效率問題是事故 / 某支畫面的 _PO.cs / 1 支 · 預設選這個 / 某支畫面的 _Ctl.cs / 1 支 / BaseEVADaoPO / 271 支全中 · 幾乎不該動 / BaseEVADao / 全系統 · 做不到 / ⚠ 兩個最常見的錯 / handler 少了表名判斷 / 主檔+每個明細各觸發一次 → 跑好幾遍 / After* 只 return 不 throw / 檢核擋了但資料庫有殘留
```

*圖:圖 1 改四眼流程的全貌。灰虛框=死碼,改了沒效果;灰框=PTPFBlock 黑箱,改不到;橘實框=你能動的地方;橘虛框=警告。*

## 2. 先決定:改在哪一層

影響半徑差三個數量級,選錯不是效率問題是事故:

| 改在哪 | 影響 | 什麼時候用 |
|---|---|---|
| **某支畫面的 `_PO.cs` 事件 handler** | **1 支畫面** | 絕大多數需求。**預設選這個** |
| 某支畫面的 `_Ctl.cs` | 1 支畫面 | 需要在轉換 Model↔View 時做事 |
| `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs` | **271 支畫面** | 幾乎不該動 |
| `BaseEVADao`(DLL) | **全系統** | **做不到**,無原始碼 |

> ⚠ **`TA.DataAccess` 是共用引擎。**動 `BaseEVADaoPO` 或 `BasicEVAPO`,271 + 66 支畫面全部跟著變,而且它們分散在 34 個專案資料夾裡,沒有任何自動化測試會告訴你哪裡壞了(repo 內沒有測試專案)。

> **需求如果只影響一支畫面,就不要動共用層。**這句話沒有例外。

## 3. 事件掛點:唯一的正規擴充點

### 3.1 掛點總表

事件宣告在 `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:37-94`(Before 15 個)與 `:100-157`(After 15 個);新世代同名事件改吃 `xEVAEventArgs`(PTPFBlock,無原始碼,從呼叫端反推)。

| 掛點 | 何時觸發 | 能改什麼 | **不能做什麼** |
|---|---|---|---|
| `BeforeAdd` | INSERT 指令組好、**參數還沒綁**之前;主檔一次 + **每個明細表各一次** | 改 model 欄位值(會被後續綁定吃進去)、換掉 `args.DbCmd`、`args.Cancel = true` 跳過 | 不能假設只跑一次;不能自己 commit |
| `BeforeSelect` · `BeforeGetMaintainData` · `BeforeGetToDoData` | 查詢 SQL 組好之前 | 整個換掉 `args.DbCmd` | 同上 |
| `AfterGetMaintainData` | 資料已進 model | 往 model 補掛額外資料 | 不能改 `DbCmd`(已執行完) |
| `AfterVerify` · `AfterApprove` · `AfterReject` · `AfterResend` · `AfterDelete` · `AfterUnDelete` · `AfterApproveDelete` | 對應動作成功、**交易尚未 commit** | 在同一交易內再下 SQL(`args.DbTran` 還活著)、寫稽核軌跡、**`throw` 讓整筆回滾** | **不能自己 commit / rollback** |

`args` 拿得到:`args.ModelVDB` · `args.TableName` · `args.DbCmd` · `args.DbTran` · `args.DbTranPTPF`。

### 3.2 ⚠ 每個 handler 第一行都要判斷表名

事件會**對主檔與每一個明細表各觸發一次**。所以 `CASM001_PO` 的每個 handler 開頭都是:

```
if (args.TableName != this.MasterTable.dbTableName) return;
```

`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:571`

**漏掉這一行,你的邏輯會在一次新增裡跑好幾遍。**症狀:流水號跳號、稽核軌跡重複、檢核訊息跳兩次。

### 3.3 訂閱寫在建構子

`CASM001_PO` 在建構子一次訂 12 個事件(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:40-60`),handler 本體在 `:77-153` 與 `:569-630`。

加一個掛點就是兩步:建構子加一行 `this.<事件> += <handler>;`,再寫 handler。

## 4. 三種常見需求怎麼做

### 4.1 加一條「覆核時檢核」

**寫在 `AfterVerify`,用 `throw` 否決。**

現況範本(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:593-599`)——`CASM001` 七個 `After*` 都是同一個寫法:

```
private void CASM001_PO_AfterVerify(object sender, xEVAEventArgs args)
{
    if (args.TableName != this.MasterTable.dbTableName) return;
    if (!SrNoCommentProcessor.AddCommentHistory(...)) throw new ApplicationException("");
}
```

改法:在 `return` 之後、原有邏輯之前,加你的檢核:

```
if (<檢核不通過>) throw new ApplicationException("<給使用者看的中文訊息>");
```

**`throw` 是 After 掛點唯一能否決整筆交易的手段。**交易此時還沒 commit,例外會讓它整個回滾。

> 範本那七處都 `throw new ApplicationException("")`——**空訊息**。使用者看到的會是空白錯誤框。你自己加的一定要給中文訊息。

### 4.2 加一條「新增時的預設值 / 流水號」

**寫在 `BeforeAdd`,而且必須在參數綁定之前。**

現況範本(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:88-101`):do-while 取流水號 `genSrNo.GetPR_NO()`,用 `IsExistByData` 檢查撞號就重取,取到之後回填到所有明細 row。

兩個要點:

1. **一定要在 `BeforeAdd`。**`architecture.md §4.2` 說明 INSERT 的參數是由 DataRow 的欄位值綁的,`BeforeAdd` 之後才綁——在 `After*` 改 model 沒有用。

2. **主檔改完要記得回填明細。**主明細是分開觸發的,主檔的新值不會自動傳到明細 row。

### 4.3 加稽核軌跡

**寫在對應的 `After*`,用 `args.DbTran` 在同一交易內下 SQL。**

這樣寫的好處是稽核紀錄與業務資料同進同退——業務資料回滾,稽核紀錄也回滾。如果你希望「即使失敗也要留紀錄」,那就**不能**用 `args.DbTran`,要另開連線;但這樣就沒有交易保護,要自己處理失敗。

> `architecture.md §3.7` 提到業務庫與待辦庫是**兩個獨立交易、沒有分散式交易**,而且兩個世代的 commit 順序相反。加稽核軌跡時不要假設它們是原子的。

## 5. 改狀態機本身:在 repo 裡做不到

計劃書原本要求本節說明「改狀態轉換(例:跳過 Verify 直接 Approve)要動 `TA_PO.EVA()` 的哪一段」。**這個問題的前提是錯的:**

1. `TA_PO` 是死碼(§0.1),改它不會有任何效果。

2. 現行主線 `BaseEVADaoPO` 的 EVA 動作全在 `BaseEVADao`(PTPFBlock,無原始碼)裡(§0.2)。

所以狀態轉換的規則、`EVAStatusCode` 的實際字面值、`SetTASecurityData` 怎麼依 `EVAType` 寫欄位,**都在編譯好的 DLL 內,repo 改不到**。

### 5.1 那實務上怎麼辦

| 需求 | 可行做法 |
|---|---|
| 某些條件下**不需要覆核** | 在 `BeforeAdd` 依條件直接把 `STATUS` 設成 `Approve*` 那組值,略過中間狀態。**〔假設〕**——`STATUS` 是 model 的一般欄位,`BeforeAdd` 改得到;但 DLL 後續是否會覆寫它未經驗證 |
| 加一個**新的動作**(例:「暫緩」) | 不要動狀態機。用一個自訂欄位 + 畫面按鈕 + PO 自訂方法實作,不要試圖新增 `EVAType` 值 |
| 改**誰能做哪個動作** | 權限不在 repo(選單 / 權限表不在版控),要在資料庫端處理 |
| 只是想**看懂**目前的規則 | `architecture.md §3.3`(`EVAType` 10 個值)與 `§3.10`(`STATUS` 12 個值),都是反推的 |

> **〔假設〕缺:PTPFBlock DLL 原始碼。**上表第一列的做法未經驗證。要確定得反編譯 `Vendor.Product.DataAccess.dll`,或在測試環境實測一次。**動正式環境前一定要先驗。**

## 6. 多筆(MultiRow)的差異

如果你那支畫面的 PO 繼承 `BaseMultiRowEVADaoPO`(61 支),規則不同:

| 面向 | 單筆 | 多筆 |
|---|---|---|
| 主檔 | `TableMapping MasterTable` 單一 | `List<TableMapping> MasterTable`(`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:20`) |
| 明細 | `List<TableMapping> DetailTable` | **沒有明細概念** |
| 筆數 | Add 時主檔強制恰好 1 筆,否則丟例外(`Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs:194-196`) | 無限制,整張表逐筆跑 |
| 重複檢查 | `IsExistByData` | 多一支 `IsExistByMasterPK`(`Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs:1465-1487`) |
| 複製 | `CopyDetail`(`Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs:155-227`) | `Copy`(`Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs:49-175`) |

**對事件 handler 的實際影響**:多筆版沒有明細,所以 §3.2 那行表名判斷的寫法要改成比對 `MasterTable` 清單裡的哪一張,不能直接 `!= this.MasterTable.dbTableName`(那是單筆的寫法,多筆時 `MasterTable` 是 `List` 沒有 `.dbTableName`)。

## 7. 四眼欄位與 `STATUS`

加檢核時常需要判斷「現在在哪一段」。

`STATUS` 的 12 個值分三段四動作(`architecture.md §3.10`):

| 段 | 常數 | 意思 |
|---|---|---|
| Entry | `EntryAdd` / `EntryModify` / `EntryDelete` / `EntryUndoDelete` | 輸入完成,待驗證 |
| Verify | `VerifyAdd` / `VerifyModify` / `VerifyDelete` / `VerifyUndoDelete` | 驗證完成,待覆核 |
| Approve | `ApproveAdd` / `ApproveModify` / `ApproveDelete` / `ApproveUndoDelete` | 已覆核,正式生效 |

判斷用 `TAEVAUtility`(`Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs:20-34` 吃 `string Status`,`:41-61` 吃 `DataRow`)。**它們是字串比較不是 enum**,所以拼錯不會編譯失敗。

15 個系統欄位(`DATAID` · `STATUS` · `CREATEID/DATE` · `UPDATEID/DATE` · `ENTRYID/DATE` · `VERIFYID/DATE` · `APPROVEID/DATE` · `REJECTID/DATE` · `DATAFLAG`)**都在 xsd 裡**,由引擎賦值(`runbooks/add-column.md 附錄 C` H8)。**檢核時可以讀,不要寫。**

## 8. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 確認你改的 PO 繼承 `BaseEVADaoPO` 或 `BaseMultiRowEVADaoPO` | 不是死碼基底(§0.1) |
| 2 | 每個新 handler 第一行有表名判斷 | §3.2 |
| 3 | 新增一筆(檢核應通過) | 成功;`STATUS` 進 `Entry*` |
| 4 | 新增一筆(**故意讓檢核不通過**) | 擋下來,**看得到中文訊息**,而且資料庫沒有殘留 |
| 5 | 覆核 / 核准 / 退回 各跑一次 | 狀態正確流轉,檢核在該擋的地方擋 |
| 6 | 有明細的畫面:一次新增多筆明細 | 檢核 / 流水號**只跑一次**(驗 §3.2) |
| 7 | 檢核擋下後查資料庫 | 主檔與明細都沒有半筆殘留(驗交易有回滾) |
| 8 | 若改的是共用層:抽驗**另外三支**不同模組的畫面 | 四眼流程照舊 |

**第 6 步與第 7 步最容易漏。**

## 9. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **改了完全沒反應** | 改到 `TA_PO` / `Basic4EyesPO` 死碼 | §0.1 |
| **檢核跑了好幾遍 / 流水號跳號** | handler 少了表名判斷那一行 | §3.2 |
| **使用者看到空白錯誤框** | `throw new ApplicationException("")` 沒給訊息 | §4.1 |
| **在 `BeforeAdd` 改了值但沒存進去** | 改的是明細但只處理了主檔(事件分開觸發) | §4.2 |
| **在 `After*` 改 model 沒有效果** | 參數早就綁完了 | §4.2 |
| **檢核擋下來了但資料庫有殘留** | 沒有 `throw`,只是 `return` | §4.1 |
| **稽核紀錄跟著業務資料一起消失** | 用了 `args.DbTran`,同進同退 | §4.3 |
| **自己 commit 之後整個流程壞掉** | 掛點內不能 commit / rollback | §3.1 |
| **多筆畫面上 `this.MasterTable.dbTableName` 編不過** | 多筆版 `MasterTable` 是 `List` | §6 |
| **改了共用層,別的模組壞了才發現** | 影響 271 支畫面,沒有自動化測試 | §2 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/Common/Source/Base/TA.DataAccess/BaseEVADaoPO.cs` | `:17-27` `:22-26` `:143-146` `:155-227` | §0.1 §0.2 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/BaseMultiRowEVADaoPO.cs` | `:18-31` `:49-175` | §0.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/BasicEVAPO.cs` | `:24` `:37-94` `:100-157` `:194-196` | §0.1 §3.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/MultiRowEVAPO.cs` | `:16` `:20` `:1465-1487` | §0.1 §6 |
| `Dev/Common/Source/Base/TA.DataAccess/TA_PO.cs` | `:19` | §0.1 |
| `Dev/Common/Source/Base/TA.DataAccess/Basic4EyesPO.cs` | `:28` `:2428` | §0.1 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs` | `:40-60` `:77-153` `:88-101` `:569-630` `:571` `:593-599` | §3 §4 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM603_PO.cs` | `:18` | §0.1 |
| `Dev/ATLAS.EC/Source/PO/PO.EC/MSSQL/OFDM694_PO.cs` | `:20` | §0.1 |
| `Dev/Common/Source/Utility/TA.Utility/TAEVAUtility.cs` | `:20-34` `:41-61` | §7 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **PTPFBlock DLL(或其原始碼)** | §0.2 §5 | 四眼動作的主體看不到,所以「改狀態機」只能說做不到。反編譯 `Vendor.Product.DataAccess.dll` 後可補上真正的狀態轉換規則與 `EVAStatusCode` 字面值 |
| **測試環境** | §5.1 | 「在 `BeforeAdd` 直接設 `STATUS` 略過覆核」這個做法未驗證,實測後改成明確可行 / 不可行 |
| **權限表** | §5.1 | 「誰能做哪個動作」查不到 |

## 附錄 C 與計劃書的差異

計劃書 §4 要求本手冊寫「改狀態轉換動到 `TA_PO.EVA()` 的哪一段,以及這是共用引擎、改了 923 支畫面全中」。

實際讀碼後兩點都要修正:

| 計劃書 | 實際 |
|---|---|
| 改 `TA_PO.EVA()` | **`TA_PO` 是死碼**,零繼承零實例化。改它不會有任何效果 |
| 共用引擎改了 923 支全中 | 現行主線是 `BaseEVADaoPO`(**271** 子類)與 `BaseMultiRowEVADaoPO`(**61**),不是 923;而且真正的 EVA 動作在無原始碼的 DLL 裡,repo 內能改的只有掛點 |

「改了很多支畫面全中」這個警告本身**仍然成立**,只是數字與位置不同——所以 §2 保留了它,並給了正確的影響半徑。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 23 · 圖 1 · 表格 12 · 程式錨點 32 · § 連結 43 · 引用檢查：畫面 1（缺 0） · 結果集 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/change-sp-fn-trigger.md
============================================================

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

============================================================
【文件】kb/runbooks/deploy.md
============================================================

# ATLAS 維護手冊 — 部署

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。 ⚠ 標「**〔客戶特定〕**」的是本站台的值,其他站台不同。

> **本手冊未實測。**本機沒有 PTPFBlock DLL、拿不到部署機,以下全部從 `.csproj` / `App.config` / `ProjectInstaller` 的設定反推(`architecture.md 附錄 C.1`)。第一次照做的人請把實際結果回填。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 改完程式要送測試 / 正式環境;或新裝一台伺服器 |
| 不適用 | 開發機環境建置(見 `runbooks/build-env.md`)· 資料庫本身的安裝 |
| 變數 | `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock`〔客戶特定〕 |
| 最重要的前提 | **Remoting 邊界在 UI 與 FormProxy 之間**(`architecture.md §8.1`)。這一條決定所有部署分工 |

### 0.1 一句話版本

**改 UI 佈客戶端,改其餘五層佈伺服端,`UIEntity` 兩邊都要。**

其他都是這句話的細節。

## 1. 部署拓撲

```text
[圖] 部署拓撲:客戶端、Remoting 端點、伺服端 IIS、資料與批次服務,各放什麼;四個常見陷阱
圖中文字:① 客戶端(桌機 / Citrix) / main.exe + UI.<MOD> / 改 UI 只佈這裡 / UIEntity.<MOD> / 兩端版本必須一致 / ClientUtility · 控件 · Crystal / Infragistics 19.1 / main.exe.config / 不在版控,端點寫在這 / ② Remoting / *.rem 端點 / http + binary / ATLAS_TAService / < / 內網伺服器IP> / ③ 伺服端 IIS / FormProxy · Control · PO / 四層改動佈這裡 / DataEntity · UIEntity / UIEntity 兩端都要 / TA.DataAccess 四眼引擎 / 改這裡 908 支全中 / PTPFBlock\CrystalReports / 609 支範本 / ④ 資料與批次 / Oracle / 先 DB 後程式 / DB/ 腳本 277 支 / 混編碼 · 票號級 rollback / WindowsService 四支 / 是 Remoting 呼叫端 / 設定檔商業參數 / 要合併不要覆蓋 / ⚠ 四個照直覺做就會錯的地方 / DLL 覆寫名單 25 個組件 / 重編不更新 PTPFBlock = 沒效果 / 服務帳號改網域帳號 / 會掉進 Console.ReadLine 啟動失敗 / rollback 是票號級一整包 / 不能只退一支
```

*圖:圖 1 部署拓撲。橘實框=兩端都要或改了影響全系統;灰虛框=不在版控,要向部署機拿;橘虛框=照直覺做會錯的地方,對應 §2.1 / §5.3 / §6.3。*

## 2. 核心對照表:改了什麼、要部署哪些

**這張表是本手冊的重點,其餘各節是它的展開。**

| 你改了 | 客戶端 | 伺服端 IIS | WindowsService | 資料庫 |
|---|---|---|---|---|
| `UI.<MOD>` | ✔ |  |  |  |
| `UIEntity.<MOD>`(`View.xsd`) | ✔ | ✔ | ✔(若該服務用到) |  |
| `FormProxy.<MOD>` |  | ✔ |  |  |
| `Control.<MOD>` |  | ✔ |  |  |
| `PO.<MOD>` |  | ✔ |  |  |
| `DataEntity.<MOD>`(`Model.xsd`) |  | ✔ |  |  |
| `TA.DataAccess`(四眼引擎) |  | ✔ |  |  |
| `TA.MappingCode`(代碼字典) | ✔ | ✔ | ✔ |  |
| `TA.ClientUtility` | ✔ |  |  |  |
| `TA.ServerUtility` |  | ✔ | ✔ |  |
| `TA.Utility*` 五件套 | ✔ | ✔ | ✔ |  |
| `Exceptions` | ✔ | ✔ | ✔ |  |
| `.rpt` 報表範本 | ✔(檢視) | ✔(產出) |  |  |
| SP / Function / Trigger / View |  |  |  | ✔ |
| 表結構 |  |  |  | ✔ |
| `appSettings` 的商業參數 |  | ✔ | ✔ |  |

三條規則解釋這張表:

1. **`UIEntity` 兩端都要**,因為它是跨 Remoting 序列化的型別,兩端版本不一致會在反序列化時出錯。**此為推論**,依據見 `architecture.md §8.1`。

2. **共用層(`Common/` 底下)一律三邊都佈**,因為客戶端、伺服端、批次服務都參考它。判斷方法:該組件被哪一側的專案 `ProjectReference`,就佈到哪一側;共用層通常三邊都有。

3. **WindowsService 是 Remoting 的呼叫端**(`architecture.md §8.4`),它需要的是「客戶端那一套」加上它自己的 exe,不是伺服端那一套。

### 2.1 ⚠ 先查你改的組件在不在 DLL 覆寫名單裡

`architecture.md 附錄 C.5` 列了 **25 個組件**:repo 有原始碼,但有 **143 筆 `<HintPath>`** 把它們綁成 `%PTPF%` 底下的預編 DLL。

**改了這類組件,只重編不更新 `%PTPF%` 的話,下游拿到的還是舊的。**症狀是「改了沒效果」。

查法:在該組件的 `.csproj` 裡搜 `PTPFBlock`,搜得到就是被綁 DLL 的那種。名單前幾名:

| 組件 | 被幾支 csproj 綁 DLL |
|---|---|
| `Vendor.Product.Framework.Exceptions` | 90 |
| `Vendor.Product.TA.FormProxy.EC` · `TA.MappingCode` · `TA.DataAccess` | 各 5 |
| `Vendor.Product.TA.ServerUtility` · `TA.Utility` | 各 4 |

> 開發機上這件事看不出來,因為 build 產出的落點就是 `%PTPF%`(`runbooks/build-env.md §5.1`)。**到了部署機就會爆。**

## 3. 客戶端

### 3.1 放什麼

| 檔 | 說明 |
|---|---|
| `main.exe` + 設定檔 | 主程式。**不在 repo 內**,見 §3.3 |
| `UI.<MOD>.dll` | 各模組畫面 |
| `UIEntity.<MOD>.dll` | 與伺服端**版本必須一致** |
| `Vendor.Product.TA.ClientUtility.dll` · `UI.CustomControl` · `UI.WindowControls` | 客戶端共用 |
| Infragistics v19.1 執行期 | 11 支 DLL |
| Crystal Reports 執行期 | 檢視報表用,版本見 `runbooks/build-env.md §2` |
| PTPFBlock 客戶端那部分 | `Vendor.Product.UI` / `Dialog` / `CustomerDefineControl` 等 |

### 3.2 Citrix

設定檔開了 Citrix 支援(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:262`):

```
<add key="IsSupportCitrix" value="true"/>
```

註解說明它會改變兩件事:不檢查 `main.exe` 是否重複執行、報表範本的暫存目錄從 `ApplicationData` 換到 log 目錄下的 `CrystalReport`。**部署到 Citrix 環境時這個值要是 `true`。**〔客戶特定〕

版本字串也是分開的(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:264`):`基金事務系統(VENDOR) (v 1.7.0.1)`。

### 3.3 ⚠ 客戶端的 Remoting 設定不在版控裡

全 repo 只有三支設定檔含 `<channel>`,而 `.rem` 註冊只有 20 筆——其中 18 筆屬於 `SWEmailService` / `SWService` 兩個別的 Vendor 產品,真正屬於 TA 的只有 `OFDB600_Pxy` 與 `OFDB609_Pxy` 兩筆(`architecture.md §8.1.1`)。

**908 支畫面顯然不是靠這兩筆在跑。`main.exe.config` 是部署產物,不在版控內。**

> **〔假設〕缺:部署機的 `main.exe.config`。**推論它會用同一種 `<wellknown>` 語法,替每一支 `_Pxy` 型別註冊一個 `.rem` 端點,或用萬用的 `RegisterActivatedClientType`。依據是 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189` 那筆的寫法。**拿到部署機的設定檔才能寫出正確步驟。**

## 4. 伺服端(IIS)

### 4.1 端點

從 WindowsService 的客戶端設定反推(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:189`):

```
<wellknown type="Vendor.Product.TA.FormProxy.EC.OFDB600_Pxy, Vendor.Product.TA.FormProxy.EC"
           url="http://<內網伺服器IP>/ATLAS_TAService/OFDB600_Pxy.rem"/>
```

| 項目 | 值 |
|---|---|
| 伺服器 | `<內網伺服器IP>`〔客戶特定〕——設定檔註解寫「趴板時請變更 url 屬性中的伺服器位置」 |
| 虛擬目錄 | `ATLAS_TAService`〔客戶特定〕 |
| 通道 | `http` + `binary` formatter(`…App.config:179`) |
| 驗證 | `useDefaultCredentials="true"`(Windows 整合驗證) |

### 4.2 放什麼

`FormProxy.<MOD>.dll` · `Control.<MOD>.dll` · `PO.<MOD>.dll` · `DataEntity.<MOD>.dll` · `UIEntity.<MOD>.dll` · `TA.DataAccess.dll` · `TA.ServerUtility.dll` · 共用層 · PTPFBlock 伺服端部分。

### 4.3 資料庫型態設定

執行期用哪個資料庫引擎由 Fusion 框架設定決定,不是寫死的(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:62-67`):

```
<add name="TA" dataBaseProvider="Oracle" sqlLogEnable="false"/>
```

六個具名資料庫(`Fusion` / `SWProduct` / `Logging` / `TA` / `SWEMail` / `Scripting`)本站台全設 Oracle。另有 `appSettings` 的 `DbServerType`(`…App.config:200`)。

**這兩處要一致**,而且 `DbServerType` 在同一個檔裡出現兩次(`:200` 與 `:202`),值相同所以目前無害,改的時候兩處都要改(`architecture.md 附錄 E21`)。

## 5. WindowsService 四支

### 5.1 清單

| 服務名 | 專案 | 安裝帳號 |
|---|---|---|
| `OFDB600_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600` | `LocalSystem` |
| `OFDB609_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609` | `LocalSystem` |
| `OFDB680_Service` | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680` | `LocalSystem` |
| `RSPB008_Service` | `Dev/ATLAS.RSP/Source/WindowsService/WindowsService.RSPB008` | `LocalSystem` |

服務名定義在 `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/ProjectInstaller.Designer.cs:42`,帳號在同檔 `:36`。

### 5.2 安裝與啟停

四支都有 `ProjectInstaller.cs`,所以走 `InstallUtil`:

```
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe" Vendor.Product.TA.WindowsService.OFDB600.exe
sc start OFDB600_Service
sc stop  OFDB600_Service
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe" /u Vendor.Product.TA.WindowsService.OFDB600.exe
```

> **〔假設〕缺:部署機。**`InstallUtil` 的路徑與位元版本(Framework vs Framework64)未實測。依據是專案為 .NET Framework 4.8 且含 `ProjectInstaller`,這是標準做法。

### 5.3 ⚠ 服務帳號**不能**改成網域帳號

`Program.cs` 用 `Environment.UserName` 判斷自己是不是以服務身分啟動(`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:27`):

```
if (Environment.UserName == "SYSTEM")
{
    ServiceBase.Run(ServicesToRun);      // 服務模式
}
else
{
    OFDB600_Service DebugToRun = new OFDB600_Service();
    DebugToRun.Start();
    Console.ReadLine();                  // 除錯模式
}
```

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs:26-44`

配合安裝時的 `ServiceAccount.LocalSystem`,`Environment.UserName` 才會是 `"SYSTEM"`。

**如果為了資安把服務帳號改成網域帳號,`UserName` 就不是 `"SYSTEM"`,程式會走進除錯分支,呼叫 `Console.ReadLine()`——服務沒有主控台,`ServiceBase.Run` 永遠不會被呼叫,SCM 等到逾時後判定啟動失敗。**

三支 `OFDB*` 都有這個判斷;`RSPB008` 沒有(`Program.cs` 裡沒有 `Environment.UserName`)。要改帳號就得先改這段程式。

### 5.4 服務也要跟著佈的東西

服務是 Remoting 的呼叫端,所以它的目錄要有:自己的 exe 與 `exe.config`、`FormProxy.<MOD>.dll`、`UIEntity.<MOD>.dll`、共用層、PTPFBlock。

**`exe.config` 裡有伺服器位址**(`…App.config:189`),換伺服器時四支都要改。

## 6. 資料庫腳本

### 6.1 順序

**一律先資料庫、後程式。**理由:程式端的 INSERT / UPDATE 欄位清單是執行期跟資料庫要 schema 決定的(`runbooks/add-column.md §5.2`),資料庫還沒有新欄位,程式先上線就會炸。

反過來,刪欄位要先下程式、再改資料庫。

### 6.2 編碼

`DB/` 底下 277 支腳本 **cp950 196 支 + UTF-8 BOM 81 支混用**(`architecture.md 附錄 B.5`)。

- 執行前確認你的工具用對編碼,否則中文註解會變亂碼,**有些工具會連帶把整支腳本解析壞**。

- 要程式化讀取一律走 `atlas_scan.py` 的 `read_text()`。

### 6.3 rollback

`DB/Table/` 的 rollback **不是逐檔配對**。`DB/Table/11706_rollback.sql` 是**票號級一整包**,對應該票號的 9 支正向腳本(`architecture.md 附錄 B.5`)。

所以回退時是「整個票號一起退」,不能只退其中一支。**部署前先確認該票號的 rollback 存在且涵蓋你要上的全部腳本。**

### 6.4 ⚠ 有些腳本不可重跑

`DB/Table/` 內有腳本含正式資料(受益人編號、經手人帳號),重跑會產生重複資料(`architecture.md 附錄 E`)。**執行前先看內容,不要當成冪等腳本無腦重跑。**

### 6.5 SP 大量不在版控

程式呼叫 380 支 SP,repo 只有 61 支有腳本(缺 84%,`architecture.md 附錄 B.0`)。**部署一支 SP 之前,先確認你手上這份是不是線上的最新版**——多數情況要先從資料庫 `ALL_SOURCE` 撈出來比對。細節見 `runbooks/change-sp-fn-trigger.md`。

## 7. Crystal 報表

### 7.1 範本是 build 出來的,不是部署過去的

25 支 `Report.<模組>` 專案帶 PostBuild(`Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj`):

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

所以 609 支範本在建置機上就落到 `%PTPF%\CrystalReports\`。**部署時要把這個目錄一起帶到伺服端。**

### 7.2 客戶端要有 Crystal 執行期

檢視報表在客戶端,所以客戶端要裝 Crystal Reports 執行期。版本見 `runbooks/build-env.md §2`(**13.0.4000.0 與 13.0.2000.0 兩版並存**,裝新的)。

## 8. 設定檔與連線字串

### 8.1 哪裡有連線字串

| 檔 | 用途 |
|---|---|
| `Dev/Common/Source/Base/TA.DataEntity/app.config:6` | SqlClient,**AGI 產品線的設計期殘留,不要照抄** |
| `Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` | 同上,14 筆 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` | Devart,**設計期**用的 Oracle 開發庫 |

**這些都不是執行期連線。**執行期的資料庫由 Fusion 設定決定(§4.3),實際連線字串在部署機的設定檔裡。

> **〔假設〕缺:部署機設定檔。**repo 內找不到正式環境的連線字串。依據是 repo 內的三種連線字串分別對應設計期與另一個客戶,見 `architecture.md §8.2`。

### 8.2 ⚠ 設定檔含明文密碼

`architecture.md 附錄 E3` 列了多處:資料庫密碼、服務帳號密碼、SMTP 密碼、影像印鑑系統帳密。

**部署時不要把開發用的設定檔直接複製到正式環境**,而且這些密碼在版控裡人人看得到,建議另案處理。本文一律不重製密碼值。

### 8.3 商業參數也在設定檔

`Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:207` 之類的 `appSettings` 放了短線費率、計費區間、TDCC 檔案路徑等**商業規則**。

**改這些不用重編,改設定檔重啟服務即可**——但也代表部署時如果整份覆蓋設定檔,會把站台調過的參數蓋掉。**設定檔要合併不要覆蓋。**

### 8.4 落地路徑

固定寫死在設定檔,部署機上這些目錄要先建好並給權限:

| 用途 | 路徑 |
|---|---|
| 框架 log | `C:\Vendor\VendorProduct\*.log` |
| 加密金鑰 | `C:\Vendor\Keys\DefaultKey.key`(`…App.config:43`) |
| 匯出檔 | `C:\Vendor\ExportFile` |
| TDCC 指託資料檔 | `C:\Vendor\TDCC指託\…` |

〔客戶特定〕

## 9. 驗證清單

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | 比對伺服端與客戶端的 `UIEntity.<MOD>.dll` 版本 | 兩邊相同 |
| 2 | 查你改的組件在不在 `architecture.md 附錄 C.5` 名單 | 在的話 `%PTPF%` 也更新了 |
| 3 | 開一支該模組的畫面查詢 | 查得出資料(驗 Remoting 通、PO 正常) |
| 4 | 新增 → 覆核 → 核准 一輪 | 四眼狀態正確流轉(`architecture.md §3`) |
| 5 | `sc query <服務名>` 四支 | `RUNNING` |
| 6 | 看服務 log | `C:\Vendor\VendorProduct\` 底下有新紀錄且無例外 |
| 7 | 印一支該模組的報表 | 出得來(驗 `%PTPF%\CrystalReports` 有帶到) |
| 8 | 資料庫腳本 | 對應票號的物件都存在且版本正確 |

## 10. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **改了沒效果** | 改的組件在 DLL 覆寫名單裡,`%PTPF%` 沒更新 | §2.1 |
| **改了沒效果(另一種)** | 只佈了伺服端或只佈了客戶端 | §2 對照表 |
| **反序列化例外 / 型別版本不符** | `UIEntity` 只佈了一端 | §2 規則 1 |
| **服務裝好了但啟動逾時失敗** | 服務帳號不是 `LocalSystem`,程式走進 `Console.ReadLine()` 分支 | §5.3 |
| **`ORA-00904` invalid identifier** | 程式先上線、資料庫腳本還沒跑 | §6.1 |
| **腳本執行後中文全變亂碼** | cp950 / UTF-8 BOM 混用,工具用錯編碼 | §6.2 |
| **回退時退不乾淨** | rollback 是票號級一整包,只退了其中一支 | §6.3 |
| **重跑腳本後資料重複** | 該腳本含正式資料,不可重跑 | §6.4 |
| **報表印不出來 / 找不到範本** | `%PTPF%\CrystalReports` 沒帶到伺服端 | §7.1 |
| **站台調過的費率被打回預設** | 整份覆蓋設定檔 | §8.3 |
| **連得到畫面但存檔報錯** | 資料庫型態設定 `dataBaseProvider` 與 `DbServerType` 不一致 | §4.3 |
| **換伺服器後客戶端連不上** | `main.exe.config` 的 `.rem` 位址沒改 | §3.3 §4.1 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:43` `:62-67` `:179` `:189` `:200` `:202` `:207` `:262` `:264` | §3 §4 §8 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/Program.cs` | `:26-44` `:27` | §5.3 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/ProjectInstaller.Designer.cs` | `:36` `:42` | §5.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB609/OFDB609_Service.cs` | `:40-42` | §5.1 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB680/OFDB680_Service.cs` | `:42-44` | §5.1 |
| `Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj` | `:1` | §7.1 |
| `Dev/Common/Source/Base/TA.DataEntity/app.config` | `:6` | §8.1 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config` | `:8` | §8.1 |
| `Dev/Common/Source/DataSource/DataEntity.DataSource/App.config` | `:7` | §8.1 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **部署機的 `main.exe.config`** | §3.3 §4.1 | 客戶端 Remoting 註冊方式目前是推論;補進來後寫出實際的端點清單與換機器要改哪幾行 |
| **部署機存取權** | 全篇 | 整本未實測。跑一次完整部署,把實際指令、路徑、耗時回填 |
| **正式環境連線字串與帳號** | §8.1 | 目前只知道設計期的值 |
| **PTPFBlock DLL** | §2.1 §3 §4 | 無法確認伺服端 / 客戶端各要哪幾支;目前只能給「該側專案參考到的就要」這個原則 |
| **IIS 設定(應用程式集區、`.rem` 對應)** | §4 | repo 內沒有 `web.config`,伺服端的裝載設定完全看不到 |

## 附錄 C 本手冊未實測

與 `runbooks/build-env.md 附錄 C` 同樣的狀況:**沒有任何一步實際跑過**。部署分工的結論來自 Remoting 邊界(有三項程式證據,`architecture.md §8.1`),但「複製哪些檔到哪個目錄」這種操作細節,repo 裡沒有答案。

本手冊的定位是:**拿到部署機那天的檢查清單與陷阱提醒**,特別是 §2.1(DLL 覆寫)、§5.3(服務帳號)、§6.3(票號級 rollback)、§8.3(設定檔要合併不要覆蓋)這四條——它們都是「照直覺做就會錯」的地方。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 38 · 圖 1 · 表格 12 · 程式錨點 23 · § 連結 37 · 引用檢查：畫面 1（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/runbooks/build-env.md
============================================================

# ATLAS 維護手冊 — 建置環境

> 產出日期:2026-09-14(v1)。本手冊為**純程式碼閱讀彙整 + 操作步驟**,未修改任何 ATLAS 原始碼。每一步附程式錨點,行號為分析當下版本,動手前以最新程式為準。

> ⚠ 標「**〔假設〕缺:輸入**」的段落是目前拿不到該輸入只能從結構推論,附錄 B 彙整。 ⚠ 標「**〔客戶特定〕**」的是本站台的值。

> **本手冊未實測。**本機沒有 PTPFBlock DLL 所以整個方案編不起來(`architecture.md 附錄 C.1`), 以下全部從 `.sln` / `.csproj` / `App.config` 的設定反推。拿到 DLL 後照著跑一次,把實際輸出回填。

## 0. 適用範圍與前提

| 項目 | 內容 |
|---|---|
| 適用情境 | 新人拿到 ATLAS 原始碼,要把它變成「編得起來、跑得動」的開發機 |
| 不適用 | 部署到測試 / 正式環境(見 `runbooks/deploy.md`)· 建置伺服器 / CI(repo 內沒有任何 CI 設定檔) |
| 變數 | `%ATLAS_ROOT%` = 〔客戶特定〕 · `%PTPF%` = `C:\Program Files\Vendor\PTPFBlock` |
| 主方案 | `Dev/Vendor.ATLAS.sln`,**299 個 `.csproj`**(方案內掛 252 個) |

### 0.1 先看這張:能不能編起來取決於三件事

| # | 前提 | 沒有的後果 | 怎麼確認 |
|---|---|---|---|
| 1 | **PTPFBlock DLL 在 `%PTPF%`** | 1,347 筆參考全部解析失敗,**整個方案編不起來** | `dir "%PTPF%\Vendor.Product.*.dll"` |
| 2 | **對 `C:\Program Files` 有寫入權** | 275 / 299 個專案的輸出目錄就在那裡(§5.1),沒權限 build 直接失敗 | 用系統管理員身分開 VS |
| 3 | **Devart dotConnect for Oracle** | 編得起來,但 **xsd 設計工具打不開**、Designer.cs 重生不了(`runbooks/add-column.md §3.3`) | VS 的伺服器總管有沒有 dotConnect 資料來源 |

**這三件缺任何一件,後面都不用做。**第 1 件目前就缺,見 §3。

## 1. 環境總覽

```text
[圖] 建置環境:三個前提、原始碼組成、六層建置順序、產出落點;Debug 與 Release 組態落點不同
圖中文字:① 三個前提,缺一不可 / Visual Studio 2022 / 17.5 · 要系統管理員身分 / PTPFBlock 118 支 DLL / 目前缺,本機編不起來 / Devart dotConnect / 10.1 · 開 xsd 設計檢視 / TFS workspace / 位址待確認 / ② 原始碼 299 個 csproj / Dev/Common / 共用層 23 專案 / Dev/ATLAS.* / 34 個業務模組資料夾 / Dev/Exceptions / 例外政策鏈 / DB/ / 277 支腳本 · 混編碼 / ③ 建置(六層由下往上) / DataEntity · UIEntity / xsd 先重生 Designer.cs / PO → Control → FormProxy / UI / Report.<模組> ×25 / PostBuild 複製 .rpt / ④ 產出落點 —— 最容易踩到的地方 / Debug|AnyCPU → PTPFBlock / 275/299 專案 · 與框架混放 / Release|AnyCPU → bin\Release / 落點不同,改動不生效 / PTPFBlock\CrystalReports / 609 支 .rpt
```

*圖:圖 1 建置環境。灰虛框=目前缺的前提;橘虛框=產出直接寫進框架安裝目錄,且 Debug 與 Release 落點不同——選錯組態會出現「改了不生效」。*

## 2. 版本清單

全部從 repo 的設定檔抽出來,不是問來的:

| 項目 | 版本 | 出處 |
|---|---|---|
| **Visual Studio** | **2022**(`17.5.33530.505`) | `Dev/Vendor.ATLAS.sln:3-4` |
| 方案檔格式 | `Format Version 12.00` | `Dev/Vendor.ATLAS.sln:2` |
| .NET Framework | **v4.8**(268 支)· v4.5(5 支)· v2.0(1 支) | 全庫 `<TargetFrameworkVersion>` |
| Oracle(執行期) | `Oracle.ManagedDataAccess` **4.122.21.1** | 全庫 csproj 參考 |
| Oracle(設計期) | `Devart.Data.Oracle` **10.1.134.0** | 同上,見 `architecture.md §8.2` |
| Oracle(遺留) | `System.Data.OracleClient` | 4 支 csproj,微軟已標為過時 |
| UI 控件 | **Infragistics WinForms v19.1** | `%PTPF%\Infragistics4.*.v19.1.dll`,11 支 |
| 報表 | **Crystal Reports 13.0.4000.0**(121 筆)+ **13.0.2000.0**(16 筆) | 全庫 `CrystalDecisions*` 參考 |
| 企業程式庫 | Microsoft Enterprise Library **5.1.0.0** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:3-6` |
| 框架 | Vendor Fusion **1.12.20.85** | `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config:10` |
| 版控 | **TFS**(不是 git),`.vspscc` 綁定 | `architecture.md §0` |

> **Crystal 有兩個版本並存**(13.0.4000.0 與 13.0.2000.0)。安裝時裝新的那個(13.0.4000.0),舊版參考的 16 筆多半靠組件繫結解析。若某支報表專案編不過,先看它參考的是哪一版。

> 計劃書原本從 `.v12.suo` 推測是 VS2013。**那是舊殘留**;方案檔本身寫的是 VS2022,以方案檔為準。

## 3. PTPFBlock:目前最大的缺口

### 3.1 現況

`%PTPF%` 底下應該要有 **118 個相異 DLL**,全庫對它們有 **1,347 筆 `<HintPath>` 參考**(`architecture.md 附錄 C.1`)。其中 65 支是 Vendor 自家的、53 支是第三方(Infragistics、Enterprise Library、Crystal、NPOI、FileHelpers…)。

**本機沒有這個目錄,所以本機編不起來。這不是設定問題,是缺件。**

清單在 `architecture.md 附錄 C.3`(自家前 20 支)與 `附錄 C.4`(第三方擇要)。

### 3.2 取得方式

> **〔假設〕缺:PTPFBlock DLL。**repo 內沒有這些 DLL、沒有安裝程式、沒有還原腳本,也沒有任何文件說它從哪來。三條可能的路,依可行性排:

> 1. **從既有開發機或伺服器整包複製 `C:\Program Files\Vendor\PTPFBlock\`。**最快,而且能確保版本與現行程式一致。

> 2. 向 Vendor 原廠索取對應版本的安裝包。

> 3. 從部署機的 GAC / 應用程式目錄逐支撿——**不建議**,容易撿到版本不一致的組合。

> 依據:所有 `<HintPath>` 都指向一個固定的絕對路徑,代表這是「裝在機器上」而非「隨 repo 帶走」的相依。**待胖虎確認哪台機器有。**

### 3.3 拿到之後先驗這件事

`architecture.md 附錄 C.6` 列了 HintPath 本身的四個問題,其中兩個會讓你就算裝了 DLL 還是編不過:

| 問題 | 影響範圍 | 處理 |
|---|---|---|
| **7 支 csproj 把 `Program Files` 打成 `Program`** | `ATLAS.OTA` / `ATLAS.OTAB` 的 Control/FormProxy/PO,加 `ATLAS.CLS.Report` 的 UI | 該筆參考必定解析失敗,要改 csproj 或建一個 `C:\Program\Vendor\PTPFBlock` 的目錄連結 |
| **同一支 csproj 內相對路徑層數自相矛盾** | `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj:82` 用 7 層 `..`、`:88` 用 10 層 `..`,指向同一個目錄 | **不論 repo 放在哪個路徑都不可能同時成立**;把相對改成絕對是最省事的解 |

**這兩件事沒解決,`OTA` / `OTAB` / `CLS.Report` / `TA.DataAccess` 這幾個專案編不過。**

## 4. TFS 取檔

repo 內每個專案旁都有 `.vspscc`,代表綁定 TFS 來源控制。

> **〔假設〕缺:TFS 位址與 workspace 設定。**`.vspscc` 只記錄綁定關係,不含伺服器位址;`.vssscc` 與 workspace 對應表不在 repo 內。**待胖虎提供** TFS 集合 URL 與應該對應到哪個 workspace。

> 在那之前可以照現況(檔案系統上的一份複本)開發,但**不能簽入**,而且拿不到別人的變更。

## 5. 建置

### 5.1 ⚠ 建置產出直接寫進框架安裝目錄

**這是本手冊最需要先知道的一件事。**

`299` 個 `.csproj` 裡有 **275** 支的 `<OutputPath>` 直接指向 `C:\Program Files\Vendor\PTPFBlock\`。以 `PO.CAS` 為例:

| 組態 | `OutputPath` | 錨點 |
|---|---|---|
| `Debug\|AnyCPU` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:25` |
| `Release\|AnyCPU` | `bin\Release\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:33` |
| `Debug\|x86` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:40` |
| `Release\|x86` | `C:\Program Files\Vendor\PTPFBlock\` | `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj:49` |

三件後果,每一件都會咬人:

1. **要用系統管理員身分開 VS。**寫入 `C:\Program Files` 需要提權,否則 build 會在寫檔那一步失敗。

2. **業務 DLL 與框架 DLL 混在同一個目錄。**你分不出哪些是原廠的、哪些是自己編出來的。要重建乾淨環境時特別麻煩。

3. **這正是 `architecture.md 附錄 C.5` 那個陷阱在原開發機上看不出來的原因。**那 25 個「repo 有原始碼卻被綁成預編 DLL」的組件,因為 build 產出就落在 `%PTPF%`,所以在原機器上「改了會生效」;**換一台機器、或改用 `Release|AnyCPU` 組態,同樣的改動就不生效了**。

**同一支專案四個組態落點不一致**(`Release|AnyCPU` 是唯一輸出到 `bin\Release\` 的),所以**你選哪個組態 build,決定 DLL 落在哪裡**。要與原機器行為一致就用 `Debug|AnyCPU`。

### 5.2 建置順序

方案內相依由 `ProjectReference` 決定,VS 會自己排。手動編單一模組時照六層順序(`architecture.md §2`):

```
DataEntity.<MOD>、UIEntity.<MOD>  →  PO.<MOD>  →  Control.<MOD>  →  FormProxy.<MOD>  →  UI.<MOD>
```

**改過 `.xsd` 的話,編之前要先重生 `Designer.cs`**(`runbooks/add-column.md §3.3`),否則編出來的是舊 schema。

### 5.3 報表專案會在 build 時複製 `.rpt`

25 支 `Report.<模組>` 專案帶了 PostBuild:

```
xcopy "$(ProjectDir)*.rpt" "C:\Program Files\Vendor\PTPFBlock\CrystalReports\." /d /r /y
```

`Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj`

所以 **609 支報表範本是「build 出來的」不是「部署過去的」**,落點 `%PTPF%\CrystalReports\`。同樣需要 `C:\Program Files` 的寫入權。

另有 1 支 `ATLAS.BO/Source/BO.BMS/BO.BMS.csproj` 複製到 `C:\Program Files\Vendor\TABlock\`——**另一個目錄**,而且該專案只有 1 支 cs 檔(`architecture.md 附錄 E24`)。

## 6. 資料庫端的開發環境

| 用途 | 需要什麼 | 出處 |
|---|---|---|
| **執行期**連 Oracle | ODP.NET Managed 4.122.21.1(隨 `%PTPF%` 帶) | `architecture.md §8.2` |
| **設計期**開 xsd | **Devart dotConnect for Oracle 10.1.134.0** + 連得到設計庫 | `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config:8` |
| 設計庫位址 | `Server=ora01.vendor.com.tw;Sid=ATLASDB`〔客戶特定〕 | 同上 |

**設計庫是 Vendor 的開發庫,不是客戶正式庫。**沒有它就不能用 VS 的 xsd 設計工具重生 typed DataSet——這是加欄位、加畫面兩本手冊的必要條件。

> 設定檔裡另有多組 `System.Data.SqlClient` 的連線字串(`Dev/Common/Source/Base/TA.DataEntity/app.config:6` 等 15 筆),那是另一個客戶(AGI)產品線的設計期殘留,**不要照著設**,見 `architecture.md §8.2.1`。

> 這些設定檔含明文密碼(`architecture.md 附錄 E3`)。本文不重製密碼值。

## 7. 驗證清單

照順序做,每一步過了才做下一步:

| # | 動作 | 過關標準 |
|---|---|---|
| 1 | `dir "%PTPF%\*.dll"` | 檔案數接近 118 |
| 2 | 用系統管理員身分開 `Dev/Vendor.ATLAS.sln` | 方案載入無「專案無法載入」 |
| 3 | 單編 `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj` | 成功。**這支是共用最底層,它過了才有意義往上編** |
| 4 | 單編 `PO.CAS` → `Control.CAS` → `FormProxy.CAS` → `UI.CAS` | 依序成功 |
| 5 | 在 VS 開 `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | 設計檢視打得開(驗 Devart 裝好了) |
| 6 | 對該 xsd 執行自訂工具 | `CASM001Model.Designer.cs` 時間戳有更新 |
| 7 | 全方案 Rebuild(`Debug\|AnyCPU`) | 0 errors |
| 8 | 編 `ATLAS.OTA` 與 `ATLAS.CLS.Report` | 若失敗,回去做 §3.3 的 HintPath 修正 |

## 8. 常見錯誤與症狀

| 症狀 | 病因 | 回去做 |
|---|---|---|
| **幾百個「找不到型別或命名空間」** | `%PTPF%` 不存在或不完整 | §3.1 §3.2 |
| **「無法寫入檔案 … 存取被拒」** | 沒有 `C:\Program Files` 寫入權 | §5.1——用系統管理員開 VS |
| **只有 `OTA` / `OTAB` / `CLS.Report` 編不過** | 那 7 支 csproj 的 `\Program\` 路徑打錯 | §3.3 |
| **`TA.DataAccess` 編不過,別的都好** | 同一支 csproj 內 7 層 / 10 層 `..` 相對路徑矛盾 | §3.3 |
| **xsd 用設計檢視打不開,只跳 XML 原始碼** | 沒裝 Devart dotConnect | §6 |
| **改了 xsd 但編出來還是舊欄位** | 沒重生 `Designer.cs` | `runbooks/add-column.md §3.3` |
| **改了共用層、重編了,執行起來還是舊行為** | 用了 `Release\|AnyCPU`,DLL 落在 `bin\Release\` 沒進 `%PTPF%` | §5.1 |
| **報表範本沒更新** | 沒編 `Report.<模組>` 專案(範本靠 PostBuild 複製) | §5.3 |
| **簽入時說沒有繫結 / 找不到 workspace** | TFS 綁定資訊不全 | §4 |

## 附錄 A 本手冊引用的檔案清單

| 檔 | 錨點 | 用在 |
|---|---|---|
| `Dev/Vendor.ATLAS.sln` | `:2` `:3-4` | §2 |
| `Dev/ATLAS.CAS/Source/PO/PO.CAS/PO.CAS.csproj` | `:25` `:33` `:40` `:49` | §5.1 |
| `Dev/ATLAS.BBS.Report/Source/CrystalReports/Report.BBS/Report.BBS.csproj` | `:1` | §5.3 |
| `Dev/ATLAS.BO/Source/BO.BMS/BO.BMS.csproj` | `:1` | §5.3 |
| `Dev/Common/Source/Base/TA.DataAccess/TA.DataAccess.csproj` | `:82` `:88` | §3.3 §7 |
| `Dev/ATLAS.EC/Source/WindowsService/WindowsService.OFDB600/App.config` | `:3-6` `:10` | §2 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/App.config` | `:8` | §6 |
| `Dev/Common/Source/Base/TA.DataEntity/app.config` | `:6` | §6 |
| `Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd` | `:1` | §7 |
| `Dev/ATLAS.OTA/Source/PO/PO.OTA/PO.OTA.csproj` | `:1` | §3.3 |

## 附錄 B 待輸入回填

| 缺什麼 | 影響哪幾段 | 補進來後要改什麼 |
|---|---|---|
| **PTPFBlock DLL(或哪台機器有)** | §0.1 §3 §5 §7 全部 | 整本手冊都是推論。拿到後跑一次 §7 的八步,把實際輸出、錯誤訊息、耗時貼進來 |
| **TFS 集合 URL 與 workspace 對應** | §4 | 寫出實際的取檔步驟 |
| **設計庫帳密** | §6 §7 第 5–6 步 | 驗證 xsd 設計工具真的打得開 |
| **原開發機的 VS 擴充清單** | §2 | 目前只知道 VS2022 + Devart;Crystal 的 VS 整合套件版本、Infragistics 的設計期授權都還沒確認 |

## 附錄 C 本手冊未實測

`runbooks/add-column.md 附錄 C` 有一份「計劃書假設 vs 實際」對照。本手冊沒有那種對照表,因為**沒有任何一步實際跑過**——缺 PTPFBlock,連第一步都做不了。

所以本手冊的定位是:**拿到 DLL 那天的檢查清單**,不是已驗證的操作紀錄。照著跑第一次的人,請把每一步的實際結果回填,並把版本升成 v2。

由 build_doc.py v2.0.0 於 2026-09-14 14:23 產生 · 標題 20 · 圖 1 · 表格 10 · 程式錨點 26 · § 連結 32 · 引用檢查：

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
