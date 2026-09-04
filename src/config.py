"""
config.py
---------
All the paths and column names live here so we don't repeat them
in every script. If we ever change the dataset, we mostly only
edit this file.
"""

from pathlib import Path

# ---------- Folders ----------
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = PROJECT_DIR / "models"
RESULTS_DIR = PROJECT_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# Files
RAW_FILE = RAW_DIR / "nanotox_dataset.tsv"
CLEAN_FILE = PROCESSED_DIR / "clean_dataset.csv"
MATERIAL_FILE = PROCESSED_DIR / "material_properties.csv"
BEST_MODEL_FILE = MODEL_DIR / "best_model.joblib"
METRICS_FILE = RESULTS_DIR / "model_comparison.csv"

# Where the dataset came from (see README)
DATA_URL = "https://raw.githubusercontent.com/NanoTox/ToxicityModel/master/dataset.txt"


# ---------- Columns ----------
TARGET_COL = "class"          # "Toxic" / "nonToxic"
TARGET_NUMERIC = "toxic"      # 1 / 0  (we make this in preprocess.py)

# The physicochemical + experimental properties we use as inputs.
# These are the ones the abstract talks about.
NUMERIC_FEATURES = [
    "coresize",      # core size of the particle (nm)
    "hydrosize",     # hydrodynamic size in solution (nm)
    "surfcharge",    # zeta potential / surface charge (mV)
    "surfarea",      # surface area (m2/g)
    "Expotime",      # exposure time (hours)
    "dosage",        # dose given to the cells (ug/mL)
    "Hsf",           # heat of formation
    "Ec",            # conduction band energy
    "Ev",            # valence band energy
    "MeO",           # metal-oxygen bond related descriptor
    "enthalpy",      # enthalpy
    "ratio",         # metal to oxygen ratio
    "e",             # electronegativity
    "esum",          # sum of electronegativity
    "esumbyo",       # electronegativity per oxygen
    "MW",            # molecular weight
    "NMetal",        # number of metal atoms
    "NOxygen",       # number of oxygen atoms
    "ox",            # oxidation state
]

CATEGORICAL_FEATURES = [
    "Celltype",      # Cancer / Normal
]

# IMPORTANT: 'viability' must NEVER be used as a feature.
# The toxic / nonToxic label was created FROM the viability value,
# so keeping it would leak the answer and give a fake 100% accuracy.
LEAKY_COLS = ["viability"]

# 'NPs' (material name) and 'Cellline' are kept in the clean file only
# for plotting / grouping, not for training.
ID_COLS = ["NPs", "Cellline"]

# The 6 properties a user actually measures / chooses in the lab.
# These are the ones the prediction app asks for.
USER_INPUT_FEATURES = [
    "coresize",
    "hydrosize",
    "surfcharge",
    "surfarea",
    "Expotime",
    "dosage",
]

# The remaining descriptors are fixed for a given material
# (Al2O3 always has the same molecular weight, etc.), so the app
# looks them up from data/processed/material_properties.csv instead
# of asking the user.
MATERIAL_FEATURES = [c for c in NUMERIC_FEATURES if c not in USER_INPUT_FEATURES]

RANDOM_STATE = 42
TEST_SIZE = 0.25
