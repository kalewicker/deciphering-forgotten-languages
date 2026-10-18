"""Audit frozen predictions, scope, counts, controls, and historical provenance."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v5 import summarize, validate
from fl_decipher.lexicon import predict
from fl_decipher.register_v5 import ALIASES, audit_aliases
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT/'runs/000005_kamri_scoped_register'
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['state'] == 'completed' and manifest['selected_fresh_denominator'] == 2
    for field, base in [('input_hashes', ROOT), ('code_hashes', ROOT), ('output_hashes', out)]:
        for path, sha in manifest[field].items():
            assert digest((base/path).read_bytes()) == sha, path
    cfg = json.loads((ROOT/'experiments/kamri_register_v5.json').read_text())
    benchmark = json.loads((ROOT/'benchmarks/kamri_register_v5.json').read_text())
    docs = validate(ROOT, benchmark, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    refs = {r['group']: r for r in benchmark['records']}
    report = json.loads((out/'report.json').read_text())
    raw = json.loads((out/'raw_scores.json').read_text())
    ps = json.loads((out/'predictions.json').read_text())
    gates = json.loads((out/'gates.json').read_text())
    permutations = json.loads((out/'permutations.json').read_text())
    lexicon = json.loads((ROOT/cfg['lexicon_path']).read_text())
    assert len(report['results']) == 33 and len(raw) == 30 and len(report['summaries']) == 6
    for group, variants in ps.items():
        fa = atoms[refs[group]['fl_id']]
        counts = {}
        for s in fa:
            for t in s.tokens:
                if t.normalized in ALIASES:
                    counts[t.normalized] = counts.get(t.normalized, 0)+1
        active = len(counts) >= 2 and sum(counts.values()) >= 3
        assert gates[group] == {'active': active, 'distinct_markers': len(counts), 'total_markers': sum(counts.values()), 'counts': counts}
        for variant, predictions in variants.items():
            use = variant == 'universal_aliases' or (variant == 'gated_aliases' and active)
            for s, row in zip(fa, predictions, strict=True):
                original = predict(s, lexicon, cfg['lexicon_rules'])
                for old, p in zip(original, row, strict=True):
                    expected = ALIASES.get(p['form'], old['prediction']) if use else old['prediction']
                    assert p['prediction'] == expected and p['span'] == old['span']
                    override = use and p['form'] in ALIASES
                    assert p['origin'] == ('registered_alias' if override else 'frozen_v1' if old['prediction'] is not None else 'abstained')
                    if override:
                        assert p['baseline_prediction'] == old['prediction'] and p['state'] == 'experimental_single_work_register_hypothesis'
    for variant in cfg['variants']:
        threshold = max(a['strength'] for r in raw if r['split'] == 'development' and r['variant'] == variant
                        for a in r['rankings'] if docs[a['source_id']]['source_group'] != r['group'])+1e-6
        assert threshold == report['thresholds'][variant]
    for row in report['results']:
        r = refs[row['group']]
        if not r['available']:
            assert row['status'] == 'source_unavailable' and row['reference_edges'] is None
            assert row['admitted'] is None and row['source_absent'] is None
            continue
        fa = atoms[r['fl_id']]
        ranked = row['rankings']
        assert {a['source_id'] for a in ranked} == set(cfg['candidate_ids'])
        top = ranked[0]
        margin = top['strength']-ranked[1]['strength']
        correct = top['source_id'] == r['source_id']
        assert row['candidate_margin'] == margin
        assert row['top_work_correct'] == correct and row['unique_correct_top1'] == (correct and margin > 1e-9)
        assert row['admitted'] == (margin > 1e-9 and top['minimum_links_met'] and top['strength'] >= row['threshold'])
        for a in ranked:
            sa = atoms[a['source_id']]
            supports = {}
            fspans, sspans = [], []
            allowed = set()
            for block in a['blocks']:
                assert block['fl_spans'] == [[fa[i].start, fa[i].end] for i in block['fl_atoms']]
                assert block['source_spans'] == [[sa[i].start, sa[i].end] for i in block['source_atoms']]
                allowed.update((f, s) for f in block['fl_atoms'] for s in block['source_atoms'])
            for p in a['token_pairs']:
                assert (p['fl_index'], p['source_index']) in allowed
                assert any([t.start, t.end] == p['fl_span'] for t in fa[p['fl_index']].tokens)
                st = next(t for t in sa[p['source_index']].tokens if [t.start, t.end] == p['source_span'])
                prediction = next(x['prediction'] for x in ps[r['group']][row['variant']][p['fl_index']] if x['span'] == p['fl_span'])
                assert p['score'] >= 0
                if p['basis'] in ('frozen_anchor', 'experimental_alias'):
                    assert prediction == st.normalized and p['score'] == 2.
                    item = next(x for x in ps[r['group']][row['variant']][p['fl_index']] if x['span'] == p['fl_span'])
                    assert p['anchor_origin'] == item['origin']
                    assert (p['basis'] == 'experimental_alias') == (item['origin'] == 'registered_alias')
                else:
                    assert prediction is None and p['score'] <= .5
                supports.setdefault((p['fl_index'], p['source_index']), []).append(p)
                fspans.append(tuple(p['fl_span'])); sspans.append(tuple(p['source_span']))
            assert len(fspans) == len(set(fspans)) and len(sspans) == len(set(sspans))
            edges = {(e['fl_index'], e['source_index']) for e in a['edges']}
            assert edges == {key for key, pairs in supports.items() if len(pairs) >= 2 or any(p['basis'] in ('frozen_anchor', 'experimental_alias') for p in pairs)}
            assert a['linked_fl_atoms'] == len({f for f, s in edges})
            assert a['minimum_links_met'] == (a['linked_fl_atoms'] >= 3)
        for field, a, right in [('retrieved_edges', top, correct), ('conditional_edges', next(a for a in ranked if a['source_id'] == r['source_id']), True)]:
            edges = {(e['fl_index'], e['source_index']) for e in a['edges']}
            truth = {(e['fl_index'], e['source_index']) for e in r['edges']}
            counts = row[field]
            assert counts['correct'] == (len(edges & truth) if right else 0)
            assert counts['proposed'] == len(edges) and counts['reference'] == len(truth)
        absent = [a for a in ranked if docs[a['source_id']]['source_group'] != r['group']]
        assert row['source_absent']['top'] == absent[0]
        am = absent[0]['strength']-absent[1]['strength']
        assert row['source_absent']['false_admission'] == (am > 1e-9 and absent[0]['minimum_links_met'] and absent[0]['strength'] >= row['threshold'])
        orders = permutations[r['group']]
        assert len(orders) == 20 and all(sorted(o) == list(range(len(fa))) and o != list(range(len(fa))) for o in orders)
        assert len(row['shuffle']['strengths']) == 20
        assert row['shuffle']['exceed_or_equal_observed'] == sum(s >= top['strength'] for s in row['shuffle']['strengths'])
    for summary in report['summaries']:
        assert summary == summarize(report['results'], summary['split'], summary['variant'])
        if summary['split'] == 'fresh':
            assert (summary['selected'], summary['available'], summary['missing']) == (2, 1, 1)
            assert summary['selected_sample_alignment_recall'] is None
            assert summary['source_absent_evaluated'] == 1 and not summary['reference_coverage_complete']
    r = refs['models_magic']
    expected = audit_aliases(docs[r['fl_id']]['text'], docs[r['source_id']]['text'], r['edges'])
    assert report['alias_audit']['observations'] == expected
    regression = json.loads((out/'synthetic_regression.json').read_text())
    assert len(regression) == 48 and all(r['split'] == 'development_regression' and not r['gate']['active'] for r in regression)
    assert all(all(n == 0 for n in r['changes'].values()) for r in regression)
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial', '000004_kamri_precision_mass']:
        old = ROOT/'runs'/oldid
        receipt = json.loads((old/'manifest.json').read_text())
        for field, base in [('code_hashes', ROOT), ('input_hashes', ROOT), ('output_hashes', old), ('artifact_hashes', old)]:
            for path, sha in receipt.get(field, {}).items():
                if field == 'input_hashes' and oldid.startswith('000001'):
                    doc = json.loads((ROOT/'data/normalized'/f'{path}.json').read_text())
                    assert digest(doc['text'].encode()) == sha
                else:
                    assert digest((base/path).read_bytes()) == sha, path
        previous.append({'run_id': oldid, 'manifest_sha256': digest((old/'manifest.json').read_bytes())})
    verification = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
        'result_rows': 33, 'variants': 3, 'fresh_selected': 2, 'fresh_available': 1, 'fresh_missing': 1,
        'reference_coverage_complete': False, 'previous_runs': previous, 'new_supported_lexical_entries': 0,
        'checks': ['saved input/raw/code/output hashes', 'query-only gate and experimental prediction origins',
                   'alias conflicts/presence retained', 'token offsets, one-to-one paths and edge support',
                   'development-only threshold calibration', 'unavailable references never become zero recall',
                   'nonidentity shared controls', '48 synthetic development regressions', 'unchanged experiments 1–4']}
    dump_json(ROOT/'reports/000005_verification.json', verification)
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
