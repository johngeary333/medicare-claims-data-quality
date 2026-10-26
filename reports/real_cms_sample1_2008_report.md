# Medicare Claims Data Quality & Utilization — CMS Synthetic Sample 1

*Generated from the two publicly released CMS Sample 1 CSVs supplied for this project. Synthetic records; not demo values. Analysis date: 2026-10-26.*

## Executive summary

The source files contain **116,352** 2008 beneficiary records and **66,773** inpatient claim-segment rows covering multiple admission years. Restricting by **2008 admission date** yields **27,701** segment rows representing **27,682** distinct claim IDs and **15,864** distinct beneficiary identifiers. The record-level quality checks flag **22** negative claim-payment values and **23** missing utilization-day values. All rows are retained for auditability.

Across 2008 segments, the average **nonnegative** claim payment is **$9,323.60** and the mean **recorded utilization days** is **5.63**, computed using nonmissing, nonnegative eligible observations only. These are descriptive figures for synthetic data and are not estimates for real Medicare patients.

## Key findings and interpretation

1. **Claims have multiple levels of identification.** The 27,701 inpatient rows represent 27,682 distinct claim IDs, so analysis should not automatically treat one row as one unique claim. The `(CLM_ID, SEGMENT)` composite key has no duplicates in the 2008 cohort.
2. **Data quality exceptions should be recorded rather than silently removed.** The data have 22 negative claim payments (0.079% of 2008 rows) and 23 missing recorded utilization-day values (0.083%). Both remain in the underlying data; only ineligible values are excluded from relevant averages.
3. **Date filters need explicit definitions.** The 2008–2010 inpatient extract includes 226 records with 2007 admission dates. This project consistently defines its study cohort by admission in 2008, not the filename or claim processing year.

## 1. Source reconciliation

| dataset | rows |
| --- | --- |
| beneficiaries_2008 | 116352 |
| inpatient_claims | 66773 |
| claims_2008 | 27701 |

### Admission-year distribution (entire inpatient source)

| admission_year | claim_segment_rows |
| --- | --- |
| 2007 | 226 |
| 2008 | 27701 |
| 2009 | 25264 |
| 2010 | 13582 |

**Note:** The inpatient source contains pre-2008 admission dates as well; we explicitly filter to admission year 2008 instead of assuming every row belongs to 2008–2010 by admission.

## 2. Data quality checks (2008 admission-year subset)

| check | count | percent_of_2008_rows |
| --- | --- | --- |
| missing_keys | 0 | 0.0 |
| invalid_dates | 0 | 0.0 |
| missing_payments | 0 | 0.0 |
| negative_payments | 22 | 0.079 |
| missing_utilization_days | 23 | 0.083 |
| negative_utilization_days | 0 | 0.0 |
| unmatched_beneficiaries | 0 | 0.0 |
| invalid_ages | 0 | 0.0 |

Duplicate `(CLM_ID, SEGMENT)` groups: **0**. Different segments belonging to the same claim are retained.

## 3. Utilization and payments by beneficiary age group

| age_group | claim_segment_rows | beneficiaries | avg_recorded_utilization_days | avg_nonnegative_payment |
| --- | --- | --- | --- | --- |
| Under 65 | 5212 | 2904 | 5.84 | 9028.82 |
| 65-74 | 8625 | 5172 | 5.6 | 9553.96 |
| 75-84 | 8681 | 5045 | 5.62 | 9564.22 |
| 85+ | 5183 | 2899 | 5.49 | 8833.53 |

Age groups are based on synthetic birth dates; these statistics demonstrate query patterns only.

## 4. Monthly summary by admission date

![2008 inpatient claim-segment rows by admission month](figures/2008_monthly_admissions.svg)

| admission_month | claim_segment_rows | beneficiaries | avg_nonnegative_payment |
| --- | --- | --- | --- |
| 2008-01 | 1535 | 1373 | 9459.28 |
| 2008-02 | 1805 | 1594 | 9015.02 |
| 2008-03 | 2301 | 2077 | 9099.4 |
| 2008-04 | 2321 | 2082 | 9367.16 |
| 2008-05 | 2588 | 2270 | 9397.16 |
| 2008-06 | 2457 | 2196 | 9403.14 |
| 2008-07 | 2472 | 2236 | 9323.04 |
| 2008-08 | 2587 | 2331 | 9242.23 |
| 2008-09 | 2455 | 2258 | 9077.49 |
| 2008-10 | 2508 | 2291 | 9397.37 |
| 2008-11 | 2341 | 2161 | 9377.55 |
| 2008-12 | 2331 | 2169 | 9702.29 |

## 5. Most frequent principal ICD-9 code values

| principal_icd9_code | claim_segment_rows |
| --- | --- |
| 486 | 1047 |
| 41401 | 737 |
| V5789 | 669 |
| 4280 | 658 |
| 49121 | 656 |
| 0389 | 650 |
| 5990 | 563 |
| 41071 | 492 |
| 42731 | 486 |
| 5849 | 466 |

These are *code values* taken from the synthetic claims, not clinically validated diagnoses. Counts are claim-segment rows, not patient incidence.

### Methods and important limitations

- **Source:** CMS 2008–2010 Data Entrepreneurs’ Synthetic Public Use File (DE-SynPUF), Sample 1. These are *synthetic* CMS training/development data, not real patient claims. The data do not support population-level clinical or utilization inference.
- **Cohort:** Select claim **segments** with `CLM_ADMSN_DT` in 2008, matching the 2008 beneficiary snapshot by `DESYNPUF_ID`. Source admissions from other years are retained in the raw table but excluded from 2008 summaries.
- **Record granularity:** Row-level records are claim segments. Repeated `CLM_ID` across different `SEGMENT` values is **not** necessarily a duplicate; composite duplicates are tested by `(CLM_ID, SEGMENT)`. Counts and averages based on rows may be segment-weighted.
- **Dates and age:** SAS/Python parse `YYYYMMDD` to dates. Age at admission derives from synthetic birth dates and is for demonstration only.
- **Payment and utilization:** Negative payment amounts are flagged, kept in the dataset, and excluded from the *nonnegative-payment average* only. Missing utilization days are retained and excluded from the utilization mean. We use CMS `CLM_UTLZTN_DAY_CNT`, not a manually inferred length of stay.
- **Missing values:** No missing value is imputed. This differs intentionally from the separate infection-surveillance coursework example, where imputation was the task.
- **Coding:** Principal diagnosis values are **ICD-9**, appropriate to the 2008 synthetic claims; these should not be presented as ICD-10-CM codes or as HAI case definitions.
- **Execution provenance:** The numerical results in this report were generated by Python standard-library ingestion of the supplied **real CMS CSVs** into SQLite, followed by SQLite queries. The separate `.sas` files are provided for execution in SAS Studio; **the SAS scripts were not executed or independently validated in a SAS runtime** as part of creating this report. The import counts were previously confirmed in SAS Studio by the project owner. The numerical tables here were validated through the independent Python/SQLite workflow.

## Reproduction steps

1. Place both CMS CSVs under `data/raw/` (exact filenames listed in README).
2. Run `py scripts/build_database.py` from the repository root; this creates the local SQLite database and `claims_2008` view.
3. Run `py scripts/generate_report.py`; this regenerates this Markdown report and the aggregate CSVs in `outputs/`.
4. Independently run `sas/00_import_and_verify.sas`, `01_clean_and_quality_checks.sas`, and `02_summary_and_export.sas` in SAS Studio Online and compare the key counts and aggregates to the SQL output.

**Official sources:** [CMS Sample 1 downloads](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1) · [CMS DE-SynPUF overview](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf) · [CMS codebook](https://www.cms.gov/files/document/de-10-codebook.pdf-0)
