# Cleaning rules recorded before execution

Student: Jenny (Zitong) Guo 

Scope: Every row of the team's committed dataset/Appliances_sample.jsonl (1,000 reviews), not the entire Appliances category. Original upstream sampling method and download date are unknown. No product metadata is supplied in the repository.

Vision: An Amazon Appliances category manager prioritizes listings for product-information review and attributes for standardization within comparable appliance types. 

Business question: Which listings warrant manual review for recurring customer requirements that may be missing or unclear? The present cleaning stage supplies review counts, average ratings, low-rating proportions, helpful-vote totals and traceable text; it does not claim to measure listing mismatch without metadata and human validation.

| Rule | Reason | Verification |
|---|---|---|
| Preserve the original file and all raw values in cleaned records. Assign source_row from the one-based input line. | Auditability; no universal review ID is provided. | SHA-256 before/after and row-by-row raw-field equality. |
| Convert integral ratings in 1..5 to integer; otherwise cleaned rating is null and flagged. | Valid scale without imputing sentiment. | Count conversion failures, rating sums and distributions. |
| Interpret timestamp as Unix milliseconds in UTC; retain numeric original. Flag dates outside May 1996 through September 2023. | Avoid seconds/nanoseconds confusion and local timezone drift. | Independent fixed expectation for source row 1 and full timestamp roundtrip. |
| In titles and review text replace only known HTML break tags with spaces, decode HTML entities once, and collapse whitespace. Preserve case, punctuation, numbers and other literal tags. | Readable review evidence without deleting negation, model numbers or comparative symbols. | Change counts, before/after examples and literal expected row 4 text. |
| Preserve IDs as strings without case folding or numeric conversion. Flag blank or malformed ASINs. Keep asin and parent_asin separately. | Variants can differ from parent listings; leading zeros are meaningful. | Validate all IDs, compare to raw values, fixed row 2 expectation. |
| Remove only exact source duplicates, keeping the earliest source row. Count repeated IDs and user_id/asin/timestamp collisions separately, retaining nonidentical records. | Multiple reviews of a listing are legitimate. | Duplicate counts, exclusion log, row reconciliation. |
| Keep missing values as null; do not fill ratings, text, dates, IDs or votes. Empty image arrays mean no attached images, not a missing review. | Avoid invented evidence or changing denominators silently. | Missing counts before/after for every source and cleaned field. |
| Accept nonnegative integer helpful votes and genuine Boolean purchase flags; otherwise set cleaned value null and flag. Keep unverified purchases and unusually high votes. | Neither is proof of an invalid review. | Failure counts, totals, fixed rows 60 and 92. |
| Do not merge with the unrelated partial metadata download. Mark required metadata join unresolved. | Partial downloads can produce misleading unmatched rates and subcategory assignments. | Report missing metadata and future many-to-one join requirements. |
| Compute low-rating share as ratings <=2 / valid rating count, average on valid ratings only, helpful total on valid votes only. Include missing parent keys in an explicit null group. | Transparent denominators and no silent row loss. | Overall and per-parent denominators, sums and counts reconcile. |

Expected record checks are saved in expected_checks.json before executing clean.py. They were selected by inspecting raw input. Codex assists with code and documentation; the included verification is automated, not a claim of personal student review.

Limitations: convenience sample of unknown selection, no metadata/subcategories/historical listing snapshots, no validated mismatch labels, no population representativeness. Quality, delivery and usage complaints must not automatically be called listing defects.
