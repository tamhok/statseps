SET SEARCH_PATH TO mimiciii;
WITH basic_set AS (
WITH sofa_max AS (
	SELECT hadm_id, subject_id, MAX(sofa) as sofa, 
	MAX(respiration) as respiration, 
	MAX(coagulation) as coagulation, 
	MAX(liver) as liver, 
	MAX(cardiovascular) as cardiovascular,
	MAX(cns) as cns,
	MAX(renal) as renal
	FROM sofa GROUP BY hadm_id, subject_id
), 
hw AS(
 WITH weights AS (
  SELECT hadm_id, i.subject_id, AVG(weight_first) as weight
  FROM heightweight INNER JOIN icustays i USING (icustay_id) 
  WHERE i.first_careunit != 'NICU' 
  GROUP BY hadm_id, i.subject_id
 ), 
 heights AS (
  SELECT subject_id, AVG(height_first) as height FROM heightweight GROUP BY subject_id
 )
 SELECT * FROM weights INNER JOIN heights USING(subject_id)
), 
care_unit AS (
 WITH care_first AS (
   SELECT subject_id, hadm_id, first_careunit AS service, 
   ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
   FROM icustays
 )
 SELECT subject_id, hadm_id, service
 FROM care_first WHERE rn = 1
),
sepsis_statins AS (
 WITH statins_max AS (
  SELECT statin, suppress, hadm_id, row_id, heart AS peripheral_vascular_disease,
  ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY chartdate) AS rn
  FROM statins
 )
 SELECT a.angus, a.mech_vent, s.*
 FROM statins_max s INNER JOIN angus_sepsis a USING(hadm_id)
 WHERE rn = 1 AND a.angus = 1 AND s.suppress = 0
 )

SELECT a.row_id, a.angus, a.mech_vent, v.vaso_flg, c.service, a.statin, a.suppress, date_part('year', age(d.admittime, p.dob)) AS age, d.admittime, p.gender, d.ethnicity, h.height, h.weight, date_part('day', p.dod - d.admittime) AS death, d.hospital_expire_flag, s.sofa, s.respiration, s.coagulation, s.liver, s.cardiovascular, s.cns, s.renal,
e.*, a.peripheral_vascular_disease
FROM sepsis_statins a 
INNER JOIN sofa_max s USING(hadm_id)
INNER JOIN elixhauser_ahrq e USING(hadm_id, subject_id)
INNER JOIN admissions d USING(hadm_id, subject_id)
LEFT JOIN hw h USING(hadm_id, subject_id)
INNER JOIN patients p USING(subject_id)
INNER JOIN sepsis_vaso_flg v USING(hadm_id, subject_id)
INNER JOIN care_unit c USING(hadm_id, subject_id)
)

SELECT * FROM basic_set