"""Validated inputs and inspectable screening rules for Appliance Listing Review."""
from __future__ import annotations

import html
import json
import re
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

FIELDS = {'rating', 'title', 'text', 'images', 'asin', 'parent_asin', 'user_id',
          'timestamp', 'helpful_vote', 'verified_purchase'}
CONCERNS = [
    dict(id='installation', label='Installation', pattern=r'\b(?:install\w*|hook[ -]?up|connect(?:ion|ing)?)\b', attribute='Installation guidance', terms=r'install|hook.?up|connect', fields=['features', 'description', 'details']),
    dict(id='dimensions', label='Size / dimensions', pattern=r'\b(?:size|dimensions?|fit|fits|fitting|small|large|inches|width|height|depth)\b', attribute='Dimensions / fit', terms=r'dimension|width|height|depth|\binch|\bcm\b|\bmm\b|\bsize\b', fields=['features', 'description', 'details']),
    dict(id='compatibility', label='Compatibility', pattern=r'\b(?:compatible|compatibility|incompatible|model|replacement)\b', attribute='Compatibility / model', terms=r'compatib|\bmodel|replacement|works? with', fields=['features', 'description', 'details']),
    dict(id='noise', label='Noise', pattern=r'\b(?:noise|noisy|loud|rattl\w*|decibels?)\b', attribute='Noise level', terms=r'noise|quiet|decibel|\bdb\b|sound', fields=['features', 'description', 'details']),
    dict(id='parts', label='Missing parts', pattern=r'\b(?:missing|parts? not included|without (?:a |the )?(?:screw|hose|adapter))\b', attribute='Included parts', terms=r'included|in the box|package contents|comes with', fields=['features', 'description', 'details']),
    dict(id='instructions', label='Instructions', pattern=r'\b(?:instructions?|manual|directions)\b', attribute='Instructions / manual', terms=r'instruction|manual|directions|user guide', fields=['features', 'description', 'details']),
    dict(id='durability', label='Durability', pattern=r'\b(?:broke|broken|break|failed|stopped working|durability|lasted)\b', attribute='Care / warranty', terms=r'warranty|care|maintenance|durab|service life', fields=['features', 'description', 'details']),
]


def clean_text(value):
    """Mirror Jamie's documented transformation for provenance validation only."""
    value = re.sub(r'<br\s*/?>', ' ', value, flags=re.IGNORECASE)
    return ' '.join(html.unescape(value).split())


def _error(path, line, field, message):
    raise ValueError(f'{path}: line {line}, field {field}: {message}')


def _read(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            _error(path, n, '<JSON>', str(e))
        if not isinstance(row, dict):
            _error(path, n, '<record>', 'expected an object')
        rows.append((n, row))
    if not rows:
        _error(path, 1, '<record>', 'file contains no records')
    return rows


def _whole(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and float(value).is_integer()


def validate_records(path, cleaned=False):
    rows = _read(path)
    for n, row in rows:
        for field in FIELDS | ({'original_row_number'} if cleaned else set()):
            if field not in row:
                _error(path, n, field, 'required field is missing')
        for f in ('title', 'text'):
            if not isinstance(row[f], str):
                _error(path, n, f, 'expected a string')
        for f in ('asin', 'parent_asin', 'user_id'):
            if not isinstance(row[f], str) or not row[f].strip():
                _error(path, n, f, 'expected a non-empty string')
        if not _whole(row['rating']) or not 1 <= row['rating'] <= 5:
            _error(path, n, 'rating', 'expected a whole number from 1 to 5')
        if not _whole(row['helpful_vote']) or row['helpful_vote'] < 0:
            _error(path, n, 'helpful_vote', 'expected a nonnegative whole number')
        if not isinstance(row['images'], list):
            _error(path, n, 'images', 'expected a list')
        if not isinstance(row['verified_purchase'], bool):
            _error(path, n, 'verified_purchase', 'expected a boolean')
        try:
            if cleaned:
                if not isinstance(row['timestamp'], str):
                    raise ValueError('expected an ISO date-time string')
                dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            else:
                if not isinstance(row['timestamp'], (int, float)) or isinstance(row['timestamp'], bool):
                    raise ValueError('expected epoch milliseconds')
                dt = datetime.fromtimestamp(row['timestamp'] / 1000, timezone.utc)
            if pd.isna(dt):
                raise ValueError('invalid date')
        except (ValueError, TypeError, OverflowError, OSError) as e:
            _error(path, n, 'timestamp', str(e))
        if cleaned and (not _whole(row['original_row_number']) or row['original_row_number'] < 1):
            _error(path, n, 'original_row_number', 'expected a positive whole number')
    fingerprints = Counter(json.dumps({k: v for k, v in r.items() if k != 'original_row_number'}, sort_keys=True) for _, r in rows)
    duplicates = sum(c - 1 for c in fingerprints.values() if c > 1)
    if duplicates:
        warnings.warn(f'{path}: {duplicates} exact duplicate records flagged for review; all retained')
    return rows


def load_reviews(cleaned_path, raw_path, qa_path=None):
    raw = dict(validate_records(raw_path))
    cleaned = validate_records(cleaned_path, True)
    if len(raw) != len(cleaned):
        _error(cleaned_path, 1, '<row count>', f'{len(cleaned)} cleaned rows versus {len(raw)} source rows')
    seen = set()
    for line, row in cleaned:
        source_id = row['original_row_number']
        if source_id in seen or source_id not in raw:
            _error(cleaned_path, line, 'original_row_number', 'duplicate or not a source line')
        seen.add(source_id)
        original = raw[source_id]
        for field in FIELDS:
            expected = original[field]
            actual = row[field]
            if field in ('title', 'text'):
                expected = clean_text(expected)
            elif field == 'timestamp':
                expected = pd.to_datetime(expected, unit='ms', utc=True)
                actual = pd.to_datetime(actual, utc=True)
            if actual != expected:
                _error(cleaned_path, line, field, f'does not reconcile to source line {source_id}')
    if qa_path and Path(qa_path).exists():
        lookup = {r['original_row_number']: r for _, r in cleaned}
        for line, row in validate_records(qa_path, True):
            if lookup.get(row['original_row_number']) != row:
                _error(qa_path, line, 'original_row_number', 'QA row does not match full cleaned input')
    frame = pd.DataFrame([r for _, r in cleaned])
    frame['date'] = pd.to_datetime(frame['timestamp'], utc=True)
    frame['rating'] = frame['rating'].astype(int)
    return frame


def load_metadata(path):
    """Explicit JSONL path plus adjacent .mapping.json describing source fields."""
    path = Path(path)
    mapping_path = path.with_suffix(path.suffix + '.mapping.json')
    if not mapping_path.exists():
        _error(mapping_path, 1, '<mapping>', 'required sidecar: source, extraction_date, fields')
    try:
        mapping = json.loads(mapping_path.read_text())
    except json.JSONDecodeError as e:
        _error(mapping_path, e.lineno, '<JSON>', str(e))
    if not isinstance(mapping, dict):
        _error(mapping_path, 1, '<mapping>', 'expected an object')
    if not isinstance(mapping.get('source'), str) or not mapping['source'].strip():
        _error(mapping_path, 1, 'source', 'document the metadata source')
    if 'extraction_date' not in mapping:
        _error(mapping_path, 1, 'extraction_date', 'supply date or null if unknown')
    fields = mapping.get('fields', {})
    normalized = ['parent_asin', 'product_title', 'product_type', 'features', 'description', 'details']
    if not isinstance(fields, dict):
        _error(mapping_path, 1, 'fields', 'expected field mapping object')
    for field in normalized:
        if field not in fields or (fields[field] is not None and (not isinstance(fields[field], str) or not fields[field])):
            _error(mapping_path, 1, field, 'map to a source key or null for unavailable')
    if fields['parent_asin'] is None:
        _error(mapping_path, 1, 'parent_asin', 'join key must be mapped')
    records, seen = [], set()
    for line, original in _read(path):
        row = {}
        for field, key in fields.items():
            if key is not None and key not in original:
                _error(path, line, key, 'mapped source field missing; use null value for empty fields')
            value = original.get(key) if key is not None else None
            if field == 'parent_asin':
                if not isinstance(value, str) or not value.strip() or value != value.strip():
                    _error(path, line, field, 'expected a nonblank key without surrounding whitespace')
            elif value is not None:
                ok = isinstance(value, dict) if field == 'details' else (
                    isinstance(value, str) or (field in ('features', 'description') and isinstance(value, list) and all(isinstance(v, str) for v in value)))
                if not ok:
                    _error(path, line, field, 'incompatible field type')
            row[field] = value
        if row['parent_asin'] in seen:
            _error(path, line, 'parent_asin', 'duplicate key; resolve variant conflicts before loading')
        seen.add(row['parent_asin'])
        row['source_line'] = line
        records.append(row)
    return dict(records=records, available={k: fields[k] is not None for k in normalized},
                source=mapping['source'], extraction_date=mapping['extraction_date'], path=str(path), mapping=fields)


def join_reviews_metadata(reviews, metadata):
    if metadata is None:
        return reviews.assign(metadata_matched=False)
    joined = reviews.merge(pd.DataFrame(metadata['records']), on='parent_asin', how='left', validate='many_to_one', indicator=True)
    joined['metadata_matched'] = joined['_merge'].eq('both')
    assert len(joined) == len(reviews) and joined.original_row_number.tolist() == reviews.original_row_number.tolist()
    return joined.drop(columns='_merge')


def tag_concerns(reviews):
    """Lowercase word/phrase regex; negated phrases excluded; one tag per review/category."""
    result = {}
    for row in reviews.to_dict('records'):
        tags = []
        if row['rating'] <= 2:
            text = (row['title'] + ' ' + row['text']).lower()
            for rule in CONCERNS:
                evidence = []
                for match in re.finditer(rule['pattern'], text):
                    before = text[max(0, match.start()-28):match.start()]
                    after = text[match.end():match.end()+18]
                    if re.search(r'\b(?:no|not|never|without)\s+(?:(?:too|very|any|a|the)\s+)?$', before):
                        continue
                    if re.match(r'\s+(?:is |was |are |were )?not\b', after):
                        continue
                    evidence.append(text[max(0, match.start()-55):match.end()+90])
                if evidence:
                    tags.append(dict(id=rule['id'], excerpts=evidence))
        result[int(row['original_row_number'])] = tags
    return result


def _content(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ' '.join(_content(v) for v in value)
    if isinstance(value, dict):
        return ' '.join(f'{k}: {_content(v)}' for k, v in value.items() if _content(v))
    return str(value)


def assess_metadata(metadata):
    if metadata is None:
        return {}
    result = {}
    for record in metadata['records']:
        assessments = {}
        for concern in CONCERNS:
            excerpts = [{'field': f, 'text': _content(record[f])} for f in concern['fields']
                        if metadata['available'][f] and re.search(concern['terms'], _content(record[f]), re.I)]
            status = ('Manual review needed' if not all(metadata['available'][f] for f in concern['fields']) else
                      'Available evidence' if excerpts else 'Potential information gap')
            assessments[concern['id']] = dict(status=status, attribute=concern['attribute'],
                                             searched=[f for f in concern['fields'] if metadata['available'][f]], excerpts=excerpts)
        result[record['parent_asin']] = dict(concerns=assessments,
            populated={f: bool(_content(record[f])) for f in ('product_title', 'features', 'description', 'details')})
    return result


def summarize_scope(reviews, tags, metadata=None, assessments=None):
    parents = sorted(set(reviews.parent_asin))
    low = reviews[reviews.rating.le(2)]
    lookup = {r['parent_asin']: r for r in metadata['records']} if metadata else {}
    matched = [p for p in parents if p in lookup]
    return dict(reviews=len(reviews), low=len(low), parents=len(parents), matched=len(matched),
        low_share=len(low)/len(reviews) if len(reviews) else None,
        metadata_share=len(matched)/len(parents) if metadata and parents else None,
        concerns={c['id']: sum(any(t['id'] == c['id'] for t in tags[int(i)]) for i in low.original_row_number) for c in CONCERNS},
        ratings=[int(reviews.rating.le(2).sum()), int(reviews.rating.eq(3).sum()), int(reviews.rating.ge(4).sum())],
        coverage={f: (None if not metadata or not metadata['available'][f] or not matched else
                      sum(assessments[p]['populated'][f] for p in matched)/len(matched))
                  for f in ('product_title', 'features', 'description', 'details')})


def rank_listings(reviews, tags, metadata=None, assessments=None):
    lookup = {r['parent_asin']: r for r in metadata['records']} if metadata else {}
    result = []
    for parent, group in reviews.groupby('parent_asin'):
        row = dict(parent_asin=parent, total=len(group), low=int(group.rating.le(2).sum()),
                   gap_count=None, attributes=[], priority='Not assessable')
        if parent in lookup:
            relevant = {t['id'] for i in group.original_row_number for t in tags[int(i)]}
            assessed = assessments[parent]['concerns']
            gaps = {c for c in relevant if assessed[c]['status'] == 'Potential information gap'}
            incomplete = any(assessed[c]['status'] == 'Manual review needed' for c in relevant)
            count = sum(any(t['id'] in gaps for t in tags[int(i)]) for i in group.original_row_number)
            possible = all(metadata['available'][f] for f in ('features', 'description', 'details')) or any(assessed[c]['status'] != 'Manual review needed' for c in relevant)
            row.update(gap_count=count if possible else None, attributes=sorted(assessed[c]['attribute'] for c in gaps), incomplete=incomplete,
                       priority=('High' if count >= 3 else 'Medium' if count == 2 else 'Low' if count == 1 else
                                 'Not assessable' if incomplete or not possible else 'No gap signal under these rules'))
        result.append(row)
    order = {'High': 0, 'Medium': 1, 'Low': 2, 'No gap signal under these rules': 3, 'Not assessable': 4}
    return sorted(result, key=(lambda r: (order[r['priority']], -(r['gap_count'] if r['gap_count'] is not None else -1), -len(r['attributes']), r['parent_asin'])) if metadata else
                  (lambda r: (-r['low'], -r['total'], r['parent_asin'])))


def get_listing_evidence(parent, reviews, tags, metadata=None, concern=None):
    selected = reviews[reviews.parent_asin.eq(parent)]
    evidence = selected if not concern else selected[selected.original_row_number.map(lambda i: any(t['id'] == concern for t in tags[int(i)]))]
    safe_fields = ['original_row_number', 'rating', 'title', 'text', 'timestamp', 'helpful_vote', 'verified_purchase', 'asin', 'parent_asin']
    return dict(total=len(selected), low=int(selected.rating.le(2).sum()),
                average=float(selected.rating.mean()) if len(selected) else None,
                verified=int(selected.verified_purchase.sum()), reviews=evidence[safe_fields].to_dict('records'),
                listing=next((r for r in metadata['records'] if r['parent_asin'] == parent), None) if metadata else None)
