"""
Lab Results page.

Shows a "shift table" for a chosen lab test. A shift table counts how many
subjects moved between reference-range categories (Low / Normal / High)
from baseline to after treatment. This is a common safety-review table.

Grouped by actual treatment received (TRT01A), consistent with the other
safety pages.
"""

import re

import pandas as pd
import streamlit as st

import utils

TRT = utils.SAFETY_TRT

# Browser-tab title/icon and wide layout, consistent with the home
# page. Visual only.
st.set_page_config(page_title="Lab Results · Clinical Data Explorer", page_icon="🧪",
                   layout="wide")

utils.inject_css()
utils.page_header(
    "Lab Results",
    "Shift from baseline in reference-range category, by treatment group.",
    eyebrow="Actual treatment (TRT01A)",
)

adlb = utils.load("adlb")

# pick a lab test
params = adlb[["PARAMCD", "PARAM"]].drop_duplicates()
choice = st.selectbox("Lab test", params["PARAM"].tolist())
one_lab = adlb[adlb["PARAM"] == choice]

# pick a treatment group
arm = st.selectbox("Treatment group", utils.ARMS)
one_lab = one_lab[one_lab[TRT] == arm]

# We want, per subject, their baseline category (BNRIND) and their category at
# the last post-baseline value (ANRIND). We need both to be present.
one_lab = one_lab.dropna(subset=["ANRIND", "BNRIND"])


def _week_num(visit):
    """Visit number for a scheduled 'Week N' visit; -1 for anything else."""
    m = re.match(r"\s*Week\s+(\d+)", str(visit))
    return int(m.group(1)) if m else -1


# The ADaM data carries a derived "last observation value" record. Selecting it
# explicitly means the result does NOT depend on the order of rows in the file.
# In pharmaverseadam this record is DTYPE == 'LOV' (labelled AVISIT
# 'POST-BASELINE LAST'). We match on DTYPE when available and fall back to the
# AVISIT label otherwise.
if "DTYPE" in one_lab.columns:
    derived_last = one_lab[one_lab["DTYPE"].astype(str).str.upper() == "LOV"]
else:
    derived_last = one_lab[one_lab["AVISIT"] == "POST-BASELINE LAST"]
# belt-and-braces: if DTYPE was present but empty for this subset, use the label
if len(derived_last) == 0:
    derived_last = one_lab[one_lab["AVISIT"] == "POST-BASELINE LAST"]
derived_last = derived_last.drop_duplicates("USUBJID", keep="last")

# Fallback for any subject without a derived last record: use their latest
# SCHEDULED weekly visit (deterministic via the parsed week number). This
# excludes baseline, unscheduled, and other derived (MIN/MAX) rows.
have = set(derived_last["USUBJID"])
scheduled = one_lab[~one_lab["USUBJID"].isin(have)].copy()
scheduled["_wk"] = scheduled["AVISIT"].map(_week_num)
scheduled = scheduled[scheduled["_wk"] >= 0]
scheduled = (scheduled.sort_values(["USUBJID", "_wk"])
                      .drop_duplicates("USUBJID", keep="last"))

last_record = pd.concat([derived_last, scheduled], ignore_index=True)

order = ["LOW", "NORMAL", "HIGH"]

if len(last_record) == 0:
    st.info("No data to show for this test and group.")
else:
    # count subjects for each (baseline -> last post-baseline) combination
    shift = pd.crosstab(last_record["BNRIND"], last_record["ANRIND"])
    # put the rows/columns in a sensible order
    shift = shift.reindex(index=[o for o in order if o in shift.index],
                          columns=[o for o in order if o in shift.columns],
                          fill_value=0)
    shift.index.name = "Baseline \\ After"
    st.write("Number of subjects moving between categories "
             "(" + str(int(shift.values.sum())) + " subjects):")

    # Cosmetic only: tint each cell in proportion to how many subjects it
    # holds (a light heat-map effect), and make the diagonal — subjects who
    # stayed in the same category — bold with a slightly stronger tint so
    # "no shift" reads at a glance. The values are unchanged.
    def _tint_cells(data):
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        biggest = data.values.max() if data.values.size else 0
        for r in data.index:
            for c in data.columns:
                on_diagonal = str(r).upper() == str(c).upper()
                # opacity scales with the count; diagonal gets a small boost
                share = (data.loc[r, c] / biggest) if biggest > 0 else 0
                opacity = round(0.04 + 0.20 * share + (0.06 if on_diagonal else 0), 3)
                style = f"background-color: rgba(28,110,140,{opacity});"
                if on_diagonal:
                    style += " font-weight: 600;"
                styles.loc[r, c] = style
        return styles

    styled = (shift.style
              .apply(_tint_cells, axis=None)
              .set_properties(**{"text-align": "center"}))
    st.dataframe(styled, use_container_width=True)
    st.caption(
        "Rows are the baseline category, columns are the category at the "
        "subject's last post-baseline value. Numbers on the diagonal are "
        "subjects who stayed in the same category. The subject count reflects "
        "those with a result for this test in this group, which can be fewer "
        "than the full group size."
    )
