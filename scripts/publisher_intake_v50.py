"""Staged intake; search-tool responses are saved externally between phases."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.capture_review_v23 import request
from fl_decipher.publisher_intake_v50 import inspect_page, nominate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'experiments/publisher_intake_v50.json'
CODE = ['src/fl_decipher/publisher_intake_v50.py', 'scripts/publisher_intake_v50.py', 'tests/test_publisher_intake_v50.py']


def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def verify_preflight():
    pre = read('data/v50/preflight.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'reserve', 'select', 'capture'])
    parser.add_argument('--query-index', type=int); args = parser.parse_args(); cfg = read(CONFIG)
    if args.phase == 'prepare':
        assert not (ROOT / 'data/v50').exists()
        for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
        write('data/v50/preflight.json', {'sealed_at_utc': now(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CONFIG]},
              'registered_search_requests': cfg['search_requests']})
        print(json.dumps({'state': 'prepared', 'search_calls': 2, 'slots': 4, 'maximum_native_routes': 4}))
        return
    verify_preflight()
    if args.phase == 'reserve':
        index = args.query_index; assert index in [0, 1]
        if index == 1: assert (ROOT / 'data/v50/discovery/query00_response.json').exists()
        intent = {'query_index': index, 'started_at_utc': now(), 'tool': 'web.run', 'request_arguments': cfg['search_requests'][index]}
        write(f'data/v50/discovery/query{index:02d}_intent.json', intent)
        print(json.dumps(intent)); return
    if args.phase == 'select':
        responses = []
        for index in range(2):
            intent = read(f'data/v50/discovery/query{index:02d}_intent.json')
            response = read(f'data/v50/discovery/query{index:02d}_response.json')
            assert intent['request_arguments'] == response['request_arguments'] == cfg['search_requests'][index]
            assert response['query_index'] == index and intent['tool'] == response['tool'] == 'web.run'
            assert datetime.fromisoformat(intent['started_at_utc']) <= datetime.fromisoformat(response['finished_at_utc'])
            responses.append(response)
        result = nominate(responses, read(cfg['prior_snapshot']), cfg['slots_per_query'])
        write('data/v50/selection.json', {'selected_at_utc': now(), **result})
        print(json.dumps({'occupied_slots': result['occupied_slots'], 'slots': result['slots'],
                         'attributable_hits': [q['attributable_hits'] for q in result['queries']]}, indent=2)); return
    selection = read('data/v50/selection.json'); assert not (ROOT / 'data/v50/acquisition').exists()
    inputs = [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'data/v50').rglob('*.json'))]
    write('data/v50/capture_preflight.json', {'sealed_at_utc': now(), 'hashes': {p: sha(p) for p in inputs},
        'requests': [{'slot_id': s['slot_id'], 'url': s['nominee']['url']} for s in selection['slots'] if s['nominee']]})
    results = []
    for slot in selection['slots']:
        if slot['nominee'] is None:
            results.append({'slot_id': slot['slot_id'], 'occupied': False, 'native_attempted': False, 'ready_for_future_registration': False,
                            'unmet': ['empty_nomination_slot']}); continue
        key = slot['slot_id']; nominee = slot['nominee']
        receipt = request(ROOT / 'data/v50/acquisition', key, nominee['url'], cfg['request_limits'], 'native')
        body = ROOT / f'data/v50/acquisition/{key}/body.bin'
        observation = inspect_page(body.read_bytes() if body.exists() else b'', receipt, nominee, cfg)
        write(f'data/v50/observations/{key}.json', observation)
        results.append({'slot_id': key, 'occupied': True, 'native_attempted': True, 'url': nominee['url'], 'title': nominee['title'],
            'prior_exposure_tags': nominee['prior_exposure_tags'], 'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
            'ready_for_future_registration': observation['ready_for_future_registration'], 'unmet': observation['unmet'],
            'publication_dates': observation['parsed_publication_dates'], 'paragraph_count': observation['paragraph_count'],
            'nonempty_paragraph_count': observation['nonempty_paragraph_count'], 'paragraph_characters': observation['paragraph_characters']})
        print(json.dumps({'captured_slot': key, 'http_status': receipt['http_status'], 'ready': observation['ready_for_future_registration'],
                          'unmet': observation['unmet']}), flush=True)
    ready = sum(r['ready_for_future_registration'] for r in results)
    report = {'experiment_id': 'publisher_intake_v50', 'outcome': 'four_ready_captures' if ready == 4 else 'partial_intake' if ready else 'no_ready_captures',
        'search_tool_calls': 2, 'search_queries': 2, 'nomination_slot_denominator': 4, 'occupied_slots': selection['occupied_slots'],
        'empty_slots': 4 - selection['occupied_slots'], 'native_route_budget': 4, 'native_routes_attempted': sum(r['native_attempted'] for r in results),
        'ready_captures': ready, 'intake_capacity_met': ready == 4, 'slot_results': results,
        'additional_source_or_page_requests': 0, 'scaffold_or_alignment_scores': 0, 'opaque_lexical_or_semantic_scores': 0,
        'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'independent_source_groups_admitted': 0, 'certified_false_parents': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000050_publisher_intake/report.json', report)
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v50').rglob('*') if p.is_file())
    write('runs/000050_publisher_intake/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
        'finished_at_utc': now(), 'outcome': report['outcome'], 'input_hashes': cfg['input_hashes'] | {CONFIG: sha(CONFIG)},
        'code_hashes': {p: sha(p) for p in CODE}, 'output_hashes': {'report.json': sha('runs/000050_publisher_intake/report.json')} |
                {str(Path('../../') / p): sha(p) for p in files}, 'verifier_written_after_intake': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
