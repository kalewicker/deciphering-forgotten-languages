"""Staged two-slot intake, with externally recorded search-tool responses."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.additional_intake_v55 import alias_plan, body_text, capacity, nominate, prospective_decision
from fl_decipher.cohort_scope_v52 import extract_scope
from fl_decipher.publisher_intake_v50 import service_title
from fl_decipher.routing_v53 import assess, capture as http_capture, header_blocks

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/additional_intake_v55.json'
RUN = 'runs/000055_additional_intake'
CODE = ['src/fl_decipher/additional_intake_v55.py', 'scripts/additional_intake_v55.py', 'tests/test_additional_intake_v55.py']


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, obj):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(obj, stream, indent=2, ensure_ascii=False); stream.write('\n')
def bytes_if(p): return (ROOT / p).read_bytes() if (ROOT / p).exists() else b''


def verify_preflight():
    for p, h in read('data/v55/preflight.json')['hashes'].items(): assert sha(p) == h, p


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'reserve', 'record', 'select', 'capture'])
    parser.add_argument('--query-index', type=int); parser.add_argument('--response-json'); parser.add_argument('--error')
    args = parser.parse_args(); cfg = read(CFG)
    if args.phase == 'prepare':
        assert not (ROOT / 'data/v55').exists()
        for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
        write('data/v55/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]},
              'registered_search_requests': cfg['search_requests']})
        print(json.dumps({'state': 'prepared', 'search_calls': 2, 'slots': 2, 'native_route_budget': 2, 'alias_route_budget': 2})); return
    verify_preflight()
    if args.phase in ('reserve', 'record'):
        index = args.query_index; assert index in (0, 1)
        if args.phase == 'reserve':
            if index: assert (ROOT / 'data/v55/discovery/query00_response.json').exists()
            intent = {'query_index': index, 'started_at_utc': utc(), 'tool': 'web.run', 'request_arguments': cfg['search_requests'][index]}
            write(f'data/v55/discovery/query{index:02d}_intent.json', intent); print(json.dumps(intent)); return
        intent = read(f'data/v55/discovery/query{index:02d}_intent.json')
        assert intent['request_arguments'] == cfg['search_requests'][index]
        saved = {'query_index': index, 'tool': 'web.run', 'request_arguments': cfg['search_requests'][index],
                 'finished_at_utc': utc(), 'response': json.loads(args.response_json) if args.response_json else None, 'error': args.error}
        write(f'data/v55/discovery/query{index:02d}_response.json', saved)
        print(json.dumps({'saved_query_index': index, 'response_type': type(saved['response']).__name__, 'error': saved['error']})); return
    if args.phase == 'select':
        saved = [read(f'data/v55/discovery/query{i:02d}_response.json') for i in range(2)]
        for i, response in enumerate(saved):
            intent = read(f'data/v55/discovery/query{i:02d}_intent.json')
            assert intent['request_arguments'] == response['request_arguments'] == cfg['search_requests'][i]
            assert intent['started_at_utc'] <= response['finished_at_utc']
        result = nominate(saved, read(cfg['prior_snapshot']))
        write('data/v55/selection.json', {'selected_at_utc': utc(), **result})
        print(json.dumps({'occupied_slots': result['occupied_slots'], 'slots': result['slots'],
                          'attributable_hits': [q['attributable_hits'] for q in result['queries']]}, indent=2)); return
    selection = read('data/v55/selection.json'); assert not (ROOT / RUN).exists()
    assert not (ROOT / 'data/v55/acquisition').exists() and not (ROOT / 'data/v55/capture_preflight.json').exists()
    inputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v55').rglob('*.json'))
    write('data/v55/capture_preflight.json', {'sealed_at_utc': utc(), 'hashes': {p: sha(p) for p in inputs},
        'requests': [{'slot_id': s['slot_id'], 'url': s['nominee']['url']} for s in selection['slots'] if s['nominee']]})
    results = []; aliases = 0
    for slot in selection['slots']:
        sid = slot['slot_id']; nominee = slot['nominee']
        if nominee is None:
            results.append({'slot_id': sid, 'occupied': False, 'development_capture_eligible': False, 'unmet': ['empty_nomination_slot']}); continue
        spec = {'id': sid, 'url': nominee['url'], 'expected_title': service_title(nominee['title']), 'v50_ready_unchanged': None}
        write(f'data/v55/{sid}_spec.json', spec)
        receipt = http_capture(ROOT / 'data/v55/acquisition', {'id': sid, 'og_url': nominee['url']}, cfg['request_limits'])
        base = f'data/v55/acquisition/{sid}'; raw = bytes_if(base + '/body.bin')
        try: scope = extract_scope(raw, body_text(raw), cfg['eligibility_rule']['source_selector'])
        except (ValueError, AssertionError): scope = None
        write(f'data/v55/{sid}_scope.json', scope)
        plan = alias_plan(raw, receipt, spec)
        native_files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / base).iterdir() if p.is_file())
        write(f'data/v55/{sid}_alias_plan.json', {'sealed_at_utc': utc(), 'native_input_hashes': {p: sha(p) for p in native_files}, **plan})
        route = None
        if plan['request_url'] is not None:
            route_spec = {'id': sid, 'og_url': plan['request_url'], 'canonical_url': spec['url'],
                          'expected_title': spec['expected_title'], 'old_body_sha256': hashlib.sha256(raw).hexdigest(), 'v50_ready_unchanged': None}
            write(f'data/v55/{sid}_route_spec.json', route_spec)
            alias_receipt = http_capture(ROOT / 'data/v55/alias_acquisition', {'id': sid, 'og_url': plan['request_url']}, cfg['request_limits'])
            alias_base = f'data/v55/alias_acquisition/{sid}'
            route = assess(bytes_if(alias_base + '/body.bin'), bytes_if(alias_base + '/headers.txt'), alias_receipt, route_spec)
            write(f'data/v55/{sid}_route.json', route); aliases += 1
        observation = prospective_decision(raw, receipt, spec, cfg['eligibility_rule'], route)
        write(f'data/v55/{sid}_decision.json', observation)
        results.append({'slot_id': sid, 'occupied': True, 'url': spec['url'], 'expected_title': spec['expected_title'],
            'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'], 'alias_attempted': route is not None,
            'development_capture_eligible': observation['development_capture_eligible'], 'unmet': observation['unmet'],
            'publication_dates': observation['parsed_publication_dates'], 'paragraph_runs': observation['paragraph_run_count'],
            'paragraph_run_characters': observation['paragraph_run_characters']})
        print(json.dumps(results[-1]), flush=True)
    old = read('runs/000054_offline_intake/report.json'); assert old['eligible_development_candidates'] == 2
    responses = sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT / 'data/v55').rglob('headers.txt'))
    report = {'experiment_id': 'additional_intake_v55', 'search_tool_calls': 2, 'search_queries': 2,
        'occupied_slots': selection['occupied_slots'], 'empty_slots': 2 - selection['occupied_slots'],
        'native_routes_attempted': selection['occupied_slots'], 'alias_routes_attempted': aliases,
        'recorded_application_responses': responses, 'slot_results': results,
        **capacity(old['eligible_candidate_ids'], results), 'v50_ready_captures_unchanged': 1,
        'v54_eligible_candidates_unchanged': 2, 'v50_and_v54_original_capacity_failures_preserved': True,
        'natural_benchmark_qualifying_works_from_intake': 0, 'natural_benchmark_capacity_met': False,
        'scaffold_or_alignment_scores': 0, 'opaque_lexical_or_semantic_scores': 0, 'source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write(RUN + '/report.json', report)
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v55').rglob('*') if p.is_file())
    write(RUN + '/manifest.json', {'experiment_id': 'additional_intake_v55', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in files},
        'verifier_written_after_intake': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
