"""Check saved experiment evidence and historical archives without rerunning models."""
from collections import Counter
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v6 import validate
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, ScoreCache, protected_groups
from fl_decipher.register_v5 import ALIASES, audit_aliases
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def check_hashes(out):
    manifest = read(out/'manifest.json')
    assert manifest['state'] == 'completed'
    for field, base in [('input_hashes', ROOT), ('code_hashes', ROOT), ('output_hashes', out), ('artifact_hashes', out)]:
        for path, sha in manifest.get(field, {}).items():
            if field == 'input_hashes' and out.name.startswith('000001'):
                doc = read(ROOT/'data/normalized'/f'{path}.json')
                assert digest(doc['text'].encode()) == sha, path
            else:
                assert digest((base/path).read_bytes()) == sha, path
    return manifest


def check_pairs(pairs, fa, sa, ps, allowed):
    f_seen, s_seen = set(), set()
    for p in pairs:
        fi, si = p['fl_index'], p['source_index']
        assert (fi, si) in allowed
        f = next(t for t in fa[fi].tokens if [t.start, t.end] == p['fl_span'])
        s = next(t for t in sa[si].tokens if [t.start, t.end] == p['source_span'])
        item = next(x for x in ps[fi] if x['span'] == p['fl_span'])
        assert item['form'] == f.normalized and p['score'] >= 0
        if p['basis'] in ('frozen_anchor', 'experimental_alias'):
            assert item['prediction'] == s.normalized and p['score'] == 2.
            assert p['anchor_origin'] == item['origin']
            assert (p['basis'] == 'experimental_alias') == (item['origin'] == 'registered_alias')
        else:
            assert p['basis'] == 'positional' and item['prediction'] is None and p['score'] <= .5
        fs, ss = tuple(p['fl_span']), tuple(p['source_span'])
        assert fs not in f_seen and ss not in s_seen
        f_seen.add(fs); s_seen.add(ss)
    # Source and query token offsets must each increase through an ordered path.
    assert [p['fl_span'][0] for p in pairs] == sorted(p['fl_span'][0] for p in pairs)
    assert [p['source_span'][0] for p in pairs] == sorted(p['source_span'][0] for p in pairs)


def main():
    out = ROOT/'runs/000006_kamri_correspondence_audit'
    manifest = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_correspondence_v6.json')
    bench = read(ROOT/'benchmarks/kamri_correspondence_v6.json')
    docs = validate(ROOT, bench, cfg)
    atoms = {k: sentences(d['text']) for k, d in docs.items()}
    units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
    refs = {r['packet']: r for r in bench['records']}
    report = read(out/'report.json')
    rows, ds = read(out/'retrieval.json'), read(out/'diagnostics.json')
    ps, gates, orders = read(out/'predictions.json'), read(out/'gates.json'), read(out/'permutations.json')
    assert report['results'] == rows and report['diagnostics'] == ds and len(rows) == len(ds) == 6
    assert report['fresh_independent_works'] == 0 and report['independent_source_works'] == 1
    assert report['selected_within_article_denominator'] == report['available_within_article_blocks'] == 2
    assert report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    lexicon = read(ROOT/cfg['lexicon_path'])
    for packet, variants in ps.items():
        fa = atoms[refs[packet]['fl_id']]
        counts = Counter(t.normalized for a in fa for t in a.tokens if t.normalized in ALIASES)
        active = len(counts) >= 2 and sum(counts.values()) >= 3
        assert gates[packet] == {'active': active, 'distinct_markers': len(counts), 'total_markers': sum(counts.values()), 'counts': dict(counts)}
        for v, prows in variants.items():
            for atom, prow in zip(fa, prows, strict=True):
                old = predict(atom, lexicon, cfg['lexicon_rules'])
                for p, original in zip(prow, old, strict=True):
                    override = v == 'gated_aliases' and active and p['form'] in ALIASES
                    assert p['span'] == original['span'] and p['form'] == original['form']
                    assert p['prediction'] == (ALIASES[p['form']] if override else original['prediction'])
                    assert p['origin'] == ('registered_alias' if override else 'frozen_v1' if original['prediction'] is not None else 'abstained')
                    if override:
                        assert p['baseline_prediction'] == original['prediction']
                        assert p['state'] == 'experimental_single_work_register_hypothesis'
        identity = list(range(len(fa)))
        assert len(orders[packet]) == 20
        assert all(sorted(o) == identity and o != identity for o in orders[packet])
    for row, d in zip(rows, ds, strict=True):
        packet, variant = row['packet'], row['variant']
        assert (d['packet'], d['variant']) == (packet, variant)
        r = refs[packet]
        fa, sa = atoms[r['fl_id']], atoms[r['source_id']]
        predicted = ps[packet][variant]
        assert row['threshold'] == report['thresholds'][variant] == cfg['thresholds'][variant]
        assert row['query_tokens'] == sum(len(a.tokens) for a in fa)
        assert row['prediction_count'] == sum(p['prediction'] is not None for pr in predicted for p in pr)
        assert row['admission_capacity_met'] == (len(fa) >= 3)
        ranked = row['rankings']
        assert {a['source_id'] for a in ranked} == set(cfg['candidate_ids'])
        assert ranked == sorted(ranked, key=lambda a: (-a['strength'], a['source_id']))
        margin = ranked[0]['strength']-ranked[1]['strength']
        assert row['candidate_margin'] == margin
        assert row['top_work_correct'] == (ranked[0]['source_id'] == r['source_id'])
        assert row['unique_correct_top1'] == (row['top_work_correct'] and margin > 1e-9)
        assert row['admitted'] == (ranked[0]['minimum_links_met'] and margin > 1e-9 and ranked[0]['strength'] >= row['threshold'])
        assert row['correct_source_rank'] == next(i+1 for i, a in enumerate(ranked) if a['source_id'] == r['source_id'])
        for a in ranked:
            target = atoms[a['source_id']]
            allowed = set()
            for block in a['blocks']:
                assert block['fl_spans'] == [[fa[i].start, fa[i].end] for i in block['fl_atoms']]
                assert block['source_spans'] == [[target[i].start, target[i].end] for i in block['source_atoms']]
                allowed.update((f, s) for f in block['fl_atoms'] for s in block['source_atoms'])
            check_pairs(a['token_pairs'], fa, target, predicted, allowed)
            supports = {}
            for p in a['token_pairs']:
                supports.setdefault((p['fl_index'], p['source_index']), []).append(p)
            expected = {key for key, pairs in supports.items() if len(pairs) >= 2 or any(p['basis'] in ('frozen_anchor', 'experimental_alias') for p in pairs)}
            assert {(e['fl_index'], e['source_index']) for e in a['edges']} == expected
            assert a['linked_fl_atoms'] == len({f for f, s in expected})
            assert a['minimum_links_met'] == (a['linked_fl_atoms'] >= 3)
        truth = {(e['fl_index'], e['source_index']) for e in r['edges']}
        conditional = next(a for a in ranked if a['source_id'] == r['source_id'])
        for name, a, correct_source in [('conditional_edges', conditional, True), ('retrieved_edges', ranked[0], row['top_work_correct'])]:
            edges = {(e['fl_index'], e['source_index']) for e in a['edges']}
            counts = row[name]
            correct = len(edges & truth) if correct_source else 0
            assert counts['correct'] == correct and counts['proposed'] == len(edges) and counts['reference'] == len(truth)
            assert counts['extra'] == len(edges)-correct
            assert counts['precision'] == (correct/len(edges) if edges else None)
            assert counts['recall'] == correct/len(truth)
        absent = [a for a in ranked if docs[a['source_id']]['source_group'] != r['group']]
        am = absent[0]['strength']-absent[1]['strength']
        assert row['source_absent']['top'] == absent[0] and row['source_absent']['margin'] == am
        assert row['source_absent']['false_admission'] == (absent[0]['minimum_links_met'] and am > 1e-9 and absent[0]['strength'] >= row['threshold'])
        shuffle = row['shuffle']
        assert len(shuffle['strengths']) == shuffle['repetitions'] == 20
        assert shuffle['unique_orders'] == len({tuple(o) for o in orders[packet]})
        assert shuffle['exceed_or_equal_observed'] == sum(s >= ranked[0]['strength'] for s in shuffle['strengths'])
        assert d['diagnostic_only'] and not d['semantic_gold']
        assert d['alias_observations'] == audit_aliases(docs[r['fl_id']]['text'], docs[r['source_id']]['text'], r['edges'])
        for capacity in d['alias_capacity']:
            i, word, form = capacity['fl_index'], capacity['proposal'], capacity['form']
            ids = sorted({e['source_index'] for e in r['edges'] if e['fl_index'] == i})
            fspans = [[t.start, t.end] for t in fa[i].tokens if t.normalized == form]
            sspans = [[t.start, t.end] for j in ids for t in sa[j].tokens if t.normalized == word]
            assert capacity['source_indices'] == ids
            assert capacity['compatible_fl_spans'] == fspans and capacity['compatible_source_spans'] == sspans
            assert capacity['fl_count'] == len(fspans) and capacity['source_count'] == len(sspans)
            assert capacity['minimum_unrealized'] == max(0, len(fspans)-len(sspans)) and not capacity['semantic_gold']
        cache = ScoreCache(fa, PreparedSource(sa, units[r['source_id']]), cfg, predicted)
        for block in d['reference_proposals']:
            assert not block['token_hypotheses_used_by_retrieval'] and not block['semantic_gold']
            fi, si = tuple(block['fl_atoms']), tuple(block['source_atoms'])
            assert si == tuple(sorted({e['source_index'] for e in r['edges'] if e['fl_index'] in fi}))
            check_pairs(block['reference_guided_token_hypotheses'], fa, sa, predicted, {(f, s) for f in fi for s in si})
            assert abs(sum(block['weighted_components'].values())-block['structural']) < 1e-12
            assert abs(.6*block['structural']+.4*block['lexical']-block['similarity']) < 1e-12
            mass = (block['fl_tokens']+block['source_tokens'])/40
            assert abs(block['reward']-((block['similarity']-.72)*mass-.04*max(0, mass-1))) < 1e-12
            assert block['positive_reward'] == (block['reward'] > 0)
            assert block['eligible_reference_proposal'] == (block['proposal_feasible'] and block['positive_reward'])
            if block['proposal_feasible']:
                source_size = block['source_effective_units']
                starts = [j for j, target in enumerate(cache.source.blocks[source_size]) if target.atoms == si]
                assert len(starts) == 1
                assert abs(cache.row(fi, source_size, 'lexical')[starts[0]]-block['similarity']) < 1e-12
        assert d['feasible_reference_proposals'] == sum(b['proposal_feasible'] for b in d['reference_proposals'])
        assert d['positive_feasible_reference_proposals'] == sum(b['eligible_reference_proposal'] for b in d['reference_proposals'])
        assert d['reference_atoms_in_positive_proposals'] == sorted({i for b in d['reference_proposals'] if b['eligible_reference_proposal'] for i in b['fl_atoms']})
    # Opening is an exact regression of the existing v5 outcomes in the same pool.
    oldrows = read(ROOT/'runs/000005_kamri_scoped_register/report.json')['results']
    for row in rows:
        if row['packet'] != 'opening':
            continue
        previous = next(r for r in oldrows if r['group'] == 'models_magic' and r['variant'] == row['variant'])
        for field in ('rankings', 'threshold', 'candidate_margin', 'correct_source_rank', 'admitted', 'conditional_edges', 'retrieved_edges', 'source_absent'):
            assert row[field] == previous[field], field
    previous = []
    for oldid in ['000001_kamri_excerpt_baseline', '000002_kamri_alignment_editions', '000003_kamri_passage_factorial',
                  '000004_kamri_precision_mass', '000005_kamri_scoped_register']:
        oldout = ROOT/'runs'/oldid
        check_hashes(oldout)
        previous.append({'run_id': oldid, 'manifest_sha256': digest((oldout/'manifest.json').read_bytes())})
    receipt = {'state': 'verified', 'run_id': manifest['run_id'], 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'result_rows': 6, 'within_article_selected': 2, 'within_article_available': 2,
               'independent_source_works': 1, 'fresh_independent_works': 0, 'new_supported_lexical_entries': 0,
               'previous_runs': previous,
               'checks': ['input/raw/code/output hashes', 'frozen v5 scorer/configuration/thresholds', 'opening exactly reproduces v5',
                          'query-only gates and prediction origins', 'token spans/order/uniqueness and edge support',
                          'retrieval counts/admissions/source-absent controls', 'shared nonidentity permutations with unique-order counts',
                          'reference-guided diagnostics separately labeled and cache score agreement', 'alias capacity counts and all candidate spans',
                          'unchanged experiment 1–5 manifests, code, inputs, outputs']}
    dump_json(ROOT/'reports/000006_verification.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
