"""Immutable accounting of bounded captures and pending independent review."""
from pathlib import Path
import json
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc

ROOT = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())


def main():
    cp, bp = ROOT/'experiments/kamri_capture_review_v23.json', ROOT/'benchmarks/kamri_capture_review_v23.json'
    cfg, benchmark = read(cp), read(bp)
    for p, sha in benchmark['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    review = read(ROOT/benchmark['review'])
    assert cfg['registered_at_utc'] < review['sealed_at_utc'] <= benchmark['frozen_at_utc']
    out = ROOT/'runs/000023_kamri_capture_review';out.mkdir(exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    manifest = {'run_id': out.name, 'experiment_id': cfg['experiment_id'], 'stage': cfg['stage'], 'state': 'running', 'started_at_utc': utc(),
                'model_executed': False, 'lexicons_used': False, 'post_denominator': 2, 'publisher_window_denominator': 2,
                'python': sys.version, 'platform': platform.platform(), 'input_hashes': benchmark['input_hashes'] | {str(bp.relative_to(ROOT)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest);start = time.monotonic()
    try:
        rows = review['records'];assert [r['nominee_id'] for r in rows] == [n['id'] for n in cfg['nominees']]
        attempts = [read(p) for p in sorted((ROOT/'data/v23/acquisition').glob('*/receipt.json'))]
        primary = [r for r in attempts if not r['route_id'].endswith('_diagnostic')]
        diagnostic = [r for r in attempts if r['route_id'].endswith('_diagnostic')]
        requests = sum(r['attempted'] for r in primary)
        assert len(primary) == 8 and 6 <= requests <= 8 and requests+len(diagnostic) <= 16
        report = {'experiment_id': cfg['experiment_id'], 'stage': cfg['stage'], 'model_executed': False, 'lexicons_used': False,
                  'post_denominator': 2, 'publisher_window_denominator': 2, 'fixed_requests_attempted': 6,
                  'archive_replays_attempted': requests-6, 'primary_requests_attempted': requests, 'infrastructure_diagnostic_requests': len(diagnostic),
                  'current_raw_fl_posts': sum(r['current_raw_fl'] for r in rows), 'archival_raw_fl_posts': sum(r['archival_raw_fl'] for r in rows),
                  'identity_confirmed_fl_materials': sum(r['selected_fl_route'] is not None for r in rows),
                  'publisher_pdf_windows_available': sum(r['gate']['requirements']['publisher_pdf_window_available'] for r in rows),
                  'source_selections_byte_bound': sum(r['gate']['requirements']['source_selection_byte_bound'] for r in rows),
                  'paired_review_materials_ready': sum(r['gate']['paired_review_material_ready'] for r in rows),
                  'review_dossiers_created': len(rows), 'independent_semantic_reviews_completed': 0,
                  'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0,
                  'reserved_unexposed_source_groups': [], 'holdout_plan': review['holdout_plan'],
                  'evaluation_metrics': None, 'source_identity_claims_admitted': 0,
                  'records': rows, 'attempts': attempts,
                  'limits': ['Current native, dated archival raw and historical indexed evidence remain distinct', 'Both nominated source groups were previously exposed',
                             'Fixed publisher windows do not establish whole-post source coverage', 'Same-assistant page QA is not independent semantic review',
                             'No lexical model, target gap scoring, semantic labels or untouched fold admitted']}
        dump_json(out/'acquisition_ledger.json', attempts);dump_json(out/'review_ledger.json', rows);dump_json(out/'holdout_plan.json', review['holdout_plan']);dump_json(out/'report.json', report)
        md = '# Experiment 23: bounded capture and independent-review preparation\n\n'
        md += f"Two whole-post nominees, two fixed publisher windows. Six fixed requests and {requests-6} metadata-derived archival replays, plus {len(diagnostic)} infrastructure diagnostics. All eight planned primary route slots remain visible.\n\n"
        md += '| Nominee | Native raw FL identity | Dated archive identity | Publisher window available | Source prose byte-bound | Paired review materials ready | Independent semantic review |\n|---|---|---|---|---|---|---|\n'
        for r in rows:
            q = r['gate']['requirements']
            md += f"| {r['nominee_id']} | {r['current_raw_fl']} | {r['archival_raw_fl']} | {q['publisher_pdf_window_available']} | {q['source_selection_byte_bound']} | {r['gate']['paired_review_material_ready']} | pending |\n"
        md += f"\nNative FL posts: {report['current_raw_fl_posts']}/2; archival FL posts: {report['archival_raw_fl_posts']}/2. Paired review-material packets: {report['paired_review_materials_ready']}/2. Both dossiers include every failure and blank reviewer forms. Semantic labels, completed independent reviews and untouched-test admissions remain zero; evaluation metrics are unavailable.\n\n"
        md += 'No new untouched connected group is reserved because the existing inventory and both nominees were exposed. The prospective holdout plan requires new source works and independent review before frozen prediction. Imported indexed excerpts and annotations were not used to fill missing captures. Native and archival attempts, cutoff choices, raw bodies/headers, fixed PDF images and page-QA limitations are preserved.\n'
        (out/'report.md').write_text(md)
        manifest.update(state='completed', outcome='review_materials_available_semantic_review_pending' if report['paired_review_materials_ready'] else 'paired_review_material_unavailable',
                        finished_at_utc=utc(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
        print(json.dumps({k: report[k] for k in ['primary_requests_attempted', 'archive_replays_attempted', 'current_raw_fl_posts', 'archival_raw_fl_posts',
                                              'publisher_pdf_windows_available', 'paired_review_materials_ready', 'independent_semantic_reviews_completed', 'evaluation_metrics']}, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}');dump_json(out/'manifest.json', manifest);raise

if __name__ == '__main__':
    main()
