---
name: hdc-query-skill
description: >
  คู่มือสร้าง SQL ติดตาม KPI HDC จาก HosXP — อธิบายความสัมพันธ์ HDC vs HosXP,
  field mapping, ช่องว่างข้อมูล, pattern แฟ้ม ANC/LABOR/EPI
  ใช้เมื่อต้องเขียน SQL KPI แม่และเด็ก, ANC, หรือต้องอ้างอิง HDC exchange data
---

# HDC KPI Query Skill

## ขั้นตอนการเขียน SQL จาก HDC (ทำตามลำดับ)

### ขั้นที่ 1 — อ่าน KPI spec ให้ครบก่อนเขียน SQL

อ่านไฟล์ template/spec (PNG, PDF, หรือเอกสาร) ในโฟลเดอร์ที่ user ให้มา เพื่อตอบคำถามให้ได้:

| คำถาม | หาจากที่ไหน |
|---|---|
| **B** (denominator) คืออะไร? | คำอธิบาย "เป้าหมาย" ในเอกสาร |
| **A** (numerator) คืออะไร? | คำอธิบาย "ผลงาน" ในเอกสาร |
| filter population? | เงื่อนไข (สัญชาติ, พื้นที่, ช่วงอายุ, ปีงบ) |
| GROUP BY อะไร? | หัวคอลัมน์ผลลัพธ์ (ตำบล / อำเภอ / ปี / ไตรมาส) |
| แหล่งข้อมูล HDC? | ชื่อแฟ้ม F43 ที่ระบุ (LABOR, ANC, CHRONIC, EPI...) |

**ถ้ามี ETL SQL reference** (เช่น `etl_sql.md`) ให้อ่านด้วย — จะเห็น logic การคำนวณ A/B ที่แท้จริงใน HDC

---

### ขั้นที่ 2 — map F43 แฟ้ม → HosXP table

ค้นหา mapping จาก `sql/43files/` ว่าแฟ้ม F43 ที่ใช้ตรงกับ HosXP table ใด:

| F43 แฟ้ม | HosXP table หลัก | field สำคัญ |
|---|---|---|
| LABOR (26) | `person_anc` | `labor_date` = BDATE, `preg_no` = GRAVIDA |
| ANC (25) | `person_anc_service` | `pa_week` = GA, `anc_service_date` = DATE_SERV |
| CHRONIC (15) | `clinicmember` | `clinic` = รหัสโรค, `regdate` |
| EPI (22) | `ovst_vaccine` + `village_student_vaccine_list` | `export_vaccine_code` = VACCINETYPE |
| PERSON (01) | `person` + `patient` | `cid`, `chwpart/amppart/tmbpart` |

**อ่านไฟล์ที่เกี่ยวข้องใน `sql/43files/`** เพื่อดู query จริงที่ใช้ export F43 — ไม่ต้องเดาเอง

---

### ขั้นที่ 3 — วิเคราะห์ Exchange CSV (ถ้ามี)

ถ้า user มี exchange file จาก HDC (`exchange_file_*.csv`) ให้อ่านและ parse ก่อนเขียน SQL:

```python
import csv
from collections import defaultdict

rows = list(csv.DictReader(open('exchange_file.csv')))

# 3a. หา B และ A จากข้อมูลจริง
# ANC/LABOR: ต้อง dedup by (cid, bdate) เพราะ 1 คน อาจมีหลาย gravida
seen = {}
for r in rows:
    key = (r['cid'], r['bdate'])          # ปรับ key ตาม KPI
    passed = r['anc_12'] == 'ผ่านการประเมิน'  # ปรับ pass condition ตาม KPI
    if key not in seen:
        seen[key] = {'pass': passed, 'vhid': r['check_vhid']}
    else:
        seen[key]['pass'] = seen[key]['pass'] or passed

B_hdc = len(seen)
A_hdc = sum(1 for v in seen.values() if v['pass'])

# 3b. group by tambon (check_vhid[:6])
tmb = defaultdict(lambda: [0, 0])
for v in seen.values():
    t = v['vhid'][:6]
    tmb[t][0] += 1
    tmb[t][1] += int(v['pass'])

for t in sorted(tmb):
    b, a = tmb[t]
    print(f'{t}: B={b} A={a} %={a*100/b:.1f}')
```

**เป้าหมาย**: รู้ B_hdc, A_hdc, และ per-tambon ก่อนเขียน SQL เพื่อใช้เป็น target เปรียบเทียบ

---

### ขั้นที่ 4 — เขียน SQL draft

โครงสร้างมาตรฐาน:

```sql
-- comment: B = ..., A = ..., source, ปีงบ
SELECT
  tambon_expr AS tambon,
  COUNT(*) AS B,
  SUM(CASE WHEN <A_condition> THEN 1 ELSE 0 END) AS A,
  ROUND(A * 100.0 / NULLIF(B, 0), 2) AS pct,
  -- quarterly columns ถ้าต้องการ
FROM <B_table> b_tbl
JOIN person p ON ...
JOIN patient pt ON ...
LEFT JOIN thaiaddress ta ON CONCAT(pt.chwpart,pt.amppart,pt.tmbpart) = ta.addressid
LEFT JOIN (
  -- pre-aggregate A source — ห้าม correlated subquery
  SELECT key_col, <aggregate> AS a_val
  FROM <A_table>
  WHERE <A_filter>
  GROUP BY key_col
) a_sub ON a_sub.key_col = b_tbl.key_col
WHERE <B_filter>
  AND pt.nationality = '99'
  AND pt.chwpart = '67' AND pt.amppart = '02'   -- อ.ชนแดน
GROUP BY tambon_expr
UNION ALL
SELECT 'รวม', COUNT(*), ... (no GROUP BY, same WHERE)
ORDER BY sort_order, tambon
```

**กฎ MariaDB 10.1.19**: ห้าม CTE / Window Functions — ใช้ derived table ใน FROM เสมอ
**กฎ performance**: A ที่ต้องนับต่อแถว → pre-aggregate แล้ว LEFT JOIN อย่าใช้ correlated subquery

---

### ขั้นที่ 5 — ทดสอบและเทียบ

```bash
docker exec sql-test python3 -c "import pymysql; ..."
```

เปรียบเทียบกับ HDC exchange CSV:

| ค่า | HosXP | HDC CSV | ยอมรับได้? |
|---|---|---|---|
| B รวม | ? | ? | ±10% ถือว่า OK |
| A รวม | ? | ? | ต่ำกว่า HDC ได้ถึง 20% |
| per-tambon | ? | ? | อาจต่างได้เพราะ check_vhid vs tmbpart |

**ถ้า B ต่างมากกว่า 10%**: ตรวจ filter (nationality, area, ปีงบ, labor_date IS NOT NULL)
**ถ้า A ต่างมากกว่า 20%**: ตรวจ join กับ service table ว่าถูกต้อง, ส่วนที่เกินคือข้อมูลข้ามโรงพยาบาล (แก้ไม่ได้)

---

### ขั้นที่ 6 — document ช่องว่างใน SQL comment

เพิ่ม comment อธิบายข้อจำกัดก่อน SELECT:

```sql
-- *** ข้อจำกัด: query นี้ดึงเฉพาะข้อมูลใน HosXP 11264 ***
-- B: อาจน้อยกว่า HDC ~X% เพราะ ...
-- A: อาจน้อยกว่า HDC ~X% เพราะ ...
```

---

## HDC vs HosXP — ภาพรวม

HDC (Health Data Center) รวบรวมข้อมูลจาก **ทุก รพ./รพ.สต.** ในเครือข่ายอำเภอ/จังหวัด ผ่าน F43 (43 แฟ้มมาตรฐาน)
HosXP ของ รพ.ชนแดน (11264) มีเฉพาะข้อมูลผู้ป่วยที่มาใช้บริการที่ รพ.ชนแดน หรือ รพ.สต.ในเครือที่ share DB เดียวกัน

**ผลที่ตามมา:**
- B (denominator): HosXP ≈ HDC ±10% — ขาดผู้ป่วย PCU-only ที่ไม่เคยมา รพ.ชนแดน
- A (numerator): HosXP น้อยกว่า HDC ~15-20% — ขาด ANC visit ที่ รพ.สต./รพ.อื่น ไม่มีใน person_anc_service

---

## 1. check_vhid — รหัสหมู่บ้านใน HDC

**รูปแบบ**: 8 หลัก `CCAATTMM` (จังหวัด 2 + อำเภอ 2 + ตำบล 2 + หมู่ 2)
- ตัวอย่าง: `67020610` → จ.เพชรบูรณ์ อ.ชนแดน ต.บ้านกล้วย หมู่ 10
- `SUBSTR(check_vhid, 1, 6)` = tambon code = เทียบได้กับ `CONCAT(chwpart, amppart, tmbpart)` ใน `patient`

**วิธีคำนวณใน HDC ETL**: ใช้ `home` table + ตาราง insurance (dbpop) + NHSO assignment — ซับซ้อน ไม่มีใน HosXP

**สิ่งที่ใกล้เคียงที่สุดใน HosXP**:
| HDC field | HosXP field | หมายเหตุ |
|---|---|---|
| `check_vhid` (8 หลัก) | `CONCAT(pt.chwpart, pt.amppart, pt.tmbpart, LPAD(pt.moopart, 2, '0'))` | ครบ 8 หลัก · moopart เก็บ 1-2 หลักต้อง LPAD |
| `check_vhid[:6]` | `CONCAT(pt.chwpart, pt.amppart, pt.tmbpart)` | 6 หลักแรก = tambon เท่านั้น |
| `check_hosp` (PCU) | `p.pttype_hospsub` | PCU ที่รับผิดชอบผู้ป่วย |
| `check_typearea` | `pt.type_area` หรือ `pt.inregion` | typearea 1/3 = ในเขต |
| `input_hosp` | `'11264'` (constant) | HosXP 11264 คือระบบที่บันทึก · person_anc ไม่มี field นี้ |

**tambon grouping pattern**:
```sql
-- ใช้ patient.tmbpart จับ tambon ใน HosXP
REPLACE(SUBSTRING_INDEX(ta.full_name, ' ', 1), 'ต.', '') AS tambon
LEFT JOIN thaiaddress ta ON CONCAT(pt.chwpart, pt.amppart, pt.tmbpart) = ta.addressid
```

---

## 2. แฟ้ม ANC/LABOR — field mapping

### F43 LABOR → HosXP `person_anc`
| HDC field | HosXP | ความหมาย |
|---|---|---|
| `BDATE` | `pa.labor_date` | วันคลอด (B denominator) |
| `LMP` | `pa.lmp` | วันแรกประจำเดือนครั้งสุดท้าย |
| `EDC` | `pa.edc` | วันคาดคลอด |
| `GRAVIDA` | `pa.preg_no` | ครั้งที่ตั้งครรภ์ |
| `BHOSP` | `pa.labour_hospcode` | รพ.ที่คลอด |
| `hoscode` (CSV) | `p.pttype_hospsub` | PCU ที่ดูแลผู้ป่วย |
| `input_hosp` (CSV) | `'11264'` (constant) | ระบบที่บันทึก — person_anc ไม่มี field นี้ |
| `check_vhid` (CSV) | `CONCAT(pt.chwpart,amppart,tmbpart,LPAD(pt.moopart,2,'0'))` | รหัสหมู่บ้าน 8 หลัก · moopart ต้อง LPAD(2,'0') |

### F43 ANC → HosXP `person_anc_service`
| HDC field | HosXP | ความหมาย |
|---|---|---|
| `GA` | `pas.pa_week` | อายุครรภ์ (สัปดาห์) ขณะ visit |
| `DATE_SERV` | `pas.anc_service_date` | วันที่มา ANC |
| `ANCNO` | `pas.anc_service_number` | ครั้งที่ ANC |
| `ANCPLACE` | `'11264'` (constant) | รพ.ที่ให้บริการ ANC |

### t_person_anc fields ใน HDC (CSV exchange format)
| field | ความหมาย |
|---|---|
| `g1_ga` | GA ของ ANC visit แรกที่ ≤ 12 สัปดาห์ (ข้ามโรงพยาบาล) |
| `g2_ga` | GA ของ visit ช่วง 13-19 สัปดาห์ |
| `g3_ga` | GA ช่วง 20-25 สัปดาห์ |
| `g4_ga` | GA ช่วง 26-31 สัปดาห์ |
| `g5_ga` | GA ≥ 32 สัปดาห์ |
| `anc_12` | `'ผ่านการประเมิน'` ถ้า g1_ga IS NOT NULL (มี ANC ≤12wks) |
| `check_vhid` | รหัสหมู่บ้าน 8 หลัก ([:6]=tambon) · HosXP: `CONCAT(chwpart,amppart,tmbpart,LPAD(moopart,2,'0'))` |
| `hoscode` | PCU ที่รับผิดชอบ (= pttype_hospsub) |
| `input_hosp` | ระบบที่บันทึก · HosXP: `'11264'` เสมอ · person_anc ไม่มี field นี้ |
| `g1–g5 hospcode/input_hosp` | hospcode ต่อ visit · HosXP: `'11264'` เสมอ เพราะ `person_anc_service.provider_hospcode` มีแต่ NULL |

**⚠️ g1-g5 ไม่ใช่ลำดับ visit — เป็น GA range!** (ตรง ETL `t_person_anc`: g1≤12/g2 13-19/g3 20-25/g4 26-31/g5 32-40)
- g1 = ANC ≤12wks (ไม่จำเป็นต้องเป็น visit แรกตามลำดับเวลา)
- HosXP bucket: g1 `pa_week <= 12` (ไม่ใช่ BETWEEN 1 AND 12 — กัน ga=0 ตก false ไม่ผ่าน) · g5 `BETWEEN 32 AND 40`

**⚠️ ยืนยันแล้ว (anc_before12wks.sql เทียบ exchange_file_4291519_1.csv):**
- **anc_12 = g1_ga IS NOT NULL** ตรงกับ ETL `result=COUNT(IF(g1_ga<=12,...))` — ทดสอบ 63 แถว ไม่ขัดกันเลย
- **นับ B/A ต้อง dedup `(cid, bdate)` union-pass** — query = 1 row/pregnancy, 1 คนมีได้หลาย gravida
- **ห้าม filter `pt.type_area IN ('1','3')`** — patient.type_area (raw) ≠ HDC check_typearea (คำนวณ insurance/dbpop) · filter นี้ทำ B ร่วง 64→13
- ผลรันจริง: SQL B=64 vs HDC B=62 (ใกล้กัน) · SQL A=30 vs HDC A=37 (~19% undercount — ANC ≤12wk ที่ รพ.อื่น) · A = lower bound ต้องยืนยันใน HDC
- input_hosp/g*_hospcode/discharge = display-only ค่าไม่ตรง CSV (hardcode 11264 ตามข้อจำกัด DB) — ห้ามใช้ตัดสินหน่วยบริการจริง

---

## 3. KPI Pattern — แม่และเด็ก

### ตัวชี้วัด 1.1 ANC ≤ 12 สัปดาห์
```sql
-- B = หญิงไทยในเขต มี labor_date ในปีงบ
-- A = B ที่มี ANC visit (pa_week <= 12) ใน person_anc_service
SELECT
  REPLACE(SUBSTRING_INDEX(ta.full_name,' ',1),'ต.','') AS tambon,
  COUNT(*) AS B,
  SUM(CASE WHEN first_ga.min_ga <= 12 THEN 1 ELSE 0 END) AS A
FROM person_anc pa
JOIN person p ON p.person_id = pa.person_id
JOIN patient pt ON pt.hn = p.patient_hn
LEFT JOIN thaiaddress ta ON CONCAT(pt.chwpart,pt.amppart,pt.tmbpart) = ta.addressid
LEFT JOIN (
  SELECT pas.person_anc_id, MIN(pas.pa_week) AS min_ga
  FROM person_anc_service pas WHERE pas.pa_week > 0
  GROUP BY pas.person_anc_id
) first_ga ON first_ga.person_anc_id = pa.person_anc_id
WHERE pa.labor_date BETWEEN '2025-10-01' AND '2026-09-30'
  AND pt.nationality = '99'
  AND pt.chwpart = '67' AND pt.amppart = '02'
GROUP BY CONCAT(pt.chwpart,pt.amppart,pt.tmbpart)
```

### Pattern รายไตรมาส + รวม (UNION ALL)
```sql
-- ไตรมาสปีงบ: Q1=ต.ค.-ธ.ค., Q2=ม.ค.-มี.ค., Q3=เม.ย.-มิ.ย., Q4=ก.ค.-ก.ย.
SUM(CASE WHEN MONTH(pa.labor_date) IN (10,11,12) THEN 1 ELSE 0 END) AS B_q1,
SUM(CASE WHEN MONTH(pa.labor_date) IN (10,11,12) AND first_ga.min_ga<=12 THEN 1 ELSE 0 END) AS A_q1,
-- Q2, Q3, Q4 pattern เดียวกัน
-- แล้ว UNION ALL SELECT 'รวม' ... (no GROUP BY)
```

### area filter มาตรฐาน อ.ชนแดน
```sql
WHERE pt.nationality = '99'       -- สัญชาติไทย
  AND pt.chwpart = '67'           -- จ.เพชรบูรณ์
  AND pt.amppart = '02'           -- อ.ชนแดน
```

---

## 4. PCU → ตำบล mapping (อ.ชนแดน)

`person.pttype_hospsub` = รหัส PCU ที่ดูแลผู้ป่วย — ตรงกับ `hoscode` ใน HDC exchange CSV

| pttype_hospsub | PCU | ตำบล |
|---|---|---|
| `11264` | โรงพยาบาลชนแดน | ชนแดน (670201) |
| `07734` | รพ.สต.บุ่งคล้า | ดงขุย (670202) |
| `07735` | รพ.สต.หนองโก | ท่าข้าม (670203) |
| `07736` | รพ.สต.น้ำลัด | พุทธบาท (670204) |
| `07737` | รพ.สต.ห้วยงาช้าง | พุทธบาท (670204) |
| `14066` | สถานีอนามัย | พุทธบาท (670204) |
| `07738` | รพ.สต.เขาแม่แก่ | ลาดแค (670205) |
| `07739` | รพ.สต.ลาดแค | ลาดแค (670205) |
| `07740` | รพ.สต.หนองใหญ่ | ลาดแค (670205) |
| `07741` | รพ.สต.โคกสำราญ | บ้านกล้วย (670206) |
| `07742` | รพ.สต.ซับพุทรา | ซับพุทรา (670208) |
| `21982` | รพ.สต.โป่งนกแก้ว | ตะกุดไร (670209) |
| `07744` | รพ.สต.ศาลาลาย | ศาลาลาย (670210) |

---

## 5. ช่องว่างข้อมูล HosXP vs HDC

### B (denominator) gap
- **สาเหตุ**: ผู้ป่วยที่ใช้ PCU อย่างเดียว (ไม่เคยมา รพ.ชนแดน) ไม่มีใน HosXP 11264
- **ขนาด**: ประมาณ 5-10%
- **ตรวจสอบ**: `p.pttype_hospmain` — ถ้าไม่ใช่ '11264' อาจ duplicate หรือ outsider

### A (numerator) gap
- **สาเหตุ**: ANC visit ที่ รพ.สต./รพ.อื่น ไม่มีใน `person_anc_service` ของ 11264
- **ขนาด**: ประมาณ 15-20% (จาก session: HosXP=30, HDC=37)
- **ไม่สามารถแก้ได้**: ต้องใช้ข้อมูลจาก HDC โดยตรง

### tambon distribution gap
- **สาเหตุ**: `patient.tmbpart` = ที่อยู่ self-reported; `check_vhid` = สิทธิ์ประกัน (insurance assignment)
- **ผล**: per-tambon split ต่างกันได้ (เช่น ผู้ป่วยจาก ต.พุทธบาทลงทะเบียน รพ.หลักเป็น ชนแดน → patient.tmbpart='04' แต่ check_vhid='670204')

---

## 6. การอ่าน Exchange CSV จาก HDC

เมื่อได้รับ exchange file (เช่น `exchange_file_XXXXXXXX_1.csv`) สำหรับ KPI:

```python
import csv
from collections import defaultdict

rows = list(csv.DictReader(open('exchange_file.csv')))

# deduplicate by (cid, bdate) — HDC นับ distinct delivery
seen = {}
for r in rows:
    key = (r['cid'], r['bdate'])
    passed = r['anc_12'] == 'ผ่านการประเมิน'
    if key not in seen:
        seen[key] = {'pass': passed, 'vhid': r['check_vhid']}
    else:
        seen[key]['pass'] = seen[key]['pass'] or passed  # union: ANY gravida ผ่าน = ผ่าน

B = len(seen)
A = sum(1 for v in seen.values() if v['pass'])

# group by tambon (6 chars)
tmb = defaultdict(lambda: [0,0])
for v in seen.values():
    t = v['vhid'][:6]
    tmb[t][0] += 1
    tmb[t][1] += int(v['pass'])
```

**Key fields ใน HDC exchange CSV:**
| field | ความหมาย |
|---|---|
| `check_vhid` | หมู่บ้าน 8 หลัก ([:6] = tambon) |
| `hoscode` | PCU ที่รับผิดชอบ |
| `g1_ga` | GA ≤12wks (NaN = ไม่มี ANC ≤12wks) |
| `anc_12` | `'ผ่านการประเมิน'` / `'ไม่ผ่าน'` |
| `bdate` | วันคลอด |
| `lmp` | LMP |
| `gravida` | ครั้งที่ตั้งครรภ์ |

---

## 7. แหล่งข้อมูล Reference

| ไฟล์ | ข้อมูลอะไร |
|---|---|
| `tmp/1.1 anc_before12wks/etl_sql.md` | HDC ETL SQL ครบ — t_person_anc, t_person_db, check_vhid logic |
| `tmp/1.1 anc_before12wks/template_anc_before12wk.png` | template KPI spec |
| `sql/43files/ANC.sql` | F43 ANC export จาก HosXP (GA source = `pas.pa_week`) |
| `sql/43files/LABOR.sql` | F43 LABOR export จาก HosXP |
| `sql/mother_child/anc_before12wks.sql` | ตัวชี้วัด 1.1 ANC ≤12wks · **person-level 47 คอลัมน์** format HDC exchange file · g1–g5 GA buckets (≤12/13-19/20-25/26-31/≥32wks) · `anc_12` = ผ่าน/ไม่ผ่าน |
