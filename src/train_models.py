"""
Steps 8 to 12 - Model Development, Training, Testing, Evaluation,
                and picking the best model
------------------------------------------------------------------
Trains the five classifiers listed in the abstract:
    Logistic Regression, Decision Tree, KNN, SVM, Random Forest
compares them, and saves the winner to models/best_model.joblib.

Run:  python src/train_models.py
"""

import matplotlib

matplotlib.use("Agg")

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

import config

sns.set_theme(style="whitegrid")


def build_preprocessor():
    """Scale the numbers, one-hot encode the Cell type column."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), config.NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                config.CATEGORICAL_FEATURES,
            ),
        ]
    )


def get_models():
    """
    The five classifiers mentioned in the abstract.

    class_weight = balanced is used because only about 16% of the
    samples are toxic. Without it the models just predict non-toxic
    for everything and still look 84% accurate, which is useless.
    """
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
        ),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM": SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
            n_jobs=-1,
        ),
    }


def make_pipeline(model):
    return Pipeline([("prep", build_preprocessor()), ("model", model)])


def evaluate(name, pipe, X_test, y_test):
    """Step 11 - all the metrics for one model."""
    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    return {
        "Model": name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1": f1_score(y_test, y_pred, zero_division=0),
        "ROC_AUC": roc_auc_score(y_test, y_prob),
    }


def plot_confusion_matrices(fitted, X_test, y_test):
    n = len(fitted)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    axes = np.atleast_1d(axes)
    for ax, (name, pipe) in zip(axes, fitted.items()):
        cm = confusion_matrix(y_test, pipe.predict(X_test))
        ConfusionMatrixDisplay(
            cm, display_labels=["Non-Toxic", "Toxic"]
        ).plot(ax=ax, colorbar=False, cmap="Blues")
        ax.set_title(name, fontsize=10)
        ax.grid(False)
    fig.suptitle("Confusion matrices on the test set", fontsize=14)
    fig.tight_layout()
    path = config.FIGURES_DIR / "07_confusion_matrices.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path.name)


def plot_roc(fitted, X_test, y_test):
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
    path = config.FIGURES_DIR / "08_roc_curves.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path.name)


def plot_scores(table):
    melted = table.melt(
        id_vars="Model",
        value_vars=["Accuracy", "Precision", "Recall", "F1"],
        var_name="Metric",
        value_name="Score",
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=melted, x="Model", y="Score", hue="Metric", ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_title("Model comparison on the test set")
    ax.tick_params(axis="x", rotation=15)
    path = config.FIGURES_DIR / "09_model_comparison.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path.name)


def plot_feature_importance(pipe, name):
    """Step 13 - which properties matter most. Only for tree models."""
    model = pipe.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        print(f"  ({name} has no feature_importances_, skipping that plot)")
        return
    names = pipe.named_steps["prep"].get_feature_names_out()
    names = [n.split("__", 1)[-1] for n in names]
    imp = pd.Series(model.feature_importances_, index=names).sort_values()[-15:]

    fig, ax = plt.subplots(figsize=(7, 6))
    imp.plot(kind="barh", ax=ax, color="#3f7cac")
    ax.set_xlabel("Importance")
    ax.set_title(f"Top features according to {name}")
    path = config.FIGURES_DIR / "10_feature_importance.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path.name)

    imp.sort_values(ascending=False).rename("importance").to_csv(
        config.RESULTS_DIR / "feature_importance.csv"
    )


def leave_one_material_out(df, X, y, best_name):
    """
    Extra check that was not in our original plan, but we added it
    after looking at the EDA.

    Almost every toxic sample in this dataset is CuO or ZnO. A lot of
    the descriptors (enthalpy, oxidation state, molecular weight ...)
    have exactly the same value for every row of a material. So with a
    normal random split, rows of the same material end up in both the
    train and the test set, and the model can partly memorise the
    material instead of learning the chemistry.

    Here we train on 4 materials and test on the 5th one. The scores
    are much lower, and that is the honest estimate of how the model
    would do on a nanoparticle it has never seen.
    """
    print("\n" + "=" * 60)
    print("EXTRA CHECK : LEAVE-ONE-MATERIAL-OUT")
    print("=" * 60)

    groups = df["NPs"]
    logo = LeaveOneGroupOut()
    rows = []

    for train_idx, test_idx in logo.split(X, y, groups):
        material = groups.iloc[test_idx].iloc[0]
        y_tr = y.iloc[train_idx]
        y_te = y.iloc[test_idx]

        if y_tr.nunique() < 2:
            # Cannot train a classifier on a single class.
            rows.append(
                {
                    "Held_out_material": material,
                    "n_samples": len(test_idx),
                    "n_toxic": int(y_te.sum()),
                    "Accuracy": np.nan,
                    "Recall_toxic": np.nan,
                }
            )
            continue

        pipe = make_pipeline(get_models()[best_name])
        pipe.fit(X.iloc[train_idx], y_tr)
        pred = pipe.predict(X.iloc[test_idx])

        rows.append(
            {
                "Held_out_material": material,
                "n_samples": len(test_idx),
                "n_toxic": int(y_te.sum()),
                "Accuracy": accuracy_score(y_te, pred),
                "Recall_toxic": (
                    recall_score(y_te, pred, zero_division=0)
                    if y_te.sum() > 0
                    else np.nan
                ),
            }
        )

    out = pd.DataFrame(rows)
    print(out.round(3).to_string(index=False))
    print(f"\nMean accuracy over held-out materials: {out['Accuracy'].mean():.3f}")
    print("This is the number we quote as the honest generalisation estimate.")
    out.to_csv(config.RESULTS_DIR / "leave_one_material_out.csv", index=False)


def main():
    if not config.CLEAN_FILE.exists():
        raise FileNotFoundError("Run 'python src/preprocess.py' first.")

    df = pd.read_csv(config.CLEAN_FILE)
    feature_cols = config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES
    X = df[feature_cols]
    y = df[config.TARGET_NUMERIC]

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Train / test split, stratified so both sets keep the same
    # toxic to non-toxic ratio.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE,
        stratify=y,
    )
    print(f"Train: {len(X_train)} rows    Test: {len(X_test)} rows")
    print(f"Toxic in train: {y_train.sum()}    Toxic in test: {y_test.sum()}")

    print("\n" + "=" * 60)
    print("STEPS 8-11 : TRAIN, TEST AND EVALUATE THE MODELS")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
    fitted = {}
    scores = []

    for name, model in get_models().items():
        pipe = make_pipeline(model)
        pipe.fit(X_train, y_train)
        fitted[name] = pipe

        row = evaluate(name, pipe, X_test, y_test)
        cv_f1 = cross_val_score(
            make_pipeline(model), X_train, y_train, cv=cv, scoring="f1"
        )
        row["CV_F1_mean"] = cv_f1.mean()
        row["CV_F1_std"] = cv_f1.std()
        scores.append(row)

        print(f"\n--- {name} ---")
        print(
            classification_report(
                y_test,
                pipe.predict(X_test),
                target_names=["Non-Toxic", "Toxic"],
                zero_division=0,
            )
        )

    table = (
        pd.DataFrame(scores)
        .sort_values("F1", ascending=False)
        .reset_index(drop=True)
    )

    print("=" * 60)
    print("STEP 11 : PERFORMANCE COMPARISON")
    print("=" * 60)
    print(table.round(3).to_string(index=False))
    table.to_csv(config.METRICS_FILE, index=False)

    print("\nMaking plots ...")
    plot_confusion_matrices(fitted, X_test, y_test)
    plot_roc(fitted, X_test, y_test)
    plot_scores(table)

    # Step 12 - pick the best model using F1, not accuracy, because
    # of the class imbalance.
    best_name = table.iloc[0]["Model"]
    print("\n" + "=" * 60)
    print(f"STEP 12 : BEST MODEL = {best_name}")
    print(
        f"  F1 = {table.iloc[0]['F1']:.3f}    "
        f"ROC-AUC = {table.iloc[0]['ROC_AUC']:.3f}"
    )
    print("=" * 60)

    plot_feature_importance(fitted[best_name], best_name)

    # Retrain the winner on the whole dataset before saving, so the
    # app in step 14 uses every sample we have.
    final = make_pipeline(get_models()[best_name])
    final.fit(X, y)
    joblib.dump(
        {
            "pipeline": final,
            "model_name": best_name,
            "numeric_features": config.NUMERIC_FEATURES,
            "categorical_features": config.CATEGORICAL_FEATURES,
            "feature_order": feature_cols,
        },
        config.BEST_MODEL_FILE,
    )
    print(f"\nSaved best model to {config.BEST_MODEL_FILE}")

    leave_one_material_out(df, X, y, best_name)


if __name__ == "__main__":
    main()
