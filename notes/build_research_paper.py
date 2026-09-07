"""
Builds the research paper PDF (two-column conference format).

Run:  python notes/build_research_paper.py
"""

import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))
import config  # noqa: E402

OUT_PDF = PROJECT / "Nanoparticle_Toxicity_Research_Paper.pdf"
OUT_HTML = PROJECT / "notes" / "research_paper.html"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    for n in ["chrome", "google-chrome", "msedge"]:
        f = shutil.which(n)
        if f:
            return f
    return None


def fig(name):
    path = config.FIGURES_DIR / name
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


CSS = """
@page { size: A4; margin: 17mm 15mm 17mm 15mm; }
:root { color-scheme: light; }
html { background:#fff; }
* { box-sizing: border-box; }
body {
  font-family: "Times New Roman", Times, serif;
  font-size: 9.6pt; line-height: 1.42; color:#000; background:#fff; margin:0;
  text-align: justify; hyphens: auto;
}
.title {
  font-size: 19pt; font-weight: 700; text-align:center;
  line-height:1.25; margin: 0 0 10px 0;
}
.authors { text-align:center; font-size: 11pt; margin-bottom: 3px; }
.affil { text-align:center; font-size: 9pt; font-style: italic; margin-bottom: 2px; }
.email { text-align:center; font-size: 8.5pt; margin-bottom: 14px; }

.abstractbox {
  border-top: 1.2px solid #000; border-bottom: 1.2px solid #000;
  padding: 8px 4px; margin-bottom: 12px;
}
.abstractbox p { margin: 0 0 6px 0; font-size: 9.2pt; }
.abstractbox .lbl { font-weight: 700; font-style: italic; }

.body2col { column-count: 2; column-gap: 7mm; }

h2 {
  font-size: 10pt; font-weight: 700; margin: 12px 0 5px 0;
  text-transform: uppercase; letter-spacing: .2px;
  break-after: avoid;
}
h3 {
  font-size: 9.6pt; font-weight: 700; font-style: italic;
  margin: 9px 0 3px 0; break-after: avoid;
}
p { margin: 0 0 6px 0; text-indent: 4mm; }
p.noind, h2 + p, h3 + p { text-indent: 0; }

figure { margin: 8px 0 10px 0; break-inside: avoid; text-align:center; }
figure img { width: 100%; }
figcaption { font-size: 8.2pt; text-align: justify; margin-top: 4px; }

figure.wide, table.wide, .spanall { column-span: all; }
figure.wide img { width: 100%; }

table {
  border-collapse: collapse; width: 100%; font-size: 8.2pt;
  margin: 6px 0 4px 0; break-inside: avoid;
  font-family: "Segoe UI", Arial, sans-serif;
}
table caption {
  caption-side: top; font-size: 8.2pt; text-align: left;
  font-family: "Times New Roman", serif; margin-bottom: 3px;
}
th { border-top: 1.1px solid #000; border-bottom: .8px solid #000;
     padding: 3px 5px; text-align: left; font-weight: 700; }
td { padding: 2.5px 5px; }
tbody tr:last-child td { border-bottom: 1.1px solid #000; }
td.num, th.num { text-align: right; }
tr.best td { font-weight: 700; }

ol.refs { padding-left: 0; margin: 0; list-style: none; counter-reset: r; }
ol.refs li {
  counter-increment: r; font-size: 8.4pt; margin-bottom: 5px;
  padding-left: 7mm; text-indent: -7mm; text-align: left;
}
ol.refs li::before { content: "[" counter(r) "] "; }
.kw { font-size: 9pt; }
.eq { text-align:center; font-style: italic; margin: 5px 0; text-indent:0; }
"""


HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Research Paper</title>
<style>{CSS}</style></head><body>

<div class="title">Predicting Metal-Oxide Nanoparticle Cytotoxicity from
Physicochemical Descriptors: A Comparative Machine Learning Study with
Leakage-Aware Data Curation</div>

<div class="authors">Pratham Joshi, Divyansh Khatri, Dhyey Bhatt, Jinay Shah</div>
<div class="affil">Department of Computer Science and Engineering</div>
<div class="affil">[Institution name to be inserted]</div>
<div class="email">KU2507U0361, KU2507U0188, KU2507U0138, KU2507U0070</div>

<div class="abstractbox">
<p><span class="lbl">Abstract&mdash;</span>
Engineered nanoparticles are increasingly used in drug delivery, where their
small size and large specific surface area allow them to interact closely with
cells and tissues. The same properties, however, can produce unwanted
cytotoxicity, and experimental screening of every candidate formulation is slow
and costly. This paper reports a data-driven framework that classifies
metal-oxide nanoparticles as toxic or non-toxic from their physicochemical
descriptors and exposure conditions. Working from a published dataset of 483
in-vitro experiments covering five metal oxides and eleven cell lines, we found
that a naive treatment of the data produces badly inflated performance
estimates for two distinct reasons. First, the cell-viability measurement from
which the toxicity label was originally derived is present as a column in the
dataset and acts as a direct label leak. Second, and less obviously, the file
contains replicate experiments that become exactly identical once that column
is removed; a conventional random split therefore places copies of the same
experiment in both the training and test partitions. After correcting both
issues the usable dataset reduces to 355 unique experiments, of which 19.2% are
toxic. Five classifiers&mdash;logistic regression, a decision tree, k-nearest
neighbours, a support vector machine and a random forest&mdash;were trained
within a leakage-safe pipeline and compared. The random forest performed best,
achieving 0.944 accuracy, 0.941 recall and an F1 score of 0.865 on a stratified
held-out test set. We argue that recall, not accuracy, is the metric that
matters for a screening tool: the k-nearest neighbours classifier attains 0.876
accuracy while detecting only 41.2% of toxic particles. Finally, a
leave-one-material-out evaluation shows that performance degrades substantially
on a material the model has not seen, with held-out ZnO accuracy falling to
0.771. We report this openly, since it indicates that models trained on the
small number of oxides available in current public datasets generalise across
exposure conditions far better than they generalise across chemistries.
</p>
<p class="kw"><span class="lbl">Keywords&mdash;</span>
nanotoxicity, nano-QSAR, machine learning, random forest, data leakage, class
imbalance, drug delivery, cytotoxicity prediction</p>
</div>

<div class="body2col">

<h2>I.&nbsp;&nbsp;Introduction</h2>
<p class="noind">
Nanoparticles occupy an awkward position in biomedical engineering. The
properties that make them attractive as drug carriers&mdash;dimensions of tens
of nanometres, very high surface-area-to-volume ratios, and surfaces that can be
functionalised to target particular tissues&mdash;are also the properties that
allow them to cross membranes, accumulate in organs and generate reactive oxygen
species. A carrier that delivers its payload efficiently is of little use if the
carrier itself damages healthy cells.</p>

<p>
Establishing whether a given formulation is safe is conventionally an
experimental question, answered with in-vitro assays across a range of doses,
exposure durations and cell lines. This is thorough but expensive, and it scales
poorly: the design space spanned by material chemistry, particle size, surface
charge and coating is far larger than any laboratory can enumerate. Computational
screening is therefore attractive not as a replacement for assays but as a filter
that decides which formulations are worth testing at all.</p>

<p>
The established computational approach is nano-QSAR, in which a quantitative
model relates structural or physicochemical descriptors of a nanomaterial to a
measured biological response. Since the earliest such models the field has moved
steadily from small hand-fitted regressions towards general-purpose machine
learning classifiers trained on curated experimental collections. Our work sits
in that second category.</p>

<p>
This paper makes three contributions. We build and compare five standard
classifiers for binary cytotoxicity prediction on a public metal-oxide dataset.
We identify and correct two data-integrity problems in that dataset&mdash;a
label leak and a replicate-duplication artefact&mdash;that between them inflate
reported performance and, in our experiments, change which classifier appears to
be the best. And we quantify how far the resulting model actually generalises by
holding out entire materials rather than random rows, which we believe is the
more honest test for this kind of data.</p>

<h2>II.&nbsp;&nbsp;Related Work</h2>
<p class="noind">
The foundational demonstration that nanoparticle toxicity can be predicted from
computed descriptors rather than measured in every case is due to Puzyn and
co-workers [1], who fitted a nano-QSAR model to the cytotoxicity of seventeen
metal oxides against <i>E. coli</i> using a single quantum-chemical descriptor,
the enthalpy of formation of the gaseous cation. The model was deliberately
parsimonious and remains a reference point for the field.</p>

<p>
Liu et al. [2] extended the idea from regression to classification, developing
nanoSAR models that separate toxic from non-toxic metal-oxide nanoparticles and
noting that classification is often the more defensible target when the
underlying assay data are noisy. Their emphasis on classification over exact
potency prediction motivated our own choice of a binary target.</p>

<p>
As datasets grew, attention shifted towards their quality. Trinh et al. [3]
curated metallic-nanoparticle datasets and explicitly assessed completeness and
consistency before building nanoSAR classifiers, arguing that curation decisions
materially affect the models that follow. Oh et al. [4] made a similar point at
larger scale, assembling 307 publications on cadmium-containing quantum dots
into a single meta-analysis and showing that surface properties and assay
conditions, rather than core composition alone, drive the observed toxicity.
Both papers informed the attention we paid to replicate structure in our own
data, which turned out to matter more than any modelling choice we made.</p>

<p>
On the modelling side, Furxhi et al. [5] compared a range of individual and
ensemble classifiers for in-vitro nanoparticle toxicity and ranked them using
the Copeland index, concluding that ensemble methods were generally preferable.
Their later review [6] surveyed practices across the nanotoxicology machine
learning literature and identified recurring weaknesses: small datasets, severe
class imbalance, inconsistent validation protocols and an over-reliance on
accuracy as the headline metric. Several of the design decisions described in
Section III are direct responses to that critique.</p>

<p>
The dataset used here was assembled by Subramanian and Palaniappan [7], who
compiled metal-oxide cytotoxicity experiments with physicochemical and
quantum-mechanical descriptors and fitted a deliberately parsimonious model to
them. We use their data rather than their model, and our contribution relative
to that work is the curation analysis and the material-wise generalisation
assessment reported below.</p>

<h2>III.&nbsp;&nbsp;Materials and Methods</h2>

<h3>A. Dataset</h3>
<p class="noind">
We used the publicly available NanoTox metal-oxide nanoparticle dataset [7],
distributed under an MIT licence. In its raw form it contains 483 in-vitro
experiments described by 24 columns. Five metal oxides are
represented&mdash;Al<sub>2</sub>O<sub>3</sub>, CuO, Fe<sub>2</sub>O<sub>3</sub>,
TiO<sub>2</sub> and ZnO&mdash;tested against eleven cell lines, each labelled as
cancerous or normal. Each record combines six experimentally measured or chosen
quantities (core size, hydrodynamic size, surface charge, specific surface area,
exposure time and dose) with thirteen material-level descriptors such as
enthalpy of formation, band-edge energies, electronegativity, molecular weight
and oxidation state. The dataset contained no missing values.</p>

<h3>B. Label leakage</h3>
<p class="noind">
The dataset supplies both a continuous <i>viability</i> measurement and a binary
<i>class</i> label. The latter was derived from the former by the original
authors by thresholding. Retaining viability as a predictor therefore does not
constitute prediction at all: it exposes a monotone transform of the target.
Grouping the raw records by class confirms this, the two groups being separated
almost perfectly along the viability axis. We excluded the column before any
analysis, and enforced its exclusion with an automated test so that it could not
be reintroduced by a later edit. We mention this explicitly because a model
trained with the column present reaches near-perfect scores that are entirely
spurious, and the trap is easy to fall into.</p>

<h3>C. Replicate consolidation</h3>
<p class="noind">
A second and more subtle problem emerged during testing. Removing six exactly
duplicated rows left 477 records, but a check for duplicates over the
<i>feature</i> columns alone revealed a further 122 repeated rows. The
explanation is that the source file records the same experimental condition
(identical particle, dose, exposure time and cell line) several times, each with
its own measured viability. While viability is present these rows are distinct;
once it is removed they become identical.</p>

<p>
The consequence for model evaluation is serious. A random train/test split
distributes such replicates across both partitions, so the test set is no longer
composed of unseen experiments and the reported score is optimistic. We
therefore consolidated replicates to one row per unique experimental condition.
Where replicates disagreed on the label&mdash;which occurred for 11
groups, reflecting genuine biological and measurement variability&mdash;we
assigned the majority label, resolving exact ties in favour of the toxic class
on the grounds that a false alarm is less costly than a missed hazard in a
screening context. This reduced the dataset to 355 unique experiments, of which
68 (19.2%) are toxic.</p>

<h3>D. Feature organisation</h3>
<p class="noind">
Of the nineteen numeric descriptors, thirteen are constant within a material:
Al<sub>2</sub>O<sub>3</sub> always carries the same molecular weight and
oxidation state regardless of how the particle was prepared. We separated these
material constants from the six quantities that genuinely vary between
experiments. The distinction has a practical purpose&mdash;a user of the
resulting tool need only supply six measurements and the material name, with
the chemistry looked up automatically&mdash;but it also has an analytical
consequence discussed in Section V. Cell type was retained as a single
categorical variable and one-hot encoded. Material identity and cell line were
deliberately excluded as predictors so that the model could not simply memorise
them.</p>

<h3>E. Classifiers and pipeline</h3>
<p class="noind">
Five classifiers were compared: logistic regression, a decision tree of maximum
depth six, k-nearest neighbours with k = 5, a support vector machine with a
radial basis kernel, and a random forest of 300 trees. Each was embedded in a
single pipeline together with the standard scaler and the one-hot encoder, so
that scaling parameters are estimated on training folds only. Fitting a scaler
on the full dataset before splitting is a common and easily overlooked source of
optimistic bias, and the pipeline construction removes it structurally rather
than by convention.</p>

<p>
Given that only 19.2% of samples are toxic, all classifiers that support it were
given balanced class weights. Without this correction the models converge on the
degenerate solution of predicting the majority class everywhere, which attains
80.8% accuracy while identifying no toxic particles whatsoever.</p>

<h3>F. Evaluation protocol</h3>
<p class="noind">
The data were split 75/25 with stratification on the target, giving 266 training
and 89 test experiments (51 and 17 toxic respectively). We report accuracy,
precision, recall, F1 and ROC-AUC on the held-out set, together with the mean
and standard deviation of F1 under five-fold stratified cross-validation on the
training portion. Model selection was performed on F1 rather than accuracy, for
reasons developed in Section V. All random seeds were fixed, and the entire
pipeline is reproducible from the raw file.</p>

<h2>IV.&nbsp;&nbsp;Results</h2>

<h3>A. Dataset characteristics</h3>
<p class="noind">
The curated dataset is strongly imbalanced and the imbalance is concentrated by
material. Table I shows that toxicity is essentially confined to CuO and ZnO,
with 38.9% and 33.5% of their respective records labelled toxic, while
Al<sub>2</sub>O<sub>3</sub> and Fe<sub>2</sub>O<sub>3</sub> contribute no toxic
records at all and TiO<sub>2</sub> contributes one. This is chemically
unsurprising, since CuO and ZnO both dissolve appreciably at biological pH and
release cytotoxic metal ions, whereas the other three oxides are comparatively
inert.</p>

<table>
<caption><b>Table I.</b> Toxicity rate by material in the curated dataset.</caption>
<tr><th>Material</th><th class="num">Experiments</th><th class="num">Toxic</th><th class="num">% toxic</th></tr>
<tr><td>CuO</td><td class="num">18</td><td class="num">7</td><td class="num">38.9</td></tr>
<tr><td>ZnO</td><td class="num">179</td><td class="num">60</td><td class="num">33.5</td></tr>
<tr><td>TiO<sub>2</sub></td><td class="num">122</td><td class="num">1</td><td class="num">0.8</td></tr>
<tr><td>Al<sub>2</sub>O<sub>3</sub></td><td class="num">18</td><td class="num">0</td><td class="num">0.0</td></tr>
<tr><td>Fe<sub>2</sub>O<sub>3</sub></td><td class="num">18</td><td class="num">0</td><td class="num">0.0</td></tr>
</table>

<h3>B. Exploratory analysis</h3>
<p class="noind">
Comparing the toxic and non-toxic groups across the six controllable properties
(Fig. 1) shows the expected dose-response behaviour: toxic records are associated
with higher doses and longer exposure times. Toxic particles also tend to have
larger core sizes and smaller specific surface areas in this dataset, though
these trends are weaker and partly confounded with material identity.
Hydrodynamic size showed almost no univariate relationship with the outcome,
with a Pearson correlation of &minus;0.079.</p>

<figure>
<img src="{fig('03_toxic_vs_nontoxic.png')}">
<figcaption><b>Fig. 1.</b> Distribution of the six controllable properties for
toxic and non-toxic experiments. Dose and exposure time separate the classes
most clearly.</figcaption>
</figure>

<p>
Ranking the descriptors by their linear correlation with the label places the
material-level chemistry first: the metal-to-oxygen ratio (r = &minus;0.415),
enthalpy (&minus;0.410), electronegativity per oxygen (+0.406) and oxidation
state (&minus;0.400) lead the list, with the strongest experimental variable,
specific surface area, some way behind at &minus;0.241. This is a direct
consequence of the structure noted in Section III-D: because these descriptors
are constant within a material, their correlation with the label is largely a
restatement of the fact that CuO and ZnO are the toxic materials.</p>

<h3>C. Classifier comparison</h3>
<p class="noind">
Table II reports held-out performance. The random forest is the strongest model
on every metric except precision, reaching 0.944 accuracy, 0.941 recall, an F1
of 0.865 and a ROC-AUC of 0.946, and it is also the most stable under
cross-validation (F1 0.880 &plusmn; 0.057).</p>

<table>
<caption><b>Table II.</b> Held-out test performance (89 experiments, 17 toxic).
CV F1 is the mean and standard deviation over five stratified folds of the
training set.</caption>
<tr><th>Model</th><th class="num">Acc.</th><th class="num">Prec.</th>
<th class="num">Rec.</th><th class="num">F1</th><th class="num">AUC</th>
<th class="num">CV F1</th></tr>
<tr class="best"><td>Random Forest</td><td class="num">0.944</td><td class="num">0.800</td>
<td class="num">0.941</td><td class="num">0.865</td><td class="num">0.946</td>
<td class="num">0.880</td></tr>
<tr><td>Decision Tree</td><td class="num">0.921</td><td class="num">0.778</td>
<td class="num">0.824</td><td class="num">0.800</td><td class="num">0.904</td>
<td class="num">0.831</td></tr>
<tr><td>Logistic Reg.</td><td class="num">0.888</td><td class="num">0.667</td>
<td class="num">0.824</td><td class="num">0.737</td><td class="num">0.931</td>
<td class="num">0.695</td></tr>
<tr><td>SVM (RBF)</td><td class="num">0.865</td><td class="num">0.609</td>
<td class="num">0.824</td><td class="num">0.700</td><td class="num">0.928</td>
<td class="num">0.665</td></tr>
<tr><td>KNN (k = 5)</td><td class="num">0.876</td><td class="num">0.875</td>
<td class="num">0.412</td><td class="num">0.560</td><td class="num">0.836</td>
<td class="num">0.527</td></tr>
</table>

<p>
The k-nearest neighbours result deserves comment. Its accuracy of 0.876 is
higher than that of the support vector machine and only modestly below the
decision tree, yet its recall is 0.412, meaning it fails to identify more than
half of the toxic particles in the test set. It achieves its accuracy largely by
agreeing with the majority class. A study reporting accuracy alone would rank
this model respectably; by F1 it is clearly the weakest of the five. Fig. 2
shows the corresponding ROC curves.</p>

<figure>
<img src="{fig('08_roc_curves.png')}">
<figcaption><b>Fig. 2.</b> ROC curves on the held-out test set. The random
forest attains the highest area under the curve (0.946).</figcaption>
</figure>

<h3>D. Feature importance</h3>
<p class="noind">
The random forest's impurity-based importances tell a different story from the
correlation ranking. Dose dominates, accounting for 0.466 of the total
importance, followed by exposure time at 0.100; the material descriptors follow
at roughly 0.04&ndash;0.06 each (Fig. 3). The two views are not in conflict.
Correlation is a linear, marginal measure and rewards descriptors that separate
the materials, since material identity explains most of the variance in the
label. The forest, by contrast, can split repeatedly on dose within a material
and so exploits the dose-response relationship that the marginal correlation
largely misses. For a practitioner the combined reading is the useful one:
choice of material sets the baseline hazard, and dose and exposure duration
modulate it.</p>

<figure>
<img src="{fig('10_feature_importance.png')}">
<figcaption><b>Fig. 3.</b> Random forest feature importances. Dose and exposure
time dominate, with material descriptors contributing at a lower level.</figcaption>
</figure>

<h3>E. Leave-one-material-out evaluation</h3>
<p class="noind">
Because thirteen of the nineteen numeric descriptors are constant within a
material, a random split allows the model to identify the material and apply a
learned per-material prior. To measure how much of the reported performance
depends on this, we retrained the selected model five times, each time holding
out one material entirely (Table III).</p>

<table>
<caption><b>Table III.</b> Leave-one-material-out evaluation. Recall is
undefined where the held-out material contains no toxic records.</caption>
<tr><th>Held out</th><th class="num">n</th><th class="num">Toxic</th>
<th class="num">Acc.</th><th class="num">Recall</th></tr>
<tr><td>Al<sub>2</sub>O<sub>3</sub></td><td class="num">18</td><td class="num">0</td>
<td class="num">1.000</td><td class="num">&ndash;</td></tr>
<tr><td>Fe<sub>2</sub>O<sub>3</sub></td><td class="num">18</td><td class="num">0</td>
<td class="num">1.000</td><td class="num">&ndash;</td></tr>
<tr><td>TiO<sub>2</sub></td><td class="num">122</td><td class="num">1</td>
<td class="num">0.992</td><td class="num">0.000</td></tr>
<tr><td>CuO</td><td class="num">18</td><td class="num">7</td>
<td class="num">0.889</td><td class="num">0.714</td></tr>
<tr><td>ZnO</td><td class="num">179</td><td class="num">60</td>
<td class="num">0.771</td><td class="num">0.717</td></tr>
</table>

<p>
The three folds that appear near-perfect are uninformative, since those
materials contain essentially no toxic records and the majority-class prediction
is almost always correct. The two informative folds are CuO and ZnO. Held-out
ZnO accuracy falls to 0.771 from 0.944 on the random split, and recall to 0.717
from 0.941. The model does retain some genuine transferable signal&mdash;recall
of roughly 0.71 on a chemistry it has never encountered is well above
chance&mdash;but the degradation is substantial and would not be visible from the
random-split figures alone.</p>

<h2>V.&nbsp;&nbsp;Discussion</h2>

<h3>A. Curation dominated modelling</h3>
<p class="noind">
The single change that most affected our results was not a modelling decision
but a data-curation one. Before replicate consolidation, the decision tree
appeared to be the best model with an F1 of 0.800, marginally ahead of the
random forest. After consolidation the ordering reversed and the random forest
led with 0.865. The decision tree had been partly memorising duplicated rows
that appeared on both sides of the split, an advantage that disappeared once
each experimental condition appeared exactly once. Held-out ZnO recall over the
same change improved from 0.257 to 0.717, indicating that the uncurated model
was not merely flattered by the split but genuinely worse. This is consistent
with the emphasis that Trinh et al. [3] and Oh et al. [4] place on curation, and
we would suggest that a duplicate check performed over feature columns only,
after any label-derived column has been dropped, is worth making routine.</p>

<h3>B. The choice of metric</h3>
<p class="noind">
With a 19.2% positive rate, accuracy is close to uninformative. The constant
majority predictor scores 80.8%, and the KNN result in Table II shows that a
real model can sit only a few points above that baseline while missing most of
the hazards it exists to detect. In a screening application the two error types
are not symmetric: a false positive costs an unnecessary assay, whereas a false
negative allows a toxic formulation to advance. Recall and F1 are the
appropriate criteria, and we would echo the observation of Furxhi et al. [6]
that accuracy-led reporting remains common in this literature and is
misleading.</p>

<h3>C. Limitations</h3>
<p class="noind">
The most important limitation is the narrow chemical coverage of the data. Five
metal oxides, only two of which contribute meaningful numbers of toxic records,
cannot support confident claims about nanoparticle toxicity in general, and the
leave-one-material-out results in Table III should be read as an upper bound on
what can be said about an unseen chemistry. The dataset is also small in
absolute terms; with 17 toxic records in the test partition, individual metrics
carry wide confidence intervals, which is why we report cross-validated F1
alongside the single-split figures.</p>

<p>
Two further constraints follow from the data rather than the method. Toxicity
here is a thresholded in-vitro viability outcome, and in-vitro viability is an
imperfect proxy for in-vivo harm. And 11 replicate groups disagreed with
themselves, which places a ceiling on the accuracy any model can legitimately
reach on this data. Extending the work to polymeric and silica nanoparticles,
applying resampling techniques such as SMOTE in place of class weighting, and
using Shapley values to explain individual predictions rather than global
importances are the natural next steps.</p>

<h2>VI.&nbsp;&nbsp;Conclusion</h2>
<p class="noind">
We have presented a machine learning framework for classifying metal-oxide
nanoparticles as toxic or non-toxic from physicochemical descriptors and
exposure conditions. A random forest trained on 355 curated experiments reaches
0.944 accuracy and 0.941 recall on a held-out stratified test set, outperforming
logistic regression, a decision tree, a support vector machine and k-nearest
neighbours.</p>

<p>
The more transferable findings, however, concern the data rather than the model.
A label-derived column and an unnoticed replicate structure each inflate
apparent performance, and correcting the second changed which classifier
appeared best. A leave-one-material-out evaluation shows that performance on an
unseen chemistry is markedly lower than a random split suggests. We would
encourage both checks in future nanotoxicity modelling work, since neither is
expensive to perform and both change the conclusions one is entitled to draw.
</p>

<h2>References</h2>
<ol class="refs">
<li>T. Puzyn, B. Rasulev, A. Gajewicz, X. Hu, T. P. Dasari, A. Michalkova,
H.-M. Hwang, A. Toropov, D. Leszczynska, and J. Leszczynski, "Using nano-QSAR to
predict the cytotoxicity of metal oxide nanoparticles," <i>Nature
Nanotechnology</i>, vol. 6, no. 3, pp. 175&ndash;178, 2011.</li>

<li>R. Liu, R. Rallo, S. George, Z. Ji, S. Nair, A. E. Nel, and Y. Cohen,
"Classification NanoSAR development for cytotoxicity of metal oxide
nanoparticles," <i>Small</i>, vol. 7, no. 8, pp. 1118&ndash;1126, 2011.</li>

<li>T. X. Trinh, M. K. Ha, J. S. Choi, H.-G. Byun, and T. H. Yoon, "Curation of
datasets, assessment of their quality and completeness, and nanoSAR
classification model development for metallic nanoparticles,"
<i>Environmental Science: Nano</i>, vol. 5, no. 8, pp. 1902&ndash;1910, 2018.</li>

<li>E. Oh, R. Liu, A. Nel, K. B. Gemill, M. Bilal, Y. Cohen, and I. L. Medintz,
"Meta-analysis of cellular toxicity for cadmium-containing quantum dots,"
<i>Nature Nanotechnology</i>, vol. 11, no. 5, pp. 479&ndash;486, 2016.</li>

<li>I. Furxhi, F. Murphy, M. Mullins, and C. A. Poland, "Machine learning
prediction of nanoparticle in vitro toxicity: A comparative study of classifiers
and ensemble-classifiers using the Copeland Index," <i>Toxicology Letters</i>,
vol. 312, pp. 157&ndash;166, 2019.</li>

<li>I. Furxhi, F. Murphy, M. Mullins, A. Arvanitis, and C. A. Poland, "Practices
and trends of machine learning application in nanotoxicology,"
<i>Nanomaterials</i>, vol. 10, no. 1, art. 116, 2020.</li>

<li>N. A. Subramanian and A. Palaniappan, "NanoTox: Development of a
parsimonious in silico model for toxicity assessment of metal-oxide
nanoparticles using physicochemical features," <i>ACS Omega</i>, vol. 6, no. 17,
pp. 11729&ndash;11739, 2021.</li>
</ol>

</div>
</body></html>"""


def main():
    OUT_HTML.write_text(HTML, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(HTML) / 1024:.0f} KB)")

    chrome = find_chrome()
    if chrome is None:
        print("Chrome/Edge not found.")
        sys.exit(1)

    profile = tempfile.mkdtemp(prefix="pdfprofile_")
    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
           f"--user-data-dir={profile}", "--no-pdf-header-footer",
           f"--print-to-pdf={OUT_PDF}", OUT_HTML.resolve().as_uri()]
    print("Printing to PDF ...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if not OUT_PDF.exists():
        print("FAILED"); print(r.stderr[-1500:]); sys.exit(1)
    print(f"Created {OUT_PDF} ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
    shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
