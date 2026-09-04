"""
Runs the whole pipeline in order:
    download -> preprocess -> EDA -> train

Run:  python run_all.py
Then: streamlit run app.py
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"

STEPS = [
    ("Step 3  - Dataset collection", "download_data.py"),
    ("Steps 4-5 - Understanding and preprocessing", "preprocess.py"),
    ("Steps 6-7 - EDA and feature analysis", "eda.py"),
    ("Steps 8-12 - Model training and evaluation", "train_models.py"),
]


def main():
    for title, script in STEPS:
        print("\n" + "#" * 70)
        print("#", title)
        print("#" * 70 + "\n")
        result = subprocess.run([sys.executable, script], cwd=SRC)
        if result.returncode != 0:
            print(f"\n{script} failed. Stopping here.")
            sys.exit(result.returncode)

    print("\n" + "#" * 70)
    print("# Done. Now run:  streamlit run app.py")
    print("#" * 70)


if __name__ == "__main__":
    main()
