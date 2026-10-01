ATLAS 知識庫 — 11-模組-CPM-CRM-DSM-TMK

本檔合併以下文件:modules/cpm.md、modules/crm.md、modules/dsm.md、modules/tmk.md


============================================================
【文件】kb/modules/cpm.md
============================================================

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

============================================================
【文件】kb/modules/crm.md
============================================================

# ATLAS CRM 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀三段:§0.2(這模組最反直覺的事)、§4–§7 各節末的卡控總表、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表中文名與少數彈出視窗標題**推測**。與 CAS 不同的是 CRM 有 11 個報表中文名寫在程式裡,推測的把握度比 CAS 高一截(§0.1)。 ⚠ **〔客戶特定〕**:`USAGE = '1'`、`SAL_CD` 的 `A` / `B` / `C` / `D` 分級、`CODE_SORT` 的 `P5` / `1C` / `11`、部門代碼補 `'01'` 的規則都是本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`CRM003A` 同時服務 CAS 與 TMK,`CRM001A` / `CRM002A` / `CRM007A` 被 `Dev/Common` 的共用 PO 讀,`CRM006A` / `CRM0061A` 被 TMK 與 OFD 讀(見 §8),改動要一起看。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。與 CAS 的交界寫在 `cas.md §8`,本文 §8 從 CRM 這側寫,兩邊結論一致。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:CRM 管「還沒成為客戶的人」與「該派誰去接觸他」——潛在客戶的聯絡紀錄、索取資料紀錄,以及把既有受益人名單依規則分配給直銷業務員去追蹤的整套指派作業。**

推測依據四條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 報表中文名(最強的一條) | 「指派單位明細表」「指派業務員明細表」「指派名單追蹤彙總表-By單位別」「指派名單追蹤明細表-By業務員別」「指派名單聯絡結果統計表」「客戶通話記錄明細表」「客服潛在客戶索取資料明細表」 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:221`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:145`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:196-202`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:151`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:122-126` |
| 欄位中文名 | `CRM003A` 是「潛在客戶序號」「潛在客戶姓名」「拒絕電訪行銷」;`CRM007A` 是「分配序號」「本次指派單位代碼」「本次指派業務代碼」「再聯絡日期」「聯絡結果代碼」「有無意願申購」 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |
| 畫面上的中文標籤 | 「規則六:依條件篩選客戶,手動上傳」「備註:依條件篩選的客戶無須『產生名單』,僅須執行『上傳名單』」「已指派歸類(轉出)」「已指派歸類(轉入)」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.Designer.cs:207`、`:220`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.Designer.cs:475`、`:527` |
| 彈出視窗標題 | 「員工銷售機構權限明細設定」「客戶歷史資料」「潛在客戶資料選取視窗」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001p0.Designer.cs:367`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003p0.Designer.cs:281`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003p1.Designer.cs:285` |

「CRM」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「潛在客戶與直銷指派」描述它的業務範圍。

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 查詢權限設定 | 哪個員工可以查哪些銷售機構、以及該機構底下哪些員工的資料 | `CRMM001` | `CRM001A` + `CRM002A` |
| B 部門歸屬設定 | 把銷售機構歸類到「部門歸屬類別」,給指派作業當分群依據 | `CRMM002` | `CRM008A` |
| C 潛在客戶 | 潛在客戶主檔 + 每一次通話紀錄 + 每一次索取資料紀錄;重複客戶合併 | `CRMM003`、`CRMB005`、`CRMR007`、`CRMR008` | `CRM003A` + `CRM006A` / `CRM0061A` / `CRM004A` / `CRM0041A` |
| D 直銷指派 | 依規則產生「該追的客戶名單」,指派給單位 / 業務員,記錄聯絡結果與再聯絡日 | `CRMB001`–`CRMB004`、`CRMI001`、`CRMR001`–`CRMR006` | `CRM007A` |
| E 客戶分級參數 | 客戶等級的庫存級距、應親訪 / 應電訪次數、計算頻率 | `CRMM004` | `CRM004` |

### 0.2 這模組最反直覺的三件事

**(1) 掃描母體少報了四張表。**`docs/_candidates/crm.md` 第 2 節只列 6 張表,實際上本模組動到的實體表是 **10 張**:母體漏了 `CRM001A`、`CRM002A`、`CRM008A`、`CRM007A`。

原因是掃描器的主檔正規式只認 `this.MasterTable = new xTableMapping(...)` 這一種寫法,而:

| 漏掉的表 | 為什麼漏 | 錨點 |
|---|---|---|
| `CRM001A` `CRM002A` | `CRMM001_PO` 繼承 `BaseMultiRowEVADaoPO`,主檔是 `List`,寫法是 `this.MasterTable.Add(...)` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `CRM008A` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:40` |
| `CRM007A` | `CRMI001_PO` / `CRMB001_PO`–`CRMB004_PO` 都是裸 DAO,根本沒有 `xTableMapping`,表名只出現在 SQL 字串裡 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:80`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:107` |

這正是「`CRMM001` 與 `CRMM002` 沒有宣告主明細」的答案:**它們有主檔,只是用多筆版的寫法宣告,而且沒有明細概念**(見 §2.1、§4.1、§4.2)。

**(2) `CRMB001` 的「產生名單」按鈕目前不會產生任何名單。**唯一會下 SQL 的那段(呼叫 `S_TA_CRMB001_EXCUTE`)整段被註解掉了(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`),剩下的只有「從 CSV 上傳指派名單」那條路。按下執行鈕時,`Execute` 走完整個 try 區塊卻一行 SQL 都沒下,而且 `Result` 在開頭被 `Clear()` 之後沒有再塞任何一列(`:77`)。**畫面不會報錯,也不會有成功訊息。**這是本模組最會咬人的一條(附錄 E.1)。

**(3) `CRMM003` 的兩張索取明細永遠查不出資料。**`CRM004A` 與 `CRM0041A` 的取數 SQL 被硬加了 `WHERE 1=2`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454`)。畫面上「索取資料」頁籤在維護模式下一定是空的,實際內容改由 `GetHistory_Call_Req` 另外撈進 `CRM004A_HIS`(§4.3)。

### 0.3 不管什麼

以下**不在** CRM 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人(正式客戶)基本資料 | BMS | `BMS001A_V01` 只被 join 取姓名 / 地址 / 電話,從不寫入;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:76-81` |
| 員工主檔、部門、離職日 | COD / OFD | `COD009` 與 `OFD002` 全部是 `LEFT JOIN`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:301-305` |
| 銷售機構主檔 | OFD | `OFD068A` 只被 join 取簡稱,`CRMM001` 的機構清單直接 `SELECT ... FROM OFD068A`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:318-324` |
| 直銷業務員的職級與所屬業務部門 | SAL(版控外) | `SAL051` 只被 `LEFT JOIN` 取 `SAL_CD` 與部門;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:302-303` |
| 電訪(OutBound)本身的作業 | TMK | `TMK001A` / `TMK_BF_V` 只被 join 取電訪人員;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:638-649` |
| 申購 / 贖回交易與庫存金額怎麼算 | OFD / EC | `CRM007A` 的 `TOT_ALLOT_AMT` / `BAL_AMT` 是被寫進來的結果,CRM 內沒有任何一支程式計算它們 |
| 「規則一~規則五」到底怎麼篩客戶 | **不明,在版控外的 SP** | 唯一的呼叫點被註解(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-205`),SP 本體不在 repo 內。**假設**:規則邏輯全寫在 `S_TA_CRMB001_EXCUTE` 裡,依據是被註解的參數只有結算日與規則代碼兩個 |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 客服 / 電訪人員 | 建立與維護潛在客戶、記錄每通電話與每次索取資料 | `CRM006A_HIS` 的 `CREATEID` 欄位 Caption 直接寫「客服」;`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| 直銷主管(`SAL_CD` = `A`) | 查詢名單時**必須**指定轉出單位;可以自由改部門與業務員欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:198-201`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348-358` |
| 組主管(`SAL_CD` = `B`) | 同上,部門與業務員欄位解鎖 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348` |
| 直銷業務員(`SAL_CD` = `C`) | 部門與業務員欄位鎖死成自己,只看得到分配給自己的名單 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:98` |
| 直銷助理(`SAL_CD` = `D`) | 在共用的業務員下拉可被排除 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:280-282` |
| 名單管理人員 | 執行產生 / 刪除名單、上傳 CSV 名單、跨單位與跨業務員調撥 | `CRMB001`、`CRMB002`、`CRMB003` |
| 系統管理 | 設定誰能查誰(`CRMM001`)、機構歸屬分類(`CRMM002`)、客戶分級參數(`CRMM004`) | 三支都是標準四眼維護畫面 |
| 覆核者 | 對 M 畫面做驗證 / 覆核 / 退回 | 四眼流程由框架處理,見 `architecture.md §3` |

**權限不在程式碼裡的部分比 CAS 多。**本模組的「可見範圍」有兩套機制疊在一起:功能權限由 PTPF 平台庫決定(`architecture.md §3.7`),資料可見範圍由 `CRM001A` / `CRM002A` 這兩張表加上 `F_TA_GET_EMPS` 這支版控外的 TVF 決定(§5.3、§8.2)。

### 0.5 全域開關

repo 內**沒有**任何 CRM 專屬的設定檔開關。`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支 M 畫面的主檔與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:54`(`CRMM001`)、`:61`(`CRMM002`)、`:69`(`CRMM003`)、`:76`(`CRMM004`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:55`、`:62`、`:70`、`:77` |
| `formstyle` | `CRMB001`–`CRMB005` 與 `CRMI001` 宣告為 `OneStep`;報表側全部 `Report` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`、`:48`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/App.config:15` |

四件要記住的:

- **四支 M 畫面一個都沒宣告 `detailtable`**,但 `CRMM001` 與 `CRMM003` 的 PO 確實有多張表(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:67-71`)。**設定檔與程式不一致,以程式為準。**

- **`CRMM004` 的 `mastertable` 寫的是 `CRMM004` 不是 `CRM004`。**設定檔填的是 typed DataSet 的表名,PO 那邊才是真正的 DB 表名 `CRM004`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:44`)。這是全庫少見的 vdb 表名與 db 表名不同的例子,也是掃描母體把 `CRM004` 報成「0 欄位」的原因(§2.3)。

- **`CRMM001` 的 `pkey` 只寫了 `EMP_NO`**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:54`),而 xsd 的 PK 是 `EMP_NO` + `AGENT_ID` + `AGENT_CODE` 三欄(`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd`)。PO 那邊宣告的 `MasterPKey` 也只有 `EMP_NO`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:51`)——這是刻意的,因為多筆版把「同一個員工的所有列」當成一批(§4.1)。

- `Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:80` 宣告 `.NETFramework,Version=v4.8`,而多支 PO 頂端留著 `using Oracle.ManagedDataAccess.Client;// .NET4.8 FIX` 的手動修補痕跡(例 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:5`)——與 CAS 同一批升版作業。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] CRM 模組全景：設定、潛在客戶、直銷指派、報表四條線，以及五張被別的模組讀的表
圖中文字:① 設定線：誰能查誰、機構怎麼歸類、客戶怎麼分級 / CRMM001 / 查詢權限 CRM001A+CRM002A / CRMM002 / 機構部門歸屬 CRM008A / CRMM004 / 客戶分級參數 CRM004 / COD009 OFD002 OFD068A / 員工／部門／機構 外部 / ② 潛在客戶線（客服） / CRMM003 / 潛在客戶 CRM003A 一主四明細 / CRM003A〔共用〕 / USAGE=1 CRM／3 CAS / CRMB005 / 重複客戶合併 走 SP / CRMR007 CRMR008 / 通話／索取明細表 / ③ 直銷指派線（與②完全沒有資料關聯） / CRMB001 / 產生／刪除／上傳 CRM007A / CRMB002 / 單位調撥 / CRMB003 / 業務員指派 / CRMB004 / 聯絡結果登錄 / CRMI001 / 名單查詢 唯讀 / ④ 報表（資料全在版控外的 SP） / CRMR001 CRMR002 / 指派單位／業務員明細 / CRMR003 CRMR004 CRMR005 / 追蹤彙總／明細 / CRMR006 / 聯絡結果三式 / 10 支 SP 不在版控 / S_TA_CRMnnn_* / ⑤ 對外：本模組維護、別人使用 / CRM001A CRM002A / BasicCRM_PO／CLS／DSM／OFD / CRM007A / 共用控件與下拉的資料來源 / CRM006A CRM0061A / TMK／OFD 唯讀 / CRM003A / CAS／TMK
```

*圖:圖 1 CRM 全景。橘框=本模組的維護／批次入口；灰虛框=被別的模組讀的表；黑框=無原始碼的外部來源；橘虛框=含寫死值或行為會咬人〔客戶特定〕。②與③兩條線之間沒有任何欄位、join 或程式呼叫關係。*

看圖的四個重點:

1. **C 線(潛在客戶)與 D 線(直銷指派)之間沒有任何程式或資料關聯。**`CRM003A` 系列與 `CRM007A` 沒有共同欄位、沒有 join、沒有互相呼叫。它們被放在同一個模組裡是歷史結果,不是設計。要驗證:全庫搜 `CRM003A` 與 `CRM007A` 同時出現的 SQL,零命中。

2. **A 線(`CRMM001`)不是給 CRM 自己用的。**`CRM001A` / `CRM002A` 在 CRM 內部只被 `CRMM001` 自己維護,真正讀它的是共用 PO `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:294-305`,而那支被 CLS / DSM / CRM 的報表共用(§8.2)。**改 `CRMM001` 的資料,會改到別的模組畫面上看得到什麼。**

3. **報表那一排全部靠版控外的 SP。**8 支 R 畫面加上 `CRMB001` 的「產出客戶名單」,共 10 支 SP(`S_TA_CRMR001_GET`…`S_TA_CRMR008_GET_2`、`S_TA_CRMB001_GET`),一支都不在版控內(附錄 B)。

4. **只有 `CRMB002` / `CRMB003` / `CRMB004` 會直接 UPDATE 四眼欄位以外的業務欄位,而且完全繞過 EVA 引擎。**三支都是手寫 `UPDATE CRM007A SET ...`(§6.3)。

### 1.2 資料表關係

見 §2 節首的圖。要記住的:

- **`CRM003A` 是唯一的一主四明細。**四張明細其實是兩組:通話(`CRM006A` 表頭 + `CRM0061A` 種類明細)與索取(`CRM004A` 表頭 + `CRM0041A` 種類明細),兩組結構完全對稱(§2.1)。

- **`CRM001A` 與 `CRM002A` 是 1:N,但在 PO 眼中兩張都是「主檔」。**多筆版沒有明細概念,所以 `CRM002A` 的新增是手寫 INSERT 補的(§4.1)。

- **`CRM007A` 完全獨立**,沒有明細,PK 是 `ASSIGN_NO` + `BF_NO`。

- **`CRM004` 是參數表**,PK 只有 `CUS_LV`,全庫只有 `CRMM004` 一支畫面碰它。

### 1.3 主要維護畫面的四眼與卡控順序

見 §4 節首的圖。整條鏈由上而下:

| 階段 | 在哪 | 失敗的表現 |
|---|---|---|
| 1 必填與格式 | `validatorManager1.DataValidate()`(框架,無原始碼) | 紅框 + 訊息清單 |
| 2 本畫面自訂檢核 | 各畫面的 `DoValidate()` | 同上 |
| 3 需要查 DB 的檢核 | UI 直接 `new` 一個 `_Pxy` 或用既有的 `FormProxy` 打過去 | 對話框(不是訊息清單) |
| 4 主檔欄位回填明細 | `CRMM002` 的 `SetMasterToDetail()`;`CRMM001` / `CRMM003` 在 `GetPageValue()` 內一併做 | 不會失敗,但漏欄位會讓明細 PK 是空的 |
| 5 PO 的 `Before*` | `BeforeAdd` 取號、`BeforeSelect` / `BeforeGetMaintainData` 換 SQL、`BeforeUpdate` 做區間重疊檢查 | `args.Cancel = true` + `CancelMsg`,或例外 → 整筆失敗 |
| 6 四眼引擎 | 框架 DLL(無原始碼) | 見 `architecture.md §3` |
| 7 PO 的 `After*` | 只有 `CRMM003` 有(8 個掛點,全是跳號一覽表) | `throw` → 整筆回滾 |

**與 CAS 的差別有兩點**:(a) CRM 有畫面在 `BeforeAdd` / `BeforeUpdate` 用 `args.Cancel + args.CancelMsg` 擋(`CRMM004`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:100-104`),這是**伺服器端**的卡控,CAS 全模組沒有;(b) `CRMM001_PO` 覆寫了 `Add` / `ApproveDelete` / `IsChangedByData` 三個基底方法,直接改寫四眼引擎的行為(§4.1)。

### 1.4 批次 / 報表資料流

見 §6 節首的圖(§7 沒有圖,報表流程與 CAS 同構)。四件事:

- **五支 B 畫面沒有一支是排程。**全部是 `formstyle="OneStep"` 的使用者按鈕觸發(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`),`Dev/` 下也沒有任何 CRM 的 WindowsService。

- **`CRMB002` / `CRMB003` / `CRMB004` 的「執行」是逐列 UPDATE**,一列一個 `DbCommand`,同一個交易內跑完再 commit(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:202-234`)。

- **報表是兩條獨立往返**:`GetReportData` 拿資料、`GetReportObject` 拿 `.rpt` 檔的 byte,後者的類別名由用戶端傳過來(與 `architecture.md §6.5` 描述一致)。

- **報表 PO 全部把 SP 包在明確交易裡**(`m_db.BeginTransaction()` … `tran.Commit()`),這點與 CAS 不同,CAS 的報表 PO 沒有交易(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54`、`:74`)。

### 1.5 一日作業泳道

repo 內**找不到任何排程設定**,所以以下是**推測**的作業順序,依據是資料相依:某張表要有資料,前一步才做得下去。

| 時點 | 誰 | 做什麼 | 畫面 | 依賴 |
|---|---|---|---|---|
| 建置期 | 系統管理 | 設定客戶分級參數(級距、應訪次數、頻率) | `CRMM004` | — |
| 建置期 | 系統管理 | 設定銷售機構的部門歸屬分類 | `CRMM002` | 機構要先在 `OFD068A` 存在 |
| 建置期 / 人員異動時 | 系統管理 | 設定員工的查詢權限(可查哪些機構、哪些人) | `CRMM001` | 員工要先在 `COD009` 存在 |
| 每期開始 | 名單管理 | 依規則產生直銷分配客戶名單,或上傳 CSV 名單 | `CRMB001` | 該結算日所有基金都要已結帳 |
| 名單產生後 | 名單管理 | 把名單在單位之間調撥 | `CRMB002` | 名單要先存在 |
| 名單產生後 | 主管 | 把名單指派到業務員 | `CRMB003` | 名單要先存在 |
| 追蹤期間 | 業務員 | 填聯絡結果、再聯絡日期 | `CRMB004` | 名單要先指派到自己 |
| 追蹤期間 | 業務員 / 主管 | 查自己(或所屬單位)的名單 | `CRMI001` | `CRM001A` / `CRM002A` 要先設好 |
| 平時 | 客服 | 建立 / 維護潛在客戶,記錄通話與索取資料 | `CRMM003` | — |
| 不定期 | 客服主管 | 合併重複的潛在客戶 | `CRMB005` | 潛在客戶要先存在 |
| 期末 | 全體 | 出各式指派與追蹤報表、潛在客戶報表 | `CRMR001`–`CRMR008` | 版控外的 SP 決定 |

**假設**:「期」的長度。依據是 `CRM007A` 的 PK 用 `ASSIGN_NO`(分配序號)而不是日期,而三支 B 畫面的預設值都取「最新一期」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:368-373`)。實際週期要問使用者。

## 2. 資料模型

```text
[圖] CRM 十張表的主明細關係、主鍵組成，以及外部唯讀表
圖中文字:CRMM003 的一主四明細（兩組對稱結構） / CRM003A〔共用〕 / PK PR_NO · 69 欄 / CRM006A / +CALLIN_DATE+SRNO / CRM0061A / 再加 CALLIN_CODE / CRM004A / +REQ_DATE+SRNO / CRM0041A / 再加 REQ_DATA_CODE / CRM006A_HIS CRM004A_HIS / 結果集 非實體表 / CRMM001 多筆版：兩張表都算主檔，沒有明細概念 / CRM001A / PK 員工+機構別+機構 / CRM002A / 再加 INQ_EMP_NO（ALL） / CRM001A_OPTION / 勾選用 來源 OFD068A / CRM002A_OPTION / 勾選用 來源 COD009 / 單表：沒有明細也沒有主明細關係 / CRM008A / PK 四欄 · CRMM002 / CRM004 / PK CUS_LV · vdb 名 CRMM004 / CRM007A / PK ASSIGN_NO+BF_NO / 無 M 畫面 / 四眼欄位有但不走四眼 / 外部唯讀（join 進來，不屬本模組） / COD009 COD006A / 員工／代碼說明 / OFD002 OFD068A / 部門／銷售機構 / OFD081A OFD081V / 基金 兩支各用一個 / BMS001A_V01 TMK_BF_V / SAL051 OFD303A CTL014
```

*圖:圖 2 資料模型。橘框=主檔；橘虛框=取數被限制或不走四眼；灰虛框=非實體結果集；黑框=外部唯讀表。實線箭頭=主明細（同一次 EVA 一起送審）；虛線=同一支畫面內的弱關聯。CRM004A／CRM0041A 的取數被加了 WHERE 1=2，維護頁永遠查不到。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

`xTableMapping` 是全庫「實體表」清單的唯一來源(`architecture.md §2.2`),但 CRM 這邊有兩種寫法,掃描器只認得其中一種(§0.2)。

| 畫面 | PO 基底 | 主檔宣告 | 明細宣告 | 錨點 |
|---|---|---|---|---|
| `CRMM001` | `BaseMultiRowEVADaoPO` | `MasterTable.Add("CRM001A")` **與** `MasterTable.Add("CRM002A")` | **無此概念** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `CRMM002` | `BaseMultiRowEVADaoPO` | `MasterTable.Add("CRM008A")` | **無此概念** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:40` |
| `CRMM003` | `BaseEVADaoPO` | `CRM003A` | `CRM006A`、`CRM0061A`、`CRM004A`、`CRM0041A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:65-71` |
| `CRMM004` | `BaseEVADaoPO` | `CRM004`(vdb 表名是 `CRMM004`) | **無** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:44` |
| `CRMI001` | **無基底**(裸 DAO) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:36`、`:44`(唯一一行是註解) |
| `CRMB001` | `BaseEVADaoPO`(但完全沒用到四眼) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:36`、`:48-50` |
| `CRMB002`–`CRMB005` | **無基底**(裸 DAO) | 無宣告 | 無宣告 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:36` |

三件要記住的:

1. **多筆版沒有明細表。**`BaseMultiRowEVADaoPO` 的 `MasterTable` 是 `List<xTableMapping>`,`DetailTable` 這個概念不存在(`architecture.md §3.9`)。所以 `CRMM001` 把 `CRM001A` 與 `CRM002A` **兩張都登記成主檔**,靠 `MasterPKey` 只填 `EMP_NO` 來讓「同一員工的所有列」被當成一批處理(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:51`)。

2. **`CRMM001` 為此付出三個覆寫的代價**(§4.1):`Add` 自己補 `CRM002A` 的 INSERT、`IsChangedByData` 只對第一張表做樂觀鎖、`ApproveDelete` 自己判存在性避免跑多次。三個覆寫的註解都直白寫了原因,是全模組最誠實的一段程式碼。

3. **`CRMM003_PO` 有兩行被註解的明細宣告**:`CRM0061A_HIS` 與 `CRM0041A_HIS`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:69`、`:72`)。這兩張「歷史表」在現行程式裡完全不存在,歷史資料改用 `CRM006A_HIS` / `CRM004A_HIS` 這兩個**非實體結果集**承接(§2.3)。

### 2.2 主鍵與四眼欄位

主鍵有兩個獨立來源:xsd 的 `msdata:PrimaryKey` 與 `App.config` 的 `pkey`。CRM 這邊**四支 M 畫面有三支不一致**。

| 表 | 主鍵(xsd) | 主鍵(`App.config`) | 一致? | xsd 錨點 |
|---|---|---|---|---|
| `CRM001A` | `EMP_NO` + `AGENT_ID` + `AGENT_CODE` | `EMP_NO` | ✘(設定檔少兩欄) | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd` |
| `CRM002A` | `EMP_NO` + `AGENT_ID` + `AGENT_CODE` + `INQ_EMP_NO` | (未宣告) | — | 同上 |
| `CRM008A` | `AGENT_BELONG_TYPE` + `AGENT_TYPE` + `AGENT_ID` + `AGENT_CODE` | 同左,四欄齊 | ✔ | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM002Model.xsd` |
| `CRM003A` | `PR_NO` | `PR_NO` | ✔ | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| `CRM006A` | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` | (未宣告) | — | 同上 |
| `CRM0061A` | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` + `CALLIN_CODE` | (未宣告) | — | 同上 |
| `CRM004A` | `PR_NO` + `REQ_DATE` + `REQ_SRNO` | (未宣告) | — | 同上 |
| `CRM0041A` | `PR_NO` + `REQ_DATE` + `REQ_SRNO` + `REQ_DATA_CODE` | (未宣告) | — | 同上 |
| `CRM004` | `CUS_LV` | `CUS_LV`(但表名寫成 `CRMM004`) | ✔(表名不同) | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM004Model.xsd` |
| `CRM007A` | `ASSIGN_NO` + `BF_NO` | (無 M 畫面,沒有設定) | — | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |

**`CRM001A` 的 `pkey` 只寫 `EMP_NO` 是刻意的,不是漏。**多筆版用 `MasterPKey` 定義「一批」的範圍,而 `IsExistByMasterPK` 就是靠它判斷(`architecture.md §3.9`);`CRMM001_PO.ApproveDelete` 明確用它來避免同一批跑多次(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:165`)。

四眼欄位(那 13 欄,清單見 `architecture.md §3.5`)的齊備狀況:

| 表 | 13 欄齊? | 中文名 | 說明 |
|---|---|---|---|
| `CRM003A` | ✔ | **全部有** | 最完整的一張,連 `DATAFLAG` 都有「資料異動碼」 |
| `CRM006A` `CRM0061A` `CRM004A` `CRM0041A` | ✔ | **全部有** | 四張明細一致 |
| `CRM001A` `CRM002A` | ✔ | **全部有** | 同上 |
| `CRM008A` | ✔ | **一個都沒有** | 欄位存在但 `msdata:Caption` 全空 |
| `CRM004` | ✔ | **一個都沒有** | 同上 |
| `CRM007A` | ✔ | **全部有,但有一個是錯的** | `STATUS` 的 Caption 寫成「資料識別碼」(那是 `DATAID` 的名字);`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |

**結論:10 張表全部有完整四眼欄位,而且 8 張有中文名——比 CAS(10 張只有 2 張有)好得多。**但要注意兩個共通的抄寫錯:`REJECTDATE` 的 Caption 在 `CRMM003Model.xsd` 的五張表裡全部寫成「資料退回**者**」(應為「資料退回日期」),`CRMM001Model.xsd` 那兩張則是對的。

`DATAFLAG` 每張表都有,型別一律 `xs:base64Binary`,是樂觀鎖唯一比對的欄位,**業務欄位一個都不進比對**(`architecture.md §3.6`)。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

以下中文名一律取自 xsd 的 `msdata:Caption`,**沒有自己翻譯**。空白代表該 xsd 沒有填。四眼的 13 欄 + `DATAID` + `DATAFLAG` 每張表都有,除特別註記外不重複列。

#### `CRM003A` — 潛在客戶主檔(69 欄,`CRMM003` 主檔)〔共用〕

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK,取號見 §4.3 |
| `USAGE` | 用途別 | string(6) | **切 CRM / CAS 兩個世界的那一欄**(§8.1) |
| `BF_NO` | 受益人戶號 | decimal | 已開戶才有 |
| `EMP_NO1` | 業務員員工代碼 | string(10) |  |
| `ID_NO` | 統一編號 | string(10) |  |
| `PR_NAME` | 潛在客戶姓名 | string(100) | 走 `AddNVarCharColumns` 宣告為 NVARCHAR |
| `HM_TEL_AREA` | 公司電話區域碼 | string(4) | **Caption 抄錯**,實際是住家 |
| `HM_TEL` | 住家電話 | string(20) |  |
| `OF_TEL_AREA` / `OF_TEL` | 公司電話區域碼 / 公司電話 | string(4) / string(20) |  |
| `AUTO_FAX_YN` | 自動傳真電話否 | string(6) | 對應 UI 已註解 |
| `FAX_TEL_AREA` / `FAX_TEL` | 傳真電話區域碼 / 傳真電話 | string(4) / string(20) |  |
| `CELL_PHONE` | 行動電話 | string(20) |  |
| `EMAIL` | (無中文名) | string(60) | UI 有格式檢核 |
| `CNT_PERSON` | 聯絡人 | string(24) |  |
| `ADDR_CODE1` … `MAIL_FLOOR` | 通訊地址區分碼 / 郵遞區號 / 通訊中文地址 / 縣市 / 行政區域 / 里名 / 鄰名 / 路名 / 幾巷 / 幾弄 / 起號 / 迄號 / 之幾 / (樓層無名) | string | 共 15 欄,`MAIL_ADDR` 走 NVARCHAR;**14 欄的回填程式全被註解**(§4.3) |
| `MEMO` | 備註說明 | string(500) |  |
| `CUST_CLASS` / `CUST_CLASS1` / `CUST_CLASS2` | 客戶等級代碼 / 總行等級代碼 / 分行等級代碼 | string(7) |  |
| `BF_SOURCE_CODE` | 潛在客戶來源代碼 | string(7) |  |
| `DES_MAKER` | 決策者 | string(24) |  |
| `DM_CODE` / `DM_EMAIL` | DM寄發碼 / 寄發廣告EMAIL | string(6) | **2020-03-30 起兩個下拉都被移除**(§4.3) |
| `REJ_SELL_CHK` / `REJ_SELL_DOC` / `REJ_SELL_WEB` / `REJ_SELL_PHONE` | 拒絕行銷 / 拒絕書面行銷 / 拒絕網路行銷 / 拒絕電訪行銷 | string(6) | **四個勾選框在編輯模式一律 `Enabled = false`**(§4.3) |
| `CUST_STYLE` / `CUST_STYLE_DESC` | (無中文名) | string(7) / string(60) |  |
| `AREA_CODE` / `DEPT_CODE` | 區域別 / 組別 | string(6) |  |
| `SOP_CLASS` | SOP等級代碼 | string(7) |  |
| `POSITION_DESC` / `SOURCE_DESC` | 職稱說明 / 客戶來源說明 | string(20) |  |
| `CUST_TYPE` | 客戶類別代碼 | string |  |
| `SEND_INFO_YN` | 發文通知 | string(6) |  |
| `TEL_STAFF` / `OUTBND_CODE` / `OUTBND_DESCRP` | 電訪人員 / OutBound項目 / OutBound項目說明 | string | **不是 `CRM003A` 的實體欄位**,是 join `TMK_BF_V` 帶回來的(§4.3) |

#### `CRM006A` — 通話紀錄表頭(21 欄,`CRMM003` 明細)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK |
| `CALLIN_DATE` | 通話日期 | string(8) | PK,`YYYYMMDD` 字串 |
| `CALLIN_SRNO` | 批次 | decimal | PK,同日第幾通 |
| `BF_NO` | 受益人戶號 | decimal |  |
| `READY_YN` | 完成碼 | string(6) |  |
| `COMMENT1` | 通話記錄備註 | string(500) |  |

#### `CRM0061A` — 通話種類明細(20 欄,`CRMM003` 明細)

比 `CRM006A` 多一欄 `CALLIN_CODE`(通話種類代碼小類,`string(7)`,入 PK),其餘同上但沒有 `READY_YN` / `COMMENT1`。**一通電話可以勾多個種類,所以才拆表。**

#### `CRM004A` — 索取資料表頭(27 欄,`CRMM003` 明細)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `PR_NO` | 潛在客戶序號 | string(11) | PK |
| `REQ_DATE` | 索取日期 | string(8) | PK |
| `REQ_SRNO` | 批次 | decimal | PK |
| `DOC_DVLY_ID` | 寄送方式 | string(6) |  |
| `POST_WAY` | 郵寄方式 | string(6) |  |
| `REQ_QTY` | 需求數量 | decimal |  |
| `FAX_TEL_AREA` / `FAX_TEL` / `EMAIL` | 傳真電話區域碼 / 傳真電話 / (無中文名) | string |  |
| `LABEL_PRINT` | 標籤列印碼 | string(6) |  |
| `PRINT_YN` | 標籤列印否 | string(6) | **由 `CRMR008` 的列印動作寫回**(§7.4) |

#### `CRM0041A` — 索取種類明細(20 欄,`CRMM003` 明細)

比 `CRM004A` 少掉全部業務欄位,多一欄 `REQ_DATA_CODE`(需求資料種類代碼,`string(7)`,入 PK)。與通話那組完全對稱。

#### `CRM001A` — 員工可查機構(20 欄,`CRMM001` 主檔之一)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `EMP_NO` | 員工代碼 | string(10) | PK;`MasterPKey` 只有這一欄 |
| `AGENT_ID` | 銷售機構別 | string(6) | PK |
| `AGENT_CODE` | 銷售機構代碼 | string(9) | PK |
| `EMP_NAME` | 員工姓名 | string | join `COD009` 帶回,非實體欄位 |
| `AGENT_SHNM` | 銷售機構名稱 | string | join `OFD068A` 帶回,非實體欄位 |

#### `CRM002A` — 員工可查員工(19 欄,`CRMM001` 主檔之二)

同 `CRM001A` 的三個 PK 欄再加 `INQ_EMP_NO`(員工代碼,`string(10)`)。**注意 Caption 是對調的**:`EMP_NO` 的 Caption 寫「可查詢員工代碼」、`INQ_EMP_NO` 的 Caption 寫「員工代碼」,但程式裡 `EMP_NO` 是「擁有權限的人」、`INQ_EMP_NO` 是「被查的人」(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:294-305` 的 `A.EMP_NO = '{0}'` 配 `B.INQ_EMP_NO`)。**以程式為準,Caption 這兩欄反了。**

`INQ_EMP_NO` 有一個保留值 **`'ALL'`**,代表「該機構底下全部員工都看得到」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:228`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:488`)。

#### `CRM008A` — 銷售機構部門歸屬(21 欄,`CRMM002` 主檔)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `AGENT_BELONG_TYPE` | 部門歸屬種類 | string | PK;下拉來源代碼 `445` |
| `AGENT_TYPE` | 部門歸屬類別代碼 | string | PK |
| `AGENT_TYPE_NM` | 部門歸屬類別名稱 | string | 由類別代碼的顯示文字自動帶入 |
| `AGENT_ID` | 銷售機構區分碼 | string | PK;下拉來源代碼 `062` |
| `AGENT_CODE` | 銷售機構代碼 | string | PK;有 `'ALL'` 保留值 |
| `AGENT_SHNM` | 銷售機構中文簡稱 | string | join `OFD068A` 帶回,非實體欄位 |

#### `CRM004` — 客戶分級參數(34 欄,`CRMM004` 主檔;vdb 表名 `CRMM004`)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `CUS_LV` | 客戶等級 | string | PK |
| `HASBF_NO` | 是否開戶 | string | `Y` / `N` |
| `HAS_MF` / `HAS_N_MF` / `HAS_PER` | (無中文名) | int | 0/1 旗標:有無貨幣型 / 非貨幣型 / 比率條件 |
| `MF_AUM_S` / `MF_AUM_E` | 貨幣結餘起 / 迄(萬元) | int | **`-1` 是「未填」的哨兵值**(§4.4) |
| `N_MF_AUM_S` / `N_MF_AUM_E` | 非貨幣結餘起 / 迄(萬元) | int | 同上 |
| `MF_PER` / `N_MF_PER` | 貨幣庫存比 / 非貨幣庫存比 | int |  |
| `VISIT_CNT` / `CALL_CNT` / `TOT_CNT` | 應親訪次數 / 應電訪次數 / 應完成總次數 | int |  |
| `NEED_CNT` | (無中文名) | int | 0 代表不需計次,`FREQ` 顯示為空 |
| `FREQ_NUM` / `FREQ_UNIT` / `FREQ` | (無) / (無) / 計算頻率 | int / string / string | `FREQ` 是 `DECODE` 出來的顯示欄,非實體欄位 |
| `MEMO` | 備註 | string | UI 上已註解不用 |

#### `CRM007A` — 直銷分配客戶名單(56 欄,`CRMI001` / `CRMB001`–`CRMB004` 共用)

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `ASSIGN_NO` | 分配序號 | string | PK,一期一個 |
| `BF_NO` | 受益人戶號 | double | PK |
| `EXE_DATE` | 執行日期 | string | 名單產生的結算日 |
| `RULE_CODE` | 規則編號 | string | `1`–`6`,`6` 是手動上傳 |
| `SOURCE_CODE` | 資料來源 | string | 下拉來源 `CTL014` 的 `442` |
| `LAST_TRN_SOURCE` / `LAST_TRN_DATE` / `LAST_FUND_ID` | 最後交易來源 / 日期 / 基金代碼 | string |  |
| `LAST_AGENT_ID` / `LAST_AGENT_CODE` / `LAST_AGENT_CODE1` | 最後交易銷售機構區別 / 代碼 / 單位1 | string | `LAST_AGENT_CODE1` 在 CSV 上傳時被塞進 `LAST_AGENT_CODE` 的值(§6.2) |
| `LAST_EMP_NO` | 最後交易員工代碼 | string |  |
| `TOT_ALLOT_AMT` / `BAL_AMT` | 單筆最高申購金額 / 庫存金額 | decimal | 由上游算好寫進來 |
| `LAST_DEPT_TYPE` / `BASE_DEPT_TYPE` | 最後交易單位類別 / 指派交易單位類別 | string |  |
| `ASSIGN_DATE1` / `ASSIGN_USER_ID1` / `ASSIGN_DEPT_NO1` / `ASSIGN_EMP_NO1` | 本次指派日期 / 指派者 / 單位代碼 / 業務代碼 | string | **調撥時整組往 `*2` 推**(§6.3) |
| `ASSIGN_DATE2` / `ASSIGN_USER_ID2` / `ASSIGN_DEPT_NO2` / `ASSIGN_EMP_NO2` | 前次指派日期 / 指派者 / 單位代碼 / 業務代碼 | string |  |
| `SPC_YN` | 特殊名單 | string | `Y` / `N`,查詢時用 `NVL(...,'N')` |
| `LAST_ASSIGN` | 前序號已指派 | string | 本模組無任何程式寫它 |
| `RESULT` | 有無意願申購 | string | `CRMB004` 寫入 |
| `NEXT_CONTACT_DATE` / `CONTACT_CODE` / `CONTACT_COMM` | 再聯絡日期 / 聯絡結果代碼 / 聯絡結果說明 | string | `CRMB004` 寫入 |

另有 9 個 join 帶回來的顯示欄(`BF_NAME`、`FUND_SH_NM`、`AGENT_SHNM`、`SOURCE_CODE_DESCRP`、`LAST_EMP_NAME`、`ASSIGN_DEPT_NO1_DESCRP`、`ASSIGN_DEPT_NO2_DESCRP`、`ASSIGN_EMP_NAME1`、`ASSIGN_EMP_NAME2`、`ASSIGN_USER_NAME1`、`ASSIGN_USER_NAME2`),**不是實體欄位**。

#### 非實體結果集(不是資料表)

| 名稱 | 用途 | 定義在 | 怎麼填 |
|---|---|---|---|
| `CRM001A_OPTION` | `CRMM001` 的全機構勾選清單 | `CRMM001Model.xsd` | `SELECT 0 AS ISCHECK, … FROM OFD068A`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:318-324` |
| `CRM002A_OPTION` | `CRMM001` 的全員工勾選清單(含 `ALL` 那一列) | 同上 | `dual` 併 `COD009` 的 `UNION`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:331-355` |
| `OUTBOUND` | `CRMM003` 的電訪人員帶值 | `CRMM003Model.xsd` | join `TMK_BF_V` / `COD006A` / `TA_AA_USER`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:638-649` |
| `CRM006A_HIS` | `CRMM003` 的通話歷史(6 欄) | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:856-870` |
| `CRM004A_HIS` | `CRMM003` 的索取歷史(12 欄) | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:872-892` |
| `EMP_INFO` | `CRMB003` / `CRMB004` / `CRMR001` / `CRMR002` 的登入者資訊與欄位鎖定旗標 | `CRMB003Model.xsd` 等 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:286-314` |
| `OutPutData` | `CRMB001` 的「產出客戶名單」Excel 資料 | `CRMB001Model.xsd` | `S_TA_CRMB001_GET`;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:368-377` |
| `CRMB005_1` | `CRMB005` 的重複潛在客戶清單(12 欄) | `CRMB005Model.xsd` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:66-107` |
| `CRMR003` `CRMR004` `CRMR005` `CRMR006_1` `CRMR006_2` `CRMR007_1` `CRMR008_1` `CRMR008_2` | 八支報表的結果集形狀 | 各 `CRMRnnnModel.xsd` | SP 的 RefCursor(§7) |

### 2.4 與其他模組共用的表

| 表 | 誰也在用 | 讀 / 寫 | 詳見 |
|---|---|---|---|
| `CRM003A` | CAS(`CASM001` 當主檔,增刪改)、TMK(`TMKM001` / `TMKM002` 唯讀 join) | CAS 寫、TMK 讀 | §8.1 |
| `CRM006A` `CRM0061A` | TMK(`TMKM001` / `TMKM002` 唯讀)、OFD(`OFDI011` 唯讀) | 只有 CRM 寫 | §8.3 |
| `CRM004A` `CRM0041A` | 本模組的 `CRMR008` 會 UPDATE `PRINT_YN` | 只有 CRM 寫 | §7.4 |
| `CRM001A` `CRM002A` | **共用 PO** `BasicCRM_PO`、CLS(`CLSM001` / `CLSM002` / `CLSR001` / `CLSR002`)、DSM(`DSMI001` / `DSMR007`)、OFD(`OFDI011`) | 只有 `CRMM001` 寫 | §8.2 |
| `CRM007A` | **共用 PO** `BasicCRM_PO`、共用控件 `ucAssignDeptNo` / `ucAssignEmpNo`、OFD(`OFDI011`) | 只有 CRM 寫 | §8.4 |
| `CRM008A` | **全庫只有 `CRMM002`** | 只有 CRM | — |
| `CRM004` | **全庫只有 `CRMM004`** | 只有 CRM | — |

外部唯讀表(join 進來取說明用,本模組從不寫入):`COD009`(員工)、`COD006A`(代碼說明)、`OFD002`(部門)、`OFD068A`(銷售機構)、`OFD081A` 與 `OFD081V`(基金)、`CTL014`(下拉代碼)、`BMS001A_V01`(受益人檢視表)、`TMK001A` 與 `TMK_BF_V`(電訪)、`SAL051`(直銷職級)、`OFD303A`(基金結帳控制)、`TA_AA_USER` 與 `AA_USER`(平台使用者)。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`

`CRM003A` / `CRM006A` / `CRM0061A` / `CRM004A` / `CRM0041A` / `CRM001A` / `CRM002A` / `CRM008A` / `CRM004` 的 `STATUS` 由框架的 `EVAStatusCode` 常數決定,值域見 `architecture.md §3.10`,CRM 內沒有任何一支程式寫死它。

**唯一的例外是 `CRM007A`,它的 `STATUS` 被寫死成 `'301'` 兩次:**

| 在哪 | 寫法 | 錨點 |
|---|---|---|
| `CRMI001_PO` 查詢時設 `DefaultValue` | `STATUSColumn.DefaultValue = "301"` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480` |
| `CRMB001_PO` 的 CSV 上傳 INSERT | SQL 裡直接寫 `'301'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:163` |

CAS 那邊 `CASB001` 也把 `CLS002A` 的狀態直接寫成 `'301'`(`cas.md §8.3`),**兩個模組寫死同一個值,顯然 `'301'` 就是「已覆核 / 正式生效」**。這是**假設**,依據是兩個模組獨立寫死同一個值,而且 `CRMI001` 把它當成「查出來的資料一律視為已生效」用。要確認得反編譯 `EVAStatusCode` 或直接查資料庫。

**`CRM007A` 從來不走四眼流程。**它的 13 個四眼欄位在 `CRMI001_PO` 被一次設成「同一個人輸入 + 驗證 + 覆核」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480-492`),`REJECTDATE` 的預設值是 `1900/1/1`。這是「有四眼欄位但沒有四眼流程」的典型。

#### 本模組自訂的旗標值

| 值域 | 用在哪 | 語意(反推) | 錨點 |
|---|---|---|---|
| `USAGE` = `'1'` | `CRM003A` | CRM / TMK 的世界(CAS 用 `'3'`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `RULE_CODE` = `'1'`–`'6'` | `CRM007A` | 名單產生規則;`'6'` 是「依條件篩選,手動上傳」 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:60`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.Designer.cs:220` |
| `EXECUTE` = `'1'` / `'2'` | `CRMB001` 的動作別 | `1` 產生、`2` 刪除 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128` |
| `SAL_CD` = `'A'` / `'B'` / `'C'` / `'D'` | `SAL051`(外部) | 直銷主管 / 組主管 / 業務員 / 助理 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-348`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:282`〔客戶特定〕 |
| `SORT_ORDER` = `'0'`–`'5'` | `CRMB002`–`CRMB004` 的排序 | 機構+員工 / 受益人類別 / 戶號 / 地址 / 庫存金額 / 最後交易日 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` |
| `REPORT_TYPE` = `'1'` / `'2'` / 其他 | `CRMR006` | 前兩者進 `CRMR006_1`,其餘進 `CRMR006_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:61-63` |
| `REPORT_TYPE` = `'0'` / 其他 | `CRMR008` | `0` 走 `S_TA_CRMR008_GET_1`,其餘走 `_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:57-60` |
| `MERGE_TYPE` = `'1'` / `'2'` | `CRMB005` | 姓名+通訊地址相同 / 姓名+統一編號相同 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:86-107` |
| `INQ_EMP_NO` = `'ALL'` | `CRM002A` | 該機構底下全部員工 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337` |
| `AGENT_CODE` = `'ALL'` | `CRM008A` | 該機構別底下全部機構 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:124` |

#### 代碼分類碼(`CODE_SORT` / `SOURCETYPE`)

| 分類碼 | 屬於 | 用途(取自程式上下文) | 錨點 |
|---|---|---|---|
| `P5` | `COD006A` | OutBound 項目說明 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:647` |
| `1C` | `COD006A` | 通話種類代碼小類 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:868` |
| `11` | `COD006A` | 需求資料種類代碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:890` |
| `442` | `CTL014` | 資料來源(`SOURCE_CODE`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:101` |
| `600` | `CTL014` | 計算頻率單位(`FREQ_UNIT`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:56` |
| `062` | 下拉(`GetDropDownDataSrc`) | 銷售機構區別碼 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:72` |
| `445` | 下拉(`GetDropDown9iDataSrc` / `GetDropDownDataSrc`) | 部門歸屬種類 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335-336` |

`438`(DM寄發碼)與 `439`(寄發廣告EMAIL)在 `CRMM003` 是**被註解掉的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:155`、`:157`),註解寫「2020.03.30 移除DM寄發碼與寄發廣告EMAIL的選項 by hanna 9000008774」——欄位還在表上,只是不再能從畫面設定。

## 3. 畫面清冊

畫面中文名 ATLAS 沒有放進版控(`architecture.md §6`),以下「中文名」欄的來源分三種:**報**=程式裡的報表名字串、**窗**=彈出視窗的 `this.Text`、**推**=由欄位與標籤推測。18 支畫面**六層全齊**。

### 3.1 維護 M

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMM001` | 員工銷售機構查詢權限維護 | 窗+推 | 齊 | `CRM001A` `CRM002A`(兩張都算主檔) | 無 | `BaseMultiRowEVADaoPO` | — | — |
| `CRMM002` | 銷售機構部門歸屬維護 | 推 | 齊 | `CRM008A` | 無 | `BaseMultiRowEVADaoPO` | — | — |
| `CRMM003` | 潛在客戶維護 | 窗+推 | 齊 | `CRM003A`〔共用〕 | `CRM006A` `CRM0061A` `CRM004A` `CRM0041A` | `BaseEVADaoPO` | — | — |
| `CRMM004` | 客戶分級參數維護 | 推 | 齊 | `CRM004`(vdb 名 `CRMM004`) | 無 | `BaseEVADaoPO` | — | — |

### 3.2 查詢 I

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMI001` | 直銷分配客戶名單查詢 | 推 | 齊 | `CRM007A`(只在 SQL 字串裡) | 無 | **無基底**(裸 DAO) | `F_TA_GET_EMPS` | — |

### 3.3 批次 B

| 代號 | 中文名 | 來源 | 六層 | 主表 | 明細 | PO 基底 | SP / Fn | rpt |
|---|---|---|---|---|---|---|---|---|
| `CRMB001` | 直銷分配客戶名單產生 / 刪除 / 上傳 | 推 | 齊 | `CRM007A` | 無 | `BaseEVADaoPO`(未用四眼) | `S_TA_CRMB001_EXCUTE`(**呼叫被註解**)、`S_TA_CRMB001_GET` | — |
| `CRMB002` | 指派名單單位調撥 | 推 | 齊 | `CRM007A` | 無 | 無基底 | — | — |
| `CRMB003` | 指派名單業務員指派 | 推 | 齊 | `CRM007A` | 無 | 無基底 | `F_TA_GET_EMPS` | — |
| `CRMB004` | 指派名單聯絡結果登錄 | 推 | 齊 | `CRM007A` | 無 | 無基底 | — | — |
| `CRMB005` | 重複潛在客戶合併 | 推 | 齊 | `CRM003A`〔共用〕 | 無 | 無基底 | `S_TA_CRMB005_EXCUTE` | — |

### 3.4 報表 R

| 代號 | 中文名 | 來源 | 六層 | 取數來源 | rpt |
|---|---|---|---|---|---|
| `CRMR001` | 指派單位明細表 | 報 | 齊 | `S_TA_CRMR001_GET` | `CRMR001RPS` |
| `CRMR002` | 指派業務員明細表 | 報 | 齊 | `S_TA_CRMR002_GET` | `CRMR002RPS` |
| `CRMR003` | 指派名單追蹤彙總表-By單位別 | 報 | 齊 | `S_TA_CRMR003_GET` | `CRMR003RPS` |
| `CRMR004` | 指派名單追蹤彙總表-By業務員別 | 報 | 齊 | `S_TA_CRMR004_GET` | `CRMR004RPS` |
| `CRMR005` | 指派名單追蹤明細表-By業務員別 | 報 | 齊 | `S_TA_CRMR005_GET` | `CRMR005RPS` |
| `CRMR006` | 指派名單聯絡結果統計表 / 明細表(三選一) | 報 | 齊 | `S_TA_CRMR006_GET` | `CRMR006RPS1` `CRMR006RPS2` `CRMR006RPS3` |
| `CRMR007` | 客戶通話記錄明細表 | 報 | 齊 | `S_TA_CRMR007_GET` | `CRMR007RPS1` |
| `CRMR008` | 客服潛在客戶索取資料明細表 / 資料表(二選一) | 報 | 齊 | `S_TA_CRMR008_GET_1` `S_TA_CRMR008_GET_2` | `CRMR008RPS1` `CRMR008RPS2` |

### 3.5 一眼看出差別的五件事

1. **五支 B + 一支 I 的 PO 有五種不同的寫法。**`CRMB001_PO` 繼承 `BaseEVADaoPO` 卻一個四眼事件都沒掛(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:48-50` 是空建構子);`CRMB002`–`CRMB005` 與 `CRMI001` 完全沒有基底,自己 `new Database("TA", ...)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:40`)。

2. **兩支 M 用多筆版、兩支用單筆版。**這決定了它們能不能有明細、樂觀鎖比什麼、`ApproveDelete` 會跑幾次(§2.1)。

3. **`CRMM004` 是全模組唯一在伺服器端擋資料的畫面**(`args.Cancel` + `args.CancelMsg`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:100-104`)。其餘所有卡控都在用戶端,繞過 UI 就沒有任何保護。

4. **`CRMI001` 與三支 B 的取數 SQL 有 90% 重複。**`CRMB002` / `CRMB003` / `CRMB004` 的 `Select` 是同一段 join 抄三份,差別只在 `CRMB003` 多掛了 `F_TA_GET_EMPS` 的權限限制、`CRMB002` 多了 `ASSIGN_DEPT_YN` 條件、`CRMB004` 多了一個 `TO_DATE` 顯示欄(§6.2)。

5. **八支報表 PO 的結構一模一樣**,差別只在 SP 名字與參數清單;只有 `CRMR006` / `CRMR008` 多了報表種類分支,`CRMR008` 多了一支寫入方法(§7)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] M 畫面從按鈕到四眼引擎的卡控順序，以及四支畫面各掛了哪些事件
圖中文字:① 用戶端：四支 M 的卡控都在這一層 / Before*ButtonClicked / Add/Modify/Delete/Search / validatorManager1 / 必填與格式 框架決定 / DoValidate() / M004 回傳語意相反 / Pxy 直呼 DB 檢核 / EXIST_EMP_NO IS_EXISTS / ② 回填：把主檔欄位寫進明細／勾選項目轉成資料列 / GetPageValue / M001 差異比對 M003 兩組明細 / SetMasterToDetail / 只有 CRMM002 有 / ProcessVDB / ViewVDB 過 Remoting / ③ 伺服端 Before*：唯一會擋資料的是 CRMM004 / BeforeAdd / M003 取 PR_NO 撞號重取 / BeforeSelect / 整條 SQL 換掉 / BeforeUpdate / M004 區間重疊 Cancel / SetDetailSrNo / 取號失敗寫 -1 進 PK / ④ EVA 引擎：CRMM001 覆寫了三個基底方法 / EVA 引擎 / 無原始碼 DLL 內 / Add 覆寫 / CRM002A 手寫 INSERT / IsChangedByData 覆寫 / CRM002A 樂觀鎖關掉 / ApproveDelete 覆寫 / 存在才做 避免跑多次 / ⑤ After*：只有 CRMM003 有，8 個掛點全是跳號一覽表 / CRMM003 / 8 個 After throw 空訊息 / CRMM001 CRMM002 / 只掛 Before* / CRMM004 / Before* + 伺服端卡控 / BeforeApproveDelete / M003 自己 DELETE 明細
```

*圖:圖 3 卡控與四眼順序。橘框=本模組寫的程式碼；黑框=框架 DLL（無原始碼，從呼叫端反推）；橘虛框=寫死值或會咬人的行為。除了 CRMM004 的區間重疊檢核之外，所有卡控都在用戶端，繞過 UI 就沒有任何保護。*

### 4.1 `CRMM001` — 員工銷售機構查詢權限維護

#### 用途(推測)

**設定「哪個員工可以查到哪些銷售機構、以及那些機構底下哪幾位員工的資料」。**這是一張純授權表,本模組自己完全不讀它——讀的人是共用 PO `BasicCRM_PO` 與 CLS / DSM / OFD 的畫面(§8.2)。

畫面結構:上方一個員工代碼欄(`custEMP_NO`),下方一個機構勾選 grid(`ugrdCRMM001`,資料來源是 `CRM001A_OPTION`)。雙擊某一列機構會開彈出視窗「員工銷售機構權限明細設定」(`CRMM001p0`),在裡面勾這個機構底下要開放哪幾位員工(`CRM002A_OPTION`)。

#### 多筆版的三個覆寫

這支是全模組技術上最特別的一支,因為 `BaseMultiRowEVADaoPO` 原本只支援「一張主表、多筆列」,而這裡要處理兩張表:

| 覆寫 | 為什麼 | 做了什麼 | 錨點 |
|---|---|---|---|
| `BeforeAdd` | 底層對第二張表下 INSERT 會噴 `ORA-01008: not all variables bound`(註解原話) | `args.TableName` 不是第一張表就 `args.Cancel = true`,整段跳過 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:70-78` |
| `Add` | 承上,`CRM002A` 的 INSERT 要自己寫 | 手寫 18 欄的 INSERT,逐列綁參數;**四眼欄位全部抄主檔第一列的值** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:86-137` |
| `IsChangedByData` | 兩張表都做樂觀鎖會比兩次 | 只在 `dbTableName == MasterTable[0]` 時做,其餘直接回 `false` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:146-152` |
| `ApproveDelete` | 主檔多筆會讓底層跑很多次 | 先用 `IsExistByMasterPK` 判斷還在不在,不在就直接回 `true` 忽略 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:160-169` |

**後果要記住三條:**

- `CRM002A` 的樂觀鎖是**關掉的**(`IsChangedByData` 對它一律回 `false`)。兩個人同時改同一個員工的可查員工清單,後存的直接蓋掉前存的,沒有「資料已被您異動」。

- `CRM002A` 的 `DATAID` 取自主檔第一列(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:110`),所以主明細確實綁在同一次 EVA 批次內。

- 手寫的那段 INSERT **把欄位名寫死在字串裡**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:93-101`),xsd 重生不會同步它。`CRM002A` 加欄位一定要手動改這段。

#### 主檔取數的「只取第一筆」把戲

查詢頁的結果 grid 一個員工只顯示一列,做法是在 SQL 裡用 `ROW_NUMBER() OVER (PARTITION BY EMP_NO ORDER BY CREATEDATE, UPDATEDATE, ENTRYDATE)` 取 `NUM = 1`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:252-258`)。

**排序欄位用的是三個日期而不是機構代碼**,所以「顯示出來的那一列是哪一個機構」是不確定的——同一批建立的列 `CREATEDATE` 會一樣。不過 grid 的顯示白名單只有 `EMP_NO` / `EMP_NAME` / `STATUS` 三欄(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:55`),使用者看不到差別。`CRMM002` 用同一招但排序多加了機構欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:90-91`),比較嚴謹。

#### 必填與存檔前檢核

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改 | 框架欄位必填(員工代碼) | 空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:529` |
| 按新增(限新增模式) | 機構 grid 至少勾一筆 | 一筆都沒勾 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:535-540` |
| 按新增(限新增模式,且前面都過) | 該員工是否已建過資料 | 已存在 | 阻擋(對話框) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:549-560` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:446-476` |
| 雙擊明細列 | 先跑一次 `DoValidate()`(不帶 `isFinish`) | 失敗 | 阻擋(不開視窗) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:190-194` |
| 雙擊明細列 | 該列沒勾選 | 沒勾 | 過濾(無提示,直接 `return`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:201-202` |

**「該員工已建過資料」這條會靜默放行。**`EXIST_EMP_NO` 的 `catch` 只做 `Result.Clear()`,**沒有再 `AddResultRow`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473`),UI 判斷的是 `Result.Count > 0 && Result[0].ReturnCode == true`,所以 SQL 一出錯 → `Count == 0` → 檢核通過 → 重複建檔(附錄 E.3)。

而且這段 SQL 是字串串接的:`string.Format(@"SELECT COUNT(*) FROM CRM001A WHERE EMP_NO = '{0}'", emp_no)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:452`),`emp_no` 來自畫面欄位。

#### 自動帶值(不是卡控,但會改資料)

| 行為 | 說明 | 錨點 |
|---|---|---|
| 勾了機構但沒勾任何員工 → 自動補一筆 `INQ_EMP_NO = 'ALL'` | 存檔前跑 `DoCheckDetail`,每個被勾的機構都檢查一次 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:478-490` |
| 開明細視窗時,原本沒有任何勾選 → 預設把 `ALL` 那列勾起來 | 只影響視窗內顯示 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:224-229` |
| 編輯模式下員工代碼欄鎖死 | `custEMP_NO.Enabled = false` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:499-507` |

**「自動補 ALL」的意思是:勾了機構卻不指定員工,等於開放該機構全部員工。**這是一個很容易被誤解成「沒設定就是沒權限」的預設值,實際上是相反的。

#### 編輯模式的差異比對

編輯模式不是整批砍掉重建,而是逐列比對(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:388-467`):原本有、現在沒勾 → `row.Delete()`;原本沒有、現在有勾 → `AddXxxRow`;兩邊都有 → 不動。`CRM002A` 的刪除有兩條路(主選項整個沒勾 / 明細單項沒勾),兩條都會 `Delete()`。

#### 四眼各階段附加動作

**一個都沒有。**`CRMM001_PO` 只掛了四個 `Before*`(`BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` / `BeforeAdd`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:46-49`),沒有任何 `After*`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | 員工代碼空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:529` |
| 新增前 | 機構至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:535-540` |
| 新增前 | 員工是否已建檔 | 已存在 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:549-560` |
| 新增前 | 同上,但 SQL 出錯 | 例外 | **記錄不擋**(靜默放行) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473` |
| 雙擊明細 | 該列未勾選 | 未勾 | 過濾(無提示) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:201-202` |
| 存檔前 | 機構有勾但員工零勾 | 成立 | **記錄不擋**(自動補 `ALL`) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:484-489` |
| 覆核刪除 | 該批已不存在 | 成立 | 過濾(直接回成功) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:165-166` |

### 4.2 `CRMM002` — 銷售機構部門歸屬維護

#### 用途(推測)

**把銷售機構歸類到「部門歸屬種類 × 部門歸屬類別」兩層分類底下。**主檔 `CRM008A` 的四個 PK 欄位就是這個結構:`AGENT_BELONG_TYPE`(種類,下拉代碼 `445`)+ `AGENT_TYPE`(類別代碼)+ `AGENT_ID`(機構別)+ `AGENT_CODE`(機構代碼)。

畫面是「一個分類 + 一個機構明細 grid」,但因為用的是多筆版,**grid 裡每一列其實都是一筆獨立的主檔**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:94`:`ugrdCRMM002.DataSource = ...UIView.CRM008A`)。查詢結果 grid 用 `ROW_NUMBER() ... PARTITION BY AGENT_BELONG_TYPE, AGENT_TYPE` 取第一筆,製造出「一個分類一列」的假象(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:89-95`)。

主檔語法那段還做了一件事:把 `AGENT_ID` 與 `AGENT_CODE` 兩欄硬寫成一個空白字元(`' ' AGENT_ID, ' ' AGENT_CODE`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:86-87`),讓查詢頁不顯示機構——**查詢與維護是兩套不同的 SQL,欄位語意不同**。

#### 必填與存檔前檢核

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改 | grid 的 `ActiveRow.Update()`(防快速鍵沒寫回) | — | 記錄不擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:125-126`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:138-139` |
| 按新增 / 修改 | 框架必填 + 明細至少一列 | grid 零列 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:175-178` |
| grid 輸入格 | 明細 PK 重複檢查 | 重複 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:229` |
| grid 插入列 / 更新列 | 明細 PK 必填 | 缺 PK | 阻擋 / 標紅 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:234-252` |
| 機構 Searcher 選完之後 | 同一部門歸屬底下機構不可重複 | 已存在 | 警示(清掉剛選的值) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:278-287` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:147-177` |
| 機構 Searcher 開啟前 | 該列要先選機構別 | 沒選 | 阻擋(取消開窗) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:305-308` |

**重複檢查也會靜默放行。**`IS_EXISTS` 的 `catch` 塞了訊息但回傳 `false`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176`),UI 判 `== true` 才擋,所以 SQL 出錯 = 允許重複(附錄 E.3)。

還有一個範圍不一致:`IS_EXISTS` 的條件只有 `AGENT_BELONG_TYPE` + `AGENT_ID` + `AGENT_CODE` 三欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:154-155`),**沒有 `AGENT_TYPE`**,但 PK 有四欄。也就是**同一個「部門歸屬種類」底下,不同「類別」不能放同一個機構**——比 PK 嚴格。這可能是刻意的(一個機構只能歸一類),但訊息寫的是「此類別已重複設定」,容易讓人以為只檢查同一類別。

#### 自動帶值

- 選了 `AGENT_TYPE` 之後,`AGENT_TYPE_NM` 自動填成該代碼的顯示文字(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:360-363`)。

- 改了某一列的 `AGENT_ID`,同列的 `AGENT_CODE` 與 `AGENT_SHNM` 會被清空(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:320-324`)。

- 存檔前 `SetMasterToDetail()` 把畫面上的三個分類欄位寫回 grid 每一列(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:185-194`)。**編輯模式下分類欄位是鎖死的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:107-108`),所以這個回填只在新增時有意義。

#### 四眼各階段附加動作

**一個都沒有。**只掛三個 `Before*`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:33-35`)。這支連 `BeforeAdd` 都沒有,因為 PK 全部由使用者輸入,不需要取號。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | 分類欄位空白 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:173` |
| 新增 / 修改前 | 明細至少一列 | grid 零列 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:175-178` |
| grid 編輯 | 明細 PK 重複 | 重複 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:229` |
| grid 編輯 | 明細 PK 必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:234-236` |
| 選機構後 | 同種類底下機構重複 | 重複 | 警示 + 清值 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:278-287` |
| 選機構後 | 同上,但 SQL 出錯 | 例外 | **記錄不擋**(靜默放行) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176` |
| 開機構 Searcher | 未先選機構別 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:305-308` |
| grid 內部錯誤 | 任何 grid error | 成立 | **過濾(無提示)**`e.Cancel = true` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:254-257` |

### 4.3 `CRMM003` — 潛在客戶維護

#### 用途(推測)

**建立與維護潛在客戶的基本資料,並且每一次通話、每一次寄送資料都留一筆紀錄。**一主四明細,四張明細其實是兩組對稱的結構:

| 組 | 表頭 | 種類明細 | 一次事件的識別 |
|---|---|---|---|
| 通話 | `CRM006A`(備註、完成碼) | `CRM0061A`(可複選的通話種類) | `PR_NO` + `CALLIN_DATE` + `CALLIN_SRNO` |
| 索取 | `CRM004A`(寄送方式、數量、傳真、Email、標籤) | `CRM0041A`(可複選的資料種類) | `PR_NO` + `REQ_DATE` + `REQ_SRNO` |

這支是全模組最大的一支(UI 1,910 行、PO 1,052 行、Ctl 344 行),也是唯一掛滿 8 個 `After*` 的一支。

#### 主檔取號與 `USAGE`

| 動作 | 做什麼 | 錨點 |
|---|---|---|
| `BeforeAdd` | `SerialNo.GetPR_NO()` 取號,`do…while (IsExistByData(...))` 撞號重取 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:210-214` |
| `GetPageValue`(新增時) | `USAGE` 硬寫 `"1"` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467` |
| `BuildMasterSQLString` | 查詢一律加 `WHERE CRM003A.USAGE = '1'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |

**CAS 的 `CASM001` 寫的是 `'3'`、查的也是 `'3'`,兩邊資料互不相見**(§8.1,與 `cas.md §8.2` 一致)。

`GetPageValue` 還會把登入者的員工代碼寫進 `EMP_NO1`,取法是「呼叫 `GetEMP_INFO` 回傳的字串用逗號切開取第 2 段」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:456`)——與 `CRMI001`、`CRMB003`、五支 R 畫面同一個寫法,是**位置取參數**的典型(附錄 E.6)。

#### 明細序號(批次)怎麼決定

同一天可以打好幾通電話,用 `CALLIN_SRNO` 區分。序號有**兩套實作**:

| 路徑 | 觸發 | 做法 | 錨點 |
|---|---|---|---|
| 畫面端 | 使用者改了通話日期 / 索取日期(`Leave` 事件),且處於「新增明細」狀態 | 打 `GetSRNO` 拿 `MAX(SRNO) + 1` 回填到畫面欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1383-1417` 配 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:729-785` |
| 伺服器端 | `BeforeAdd` / `BeforeUpdate` 的 `SetDetailSrNo` | 用 `intGetSRNO` 再算一次,**與畫面上那個不一致時整批覆寫** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:228-307`、`:1003-1050` |

兩套算的是同一件事,但**錯誤處理完全不同**:

- `GetSRNO`(畫面路徑)出錯時 `AddResultRow(false, 0, "取得批次失敗,請檢查")`,UI 會跳訊息並 `return`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1392-1397`)。

- `intGetSRNO`(伺服器路徑)出錯時**回傳 `-1`**,錯誤訊息塞進 `ref sErr`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047`)。而呼叫端 `SetDetailSrNo` **完全沒有檢查 `sErr`,也沒有檢查回傳值是不是 `-1`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:234-241`),`-1` 會被當成正常序號寫進 `CALLIN_SRNO` / `REQ_SRNO`。

**這是本模組最容易產生髒資料的一條:DB 一出問題,批次序號變成 `-1` 並且寫進 PK。**嚴重度高(附錄 E.3)。

#### 明細取數:兩張永遠查不到、兩張只看今天

`BuildDetailSQLString` 的四個分支:

| 明細 | 條件 | 效果 | 錨點 |
|---|---|---|---|
| `CRM006A` | `CALLIN_DATE = TO_CHAR(SYSDATE,'YYYYMMDD')`,且只取同日 `MAX(CALLIN_SRNO)` | **只看得到今天的最後一通** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:390-402` |
| `CRM0061A` | 同上 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:408-420` |
| `CRM004A` | **`WHERE 1=2 AND …`** | **永遠零筆** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436` |
| `CRM0041A` | **`WHERE 1=2 AND …`** | **永遠零筆** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:454` |

`1=2` 顯然是刻意加的(兩處都加在同一個位置、同一次改動),但**沒有任何註解說明為什麼**。合理的解釋是「索取資料頁改成一律新增,不載入既有資料」,因為畫面上的索取區塊搭配的是 `IsAddREQ` 狀態機。**這是假設**,依據是 `CRM006A` 那邊沒有 `1=2` 而且有 `CALLIN_DATE = SYSDATE` 的限制,兩者的設計意圖看起來是同一個方向,只是手段不同。要確認得問使用者「開啟舊客戶時索取資料頁應該顯示什麼」。

真正給使用者看的歷史資料走另一條路:`GetHistory_Call_Req` 撈進 `CRM006A_HIS` / `CRM004A_HIS` 兩個結果集,在 `ModifyDataLoad` 時由 `CallInHis()` 觸發(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1149`、`:1736`)。

**`GetHistory_Call_Req` 那段 SQL 是兩句 `SELECT` 用分號串起來的**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:870`、`:892`),然後一次 `LoadDataSet(cmd, ds, "CRM006A_HIS", "CRM004A_HIS")` 期待回兩張表(`:897`)。**Oracle 的 `ExecuteReader` 不接受分號分隔的多句 SQL**,這段**應該**會丟 `ORA-00911: invalid character`。這是**假設**——依據是 Oracle 的語法規則與 ODP.NET 不支援批次語句;無法在本機驗證。若假設成立,後果是「客戶歷史資料」永遠是空的,而且因為 `catch` 只塞了「取得客戶歷史資料失敗,請檢查」的訊息,使用者只看得到一句沒有細節的錯誤(附錄 E.7)。

#### 必填與存檔前檢核(`DoValidate`)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填 | — | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:279` |
| 新增 / 修改前 | 統一編號與客戶姓名不可同時空白 | 兩個都空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:283-287` |
| 新增 / 修改前 | 主檔 EMAIL 格式 | 有填且格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:290-294` |
| 新增 / 修改前 | 索取資料的 EMAIL 格式 | 有填且格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:296-300` |
| 新增 / 修改前 | 通話有異動時,通聯原因至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:303-314` |
| 新增 / 修改前 | 索取有異動時,資料種類至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:316-328` |
| 上述全過之後 | 通話日期大於系統日 | 成立 | **詢問**(選否就中止) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:341-352` |
| 上述全過之後 | 索取日期大於系統日 | 成立 | **詢問**(選否就中止) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:354-365` |

兩個詢問通過之後都會呼叫 `ByPassAddMessage` 把「使用者已知悉」寫進 VDB(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:351`、`:364`),這是全模組唯一用到繞行紀錄的地方。

**六條檢核的錯誤全部掛在兩個 Email 控件上**(`utxtEMAIL` / `utxtEMAIL_REQ`),包括「統一編號或客戶姓名不可同時空白」與兩個勾選檢核。使用者按訊息會跳到錯誤的欄位(附錄 E.8)。

#### 查詢前檢核(`DoValidateQuery`)

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 戶號起迄必須皆填或皆不填 | 只填一邊 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:219-224` |
| 查詢前 | 戶號起 ≤ 戶號迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:225-229` |
| 查詢前 | 通話日期起迄必須皆填或皆不填 / 起 ≤ 迄 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:231-241` |
| 查詢前 | 索取日期起迄必須皆填或皆不填 / 起 ≤ 迄 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:243-253` |
| 查詢前 | 查詢條件不可同時空白 | 全空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:255-265` |

**「不可同時空白」那條漏掉了行動電話。**條件式列了 8 個欄位,其中 `utxtEMAIL_0.Text` **重複寫了兩次**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:260-261`),而送查詢時明明有 `CELL_PHONE` 這個條件(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1054-1057`)。**只填行動電話按查詢會被擋下來說「查詢條件不可同時空白」**,重複的那一行八成本來要寫 `utxtCELL_PHONE_0`(附錄 E.8)。

第一條檢核的錯誤訊息是「戶號(起)(迄) 必須皆(不)填寫」,但掛的控件是通話日期欄(`udatCALLIN_DATE_ST_0`,`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:222`)。

#### 查詢條件怎麼組

`BeforeSearchButtonClicked` 每次都 `QueryVDB.Util.Parameters.Clear()`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1014`)——這點比 CAS 的 `CASM006` 好(那支的 `Clear()` 是被註解的)。

PO 端組 SQL 有兩個特別的:

- **客戶姓名用字串串接**:`AND CRM003A.PR_NAME LIKE N'%{0}%'`,值直接取自參數(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:339`)。這是本模組唯一一處對主檔查詢做字串串接的地方,其餘走 `EVAStringHelper.AddParam`。

- **通話 / 索取日期範圍是子查詢**:`AND CRM003A.PR_NO IN (SELECT DISTINCT PR_NO FROM CRM006A WHERE …)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:344-364`)。只有起日有值才加,迄日是跟著一起進去的。

另外主檔查詢一律 `LEFT JOIN` 一段自組的電訪人員子查詢(`GetOutBoundSQLString`),而那段子查詢的 `BF_NO` 條件也會吃查詢參數(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:687-688`)。**查戶號區間時,條件同時作用在主表與電訪子查詢上**,這是刻意的(避免把整張 `TMK_BF_V` 掃進來)。

#### 新增前的重複統編檢查

開「潛在客戶資料選取視窗」(`CRMM003p1`)之前,新增模式會先檢查該統編有沒有既有的潛在客戶序號:

- PO 的 `IsValidAdd` 用綁定參數查 `CRM003A` join `CRM006A` 的筆數,**出錯回 `-1`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:966-986`)。

- UI 判 `i == 0 ? true : false`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1475-1480`),所以 `-1` → `false` → 跳「此統一編號已有潛在客戶序號,是否要繼續新增?」的詢問。

**這條的錯誤處理方向與其他檢核相反:出錯時是「多問一次」而不是「靜默放行」。**結果安全,但訊息會誤導。

還有一條訊息與行為不符:按統編欄的按鈕時,條件是「長度 ≤ 5」,訊息卻寫「統一編號資料**過多**,請至少key六碼」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530`)——條件是太短,訊息說太多。

#### 自動帶值與被關掉的功能

| 行為 | 說明 | 錨點 |
|---|---|---|
| 選了戶號 → 自動帶電訪人員 | 只有新增模式做;編輯模式保留畫面原值 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1549-1566` |
| 拒絕行銷四個勾選框 → 反寫 `DM_CODE` / `DM_EMAIL` | 勾「拒絕所有」或「拒絕網路」→ `DM_EMAIL = 'N'`;勾「拒絕所有」或「拒絕書面」→ `DM_CODE = 'N'`;否則一律 `'Y'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:527-542` |
| **編輯模式下四個拒絕行銷勾選框全部 disabled** | 新增模式沒有這段,所以只有建檔當下能設 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| DM寄發碼 / 寄發廣告EMAIL 的下拉 | **2020-03-30 移除**,欄位改由上面那條規則反推 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:153-157` |
| 通訊地址 14 個細欄的回填 | **整段被註解**,只剩 `MAIL_ADDR` 由控件直接綁 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:483-496` |

「拒絕行銷只能在新增時設」是一個很硬的限制:**客戶事後表示要拒絕行銷,這支畫面改不了**。要確認這是刻意的還是漏了 `AddDataLoad` 的對應處理。

#### 覆核刪除時的明細處理

`BeforeApproveDelete` 做了一件很特別的事:把 model 裡四張明細全部 `Clear()` + `AcceptChanges()`,然後**自己下四句 `DELETE {表} WHERE PR_NO = '{值}'`**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:88-121`)。註解寫的理由是「因為有歷史資料的問題,所以忽略底層處理」。

三件事要注意:

1. **`PR_NO` 是用 `string.Format` 串進 SQL 的**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:109`、`:113`),不是綁定參數。`PR_NO` 由系統取號所以風險低,但寫法是髒的。

2. **刪除的是該客戶的全部明細,不只是畫面上載入的那幾筆。**因為明細取數有 `SYSDATE` 與 `1=2` 的限制,畫面上根本看不到全部,所以**使用者按下覆核刪除時,刪掉的比他看到的多很多**。

3. 迴圈跑的是 `this.DetailTable`,四張表都會刪;`ExecuteNonQuery` 的回傳值被丟掉,刪 0 筆也算成功。

#### 四眼各階段附加動作

八個 `After*` 全部做同一件事:呼叫 `SrNoCommentProcessor.AddCommentHistory(...)` 寫跳號一覽表,失敗就 `throw new ApplicationException("")`(空訊息)。

| 掛點 | 錨點 |
|---|---|
| `AfterGetMaintainData`(讀回跳號歷史) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:915-919` |
| `AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:920-962` |

每個 handler 第一行都是 `if (args.TableName != this.MasterTable.dbTableName) return;`,因為事件會對主檔 + 每張明細各觸發一次(`architecture.md §3.8`)。**這套與 CAS 的 `CASM001` 完全同構**,連 `throw new ApplicationException("")` 的空訊息都一樣。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 四組起迄的成對與大小 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:219-253` |
| 查詢前 | 條件不可全空(**漏算行動電話**) | 全空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:255-265` |
| 按統編查詢鈕 | 統編長度 ≤ 5 | 成立 | 阻擋(訊息寫反) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530` |
| 開選取視窗前(新增) | 該統編已有潛在客戶 | 成立 | **詢問**(選否清畫面) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1487-1497` |
| 開選取視窗前(新增) | 同上但 SQL 出錯 | 例外 | **詢問**(回 `-1` 當成已存在) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:980-984` |
| 新增 / 修改前 | 統編與姓名不可同時空白 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:283-287` |
| 新增 / 修改前 | 兩個 EMAIL 格式 | 格式錯 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:290-300` |
| 新增 / 修改前 | 通話 / 索取種類至少勾一項 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:303-328` |
| 新增 / 修改前 | 通話 / 索取日期大於系統日 | 成立 | 詢問 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:341-365` |
| 新增前(PO) | `PR_NO` 撞號 | 成立 | 記錄不擋(重取號) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:211-214` |
| 存檔前(PO) | 批次序號重算,取號失敗 | 例外 | **記錄不擋**(`-1` 寫進 PK) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047` |
| 編輯模式載入 | 四個拒絕行銷勾選框 | 一律 | 過濾(disabled,無提示) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| 明細取數 | `CRM004A` / `CRM0041A` | 一律 | **過濾(無提示,`1=2`)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454` |
| 明細取數 | `CRM006A` / `CRM0061A` 非今日 | 一律 | 過濾(無提示) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:400`、`:418` |
| 覆核刪除 | 明細一律整批實體刪除 | 一律 | 記錄不擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:111-118` |
| 四眼各階段 | 跳號一覽表寫入失敗 | 失敗 | 阻擋(`throw`,訊息空白) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:924` |

### 4.4 `CRMM004` — 客戶分級參數維護

#### 用途(推測)

**定義客戶等級的判定條件與對應的服務標準。**一列就是一個等級(`CUS_LV`),內容是:要不要開戶、貨幣型 / 非貨幣型基金的庫存金額級距與庫存比、應親訪 / 應電訪 / 應完成總次數、以及計算頻率。

這是本模組唯一一支**單表、無明細、伺服器端有卡控**的維護畫面,也是最小的一支(PO 137 行)。

#### 三個旗標控制四組欄位的可編輯性

| 勾選框 | 控制什麼 | 勾掉時 | 錨點 |
|---|---|---|---|
| `uchkHASBF_NO`(是否開戶) | 連動 `uchkHAS_MF` 的可用性與勾選狀態 | 一併關掉貨幣型 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:220-230` |
| `uchkHAS_N_MF` | 非貨幣結餘起 / 迄 | 兩欄 `ReadOnly` 且清空 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:231-237` |
| `uchkHAS_MF` | 貨幣結餘起 / 迄 | 兩欄 `ReadOnly` 且清空 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:242-248` |
| `uchkHAS_PER` | 兩個庫存比欄位 | 同上 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:251-259` |

必填旗標(`reqv*.IsRequisite`)是**每次 `DoValidate` 時依 `ReadOnly` 動態設定**的(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:36-43`),不是 Designer 寫死的。這比全庫其他畫面的做法都乾淨。

#### `-1` 哨兵值

「起」的欄位空白時寫 `-1` 進 DB(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:66-71`),讀回來時 `>= 0` 才填進畫面(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:132-140`),grid 顯示時 `< 0` 就設成 Null(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:203-207`)。

**三個地方各自處理同一個哨兵值,沒有共用函式。**「迄」的欄位沒有這套(直接 `Convert.ToInt32`),因為它是必填的。

#### 伺服器端的區間重疊檢核

`BeforeUpdate`(`BeforeAdd` 直接轉呼叫它)會下兩段 SQL 檢查新資料的庫存區間與別的等級重疊:

| 段 | 條件 | 錨點 |
|---|---|---|
| 非貨幣 | `HAS_N_MF = 1 AND HAS_MF = :HAS_MF AND CUS_LV <> :CUS_LV AND ((:S > S AND :S < E) OR (:E > S AND :E <= E))` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:88-94` |
| 貨幣 | 同形狀,換成 `MF_*` 欄位 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:109-115` |

兩段都是 `SELECT '與客戶等級' || CUS_LV || '之…區間重疊'`,用 `ExecuteScalar` 取回訊息;非空就 `args.CancelMsg = msg; args.Cancel = true;`。**這是全模組唯一在伺服器端擋下資料的地方。**

**但重疊判斷式漏了一種情形:新區間完全包住既有區間。**

| 既有 | 新輸入 | `:S > S AND :S < E` | `:E > S AND :E <= E` | 判定 | 實際 |
|---|---|---|---|---|---|
| [10, 20] | [15, 25] | 15>10 且 15<20 ✔ | — | 重疊 ✔ | 重疊 |
| [10, 20] | [5, 15] | 5>10 ✘ | 15>10 且 15≤20 ✔ | 重疊 ✔ | 重疊 |
| [10, 20] | **[5, 30]** | 5>10 ✘ | 30>10 但 30≤20 ✘ | **不重疊** ✘ | **完全包住** |
| [10, 20] | [10, 20] | 10>10 ✘ | 20>10 且 20≤20 ✔ | 重疊 ✔ | 相同 |

也就是說**只要新等級的區間比既有等級寬,兩邊就都設得起來**,兩個等級會同時命中同一筆客戶。嚴重度高(附錄 E.4)。

另外兩個小問題:

- 兩段檢核的 `ExecuteScalar` 都沒有把 `cmd` 包在 `using` 裡(原本的 `using` 被註解掉了,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:83-84`、`:128`),命令物件不會被釋放。

- 第二段多了一句 `cmd.Parameters.Clear()`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:116`),但 `cmd` 是上一行剛 `GetSqlStringCommand` 出來的新物件,這句沒有作用。第一段沒有這句。**同一個方法裡兩段對稱的程式碼寫法不一致。**

#### `DoValidate` 的回傳語意與其他畫面相反

`CRMM004.DoValidate()` **回傳 `true` 代表有錯**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:45`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:54`),呼叫端寫 `if (DoValidate()) { e.Cancel = true; }`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:167-171`)。

而 `CRMM001` / `CRMM003` / 五支 B 畫面的 `DoValidate()` **回傳 `true` 代表通過**,呼叫端寫 `if (DoValidate() == false) { e.Cancel = true; }`。**同一個名字、相反的語意,在同一個模組裡並存**(附錄 E.4)。

#### 查詢與顯示

- 查詢只有一個條件 `CUS_LV`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:97-101`),而且每次先 `Parameters.Clear()`。

- 查詢 SQL 會 `LEFT JOIN CTL014`(`SOURCETYPE = '600'`)把 `FREQ_UNIT` 轉成顯示文字,再用 `DECODE(NEED_CNT, 0, '', TO_CHAR(FREQ_NUM) || DISPLAYNAME)` 組成 `FREQ` 欄(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:52-57`)。**維護頁的取數 SQL 沒有這個 join**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:66-70`),所以 `FREQ` 只在查詢 grid 上看得到。

#### 四眼各階段附加動作

**沒有 `After*`。**只有 `BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData` / `BeforeAdd` / `BeforeUpdate` 五個(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:39-43`),其中 `BeforeGetToDoData` 直接轉呼叫 `BeforeSelect`、`BeforeAdd` 直接轉呼叫 `BeforeUpdate`。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 新增 / 修改前 | 框架必填(依旗標動態決定哪些欄必填) | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:36-45` |
| 新增 / 修改前 | 非貨幣結餘起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:47-49` |
| 新增 / 修改前 | 貨幣結餘起 ≤ 迄 | 起 > 迄 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:51-53` |
| **伺服器端** `BeforeAdd` / `BeforeUpdate` | 非貨幣庫存區間與其他等級重疊 | 成立 | 阻擋(`args.Cancel` + 訊息) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:85-105` |
| **伺服器端** 同上 | 貨幣庫存區間與其他等級重疊 | 成立 | 阻擋(訊息串接在前一條後面) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:106-127` |
| 伺服器端 同上 | **新區間完全包住既有區間** | 成立 | **記錄不擋**(判斷式漏掉) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:93-94`、`:114-115` |
| 勾選框連動 | 取消勾選 | 成立 | 記錄不擋(欄位清空且唯讀) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:231-259` |

## 5. 查詢畫面(I)

### 5.1 結構

`CRMI001` 是本模組唯一的 I 畫面,查的是 `CRM007A`(直銷分配客戶名單)。

| 面向 | `CRMM003`(M 型) | `CRMI001`(I 型) |
|---|---|---|
| 介面 | `ICRMM003_PO : IEvaDataAccess` | `ICRMI001_PO`,**不繼承任何東西**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:24` |
| 類別 | `: BaseEVADaoPO, ICRMM003_PO` | `: ICRMI001_PO`,**沒有基底**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:36` |
| 連線 | 由基底管 | **自己 `new` 兩個 `Database`**(`TA` 與 `SWProduct`);`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:38-39` |
| 主明細宣告 | `xTableMapping` | **整行被註解**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:44` |
| 唯一活著的方法 | 一堆 | 只有 `Select`(介面上還有三個宣告被註解);`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:26-30` |

> **與 CAS 一模一樣的掃描器誤判。**`CRMI001_PO.cs:44` 那行註解是 `//this.MasterTable = new TableMapping("OFD701", "SEAL");`,與 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASI001_PO.cs:41` 逐字相同——兩支都是從同一個樣板複製來的。掃描器的正規式不剝註解(`architecture.md §6.3` 已記),所以全庫的「實體表」計數含有一批來自註解行的假表。本文一律以程式為準。

`CRMI001_PO` 另有兩支 `public` 方法 `GetEmpNo` / `GetUidCode`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:529`、`:560`),**但它們不在介面裡**——Ctl 拿到的是 `ICRMI001_PO` 型別,呼叫不到。**兩支都是死碼**,而且 `GetUidCode` 判了 `ds.Tables.Count > 0` 卻直接取 `Rows[0]`,查無資料時會 `IndexOutOfRange`(被 `catch` 吞成空字串)。

### 5.2 查詢條件

畫面共 20 組條件,分兩類:

| 類 | 條件 | 送出的參數名 |
|---|---|---|
| 起迄成對 | 分配期別、執行日期、受益人戶號、最後交易日期、最後交易員工代碼、單筆最高申購金額、結存金額、本次指派日期、再聯絡日期 | `*_BGN` / `*_END` |
| 單值 | 資料來源、最後交易基金代碼、最後交易銷售機構區別 / 代碼、最後交易單位類別、指派交易單位類別、本次指派者 / 單位 / 業務員、特殊名單、有無意願申購、聯絡結果代碼 | 同欄位名 |

外加一個看不見的:**登入者的員工代碼**(`QUERY_EMP_NO`),見 §5.3。

UI 端的檢核有一個共同的模式:「起有值、迄空白 → 自動把迄填成起」、「起空白、迄有值 → 報錯」、「兩邊都有 → 比大小」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:108-191`)。只有分配期別多一條「兩個都空也要報錯」(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:112-113`),所以**分配期別是唯一的必填條件**。

### 5.3 哪些條件會靜默濾掉資料

#### (1) 登入者權限:`F_TA_GET_EMPS` 的 INNER JOIN

查詢 SQL 開頭是一段 `WITH`:

```
WITH MYAGENT_LIST AS
(SELECT RTRIM(SUBSTR(DEPT_EMP_NO, 2)) AS DEPT_EMP_NO
   FROM TABLE(F_TA_GET_EMPS('<登入者員工代號>')))
```

然後在 `WHERE` 裡硬加 `AND (CRM007A.ASSIGN_DEPT_NO1||CRM007A.ASSIGN_EMP_NO1) = RTRIM(Z.DEPT_EMP_NO)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`:107`)。

**這是 INNER JOIN,不是 `LEFT JOIN`,也不是 `EXISTS`。**後果:

| 情形 | 結果 |
|---|---|
| `F_TA_GET_EMPS` 回空集合 | **一筆都查不到**,而且畫面只會說「查無資料」 |
| 名單的 `ASSIGN_DEPT_NO1` 或 `ASSIGN_EMP_NO1` 是空白 | **查不到**(串起來對不上任何一筆) |
| 兩欄串起來的長度與 TVF 回的格式差一個字 | **查不到** |

`F_TA_GET_EMPS` **不在版控內**,回傳格式也只能從 `RTRIM(SUBSTR(DEPT_EMP_NO, 2))` 反推:第一個字元被丟掉、尾端空白被砍。**假設**:那個被丟掉的字元是某種前綴旗標。要確認得看 SP 原始碼。

而且 `QUERY_EMP_NO` 的值是這樣來的(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:200-206`):

```
string data = biz.GetEMP_INFO(this.UserID);
string[] words = data.Split(',');
if (words[1] != "") QueryVDB…AddParametersRow("QUERY_EMP_NO", …, words[1]);
```

**位置取參數**:取逗號切開的第 2 段。回傳格式一改就拿不到值,而且 `data` 是空字串時 `words[1]` 會 `IndexOutOfRange`(沒有長度檢查)。若 `words[1]` 是空字串,參數不會被加,PO 端 `GetParamValue` 回空字串 → `F_TA_GET_EMPS('')` → **多半回空集合 → 查無資料**。

**與 CAS 的差別要特別記住。**`CASI001` 拿不到員工代號時是「條件整個不加 → 看到全部資料」(`cas.md §5.3`),`CRMI001` 是「條件還在但比不到 → 看不到任何資料」。**同一個機制,兩個模組的失效方向相反。**

#### (2) 五處 `> =` / `< =`(中間有空白)

| 條件 | 寫法 | 錨點 |
|---|---|---|
| 分配期別(起) | `CRM007A.ASSIGN_NO > = '…'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140` |
| 分配期別(迄) | `CRM007A.ASSIGN_NO < = '…'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:150` |
| 受益人戶號(起) | `CRM007A.BF_NO > = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:194` |
| 受益人戶號(迄) | `CRM007A.BF_NO < = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:204` |

**假設**:整段 SQL 會語法錯,被 `catch` 吞成「執行失敗,請檢查」(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:507-511`)。依據是 SQL 標準與 Oracle 的詞法規則(`>` 與 `=` 之間不得有空白)。與 `cas.md §5.3` 的 8 處同源——**兩個模組的 I 畫面是同一份樣板複製的,連 bug 都一樣**。無法本機驗證,要連 DB 跑一次帶分配期別條件的查詢。

因為**分配期別是必填**,所以只要這條假設成立,`CRMI001` 就是**完全不能用**的。這一點與 CAS 那邊不同(CAS 的起迄條件是選填)。

#### (3) 最後交易日期(迄)與本次指派日期(迄)被無效化

```
if (this.udatLAST_TRN_DATE_BGN_0 != null && this.udatLAST_TRN_DATE_END_0.Value == null)
{ this.udatLAST_TRN_DATE_END_0.Value = this.udatLAST_TRN_DATE_BGN_0.Value; }
```

比較的是**控件物件**而不是 `.Value`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174`)。控件永遠不是 `null`,所以第一個分支永遠成立 → **只要「迄」是空的就被填成「起」的值,而且後面兩個 `else if` 永遠跑不到**。

其他七組起迄都寫 `.Value != null`,只有這兩組漏了。實際效果:**這兩個條件的「迄」欄位只要留空就會變成單日查詢,而不是「起日之後全部」**——但因為「起」空白時也會被複製成空白,所以只有在「填了起、沒填迄」時才看得出差異。嚴重度中(附錄 E.8)。

#### (4) `LAST_TRN_DATE_END` 抓錯參數列

```
DataModelUtility.ParametersRow Row = …Rows.Find("EXE_DATE_END");
String end_date = …FindByName("LAST_TRN_DATE_END").Value;
```

`Row` 找的是 `EXE_DATE_END`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:221`),但實際用的值取自 `LAST_TRN_DATE_END`。`Row` 這個變數在該區塊內**完全沒被用到**,所以目前無害;但如果有人照其他區塊的樣子補上 `if (Row.Opeartor == …)`,就會在 `EXE_DATE_END` 不存在時 `NullReferenceException`。複製貼上沒改乾淨(附錄 E.8)。

#### (5) 全部條件都是字串串接

20 組條件沒有一個用綁定參數,全部是 `strSQL += "AND CRM007A." + Row.Name + " = '" + Row.Value + "'"`。其中**只有一部分做了 `Replace("'", "''")`**:

| 有跳脫 | 沒跳脫 |
|---|---|
| `ASSIGN_NO_BGN` / `ASSIGN_NO_END` / `SOURCE_CODE` / `LAST_FUND_ID` / `LAST_AGENT_ID` / `LAST_AGENT_CODE` / `LAST_EMP_NO_BGN` / `LAST_EMP_NO_END` / `LAST_DEPT_TYPE` / `BASE_DEPT_TYPE` | `EXE_DATE_BGN` / `EXE_DATE_END` / `BF_NO_BGN` / `BF_NO_END` / `LAST_TRN_DATE_BGN` / `LAST_TRN_DATE_END` / `TOT_ALLOT_AMT_*` / `BAL_AMT_*` / `ASSIGN_DATE1_*` / `ASSIGN_USER_ID1` / `ASSIGN_DEPT_NO1` / `ASSIGN_EMP_NO1` / `SPC_YN` / `RESULT` / `NEXT_CONTACT_DATE_*` / `CONTACT_CODE` |

錨點:`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`(有跳脫)vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:161`(沒跳脫)。而且 `QUERY_EMP_NO` 直接串進 `F_TA_GET_EMPS('…')` 也沒跳脫(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`)。**`Replace("'", "''")` 本來就不是正確的防注入手段**,這裡連它都只做一半(附錄 E.7)。

#### (6) `ASSIGN_DEPT_NO1` 是唯一支援 `Like` 的條件

其他所有單值條件只在 `Opeartor == SQLOperator.Equal` 時才加,`ASSIGN_DEPT_NO1` 多寫了一個 `Like` 分支(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:396-399`)。**送了 `Like` 以外運算子的條件會被無聲丟掉**——例如 UI 若送 `GreaterthanEqual`,PO 這邊什麼都不加,使用者以為有限制其實沒有。

#### (7) 九張表的舊式 `(+)` 外連接寫在 `WHERE` 裡

`FROM CRM007A, BMS001A_V01 BMS001A, COD009 COD009_L, COD009 COD009_1, COD009 COD009_2, OFD081A, CTL014 A, OFD068A, OFD002 B, OFD002 C, AA_USER D, AA_USER E, MYAGENT_LIST Z`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:91-94`),外連接一律用 Oracle 的 `(+)` 語法。

注意 `CRM007A.LAST_AGENT_CODE = OFD068A.AGENT_CODE(+)` **只 join 機構代碼、沒有 join 機構區別碼**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:102`),而 `CRMB002` / `CRMB003` / `CRMB004` 的同一段 join **兩個欄位都有**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:88-89`)。**同一張表在 I 畫面與 B 畫面的機構簡稱可能不同**——`OFD068A` 的 PK 若含 `AGENT_ID`,`CRMI001` 這邊會重複列。嚴重度中(附錄 E.4)。

### 5.4 取數之後做的事

`Select` 不是把結果塞回傳進來的 VDB,而是 `xVirtualDataBase.CreateNewVDB(mModel)` 建一個新的再回傳(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:64-65`)。填之前先把 `CRM007A` 的 13 個四眼欄位設成 `DefaultValue`(§2.5),所以**查出來的每一列都帶著「登入者 + 現在時間」的假四眼資訊**。

這段是從別的畫面樣板複製來的死碼——`CRMI001` 是唯讀查詢,不會寫回 DB。但它會影響 grid 顯示:`STATUS` 欄一律顯示 `301`。

### 5.5 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 分配期別必填 | 兩欄都空 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:112-113` |
| 查詢前 | 九組起迄的「起空迄有值」 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:108-191` |
| 查詢前 | 九組起迄的大小比較 | 起 > 迄 | 阻擋 | 同上 |
| 查詢前 | 「起有值迄空白」 | 成立 | **記錄不擋**(自動把迄填成起) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:109-110` |
| 查詢前 | 最後交易日期 / 本次指派日期的成對檢核 | 一律 | **過濾(無提示,判斷式錯)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174` |
| 取數 | 登入者權限(`F_TA_GET_EMPS` INNER JOIN) | 對不上 | **過濾(無提示)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:107` |
| 取數 | 五處 `> =` 語法 | 一律 | **阻擋**(假設:語法錯 → 「執行失敗」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`、`:150`、`:194`、`:204` |
| 取數 | `ASSIGN_DEPT_NO1` 以外的條件運算子非 `Equal` | 成立 | **過濾(無提示,條件不加)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:181-184` |
| 取數 | 查無資料 | 零筆 | 記錄不擋(「查無資料」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:498-500` |
| 取數 | 任何例外 | 成立 | 記錄不擋(「執行失敗,請檢查」) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:507-511` |

## 6. 批次(B)與 WindowsService

```text
[圖] 五支批次畫面的觸發、檢核、寫入路徑，以及三個共同缺陷
圖中文字:① CRMB001 三條路徑共用一個畫面 / 執行鈕 → Execute / 參數走 Parameters / S_TA_CRMB001_EXCUTE / 呼叫整段被註解 空操作 / DoExp1 上傳 CSV / 事件解掛 全無檢核 / DoExp2 產 Excel / S_TA_CRMB001_GET / ② 執行前檢核（只有產生那條還活著） / DoCheck / 基金結帳／重複產生 / POST_CTL_CODE <> Y / NULL 被靜默放行 / 刪除檢核 / 整段註解 / WARNING 詢問 / UI 還在 但永不觸發 / ③ CRM007A 的一生：產生 → 調撥 → 指派 → 登錄 / CRMB001 INSERT / DATAID 綁成 ASSIGN_NO / CRMB002 UPDATE / 單位 1→2 會動四眼欄 / CRMB003 UPDATE / 業務員 1→2 不動四眼欄 / CRMB004 UPDATE / 聯絡結果 不動四眼欄 / ④ 三支的共同毛病：影響筆數被丟掉 / ExecuteNonQuery / 回傳值沒有接 / i += 1 硬寫 / B004 寫成 i = +1 / if (i == 0) throw / 永遠不成立 死碼 / 更新 0 筆也算成功 / 使用者看到執行成功 / ⑤ CRMB005：唯一會動到 CRMM003 資料的批次 / CRMB005 查重複 / PR_NAME=／MAIL_ADDR= 三值邏輯 / GetMergePrNoList / UI 用 LINQ 另組一次 / S_TA_CRMB005_EXCUTE / 不在版控 內容未知 / CRM003A 與明細 / 合併後 PR_NO 消失
```

*圖:圖 4 批次流。橘框=本模組程式碼；黑框=無原始碼（版控外的 SP）；灰虛框=被影響的資料；橘虛框=會咬人的行為。CRMB001 的「產生／刪除名單」目前是空操作——唯一會下 SQL 的那段被註解掉了。*

**本模組沒有任何 WindowsService。**`Dev/` 底下與 CRM 相關的專案只有 `Dev/ATLAS.CRM` 與 `Dev/ATLAS.CRM.Report` 兩個,沒有服務專案。五支 B 全部是 `formstyle="OneStep"` 的使用者按鈕(`Dev/ATLAS.CRM/Source/UI/UI.CRM/App.config:18`)。

### 6.1 觸發與按鈕配置

| 畫面 | 查詢鈕 | 執行鈕 | 額外鈕 | 錨點 |
|---|---|---|---|---|
| `CRMB001` | **關閉**(`ButtonSearchEnable = false`) | 開 | `DoExp1` 上傳 CSV、`DoExp2` 產出 Excel | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:63-64`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:170`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:255` |
| `CRMB002` | 開 | 開 | — | — |
| `CRMB003` | 開 | 開 | — | — |
| `CRMB004` | 開 | 開 | — | — |
| `CRMB005` | 開(執行模式下鎖住查詢欄) | 開 | — | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:188-205` |

### 6.2 `CRMB001` — 名單產生 / 刪除 / 上傳

這支有三條互不相干的路徑,共用同一個畫面:

| 路徑 | 入口 | 走哪支 PO 方法 | 現況 |
|---|---|---|---|
| A 產生 / 刪除名單 | 「執行」鈕 | `Execute`(參數走 `Parameters`) | **SP 呼叫整段被註解,什麼都不做** |
| B 上傳 CSV 名單 | `DoExp1` | `Execute`(資料走 `DataEntity.CRM007A`) | 可用 |
| C 產出客戶名單 Excel | `DoExp2` | `GetReportData` → `S_TA_CRMB001_GET` | 可用 |

`Execute` 靠一個 `if` 分流(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:78`):

```
if (model.Utility.Parameters.Count == 0 && model.DataEntity.CRM007A.Count > 0)
```

參數是空的且有資料列 → 走 CSV 上傳的 INSERT;否則**走完 try 區塊什麼都不做**,因為底下那段 SP 呼叫是註解(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`)。而 `Result` 在 `:77` 被 `Clear()` 之後沒有再塞任何一列,所以畫面拿到的是空的結果集合。

**路徑 A 的檢核還完整地留著**,使用者會覺得「有檢核就是有在做事」:

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 執行前 | 框架必填 | — | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:84-89` |
| 執行前(PO) | 該結算日有基金尚未結帳 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:261-280` |
| 執行前(PO) | (產生)該結算日已有名單 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296-300` |
| 執行前(PO) | (刪除)該結算日沒有名單可刪 | — | **整段被註解** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-306` |
| 執行前(PO) | (刪除)名單已有聯絡日期,詢問是否全刪 | — | **整段被註解** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:311-332` |
| 執行前(UI) | 上一條的 `WARNING` 參數 | 永遠不存在 | **詢問(死碼)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128-136` |

**「尚未結帳」那條有 Oracle 三值邏輯的問題。**

```
SELECT DISTINCT FUND_ID FROM OFD303A
 WHERE CTL_DATE <= :END_DATE AND POST_CTL_CODE <> 'Y'
```

`POST_CTL_CODE` 是 `NULL` 時,`NULL <> 'Y'` 的結果是 `UNKNOWN` 不是 `TRUE`,該列**被靜默排除**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265`)。也就是**從來沒被設定過結帳旗標的基金,會被當成已結帳放行**。與 `cas.md` 附錄 E.7 記的 `CASB001_PO.cs:214` 是同一類缺陷,嚴重度高(附錄 E.2)。

#### CSV 上傳(路徑 B)

| 步驟 | 做什麼 | 錨點 |
|---|---|---|
| 1 | `OpenFileDialog`,只接 `*.csv` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:172-177` |
| 2 | **把 `BeforeExecuteButtonClicked` 事件解掛** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:185` |
| 3 | 讀第一行(標題)丟掉;空白就 `return` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:191` |
| 4 | 逐行 `Split(',')`,**欄數 < 17 或第一欄空白就 `break`** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:192-194` |
| 5 | 17 欄依位置對映到 `CRM007A` 的欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:196-230` |
| 6 | 有資料就 `DoExecute()` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:234-237` |
| 7 | `finally` 把事件掛回去 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:246` |

四個要命的地方:

1. **第 2 步解掛事件,等於這條路徑完全沒有檢核。**結帳檢查、重複產生檢查全部跳過。上傳的名單可以撞到同一個 `ASSIGN_NO` + `BF_NO`(靠 PK 才會擋),也可以指到任何結算日。

2. **第 4 步用 `break` 不是 `continue`。**格式壞掉的那一列之後的所有列**全部靜默丟掉**,而且畫面只會說「已上傳 N 筆」,N 是實際寫進去的筆數。使用者不會知道檔案有 500 列只進了 37 列。

3. **`Split(',')` 不處理引號。**欄位值裡有逗號就整列錯位,而錯位之後 `line.Length` 反而 ≥ 17,不會被第 4 步擋下。

4. **兩個 `catch` 只跳訊息就 `return`**,前面已經 `AddCRM007ARow` 的列雖然被 `vdb.UIView.Clear()` 清掉了,但使用者看到的訊息是「戶號欄位格式不正確」——沒有說是第幾列。

INSERT 那段本身也有兩個問題(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:107-175`):

- **`DATAID` 被綁成 `:ASSIGN_NO`。**欄位清單第一個是 `DATAID`,`VALUES` 第一個也是 `:ASSIGN_NO`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:108`、`:142-143`)。**上傳進來的每一筆,`DATAID` 都等於分配序號**,而不是 `Guid`。

- **所有參數一律綁成 `OracleDbType.Varchar2`**,包含金額(`decimal`)與日期(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:184`)。因為是逐欄跑 `Columns` 迴圈,型別資訊整個被丟掉。

還有一個隱形的耦合:INSERT 的參數名來自 `DataTable` 的欄位名,而上面那 26 行 `Columns.Remove(...)`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:80-105`)決定了哪些欄位會被綁。**`CRMB001Model.xsd` 加一個欄位,這段 INSERT 就會多綁一個 SQL 裡沒有的參數 → `ORA-01036`。**

### 6.3 `CRMB002` / `CRMB003` / `CRMB004` — 三支調撥 / 指派 / 登錄

三支的結構完全一樣:查詢 → 勾選 → 執行逐列 UPDATE。

| 面向 | `CRMB002` 單位調撥 | `CRMB003` 業務員指派 | `CRMB004` 聯絡結果登錄 |
|---|---|---|---|
| 查詢是否受 `F_TA_GET_EMPS` 限制 | **否** | **是** | **否** |
| 查詢必填 | 分配期別 + 已指派歸類(轉出) | 分配期別 | 分配期別 |
| 執行必填 | 已指派歸類(轉入) + 部門代碼(轉入) | 轉入業務員 + 部門代碼 | 無(欄位在 grid 裡) |
| UPDATE 哪些欄 | `ASSIGN_*1` → `ASSIGN_*2`,`ASSIGN_DEPT_NO1` 換新值,`ASSIGN_USER_ID1` / `ASSIGN_EMP_NO1` 清空 | 同左,但 `ASSIGN_USER_ID1` / `ASSIGN_EMP_NO1` 填新值 | `NEXT_CONTACT_DATE` / `RESULT` / `CONTACT_CODE` / `CONTACT_COMM` |
| 有沒有動四眼欄位 | **有**(`UPDATEID` / `UPDATEDATE` / `VERIFYID` / `VERIFYDATE`) | **沒有** | **沒有** |
| 錨點 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:196-211` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:205-216` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:182-189` |

**三支都繞過 EVA 引擎直接 UPDATE。**`CRM007A` 的資料從頭到尾沒有走過四眼流程(§2.5),所以這不算「破壞狀態機」,但 `CRMB002` 把 `VERIFYID` / `VERIFYDATE` 蓋成執行者、另外兩支完全不動任何時戳,**三支對「誰在什麼時候改了這筆」的紀錄方式不一致**。

#### 三支共同的三個缺陷

| 缺陷 | 說明 | 錨點 |
|---|---|---|
| 影響筆數被丟掉 | `m_db.ExecuteNonQuery(cmd, tran);` 的回傳值沒有接,下一行硬寫 `i += 1`(`CRMB004` 是 `i = +1`),所以 `if (i == 0) throw` 是死碼。**更新 0 筆也算成功** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:226-233`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:207-214` |
| `catch` 直接 `tran.Rollback()` 沒判 null | `BeginTransaction()` 本身失敗時 `tran` 是 `null` → 真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:237`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:243`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:224` |
| 查無資料回空訊息 | `AddResultRow(false, 0, "")`,使用者看到的是空白對話框 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:159`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:168`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:147` |

#### 三支不一致的地方

| 面向 | 差異 | 錨點 |
|---|---|---|
| `BF_NO` 的綁定型別 | `CRMB002` 綁 `Int32`,`CRMB003` / `CRMB004` 綁 `Varchar2`——同一欄三支兩種型別 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:217` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:224` |
| 「已指派」的判斷 | `CRMB002` 用 `DECODE(ASSIGN_DEPT_NO1, NULL,'N', ' ','N', 'Y')`(空白也算未指派);`CRMB003` 用 `DECODE(ASSIGN_EMP_NO1, NULL,'N','Y')`(**空白算已指派**) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:114` |
| 基金表 | `CRMB002` join `OFD081V`,`CRMB003` / `CRMB004` join `OFD081A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:80` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:87` |
| 執行者從哪來 | `CRMB002` 從參數 `USER_ID`(UI 傳);`CRMB003` 從 `model.Utility.PermissionInfo[0].UserID` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:190` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:197` |
| 排序 `switch` 有無 `default` | 三支都**沒有**,`SORT_ORDER` 不是 `0`–`5` 就完全沒有 `ORDER BY` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` |
| 轉入 = 轉出的檢核 | `CRMB002` **被註解**(2016-08-16「轉出與轉入應可為同一部門」);`CRMB003` 還活著 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:258-262` |

#### `CRMB003` / `CRMB004` 的登入者欄位鎖定

兩支的 `GetDefault` 有一段**逐字相同**的 SQL(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:286-314` 與 `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:268-296`),用 `COD009` + `SAL051` + `OFD002` 取登入者的員工代號、部門、職級,然後:

| `SAL_CD` | 效果 | 錨點 |
|---|---|---|
| `A` 或 `B`(主管) | 清空員工與部門的預設值,**解鎖兩個欄位** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:348-358` |
| `C`(業務員) | `xIS_LOCK_EMP = true`——**但它上面兩行已經是 `true` 了,這個 `if` 什麼都沒做** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345` |
| 空白 / 其他 | 兩個欄位都鎖 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:335-338` |

三個〔客戶特定〕的寫死值:

- `TRANSLATE(NVL(SAL051.SAL_CD,'Z'), 'BCADEFZ', '9876540')` — 把職級碼翻成排序碼,**`B` 最大、`Z` 最小**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:298`)。

- `CASE WHEN LENGTH(OFD002.DEPT_NO) = 3 THEN OFD002.DEPT_NO || '01' ELSE OFD002.DEPT_NO END` — 三碼部門自動補 `'01'`(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:291-296`)。

- `SUBSTR(SAL051.SAL_DEPT_NO, 1, 3)` — 取直銷部門前三碼當業務部門(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:305`)。

而且這段 SQL **把登入者代號用 `string.Format` 串了兩次**(`'{0}' AS UID_CODE` 與 `COD009.UID_CODE = '{0}'`,`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:300`、`:307`)。

`CRMB003` 的 UI 還有一條依職級的檢核:**主管(`SAL_CD == "A"`)查詢時必須填「指派單位別(轉出)」**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:198-201`)。註解列了 8 條應有的檢核(編號 1–8),**實作的只有 1、2、3、5、8,第 4 與第 7 條只留註解**(第 7 條還寫了「PS: Searcher已擋住不給選用,pass」)。

### 6.4 `CRMB005` — 重複潛在客戶合併

#### 查詢

查 `CRM003A`(`USAGE = '1'`)裡「有另一筆同姓名 + 同地址」或「有另一筆同姓名 + 同統編」的潛在客戶:

```
AND EXISTS (SELECT * FROM CRM003A OTHER
             WHERE OTHER.PR_NO <> CRM003A.PR_NO
               AND OTHER.PR_NAME = CRM003A.PR_NAME
               AND OTHER.MAIL_ADDR = CRM003A.MAIL_ADDR)
```

三個問題:

1. **Oracle 三值邏輯。**`PR_NAME`、`MAIL_ADDR`、`ID_NO` 任一為 `NULL` 時,`=` 的結果是 `UNKNOWN`,該組**靜默不算重複**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:91-107`)。在 Oracle 裡空字串就是 `NULL`,所以**地址空白的那一批重複客戶永遠找不出來**。嚴重度高(附錄 E.2)。

2. **`merge_type` 的 `if / else if` 沒有 `else`。**不是 `"1"` 也不是 `"2"` 時,`EXISTS` 條件與 `ORDER BY` **一起消失**,查詢會回傳**全部** `USAGE = '1'` 的潛在客戶,而畫面會把它們全部當成「重複清單」顯示(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:89-107`)。目前 UI 的選項只有 1 / 2,所以踩不到,但沒有任何防護。

3. **查詢前檢核區塊是空的**(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:80-84`),四個查詢欄位全部可留白 → 掃全表。

#### 合併

UI 端 `GetMergePrNoList` 把勾選那一列當成「存續序號」,在畫面資料裡用 LINQ 分組找出同組的其他序號,組成 `存續|其他1|其他2` 的字串送給 SP(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:213-260`)。

**分組的鍵與 SQL 的條件不是同一套:**

| 層 | 怎麼判「同一組」 | 錨點 |
|---|---|---|
| SQL(挑出重複) | `OTHER.PR_NAME = CRM003A.PR_NAME AND OTHER.MAIL_ADDR = …` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` |
| UI(組合併清單) | `(PR_NAME + "_" + MAIL_ADDR).Trim()` 當 group key | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:235-241` |

`.Trim()` 只砍整串的頭尾,**中間那個 `_` 前後的空白不會被砍**。姓名尾端有空白時,SQL 的 `=` 在 Oracle 的 `VARCHAR2` 語意下會視為不同(`'A ' <> 'A'`),UI 這邊也是不同——兩邊碰巧一致。但如果哪天 SQL 改成 `TRIM(...) =`,UI 這邊就對不上了。

實際的合併動作全在 `S_TA_CRMB005_EXCUTE` 裡,**不在版控內**(`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:156`)。CRM 這邊只負責挑名單、組字串。

### 6.5 與 M 畫面的關係

| B 畫面 | 動到哪張表 | 對應的 M 畫面 | 會不會打架 |
|---|---|---|---|
| `CRMB001` / `CRMB002` / `CRMB003` / `CRMB004` | `CRM007A` | **無**(`CRM007A` 沒有 M 畫面) | 不會 |
| `CRMB005` | `CRM003A` 與其明細(由 SP 決定) | `CRMM003` | **會**——合併會讓某些 `PR_NO` 消失或被改掛,而 `CRMM003` 正在編輯的那筆可能就是被合併掉的 |

`CRMB005` 的合併是**唯一一個會動到 `CRMM003` 主檔的批次**,而且它繞過四眼(直接進 SP)。合併之後:

- 被合併掉的 `PR_NO` 在 `CRMM003` 查不到(或查到的是存續那筆)。

- `CRM006A` / `CRM004A` 的明細如果被改掛到存續 `PR_NO`,**`CALLIN_SRNO` / `REQ_SRNO` 可能撞號**——SP 有沒有處理這件事,repo 內看不到。**建議在合併前後各跑一次 `CRM006A` 的 PK 重複檢查。**

### 6.6 卡控總表

| 畫面 | 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|---|
| `CRMB001` | 執行前 | 框架必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:84-89` |
| `CRMB001` | 執行前 | 該結算日有基金未結帳 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:274-280` |
| `CRMB001` | 執行前 | 同上,但旗標為 `NULL` | 成立 | **過濾(無提示,三值邏輯)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265` |
| `CRMB001` | 執行前 | 產生:該日已有名單 | 有 | 阻擋 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:296-300` |
| `CRMB001` | 執行前 | 刪除:無名單可刪 / 已有聯絡資訊 | — | **記錄不擋**(整段註解) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-332` |
| `CRMB001` | 執行 | 產生 / 刪除實際動作 | 一律 | **記錄不擋**(SP 呼叫被註解,無任何訊息) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214` |
| `CRMB001` | 上傳 CSV | 全部檢核 | 一律 | **過濾(無提示,事件被解掛)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:185` |
| `CRMB001` | 上傳 CSV | 欄數 < 17 或首欄空白 | 成立 | **過濾(無提示,`break` 丟掉後續全部)** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:194` |
| `CRMB001` | 上傳 CSV | 戶號 / 金額格式 | 轉型失敗 | 阻擋(整批放棄) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:199-206`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:218-226` |
| `CRMB002` | 查詢前 | 分配期別 + 已指派歸類(轉出)必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:156-157` |
| `CRMB002` | 查詢前 | 兩組金額起迄成對與大小 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:170-204` |
| `CRMB002` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:214-217` |
| `CRMB002` | 執行前 | 轉入單位不可等於轉出單位 | — | **記錄不擋**(2016 起被註解) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` |
| `CRMB003` | 查詢前 | 分配期別必填 | 缺 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:180` |
| `CRMB003` | 查詢前 | 主管(`SAL_CD = 'A'`)必須填轉出單位 | 未填 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:197-202` |
| `CRMB003` | 查詢 | `F_TA_GET_EMPS` 的 INNER JOIN | 對不上 | **過濾(無提示)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:98` |
| `CRMB003` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:252-256` |
| `CRMB003` | 執行前 | 轉入業務員不可等於轉出業務員 | 成立 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:258-262` |
| `CRMB003` | 執行前 | 轉入業務員不可為離職員工 | — | **記錄不擋**(只有註解,靠下拉擋) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:246-247` |
| `CRMB004` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB004.cs:206-210` |
| `CRMB005` | 查詢前 | (區塊是空的) | — | **記錄不擋** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:80-84` |
| `CRMB005` | 查詢 | 姓名 / 地址 / 統編為 `NULL` | 成立 | **過濾(無提示,三值邏輯)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-105` |
| `CRMB005` | 執行前 | 至少勾一筆 | 零勾選 | 阻擋 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:88-92` |
| `CRMB002`–`CRMB005` | 執行 | 實際影響筆數為 0 | 成立 | **記錄不擋**(硬寫 `i = 1`) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227` |

## 7. 報表(R)

### 7.1 一覽

| rpt | 對應畫面 | 取數來源 | 結果集 | 主要參數 |
|---|---|---|---|---|
| `CRMR001RPS` | `CRMR001` | `S_TA_CRMR001_GET` | `CRM007A` | 分配序號、資料來源、最後交易歸屬 / 單位、指派單位 / 業務員、已指派否、受益人類別、特殊名單、兩組金額起迄、排序、**登入者員工代碼** |
| `CRMR002RPS` | `CRMR002` | `S_TA_CRMR002_GET` | `CRM007A` | 同上,但把「已指派否」換成「有無意願申購」(`RESULT`) |
| `CRMR003RPS` | `CRMR003` | `S_TA_CRMR003_GET` | `CRMR003` | 分配序號、資料來源、交易日期起迄、指派單位、**登入者員工代碼** |
| `CRMR004RPS` | `CRMR004` | `S_TA_CRMR004_GET` | `CRMR004` | 同 `CRMR003` 再加指派業務員 |
| `CRMR005RPS` | `CRMR005` | `S_TA_CRMR005_GET` | `CRMR005` | 同 `CRMR004` |
| `CRMR006RPS1` / `RPS2` / `RPS3` | `CRMR006` | `S_TA_CRMR006_GET` | `CRMR006_1` 或 `CRMR006_2` | 報表類型、分配序號、資料來源、指派單位 / 業務員、有無意願申購、再聯絡日期、聯絡結果、**登入者員工代碼** |
| `CRMR007RPS1` | `CRMR007` | `S_TA_CRMR007_GET` | `CRMR007_1` | 通話日期起迄、通話種類、潛在客戶姓名起迄、建立者、**登入者員工代碼** |
| `CRMR008RPS1` / `RPS2` | `CRMR008` | `S_TA_CRMR008_GET_1` 或 `_GET_2` | `CRMR008_1` 或 `CRMR008_2` | 索取日期起迄、索取種類、潛在客戶姓名起迄、建立者(**沒有登入者員工代碼**) |

**母體的 11 支 `.rpt` 與程式裡的 11 個 `ReportClass` 一對一,沒有孤兒、沒有缺件。**這與 CAS 那邊(19 支 rpt 有一支零引用)不同。

### 7.2 八支 PO 的共同骨架

八支 `CRMRnnn_PO.GetData` 逐行對應,只差 SP 名字與參數:

| 步驟 | 做什麼 | 錨點(以 `CRMR003` 為例) |
|---|---|---|
| 1 | `model.Utility.Result.Clear()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:50` |
| 2 | `tran = m_db.BeginTransaction()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54` |
| 3 | `GetStoredProcCommand`,`CommandTimeout = 0` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:55-57` |
| 4 | 逐個 `AddInParameter`,`OutTB` 是 `RefCursor` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:59-66` |
| 5 | `LoadDataSet(cmd, model.DataEntity, tran, 表名)` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:68` |
| 6 | (部分)`TableHelper.SetNumberToZero` 把數值 NULL 補 0 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:72` |
| 7 | `tran.Commit()`,再依筆數 `AddResultRow(true/false, 0, "")` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:74-82` |
| 8 | `catch` → `tran.Rollback()` + `AddResultRow(false, 0, string.Empty)` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:84-89` |
| 9 | `finally` → `m_db.Dispose(tran)` 或 `m_db.Dispose()` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:90-95` |

**與 CAS 的三個差別:**

1. **CRM 的報表把 SP 包在明確交易裡**(第 2、7、8 步),CAS 沒有。純讀取的 SP 用交易沒有壞處,但 `tran.Rollback()` 在 `BeginTransaction()` 失敗時會 `NullReferenceException`(與 §6.3 同一類)。

2. **`CRMR001` / `CRMR002` 沒有交易**(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67`),其餘六支有。**八支裡兩支例外。**

3. **`catch` 的訊息全部是 `string.Empty`**(八支皆然,例 `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:103`)。SP 出錯時使用者拿到的是空白對話框,連「查無資料」都不是。與 `cas.md` 附錄 E.3 記的完全同型。

還有一條共同的:**八支全部 `CommandTimeout = 0`**,註解寫「此程式讓它永久跑」。使用者端沒有取消機制。

### 7.3 報表種類的三種分支寫法

| 畫面 | 分支邏輯 | 有沒有 `default` | 錨點 |
|---|---|---|---|
| `CRMR006`(UI) | `switch (rpt_type)` 三個 `case`(`"1"` / `"2"` / `"3"`) | **沒有** | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:193-204` |
| `CRMR006`(PO) | `(rpt_type == "1" \|\| rpt_type == "2") ? CRMR006_1 : CRMR006_2` | 三元式,`"3"` 落到 `_2` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:61-63` |
| `CRMR008`(UI) | `if (report_type == "0") … else …` | 有 `else` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:120-128` |
| `CRMR008`(PO) | `if (rpt_type == "0") … else …`,兩段各自跑一支 SP | 有 `else` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:57-125` |

**`CRMR006` 的 UI 沒有 `default`,所以報表類型若不是 1/2/3,`SetQueryParameters` 不會被呼叫 → `ReportClass` 是空的 → 伺服器端 `CRReportTransfer.TransferFileByte("")`。**目前 UI 是三選一的選項鈕,踩不到,但沒有防護。

`CRMR006` 的筆數判斷用的是 `CRMR006_1.Count + CRMR006_2.Count`(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:83`),兩張表相加——這是對的,因為只有一張會被填。`CRMR008` 則是兩段各自判各自的(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:80-91`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:112-123`)。

### 7.4 `CRMR008` 的列印後寫回

**這是八支報表裡唯一一支會寫 DB 的。**列印 / 預覽完成後,如果報表類型是 `"1"`(標籤),就把該批索取紀錄標記為已列印:

| 層 | 做什麼 | 錨點 |
|---|---|---|
| UI | `AfterPreviewOrPrintButtonClicked` 判 `REPORT_TYPE == "1"` 就打 `SetPRINT_LABEL` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:212-221` |
| PO | `UPDATE (SELECT … FROM CRM004A WHERE EXISTS (…)) SET PRINT_YN = 'Y'` | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:162-188` |

三件事:

1. **這段 SQL 是本模組寫得最乾淨的一段**:全部綁定參數、用 `(:X IS NULL OR 條件)` 的可選條件寫法(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:176-181`)。在 Oracle 裡空字串等於 `NULL`,所以 `GetParamValue` 回空字串時那個條件自動失效——**這個寫法只在 Oracle 成立,換 SQL Server 會全部變成「條件永遠不成立」**。

2. **它更新的範圍與剛才印的那份報表不保證一致。**報表資料來自 SP(`S_TA_CRMR008_GET_2`),而這段 UPDATE 是自己重新算一次「每個 `PR_NO` 的最新一筆索取」。SP 的邏輯看不到,兩邊有沒有對齊無法驗證。**假設**:對齊。依據是參數清單完全相同。

3. **`UPDATE (SELECT …) SET` 這種 updatable view 的寫法要求 Oracle 能判定 key-preserved**。`EXISTS` 子句不影響這一點,所以語法上沒問題,但這是全庫少見的寫法。

`SetPRINT_LABEL` 的 `catch` 同樣是 `tran.Rollback()` 不判 null + 空訊息(`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:211-215`)。

### 7.5 畫面端的檢核

| 畫面 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| `CRMR001` / `CRMR002` | 兩組金額起迄成對 + 大小 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:376-419` |
| `CRMR003` | 交易日期起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:220-235` |
| `CRMR004` / `CRMR005` | 同 `CRMR003` | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR004.cs:238-253` |
| `CRMR006` | **只有框架必填,沒有任何自訂檢核** | — | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:309-318` |
| `CRMR007` | 通話日期區間必填 + 起 ≤ 迄;姓名起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:247-280` |
| `CRMR008` | 索取日期區間必填 + 起 ≤ 迄;姓名起 ≤ 迄 | 阻擋 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:238-271` |

`CRMR007` / `CRMR008` 還有一個共同的自動帶值:**姓名(起)有值、姓名(迄)空白時,自動把迄填成起**(`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:95-99`),與 `CRMI001` 的起迄處理同一套。

### 7.6 登入者查詢權限:七支有、一支沒有

七支報表都會送 `QUERY_EMP_NO` 給 SP:

| 畫面 | 值從哪來 | 錨點 |
|---|---|---|
| `CRMR001` / `CRMR002` | `GetEMPInfo` 回來的 `EMP_INFO` 結果集的 `EMP_NO` 欄 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:215-216` |
| `CRMR003` / `CRMR004` / `CRMR005` / `CRMR006` / `CRMR007` | `GetEMP_INFO(this.UserID).Split(',')[1]` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:55-63` |
| **`CRMR008`** | **不送** | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:107-117`(只有 `CREATER`) |

`CRMR008` 是潛在客戶側的報表(不是指派名單側),所以沒有直銷業務員的可見範圍問題——這解釋得通。但 `CRMR007` 也是潛在客戶側的,它**有**送。**兩支同一條業務線的報表,一支有權限限制一支沒有**,要問清楚哪一個才是對的(附錄 E.4)。

`CRMR001` / `CRMR002` 用的是另一套:`GetEMPInfo` 打 PO 拿 `EMP_INFO`,取不到時 `NewEMP_INFORow()` 建一個空列(`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:56-63`),於是 `EMP_NO` 是空字串。**空字串送進 SP 之後會怎樣,取決於 SP;repo 內看不到。**

### 7.7 `.rpt` 檔的取得路徑

與 `architecture.md §6.5` 描述一致:`GetReportObject` 從用戶端傳來的 `ReportParameters[0].ReportClass` 取類別名,直接丟給 `CRReportTransfer.TransferFileByte(rpt)`(`Dev/ATLAS.CRM.Report/Source/Control/ReportControl.CRM/CRMR001_Ctl.cs:77-81`,八支逐字相同)。**伺服器不驗證用戶端傳來的類別名。**

11 支 `.rpt` 全部放在第七個專案 `Dev/ATLAS.CRM.Report/Source/CrystalReports/Report.CRM/`,以 `EmbeddedResource` 編進 `Vendor.Product.TA.Report.CRM` 組件。

### 7.8 與維護資料的關係

| 報表 | 讀的是哪張表 | 誰寫進去的 |
|---|---|---|
| `CRMR001`–`CRMR006` | `CRM007A`(經由 SP) | `CRMB001` 產生 / 上傳、`CRMB002` / `CRMB003` 指派、`CRMB004` 登錄結果 |
| `CRMR007` | `CRM006A` / `CRM0061A`(經由 SP,參數是通話日期與種類) | `CRMM003` |
| `CRMR008` | `CRM004A` / `CRM0041A`(經由 SP + 自己的 UPDATE) | `CRMM003` 寫、`CRMR008` 回寫 `PRINT_YN` |

**因為 SP 不在版控內,「報表上的數字」與「維護畫面存進去的值」之間的關係在 repo 內是斷的。**唯一看得到的一段對應是 `CRMR008` 的 `SetPRINT_LABEL`(§7.4)。

## 8. 跨模組共用

```text
[圖] 改 CRM003A、CRM001A、CRM002A、CRM007A、CRM006A、CRM0061A 會波及哪些畫面
圖中文字:CRM003A：靠 USAGE 切成兩個互不相見的世界 / CRM003A / 69 欄 四眼齊 四份 xsd / CRMM003 USAGE=1 / CRM 增刪改 / CASM001 USAGE=3 / CAS 增刪改 / TMKM001／TMKM002 / 唯讀 一處無 USAGE 條件 / CRM001A／CRM002A：CRM 維護，四個模組使用 / CRM001A CRM002A / 只有 CRMM001 寫 / BasicCRM_PO / 共用 PO SEARCHER 參數 / CLSM001 CLSM002 / CLSR001 CLSR002 唯讀 / DSMI001 DSMR007 / OFDI011 唯讀 / CRM007A：全庫三個下拉的資料來源 / CRM007A / CRMB001 產生／上傳 / GetAssignNo / 分配期別下拉 / ucAssignDeptNo / 指派單位下拉 / ucAssignEmpNo / 指派業務員下拉 / OFDI011 / 唯讀 / CRM006A／CRM0061A：CRM 寫，TMK 與 OFD 讀 / CRM006A CRM0061A / CRMM003 增刪改 / TMKM001 TMKM002 / 查統編的通話種類 / OFDI011 / join 取業務員代碼 / 覆核刪除整批 DELETE / 兩邊歷史一起不見 / 只有 CRM 用（改動只影響本模組） / CRM008A / 只有 CRMM002 / CRM004 / 只有 CRMM004 / CRM004A CRM0041A / CRMM003 + CRMR008 回寫
```

*圖:圖 5 跨模組影響面。橘框=本模組維護的表；灰虛框=本模組以外的入口或共用件；橘虛框=會咬人的行為。左邊的表只要加欄或改型別，箭頭所指的每個入口都要重編與回歸；CRM003A 的欄位定義散在四份 xsd，四份都要一起重生。*

這一章回答一個問題:**改 CRM 的表會打到誰、改別人的表會打到 CRM 哪裡。**

10 張表裡 CRM 自己的有 10 張(全部都是 CRM 開頭),但其中 5 張被別的模組讀:

| 表 | 誰也在用 | 怎麼用 | 詳見 |
|---|---|---|---|
| `CRM003A` | CAS(`CASM001` 增刪改)、TMK(`TMKM001` / `TMKM002` 唯讀) | 靠 `USAGE` 分治 | §8.1 |
| `CRM001A` `CRM002A` | 共用 PO `BasicCRM_PO`、CLS、DSM、OFD | 唯讀,當授權表 | §8.2 |
| `CRM006A` `CRM0061A` | TMK、OFD | 唯讀 join | §8.3 |
| `CRM007A` | 共用 PO `BasicCRM_PO`、共用控件、OFD | 唯讀 | §8.4 |
| `CRM008A` `CRM004` `CRM004A` `CRM0041A` | **無人** | — | — |

### 8.1 `CRM003A`:靠 `USAGE` 切成兩個互不相見的世界

| 誰 | 寫進去的 `USAGE` | 查詢時的條件 | 錨點 |
|---|---|---|---|
| `CRMM003` | `'1'` | `= '1'` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `CRMB005` | 不寫(只挑名單給 SP) | `= '1'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:79` |
| `CASM001` | `'3'` | `= '3'` | `Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM001.cs:58`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:224` |
| `TMKM001` | 不寫 | `= '1'`(唯讀 join) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` |
| `TMKM002`(通聯總覽第二路) | 不寫 | `= '1'` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:296` |
| `TMKM002`(取姓名) | 不寫 | **無 `USAGE` 條件**(`LEFT JOIN`) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` |
| `OFDI011` | 不寫 | **無 `USAGE` 條件** | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:232`、`:248` |

**結論與 `cas.md §8.2` 一致:資料層面互不干擾,schema 層面完全共用。**從 CRM 這一側補三點 CAS 那篇沒有的:

1. **`CRMB005` 的合併會動到 `USAGE = '1'` 的資料,但合併動作在 SP 裡。**如果 SP 沒有把 `USAGE` 條件帶進去,**合併可能會誤觸 CAS 的 `USAGE = '3'` 資料**。SP 不在版控內,無法驗證。這是 CRM 這一側最需要確認的跨模組風險。

2. **`CRM003A` 的欄位定義出現在四份 xsd**,不是 `cas.md §8.2` 說的三份:`Dev/ATLAS.CAS/Source/Entity/DataEntity.CAS/CASM001Model.xsd`、`Dev/ATLAS.CAS/Source/Entity/UIEntity.CAS/CASM001View.xsd`、`Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd`、`Dev/ATLAS.CRM/Source/Entity/UIEntity.CRM/CRMM003View.xsd`。**四份都要同步重生。**

3. **CRM 這邊的 xsd 宣告 69 欄,CAS 那邊的 Model xsd 也是 69 欄,但掃描索引記的是 72 欄**——多出來的 3 欄來自 `CASM001View.xsd`(CAS 的畫面多帶了三個顯示欄)。**兩邊的 View 不同構,Model 同構。**

| 改什麼 | 會打到誰 |
|---|---|
| 加欄位 / 改型別 / 改長度 | **四份 xsd 都要重生**,`CRMM003` 與 `CASM001` 兩支畫面都要回歸 |
| 改 PK(`PR_NO`) | `CRMM003` 取號、`CRMM003_PO` 的四句 `DELETE`、`CRMB005` 的合併字串、`CASM001`、`TMKM001` / `TMKM002`、`OFDI011` 全打到 |
| 改 `USAGE` 的值域 | **兩個模組的可見範圍同時翻掉**,而且 `TMKM002` 取姓名那段與 `OFDI011` 根本沒有條件,會突然看到對方的資料 |
| 只改 `USAGE = '1'` 那一批資料 | 只有 CRM 與 TMK 受影響 |

### 8.2 `CRM001A` / `CRM002A`:本模組維護、四個模組使用

**這兩張表是 CRM 對外影響最大的資產,而 CRM 自己一行都不讀。**

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMM001` | **唯一的寫入者**(增刪改) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:52-53` |
| `BasicCRM_PO.GetAssignEmpNo`(共用 PO) | 有 `SEARCHER` 參數時,加一段 `EXISTS (CRM001A INNER JOIN CRM002A …)` 限制員工下拉的範圍 | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:290-306` |
| `CLSM001` / `CLSM002` / `CLSR001` / `CLSR002` | 唯讀 | `Dev/ATLAS.CLS/SOURCE/UI/UI.CLS/CLSM001.cs`、`Dev/ATLAS.CLS.Report/Source/PO/ReportPO.CLS/CLSR001_PO.cs` |
| `DSMI001` / `DSMR007` | 唯讀 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs` |
| `OFDI011` | 唯讀 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` |

共用 PO 那段的判定邏輯要看清楚:

```
AND EXISTS (SELECT B.* FROM CRM001A A
             INNER JOIN CRM002A B ON B.EMP_NO = A.EMP_NO
                                 AND B.AGENT_ID = A.AGENT_ID
                                 AND B.AGENT_CODE = A.AGENT_CODE
             WHERE A.EMP_NO = '<登入者>'
               AND A.AGENT_CODE = B.AGENT_CODE
               AND (A.EMP_NO = B.INQ_EMP_NO OR B.INQ_EMP_NO = 'ALL'))
```

**這段有一個怪處:`EXISTS` 子查詢與外層完全沒有關聯欄位。**它只判斷「登入者在 `CRM001A` 有沒有設定,而且該設定的 `CRM002A` 明細裡有自己或 `ALL`」——**成立時外層一筆都不濾,不成立時外層全部濾掉**。也就是這段實際上是一個「有沒有權限」的開關,不是「可以看到誰」的過濾。

**後果:`CRMM001` 裡那個精心設計的「哪個機構的哪幾位員工」在共用 PO 這邊只被當成布林值用。**這可能是刻意簡化,也可能是條件漏寫。**假設**:漏寫。依據是 `CRM002A` 的 `INQ_EMP_NO` 欄位存在的意義就是列舉可查的員工,而這段只拿它跟登入者自己比對。要確認得看 `ucAssignEmpNo` 控件實際的下拉內容。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `CRM001A` `CRM002A` 欄位 | `CRMM001Model.xsd` / `CRMM001View.xsd` 要重生;`BasicCRM_PO` 那段手寫 SQL **不會自動同步** |
| 改 `INQ_EMP_NO` 的 `'ALL'` 保留字 | 共用 PO、`CRMM001` 的自動補值、`CRMM001p0` 的預設勾選三處都要改 |
| 清掉某個員工的 `CRM001A` 資料 | 那個員工在 **CLS / DSM / OFD / CRM 報表的業務員下拉** 會整個看不到資料 |
| 改 `CRMM001` 的「自動補 `ALL`」行為 | 同上,而且是無聲的權限放寬 / 收緊 |

### 8.3 `CRM006A` / `CRM0061A`:TMK 與 OFD 讀,CRM 寫

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMM003` | 增刪改(明細) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:67-68` |
| `CRMM003`(覆核刪除) | **實體 DELETE 該客戶的全部明細** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:111-118` |
| `TMKM001` / `TMKM002` | `CRM0061A` join `CRM003A` join `COD006A`,查某統編的通話種類 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:328-331` |
| `OFDI011` | `CRM006A` / `CRM0061A` join `CRM003A` 取業務員代碼 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:232`、`:248` |
| `CRMR007` | 經由 `S_TA_CRMR007_GET`(版控外) | — |

**要注意的是覆核刪除那段。**它直接 `DELETE CRM006A WHERE PR_NO = '…'`,而 TMK 與 OFD 的畫面是靠 `CRM0061A`.`PR_NO` join 回 `CRM003A` 的。**刪一個潛在客戶會讓 TMK / OFD 那邊的歷史查詢少掉資料,而且沒有任何保護與提示。**

### 8.4 `CRM007A`:共用控件的資料來源

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| `CRMB001`–`CRMB004`、`CRMI001`、`CRMR001`–`CRMR006` | 寫 / 讀 | §6、§7 |
| `ucAssignDeptNo`(共用控件) | 「指派部門代碼,將會串接 `CRM007A` 的資料擷取部門欄位」(註解原話) | `Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignDeptNo.cs:49` |
| `ucAssignEmpNo`(共用控件) | 「屬於指派部門,將會串接 `CRM007A` 的部門代碼為查詢條件」 | `Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignEmpNo.cs:35` |
| `BasicCRM_PO`(共用 PO) | `GetAssignDeptNo` / `GetAssignEmpNo` / `GetAssignNo` / `GetLastDeptType` / `GetLastAgentCode` 五支都讀 `CRM007A` | `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:127-133`、`:249-253`、`:406-413`、`:468-472` |
| `OFDI011` | 唯讀 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs` |

**`CRM007A` 是全庫的「分配期別 / 指派單位 / 指派業務員」三個下拉的資料來源。**`GetAssignNo` 直接 `SELECT DISTINCT ASSIGN_NO, SOURCE_CODE, MAX(EXE_DATE) FROM CRM007A GROUP BY …`(`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:406-411`),所以:

- **`CRMB001` 的刪除功能一旦修好,下拉裡的期別會跟著消失。**

- **CSV 上傳一筆亂資料,分配期別下拉就多一個選項**,而且沒有任何畫面可以刪掉它(`CRMB001` 的刪除是空操作)。

### 8.5 共用的 UI 控件與下拉來源

| 控件 / 來源 | 用在哪 | 說明 |
|---|---|---|
| `ucAssignDeptNo` / `ucAssignEmpNo` | `CRMB002`–`CRMB004`、`CRMR001`–`CRMR006` | 吃 `SEARCHER` 屬性做權限過濾(§8.2) |
| `TrustAgentCodeDataSrc` | `CRMM002` 的機構 Searcher | 無原始碼,從呼叫端反推 |
| `GetDropDownDataSrc` / `GetDropDown9iDataSrc` | 各畫面的代碼下拉 | 兩套並存,`CRMM002` 同一個代碼 `445` 兩種都用到(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335`) |
| `ClientBizUtility.GetEMP_INFO` | `CRMM003`、`CRMI001`、`CRMB003`、`CRMR003`–`CRMR007` | 回傳逗號分隔字串,**全部靠位置取第 2 段**(附錄 E.6) |
| `UltraGridCheckedListManager` | `CRMM003` 的兩組大小類勾選 grid | **本模組自有**,放在 `Dev/ATLAS.CRM/Source/UI/UI.CRM/App_Code/UltraGridCheckedListManager.cs` |
| `SrNoCommentProcessor` | `CRMM003` 的跳號一覽表 | 無原始碼,從呼叫端反推;與 CAS 的 `CASM001` 用同一支 |
| `CRReportTransfer` | 八支報表的 `.rpt` 取得 | 無原始碼,從呼叫端反推 |

## 附錄 A. 資料表總表

| 表 | 欄位數(Model xsd) | 四眼欄位 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `CRM001A` | 20 | 有(全部有中文名) | CRM | `CRMM001` | — | 增刪改 |
| `CRM002A` | 19 | 有 | CRM | `CRMM001`(多筆版,也算主檔) | — | 增刪改;INSERT 是手寫的 |
| `CRM003A` | 69 | 有 | **CRM / CAS / TMK**〔共用〕 | `CRMM003` `CASM001` | — | 增刪改(限 `USAGE = '1'`);`CRMB005` 交給 SP 合併 |
| `CRM004` | 34 | 有(無中文名) | CRM | `CRMM004`(vdb 表名 `CRMM004`) | — | 增刪改 |
| `CRM004A` | 27 | 有 | CRM | — | `CRMM003` | 增刪改;`CRMR008` UPDATE `PRINT_YN` |
| `CRM0041A` | 20 | 有 | CRM | — | `CRMM003` | 增刪改 |
| `CRM006A` | 21 | 有 | CRM〔被 TMK / OFD 讀〕 | — | `CRMM003` | 增刪改 |
| `CRM0061A` | 20 | 有 | CRM〔被 TMK / OFD 讀〕 | — | `CRMM003` | 增刪改 |
| `CRM007A` | 56 | 有(`STATUS` 的 Caption 抄錯) | CRM〔被共用 PO / 控件 / OFD 讀〕 | (無 M 畫面) | — | `CRMB001` INSERT、`CRMB002`–`CRMB004` UPDATE,**全部繞過四眼** |
| `CRM008A` | 21 | 有(無中文名) | CRM | `CRMM002` | — | 增刪改 |

只讀不寫的外部表(join 進來取說明用,本模組從不寫入):

| 表 | 取什麼 | 被誰 join | join 型態 |
|---|---|---|---|
| `COD009` | 員工姓名、部門、`UID_CODE` | `CRMM001` `CRMM003` `CRMI001` `CRMB002`–`CRMB004` | `LEFT`(`CRMI001` 用 `(+)`) |
| `COD006A` | OutBound 項目、通話種類、資料種類說明 | `CRMM003` | `INNER`(OutBound 那段)/ `LEFT`(歷史那段) |
| `OFD002` | 部門名稱 | `CRMM001` `CRMI001` `CRMB002`–`CRMB004` | `LEFT` |
| `OFD068A` | 銷售機構名稱 / 簡稱 | `CRMM001` `CRMM002` `CRMI001` `CRMB002`–`CRMB004` | `LEFT` |
| `OFD081A` | 基金簡稱 | `CRMI001` `CRMB003` `CRMB004` | `LEFT` |
| `OFD081V` | 基金簡稱(**`CRMB002` 用這個,不是 `OFD081A`**) | `CRMB002` | `LEFT` |
| `OFD303A` | 基金結帳控制 | `CRMB001` 的執行前檢核 | 直接 `SELECT` |
| `CTL014` | 資料來源說明(`442`)、頻率單位(`600`) | `CRMI001` `CRMM004` | `LEFT` |
| `BMS001A_V01` | 受益人姓名 / 地址 / 電話 | `CRMI001` `CRMB002`–`CRMB004` | `LEFT`(`(+)`) |
| `TMK001A` / `TMK_BF_V` | 電訪項目與電訪人員 | `CRMM003` | `INNER`(在子查詢內) |
| `SAL051` | 直銷職級與直銷部門 | `CRMB003` `CRMB004` 的 `GetDefault` | `LEFT` |
| `TA_AA_USER` / `AA_USER` | 平台使用者中文名 | `CRMM003` `CRMI001` | `LEFT`(`(+)`) |

非實體結果集(不是資料表)共 15 個,清單見 §2.3 最後一節。

## 附錄 B. SP / Function / Trigger / View

**`DB/` 裡屬於本模組的 SP / Function / Trigger / View 是 0 支。**掃描母體(`docs/_candidates/crm.md` 第 3 節)是空表,`DB/SP/`、`DB/Function/`、`DB/Trigger/`、`DB/View/` 四個資料夾裡沒有任何檔名含 `CRM` 的檔案。

但程式確實呼叫了 **11 支版控外的 DB 物件**:

| 物件 | 類 | 被誰呼叫 | 用途 | 呼叫點錨點 |
|---|---|---|---|---|
| `S_TA_CRMB001_EXCUTE` | SP | `CRMB001` | 依規則產生 / 刪除分配名單 | **呼叫整段被註解**;`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-205` |
| `S_TA_CRMB001_GET` | SP | `CRMB001` 的「產出客戶名單」 | 產 Excel 用的資料 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:368` |
| `S_TA_CRMB005_EXCUTE` | SP | `CRMB005` | 合併重複潛在客戶 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:156` |
| `S_TA_CRMR001_GET` | SP | `CRMR001` | 指派單位明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67` |
| `S_TA_CRMR002_GET` | SP | `CRMR002` | 指派業務員明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR002_PO.cs:66` |
| `S_TA_CRMR003_GET` | SP | `CRMR003` | 追蹤彙總-單位別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:55` |
| `S_TA_CRMR004_GET` | SP | `CRMR004` | 追蹤彙總-業務員別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR004_PO.cs:55` |
| `S_TA_CRMR005_GET` | SP | `CRMR005` | 追蹤明細-業務員別 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR005_PO.cs:55` |
| `S_TA_CRMR006_GET` | SP | `CRMR006` | 聯絡結果統計 / 明細(三合一) | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR006_PO.cs:55` |
| `S_TA_CRMR007_GET` | SP | `CRMR007` | 客戶通話記錄明細 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR007_PO.cs:58` |
| `S_TA_CRMR008_GET_1` / `S_TA_CRMR008_GET_2` | SP | `CRMR008` | 索取資料明細 / 標籤 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR008_PO.cs:64`、`:96` |
| `F_TA_GET_EMPS` | Function(TVF) | `CRMI001`、`CRMB003` | 回傳登入者可見的「部門+員工」清單 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:80` |

另有三個**檢視表**被 join 但不在索引內:`BMS001A_V01`(受益人)、`OFD081V`(基金)、`TMK_BF_V`(電訪戶號)。

**這 11 支 + 3 個檢視表的內容在 repo 內完全看不到。**要知道規則一到規則五怎麼篩客戶、合併怎麼處理明細撞號、`F_TA_GET_EMPS` 回傳的第一個字元是什麼,只能去 Oracle 撈 `USER_SOURCE`,或問 DBA。

**`F_TA_GET_EMPS` 是本模組最關鍵的單一外部相依**:它決定 `CRMI001` 與 `CRMB003` 使用者看得到什麼,而且是用 INNER JOIN 串的——回空集合就等於查無資料(§5.3)。

## 附錄 C. 代碼對照

`STATUS` 與本模組自訂旗標值見 §2.5,不重複。這裡補下拉選單的代碼來源編號。

| 代碼 | 來源 | 用途(取自程式上下文) | 用在哪 |
|---|---|---|---|
| `062` | `GetDropDownDataSrc` | 銷售機構區別碼 | `CRMM001` `CRMM002` |
| `445` | `GetDropDownDataSrc` / `GetDropDown9iDataSrc` | 部門歸屬種類 | `CRMM002`(**同一個代碼兩種 DataSrc**) |
| `442` | `CTL014` 的 `SOURCETYPE` | 資料來源(`SOURCE_CODE`) | `CRMI001` |
| `600` | `CTL014` 的 `SOURCETYPE` | 計算頻率單位(`FREQ_UNIT`) | `CRMM004` |
| `P5` | `COD006A` 的 `CODE_SORT` | OutBound 項目說明 | `CRMM003` |
| `1C` | `COD006A` 的 `CODE_SORT` | 通話種類代碼小類 | `CRMM003` 的歷史查詢 |
| `11` | `COD006A` 的 `CODE_SORT` | 需求資料種類代碼 | `CRMM003` 的歷史查詢 |
| `438` | `GetDropDownDataSrc` | DM寄發碼 | **`CRMM003`,已於 2020-03-30 註解** |
| `439` | `GetDropDownDataSrc` | 寄發廣告EMAIL | **同上** |

**兩件要記住的:**

1. **同一個代碼分類 `445` 在 `CRMM002` 用了兩種 DataSrc。**查詢 grid 與維護下拉用 `GetDropDown9iDataSrc`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64`),查詢條件與維護欄位用 `GetDropDownDataSrc`(`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335-336`)。**兩個資料來源的選項若不一致,grid 與欄位會顯示不同的文字。**

2. **`CRMM003` 的 `CALLIN_CODE` / `REQ_DATA_CODE` 的下拉不是走代碼分類,而是走自訂的大小類勾選 grid**(`UltraGridCheckedListManager`,`Dev/ATLAS.CRM/Source/UI/UI.CRM/App_Code/UltraGridCheckedListManager.cs`)。歷史查詢那邊才用 `COD006A` 的 `1C` / `11` 去翻中文。**兩邊的代碼來源不同,要一起確認。**

## 附錄 D. 掃描母體與覆蓋率

母體來源:`docs/_candidates/crm.md`(由 `atlas_scan.py --module CRM` 產生)。

| 類別 | 母體 | 本文提及 | 覆蓋率 |
|---|---|---|---|
| 畫面 | 18(B 5 / I 1 / M 4 / R 8) | 18 | 100% |
| 實體表 | 6 | 6 | 100% |
| SP / Fn / Trigger / View | 0 | —(版控外的 11 支另列於附錄 B) | — |
| `.rpt` | 11 | 11 | 100% |
| WindowsService | 0 | — | — |

**沒有未提及的物件。**但母體本身有兩處要註記:

| 項目 | 狀態 | 處置 |
|---|---|---|
| `CRM001A` `CRM002A` `CRM007A` `CRM008A` | **不在**母體的實體表清單內,但它們是本模組確實維護的實體表 | 本文在 §0.2、§2.1、附錄 A 補上,並說明掃描器為何漏掉 |
| `CRM004` 的「欄位 0」 | 母體記 0 欄 | 實際 34 欄。掃描器以 **DB 表名** 去索引 xsd 的表名,而 `CRMM004Model.xsd` 裡那張表叫 `CRMM004`,所以對不上(§0.5) |
| `CRM006A` 記 9 欄、`CRM004A` 記 10 欄 | 母體的欄位數偏低 | 實際 21 / 27 欄。掃描器的 xsd 解析只認 `type=` 屬性的欄位,**用 inline `simpleType` 宣告長度的字串欄位全被漏掉**。可用 `py -V:3.12 docs/tools/atlas_scan.py --table CRM006A` 複驗:列出來的 9 欄全是 `decimal` / `dateTime` / `base64Binary`,一個 `string` 都沒有 |

本文另外提及但不屬於 CRM 母體的物件(唯讀 join、跨模組對照或版控外),列出以免被當成漏網:

- 表 / 檢視表:`COD009` `COD006A` `OFD002` `OFD068A` `OFD081A` `OFD081V` `OFD303A` `CTL014` `BMS001A_V01` `TMK001A` `TMK_BF_V` `SAL051` `TA_AA_USER` `AA_USER`

- 畫面:`CASM001` `TMKM001` `TMKM002` `CLSM001` `CLSM002` `CLSR001` `CLSR002` `DSMI001` `DSMR007` `OFDI011` `CASI001` `CASB001` `CASM006` `DSMM001`

- 彈出視窗:`CRMM001p0` `CRMM003p0` `CRMM003p1`(母體不含 `p` 系列)

- DB 物件:附錄 B 的 11 支

## 附錄 E. 讀本文時要注意的地方

按「讀碼時會被騙的方式」分類。嚴重度:**高** = 會造成錯誤資料或錯誤決策;**中** = 會誤導維護者;**低** = 髒但無害。

### E.1 被註解掉但外殼還在的功能

**本模組最大的一類,而且比 CAS 嚴重——這裡被註解掉的不是檢核,是主要功能本身。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| **`CRMB001` 的「產生 / 刪除名單」SP 呼叫整段被註解**,按鈕、檢核、參數組裝全部還在 | 按執行鈕什麼都不會發生,而且**沒有成功也沒有失敗訊息**(`Result` 被 `Clear()` 之後沒再塞) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:195-214`、`:77` | **高(本模組最嚴重)** |
| `CRMB001` 的「刪除時檢核有無名單可刪」被註解 | 刪除作業沒有前置檢核 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:302-306` | 中 |
| `CRMB001` 的「刪除時已有聯絡資訊,詢問是否全刪」被註解,但 UI 端讀 `WARNING` 參數的程式還在 | 那段詢問**永遠不會出現**,是死碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:311-332` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:128-136` | 中 |
| `CRMM003` 的 `CRM004A` / `CRM0041A` 取數被加上 `WHERE 1=2` | 索取資料明細**永遠是空的**,而且沒有任何註解說明 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:436`、`:454` | **高** |
| `CRMM003` 的通訊地址 14 個細欄回填整段被註解 | 地址只存 `MAIL_ADDR` 一欄,郵遞區號 / 縣市 / 路名等全部不會被寫入 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:483-496` | 中 |
| `CRMM003` 的 DM寄發碼 / 寄發廣告EMAIL 下拉被註解,欄位改由拒絕行銷勾選反推 | 使用者無法直接設定這兩個欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:153-157`、`:527-542` | 低(有替代邏輯) |
| `CRMM003_PO` 的 `BuildDetailSQLString` 有一整段 130 行的舊版取數被 `/* */` 包起來 | 讀碼時會誤以為明細有「歷史模式 / 一般模式」兩條路 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:460-626` | 中 |
| `CRMM003_PO` 的 `GetOutBoundSQLString` 有一整段舊版 TMK 兩表 join 被註解 | 同上;現行版本改用 `TMK_BF_V` 檢視表 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:650-685` | 低 |
| `CRMM003_PO` 宣告了 `CRM0061A_HIS` / `CRM0041A_HIS` 兩張明細但被註解 | 兩張表在現行系統不存在 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:69`、`:72` | 低 |
| `CRMB002` 的「轉入單位不能等於轉出單位」被註解(2016-08-16) | 可以把名單轉給自己;註解說明了原因,是刻意的 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB002.cs:218-223` | 低 |
| `CRMB003` 的註解列了 8 條檢核,第 4、7 兩條沒有實作 | 「轉入業務員必須輸入」「不可為離職員工」靠框架與下拉擋,程式端沒有 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:184-190`、`:246-247` | 中 |
| `CRMI001_PO` 的介面有三個方法宣告被註解(`ExecuteNonQuery` / `GetEmpNo` / `GetUidCode`),但實作還在 | 兩支 `public` 方法**呼叫不到**,是死碼 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:26-30`、`:529`、`:560` | 低 |
| `CRMI001` 的員工白名單檢核整段被註解,裡面的 5 個員工代號與 CAS 的 `CASI001_PO.cs:206` **完全相同** | 證明兩支 I 畫面同源;目前 CRM 這邊沒有白名單 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:444-453` | 低〔客戶特定〕 |
| `CRMM001` 的 `AfterModifyButtonClicked` / `AfterDeleteButtonClicked` 兩個事件處理器整個是空的(內容全註解) | 事件有掛但什麼都不做 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:248-277` | 低 |

### E.2 Oracle 三值邏輯造成的靜默過濾

**`欄 <> '值'` 或 `欄 = 欄` 在欄位為 `NULL` 時結果是 `UNKNOWN` 不是 `TRUE`,該列被靜默排除。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CRMB001` 的結帳檢核 `POST_CTL_CODE <> 'Y'` | **結帳旗標從沒被設定過(`NULL`)的基金會被當成已結帳放行**,名單可能在未結帳的資料上產生 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:265` | **高** |
| `CRMB005` 的重複判斷 `OTHER.PR_NAME = CRM003A.PR_NAME AND OTHER.MAIL_ADDR = …` | 姓名或地址為空(Oracle 裡空字串就是 `NULL`)的重複客戶**永遠找不出來** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` | **高** |
| `CRMB005` 的第二種合併 `OTHER.ID_NO = CRM003A.ID_NO` | 統編為空的重複客戶同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:102-105` | **高** |
| `CRMM004` 的區間重疊檢核 `CUS_LV <> :CUS_LV` | `CUS_LV` 是 PK 不會為 `NULL`,目前無害;但同一段的 `HAS_MF = :HAS_MF` 若某列的旗標為 `NULL` 就比不到 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:91-92`、`:112-113` | 中 |
| `CRMB005` 的 `OTHER.PR_NO <> CRM003A.PR_NO` | `PR_NO` 是 PK,無害,但寫法同型 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:93` | 低 |

### E.3 `catch` 吞例外 / 回傳值語意錯誤

**這一類最危險,因為它讓「檢核」在系統出問題時自動放行。**

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `intGetSRNO` 出錯回 `-1` 並把訊息塞進 `ref sErr`,呼叫端 `SetDetailSrNo` **兩個都不檢查** | **`-1` 被當成正常批次序號寫進 `CALLIN_SRNO` / `REQ_SRNO`(PK 欄位)** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:1043-1047` 配 `:234-241`、`:270-276` | **高(本模組最危險)** |
| `EXIST_EMP_NO` 的 `catch` 只 `Result.Clear()` **不再 `AddResultRow`**,UI 判 `Count > 0` | 「員工已建檔」檢核靜默放行 → 重複建檔 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:469-473` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM001.cs:554-556` | 高 |
| `IS_EXISTS` 出錯塞了訊息但**回傳 `false`**,UI 判 `== true` 才擋 | 「同種類機構重複」檢核靜默放行 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:170-176` | 高 |
| `IsValidAdd` 出錯回 `-1`,UI 判 `i == 0` | 方向相反:出錯時會**多問一次**「是否要繼續新增」,結果安全但訊息誤導 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:980-984` 配 `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1475-1480` | 中 |
| `GetUidCode` 判了 `ds.Tables.Count > 0` 卻直接取 `Rows[0]` | 查無資料 → `IndexOutOfRange` → 被 `catch` 吞成空字串(而且這支是死碼) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:575-577` | 低 |
| 八支報表 PO 的 `catch` 都是 `AddResultRow(false, 0, string.Empty)` | **SP 出錯時使用者拿到空訊息**,連「查無資料」都不是 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:101-105` | 高 |
| `CRMB002`–`CRMB005`、六支報表 PO 的 `catch` 直接 `tran.Rollback()` **不判 null** | `BeginTransaction()` 失敗時真正的錯誤被 `NullReferenceException` 蓋掉 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:235-237`、`Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:84-86` | 中 |
| `CRMB002` / `CRMB003` / `CRMB004` 把 `ExecuteNonQuery` 的影響筆數丟掉,硬寫 `i += 1`(`CRMB004` 寫成 `i = +1`) | `if (i == 0) throw` 是死碼,**更新 0 筆也算成功** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:220-227`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:207-214` | 高 |
| `CRMM003` 的覆核刪除四句 `DELETE` 也丟掉影響筆數 | 刪 0 筆也算成功 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:114-117` | 中 |
| `CRMM003` 的八個 `After*` 全部 `throw new ApplicationException("")`(空訊息) | 追不到是哪一步失敗 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:924` | 中 |
| `CRMB001` 的 `finally` 在沒有交易時直接 `m_db.Dispose()` | 釋放的是**共用的欄位物件**,同一個 PO 實例的下一次呼叫會用到已釋放的 `Database` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:222-227` | 中 |

### E.4 同一概念多套實作

| 概念 | 幾套 | 差在哪 | 錨點 |
|---|---|---|---|
| `DoValidate()` 的回傳語意 | 2 | `CRMM004` **回 `true` 代表有錯**;其餘七支畫面回 `true` 代表通過 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM004.cs:54` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:366` |
| 批次序號取號 | 2 | 畫面端 `GetSRNO`(出錯跳訊息);伺服器端 `intGetSRNO`(出錯回 `-1` 照寫) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:729-785` vs `:1003-1050` |
| 「已指派」的判斷 | 2 | `CRMB002` 把空白也算未指派;`CRMB003` **空白算已指派** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:114` |
| `BF_NO` 的綁定型別 | 2 | `CRMB002` 綁 `Int32`,`CRMB003` / `CRMB004` 綁 `Varchar2` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:217` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:224` |
| 基金表 | 2 | `CRMB002` join `OFD081V`;`CRMB003` / `CRMB004` / `CRMI001` join `OFD081A` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:80` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:87` |
| 機構簡稱的 join 條件 | 2 | `CRMI001` **只 join `AGENT_CODE`**;三支 B 畫面 join `AGENT_ID` + `AGENT_CODE` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:102` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:88-89` |
| 執行者身分從哪來 | 2 | `CRMB002` 從 UI 傳的 `USER_ID` 參數;`CRMB003` / `CRMB005` 從 `PermissionInfo[0].UserID` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:190` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:197` |
| 報表交易處理 | 2 | 六支包交易;`CRMR001` / `CRMR002` 不包 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR003_PO.cs:54` vs `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:67` |
| 登入者員工代碼怎麼取 | 2 | `CRMR001` / `CRMR002` 走 `GetEMPInfo` 打 PO;其餘六處走 `GetEMP_INFO(...).Split(',')[1]` | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR001.cs:56-63` vs `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:55-63` |
| 報表的查詢權限 | 2 | 七支送 `QUERY_EMP_NO`,`CRMR008` 不送 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR007.cs:110` vs `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR008.cs:107-117` |
| 代碼分類 `445` 的 DataSrc | 2 | `GetDropDown9iDataSrc` 與 `GetDropDownDataSrc` 並用 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:64` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM002.cs:335` |
| 「一群裡取第一筆」的排序 | 2 | `CRMM001` 只用三個日期;`CRMM002` 日期後再加機構欄 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:253` vs `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:90-91` |
| 重複客戶的分組鍵 | 2 | SQL 用欄位 `=` 比對;UI 用 `(PR_NAME + "_" + MAIL_ADDR).Trim()` 當 group key | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:92-95` vs `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB005.cs:235-241` |
| 區間重疊的判斷 | 1(但不完整) | **新區間完全包住既有區間時判不出來**,兩個客戶等級會同時命中 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:93-94`、`:114-115` |

### E.5 寫死常數〔客戶特定〕

換站台**一定要逐條確認**。

| 寫死的東西 | 值 | 錨點 |
|---|---|---|
| `CRM003A` 的用途別 | `'1'`(CRM / TMK)/ `'3'`(CAS) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:467`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:329` |
| `CRM007A` 寫進去的 `STATUS` | `'301'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:163`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:480` |
| 直銷職級分級 | `A` 主管 / `B` 組主管 / `C` 業務員 / `D` 助理 / `Z` 未設定 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-348`、`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCRM_PO.cs:282` |
| 職級排序對照 | `TRANSLATE(…, 'BCADEFZ', '9876540')` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:298`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:280` |
| 三碼部門補碼規則 | `LENGTH(DEPT_NO) = 3` → 後面補 `'01'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:291-296` |
| 直銷部門取法 | `SUBSTR(SAL_DEPT_NO, 1, 3)` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:305` |
| `F_TA_GET_EMPS` 回傳值的處理 | `RTRIM(SUBSTR(DEPT_EMP_NO, 2))`——固定砍掉第一個字元 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:80` |
| `INQ_EMP_NO` / `AGENT_CODE` 的 `'ALL'` 保留值 | `'ALL'` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:337`、`Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:124` |
| CSV 上傳的欄位順序與欄數 | 固定 17 欄,依位置對映 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:194-230` |
| 被註解的 I 畫面白名單 | 5 個員工代號,與 CAS 的 `CASI001` 相同 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:448` |
| 代碼分類碼 | `P5` `1C` `11` `442` `600` `062` `445` `438` `439` | 附錄 C |

### E.6 位置取參數

「值不是從資料來的,是從**它在哪裡**推出來的」。改名字、改順序就壞,而且編譯不會報錯。

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| 八處把 `GetEMP_INFO` 的回傳字串用逗號切開**取第 2 段** | 回傳格式一改,`CRMI001` 與 `CRMB003` 直接查無資料、`CRMM003` 的 `EMP_NO1` 寫空白;而且沒有長度檢查,空字串會 `IndexOutOfRange` | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:205`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:456`、`Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB003.cs:87`、`Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR003.cs:59` | **高** |
| `F_TA_GET_EMPS` 回傳值固定砍第一個字元 | TVF 的回傳格式改一個字就全部對不上,而且是 INNER JOIN | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79` | **高** |
| CSV 上傳靠 `line[0]`–`line[16]` 的位置對映 | 欄位順序一換就全錯,而且不會報錯(型別轉換失敗的那兩欄才會) | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMB001.cs:196-230` | 高 |
| `CRMB001` 的 INSERT 把 `DATAID` 綁成 `:ASSIGN_NO` | 上傳的每一筆 `DATAID` 都等於分配序號,不是 `Guid` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:108`、`:142-143` | 中 |
| `CRMB001` 的 INSERT 參數來自 `DataTable` 的欄位迴圈 | **xsd 加欄位就會多綁一個 SQL 裡沒有的參數 → `ORA-01036`** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:80-105`、`:182-185` | 中 |
| `CRMM001` 手寫的 `CRM002A` INSERT 把欄位名寫死在字串裡 | xsd 重生不同步,改錯只有執行時才會炸 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:93-101` | 中 |

### E.7 SQL 層面的髒寫法

| 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|
| `CRMI001` 的 4 處起迄條件寫成 `> =` / `< =`(中間有空白) | **假設**整段 SQL 語法錯、被 `catch` 吞成「執行失敗」;而分配期別是必填,所以這支可能完全不能用(§5.3) | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:140`、`:150`、`:194`、`:204` | **高** |
| `CRMM003` 的 `GetHistory_Call_Req` 用分號串兩句 `SELECT` 丟給 ODP.NET | **假設** `ORA-00911`;若成立則「客戶歷史資料」永遠是空的 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:870`、`:892`、`:897` | **高** |
| `CRMI001` 的 20 組條件全部字串串接,**只有一半做了 `Replace("'", "''")`** | SQL 注入面;`QUERY_EMP_NO` 串進 TVF 也沒跳脫 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:79`、`:161`、`:194` | 高 |
| `CRMM003` 的客戶姓名 `LIKE N'%{0}%'` 字串串接 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:339` | 高 |
| `CRMM001` 的 `EXIST_EMP_NO` 用 `string.Format` 串 `EMP_NO` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM001_PO.cs:452` | 中 |
| `CRMB003` / `CRMB004` 的 `GetDefault` 把登入者代號串進 SQL 兩次 | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:300`、`:307` | 中 |
| `CRMB002` / `CRMB003` 的 `ASSIGN_DEPT_YN` / `SPC_YN` 條件用 `string.Format` | 同上 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:105`、`:112` | 中 |
| `CRMM003` 的覆核刪除 `DELETE {0} WHERE PR_NO = '{1}'` 串表名與值 | `PR_NO` 由系統取號,風險低但寫法髒 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:109`、`:113` | 中 |
| `CRMB002`–`CRMB004` 的 `SORT_ORDER` `switch` 沒有 `default` | 值不在 `0`–`5` 就整個沒有 `ORDER BY` | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB002_PO.cs:118-138` | 低 |
| `CRMB005` 的 `merge_type` `if / else if` 沒有 `else` | 值不是 `1` / `2` 就**回傳全部潛在客戶並當成重複清單** | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:89-107` | 中 |
| `CRMR006` 的 UI `switch` 沒有 `default` | `ReportClass` 會是空字串 | `Dev/ATLAS.CRM.Report/Source/UI/ReportUI.CRM/CRMR006.cs:193-204` | 低 |
| 十支 SP 全部 `CommandTimeout = 0` | 永不逾時,使用者端沒有取消機制 | `Dev/ATLAS.CRM.Report/Source/PO/ReportPO.CRM/CRMR001_PO.cs:69` | 中 |
| `CRMM004` 的兩段檢核 `cmd` 沒有 `using`(原本的 `using` 被註解) | 命令物件不釋放 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:83-84`、`:128` | 低 |
| `CRMB001` 的 INSERT 把所有參數綁成 `Varchar2` | 金額與日期靠 Oracle 隱式轉型,NLS 設定一改就可能錯 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB001_PO.cs:184` | 中 |

### E.8 其他讀碼陷阱

| 陷阱 | 說明 | 錨點 |
|---|---|---|
| `CRMI001` 的兩處 `if (控件 != null)` 而不是 `if (控件.Value != null)` | 條件永遠成立,最後交易日期(迄)與本次指派日期(迄)被無聲覆寫 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMI001.cs:138`、`:174` |
| `CRMM003` 查詢檢核裡 `utxtEMAIL_0.Text` 出現兩次 | 應該有一個是 `utxtCELL_PHONE_0`,所以**只填行動電話會被擋** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:260-261` |
| `CRMI001_PO` 的 `LAST_TRN_DATE_END` 區塊 `Find("EXE_DATE_END")` | 複製貼上沒改;`Row` 沒被用到所以目前無害 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMI001_PO.cs:221` |
| `CRMM003` 六條檢核的錯誤全掛在兩個 Email 控件上 | 按訊息會跳到錯誤的欄位 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:285`、`:312`、`:326` |
| `CRMM003` 第一條查詢檢核的訊息講戶號、控件掛通話日期 | 同上 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:222-223` |
| `CRMM003` 的「統一編號資料**過多**」訊息,條件是長度 ≤ 5 | 訊息與行為相反 | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1526-1530` |
| `CRMM002` 的「此類別已重複設定」訊息,條件其實不含類別欄 | 檢核比 PK 嚴格,訊息看不出來 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM002_PO.cs:154-155` |
| `CRMB004` 寫 `i = +1;`(一元正號)而不是 `i += 1;` | 結果一樣,但看起來像 typo | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB004_PO.cs:208` |
| `CRMB003` / `CRMB004` 的 `if (xSAL_CD == "C") { xIS_LOCK_EMP = true; }` | 上兩行已經是 `true`,這個分支什麼都沒做 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB003_PO.cs:342-345` |
| `CRMM004_PO` 第二段檢核多一句 `cmd.Parameters.Clear()`,第一段沒有 | `cmd` 是剛建出來的新物件,這句沒有作用 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM004_PO.cs:116` |
| `CRMM003_Ctl` 的 `CustomTransferViewToOracleModel` 的 `default` 分支寫成 `TransferDataSet(model.DataEntity, view.UIView, …)` | **方向反了**(其他分支是 `view → model`)。目前 `Action` 參數一定存在且值在列舉內,所以踩不到 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:220` |
| `CRMM003_Ctl` 在 VDB 轉換方法裡 `new CRMM003_PO()` 直接打 DB | 繞過 `DataAccessPool` 與交易,而且每次 `DataLoad` 都會多一次連線 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:152-156` |
| 十支 `_PO` 的介面註解都寫「覆核層級管理 PO 共用介面」 | 樣板複製沒改,與實際功能無關 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:23-25` |
| `CRMM003_PO` 建構子第一行是 `this.BeforeSelect += CRMM003_PO_BeforeSelect; ;`(多一個分號) | 無害,但顯示這段沒被審過 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMM003_PO.cs:46` |
| `CRMB005_PO` 的 `Execute` 宣告了 `int i = 0` 卻完全沒用 | 死變數 | `Dev/ATLAS.CRM/Source/PO/PO.CRM/CRMB005_PO.cs:155` |
| `CRMM003` 的「拒絕行銷」勾選框在編輯模式全部 disabled | **客戶事後要拒絕行銷,這支畫面改不了** | `Dev/ATLAS.CRM/Source/UI/UI.CRM/CRMM003.cs:1155-1158` |
| `CRM002A` 的 `EMP_NO` / `INQ_EMP_NO` 兩欄 Caption 對調 | 以程式為準:`EMP_NO` 是有權限的人 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM001Model.xsd` |
| `CRM007A` 的 `STATUS` Caption 寫成「資料識別碼」 | 那是 `DATAID` 的名字 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMI001Model.xsd` |
| `CRMM003Model.xsd` 五張表的 `REJECTDATE` Caption 都是「資料退回**者**」 | 應為「資料退回日期」;`CRMM001Model.xsd` 那兩張是對的 | `Dev/ATLAS.CRM/Source/Entity/DataEntity.CRM/CRMM003Model.xsd` |
| `CRM003A` 的 `HM_TEL_AREA` Caption 寫「公司電話區域碼」 | 應為住家 | 同上 |
| 四支 R 的 `CustomTransferSQLModelToView` 全部 `throw new NotImplementedException()` | 只支援 Oracle,沒有 SQL Server 路徑 | `Dev/ATLAS.CRM/Source/Control/Control.CRM/CRMM003_Ctl.cs:255-263` |

### E.9 標「假設」的地方一覽

本文所有需要現場確認的推論,集中在這裡:

| § | 假設 | 依據 | 怎麼確認 |
|---|---|---|---|
| §0.3 | 規則一到規則五的篩選邏輯全寫在 `S_TA_CRMB001_EXCUTE` 裡 | 被註解的呼叫只傳結算日與規則代碼兩個參數 | 查 SP;問 DBA |
| §1.5 | 「一期」的長度 | `CRM007A` 用 `ASSIGN_NO` 不用日期當 PK,三支 B 的預設值取最新一期 | 問使用者 |
| §2.5 | `'301'` 就是「已覆核 / 正式生效」 | CRM 與 CAS 兩個模組獨立寫死同一個值 | 反編譯 `EVAStatusCode` 或查資料庫 |
| §4.3 | `CRM004A` / `CRM0041A` 的 `WHERE 1=2` 是為了「索取頁一律新增不載入舊資料」 | 通話那組用 `CALLIN_DATE = SYSDATE` 達到類似效果 | 問使用者「開啟舊客戶時索取頁應該顯示什麼」 |
| §4.3 | `GetHistory_Call_Req` 的分號多句 SQL 會丟 `ORA-00911` | Oracle 語法規則、ODP.NET 不支援批次語句 | 連 DB 跑一次「客戶歷史資料」 |
| §5.3 | 五處 `> =` 會造成 Oracle 語法錯誤 | SQL 標準與 Oracle 詞法規則 | 連 DB 跑一次帶分配期別條件的 `CRMI001` 查詢 |
| §5.3 | `F_TA_GET_EMPS` 回傳值的第一個字元是某種前綴旗標 | 程式固定用 `SUBSTR(..., 2)` 砍掉它 | 看 Function 原始碼 |
| §7.4 | `CRMR008` 的 `SetPRINT_LABEL` 更新範圍與 `S_TA_CRMR008_GET_2` 印出來的一致 | 兩邊參數清單完全相同 | 看 SP 原始碼 |
| §7.6 | `CRMR001` / `CRMR002` 送空字串的 `QUERY_EMP_NO` 給 SP 時 SP 會當成「全部」 | 其餘畫面拿不到值時的行為是查無資料,兩者不一致 | 看 SP 原始碼 |
| §8.1 | `S_TA_CRMB005_EXCUTE` 合併時有帶 `USAGE` 條件 | 若沒帶會誤觸 CAS 的資料 | 看 SP 原始碼(**優先確認**) |
| §8.2 | 共用 PO 的 `EXISTS` 子句漏了與外層的關聯條件 | `CRM002A` 的 `INQ_EMP_NO` 存在的意義就是列舉可查員工,而該段只拿它跟登入者自己比 | 實測 `ucAssignEmpNo` 的下拉內容 |
| §3.1 | 四支 M 畫面的中文名 | 由主表欄位與彈出視窗標題推測,沒有選單表可對 | 看選單表 |
| §3.3 | 五支 B 畫面的中文名 | 由畫面標籤與 UPDATE 的欄位推測 | 看選單表 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。純程式碼閱讀彙整,未執行、未連 DB。畫面中文名待選單表回填(報表中文名已取自程式);版控外的 11 支 DB 物件內容未涵蓋;掃描母體漏掉的四張表已在本文補齊。 |

由 build_doc.py v2.0.0 於 2026-09-15 10:48 產生 · 標題 133 · 圖 5 · 表格 94 · 程式錨點 579 · § 連結 84 · 引用檢查：畫面 32（缺 0） · Table 17（缺 0） · Report 11（缺 0） · 結果集 19（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/dsm.md
============================================================

# ATLAS DSM 模組 全流程商業邏輯

> 產出日期:2026-09-14(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把資料模型搞清楚,之後 §3 的清冊配 §4 起的畫面章節就讀得動了。趕時間只讀四段:§0.2(這模組最反直覺的事)、§4 各節末的卡控總表、§8(跨模組)、附錄 E(踩雷)。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表標題與郵件內文**推測**,待選單表 / 對照表回填。ATLAS 沒有把畫面中文名放進版控,29 支畫面裡只有 4 個彈出視窗有 `this.Text`。 ⚠ **〔客戶特定〕**:部門代碼(`S` / `090` / `S01` / `S05` / `08001`)、員工代號(`101722`)、列印帳號(`ntaprt05`–`ntaprt11`)、券商代碼 `551`、退信信箱 `ta-it@example.com` 為本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:`OFD374A`(給 BMS / OFDI / RSP)、`DSM001A` / `DSM002A`(給 CAS)、`BMS906`(前綴不屬 DSM)、`SAL050` / `SAL051`(沒有對應模組)四組表跨界,改動要一起看(§8)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`。**不要整份讀**。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:DSM 管「直銷(自家業務員直接賣)」這條通路的五件事——業務組織怎麼編、業績目標訂多少、客戶歸誰、客戶怎麼移轉、業績與收入怎麼算,外加一整排把結果印出來的報表。**

推測依據五條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `SAL050` / `SAL051` 是「業務部門代碼」「部門屬性」「部門主管獎金計算類別」「業務屬性」「獎金制度」;`DSM001A` 是「業績年度」「營業收入」「新開百萬戶數」;`DSM905` 是「業績拆帳比例」「歸屬A業務員之業績上限」 | `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:19-21`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:46-51`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:63-65` |
| PO 內的原始註解 | 「`SAL051` 為直銷的員工範圍」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:112` |
| 郵件內文 | 「送簽來源:DSMM901 業務移轉申請－新增資料作業」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:101-110` |
| 報表標題 | 「直銷業務處 新開百萬客戶清冊」「直銷業務部實際營收達成表--月報」「業務員基金別餘額彙總日報表」「期間各業務單位淨申購/結存金額統計表」 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:429`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR004.cs:230`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010.cs:261`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR011.cs:262` |
| 彈出視窗標題 | 「業務移轉明細」「業務移轉報表」「E-mail備註」「拷貝作業」 | 四支 `yPopUpForm` 的 Designer,用 `grep -n "this.Text"` 取字串,不 Read Designer |

「DSM」三個字母的展開在 repo 內找不到定義,**不要猜**。本文一律用「直銷業務」描述它的範圍,這是從上表推出來的,不是官方名稱。

六條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主要資料 |
|---|---|---|---|
| A 業務組織 | 業務部門的屬性與主管獎金類別、部門底下有哪些人、每個人的業務屬性與獎金制度 | `DSMM050` | `SAL050` + `SAL051` |
| B 業績目標 | 每人 / 每單位 / 每人每基金型別的年度目標與月分配 | `DSMM001` `DSMM002` `DSMM003` | `DSM001A`+`DSM002A`、`DSM007A`+`DSM008A`、`DSM003A`+`DSM004A` |
| C 客戶歸屬與拆帳 | 受益人歸哪個業務員、公單怎麼跟業務員拆帳、離職業務的業績分攤比率 | `DSMM060` `DSMM903` `DSMM005` | `OFD374A`〔共用〕、`DSM905`+`DSM9051`、`DSM005A` |
| D 業務移轉 | 客戶(或個別申購書)從 A 業務員 / A 機構整批搬到 B,走四眼 + 寄信 + 執行 SP | `DSMM901` `DSMM902` | `DSM901`+`DSM902`、`DSM903`+`DSM904` |
| E 收入計算與查詢 | 每日算出每位業務員每檔基金的結存與管理費 / 手續費收入,再給查詢與 17 支報表用 | `DSMB001` `DSMI001` `DSMR001`–`DSMR013` | `DSM006A`(計算結果)+ 版控外的 SP |
| F 對帳單名單 | 業務員自己維護哪些客戶要寄月對帳單 | `DSMM906` | `BMS906`〔前綴不屬 DSM〕 |

### 0.2 這模組最反直覺的四件事

**(1) 16 張表裡有 4 張的前綴不是 `DSM`,其中兩張是別的模組的字頭。**

| 表 | 前綴屬於 | 主檔於 | 為什麼在 DSM |
|---|---|---|---|
| `SAL050` `SAL051` | **沒有任何模組**(全庫沒有 `ATLAS.SAL` 專案,也沒有 `SAL` 開頭的畫面代號) | `DSMM050` | 直銷的業務組織設定,唯一維護入口就在 DSM,見 §8.4 |
| `OFD374A` · `BMS906` | OFD · BMS | `DSMM060` · `DSMM906` | 受益人歸屬業務員(BMS 拿去當明細,§8.2);對帳單郵寄名單(BMS 側沒有任何畫面碰它,§8.3) |

**(2) 有一支維護畫面根本不走四眼引擎。**`DSMM906` 把 `Add` / `Update` / `Delete` 三個方法整個 override 成手寫 SQL,不寫 `STATUS` / `DATAID` / 四眼 13 欄(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-278`);`BMS906` 的 xsd 也確實沒有四眼欄位。**同一顆「新增」按鈕,在這支畫面按下去是直接進資料庫,沒有待驗證 / 待覆核。**

**(3) 兩支「業務移轉」畫面(`DSMM901` / `DSMM902`)的結構幾乎一樣,行為卻差三件事。**

| 面向 | `DSMM901`(戶號層) | `DSMM902`(申購書層) |
|---|---|---|
| 覆核通過後 | **不自動執行**,要人工按執行鈕 | **自動呼叫 `DoExp1()` 跑 SP**,且不寄「執行」通知信 |
| SP 有沒有錯誤回傳 | 沒有 OUT 參數,一律回「執行成功」 | 有 `strMsg` OUT,非空就 rollback 並顯示 |
| 移轉後業務員的檢核 | 只查「員工存在」 | 查「員工存在 + 屬於移轉後部門 + 未離職」 |
| 錨點 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:302-305`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:470-500`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:424-439` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:274-282`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:464-512`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:433-447` |

**(4) 同一顆「月分配」按鈕,三支畫面三種算法。**`DSMM001` 可分配月數是「13 − 起算月」,`DSMM002` 固定 12(所以會跨到次年),`DSMM003` 月數算「13 − 起算月」但補餘額的判斷式寫死 12。細節見 §4.1 / §4.2 / §4.3 與附錄 E3。

### 0.3 不管什麼

以下**不在** DSM 範圍內,看到相關需求要轉出去:

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料 | BMS | `BMS001A` 全部是 `JOIN` 取姓名 / 身分證 / 地址,DSM 沒有任何一行寫入;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| 員工主檔、部門、離職日 | COD | `COD009` 只被 join;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:127-128` |
| 部門名稱主檔 | OFD | `OFD002` 只被 join 取 `DEPT_SH_NM` / `DEPT_CH_NAME`;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127` |
| 銷售機構主檔 | OFD | `OFD068A` 與 view `OFD068A_V02` 只讀不寫;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141` |
| 申購 / 贖回交易本身 | OFD | `OFD221` `OFD221A` `OFD306` `OFD306A` 只讀;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:204-206` |
| 結帳控制 | OFD | `OFD303A` 只用來判斷「有沒有結帳」;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:185-189` |
| 查詢權限對照 | CRM | `CRM002A` 只被 `DSMI001` join;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |
| **收入數字怎麼算出來的** | **版控外的 SP** | `DSMB001` 只負責呼叫 `S_TA_DSMB001_EXCUTE_P01`,算式在 DB 裡;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:66-76`。repo 內**沒有**任何一行程式讀 `DSM905` 的 `RATE_A` / `RATE_B`,也沒有讀 `DSM005A` 的 `SHARE_RATE` 去做計算。**假設**:這些比率全部由 `S_TA_DSMB001_EXCUTE_P01` 在 DB 端套用,依據是 `DSMB001` 的檢核直接查 `DSM006A` 有沒有資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:160-171`),而 `DSM006A` 就是這支 SP 的產出 |
| 業務移轉實際搬資料 | **版控外的 SP** | `S_TA_DSMM901_EXE` / `S_TA_DSMM902_EXE`;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:477`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:472` |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 直銷業務員 | 維護自己客戶的對帳單寄送設定(`DSMM906`)、查自己的收入(`DSMI001`) | `DSMM906` 查詢無條件加上「`EMP_NO` = 登入者員編」(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125`);`DSMI001` 靠 `CRM002A` 決定看得到誰(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89`) |
| 直銷部門主管 | 當公單的預設歸屬人;`DSMM903` 開畫面就去撈業務屬性為 `A` 的在職者 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` |
| 業務助理 / 內勤 | 建業績目標(`DSMM001`–`DSMM003`)、建業務移轉申請(`DSMM901` / `DSMM902`)、跑收入計算(`DSMB001`) | 這幾支都是標準畫面,權限在程式內看不到 |
| 移轉流程的 E / V / A 三種角色 | 輸入 / 驗證 / 覆核,每一段各自收到不同收件人的通知信 | 角色代碼存在 view `DSMM901_V01` 的 `ROLE901` 欄;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:118-132` |
| 報表列印專用帳號 | `ntaprt05`–`ntaprt11` 這批帳號在 `DSMR008` 可以查全部部門 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:134-143`〔客戶特定〕 |
| 一位特定員工 | 員編 `101722` 不受部門限制,看得到全部 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:117-125`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:119-127`〔客戶特定〕 |

**除了上面這兩條寫死的白名單,本模組所有畫面的權限都不在程式碼裡。**看不到不代表沒有——功能權限由 PTPF 平台庫決定(`architecture.md §3.7`)。

### 0.5 全域開關

repo 內**沒有**任何 DSM 專屬的設定檔開關。`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔與主鍵,給框架做 grid 的 PK 檢查用 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:32`(`DSMM001`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:67`(`DSMM050`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:76`(`DSMM060`)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:108`(`DSMM906`) |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄位、順序為何 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:34`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:101` |
| `formstyle` | `DSMB001` / `DSMI001` 宣告為 `OneStep`;其餘 M 畫面不宣告 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:20`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:26` |

四個要記住的:

- **五支畫面的 `detailtable` 那行全部被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:33`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:42`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:51`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:68`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:109`),而且那五行被註解的內容**全都寫 `DSM002A`**,連 `DSMM050` 那一行也是——是從 `DSMM001` 複製樣板留下來的殘骸,**別當成事實**。實際的明細表以 PO 建構子為準(§2.1)。

- **`DSMM005` 的 `mastertable` 寫 `DSM005A`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:59`),PO 也確實宣告了,只是用多筆型的 `this.MasterTable.Add(...)` 寫法(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:47`)。掃描器只認 `this.MasterTable = new xTableMapping(...)`,所以母體把 `DSMM005` 判成「沒有主明細」。**設定檔與 PO 一致,母體才是缺的那一方**(附錄 D)。

- **`DSMM902` 的 `detailtable` 的 `pkey` 中間有一個空白**:`BATCHID,ALLOT_NO, ALLOT_SRNO`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:92`)。框架怎麼切這個字串無原始碼,**假設**是 `Split(',')` 之後不 `Trim`,那第三個 PK 名會變成前面帶一個空白而對不上欄位。依據是同檔其他六處 `pkey` 都沒有空白。

- **`DSMM903` 的主鍵含 `AGENT_CODE_LIKE`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:99`),而這個欄位的 Caption 直接寫「原銷售機構代碼LIKE用(固定S%)直鎖專用」(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:33`)。**一個永遠是常數的欄位被放進主鍵**,見 §4.9。

`.Report` 側的 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/App.config` 只宣告 `formstyle`,沒有主明細。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] DSM 模組全景：業務組織、業績目標、客戶歸屬與拆帳、業務移轉、收入計算、報表六條線
圖中文字:① 業務組織：全庫共用的員工編制,唯一維護入口在 DSM / DSMM050 / 業務部門與人員 SAL050/051 / SAL050 SAL051 / 無模組前綴 全庫共用 / 共用員工下拉 / V_SAL051 全庫都吃 / ② 業績目標：三支結構相同、算法各異的畫面 / DSMM001 / 員工年度目標 DSM001A / DSMM002 / 單位年度目標 DSM007A / DSMM003 / 員工x型別 DSM003A / CASM006〔CAS〕 / 同用 DSM001A/002A / ③ 客戶歸屬與拆帳 / DSMM060 / 受益人歸屬 OFD374A / DSMM903 / 公單拆帳 DSM905/9051 / DSMM005 / 離職業務分攤 DSM005A / BMSM001 BMSM006 / 借 OFD374A 當明細 / ④ 業務移轉：四眼 + 寄信 + 版控外的執行 SP / DSMM901 / 業務移轉 戶號層 / DSMM902 / 業務移轉 申購書層 / S_TA_DSMM901_EXE 等 / 版控外 SP / DSMM901_V01 / 通知信收件人 view / ⑤ 收入計算：全模組的匯流點,母體卻沒列到這張表 / DSMB001 / 收入計算 呼叫 SP / DSM006A / 每日業務員收入檔 / DSMI001 / 收入查詢 CRM002A 權限 / DSMR003 DSMR004 / 達成率報表 / ⑥ 報表與對帳單名單 / DSMM906 / 對帳單名單 BMS906 / DSMR001 ~ DSMR013 / 17 支 全走版控外 SP / 40 個 .rpt 在 repo / 另有 13 個引用不在
```

*圖:圖 1 DSM 全景。橘框=本模組的維護入口;灰虛框=別的模組借用同一張表;黑框=無原始碼或版控外的東西;橘虛框=行為含寫死值〔客戶特定〕。六條線之間幾乎沒有程式呼叫,全靠表相連——尤其 ① 的 SAL051 決定了 ② 看得到哪些員工。*

看圖的四個重點:

1. **六條業務線之間幾乎沒有程式呼叫關係。**唯一的例外是 `DSMM902` 覆核後直接叫自己的執行流程(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:280`)。其餘全靠表相連:`DSMM001` / `DSMM003` 的取數 SQL 去 join `SAL051`(`DSMM050` 維護的),所以**改 `DSMM050` 的部門成員,會直接改變 `DSMM001` 查得到的員工集合**(§8.5)。

2. **`DSM006A` 是全模組的匯流點,但沒有任何一支畫面拿它當主檔。**它由 `DSMB001` 呼叫的 SP 產出,被 `DSMI001` 查詢、被大半報表統計。母體的 16 張表裡**沒有它**(它只出現在 `DSMI001Model.xsd`,被判成結果集),見附錄 D。

3. **報表那一排與上面五排在 repo 內是斷的。**17 支 R 畫面沒有一支引用 DSM 的維護 PO,資料全部來自版控外的 SP(§7)。也就是說**報表看到的數字,跟維護畫面寫進去的值之間的關係,在 repo 內查不到**。

4. **只有 `DSMM901` / `DSMM902` 會寄信,而且寄給誰由一支 view 決定。**`DSMM901_V01` 過濾 `DEPT = 'S'`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259`)〔客戶特定〕。

### 1.2 資料表關係

七組配對 + 三張沒有明細的孤兒:

| 組 | 主檔 | 明細 | 配對欄位 |
|---|---|---|---|
| 業績目標(人) | `DSM001A` | `DSM002A` | `QUO_YEAR` + `EMP_NO`,明細再加 `QUO_YYMM` |
| 業績目標(單位) | `DSM007A` | `DSM008A` | `QUO_YEAR` + `DEPT_NO`,明細再加 `QUO_YYMM` |
| 業績目標(人×基金型別) | `DSM003A` | `DSM004A` | `QUO_YEAR` + `EMP_NO` + `FUND_TYPE_SALE`,明細再加 `QUO_YYMM` |
| 業務組織 | `SAL050` | `SAL051` | `SAL_DEPT_NO`,明細再加 `EMP_NO` |
| 業務移轉(戶號層) | `DSM901` | `DSM902` | `BATCHID`,明細再加 `BF_NO` |
| 業務移轉(申購書層) | `DSM903` | `DSM904` | `BATCHID`,明細再加 `ALLOT_NO` + `ALLOT_SRNO` |
| 公單拆帳 | `DSM905` | `DSM9051` | `BF_NO` + `AGENT_ID` + `AGENT_CODE_LIKE`,明細再加 `EMP_NO_A` |
| 孤兒(無明細) | `OFD374A` · `BMS906` · `DSM005A` | — | 見 §2.1 |

### 1.3 主要維護畫面的四眼與卡控順序

三條要記住的:

- **卡控幾乎全在 UI 層。**10 支 M 畫面裡,只有 `DSMM901`(執行基準日 vs 結帳日)與 `DSMM906`(戶號歸屬)在 PO 的 `BeforeAdd` / `BeforeUpdate` 有伺服器端檢核,其餘全靠 `DoValidate()` 擋在按鈕之前。**繞過 UI 就沒有第二道防線**。

- **`DSMM050` 與 `DSMM903` 的 grid 逐列檢核只顯示訊息、不擋。**七處 `e.Cancel = true;` 全部被註解(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:373`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:382`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:394`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:413`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:422`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:431`),真正的閘門是存檔前的 `DoValidate()`,而它比逐列檢核寬。

- **`DSMM906` 沒有四眼。**它的按鈕直接落地,`architecture.md §3` 的狀態機在這支畫面完全不適用。

### 1.4 批次 / 報表資料流

一條直線:`DSMB001`(人工按執行,可跑一段日期區間)→ `S_TA_DSMB001_EXCUTE_P01` → 寫 `DSM006A` → `DSMI001` 查詢、`DSMR003` / `DSMR004` 統計。`DSMR003` / `DSMR004` 在列印前還會先呼叫一支 `Exists` 確認 `DSM006A` 這段區間有沒有資料,沒有就擋下列印(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:282-290`)。

### 1.5 一日作業泳道

程式內看不到排程:`DSMB001` 是 `OneStep` 人工畫面,repo 裡**沒有** DSM 的 WindowsService(母體第 5 節空白)。所以下面這條是**假設**,依據是 `DSMB001` 的檢核要求「該段日期的基金都已結帳」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:132-137`):

| 時點 | 誰 | 做什麼 |
|---|---|---|
| 前一日結帳完成後 | OFD | `OFD303A` 的結帳旗標變 `Y` |
| 當日上班 | 直銷內勤 | 開 `DSMB001`,輸入計算日期起迄,按執行 |
| 執行中 | 版控外的 SP | 重算 `DSM006A`(已有資料會先跳「是否確認要執行」的詢問) |
| 執行後 | 業務員 / 主管 | `DSMI001` 查收入、`DSMR010` 印日報表 |
| 不定期 | 內勤 | `DSMM901` / `DSMM902` 送業務移轉申請;`DSMM060` 設新客戶歸屬,公單客戶另外在 `DSMM903` 設拆帳 |
| 年初 / 每月 | 內勤 | `DSMM001`–`DSMM003` 設當年度目標;`DSMM005` 設當月離職業務分攤比率(可用拷貝一次產生多個月) |

## 2. 資料模型

```text
[圖] DSM 十六張表的主明細配對、主鍵組成,以及外部唯讀表
圖中文字:三組業績目標:主檔 + 月明細,六個指標欄位完全同名 / DSM001A / PK 年度+員工 / DSM002A / + 業績年月 / DSM007A / PK 年度+單位 / DSM008A / + 業績年月 / DSM003A / PK 年度+員工+型別 / DSM004A / + 業績年月 / DSM005A / PK 年月+部門 多筆型 / SAL050 SAL051 / PK 部門 / + 員工 / 兩組業務移轉 + 一組公單拆帳 / DSM901 / PK 期別 / DSM902 / + 戶號 / DSM903 / PK 期別 / DSM904 / + 申購書號+序號 / DSM905 / PK 戶號+機構別+LIKE / DSM9051 / + 業務員 / 三張沒有明細的孤兒,兩張前綴不屬 DSM / OFD374A〔共用〕 / PK 戶號 · 主檔在 DSMM060 / BMS906〔共用〕 / PK 戶號 · 無四眼欄位 / DSM006A / 母體沒列 · 批次產出 / 外部唯讀(join 進來,不屬本模組) / COD009 / 員工/離職日 / OFD002 / 部門名稱 / BMS001A / 受益人資料 / OFD068A(_V02) / 銷售機構 / CRM002A / 查詢權限
```

*圖:圖 2 資料模型。橘框=主檔;白框=明細;灰虛框=前綴不屬 DSM 的共用表;黑框=外部唯讀。實線箭頭=主明細(同一次四眼一起送審)。除了 BMS906 之外,十五張表都有完整的四眼 13 欄。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

以 PO 建構子為唯一事實來源(設定檔那份有五行被註解,見 §0.5):

| 畫面 | PO 基底 | 主檔 | 明細 | 錨點 |
|---|---|---|---|---|
| `DSMM001` | `BaseEVADaoPO` | `DSM001A` | `DSM002A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36` |
| `DSMM002` | `BaseEVADaoPO` | `DSM007A` | `DSM008A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36` |
| `DSMM003` | `BaseEVADaoPO` | `DSM003A` | `DSM004A` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:32-33` |
| `DSMM005` | **`BaseMultiRowEVADaoPO`** | `DSM005A`(多筆型) | —(grid 就是主檔本身) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:43-47` |
| `DSMM050` | `BaseEVADaoPO` | `SAL050` | `SAL051` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:39-40` |
| `DSMM060` | `BaseEVADaoPO` | `OFD374A` | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:33` |
| `DSMM901` | `BaseEVADaoPO` | `DSM901` | `DSM902` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:48-49` |
| `DSMM902` | `BaseEVADaoPO` | `DSM903` | `DSM904` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:47-48` |
| `DSMM903` | `BaseEVADaoPO` | `DSM905` | `DSM9051` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:38-39` |
| `DSMM906` | `BaseEVADaoPO`(但三個寫入方法全 override) | `BMS906` | —(建構子那行被註解) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:39-40` |
| `DSMI001` | **無基底**,自訂介面 | —(裸 DAO,見 `architecture.md §6.3`) | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:34` |
| `DSMB001` | **無基底**,自訂介面 | — | — | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:27` |

**`DSMM005` 是全模組唯一的多筆型 EVA 畫面。**它宣告的是 `MasterPKey` 兩欄(`QUO_YYMM` / `DEPT_NO`)加一張 `MasterTable`,grid 裡的每一列都是主檔的一筆,靠 `ROW_NUMBER() … R_NUM = 1` 把同一個年月 + 部門折成查詢結果的一列(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:129-141`)。

### 2.2 主鍵與四眼欄位

主鍵以 `App.config` 的 `pkey` 為準(框架用它做 grid 的 PK 檢查),PO 的 SQL 條件與之一致:

| 表 | 主鍵 | 四眼 13 欄 | 來源 |
|---|---|---|---|
| `DSM001A` | `QUO_YEAR` + `EMP_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:32` |
| `DSM002A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:215-224` |
| `DSM007A` | `QUO_YEAR` + `DEPT_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:41` |
| `DSM008A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:220-229` |
| `DSM003A` | `QUO_YEAR` + `EMP_NO` + `FUND_TYPE_SALE` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:50` |
| `DSM004A` | 主檔鍵 + `QUO_YYMM` | 有 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:210-215` |
| `DSM005A` | `QUO_YYMM` + `DEPT_NO` + `EMP_NO`(設定檔)/ 只有前兩欄(PO) | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:59` vs `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:43-44` |
| `SAL050` | `SAL_DEPT_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:67` |
| `SAL051` | `SAL_DEPT_NO` + `EMP_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:71` 的 `m_PkeyNotInMaster` |
| `OFD374A` | `BF_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:76` |
| `DSM901` | `BATCHID` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:83` |
| `DSM902` | `BATCHID` + `BF_NO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:84` |
| `DSM903` | `BATCHID` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:91` |
| `DSM904` | `BATCHID` + `ALLOT_NO` + `ALLOT_SRNO` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:92` |
| `DSM905` | `BF_NO` + `AGENT_ID` + `AGENT_CODE_LIKE` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:99` |
| `DSM9051` | 主檔鍵 + `EMP_NO_A` | 有 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:100` |
| `BMS906` | `BF_NO` | **無** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/App.config:108` |

**兩個要注意的:**

1. **`DSM005A` 的主鍵兩處不一致。**設定檔三欄、PO 兩欄。這不是筆誤——多筆型 EVA 的 `MasterPKey` 是「一組要一起送審的資料共用的鍵」,`EMP_NO` 是列層級的鍵,所以 UI 才另外把它放進 `m_PkeyNotInMaster`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:67`)。**兩邊都對,但只看一邊會誤解。**

2. **母體說只有 5 張表有四眼欄位,那是掃描器的誤判。**實測 16 張表裡 **15 張都有完整的 13 欄**,唯一沒有的是 `BMS906`。原因見附錄 D。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

只列業務欄,四眼 13 欄與 `DATAID` / `DATAFLAG` 全模組一致不重複列。

#### `DSM001A` — 年度業績目標(人層,26 欄,`DSMM001` 主檔)

| 欄位 | 中文名 |
|---|---|
| `QUO_YEAR` · `EMP_NO` · `BOUNS_ST_YYMM` | 業績年度 · 員工代碼 · 起算年月 |
| `QUO_MGR_TOT` · `QUO_RSP_NM_TOT` · `QUO_RSP_LNM_TOT` | 營業收入 · 定期(不)定額戶數-目標 · 定期(不)定額戶數-保守 |
| `QUO_RSP_AMT_TOT` · `QUO_MIL_NA_TOT` · `QUO_MIL_A_TOT` | 定期(不)定額扣款成功金額 · 新開百萬戶數 · 單筆申購交易百萬戶數 |
| `EMP_NAME` `DEPT_NO` | 員工姓名 / 部門代碼(**join 來的,不是 `DSM001A` 的實體欄**) |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:25-51`。

#### `DSM002A` — 月業績目標明細(24 欄,`DSMM001` 明細)

欄名把主檔的 `_TOT` 去掉就是:`QUO_MGR` / `QUO_RSP_NM` / `QUO_RSP_LNM` / `QUO_RSP_AMT` / `QUO_MIL_NA` / `QUO_MIL_A`,加上 `QUO_YYMM`「業績年月」。注意**明細的 `QUO_MIL_A` 中文名是「單筆申購交易百萬戶」,主檔是「單筆申購交易百萬戶數」**,差一個字(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:51` 對 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM001Model.xsd:149`)。

#### `DSM007A` / `DSM008A`、`DSM003A` / `DSM004A`、`DSM005A`

| 表(欄數) | 業務欄 | 中文名 |
|---|---|---|
| `DSM007A`(25)/ `DSM008A`(24) | 同 `DSM001A` 的六個指標 | 差別只在鍵:人層是 `EMP_NO`,單位層是 `DEPT_NO`「單位代碼」;join 來的名稱欄叫 `DEPT_NAME`「部門單位名稱」 |
| `DSM003A`(22)/ `DSM004A`(20) | `FUND_TYPE_SALE` · `QUO_NET_IN_TOT` / `QUO_NET_IN` · `SALE_DEPT_NO` | 基金型別 · 淨銷售金額(年度 / 月)· 部門代碼(join 自 `SAL051`) |
| `DSM005A`(21) | `QUO_YYMM` · `DEPT_NO` / `DEPT_SHNM` · `EMP_NO` / `EMP_NAME` · `SHARE_RATE` | 業績年月 · 部門代碼 / 部門名稱 · 員工代碼 / 員工名稱 · 離職業務分攤比率 |

#### `SAL050` / `SAL051` — 業務組織(20 / 22 欄,`DSMM050`)

| 欄位 | 中文名 | 備註 |
|---|---|---|
| `SAL_DEPT_NO` | 業務部門代碼 | 3 碼=大部門、5 碼=小部門,見 §4.5 |
| `DEPT_CD` / `MGR_BNS_KIND` | 部門屬性 / 部門主管獎金計算類別 | 下拉代碼分類 `458` / `459`;後者的 Caption 前面多一個空白 |
| `DEPT_CH_NAME` · `EMP_NO` / `EMP_NAME` | 業務部門名稱(join 自 `OFD002`)· 員工代號 / 姓名 |  |
| `SAL_CD` / `BONUS_TYPE` | 業務屬性 / 獎金制度 | 下拉代碼分類 `460` / `461`,值域見附錄 C |
| `TOT_ADD_AC` | (無 Caption) | 整數欄,repo 內**沒有任何程式讀寫它** |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:19-21`、`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd:46-53`。

#### `OFD374A` — 受益人歸屬業務員(22 欄,`DSMM060` 主檔)〔共用〕

| 欄位 | 中文名 |
|---|---|
| `BF_NO` | 受益人戶號 |
| `EMP_NO` | 員工代號 |
| `SAL_DEPT_NO` | 業務部門代碼 |
| `BELONG_DATE` | 歸屬日期 |
| `BF_NAME` `DEPT_SH_NM` `EMP_NAME` | 受益人中文姓名 / 部門中文簡稱 / 員工姓名(全部 join 來的) |

**業務欄只有四個**,其餘 18 欄是四眼與 join 欄。這一點對 §8.2 很關鍵。

#### 兩組業務移轉表(`DSM901`/`DSM902`、`DSM903`/`DSM904`)

| 表(欄數) | 業務欄與中文名 |
|---|---|
| `DSM901`(23) | `BATCHID` 期別 · `EXEDATE` 執行基準日 · `EXETYPE` 類別 · `EXESTATUS` 執行狀態 · `EXETIME` 實際執行時間 · `EXEUSER` 執行者 · `MEMO` 備註 · `EXESEQ`(無 Caption,第幾次執行,`DSMM901` 拿它當明細 `SEQ` 的預設值) |
| `DSM902`(31) | `SEQ` 序號 · `BF_NO` / `BF_NAME` 戶號 / 受益人姓名 · `AGENT_CODE` / `AGENT_NAME` / `EMP_NO` / `EMP_NAME` 移轉前四欄 · 同名加 `_N` 的移轉後四欄 · `EXEAUM` 移轉時庫存 · `EXESTATUS` 執行結果 |
| `DSM903`(22) | 比 `DSM901` 多一欄 `FUND_TYPE`「基金來源」,少 `EXETYPE` 與 `EXESEQ` |
| `DSM904`(40) | `DSM902` 的前後四欄 + `ALLOT_NO` 申購書號 / `ALLOT_SRNO` 申購序號 + 一整組從 `OFD221` / `OFD221A` 帶進來的顯示欄(`FUND_ID` `FUND_SH_NM` `ALLOT_DATE` `ALLOT_NAV_DATE` `NAV_B` `ALLOT_AMT` `ALLOT_UNIT` `UNIT_DEC` `DEC_LEN` `NAV_DEC`)+ **移轉前後各自的銷售機構別** `AGENT_ID` / `AGENT_ID_N`(`DSM902` 沒有這兩欄,`DSMM901` 固定只做直銷) |

`DSMM901Model.xsd` 內另有三張非實體表:`Total`(`CNT` 筆數、`AUM` 總庫存)、`MAIL`(`ROLE901`、`EMAIL`)、`AO`(`AGENT_CODE`、`EMP_NO`)。錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM901Model.xsd:117-141`。

#### `DSM905` / `DSM9051` — 公單拆帳(27 / 25 欄,`DSMM903`)

| 欄位 | 中文名(原文照抄) |
|---|---|
| `BF_NO` | 戶號 |
| `AGENT_ID` | 原銷售機構別(固定0) |
| `AGENT_CODE_LIKE` | 原銷售機構代碼LIKE用(固定S%)直鎖專用 |
| `AGENT_ID_B` / `AGENT_CODE_B` / `EMP_NO_B` | 公單銷售機構別 / 新銷售機構代碼:公單(預設SAL051部門主管)/ 新員工代碼:公單(預設SAL051部門主管) |
| `MAX_BAL_AMT_A` | 歸屬A業務員之業績上限, 若為0則無上限 |
| `RATE_B` / `RATE_A` | 業績拆帳比例B業務員 / 業績拆帳比例A業務員 |
| `AGENT_ID_A` / `AGENT_CODE_A` / `EMP_NO_A` | 新銷售機構別:業務員(固定0)/ 新銷售機構代碼:業務員(取SAL051業務屬性C)/ 新員工代碼:公單(取SAL051業務屬性C) |
| `SDATE` / `EDATE` | 計算日(起)/ 計算日(迄:預設29991231) |

錨點 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM903Model.xsd:25-66`。**`EMP_NO_A` 的 Caption 寫「新員工代碼:公單」是明顯的複製貼上錯誤**,從欄名與取數條件看應該是「業務員」(附錄 E)。

#### `BMS906` — 對帳單郵寄名單(25 欄,`DSMM906` 主檔)〔前綴不屬 DSM〕

**實體欄只有 7 個**:`BF_NO` / `EMP_NO` / `MAIL_YN`「是否郵寄」/ `REMARK`「備註」/ `UPD_USER`「更新者」/ `UPD_DATE`「更新日期」/ `UPD_TIME`「更新時間」——從 PO 的 INSERT 欄位清單反推(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:158-159`)。xsd 裡其餘 18 欄(`BF_NAME` / `ID_NO` / `BIR_DATE` / `AGENT_IN_LAW*` / `PERM_ADDR` / `MAIL_ADDR` / 各種電話 / `EMAIL1`)**全部 join 自 `BMS001A`**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:292-306`)。

**這張 DataTable 叫 `BMS906`,但它不是 `BMS906` 這張實體表。**改 xsd 的欄位跟改實體表是兩件事,見 §8.3。

#### `DSM006A` — 每日直銷及代銷業務員收入檔(34 欄,無畫面當主檔)

| 欄位 | 中文名 |
|---|---|
| `BAL_DATE` / `FUND_ID` / `AGENT_ID` / `AGENT_CODE` / `EMP_NO` | 結存日期 / 基金代碼 / 銷售機構別 / 銷售機構代碼 / 員工代碼 |
| `BAL_UNIT` / `NAV_B` / `BAL_AMT` | 結存單位數 / 淨值 / 結存金額 |
| `MGR_RATE` / `MGR_FEE` / `ALLOT_FEE` | 管理費率 / 管理費 / 手續費 |
| `TOT_FEE` | 總收入(**SQL 算出來的 `MGR_FEE + ALLOT_FEE`,不是實體欄**;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:72`) |
| `LEAVE_YN` | 離職否(**`DECODE` 算出來的**;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:76`) |

注意這張表的 `STATUS` 中文名被寫成「資料識別碼」(`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMI001Model.xsd` 內),其他表都寫「資料狀態碼」。

### 2.4 與其他模組共用的表

| 表 | 誰的 | DSM 的角色 | 別人怎麼用 | 詳見 |
|---|---|---|---|---|
| `DSM001A` `DSM002A` | DSM | `DSMM001` 主明細 | `CASM006` 也拿它當主明細 | §8.1 |
| `OFD374A` | OFD(前綴)/ DSM(唯一維護者) | `DSMM060` 主檔,唯一會寫的地方之一 | `BMSM001` `BMSM006` 條件掛明細;`OFDI011` 檢查歸屬;`RSPM004` 直接 INSERT | §8.2 |
| `BMS906` | BMS(前綴)/ DSM(唯一使用者) | `DSMM906` 主檔 | BMS 側沒有任何畫面 | §8.3 |
| `SAL050` `SAL051` | 無模組 | `DSMM050` 主明細 | `SAL051` 被 `DSMM001` `DSMM003` `DSMM901` `DSMM902` `DSMM903` 五支 join | §8.4 §8.5 |
| `OFD068A_V02`(view) | OFD | `DSMM901` 驗機構、`DSMM903` 取機構名 | `OFDI011` 也用 | §8.6 |

外部唯讀(只 join、從不寫):`COD009`、`OFD002`、`BMS001A`、`OFD068A`、`OFD303A`、`OFD306` / `OFD306A`、`OFD221` / `OFD221A`、`OFD081` / `OFD081A` / `OFD081V`、`FSK003`、`CRM002A`。

### 2.5 狀態碼(從程式反推,標來源)

#### `STATUS`(四眼引擎的狀態)

DSM 側出現**兩個字面值**,而且都是三碼:

| 值 | 出現處 | 語意(反推) |
|---|---|---|
| `203` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` 的 `this.strSTATUS != "203"` | **刪除待覆核**。註解寫「刪除覆核不執行SP」,所以覆核一筆 `203` 時不會去跑移轉 |
| 以 `3` 開頭 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:216` 的 `row.STATUS.StartsWith("3")` | **已覆核 / 正式生效**。這是「可以按執行鈕」的前提 |
| `301` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206` 直接塞給查詢結果的 `STATUS` 預設值 | 同上,`3` 開頭的其中一個 |

**這是 DSM 對 `architecture.md §3.10` 那個懸案的補充證據**:該節說全庫 SQL 裡的 `STATUS` 字面量掃出來是單字元 `'0'`~`'9'`,並**假設**單字元就是 `EVAStatusCode` 的實際值。DSM 這三處是三碼,而且語意可以對上「輸入 / 驗證 / 覆核」三段(`2xx` 待覆核、`3xx` 已覆核)。**假設**:本站台的 `STATUS` 是三碼,第一碼是階段、後兩碼是動作別;依據是 `203`(刪除待覆核)與 `301` 這兩個實際值以及 `StartsWith("3")` 的用法。要確定得反編譯 `Vendor.Product.TA.MappingCode` 或直接查資料庫。

#### `EXESTATUS`(移轉批次自己的執行狀態)

值由 `EXE_STATUS` 這組常數決定(無原始碼,`Vendor.Product.TA.MappingCode`):

| 常數 | 用在哪 | 錨點 |
|---|---|---|
| `EXE_STATUS.NonExecute` | 新增時強制設定;`DSMM901` / `DSMM902` 都一樣 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:68`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:67` |
| `EXE_STATUS.Executed` | 判斷「已執行」,決定要不要把 `EXESEQ` 加一、要不要鎖修改 / 刪除 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:207`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:190` |

UI 上顯示的中文由下拉代碼分類 **`322`**(主檔)與 **`300`**(明細)提供——**同一個 `EXESTATUS` 欄位,主檔與明細用兩份不同的代碼表**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:147-151`)。

#### 本模組自訂的旗標與代碼〔客戶特定〕

`SAL_CD`(業務屬性)、`DEPT_CD`(部門屬性)、`FUND_TYPE`(境內外)、`AGENT_ID`(銷售機構別)、`MAIL_YN`、`ROLE901`、`FUND_TYPE_SALE`、`EXETYPE` 與六組下拉代碼分類的值域與出處,整理在附錄 C,不在這裡重複。

## 3. 畫面清冊

29 支:M 10 · I 1 · B 1 · R 17。中文名一律待選單表回填,以下「用途(推測)」欄是本文的推測。

### 3.1 維護 M

| 代號 | 用途(推測) | 六層 | 主表 | 明細 | SP / Fn / View | rpt |
|---|---|---|---|---|---|---|
| `DSMM001` | 業務員年度業績目標與月分配 | 齊 | `DSM001A` | `DSM002A` | — | — |
| `DSMM002` | 業務單位年度業績目標與月分配 | 齊 | `DSM007A` | `DSM008A` | — | — |
| `DSMM003` | 業務員×基金型別年度淨銷售目標 | 齊 | `DSM003A` | `DSM004A` | — | — |
| `DSMM005` | 離職業務分攤比率(多筆型 EVA + 拷貝) | 齊 | `DSM005A` | —(多筆主檔) | — | — |
| `DSMM050` | 業務部門與人員設定 | 齊 | `SAL050` | `SAL051` | — | — |
| `DSMM060` | 受益人歸屬業務員 | 齊 | `OFD374A`〔共用〕 | — | — | — |
| `DSMM901` | 業務移轉申請(戶號層)+ CSV 匯入 + 寄信 + 執行 | 齊 | `DSM901` | `DSM902` | `S_TA_DSMM901_AUM` `S_TA_DSMM901_EXE` `S_TA_DSMM901_GET` · view `OFD068A_V02` `DSMM901_V01` | `DSMM901RPS` |
| `DSMM902` | 業務移轉申請(申購書層)+ CSV 匯入 + 覆核即執行 | 齊 | `DSM903` | `DSM904` | `S_TA_DSMM902_EXE` · view `DSMM901_V01` | — |
| `DSMM903` | 直銷公單拆帳設定 | 齊 | `DSM905` | `DSM9051` | view `OFD068A_V02` | — |
| `DSMM906` | 每月對帳單郵寄名單(業務員自維護) | 齊 | `BMS906`〔共用〕 | — | `S_TA_DSMM906_IMP` | — |

另有四個彈出子視窗(代號沿用母畫面,不列入 29):`DSMM005p0`(拷貝作業)、`DSMM901p0`(業務移轉明細)、`DSMM901p1`(業務移轉報表)、`DSMM901p2`(E-mail備註)。

### 3.2 查詢 I

| 代號 | 用途(推測) | 六層 | 資料來源 |
|---|---|---|---|
| `DSMI001` | 業務員每日收入查詢 | 齊 | `DSM006A` + `CRM002A` 權限對照 |

### 3.3 批次 B

| 代號 | 用途(推測) | 六層 | SP |
|---|---|---|---|
| `DSMB001` | 每日直銷及代銷業務員收入計算 | **缺 model / view** | `S_TA_DSMB001_EXCUTE_P01` |

**「缺 model / view」是真缺,不是命名問題。**`Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:38-39` 明白宣告 `ModelVDBType = typeof(BasicModelVDB)` / `ViewVDBType = typeof(BasicViewVDB)`,也就是**刻意用框架的泛用 VDB**,參數全靠 `Util.Parameters` 傳。對照 `architecture.md 附錄 D.4` 講的兩種假警報(`_9i` 檔名、`.Query` 專案的 `OracleDao` 命名),`DSMB001` **兩種都不是**:`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/` 底下沒有任何 `DSMB001*` 檔,也沒有 `_9i` 變體。

不過 UI 層另外做了一個東西:`Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs:8` 有一支手寫的 29 行 `DSMBViewVDB`(包一個 `DataSet`),`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:36` 用的是它。它繼承自 `BasicViewVDB` 所以傳得過去,只是那個 `UIView` 屬性從頭到尾沒人用。

### 3.4 報表 R

| 代號 | 用途(推測) | 六層 | SP | rpt(程式引用的) |
|---|---|---|---|---|
| `DSMR001` | 新開百萬客戶清冊 / 戶數統計 / 單筆申購金額統計 | 齊 | `S_TA_DSMR001_GET_1`~`S_TA_DSMR001_GET_5` | `DSMR001RPS1` `DSMR001RPS2` `DSMR001RPS3` |
| `DSMR002` | 業務部單筆申購百萬客戶清冊 / 統計(by 戶數) | 齊 | `S_TA_DSMR002_GET_1` `S_TA_DSMR002_GET_2` | `DSMR002RPS1` `DSMR002RPS2` |
| `DSMR003` | 部門 / 員工 / 單位別期間收入目標達成率排行 | 齊 | `S_TA_DSMR003_GET` | `DSMR003RPS1` `DSMR003RPS2` |
| `DSMR004` | 實際營收達成表(月 / 季 / 年報) | 齊 | `S_TA_DSMR004_GET` | `DSMR004RPS1` `DSMR004RPS2` `DSMR004RPS3` |
| `DSMR005` | 業務人員定額 / 不定額 / 168 循環年度配額達成與客戶明細 | 齊 | `S_TA_DSMR005_GET_1`~`S_TA_DSMR005_GET_3` | `DSMR005RPS1`~`DSMR005RPS6` |
| `DSMR006` | 銷售機構 / 促銷方案年度定額月統計 | 齊 | `S_TA_DSMR006_GET_1` `S_TA_DSMR006_GET_2` `S_TA_DSMR006_GET_4` `S_TA_DSMR006_GET_5` | `DSMR006RPS2` `DSMR006RPS3` `DSMR006RPS4` `DSMR006RPS6` `DSMR006RPS7` `DSMR006RPS8` |
| `DSMR007` | 業務員客戶組成表(彙總 / 明細) | 齊 | `S_TA_DSMR007_GET` | `DSMR007RPS1` `DSMR007RPS2` |
| `DSMR008` / `DSMR008_1` | 期間各基金業績(業務員別,含 / 不含申購來源);`_1` 是後綴變體,改走 Query / QryDetail 兩支 SP | 齊 | `S_TA_DSMR008_GET_1`~`S_TA_DSMR008_GET_4`;`S_TA_DSMR008_1_Query` `S_TA_DSMR008_1_QryDetail` | `DSMR008RPS1` `DSMR008RPS2` + 四個 **repo 內沒有的** |
| `DSMR009` / `DSMR009_1` | 期間各基金業績(銷售機構別 / 通路業務處 / MBR) | 齊 | `S_TA_DSMR009_GET` `S_TA_DSMR009_GET_2` `S_TA_DSMR009_GET_MBR`;`S_TA_DSMR009_1_Query` `S_TA_DSMR009_1_QryDetail` | `DSMR009RPS1`–`DSMR009RPS3` + 兩個 **repo 內沒有的** |
| `DSMR010` / `DSMR010a` / `DSMR010b` | 業務員基金別餘額彙總日報表;`a` 是變體,**`b` 已改成「境外基金每日原幣存量」** | 齊 | `S_TA_DSMR010_GET_1`~`S_TA_DSMR010_GET_3`;`S_TA_DSMR010a_GET_3`;`S_TA_DSMR010b_GET` | `DSMR010RPS1` + 三個 **repo 內沒有的** |
| `DSMR011` | 期間各業務單位淨申購 / 結存金額統計(9 種組合) | 齊 | `S_TA_DSMR011_GET` | `DSMR011RPS1`~`DSMR011RPS9` |
| `DSMR012` / `DSMR013` | 累積月平均淨申購;各基金業績表(機構 / 受益人 / 申贖明細) | 齊 | `S_TA_DSMR012_GET_2` `S_TA_DSMR012_GET_3`;`S_TA_DSMR013_GET` | **repo 內都沒有** |

**表尾那五支「repo 內沒有 rpt」不是掃描漏了。**`Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/` 只有 40 個 `.rpt`,最新的是 `DSMR011RPS9`。`DSMR008_1` / `DSMR009_1` / `DSMR010a` / `DSMR010b` / `DSMR012` / `DSMR013` 引用的報表檔名在專案裡都不存在。原因見 §7.2。

### 3.5 一眼看出差別的五件事

1. **只有兩支畫面會寄 e-mail**(`DSMM901` / `DSMM902`),而且信裡的送簽來源字串是寫死的中文,改畫面代號要一起改(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:102`)。

2. **只有兩支畫面會匯入 CSV**(同上兩支),兩支的欄位數不同(5 欄 vs 9 欄),錯誤處理的寬嚴也不同(§4.7 / §4.8)。

3. **只有一支畫面有「拷貝」功能**(`DSMM005`),而且拷貝是一整段 PL/SQL 匿名區塊直接送 DB(§4.4)。

4. **只有一支畫面完全不走四眼**(`DSMM906`)。

5. **17 支 R 畫面裡有 4 支是後綴變體**(`DSMR008_1` `DSMR009_1` `DSMR010a` `DSMR010b`),它們與本體的關係見 §7.4。

## 4. 維護畫面(M)— 一支一節

```text
[圖] DSM 維護畫面的卡控分層:UI 層、PO 層、四眼引擎,以及不走四眼的 DSMM906
圖中文字:① 用戶端(UI):十支 M 畫面的卡控幾乎全在這一層 / 欄位驗證 / validatorManager1 / DoValidate() / 業務檢核 + 總和比對 / grid 逐列檢核 / DSMM050/903 只警示不擋 / SetMasterToDetail / 把主檔鍵塞進明細 / ② 伺服端(PO):只有兩支畫面有第二道防線 / BeforeAdd/Update / DSMM901 結帳日 / BeforeAdd/Update / DSMM906 戶號歸屬 / 其餘八支 / PO 只掛取數事件 / 繞過 UI = 沒有卡控 / 風險 / ③ 四眼引擎(BaseEVADaoPO,無原始碼) / 輸入 2xx / 待驗證 / 驗證 / 待覆核 / 覆核 3xx / 生效 / DSMM902 覆核即執行 / 狀態 203 例外 / ④ 例外:一支畫面完全不走四眼 / DSMM906 / Add/Update/Delete 全 override / 手寫 INSERT/UPDATE/DELETE / 不寫 STATUS 與四眼 13 欄 / 直接落地 / 沒有待驗證/待覆核
```

*圖:圖 3 卡控順序。橘框=真正會擋下的關卡;橘虛框=風險或客戶特定;黑框=無原始碼的框架層。十支 M 畫面裡只有 DSMM901 與 DSMM906 在伺服端再驗一次,DSMM906 更是連四眼都不走。*

十支 M 畫面可以分成三群:**三支業績目標**(`DSMM001` `DSMM002` `DSMM003`,程式幾乎是同一份複製三次)、**三支歸屬與拆帳**(`DSMM005` `DSMM060` `DSMM903`)、**兩支業務移轉**(`DSMM901` `DSMM902`),外加 `DSMM050`(組織)與 `DSMM906`(對帳單名單)兩支獨立的。

### 4.1 `DSMM001` — 業務員年度業績目標

#### 用途(推測)

一位業務員、一個業績年度,設六個指標的年度總額(存 `DSM001A`),再把年度總額拆成每月的目標(存 `DSM002A`)。六個指標見 §2.3。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:69-147`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 框架必填 / 格式 | 欄位空或錯 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:72` |
| 2 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:75-76` |
| 3 | 明細 PK 必填 | 有列缺 PK | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:91-96` |
| 4 | 明細至少一列 | grid 空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:97-100` |
| 5–10 | **六個指標**各自的年度總額 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:123-145` |
| — | 年份不得小於 1900 | 離開欄位時 | 阻擋(`e.Cancel`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:476-486` |

**六個指標的「必須大於 0」檢核全部被註解掉**——主檔那六條在 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89`,明細那六條在 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120`。也就是說 **`DSMM001` 的六個指標全部可以是 0、甚至負數**,只要總和相符就過。

> **與 `CASM006` 的差異(§8.1)**:`CASM006` 保留了「總營業收入必須大於 0」那一條(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78`),`DSMM001` 連這條都註解掉了。**同一張表,兩個入口,一邊擋一邊不擋。**

#### 「月分配」鈕的行為

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:154-292`。可分配月數 `iMONTH_COUNT = 12 - 起算月 + 1`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196`),均分值一律 `Math.Floor`。

| 模式 | 行為 | 錨點 |
|---|---|---|
| 新增 | 先 `Clear()`,建 `iMONTH_COUNT - 1` 列均分值,**最後一列補全部餘額** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:243-291` |
| 修改 | 依 `QUO_YYMM` 排序逐列寫入,前 `iMONTH_COUNT - 1` 列均分、之後補餘額 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:210-242` |

**新增模式是對的**(餘額寫得回去,總和檢核會過)。**修改模式有一個坑**:`j` 只在 `if` 分支內遞增(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:230`),一旦 `j` 到達 `iMONTH_COUNT`,**後面每一列都會各自被寫入整筆餘額**。只要明細列數大於可分配月數(例如起算月改過、或手動加了列),按一次月分配就會讓總和爆掉,然後被第 5–10 條擋下。

#### 四眼各階段附加動作

**沒有。**`DSMM001_PO` 只掛三個取數事件(`BeforeSelect` / `BeforeGetMaintainData` / `BeforeGetToDoData`),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:32-34`。新增 / 修改 / 刪除的寫入完全交給 `BaseEVADaoPO` 的預設實作。

#### 跨表更新

只寫 `DSM001A` + `DSM002A`。查詢時 join `COD009`(INNER)與 `SAL051`(INNER),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:126-131`。

| join | 型別 | 後果 |
|---|---|---|
| `COD009` | INNER | 員工從員工檔消失 → 這筆目標整筆查不到 |
| `SAL051` | INNER | 員工不在任何業務部門(或被 `DSMM050` 刪掉)→ 這筆目標整筆查不到 |

**兩條都是過濾(無提示)。**PO 的原始註解直接寫「`SAL051` 為直銷的員工範圍」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:112`),所以這是設計如此,不是 bug——但它同時意味著 **`DSMM050` 刪一個人,`DSMM001` 就看不到他的歷年目標**。

#### 查詢條件的組法

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:394-419` 加條件,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:134-184` 組 SQL:

| 畫面條件 | 送出的參數 | SQL 實際長相 |
|---|---|---|
| 業績年度 | `QUO_YEAR` Equal | `DSM001A.QUO_YEAR = '值'` |
| 員工代碼(起) | `EMP_NO` Equal | `DSM001A.EMP_NO >= '值'`(**運算子在 PO 內被改寫成 `>=`**) |
| 員工代碼(迄) | `EMP_NO1` Equal | `DSM001A.EMP_NO <= '值'` |
| 業務部門 | `SAL_DEPT_NO` **Like** | `SAL051.SAL_DEPT_NO LIKE '值'` |

**最後一條有陷阱**:`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148` 是 `" AND SAL051." + Row.Name + Row.Opeartor + "'" + Row.Value + "'"`,直接把運算子字串接上去,**而畫面送的值沒有加 `%`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:417-418`)。`LIKE 'S01'` 在 Oracle 等同於 `= 'S01'`,所以選一個大部門不會帶出底下的小部門。**假設**這是非預期行為,依據是同檔其他條件都明確寫 `=`,只有這一條特地改成 `Like`。

同一行還是**字串串接進 SQL**(值沒有跳脫),見附錄 E7。

#### 下拉的過濾〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:304-312`:三個員工選擇控件都設 `IS_SALE = true`、`SAL_CD = "B,C"`、`Filter = "(LEAVE_DATE >= '<今年>/01/01' OR LEAVE_DATE IS NULL)"`。也就是**只挑業務屬性 B 或 C、且不是往年離職的人**。今年才離職的人**選得到**。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:75-76` |
| 按新增 / 修改前 | 六個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:91-100` |
| 按新增 / 修改前 | 明細每列六個指標 > 0 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:123-145` |
| 按查詢前 | 員工代碼起迄成對 | 只填一邊 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:398-399` |
| 查詢時 | 員工不在 `COD009` 或不在 `SAL051` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:126-131` |
| 查詢時 | 部門條件用 `LIKE` 但不補 `%` | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148` |
| 選部門時 | 清掉已選的員工起迄 | 部門有值 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:488-502` |
| 選員工時 | 起填了、迄沒填 → 自動補成一樣 | 是 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:469-473` |
| 按月分配 | 明細列數 > 可分配月數時餘額重複寫 | 是 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:215-241` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.2 `DSMM002` — 業務單位年度業績目標

#### 用途(推測)

與 `DSMM001` 結構完全平行,但鍵從「員工」換成「單位」(`DEPT_NO`),六個指標一模一樣。

#### 與 `DSMM001` 的三個實質差異

| 面向 | `DSMM001` | `DSMM002` | 錨點 |
|---|---|---|---|
| **可分配月數** | `13 - 起算月` | **固定 12** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:201-206` |
| **會不會跨年** | 不會(月份鎖在年內) | **會**:起算月非 1 月時,`iQUO_Month > 12` 的那幾列會寫成「次年 + 月」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:254-255`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:279-280` |
| **查詢的員工起迄檢核** | 有 | **整段被註解** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` |

**第二列是關鍵**:同一份「起算年月 = 2026/07」的設定,在 `DSMM001` 會產生 6 列(202607–202612),在 `DSMM002` 會產生 12 列(202607–202712)。**兩支畫面對「年度目標」的定義不一樣**,而且畫面上沒有任何文字說明。

第三個差異還有一個連帶效果:`DSMM002` 的「月分配」是靠 `DSM008A.Rows.Count > 0` 決定走哪一個分支(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:208`),而 `DSMM001` 是靠 `ActionMode`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:210`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:243`)。結果一樣,但讀 code 時很容易對錯。

#### 取數 SQL 的部門對照〔客戶特定〕

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:126-127`:

```
LEFT JOIN OFD002
  ON OFD002.DEPT_NO = DECODE(DSM007A.DEPT_NO, 'S', 'G', '090', 'I', DSM007A.DEPT_NO)
```

也就是說 **`DSM007A` 存的部門代碼 `S` 要對到 `OFD002` 的 `G`、`090` 要對到 `I`**,其餘原樣。這是寫死在 SQL 裡的兩筆對照,不是設定檔,換站台一定要重問。好消息是這裡用的是 `LEFT JOIN`,對不到只是名稱空白,不會整筆消失(對照 `DSMM001` 的兩個 INNER JOIN)。

#### 下拉的過濾

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:302-303`:兩個部門控件的 `Filter` 都是 `LEN(DEPT_NO) = 5`,註解寫「只顯示5碼部門代碼」。**所以 3 碼的大部門在這支畫面選不到**,但資料庫裡可以存(檢核不擋),見附錄 E。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:75-76` |
| 按新增 / 修改前 | 六個指標 > 0(主檔與明細) | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:78-89`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:104-120` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:91-100` |
| 按新增 / 修改前 | 六個指標年度 = 月分配總和 | 任一不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:123-145` |
| 按查詢前 | 員工代碼起迄 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` |
| 查詢時 | 部門條件用 `LIKE` 但不補 `%` | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:146` |
| 選部門時 | 只能選 5 碼部門 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:302-303` |
| 按月分配 | 固定切 12 個月,會跨年 | 起算月 ≠ 1 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:254-255` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.3 `DSMM003` — 業務員×基金型別年度淨銷售目標

#### 用途(推測)

與前兩支同樣是「年度總額 + 月分配」,但只有**一個**指標(`QUO_NET_IN` 淨銷售金額),而且主鍵多一個 `FUND_TYPE_SALE`(基金型別),也就是同一位業務員可以對不同基金型別各設一組目標。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:62-94`。**這支是三兄弟裡唯一沒有把「必須大於 0」註解掉的**:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | 起算年月與業績年度同一年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:68-69` |
| 2 | **年度淨銷售金額 > 0** | `< 1` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:71-72` |
| 3 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:74-83` |
| 4 | **每列淨銷售金額 > 0** | 有列 `<= 0` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:87-88` |
| 5 | 年度總額 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:90-92` |

#### 「月分配」鈕的實質缺陷

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:103-178`。可分配月數算 `12 - 起算月 + 1`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:121`),**但修改模式補餘額的判斷式寫死 `j < 12`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130`)。

後果:起算月不是 1 月時,明細列數只有 `iMONTH_COUNT`(< 12),迴圈裡 `j` 永遠到不了 12,**每一列都拿到均分值,餘額從來沒寫回去**。而 `Math.Floor` 幾乎一定會有餘數 → 總和小於年度總額 → 第 5 條把存檔擋下來 → 使用者必須手動改最後一列。

**新增模式沒有這個問題**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:143-177` 用的是 `iMONTH_COUNT - 1` 加一列補餘額)。所以**同一筆資料,第一次建立時月分配是對的,之後改年度總額再按一次就錯**。這是本模組最會咬人的三個缺陷之一(附錄 E3)。

#### 取數 SQL:一個會被查詢條件毀掉的 `LEFT JOIN`

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:120-126`:

```
FROM DSM003A JOIN COD009 ON COD009.EMP_NO = DSM003A.EMP_NO
LEFT JOIN SAL051 ON SAL051.EMP_NO = DSM003A.EMP_NO AND SAL051.SAL_CD = 'C'
```

刻意用 `LEFT JOIN`(不在 `SAL051` 的人也查得到,只是部門顯示空白)。**但只要使用者在查詢畫面選了部門**,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` 會在 `WHERE` 後面加 `AND SAL051.SAL_DEPT_NO = '值'`,這一條會**把 `LEFT JOIN` 變回 INNER JOIN**(NULL 不等於任何值)。

也就是說:**不填部門查得到的資料,填了部門就永遠查不到**——即使那個人真的在該部門、只是 `SAL_CD` 不是 `C`。過濾(無提示)。

#### 下拉的過濾〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:196-216`:

| 控件 | 條件 |
|---|---|
| 基金型別 | 代碼分類 `412`,再用 `RowFilter = "TextValue<>'C'"` **把 `C` 這一項拿掉** |
| 部門 | `(LEN(DEPT_NO) = 5) AND ((DEPT_NO LIKE 'S0%') OR (DEPT_NO LIKE '08%'))` |
| 員工(三個控件) | `IS_SALE = true`、`SAL_CD = "C"`、不是往年離職 |

注意**員工的 `SAL_CD` 在這支是 `"C"`,`DSMM001` 是 `"B,C"`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:305`)。同樣是「選業務員」,兩支畫面的候選人集合不同。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 起算年月與業績年度同年 | 年份不同 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:68-69` |
| 按新增 / 修改前 | 年度淨銷售金額 > 0 | `< 1` | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:71-72` |
| 按新增 / 修改前 | 明細 PK 必填、至少一列 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:74-83` |
| 按新增 / 修改前 | 年度 = 月分配總和 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:90-92` |
| 按查詢前 | 員工代碼起迄成對且起 ≤ 迄 | 不符 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:279-283` |
| 查詢時 | 員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:121-122` |
| 查詢時 | 有填部門 → `LEFT JOIN` 退化成 INNER | 有填部門 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` |
| 選基金型別時 | 代碼 `C` 被拿掉 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:202-204` |
| 選部門時 | 只看 `S0` 與 `08` 開頭的 5 碼部門 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:205` |
| 按月分配 | 修改模式餘額從不寫回 | 起算月 ≠ 1 | 記錄不擋(之後被總和檢核擋) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.4 `DSMM005` — 離職業務分攤比率

#### 用途(推測)

某個業績年月、某個部門,離職業務員留下來的業績要按什麼比率分給部門裡的哪些人。grid 裡每一列是一個人 + 一個比率,**全部比率加起來必須是 100**。

這是全模組唯一的**多筆型 EVA**(`BaseMultiRowEVADaoPO`):`QUO_YYMM` + `DEPT_NO` 是「一組」的鍵,一組裡的 N 個人一起送審。

#### 必填與存檔前檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:391-451`:

| # | 檢核 | 成立時 | 結果 | 錨點 |
|---|---|---|---|---|
| 1 | grid 編輯中的列先 `Update()` | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:399-402` |
| 2 | 至少一列有員工代碼 | 全空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:405-409` |
| 3 | 每列分攤比率 >= 0 | 有負數 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:412-416` |
| 4 | **分攤比率加總 = 100** | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:419-423` |
| 5 | 新增模式:此年月 + 部門不可已存在 | 查得到 | 阻擋(先送一次查詢去 DB 確認) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:431-448` |

第 5 條是本模組唯一一處「**存檔前先打一次 DB 確認重複**」的寫法,其他畫面都靠主鍵違反去擋。

#### 「加入部門組織成員」鈕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:483-530`:一次把部門底下的人全部帶進 grid,比率預設 0。

| 行為 | 說明 | 錨點 |
|---|---|---|
| 必須先選部門 | 沒選就跳訊息並 `return` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:486-490` |
| **部門代碼第 1 碼是 `S`** → 走直銷分支(`IS_SALE` + `SAL_DEPT_NO` + `SAL_CD = 'C'`);否則只用 `DEPT_NO` | `Substring(0, 1)` 位置取值 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:494-506`〔客戶特定〕 |
| 排除往年離職者 | `LEAVE_DATE.Substring(0, 4)` 取年份 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:514-517` |
| 已在 grid 的人跳過 | 靠 `EMP_NO` 比對 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:518` |

兩個位置取值都沒有長度保護:部門代碼是空字串時 `Substring(0,1)` 會丟例外(前面的必填檢核擋住了),離職日格式不是 `yyyy…` 時 `Convert.ToInt16` 會丟例外(附錄 E6)。

#### 「拷貝」鈕與那段 PL/SQL

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:536-543` 開 `DSMM005p0`,按確定後走 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:191-318` 的 `Copy`。

流程:先數來源筆數(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:201-215`),0 筆就回失敗;否則送一整段 **PL/SQL 匿名區塊**,用 `WHILE` 迴圈從目的起月跑到目的迄月,每個月 `INSERT … SELECT` 一次(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:224-278`)。

這段有五個要記住的地方:

| 項 | 內容 | 錨點 |
|---|---|---|
| **GUID 只產一次** | `xNEW_GUID` 在迴圈**外面**算,每一個月、每一列 `INSERT` 都用同一個值當 `DATAID` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:237-244` |
| **直接寫成已覆核** | `STATUS` 照抄來源列,`ENTRYID` / `VERIFYID` / `APPROVEID` 一次填滿、`REJECTID` 填空白 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:264-276` |
| **已存在的年月直接跳過** | `DECODE(COUNT(*),0,'Y','N')` 判斷,`N` 就 `CONTINUE`,不覆蓋也不提示 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:254-262` |
| **`SYSDATE ASENTRYDATE`** 別名黏字 · **成功卻回報失敗** | 前者靠位置對應所以執行沒事;後者是 `i = ExecuteNonQuery(匿名區塊)` 對 PL/SQL 區塊通常回 0 或 -1,而程式用 `if (i > 0)` 判成功 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:271`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:290-302` |

最後一條的實際表現是「資料明明複製進去了,畫面卻顯示『查無可拷貝的資料 或 資料已存在。』」(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:87-91`)。**假設**:依據是 `ExecuteNonQuery` 對非 DML 敘述的回傳值定義,以及同檔 `Copy` 前半段用 `ExecuteScalar` 數筆數時就沒有這個問題。要確定得實跑一次。

#### 彈出視窗 `DSMM005p0` 的檢核

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:110-155`:

| 檢核 | 結果 | 錨點 |
|---|---|---|
| 來源業績年月必填 · 目的業績年月起迄皆必填且起 ≤ 迄 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:115-132` |
| 部門起迄要嘛都填要嘛都空 · 部門起 ≤ 部門迄 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:138-147` |

**沒有任何一條檢查「來源年月 ≠ 目的年月」**,也沒有檢查目的區間長度。把來源設成 202601、目的設成 202601–203012,會送出一段跑 60 次迴圈的 PL/SQL。

另外:所有錯誤訊息都掛在 `umskQUO_YYMM` 這一個控件上(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:125`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:141`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:146`),即使講的是部門欄的問題,紅框也會標在年月欄上。

#### 查詢的取數

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:117-153`。條件由共用 helper `EVAStringHelper.AddParam` 產生(參數化,**這是全模組少數有綁參數的取數 SQL**),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:136` 一次宣告六個條件名。`OFD002` 是 `LEFT JOIN`,部門名稱查不到只會空白。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 至少一列有員工 | 全空 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:405-409` |
| 按新增 / 修改前 | 分攤比率加總 = 100 | 不等 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:419-423` |
| 按加入成員 | 往年離職者不帶進來 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:514-517` |
| 拷貝 | 來源 = 目的、區間過長 | — | **完全沒有檢核** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:110-155` |
| 拷貝成功 | 回報值判斷式可能永遠為假 | 是 | 記錄不擋(誤報失敗) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:295-302` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.5 `DSMM050` — 業務部門與人員設定

#### 用途(推測)

主檔 `SAL050` 一個業務部門一列(部門屬性、主管獎金計算類別);明細 `SAL051` 是部門底下的人(業務屬性、獎金制度)。**這是整個直銷業務組織的來源**,`DSMM001` `DSMM003` `DSMM901` `DSMM902` `DSMM903` 五支畫面的員工範圍都由它決定(§8.5)。

#### 部門代碼長度決定一切

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:154-240` 的 `DoValidate` 把「部門代碼幾碼」當成主要分支:

| 部門代碼長度 | 部門屬性(`DEPT_CD`)的限制 | 明細業務屬性(`SAL_CD`)的限制 | 錨點 |
|---|---|---|---|
| **5 碼** | 不可為 `0`(大部門) | 不可為 `A`(部門主管);`DEPT_CD = 'A'` 時不可為 `D` / `E`;`DEPT_CD = 'S'` 時不可為 `B` / `C` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:170-176`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:197-216` |
| **3 碼** | 只能是 `0` | **只能是 `A`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:178-184`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:219-226` |
| 其他長度 | **不檢核** | **不檢核** | 同上,兩個 `if` 都只認 3 與 5 |

最後一列是實質漏洞:輸入 4 碼或 6 碼的部門代碼,上面所有規則一條都不會跑。

#### 逐列檢核與存檔前檢核,兩套規則兩種嚴格度

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:346-430` 的 `BeforeRowUpdate` 是另一套:

| `DEPT_CD` | 逐列規則(`BeforeRowUpdate`) | 存檔前規則(`DoValidate`) |
|---|---|---|
| `0` | `SAL_CD` **必須**是 `A` | 只有 3 碼部門才要求 `A` |
| `A` | `SAL_CD` **必須**是 `B` 或 `C` | 只擋 `D` / `E` |
| `S` | `SAL_CD` **必須**是 `D` 或 `E` | 只擋 `B` / `C` |
| 其他 | 不檢核 | 不檢核 |

方向一致,但**逐列那套嚴格、存檔那套寬鬆**;而且**逐列那套的四處 `e.Cancel = true;` 全部被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:373`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:382`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:394`),只剩訊息與紅框。**結論:逐列規則全部是「警示(不擋)」,真正的閘門是比較寬的那一套。**

還有一個小坑:`BeforeRowUpdate` 的每一段檢核前都先 `ValidateErrList.Clear()`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:360`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:369`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:378`),所以**一次只會看到最後一條錯誤訊息**。

#### 下拉與挑人〔客戶特定〕

| 項目 | 來源 | 錨點 |
|---|---|---|
| 部門屬性 / 主管獎金類別 | 代碼分類 `458` / `459`,**用 `GetDropDownDataSrc`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:115-117` |
| 查詢結果 grid 的同兩欄 | 同樣是 `458` / `459`,但**改用 `GetDropDown9iDataSrc`** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-78` |
| 明細的業務屬性 / 獎金制度 | 代碼分類 `460` / `461`,`GetDropDown9iDataSrc` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:79-80` |
| 挑員工時的條件 | `AO_CODE = 'Y'` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |
| 明細新列預設值 | `SAL_CD = "C"`、`BONUS_TYPE = "1"` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:320-321` |

**同一個代碼分類用兩套 DataSource 實作**(`GetDropDownDataSrc` 與 `GetDropDown9iDataSrc`),兩者都無原始碼、從呼叫端反推。維護畫面與查詢結果拿到的清單如果不一致,就是從這裡來的。

#### 取數 SQL

| 段 | 寫法 | 風險 |
|---|---|---|
| 主檔 | `FROM SAL050 JOIN OFD002 ON SAL050.SAL_DEPT_NO = OFD002.DEPT_NO`(INNER) | 部門不在 `OFD002` → 整筆查不到(過濾,無提示);`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127` |
| 明細 | `FROM SAL051,COD009 WHERE … SAL051.EMP_NO = COD009.EMP_NO`(舊式逗號 join,等同 INNER) | 員工不在 `COD009` → 該列消失(過濾,無提示);`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178-180` |
| `ORDER BY` | **被註解掉,而且註解裡寫的還是 `DSM003A` 的欄位** | 查詢結果沒有固定排序;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:150` |

**這支 PO 是全模組唯一會對查詢值做單引號跳脫的**:`Row.Value.Replace("'", "''")`,三處(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:139`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:190`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:200`)。其他 PO 全部直接串。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 屬性 `A` 不可配 `D` / `E`;屬性 `S` 不可配 `B` / `C` | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:206-214` |
| 挑員工時 | `AO_CODE = 'Y'` | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |
| 查詢時 | 部門不在 `OFD002` / 員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:125-127`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178-180` |
| 按查詢前 | **完全沒有檢核** | — | — | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:282-292` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.6 `DSMM060` — 受益人歸屬業務員〔共用表〕

#### 用途(推測)

一個受益人戶號歸給一位業務員 + 一個業務部門,加一個歸屬日期。主檔是 `OFD374A`——**OFD 前綴的表,但唯一的維護畫面在 DSM**。BMS 那側怎麼用它見 §8.2。

#### 這支畫面有多小

PO 只有 77 行,沒有任何 `BeforeAdd` / `BeforeUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:28-34` 只掛三個取數事件);UI 187 行,`DoValidate()` 只呼叫框架的欄位驗證(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:50-55`)。**所以「這個戶號是不是已經歸給別人」「這個業務員是不是真的在這個部門」在存檔時完全不檢查**,只靠下拉的連動。

#### 歸屬日期永遠是今天

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:85-86`(新增)與 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:96-97`(修改)都做同一件事:

```
udatBELONG_DATE.DateTime = DateTime.Today;  udatBELONG_DATE.ReadOnly = true;
```

**修改一筆舊資料,歸屬日期會被改成今天**,而且欄位是唯讀的、使用者救不回來。查詢頁的歸屬日期倒是可以自己輸入當條件(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:103-104`)。

#### 下拉連動

| 事件 | 行為 | 錨點 |
|---|---|---|
| 選業務員之前沒選部門 | 跳「須先選擇業務部門。」並 `e.Cancel = true` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:152-159`(維護頁)、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:177-184`(查詢頁) |
| 換部門 | 清掉已選的業務員,並把新部門傳給員工控件 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:141-145`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:166-170` |
| 修改模式載入時 | **先解除再重掛**「選業務員前」事件,避免載入既有值時跳警告 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:91`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:95` |

#### 取數 SQL:四張表全是 INNER JOIN

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:48-62`:

```
select a.*, b.bf_name, c.dept_sh_nm, d.emp_name from ofd374a a
  join bms001a b on a.bf_no = b.bf_no
  join ofd002  c on a.sal_dept_no = c.dept_no
  join cod009  d on a.emp_no = d.emp_no
```

三個 INNER JOIN,任何一個對不到,整筆歸屬資料就在畫面上消失。**這一條對 §8.2 很重要**:`RSPM004` 會直接 `INSERT OFD374A`(`Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700`),如果它寫進去的部門代碼不在 `OFD002`,`DSMM060` 就永遠看不到那筆,也改不掉。過濾(無提示)。

好消息:這支 PO 的條件是用 `EVAStringHelper.AddParam(dbProduct, args.DbCmd, …)` 產生的**綁定參數**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:58`),不是字串串接——全模組只有 `DSMM060`、`DSMM005`、`DSMM901`、`DSMM902` 做到這一點。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 業務員是否屬於該部門 | — | **完全沒有檢核**(只靠下拉過濾) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:144` |
| 選業務員前 | 必須先選部門 | 沒選 | 阻擋(`e.Cancel`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:152-159` |
| 新增 / 修改時 | 歸屬日期強制為今天且唯讀 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:85-86`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM060.cs:96-97` |
| 查詢時 | 戶號不在 `BMS001A`、部門不在 `OFD002`、員工不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:50-56` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.7 `DSMM901` — 業務移轉申請(戶號層)

#### 用途(推測)

一批(`BATCHID`)要移轉的客戶:每一列是「戶號 + 移轉前銷售機構 / 業務員 → 移轉後銷售機構 / 業務員」。走完四眼、覆核通過後,由人工按「執行」呼叫 SP 真正搬資料,搬完把當時庫存寫回 `EXEAUM`。**每一段狀態變化都寄一封信給下一關。**

#### 期別(`BATCHID`)怎麼產

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:58-75`:

```
SELECT NVL(MAX(DSM901.BATCHID) + 1, <今年>001) FROM DSM901 WHERE DSM901.BATCHID > <今年>000
```

年份用 `DateTime.Today.Year` 直接 `string.Format` 進 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:62`)。**沒有鎖、沒有序列**,兩個人同時新增會拿到同一個號(附錄 E5)。拿到號之後,主檔與明細的 `BATCHID` 一起被覆寫(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:66-74`),同時把 `EXESTATUS` 強制設成未執行、清掉執行時間與執行者。

#### 唯一的伺服器端卡控:執行基準日不可大於結帳日

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:180-200`:

```
SELECT MAX(CTL_DATE) FROM OFD303A A WHERE A.POST_CTL_CODE = 'Y'
   AND CTL_DATE < (SELECT MIN(CTL_DATE) FROM OFD303A WHERE POST_CTL_CODE = 'N')
```

取「最後一個已結帳、且早於第一個未結帳」的日期,基準日晚於它就擋下(`args.Cancel = true`,訊息「執行基準日不可大於結帳日yyyy/MM/dd」)。

三個要注意的:**只有 `EXESEQ == 1` 才檢查**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184`),第二次以後的移轉完全不驗結帳日;`DSM901[0]` 直接取第一列,主檔 0 列時會丟例外(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:183`);`BeforeAdd` 第一行寫成 `if (args.TableName != "DSM901" || CheckExeDATE(args)) return;`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:56`),檢核不過就直接 `return`、**連 `BATCHID` 都不會配**(結果是對的,但讀起來很容易以為漏了)。

#### CSV 匯入:五欄,而且兩道檢核被註解掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:400-491`。「下載範本」鈕只寫一行標題,不含任何資料列(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:493-510`):

```
戶號,移轉前銷售機構代碼,移轉前業務員代碼,移轉後銷售機構代碼,移轉後業務員代碼
```

匯入的逐列處理:

| 步驟 | 行為 | 錨點 |
|---|---|---|
| 第一行當標題丟掉 | 空字串就整個放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:419` |
| **欄數不足 5 就 `break`** | **無訊息、無記錄**,檔案後半直接被丟掉 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:426` |
| 戶號轉數字失敗 · 主鍵重複 | 各自跳訊息並整批放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:428-436`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:462-466` |
| 員工代碼補 0 到 6 碼 | 前後兩個都補 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:439-440`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:450-451`〔客戶特定〕 |
| **「移轉後機構必須是直銷」與「移轉前後不可完全相同」** | **兩段都被註解**,理由分別是「20190808 不檔移轉後需為直銷單位」與「鳳滿說為了活化1不擋 20180820」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` |
| 全部讀完後送 `CheckExists` | 成功才把 grid 換成回傳的資料 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:470-480` |

CSV 讀檔用 `new StreamReader(檔名)`(預設編碼)、寫範本用 `Encoding.Default`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:500`),兩邊不對稱,而且都吃作業系統的 codepage。

#### 逐筆新增(`DSMM901p0`)比 CSV 嚴格

雙擊 grid 的空白列會開 `DSMM901p0`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:357-378`)。它的檢核有三條,**其中兩條就是 CSV 匯入被註解掉的那兩條**:

| 檢核 | 錨點 |
|---|---|
| 戶號 + 移轉前機構 + 移轉前業務員 不可重覆 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:55-62` |
| **銷售機構及員工代碼修改前後不可都一樣** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:64-65` |
| 移轉前業務員留空時,該戶號必須真的有該機構的「公單」交易 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:67-75` |

**同一張表、同一個畫面,用手打跟用 CSV 匯入,規則不一樣。**這是本模組最值得先問清楚的一件事。

`DSMM901p0` 的候選清單來自 `GetEmpNo`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:278-324`):對 `OFD306A` 與 `OFD306` 各跑一次「取基準日之前最後一次異動、且累計單位數 > 0」的查詢,`UNION ALL` 之後再取最新的一筆。也就是**只有「還有庫存」的機構 / 業務員組合才選得到**。查無資料時回一句「查無有庫存之業務員資料」但 `ReturnCode` 仍是 `true`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:314`)——訊息有、不擋。

#### `CheckExists`:逐列打五次 DB

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:330-464`。對 grid 的每一列,依序驗:戶號在 `BMS001A`、移轉前機構在 `OFD068A_V02`、移轉後機構在 `OFD068A_V02`、移轉前員工在 `COD009`、移轉後員工在 `COD009`。任何一條不過就**清空整個明細**並回錯誤訊息。

兩個要記住的:**移轉後員工的檢核在 2019 年被降級**——原本準備了 `sqlEm`(要求員工同時在 `SAL051` 的移轉後部門、且未離職,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:346-354`),但實際執行的那一行被換成只查姓名的 `sqlEmpNM`,舊的留在註解裡(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430`);**`DSMM902` 到今天還在用 `sqlEm`**(§4.8)。另外**「戶號必須有該機構 / 員工的結餘」整段被註解**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:355-369` 的 SQL 與 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` 的呼叫),理由同樣是「鳳滿說為了活化1不擋 20180820」。

`OFD068A_V02` 這支 view 本身有兩個已知問題,對這裡的影響見 §8.6。

#### 執行與列印

| 動作 | 呼叫 | 回傳處理 | 錨點 |
|---|---|---|---|
| 執行(`DoExp1`) | `S_TA_DSMM901_EXE`(IN:期別、執行者) | **SP 沒有 OUT 參數**,只要不丟例外就 `tran.Commit()` 並回「執行成功」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:470-500`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:512-531` |
| 列印(`DoExp2`) | `S_TA_DSMM901_GET`(IN:期別、比較日、機構;OUT:兩個游標) | 明細 0 筆但主檔有 → 「未執行不可列印」;都 0 → 「查無資料」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:506-533` |
| 覆核 / 新增後重算庫存 | `S_TA_DSMM901_AUM`(IN:期別) | 沒有回傳判斷 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:127-140` |

**`S_TA_DSMM901_AUM` 那段有一個明確的 bug**:`cmd` 建立一次,然後在 `foreach` 裡對每一列 `AddInParameter(cmd, "wBATCHID", …)`,**中間沒有 `Parameters.Clear()`**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:131-139`)。主檔只有一列時看不出來,多列就會在同一個 command 上重複加同名參數。附錄 E5。

#### 寄信

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:96-116` 組信、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:118-125` 依角色取收件人。每一段的收件人:

| 事件 | 收件人 / 副本 | 錨點 |
|---|---|---|
| 新增 / 修改 / 刪除 / 復原刪除 / 重送後 | V,副本 E | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:287-295`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:321-334` |
| 驗證後 | A,副本 E | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:297-300` |
| 覆核後 | E + V,無副本 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:302-305` |
| 退回後 | 有覆核權限的人退 → E;否則 → V(副本 E) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:313-319` |

**寄件人是登入者的 e-mail,空的話用寫死的 `ta-it@example.com`**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:111-113`)〔客戶特定〕。而且 `SendMail` 第一行會先看 `Util.Result[0].ReturnCode`,前一步失敗就不寄(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:98`)。

#### 兩個會改資料但不是卡控的行為

**改執行基準日 → 明細全刪**(`udatEXEDATE.ValueChanged` 直接把 `DSM902` 每一列 `Delete()`,沒有任何確認,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:543-547`);**載入已執行的批次 → `EXESEQ` 就地加 1**(在 `ModifyDataLoad` 裡改 row 的值,只是為了給明細的 `SEQ` 當預設值,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:207-209`)。前者在新增模式綁在 `AddDataLoad`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:183-184`)、修改模式只在「還沒執行過」時才綁(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:211-212`)——設計是對的,但這種「設值後才綁事件」的寫法很容易在改 code 時破功。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增 / 修改前 | 已執行的批次要有新增 / 修改過的明細 | 全是舊列 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:74-82` |
| 按修改前 | 跳出「E-mail備註」視窗,按取消就中止 | 按取消 | **詢問** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:282-285` |
| 按退回前 | 同上 | 按取消 | **詢問** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:307-311` |
| 新增 / 修改(PO) | 第一次移轉時,執行基準日不可大於結帳日 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:192-197` |
| 新增 / 修改(PO) | 第二次以後不驗結帳日 | 永遠 | **記錄不擋** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184` |
| 選執行基準日 | 不可大於今天 | 是 | 阻擋(控件 `MaxDate`) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:156` |
| 改執行基準日 | 明細全部刪除 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:543-547` |
| CSV 匯入 | 欄數 < 5 的那一行起,整個檔案不再讀 | 是 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:426` |
| CSV 匯入 | 移轉後機構須為直銷 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448` |
| CSV 匯入 | 移轉前後不可完全相同 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` |
| 手動新增明細 | 移轉前後不可完全相同 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:64-65` |
| 手動新增明細 | 前業務員留空時須有該機構公單交易 | 否 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p0.cs:67-75` |
| 手動新增明細 | 可選的機構 / 員工限「基準日前還有庫存」的組合 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:283-309` |
| 送出前檢查 | 戶號 / 前後機構 / 前後員工 任一查不到 | 是 | 阻擋(且清空整個明細) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:373-454` |
| 送出前檢查 | 移轉後員工須屬於移轉後部門且未離職 | — | **被降級成只查姓名** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430` |
| 送出前檢查 | 戶號須有該機構 / 員工的結餘 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` |
| 按執行鈕 | 只有狀態 `3` 開頭且未執行過才亮 | 不符 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:215-216` |
| 執行結果 | SP 沒有錯誤回傳通道 | 永遠 | **記錄不擋(一律回成功)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:481-486` |
| 刪除 | 已執行過(`EXESEQ > 1`)不可刪 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:219-222` |

### 4.8 `DSMM902` — 業務移轉申請(申購書層)

#### 用途(推測)

跟 `DSMM901` 同一件事,但顆粒度到「單一張申購書」(`ALLOT_NO` + `ALLOT_SRNO`),而且要先選境內 / 境外(`FUND_TYPE`)。移轉前後都可以換銷售機構**別**(`AGENT_ID`),不像 `DSMM901` 鎖死直銷。

#### 與 `DSMM901` 的差異總表

| 面向 | `DSMM901` | `DSMM902` | 錨點 |
|---|---|---|---|
| 覆核通過後 | 人工按執行 | **自動 `DoExp1()`**,且原本的「執行」通知信被註解掉 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:274-282` |
| 刪除覆核 | 沒有特例 | **狀態 `203`(刪除待覆核)時不跑 SP** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` |
| SP 錯誤回傳 | 無 | `strMsg` OUT 非空 → `tran.Rollback()` + 顯示訊息 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:476-490` |
| 移轉後員工檢核 | 只查姓名 | **查姓名 + 部門 + 未離職** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:433-447` |
| 執行基準日上限 | `MaxDate = 今天` | **那一行被註解掉,可選未來日** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` |
| 執行基準日 vs 結帳日 | 有檢核 | **`BeforeUpdate` 是空的 `{ };`** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81` |
| 改基準日會不會清明細 | 會 | **事件方法是空的** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:513-515` |
| 列印 | 有(`DoExp2` 開 `DSMM901p1`) | **`DoExp2` 是空的** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:508-511` |
| CSV 欄數 | 5 | 9 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:477` |

**第五、六列合起來是實質風險**:`DSMM902` 的執行基準日既沒有「不可大於今天」也沒有「不可大於結帳日」,完全不驗。

#### CSV 匯入(9 欄)

範本標題(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:477`):

```
戶號,申購書號,申購序號,移轉前銷售機構別,移轉前銷售機構代碼,移轉前業務員代碼,移轉後銷售機構別,移轉後銷售機構代碼,移轉後業務員代碼
```

| 步驟 | 行為 | 錨點 |
|---|---|---|
| 欄數不足 9 就 `break` | **無訊息**,同 `DSMM901` 的毛病 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:401` |
| 戶號 / 申購序號轉型失敗 | 各自跳訊息並整批放棄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:403-421` |
| 員工代碼補 0 到 6 碼 | 前後都補 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:425-431`〔客戶特定〕 |
| 主鍵重複 | 訊息含戶號與申購書號 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:436-440` |

**`DSMM902` 的 CSV 匯入沒有「移轉前後不可相同」的檢核,也沒有對應的逐筆新增彈出視窗**——`DSM904` 的明細只能靠 CSV 進來(grid 用 `GridLayoutNoUpdate`,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:130-131`)。

#### `CheckExists` 的四段檢核

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:294-458`,逐列:

| 段 | 查什麼 | 特別之處 | 錨點 |
|---|---|---|---|
| 1 | 戶號在 `BMS001A` |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:356-365` |
| 2 | 申購書在 `OFD221A`(境內)或 `OFD221`(境外),**而且只能剛好 1 筆** | 順便把基金 / 淨值 / 金額 / 單位數帶回畫面 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:366-391` |
| 3 | 移轉前 / 後機構在 `OFD068A`(境內)或 `OFD068` (境外) |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:392-417` |
| 4 | 移轉前員工在 `COD009`;**移轉後員工要在 `SAL051` 的移轉後部門且未離職** | 這就是 `DSMM901` 放掉的那條 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:418-447` |

境內 / 境外的切換不是用 `if`,而是**把 `FUND_TYPE` 綁成參數塞進 `WHERE` 當開關**:`AND :FUND_TYPE = '2'` 的那一段與 `AND :FUND_TYPE = '1'` 的那一段用 `UNION` 接起來,哪一段成立就只有那一段回資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:323-336`)。取數 SQL 也用同一招(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:222`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:260`)。這個寫法能跑,但**兩段的 join 對象不同**(境內接 `OFD081V` + `OFD068A`,境外接 `OFD081` + `OFD068` + `FSK003`),看的時候要分開讀。

#### 兩個空掛的事件

`DSMM902_PO` 的 `AfterGetMaintainData`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:105-108`)、`BeforeUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81`)、`AfterUpdate`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:115-118`)三個方法**都是空的或只有一行 `return`**,但建構子照樣把它們掛上去。對照 `DSMM901` 的同名方法都有實際內容——這幾個空殼是複製 `DSMM901` 之後沒刪乾淨的,**不要以為 `DSMM902` 也會重算庫存**(它不會,`DSM904` 也沒有 `EXEAUM` 這個欄位)。

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 選執行基準日 | 不可大於今天 | — | **被註解,不執行** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` |
| 新增 / 修改(PO) | 執行基準日 vs 結帳日 | — | **方法是空的** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81` |
| 修改模式 | 已執行 或 自己是驗證 / 覆核者 → 鎖匯入、鎖基準日、鎖修改與刪除 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:189-198` |
| CSV 匯入 | 欄數 < 9 的那一行起,整個檔案不再讀 | 是 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:401` |
| 覆核通過 | 狀態不是 `203` 就自動執行 SP | 是 | 記錄不擋(自動動作) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277-281` |
| 執行結果 | SP 的 `strMsg` 非空 | 是 | 阻擋(rollback + 顯示訊息) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:484-490` |
| 刪除 | 已執行 / 驗證 / 覆核狀態不可刪 | 是 | 記錄不擋(鎖按鈕) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:189-198` |

### 4.9 `DSMM903` — 直銷公單拆帳設定

#### 用途(推測)

一個受益人戶號,原本掛在直銷的「公單」(`AGENT_CODE` 以 `S` 開頭)底下。這支畫面設定:公單這一側掛哪個機構 / 主管(B 側),以及各段期間實際服務的業務員(A 側),兩邊按 `RATE_B` / `RATE_A` 拆帳;A 側還可以設業績上限 `MAX_BAL_AMT_A`(0 表示無上限)。

#### 四個寫死的常數〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29`:

```
static string myAGENT_ID = "0";        static string myAGENT_CODE_LIKE = "S%";
static string myAGENT_ID_B = "0";      static string myAGENT_ID_A = "0";
```

存檔時原封不動寫進主檔與每一列明細(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:51-53`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:70-72`)。**其中 `AGENT_ID` 與 `AGENT_CODE_LIKE` 還是主鍵的一部分**(§0.5),等於主鍵有兩欄永遠是同一個值。想支援非直銷,得同時改這四個常數、主鍵設定與取數 SQL。

用 `static` 存這種常數在 WinForms 單一使用者的情境不會互踩,但它與 BMS 的 `BMSB901A` 那條「靜態批號被兩人同跑互刪」是同一種寫法(`bms.md 附錄 E`),看到要警覺。

#### 開畫面就可能爆掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:200-218`:

```
if (view.UIView.DSHead_INFO.Count > 0) this._DSHead_INFORow = view.UIView.DSHead_INFO[0];
...
this.custEMP_NO_B.Filter = string.Format(" EMP_NO = '{0}'", this._DSHead_INFORow.EMP_NO);
```

`if` 有判斷,但**下面那行無條件用 `_DSHead_INFORow`**。`GetDSHeadInfo` 撈的是「`SAL051` 裡 `SAL_CD = 'A'` 且 `COD009.LEAVE_DATE` 為空」的人(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258`)。**只要沒有任何在職的部門主管,這支畫面在 `FormInitial` 就丟 `NullReferenceException`,根本開不起來。**`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` 還有第二次同樣的用法。附錄 E1。

順帶一提:`GetDSHeadInfo` 讀了 `model.Utility.PermissionInfo[0].UserID` 存進區域變數 `user_id`,**然後完全沒用到**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:247`)。看起來原本想按登入者篩主管,後來改成撈全部。

#### 拆帳比例的檢核只有一半

| 行為 | 說明 | 錨點 |
|---|---|---|
| 新增時 `RATE_B` 預設 30 | 寫死 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:276`〔客戶特定〕 |
| 改 `RATE_B` → `RATE_A = 100 - RATE_B` | 事件連動 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:385-389` |
| 改 `RATE_A` | **沒有反向連動** | 檔內無 `umskRATE_A_ValueChanged` |
| 存檔時 `RATE_A + RATE_B = 100` | **沒有這條檢核**,`DoValidate` 只檢查兩欄非空 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:120-124` |

也就是說**只要使用者最後動的是 `RATE_A`,就可以存出總和不是 100 的拆帳設定**。對照 `DSMM005` 有明確的「加總必須 = 100」檢核(§4.4),這裡是漏的。

#### 期間怎麼自動銜接

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61-79`:存檔前把明細依 `SDATE` **由新到舊**排一次,然後:

- 最新的那一列(`iCnt == 1`)的 `EDATE` 不動(來自 grid 預設值 `29991231`,`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355`);

- 其餘每一列的 `EDATE` 被改成「下一段(較新)那列的 `SDATE` 減一天」。

所以**使用者在 grid 裡打的 `EDATE`,除了最新那一列之外全部會被覆蓋**。這不是卡控,是自動改值,而且畫面上 `EDATE` 是可以編輯的、還被設成必填(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:353`),使用者不會知道自己打的值沒有用。

局部變數 `myEDATE` 初值 `"29991231"` 從頭到尾沒被讀過(第一圈就走 `iCnt == 1` 分支),是死碼。

#### 明細挑人的條件〔客戶特定〕

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:252-257`:

```
IS_SALE  = 'Y'
SAL_CD   = 'C'
LEAVE_DATE >= '29991231'
```

最後一條字面意思是「離職日大於等於 29991231」,正常人都沒有離職日。**假設**共用控件 `EmployeeDataSrc` 把 `LEAVE_DATE` 為 NULL 的人視為 `29991231` 來比對(否則這條會把所有人濾光),依據是同 repo 其他畫面用「`LEAVE_DATE >= '今年/01/01' OR LEAVE_DATE IS NULL`」這種明確寫法,而這裡只有一個 `>=` 卻仍然能用。**這條要現場驗證。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 開畫面 | 撈在職的直銷部門主管 | 一個都沒有 | **例外(畫面開不起來)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:217` |
| 按新增 / 修改前 | `RATE_A + RATE_B = 100` | — | **完全沒有檢核** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:120-124` |
| 存檔前 | 除最新一列外,`EDATE` 一律被覆寫成下一段起日減一天 | 永遠 | 記錄不擋(自動改值) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61-79` |
| 存檔前 | `AGENT_ID` / `AGENT_CODE_LIKE` / `AGENT_ID_A` / `AGENT_ID_B` 一律覆寫成常數 | 永遠 | 記錄不擋〔客戶特定〕 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:51-53` |
| 查詢時 | 戶號不在 `BMS001A`、公單業務員不在 `COD009` | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:133-137` |
| 查詢時 | 機構名稱靠 `OFD068A_V02` 且限 `AGENT_VALID_CODE = 'Y'` | 永遠 | 記錄不擋(`LEFT JOIN`,查不到只是空白) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141` |
| 刪除 | **完全沒有檢核** | — | — | 檔內無 `BeforeDeleteButtonClicked` |

### 4.10 `DSMM906` — 每月對帳單郵寄名單〔共用表·無四眼〕

#### 用途(推測)

業務員自己維護「我的哪些客戶要寄月對帳單」:一個戶號一列,存是否郵寄與備註。畫面上還會顯示從 `BMS001A` 帶出來的一整組客戶聯絡資料(地址、電話、e-mail、法定代理人)供核對,但那些欄位不寫回去。

#### 這支畫面跟其他九支的根本差別

`DSMM906_PO` 把 `Add` / `Update` / `Delete` 三個方法整個 override,自己寫 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-278`),**不呼叫 `base`**:

| 方法 | SQL | 影響 |
|---|---|---|
| `Add` | `INSERT INTO BMS906 (BF_NO, EMP_NO, MAIL_YN, REMARK, UPD_USER, UPD_DATE, UPD_TIME)` | 只寫 7 欄,**沒有 `DATAID` / `STATUS` / 四眼 13 欄** |
| `Update` | `UPDATE BMS906 SET … WHERE BF_NO = :BF_NO` | 同上;而且**用 `foreach` 跑所有列** |
| `Delete` | `DELETE FROM BMS906 WHERE BF_NO = :BF_NO AND EMP_NO = :EMP_NO AND UPD_USER = :UPD_USER` | **必須三個條件全中才刪得掉** |

`Delete` 那個 `UPD_USER` 條件是隱性的權限控制:**只有「最後一次更新者是你」的那一筆才刪得掉**,不符就影響 0 筆,然後丟「刪除時影響筆數等於 0 筆,刪除失敗,請檢查」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255`)。使用者看到的訊息不會告訴他真正的原因。

#### `Delete` 的守衛式寫反了

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241`:

```
if (Rows.Count < 0 && Rows[0].RowState != DataRowState.Deleted)
    throw new ApplicationException("傳入主檔表格至少一個，請檢查");
```

`Rows.Count < 0` **永遠是 false**(筆數不可能是負的),所以這個守衛從來不會成立;而且 `&&` 的右半在筆數為 0 時會先去讀 `Rows[0]`。實際效果:**空集合時不會得到那句友善訊息,而是在 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:247` 的 `Rows[0]` 丟 `IndexOutOfRangeException`**。應該是 `Count < 1` 配 `||`。附錄 E1。

#### `MAIL_YN` 讀進畫面時被改掉

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91`:

```
custMAIL_YN.Value = master.IsMAIL_YNNull() ? "N" : (IsNullOrWhiteSpace(master.MAIL_YN) ? "N" : "Y");
```

判斷式只分「空白 → N」與「非空白 → Y」。**資料庫存 `N` 的那一筆,載入修改畫面會顯示成「Y」**,使用者不改任何東西按存檔,`SetData` 就把畫面上的 `Y` 寫回去(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:200`)。

**這是本模組後果最直接的缺陷:一個「不要寄」的設定,只要有人打開來看一下再存檔,就變成「要寄」。**附錄 E1。

#### 登入者的員工代碼

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:50-55`:

```
if (string.IsNullOrWhiteSpace(emp_Info) == false) m_EMP_NO = emp_Info.Split(',')[1];
```

`GetEMP_INFO` 無原始碼(`ClientBizUtility`,從呼叫端反推是「逗號分隔的員工資訊字串」)。這裡**位置取第 2 段**,沒有檢查段數——回傳值只有一段時會 `IndexOutOfRangeException`。對照 `DSMI001` 同一個呼叫有 `words.Length > 1` 的保護(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:106-111`),**同一件事三支畫面三種寫法**(第三種見 §7.3 的 `DSMR008`)。

`m_EMP_NO` 之後被無條件放進查詢條件(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125`),所以**取不到員工代碼時會變成查 `EMP_NO = ''`,永遠查無資料**,而且沒有任何提示。

#### 查詢條件的三選一

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:126-134`:戶號有填就只用戶號;否則身分證有填就用身分證;否則才用姓名。**三個條件永遠只會送出一個**,使用者同時填三個時另外兩個被靜默忽略。

PO 那邊四個條件全部用 `string.Format` 直接串進 SQL(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:312-350`),連運算子都是從 `Row.Opeartor` 串進去的。姓名那條還加了 `N` 前綴(`N'值'`)——Oracle 的 `N''` 字面量語法,同檔其他三條沒有。

#### 重建名單鈕(`DoExp1`)

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:299-307` → `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:417-443` → SP `S_TA_DSMM906_IMP`(IN:員工代碼、模式固定 `"1"`),`CommandTimeout = 0`(註解寫「此程式讓它永久跑」)。

回傳判斷是 `if (pxy.RebuildBF_List(...) < 0)` 顯示失敗、否則顯示「執行完成」。而 `RebuildBF_List` 回傳的是 `ExecuteNonQuery` 的影響筆數;Oracle 對 SP 呼叫通常回 -1。**假設**:這支按下去很可能永遠顯示「執行失敗」,依據是 `nResult = i` 直接把 `ExecuteNonQuery` 的結果當成功指標(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:431-435`),而同模組 `DSMB001` 的作者遇到同樣情況是硬寫 `i = 1`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:75`)。**要實跑確認。**

#### 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 按新增前 | 戶號歸屬檢查 | 屬於別人 | 阻擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:151-159` |
| 刪除(PO) | 只刪得掉「最後更新者是自己」的那一筆 | 不是 | 阻擋(訊息不說原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:232-233`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255` |
| 刪除(PO) | 空集合守衛 | — | **判斷式寫反,永遠不成立** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241` |
| 載入修改畫面 | `MAIL_YN` 非空白一律顯示成 `Y` | 永遠 | **記錄不擋(靜默改值)** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` |
| 查詢時 | 一律只看自己的客戶 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:125` |
| 查詢時 | 戶號 / 身分證 / 姓名三選一 | 填多個 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:126-134` |
| 查詢時 | 戶號不在 `BMS001A` | 永遠 | 過濾(無提示,INNER JOIN) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| 按重建鈕 | 無任何確認 | 永遠 | 記錄不擋 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:299-307` |

## 5. 查詢畫面(I)

本模組只有一支:`DSMI001`(業務員每日收入查詢,推測)。單頁(`TabPages = 1`)、唯讀、不走四眼,`architecture.md §6.3` 說的「PO 退化成裸 DAO」在這裡完全成立——`DSMI001_PO` 不繼承任何基底、自己 new 兩個 `Database`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:34-37`)。

### 5.1 結構

| 層 | 特徵 | 錨點 |
|---|---|---|
| UI | `xOneStepProcessForm`,兩個 grid:上面挑基金、下面顯示結果 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:24-32` |
| PO | 唯一的方法是 `Select<T>`,回傳一個**新建的** VDB 而不是改傳入的 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:57-63` |
| 資料 | `DSM006A`(`DSMB001` 產出的)join `CRM002A` / `OFD081A` / `COD009` / `OFD002` / `FSK003` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:71-98` |

`dbPTPF` 這個欄位 new 出來之後**全檔沒有用到**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:37`)。

### 5.2 查詢條件

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:64-145`:

| 條件 | 必填 | 送出的參數 | SQL 長相 |
|---|---|---|---|
| 結存日期(起 / 迄) | **是** | `BAL_DATE_BGN` / `BAL_DATE_END` | `to_date(DSM006A.BAL_DATE,'YYYYMMDD') >= to_date(' 值 ','yyyy-MM-dd')` |
| 基金(勾選) | **至少一檔** | `FUND_ID` | `OFD081A.FUND_ID IN (值清單)` |
| 部門代碼 | 否 | `SAL_DEPT_NO` | `DSM006A.AGENT_CODE LIKE '值%'` |
| 員工代號 | 否 | `EMP_NO` | `DSM006A.EMP_NO = '值'` |
| 是否離職 | 否 | `LEAVE_YN` | `COD009.LEAVE_DATE IS (NOT) NULL` |
| 登入者員工代號 | 自動 | `QUERY_EMP_NO` | 進 `CRM002A` 子查詢當權限條件 |

三條前置檢核(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:74-92`):起迄都必填、起 ≤ 迄、**區間不可超過一個月**、基金至少選一項。

### 5.3 哪些條件會靜默濾掉資料

#### (1) `CRM002A` 的權限 INNER JOIN

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89`:

```
JOIN ( 取 CRM002A 裡 EMP_NO = :iQUERY_EMP_NO 且 INQ_EMP_NO <> 'ALL' 的授權列
       UNION ALL
       取同一人 INQ_EMP_NO = 'ALL' 的列,並把 INQ_EMP_NO 換成 '%' ) CRM002A
  ON DSM006A.AGENT_ID = CRM002A.AGENT_ID AND DSM006A.AGENT_CODE = CRM002A.AGENT_CODE
 AND DSM006A.EMP_NO LIKE CRM002A.INQ_EMP_NO
```

這是本模組唯一一段真正的資料列權限:**登入者在 `CRM002A` 裡有幾筆授權,就看得到幾個機構 / 業務員的資料**。設了 `INQ_EMP_NO = 'ALL'` 就用 `'%'` 放行整個機構。

**`CRM002A` 沒有他的資料 → 一筆都查不到,而且畫面只會說「查無資料」**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:227-230`)。權限與沒資料在這支畫面看起來完全一樣。

#### (2) 三條寫死的硬條件〔客戶特定〕

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:95-97`:

```
WHERE DSM006A.AGENT_ID = '0'
  AND ((NVL(A.DEPT_NO,' ')='G' AND (DSM006A.AGENT_CODE LIKE 'S%' OR DSM006A.AGENT_CODE IN ('08001','08101','08201')))
   OR  (NVL(A.DEPT_NO,' ')<>'G'))
```

| 條件 | 效果 |
|---|---|
| `AGENT_ID = '0'` | **只看直銷**,代銷 / 銀行 / 券商的收入永遠查不到 |
| 登入者部門是 `G` 時 | 只看得到 `S` 開頭的機構,外加三個寫死的代碼 `08001` / `08101` / `08201` |
| 登入者部門不是 `G` 時 | 不受上一條限制 |

三個機構代碼與 `G` 這個部門代碼都是寫死的字面量,換站台必須重問。

#### (3) 基金代碼直接串進 `IN (…)`

`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:85-90` 先把勾選的基金組成 `'A','B','C'` 這種字串,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:159` 再原樣接進 `IN (…)`。**沒有綁參數、沒有跳脫**。值來自資料庫撈出來的基金清單,實務上不會被注入,但這是全模組最典型的字串串接寫法(附錄 E7)。

那段組字串還有一個括號放錯位置:`funds.Add("'" + Convert.ToString(row.Cells["FUND_ID"].Value + "'"))`(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:89`)——結尾的單引號被接在 `object` 上再轉字串。結果碰巧一樣,但下一個人改這行會踩到。

#### (4) 日期字串與位置取值

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`:

```
" AND to_date (DSM006A.BAL_DATE , 'YYYYMMDD'  ) >= to_date(' " + beg_date.Substring(0,10) + " ','yyyy-MM-dd')"
```

兩個問題:**日期字面量前後各多一個空白**(Oracle 的 `TO_DATE` 對前導空白通常寬容,**假設**目前能跑就是靠這個;依據是這段程式運行多年),以及 `beg_date.Substring(0, 10)` 是位置取值(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:184`),而畫面傳的是 `Convert.ToString(DateTime)`,長度取決於執行緒的地區設定。

#### (5) 部門條件補了 `%`,這支是對的

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:134` 明確寫 `LIKE '值%'`,而且值有做單引號跳脫。對照 `DSMM001` / `DSMM002` 的 `LIKE` 沒補 `%`(§4.1),**同一個概念三支畫面兩種結果**。

### 5.4 取數之後做的事

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206-218` 在載入資料之前,對結果集的 13 個四眼欄位設 `DefaultValue`:`STATUS = "301"`、`CREATEID` / `ENTRYID` / `VERIFYID` / `APPROVEID` 全填登入者、`REJECTDATE` 填 `1900/01/01`。

**這是一支唯讀查詢畫面,設這些值沒有任何用途**(不會寫回 DB),grid 也把它們全部隱藏(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:168-169`)。看起來是從某支 M 畫面複製過來的殘骸。它唯一的副作用是:`STATUS` 的字面值 `301` 被固定在程式裡,成了 §2.5 反推狀態碼的證據之一。

### 5.5 三支死碼方法

`GetEmpNo`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:258-282`)與 `GetUidCode`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:289-315`)是 `public` 但介面宣告被註解掉(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:26-27`),Control 拿不到;兩支都把參數直接串進 SQL,而且對 `Rows[0]` 的存在性檢查不完整。第三支 `GetEmail` 連方法本體都被註解(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:318-349`),查的是 `AA_USER` 這張平台表。

### 5.6 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢時 | 登入者不在 `CRM002A` | 永遠 | **過濾(訊息只說「查無資料」)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |
| 查詢時 | 只看 `AGENT_ID = '0'` 的直銷 | 永遠 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:95` |
| 查詢時 | 部門 `G` 的人只看 `S%` 與三個寫死代碼 | 是 | 過濾(無提示)〔客戶特定〕 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:96-97` |
| 查詢時 | 基金下拉只列正常狀態的基金 | 永遠 | 過濾(無提示) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:41` |
| 取數失敗 | 例外一律回「執行失敗，請檢查」 | 是 | 記錄不擋(訊息不含原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:236-241` |

## 6. 批次(B)與 WindowsService

本模組只有一支 B 畫面 `DSMB001`,**沒有** WindowsService(母體第 5 節空白,`Dev/ATLAS.DSM/` 底下也沒有任何 service 專案)。

### 6.1 觸發

人工。`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:45-50` 在 `RefreshPage` 直接把查詢鈕關掉、只留執行鈕(註解寫「只供執行」)。畫面上只有兩個欄位:計算日期(起)與(迄)。

### 6.2 輸入

| 欄位 | 檢核 | 錨點 |
|---|---|---|
| 計算日期(起) | **不可大於今日**(離開欄位時驗) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:178-187` |
| 計算日期(迄) | **沒有「不可大於今日」的檢核** | 檔內無對應的 `Validating` |
| 起 vs 迄 | 起 ≤ 迄 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:79-83` |
| 起迄同步 | 填了起、迄還空著,而且起 ≤ 今天 → 自動補成一樣 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:159-166` |

**迄日可以填未來日期**,這是不對稱的地方。

### 6.3 執行前的兩道檢核(`DoCheck`)

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:110-194`,一次跑兩段,結果分別走「阻擋」與「詢問」兩條路:

#### 第一段:有基金未結帳就不給跑(阻擋)

```
SELECT DISTINCT FUND_ID FROM OFD303A
 WHERE CTL_DATE BETWEEN :CAL_DATE_ST AND :CAL_DATE_END AND POST_CTL_CODE <> 'Y'
```

有結果就把基金代碼串成一句「○○,○○基金於計算日期迄日有尚未結帳情形，不可執行批次計算」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:146-152`)。

**`POST_CTL_CODE <> 'Y'` 是 Oracle 三值邏輯的典型陷阱**:該欄為 NULL 時,`NULL <> 'Y'` 的結果是 UNKNOWN,不是 TRUE,那一列**不會**被選出來。也就是說**一檔「結帳旗標還沒寫入」的基金,這道檢核不會抓到它**,批次照跑。與 CAS 的 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` 是同一種缺陷(附錄 E2)。

#### 第二段:已經算過就問一次(詢問)

```
SELECT DISTINCT COUNT(*) FROM DSM006A WHERE BAL_DATE BETWEEN :CAL_DATE_ST AND :CAL_DATE_END
```

有資料就把一句警告字串塞進 `Util.Parameters` 的 `WARNING` 鍵(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:174-178`),UI 收到後跳 Yes/No 對話框,按「否」就取消(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:118-126`)。**這是全模組唯一一處標準的「詢問」型卡控。**

`SELECT DISTINCT COUNT(*)` 的 `DISTINCT` 對聚合結果沒有作用,是多餘的。

### 6.4 寫哪些表

`DSMB001` 自己**一張表都不寫**。它呼叫 `S_TA_DSMB001_EXCUTE_P01`(IN:計算日期起、迄、更新者),`CommandTimeout = 0`,註解寫「此程式讓它永久跑」(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:66-76`)。

從 `DoCheck` 第二段查 `DSM006A` 可以反推:**這支 SP 的產出就是 `DSM006A`**。至於它怎麼算管理費 / 手續費、有沒有套 `DSM905` 的拆帳比例與 `DSM005A` 的離職分攤,**在 repo 內查不到**(§0.3)。

### 6.5 失敗處理:永遠回成功

`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:74-87`:

```
m_db.ExecuteNonQuery(cmd);
i = 1;
...
if (i > 0) { AddResultRow(true, 0, ""); } else { AddResultRow(false, 0, ""); }
```

`i` 在呼叫之後被**硬寫成 1**,所以那個 `if/else` 的 `else` 分支永遠到不了。只要 SP 沒有丟例外,畫面就顯示成功——**SP 內部自行吞掉的錯誤、或處理 0 筆,使用者完全看不出來**。這與 `DSMM901` 的執行(§4.7)是同一種問題,只是這裡更明顯:作者顯然知道 `ExecuteNonQuery` 的回傳值不能用,於是寫死 1。

例外時一律回「執行失敗，請檢查」,**不帶任何原因**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:89-94`)。

### 6.6 與 M 畫面的關係

沒有直接關係。`DSMB001` 不讀也不寫任何 DSM 的維護表,唯一的交集是**它產出的 `DSM006A` 被 `DSMI001` 與 `DSMR003` / `DSMR004` 消費**。要確認「某位業務員的目標與實績」是不是對得上,得自己比對 `DSM001A`(目標)與 `DSM006A`(實績),程式沒有做這件事。

### 6.7 卡控總表

| 時點 | 檢核 | 成立時 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 離開計算日期(迄) | 不可大於今日 | — | **完全沒有檢核** | 檔內無對應事件 |
| 按執行前 | 區間內有基金未結帳 | 是 | 阻擋 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:132-152` |
| 按執行前 | 未結帳判斷用 `<> 'Y'`,NULL 抓不到 | 永遠 | **過濾(無提示)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:136` |
| 按執行前 | 該區間已產生過資料 | 是 | **詢問**(按否就取消) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:174-178` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:118-126` |
| 執行結果 | SP 的成敗 | 永遠 | **記錄不擋(一律回成功)** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:75` |
| 執行例外 | 訊息固定「執行失敗，請檢查」 | 是 | 記錄不擋(不含原因) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:89-94` |

## 7. 報表(R)

```text
[圖] DSM 十七支報表的共同骨架、報表檔選擇方式、後綴變體與權限做法
圖中文字:共同骨架:17 支長得幾乎一樣 / DoValidate() / 日期/基金/路徑 / GetReportFileTitle / 決定 rpt 與中文標題 / PO GetData / SP + RefCursor / ReportLoad / SetParameterValue / 決定要印哪一支 rpt 的三種寫法 / switch 階梯 / DSMR001 等 13 支 / 算術 / DSMR011 九選一 / 固定一支 / DSMR010b 分支被註解 / 40 個 rpt 在 repo / 13 個引用的不在 / 四支後綴變體與本體的關係 / DSMR008 / DSMR008_1 / 同權限邏輯 換兩支 SP / DSMR009 / DSMR009_1 / 同上 / DSMR010 / DSMR010a / 只留第三支 SP / DSMR010b / 借殼改成另一張 / 自己做權限的三種做法〔客戶特定〕 / 丟給 SP 判 / QUERY_EMP_NO 參數 / 畫面直接鎖欄位 / DSMR008 白名單 101722 / 取了卻註解掉 / DSMR009 等於沒權限 / 資料全在版控外 / SP 內容看不到
```

*圖:圖 4 報表群。橘框=值得特別看的做法;灰虛框=平行實作,改一邊要改兩邊;橘虛框=客戶特定或已偏離原設計;黑框=版控外。所有數字都來自版控外的 SP,repo 內看不到算法。*

17 支 R 畫面、40 個 `.rpt`。**全部的資料都來自版控外的 SP**(`DB/` 底下一支 DSM 的報表 SP 都沒有),所以本節只能寫「畫面怎麼決定要跑哪支 SP、要印哪個 `.rpt`、以及有哪些檢核」,**SP 內部的算法查不到**。

### 7.1 共同骨架

17 支長得幾乎一樣,差別只在條件欄位與分支:

| 步驟 | 做什麼 | 代表錨點 |
|---|---|---|
| `FormInitial` | new `ResultVDB` + `FormProxy`;多數會呼叫 `ClientBizUtility.GetEMP_INFO(UserID)` 取登入者員工代碼 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:49-69` |
| `BeforePrintOrPreviewButtonClicked` | `DoValidate()` → `GetReportFileTitle()` 取 (rpt 檔名, 中文標題) → `SetQueryParameters(...)` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:115-128` |
| PO `GetData` | `BeginTransaction` → `GetStoredProcCommand` → `AddOutParameter(RefCursor)` → `LoadDataSet` → `Commit` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:48-105` |
| `ReportLoad` | `SetRptSchemaOnDoc()` 之後一連串 `SetParameterValue`,把查詢條件以文字印在報表抬頭 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:134-176` |

幾個全模組一致的慣例:

- **每支 SP 都設 `cmd.CommandTimeout = 0`**,註解一律是「此程式讓它永久跑」。

- **結果集用 `OutTB` / `OutTB2` / `OutTB3` 這種位置命名的 RefCursor**,`LoadDataSet` 靠參數順序對應 DataTable 順序(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:71-78`)。**加一個游標就要同時改兩處而且順序不能錯**,`change-sp-fn-trigger.md §8.3` 講的就是這件事。

- **條件「全部」的表示法是空字串**,報表抬頭則印中文「全部」(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:152`)。

- **有 Excel 匯出的畫面都要填「轉出路徑」**,檢核兩條:非空、`Directory.Exists`(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:294-305`)。

### 7.2 40 個 `.rpt` 與程式引用的對不上

`Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/` 有 40 個 `.rpt` + 40 個對應的 `ReportClass`,涵蓋 `DSMR001`–`DSMR011`。但程式裡叫得出名字的報表檔還包括:

| 程式引用但 repo 內沒有的 rpt(共 13 個) | 錨點 |
|---|---|
| `DSMR008RPS3` / `DSMR008RPS4` · `DSMR008_1RPS1` / `DSMR008_1RPS2` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:388-391`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:347-351` |
| `DSMR009_1RPS1` / `DSMR009_1RPS2` · `DSMR010aRPS1` / `DSMR010aRPS2` · `DSMR010bRPS` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009_1.cs:259-263`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010a.cs:264-267`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:263` |
| `DSMR012RPS1` / `DSMR012RPS2` · `DSMR013RPS1` / `DSMR013RPS2` / `DSMR013RPS3` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR012.cs:286-290`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR013.cs:259-265` |

為什麼還印得出來:**報表檔是在執行期跟伺服器要的**。`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p1.cs:109-131` 示範了完整流程——`FormProxy.GetReportObject(QueryVDB)` 回傳 `byte[]`,寫成使用者「我的文件」底下一個 GUID 檔名的 `.rpt`,`ReportDocument.Load()` 之後立刻 `File.Delete()`。R 畫面走的是框架包好的同一條路(`SetQueryParameters` 把報表名傳下去)。

**所以 `Report.DSM` 專案裡的 40 個檔只是「有被編進 DLL 的那一批」,不是全部。**要找 `DSMR013RPS1` 的長相,得去部署目錄或報表伺服器,repo 內沒有。

另外 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS31.cs:19` 宣告了一個與 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS3.cs:19` **同名**的 `DSMR001RPS3` 類別。兩個檔同時編譯會衝突——查 `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/Report.DSM.csproj:132-133` 只把 `DSMR001RPS3.cs` 收進去,`…RPS31.cs` 不在 csproj 裡,是**沒被刪乾淨的孤兒檔**。

### 7.3 權限:三支報表自己做,而且做法不同〔客戶特定〕

| 畫面 | 怎麼取登入者 | 之後做什麼 | 錨點 |
|---|---|---|---|
| `DSMR001` `DSMR002` `DSMR007` | `GetEMP_INFO(UserID).Split(',')[1]`,取不到就空字串 | 當 `QUERY_EMP_NO` 參數丟給 SP,**由 SP 決定看得到什麼** | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:56-68`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:330` |
| `DSMR008` `DSMR008_1` | 同上,**再多取第 3、4 段**當部門與業務屬性 | 在畫面上直接鎖死部門 / 員工欄位 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:69-88` |
| `DSMR009` `DSMR009_1` | 取了之後**把送參數那行註解掉** | 等於沒有權限控制 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009.cs:272-287` |

`DSMR008` 那套值得展開(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:106-144`):

| 登入者 | 可查範圍 |
|---|---|
| 業務屬性為 `C` | 部門鎖成自己的部門、員工鎖成自己,兩個欄位都停用 |
| 其他有業務屬性的人 | 部門鎖成自己部門的前 3 碼 |
| 部門前 3 碼是 `S01` 或 `S05` 且業務屬性 `D` | **解除鎖定,可查全部** |
| **員編 `101722`** | **解除鎖定,可查全部**(兩個分支各寫一次) |
| 帳號 `ntaprt` + 數字 5–11 | **解除鎖定,可查全部** |

三個要記住的:

1. **`if (emp_Info.Count() > 1)` 這個守衛是錯的**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74`)。`Count()` 數的是**字串的字元數**,不是逗號分段數;作者要的是 `Split(',').Count() > 1`。所以只要 `GetEMP_INFO` 回傳超過 1 個字元,就會直接去取 `Split(',')[2]` 與 `[3]`——**回傳格式少於 4 段時丟 `IndexOutOfRangeException`,畫面開不起來**。附錄 E1。

2. **員編 `101722` 寫死兩次**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:118`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:126`),`DSMR008_1` 再各寫一次(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:120`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:128`)。這個人離職就沒有人有全域權限。

3. **`Convert.ToInt32(this.UserID.Substring(6).Trim())`**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:136`)對任何 `ntaprt` 開頭且長度 > 6 的帳號都會執行,後綴不是純數字就丟 `FormatException`。

### 7.4 四支後綴變體與本體的關係

| 變體 | 本體 | 關係 | 依據 |
|---|---|---|---|
| `DSMR008_1` | `DSMR008` | **幾乎整支複製**:同樣的權限邏輯(連 `101722` 與 `Count()` 的 bug 都一樣)、同樣的檢核訊息;差別只在 SP 換成 `S_TA_DSMR008_1_Query` / `S_TA_DSMR008_1_QryDetail` 兩支,報表種類從 4 種縮成 2 種 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:69-128` 對 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:69-126`;`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR008_1_PO.cs:63` |
| `DSMR009_1` | `DSMR009` | 同上的關係,SP 換成 `S_TA_DSMR009_1_Query` / `S_TA_DSMR009_1_QryDetail`,報表從 3 種縮成 2 種 | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR009_1_PO.cs:62`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR009_1.cs:259-263` |
| `DSMR010a` | `DSMR010` | 複製後**只留第三支 SP**:`S_TA_DSMR010a_GET_1` 與 `_GET_2` 的呼叫段整段被註解,實際只跑 `S_TA_DSMR010a_GET_3` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:62`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:83`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:99` |
| `DSMR010b` | `DSMR010` | **已經不是同一張報表了**:標題改成「境外基金每日原幣存量」,原本的兩選一分支整段被註解、固定回 `DSMR010bRPS`;PO 讀了 `rpt_type` 卻沒用;結果集的 DataTable 名還沿用 `DSMR010_1`;基金群組那三條檢核也被註解掉 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:263-271`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010b_PO.cs:58-71`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:333-345` |

**結論:`_1` / `a` 是「同一張報表換一組 SP」的平行實作,`b` 是「借殼改成另一張報表」。**改 `DSMR008` 的邏輯時,`DSMR008_1` 要一起改;改 `DSMR010` 時,`DSMR010a` 要一起看,但 `DSMR010b` 不用。

### 7.5 三支值得展開的

#### `DSMR001` — 五支 SP、逐月迴圈、外加一次 DISTINCT

`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:48-224`。分支條件是「報表類型」與「列印類型」兩個參數的組合:

| 條件 | 走哪支 SP |
|---|---|
| 列印類型 ∈ {2,3,4} 且 報表類型 = 1 | `S_TA_DSMR001_GET_3` |
| 列印類型 ∈ {2,3,4} 且 報表類型 ≠ 1(且 ≠ 2 的分支) | `S_TA_DSMR001_GET_4` / `S_TA_DSMR001_GET_5` |
| 其他 且 報表類型 = 1 | **`S_TA_DSMR001_GET_1`,一個月跑一次** |
| 其他 且 報表類型 = 2 | `S_TA_DSMR001_GET_2` |

第三列是重點(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:138-178`):把使用者給的日期區間切成一個月一段,**每個月開一次交易、跑一次 SP、`Merge` 進同一張 `DataTable`**,跑完再用

```
DT.DefaultView.ToTable(true, new string[]{ "AGENT_CODE","AGENT_NAME","EMP_NO","EMP_NAME",
  "BF_NO","BF_NAME","FUND_ID","FUND_SH_NM","ALLOT_DATE","ALLOT_AMT","ALLOT_DATE_B","REDEM_DATE" })
```

做一次 DISTINCT(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:176-177`)。兩個後果:**同一個客戶在兩個月都符合條件時會被折成一列**(這正是「新開百萬客戶清冊」要的),但**這 12 個欄位以外的欄位全部被丟掉**——SP 回的游標若多回欄位,在這裡就消失了;以及 `tran` 在迴圈裡被重新指派(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:152`),**前一個月的交易物件沒有被 `Dispose`**。

另外 `catch` 區塊第一行就是 `tran.Rollback()`(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:213`),而 `tran` 在 `try` 內才賦值——日期轉換那幾行(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:142-143`)丟例外時 `tran` 還是 null,**真正的錯誤會被 `NullReferenceException` 蓋掉**。這個寫法 17 支報表 PO 全都一樣(附錄 E1)。

#### `DSMR011` — 報表檔名用算的

`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR011.cs:249-257`:

```
key = "DSMR011RPS" + ((報表類型 - 1) * 3 + 排序類型)
```

報表類型 1–3、排序類型 1–3,乘出來剛好 1–9,對上 `DSMR011RPS1`–`DSMR011RPS9` 九個檔。程式碼裡還附了算式說明的註解。

**這是全模組唯一一支用算的而不是 `switch` 的**,好處是加組合不用改 code,壞處是任一個選項的值域擴大(例如報表類型多一個 4)就會算出不存在的檔名,而且不會有編譯期或執行期的提示。PO 那側則是**一次抓三個游標,靠「1~3 僅會有一個有資料」的約定**(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:80`)——這個約定只寫在註解裡,SP 那邊沒有任何保證。

#### `DSMR005` — 一個畫面七種報表 + 四種 Excel

`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR005.cs:314-365` 用巢狀 `switch` 決定七種組合(定額 / 不定額 / 168 循環 / 退休財富管理 × 達成表 / 客戶明細,外加一個「By 戶數(含168)」),Excel 匯出再用**另一套幾乎平行的判斷**(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR005.cs:878-907`)決定要跑四個產生函式中的哪一個。兩套的條件不完全相同:列印時「退休財富管理」對到 `DSMR005RPS1` / `DSMR005RPS2`,Excel 那側沒有對應分支。**假設**這個選項不支援 Excel 匯出,依據是 Excel 的 `switch` 只列了 168 與非 168 兩支,要現場確認。PO 側三支 SP 的參數與游標數也都不同(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR005_PO.cs:66-134`)。

### 7.6 畫面端的檢核總表

| 檢核 | 出現在幾支 | 代表錨點 |
|---|---|---|
| 日期(起) 不可大於 日期(迄) | 12 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR001.cs:202-206` |
| 轉 Excel 必須填轉出路徑 + 路徑必須存在 | 10 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:294-305` |
| 基金群組 / 管理費率 / 基金代碼 三選一必選 | 8 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:427-446` |
| 「挑選基金資料」至少勾一筆 | 6 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:355-359` |
| 報表種類 / 部門類別 必須選一個 | 3 支 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:418-425` |
| **統計日期區間資料仍未產生** | 2 支(`DSMR003` `DSMR004`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR003.cs:282-290` |
| **統計方式為人數時,某些報表選項不存在** | 1 支(`DSMR006`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR006.cs:444-448` |
| 業務員有輸入時業務部門必須同時輸入 | 1 支(`DSMR007`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:519-522` |
| 生日 / 結餘 / 未交易日 / 報酬率 四組範圍各自「要嘛都填要嘛都空」且起 ≤ 迄 | 1 支(`DSMR007`) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:526-598` |

兩個特別的:

- **`DSMR003` / `DSMR004` 的「資料仍未產生」是先打一次 DB 才知道的**:`Exists` 去數 `DSM006A` 在該區間的筆數(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR003_PO.cs:112-146`)。這是報表與 `DSMB001` 之間唯一一條程式層的關聯。那段 SQL 用 `string.Format` 把日期串進 `BETWEEN '{0}' AND '{1}'`(`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR003_PO.cs:119-126`),沒有綁參數。

- **`DSMR006` 的「程式無製作此類報表」是最誠實的一條訊息**:統計方式選「人數」而報表選項選「BY促銷代碼」或「BY部門別各基金(EXCEL檔)」時,直接說「程式無製作此類報表，請重新選擇!」(`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR006.cs:444-448`)。

### 7.7 對維護資料的關係

| 報表群 | 吃誰的資料 | 在 repo 內看得到嗎 |
|---|---|---|
| `DSMR003` `DSMR004` | `DSM006A`(`DSMB001` 產出)+ 推測來自 `DSM001A` / `DSM007A` 的目標值 | **只看得到前者** |
| 其餘 15 支 | 交易與結存(`OFD` 那批)、定期定額、客戶組成 + `CPM001A` | 看不到;例 `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR007.cs:900` 只看得到參數 |

**沒有任何一支報表讀 `DSM905` / `DSM005A` 的拆帳與分攤比率**——與 §0.3 的結論一致:那些比率只可能在 `S_TA_DSMB001_EXCUTE_P01` 內被套用。

## 8. 跨模組共用

```text
[圖] DSM 四組跨模組共用的表:DSM001A 給 CAS、OFD374A 給 BMS、BMS906 無人共用、SAL051 全庫共用
圖中文字:A：DSM 自己的表借給 CAS / DSMM001〔DSM〕 / 主明細 · SAL051 限制 / DSM001A DSM002A / 六個業績指標 / CASM006〔CAS〕 / 主明細 · 八部門白名單 / 兩個不同的員工集合 / 不是包含關係 / B：OFD 前綴的表,主檔在 DSM / DSMM060〔DSM〕 / 唯一正規維護入口 / OFD374A / 受益人歸屬業務員 / BMSM001 條件寫死 false / 實際永遠不掛明細 / RSPM004 直接 INSERT / OFDI011 檢查歸屬 / C：BMS 前綴,但 BMS 一行都沒碰 / DSMM906〔DSM〕 / 不走四眼 · 手寫 SQL / BMS906 / 實體只有 7 欄 / xsd 另 18 欄來自 BMS001A / DataTable ≠ 實體表 / BMS 側零引用 / 實測 7 個檔全在 DSM / D：沒有模組的表,影響面最大 / DSMM050〔DSM〕 / 唯一維護者 · 刪除無檢核 / SAL050 SAL051 / 業務部門與人員編制 / BasicCOD_PO / V_SAL051 / 共用員工下拉的來源 / 七個模組 十七個檔 / CLS CRM NFD CPM OFDI
```

*圖:圖 5 跨模組。橘框=主檔或維護入口;白框=表本身;灰虛框=別的模組的用法;橘虛框=風險;黑框=無原始碼。四組的「借法」都不一樣,其中 D 的 SAL051 透過共用員工下拉影響全庫,是本模組風險最高的一張表。*

DSM 有四組跨界的表,每一組的「借法」都不一樣:

| 組 | 表 | 誰是主檔 | 誰是借用方 | 借法 |
|---|---|---|---|---|
| A | `DSM001A` `DSM002A` | DSM 自己 | **CAS**(`CASM006`) | 兩邊都是主明細維護,只是取數範圍不同 |
| B | `OFD374A` | **DSM**(`DSMM060`) | BMS / OFDI / RSP | DSM 是唯一的正規維護入口,別人有讀有寫 |
| C | `BMS906` | **DSM**(`DSMM906`) | 沒有人 | 名字是 BMS 的,但 BMS 一行都沒碰 |
| D | `SAL050` `SAL051` | **DSM**(`DSMM050`) | 全庫(透過共用控件) | DSM 是唯一維護者,影響面最大 |

### 8.1 `DSM001A` / `DSM002A`:同一張表,兩支維護畫面,兩種員工範圍

`CASM006` 與 `DSMM001` 都把這兩張當主明細(`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:32-33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:35-36`),**六個業績指標欄位一模一樣**。`cas.md §8.4` 已經從 CAS 那側寫過一次;從 DSM 這側看,結論相同:

| 面向 | `CASM006` | `DSMM001` |
|---|---|---|
| 部門欄從哪來 | `COD009` 的部門欄 | **`SAL051` 的業務部門欄** |
| 額外 join | 只有 `COD009`(INNER) | `COD009` **加** `SAL051`,兩個都是 INNER |
| 部門限制 | 寫死八個部門的白名單 | 沒有白名單,但被 `SAL051` 的 INNER JOIN 限制成「有在業務部門編制內的人」 |
| 「營業收入 > 0」檢核 | **有**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:77-78`) | **被註解掉**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-79`) |
| 月分配補餘額 | **被註解掉**(`Dev/ATLAS.CAS/Source/UI/UI.CAS/CASM006.cs:259-274`) | **是活的**(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:274-290`) |
| 錨點 | `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:113-127`、`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM006_PO.cs:210` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:113-131`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:144-154` |

**兩支畫面看到的員工集合是兩個不同的集合,不是包含關係**——這一段與 `cas.md §8.4` 的四象限表一致,不重複列。

從 DSM 這側再補兩件 `cas.md` 沒講的:

1. **兩支的「必須大於 0」與「月分配補餘額」剛好互補地壞掉。**`CASM006` 擋得比較嚴(至少營業收入不能是 0)但月分配算錯;`DSMM001` 月分配算對但六個指標都可以是 0。**同一張表可以同時存在「被 CAS 擋下的資料」與「被 DSM 擋下的資料」。**

2. **`DSMM002` 不算在內。**它的主明細是 `DSM007A` / `DSM008A`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:35-36`),`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:149-189` 出現的 `SAL051` 與 `EMP_NO` 條件**全部在註解區塊**,是從 `DSMM001` 複製樣板留下的。搜尋字串時會誤判,別被騙——這一點 `cas.md §8.4` 也提過。

| 改什麼 | 會打到誰 |
|---|---|
| 加 / 改 `DSM001A` `DSM002A` 欄位 | `CASM006Model.xsd` / `CASM006View.xsd` 與 `DSMM001Model.xsd` / `DSMM001View.xsd` 四份都要重生,兩支畫面都要回歸 |
| 改 `CASM006` 的部門白名單 | 只影響 `CASM006` |
| **改 `DSMM050` 的部門成員** | **只影響 `DSMM001`**(它是靠 `SAL051` INNER JOIN 的那一支) |
| 改 `COD009` | **兩支都影響**,而且都是 INNER JOIN,刪一個員工等於他的目標整筆消失 |

### 8.2 `OFD374A`:DSM 是主檔,BMS 是條件掛載的明細

`bms.md` 已經從 BMS 那側寫過(見該文的 `OFD374A` 段與 `AUTO_BELONG_EMP` 段),**兩邊結論一致**,這裡補 DSM 這側的細節:

| 誰 | 怎麼用 | 錨點 |
|---|---|---|
| **`DSMM060`(DSM)** | **主檔**,唯一的正規維護入口。四張表 INNER JOIN 取數;歸屬日期強制為今天 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:33`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:48-62` |
| `BMSM001`(BMS) | 條件掛載成明細,但條件寫死 `false`,**實際永遠不掛** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM001_PO.cs:1901-1915` |
| `BMSM006`(BMS) | 條件寫死 `true`,**永遠掛** | `Dev/ATLAS.BMS/Source/PO/PO.BMS/BMSM006_PO.cs:2203-2214` |
| `OFDI011`(OFDI) | 有一支 `CheckOFD374A` 專門檢查歸屬 | `Dev/ATLAS.OFDI/Source/PO/PO.OFDI/OFDI011_PO.cs:5980-5994` |
| `RSPM004`(RSP) | **直接 `INSERT OFD374A`** | `Dev/ATLAS.RSP/Source/PO/PO.RSP/RSPM004_PO.cs:700` |

從 DSM 這側要補的三件事:

1. **`DSMM060` 的取數是三個 INNER JOIN**(`BMS001A` / `OFD002` / `COD009`,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:50-56`)。`RSPM004` 直接寫進來的資料,只要部門代碼不在 `OFD002` 或員工不在 `COD009`,**`DSMM060` 就查不到、也改不掉那筆**。BMS 那側是把它當唯讀明細,不受這個影響。

2. **欄位定義有兩份且不同構。**DSM 側 `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM060Model.xsd` 宣告 22 欄(4 個業務欄 + 3 個 join 欄 + 15 個四眼相關);BMS 側自己有一份(`bms.md` 已指出)。**加欄位要兩邊一起改**,否則會出現 `architecture.md §5.4` 講的那種靜默失敗。

3. **`DSMM060` 完全沒有業務檢核**(§4.6):不檢查戶號是否已歸屬他人、不檢查員工是否真的在該部門。BMS 側的 `BMSM001` 有一段補業務部門的邏輯,但因為它永遠不掛明細,那段也不會跑(`bms.md` 附錄 E16 的潛伏 bug)。**兩邊都沒有把關的結果,`OFD374A` 的資料品質實際上只由 `DSMM060` 的下拉連動保證。**

### 8.3 `BMS906`:BMS 前綴,DSM 專屬

實測 `grep -rl "BMS906" Dev/` 只命中 7 個檔,**全部在 `Dev/ATLAS.DSM/` 底下**(PO / UI / 兩組 xsd + Designer / `App.config`)。**BMS 模組沒有任何程式碰它。**

為什麼會這樣,repo 內找不到答案。**假設**:這張表原本規劃在 BMS(對帳單是受益人資料的一部分),後來功能改由業務員自己維護,畫面就落在 DSM,表名沒有跟著改。依據有兩條:

- 它的 xsd 裡有 18 個欄位是從 `BMS001A` join 出來的受益人聯絡資料(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:292-306`),形狀比較像 BMS 的東西;

- `DSMM906` 是全模組唯一不走四眼的維護畫面(§4.10),看起來是後來補的、沒有照 DSM 的規格做。

**改這張表要注意兩件事:**

1. **xsd 裡的 `BMS906` DataTable ≠ 實體表 `BMS906`。**實體欄只有 7 個(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:158-159` 的 INSERT 欄位清單),其餘 18 欄是 join 進來的。要加實體欄位,`INSERT` / `UPDATE` 兩段手寫 SQL 也要一起改(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:155-226`)——**框架不會幫你組欄位清單,因為這支把寫入方法整個 override 了**。

2. **它沒有四眼欄位**,所以任何「幫 DSM 的表加四眼稽核」的一次性作業,都必須把 `BMS906` 排除,否則 `DSMM906` 的三段手寫 SQL 會因為 NOT NULL 欄位沒填而爆掉。

### 8.4 `SAL050` / `SAL051`:沒有模組的表,影響面卻最大

**`SAL` 這個前綴在全庫沒有對應的專案、沒有對應的畫面代號。**兩張表的唯一維護入口是 `DSMM050`(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:39-40`)。

它們管的是**直銷的業務組織**:`SAL050` 一列一個業務部門(部門屬性 `DEPT_CD`、主管獎金計算類別 `MGR_BNS_KIND`),`SAL051` 一列一個「部門 × 員工」的編制(業務屬性 `SAL_CD`、獎金制度 `BONUS_TYPE`)。§2.5 有值域。

**影響面比表名看起來大得多。**實測 `SAL051` 在 DSM 之外還被 **17 個檔、7 個模組**引用:

| 模組 | 檔數 | 怎麼用(從檔名與位置推測) |
|---|---|---|
| `Common` | 4 | **共用員工挑選控件的資料來源**,見下 |
| CLS | 4 + 1(Report) | 拜訪紀錄的業務員範圍 |
| CRM | 2 + 2(Report) | 潛在客戶與業務員的對應 |
| NFD.Report · CPM · OFDI | 2 · 1 · 1 | 報表的業務員部門;其餘兩支從檔名看不出用途 |

**最關鍵的是 `Common` 那四個檔。**`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:284-324` 是共用員工資料來源(`EmployeeDataSrc`)的取數 SQL:

```
JOIN (SELECT …, ROW_NUMBER() OVER(PARTITION BY EMP_NO ORDER BY …) RNO FROM V_SAL051) SAL051
  ON COD009.EMP_NO = SAL051.EMP_NO AND SAL051.RNO = 1
… AND SAL051.SAL_DEPT_NO = '<SAL_DEPT_NO 屬性>'
… AND SAL051.SAL_CD <in/not in> ('<SAL_CD 屬性>')
```

也就是說:**任何畫面上的員工下拉,只要設了 `IS_SALE` / `SAL_DEPT_NO` / `SAL_CD` 這三個屬性,背後查的就是 `SAL051`**(2023-05-23 起改查 view `V_SAL051`,註解留在 `Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:277`)。共用控件 `ucAssignEmpNo` 的屬性說明也直接寫「屬於業務部門，將會串接SAL051為部門代碼的查詢條件」(`Dev/Common/Source/CustomControl/UI.CustomControl/ucAssignEmpNo.cs:45`)。

**結論:在 `DSMM050` 刪掉一位業務員的編制,不只 DSM 的畫面查不到他,全庫所有「業務員」下拉都會少一個人。**這張表是全庫等級的主檔,但它的維護畫面(§4.5)的卡控是「逐列警示不擋 + 存檔時寬鬆檢核」,而且**刪除完全沒有檢核**。這是本模組風險最高的一件事。

`SAL050` 在 DSM 之外只被 `Common` 引用,影響面小得多。

另外注意 `SAL051` 有一欄 `TOT_ADD_AC`(整數,無 Caption),repo 內完全沒有程式讀寫它——但它可能被版控外的 SP 使用,**不要因為「沒人用」就刪**。

### 8.5 `SAL051` 在 DSM 內部的五種用法

同一張表,五支畫面五種條件,值得並排看:

| 畫面 | join 方式 | 額外條件 | 效果 | 錨點 |
|---|---|---|---|---|
| `DSMM001` | `JOIN`(INNER) | 無 | 不在編制內的人,他的年度目標整筆查不到 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:129-130` |
| `DSMM003` | `LEFT JOIN` | `SAL_CD = 'C'` | 平常查得到、部門欄空白;**一填部門條件就退化成 INNER** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:123-125`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` |
| `DSMM901` | 子查詢 + `ROW_NUMBER() … RNO = 1` | 原本要求「員工在移轉後部門且未離職」 | **這段 SQL 還在,但呼叫點被換掉了**(§4.7) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:346-354` |
| `DSMM902` | 同上 | 同上,**實際有在用** | 移轉後員工必須真的在移轉後部門 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:339-350` |
| `DSMM903` | `INNER JOIN COD009` | `SAL_CD = 'A'` + 未離職 | 撈直銷部門主管;**一個都沒有時畫面開不起來**(§4.9) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:248-258` |
| `DSMM005` / `DSMM050` | 不直接 join,走共用控件 | `IS_SALE` / `SAL_DEPT_NO` / `SAL_CD` / `AO_CODE` | 只影響下拉候選,不影響已存的資料 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:496-501`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252` |

**`DSMM901` / `DSMM902` 那兩段 `ROW_NUMBER() … RNO = 1` 值得注意**:一個員工同時掛在兩個業務部門時,它靠 `ORDER BY UPDATEDATE DESC, SAL_DEPT_NO` 取「最後更新的那一筆」當唯一部門。也就是說**在 `DSMM050` 改一個人的部門編制,會改變他在移轉檢核裡被認定的部門**,而且沒有任何地方寫下來。

### 8.6 `OFD068A_V02`:一支 view,兩個已知缺陷,對 DSM 的實際影響

這支 view 的問題 `change-sp-fn-trigger.md §7.1` 到 `change-sp-fn-trigger.md §7.3` 已經查過,結論兩條:

1. **view 回 9 欄,共用 typed DataSet 只宣告 5 欄**(`Dev/Common/Source/DataSource/DataEntity.DataSource/OFD_AgentCodeOriginalListModel.xsd:15-22`,DataTable 名字就叫 `OFD068A_V02`)。多回的 `AGENT_CODE_M` / `BANK_KIND` / `AGENT_VALID_CODE` / 一個重複的 `AGENT_ID` 位置會被 `LoadDataSet` 靜默丟掉。

2. **券商那一段的子查詢裡硬寫了一筆常數資料列** `'551','永豐金證券'`(`DB/View/OFD068A_V02.SQL:76`),而該段外層還有 `ROW_NUMBER() … WHERE RNO = 1` 的去重。

DSM 這兩支畫面用它的方式**都不是走那組共用 typed DataSet**,而是 PO 手寫 SQL 直接 join、自己取別名:

| 畫面 | 怎麼用 | 錨點 |
|---|---|---|
| `DSMM901` | `SELECT BANK_BRH_SHNM FROM OFD068A_V02 WHERE AGENT_CODE = :AGENT_CODE`,**當作「這個銷售機構存不存在」的驗證** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:341-344` |
| `DSMM903` | `LEFT JOIN OFD068A_V02 D ON D.AGENT_ID = … AND D.AGENT_CODE = … AND D.AGENT_VALID_CODE = 'Y'`,只取 `BANK_HQ_SHNM AS AGENT_NAME` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:138-141`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:203-206` |

所以**「5 欄 vs 9 欄」那個缺陷不會直接打到這兩支畫面**——它們沒有把 view 載進那組 DataSet,`DSMM903` 甚至用到了 DataSet 沒宣告的 `AGENT_VALID_CODE`(只出現在 join 條件裡,不進結果集)。真正被那個缺陷影響的是任何用共用銷售機構下拉的地方。

**但第 2 條會直接打到 `DSMM901`。**那筆 `'551','永豐金證券'` 是 `UNION ALL` 進 `FSK005` 的,券商段的輸出 `AGENT_CODE` 是 `'K' || 補位後的 STK_BRK`,所以 view 裡會多出一個 `K5510`(或 `K551` 補位後的值)這種**在基礎表裡不存在的銷售機構**。而 `DSMM901.CheckExists` 就是拿 `AGENT_CODE` 去這支 view 查有沒有(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:389-396`):

- **匯入 CSV 時填這個代碼會通過驗證**,然後被送去給 `S_TA_DSMM901_EXE` 執行;

- 第二個效應在 `DSMM903`:券商段的 `ROW_NUMBER() … PARTITION BY 補位後的代碼 ORDER BY NVL(FSK005.STK_BRK, OFD068A.STK_BRK)` 去重時,**這筆常數列有可能贏過真實資料**,讓畫面上的機構簡稱顯示成「永豐金證券」。這一條是**假設**,成不成立要看 `FSK005` 裡 `551` 這個代碼實際存不存在、以及排序鍵是否相同;依據是那個 `PARTITION BY` 用的是補位後的代碼,而常數列與真實列補位後可能落在同一組。

〔客戶特定〕:`551` 與「永豐金證券」都是本站台的值。

**改這支 view 之前先讀 `change-sp-fn-trigger.md §7.2`**:六段 `UNION` 靠位置對齊,加一欄要六段都加,券商那段還要改兩層 SELECT。

### 8.7 共用的 UI 控件與資料來源

DSM 沒有用到 `Dev/Common/Source/DataSource/PO.DataSource` 底下的共用 **PO**(Control 全部只掛自己的 PO),但大量使用共用控件與 DataSource:

| 名稱 | 用在哪 | 為什麼要小心 |
|---|---|---|
| `EmployeeDataSrc` | `DSMM005` `DSMM050` `DSMM903` 的 grid 挑人 | 背後查 `V_SAL051`,見 §8.4 |
| `ucAssignEmpNo` / `ucAssignDeptNo`(從屬性名反推) | 幾乎每支畫面的員工 / 部門欄 | `IS_SALE` / `SAL_CD` / `SAL_DEPT_NO` / `LEAVE_DATE` / `Filter` **五種過濾入口混用**,同一支畫面可能同時設兩種(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:304-306`) |
| `custFundIDClassify` / `custFundIDChoiceType` | 報表與 `DSMI001` 的基金選取 | `FUND_STATUS = "0"` 只列正常狀態基金(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:41`) |
| `GetDropDownDataSrc` vs `GetDropDown9iDataSrc` | `DSMM050` **同時用兩套**取同樣的代碼分類 | 兩套實作可能不同步,見 §4.5 |
| `CodeDataSrc` | `DSMM901` 的 `EXETYPE`(`COD006A` 的 `D1` 分類)、`DSMM902` 的 `FUND_TYPE`(`D4`) | 無原始碼 |
| `ClientBizUtility.GetEMP_INFO` | `DSMM906` `DSMI001` `DSMR001` `DSMR002` `DSMR007` `DSMR008` `DSMR008_1` `DSMR009` `DSMR009_1` | **回傳逗號分隔字串,九支畫面用位置取值,三種不同的長度保護**(§4.10、§5.2、§7.3) |
| `MailUtility.SendMailTo` | `DSMM901` `DSMM902` | 無原始碼;寄件人取不到時用寫死的信箱 |

全部無原始碼,從呼叫端反推。

## 附錄 A. 資料表總表

### A.1 母體的 16 張表

| 表 | 欄位(xsd) | 四眼 | 屬於 | 主檔於 | 明細於 | 本模組怎麼動它 |
|---|---|---|---|---|---|---|
| `DSM001A` | 26 | 有 | DSM | `DSMM001` `CASM006` | — | 主檔,新增 / 修改 / 刪除 |
| `DSM002A` | 24 | 有 | DSM | — | `DSMM001` `CASM006` | 明細,隨主檔 |
| `DSM003A` | 22 | 有 | DSM | `DSMM003` | — | 主檔 |
| `DSM004A` | 20 | 有 | DSM | — | `DSMM003` | 明細 |
| `DSM005A` | 21 | 有 | DSM | `DSMM005`(多筆型) | — | 主檔 + 拷貝(PL/SQL 直接 INSERT) |
| `DSM007A` | 25 | 有 | DSM | `DSMM002` | — | 主檔 |
| `DSM008A` | 24 | 有 | DSM | — | `DSMM002` | 明細 |
| `DSM901` | 23 | 有 | DSM | `DSMM901` | — | 主檔;`BATCHID` 由程式取號 |
| `DSM902` | 31 | 有 | DSM | — | `DSMM901` | 明細;CSV 匯入 + SP 回寫 `EXEAUM` |
| `DSM903` | 22 | 有 | DSM | `DSMM902` | — | 主檔 |
| `DSM904` | 40 | 有 | DSM | — | `DSMM902` | 明細;CSV 匯入 |
| `DSM905` | 27 | 有 | DSM | `DSMM903` | — | 主檔 |
| `DSM9051` | 25 | 有 | DSM | — | `DSMM903` | 明細;`EDATE` 被程式覆寫 |
| `SAL050` | 20 | 有 | **無模組** | `DSMM050` | — | 主檔 |
| `SAL051` | 22 | 有 | **無模組** | — | `DSMM050` | 明細;**全庫共用**(§8.4) |
| `OFD374A` | 22 | 有 | OFD | `DSMM060` | `BMSM001` `BMSM006` | 主檔;歸屬日期強制今天 |
| `BMS906` | 25(實體 7) | **無** | BMS | `DSMM906` | — | 主檔;三個寫入方法全 override |

### A.2 母體沒列、但本文有提到的表

| 表 | 為什麼母體沒列 | DSM 怎麼用 | 錨點 |
|---|---|---|---|
| `DSM006A` | 沒有畫面拿它當主明細,只出現在 `DSMI001Model.xsd`,被判成結果集 | **`DSMB001` 的產出、`DSMI001` 與 `DSMR003` / `DSMR004` 的來源** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:71-78` |
| `COD009` · `OFD002` · `BMS001A` | 外部唯讀 | 員工 / 部門 / 受益人的名稱與離職日,是全模組 join 最多的三張 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:127-128`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:126-127`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:303-305` |
| `OFD068A` · `OFD303A` | 外部唯讀 | 銷售機構簡稱;結帳日判斷 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:237-242`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:185-189` |
| `OFD306` / `OFD306A` · `OFD221` / `OFD221A` | 外部唯讀 | 取「還有庫存」的機構 / 業務員;申購書資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:283-309`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320` |
| `OFD081` / `OFD081A` / `OFD081V` · `FSK003` | 外部唯讀 | 基金名稱與小數位;幣別小數位 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:219-220`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:257-258` |
| `CRM002A` | 外部唯讀(索引判為結果集) | `DSMI001` 的查詢權限 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:79-89` |

## 附錄 B. SP / Function / Trigger / View

### B.1 Stored Procedure

`DB/SP/` 底下**只有一支** DSM 的 SP,其餘全部在版控外(`architecture.md 附錄 B.0` 說全庫只有 16% 的 SP 進版控,DSM 這邊的比例是 1/41)。

| SP | 在 `DB/` | 被誰呼叫 | 參數 |
|---|---|---|---|
| `S_TA_DSMB001_EXCUTE_P01` | **有**(cp950) | `DSMB001` | 計算日起、迄、更新者 |
| `S_TA_DSMM901_EXE` | 沒有 | `DSMM901` 執行 | 期別、執行者 |
| `S_TA_DSMM901_GET` | 沒有 | `DSMM901` 列印 | 期別、比較日、機構;2 個 RefCursor |
| `S_TA_DSMM901_AUM` | 沒有 | `DSMM901` 新增 / 修改明細後 | 期別 |
| `S_TA_DSMM902_EXE` | 沒有 | `DSMM902` 執行(覆核後自動) | 期別、執行者;OUT `strMsg` |
| `S_TA_DSMM906_IMP` | 沒有 | `DSMM906` 重建名單 | 員工代碼、模式(寫死 `"1"`) |
| `S_TA_DSMR001_GET_1`–`_5` | 沒有 | `DSMR001` | 見 §7.5 |
| `S_TA_DSMR002_GET_1` `_2` | 沒有 | `DSMR002` | 申購日起迄、機構、查詢者 |
| `S_TA_DSMR003_GET` · `S_TA_DSMR004_GET` | 沒有 | `DSMR003` `DSMR004` | 日期、報表別、業務別、含員工、含分攤、前 N 名(`DSMR003` 多一個排序) |
| `S_TA_DSMR005_GET_1` `_2` `_3` | 沒有 | `DSMR005` | 5 / 8 / 2 個 IN,游標數也不同 |
| `S_TA_DSMR006_GET_1` `_2` `_4` `_5` | 沒有 | `DSMR006` | 期間、業務別、單位別、報表別、定額別 / 促銷代碼 |
| `S_TA_DSMR007_GET` | 沒有 | `DSMR007` | 結存日、部門、員工…(部分參數被註解) |
| `S_TA_DSMR008_GET_1`–`_4` · `S_TA_DSMR008_1_Query` `S_TA_DSMR008_1_QryDetail` | 沒有 | `DSMR008` `DSMR008_1` |  |
| `S_TA_DSMR009_GET` `_GET_2` `_GET_MBR` · `S_TA_DSMR009_1_Query` `S_TA_DSMR009_1_QryDetail` | 沒有 | `DSMR009` `DSMR009_1` |  |
| `S_TA_DSMR010_GET_1` `_2` `_3` · `S_TA_DSMR010a_GET_3` · `S_TA_DSMR010b_GET` | 沒有 | `DSMR010` `DSMR010a` `DSMR010b` | `DSMR010a` 另兩支被註解;`DSMR010b` 吃計算日起迄 + 戶號 |
| `S_TA_DSMR011_GET` | 沒有 | `DSMR011` | 8 個 IN + 3 個 RefCursor |
| `S_TA_DSMR012_GET_2` `_3` · `S_TA_DSMR013_GET` | 沒有 | `DSMR012` `DSMR013` | `_GET_1` 的註解寫「原來的不用 by Mia」 |

### B.2 Function / Trigger / View

**本模組沒有引用任何 Function 或 Trigger**(母體第 3 節也是 0)。View 三支:

| View | 在 `DB/` | 被誰用 | 說明 |
|---|---|---|---|
| `OFD068A_V02` | **有**(112 行,cp950) | `DSMM901` `DSMM903`(外加 OFD 的 `OFDI011`) | 銷售機構六段 `UNION`,見 §8.6 |
| `DSMM901_V01` | 沒有 | `DSMM901` `DSMM902` 取通知信收件人 | 至少有 `DEPT` / `ROLE901` / `EMAIL` 三欄;`WHERE DEPT = 'S'`〔客戶特定〕;`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259` |
| `V_SAL051` | 沒有 | 共用員工 DataSource | 2023-05-23 起取代直接查 `SAL051`;`Dev/Common/Source/DataSource/PO.DataSource/Basic/BasicCOD_PO.cs:277-291` |

## 附錄 C. 代碼對照

彙整 §2.5,方便查:

| 代碼 | 值 | 意義(反推) | 來源 |
|---|---|---|---|
| `STATUS` | `203` | 刪除待覆核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:277` |
| `STATUS` | `3` 開頭(見到 `301`) | 已覆核 / 生效 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:216`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:206` |
| `SAL_CD` | `A` 部門主管 · `B` `C` 組長 / 業務員 · `D` `E` 助理 / (外)交割人員 | 從訊息文字反推 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:199-214`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:397-422`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:257` |
| `DEPT_CD` | `0` 大部門(3 碼部門專用)· `A` `S` 兩種小部門屬性 |  | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:172-183`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:397`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:411` |
| `FUND_TYPE` | `1` 境外 · `2` 境內 |  | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:222`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:260` |
| `AGENT_ID` | `0`–`5` | 直銷 / 銀行 / 券商 / 投顧 / 投信 / 產壽險 | `DB/View/OFD068A_V02.SQL:11`、`DB/View/OFD068A_V02.SQL:24` |
| `ROLE901` | `E` `V` `A` | 輸入 / 驗證 / 覆核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:127-132` |
| `MAIL_YN` | 空白 = 否;其餘 = 是 | **程式只認這兩種** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` |
| `EDATE` | `29991231` | 無限期 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355` |
| 下拉分類 | `000` 是否 · `300` / `322` 執行狀態(明細 / 主檔,**兩份**)· `412` 基金型別(過濾掉 `C`)· `458` `459` `460` `461` 部門屬性 / 主管獎金類別 / 業務屬性 / 獎金制度 |  | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:66`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:147-151`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:201-204`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-80` |
| `COD006A` 分類 | `D1` `D4` | 移轉類別 / 基金來源 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:152`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:137` |

## 附錄 D. 掃描母體與覆蓋率

### D.1 母體

`docs/_candidates/dsm.md` 由 `atlas_scan.py --module DSM` 產生:

| 類 | 母體數 | 本文處置 |
|---|---|---|
| 畫面 | 29(B 1 / I 1 / M 10 / R 17) | **全部寫到**:M 十支各一節(§4)、I §5、B §6、R §7 + §3.4 一覽 |
| 實體表 | 16 | **全部寫到**:附錄 A.1 逐張列,外加 A.2 補 12 張母體沒列的 |
| SP | 1(`S_TA_DSMB001_EXCUTE_P01`) | §6、附錄 B.1;另補 40 支版控外的 |
| Function / Trigger | 0 / 0 | 確認本模組不用(附錄 B.2) |
| View | 1(`OFD068A_V02`) | §8.6、附錄 B.2;另補 `DSMM901_V01` 與 `V_SAL051` |
| rpt | 40 | §7.2 一覽;另補 13 個「程式引用但 repo 內沒有」的 |
| Service | 0 | 確認本模組沒有(§6) |

### D.2 母體有四處與程式不符,以程式為準

| 母體怎麼說 | 實際 | 為什麼 | 本文寫在哪 |
|---|---|---|---|
| `DSMM005` **沒有主檔 / 明細** | 主檔是 `DSM005A` | PO 用多筆型的 `this.MasterTable.Add(...)`,掃描器只認 `this.MasterTable = new xTableMapping(...)` | §2.1、§0.5 |
| `BMS906` **只有 2 欄** | xsd 有 25 欄(實體 7 欄) | 掃描器只數自封閉且帶 `type=` 的 `<xs:element/>`;`BMS906` 有 23 欄是帶 `<xs:simpleType>` 子節點的寫法 | §2.3、附錄 A.1 |
| 只有 5 張表**有四眼欄位** | **15 張都有**(只有 `BMS906` 沒有) | 同上,四眼欄位多半是帶 `maxLength` 限制的巢狀寫法 | §2.2 |
| 16 張表(不含 `DSM006A`) | `DSM006A` 是本模組最重要的表之一 | 它只出現在 `DSMI001Model.xsd`,沒有畫面拿它當主明細,索引把它歸成結果集 | 附錄 A.2、§6.4 |

驗證方式(不改任何檔):`atlas_scan.py --table BMS906` / `--table DSM005A` / `--screen DSMM005`。

### D.3 `DSMB001` 的「六層不齊」是真缺

母體說 `DSMB001` 缺 model 與 view。`architecture.md 附錄 D.4` 列了兩種假警報(entity 檔名帶 `_9i`、`.Query` 專案改用 `OracleDao` 命名),**`DSMB001` 兩種都不是**:`Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/` 與 `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/` 底下沒有任何 `DSMB001` 開頭的檔、也沒有 `_9i` 變體;DSM 也沒有 `.Query` 專案,PO 就叫 `DSMB001_PO`,命名完全合鐵律。

真正的原因寫在 Control 裡:`Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:38-39` 宣告 `ModelVDBType = typeof(BasicModelVDB)` / `ViewVDBType = typeof(BasicViewVDB)`,**刻意用框架的泛用 VDB**,參數靠 `Util.Parameters` 傳、結果靠 `Util.Result` 回,不需要 typed DataSet。這與 `architecture.md §6.4` 講的「B 跟 I 是同一份程式碼、常常沒有自己的 entity」一致。

唯一的旁枝是 `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs`:一支手寫的 29 行 VDB,UI 在用(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMB001.cs:36`)但 Control 不認識它,裡面的 `UIView` 屬性全 repo 零讀取(附錄 E11)。

### D.4 四支後綴變體不是掃描器的誤判

`DSMR008_1` / `DSMR009_1` / `DSMR010a` / `DSMR010b` 四支在母體裡都是獨立畫面、六層齊。實測它們確實各有完整六層(`_Ctl.cs` / `_Pxy.cs` / `_PO.cs` / `Model.xsd` / `View.xsd` / UI),**是真的四支畫面**,不是 `architecture.md 附錄 D.4` 講的 `_9i` 那種命名假警報。它們與本體的關係見 §7.4。

### D.5 本篇引用的覆蓋率

以 `atlas_scan.py --module DSM --doc docs/modules/dsm.md` 計:

| 類 | 母體 | 本文提到 | 覆蓋率 |
|---|---|---|---|
| 實體表 | 16 | 16 | **100%** |
| 畫面 | 29 | 29 | **100%** |
| SP / View | 2 | 2 | 100% |

母體沒列而本文提到的識別字(外部表、版控外的 SP、repo 內沒有的 rpt、彈出子視窗),全部列進 `meta` 的 `refcheck-ignore`,清單見本文開頭。

### D.6 怎麼自己重跑

```
py -V:3.12 docs\tools\atlas_scan.py --module DSM [--doc docs\modules\dsm.md]
py -V:3.12 docs\tools\atlas_build_doc.py docs\modules\dsm.md --repo-root  --report docs\modules\dsm.refcheck.md
```

## 附錄 E. 讀本文時要注意的地方

讀碼過程中發現的缺陷與陷阱。每條:缺陷 / 影響 / 錨點 / 嚴重度。**沒有任何一條被修改過**,本文只是把它們寫下來。

### E1 會直接產生錯誤資料或讓畫面開不起來的六條

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`MAIL_YN` 讀進畫面時被改成 `Y`**:判斷式只分「空白 → N」「非空白 → Y」,資料庫存 `N` 也會顯示成 `Y` | 一筆「不寄對帳單」的設定,只要有人打開修改畫面再存檔就變成「要寄」。**業務後果最直接的一條** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:91` 配 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:200` | **高** |
| 2 | **`DSMM903` 用 `_DSHead_INFORow` 前只檢查了第一次**:`if (Count > 0)` 之後兩處無條件解參考 | 沒有任何在職的直銷部門主管(`SAL051.SAL_CD = 'A'` 且未離職)時,`FormInitial` 丟 `NullReferenceException`,**畫面完全開不起來** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:205-208` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:217`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:274` | **高** |
| 3 | **`emp_Info.Count() > 1` 數的是字元不是欄位**:作者要的是 `Split(',').Count() > 1` | `GetEMP_INFO` 回傳少於 4 段時 `Split(',')[2]` / `[3]` 丟 `IndexOutOfRangeException`,`DSMR008` / `DSMR008_1` 開不起來 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74-78`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008_1.cs:74-78` | **高** |
| 4 | **`DSMM906.Delete` 的守衛寫反**:`Rows.Count < 0`(不可能成立)且用 `&&` 串一個會解參考的條件 | 空集合時得不到「傳入主檔表格至少一個」的友善訊息,而是在下一行 `Rows[0]` 丟例外 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:239-241` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:247` | 中 |
| 5 | **`catch { tran.Rollback(); }` 但 `tran` 在 `try` 內才賦值**:17 支報表 PO 全部這樣寫 | 連線開失敗、或 `try` 前段(日期轉換)丟例外時,真正的錯誤被 `NullReferenceException` 蓋掉。與 `architecture.md §3.11` 記錄的 `BasicEVAPO` 同型 | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:211-216`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR011_PO.cs:93-98`(其餘 15 支同型) | 中 |
| 6 | **`DSMM901` 的結帳日檢核只在第一次移轉時跑**:`if (row.EXESEQ == 1)` | 同一個批次第二次執行完全不驗結帳日,可以對未結帳的期間動資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:184` | 中 |

### E2 Oracle 三值邏輯:`<> 'Y'` 抓不到 NULL

| 項 | 內容 |
|---|---|
| 缺陷 | `DSMB001` 的「有沒有基金還沒結帳」檢核寫成 `AND POST_CTL_CODE <> 'Y'`。Oracle 裡 `NULL <> 'Y'` 是 UNKNOWN,那一列不會被選出來 |
| 影響 | **結帳旗標還沒寫入(NULL)的基金,不會被判定為「未結帳」**,收入批次照跑,算出來的 `DSM006A` 可能少了那檔基金的資料 |
| 錨點 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:136` |
| 同型前例 | CAS 的 `Dev/ATLAS.CAS/Source/PO/PO.CAS/CASB001_PO.cs:214` |
| 正解 | `AND NVL(POST_CTL_CODE,'N') <> 'Y'` 或 `AND (POST_CTL_CODE IS NULL OR POST_CTL_CODE <> 'Y')` |
| 嚴重度 | **高** |

全模組再掃一次同型寫法:除了這一處,DSM 沒有其他 `<> '值'` 的過濾條件(`DSMI001` 的 `A.DEPT_NO <> 'G'` 那一段用了 `NVL(A.DEPT_NO,' ')` 包起來,是對的,`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:97`)。**寫對的那一處與寫錯的那一處在同一個模組裡**。

### E3 「月分配」三支畫面三種算法,其中一支一定算錯

| 畫面 | 可分配月數 | 修改模式補餘額的判斷 | 結果 |
|---|---|---|---|
| `DSMM001` | `13 - 起算月` | `j < iMONTH_COUNT` | **正確**(但列數多於月數時餘額會被重複寫,見 §4.1) |
| `DSMM002` | 固定 `12` | `j < 12` | 一致,但會跨到次年 |
| `DSMM003` | `13 - 起算月` | **寫死 `j < 12`** | **起算月 ≠ 1 時,餘額永遠不會被寫回去** |

`DSMM003` 那條的實際表現:起算月 7 月 → 6 列明細 → `j` 最多到 6,永遠進不了 `else` → 六列都是 `Math.Floor(年度/6)` → 總和小於年度 → 存檔被「年度淨銷售金額 與 月分配總和不符」擋下 → 使用者只好手動改最後一列。

錨點:`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:196`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:215`;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:201-206`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:213`;`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:121`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:130`。嚴重度:**中**(會被後續檢核擋下,不會產生錯資料,但每次都要手工修)。

### E4 被註解掉但外殼還在的檢核

| # | 被拿掉的檢核 | 錨點 | 註解裡的理由 | 嚴重度 |
|---|---|---|---|---|
| 1 | `DSMM001` 與 `DSMM002` 六個指標「必須大於 0」(主檔 + 明細,各 12 條) | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:78-89`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:104-120`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:78-89` | 無 | 中 |
| 2 | `DSMM002` 查詢的員工代碼起迄檢核 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM002.cs:389-393` | 無(連對應的查詢條件也一起註解了) | 低 |
| 3 | `DSMM901` CSV 匯入「移轉後機構必須是直銷」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:442-448` | 「20190808 … 不檔移轉後需為直銷單位」 | **高**(有票號可查) |
| 4 | `DSMM901` CSV 匯入「移轉前後不可完全相同」 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:452-457` | 「鳳滿說為了活化1不擋 20180820」 | **高** |
| 5 | `DSMM901` `CheckExists` 的「戶號須有該機構 / 員工的結餘」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:355-369`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:440-453` | 同上 | **高** |
| 6 | `DSMM901` 移轉後員工的部門與在職檢核(`sqlEm` 被換成 `sqlEmpNM`) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:426-430` | 「20190812 … 程式名稱及業務移轉範圍」 | **高** |
| 7 | `DSMM902` 執行基準日的 `MaxDate = 今天` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:139` | 無 | 中 |
| 8 | `DSMM902` 覆核後的「執行」通知信 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:279` | 無(改成直接執行) | 低 |
| 9 | `DSMM050` / `DSMM903` 逐列檢核的 7 處 `e.Cancel = true;` | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:364`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:413`(共 7 處) | 無 | 中 |
| 10 | `DSMR010b` 的基金三選一檢核 · `DSMR010a` 的兩支 SP 呼叫 · `DSMI001_PO` 的 `GetEmail` 整支 · `DSMM906_PO` 的 `BeforeDelete` | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR010b.cs:333-345`、`Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR010a_PO.cs:62`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:318-349`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:138-142` | 無;`DSMM906` 的刪除改由 `AND UPD_USER = :UPD_USER` 隱性擋 | 低 |

**第 3–6 條(`DSMM901` 那四條)是同一段時期(2018-08 到 2019-08)為了「活化」業務移轉功能而一起放寬的**,四條都有明確的人名或票號。**要收緊之前先找到那批決策的來源**,不要只看程式。

### E5 併發與參數處理

| # | 缺陷 | 影響 | 錨點 | 嚴重度 |
|---|---|---|---|---|
| 1 | **`BATCHID` 用 `MAX(...)+1` 取號,沒有鎖也沒有序列** | 兩人同時新增拿到同一個期別,第二個人存檔時撞主鍵 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:58-64`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:57-63` | 中 |
| 2 | **`S_TA_DSMM901_AUM` 在 `foreach` 內重複 `AddInParameter` 同一個名字,沒有 `Parameters.Clear()`** | 主檔多於一列時,同一個 command 累積重複參數 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:131-139` | 中 |
| 3 | **`DSMM903` 用 `static` 欄位存四個常數** | 目前是唯讀常數所以不會互踩,但與 BMS `BMSB901A` 那條「靜態批號兩人同跑互刪」是同一種寫法 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29` | 低 |
| 4 | **`DSMM005.Copy` 的 GUID 只在迴圈外產一次** | 拷貝多個月時,所有新列的 `DATAID` 是同一個值 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:237-244` | 中 |
| 5 | **`DSMR001` 逐月迴圈裡重新指派 `tran`,舊的不釋放** | 一次查 12 個月會開 12 個交易物件,只有最後一個被 `Dispose` | `Dev/ATLAS.DSM.Report/Source/PO/ReportPO.DSM/DSMR001_PO.cs:152` | 低 |
| 6 | **`DSMB001_PO` 在 `finally` 釋放類別層級的 `m_db`** | 目前因為 PO 每次 new 而不出事;PO 若改成共用實例,第二次呼叫就拿到已釋放的連線 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:31` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:95-99` | 低 |
| 7 | **`DSMM903_PO` / `DSMM906_PO` 各自 new 一個獨立的 `Database`** | 那些查詢不在四眼的交易裡,讀到的是交易外的資料 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:30`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:28` | 低 |

### E6 位置取參數

`ClientBizUtility.GetEMP_INFO(UserID)` 回傳一個逗號分隔字串(無原始碼),九支畫面用位置取值,**三種不同的長度保護**:

| 寫法 | 用在哪 | 安全嗎 | 錨點 |
|---|---|---|---|
| `if (非空白) { …Split(',')[1] }` | `DSMM906` `DSMR001` `DSMR002` `DSMR007` `DSMR009` `DSMR009_1` | **否**,單段回傳就爆 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM906.cs:52-55` |
| `if (words.Length > 1 && words[1] != "")` | `DSMI001` | **是** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:106-111` |
| `if (emp_Info.Count() > 1) { …[2]; …[3] }` | `DSMR008` `DSMR008_1` | **否**,而且守衛本身寫錯(E1-3) | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:74-78` |

其他位置取值:

| 位置 | 取什麼 / 沒保護時的後果 | 錨點 |
|---|---|---|
| `custDEPT_NO.Value.Substring(0, 1)` · `LEAVE_DATE.Substring(0, 4)` + `Convert.ToInt16` | 部門第 1 碼判直銷 / 離職年份;空字串或格式非 `yyyy…` 丟例外 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:494`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005.cs:516` |
| `xUserDept.Substring(0, 3)` · `UserID.Substring(6)` + `Convert.ToInt32` | 部門前 3 碼 / 列印帳號序號;少於 3 碼或後綴非數字丟例外 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:110`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:136` |
| `beg_date.Substring(0, 10)` | 日期前 10 碼;短於 10 碼丟例外 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172` |

### E7 SQL 層面的髒寫法

| # | 寫法 | 出現處 | 嚴重度 |
|---|---|---|---|
| 1 | **查詢值直接串進 SQL,不綁參數也不跳脫**(`DSMM001_PO` `DSMM002_PO` `DSMM003_PO` `DSMM903_PO` `DSMM906_PO` `DSMI001_PO` `DSMR003_PO` `DSMR004_PO` 全部);唯一做跳脫的是 `DSMM050_PO`,真正綁參數的只有 `DSMM005_PO` `DSMM060_PO` `DSMM901_PO` `DSMM902_PO` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:140`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:318`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:139`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM060_PO.cs:58` | 中(`DSMM906` 的姓名 / 身分證是使用者自由輸入) |
| 2 | **`LIKE` 條件不補 `%`**,等同於 `=` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:148`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:146` | 中 |
| 3 | **`LEFT JOIN` 被 `WHERE` 條件退化成 INNER** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:123-125` 配 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM003_PO.cs:147` | 中 |
| 4 | 舊式逗號 join · `ORDER BY` 被註解且註解裡是別的畫面的欄位 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:178`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM050_PO.cs:150` | 低 |
| 5 | 日期字面量前後多空白 · `SELECT DISTINCT COUNT(*)` · `SYSDATE ASENTRYDATE` 別名黏字 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:172`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:161`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:271` | 低 |
| 6 | 綁定變數當分支開關(`AND :FUND_TYPE = '2'` … `UNION` … `= '1'`) | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:304-320` | 低(兩段的 join 對象不同,很容易只讀一半) |
| 7 | 參數型別與欄位型別不符:`BF_NO` / `BATCHID` 是 decimal 卻綁 `Varchar2` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:369`(同檔 `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:358` 用 `Decimal`)、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:117` | 低 |

### E8 有訊息但沒有 `return` / 訊息誤導

| # | 情況 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `DSMM050` / `DSMM903` 的逐列檢核顯示訊息但 `e.Cancel` 被註解 | E4-10 | 中 |
| 2 | 訊息文字或掛的控件對不上:`DSMM903` 的「計算日(迄)」寫成「計算日(起)」、`DSMM050` 的獎金類別訊息掛在部門屬性上、`DSMM005p0` 的五條訊息全掛在業績年月上 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:167`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:167`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM005p0.cs:141` | 低 |
| 3 | `DSMM050` / `DSMM903` 的 `BeforeRowUpdate` 每段檢核前都 `ValidateErrList.Clear()`,**只看得到最後一條錯誤** | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:360`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:369`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:378` | 低 |
| 4 | `DSMM906` 刪除失敗只說「影響筆數等於 0 筆」,不說真正原因是 `UPD_USER` 不符;`DSMI001` 權限不足與真的沒資料**都顯示「查無資料」** | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:254-255`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:227-230` | 中 |
| 5 | `DSMB001` / `DSMM903` / `DSMM005` 的例外一律回固定字串,不帶原因 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:92`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:272` | 中 |
| 6 | **相反的問題**:`DSMM901` / `DSMM902` 的 `catch` 把 `ex.ToString()` 當結果訊息回給前端;`DSMM906.chkBF_NO_Valid` 也回 `ex.Message` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:268`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:284`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:403-407` | 中(堆疊資訊外洩到 UI) |

### E9 一律回成功 / 回傳值判斷可疑

| # | 情況 | 錨點 | 嚴重度 |
|---|---|---|---|
| 1 | `DSMB001.Execute` 呼叫 SP 之後**硬寫 `i = 1`**,`else` 分支永遠到不了 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMB001_PO.cs:74-87` | **高**(批次失敗看不出來) |
| 2 | `DSMM901.Execute` 的 SP 沒有 OUT 錯誤通道,只要不丟例外就回「執行成功」 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:481-486` | **高** |
| 3 | `DSMM005.Copy` 用 `ExecuteNonQuery` 的回傳值判斷成敗,而它跑的是 PL/SQL 匿名區塊 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM005_PO.cs:290-302` | 中(**假設**成功會被誤報成失敗) |
| 4 | `DSMM906.RebuildBF_List` 同樣拿 `ExecuteNonQuery` 的回傳值當成敗 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:431-435` | 中(**假設**) |

### E10 寫死常數〔客戶特定〕

| 值 | 意義 | 錨點 |
|---|---|---|
| `"B,C"` / `"C"` · `S0%` / `08%` | 兩支畫面挑業務員的業務屬性不同;`DSMM003` 部門下拉只列這兩種開頭 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM001.cs:305`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:207`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM003.cs:205` |
| `'S'→'G'`、`'090'→'I'` | `DSMM002` 取數的部門對照 `DECODE` | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:127` |
| `'0'` / `'S%'` · `30` · `29991231` | `DSMM903` 的四個常數、公單拆帳比例預設值、無限期迄日 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:26-29`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:276`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:355` |
| `AO_CODE = 'Y'` · `DEPT = 'S'` · `6` | `DSMM050` 挑員工的條件;通知信 view 的過濾;員工代碼補 0 的長度 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:252`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM901_PO.cs:259`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:440` |
| `ta-it@example.com` | 寄件人取不到時的退路 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901.cs:113`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM902.cs:100` |
| `'G'`、`08001` / `08101` / `08201` | `DSMI001` 的部門與機構白名單 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:96` |
| `101722` · `S01` / `S05` · `ntaprt` + 5–11 | `DSMR008` / `DSMR008_1` 的三組全域權限白名單 | `Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:117-118`、`Dev/ATLAS.DSM.Report/Source/UI/ReportUI.DSM/DSMR008.cs:135-136` |
| `'551'` / `'永豐金證券'` · `"1"` | view 內硬寫的券商資料列;`DSMM906` 重建名單的模式參數 | `DB/View/OFD068A_V02.SQL:76`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM906_PO.cs:429` |

### E11 同一概念多套實作 / 死碼

| # | 情況 | 錨點 |
|---|---|---|
| 1 | `GetDropDownDataSrc` 與 `GetDropDown9iDataSrc` 對同樣的代碼分類並存 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:77-78` 對 `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:115-117` |
| 2 | `DSMR008` / `DSMR008_1`、`DSMR009` / `DSMR009_1`、`DSMR010` / `DSMR010a` 三組平行實作 | §7.4 |
| 3 | `DSMR001RPS31.cs` 宣告與 `DSMR001RPS3.cs` **同名的類別**,不在 csproj 內,是沒刪乾淨的孤兒 | `Dev/ATLAS.DSM.Report/Source/CrystalReports/Report.DSM/DSMR001RPS31.cs:19` |
| 4 | `DSMBViewVDB` 有 UI 在用,但 Control 宣告的是 `BasicViewVDB`,那個 `UIView` 屬性從沒被讀過 | `Dev/ATLAS.DSM/Source/Entity/UIEntity.DSM/DSMBViewVDB.cs:18-22` 對 `Dev/ATLAS.DSM/Source/Control/Control.DSM/DSMB001_Ctl.cs:39` |
| 5 | `DSMI001_PO` 的 `GetEmpNo` / `GetUidCode` 是 public 但介面宣告被註解,拿不到;同檔 new 了 `dbPTPF` 卻沒用 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:26-27`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMI001_PO.cs:37` |
| 6 | 三個取了卻沒用的變數:`GetDSHeadInfo` 的 `user_id`、`DSMM050` 的 `Employ_Util` 與 `tmpVDB`、`DSMM903` 的 `myEDATE` 初值 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM903_PO.cs:247`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:87-91`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM050.cs:145-146`、`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM903.cs:61` |
| 7 | `DSMM902_PO` 的三個事件方法是空殼,卻照樣掛上去 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:77-81`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:105-108`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM902_PO.cs:115-118` |
| 8 | `SAL051.TOT_ADD_AC` 欄位 repo 內零讀寫(但可能被版控外的 SP 用,**不要刪**) | `Dev/ATLAS.DSM/Source/Entity/DataEntity.DSM/DSMM050Model.xsd` |
| 9 | 十個 PO 的介面註解全寫「覆核層級管理 PO 共用介面」;三個 PO 的明細 region 註解寫「明細資料 SQL(OFD200)」,都與實際功能無關 | `Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:19`、`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM001_PO.cs:211` |

### E12 其他讀碼陷阱

| # | 陷阱 |
|---|---|
| 1 | **`DSMM002_PO` 內出現的 `SAL051` 與 `EMP_NO` 條件全在註解區塊**(`Dev/ATLAS.DSM/Source/PO/PO.DSM/DSMM002_PO.cs:149-189`)。用 grep 找「誰 join 了 `SAL051`」會誤判 |
| 2 | **五處 `App.config` 的 `detailtable` 註解全寫 `DSM002A`**,包含 `DSMM050`(§0.5) |
| 3 | **`DSMM901p0` 那三條檢核比 CSV 匯入嚴格**,同一支畫面兩條輸入路徑兩套規則(§4.7) |
| 4 | **`DSMM903` 的 `EDATE` 使用者打了也會被覆蓋**(§4.9) |
| 5 | **`DSMM060` 修改一筆舊資料會把歸屬日期改成今天**(§4.6) |
| 6 | **`DSMR010b` 的名字像 `DSMR010` 的變體,實際上是另一張報表**(§7.4) |
| 7 | **`DSM006A` 不在母體的 16 張表裡**,但它是整個 E 線的核心(附錄 A.2) |
| 8 | `Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMI001.cs:89` 的括號位置寫錯(單引號被接在 `object` 上),目前結果碰巧正確 |
| 9 | `DSMM901p1` 列印時會把 `.rpt` 寫進使用者的「我的文件」再刪除;`File.Delete` 失敗就留檔(`Dev/ATLAS.DSM/Source/UI/UI.DSM/DSMM901p1.cs:121-124`) |
| 10 | **本模組所有原始檔都是 UTF-8 with BOM**,沒有 BMS 那種混編碼問題(實測 `Dev/ATLAS.DSM/` 與 `Dev/ATLAS.DSM.Report/` 底下的 `.cs` / `.xsd` / `.config` 共 0 個例外) |

### E13 標「假設」的地方一覽

| # | 假設 | 依據 | 怎麼驗 | 在哪一節 |
|---|---|---|---|---|
| 1 | 拆帳比率 / 分攤比率由 `S_TA_DSMB001_EXCUTE_P01` 在 DB 端套用 | repo 內零程式讀 `RATE_A` / `RATE_B` / `SHARE_RATE`;`DSMB001` 的檢核直接查 `DSM006A` | 撈 SP 原始碼 | §0.3 |
| 2 | 本站台的 `STATUS` 是三碼(`2xx` 待覆核、`3xx` 已覆核) | `203` 與 `301` 兩個實際值 + `StartsWith("3")` | 查 `TA_STATUS` 相關代碼表或反編譯 `MappingCode` | §2.5 |
| 3 | `DSMM902` 的 `pkey` 中間有空白會讓第三個 PK 名對不上欄位 | 同檔其他六處都沒有空白 | 看框架怎麼切字串,或實測 grid 的 PK 檢查 | §0.5 |
| 4 | `DSMM005.Copy` 成功時會被誤報成失敗 | `ExecuteNonQuery` 對 PL/SQL 匿名區塊的回傳值定義 | 實跑一次拷貝 | §4.4 |
| 5 | `DSMM906` 的重建名單鈕可能永遠顯示「執行失敗」 | 同上 | 實跑一次 | §4.10 |
| 6 | `DSMM903` 挑人條件 `LEAVE_DATE >= '29991231'` 能用,是因為共用控件把 NULL 當 `29991231` | 其他畫面都寫 `OR LEAVE_DATE IS NULL`,只有這裡沒寫卻還能用 | 看 `EmployeeDataSrc` 的實際 SQL,或實測下拉有沒有人 | §4.9 |
| 7 | `DSMI001` 的日期字面量前後空白目前能跑,是因為 Oracle 容忍前導空白 | 這段程式運行多年 | 換 provider 或改 NLS 前實測 | §5.3 |
| 8 | `DSMR005` 的「退休財富管理」不支援 Excel 匯出 | Excel 的 `switch` 只列 168 與非 168 兩支 | 實測 | §7.5 |
| 9 | view 的常數列 `'551','永豐金證券'` 可能在去重時贏過真實資料 | `PARTITION BY` 用的是補位後的代碼,常數列與真實列可能落在同一組 | 撈 `FSK005` 看 `551` 在不在 | §8.6 |
| 10 | `BMS906` 原本規劃在 BMS,後來功能移到 DSM 但表名沒改 | 18 個欄位來自 `BMS001A`;它是唯一不走四眼的 DSM 維護畫面 | 問業務或查當年的需求文件 | §8.3 |
| 11 | `DSMB001` 的 `m_db` 在 `finally` 被釋放目前不出事,是因為 PO 每次都是新實例 | `architecture.md §2.2` 說 Control 在 `InitializeDataAccessPool` 裡 new | 看框架的 DataAccessPool 生命週期 | §6.6 |
| 12 | 一日作業泳道(§1.5) | `DSMB001` 要求該段日期的基金都已結帳 | 問實際作業人員 | §1.5 |

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。29 支畫面全數涵蓋;16 張表 + 12 張外部表;41 支 SP、3 支 view、40 個 rpt。已與 `cas.md §8.4`(`DSM001A` / `DSM002A`)、`bms.md`(`OFD374A`)、`change-sp-fn-trigger.md §7`(`OFD068A_V02`)對過,結論一致。 |

由 build_doc.py v2.0.0 於 2026-09-14 19:26 產生 · 標題 187 · 圖 5 · 表格 105 · 程式錨點 740 · § 連結 100 · 引用檢查：畫面 35（缺 0） · Table 29（缺 0） · SP 1（缺 0） · View 1（缺 0） · Report 29（缺 0） · 結果集 8（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合

============================================================
【文件】kb/modules/tmk.md
============================================================

# ATLAS TMK 模組 全流程商業邏輯

> 產出日期:2026-09-15(v1)。本文為**純程式碼閱讀彙整**,未修改任何 ATLAS 原始碼。每條規則附程式錨點(`Dev/…/X.cs:行號`),行號為分析當下版本,動手前以最新程式為準。 **建議讀法**:先翻 §1 的圖抓全貌,再看 §2 把四張表的主鍵搞清楚,之後 §3 的清冊配 §4 起的章節就讀得動了。趕時間只讀三段:§0.2(`TMKM001` 與 `TMKM002` 到底差在哪)、§4.1 的差異總表、附錄 E(踩雷)。 **本模組的重心在報表**:14 支畫面裡 11 支是 R,配 24 份 `.rpt`,維護只有 3 支。所以 §7 寫得比 §4 長,這是刻意的。

> ⚠ **本模組的業務意義**(§0)由表名、欄位中文名(`msdata:Caption`)、報表中文名與程式註解**推測**,待選單表回填。ATLAS 沒有把畫面中文名放進版控,14 支畫面沒有一支在非 Designer 檔裡寫出自己的中文名;唯一例外是明細 grid 的標題「電話行銷CALL OUT記錄明細檔」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.Designer.cs:1229`)與彈窗的 MessageBox 標題(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:410`)。 ⚠ **〔客戶特定〕**:專案代碼 `'A0'`、代碼分類 `'P5'` `'P9'` `'84'` `'1C'` `'15'` `'20'` `'440'` `'476'` `'482'`、通話種類前三碼 `'001'` `'004'` `'005'` `'007'`、部門 `'08201'` `'G2'` `'G11'`、銷售機構 `'08001'` `'08201'`、日期門檻 `'20200101'` 全是本站台的值,換站一定要重新確認。 ⚠ **〔共用〕**:標記的表(`CRM003A` `CRM0061A` `COD006A` `BMS001A`)由別的模組維護,TMK 幾乎只讀不寫;唯一的例外是整批匯入會往 `COD006A` 塞一列(§8.4)。

> 前提知識在 `architecture.md`:六層看 `architecture.md §2`、四眼看 `architecture.md §3`、typed DataSet 看 `architecture.md §5`、畫面型別看 `architecture.md §6`、`9xx` 保留段與模組地圖看 `architecture.md §9`。**不要整份讀**。跨模組的另一半在 `crm.md §8`,本文 §8 是從 TMK 這一側做的交叉驗證。平行畫面的分析方法沿用 `bbs.md §4.5`。

## 0. 系統邊界與角色

### 0.1 這模組管什麼(推測)

**一句話:TMK 管「一份外撥名單從進系統、被打電話、留下通聯紀錄,到換人接手、最後被統計成業績與報表」的整段過程。**

「TMK」三個字母的展開在 repo 裡找不到定義,**不要猜**。本文一律用「電話行銷 / CallOut」描述它的範圍,這是從下表推出來的,不是官方名稱。

推測依據六條,逐條可查:

| 依據 | 內容 | 出處 |
|---|---|---|
| 欄位中文名 | `TMK001A` 是「OutBound項目」「OutBound序號」「三年內股票型基金最大申購金額」「風險屬性」;`TMK002A` 是「本次服務人員」「上次服務人員」「再聯絡否」「有效之電話行銷」「電訪重點代碼」 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:25-181`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:287-357` |
| 畫面上的中文標題 | 明細 grid 的標題是「電話行銷CALL OUT記錄明細檔」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.Designer.cs:1229` |
| 報表中文名 | 「通話紀錄統計日報表」「電話行銷聯絡結果統計表」「期間各基金業績彙總表(電訪專員別)」「TM專案名單使用狀況及績效表」「電話行銷專員定額彙總表」「電訪專員個人淨銷售月報表」「電話行銷組客戶組成表」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:192`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:234`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:244`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:185`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:214`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:138`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:193` |
| 流水號種類 | 全模組只跟框架要一種號:OutBound 序號,對應的流水號種類就叫 `TMK001A` | `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`、`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-152` |
| 名單怎麼進來 | `TMKM001` 沒有新增按鈕,名單靠一支 CSV 整批匯入(只有兩欄:戶號、員工編號),伺服端從 `BMS001A` 把客戶資料整批複製成名單 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:314-315`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:89`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:523-586` |
| 通聯原因是兩層代碼 | 大類三碼、小類六碼,小類的前三碼就是大類;報表用前三碼分「有意願」「無意願」「無法聯絡」「勿打擾」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:403`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:415`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:427` |

四條業務線與對應畫面:

| 線 | 在管什麼(推測) | 畫面 | 主 / 明細 |
|---|---|---|---|
| A 專案外撥 | 行銷專案批次匯入名單、指派給電訪專員、逐通電話留紀錄 | `TMKM001` ＋ `TMKM001p0` ＋ `TMKM001p1` | `TMK001A` / `TMK002A` `TMK003A` `TMK0031A` |
| B AO 新開發 | 專員自己開發的客戶,一筆一筆手動建、走四眼 | `TMKM002` ＋ `TMKM002p0` ＋ `TMKM002p1` ＋ `TMKM002p2` | 同上,完全同一組表 |
| C 名單移轉 | 專員離職 / 調動時,把名下名單整批改派給另一位 | `TMKM901` | `TMK901` |
| D 報表 | 通話量、聯絡結果、業績、定額、淨銷售、客戶組成 | `TMKR001`–`TMKR010`、`TMKR901` | 全部來自版控外的 SP |

### 0.2 這模組最反直覺的一件事:`TMKM001` 與 `TMKM002` 共用**全部**的表

母體掃出兩支畫面共用完全相同的主檔 `TMK001A` 與三張明細 `TMK002A` `TMK0031A` `TMK003A`,乍看是「一份程式被複製兩次」。**不完全是。**兩支畫面被主檔上的 `OUTBND_CODE` 欄位切成兩個互不相見的世界,而且被切開的東西不只資料,連「能不能新增」都不一樣:

| 本體 | 平行版 | 共用主 / 明細 | 切分欄位 | 各自的硬條件 |
|---|---|---|---|---|
| `TMKM001` 專案外撥名單 | `TMKM002` AO 新開發客戶 | `TMK001A` / `TMK002A` `TMK003A` `TMK0031A` | `OUTBND_CODE` | `<> 'A0'` vs `= 'A0'` |

五條互相獨立的證據(§4.1 逐條展開):

1. **查詢時各自加硬條件。** `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245` 是 `AND TMK001A.OUTBND_CODE <> 'A0'`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` 是 `WHERE TMK001A.OUTBND_CODE = 'A0'`。**在 A 畫面查不到 B 畫面建的單是設計如此,不是資料掉了。**兩支的 `BuildMasterSQLString` 開頭甚至留著同一句註解「TMKM00x的查詢不會包含A0的項目」——`TMKM002` 那句是從 `TMKM001` 複製過去的,語意剛好相反卻沒改(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:203`)。

2. **新增時寫死型態值。** `TMKM002` 在新增頁把 `OUTBND_CODE` 直接設成 `"A0"` 並鎖成唯讀(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:161`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:299`),送出前再寫一次(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:392`)。`TMKM001` 的 `OUTBND_CODE` 來自整批匯入時選的專案代碼(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:75`)。

3. **能不能新增主檔不一樣。** `TMKM001` 的 `BeforeAdd` 直接 `args.Cancel = true`,註解寫「本功能不支援新增,此段為防線之一」(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:157-161`),前端也把新增 / 刪除 / 清除三顆鈕關掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:313-316`)。`TMKM002` 反過來,`BeforeAdd` 會跟框架要一個 OutBound 序號(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:141-157`)。

4. **只有 `TMKM002` 跑四眼跳號一覽表。** 七個四眼事件(`AfterDelete` / `AfterUnDelete` / `AfterVerify` / `AfterApprove` / `AfterApproveDelete` / `AfterResend` / `AfterReject`)全部掛了 `SrNoCommentProcessor`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`),`TMKM001` 一個都沒掛。

5. **typed DataSet 的形狀不同。** `TMKM001` 的 Model 有七張 DataTable,多了 `OUTBND_TOTAL`(專案總計七個計數)與 `TMK001A1`(CSV 匯入暫存);`TMKM002` 只有六張,多的是 `CRM003A`。見 §2.1。

所以三個候選解釋的答案是:

| 候選 | 判定 | 理由 |
|---|---|---|
| (a) 同一張表兩種用途的平行維護 | **✔ 就是這個** | 切分維度是「名單來源」:`<> 'A0'` 是行銷專案整批匯入的,`= 'A0'` 是專員自己開發的。兩邊資料永久共存、各自有效 |
| (b) 舊版與新版並存 | ✘ | 兩邊都在跑、都在寫同一組表;檔案編碼、語法世代、方法簽名風格也完全一致(六個檔全是 UTF-8 with BOM) |
| (c) 不同角色權限的入口 | ✘(但權限規則確實不同) | 兩支都有主管判斷,只是判斷的來源表不同:`TMKM001` 看 `TMK_MGN_V`、`COD009` 與 `TMK002A` 三路(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`),`TMKM002` 只看 `TMK_MGN_V` 加「服務人員是自己」兩路(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`) |

**維護上最重要的一句話:兩支的逐層相似度從 Control 的 0.91 到 UI 的 0.37 都有(§4.1.1 的量測),所以「改一支要不要改另一支」沒有機械答案——但事實是已經有三個地方只改了一邊(附錄 E1、E2、E3)。**

### 0.3 這模組不管什麼

| 不管 | 誰管(推測) | 依據 |
|---|---|---|
| 受益人基本資料 | BMS | `BMS001A` 只被 `LEFT JOIN` 取姓名、法代與拒絕行銷旗標,從無寫入;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:218-219`。整批匯入那次是 `SELECT … FROM BMS001A` 當來源,也不改它(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:580`) |
| 潛在客戶主檔 | CRM(寫)/ CAS(另一個世界) | `CRM003A` 只被唯讀 join,寫入者是 `CRMM003` 與 `CASM001`,見 `crm.md §8` 與本文 §8.1 |
| 客服進線通聯 | CRM | `CRM0061A` 只在通聯總覽的 `UNION ALL` 裡被讀;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:322-333` |
| 代碼檔維護 | COD | `COD006A` 是 TMK 所有下拉的來源,只讀。**唯一的例外是整批匯入會 INSERT 一列專案代碼**,見 §8.4 |
| 員工與登入者主檔 | 平台 / 人事 | `COD009`、`AA_USER`、`TMK_MGN_V` 只被 join;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:194-200`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68` |
| 申購 / 贖回交易本身 | OFD | TMK 一行都不寫。整批匯入會去 `OFD081A` `OFD221A` `OFD220A` `OFD123A` `OFD601` `OFD607A` 撈六個衍生欄位當名單的參考值(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-584`),之後就不再同步 |
| 業績、手續費、淨銷售的算法 | 版控外的 SP | 11 支報表的口徑全部在 `S_TA_TMKRxxx_GET*` 裡,repo 內查不到。**這是本模組最大的黑箱**,見附錄 B |
| 名單是誰、什麼時候該打 | 不明 | `TMK001A` 有「活動日期(起)/(迄)」與「下次可連絡日期時間」,但沒有任何程式依這兩欄派工或提醒。**假設**:靠報表與人工,依據是 repo 內沒有 B 型畫面也沒有 WindowsService(§6) |

### 0.4 使用角色(推測)

| 角色 | 做什麼 | 程式上的證據 |
|---|---|---|
| 行銷 / 專案管理 | 用 CSV 整批匯入名單、指定專案代碼與活動日期區間 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:54-90` |
| 電訪專員(CallOut 專員) | 打電話、逐通建項次、勾通聯原因、填是否有效電訪、約下次聯絡時間 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:369-506` |
| 電訪主管 | 在 `TMK_MGN_V` 有一列就是主管:可以看全部名單;報表 `TMKR003` 另外用 `GetMasterEmpNo("G11")` 判斷 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227-228`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:226`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57-71` |
| 覆核者 | `TMKM002` 與 `TMKM901` 走四眼;`TMKM001` 只有修改,沒有新增與刪除 | 四眼流程由框架處理,見 `architecture.md §3` |

**資料層級的權限在程式裡看得到,功能層級的看不到。**功能權限由框架平台庫決定(`architecture.md §3`)。程式裡看得到的「誰不能動」有三條:

1. 主檔查詢:三路 `OR` 條件,主管 / 名單建立者或被指定員工 / 本次服務人員,任一成立才看得到(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`)。

2. 明細刪除:`TMKM001` 只能刪指派給自己的項次(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:475-481`)。

3. 明細編輯:彈窗一開就比對「本次服務人員」是不是登入者,不是就把全部欄位鎖成唯讀並關掉確定鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:281-318`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:146-170`)。

### 0.5 全域開關

repo 內**沒有**任何 TMK 專屬的設定檔開關。`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config` 只做三件事:

| 內容 | 作用 | 錨點 |
|---|---|---|
| `mastertable` + `pkey` | 宣告每支畫面的主檔 DataTable 與主鍵,給框架做 grid 的 PK 檢查 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:11`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:19`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:26` |
| `ugrdResult` 的 `column` 白名單 | 查詢結果 grid 顯示哪些欄、順序為何 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:12`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:20`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:27` |
| `supportedRuntime` | 宣告 `.NETFramework,Version=v4.8` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:32` |

三件要記住的:

- **三支畫面都沒有宣告 `detailtable`。**明細表完全由 PO 的 `DetailTable` 決定(§2.1),設定檔上看不出來一支畫面有幾張明細。

- **`TMKM001` 與 `TMKM002` 的結果 grid 只差一欄。**`TMKM001` 排 `EMP_NO`(員工代碼),`TMKM002` 排 `USER_ID_T`(本次服務人員)。其餘 13 欄逐字相同。這一欄就是兩支畫面對「誰負責這筆」的不同定義:專案名單綁員工代碼,AO 名單綁登入帳號。

- **`TMKM901` 的主檔 DataTable 叫 `TMKM901`(畫面代號),不是實體表名 `TMK901`。**`Dev/ATLAS.TMK/Source/UI/UI.TMK/App.config:26` 與 `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36` 的 `xTableMapping("TMK901", "TMKM901")` 對得上,但寫 SQL 或做欄位搬運時兩個名字會打架。

報表側的 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App.config` 有 11 個 section,逐支登記報表畫面,內容只有 `moduleID`,沒有業務開關。

### 0.6 一眼看懂的五個縮寫

| 縮寫 | 展開(推測) | 出現在 |
|---|---|---|
| `OUTBND` | Outbound,外撥。`OUTBND_CODE` 是專案代碼、`OUTBND_NO` 是名單序號、`OUTBND_SRNO` 是同一份名單下的第幾通電話 | `TMK001A` `TMK002A` `TMK003A` `TMK0031A` `TMK901` 的前三欄主鍵 |
| `CALLIN` | 這個字很容易誤會:欄位叫 `CALLIN_DATE` / `CALLIN_CODE`,但它們記的是**外撥這一通**的日期與通聯原因,不是客戶打進來 | `TMK003A` `TMK0031A`;`CRM0061A` 那邊的 `CALLIN_CODE` 才是真的進線 |
| `USER_ID_T` / `USER_ID_L` | This / Last,本次服務人員 / 上次服務人員 | `TMK002A`;新增項次時自動把前一個項次的 `USER_ID_T` 抄成 `USER_ID_L`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:439-443`) |
| `TOPIC` | 電訪重點:`TOPIC_CODE` 取自代碼分類 `'P4'`,`TOPIC_MEMO` 是可以人工改寫的說明 | `TMK002A`;帶出說明的地方在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:269-276` |
| `EFFECT` | 有效電訪:`EFFECT_YN` 是勾選、`EFFECT_CODE` 是種類。**同一份名單只能有一個 `EFFECT_CODE`**,所以改一筆會覆蓋同名單的全部項次 | `TMK002A`;覆蓋邏輯在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447` |

名單的三段式識別碼**永遠是三欄一組**:`OUTBND_CODE` + `OUTBND_NO` + `ID_NO`。四張表的主鍵都從這三欄開始,往下再加 `OUTBND_SRNO`、`CALLIN_DATE`、`CALLIN_SEQ`、`CALLIN_CODE`(§2.2)。寫 SQL 時漏掉任何一段不會報錯,只會多撈到別人的名單。

## 1. 全景與各式流程圖

### 1.1 全景圖

```text
[圖] TMK 全景：名單的兩個來源、兩支共用同組表的維護畫面、三層通話紀錄、名單移轉，以及十一支報表
圖中文字:① 名單怎麼進來：專案名單靠 CSV 整批匯入，AO 個案靠人工一筆一筆開 / CSV 戶號＋員工編號 / TMKM001p1 整批匯入 / BatchAdd 先刪後插 / 四張表整批清掉重建 / TMKM002 人工開單 / OUTBND_CODE 寫死 A0 / COD006A 代碼檔 / 專案代碼寫進 CODE_SORT P5 / ② 名單怎麼用：兩支維護畫面共用同一組表，靠 OUTBND_CODE 是不是 A0 切開 / TMKM001 專案外撥 / 查詢條件 OUTBND_CODE <> A0 / TMKM002 AO 新開發 / 查詢條件 OUTBND_CODE = A0 / TMK001A 名單主檔 / 兩支完全共用 / ③ 一次通話留三層紀錄：項次、通話、通聯原因小類 / TMK002A 通話項次 / 本次上次服務人員 再聯絡 / TMK003A 一次通話 / 通話日期 完成碼 備註 / TMK0031A 通聯原因 / 小類代碼 COD006A 84 / CRM0061A 客服通聯 / 唯讀 COD006A 1C / ④ 名單轉手：TMKM901 把整批名單從一位專員改派給另一位 / TMKM901 勾要移轉的名單 / TMK901 是工單不是業務表 / 覆核時改 TMK002A 服務人員 / 再 MERGE 回 TMK001A 的 EMP_NO / ⑤ 產出：11 支 R 畫面、24 份 rpt，資料全部來自版控外的 SP / TMKR001 TMKR002 TMKR003 / 通話量與聯絡結果 / TMKR004 TMKR005 TMKR007 / 業績與名單使用狀況 / TMKR006 TMKR008 TMKR009 / 定額 買回 淨銷售 / TMKR010 客戶組成表 / 彙總與明細兩份 / TMKR901 定額促銷成效 / 只有 Excel 路能跑 / 13 支報表 SP / 全部不在 DB 資料夾內
```

*圖:圖 1 TMK 全景。橘框=本模組自己的入口與動作；灰虛框=借用或唯讀的外部表；黑框=沒有原始碼的 SP 或已確認的缺陷。第②排那條線就是本模組最重要的一件事：兩支維護畫面共用全部四張表，只靠 OUTBND_CODE 是不是 A0 分家。*

### 1.2 資料表關係

第二張圖畫的是五張自有表的主明細關係、三張只活在 typed DataSet 裡的結果集,以及唯讀 join 進來與只出現在 SQL 字串裡的外部表。**重點在三段主鍵一路帶到底**,以及 `TMK0031A` 那七欄主鍵——它是全模組最長的,改任何一段都會同時打到 `TMKM001` `TMKM002` `TMKM901` 三支畫面。詳細欄位表在 §2.3。

### 1.3 主要維護畫面的四眼與卡控順序

`TMKM001` 與 `TMKM002` 的四眼掛法完全不同,這是兩支最實質的差別之一:

| 階段 | `TMKM001` | `TMKM002` | `TMKM901` |
|---|---|---|---|
| 新增前 | **直接取消**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:160`) | 取 OutBound 序號並回填三張明細的 Key(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-155`) | 前端先把未勾選的列 `Delete()`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:95-99`) |
| 修改前 | 前端檢核:新增的項次有沒有勾通話記錄(詢問)(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:564-571`) | 只跑 `validatorManager1`,沒有額外檢核(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:646-659`) | 同新增(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:102-105`) |
| 更新前 | 掛了 `BeforeUpdate` 但**函式是空的**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:167-169`) | 沒掛(那一行被註解掉,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:41`) | 沒掛 |
| 覆核前 | 無 | 無 | **整段業務邏輯在這裡**:逐列改 `TMK002A` 的服務人員,再 `MERGE` 回 `TMK001A` 的員工代碼(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:154-239`) |
| 七個 After 事件 | 全部沒掛 | 全部掛 `SrNoCommentProcessor`,寫跳號一覽表(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`) | 沒掛 |

**`TMKM001` 實際上不是一支完整的四眼維護畫面,它是一支「只能改明細」的畫面。**主檔九成欄位在 `SetUIEnable` 裡被鎖成唯讀(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:283-311`),能動的只有 `TMK002A` 項次與它掛的兩張子表。

### 1.4 批次 / 報表資料流

本模組**沒有** B 型畫面也沒有 WindowsService(§5、§6),但有一條實質上的批次:`TMKM001` 工具列第二顆自訂鈕開出來的整批匯入彈窗。它的資料流是:

1. 使用者選 CSV(兩欄:戶號、員工編號)→ 讀進 `TMK001A1` 這張只存在於 typed DataSet 的暫存表(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:104-126`)。

2. 選專案代碼 → 呼叫 `CheckExists` 問伺服器這個專案有沒有資料,有就詢問「是否全數刪除」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:143-150`)。

3. 按確定 → `BatchAdd` 在一個交易裡先把四張表這個專案的資料**全部 DELETE**,再從 `BMS001A` 逐筆 INSERT 回 `TMK001A`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-655`)。

4. 如果專案名稱是新填的,順手往 `COD006A` 塞一列代碼分類 `'P5'` 的新代碼,狀態碼寫死 `'301'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623`)。

報表側固定四段鏈:R 畫面收條件 → `ReportFormProxy` 過一次 Remoting → `ReportPO` 呼叫 SP → Crystal Report 或 Excel。四段鏈的形狀與 `architecture.md §6` 描述的 R 型一致,TMK 沒有例外。

### 1.5 一日作業泳道

| 時點 | 誰 | 做什麼 | 落在哪張表 |
|---|---|---|---|
| 專案開始前 | 行銷 | CSV 整批匯入名單、指定專案代碼與活動日期區間 | `TMK001A` 全刪重建、`COD006A` 可能多一列 |
| 專案期間 | 電訪專員 | 在 `TMKM001` 查自己的名單、雙擊新增一個項次、在彈窗勾通聯原因與電訪重點 | `TMK002A` `TMK003A` `TMK0031A` |
| 專案期間 | 電訪專員 | 自己開發的客戶走 `TMKM002`,一筆一單,需覆核 | 同上,但 `OUTBND_CODE` 固定 `'A0'` |
| 隨時 | 主管 | 專員異動時用 `TMKM901` 把名下名單整批改派 | `TMK901` 當工單,覆核時才真的改 `TMK002A` 與 `TMK001A` |
| 日 / 週 | 主管 | `TMKR001` 通話紀錄統計日報表(迄日固定為起日 +6,所以其實是週報) | 版控外 SP |
| 月 | 主管 | `TMKR002` 月報、`TMKR009` 個人淨銷售月報 | 版控外 SP |
| 期間查詢 | 主管 / 專員 | `TMKR003`–`TMKR008`、`TMKR010`、`TMKR901` | 版控外 SP |

**沒有任何自動排程。**`TMKR004` 是唯一宣告成非同步報表的(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:47-51`),其餘都同步跑,而且每支 PO 都把 `cmd.CommandTimeout = 0` 註解成「此程式讓它永久跑」。

## 2. 資料模型

```text
[圖] TMK 五張自有表的主明細關係與主鍵組成、三張只存在於 typed DataSet 的結果集，以及唯讀與隱藏的外部表
圖中文字:① 本模組五張表：一主三明細，加一張跟業務無關的移轉工單 / TMK001A 名單主檔 / PK 三段 加 50 欄 / TMK002A 通話項次 / PK 三段 加 OUTBND_SRNO / TMK003A 一次通話 / PK 再加 CALLIN_DATE / TMK0031A 通聯原因小類 / PK 七欄 全模組最長 / TMK901 名單移轉工單 / PK 加 DATAID 母體 0 欄 / 三段主鍵一路帶到底 / OUTBND_CODE OUTBND_NO ID_NO / ② 只活在 typed DataSet 裡的三張結果集，沒有同名實體表 / CALLIN_RECORD / 三路 UNION ALL 的通聯總覽 / OUTBND_TOTAL / 七個計數 只有 TMKM001 有 / TMK001A1 / CSV 暫存 只有 TMKM001 有 / ③ 唯讀 join 進來的外部表：TMK 一行都不寫 / BMS001A 受益人主檔 / 姓名 法代 拒絕行銷旗標 / CRM003A〔共用〕 / USAGE 1 才是 TMK 的世界 / CRM0061A〔共用〕 / 客服通聯明細 / COD006A 代碼檔 / P5 P9 84 1C 15 20 / ④ 只出現在 SQL 字串裡的：母體與反查工具都看不到 / COD009 員工檔 / UID_CODE 對 EMP_NO / AA_USER 登入者檔 / USERID 對 USERCNAME / TMK_MGN_V 主管視圖 / 有一列就是主管 / OFD 側五張表 / 只在 BatchAdd 的 INSERT 內
```

*圖:圖 2 資料模型。橘框=主檔；白框=明細；橘虛框=不屬於業務流程的工單表〔客戶特定〕；灰虛框=唯讀 join 或只活在 typed DataSet 裡的東西；黑框=只出現在 SQL 字串內、母體與反查工具都掃不到的表。TMK0031A 的七欄主鍵是全模組最長的，改任何一段都會打到三支畫面。*

### 2.1 主表與明細(來自 PO 的 `xTableMapping`)

三支維護畫面的宣告:

| 畫面 | 主檔宣告 | 明細宣告 | 錨點 |
|---|---|---|---|
| `TMKM001` | `xTableMapping("TMK001A", "TMK001A")` | `TMK002A`、`TMK003A`、`TMK0031A`(注意順序:003 在 0031 前面) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:49-54` |
| `TMKM002` | `xTableMapping("TMK001A", "TMK001A")` | `TMK002A`、`TMK003A`、`TMK0031A`(順序相同) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:56-61` |
| `TMKM901` | `MasterTable.Add(xTableMapping("TMK901", "TMKM901"))` ＋ `MasterPKey.Add("DATAID")` | 無 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36-37` |

**`TMKM001` 與 `TMKM002` 的 `xTableMapping` 四行逐字相同,連 `AddNVarCharColumns` 的五行也一樣**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:56-60` vs `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:63-67`):`TMK001A` 的 `BF_NAME` / `MAIL_ADDR`、`TMK002A` 的 `TOPIC_MEMO` / `REMARK`、`TMK003A` 的 `COMMENT1` 五欄宣告成 NVARCHAR。**改其中一支的 mapping 一定要同步另一支。**

`TMKM901` 用的是 `BaseMultiRowEVADaoPO`(多筆覆核),不是 `BaseEVADaoPO`,而且 `MasterTable` 是 `Add` 不是指派——它一張工單掛 N 列名單,整批一起覆核(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:27`)。

### 2.2 主鍵與四眼欄位

從 xsd 的 `msdata:PrimaryKey` 讀:

| 表 | 主鍵欄位(依 xsd 順序) | 欄數 | 四眼欄 | 錨點 |
|---|---|---|---|---|
| `TMK001A` | `OUTBND_CODE` `OUTBND_NO` `ID_NO` | 3 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:731-736` |
| `TMK002A` | `OUTBND_CODE` `OUTBND_SRNO` `ID_NO` `OUTBND_NO` | 4 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:737-743` |
| `TMK003A` | `OUTBND_CODE` `CALLIN_DATE` `OUTBND_SRNO` `ID_NO` `OUTBND_NO` | 5 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:744-751` |
| `TMK0031A` | `OUTBND_CODE` `OUTBND_NO` `ID_NO` `OUTBND_SRNO` `CALLIN_DATE` `CALLIN_SEQ` `CALLIN_CODE` | 7 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:752-761` |
| `TMK901`(DataTable 名 `TMKM901`) | `OUTBND_SRNO` `ID_NO` `OUTBND_NO` `OUTBND_CODE` `DATAID` | 5 | 有 | `Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:133-140` |

三件要注意的:

1. **主鍵欄位順序在四張表之間不一致。**`TMK002A` 把 `OUTBND_SRNO` 排在第二,`TMK0031A` 排在第四。順序對 DataTable 的 `Find()` 有影響,對 SQL 沒有,但讀 code 時很容易看錯。

2. **`TMK003A` 把 `CALLIN_DATE` 放進主鍵。**所以「同一個項次同一天只能有一筆通話記錄」,而且通話日期一旦存檔就不能改——程式也真的這樣做:只有新增模式才讓改通話日期(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:302-307`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:273-278`)。

3. **`TMK0031A` 的主鍵含 `CALLIN_SEQ`,但程式永遠寫 1。**註解直接寫「通訊序號在此暫無義意,固定寫1」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:530-531`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:497-498`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:312-313`)。等於一個永遠不變的主鍵欄。

四眼欄位在五張表上都是同一組 12 欄:`STATUS` `CREATEID` `CREATEDATE` `UPDATEID` `UPDATEDATE` `ENTRYID` `ENTRYDATE` `VERIFYID` `VERIFYDATE` `APPROVEID` `APPROVEDATE` `REJECTID` `REJECTDATE` `DATAFLAG`,值域見 `architecture.md §3`。

### 2.3 欄位中文名總表(來自 xsd `msdata:Caption`)

`TMK001A`(49 欄,扣掉 14 欄四眼與稽核欄):

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `DATAID` | 資料識別碼 | string | 框架欄 |
| `OUTBND_CODE` | OutBound項目 | string | **本模組的切分鍵**,`'A0'` 是 AO 新開發 |
| `OUTBND_NO` | OutBound序號 | string | `TMKM002` 取號時填 11 位;整批匯入填 `i.ToString("D11")` |
| `ID_NO` | 統一編號 | string |  |
| `OUTBND_DATE1` | 活動日期(起) | string | 整批匯入時一次帶給整批 |
| `OUTBND_DATE2` | 活動日期(迄) | string | 同上 |
| `BASE_DATE` | 資料基準日 | string | `TMKM002` 新增時預設 AP Server 系統日 |
| `PR_NO` | 潛在客戶序號 | string | 對 `CRM003A`;**只有 `TMKM002` 用得到** |
| `BF_NO` | 受益人戶號 | decimal | 潛在客戶沒有戶號時為 NULL |
| `BF_NAME` | 姓名 | string | 宣告成 NVARCHAR |
| `BIR_DATE` | 出生日期 | string |  |
| `MAIL_ZIP` | 通訊郵遞區號 | string |  |
| `MAIL_ADDR` | 通訊地址 | string | 宣告成 NVARCHAR;`TMKM002` 存檔前會轉全形 |
| `HM_TEL_AREA` / `HM_TEL` | 住家電話區域碼 / 住家電話 | string |  |
| `OF_TEL_AREA` / `OF_TEL` | 公司電話區域碼 / 公司電話 | string |  |
| `CELL_PHONE` | 手機號碼 | string |  |
| `FAX_TEL_AREA` / `FAX_TEL` | 傳真電話區域碼 / 傳真電話 | string | 來源是 `BMS001A` 的 `FAX_TEL_AREA1` / `FAX_TEL1` |
| `EMAIL` | (xsd 沒填中文名) | string |  |
| `EMAIL_DATE` | EMAIL啟用日 | string | 整批匯入時取 `OFD607A.OPENDAY` |
| `MAX_ALLOT_AMT` | 三年內股票型基金最大申購金額 | decimal | 整批匯入時算一次,之後不再更新 |
| `AGENT_CODE` | 銷售單位 | string | 整批匯入時取最近一筆申購書的銷售機構 |
| `CUST_STYLE` | 風險屬性 | string | 代碼分類 `'15'`;整批匯入時取 `OFD123A` 最新一筆,查無給 `'00'` |
| `EMP_NO` | 員工代碼 | string | **`TMKM001` 的負責人欄**;`TMKM901` 覆核時會 `MERGE` 改它 |
| `AGENT_IN_LAW1` / `AGENT_IN_LAW_ID1` | 法定代理人1 / 法定代理人ID1 | string | 只從 `BMS001A` 讀,不落地 |
| `AGENT_IN_LAW2` / `AGENT_IN_LAW_ID2` | 法定代理人2 / 法定代理人ID2 | string | 同上 |
| `REJ_SELL_CHK` | 拒絕行銷查詢 | string | **只在 `TMKM001` 的 Model 上**,見附錄 E1 |
| `REJ_SELL_DOC` | 拒絕書面文宣 | string | 同上 |
| `REJ_SELL_WEB` | 拒絕網路文宣 | string | 同上 |
| `REJ_SELL_PHONE` | 拒絕電訪 | string | 同上。**這一欄是電訪最該看的旗標** |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:18-251`。`TMKM002` 的同一張表多兩欄少四欄:多 `PR_NAME`(潛在客戶名稱)與 `USER_ID_T`(服務人員),少四個 `REJ_SELL_*`(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:244-245`)。

`TMK002A`(33 欄):

| 欄位 | 中文名 | 型別 |
|---|---|---|
| `OUTBND_SRNO` | 項次 | decimal |
| `USER_ID_T` | 本次服務人員 | string |
| `USER_ID_L` | 上次服務人員 | string |
| `MAIL_AGAIN` | 再郵寄否 | string(代碼分類 `'476'`) |
| `RECONTACT` | 再聯絡否 | string |
| `RECONTACT_DTTM` | 再聯絡日期時間 | string(日期 8 碼 + 小時 2 碼) |
| `RECONTACT_DT` | 改聯絡時間於(日期) | string(**衍生欄,不是實體欄**) |
| `RECONTACT_TM` | 改聯絡時間於(時間) | string(同上) |
| `REMARK` | 備註 | string(NVARCHAR) |
| `EFFECT_YN` | 有效之電話行銷 | string |
| `EFFECT_CODE` | 有效代碼 | string |
| `TOPIC_CODE` | 電訪重點代碼 | string(代碼分類 `'P4'`) |
| `TOPIC_MEMO` | 電訪重點說明 | string(NVARCHAR) |
| `CUST_CLASS` | 客戶等級代碼 | string(代碼分類 `'20'`) |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:286-427`。**`RECONTACT_DT` 與 `RECONTACT_TM` 是 SQL 用 `SUBSTR` 或 `TO_CHAR` 從 `RECONTACT_DTTM` 拆出來的**,不是實體欄;兩支畫面拆法不同,見附錄 E4。

`TMK003A`(25 欄)與 `TMK0031A`(25 欄):

| 表 | 欄位 | 中文名 |
|---|---|---|
| `TMK003A` | `CALLIN_DATE` | 通話日期 |
| `TMK003A` | `READY_YN` | 完成碼(代碼分類 `'440'`,程式預設 `"Y"`) |
| `TMK003A` | `COMMENT1` | 通話記錄備註(NVARCHAR) |
| `TMK003A` | `PR_NO` / `BF_NO` | 潛在客戶序號 / 受益人戶號(從主檔抄下來) |
| `TMK0031A` | `CALLIN_DATE` | 通話日期 |
| `TMK0031A` | `CALLIN_SEQ` | 通話記錄序號(decimal,**永遠寫 1**) |
| `TMK0031A` | `CALLIN_CODE` | 通話種類代碼小類(代碼分類 `'84'`,六碼) |
| `TMK0031A` | `PR_NO` / `BF_NO` | 同 `TMK003A` |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:440-667`。

`TMK901`(DataTable `TMKM901`,母體記 0 欄是因為掃描器找不到它的 DDL):

| 欄位 | 中文名 | 型別 | 備註 |
|---|---|---|---|
| `Checked` | (無中文名) | boolean | **純 UI 欄**,不落地;`BuildDetailSQLString` 把它的預設值設成 true |
| `DATAID` | 資料識別碼 | string | 主鍵之一,一張工單一個值 |
| `OUTBND_CODE` `OUTBND_NO` `ID_NO` `OUTBND_SRNO` | 同前四表 |  | 指向要移轉的那一筆 `TMK002A` |
| `USER_ID_T` | 原CallOut專員 | string |  |
| `USER_ID_NEW` | 新CallOut專員 | string | 覆核時寫回 `TMK002A.USER_ID_T` |
| `USERCNAME` | Callout專員姓名 | string | join `AA_USER` 來的,不落地 |
| `TOPIC_CODE` | 分配CallOut專案 | string |  |
| `BF_NO` / `BF_NAME` | 戶號 / 客戶姓名 | decimal / string | join `TMK001A` 來的 |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:18-127`。

三張只存在於 typed DataSet、沒有同名實體表的結果集:

| 結果集 | 出現在 | 欄位 | 怎麼來的 |
|---|---|---|---|
| `CALLIN_RECORD` | 兩支 M 畫面 | `ID_NO` `TOPIC_CODE`(專案代碼)`UPDATEDATE`(通話日期)`UPDATETIME`(通話時間)`TOPIC_MEMO`(通話種類)`CREATEID`(建檔人員) | 三路 `UNION ALL`:`TMK002A` / `CRM0061A` / `TMK0031A`,見 §8.2 |
| `OUTBND_TOTAL` | **只有 `TMKM001`** | `OUTBND_CODE` `OUTBND_NUM`(專案人數)`CALL_NUM`(已Call過人數)`WILL_NUM`(有意願申購)`UNWILL_NUM`(無意願申購)`OTHER_PRD_NUM`(其他產品)`NOCONTACT_NUM`(無法聯絡)`THK_NUM`(勿打擾) | 一句 7 個純量子查詢的 SQL,見 §4.2 |
| `TMK001A1` | **只有 `TMKM001`** | `EMP_NO`(員工代碼)`BF_NO`(受益人戶號) | CSV 兩欄讀進來的暫存 |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:671-725`。**`TMKM002` 的 Model 反過來多一張 `CRM003A`(主鍵只有 `PR_NO`),但沒有任何程式填它**(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:699`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:1137-1140`),見附錄 E1。

### 2.4 與其他模組共用的表

| 表 | TMK 這側怎麼用 | 誰維護 | 詳見 |
|---|---|---|---|
| `CRM003A`〔共用〕 | 唯讀:通聯總覽帶 `USAGE = '1'`;`TMKM002` 取姓名不帶條件 | `CRMM003`(`USAGE='1'`)、`CASM001`(`USAGE='3'`) | §8.1 |
| `CRM0061A`〔共用〕 | 唯讀:通聯總覽的第二路 | `CRMM003` | §8.2 |
| `COD006A`〔共用〕 | 讀六種代碼分類;**整批匯入會 INSERT 一列 `'P5'`** | COD | §8.4 |
| `BMS001A`〔共用〕 | 唯讀:姓名、法代、四個拒絕行銷旗標;整批匯入時當名單來源 | BMS | §8.3 |
| `COD009` | 唯讀:登入帳號對員工代碼,並用離職日過濾 | 人事 / 平台 | §8.5 |
| `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 唯讀:只在整批匯入那句 INSERT-SELECT 的六個子查詢裡 | OFD | §4.2.3 |

**沒有任何別的模組讀 TMK 自己的五張表。**母體的「跨模組」欄全空,`crm.md §8` 那側也只列到 TMK 讀 CRM,沒有反向。

### 2.5 狀態碼(從程式反推,標來源)

TMK 沒有自己的業務狀態機——名單沒有「已結案 / 進行中」這種欄位。能當狀態看的只有四組代碼,全部來自 `COD006A`:

| 概念 | 欄位 | 代碼分類 | 值域(從程式反推) | 錨點 |
|---|---|---|---|---|
| 完成碼 | `TMK003A.READY_YN` | `'440'` | 程式只寫死過 `"Y"`;查詢時用 `NVL(...,'N') = 'Y'/'N'` 兩分 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:155`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:274`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:278` |
| 是否含已結案清單 | 查詢條件 `READY_YN` | `'482'` | `'Y'` / `'N'` / 空白(不過濾) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |
| 有效代碼 | `TMK002A.EFFECT_CODE` | 畫面上是 `uoptEFFECT_CODE` 選項組 | 程式只寫死過預設值 `"2"`;`TMKM002` 已註解掉的舊碼註明 `"2"` 是「新戶開發(固定)」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:392`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:456` |
| 通話種類 | `TMK0031A.CALLIN_CODE` | `'84'`(小類)/ `'P9'`(大類) | 六碼;前三碼是大類。報表側用到的前三碼見下表 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416` |

`OUTBND_TOTAL` 那句 SQL 把通話種類前三碼寫死成四個統計口徑,**這是全模組唯一能看到通話種類語意的地方**:

| 前三碼 | 統計欄 | 中文名 | 錨點 |
|---|---|---|---|
| `'001'` | `WILL_NUM` | 有意願申購 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391` |
| `'004'` | `UNWILL_NUM` | 無意願申購 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:403` |
| `'005'` | `THK_NUM` | 勿打擾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:427` |
| `'007'` | `NOCONTACT_NUM` | 無法聯絡 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:415` |
| `'004004'`(整六碼) | `OTHER_PRD_NUM` | 其他產品 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:439` |

**注意 `'004004'` 是 `'004'` 的小類**,所以「其他產品」被算在「無意願申購」裡面,兩個數字會重複計。這不一定是錯,但報表上並排時要知道它們不是互斥的。

### 2.6 兩支 M 畫面的 typed DataSet 差異一覽

| 項目 | `TMKM001` | `TMKM002` | 是否同構 |
|---|---|---|---|
| DataTable 張數 | 7 | 6 | ✘ |
| `TMK001A` 欄數 | 49 | 47 | ✘ |
| `TMK002A` / `TMK003A` / `TMK0031A` / `CALLIN_RECORD` | 33 / 25 / 25 / 7 | 33 / 25 / 25 / 7 | ✔ 逐欄相同 |
| 多出來的 | `OUTBND_TOTAL`(8 欄)、`TMK001A1`(2 欄) | `CRM003A`(69 欄,**沒有程式填它**) | ✘ |
| Model 與 View 是否同構 | ✔ | ✔ | — |

錨點:`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM001Model.xsd:15-725`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:15-1105`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM001View.xsd:15-729`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM002View.xsd:15-1105`。

**`TMKM002Model.xsd` 的 `CRM003A` 是整個模組最大的一張死表:69 欄、含四個 `REJ_SELL_*`,但 PO 的 `DetailTable` 沒宣告它、`BuildDetailSQLString` 沒有它的分支、UI 沒有任何控件綁它。**它多半是從 `CASM001` 的 xsd 複製過來的(`crm.md §8.1` 記錄 `CRM003A` 的欄位定義分散在四份 xsd,TMK 這份是第五份),改 `CRM003A` 的欄位時很容易漏掉。

## 3. 畫面清冊

### 3.1 維護 M(3 支)

| 代號 | 中文名(待選單表) | 六層齊不齊 | 主表 | 明細 | SP / Fn | rpt / Service |
|---|---|---|---|---|---|---|
| `TMKM001` | 專案外撥名單維護(推測) | 齊 ＋ 兩支彈窗 | `TMK001A` | `TMK002A` `TMK003A` `TMK0031A` | 無 | 無 |
| `TMKM002` | AO 新開發客戶電話行銷維護(推測) | 齊 ＋ 三支彈窗 | `TMK001A` | `TMK002A` `TMK003A` `TMK0031A` | 無 | 無 |
| `TMKM901` | CallOut 專員名單移轉(推測) | 齊 | `TMK901` | 無 | 無 | 無 |

五支彈窗(母體不列,因為它們不是獨立畫面):

| 彈窗 | 屬於 | 用途 | 錨點 |
|---|---|---|---|
| `TMKM001p0` | `TMKM001` | 通話項次編輯 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:58-65` |
| `TMKM001p1` | `TMKM001` | CSV 整批匯入 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:28-33` |
| `TMKM002p0` | `TMKM002` | 通話記錄編輯(**舊的那一套**) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:46-53` |
| `TMKM002p1` | `TMKM002` | 潛在客戶 / 受益人挑選 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:45-51` |
| `TMKM002p2` | `TMKM002` | 通話項次編輯(**新的那一套**,對應 `TMKM001p0`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:56-63` |

**`TMKM001p1` 與 `TMKM002p1` 名字對仗但功能完全無關**(一個是 CSV 匯入、一個是客戶挑選),這是全模組最容易找錯檔的地方。

### 3.2 查詢 I

**本模組無此類畫面。**母體 `I 0`。原因見 §5。

### 3.3 批次 B

**本模組無此類畫面,也沒有 WindowsService。**母體 `B 0`、`Service 0`。原因見 §6。

### 3.4 報表 R(11 支、24 份 rpt)

| 代號 | 中文名(來自程式字面) | SP | rpt 數 | 結果集 |
|---|---|---|---|---|
| `TMKR001` | 通話紀錄 / 資料需求 / 通話通數 統計**日**報表 | `S_TA_TMKR001_GET` | 3 | `TMKR001_1` `TMKR001_2` `TMKR001_3` |
| `TMKR002` | 通話紀錄 / 資料需求 / 通話通數 統計**月**報表 | `S_TA_TMKR002_GET` | 3 | `TMKR002_1` `TMKR002_2` `TMKR002_3` |
| `TMKR003` | 電話行銷聯絡結果統計表 / 明細表一 / 通話代碼數量期間統計表 | `S_TA_TMKR003_GET_1` `_2` `_3` | 3 | `TMKR003_1A` `TMKR003_1B` `TMKR003_2` `TMKR003_3` |
| `TMKR004` | 期間各基金業績彙總表 / 明細表(電訪專員別) | `S_TA_TMKR004_GET_1` `_2` | 2 | `TMKR004T1` |
| `TMKR005` | TM專案名單使用狀況及績效表(By TM專員 / By 單位別) | `S_TA_TMKR005_GET_1` | 2 | `TMKR005T1` |
| `TMKR006` | 電話行銷專員定額 彙總 / 客戶明細 / 年度配額達成 / 扣款成功統計 | `S_TA_TMKR006_GET_1` `_2` | 5 | `TMKR006T1`–`TMKR006T4` |
| `TMKR007` | 電訪專員期間單筆銷售 手續費明細表 / 彙總表 | `S_TA_TMKR007_GET_1` | 2 | `TMKR007_1` |
| `TMKR008` | 電訪專員各期別基金買回明細表 | `S_TA_TMKR008_GET_1` | 1 | `TMKR008_1` |
| `TMKR009` | 電訪專員個人淨銷售月報表 | `S_TA_TMKR009_GET_1` | 1 | `TMKR009_1` `TMKR009_2` |
| `TMKR010` | 電話行銷組客戶組成表 彙總 / 明細 | `S_TA_TMKR010_GET_1` | 2 | `TMKR010_1` `TMKR010_2` `TMKR010_3` |
| `TMKR901` | 定額促銷活動成效(推測,程式沒給標題) | `S_TA_TMKR901_GET` | **0**(指名的檔不存在) | `TMKR901T0`–`TMKR901T4` |

合計 24 份 `.rpt`,與母體一致。詳細展開在 §7。

### 3.5 一眼看出差別的五件事

1. **11 支 R 對 3 支 M。**這是報表導向的模組:維護只是把資料存起來,價值在統計。

2. **一支 R 畫面不等於一份報表。**`TMKR001` `TMKR002` `TMKR003` 各三份、`TMKR006` 五份,靠畫面上的「報表選項」決定載哪一份 `.rpt`。

3. **每一支 R 都有「轉 Excel」第三條路**,而且 Excel 的版面是手寫在 UI 層的 `GenExcelR1`–`GenExcelR5`,跟 `.rpt` 各寫一次。改報表欄位要改兩個地方。

4. **`TMKR901` 是唯一沒有 `.rpt` 的報表畫面。**它指名 `TMKR901RPS0`,repo 裡沒有這個檔(§7.6)。

5. **查詢權限四種做法並存**:傳 `QUERY_EMP_NO`、傳 `USER_EMP_NO`、前端鎖欄位、什麼都不做(§7.8)。

## 4. 維護畫面(M)— 一支一節

```text
[圖] TMKM001 與 TMKM002 的關係：共用四張表、逐層相似度、真正的行為差異、單邊才有的功能，以及必須同步修改的共同段落
圖中文字:① 兩支共用全部四張表，切分鍵是 OUTBND_CODE 是不是 A0 / TMKM001 專案外撥名單 / SQL 寫死 不等於 A0 / TMKM002 AO 新開發客戶 / SQL 寫死 等於 A0 / TMK001A TMK002A / TMK003A TMK0031A 全共用 / ② 逐層相似度：Control 幾乎同一份，UI 差最遠 / Control 0.91 / 只差兩支自訂方法 / FormProxy 0.72 / 一邊整批匯入一邊取指派人 / PO 0.50 / 主檔 SQL 完全不同 / UI 主檔 0.37 / 1036 行對 597 行 / ③ 真的不同：誰能新增、誰能刪明細、誰跑四眼跳號 / TMKM001 不能新增主檔 / BeforeAdd 直接 Cancel / TMKM002 新增時取序號 / 七個四眼事件寫跳號一覽表 / TMKM001 刪明細會連刪子表 / TMKM002 明細一律不准刪 / ④ 只有一邊有的東西 —— 改一支要不要同步，答案在這排 / 整批 CSV 匯入與範本下載 / 只有 TMKM001 有 / 專案總計七個計數 / 只有 TMKM001 有 / 潛在客戶序號與姓名 / 只有 TMKM002 有 / 拒絕行銷四個旗標 / M001 顯示 M002 撈了沒用 / 通話明細彈窗兩套 / TMKM002 有 p0 與 p2 兩份 / 跳號號別掛成申購書號 / TMKM002 七處全錯 / ⑤ 兩邊一模一樣、改一定要一起改的部分 / 三張明細的組 SQL 與參數拼裝 / 只差一句日期轉換寫法 / 通聯總覽三路 UNION ALL / 逐字相同 含 USAGE 條件 / 再聯絡時間 1 到 24 的檢核 / 兩邊同樣只擋 0 不擋 25 / 查詢條件與姓名 LIKE 串接 / 兩邊同樣把值直接串進 SQL
```

*圖:圖 3 兩支平行畫面。橘框=可從程式判定的差異；橘虛框=只有單邊才有的功能〔客戶特定〕；黑框=已確認的缺陷或兩邊同時錯的地方。第④排下面三格是「有人只改了一邊」的證據，第⑤排是「改一支就一定要改另一支」的清單。*

本章三支:`TMKM001` 與 `TMKM002` 是共用全部四張表的平行畫面,先用 §4.1 一次講清楚它們的關係,再各自展開(§4.2、§4.3),卡控併成一張對照表(§4.4);`TMKM901` 獨立(§4.5)。

### 4.1 `TMKM001` / `TMKM002` — 兩支共用全部四張表的平行畫面

方法沿用 `bbs.md §4.5`:把 `TMKM002` 全檔的代號代換成 `TMKM001` 後做逐行序列比對,再把「只差代號」與「真的不同」分開。

#### 4.1.1 兩支到底有多像:逐層量測

| 層 | `TMKM001` 行數 | `TMKM002` 行數 | 相同行 | 相似度 |
|---|---|---|---|---|
| UI 主檔 | 597 | 1036 | 302 | 0.370 |
| UI 項次彈窗(`p0` vs `p2`) | 574 | 533 | 268 | 0.597 |
| UI 第二彈窗(`p1` vs `p1`) | 173 | 218 | 33 | 0.169 |
| FormProxy | 71 | 56 | 46 | 0.724 |
| Control | 156 | 148 | 139 | 0.914 |
| PO | 700 | 462 | 293 | 0.504 |

**結論:Control 幾乎是同一份、UI 主檔則是兩套不同的東西。**這跟 `bbs.md §4.5.1` 那三對(全層 0.15–0.60)不一樣:BBS 是「重寫」,TMK 是「同一套骨架長出兩種前端」。三個數字要分開解讀:

- **Control 0.914**:兩支的 `BaseController` 樣板逐字相同,差的只有 `TMKM001_Ctl` 多了 `BatchAdd` / `CheckExists` 兩支自訂方法(`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM001_Ctl.cs:52-69`),`TMKM002_Ctl` 多了 `GetLAST_USERID` 與跳號一覽表的兩行 `TransferTable`(`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:52-57`、`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:77`、`Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM002_Ctl.cs:97`)。

- **PO 0.504**:三張明細的組 SQL 與通聯總覽逐字相同,不同的全在主檔 SQL 與四眼事件。

- **UI 主檔 0.370**:`TMKM002` 多出 439 行,幾乎全是 §4.3 講的「挑客戶 → 回填十幾個欄位」那一段,`TMKM001` 完全沒有(它的客戶資料是整批匯入時就決定的)。

`p1` 那一列(0.169)**不要當成差異**:兩支的 `p1` 根本是不同功能,只是檔名撞號(§3.1)。

#### 4.1.2 真的不同的地方

| 面向 | `TMKM001`(專案外撥) | `TMKM002`(AO 新開發) |
|---|---|---|
| 主檔查詢硬條件 | `OUTBND_CODE <> 'A0'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`) | `OUTBND_CODE = 'A0'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227`) |
| 能不能新增主檔 | **不能**,`BeforeAdd` 直接取消(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:157-161`) | 能,取 OutBound 序號(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:148-152`) |
| 能不能刪主檔 | **不能**,前端關掉按鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:314-316`) | 能(受權限鎖控制,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:359-364`) |
| 能不能刪明細 | 能,但只能刪自己的,而且會連刪 `TMK003A` 與 `TMK0031A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:321-357`) | **一律不能**,`BeforeRowsDeleted` 無條件 `e.Cancel = true`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1025-1028`) |
| 四眼跳號一覽表 | 沒有 | 七個事件全掛(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415`) |
| 主管判斷 | 三路 `OR`:`TMK_MGN_V` / `COD009` 對建立者或指定員工 / `TMK002A` 服務人員(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`) | 兩路 `OR`:`TMK_MGN_V` / 服務人員是自己(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`) |
| 主檔 join 誰 | `BMS001A`、`LAST_TMK003A`(CTE)、`TMK_MGN_V`、`COD009`、`MYTMK002A`(CTE) | `TMK002A`(INNER,限 `OUTBND_SRNO=1`)、`BMS001A`、`COD009`、`CRM003A`、`TMK_MGN_V` |
| 主檔一定要有明細嗎 | 不用(註解明講「不需要一定要有明細」,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:247`) | **要**,`JOIN TMK002A … AND TMK002A.OUTBND_SRNO=1`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:219-222`) |
| 「是否含已結案清單」查詢條件 | 有(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280`) | 沒有 |
| 專案總計七個計數 | 有,`OUTBND_TOTAL`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:354-453`) | 沒有(彈窗上七個欄位還在,但填值那段被註解掉,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:93-100`) |
| 潛在客戶 | 完全沒有 | 主軸之一:`PR_NO`、`PR_NAME`、挑選彈窗 `TMKM002p1` |
| 整批匯入 | 有,三顆自訂鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:66-68`) | 沒有 |
| 通聯記錄 grid | `ugrdCALLIN`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:265`) | `ugrdCALLIN1`,舊的 `ugrdCALLIN` 被註解掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:247-248`) |
| 項次彈窗 | 一套(`TMKM001p0`) | **兩套**(`TMKM002p0` 與 `TMKM002p2`),入口不同 |
| 取得維護資料時載通聯總覽 | 在 `AfterGetMaintainData`,連 `OUTBND_TOTAL` 一起(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:128-151`) | 在 `BeforeGetMaintainData` 的主檔分支內(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:120-126`) |

#### 4.1.3 只差代號的部分 —— 改一支就一定要改另一支

下列項目在兩支之間除了代號以外完全一致:

| 段落 | `TMKM001` | `TMKM002` |
|---|---|---|
| `xTableMapping` 與 `AddNVarCharColumns` 九行 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:49-60` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:56-67` |
| 通聯總覽三路 `UNION ALL`(含 `USAGE = '1'`、`CODE_SORT = '1C'` / `'84'`) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:303-352` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:269-319` |
| `TMK003A` 與 `TMK0031A` 的明細 SQL | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:483-508` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:339-362` |
| 姓名 `LIKE` 與再聯絡日期區間三段字串串接 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:254-263` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:236-245` |
| 被註解掉的「必須擇一填寫」查詢前檢核 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:129-139` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:100-111` |
| 被註解掉的 `AddParam` 多帶 `BF_NAME` 那一行 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:251-252` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:233-234` |
| 下次可連絡日期(起)(迄)的成對檢核與 `Leave` 自動補迄日 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:509-515`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:591-595` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:622-628`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1030-1034` |
| 再聯絡時間 1~24 的 `Validating` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:542-552` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:866-876`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:508-518` |
| 通聯原因管理器的建立(代碼分類 `"P9"` / `"84"`、`IsTopTick2`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61-64` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:62-65` |
| 項次彈窗的存檔流程(更新 `TMK002A` → `TMK003A` → 重算 `TMK0031A` 勾選) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:369-506` |
| 有效代碼覆蓋同名單全部項次 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 被註解掉的「只有第一個項次能設有效代碼」 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:374-381` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:345-352` |

#### 4.1.4 已經只改了一邊的三個地方

這一段是本節的重點:程式碼本身可以證明有人只改了一邊。

| # | 現象 | `TMKM001` | `TMKM002` | 影響 |
|---|---|---|---|---|
| 1 | 四個拒絕行銷旗標 | Model 有四欄、畫面四個 checkbox 都填值(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:243-246`) | **SQL 照樣 SELECT 四欄**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:214-217`),但 Model 的 `TMK001A` 沒宣告這四欄(它們被宣告在那張沒人填的 `CRM003A` 上),控件 `Visible = false`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.Designer.cs:2016`),UI 程式一行都沒指派 | **AO 新開發畫面看不到「拒絕電訪」旗標**,但 SQL 每次都白撈四欄 |
| 2 | 再聯絡日期的拆法 | `SUBSTR(RECONTACT_DTTM,1,8)` / `SUBSTR(...,9,2)`,舊的 `TO_DATE` 版被註解掉(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:460-477`) | **還是舊的 `TO_CHAR(TO_DATE(...))` 版**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:326-331`) | `TMKM001` 那邊改過一次是為了避開 `TO_DATE` 對格式不合的值丟 `ORA-01861`;`TMKM002` 沒跟,同一批髒資料在 AO 畫面上會炸 |
| 3 | 通話項次彈窗 | 一套 `TMKM001p0` | **兩套**:`TMKM002p0`(舊,`btnCALLIN` 進去)與 `TMKM002p2`(新,雙擊 grid 進去)。`p0` 撈 `TMK003A` 不帶主鍵條件、刪 `TMK0031A` 不帶篩選(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:255-256`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:269`) | 多項次時走 `p0` 會改到別的項次的通話記錄、刪掉別的項次的通聯原因,見附錄 E3 |

**改一支要不要同步另一支?分三類回答:**

| 類別 | 答案 | 清單 |
|---|---|---|
| 主檔 SQL、四眼事件、能不能新增刪除、潛在客戶、整批匯入、專案總計 | **不用同步**,這些本來就是兩支的差異 | §4.1.2 整張表 |
| `xTableMapping`、三張明細的 SQL、通聯總覽、項次彈窗存檔流程、共同檢核 | **一定要同步**,它們逐字相同 | §4.1.3 整張表 |
| `TMK001A` `TMK002A` `TMK003A` `TMK0031A` 的欄位異動 | **兩份 Model xsd ＋ 兩份 View xsd 共四份都要重生**,兩支畫面都要回歸 | §2.6 |

### 4.2 `TMKM001` — 專案外撥名單維護

#### 4.2.1 用途(推測)

行銷專案把一批客戶整批匯進來,分派給電訪專員;專員在這裡查自己的名單、逐通電話建項次。**主檔完全唯讀**,能動的只有項次與它掛的兩張子表。

#### 4.2.2 查詢條件與「會把資料濾掉而不提示」的部分

| 條件 | 控件 | 傳到 PO 的參數 | 錨點 |
|---|---|---|---|
| OutBound 項目 | `custOUTBND_CODE_0` | `OUTBND_CODE`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:151-154` |
| 是否含已結案清單 | `ucomREADY_YN_0`(代碼分類 `'482'`) | `READY_YN`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:157-160` |
| 統一編號 | `utxtID_NO_0` | `ID_NO`(Like) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:162-165` |
| 姓名 | `utxtBF_NAME_0` | `BF_NAME`(Like) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:168-171` |
| 受益人戶號 | `custBF_NO_0` | `BF_NO`(Equal) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:174-177` |
| 下次可連絡日期(起)(迄) | `udatNext_DATE_ST` / `_END` | `RECONTACT_DTTM_S` / `_E` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:180-184` |

會靜默濾掉資料的有五條:

| # | 條件 | 為什麼會濾掉 | 錨點 |
|---|---|---|---|
| 1 | `AND TMK001A.OUTBND_CODE <> 'A0'` | 設計如此:AO 名單永遠看不到。**但 Oracle 三值邏輯:`OUTBND_CODE` 若為 NULL,`<> 'A0'` 是 UNKNOWN 不是 TRUE**,那筆會被靜默丟掉。`OUTBND_CODE` 是主鍵所以理論上不會 NULL,但這是全模組唯一的 `<>` 比較,同型缺陷在 CAS / CLS / DSM 都中過 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245` |
| 2 | CTE `MYTMK002A` 裡的 `A.OUTBND_CODE <> 'A0'` | 同上,而且這一層是決定「本次服務人員」那一路權限成不成立 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:206` |
| 3 | 三路 `OR` 權限條件 | 不是主管、不是建立者 / 指定員工、也不是任何一通電話的服務人員 → 整筆看不到,沒有任何提示 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244` |
| 4 | `COD009` 的離職日過濾 `NVL(TRIM(A.LEAVE_DATE), '99991231') >= 今天` | 登入者若已離職,`MYEMP_LIST` 是空的,第二路權限直接失效 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| 5 | `NVL(LAST_TMK003A.READY_YN,'N') = 'Y'` / `= 'N'` | 「是否含已結案清單」選了就是硬過濾;**它比的是該名單最後一通電話的完成碼**,不是整份名單 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |

第 5 條的「最後一通」是用 `MAX(...) KEEP(DENSE_RANK FIRST ORDER BY OUTBND_SRNO DESC)` 算的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:189-190`),**取的是項次最大的那一筆,不是日期最新的那一筆**。項次是人工遞增的,通常一致,但如果有人插號就會不一樣。

#### 4.2.3 整批匯入(`TMKM001p1` ＋ `BatchAdd`)

這是全模組唯一會大量寫資料的地方,也是缺陷最密的一段。

前端流程(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:92-133`):

1. 選 CSV → `StreamReader` 預設編碼開檔,**第一行當標題丟掉**(`:106`)。

2. 逐行 `Split(',')`,**欄數少於 2 就 `break`**(`:111`)——後面所有列靜默消失,連提示都沒有。

3. 戶號轉 `decimal` 失敗 → 跳訊息、清空整份、`return`(`:115-122`)。

4. 員工編號不做任何檢核,直接塞(`:123`)。

**範本下載寫出的檔用 `Encoding.Default`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:87`),讀回來的 `StreamReader` 沒指定編碼(預設 UTF-8)。**兩邊不一致;因為範本只有一行 ASCII 表頭而且會被丟掉,目前不會出事,但只要有人在 CSV 裡放中文就會壞。

選專案代碼時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:135-165`):呼叫 `CheckExists` 問伺服器,有資料就跳「已有該OutBound項目,是否全數刪除?」。**按「否」只是把代碼欄清掉,不會取消整個對話框**;按「是」就進入下一步。

伺服端 `BatchAdd`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:513-674`),一個交易裡做四件事:

1. **先刪**:`TMK001A` `TMK002A` `TMK003A` `TMK0031A` 四張表這個專案的資料全部 DELETE(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-602`)。**四句都包在 `string.Format(...)` 裡但樣板沒有任何 `{0}`**,傳進去的第二個參數完全沒用到——只是沒害,不是對。

2. **可能新增代碼**:專案名稱欄不是空字串就往 `COD006A` INSERT 一列 `CODE_SORT = 'P5'`,狀態碼寫死 `'301'`、四眼六個 ID 全填登入者、六個日期全填 `SYSDATE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623`)。**等於繞過四眼直接生效**,見 §8.4。

3. **逐筆 INSERT**:對 CSV 的每一列,從 `BMS001A` 撈客戶資料 INSERT 進 `TMK001A`,`OUTBND_NO` 用迴圈計數補成 11 位(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:643-655`)。六個衍生欄位用子查詢算:

- `MAX_ALLOT_AMT`:三年內股票型基金最大申購金額,靠 `F_GET_FND_PROF_TYPE(FUND_ID,'0') = '1'` 判斷股票型(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-576`)。

- `AGENT_CODE`:`OFD220A` 最近一筆申購書的銷售機構,查無給 `' '`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:577`)。

- `CUST_STYLE`:`OFD123A` 最新一筆的 `EFFECT_CODE2`,沒有就 `EFFECT_CODE1`,再沒有給 `'00'`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:578`)。

- `EMAIL_DATE`:`OFD601` → `OFD607A` 的 `OPENDAY`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:570`、`:581-584`)。

- `STATUS` 寫死 `'301'`,四眼六個 ID / 日期一樣全填登入者與 `SYSDATE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:579`)。**匯入的名單一進來就是已覆核狀態。**

4. **回報**:`Model.Utility.Result.AddResultRow(true, i, "")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657`)。`i` 從 1 起跳當序號用,最後回報的筆數是「實際筆數 + 1」;**CSV 一筆都沒讀到時 `i` 仍是 1,照樣回報成功一筆**。

還有兩個要記住的:

- **子查詢的 alias `A` 蓋掉外層的 `A`**:外層 `FROM BMS001A A`,`MAX_ALLOT_AMT` 子查詢裡又 `FROM OFD081A A, OFD221A B`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:572`)。Oracle 以最內層為準,目前算得出來,但任何人想在子查詢裡引用外層的 `A` 都會拿到錯的表。

- **`CheckExists` 先塞一句假 SQL 佔位**:`GetSqlStringCommand("SELECT 1 = 1")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:679`),那不是合法的 Oracle 語句,只是因為後面立刻被覆蓋掉才沒事。

#### 4.2.4 項次彈窗 `TMKM001p0`

雙擊明細 grid 開啟(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:409-465`)。新增列時自動補三件事:主檔三段 Key、項次 = 現有最大值 + 1、本次服務人員 = 登入者、上次服務人員 = 前一個項次的本次服務人員(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:424-445`)。

彈窗載入時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:71-182`):

1. 帶出主檔五欄與 `OUTBND_TOTAL` 七個計數(唯讀)。

2. 用四段主鍵找對應的 `TMK003A`,找不到就**當場新增一列**,通話日期 = AP Server 系統日、完成碼 = `"Y"`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:133-159`)。

3. 用 `m_callin_mgr.GetDataFilter(m_detail_row)` 組出 `TMK002A` 四段主鍵的 DataTable 篩選字串,拿去篩 `TMK0031A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:170-173`)。

4. 權限:`USER_ID_T` 不是登入者就把十幾個欄位鎖唯讀、兩張 grid 停用、確定鈕關掉(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`)。

按確定時(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:404-539`):

1. 通聯原因大小類**至少勾一項**,否則擋(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:407-413`)。

2. 回寫 `TMK002A` 六欄。

3. **有效代碼變更時,把同一份名單的其他項次全部覆蓋成新值**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`),註解說明「同一檔 `OUTBND_CODE` 只能有一筆有效代碼」。這是一個沒有任何提示的跨列寫入。

4. 再聯絡否為 N 時把三個再聯絡欄位清空(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:451-463`)。

5. 回寫 `TMK003A` 的通話日期與完成碼;**`COMMENT1` 那一行被註解掉**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:477`),所以畫面上的備註只進 `TMK002A.REMARK`,不進 `TMK003A.COMMENT1`。

6. 重算 `TMK0031A`:舊的還勾著就留、沒勾就 `Delete()`;新勾的逐一 `AddTMK0031ARow`,`CALLIN_SEQ` 固定 1(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:480-535`)。

#### 4.2.5 跨表更新

| 表 | 動作 | 時機 | 錨點 |
|---|---|---|---|
| `TMK001A` | INSERT / DELETE(整批) | 整批匯入 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:649` |
| `TMK002A` `TMK003A` `TMK0031A` | DELETE(整批)／四眼 INSERT-UPDATE-DELETE | 整批匯入／畫面維護 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:597-601`、框架 |
| `COD006A`〔共用〕 | **INSERT 一列** | 整批匯入且專案名稱有填 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623` |
| `BMS001A` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只讀 | 整批匯入 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:571-585` |

### 4.3 `TMKM002` — AO 新開發客戶電話行銷維護

#### 4.3.1 用途(推測)

電訪專員自己開發的客戶,一位客戶一張單、走完整四眼。名單來源不是專案,而是從潛在客戶檔 `CRM003A` 或受益人檔 `BMS001A` 挑一筆進來,因此主檔上多了 `PR_NO` 與 `PR_NAME`。

#### 4.3.2 挑客戶這一段(`TMKM002` 多出來的 439 行)

三個入口都通到同一支 `SetPrNoData`:

| 入口 | 觸發 | 錨點 |
|---|---|---|
| 統一編號欄的「…」鈕 | 開 `TMKM002p1`,同時列潛在客戶與受益人兩張 grid | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:668-679` |
| 姓名欄的「…」鈕 | 同上,用姓名查 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:685-696` |
| 戶號 Searcher 選取後 | 先把受益人列轉成潛在客戶列,再填 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:702-719` |

`TMKM002p1` 兩張 grid 互斥:選了一邊就取消另一邊(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:111-145`)。**兩張 grid 的查詢條件寫法不一樣**:潛在客戶直接傳原值給 `Like`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:66`),受益人要自己在後面加 `%`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:83-84`、`:90-91`),註解說「DataSrc的Where值必須自己處理」。**同一個畫面兩種前置條件,查出來的範圍不一樣。**

`SetPrNoData`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:737-801`)一次填十四個欄位。裡面有一條永遠不成立的判斷:

```
if (string.IsNullOrWhiteSpace(mainRow.PR_NO) && mainRow.PR_NO == "-1")
```

`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759`。**`&&` 應該是 `||`**:一個空白字串不可能同時等於 `"-1"`,所以這條分支是死的,`PR_NO = "-1"` 的哨兵值會被原樣填進畫面。這是 `AND` / `OR` 用錯的同型缺陷(CAS `CASB001_PO.cs:431` 那一類)。

`GetCRM003A_Row`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:807-863`)手寫逐欄搬 30 幾欄,裡面有三組重複的 `HM_TEL_AREA` / `HM_TEL` 指派(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:842-853`),後兩組是純粹的複製貼上殘留。地址別代碼被硬壓成兩種值:`addr_code == "1" ? "1" : "0"`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:822`),註解寫「強制此處代碼只會有 0.長條式 or 1.分段式」。風險屬性那一行被註解掉,理由是「二邊欄位代碼不同,不採用」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:858-859`)。

#### 4.3.3 新增時的取號與前次指派人

`GetPageValue` 在新增模式下(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:390-413`):

1. `OUTBND_CODE = "A0"`、`OUTBND_NO = ""`(序號留給伺服端配)、`ID_NO` 取畫面值。

2. 明細第一列的本次服務人員 = 登入者。

3. 呼叫 `GetLAST_USERID` 問伺服器「這個統編上次是誰服務的」,填進 `USER_ID_L`。

`GetLAST_USERID` 的 SQL 是 `SELECT MAX(USER_ID_L) FROM TMK002A WHERE OUTBND_CODE = 'A0' AND ID_NO = :ID_NO GROUP BY OUTBND_CODE`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:433-438`)。**它取的是 `USER_ID_L`(上次服務人員)的最大值,不是 `USER_ID_T`(本次服務人員)。**方法名與註解都說「取得最後指派人員」,但實際拿到的是「歷史上所有紀錄裡,上次服務人員欄位的字典序最大值」——既不是最後一次,也不是本次。這是欄位比錯欄的同型缺陷(CLS `CLSR002_PO.cs:864` 那一類),嚴重度中:它只影響一個顯示欄位,不影響權限。

伺服端 `BeforeAdd` 用 `do { … } while (IsExistByData(...))` 迴圈取號直到不重複(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:149-152`),取到之後把三段 Key 回填給三張明細裡 `OUTBND_NO` 還空著的列(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:165-195`)。

#### 4.3.4 四眼跳號一覽表:七個事件、一個號別,而且號別是錯的

`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:374-415` 七個事件的寫法完全一樣,只差 `EVAType`:

```
if (!SrNoCommentProcessor.AddCommentHistory(EVAType.Xxx, SrNo.AllotNoForNfd, …)) throw new ApplicationException("");
```

**`SrNo.AllotNoForNfd` 的值是 `"OFD220A"`,也就是「境內申購書號」**(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103`)。但這支畫面取的號是 `SrNo.OUTBND_NO`,值是 `"TMK001A"`(`Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`、`Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604`)。**七處全部把 TMK 的跳號紀錄寫到申購書號那一本帳上。**這與 `bbs.md` 附錄 E1 記的 `BBSM013_PO.cs:1260` 是同一型缺陷,差別是 BBS 只錯一處、TMK 是七處一致地錯(所以八成是複製 `CASM001_PO` 的樣板來的——`Dev/ATLAS.CAS/Source/PO/PO.CAS/CASM001_PO.cs:582` 就是同一行)。

另外 `throw new ApplicationException("")` 丟的是**空訊息例外**,七處都一樣。使用者看到的會是框架的預設字串,沒有任何線索指向跳號一覽表。

#### 4.3.5 兩套通話彈窗

| 彈窗 | 入口 | 怎麼找 `TMK003A` | 怎麼篩 `TMK0031A` | 寫 `COMMENT1` |
|---|---|---|---|---|
| `TMKM002p0` | 「通話記錄」鈕(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:579-602`) | `FirstOrDefault()`,**不帶任何條件**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:74-75`) | `Select()`,**不帶任何篩選**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:269`) | 會寫(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:260`) |
| `TMKM002p2` | 雙擊明細 grid(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:948-1023`) | 四段主鍵比對(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:120-125`) | `GetDataFilter` 組主鍵條件(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:453-454`) | **被註解掉**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:444`) |

**只要這張單有兩個以上的項次,走 `TMKM002p0` 就會改到第一個項次的通話記錄、並把不在本次勾選裡的所有項次的通聯原因全部刪掉。**`TMKM002p0` 的註解自己寫著「此功能對會對應一份通訊記錄,所以不做篩選(全部取出)」(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:113`、`:268`)——這個前提在 `TMKM002p2` 允許多項次之後就不成立了,但 `p0` 沒有跟著下架。詳見附錄 E3。

#### 4.3.6 跨表更新

`TMKM002` **不寫任何外部表**。它的寫入面就是四張自有表,全部經由四眼引擎;`TMK901` 不碰、`COD006A` 不碰、`CRM003A` 不碰。

### 4.4 兩支 M 畫面的卡控總表

結果類型五類:阻擋 / 警示 / 詢問 / 過濾(無提示)/ 記錄不擋。

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 查詢前 | 五個條件必須擇一填寫 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:499-507` |
| 查詢前 | 下次可連絡日期(起)(迄)必須同時有值或同時無值 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:509-511`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:622-624` |
| 查詢前 | 下次可連絡日期(起)不可大於(迄) | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:513-515`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:626-628` |
| 查詢 | 專案代碼硬條件(`<> 'A0'` / `= 'A0'`) | 兩支各自 | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` |
| 查詢 | 三路 / 兩路權限條件 | 兩支 | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:237-244`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228` |
| 查詢 | 登入者已離職 → 第二路權限失效 | 只有 `TMKM001` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| 查詢 | 主檔必須有 `OUTBND_SRNO = 1` 的明細 | 只有 `TMKM002` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:219-222` |
| 查詢 | 是否含已結案清單 | 只有 `TMKM001` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:269-280` |
| 新增主檔 | 一律不支援 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:160` |
| 新增明細 | 新增模式下雙擊 grid | 只有 `TMKM001` | 警示 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:411-416` |
| 存檔前 | 新增的項次沒有勾通話記錄 | 只有 `TMKM001` | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:564-571` |
| 刪明細前 | 選取列含不是自己的項次 | 只有 `TMKM001` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:475-481` |
| 刪明細前 | 一律不准刪 | 只有 `TMKM002` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:1027` |
| 修改 | 服務人員不是登入者 → 鎖修改與刪除鈕 | 只有 `TMKM002` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:359-364` |
| 彈窗開啟 | 服務人員不是登入者 → 全鎖、關掉確定鈕 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:310-347`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:281-318` |
| 彈窗確定 | 通聯原因大小類至少勾一項 | 兩支(三個彈窗) | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:407-413`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:372-378`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:241-247` |
| 加通聯原因 | 代碼未選 / 不存在或無效 / 已勾選 | 兩支(三個彈窗) | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:227-249`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:207-229`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:202-224` |
| 離開再聯絡時間欄 | 值等於 0 | 兩支 | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:546`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:512` |
| 離開再聯絡時間欄 | **值大於 24** | 兩支都**不擋**,但訊息說「必須介於1~24時之間」 | 記錄不擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:548`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:514` |
| 存有效代碼 | 值變更時覆蓋同名單全部項次 | 兩支 | **記錄不擋(無提示的跨列寫入)** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 匯入前 | 至少要有一筆資料 | 只有 `TMKM001p1` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:56-61` |
| 匯入前 | OutBound 項目與項目名稱必填 | 只有 `TMKM001p1` | 阻擋 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:62-73` |
| 匯入前 | 該專案已有資料 → 是否全數刪除 | 只有 `TMKM001p1` | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:147-149` |
| 讀 CSV | 戶號欄不是數字 | 只有 `TMKM001p1` | 阻擋(清空整份) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:115-122` |
| 讀 CSV | **欄數少於 2** | 只有 `TMKM001p1` | **過濾(無提示,而且吃掉後面全部)** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:111` |
| 匯入執行 | `COD006A` INSERT 失敗 | 只有 `TMKM001p1` | 阻擋(回滾) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:625-630` |
| 匯入執行 | 任一列 INSERT 影響 0 列 | 只有 `TMKM001p1` | 阻擋(回滾) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:649-654` |
| 匯入執行 | **CSV 一筆都沒有時** | 只有 `TMKM001p1` | **記錄不擋(回報成功一筆)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:642`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657` |

### 4.5 `TMKM901` — CallOut 專員名單移轉

#### 4.5.1 用途(推測)

專員離職或調動時,把他名下的名單整批改派給另一位。`TMK901` 不是業務表,是一張**移轉工單**:一個 `DATAID` 掛 N 列要移轉的 `TMK002A`,整批走一次四眼。9xx 是保留段的畫面代號,見 `architecture.md §9`。

#### 4.5.2 帶資料進來

在「OutBound 項目」或「原專員」兩個 Searcher 選完值時觸發 `GetTMK002A`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:153-161`):

1. 兩個條件都空 → 什麼都不做(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:111-112`)。

2. grid 已經有資料 → **詢問**「是否清除現有明細,並重新帶入資料」,選否就 `e.Cancel = true`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:113-118`)。

3. 呼叫伺服端 `GetTMK002A`,SQL 是 `TMK002A` × `TMK001A` × `AA_USER` 三表內連(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:58-72`)。

4. 把舊列全部 `Delete()`、新列全部 `SetAdded()` 再 `Merge`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:127-131`)。

三件要注意的:

- **`AA_USER` 是 INNER JOIN**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:72`)。原專員的帳號如果已經從 `AA_USER` 刪掉,他名下的名單**一筆都帶不出來**,而且畫面不會說為什麼。這對「離職後要移轉」這個主要使用情境剛好是反的。

- **`BF_NO = -1` 被當成 NULL**:`case TMK001A.BF_NO when -1 then null else TMK001A.BF_NO end`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:63`、`:123`)。`-1` 是潛在客戶沒有戶號時的哨兵值,與 `TMKM002` 那邊的 `"-1"`(§4.3.2)是同一回事。

- **查無資料的 `catch` 把所有例外都翻譯成「查無資料」**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:79-83`)。連線失敗、SQL 語法錯、權限不足,畫面上都只會看到這四個字。

#### 4.5.3 覆核時真正發生的事

`BeforeApprove`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:154-239`)做兩步:

**第一步**:逐列 UPDATE `TMK002A` 的 `USER_ID_T`,用四段主鍵定位(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:160-186`)。

**第二步**:一句 `MERGE INTO TMK001A`,把名單主檔的 `EMP_NO` 從原專員的員工代碼改成新專員的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:188-237`)。註解註明是 2020/06/18 才加的。MERGE 的來源子查詢做三件事:

1. `MYEMP_NO`:從 `COD009` 取每個登入帳號最新的員工代碼,用 `MAX(EMP_NO) KEEP(DENSE_RANK FIRST ORDER BY ENTRY_DATE DESC, LEAVE_DATE DESC)`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:193-200`)。

2. `MYTMK901`:讀本次 `DATAID` 的工單,把原 / 新專員帳號各自對到員工代碼。

3. 用 `OUTBND_CODE` ＋ **`EMP_NO = 原專員員工代碼**` 去 `TMK001A` 找要改的列(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:224-226`)。

**這裡有一個範圍放大的風險**:第一步改的是工單上勾選的那幾筆 `TMK002A`;第二步的 `MERGE` 卻是用「同一個專案 ＋ 同一個原專員」去比對 `TMK001A`,**沒有帶 `OUTBND_NO` 與 `ID_NO` 去限制範圍**。也就是說,只勾了三筆,`TMK001A` 上那位專員在該專案的**全部**名單的 `EMP_NO` 都會被改掉。這是設計意圖還是漏寫,程式碼無法分辨——**需要業務確認**。

三個確認的缺陷:

| # | 現象 | 錨點 |
|---|---|---|
| 1 | `args.Cancel` 在迴圈裡**每一圈都被覆寫**。第 3 列失敗設成 true,第 4 列成功又設回 false,整批照樣覆核成功,而且錯誤訊息也被蓋掉 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185` |
| 2 | `DATAID` 取自迴圈的**最後一圈**。列數為 0 時 `DATAID` 是空字串,MERGE 照樣執行(比對不到就什麼都不做,但交易是成功的) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:180`、`:235` |
| 3 | MERGE 的 `ON` 後面是**全形空白 U+3000**,不是 ASCII 空白 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:230` |

第 3 條要講清楚:全形空白是否被 Oracle 的語彙分析器當成空白,取決於用戶端字元集與版本,repo 內無法驗證。**如果不被接受,整句 MERGE 會丟 `ORA-00920` 之類的錯,而第一步的 `TMK002A` 更新已經做完**——覆核會失敗回滾,但這支畫面的主要功能等於壞的。**這一條務必實測**。

#### 4.5.4 前端的三個問題

| # | 現象 | 錨點 |
|---|---|---|
| 1 | `BeforeAddButtonClicked` 檢核失敗只設 `e.Cancel = true`,**沒有 `return`**,後面照樣把未勾選的列 `Delete()`。使用者按取消或檢核不過,畫面上的資料已經被改掉了 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99` |
| 2 | 「已覆核資料不可修改」判斷寫成 `APPROVEID != string.Empty`。ATLAS 的預設值常是一個空白字元 `' '`(整批匯入那段就寫 `' '`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:623`),那樣的話**還沒覆核的工單也會被當成已覆核而鎖住** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84` |
| 3 | `if (view.Util.Result.Count == 0 \|\| view.Util.Result[0].ReturnCode)` 把「伺服器一個結果列都沒回」當成成功 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:125` |

#### 4.5.5 `TMKM901` 卡控總表

| 時點 | 檢核 | 結果類型 | 錨點 |
|---|---|---|---|
| 帶資料前 | 兩個查詢條件都空 | 過濾(無提示,直接什麼都不做) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:111-112` |
| 帶資料前 | grid 已有資料 | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:113-118` |
| 帶資料 | 原專員不在 `AA_USER` | **過濾(無提示)** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:72` |
| 全選 / 全不選 | 目前有套篩選 | **詢問** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:165-169`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:176-180` |
| 新增 / 修改前 | 至少勾選一筆 | 阻擋(但**沒有 return**,資料照改) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:211-215`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99` |
| 載入維護頁 | `APPROVEID` 不是空字串 | 阻擋(判斷式可能誤判,見 §4.5.4) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84-88` |
| 覆核時 | 某列在 `TMK002A` 找不到 | **記錄不擋**(訊息會被下一圈蓋掉) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185` |

## 5. 查詢畫面(I)

**本模組無此類畫面。**

原因:TMK 的查詢需求全部被兩個地方吸收了。

1. **M 畫面本身就是查詢頁 ＋ 維護頁兩頁式**(`this.TabPages = 2`,`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:43`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:45`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:38`)。查詢頁的結果 grid 欄位在 `App.config` 裡宣告(§0.5),要「只看不改」直接用查詢頁就好,不需要另開 I 型畫面。

2. **要跨名單、跨期間看的東西一律走 R**。11 支報表把統計與明細都涵蓋了,而且 R 型畫面多了「轉 Excel」這條路,比 I 型的 grid 更符合電訪主管的使用方式。

另外,TMK 的資料也會出現在別的模組的 I 畫面裡:`OFDI011` 讀 `CRM006A` / `CRM0061A` / `CRM003A`(見 `crm.md §8.3`),而 `TMKM001` 工具列第一顆自訂鈕直接開 `OFDI011D`(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:581-584`)——**電訪專員要看客戶全貌時是跳到 OFD 的查詢畫面,不是留在 TMK。**這也是 TMK 不需要自己的 I 畫面的原因之一。

## 6. 批次(B)與 WindowsService

**本模組無此類畫面,也沒有 WindowsService。**

原因有三:

1. **名單的產生是人工觸發的,不是排程。**整批匯入做在 `TMKM001` 的自訂鈕上(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:72-78`),使用者自己選檔、自己按確定;沒有任何地方監看目錄或排程。

2. **統計是報表算的,不是批次先算好的。**11 支報表每次都現跑 SP,PO 一律 `cmd.CommandTimeout = 0` 並註解「此程式讓它永久跑」(例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:58`)。所以沒有中介的統計表要靠批次維護。

3. **唯一像批次的 `TMKM901`,被做成 M 型畫面**:它有勾選 grid、有四眼、有工單表 `TMK901`,整批動作發生在覆核那一刻(§4.5.3),而不是在某個排程時點。

要留意的是:`BatchAdd` 雖然掛在 M 畫面上,**行為上它就是一支批次**——一個交易、先刪四張表、再逐筆插入、失敗整批回滾(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:513-674`)。它沒有 B 型畫面該有的東西:沒有執行紀錄、沒有筆數對帳(回報的筆數還多 1,§4.2.3)、沒有重跑保護(重跑就是再刪一次再插一次)。**把它當批次看待,不要當成一般的畫面存檔。**

## 7. 報表(R)

```text
[圖] TMK 十一支報表畫面的四段鏈、兩種選 rpt 的寫法、二十四份 rpt 的分佈、兩個已確認缺陷，以及四種查詢權限做法
圖中文字:① 11 支 R 畫面固定四段鏈，全部不碰維護層的 PO / R 畫面收條件 算登入者員編 / 三條路 預覽 列印 轉 Excel / 報表 FormProxy 過一次遠端 / 報表 PO 只呼叫 SP / 13 支報表 SP / 游標回一到四張結果集 / ② 報表選項怎麼決定要載哪一份 rpt：兩種寫法並存 / 先算出檔名與標題再設定 / R001 R002 R003 R004 R005 R006 R901 / 在判斷式裡直接設定 / R007 R008 R009 R010 / 單一選項對單一 rpt / R001 R002 R003 各三份 / 兩個選項相乘 / R006 兩軸配出五份 / 沒有選項 固定一份 / R008 R009 各一份 / ③ 24 份 rpt 的分佈：畫面數不等於報表數 / R001 R002 R003 各三份 / 共九份 / R006 五份 / 三種計數乘兩種呈現 / R004 R005 R007 R010 各兩份 / 共八份 / R008 R009 各一份 / 共兩份 / ④ 兩個會咬人的地方 / TMKR901 指名一支不存在的 rpt / repo 內找不到這個檔 / 產 Excel 失敗時沒有任何訊息 / 使用者以為成功其實沒存檔 / ⑤ 登入者查詢權限：三種做法，三支完全沒有 / 傳查詢者員編給 SP / R004 R005 R006 / 傳登入者員編給 SP / R007 R008 R009 R010 / 前端鎖專員欄位 / R003 主管才解鎖 / R001 R002 R901 沒有 / R901 算了卻沒傳
```

*圖:圖 4 報表群。黑框=沒有原始碼的 SP 或已確認的缺陷；橘框=值得特別記住的一支。TMKR006 是唯一用兩個選項相乘決定報表檔的；TMKR901 的預覽與列印路徑指到一個不存在的 rpt，只有轉 Excel 那條路能跑。*

**這一章是本模組的重心。**14 支畫面裡 11 支是 R,配 24 份 `.rpt`、13 支版控外的 SP。31 個組合不可能每支深挖,所以先用 §7.1–§7.3 把共同模式講完,再挑三支有特色的展開(§7.4–§7.6),最後兩節講兩條橫向規則(§7.7 Excel、§7.8 查詢權限)。

### 7.1 一覽

| rpt | 對應畫面 | 取數來源 | 參數 |
|---|---|---|---|
| `TMKR001RPS1` `TMKR001RPS2` `TMKR001RPS3` | `TMKR001` | `S_TA_TMKR001_GET`(三個 refcursor 一次回) | `iCAL_DATE` `iCREATEID` `iREPORT_TYPE` |
| `TMKR002RPS1` `TMKR002RPS2` `TMKR002RPS3` | `TMKR002` | `S_TA_TMKR002_GET`(三個 refcursor) | `iCAL_YEAR` `iCREATEID` `iREPORT_TYPE` |
| `TMKR003RPS1` | `TMKR003`(選項 `'0'`) | `S_TA_TMKR003_GET_1`(兩個 refcursor) | `iOUTBND_USER` `iCALLIN_DATE_ST` `iCALLIN_DATE_END` `iOUTBND_CODE` `iCALLIN_CODE` |
| `TMKR003RPS2` | `TMKR003`(選項 `'1'`) | `S_TA_TMKR003_GET_2` | 同上 |
| `TMKR003RPS3` | `TMKR003`(選項 `'2'`) | `S_TA_TMKR003_GET_3` | 同上 |
| `TMKR004RPS1` | `TMKR004`(選項 `'0'`) | `S_TA_TMKR004_GET_1` | `iALLOT_DATE_ST` `iALLOT_DATE_END` `iSAL_EMP_NO` `iFUND_ID` `iHAS_RSP` `iQUERY_EMP_NO` |
| `TMKR004RPS2` | `TMKR004`(選項 `'1'`) | `S_TA_TMKR004_GET_2` | 同上 |
| `TMKR005RPS1` `TMKR005RPS2` | `TMKR005`(選項 `'0'` / `'1'`) | `S_TA_TMKR005_GET_1`(**兩種選項共用一支 SP**) | `iALLOT_DATE_ST` `iALLOT_DATE_END` `iOUTBND_CODE` `iREPORT_TYPE` `iQUERY_EMP_NO` |
| `TMKR006RPS1` `TMKR006RPS2` `TMKR006RPS3` `TMKR006RPS4` | `TMKR006`(類型1 `'1'`/`'2'` × 類型2 `'1'`/`'2'`) | `S_TA_TMKR006_GET_1`(四個 refcursor) | `iRSP_DATE_ST` `iRSP_DATE_END` `iEMP_NO` `iMQ_NUMBER` `iRSP_TYPE` `iREPORT_TYPE1` `iREPORT_TYPE2` `iQUERY_EMP_NO` |
| `TMKR006RPS5` | `TMKR006`(類型1 `'3'`) | `S_TA_TMKR006_GET_2` | `iRSP_DATE_ST` `iRSP_DATE_END` `iRSP_TYPE` `iQUERY_EMP_NO` |
| `TMKR007RPS1` `TMKR007RPS2` | `TMKR007`(選項 `'1'` / `'0'`) | `S_TA_TMKR007_GET_1` | `iUSER_EMP_NO` `iCTL_DATE_ST` `iCTL_DATE_END` `iSAL_EMP_NO` `iFUND_ID` |
| `TMKR008RPS1` | `TMKR008` | `S_TA_TMKR008_GET_1` | `iUSER_EMP_NO` `iALLOT_DATE_ST` `iALLOT_DATE_END` `iEMP_NO` `iFUND_ID` |
| `TMKR009RPS1` | `TMKR009` | `S_TA_TMKR009_GET_1`(兩個 refcursor) | `iUSER_EMP_NO` `iPRINT_YYMM` `iEMP_NO_ST` `iEMP_NO_END` `iFUND_ID` `iRATE_DATE` |
| `TMKR010RPS1` `TMKR010RPS2` | `TMKR010`(選項 `'1'` / `'2'`) | `S_TA_TMKR010_GET_1`(三個 refcursor) | 14 個,含三個可為 `NULL` 的數值參數 |
| (指名 `TMKR901RPS0`,**檔不存在**) | `TMKR901` | `S_TA_TMKR901_GET`(五個 refcursor) | `iCAL_DATE_S` `iCAL_DATE_E` `iAGENT_CODE` `iEMP_NO` `iPROJECT` `iOUTBND_CODE` `iCAMPAIGN_CODE` `iFUND_ID` `iRSP_TYPE` `iSUCCESS_SUB` `iRENEW` |

錨點:每支 PO 的 `GetStoredProcCommand` 那一行,例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:56`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:68`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR010_PO.cs:56`、`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR901_PO.cs:58`。**13 支 SP 一支都不在 `DB/` 資料夾內**,口徑無法從 repo 確認(附錄 B)。

### 7.2 十一支的共同骨架

每支 R 都長得一樣,只有參數不同。骨架五段:

| 段 | 做什麼 | 範例錨點 |
|---|---|---|
| 1 `FormInitial` | 綁 ViewVDB 與 FormProxy;多數會算登入者員工代碼 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:37-42`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:46-68` |
| 2 `RefreshPage` | 設預設值(報表選項、部門固定 `'08201'`、基金全選) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:85-105` |
| 3 `BeforePreviewOrPrintButtonClicked` | 檢核 → 組查詢參數 → `SetQueryParameters(rpt, rpt, 標題)` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:90-106` |
| 4 PO `GetData` | `BeginTransaction` → 呼叫 SP → `LoadDataSet` → 依筆數寫 `Result` → `Commit` | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:47-98` |
| 5 `ReportLoad` | `SetRptSchemaOnDoc()` 再逐一 `SetParameterValue` 把查詢條件印在報表頁首 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:112-154` |

Ctl 層十一支逐字相同,都是 151 行,`GetReportData` ＋ `GetReportObject` 兩支加樣板(`Dev/ATLAS.TMK.Report/Source/Control/ReportControl.TMK/TMKR001_Ctl.cs:49-64`)。`GetReportObject` 直接把**用戶端傳來的報表類別名稱**交給 `CRReportTransfer.TransferFileByte`(無原始碼,從呼叫端反推),與 `architecture.md §6` 描述的一致:伺服器照單全收。

PO 層有四個共同寫法要記住:

1. **`cmd.CommandTimeout = 0`,註解「此程式讓它永久跑」**,十一支全部有(例 `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:64`)。查詢條件開太大就是整條連線卡住,沒有逾時保護。

2. **報表只讀卻開交易**:每支都 `BeginTransaction` / `Commit`(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:54`、`:83`)。

3. **`catch` 裡先 `tran.Rollback()`**(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:87`)。如果 `BeginTransaction()` 自己就丟例外,`tran` 是 null,`catch` 裡會再丟一個 `NullReferenceException`,原始錯誤直接消失。十一支全中。

4. **「查無資料」與「執行失敗」在 `Result` 上長得一樣**:兩者都是 `AddResultRow(false, 0, "")`,訊息都是空字串(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:80`、`:88`)。畫面端只好一律顯示「無符合查詢條件的資料。」(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352`)——**SP 掛掉時使用者看到的也是這一句**。

### 7.3 選 rpt 的兩種寫法,加一組對不齊的值域

兩種寫法:

| 寫法 | 畫面 | 錨點 |
|---|---|---|
| 先 `GetReportFileTitle()` 回一個 `KeyValuePair`,再統一 `SetQueryParameters` | `TMKR001` `TMKR002` `TMKR003` `TMKR004` `TMKR005` `TMKR006` `TMKR901` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:186-203` |
| 在判斷式裡直接 `SetQueryParameters` | `TMKR007` `TMKR008` `TMKR009` `TMKR010` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:143-150` |

**報表選項的值域每支都不一樣,而且沒有規律:**

| 畫面 | 選項值 | 對應 | 錨點 |
|---|---|---|---|
| `TMKR001` `TMKR002` | `'1'` `'2'` `'3'` | RPS1 / RPS2 / RPS3 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:190-201` |
| `TMKR003` | `'0'` `'1'` `'2'` | RPS1 / RPS2 / RPS3 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:232-243` |
| `TMKR004` `TMKR005` | `'0'` `'1'` | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:242-249`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:183-190` |
| `TMKR007` | `'1'` `'0'`(**反過來**:`'1'` 是明細、`'0'` 是彙總) | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:143-150` |
| `TMKR010` | `'1'` `'2'` | RPS1 / RPS2 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:191-198` |
| `TMKR006` | 類型1 `'1'` `'2'` `'3'` × 類型2 `'1'` `'2'` | 見 §7.4 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:205-237` |

**同一個模組裡「彙總 / 明細」在三支報表上用了三組不同的碼(`'0'/'1'`、`'1'/'0'`、`'1'/'2'`)。**改 SP 或改選項時很容易對錯,而且值都是直接傳給版控外的 SP,錯了也不會有編譯錯誤。

另外三支報表的 PO 有「選項沒對上就什麼都不做」的分支:

- `TMKR003_PO` 只認 `'0'` `'1'` `'2'`,其他值三個分支都不進,`Result` 一列都沒有(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:59-146`)。

- `TMKR006_PO` 只認 `'1'` `'2'` `'3'`(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:61`、`:106`)。

- 這時畫面端的 `view.Util.Result[0]` 會**丟 `IndexOutOfRangeException`**(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348`)。目前因為選項組的預設值都落在有效值域內而沒發作。

### 7.4 `TMKR006` — 唯一用兩個選項相乘決定報表檔的

兩個選項組:

| 類型1(`uoptREPORT_TYPE`) | 類型2(`uoptREPORT_TYPE2`) | 載入的 rpt | 標題 |
|---|---|---|---|
| `'1'` 筆數 | `'1'` 彙總表 | `TMKR006RPS1` | 電話行銷專員定額彙總表 |
| `'1'` 筆數 | `'2'` 明細-BY戶數 | `TMKR006RPS2` | 電話行銷專員定額客戶明細表 |
| `'2'` 戶數 | `'1'` 彙總表 | `TMKR006RPS3` | 電話行銷專員定額年度配額達成表--By 戶數(含168) |
| `'2'` 戶數 | `'2'` 明細-BY戶數 | `TMKR006RPS4` | 電話行銷專員定額客戶明細表--By 戶數(含168) |
| `'3'` 連續扣款三次筆數 | (忽略) | `TMKR006RPS5` | 電話行銷專員定額扣款成功統計表--By 戶數(含168) |

錨點:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:205-237`、選項值域在 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.Designer.cs:216-221` 與 `:364-367`。

PO 側對應兩支 SP:類型1 是 `'1'` 或 `'2'` 走 `S_TA_TMKR006_GET_1`(一次回四張表),`'3'` 走 `S_TA_TMKR006_GET_2`(回一張)。**兩個選項都原樣傳給 SP,所以四種組合共用同一支 SP、同一組四張結果集,由 SP 自己決定填哪幾張**——註解把對應關係寫在 PO 裡:「筆數 彙總 = TMKR006T3、筆數 明細 = TMKR006T4、戶數 彙總/明細 = TMKR006T1、TMKR006T2」(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR006_PO.cs:64-67`)。**這段註解是唯一能知道哪份 rpt 吃哪張結果集的線索,SP 不在版控裡。**

另外兩件事:

- 「每月配額數」預設 2,只有筆數/彙總會用,但**`ReportLoad` 裡把它印在報表頁首那一行被註解掉**(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:157-159`),參數照樣傳給 SP(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:185`)。所以報表上印不出這次用的配額數是多少。

- 業務員條件只有在 `custEMP_NO.Enabled` 時才傳(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:178-182`),而 `Enabled` 由選項變更事件控制(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:396-405`)。**切換選項時畫面上還看得到填過的業務員,但參數不會傳出去**——這是一條過濾(無提示)。

### 7.5 `TMKR003` — 唯一在前端做主管判斷的

`FormInitial` 直接問「你是不是 G11 的主管」:

```
var masters = new List<string>(utility.GetMasterEmpNo("G11"));
if (masters.Contains(empNo)) { 解鎖專員欄位 } else { 鎖成登入者自己 }
```

`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:48-72`。三點要注意:

1. **`"G11"` 是寫死的部門代碼**〔客戶特定〕,與 `TMKR901` 用的 `"G2"`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81`)、`TMKR004`–`TMKR010` 用的 `"08201"`(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:88`)是三組不同的值,三處都沒有註解說明關係。

2. **員工代碼是用位置取的**:`empInfo.Split(',')[1]`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:54`)。`ClientBizUtility.GetEMP_INFO` 沒有原始碼(從呼叫端反推),回傳一個逗號分隔字串,第 2 段被當成員工代碼。**只要那支共用函式多加一欄或換順序,八支報表同時錯。**同型缺陷見 `crm.md` 附錄 E.6。

3. **鎖定是前端做的,後端沒有第二道。**`TMKR003` 的 PO 沒有 `QUERY_EMP_NO` / `USER_EMP_NO` 參數(`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR003_PO.cs:66-70`),SP 收不到登入者是誰。繞過前端就能查全部。

### 7.6 `TMKR901` — 9xx 保留段的報表,而且列印路徑指到一個不存在的檔

`TMKR901` 是唯一在 `9xx` 保留段的報表(`architecture.md §9`),也是全模組最特別的一支:

| 特徵 | 內容 | 錨點 |
|---|---|---|
| 指名的 rpt | `TMKR901RPS0`,標題是空字串 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:194` |
| 這個檔存在嗎 | **不存在。**`Dev/ATLAS.TMK.Report/Source/CrystalReports/Report.TMK/` 底下 24 份 `.rpt` 沒有任何 901 開頭的 | 母體第 4 節 |
| 註解怎麼說 | 「直接指定同一檔案同時產出多個 Sheets,Sheets Name 各自由 GenExcelR 指定」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:193` |
| `ReportLoad` 做什麼 | `SetRptSchemaOnDoc()` 之後就是一行註解 `// nothing` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:131-138` |
| 結果集 | 五張 `TMKR901T0`–`TMKR901T4`,對應 Excel 的五個工作表 | `Dev/ATLAS.TMK.Report/Source/Entity/ReportDataEntity.TMK/TMKR901Model.xsd:15-103` |

**結論:這支報表只有「轉 Excel」那條路能跑。**按預覽或列印時,`CRReportTransfer.TransferFileByte("TMKR901RPS0")` 會找不到檔;它沒有原始碼,回傳 null 還是丟例外無法從 repo 判定,但**無論哪一種,使用者都拿不到報表**。這與 `bbs.md` 附錄 E11 記的「列印路徑壞掉」是同一類,差別是 BBS 錯在參數名、TMK 錯在檔名。

`TMKR901` 另外三個寫死值〔客戶特定〕:

| 值 | 意思 | 錨點 |
|---|---|---|
| `AGENT_CODE IN ('08001', '08201')` | 只看兩個銷售機構 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:79` |
| `DEPT_NO = 'G2'` ＋ 離職日 >= 去年 1/1 | 業務員下拉限 G2 現職或前年度在職 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81-82` |
| `OUTBND_DATE1 = "20200101"` | 專案下拉只取 2020/01/01 之後的 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:87` |

還有一個死變數:`xUserEmpNo` 在 `FormInitial` 算出來了(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`),但 `GetQueryVDB` 從頭到尾沒有把它加進參數(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:143-185`)。**這支報表沒有任何登入者查詢權限過濾**,見 §7.8。

### 7.7 轉 Excel 這條路

十一支都有第三顆鈕「轉 Excel」,共用 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs`(285 行,本模組自有)。流程:

1. `DoValidate(isExcel: true)` 多檢查兩件事:轉出路徑必填、路徑必須存在(例 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:236-246`)。

2. 呼叫同一支 `GetReportData` 取數(**與預覽走同一條後端路徑**)。

3. 依報表選項挑一支 `GenExcelR1`–`GenExcelR5` 委派,檔名固定是 `<路徑>\<rpt名>.xlsx`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:356`)。

4. `ExcelHelper.GenExcelFile` 開 Excel COM、逐格寫、`SaveAs`、`Quit`、`FinalReleaseComObject`。

四個要注意的:

| # | 內容 | 錨點 |
|---|---|---|
| 1 | **回傳 false 時畫面什麼都不顯示。**只有 `== true` 才跳「執行成功」,`false` 沒有 else | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385` |
| 2 | `GenExcelFile` 用**錯誤訊息字串**判斷要不要吞例外:`e.Message.Contains("0x800A03EC")` 就當成使用者按了取消,回 false;否則 `throw e`(重設堆疊) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs:67-75` |
| 3 | 畫面端的 `catch` 把例外訊息寫到 `Console.WriteLine`(WinForms 看不到),使用者只看到「商業邏輯異常!」 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:387-392` |
| 4 | **Excel 版面是手寫在 UI 層的**,跟 `.rpt` 各寫一次。`TMKR006` 有五支 `GenExcelR1`–`GenExcelR5`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:539-639`)。改報表欄位要同時改 `.rpt` 與這裡 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:417-464` |

`GetOutPath()` 在路徑為空時回傳桌面(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:261-266`),但 `DoValidate` 已經先擋掉空路徑,所以這個 fallback 只在選資料夾對話框的初始位置用得到。

### 7.8 登入者查詢權限:四種做法並存

| 做法 | 畫面 | 錨點 |
|---|---|---|
| 算出員工代碼,以 `QUERY_EMP_NO` 傳給 SP | `TMKR004` `TMKR005` `TMKR006` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:231`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:171`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:195` |
| 算出員工代碼,以 `USER_EMP_NO` 傳給 SP | `TMKR007` `TMKR008` `TMKR009` `TMKR010` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR007.cs:119`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:100`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:100`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:119` |
| 前端鎖專員欄位,後端不知道登入者是誰 | `TMKR003` | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57-71` |
| **完全沒有** | `TMKR001` `TMKR002` `TMKR901` | `TMKR001` / `TMKR002` 連 `GetEMP_INFO` 都沒呼叫;`TMKR901` 算了卻沒傳(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`) |

**同一個參數概念用了兩個名字(`QUERY_EMP_NO` / `USER_EMP_NO`),而且兩組 SP 各自定義。**這與 `crm.md §7.6` 記的「七支有、一支沒有」是同一類問題,TMK 這邊更散:四種做法、三支沒有。

`TMKR001` 與 `TMKR002` 沒有權限過濾是可以理解的——它們統計的是「建立者」維度的通話量(參數 `iCREATEID`),本來就是主管看的。**但那是推測,程式裡沒有任何註解說明,而且畫面上也沒有擋誰能開。假設**:功能權限由框架平台庫擋(`architecture.md §3`)。

### 7.9 報表側的卡控總表

| 時點 | 檢核 | 畫面 | 結果類型 | 錨點 |
|---|---|---|---|---|
| 預覽 / 列印前 | 日期(起)不可大於(迄) | 幾乎全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:227-231`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:283` |
| 預覽 / 列印前 | 日期(起)(迄)必填 | `TMKR004` `TMKR005` `TMKR008` `TMKR901` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:278`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR005.cs:220`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:206`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:224` |
| 預覽 / 列印前 | 至少勾一檔基金 | `TMKR004` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:298` |
| 預覽 / 列印前 | 基金分類選了群組 / 費率 / 代碼卻沒指定值 | `TMKR008` `TMKR009` `TMKR010` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR008.cs:223-235`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:231-243`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:347-359` |
| 預覽 / 列印前 | AO 代碼(起)不可大於(迄) | `TMKR009` | 阻擋(**訊息掛在列印年月欄上**) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:216-221` |
| 預覽 / 列印前 | 結餘範圍 / 未交易日期必須成對 | `TMKR010` | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:331`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR010.cs:368` |
| 組參數時 | AO 代碼只填(迄)沒填(起) | `TMKR009` | **過濾(無提示,迄被丟掉)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:109-117` |
| 組參數時 | 業務員欄被停用 | `TMKR006` | **過濾(無提示)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:178-182` |
| 組參數時 | 客戶來源不是「專案」時,專案代碼不傳 | `TMKR901` | **過濾(無提示)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:164-165` |
| 轉 Excel 前 | 轉出路徑必填且必須存在 | 全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:236-246` |
| 離開路徑欄 | 路徑不存在 | 全部 | 阻擋 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:290-300` |
| 取數後 | 一筆資料都沒有 | 全部 | 警示(「無符合查詢條件的資料。」) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352` |
| 取數後 | **SP 執行失敗** | 全部 | 警示,但訊息與「查無資料」**一模一樣** | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:88` |
| 產 Excel 後 | 存檔失敗或使用者取消 | 全部 | **記錄不擋(完全沒有訊息)** | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385` |
| 日期連動 | `TMKR001` 的迄日固定為起日 +6 且不可輸入 | `TMKR001` | 記錄不擋(自動改值) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:69`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:306-317` |

最後一條值得單獨講:**`TMKR001` 的名字叫「日報表」,但迄日被程式固定成起日 +6,所以它其實是週報表**(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:308-311`),頁首還會印出七天的中文日期標題 `YD1`–`YD7`(`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:146-153`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:399-409`)。名字與行為不一致,但這一支是刻意的(七欄一週的版面),不是缺陷。

## 8. 跨模組共用

```text
[圖] TMK 跨模組影響面：CRM003A 靠 USAGE 分治、TMK 這側三處讀取的驗證結果、唯讀關係，以及整批匯入寫入代碼檔的副作用
圖中文字:① CRM003A 一張表多個模組共用，靠 USAGE 切成互不相見的世界 / CRMM003 寫入 USAGE 1 / 潛在客戶的唯一寫入者 / CASM001 寫入 USAGE 3 / CAS 的世界 TMK 看不到 / CRM003A〔共用〕 / 主鍵只有一欄 全表唯一 / ② TMK 這一側的三處讀取：兩處帶條件、一處沒帶 / TMKM001 通聯總覽 帶 USAGE / 與 crm.md 記載一致 / TMKM002 通聯總覽 帶 USAGE / 與 crm.md 記載一致 / TMKM002 取姓名 沒有條件 / 只靠潛在客戶序號 join / ③ 沒帶條件為什麼還是不會多撈：那一欄本身就是全表主鍵 / 序號唯一 join 不會多撈列 / 風險是顯示到別模組建的名字 / 若 CRMM003 覆核刪除該客戶 / TMK 的歷史通聯直接少一段 / ④ TMK 唯讀別人的表，沒有任何別的模組讀 TMK 的表 / BMS001A CRM003A CRM0061A / COD006A COD009 AA_USER / TMK 自有五張表 / 反查結果 無外部使用者 / 回歸範圍等於 TMK 自己 / 外加整批匯入會寫 COD006A / ⑤ 唯一的例外：整批匯入會往 COD006A 塞一列專案代碼 / TMKM001p1 填專案名稱 / 沒填就不寫 COD006A / 寫一列代碼分類 P5 / 狀態碼寫死 直接生效 / 全庫的 P5 下拉跟著多一筆 / 沒有任何畫面刪得掉
```

*圖:圖 5 跨模組。灰虛框=唯讀 join 的外部表；黑框=沒有原始碼或已確認的風險；橘虛框=〔客戶特定〕。TMK 對 CRM003A 是純唯讀，寫入者只有 CRMM003 與 CASM001；真正會回頭打到別人的只有整批匯入那一條：它會在共用代碼檔 COD006A 塞一列並直接標成已覆核。*

這一章回答一個問題:**改 TMK 的表會打到誰、改別人的表會打到 TMK 哪裡。**

先講結論:**TMK 的五張表沒有任何別的模組在用**,所以第一個問題的答案是「只打到 TMK 自己」;第二個問題才是重點。

### 8.1 `CRM003A`:從 TMK 這一側驗證 `USAGE` 分治

`crm.md §8.1` 記載 `CRM003A` 靠 `USAGE` 切成互不相見的世界:CRM / TMK 用 `'1'`、CLS 用 `'2'`、CAS 用 `'3'`,並且點名 TMK 這側有三處讀取。逐條從 TMK 這邊對:

| `crm.md §8.1` 記的 | TMK 這側實際看到的 | 對得上嗎 |
|---|---|---|
| `TMKM001` 不寫、查詢 `= '1'`,錨點 `TMKM001_PO.cs:330` | `AND CRM003A.USAGE = '1'` 在通聯總覽第二路的 `UNION ALL` 裡,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:330` | **✔ 逐字對得上,行號也對** |
| `TMKM002`(重複檢查)不寫、查詢 `= '1'`,錨點 `TMKM002_PO.cs:296` | `AND CRM003A.USAGE = '1'`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:296` | **✔ 對得上。**但它不是「重複檢查」,它是**通聯總覽的第二路**,與 `TMKM001` 那一段逐字相同。`crm.md` 的用途描述要修 |
| `TMKM002`(取姓名)**無 `USAGE` 條件**,`LEFT JOIN`,錨點 `TMKM002_PO.cs:225` | `LEFT JOIN CRM003A ON CRM003A.PR_NO = TMK001A.PR_NO`,`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:225` | **✔ 完全對得上** |
| `crm.md §8.3` 說 TMK 讀 `CRM0061A` join `CRM003A` join `COD006A`,錨點 `TMKM001_PO.cs:328-331` | `FROM CRM0061A,CRM003A,COD006A`(`:328`)、`CRM0061A.PR_NO = CRM003A.PR_NO`(`:329`)、`USAGE = '1'`(`:330`)、`CRM003A.ID_NO = '{0}'`(`:331`) | **✔ 對得上** |

**三處以外還有第四處嗎?沒有。**全 TMK(含報表側)只有這三處提到 `CRM003A`,加上 `TMKM002Model.xsd` / `TMKM002View.xsd` 裡那張沒人填的 DataTable(§2.6)。

從 TMK 這側補三點 `crm.md` 沒有的:

1. **「取姓名沒帶 `USAGE`」在資料正確性上不會出事,但在語意上會。**`CRM003A` 的主鍵只有 `PR_NO` 一欄(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:1137-1140`,與 `crm.md §8.1` 一致),所以 join 不會多撈列。**真正的風險是顯示**:如果某個 `PR_NO` 是 `CASM001` 建的(`USAGE = '3'`),`TMKM002` 照樣會把那個名字印在畫面上,而使用者以為那是一筆潛在客戶。

2. **`TMKM002Model.xsd` 是 `CRM003A` 的第五份 schema 副本。**`crm.md §8.1` 列了四份(CAS 的 Model 與 View、CRM 的 Model 與 View),TMK 這裡還有兩份(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:699`、`Dev/ATLAS.TMK/Source/Entity/UIEntity.TMK/TMKM002View.xsd:699`),而且**沒有任何程式填它**。改 `CRM003A` 的欄位時,這兩份會被漏掉;好消息是漏了也不會壞,因為沒人用。

3. **`CRMM003` 的覆核刪除會讓 TMK 的通聯總覽少一段。**`crm.md §8.3` 已經點出 `CRMM003_PO` 會實體 `DELETE CRM006A`;從 TMK 這側看,後果就是通聯總覽的第二路(`CRM0061A` join `CRM003A`)撈不到東西——**畫面不會報錯,只會少幾列,而且沒有任何提示**。

| 改什麼 | 會打到 TMK 哪裡 |
|---|---|
| `CRM003A` 加欄 / 改型別 | TMK 的兩份 xsd 理論上要重生,但因為沒人填那張表,實務上不改也不會壞 |
| 改 `CRM003A.PR_NO` 的定義 | `TMKM002` 的取姓名 join、通聯總覽的兩路、`TMK001A.PR_NO` 三處都打到 |
| 改 `USAGE` 的值域 | 通聯總覽的兩路會突然看到 / 看不到資料;`TMKM002` 取姓名那一處**完全不受影響**(它本來就不看) |
| 刪掉某個 `USAGE = '1'` 的潛在客戶 | `TMKM002` 上那筆名單的 `PR_NAME` 變空白、通聯總覽少一段歷史 |

### 8.2 通聯總覽:三路 `UNION ALL`,兩個代碼分類

`CALLIN_RECORD` 這張結果集是 TMK 對外最複雜的一段 SQL,兩支 M 畫面逐字相同(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:306-348`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:272-314`):

| 路 | 來源 | 代碼分類 | 專案代碼欄填什麼 | 錨點 |
|---|---|---|---|---|
| 1 | `TMK001A` × `TMK002A` | 無(直接接 `TOPIC_MEMO`) | `TMK001A.OUTBND_CODE` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:309-320` |
| 2 | `CRM0061A` × `CRM003A` × `COD006A` | **`'1C'`**(客服進線通聯種類) | 寫死 `'080'` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:322-333` |
| 3 | `TMK0031A` × `COD006A` | **`'84'`**(電訪通聯原因小類) | `TMK0031A.OUTBND_CODE` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:335-345` |

三件要記住的:

1. **同一個欄位名 `CALLIN_CODE` 在兩張表上用不同的代碼分類**:`CRM0061A` 那邊是 `'1C'`,`TMK0031A` 這邊是 `'84'`。兩本字典,值域不重疊(假設;repo 內沒有 `COD006A` 的資料可以驗)。

2. **第二路的專案代碼寫死 `'080'`**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:327`)。`'080'` 不是任何一個真的 `OUTBND_CODE`,只是讓畫面上那一欄有東西顯示、好跟 TMK 自己的紀錄區分。〔客戶特定〕

3. **第一路有正確處理 NULL**:`AND NOT (TMK002A.TOPIC_MEMO IS NULL OR TMK002A.TOPIC_MEMO = ' ')`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:320`)。這是全模組唯一一處明確處理三值邏輯的地方,值得拿來對照 §4.2.2 的 `<> 'A0'`。

4. 三路的 `ID_NO` 都是用 `string.Format` 串進去的(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:351`),不是參數化。

### 8.3 TMK 讀別人的表,沒有人讀 TMK 的表

| 表 | TMK 怎麼用 | 錨點 |
|---|---|---|
| `BMS001A`〔共用〕 | 兩支 M 畫面 `LEFT JOIN` 取法代與四個拒絕行銷旗標;整批匯入時當 INSERT 的來源 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:218-219`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:223`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:580` |
| `CRM003A` `CRM0061A`〔共用〕 | 唯讀,見 §8.1、§8.2 | — |
| `COD006A`〔共用〕 | 六種代碼分類的來源;**整批匯入會 INSERT**,見 §8.4 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:333`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:345`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607` |
| `COD009` | 登入帳號對員工代碼,並用離職日過濾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:194-200`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:224`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:193-200` |
| `AA_USER` | 登入帳號對中文姓名;`TMKM901` 用的是 **INNER JOIN**(§4.5.2) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:105`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:126` |
| `TMK_MGN_V` | 主管判斷:有一列就是主管。**名字結尾是 `_V`,應該是 View,但 `DB/View/` 底下沒有它** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:226` |
| `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只在整批匯入那句 INSERT-SELECT 的六個子查詢裡,只讀 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:570-584` |

**反向:母體的「跨模組」欄全空,`crm.md` 與其他六篇也沒有任何一支畫面讀 TMK 的表。**`TMK001A` `TMK002A` `TMK003A` `TMK0031A` `TMK901` 改欄位時,回歸範圍就是 TMK 自己的三支 M 畫面 ＋ 四份 xsd(§4.1.4)。報表側不受影響,因為報表全走 SP,不吃 typed DataSet 的實體表定義。

### 8.4 唯一的例外:整批匯入會往 `COD006A` 塞一列

`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:603-631`:

```
if (EVAStringHelper.GetParamValue(Model, "OUTBND_NAME") != "")   // 加cod006a
    INSERT INTO cod006a (…) VALUES ('P5', :OUTBND_CODE, :OUTBND_NAME, ' ', 'Y', 'Y', 1, '301', …)
```

四件事:

1. **`CODE_SORT` 寫死 `'P5'`**〔客戶特定〕,與 `TMKM901` 讀專案下拉時用的 `new CodeDataSrc("P5")` 是同一本(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:45`)。

2. **`STATUS` 寫死 `'301'`、四眼六個 ID 全填登入者、六個日期全填 `SYSDATE`、`REJECTID` 填一個空白字元**(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:623`)。等於**繞過四眼直接生效**,COD 模組的覆核流程完全不知道有這一列。

3. **觸發條件只看名稱欄是不是空字串**。前端在選了既有代碼時會把名稱欄設成唯讀並填上既有名稱(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:162-163`),送出時只有在 `!utxtOUTBND_NAME.ReadOnly` 才把名稱加進參數(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:76-77`)。**所以「選既有代碼 → 不寫 `COD006A`」「打新代碼 → 寫一列」的判斷是靠前端的唯讀旗標,不是靠伺服端查 `COD006A`。**繞過前端就會重複 INSERT。

4. **沒有任何畫面刪得掉這一列。**`TMKM001p1` 只會新增;`COD006A` 的維護畫面在 COD 模組。這與 `crm.md §8.4` 記的「CSV 上傳一筆亂資料,分配期別下拉就多一個選項,而且沒有任何畫面可以刪掉它」是同一型。

| 改什麼 | 會打到誰 |
|---|---|
| 改 `COD006A` 的 `CODE_SORT` 值域 | TMK 六處下拉(`'P4'` `'P5'` `'P9'` `'84'` `'1C'` `'15'` `'20'`)＋ 整批匯入那句 INSERT |
| 改 `COD006A` 的欄位或 NOT NULL 條件 | 整批匯入那句 INSERT 是手寫欄位清單,**不會自動同步** |
| COD 那邊給 `'P5'` 加覆核規則 | TMK 匯入寫進去的那一列會是繞過規則的髒資料 |

### 8.5 共用控件與黑箱

| 控件 / 來源 | 用在哪 | 說明 |
|---|---|---|
| `UltraGridCheckedListManager` | 三個通話彈窗的大小類勾選 grid | **本模組自有**,放在 `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs`(570 行)。與 CRM 那支同名但是各自一份(`crm.md §8.5`) |
| `ExcelHelper` | 十一支報表的轉 Excel | **本模組自有**,`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs` |
| `ClientBizUtility.GetEMP_INFO` | 八支報表算登入者員工代碼 | 無原始碼,從呼叫端反推;**全部靠位置取第 2 段**(§7.5) |
| `ClientBizUtility.GetMasterEmpNo` | `TMKR003` 判斷主管 | 無原始碼,從呼叫端反推 |
| `SrNoCommentProcessor` | `TMKM002` 的跳號一覽表 | 無原始碼,從呼叫端反推;與 `CASM001` 用同一支,**號別也一起抄錯了**(§4.3.4) |
| `SerialNo.GetOUTBND_NO` | `TMKM002` 取號 | `Dev/Common/Source/Utility/TA.ServerUtility/SerialNo.cs:601-604` |
| `CRReportTransfer.TransferFileByte` | 十一支報表取 `.rpt` | 無原始碼,從呼叫端反推 |
| `CodeDataSrc` / `GetDropDownDataSrc` | 各畫面的代碼下拉 | 無原始碼,從呼叫端反推;**兩套並存**,`TMKM001` 同一支畫面裡兩種都用到(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107` vs `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:109`) |
| `PrNoDataSrc` / `BF_NODataSrc` | `TMKM002p1` 兩張 grid | 無原始碼,從呼叫端反推;**前置條件寫法不一致**(§4.3.2) |
| `SystemDateTime.GetSystemDateTime(APServer)` | 三個彈窗的通話日期預設值 | 無原始碼,從呼叫端反推 |
| `F_GET_FND_PROF_TYPE` | 整批匯入判斷股票型基金 | DB 函式,`DB/` 內沒有 |

## 附錄 A. 資料表總表

### A.1 母體的五張表

| 表 | 母體欄數 | xsd 欄數 | 四眼 | 主檔於 | 明細於 | 跨模組 |
|---|---|---|---|---|---|---|
| `TMK001A` | 50 | 49(`TMKM001`)/ 47(`TMKM002`) | Y | `TMKM001` `TMKM002` | — | 無 |
| `TMK002A` | 32 | 33 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK0031A` | 24 | 25 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK003A` | 24 | 25 | Y | — | `TMKM001` `TMKM002` | 無 |
| `TMK901` | **0** | 26(DataTable 名 `TMKM901`) | Y | `TMKM901` | — | 無 |

母體與 xsd 的欄數差異來源:母體算的是實體表定義,xsd 多了 `DATAID`(框架欄)與畫面用的衍生欄(`TMK002A` 的 `RECONTACT_DT` / `RECONTACT_TM`)。`TMK901` 母體記 0 欄是因為掃描器在 `DB/Table/` 找不到它的 DDL,`architecture.md §9` 的模組地圖也記成 `?`。**`TMK901` 的欄位定義只存在於 xsd 裡**(`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM901Model.xsd:15-127`)。

### A.2 實體表名與 xsd DataTable 名對照

| 實體表 | xsd DataTable | 說明 |
|---|---|---|
| `TMK001A` | `TMK001A` | 同名 |
| `TMK002A` | `TMK002A` | 同名 |
| `TMK003A` | `TMK003A` | 同名 |
| `TMK0031A` | `TMK0031A` | 同名 |
| `TMK901` | **`TMKM901`** | **不同名**,`xTableMapping("TMK901", "TMKM901")`(`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:36`) |

### A.3 母體之外、TMK 實際會動到的表

| 表 | 動作 | 出現在 |
|---|---|---|
| `COD006A` | **INSERT** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:607-623` |
| `BMS001A` `CRM003A` `CRM0061A` `COD009` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 只讀 | §8.3 |
| `AA_USER` `TMK_MGN_V` | 只讀,**兩者都不在掃描索引裡** | §8.3 |

### A.4 只存在於結果集、沒有同名實體表的 DataTable

| DataTable | 出現在 | 欄數 |
|---|---|---|
| `CALLIN_RECORD` | `TMKM001` `TMKM002` | 7 |
| `OUTBND_TOTAL` | `TMKM001` | 8 |
| `TMK001A1` | `TMKM001` | 2 |
| `CRM003A`(在 `TMKM002Model.xsd` 內) | `TMKM002`,**沒人填** | 69 |
| `TMKR001_1`–`TMKR010_3`、`TMKR901T0`–`TMKR901T4` | 11 支報表 | 見 §3.4 |

## 附錄 B. SP / Function / Trigger / View

### B.1 repo 內有原始碼的:**一支都沒有**

母體第 3 節是空的。`DB/` 底下找不到任何 TMK 的 SP / Function / Trigger / View。

### B.2 程式會呼叫、但 repo 內查不到原始碼的

| 類 | 名稱 | 被誰呼叫 | 參數數 |
|---|---|---|---|
| SP | `S_TA_TMKR001_GET` | `TMKR001` | 3 in ＋ 3 refcursor |
| SP | `S_TA_TMKR002_GET` | `TMKR002` | 3 in ＋ 3 refcursor |
| SP | `S_TA_TMKR003_GET_1` `_2` `_3` | `TMKR003` | 5 in ＋ 2 / 1 / 1 refcursor |
| SP | `S_TA_TMKR004_GET_1` `_2` | `TMKR004` | 6 in ＋ 1 refcursor |
| SP | `S_TA_TMKR005_GET_1` | `TMKR005` | 5 in ＋ 1 refcursor |
| SP | `S_TA_TMKR005_GET_2` | **沒有人呼叫**(整段被註解掉,`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR005_PO.cs:94`) | — |
| SP | `S_TA_TMKR006_GET_1` `_2` | `TMKR006` | 8 / 4 in ＋ 4 / 1 refcursor |
| SP | `S_TA_TMKR007_GET_1` | `TMKR007` | 5 in |
| SP | `S_TA_TMKR008_GET_1` | `TMKR008` | 5 in |
| SP | `S_TA_TMKR009_GET_1` | `TMKR009` | 6 in ＋ 2 refcursor |
| SP | `S_TA_TMKR010_GET_1` | `TMKR010` | 14 in ＋ 3 refcursor |
| SP | `S_TA_TMKR901_GET` | `TMKR901` | 11 in ＋ 5 refcursor |
| Fn | `F_GET_FND_PROF_TYPE` | `BatchAdd` 判斷股票型基金 | 2 in |
| View(推測) | `TMK_MGN_V` | 兩支 M 畫面的主管判斷 | — |
| Table(推測) | `AA_USER` | `TMKM901` 與報表 | — |

**這 15 個物件是本模組最大的黑箱。**所有報表口徑、主管的定義、股票型基金的判斷全在裡面。要改報表數字,九成是改 SP 不是改 C#。

## 附錄 C. 代碼對照

### C.1 專案代碼 `OUTBND_CODE`

| 值 | 意義 | 來源 |
|---|---|---|
| `'A0'` | AO 新開發客戶(`TMKM002` 的世界) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:161`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:227` |
| 其他 | 行銷專案,值來自代碼分類 `'P5'`;整批匯入時可以現場新建 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:617` |
| `'080'` | **不是真的專案代碼**,是通聯總覽第二路(客服進線)的顯示用標記 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:327` |

### C.2 通話種類 `CALLIN_CODE`(前三碼)

| 前三碼 | 統計欄 | 中文名 |
|---|---|---|
| `'001'` | `WILL_NUM` | 有意願申購 |
| `'004'` | `UNWILL_NUM` | 無意願申購 |
| `'004004'` | `OTHER_PRD_NUM` | 其他產品(**是 `'004'` 的小類,會重複計**) |
| `'005'` | `THK_NUM` | 勿打擾 |
| `'007'` | `NOCONTACT_NUM` | 無法聯絡 |

錨點:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:391`、`:403`、`:415`、`:427`、`:439`。**這五個值是 repo 內唯一能看到通話種類語意的地方。**

### C.3 代碼分類(`COD006A.CODE_SORT`)

| 分類 | 用途 | 錨點 |
|---|---|---|
| `'P4'` | 電訪重點 `TOPIC_CODE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:44` |
| `'P5'` | 專案代碼 `OUTBND_CODE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:45`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:617` |
| `'P9'` | 通聯原因**大類** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61` |
| `'84'` | 通聯原因**小類** | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:345` |
| `'1C'` | 客服進線通聯種類(CRM 那邊的) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:333` |
| `'15'` | 風險屬性 `CUST_STYLE` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:109` |
| `'20'` | 客戶等級 `CUST_CLASS` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:113` |
| `'440'` | 完成碼 `READY_YN` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:195` |
| `'476'` | 再郵寄別 `MAIL_AGAIN` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:192` |
| `'482'` | 是否含已結案清單(查詢條件) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:107` |

### C.4 報表選項值域

見 §7.3 的表。**三支報表的「彙總 / 明細」用了三組不同的碼。**

### C.5 其他在程式裡出現的字面量〔客戶特定〕

| 值 | 意義 | 錨點 |
|---|---|---|
| `'301'` | 整批匯入寫入的資料狀態碼(已生效) | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:579`、`:623` |
| `'00'` | 風險屬性查無時的預設值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:578` |
| `-1` / `"-1"` | 潛在客戶沒有戶號時的哨兵值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:63`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759` |
| `"2"` | 有效代碼預設值(「新戶開發」) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:392`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:456` |
| `1` | `TMK0031A.CALLIN_SEQ` 固定值 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:531` |
| `'08201'` | 電訪部門(六支報表固定) | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR004.cs:88` |
| `'08001'` `'08201'` | `TMKR901` 的銷售機構白名單 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:79` |
| `'G2'` / `'G11'` | `TMKR901` 的業務員部門 / `TMKR003` 的主管部門 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:81`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR003.cs:57` |
| `"20200101"` | `TMKR901` 專案下拉的起始日 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:87` |
| `'99991231'` | `COD009` 離職日為空時的代用值 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:200` |
| `"D11"` | 整批匯入的 `OUTBND_NO` 補零位數 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:647` |

## 附錄 D. 掃描母體與覆蓋率

### D.1 數字

`atlas_scan.py --module TMK` 的母體:畫面 14(B 0 / I 0 / M 3 / R 11)· 表 5 · SP 0 · Fn 0 · Trigger 0 · View 0 · rpt 24 · Service 0。

本文逐一交代:14 支畫面全部提及(§3.1、§3.4)、5 張表全部提及(附錄 A.1)、24 份 rpt 全部提及(§7.1)。

### D.2 母體沒列到、但本文寫了的東西

| 項目 | 為什麼寫 |
|---|---|
| `TMKM001p0` `TMKM001p1` `TMKM002p0` `TMKM002p1` `TMKM002p2` 五支彈窗 | 它們不是獨立畫面(沒有六層),但業務邏輯有一半在裡面 |
| `AA_USER` `TMK_MGN_V` | 只出現在 SQL 字串裡,掃描器抓不到;主管權限與姓名顯示都靠它們 |
| `COD009` `BMS001A` `CRM003A` `CRM0061A` `COD006A` `OFD081A` `OFD220A` `OFD221A` `OFD123A` `OFD601` `OFD607A` | 同上,只出現在 SQL 字串裡 |
| 13 支報表 SP(見附錄 B.2)、`F_GET_FND_PROF_TYPE` | 母體 SP 欄是 0,因為 `DB/` 內沒有;但程式確實在呼叫 |
| `TMKR901RPS0` | 程式指名但檔案不存在,列進來就是為了記錄這個缺陷 |

### D.3 母體列了、本文交代不足的

| 項目 | 交代程度 |
|---|---|
| 24 份 `.rpt` 的**版面內容** | 只寫到檔名、標題、對應選項與 SP。`.rpt` 是二進位,repo 內無法閱讀;欄位配置要開 Crystal Reports 才看得到 |
| `TMK901` 的實體欄位定義 | `DB/` 內沒有 DDL,只能從 xsd 反推(附錄 A.1) |
| 各 SP 的實際口徑 | 完全無法從 repo 得知(附錄 B.2) |

### D.4 標「假設」的地方總表

| # | 假設 | 依據 | 在哪一節 |
|---|---|---|---|
| 1 | TMK = 電話行銷 / CallOut | 欄位中文名、grid 標題「電話行銷CALL OUT記錄明細檔」、報表名 | §0.1 |
| 2 | `TMKM001` 是專案外撥、`TMKM002` 是 AO 新開發 | `'A0'` 切分 ＋ `TMKM002` 註解掉的舊碼寫「新戶開發(固定)」 ＋ `TMKM001` 靠專案代碼整批匯入 | §0.1、§0.2 |
| 3 | `TMKM901` 是名單移轉 | 欄位中文名「原CallOut專員」「新CallOut專員」＋ 覆核時的兩段 UPDATE / MERGE | §4.5.1 |
| 4 | 「名單什麼時候該打」靠人工,不靠系統 | 有活動日期與下次可連絡日期欄,但沒有任何程式讀它們去派工;模組內無 B 型畫面與 Service | §0.3、§6 |
| 5 | `'1C'` 與 `'84'` 兩本代碼字典值域不重疊 | 兩張表的 `CALLIN_CODE` 各自 join 不同的 `CODE_SORT`;`COD006A` 的資料不在 repo 內 | §8.2 |
| 6 | `TMKR001` / `TMKR002` 沒有查詢權限是刻意的 | 它們的維度是「建立者」,像主管報表;但程式無註解 | §7.8 |
| 7 | `TMK_MGN_V` 是一支 View | 名字結尾 `_V` ＋ 用法是「有一列就是主管」;`DB/View/` 內沒有它 | §8.3 |
| 8 | `TMKM901` 的 MERGE 範圍放大是漏寫不是設計 | 第一步逐列精準更新、第二步只用專案＋原專員比對;兩步的粒度不一致 | §4.5.3 |
| 9 | 全形空白會讓 MERGE 整句失敗 | Oracle 語彙分析器是否接受 U+3000 取決於字元集與版本,**repo 內無法驗證,務必實測** | §4.5.3、附錄 E10 |

## 附錄 E. 讀本文時要注意的地方

讀碼發現的缺陷與陷阱。每條:缺陷 / 影響 / 錨點 / 嚴重度。

### E1 平行畫面只改一邊:四個拒絕行銷旗標在 `TMKM002` 是死的

- **缺陷**:`TMKM002` 的主檔 SQL 照樣 `SELECT BMS001A.REJ_SELL_CHK / _DOC / _WEB / _PHONE` 四欄,但 `TMKM002Model.xsd` 的 `TMK001A` 沒有這四欄(它們被宣告在那張沒人填的 `CRM003A` DataTable 上),四個 checkbox 的 `Visible = false`,UI 程式一行都沒指派。

- **影響**:**AO 新開發畫面上看不到「拒絕電訪」旗標。**電訪專員在這支畫面開單時,不會被提醒這位客戶已表示拒絕電訪。`TMKM001` 那邊四個 checkbox 都正常顯示。這是業務層級的差異,不是排版差異。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:214-217`、`Dev/ATLAS.TMK/Source/Entity/DataEntity.TMK/TMKM002Model.xsd:949-964`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.Designer.cs:2015-2016`、對照 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:243-246`。

- **嚴重度**:**高**(法遵相關的旗標看不到)。

### E2 平行畫面只改一邊:再聯絡日期的拆法

- **缺陷**:`TMKM001` 的 `TMK002A` 明細 SQL 已經從 `TO_CHAR(TO_DATE(RECONTACT_DTTM,'YYYYMMDDHH24MISS'),…)` 改成 `SUBSTR(RECONTACT_DTTM,1,8)`,舊版留在註解裡;`TMKM002` 還是舊版。

- **影響**:`RECONTACT_DTTM` 只要有一筆格式不合(長度夠 10 但不是合法日期),`TMKM002` 會丟 `ORA-01861`,整個明細撈不回來;`TMKM001` 不會。**同一張表、同一筆資料,兩支畫面一支能開一支不能開。**

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:460-465`(新)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:468-477`(註解掉的舊版)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:326-331`(還是舊版)。

- **嚴重度**:**中高**。

### E3 同一件事兩套實作,而且舊的那套沒有主鍵條件

- **缺陷**:`TMKM002` 有兩支通話彈窗。舊的 `TMKM002p0` 用 `FirstOrDefault()` 抓 `TMK003A`、用 `Select()` 抓 `TMK0031A`,**兩個都不帶任何條件**;新的 `TMKM002p2` 用四段主鍵比對與 `GetDataFilter`。兩支同時存在,入口不同(按鈕 vs 雙擊 grid)。

- **影響**:只要這張單有兩個以上的項次,走 `TMKM002p0` 就會:(1) 改到**第一個**項次的通話記錄,不管你現在編的是哪一個;(2) 把不在本次勾選裡的**所有項次**的通聯原因 `Delete()` 掉。`TMKM002p0` 的註解自己寫「此功能對會對應一份通訊記錄,所以不做篩選(全部取出)」——這個前提在 `p2` 允許多項次之後就不成立了。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:74-75`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:113`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:255-256`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:268-269`;對照 `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:120-125`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:453-454`。

- **嚴重度**:**高**(靜默的資料遺失)。

### E4 跳號一覽表記到別人的號別,七處一致

- **缺陷**:`TMKM002` 取的號是 `SrNo.OUTBND_NO`(值 `"TMK001A"`),但七個四眼事件寫跳號紀錄時全部傳 `SrNo.AllotNoForNfd`(值 `"OFD220A"`,境內申購書號)。

- **影響**:TMK 的跳號稽核紀錄全部落在申購書號那一本帳上。查 OFD 申購書跳號時會看到一堆 TMK 的紀錄,查 TMK 的跳號則什麼都查不到。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:378`、`:384`、`:390`、`:396`、`:402`、`:408`、`:414`;號別定義在 `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:103` 與 `Dev/Common/Source/MappingCode/TA.MappingCode/SysCode.cs:321`;取號在 `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:151`。同型見 `bbs.md` 附錄 E1。

- **嚴重度**:**中**(稽核用,不影響業務資料)。

### E5 有訊息但沒有 `return`:`TMKM901` 檢核失敗照樣改資料

- **缺陷**:`TMKM901_BeforeAddButtonClicked` 檢核失敗只設 `e.Cancel = true`,後面的 `foreach` 照樣執行,把未勾選的列 `Delete()`。

- **影響**:使用者一筆都沒勾就按新增 → 跳「至少勾選一筆資料」→ 存檔被取消,但畫面上的名單**全部被標記成刪除**。再按一次新增就什麼都沒有了。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:93-99`。

- **嚴重度**:**中高**。

### E6 覆核回報永遠成功:`TMKM901` 的 `args.Cancel` 在迴圈裡被覆寫

- **缺陷**:`args.Cancel = dbProduct.ExecuteNonQuery(...) != 1;` 寫在 `foreach` 內,每一圈都覆蓋前一圈的結果。

- **影響**:十列裡第三列在 `TMK002A` 找不到,第四列成功 → `Cancel` 被設回 false、`CancelMsg` 也被蓋掉。**覆核成功,但有一筆沒移轉到,而且沒有任何人知道。**這與 DSM `DSMB001_PO.cs:75` 硬寫 `i = 1` 是同一型。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:182-185`。

- **嚴重度**:**高**。

### E7 CSV 遇壞列 `break`,靜默吃掉後面全部

- **缺陷**:整批匯入讀 CSV 時 `if (line.Length < 2) break;`。

- **影響**:檔案中間有一列少了逗號(或有一個空行),**後面所有列全部消失**,畫面上不會有任何提示,匯入照樣成功。一千筆的名單可能只進去三百筆。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:111`。

- **嚴重度**:**高**。

### E8 匯入筆數回報多一筆,而且空檔也回報成功

- **缺陷**:`int i = 1;` 被同時當成 `OUTBND_NO` 的流水號與回報的筆數。迴圈結束後 `AddResultRow(true, i, "")` 回報的是「實際筆數 + 1」。CSV 一筆都沒有時 `i` 仍是 1,照樣回報成功。

- **影響**:對帳對不起來;而且「匯入 0 筆」與「匯入 1 筆」在畫面上長得一樣(都顯示「複製成功」,因為前端只看 `ReturnCode`)。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:642`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:657`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:83-87`。

- **嚴重度**:**中**。

### E9 `AND` 應該是 `OR`:`TMKM002` 的哨兵值判斷是死碼

- **缺陷**:`if (string.IsNullOrWhiteSpace(mainRow.PR_NO) && mainRow.PR_NO == "-1")`。空白字串不可能等於 `"-1"`,條件恆為 false。

- **影響**:潛在客戶序號的哨兵值 `-1` 會被原樣填進畫面的 Searcher,再一路存進 `TMK001A.PR_NO`。同型見 CAS `CASB001_PO.cs:431`。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:759-762`。

- **嚴重度**:**中**。

### E10 全形空白混進 SQL:`TMKM901` 的 MERGE

- **缺陷**:`ON　(A.OUTBND_CODE = …` 的 `ON` 後面是 U+3000(全形空白),不是 ASCII 空白。

- **影響**:Oracle 的語彙分析器是否把 U+3000 當成空白,取決於用戶端字元集與版本。**如果不接受,整句 MERGE 會丟語法錯,`TMKM901` 的覆核就等於壞的**(第一步的 `TMK002A` 已經更新,但交易會回滾)。repo 內無法驗證,**務必實測**。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:230`。

- **嚴重度**:**高(待實測)**。

### E11 `TMKM901` 的 MERGE 範圍比工單大

- **缺陷**:第一步逐列用四段主鍵精準更新 `TMK002A`;第二步的 `MERGE INTO TMK001A` 卻只用「專案代碼 ＋ 原專員員工代碼」比對,沒有 `OUTBND_NO` 與 `ID_NO`。

- **影響**:只勾三筆,`TMK001A` 上那位專員在該專案的**全部**名單的 `EMP_NO` 都會被改掉。**是設計還是漏寫,程式碼無法分辨,需要業務確認。**

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:169-186`(第一步)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:224-226`(第二步的比對條件)。

- **嚴重度**:**高**。

### E12 `TMKM901` 帶資料用 INNER JOIN `AA_USER`,離職的人帶不出來

- **缺陷**:`FROM TMK002A,TMK001A, AA_USER WHERE … AND TMK002A.USER_ID_T = AA_USER.USERID`。

- **影響**:這支畫面的主要情境就是「專員離職,把名單轉給別人」。**如果帳號已經從 `AA_USER` 移除,他名下的名單一筆都帶不出來**,畫面上只會顯示空白,不會說為什麼。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:68`、`:72`。

- **嚴重度**:**中高**。

### E13 Oracle 三值邏輯:`<> 'A0'` 遇 NULL 是 UNKNOWN

- **缺陷**:`TMKM001` 有兩處 `OUTBND_CODE <> 'A0'`,一處在主檔 `WHERE`、一處在 CTE `MYTMK002A`。

- **影響**:`OUTBND_CODE` 若為 NULL,那筆被靜默濾掉。`OUTBND_CODE` 是主鍵所以理論上不會 NULL,**但這是全模組僅有的兩處 `<>` 比較,而 CAS `CASB001_PO.cs:214`、CLS `CLSM001_PO.cs:179`、DSM `DSMB001_PO.cs:136` 三個模組都因為同一型寫法出過事**。要改 `OUTBND_CODE` 的 NOT NULL 條件前先看這兩行。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:206`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:245`。

- **嚴重度**:**低(目前)/ 中(改 schema 後)**。

### E14 字串串接進 SQL

- **缺陷**:五處把值直接 `string.Format` 進 SQL:登入者帳號、姓名 `LIKE`、再聯絡日期起訖、通聯總覽的統編、專案總計的專案代碼。

- **影響**:值內含單引號就會語法錯,惡意值可以改變語意。姓名欄是自由文字輸入,風險最高。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:259`、`:261`、`:263`、`:265`、`:351`、`:451`;`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:228`、`:241`、`:243`、`:245`、`:317`。另外 `UltraGridCheckedListManager.GetDataFilter` 也是字串組 DataTable 篩選(`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:538`)。

- **嚴重度**:**中高**。

### E15 `catch` 把所有例外翻譯成一句話

- **缺陷**:四處把不同原因的失敗壓成同一句訊息。

- **影響**:連線失敗、SQL 語法錯、權限不足在畫面上看起來都一樣。

- **錨點**:`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM901_PO.cs:82`(「查無資料」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:664`(「執行失敗,請檢查」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:693`(「檢核失敗,請檢查」)、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:454`(「取得批次失敗,請檢查」——**訊息裡的「批次」跟這支方法一點關係都沒有**)。

- **嚴重度**:**中**。

### E16 例外訊息直接丟給使用者看

- **缺陷**:整批匯入彈窗兩處 `ShowMessage(..., ex.ToString())`,顯示完整堆疊。

- **影響**:使用者看到一整面 .NET 堆疊;同時洩漏內部路徑與類別名。

- **錨點**:`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:130`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:159`。同型見 CAS `CASM004_PO.cs:227`、COD `CODM009_Pxy.cs:36`。

- **嚴重度**:**中**。

### E17 「查無資料」與「SP 失敗」在報表上長得一樣

- **缺陷**:十一支報表 PO 的成功零筆與 `catch` 都是 `AddResultRow(false, 0, "")`,訊息都是空字串。

- **影響**:SP 掛掉時使用者看到「無符合查詢條件的資料。」,會以為是條件下錯,不會回報問題。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:80`、`:88`;畫面端 `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:348-352`。

- **嚴重度**:**中**。

### E18 報表 PO 的 `catch` 先 `tran.Rollback()`

- **缺陷**:`tran` 在 `try` 的第一行才指派;`BeginTransaction()` 自己丟例外時 `tran` 是 null,`catch` 裡再丟 `NullReferenceException`。

- **影響**:原始錯誤被吃掉,`HandleBusinessException` 收到的是 NRE。十一支報表全中。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR001_PO.cs:51-54`、`:85-90`。

- **嚴重度**:**中**。

### E19 產 Excel 失敗完全沒有訊息

- **缺陷**:`if (GenExcelFile(...) == true) 顯示成功`,沒有 `else`;`ExcelHelper` 用錯誤訊息字串 `Contains("0x800A03EC")` 判斷要不要吞例外。

- **影響**:存檔被防毒擋掉、路徑沒權限、檔案被開著 → 使用者按完鈕什麼都沒發生,以為還在跑。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR001.cs:382-385`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/App_Code/ExcelHelper.cs:67-75`。

- **嚴重度**:**中**。

### E20 `TMKR901` 指名一支不存在的 `.rpt`

- **缺陷**:`GetReportFileTitle()` 回 `("TMKR901RPS0", "")`,`Dev/ATLAS.TMK.Report/Source/CrystalReports/Report.TMK/` 底下沒有這個檔。

- **影響**:`TMKR901` 的預覽與列印兩條路都拿不到報表,只有轉 Excel 能用。同型見 `bbs.md` 附錄 E11。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:194`;母體第 4 節的 24 份清單。

- **嚴重度**:**高**。

### E21 `TMKR901` 算了登入者員工代碼卻沒傳

- **缺陷**:`xUserEmpNo` 在 `FormInitial` 算好,`GetQueryVDB` 沒有把它加進參數。

- **影響**:這支報表沒有任何登入者查詢權限過濾,任何能開這支畫面的人都看得到全部資料。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:55-64`、`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR901.cs:143-185`。

- **嚴重度**:**中高**。

### E22 `TMKR009` 的錯誤訊息掛在錯的控件上

- **缺陷**:「AO代碼(起) 不可大於 AO代碼(迄)」這條錯誤被 `AddError` 到 `udatPRINT_YYMM`(列印年月)上。

- **影響**:紅框標在列印年月欄,使用者會去改日期,改不好。同型見 CLS `CLSR002_PO.cs:864`。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:216-221`。

- **嚴重度**:**低**。

### E23 `TMKR009` 只填「AO代碼(迄)」時,迄會被靜默丟掉

- **缺陷**:`EMP_NO_END` 的 `AddParametersRow` 巢狀在 `EMP_NO_ST` 的判斷式裡面。

- **影響**:只填迄不填起 → 兩個參數都不傳 → 查全部,使用者以為有過濾。

- **錨點**:`Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR009.cs:109-117`。

- **嚴重度**:**低**。

### E24 被註解掉但外殼還在的六處

| 處 | 內容 | 錨點 |
|---|---|---|
| 1 | 「只有第一個項次能設有效代碼」的整段判斷(兩支彈窗) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:374-381`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:345-352`。**外層的 `first` 變數還在算,但只剩下面那個 `IsAddNew` 分支用得到** |
| 2 | 查詢前「五個條件必須擇一填寫」(兩支 M 畫面) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:129-139`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:100-111`。`TMKM001` 後來在 `DoSearchValidate` 補回來了,`TMKM002` 沒有——註解寫「因需查詢所有,故改為不check」 |
| 3 | `TMK003A.COMMENT1` 的回寫(`TMKM001p0` 與 `TMKM002p2`) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:477`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:444`。**只有舊的 `TMKM002p0` 還在寫**(`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p0.cs:260`),所以同一張表的同一欄有人寫有人不寫 |
| 4 | `TMKM002` 的整段明細欄位回寫(15 行) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:448-472`。主檔頁上那幾個明細控件現在只是擺設 |
| 5 | `TMKR005_PO` 的 `rpt_type` 分支 | `Dev/ATLAS.TMK.Report/Source/PO/ReportPO.TMK/TMKR005_PO.cs:83-115`。`rpt_type` 變數在 `:58` 算出來後**完全沒用到**;`S_TA_TMKR005_GET_2` 因此是一支沒人呼叫的 SP |
| 6 | `TMKR006` 的每月配額數頁首參數 | `Dev/ATLAS.TMK.Report/Source/UI/ReportUI.TMK/TMKR006.cs:159`。參數照傳給 SP,但報表上印不出來 |

- **嚴重度**:**低到中**(第 3 條會造成資料不一致)。

### E25 其他讀碼陷阱

| # | 內容 | 錨點 |
|---|---|---|
| 1 | 主檔 SQL 有**兩個 `LEFT JOIN` 都叫 `X`**(`TMK_MGN_V X` 與 `MYTMK002A X`)。目前因為兩者沒有同名欄位被引用而能跑,任何一邊加欄位就會 `ORA-00918` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:227`、`:231` |
| 2 | `LEFT JOIN MYEMP_LIST Z ON 1 = 1` —— 沒有關聯條件的 join,靠 `WHERE` 裡的 `Z.EMP_NO = TMK001A.EMP_NO` 收尾 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:229-230` |
| 3 | 整批匯入的子查詢 alias `A` 蓋掉外層的 `FROM BMS001A A` | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:572` |
| 4 | 四句 DELETE 包在 `string.Format` 裡但樣板沒有 `{0}`,傳進去的參數完全沒用 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:595-602` |
| 5 | `CheckExists` 先塞一句不合法的 `"SELECT 1 = 1"` 佔位,靠後面覆蓋才沒事 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:679` |
| 6 | 再聯絡時間的檢核訊息說「必須介於1~24時之間」,實際只擋 0,25 以上照過(三處都一樣) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:546-551`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:870-875`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:512-517` |
| 7 | 有效代碼變更時無提示覆蓋同名單全部項次 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p0.cs:437-447`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p2.cs:402-412` |
| 8 | `GetLAST_USERID` 取的是 `MAX(USER_ID_L)`(上次服務人員),方法名與註解卻說「最後指派人員」 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:433-438` |
| 9 | `TMKM901` 的「已覆核不可修改」用 `APPROVEID != string.Empty` 判斷;ATLAS 的預設值常是一個空白字元 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:84` |
| 10 | `TMKM901` 把「伺服器一列結果都沒回」當成成功 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM901.cs:125` |
| 11 | `GetCRM003A_Row` 有三組重複的 `HM_TEL_AREA` / `HM_TEL` 指派,後兩組是複製貼上殘留 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:842-853` |
| 12 | `TMKM002p1` 兩張 grid 的 `LIKE` 前置條件寫法不一致(一邊自動加 `%`,一邊要自己加) | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002p1.cs:66` vs `:83-84` |
| 13 | `TMKM002` 新增列時 `Convert.ToDecimal(this.custBF_NO.Value)`,潛在客戶沒有戶號時會丟例外 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM002.cs:969`、`:985` |
| 14 | `TMKM001_Ctl.CheckExists` 的區域變數叫 `m_OFDM907_PO` —— 從 OFD 那支畫面複製過來沒改名 | `Dev/ATLAS.TMK/Source/Control/Control.TMK/TMKM001_Ctl.cs:66` |
| 15 | `TMKM001_Pxy` 的兩支自訂方法 `new TMKM001_Ctl()` 而不用 `this.Control`;`GetExceptionResult` 定義了卻沒人呼叫 | `Dev/ATLAS.TMK/Source/FormProxy/FormProxy.TMK/TMKM001_Pxy.cs:30-36`、`:43`、`:59` |
| 16 | 範本下載用 `Encoding.Default` 寫檔,讀回來的 `StreamReader` 用預設 UTF-8 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:87` vs `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001p1.cs:104` |
| 17 | 通聯原因大類是用 `code.Substring(0, 3)` 取的,代碼短於 3 碼會丟例外 | `Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:416` |
| 18 | `TMKM001` 的通聯管理器註解說「只建一次」,但每次關掉彈窗都 `Dispose()`,下次靠 `Initialize` 重建 → 每開一次彈窗就重查兩次 `COD006A` | `Dev/ATLAS.TMK/Source/UI/UI.TMK/TMKM001.cs:61`、`:464`、`Dev/ATLAS.TMK/Source/UI/UI.TMK/App_Code/UltraGridCheckedListManager.cs:302-327` |
| 19 | `TMKM001` 的主檔 SQL 有兩行 180 個以上的空白把註解推到極右,`TMKM002` 也照抄 | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM001_PO.cs:180`、`Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:203` |
| 20 | `TMKM002` 的七處 `throw new ApplicationException("")` 是**空訊息例外** | `Dev/ATLAS.TMK/Source/PO/PO.TMK/TMKM002_PO.cs:378`、`:384`、`:390`、`:396`、`:402`、`:408`、`:414` |

### E26 編碼:全模組乾淨

TMK 與 TMK.Report 兩個專案底下所有 `.cs` / `.xsd` / `.config` **全部是 UTF-8 with BOM**,沒有 cp950 混編的問題(這在 ATLAS 裡算少見,`bbs.md` 附錄 E14 記的 BBS 那邊是混的)。唯一的編碼問題是 E25 第 16 條的 CSV,以及 E10 那個混進 SQL 的全形空白。

## 附錄 F. 版本紀錄

| 版本 | 日期 | 變更 |
|---|---|---|
| v1 | 2026-09-15 | 初版。重點:`TMKM001` / `TMKM002` 的 `'A0'` 分治與逐層相似度量測、11 支 R 與 24 份 rpt 的對應、從 TMK 側驗證 `crm.md §8.1` 的 `USAGE` 分治、26 條讀碼陷阱 |

由 build_doc.py v2.0.0 於 2026-09-15 10:47 產生 · 標題 118 · 圖 5 · 表格 69 · 程式錨點 593 · § 連結 87 · 引用檢查：畫面 17（缺 0） · Table 17（缺 0） · Report 24（缺 0） · 結果集 27（缺 0）

快速鍵：/ 或 Ctrl+K 搜尋目錄 · Esc 清除／關閉放大圖 · 點章節標題左側方塊可收合
