"""Freeze the finite provenance continuation and neutral review supplements."""
from pathlib import Path
from email.utils import parsedate_to_datetime
import json
from fl_decipher.capture_review_v23 import extract_post, review_form
from fl_decipher.provenance_v24 import decode_entity, dump, fingerprint, sha, utc, window_gate

ROOT = Path(__file__).resolve().parents[1]


def read(p):
    return json.loads((ROOT/p).read_text())


def main():
    cfg = read('experiments/kamri_provenance_v24.json');seal = read('data/v24/preflight.json')
    for p, h in seal['input_hashes'].items() | seal['code_hashes'].items():
        assert sha((ROOT/p).read_bytes()) == h, p
    out = ROOT/'runs/000024_kamri_provenance';out.mkdir(exist_ok=False)
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'running', 'started_at_utc': utc(),
                'model_executed': False, 'code_hashes': seal['code_hashes'], 'input_hashes': {}}
    dump(out/'manifest.json', manifest)
    try:
        oldcfg = read('experiments/kamri_capture_review_v23.json')
        nominees = {n['id']: n for n in oldcfg['nominees']}
        pdf = read('data/v24/pdf_comparison.json');visual = read('data/v24/visual_review.json')
        assert pdf['window_gate'] == window_gate(pdf['pages'], pdf['page_counts'])
        assert visual['pages_one_based'] == [90,91,92,93,94] and visual['independent_semantic_review'] is False
        analysis = ROOT/'data/v24/analysis';analysis.mkdir(exist_ok=False)
        rows = []
        for route in cfg['routes']:
            n = nominees[route['nominee_id']];directory = ROOT/'data/v24/acquisition'/route['id']
            r = read(str((directory/'receipt.json').relative_to(ROOT)))
            headers = read(str((directory/'headers.json').relative_to(ROOT))) if (directory/'headers.json').exists() else []
            header = {k.lower(): v for k, v in headers}
            raw = (directory/'body.bin').read_bytes() if (directory/'body.bin').exists() else None
            record = {'route_id': route['id'], 'nominee_id': n['id'], 'kind': route['kind'], 'receipt': r,
                      'content_encoding': header.get('content-encoding', 'identity'), 'entity': fingerprint(raw) if raw is not None else None,
                      'decoded': None, 'decode_error': None, 'identity_confirmed': False, 'material': None,
                      'same_decoded_bytes_as_v23_archive': None, 'same_post_text_as_v23_archive': None,
                      'cdx_digest': None, 'entity_matches_cdx': None, 'decoded_matches_cdx': None,
                      'fingerprint_state': 'not_applicable', 'archive_memento_bound': None}
            if route['kind'] == 'archive':
                selection = read('data/v23/acquisition/risk_math_archive_selection.json')
                record['cdx_digest'] = selection['record']['digest']
                record['entity_matches_cdx'] = raw is not None and fingerprint(raw)['sha1_base32'] == record['cdx_digest']
            else:
                selection = None
            decoded = None
            if r['transport_complete']:
                try:
                    decoded = decode_entity(raw, record['content_encoding'], cfg['max_body_bytes'])
                    record['decoded'] = fingerprint(decoded)
                    (analysis/(route['id']+'_decoded.bin')).write_bytes(decoded)
                except Exception as error:
                    record['decode_error'] = f'{type(error).__name__}: {error}'
            if decoded is not None:
                material = extract_post(decoded, r, n, selection)
                exact = r['final_url'] == route['url']
                date_ok = True
                if selection:
                    try:
                        date_ok = parsedate_to_datetime(header['memento-datetime']).strftime('%Y%m%d%H%M%S') == selection['record']['timestamp']
                    except (ValueError, TypeError, KeyError):
                        date_ok = False
                    record['archive_memento_bound'] = date_ok
                record['material'] = material
                record['identity_confirmed'] = material['eligible'] and exact and date_ok
                oldbody = (ROOT/f'data/v23/acquisition/{n["id"]}_archive/body.bin').read_bytes()
                oldtext = (ROOT/f'data/v23/review_packets/{n["id"]}/fl_post.txt').read_text().rstrip('\n')
                record['same_decoded_bytes_as_v23_archive'] = decoded == oldbody
                record['same_post_text_as_v23_archive'] = material.get('text') == oldtext
                if selection:
                    record['decoded_matches_cdx'] = fingerprint(decoded)['sha1_base32'] == record['cdx_digest']
                    if record['entity_matches_cdx'] and record['decoded_matches_cdx']:
                        record['fingerprint_state'] = 'both_representations_match_index'
                    elif record['entity_matches_cdx']:
                        record['fingerprint_state'] = 'entity_matches_decoded_differs_encoding_layer_supported'
                    elif record['decoded_matches_cdx']:
                        record['fingerprint_state'] = 'decoded_matches_entity_differs'
                    else:
                        record['fingerprint_state'] = 'neither_representation_matches_unresolved'
                if record['identity_confirmed']:
                    (analysis/(route['id']+'_post.txt')).write_text(material['text']+'\n')
            elif selection:
                record['fingerprint_state'] = 'incomplete_response_unresolved'
            rows.append(record)
        supplements = ROOT/'data/v24/review_supplements';supplements.mkdir(exist_ok=False)
        for key, n in nominees.items():
            d = supplements/key;d.mkdir()
            dump(d/'review_form.json', review_form(n))
            current = next(r for r in rows if r['nominee_id'] == key and r['kind'] == 'native')
            fl_path = (analysis/(current['route_id']+'_post.txt')) if current['identity_confirmed'] else ROOT/f'data/v23/review_packets/{key}/fl_post.txt'
            (d/'fl_post.txt').write_bytes(fl_path.read_bytes())
            if key == 'western_esoterism' and pdf['window_gate']:
                text = '\n\n'.join(f'PDF PAGE {p}\n'+(ROOT/f'data/v24/qa/new_{p:03d}.txt').read_text() for p in cfg['western']['pages_one_based'])
                (d/'publisher_window.txt').write_text(text+'\n')
            provenance = {'nominee_id': key, 'fl_material_route': 'v24_current_native' if current['identity_confirmed'] else 'v23_dated_archive',
                          'fl_text_origin': str(fl_path.relative_to(ROOT)),
                          'western_window_equivalent_under_v24_rule': pdf['window_gate'] if key == 'western_esoterism' else None,
                          'v23_exact_byte_gate_unchanged': True, 'source_coverage_of_whole_fl_post_established': False,
                          'independent_semantic_review_completed': False, 'source_identity_admitted': False,
                          'semantic_labels_admitted': 0, 'untouched_test_admitted': False}
            dump(d/'provenance.json', provenance)
            (d/'review.md').write_text('# Provenance supplement for independent review\n\n'
                +json.dumps(provenance,indent=2)+'\n\n'
                +'Consult the unchanged v23 publisher PDF and fixed page images; raw hashes and original failures remain authoritative. '
                +'The Western page export, if present, is extracted directly from the new PDF and includes page labels/footnotes, with unverified passage boundaries. '
                +'Window equivalence does not establish a translation, whole-post source coverage or byte identity. '
                +'Risk archive fingerprint layers are reported in the v24 run; a repeat does not replace the original capture. '
                +'Copy the blank form into a new return file; leave this sealed original unchanged. '
                +'Review source identity, language scope, coverage, boundaries, correspondences, counterexamples and uncertainty independently.\n')
        report = {'experiment_id': cfg['experiment_id'], 'logical_requests_attempted': len(rows),
                  'http_transactions_attempted': sum(1+sum(x['allowed'] for x in read(f'data/v24/acquisition/{r["route_id"]}/redirects.json')) for r in rows),
                  'current_native_materials': sum(r['identity_confirmed'] for r in rows if r['kind'] == 'native'),
                  'native_denominator': 2, 'archive_denominator': 1, 'western_window_gate': pdf['window_gate'],
                  'western_raw_bytes_identical': pdf['raw_hashes'][0] == pdf['raw_hashes'][1],
                  'risk_fingerprint_state': rows[-1]['fingerprint_state'], 'records': rows,
                  'independent_semantic_reviews_completed': 0, 'semantic_labels_admitted': 0,
                  'untouched_test_units_admitted': 0, 'evaluation_metrics': None, 'model_executed': False,
                  'v23_gates_and_failures_unchanged': True,
                  'limits': ['Window agreement is scoped to pages 90–94 at one render scale',
                             'Full-document extracted text is descriptive, not full visual identity',
                             'Repeat archive bytes do not establish the original WARC payload',
                             'Current native and historical archive observations remain distinct',
                             'Independent semantic review and new unexposed groups remain pending']}
        dump(out/'report.json', report)
        (out/'report.md').write_text('# Experiment 24: provenance continuation\n\n'
            +f'Western window gate: {pdf["window_gate"]}; raw bytes identical: {report["western_raw_bytes_identical"]}.\n\n'
            +f'Native identity-confirmed captures: {report["current_native_materials"]}/2. Risk archive: {report["risk_fingerprint_state"]}.\n\n'
            +'All three registered route attempts remain in the denominator. Independent semantic reviews, labels and untouched-test admissions remain zero. Evaluation metrics are unavailable. See report.json for every route, both fingerprint layers and original comparison outcomes.\n')
        datafiles = [p for p in (ROOT/'data/v24').rglob('*') if p.is_file()]
        manifest.update(state='completed', outcome='provenance_diagnosis_complete_semantic_review_pending', finished_at_utc=utc(),
             input_hashes=seal['input_hashes'] | {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in datafiles},
             output_hashes={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump(out/'manifest.json', manifest)
        print(json.dumps({k:report[k] for k in ['logical_requests_attempted','current_native_materials','western_window_gate','risk_fingerprint_state']},indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');dump(out/'manifest.json',manifest);raise


if __name__ == '__main__':
    main()
