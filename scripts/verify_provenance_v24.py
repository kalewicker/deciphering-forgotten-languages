"""Offline independent replay of v24 gates, representations and sealed evidence."""
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import base64
import gzip
import hashlib
import io
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(p):
    return json.loads((ROOT/p).read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fp(raw):
    return {'bytes': len(raw), 'sha256': sha(raw), 'sha1_base32': base64.b32encode(hashlib.sha1(raw).digest()).decode()}


def pdf_replay():
    import pypdf
    import pypdfium2
    cfg = read('experiments/kamri_provenance_v24.json');saved = read('data/v24/pdf_comparison.json')
    textlists = [];counts = []
    for i, name in enumerate(['old_pdf','new_pdf']):
        path = ROOT/cfg['western'][name];reader = pypdf.PdfReader(path)
        counts.append(len(reader.pages));texts = [p.extract_text() for p in reader.pages];textlists.append(texts)
        assert sha(path.read_bytes()) == saved['raw_hashes'][i]
        assert dict(reader.metadata or {}) == saved['metadata'][i]
        document = pypdfium2.PdfDocument(str(path))
        for number, row in zip([90,91,92,93,94], saved['pages'], strict=True):
            assert number == row['page_one_based']
            side = row['sides'][i];page = document[number-1];bmp = page.render(scale=1.5)
            rgb = bmp.to_pil().convert('RGB')
            assert side['dimensions'] == list(page.get_size()) and side['pixel_size'] == list(rgb.size)
            assert side['pixels_sha256'] == sha(rgb.tobytes())
            from PIL import Image
            image = Image.open(ROOT/side['image']).convert('RGB')
            assert image.size == rgb.size and image.tobytes() == rgb.tobytes()
            assert side['image_sha256'] == sha((ROOT/side['image']).read_bytes())
            assert side['text_sha256'] == sha(texts[number-1].encode())
            assert (ROOT/side['text_path']).read_text() == texts[number-1]
            assert side['text_nonempty'] == bool(texts[number-1].strip())
            contents = reader.pages[number-1].get_contents()
            assert side['content_sha256'] == sha(contents.get_data() if contents else b'')
            bmp.close();page.close()
        document.close()
    assert counts == saved['page_counts']
    assert saved['all_page_text_equal'] == (textlists[0] == textlists[1])
    assert saved['all_page_text_hashes'] == [sha(json.dumps(t,ensure_ascii=False).encode()) for t in textlists]
    gate = counts[0] == counts[1] and len(saved['pages']) == 5
    for row in saved['pages']:
        a,b = row['sides']
        expected = {'text_equal': a['text_sha256'] == b['text_sha256'],
                    'text_nonempty': a['text_nonempty'] and b['text_nonempty'],
                    'dimensions_equal': a['dimensions'] == b['dimensions'],
                    'pixels_equal': a['pixel_size'] == b['pixel_size'] and a['pixels_sha256'] == b['pixels_sha256'],
                    'decoded_content_streams_equal': a['content_sha256'] == b['content_sha256']}
        for k,v in expected.items():
            assert row[k] == v, k
        gate = gate and all(expected[k] for k in ['text_equal','text_nonempty','dimensions_equal','pixels_equal'])
    assert saved['window_gate'] == gate
    assert saved['whole_document_visual_equivalence_established'] is False
    print(json.dumps({'pdf_replay_verified':True,'window_gate':gate,'pages_verified':5}))


def main():
    from verify_capture_review_v23 import replay_html
    cfg = read('experiments/kamri_provenance_v24.json');seal = read('data/v24/preflight.json')
    manifest = read('runs/000024_kamri_provenance/manifest.json');report = read('runs/000024_kamri_provenance/report.json')
    assert manifest['state'] == 'completed' and manifest['model_executed'] is False
    for hashes in [cfg['input_hashes'], seal['input_hashes'], seal['code_hashes'], manifest['input_hashes'], manifest['code_hashes']]:
        for p,h in hashes.items():
            assert sha((ROOT/p).read_bytes()) == h, p
    for name,h in manifest['output_hashes'].items():
        assert sha((ROOT/'runs/000024_kamri_provenance'/name).read_bytes()) == h
    assert cfg['registered_at_utc'] < seal['sealed_at_utc'] < manifest['started_at_utc'] < manifest['finished_at_utc']
    assert cfg['max_redirects'] == 3 and cfg['max_http_transactions'] == 12 and cfg['logical_request_denominator'] == 3
    assert cfg['socket_timeout_seconds'] == 15 and cfg['total_timeout_seconds'] == 30 and cfg['max_body_bytes'] == 2000000
    oldcfg = read('experiments/kamri_capture_review_v23.json');nominees = {n['id']:n for n in oldcfg['nominees']}
    selected = read('data/v23/acquisition/risk_math_archive_selection.json')
    assert [r['url'] for r in cfg['routes']] == [n['fl_url'] for n in oldcfg['nominees']] + [selected['replay_url']]
    assert [r['id'] for r in cfg['routes']] == ['western_esoterism_native','risk_math_native','risk_math_archive']
    assert len(report['records']) == 3
    native_count = 0;transactions = 0
    for route,row in zip(cfg['routes'],report['records'],strict=True):
        directory = f'data/v24/acquisition/{route["id"]}'
        r = read(directory+'/receipt.json');client = read(directory+'/client.json');redirects = read(directory+'/redirects.json')
        assert row['receipt'] == r and r['attempted'] and r['route_id'] == route['id'] and r['requested_url'] == route['url'] and r['kind'] == route['kind']
        assert seal['sealed_at_utc'] < r['started_at_utc'] < r['finished_at_utc'] < manifest['started_at_utc']
        assert client['verify_mode'] == 2 and client['check_hostname'] is True and client['trust_store']['x509_ca'] > 0
        assert client['proxy_policy'] == 'explicit_empty' and client['accept_encoding'] == 'identity' and client['content_decoding_automatic'] is False
        assert client['openssl'].startswith('OpenSSL')
        assert len(redirects) <= 4 and sum(x['allowed'] for x in redirects) <= 3
        from urllib.parse import urlsplit
        for i,x in enumerate(redirects,1):
            u=urlsplit(x['to']);o=urlsplit(route['url'])
            allowed = i <= 3 and u.scheme == 'https' and u.hostname == o.hostname and u.port in (None,443) and u.username is None and u.password is None
            assert x['allowed'] == allowed
        transactions += 1+sum(x['allowed'] for x in redirects)
        for name,data in r['artifacts'].items():
            assert fp((ROOT/directory/name).read_bytes()) == data
        bodypath = ROOT/directory/'body.bin';raw = bodypath.read_bytes() if bodypath.exists() else None
        complete = (not r['deadline_expired'] and r['child_returncode'] == 0 and r['http_status'] == 200 and r['read_complete'] and raw is not None and len(raw) <= 2000000)
        assert r['transport_complete'] == complete
        assert row['entity'] == (fp(raw) if raw is not None else None)
        headers = {k.lower():v for k,v in read(directory+'/headers.json')} if (ROOT/directory/'headers.json').exists() else {}
        assert row['content_encoding'] == headers.get('content-encoding','identity')
        decoded = None
        if complete:
            encoding = row['content_encoding'].strip().lower()
            try:
                if encoding in ('identity',''):
                    decoded = raw
                elif encoding == 'gzip':
                    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                        decoded = stream.read(2000001)
                else:
                    raise ValueError('unsupported encoding')
                if len(decoded) > 2000000:
                    raise ValueError('decoded bound exceeded')
            except (ValueError, OSError, EOFError):
                decoded = None;assert row['decode_error']
        if decoded is not None:
            assert row['decoded'] == fp(decoded)
            assert (ROOT/f'data/v24/analysis/{route["id"]}_decoded.bin').read_bytes() == decoded
            n=nominees[route['nominee_id']];selection=selected if route['kind'] == 'archive' else None
            material = replay_html(decoded,r,n,selection)
            assert material == row['material']
            bound=True
            if selection:
                try:
                    bound=parsedate_to_datetime(headers['memento-datetime']).strftime('%Y%m%d%H%M%S') == selected['record']['timestamp']
                except (KeyError, ValueError, TypeError):
                    bound=False
                assert row['archive_memento_bound'] == bound
            identity = material['eligible'] and r['final_url'] == route['url'] and bound
            assert row['identity_confirmed'] == identity
            assert row['same_decoded_bytes_as_v23_archive'] == (decoded == (ROOT/f'data/v23/acquisition/{n["id"]}_archive/body.bin').read_bytes())
            assert row['same_post_text_as_v23_archive'] == (material.get('text') == (ROOT/f'data/v23/review_packets/{n["id"]}/fl_post.txt').read_text().rstrip('\n'))
            if identity:
                assert (ROOT/f'data/v24/analysis/{route["id"]}_post.txt').read_text() == material['text']+'\n'
                native_count += route['kind'] == 'native'
        else:
            assert row['decoded'] is None and row['identity_confirmed'] is False
        if route['kind'] == 'archive':
            expected_digest=selected['record']['digest'];assert row['cdx_digest'] == expected_digest
            entitymatch=raw is not None and fp(raw)['sha1_base32'] == expected_digest
            assert row['entity_matches_cdx'] == entitymatch
            if decoded is not None:
                decodedmatch=fp(decoded)['sha1_base32'] == expected_digest
                assert row['decoded_matches_cdx'] == decodedmatch
                state=('both_representations_match_index' if entitymatch and decodedmatch else
                       'entity_matches_decoded_differs_encoding_layer_supported' if entitymatch else
                       'decoded_matches_entity_differs' if decodedmatch else 'neither_representation_matches_unresolved')
            else:
                state='incomplete_response_unresolved'
            assert row['fingerprint_state'] == state == report['risk_fingerprint_state']
    assert report['current_native_materials'] == native_count and report['logical_requests_attempted'] == 3
    assert report['http_transactions_attempted'] == transactions <= 12
    pdf = read('data/v24/pdf_comparison.json');assert report['western_window_gate'] == pdf['window_gate']
    assert report['western_raw_bytes_identical'] == (pdf['raw_hashes'][0] == pdf['raw_hashes'][1])
    visual = read('data/v24/visual_review.json');assert visual['independent_semantic_review'] is False and visual['pages_one_based'] == [90,91,92,93,94]
    for image,h in visual['image_hashes'].items():
        assert sha((ROOT/image).read_bytes()) == h
    for key in nominees:
        prefix=f'data/v24/review_supplements/{key}'
        form=read(prefix+'/review_form.json');provenance=read(prefix+'/provenance.json')
        assert form['nominee_id'] == key
        assert all(v is None for k,v in form.items() if k not in ['nominee_id','span_correspondences','word_correspondences','counterexamples','uncertainty_notes','review_completed','semantic_training_eligible','untouched_test_eligible'])
        for k in ['span_correspondences','word_correspondences','counterexamples','uncertainty_notes']:
            assert form[k] == []
        assert form['review_completed'] is form['semantic_training_eligible'] is form['untouched_test_eligible'] is False
        assert (ROOT/prefix/'fl_post.txt').read_bytes() == (ROOT/provenance['fl_text_origin']).read_bytes()
        current=next(r for r in report['records'] if r['nominee_id'] == key and r['kind'] == 'native')
        assert provenance['fl_material_route'] == ('v24_current_native' if current['identity_confirmed'] else 'v23_dated_archive')
        assert provenance['independent_semantic_review_completed'] is provenance['source_identity_admitted'] is provenance['untouched_test_admitted'] is False
        assert provenance['semantic_labels_admitted'] == 0 and provenance['v23_exact_byte_gate_unchanged'] is True
        if key == 'western_esoterism' and pdf['window_gate']:
            expected='\n\n'.join(f'PDF PAGE {p}\n'+(ROOT/f'data/v24/qa/new_{p:03d}.txt').read_text() for p in [90,91,92,93,94])+'\n'
            assert (ROOT/prefix/'publisher_window.txt').read_text() == expected
    for k in ['independent_semantic_reviews_completed','semantic_labels_admitted','untouched_test_units_admitted']:
        assert report[k] == 0
    assert report['evaluation_metrics'] is None and report['model_executed'] is False and report['v23_gates_and_failures_unchanged'] is True
    result=subprocess.run([cfg['pdf_runtime'],str(Path(__file__).resolve()),'--pdf'],check=True,capture_output=True,text=True)
    pdf_result=json.loads(result.stdout)
    # All prior experiments: validate their persisted input/code/output inventories offline.
    prior=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent.name == '000024_kamri_provenance':
            continue
        m=json.loads(path.read_text())
        for key in ['input_hashes','code_hashes']:
            for p,h in m.get(key,{}).items():
                assert sha((ROOT/p).read_bytes()) == h, (str(path),p)
        for p,h in m.get('output_hashes',{}).items():
            assert sha((path.parent/p).read_bytes()) == h, (str(path),p)
        prior.append(path.parent.name)
    oldseal=read('reports/000023_deliverable_seal.json')
    assert sha((ROOT/'runs/000023_kamri_capture_review/manifest.json').read_bytes()) == oldseal['run_manifest_sha256']
    for p,h in oldseal['deliverable_hashes'].items():
        assert sha((ROOT/p).read_bytes()) == h,p
    receipt={'state':'verified','manifest_sha256':sha((ROOT/'runs/000024_kamri_provenance/manifest.json').read_bytes()),
             'prior_runs_preserved':prior,'pdf_replay':pdf_result,'logical_requests_verified':3,'http_transactions_verified':transactions,
             'current_native_materials_verified':native_count,'risk_fingerprint_state':report['risk_fingerprint_state'],
             'independent_semantic_reviews_completed':0,'evaluation_metrics':None}
    target=ROOT/'reports/000024_verification.json'
    if target.exists():
        previous=json.loads(target.read_text());assert {k:v for k,v in previous.items() if k != 'verified_at_utc'} == receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['--pdf']:
        pdf_replay()
    else:
        main()
