"""Seal, acquire fixed posts/sources, then write the bounded capacity ledger."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json

from fl_decipher.source_intake_v37 import known_metadata, nominate, citation_metadata, select_sources, source_material
from fl_decipher.capture_review_v23 import request, extract_post

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/source_intake_v37.json'
RUN = 'runs/000037_source_intake'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def write(path, obj):
    target = ROOT/path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def check(hashes):
    for path, expected in hashes.items():
        assert sha(path) == expected, path


def seal():
    cfg = read(CFG)
    check(cfg['input_hashes'])
    revision = read('experiments/source_intake_v37_discovery_revision1.json')
    check(revision['input_hashes'])
    assert not (ROOT/'data/v37/acquisition').exists()
    known = known_metadata(ROOT)
    write('data/v37/known_exposure.json', known)
    discoveries = [read(f'data/v37/discovery/query{i}.json') for i in range(4)]
    assert [d['query'] for d in discoveries] == cfg['queries']
    nominations = nominate(discoveries, known['urls'])
    write('data/v37/nominations.json', nominations)
    inputs = cfg['input_hashes'] | {p: sha(p) for p in [CFG, 'experiments/source_intake_v37_discovery_revision1.json',
                *revision['input_hashes'], *known['input_files'], 'data/v37/known_exposure.json', 'data/v37/nominations.json',
                *[f'data/v37/discovery/query{i}.json' for i in range(4)]]}
    code = [*list((ROOT/'src/fl_decipher').glob('*.py')), *list((ROOT/'scripts').glob('*.py')), *list((ROOT/'tests').glob('*.py'))]
    write('data/v37/preflight.json', {'sealed_at_utc': now(), 'input_hashes': inputs,
                                     'code_hashes': {str(p.relative_to(ROOT)): sha(p) for p in sorted(code)},
                                     'raw_requests_before_seal': 0, 'search_executions': 8, 'distinct_queries': 4})
    print(json.dumps({'nominees': nominations['nominees'], 'unfilled_post_slots': sum(s['post_id'] is None for s in nominations['slots']), 'sealed': True}))


def posts():
    pre = read('data/v37/preflight.json')
    check(pre['input_hashes'])
    check(pre['code_hashes'])
    cfg, nominations = read(CFG), read('data/v37/nominations.json')
    out = ROOT/'data/v37/acquisition'
    out.mkdir(exist_ok=False)
    for n in nominations['nominees']:
        r = request(out, n['post_id'], n['url'], cfg['request_limits'], 'native')
        print(json.dumps({'post_id': n['post_id'], 'http': r['http_status'], 'curl': r['curl_returncode'], 'complete': r['transport_complete']}), flush=True)


def metadata():
    pre = read('data/v37/preflight.json')
    check(pre['input_hashes'])
    check(pre['code_hashes'])
    records = []
    for n in read('data/v37/nominations.json')['nominees']:
        receipt = read(f'data/v37/acquisition/{n["post_id"]}/receipt.json')
        if receipt['transport_complete']:
            raw = (ROOT/f'data/v37/acquisition/{n["post_id"]}/body.bin').read_bytes()
            extracted = extract_post(raw, receipt, {'fl_title': n['title'], 'fl_url': n['url']})
            meta = citation_metadata(raw.decode('utf-8', errors='replace'))
            record = {'post_id': n['post_id'], 'representation': 'raw_html', 'post_identity_gate': {k: v for k, v in extracted.items() if k != 'text'},
                      'metadata': meta, 'raw_capture_available': bool(extracted['eligible']), 'target_prose_compared': False,
                      'target_prose_displayed': False, 'search_snippet_exposure': True}
            if extracted['eligible']:
                write(f'data/v37/posts/{n["post_id"]}.json', {'url': n['url'], 'text': extracted['text'], 'text_sha256': extracted['text_sha256'],
                                                           'representation': 'visible_post_body_export', 'semantic_labels': []})
            else:
                record['metadata'] = {'links': [], 'eligible_citations': [], 'reason': 'raw_post_identity_gate_failed'}
        else:
            path = f'data/v37/fallback/{n["post_id"]}.json'
            if (ROOT/path).exists():
                fallback = read(path)
                assert fallback['url'] == n['url']
                record = {'post_id': n['post_id'], 'representation': 'indexed_browser_extraction', 'raw_capture_available': False,
                          'metadata': citation_metadata(fallback['response'], indexed=True), 'fallback_path': path,
                          'target_prose_compared': False, 'target_prose_displayed': True, 'search_snippet_exposure': True,
                          'limitation': 'Browser extraction may omit links, paragraphs or layout; not raw/current HTML or complete post proof'}
            else:
                record = {'post_id': n['post_id'], 'representation': 'unavailable', 'raw_capture_available': False,
                          'metadata': {'links': [], 'eligible_citations': [], 'reason': 'no_fallback_artifact'},
                          'target_prose_compared': False, 'search_snippet_exposure': True}
        records.append(record)
    selected = select_sources(records, read('data/v37/known_exposure.json'))
    write('data/v37/post_metadata.json', {'records': records})
    write('data/v37/source_selection.json', selected | {'frozen_at_utc': now()})
    print(json.dumps({'posts': len(records), 'selected_sources': selected['selected'], 'unfilled_source_slots': selected['unfilled_source_slots']}))


def sources():
    pre = read('data/v37/preflight.json')
    check(pre['input_hashes'])
    check(pre['code_hashes'])
    selection = read('data/v37/source_selection.json')
    out = ROOT/'data/v37/source_acquisition'
    out.mkdir(exist_ok=False)
    for s in selection['selected']:
        r = request(out, s['source_id'], s['request_url'], read(CFG)['request_limits'], 'source')
        print(json.dumps({'source_id': s['source_id'], 'http': r['http_status'], 'curl': r['curl_returncode'], 'complete': r['transport_complete']}), flush=True)


def finish():
    pre = read('data/v37/preflight.json')
    check(pre['input_hashes'])
    check(pre['code_hashes'])
    cfg = read(CFG)
    nominations = read('data/v37/nominations.json')
    posts = read('data/v37/post_metadata.json')['records']
    selection = read('data/v37/source_selection.json')
    ledger = []
    for s in selection['selected']:
        r = read(f'data/v37/source_acquisition/{s["source_id"]}/receipt.json')
        path = ROOT/f'data/v37/source_acquisition/{s["source_id"]}/body.bin'
        material = source_material(path.read_bytes() if path.exists() else b'', r)
        post = next(p for p in posts if p['post_id'] == s['post_id'])
        ledger.append({**s, **material, 'target_representation': post['representation'], 'independent_review_completed': False,
                       'reviewed_nonoverlapping_passages': 0, 'eligible_for_four_work_capacity': False,
                       'exclusion_reasons': ['independent_review_missing', 'novel_connected_group_not_confirmed', 'target_exposed_at_discovery'] +
                         ([] if material['source_prose_verified'] else ['source_prose_or_edition_review_missing'])})
    write('data/v37/capacity_ledger.json', {'source_slot_denominator': 4, 'selected_work_denominator': len(ledger),
                                          'unfilled_source_slots': 4-len(ledger), 'records': ledger})
    review = {'reviewer_name': None, 'reviewer_identifier': None, 'reviewer_role': None, 'independent_of_prior_predictions': None,
              'prior_exposure': None, 'source_id': None, 'material_hashes': {}, 'source_identity': 'uncertain', 'source_coverage': 'uncertain',
              'span_correspondences': [], 'counterexamples': [], 'uncertainty_notes': [], 'review_completed': False,
              'semantic_labels_admitted': 0, 'source_identity_admitted': False, 'untouched_test_admitted': False}
    write('data/v37/review_return_template.json', review)
    output_dir = ROOT/RUN
    output_dir.mkdir(exist_ok=False)
    report = {'experiment_id': cfg['experiment_id'], 'engineering_state': 'bounded_intake_complete',
              'discovery_queries_distinct': 4, 'search_executions': 8, 'unattributed_batch_preserved_and_excluded': True,
              'post_slot_denominator': 8, 'post_nominees': len(nominations['nominees']),
              'unfilled_post_slots': sum(s['post_id'] is None for s in nominations['slots']),
              'queries_with_no_eligible_results': nominations['queries_with_no_hits'],
              'raw_post_attempts': len(posts), 'raw_posts_available': sum(p['raw_capture_available'] for p in posts),
              'indexed_fallback_opens': len(list((ROOT/'data/v37/fallback').glob('*.json'))),
              'source_slot_denominator': 4, 'selected_source_attempts': len(ledger),
              'source_transport_available': sum(r['transport_available'] for r in ledger),
              'raw_pdfs_available_for_later_review': sum(r['representation'] == 'raw_pdf_unreviewed' for r in ledger),
              'verified_source_prose_units': 0, 'review_ready_pairs': 0, 'independent_reviews_completed': 0,
              'qualifying_unexposed_reviewed_works': 0, 'four_work_capacity_gate_passed': False,
              'scientific_acceptance': None, 'semantic_evaluation_metrics': None, 'semantic_labels_admitted': 0,
              'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
              'natural_targets_rescored': 0, 'lexicon_updates': 0, 'external_messages_sent': 0,
              'next_boundary': 'Review acquired source representation/edition and identify the exact cited-work scope; obtain adequate target captures and a declared review route before any correspondence test.',
              'failures_retained': True}
    write(RUN+'/report.json', report)
    paths = [p for p in (ROOT/'data/v37').rglob('*') if p.is_file()]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'completed', 'finished_at_utc': now(),
                'input_hashes': pre['input_hashes'] | hashes, 'code_hashes': pre['code_hashes'],
                'output_hashes': {'report.json': sha(RUN+'/report.json')}, 'outcome': 'natural_capacity_gate_not_met'}
    write(RUN+'/manifest.json', manifest)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['seal', 'posts', 'metadata', 'sources', 'finish'])
    action = p.parse_args().action
    {'seal': seal, 'posts': posts, 'metadata': metadata, 'sources': sources, 'finish': finish}[action]()
