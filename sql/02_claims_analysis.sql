-- Aggregate only 2008 admission-year segments; preserve all rows in underlying tables.
-- EXCLUDE negative payments solely from valid-payment averages; do NOT discard the row.
-- Recorded utilization days are used instead of treating date difference as length of stay.

-- Overview
SELECT COUNT(*) AS inpatient_segment_rows,
       COUNT(DISTINCT CLM_ID) AS distinct_claim_ids,
       COUNT(DISTINCT DESYNPUF_ID) AS distinct_beneficiaries,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_claim_payment,
       ROUND(AVG(CASE WHEN CLM_UTLZTN_DAY_CNT >= 0 THEN CLM_UTLZTN_DAY_CNT END),2) AS avg_recorded_utilization_days
FROM claims_2008;

-- By age at admission (derived using synthetic birth dates)
SELECT age_group,
       COUNT(*) AS segment_rows,
       COUNT(DISTINCT DESYNPUF_ID) AS beneficiaries,
       ROUND(AVG(CASE WHEN CLM_UTLZTN_DAY_CNT >= 0 THEN CLM_UTLZTN_DAY_CNT END),2) AS avg_utilization_days,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_payment
FROM claims_2008
GROUP BY age_group
ORDER BY CASE age_group WHEN 'Under 65' THEN 1 WHEN '65-74' THEN 2
                        WHEN '75-84' THEN 3 WHEN '85+' THEN 4 ELSE 5 END;

-- By month of admission (not generalizable to real patients)
SELECT substr(admission_date,1,7) AS admission_month,
       COUNT(*) AS segment_rows,
       COUNT(DISTINCT DESYNPUF_ID) AS beneficiaries,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_payment
FROM claims_2008 WHERE admission_date IS NOT NULL
GROUP BY admission_month ORDER BY admission_month;

-- Most frequent synthetic principal diagnosis codes (ICD-9 era, not ICD-10)
SELECT ICD9_DGNS_CD_1 AS principal_icd9_code, COUNT(*) AS segment_rows
FROM claims_2008
WHERE ICD9_DGNS_CD_1 IS NOT NULL AND ICD9_DGNS_CD_1 <> ''
GROUP BY ICD9_DGNS_CD_1
ORDER BY segment_rows DESC, principal_icd9_code ASC LIMIT 10;
