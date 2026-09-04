"""
Steps 6 & 7 - Exploratory Data Analysis + Feature Analysis
-----------------------------------------------------------
Makes the plots that go into the report and saves them in
results/figures/.

Run:  python src/eda.py
"""

import matplotlib

matplotlib.use("Agg")  # save plots to files instead of opening windows

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config

sns.set_theme(style="whitegrid")

# The properties the abstract specifically mentions - we plot these in
# detail. Same list the prediction app asks the user for.
MAIN_PROPS = config.USER_INPUT_FEATURES


def load_clean():
    if not config.CLEAN_FILE.exists():
        raise FileNotFoundError(
            f"{config.CLEAN_FILE} not found. Run 'python src/preprocess.py' first."
        )
    return pd.read_csv(config.CLEAN_FILE)


def save(fig, name):
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / name
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("  saved", path.name)


def plot_target_balance(df):
    fig, ax = plt.subplots(figsize=(5, 4))
    counts = df[config.TARGET_NUMERIC].value_counts().sort_index()
    ax.bar(["Non-Toxic", "Toxic"], counts.values, color=["#4c9f70", "#d1495b"])
    for i, v in enumerate(counts.values):
        ax.text(i, v + 4, str(v), ha="center")
    ax.set_ylabel("Number of samples")
    ax.set_title("Class balance in the dataset")
    save(fig, "01_class_balance.png")


def plot_histograms(df):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.ravel(), MAIN_PROPS):
        ax.hist(df[col], bins=25, color="#3f7cac", edgecolor="white")
        ax.set_title(col)
        ax.set_xlabel("")
    fig.suptitle("Distribution of the main physicochemical properties", fontsize=14)
    fig.tight_layout()
    save(fig, "02_histograms.png")


def plot_toxic_vs_nontoxic(df):
    """Box plots comparing toxic and non-toxic groups."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    tmp = df.copy()
    tmp["Toxicity"] = tmp[config.TARGET_NUMERIC].map({0: "Non-Toxic", 1: "Toxic"})
    for ax, col in zip(axes.ravel(), MAIN_PROPS):
        sns.boxplot(
            data=tmp, x="Toxicity", y=col, ax=ax,
            hue="Toxicity", palette=["#4c9f70", "#d1495b"], legend=False,
        )
        ax.set_title(col)
        ax.set_xlabel("")
    fig.suptitle("Toxic vs Non-Toxic comparison", fontsize=14)
    fig.tight_layout()
    save(fig, "03_toxic_vs_nontoxic.png")


def plot_scatter(df):
    tmp = df.copy()
    tmp["Toxicity"] = tmp[config.TARGET_NUMERIC].map({0: "Non-Toxic", 1: "Toxic"})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.scatterplot(
        data=tmp, x="coresize", y="hydrosize", hue="Toxicity",
        palette=["#4c9f70", "#d1495b"], alpha=0.75, ax=axes[0],
    )
    axes[0].set_title("Core size vs Hydrodynamic size")
    sns.scatterplot(
        data=tmp, x="dosage", y="surfcharge", hue="Toxicity",
        palette=["#4c9f70", "#d1495b"], alpha=0.75, ax=axes[1],
    )
    axes[1].set_title("Dosage vs Surface charge")
    fig.tight_layout()
    save(fig, "04_scatter_plots.png")


def plot_correlation(df):
    cols = config.NUMERIC_FEATURES + [config.TARGET_NUMERIC]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, cmap="coolwarm", center=0, square=True,
                linewidths=0.4, cbar_kws={"shrink": 0.7}, ax=ax)
    ax.set_title("Correlation heatmap of all numeric features")
    save(fig, "05_correlation_heatmap.png")

    # Which features move the most with toxicity?
    print("\nCorrelation of each feature with toxicity (strongest first):")
    ranked = (
        corr[config.TARGET_NUMERIC]
        .drop(config.TARGET_NUMERIC)
        .sort_values(key=abs, ascending=False)
    )
    for name, value in ranked.items():
        print(f"  {name:12s} {value:+.3f}")
    return ranked


def plot_by_material(df):
    rate = (
        df.groupby("NPs")[config.TARGET_NUMERIC]
        .agg(["mean", "count"])
        .sort_values("mean", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(rate.index, rate["mean"] * 100, color="#e07a5f")
    ax.set_ylabel("% of samples that are toxic")
    ax.set_title("Toxicity rate by nanoparticle material")
    for i, (m, c) in enumerate(zip(rate["mean"], rate["count"])):
        ax.text(i, m * 100 + 1, f"n={c}", ha="center", fontsize=8)
    save(fig, "06_toxicity_by_material.png")
    print("\nToxicity rate per material:")
    print((rate["mean"] * 100).round(1).to_string())


def main():
    df = load_clean()
    print("Making EDA plots ...")
    plot_target_balance(df)
    plot_histograms(df)
    plot_toxic_vs_nontoxic(df)
    plot_scatter(df)
    ranked = plot_correlation(df)
    plot_by_material(df)

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ranked.rename("correlation_with_toxicity").to_csv(
        config.RESULTS_DIR / "feature_correlation.csv"
    )
    print("\nAll figures are in", config.FIGURES_DIR)


if __name__ == "__main__":
    main()
