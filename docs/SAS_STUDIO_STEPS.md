# Running the SAS portion in SAS Studio Online

The project uses two separate, reproducible approaches: **(1) SAS Studio cleaning and aggregation**, and **(2) a Python + SQLite analytics pipeline**. The checked-in summary report was generated using approach 2. To validate the SAS portion independently, follow these steps.

1. **Sign into SAS Studio Online.** Under *Server Files and Folders* upload the two **extracted** CMS CSV files to one folder (for example `medicare_project`). Do not upload ZIP files.
2. **Start a SAS Program.** Open [`sas/00_import_and_verify.sas`](../sas/00_import_and_verify.sas) and change `%let raw_dir=...;` to the **server** folder containing both CSVs. Do not use `C:\Users\...` paths; SAS Studio Online runs on a remote server. Run it. Confirm 116,352 beneficiaries (32 columns) and 66,773 inpatient rows (81 columns).
3. **Clean and validate.** Run [`sas/01_clean_and_quality_checks.sas`](../sas/01_clean_and_quality_checks.sas) in the same session. It creates `WORK.CLAIMS_2008_JOINED`, `WORK.QC_SUMMARY`, and `WORK.DUPLICATE_CLAIM_SEGMENTS`. Compare its 2008 results with the report (27,701 rows, 22 negative payments, 23 missing utilization days, zero duplicated composite-key groups).
4. **Summarize and export.** Run [`sas/02_summary_and_export.sas`](../sas/02_summary_and_export.sas). It writes three **aggregated** `.csv` files to the online `raw_dir` folder. Download these aggregates if you want to compare them to `outputs/` locally.
5. **Save SAS programs as `.sas` text files** and add them to GitHub alongside SQL and Python scripts. It is normal for `WORK` tables to disappear between sessions; rerun scripts 00 → 01 → 02 next time.

If `PROC IMPORT` infers an unexpected field type (especially identifiers or ICD-9 codes), inspect the `PROC CONTENTS` output and consider a fixed-layout `DATA` step or CMS-supplied SAS read-in code before subsequent analysis. The quality analysis intentionally **does not impute missing values**, unlike a separate course exercise.

The checked-in report was generated using Python and SQLite against the original CMS CSV files. **The project owner independently executed all three SAS programs in SAS Studio Online on October 26, 2026**, and compared their results with the checked-in figures. The matching key quality checks and summaries are documented in [SAS Validation Results](SAS_VALIDATION_RESULTS.md). Reviewers can use the instructions above to reproduce the comparison in their own SAS environment.
