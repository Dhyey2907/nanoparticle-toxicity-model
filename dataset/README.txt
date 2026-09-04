DATASET FILES
=============

Source : NanoTox metal-oxide nanoparticle dataset
Repo   : https://github.com/NanoTox/ToxicityModel  (file dataset.txt)
Paper  : NanoTox: Development of a parsimonious in silico model for toxicity
         assessment of metal-oxide nanoparticles using physicochemical features
         bioRxiv 2021, doi:10.1101/2021.02.22.432301


1_raw_nanotox_dataset.csv
    The original dataset exactly as downloaded, just converted from
    tab-separated to comma-separated so it opens in Excel.
    483 rows, 24 columns.
    NOTE: this file still contains the 'viability' column. Do NOT use
    that column as a model input - the toxic/nonToxic label was made
    from it, so using it leaks the answer.

2_cleaned_dataset_used_for_training.csv
    This is the file the model was actually trained on.
    355 rows, after:
      - removing 6 exact duplicate rows
      - dropping the leaky 'viability' column
      - merging 122 repeated experiments into one row each
        (majority vote on the label, ties count as toxic)
    Target column is 'toxic'  (1 = toxic, 0 = non-toxic).
    68 toxic / 287 non-toxic.
    'n_replicates' says how many raw rows were merged into that row.
    'NPs' and 'Cellline' are kept for reference but are NOT model inputs.

3_material_properties_lookup.csv
    The 13 chemistry descriptors that are constant for each material.
    The prediction app uses this so the user only has to enter the 6
    properties they can actually measure.


COLUMN MEANINGS
---------------
coresize    core size of the particle (nm)
hydrosize   hydrodynamic size in solution (nm)
surfcharge  surface charge / zeta potential (mV)
surfarea    surface area (m2/g)
Expotime    exposure time (hours)
dosage      dose given to the cells (ug/mL)
Celltype    Cancer or Normal
Hsf         heat of formation
Ec          conduction band energy
Ev          valence band energy
MeO         metal-oxygen bond descriptor
enthalpy    enthalpy
ratio       metal to oxygen ratio
e           electronegativity
esum        sum of electronegativity
esumbyo     electronegativity per oxygen
MW          molecular weight
NMetal      number of metal atoms
NOxygen     number of oxygen atoms
ox          oxidation state
