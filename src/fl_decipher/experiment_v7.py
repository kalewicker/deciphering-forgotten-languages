"""One frozen editorial factorial execution; calibration precedes fresh scoring."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .editorial_v7 import EditorialScoreCache, VARIANTS
from .experiment_v4 import metrics
from .experiment_v5 import nonidentity_orders
from .passage_v3 import PreparedSource, ordered_units, protected_groups
from .precision_v4 import admission, align, decode
from .register_v5 import ALIASES, label_anchor_origins, predictions
from .text import sentences


def read(path):
    return json.loads(path.read_text())


def validate(root, bench, cfg):
    for path, sha in {**bench['input_hashes'], **bench['raw_acquisition_hashes']}.items():
        assert digest((root/path).read_bytes()) == sha, path
    old = read(root/'experiments/kamri_register_v5.json')
    for k in old:
        if k not in ('experiment_id', 'registration', 'variants', 'seed', 'shuffle_repetitions', 'development_groups', 'fresh_groups'):
            assert cfg[k] == old[k], k
    assert cfg['variants'] == VARIANTS and cfg['aliases'] == ALIASES and cfg['repetition_bins'] == 8
    assert cfg['prediction_variant'] == 'gated_aliases'
    assert cfg['calibration_seeds'] == [7401, 7402] and cfg['fresh_seeds'] == list(range(7501, 7509))
    assert set(cfg['fresh_seeds']).isdisjoint(cfg['calibration_seeds'])
    docs = {}
    for k, info in bench['documents'].items():
        d = read(root/info['path'])
        assert digest((root/info['path']).read_bytes()) == info['sha256']
        assert digest(d['text'].encode()) == d['text_sha256'] == info['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[k] = d
    records = bench['records']
    assert len({r['case_id'] for r in records}) == len(records) == 172
    for split, seeds, total in [('calibration', cfg['calibration_seeds'], 32), ('fresh', cfg['fresh_seeds'], 128)]:
        own = [r for r in records if r['split'] == split]
        assert len(own) == total
        assert {(r['seed'], r['mask']) for r in own} == {(seed, mask) for seed in seeds for mask in range(16)}
    assert bench['fresh_condition_denominator'] == 128 and bench['fresh_world_denominator'] == 8
    assert bench['calibration_condition_denominator'] == 32 and bench['calibration_world_denominator'] == 2
    assert len([r for r in records if r['split'] == 'real_development']) == 10
    assert len([r for r in records if r['split'] == 'real_audit']) == 2
    for r in records:
        assert r['source_id'] in r['candidate_ids']
        fa, sa = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        for e in r['edges']:
            assert e['fl_span'] == [fa[e['fl_index']].start, fa[e['fl_index']].end]
            assert e['source_span'] == [sa[e['source_index']].start, sa[e['source_index']].end]
        if r['dataset'] == 'synthetic':
            assert len(fa) == len(sa) == 6 and len(r['candidate_ids']) == 4
            assert len({docs[k]['text'] for k in r['candidate_ids']}) == 4
            fi = {t['uid']: t for t in r['fl_token_ids']}
            si = {t['uid']: t for t in r['source_token_ids'] if t['uid'] is not None}
            assert fi.keys() == si.keys() == {p['uid'] for p in r['token_pairs']}
            for p in r['token_pairs']:
                assert p['fl_span'] == fi[p['uid']]['span'] and p['source_span'] == si[p['uid']]['span']
                assert p['fl_index'] == fi[p['uid']]['atom_index'] and p['source_index'] == si[p['uid']]['atom_index']
    return docs


def aggregate(rows, panel, variant):
    result = {'panel': panel, 'variant': variant, 'selected_conditions': len(rows),
              'independent_worlds': len({r['seed'] for r in rows if r['dataset'] == 'synthetic'}),
              'unique_correct_top1': sum(r['unique_correct_top1'] for r in rows),
              'correct_admissions': sum(r['admitted'] and r['top_work_correct'] for r in rows),
              'wrong_admissions': sum(r['admitted'] and not r['top_work_correct'] for r in rows),
              'source_absent_false_admissions': sum(r['source_absent']['false_admission'] for r in rows)}
    for field in ('retrieved_edges', 'conditional_edges', 'retrieved_tokens', 'conditional_tokens'):
        entries = [r[field] for r in rows if r[field] is not None]
        if not entries:
            result[field] = None
            continue
        counts = {k: sum(e[k] for e in entries) for k in ('correct', 'proposed', 'reference', 'extra')}
        counts.update(precision=counts['correct']/counts['proposed'] if counts['proposed'] else None,
                      recall=counts['correct']/counts['reference'] if counts['reference'] else None)
        result[field] = counts
    return result


def measures(row):
    return {'unique_correct_top1': int(row['unique_correct_top1']),
            'correct_admission': int(row['admitted'] and row['top_work_correct']),
            'absent_false_admission': int(row['source_absent']['false_admission']),
            'conditional_correct_edges': row['conditional_edges']['correct'],
            'conditional_correct_tokens': row['conditional_tokens']['correct']}


def comparisons(rows):
    fresh = [r for r in rows if r['split'] == 'fresh']
    by_key = {(r['seed'], r['mask'], r['variant']): r for r in fresh}
    edits, factors = [], []
    for row in fresh:
        if row['mask']:
            before = by_key[row['seed'], 0, row['variant']]
            edits.append({'seed': row['seed'], 'mask': row['mask'], 'variant': row['variant'],
                          'difference_from_pristine': {k: v-measures(before)[k] for k, v in measures(row).items()}})
    for seed, mask, vid in by_key:
        low = next(v for v in VARIANTS if v['id'] == vid)
        for factor in ('punctuation_neutral', 'relative_repetition', 'lexical_neutral'):
            if low[factor]:
                continue
            target = {**low, factor: True}
            high = next(v for v in VARIANTS if all(v[k] == target[k] for k in ('punctuation_neutral', 'relative_repetition', 'lexical_neutral')))
            before, after = by_key[seed, mask, vid], by_key[seed, mask, high['id']]
            factors.append({'seed': seed, 'mask': mask, 'factor': factor, 'low': vid, 'high': high['id'],
                            'difference': {k: v-measures(before)[k] for k, v in measures(after).items()}})
    return {'condition_vs_pristine': edits, 'matched_scoring_factors': factors,
            'independent_worlds': len({r['seed'] for r in fresh}), 'descriptive_only': True}


def finish_row(raw, ref, docs, threshold):
    ranked = raw['rankings']; top = ranked[0]
    margin = top['strength']-ranked[1]['strength']
    correct = top['source_id'] == ref['source_id']
    conditional = next(a for a in ranked if a['source_id'] == ref['source_id'])
    absent = [a for a in ranked if (docs[a['source_id']]['source_group'] != ref['group'] if ref['dataset'] == 'real' else a['source_id'] != ref['source_id'])]
    am = absent[0]['strength']-absent[1]['strength']
    return {**raw, 'threshold': threshold, 'candidate_margin': margin, 'top_work_correct': correct,
            'unique_correct_top1': correct and margin > 1e-9, 'admitted': admission(top, margin, threshold),
            'correct_source_rank': next(i+1 for i, a in enumerate(ranked) if a['source_id'] == ref['source_id']),
            'retrieved_edges': metrics(top['edges'], ref['edges'], correct),
            'conditional_edges': metrics(conditional['edges'], ref['edges'], True),
            'retrieved_tokens': metrics(top['token_pairs'], ref['token_pairs'], correct, token=True) if ref['dataset'] == 'synthetic' else None,
            'conditional_tokens': metrics(conditional['token_pairs'], ref['token_pairs'], True, token=True) if ref['dataset'] == 'synthetic' else None,
            'source_absent': {'top': absent[0], 'margin': am, 'false_admission': admission(absent[0], am, threshold)}}


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    bp = root/'benchmarks/kamri_editorial_v7.json'
    cfg, bench = read(root/'experiments/kamri_editorial_v7.json'), read(bp)
    docs = validate(root, bench, cfg)
    out = root/'runs'/run_id
    out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
                'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
                'fresh_condition_denominator': 128, 'fresh_world_denominator': 8,
                'input_hashes': {**bench['input_hashes'], **bench['raw_acquisition_hashes'], str(bp.relative_to(root)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic(); raw = []
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
        prepared = {k: PreparedSource(atoms[k], units[k]) for k in {k for r in bench['records'] for k in r['candidate_ids']}}
        lexicon = read(root/cfg['lexicon_path'])
        ps, gates = {}, {}
        for r in bench['records']:
            ps[r['case_id']], gates[r['case_id']] = predictions(atoms[r['fl_id']], lexicon, cfg['lexicon_rules'], cfg['prediction_variant'])
        rng = random.Random(cfg['shuffle_seed'])
        orders = {r['case_id']: ([] if r['split'] == 'calibration' else nonidentity_orders(len(atoms[r['fl_id']]), cfg['shuffle_repetitions'], rng)) for r in bench['records']}
        dump_json(out/'predictions.json', ps); dump_json(out/'gates.json', gates); dump_json(out/'permutations.json', orders)
        refs = {r['case_id']: r for r in bench['records']}

        def compute(records):
            for index, r in enumerate(records):
                key, cid = r['fl_id'], r['case_id']
                for v in cfg['variants']:
                    caches = {k: EditorialScoreCache(atoms[key], prepared[k], cfg, ps[cid], v) for k in r['candidate_ids']}
                    ranked = []
                    for sk in r['candidate_ids']:
                        a = align(units[key], prepared[sk], caches[sk], cfg, 'tokens')
                        a = label_anchor_origins(decode(a, atoms[key], atoms[sk], ps[cid], cfg, 'ordered'), ps[cid])
                        ranked.append({'source_id': sk, **a})
                    ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                    shuffled = [max(align(ordered_units(units[key], o), prepared[sk], caches[sk], cfg, 'tokens')['strength'] for sk in r['candidate_ids']) for o in orders[cid]]
                    raw.append({k: r.get(k) for k in ('case_id', 'group', 'dataset', 'split', 'seed', 'mask', 'edits')} | {
                        'variant': v['id'], 'rankings': ranked,
                        'shuffle': {'strengths': shuffled, 'repetitions': len(shuffled), 'unique_orders': len({tuple(o) for o in orders[cid]}),
                                    'exceed_or_equal_observed': sum(s >= ranked[0]['strength'] for s in shuffled), 'identity_allowed': False}})
                if r['dataset'] == 'real' or index % 16 == 15:
                    print(f'Computed {cid} ({r["split"]})', flush=True)

        calibration = [r for r in bench['records'] if r['split'] in ('real_development', 'calibration')]
        compute(calibration)
        thresholds = {}
        for dataset, split in [('real', 'real_development'), ('synthetic', 'calibration')]:
            thresholds[dataset] = {v['id']: max(a['strength'] for r in raw if r['split'] == split and r['variant'] == v['id']
                for a in r['rankings'] if (docs[a['source_id']]['source_group'] != r['group'] if dataset == 'real' else a['source_id'] != refs[r['case_id']]['source_id']))+1e-6 for v in cfg['variants']}
        dump_json(out/'calibration_scores.json', raw)
        dump_json(out/'thresholds.json', thresholds)
        manifest.update(calibration_sealed_at_utc=datetime.now(timezone.utc).isoformat(),
                        calibration_thresholds_sha256=digest((out/'thresholds.json').read_bytes()))
        dump_json(out/'manifest.json', manifest)
        print('Calibration sealed; beginning audit/fresh panels', flush=True)
        compute([r for r in bench['records'] if r['split'] in ('real_audit', 'fresh')])
        rows = [finish_row(r, refs[r['case_id']], docs, thresholds[r['dataset']][r['variant']]) for r in raw]
        summaries = []
        for v in cfg['variants']:
            own = [r for r in rows if r['variant'] == v['id']]
            for split in ('real_development', 'real_audit', 'calibration', 'fresh'):
                summaries.append(aggregate([r for r in own if r['split'] == split], split, v['id']))
            for mask in range(16):
                summaries.append(aggregate([r for r in own if r['split'] == 'fresh' and r['mask'] == mask], f'fresh_mask_{mask:02d}', v['id']))
            for seed in cfg['fresh_seeds']:
                summaries.append(aggregate([r for r in own if r['split'] == 'fresh' and r['seed'] == seed], f'fresh_world_{seed}', v['id']))
        report = {'experiment_id': cfg['experiment_id'], 'fresh_condition_denominator': 128, 'fresh_world_denominator': 8,
                  'fresh_real_source_works': 0, 'new_supported_lexical_entries': 0, 'semantic_gold': False,
                  'thresholds': thresholds, 'results': rows, 'summaries': summaries, 'comparisons': comparisons(rows),
                  'evidence': 'Constructed engineering identity truth; paired conditions; real development only'}
        dump_json(out/'raw_scores.json', raw); dump_json(out/'report.json', report)
        dump_json(out/'summary.json', {'thresholds': thresholds, 'summaries': summaries})
        dump_json(out/'comparisons.json', report['comparisons'])
        lines = ['# Experiment 7: controlled editorial robustness', '', '128 fresh conditions from eight paired worlds; 32 calibration conditions from two other worlds. No fresh real work.', '',
                 '| Variant | Unique correct / 128 | Correct admissions | Wrong admissions | Absent false | Edge precision | Edge recall | Token precision | Token recall |',
                 '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for s in summaries:
            if s['panel'] != 'fresh':
                continue
            e, t = s['retrieved_edges'], s['retrieved_tokens']
            lines.append(f'| {s["variant"]} | {s["unique_correct_top1"]} | {s["correct_admissions"]} | {s["wrong_admissions"]} | {s["source_absent_false_admissions"]} | {e["correct"]}/{e["proposed"]} | {e["correct"]}/{e["reference"]} | {t["correct"]}/{t["proposed"]} | {t["correct"]}/{t["reference"]} |')
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        dump_json(out/'partial_scores.json', raw)
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}', elapsed_seconds=time.monotonic()-start)
        dump_json(out/'manifest.json', manifest)
        raise
    return out
