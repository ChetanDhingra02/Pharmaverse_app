"""
Safety page.

Shows how common adverse events were in each treatment group. You can
look at the overall rate, the rate by system organ class, and the risk
difference of each Xanomeline group compared with placebo.

Safety is summarised by ACTUAL treatment received (TRT01A), the usual
convention. In this pilot that differs from planned treatment for 12
subjects, so the group sizes here are not the same as on the demographics
page (which uses randomised/planned treatment).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils

TRT = utils.SAFETY_TRT  # actual treatment

# Browser-tab title/icon and wide layout, consistent with the home
# page. Visual only.
st.set_page_config(page_title="Safety · Clinical Data Explorer", page_icon="🧪",
                   layout="wide")

utils.inject_css()
utils.page_header(
    "Safety — Adverse Events",
    "Treatment-emergent adverse events (TEAEs) by actual treatment received. "
    "Each subject is counted once per category.",
    eyebrow="Actual treatment (TRT01A)",
)

adsl = utils.load("adsl")
adae = utils.load("adae")
sizes = utils.arm_sizes(adsl, TRT)

# --- overall incidence ---
st.subheader("Subjects with any treatment-emergent adverse event")
incidence = utils.teae_incidence(adsl, adae, TRT)

cols = st.columns(3)
for i, arm in enumerate(utils.ARMS):
    row = incidence[incidence["Treatment"] == arm].iloc[0]
    cols[i].metric(utils.SHORT_NAME[arm],
                   str(row["Percent"]) + "%",
                   str(int(row["With TEAE"])) + " of " + str(int(row["Subjects"])))

# --- risk difference vs placebo ---
st.subheader("Risk difference vs placebo")
st.write(
    "The difference in the percent of subjects with any TEAE, compared with "
    "placebo, with a 95% confidence interval."
)

placebo = incidence[incidence["Treatment"] == "Placebo"].iloc[0]
rd_rows = []
for arm in ["Xanomeline Low Dose", "Xanomeline High Dose"]:
    g = incidence[incidence["Treatment"] == arm].iloc[0]
    diff, low, high = utils.risk_difference(
        int(g["With TEAE"]), int(g["Subjects"]),
        int(placebo["With TEAE"]), int(placebo["Subjects"]))
    rd_rows.append({
        "Comparison": arm + " vs Placebo",
        "Risk difference (%)": diff,
        "95% CI low": low,
        "95% CI high": high,
    })

# --- forest plot (display only) ---
# Draws exactly the numbers in rd_rows (point estimate + CI) in the usual
# forest-plot layout: a marker with a horizontal CI whisker per comparison
# and a dashed reference line at zero. No values are recomputed.
fig = go.Figure()
for row in reversed(rd_rows):  # reversed so the first comparison sits on top
    arm_name = row["Comparison"].replace(" vs Placebo", "")
    diff = row["Risk difference (%)"]
    low, high = row["95% CI low"], row["95% CI high"]
    fig.add_trace(go.Scatter(
        x=[diff], y=[row["Comparison"]],
        mode="markers",
        marker=dict(size=13, color=utils.ARM_COLORS[arm_name],
                    line=dict(width=2, color="white")),
        error_x=dict(type="data", symmetric=False,
                     array=[high - diff], arrayminus=[diff - low],
                     thickness=2.4, width=7,
                     color=utils.ARM_COLORS[arm_name]),
        hovertemplate=(row["Comparison"] + "<br>Risk difference: "
                       + str(diff) + "%<br>95% CI: " + str(low) + "% to "
                       + str(high) + "%<extra></extra>"),
        showlegend=False,
    ))
fig.add_vline(x=0, line_dash="dot", line_color="#9AA7B4", line_width=1.4,
              annotation_text="No difference", annotation_position="top",
              annotation_font=dict(size=11, color="#5B6B7B"))
fig.update_layout(height=240, xaxis_title="Risk difference vs placebo (%)",
                  yaxis_title="")
utils.style_plotly(fig)
fig.update_yaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)

st.dataframe(rd_rows, use_container_width=True, hide_index=True)

# --- incidence by system organ class ---
st.subheader("Treatment-emergent adverse events by system organ class")

teae = adae[adae["TRTEMFL"] == "Y"]

# build a long table: one row per SOC per arm with the percent
soc_rows = []
for soc in sorted(teae["AESOC"].dropna().unique()):
    soc_data = teae[teae["AESOC"] == soc]
    for arm in utils.ARMS:
        n_event = soc_data[soc_data[TRT] == arm]["USUBJID"].nunique()
        percent = 100 * n_event / sizes[arm] if sizes[arm] > 0 else 0
        soc_rows.append({"SOC": utils.pretty(soc), "Treatment": arm,
                         "Percent": round(percent, 1)})

soc_df = pd.DataFrame(soc_rows)

# only show the more common SOCs so the chart isn't too tall
top_socs = (soc_df.groupby("SOC")["Percent"].max()
            .sort_values(ascending=False).head(10).index.tolist())
soc_df = soc_df[soc_df["SOC"].isin(top_socs)]

fig = px.bar(soc_df, x="Percent", y="SOC", color="Treatment",
             barmode="group", color_discrete_map=utils.ARM_COLORS,
             category_orders={"Treatment": utils.ARMS, "SOC": top_socs})
fig.update_traces(
    hovertemplate="%{y}<br>%{fullData.name}: %{x}%<extra></extra>")
fig.update_layout(height=500, xaxis_title="Percent of subjects", yaxis_title="")
utils.style_plotly(fig)
st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)
st.caption(
    "Chart shows the 10 system organ classes with the highest incidence in any "
    "group. The full list of all system organ classes is in "
    "outputs/t_ae_summary.csv."
)
