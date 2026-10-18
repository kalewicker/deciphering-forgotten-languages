"""Finite capture, source-page export and exact-text scope assessment."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

from fl_decipher.capture_review_v23 import request, skipped
from fl_decipher.dated_capture_scope_v38 import archive_selection, dated_gate, indexed_export, observable_scope

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/dated_capture_scope_v38.json'
RUN = 'runs/000038_dated_capture_scope'


def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def write(p, obj):
    target = ROOT/p
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def check():
    pre = read('data/v38/preflight.json')
    for field in ('input_hashes', 'code_hashes'):
        for p, expected in pre[field].items():
            assert sha(p) == expected, p
    return pre


def seal():
    cfg = read(CFG)
    for p, expected in cfg['input_hashes'].items(): assert sha(p) == expected, p
    assert not (ROOT/'data/v38/acquisition').exists()
    code = [*list((ROOT/'src/fl_decipher').glob('*.py')), *list((ROOT/'scripts').glob('*.py')), *list((ROOT/'tests').glob('*.py'))]
    write('data/v38/preflight.json', {'sealed_at_utc': now(), 'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)},
                                     'code_hashes': {str(p.relative_to(ROOT)): sha(p) for p in sorted(code)},
                                     'raw_requests_before_seal': 0, 'source_comparisons_before_seal': 0})
    print('Registered fixed target/source and two route slots sealed before acquisition.')


def acquire():
    check()
    cfg = read(CFG)
    root = ROOT/'data/v38/acquisition'
    root.mkdir(exist_ok=False)
    receipt = request(root, 'metadata', cfg['cdx_url'], cfg['request_limits'], 'metadata')
    raw_path = root/'metadata/body.bin'
    selection = archive_selection(raw_path.read_bytes(), cfg) if receipt['transport_complete'] else {
        'eligible': False, 'reason': 'metadata_transport_unavailable', 'record': None, 'replay_url': None}
    write('data/v38/acquisition/selection.json', selection)
    print(json.dumps({'slot': 'metadata', 'http': receipt['http_status'], 'curl': receipt['curl_returncode'], 'eligible': selection['eligible']}), flush=True)
    if selection['eligible']:
        r = request(root, 'replay', selection['replay_url'], cfg['request_limits'], 'archive')
        print(json.dumps({'slot': 'replay', 'http': r['http_status'], 'curl': r['curl_returncode']}), flush=True)
    else:
        skipped(root, 'replay', 'archive', selection['reason'])
        print('Replay slot retained as skipped: '+selection['reason'], flush=True)


def export_source():
    check()
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    cfg = read(CFG)
    out = ROOT/'data/v38/source_pages'
    out.mkdir(exist_ok=False)
    reader, pdf = PdfReader(ROOT/cfg['source_pdf']), pdfium.PdfDocument(str(ROOT/cfg['source_pdf']))
    assert len(reader.pages) == len(pdf) == cfg['source_pages']
    pages = []
    for i, p in enumerate(reader.pages):
        text = p.extract_text()
        assert text.strip()
        image_path = f'data/v38/source_pages/page{i+1:02d}.png'
        pdf[i].render(scale=1.4).to_pil().save(ROOT/image_path)
        pages.append({'page': i+1, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                      'unicode_scope': [0, len(text)], 'image': image_path, 'image_sha256': sha(image_path),
                      'width': float(p.mediabox.width), 'height': float(p.mediabox.height)})
    write('data/v38/source_export.json', {'exported_at_utc': now(), 'source_pdf_sha256': sha(cfg['source_pdf']),
                                        'pages': pages, 'method': 'pypdf unchanged page text; PDFium images; no text repairs',
                                        'independent_semantic_review': False})
    print(json.dumps({'pages_exported': len(pages), 'source_sha256': sha(cfg['source_pdf']), 'source_compared': False}))


def assess():
    pre = check()
    cfg = read(CFG)
    qa = read('data/v38/visual_review.json')
    exported = read('data/v38/source_export.json')
    assert qa['reviewed_pages'] == list(range(1, 9)) and qa['independent_review'] is False
    root = ROOT/'data/v38/acquisition'
    meta, replay = read('data/v38/acquisition/metadata/receipt.json'), read('data/v38/acquisition/replay/receipt.json')
    def bytes_or_empty(p): return p.read_bytes() if p.exists() else b''
    gate = dated_gate(cfg, meta, bytes_or_empty(root/'metadata/body.bin'), replay,
                      bytes_or_empty(root/'replay/body.bin'), bytes_or_empty(root/'replay/headers.txt').decode(errors='replace'))
    assert gate['selection'] == read('data/v38/acquisition/selection.json')
    write('data/v38/dated_material_gate.json', gate)
    if gate['passed']:
        target = {'text': gate['post_extraction']['text'], 'representation': 'dated_archival_post_body_export',
                  'raw_post': True, 'current_post': False, 'capture_timestamp': gate['selection']['record']['timestamp'],
                  'parent_sha256': sha('data/v38/acquisition/replay/body.bin')}
    else:
        parent = (ROOT/cfg['indexed_parent']).read_text()
        target = indexed_export(parent, *cfg['indexed_lines']) | {'parent': cfg['indexed_parent'], 'parent_sha256': sha(cfg['indexed_parent'])}
    write('data/v38/target_export.json', target)
    scope = observable_scope(target['text'], exported['pages'], cfg['anchors'])
    write('data/v38/observable_scope.json', scope)
    # The bundle retains uncertainty and cannot serve as an independent review.
    bundle = ROOT/'data/v38/scoped_materials'
    bundle.mkdir(exist_ok=False)
    shutil.copyfile(ROOT/cfg['source_pdf'], bundle/'source.pdf')
    for name, obj in [('source_export.json', exported), ('target_export.json', target), ('dated_material_gate.json', gate),
                      ('same_assistant_observations.json', scope), ('visual_review.json', qa)]:
        with (bundle/name).open('x') as f: json.dump(obj, f, indent=2); f.write('\n')
    with (bundle/'target.txt').open('x') as f: f.write(target['text'])
    form = {'reviewer_name': None, 'reviewer_role': None, 'prior_exposure': None, 'independent_of_prior_predictions': None,
            'source_relationship': 'uncertain', 'whole_post_source_coverage': 'uncertain', 'span_correspondences': [],
            'counterexamples': [], 'uncertainty_notes': [], 'review_completed': False, 'semantic_labels_admitted': 0,
            'source_identity_admitted': False, 'untouched_test_admitted': False}
    with (bundle/'review_return_template.json').open('x') as f: json.dump(form, f, indent=2); f.write('\n')
    note = ('# Scoped material-review bundle\n\nTarget representation: '+target['representation']+'.\nDated-material gate: '+str(gate['passed'])+
            '. The gate file retains every failure; indexed text is not raw/current HTML or proven complete.\n\n'+
            'The source PDF is unchanged. Source exports are page-local pypdf text with Unicode code-point offsets; page images remain in data/v38/source_pages/. '+
            'No extraction repairs were made; hyphenation, math and broken spacing remain. Same-assistant observations are exposed development notes, not independent review.\n\n'+
            'Quote matches test exact literal text only. Shared topic words, copied names and a bibliography citation do not establish source identity, opaque word meanings, translation or whole-post coverage. '+
            'Source absence under this extraction does not reject edited or translated reuse.\n\n'+
            'For independent review, declare identity, human/automated role, prior exposure and independence; cite exact file hashes, half-open Unicode offsets and quotes, plus source page. '+
            'Supported, rejected and uncertain findings are welcome. Save a new return; preserve originals. No reviewer is assigned or contacted. '+
            'The included observations expose predictions, so reviewing this annotated bundle is not a blind independent replication.\n')
    with (bundle/'README.md').open('x') as f: f.write(note)
    members = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(bundle.iterdir())}
    with (bundle/'manifest.json').open('x') as f: json.dump({'members': members, 'state': 'scoped_exposed_materials_not_semantic_gold'}, f, indent=2); f.write('\n')
    with zipfile.ZipFile(ROOT/'data/v38/scoped_materials.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.iterdir()): z.write(p, p.name)
    report = {'experiment_id': cfg['experiment_id'], 'engineering_state': 'completed', 'route_slot_denominator': 2,
              'route_attempts': int(meta['attempted'])+int(replay['attempted']), 'metadata_transport_complete': meta['transport_complete'],
              'replay_attempted': replay['attempted'], 'replay_transport_complete': replay['transport_complete'],
              'dated_material_gate_passed': gate['passed'], 'dated_material_checks': gate['checks'],
              'target_representation': target['representation'], 'source_pages': len(exported['pages']),
              'quote_denominator': scope['quote_denominator'], 'quotes_with_literal_source_presence': scope['quotes_with_literal_source_presence'],
              'positive_controls_passed': scope['positive_controls_passed'], 'negative_control_passed': scope['negative_control']['passed'],
              'exact_citation_occurrences': len(scope['exact_citation_hits_in_target']), 'anchor_observations': scope['anchors'],
              'source_relationship': 'unresolved', 'whole_post_source_coverage': 'unresolved',
              'four_work_capacity_gate_passed': False, 'natural_targets_rescored': 0, 'opaque_passages_scored': 0,
              'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
              'untouched_test_units_admitted': 0, 'scientific_acceptance': None, 'semantic_evaluation_metrics': None,
              'external_messages_sent': 0, 'new_source_downloads': 0, 'source_or_target_replaced': False}
    (ROOT/RUN).mkdir(exist_ok=False)
    write(RUN+'/report.json', report)
    paths = sorted(p for p in (ROOT/'data/v38').rglob('*') if p.is_file())
    write(RUN+'/manifest.json', {'experiment_id': cfg['experiment_id'], 'state': 'completed', 'finished_at_utc': now(),
                                'outcome': 'material_scope_audited_source_relationship_unresolved',
                                'input_hashes': pre['input_hashes'] | {str(p.relative_to(ROOT)): sha(p) for p in paths},
                                'code_hashes': pre['code_hashes'], 'output_hashes': {'report.json': sha(RUN+'/report.json')}})
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['seal', 'acquire', 'export-source', 'assess'])
    action = parser.parse_args().action
    {'seal': seal, 'acquire': acquire, 'export-source': export_source, 'assess': assess}[action]()
