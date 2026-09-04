"""
Step 14 - Final Prediction System (command line version)
---------------------------------------------------------
Loads the saved best model and predicts TOXIC / NON-TOXIC for a
nanoparticle described by the user.

The user only gives the 6 properties they can measure. The rest of
the chemical descriptors are looked up from the material name.

Examples:
    python src/predict.py --demo
    python src/predict.py --material ZnO --coresize 40 --hydrosize 300 \
        --surfcharge -12 --surfarea 50 --expotime 24 --dosage 100

Run without arguments to be asked question by question.
"""

import argparse
import sys

import joblib
import pandas as pd

import config


def load_model():
    if not config.BEST_MODEL_FILE.exists():
        print("No trained model found.")
        print("Run 'python src/train_models.py' first.")
        sys.exit(1)
    return joblib.load(config.BEST_MODEL_FILE)


def load_materials():
    if not config.MATERIAL_FILE.exists():
        print("Material lookup missing. Run 'python src/preprocess.py' first.")
        sys.exit(1)
    return pd.read_csv(config.MATERIAL_FILE, index_col="NPs")


def training_ranges():
    """
    Min and max of each input property in the training data.

    We use this to warn the user when they type something far outside
    what the model has ever seen, because the prediction there is just
    extrapolation and should not be trusted.
    """
    if not config.CLEAN_FILE.exists():
        return None
    df = pd.read_csv(config.CLEAN_FILE)
    return df[config.USER_INPUT_FEATURES].agg(["min", "max"])


def check_ranges(values, ranges):
    """Return a list of warning strings for out-of-range inputs."""
    if ranges is None:
        return []
    warnings = []
    for name, value in values.items():
        if name not in ranges.columns:
            continue
        low, high = ranges.loc["min", name], ranges.loc["max", name]
        if value < low or value > high:
            warnings.append(
                f"{name} = {value} is outside the training range "
                f"({low:g} to {high:g})"
            )
    return warnings


def build_row(material, values, celltype, materials):
    """Put the user values plus the material descriptors into one row."""
    if material not in materials.index:
        raise ValueError(
            f"Unknown material '{material}'. "
            f"Known materials: {', '.join(materials.index)}"
        )
    if celltype not in ("Cancer", "Normal"):
        raise ValueError(f"Cell type must be 'Cancer' or 'Normal', got '{celltype}'")

    missing = [c for c in config.USER_INPUT_FEATURES if c not in values]
    if missing:
        raise ValueError(f"Missing properties: {', '.join(missing)}")

    row = dict(values)
    row.update(materials.loc[material].to_dict())
    row["Celltype"] = celltype
    return pd.DataFrame([row])


def predict(bundle, materials, material, values, celltype):
    row = build_row(material, values, celltype, materials)
    row = row[bundle["feature_order"]]  # same column order as training

    pipeline = bundle["pipeline"]
    label = int(pipeline.predict(row)[0])
    prob = float(pipeline.predict_proba(row)[0][1])
    return label, prob


def show_result(material, values, celltype, label, prob, model_name):
    print()
    print("=" * 50)
    print("        NANOPARTICLE TOXICITY PREDICTION")
    print("=" * 50)
    print(f"  Material          : {material}")
    print(f"  Core size         : {values['coresize']} nm")
    print(f"  Hydrodynamic size : {values['hydrosize']} nm")
    print(f"  Surface charge    : {values['surfcharge']} mV")
    print(f"  Surface area      : {values['surfarea']} m2/g")
    print(f"  Exposure time     : {values['Expotime']} hours")
    print(f"  Dosage            : {values['dosage']} ug/mL")
    print(f"  Cell type         : {celltype}")
    print("-" * 50)
    verdict = "TOXIC" if label == 1 else "NON-TOXIC"
    print(f"  PREDICTION        : {verdict}")
    print(f"  Probability toxic : {prob * 100:.1f}%")
    print(f"  Model used        : {model_name}")
    print("=" * 50)
    for warning in check_ranges(values, training_ranges()):
        print(f"  ! {warning}")
    print("  Note: this is a screening tool, not a lab result.")
    print()


def ask_interactively(materials):
    """Simple question-answer mode for when no arguments are given."""
    print("Enter the nanoparticle details (press Ctrl+C to quit).\n")
    print("Available materials:", ", ".join(materials.index))

    material = input("Material: ").strip()
    while material not in materials.index:
        print("  Not in the list, try again.")
        material = input("Material: ").strip()

    questions = [
        ("coresize", "Core size (nm)"),
        ("hydrosize", "Hydrodynamic size (nm)"),
        ("surfcharge", "Surface charge / zeta potential (mV)"),
        ("surfarea", "Surface area (m2/g)"),
        ("Expotime", "Exposure time (hours)"),
        ("dosage", "Dosage (ug/mL)"),
    ]
    values = {}
    for key, question in questions:
        while True:
            try:
                values[key] = float(input(f"{question}: ").strip())
                break
            except ValueError:
                print("  Please type a number.")

    celltype = input("Cell type [Cancer/Normal] (default Cancer): ").strip()
    if celltype.lower().startswith("n"):
        celltype = "Normal"
    else:
        celltype = "Cancer"

    return material, values, celltype


def run_demo(bundle, materials):
    """A few ready made examples so we can show the app quickly."""
    examples = [
        ("ZnO", dict(coresize=40, hydrosize=300, surfcharge=-12,
                     surfarea=50, Expotime=24, dosage=100), "Cancer"),
        ("TiO2", dict(coresize=25, hydrosize=200, surfcharge=15,
                      surfarea=90, Expotime=24, dosage=10), "Normal"),
        ("Al2O3", dict(coresize=39.7, hydrosize=267, surfcharge=36.3,
                       surfarea=64.7, Expotime=24, dosage=0.01), "Normal"),
        ("CuO", dict(coresize=30, hydrosize=400, surfcharge=-20,
                     surfarea=30, Expotime=48, dosage=200), "Cancer"),
    ]
    for material, values, celltype in examples:
        label, prob = predict(bundle, materials, material, values, celltype)
        show_result(material, values, celltype, label, prob, bundle["model_name"])


def main():
    parser = argparse.ArgumentParser(
        description="Predict whether a nanoparticle is toxic or not."
    )
    parser.add_argument("--material", help="e.g. ZnO, CuO, TiO2, Al2O3, Fe2O3")
    parser.add_argument("--coresize", type=float, help="core size in nm")
    parser.add_argument("--hydrosize", type=float, help="hydrodynamic size in nm")
    parser.add_argument("--surfcharge", type=float, help="surface charge in mV")
    parser.add_argument("--surfarea", type=float, help="surface area in m2/g")
    parser.add_argument("--expotime", type=float, help="exposure time in hours")
    parser.add_argument("--dosage", type=float, help="dosage in ug/mL")
    parser.add_argument("--celltype", default="Cancer", choices=["Cancer", "Normal"])
    parser.add_argument("--demo", action="store_true", help="run some examples")
    args = parser.parse_args()

    bundle = load_model()
    materials = load_materials()

    if args.demo:
        run_demo(bundle, materials)
        return

    needed = ["material", "coresize", "hydrosize", "surfcharge",
              "surfarea", "expotime", "dosage"]
    given = [n for n in needed if getattr(args, n) is not None]

    if not given:
        material, values, celltype = ask_interactively(materials)
    elif len(given) < len(needed):
        missing = [n for n in needed if n not in given]
        print("Missing values:", ", ".join(missing))
        print("Give all of them, or give none to use the interactive mode.")
        sys.exit(1)
    else:
        material = args.material
        celltype = args.celltype
        values = {
            "coresize": args.coresize,
            "hydrosize": args.hydrosize,
            "surfcharge": args.surfcharge,
            "surfarea": args.surfarea,
            "Expotime": args.expotime,
            "dosage": args.dosage,
        }

    try:
        label, prob = predict(bundle, materials, material, values, celltype)
    except ValueError as err:
        print("Error:", err)
        sys.exit(1)

    show_result(material, values, celltype, label, prob, bundle["model_name"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
