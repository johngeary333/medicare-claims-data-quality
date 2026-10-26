"""Load genuine CMS DE-SynPUF Sample 1 CSVs into SQLite using Python standard library.

No demo/fabricated records. Rebuild by running: py scripts/build_database.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "processed" / "medicare_claims.sqlite"
BENEFICIARY = RAW / "DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv"
INPATIENT = RAW / "DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv"


def date_iso(s: str) -> str | None:
    if not s.strip():
        return None
    try:
        return dt.datetime.strptime(s.strip(), "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def number(s: str) -> float | None:
    if not s.strip():
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load():
    for file in (BENEFICIARY, INPATIENT):
        if not file.exists():
            raise FileNotFoundError(f"Missing source: {file}\nExtract the original CMS CSV here first.")
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    try:
        conn.executescript("""
            PRAGMA foreign_keys=OFF;
            CREATE TABLE beneficiaries_2008 (
                DESYNPUF_ID TEXT PRIMARY KEY,
                BENE_BIRTH_DT TEXT,
                birth_date TEXT,
                BENE_SEX_IDENT_CD TEXT,
                BENE_RACE_CD TEXT,
                BENE_HI_CVRAGE_TOT_MONS INTEGER
            );
            CREATE TABLE inpatient_claims (
                source_row INTEGER PRIMARY KEY,
                DESYNPUF_ID TEXT,
                CLM_ID TEXT,
                SEGMENT TEXT,
                CLM_ADMSN_DT TEXT,
                NCH_BENE_DSCHRG_DT TEXT,
                admission_date TEXT,
                discharge_date TEXT,
                CLM_PMT_AMT REAL,
                CLM_UTLZTN_DAY_CNT REAL,
                ICD9_DGNS_CD_1 TEXT
            );
            CREATE INDEX ix_ip_bene ON inpatient_claims(DESYNPUF_ID);
            CREATE INDEX ix_ip_key ON inpatient_claims(CLM_ID,SEGMENT);
            CREATE INDEX ix_ip_admission ON inpatient_claims(CLM_ADMSN_DT);
        """)
        with BENEFICIARY.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"DESYNPUF_ID", "BENE_BIRTH_DT", "BENE_SEX_IDENT_CD", "BENE_RACE_CD"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"Beneficiary missing columns: {required-set(reader.fieldnames or [])}")
            conn.executemany("""
                INSERT INTO beneficiaries_2008 VALUES (?,?,?,?,?,?)
            """, (
                (r["DESYNPUF_ID"], r["BENE_BIRTH_DT"], date_iso(r["BENE_BIRTH_DT"]),
                 r["BENE_SEX_IDENT_CD"], r["BENE_RACE_CD"],
                 int(r["BENE_HI_CVRAGE_TOT_MONS"]) if r["BENE_HI_CVRAGE_TOT_MONS"].strip() else None)
                for r in reader
            ))
        with INPATIENT.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"DESYNPUF_ID", "CLM_ID", "SEGMENT", "CLM_ADMSN_DT", "NCH_BENE_DSCHRG_DT", "CLM_PMT_AMT", "CLM_UTLZTN_DAY_CNT", "ICD9_DGNS_CD_1"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"Inpatient missing columns: {required-set(reader.fieldnames or [])}")
            conn.executemany("""
                INSERT INTO inpatient_claims VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                (i, r["DESYNPUF_ID"], r["CLM_ID"], r["SEGMENT"],
                 r["CLM_ADMSN_DT"], r["NCH_BENE_DSCHRG_DT"],
                 date_iso(r["CLM_ADMSN_DT"]), date_iso(r["NCH_BENE_DSCHRG_DT"]),
                 number(r["CLM_PMT_AMT"]), number(r["CLM_UTLZTN_DAY_CNT"]),
                 r["ICD9_DGNS_CD_1"])
                for i, r in enumerate(reader, 1)
            ))
        conn.executescript("""
            DROP VIEW IF EXISTS claims_2008;
            CREATE VIEW claims_2008 AS
            WITH joined AS (
                SELECT c.*, b.BENE_BIRTH_DT, b.birth_date, b.BENE_SEX_IDENT_CD,
                       b.BENE_RACE_CD,
                       (CAST(strftime('%Y',c.admission_date) AS INTEGER)
                        - CAST(strftime('%Y',b.birth_date) AS INTEGER)
                        - (strftime('%m-%d',c.admission_date) < strftime('%m-%d',b.birth_date))) AS age_at_admission,
                       CASE WHEN b.DESYNPUF_ID IS NULL THEN 1 ELSE 0 END AS flag_unmatched_beneficiary
                FROM inpatient_claims c
                LEFT JOIN beneficiaries_2008 b ON c.DESYNPUF_ID=b.DESYNPUF_ID
                WHERE substr(c.CLM_ADMSN_DT,1,4)='2008'
            )
            SELECT j.*,
                CASE WHEN admission_date IS NULL OR discharge_date IS NULL
                          OR discharge_date < admission_date THEN 1 ELSE 0 END AS flag_invalid_dates,
                CASE WHEN CLM_PMT_AMT IS NULL THEN 1 ELSE 0 END AS flag_missing_payment,
                CASE WHEN CLM_PMT_AMT < 0 THEN 1 ELSE 0 END AS flag_negative_payment,
                CASE WHEN CLM_UTLZTN_DAY_CNT IS NULL THEN 1 ELSE 0 END AS flag_missing_utilization,
                CASE WHEN CLM_UTLZTN_DAY_CNT < 0 THEN 1 ELSE 0 END AS flag_negative_utilization,
                CASE WHEN DESYNPUF_ID IS NULL OR DESYNPUF_ID=''
                       OR CLM_ID IS NULL OR CLM_ID=''
                       OR SEGMENT IS NULL OR SEGMENT='' THEN 1 ELSE 0 END AS flag_missing_key,
                CASE WHEN age_at_admission IS NULL OR age_at_admission < 0 OR age_at_admission > 120
                       THEN 1 ELSE 0 END AS flag_invalid_age,
                CASE WHEN discharge_date >= admission_date
                       THEN CAST(julianday(discharge_date)-julianday(admission_date) AS INTEGER) END AS elapsed_nights,
                CASE WHEN age_at_admission BETWEEN 0 AND 64 THEN 'Under 65'
                     WHEN age_at_admission BETWEEN 65 AND 74 THEN '65-74'
                     WHEN age_at_admission BETWEEN 75 AND 84 THEN '75-84'
                     WHEN age_at_admission BETWEEN 85 AND 120 THEN '85+'
                     ELSE 'Unknown' END AS age_group
            FROM joined j;
        """)
        conn.commit()
        n_ben = conn.execute("SELECT count(*) FROM beneficiaries_2008").fetchone()[0]
        n_claim = conn.execute("SELECT count(*) FROM inpatient_claims").fetchone()[0]
        n_2008 = conn.execute("SELECT count(*) FROM claims_2008").fetchone()[0]
        print(f"Loaded real CMS CSVs: {n_ben:,} beneficiary rows, {n_claim:,} inpatient rows, {n_2008:,} inpatient rows with 2008 admission dates")
        print(f"SQLite database: {DB}")
    finally:
        conn.close()


if __name__ == "__main__":
    load()
