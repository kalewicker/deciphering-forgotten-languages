"""Freeze nominees, comparator, and provenance receipts without statement scoring."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def provenance(root, doc, registry, qa):
    snapshot = doc['snapshot']
    descriptors = [{'path': snapshot['artifact'], 'sha256': snapshot['sha256'], 'bytes': snapshot.get('bytes')}] if 'artifact' in snapshot else list(snapshot.get('artifacts', {}).values())
    artifacts = []
    for item in descriptors:
        path = Path(item['path']);path = path if path.is_absolute() else root/path
        valid = path.exists() and digest(path.read_bytes()) == item['sha256'] and (item.get('bytes') is None or path.stat().st_size == item['bytes'])
        artifacts.append({'path': str(path.relative_to(root)), 'sha256': item['sha256'], 'bytes': path.stat().st_size if path.exists() else None, 'verified': valid})
    requirements = {'snapshot_artifacts_verified': bool(artifacts) and all(a['verified'] for a in artifacts)}
    review = None
    if doc['kind'] == 'fl':
        requirements['historical_indexed_snapshot'] = snapshot['acquisition_kind'] == 'indexed_web_excerpt'
    else:
        requirements.update(authority_reviewed=registry['authoritative_source'], http_200=snapshot.get('http_status') == 200,
                            reviewed_extraction=registry['extraction_review'] in ('publisher_html_extract', 'selected_pages_visually_reviewed'))
        if registry['extraction_review'] == 'selected_pages_visually_reviewed':
            matching = [r for r in qa['records'] if r['document_id'] == doc['id']]
            review = matching[0] if len(matching) == 1 else None
            requirements['prior_pdf_selection_review_bound'] = review is not None and review['raw_sha256'] in {a['sha256'] for a in artifacts} and bool(review['images']) and all((root/p).is_file() for p in review['images'])
    return {'acquisition_kind': snapshot['acquisition_kind'], 'requirements': requirements,
            'eligible': all(requirements.values()), 'artifacts': artifacts, 'prior_pdf_qa': review,
            'new_visual_or_semantic_review': False}


def freeze(root=ROOT):
    dest, bp = root/'data/v21/frozen_inputs.json', root/'benchmarks/kamri_calibration_evidence_v21.json'
    for p in (dest, bp):
        if p.exists():
            raise FileExistsError(p)
    cp = root/'experiments/kamri_calibration_evidence_v21.json'
    config = read(cp)
    for p, sha in config['input_hashes'].items():
        assert digest((root/p).read_bytes()) == sha, p
    v15 = read(root/'benchmarks/kamri_dataset_audit_v15.json')['documents']
    ledger = read(root/'runs/000015_kamri_dataset_audit/unit_ledger.json')['rows']
    annotations = read(root/'data/v15/parsed_annotations.json')['articles']
    article_by_uid = {u['uid']: (a, u) for a in annotations for u in a['units']}
    qa = read(root/'data/v15/qa/review.json')
    docs, nominees = {}, []
    def add(path, registry):
        if path not in docs:
            d = read(root/path)
            docs[path] = {'document': d, 'registry': registry, 'provenance': provenance(root, d, registry, qa)}
    selected = [r for r in ledger if r['language'] == 'Kamri' and r['both_with_authoritative_english'] and r['uid'] != config['excluded_target_uid']]
    assert [r['uid'] for r in selected] == config['nominee_uids'] and len(selected) == 33
    for r in selected:
        a, u = article_by_uid[r['uid']]
        paths = {}
        for side, key in [('fl', 'fl_matches'), ('source', 'english_matches')]:
            ids = sorted({m['document_id'] for m in r[key] if m['scope_accepted'] and (side == 'fl' or m['authoritative_source'])})
            paths[side] = [v15[i]['path'] for i in ids]
            for i in ids:
                add(v15[i]['path'], v15[i])
        nominees.append({'uid': r['uid'], 'article': a['entry'], 'connected_group': r['component'],
                         'article_url': a['original_url'], 'fl_locator': u['fl'], 'source_locator': u['english'],
                         'fl_documents': paths['fl'], 'source_documents': paths['source'], 'original_v15_row': r})
    prior = read(root/'data/v20/frozen_panel.json')['units']
    comparator = []
    assert [u['uid'] for u in prior] == config['comparator_uids'] and len(prior) == 11
    for u in prior:
        a, annotation = article_by_uid[u['uid']]
        for side in ('fl', 'source'):
            add(u[side+'_document'], {'authoritative_source': side == 'source', 'extraction_review': 'publisher_html_extract' if side == 'source' else 'qualified_or_unreviewed', 'authority_route': 'verified_v16_publisher_capture'})
        comparator.append({'uid': u['uid'], 'article': a['entry'], 'connected_group': a['component'] if 'component' in a else [u['component']],
                           'article_url': a['original_url'], 'fl_locator': u['fl_statement']['text'], 'source_locator': u['source_statement']['text'],
                           'fl_documents': [u['fl_document']], 'source_documents': [u['source_document']], 'original_v20_packet': u})
    frozen = {'sealed_at_utc': utc(), 'nominees': nominees, 'comparator': comparator, 'documents': docs,
              'orthographic_scores_computed': False, 'target_excluded': True}
    dump_json(dest, frozen)
    inputs = config['input_hashes'] | {str(cp.relative_to(root)): digest(cp.read_bytes()), str(dest.relative_to(root)): digest(dest.read_bytes())}
    dump_json(bp, {'experiment_id': config['experiment_id'], 'frozen_at_utc': utc(), 'inputs': str(dest.relative_to(root)), 'input_hashes': inputs})
    print('Frozen all 33 nominees and eleven comparator inputs; statement and orthographic scores uncomputed.')

if __name__ == '__main__':
    freeze()
