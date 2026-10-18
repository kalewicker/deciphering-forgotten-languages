"""Independently audit order objectives, calibration, controls and historical archives."""
from collections import Counter
from functools import lru_cache
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.editorial_v7 import EditorialScoreCache
from fl_decipher.experiment_v7 import read
from fl_decipher.evaluation_v10 import aggregate, comparisons, validate, panel_rows
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, protected_groups
from fl_decipher.register_v5 import ALIASES
from fl_decipher.synthetic_v10 import generate
from fl_decipher.content_v10 import CONTENT_FORMS
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes, check_pairs
from verify_editorial_v7 import check_metrics

ROOT = Path(__file__).resolve().parents[1]


from verify_coverage_v9 import check_quality as check_positional


@lru_cache(maxsize=200000)
def lcs_matrix(a, b):
    table = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            table[i+1][j+1] = table[i][j]+1 if x == y else max(table[i+1][j], table[i][j+1])
    return table[-1][-1]


def check_evidence(e, fa, sa, ps):
    q = e['positional']; c = e['content']
    check_positional(q, fa, sa, ps)
    covered = {i for b in q['blocks'] for i in b['fl_atoms']}
    upper = sum(2. if p['prediction'] is not None else .5 for i in covered for p in ps[i])
    assert q['covered_upper_bound'] == upper
    assert [(b['fl_atoms'], b['source_atoms']) for b in q['blocks']] == [(b['fl_atoms'], b['source_atoms']) for b in c['blocks']]
    denominator = bag = ordered = 0
    for b in c['blocks']:
        qp = [{'word': p['prediction'], 'span': p['span'], 'atom_index': i} for i in b['fl_atoms'] for p in ps[i] if p['prediction'] in CONTENT_FORMS]
        sp = [{'word': t.normalized, 'span': [t.start, t.end], 'atom_index': i} for i in b['source_atoms'] for t in sa[i].tokens if t.normalized in CONTENT_FORMS]
        assert b['query_content'] == qp and b['source_content'] == sp
        qw, sw = tuple(x['word'] for x in qp), tuple(x['word'] for x in sp)
        bm = sum(min(qw.count(w), sw.count(w)) for w in CONTENT_FORMS)
        om = lcs_matrix(qw, sw)
        assert b['bag_matches'] == bm and b['ordered_matches'] == om
        denominator += len(qw); bag += bm; ordered += om
    assert c['covered_content_predictions'] == denominator
    assert c['total_query_content_predictions'] == sum(p['prediction'] in CONTENT_FORMS for row in ps for p in row)
    assert c['bag_matches'] == bag and c['ordered_matches'] == ordered
    assert c['bag_quality'] == (bag/denominator if denominator else 0.)
    assert c['ordered_quality'] == (ordered/denominator if denominator else 0.)
    assert 0 <= c['ordered_quality'] <= c['bag_quality'] <= 1


def independent_mode(e, mode):
    c = e['content']; q = e['positional']
    if mode == 'base':
        return 1.
    if mode == 'positional':
        return min(1., max(0., q['block_objective_sum']/q['covered_upper_bound'])) if q['covered_upper_bound'] else 0.
    return c['bag_quality'] if mode == 'content_bag' else c['ordered_quality']

def base_view(a):
    return {k: v for k, v in a.items() if k not in ('base_strength', 'candidate_evidence', 'mode_quality')} | {'strength': a['base_strength']}



def old_base_view(a):
    return {k: v for k, v in a.items() if k not in ('base_strength', 'order_quality', 'factor_quality')} | {'strength': a['base_strength']}

def main():
    out = ROOT/'runs/000010_kamri_content_capacity'
    manifest = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_content_v10.json'); bench = read(ROOT/'benchmarks/kamri_content_v10.json')
    docs = validate(ROOT, bench, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
    refs = {r['case_id']: r for r in bench['records']}
    report, raw = read(out/'report.json'), read(out/'raw_scores.json')
    ps, gates, orders = read(out/'predictions.json'), read(out/'gates.json'), read(out/'permutations.json')
    thresholds, details = read(out/'thresholds.json'), read(out/'shuffle_details.json')
    lexicon = read(ROOT/cfg['lexicon_path']); rows = report['results']
    assert len(rows) == len(raw) == 9312 and len(report['summaries']) == 480
    assert {(r['case_id'], r['variant']) for r in rows} == {(cid, v['id']) for cid in refs for v in cfg['variants']}
    assert report['fresh_world_denominator'] == report['calibration_world_denominator'] == 32
    assert report['fresh_condition_denominator'] == report['calibration_condition_denominator'] == 576
    assert report['fresh_real_source_works'] == report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    assert read(out/'calibration_scores.json') == raw[:4688]
    assert all(r['split'] in ('real_development', 'calibration') for r in raw[:4688])
    assert all(r['split'] in ('real_audit', 'fresh') for r in raw[4688:])
    assert manifest['started_at_utc'] <= manifest['calibration_sealed_at_utc'] <= manifest['finished_at_utc']
    assert manifest['calibration_thresholds_sha256'] == digest((out/'thresholds.json').read_bytes())
    assert report['thresholds'] == thresholds == read(out/'summary.json')['thresholds']
    for policy in ('primary', 'pooled'):
        for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
            for v in cfg['variants']:
                maximum = max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id']
                              and (policy == 'pooled' or dataset == 'real' or r['family'] == 'content_renamed') for a in r['rankings']
                              if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))
                assert thresholds[policy][dataset][v['id']] == maximum+1e-6
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
                    check_evidence(a['candidate_evidence'], fa, atoms[a['source_id']], ps[cid])
        if ref['dataset'] == 'synthetic':
            packet = read(ROOT/ref['packet_path'])
            assert packet == generate(ref['seed'], ref['density'], ref['extent'], ref['family'], lexicon)
            assert packet['fl_text'] == docs[ref['fl_id']]['text']
            assert packet['candidate_texts'] == [docs[k]['text'] for k in ref['candidate_ids']]
            assert ref['source_id'] == ref['candidate_ids'][packet['answer_index']]
            for k in ('edges', 'token_pairs', 'fl_token_ids', 'source_token_ids', 'unavailable_query_uids', 'candidate_roles', 'content_query_uids', 'probe_positions'):
                assert ref[k] == packet[k]
            assert not active
            emitted = sum(p['prediction'] is not None for row in ps[cid] for p in row)
            assert emitted == 12+6*ref['density']
            assert sum(p['prediction'] in CONTENT_FORMS for row in ps[cid] for p in row) == 6*ref['density']
            roster_spans = {tuple(p['span']) for row in ps[cid] for p in row if p['prediction'] in CONTENT_FORMS}
            assert {t['uid'] for t in ref['fl_token_ids'] if tuple(t['span']) in roster_spans} == set(ref['content_query_uids'])
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
        assert row['background'] == variant['background'] and row['mode'] == variant['mode']
        bg = next(b for b in cfg['backgrounds'] if b['id'] == row['background'])
        ranked = row['rankings']
        assert {a['source_id'] for a in ranked} == set(ref['candidate_ids'])
        assert ranked == sorted(ranked, key=lambda a: (-a['strength'], a['source_id']))
        assert row['threshold'] == thresholds['primary'][row['dataset']][row['variant']]
        top = ranked[0]; margin = top['strength']-ranked[1]['strength']; correct = top['source_id'] == ref['source_id']
        assert row['candidate_margin'] == margin and row['top_work_correct'] == correct
        assert row['unique_correct_top1'] == (correct and margin > 1e-9)
        assert row['admitted'] == (top['minimum_links_met'] and margin > 1e-9 and top['strength'] >= row['threshold'])
        assert row['correct_source_rank'] == next(i+1 for i, a in enumerate(ranked) if a['source_id'] == ref['source_id'])
        for a in ranked:
            sa = atoms[a['source_id']]; e = a['candidate_evidence']; q = e['positional']
            check_evidence(e, fa, sa, ps[cid])
            f = independent_mode(e, row['mode'])
            assert a['mode_quality'] == f and a['strength'] <= a['base_strength']+1e-12
            assert a['strength'] == a['base_strength']*f
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
        pt = thresholds['pooled'][row['dataset']][row['variant']]
        assert row['pooled_threshold'] == pt
        assert row['pooled_admitted'] == (top['minimum_links_met'] and margin > 1e-9 and top['strength'] >= pt)
        assert row['pooled_source_absent_false_admission'] == (absent[0]['minimum_links_met'] and am > 1e-9 and absent[0]['strength'] >= pt)
        assert row['capacity_scope'] == ('primary' if ref.get('family') == 'content_renamed' else 'stress' if ref['dataset'] == 'synthetic' else 'real_development')
        strengths = [max(a['base_strength']*independent_mode(a['candidate_evidence'], row['mode']) for a in candidates) for candidates in details[cid][row['background']]]
        assert row['shuffle']['strengths'] == strengths and row['shuffle']['repetitions'] == len(orders[cid])
        assert row['shuffle']['unique_orders'] == len({tuple(o) for o in orders[cid]})
        assert row['shuffle']['exceed_or_equal_observed'] == sum(s >= top['strength'] for s in strengths)
        tied = [a['source_id'] for a in ranked if top['strength']-a['strength'] <= 1e-9]
        assert row['maximum_score_sources'] == tied and row['maximum_set_size'] == len(tied)
        assert row['correct_in_maximum_set'] == (ref['source_id'] in tied)
        assert row['top_score_tie'] == (len(tied) > 1) and row['all_zero_tie'] == all(a['strength'] == 0. for a in ranked)
    paired = {(r['case_id'], r['background'], r['mode']): r for r in rows}
    for r in rows:
        base = paired[r['case_id'], r['background'], 'base']
        assert {a['source_id']: base_view(a) for a in r['rankings']} == {a['source_id']: base_view(a) for a in base['rankings']}
        assert r['conditional_edges'] == base['conditional_edges'] and r['conditional_tokens'] == base['conditional_tokens']
    for s in report['summaries']:
        own = [r for r in rows if r['variant'] == s['variant']]; panel = s['panel']
        selected = panel_rows(own, panel)
        assert s == aggregate(selected, panel, s['variant'])
    assert read(out/'summary.json')['summaries'] == report['summaries']
    assert report['comparisons'] == read(out/'comparisons.json') == comparisons(rows)
    assert len(report['comparisons']['matched_mode_contrasts']) == 4608
    oldrows = read(ROOT/'runs/000009_kamri_coverage_negatives/report.json')['results']
    for r in rows:
        if r['dataset'] != 'real' or r['mode'] not in ('base', 'positional'):
            continue
        old = next(x for x in oldrows if x['case_id'] == r['case_id'] and x['background'] == r['background'] and x['order'] == (r['mode'] == 'positional') and not x['coverage'])
        assert [base_view(a) for a in r['rankings']] == [old_base_view(a) for a in old['rankings']]
        assert [a['strength'] for a in r['rankings']] == [a['strength'] for a in old['rankings']]
        assert r['threshold'] == old['threshold'] and r['admitted'] == old['admitted']
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial',
                  '000004_kamri_precision_mass', '000005_kamri_scoped_register', '000006_kamri_correspondence_audit', '000007_kamri_editorial_robustness', '000008_kamri_order_admission', '000009_kamri_coverage_negatives']:
        check_hashes(ROOT/'runs'/oldid)
        previous.append({'run_id': oldid, 'manifest_sha256': digest((ROOT/'runs'/oldid/'manifest.json').read_bytes())})
    receipt = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'result_rows': 9312, 'variants': 8, 'fresh_conditions': 576, 'fresh_independent_worlds': 32,
               'fresh_primary_conditions': 192, 'fresh_stress_conditions': 384,
               'calibration_conditions': 576, 'calibration_independent_worlds': 32,
               'real_development_queries': 12, 'new_supported_lexical_entries': 0, 'previous_runs': previous,
               'checks': ['input/raw/code/output hashes', 'generated panels and available/unavailable identities',
                          'unchanged frozen eligibility, predictions, aliases and roster density',
                          'two preregistered calibration policies sealed before fresh/audit',
                          'independent full-matrix positional and content sequence objectives and evidence spans',
                          'same candidate paths across four modes', 'all rankings/ties/metrics and both admission policies',
                          'all actual shuffled candidate evidence/maxima', 'all 480 summaries and 4608 mode contrasts',
                          'real base/positional strengths/decisions match v9', 'experiments 1–9 unchanged']}
    dump_json(ROOT/'reports/000010_verification.json', receipt)
    import json
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
