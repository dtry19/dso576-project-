# Module 9 audit claims and change requests

## Claims

- Jenny Guo — I audit low-rated concern tagging, distinguishing missing instructions from missing physical parts. I also audit the distinct reviewed parent-ASIN count. Scope: analysis code at `a1b411b06ca50df55ec6f2f31055d736760aaa0f` (full commit recorded in `jenny-audit.md`); browser behavior is untested.

- Jamie Sun — I audit whether the review-date filter limits the dashboard to reviews from the selected year and updates the review count consistently. I also audit the filtered review count by independently counting matching rows in the full cleaned review sample.

## CR-JG-01: Clarify and narrow the Missing parts rule

- Status: Proposed. I recommend treating instructions and physical parts as separate categories for this check.
- Evidence: Run `../09-audit/.venv/bin/python verification/check_jenny_audit.py` from the project root. A synthetic 1-star review saying “Missing instructions.” receives both `parts` and `instructions` tags. The Missing parts regex matches the word `missing` alone.
- Effect: If Missing parts means physical components, the extra tag has no physical-component evidence and may inflate that concern's count.
- Requested change: Agree whether manuals are physical parts for this taxonomy. If separate, require a missing-component phrase or component noun, preserve legitimate category overlap, and retain the fixture as a check.
- Acceptance: Under the separate-category definition, “Missing instructions.” supports Instructions only; “Missing hose.” supports Missing parts; 5-star reviews remain untagged and “No missing parts.” remains excluded. Check additional real examples before claiming improved overall accuracy.

## CR-JG-02: Verify the reviewed-parent card when the UI is available

- Status: Follow-up verification; no backend formula defect found.
- Evidence: The independent raw-data calculation and production summary both return 829 parents for 1,000 reviews and 15 parents for the 15 unverified, low-rated reviews. Repeated-parent and empty fixtures return the expected counts.
- Requested change: No counting formula change. Use the label “Reviewed parent ASINs” and reconcile the eventual UI card with these backend results under the same scopes.
- Limitation: This checkout has analysis code but no dashboard HTML or builder; no claim is made about rendered values or interactive filters.
