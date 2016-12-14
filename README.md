# statseps

This repository contains the files necessary to recreate the dataset for the Statins in Sepsis paper. In order to use it, you will need to get access to MIMIC III from the site https://mimic.physionet.org/. After obtaining the dataset, you need to ensure you have the full discharge notes in CSV form. 

Change the file paths in `proc_mimic_drugs.py` to the desired paths, and then run the script. Use the resulting sql table to create the table.

Then, follow instructions from the mimic code on github and run the code to generate the Angus sepsis view and the Elixhauser scores view. Afterwards, run `sepsis_vaso_flg.sql` to generate the auxillary view for vasopressors. 

Finally, run `get_tests.sql` and export the output to `tests_output.csv`. Run `get_basic_set.sql` and export the output to `basic_set.csv`. You can now run the Rmd file in R to generate the output.