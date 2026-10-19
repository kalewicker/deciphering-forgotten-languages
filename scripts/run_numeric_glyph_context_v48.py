"""Prepare fixed image-audit packet, then validate the complete manual ledger."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.numeric_glyph_context_v48 import select_occurrences, summarize

ROOT = Path(__file__).resolve().parents[1]
CODE = ['scripts/run_numeric_glyph_context_v48.py', 'src/fl_decipher/numeric_glyph_context_v48.py', 'tests/test_numeric_glyph_context_v48.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'finalize']); args = parser.parse_args()
    config_path = 'experiments/numeric_glyph_context_v48.json'; cfg = read(config_path)
    if args.phase == 'prepare':
        assert not (ROOT / 'data/v48').exists()
        for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
        write('data/v48/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
              'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [config_path]}})
        target = read('data/v47/reference.json')['target_inventory']['anchors']; selection = []
        for spec in cfg['sources']:
            export = read(spec['export']); assert sha(spec['pdf']) == export['source_pdf_sha256']
            rows = select_occurrences(spec['id'], target, read(spec['inventory']), export, cfg['page_image_hashes'], cfg['context_radius'])
            assert len(rows) == spec['expected_occurrences']
            assert len({r['page'] for r in rows}) == spec['expected_pages']
            selection.extend(rows)
        assert len(selection) == cfg['expected_occurrences'] == 13
        assert len({(r['source_id'], r['page']) for r in selection}) == cfg['expected_pages'] == 7
        assert {r['image']: r['image_sha256'] for r in selection} == cfg['page_image_hashes']
        write('data/v48/selection.json', {'selected_at_utc': datetime.now(timezone.utc).isoformat(), 'occurrences': selection})
        print(json.dumps({'phase': 'prepared', 'occurrences': len(selection), 'pages': 7, 'selection_sha256': sha('data/v48/selection.json')}))
    else:
        pre = read('data/v48/preflight.json')
        for p, h in pre['hashes'].items(): assert sha(p) == h, p
        frozen = read('data/v48/selection.json'); ledger = read('data/v48/review_ledger.json')
        assert ledger['selection_sha256'] == sha('data/v48/selection.json')
        assert ledger['reviewer'] == 'same_agent_visual_review' and ledger['independent_review'] is False
        assert frozen['selected_at_utc'] < ledger['reviewed_at_utc']
        summary = summarize(frozen['occurrences'], ledger['reviews'])
        gate = summary['literal_glyph_agreement_gate']
        report = {'experiment_id': 'numeric_glyph_context_v48', 'outcome': 'all_literal_glyphs_agree' if gate is True else 'serialization_mismatch_present' if gate is False else 'visual_mapping_unresolved',
                  **summary, 'network_requests': 0, 'new_pdf_extractions': 0, 'new_page_renders': 0, 'new_structural_scores': 0,
                  'opaque_lexical_or_semantic_scores': 0, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
                  'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
                  'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
        write('runs/000048_numeric_glyph_context/report.json', report)
        outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v48').glob('*.json'))
        write('runs/000048_numeric_glyph_context/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
              'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'outcome': report['outcome'],
              'input_hashes': cfg['input_hashes'] | {config_path: sha(config_path)}, 'code_hashes': {p: sha(p) for p in CODE},
              'output_hashes': {'report.json': sha('runs/000048_numeric_glyph_context/report.json')} |
                               {str(Path('../../') / p): sha(p) for p in outputs}, 'verifier_written_after_review': True})
        print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
