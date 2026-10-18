"""Independently audit order objectives, calibration, controls and historical archives."""
from collections import Counter
from functools import lru_cache
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.editorial_v7 import EditorialScoreCache
from fl_decipher.experiment_v7 import read
from fl_decipher.evaluation_v9 import aggregate, comparisons, validate, panel_rows
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, protected_groups
from fl_decipher.register_v5 import ALIASES
from fl_decipher.synthetic_v9 import generate
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes, check_pairs
from verify_editorial_v7 import check_metrics

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=200000)
def objective_matrix(ps, words):
    """Independent full-matrix implementation; unknown source content is collapsed."""
    n, m = len(ps), len(words)
    table = [[0.]*(m+1) for _ in range(n+1)]
    for i in range(n+1):
        table[i][0] = -.75*i
    for j in range(m+1):
        table[0][j] = -.75*j
    for i in range(n):
        for j in range(m):
            diagonal = (.5-abs((i+.5)/n-(j+.5)/m)) if ps[i] is None else (2. if ps[i] == words[j] else -2.)
            table[i+1][j+1] = max(table[i][j]+diagonal, table[i+1][j]-.75, table[i][j+1]-.75)
    return table[-1][-1]


def check_quality(q, fa, sa, ps):
    covered = set(); objective = 0.
    for block in q['blocks']:
        assert not covered.intersection(block['fl_atoms'])
        covered.update(block['fl_atoms'])
        predicted = tuple(p['prediction'] for i in block['fl_atoms'] for p in ps[i])
        vocabulary = set(predicted)-{None}
        words = tuple(t.normalized if t.normalized in vocabulary else None for i in block['source_atoms'] for t in sa[i].tokens)
        score = objective_matrix(predicted, words)
        assert abs(score-block['objective']) < 1e-12
        assert block['fl_tokens'] == len(predicted) and block['source_tokens'] == len(words)
        objective += score
    total = sum(len(a.tokens) for a in fa)
    coverage = sum(len(fa[i].tokens) for i in covered)
    upper = sum(2. if p['prediction'] is not None else .5 for row in ps for p in row)
    penalty = -.75*(total-coverage)
    raw = (objective+penalty)/upper if upper else 0.
    assert q['covered_query_tokens'] == coverage and q['uncovered_query_tokens'] == total-coverage and q['total_query_tokens'] == total
    for key, value in [('upper_bound', upper), ('block_objective_sum', objective), ('uncovered_query_penalty', penalty),
                       ('adjusted_objective', objective+penalty), ('raw_quality', raw), ('quality', min(1., max(0., raw)))]:
        assert abs(q[key]-value) < 1e-12, key


def base_view(a):
    return {k: v for k, v in a.items() if k not in ('base_strength', 'order_quality', 'factor_quality')} | {'strength': a['base_strength']}



def independent_factor(q, fa, ps, order, coverage):
    ids = {i for b in q['blocks'] for i in b['fl_atoms']}
    uc = sum(2. if p['prediction'] is not None else .5 for i in ids for p in ps[i])
    assert abs(q['covered_upper_bound']-uc) < 1e-12
    numerator = q['block_objective_sum'] if order else uc
    penalty = -.75*q['uncovered_query_tokens'] if coverage else 0.
    denominator = q['upper_bound'] if coverage else uc
    raw = (numerator+penalty)/denominator if denominator else 0.
    value = min(1., max(0., raw)) if order or coverage else 1.
    return {'quality': value, 'raw_quality': raw if order or coverage else 1., 'numerator': numerator,
            'penalty': penalty, 'denominator': denominator, 'order': order, 'coverage': coverage}


def old_base_view(a):
    return {k: v for k, v in a.items() if k not in ('base_strength', 'order_quality', 'order_applied')} | {'strength': a['base_strength']}

def main():
    out = ROOT/'runs/000009_kamri_coverage_negatives'
    manifest = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_coverage_v9.json'); bench = read(ROOT/'benchmarks/kamri_coverage_v9.json')
    docs = validate(ROOT, bench, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
    refs = {r['case_id']: r for r in bench['records']}
    report, raw = read(out/'report.json'), read(out/'raw_scores.json')
    ps, gates, orders = read(out/'predictions.json'), read(out/'gates.json'), read(out/'permutations.json')
    thresholds, details = read(out/'thresholds.json'), read(out/'shuffle_details.json')
    lexicon = read(ROOT/cfg['lexicon_path']); rows = report['results']
    assert len(rows) == len(raw) == 6240 and len(report['summaries']) == 408
    assert {(r['case_id'], r['variant']) for r in rows} == {(cid, v['id']) for cid in refs for v in cfg['variants']}
    assert report['fresh_world_denominator'] == report['calibration_world_denominator'] == 32
    assert report['fresh_condition_denominator'] == report['calibration_condition_denominator'] == 384
    assert report['fresh_real_source_works'] == report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    assert read(out/'calibration_scores.json') == raw[:3152]
    assert all(r['split'] in ('real_development', 'calibration') for r in raw[:3152])
    assert all(r['split'] in ('real_audit', 'fresh') for r in raw[3152:])
    assert manifest['started_at_utc'] <= manifest['calibration_sealed_at_utc'] <= manifest['finished_at_utc']
    assert manifest['calibration_thresholds_sha256'] == digest((out/'thresholds.json').read_bytes())
    assert report['thresholds'] == thresholds == read(out/'summary.json')['thresholds']
    for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
        for v in cfg['variants']:
            maximum = max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id'] for a in r['rankings']
                          if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))
            assert thresholds[dataset][v['id']] == maximum+1e-6
    cal_texts = {docs[r['fl_id']]['text'] for r in refs.values() if r['split'] == 'calibration'}
    fresh_texts = {docs[r['fl_id']]['text'] for r in refs.values() if r['split'] == 'fresh'}
    assert not cal_texts.intersection(fresh_texts)
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
                    assert p['baseline_prediction'] == original['prediction'] and p['state'] == 'experimental_single_work_register_hypothesis'
        count = 0 if ref['split'] == 'calibration' else 10
        identity = list(range(len(fa)))
        assert len(orders[cid]) == count and all(sorted(o) == identity and o != identity for o in orders[cid])
        for background, shuffled in details[cid].items():
            assert len(shuffled) == count
            for candidates in shuffled:
                assert {a['source_id'] for a in candidates} == set(ref['candidate_ids'])
                for a in candidates:
                    check_quality(a['order_quality'], fa, atoms[a['source_id']], ps[cid])
        if ref['dataset'] == 'synthetic':
            packet = read(ROOT/ref['packet_path'])
            assert packet == generate(ref['seed'], ref['density'], ref['extent'], ref['family'], lexicon)
            assert packet['fl_text'] == docs[ref['fl_id']]['text']
            assert packet['candidate_texts'] == [docs[k]['text'] for k in ref['candidate_ids']]
            assert ref['source_id'] == ref['candidate_ids'][packet['answer_index']]
            for k in ('edges', 'token_pairs', 'fl_token_ids', 'source_token_ids', 'unavailable_query_uids', 'candidate_roles'):
                assert ref[k] == packet[k]
            assert not active
            emitted = sum(p['prediction'] is not None for row in ps[cid] for p in row)
            assert emitted == (12 if ref['density'] == 'normal' else 0)
            available = {p['uid'] for p in ref['token_pairs']}
            unavailable = set(ref['unavailable_query_uids'])
            assert available.isdisjoint(unavailable)
            assert available | unavailable == {t['uid'] for t in ref['fl_token_ids']}
            for t in ref['fl_token_ids']:
                assert any([x.start, x.end] == t['span'] for x in fa[t['atom_index']].tokens)
            sa = atoms[ref['source_id']]
            for t in ref['source_token_ids']:
                assert any([x.start, x.end] == t['span'] for x in sa[t['atom_index']].tokens)
    for oldrow, row in zip(raw, rows, strict=True):
        assert all(row[k] == v for k, v in oldrow.items())
        cid = row['case_id']; ref = refs[cid]; fa = atoms[ref['fl_id']]
        variant = next(v for v in cfg['variants'] if v['id'] == row['variant'])
        assert row['background'] == variant['background'] and row['order'] == variant['order'] and row['coverage'] == variant['coverage']
        bg = next(b for b in cfg['backgrounds'] if b['id'] == row['background'])
        ranked = row['rankings']
        assert {a['source_id'] for a in ranked} == set(ref['candidate_ids'])
        assert ranked == sorted(ranked, key=lambda a: (-a['strength'], a['source_id']))
        assert row['threshold'] == thresholds[row['dataset']][row['variant']]
        top = ranked[0]; margin = top['strength']-ranked[1]['strength']; correct = top['source_id'] == ref['source_id']
        assert row['candidate_margin'] == margin and row['top_work_correct'] == correct
        assert row['unique_correct_top1'] == (correct and margin > 1e-9)
        assert row['admitted'] == (top['minimum_links_met'] and margin > 1e-9 and top['strength'] >= row['threshold'])
        assert row['correct_source_rank'] == next(i+1 for i, a in enumerate(ranked) if a['source_id'] == ref['source_id'])
        for a in ranked:
            sa = atoms[a['source_id']]; q = a['order_quality']
            check_quality(q, fa, sa, ps[cid])
            f = independent_factor(q, fa, ps[cid], row['order'], row['coverage'])
            assert a['factor_quality'] == f and a['strength'] <= a['base_strength']+1e-12
            assert a['strength'] == a['base_strength']*f['quality']
            assert [(b['fl_atoms'], b['source_atoms']) for b in q['blocks']] == [(b['fl_atoms'], b['source_atoms']) for b in a['blocks']]
            prep = PreparedSource(sa, units[a['source_id']]); cache = EditorialScoreCache(fa, prep, cfg, ps[cid], bg)
            allowed = set()
            for b in a['blocks']:
                fi, si = tuple(b['fl_atoms']), tuple(b['source_atoms'])
                assert b['fl_spans'] == [[fa[i].start, fa[i].end] for i in fi]
                assert b['source_spans'] == [[sa[i].start, sa[i].end] for i in si]
                allowed.update((f, s) for f in fi for s in si)
                start = next(j for j, block in enumerate(prep.blocks[b['source_effective_units']]) if block.atoms == si)
                assert abs(cache.row(fi, b['source_effective_units'], 'lexical')[start]-b['similarity']) < 1e-12
            check_pairs(a['token_pairs'], fa, sa, ps[cid], allowed)
            supports = {}
            for p in a['token_pairs']:
                supports.setdefault((p['fl_index'], p['source_index']), []).append(p)
            expected = {key for key, pairs in supports.items() if len(pairs) >= 2 or any(p['basis'] in ('frozen_anchor', 'experimental_alias') for p in pairs)}
            assert {(e['fl_index'], e['source_index']) for e in a['edges']} == expected
            assert a['linked_fl_atoms'] == len({f for f, s in expected}) and a['minimum_links_met'] == (a['linked_fl_atoms'] >= 3)
        conditional = next(a for a in ranked if a['source_id'] == ref['source_id'])
        check_metrics(row['retrieved_edges'], top['edges'], ref['edges'], correct)
        check_metrics(row['conditional_edges'], conditional['edges'], ref['edges'], True)
        if ref['dataset'] == 'synthetic':
            check_metrics(row['retrieved_tokens'], top['token_pairs'], ref['token_pairs'], correct, True)
            check_metrics(row['conditional_tokens'], conditional['token_pairs'], ref['token_pairs'], True, True)
        else:
            assert row['retrieved_tokens'] is None and row['conditional_tokens'] is None
        absent = [a for a in ranked if (docs[a['source_id']]['source_group'] != ref['group'] if ref['dataset'] == 'real' else a['source_id'] != ref['source_id'])]
        am = absent[0]['strength']-absent[1]['strength']
        assert row['source_absent']['top'] == absent[0] and row['source_absent']['margin'] == am
        assert row['source_absent']['false_admission'] == (absent[0]['minimum_links_met'] and am > 1e-9 and absent[0]['strength'] >= row['threshold'])
        strengths = [max(a['base_strength']*independent_factor(a['order_quality'], fa, ps[cid], row['order'], row['coverage'])['quality'] for a in candidates) for candidates in details[cid][row['background']]]
        assert row['shuffle']['strengths'] == strengths and row['shuffle']['repetitions'] == len(orders[cid])
        assert row['shuffle']['unique_orders'] == len({tuple(o) for o in orders[cid]})
        assert row['shuffle']['exceed_or_equal_observed'] == sum(s >= top['strength'] for s in strengths)
        tied = [a['source_id'] for a in ranked if top['strength']-a['strength'] <= 1e-9]
        assert row['maximum_score_sources'] == tied and row['maximum_set_size'] == len(tied)
        assert row['correct_in_maximum_set'] == (ref['source_id'] in tied)
        assert row['top_score_tie'] == (len(tied) > 1) and row['all_zero_tie'] == all(a['strength'] == 0. for a in ranked)
    paired = {(r['case_id'], r['background'], r['order'], r['coverage']): r for r in rows}
    for r in rows:
        base = paired[r['case_id'], r['background'], False, False]
        assert {a['source_id']: base_view(a) for a in r['rankings']} == {a['source_id']: base_view(a) for a in base['rankings']}
        assert r['conditional_edges'] == base['conditional_edges'] and r['conditional_tokens'] == base['conditional_tokens']
    for s in report['summaries']:
        own = [r for r in rows if r['variant'] == s['variant']]; panel = s['panel']
        selected = panel_rows(own, panel)
        assert s == aggregate(selected, panel, s['variant'])
    assert read(out/'summary.json')['summaries'] == report['summaries']
    assert report['comparisons'] == read(out/'comparisons.json') == comparisons(rows)
    assert len(report['comparisons']['matched_factor_contrasts']) == 3072
    oldrows = read(ROOT/'runs/000008_kamri_order_admission/report.json')['results']
    for r in rows:
        if r['dataset'] != 'real' or r['order'] != r['coverage']:
            continue
        old = next(x for x in oldrows if x['case_id'] == r['case_id'] and x['background'] == r['background'] and x['order'] == r['order'])
        assert [base_view(a) for a in r['rankings']] == [old_base_view(a) for a in old['rankings']]
        assert [a['strength'] for a in r['rankings']] == [a['strength'] for a in old['rankings']]
        assert r['threshold'] == old['threshold'] and r['admitted'] == old['admitted']
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial',
                  '000004_kamri_precision_mass', '000005_kamri_scoped_register', '000006_kamri_correspondence_audit', '000007_kamri_editorial_robustness', '000008_kamri_order_admission']:
        check_hashes(ROOT/'runs'/oldid)
        previous.append({'run_id': oldid, 'manifest_sha256': digest((ROOT/'runs'/oldid/'manifest.json').read_bytes())})
    receipt = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'result_rows': 6240, 'variants': 8, 'fresh_conditions': 384, 'fresh_independent_worlds': 32,
               'calibration_conditions': 384, 'calibration_independent_worlds': 32,
               'real_development_queries': 12, 'new_supported_lexical_entries': 0, 'previous_runs': previous,
               'checks': ['input/raw/code/output hashes', 'generated seeds/conditions/available and unavailable identity spans',
                          'frozen predictions and aliases; zero anchor intervention', 'calibration seal and calibration-only thresholds',
                          'independent full-matrix DP and factor formula including coverage bounds',
                          'all candidate paths unchanged across four factor combinations', 'all rankings, ties, metrics, admissions and absent controls',
                          'all actual shuffled qualities/maxima', 'all 408 summaries and 3072 matched contrasts',
                          'real both-off and both-on exactly match v8 strengths/decisions', 'experiments 1–8 unchanged']}
    dump_json(ROOT/'reports/000009_verification.json', receipt)
    import json
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
