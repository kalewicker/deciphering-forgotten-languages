"""Freeze current/archival evidence and neutral reviewer dossiers, withholding labels."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.capture_review_v23 import extract_post, review_form

ROOT = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())


def prepare(root=ROOT):
    dest, bp, packets = root/'data/v23/frozen_review.json', root/'benchmarks/kamri_capture_review_v23.json', root/'data/v23/review_packets'
    for p in (dest, bp, packets):
        if p.exists():
            raise FileExistsError(p)
    cp = root/'experiments/kamri_capture_review_v23.json';cfg = read(cp)
    for p, sha in cfg['input_hashes'].items():
        assert digest((root/p).read_bytes()) == sha, p
    pdfs = read(root/'data/v23/pdf_diagnostics.json');qa = read(root/'data/v23/visual_review.json')
    assert qa['independent_semantic_review'] is False
    fingerprints = read(root/'data/v23/archive_payload_digests.json')
    rows = []
    for n in cfg['nominees']:
        capture = root/'data/v23/acquisition';receipts = {}
        for kind in ['native', 'source', 'metadata', 'archive']:
            directory = capture/(n['id']+'_'+kind);receipts[kind] = read(directory/'receipt.json')
        selection = read(capture/(n['id']+'_archive_selection.json'))
        material = {}
        for kind in ['native', 'archive']:
            receipt = receipts[kind];body = capture/(n['id']+'_'+kind)/'body.bin'
            material[kind] = extract_post(body.read_bytes() if body.exists() else b'', receipt, n, selection if kind == 'archive' else None)
        chosen = 'native' if material['native']['eligible'] else 'archive' if material['archive']['eligible'] else None
        pdf = next(r for r in pdfs['records'] if r['nominee_id'] == n['id'])
        page_qa = next(r for r in qa['records'] if r['nominee_id'] == n['id'])
        source_raw = receipts['source']['transport_complete'] and pdf['pdf_parse_valid'] and pdf['source_window_present']
        source_bound = bool(source_raw and pdf['matches_prior_snapshot'])
        checked_images = page_qa['reviewed_images']
        visual = len(pdf['images']) == len(n['source_pages_one_based']) and set(checked_images) == {x['path'] for x in pdf['images']} and page_qa['visual_selection_inspected']
        requirements = {'raw_fl_identity_confirmed': chosen is not None, 'publisher_pdf_window_available': bool(source_raw),
                        'source_selection_byte_bound': source_bound, 'page_image_qa_completed': bool(visual)}
        gate = {'paired_review_material_ready': all(requirements.values()), 'requirements': requirements,
                'unmet': [k for k, v in requirements.items() if not v], 'semantic_training_eligible': False,
                'untouched_test_eligible': False, 'independent_semantic_review_completed': False}
        directory = packets/n['id'];directory.mkdir(parents=True)
        files = []
        if source_raw:
            p = directory/'publisher.pdf';p.write_bytes((capture/(n['id']+'_source')/'body.bin').read_bytes());files.append(str(p.relative_to(root)))
        fingerprint = next(x for x in fingerprints['records'] if x['nominee_id'] == n['id'])
        issues = {'nominee_id': n['id'], 'source_pdf_bytes_differ_from_prior': not pdf['matches_prior_snapshot'],
                  'archival_payload_fingerprint_disagreement': fingerprint['matches_index_digest'] is False,
                  'independent_semantic_review_pending': True, 'full_post_source_coverage_unestablished': True,
                  'registered_material_gate_changed': False}
        dump_json(directory/'open_review_issues.json', issues);files.append(str((directory/'open_review_issues.json').relative_to(root)))
        if chosen:
            p = directory/'fl_post.txt';p.write_text(material[chosen]['text']+'\n');files.append(str(p.relative_to(root)))
        if source_bound:
            p = directory/'publisher_selection.txt';p.write_text(read(root/n['source_document'])['text']+'\n');files.append(str(p.relative_to(root)))
        form = review_form(n);dump_json(directory/'review_form.json', form);files.append(str((directory/'review_form.json').relative_to(root)))
        md = '# Independent review dossier: '+n['id']+'\n\n'
        md += 'Status: '+('paired materials ready; independent semantic review pending' if gate['paired_review_material_ready'] else 'registered material gate incomplete; provenance/extraction review needed')+'.\n\n'
        md += f"Fixed whole FL post: {n['fl_url']}\n\nPublisher route: {n['source_url']}\n\nFixed PDF pages: {n['source_pages_one_based']}. These pages are a source window; whole-post source coverage is not established.\n\n"
        md += f"Chosen FL capture: {chosen or 'unavailable'}. Native current-post availability: {material['native']['eligible']}; dated archival availability: {material['archive']['eligible']}. Archive timestamp: {material['archive'].get('capture_timestamp')}.\n\n"
        md += 'All original HTTP bodies, headers, errors and route decisions are retained in `data/v23/acquisition/`. The source PDF body is `'+str((capture/(n['id']+'_source')/'body.bin').relative_to(root))+'` when available. Fixed page images are listed in `data/v23/pdf_diagnostics.json`.\n\n'
        md += 'The unchanged current publisher PDF is available as [publisher.pdf](publisher.pdf) when parsed. See `open_review_issues.json` for source-byte drift and archive payload-fingerprint discrepancies. Fingerprint disagreement does not prove visible-prose alteration; it remains an open provenance/representation issue. These issues require review before semantic admission.\n\n'
        md += 'Review the full captured FL body, including mixed-language prefaces and headings. Independently check source identity, language scope, statement boundaries, source coverage, span correspondences, copied/renamed entities, gaps and uncertainty. Equal counts and copied names are insufficient for word meanings. Reading-edition English, dictionaries and prior model outputs are excluded.\n\n'
        md += 'Copy `review_form.json` to a new review-return file outside this sealed dossier; do not edit sealed originals. Fill reviewer identity and independence declarations before proposing labels. If FL material is missing, record the acquisition gap rather than reconstructing it from annotations. No labels are accepted by this packet.\n'
        p = directory/'review.md';p.write_text(md);files.append(str(p.relative_to(root)))
        rows.append({'nominee_id': n['id'], 'inventory_entry': n['inventory_entry'], 'connected_group': n['connected_group'],
                     'receipts': receipts, 'archive_selection': selection, 'fl_material': material, 'selected_fl_route': chosen,
                     'pdf_diagnostics': pdf, 'visual_review': page_qa, 'archive_payload_digest_check': fingerprint, 'open_review_issues': issues, 'gate': gate, 'review_packet_files': files,
                     'current_raw_fl': material['native']['eligible'], 'archival_raw_fl': material['archive']['eligible'],
                     'component_previously_exposed': True, 'review_form': form})
    holdout = {'all_existing_inventory_groups_previously_exposed': True, 'reserved_unexposed_groups': [],
               'status': 'new_source_groups_and_independent_review_required', 'nominee_groups_untouched': False,
               'instructions': ['Nominate unexposed connected source works before model/annotation review', 'Freeze future predictions before reference answers are revealed',
                                'Use realistic wrong-source and source-absent controls; count all missing evidence', 'Independent semantic review is separate from capture/automated replay']}
    dump_json(root/'data/v23/holdout_plan.json', holdout)
    frozen = {'sealed_at_utc': utc(), 'records': rows, 'post_denominator': 2, 'publisher_window_denominator': 2,
              'holdout_plan': holdout, 'independent_semantic_reviews_completed': 0, 'model_executed': False,
              'lexicons_used': False, 'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0}
    dump_json(dest, frozen)
    paths = sorted(p for p in (root/'data/v23').rglob('*') if p.is_file())
    inputs = cfg['input_hashes'] | {str(cp.relative_to(root)): digest(cp.read_bytes())} | {str(p.relative_to(root)): digest(p.read_bytes()) for p in paths}
    dump_json(bp, {'experiment_id': cfg['experiment_id'], 'frozen_at_utc': utc(), 'review': str(dest.relative_to(root)), 'input_hashes': inputs})
    print('Frozen both dossiers and all failure/capture routes; independent review remains pending.')

if __name__ == '__main__':
    prepare()
