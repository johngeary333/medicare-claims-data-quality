# Data dictionary and analytic grain

## Source files

| Source | Source grain | Fields used | Purpose |
| --- | --- | --- | --- |
| 2008 Beneficiary Summary | One synthetic beneficiary per row | `DESYNPUF_ID`, `BENE_BIRTH_DT`, `BENE_SEX_IDENT_CD`, `BENE_RACE_CD` | Linking and demographic context |
| 2008–2010 Inpatient Claims | Claim-segment row | `DESYNPUF_ID`, `CLM_ID`, `SEGMENT`, `CLM_ADMSN_DT`, `NCH_BENE_DSCHRG_DT`, `CLM_PMT_AMT`, `CLM_UTLZTN_DAY_CNT`, `ICD9_DGNS_CD_1` | Claims and utilization |

## Processing rules

- Join on `DESYNPUF_ID`, as documented by CMS. This links the 2008 beneficiary snapshot only to claims with **2008 admission date**.
- `CLM_ID` can appear on more than one claim segment. Use `(CLM_ID, SEGMENT)` for duplicate-identity checks; do **not** remove legitimate segments.
- Parse date values from `YYYYMMDD` strings/numbers. An inpatient record can have admission in 2007 even when the claims file says 2008–2010.
- Compute age at admission from the *synthetic* date of birth. Age groups can change for one beneficiary across admissions, so distinct beneficiary counts **must not be summed** across groups to obtain a unique total.
- `CLM_UTLZTN_DAY_CNT` is used as recorded utilization days. `elapsed_nights` is a diagnostic cross-check rather than a substitute for utilization days.
- Preserve negative payment values in row-level data, flag them, and exclude them only from nonnegative-payment averages. Do not assume a negative payment is an error without payment context.
- Preserve missing days; no imputation or record deletion. For means, exclude missing or negative values only.
- 2008 diagnoses use **ICD-9**, not ICD-10. This project does not attempt to identify or validate healthcare-associated infections.

## Scope and bias

CMS states that DE-SynPUF is released for training, development, and exploration and has limited inferential utility for real populations. The result tables demonstrate methodology, not a generalizable clinical or financial conclusion about Medicare beneficiaries.

**Primary documentation**: [CMS Sample 1](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1) · [DE-SynPUF overview](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf) · [CMS codebook](https://www.cms.gov/files/document/de-10-codebook.pdf-0)
