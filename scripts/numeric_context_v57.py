"""Prepare complete fixed context packet; finalize after a separate annotation ledger."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from bs4 import BeautifulSoup
from fl_decipher.cohort_scope_v52 import extract_scope
from fl_decipher.numeric_context_v57 import occurrences, summarize

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/numeric_context_v57.json'
RUN = 'runs/000057_numeric_context'
CODE = ['src/fl_decipher/numeric_context_v57.py', 'scripts/numeric_context_v57.py', 'tests/test_numeric_context_v57.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def original_texts(cfg):
    export = read('data/v38/target_export.json'); raw = (ROOT / cfg['target_raw']).read_bytes()
    receipt = read(cfg['target_receipt']); gate = read('data/v38/dated_material_gate.json')
    assert receipt['transport_complete'] and sha(cfg['target_raw']) == export['parent_sha256'] == receipt['artifacts']['body.bin']['sha256']
    assert gate['passed'] and base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=') == gate['cdx_digest']
    assert export['raw_post'] is True and export['representation'] == 'dated_archival_post_body_export'
    assert export['capture_timestamp'] == gate['selection']['record']['timestamp'] == cfg['capture_timestamp']
    soup = BeautifulSoup(raw, 'html.parser'); bodies = soup.select('div.post-body'); assert len(bodies) == 1
    for tag in bodies[0].select('script,style,noscript'): tag.decompose()
    assert bodies[0].get_text(' ', strip=True) == export['text']
    saved = read(cfg['source_scope']); source_raw = (ROOT / cfg['source_raw']).read_bytes(); source_receipt = read(cfg['source_receipt'])
    assert source_receipt['transport_complete'] and sha(cfg['source_raw']) == source_receipt['artifacts']['body.bin']['sha256']
    assert extract_scope(source_raw, saved['body_text'], cfg['source_selector']) == saved
    return {'target': export['text'], 'source': saved['body_text']}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'finalize']); args = parser.parse_args(); cfg = read(CFG)
    if args.phase == 'prepare':
        assert not (ROOT / 'data/v57').exists()
        for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
        write('data/v57/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]}})
        texts = original_texts(cfg); target = read('data/v56/target.json'); source = read('data/v56/reference_v42_representation.json')
        target_keys = {r['key'] for r in target['inventory']['anchors'] if r['kind'] == 'number'}
        keys = list(dict.fromkeys(r['key'] for r in source['inventory']['anchors'] if r['kind'] == 'number' and r['key'] in target_keys))
        assert keys == cfg['shared_keys'] and len(keys) == 6
        rows = []
        for side, units, masks, inv in [('target', target['units'], target['mask_ledger'], target['inventory']['anchors']),
                ('source', source['units'], source['quote_mask_ledger'], source['inventory']['anchors'])]:
            selected = occurrences(texts[side], side, keys, units, masks, inv, cfg['context_radius'], cfg['cue_horizon'])
            assert sum(r['status'] == 'retained' for r in selected) == cfg['expected_retained'][side]
            rows.extend(selected)
        write('data/v57/selection.json', {'selected_at_utc': utc(), 'shared_keys': keys, 'occurrences': rows,
            'text_sha256': {s: hashlib.sha256(t.encode()).hexdigest() for s, t in texts.items()},
            'target_capture_timestamp': cfg['capture_timestamp'], 'target_archival_parent_verified': True,
            'source_native_body_verified': True, 'glyphs_visually_verified': False, 'historical_2018_bytes_authenticated': False})
        print(json.dumps({'state': 'prepared', 'shared_keys': keys, 'all_occurrences': len(rows),
            'retained': sum(r['status'] == 'retained' for r in rows), 'supplementary': sum(r['status'] != 'retained' for r in rows)}, indent=2)); return
    pre = read('data/v57/preflight.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    frozen = read('data/v57/selection.json'); ledger = read('data/v57/review_ledger.json')
    assert ledger['selection_sha256'] == sha('data/v57/selection.json') and frozen['selected_at_utc'] < ledger['reviewed_at_utc']
    assert ledger['reviewer'] == 'same_agent_text_context_review' and ledger['independent_review'] is False
    texts = original_texts(cfg); summary = summarize(frozen['occurrences'], ledger['reviews'], texts)
    report = {'experiment_id': 'numeric_context_v57', 'shared_numeric_key_types': 6, **summary,
        'target_archival_capture_timestamp': cfg['capture_timestamp'], 'target_archival_parent_verified': True,
        'source_native_body_verified': True, 'historical_2018_bytes_authenticated': False,
        'context_judgments_independently_verified': False, 'glyphs_visually_verified': False,
        'network_requests': 0, 'new_renders': 0, 'new_structural_scores': 0, 'opaque_lexical_or_semantic_scores': 0,
        'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'natural_benchmark_capacity_met': False, 'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write(RUN + '/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v57').glob('*.json'))
    write(RUN + '/manifest.json', {'experiment_id': 'numeric_context_v57', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in outputs},
        'verifier_written_after_review': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
