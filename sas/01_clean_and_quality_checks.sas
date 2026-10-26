/* ====================================================================
 CMS DE-SynPUF Sample 1 | 01_clean_and_quality_checks.sas
 Run AFTER 00_import_and_verify.sas in the same SAS Studio WORK session.
 Input:  work.bene2008, work.inpatient_raw
 Output: work.claims_2008_joined, work.qc_summary
 Rule: no imputation, no deletion for flagged values, no claim deduplication.
 Filter by ADMISSION year 2008 to match the 2008 beneficiary snapshot.
 ==================================================================== */

/* CMS YYYYMMDD values are numerics after PROC IMPORT; convert to SAS dates. */
data work.bene2008_clean;
  set work.bene2008(keep=DESYNPUF_ID BENE_BIRTH_DT
                         BENE_SEX_IDENT_CD BENE_RACE_CD);
  birth_date = input(put(BENE_BIRTH_DT,z8.),yymmdd8.);
  format birth_date yymmdd10.;
run;

data work.claims_2008_qc;
  set work.inpatient_raw(
    keep=DESYNPUF_ID CLM_ID SEGMENT CLM_ADMSN_DT NCH_BENE_DSCHRG_DT
         CLM_PMT_AMT CLM_UTLZTN_DAY_CNT ICD9_DGNS_CD_1);

  admission_date = input(put(CLM_ADMSN_DT,z8.),yymmdd8.);
  discharge_date = input(put(NCH_BENE_DSCHRG_DT,z8.),yymmdd8.);
  format admission_date discharge_date yymmdd10.;

  /* Preserve segment-level records; 2008 beneficiary data is time-specific. */
  if year(admission_date) = 2008;

  flag_missing_key = missing(DESYNPUF_ID) or missing(CLM_ID)
                     or missing(SEGMENT);
  flag_invalid_dates = missing(admission_date) or missing(discharge_date)
                      or discharge_date < admission_date;
  flag_missing_payment = missing(CLM_PMT_AMT);
  flag_negative_payment = not missing(CLM_PMT_AMT) and CLM_PMT_AMT < 0;
  flag_missing_utilization = missing(CLM_UTLZTN_DAY_CNT);
  flag_negative_utilization = not missing(CLM_UTLZTN_DAY_CNT)
                              and CLM_UTLZTN_DAY_CNT < 0;
  if not flag_invalid_dates then
    elapsed_nights = discharge_date - admission_date;
run;

/* Beneficiary records joined by CMS linking ID. LEFT JOIN keeps unmatched rows. */
proc sql;
  create table work.claims_2008_joined as
  select c.*,
         b.birth_date,
         b.BENE_SEX_IDENT_CD,
         b.BENE_RACE_CD,
         case when missing(b.DESYNPUF_ID) then 1 else 0 end
           as flag_unmatched_beneficiary
  from work.claims_2008_qc as c
  left join work.bene2008_clean as b
    on c.DESYNPUF_ID = b.DESYNPUF_ID;
quit;

data work.claims_2008_joined;
  set work.claims_2008_joined;
  length age_group $10;
  if not missing(birth_date) and not missing(admission_date) then
    age_at_admission = intck('year',birth_date,admission_date,'c');

  flag_invalid_age = missing(age_at_admission)
                     or age_at_admission < 0 or age_at_admission > 120;
  if 0 <= age_at_admission and age_at_admission <= 64 then age_group='Under 65';
  else if 65 <= age_at_admission and age_at_admission <= 74 then age_group='65-74';
  else if 75 <= age_at_admission and age_at_admission <= 84 then age_group='75-84';
  else if 85 <= age_at_admission and age_at_admission <= 120 then age_group='85+';
  else age_group='Unknown';
run;

/* Quality flags are counts of record-level exceptions, not errors to delete. */
proc sql;
  create table work.qc_summary as
    select 'Missing claim or beneficiary key' as Check_Name length=45,
           sum(flag_missing_key) as Flagged_Rows from work.claims_2008_joined
    union all
    select 'Missing or reversed dates', sum(flag_invalid_dates)
      from work.claims_2008_joined
    union all
    select 'Missing claim payment', sum(flag_missing_payment)
      from work.claims_2008_joined
    union all
    select 'Negative claim payment', sum(flag_negative_payment)
      from work.claims_2008_joined
    union all
    select 'Missing recorded utilization days', sum(flag_missing_utilization)
      from work.claims_2008_joined
    union all
    select 'Negative recorded utilization days', sum(flag_negative_utilization)
      from work.claims_2008_joined
    union all
    select 'No matching 2008 beneficiary', sum(flag_unmatched_beneficiary)
      from work.claims_2008_joined
    union all
    select 'Missing or invalid age', sum(flag_invalid_age)
      from work.claims_2008_joined;

  /* Claim IDs can recur across segments: check composite-key duplicates. */
  create table work.duplicate_claim_segments as
    select CLM_ID, SEGMENT, count(*) as Number_Of_Rows
    from work.claims_2008_joined
    group by CLM_ID, SEGMENT
    having calculated Number_Of_Rows > 1;
quit;

title 'Actual 2008 Claims - Data Quality Flag Counts';
proc print data=work.qc_summary noobs; run;
title 'Composite claim ID + segment duplicate groups';
proc sql;
 select count(*) as Duplicate_Groups from work.duplicate_claim_segments;
 select count(*) as Claim_Segment_Rows,
        count(distinct CLM_ID) as Distinct_Claim_IDs,
        count(distinct DESYNPUF_ID) as Distinct_Beneficiaries
 from work.claims_2008_joined;
quit;
title;

/* Expected for CMS Sample 1 (verified independently against raw CSV):
   2008 claim-segment rows = 27701
   Distinct claim IDs = 27682
   Negative payments = 22
   Missing recorded utilization days = 23
   Duplicate (CLM_ID,SEGMENT) groups = 0
   Do not use CLM_ID alone as a uniqueness key.
*/
