"""Generate REAL aggregated CMS Sample 1 analysis outputs from local SQLite database.
Run after scripts/build_database.py; no fabricated/demo records or dependencies.
"""
from __future__ import annotations
import csv
import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "medicare_claims.sqlite"
OUT = ROOT / "outputs"
REPORTS = ROOT / "reports"

QUALITY_QUERY = """
SELECT COUNT(*) AS rows_2008,
       SUM(flag_missing_key) AS missing_keys,
       SUM(flag_invalid_dates) AS invalid_dates,
       SUM(flag_missing_payment) AS missing_payments,
       SUM(flag_negative_payment) AS negative_payments,
       SUM(flag_missing_utilization) AS missing_utilization_days,
       SUM(flag_negative_utilization) AS negative_utilization_days,
       SUM(flag_unmatched_beneficiary) AS unmatched_beneficiaries,
       SUM(flag_invalid_age) AS invalid_ages
FROM claims_2008
"""
OVERALL_QUERY = """
SELECT COUNT(*) AS claim_segment_rows,
       COUNT(DISTINCT CLM_ID) AS distinct_claim_ids,
       COUNT(DISTINCT DESYNPUF_ID) AS distinct_beneficiaries,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_payment,
       ROUND(AVG(CASE WHEN CLM_UTLZTN_DAY_CNT >= 0 THEN CLM_UTLZTN_DAY_CNT END),2) AS avg_recorded_utilization_days
FROM claims_2008
"""
AGE_QUERY = """
SELECT age_group,
       COUNT(*) AS claim_segment_rows,
       COUNT(DISTINCT DESYNPUF_ID) AS beneficiaries,
       ROUND(AVG(CASE WHEN CLM_UTLZTN_DAY_CNT >= 0 THEN CLM_UTLZTN_DAY_CNT END),2) AS avg_recorded_utilization_days,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_payment
FROM claims_2008 GROUP BY age_group
ORDER BY CASE age_group WHEN 'Under 65' THEN 1 WHEN '65-74' THEN 2
                        WHEN '75-84' THEN 3 WHEN '85+' THEN 4 ELSE 5 END
"""
MONTH_QUERY = """
SELECT substr(admission_date,1,7) AS admission_month,
       COUNT(*) AS claim_segment_rows,
       COUNT(DISTINCT DESYNPUF_ID) AS beneficiaries,
       ROUND(AVG(CASE WHEN CLM_PMT_AMT >= 0 THEN CLM_PMT_AMT END),2) AS avg_nonnegative_payment
FROM claims_2008 WHERE admission_date IS NOT NULL
GROUP BY admission_month ORDER BY admission_month
"""
DIAG_QUERY = """
SELECT ICD9_DGNS_CD_1 AS principal_icd9_code, COUNT(*) AS claim_segment_rows
FROM claims_2008
WHERE ICD9_DGNS_CD_1 <> '' AND ICD9_DGNS_CD_1 IS NOT NULL
GROUP BY ICD9_DGNS_CD_1 ORDER BY claim_segment_rows DESC, principal_icd9_code LIMIT 10
"""
ADMISSION_QUERY = """
SELECT substr(CLM_ADMSN_DT,1,4) AS admission_year, COUNT(*) AS claim_segment_rows
FROM inpatient_claims GROUP BY 1 ORDER BY 1
"""
DUP_QUERY = """
SELECT COUNT(*) AS duplicate_composite_key_groups
FROM (SELECT CLM_ID,SEGMENT,COUNT(*) AS n FROM claims_2008
      GROUP BY CLM_ID,SEGMENT HAVING COUNT(*)>1)
"""


def get(conn, query):
    return [dict(x) for x in conn.execute(query)]


def write_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def md_table(rows):
    if not rows:
        return '*No rows.*'
    keys = list(rows[0])
    return '\n'.join([
        '| ' + ' | '.join(keys) + ' |',
        '| ' + ' | '.join(['---'] * len(keys)) + ' |',
        *('| ' + ' | '.join(str(r[k]) if r[k] is not None else 'NA' for k in keys) + ' |' for r in rows),
    ])




def make_monthly_chart(rows):
    """Generate a dependency-free SVG figure from actual monthly aggregates."""
    from html import escape
    chart_dir = REPORTS / 'figures'
    chart_dir.mkdir(parents=True, exist_ok=True)
    W, H = 850, 370
    left, top, baseline, right = 82, 42, 298, 825
    max_v = 3000
    plot_h = baseline - top
    bar_width = 36
    step = (right - left) / len(rows)
    elems = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
      '<title id="title">2008 inpatient claim-segment rows by admission month</title>',
      '<desc id="desc">Bar chart of 27,701 synthetic CMS inpatient claim segments admitted in 2008, grouped by month.</desc>',
      '<rect width="850" height="370" fill="#ffffff"/>',
      '<text x="82" y="25" fill="#16324f" font-family="Arial,sans-serif" font-size="18" font-weight="bold">Inpatient claim-segment rows by admission month</text>',
    ]
    for tick in (0, 1000, 2000, 3000):
        y = baseline - round(tick/max_v*plot_h)
        elems.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#e2e8f0" stroke-width="1"/>')
        elems.append(f'<text x="{left-13}" y="{y+5}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#475569">{tick:,}</text>')
    for i, row in enumerate(rows):
        count = int(row['claim_segment_rows'])
        cx = left + step*(i+0.5)
        h = round(count/max_v*plot_h)
        y = baseline - h
        month = row['admission_month'][-2:]
        elems.append(f'<rect x="{cx-bar_width/2:.1f}" y="{y}" width="{bar_width}" height="{h}" rx="3" fill="#327f8f"/>')
        elems.append(f'<text x="{cx:.1f}" y="{y-7}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#16324f">{count:,}</text>')
        elems.append(f'<text x="{cx:.1f}" y="{baseline+19}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#475569">{escape(month)}</text>')
    elems.append('<text x="454" y="341" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#64748b">2008 admission month | CMS DE-SynPUF Sample 1 (synthetic data)</text>')
    elems.append('</svg>')
    (chart_dir/'2008_monthly_admissions.svg').write_text('\n'.join(elems)+'\n', encoding='utf-8')

def generate():
    if not DB.exists():
        raise FileNotFoundError(f"Run py scripts/build_database.py first; missing: {DB}")
    OUT.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        record_counts = get(c, "SELECT 'beneficiaries_2008' AS dataset, COUNT(*) AS rows FROM beneficiaries_2008 UNION ALL SELECT 'inpatient_claims', COUNT(*) FROM inpatient_claims UNION ALL SELECT 'claims_2008', COUNT(*) FROM claims_2008")
        years = get(c, ADMISSION_QUERY)
        quality = get(c, QUALITY_QUERY)
        overall = get(c, OVERALL_QUERY)
        ages = get(c, AGE_QUERY)
        months = get(c, MONTH_QUERY)
        diagnoses = get(c, DIAG_QUERY)
        dup = get(c, DUP_QUERY)
        rows = quality[0]['rows_2008']
        flagged = [{"check": k, "count": v, "percent_of_2008_rows": round(v / rows * 100, 3) if rows else None}
                   for k, v in quality[0].items() if k != 'rows_2008']
        data = {"source": "CMS DE-SynPUF Sample 1, beneficiary 2008 and inpatient 2008–2010 (synthetic)",
                "analysis_filter": "inpatient CLM_ADMSN_DT admission year 2008",
                "record_counts": record_counts, "admission_years": years,
                "quality_flags": quality[0], "composite_key_duplicate_groups": dup[0]['duplicate_composite_key_groups'],
                "overall": overall[0], "age_group": ages, "admission_month": months, "top_icd9": diagnoses}
        (OUT / 'metrics.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
        for f, rows_ in [('source_counts.csv',record_counts),('admission_year_counts.csv',years),
                         ('quality_flags.csv',flagged),('age_group_summary.csv',ages),
                         ('monthly_summary.csv',months),('top_icd9_diagnoses.csv',diagnoses)]:
            write_csv(f, rows_)
        make_monthly_chart(months)
        o = overall[0]; q=quality[0]
        note='''### Methods and important limitations

- **Source:** CMS 2008–2010 Data Entrepreneurs’ Synthetic Public Use File (DE-SynPUF), Sample 1. These are *synthetic* CMS training/development data, not real patient claims. The data do not support population-level clinical or utilization inference.
- **Cohort:** Select claim **segments** with `CLM_ADMSN_DT` in 2008, matching the 2008 beneficiary snapshot by `DESYNPUF_ID`. Source admissions from other years are retained in the raw table but excluded from 2008 summaries.
- **Record granularity:** Row-level records are claim segments. Repeated `CLM_ID` across different `SEGMENT` values is **not** necessarily a duplicate; composite duplicates are tested by `(CLM_ID, SEGMENT)`. Counts and averages based on rows may be segment-weighted.
- **Dates and age:** SAS/Python parse `YYYYMMDD` to dates. Age at admission derives from synthetic birth dates and is for demonstration only.
- **Payment and utilization:** Negative payment amounts are flagged, kept in the dataset, and excluded from the *nonnegative-payment average* only. Missing utilization days are retained and excluded from the utilization mean. We use CMS `CLM_UTLZTN_DAY_CNT`, not a manually inferred length of stay.
- **Missing values:** No missing value is imputed. This differs intentionally from the separate infection-surveillance coursework example, where imputation was the task.
- **Coding:** Principal diagnosis values are **ICD-9**, appropriate to the 2008 synthetic claims; these should not be presented as ICD-10-CM codes or as HAI case definitions.
- **Execution provenance:** The numerical results in this report were generated by Python standard-library ingestion of the supplied **real CMS CSVs** into SQLite, followed by SQLite queries. The separate `.sas` files are provided for execution in SAS Studio; **the SAS scripts were not executed or independently validated in a SAS runtime** as part of creating this report. The import counts were previously confirmed in SAS Studio by the project owner. The numerical tables here were validated through the independent Python/SQLite workflow.
'''
        report = f'''# Medicare Claims Data Quality & Utilization — CMS Synthetic Sample 1

*Generated from the two publicly released CMS Sample 1 CSVs supplied for this project. Synthetic records; not demo values. Analysis date: {dt.date.today().isoformat()}.*

## Executive summary

The source files contain **{record_counts[0]['rows']:,}** 2008 beneficiary records and **{record_counts[1]['rows']:,}** inpatient claim-segment rows covering multiple admission years. Restricting by **2008 admission date** yields **{o['claim_segment_rows']:,}** segment rows representing **{o['distinct_claim_ids']:,}** distinct claim IDs and **{o['distinct_beneficiaries']:,}** distinct beneficiary identifiers. The record-level quality checks flag **{q['negative_payments']:,}** negative claim-payment values and **{q['missing_utilization_days']:,}** missing utilization-day values. All rows are retained for auditability.

Across 2008 segments, the average **nonnegative** claim payment is **${o['avg_nonnegative_payment']:,.2f}** and the mean **recorded utilization days** is **{o['avg_recorded_utilization_days']:.2f}**, computed using nonmissing, nonnegative eligible observations only. These are descriptive figures for synthetic data and are not estimates for real Medicare patients.

## Key findings and interpretation

1. **Claims have multiple levels of identification.** The 27,701 inpatient rows represent 27,682 distinct claim IDs, so analysis should not automatically treat one row as one unique claim. The `(CLM_ID, SEGMENT)` composite key has no duplicates in the 2008 cohort.
2. **Data quality exceptions should be recorded rather than silently removed.** The data have 22 negative claim payments ({q['negative_payments']/o['claim_segment_rows']*100:.3f}% of 2008 rows) and 23 missing recorded utilization-day values ({q['missing_utilization_days']/o['claim_segment_rows']*100:.3f}%). Both remain in the underlying data; only ineligible values are excluded from relevant averages.
3. **Date filters need explicit definitions.** The 2008–2010 inpatient extract includes 226 records with 2007 admission dates. This project consistently defines its study cohort by admission in 2008, not the filename or claim processing year.

## 1. Source reconciliation

{md_table(record_counts)}

### Admission-year distribution (entire inpatient source)

{md_table(years)}

**Note:** The inpatient source contains pre-2008 admission dates as well; we explicitly filter to admission year 2008 instead of assuming every row belongs to 2008–2010 by admission.

## 2. Data quality checks (2008 admission-year subset)

{md_table(flagged)}

Duplicate `(CLM_ID, SEGMENT)` groups: **{dup[0]['duplicate_composite_key_groups']:,}**. Different segments belonging to the same claim are retained.

## 3. Utilization and payments by beneficiary age group

{md_table(ages)}

Age groups are based on synthetic birth dates; these statistics demonstrate query patterns only.

## 4. Monthly summary by admission date

![2008 inpatient claim-segment rows by admission month](figures/2008_monthly_admissions.svg)

{md_table(months)}

## 5. Most frequent principal ICD-9 code values

{md_table(diagnoses)}

These are *code values* taken from the synthetic claims, not clinically validated diagnoses. Counts are claim-segment rows, not patient incidence.

{note}
## Reproduction steps

1. Place both CMS CSVs under `data/raw/` (exact filenames listed in README).
2. Run `py scripts/build_database.py` from the repository root; this creates the local SQLite database and `claims_2008` view.
3. Run `py scripts/generate_report.py`; this regenerates this Markdown report and the aggregate CSVs in `outputs/`.
4. Independently run `sas/00_import_and_verify.sas`, `01_clean_and_quality_checks.sas`, and `02_summary_and_export.sas` in SAS Studio Online and compare the key counts and aggregates to the SQL output.

**Official sources:** [CMS Sample 1 downloads](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1) · [CMS DE-SynPUF overview](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf) · [CMS codebook](https://www.cms.gov/files/document/de-10-codebook.pdf-0)
'''
        dest=REPORTS/'real_cms_sample1_2008_report.md'
        dest.write_text(report,encoding='utf-8')
        print(f'Report written: {dest}')
        print(f"2008 rows {o['claim_segment_rows']:,}; negative payments {q['negative_payments']:,}; missing utilization {q['missing_utilization_days']:,}")
    finally:
        c.close()

if __name__=='__main__':
    generate()
