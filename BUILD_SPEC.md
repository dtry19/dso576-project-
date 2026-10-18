# BUILD_SPEC.md — Amazon Appliances Review Explorer

Build an interactive dashboard in this repository using the cleaned Amazon Reviews 2023 Appliances sample. The dashboard helps an Amazon Appliances category manager analyze customer ratings, review activity, and recurring concerns to identify parent products that may require further investigation.

The dashboard must use the cleaned dataset documented in Section 2 and follow the interactions specified in Section 3. All metrics and visualizations must be calculated from actual review data rather than illustrative mockup values.

The implementation should include reusable analysis functions, data validation, and an interactive dashboard. Technical requirements and acceptance checks are defined in Sections 4–6.

Do not modify the original dataset or infer unavailable product metadata. The dashboard must clearly communicate the limitations of the 1,000-review sample.

## 1. User, decision, and scope

An Amazon Appliances category manager needs to identify parent products that may require closer investigation based on customer feedback. The manager must determine which products receive recurring low-rated reviews, what concerns appear frequently in customer comments, and how review activity changes over time.

The dashboard consolidates customer ratings, review text, timestamps, verified-purchase information, and parent ASIN identifiers into an interactive interface. Instead of manually reviewing individual comments, the manager can filter feedback, compare parent products, and examine supporting evidence to prioritize further investigation.

| Use case | User selects | Dashboard shows | Decision supported |
| --- | --- | --- | --- |
| Identify recurring concerns | Rating, review year, and verified-purchase filters | Rating distribution and frequently mentioned terms in low-rated reviews | Which customer concerns deserve further investigation |
| Prioritize parent products | A parent ASIN or ranked parent-ASIN table | Review counts, low-rated share, average rating, and helpful votes | Which parent products warrant closer examination |
| Examine review activity | A review year or all available dates | Monthly review counts and rating patterns | Which periods may require further review |
| Review supporting evidence | A selected parent ASIN | Review titles, text, ratings, dates, and verified-purchase status | Whether the available reviews justify additional manual investigation |

The dashboard supports review exploration and investigation prioritization, not automatic conclusions about product defects or listing accuracy. The current dataset contains 1,000 customer reviews without product listing metadata. Therefore, the dashboard cannot verify missing product attributes, estimate sales or inventory, or represent the full Amazon Appliances category.

Every major display element must serve one of these use cases.

## 2. Input and definitions

The project uses the bundled **Amazon Reviews 2023 Appliances sample** described in the repository README. The data is line-delimited JSON (JSONL), with one JSON object per line. Each row represents **one customer review**, not one product or product listing. Do not fetch another dataset or use the illustrative values in the dashboard mockup as data.

### Files and roles

| File | Role | Rows inspected |
| --- | --- | ---: |
| `dataset/Appliances_sample.jsonl` | Original project input. Preserve it unchanged so the cleaning process remains reproducible. | 1,000 |
| `dataset/output/Appliances_cleaned.jsonl` | Cleaned, full-size analysis input for dashboard calculations. It preserves the 1,000 source reviews and adds source-row provenance. | 1,000 |
| `dataset/output/Appliances_cleaned_50_examples.jsonl` | QA/example subset drawn from the cleaned file. Use it for inspection and demonstrations, not for full-dataset totals. | 50 |

`dataset/proj_data.ipynb` reads the original sample but is code, not an additional data source. The inspected cleaned file converts the source millisecond timestamps to ISO-style date-time strings, normalizes review text (including HTML and repeated whitespace), represents ratings as integers, and adds `original_row_number`. Dashboard analysis should read the cleaned full-size file and retain the raw file for validation and traceability.

### Row fields

| Column | Definition |
| --- | --- |
| `rating` | Customer star rating. Values in the inspected files are whole numbers from 1 through 5. A low-rated review means a rating of 1 or 2 stars. |
| `title` | Customer-written **review title**; it is not a product or listing title. |
| `text` | Customer-written review body and the main source for identifying recurring concerns. |
| `images` | List of images attached to the review. An empty list means that the review has no attached image. |
| `asin` | Amazon identifier for the reviewed item or variant; suitable for item-level grouping. |
| `parent_asin` | Parent product identifier used to group related item variants. |
| `user_id` | Identifier for the reviewer. Treat it as an opaque identifier, not customer profile information. |
| `timestamp` | Review time: epoch milliseconds in the original sample and an ISO-style date-time string in the cleaned files. Parse it as a date-time before filtering by review date. |
| `helpful_vote` | Nonnegative count of helpful votes recorded for the review. |
| `verified_purchase` | Boolean indicating whether the review is marked as a verified purchase. |
| `original_row_number` | One-based source row number added to cleaned files for traceability. It is not present in the original sample and is not a permanent review ID. |

The current files contain review data and product identifiers, but **do not contain product name, product type, features, description, dimensions, details, or other listing-metadata fields** shown in the mockup. Therefore, metadata coverage, metadata gaps, and product-type filters cannot be calculated from the current project files alone. Do not infer those fields from review text or mistake `title` for a product name. ASIN-level review metrics can still be calculated, but any listing-metadata feature requires a separately supplied and documented product metadata file.

### Validation and verification

When loading a JSONL file, report an actionable error that names the file, line number, and field. Do not silently repair or discard invalid records. Check that:

- every nonblank line is valid JSON and contains the expected columns;
- `rating` is numeric, whole, and between 1 and 5;
- `title` and `text` are strings, `images` is a list, and `verified_purchase` is boolean;
- `asin`, `parent_asin`, and `user_id` are non-empty strings;
- `timestamp` is numeric epoch milliseconds in the raw file or a parseable date-time in a cleaned file;
- `helpful_vote` is a nonnegative whole number;
- cleaned `original_row_number` values are whole, unique, in source range, and map back to the corresponding raw records;
- the full cleaned file has the same row count as the source, while every 50-example row matches its full-cleaned record by `original_row_number`; and
- exact duplicate records are flagged for review rather than automatically removed solely because an ASIN or user appears more than once.

As inspection-time reconciliation facts, all three files parsed without malformed JSON or missing/null fields. The full sample contains **1,000 reviews**, **870 distinct `asin` values**, **829 distinct `parent_asin` values**, and **625 distinct users**. It includes **105 low-rated reviews (10.5%)**, **898 verified-purchase reviews**, and review timestamps from September 2009 through March 2023. These are checks against the current files, not values to hard-code in dashboard HTML; displayed metrics must be calculated from the selected input and active filters. Empty image lists are valid and common (957 of 1,000 source rows).

## 3. Page and interaction specification

The page is an **Appliance Review Explorer** for examining customer feedback in the cleaned Appliances review sample. Follow the mockup's broad organization—a clear header, a compact filter row, summary cards, overview visuals, a ranked identifier table, and a selected-item evidence panel—but calculate every value from `dataset/output/Appliances_cleaned.jsonl`. The mockup's displayed figures are not inputs or expected results.

### Header, scope, and filters

At the top, show the dashboard title and a short purpose statement: identify rating patterns, review activity, and recurring language that may warrant closer investigation of an appliance item or parent product. Include a visible note that the dashboard describes the repository's review sample and does not represent all Amazon appliance reviews.

Provide these labeled controls using only values present in the data:

- **Rating:** all ratings, 1–2 stars (low-rated), or an individual rating from 1 through 5.
- **Review date:** an all-dates default plus available year choices derived from `timestamp`; do not offer years absent from the selected data.
- **Verified purchase:** all, verified, or not verified, based on `verified_purchase`.
- **Product identifier:** an optional searchable `parent_asin` selector, with a way to clear the selection. Show the identifier itself because no product name is available.

Place a **Reset filters** control beside the filters. Do not include the mockup's Product Type filter because the project has no product-type field. All controls must have persistent text labels, support keyboard operation, and visibly indicate focus.

### Summary cards

Under the filters, show four cards calculated from the currently filtered reviews:

1. **Reviews:** row count after filtering.
2. **Low-rated reviews:** count and share of filtered reviews with `rating` equal to 1 or 2. If no rows remain, show 0 reviews and “N/A” for the share.
3. **Distinct parent ASINs:** distinct non-empty `parent_asin` count. Label this as an identifier count, not a count of listings with known metadata.
4. **Verified purchases:** count and share with `verified_purchase == true`; use “N/A” for the share when no rows remain.

Do not hard-code the current sample totals in the page. Recompute all four cards whenever any filter changes.

### Review overview

Use the left and center portions of the mockup as a visual hierarchy reference, with these data-supported displays:

- **Rating distribution:** a bar or donut chart showing review count and percentage for ratings 1 through 5. Keep all five rating categories visible and show zero where a valid category has no filtered reviews.
- **Reviews over time:** a monthly time-series chart based on parsed `timestamp`, showing counts only for months represented by filtered records. Do not invent observations for months outside the filtered range.
- **Recurring terms in low-rated reviews:** a ranked bar chart derived from `title` and `text` for 1–2-star reviews within the active filters. Label the results as frequent terms or phrases, not verified product defects or listing attributes. Exclude empty tokens and documented stop words, show the review count supporting each term, and show an explanatory empty state when no low-rated text remains. Recurring terms are exploratory signals that require examination of the underlying review text before being interpreted as customer concerns.

Give each chart a short caption explaining the question it answers. Tooltips must report the underlying count and, where applicable, percentage; counts and percentages must use the same filtered denominator shown in the cards.

### Parent-ASIN prioritization and review evidence

Show a sortable table that helps the user choose a `parent_asin` for review. Each row represents one parent ASIN in the current rating, date, and verified-purchase scope. Supported columns are:

- `parent_asin`;
- total review count;
- low-rated review count and share;
- average rating; and
- total helpful votes.

Default the table to low-rated review count descending, then total helpful votes descending, then `parent_asin` ascending for a deterministic tie-break. Always display the total review count so a high percentage based on very few reviews is not presented without context. Do not assign “high,” “medium,” or “low” priority labels unless a later specification defines a transparent rule. All ranking metrics must reflect the active filters. If the rating filter excludes 1–2-star reviews, the low-rated review count and share should display zero rather than values from the unfiltered dataset.

Selecting a table row or choosing a parent ASIN in the filter opens a detail panel modeled on the mockup's selected-product area. The panel must identify the selection as a **parent ASIN**, not a product name, and show its filtered review count, low-rated count/share, average rating, and verified-purchase count/share. Beneath the summary, show review evidence using actual `rating`, `title`, `text`, `timestamp`, `helpful_vote`, `verified_purchase`, and `asin` values. Truncate long text visually with an accessible expand/collapse control; do not alter the stored text. Do not display `user_id` because it is unnecessary for the stated analysis.

### Interaction and unsupported states

Every global filter updates the cards, charts, ranking table, and selected-parent panel from one consistent filtered set. Selecting a parent ASIN narrows the overview and highlights the same row in the table; clearing it returns to the broader filtered view. If a filter combination returns no reviews, retain the controls and headings, show zero/N/A cards as specified, and replace each visualization or table with a clear “No reviews match these filters” message. If a selected parent ASIN has no reviews under the current filters, retain the selection, display the empty-state message, and allow the user to clear the parent-ASIN filter.

Do not show product names, product types, listing descriptions, features, dimensions, metadata coverage, metadata gaps, or comparisons between review concerns and listing content. Those fields are not present in the repository. Review text may indicate topics for investigation, but the dashboard must not claim that a recurring term proves a product defect or missing listing information. Add a footer naming the Amazon Reviews 2023 Appliances sample as the source and explaining these limitations.

## 4. Components and contracts

The components must support the three-step workflow: identify customer concerns, examine potential metadata gaps, and prioritize listings for investigation. Keep reusable calculations in `appliance_analysis.py` and HTML generation in `build_dashboard.py`. Functions must return structured values or DataFrames rather than only print results.

| Component | Input | Output | Correctness check |
| --- | --- | --- | --- |
| `load_reviews` | Full cleaned review JSONL and raw source for reconciliation | Validated reviews with parsed dates and source-row identifiers | Enforces Section 2 validation and preserves one row per source review. |
| `load_metadata` | Separately supplied listing metadata and a documented field mapping | One normalized metadata record per `parent_asin`, retaining original fields and source information | Rejects blank keys and unresolved duplicate keys; records absent fields without inventing values. |
| `join_reviews_metadata` | Validated reviews and metadata | Reviews linked to metadata, with an explicit match status | Uses a many-to-one left join on `parent_asin`; review count and review identifiers remain unchanged. Reports unmatched identifiers. |
| `tag_concerns` | Review titles/bodies and documented concern rules | Review-to-concern matches with supporting text | Uses only 1–2-star reviews; counts each review at most once per concern and retains evidence for each match. |
| `assess_metadata` | Relevant parent identifiers, matched metadata, and concern-to-attribute rules | Field coverage and a parent-by-concern evidence table | Distinguishes missing records, empty fields, missing attribute evidence, available evidence, and cases requiring manual comparison. |
| `summarize_scope` | Linked reviews, concern matches, metadata assessments, and active filters | Summary cards, chart series, and concern/coverage comparisons | All review metrics use one filtered review set; product metrics count distinct parent identifiers rather than joined review rows. |
| `rank_listings` | Filtered review evidence and metadata assessments | One row per parent ASIN with supporting counts, potential gaps, and investigation priority | Ranking follows the explicit rule below, with deterministic ties and visible sample sizes. |
| `get_listing_evidence` | Selected parent ASIN and current filtered scope | Supporting reviews, listing field excerpts, and potential follow-up checks | Every quotation and metadata excerpt is traceable to its source; review titles are never used as product names. |
| `build_dashboard.py` | Validated analysis outputs and source text needed for interaction | Self-contained `dashboard.html` | Offline controls update all components consistently, and displayed values reconcile to reusable calculations. |

### Metadata prerequisite and comparison rules

The new vision requires an additional, documented metadata file. Its field mapping must identify `parent_asin`, product title, product type when available, features, description, and details. Record the source and extraction date where known. Retain structured attribute keys and units. Do not treat review data's `title` as a listing title or infer product type from customer comments. If metadata is supplied at variant level, define the variant mapping before joining; do not arbitrarily collapse conflicting variants into a parent record.

Until this input is supplied, show review analysis and label the metadata panels **“Listing metadata not supplied.”** Do not classify unmatched products as having missing listing attributes. Unmatched records after a valid metadata load use **“No matching metadata record.”**

Define an inspectable concern dictionary for installation, size/dimensions, compatibility, noise, missing parts, instructions, and durability. Document keywords, phrase matching, normalization, exclusions, and the relevant metadata attributes for each concern. Matches are screening signals, not verified complaints: a phrase may be negated, ambiguous, or unrelated to an information gap. Allow a review to match several concerns and explain that concern percentages therefore need not sum to 100%.

For each concern, report its distinct supporting review count and share of all filtered low-rated reviews, including low-rated reviews with no matched concern in the denominator. For field coverage, divide the number of distinct matched parent ASINs with a non-empty field by the number of distinct matched parent ASINs in the filtered scope. Display that denominator and metadata match coverage separately. A non-empty description does not establish that dimensions or compatibility information is present.

At the parent-and-concern level, flag a **potential information gap** only when a metadata record is available and the documented attribute rule finds no relevant evidence in its mapped fields. Preserve the fields searched and matching excerpts. An available attribute is not proof that the listing is correct or clear. Label unresolvable comparisons **“Manual review needed.”** Claim a potential inconsistency only when explicit, comparable values and units support it; otherwise show the review and listing text side by side. Metadata may reflect a different time from the review, so do not claim it represents what the customer originally saw.

### Investigation priority

For an initial, transparent screening rule, count distinct filtered low-rated reviews mentioning at least one concern with a potential information gap for that parent ASIN. Count a review once even when it supports multiple gaps. Assign **High** for 3 or more such reviews, **Medium** for 2, and **Low** for 1. Products with no such evidence show **“No gap signal under these rules”**; unavailable or unmatched metadata shows **“Not assessable.”** These labels indicate investigation priority, not defect severity or a validated assessment of listing quality.

Sort High, Medium, and Low first, followed by no-gap-signal and not-assessable records. Within each group, sort by supporting review count descending, distinct potential-gap attributes descending, and `parent_asin` ascending. Display total reviews and low-rated reviews alongside the supporting count. Document these initial thresholds and expose the evidence behind each label.

## 5. Technical and visual design

### Implementation and delivery

Use Python with pandas for validation, joins, concern tagging, and reusable summaries, and Plotly for interactive charts. Deliver `dashboard.html` with embedded data, CSS, JavaScript, and Plotly. It must open directly through a `file://` URL and support filtering, sorting, selection, and evidence expansion offline, without a database, server, CDN, API, or credentials.

The intended commands are `uv sync --frozen` and `uv run python build_dashboard.py` from this repository once `pyproject.toml`, `uv.lock`, the cleaned full review input, and the metadata input have been supplied. These prerequisites are not all present in the current checkout; do not claim the full build is ready or substitute the QA subset. Preserve source data and embed only fields needed for the dashboard; exclude reviewer identifiers. Escape review and listing text before rendering it as HTML.

Compute concern matches and metadata assessments once in Python. In the browser, use one shared filter state and one aggregation path to derive the current cards, charts, ranking, and evidence; do not implement separate metric definitions in each visual. This local HTML approach is intended for the documented sample. If inputs expand substantially, measure file size and interaction speed before deciding whether a different delivery approach is needed.

### Layout and visual identity

Use the mockup's title **“Appliance Listing Review”** and subtitle **“Turn customer feedback into clearer, more complete product listings.”** Identify the intended user as an Amazon Appliances category manager. Use a pale background (`#F7F8FC`), white cards, dark text (`#22324A`), burgundy headings (`#940B32`), rose concern bars (`#D4778A`), and blue metadata charts (`#3879C4`). Use a system sans-serif font, restrained shadows, rounded cards, and consistent spacing.

Arrange the page in this order:

1. **Header and filters:** product type when metadata provides it, rating, review date, verified-purchase status, and Reset. Default to all available dates and derive date choices from the input. If offering “Last 12 months,” label it as relative to the latest review date in the dataset. Keep reviews with unmatched metadata selectable through an explicit unknown-type option. Omit product type when the field is unavailable.
2. **Summary cards:** filtered review count, low-rated count/share, distinct reviewed parent ASINs, and metadata match coverage. Label reviewed products separately from all products in the metadata file. Use computed sample values rather than the mockup's illustrative totals.
3. **Three numbered workflow columns:** concerns on the left, metadata comparison in the center, and listing prioritization on the right. On narrow screens, stack these in the same order.

### Workflow panels and interactions

- **1 — Find recurring customer concerns:** show a horizontal concern bar chart with supporting counts and percentages, a low-rated review-share chart, and expandable review evidence. Selecting a concern highlights its evidence and corresponding metadata attributes in the other panels; it does not silently change the global review denominator.
- **2 — Check listing information and metadata gaps:** show non-empty field coverage for title, features, description, and details among matched reviewed products. Add a concern-to-attribute comparison table that labels each denominator, followed by review-versus-listing evidence with textual statuses. Missing metadata receives an unavailable state, never a zero-coverage chart suggesting measured absence.
- **3 — Prioritize listings for investigation:** show a sortable table containing product title when available, parent ASIN, product type when available, total and low-rated review counts, supporting gap-review count, potential-gap attributes, and priority. Below it, show a selected-product panel with customer quotations, available listing excerpts, and a recommended manual check tied to the evidence. Product images are optional and must come from documented metadata, with a fallback when absent.

Global filters update all three workflow panels consistently. Selecting a listing highlights its ranking row and updates the detail and comparison evidence while retaining the broader ranking for comparison; display the selected parent ASIN prominently and provide a clear-selection control. Concern selection narrows evidence and highlights relevant attributes without recalculating global cards or priority under a different, hidden scope. Reset clears both global filters and selections.

Show counts with thousands separators, percentages to one decimal place, and average ratings to one decimal place where used. Tooltips and captions must explain denominators. Empty results retain headings and controls, show zero counts and N/A percentages, and explain whether reviews, concern evidence, or metadata are unavailable. Use visible labels and text badges alongside color; support keyboard navigation, visible focus, accessible chart summaries, and expandable text. Keep page content within laptop and phone widths, allowing the ranking table its own labeled horizontal scroll area if necessary.

The footer must name the actual review and metadata sources, state the available sample size and date range, and explain that concern matching and potential-gap flags support manual investigation. The dashboard must not present these signals as proof of defects, historical listing omissions, sales effects, or inventory needs.

## 6. Build order and acceptance checks

1. Confirm that the raw sample, full cleaned input, and 50-example QA subset named in Section 2 exist. If a cleaned file or the locked environment is missing, report the missing prerequisite before building; do not substitute the QA subset or invent data.
2. Validate the JSONL inputs against Section 2, including source-row provenance, row-count reconciliation, and duplicate reporting. Preserve the original sample unchanged.
3. Implement reusable review calculations for filters, summary cards, rating distribution, monthly activity, recurring low-rated terms, parent-ASIN ranking, and selected-parent evidence. Document tokenization and stop words. Use one consistent filtered set across components.
4. Build the HTML shell, labeled controls, four summary cards, and overview charts. Add the sortable parent-ASIN table, selection behavior, review evidence, and accessible text expansion.
5. Add empty states, captions, source and limitation notes, responsive styling, and keyboard support. Embed the data, CSS, JavaScript, and Plotly library in `dashboard.html`.
6. Run the acceptance checks below, fix discrepancies, and report each check as passed, failed, or blocked with supporting evidence. Do not report a check as passed solely because it appears in this specification.

Acceptance checks:

- **Build and offline use:** With the locked environment present, `uv sync --frozen` and `uv run python build_dashboard.py` succeed and create `dashboard.html` in this repository. Open it directly with a `file://` URL and disconnect networking; filters, charts, sorting, selection, and review expansion still work without a server, CDN, API, or live data fetch.
- **Input reconciliation:** Compute the Section 2 inspection facts from the files: 1,000 raw and full-cleaned reviews, 50 matching QA examples, 870 distinct ASINs, 829 distinct parent ASINs, 625 distinct users, 105 low-rated reviews, and 898 verified purchases, with timestamps spanning September 2009 through March 2023. Reconcile every cleaned row to its raw source through `original_row_number`. Investigate discrepancies rather than hard-coding the expected values or silently dropping records.
- **Default cards:** With all filters cleared, show 1,000 reviews, 105 low-rated reviews (10.5%), 829 distinct parent ASINs, and 898 verified purchases (89.8%), calculated from the full cleaned input. The 50-example subset must not supply dashboard totals.
- **Filter consistency:** Exercise rating, available review year, verified-purchase status, and parent-ASIN filters individually and in combination. Independently calculate the expected results for at least one combined selection and reconcile the cards, charts, table, and evidence panel to that same filtered set. Selecting an individual rating of 3, 4, or 5 stars produces zero low-rated counts and 0% low-rated shares in the cards, ranking table, and selected-parent panel when reviews remain; empty results use N/A shares. Reset restores the default view. Year and identifier options come from the input; no product-type control is present.
- **Overview calculations:** Rating counts sum to the filtered review count, use that count as the percentage denominator, and retain all five categories, including zeros. Monthly counts sum to the same review count and use parsed review timestamps without inventing observations. Frequent terms use only filtered 1–2-star review titles and bodies, count each supporting review at most once per term, exclude documented stop words, and show an explanatory state when no low-rated text remains. Verify that the page explains that recurring terms are exploratory signals requiring examination of the underlying review text before interpretation as customer concerns.
- **Parent-ASIN ranking and evidence:** Reconcile each table row's review count, low-rated count/share, average rating, and helpful votes to the underlying filtered reviews. Verify the default ordering of low-rated count descending, helpful votes descending, and parent ASIN ascending, and exercise sorting controls. Selecting a row or identifier narrows the overview, highlights the same table row, and updates the detail panel; clearing the selection restores the broader scope. Evidence preserves actual review fields and supports accessible expand/collapse without displaying `user_id`.
- **Empty and boundary cases:** Use temporary fixtures where needed to check no matching reviews, no low-rated text, a single review, an absent rating category, and zero helpful votes. Empty results retain controls and headings, show zero counts and N/A shares, and display “No reviews match these filters” in charts and the table. If other filters leave a selected parent ASIN with no matching reviews, retain that selection, show the empty-state message in the detail panel as well, and keep the parent-ASIN clear control available. Clearing the parent-ASIN filter restores the broader scope while preserving the other filters. Do not divide by zero or present missing evidence as a product finding.
- **Validation failures:** On temporary copies only, test malformed JSON, a missing required field, an invalid rating or timestamp, a negative helpful-vote count, and duplicate or out-of-range `original_row_number` values. Each invalid record is rejected with an actionable message naming the file, line, and field. Exact duplicate reviews are flagged for review; repeated ASINs or users alone are not grounds for removal. Do not alter the bundled source or cleaned inputs for these checks.
- **Usability and scope:** Inspect laptop and phone widths for clipped labels or horizontal overflow. Complete filtering, reset, table sorting/selection, and evidence expansion using a keyboard with persistent labels and visible focus. Check chart captions and tooltips for correct counts and denominators. The page identifies parent ASINs as identifiers, labels recurring language as topics for investigation, and visibly states the sample's scope and lack of listing metadata; it makes no unsupported product-defect or listing-quality claims.

When finished, name the files created or changed, give the build and verification commands, and report the checks actually run with their results and remaining limitations. Identify missing inputs or environment files as blockers. A polished dashboard alone does not validate the data or establish that review concerns reflect missing or inaccurate listing information.
