<!-- 由 tools/build_copilot_kb.py 從 runbooks/add-screen.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-14 -->

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
