<!-- 由 tools/build_copilot_kb.py 從 modules/cpm.html 產生,請勿手改 -->
<!-- doc-date: 2026-09-15 -->

# ATLAS CPM 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:CPM 的重心不在維護畫面而在**簽核鏈**。趕時間只讀三段:§0.2(兩條互不相通的業務線)、**§6(六支 B 畫面 —— 四支是同一組表上的四道關卡,這是全篇最重要的一節)**、附錄 E(踩雷)。要查某個 `COMPLAIN_STATUS` 值是誰寫的、下一關是誰,直接翻 §2.7 與 §6.7。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、`CPM003A` 的權限欄位中文名、以及程式內寄發的 EMAIL 主旨**推測**。ATLAS 沒有把畫面中文名放進版控;本模組 13 支畫面沒有任何一支有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼(`OP1` 股務代理 / `M2` / `C3` / `C4` / `C5` / `E` / `E1` / `G2` / `G3` / `G12` / `G13` / `G17` / `GA`)、員工代號 `920406` / `102744`、寄件人 `ta-it@example.com`、`op%` 帳號前綴為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`CPM007A` 被 OFD 的 `OFDI011` 讀、`CPM001A` 被全系統的 `MailUtility` 讀(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`TA.MappingCode` 看 `architecture.md §7.2`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CPM 管「客戶／業務員提出的意見案件從受理到結案的簽核流轉」,而且是兩套完全獨立的流程 —— 需求處理件／抱怨記錄件(`CPM004A`)走五道關卡,客訴件(`CPM007A`)走三道關卡。**

推測依據逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 權限欄位中文名(最強證據) | `CPM003A` 六個旗標欄位的 `msdata:Caption` 直接寫出五道關卡的名字:「處理件維護權限」「處理件確認權限」「處理件指定部門處理權限」「處理件指定部門處理確認權限」「處理件結案權限」「客訴件結案權限」 | `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM003Model.xsd:21-25`、`:46` |
| 主表欄位中文名 | `CPM004A` 有「處理件單號」「受理日期」「受理部門」「指定處理部門」「處理部門」「預計完成日」「展延日期」「結案日期」「回覆情形」 | `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM004Model.xsd`(欄位表見 §2.5) |
| EMAIL 主旨與內文 | 「【簽核通知】需求處理件(CPMB001)」「簽核程式:CPMB002 指定部門處理確認」「【指定處理部門確認通知】…簽核程式:CPMB003 處理部門處理確認」 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:372-376`、`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:414-417` |
| 資料型態分流 | `DECODE(CPM004A.DATA_TYPE,'1','需求處理件','2','抱怨記錄件',' ')` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:251` |
| 客訴件欄位中文名 | `CPM007A` 有「客訴件單號」「申請人」「組主管」「部門主管」「主管確認日期」「客戶訴求」「業務單位建議」「Compliance建議」「客訴收件窗口建議」「CEO審核」「改善建議」 | `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB005Model.xsd`(欄位表見 §2.5) |

「CPM」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「處理件」與「客訴件」描述兩條線,這是從上表推出來的,不是官方名稱。

兩條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| **A 處理件線**(需求處理件 `DATA_TYPE='1'` / 抱怨記錄件 `DATA_TYPE='2'`) | 受理 → 受理部門確認並指定處理部門 → 指定處理部門簽核 → 處理部門簽核 → 結案或退回重辦 | `CPMM004`(建檔)+ `CPMB001`~`CPMB004`(四道關卡)+ `CPMR004`~`CPMR006`(報表) | `CPM004A` 主檔 + `CPM005A` / `CPM006A` / `CPM0061A` 三張代碼明細 |
| **B 客訴件線** | 業務員申請 → 主管確認 → 收件窗口結案 | `CPMM005`(建檔)+ `CPMB005`(主管確認)+ `CPMB006`(結案) | `CPM007A` 單一主檔,**無明細** |
| C 權限與通知設定 | 誰能過哪一關、誰要收簽核通知信 | `CPMM003`(關卡權限 + 管轄部門)、`CPMM001`(各功能的通知名單) | `CPM003A` / `CPM0031A`、`CPM001A` |

### 0.2 兩條業務線互不相通

看起來兩條線都叫「客戶意見」,但程式上**零交集**:

| 面向 | 處理件線 | 客訴件線 |
|---|---|---|
| 主表 | `CPM004A`(69 欄) | `CPM007A`(43 欄) |
| 單號欄 | `COMPLAIN_NO`,流水號類別 `SrNo.COMPLAIN_NO = "CPM004A"`(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:331`) | `CLAIM_NO`,流水號類別 `SrNo.CLAIM_NO = "CPM007A"`(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:336`) |
| 狀態欄 | `COMPLAIN_STATUS`,值域 `COD006A.CODE_SORT = 'Q2'` | `CLAIM_STATUS`,值域 `COD006A.CODE_SORT = 'P7'` |
| 權限來源 | `CPM003A.MGM_CD_CPMM004` / `MGM_CD_CPMB001`~`MGM_CD_CPMB004` + `CPM0031A.DEPT_NO` 管轄部門 | 只有 `CPM003A.MGM_CD_CPMB006`(結案關),**申請關與主管確認關完全沒有權限檢查** |
| PO 基底 | `BaseEVADaoPO`(四眼引擎) | `CPMM005` 是 `BaseEVADaoPO`;`CPMB005` / `CPMB006` **不繼承任何基底**,是裸 DAO |
| 兩條線唯一交集 | 都用 `CPM001A` 當「找不到收件者時的備援通知名單」(`MailUtility.GetNotifyMail`) | 同左 |

**沒有任何程式把一張 `CPM004A` 轉成 `CPM007A`(或反向)**。全庫 grep `CLAIM_NO` 與 `COMPLAIN_NO` 同時出現的檔案,只有 `SysCode.cs` 的流水號常數清單。

### 0.3 這模組最反直覺的三件事

**一、六支 `B` 畫面沒有一支是排程批次。** 六支全部繼承 `xOneStepProcessForm`,畫面長相是「查詢 → 清單 Grid → 雙擊某一列 → 跳出彈出視窗 → 按確定」,一次處理一筆。`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:139-171` 的 `ugrdCPMB001_DoubleClickRow` 就是整個 B 畫面唯一會寫資料的入口。repo 內沒有任何 `WindowsService.CPM*` 專案,也沒有排程設定。**它們是「簽核工作佇列」,不是批次。**

**二、四支處理件關卡畫面的「執行」按鈕是空操作。** `CPMB001`~`CPMB004` 的 PO 都有 `ExecuteNonQuery`,但四支的本體都是同一段:

```
public T ExecuteNonQuery<T>(T mModel, params object[] args)
{
    CPMB001ModelVDB model = mModel as CPMB001ModelVDB;
    //UpdateDataList(model);
    return mModel;
}
```

(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:210-215`;`CPMB002_PO.cs:229-234`、`CPMB003_PO.cs:231-236`、`CPMB004_PO.cs:234-239` 逐字相同)

原本的 `UpdateDataList` 整支(約 90 行 UPDATE + 參數綁定)被註解在檔案裡(例 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:221-310`)。按下「執行」會走一趟 Remoting、回傳一個沒改過的 VDB,**畫面不會報錯**。真正寫資料的是雙擊後彈出視窗按「確定」→ `pxy.Modify()`。詳見 §6.2 與附錄 E.3。

**三、四支關卡共用同一組主明細,但每一關寫的是不同欄位。** `CPMB001` / `CPMB002` / `CPMB003` / `CPMB004` / `CPMM004` 五支的 `xTableMapping` 宣告**逐字相同**(主 `CPM004A`,明細 `CPM005A` / `CPM006A` / `CPM0061A`),差別全在三個地方:(1) Grid 的 `SELECT` 撈哪些 `COMPLAIN_STATUS`、(2) 彈出視窗把 `COMPLAIN_STATUS` 推到哪一個值、(3) 彈出視窗填哪一組 `*_UID` / `*_DATE` / `*_TIME` 欄位。§6 把三件事逐支攤開。

### 0.4 不管什麼

| 不管 | 誰在管 |
|---|---|
| 受益人／戶號基本資料 | `BMS001A`,CPM 只讀(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:330-354`) |
| 員工、部門、離職日 | `COD009`,CPM 只讀 |
| 部門中文名 | `OFD002`,CPM 只讀 |
| 代碼說明 | `COD006A`(`CODE_SORT` = `12` / `13` / `Q2` / `P7`)與 `CTL014`(`SOURCETYPE` = `486` / `487` / `492`),CPM 只讀 |
| 使用者帳號與 EMAIL | `TA_AA_USER`,CPM 只讀 |
| 待辦事項(ToDo)清單 | 四眼引擎與 PTPF 庫,見 `architecture.md §3` |
| 真正的信件寄送 | `MailUtility`(`Dev/Common/Source/Utility/TA.ClientUtility/MailUtility.cs`),CPM 只組收件者與內文 |

### 0.5 使用角色(推測)

| 角色 | 由什麼決定 | 能做什麼 |
|---|---|---|
| 受理人員 | `CPM003A.MGM_CD_CPMM004 = 'Y'` 且 `CPM0031A.DEPT_NO` 含該案的 `COMPLAIN_DEPT` | 用 `CPMM004` 建檔、修改、作廢申請 |
| 受理部門主管 | `CPM003A.MGM_CD_CPMB001 = 'Y'` + 同上部門條件 | 用 `CPMB001` 確認案件、指定處理部門 |
| 指定處理部門主管 | `CPM003A.MGM_CD_CPMB002 = 'Y'` 且 `CPM0031A.DEPT_NO` = 該案 `ASN_SOLVE_DEPT_NO`;第二關另需 `CPM003A.MANGR_CODE = 'Y'` | 用 `CPMB002` 簽核、指派處理部門 |
| 處理部門主管 | `CPM003A.MGM_CD_CPMB003 = 'Y'` 且 `CPM0031A.DEPT_NO` = 該案 `SOLVE_DEPT_NO`;第二關另需 `MANGR_CODE = 'Y'` | 用 `CPMB003` 簽核、填處理說明 |
| 結案人員 | `CPM003A.MGM_CD_CPMB004 = 'Y'` + `CPM0031A.DEPT_NO` 含 `COMPLAIN_DEPT` | 用 `CPMB004` 結案或退回重辦 |
| 股代人員〔客戶特定〕 | 帳號 `USERID LIKE 'op%'`,或所屬 `COD009.DEPT_NO = 'M2'` | `ASN_SOLVE_DEPT_NO = 'OP1'` 的案件多一道股代簽核,見 §6.4 |
| 客訴件申請人 | 無任何旗標 | 用 `CPMM005` 建檔 |
| 客訴件主管 | **無檢查**(見附錄 E.2) | 用 `CPMB005` 確認 |
| 客訴件收件窗口 | `CPM003A.MGM_CD_CPMB006 = 'Y'` | 用 `CPMB006` 結案 |
| 全模組管理者 | 出現在資料庫 View `CPMB001_MGN_V` 內 | `CPMB001` 彈出視窗才會顯示「刪除」鈕(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:654-681`) |

`CPMB001_MGN_V` 這個 View **不在版控**(`DB/View/` 底下找不到),內容只能到現場查。標**假設**:從 `SELECT EMP_NO, UID_CODE, EMP_NAME FROM CPMB001_MGN_V WHERE UID_CODE = :UID_CODE` 推測它是一張「主管白名單」。

### 0.6 全域開關

| 開關 | 位置 | 效果 |
|---|---|---|
| `CPM003A.MGM_CD_CPMM004` … `MGM_CD_CPMB004`、`MGM_CD_CPMB006` | `CPMM003` 維護 | 六個 `Y`/`N` 旗標,逐關卡決定誰看得到工作佇列 |
| `CPM003A.MANGR_CODE`(主管辨識碼) | `CPMM003` 維護 | `CPMB002` / `CPMB003` 的**第二關**(`03H`→`03`、`04H`→`04`)只有 `Y` 的人看得到 |
| `CPM003A.SEND_EMAIL_YN` | `CPMM003` 維護 | 逐人決定要不要收簽核通知信 |
| `CPM003A.CLOSE_SEND_EMAIL_YN` | `CPMM003` 維護 | 逐人決定要不要收**結案**通知信,只有 `CPMB004` 的 `GetCloseEmail` 在用(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:653`) |
| `CPM0031A.DEPT_NO` | `CPMM003` 明細 | 一個人可以掛多個管轄部門;**沒有掛部門的人,四支關卡畫面一筆都查不到** |
| `CPM001A`(FUNCTIONID + USERID) | `CPMM001` 維護 | 「找不到收件者」時的備援通知名單。跨模組共用,見 §8.2 |
| `CPM004A.CC_EMAIL_YN` + 五個 `CC_EMAIL_*` | `CPMM004` 逐案設定 | 決定要不要副知法律顧問 / 法令遵循 / 風險管理 / 行銷 / 通路五個部門〔客戶特定〕 |

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CPM 全景:處理件五道關卡、抱怨記錄件兩關、客訴件三關,以及權限與通知設定
圖中文字:① 處理件線:一支建檔 + 四道關卡,全掛在 CPM004A 上 / CPMM004 / 建檔 / CPMB001 / 第一關 確認 / CPMB002 / 第二關 指定部門 / CPMB003 / 第三關 處理部門 / CPMB004 / 第四關 結案退回 / ② 狀態機:COMPLAIN_STATUS 一路被推,沒有任何一關檢查前一關 / 01 待確認 / CPMM004 寫 / 02 待指定部門 / CPMB001 寫 / 03H 03O 03 / CPMB002 寫 股代三關 / 04H 04O 04 / CPMB003 寫 股代三關 / 06 結案 / 05 退回 / CPMB004 寫 / ③ 抱怨記錄件 DATA_TYPE=2 只走兩關 / CPMM004 建檔 / DATA_TYPE=2 / CPMB001 確認 / 直接推 04S / CPMB004 結案 / 跳過 B002 B003 / ④ 客訴件線:另一組表、另一套狀態、權限只有最後一關有 / CPMM005 / 建檔 狀態01 / CPMB005 / 主管確認 無權限檢查 / CPMB006 / 結案 有旗標才推狀態 / CPM007A / 客訴件主檔 43 欄 / ⑤ 設定與通知 / CPMM003 / 六個關卡權限旗標 / CPM003A CPM0031A / 使用者 x 管轄部門 / CPMM001 / 備援通知名單 / CPM001A 全系統共用 / DSM 也讀
```

*圖:圖 1 CPM 全景。橘框=本模組主要入口;橘虛框=行為要留意(跳關、缺權限檢查);灰虛框=跨模組共用。五支處理件畫面掛的是同一組主明細,差別只在狀態與欄位群 —— 見圖 4。*

### 1.2 資料表關係

八張表分兩群:處理件群(`CPM004A` + 三張代碼明細)、客訴件群(`CPM007A` 單張),外加設定群(`CPM003A`/`CPM0031A`、`CPM001A`)。圖見 §2 開頭。

### 1.3 主要維護畫面的四眼與卡控順序

`CPMM004` 與 `CPMM005` 是模組內唯二掛滿八個 `After*` 事件的畫面,但兩支的 `After*` **只做跳號一覽表**(`SrNoCommentProcessor.AddCommentHistory`),零業務 SQL —— 也就是 `architecture.md §3.8.1` 講的「四眼只留軌跡,不把關資料」那一型。圖見 §4 開頭。

### 1.4 批次資料流

四支關卡畫面在 `CPM004A` 上依 `COMPLAIN_STATUS` 接力。圖見 §6 開頭,那是本篇最重要的一張。

### 1.5 一日作業泳道

沒有排程,所以沒有「一日」的概念。實際節奏是**事件驅動**:

| 順序 | 誰 | 動作 | 觸發下一步的方式 |
|---|---|---|---|
| 1 | 受理人員 | `CPMM004` 建檔 → `COMPLAIN_STATUS = '01'` | `CPMM004_AfterAddButtonClicked` 寄信給該部門有 `MGM_CD_CPMB001` 的人(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:657-660`) |
| 2 | 受理部門主管 | `CPMB001` 確認 → `'02'`(或客訴型態直接 `'04S'`) | 寄信給指定處理部門有 `MGM_CD_CPMB002` 的人(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:372-380`) |
| 3 | 指定處理部門 | `CPMB002` 兩關(一般)或三關(股代)→ `'03'` | `COMPLAIN_STATUS == "03"` 才寄信(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:324-325`) |
| 4 | 處理部門 | `CPMB003` 兩關或三關 → `'04'` | `COMPLAIN_STATUS == "04"` 才寄信(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:352-353`) |
| 5 | 結案人員 | `CPMB004` 選 `'06'` 結案或 `'05'` 退回重辦 | 一律寄信(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:280`) |
| 5' | (退回時) | 回到步驟 2,由 `CPMB001` 以 `'05'` 重新確認 | 見 §6.7 的回圈 |

**沒有任何一步有時限檢查。** `COMPLAIN_PRV_DATE`(預計完成日)只在 `CPMM004` 依 `COMPLAIN_KIND` 算出來存著(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:868-886`),之後沒有任何程式拿它跟今天比。逾期靠 `CPMR004` / `CPMR006` 報表人工看。

## 2. 資料模型

```text
[圖] CPM 八張表的主明細關係、主鍵組成,以及外部唯讀表
圖中文字:處理件群:一主三明細,四支關卡 + CPMM004 共用 / CPM004A / 主檔 69 欄 PK COMPLAIN_NO / CPM005A / 明細 處理件分類 12 / CPM006A / 明細 處理方式 13 / CPM0061A / 明細 指定部門方式 13 / 客訴件群:單張主檔,沒有明細 / CPM007A / 主檔 43 欄 PK CLAIM_NO / OFDI011 唯讀 / OFD 模組客戶查詢 / 設定群 / CPM003A / 使用者權限 六旗標 / CPM0031A / 管轄部門 一對多 / CPM001A / 功能 x 通知名單 / DSMR007 等外部 / 透過 MailUtility 讀 / 外部唯讀表(join 進來,不屬本模組) / COD009 / 員工 部門 離職日 / COD006A / 12 13 Q2 P7 / CTL014 / 486 487 492 / OFD002 / 部門中文名 / BMS001A TA_AA_USER / 受益人 帳號 EMAIL
```

*圖:圖 2 資料模型。橘框=主檔;實線箭頭=主明細(同一次 EVA 一起送審);灰虛框=跨模組;黑框=外部唯讀表。CPM006A 與 CPM0061A 欄位結構完全相同,只差語意。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

| 畫面 | PO 基底 | 主檔 | 明細 | 錨點 |
|---|---|---|---|---|
| `CPMM001` | `BaseMultiRowEVADaoPO` | `CPM001A`(多筆主檔) | 無 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:33-35` |
| `CPMM003` | `BaseEVADaoPO` | `CPM003A` | `CPM0031A` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM003_PO.cs:40-41` |
| `CPMM004` | `BaseEVADaoPO` | `CPM004A` | `CPM005A`、`CPM006A`、`CPM0061A` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:62-65` |
| `CPMM005` | `BaseEVADaoPO` | `CPM007A` | 無 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:49` |
| `CPMB001` | `BaseEVADaoPO` | `CPM004A` | `CPM005A`、`CPM006A`、`CPM0061A` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:49-52` |
| `CPMB002` | `BaseEVADaoPO` | `CPM004A` | 同上 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:50-53` |
| `CPMB003` | `BaseEVADaoPO` | `CPM004A` | 同上 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:50-53` |
| `CPMB004` | `BaseEVADaoPO` | `CPM004A` | 同上 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:50-53` |
| `CPMB005` | **無基底**(`: ICPMB005_PO`) | **沒宣告** | 沒宣告 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:37`、`:43-47` |
| `CPMB006` | **無基底** | **沒宣告** | 沒宣告 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:38`、`:44-47` |
| `CPMR004` | `BaseEVADaoPO` | `CPM004A` | `CPM005A`、`CPM006A`(**少 `CPM0061A`**) | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:46-48` |
| `CPMR005` / `CPMR006` | **無基底** | 沒宣告 | 沒宣告 | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:28`、`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs:27` |

兩件事要記住:

1. **`CPMB005` / `CPMB006` 沒宣告主明細,是因為它們根本不走四眼引擎。** 兩支的 PO 只實作 `Select` / `Update` / `ExecuteNonQuery` 三個自訂方法,`UpdateDataList` 用手寫的 `UPDATE CPM007A … WHERE CLAIM_NO = :CLAIM_NO` 自己開交易(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:216-329`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:216-337`)。建構子裡那行 `//this.MasterTable = new TableMapping("OFD701", "SEAL");` 是從 OFD 複製過來忘了刪的殘骸(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:46`)。詳見 §6.10。

2. **`CPMR004` 的明細少一張。** 它宣告 `CPM005A` + `CPM006A`,沒有 `CPM0061A`(指定處理部門處理方式)。同一張主檔在報表側與維護側的明細組不一致,`CPMR004p0` 彈出視窗看不到指定處理部門的處理方式代碼。

### 2.2 主鍵與四眼欄位

| 表 | 主鍵(反推自 PO 的 WHERE 與 `SetMasterToDetail`) | 四眼 13 欄 | `DATAFLAG` | 欄位數 |
|---|---|---|---|---|
| `CPM001A` | `FUNCTIONID` + `USERID`(`MasterPKey`,`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:33-34`) | 有 | 有 | 20 |
| `CPM003A` | `USERID` | 有 | 有 | 29 |
| `CPM0031A` | `USERID` + `DEPT_NO` | 有 | 有 | 18 |
| `CPM004A` | `COMPLAIN_NO` | 有 | 有 | 69 |
| `CPM005A` | `COMPLAIN_NO` + `COMPLAIN_CODE` | 有 | 有 | 18 |
| `CPM006A` | `COMPLAIN_NO` + `SOLVE_CODE` | 有 | 有 | 18 |
| `CPM0061A` | `COMPLAIN_NO` + `SOLVE_CODE` | 有 | 有 | 18 |
| `CPM007A` | `CLAIM_NO` | 有 | 有 | 43 |

明細 PK 的第二段來自 `CPMM004` 的 `m_PkeyNotInMaster.Add("COMPLAIN_CODE")` 與 `.Add("SOLVE_CODE")`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:218-219`)—— 這是框架用來判斷「明細自己的 PK 欄位」的宣告。`CPM006A` 與 `CPM0061A` 欄位結構**完全相同**(`DATAID` / `COMPLAIN_NO` / `SOLVE_CODE` + 四眼 + `CODE_DESCRP`),差別只在語意:`CPM006A` 是處理部門的處理方式、`CPM0061A` 是指定處理部門的處理方式。

八張表的四眼欄位都齊,但**只有 `CPMM003` / `CPMM004` / `CPMM005` / `CPMM001` 四支 M 畫面真的走四眼按鈕**。四支 B 關卡畫面(§6)是直接叫 `Modify`,`CPMB005` / `CPMB006` 更是自己寫 `UPDATE`,一律把 `STATUS` 硬塞 `'301'`。見 §2.7 與附錄 E.1。

### 2.3 `CPM004A` 的 33 個流程欄位:五道關卡各寫哪一組

`CPM004A` 69 欄裡有 33 欄是「某一關的人、日期、時間」。這張表是讀本模組最需要的一張,因為欄名跟關卡的對應**完全不直觀**(例:第三關 `CPMB003` 寫的是 `SOLVE_CFM_*`,第二關 `CPMB002` 寫的卻是 `SOLVE_*`):

| 關卡 | 欄位 | 中文名(`msdata:Caption`) | 寫入錨點 |
|---|---|---|---|
| 建檔 `CPMM004` | `COMPLAIN_UID` / `COMPLAIN_DEPT` / `COMPLAIN_DATE` / `COMPLAIN_TIME` | 受理人員 / 受理部門 / 受理日期 / 受理時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:53`、`:66-74` |
| 建檔 `CPMM004` | `COMPLAIN_KIND` / `COMPLAIN_PRV_DATE` | 處理時效 / 預計完成日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:85-87`,算法在 `:868-886` |
| 第一關 `CPMB001`(正常件) | `COMPLAIN_CFM_UID` / `COMPLAIN_CFM_DATE` / `COMPLAIN_CFM_TIME` | 受理部門主管 / 受理單位完成日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:236-241` |
| 第一關 `CPMB001`(重辦件,原狀態 `05`) | `SOLVE_CFM_UID1` / `SOLVE_CFM_DATE1` / `SOLVE_CFM_TIME1` | 重新處理受埋部門主管 / 確認日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:242-247` |
| 第一關 `CPMB001` | `ASN_SOLVE_DEPT_NO` / `COMPLAIN_COMM` | 指定處理部門 / 受理內容說明 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:232-234` |
| 第二關 `CPMB002`(首辦) | `SOLVE_UID` / `SOLVE_DATE` / `SOLVE_TIME` | 指定處理部門主管 / 完成日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:302-308` |
| 第二關 `CPMB002`(重辦) | `SOLVE_UID1` / `SOLVE_DATE1` / `SOLVE_TIME1` | 重新處理指定處理部門主管 / 日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:309-315` |
| 第二關 `CPMB002` | `SOLVE_DEPT_NO` / `ASN_EMP_NO` / `COMPLAIN_SOLUTION_SOLVE` / `COMPLAIN_DELAY_DATE` | 處理部門 / 指定處理部門處理人員 / 指定處理部門處理說明 / 展延日期 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:289-296` |
| 第三關 `CPMB003`(首辦) | `SOLVE_CFM_UID` / `SOLVE_CFM_DATE` / `SOLVE_CFM_TIME` | 處理部門主管 / 完成日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:331-336` |
| 第三關 `CPMB003`(重辦) | `COMPLAIN_CFM_UID1` / `COMPLAIN_CFM_DATE1` / `COMPLAIN_CFM_TIME1` | 重新處理件處理部門主管 / 完成日期 / 時間 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:337-342` |
| 第三關 `CPMB003` | `DEPT_SOLVE_EMP_NO` / `COMPLAIN_SOLUTION` | 處理人員 / 處理部門處理說明 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:323-325` |
| 第四關 `CPMB004`(結案) | `CLOSE_DATE` / `COMPLAIN_REMARK` | 結案日期 / 回覆情形 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:246-251` |
| 第四關 `CPMB004`(退回重辦) | `VERIFY_DATE` / `COMPLAIN_DELAY_DATE` / `COMPLAIN_PRV_DATE1`,並清空六個重辦欄位 | 處理件退件日期 / 展延日期 / 預計完成日(退件) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:256-272` |

**「首辦 / 重辦」怎麼判?** 三支關卡畫面用的都是同一招:看 `custSOLVE_CFM_UID1.Value` 是不是空的(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:302`、`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:331`)。而 `SOLVE_CFM_UID1` 正是 `CPMB001` 在處理 `05`(重新處理)案件時寫進去的。所以整條「重辦分支」是靠這一個欄位串起來的,`CPMB004` 退回時也是把它連同另外五欄一起清空(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:262-272`)—— 少清一欄,後面兩關就會走錯分支。

還有一組 `SOLVE_DATE11` / `SOLVE_TIME11` / `SOLVE_CFM_UID11` / `SOLVE_CFM_DATE11` / `SOLVE_CFM_TIME11` / `COMPLAIN_COMM1` / `COMPLAIN_SOLUTION1` / `COMPLAIN_REMARK1` 只出現在 `CPMB001Model.xsd` 的 `CPM004A_SELECT` 結果集(`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB001Model.xsd`),**實體表 `CPM004A` 沒有這些欄位,程式也沒有任何一處讀寫它們**。判定為死欄位。

### 2.4 代碼值域:哪些查表、哪些寫死

`architecture.md §7.2` 提到 `TA.MappingCode` 有一整組 `CAMPAIGN_*` / `CAMP_*` / `PROMT_TYPE` 代碼類別。**本模組一個都沒用到。** 實測:

```
grep -rn "CAMPAIGN_\|CAMP_\|PROMT_TYPE" Dev/ATLAS.CPM Dev/ATLAS.CPM.Report --include=*.cs   → 0 命中
```

`using Vendor.Product.TA.MappingCode;` 出現在每一支 PO 的 using 區(例 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:15`),但整個模組實際引用的 `TA.MappingCode` 成員只有兩個:`SQLOperator.Equal` / `SQLOperator.Like`(SQL 運算子字串)與 `SysCode.SrNo.AllotNoForNfd`(跳號一覽表的類別鍵)。**代碼值域一律是字面值或查 DB,沒有一處走常數。** 這跟 `cod.md §2` 的實測結論一致。

| 代碼欄位 | 值域來源 | 程式怎麼拿 | 寫死在哪 |
|---|---|---|---|
| `COMPLAIN_STATUS` | `COD006A` 的 `CODE_SORT = 'Q2'` | UI 下拉:`new CodeDataSrc("Q2")`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:44`);SQL join:`AND C3.CODE_SORT = 'Q2'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:134`) | **每個值都寫死在 C# 與 SQL 裡**,見 §2.7 |
| `CLAIM_STATUS` | `COD006A` 的 `CODE_SORT = 'P7'` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:108` | `'01'` / `'02'` / `'06'` 寫死,見 §2.7 |
| `COMPLAIN_CODE`(處理件分類) | `COD006A` 的 `CODE_SORT = '12'` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:535`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:846` | 未寫死,全查表 |
| `SOLVE_CODE`(處理方式) | `COD006A` 的 `CODE_SORT = '13'` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:451`、`:492` | 未寫死,全查表 |
| `COMPLAIN_KIND`(處理時效) | `CTL014` 的 `SOURCETYPE = '486'` | `new GetDropDownDataSrc("486")`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:239`) | **`'1'`/`'2'`/`'3'` 寫死在 `SetCOMPLAIN_KIND()`**,見下 |
| `CC_EMAIL_YN`(是否副知相關部門) | `CTL014` 的 `SOURCETYPE = '487'` | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:241` | `"Y"` / `"N"` 寫死 |
| `CPM003A` 六個權限旗標的 Grid 下拉 | `CTL014` 的 `SOURCETYPE = '492'` | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:121-126` | `"Y"` / `"N"` 寫死(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:49-77`) |
| `DATA_TYPE` | **無代碼表** | 直接 `DECODE(…,'1','需求處理件','2','抱怨記錄件',' ')` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:251`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:115`、`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:77-80` |

`COMPLAIN_KIND` 的三個值與工作天數是寫死的對應:

| 值 | 預計完成日 | 錨點 |
|---|---|---|
| `1` | 受理日 + **1** 個公司營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:870-873` |
| `2` | 受理日 + **2** 個公司營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:874-877` |
| `3` | 受理日 + **7** 個公司營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:878-881` |
| 其他 | **今天**(不是受理日) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:882-885` |

`CTL014` 的 `486` 若被加上第四個值,這裡會靜默落到 `else` 分支 —— 預計完成日變成當天,不會有任何提示。〔客戶特定〕且是典型的「代碼表能加、程式不能跟」。

`DATA_TYPE` 的中文對照在三個地方各寫一套,而且**不一致**:`CPMM004_PO.cs:251` 與 `CPMR005_PO.cs:77-80` 寫「需求處理件 / 抱怨記錄件」,`CPMM004_PO.cs:673` 的報表查詢卻寫「問題件 / 客訴件」,`CPMR004_PO.cs:110` 也是「問題件 / 客訴件」。同一筆資料在不同報表上顯示不同名稱。

### 2.5 欄位中文名總表(來自 xsd `msdata:Caption`)

**`CPM004A`(69 欄,主檔)** —— 四眼 13 欄與 `DATAID` / `DATAFLAG` 在 `CPMM004Model.xsd` 沒有 Caption(在 `CPM004A_SELECT` 結果集裡才有),表內以「—」表示:

| 欄位 | 中文名 | 欄位 | 中文名 |
|---|---|---|---|
| `COMPLAIN_NO` | 處理件單號 | `SOLVE_CFM_UID` | 處理部門主管 |
| `DATA_TYPE` | —(作業類型,見 §2.4) | `SOLVE_CFM_DATE` | 處理部門完成日期 |
| `DATA_TYPE_NM` | 處理件型態(結果集欄) | `SOLVE_CFM_TIME` | 處理部門完成時間 |
| `BF_NO` | 戶號 | `COMPLAIN_KIND` | 處理時效 |
| `ID_NO` | 受益人ID | `COMPLAIN_DELAY_DATE` | 展延日期 |
| `BF_NAME` | 姓名 | `COMPLAIN_PRV_DATE1` | 預計完成日(退件) |
| `EMP_NO` | 業務員 | `CC_EMAIL_YN` | EMAIL通知相關部門 |
| `AGENT_CODE` | 業務部門 | `CC_EMAIL_LAW` | EMAIL通知(法律顧問 |
| `COMPLAIN_SOLUTION_SOLVE` | 指定處理部門處理說明 | `CC_EMAIL_CMP` | EMAIL通知(法令遵循組 |
| `COMPLAIN_DATE` | 受理日期 | `CC_EMAIL_RSK` | EMAIL通知(風險管理 |
| `COMPLAIN_TIME` | 受理時間 | `CC_EMAIL_MAT` | EMAIL通知(行銷部 |
| `COMPLAIN_PRV_DATE` | 預計完成日 | `CC_EMAIL_CHN` | EMAIL通知(通路業務部 |
| `COMPLAIN_STATUS` | 處理狀態 | `COMPLAIN_TEL1` | 聯絡電話1 |
| `COMPLAIN_STATUS_DESCRP` | 處理狀態說明 | `COMPLAIN_TEL2` | 聯絡電話2 |
| `COMPLAIN_CFM_UID` | 受理部門主管 | `VERIFY_DATE` | 處理件退件日期 |
| `COMPLAIN_CFM_DATE` | 受理單位完成日期 | `COMPLAIN_COMM` | 受理內容說明 |
| `COMPLAIN_CFM_TIME` | 受理單位完成時間 | `COMPLAIN_SOLUTION` | 處理部門處理說明 |
| `ASN_SOLVE_DEPT_NO` | 指定處理部門 | `COMPLAIN_REMARK` | 回覆情形 |
| `ASN_EMP_NO` | 指定處理部門處理人員 | `SOLVE_UID1` | 重新處理指定處理部門主管 |
| `SOLVE_UID` | 指定處理部門主管 | `SOLVE_DATE1` / `SOLVE_TIME1` | 重新處理日期 / 時間 |
| `SOLVE_DEPT_NO` | 處理部門 | `SOLVE_CFM_UID1` | 重新處理受埋部門主管 |
| `DEPT_SOLVE_EMP_NO` | 處理人員 | `SOLVE_CFM_DATE1` / `SOLVE_CFM_TIME1` | 重新處理確認日期 / 時間 |
| `SOLVE_DATE` | 指定處理部門完成日期 | `CLOSE_DATE` | 結案日期 |
| `SOLVE_TIME` | 指定處理部門完成時間 | `COMPLAIN_CFM_UID1` | 重新處理件處理部門主管 |
| `COMPLAIN_UID` | 受理人員 | `COMPLAIN_CFM_DATE1` / `COMPLAIN_CFM_TIME1` | 重新處理件處理部門完成日期 / 時間 |
| `COMPLAIN_DEPT` | 受理部門 | `DATAID` / `STATUS` / 四眼 12 欄 / `DATAFLAG` | —(見 `architecture.md §3`) |

來源:`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM004Model.xsd`。注意 `SOLVE_CFM_UID1` 的 Caption 是「重新處理**受埋**部門主管」—— xsd 裡就是這個錯字,不是本文打錯。

**`CPM007A`(43 欄,客訴件主檔)**:

| 欄位 | 中文名 | 欄位 | 中文名 |
|---|---|---|---|
| `CLAIM_NO` | 客訴件單號 | `CLAIM_DOC` | 附件說明 |
| `BF_NO` | 受益人戶號 | `CLAIM_DEMAND` | 客戶訴求 |
| `ID_NO` | 統一編號 | `SALES_COMM` | 業務單位建議 |
| `BF_NAME` | 受益人姓名 | `OTHER_DEPT_COMM` | 其他單位建議 |
| `CLAIM_STATUS` | 客訴件狀態 | `COMPLIANCE_COMM` | Compliance建議 |
| `CLAIM_DATE` | 申請日期 | `SER_WINDOW_COMM` | 客訴收件窗口建議 |
| `EMP_NO` | 業務員 | `CEO_VERIFY` | CEO審核 |
| `CLAIM_EMP_NO` | 申請人 | `IMPROVE_COMM` | 改善建議 |
| `LEADER_EMP_NO` | 組主管 | `OTHER_REMARK` | 其他意見 |
| `BOSS_EMP_NO` | 部門主管 | `CLAIM_STATUS_DESCRP` | 客訴件狀態說明(結果集欄) |
| `CONFIRM_DATE` | 主管確認日期 | `EMP_NAME` | 業務員姓名(結果集欄) |
| `CLAIM_CONTENT` | 案件說明 | `CLAIM_EMP_NO_NAME` | 申請人姓名(結果集欄) |
| `CLAIM_DOC_PATH` | 文件存檔路徑 | `LEADER_EMP_NO_NAME` | 組主管姓名(結果集欄) |
| `CLOSE_DATE` | 結案日期 | `BOSS_EMP_NO_NAME` | 部門主管姓名(結果集欄) |
| `STATUS` … `DATAFLAG` | 四眼 13 欄 + 資料異動碼 |  |  |

來源:`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB005Model.xsd`。

**`CPM003A` / `CPM0031A` / `CPM001A`**:

| 表 | 欄位 | 中文名 |
|---|---|---|
| `CPM003A` | `USERID` / `MANGR_CODE` | 使用者代碼 / 主管辨識碼 |
| `CPM003A` | `MGM_CD_CPMM004` | 處理件維護權限 |
| `CPM003A` | `MGM_CD_CPMB001` | 處理件確認權限 |
| `CPM003A` | `MGM_CD_CPMB002` | 處理件指定部門處理權限 |
| `CPM003A` | `MGM_CD_CPMB003` | 處理件指定部門處理確認權限 |
| `CPM003A` | `MGM_CD_CPMB004` | 處理件結案權限 |
| `CPM003A` | `MGM_CD_CPMB006` | 客訴件結案權限 |
| `CPM003A` | `SEND_EMAIL_YN` / `CLOSE_SEND_EMAIL_YN` | 寄發EMAIL否 / 結案寄發EMAIL否 |
| `CPM003A` | `EMP_NO` / `EMP_CD` / `EMAIL` / `USERCNAME` | 員工代碼 / 員工類別 / 使用者Email / 使用者姓名(皆為 join 來的結果集欄) |
| `CPM0031A` | `DEPT_NO` / `DEPT_CH_NAME` | 部門代碼 / 部門名稱 |
| `CPM001A` | `FUNCTIONID` / `USERID` | 程式功能代碼 / 使用者代碼 |
| `CPM001A` | `USERCNAME` / `EMAIL` / `FORMNAME` | 使用者姓名 / 使用者Emai / 程式功能名稱(結果集欄) |

來源:`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM003Model.xsd:21-25`、`:46`、`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM001Model.xsd`。`CPM001A.EMAIL` 的 Caption 是「使用者Emai」,少一個 l,xsd 原文如此。

**⚠ 同一張表在不同 xsd 的 Caption 不一致。** `CPM004A_SELECT` 這個結果集在四支 B 畫面的 Model 裡都有,但中文名被改過:

| 欄位 | `CPMB001Model.xsd` / `CPMB002Model.xsd` | `CPMB003Model.xsd` / `CPMB004Model.xsd` |
|---|---|---|
| `USERCNAME` | 受理人員 | KEY單人員 |
| `COMPLAIN_DEPT_CH_NAME` | 受理部門名稱 | KEY單部門名稱 |
| `ASN_SOLVE_DEPT_CH_NAME` | 指定處理部門名稱 | **處理部門名稱** |
| `SOLVE_DEPT_CH_NAME` | 處理部門名稱 | **指定處理部門名稱** |
| `EMP_NAME` | 處理人員姓名 | 指定處理部門的處理人員姓名 |

後兩列是**對調的**:`ASN_SOLVE_DEPT_CH_NAME` 在 SQL 裡一律取自 `CPM004A.ASN_SOLVE_DEPT_NO`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:117-122` 的 `C5`),語意就是「指定處理部門」,但 `CPMB003` / `CPMB004` 的 xsd 把它標成「處理部門名稱」。Grid 欄位標題會跟資料對不上。嚴重度中,見附錄 E.6。

### 2.6 與其他模組共用的表

| 表 | 也被誰用 | 怎麼用 | 錨點 |
|---|---|---|---|
| `CPM007A` | **OFD**(`OFDI011` 客戶查詢) | 唯讀,`WHERE BF_NO = :BF_NO` 撈該戶號的客訴歷史,顯示在 `frmCLAIM` 彈出視窗 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:3953-3977`、`Dev/ATLAS.OFDI/Source/UI/UI.OFDI/frmCLAIM.cs:46` |
| `CPM001A` | **全系統**(`TA.UtilityPO`) | 唯讀,`WHERE FUNCTIONID = :ProductID` 取備援通知名單 | `Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:2753-2759` |
| `CPM004A` / `CPM005A` / `CPM006A` / `CPM0061A` / `CPM003A` / `CPM0031A` | 只有 CPM 自己 | — | — |

反向:CPM 借用的外部表(全部唯讀)

| 表 | 用途 | 典型錨點 |
|---|---|---|
| `COD009` | 員工姓名、部門、離職日、`UID_CODE` ↔ `EMP_NO` 對照、EMAIL | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:735-737` |
| `COD006A` | 四組代碼說明(`12` / `13` / `Q2` / `P7`) | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:532-536` |
| `CTL014` | 下拉選單(`486` / `487` / `492`) | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:131-132` |
| `OFD002` | 部門中文名 `DEPT_CH_NAME` / 簡稱 `DEPT_SH_NM` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM003_PO.cs:203` |
| `BMS001A` | 戶號 → `ID_NO` / `BF_NAME` 帶值 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:334-336` |
| `TA_AA_USER` | 使用者中文名與 EMAIL | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:698-700` |
| `TA_SWPRODUCTSDETAIL` | 功能代碼 → 功能中文名(`CPMM001` 用) | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:93-94` |
| `AA_USER` | **只有一處**用了這個沒有 `TA_` 前綴的名字 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:650` |
| `CPMB001_MGN_V` | 主管白名單 View,**不在版控** | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:659-661` |

### 2.7 狀態碼(從程式反推)

#### 2.7.1 `COMPLAIN_STATUS`(處理件,值域表 `COD006A.CODE_SORT = 'Q2'`)

`COD006A` 的實際內容不在版控,以下**全部由程式反推**,每個值都附「誰寫的 / 誰讀的」:

| 值 | 語意(推測) | 誰寫進去 | 誰在等這個值 |
|---|---|---|---|
| `01` | 已受理,待受理部門確認 | `CPMM004` 新增(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:57-60`) | `CPMB001` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:135`) |
| `02` | 受理部門已確認,待指定處理部門簽核 | `CPMB001`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:230`) | `CPMB002` 佇列第一關(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:151`) |
| `03H` | 指定處理部門經辦已簽,待主管 | `CPMB002`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:262`、`:286`) | `CPMB002` 佇列第二關,需 `MANGR_CODE='Y'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:153-155`) |
| `03O` | 股代主管已簽,待股務(`M2`)主管 —— **只有 `ASN_SOLVE_DEPT_NO = 'OP1'` 走得到** | `CPMB002`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:268`) | `CPMB002` 佇列第三關,需 `D.DEPT_NO = 'M2'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:157`) |
| `03` | 指定處理部門簽核完成,待處理部門 | `CPMB002`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:273`、`:286`) | `CPMB003` 佇列第一關(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:150`);**若 `SOLVE_DEPT_NO` 為空則直接跳到 `CPMB004`**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:155`) |
| `04H` | 處理部門經辦已簽,待主管 | `CPMB003`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:270`、`:294`) | `CPMB003` 佇列第二關(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:152-154`) |
| `04O` | 股代主管已簽,待 `M2` 主管 | `CPMB003`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:276`) | `CPMB003` 佇列第三關(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:156`) |
| `04` | 處理部門簽核完成,待結案 | `CPMB003`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:281`、`:294`) | `CPMB004` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:153`) |
| `04S` | **抱怨記錄件(`DATA_TYPE='2'`)專用**:`CPMB001` 確認後直接跳到結案關 | `CPMB001`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:254`) | `CPMB004` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:146`) |
| `05` | 退回重辦 | `CPMB004`(使用者從下拉選,`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:244`) | `CPMB001` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:135`) |
| `06` | 結案 | `CPMB004`(下拉選,`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:248`) | 終點,無人再撈 |
| `D1` | 作廢申請 | `CPMM004` 修改時使用者把狀態選成 `06` 會被改寫成 `D1`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:626-627`) | `CPMB001` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:135`) |
| `D2` | 作廢確認 | `CPMB001`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:230`、`:254`) | 終點;報表以 `COMPLAIN_STATUS NOT LIKE 'D%'` 排除(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:91`) |
| `07` | **死值** | 無人寫 | 唯一提及處整段被註解(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:296-320`) |

**`06` 這個值被兩套語意共用**:在 `CPMB004` 的下拉裡是「結案」,在 `CPMM004` 的修改畫面裡卻被當成「作廢」的觸發鍵然後改寫成 `D1`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:626`)。同一個代碼在兩支畫面意思不同,是讀碼時最容易誤判的一處。

#### 2.7.2 `CLAIM_STATUS`(客訴件,值域表 `COD006A.CODE_SORT = 'P7'`)

| 值 | 語意(推測) | 誰寫進去 | 誰在等 |
|---|---|---|---|
| `01` | 已申請,待主管確認 | `CPMM005` 新增時 `AddDataLoad` 直接塞(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:118-119`) | `CPMB005` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:119`) |
| `02` | 主管已確認,待收件窗口結案 | `CPMB005`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:140`) | `CPMB006` 佇列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:119`) |
| `06` | 結案 | `CPMB006`,**且操作者要有 `MGM_CD_CPMB006='Y'`**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:158-161`) | 終點 |

`CPMM005` 的重複件檢查也只認 `01` 與 `02` 兩個值(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:368`、`:399`),所以 `P7` 若有第四個「進行中」的值,重複件就擋不到。

#### 2.7.3 四眼 `STATUS`

八張表都有四眼 `STATUS`,但本模組**沒有一支畫面在讀它**。四支 B 關卡與 `CPMB005` / `CPMB006` 一律把它硬寫成 `'301'`:

- 結果集預設值:`ResultVDB.DataEntity.CPM004A_SELECT.STATUSColumn.DefaultValue = "301";`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:161`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:180`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:182`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:185`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:139`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:139`)

- 實際 UPDATE:`dbTA.AddInParameter(cmd, "STATUS", OracleDbType.Varchar2, "301");`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:284`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:292`)

`'301'` 這個值在 `architecture.md §3.10` 反推出來的 12 個 `EVAStatusCode` 值域裡找不到對應(那邊掃到的字面量是 `'0'`~`'6'`、`'8'`、`'9'` 單字元)。**標假設**:`'301'` 是本模組自訂的「已覆核 / 正式生效」佔位值,依據是六支畫面一致使用同一個值、且沒有任何程式讀它。要確定得查 DB。

**真正的流程狀態是 `COMPLAIN_STATUS` / `CLAIM_STATUS`,不是四眼 `STATUS`。** 這是本模組跟其他模組最大的差別:四眼欄位存在、四眼引擎被呼叫,但流程控制完全走自己的狀態欄。

## 3. 畫面清冊

13 支畫面,型別分布 `B` 6 / `M` 4 / `R` 3 / **`I` 0**。畫面中文名 ATLAS 沒放進版控(13 支 Form 沒有任何一支設 `this.Text`),下表的「用途」欄一律是**推測**,依據寫在各節。

### 3.1 維護 M(4 支)

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | SP / Fn | rpt |
|---|---|---|---|---|---|---|
| `CPMM001` | 各功能的備援通知名單維護 | 齊 | `CPM001A` | 無(多筆主檔) | 無 | 無 |
| `CPMM003` | 關卡權限與管轄部門維護 | 齊 | `CPM003A` | `CPM0031A` | 無 | 無 |
| `CPMM004` | 處理件建檔、修改、作廢申請 | 齊 | `CPM004A` | `CPM005A` `CPM006A` `CPM0061A` | 無 | `CPMM004RPS` |
| `CPMM005` | 客訴件建檔 | 齊 | `CPM007A` | 無 | 無 | `CPMM005RPS` |

### 3.2 查詢 I

**本模組無 I 畫面。** 原因見 §5。

### 3.3 批次 B(6 支)

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | 寫入方式 | 權限旗標 |
|---|---|---|---|---|---|---|
| `CPMB001` | 處理件第一關:受理部門確認 + 指定處理部門 | 齊 | `CPM004A` | `CPM005A` `CPM006A` `CPM0061A` | EVA `Update` | `MGM_CD_CPMB001` |
| `CPMB002` | 處理件第二關:指定處理部門簽核 | 齊 | 同上 | 同上 | EVA `Update` | `MGM_CD_CPMB002` + `MANGR_CODE` |
| `CPMB003` | 處理件第三關:處理部門簽核 | 齊 | 同上 | 同上 | EVA `Update` | `MGM_CD_CPMB003` + `MANGR_CODE` |
| `CPMB004` | 處理件第四關:結案或退回重辦 | 齊 | 同上 | 同上 | EVA `Update` | `MGM_CD_CPMB004` |
| `CPMB005` | 客訴件第二關:主管確認 | 齊 | **未宣告** | 無 | 手寫 `UPDATE CPM007A` | **無** |
| `CPMB006` | 客訴件第三關:收件窗口結案 | 齊 | **未宣告** | 無 | 手寫 `UPDATE CPM007A` | `MGM_CD_CPMB006` |

### 3.4 報表 R(3 支,住在 `ATLAS.CPM.Report`,七層)

| 代號 | 用途(推測) | 七層 | 取數來源 | rpt |
|---|---|---|---|---|
| `CPMR004` | 處理件明細清單(Grid,可雙擊看單筆) | 齊 | `CPM004A` 直接組 SQL | **無 `.rpt`**,只有 Grid |
| `CPMR005` | 處理件種類統計(依部門 × 處理件分類) | 齊 | `CPM004A` + `CPM005A` `GROUP BY` | `CPMR005RPS` |
| `CPMR006` | 處理件件數與天數統計 | 齊 | `CPM004A` 直接組 SQL | `CPMR006RPS` |

四支 `.rpt` 的完整清單:

| rpt | 屬於 | 路徑 |
|---|---|---|
| `CPMM004RPS` | `CPMM004` 的「印表」鈕(`DoExp1`) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004RPS.rpt` |
| `CPMM005RPS` | `CPMM005` 的「印表」鈕 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005RPS.rpt` |
| `CPMR005RPS` | `CPMR005` | `Dev/ATLAS.CPM.Report/Source/CrystalReports/Report.CPM/CPMR005RPS.rpt` |
| `CPMR006RPS` | `CPMR006` | `Dev/ATLAS.CPM.Report/Source/CrystalReports/Report.CPM/CPMR006RPS.rpt` |

**兩支 `.rpt` 住在 `UI.CPM`,不住在 `Report.CPM`。** 這違反 `architecture.md §6.5` 的「`.rpt` 在第七層」慣例 —— 但不是例外,而是因為 `CPMM004` / `CPMM005` 是 M 畫面,M 畫面沒有第七層,只能把 `.rpt` 直接放在 `UI.CPM` 資料夾。這也代表**本模組有兩張報表不受 `.Report` 專案的重編流程管**。

### 3.5 命名與層級的四個例外

| # | 例外 | 具體 | 影響 |
|---|---|---|---|
| 1 | **專案資料夾是大寫 `SOURCE`** | `Dev/ATLAS.CPM/SOURCE/…`,但 `Dev/ATLAS.CPM.Report/Source/…` 是小寫 | 同一個模組的兩個專案大小寫不一致;大小寫敏感的工具(Linux CI、Python glob)會漏掉主專案。`architecture.md §2.6` 已記錄 CPM 與 CLS 是全庫僅有的兩個 |
| 2 | **`CPMM001` 的 PO 類別不叫 `CPMM001_PO`** | `public class CPMM001OracleDao : BaseMultiRowEVADaoPO, ICPMM001_PO`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:24`) | 檔名對、類別名不對;以類別名做 grep 的工具會漏。介面 `ICPMM001_PO` 又是舊命名,三套混用 |
| 3 | **`CPMM003` 的 Designer 檔是小寫 `d`** | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.designer.cs`,其餘 12 支都是 `.Designer.cs` | 同 #1,大小寫敏感工具會判定「缺 Designer」 |
| 4 | **`CPMR004` 沒有 `.rpt`** | 它是 Grid-only 的清單畫面,`CPMR004p0` / `p1` / `p2` 三個彈出視窗只看單筆 | 看到 `R` 就以為有 Crystal 報表會找錯 |

### 3.6 一眼看出差別的五件事

| 觀察 | 說明 |
|---|---|
| 六支 B 沒有一支覆寫 `InitializeVDBTypes()` | 只有 `CPMM004_Ctl:43-48` 與 `CPMM005_Ctl:43-48` 有。符合 `architecture.md §6.1` 的「B 常常沒有」 |
| 四支 B 關卡的 Pxy 都覆寫 `Modify()` 指向 `ctl.UpdateData` → `m_PO.Update` | 例 `Dev/ATLAS.CPM/SOURCE/FormProxy/FormProxy.CPM/CPMB001_Pxy.cs:131-146` + `Dev/ATLAS.CPM/SOURCE/Control/Control.CPM/CPMB001_Ctl.cs:59-65`。`Update` 是框架 DLL 的方法(無原始碼,從呼叫端反推) |
| 每支 PO 的介面註解都寫「覆核層級管理 PO 共用介面」 | 12 支 PO 一字不差(例 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:20-22`),是樣板複製沒改的殘留,**不要拿它推測用途** |
| 四支 B 關卡的 `SelectGrid` 結構逐行對應 | 同樣的 `try` / 13 行 `DefaultValue` / `LoadDataSet` / `intCount == 0 → "查無資料"` / `catch → "執行失敗，請檢查"`。差別只有 SQL 的 WHERE。是複製貼上出來的四份 |
| `CPMB005` 與 `CPMB006` 的 `Select` SQL **只差一個字元** | `AND CPM007A.CLAIM_STATUS = '01'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:119`)對 `= '02'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:119`),其餘 43 行完全相同 |

## 4. 維護畫面(M)— 一支一節

```text
[圖] M 畫面從按鈕到四眼引擎的卡控順序,以及 After* 掛點實際做了什麼
圖中文字:① 用戶端:卡控全在 UI 層,伺服器不重驗 / Before*ButtonClicked / Add Modify Delete Search / validatorManager1 / 框架必填 無原始碼 / DoValidate() / 本畫面自訂檢核 / Pxy 直呼 DB 檢核 / GetEmpNo GetCPM007A / ② SetMasterToDetail:把主檔 PK 回填明細 / CPMM004 / 三張明細各回填一次 / CPMM001 CPMM003 / Grid 每列回填 / CPMM005 / 無明細 不需回填 / ③ 伺服端 PO 掛點 / BeforeAdd / 取號 撞號重取 / BeforeSelect / 換掉整條 SQL / BeforeGetToDoData / 待辦清單語法 / EVA 引擎 / 無原始碼 DLL 內 / ④ After* 八個掛點:只寫跳號一覽表,零業務 SQL / CPMM004 CPMM005 / 各掛 8 個 After / AddCommentHistory / SrNo.AllotNoForNfd / CPMM001 CPMM003 / 完全沒有 After / 覆核通過資料不變 / 狀態靠 COMPLAIN_STATUS / ⑤ 卡控結果類型分布(本模組實測) / 阻擋 / 必填 狀態 起迄 已確認 / 詢問 / B002 結案 B001 刪除 / 過濾無提示 / 部門 ROWNUM 權限 / 記錄不擋 / 回填 預設值 寄信
```

*圖:圖 3 卡控與四眼順序。橘框=本模組程式碼;黑框=框架 DLL(無原始碼,從呼叫端反推);橘虛框=要留意的行為。八個 After* 只寫跳號一覽表,所以「覆核完資料才生效」在本模組不成立。*

四支 M 的共同結構(`architecture.md §6.2` 的滿血版):`xMaintainForm` + `TabPages = 2`(查詢頁 + 維護頁)、`FormInitial` 綁 `ProcessVDB` 與 `FormProxy`、`Before*ButtonClicked` 做卡控、`SetMasterToDetail()` 回填主鍵。

四眼的實際效果請先記住一件事:**`CPMM004` 與 `CPMM005` 的八個 `After*` handler 只做跳號一覽表,零業務 SQL** —— 也就是 `architecture.md §3.8.1` 講的「四眼只留軌跡、不把關資料」那一型。八個 handler 的本體都是同一行:

```
if (!SrNoCommentProcessor.AddCommentHistory(EVAType.Verify, SrNo.AllotNoForNfd, …)) throw new ApplicationException("");
```

(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1093-1097`,另七支在 `:1081-1123`;`CPMM005_PO` 同構)

`SrNo.AllotNoForNfd` 的值是 `"OFD220A"`(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103`)—— CPM 的跳號紀錄被記在 **NFD/OFD 的跳號類別底下**,不是 CPM 自己的。見附錄 E.7。

### 4.1 `CPMM001` — 功能通知名單維護

**用途(推測)**:維護「某支功能程式找不到收件者時,信要寄給誰」。`CPM001A` 的 PK 是 `FUNCTIONID` + `USERID`,畫面上方選一個功能代碼、下方 Grid 掛多個使用者。`FORMNAME` 由 `TA_SWPRODUCTSDETAIL` join 出中文名(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:93-94`)。

依據:`MailUtility.GetNotifyMail(productID, getCPM001A: true)` 的註解「應協理需求,更改為取自 CPMM001 的設定值」出現在本模組七支畫面的 EMAIL 失敗分支(例 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:386-388`)。

**PO 是多筆主檔型**:`CPMM001OracleDao : BaseMultiRowEVADaoPO`,`MasterPKey` 宣告 `FUNCTIONID` + `USERID`,`MasterTable` 用 `.Add()`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:33-35`)。這代表整個 Grid 的每一列都是主檔 row,不是明細 —— `architecture.md §3.9` 的多筆版。

**查詢頁的取數很特別**:`BuildMasterSQLString` 用 `ROW_NUMBER() OVER (PARTITION BY FUNCTIONID ORDER BY CreateDate, UpdateDate, EntryDate) NUM` 再 `WHERE NUM = 1`,只回每個 `FUNCTIONID` 的第一筆,並把 `USERID` / `USERCNAME` / `EMAIL` 三欄硬填空白(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:76-101`)。維護頁才用 `BuildDetailSQLString` 撈完整名單(`:107-126`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | `validatorManager1.DataValidate()`(框架必填檢查,清單在 Designer) | 有缺 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM001.cs:135` |
| 新增 / 修改前 | Grid 一列都沒有 | 「明細資料 必須輸入」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM001.cs:152-155` |
| 新增 / 修改前 | 把畫面上的 `FUNCTIONID` 回填到 Grid 每一列 | 一律執行 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM001.cs:162-168` |
| 修改頁載入 | `ucFUNCTIONID.Enabled = false`(PK 不可改) | 一律 | 阻擋(UI 層) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM001.cs:86` |

**沒有任何 `After*` 事件**,PO 只掛三個 `Before*`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM001_PO.cs:30-32`)。也就是四眼覆核通過後除了狀態欄以外什麼都不會發生。

### 4.2 `CPMM003` — 關卡權限與管轄部門維護

**用途(推測)**:一列 = 一個使用者,勾六個關卡權限 + 主管辨識碼 + 兩個寄信旗標;明細 Grid 掛該使用者管轄的部門。依據是六個 `MGM_CD_*` 欄位的 `msdata:Caption`(`Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMM003Model.xsd:21-25`、`:46`)。

**這是整個 CPM 的權限總開關。** 四支 B 關卡畫面的 Grid SQL 全都要 join `CPM003A` + `CPM0031A`(見 §6),沒有這張表的資料,誰都看不到任何案件。

**主檔 SQL 的 `COD009` 去重很值得看**:一個 `UID_CODE` 在 `COD009` 可能有多筆(離職再任職),所以先用 `ROW_NUMBER() OVER (PARTITION BY UID_CODE ORDER BY NVL(TRIM(LEAVE_DATE),'99991231') DESC)` 取離職日最晚的那筆,再 `AND 1 = COD009.RNO(+)`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM003_PO.cs:136-143`)。**同模組其他畫面都沒做這道去重**,直接 join `COD009` —— 同一個 `UID_CODE` 有兩筆時會出現重複列。見附錄 E.5。

**勾選框 → `Y`/`N` 的轉換寫死在 UI**(六組 if/else,`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:49-77`),Grid 欄位的顯示下拉則查 `CTL014` 的 `492`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:121-126`)。程式端寫死 `"Y"`/`"N"`,顯示端查表 —— 表裡若不是 `Y`/`N` 就對不起來。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | `ucUSERID.Value == ""` | 「使用者ID為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:270-273` |
| 新增 / 修改前 | `AutoCheckPKeyRequireByEssDataReturnMsg` 檢查 Grid PK 欄位 | 有缺 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:275-277` |
| 新增 / 修改前 | Grid 一列都沒有 | 「明細資料 必須輸入!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:280-283` |
| 新增前 | `ugrdCPMM003.ActiveRow.Update()`(快速鍵時強制把編輯中的格子寫回 DataSet) | 一律 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:303-304` |

**注意 `this.validatorManager1.DataValidate()` 在這支被註解掉了**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:269`)—— 框架的必填檢查整組不跑,只剩上表那三條手寫檢查。其他三支 M 都有跑。見附錄 E.4。

**沒有 `After*` 事件**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM003_PO.cs:37-39` 只掛三個 `Before*`)。

### 4.3 `CPMM004` — 處理件建檔(本模組的入口)

**用途(推測)**:受理人員把客戶或業務員提出的需求 / 抱怨建檔,選處理件分類(可複選,存 `CPM005A`)、處理時效、指定處理部門、是否副知五個相關部門。存檔後狀態 `01`,案件進入 `CPMB001` 的佇列。

#### 4.3.1 取號與明細回填(`BeforeAdd`)

```
SerialNo genSrNo = new SerialNo(args.DbTranPTPF, dbPTPF);
do { row.COMPLAIN_NO = genSrNo.GetCOMPLAIN_NO(); }
while (IsExistByData(args.DbTran, row, args.TableName));
```

(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:96-101`)

取到號之後把 `COMPLAIN_NO` 回填到三張明細的每一列(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:106-119`)。**這段跟 UI 的 `SetMasterToDetail()`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:185-208`)做同一件事,做了兩次** —— UI 那次在新增時 `COMPLAIN_NO` 還是空的(取號在伺服器端),所以真正有效的是 PO 這次;修改時則反過來,PO 的 `BeforeAdd` 不會觸發,靠 UI 那次。兩邊都不能拿掉。

#### 4.3.2 查詢頁的四眼與卡控

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 六個條件全空 → 「請至少輸入任一筆 查詢條件」 | **永遠不成立**(見附錄 E.2) | 過濾(無提示) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:538-546` |
| 查詢前 | 處理件日期起迄只填一邊(`^` XOR) | 「處理件日期(起)(迄) 必須皆(不)填寫」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:548-549` |
| 查詢前 | 起 > 迄 | 「處理件日期(起)必須小於等於處理件日期(迄)」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:551-552` |
| 查詢前 | 戶號起迄只填一邊 / 起 > 迄 | 對應訊息 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:559-563` |
| 查詢 SQL | `COMPLAIN_DEPT IN (該使用者 `MGM_CD_CPMM004='Y'` 的管轄部門)` | 一律 | **過濾(無提示)** | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:268-275` |

最後一條是本畫面最重要的隱形過濾:**沒有 `CPM003A` 資料、或 `MGM_CD_CPMM004` 不是 `'Y'`、或 `CPM0031A` 沒掛部門的人,查詢永遠零筆,而且畫面只說「查無資料」。**

#### 4.3.3 新增 / 修改 / 刪除前卡控

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | `pxy.GetEmpNo(user) == ""` | 「使用者帳號尚未設定連接員工代碼，請通知資訊組!!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:707-712` |
| 新增 / 修改前 | 受理內容說明空白 | 「處理件內容不得為空白!!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:713-714` |
| 新增 / 修改前 | `DATA_TYPE = '1'`(需求處理件)且指定處理部門空白 | 「指定處理部門內容不得為空白!!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:716-718` |
| 新增 / 修改前 | `CC_EMAIL_YN = 'Y'` 但五個副知勾選框全沒勾 | 「請勾選EMAIL通知單位!!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:721-729` |
| 新增前 | `CPM005A`(處理件分類)零列 | 「處理件分類，必須選取至少一項!!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:603-604` |
| 修改前 | 狀態選 `06` → 改寫成 `D1`(作廢申請) | 一律 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:626-627` |
| 修改前 | `COMPLAIN_CFM_UID` 非空 且 狀態 ≠ `05` | 「此需求處理/抱怨記錄件序號已申請確認,不能修改!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:630-637` |
| 修改前 | `SOLVE_CFM_UID1` 非空 且 狀態 = `05` | 「此需求處理/抱怨記錄件序號已重新處理申請確認,不能修改!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:638-645` |
| 刪除前 | `COMPLAIN_CFM_UID` 非空 | 「此需求處理/抱怨記錄件序號已申請確認,不能修改!」(訊息寫「修改」但這是刪除) | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:903-912` |
| 分類值變更 | 依 `COMPLAIN_KIND` 算 `COMPLAIN_PRV_DATE` | 一律 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:868-886` |

**「已申請確認就不能改」這條的實作是看 `COMPLAIN_CFM_UID` 而不是看 `COMPLAIN_STATUS`。** 兩者理論上同步(都由 `CPMB001` 寫),但 `CPMB004` 退回重辦時**沒有清掉 `COMPLAIN_CFM_UID`**(它只清 `SOLVE_CFM_*1` / `SOLVE_*1` / `COMPLAIN_CFM_*1` 六欄,`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:262-272`)。所以退回成 `05` 之後,`CPMM004` 是靠第二條規則(`SOLVE_CFM_UID1` 非空 + 狀態 `05`)放行的 —— 這是刻意設計,但兩條規則耦合得很緊,改任何一邊都會壞。

#### 4.3.4 存檔後動作

| 事件 | 做什麼 | 錨點 |
|---|---|---|
| `AfterAddButtonClicked` | `Email("新增")` | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:657-660` |
| `AfterModifyButtonClicked` | 狀態 `D1` → `Email("作廢")`,否則 `Email("修改")` | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:667-674` |
| 刪除 | **不寄信** | — |
| PO `After*` ×8 | 只寫跳號一覽表 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1076-1123` |

`Email()` 的收件者來自 `pxy.GetEmail(COMPLAIN_DEPT, ccEMAIL)`,而 `ccEMAIL` 被寫死成 `"NNNNN"`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:924`,原本的計算整段註解在 `:927-947`,註記「20200612 改由 CPMB001 覆核完才通知相關部門」)。後果見附錄 E.1 —— `GetEmail` 的第三段 UNION 因此永久失效。

#### 4.3.5 列印(`DoExp1` → `CPMM004p2`)

`CPMM004p2` 走的是 `architecture.md §6.5` 那套「資料一條、`.rpt` 檔一條」的雙往返:`pxy.GetReport_Data(ProcessVDB)` 取資料(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004p2.cs:104`),`pxy.GetReportObject(m_ResultVDB)` 取 `.rpt` 位元組(`:112`、`:149-154`),再 `CreateCRReportDocument` 落地成暫存檔(`:114`)。報表標題硬寫「處理件處理單」(`:126`)。

`GetReport_Data` 有兩處值得記住(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:663-814`):

1. **`ID_NO` 被遮罩**:`SUBSTR(ID_NO,1,1) || '**** ' || SUBSTR(ID_NO,6,5)`(`:674`)。這是模組內唯一一處個資遮罩,`CPMR004` 的 Grid 沒有做。

2. **兩張明細用 `SYS_CONNECT_BY_PATH` 逐筆再查一次**:`CPM005privot` / `CPM006privot` 對報表每一列各下一次 SQL(`:786-794`、`:821-917`)。100 列就是 200 次來回。而且 SQL 用字串串接 `COMPLAIN_NO`(`:847`、`:893`)。

### 4.4 `CPMM005` — 客訴件建檔

**用途(推測)**:業務員或收件窗口把客訴案件建檔,填申請人、組主管、部門主管、案件說明、文件存檔路徑;存檔後 `CLAIM_STATUS = '01'`,進 `CPMB005` 佇列。

**取號**:`genSrNo.GetCLAIM_NO()`,同樣是 do-while 撞號重取(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:91-97`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增頁載入 | `CLAIM_STATUS` 固定 `"01"`,狀態 / 主管確認日 / 結案日 / 五個建議欄唯讀 | 一律 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:107-119` |
| 戶號選取後 | `GetCPM007A(BF_NO)` 有 `CLAIM_STATUS` 在 `01`/`02` 的案件 → 「此客戶已有進行中的客訴件，是否確定新增？」 | **訊息是問句,行為是阻擋**(見附錄 E.8) | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:440-444`、`:453-457` |
| 戶號選取後 | `GetBMS001(BF_NO)` 帶出 `ID_NO` / `BF_NAME` | 有資料時 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:446-451` |
| `ID_NO` 離開欄位 | `GetCPM007B(ID_NO)` 同上檢查 | 同上 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:488-504` |
| 新增 / 修改前 | `validatorManager1.DataValidate()` | 有缺 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:383-390` |
| 查詢前 | 戶號起迄 / 申請日期起迄 只填一邊或起 > 迄 | 對應訊息 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:221-232` |
| 查詢前 | 受益人姓名少於 2 碼 | 「此欄位需輸入2碼以上才可以查詢」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:235-238` |
| 查詢 SQL | 有填 `BF_NAME` 時自動加 `AND ROWNUM <= 100` | 一律 | **過濾(無提示)** | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:317-318` |

**這支沒有任何權限過濾。** `BuildMasterSQLString` 完全不 join `CPM003A`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:162-322`),誰能開這支畫面就能查到全部客訴件。跟處理件線(`CPMM004` 有部門過濾)不一致。

**存檔後不寄信。** 整支 `CPMM005.cs` 沒有 `Email()`,也沒有 `After*ButtonClicked`。所以客訴件建檔完成後**沒有任何人會被通知** —— 主管要自己去開 `CPMB005` 看。這是兩條業務線最明顯的成熟度落差。

**顯示欄位的 join 全部錯**:`BuildMasterSQLString` 的四個 `COD009` 別名 `A`(取 `LEADER_EMP_NO_NAME`)、`B`(`BOSS_EMP_NO_NAME`)、`D`(`CLAIM_EMP_NO_NAME`)**都 join 在 `CPM007A.EMP_NO` 上**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:198-206`),所以組主管、部門主管、申請人三個姓名欄顯示的都是「業務員」那個人的名字。同一支 PO 的報表查詢 `GetReport_Data` 卻 join 對了(`:451-453`),證明這是 bug 不是設計。見附錄 E.5。

**文件存檔路徑用 `FolderBrowserDialog` 選本機資料夾**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:421-433`)—— 存進 DB 的是操作者那台機器看到的路徑,換一台機器不一定打得開。〔客戶特定〕

## 5. 查詢畫面(I)

**本模組無 I 畫面。**

原因不是漏做,而是**查詢功能被 B 與 R 吸收了**:

| 需求 | 誰在做 |
|---|---|
| 「我的待辦案件有哪些」 | 四支 B 關卡畫面本身就是查詢頁 + Grid,而且只撈「輪到我」的案件(§6) |
| 「某個案件現在到哪一關」 | `CPMR004`,它是 Grid-only 沒有 `.rpt`,實質就是一支 I 畫面(§7.1) |
| 「歷史案件明細」 | `CPMM004` / `CPMM005` 的查詢頁 |
| 「某個客戶有沒有客訴」 | 不在本模組,在 OFD 的 `OFDI011` → `frmCLAIM`(§8.1) |

`CPMR004` 掛在 `R` 底下而不是 `I`,結果是它跑到 `ATLAS.CPM.Report` 專案、多背了一整套 `Report*` 七層,卻沒有 `.rpt` 可用。**如果要找「處理件查詢」畫面,不要在 `ATLAS.CPM` 找,它在 `.Report` 專案裡。**

## 6. 批次(B)與 WindowsService

```text
[圖] 四支關卡在同一組主明細上的處理順序、各自的撈取條件與寫入欄位群,以及兩條跳關路徑
圖中文字:① 五支畫面掛同一組表:主 CPM004A + 明細 CPM005A CPM006A CPM0061A / CPMM004 / 建檔 EVA Add / CPMB001 / Modify / CPMB002 / Modify / CPMB003 / Modify / CPMB004 / Modify / CPMR004 / 唯讀 少 CPM0061A / ② 每一關撈什麼:狀態 + 權限旗標 + 管轄部門三者同時成立才看得到 / 01 05 D1 / MGM_CD_CPMB001 受理部門 / 02 03H 03O / MGM_CD_CPMB002 指定部門 / 03 04H 04O / MGM_CD_CPMB003 處理部門 / 04 04S 03無部門 / MGM_CD_CPMB004 受理部門 / ③ 每一關寫什麼:同一張 CPM004A,不同欄位群,互不重疊 / B001 寫 / COMPLAIN_CFM_ ASN_SOLVE_DEPT_NO / B002 寫 / SOLVE_ SOLVE_DEPT_NO ASN_EMP_NO / B003 寫 / SOLVE_CFM_ DEPT_SOLVE_EMP_NO / B004 寫 / CLOSE_DATE 或清空六欄 / ④ 兩條會咬人的跳關路徑 / 抱怨記錄件 DATA_TYPE=2 / B001 直接推 04S 進 B004 / B002 未填處理部門 / 狀態 03 但 B003 撈不到 / 落到 B004 特例 / 03 AND SOLVE_DEPT_NO NULL / B004 退回 05 / 回到 B001 重走 / ⑤ 客訴件線:不走 EVA,手寫 UPDATE,沒有樂觀鎖 / CPMB005 / CLAIM_STATUS 01 到 02 / CPMB006 / 02 到 06 無權限不推 / CPM007A / 手寫 UPDATE 無樂觀鎖 / 一律回報成功 / 回傳值全部丟掉
```

*圖:圖 4 四支關卡的資料流(本篇最重要的一張)。橘框=本模組入口;橘虛框=要留意的行為;灰虛框=唯讀。四支不能亂跑,但擋住亂跑的是第②列的撈取條件,不是任何一道檢核 ——同一筆案件被兩人同時雙擊時,後按確定的人會整張蓋掉前一個人寫的欄位,而且畫面不會提示。*

**本模組沒有 WindowsService。** repo 內無 `WindowsService.CPM*` 專案,`architecture.md §6.4` 列的四支服務也沒有一支對到 CPM。六支 B 畫面全部是人工操作的畫面。

### 6.1 六支的共同外殼

| 層 | 六支共同 | 例外 |
|---|---|---|
| UI | `xOneStepProcessForm`,`TabPages = 1`,一個唯讀 Grid(`GridLayoutReadOnly`),`DoubleClickRow` 開彈出視窗 | — |
| UI | `BeforeSearchButtonClicked` → `ProcessQueryCondition`,只塞一個參數 `USERID` | `CPMB005` / `CPMB006` 也塞 `USERID`,但 PO 根本不讀 |
| Pxy | 覆寫 `Query` / `Execute` / `Modify`;`Modify` → `ctl.UpdateData` | `CPMB001_Pxy` 多覆寫 `Delete` 與 `GetMaintainData` |
| Ctl | 只覆寫 `InitializeDataAccessPool()`,**沒有 `InitializeVDBTypes()`** | — |
| PO | `SelectGrid`(或 `Select`)撈佇列;`ExecuteNonQuery` | 四支關卡的 `ExecuteNonQuery` 是空的,`CPMB005`/`CPMB006` 的是真的 |
| 寫入 | 彈出視窗 `ubtnOK_Click` → `pxy.Modify(ProcessVDB)` | — |

**流程長這樣**(以 `CPMB001` 為例,四支結構相同):

1. 進畫面 → 按查詢 → `QueryVDB` 只帶 `USERID`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:90-91`)

2. `Pxy.Query` → `Ctl.GetData` → `PO.SelectGrid`,SQL 裡把 `USERID` **字串串接**進去(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:138-139`),回傳結果集 `CPM004A_SELECT`

3. Grid 綁 `CPM004A_SELECT`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:96-100`)

4. 雙擊一列 → 用 `COMPLAIN_NO` 呼叫 `Pxy.GetMaintainData` 撈完整主明細 → 開 `CPMB001p0`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:139-154`)

5. 彈出視窗按「確定」→ 改 `COMPLAIN_STATUS` 與該關的欄位 → `pxy.Modify(ProcessVDB)` → 寄信 → `DialogResult.OK`

6. 回到 Grid,該列 `row.Delete()` 從畫面上消失、底色變紅(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:155-166`)

### 6.2 「執行」按鈕是空操作 —— 這是本節最需要先講清楚的事

四支關卡畫面的畫面上都有「執行」鈕(`xOneStepProcessForm` 的標準鈕),也都掛了 `BeforeExecuteButtonClicked` / `AfterExecuteButtonClicked`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:122-131`、`:189-192`),但兩個 handler 一個只有 `ValidateErrList.Show()`、一個整個空的。往下走:

```
按「執行」→ Pxy.Execute → Ctl.DoExecute → PO.ExecuteNonQuery → 「//UpdateDataList(model); return mModel;」
```

錨點:`Dev/ATLAS.CPM/SOURCE/FormProxy/FormProxy.CPM/CPMB001_Pxy.cs:86-101` → `Dev/ATLAS.CPM/SOURCE/Control/Control.CPM/CPMB001_Ctl.cs:76-82` → `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:210-215`。

**四支都一樣**(`CPMB002_PO.cs:229-234`、`CPMB003_PO.cs:231-236`、`CPMB004_PO.cs:234-239`),被註解掉的 `UpdateDataList` 也都還躺在檔案裡(`CPMB001_PO.cs:221-310`、`CPMB002_PO.cs:240-331`、`CPMB003_PO.cs:242-333`、`CPMB004_PO.cs:245-337`)。

含意:

- **「執行」鈕按下去不會有任何錯誤訊息,也不會有任何效果。** 使用者以為送出了,其實沒有。

- 那段註解掉的 SQL 是舊實作(`UPDATE CPM004A SET COMPLAIN_COMM, ASN_SOLVE_DEPT_NO, STATUS='301' …`),它只更新**兩個業務欄位加四眼欄位**,現行 `Modify` 路線更新的是整張主檔 + 三張明細。兩者行為差很多,**不要照著註解的內容去理解現況**。

- 如果有人要把「批次處理多筆」做回來,不能只解除註解 —— 註解版沒有 `COMPLAIN_STATUS`、沒有各關的 `*_UID` / `*_DATE`,補回去等於重寫。

嚴重度:高。詳見附錄 E.3。

### 6.3 `CPMB001` — 第一關:受理部門確認 + 指定處理部門

**佇列 SQL**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:114-142`)

| 條件 | 值 |
|---|---|
| 狀態 | `COMPLAIN_STATUS IN ('01','05','D1')` —— 新案、退回重辦、作廢申請三種一起撈(`:135`) |
| 權限 | `COMPLAIN_DEPT IN (該 USERID 在 CPM003A 有 MGM_CD_CPMB001='Y' 的 CPM0031A 管轄部門)`(`:136-141`) |
| 型態 | **不限**(`DATA_TYPE` 沒有條件) |
| 排序 | `COMPLAIN_KIND, COMPLAIN_NO`(`:142`) |
| 員工姓名來源 | `COD009` **UNION ALL** `TA_AA_USER WHERE USERID LIKE 'op%'`(`:122-125`)—— 股代人員沒有 `COD009` 資料,靠這個 UNION 補〔客戶特定〕 |

**彈出視窗寫什麼**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:224-280`)

| `DATA_TYPE` | 原狀態 | 新狀態 | 另外寫的欄位 |
|---|---|---|---|
| `1` 需求處理件 | `D1` | `D2`(作廢確認) | `COMPLAIN_COMM`、`ASN_SOLVE_DEPT_NO` |
| `1` | `01` | `02` | 同上 + `COMPLAIN_CFM_UID` / `_DATE` / `_TIME`(`:236-241`) |
| `1` | `05` | `02` | 同上 + `SOLVE_CFM_UID1` / `_DATE1` / `_TIME1`(`:242-247`) |
| `2` 抱怨記錄件 | `D1` | `D2` | `COMPLAIN_COMM`、`ASN_SOLVE_DEPT_NO`、`COMPLAIN_CFM_*`、`CLOSE_DATE = 今天` |
| `2` | 其他 | **`04S`** | 同上 —— **直接跳過 `CPMB002` / `CPMB003` 兩關,進 `CPMB004`**(`:254`) |

`04S` 這條分支是 2022 年的異動(`//20220607 modify by jye 9000011084 【程式調整】需求處理/抱怨記錄件之流程調整 調整至CPMB004結案填寫結案說明`,`:251`),舊版是直接寫 `06` 結案(`:253` 註解)。所以**抱怨記錄件走的是兩關流程(`CPMM004` → `CPMB001` → `CPMB004`),不是五關**。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 彈出視窗載入 | `DATA_TYPE = '2'` → 指定處理部門欄位鎖住 | 一律 | 阻擋(UI 層) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:161-165` |
| 彈出視窗載入 | `pxy.GetDeleteGrant(UserID) != 1` → 隱藏「刪除」鈕 | 一律 | 過濾(無提示) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:207-210` |
| 按確定 | **完全沒有 `DoValidate()`** | — | — | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:224-280` |
| 按刪除 | 「你確定要刪除資料嗎？」 | 按否時中止 | 詢問 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:500-501` |

**`CPMB001p0` 是四支關卡裡唯一沒有任何存檔前檢核的一支**(其他三支都有 `this.DoValidate(); if (!this.ValidateErrList.Show())` 包住)。指定處理部門可以留空就按確定。

**寄信**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:310-451`):需求處理件走 `Email()`(通知下一關 `CPMB002` 的人 + 原受理部門),抱怨記錄件走 `Email2()`(只通知 `COMPLAIN_UID` 本人)。兩者都在「查不到收件者」時 fallback 到 `mailUT.GetNotifyMail("CPMB001", getCPM001A: true)`,也就是 `CPM001A`。

`GetEmail` 的第三段 UNION 用五個 `CC_EMAIL_*` 旗標決定要不要副知法律顧問(`C5`)/ 法令遵循(`C3`)/ 風險管理(`C4`)/ 行銷(`E`,`E1`,`G2`)/ 通路(`G3`,`G12`,`G13`,`GA`,`G17`)—— 部門代碼全部寫死在 SQL(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:610-614`)〔客戶特定〕。

### 6.4 `CPMB002` — 第二關:指定處理部門簽核(一般兩關、股代三關)

**佇列 SQL**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:114-161`)

| 條件 | 值 |
|---|---|
| 型態 | `DATA_TYPE = '1'` —— **只收需求處理件**(`:141`) |
| 前置 | `RTRIM(ASN_SOLVE_DEPT_NO) IS NOT NULL`(`:140`) |
| 管轄 | `CPM0031A.DEPT_NO = CPM004A.ASN_SOLVE_DEPT_NO`(`:148`)+ `MGM_CD_CPMB002 = 'Y'`(`:160`) |
| 狀態 × 角色 | 四選一(`:149-158`),見下表 |

| 子條件 | 狀態 | 額外要求 | 錨點 |
|---|---|---|---|
| 第一關(經辦) | `02` | 無 | `:151` |
| 第二關(一般單位主管) | `03H` | `MANGR_CODE='Y'` 且 `ASN_SOLVE_DEPT_NO <> 'OP1'` | `:153` |
| 第二關(股代主管) | `03H` | `MANGR_CODE='Y'`、`ASN_SOLVE_DEPT_NO = 'OP1'`、`USERID LIKE 'op%'` | `:155` |
| 第三關(股務主管) | `03O` | `MANGR_CODE='Y'`、`ASN_SOLVE_DEPT_NO = 'OP1'`、操作者 `COD009.DEPT_NO = 'M2'` | `:157` |

**狀態推進**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:256-287`)

```
ASN_SOLVE_DEPT_NO == 'OP1'(股代):  02 → 03H → 03O → 03      (三關)
其他部門:                          02 → 03H,  03H → 03      (兩關,用三元運算子)
```

一般部門那行寫成 `row.COMPLAIN_STATUS = row.COMPLAIN_STATUS == "03H" ? "03" : "03H";`(`:286`)—— **任何不是 `03H` 的狀態都會被推成 `03H`**。佇列 SQL 已經把狀態限制在 `02`/`03H`/`03O` 三種,所以現況安全;但若日後有人繞過佇列(例如從 `CPMR004` 雙擊、或佇列 SQL 放寬),`03O` 會被誤推成 `03H` 倒退一關。股代分支則相反,寫了 `else { MessageBox "股代簽核流程有誤!"; return; }` 明確擋住(`:275-279`)。

**其他寫入**:`SOLVE_DEPT_NO`(處理部門,可留空)、`ASN_EMP_NO`、`COMPLAIN_SOLUTION_SOLVE`、`COMPLAIN_DELAY_DATE`(`:289-296`);達到 `03O` 或 `03` 時才寫 `SOLVE_UID`/`SOLVE_DATE`/`SOLVE_TIME`(首辦)或 `SOLVE_UID1`/`SOLVE_DATE1`/`SOLVE_TIME1`(重辦)(`:300-316`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按確定 | `DoValidate()` + `ValidateErrList.Show()` | 有錯 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:243-244` |
| 按確定 | 處理部門空白 → 「無指定處理部門將進行結案程序?」Yes/No | 按 No 中止 | **詢問** | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:246-252` |
| 按確定 | 股代流程狀態不在 `02`/`03H`/`03O` | 「股代簽核流程有誤!」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:277-278` |
| 寄信 | 只有推到 `03` 才寄 | 否則不寄 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:324-325` |

「無指定處理部門將進行結案程序?」這個詢問的真正效果是:`SOLVE_DEPT_NO` 留空 → 狀態仍推成 `03` → `CPMB003` 撈不到(它要求 `RTRIM(SOLVE_DEPT_NO) IS NOT NULL`,`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:139`)→ 由 `CPMB004` 的特例條件 `(COMPLAIN_STATUS = '03' AND TRIM(SOLVE_DEPT_NO) IS NULL)` 接手(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:155`)。**第三關被跳過是靠一個欄位留空,不是靠狀態值** —— 這是全流程最隱晦的一條路徑。

**展延流程是死的**:`CPMB002p0.Email()` 把 `nDelay` 硬寫 `0`,計算整段註解(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:372-377`,註解寫「無展延流程」)。所以 `GetEmail_YN` 的 `nDelay == 1` 分支永遠走不到 —— 而那個分支裡有一行 SQL 少了等號(`AND CPM0031A.DEPT_NO '…'`,`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:693`),一旦有人把展延流程打開就會 ORA 錯。見附錄 E.9。

### 6.5 `CPMB003` — 第三關:處理部門簽核

**佇列 SQL**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:112-161`)—— 結構與 `CPMB002` 逐行對應,差別只有三處:

| 面向 | `CPMB002` | `CPMB003` |
|---|---|---|
| 前置 | `RTRIM(ASN_SOLVE_DEPT_NO) IS NOT NULL` | 多一條 `RTRIM(SOLVE_DEPT_NO) IS NOT NULL`(`:138-139`) |
| 管轄部門比對 | `CPM0031A.DEPT_NO = ASN_SOLVE_DEPT_NO` | `CPM0031A.DEPT_NO = SOLVE_DEPT_NO`(`:147`) |
| 狀態組 | `02` / `03H` / `03O` | `03` / `04H` / `04O`(`:150-156`) |
| 權限旗標 | `MGM_CD_CPMB002` | `MGM_CD_CPMB003`(`:159`) |
| 排序 | `COMPLAIN_KIND, COMPLAIN_NO` | **`COMPLAIN_NO, COMPLAIN_KIND`**(`:160`,兩欄對調) |

**狀態推進**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:264-295`):與 `CPMB002` 同形,`SOLVE_DEPT_NO == 'OP1'` 走 `03 → 04H → 04O → 04`,其他走 `03 → 04H → 04`。

**其他寫入**:`DEPT_SOLVE_EMP_NO`(處理人員)、`COMPLAIN_SOLUTION`(處理說明)(`:323-325`);達到 `04O`/`04` 才寫 `SOLVE_CFM_*`(首辦)或 `COMPLAIN_CFM_*1`(重辦)(`:328-343`)。

**整段「資訊簽核 / 副主管審核」邏輯被註解掉**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:296-320`):原本會依 `UserID == "op16"` 與 `SOLVE_DEPT_NO` 推出 `07` 狀態並在條件不符時擋下(「副主管尚未審核!」「無此權限!」)。現在整段不執行,`07` 變成死值。外殼(`//20180214 modify by jye 加入資訊簽核` 註記)還在。見附錄 E.4。

### 6.6 `CPMB004` — 第四關:結案或退回重辦

**佇列 SQL**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:114-165`)—— 這支的 WHERE 是四支裡最複雜的,兩條路並聯:

```
(  DATA_TYPE = '2' AND COMPLAIN_STATUS = '04S' )            ← 抱怨記錄件,無權限檢查
OR
(  DATA_TYPE = '1'
   AND RTRIM(ASN_SOLVE_DEPT_NO) IS NOT NULL
   AND RTRIM(COMPLAIN_CFM_UID) IS NOT NULL
   AND ( COMPLAIN_STATUS = '04'
         OR (COMPLAIN_STATUS = '03' AND TRIM(SOLVE_DEPT_NO) IS NULL) )   ← 第三關被跳過的案子
   AND COMPLAIN_DEPT IN (該 USERID MGM_CD_CPMB004='Y' 的管轄部門) )
```

(`:145-163`)

**第一條路完全沒有權限過濾。** 抱怨記錄件(`DATA_TYPE='2'`、狀態 `04S`)只要有人打得開 `CPMB004` 就全部看得到,不論他的 `MGM_CD_CPMB004` 是什麼、管轄哪個部門。需求處理件那條路才有 `COMPLAIN_DEPT IN (...)`。這是四支關卡裡唯一的權限缺口。嚴重度中,見附錄 E.2。

**狀態推進**:使用者從下拉自己選(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:244`),下拉被 `Filter` 限定:

| 原狀態 | 可選 | 錨點 |
|---|---|---|
| `04S`(抱怨記錄件) | 只有 `06` 結案 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:87-91` |
| 其他 | `05` 退回重辦 / `06` 結案 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:92-95` |

下拉的資料來源另外加了一條 `Dis > '04'` 參數(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:609-612`),跟上面的 `Filter` 是兩層各自獨立的過濾 —— 兩邊都要對,少一邊就會冒出不該出現的選項。

**選 `06` 結案**:寫 `CLOSE_DATE`(取畫面上的日期,不是今天,`:250-251`)、`COMPLAIN_REMARK`。 **選 `05` 退回重辦**:寫 `VERIFY_DATE`(退件日)、`COMPLAIN_DELAY_DATE`、`COMPLAIN_PRV_DATE1`,並**清空六個重辦欄位** `SOLVE_CFM_UID1`/`_DATE1`/`_TIME1`、`SOLVE_UID1`/`SOLVE_DATE1`/`SOLVE_TIME1`、`COMPLAIN_CFM_UID1`/`_DATE1`/`_TIME1`(`:256-272`)。這一清是為了讓下一輪的 `CPMB002`/`CPMB003` 重新走「首辦」分支(判斷式是 `string.IsNullOrWhiteSpace(custSOLVE_CFM_UID1.Value)`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按確定 | 處理狀態空白 | 「處理狀態為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:634-638` |
| 按確定 | 狀態 `05` 但展延日期空白 | 「展延日期為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:639-643` |
| 按確定 | 狀態 `06` 但結案日期空白 | 「結案日期為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:644-648` |
| 按確定 | 回覆情形空白 | 「結案說明為必填」—— **退回重辦也要填** | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:649-652` |

前兩條錯誤訊息掛錯控件:`AddError(this.ucDEPT_SOLVE_EMP_NO, "展延日期為必填")` / `AddError(this.ucDEPT_SOLVE_EMP_NO, "結案日期為必填")`(`:641`、`:646`)—— 游標會跳到「處理人員」欄而不是日期欄。見附錄 E.6。

**寄信一律寄**(`:280`,沒有狀態條件),但內容依狀態分兩套:`05` 通知操作者部門 + KEY 單部門(`:342-346`),`06` 走 `GetCloseEmail(AGENT_CODE)` 通知 `CLOSE_SEND_EMAIL_YN='Y'` 的人(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:640-673`)。`GetCloseEmail` 是全模組唯一一支**全程參數化**的 EMAIL 查詢,但它 join 的是 `AA_USER` 而不是其他地方用的 `TA_AA_USER`(`:650`)。

### 6.7 四支關卡的執行順序與相依 —— 「能不能亂跑?」

**結論:四支不能亂跑,但擋住亂跑的不是程式,而是每支佇列 SQL 的狀態條件。**

沒有任何一處檢查「前一關做完了沒」。四支各自獨立地用 `COMPLAIN_STATUS`(加上部門與權限)決定 Grid 裡看得到什麼。案件只會出現在「輪到它的那一支」的清單裡,所以正常操作下順序是被資料逼出來的,不是被驗證出來的:

| 狀態 | `CPMB001` 看得到 | `CPMB002` | `CPMB003` | `CPMB004` |
|---|---|---|---|---|
| `01` 新案 | ✔ | ✘ | ✘ | ✘ |
| `02` | ✘ | ✔(第一關) | ✘ | ✘ |
| `03H` | ✘ | ✔(需 `MANGR_CODE`) | ✘ | ✘ |
| `03O` | ✘ | ✔(需 `M2` 主管) | ✘ | ✘ |
| `03` + 有處理部門 | ✘ | ✘ | ✔(第一關) | ✘ |
| `03` + **無**處理部門 | ✘ | ✘ | ✘(被 `SOLVE_DEPT_NO IS NOT NULL` 擋) | ✔(特例) |
| `04H` / `04O` | ✘ | ✘ | ✔(需 `MANGR_CODE`) | ✘ |
| `04` | ✘ | ✘ | ✘ | ✔ |
| `04S`(抱怨記錄件) | ✘ | ✘ | ✘ | ✔(**無權限檢查**) |
| `05` 退回重辦 | ✔ | ✘ | ✘ | ✘ |
| `06` 結案 | ✘ | ✘ | ✘ | ✘(終點) |
| `D1` 作廢申請 | ✔ | ✘ | ✘ | ✘ |
| `D2` 作廢確認 | ✘ | ✘ | ✘ | ✘(終點) |

**四種真的會咬人的情況:**

1. **同一筆案件被兩個人同時雙擊。** 兩人都拿到同一份 VDB,先按確定的推 `02`,後按確定的**還是從舊狀態推**,寫進去的 `COMPLAIN_STATUS` 可能倒退,而且第二次的 `Modify` 會把第一個人寫的欄位整個蓋掉。框架的樂觀鎖(`DATAFLAG`)理論上會擋,但 `architecture.md §3.6` 的實測結論是**四種 `IsDataChanged` 實作沒有一種會比到新增的業務欄位**,也就是靠不住。畫面上沒有任何提示。

2. **`CPMB002` 把 `SOLVE_DEPT_NO` 留空。** 案件從第三關消失、直接落到 `CPMB004`,而使用者只看到一句「無指定處理部門將進行結案程序?」。想補救只能改 DB,因為 `CPMM004` 這時已經因為 `COMPLAIN_CFM_UID` 非空而不准修改。

3. **`CPMB004` 退回重辦後六個欄位沒清乾淨。** 現行程式清了九個欄位(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:262-272`),但**沒有清 `SOLVE_DEPT_NO`**。下一輪 `CPMB002` 若沿用舊的處理部門,`CPMB003` 會落到原班人馬手上 —— 這可能是刻意的,但沒有註解說明,標**假設**。

4. **股代(`OP1`)路徑靠三個條件同時成立**:`ASN_SOLVE_DEPT_NO='OP1'`(或第三關的 `SOLVE_DEPT_NO='OP1'`)、`CPM003A.USERID LIKE 'op%'`、操作者 `COD009.DEPT_NO='M2'`。三者任一不符,案件就卡在 `03H`/`03O`/`04H`/`04O` 沒人看得到,而且**沒有任何畫面會列出「卡住的案件」** —— 只能靠 `CPMR004` 人工撈。

**沒有回頭路。** 除了 `CPMB004` 的 `05` 退回,任何一關做完都不能撤銷:`CPMM004` 的修改被 `COMPLAIN_CFM_UID` 非空擋住、四支關卡的佇列 SQL 也不會再撈到舊狀態。要救只能改 DB,或用 `CPMB001p0` 的隱藏「刪除」鈕(需列在 `CPMB001_MGN_V`)。

### 6.8 `CPMB005` — 客訴件第二關:主管確認

**佇列 SQL**(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:77-128`):`SELECT … FROM CPM007A LEFT JOIN … WHERE 1=1 AND CPM007A.CLAIM_STATUS = '01'`,再加上可選的 `CLAIM_NO`(`SQLHelper.AddParam`,`:127`)。

**沒有任何權限或部門過濾。** UI 明明塞了 `USERID` 參數(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005.cs:87-88`),PO 從頭到尾不讀它。任何能開這支畫面的人,都能看到並簽核**全公司所有**待確認的客訴件。嚴重度高,見附錄 E.2。

**寫什麼**(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:126-159`):`CLAIM_CONTENT`、`CONFIRM_DATE`、`CLAIM_DOC`、`CLAIM_DEMAND`、`SALES_COMM`,狀態硬推 `"02"`(`:140`)。

**怎麼寫**:不走四眼。`pxy.Modify` → `Ctl.UpdateData` → `PO.Update` → `UpdateDataList`,手寫的 `UPDATE CPM007A SET … WHERE CLAIM_NO = :CLAIM_NO`,自己 `BeginTransaction` / `Commit`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:216-329`)。

**卡控總表**

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 彈出視窗載入 | 狀態 `01` 且主管確認日空 → 預設今天(取 AP Server 系統日) | 一律 | 記錄不擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:113-118` |
| 按確定 | 主管確認日期空白 | 「主管確認日期為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:236-240` |
| 按確定 | 客戶訴求空白 | 「客戶訴求為必填」 | 阻擋 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:241-245` |

**寄信**:`pxy.GetEMAIL(user, GetUidCode(BOSS_EMP_NO), GetUidCode(LEADER_EMP_NO))`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:182`),而 PO 端的簽名是 `GetEmail(strUserID, strLEADER_EMP_NO, strBOSS_EMP_NO)`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:402`)—— **第二、三個參數對調了**。收件者實際上是 SP `GET_CPMB005` 決定的,而那支 SP 不在版控(`DB/SP/` 底下沒有),所以無法從 repo 判斷影響。見附錄 E.6。

`GET_CPMB005` 是本模組唯一一支被呼叫的 Stored Procedure,`CommandTimeout = 0`(永不逾時,`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:415`),參數 `strUSERID` / `strLEADER_EMP_NO` / `strBOSS_EMP_NO` / `strFUNCTIONID='CPMB005'`,回傳 `RefCursor`。

### 6.9 `CPMB006` — 客訴件第三關:收件窗口結案

**佇列 SQL**:與 `CPMB005` 逐字相同,只差 `CLAIM_STATUS = '02'`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:119`)。同樣沒有權限過濾。

**權限檢查在彈出視窗,而且不擋**:

```
strYN = pxy.GetPermission(UserID);            // CPMB006p0.cs:55
…
if (strYN == "Y" && DateTimeHelper.DateToString(this.udatCLOSE_DATE.Value) != "")
{
    row.CLAIM_STATUS = "06";                  // CPMB006p0.cs:158-161
}
…
BasicViewVDB view = pxy.Modify(this.ProcessVDB);   // :171 —— 不論 strYN 是什麼都會執行
Email();                                            // :174 —— 不論 strYN 是什麼都會寄
```

**沒有 `MGM_CD_CPMB006` 權限的人按下確定,九個意見欄位照樣寫進 DB、通知信照樣寄出,只是狀態沒推進,而且畫面不會有任何訊息。** 使用者會以為結案了。嚴重度高,見附錄 E.2。

`GetPermission` 本身也脆:`ds.Tables["CPM003A"].Rows[0]["MGM_CD_CPMB006"]`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:358`),使用者沒有 `CPM003A` 資料時 `Rows[0]` 丟 `IndexOutOfRangeException`,被 `catch` 吞掉回傳空字串 —— 結果等同「沒權限」,方向正確但靠例外流程達成。

**`DoValidate()` 是空殼**:整段檢查被註解(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:253-264`),方法留著、呼叫留著、永遠回傳無錯。所以結案日期可以空白就按確定 —— 空白時狀態不會推進(上面那個 `&&`),同樣沒有提示。

**寫什麼**:`CLOSE_DATE` + 八個意見欄(`CLAIM_DOC`、`CLAIM_DEMAND`、`SALES_COMM`、`OTHER_DEPT_COMM`、`COMPLIANCE_COMM`、`SER_WINDOW_COMM`、`CEO_VERIFY`、`IMPROVE_COMM`、`OTHER_REMARK`)(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:147-156`)。

### 6.10 `CPMB005` / `CPMB006` 為什麼沒宣告主明細

三個原因疊在一起:

1. **PO 不繼承任何 EVA 基底。** `public class CPMB005_PO : ICPMB005_PO`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:37`)、`public class CPMB006_PO : ICPMB006_PO`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:38`),介面也**沒有** `: IEvaDataAccess`(對照 `ICPMB001_PO : IEvaDataAccess`,`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:25`)。`MasterTable` / `DetailTable` 這兩個屬性根本不存在,寫了編不過。

2. **建構子裡的宣告是從 OFD 複製來的殘骸。** 兩支的建構子都只剩一行註解 `//this.MasterTable = new TableMapping("OFD701", "SEAL");`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:46`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:46`)。`OFD701` / `SEAL` 跟 CPM 毫無關係,是樣板來源沒刪乾淨。

3. **寫入路徑自己重做一遍。** `UpdateDataList` 用手寫的 `UPDATE CPM007A SET 六(九)個業務欄 + 13 個四眼欄 WHERE CLAIM_NO = :CLAIM_NO`,自己開 `DbTransaction`、自己 `Commit`(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:219`、`:298-304`)。因為不走 EVA,框架不需要知道主明細對應。

**所以「沒宣告主明細」不是漏掉,是這兩支根本不在四眼軌道上。** `atlas_scan` 判斷「主檔於 / 明細於」是靠 `xTableMapping` 宣告,所以母體才會把它們列成空白 —— 它們實際操作的是 `CPM007A`。

**代價**(三項都寫進附錄 E):

| 代價 | 說明 | 錨點 |
|---|---|---|
| `CREATEID` / `CREATEDATE` 每次更新都被覆蓋 | 手寫 SQL 把 13 個四眼欄全部重寫,包含「資料建立者 / 建立日期」 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:285-286`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:293-294` |
| `ExecuteNonQuery` 的回傳值丟掉 | `dbTA.ExecuteNonQuery(cmd, tran); i += 1;` —— `i` 數的是迴圈跑幾次,不是實際更新幾列。`WHERE CLAIM_NO` 沒對到任何列也會 `Commit` 並回報成功 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:298-304`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:306-312` |
| 零列時交易既不 commit 也不 rollback | `if (i > 0) { tran.Commit(); }` 沒有 else;`finally` 只 `Dispose` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:301-304`、`:323-328` |
| 樂觀鎖完全沒有 | 不經過 EVA 就沒有 `DATAFLAG` 比對,兩人同時開同一筆後改必定互蓋 | 同上 |

## 7. 報表(R)

三支 R 住在 `ATLAS.CPM.Report`,七層俱全(`architecture.md §6.5`)。第七層 `Report.CPM` 只裝兩支 `.rpt`,因為 `CPMR004` 沒有報表本體。

| rpt | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| —(Grid only) | `CPMR004` | `CPM004A` 直接組 SQL,`SelectGrid` | 處理件日期起迄、預計完成日起迄、展延日期起迄、結案日期起迄、處理狀態、處理部門、KEY 單人員、KEY 單部門、受益人戶號、作業類型 |
| `CPMR005RPS` | `CPMR005` | `CPM004A` + `CPM005A` + `COD006A` + `OFD002`,`GROUP BY` | 處理件日期起迄、展延日期起迄、受益人戶號起迄、處理件分類、作業類型 |
| `CPMR006RPS` | `CPMR006` | `CPM004A` + `BMS001A` + `TA_AA_USER` | 處理件日期起迄、處理件單號起迄、作業類型 |
| `CPMM004RPS` | `CPMM004` 的「印表」鈕 | `CPMM004_PO.GetReport_Data` + 兩支 `SYS_CONNECT_BY_PATH` 子查詢 | 目前畫面上那一筆 |
| `CPMM005RPS` | `CPMM005` 的「印表」鈕 | `CPMM005_PO.GetReport_Data` | `CLAIM_NO`(唯一一支全參數化的報表查詢,`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs` 以外) |

### 7.1 `CPMR004` — 處理件明細清單(實質是 I 畫面)

- 沒有 `.rpt`,`BeforePreviewOrPrintButtonClicked` 也沒有 `SetQueryParameters`;只有 Grid + 三個彈出視窗(`CPMR004p0` / `p1` / `p2`)。

- **權限模型跟其他所有畫面都不同**:`AND '<登入者部門>' IN ('OP1', 'M2', CPM004A.COMPLAIN_DEPT, CPM004A.SOLVE_DEPT_NO)`(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:133`)。含意是:

- 部門是 `OP1` 或 `M2` 的人 → 條件恆真 → **看得到全部案件**〔客戶特定〕

- 其他人 → 只看得到自己部門是受理部門或處理部門的案件

- **完全不看 `CPM003A` 的任何權限旗標**,也不看 `CPM0031A` 管轄部門

- 部門代碼還做了一次替換:`Row.Value.Replace("GC", "G2")`,註記「20171206 Mia GC視為G2」(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:104`)〔客戶特定〕。

- 只撈已經過第一關的案件:`RTRIM(ASN_SOLVE_DEPT_NO) IS NOT NULL AND RTRIM(COMPLAIN_CFM_UID) IS NOT NULL`(`:131-132`)。**所以狀態 `01` 的新案在這支報表上看不到**,想查「剛建檔還沒確認的案子」只能回 `CPMM004`。

- 起迄日期檢核有一個與其他畫面不同的習慣:只填「起」時**自動把「迄」補成同一天**(`Dev/ATLAS.CPM.Report/Source/UI/ReportUI.CPM/CPMR004.cs:83-84`、`:93-94`、`:103-104`、`:113-114`),四組日期都這樣。`CPMM004` 則是直接報錯要求兩邊都填。

- `DoValidate()` 是空的,而且呼叫它之後那段 `if (this.ValidateErrList.Show())` 被註解掉(`Dev/ATLAS.CPM.Report/Source/UI/ReportUI.CPM/CPMR004.cs:72-76`)—— 真正生效的檢查是後面 `:122-126` 那一段。

### 7.2 `CPMR005` — 處理件種類統計

- `GROUP BY` 部門 × 作業類型 × 處理件分類,`COUNT(*)`(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:76-96`、`:205-221`)。

- **部門歸屬取「先業務部門、後受理部門」**:`NVL(TRIM(CPM004A.AGENT_CODE), CPM004A.COMPLAIN_DEPT)`(`:83`、`:87`),註記「20200529 mofidy by jye 受理部門:先取業務部門再取受理部門」。

- 權限:`COMPLAIN_DEPT IN (SELECT CPM0031A.DEPT_NO FROM CPM003A, CPM0031A WHERE CPM003A.USERID = '<登入者>' AND CPM003A.USERID = CPM0031A.USERID)`(`:92-96`)—— **只看有沒有掛管轄部門,不看任何 `MGM_CD_*` 旗標**。

- `ORDER BY` 用 `CASE` 把七個部門代碼硬排在前面(`G`/`GB`→0、`G16`→1、`G1`→2、`G8`→3、`G7`→4、`G5`→5、`G4`→6),其餘照代碼排(`:212-221`)〔客戶特定〕。

- 報表名稱依作業類型三選一,在 UI 決定(`Dev/ATLAS.CPM.Report/Source/UI/ReportUI.CPM/CPMR005.cs:119-128`)。

- **`QUERY_DEPT_NO` 參數收了但沒用**:`dept_NO` 在 `:69` 被賦值後,整支 SQL 沒有任何一處引用它(`CPMR006_PO.cs:68` 同樣情形)。UI 每次都多做一次 `GetEMP_INFO` 遠端呼叫,結果丟掉。

### 7.3 `CPMR006` — 處理件件數與天數統計

- 每筆案件一列,`1 AS ALL_COUNT`,由 Crystal 端加總(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs:89`)。

- 三個日期用 `TO_DATE(NVL(TRIM(…),'19000101'),'YYYYMMDD')` 轉,空值變 1900/01/01(`:86-88`)。完成日取 `NVL(NVL(TRIM(SOLVE_CFM_DATE), TRIM(SOLVE_DATE)),'19000101')` —— 先取處理部門完成日,沒有才取指定處理部門完成日。

- 權限:`COMPLAIN_DEPT IN (SELECT CPM0031A.DEPT_NO FROM CPM0031A WHERE CPM0031A.USERID = '<登入者>')`(`:98-99`)—— **連 `CPM003A` 都不 join**,只看 `CPM0031A`。三支報表三種權限模型,見下表。

### 7.4 三支報表的權限模型不一致

| 畫面 | 檢查 `MGM_CD_*` | 檢查 `CPM0031A` 管轄 | 特權後門 | 錨點 |
|---|---|---|---|---|
| `CPMR004` | ✘ | ✘ | 部門 `OP1` / `M2` 看全部 | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:133` |
| `CPMR005` | ✘ | ✔(join `CPM003A` 但不看旗標) | 無 | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:92-96` |
| `CPMR006` | ✘ | ✔(**不 join `CPM003A`**) | 無 | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs:98-99` |
| (對照)`CPMM004` | ✔ `MGM_CD_CPMM004` | ✔ | 無 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:268-275` |

**同一批資料,四支畫面四套可見範圍。** 要回答「某人看得到哪些案件」必須逐畫面判斷,不能用一句話概括。

### 7.5 兩支 M 畫面的列印

`CPMM004` 的「印表」鈕(`DoExp1` → `CPMM004p2`)與 `CPMM005` 的(`DoExp1` → `CPMM005` 自己的流程)走的是 `architecture.md §6.5` 第 3 步那條路:`GetReportObject` 由**用戶端指定報表類別名**,伺服器照單全收:

```
string rpt = Convert.ToString(ClassData.Util.ReportParameters[0].ReportClass);
return CRReportTransfer.TransferFileByte(rpt);
```

(`Dev/ATLAS.CPM.Report/Source/Control/ReportControl.CPM/CPMR005_Ctl.cs:59-63`;`CPMM004p2` 走的是 `CPMM004_Pxy.GetReportObject`,同構)

`CRReportTransfer`(無原始碼,從呼叫端反推)。兩支 `.rpt` 放在 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/`,不在 `Report.CPM` 專案裡 —— 交付路徑與 `.Report` 那兩支不同,版本要分開追。

## 8. 跨模組共用

```text
[圖] 改 CPM007A 與 CPM001A 會波及哪些模組,以及 CPM 借用的外部表
圖中文字:CPM007A:CPM 寫、OFD 讀 / CPM007A / 43 欄 四眼齊 / CPMM005 建檔 / EVA 四眼 / CPMB005 CPMB006 / 手寫 UPDATE / OFDI011 frmCLAIM / 唯讀 WHERE BF_NO / CPM001A:CPM 維護、全系統讀 / CPM001A / FUNCTIONID x USERID / CPMM001 維護 / 唯一入口 / Utility_PO MailUtility / 共用層 無原始碼 / CPM 七支 + DSMR007 / fallback 收件者 / CPM 借用的外部表(全部唯讀) / COD009 / 員工 部門 離職日 EMAIL / COD006A / 四組代碼 12 13 Q2 P7 / CTL014 / 486 487 492 / OFD002 BMS001A / 部門名 受益人 / 改動影響面速查 / 改 CPM007A / 六份 xsd + OFDI011 / 改 CPM001A / 要先問 DSM / 改 COMPLAIN_STATUS / 20 處字面值 / 改 CPM0031A / 七處權限子查詢
```

*圖:圖 5 跨模組影響面。橘框=被共用的表;灰虛框=本模組以外的讀取端;黑框=外部唯讀表或無原始碼的共用層;橘虛框=改動時要一起看的範圍。CPM001A 表面上是 CPM 的小設定檔,實際上 DSM 的報表也會讀它。*

### 8.1 `CPM007A`:CPM 寫、OFD 讀

`CPM007A` 是本模組唯一被別的模組碰到的業務表。

| 誰 | 動作 | 怎麼做 | 錨點 |
|---|---|---|---|
| `CPMM005` | 新增 / 修改 / 刪除(四眼) | `BaseEVADaoPO`,`MasterTable = CPM007A` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:49` |
| `CPMB005` | `UPDATE` 六個欄位 + 狀態 `02` | 手寫 SQL | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:229-251` |
| `CPMB006` | `UPDATE` 十個欄位 + 狀態 `06` | 手寫 SQL | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:229-255` |
| **OFD 的 `OFDI011`** | **唯讀** | 客戶查詢畫面的一個 case:`SELECT 17 欄 FROM CPM007A WHERE BF_NO = :BF_NO`,參數化 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:3953-3977` |

`OFDI011` 的呼叫端是 `frmCLAIM` 彈出視窗,把結果綁到 `ugrdCLAIM`(`Dev/ATLAS.OFDI/Source/UI/UI.OFDI/frmCLAIM.cs:41-49`),查詢情境常數是 `QueryScenario.CLAIM_LOG`(`:42`)。零筆時跳「無符合查詢條件的資料!」(`:56-59`)。

**改動影響面**:

| 改動 | 要一起看 |
|---|---|
| `CPM007A` 加欄位 | `CPMB005Model.xsd` / `CPMB005View.xsd` / `CPMB006Model.xsd` / `CPMB006View.xsd` / `CPMM005Model.xsd` / `CPMM005View.xsd` 六份 xsd + 對應 Designer;`CPMB005_PO` / `CPMB006_PO` 的 `UPDATE` 欄位清單是**手寫的**,不會自動跟 |
| `CPM007A` 改欄位型別 | 再加 `OFDI011Model.xsd` / `OFDI011View.xsd`(`Dev/ATLAS.OFDI/Source/Entity/DataEntity.OFDI/OFDI011Model.xsd`) |
| `CPM007A` 刪欄位 | `OFDI011_PO.cs:3956-3972` 那 17 欄的 `SELECT` 會直接 ORA 錯,而且那支 PO 有 4000 多行、這個 case 藏在中間 |
| 改 `CLAIM_STATUS` 值域 | `CPMB005_PO.cs:119`(`'01'`)、`CPMB006_PO.cs:119`(`'02'`)、`CPMB005p0.cs:140`(推 `'02'`)、`CPMB006p0.cs:160`(推 `'06'`)、`CPMM005_PO.cs:368`、`:399`(重複件檢查認 `'01'`/`'02'`)、`CPMM005.cs:119`(新增預設 `'01'`)—— 七處字面值 |

### 8.2 `CPM001A`:CPM 維護、全系統讀

`CPM001A` 表面上是 CPM 的小設定檔,實際上是**跨模組的備援通知名單**:

```
CPMM001 維護 → CPM001A(FUNCTIONID + USERID)
                    ↑
      Utility_PO.GetSendMailToList(productID)          ← Dev/Common/Source/Utility/TA.UtilityPO/Utility_PO.cs:2745-2780
                    ↑
      MailUtility.GetNotifyMail(productID, getCPM001A: true)   ← Dev/Common/Source/Utility/TA.ClientUtility/MailUtility.cs:248-277
      MailUtility.SendMailEX(…, getCPM001A: true)              ← Dev/Common/Source/Utility/TA.ClientUtility/MailUtility.cs:137-192
                    ↑
      CPM 七支畫面 + DSM 的 DSMR007
```

呼叫端(實測 `grep -rn "getCPM001A" Dev --include=*.cs`,排除 `MailUtility.cs` 本身,共 8 個檔):

| 模組 | 檔 | 用途 |
|---|---|---|
| CPM | `CPMM004.cs:974`、`CPMB001p0.cs:388`、`:441`、`CPMB002p0.cs`、`CPMB003p0.cs`、`CPMB004p0.cs`、`CPMB005p0.cs:213`、`CPMB006p0.cs` | 「查不到收件者」的 fallback |
| **DSM** | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:898-900` | `SendMailEX(this.FunctionID, …, getCPM001A: true)` |

**含意**:`CPMM001` 裡若有人為 `FUNCTIONID = 'DSMR007'` 建了一列,DSM 的匯率通知信就會多寄給那個人 —— 而 DSM 的維護者不會知道那筆設定在 CPM 的畫面裡。改 `CPM001A` 的結構或清資料,要先問 DSM。

`GetSendMailToList` 是全參數化的(`:2763`),join `TA_AA_USER` 取 EMAIL,`NOT TRIM(EMAIL) IS NULL`。

### 8.3 CPM 借用的共用元件

| 元件 | 用途 | 錨點 |
|---|---|---|
| `SerialNo.GetCOMPLAIN_NO()` / `GetCLAIM_NO()` | 取單號,連的是 PTPF 庫 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:96-100`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:91-95` |
| `SrNoCommentProcessor` + `JumpSrNoUtility` | 跳號一覽表 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1076-1123`、`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:733-751` |
| `ClientBizUtility.GetEMP_INFO(user)` | 取登入者部門(回傳逗號分隔字串,取 `words[0]`) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:64-66`、`Dev/ATLAS.CPM.Report/Source/UI/ReportUI.CPM/CPMR004.cs:133-136` |
| `ClientBizUtility.GetBusinessDay(COMP_CALENDER_TYPE.Company, …)` | 算營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:872` |
| `SystemDateTime.GetSystemDate(APServer)` | 取伺服器日期 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:116`、`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:128` |
| `MailUtility.SendMailTo` / `SendMailEX` / `GetNotifyMail` | 寄信 | 全模組 |
| `UltraGridComboHelper` / `UltraGridInitialHelper` / `GridLayoutManager` / `UltraComboUtility` | DevExpress(Infragistics)Grid 與下拉設定 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001.cs:42-50` |
| `CommonExceptionBlocker.HandleBusinessException` / `HandleFormProxyException` | 例外政策 | 全模組 |

### 8.4 改動影響面速查

| 你要改 | 連帶要看 |
|---|---|
| `CPM004A` 任一欄位 | 5 份 Model xsd(`CPMB001`~`CPMB004`、`CPMM004`)+ 1 份 `CPMR004Model.xsd` + 6 份對應 View xsd + 全部 Designer;`CPMB001_PO.BuildMasterSQLString` 等 5 支手寫欄位清單的 `SELECT` |
| `COMPLAIN_STATUS` 值域 | §2.7.1 那張表的每一個錨點,共 **20 處字面值**,分佈在 4 支 PO + 5 支 UI |
| `CPM003A` 加一個關卡旗標 | `CPMM003Model.xsd` / `CPMM003View.xsd` / `CPMM003.cs`(勾選框轉換)/ `CPMM003.designer.cs` / `CPMM003_PO.BuildMasterSQLString` 的欄位清單 / 新關卡的佇列 SQL |
| `CPM0031A`(管轄部門) | 四支 B 關卡 + `CPMM004` + `CPMR005` + `CPMR006` 的權限子查詢,共 7 處 |
| `CPM007A` | 見 §8.1,**含 OFD** |
| `CPM001A` | 見 §8.2,**含 DSM** |
| 五個 `CC_EMAIL_*` 對應的部門代碼 | `CPMB001_PO.cs:610-614` 與 `CPMM004_PO.cs:1031-1035` **兩份一模一樣的 SQL**,改一邊會漏 |
| 新增一支 B 關卡 | `CPM003A` 加旗標欄、`CPMM003` 加勾選框、六層新檔、上一關的寄信 SQL 要加 UNION、`CPM001A` 加 `FUNCTIONID` |

## 附錄 A. 資料表總表

| 表 | 欄位 | 四眼 | 主檔於 | 明細於 | 跨模組 | 一句話 |
|---|---|---|---|---|---|---|
| `CPM001A` | 20 | 有 | `CPMM001` | — | **全系統讀**(§8.2) | 功能代碼 × 使用者 = 備援通知名單 |
| `CPM003A` | 29 | 有 | `CPMM003` | — | — | 使用者的六個關卡權限旗標 + 主管辨識碼 + 兩個寄信旗標 |
| `CPM0031A` | 18 | 有 | — | `CPMM003` | — | 使用者的管轄部門(一對多) |
| `CPM004A` | 69 | 有 | `CPMM004` `CPMB001` `CPMB002` `CPMB003` `CPMB004` `CPMR004` | — | — | 處理件主檔,33 欄是五道關卡的人 / 日 / 時 |
| `CPM005A` | 18 | 有 | — | `CPMM004` `CPMB001`~`CPMB004` `CPMR004` | — | 處理件分類(`COD006A` `CODE_SORT='12'`),可複選 |
| `CPM006A` | 18 | 有 | — | 同上 | — | 處理部門的處理方式(`CODE_SORT='13'`) |
| `CPM0061A` | 18 | 有 | — | `CPMM004` `CPMB001`~`CPMB004`(**`CPMR004` 沒有**) | — | 指定處理部門的處理方式(同一組代碼) |
| `CPM007A` | 43 | 有 | `CPMM005` | — | **OFD 讀**(§8.1) | 客訴件主檔,無明細 |

外部唯讀表見 §2.6 下半。

## 附錄 B. SP / Function / Trigger / View

| 類 | 名稱 | 在版控? | 被誰用 | 備註 |
|---|---|---|---|---|
| SP | `GET_CPMB005` | **否**(`DB/SP/` 找不到) | `CPMB005_PO.GetEmail`、`CPMB006_PO.GetEmail` | 參數 `strUSERID` / `strLEADER_EMP_NO` / `strBOSS_EMP_NO` / `strFUNCTIONID`,出參 `OutTB` RefCursor;`CommandTimeout = 0` |
| View | `CPMB001_MGN_V` | **否**(`DB/View/` 找不到) | `CPMB001_PO.GetDeleteGrant` | 欄位至少有 `EMP_NO` / `UID_CODE` / `EMP_NAME`;推測是主管白名單 |
| Function | — | — | — | 本模組不呼叫任何 Function |
| Trigger | — | — | — | 本模組不涉及 Trigger |

`DB/` 底下對 `CPM` 的搜尋零命中(`find DB -iname "*CPM*"`)—— **本模組的資料表 DDL、代碼表內容、上述兩個物件全部不在版控**。

## 附錄 C. 代碼對照

### C.1 `COMPLAIN_STATUS`(`COD006A.CODE_SORT = 'Q2'`)

值域表內容不在版控,以下是程式反推。完整的「誰寫誰讀」在 §2.7.1。

| 值 | 語意(推測) | 終點? |
|---|---|---|
| `01` | 已受理待確認 |  |
| `02` | 已確認待指定部門簽核 |  |
| `03H` / `03O` / `03` | 指定部門簽核中 / 股代第二關 / 簽核完成 |  |
| `04H` / `04O` / `04` | 處理部門簽核中 / 股代第二關 / 簽核完成 |  |
| `04S` | 抱怨記錄件待結案 |  |
| `05` | 退回重辦 |  |
| `06` | 結案 | ✔ |
| `D1` / `D2` | 作廢申請 / 作廢確認 | `D2` ✔ |
| `07` | **死值**,唯一寫入處已被註解 |  |

### C.2 `CLAIM_STATUS`(`COD006A.CODE_SORT = 'P7'`)

| 值 | 語意(推測) | 寫入者 |
|---|---|---|
| `01` | 已申請待主管確認 | `CPMM005`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:119`) |
| `02` | 主管已確認待結案 | `CPMB005`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:140`) |
| `06` | 結案 | `CPMB006`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:160`) |

`03`/`04`/`05` 在 `P7` 底下有沒有值、代表什麼,程式看不出來。

### C.3 `COMPLAIN_KIND`(`CTL014.SOURCETYPE = '486'`)

| 值 | 效果 | 錨點 |
|---|---|---|
| `1` | 預計完成日 = 受理日 + 1 營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:870-873` |
| `2` | + 2 營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:874-877` |
| `3` | + 7 營業日 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:878-881` |
| 其他 | **今天**(靜默落底) | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:882-885` |

### C.4 其他代碼類別

| 類別 | 來源 | 用在哪 |
|---|---|---|
| `COMPLAIN_CODE` 處理件分類 | `COD006A` `CODE_SORT='12'` | `CPM005A`、`CPMM004p0` 複選視窗、`CPMR005` 統計軸 |
| `SOLVE_CODE` 處理方式 | `COD006A` `CODE_SORT='13'` | `CPM006A` / `CPM0061A` |
| `CC_EMAIL_YN` | `CTL014` `SOURCETYPE='487'` | `CPMM004` 與四支關卡彈出視窗的下拉 |
| 權限旗標 Grid 下拉 | `CTL014` `SOURCETYPE='492'` | `CPMM003` 的六個權限欄 |
| `DATA_TYPE` | **無代碼表**,`1`/`2` 寫死 | 全模組 |

### C.5 本模組寫死的值〔客戶特定〕

| 值 | 意思 | 出現處 |
|---|---|---|
| `OP1` | 股務代理單位 | `CPMB002_PO.cs:153` `:155` `:157`、`CPMB003_PO.cs:152` `:154` `:156`、`CPMB002p0.cs:256`、`CPMB003p0.cs:264`、`CPMR004_PO.cs:133` |
| `M2` | 股務單位(股代案件的最後一關) | `CPMB002_PO.cs:157`、`CPMB003_PO.cs:156`、`CPMR004_PO.cs:133` |
| `op%` | 股代人員的帳號前綴 | `CPMB001_PO.cs:125`、`CPMB002_PO.cs:155`、`CPMB003_PO.cs:154`、`CPMM004_PO.cs:935` `:941` |
| `C5` / `C3` / `C4` | 法律顧問 / 法令遵循組 / 風險管理 | `CPMB001_PO.cs:610-612`、`CPMM004_PO.cs:1031-1033` |
| `E` `E1` `G2` | 行銷部 | `CPMB001_PO.cs:613`、`CPMM004_PO.cs:1034` |
| `G3` `G12` `G13` `GA` `G17` | 通路業務部 | `CPMB001_PO.cs:614`、`CPMM004_PO.cs:1035` |
| `920406` / `102744` | 兩個固定收信員工代號 | `CPMB004_PO.cs:688` |
| `C3` `G2` `G3` `G12` `G13` `GA` `Z2` `G17` `GC` `G15` | `CPMB004_PO.GetEmail()` 的固定收信部門 | `CPMB004_PO.cs:689` |
| `GC` → `G2` | 部門代碼替換 | `CPMR004_PO.cs:104` |
| `G` `GB` `G16` `G1` `G8` `G7` `G5` `G4` | `CPMR005` 報表的排序優先序 | `CPMR005_PO.cs:213-220` |
| `ta-it@example.com` | 所有通知信的寄件人 | 七支彈出視窗,例 `CPMB001p0.cs:380` |
| `301` | 四眼 `STATUS` 的佔位值 | 見 §2.7.3,六處 |

### C.6 四眼 `STATUS`

見 §2.7.3:本模組六支 B 畫面一律寫 `'301'`,沒有任何程式讀它。四支 M 畫面走框架,值由 `EVAStatusCode` 決定(`architecture.md §3.10`)。

## 附錄 D. 掃描母體與覆蓋率

`atlas_scan.py --module CPM --doc docs/modules/cpm.md` 的結果:

| 類別 | 母體 | 已提及 | 未提及 |
|---|---|---|---|
| 畫面 | 13 | 13 | 0 |
| 資料表 | 8 | 8 | 0 |
| SP / Fn | 0 | 0 | 0 |

母體外但本文有寫的物件,來源如下(**不是編造**):

| 物件 | 為什麼母體沒有 | 從哪讀到 |
|---|---|---|
| `GET_CPMB005` | `DB/` 沒有這支 SP 的腳本,掃描器掃不到 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:411` |
| `CPMB001_MGN_V` | 同上,`DB/View/` 沒有 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:660` |
| `CPM007B` | 不是表,是 `LoadDataSet` 的 DataTable 命名 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:404` |
| `CPMB001p0`~`CPMR004p2` 等彈出視窗 | 掃描器只收 7 碼代號,`yPopUpForm` 子視窗不算獨立畫面 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/` 下各檔 |
| `OFDI011` / `DSMR007` | 屬 OFD / DSM 模組母體 | §8.1 / §8.2 |

## 附錄 E. 讀本文時要注意的地方

依嚴重度排。每條:缺陷 / 影響 / 錨點 / 嚴重度。

### E.1 因參數格式改變而永久失效的通知分支

**缺陷。** `CPMM004_PO.GetEmail(strDeptNo, RelationDept_YN)` 的第三段 UNION 用 `AND '" + RelationDept_YN + "'='Y'` 當開關(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1051`)。但 2020-05-25 的異動把 `RelationDept_YN` 從單字元 `Y`/`N` 改成**五字元旗標串**(`YNNNY` 這種,`:1008-1012` 就是在拆這五個字元)。

**影響。** `'NNNNN' = 'Y'` 永遠是 false,所以「`CPM001A` 裡 `FUNCTIONID='CPMM004'` 的人」這段通知名單**自 2020-05-25 起完全失效**,建檔通知信只會寄給第一段 UNION(該部門有 `MGM_CD_CPMB001` 的人)。呼叫端 `CPMM004.cs:924` 又把 `ccEMAIL` 寫死 `"NNNNN"`,所以連第二段 UNION(五個相關部門)也一起死了 —— 註解說「20200612 改由 CPMB001 覆核完才通知相關部門」,那是刻意的;但第三段 UNION 是被順手弄死的,沒有任何註解提到。

**錨點。** `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1043-1051`(死掉的 UNION)、`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:924`(硬寫 `"NNNNN"`)。**嚴重度:高**(通知漏寄,沒有人會發現)。

### E.2 權限檢查缺口(三處)

**一、`CPMB005` 完全沒有權限過濾。** `Select` 的 WHERE 只有 `CLAIM_STATUS = '01'`,UI 傳來的 `USERID` 參數被忽略。任何能開此畫面的人都能簽核全公司的客訴件。錨點:`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:118-128` 對照 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005.cs:87-88`。**嚴重度:高**。

**二、`CPMB006` 沒權限時「寫入照做、狀態不推、無提示」。** `if (strYN == "Y" && 結案日非空) { row.CLAIM_STATUS = "06"; }` 之後無條件 `pxy.Modify()` + `Email()`。沒權限的人按確定,九個意見欄照樣寫進 DB、信照樣寄,只是狀態沒變,畫面完全沒說。錨點:`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:158-174`。**嚴重度:高**(結果類型是「過濾(無提示)」,但使用者以為是「成功」)。

**三、`CPMB004` 的抱怨記錄件那條路沒有部門過濾。** `(DATA_TYPE = '2' AND COMPLAIN_STATUS = '04S')` 是獨立的 OR 分支,不受後面 `COMPLAIN_DEPT IN (...)` 約束。錨點:`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:145-163`。**嚴重度:中**。

另外 `CPMM005`(客訴件建檔)也沒有任何權限過濾(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:162-322` 不 join `CPM003A`),但那是「建檔誰都能建」,語意上說得通,列在 §4.4 不重複。

### E.3 整段寫入被註解,按鈕變空操作

**缺陷。** 四支關卡畫面的「執行」鈕 → `PO.ExecuteNonQuery` → `//UpdateDataList(model); return mModel;`。

**影響。** 按下去沒反應、沒錯誤。真正的寫入在雙擊後的彈出視窗。維護者若照著被註解的 `UpdateDataList` 去理解「批次在寫什麼」會得到完全錯誤的結論(註解版只寫 `COMPLAIN_COMM` + `ASN_SOLVE_DEPT_NO` + 四眼欄,沒有 `COMPLAIN_STATUS`)。

**錨點。** `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:210-215` 與被註解的 `:221-310`;`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:229-234`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:231-236`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:234-239`。**嚴重度:高**(與 CRM `CRMB001_PO.cs:195-214` 同型)。

### E.4 被註解掉但外殼還在的檢核(四處)

| # | 位置 | 被註解的是什麼 | 外殼留下什麼 |
|---|---|---|---|
| 1 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB006p0.cs:253-264` | 「尚未結案,不能輸入結案日期」整條 | `DoValidate()` 方法還在、呼叫還在,永遠無錯 |
| 2 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB003p0.cs:296-320` | 資訊簽核 / 副主管審核:`07` 狀態 + 「副主管尚未審核!」+「無此權限!」 | 註記 `//20180214 modify by jye 加入資訊簽核` 還在,`07` 變死值 |
| 3 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM003.cs:269` | `this.validatorManager1.DataValidate();` | 框架必填檢查整組不跑,只剩三條手寫檢查;其他三支 M 都有跑 |
| 4 | `Dev/ATLAS.CPM.Report/Source/UI/ReportUI.CPM/CPMR004.cs:72-76` | `if (this.ValidateErrList.Show()) { e.Cancel = true; return; }` | `DoValidate()` 還是被呼叫(而且它本身是空的),真正生效的檢查在 `:122-126` |

**嚴重度:#1 #2 高,#3 #4 中。**

### E.5 顯示欄位 join 錯人(兩支畫面、三個欄位)

**缺陷。** `CPMM005_PO.BuildMasterSQLString` 的四個 `COD009` 別名全部 join 在 `CPM007A.EMP_NO`:

```
LEFT JOIN COD009 A ON CPM007A.EMP_NO = A.EMP_NO     -- A 被拿來當 LEADER_EMP_NO_NAME
LEFT JOIN COD009 B ON CPM007A.EMP_NO = B.EMP_NO     -- B 被拿來當 BOSS_EMP_NO_NAME
LEFT JOIN COD009 D ON CPM007A.EMP_NO = D.EMP_NO     -- D 被拿來當 CLAIM_EMP_NO_NAME
```

`CPMB005_PO` / `CPMB006_PO` 是另一種錯法:三個別名 `B` / `C` / `D` 全部 join 在 `CPM007A.CLAIM_EMP_NO`。

**影響。** 客訴件維護與兩支關卡畫面上的「申請人姓名」「組主管姓名」「部門主管姓名」顯示的是同一個人。同一支 PO 的 `GetReport_Data` join 對了(`A`=`CLAIM_EMP_NO`、`B`=`LEADER_EMP_NO`、`C`=`BOSS_EMP_NO`),證明是 bug 不是設計 —— **報表印出來的人跟畫面上看到的人不一樣**。

**錨點。** `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:198-206` 對照 `:451-453`;`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:111-116`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:111-116`。**嚴重度:中**(顯示錯誤,不影響流程)。

另外 `CPMM003_PO` 有做 `COD009` 的 `ROW_NUMBER()` 去重(`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM003_PO.cs:136-143`),但同模組其他畫面都沒做 —— 一個 `UID_CODE` 在 `COD009` 有兩筆(離職再任職)時,那些畫面會出現重複列。

### E.6 位置取參數 / 掛錯控件 / Caption 對調

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | `pxy.GetEMAIL(user, GetUidCode(BOSS_EMP_NO), GetUidCode(LEADER_EMP_NO))` 但簽名是 `(strUserID, strLEADER_EMP_NO, strBOSS_EMP_NO)` —— **第二三個參數對調** | 客訴件主管確認的通知信寄錯人(實際收件者由版控外的 SP `GET_CPMB005` 決定,無法從 repo 判斷後果) | 呼叫 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:182` 對照簽名 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:402` | 中 |
| 2 | `AddError(this.ucDEPT_SOLVE_EMP_NO, "展延日期為必填")` / `AddError(this.ucDEPT_SOLVE_EMP_NO, "結案日期為必填")` | 訊息正確但游標跳到「處理人員」欄,使用者找不到要填哪裡 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB004p0.cs:641`、`:646` | 低 |
| 3 | `CPM004A_SELECT` 的 `ASN_SOLVE_DEPT_CH_NAME` 與 `SOLVE_DEPT_CH_NAME` 兩個 Caption 在 `CPMB003`/`CPMB004` 的 xsd 裡**對調** | Grid 欄位標題與資料對不上 | `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB003Model.xsd` 對照 `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB001Model.xsd`(明細見 §2.5 末) | 中 |
| 4 | `CPMB004` 刪除前訊息寫「不能修改」,實際是不能刪除 | 訊息誤導 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:907` | 低 |

### E.7 寫死常數與跨模組借用

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | 跳號一覽表用 `SrNo.AllotNoForNfd`(值 `"OFD220A"`) | CPM 的跳號紀錄被記在 NFD/OFD 的類別底下,跨模組查詢跳號時會混在一起;`CPMM004` 與 `CPMM005` 兩支共 16 個 handler 都用同一個 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1085`(另七處在 `:1081-1123`)、`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103` | 中 |
| 2 | `CPMB004_PO.GetCloseEmail` join `AA_USER`,其他 20 多處都是 `TA_AA_USER` | 若兩者不是同義詞(synonym),結案通知信會查不到人 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB004_PO.cs:650` | 中 |
| 3 | 五個 `CC_EMAIL_*` 的部門清單在 `CPMB001_PO` 與 `CPMM004_PO` 各寫一份,一字不差 | 組織調整時要改兩處 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:609-615`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:1030-1036` | 中 |
| 4 | `DATA_TYPE` 的中文對照三套並存:「需求處理件/抱怨記錄件」vs「問題件/客訴件」 | 同一筆資料在不同報表顯示不同名稱 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:251` vs `:673`;`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:110` vs `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:77-80` | 低 |

### E.8 有訊息但行為不符 / 檢核永遠不成立

**一、`CPMM004` 的「請至少輸入任一筆 查詢條件」永遠不會跳。**

```
if (string.IsNullOrWhiteSpace(this.utxtCOMPLAIN_NO_0.Text) && … &&
    (udatCOMPLAIN_Date_ST.Value == null && udatCOMPLAIN_Date_END == null))
```

最後一項比的是**控件物件本身**(`udatCOMPLAIN_Date_END`)而不是 `.Value`。控件永遠不是 `null`,整個 `&&` 鏈永遠 false,這條檢核形同不存在。使用者不填任何條件按查詢,會直接送出一條只有部門過濾的全表掃描。錨點:`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:538-546`(問題在 `:543`)。**嚴重度:中**。

**二、同一支的日期參數複製貼上錯。** `if (this.udatCOMPLAIN_Date_ST.Value != null)` 出現兩次,第二次應該是 `_END`:

```
if (this.udatCOMPLAIN_Date_ST.Value != null)
    …AddParametersRow("COMPLAIN_SDATE", …, udatCOMPLAIN_Date_ST…);
if (this.udatCOMPLAIN_Date_ST.Value != null)          // ← 應為 _END
    …AddParametersRow("COMPLAIN_EDATE", …, udatCOMPLAIN_Date_END.DateTime…);
```

現況被 `:548-549` 的「起迄必須皆(不)填寫」擋住而不會出事,但那條檢核一旦放寬就會拿 `DateTime.MinValue` 去組 `COMPLAIN_DATE <= '00010101'`,查出零筆。錨點:`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM004.cs:587-590`。**嚴重度:中**。

**三、`CPMM005` 的「是否確定新增？」是阻擋不是詢問。** 訊息用問句寫,但走的是 `ValidateErrList.AddError` + `e.Cancel = true`,使用者沒有「是」可以按,只能改戶號。兩處都這樣。錨點:`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMM005.cs:440-444`、`:494-503`。**嚴重度:低**(行為比訊息嚴格,不會放行錯的資料)。

**四、`CPMB001p0` 完全沒有存檔前檢核。** 其他三支關卡都有 `DoValidate()`,這支沒有,指定處理部門可留空直接送出。錨點:`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:224-280`。**嚴重度:中**。

### E.9 Oracle 三值邏輯與 SQL 寫法

**一、`欄 <> ' '` 遇 NULL 靜默過濾(九處)。** 四支報表 PO 的日期區間查詢都會多加一條 `AND CPM004A.<日期欄> <> ' '`:

| 檔 | 行 | 欄位 |
|---|---|---|
| `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs` | `:159` `:188` `:241` `:325` | `COMPLAIN_DATE` / `COMPLAIN_PRV_DATE` / `COMPLAIN_DELAY_DATE` / `CLOSE_DATE` |
| `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs` | `:121` `:151` | `COMPLAIN_DATE` / `COMPLAIN_DELAY_DATE` |
| `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs` | `:124` | `COMPLAIN_DATE` |

日期欄是 `VARCHAR2`,存空白字串時 `' ' <> ' '` 為 false(擋掉,符合意圖);但**存 NULL 時 `NULL <> ' '` 是 UNKNOWN,那一列一樣被擋掉,而且沒有任何提示**。這跟 CAS `CASB001_PO.cs:214`、CLS `CLSM001_PO.cs:179`、DSM `DSMB001_PO.cs:136` 是同一型 —— **這是第五個中同一招的模組**。 **嚴重度:中**(報表少列,查不出原因)。

同型還有 `AND CPM004A.COMPLAIN_STATUS NOT LIKE 'D%'`(`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:91`、`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs:96`)—— `COMPLAIN_STATUS` 為 NULL 的案件被靜默排除。

**二、外接條件把 `(+)` 外部聯結變成內部聯結。** `CPMR005_PO` 寫:

```
AND CPM004A.COMPLAIN_NO = CPM005A.COMPLAIN_NO(+)
AND CPM005A.COMPLAIN_CODE = COD006A.CODE(+)
AND COD006A.CODE_SORT = '12'          -- ← 沒有 (+)
```

最後一行對外接表下了沒有 `(+)` 的條件,Oracle 會把整個外接退化成內接:**沒有處理件分類明細、或分類代碼不在 `CODE_SORT='12'` 的案件,直接從統計報表消失**。同一支的 `COMPLAIN_CODE` 篩選(`:201`)也是同樣情形。錨點:`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:87-90`、`:195-203`。**嚴重度:中**。

**三、`AND CPM0031A.DEPT_NO '…'` 少了等號。** `CPMB002_PO.GetEmail_YN` 的 `nDelay == 1` 分支有語法錯誤(少 `=`),會丟 ORA-00920,被 `catch` 吞掉回傳 `null`,呼叫端 `dt.Select()` 再丟 NullReferenceException。目前 `nDelay` 被硬寫 `0`(`Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB002p0.cs:373`,註解「無展延流程」)所以走不到 —— **一旦有人把展延流程打開就會炸**。錨點:`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB002_PO.cs:693`。**嚴重度:中(休眠中)**。

**四、字串串接進 SQL(全模組,約 60 處)。** 使用者 ID、部門代碼、單號、姓名、身分證號一律 `"… '" + value + "'"`。舉例: `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:138-139`(`userID`)、 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:294`(`COMPLAIN_NO`)、`:305`(`ID_NO` 用 `LIKE`)、`:847`(子查詢內的 `COMPLAIN_NO`)、 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM005_PO.cs:336`(`BF_NO`)、 `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:95`(`USER_ID`)。全模組只有三處是參數化的:`CPMB001_PO.GetDeleteGrant`(`:666`)、`CPMB004_PO.GetCloseEmail`(`:660`)、`CPMM004_PO.GetReport_Data`(`:758-777`)與 `CPMM005_PO.GetReport_Data`(`:460`)。 **嚴重度:中**(值多半來自系統而非自由輸入,但 `BF_NAME` / `ID_NO` 是使用者打的)。

### E.10 一律回報成功 / 回傳值丟掉

| # | 缺陷 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | 七支彈出視窗 `BasicViewVDB view = pxy.Modify(...)` 之後**完全不看 `view.Util.Result`**,直接寄信 + `DialogResult.OK` + 從 Grid 移除該列。伺服器端失敗(`AddResultRow(false, …)`)時使用者看到的仍是「成功」 | `CPMB001p0.cs:267-279`、`CPMB002p0.cs:319-328`、`CPMB003p0.cs:347-356`、`CPMB004p0.cs:276-283`、`CPMB005p0.cs:149-157`、`CPMB006p0.cs:170-178`(皆在 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/`) | **高** |
| 2 | `CPMB005` / `CPMB006` 的 `UpdateDataList` 丟掉 `ExecuteNonQuery` 回傳值,用 `i += 1` 數迴圈次數。`WHERE CLAIM_NO` 沒對到列也算成功 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:298-304`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:306-312` | 高 |
| 3 | 零列時 `if (i > 0)` 不成立 → 既不 `Commit` 也不 `Rollback`,`finally` 只 `Dispose`;`model.Utility.Result` 一列都沒加,呼叫端拿到空結果也當成功 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:301-304`、`:323-328` | 中 |
| 4 | `CPMB001p0` 的刪除鈕同樣不看 `pxy.Delete` 的結果 | `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:506-513` | 中 |
| 5 | 所有 `GetEmail*` 失敗時 `return null`,呼叫端直接 `dt.Select()` / `dt.Rows.Count` | 例 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:643-647` 對照 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB001p0.cs:348-355` | 中 |

**本模組沒有「批次呼叫 SP 後硬寫成功」那一型**(只有一支 SP,而且只用來查 EMAIL),但第 1、2 條的效果是一樣的。

### E.11 其他讀碼陷阱

| # | 事情 | 說明 | 錨點 |
|---|---|---|---|
| 1 | `dept_no` / `dept_NO` 算了不用 | `CPMM004_PO.BuildMasterSQLString` 每次查詢都多打一次 DB 取登入者部門,結果完全沒用到;`CPMR005_PO` / `CPMR006_PO` 也一樣 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:185` `:191`、`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR005_PO.cs:58` `:69`、`Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR006_PO.cs:57` `:68` |
| 2 | `SOLVE_DATE11` / `SOLVE_CFM_UID11` 等八個死欄位 | 只在 `CPMB001Model.xsd` 的結果集裡,實體表沒有,程式不讀不寫 | `Dev/ATLAS.CPM/SOURCE/Entity/DataEntity.CPM/CPMB001Model.xsd` |
| 3 | 每支 PO 的介面註解都是「覆核層級管理 PO 共用介面」 | 12 支一字不差的樣板殘留,不能拿來推測用途 | 例 `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:20-22` |
| 4 | `//this.MasterTable = new TableMapping("OFD701", "SEAL");` | 從 OFD 複製來的殘骸,兩支都有 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:46`、`Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB006_PO.cs:46` |
| 5 | `CPMB001_Ctl.GetDeleteGrant` 直接 `new CPMB001_PO()` | 繞過 `DataAccessPool`,與同檔其他方法的 `GetDaoInstance<ICPMB001_PO>()` 不一致 | `Dev/ATLAS.CPM/SOURCE/Control/Control.CPM/CPMB001_Ctl.cs:38-42` |
| 6 | `CPMB005_PO.GetDeleteGrant` 之後有一行不可及的 `return 0;` | `try` 的兩條路都 return 了,編譯器只會警告 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB001_PO.cs:680` |
| 7 | `UpdateDataList` 參數名大小寫不一致 | PO 找 `"UserID"`、UI 塞 `"USERID"`;靠 `DataTable.CaseSensitive` 預設 false 才對得上 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:262` 對照 `Dev/ATLAS.CPM/SOURCE/UI/UI.CPM/CPMB005p0.cs:144-145` |
| 8 | `STATUS = : STATUS` 綁定符號後有空白 | 13 個四眼欄位的綁定都寫成 `: XXX`;Oracle 可解析,但與同檔前幾行的 `:CLAIM_CONTENT` 風格不一致,容易誤判 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB005_PO.cs:237-251` |
| 9 | `CPMM004` 報表對每一列各下兩次子查詢 | `CPM005privot` / `CPM006privot` 用 `SYS_CONNECT_BY_PATH`,N 列 = 2N 次來回 | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMM004_PO.cs:786-794` |
| 10 | 所有 `.cs` / `.xsd` 皆為 UTF-8 | 實測 142 支 `.cs` 與全部 `.xsd` 都是合法 UTF-8,**本模組沒有混編碼問題** | — |
| 11 | `CPMB003` 佇列的 `ORDER BY` 與其他三支相反 | `COMPLAIN_NO, COMPLAIN_KIND` vs 其他的 `COMPLAIN_KIND, COMPLAIN_NO` | `Dev/ATLAS.CPM/SOURCE/PO/PO.CPM/CPMB003_PO.cs:160` |
| 12 | `CPMR004` 的明細少一張 `CPM0061A` | 與 `CPMM004` / 四支 B 不一致 | `Dev/ATLAS.CPM.Report/Source/PO/ReportPO.CPM/CPMR004_PO.cs:46-48` |

### E.12 標「假設」的地方一覽

| # | 假設 | 依據 | 怎麼驗證 |
|---|---|---|---|
| 1 | `CPMB001_MGN_V` 是主管白名單 | `SELECT EMP_NO, UID_CODE, EMP_NAME … WHERE UID_CODE = :UID_CODE`,回傳有列就顯示刪除鈕 | 查 DB 的 View 定義 |
| 2 | 四眼 `STATUS = '301'` 代表「已生效」 | 六支畫面一致寫入、無人讀取;不在 `architecture.md §3.10` 反推出的值域內 | 查 `EVAStatusCode` 或 DB |
| 3 | `COD006A` `CODE_SORT` = `Q2` / `P7` / `12` / `13` 的中文說明 | 只從欄位語意與畫面標題推,值域表內容不在版控 | 查 `COD006A` |
| 4 | `CPMB004` 退回重辦故意不清 `SOLVE_DEPT_NO` | 程式清了九個欄位獨獨留下它,沒有註解說明 | 問業務 |
| 5 | 抱怨記錄件走兩關(`CPMM004` → `CPMB001` → `CPMB004`) | `CPMB001p0.cs:254` 推 `04S`、`CPMB004_PO.cs:146` 撈 `04S`、`CPMB002`/`CPMB003` 都限 `DATA_TYPE='1'` | 對照業務流程圖 |
| 6 | 「CPM」的展開 | repo 內查無定義 | 問客戶 |
| 7 | `AA_USER` 與 `TA_AA_USER` 是同義詞 | 只有一處用 `AA_USER`,其餘全用 `TA_AA_USER`,且該處程式在線上 | 查 DB synonym |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。純程式碼閱讀彙整,未修改 ATLAS 任何原始碼 |

由 build_doc.py v2.0.0 於 2026-09-15 10:47 產生 · 標題 89 · 圖 5 · 表格 70 · 程式錨點 379 · § 連結 40 · 引用檢查：畫面 15（缺 0） · Table 12（缺 0） · Report 4（缺 0） · 結果集 5（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
