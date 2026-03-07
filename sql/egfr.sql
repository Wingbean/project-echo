-- eGFR
SELECT 
	lh.hn AS 'HN'
	, lh.report_date AS 'LabDate'
	, lh.report_time AS 'LabTime'
	, lo.lab_order_result AS 'result'
	,  CASE 
            WHEN lo.lab_order_result >= 90 THEN '1'
            WHEN lo.lab_order_result >= 60 THEN '2'
            WHEN lo.lab_order_result >= 45 THEN '3a'
            WHEN lo.lab_order_result >= 30 THEN '3b'
            WHEN lo.lab_order_result >= 15 THEN '4'
            WHEN lo.lab_order_result < 15  THEN '5'
            ELSE 'Unknown' 
        END AS CKD_Stage
FROM lab_head lh
INNER JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
WHERE lo.lab_items_code = 883 
--      AND lh.report_date BETWEEN '2025-10-01' AND '2026-09-30'
     AND lo.lab_order_result REGEXP '^[0-9]'
     AND lh.hn = %(hn)s
GROUP BY lh.hn, lh.report_date
ORDER BY lh.report_date DESC
;