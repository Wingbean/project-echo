---
name: hosxp-query-skill
description: >
  คู่มือโครงสร้าง table และ pattern การเขียน SQL สำหรับ HosXP (MariaDB)
  ใช้เมื่อต้องเขียน query ดึงข้อมูลผู้ป่วย, OPD/IPD, Lab, ยา, NCD, นัดหมาย หรือสถิติโรงพยาบาล
---

# HosXP SQL Query Skill

## Database
- **Engine**: MariaDB — Host: 192.168.10.1 / DB: hosxp
- **ปีงบประมาณไทย**: ต.ค. — ก.ย. (ปี 2567 = `'2023-10-01'`–`'2024-09-30'`, ปี 2568 = `'2024-10-01'`–`'2025-09-30'`, ปี 2569 = `'2025-10-01'`–`'2026-09-30'`)

---

## 1. ตาราง Core — ผู้ป่วย / ประชากร

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `patient` | `hn` | `cid`, `pname`, `fname`, `lname`, `birthday`, `nationality`, `death`, `pttype`, `type_area`, `inregion`, `in_cups`, `hometel`, `informtel`, `worktel`, `informaddr`, `addrpart`, `moopart`, `chwpart`, `amppart`, `tmbpart`, `po_code`, `last_visit` |
| `person` | `cid` | `patient_hn`, `sex`, `birthdate`, `age_y`, `age_m`, `age_d`, `occupation`, `nationality`, `person_discharge_id`, `death`, `house_regist_type_id` |
| `thaiaddress` | `addressid` | `full_name` |
| `house` | `house_id` | `address`, `village_id` — ใช้ `house.address` (ไม่ใช่ `house_no`) |
| `village` | `village_id` | `village_moo`, `village_name`, `village_code` |

**ลิงก์**: `patient.cid = person.cid` หรือ `person.patient_hn = patient.hn`
**ลิงก์ที่อยู่**: `person.house_id → house.house_id → village.village_id`

**Filter คนในพื้นที่ มีชีวิต ไม่จำหน่าย**:
```sql
WHERE pt.nationality = '99'
  AND p.person_discharge_id = '9'
  AND pt.death = 'N'
  AND (p.death = 'N' OR p.death IS NULL)
```

---

## 2. ตาราง WBC / วัคซีน

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `person_wbc` | `person_wbc_id` | `person_id`, `wbc_type` — 1 แถวต่อเด็ก 1 คน |
| `person_wbc_service` | `person_wbc_service_id` | `person_wbc_id`, `service_date`, `vn` — แต่ละครั้งที่มารับวัคซีน |
| `person_wbc_vaccine_detail` | `person_wbc_service_id` | `wbc_vaccine_id` — วัคซีนที่ได้รับในครั้งนั้น |
| `wbc_vaccine` | `wbc_vaccine_id` | `export_vaccine_code` — HDC code (D21/I11/R21/...) |
| `person_vaccine_elsewhere` | `person_id` | `person_vaccine_id`, `vaccine_date` — วัคซีนที่รับจากที่อื่น |
| `ovst_vaccine` | `ovst_vaccine_id` | `vn`, `person_vaccine_id`, `update_datetime` — วัคซีน OPD ทุกชนิด (WBC/EPI/Influenza/TT) |
| `person_vaccine` | `person_vaccine_id` | `export_vaccine_code`, `vaccine_name` — master: 815=Influenza adult, 816=Influenza ped, HPVC21/22, D21/I11/R21... |
| `village_student_vaccine` | `village_student_vaccine_id` | `village_student_id`, `vaccine_date` — วัคซีนรณรงค์ในโรงเรียน |
| `village_student_vaccine_list` | `village_student_vaccine_list_id` | `village_student_vaccine_id`, `student_vaccine_id`, `doctor_code` |
| `student_vaccine` | `student_vaccine_id` | `export_vaccine_code` — master: HPVC21/22/HPVG91/024/310... |
| `village_student` | `village_student_id` | `person_id`, `last_update`, `discharge` — `last_update` = เวลา update ล่าสุด (ใช้ filter F43 EPI) |

**Relation**: `person_wbc` → `person_wbc_service` → `person_wbc_vaccine_detail`

**JOIN pattern วัคซีน WBC (pivot per person)**:
```sql
LEFT JOIN (
  SELECT
    pws.person_wbc_id,
    MIN(CASE WHEN pvd.wbc_vaccine_id = 1  THEN pws.service_date END) AS bcg,
    MIN(CASE WHEN pvd.wbc_vaccine_id = 26 THEN pws.service_date END) AS ipv1
    -- เพิ่ม wbc_vaccine_id ตามต้องการ
  FROM person_wbc_service pws
  JOIN person_wbc_vaccine_detail pvd ON pvd.person_wbc_service_id = pws.person_wbc_service_id
  WHERE pvd.wbc_vaccine_id IN (1, 26)
  GROUP BY pws.person_wbc_id
) wv ON wv.person_wbc_id = pw.person_wbc_id
```

**wbc_vaccine_id ที่ใช้บ่อย** (ดู mapping ครบ: `knowledge/vaccine_wbc_0_1yr_mapping.md`):
| ID | วัคซีน | ID | วัคซีน |
|---|---|---|---|
| 1 | BCG | 5/6/7 | DTP 1/2/3 (แยก) |
| 2 | HBV1 | 13/14/15 | DTP-HBV 1/2/3 |
| 8 | OPV1 | **22/23/24** | **DTP-HBV-Hib (Penta) 1/2/3** |
| 26 | IPV1 | 17/18 | Rotarix 1/2 |
| 9 | OPV2 | 19/20/21 | RotaSiil 1/2/3 |
| 27 | IPV2 | 11 | MMR1 |
| 10 | OPV3 | | |

**⚠️ โรงพยาบาลนี้ใช้ Penta (wbc_vaccine_id=22/23/24) ไม่ใช่ DTP แยก** — ตรวจ DTP3 ครบต้องรวม `wbc_vaccine_id IN (7, 15, 24)` เสมอ

**person_vaccine_id ที่ใช้บ่อย** (elsewhere):
| ID | วัคซีน | ID | วัคซีน |
|---|---|---|---|
| 1 | BCG | 69/70/71 | Hib 1/2/3 |
| 11 | HBV1 | 53 | Rotarix dose 1 |
| 19 | OPV1 | 54 | Rotarix dose 2 |
| 114 | IPV1 | 55/56/57 | RotaSiil dose 1/2/3 |
| 20 | OPV2 | 18 | MMR1 |
| 115 | IPV2 | 21 | OPV3 |

---

## 3. ตาราง EPI / บัญชี 4 (วัคซีนเด็ก 1-5 ปี)

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `person_epi` | `person_epi_id` | `person_id`, `discharge`, `vaccine_dtp4_date`, `vaccine_opv4_date`, `vaccine_mmr2_date`, `vaccine_je1_lived_date`, `vaccine_je2_lived_date`, `vaccine_dtp5_date`, `vaccine_opv5_date` |
| `person_epi_vaccine` | `person_epi_vaccine_id` | `person_epi_id`, `vaccine_date` |
| `person_epi_vaccine_list` | `person_epi_vaccine_list_id` | `person_epi_vaccine_id`, `epi_vaccine_id` |
| `epi_vaccine` | `epi_vaccine_id` | `epi_vaccine_name`, `age_min`, `age_max` |

**epi_vaccine_id ที่ใช้บ่อย**:
| ID | ชื่อ | age_min (เดือน) |
|---|---|---|
| 9 | LAJE1 | 12 |
| 1 | DTP4 | 18 |
| 2 | OPV4 | 18 |
| 8 | MMR2 | 30 |
| 10 | LAJE2 | 30 |
| 6 | DTP5 | 48 |
| 7 | OPV5 | 48 |

**ข้อสำคัญ**:
- `person_epi` มี date column สำเร็จรูปทุกตัว — ไม่ต้อง pivot จาก `person_epi_vaccine_list` ในส่วนใหญ่
- ใช้ `vaccine_je1_lived_date` / `vaccine_je2_lived_date` (LAJE = Live Attenuated) ไม่ใช่ `vaccine_je1_date` — มีข้อมูลมากกว่า 10×
- filter active: `(pe.discharge <> 'Y' OR pe.discharge IS NULL)`
- age filter: `TIMESTAMPDIFF(MONTH, pt.birthday, CURDATE()) BETWEEN 12 AND 71`

### F43 EPI — VACCINETYPE source
**⚠️ VACCINETYPE ต้องใช้ `export_vaccine_code` เสมอ — ห้ามใช้ numeric ID (wbc_vaccine_id)**

| source | VACCINETYPE join |
|---|---|
| `ovst_vaccine` (OPD) | `person_vaccine.export_vaccine_code` via `ovst_vaccine.person_vaccine_id` |
| `person_wbc_vaccine_detail` (WBC) | `wbc_vaccine.export_vaccine_code` via `pvd.wbc_vaccine_id` |
| `person_epi_vaccine_list` (EPI) | `epi_vaccine.export_vaccine_code` via `pevl.epi_vaccine_id` |
| `village_student_vaccine_list` (school) | `student_vaccine.export_vaccine_code` via `vsvl.student_vaccine_id` |

**F43 EPI filter**:
- OPD source: `ovst.vstdate BETWEEN DATE_FORMAT(NOW(),'%Y-%m-01') AND LAST_DAY(NOW())`
- School source: `village_student.last_update BETWEEN DATE_FORMAT(NOW(),'%Y-%m-01') AND LAST_DAY(NOW())` (ดึงประวัติ dose ทุก dose ของเด็กที่ last_update ใน current month)

**⚠️ WBC records ทั้งหมดใน current month มี vn และปรากฏใน `ovst_vaccine` ด้วย** → ใช้ `ovst_vaccine` เป็น single source สำหรับ OPD ได้เลย ไม่ต้อง UNION person_wbc_service แยก

**JOIN pattern บัญชี 4**:
```sql
SELECT pe.vaccine_dtp4_date AS DTP4, pe.vaccine_opv4_date AS OPV4,
       pe.vaccine_mmr2_date AS MMR2,
       pe.vaccine_je1_lived_date AS LAJE1, pe.vaccine_je2_lived_date AS LAJE2,
       pe.vaccine_dtp5_date AS DTP5, pe.vaccine_opv5_date AS OPV5
FROM person_epi pe
JOIN person p ON p.person_id = pe.person_id
JOIN patient pt ON pt.hn = p.patient_hn
WHERE p.house_regist_type_id IN (1, 3)
  AND TIMESTAMPDIFF(MONTH, pt.birthday, CURDATE()) BETWEEN 12 AND 71
  AND pt.death = 'N'
  AND (p.death = 'N' OR p.death IS NULL)
  AND (pe.discharge <> 'Y' OR pe.discharge IS NULL)
```

---

## 4. ตาราง OPD Visit

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `ovst` | `vn` | `hn`, `an`, `vstdate`, `vsttime`, `main_dep`, `cur_dep`, `last_dep`, `doctor`, `command_doctor`, `sign_doctor`, `diag_text`, `pttype` |
| `vn_stat` | `vn` | `hn`, `vstdate`, `pdx`, `dx0`–`dx5`, `op0`–`op5`, `age_y`, `age_m`, `age_d`, `pttype`, `dx_doctor`, `aid`, `lastvisit`, `lastvisit_vn` |
| `ovstdiag` | `vn` | `hn`, `vstdate`, `icd10`, `diagtype` |
| `ovst_doctor_diag` | `vn` | `diag_text`, `diag_datetime` |
| `opdscreen` | `vn` | `hn`, `vstdate`, `bps`, `bpd`, `bw`, `height`, `pulse`, `bmi`, `cc`, `hpi`, `pe`, `symptom` |
| `screen_doctor` | `vn` | `staff`, `depcode` |

**JOIN pattern Visit สมบูรณ์**:
```sql
SELECT
    o.vn, o.hn, o.vstdate, o.vsttime,
    MAX(os.cc) AS CC, MAX(os.hpi) AS Hpi, MAX(os.pe) AS PE,
    MAX(v.age_y) AS age_y,
    MAX(d.name) AS Doctor,
    MAX(k.department) AS Dept,
    GROUP_CONCAT(od.icd10 ORDER BY od.diagtype SEPARATOR ' | ') AS ICD10s,
    GROUP_CONCAT(odd.diag_text SEPARATOR ' , ') AS Dx_Text
FROM ovst o
LEFT JOIN opdscreen os ON os.vn = o.vn
LEFT JOIN vn_stat v ON v.vn = o.vn
LEFT JOIN doctor d ON d.code = o.doctor
LEFT JOIN kskdepartment k ON k.depcode = o.main_dep
LEFT JOIN ovstdiag od ON od.vn = o.vn
LEFT JOIN ovst_doctor_diag odd ON odd.vn = o.vn
WHERE o.hn = '0000001'
GROUP BY o.vn
ORDER BY o.vstdate DESC
```

---

## 5. ตาราง IPD

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `ipt` | `an` | `hn`, `vn`, `ward`, `first_ward`, `regdate`, `regtime`, `dchdate`, `dchtime`, `dchstts` (NULL=ยังอยู่), `admdoctor`, `dch_doctor`, `pttype`, `prediag` |
| `iptdiag` | `an` | `hn`, `icd10` |
| `iptadm` | `an` | `bedno`, `bedtype`, `roomno`, `move_in_bed_datetime`, `rate` |

**คนไข้ที่ยังนอนอยู่** (`dchstts IS NULL`):
```sql
SELECT w.name AS Ward, COUNT(a.hn) AS จำนวน
FROM ipt a
LEFT JOIN ward w ON w.ward = a.ward
WHERE a.dchstts IS NULL
GROUP BY a.ward
```

---

## 6. ตาราง NCD / Clinic Registration

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `clinicmember` | `hn, clinic` | `regdate`, `clinic_member_status_id`, `dchdate`, `last_bp_date`, `last_bp_bps_value`, `last_bp_bpd_value`, `last_a1c_value` |

**รหัสคลินิก NCD**:
- `001` DM | `002` HT | `003` ARV | `007` Asthma | `008` COPD | `009` Stroke | `010` MI | `011` TB | `012` จิตเวช | `017` CKD

**clinic_member_status_id**: 1=ติดตามรักษา, 2=ส่งต่อ, 3=เสียชีวิต, 4=รายใหม่, 8=ขาดการรักษา

**หากลุ่มเป้าหมาย DM/HT (3 แหล่ง UNION)**:
```sql
SELECT hn FROM ovstdiag WHERE icd10 BETWEEN 'E10' AND 'E149' AND vstdate <= '2025-09-30'
UNION
SELECT i.hn FROM iptdiag i JOIN ipt it ON it.an = i.an WHERE i.icd10 BETWEEN 'E10' AND 'E149' AND it.dchdate <= '2025-09-30'
UNION
SELECT hn FROM clinicmember WHERE clinic = '001' AND regdate <= '2025-09-30'
```

---

## 7. ตาราง Lab

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `lab_head` (lh) | `lab_order_number` | `hn`, `vn`, `order_date`, `report_date`, `report_time`, `department`, `form_name`, `confirm_report` |
| `lab_order` (lo) | `lab_order_number` | `lab_items_code`, `lab_order_result`, `confirm` |

**JOIN**: `lab_head lh JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number`

**lab_items_code ที่ใช้บ่อย**:
| Code | ชื่อ | Code | ชื่อ |
|------|------|------|------|
| 76 | FBS | 102 | Cholesterol |
| 78 | Creatinine (CR) | 103 | TG |
| 79 | Uric | 193 / 948 | HbA1c |
| 81 | K | 199 | Hct |
| 91 | HDL | 259 | Syphilis Ab |
| 92 | LDL | 269 | HBsAb |
| 99 | SGOT | 271 | HBsAg |
| 100 | SGPT | 272 | HIV screen |
| 709 | INR | 883 | eGFR |
| 930 | Urine Microalbumin | 473 | HIV Viral Load |

**Pivot Lab หลายรายการใน 1 VN**:
```sql
SELECT
    lh.hn, lh.vn, lh.order_date,
    MAX(CASE WHEN lo.lab_items_code = 76  THEN lo.lab_order_result ELSE '-' END) AS FBS,
    MAX(CASE WHEN lo.lab_items_code = 948 THEN lo.lab_order_result ELSE '-' END) AS HbA1c,
    MAX(CASE WHEN lo.lab_items_code = 78  THEN lo.lab_order_result ELSE '-' END) AS CR,
    MAX(CASE WHEN lo.lab_items_code = 883 THEN lo.lab_order_result ELSE '-' END) AS eGFR
FROM lab_head lh
JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
WHERE lh.order_date BETWEEN '2025-10-01' AND '2026-09-30'
GROUP BY lh.vn
```

**ผล Lab ล่าสุด (1 ค่าต่อ HN)**:
```sql
-- ใช้ GROUP_CONCAT + SUBSTRING_INDEX เพื่อดึงค่าล่าสุด
SELECT
    hn,
    CAST(SUBSTRING_INDEX(GROUP_CONCAT(lab_order_result ORDER BY report_date DESC), ',', 1) AS DECIMAL(10,2)) AS latest_value
FROM lab_head lh
JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
WHERE lo.lab_items_code IN (193, 948)
  AND lo.lab_order_result REGEXP '^[0-9]'   -- กรองเฉพาะตัวเลข
GROUP BY hn
```

**CKD Stage จาก eGFR**:
```sql
CASE
    WHEN egfr >= 90 THEN 'Stage 1'
    WHEN egfr >= 60 THEN 'Stage 2'
    WHEN egfr >= 45 THEN 'Stage 3a'
    WHEN egfr >= 30 THEN 'Stage 3b'
    WHEN egfr >= 15 THEN 'Stage 4'
    WHEN egfr < 15  THEN 'Stage 5'
    ELSE 'Unknown'
END
```

---

## 8. ตาราง ยา / Pharmacy

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `opitemrece` | `vn, icode` | `hn`, `vstdate`, `rxdate`, `icode`, `qty`, `sum_price`, `unitprice`, `drugusage`, `an`, `doctor` |
| `drugitems` | `icode` | `did`, `name`, `strength`, `units`, `unitcost`, `unitprice`, `tmt_tp_code`, `istatus` |
| `drugusage` | `drugusage` | `shortlist`, `status` |

**JOIN**: `opitemrece o JOIN drugitems d ON d.icode = o.icode`

**สรุปการใช้ยา**:
```sql
SELECT d.name, d.strength, COUNT(*) AS ครั้งที่จ่าย, SUM(o.qty) AS จำนวนรวม,
       (SUM(o.qty) * d.unitcost) AS ต้นทุนรวม, SUM(o.sum_price) AS มูลค่ารวม
FROM opitemrece o
JOIN drugitems d ON d.icode = o.icode
WHERE o.rxdate BETWEEN '2025-10-01' AND '2026-09-30'
GROUP BY o.icode
```

**ตรวจสอบว่า visit มียาหรือไม่**:
```sql
IF(COUNT(op.icode) = 0, 'ไม่มียา', 'มียา') AS status
-- หรือ EXISTS สำหรับ icode เฉพาะ
CASE WHEN EXISTS (SELECT 1 FROM opitemrece oi WHERE oi.vn = o.vn AND oi.icode = 'XXXX') THEN 'Y' ELSE 'N' END
```

---

## 9. ตาราง นัดหมาย

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `oapp` | `oapp_id` | `hn`, `vn`, `vstdate`, `nextdate`, `nexttime`, `clinic`, `depcode`, `spclty`, `note`, `note1`, `patient_visit`, `visit_vn`, `lab_list_text`, `doctor` |

**ตรวจสอบนัดในวัน visit (LEFT JOIN)**:
```sql
LEFT JOIN oapp oa
  ON oa.hn = o.hn
  AND oa.nextdate = o.vstdate          -- จับเฉพาะนัดตรงวัน
  AND (oa.clinic IN ('015','002') OR oa.depcode = '033')
-- oa.nextdate IS NULL = ไม่มีนัดวันนั้น
```

**คนมา NCD แต่ไม่มีนัด** (NOT EXISTS):
```sql
AND NOT EXISTS (
    SELECT 1 FROM oapp a
    WHERE a.hn = o.hn
      AND a.nextdate = o.vstdate
      AND (a.clinic IN ('015','002') OR a.depcode = '033')
)
```

---

## 10. ตาราง Lookup / Reference

| Table | Key | ใช้สำหรับ |
|-------|-----|-----------|
| `kskdepartment` | `depcode` | ชื่อแผนก (`department`) |
| `doctor` | `code` | ชื่อแพทย์ (`name`) |
| `clinic` | `clinic` | ชื่อคลินิก (`name`) |
| `opduser` | `loginname` | ชื่อผู้ใช้ (`name`) |
| `ward` | `ward` | ชื่อวอร์ด (`name`) |
| `pttype` | `pttype` | ชื่อสิทธิ์ (`name`, `hipdata_code`) |
| `bedtype` | `bedtype` | ชนิดเตียง (`name`) |

**รหัสแผนก NCD ที่ใช้บ่อย**: `033`=NCD คลินิกดอกลำดวน, `047`=NCD PCU, `009`=ส่งเสริม/ANC, `060`=check-up

---

## 11. ตาราง PP / Preventive

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `pp_special` | `vn` | `hn`, `pp_special_type_id`, `entry_datetime`, `pp_special_service_place_type_id` |
| `pp_special_type` | `pp_special_type_id` | `pp_special_code`, `pp_special_type_name` |

**⚠️ filter ด้วย `hn` + `entry_datetime` — ไม่ใช่ `person_id` หรือ `service_date`**

**รหัส pp_special_type_id ที่ใช้บ่อย**:
| range | ความหมาย |
|---|---|
| 2-10 | คัดกรองมะเร็งเต้านม (1B0030-1B0039) หญิง 30-70 ปี |
| 21-25 | 9Q (ซึมเศร้า follow-up) |
| 33-34 | 2Q ผู้สูงอายุ |
| 73-76 | คัดกรองหกล้มผู้สูงอายุ (1B1200-1B1209) |
| 233, 236 | PAP smear ปกติ/ผิดปกติ (1B30/1B40) มะเร็งปากมดลูก |
| 245-251 | สูบบุหรี่ปัจจุบัน |
| 252 | เลิกบุหรี่แล้ว |
| 253 | ไม่เคยสูบบุหรี่ |
| 254-256 | บำบัดเลิกบุหรี่ (Brief Advice / Counseling / +Medicine) |
| 283-313 | HPV DNA test (1B0046) มะเร็งปากมดลูก |
| 335-337 | 2Q ทั่วไป |
| 336 | 2Q ผิดปกติ (ซึมเศร้า) |

## 11b. ตาราง MCH / อนามัยแม่และเด็ก

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `person_anc` | `person_anc_id` | `person_id`, `labor_date`, `service_count`, `alive_child_count`, `dead_child_count` |
| `person_wbc_nutrition` | `person_wbc_id, nutrition_date` | `age_y`, `age_m`, `body_weight`, `person_nutrition_food_type_id`, `person_nutrition_childdevelop_type_id` |
| `depression_screen` | `vn` | `screen_datetime` — 2Q screening record (JOIN ovst ON vn) |

**person_nutrition_food_type_id**: 1 = นมแม่อย่างเดียว
**person_nutrition_childdevelop_type_id IS NOT NULL** = ผ่านการประเมินพัฒนาการ (TEDA4I)

## 11c. ตาราง ทันตกรรม

| Table | Key | คอลัมน์สำคัญ |
|-------|-----|--------------|
| `dental_care` | `vn` | `dental_care_type_id`, `need_fluoride`, `need_sealant`, `dental_care_nprosthesis_id` |

**dental_care_type_id**: 2=เด็กก่อนวัยเรียน 0-5ปี, 3=เด็กวัยเรียน 6-12ปี, 4=ผู้สูงอายุ
**dental_care_nprosthesis_id**: 1=ฟันเทียมทั้งปาก, 2=ฟันเทียมบน, 3=ฟันเทียมล่าง, 4=ไม่ต้องใส่
**need_fluoride**: 'Y' = เคลือบฟลูออไรด์ | **need_sealant**: > 0 = เคลือบหลุมร่องฟัน

---

## 12. Query Patterns ที่ใช้บ่อย

### A. หา NCD/Chronic ที่มาคลินิก (ใช้ screen_doctor)
```sql
JOIN screen_doctor sd ON sd.vn = o.vn
  AND (sd.depcode = '033'
       OR sd.staff IN ('noi','duang','kumrai','jeab','coolnurse','haha'))
```

### B. Pivot ยืนยันว่า visit มี ICD10 ใดบ้าง (EXISTS)
```sql
CASE WHEN EXISTS (
    SELECT 1 FROM ovstdiag o2
    WHERE o2.vn = lh.vn AND o2.icd10 BETWEEN 'E100' AND 'E149'
) THEN 'Y' ELSE 'N' END AS DM
```

### C. Revisit ภายใน 48 ชั่วโมง (Self-JOIN)
```sql
FROM ovst o1
JOIN ovst o2 ON o1.hn = o2.hn AND o2.vn > o1.vn
WHERE TIMESTAMPDIFF(HOUR,
    CONCAT(o1.vstdate,' ',o1.vsttime),
    CONCAT(o2.vstdate,' ',o2.vsttime)) BETWEEN 1 AND 48
AND o2.vn = (SELECT MIN(v3.vn) FROM ovst v3 WHERE v3.hn = o1.hn AND v3.vn > o1.vn)
```

### D. ICD10 รวมต่อ VN (GROUP_CONCAT)
```sql
SELECT od.vn,
    GROUP_CONCAT(od.icd10 ORDER BY od.diagtype SEPARATOR ' | ') AS icd10s
FROM ovstdiag od
WHERE od.vstdate BETWEEN '2026-01-01' AND '2026-06-30'
GROUP BY od.vn
```

### E. จำนวน admit เฉลี่ยต่อวัน
```sql
SELECT
    DATE_FORMAT(regdate, '%Y-%m') AS ReportMonth,
    COUNT(an) AS AdmitCount,
    FORMAT(COUNT(an) / DAY(LAST_DAY(regdate)), 2) AS AvgPerDay
FROM ipt
WHERE regdate BETWEEN '2025-10-01' AND '2026-09-30'
GROUP BY ReportMonth
ORDER BY ReportMonth
```

### F. clinicmember + ผล BP (HT control)
```sql
SELECT cm.hn, cm.last_bp_bps_value AS SBP, cm.last_bp_bpd_value AS DBP
FROM clinicmember cm
WHERE cm.clinic = '002'
  AND cm.last_bp_date BETWEEN '2025-10-01' AND '2026-09-30'
  AND cm.last_bp_bps_value BETWEEN 50 AND 139
  AND cm.last_bp_bpd_value BETWEEN 50 AND 89
```

### G. workload แพทย์ (ผ่าน opitemrece)
```sql
SELECT doctor, COUNT(*) AS CountPt
FROM (
    SELECT vn, doctor FROM opitemrece
    WHERE vstdate = '2026-06-17'
    GROUP BY vn
) AS sub
GROUP BY doctor
ORDER BY CountPt DESC
```

### H. ชื่อผู้ป่วย (CONCAT standard)
```sql
CONCAT(p.pname, p.fname, ' ', p.lname) AS ptname
```

### I. อายุจาก birthday
```sql
TIMESTAMPDIFF(YEAR, pt.birthday, CURDATE()) AS age
-- หรือใช้จาก vn_stat: v.age_y, v.age_m, v.age_d
```

### M. หาคนไข้ที่มีสัญญาณ DM แต่ไม่อยู่ในทะเบียน (unregistered DM detection)
- scope lab/drug **เฉพาะ vn นั้น** ด้วย `lh.vn = o.vn` / `op.vn = o.vn` — ห้ามใช้ `hn` เพราะจะดึงประวัติทั้งหมด
- "ไม่อยู่ในทะเบียน" = `NOT EXISTS (SELECT 1 FROM clinicmember cm WHERE cm.hn = o.hn AND cm.clinic = '001')` — **ไม่ต้องกรอง dchdate**
- กรองยาด้วย `d.istatus = 'Y'` เสมอ เพื่อไม่ให้ยาเลิกใช้ trigger flag
- ดู `sql/dm_unregistered_today.sql` เป็น reference

---

## 13. ข้อควรระวัง

1. **lab_order_result เป็น string** — กรองตัวเลขด้วย `REGEXP '^[0-9]'` ก่อน CAST
2. **vn ไม่ unique ใน ovst vs oapp** — JOIN นัดต้องใช้ `nextdate = vstdate` ไม่ใช่แค่ `hn`
3. **clinicmember.dchdate** — ถ้าไม่ NULL = ถูกจำหน่ายออกจากทะเบียนแล้ว แต่ **"ไม่อยู่ในทะเบียน" หมายถึงไม่มีแถวเลย** — อย่าใส่ `dchdate IS NULL` เพราะคนที่เคยขึ้นทะเบียนแล้ว discharge ก็ยังถือว่า "เคยลงทะเบียน"
4. **patient vs person** — `patient` = เวชระเบียน (hn), `person` = ประชากร (cid); บางคนมี person หลายแถวต่อ 1 hn
5. **thaiaddress** — join ผ่าน `vn_stat.aid` หรือ `person.house_id` ไม่ใช่ `patient.tmbpart`
6. **diagtype ใน ovstdiag** — 1=PDx, 2=SDx, 5=Complication; กรองเฉพาะ PDx ด้วย `AND diagtype = '1'`
7. **opitemrece icode LIKE '30%'** = ค่าบริการ (ไม่ใช่ยา) — ใช้ `AND icode NOT LIKE '30%'` เพื่อกรองเฉพาะยา
8. **MariaDB 10.1.19** — ไม่รองรับ CTE (`WITH`) และ Window Functions ใช้ derived table ใน FROM แทนเสมอ
9. **Correlated subquery ×N แถว = ช้ามาก** — ใช้ pre-aggregate derived table JOIN แทน (ดูตัวอย่างใน Pattern J)
10. **opitemrece เป็น table ใหญ่** — กรองด้วย `icode IN (...)` เฉพาะรายการที่ต้องการ อย่าใช้ `NOT LIKE '30%'` ถ้าต้องการความเร็ว
11. **opitemrece ไม่มี date index ที่ดี** — กรองวันที่ผ่าน `ovst.vstdate` (JOIN ovst ON ovst.vn = o.vn) ดีกว่าใช้ `o.rxdate` โดยตรงในบาง version; ตรวจสอบ query plan ก่อนใช้ production

---

## 14. Performance Pattern — Derived Table แทน Correlated Subquery

### J. Pre-aggregate แทน Correlated Subquery (MariaDB 10.1 compatible)

**อย่าทำ (ช้า — รัน subquery ×N ครั้ง):**
```sql
SELECT pt.hn,
    (SELECT MAX(o.vstdate) FROM ovst o WHERE o.hn = pt.hn) AS last_visit,
    (SELECT MIN(od.vstdate) FROM ovstdiag od WHERE od.hn = pt.hn AND od.icd10 BETWEEN 'I10' AND 'I15') AS first_ht
FROM patient pt
```

**ทำแบบนี้แทน (เร็ว — scan ครั้งเดียว):**
```sql
SELECT pt.hn, lv.last_visit, ht.first_ht
FROM patient pt
LEFT JOIN (
    SELECT hn, MAX(vstdate) AS last_visit FROM ovst GROUP BY hn
) AS lv ON lv.hn = pt.hn
LEFT JOIN (
    SELECT hn, MIN(vstdate) AS first_ht
    FROM ovstdiag WHERE icd10 BETWEEN 'I10' AND 'I15'
    GROUP BY hn
) AS ht ON ht.hn = pt.hn
```

### K. source_group HT (น้ำหนักหลักฐาน — OPD/IPD/Clinic)

```sql
CASE
    WHEN (opd.hn IS NOT NULL) AND (ipd.hn IS NOT NULL) AND (cln.hn IS NOT NULL) THEN '1. OPD+IPD+Clinic'
    WHEN (opd.hn IS NOT NULL) AND (ipd.hn IS NOT NULL) AND (cln.hn IS NULL)     THEN '2. OPD+IPD'
    WHEN (opd.hn IS NOT NULL) AND (ipd.hn IS NULL)    AND (cln.hn IS NOT NULL)  THEN '3. OPD+Clinic'
    WHEN (opd.hn IS NULL)    AND (ipd.hn IS NOT NULL) AND (cln.hn IS NOT NULL)  THEN '4. IPD+Clinic'
    WHEN (opd.hn IS NOT NULL) AND (ipd.hn IS NULL)    AND (cln.hn IS NULL)      THEN '5. OPD Only'
    WHEN (opd.hn IS NULL)    AND (ipd.hn IS NOT NULL) AND (cln.hn IS NULL)      THEN '6. IPD Only'
    WHEN (opd.hn IS NULL)    AND (ipd.hn IS NULL)     AND (cln.hn IS NOT NULL)  THEN '7. Clinic Only'
END AS source_group
-- ใช้ explicit 3-flag CHECK ทุก condition → ไม่มี ambiguity, ไม่ต้องการ ELSE
-- (WHERE กรอง all-NULL ออกแล้ว ทำให้ ELSE dead code)
```

### L. ยา HT icode reference (opitemrece)

```
Amlodipine : 1481400, 1440105, 1481366
Atenolol   : 1481175, 1481403, 1440601, 1000040
Carvedilol : 1590010, 1460529, 1460530
Doxazosin  : 1481307, 1580018, 1036001
Enalapril  : 1481003, 1481161, 1481395, 1000122, 1460151
HCTZ       : 1481025, 1460179
Hydralazine: 1481202, 1580002, 1460193, 1481404
Losartan   : 1481344, 1481453
Manidipine : 1610010
Methyldopa : 1460012, 1460013, 1481062
Metoprolol : 1560004
Moduretic  : 1481067, 1450503
Nifedipine : 1481076, 1481077, 1481173, 1000206, 1431201, 1000204, 1000205
Propranolol: 1000255, 1000254, 1421102
```
