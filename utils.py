"""
utils.py

Small helper functions that all the pages use, so I don't repeat the
same code everywhere. It loads the data, keeps the treatment groups and
their colours in one place, and has a couple of simple statistics helpers.

Note on treatment variables:
  * Demographics/baseline are summarised by PLANNED treatment (TRT01P), the
    randomised allocation.
  * Safety analyses (adverse events, vitals, labs) are summarised by ACTUAL
    treatment (TRT01A), which is the usual convention. In this pilot 12
    subjects planned to High Dose actually received Low Dose, so the two
    groupings genuinely differ.
"""

import math
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve the data folder relative to THIS file, not the current working
# directory, so the app works no matter where it is launched from.
DATA_DIR = Path(__file__).resolve().parent / "data"

# treatment groups, always shown in this order
ARMS = ["Placebo", "Xanomeline Low Dose", "Xanomeline High Dose"]

# a colour for each group so charts look the same across pages.
# (These are purely cosmetic. Placebo stays neutral grey, low dose blue,
# high dose warm red — same semantics as before, just a more modern palette.)
ARM_COLORS = {
    "Placebo": "#7C8A99",
    "Xanomeline Low Dose": "#2D6E9E",
    "Xanomeline High Dose": "#C15B45",
}

# short names for charts where the full label is too long
SHORT_NAME = {
    "Placebo": "Placebo",
    "Xanomeline Low Dose": "Xan. Low",
    "Xanomeline High Dose": "Xan. High",
}

# the treatment variable used for safety analyses (actual treatment received)
SAFETY_TRT = "TRT01A"

# small joining words to keep lower-case when tidying UPPER CASE labels
_LOWER_WORDS = {"or", "and", "of", "the", "in", "on", "to", "a", "an"}


@st.cache_data
def load(name):
    """Read one of the CSV files from the data folder."""
    return pd.read_csv(DATA_DIR / (name + ".csv"))


def pretty(text):
    """Tidy an UPPER CASE label into Title Case, keeping small words lower.

    e.g. 'BLACK OR AFRICAN AMERICAN' -> 'Black or African American'.
    """
    words = str(text).split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if i > 0 and lw in _LOWER_WORDS:
            out.append(lw)
        else:
            out.append(lw.capitalize())
    return " ".join(out)


def arm_sizes(adsl, treat_col="TRT01P"):
    """Number of subjects in each treatment group (a dictionary).

    Pass treat_col='TRT01A' for the actual-treatment (safety) denominators.
    """
    sizes = {}
    for arm in ARMS:
        sizes[arm] = len(adsl[adsl[treat_col] == arm])
    return sizes


def teae_incidence(adsl, adae, treat_col=SAFETY_TRT):
    """
    Percent of subjects in each group who had at least one
    treatment-emergent adverse event. Returns a small dataframe.

    Both the numerator and the denominator use the same treatment variable
    (actual treatment by default) so the percentages are internally consistent.
    """
    sizes = arm_sizes(adsl, treat_col)
    teae = adae[adae["TRTEMFL"] == "Y"]

    rows = []
    for arm in ARMS:
        n_total = sizes[arm]
        n_event = teae[teae[treat_col] == arm]["USUBJID"].nunique()
        percent = 100 * n_event / n_total if n_total > 0 else 0
        rows.append({
            "Treatment": arm,
            "Subjects": n_total,
            "With TEAE": n_event,
            "Percent": round(percent, 1),
        })
    return pd.DataFrame(rows)


def risk_difference(n1, total1, n2, total2):
    """
    Risk difference between two groups (group1 minus group2) with a
    simple 95% confidence interval using the normal approximation.
    Returns (difference, low, high) as percentages.

    This Wald interval is deliberately simple; for small or extreme
    proportions it can extend past plausible bounds.
    """
    p1 = n1 / total1
    p2 = n2 / total2
    diff = p1 - p2
    # standard error of the difference in proportions
    se = math.sqrt(p1 * (1 - p1) / total1 + p2 * (1 - p2) / total2)
    low = diff - 1.96 * se
    high = diff + 1.96 * se
    # turn into percentages and round
    return round(diff * 100, 1), round(low * 100, 1), round(high * 100, 1)


# ---------------------------------------------------------------------------
# Presentation helpers (UI only).
#
# Everything below is cosmetic: a small design system so the pages share the
# same fonts, colours, card styling and chart look. None of it changes the
# data, the statistics, or the values shown on screen.
# ---------------------------------------------------------------------------

# Shared palette used by the CSS and the Plotly styler.
INK = "#1E2A38"        # primary text
MUTED = "#5B6B7B"      # secondary text
ACCENT = "#1C6E8C"     # brand accent (matches .streamlit/config.toml)
SURFACE = "#FFFFFF"     # card background
BORDER = "#E4E8EF"      # hairline borders
GRID = "#EDF1F6"        # chart gridlines
FONT_STACK = ('Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", '
              'Roboto, Helvetica, Arial, sans-serif')

# Config passed to st.plotly_chart to keep the chart chrome clean.
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* --- typography ------------------------------------------------------- */
html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
    font-family: %(font)s;
    color: %(ink)s;
}

/* a little more room to breathe at the top of each page */
.block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1180px; }

/* gentle one-time fade/rise when a page loads (skipped for users who
   prefer reduced motion) */
@keyframes pv-fade-up {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.block-container { animation: pv-fade-up .45s ease-out; }
@media (prefers-reduced-motion: reduce) {
    .block-container { animation: none; }
    * { transition: none !important; }
}

h1, h2, h3 { letter-spacing: -0.01em; font-weight: 700; }
h1 { font-size: 1.9rem !important; }
h2 { font-size: 1.35rem !important; }
h3 { font-size: 1.12rem !important; }

/* small accent tick under section headings (st.subheader) */
[data-testid="stHeadingWithActionElements"] h3 {
    padding-bottom: .3rem;
    position: relative;
}
[data-testid="stHeadingWithActionElements"] h3::after {
    content: "";
    position: absolute;
    left: 0; bottom: 0;
    width: 26px; height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, %(accent)s, rgba(28,110,140,0.25));
}

/* --- page banner (rendered via utils.page_header) -------------------- */
.pv-banner {
    background: linear-gradient(120deg, #1C6E8C 0%%, #17566d 55%%, #123f52 100%%);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.4rem;
    color: #EAF2F6;
    box-shadow: 0 10px 30px -14px rgba(18,63,82,0.55);
    position: relative;
    overflow: hidden;
}
/* faint vital-sign trace in the banner corner. decorative only. */
.pv-banner::after {
    content: "";
    position: absolute;
    right: -20px; top: 0; bottom: 0;
    width: 420px;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 140"><polyline fill="none" stroke="rgba(255,255,255,0.13)" stroke-width="2" stroke-linejoin="round" points="0,70 60,70 78,70 88,52 98,88 108,26 120,108 132,62 144,70 210,70 228,70 238,54 248,86 258,30 270,104 282,64 294,70 420,70"/></svg>');
    background-repeat: no-repeat;
    background-position: right center;
    background-size: contain;
    pointer-events: none;
}
.pv-banner h1 { color: #FFFFFF; margin: 0 0 .2rem 0; font-size: 1.75rem !important; }
.pv-banner p { color: #C6DCE6; margin: 0; font-size: .95rem; line-height: 1.45;
               max-width: 46rem; position: relative; z-index: 1; }
.pv-eyebrow {
    display: inline-block; text-transform: uppercase; letter-spacing: .14em;
    font-size: .68rem; font-weight: 600; color: #9FD0DE; margin-bottom: .55rem;
}

/* --- metric cards with hover lift ------------------------------------ */
[data-testid="stMetric"] {
    background: %(surface)s;
    border: 1px solid %(border)s;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    position: relative;
    overflow: hidden;
}
/* thin accent bar that slides in along the top on hover */
[data-testid="stMetric"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, %(accent)s, #4FA3C2);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform .22s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px -16px rgba(28,110,140,0.45);
    border-color: #BFD8E2;
}
[data-testid="stMetric"]:hover::before { transform: scaleX(1); }
[data-testid="stMetricValue"] {
    font-weight: 700; color: %(ink)s;
    font-variant-numeric: tabular-nums;
}
[data-testid="stMetricLabel"] { color: %(muted)s; font-weight: 500; }
[data-testid="stMetricLabel"] p { font-size: .82rem; }

/* --- dataframes: soft card frame ------------------------------------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid %(border)s;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
    transition: box-shadow .18s ease, border-color .18s ease;
}
[data-testid="stDataFrame"]:hover {
    box-shadow: 0 8px 22px -16px rgba(16,24,40,0.30);
    border-color: #D3DCE6;
}

/* --- plotly charts sit on their own subtle card ---------------------- */
[data-testid="stPlotlyChart"] {
    background: %(surface)s;
    border: 1px solid %(border)s;
    border-radius: 14px;
    padding: .55rem .4rem .3rem .4rem;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
    transition: box-shadow .18s ease, border-color .18s ease;
}
[data-testid="stPlotlyChart"]:hover {
    box-shadow: 0 12px 26px -18px rgba(16,24,40,0.35);
    border-color: #D3DCE6;
}

/* --- inputs ---------------------------------------------------------- */
[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border-color: %(border)s !important;
    transition: border-color .15s ease, box-shadow .15s ease;
}
[data-baseweb="select"] > div:hover { border-color: #A9C6D3 !important; }
[data-baseweb="select"] > div:focus-within {
    border-color: %(accent)s !important;
    box-shadow: 0 0 0 3px rgba(28,110,140,0.15) !important;
}
.stSelectbox label p { color: %(muted)s; font-weight: 500; font-size: .85rem; }

/* --- sidebar --------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: #FBFCFE;
    border-right: 1px solid %(border)s;
}
/* small section label above the page list */
[data-testid="stSidebarNav"]::before {
    content: "Study explorer";
    display: block;
    padding: .4rem 1.3rem .35rem 1.3rem;
    text-transform: uppercase;
    letter-spacing: .13em;
    font-size: .66rem;
    font-weight: 600;
    color: %(muted)s;
}
[data-testid="stSidebarNavLink"] {
    border-radius: 8px;
    transition: background .15s ease, transform .15s ease, box-shadow .15s ease;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(28,110,140,0.08);
    transform: translateX(2px);
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(28,110,140,0.10);
    box-shadow: inset 3px 0 0 %(accent)s;
}
[data-testid="stSidebarNavLink"][aria-current="page"] p {
    color: %(accent)s;
    font-weight: 600;
}

/* --- keyboard focus -------------------------------------------------- */
a:focus-visible, button:focus-visible {
    outline: 2px solid %(accent)s;
    outline-offset: 2px;
    border-radius: 6px;
}

/* --- dividers & captions --------------------------------------------- */
hr { border-color: %(border)s; }
[data-testid="stCaptionContainer"], .stCaption { color: %(muted)s; }

/* --- tidy up default chrome ------------------------------------------ */
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
</style>
""" % {"font": FONT_STACK, "ink": INK, "muted": MUTED, "accent": ACCENT,
       "surface": SURFACE, "border": BORDER}


def blank_repeats(rows, column):
    """Return a copy of a list of row-dicts where consecutive repeats of
    one column are blanked out for display.

    This mimics how clinical TLFs print grouped tables (the group label
    appears once, on its first row). Purely cosmetic — the underlying
    values and every other column are untouched.
    """
    out = []
    previous = object()  # sentinel that never equals a real value
    for row in rows:
        row = dict(row)  # shallow copy so the caller's data is unchanged
        if row.get(column) == previous:
            row[column] = ""
        else:
            previous = row.get(column)
        out.append(row)
    return out


def inject_css():
    """Inject the shared stylesheet. Call once, at the top of every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title, subtitle="", eyebrow="Clinical Data Explorer"):
    """Render a consistent gradient banner instead of a plain st.title.

    Purely visual — it just displays the text it is given.
    """
    eyebrow_html = f'<span class="pv-eyebrow">{eyebrow}</span>' if eyebrow else ""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="pv-banner">{eyebrow_html}'
        f"<h1>{title}</h1>{sub_html}</div>",
        unsafe_allow_html=True,
    )


def style_plotly(fig, hovermode="closest"):
    """Apply the shared chart look to a Plotly figure and return it.

    Only touches cosmetics (fonts, gridlines, hover box, spacing, legend,
    rounded bars). It never changes the traces or the data behind them, and
    it leaves each chart's own height / axis titles / legend visibility alone.
    """
    fig.update_layout(
        font=dict(family=FONT_STACK, size=13, color=INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode=hovermode,
        hoverlabel=dict(bgcolor="white", bordercolor=BORDER,
                        font_size=12, font_family=FONT_STACK),
        margin=dict(l=16, r=16, t=48, b=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title_text="",
                    font=dict(size=12, color=MUTED)),
        barcornerradius=6,
        colorway=list(ARM_COLORS.values()),
    )
    # Light, unobtrusive axes. Only affects axes that already show a grid,
    # so categorical axes stay clean.
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER,
                     ticks="outside", tickcolor=BORDER, tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER,
                     tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED, size=12))
    return fig
