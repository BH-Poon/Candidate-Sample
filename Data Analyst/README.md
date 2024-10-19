# TAKE HOME EXERCISE #

## Requirement ##

Answer **three of the following questions** with at least one question coming from the closed-ended and one from the open-ended question set. Each question should be answered using **one query**.

### Closed-Ended Questions ###

    1. What are the top 5 brands by receipts scanned among users 21 and over?
    2. What are the top 5 brands by sales among users that have had their account for at least six months?
    3. What is the percentage of sales in the Health & Wellness category by generation?

### Open-Ended Questions ###

    1. Who are Fetch’s power users?
    2. Which is the leading brand in the Dips & Salsa category?
    3. At what percent has Fetch grown year over year?

## EXERCISE ANSWERS ##

### FILES AND SCRIPTS ###

The following are the files used for the exercise:

1. *exercise_util.py* - This module contains functions for connecting to a database, creating the sample database, disconnecting from the database, and writing query output to an Excel sheet. Sample database created for the exercise will be named *exercise_db.db*. Source CSV files will be stored in directly ~/source.
2. *exercise_util_qc.py* - This module contains the controller and functions for quality control and validation on columns. 
3. *exercise_database.db* - SQLite database file generated with all CSV files from `sqlalchemy`.
4. *exercise_results.xlsx* - This file contains the output of indvidual exercises written in sheets within the workbook. If a sheet exists, the sheet will be written over.
5. *q2_close_ended.py* - This file contains the Python script and SQL query for answering question.
6. *img_q2_close_ended.png* - Simple bar chart for visualizing results from above.
7. *q3_close_ended.py* - This file contains the Python script and SQL query for answering question.
8. *img_q3_close_ended.png* - Simple bar chart for visualizing results from above.
9. *exercise_3_email.md* - Sample email to product or business leader written with markdown to try to capture what it may be like on Outlook or Slack.

### EXPLORING THE DATA ###

**<ins>UNDERSTANDING FIELDS</ins>**
Listed below are some fields that were not as straightforward to ascertain the background on how the table values fit with the database relationship model.

For the table `TRANSACTION_TAKEHOME`:

   1. `final_quantity`- The final_quantity field was a float datatype. However, it is not logical to partial quantity on a transaction record. Initially, I thought it might be an average quantity, but that did not make sense either because the transaction is mapped to a specific scan time and transaction time. Therefore, it should have been a whole number.
   2. `receipt_id`, `scan_date` - These fields contain heavily duplicated values that are bilaterally matching and, in some cases, matching entirely between records. It is not likely that these are repeated scans by the user because the timestamp in `scan_date` matches exactly. This is likely a system-related duplication.

For the table `PRODUCTS_TAKEHOME`:

   1. `brand` - This field had many rows without values. However, the largest impact is that the information gap makes it hard to align with queries to make sense of it. This makes it hard to understand how the records were generated. It is likely through another source or through manual curation of raw data.
   2. `barcode` - It was odd that there were records that did not contain a barcode. In the same respect as `brand`, makes it hard to understand where the information was generated from.


**<ins>OBSERVATIONS RELATED TO QUALITY CONTROL</ins>**
There were some quality-related issues observed when performing an initial visual inspection of the CSV files. There were some inhernt problems that occurred when generating the exercise database, albiet this may have been uniquely because of how the database was created using Python. The following were issues found and addressed in *exercise_util.py*:

   1. There were string integers found in the values. For example, `TRANSACTION_TAKEHOME.final_quantity` had string "zero" instead of integer 0.
   2. Fields also contained whitespace strings that were not apparent during visual inspection but will affect the approach to generate the database in Python and, subsequently, running the query. The issue apparent when the database was created because the values were interpreted as strings when it was actually `NaN`, which will lead to miscounting and grouping errors.
   3. Inconsistencies were found with values in `USER_TAKEHOME.gender` with duplicates selections in categories for "Not Listed", "Prefer To Not Say", and "Non-Binary". There was also a value "unknown", which is ambiguous because it isn't clear whether this is a specific gender status or it is an unknown input value.
   4. The `USER_TAKEHOME.birth_date` field contains some questionable values, with the degree of "questionability" being subjective. For the purpose of this exercise, the two degrees were distinguished:
      1. *Highly Questionable*: There were 35 records contains birthyear from 1900 (min) to 1907. The oldest person in the world (verified by Guinness World Records) was born in 1908. This makes it an extremely low likelihood of being valid. On the other hand, there were 22 records with birth year from 2022 (max) to 2014, which meant the users were under 13 years old. This would technically be in violation of the Terms of Service for Fetch.
      2. *Moderately Questionable*: There were 2,192 records with birthyear from 2007 to 2013, which meant that users were 11-18 years old. This would be in violation of age of majority in nearly all US states and territories, except for AL, NE, MS, IN, NY, and PR where the age is higher than 18 years old. However, this is only moderately questionable because there is less doubt on whether the user age is legitimate.
   5. The `TRANSACTION_TAKEHOME.receipt_id` field is heavily duplicated when the ID is supposed to be a unique identifier. However, duplications seems to be in pairs with one or two other fields conflicting. An example with two rows that are matching exactly but differing in two fields can be can be found in `receipt_id=007d3232-3990-497f-a081-549e9e7a478b`. One row will not have a value in in `final_sale` and one row will have "zero" written in `final_quantity`.
   6. The `PRODUCTS_TAKEHOME.barcde` field has numerous missing barcodes, which is unfortunate because of the information lost when not being able to match the barcode to differing tables. However, the number of records missing a barcode was 4,025, which was not terrible compared to the 845,552 records. There were 185 duplicates in the records and were once-repeated duplicates. Some duplicates were complete duplicates, such as `barcode=952811` and `barcode=400510`. Some differed in one field, such as `barcode=404310` that had `brand="BRAND NOT KNOWN"`. Some were duplicated in different sub-categories depending on the brand. Using `barcode=701983` as an example, the `brand` was either "SUNRIDGE FARMS" or "TRADER JOE'S", and the values `category_2` and `category_3` were different from the brand.

In order to control the impact of the data-related issues, quality control measures were employed before generating the SQLite database from the CSV files. Each table was read into a dataframe and each column was systematically evaluated for the datatype and known issues to correct (e.g. "zero" to 0 for integer/float fields). Next the `qc_by_row()` function will identify each duplication and feed a set of duplicated rows to the `reconcile()` function, which will recursively attempt to reconcile the differences. Please note that not all differences can be reconciled at this time due to the limitations of time and tools. Best measures for this would be to use a ML-based method.

### Q2 Closed-Ended Question ###

**ASSUMPTION & REASON:** Users who have had their account for at least six months would be calculated based on the time from `USER_TAKEHOME.created_date` to the time in `TRANSACTIONS_TAKEHOME.scan_date`. The reasoning for this is that the user must be adding a qualified transaction for calculation. In which case, the sales numbers qualified for query must be qualified at the time of scan and not based on current time. Using the current time as the reference may show inconsistent results when query is repeated some time later.

**QUALIFIED TRANSACTIONS:** Continuing on the topic of a "qualified transaction", the query will also add filters for `TRANSACTION_TAKEHOME.final_quantity` and `PRODUCTS_TAKEHOME.brand` (when aggregating `TRANSACTION_TAKEHOME.final_sale`). The `final_quantity` must be greater than 0 because it will not make sense if there's a final sale value of $X and final quantity of 0 because the transactional value should essentially be $0. The `brand` must not be null because it would add direct value to the analysis.However, it will add indirect value in highlighting gaps and opportutnies in the data. From the SQL statement, the records with `NULL` in `brand` will show up if a `FULL JOIN` (or Outer Join) operation was used instead of (INNER) `JOIN` operation. Even though `sqlalchemy` cannot perform `FULL JOIN` at this time and `INNER JOIN` was used instead, the `WHERE` statement was written out for `brand` as an assurance and a good practice for variable filter control.

**NOTE #1:** The `JULIANDAY()` function is used to calculate difference between `TRANSACTION_TAKEHOME.scan_date` and `USER_TAKEHOME.created_date`, and will give the difference in the number of days, in which case 6 months can be estimated to 183 days. This function is only used because exercise_database.db was created in SQLite. Otherwise, the function `DATEDIFF()` would have been preferred if allowed in the server environment.

**NOTE #2:** The SQL query is written in variable `sql_query` as a raw SQL text to satisfy exercise requirement. Utilizing the Python package `sqlalchemy`, it is important to point out that the same query could have been built with its query builder or, with `sqlalchemy.orm` installed, its Object Relational Mapper (ORM), which can add versatility for future applications.

**RESULT:** The result showed the following as the top 5 brands based on total sales: CVS (72), DOVE (30.91), TRIDENT (23.36), COORS LIGHT (17.48), and TRESEMME (14.58). 

### Q3 Closed-Ended Question ###

**ASSUMPTION & REASON:** The assumptions made for this exercise includes what age range is considered in each generation. Instead, a definition is taken from an outside ![source](https://libguides.usc.edu/busdem/ag). After delinating the generations in the CTE, `WHERE` was employed to filter through users whose birth date is greater than 1907 (the longest living person was born in 1908) and whose age at the time of scanning is greater than 17 (age of majority requirement). This will give a list of valid transactions to find the users per generation, total sales, and percent total sale for the category "Health & Wellness"

**RESULT:** The result showed the following as the generation and percentage of sales in the "Health & Wellness" category: Baby Boomers (1946-1964) with 53.5366%, Generation X (1965-1979) with 24.0721%, and Millennials (1980-1994) with 22.3913%.

### Q2 Open-Ended Question ###

**ASSUMPTION & REASON:** The first assumption was the "Dips" and "Salsa" are dimensionally separate categories and that the "leading brand" does not truly reflect the leading brand in both dips and salsas. Hence, the first assumption was to separate rows based on the subcategory, which was grouped to either "Dips" or "Salsas". The query aggregated the number of receipts, total sales, and total quantity in their respective fields. Additionally, an average was calculated between sales/receipt and sales/quantity to help identify further what the "leading" brand may be.

**RESULT:** The result primarily depends on total sales based on each type, either "Dips" or "Salas". For "Dips", the winner was TOSTITOS with 177.32 total sales and 37 total quantity. Comparatively, the next runner up is FRITOS with 63.18 total sales and 19 total quantity. Now, the sales per receipt would not have shown this as clearly because of the bias in the number of receipts. However, it does help for the "Salsa" category in providing supporting reasons for identifying the leading brand. In the "Salsa" category, the top two brands are GOOD FOODS (94.91 | 9) and PACE (79.73 | 22) when compared to (total sales | total quantity). It might be tempting to say that PACE is the leading brand, but notice that that GOOD FOODS has an average sales/quantity of 10.5456 as compared to PACE's 3.62409. Although I would normally believe that people buying means better, it would be hard to justify why some would pay almost 3 times the price for another brand. In which case, I would say GOOD FOODS is perhaps the leading brand for "Salsa".