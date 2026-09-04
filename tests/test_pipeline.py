"""
Basic tests for the project.

We wrote these while doing the bug sweep at the end of the project.
They check the things that would silently give us wrong results.

Run:  pytest -v
(from the project folder, after running python run_all.py)
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))

import config  # noqa: E402
import predict as predict_module  # noqa: E402
from preprocess import clean_data, load_raw  # noqa: E402


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def clean():
    if not config.CLEAN_FILE.exists():
        pytest.skip("Run 'python run_all.py' first.")
    return pd.read_csv(config.CLEAN_FILE)


@pytest.fixture(scope="module")
def bundle():
    if not config.BEST_MODEL_FILE.exists():
        pytest.skip("Run 'python run_all.py' first.")
    return joblib.load(config.BEST_MODEL_FILE)


@pytest.fixture(scope="module")
def materials():
    if not config.MATERIAL_FILE.exists():
        pytest.skip("Run 'python run_all.py' first.")
    return pd.read_csv(config.MATERIAL_FILE, index_col="NPs")


# ------------------------------------------------------------------
# Data tests
# ------------------------------------------------------------------
def test_raw_file_exists():
    assert config.RAW_FILE.exists(), "raw dataset missing, run download_data.py"


def test_no_leaky_column_in_clean_data(clean):
    """
    The most important test. 'viability' is what the toxic label was
    made from, so if it ever comes back into the clean file our
    accuracy becomes fake.
    """
    for col in config.LEAKY_COLS:
        assert col not in clean.columns, f"leaky column '{col}' is back in the data"


def test_target_is_binary(clean):
    assert set(clean[config.TARGET_NUMERIC].unique()) == {0, 1}


def test_no_missing_values(clean):
    assert clean.isna().sum().sum() == 0


def test_no_duplicate_rows(clean):
    assert clean.duplicated().sum() == 0


def test_all_features_present(clean):
    for col in config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES:
        assert col in clean.columns, f"feature '{col}' missing from clean data"


def test_feature_lists_do_not_overlap():
    """A column must not be both a user input and a material constant."""
    overlap = set(config.USER_INPUT_FEATURES) & set(config.MATERIAL_FEATURES)
    assert not overlap, f"columns in both lists: {overlap}"
    assert (
        set(config.USER_INPUT_FEATURES) | set(config.MATERIAL_FEATURES)
    ) == set(config.NUMERIC_FEATURES)


def test_material_columns_really_are_constant(clean):
    """
    The app fills these in from the material name. If any of them
    actually varied within a material, the app would be feeding the
    model a wrong value.
    """
    for col in config.MATERIAL_FEATURES:
        counts = clean.groupby("NPs")[col].nunique()
        bad = counts[counts > 1]
        assert bad.empty, f"'{col}' is not constant for: {list(bad.index)}"


def test_preprocessing_is_repeatable():
    """Running clean_data twice on the same raw data gives the same thing."""
    a = clean_data(load_raw())
    b = clean_data(load_raw())
    pd.testing.assert_frame_equal(a, b)


# ------------------------------------------------------------------
# Model tests
# ------------------------------------------------------------------
def test_model_bundle_has_what_we_need(bundle):
    for key in ["pipeline", "model_name", "feature_order"]:
        assert key in bundle


def test_feature_order_matches_config(bundle):
    expected = config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES
    assert bundle["feature_order"] == expected


def test_prediction_returns_valid_output(bundle, materials):
    values = dict(
        coresize=40, hydrosize=300, surfcharge=-12,
        surfarea=50, Expotime=24, dosage=100,
    )
    label, prob = predict_module.predict(
        bundle, materials, "ZnO", values, "Cancer"
    )
    assert label in (0, 1)
    assert 0.0 <= prob <= 1.0


def test_unknown_material_is_rejected(bundle, materials):
    values = dict(
        coresize=40, hydrosize=300, surfcharge=-12,
        surfarea=50, Expotime=24, dosage=100,
    )
    with pytest.raises(ValueError):
        predict_module.predict(bundle, materials, "Gold", values, "Cancer")


def test_column_order_does_not_change_the_answer(bundle, materials):
    """
    We shuffle the dict order. build_row must still put the columns in
    the training order, otherwise the model reads the wrong numbers.
    """
    ordered = dict(
        coresize=40, hydrosize=300, surfcharge=-12,
        surfarea=50, Expotime=24, dosage=100,
    )
    shuffled = dict(reversed(list(ordered.items())))
    a = predict_module.predict(bundle, materials, "CuO", ordered, "Cancer")
    b = predict_module.predict(bundle, materials, "CuO", shuffled, "Cancer")
    assert a == b


def test_known_toxic_and_nontoxic_cases(bundle, materials):
    """
    Sanity check with chemistry we know: CuO and ZnO are the toxic ones
    in this dataset, Al2O3 and Fe2O3 are not.
    """
    values = dict(
        coresize=40, hydrosize=300, surfcharge=-12,
        surfarea=50, Expotime=24, dosage=100,
    )
    toxic_label, _ = predict_module.predict(
        bundle, materials, "CuO", values, "Cancer"
    )
    safe_label, _ = predict_module.predict(
        bundle, materials, "Al2O3", values, "Normal"
    )
    assert toxic_label == 1, "CuO at a high dose should come out toxic"
    assert safe_label == 0, "Al2O3 should come out non-toxic"


def test_model_beats_the_lazy_baseline():
    """
    A model that always says 'non-toxic' would score about 0.84
    accuracy and 0.0 F1. Ours has to do better than that.
    """
    if not config.METRICS_FILE.exists():
        pytest.skip("Run 'python src/train_models.py' first.")
    table = pd.read_csv(config.METRICS_FILE)
    best = table.sort_values("F1", ascending=False).iloc[0]
    assert best["F1"] > 0.5, "best model is no better than guessing the majority"
    assert best["Recall"] > 0.5, "model misses more than half of the toxic particles"


def test_app_and_cli_use_the_same_function():
    """
    We had a bug where app.py had its own copy of the prediction code
    and could drift from predict.py. This test makes sure the app
    imports the shared one.
    """
    source = (PROJECT / "app.py").read_text(encoding="utf-8")
    assert "from predict import predict" in source
    assert "predict_proba" not in source, (
        "app.py is doing its own prediction again instead of calling predict.py"
    )


def test_probability_and_label_agree(bundle, materials):
    """label 1 should mean probability >= 0.5 (default threshold)."""
    rng = np.random.default_rng(0)
    for material in materials.index:
        for _ in range(5):
            values = dict(
                coresize=float(rng.uniform(5, 120)),
                hydrosize=float(rng.uniform(50, 1800)),
                surfcharge=float(rng.uniform(-50, 50)),
                surfarea=float(rng.uniform(1, 200)),
                Expotime=float(rng.choice([6, 12, 24, 48, 72])),
                dosage=float(rng.uniform(0.001, 300)),
            )
            label, prob = predict_module.predict(
                bundle, materials, material, values, "Cancer"
            )
            assert label == int(prob >= 0.5), (
                f"{material}: label {label} but probability {prob}"
            )
