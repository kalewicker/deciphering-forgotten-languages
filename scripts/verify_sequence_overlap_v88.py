"""Independent diagonal-run reconstruction; imports no project parsers/models."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = 'runs/000088_sequence_overlap'


def read(path):
    return json.loads((ROOT/path).read_text())


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def close(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            close(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            close(a, b)
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def split(row):
    """Identify starts, then extend each segment along original pair flags."""
    ts = row['tokens']
    result = []
    for i, t in enumerate(ts):
        if t['blocked']:
            assert not t['pair_from_previous']
        elif not t['pair_from_previous']:
            j = i+1
            while j < len(ts) and not ts[j]['blocked'] and ts[j]['pair_from_previous']:
                j += 1
            result.append(list(range(i, j)))
    assert sorted(i for s in result for i in s) == [i for i,t in enumerate(ts) if not t['blocked']]
    return result


def diagonal_matches(evaluation, training):
    result = []
    for e in evaluation:
        for t in training:
            for es in split(e):
                for ts in split(t):
                    a = [e['tokens'][i]['form'] for i in es]
                    b = [t['tokens'][i]['form'] for i in ts]
                    for i in range(len(a)):
                        for j in range(len(b)):
                            if a[i] != b[j] or (i > 0 and j > 0 and a[i-1] == b[j-1]):
                                continue
                            length = 0
                            while i+length < len(a) and j+length < len(b) and a[i+length] == b[j+length]:
                                length += 1
                            for n in range(2, min(8, length)+1):
                                for off in range(length-n+1):
                                    result.append({'length': n, 'evaluation_uid': e['uid'],
                                                   'evaluation_indices': es[i+off:i+off+n],
                                                   'training_uid': t['uid'], 'training_indices': ts[j+off:j+off+n]})
    return sorted(result, key=lambda m: (m['length'], m['evaluation_uid'], m['evaluation_indices'],
                                         m['training_uid'], m['training_indices']))


def cell(rows, denominator):
    s = math.fsum(r['gain'] for r in rows)
    pos = math.fsum(r['gain'] for r in rows if r['gain'] > 0)
    neg = math.fsum(r['gain'] for r in rows if r['gain'] < 0)
    return dict(pairs=len(rows), changed_predictions=sum(r['changed'] for r in rows),
                gain_sum=s, positive_gain_sum=pos, negative_gain_sum=neg,
                mean_gain=s/len(rows) if rows else None, contribution=s/denominator,
                positive_contribution=pos/denominator, negative_contribution=neg/denominator)


def verify():
    reg_path = 'experiments/sequence_overlap_v88.json'
    reg = read(reg_path)
    assert reg['lengths'] == list(range(2, 9)) and reg['new_predictions'] is False
    for p, h in reg['input_hashes'].items():
        assert digest(p) == h, p
    manifest = read(OUT+'/manifest.json')
    assert manifest['state'] == 'complete'
    assert manifest['input_hashes'] == reg['input_hashes'] | {reg_path: digest(reg_path)}
    for p, h in manifest['output_hashes'].items():
        assert digest(p) == h, p
    for version in (76, 77, 79, 87):
        for p, h in read(f'reports/{version:06}_deliverable_seal.json')['deliverable_hashes'].items():
            assert digest(p) == h, p
    prior = read('runs/000079_context_guard/report.json')
    groups = [r['group'] for r in prior['folds']]
    assert len(groups) == len(set(groups)) == 13
    units = [r for r in read('runs/000076_order_corpus/unit_ledger.json')
             if r['exclusion'] is None and r['group'] in groups]
    assert len(units) == 98
    lookup = {r['uid']: r for r in units}
    assert len(lookup) == 98
    reconstructed = []
    total_matches = 0
    for fi, g in enumerate(groups):
        saved = read(f'runs/000079_context_guard/fold_{fi:02}.json')
        old = read(f'runs/000077_word_order/fold_{fi:02}.json')
        assert saved['targets'] == old['targets']
        assert saved['unigram_probabilities'] == old['unigram_probabilities']
        assert saved['group'] == g and saved['training_groups'] == [x for x in groups if x != g]
        evaluation = [r for r in units if r['group'] == g]
        training = [r for r in units if r['group'] != g]
        expected_targets = [(r['uid'], a, b) for r in evaluation for s in split(r) for a,b in zip(s, s[1:])]
        assert expected_targets == [(t['uid'],t['context_index'],t['target_index']) for t in saved['targets']]
        occurrences = diagonal_matches(evaluation, training)
        total_matches += len(occurrences)
        affected = {}
        for m in occurrences:
            for k in range(1, m['length']):
                pair = m['evaluation_uid'], m['evaluation_indices'][k-1], m['evaluation_indices'][k]
                affected.setdefault(pair, set()).add(m['length'])
        rows = []
        for j, t in enumerate(saved['targets']):
            uid, a, b = t['uid'], t['context_index'], t['target_index']
            r = lookup[uid]
            v = set(saved['vocabulary'])
            for idx, field in ((a, 'context'), (b, 'target')):
                form = r['tokens'][idx]['form']
                assert t[field] == (form if form in v else '<UNK>')
            ls = sorted(affected.get((uid,a,b), ()))
            u, p = saved['unigram_probabilities'][j], saved['observed_probabilities'][j]
            assert 0 < u <= 1 and 0 < p <= 1
            binding = r['canonical_binding']
            row = dict(uid=uid, context_index=a, target_index=b, source_path=binding['path'],
                       context_span=[binding['start']+r['tokens'][a][key] for key in ('start','end')],
                       target_span=[binding['start']+r['tokens'][b][key] for key in ('start','end')],
                       covered_lengths=ls, max_covered_length=max(ls, default=0),
                       unigram_probability=u, saved_probability=p, changed=p != u,
                       gain=math.log2(p)-math.log2(u))
            if t['target'] == '<UNK>':
                assert p == u
            rows.append(row)
        close(read(OUT+f'/fold_{fi:02}.json'), dict(group=g, matches=occurrences, targets=rows))
        count = len(rows)
        assert count == saved['pairs']
        lengths = {}
        for n in range(2,9):
            covered = [r for r in rows if n in r['covered_lengths']]
            uncovered = [r for r in rows if n not in r['covered_lengths']]
            lengths[str(n)] = dict(covered=cell(covered,count), uncovered=cell(uncovered,count))
            assert len(covered)+len(uncovered) == count
        stats = dict(group=g, units=len(evaluation), occurrence_matches=len(occurrences), pairs=count,
                     total=cell(rows,count), lengths=lengths,
                     max_bins={str(n):cell([r for r in rows if r['max_covered_length']==n],count)
                               for n in (0,2,3,4,5,6,7,8)})
        assert math.isclose(stats['total']['contribution'],saved['observed']['gain'],abs_tol=1e-12)
        reconstructed.append(stats)
    def combine(cells):
        return dict(pairs=sum(c['pairs'] for c in cells),
                    changed_predictions=sum(c['changed_predictions'] for c in cells),
                    **{key:math.fsum(c[key] for c in cells)/13
                       for key in ('contribution','positive_contribution','negative_contribution')})
    summary = dict(total=combine([f['total'] for f in reconstructed]), lengths={},
                   max_bins={str(n):combine([f['max_bins'][str(n)] for f in reconstructed])
                             for n in (0,2,3,4,5,6,7,8)})
    for n in range(2,9):
        cells = {label:combine([f['lengths'][str(n)][label] for f in reconstructed])
                 for label in ('covered','uncovered')}
        pos = summary['total']['positive_contribution']
        cells['positive_mass_fraction_covered'] = cells['covered']['positive_contribution']/pos if pos else None
        close(cells['covered']['contribution']+cells['uncovered']['contribution'],summary['total']['contribution'])
        summary['lengths'][str(n)] = cells
    report = dict(experiment_id='sequence_overlap_v88', groups=13, units=98, pairs=1918,
                  folds=reconstructed, macro=summary, new_predictions=False, network_requests=0,
                  new_confirmation_units=0, semantic_benchmark_qualifying_works=0, e79_gate_retested=False)
    close(read(OUT+'/report.json'), report)
    assert summary['total']['pairs'] == 1918 and summary['total']['changed_predictions'] == 311
    close(summary['total']['contribution'],prior['summary']['macro_gain'])
    print(json.dumps(dict(verified=True, groups=13, units=98, pairs=1918,
                          occurrence_matches=total_matches, changed_predictions=311,
                          new_predictions=False, network_requests=0), indent=2))


if __name__ == '__main__':
    verify()
