SELECT
    opi.vn,
    opi.vsttime AS 'vsttime',
    opi.rxdate AS 'rxdate',
    opi.rxtime AS 'rx_time',
    opi.icode AS 'icode',
    di.name AS 'dName',
    opi.drugusage AS 'usage',
    du.shortlist AS 'use',
    opi.qty AS 'qty'
FROM opitemrece opi
LEFT JOIN drugusage du ON opi.drugusage = du.drugusage AND du.status = 'Y'
LEFT JOIN drugitems di ON opi.icode = di.icode 
WHERE 
    opi.drugusage <> '' AND
    opi.hn = %(hn)s
ORDER BY opi.vn DESC, opi.rxdate DESC, opi.rxtime DESC;
