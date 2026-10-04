# Data Cleaning

This submission cleans every row of the team's 1,000-review Appliances sample. It does not validate the entire upstream category.

## Source and scope

- Team source: `dataset/Appliances_sample.jsonl`
- Repository source version: `2a623b24ff6e1a427426707117e4e45ed4d948c2`.
- Upstream: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 (McAuley Lab, Amazon Reviews 2023).
- SHA-256: `6e5ce91e627c1eb52471166a207b8b76b36e062835a544bcd793af4d743f1608`.
- Original sampling procedure and upstream download date are unknown; the Git version identifies the exact input used here.

## Branch and submission identity

- Personal branch: `Jenny-Guo`.
- Branch URL: https://github.com/dtry19/dso576-project-/tree/Jenny-Guo
- The submitted code/results commit is recorded below when the tested implementation is committed. 

## Run

From the repository root with Python 3.11 or later:

```sh
python3 jenny_guo/clean.py
```

Cleaning has no third-party dependencies. Verified using Python 3.12.14. For an independent output directory:

```sh
python3 jenny_guo/clean.py --output /tmp/jenny-independent-run
```

Alternatively open `dataset/proj_data_clean_jenny_guo.ipynb`, select Python 3, restart the kernel and run all cells. The saved cell outputs were produced by sequential Python execution, not by an interactive Jupyter kernel in the preparation environment.

## Files and evidence

- `cleaning_rules.md`: rules, reasons and checks, written before cleaning.
- `expected_checks.json`: five literal expected results written before cleaning.
- `clean.py`: cleaning, full-input verification and sample selection.
- `output/cleaned_reviews.jsonl`: all 1,000 cleaned reviews with original fields preserved.
- `output/cleaned_sample_50.jsonl`: 50 cleaned records, rows 1-48, 60 and 92; includes all five checked cases. Purposeful audit sample, not random.
- `output/audit.json`: counts, types, missingness, conversions, duplicates, date range and metrics.
- `output/record_checks.json`: original, expected, actual, reasons and pass/fail for five records.
- `output/product_metrics.json`: metrics and denominators for all 829 parent IDs.
- `output/excluded_rows.json`: empty because no exact duplicates were found.
- `reproducibility.json`: all six outputs matched byte-for-byte in a fresh process.

## Results and limitations

1,000 input and output rows; zero exact duplicates and no missing source fields. Normalize 314 review bodies and 13 titles. Retain 389 variant/parent differences and 102 unverified purchases. Rating sum stays 4,406, average stays 4.406, low-rating share stays 105/1,000 (10.5%), and helpful votes total 1,229. Repeated parent IDs are valid reviews, not duplicates.

Missing metadata prevents reviewing listing attributes, checking the many-to-one join, or grouping comparable appliance types. Unknown source sampling prevents category-level inference. Ratings alone do not demonstrate listing defects; review complaints require human interpretation and metadata evidence.

Codex assisted with code and documentation. Its timestamp conversion suggestion was checked against a literal expected UTC timestamp, a full-file millisecond roundtrip, preservation of raw values, and unchanged metric totals. 

Submitted code/results commit: `79259a8fd8d55f677674a4230a2e5ca694bdf177`.

