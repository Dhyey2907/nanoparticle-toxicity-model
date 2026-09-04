"""
Step 14 - Final Prediction System (web version)
------------------------------------------------
A small Streamlit app so we can demo the project without touching
the terminal.

Run:  streamlit run app.py
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

# Let this file import the modules inside src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import config  # noqa: E402
from predict import check_ranges, training_ranges  # noqa: E402
from predict import predict as predict_toxicity  # noqa: E402

st.set_page_config(page_title="Nanoparticle Toxicity Prediction", page_icon="*")


@st.cache_resource
def load_model():
    if not config.BEST_MODEL_FILE.exists():
        return None
    return joblib.load(config.BEST_MODEL_FILE)


@st.cache_data
def load_materials():
    if not config.MATERIAL_FILE.exists():
        return None
    return pd.read_csv(config.MATERIAL_FILE, index_col="NPs")


@st.cache_data
def load_metrics():
    if not config.METRICS_FILE.exists():
        return None
    return pd.read_csv(config.METRICS_FILE)


st.title("Nanoparticle Toxicity Prediction")
st.caption("Mini project - predicting nanoparticle toxicity using machine learning")

bundle = load_model()
materials = load_materials()

if bundle is None or materials is None:
    st.error(
        "The model or the material table is missing.\n\n"
        "Please run these first:\n\n"
        "```\n"
        "python src/download_data.py\n"
        "python src/preprocess.py\n"
        "python src/train_models.py\n"
        "```"
    )
    st.stop()

tab_predict, tab_results, tab_about = st.tabs(
    ["Prediction", "Model results", "About"]
)

# ------------------------------------------------------------------
# Prediction tab
# ------------------------------------------------------------------
with tab_predict:
    st.subheader("Enter the nanoparticle properties")

    col1, col2 = st.columns(2)

    with col1:
        material = st.selectbox("Nanoparticle material", list(materials.index))
        coresize = st.number_input(
            "Core size (nm)", min_value=1.0, max_value=500.0, value=40.0, step=1.0
        )
        hydrosize = st.number_input(
            "Hydrodynamic size (nm)",
            min_value=1.0, max_value=3000.0, value=300.0, step=10.0,
        )
        surfcharge = st.number_input(
            "Surface charge / zeta potential (mV)",
            min_value=-100.0, max_value=100.0, value=-12.0, step=1.0,
        )

    with col2:
        surfarea = st.number_input(
            "Surface area (m2/g)",
            min_value=0.1, max_value=500.0, value=50.0, step=1.0,
        )
        expotime = st.number_input(
            "Exposure time (hours)",
            min_value=1.0, max_value=200.0, value=24.0, step=1.0,
        )
        dosage = st.number_input(
            "Dosage (ug/mL)",
            min_value=0.0, max_value=1000.0, value=100.0, step=1.0,
        )
        celltype = st.selectbox("Cell type", ["Cancer", "Normal"])

    if st.button("Predict toxicity", type="primary"):
        values = {
            "coresize": coresize,
            "hydrosize": hydrosize,
            "surfcharge": surfcharge,
            "surfarea": surfarea,
            "Expotime": expotime,
            "dosage": dosage,
        }
        # Same function the command line version uses, so the two can
        # never drift apart and give different answers.
        label, prob = predict_toxicity(
            bundle, materials, material, values, celltype
        )

        st.divider()
        if label == 1:
            st.error(f"Prediction: **TOXIC**  (probability {prob * 100:.1f}%)")
        else:
            st.success(f"Prediction: **NON-TOXIC**  (probability of toxic {prob * 100:.1f}%)")

        st.progress(min(max(prob, 0.0), 1.0))
        st.caption(f"Model used: {bundle['model_name']}")

        for warning in check_ranges(values, training_ranges()):
            st.warning(warning)

        st.info(
            "This is a screening tool built on a small dataset. "
            "It is not a replacement for an actual toxicity assay."
        )

# ------------------------------------------------------------------
# Results tab
# ------------------------------------------------------------------
with tab_results:
    st.subheader("How the five models compared")
    metrics = load_metrics()
    if metrics is None:
        st.warning("Run 'python src/train_models.py' to generate the results.")
    else:
        st.dataframe(metrics.round(3), width="stretch")
        st.caption(
            "The best model is chosen by F1 score, not accuracy, because only "
            "about 16% of the samples in the dataset are toxic."
        )

    figures = [
        ("01_class_balance.png", "Class balance"),
        ("03_toxic_vs_nontoxic.png", "Toxic vs non-toxic properties"),
        ("05_correlation_heatmap.png", "Correlation heatmap"),
        ("07_confusion_matrices.png", "Confusion matrices"),
        ("08_roc_curves.png", "ROC curves"),
        ("09_model_comparison.png", "Model comparison"),
        ("10_feature_importance.png", "Feature importance"),
    ]
    for filename, caption in figures:
        path = config.FIGURES_DIR / filename
        if path.exists():
            st.image(str(path), caption=caption, width="stretch")

# ------------------------------------------------------------------
# About tab
# ------------------------------------------------------------------
with tab_about:
    st.markdown(
        """
### Nanoparticle Toxicity Prediction Using Data-Driven Methods

Nanoparticles are widely used in drug delivery because they are small,
have a large surface area and can target specific cells. The same
properties can also make them toxic, so being able to predict toxicity
early helps in designing safer particles.

This project takes physicochemical properties of a nanoparticle
(core size, hydrodynamic size, surface charge, surface area, dosage and
exposure time) plus standard chemical descriptors of the material, and
classifies the particle as **toxic** or **non-toxic**.

**Models compared:** Logistic Regression, Decision Tree, K-Nearest
Neighbors, Support Vector Machine and Random Forest.

**Dataset:** the NanoTox metal-oxide nanoparticle dataset
(477 experiments after cleaning, 5 materials: Al2O3, CuO, Fe2O3,
TiO2, ZnO).

**Known limitation:** almost all the toxic samples in the dataset are
CuO and ZnO. When we hold out a whole material and test on it, the
scores drop a lot. So the model works well for materials similar to
the ones it has seen, and should not be trusted for a completely new
material. This is discussed in the README.
        """
    )
