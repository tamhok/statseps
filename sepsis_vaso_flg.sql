-- Create a table which indicates if a patient was ever on a vasopressor during their ICU stay

-- List of vasopressors used:
-- norepinephrine - 30047,30120,221906
-- epinephrine - 30044,30119,30309,221289
-- phenylephrine - 30127,30128,221749
-- vasopressin - 30051,222315
-- dopamine - 30043,30307,221662
-- Isuprel - 30046,227692

SET search_path TO mimiciii;
DROP MATERIALIZED VIEW IF EXISTS SEPSIS_VASO_FLG CASCADE;
CREATE MATERIALIZED VIEW SEPSIS_VASO_FLG as
with io_cv as
(
  select
    icustay_id, charttime, itemid, stopped, rate, amount
  from mimiciii.inputevents_cv
  where itemid in
  (
    30047,30120 -- norepinephrine
    ,30044,30119,30309 -- epinephrine
    ,30127,30128 -- phenylephrine
    ,30051 -- vasopressin
    ,30043,30307,30125 -- dopamine
    ,30046 -- isuprel
  )
  and rate is not null
  and rate > 0
)
-- select only the ITEMIDs from the inputevents_mv table related to vasopressors
, io_mv as
(
  select
    icustay_id, linkorderid, starttime, endtime
  from mimiciii.inputevents_mv io
  -- Subselect the vasopressor ITEMIDs
  where itemid in
  (
  221906 -- norepinephrine
  ,221289 -- epinephrine
  ,221749 -- phenylephrine
  ,222315 -- vasopressin
  ,221662 -- dopamine
  ,227692 -- isuprel
  )
  and rate is not null
  and rate > 0
  and statusdescription != 'Rewritten' -- only valid orders
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
select
  subject_id, hadm_id
  , max(case when coalesce(io_mv.icustay_id, io_cv.icustay_id) is not null then 1 else 0 end) as vaso_flg
from sepsis_statins ss 
inner join icustays ic using (hadm_id)
left join io_mv using(icustay_id)
left join io_cv
  on ic.icustay_id = io_cv.icustay_id
group by subject_id, hadm_id
