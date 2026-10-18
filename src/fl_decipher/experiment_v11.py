"""Frozen anchor-conflict experiment with two sealed admission policies."""
from datetime import datetime, timezone
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .editorial_v7 import EditorialScoreCache
from .experiment_v5 import nonidentity_orders
from .experiment_v7 import read
from .evaluation_v11 import validate, finish, summaries as make_summaries, comparisons
from .content_v10 import evidence, apply_mode, mode_quality
from .passage_v3 import PreparedSource, ordered_units, protected_groups
from .precision_v4 import admission, align, decode
from .register_v5 import label_anchor_origins, predictions
from .text import sentences


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    bp = root/'benchmarks/kamri_conflict_v11.json'
    cfg, bench = read(root/'experiments/kamri_conflict_v11.json'), read(bp)
    docs = validate(root, bench, cfg)
    out = root/'runs'/run_id; out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
        'fresh_condition_denominator': 768, 'fresh_world_denominator': 32,
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
                        q = evidence(a, atoms[key], atoms[sk], ps[cid], cfg)
                        decoded = label_anchor_origins(decode(a, atoms[key], atoms[sk], ps[cid], cfg, 'ordered'), ps[cid])
                        bases.append((sk, decoded, q))
                    shuffled = []
                    for o in orders[cid]:
                        candidates = []
                        for sk in r['candidate_ids']:
                            a = align(ordered_units(units[key], o), prepared[sk], caches[sk], cfg, 'tokens')
                            q = evidence(a, atoms[key], atoms[sk], ps[cid], cfg)
                            candidates.append({'source_id': sk, 'base_strength': a['strength'], 'candidate_evidence': q})
                        shuffled.append(candidates)
                    details[cid][bg['id']] = shuffled
                    for v in [v for v in cfg['variants'] if v['background'] == bg['id']]:
                        ranked = [{'source_id': sk, **apply_mode(a, q, v['mode'])} for sk, a, q in bases]
                        ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                        strengths = [max(a['base_strength']*mode_quality(a['candidate_evidence'], v['mode']) for a in candidates) for candidates in shuffled]
                        raw.append({k: r.get(k) for k in ('case_id', 'group', 'dataset', 'split', 'seed', 'density', 'corruption', 'extent', 'family')} | {
                            'variant': v['id'], 'background': bg['id'], 'mode': v['mode'], 'rankings': ranked,
                            'shuffle': {'strengths': strengths, 'repetitions': len(strengths), 'unique_orders': len({tuple(o) for o in orders[cid]}),
                                        'exceed_or_equal_observed': sum(s >= ranked[0]['strength'] for s in strengths), 'identity_allowed': False}})
                if r['dataset'] == 'real' or (r.get('density'), r.get('corruption'), r.get('extent'), r.get('family')) == (3, 'omit_all', 'half', 'prediction_lure'):
                    print(f'Computed {cid} ({r["split"]})', flush=True)

        compute([r for r in bench['records'] if r['split'] in ('real_development', 'calibration')])
        thresholds = {}
        for policy in ('primary', 'pooled'):
            thresholds[policy] = {}
            for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
                thresholds[policy][dataset] = {v['id']: max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id']
                    and (policy == 'pooled' or dataset == 'real' or r['family'] == cfg['primary_family']) for a in r['rankings']
                    if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))+1e-6 for v in cfg['variants']}
        dump_json(out/'calibration_scores.json', raw); dump_json(out/'thresholds.json', thresholds)
        manifest.update(calibration_sealed_at_utc=datetime.now(timezone.utc).isoformat(), calibration_thresholds_sha256=digest((out/'thresholds.json').read_bytes()))
        dump_json(out/'manifest.json', manifest)
        print('Calibration sealed; beginning fresh and development-only diagnostics', flush=True)
        compute([r for r in bench['records'] if r['split'] in ('real_audit', 'fresh')])
        rows = [finish(r, refs[r['case_id']], docs, thresholds['primary'][r['dataset']][r['variant']], thresholds['pooled'][r['dataset']][r['variant']]) for r in raw]
        summaries = make_summaries(rows, cfg)
        report = {'experiment_id': cfg['experiment_id'], 'fresh_condition_denominator': 768, 'fresh_world_denominator': 32,
                  'calibration_condition_denominator': 768, 'calibration_world_denominator': 32,
                  'fresh_real_source_works': 0, 'new_supported_lexical_entries': 0, 'semantic_gold': False,
                  'thresholds': thresholds, 'results': rows, 'summaries': summaries, 'comparisons': comparisons(rows),
                  'evidence': 'Constructed stress test of fixed content scoring under occurrence-preserving anchor conflicts/omissions and prediction-matching lures; primary policy scope is content_renamed; real remains development'}
        dump_json(out/'raw_scores.json', raw); dump_json(out/'report.json', report); dump_json(out/'shuffle_details.json', details)
        dump_json(out/'summary.json', {'thresholds': thresholds, 'summaries': summaries})
        dump_json(out/'comparisons.json', report['comparisons'])
        lines = ['# Experiment 11: frozen anchor conflicts and prediction lures', '',
                 '768 fresh conditions from 32 worlds; 768 calibration conditions from 32 other worlds. Primary scope: 384 content-renamed conditions.', '',
                 '| Variant | Unique primary / 384 | Primary correct admissions | Primary absent false | Pooled correct / 768 | Pooled absent false |',
                 '|---|---:|---:|---:|---:|---:|']
        for s in summaries:
            if s['panel'] != 'fresh_primary':
                continue
            pooled = next(x for x in summaries if x['panel'] == 'fresh' and x['variant'] == s['variant'])
            lines.append(f'| {s["variant"]} | {s["unique_correct_top1"]} | {s["correct_admissions"]} | {s["source_absent_false_admissions"]} | {pooled["pooled_correct_admissions"]} | {pooled["pooled_absent_false_admissions"]} |')
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
