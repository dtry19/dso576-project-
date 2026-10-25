"""Reproduce the feature and number checks in jenny-audit.md.

From the project root: ../09-audit/.venv/bin/python verification/check_jenny_audit.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from appliance_analysis import load_reviews, summarize_scope, tag_concerns


def main():
    # Synthetic cases isolate screening behavior; these are not customer quotations.
    cases = pd.DataFrame([
        dict(original_row_number=1, rating=1, title='', text='Missing instructions.'),
        dict(original_row_number=2, rating=1, title='', text='Missing hose.'),
        dict(original_row_number=3, rating=5, title='', text='Missing hose.'),
        dict(original_row_number=4, rating=1, title='', text='No missing parts.'),
    ])
    expected = {1: {'instructions'}, 2: {'parts'}, 3: set(), 4: set()}
    tags = tag_concerns(cases)
    for row_id, wanted in expected.items():
        actual = {t['id'] for t in tags[row_id]}
        print(f'FEATURE row {row_id}: expected={sorted(wanted)}, actual={sorted(actual)}, matches={actual == wanted}')
    assert {t['id'] for t in tags[1]} == {'instructions', 'parts'}, 'Recheck documented finding if behavior changes'
    for row_id in (2, 3, 4):
        assert {t['id'] for t in tags[row_id]} == expected[row_id]

    small = pd.DataFrame(dict(parent_asin=['A', 'A', 'B', 'C', 'C'], rating=[1, 2, 3, 4, 5], original_row_number=range(1, 6)))
    empty_tags = {i: [] for i in range(1, 6)}
    for name, frame, wanted in [('Repeated parents', small, 3), ('Only A', small[small.parent_asin.eq('A')], 1), ('Empty', small.iloc[:0], 0)]:
        actual = summarize_scope(frame, empty_tags)['parents']
        assert actual == wanted
        print(f'NUMBER {name}: expected={wanted}, actual={actual}')

    raw = [json.loads(line) for line in (ROOT / 'dataset/Appliances_sample.jsonl').read_text().splitlines() if line.strip()]
    reviews = load_reviews(ROOT / 'output/Appliances_cleaned.jsonl', ROOT / 'dataset/Appliances_sample.jsonl')
    scopes = [('All reviews', raw, reviews), ('Not verified and 1–2 stars', [r for r in raw if not r['verified_purchase'] and r['rating'] in (1, 2)], reviews[~reviews.verified_purchase & reviews.rating.le(2)])]
    for name, independent, frame in scopes:
        wanted = len({r['parent_asin'] for r in independent})
        actual = summarize_scope(frame, tag_concerns(frame))['parents']
        assert actual == wanted
        print(f'NUMBER {name}: reviews={len(independent)}, independent parents={wanted}, production parents={actual}')


if __name__ == '__main__':
    main()
