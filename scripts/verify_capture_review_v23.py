"""Independent request, archival-selection, PDF/window and withheld-review audit."""
from pathlib import Path
from urllib.parse import urlparse
import json
import hashlib
import base64
import re
import subprocess
import unicodedata
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())


def identity(url):
    if not isinstance(url, str):
        return None
    p = urlparse(url)
    if p.scheme not in ['http', 'https'] or p.username is not None or p.password is not None:
        return None
    try:
        if p.port not in [None, 80 if p.scheme == 'http' else 443]:
            return None
    except ValueError:
        return None
    return p.hostname, p.path.rstrip('/'), p.query


def metadata_selection(raw, n):
    try:
        rows = json.loads(raw)
        keys = ['timestamp', 'original', 'statuscode', 'mimetype', 'digest']
        if not isinstance(rows, list) or len(rows) != 2 or rows[0] != keys or len(rows[1]) != 5:
            return {'eligible': False, 'reason': 'absent_or_ambiguous_metadata', 'record': None, 'replay_url': None}
        record = {key: rows[1][i] for i, key in enumerate(keys)}
        if not all(isinstance(v, str) for v in record.values()):
            return {'eligible': False, 'reason': 'invalid_metadata_fields', 'record': None, 'replay_url': None}
        ok = re.fullmatch(r'\d{14}', record['timestamp']) is not None and record['timestamp'] <= n['archive_cutoff'] and record['statuscode'] == '200' and record['mimetype'] == 'text/html' and identity(record['original']) == identity(n['fl_url'])
        return {'eligible': ok, 'reason': None if ok else 'metadata_identity_or_cutoff_failure', 'record': record,
                'replay_url': 'https://web.archive.org/web/'+record['timestamp']+'id_/'+record['original'] if ok else None}
    except (ValueError, TypeError, KeyError):
        return {'eligible': False, 'reason': 'invalid_metadata_json', 'record': None, 'replay_url': None}


def replay_html(raw, r, n, selection=None):
    if not r['transport_complete']:
        return {'eligible': False, 'unmet': ['transport_complete'], 'text': None, 'current_raw_fl': False, 'archival_raw_fl': False}
    soup = BeautifulSoup(raw, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    headings = [h.get_text(' ', strip=True) for h in soup.select('.post-title')]
    bodies = soup.select('div.post-body')
    urls = [r.get('final_url') or '']+[x.get('href', '') for x in soup.select('link[rel="canonical"]')]+[x.get('content', '') for x in soup.select('meta[property="og:url"]')]
    archival = selection is not None;final = urlparse(r.get('final_url') or '')
    marker = '/web/'+selection['record']['timestamp']+'id_/' if archival and selection['eligible'] else None
    original = final.path[len(marker):] if marker and final.path.startswith(marker) else None
    if original:
        urls.append(original)
    bound = not archival or selection['eligible'] and final.hostname == 'web.archive.org' and original is not None and identity(original) == identity(n['fl_url']) and identity(selection['record']['original']) == identity(n['fl_url'])
    canonical = lambda x: ' '.join(unicodedata.normalize('NFC', x).casefold().split())
    req = {'single_post_body': len(bodies) == 1, 'page_title_matches': any(canonical(n['fl_title']) in canonical(t) for t in [title, *headings]),
           'native_permalink_bound': any(identity(u) == identity(n['fl_url']) for u in urls), 'archive_timestamp_original_bound': bool(bound),
           'no_challenge_signatures': not any(v in raw.decode(errors='replace').lower() for v in ['cf-chl-', 'verify you are human', 'checking your browser', 'enable javascript and cookies to continue'])}
    text = None
    if len(bodies) == 1:
        for node in bodies[0].select('script,style,noscript'):
            node.decompose()
        text = bodies[0].get_text(' ', strip=True)
    req['body_prose_nonempty'] = bool(text);ok = all(req.values())
    return {'eligible': ok, 'requirements': req, 'unmet': [k for k, v in req.items() if not v], 'html_title': title, 'post_titles': headings,
            'identity_urls': urls, 'text': text if ok else None, 'text_sha256': digest(text.encode()) if ok else None,
            'current_raw_fl': ok and not archival, 'archival_raw_fl': ok and archival,
            'capture_timestamp': selection['record']['timestamp'] if archival and selection['eligible'] else None,
            'transformations': ['Exactly one div.post-body', 'Remove script/style/noscript only; headings and superscripts retained',
                                'BeautifulSoup visible prose joined with spaces; no language, word, alias or alignment labels']}


def verify_request(r, url, kind, cfg, frozen_at):
    assert r['attempted'] and r['requested_url'] == url and r['kind'] == kind
    assert cfg['registered_at_utc'] < r['started_at_utc'] <= r['finished_at_utc'] < frozen_at
    limits = cfg['request_limits'];maximum = limits['pdf_max_bytes'] if kind == 'source' else limits['fl_metadata_max_bytes']
    directory = ROOT/'data/v23/acquisition'/r['route_id']
    expected = ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed', '--proto', '=https', '--proto-redir', '=https',
                '--connect-timeout', '15', '--max-time', '30', '--max-redirs', '3', '--max-filesize', str(maximum), '--user-agent', limits['user_agent'],
                '--output', str(directory/'body.bin'), '--dump-header', str(directory/'headers.txt'), '--write-out', '%{url_effective}\n%{http_code}', url]
    assert r['command'] == expected and r['max_body_bytes'] == maximum
    for name, artifact in r['artifacts'].items():
        p = Path(artifact['path']);assert p == directory/name and p.is_file()
        assert p.stat().st_size == artifact['bytes'] and digest(p.read_bytes()) == artifact['sha256']
    complete = r['curl_returncode'] == 0 and r['http_status'] == 200 and 'body.bin' in r['artifacts'] and r['artifacts']['body.bin']['bytes'] <= maximum
    assert r['transport_complete'] == complete
    headers = directory/'headers.txt'
    if headers.exists() and r['http_status'] and r['http_status'] >= 100:
        statuses = re.findall(rb'(?m)^HTTP/\S+\s+(\d{3})', headers.read_bytes())
        assert statuses and int(statuses[-1]) == r['http_status']
    assert r['body_representation'] == 'curl transfer/content-decoded response body (--compressed)'


def main():
    out = ROOT/'runs/000023_kamri_capture_review';m = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_capture_review_v23.json');benchmark = read(ROOT/'benchmarks/kamri_capture_review_v23.json')
    frozen = read(ROOT/benchmark['review']);report = read(out/'report.json')
    for p, sha in cfg['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    assert [n['inventory_entry'] for n in cfg['nominees']] == [4, 8] and [n['id'] for n in cfg['nominees']] == ['western_esoterism', 'risk_math']
    assert cfg['post_denominator'] == cfg['publisher_window_denominator'] == frozen['post_denominator'] == frozen['publisher_window_denominator'] == m['post_denominator'] == m['publisher_window_denominator'] == 2
    assert cfg['fixed_request_denominator'] == 6 and cfg['max_primary_requests'] == 8 and cfg['max_total_requests_with_infrastructure_diagnostics'] == 16
    assert cfg['request_limits'] == {'connect_timeout_seconds': 15, 'total_timeout_seconds': 30, 'max_redirects': 3, 'fl_metadata_max_bytes': 2000000,
                                     'pdf_max_bytes': 12000000, 'user_agent': 'FL-Decipher/0.1 finite research pilot'}
    assert cfg['registered_at_utc'] < frozen['sealed_at_utc'] <= benchmark['frozen_at_utc'] < m['started_at_utc']
    pdfs = read(ROOT/'data/v23/pdf_diagnostics.json');qa = read(ROOT/'data/v23/visual_review.json')
    fingerprints = read(ROOT/'data/v23/archive_payload_digests.json');assert fingerprints['registered_primary_gate'] is False
    assert qa['independent_semantic_review'] is False and pdfs['independent_semantic_review'] is False
    assert pdfs['inspected_at_utc'] <= qa['reviewed_at_utc'] < frozen['sealed_at_utc']
    expected_forms = []
    for n, row in zip(cfg['nominees'], frozen['records'], strict=True):
        assert row['nominee_id'] == n['id'] and row['inventory_entry'] == n['inventory_entry'] and row['connected_group'] == n['connected_group']
        for kind, url in [('native', n['fl_url']), ('source', n['source_url']), ('metadata', n['cdx_url'])]:
            r = read(ROOT/'data/v23/acquisition'/(n['id']+'_'+kind)/'receipt.json')
            assert r == row['receipts'][kind];verify_request(r, url, kind, cfg, frozen['sealed_at_utc'])
        metadata = row['receipts']['metadata'];meta_body = ROOT/'data/v23/acquisition'/(n['id']+'_metadata')/'body.bin'
        selection = metadata_selection(meta_body.read_bytes(), n) if metadata['transport_complete'] else {'eligible': False, 'reason': 'metadata_transport_unavailable', 'record': None, 'replay_url': None}
        assert selection == row['archive_selection'] == read(ROOT/'data/v23/acquisition'/(n['id']+'_archive_selection.json'))
        r = row['receipts']['archive'];assert r == read(ROOT/'data/v23/acquisition'/(n['id']+'_archive')/'receipt.json')
        if selection['eligible']:
            verify_request(r, selection['replay_url'], 'archive', cfg, frozen['sealed_at_utc'])
            headers = (ROOT/'data/v23/acquisition'/(n['id']+'_archive')/'headers.txt').read_text(errors='replace')
            dates = re.findall(r'(?im)^memento-datetime:\s*(.+)$', headers)
            assert dates and parsedate_to_datetime(dates[-1].strip()).strftime('%Y%m%d%H%M%S') == selection['record']['timestamp']
        else:
            assert r['attempted'] is False and not r['transport_complete'] and r['requested_url'] is None and r['reason'] == selection['reason'] and r['artifacts'] == {}
        materials = {}
        for kind in ['native', 'archive']:
            p = ROOT/'data/v23/acquisition'/(n['id']+'_'+kind)/'body.bin'
            materials[kind] = replay_html(p.read_bytes() if p.exists() else b'', row['receipts'][kind], n, selection if kind == 'archive' else None)
        assert materials == row['fl_material']
        chosen = 'native' if materials['native']['eligible'] else 'archive' if materials['archive']['eligible'] else None
        assert row['selected_fl_route'] == chosen and row['current_raw_fl'] == materials['native']['eligible'] and row['archival_raw_fl'] == materials['archive']['eligible']
        pdf = next(p for p in pdfs['records'] if p['nominee_id'] == n['id']);assert pdf == row['pdf_diagnostics']
        source_body = ROOT/'data/v23/acquisition'/(n['id']+'_source')/'body.bin'
        assert pdf['source_body_sha256'] == (digest(source_body.read_bytes()) if source_body.exists() else None)
        assert pdf['matches_prior_snapshot'] == (source_body.exists() and digest(source_body.read_bytes()) == n['source_snapshot_sha256'])
        assert pdf['selected_pages_one_based'] == n['source_pages_one_based']
        if row['receipts']['source']['transport_complete'] and source_body.read_bytes().startswith(b'%PDF-') and pdf['pdf_parse_valid']:
            code = 'import sys,json;from pypdf import PdfReader;r=PdfReader(sys.argv[1]);print(json.dumps({"pages":len(r.pages)}))'
            result = subprocess.run([cfg['pdf_runtime'], '-c', code, str(source_body)], capture_output=True, text=True)
            assert result.returncode == 0 and json.loads(result.stdout)['pages'] == pdf['page_count']
            assert pdf['source_window_present'] == (max(n['source_pages_one_based']) <= pdf['page_count'])
        elif not row['receipts']['source']['transport_complete'] or not source_body.read_bytes().startswith(b'%PDF-'):
            assert pdf['pdf_parse_valid'] is False and pdf['source_window_present'] is False
        for image in pdf['images']:
            path = ROOT/image['path'];assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') and digest(path.read_bytes()) == image['sha256']
            assert image['page_one_based'] in n['source_pages_one_based']
        page_qa = next(p for p in qa['records'] if p['nominee_id'] == n['id']);assert page_qa == row['visual_review']
        visual = len(pdf['images']) == len(n['source_pages_one_based']) and set(page_qa['reviewed_images']) == set(i['path'] for i in pdf['images']) and page_qa['visual_selection_inspected']
        source_raw = row['receipts']['source']['transport_complete'] and pdf['pdf_parse_valid'] and pdf['source_window_present']
        bound = bool(source_raw and pdf['matches_prior_snapshot'])
        req = {'raw_fl_identity_confirmed': chosen is not None, 'publisher_pdf_window_available': bool(source_raw), 'source_selection_byte_bound': bound, 'page_image_qa_completed': bool(visual)}
        gate = {'paired_review_material_ready': all(req.values()), 'requirements': req, 'unmet': [k for k, v in req.items() if not v],
                'semantic_training_eligible': False, 'untouched_test_eligible': False, 'independent_semantic_review_completed': False}
        assert row['gate'] == gate
        form = {'nominee_id': n['id'], 'reviewer_name': None, 'independent_of_prior_predictions': None, 'source_identity_checked': None,
                'language_scope_checked': None, 'statement_boundaries_checked': None, 'full_post_source_coverage': None, 'span_correspondences': [],
                'word_correspondences': [], 'counterexamples': [], 'uncertainty_notes': [], 'review_completed': False, 'semantic_training_eligible': False, 'untouched_test_eligible': False}
        assert row['review_form'] == form
        packet = ROOT/'data/v23/review_packets'/n['id'];assert read(packet/'review_form.json') == form
        expected_files = []
        if source_raw:
            assert (packet/'publisher.pdf').read_bytes() == source_body.read_bytes();expected_files.append(str((packet/'publisher.pdf').relative_to(ROOT)))
        fingerprint = next(x for x in fingerprints['records'] if x['nominee_id'] == n['id'])
        archive_body = ROOT/'data/v23/acquisition'/(n['id']+'_archive')/'body.bin'
        actual_digest = base64.b32encode(hashlib.sha1(archive_body.read_bytes()).digest()).decode().rstrip('=') if archive_body.exists() else None
        indexed_digest = selection['record']['digest'] if selection['eligible'] else None
        assert fingerprint['received_decoded_body_sha1_base32'] == actual_digest and fingerprint['cdx_payload_digest'] == indexed_digest
        assert fingerprint['matches_index_digest'] == (actual_digest == indexed_digest if actual_digest is not None and indexed_digest is not None else None)
        assert fingerprint['registered_material_gate_changed'] is False and row['archive_payload_digest_check'] == fingerprint
        issues = {'nominee_id': n['id'], 'source_pdf_bytes_differ_from_prior': not pdf['matches_prior_snapshot'],
                  'archival_payload_fingerprint_disagreement': fingerprint['matches_index_digest'] is False,
                  'independent_semantic_review_pending': True, 'full_post_source_coverage_unestablished': True, 'registered_material_gate_changed': False}
        assert read(packet/'open_review_issues.json') == row['open_review_issues'] == issues
        expected_files.append(str((packet/'open_review_issues.json').relative_to(ROOT)))
        if chosen:
            assert (packet/'fl_post.txt').read_text() == materials[chosen]['text']+'\n';expected_files.append(str((packet/'fl_post.txt').relative_to(ROOT)))
        else:
            assert not (packet/'fl_post.txt').exists()
        if bound:
            assert (packet/'publisher_selection.txt').read_text() == read(ROOT/n['source_document'])['text']+'\n';expected_files.append(str((packet/'publisher_selection.txt').relative_to(ROOT)))
        else:
            assert not (packet/'publisher_selection.txt').exists()
        expected_files += [str((packet/p).relative_to(ROOT)) for p in ['review_form.json', 'review.md']]
        assert row['review_packet_files'] == expected_files
        doc = (packet/'review.md').read_text();assert 'No labels are accepted' in doc and 'do not edit sealed originals' in doc and n['fl_url'] in doc and n['source_url'] in doc
        expected_forms.append(form)
    assert frozen['holdout_plan'] == read(ROOT/'data/v23/holdout_plan.json') == read(out/'holdout_plan.json') == report['holdout_plan']
    assert frozen['holdout_plan']['all_existing_inventory_groups_previously_exposed'] and frozen['holdout_plan']['reserved_unexposed_groups'] == []
    assert frozen['holdout_plan']['nominee_groups_untouched'] is False
    attempts = [read(p) for p in sorted((ROOT/'data/v23/acquisition').glob('*/receipt.json'))]
    assert attempts == report['attempts'] == read(out/'acquisition_ledger.json') and frozen['records'] == report['records'] == read(out/'review_ledger.json')
    primary = [r for r in attempts if not r['route_id'].endswith('_diagnostic')];diagnostic = [r for r in attempts if r['route_id'].endswith('_diagnostic')]
    assert len(primary) == 8
    count = sum(r['attempted'] for r in primary);assert 6 <= count <= 8 and count+len(diagnostic) <= 16
    for r in diagnostic:
        original = next(p for p in primary if p['route_id'] == r['route_id'].removesuffix('_diagnostic'))
        assert original['attempted'] and original['curl_returncode'] in [6, 7]
        assert original['curl_returncode'] == 6 or any(s in original['stderr'].lower() for s in ['permission denied', 'operation not permitted'])
        verify_request(r, original['requested_url'], original['kind'], cfg, frozen['sealed_at_utc'])
    assert report['fixed_requests_attempted'] == 6 and report['primary_requests_attempted'] == count and report['archive_replays_attempted'] == count-6 and report['infrastructure_diagnostic_requests'] == len(diagnostic)
    rows = frozen['records']
    for key, expected in [('current_raw_fl_posts', sum(r['current_raw_fl'] for r in rows)), ('archival_raw_fl_posts', sum(r['archival_raw_fl'] for r in rows)),
                          ('identity_confirmed_fl_materials', sum(r['selected_fl_route'] is not None for r in rows)),
                          ('publisher_pdf_windows_available', sum(r['gate']['requirements']['publisher_pdf_window_available'] for r in rows)),
                          ('source_selections_byte_bound', sum(r['gate']['requirements']['source_selection_byte_bound'] for r in rows)),
                          ('paired_review_materials_ready', sum(r['gate']['paired_review_material_ready'] for r in rows))]:
        assert report[key] == expected
    assert report['review_dossiers_created'] == 2 and report['evaluation_metrics'] is None and report['reserved_unexposed_source_groups'] == []
    assert all(report[k] == 0 for k in ['independent_semantic_reviews_completed', 'semantic_training_eligible_tokens', 'untouched_test_eligible_units', 'source_identity_claims_admitted'])
    assert not report['model_executed'] and not report['lexicons_used'] and not m['model_executed'] and not frozen['model_executed'] and not frozen['lexicons_used']
    assert m['outcome'] == ('review_materials_available_semantic_review_pending' if report['paired_review_materials_ready'] else 'paired_review_material_unavailable')
    previous = []
    for directory in sorted(p for p in (ROOT/'runs').glob('0000*') if p.name < out.name):
        check_hashes(directory);previous.append({'run_id': directory.name, 'manifest_sha256': digest((directory/'manifest.json').read_bytes())})
    assert len(previous) == 22
    for p, sha in read(ROOT/'reports/000022_deliverable_seal.json')['deliverable_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    receipt = {'state': 'verified', 'verified_at_utc': utc(), 'run_id': out.name, 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'primary_requests_attempted': count, 'current_raw_fl_posts': report['current_raw_fl_posts'], 'archival_raw_fl_posts': report['archival_raw_fl_posts'],
               'paired_review_materials_ready': report['paired_review_materials_ready'], 'previous_runs': previous,
               'checks': ['Fixed nominees, request commands/limits/timestamps, all errors, bodies/headers and conditional archive slots',
                          'Independent exact-URL single-record cutoff selection and dated raw replay identity',
                          'Native/current versus archived versus missing FL material; no indexed/annotation fallback',
                          'Independent publisher PDF page count, original-byte/window binding, PNG hashes and same-assistant visual QA',
                          'Reviewer-export provenance, blank answers, missing-material gates and no fake untouched group',
                          'Immutable inputs/code/outputs, twenty-two prior archives and prior deliverable seal unchanged'], 'limits': report['limits']}
    rp = ROOT/'reports/000023_verification.json';preserved = rp.exists()
    if preserved:
        old = read(rp);assert old['state'] == 'verified' and old['manifest_sha256'] == receipt['manifest_sha256'] and old['paired_review_materials_ready'] == receipt['paired_review_materials_ready']
    else:
        dump_json(rp, receipt)
    print(json.dumps({k: receipt[k] for k in ['state', 'primary_requests_attempted', 'current_raw_fl_posts', 'archival_raw_fl_posts', 'paired_review_materials_ready']} | {'previous_runs': 22, 'existing_receipt_preserved': preserved}, indent=2))

if __name__ == '__main__':
    main()
