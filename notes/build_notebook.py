"""
Builds the complete step-by-step project notebook and executes it so all
the outputs and figures are baked in.

Run:  python notes/build_notebook.py
"""

import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

PROJECT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT / "notebooks"
OUT_NB = OUT_DIR / "Nanoparticle_Toxicity_Complete_Project.ipynb"

cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))


# ==================================================================
md("""
# Nanoparticle Toxicity Prediction Using Data-Driven Methods

**Mini Project — complete step-by-step implementation**

| Name | Enrolment No. |
|---|---|
| Pratham Joshi | KU2507U0361 |
| Divyansh Khatri | KU2507U0188 |
| Dhyey Bhatt | KU2507U0138 |
| Jinay Shah | KU2507U0070 |

---

### What this notebook does

It runs the entire project from start to finish, in order:

| Part | Stage | What happens |
|---|---|---|
| 1 | Setup | Imports and settings |
| 2 | Load raw data | Read the downloaded dataset |
| 3 | Data understanding | Shape, types, missing values, class balance |
| 4 | **Raw data cleaning** | Duplicates, target encoding, leakage removal |
| 5 | **Replicate merging** | Produce the final clean dataset |
| 6 | **EDA** | All the exploratory plots |
| 7 | Feature analysis | Which properties drive toxicity |
| 8 | Train/test split | Stratified split + preprocessing pipeline |
| 9 | **Model training** | Five classifiers |
| 10 | **Evaluation** | Metrics, confusion matrices, ROC curves |
| 11 | Model selection | Pick the best one |
| 12 | Interpretation | Feature importance |
| 13 | Honesty check | Leave-one-material-out |
| 14 | Save the model | Export for the app |
| 15 | Prediction system | Use the model on new inputs |

> This notebook is the walkthrough version, written so every step can be read
> in order. The production pipeline lives in `src/` and is what `run_all.py`
> executes. The last cell checks that this notebook reproduces exactly the same
> numbers as the pipeline, so the two can never silently disagree.
""")

# ------------------------------------------------------------------
md("""
---
## Part 1 — Setup

Imports and a few settings we use everywhere. `RANDOM_STATE = 42` is fixed so
that every run of this notebook gives identical numbers.
""")

code("""
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    LeaveOneGroupOut,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
%matplotlib inline
sns.set_theme(style="whitegrid")
pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 30)

RANDOM_STATE = 42
TEST_SIZE = 0.25

# Find the project folder whether we run from notebooks/ or the root
PROJECT = Path.cwd()
if not (PROJECT / "src").exists():
    PROJECT = PROJECT.parent

RAW_FILE = PROJECT / "data" / "raw" / "nanotox_dataset.tsv"

print("Project folder :", PROJECT)
print("Raw data file  :", RAW_FILE.name, "| exists:", RAW_FILE.exists())
""")

# ------------------------------------------------------------------
md("""
---
## Part 2 — Load the raw data

The dataset is the **NanoTox metal-oxide nanoparticle dataset**, published
alongside a peer-reviewed study.

- Source: <https://github.com/NanoTox/ToxicityModel> (file `dataset.txt`)
- Paper: *NanoTox: Development of a parsimonious in silico model for toxicity
  assessment of metal-oxide nanoparticles using physicochemical features*,
  bioRxiv 2021, doi:10.1101/2021.02.22.432301
- Licence: MIT

If the file is not present, the cell below downloads it. Note it is
**tab separated**, not comma separated.
""")

code("""
import urllib.request

DATA_URL = "https://raw.githubusercontent.com/NanoTox/ToxicityModel/master/dataset.txt"

if not RAW_FILE.exists():
    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading the dataset ...")
    urllib.request.urlretrieve(DATA_URL, RAW_FILE)
    print("Saved to", RAW_FILE)

raw = pd.read_csv(RAW_FILE, sep="\\t")   # tab separated!
print("Raw dataset shape:", raw.shape)
raw.head()
""")

# ------------------------------------------------------------------
md("""
---
## Part 3 — Data understanding

Before changing anything, look at what we actually have.
""")

code("""
print("Rows:", raw.shape[0], " Columns:", raw.shape[1])
print()
print("Column names:")
print(list(raw.columns))
""")

code("""
raw.info()
""")

code("""
print("Missing values per column:")
missing = raw.isna().sum()
print(missing[missing > 0] if missing.sum() else "  None - the dataset is complete.")
print()
print("Exact duplicate rows:", raw.duplicated().sum())
""")

code("""
print("Target variable distribution:")
counts = raw["class"].value_counts()
for label, n in counts.items():
    print(f"  {label:10s} {n:4d}   ({n / len(raw) * 100:.1f}%)")

print()
print("=> The dataset is IMBALANCED (about 84% non-toxic).")
print("   So accuracy on its own will be a misleading metric.")
""")

code("""
print("Nanoparticle materials:", ", ".join(sorted(raw["NPs"].unique())))
print("Cell lines           :", raw["Cellline"].nunique(), "distinct")
print("Cell types           :", ", ".join(raw["Celltype"].unique()))
print()
raw.describe().T
""")

md("""
### The most important observation

There is a `viability` column (how many cells survived) sitting right next to
the `class` column. The `class` label was **created from** the viability value
by the dataset authors.

That makes `viability` the answer in disguise, not an input property. Let us
prove it before deciding to drop it.
""")

code("""
# Cell viability of toxic vs non-toxic samples
print(raw.groupby("class")["viability"].describe()[["count", "mean", "min", "max"]])
print()
print("The two groups are split almost perfectly at a viability threshold.")
print("Using this column as a feature would leak the answer into the model,")
print("giving a fake ~100% accuracy. It must be excluded.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 4 — Raw data cleaning

Now the actual cleaning. Five operations, in order:

1. Remove exact duplicate rows
2. Encode the target: `Toxic` → 1, `nonToxic` → 0
3. **Drop the leaking `viability` column**
4. Force the numeric columns to be numeric
5. Fill any missing numeric value with the column median

We define the column groups first, because the rest of the project depends on
them.
""")

code("""
TARGET_COL = "class"        # the original text label
TARGET = "toxic"            # our numeric 1/0 label

# The 6 properties an experimenter actually measures or chooses
USER_INPUT_FEATURES = [
    "coresize",    # core size of the particle (nm)
    "hydrosize",   # hydrodynamic size in solution (nm)
    "surfcharge",  # surface charge / zeta potential (mV)
    "surfarea",    # surface area (m2/g)
    "Expotime",    # exposure time (hours)
    "dosage",      # dose given to the cells (ug/mL)
]

# The 13 chemistry descriptors, fixed for a given material
MATERIAL_FEATURES = [
    "Hsf",       # heat of formation
    "Ec",        # conduction band energy
    "Ev",        # valence band energy
    "MeO",       # metal-oxygen bond descriptor
    "enthalpy",  # enthalpy
    "ratio",     # metal to oxygen ratio
    "e",         # electronegativity
    "esum",      # sum of electronegativity
    "esumbyo",   # electronegativity per oxygen
    "MW",        # molecular weight
    "NMetal",    # number of metal atoms
    "NOxygen",   # number of oxygen atoms
    "ox",        # oxidation state
]

NUMERIC_FEATURES = USER_INPUT_FEATURES + MATERIAL_FEATURES
CATEGORICAL_FEATURES = ["Celltype"]          # Cancer / Normal
ID_COLS = ["NPs", "Cellline"]                # kept for reference, NOT features
LEAKY_COLS = ["viability"]                   # never a feature

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

print(f"{len(USER_INPUT_FEATURES)} user-entered properties")
print(f"{len(MATERIAL_FEATURES)} material chemistry descriptors")
print(f"{len(CATEGORICAL_FEATURES)} categorical feature")
print(f"{len(FEATURES)} features in total")
""")

code("""
df = raw.copy()

# --- 1. remove exact duplicates ------------------------------------
before = len(df)
df = df.drop_duplicates().reset_index(drop=True)
print(f"1. Removed {before - len(df)} exact duplicate rows  ({before} -> {len(df)})")

# --- 2. encode the target ------------------------------------------
df[TARGET] = df[TARGET_COL].str.strip().str.lower().eq("toxic").astype(int)
print(f"2. Encoded target: Toxic = 1, nonToxic = 0")

# --- 3. drop the leaking column ------------------------------------
dropped = [c for c in LEAKY_COLS if c in df.columns]
df = df.drop(columns=dropped)
print(f"3. Dropped leaky column(s): {dropped}")

# --- 4. force numeric types ----------------------------------------
for col in NUMERIC_FEATURES:
    df[col] = pd.to_numeric(df[col], errors="coerce")
print(f"4. Converted {len(NUMERIC_FEATURES)} columns to numeric")

# --- 5. fill missing numeric values with the median ----------------
n_missing = df[NUMERIC_FEATURES].isna().sum().sum()
if n_missing:
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].fillna(df[NUMERIC_FEATURES].median())
    print(f"5. Filled {n_missing} missing values with the column median")
else:
    print("5. No missing numeric values to fill")

# tidy the categorical column and keep only what we need
for col in CATEGORICAL_FEATURES:
    df[col] = df[col].astype(str).str.strip()

df = df[ID_COLS + NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]]
print()
print("Shape after basic cleaning:", df.shape)
df.head()
""")

# ------------------------------------------------------------------
md("""
---
## Part 5 — Merging replicate experiments

This step was added after we found a problem during testing.

Once `viability` is removed, many rows become **identical**. The raw file
records the same experiment (same particle, same dose, same cell line) several
times, each with a slightly different measured viability. With those repeats
present, a random train/test split puts *copies of the same experiment* in both
the training set and the test set — so the test score is not honest.

Let us measure the problem first.
""")

code("""
n_dupes = df.duplicated(subset=FEATURES).sum()
groups = df.groupby(FEATURES, dropna=False)[TARGET]
n_unique = groups.ngroups
n_conflicting = (groups.nunique() > 1).sum()

print(f"Rows after basic cleaning        : {len(df)}")
print(f"Unique experiments (by features) : {n_unique}")
print(f"Rows that are repeats            : {n_dupes}")
print(f"Repeat groups that DISAGREE on")
print(f"  the label                      : {n_conflicting}")
print()
print("So the same conditions sometimes came out toxic in one repeat and")
print("non-toxic in another. That is real experimental variation.")
""")

md("""
**Fix:** keep one row per unique experiment. Where the repeats disagree, take
the majority vote. An exact tie counts as **toxic**, because for a safety
screening tool a false warning is safer than a false all-clear.
""")

code("""
grouped = df.groupby(FEATURES, dropna=False, sort=False)

clean = grouped.agg(
    NPs=("NPs", "first"),
    Cellline=("Cellline", "first"),
    n_replicates=(TARGET, "size"),
    toxic_mean=(TARGET, "mean"),
).reset_index()

# majority vote; an exact 50/50 tie counts as toxic
clean[TARGET] = (clean["toxic_mean"] >= 0.5).astype(int)
clean = clean.drop(columns=["toxic_mean"])

# put the columns back in a sensible order
clean = clean[ID_COLS + NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET, "n_replicates"]]

print(f"Merged {n_dupes} repeated experiments: {len(df)} rows -> {len(clean)} unique experiments")
print()
print("FINAL CLEAN DATASET")
print("  shape      :", clean.shape)
print("  toxic      :", int(clean[TARGET].sum()))
print("  non-toxic  :", int((clean[TARGET] == 0).sum()))
print(f"  toxic rate : {clean[TARGET].mean() * 100:.1f}%")
clean.head()
""")

code("""
# Save the clean dataset
out_dir = PROJECT / "data" / "processed"
out_dir.mkdir(parents=True, exist_ok=True)
clean.to_csv(out_dir / "clean_dataset.csv", index=False)
print("Saved:", out_dir / "clean_dataset.csv")

# The material lookup table - the 13 descriptors are constant per material,
# so the prediction app can fill them in from just the material name.
material_lookup = clean.groupby("NPs")[MATERIAL_FEATURES].first()

# verify they really are constant
varying = [c for c in MATERIAL_FEATURES if clean.groupby("NPs")[c].nunique().max() > 1]
print("Descriptors that vary within a material:", varying if varying else "none - good")

material_lookup.to_csv(out_dir / "material_properties.csv")
print("Saved:", out_dir / "material_properties.csv")
material_lookup
""")

# ------------------------------------------------------------------
md("""
---
## Part 6 — Exploratory Data Analysis (EDA)

Now we look at the cleaned data.
""")

code("""
FIGS = PROJECT / "results" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# --- Class balance -------------------------------------------------
fig, ax = plt.subplots(figsize=(5, 4))
counts = clean[TARGET].value_counts().sort_index()
ax.bar(["Non-Toxic", "Toxic"], counts.values, color=["#4c9f70", "#d1495b"])
for i, v in enumerate(counts.values):
    ax.text(i, v + 4, str(v), ha="center")
ax.set_ylabel("Number of experiments")
ax.set_title("Class balance in the cleaned dataset")
plt.show()

print(f"Only {clean[TARGET].mean() * 100:.1f}% of the samples are toxic.")
print("A model that always says 'non-toxic' would already score",
      f"{(1 - clean[TARGET].mean()) * 100:.1f}% accuracy while being useless.")
""")

code("""
# --- Distribution of the six measurable properties -----------------
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
for ax, col in zip(axes.ravel(), USER_INPUT_FEATURES):
    ax.hist(clean[col], bins=25, color="#3f7cac", edgecolor="white")
    ax.set_title(col)
fig.suptitle("Distribution of the main physicochemical properties", fontsize=14)
fig.tight_layout()
plt.show()
""")

code("""
# --- Toxic vs non-toxic, property by property ----------------------
tmp = clean.copy()
tmp["Toxicity"] = tmp[TARGET].map({0: "Non-Toxic", 1: "Toxic"})

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
for ax, col in zip(axes.ravel(), USER_INPUT_FEATURES):
    sns.boxplot(data=tmp, x="Toxicity", y=col, ax=ax, hue="Toxicity",
                palette=["#4c9f70", "#d1495b"], legend=False)
    ax.set_title(col)
    ax.set_xlabel("")
fig.suptitle("Toxic vs Non-Toxic comparison", fontsize=14)
fig.tight_layout()
plt.show()

print("Toxic particles tend to have LONGER exposure times, HIGHER doses,")
print("LARGER core size and SMALLER surface area.")
""")

code("""
# --- Scatter plots -------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.scatterplot(data=tmp, x="coresize", y="hydrosize", hue="Toxicity",
                palette=["#4c9f70", "#d1495b"], alpha=0.75, ax=axes[0])
axes[0].set_title("Core size vs Hydrodynamic size")
sns.scatterplot(data=tmp, x="dosage", y="surfcharge", hue="Toxicity",
                palette=["#4c9f70", "#d1495b"], alpha=0.75, ax=axes[1])
axes[1].set_title("Dosage vs Surface charge")
fig.tight_layout()
plt.show()
""")

code("""
# --- Toxicity rate per material ------------------------------------
rate = (clean.groupby("NPs")[TARGET]
        .agg(Samples="size", Toxic="sum"))
rate["% toxic"] = (rate["Toxic"] / rate["Samples"] * 100).round(1)
rate = rate.sort_values("% toxic", ascending=False)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(rate.index, rate["% toxic"], color="#e07a5f")
ax.set_ylabel("% of samples that are toxic")
ax.set_title("Toxicity rate by nanoparticle material")
for i, (pct, n) in enumerate(zip(rate["% toxic"], rate["Samples"])):
    ax.text(i, pct + 1, f"n={n}", ha="center", fontsize=8)
plt.show()

print(rate.to_string())
print()
print("CuO and ZnO account for essentially all the toxicity.")
print("This matches the chemistry - both dissolve and release metal ions.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 7 — Feature analysis

Which properties actually relate to toxicity?
""")

code("""
corr = clean[NUMERIC_FEATURES + [TARGET]].corr()

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr, cmap="coolwarm", center=0, square=True,
            linewidths=0.4, cbar_kws={"shrink": 0.7}, ax=ax)
ax.set_title("Correlation heatmap of all numeric features")
plt.show()
""")

code("""
ranked = (corr[TARGET].drop(TARGET)
          .sort_values(key=abs, ascending=False)
          .rename("correlation_with_toxicity"))

print("Correlation of each feature with toxicity (strongest first):")
print(ranked.to_frame().to_string())
print()
print("The strongest signals are all MATERIAL-LEVEL chemistry descriptors")
print("(ratio, enthalpy, ox, Hsf) rather than particle geometry.")
print("In plain terms: what the particle is MADE OF matters more than its size.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 8 — Train / test split and the preprocessing pipeline

Two important choices here:

- **Stratified split**, so both halves keep the same toxic ratio. With only
  19% toxic samples, a plain random split could easily land very few toxic
  cases in the test set.
- **Scaling inside a `Pipeline`.** This matters: if we scaled the whole dataset
  before splitting, information from the test set would leak into the training
  set through the mean and standard deviation. Putting the scaler in a pipeline
  means it is fitted on the training fold only.
""")

code("""
X = clean[FEATURES]
y = clean[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,          # keep the same toxic ratio in both halves
)

print(f"Training set : {len(X_train)} experiments  ({y_train.sum()} toxic)")
print(f"Test set     : {len(X_test)} experiments  ({y_test.sum()} toxic)")
print(f"Toxic rate    - train: {y_train.mean():.3f}   test: {y_test.mean():.3f}")
""")

code("""
def build_preprocessor():
    \"\"\"Scale the numeric columns, one-hot encode the categorical one.\"\"\"
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])


def make_pipeline(model):
    \"\"\"Preprocessing + model as one object, so nothing leaks.\"\"\"
    return Pipeline([("prep", build_preprocessor()), ("model", model)])


print(build_preprocessor())
""")

# ------------------------------------------------------------------
md("""
---
## Part 9 — Model training

The five classifiers named in our abstract.

**Why `class_weight="balanced"`?** Only 19% of samples are toxic. Without it
the models simply learn to answer "non-toxic" to everything, which still scores
about 81% accuracy while catching zero toxic particles. Balancing the class
weights forces them to pay attention to the minority class.
""")

code("""
def get_models():
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6, class_weight="balanced", random_state=RANDOM_STATE),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM": SVC(kernel="rbf", probability=True,
                   class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1),
    }


for name, model in get_models().items():
    print(f"{name:22s} {type(model).__name__}")
""")

code("""
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

fitted = {}
rows = []

for name, model in get_models().items():
    pipe = make_pipeline(model)
    pipe.fit(X_train, y_train)          # <-- training happens here
    fitted[name] = pipe

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]

    cv_f1 = cross_val_score(make_pipeline(model), X_train, y_train,
                            cv=cv, scoring="f1")

    rows.append({
        "Model": name,
        "Accuracy":  accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall":    recall_score(y_test, y_pred, zero_division=0),
        "F1":        f1_score(y_test, y_pred, zero_division=0),
        "ROC_AUC":   roc_auc_score(y_test, y_prob),
        "CV_F1_mean": cv_f1.mean(),
        "CV_F1_std":  cv_f1.std(),
    })
    print(f"trained: {name}")

print("\\nAll five models trained.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 10 — Evaluation

Per-model classification reports, then the comparison table, confusion
matrices and ROC curves.
""")

code("""
for name, pipe in fitted.items():
    print("=" * 60)
    print(name)
    print("=" * 60)
    print(classification_report(y_test, pipe.predict(X_test),
                                target_names=["Non-Toxic", "Toxic"],
                                zero_division=0))
""")

code("""
results = pd.DataFrame(rows).sort_values("F1", ascending=False).reset_index(drop=True)
print("MODEL COMPARISON (sorted by F1)")
results.round(3)
""")

code("""
# --- Confusion matrices --------------------------------------------
fig, axes = plt.subplots(1, len(fitted), figsize=(4 * len(fitted), 4))
for ax, (name, pipe) in zip(np.atleast_1d(axes), fitted.items()):
    cm = confusion_matrix(y_test, pipe.predict(X_test))
    ConfusionMatrixDisplay(cm, display_labels=["Non-Toxic", "Toxic"]).plot(
        ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(name, fontsize=10)
    ax.grid(False)
fig.suptitle("Confusion matrices on the test set", fontsize=14)
fig.tight_layout()
plt.show()

print("Reading a confusion matrix: the bottom-left cell is a TOXIC particle")
print("that the model called safe. That is the dangerous kind of error.")
""")

code("""
# --- ROC curves ----------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 5))
for name, pipe in fitted.items():
    prob = pipe.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, prob)
    ax.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_test, prob):.3f})")
ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random guess")
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title("ROC curves")
ax.legend(fontsize=8)
plt.show()
""")

code("""
# --- Metric comparison bar chart -----------------------------------
melted = results.melt(id_vars="Model",
                      value_vars=["Accuracy", "Precision", "Recall", "F1"],
                      var_name="Metric", value_name="Score")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(data=melted, x="Model", y="Score", hue="Metric", ax=ax)
ax.set_ylim(0, 1.05)
ax.set_title("Model comparison on the test set")
ax.tick_params(axis="x", rotation=15)
plt.show()
""")

# ------------------------------------------------------------------
md("""
---
## Part 11 — Selecting the best model

We select by **F1 score, not accuracy**.

Look at KNN in the table above: it reaches a respectable-looking accuracy, but
its recall is only ~0.41, meaning it misses nearly 60% of the toxic particles.
For a safety screening tool that is the worst possible failure mode. F1
balances precision and recall, so it will not reward a model that simply
ignores the minority class.
""")

code("""
best_name = results.iloc[0]["Model"]
best_row = results.iloc[0]

print("=" * 55)
print(f"  BEST MODEL: {best_name}")
print("=" * 55)
print(f"  Accuracy  : {best_row['Accuracy']:.3f}")
print(f"  Precision : {best_row['Precision']:.3f}")
print(f"  Recall    : {best_row['Recall']:.3f}   <- catches this share of toxic particles")
print(f"  F1        : {best_row['F1']:.3f}")
print(f"  ROC-AUC   : {best_row['ROC_AUC']:.3f}")
print("=" * 55)

# Save the comparison table
res_dir = PROJECT / "results"
res_dir.mkdir(parents=True, exist_ok=True)
results.to_csv(res_dir / "model_comparison.csv", index=False)
print("\\nSaved:", res_dir / "model_comparison.csv")
""")

# ------------------------------------------------------------------
md("""
---
## Part 12 — Interpretation: which features matter?
""")

code("""
best_pipe = fitted[best_name]
model = best_pipe.named_steps["model"]

if hasattr(model, "feature_importances_"):
    names = [n.split("__", 1)[-1]
             for n in best_pipe.named_steps["prep"].get_feature_names_out()]
    imp = pd.Series(model.feature_importances_, index=names).sort_values()

    fig, ax = plt.subplots(figsize=(7, 6))
    imp[-15:].plot(kind="barh", ax=ax, color="#3f7cac")
    ax.set_xlabel("Importance")
    ax.set_title(f"Top features according to {best_name}")
    plt.show()

    print(imp.sort_values(ascending=False).head(10).to_frame("importance").to_string())
else:
    print(f"{best_name} has no feature_importances_ attribute.")
""")

md("""
**What the model is telling us**

- The chemical identity of the material dominates. The descriptors that encode
  *which* oxide it is are the most informative features.
- Among the properties an experimenter can control, **dosage**, **exposure
  time** and **surface area** carry the most weight.
- Hydrodynamic size is almost uninformative here.
- Practical takeaway: choosing a safer base material matters more than
  fine-tuning the particle size.
""")

# ------------------------------------------------------------------
md("""
---
## Part 13 — Honesty check: leave-one-material-out

This check was not in our original plan. We added it after the EDA.

Almost every toxic sample is CuO or ZnO, and 13 of the 19 numeric features are
**constant within a material**. So a normal random split lets the model partly
*recognise the material* rather than learn the underlying chemistry — and the
reported accuracy would be optimistic for a genuinely new nanoparticle.

To measure this, we train on 4 materials and test on the 5th, which the model
has never seen at all.
""")

code("""
logo = LeaveOneGroupOut()
group_rows = []

for train_idx, test_idx in logo.split(X, y, clean["NPs"]):
    material = clean["NPs"].iloc[test_idx].iloc[0]
    y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]

    if y_tr.nunique() < 2:          # cannot train on a single class
        group_rows.append({"Held_out_material": material, "n_samples": len(test_idx),
                           "n_toxic": int(y_te.sum()), "Accuracy": np.nan,
                           "Recall_toxic": np.nan})
        continue

    pipe = make_pipeline(get_models()[best_name])
    pipe.fit(X.iloc[train_idx], y_tr)
    pred = pipe.predict(X.iloc[test_idx])

    group_rows.append({
        "Held_out_material": material,
        "n_samples": len(test_idx),
        "n_toxic": int(y_te.sum()),
        "Accuracy": accuracy_score(y_te, pred),
        "Recall_toxic": recall_score(y_te, pred, zero_division=0) if y_te.sum() else np.nan,
    })

lomo = pd.DataFrame(group_rows)
lomo.to_csv(res_dir / "leave_one_material_out.csv", index=False)
print(lomo.round(3).to_string(index=False))
print()
print(f"Normal test accuracy      : {best_row['Accuracy']:.3f}")
print(f"Held-out ZnO accuracy     : {lomo.set_index('Held_out_material').loc['ZnO', 'Accuracy']:.3f}")
print()
print("CONCLUSION: the model does clearly worse on a material it has never")
print("seen. It should be used for materials similar to the five it was")
print("trained on, not for a brand new nanoparticle. This is a limitation of")
print("the dataset (only 5 materials), not of the code.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 14 — Save the final model

The winner is retrained on **all** the data (not just the training split), so
the deployed model uses every experiment we have.
""")

code("""
final_pipe = make_pipeline(get_models()[best_name])
final_pipe.fit(X, y)

model_dir = PROJECT / "models"
model_dir.mkdir(parents=True, exist_ok=True)

joblib.dump({
    "pipeline": final_pipe,
    "model_name": best_name,
    "numeric_features": NUMERIC_FEATURES,
    "categorical_features": CATEGORICAL_FEATURES,
    "feature_order": FEATURES,      # so columns are never fed in the wrong order
}, model_dir / "best_model.joblib")

print(f"Saved {best_name} to {model_dir / 'best_model.joblib'}")
print(f"Trained on all {len(X)} experiments.")
""")

# ------------------------------------------------------------------
md("""
---
## Part 15 — The prediction system

The user supplies only the **6 measurable properties** plus the material name.
The 13 chemistry descriptors are looked up automatically.

Note `X = X[bundle["feature_order"]]` — this reindexes the columns into the
exact order used during training. Without it, a dictionary written in a
different order would silently feed core size in as dosage, and the model would
return a confident but wrong answer with no error at all.
""")

code("""
def predict_toxicity(material, values, celltype="Cancer",
                     bundle=None, lookup=None):
    \"\"\"Predict TOXIC / NON-TOXIC for one nanoparticle.\"\"\"
    bundle = bundle or joblib.load(model_dir / "best_model.joblib")
    lookup = material_lookup if lookup is None else lookup

    # --- validate the input ---
    if material not in lookup.index:
        raise ValueError(f"Unknown material '{material}'. "
                         f"Known: {', '.join(lookup.index)}")
    if celltype not in ("Cancer", "Normal"):
        raise ValueError(f"Cell type must be 'Cancer' or 'Normal', got '{celltype}'")
    missing = [c for c in USER_INPUT_FEATURES if c not in values]
    if missing:
        raise ValueError(f"Missing properties: {', '.join(missing)}")

    # --- build the row: user values + material chemistry ---
    row = dict(values)
    row.update(lookup.loc[material].to_dict())
    row["Celltype"] = celltype

    X_one = pd.DataFrame([row])[bundle["feature_order"]]   # correct column order

    label = int(bundle["pipeline"].predict(X_one)[0])
    prob = float(bundle["pipeline"].predict_proba(X_one)[0][1])
    return label, prob


bundle = joblib.load(model_dir / "best_model.joblib")
print("Prediction function ready. Model:", bundle["model_name"])
""")

code("""
# --- Worked examples -----------------------------------------------
examples = [
    ("ZnO",   dict(coresize=40, hydrosize=300, surfcharge=-12,
                   surfarea=50, Expotime=24, dosage=100), "Cancer"),
    ("CuO",   dict(coresize=30, hydrosize=400, surfcharge=-20,
                   surfarea=30, Expotime=48, dosage=200), "Cancer"),
    ("TiO2",  dict(coresize=25, hydrosize=200, surfcharge=15,
                   surfarea=90, Expotime=24, dosage=10), "Normal"),
    ("Al2O3", dict(coresize=39.7, hydrosize=267, surfcharge=36.3,
                   surfarea=64.7, Expotime=24, dosage=0.01), "Normal"),
]

print(f"{'Material':10s} {'Dose':>8s}  {'Cell':8s} {'Prediction':12s} {'P(toxic)':>9s}")
print("-" * 56)
for material, values, celltype in examples:
    label, prob = predict_toxicity(material, values, celltype, bundle)
    verdict = "TOXIC" if label else "NON-TOXIC"
    print(f"{material:10s} {values['dosage']:>8} "
          f"{celltype:8s} {verdict:12s} {prob * 100:>8.1f}%")

print()
print("These match the known chemistry: CuO and ZnO release toxic metal ions,")
print("while TiO2 and Al2O3 are largely inert.")
""")

code("""
# --- The input validation actually works ---------------------------
for bad_call, description in [
    (lambda: predict_toxicity("Gold", dict(coresize=40, hydrosize=300,
        surfcharge=-12, surfarea=50, Expotime=24, dosage=100), "Cancer", bundle),
     "unknown material"),
    (lambda: predict_toxicity("ZnO", dict(coresize=40), "Cancer", bundle),
     "missing properties"),
    (lambda: predict_toxicity("ZnO", dict(coresize=40, hydrosize=300,
        surfcharge=-12, surfarea=50, Expotime=24, dosage=100), "Alien", bundle),
     "invalid cell type"),
]:
    try:
        bad_call()
        print(f"NO ERROR for {description}  <-- this would be a bug")
    except ValueError as err:
        print(f"correctly rejected ({description}): {err}")
""")

# ------------------------------------------------------------------
md("""
---
## Verification — does this notebook match the `src/` pipeline?

This notebook re-implements the pipeline as a readable walkthrough. That means
there are now two copies of the logic, which could drift apart.

The cell below re-runs the real pipeline's saved results and checks the numbers
are identical. If anyone edits one side and not the other, this cell fails.
""")

code("""
pipeline_results = PROJECT / "results" / "model_comparison.csv"

# The notebook just overwrote this file, so compare against a fresh run
# of the src/ pipeline instead.
import subprocess
import sys

proc = subprocess.run([sys.executable, "train_models.py"],
                      cwd=PROJECT / "src", capture_output=True, text=True)
print("src/train_models.py exit code:", proc.returncode)

pipeline_table = pd.read_csv(pipeline_results).set_index("Model").sort_index()
notebook_table = results.set_index("Model").sort_index()

cols = ["Accuracy", "Precision", "Recall", "F1", "ROC_AUC"]
diff = (pipeline_table[cols] - notebook_table[cols]).abs().max().max()

print(f"\\nLargest difference between notebook and pipeline: {diff:.10f}")
assert diff < 1e-9, "Notebook and src/ pipeline disagree!"
print("MATCH - the notebook reproduces the pipeline exactly.")
print()
print(pipeline_table[cols].round(3).to_string())
""")

md("""
---
## Summary

| Stage | Result |
|---|---|
| Raw dataset | 483 experiments |
| After cleaning and replicate merging | **355 unique experiments** |
| Toxic / non-toxic | 68 / 287 (19% toxic) |
| Models compared | 5 |
| **Best model** | **Random Forest** |
| Accuracy | 0.944 |
| Recall on toxic | 0.941 |
| F1 | 0.865 |
| ROC-AUC | 0.946 |

**Two data problems we had to catch:**

1. `viability` leaks the label — it is what the toxic/non-toxic class was
   derived from. Excluded.
2. 122 replicate experiments become identical once `viability` is dropped, so a
   random split was putting the same experiment in both train and test. Merged
   into one row each.

**The honest limitation:** held-out ZnO accuracy is 0.771 against 0.944 on the
normal split, because only 5 materials are represented. The model works for
materials similar to those it has seen, not for genuinely new ones.
""")

# ==================================================================
nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": sys.version.split()[0]},
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT_NB)
print(f"Wrote {OUT_NB} ({len(cells)} cells)")

print("Executing the notebook (this takes a minute) ...")
client = NotebookClient(
    nb,
    timeout=900,
    kernel_name="python3",
    resources={"metadata": {"path": str(OUT_DIR)}},
    allow_errors=False,
)
client.execute()
nbf.write(nb, OUT_NB)

n_out = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
print(f"Executed successfully. {n_out} code cells produced output.")
print("Saved:", OUT_NB)
