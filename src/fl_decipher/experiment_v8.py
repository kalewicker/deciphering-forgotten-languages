"""Frozen candidate-order comparison with enlarged, sealed calibration panels."""
from datetime import datetime, timezone
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .editorial_v7 import EditorialScoreCache
from .experiment_v5 import nonidentity_orders
from .experiment_v7 import aggregate as aggregate_v7, finish_row, read
from .order_v8 import BACKGROUNDS, VARIANTS, apply_order, order_quality
from .passage_v3 import PreparedSource, ordered_units, protected_groups
from .precision_v4 import admission, align, decode
from .register_v5 import label_anchor_origins, predictions
from .text import sentences


def validate(root, bench, cfg):
    for path, sha in {**bench['input_hashes'], **bench['raw_acquisition_hashes']}.items():
        assert digest((root/path).read_bytes()) == sha, path
    old = read(root/'experiments/kamri_editorial_v7.json')
    for k in old:
        if k not in ('experiment_id', 'registration', 'variants', 'calibration_seeds', 'fresh_seeds', 'conditions', 'shuffle_seed'):
            assert cfg[k] == old[k], k
    assert cfg['variants'] == VARIANTS and cfg['backgrounds'] == BACKGROUNDS
    assert cfg['calibration_seeds'] == list(range(8401, 8433)) and cfg['fresh_seeds'] == list(range(8501, 8533))
    assert cfg['conditions'] == [0, 1, 2, 4, 8, 15]
    oldth = read(root/'runs/000007_kamri_editorial_robustness/thresholds.json')['synthetic']
    assert cfg['old_synthetic_thresholds'] == {b['id']: oldth[b['id']] for b in BACKGROUNDS}
    docs = {}
    for k, info in bench['documents'].items():
        d = read(root/info['path'])
        assert digest((root/info['path']).read_bytes()) == info['sha256']
        assert digest(d['text'].encode()) == d['text_sha256'] == info['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[k] = d
    records = bench['records']
    assert len(records) == len({r['case_id'] for r in records}) == 404
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        own = [r for r in records if r['split'] == split]
        assert len(own) == 192
        assert {(r['seed'], r['mask']) for r in own} == {(seed, mask) for seed in seeds for mask in cfg['conditions']}
    assert bench['fresh_condition_denominator'] == bench['calibration_condition_denominator'] == 192
    assert bench['fresh_world_denominator'] == bench['calibration_world_denominator'] == 32
    assert len([r for r in records if r['split'] == 'real_development']) == 10
    assert len([r for r in records if r['split'] == 'real_audit']) == 2
    assert {(r['seed'], r['mask']) for r in records if r['split'] == 'old_development'} == {(s, 0) for s in range(7501, 7509)}
    seedsets = [{r['seed'] for r in records if r['split'] == s} for s in ('calibration', 'fresh', 'old_development')]
    assert all(not a.intersection(b) for i, a in enumerate(seedsets) for b in seedsets[i+1:])
    for r in records:
        fa, sa = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        assert r['source_id'] in r['candidate_ids']
        for e in r['edges']:
            assert e['fl_span'] == [fa[e['fl_index']].start, fa[e['fl_index']].end]
            assert e['source_span'] == [sa[e['source_index']].start, sa[e['source_index']].end]
        if r['dataset'] == 'synthetic':
            assert len(fa) == len(sa) == 6 and len(r['candidate_ids']) == 4
            fi = {t['uid']: t for t in r['fl_token_ids']}
            si = {t['uid']: t for t in r['source_token_ids'] if t['uid'] is not None}
            assert fi.keys() == si.keys() == {p['uid'] for p in r['token_pairs']}
            for p in r['token_pairs']:
                assert p['fl_span'] == fi[p['uid']]['span'] and p['source_span'] == si[p['uid']]['span']
    return docs


def aggregate(rows, panel, variant):
    result = aggregate_v7(rows, panel, variant)
    result['worlds_with_absent_false_admission'] = len({r['seed'] for r in rows if r['dataset'] == 'synthetic' and r['source_absent']['false_admission']})
    entries = [r for r in rows if r['old_v7_threshold_counterfactual'] is not None]
    result['old_threshold_counterfactual'] = ({
        'evaluated': len(entries),
        'correct_admissions': sum(r['old_v7_threshold_counterfactual']['admitted'] and r['top_work_correct'] for r in entries),
        'wrong_admissions': sum(r['old_v7_threshold_counterfactual']['admitted'] and not r['top_work_correct'] for r in entries),
        'source_absent_false_admissions': sum(r['old_v7_threshold_counterfactual']['source_absent_false_admission'] for r in entries),
    } if entries else None)
    return result


def comparisons(rows):
    fresh = [r for r in rows if r['split'] == 'fresh']
    lookup = {(r['seed'], r['mask'], r['background'], r['order']): r for r in fresh}
    paired = []
    for r in fresh:
        if r['order']:
            continue
        on = lookup[r['seed'], r['mask'], r['background'], True]
        def values(x):
            return {'unique_correct_top1': int(x['unique_correct_top1']),
                    'correct_admission': int(x['admitted'] and x['top_work_correct']),
                    'absent_false_admission': int(x['source_absent']['false_admission']),
                    'retrieved_correct_edges': x['retrieved_edges']['correct'], 'retrieved_correct_tokens': x['retrieved_tokens']['correct']}
        correct = r['rankings'][r['correct_source_rank']-1]
        paired.append({'seed': r['seed'], 'mask': r['mask'], 'background': r['background'],
                       'difference': {k: v-values(r)[k] for k, v in values(on).items()},
                       'correct_source_quality': correct['order_quality']['quality'],
                       'correct_source_base_strength': correct['base_strength'],
                       'off_strength': correct['strength'], 'on_strength': correct['base_strength']*correct['order_quality']['quality'],
                       'rank_change': on['correct_source_rank']-r['correct_source_rank']})
    return {'paired_order_contrasts': paired, 'independent_worlds': 32, 'descriptive_only': True}


def counterfactual(row, cfg):
    if row['split'] != 'fresh' or row['order']:
        return None
    threshold = cfg['old_synthetic_thresholds'][row['background']]
    return {'threshold': threshold,
            'admitted': admission(row['rankings'][0], row['candidate_margin'], threshold),
            'source_absent_false_admission': admission(row['source_absent']['top'], row['source_absent']['margin'], threshold)}


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    bp = root/'benchmarks/kamri_order_v8.json'
    cfg, bench = read(root/'experiments/kamri_order_v8.json'), read(bp)
    docs = validate(root, bench, cfg)
    out = root/'runs'/run_id; out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
        'fresh_condition_denominator': 192, 'fresh_world_denominator': 32,
        'input_hashes': {**bench['input_hashes'], **bench['raw_acquisition_hashes'], str(bp.relative_to(root)): digest(bp.read_bytes())},
        'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic(); raw = []; details = {}
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
        prepared = {k: PreparedSource(atoms[k], units[k]) for k in {k for r in bench['records'] for k in r['candidate_ids']}}
        lexicon = read(root/cfg['lexicon_path']); ps = {}; gates = {}
        for r in bench['records']:
            ps[r['case_id']], gates[r['case_id']] = predictions(atoms[r['fl_id']], lexicon, cfg['lexicon_rules'], cfg['prediction_variant'])
        rng = random.Random(cfg['shuffle_seed'])
        orders = {r['case_id']: ([] if r['split'] == 'calibration' else nonidentity_orders(len(atoms[r['fl_id']]), cfg['shuffle_repetitions'], rng)) for r in bench['records']}
        dump_json(out/'predictions.json', ps); dump_json(out/'gates.json', gates); dump_json(out/'permutations.json', orders)
        refs = {r['case_id']: r for r in bench['records']}

        def compute(records):
            for r in records:
                key, cid = r['fl_id'], r['case_id']; details[cid] = {}
                for bg in cfg['backgrounds']:
                    caches = {k: EditorialScoreCache(atoms[key], prepared[k], cfg, ps[cid], bg) for k in r['candidate_ids']}
                    bases = []
                    for sk in r['candidate_ids']:
                        a = align(units[key], prepared[sk], caches[sk], cfg, 'tokens')
                        q = order_quality(a, atoms[key], atoms[sk], ps[cid], cfg)
                        decoded = label_anchor_origins(decode(a, atoms[key], atoms[sk], ps[cid], cfg, 'ordered'), ps[cid])
                        bases.append((sk, decoded, q))
                    shuffled = []
                    for o in orders[cid]:
                        candidates = []
                        for sk in r['candidate_ids']:
                            a = align(ordered_units(units[key], o), prepared[sk], caches[sk], cfg, 'tokens')
                            q = order_quality(a, atoms[key], atoms[sk], ps[cid], cfg)
                            candidates.append({'source_id': sk, 'base_strength': a['strength'], 'order_quality': q})
                        shuffled.append(candidates)
                    details[cid][bg['id']] = shuffled
                    for v in [v for v in cfg['variants'] if v['background'] == bg['id']]:
                        ranked = [{'source_id': sk, **apply_order(a, q, v['order'])} for sk, a, q in bases]
                        ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                        strengths = [max(a['base_strength']*a['order_quality']['quality'] if v['order'] else a['base_strength'] for a in candidates) for candidates in shuffled]
                        raw.append({k: r.get(k) for k in ('case_id', 'group', 'dataset', 'split', 'seed', 'mask', 'edits')} | {
                            'variant': v['id'], 'background': bg['id'], 'order': v['order'], 'rankings': ranked,
                            'shuffle': {'strengths': strengths, 'repetitions': len(strengths), 'unique_orders': len({tuple(o) for o in orders[cid]}),
                                        'exceed_or_equal_observed': sum(s >= ranked[0]['strength'] for s in strengths), 'identity_allowed': False}})
                if r['dataset'] == 'real' or r.get('mask') == 15 or r['split'] == 'old_development':
                    print(f'Computed {cid} ({r["split"]})', flush=True)

        compute([r for r in bench['records'] if r['split'] in ('real_development', 'calibration')])
        thresholds = {}
        for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
            thresholds[dataset] = {v['id']: max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id'] for a in r['rankings']
                if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))+1e-6 for v in cfg['variants']}
        dump_json(out/'calibration_scores.json', raw); dump_json(out/'thresholds.json', thresholds)
        manifest.update(calibration_sealed_at_utc=datetime.now(timezone.utc).isoformat(), calibration_thresholds_sha256=digest((out/'thresholds.json').read_bytes()))
        dump_json(out/'manifest.json', manifest)
        print('Calibration sealed; beginning fresh and development-only diagnostics', flush=True)
        compute([r for r in bench['records'] if r['split'] in ('real_audit', 'old_development', 'fresh')])
        rows = []
        for r in raw:
            row = finish_row(r, refs[r['case_id']], docs, thresholds[r['dataset']][r['variant']])
            row['old_v7_threshold_counterfactual'] = counterfactual(row, cfg); rows.append(row)
        summaries = []
        for v in cfg['variants']:
            own = [r for r in rows if r['variant'] == v['id']]
            for split in ('real_development', 'real_audit', 'old_development', 'calibration', 'fresh'):
                summaries.append(aggregate([r for r in own if r['split'] == split], split, v['id']))
            for mask in cfg['conditions']:
                summaries.append(aggregate([r for r in own if r['split'] == 'fresh' and r['mask'] == mask], f'fresh_mask_{mask:02d}', v['id']))
            for seed in cfg['fresh_seeds']:
                summaries.append(aggregate([r for r in own if r['split'] == 'fresh' and r['seed'] == seed], f'fresh_world_{seed}', v['id']))
        report = {'experiment_id': cfg['experiment_id'], 'fresh_condition_denominator': 192, 'fresh_world_denominator': 32,
                  'calibration_condition_denominator': 192, 'calibration_world_denominator': 32,
                  'fresh_real_source_works': 0, 'new_supported_lexical_entries': 0, 'semantic_gold': False,
                  'thresholds': thresholds, 'results': rows, 'summaries': summaries, 'comparisons': comparisons(rows),
                  'evidence': 'Constructed engineering identities; paired stress conditions; old/real material remains development'}
        dump_json(out/'raw_scores.json', raw); dump_json(out/'report.json', report); dump_json(out/'shuffle_details.json', details)
        dump_json(out/'summary.json', {'thresholds': thresholds, 'summaries': summaries})
        dump_json(out/'comparisons.json', report['comparisons'])
        lines = ['# Experiment 8: candidate order and admission', '', '192 fresh conditions from 32 worlds; 192 calibration conditions from 32 other worlds.', '',
                 '| Variant | Unique correct / 192 | Correct admissions | Wrong admissions | Absent false | Pristine absent false / 32 | Edge precision | Token precision |',
                 '|---|---:|---:|---:|---:|---:|---:|---:|']
        for s in summaries:
            if s['panel'] != 'fresh':
                continue
            pristine = next(x for x in summaries if x['panel'] == 'fresh_mask_00' and x['variant'] == s['variant'])
            e, t = s['retrieved_edges'], s['retrieved_tokens']
            lines.append(f'| {s["variant"]} | {s["unique_correct_top1"]} | {s["correct_admissions"]} | {s["wrong_admissions"]} | {s["source_absent_false_admissions"]} | {pristine["source_absent_false_admissions"]} | {e["correct"]}/{e["proposed"]} | {t["correct"]}/{t["proposed"]} |')
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        dump_json(out/'partial_scores.json', raw); dump_json(out/'partial_shuffle_details.json', details)
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}', elapsed_seconds=time.monotonic()-start)
        dump_json(out/'manifest.json', manifest)
        raise
    return out
