# Zitong Guo Module 6 homework

This individual submission cleans every row of the team's 1,000-review Appliances sample. It does not validate the entire upstream category. Review the rules and five record checks before submitting the PDF on Gradescope.

## Source and scope

- Team source: `dataset/Appliances_sample.jsonl`, preserved unchanged.
- Repository source version: `2a623b24ff6e1a427426707117e4e45ed4d948c2`.
- Upstream: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 (McAuley Lab, Amazon Reviews 2023).
- SHA-256: `6e5ce91e627c1eb52471166a207b8b76b36e062835a544bcd793af4d743f1608`.
- Original sampling procedure and upstream download date are unknown; the Git version identifies the exact input used here.
- No metadata table was supplied. Checklist item 9 is Unresolved. No unsupported listing mismatch or subcategory conclusions are made.

## Branch and submission identity

- Personal branch: `codex/cleaning-zitong-guo`.
- Branch URL: https://github.com/dtry19/dso576-project-/tree/codex/cleaning-zitong-guo
- The submitted code/results commit is recorded below when the tested implementation is committed. A subsequent documentation commit may add its identifier and the PDF without changing the tested data/code.

## Run

From the repository root with Python 3.11 or later:

```sh
python3 zitong_guo/clean.py
```

Cleaning has no third-party dependencies. Verified using Python 3.12.14. For an independent output directory:

```sh
python3 zitong_guo/clean.py --output /tmp/zitong-independent-run
```

Alternatively open `dataset/proj_data_clean_zitong_guo.ipynb`, select Python 3, restart the kernel and run all cells. The saved cell outputs were produced by sequential Python execution, not by an interactive Jupyter kernel in the preparation environment.

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

Missing metadata prevents reviewing listing attributes, checking the many-to-one join, or grouping comparable appliance types. Unknown source sampling prevents category-level inference. Ratings alone do not demonstrate listing defects; review complaints require human interpretation and metadata evidence. Instructor repository access must be confirmed by the repository owner. Gradescope upload is the student's responsibility.

Codex assisted with code and documentation. Its timestamp conversion suggestion was checked against a literal expected UTC timestamp, a full-file millisecond roundtrip, preservation of raw values, and unchanged metric totals. This records automated verification, not personal review by the student.

Submitted code/results commit: `d816d115a2805ef63d5d023ef74e4a77dc7c2949`.

PDF: `output/pdf/Module_6_Zitong_Guo.pdf`. Rebuild with `python3 zitong_guo/build_report.py` after installing `requirements.txt`.
