# Clinical Trial Data Explorer

A small web app I built to explore clinical trial data in Python. It takes the
CDISC pilot study (Xanomeline vs Placebo, a Phase 3 Alzheimer's study) and lets
you look at the demographics, adverse events, vital signs and lab results
through a simple interface.

I made this because I have been learning clinical trial data standards (SDTM and
ADaM) and I wanted a project where I could work with the actual analysis
datasets and build something interactive on top of them, instead of just running
scripts. It also gave me a reason to practice pandas and Streamlit.

## What it does

The project has two parts.

**1. A script that builds summary tables (`make_outputs.py`)**

This is the programming part. It reads the analysis datasets and builds the kind
of summary tables a clinical programmer would normally make in SAS:

- a demographics / baseline characteristics table (age, sex, race by group)
- a treatment-emergent adverse event summary by system organ class
- a vital signs change-from-baseline table at Week 24

The tables are saved as CSV files in the `outputs/` folder. I basically tried to
reproduce SAS `PROC FREQ` and `PROC MEANS` style outputs using pandas.

**2. A Streamlit app**

The app has a few pages you can move between in the sidebar:

- **Home** – study summary and headline numbers
- **Demographics** – baseline characteristics table and an age chart
- **Safety** – adverse event rates by group, risk difference vs placebo, and a
  chart of the most common event categories
- **Vital Signs** – average change from baseline over the study visits
- **Lab Results** – a shift table showing how subjects moved between
  reference-range categories (Low / Normal / High) from baseline to after
  treatment

## The data

The data comes from the **pharmaverse** project, specifically the
`pharmaverseadam` package. The prepared CSVs in this repository are trimmed copies of open-source pharmaverseadam test datasets under Apache License 2.0, included for educational dashboard use with attribution to the source project. There is no real patient data here, it is all
synthetic test data.

I only keep the safety population (SAFFL = "Y"), which is 254 subjects, and I
trim the files down to the columns and tests the app actually uses so the
repository stays small. The script that does this is `prepare_data.py`. The
smaller files it produces are in the `data/` folder.

Credit: data © CDISC, provided through the pharmaverse packages
(https://github.com/pharmaverse/pharmaverseadam).

## How to run it

```bash
# install the packages
pip install -r requirements.txt

# (optional) rebuild the data files from pharmaverse
python prepare_data.py

# (optional) rebuild the summary tables
python make_outputs.py

# start the app
streamlit run app.py
```

The app opens at http://localhost:8501.

The `data/` folder already has the prepared files, so you only need
`prepare_data.py` if you want to build them again yourself.

## Project layout

```
.
├── app.py                 # home page of the app
├── utils.py               # shared helpers (loading data, colours, stats)
├── pages/                 # one file per app page
│   ├── 1_Demographics.py
│   ├── 2_Safety.py
│   ├── 3_Vital_Signs.py
│   └── 4_Lab_Results.py
├── prepare_data.py        # downloads and trims the pharmaverse data
├── make_outputs.py        # builds the SAS-style summary tables
├── data/                  # the prepared CSV files the app reads
├── outputs/               # the summary tables (CSV)
└── requirements.txt
```

## Known limitations

This is an exploratory dashboard for learning, not a validated or regulatory
output. A few things are deliberately simplified, and worth knowing before you
read too much into the numbers:

- **Exploratory, not a CSR.** The summaries here are dashboard summaries, not
  official clinical study report / regulatory outputs. A real study would use
  pre-specified analysis models and undergo formal validation.
- **Statistics are kept simple** on purpose (means, percentages, and a
  normal-approximation confidence interval for the risk difference).
- **Treatment groups follow convention.** Demographics/baseline are shown by
  *planned* treatment (`TRT01P`, the randomised allocation). Safety analyses
  (adverse events, vital signs, labs) use *actual* treatment (`TRT01A`), which
  is the usual convention. In this pilot 12 subjects planned to Xanomeline High
  Dose actually received Low Dose, so the safety group sizes (86 / 96 / 72)
  genuinely differ from the randomised sizes (86 / 84 / 84).
- **Vital signs use a single body position.** Blood pressure and pulse are
  recorded in several positions per visit. The app analyses the supine record
  ("after lying down for 5 minutes") rather than averaging across positions:
  averaging would mix supine and standing readings and would break the ADaM
  rule that baseline is invariant within a subject/parameter.
- **Lab shift table uses the last post-baseline value.** For each subject the
  shift table compares the baseline reference-range category with the category
  at their last post-baseline value — the ADaM-derived record `DTYPE == 'LOV'`
  (labelled `POST-BASELINE LAST`), selected explicitly rather than by row order.
- **The system-organ-class chart shows the top 10** classes by incidence; the
  full list is in `outputs/t_ae_summary.csv`.
- **Later visits have fewer subjects** because some people left the study
  early. That is real, not a bug — the Xanomeline groups in particular had many
  early discontinuations.
- **`AGEGR1` has two groups** (`18-64`, `>64`) in this pharmaverseadam version,
  which is what the source provides; it is carried through unchanged and is not
  the three-band grouping some other pilot copies use.
- **Data is a pinned snapshot.** `prepare_data.py` is pinned to an immutable
  commit (`ADAM_REF` = pharmaverseadam tag v1.2.0) so a rebuild reproduces the
  files in `data/` exactly.

## License

The application code in this repository is released under the MIT License
(see `LICENSE`). The bundled test data in `data/` consists of trimmed copies of
the CDISC pilot datasets from pharmaverseadam, which remain under their original
Apache License 2.0.

Built by Chetan Dhingra.
