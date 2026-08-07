SELECT
  omax.hn AS 'HN',
  p.sex AS 'Sex',
  TIMESTAMPDIFF(YEAR, p.birthday, ops_latest.vstdate) AS 'Age',
  ops_latest.vstdate AS 'lastDate',
  a.RegDate AS 'RegDate',
  CASE WHEN a.DM > 0 THEN 'Y' ELSE 'N' END AS 'DM',
  CASE WHEN a.HT > 0 THEN 'Y' ELSE 'N' END AS 'HT',
  ops_latest.cholesterol AS 'TC_ops',
  ops_latest.waist AS 'waist_ops',
  ops_latest.bps AS 'bps_ops',
  ops_latest.height AS 'height_ops',
  ops_latest.smoking_type_id AS 'Smoke',
  CONCAT(p.pname,p.fname,' ',p.lname) AS 'Name'
FROM
(
  SELECT o.hn, MAX(o.vn) AS lastVN , o.screen_dep
  FROM opdscreen o
  WHERE o.vstdate = %(startdate)s
  GROUP BY o.hn
) omax
LEFT OUTER JOIN
(
  SELECT
      cm.hn AS HN,
      MIN(cm.regdate) AS RegDate,
      SUM(cm.clinic = '001') AS DM,
      SUM(cm.clinic = '002') AS HT
  FROM clinicmember cm
  WHERE cm.clinic IN ('001','002')
    AND cm.hn <> '' AND cm.hn IS NOT NULL
  GROUP BY cm.hn
) a
  ON a.hn = omax.hn
INNER JOIN opdscreen ops_latest
  ON ops_latest.vn = omax.lastVN
LEFT JOIN patient p ON p.hn = omax.hn
WHERE TIMESTAMPDIFF(YEAR, p.birthday, ops_latest.vstdate) > 25
ORDER BY a.RegDate;
