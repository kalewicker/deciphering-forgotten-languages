"""Input contracts and scoped/pooled evaluation for the anchor-conflict experiment."""
from .corpus import digest
from .experiment_v7 import aggregate as aggregate_v7, finish_row, read
from .content_v10 import BACKGROUNDS, VARIANTS, CONTENT_FORMS
from .synthetic_v11 import CONDITIONS
from .text import sentences


def validate(root, bench, cfg):
    for path, sha in {**bench['input_hashes'], **bench['raw_acquisition_hashes']}.items():
        assert digest((root/path).read_bytes()) == sha, path
    old = read(root/'experiments/kamri_content_v10.json')
    changed = {'experiment_id', 'registration', 'variants', 'calibration_seeds', 'fresh_seeds', 'conditions', 'shuffle_seed', 'old_synthetic_thresholds'}
    for k in old.keys()-changed:
        assert cfg[k] == old[k], k
    assert cfg['content_forms'] == CONTENT_FORMS and cfg['primary_family'] == 'content_renamed'
    assert cfg['variants'] == VARIANTS and cfg['backgrounds'] == BACKGROUNDS and cfg['conditions'] == CONDITIONS
    assert cfg['calibration_seeds'] == list(range(11401, 11433)) and cfg['fresh_seeds'] == list(range(11501, 11533))
    assert cfg['shuffle_seed'] == 11331
    docs = {}
    for k, info in bench['documents'].items():
        d = read(root/info['path'])
        assert digest((root/info['path']).read_bytes()) == info['sha256']
        assert digest(d['text'].encode()) == d['text_sha256'] == info['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[k] = d
    records = bench['records']
    assert len(records) == len({r['case_id'] for r in records}) == 1548
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        own = [r for r in records if r['split'] == split]
        assert len(own) == 768
        assert {(r['seed'], r['density'], r['corruption'], r['extent'], r['family']) for r in own} == {
            (s, c['density'], c['corruption'], c['extent'], c['family']) for s in seeds for c in CONDITIONS}
        assert bench[split+'_condition_denominator'] == 768 and bench[split+'_world_denominator'] == 32
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


def finish(raw, ref, docs, threshold, pooled_threshold):
    row = finish_row(raw, ref, docs, threshold)
    maximum = raw['rankings'][0]['strength']
    tied = [a['source_id'] for a in raw['rankings'] if maximum-a['strength'] <= 1e-9]
    row.update(maximum_score_sources=tied, correct_in_maximum_set=ref['source_id'] in tied,
               maximum_set_size=len(tied), top_score_tie=len(tied) > 1,
               all_zero_tie=all(a['strength'] == 0. for a in raw['rankings']))
    from .precision_v4 import admission
    row.update(pooled_threshold=pooled_threshold, pooled_admitted=admission(row['rankings'][0], row['candidate_margin'], pooled_threshold),
               pooled_source_absent_false_admission=admission(row['source_absent']['top'], row['source_absent']['margin'], pooled_threshold),
               capacity_scope='primary' if ref.get('family') == 'content_renamed' else 'stress' if ref['dataset'] == 'synthetic' else 'real_development')
    return row


def aggregate(rows, panel, variant):
    result = aggregate_v7(rows, panel, variant)
    for field in ('correct_in_maximum_set', 'top_score_tie', 'all_zero_tie'):
        result[field] = sum(r[field] for r in rows)
    result['worlds_with_wrong_admission'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['admitted'] and not r['top_work_correct']})
    result['worlds_with_absent_false_admission'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['source_absent']['false_admission']})
    result['pooled_correct_admissions'] = sum(r['pooled_admitted'] and r['top_work_correct'] for r in rows)
    result['pooled_wrong_admissions'] = sum(r['pooled_admitted'] and not r['top_work_correct'] for r in rows)
    result['pooled_absent_false_admissions'] = sum(r['pooled_source_absent_false_admission'] for r in rows)
    result['pooled_worlds_with_wrong_admission'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['pooled_admitted'] and not r['top_work_correct']})
    result['pooled_worlds_with_absent_error'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['pooled_source_absent_false_admission']})
    return result


def panel_rows(rows, panel):
    if panel in ('fresh_primary', 'fresh_stress', 'calibration_primary'):
        split = 'calibration' if panel == 'calibration_primary' else 'fresh'
        primary = panel != 'fresh_stress'
        return [r for r in rows if r['split'] == split and (r['family'] == 'content_renamed') == primary]
    if panel.startswith('fresh_condition_'):
        density, corruption, extent, family = panel.removeprefix('fresh_condition_').split(':')
        return [r for r in rows if r['split'] == 'fresh' and (r['density'], r['corruption'], r['extent'], r['family']) == (int(density), corruption, extent, family)]
    if panel.startswith('fresh_family_'):
        return [r for r in rows if r['split'] == 'fresh' and r['family'] == panel.removeprefix('fresh_family_')]
    if panel.startswith('fresh_world_'):
        return [r for r in rows if r['split'] == 'fresh' and r['seed'] == int(panel.removeprefix('fresh_world_'))]
    return [r for r in rows if r['split'] == panel]


def summaries(rows, cfg):
    panels = ['real_development', 'real_audit', 'calibration', 'fresh', 'fresh_primary', 'fresh_stress', 'calibration_primary']
    panels += ['fresh_condition_'+':'.join(str(c[k]) for k in ('density', 'corruption', 'extent', 'family')) for c in CONDITIONS]
    panels += ['fresh_family_'+f for f in ('content_renamed', 'prediction_lure')]
    panels += ['fresh_world_'+str(s) for s in cfg['fresh_seeds']]
    return [aggregate(panel_rows([r for r in rows if r['variant'] == v['id']], panel), panel, v['id'])
            for v in cfg['variants'] for panel in panels]


def measures(row):
    correct = row['rankings'][row['correct_source_rank']-1]
    return {'unique_correct_top1': int(row['unique_correct_top1']), 'correct_in_maximum_set': int(row['correct_in_maximum_set']),
            'correct_admission': int(row['admitted'] and row['top_work_correct']),
            'wrong_admission': int(row['admitted'] and not row['top_work_correct']),
            'pooled_wrong_admission': int(row['pooled_admitted'] and not row['top_work_correct']),
            'conditional_correct_edges': row['conditional_edges']['correct'],
            'conditional_correct_tokens': row['conditional_tokens']['correct'],
            'conditional_proposed_tokens': row['conditional_tokens']['proposed'],
            'conditional_extra_tokens': row['conditional_tokens']['extra'],
            'absent_false_admission': int(row['source_absent']['false_admission']),
            'pooled_correct_admission': int(row['pooled_admitted'] and row['top_work_correct']),
            'pooled_absent_false_admission': int(row['pooled_source_absent_false_admission']),
            'retrieved_correct_edges': row['retrieved_edges']['correct'],
            'retrieved_correct_tokens': row['retrieved_tokens']['correct'],
            'correct_source_strength': correct['strength'], 'correct_source_quality': correct['mode_quality']}


def comparisons(rows):
    fresh = [r for r in rows if r['split'] == 'fresh']
    by_key = {(r['case_id'], r['background'], r['mode']): r for r in fresh}
    contrasts = []
    for row in fresh:
        targets = ['positional', 'content_bag', 'content_order'] if row['mode'] == 'base' else ['content_order'] if row['mode'] == 'content_bag' else []
        for target in targets:
            high = by_key[row['case_id'], row['background'], target]
            low_m, high_m = measures(row), measures(high)
            contrasts.append({k: row[k] for k in ('case_id', 'seed', 'density', 'corruption', 'extent', 'family', 'background')} | {
                'low': row['variant'], 'high': high['variant'],
                'difference': {k: high_m[k]-low_m[k] for k in low_m}})
    paired = {(r['seed'], r['density'], r['corruption'], r['extent'], r['family'], r['variant']): r for r in fresh}
    corruptions = []
    for row in fresh:
        if row['density'] != 3 or row['corruption'] == 'clean':
            continue
        clean = paired[row['seed'], 3, 'clean', row['extent'], row['family'], row['variant']]
        before, after = measures(clean), measures(row)
        corruptions.append({k: row[k] for k in ('case_id', 'seed', 'corruption', 'extent', 'family', 'variant')} | {
            'clean_case_id': clean['case_id'], 'difference_from_clean': {k: after[k]-before[k] for k in before}})
    return {'paired_corruption_contrasts': corruptions, 'matched_mode_contrasts': contrasts, 'independent_worlds': 32, 'descriptive_only': True}
