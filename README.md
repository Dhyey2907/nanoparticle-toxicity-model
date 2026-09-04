# Nanoparticle Toxicity Prediction Using Data-Driven Methods

Mini project – predicting whether a nanoparticle is **toxic** or **non-toxic**
from its physicochemical properties using machine learning.

**Team members**

| Name | Roll No |
|---|---|
| Pratham Joshi | KU2507U0361 |
| Divyansh Khatri | KU2507U0188 |
| Dhyey Bhatt | KU2507U0138 |
| Jinay Shah | KU2507U0070 |

---

## 1. Problem

Nanoparticles are used a lot in drug delivery because they are small, have a
large surface area and can be targeted to specific cells. Unfortunately the
same properties can also make them toxic. Testing every new particle in the
lab is slow and expensive, so it helps to have a model that can flag risky
particles early.

This project builds that model. Given the properties of a nanoparticle
(core size, hydrodynamic size, surface charge, surface area, dosage and
exposure time) it predicts **TOXIC** or **NON-TOXIC**.

---

## 2. Dataset

We used the **NanoTox metal-oxide nanoparticle dataset**.

- Source: <https://github.com/NanoTox/ToxicityModel> (file `dataset.txt`)
- Paper: *NanoTox: Development of a parsimonious in silico model for toxicity
  assessment of metal-oxide nanoparticles using physicochemical features*,
  bioRxiv 2021 – <https://doi.org/10.1101/2021.02.22.432301>
- 483 experiments, 5 materials (Al2O3, CuO, Fe2O3, TiO2, ZnO), 11 cell lines
- After cleaning: **355 unique experiments**, 19% of them toxic (68 toxic / 287 non-toxic)

`src/download_data.py` downloads it automatically, so nothing has to be
downloaded by hand.

### Columns we use

| Group | Columns |
|---|---|
| Entered by the user | `coresize`, `hydrosize`, `surfcharge`, `surfarea`, `Expotime`, `dosage` |
| Looked up from the material | `Hsf`, `Ec`, `Ev`, `MeO`, `enthalpy`, `ratio`, `e`, `esum`, `esumbyo`, `MW`, `NMetal`, `NOxygen`, `ox` |
| Categorical | `Celltype` (Cancer / Normal) |
| Target | `class` → `toxic` (1 / 0) |
| **Never used** | `viability` – see the note below |

---

## 3. How to run it

```bash
pip install -r requirements.txt
python run_all.py            # download -> clean -> EDA -> train
streamlit run app.py         # the web app
```

Or run the steps one at a time:

```bash
python src/download_data.py
python src/preprocess.py
python src/eda.py
python src/train_models.py
```

Command line predictions:

```bash
python src/predict.py --demo
python src/predict.py          # asks you question by question
python src/predict.py --material ZnO --coresize 40 --hydrosize 300 --surfcharge -12 --surfarea 50 --expotime 24 --dosage 100
```

Tests:

```bash
pytest -v
```

---

## 4. Folder structure

```
nanoparticle-toxicity/
├── app.py                  Streamlit web app (final prediction system)
├── run_all.py              runs the whole pipeline in order
├── requirements.txt
├── data/
│   ├── raw/                the downloaded dataset
│   └── processed/          cleaned data + material lookup table
├── src/
│   ├── config.py           all paths and column names
│   ├── download_data.py    step 3
│   ├── preprocess.py       steps 4 and 5
│   ├── eda.py              steps 6 and 7
│   ├── train_models.py     steps 8 to 12
│   └── predict.py          step 14
├── models/best_model.joblib
├── results/                metrics CSVs + all the figures
├── tests/test_pipeline.py
└── notes/BUG_SWEEP.md      what we found while testing
```

---

## 5. Results

Test set = 25% of the data, stratified. Best model chosen by **F1 score**,
not accuracy, because only 19% of the samples are toxic.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Random Forest** | **0.944** | **0.800** | **0.941** | **0.865** | **0.946** |
| Decision Tree | 0.921 | 0.778 | 0.824 | 0.800 | 0.904 |
| Logistic Regression | 0.888 | 0.667 | 0.824 | 0.737 | 0.931 |
| SVM | 0.865 | 0.609 | 0.824 | 0.700 | 0.928 |
| KNN | 0.876 | 0.875 | 0.412 | 0.560 | 0.836 |

**Random Forest** is the final model.

KNN has good precision but terrible recall – it misses almost 60% of the
toxic particles. For a safety tool that is the worst kind of mistake, which
is exactly why we did not pick the model by accuracy.

All the plots are in `results/figures/`.

### What matters most

From the correlation analysis and the Random Forest feature importances, the
strongest signals are the material-level chemistry descriptors (`ratio`,
`enthalpy`, `ox`, `Hsf`, `NOxygen`) followed by `surfarea`, `Expotime` and
`coresize`. In plain terms: **what the particle is made of matters more than
how big it is**, and CuO and ZnO are the dangerous ones in this dataset.

| Material | % of samples toxic |
|---|---|
| CuO | 38.9% |
| ZnO | 33.5% |
| TiO2 | 0.8% |
| Al2O3 | 0% |
| Fe2O3 | 0% |

---

## 6. Two things we had to be careful about

These are the two mistakes that would have made our results look much better
than they really are. Both are explained properly in `notes/BUG_SWEEP.md`.

**1. The `viability` column leaks the answer.**
The toxic / non-toxic label was created from the cell viability value. If we
left `viability` in as a feature the models would get near 100% accuracy,
but they would just be reading the answer, not predicting anything. We drop
it in `preprocess.py` and there is a test that fails if it ever comes back.

**2. The dataset has repeated experiments.**
The same experiment (same particle, same dose, same cell line) is recorded
several times with a slightly different viability each time. Once `viability`
is removed those rows become identical, so a random train/test split was
putting copies of the same experiment in both sets. We found 122 such rows.
We now merge them into one row per unique experiment (majority vote on the
label, ties count as toxic).

---

## 7. Limitation we want to be honest about

Almost every toxic sample in this dataset is CuO or ZnO, and many of the
descriptors are the same for every row of a material. So a normal random
split lets the model partly recognise the *material* instead of learning the
underlying chemistry.

To check how bad this is we also ran **leave-one-material-out**: train on 4
materials and test on the 5th one, which the model has never seen.

| Held out material | Samples | Accuracy | Recall on toxic |
|---|---|---|---|
| Al2O3 | 18 | 1.000 | – (no toxic samples) |
| CuO | 18 | 0.889 | 0.714 |
| Fe2O3 | 18 | 1.000 | – |
| TiO2 | 122 | 0.992 | 0.000 (only 1 toxic sample) |
| ZnO | 179 | 0.771 | 0.717 |

So the model does clearly worse on a material it has never seen than the
0.944 test accuracy suggests. **It should be used for materials similar to the
five it was trained on, not for a brand new nanoparticle.**

---

## 8. Conclusion and future work

We built a working end-to-end system: it downloads the data, cleans it,
explores it, trains and compares five classifiers, picks the best one and
serves predictions through both a command line tool and a web app.

Random Forest gives 94.4% accuracy and 0.865 F1 on the held out test set,
and catches 94% of the toxic particles.

What we would do next:

- Get a bigger dataset with more materials (this one only has 5), so the
  leave-one-material-out scores improve
- Add polymeric and silica nanoparticles, not just metal oxides
- Try SMOTE or other resampling for the class imbalance instead of only
  `class_weight="balanced"`
- Use SHAP values so we can explain each individual prediction, not just
  the overall feature importances
- Tune the hyperparameters properly with GridSearchCV

---

## 9. Note

This is a student project and a screening tool. It is not validated for real
safety decisions and does not replace an actual toxicity assay.
