"""Audit all factorial rows, controlled identities, calibration and earlier archives."""
from collections import Counter
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.editorial_v7 import EditorialScoreCache
from fl_decipher.experiment_v7 import aggregate, comparisons, validate
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, protected_groups
from fl_decipher.register_v5 import ALIASES
from fl_decipher.synthetic_v7 import generate
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes, check_pairs

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def check_metrics(value, proposed, reference, correct, token=False):
    key = (lambda p: (tuple(p['fl_span']), tuple(p['source_span']))) if token else (lambda p: (p['fl_index'], p['source_index']))
    p, r = {key(x) for x in proposed}, {key(x) for x in reference}
    n = len(p & r) if correct else 0
    assert value == {'correct': n, 'proposed': len(p), 'reference': len(r), 'extra': len(p)-n,
                     'precision': n/len(p) if p else None, 'recall': n/len(r) if r else None}


def main():
    out = ROOT/'runs/000007_kamri_editorial_robustness'
    manifest = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_editorial_v7.json'); bench = read(ROOT/'benchmarks/kamri_editorial_v7.json')
    docs = validate(ROOT, bench, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
    refs = {r['case_id']: r for r in bench['records']}
    report, raw = read(out/'report.json'), read(out/'raw_scores.json')
    ps, gates, orders = read(out/'predictions.json'), read(out/'gates.json'), read(out/'permutations.json')
    thresholds = read(out/'thresholds.json'); rows = report['results']
    lexicon = read(ROOT/cfg['lexicon_path'])
    assert len(raw) == len(rows) == 1376
    assert len(report['summaries']) == 224 and report['fresh_world_denominator'] == 8 and report['fresh_condition_denominator'] == 128
    assert report['fresh_real_source_works'] == report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    assert {(r['case_id'], r['variant']) for r in rows} == {(cid, v['id']) for cid in refs for v in cfg['variants']}
    assert read(out/'calibration_scores.json') == raw[:336]
    assert all(r['split'] in ('real_development', 'calibration') for r in raw[:336])
    assert all(r['split'] in ('real_audit', 'fresh') for r in raw[336:])
    assert manifest['calibration_thresholds_sha256'] == digest((out/'thresholds.json').read_bytes())
    assert manifest['started_at_utc'] <= manifest['calibration_sealed_at_utc'] <= manifest['finished_at_utc']
    assert report['thresholds'] == thresholds == read(out/'summary.json')['thresholds']
    for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
        for v in cfg['variants']:
            value = max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id'] for a in r['rankings']
                        if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))+1e-6
            assert thresholds[dataset][v['id']] == value
    cal_texts = {docs[r['fl_id']]['text'] for r in refs.values() if r['split'] == 'calibration'}
    fresh_texts = {docs[r['fl_id']]['text'] for r in refs.values() if r['split'] == 'fresh'}
    assert cal_texts.isdisjoint(fresh_texts)
    for cid, ref in refs.items():
        fa = atoms[ref['fl_id']]
        counts = Counter(t.normalized for a in fa for t in a.tokens if t.normalized in ALIASES)
        active = len(counts) >= 2 and sum(counts.values()) >= 3
        assert gates[cid] == {'active': active, 'distinct_markers': len(counts), 'total_markers': sum(counts.values()), 'counts': dict(counts)}
        for atom, row in zip(fa, ps[cid], strict=True):
            originals = predict(atom, lexicon, cfg['lexicon_rules'])
            for original, p in zip(originals, row, strict=True):
                override = active and p['form'] in ALIASES
                assert p['prediction'] == (ALIASES[p['form']] if override else original['prediction'])
                assert p['span'] == original['span'] and p['form'] == original['form']
                assert p['origin'] == ('registered_alias' if override else 'frozen_v1' if original['prediction'] is not None else 'abstained')
                if override:
                    assert p['baseline_prediction'] == original['prediction']
                    assert p['state'] == 'experimental_single_work_register_hypothesis'
        expected_count = 0 if ref['split'] == 'calibration' else 10
        identity = list(range(len(fa)))
        assert len(orders[cid]) == expected_count
        assert all(sorted(o) == identity and o != identity for o in orders[cid])
        if ref['dataset'] != 'synthetic':
            continue
        packet = read(ROOT/ref['packet_path'])
        assert packet == generate(ref['seed'], ref['mask'], lexicon), cid
        assert packet['fl_text'] == docs[ref['fl_id']]['text']
        assert packet['candidate_texts'] == [docs[k]['text'] for k in ref['candidate_ids']]
        assert ref['source_id'] == ref['candidate_ids'][packet['answer_index']]
        for k in ('edges', 'token_pairs', 'fl_token_ids', 'source_token_ids', 'conflicted_fl_spans', 'edits'):
            assert ref[k] == packet[k]
        assert not active
        sa = atoms[ref['source_id']]
        for t in ref['fl_token_ids']:
            assert any([x.start, x.end] == t['span'] for x in fa[t['atom_index']].tokens)
        for t in ref['source_token_ids']:
            assert any([x.start, x.end] == t['span'] for x in sa[t['atom_index']].tokens)
        for span in ref['conflicted_fl_spans']:
            p = next(p for row in ps[cid] for p in row if p['span'] == span)
            assert p['prediction'] == 'and' and p['origin'] == 'frozen_v1'
    for rawrow, row in zip(raw, rows, strict=True):
        cid, vid = row['case_id'], row['variant']; ref = refs[cid]
        assert all(row[k] == v for k, v in rawrow.items())
        assert row['threshold'] == thresholds[row['dataset']][vid]
        ranked = row['rankings']; fa = atoms[ref['fl_id']]
        assert {a['source_id'] for a in ranked} == set(ref['candidate_ids'])
        assert ranked == sorted(ranked, key=lambda a: (-a['strength'], a['source_id']))
        margin = ranked[0]['strength']-ranked[1]['strength']
        correct = ranked[0]['source_id'] == ref['source_id']
        assert row['candidate_margin'] == margin and row['top_work_correct'] == correct
        assert row['unique_correct_top1'] == (correct and margin > 1e-9)
        assert row['admitted'] == (ranked[0]['minimum_links_met'] and margin > 1e-9 and ranked[0]['strength'] >= row['threshold'])
        assert row['correct_source_rank'] == next(i+1 for i, a in enumerate(ranked) if a['source_id'] == ref['source_id'])
        for a in ranked:
            sa = atoms[a['source_id']]
            prep = PreparedSource(sa, units[a['source_id']])
            variant = next(v for v in cfg['variants'] if v['id'] == vid)
            cache = EditorialScoreCache(fa, prep, cfg, ps[cid], variant)
            allowed = set()
            for block in a['blocks']:
                fi, si = tuple(block['fl_atoms']), tuple(block['source_atoms'])
                assert block['fl_spans'] == [[fa[i].start, fa[i].end] for i in fi]
                assert block['source_spans'] == [[sa[i].start, sa[i].end] for i in si]
                allowed.update((f, s) for f in fi for s in si)
                size = block['source_effective_units']
                start = next(j for j, b in enumerate(prep.blocks[size]) if b.atoms == si)
                assert abs(cache.row(fi, size, 'lexical')[start]-block['similarity']) < 1e-12
            check_pairs(a['token_pairs'], fa, sa, ps[cid], allowed)
            support = {}
            for p in a['token_pairs']:
                support.setdefault((p['fl_index'], p['source_index']), []).append(p)
            edges = {key for key, pairs in support.items() if len(pairs) >= 2 or any(p['basis'] in ('frozen_anchor', 'experimental_alias') for p in pairs)}
            assert edges == {(e['fl_index'], e['source_index']) for e in a['edges']}
            assert a['linked_fl_atoms'] == len({f for f, s in edges})
            assert a['minimum_links_met'] == (a['linked_fl_atoms'] >= 3)
        conditional = next(a for a in ranked if a['source_id'] == ref['source_id'])
        for field, a, right in [('retrieved_edges', ranked[0], correct), ('conditional_edges', conditional, True)]:
            check_metrics(row[field], a['edges'], ref['edges'], right)
        if ref['dataset'] == 'synthetic':
            check_metrics(row['retrieved_tokens'], ranked[0]['token_pairs'], ref['token_pairs'], correct, True)
            check_metrics(row['conditional_tokens'], conditional['token_pairs'], ref['token_pairs'], True, True)
        else:
            assert row['retrieved_tokens'] is None and row['conditional_tokens'] is None
        absent = [a for a in ranked if (docs[a['source_id']]['source_group'] != ref['group'] if ref['dataset'] == 'real' else a['source_id'] != ref['source_id'])]
        am = absent[0]['strength']-absent[1]['strength']
        assert row['source_absent']['top'] == absent[0] and row['source_absent']['margin'] == am
        assert row['source_absent']['false_admission'] == (absent[0]['minimum_links_met'] and am > 1e-9 and absent[0]['strength'] >= row['threshold'])
        s = row['shuffle']
        assert len(s['strengths']) == s['repetitions'] == len(orders[cid])
        assert s['unique_orders'] == len({tuple(o) for o in orders[cid]})
        assert s['exceed_or_equal_observed'] == sum(x >= ranked[0]['strength'] for x in s['strengths'])
    for summary in report['summaries']:
        own = [r for r in rows if r['variant'] == summary['variant']]
        panel = summary['panel']
        if panel.startswith('fresh_mask_'):
            selected = [r for r in own if r['split'] == 'fresh' and r['mask'] == int(panel.rsplit('_', 1)[1])]
        elif panel.startswith('fresh_world_'):
            selected = [r for r in own if r['split'] == 'fresh' and r['seed'] == int(panel.rsplit('_', 1)[1])]
        else:
            selected = [r for r in own if r['split'] == panel]
        assert summary == aggregate(selected, panel, summary['variant'])
    assert report['comparisons'] == read(out/'comparisons.json') == comparisons(rows)
    assert len(report['comparisons']['condition_vs_pristine']) == 960
    assert len(report['comparisons']['matched_scoring_factors']) == 1536
    # Legacy scores/paths exactly reproduce v5 gated predictions, including v6 blocks.
    old5 = read(ROOT/'runs/000005_kamri_scoped_register/report.json')['results']
    old6 = read(ROOT/'runs/000006_kamri_correspondence_audit/report.json')['results']
    for row in rows:
        if row['dataset'] != 'real' or row['variant'] != 'p0_r0_l0':
            continue
        ref = refs[row['case_id']]
        previous = (next(r for r in old5 if r['group'] == ref['group'] and r['variant'] == 'gated_aliases') if ref['split'] == 'real_development'
                    else next(r for r in old6 if r['packet'] == ref['packet'] and r['variant'] == 'gated_aliases'))
        assert row['rankings'] == previous['rankings']
        assert row['conditional_edges'] == previous['conditional_edges'] and row['retrieved_edges'] == previous['retrieved_edges']
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial',
                  '000004_kamri_precision_mass', '000005_kamri_scoped_register', '000006_kamri_correspondence_audit']:
        check_hashes(ROOT/'runs'/oldid)
        previous.append({'run_id': oldid, 'manifest_sha256': digest((ROOT/'runs'/oldid/'manifest.json').read_bytes())})
    receipt = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'result_rows': 1376, 'variants': 8, 'fresh_conditions': 128, 'fresh_independent_worlds': 8,
               'calibration_conditions': 32, 'calibration_independent_worlds': 2, 'real_queries': 12,
               'new_supported_lexical_entries': 0, 'previous_runs': previous,
               'checks': ['saved input/raw/code/output hashes', 'all seeded conditions regenerated without model execution',
                          'occurrence identities and Unicode spans', 'unchanged eligible predictions/query-only aliases',
                          'calibration sealed before fresh scores; thresholds from calibration only', 'token order, origins, uniqueness, edge support',
                          'rankings/admissions and all edge/token counts', 'source-absent controls and shared nonidentity permutations',
                          'all 224 summaries and paired edit/factor contrasts', 'legacy matches v5/v6 scores and paths exactly',
                          'experiments 1–6 remain unchanged']}
    dump_json(ROOT/'reports/000007_verification.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
