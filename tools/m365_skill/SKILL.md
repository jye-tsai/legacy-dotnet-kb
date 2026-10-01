---
name: atlaskb
description: 查詢 ATLAS 老系統(.NET WinForms + Oracle)維護知識庫。凡是問到 ATLAS 的畫面代號(如 CASM001、OFDB061)、資料表(如 CAS003A)、SP / 報表 / Windows 服務、使用者回報的錯誤訊息、四眼(EVA)覆核、已知缺陷、六層架構,或要加欄位 / 加畫面 / 改 SP / 部署等維護步驟時使用。回答附出處,不編造。
---

# ATLAS 知識庫查詢

ATLAS 是一套老 .NET WinForms + Oracle 系統。本技能的 `references/` 是純讀原始碼彙整的**快照**知識庫(已去識別化)。一律用繁體中文回答。

`references/` 每個檔合併了數篇原始文件;每篇以 `【文件】kb/<路徑>.md` 這行開頭,例如 `【文件】kb/modules/cas.md`、`【文件】kb/runbooks/add-column.md`。回答時用這個路徑標出處。

## 鐵律

1. **先查再答**。先在 `references/` 找到依據再回答;不要憑一般常識回答 ATLAS 的細節。
2. **附出處**。每個結論後標 `(kb/<路徑>.md §章節)`。原文的程式錨點(`Dev/…/X.cs:行號`)原樣列出,並提醒「行號為快照當下版本,動手前以最新程式為準」。
3. **不編造**。原文標「推測」「假設」「版控外」「〔客戶特定〕」「〔共用〕」的內容,回答時保留標記。查不到就說「知識庫沒有」,並參考 `references/01-guide.md` 中 TROUBLESHOOT 的 §7(文件裡還沒有答案的症狀)。
4. **不要整份讀大檔**。資料檔與模組檔很大;先用代號 / 表名 / 訊息片段定位,只讀需要的段落。
5. 代號、表名、檔名、訊息原文照抄,不翻譯。

## 查詢流程

| 使用者問的是… | 先讀 | 再讀 |
|---|---|---|
| 畫面代號是什麼、六層檔案在哪 | `references/20-screens.md`(找 `[畫面 代號]` 那一行) | 該模組所在的模組檔(見下表) |
| 某張表被誰用、改它影響誰 | `references/21-tables.md`(找 `[表 表名]`) | 模組檔中該模組的「跨模組共用 / 跨模組依賴」章節 |
| SP / Function / Trigger / 報表範本 / 服務 | `references/22-objects.md`(找 `[物件 名稱]`) | 對應模組檔 |
| 使用者貼上的錯誤訊息 | `references/23-messages.md`(用訊息中固定的片段找;`{…}` 是變數部分) | 丟出位置所屬的模組檔 |
| 已知缺陷、某畫面有沒有坑 | `references/24-defects.md`(找 `[缺陷 模組]` 或畫面代號) | 模組檔中該模組的「附錄 E」 |
| 症狀排查(開不起來、資料沒進去、報表、批次、部署) | `references/01-guide.md` 的 `【文件】kb/TROUBLESHOOT.md` | 它指向的文件章節 |
| 代號規則、四眼 13 欄、部署矩陣、常用指令 | `references/01-guide.md` 的 `【文件】kb/CHEATSHEET.md` | `references/03-architecture.md` |
| 模組清單與中文名、手冊清單 | `references/01-guide.md` 的 `kb/modules/README.md`、`kb/runbooks/README.md` | — |
| 業務線、一日作業時序、端到端流程 | `references/02-overview.md` | — |
| 六層、.NET Remoting、四眼引擎、typed DataSet、畫面型別 | `references/03-architecture.md` | — |
| 要動手改 | `references/04-runbooks.md` 中對應的手冊 | 相關模組檔 |

### 模組在哪個檔

| 模組 | 檔案 |
|---|---|
| BBS、BMS、CAS、CLS、COD | `references/10-modules-bbs-bms-cas-cls-cod.md` |
| CPM、CRM、DSM、TMK | `references/11-modules-cpm-crm-dsm-tmk.md` |
| EC、MISC(TRP / OTA / FSK / IJP)、RSP、NFDR1、NFDR2 | `references/12-modules-ec-misc-rsp-nfdr.md` |
| OFD1–3(`ofd123`)、OFD4、OFD5 | `references/13-modules-ofd1-5.md` |
| OFD6、OFD7、OFD8、OFD9 | `references/14-modules-ofd6-9.md` |
| OFDB 批次(`ofdb`、`ofdb3`、`ofdb4`、`ofdb5`) | `references/15-modules-ofdb.md` |
| OFDI 查詢(`ofdi1`、`ofdi2`)、OFDR 報表(`ofdr1`、`ofdr2`) | `references/16-modules-ofdi-ofdr.md` |

OFD 畫面不確定屬於哪片時,先看 `20-screens.md` 該行的「各層檔案」路徑與模組欄。

### 維護手冊(都在 `references/04-runbooks.md`)

`add-column`(加欄位)· `add-screen`(加 M 維護畫面)· `add-query-screen`(加 I 查詢畫面)· `add-batch`(加 B 批次)· `add-report`(加 / 改 Crystal 報表)· `change-eva-flow`(改四眼流程)· `change-sp-fn-trigger`(改 SP / Function / Trigger / View)· `deploy`(部署)· `build-env`(建環境)。找 `【文件】kb/runbooks/<名稱>.md` 那一行開始讀。

## 背景速記

- 畫面代號 = 前 3 碼模組 + 第 4 碼型別(`M` 維護 / `I` 查詢 / `B` 批次 / `R` 報表)+ 3 碼流水號 + 可選後綴。六層檔名由代號推導:`UI.<MOD>/<代號>.cs` → `FormProxy.<MOD>/<代號>_Pxy.cs` → `Control.<MOD>/<代號>_Ctl.cs` → `PO.<MOD>/<代號>_PO.cs` → `<代號>Model.xsd`(DataEntity)/ `<代號>View.xsd`(UIEntity)。
- `A` / `B` 後綴成因至少七種,**不能套規則**,要逐支查。
- 四眼(EVA)= Entry(經辦鍵入)→ Verify(覆核)→ Approve(核准);核准前資料在待辦裡,不算正式資料(CHEATSHEET §4、architecture §3)。

## 回答格式

1. 一句話結論。
2. **依據**:條列重點,每條附出處與程式錨點。
3. **風險 / 注意**:跨模組共用的表、四眼影響、已知缺陷、推測或客戶特定的值。
4. 若涉及修改,**下一步**:指向對應手冊章節,並列出要一起改、重編、回歸測試的畫面與表。

問題太模糊時(例如只說「存檔失敗」),先問畫面代號或完整錯誤訊息。這是快照,與現行程式不符時以程式為準。
