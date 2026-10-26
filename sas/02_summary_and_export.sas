/* =====================================================================
 CMS DE-SynPUF Sample 1 | 02_summary_and_export.sas
 Run AFTER 01_clean_and_quality_checks.sas.
 It exports aggregated tables ONLY to your SAS Studio project folder.
 This program does not claim that the values represent real Medicare patients.
 ===================================================================== */

title '2008 Inpatient Claim-Segment Summary';
proc sql;
 select count(*) as Claim_Segment_Rows,
        count(distinct CLM_ID) as Unique_Claim_IDs,
        count(distinct DESYNPUF_ID) as Unique_Beneficiaries,
        mean(case when CLM_PMT_AMT >= 0 then CLM_PMT_AMT else . end)
          as Mean_Nonnegative_Payment format=dollar12.2,
        mean(case when CLM_UTLZTN_DAY_CNT >= 0 then CLM_UTLZTN_DAY_CNT else . end)
          as Mean_Recorded_Utilization_Days format=8.2
 from work.claims_2008_joined;

 create table work.by_age_group as
 select age_group, count(*) as Segment_Rows,
        count(distinct DESYNPUF_ID) as Unique_Beneficiaries,
        mean(case when CLM_PMT_AMT >= 0 then CLM_PMT_AMT else . end)
          as Mean_Nonnegative_Payment format=dollar12.2,
        mean(case when CLM_UTLZTN_DAY_CNT >= 0 then CLM_UTLZTN_DAY_CNT else . end)
          as Mean_Recorded_Utilization_Days format=8.2
 from work.claims_2008_joined
 group by age_group;

 create table work.by_month as
 select substr(put(admission_date,yymmdd10.),1,7) as Admission_Month length=7,
        count(*) as Segment_Rows,
        count(distinct DESYNPUF_ID) as Unique_Beneficiaries,
        mean(case when CLM_PMT_AMT >= 0 then CLM_PMT_AMT else . end)
          as Mean_Nonnegative_Payment format=dollar12.2
 from work.claims_2008_joined
 where not missing(admission_date)
 group by calculated Admission_Month;
quit;

title 'Inpatient 2008: Utilization and Payments by Age Group';
proc print data=work.by_age_group noobs; run;
title 'Inpatient 2008: Claims by Admission Month';
proc print data=work.by_month noobs; run;
title;

/* Reuses raw_dir from Step 00. Change it in Step 00 if needed. */
proc export data=work.qc_summary
  outfile="&raw_dir./sas_qc_summary.csv" dbms=csv replace;
run;
proc export data=work.by_age_group
  outfile="&raw_dir./sas_by_age_group.csv" dbms=csv replace;
run;
proc export data=work.by_month
  outfile="&raw_dir./sas_by_month.csv" dbms=csv replace;
run;

/* NOTE: export the SAS code to GitHub, but leave raw/row-level data
   out of the GitHub repo. Only aggregated report outputs are needed. */
