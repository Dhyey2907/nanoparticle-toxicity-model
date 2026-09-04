"""
Steps 4 & 5 - Data Understanding + Data Preprocessing
-----------------------------------------------------
Loads the raw tab separated file, prints a small report about it,
cleans it up and saves a tidy CSV in data/processed/.

Run:  python src/preprocess.py
"""

import pandas as pd

import config


def load_raw():
    """Read the raw dataset. It is tab separated, not comma separated."""
    if not config.RAW_FILE.exists():
        raise FileNotFoundError(
            f"{config.RAW_FILE} not found. Run 'python src/download_data.py' first."
        )
    return pd.read_csv(config.RAW_FILE, sep="\t")


def describe_data(df):
    """Step 4 - just look at the data and print what we find."""
    print("=" * 60)
    print("STEP 4 : DATA UNDERSTANDING")
    print("=" * 60)
    print(f"Rows: {df.shape[0]}   Columns: {df.shape[1]}")
    print("\nColumns and data types:")
    print(df.dtypes.to_string())

    print("\nMissing values per column:")
    missing = df.isna().sum()
    if missing.sum() == 0:
        print("  No missing values found.")
    else:
        print(missing[missing > 0].to_string())

    print(f"\nDuplicate rows: {df.duplicated().sum()}")

    print("\nTarget variable distribution:")
    counts = df[config.TARGET_COL].value_counts()
    for label, n in counts.items():
        print(f"  {label:10s} {n:4d}  ({n / len(df) * 100:.1f}%)")
    print("  -> The dataset is imbalanced, so accuracy alone is not enough.")

    if "NPs" in df.columns:
        print("\nNanoparticle materials in the dataset:")
        print(" ", ", ".join(sorted(df["NPs"].unique())))


def clean_data(df):
    """Step 5 - the actual cleaning."""
    print("\n" + "=" * 60)
    print("STEP 5 : DATA PREPROCESSING")
    print("=" * 60)

    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Removed {before - len(df)} duplicate rows.")

    # Make the target numeric: Toxic -> 1, nonToxic -> 0
    df[config.TARGET_NUMERIC] = (
        df[config.TARGET_COL].str.strip().str.lower().eq("toxic").astype(int)
    )
    print("Encoded target: Toxic = 1, nonToxic = 0")

    # Drop the leaky column. See the note in config.py.
    dropped = [c for c in config.LEAKY_COLS if c in df.columns]
    df = df.drop(columns=dropped)
    print(f"Dropped leaky column(s): {dropped}")

    # Numeric columns should really be numeric
    for col in config.NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill any missing numeric value with the median of that column.
    # (This dataset has none, but we keep the step so the pipeline is safe.)
    n_missing = df[config.NUMERIC_FEATURES].isna().sum().sum()
    if n_missing:
        df[config.NUMERIC_FEATURES] = df[config.NUMERIC_FEATURES].fillna(
            df[config.NUMERIC_FEATURES].median()
        )
        print(f"Filled {n_missing} missing numeric values with the column median.")
    else:
        print("No missing numeric values to fill.")

    # Tidy up the categorical column
    for col in config.CATEGORICAL_FEATURES:
        df[col] = df[col].astype(str).str.strip()

    keep = (
        config.ID_COLS
        + config.NUMERIC_FEATURES
        + config.CATEGORICAL_FEATURES
        + [config.TARGET_NUMERIC]
    )
    keep = [c for c in keep if c in df.columns]
    df = df[keep]

    df = collapse_replicates(df)

    print(f"Final clean shape: {df.shape}")
    return df


def collapse_replicates(df):
    """
    Merge repeated experiments into one row.

    We found this during the bug sweep. The raw file has the same
    experiment (same particle, same dose, same cell line) recorded
    several times with a slightly different viability each time.
    Once we drop the viability column those rows become identical.

    That is a problem because train_test_split would then put copies
    of the SAME experiment in both the training set and the test set,
    and the test score would look better than it really is.

    So we keep one row per unique set of properties. If the repeats
    disagree on the label we take the majority, and if it is an exact
    tie we call it toxic, because for a safety tool it is better to
    wrongly warn than to wrongly clear.
    """
    features = config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES

    n_dupes = df.duplicated(subset=features).sum()
    if n_dupes == 0:
        df["n_replicates"] = 1
        return df.reset_index(drop=True)

    grouped = df.groupby(features, dropna=False, sort=False)

    conflicting = (grouped[config.TARGET_NUMERIC].nunique() > 1).sum()

    merged = grouped.agg(
        NPs=("NPs", "first"),
        Cellline=("Cellline", "first"),
        n_replicates=(config.TARGET_NUMERIC, "size"),
        toxic_mean=(config.TARGET_NUMERIC, "mean"),
    ).reset_index()

    # majority vote, ties count as toxic
    merged[config.TARGET_NUMERIC] = (merged["toxic_mean"] >= 0.5).astype(int)
    merged = merged.drop(columns=["toxic_mean"])

    print(
        f"Merged {n_dupes} repeated experiments "
        f"({len(df)} rows -> {len(merged)} unique experiments)."
    )
    print(
        f"  {conflicting} of them had repeats that disagreed on the label "
        f"- majority vote used."
    )

    order = (
        config.ID_COLS
        + config.NUMERIC_FEATURES
        + config.CATEGORICAL_FEATURES
        + [config.TARGET_NUMERIC, "n_replicates"]
    )
    return merged[[c for c in order if c in merged.columns]].reset_index(drop=True)


def save_material_lookup(df):
    """
    Build a small lookup table of the descriptors that are fixed for
    a material (molecular weight, enthalpy, oxidation state ...).

    The prediction app uses this so the user only has to type the 6
    properties they can actually measure, and we fill in the chemistry
    for them.
    """
    lookup = df.groupby("NPs")[config.MATERIAL_FEATURES].first()

    # Sanity check: these really should be constant inside a material.
    varying = [
        c
        for c in config.MATERIAL_FEATURES
        if df.groupby("NPs")[c].nunique().max() > 1
    ]
    if varying:
        print(f"  warning: these are NOT constant per material: {varying}")

    lookup.to_csv(config.MATERIAL_FILE)
    print(f"Saved material lookup ({len(lookup)} materials) to {config.MATERIAL_FILE}")


def main():
    df = load_raw()
    describe_data(df)
    clean = clean_data(df)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(config.CLEAN_FILE, index=False)
    print(f"\nSaved cleaned data to {config.CLEAN_FILE}")
    save_material_lookup(clean)


if __name__ == "__main__":
    main()
