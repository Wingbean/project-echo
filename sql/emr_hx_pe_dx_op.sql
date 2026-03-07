-- แสดง Hx Pe Dxtext
SELECT
o.vn AS 'VN'
,MAX(o.hn) AS 'HN' 
,MAX(o.an) AS 'AN' 
,MAX(o.vstdate) AS 'VstDate'
,MAX(o.vsttime) AS 'VstTime'
,MAX(v.pttype) AS 'Rights'
,MAX(k.department ) AS 'Dept'
,MAX(ou.name) AS 'HxTaker'
,MAX(d.name) AS 'Dr'
,MAX(os.cc) AS 'CC' 
,MAX(os.hpi) AS 'Hpi' 
,MAX(os.pe) AS 'PE'
,MAX(od.diag_text) AS 'Dx_Text'
,MAX(v.pdx) AS 'PDx' 
,MAX(v.dx1) AS 'Dx1' 
,MAX(v.dx2) AS 'Dx2' 
,MAX(v.dx3) AS 'Dx3' 
,MAX(v.op0) AS 'op0' ,MAX(v.op1) AS 'op1' ,MAX(v.op2) AS 'op2' ,MAX(v.op3) AS 'op3' ,MAX(v.op4) AS 'op4' ,MAX(v.op5) AS 'op5'
FROM ovst o 
LEFT OUTER JOIN opdscreen os ON o.vn = os.vn
LEFT OUTER JOIN doctor d  ON o.doctor = d.code
LEFT OUTER JOIN screen_doctor sd ON sd.vn = o.vn
LEFT OUTER JOIN opduser ou ON ou.loginname = sd.staff
LEFT OUTER JOIN vn_stat v ON v.vn = o.vn
LEFT OUTER JOIN ovst_doctor_diag od ON od.vn = o.vn
LEFT OUTER JOIN kskdepartment k  ON k.depcode = o.main_dep
WHERE o.hn = %(hn)s
GROUP BY o.vn
ORDER BY MAX(o.vstdate) DESC, MAX(o.vsttime) DESC, MAX(o.doctor)
;

-- SELECT
--         opi.vn,
--         opi.vsttime AS 'vsttime' ,
--         opi.rxdate AS 'rxdate' ,
--         opi.rxtime AS 'rx_time' ,
--         opi.icode AS 'icode' ,
--         di.name AS 'dName' ,
--         opi.drugusage AS 'usage' ,
--         du.shortlist AS 'use' ,
--         opi.qty AS 'qty'
--     FROM opitemrece opi
--     LEFT JOIN drugusage du ON opi.drugusage = du.drugusage AND du.status = 'Y'
--     LEFT JOIN drugitems di ON opi.icode = di.icode 
--     WHERE 
--     	opi.drugusage <> '' AND
--     	opi.hn = '0012000'
-- ;