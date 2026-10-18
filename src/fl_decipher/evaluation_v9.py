"""Input contracts and descriptive evaluation for the fixed coverage experiment."""
from .corpus import digest
from .experiment_v7 import aggregate as aggregate_v7, finish_row, read
from .coverage_v9 import BACKGROUNDS, VARIANTS
from .synthetic_v9 import CONDITIONS
from .text import sentences


def validate(root, bench, cfg):
    for path, sha in {**bench['input_hashes'], **bench['raw_acquisition_hashes']}.items():
        assert digest((root/path).read_bytes()) == sha, path
    old = read(root/'experiments/kamri_order_v8.json')
    changed = {'experiment_id', 'registration', 'variants', 'calibration_seeds', 'fresh_seeds', 'conditions', 'shuffle_seed', 'old_synthetic_thresholds'}
    for k in old.keys()-changed:
        assert cfg[k] == old[k], k
    assert 'old_synthetic_thresholds' not in cfg
    assert cfg['variants'] == VARIANTS and cfg['backgrounds'] == BACKGROUNDS and cfg['conditions'] == CONDITIONS
    assert cfg['calibration_seeds'] == list(range(9401, 9433)) and cfg['fresh_seeds'] == list(range(9501, 9533))
    assert cfg['shuffle_seed'] == 9931
    docs = {}
    for k, info in bench['documents'].items():
        d = read(root/info['path'])
        assert digest((root/info['path']).read_bytes()) == info['sha256']
        assert digest(d['text'].encode()) == d['text_sha256'] == info['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[k] = d
    records = bench['records']
    assert len(records) == len({r['case_id'] for r in records}) == 780
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        own = [r for r in records if r['split'] == split]
        assert len(own) == 384
        assert {(r['seed'], r['density'], r['extent'], r['family']) for r in own} == {
            (s, c['density'], c['extent'], c['family']) for s in seeds for c in CONDITIONS}
        assert bench[split+'_condition_denominator'] == 384 and bench[split+'_world_denominator'] == 32
    assert len([r for r in records if r['split'] == 'real_development']) == 10
    assert len([r for r in records if r['split'] == 'real_audit']) == 2
    for r in records:
        fa, sa = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        assert r['source_id'] in r['candidate_ids']
        for e in r['edges']:
            assert e['fl_span'] == [fa[e['fl_index']].start, fa[e['fl_index']].end]
            assert e['source_span'] == [sa[e['source_index']].start, sa[e['source_index']].end]
        if r['dataset'] != 'synthetic':
            continue
        assert len(fa) == 6 and len(sa) == (6 if r['extent'] == 'full' else 3)
        assert len(r['candidate_ids']) == len({docs[k]['text'] for k in r['candidate_ids']}) == 4
        fi = {t['uid']: t for t in r['fl_token_ids']}; si = {t['uid']: t for t in r['source_token_ids']}
        assert set(si) == {p['uid'] for p in r['token_pairs']}
        assert set(r['unavailable_query_uids']) == set(fi)-set(si)
        assert not set(si).intersection(r['unavailable_query_uids'])
        for p in r['token_pairs']:
            assert p['fl_span'] == fi[p['uid']]['span'] and p['source_span'] == si[p['uid']]['span']
    return docs


def finish(raw, ref, docs, threshold):
    row = finish_row(raw, ref, docs, threshold)
    maximum = raw['rankings'][0]['strength']
    tied = [a['source_id'] for a in raw['rankings'] if maximum-a['strength'] <= 1e-9]
    row.update(maximum_score_sources=tied, correct_in_maximum_set=ref['source_id'] in tied,
               maximum_set_size=len(tied), top_score_tie=len(tied) > 1,
               all_zero_tie=all(a['strength'] == 0. for a in raw['rankings']))
    return row


def aggregate(rows, panel, variant):
    result = aggregate_v7(rows, panel, variant)
    for field in ('correct_in_maximum_set', 'top_score_tie', 'all_zero_tie'):
        result[field] = sum(r[field] for r in rows)
    result['worlds_with_absent_false_admission'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['source_absent']['false_admission']})
    return result


def panel_rows(rows, panel):
    if panel.startswith('fresh_condition_'):
        density, extent, family = panel.removeprefix('fresh_condition_').split(':')
        return [r for r in rows if r['split'] == 'fresh' and (r['density'], r['extent'], r['family']) == (density, extent, family)]
    if panel.startswith('fresh_family_'):
        return [r for r in rows if r['split'] == 'fresh' and r['family'] == panel.removeprefix('fresh_family_')]
    if panel.startswith('fresh_world_'):
        return [r for r in rows if r['split'] == 'fresh' and r['seed'] == int(panel.removeprefix('fresh_world_'))]
    return [r for r in rows if r['split'] == panel]


def summaries(rows, cfg):
    panels = ['real_development', 'real_audit', 'calibration', 'fresh']
    panels += ['fresh_condition_'+':'.join(c[k] for k in ('density', 'extent', 'family')) for c in CONDITIONS]
    panels += ['fresh_family_'+f for f in ('rotation', 'renamed', 'content_order')]
    panels += ['fresh_world_'+str(s) for s in cfg['fresh_seeds']]
    return [aggregate(panel_rows([r for r in rows if r['variant'] == v['id']], panel), panel, v['id'])
            for v in cfg['variants'] for panel in panels]


def measures(row):
    correct = row['rankings'][row['correct_source_rank']-1]
    return {'unique_correct_top1': int(row['unique_correct_top1']), 'correct_in_maximum_set': int(row['correct_in_maximum_set']),
            'correct_admission': int(row['admitted'] and row['top_work_correct']),
            'absent_false_admission': int(row['source_absent']['false_admission']),
            'retrieved_correct_edges': row['retrieved_edges']['correct'],
            'retrieved_correct_tokens': row['retrieved_tokens']['correct'],
            'correct_source_strength': correct['strength'], 'correct_source_quality': correct['factor_quality']['quality']}


def comparisons(rows):
    fresh = [r for r in rows if r['split'] == 'fresh']
    by_key = {(r['case_id'], r['background'], r['order'], r['coverage']): r for r in fresh}
    contrasts = []
    for row in fresh:
        for factor in ('order', 'coverage'):
            if row[factor]:
                continue
            o, c = (True, row['coverage']) if factor == 'order' else (row['order'], True)
            high = by_key[row['case_id'], row['background'], o, c]
            low_m, high_m = measures(row), measures(high)
            contrasts.append({k: row[k] for k in ('case_id', 'seed', 'density', 'extent', 'family', 'background')} | {
                'factor': factor, 'low': row['variant'], 'high': high['variant'],
                'difference': {k: high_m[k]-low_m[k] for k in low_m}})
    return {'matched_factor_contrasts': contrasts, 'independent_worlds': 32, 'descriptive_only': True}
