"""
Builds the step-by-step procedure document as a PDF.

It writes an HTML file and then uses headless Chrome to print it to PDF,
so the tables and the figures come out looking properly typeset.

Run:  python notes/make_procedure_pdf.py
"""

import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))
import config  # noqa: E402

OUT_PDF = PROJECT / "Nanoparticle_Toxicity_Project_Procedure.pdf"
OUT_HTML = PROJECT / "notes" / "procedure.html"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    for name in ["chrome", "google-chrome", "msedge"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def img(name, width="100%"):
    """Embed a figure as base64 so the HTML is self contained."""
    path = config.FIGURES_DIR / name
    if not path.exists():
        return f'<p class="missing">[figure {name} not found - run python run_all.py]</p>'
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'<img src="data:image/png;base64,{data}" style="width:{width}">'


def df_to_html(df, index=False, decimals=3):
    out = df.copy()
    for col in out.select_dtypes("number").columns:
        out[col] = out[col].round(decimals)
    return out.to_html(index=index, border=0, na_rep="&ndash;", escape=False)


# ------------------------------------------------------------------
# Pull the real numbers out of the results folder
# ------------------------------------------------------------------
metrics = pd.read_csv(config.METRICS_FILE)
lomo = pd.read_csv(config.RESULTS_DIR / "leave_one_material_out.csv")
importance = pd.read_csv(config.RESULTS_DIR / "feature_importance.csv")
importance.columns = ["Feature", "Importance"]
correlation = pd.read_csv(config.RESULTS_DIR / "feature_correlation.csv")
correlation.columns = ["Feature", "Correlation with toxicity"]
materials = pd.read_csv(config.MATERIAL_FILE)
clean = pd.read_csv(config.CLEAN_FILE)
raw = pd.read_csv(config.RAW_FILE, sep="\t")

n_raw = len(raw)
n_clean = len(clean)
n_toxic = int(clean[config.TARGET_NUMERIC].sum())
pct_toxic = n_toxic / n_clean * 100

best = metrics.sort_values("F1", ascending=False).iloc[0]

by_material = (
    clean.groupby("NPs")[config.TARGET_NUMERIC]
    .agg(Samples="size", Toxic="sum")
    .reset_index()
    .rename(columns={"NPs": "Material"})
)
by_material["% toxic"] = (by_material["Toxic"] / by_material["Samples"] * 100).round(1)
by_material = by_material.sort_values("% toxic", ascending=False)

top_corr = correlation.head(8)
top_imp = importance.head(10)

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
/* This is a print document, so it is always light. Without this it
   picks up the browser's dark mode and comes out unreadable. */
:root { color-scheme: light; }
html { background: #ffffff; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.55;
  color: #1a1a1a; background: #ffffff; margin: 0;
}
h1 { font-size: 20pt; color: #10365c; margin: 0 0 4px 0; }
h2 {
  font-size: 14pt; color: #10365c; margin: 26px 0 8px 0;
  padding-bottom: 4px; border-bottom: 2px solid #10365c;
  page-break-after: avoid;
}
h3 {
  font-size: 11.5pt; color: #1d4e7e; margin: 18px 0 6px 0;
  page-break-after: avoid;
}
h4 { font-size: 10.5pt; margin: 12px 0 4px 0; color: #333; }
p { margin: 6px 0; text-align: justify; }
code {
  font-family: Consolas, "Courier New", monospace; font-size: 9pt;
  background: #eef2f6; padding: 1px 4px; border-radius: 3px;
}
pre {
  font-family: Consolas, "Courier New", monospace; font-size: 8.5pt;
  background: #f6f8fa; border: 1px solid #d8dee4; border-left: 3px solid #10365c;
  padding: 8px 10px; border-radius: 4px; overflow-x: auto;
  white-space: pre-wrap; word-wrap: break-word; line-height: 1.4;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 8.5pt; }
table {
  border-collapse: collapse; width: 100%; margin: 10px 0;
  font-size: 9pt; page-break-inside: avoid;
}
th {
  background: #10365c; color: #fff; text-align: left;
  padding: 5px 7px; font-weight: 600;
}
td { padding: 4px 7px; border-bottom: 1px solid #dde3ea; }
tr:nth-child(even) td { background: #f7f9fb; }
img { display: block; margin: 10px auto; max-width: 100%; page-break-inside: avoid; }
.cover { text-align: center; padding-top: 55mm; page-break-after: always; }
.cover h1 { font-size: 26pt; line-height: 1.25; border: none; }
.cover .sub { font-size: 13pt; color: #444; margin-top: 10px; }
.cover .rule { width: 70mm; height: 3px; background: #10365c; margin: 22px auto; }
.cover table { width: 78%; margin: 26px auto; font-size: 11pt; }
.badge {
  display: inline-block; background: #10365c; color: #fff;
  padding: 3px 12px; border-radius: 12px; font-size: 9.5pt; margin-top: 14px;
}
.step {
  background: #10365c; color: #fff; display: inline-block;
  width: 24px; height: 24px; line-height: 24px; text-align: center;
  border-radius: 50%; font-size: 10pt; font-weight: 700; margin-right: 7px;
}
.note {
  background: #fff8e6; border-left: 4px solid #e0a800;
  padding: 8px 12px; margin: 10px 0; font-size: 9.5pt;
  page-break-inside: avoid;
}
.warn {
  background: #fdeceb; border-left: 4px solid #c0392b;
  padding: 8px 12px; margin: 10px 0; font-size: 9.5pt;
  page-break-inside: avoid;
}
.ok {
  background: #eaf6ec; border-left: 4px solid #2e7d32;
  padding: 8px 12px; margin: 10px 0; font-size: 9.5pt;
  page-break-inside: avoid;
}
.caption {
  text-align: center; font-size: 8.5pt; color: #666;
  font-style: italic; margin: -4px 0 12px 0;
}
.pagebreak { page-break-before: always; }
.missing { color: #c0392b; font-size: 9pt; }
ul, ol { margin: 6px 0 6px 0; padding-left: 20px; }
li { margin: 3px 0; }
.small { font-size: 9pt; color: #555; }
"""


def build_html():
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Project Procedure</title>
<style>{CSS}</style></head><body>

<!-- ============ COVER ============ -->
<div class="cover">
  <h1>Nanoparticle Toxicity Prediction<br>Using Data-Driven Methods</h1>
  <div class="rule"></div>
  <div class="sub">Step-by-Step Project Procedure Report</div>
  <table>
    <tr><th>Team Member</th><th>Enrolment No.</th></tr>
    <tr><td>Pratham Joshi</td><td>KU2507U0361</td></tr>
    <tr><td>Divyansh Khatri</td><td>KU2507U0188</td></tr>
    <tr><td>Dhyey Bhatt</td><td>KU2507U0138</td></tr>
    <tr><td>Jinay Shah</td><td>KU2507U0070</td></tr>
  </table>
  <div class="badge">Final model: {best['Model']} &nbsp;|&nbsp; Accuracy {best['Accuracy']:.1%} &nbsp;|&nbsp; F1 {best['F1']:.3f}</div>
</div>

<!-- ============ AIM ============ -->
<h2>1. Aim of the Project</h2>
<p>
Nanoparticles are widely used in drug delivery because they are extremely small,
have a very large surface area for their size, and can be directed towards
specific cells and tissues. The problem is that these very same properties can
also make them toxic to healthy cells. Testing every newly designed particle in
a laboratory is slow and expensive, so it is useful to be able to screen a
particle computationally before it ever reaches the lab bench.
</p>
<p>
The aim of this project is therefore to build a working machine learning system
that takes the measurable physicochemical properties of a nanoparticle and
classifies it as <strong>TOXIC</strong> or <strong>NON-TOXIC</strong>.
</p>

<h3>Objectives</h3>
<ol>
  <li>Collect a real, published nanoparticle toxicity dataset.</li>
  <li>Understand, clean and preprocess the data.</li>
  <li>Explore the data and identify which properties influence toxicity.</li>
  <li>Train and compare five machine learning classifiers.</li>
  <li>Evaluate them properly and select the best one.</li>
  <li>Build a prediction system that anybody can use.</li>
  <li>Test the whole thing and fix whatever is broken.</li>
</ol>

<h2>2. Software and Libraries Used</h2>
<table>
<tr><th>Component</th><th>What we used</th><th>Why</th></tr>
<tr><td>Language</td><td>Python 3.12</td><td>Standard for data science work</td></tr>
<tr><td>Data handling</td><td>pandas, numpy</td><td>Reading, cleaning and reshaping the dataset</td></tr>
<tr><td>Machine learning</td><td>scikit-learn</td><td>All five classifiers, scaling, metrics, cross validation</td></tr>
<tr><td>Plots</td><td>matplotlib, seaborn</td><td>Histograms, box plots, heatmap, ROC curves</td></tr>
<tr><td>Saving the model</td><td>joblib</td><td>Storing the trained pipeline to a file</td></tr>
<tr><td>Web app</td><td>Streamlit</td><td>Front end for the final prediction system</td></tr>
<tr><td>Testing</td><td>pytest</td><td>The bug sweep at the end</td></tr>
</table>

<div class="pagebreak"></div>

<!-- ============ PROCEDURE ============ -->
<h2>3. Step-by-Step Procedure</h2>
<p>
We followed the fifteen step research workflow. Each step below explains what we
did, how we did it, and what came out of it.
</p>

<h3><span class="step">1</span>Define the Research Problem</h3>
<p>
We first fixed exactly what the model should answer. We settled on a
<strong>binary classification problem</strong>: given the properties of a
nanoparticle and the exposure conditions, predict whether it will be toxic to
cells or not. We deliberately did not attempt to predict the exact cell
viability percentage, because a yes/no toxicity flag is what is actually useful
for early screening, and it is a much more achievable target with a small
dataset.
</p>

<h3><span class="step">2</span>Literature Review</h3>
<p>
We read around the topic of nanotoxicity and machine learning based prediction
(nano-QSAR). The main things we took away were:
</p>
<ul>
  <li>Toxicity does not depend on any single property. Size, charge, dose and
      exposure time act together, so a multivariate model makes sense.</li>
  <li>Published nanotoxicity datasets are small and heavily imbalanced, so
      accuracy on its own is a misleading metric.</li>
  <li>The chemistry of the material itself (which metal oxide it is) is often a
      stronger signal than the particle geometry.</li>
</ul>
<p>
This review is also how we found our dataset, from the NanoTox study.
</p>

<h3><span class="step">3</span>Dataset Collection</h3>
<p>
We used the <strong>NanoTox metal-oxide nanoparticle dataset</strong>, which is
published openly alongside a peer reviewed study.
</p>
<table>
<tr><th>Item</th><th>Detail</th></tr>
<tr><td>Source repository</td><td>github.com/NanoTox/ToxicityModel (file <code>dataset.txt</code>)</td></tr>
<tr><td>Reference</td><td><em>NanoTox: Development of a parsimonious in silico model for toxicity assessment of metal-oxide nanoparticles using physicochemical features</em>, bioRxiv 2021, doi:10.1101/2021.02.22.432301</td></tr>
<tr><td>Records</td><td>{n_raw} experiments</td></tr>
<tr><td>Columns</td><td>{raw.shape[1]}</td></tr>
<tr><td>Materials</td><td>Al<sub>2</sub>O<sub>3</sub>, CuO, Fe<sub>2</sub>O<sub>3</sub>, TiO<sub>2</sub>, ZnO</td></tr>
<tr><td>Cell lines</td><td>{raw['Cellline'].nunique()} different cell lines</td></tr>
<tr><td>Format</td><td>Tab separated text</td></tr>
</table>
<p>
Rather than downloading it by hand we wrote <code>src/download_data.py</code> so
that the whole project can be reproduced from an empty folder:
</p>
<pre><code>python src/download_data.py

Downloading from https://raw.githubusercontent.com/NanoTox/ToxicityModel/master/dataset.txt ...
Saved nanotox_dataset.tsv (58.4 KB)</code></pre>

<h3><span class="step">4</span>Data Understanding</h3>
<p>
Before changing anything we simply looked at the data and printed a report of
what we had. This is done by <code>describe_data()</code> in
<code>src/preprocess.py</code>.
</p>
<pre><code>Rows: {n_raw}   Columns: {raw.shape[1]}
Missing values per column:
  No missing values found.
Duplicate rows: 6
Target variable distribution:
  nonToxic   405  (83.9%)
  Toxic       78  (16.1%)
  -&gt; The dataset is imbalanced, so accuracy alone is not enough.</code></pre>
<p>What we learned at this stage:</p>
<ul>
  <li>There are no missing values, which is unusually clean.</li>
  <li>The classes are badly imbalanced, roughly 84% to 16%.</li>
  <li>There are a handful of exactly duplicated rows.</li>
  <li>There is a <code>viability</code> column sitting right next to the
      <code>class</code> column, which we flagged as suspicious.</li>
</ul>

<div class="warn">
<strong>Important observation.</strong> The <code>class</code> label
(Toxic / nonToxic) was created by the dataset authors <em>from</em> the
<code>viability</code> value. So <code>viability</code> is not an input
property, it is the answer in disguise. If we had used it as a feature every
model would have scored close to 100% and the project would have proved
nothing. We excluded it from the very beginning.
</div>

<h3><span class="step">5</span>Data Preprocessing</h3>
<p>This is where the data was actually cleaned. The steps, in order:</p>
<ol>
  <li><strong>Remove duplicate rows</strong> &ndash; 6 exact duplicates removed.</li>
  <li><strong>Encode the target</strong> &ndash; <code>Toxic</code> becomes 1,
      <code>nonToxic</code> becomes 0.</li>
  <li><strong>Drop the leaking column</strong> &ndash; <code>viability</code> is
      removed and listed in <code>config.LEAKY_COLS</code>.</li>
  <li><strong>Force numeric types</strong> and fill any missing numeric value
      with the column median. There were none here, but the step stays so the
      pipeline does not break on a different dataset.</li>
  <li><strong>Merge repeated experiments</strong> &ndash; explained below.</li>
  <li><strong>Train/test split</strong> &ndash; 75% train, 25% test, stratified
      so both halves keep the same toxic ratio.</li>
  <li><strong>Feature scaling</strong> &ndash; <code>StandardScaler</code>, but
      placed <em>inside</em> a scikit-learn <code>Pipeline</code> so it is only
      ever fitted on the training fold.</li>
</ol>

<div class="warn">
<strong>The problem we nearly missed.</strong> Once <code>viability</code> is
removed, a lot of rows become <em>identical</em>. The raw file records the same
experiment (same particle, same dose, same cell line) several times, each with a
slightly different measured viability. With those repeats present, the random
train/test split was putting copies of the same experiment into both the
training set and the test set, which meant our test scores were not honest.
<br><br>
We fixed this with <code>collapse_replicates()</code>, which keeps one row per
unique experiment. Where the repeats disagreed on the label we took the
majority, and an exact tie counts as toxic, because for a safety tool a false
warning is safer than a false all-clear.
</div>

<pre><code>Removed 6 duplicate rows.
Encoded target: Toxic = 1, nonToxic = 0
Dropped leaky column(s): ['viability']
Merged 122 repeated experiments (477 rows -&gt; 355 unique experiments).
  11 of them had repeats that disagreed on the label - majority vote used.
Final clean shape: (355, 24)</code></pre>

<table>
<tr><th>Stage</th><th>Rows</th></tr>
<tr><td>Raw dataset as downloaded</td><td>{n_raw}</td></tr>
<tr><td>After removing exact duplicates</td><td>477</td></tr>
<tr><td>After merging repeated experiments</td><td><strong>{n_clean}</strong></td></tr>
<tr><td>Toxic samples in the final data</td><td>{n_toxic} ({pct_toxic:.1f}%)</td></tr>
</table>

<h4>How the columns were divided</h4>
<p>
Thirteen of the descriptors are pure chemistry and are <em>the same for every
row of a material</em> (Al<sub>2</sub>O<sub>3</sub> always has the same
molecular weight). We separated these from the six properties a user can
actually measure, so that the final app only has to ask for six numbers and can
look up the rest itself.
</p>
<table>
<tr><th>Group</th><th>Columns</th></tr>
<tr><td>Entered by the user (6)</td><td><code>coresize</code>, <code>hydrosize</code>, <code>surfcharge</code>, <code>surfarea</code>, <code>Expotime</code>, <code>dosage</code></td></tr>
<tr><td>Looked up from the material (13)</td><td><code>Hsf</code>, <code>Ec</code>, <code>Ev</code>, <code>MeO</code>, <code>enthalpy</code>, <code>ratio</code>, <code>e</code>, <code>esum</code>, <code>esumbyo</code>, <code>MW</code>, <code>NMetal</code>, <code>NOxygen</code>, <code>ox</code></td></tr>
<tr><td>Categorical (1)</td><td><code>Celltype</code> (Cancer / Normal)</td></tr>
<tr><td>Target</td><td><code>class</code> &rarr; <code>toxic</code> (1 / 0)</td></tr>
<tr><td>Never used</td><td><code>viability</code> (leaks the answer)</td></tr>
</table>

<h4>The material lookup table that was generated</h4>
{df_to_html(materials, decimals=3)}

<div class="pagebreak"></div>

<h3><span class="step">6</span>Exploratory Data Analysis</h3>
<p>
We then plotted the data to see what it actually looks like. All of this is in
<code>src/eda.py</code> and the figures are saved to <code>results/figures/</code>.
</p>

{img("01_class_balance.png", "62%")}
<div class="caption">Figure 1 &ndash; Class balance. The dataset is clearly imbalanced.</div>

{img("02_histograms.png")}
<div class="caption">Figure 2 &ndash; Distribution of the six measurable properties.</div>

{img("03_toxic_vs_nontoxic.png")}
<div class="caption">Figure 3 &ndash; Toxic versus non-toxic groups compared property by property.</div>

{img("04_scatter_plots.png")}
<div class="caption">Figure 4 &ndash; Scatter plots showing how the two classes separate.</div>

{img("05_correlation_heatmap.png", "85%")}
<div class="caption">Figure 5 &ndash; Correlation heatmap of all numeric features.</div>

<h3><span class="step">7</span>Feature Analysis</h3>
<p>
From the correlation analysis, these are the features most strongly related to
toxicity:
</p>
{df_to_html(top_corr, decimals=3)}
<p>
The striking result is that the strongest signals are all
<strong>material-level chemistry descriptors</strong> &ndash; the metal to
oxygen ratio, the enthalpy, the oxidation state &ndash; rather than the particle
geometry. In plain language, <em>what the particle is made of matters more than
how big it is</em>.
</p>

{img("06_toxicity_by_material.png", "62%")}
<div class="caption">Figure 6 &ndash; Toxicity rate by material.</div>

{df_to_html(by_material, decimals=1)}
<p>
CuO and ZnO account for essentially all of the toxicity in this dataset, which
matches the chemistry &ndash; both dissolve and release metal ions inside cells.
Al<sub>2</sub>O<sub>3</sub> and Fe<sub>2</sub>O<sub>3</sub> are inert here.
</p>

<div class="pagebreak"></div>

<h3><span class="step">8</span>Model Development</h3>
<p>
We built the five classifiers named in our abstract. Every one of them is
wrapped in a scikit-learn <code>Pipeline</code> together with the scaler and the
one-hot encoder, so that no information from the test set can leak into the
scaling.
</p>
<table>
<tr><th>#</th><th>Model</th><th>Settings we chose</th></tr>
<tr><td>1</td><td>Logistic Regression</td><td><code>max_iter=2000</code>, <code>class_weight="balanced"</code></td></tr>
<tr><td>2</td><td>Decision Tree</td><td><code>max_depth=6</code>, <code>class_weight="balanced"</code></td></tr>
<tr><td>3</td><td>K-Nearest Neighbors</td><td><code>n_neighbors=5</code></td></tr>
<tr><td>4</td><td>Support Vector Machine</td><td>RBF kernel, <code>probability=True</code>, <code>class_weight="balanced"</code></td></tr>
<tr><td>5</td><td>Random Forest</td><td><code>n_estimators=300</code>, <code>class_weight="balanced"</code></td></tr>
</table>
<div class="note">
<strong>Why <code>class_weight="balanced"</code>?</strong> Only {pct_toxic:.0f}% of
the samples are toxic. Without this setting the models simply learn to answer
"non-toxic" to everything, which still scores about 81% accuracy while being
completely useless. Balancing the class weights forces the models to actually
pay attention to the toxic minority.
</div>

<h3><span class="step">9</span>Model Training</h3>
<p>
Each pipeline was fitted on the training portion (266 experiments). On top of
the single train/test split we also ran <strong>5-fold stratified cross
validation</strong> on the training data, so that we could see how stable each
model is rather than trusting one lucky split.
</p>
<pre><code>Train: 266 rows    Test: 89 rows
Toxic in train: 51    Toxic in test: 17</code></pre>

<h3><span class="step">10</span>Model Testing</h3>
<p>
Each trained model then predicted on the 89 unseen test experiments, producing
both a class label and a probability of toxicity.
</p>

<h3><span class="step">11</span>Performance Evaluation</h3>
<p>
We recorded accuracy, precision, recall, F1 score and ROC-AUC, plus a confusion
matrix for every model.
</p>
{df_to_html(metrics, decimals=3)}

{img("07_confusion_matrices.png")}
<div class="caption">Figure 7 &ndash; Confusion matrices on the test set.</div>

{img("08_roc_curves.png", "62%")}
<div class="caption">Figure 8 &ndash; ROC curves for all five models.</div>

{img("09_model_comparison.png", "88%")}
<div class="caption">Figure 9 &ndash; Model comparison across all metrics.</div>

<h3><span class="step">12</span>Selecting the Best Model</h3>
<p>
We selected the best model by <strong>F1 score, not accuracy</strong>. The
reason is visible in the results table: KNN reaches {metrics.set_index('Model').loc['KNN','Accuracy']:.1%}
accuracy, which looks respectable, but its recall is only
{metrics.set_index('Model').loc['KNN','Recall']:.3f} &ndash; it misses almost
60% of the toxic particles. For a safety screening tool, failing to flag a toxic
particle is the worst possible mistake, so a metric that balances precision and
recall is the right one to optimise.
</p>
<div class="ok">
<strong>Final model: {best['Model']}</strong><br>
Accuracy {best['Accuracy']:.3f} &nbsp;&middot;&nbsp;
Precision {best['Precision']:.3f} &nbsp;&middot;&nbsp;
Recall {best['Recall']:.3f} &nbsp;&middot;&nbsp;
F1 {best['F1']:.3f} &nbsp;&middot;&nbsp;
ROC-AUC {best['ROC_AUC']:.3f}
<br><br>
It correctly identifies {best['Recall']:.0%} of the toxic nanoparticles in the
test set. The winner is then retrained on all {n_clean} experiments and saved to
<code>models/best_model.joblib</code>.
</div>

<h3><span class="step">13</span>Interpretation and Insights</h3>
{img("10_feature_importance.png", "70%")}
<div class="caption">Figure 10 &ndash; Feature importance from the Random Forest.</div>
{df_to_html(top_imp, decimals=4)}
<p>What the model is telling us:</p>
<ul>
  <li>The chemical identity of the material dominates. The descriptors that
      encode <em>which</em> oxide it is are the most informative features.</li>
  <li>Among the properties an experimenter can actually control,
      <strong>dosage</strong>, <strong>exposure time</strong> and
      <strong>surface area</strong> carry the most weight.</li>
  <li>Hydrodynamic size turned out to be almost uninformative here
      (correlation with toxicity of only &minus;0.02).</li>
  <li>Practical takeaway: choosing a safer base material matters more than
      fine-tuning the particle size.</li>
</ul>

<div class="pagebreak"></div>

<h3><span class="step">14</span>Final Prediction System</h3>
<p>
We built two front ends, both of which call the exact same prediction function
so they can never disagree with each other.
</p>

<h4>a) Web application (Streamlit)</h4>
<pre><code>streamlit run app.py</code></pre>
<p>
The user picks a material and types in the six measurable properties. The app
fills in the thirteen chemistry descriptors automatically from the material
lookup table, runs the saved model, and displays TOXIC or NON-TOXIC together
with a probability. It has three tabs: the prediction form, the model results
with all the figures, and an about page.
</p>

<h4>b) Command line tool</h4>
<pre><code>python src/predict.py --material ZnO --coresize 40 --hydrosize 300 \\
    --surfcharge -12 --surfarea 50 --expotime 24 --dosage 100

==================================================
        NANOPARTICLE TOXICITY PREDICTION
==================================================
  Material          : ZnO
  Core size         : 40.0 nm
  Hydrodynamic size : 300.0 nm
  Surface charge    : -12.0 mV
  Surface area      : 50.0 m2/g
  Exposure time     : 24.0 hours
  Dosage            : 100.0 ug/mL
  Cell type         : Cancer
--------------------------------------------------
  PREDICTION        : TOXIC
  Probability toxic : 99.0%
  Model used        : Random Forest
==================================================</code></pre>
<p>
It also runs in an interactive question-by-question mode if no arguments are
given, and has a <code>--demo</code> flag that runs four worked examples.
</p>

<h4>Sample outputs from <code>--demo</code></h4>
<table>
<tr><th>Material</th><th>Dose</th><th>Cell type</th><th>Prediction</th><th>Probability toxic</th></tr>
<tr><td>ZnO</td><td>100 &micro;g/mL</td><td>Cancer</td><td><strong>TOXIC</strong></td><td>99.0%</td></tr>
<tr><td>CuO</td><td>200 &micro;g/mL</td><td>Cancer</td><td><strong>TOXIC</strong></td><td>96.7%</td></tr>
<tr><td>TiO<sub>2</sub></td><td>10 &micro;g/mL</td><td>Normal</td><td>NON-TOXIC</td><td>1.3%</td></tr>
<tr><td>Al<sub>2</sub>O<sub>3</sub></td><td>0.01 &micro;g/mL</td><td>Normal</td><td>NON-TOXIC</td><td>0.0%</td></tr>
</table>
<p class="small">
These agree with the known chemistry: CuO and ZnO release toxic metal ions,
while TiO<sub>2</sub> and Al<sub>2</sub>O<sub>3</sub> are largely inert.
</p>

<h3><span class="step">15</span>Bug Sweep, Conclusion and Future Work</h3>
<p>
Once everything worked we deliberately went back and tried to break it. We wrote
a test suite of 18 tests in <code>tests/test_pipeline.py</code> and found seven
issues. The full write-up is in <code>notes/BUG_SWEEP.md</code>; the summary is
in section 5 of this report.
</p>
<pre><code>pytest -v
...
18 passed</code></pre>

<div class="pagebreak"></div>

<!-- ============ RESULTS ============ -->
<h2>4. Results</h2>
{df_to_html(metrics, decimals=3)}
<p>
<strong>{best['Model']}</strong> is the final model, with
{best['Accuracy']:.1%} accuracy, an F1 score of {best['F1']:.3f} and a ROC-AUC
of {best['ROC_AUC']:.3f} on the held-out test set.
</p>

<h3>Honest limitation: leave-one-material-out</h3>
<p>
Almost all the toxic samples in this dataset are CuO or ZnO, and thirteen of the
nineteen numeric features are constant within a material. That means a normal
random split allows the model to partly <em>recognise the material</em> rather
than learn the underlying chemistry, and the reported accuracy would be
optimistic for a genuinely new nanoparticle.
</p>
<p>
To measure how serious this is, we ran an extra test that was not in the
original plan: train on four materials and test on the fifth, which the model
has never seen at all.
</p>
{df_to_html(lomo, decimals=3)}
<div class="warn">
Held-out ZnO accuracy drops to {lomo.set_index('Held_out_material').loc['ZnO','Accuracy']:.3f},
against {best['Accuracy']:.3f} on the normal test split. The model should
therefore be used for materials similar to the five it was trained on, and
<strong>not</strong> trusted for a completely new nanoparticle. This is a
limitation of the dataset (only 5 materials), not of the code.
</div>

<h2>5. Bug Sweep Summary</h2>
<table>
<tr><th>#</th><th>Issue</th><th>Severity</th><th>Fix</th></tr>
<tr><td>1</td><td>The <code>viability</code> column leaked the answer</td><td>Critical</td><td>Dropped in preprocessing; a test fails if it returns</td></tr>
<tr><td>2</td><td>Repeated experiments split across train and test</td><td>High</td><td><code>collapse_replicates()</code>; 477 &rarr; 355 unique experiments</td></tr>
<tr><td>3</td><td>The web app had its own copy of the prediction code</td><td>Medium</td><td>App now imports the shared <code>predict()</code> function</td></tr>
<tr><td>4</td><td>Column order was never verified</td><td>Medium</td><td>Feature order saved with the model and reapplied every time</td></tr>
<tr><td>5</td><td>Accuracy was hiding a model with 0.41 recall</td><td>Medium</td><td>Best model selected by F1; balanced class weights</td></tr>
<tr><td>6</td><td>No validation on user input</td><td>Low</td><td>Clear <code>ValueError</code> for unknown material or cell type</td></tr>
<tr><td>7</td><td>No warning when input is outside the training range</td><td>Low</td><td><code>check_ranges()</code> warns in both the app and the CLI</td></tr>
</table>
<div class="ok">
Two of these actually changed our results. Bug 2 was found by a test we expected
to pass, and fixing it <strong>changed which model won</strong> &ndash; the
Decision Tree had been coming first partly because it could memorise the
duplicated rows. After the fix, Random Forest wins and the held-out ZnO recall
improved from 0.257 to 0.717.
</div>

<h2>6. Conclusion</h2>
<p>
We built a complete, working, end-to-end system. It downloads a real published
dataset, cleans it, explores it, trains and compares five classifiers, evaluates
them properly, selects the best one, and serves predictions through both a web
app and a command line tool. The final Random Forest model reaches
{best['Accuracy']:.1%} accuracy and correctly flags {best['Recall']:.0%} of the
toxic nanoparticles in the test set.
</p>
<p>
Just as importantly, we tested our own work and documented what was wrong with
it. Two of the seven bugs we found would have made our results look considerably
better than they really are, and we would rather report an honest 94% than a
fake 100%.
</p>

<h3>Future work</h3>
<ul>
  <li>Obtain a larger dataset with more than five materials, so the
      leave-one-material-out scores improve.</li>
  <li>Extend beyond metal oxides to polymeric and silica nanoparticles.</li>
  <li>Try SMOTE or other resampling techniques for the class imbalance instead
      of relying only on <code>class_weight="balanced"</code>.</li>
  <li>Use SHAP values so that each individual prediction can be explained, not
      just the overall feature importances.</li>
  <li>Tune hyperparameters systematically with <code>GridSearchCV</code>.</li>
</ul>

<h2>7. How to Reproduce Everything</h2>
<pre><code>pip install -r requirements.txt

python run_all.py         # download -&gt; clean -&gt; EDA -&gt; train
streamlit run app.py      # launch the web app
pytest -v                 # run the 18 tests</code></pre>
<p>
Deleting the <code>data/</code>, <code>models/</code> and <code>results/</code>
folders and running <code>python run_all.py</code> rebuilds the entire project
from scratch, including re-downloading the dataset. Every random seed is fixed
at 42, so the numbers in this report come out identical every time.
</p>

<h2>8. Files Submitted</h2>
<table>
<tr><th>File</th><th>What it is</th></tr>
<tr><td><code>dataset/1_raw_nanotox_dataset.csv</code></td><td>The original dataset as downloaded ({n_raw} rows)</td></tr>
<tr><td><code>dataset/2_cleaned_dataset_used_for_training.csv</code></td><td>The cleaned data the model was actually trained on ({n_clean} rows)</td></tr>
<tr><td><code>dataset/3_material_properties_lookup.csv</code></td><td>The chemistry descriptors per material</td></tr>
<tr><td><code>src/config.py</code></td><td>All paths and column definitions</td></tr>
<tr><td><code>src/download_data.py</code></td><td>Step 3</td></tr>
<tr><td><code>src/preprocess.py</code></td><td>Steps 4 and 5</td></tr>
<tr><td><code>src/eda.py</code></td><td>Steps 6 and 7</td></tr>
<tr><td><code>src/train_models.py</code></td><td>Steps 8 to 12</td></tr>
<tr><td><code>src/predict.py</code></td><td>Step 14, command line</td></tr>
<tr><td><code>app.py</code></td><td>Step 14, web app</td></tr>
<tr><td><code>tests/test_pipeline.py</code></td><td>Step 15, the 18 tests</td></tr>
<tr><td><code>notes/BUG_SWEEP.md</code></td><td>Full bug sweep write-up</td></tr>
<tr><td><code>results/</code></td><td>All metrics tables and the ten figures</td></tr>
<tr><td><code>models/best_model.joblib</code></td><td>The trained Random Forest pipeline</td></tr>
</table>


</body></html>"""


def main():
    html = build_html()
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(html) / 1024:.0f} KB)")

    chrome = find_chrome()
    if chrome is None:
        print("Chrome or Edge not found - cannot make the PDF.")
        print(f"Open {OUT_HTML} in a browser and print to PDF manually.")
        sys.exit(1)

    profile = tempfile.mkdtemp(prefix="pdfprofile_")
    url = OUT_HTML.resolve().as_uri()
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={profile}",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUT_PDF}",
        url,
    ]
    print("Printing to PDF with", Path(chrome).name, "...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if not OUT_PDF.exists():
        print("PDF was not created.")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        sys.exit(1)

    print(f"Created {OUT_PDF} ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
    shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
