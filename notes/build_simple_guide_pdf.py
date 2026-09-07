"""
Builds the plain-English "how we did this project" guide as a PDF.

This is the easy-words version. The detailed technical one is
Nanoparticle_Toxicity_Project_Procedure.pdf.

Run:  python notes/build_simple_guide_pdf.py
"""

import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))
import config  # noqa: E402

OUT_PDF = PROJECT / "Nanoparticle_Toxicity_Simple_Guide.pdf"
OUT_HTML = PROJECT / "notes" / "simple_guide.html"

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


def fig(name):
    path = config.FIGURES_DIR / name
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


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
h3 { font-size: 12pt; color:#1d5c8f; margin: 16px 0 5px 0; page-break-after: avoid; }
p { margin: 8px 0; }
b, strong { color:#0d3b66; }

.cover { text-align:center; padding-top: 48mm; page-break-after: always; }
.cover h1 { font-size: 27pt; line-height:1.25; border:none; }
.cover .sub { font-size: 14pt; color:#555; margin-top: 12px; }
.cover .rule { width: 65mm; height:3px; background:#0d3b66; margin: 24px auto; }
.cover .tag {
  display:inline-block; background:#e8f0f7; color:#0d3b66;
  padding: 8px 20px; border-radius: 18px; font-size: 11pt; margin-top: 18px;
}
.cover table { width:74%; margin: 30px auto; border-collapse:collapse; font-size:11pt; }
.cover th { background:#0d3b66; color:#fff; padding:7px 12px; text-align:left; }
.cover td { padding:6px 12px; border-bottom:1px solid #dde3ea; }

.step {
  border:1.5px solid #d6dfe8; border-radius:9px;
  padding: 12px 16px 14px 16px; margin: 13px 0;
}
.step .hd {
  display:flex; align-items:center; margin-bottom:6px;
  break-after: avoid; page-break-after: avoid;
}
.stepnum {
  background:#0d3b66; color:#fff; min-width:32px; height:32px; line-height:32px;
  border-radius:50%; text-align:center; font-weight:700; font-size:13pt;
  margin-right:12px; flex-shrink:0;
}
.steptitle { font-size:12.5pt; font-weight:700; color:#0d3b66; }
.step p { margin: 6px 0; }

.why {
  background:#eef5fb; border-left:4px solid #2e75b6;
  padding: 9px 14px; margin: 9px 0; font-size:10.5pt;
}
.why .lbl { font-weight:700; color:#1d5c8f; }
.oops {
  background:#fdeceb; border-left:4px solid #c0392b;
  padding: 9px 14px; margin: 9px 0; font-size:10.5pt;
}
.oops .lbl { font-weight:700; color:#a93226; }
.win {
  background:#eaf6ec; border-left:4px solid #2e7d32;
  padding: 9px 14px; margin: 9px 0; font-size:10.5pt;
}
.win .lbl { font-weight:700; color:#1e6023; }

table.t { border-collapse:collapse; width:100%; margin:10px 0; font-size:10pt;
          page-break-inside:avoid; }
table.t th { background:#0d3b66; color:#fff; padding:6px 9px; text-align:left; }
table.t td { padding:5px 9px; border-bottom:1px solid #dde3ea; }
table.t tr:nth-child(even) td { background:#f7f9fb; }
td.n, th.n { text-align:right; }
tr.hi td { font-weight:700; background:#eaf6ec !important; }

img.fg { width:100%; display:block; margin: 8px auto; }
.cap { text-align:center; font-size:9pt; color:#666; font-style:italic; margin-bottom:10px; }

ul { margin:8px 0; padding-left:22px; }
li { margin:5px 0; }
.pagebreak { page-break-before: always; }
.small { font-size:9.5pt; color:#555; }
.flow { text-align:center; margin: 14px 0; page-break-inside:avoid; }
"""


FLOW_SVG = """
<svg viewBox="0 0 760 108" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px">
  <defs>
    <marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3"
            orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#0d3b66"/></marker>
    <style>
      .bx { fill:#e8f0f7; stroke:#0d3b66; stroke-width:1.6; rx:7; }
      .tx { font: 600 11px "Segoe UI", Arial; fill:#0d3b66; text-anchor:middle; }
      .sb { font: 9px "Segoe UI", Arial; fill:#55707f; text-anchor:middle; }
      .ln { stroke:#0d3b66; stroke-width:1.8; marker-end:url(#ar); }
    </style>
  </defs>
  <rect class="bx" x="4"   y="26" width="118" height="52"/>
  <text class="tx" x="63"  y="48">Raw data</text>
  <text class="sb" x="63"  y="64">483 rows</text>
  <line class="ln" x1="126" y1="52" x2="152" y2="52"/>
  <rect class="bx" x="156" y="26" width="118" height="52"/>
  <text class="tx" x="215" y="48">Clean it</text>
  <text class="sb" x="215" y="64">355 rows</text>
  <line class="ln" x1="278" y1="52" x2="304" y2="52"/>
  <rect class="bx" x="308" y="26" width="118" height="52"/>
  <text class="tx" x="367" y="48">Look at it</text>
  <text class="sb" x="367" y="64">graphs</text>
  <line class="ln" x1="430" y1="52" x2="456" y2="52"/>
  <rect class="bx" x="460" y="26" width="118" height="52"/>
  <text class="tx" x="519" y="48">Train models</text>
  <text class="sb" x="519" y="64">5 of them</text>
  <line class="ln" x1="582" y1="52" x2="608" y2="52"/>
  <rect class="bx" x="612" y="26" width="140" height="52" style="fill:#eaf6ec;stroke:#2e7d32"/>
  <text class="tx" x="682" y="48" style="fill:#1e6023">Predict!</text>
  <text class="sb" x="682" y="64" style="fill:#2e7d32">toxic / safe</text>
</svg>
"""


HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Simple Guide</title>
<style>{CSS}</style></head><body>

<div class="cover">
  <h1>How We Built This Project</h1>
  <div class="rule"></div>
  <div class="sub">Nanoparticle Toxicity Prediction<br>explained in simple words</div>
  <div class="tag">A short, plain-English walkthrough</div>
  <table>
    <tr><th>Team Member</th><th>Enrolment No.</th></tr>
    <tr><td>Pratham Joshi</td><td>KU2507U0361</td></tr>
    <tr><td>Divyansh Khatri</td><td>KU2507U0188</td></tr>
    <tr><td>Dhyey Bhatt</td><td>KU2507U0138</td></tr>
    <tr><td>Jinay Shah</td><td>KU2507U0070</td></tr>
  </table>
</div>

<h2>Start Here: What Is This Project?</h2>
<p>
In one sentence: <b>we built a computer program that looks at a tiny particle
and guesses whether it is poisonous to human cells.</b>
</p>

<h3>What is a nanoparticle?</h3>
<p>
It is an extremely small piece of material. To get a sense of the scale: if a
nanoparticle were the size of a football, then a football would be the size of
the Earth. They are measured in <b>nanometres</b> &mdash; a nanometre is one
millionth of a millimetre.
</p>

<h3>Why do doctors care about them?</h3>
<p>
Because they are so small, they can be used to <b>carry medicine directly to a
sick cell</b> &mdash; for example, delivering a cancer drug straight to a tumour
instead of flooding the whole body with it. Fewer side effects, better results.
</p>

<h3>So what is the problem?</h3>
<p>
The same smallness that makes them useful also makes them dangerous. They can
slip into healthy cells too, and some of them poison those cells. So before
using any new particle in medicine, scientists must check: <b>is this one safe
or is it toxic?</b>
</p>

<h3>Why not just test them in a lab?</h3>
<p>
They do &mdash; but lab testing is slow and expensive. There are thousands of
possible particle designs (different materials, sizes, coatings, doses). Testing
every single one is impossible.
</p>
<div class="win">
<span class="lbl">Our idea:</span> use a computer to <b>quickly guess</b> which
particles are likely toxic, so scientists only spend lab time and money on the
ones worth testing. Think of it as a filter, not a replacement for the lab.
</div>

<h2>The Big Picture</h2>
<p>The whole project is really just five stages:</p>
<div class="flow">{FLOW_SVG}</div>
<p>
Everything below is just these five boxes explained in more detail.
</p>

<h3>What is "machine learning", in simple words?</h3>
<p>
Normally you program a computer with rules: "if X, then do Y." Machine learning
is different. You do not give it rules &mdash; you give it <b>lots of
examples</b>, and it figures out the rules by itself.
</p>
<div class="why">
<span class="lbl">Everyday example:</span> nobody wrote a rule that says "an
email containing the word FREE five times is spam." Your email app learned that
by looking at millions of emails that people marked as spam. Our project works
exactly the same way &mdash; we showed the computer hundreds of nanoparticle
experiments and let it work out the pattern.
</div>

<h2>Step By Step: How We Actually Did It</h2>

<div class="step">
  <div class="hd"><div class="stepnum">1</div><div class="steptitle">We found the data</div></div>
  <p>
  A machine learning model is useless without examples to learn from. We found a
  <b>free, published dataset</b> from a real scientific study. It contains
  <b>483 laboratory experiments</b> on nanoparticles.
  </p>
  <p>Each experiment recorded things like:</p>
  <ul>
    <li>What material the particle was made of (5 different materials)</li>
    <li>How big it was</li>
    <li>Its surface charge and surface area</li>
    <li>How much of it was given to the cells (the <b>dose</b>)</li>
    <li>How long the cells were exposed to it (the <b>exposure time</b>)</li>
    <li>And finally: <b>did the cells die or not?</b></li>
  </ul>
  <p class="small">
  That last one is the answer we want the computer to learn to predict.
  </p>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">2</div><div class="steptitle">We looked at the data before touching it</div></div>
  <p>
  Before changing anything, we just printed out what was in the file. How many
  rows? Any blanks? Any repeated rows? How many toxic vs safe?
  </p>
  <p>
  This is where we found something important: <b>only about 1 in 5 experiments
  was toxic.</b> The rest were safe. That sounds like a small detail, but it
  causes a big trap later (see Step 6).
  </p>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">3</div><div class="steptitle">We cleaned the data &mdash; and found two traps</div></div>
  <p>
  Real data is always messy. Cleaning it is boring but it is the most important
  step in the whole project. We found two serious problems.
  </p>

  <div class="oops">
  <span class="lbl">Trap 1 &mdash; the answer was hidden in the question.</span><br>
  The file had a column called <i>viability</i>, which means "what percentage of
  cells survived." But the toxic/safe label was <b>calculated from that very
  column</b> by the original scientists.
  <br><br>
  So if we let the computer see it, the computer is not predicting anything
  &mdash; it is just reading the answer.
  <br><br>
  <b>Like this:</b> imagine giving a student an exam, but accidentally printing
  the answer key on the back of the paper. They score 100%, and you have learned
  nothing about whether they can actually do the work.
  <br><br>
  <b>What we did:</b> deleted that column completely.
  </div>

  <div class="oops">
  <span class="lbl">Trap 2 &mdash; the same experiment appeared many times.</span><br>
  Scientists repeat experiments to be careful. So the same test (same particle,
  same dose, same cells) appears several times in the file, each with a slightly
  different survival number.
  <br><br>
  Once we deleted the <i>viability</i> column, those repeated rows became
  <b>exactly identical</b>. We found <b>122 such repeated rows</b>.
  <br><br>
  <b>Why this is bad:</b> later we split the data into "practice questions" and
  "exam questions." If the same experiment appears in both, the computer has
  already seen the exam answers during practice. Its score looks great but it is
  cheating without knowing it.
  <br><br>
  <b>What we did:</b> merged the repeats so each unique experiment appears only
  once. When repeats disagreed with each other, we took the majority answer.
  </div>

  <div class="win">
  <span class="lbl">Result of cleaning:</span> 483 rows became
  <b>355 genuine, unique experiments</b>. Smaller, but honest.
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">4</div><div class="steptitle">We drew graphs to understand it</div></div>
  <p>
  Before building anything, we plotted the data to see patterns with our own
  eyes. This is called <b>EDA</b> (Exploratory Data Analysis) &mdash; a fancy
  name for "look at your data properly."
  </p>
  <img class="fg" src="{fig('03_toxic_vs_nontoxic.png')}">
  <div class="cap">Green = safe particles, red = toxic ones, compared property by property.</div>
  <p>What we could see straight away:</p>
  <ul>
    <li><b>Higher dose &rarr; more toxic.</b> Not surprising, but good &mdash; it
        means the data behaves sensibly.</li>
    <li><b>Longer exposure &rarr; more toxic.</b> Same idea.</li>
    <li>Two materials in particular (<b>CuO</b> and <b>ZnO</b>) caused almost all
        the toxicity. The other three were basically harmless.</li>
  </ul>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">5</div><div class="steptitle">We split the data into practice and exam</div></div>
  <p>
  We divided the 355 experiments into two piles:
  </p>
  <ul>
    <li><b>266 experiments for learning</b> (75%) &mdash; the practice questions</li>
    <li><b>89 experiments kept hidden</b> (25%) &mdash; the exam</li>
  </ul>
  <div class="why">
  <span class="lbl">Why hide some?</span> If we tested the computer on the same
  examples it learned from, of course it would do well &mdash; it memorised them.
  The only fair test is on experiments it has <b>never seen before</b>. That is
  exactly how a real exam works.
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">6</div><div class="steptitle">We trained five different models</div></div>
  <p>
  There is no single "best" machine learning method, so we tried five common
  ones and let the results decide:
  </p>
  <ul>
    <li><b>Logistic Regression</b> &mdash; draws a straight dividing line between
        toxic and safe</li>
    <li><b>Decision Tree</b> &mdash; a flowchart of yes/no questions</li>
    <li><b>K-Nearest Neighbours</b> &mdash; "which past experiments look most like
        this one?"</li>
    <li><b>Support Vector Machine</b> &mdash; draws a curved dividing boundary</li>
    <li><b>Random Forest</b> &mdash; hundreds of decision trees that vote together</li>
  </ul>

  <div class="oops">
  <span class="lbl">The trap we avoided here.</span> Remember that only 1 in 5
  experiments is toxic? That means a completely useless model that just says
  <b>"safe"</b> to absolutely everything would still be right <b>81% of the
  time</b>.
  <br><br>
  <b>Like this:</b> a doctor who tells every single patient "you're fine, go
  home" will be correct most of the time, because most people are healthy. That
  does not make them a good doctor. The whole point is catching the sick ones.
  <br><br>
  <b>What we did:</b> we told the models to pay extra attention to the rare toxic
  cases, and we stopped judging them by accuracy alone.
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">7</div><div class="steptitle">We tested them properly</div></div>
  <p>
  We gave all five models the 89 hidden experiments and measured them in
  several ways, not just one:
  </p>
  <table class="t">
    <tr><th>Measure</th><th>What it means in plain words</th></tr>
    <tr><td><b>Accuracy</b></td><td>Out of everything, how often was it right?</td></tr>
    <tr><td><b>Recall</b></td><td>Out of the truly toxic particles, how many did it catch? <i>(most important for us)</i></td></tr>
    <tr><td><b>Precision</b></td><td>When it shouted "toxic!", how often was it actually right?</td></tr>
    <tr><td><b>F1 score</b></td><td>A fair combination of recall and precision</td></tr>
  </table>
  <div class="why">
  <span class="lbl">Why recall matters most here:</span> there are two ways to be
  wrong. Calling a safe particle toxic just wastes one lab test. Calling a
  <b>toxic particle safe</b> could let something harmful move forward. The second
  mistake is far worse, so we care most about catching every toxic one.
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">8</div><div class="steptitle">We picked the winner</div></div>
  <table class="t">
    <tr><th>Model</th><th class="n">Accuracy</th><th class="n">Recall</th><th class="n">F1</th></tr>
    <tr class="hi"><td>Random Forest</td><td class="n">94.4%</td><td class="n">94.1%</td><td class="n">0.865</td></tr>
    <tr><td>Decision Tree</td><td class="n">92.1%</td><td class="n">82.4%</td><td class="n">0.800</td></tr>
    <tr><td>Logistic Regression</td><td class="n">88.8%</td><td class="n">82.4%</td><td class="n">0.737</td></tr>
    <tr><td>Support Vector Machine</td><td class="n">86.5%</td><td class="n">82.4%</td><td class="n">0.700</td></tr>
    <tr><td>K-Nearest Neighbours</td><td class="n">87.6%</td><td class="n">41.2%</td><td class="n">0.560</td></tr>
  </table>
  <p>
  <b>Random Forest won.</b> It gets 94.4% right overall, and more importantly it
  catches <b>94% of the toxic particles</b>.
  </p>
  <div class="oops">
  <span class="lbl">Look at the last row.</span> K-Nearest Neighbours has 87.6%
  accuracy &mdash; that looks respectable! But its recall is only 41.2%, meaning
  it <b>misses nearly 6 out of every 10 toxic particles</b>.
  <br><br>
  This is exactly the "lazy doctor" problem. If we had picked our model by
  accuracy alone, we might have chosen this one and never realised it barely
  works.
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">9</div><div class="steptitle">We asked: which properties actually matter?</div></div>
  <p>
  A good model should also teach us something. So we asked the Random Forest
  which pieces of information it relied on most.
  </p>
  <img class="fg" src="{fig('10_feature_importance.png')}">
  <div class="cap">The longer the bar, the more the model depends on that property.</div>
  <p>The answer was clear:</p>
  <ul>
    <li><b>Dose matters most by far</b> &mdash; how much you give is the single
        biggest factor.</li>
    <li><b>Exposure time</b> comes second.</li>
    <li>Then the <b>chemistry of the material</b> itself.</li>
    <li>Particle size mattered surprisingly little.</li>
  </ul>
  <div class="win">
  <span class="lbl">In plain terms:</span> <b>what the particle is made of sets
  the danger level, and how much you use decides whether that danger actually
  shows up.</b>
  </div>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">10</div><div class="steptitle">We built something people can actually use</div></div>
  <p>
  A model sitting in a file is not useful. So we built two ways to use it:
  </p>
  <ul>
    <li>A <b>web app</b> &mdash; you pick the material, type in six numbers, press
        a button, and it tells you TOXIC or NON-TOXIC with a confidence
        percentage.</li>
    <li>A <b>command line tool</b> &mdash; the same thing for people comfortable
        with a terminal.</li>
  </ul>
  <p>
  The user only has to enter <b>six numbers</b>. The other thirteen chemistry
  values are filled in automatically once you pick the material, because those
  never change for a given substance.
  </p>
</div>

<div class="step">
  <div class="hd"><div class="stepnum">11</div><div class="steptitle">We tried to break our own project</div></div>
  <p>
  Finally, instead of assuming it worked, we deliberately went hunting for
  mistakes. We wrote <b>18 automatic tests</b> and found <b>7 problems</b>.
  </p>
  <p>
  The most interesting one: a test we <i>expected to pass</i> failed, and that is
  how we discovered the repeated-experiments problem from Step 3. Fixing it
  actually <b>changed which model won</b> &mdash; the Decision Tree had been
  coming first only because it was quietly memorising the duplicate rows.
  </p>
  <div class="win">
  <span class="lbl">Lesson:</span> testing your own work is not extra credit. It
  changed our actual result.
  </div>
</div>

<h2>What We Found</h2>
<table class="t">
  <tr><th>Question</th><th>Answer</th></tr>
  <tr><td>How much data did we end up with?</td><td>355 clean experiments (from 483 raw)</td></tr>
  <tr><td>How many were toxic?</td><td>68 out of 355, about 1 in 5</td></tr>
  <tr><td>Which model is best?</td><td>Random Forest</td></tr>
  <tr><td>How accurate is it?</td><td>94.4%</td></tr>
  <tr><td>How many toxic particles does it catch?</td><td>94 out of every 100</td></tr>
  <tr><td>What matters most for toxicity?</td><td>The dose, then exposure time, then the material</td></tr>
  <tr><td>Which materials were dangerous?</td><td>CuO and ZnO. Al<sub>2</sub>O<sub>3</sub>, Fe<sub>2</sub>O<sub>3</sub> and TiO<sub>2</sub> were nearly harmless</td></tr>
</table>

<h2>What Our Project Cannot Do</h2>
<p>
Being honest about limits is part of doing this properly.
</p>
<div class="oops">
<span class="lbl">It only knows five materials.</span> Our data covered just five
substances. We tested what happens with a completely new material by hiding one
material entirely and asking the model to judge it blind. Its accuracy dropped
from <b>94% to 77%</b>.
<br><br>
So the model is reliable for materials similar to the ones it studied, but you
<b>should not trust it on a brand-new substance it has never seen</b>. Fixing
this needs a bigger dataset, not better code.
</div>
<ul>
  <li>355 experiments is a <b>small</b> dataset by machine learning standards.</li>
  <li>The tests were done on cells in a dish, which is not the same as a whole
      human body.</li>
  <li>It is a <b>screening tool</b> &mdash; a helpful filter to decide what to
      test in the lab, not a replacement for the lab.</li>
</ul>

<h2>The Whole Project In One Paragraph</h2>
<p>
We took 483 real laboratory experiments on nanoparticles and cleaned them down
to 355 trustworthy ones, throwing away a column that was secretly giving away
the answer and merging repeated experiments that would have let the computer
cheat. We looked at the data with graphs, split it into practice and exam
portions, and trained five different machine learning models on it. The Random
Forest performed best, correctly identifying 94% of toxic particles on
experiments it had never seen. It told us that dose and exposure time matter
most, followed by the chemistry of the material. We wrapped it in an app anyone
can use, then wrote 18 tests to hunt for our own mistakes &mdash; and found
seven, one of which changed our final answer.
</p>

<h2>Quick Word List</h2>
<table class="t">
  <tr><th>Term</th><th>Simple meaning</th></tr>
  <tr><td><b>Nanoparticle</b></td><td>An incredibly tiny piece of material</td></tr>
  <tr><td><b>Toxic</b></td><td>Harmful &mdash; it kills cells</td></tr>
  <tr><td><b>Dataset</b></td><td>The table of past experiments we learn from</td></tr>
  <tr><td><b>Feature</b></td><td>One piece of information about a particle (its size, its dose...)</td></tr>
  <tr><td><b>Label</b></td><td>The answer we are trying to predict (toxic or safe)</td></tr>
  <tr><td><b>Training</b></td><td>Letting the computer study the examples</td></tr>
  <tr><td><b>Model</b></td><td>The thing that comes out of training and makes predictions</td></tr>
  <tr><td><b>Data leakage</b></td><td>Accidentally showing the answer during training &mdash; cheating by mistake</td></tr>
  <tr><td><b>Accuracy</b></td><td>How often it is right overall</td></tr>
  <tr><td><b>Recall</b></td><td>How many of the truly toxic ones it managed to catch</td></tr>
  <tr><td><b>EDA</b></td><td>Drawing graphs to understand your data before modelling</td></tr>
</table>

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
