# DSO 576 Module 6 - Project Data Cleaning

## Project

**Improving Amazon Product Listings - Appliances Category**

**Student:** Zhangli Tong  
**Branch:** `Zhangli-Tong`  
**Branch URL:** https://github.com/dtry19/dso576-project-/tree/Zhangli-Tong  
**Commit ID:** `[ADD AFTER FINAL COMMIT]`

## Project dataset

This Module 6 assignment uses `Appliances_sample.jsonl`, a 1,000-review working sample from the **Amazon Reviews 2023 - Appliances** dataset. The full Appliances dataset is substantially larger, so the team uses this 1,000-review sample as the complete project working dataset for the repository workflow. The sampling approach was discussed with and approved by the professor.

One row represents one Amazon customer review. The dataset does not contain a dedicated unique review ID. `parent_asin`, `asin`, and `user_id` may repeat legitimately, so repeated identifiers are evaluated separately from exact duplicate rows.

Expected source location:

```text
data/raw/Appliances_sample.jsonl
```

The source file is not overwritten by the cleaning workflow.

## Cleaning approach

The workflow uses rule-based validation rather than forcing changes. A record would be changed or removed only if it violated a predefined rule involving missingness, blank text, exact duplication, rating validity, helpful-vote validity, or timestamps.

For the 1,000-review working dataset, the checks found:

- 0 missing values
- 0 blank review texts
- 0 blank review titles
- 0 exact duplicate rows
- 0 invalid ratings outside 1-5
- 0 negative helpful-vote values
- 0 reviews after the reference date

Repeated identifiers were inspected and retained because multiple reviews can refer to the same product or reviewer. No destructive text normalization was applied because the original customer wording may be analytically meaningful.

As a result, all 1,000 reviews were retained in the cleaned dataset.

## Files for Module 6

- `module6_cleaning_sample.ipynb` - documented cleaning and validation notebook
- `module6_cleaning.py` - reproducible cleaning script
- `cleaned_sample.csv` - 50-row cleaned submission sample
- `requirements.txt` - Python dependency file
- `README.md` - run instructions and submission information

## Dependencies

The workflow requires Python and pandas.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## How to run

From the repository root, run:

```bash
python module6_cleaning.py
```

Or open `module6_cleaning_sample.ipynb`, restart the kernel, and run all cells from top to bottom.

## Expected outputs

Running the script recreates:

```text
cleaned_sample.csv
```

Expected QA results:

```text
Original shape: (1000, 10)
Cleaned shape: (1000, 10)
Missing values: 0
Blank text: 0
Blank titles: 0
Exact duplicates: 0
Invalid ratings: 0
Negative helpful votes: 0
Future reviews: 0
Submission sample: (50, 10)
```

## Submission sample selection

The 50-row submitted sample contains five notable or difficult cases followed by 45 additional cleaned records. The five cases represent:

1. a 1-star review;
2. a 5-star review;
3. an unverified purchase;
4. the review with the highest helpful-vote count; and
5. a review associated with a repeated `parent_asin`.

This preserves representative and edge-case evidence while staying within the Module 6 limit of up to 50 cleaned rows.

## Remaining limitations

The 1,000 reviews are a subset of the full Amazon Appliances review dataset and should not be interpreted as representing all Appliances reviews. Review text may contain subjective opinions, spelling differences, product-use issues, or delivery-related comments that are not directly related to listing quality. The project working sample contains review data only, so this Module 6 workflow cannot compare reviews directly with product metadata such as features, descriptions, or prices. Repeated `parent_asin` values are expected because multiple reviews may refer to the same parent product.
