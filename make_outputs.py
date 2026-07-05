"""
make_outputs.py

This is the "programming" part of the project. It reads the analysis
datasets in data/ and builds the kind of summary tables a clinical
programmer would normally make in SAS (a demographics table, an adverse
event summary, and a vital signs change-from-baseline table).

The idea is to show the same outputs you'd get from SAS PROC FREQ /
PROC MEANS, but done in Python with pandas. The tables are saved as CSV
files in the outputs/ folder. The Streamlit app recomputes and visualises
these figures on its pages rather than reading these CSVs directly.

Treatment variables follow the usual convention: demographics by PLANNED
treatment (TRT01P), safety tables (adverse events, vitals) by ACTUAL
treatment received (TRT01A).

Run it with:  python make_outputs.py
"""

import os
from pathlib import Path

import pandas as pd

# Resolve folders relative to THIS file so the script works from any CWD.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"

# treatment groups in the order we want them shown
ARMS = ["Placebo", "Xanomeline Low Dose", "Xanomeline High Dose"]

# treatment variables: planned for demographics, actual for safety
PLANNED_TRT = "TRT01P"
ACTUAL_TRT = "TRT01A"

_LOWER_WORDS = {"or", "and", "of", "the", "in", "on", "to", "a", "an"}


def load(name):
    return pd.read_csv(DATA_DIR / (name + ".csv"))


def pretty(text):
    """Tidy an UPPER CASE label into Title Case, keeping small words lower."""
    words = str(text).split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        out.append(lw if (i > 0 and lw in _LOWER_WORDS) else lw.capitalize())
    return " ".join(out)


def pct(count, total):
    """Return a 'n (xx.x%)' string, like SAS would print."""
    if total == 0:
        return "0"
    return str(count) + " (" + format(100 * count / total, ".1f") + "%)"


# ---------------------------------------------------------------------------
# Table 1 - Demographics and baseline characteristics (PLANNED treatment)
# ---------------------------------------------------------------------------
def demographics_table(adsl):
    # how many subjects in each arm (this is the denominator for %)
    n_by_arm = {}
    for arm in ARMS:
        n_by_arm[arm] = len(adsl[adsl[PLANNED_TRT] == arm])

    rows = []

    # header row showing N per arm
    header = {"Characteristic": "", "Category": "N"}
    for arm in ARMS:
        header[arm] = n_by_arm[arm]
    rows.append(header)

    # Age - summary statistics (mean, sd, min, max)
    for stat in ["Mean", "SD", "Min", "Max"]:
        row = {"Characteristic": "Age (years)", "Category": stat}
        for arm in ARMS:
            ages = adsl[adsl[PLANNED_TRT] == arm]["AGE"]
            if stat == "Mean":
                row[arm] = format(ages.mean(), ".1f")
            elif stat == "SD":
                row[arm] = format(ages.std(), ".1f")
            elif stat == "Min":
                row[arm] = int(ages.min())
            else:
                row[arm] = int(ages.max())
        rows.append(row)

    # Sex - counts and percents
    for value in ["F", "M"]:
        row = {"Characteristic": "Sex", "Category": value}
        for arm in ARMS:
            arm_data = adsl[adsl[PLANNED_TRT] == arm]
            count = len(arm_data[arm_data["SEX"] == value])
            row[arm] = pct(count, n_by_arm[arm])
        rows.append(row)

    # Race - counts and percents
    for value in sorted(adsl["RACE"].dropna().unique()):
        row = {"Characteristic": "Race", "Category": pretty(value)}
        for arm in ARMS:
            arm_data = adsl[adsl[PLANNED_TRT] == arm]
            count = len(arm_data[arm_data["RACE"] == value])
            row[arm] = pct(count, n_by_arm[arm])
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 2 - Treatment emergent adverse events by SOC (ACTUAL treatment)
# ---------------------------------------------------------------------------
def ae_table(adsl, adae):
    # denominators = subjects who ACTUALLY received each treatment
    n_by_arm = {}
    for arm in ARMS:
        n_by_arm[arm] = len(adsl[adsl[ACTUAL_TRT] == arm])

    # only treatment emergent AEs
    teae = adae[adae["TRTEMFL"] == "Y"]

    rows = []

    # row 1: subjects with at least one TEAE
    row = {"System Organ Class": "Subjects with any TEAE"}
    for arm in ARMS:
        subs = teae[teae[ACTUAL_TRT] == arm]["USUBJID"].nunique()
        row[arm] = pct(subs, n_by_arm[arm])
    rows.append(row)

    # then one row per system organ class (count each subject once)
    for soc in sorted(teae["AESOC"].dropna().unique()):
        soc_data = teae[teae["AESOC"] == soc]
        row = {"System Organ Class": pretty(soc)}
        for arm in ARMS:
            subs = soc_data[soc_data[ACTUAL_TRT] == arm]["USUBJID"].nunique()
            row[arm] = pct(subs, n_by_arm[arm])
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 3 - Vital signs change from baseline at Week 24 (ACTUAL treatment)
# ---------------------------------------------------------------------------
def vitals_table(advs):
    # we look at the Week 24 visit
    week24 = advs[advs["AVISIT"] == "Week 24"]

    rows = []
    for param_code in ["SYSBP", "DIABP", "PULSE", "TEMP", "WEIGHT"]:
        param_data = week24[week24["PARAMCD"] == param_code]
        if len(param_data) == 0:
            continue
        # nice label for the parameter
        label = param_data["PARAM"].iloc[0]
        for arm in ARMS:
            arm_data = param_data[param_data[ACTUAL_TRT] == arm]
            row = {
                "Parameter": label,
                "Treatment": arm,
                "N": len(arm_data),
                "Baseline Mean": format(arm_data["BASE"].mean(), ".1f"),
                "Week 24 Mean": format(arm_data["AVAL"].mean(), ".1f"),
                "Change Mean": format(arm_data["CHG"].mean(), ".2f"),
                "Change SD": format(arm_data["CHG"].std(), ".2f"),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    adsl = load("adsl")
    adae = load("adae")
    advs = load("advs")

    t1 = demographics_table(adsl)
    t1.to_csv(OUT_DIR / "t_demographics.csv", index=False)
    print("saved outputs/t_demographics.csv")

    t2 = ae_table(adsl, adae)
    t2.to_csv(OUT_DIR / "t_ae_summary.csv", index=False)
    print("saved outputs/t_ae_summary.csv")

    t3 = vitals_table(advs)
    t3.to_csv(OUT_DIR / "t_vitals_change.csv", index=False)
    print("saved outputs/t_vitals_change.csv")

    print("all tables built")


if __name__ == "__main__":
    main()
