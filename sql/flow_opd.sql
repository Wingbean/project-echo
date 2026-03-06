SELECT
    -- ข้อมูลจากตาราง ovst และ kskdepartment
    o.vn, 
    o.hn, 
    o.an, 
    o.oqueue AS 'all_que', 
    o.main_dep_queue AS 'dep_que', 
    CONCAT(o.main_dep,' ',k1.department) AS 'main_dep', 
    -- ข้อมูลจากตาราง opdscreen
    CONCAT(s.screen_dep,' ',k4.department) AS 'screen_dep',
    CASE 
        WHEN s.cc IS NOT NULL AND s.cc <> '' THEN 'Y' 
        ELSE 'N' 
    END AS cc2,
    CASE 
        WHEN s.pe IS NOT NULL AND s.pe <> '' THEN 'Y' 
        ELSE 'N' 
    END AS pe2,
    CONCAT(o.last_dep, ' ', k2.department) AS 'last_dep',
    CONCAT(o.cur_dep, ' ', k3.department) AS 'cur_dep',
    o.vsttime,     
    o.cur_dep_time,       
    -- ข้อมูลเวลา Lab
    l.all_order_times AS 'lab_order_time',
    l.all_receive_times AS 'lab_recieve_time',
    l.all_report_times AS 'lab_report_time',
    -- ข้อมูลจากตาราง opitemrece (ที่เพิ่มเข้ามาใหม่)
    rx.vsttime_rx,
    rx.all_rxdate AS 'rx_date',
    rx.last_rx_time,
    o.rx_queue AS 'rx_que'
FROM ovst o
-- เชื่อมชื่อแผนก
LEFT JOIN kskdepartment k1 ON k1.depcode = o.main_dep
LEFT JOIN kskdepartment k2 ON k2.depcode = o.last_dep
LEFT JOIN kskdepartment k3 ON k3.depcode = o.cur_dep
-- เชื่อมข้อมูลการคัดกรอง
LEFT JOIN opdscreen s ON s.vn = o.vn
-- เชื่อมชื่อแผนกสำหรับจุดคัดกรอง (k4)
LEFT JOIN kskdepartment k4 ON k4.depcode = s.screen_dep
-- เชื่อมข้อมูลสรุปเวลา Lab ราย Visit
LEFT JOIN (
    SELECT 
        lh.vn, 
        GROUP_CONCAT(DISTINCT lh.order_time ORDER BY lh.order_time) AS all_order_times,
        GROUP_CONCAT(DISTINCT lh.receive_time ORDER BY lh.receive_time) AS all_receive_times,
        GROUP_CONCAT(DISTINCT lh.report_time ORDER BY lh.report_time) AS all_report_times
    FROM lab_head lh 
    WHERE lh.order_date = CURDATE()
    GROUP BY lh.vn
) l ON l.vn = o.vn
-- เชื่อมข้อมูลสรุปจาก opitemrece (Subquery rx)
LEFT JOIN (
    SELECT
        opi.vn,
        MIN(opi.vsttime) AS vsttime_rx,
        GROUP_CONCAT(DISTINCT opi.rxdate) AS all_rxdate,
        MAX(opi.rxtime) AS last_rx_time
    FROM opitemrece opi
    WHERE opi.vstdate = CURDATE()
    GROUP BY opi.vn
) rx ON rx.vn = o.vn
WHERE o.vstdate = CURDATE()
  AND o.hn = %(hn)s
ORDER BY o.vn DESC
;