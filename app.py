"""
app.py - home page

This is the main page of the app. It shows a short summary of the study
and a few headline numbers. The other pages (demographics, safety, vital
signs, lab results) are in the pages/ folder and show up in the sidebar.

Run the app with:  streamlit run app.py
"""

import plotly.express as px
import streamlit as st

import utils

st.set_page_config(page_title="Clinical Data Explorer", page_icon="🧪",
                   layout="wide")

utils.inject_css()

# load the data
adsl = utils.load("adsl")
adae = utils.load("adae")

# --- header ---
utils.page_header(
    "Clinical Trial Data Explorer",
    "Xanomeline vs Placebo — Phase 3 Alzheimer's study (CDISC pilot data)",
    eyebrow="Pharmaverse · Safety population",
)

st.write(
    "This is a small app I built to explore clinical trial data. It uses the "
    "open-source CDISC pilot datasets from the pharmaverse project and lets you "
    "look at the demographics, adverse events, vital signs and lab results for "
    "the study. Use the sidebar to move between the pages."
)

st.write("")

# --- headline numbers ---
sizes = utils.arm_sizes(adsl)
incidence = utils.teae_incidence(adsl, adae)
teae_records = adae[adae["TRTEMFL"] == "Y"]
overall_teae = teae_records["USUBJID"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Subjects", len(adsl))
c2.metric("Treatment groups", len(utils.ARMS))
c3.metric("Subjects with a TEAE", overall_teae)
c4.metric("TEAE records", len(teae_records))

st.write("")

# --- two simple charts side by side ---
left, right = st.columns(2)

with left:
    st.subheader("Subjects per group")
    counts = adsl["TRT01P"].value_counts().reindex(utils.ARMS).reset_index()
    counts.columns = ["Treatment", "Subjects"]
    fig = px.bar(counts, x="Treatment", y="Subjects", color="Treatment",
                 color_discrete_map=utils.ARM_COLORS, text="Subjects")
    fig.update_traces(textposition="outside", textfont_size=13,
                      cliponaxis=False,
                      hovertemplate="%{x}<br>Subjects: %{y}<extra></extra>")
    fig.update_layout(showlegend=False, height=350,
                      xaxis_title="", yaxis_title="Subjects")
    utils.style_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)

with right:
    st.subheader("Subjects with any TEAE (%)")
    fig = px.bar(incidence, x="Treatment", y="Percent", color="Treatment",
                 color_discrete_map=utils.ARM_COLORS, text="Percent")
    fig.update_traces(texttemplate="%{text}%", textposition="outside",
                      textfont_size=13, cliponaxis=False,
                      hovertemplate="%{x}<br>%{y}% of subjects<extra></extra>")
    fig.update_layout(showlegend=False, height=350,
                      xaxis_title="", yaxis_title="Percent of subjects")
    utils.style_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config=utils.PLOTLY_CONFIG)
    st.caption(
        "Subject counts are by planned treatment (randomised allocation); "
        "adverse-event rates are by actual treatment received (TRT01A), which "
        "is the usual safety convention."
    )

st.divider()
st.caption(
    "Data source: CDISC pilot study data from the pharmaverse packages "
    "(pharmaverseadam), which are open source. This app is a personal learning "
    "project and is not a regulatory output."
)
