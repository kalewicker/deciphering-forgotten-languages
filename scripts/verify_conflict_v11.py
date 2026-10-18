"""Independently audit order objectives, calibration, controls and historical archives."""
from collections import Counter
from functools import lru_cache
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.editorial_v7 import EditorialScoreCache
from fl_decipher.experiment_v7 import read
from fl_decipher.evaluation_v11 import aggregate, comparisons, validate, panel_rows
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, protected_groups
from fl_decipher.register_v5 import ALIASES
from fl_decipher.synthetic_v11 import generate
from fl_decipher.content_v10 import CONTENT_FORMS
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes, check_pairs
from verify_editorial_v7 import check_metrics

ROOT = Path(__file__).resolve().parents[1]


from verify_content_v10 import check_evidence, independent_mode, base_view


def check_panel_truth(packet, ps, fa, sa):
    """Audit perturbations against emitted spans and unchanged English identities."""
    fi = {x['uid']: x for x in packet['fl_token_ids']}
    si = {x['uid']: x for x in packet['source_token_ids']}
    by_span = {tuple(p['span']): p for row in ps for p in row}
    content = packet['content_truth']
    assert {x['uid'] for x in content} == set(packet['content_query_uids'])
    assert len(content) == 6*packet['density']
    changed = [x for x in content if x['changed']]
    expected_changes = 0 if packet['corruption'] == 'clean' else 6 if packet['corruption'].endswith('_one') else 18
    assert len(changed) == expected_changes
    words = list(CONTENT_FORMS)
    for x in content:
        f = fi[x['uid']]; p = by_span[tuple(f['span'])]
        selected = packet['corruption'].endswith('_all') or (packet['corruption'].endswith('_one') and
                    f['span'] == [fa[f['atom_index']].tokens[packet['probe_positions'][f['atom_index']][0]].start,
                                  fa[f['atom_index']].tokens[packet['probe_positions'][f['atom_index']][0]].end])
        assert x['changed'] == selected and x['fl_span'] == f['span']
        truth = x['truth_word']
        expected = None if selected and packet['corruption'].startswith('omit') else words[(words.index(truth)+1)%3] if selected else truth
        assert x['expected_prediction'] == expected == p['prediction']
        assert x['surface'] == p['form']
        if expected is not None:
            assert p['form'] == CONTENT_FORMS[expected]
        if x['uid'] in si:
            s = si[x['uid']]
            token = next(t for t in sa[s['atom_index']].tokens if [t.start, t.end] == s['span'])
            assert token.normalized == truth
            assert x['uid'] in {p['uid'] for p in packet['token_pairs']}
        else:
            assert x['uid'] in packet['unavailable_query_uids']
    known = 6*packet['density'] - (expected_changes if packet['corruption'].startswith('omit') else 0)
    assert sum(p['prediction'] in CONTENT_FORMS for row in ps for p in row) == known
    assert sum(p['prediction'] is not None for row in ps for p in row) == 12+known
    for text, agreement in zip(packet['candidate_texts'], packet['candidate_content_agreements'], strict=True):
        ca = sentences(text); known = matched = 0
        for x in content:
            if x['uid'] in si and x['expected_prediction'] is not None:
                s = si[x['uid']]
                j = next(i for i, t in enumerate(sa[s['atom_index']].tokens) if [t.start, t.end] == s['span'])
                known += 1
                matched += ca[s['atom_index']].tokens[j].normalized == x['expected_prediction']
        assert agreement == {'known_content_predictions': known, 'matches_at_truth_positions': matched}
    if packet['family'] == 'content_renamed':
        for i, text in enumerate(packet['candidate_texts']):
            if i != packet['answer_index']:
                assert all(t.normalized not in CONTENT_FORMS for a in sentences(text) for t in a.tokens)
    else:
        lure = sentences(packet['candidate_texts'][packet['candidate_roles'].index('prediction_lure_1')])
        content_by_uid = {x['uid']: x for x in content}
        for uid, s in si.items():
            if uid in content_by_uid:
                token_index = next(i for i, t in enumerate(sa[s['atom_index']].tokens) if [t.start, t.end] == s['span'])
                word = lure[s['atom_index']].tokens[token_index].normalized
                prediction = content_by_uid[uid]['expected_prediction']
                assert word == prediction if prediction is not None else word not in CONTENT_FORMS


def main():
    out = ROOT/'runs/000011_kamri_anchor_conflicts'
    manifest = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_conflict_v11.json'); bench = read(ROOT/'benchmarks/kamri_conflict_v11.json')
    docs = validate(ROOT, bench, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
    refs = {r['case_id']: r for r in bench['records']}
    report, raw = read(out/'report.json'), read(out/'raw_scores.json')
    ps, gates, orders = read(out/'predictions.json'), read(out/'gates.json'), read(out/'permutations.json')
    thresholds, details = read(out/'thresholds.json'), read(out/'shuffle_details.json')
    lexicon = read(ROOT/cfg['lexicon_path']); rows = report['results']
    assert len(rows) == len(raw) == 12384 and len(report['summaries']) == 520
    assert {(r['case_id'], r['variant']) for r in rows} == {(cid, v['id']) for cid in refs for v in cfg['variants']}
    assert report['fresh_world_denominator'] == report['calibration_world_denominator'] == 32
    assert report['fresh_condition_denominator'] == report['calibration_condition_denominator'] == 768
    assert report['fresh_real_source_works'] == report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    assert read(out/'calibration_scores.json') == raw[:6224]
    assert all(r['split'] in ('real_development', 'calibration') for r in raw[:6224])
    assert all(r['split'] in ('real_audit', 'fresh') for r in raw[6224:])
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
            assert packet == generate(ref['seed'], ref['density'], ref['corruption'], ref['extent'], ref['family'], lexicon)
            assert packet['fl_text'] == docs[ref['fl_id']]['text']
            assert packet['candidate_texts'] == [docs[k]['text'] for k in ref['candidate_ids']]
            assert ref['source_id'] == ref['candidate_ids'][packet['answer_index']]
            for k in ('edges', 'token_pairs', 'fl_token_ids', 'source_token_ids', 'unavailable_query_uids', 'candidate_roles', 'content_query_uids', 'probe_positions', 'content_truth', 'candidate_content_agreements'):
                assert ref[k] == packet[k]
            assert not active
            check_panel_truth(packet, ps[cid], fa, atoms[ref['source_id']])
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
    assert len(report['comparisons']['matched_mode_contrasts']) == 6144
    assert len(report['comparisons']['paired_corruption_contrasts']) == 4096
    # Corruption cannot change ground-truth source, identities, or fully renamed negatives.
    paired_refs = {(r['seed'], r['density'], r['corruption'], r['extent'], r['family']): r for r in refs.values() if r['dataset'] == 'synthetic'}
    for r in paired_refs.values():
        if r['density'] != 3:
            continue
        clean = paired_refs[r['seed'], 3, 'clean', r['extent'], r['family']]
        assert docs[r['source_id']]['text'] == docs[clean['source_id']]['text']
        for k in ('source_token_ids', 'unavailable_query_uids', 'content_query_uids', 'probe_positions', 'candidate_roles'):
            assert r[k] == clean[k]
        assert [(p['uid'], p['source_span'], p['fl_index'], p['source_index']) for p in r['token_pairs']] == [(p['uid'], p['source_span'], p['fl_index'], p['source_index']) for p in clean['token_pairs']]
        if r['family'] == 'content_renamed':
            assert [docs[k]['text'] for k in r['candidate_ids']] == [docs[k]['text'] for k in clean['candidate_ids']]
    oldrows = read(ROOT/'runs/000010_kamri_content_capacity/report.json')['results']
    old_by_key = {(r['case_id'], r['variant']): r for r in oldrows if r['dataset'] == 'real'}
    for r in rows:
        if r['dataset'] != 'real':
            continue
        old = old_by_key[r['case_id'], r['variant']]
        assert r['rankings'] == old['rankings']
        for k in ('threshold', 'admitted', 'pooled_threshold', 'pooled_admitted', 'source_absent', 'pooled_source_absent_false_admission', 'conditional_edges'):
            assert r[k] == old[k]
    del oldrows, old_by_key
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial',
                  '000004_kamri_precision_mass', '000005_kamri_scoped_register', '000006_kamri_correspondence_audit', '000007_kamri_editorial_robustness', '000008_kamri_order_admission', '000009_kamri_coverage_negatives', '000010_kamri_content_capacity']:
        check_hashes(ROOT/'runs'/oldid)
        previous.append({'run_id': oldid, 'manifest_sha256': digest((ROOT/'runs'/oldid/'manifest.json').read_bytes())})
    receipt = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'result_rows': 12384, 'variants': 8, 'fresh_conditions': 768, 'fresh_independent_worlds': 32,
               'fresh_primary_conditions': 384, 'fresh_stress_conditions': 384,
               'calibration_conditions': 768, 'calibration_independent_worlds': 32,
               'real_development_queries': 12, 'new_supported_lexical_entries': 0, 'previous_runs': previous,
               'checks': ['input/raw/code/output hashes', 'generated panels and available/unavailable identities',
                          'unchanged prediction policy, aliases, per-occurrence corruption/omission expectations and retained truth identities',
                          'two preregistered calibration policies sealed before fresh/audit',
                          'independent full-matrix positional and content sequence objectives and evidence spans',
                          'same candidate paths across four modes', 'all rankings/ties/metrics and both admission policies',
                          'all actual shuffled candidate evidence/maxima', 'all 520 summaries, 6144 mode and 4096 paired corruption contrasts',
                          'all eight real ranking paths and admission policies match v10', 'experiments 1–10 unchanged']}
    dump_json(ROOT/'reports/000011_verification.json', receipt)
    import json
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
