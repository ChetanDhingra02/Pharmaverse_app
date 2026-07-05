"""
Demographics page.

Shows the baseline characteristics table (age, sex, race by treatment
group) and a chart of the age distribution.
"""

import plotly.express as px
import streamlit as st

import utils

# Browser-tab title/icon and wide layout, consistent with the home
# page. Visual only.
st.set_page_config(page_title="Demographics · Clinical Data Explorer", page_icon="🧪",
                   layout="wide")

utils.inject_css()
utils.page_header(
    "Demographics",
    "Baseline characteristics of the subjects in each treatment group.",
    eyebrow="Planned treatment (TRT01P)",
)

adsl = utils.load("adsl")

# --- summary table ---
st.subheader("Baseline characteristics")

sizes = utils.arm_sizes(adsl)
table_rows = []

# age summary
for stat in ["Mean", "SD", "Min", "Max"]:
    row = {"Characteristic": "Age (years)", "": stat}
    for arm in utils.ARMS:
        ages = adsl[adsl["TRT01P"] == arm]["AGE"]
        if stat == "Mean":
            row[arm] = format(ages.mean(), ".1f")
        elif stat == "SD":
            row[arm] = format(ages.std(), ".1f")
        elif stat == "Min":
            row[arm] = str(int(ages.min()))
        else:
            row[arm] = str(int(ages.max()))
    table_rows.append(row)

# sex counts
for value in ["F", "M"]:
    row = {"Characteristic": "Sex", "": value}
    for arm in utils.ARMS:
        arm_data = adsl[adsl["TRT01P"] == arm]
        count = len(arm_data[arm_data["SEX"] == value])
        row[arm] = str(count) + " (" + format(100 * count / sizes[arm], ".1f") + "%)"
    table_rows.append(row)

# race counts
for value in sorted(adsl["RACE"].dropna().unique()):
    row = {"Characteristic": "Race", "": utils.pretty(value)}
    for arm in utils.ARMS:
        arm_data = adsl[adsl["TRT01P"] == arm]
        count = len(arm_data[arm_data["RACE"] == value])
        row[arm] = str(count) + " (" + format(100 * count / sizes[arm], ".1f") + "%)"
    table_rows.append(row)

# Display only: blank repeated group labels so the table reads like a
# standard clinical TLF (the label prints once per group). The values in
# table_rows are unchanged.
st.dataframe(utils.blank_repeats(table_rows, "Characteristic"),
             use_container_width=True, hide_index=True)

# --- age distribution chart ---
st.subheader("Age distribution")
# points="all" additionally shows each subject's age as a jittered dot
# beside its box — same data as the box plot, just displayed in full.
fig = px.box(adsl, x="TRT01P", y="AGE", color="TRT01P",
             color_discrete_map=utils.ARM_COLORS,
             category_orders={"TRT01P": utils.ARMS},
             points="all")
fig.update_traces(marker=dict(size=5, opacity=0.45),
                  line=dict(width=1.6),
                  jitter=0.35, pointpos=-1.6,
                  hovertemplate="Age: %{y}<extra></extra>")
fig.update_layout(showlegend=False, height=400,
                  xaxis_title="", yaxis_title="Age (years)")
utils.style_plotly(fig)
st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)
