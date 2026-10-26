/* =====================================================================
 CMS DE-SynPUF Sample 1 | 00_import_and_verify.sas
 SAS Studio Online / SAS 9.4. Run this FIRST during each new WORK session.
 Uses the REAL CSV files you uploaded to SAS Studio Online.
 Change ONLY raw_dir to the folder displayed in Server Files and Folders.
 ===================================================================== */

%let raw_dir=/home/YOUR_USERNAME/medicare_project;

filename bene "&raw_dir./DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv";
filename ip   "&raw_dir./DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv";

%put NOTE: Beneficiary file = %sysfunc(pathname(bene));
%put NOTE: Inpatient file = %sysfunc(pathname(ip));

data _null_;
  if fexist('bene') then put 'NOTE: Beneficiary CSV is accessible.';
  else put 'ERROR: Beneficiary CSV NOT FOUND. Check raw_dir and filename.';
  if fexist('ip') then put 'NOTE: Inpatient CSV is accessible.';
  else put 'ERROR: Inpatient CSV NOT FOUND. Check raw_dir and filename.';
run;

/* PROC IMPORT guesses types; inspect PROC CONTENTS after import.
   It should show 32 beneficiary columns and 81 inpatient columns.
   Keep ID and ICD-9 code fields intact; do not perform arithmetic on them. */
proc import datafile=bene out=work.bene2008 dbms=csv replace;
  getnames=yes;
  guessingrows=max;
run;

proc import datafile=ip out=work.inpatient_raw dbms=csv replace;
  getnames=yes;
  guessingrows=max;
run;

title 'CMS DE-SynPUF Sample 1 - Source Row Counts';
proc sql;
  select count(*) as Beneficiary_Rows from work.bene2008;
  select count(*) as Inpatient_Rows from work.inpatient_raw;
quit;

title 'Beneficiary Data Dictionary - Verify 32 Variables';
proc contents data=work.bene2008 varnum; run;

title 'Inpatient Data Dictionary - Verify 81 Variables';
proc contents data=work.inpatient_raw varnum; run;
title;

/* Expected for the exact CMS Sample 1 CSVs:
   Beneficiary rows  = 116352
   Inpatient rows    = 66773
   Distinct file schemas: 32 vs 81 variables
*/
