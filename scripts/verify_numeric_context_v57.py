"""Independently replay text/cue/span accounting; do not ratify semantic judgments."""
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_cohort_scope_v52 import reconstruct as scope_replay


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def cues(text, span, limit, horizon):
    start, end = span; stop = min(limit, end + horizon)
    markers = sorted(['km', 'km³', 'km3', 'km^3', 'm', 'MHz', 'GHz', 'Hz', 'GeV', 'PeV', 'EeV', '°', '%'], key=lambda s: (-len(s), s))
    def skip(i):
        while i < stop and text[i].isspace(): i += 1
        return i
    def unit(i):
        i = skip(i)
        for marker in markers:
            last = i + len(marker)
            if last <= stop and text[i:last] == marker and (last == stop or not re.match(r'\w', text[last])):
                return {'span': [i, last], 'text': marker}
        return None
    direct = unit(end); at = skip(end); interval = None
    if at < stop and text[at] in '-–−':
        at = skip(at + 1); match = re.match(r'[0123456789]+(?:[.,][0123456789]+)*', text[at:stop])
        if match:
            last = at + len(match.group()); marker = unit(last); finish = marker['span'][1] if marker else last
            interval = {'span': [start, finish], 'text': text[start:finish], 'endpoint_span': [at, last], 'endpoint_value': match.group(), 'unit': marker}
    return {'direct_unit_marker': direct, 'numeric_range_surface': interval}


def reconstruct(text, side, keys, units, masks, inventory, radius, horizon):
    frozen = {(tuple(r['span']), r['key']): r for r in inventory if r['kind'] == 'number' and r['key'] in keys}
    rows = []; admitted_ids = set()
    for match in re.finditer(r'[0123456789]+(?:[.,][0123456789]+)*', text):
        key = 'number:' + match.group()
        if key not in keys: continue
        a, b = match.span(); containing = [u for u in units if u['span'] and u['span'][0] <= a < b <= u['span'][1]]
        overlapping = [m for m in masks if m['span'][0] < b and m['span'][1] > a]
        before = text[a - 1] if a else ''; after = text[b] if b < len(text) else ''
        bad = bool(re.match(r'\w', before) or re.match(r'\w', after) or before in ('.', ','))
        expected_anchor = frozen.get(((a, b), key)); retained = len(containing) == 1 and not overlapping and not bad
        assert retained == (expected_anchor is not None)
        if retained: admitted_ids.add(((a, b), key))
        status = 'retained' if retained else 'boundary_rejected' if bad else 'masked' if overlapping else 'outside_selected_scope'
        context = [max(0, a - radius), min(len(text), b + radius)]
        clipped = [max(context[0], containing[0]['span'][0]), min(context[1], containing[0]['span'][1])] if len(containing) == 1 else None
        rows.append({'occurrence_id': f'{side}:{len(rows):03d}', 'side': side, 'key': key, 'value': match.group(), 'span': [a, b],
            'status': status, 'boundary_rejected': bad, 'containing_unit_ids': [u['unit'] for u in containing],
            'mask_overlaps': overlapping, 'frozen_anchor_index': expected_anchor['anchor_index'] if expected_anchor else None,
            'context_span': context, 'context_text': text[slice(*context)], 'unit_clipped_context_span': clipped,
            'unit_clipped_context_text': text[slice(*clipped)] if clipped else None,
            'literal_cues': cues(text, [a, b], containing[0]['span'][1] if len(containing) == 1 else len(text), horizon),
            'glyphs_visually_verified': False, 'quantity_correspondence': 'unresolved', 'opaque_meaning_admitted': False})
    assert admitted_ids == set(frozen)
    return rows


def summarize(rows, reviews, texts):
    expected = {r['occurrence_id']: r for r in rows}
    assert len(expected) == len(rows) == len(reviews) and set(expected) == {r['occurrence_id'] for r in reviews}
    for review in reviews:
        row = expected[review['occurrence_id']]
        assert review['glyph_status'] == 'not_visually_checked' and review['quantity_correspondence'] == 'unresolved' and review['opaque_meaning_admitted'] is False
        allowed = {'discrete_count', 'distance_or_length', 'volume', 'angle_or_phase', 'calendar_or_campaign_date', 'other_or_unresolved'} if row['side'] == 'source' else {'opaque_context_unresolved'} if row['status'] == 'retained' else {'declared_excluded_context'}
        assert review['context_class'] in allowed and review['note'].strip() and review['evidence']
        for evidence in review['evidence']:
            a, b = evidence['span']; assert row['context_span'][0] <= a < b <= row['context_span'][1]
            assert texts[row['side']][a:b] == evidence['text']
    by_side = {}
    for side in ['target', 'source']:
        subset = [r for r in rows if r['side'] == side]; ids = {r['occurrence_id'] for r in subset}
        by_side[side] = {'occurrences': len(subset), 'status_counts': dict(sorted(Counter(r['status'] for r in subset).items())),
                       'context_class_counts': dict(sorted(Counter(r['context_class'] for r in reviews if r['occurrence_id'] in ids).items()))}
    by_key = []
    for key in dict.fromkeys(r['key'] for r in rows):
        info = {'key': key}
        for side in ['target', 'source']:
            subset = [r for r in rows if r['key'] == key and r['side'] == side]; markers = set()
            for row in subset:
                cue = row['literal_cues']
                for marker in [cue['direct_unit_marker'], cue['numeric_range_surface']['unit'] if cue['numeric_range_surface'] else None]:
                    if marker: markers.add(marker['text'])
            info[side] = {'all_occurrence_ids': [r['occurrence_id'] for r in subset],
                         'retained_occurrence_ids': [r['occurrence_id'] for r in subset if r['status'] == 'retained'], 'literal_unit_markers': sorted(markers)}
        by_key.append(info)
    return {'occurrence_denominator': len(rows), 'retained_occurrences': sum(r['status'] == 'retained' for r in rows),
        'supplementary_occurrences': sum(r['status'] != 'retained' for r in rows), 'by_side': by_side, 'by_key': by_key,
        'review_coverage_complete': True, 'visual_glyph_agreement_gate': None, 'quantity_correspondence_gate': None,
        'opaque_meanings_admitted': 0, 'source_target_pairs_selected': 0}


def main():
    run = ROOT / 'runs/000057_numeric_context'; check_hashes(run)
    cfg = read('experiments/numeric_context_v57.json'); pre = read('data/v57/preflight.json')
    manifest = read('runs/000057_numeric_context/manifest.json'); report = read('runs/000057_numeric_context/report.json')
    selection = read('data/v57/selection.json'); ledger = read('data/v57/review_ledger.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/numeric_context_v57.json'] == sha('experiments/numeric_context_v57.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < selection['selected_at_utc'] < ledger['reviewed_at_utc'] < manifest['finished_at_utc']
    assert cfg['network_request_budget'] == 0 and cfg['context_radius'] == 120 and cfg['cue_horizon'] == 64
    export = read('data/v38/target_export.json'); raw = (ROOT / cfg['target_raw']).read_bytes(); receipt = read(cfg['target_receipt']); gate = read('data/v38/dated_material_gate.json')
    assert gate['passed'] and receipt['transport_complete'] and export['parent_sha256'] == sha(cfg['target_raw']) == receipt['artifacts']['body.bin']['sha256']
    assert len(raw) == receipt['artifacts']['body.bin']['bytes']
    assert base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=') == gate['cdx_digest']
    assert export['representation'] == 'dated_archival_post_body_export' and export['raw_post'] is True
    assert cfg['capture_timestamp'] == export['capture_timestamp'] == gate['selection']['record']['timestamp'] == '20260110222100'
    soup = BeautifulSoup(raw, 'html.parser'); bodies = soup.find_all('div', class_='post-body'); assert len(bodies) == 1
    for tag in bodies[0].find_all(['script', 'style', 'noscript']): tag.decompose()
    assert bodies[0].get_text(' ', strip=True) == export['text']
    saved = read(cfg['source_scope']); source_receipt = read(cfg['source_receipt']); source_raw = (ROOT / cfg['source_raw']).read_bytes()
    assert source_receipt['transport_complete'] and sha(cfg['source_raw']) == source_receipt['artifacts']['body.bin']['sha256']
    assert len(source_raw) == source_receipt['artifacts']['body.bin']['bytes']
    replayed, checks = scope_replay(source_raw, saved['body_text'], cfg['source_selector']); assert replayed == saved and all(checks.values())
    texts = {'target': export['text'], 'source': saved['body_text']}
    target = read('data/v56/target.json'); source = read('data/v56/reference_v42_representation.json')
    target_keys = {r['key'] for r in target['inventory']['anchors'] if r['kind'] == 'number'}
    keys = list(dict.fromkeys(r['key'] for r in source['inventory']['anchors'] if r['kind'] == 'number' and r['key'] in target_keys))
    assert keys == cfg['shared_keys'] == selection['shared_keys'] and len(keys) == report['shared_numeric_key_types'] == 6
    rows = []
    for side, units, masks, inv in [('target', target['units'], target['mask_ledger'], target['inventory']['anchors']),
                                   ('source', source['units'], source['quote_mask_ledger'], source['inventory']['anchors'])]:
        subset = reconstruct(texts[side], side, keys, units, masks, inv, 120, 64); rows.extend(subset)
        assert sum(r['status'] == 'retained' for r in subset) == cfg['expected_retained'][side]
        assert cfg['expected_retained'][side] == sum(r['kind'] == 'number' and r['key'] in keys for r in inv)
    assert selection['occurrences'] == rows
    assert selection['text_sha256'] == {s: hashlib.sha256(t.encode()).hexdigest() for s, t in texts.items()}
    for k in ['target_archival_parent_verified', 'source_native_body_verified']: assert selection[k] is True and report[k] is True
    assert selection['glyphs_visually_verified'] is report['glyphs_visually_verified'] is False
    assert selection['historical_2018_bytes_authenticated'] is report['historical_2018_bytes_authenticated'] is False
    assert selection['target_capture_timestamp'] == report['target_archival_capture_timestamp'] == cfg['capture_timestamp']
    assert ledger['selection_sha256'] == sha('data/v57/selection.json') and ledger['reviewer'] == 'same_agent_text_context_review' and ledger['independent_review'] is False
    summary = summarize(rows, ledger['reviews'], texts)
    for k, v in summary.items(): assert report[k] == v
    assert report['context_judgments_independently_verified'] is report['natural_benchmark_capacity_met'] is False
    for k in ['network_requests', 'new_renders', 'new_structural_scores', 'opaque_lexical_or_semantic_scores', 'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    # Context-class evidence is validated for traceability, not independently interpreted here.
    previous = []
    for p in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if p.parent != run: check_hashes(p.parent); previous.append(p.parent.name)
    assert len(previous) == 56
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000057_numeric_context/manifest.json'),
        'all_occurrences_contexts_and_literal_cues_reconstructed': True, 'occurrences_verified': len(rows),
        'retained_occurrences': summary['retained_occurrences'], 'supplementary_occurrences': summary['supplementary_occurrences'],
        'target_archival_parent_and_source_body_reproduced': True, 'review_coverage_and_exact_evidence_verified': True,
        'production_occurrence_cue_and_summary_functions_not_used': True, 'source_context_labels_independently_verified': False,
        'glyphs_visually_verified': False, 'quantity_correspondence_validated': False,
        'shared_html_parser': 'BeautifulSoup html.parser', 'verification_network_requests': 0,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000057_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(previous)}, indent=2))


if __name__ == '__main__': main()
