"""Verify selection, image identities and review arithmetic; not visual judgment."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    run = ROOT / 'runs/000048_numeric_glyph_context'; check_hashes(run)
    cfg = read('experiments/numeric_glyph_context_v48.json'); pre = read('data/v48/preflight.json')
    frozen = read('data/v48/selection.json'); ledger = read('data/v48/review_ledger.json')
    manifest = read('runs/000048_numeric_glyph_context/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/numeric_glyph_context_v48.json'] == sha('experiments/numeric_glyph_context_v48.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < frozen['selected_at_utc'] < ledger['reviewed_at_utc'] < manifest['finished_at_utc']
    assert cfg['request_budget'] == 0 and cfg['context_radius'] == 120
    target = read('data/v47/reference.json')['target_inventory']['anchors']
    keys = {r['key'] for r in target if r['kind'] == 'number'}
    expected = []; images = {}
    for spec in cfg['sources']:
        export = read(spec['export']); inv = read(spec['inventory']); assert sha(spec['pdf']) == export['source_pdf_sha256']
        offsets = []; cursor = 0
        for i, page in enumerate(export['pages']):
            assert page['page'] == i + 1 and hashlib.sha256(page['text'].encode()).hexdigest() == page['text_sha256']
            offsets.append(cursor); cursor += len(page['text']) + 1
        selected = []
        for row in inv['inventory']['anchors']:
            if row['kind'] != 'number' or row['key'] not in keys: continue
            page = export['pages'][row['page'] - 1]; a, b = row['page_span']; text = page['text']
            assert 0 <= a < b <= len(text) and text[a:b] == row['value'] and row['key'] == 'number:' + row['value']
            assert row['span'] == [offsets[row['page'] - 1] + a, offsets[row['page'] - 1] + b]
            assert row['unit'] == row['page'] - 1
            bounds = [max(0, a - 120), min(len(text), b + 120)]
            assert sha(page['image']) == page['image_sha256']; images[page['image']] = page['image_sha256']
            selected.append({'occurrence_id': f"{spec['id']}:{row['anchor_index']}", 'source_id': spec['id'],
                'anchor_index': row['anchor_index'], 'key': row['key'], 'value': row['value'], 'page': row['page'],
                'span': row['span'], 'page_span': row['page_span'], 'image': page['image'], 'image_sha256': page['image_sha256'],
                'context_span': bounds, 'context_text': text[slice(*bounds)]})
        assert len(selected) == spec['expected_occurrences']
        assert len({r['page'] for r in selected}) == spec['expected_pages']
        expected.extend(selected)
    assert frozen['occurrences'] == expected and len(expected) == cfg['expected_occurrences'] == 13
    assert len(images) == cfg['expected_pages'] == 7 and images == cfg['page_image_hashes']
    assert len({(r['source_id'], r['page']) for r in expected}) == 7
    assert ledger['selection_sha256'] == sha('data/v48/selection.json')
    assert ledger['reviewer'] == 'same_agent_visual_review' and ledger['independent_review'] is False
    assert {r['image']: r['image_sha256'] for r in ledger['inspected_pages']} == images
    assert len(ledger['inspected_pages']) == 7 and all(r['complete_page_inspected'] is True for r in ledger['inspected_pages'])
    reviews = ledger['reviews']; ids = {r['occurrence_id']: r for r in expected}
    assert len(reviews) == len({r['occurrence_id'] for r in reviews}) == 13
    assert {r['occurrence_id'] for r in reviews} == set(ids)
    for r in reviews:
        f = ids[r['occurrence_id']]; status = r['glyph_status']; literal = r['visible_literal']
        assert r['image_sha256'] == f['image_sha256']
        assert status in ['literal_match', 'serialization_mismatch', 'unreadable', 'ambiguous']
        assert r['context'] in ['prose', 'figure', 'table', 'header', 'reference', 'ambiguous']
        assert all(isinstance(r[k], str) and r[k].strip() for k in ['locator', 'context_detail', 'note'])
        if status == 'literal_match': assert literal == f['value']
        elif status == 'serialization_mismatch': assert isinstance(literal, str) and literal and literal != f['value']
        elif status == 'unreadable': assert literal is None
        else: assert literal is None or isinstance(literal, str)
    glyphs = dict(sorted(Counter(r['glyph_status'] for r in reviews).items()))
    contexts = dict(sorted(Counter(r['context'] for r in reviews).items()))
    gate = False if glyphs.get('serialization_mismatch') else True if glyphs.get('literal_match', 0) == 13 else None
    by_source = {}
    for s in sorted({r['source_id'] for r in expected}):
        rs = [r for r in reviews if ids[r['occurrence_id']]['source_id'] == s]
        by_source[s] = {'occurrences': len(rs), 'glyph_status_counts': dict(sorted(Counter(r['glyph_status'] for r in rs).items())),
                        'context_counts': dict(sorted(Counter(r['context'] for r in rs).items()))}
    report = read('runs/000048_numeric_glyph_context/report.json')
    assert report['occurrence_denominator'] == 13 and report['page_denominator'] == 7 and report['review_coverage_complete'] is True
    assert report['glyph_status_counts'] == glyphs and report['context_counts'] == contexts and report['by_source'] == by_source
    assert report['literal_glyph_agreement_gate'] == gate and report['all_contexts_resolved'] == ('ambiguous' not in contexts)
    assert report['outcome'] == ('all_literal_glyphs_agree' if gate is True else 'serialization_mismatch_present' if gate is False else 'visual_mapping_unresolved')
    for k in ['network_requests', 'new_pdf_extractions', 'new_page_renders', 'new_structural_scores', 'opaque_lexical_or_semantic_scores',
              'semantic_labels_admitted', 'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 47
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000048_numeric_glyph_context/manifest.json'),
              'all_13_occurrences_and_context_slices_reconstructed': True, 'all_7_original_image_hashes_verified': True,
              'review_coverage_categories_and_arithmetic_verified': True, 'visual_judgments_independently_verified': False,
              'independent_scientific_review': False, 'prior_scores_unchanged': True, 'prior_runs_preserved': prior,
              'semantics_or_source_identity_validated': False}
    out = ROOT / 'reports/000048_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(prior), 'occurrences': 13, 'pages': 7, 'glyph_gate': gate}, indent=2))


if __name__ == '__main__': main()
