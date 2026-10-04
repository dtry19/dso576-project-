import pandas as pd

SOURCE_FILE = "data/raw/Appliances_sample.jsonl"
OUTPUT_FILE = "cleaned_sample.csv"
REFERENCE_DATE = pd.Timestamp("2026-10-04")

# 1. Load the 1,000-review project dataset.
reviews_full = pd.read_json(SOURCE_FILE, lines=True)

# 2. Define and run validation checks.
missing_counts = reviews_full.isna().sum()
blank_text_count = (reviews_full["text"].str.strip() == "").sum()
blank_title_count = (reviews_full["title"].str.strip() == "").sum()

# images contains lists, so use a comparison-only copy for exact duplicates.
reviews_compare = reviews_full.copy()
reviews_compare["images"] = reviews_compare["images"].astype(str)
exact_duplicate_count = reviews_compare.duplicated().sum()

invalid_ratings = (~reviews_full["rating"].between(1, 5)).sum()
negative_helpful_votes = (reviews_full["helpful_vote"] < 0).sum()
future_reviews = (reviews_full["timestamp"] > REFERENCE_DATE).sum()

# 3. Apply the cleaning decision.
# No records violate the predefined rules, so all rows are retained unchanged.
reviews_clean = reviews_full.copy()

# 4. Five representative / difficult cases.
record_1 = reviews_clean[reviews_clean["rating"] == 1].head(1)
record_2 = reviews_clean[reviews_clean["rating"] == 5].head(1)
record_3 = reviews_clean[reviews_clean["verified_purchase"] == False].head(1)
record_4 = reviews_clean[
    reviews_clean["helpful_vote"] == reviews_clean["helpful_vote"].max()
].head(1)

repeated_parent = reviews_clean["parent_asin"].value_counts().index[0]
record_5 = reviews_clean[
    reviews_clean["parent_asin"] == repeated_parent
].head(1)

difficult_cases = pd.concat([
    record_1,
    record_2,
    record_3,
    record_4,
    record_5,
])

# 5. Add 45 additional rows and create the 50-row submission sample.
normal_cases = reviews_clean.drop(
    index=difficult_cases.index,
    errors="ignore",
).head(45)

submission_sample = pd.concat(
    [difficult_cases, normal_cases],
    ignore_index=True,
)

submission_sample.to_csv(OUTPUT_FILE, index=False)

# 6. Final reproducibility / QA checks.
print("Original shape:", reviews_full.shape)
print("Cleaned shape:", reviews_clean.shape)
print("Missing values:", int(missing_counts.sum()))
print("Blank text:", int(blank_text_count))
print("Blank titles:", int(blank_title_count))
print("Exact duplicates:", int(exact_duplicate_count))
print("Invalid ratings:", int(invalid_ratings))
print("Negative helpful votes:", int(negative_helpful_votes))
print("Future reviews:", int(future_reviews))
print("Submission sample:", submission_sample.shape)
