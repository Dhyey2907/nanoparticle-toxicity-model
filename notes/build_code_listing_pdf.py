"""
Builds the complete code listing PDF - every source file, grouped by the
stage of the project it belongs to.

Run:  python notes/build_code_listing_pdf.py
"""

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, TextLexer

PROJECT = Path(__file__).resolve().parent.parent
OUT_PDF = PROJECT / "Nanoparticle_Toxicity_Code_Listing.pdf"
OUT_HTML = PROJECT / "notes" / "code_listing.html"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# ------------------------------------------------------------------
# The bifurcation: which file belongs to which stage of the project
# ------------------------------------------------------------------
STAGES = [
    {
        "id": "A",
        "title": "Configuration",
        "workflow": "Shared by every step",
        "blurb": (
            "Every path and column name lives in one file, so the rest of the "
            "project never hard-codes them. Changing the dataset mostly means "
            "editing only this file."
        ),
        "files": ["src/config.py"],
    },
    {
        "id": "B",
        "title": "Dataset Collection",
        "workflow": "Step 3",
        "blurb": (
            "Downloads the NanoTox dataset if it is not already present, so the "
            "whole project can be rebuilt from an empty folder."
        ),
        "files": ["src/download_data.py"],
    },
    {
        "id": "C",
        "title": "Data Understanding and Raw Data Cleaning",
        "workflow": "Steps 4 and 5",
        "blurb": (
            "describe_data() prints the report on the raw file. clean_data() does "
            "the cleaning: duplicate removal, target encoding, dropping the leaky "
            "viability column, type coercion and median filling. "
            "collapse_replicates() then merges repeated experiments into one row "
            "each, which is what takes the dataset from 477 rows to 355 unique "
            "experiments."
        ),
        "files": ["src/preprocess.py"],
    },
    {
        "id": "D",
        "title": "Exploratory Data Analysis and Feature Analysis",
        "workflow": "Steps 6 and 7",
        "blurb": (
            "Produces all ten figures and ranks the features by their correlation "
            "with toxicity."
        ),
        "files": ["src/eda.py"],
    },
    {
        "id": "E",
        "title": "Model Development, Training, Testing and Evaluation",
        "workflow": "Steps 8 to 13",
        "blurb": (
            "Builds the five classifiers, trains them, evaluates them on the held-"
            "out test set, plots the confusion matrices and ROC curves, selects the "
            "best model by F1, saves it, and runs the leave-one-material-out "
            "generalisation check."
        ),
        "files": ["src/train_models.py"],
    },
    {
        "id": "F",
        "title": "Final Prediction System",
        "workflow": "Step 14",
        "blurb": (
            "Two front ends. predict.py is the command line tool and holds the "
            "shared predict() function; app.py is the Streamlit web app and calls "
            "that same function, so the two can never disagree."
        ),
        "files": ["src/predict.py", "app.py"],
    },
    {
        "id": "G",
        "title": "Pipeline Runner",
        "workflow": "Runs steps 3 to 13 in order",
        "blurb": "One command that executes the whole pipeline from start to finish.",
        "files": ["run_all.py"],
    },
    {
        "id": "H",
        "title": "Bug Sweep Test Suite",
        "workflow": "Step 15",
        "blurb": (
            "The 18 tests written during the bug sweep. The leakage test and the "
            "duplicate test are the two that caught real problems."
        ),
        "files": ["tests/test_pipeline.py"],
    },
]

SUPPORT_FILES = ["requirements.txt", "dataset/README.txt"]


def find_chrome():
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    for name in ["chrome", "google-chrome", "msedge"]:
        found = shutil.which(name)
        if found:
            return found
    return None


formatter = HtmlFormatter(nowrap=False, cssclass="src", linenos="table")


def render_file(relpath):
    path = PROJECT / relpath
    if not path.exists():
        return f'<p class="missing">[{relpath} not found]</p>'
    source = path.read_text(encoding="utf-8")
    lexer = PythonLexer() if path.suffix == ".py" else TextLexer()
    body = highlight(source, lexer, formatter)
    n_lines = source.count("\n") + 1
    return f"""
<div class="filecard">
  <div class="filehead">
    <span class="fname">{html.escape(relpath)}</span>
    <span class="flines">{n_lines} lines</span>
  </div>
  {body}
</div>"""


CSS = (
    HtmlFormatter().get_style_defs(".src")
    + """
@page { size: A4; margin: 15mm 12mm 15mm 12mm; }
:root { color-scheme: light; }
html { background: #fff; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10pt; line-height: 1.5; color: #1a1a1a;
  background: #fff; margin: 0;
}
h1 { font-size: 19pt; color: #10365c; margin: 0 0 4px 0; }
h2 {
  font-size: 13.5pt; color: #10365c; margin: 0 0 6px 0;
  padding-bottom: 4px; border-bottom: 2px solid #10365c;
}
p { margin: 6px 0; text-align: justify; }
code {
  font-family: Consolas, "Courier New", monospace; font-size: 8.5pt;
  background: #eef2f6; padding: 1px 4px; border-radius: 3px;
}
table.overview { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9pt; }
table.overview th {
  background: #10365c; color: #fff; text-align: left; padding: 6px 8px;
}
table.overview td { padding: 5px 8px; border-bottom: 1px solid #dde3ea; vertical-align: top; }
table.overview tr:nth-child(even) td { background: #f7f9fb; }

.cover { text-align: center; padding-top: 60mm; page-break-after: always; }
.cover h1 { font-size: 25pt; line-height: 1.25; }
.cover .sub { font-size: 13pt; color: #444; margin-top: 10px; }
.cover .rule { width: 70mm; height: 3px; background: #10365c; margin: 22px auto; }
.cover table { width: 78%; margin: 26px auto; font-size: 11pt; border-collapse: collapse; }
.cover th { background: #10365c; color: #fff; padding: 6px 10px; text-align: left; }
.cover td { padding: 5px 10px; border-bottom: 1px solid #dde3ea; }

.stage { page-break-before: always; }
.stagehead {
  background: #10365c; color: #fff; padding: 10px 14px;
  border-radius: 5px; margin-bottom: 10px;
}
.stagehead .sid {
  display: inline-block; background: #fff; color: #10365c;
  width: 26px; height: 26px; line-height: 26px; text-align: center;
  border-radius: 50%; font-weight: 700; margin-right: 9px; font-size: 11pt;
}
.stagehead .stitle { font-size: 13pt; font-weight: 600; }
.stagehead .swork {
  float: right; font-size: 9pt; opacity: .85;
  background: rgba(255,255,255,.15); padding: 3px 10px; border-radius: 10px;
}
.blurb {
  background: #f2f6fa; border-left: 4px solid #10365c;
  padding: 8px 12px; margin: 0 0 12px 0; font-size: 9.5pt;
}
.filecard {
  border: 1px solid #d8dee4; border-radius: 5px;
  margin: 12px 0; overflow: hidden;
}
.filehead {
  background: #eef2f6; padding: 5px 10px; border-bottom: 1px solid #d8dee4;
  font-family: Consolas, "Courier New", monospace; font-size: 9pt;
}
.filehead .fname { font-weight: 700; color: #10365c; }
.filehead .flines { float: right; color: #666; font-size: 8pt; }

.src, .src table { font-family: Consolas, "Courier New", monospace; font-size: 7.4pt; }
.src pre { margin: 0; padding: 0; line-height: 1.35; white-space: pre-wrap; word-wrap: break-word; }
.src table { border-collapse: collapse; width: 100%; }
.src td { padding: 6px 8px; vertical-align: top; border: none; background: #fff; }
.src td.linenos { color: #aab; text-align: right; border-right: 1px solid #e3e8ee;
                  background: #fafbfc; user-select: none; width: 1%; }
.src .linenodiv pre { color: #aab; }
.missing { color: #c0392b; }
.note {
  background: #fff8e6; border-left: 4px solid #e0a800;
  padding: 8px 12px; margin: 10px 0; font-size: 9.5pt;
}
"""
)


def build_html():
    overview_rows = "".join(
        f"<tr><td><strong>{s['id']}</strong></td>"
        f"<td>{s['title']}</td>"
        f"<td>{s['workflow']}</td>"
        f"<td>{'<br>'.join(f'<code>{f}</code>' for f in s['files'])}</td></tr>"
        for s in STAGES
    )

    stage_blocks = []
    for s in STAGES:
        files_html = "".join(render_file(f) for f in s["files"])
        stage_blocks.append(f"""
<div class="stage">
  <div class="stagehead">
    <span class="swork">{s['workflow']}</span>
    <span class="sid">{s['id']}</span><span class="stitle">{s['title']}</span>
  </div>
  <div class="blurb">{s['blurb']}</div>
  {files_html}
</div>""")

    support_html = "".join(render_file(f) for f in SUPPORT_FILES)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Code Listing</title>
<style>{CSS}</style></head><body>

<div class="cover">
  <h1>Nanoparticle Toxicity Prediction<br>Using Data-Driven Methods</h1>
  <div class="rule"></div>
  <div class="sub">Complete Source Code Listing</div>
  <table>
    <tr><th>Team Member</th><th>Enrolment No.</th></tr>
    <tr><td>Pratham Joshi</td><td>KU2507U0361</td></tr>
    <tr><td>Divyansh Khatri</td><td>KU2507U0188</td></tr>
    <tr><td>Dhyey Bhatt</td><td>KU2507U0138</td></tr>
    <tr><td>Jinay Shah</td><td>KU2507U0070</td></tr>
  </table>
</div>

<h2>Code Bifurcation &ndash; which file does which job</h2>
<p>
The project is split so that each stage of the workflow lives in its own file.
Nothing is duplicated: the web app and the command line tool, for example, both
call the same prediction function rather than each having their own copy.
</p>
<table class="overview">
  <tr><th>Stage</th><th>What it does</th><th>Workflow step</th><th>File</th></tr>
  {overview_rows}
</table>

<div class="note">
<strong>Order of execution.</strong> <code>run_all.py</code> executes stages
B &rarr; C &rarr; D &rarr; E in that order. Stage F is used afterwards, once a
trained model exists. Stage H is run separately with <code>pytest</code>.
</div>

<h2>Supporting files</h2>
{support_html}

{''.join(stage_blocks)}

</body></html>"""


def main():
    html_text = build_html()
    OUT_HTML.write_text(html_text, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(html_text) / 1024:.0f} KB)")

    chrome = find_chrome()
    if chrome is None:
        print("Chrome or Edge not found - open the HTML and print to PDF manually.")
        sys.exit(1)

    profile = tempfile.mkdtemp(prefix="pdfprofile_")
    cmd = [
        chrome, "--headless", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={profile}", "--no-pdf-header-footer",
        f"--print-to-pdf={OUT_PDF}", OUT_HTML.resolve().as_uri(),
    ]
    print("Printing to PDF with", Path(chrome).name, "...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if not OUT_PDF.exists():
        print("PDF was not created.")
        print(result.stderr[-2000:])
        sys.exit(1)

    print(f"Created {OUT_PDF} ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
    shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
