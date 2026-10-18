"""Independent boundary/group enumeration and evidence replay; no v21 audit import."""
from pathlib import Path
import json
import re
from collections import defaultdict
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def independent_provenance(doc, registry, qa):
    s = doc['snapshot']
    items = [{'path': s['artifact'], 'sha256': s['sha256'], 'bytes': s.get('bytes')}] if 'artifact' in s else list(s.get('artifacts', {}).values())
    records = []
    for item in items:
        p = Path(item['path']);p = p if p.is_absolute() else ROOT/p
        exists = p.is_file()
        size = p.stat().st_size if exists else None
        ok = exists and digest(p.read_bytes()) == item['sha256'] and (item.get('bytes') is None or size == item['bytes'])
        records.append({'path': str(p.relative_to(ROOT)), 'sha256': item['sha256'], 'bytes': size, 'verified': ok})
    req = {'snapshot_artifacts_verified': len(records) > 0 and all(r['verified'] for r in records)}
    review = None
    if doc['kind'] == 'fl':
        req['historical_indexed_snapshot'] = s['acquisition_kind'] == 'indexed_web_excerpt'
    else:
        req['authority_reviewed'] = registry['authoritative_source']
        req['http_200'] = s.get('http_status') == 200
        req['reviewed_extraction'] = registry['extraction_review'] in ['publisher_html_extract', 'selected_pages_visually_reviewed']
        if registry['extraction_review'] == 'selected_pages_visually_reviewed':
            rr = [r for r in qa['records'] if r['document_id'] == doc['id']]
            review = rr[0] if len(rr) == 1 else None
            req['prior_pdf_selection_review_bound'] = review is not None and any(r['sha256'] == review['raw_sha256'] for r in records) and bool(review['images']) and all((ROOT/p).is_file() for p in review['images'])
    return {'acquisition_kind': s['acquisition_kind'], 'requirements': req, 'eligible': all(req.values()),
            'artifacts': records, 'prior_pdf_qa': review, 'new_visual_or_semantic_review': False}


def independent_atoms(doc):
    result = []
    blocks = doc.get('blocks') or [{'id': 0, 'text': doc['text'], 'span': [0, len(doc['text'])]}]
    for block in blocks:
        assert doc['text'][slice(*block['span'])] == block['text']
        text, spans, start = block['text'], [], 0
        for match in re.finditer(r"[.!?]+(?:[\"”’']*)(?=\s|$)", text):
            if re.fullmatch(r'\s*\d+', text[start:match.start()]):
                continue
            spans.append((start, match.end()));start = match.end()
        if text[start:].strip():
            spans.append((start, len(text)))
        for left, right in spans:
            raw = text[left:right]
            a = left+len(raw)-len(raw.lstrip());b = right-(len(raw)-len(raw.rstrip()))
            if a >= b or not tokens(text[a:b]):
                continue
            raw = text[a:b]
            tt = tokens(raw, block['span'][0]+a)
            result.append({'index': len(result), 'block_id': block['id'], 'text': raw,
                           'span': [block['span'][0]+a, block['span'][0]+b], 'token_span': [tt[0].start, tt[-1].end],
                           'complete': tt[0].surface[0].isupper() and re.search(r'[.!?][\"”’\']*$', raw) is not None})
    return result


def brute_occurrences(locator, doc):
    wanted = [t.normalized for t in tokens(locator)]
    full, aa = tokens(doc['text']), independent_atoms(doc)
    out = []
    for start in range(len(full)):
        window = full[start:start+len(wanted)]
        if not wanted or len(window) != len(wanted) or any(t.normalized != w for t, w in zip(window, wanted, strict=True)):
            continue
        group = []
        for first in range(len(aa)):
            if aa[first]['token_span'][0] != window[0].start:
                continue
            for last in range(first, len(aa)):
                if aa[last]['token_span'][1] > window[-1].end:
                    break
                if aa[last]['token_span'][1] != window[-1].end:
                    continue
                proposal = aa[first:last+1]
                a, b = proposal[0]['span'][0], proposal[-1]['span'][1]
                if [t.normalized for t in tokens(doc['text'][a:b])] == wanted:
                    group = proposal
        span = [group[0]['span'][0], group[-1]['span'][1]] if group else [window[0].start, window[-1].end]
        complete = bool(group) and all(a['complete'] for a in group)
        out.append({'token_span': [window[0].start, window[-1].end], 'statement_span': span if group else None,
                    'text': doc['text'][slice(*span)], 'complete_group': complete, 'atoms': group,
                    'failure': None if complete else 'incomplete_atom' if group else 'partial_statement_match',
                    'tokens': [{'index': i, 'document_token_index': start+i, 'surface': t.surface, 'form': t.normalized,
                                'span': [t.start, t.end]} for i, t in enumerate(window)]})
    return out


def replay(specs, documents, excluded):
    rows = []
    for s in specs:
        occurrences = {}
        for side in ['source', 'fl']:
            occurrences[side] = []
            for path in s[side+'_documents']:
                d = documents[path]['document']
                occurrences[side] += [{'document_id': d['id'], 'document': path, **o} for o in brute_occurrences(s[side+'_locator'], d)]
        so, fo = occurrences['source'], occurrences['fl']
        sc = so[0] if len(so) == 1 else None
        fc = sorted(fo, key=lambda o: (o['document_id'], o['document']))[0] if fo else None
        counts = {p: len([o for o in fo if o['document'] == p]) for p in s['fl_documents']}
        req = {'unique_source_occurrence': len(so) == 1, 'source_complete_statement_group': sc is not None and sc['complete_group'],
               'source_provenance_reviewed': bool(s['source_documents']) and all(documents[p]['provenance']['eligible'] for p in s['source_documents']),
               'source_expected_component': all(documents[p]['document']['source_group'] in s['connected_group'] for p in s['source_documents']),
               'unique_fl_occurrence_per_support_view': bool(counts) and all(n == 1 for n in counts.values()),
               'all_fl_complete_statement_groups': bool(fo) and all(o['complete_group'] for o in fo),
               'fl_support_views_compatible': bool(fo) and len(set(o['text'] for o in fo)) == 1,
               'fl_historical_provenance_and_article_scope': bool(s['fl_documents']) and all(documents[p]['provenance']['eligible'] and documents[p]['document']['url'] == s['article_url'] and documents[p]['document']['source_group'] in s['connected_group'] for p in s['fl_documents']),
               'equal_project_token_counts': sc is not None and fc is not None and len(sc['tokens']) == len(fc['tokens']),
               'target_excluded': s['uid'] != excluded, 'no_observed_order_conflicts': True}
        rows.append({'uid': s['uid'], 'article': s['article'], 'connected_group': s['connected_group'], 'source_occurrences': so,
                     'fl_occurrences': fo, 'fl_support_view_denominator': len(s['fl_documents']), 'fl_occurrences_per_document': counts,
                     'canonical_source': sc, 'canonical_fl': fc, 'fl_token_count': len(fc['tokens']) if fc else None,
                     'source_token_count': len(sc['tokens']) if sc else None, 'requirements': req, 'order_conflicts': [],
                     'semantic_gold': False, 'current_raw_fl': False, 'semantic_training_eligible': False, 'untouched_test_eligible': False})
    ordering = []
    for i in range(len(rows)):
        for j in range(i+1, len(rows)):
            a, b = rows[i], rows[j]
            if a['article'] != b['article']:
                continue
            for side in ['source', 'fl']:
                x, y = a['canonical_'+side], b['canonical_'+side]
                if x is None or y is None or not x['complete_group'] or not y['complete_group'] or x['document'] != y['document']:
                    continue
                check = {'earlier_uid': a['uid'], 'later_uid': b['uid'], 'side': side, 'document': x['document'],
                         'earlier_span': x['statement_span'], 'later_span': y['statement_span'],
                         'ordered_nonoverlapping': x['statement_span'][1] <= y['statement_span'][0]}
                ordering.append(check)
                if not check['ordered_nonoverlapping']:
                    a['order_conflicts'].append(check);b['order_conflicts'].append(check)
    for row in rows:
        row['requirements']['no_observed_order_conflicts'] = len(row['order_conflicts']) == 0
        row['gate'] = {'development_packet_eligible': all(row['requirements'].values()),
                       'unmet': [k for k, v in row['requirements'].items() if v is False],
                       'semantic_training_eligible': False, 'untouched_test_eligible': False, 'current_raw_reference_eligible': False}
    return {'unit_denominator': len(rows), 'rows': rows, 'order_checks': ordering,
            'eligible_uids': [r['uid'] for r in rows if r['gate']['development_packet_eligible']]}


def main():
    out = ROOT/'runs/000021_kamri_calibration_evidence'
    m = check_hashes(out)
    cp = ROOT/'experiments/kamri_calibration_evidence_v21.json'
    config = read(cp);benchmark = read(ROOT/'benchmarks/kamri_calibration_evidence_v21.json');inputs = read(ROOT/benchmark['inputs'])
    report = read(out/'report.json')
    assert config['nominee_denominator'] == m['nominee_denominator'] == report['nominee_denominator'] == 33
    assert config['comparator_denominator'] == m['comparator_denominator'] == report['comparator_denominator'] == 11
    assert config['excluded_target_uid'] == '03:007'
    assert config['broadening_gate'] == {'min_new_eligible_units': 6, 'min_additional_connected_groups': 2, 'min_total_connected_groups': 3}
    assert config['registered_at_utc'] < inputs['sealed_at_utc'] <= benchmark['frozen_at_utc'] < m['started_at_utc']
    assert inputs['orthographic_scores_computed'] is False and inputs['target_excluded'] is True
    for p, sha in config['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    old_docs = read(ROOT/'benchmarks/kamri_dataset_audit_v15.json')['documents']
    annotations = read(ROOT/'data/v15/parsed_annotations.json')['articles']
    article_units = {u['uid']: (a, u) for a in annotations for u in a['units']}
    selected = [r for r in read(ROOT/'runs/000015_kamri_dataset_audit/unit_ledger.json')['rows'] if r['language'] == 'Kamri' and r['both_with_authoritative_english'] and r['uid'] != '03:007']
    assert [r['uid'] for r in selected] == config['nominee_uids'] and len(selected) == 33
    expected_nominees, registries = [], {}
    ids = set()
    for r in selected:
        a, u = article_units[r['uid']]
        paths = {}
        for side, field in [('fl', 'fl_matches'), ('source', 'english_matches')]:
            included = sorted(set(x['document_id'] for x in r[field] if x['scope_accepted'] and (side == 'fl' or x['authoritative_source'])))
            ids.update(included)
            paths[side] = [old_docs[i]['path'] for i in included]
            for i in included:
                registries[old_docs[i]['path']] = old_docs[i]
        expected_nominees.append({'uid': r['uid'], 'article': a['entry'], 'connected_group': r['component'], 'article_url': a['original_url'],
                                  'fl_locator': u['fl'], 'source_locator': u['english'], 'fl_documents': paths['fl'], 'source_documents': paths['source'], 'original_v15_row': r})
    assert config['document_ids'] == sorted(ids) and inputs['nominees'] == expected_nominees
    prior = read(ROOT/'data/v20/frozen_panel.json')['units']
    assert [u['uid'] for u in prior] == config['comparator_uids'] and len(prior) == 11
    expected_comparator = []
    for u in prior:
        a, annotation = article_units[u['uid']]
        for side in ['fl', 'source']:
            path = u[side+'_document']
            if path not in registries:
                registries[path] = {'authoritative_source': side == 'source', 'extraction_review': 'publisher_html_extract' if side == 'source' else 'qualified_or_unreviewed', 'authority_route': 'verified_v16_publisher_capture'}
            if side == 'source':
                assert read(ROOT/path)['source_authority_reviewed']
        expected_comparator.append({'uid': u['uid'], 'article': a['entry'], 'connected_group': a.get('component', [u['component']]),
                                    'article_url': a['original_url'], 'fl_locator': u['fl_statement']['text'], 'source_locator': u['source_statement']['text'],
                                    'fl_documents': [u['fl_document']], 'source_documents': [u['source_document']], 'original_v20_packet': u})
    assert inputs['comparator'] == expected_comparator
    qa = read(ROOT/'data/v15/qa/review.json')
    documents = {}
    for path, registry in registries.items():
        d = read(ROOT/path)
        documents[path] = {'document': d, 'registry': registry, 'provenance': independent_provenance(d, registry, qa)}
    assert inputs['documents'] == documents
    nominees = replay(expected_nominees, documents, '03:007')
    comparator = replay(expected_comparator, documents, '03:007')
    assert nominees == read(out/'nominee_ledger.json') and comparator == read(out/'comparator_ledger.json')
    routes = defaultdict(list)
    for origin, result in [('comparator', comparator), ('nominee', nominees)]:
        for row in result['rows']:
            routes[row['uid']].append((origin, row))
    packets, excluded = [], []
    for uid in sorted(routes):
        rr = routes[uid]
        if any(not r['gate']['development_packet_eligible'] for _, r in rr):
            excluded.append({'uid': uid, 'routes': [{'origin': origin, 'eligible': r['gate']['development_packet_eligible']} for origin, r in rr]})
            continue
        origin, r = rr[0]
        tt = {}
        for side in ['fl', 'source']:
            o = r['canonical_'+side]
            tt[side] = [{'unit_uid': uid, 'document': o['document'], 'index': t['index'], 'surface': t['surface'], 'form': t['form'], 'span': t['span'], 'view_surface': t['surface']} for t in o['tokens']]
        packets.append({'uid': uid, 'connected_group': r['connected_group'], 'fl_document': r['canonical_fl']['document'], 'source_document': r['canonical_source']['document'],
                        'fl_statement': r['canonical_fl'], 'source_statement': r['canonical_source'], 'fl_tokens': tt['fl'], 'source_tokens': tt['source'],
                        'positional_assumptions_unvalidated': True, 'semantic_gold': False, 'current_raw_fl': False, 'untouched_test_eligible': False,
                        'preferred_route': origin, 'eligible_routes': [o for o, _ in rr]})
    baseline_groups = set(tuple(r['connected_group']) for r in comparator['rows'])
    new = [r for r in nominees['rows'] if r['gate']['development_packet_eligible'] and r['uid'] not in config['comparator_uids']]
    additional = sorted(set(tuple(r['connected_group']) for r in new)-baseline_groups)
    total = sorted(set(tuple(p['connected_group']) for p in packets))
    req = {'minimum_new_eligible_units': len(new) >= 6, 'minimum_additional_connected_groups': len(additional) >= 2, 'minimum_total_connected_groups': len(total) >= 3}
    decision = {'meaningfully_broader_panel_available': all(req.values()), 'requirements': req, 'unmet': [k for k, v in req.items() if not v],
                'new_eligible_uids': [r['uid'] for r in new], 'additional_connected_groups': [list(g) for g in additional], 'future_panel_groups': [list(g) for g in total],
                'next_step': 'separately_register_unchanged_rule_retest' if all(req.values()) else 'prioritize_evidence_acquisition_and_independent_review',
                'orthographic_rule_executed': False, 'semantic_acceptance': False, 'untouched_test_eligible': False}
    expected_panel = {'units': packets, 'unit_denominator': len(packets), 'route_failures_retained': excluded,
                      'target_excluded': all(p['uid'] != '03:007' for p in packets), 'decision': decision}
    assert expected_panel == read(out/'future_panel.json')
    assert report['decision'] == decision and report['nominee_eligible_uids'] == nominees['eligible_uids'] and report['comparator_eligible_uids'] == comparator['eligible_uids']
    assert report['nominee_eligible_units'] == len(nominees['eligible_uids']) and report['nominee_ineligible_units'] == 33-len(nominees['eligible_uids'])
    assert report['future_panel_units'] == len(packets) and report['future_panel_token_pairs'] == sum(len(p['fl_tokens']) for p in packets)
    assert report['nominee_eligible_connected_groups'] == [list(g) for g in sorted(set(tuple(r['connected_group']) for r in nominees['rows'] if r['gate']['development_packet_eligible']))]
    assert report['nominee_order_checks'] == len(nominees['order_checks']) and report['comparator_order_checks'] == len(comparator['order_checks'])
    assert report['all_groups_previously_exposed'] and all(not r[k] for r in nominees['rows']+comparator['rows'] for k in ['semantic_gold', 'current_raw_fl', 'semantic_training_eligible', 'untouched_test_eligible'])
    assert all(report[k] == 0 for k in ['semantic_training_eligible_tokens', 'untouched_test_eligible_units', 'current_raw_fl_admissions', 'source_identity_claims_admitted'])
    for item in (m, report):
        assert all(item[k] is False for k in ['model_executed', 'orthographic_rule_executed', 'lexical_prediction_executed', 'translation_model_executed', 'shared_lexicons_used'])
    assert m['outcome'] == ('broader_development_panel_available' if all(req.values()) else 'prioritize_evidence_acquisition')
    v20 = read(ROOT/'runs/000020_kamri_orthographic_anchors/report.json')
    v19 = read(ROOT/'runs/000019_kamri_single_gap/report.json')
    assert v20['primary_gap_lead'] is None and not v20['calibration']['primary']['gate']['conditional_anchor_calibration_eligible']
    assert v19['observed']['maxima']['primary']['gaps'] == list(range(14)) and v19['observed']['maxima']['secondary']['gaps'] == [1, 2]
    oldseal = read(ROOT/'reports/000020_deliverable_seal.json')
    for p, sha in oldseal['deliverable_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    previous = []
    for directory in sorted(p for p in (ROOT/'runs').glob('0000*') if p.name < out.name):
        check_hashes(directory)
        previous.append({'run_id': directory.name, 'manifest_sha256': digest((directory/'manifest.json').read_bytes())})
    assert len(previous) == 20
    receipt = {'state': 'verified', 'verified_at_utc': utc(), 'run_id': out.name, 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'nominee_denominator': 33, 'comparator_denominator': 11, 'nominee_eligible_units': len(nominees['eligible_uids']),
               'future_panel_units': len(packets), 'decision': decision, 'previous_runs': previous,
               'checks': ['Provenance-only nomination, every locator, original v15 row, comparator packet and input seal',
                          'Independent sentence segmentation, exhaustive token occurrences, complete groups and original Unicode spans',
                          'Snapshot artifact hashes, publisher/source extraction review and prior PDF QA binding',
                          'Duplicate FL support views, per-route fail-closed gates, all observable order comparisons and UID deduplication',
                          'Predeclared new-unit/source-group breadth decision; no orthographic or target scoring',
                          'Original v20 failure, v19 alternatives, twenty previous archives and latest prior deliverable seal unchanged'],
               'limits': report['limits']}
    receipt_path = ROOT/'reports/000021_verification.json'
    preserved = receipt_path.exists()
    if preserved:
        saved = read(receipt_path)
        assert saved['state'] == 'verified' and saved['manifest_sha256'] == receipt['manifest_sha256'] and saved['decision'] == decision
    else:
        dump_json(receipt_path, receipt)
    print(json.dumps({'state': 'verified', 'nominees': 33, 'comparator': 11, 'eligible_nominees': len(nominees['eligible_uids']),
                      'future_panel_units': len(packets), 'previous_runs': 20, 'decision': decision, 'existing_receipt_preserved': preserved}, indent=2))

if __name__ == '__main__':
    main()
