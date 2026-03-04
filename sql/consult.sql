SELECT 
	hn AS 'HN' ,
	vn AS 'VN' ,
	consult_date AS 'Date' ,
	consult_question  AS 'Q' ,
	consult_reply AS 'A'
FROM doctor_consult
WHERE
	hn = %(hn)s
ORDER BY consult_date DESC
;