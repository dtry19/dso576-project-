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

The sole input is **`data/monthly_wildfire.csv`** in this repository. It is bundled; do not fetch data, require credentials, or depend on a file in the student's Module 7 folder. It was created from Module 7's cleaned USDA FPA FOD wildfire file ([seventh edition](https://doi.org/10.2737/RDS-2013-0009.7)). Each row is one **calendar month**, not one fire. Parse `month` as a date. Required columns:

| Column | Definition |
| --- | --- |
| `month` | First day of the calendar month; one row per month in ascending order. |
| `fires` | Number of reported wildfire records discovered in that month. |
| `known_acres` | Sum of final reported fire sizes for records discovered that month; not distinct land burned in that month. |
| `sizes_known` | Number of records with a known fire size. |
| `previous` | Previous calendar month's `fires`; blank for the first month. |
| `change` | `fires - previous`; blank for the first month. |
| `running` | Cumulative `fires` from the first available month; never resets at a year boundary. |
| `average_3m` | Mean `fires` for the current and up to two preceding calendar months, calculated across the full series before filtering to a year. |

Validate required columns, parseable and unique month starts, increasing monthly order, numeric fields, nonnegative `fires` and `known_acres`, and `0 <= sizes_known <= fires`. Check that `previous`, `change`, `running`, and `average_3m` agree with the preceding rows within normal floating-point tolerance; do not silently repair inconsistent input. Show an actionable error naming the file, row/month, and field when validation fails. Blanks are allowed only for the first row's `previous` and `change`.

The bundled data has **396 rows**, January 1992–December 2024. It sums to **283,285** reported records. January 1992 has **92** records; 2023 has **8,191**, and 2024 has **8,182**. Use these as verification facts, **not hard-coded display values**. Other values, including known acres and peak month, must come from the CSV.

## 3. Page and interaction specification

The page opens with **2024** as focus year and **2023** as comparison year when both exist. Otherwise choose the latest available year and the nearest earlier year. Populate selectors only from years present in the data. Put a clear title, purpose sentence, labeled selectors, and brief interpretation note at the top.

Under the controls, show four focus-year cards:

1. Total **reported records**: sum of focus-year `fires`.
2. **Known reported acres**: sum of focus-year `known_acres`.
3. **Peak reporting month**: month with the largest focus-year `fires`, with its count; earliest month wins a tie.
4. **Difference from comparison year**: focus-year annual `fires` minus comparison-year annual `fires`, signed. Show a percentage using the comparison total as denominator only if that total is nonzero; otherwise show “N/A.”

Below the cards, show:

- A prominent **two-year monthly comparison** line chart using `fires`. Align January with January through December with December, using month number rather than full dates. Keep unavailable months as gaps, never invented zeros.
- A **focus-year trend** chart with `fires` and the CSV's `average_3m` on the same record-count scale. Never recompute the average after year filtering; January can include the preceding November and December.
- A **month-to-month change** chart from the CSV's `change`, with a visible zero line and negative values visually distinct. January uses the previous December if one exists; the first-ever month has no change.
- A **known reported acres** chart, clearly separate from record counts and labeled in acres.

Include a concise caption near each chart saying what question it answers. Add a footer that names the source and explains the limits of the measures. The language must consistently say **reported records** and **known reported acres**, never “all fires,” “fire risk,” or “acres burned that month.”

Changing the focus year updates all four cards and all focus-year charts, plus the comparison chart. Changing only the comparison year updates the comparison chart and difference card, leaving the focus-year charts unchanged. If the same year is selected twice, show one line and a clear same-year note. If any year has fewer than 12 monthly rows, show its available months and an incomplete-year note; do not fabricate observations.

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
