-- CMS DE-SynPUF Sample 1; genuine 2008 beneficiary CSV and 2008-2010 inpatient CSV.
-- Run against data/processed/medicare_claims.sqlite after build_database.py.
-- Claims subset: admission year 2008; claim segments are individual rows.

-- Check 1: source file record counts.
SELECT 'beneficiaries_2008' AS dataset, COUNT(*) AS row_count FROM beneficiaries_2008
UNION ALL SELECT 'inpatient_claims', COUNT(*) FROM inpatient_claims
UNION ALL SELECT 'claims_2008', COUNT(*) FROM claims_2008;

-- Check 2: claim admission years (2007 admissions can occur in the source).
SELECT substr(CLM_ADMSN_DT,1,4) AS admission_year, COUNT(*) AS rows
FROM inpatient_claims GROUP BY 1 ORDER BY 1;

-- Check 3: flag counts; do not delete rows just because a flag is present.
SELECT COUNT(*) AS rows_2008,
       SUM(flag_missing_key) AS missing_keys,
       SUM(flag_invalid_dates) AS invalid_dates,
       SUM(flag_missing_payment) AS missing_payments,
       SUM(flag_negative_payment) AS negative_payments,
       SUM(flag_missing_utilization) AS missing_utilization_days,
       SUM(flag_negative_utilization) AS negative_utilization_days,
       SUM(flag_unmatched_beneficiary) AS unmatched_beneficiaries,
       SUM(flag_invalid_age) AS invalid_ages
FROM claims_2008;

-- Check 4: repeated claim ID vs repeated claim ID + segment.
SELECT COUNT(*) AS distinct_claim_ids
FROM (SELECT CLM_ID FROM claims_2008 WHERE CLM_ID <> '' GROUP BY CLM_ID);
SELECT COUNT(*) AS duplicated_claim_segment_groups
FROM (SELECT CLM_ID, SEGMENT, COUNT(*) AS n
      FROM claims_2008
      GROUP BY CLM_ID, SEGMENT HAVING COUNT(*) > 1);

-- Check 5: payment and utilization values are inspected, not blindly imputed.
SELECT MIN(CLM_PMT_AMT) AS min_payment,
       MAX(CLM_PMT_AMT) AS max_payment,
       MIN(CLM_UTLZTN_DAY_CNT) AS min_utilization,
       MAX(CLM_UTLZTN_DAY_CNT) AS max_utilization
FROM claims_2008;
