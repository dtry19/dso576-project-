# My Module 9 audit

My audit focuses on the analysis code for concern tagging and the reviewed parent-ASIN count. I use reproducible code checks as evidence; dashboard interactions are outside the scope of this audit.

## Context

- Name: Jenny Guo
- Team app and version or commit checked: Appliance Listing Review, commit a1b411b. I audited the concern-tagging and parent-ASIN counting functions in appliance_analysis.py. 
- Intended user and decision: An Amazon Appliances category manager uses recurring review concerns to decide which parent products and listing information deserve manual investigation.

## 1. Feature audit

- Feature and intended behavior: Concern tagging for low-rated reviews, specifically distinguishing missing physical parts from missing instructions. I focus on the `tag_concerns` function. The build specification describes separate missing-parts and instructions categories and requires traceable evidence for each match.
- Inputs and steps to reproduce: Run `../09-audit/.venv/bin/python verification/check_jenny_audit.py` from the project root. The script passes four synthetic reviews to `tag_concerns`: a 1-star review saying “Missing instructions.”, a 1-star review saying “Missing hose.”, a 5-star review saying “Missing hose.”, and a 1-star review saying “No missing parts.” These are test fixtures, not quotations from the sample.
- Expected behavior: Under the interpretation that “Missing parts” means physical components, the first review should support only Instructions; the second should support Missing parts; the third should have no tags because it is not low-rated; the fourth should have no tags because it denies missing parts.
- Actual behavior and evidence: The first review receives both `instructions` and `parts`. The other three cases match the expected tags. In `appliance_analysis.py`, the Missing parts regex includes `missing` as a standalone alternative. `tag_concerns` searches each category independently, so “Missing instructions” satisfies both rules. Multiple categories are allowed by the specification, but this particular overlap has no physical-part evidence.
- Conclusion and any recommended change: My conclusion is that the current keyword rule can inflate the Missing parts signal for reviews about missing instructions. CR-JG-01 requests a more specific physical-component phrase rule and an explicit decision on whether manuals count as parts. I recommend keeping overlapping categories when each has supporting evidence. This fixture demonstrates one ambiguous classification, not its frequency in customer data or a verified product defect. No browser behavior was tested.

## 2. Number audit

- Number audited and its meaning: I audit the reviewed parent-ASIN count. The default result is 829 distinct parent identifiers represented in the 1,000-review sample.
- Formula, units, population, and time window: Count the unique `parent_asin` values in the active review scope. Unit: distinct parent identifiers. This is a count, with no percentage denominator. The default includes all dates in the supplied sample, September 2009 through March 2023; it is not limited to the last 12 months.
- Relevant data assumptions: Each row is one review; different reviews can share a parent ASIN. Parent identifiers are validated as non-empty strings. The count does not establish the number of variants, named products, metadata records, or all Amazon Appliances listings.
- Code checked: `appliance_analysis.py`, `summarize_scope`, lines 245–250 at the recorded commit: `parents = sorted(set(reviews.parent_asin))` followed by `parents=len(parents)` in the returned dictionary.
- What this code computes, in my own words: It removes repeated parent identifiers from the supplied scope and counts the remaining identifiers. It counts each parent once even when it has several reviews.
- Small test case and expected result: For parents `[A, A, B, C, C]`, expect 3. Restricting the input to the two A reviews should give 1. An empty scope should give 0.
- Actual result: The production summary returns 3, 1, and 0 respectively. For the full sample it returns 829 parents across 1,000 reviews. For the combined scope of unverified purchases with 1–2-star ratings, it returns 15 parents across 15 reviews.
- Independent calculation or check of a specific assumption/code line: `verification/check_jenny_audit.py` independently parses the original JSONL using Python's standard `json` module, applies the combined conditions directly, and counts a set of parent identifiers without calling the production loader or summary for the independent result. It compares those counts with the production summary loaded from the cleaned data. Both scopes agree: 829 and 15. The production loader also checks cleaned-to-raw provenance.
- What the evidence establishes and what remains uncertain: The distinct-parent calculation agrees with independent raw-data counts for the full sample and one combined scope, and handles the tested repeated-parent and empty fixtures. It does not establish that browser filters pass the correct rows, that the card displays these outputs, or that every possible filter combination works. Parent-ID validity against Amazon and sample representativeness remain untested.
- Recommended change, if any: I do not recommend changing the formula based on these checks. I recommend labeling the metric “Reviewed parent ASINs” and verifying the connection between the UI and analysis code when a dashboard build is available; see CR-JG-02.

Reproduction: `verification/check_jenny_audit.py`. It uses pandas and the repository's analysis module; the command above uses the existing Module 9 environment. The script deliberately reports the known feature mismatch rather than describing the whole run as a pass.

## My contribution

- What I personally checked and concluded: My audit covers the distinction between missing instructions and missing physical parts, along with the distinct-parent counting formula. The AI-assisted checks show one ambiguous concern classification and matching parent counts for the tested scopes. I keep these findings limited to the analysis code; they do not establish that the dashboard displays or filters the results correctly.
- How AI helped, if used: I used Codex to inspect the code and build specification, write the reproducible verification script, and help organize my audit. The script compares production results with an independent calculation from the raw JSONL. 