# statseps

This repository contains the files necessary to recreate the dataset for the Statins in Sepsis paper. In order to use it, you will need to get access to MIMIC III from the site https://mimic.physionet.org/. After obtaining the dataset, you need to ensure you have the full discharge notes in CSV form. 

Change the file paths in `proc_mimic_drugs.py` to the path the notes and desired output folders are at, and then run the SQL file `notes_output.sql`. Import `notes_output_full.csv` into the table.

Then, follow instructions from the mimic code on Github (https://github.com/MIT-LCP/mimic-code) and run the code to generate the Angus sepsis view (`sepsis/angus.sql`) and the Elixhauser scores view (`comorbidity/postgres/elixhauser-ahrq-v37-with-drg.sql`). Afterwards, run `sepsis_vaso_flg.sql` to generate the auxillary view for vasopressors. To generate the SOFA scores, you will need to run `severityscores/make-severity-scores.sql`, which will generate SOFA scores along with a bunch of other scores. In order to compute the creatinine clearance, we also use the height and weight, which can be generated from `demographics/postgres/HeightWeightQuery.sql`.

Finally, run `get_tests.sql` and export the output to `tests_output.csv`. Run `get_basic_set.sql` and export the output to `basic_set.csv`. You can now run the Rmd file in R to generate the output. 