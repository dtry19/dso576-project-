"""Run from the project root: .venv/bin/python verification/check_low_rated_share.py."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from appliance_analysis import load_reviews, summarize_scope, tag_concerns


def main():
    small = pd.DataFrame({
        'rating': [1, 2, 3, 4, 5],
        'parent_asin': ['A', 'B', 'C', 'D', 'E'],
        'original_row_number': [1, 2, 3, 4, 5],
    })
    tags = {i: [] for i in range(1, 6)}
    for name, frame, expected in [
        ('Five reviews: expected 2/5 = 40%', small, 0.4),
        ('Low-only scope: expected 2/2 = 100%', small[small.rating.le(2)], 1.0),
        ('Empty scope: expected None (N/A)', small.iloc[:0], None),
    ]:
        result = summarize_scope(frame, tags)
        assert result['low_share'] == expected, (name, result)
        print(f"PASS: {name}; actual share={result['low_share']}")

    # Independent calculation: standard-library JSON parsing and explicit
    # membership in (1, 2), without the production filtering/summary functions.
    raw_path = ROOT / 'dataset/Appliances_sample.jsonl'
    raw = [json.loads(line) for line in raw_path.read_text().splitlines()]
    assert all(type(row['rating']) in (int, float) and row['rating'] in (1, 2, 3, 4, 5) for row in raw)
    low_count = sum(row['rating'] in (1, 2) for row in raw)
    independent_share = low_count / len(raw)
    reviews = load_reviews(ROOT / 'output/Appliances_cleaned.jsonl', raw_path)
    actual = summarize_scope(reviews, tag_concerns(reviews))
    assert (actual['reviews'], actual['low'], actual['low_share']) == (len(raw), low_count, independent_share)
    print(f"PASS: independent raw count={low_count}/{len(raw)} = {independent_share:.1%}; matches production summary")


if __name__ == '__main__':
    main()
