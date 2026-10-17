# BUILD_SPEC.md — California wildfire reports dashboard

Build the dashboard described here in **this repository**. The input data and locked Python environment are already included. The required result is a polished, responsive, **self-contained `dashboard.html`** that opens directly in a browser without a server or internet connection. Implement the reusable analysis behind it, run the build, check the output, and report the commands and checks you used.

Create `wildfire_analysis.py` for data validation and reusable calculations and `build_dashboard.py` for HTML generation. You may add supporting source files, but the final HTML must embed its data, CSS, JavaScript, and Plotly library. Do not edit `data/monthly_wildfire.csv`, the four-problem homework notebook, or its policies. The earlier Module 7 Streamlit app is separate and does not need to be changed.

## 1. User, decision, and scope

A California analyst reviews wildfire reports by **discovery month**. They need to identify months and year-to-year differences worth investigating in the source records. The dashboard makes the monthly pattern and comparison easy to inspect; it does **not** forecast, measure wildfire risk, establish causation, or claim that reported final fire sizes are acres newly burned during a month.

| Use case | User selects | Dashboard shows | Decision supported |
| --- | --- | --- | --- |
| Compare years | A focus year and comparison year | Monthly reported-record counts aligned by calendar month; annual count difference | Which months account for a difference and deserve closer investigation |
| Examine one year | A focus year | Monthly counts, three-month average, changes, and known reported acres | Which months have unusual reporting activity or reported size |

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
- **Recurring terms in low-rated reviews:** a ranked bar chart derived from `title` and `text` for 1–2-star reviews within the active filters. Label the results as frequent terms or phrases, not verified product defects or listing attributes. Exclude empty tokens and documented stop words, show the review count supporting each term, and show an explanatory empty state when no low-rated text remains.

Give each chart a short caption explaining the question it answers. Tooltips must report the underlying count and, where applicable, percentage; counts and percentages must use the same filtered denominator shown in the cards.

### Parent-ASIN prioritization and review evidence

Show a sortable table that helps the user choose a `parent_asin` for review. Each row represents one parent ASIN in the current rating, date, and verified-purchase scope. Supported columns are:

- `parent_asin`;
- total review count;
- low-rated review count and share;
- average rating; and
- total helpful votes.

Default the table to low-rated review count descending, then total helpful votes descending, then `parent_asin` ascending for a deterministic tie-break. Always display the total review count so a high percentage based on very few reviews is not presented without context. Do not assign “high,” “medium,” or “low” priority labels unless a later specification defines a transparent rule.

Selecting a table row or choosing a parent ASIN in the filter opens a detail panel modeled on the mockup's selected-product area. The panel must identify the selection as a **parent ASIN**, not a product name, and show its filtered review count, low-rated count/share, average rating, and verified-purchase count/share. Beneath the summary, show review evidence using actual `rating`, `title`, `text`, `timestamp`, `helpful_vote`, `verified_purchase`, and `asin` values. Truncate long text visually with an accessible expand/collapse control; do not alter the stored text. Do not display `user_id` because it is unnecessary for the stated analysis.

### Interaction and unsupported states

Every global filter updates the cards, charts, ranking table, and selected-parent panel from one consistent filtered set. Selecting a parent ASIN narrows the overview and highlights the same row in the table; clearing it returns to the broader filtered view. If a filter combination returns no reviews, retain the controls and headings, show zero/N/A cards as specified, and replace each visualization or table with a clear “No reviews match these filters” message.

Do not show product names, product types, listing descriptions, features, dimensions, metadata coverage, metadata gaps, or comparisons between review concerns and listing content. Those fields are not present in the repository. Review text may indicate topics for investigation, but the dashboard must not claim that a recurring term proves a product defect or missing listing information. Add a footer naming the Amazon Reviews 2023 Appliances sample as the source and explaining these limitations.

## 4. Components and contracts

| Component | Input | Output | Correctness check |
| --- | --- | --- | --- |
| `load_monthly` in `wildfire_analysis.py` | CSV path | Validated, ordered monthly DataFrame | Rejects missing/duplicate/invalid fields and contradictory derived columns with a useful error. |
| `summarize_year` in `wildfire_analysis.py` | Validated DataFrame, year | Reusable year summary with totals and peak month | Annual totals equal sums of that year's rows; earliest tied peak wins. |
| `year_series` in `wildfire_analysis.py` | Validated DataFrame, year | Chart-ready monthly values keyed by month number | Preserves CSV averages and changes, including cross-year January values and missing months. |
| `build_dashboard.py` | Validated records and reusable summaries/series | Self-contained `dashboard.html` | No live data fetch; selectors update the specified elements; display values reconcile to backend outputs. |

Precompute summaries and chart-ready values for all years in Python, then embed them in the HTML. Browser JavaScript should select and render those prepared values, with one clearly defined calculation for the selected-year difference. Do not duplicate raw-data aggregation in multiple UI components. Functions must **return** values or DataFrames rather than only print them. Keep analysis separate from rendering so a metric definition can change without edits to unrelated layout code.

## 5. Technical and visual design

Run from this repository with `uv sync --frozen`, then `uv run python build_dashboard.py`. Use the locked **pandas** and **Plotly** packages. Embed Plotly's JavaScript inside the final HTML; do not use a CDN or API. The monthly table is small, so a static HTML file with embedded chart data is appropriate and needs no database, server, cache, or secrets. The file should open with a `file://` URL and remain usable offline.

Use a warm off-white page background (`#F7F6F2`), white cards, dark ink text (`#18252D`), rust for the focus year (`#C75B39`), and teal for the comparison year (`#167D79`). Use a system sans-serif font. Arrange the header and controls, then a four-card summary row, one wide comparison chart, then a balanced grid of the remaining charts. Use generous whitespace, readable axes and tooltips, consistent number formatting, and captions near the evidence. On narrow screens, stack cards and charts without clipping labels. Label controls, preserve keyboard operation and visible focus states, and distinguish chart series by both color and text.

## 6. Build order and acceptance checks

1. Read and validate the bundled CSV. Confirm the 396 months and sample counts below before rendering.
2. Implement the reusable year summaries and chart series. Check 2023 and 2024 totals, plus one January value from the full series.
3. Build the HTML shell, controls, cards, and comparison chart; open the file locally and exercise both selectors.
4. Add the focus-year charts, captions, responsive styling, and keyboard details.
5. Run the checks below, fix discrepancies, and report the result.

Acceptance checks:

- `uv run python build_dashboard.py` creates `dashboard.html` in this repository. Opening the file directly requires no server or network.
- The default view computes **8,182** focus-year records for 2024, **8,191** comparison-year records for 2023, and a **−9** record difference. These values are computed from the CSV rather than typed into the HTML as constants.
- The source table's first month has **92** records, and December 2024 `running` is **283,285**.
- The comparison chart aligns equal calendar months. Changing the comparison year leaves the focus-year charts unchanged. Choosing the same year twice does not draw two indistinguishable lines.
- The focus-year `average_3m` and `change` preserve cross-year January values from the CSV. Missing months, first-row blanks, and zero comparison totals do not break the page.
- An invalid copy of the CSV with a missing required column or duplicate month is rejected with an actionable error. Do this check on a temporary copy; do not alter the bundled CSV.
- The page is readable at laptop and phone widths, selectors work with a keyboard, and every title, card, and tooltip keeps counts separate from acres.

When finished, name the files created, give the build command, and report which checks passed and any remaining limitation. Do not claim that a polished page by itself validates the data or proves a change in wildfire risk.
