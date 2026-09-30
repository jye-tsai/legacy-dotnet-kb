<!-- 由 tools/build_copilot_kb.py 從 runbooks/add-column.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

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
