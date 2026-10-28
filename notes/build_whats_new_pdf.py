"""
Builds the "what is new in our paper" explainer PDF, in simple words.

This is the viva / presentation prep sheet: what the papers we cited had
already done, what we added on top, and what we should NOT claim.

Run:  python notes/build_whats_new_pdf.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_PDF = PROJECT / "Nanoparticle_Toxicity_What_Is_New.pdf"
OUT_HTML = PROJECT / "notes" / "whats_new.html"

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    for p in CHROME:
        if Path(p).exists():
            return p
    for n in ["chrome", "google-chrome", "msedge"]:
        f = shutil.which(n)
        if f:
            return f
    return None


CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
:root { color-scheme: light; }
html { background:#fff; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.6pt; line-height: 1.55; color:#222; background:#fff; margin:0;
}
h1 { font-size: 21pt; color:#0d3b66; margin: 0 0 6px 0; }
h2 {
  font-size: 15pt; color:#0d3b66; margin: 20px 0 8px 0;
  padding-bottom: 5px; border-bottom: 2.5px solid #0d3b66;
  page-break-after: avoid;
}
h3 { font-size: 12pt; color:#1d5c8f; margin: 15px 0 5px 0; page-break-after: avoid; }
p { margin: 8px 0; }
b, strong { color:#0d3b66; }

.cover { text-align:center; padding-top: 50mm; page-break-after: always; }
.cover h1 { font-size: 26pt; line-height:1.25; border:none; }
.cover .sub { font-size: 13.5pt; color:#555; margin-top: 12px; }
.cover .rule { width: 65mm; height:3px; background:#0d3b66; margin: 24px auto; }
.cover .tag {
  display:inline-block; background:#e8f0f7; color:#0d3b66;
  padding: 8px 20px; border-radius: 18px; font-size: 11pt; margin-top: 18px;
}
.cover table { width:74%; margin: 30px auto; border-collapse:collapse; font-size:11pt; }
.cover th { background:#0d3b66; color:#fff; padding:7px 12px; text-align:left; }
.cover td { padding:6px 12px; border-bottom:1px solid #dde3ea; }

.card {
  border:1.5px solid #d6dfe8; border-radius:9px;
  padding: 12px 16px 14px 16px; margin: 13px 0;
}
.card .hd {
  display:flex; align-items:center; margin-bottom:6px;
  break-after: avoid; page-break-after: avoid;
}
.num {
  background:#0d3b66; color:#fff; min-width:32px; height:32px; line-height:32px;
  border-radius:50%; text-align:center; font-weight:700; font-size:13pt;
  margin-right:12px; flex-shrink:0;
}
.cardtitle { font-size:12.5pt; font-weight:700; color:#0d3b66; }
.card p { margin: 6px 0; }
.star { background:#f5a623; }

.why { background:#eef5fb; border-left:4px solid #2e75b6;
       padding: 9px 14px; margin: 9px 0; font-size:10.4pt; }
.why .lbl { font-weight:700; color:#1d5c8f; }
.oops { background:#fdeceb; border-left:4px solid #c0392b;
        padding: 9px 14px; margin: 9px 0; font-size:10.4pt; }
.oops .lbl { font-weight:700; color:#a93226; }
.win { background:#eaf6ec; border-left:4px solid #2e7d32;
       padding: 9px 14px; margin: 9px 0; font-size:10.4pt; }
.win .lbl { font-weight:700; color:#1e6023; }
.warn { background:#fff8e6; border-left:4px solid #e0a800;
        padding: 9px 14px; margin: 9px 0; font-size:10.4pt; }
.warn .lbl { font-weight:700; color:#9a7600; }

table.t { border-collapse:collapse; width:100%; margin:10px 0; font-size:9.8pt;
          page-break-inside:avoid; }
table.t th { background:#0d3b66; color:#fff; padding:6px 9px; text-align:left; }
table.t td { padding:5px 9px; border-bottom:1px solid #dde3ea; vertical-align:top; }
table.t tr:nth-child(even) td { background:#f7f9fb; }
tr.hi td { background:#eaf6ec !important; font-weight:600; }

ul { margin:8px 0; padding-left:22px; }
li { margin:5px 0; }
.small { font-size:9.5pt; color:#555; }
.qa { margin: 12px 0; page-break-inside: avoid; }
.q { font-weight:700; color:#0d3b66; margin-bottom:3px; }
.a { background:#f7f9fb; border-left:3px solid #9bb5cc; padding:8px 13px; }
.big {
  background:#0d3b66; color:#fff; padding: 16px 20px; border-radius:9px;
  font-size:11.5pt; line-height:1.6; margin: 14px 0;
}
.big b { color:#ffd966; }
"""


HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>What Is New</title>
<style>{CSS}</style></head><body>

<div class="cover">
  <h1>What Is New In Our Paper?</h1>
  <div class="rule"></div>
  <div class="sub">How our work is different from the<br>research papers we referred to</div>
  <div class="tag">Explained in simple words</div>
  <table>
    <tr><th>Team Member</th><th>Enrolment No.</th></tr>
    <tr><td>Pratham Joshi</td><td>KU2507U0361</td></tr>
    <tr><td>Divyansh Khatri</td><td>KU2507U0188</td></tr>
    <tr><td>Dhyey Bhatt</td><td>KU2507U0138</td></tr>
    <tr><td>Jinay Shah</td><td>KU2507U0070</td></tr>
  </table>
</div>

<h2>The Question This Sheet Answers</h2>
<p>
When you write a research paper, the first thing anyone asks is:
<b>"Other people already worked on this. So what did YOU add?"</b>
</p>
<p>
This sheet answers that in plain language. It also tells you honestly which
parts are <b>not</b> new, so nobody can catch you out.
</p>

<h2>Part 1: What The Other Papers Already Did</h2>
<p>
We referred to <b>7 published research papers</b>. Here is what each one had
already figured out, one line each:
</p>

<table class="t">
<tr><th>Paper</th><th>What they already did</th></tr>
<tr><td><b>Puzyn, 2011</b></td>
    <td>Proved for the first time that you <i>can</i> predict toxicity using a computer instead of a lab</td></tr>
<tr><td><b>Liu, 2011</b></td>
    <td>Changed the question from "how toxic?" to a simpler <b>"toxic: yes or no?"</b></td></tr>
<tr><td><b>Oh, 2016</b></td>
    <td>Collected hundreds of studies together and showed the surface and the test conditions matter, not just the material</td></tr>
<tr><td><b>Trinh, 2018</b></td>
    <td><b>Cleaned up</b> nanoparticle datasets and checked their quality before building models</td></tr>
<tr><td><b>Furxhi, 2019</b></td>
    <td><b>Compared many models</b> against each other to see which type works best</td></tr>
<tr><td><b>Furxhi, 2020</b></td>
    <td>Reviewed the whole field and <b>complained about common mistakes</b>: tiny datasets, unfair testing, too much focus on accuracy</td></tr>
<tr><td><b>Subramanian, 2021</b></td>
    <td>Built the <b>dataset we used</b>, plus one model of their own</td></tr>
</table>

<div class="why">
<span class="lbl">Notice the gap:</span> Trinh cleaned data. Furxhi compared
models. But <b>nobody did both on the same dataset</b> &mdash; and nobody checked
what happens when you clean the data <i>and then</i> compare the models. That gap
is where our work sits.
</div>

<h2>Part 2: The Three New Things We Did</h2>

<div class="card">
  <div class="hd"><div class="num star">1</div><div class="cardtitle">The main one: fixing one problem secretly created another</div></div>

  <p>This is our most interesting finding. Follow it slowly, it has two parts.</p>

  <h3>Part A &mdash; the answer was hidden in the data</h3>
  <p>
  The dataset had a column called <i>viability</i> (how many cells survived). But
  the toxic/safe answer was <b>calculated from that exact column</b>. So if the
  computer sees it, it is not predicting &mdash; it is just reading the answer.
  </p>
  <div class="why">
  <span class="lbl">Like this:</span> giving a student an exam with the answer key
  accidentally printed on the back page.
  </div>
  <p>We deleted that column. Problem solved &mdash; or so we thought.</p>

  <h3>Part B &mdash; deleting it caused a brand new problem</h3>
  <p>
  Scientists repeat the same experiment several times. Those repeat rows were
  <b>almost</b> identical &mdash; they only differed in the <i>viability</i>
  number.
  </p>
  <p>
  So the moment we deleted that column, those rows became <b>exactly
  identical</b>. <b>122 duplicate rows appeared out of nowhere.</b>
  </p>
  <div class="oops">
  <span class="lbl">Why that is bad:</span> we split the data into "practice
  questions" and "exam questions." With duplicates around, <b>the same question
  ends up in both</b>. The computer sees the exam paper during practice. Its
  score looks great, but it cheated without anyone noticing.
  </div>

  <div class="win">
  <span class="lbl">The point:</span> <b>fixing problem 1 is what created problem
  2.</b> Most people would fix the first one, feel satisfied, and never look
  again. That chain reaction is the new thing we are reporting.
  </div>

  <p><b>And it actually mattered:</b></p>
  <table class="t">
    <tr><th>&nbsp;</th><th>Before we fixed it</th><th>After we fixed it</th></tr>
    <tr><td>Which model won</td><td>Decision Tree</td><td><b>Random Forest</b></td></tr>
    <tr><td>Its score (F1)</td><td>0.800</td><td><b>0.865</b></td></tr>
    <tr><td>Toxic ZnO caught</td><td>26%</td><td><b>72%</b></td></tr>
  </table>
  <p class="small">
  The Decision Tree had only been "winning" because it was quietly memorising
  the duplicate rows. Fixing the data <b>changed our final answer.</b>
  </p>
</div>

<div class="card">
  <div class="hd"><div class="num">2</div><div class="cardtitle">We tested the model on a material it had never seen</div></div>
  <p>
  Normally you shuffle all the data and split it randomly. But our 5 materials
  each have their own fixed chemistry values &mdash; so the model can secretly
  learn <b>"this is ZnO, and ZnO is usually toxic"</b> instead of learning real
  chemistry.
  </p>
  <p>
  So we ran a harder test: <b>train on 4 materials, then test on the 5th one it
  has never seen at all.</b>
  </p>
  <div class="why">
  <span class="lbl">Like this:</span> a student who scores well on the chapters
  they revised, versus a student given a question from a chapter they have never
  opened. The second test tells you far more.
  </div>
  <div class="oops">
  <span class="lbl">The result:</span> accuracy dropped from <b>94% down to
  77%</b>. The normal random test was hiding this completely.
  </div>
  <p>
  Furxhi's 2020 review <i>complained</i> that people test unfairly. We actually
  did something about it and <b>measured exactly how big the gap is.</b>
  </p>
</div>

<div class="card">
  <div class="hd"><div class="num">3</div><div class="cardtitle">We compared five models on this particular dataset</div></div>
  <p>
  The team who built this dataset (Subramanian, 2021) made <b>one</b> model.
  We tried <b>five</b> and compared them fairly.
  </p>
  <p>
  We also judged them the right way. We did <b>not</b> pick the winner by
  accuracy, because with only 1 in 5 particles being toxic, accuracy lies.
  </p>
  <div class="oops">
  <span class="lbl">Proof that accuracy lies:</span> the KNN model scored
  <b>87.6% accuracy</b> &mdash; looks good! But it caught only <b>41%</b> of the
  toxic particles. It missed nearly 6 out of every 10 dangerous ones. If we had
  judged by accuracy we might have picked it.
  </div>
</div>

<h2>Part 3: What Is NOT New &mdash; Be Honest About This</h2>
<p>
If you claim too much, an examiner will catch it. Here is what you should
<b>not</b> claim:
</p>

<table class="t">
<tr><th>Do NOT say this</th><th>Say this instead</th></tr>
<tr><td>"We invented the idea of data leakage"</td>
    <td>It is a well-known concept in machine learning. <b>Our specific example</b> is what we found</td></tr>
<tr><td>"We invented this way of testing"</td>
    <td>Holding out a whole group is a known technique. <b>Applying it here and measuring the gap</b> is ours</td></tr>
<tr><td>"We found a mistake in Subramanian's paper"</td>
    <td>They made the label from viability themselves, so they knew. The trap only catches <b>people who reuse their dataset later</b></td></tr>
<tr><td>"Nobody has ever reported this"</td>
    <td>"We did not find it in the papers we reviewed." We read 7 papers, not the entire field</td></tr>
</table>

<div class="warn">
<span class="lbl">Why this matters:</span> being careful about what you claim
makes you look <b>more</b> confident, not less. Examiners respect a student who
knows the limits of their own work. Over-claiming is the fastest way to get
picked apart.
</div>

<h2>Part 4: If They Ask You In The Viva</h2>

<div class="qa">
<div class="q">Q. What is new in your work?</div>
<div class="a">
Earlier papers either cleaned the data <b>or</b> compared models. We did both on
the same dataset. While doing it we found that removing the leaking column
<b>creates</b> duplicate rows, and fixing that <b>changed which model won.</b>
</div>
</div>

<div class="qa">
<div class="q">Q. Why does your duplicate finding matter to anyone else?</div>
<div class="a">
Because this dataset is public and other people will use it. Anyone who removes
the leaking column (which they must) will silently end up with 122 duplicates
and get a score that is too good. It is a simple check: <b>look for duplicates
again AFTER deleting any column that came from the answer.</b>
</div>
</div>

<div class="qa">
<div class="q">Q. Your accuracy is 94% but also 77%. Which is true?</div>
<div class="a">
Both, for different questions. <b>94%</b> is for a material the model has
already studied. <b>77%</b> is for a completely new material. We report both
because quoting only 94% would be misleading.
</div>
</div>

<div class="qa">
<div class="q">Q. Why Random Forest and not the others?</div>
<div class="a">
It had the best balance of catching toxic particles without too many false
alarms (F1 = 0.865), and it was the most <b>stable</b> across repeated tests.
</div>
</div>

<div class="qa">
<div class="q">Q. Isn't 355 rows too small?</div>
<div class="a">
Yes, and we say so in the paper. That is exactly why we did the harder
material-wise test instead of trusting one lucky split &mdash; and why our main
suggestion for future work is simply <b>more materials.</b>
</div>
</div>

<h2>Remember This One Thing</h2>
<div class="big">
Earlier papers either <b>cleaned the data</b> or <b>compared the models</b>.
We did both together &mdash; and discovered that removing the column which leaks
the answer <b>secretly creates duplicate rows</b>. Fixing that
<b>changed which model won</b>. We also showed that on a brand-new material,
accuracy falls from <b>94% to 77%</b> &mdash; a drop the normal testing method
hides completely.
</div>

<p class="small">
That is a genuine, honest contribution for a project of this size. It is not a
Nature paper, and it does not pretend to be &mdash; but it is real work with a
finding that actually changed the result, which many student papers cannot say.
</p>

</body></html>"""


def main():
    OUT_HTML.write_text(HTML, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(HTML) / 1024:.0f} KB)")

    chrome = find_chrome()
    if chrome is None:
        print("Chrome/Edge not found.")
        sys.exit(1)

    profile = tempfile.mkdtemp(prefix="pdfprofile_")
    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
           f"--user-data-dir={profile}", "--no-pdf-header-footer",
           f"--print-to-pdf={OUT_PDF}", OUT_HTML.resolve().as_uri()]
    print("Printing to PDF ...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if not OUT_PDF.exists():
        print("FAILED")
        print(r.stderr[-1500:])
        sys.exit(1)
    print(f"Created {OUT_PDF} ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
    shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
