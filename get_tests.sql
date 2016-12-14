SET SEARCH_PATH TO mimiciii;

WITH sepsis_statins AS (
 WITH statins_max AS (
  SELECT statin, suppress, hadm_id, row_id, heart AS peripheral_vascular_disease,
  ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY chartdate) AS rn
  FROM statins
 )
 SELECT a.angus, a.mech_vent, s.*
 FROM statins_max s INNER JOIN angus_sepsis a USING(hadm_id)
 WHERE rn = 1 AND a.angus = 1 AND s.suppress = 0
)
SELECT hadm_id, l.itemid, l.charttime, l.valuenum, l.valueuom 
FROM sepsis_statins INNER JOIN labevents l USING(hadm_id)
WHERE l.itemid IN (50861, 50878, 50813, 50912, 51003, 51002)