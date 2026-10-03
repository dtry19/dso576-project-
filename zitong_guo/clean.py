"""Deterministic review cleaning and verification; Python standard library only."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import html
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def missing(v):
    return v is None or (isinstance(v, str) and not v.strip())

def text_clean(v):
    if missing(v) or not isinstance(v, str):
        return None
    return ' '.join(html.unescape(re.sub(r'<br\s*/?>', ' ', v, flags=re.I)).split()) or None

def integer(v, lo, hi=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if not float(v).is_integer() or v < lo or (hi is not None and v > hi):
        return None
    return int(v)

def dates(v):
    if type(v) is not int:
        return None
    try:
        return (EPOCH + timedelta(milliseconds=v)).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    except (OverflowError, ValueError):
        return None

def metrics(rows, raw=False):
    rk, vk = ('rating', 'helpful_vote') if raw else ('rating_clean', 'helpful_vote_clean')
    ratings = [integer(r.get(rk), 1, 5) for r in rows]
    ratings = [v for v in ratings if v is not None]
    votes = [integer(r.get(vk), 0) for r in rows]
    votes = [v for v in votes if v is not None]
    low = sum(v <= 2 for v in ratings)
    return dict(rows=len(rows), rating_n=len(ratings), rating_sum=sum(ratings),
                mean_rating=sum(ratings)/len(ratings) if ratings else None,
                low_rating_n=low, low_rating_share=low/len(ratings) if ratings else None,
                helpful_vote_n=len(votes), helpful_vote_sum=sum(votes))

def run(source, out):
    out.mkdir(parents=True, exist_ok=True)
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    # Malformed JSON is a hard error, never silently discarded.
    original = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    cleaned, excluded, seen = [], [], set()
    for index, raw in enumerate(original, 1):
        signature = json.dumps(raw, sort_keys=True, ensure_ascii=False)
        if signature in seen:
            excluded.append(dict(source_row=index, reason='exact duplicate'))
            continue
        seen.add(signature)
        r = dict(raw, source_row=index)
        r.update(rating_clean=integer(raw.get('rating'), 1, 5),
                 title_clean=text_clean(raw.get('title')), text_clean=text_clean(raw.get('text')),
                 timestamp_utc=dates(raw.get('timestamp')),
                 helpful_vote_clean=integer(raw.get('helpful_vote'), 0),
                 verified_purchase_clean=raw.get('verified_purchase') if type(raw.get('verified_purchase')) is bool else None)
        flags = []
        for k in ['rating_clean', 'timestamp_utc', 'helpful_vote_clean', 'verified_purchase_clean', 'title_clean', 'text_clean']:
            if r[k] is None:
                flags.append('missing_or_invalid_' + k)
        for k in ['asin', 'parent_asin']:
            if not isinstance(r.get(k), str) or not re.fullmatch(r'[A-Z0-9]{10}', r[k]):
                flags.append('missing_or_invalid_' + k)
        if missing(r.get('user_id')):
            flags.append('missing_user_id')
        if r['timestamp_utc'] and not ('1996-05-01' <= r['timestamp_utc'] < '2023-10-01'):
            flags.append('outside_dataset_date_window')
        r['quality_flags'] = flags
        cleaned.append(r)
    keys = sorted(set().union(*(r.keys() for r in original)))
    repeated = {}
    for k in ['asin', 'parent_asin', 'user_id']:
        c = Counter(r.get(k) for r in original)
        repeated[k] = dict(distinct=len(c), repeated_keys=sum(v > 1 for v in c.values()), excess_rows=sum(v-1 for v in c.values()))
    cc = Counter((r.get('user_id'), r.get('asin'), r.get('timestamp')) for r in original)
    by_source = {r['source_row']: r for r in cleaned}
    checks = []
    for case in json.loads((HERE/'expected_checks.json').read_text()):
        row = by_source.get(case['source_row'])
        actual = row.get(case['field']) if row else None
        checks.append(dict(case, original=original[case['source_row']-1].get(case['original_field']),
                           actual=actual, passed=row is not None and actual == case['expected']))
    assert all(c['passed'] for c in checks), 'Record check failure'
    assert len(original) == len(cleaned)+len(excluded)
    assert all(all(r[k] == original[r['source_row']-1][k] for k in keys) for r in cleaned)
    assert all(round((datetime.fromisoformat(r['timestamp_utc'].replace('Z', '+00:00'))-EPOCH).total_seconds()*1000)==r['timestamp'] for r in cleaned if r['timestamp_utc'])
    groups = defaultdict(list)
    for r in cleaned:
        groups[None if missing(r.get('parent_asin')) else r['parent_asin']].append(r)
    grouped = [dict(parent_asin=k, **metrics(v)) for k,v in sorted(groups.items(), key=lambda pair: pair[0] or '')]
    assert sum(g['rows'] for g in grouped) == len(cleaned)
    assert sum(g['rating_sum'] for g in grouped) == metrics(cleaned)['rating_sum']
    assert sum(g['helpful_vote_sum'] for g in grouped) == metrics(cleaned)['helpful_vote_sum']
    after_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before_hash == after_hash
    changed = {k:sum(r[k] != r[k+'_clean'] for r in cleaned) for k in ['title','text']}
    type_counts = {k:dict(Counter(type(r.get(k)).__name__ for r in original)) for k in keys}
    sample_ids = [c['source_row'] for c in checks]
    for r in cleaned:
        if r['source_row'] not in sample_ids and len(sample_ids)<50:
            sample_ids.append(r['source_row'])
    sample = [by_source[n] for n in sorted(sample_ids)]
    audit = dict(source_file='dataset/Appliances_sample.jsonl', sha256=before_hash,
                 source_unchanged=before_hash==after_hash, source_types=type_counts,
                 source_rows=len(original), cleaned_rows=len(cleaned), exact_duplicates_removed=len(excluded),
                 repeated_ids=repeated, composite_key_excess_rows=sum(v-1 for v in cc.values()),
                 missing_before={k:sum(missing(r.get(k)) for r in original) for k in keys},
                 missing_after={k:sum(missing(r.get(k)) for r in cleaned) for k in sorted(cleaned[0]) if k not in ['source_row','quality_flags']},
                 conversion_failures={k:sum(r[k] is None for r in cleaned) for k in ['rating_clean','timestamp_utc','helpful_vote_clean','verified_purchase_clean']},
                 changed_text=changed, flags=dict(Counter(f for r in cleaned for f in r['quality_flags'])),
                 rating_distribution=dict(sorted(Counter(r['rating_clean'] for r in cleaned).items())),
                 before=metrics(original,True), after=metrics(cleaned),
                 first_utc=min(r['timestamp_utc'] for r in cleaned if r['timestamp_utc']),
                 last_utc=max(r['timestamp_utc'] for r in cleaned if r['timestamp_utc']),
                 variant_rows=sum(r['asin']!=r['parent_asin'] for r in cleaned),
                 unverified_rows=sum(r['verified_purchase_clean'] is False for r in cleaned),
                 empty_images=sum(r['images']==[] for r in cleaned),
                 max_helpful_votes=max(r['helpful_vote_clean'] for r in cleaned),
                 join_status='Unresolved: no metadata supplied; no merge performed',
                 sample_selection='Five prespecified checked rows plus earliest remaining source rows until 50. Purposive audit sample, not random.',
                 sample_source_rows=sorted(sample_ids), assertions_passed=True)
    for name, rows in [('cleaned_reviews.jsonl',cleaned),('cleaned_sample_50.jsonl',sample)]:
        (out/name).write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf-8')
    for name,value in [('audit.json',audit),('record_checks.json',checks),('excluded_rows.json',excluded),('product_metrics.json',grouped)]:
        dump(out/name,value)
    print(json.dumps({'source_rows':len(original),'cleaned_rows':len(cleaned),'checks_passed':len(checks),'out':str(out)},indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, default=HERE.parent/'dataset/Appliances_sample.jsonl')
    p.add_argument('--output', type=Path, default=HERE/'output')
    args = p.parse_args()
    run(args.input, args.output)
