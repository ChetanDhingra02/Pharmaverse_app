"""
Vital Signs page.

Lets you pick a vital sign and see the average change from baseline over
the study visits for each treatment group.
"""

import plotly.express as px
import streamlit as st

import utils

# Browser-tab title/icon and wide layout, consistent with the home
# page. Visual only.
st.set_page_config(page_title="Vital Signs · Clinical Data Explorer", page_icon="🧪",
                   layout="wide")

utils.inject_css()
utils.page_header(
    "Vital Signs",
    "Average change from baseline over time, by treatment group.",
    eyebrow="Actual treatment (TRT01A)",
)

advs = utils.load("advs")

# let the user pick which vital sign to look at
params = advs[["PARAMCD", "PARAM"]].drop_duplicates()
labels = params["PARAM"].tolist()
choice = st.selectbox("Vital sign", labels)

# keep only the chosen parameter
one_param = advs[advs["PARAM"] == choice]
# keep scheduled post-baseline visits only. There is no separate "Baseline"
# row in the trimmed data, but we also drop derived non-scheduled visits such
# as "End of Treatment" (AVISITN 99) so the x-axis stays in true time order.
one_param = one_param[one_param["AVISIT"] != "Baseline"]
one_param = one_param[one_param["AVISITN"] < 90]

# average change from baseline for each visit and treatment group
# (vitals are a safety endpoint, so group by actual treatment received)
TRT = utils.SAFETY_TRT
summary = (one_param.groupby(["AVISIT", "AVISITN", TRT])["CHG"]
           .mean().reset_index())
summary = summary.sort_values("AVISITN")

fig = px.line(summary, x="AVISIT", y="CHG", color=TRT,
              markers=True, color_discrete_map=utils.ARM_COLORS,
              category_orders={TRT: utils.ARMS})
fig.update_traces(line=dict(width=2.6),
                  marker=dict(size=7, line=dict(width=1.5, color="white")),
                  hovertemplate="%{y:.2f}<extra></extra>")
fig.add_hline(y=0, line_dash="dot", line_color="#9AA7B4", line_width=1.4)
fig.update_layout(height=450, xaxis_title="Visit",
                  yaxis_title="Mean change from baseline",
                  legend_title="")
utils.style_plotly(fig, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)

st.caption(
    "Change from baseline is the value at the visit minus the subject's "
    "baseline value. Fewer subjects have later visits because some left the "
    "study early."
)
