"""
prepare_data.py

This script downloads the CDISC pilot test data from the pharmaverse
packages and saves smaller, cleaned-up copies into the data/ folder.
I only run this once. After that the app just reads the files in data/.

The pharmaverse data is open source (Apache License 2.0), so it's fine to
download, trim and keep a copy here (with credit - see the README).

What it does:
  1. download ADSL, ADAE, ADVS, ADLB from the pharmaverse GitHub (pinned commit)
  2. keep only the safety population (SAFFL = 'Y'), which is 254 subjects
  3. select the proper CDISC analysis records (see notes on ADVS / ADLB below)
  4. keep only the columns the app actually uses
  5. save the results as small CSV files in data/
"""

import os
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# --- Pin the data source for reproducibility ----------------------------------
# The pharmaverseadam CSVs are read from GitHub. Pulling from the moving "main"
# branch means a rerun months from now could quietly produce different numbers,
# so we pin to an immutable commit SHA (tag v1.2.0). The committed files in
# data/ are the snapshot the app currently ships with, built from this commit.
ADAM_REF = "5a12292134aaf4e2893136e1eb92329ddbf2576a"  # pharmaverseadam v1.2.0
ADAM_URL = (
    "https://raw.githubusercontent.com/pharmaverse/pharmaverseadam/"
    + ADAM_REF
    + "/inst/extdata"
)

# only keep these columns so the files stay small.
# TRT01A (actual treatment) is kept alongside TRT01P (planned) because safety
# analyses conventionally use ACTUAL treatment. In this pilot 12 subjects were
# planned Xanomeline High Dose but actually received Low Dose, so the two are
# NOT interchangeable and the app groups its safety pages by TRT01A.
ADSL_COLS = ["USUBJID", "TRT01P", "TRT01A", "AGE", "AGEGR1", "SEX", "RACE", "SAFFL"]
ADAE_COLS = ["USUBJID", "TRT01P", "TRT01A", "TRTEMFL", "AESOC", "AEDECOD", "AESEV"]
# ATPT (analysis timepoint = body position) is kept so the position choice for
# blood pressure / pulse is transparent in the shipped data.
ADVS_COLS = ["USUBJID", "TRT01P", "TRT01A", "PARAMCD", "PARAM", "AVISIT", "AVISITN",
             "ATPT", "AVAL", "BASE", "CHG"]
# DTYPE marks ADaM-derived analysis rows. We keep it because the shift table uses
# the DTYPE == 'LOV' ("last observation value", labelled AVISIT 'POST-BASELINE
# LAST') record directly, selecting it explicitly instead of relying on row order.
ADLB_COLS = ["USUBJID", "TRT01P", "TRT01A", "PARAMCD", "PARAM", "AVISIT", "AVISITN",
             "DTYPE", "AVAL", "BASE", "ANRIND", "BNRIND"]

# a few vitals / lab tests to keep (otherwise the files are huge)
VS_KEEP = ["SYSBP", "DIABP", "PULSE", "TEMP", "WEIGHT"]
LB_KEEP = ["ALT", "AST", "BILI", "CREAT", "GLUC", "CHOLES", "ALB", "BUN"]

# Blood pressure and pulse are recorded in several body positions. We analyse a
# single, pre-specified position (supine) rather than averaging across positions:
# averaging mixes supine and standing measurements (not a meaningful quantity)
# and, because the number of positions can vary by visit, it also breaks the
# ADaM rule that BASE is invariant within a subject/parameter.
VS_POSITION = "AFTER LYING DOWN FOR 5 MINUTES"


def get_data(name):
    """Download one pharmaverse csv and return it as a dataframe."""
    url = ADAM_URL + "/" + name + ".csv"
    print("downloading", name, "...")
    return pd.read_csv(url, low_memory=False)


def keep_cols(df, cols):
    """Keep the requested columns that actually exist, in order.

    This tolerates schema differences between pharmaverse releases: if a
    pinned version is missing an optional column we keep what is present and
    warn instead of raising a KeyError.
    """
    present = [c for c in cols if c in df.columns]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print("  note: columns not found and skipped:", ", ".join(missing))
    return df[present]


def select_vs_records(advs):
    """One observed analysis record per subject/parameter/visit for vitals.

    Steps:
      * keep the analysis records (ANL01FL == 'Y') when the flag is present;
      * drop ADaM-derived rows (DTYPE not null) such as AVERAGE / MIN / MAX /
        LAST - the derived AVERAGE record in particular carries no BASE or CHG;
      * for positioned parameters (BP, pulse) keep the supine record, falling
        back deterministically to the first position if supine is unavailable;
        non-positioned parameters (temperature, weight) pass through unchanged.
    The result is one row per subject/parameter/visit with a valid, invariant
    BASE and CHG == AVAL - BASE.
    """
    if "ANL01FL" in advs.columns:
        advs = advs[advs["ANL01FL"] == "Y"]
    if "DTYPE" in advs.columns:
        advs = advs[advs["DTYPE"].isna()]

    if "ATPT" in advs.columns:
        # supine first (rank 0), then any other position alphabetically, so the
        # choice is deterministic and never depends on row order.
        advs = advs.copy()
        advs["_pos_rank"] = (advs["ATPT"] != VS_POSITION).astype(int)
        advs = advs.sort_values(["USUBJID", "PARAMCD", "AVISIT",
                                 "_pos_rank", "ATPT"])
        advs = advs.drop_duplicates(["USUBJID", "PARAMCD", "AVISIT"],
                                    keep="first")
        advs = advs.drop(columns="_pos_rank")
    return advs


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. ADSL - subject level. Keep the safety population only.
    adsl = get_data("adsl")
    adsl = adsl[adsl["SAFFL"] == "Y"]
    adsl = keep_cols(adsl, ADSL_COLS)
    subjects = adsl["USUBJID"].unique()   # the 254 subjects we keep
    adsl.to_csv(DATA_DIR / "adsl.csv", index=False)
    print("adsl:", len(adsl), "subjects")

    # 2. ADAE - adverse events. Keep only our subjects.
    adae = get_data("adae")
    adae = adae[adae["USUBJID"].isin(subjects)]
    adae = keep_cols(adae, ADAE_COLS)
    adae.to_csv(DATA_DIR / "adae.csv", index=False)
    print("adae:", len(adae), "rows")

    # 3. ADVS - vital signs. One supine analysis record per subject/test/visit.
    advs = get_data("advs")
    advs = advs[advs["USUBJID"].isin(subjects)]
    advs = advs[advs["PARAMCD"].isin(VS_KEEP)]
    advs = select_vs_records(advs)
    advs = keep_cols(advs, ADVS_COLS)
    advs.to_csv(DATA_DIR / "advs.csv", index=False)
    print("advs:", len(advs), "rows")

    # 4. ADLB - lab results. Keep our subjects and a few tests.
    # We keep the ANL01FL-flagged analysis rows (scheduled visits plus the
    # DTYPE-derived POST-BASELINE LAST / MIN / MAX records). The shift table in
    # pages/4_Lab_Results.py uses the DTYPE == 'LOV' record directly. A defensive
    # de-duplication keeps a single row per subject/test/visit, chosen
    # deterministically by visit number rather than by row order.
    adlb = get_data("adlb")
    adlb = adlb[adlb["USUBJID"].isin(subjects)]
    adlb = adlb[adlb["PARAMCD"].isin(LB_KEEP)]
    if "ANL01FL" in adlb.columns:
        adlb = adlb[adlb["ANL01FL"] == "Y"]
    adlb = keep_cols(adlb, ADLB_COLS)
    sort_keys = [c for c in ["USUBJID", "PARAMCD", "AVISITN", "AVISIT"]
                 if c in adlb.columns]
    adlb = (adlb.sort_values(sort_keys)
                .drop_duplicates(["USUBJID", "PARAMCD", "AVISIT"], keep="last"))
    adlb.to_csv(DATA_DIR / "adlb.csv", index=False)
    print("adlb:", len(adlb), "rows")

    print("done - files saved in data/")


if __name__ == "__main__":
    main()
