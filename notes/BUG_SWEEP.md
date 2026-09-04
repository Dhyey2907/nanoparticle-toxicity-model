# Bug sweep

Step 15 of the workflow. After the project was working we went back and
tried to break it. This is what we found and what we did about it.

---

## Bug 1 – The `viability` column was leaking the answer

**Severity: critical**

The dataset has a `viability` column (how many cells survived) and a `class`
column (Toxic / nonToxic). The `class` label was *created from* the viability
value by the people who published the dataset.

If we had kept `viability` as an input feature, every model would have got
almost 100% accuracy, but it would have been reading the answer instead of
predicting it. The whole project would have been meaningless.

**Fix:** `viability` is listed in `config.LEAKY_COLS` and dropped in
`preprocess.py`. `tests/test_pipeline.py::test_no_leaky_column_in_clean_data`
fails if it ever reappears.

---

## Bug 2 – Repeated experiments split across train and test

**Severity: high. Found by a test, not by us reading the code.**

We wrote `test_no_duplicate_rows` expecting it to pass, and it failed with
109 duplicates. We had removed duplicates *before* dropping `viability`, so
we only caught 6 rows.

What is actually going on: the raw file records the same experiment (same
particle, same dose, same cell line) several times, each with a slightly
different measured viability. Those rows are different while `viability` is
there, but become **identical** the moment we drop it.

That meant `train_test_split` was putting copies of the same experiment in
both the training set and the test set, so the test set was not really
unseen data and our scores were too optimistic.

Scale of the problem:

- 477 rows → only **355 unique experiments**
- 122 rows were repeats
- 11 of those groups **disagreed with each other on the label** (the same
  conditions came out toxic in one repeat and non-toxic in another)

**Fix:** `collapse_replicates()` in `preprocess.py` merges repeats into one
row per unique experiment. Where the repeats disagree we take the majority,
and an exact tie counts as toxic (for a safety tool, wrongly warning is
better than wrongly clearing).

**Effect on the results** – the best model actually changed:

| | Before the fix | After the fix |
|---|---|---|
| Best model | Decision Tree | Random Forest |
| Best F1 | 0.800 | 0.865 |
| ZnO recall (leave-one-material-out) | 0.257 | 0.717 |

The Decision Tree had been "winning" partly because it could memorise the
duplicated rows.

---

## Bug 3 – The web app had its own copy of the prediction code

**Severity: medium**

`app.py` built the input row and called `predict_proba` itself, instead of
using the function in `predict.py`. Two copies of the same logic means they
can drift apart and give different answers for the same particle, and we
would probably never notice.

We actually hit this while testing: the app said NON-TOXIC for a particle
where the command line said TOXIC. (That one turned out to be us not
selecting the material properly, but it made the risk obvious.)

**Fix:** `app.py` now imports `predict()` from `predict.py`. Both interfaces
run the exact same code. `test_app_and_cli_use_the_same_function` fails if
someone puts a `predict_proba` call back into `app.py`.

**Verified:** ZnO, core 40 nm, hydro 300 nm, charge -12 mV, area 50 m²/g,
24 h, 100 µg/mL, cancer cells → both the app and the CLI return
**TOXIC, 99.0%, Random Forest**.

---

## Bug 4 – Column order was never checked

**Severity: medium (would have been silent)**

The model expects its columns in the order they were in during training. We
build the input row from a dictionary, and dictionary order depends on how
the caller wrote it. If the order ever came out wrong, the model would read
core size as dosage and so on, and still happily return a prediction with no
error at all.

**Fix:** the trained bundle now stores `feature_order`, and `predict()`
reindexes to it every time. `test_column_order_does_not_change_the_answer`
shuffles the input dictionary and checks the answer is the same.

---

## Bug 5 – Accuracy was hiding a useless model

**Severity: medium**

Only 19% of the samples are toxic. A model that just says "non-toxic" to
everything scores 81% accuracy. KNN is close to this – it gets 87.6%
accuracy but only **0.412 recall**, so it misses almost 60% of the toxic
particles. If we had picked the best model by accuracy we could easily have
shipped something that does not do its job.

**Fix:**

- Best model is chosen by **F1**, not accuracy
- `class_weight="balanced"` on Logistic Regression, Decision Tree, SVM and
  Random Forest
- Precision, recall, F1, ROC-AUC and confusion matrices are all reported
- `test_model_beats_the_lazy_baseline` fails if the best model's F1 drops
  below 0.5 or its recall below 0.5

---

## Bug 6 – No validation on user input

**Severity: low**

The prediction functions accepted anything. An unknown material threw a
confusing `KeyError` from deep inside pandas, and a nonsense cell type was
silently one-hot encoded as all zeros and gave a prediction anyway.

**Fix:** `build_row()` now checks the material is known, the cell type is
`Cancer` or `Normal`, and all six properties were given, and raises a clear
`ValueError` otherwise. `predict.py` catches it and prints a readable
message. `test_unknown_material_is_rejected` covers this.

---

## Bug 7 – No warning when the user is far outside the training data

**Severity: low, but it matters for a safety tool**

Nothing stopped a user from asking about a dose of 900 µg/mL when the model
has only ever seen up to 300, and the answer looked just as confident as any
other.

**Fix:** `check_ranges()` compares every input against the min and max in the
training data and warns. Both the CLI and the app show it:

```
! dosage = 900.0 is outside the training range (1e-05 to 300)
```

---

## Not a bug, but the biggest limitation

Almost every toxic sample is CuO or ZnO, and 13 of the 19 numeric features
have the same value for every row of a material. So the model can partly
identify the *material* rather than learn the chemistry, and a normal random
split does not reveal this.

We added a **leave-one-material-out** check
(`results/leave_one_material_out.csv`): train on 4 materials, test on the
5th. Held-out ZnO accuracy is 0.771 against a 0.944 normal test accuracy.

This is not something we can fix with better code – it needs a dataset with
more than 5 materials. It is written up in the README so nobody reads 94%
and thinks the model works on any nanoparticle.

---

## Also checked, no problem found

- Missing values – there are none, but the median fill step is still there
  so the pipeline does not break on a different dataset
- The material lookup table – `test_material_columns_really_are_constant`
  confirms all 13 looked-up descriptors really are constant within a
  material, so the app is not filling in a wrong value
- Scaling – done inside a `Pipeline`, so the scaler is fitted on the
  training fold only and does not leak into the test fold
- Reproducibility – `random_state=42` everywhere;
  `test_preprocessing_is_repeatable` checks cleaning twice gives the same
  result
- Label and probability agreeing – checked on 25 random inputs across all
  5 materials
- Deleting `data/`, `models/` and `results/` and running `python run_all.py`
  from scratch reproduces everything, including re-downloading the dataset

---

## Final state

```
18 passed
```

All 7 bugs fixed. The two that actually changed our results were Bug 1 and
Bug 2, and Bug 2 changed which model won.
