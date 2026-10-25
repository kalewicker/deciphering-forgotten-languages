"""Read-only custody/span checks; no network, parsing of ZIPs, or claim validation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text())


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def verify():
    reg_path = 'experiments/yid_resource_v89.json'
    reg = read(reg_path)
    manifest = read('runs/000089_yid_resource/manifest.json')
    assert manifest['state'] == 'complete'
    assert manifest['input_hashes'] == reg['input_hashes'] | {reg_path: digest(reg_path)}
    for path, value in manifest['input_hashes'].items():
        assert digest(path) == value, path
    for path, value in manifest['output_hashes'].items():
        assert digest(path) == value, path
    assert reg['request_budget'] == manifest['web_tool_open_calls'] == 1
    assert reg['followup_requests'] == manifest['followup_requests'] == manifest['payload_downloads'] == 0
    assert not reg['new_predictions'] and not manifest['new_predictions']
    intent = read('data/v89/request_intent.json')
    assert intent['registration_sha256'] == digest(reg_path)
    assert intent['request'] == {'open': [{'ref_id': reg['target_url']}], 'response_length': 'long'}
    provider = read('data/v89/provider_response.json')
    assert provider['representation'] == 'serialized_web_provider_response_not_raw_origin_html'
    assert reg['registered_at_utc'] <= intent['reserved_at_utc'] <= provider['returned_at_utc'] <= manifest['finished_at_utc']
    ledger = read('data/v89/observations.json')
    assert ledger['provider_artifact_sha256'] == digest(ledger['provider_artifact_path'])
    assert ledger['source_url'] == reg['target_url']
    text = provider['provider_result']
    for item in ledger['spans'].values():
        assert item['json_pointer'] == '/provider_result'
        assert 0 <= item['start'] < item['end'] <= len(text)
        assert text[item['start']:item['end']] == item['exact_text']
    spans = ledger['spans']
    assert spans['author_claimed_package_scope']['end'] < spans['download_label']['start'] < spans['download_url']['start'] < spans['comments_boundary']['start']
    assert ledger['offer_url'] == spans['download_url']['exact_text']
    assert ledger['resource_offer_found'] and ledger['feasibility_status'] == 'download_offer_observed_payload_unchecked'
    assert ledger['verified_post_count'] is None and ledger['independent_group_capacity'] is None
    assert ledger['new_confirmation_units'] == ledger['semantic_benchmark_qualifying_works'] == 0
    for key in ('payload_downloaded', 'payload_availability_verified', 'native_FL_bytes_authenticated',
                'new_corpus_material_admitted', 'new_predictions'):
        assert not ledger[key]
    report = read('runs/000089_yid_resource/report.json')
    assert {k:v for k,v in report.items() if k != 'retained_evidence_files'} == {
        k:v for k,v in ledger.items() if k not in ('spans','offer_url','prior_exposure')}
    for path, value in read('reports/000088_deliverable_seal.json')['deliverable_hashes'].items():
        assert digest(path) == value, path
    print(json.dumps({'integrity_and_spans_verified': True, 'evidence_spans': len(spans),
                      'web_tool_open_calls': 1, 'followup_requests': 0,
                      'resource_offer_found': True, 'payload_downloaded': False,
                      'scientific_claims_validated': False}, indent=2))


if __name__ == '__main__':
    verify()
