"""
Step 3 - Dataset Collection
---------------------------
Downloads the nanoparticle toxicity dataset if it is not already
present in data/raw/.

Run:  python src/download_data.py
"""

import sys
import urllib.request

import config


def download():
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    if config.RAW_FILE.exists():
        print(f"Dataset already present at {config.RAW_FILE}")
        print("Delete it first if you want a fresh copy.")
        return

    print(f"Downloading from {config.DATA_URL} ...")
    try:
        urllib.request.urlretrieve(config.DATA_URL, config.RAW_FILE)
    except Exception as err:
        print("Download failed:", err)
        print("You can also download the file manually and save it as:")
        print("  ", config.RAW_FILE)
        sys.exit(1)

    size_kb = config.RAW_FILE.stat().st_size / 1024
    print(f"Saved {config.RAW_FILE.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    download()
