"""Post-run auditor correction, preserving the execution-frozen v4 auditor.

The original auditor passed all v4 result checks but failed reading v1's
input_hashes: v1 keys are document IDs and values hash normalized text, whereas
v2 onward hash files by path. Only audit compatibility is corrected here; no
matcher, input, threshold, prediction or output is changed or rerun.
"""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v4 import aggregate, validate
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT/'runs/000004_kamri_precision_mass'
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['state'] == 'completed' and manifest['selected_fresh_denominator'] == 40
    for field, base in [('code_hashes', ROOT), ('input_hashes', ROOT), ('output_hashes', out)]:
        for path, sha in manifest[field].items():
            assert digest((base/path).read_bytes()) == sha, path
    cfg = json.loads((ROOT/'experiments/kamri_precision_v4.json').read_text())
    benchmark = json.loads((ROOT/'benchmarks/kamri_precision_v4.json').read_text())
    docs = validate(ROOT, benchmark, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    refs = {r['group']: r for r in benchmark['records']}
    report = json.loads((out/'report.json').read_text())
    raw = json.loads((out/'raw_scores.json').read_text())
    permutations = json.loads((out/'permutations.json').read_text())
    predictions = json.loads((out/'predictions.json').read_text())
    assert len(report['results']) == 228 and len(raw) == 114 and len(report['summaries']) == 44
    for dataset, split in [('real', 'development'), ('synthetic', 'calibration')]:
        for mode in ('effective', 'tokens'):
            threshold = max(a['strength'] for r in raw if r['dataset'] == dataset and r['split'] == split and r['reward'] == mode
                            for a in r['rankings'] if a['source_id'] != refs[r['group']]['source_id']) + 1e-6
            assert threshold == report['thresholds'][dataset+'_'+mode]
    for row in report['results']:
        r = refs[row['group']]
        assert row['split'] == r['split']
        assert row['threshold'] == report['thresholds'][r['dataset']+'_'+row['reward']]
        ranked = row['rankings']
        assert {a['source_id'] for a in ranked} == set(r['candidate_ids'])
        assert [a['strength'] for a in ranked] == sorted([a['strength'] for a in ranked], reverse=True)
        top = ranked[0]
        margin = top['strength'] - ranked[1]['strength']
        correct = top['source_id'] == r['source_id']
        assert row['candidate_margin'] == margin and row['top_work_correct'] == correct
        assert row['unique_correct_top1'] == (correct and margin > 1e-9)
        assert row['admitted'] == (margin > 1e-9 and top['minimum_links_met'] and top['strength'] >= row['threshold'])
        for a in ranked:
            fa, sa = atoms[r['fl_id']], atoms[a['source_id']]
            Cartesian = set()
            for block in a['blocks']:
                assert block['fl_spans'] == [[fa[i].start, fa[i].end] for i in block['fl_atoms']]
                assert block['source_spans'] == [[sa[i].start, sa[i].end] for i in block['source_atoms']]
                Cartesian.update((f, s) for f in block['fl_atoms'] for s in block['source_atoms'])
            edges = {(e['fl_index'], e['source_index']) for e in a['edges']}
            if row['decoder'] == 'cartesian':
                assert edges == Cartesian and a['token_pairs'] is None
            else:
                supports = {}
                for p in a['token_pairs']:
                    assert (p['fl_index'], p['source_index']) in Cartesian and p['score'] >= 0
                    assert any([t.start, t.end] == p['fl_span'] for t in fa[p['fl_index']].tokens)
                    st = next(t for t in sa[p['source_index']].tokens if [t.start, t.end] == p['source_span'])
                    prediction = next(t['prediction'] for t in predictions[r['group']][p['fl_index']] if t['span'] == p['fl_span'])
                    if p['basis'] == 'frozen_anchor':
                        assert prediction == st.normalized and p['score'] == 2.
                    else:
                        assert prediction is None and 0 <= p['score'] <= .5
                    supports.setdefault((p['fl_index'], p['source_index']), []).append(p)
                inferred = {key for key, ps in supports.items() if len(ps) >= 2 or any(p['basis'] == 'frozen_anchor' for p in ps)}
                assert edges == inferred
            assert a['linked_fl_atoms'] == len({f for f, s in edges})
            assert a['minimum_links_met'] == (a['linked_fl_atoms'] >= 3)
        gold = {(e['fl_index'], e['source_index']) for e in r['edges']}
        edges = {(e['fl_index'], e['source_index']) for e in top['edges']}
        assert row['retrieved_edges']['correct'] == (len(edges & gold) if correct else 0)
        assert row['retrieved_edges']['proposed'] == len(edges)
        assert row['retrieved_edges']['reference'] == len(gold)
        if row['retrieved_tokens'] is not None:
            pairs = {(tuple(p['fl_span']), tuple(p['source_span'])) for p in top['token_pairs']}
            truth = {(tuple(p['fl_span']), tuple(p['source_span'])) for p in r['token_pairs']}
            assert row['retrieved_tokens']['correct'] == (len(pairs & truth) if correct else 0)
            assert row['retrieved_tokens']['proposed'] == len(pairs)
            assert row['retrieved_tokens']['reference'] == len(truth)
        absent = [a for a in ranked if (docs[a['source_id']]['source_group'] != r['group'] if r['dataset'] == 'real'
                                       else a['source_id'] != r['source_id'])]
        assert row['source_absent']['top'] == absent[0]
        am = absent[0]['strength'] - absent[1]['strength']
        assert row['source_absent']['false_admission'] == (am > 1e-9 and absent[0]['minimum_links_met'] and absent[0]['strength'] >= row['threshold'])
        count = 0 if r['split'] == 'calibration' else (20 if r['dataset'] == 'real' else 10)
        orders = permutations[r['group']]
        assert len(orders) == count and all(sorted(order) == list(range(len(atoms[r['fl_id']]))) for order in orders)
        assert len(row['shuffle']['strengths']) == count
        assert row['shuffle']['exceed_or_equal_observed'] == sum(s >= top['strength'] for s in row['shuffle']['strengths'])
    for summary in report['summaries']:
        rows = [r for r in report['results'] if r['variant'] == summary['variant']]
        panel = summary['panel']
        if panel.startswith('fresh_'):
            rows = [r for r in rows if r['split'] == 'fresh' and r['family'] == panel[6:]]
        else:
            rows = [r for r in rows if r['split'] == panel]
        assert summary == aggregate(rows, panel, summary['variant'])
        assert summary['selected'] == (5 if panel.startswith('fresh_') else {'fresh': 40, 'calibration': 8, 'development': 9}[panel])
    assert all(e['tokens']['difference'] == 0 for e in report['metamorphic'])
    assert any(e['legacy_units'] != e['protected_units'] for e in report['metamorphic']), 'Metamorphic control must exercise actual boundary changes'
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial']:
        old = ROOT/'runs'/oldid
        receipt = json.loads((old/'manifest.json').read_text())
        for field, base in [('code_hashes', ROOT), ('input_hashes', ROOT), ('output_hashes', old), ('artifact_hashes', old)]:
            for path, sha in receipt.get(field, {}).items():
                if field == 'input_hashes' and oldid == '000001_kamri_excerpt_baseline':
                    document = json.loads((ROOT/'data/normalized'/f'{path}.json').read_text())
                    assert digest(document['text'].encode()) == sha, path
                else:
                    assert digest((base/path).read_bytes()) == sha, path
        previous.append({'run_id': oldid, 'manifest_sha256': digest((old/'manifest.json').read_bytes())})
    verification = {'auditor_path': str(Path(__file__).relative_to(ROOT)),
                    'auditor_sha256': digest(Path(__file__).read_bytes()),
                    'audit_correction': 'v1 document-ID/text hashes handled separately from later path/file hashes; frozen model code unchanged',
                    'pre_execution_tests': '31 passed', 'state': 'verified', 'run_id': manifest['run_id'],
                    'manifest_sha256': digest((out/'manifest.json').read_bytes()),
                    'queries': 57, 'fresh_selected_denominator': 40, 'variants': 4, 'result_rows': 228,
                    'checks': ['input, raw, code and output hashes', 'generated identity spans and reference edges',
                               'fixed family and seed denominators', 'calibration excludes all fresh outcomes',
                               'ordered token evidence and Cartesian expansion', 'unique ranking margins and admissions',
                               'source-absent controls', 'shared shuffled atom orders and exceedances',
                               'boundary-change reward controls', 'aggregate family counts', 'unchanged previous experiments'],
                    'previous_runs': previous, 'new_lexical_claims': 0, 'fresh_real_source_works': 0}
    dump_json(ROOT/'reports/000004_verification.json', verification)
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
