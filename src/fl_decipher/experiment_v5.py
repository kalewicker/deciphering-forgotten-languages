"""Frozen scoped-register comparison with explicit unavailable denominators."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .experiment_v4 import metrics
from .passage_v3 import PreparedSource, ScoreCache, ordered_units, protected_groups
from .precision_v4 import admission, align, decode
from .register_v5 import ALIASES, label_anchor_origins, predictions
from .text import normal, sentences


def read(path):
    return json.loads(path.read_text())


def validate(root, benchmark, cfg):
    for path, sha in {**benchmark['input_hashes'], **benchmark['raw_acquisition_hashes']}.items():
        assert digest((root/path).read_bytes()) == sha, path
    assert cfg['aliases'] == ALIASES
    assert cfg['development_groups'] == [r['group'] for r in benchmark['records'] if r['split'] == 'development']
    assert cfg['fresh_groups'] == [r['group'] for r in benchmark['records'] if r['split'] == 'fresh']
    assert benchmark['selected_fresh_denominator'] == len(cfg['fresh_groups']) == 2
    assert not set(cfg['development_groups']) & set(cfg['fresh_groups'])
    docs = {}
    for key, info in benchmark['documents'].items():
        path = root/info['path']
        assert digest(path.read_bytes()) == info['sha256'], key
        d = read(path)
        assert digest(d['text'].encode()) == info['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[key] = d
    assert len({docs[k]['source_group'] for k in cfg['candidate_ids']}) == len(cfg['candidate_ids'])
    seen = {}
    for r in benchmark['records']:
        fs = sentences(docs[r['fl_id']]['text'])
        for f in fs:
            key = normal(' '.join(f.text.split()))
            assert key not in seen or seen[key] == r['group'], 'Exact FL duplicate across works'
            seen[key] = r['group']
        if not r['available']:
            assert r['edges'] is None and r['source_id'] not in cfg['candidate_ids']
            continue
        assert r['source_id'] in cfg['candidate_ids'] and docs[r['source_id']]['source_group'] == r['group']
        ss = sentences(docs[r['source_id']]['text'])
        for e in r['edges']:
            assert e['fl_span'] == [fs[e['fl_index']].start, fs[e['fl_index']].end]
            assert e['source_span'] == [ss[e['source_index']].start, ss[e['source_index']].end]
    return docs


def nonidentity_orders(n, repetitions, rng):
    if n < 2:
        return []
    identity, result = list(range(n)), []
    while len(result) < repetitions:
        order = list(identity)
        rng.shuffle(order)
        if order != identity:
            result.append(order)
    return result


def summarize(rows, split, variant):
    selected = [r for r in rows if r['split'] == split and r['variant'] == variant]
    available = [r for r in selected if r['status'] == 'scored']
    result = {'variant': variant, 'split': split, 'selected': len(selected), 'available': len(available),
        'missing': len(selected)-len(available), 'unique_correct_top1': sum(r['unique_correct_top1'] for r in available),
        'correct_admissions': sum(r['admitted'] and r['top_work_correct'] for r in available),
        'wrong_admissions': sum(r['admitted'] and not r['top_work_correct'] for r in available),
        'source_absent_false_admissions': sum(r['source_absent']['false_admission'] for r in available),
        'source_absent_evaluated': len(available), 'selected_sample_alignment_recall': None if len(available) != len(selected) else 'see retrieved_edges',
        'reference_coverage_complete': len(available) == len(selected)}
    for field in ('retrieved_edges', 'conditional_edges'):
        entries = [r[field] for r in available]
        counts = {k: sum(e[k] for e in entries) for k in ('correct', 'proposed', 'reference', 'extra')}
        counts.update(precision=counts['correct']/counts['proposed'] if counts['proposed'] else None,
                      recall_on_available=counts['correct']/counts['reference'] if counts['reference'] else None)
        result[field] = counts
    return result


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    cfgpath, benchpath = root/'experiments/kamri_register_v5.json', root/'benchmarks/kamri_register_v5.json'
    cfg, benchmark = read(cfgpath), read(benchpath)
    docs = validate(root, benchmark, cfg)
    out = root/'runs'/run_id
    out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
        'selected_fresh_denominator': 2, 'available_fresh': sum(r['available'] for r in benchmark['records'] if r['split'] == 'fresh'),
        'input_hashes': {**benchmark['input_hashes'], **benchmark['raw_acquisition_hashes'], str(benchpath.relative_to(root)): digest(benchpath.read_bytes())},
        'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    started = time.monotonic()
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
        lexicon = read(root/cfg['lexicon_path'])
        prepared = {k: PreparedSource(atoms[k], units[k]) for k in cfg['candidate_ids']}
        refs = {r['group']: r for r in benchmark['records']}
        ps, detectors = {}, {}
        for r in benchmark['records']:
            ps[r['group']], detectors[r['group']] = {}, None
            for variant in cfg['variants']:
                ps[r['group']][variant], detectors[r['group']] = predictions(atoms[r['fl_id']], lexicon, cfg['lexicon_rules'], variant)
        # Existing synthetic cases are regression diagnostics, never new evaluation/training.
        synthetic = read(root/'benchmarks/kamri_precision_v4.json')
        regression = []
        for r in synthetic['records']:
            if r['dataset'] != 'synthetic':
                continue
            d = read(root/synthetic['documents'][r['fl_id']]['path'])
            a = sentences(d['text'])
            original, detector = predictions(a, lexicon, cfg['lexicon_rules'], 'baseline')
            before = [p['prediction'] for row in original for p in row]
            entry = {'group': r['group'], 'split': 'development_regression', 'gate': detector, 'changes': {}}
            for variant in cfg['variants']:
                after, _ = predictions(a, lexicon, cfg['lexicon_rules'], variant)
                entry['changes'][variant] = sum(x != y for x, y in zip(before, [p['prediction'] for row in after for p in row], strict=True))
            regression.append(entry)
        dump_json(out/'synthetic_regression.json', regression)
        dump_json(out/'predictions.json', ps)
        dump_json(out/'gates.json', detectors)
        rng = random.Random(cfg['seed'])
        permutations = {r['group']: nonidentity_orders(len(atoms[r['fl_id']]), cfg['shuffle_repetitions'], rng)
                        for r in benchmark['records'] if r['available']}
        dump_json(out/'permutations.json', permutations)
        raw = []
        for r in benchmark['records']:
            if not r['available']:
                continue
            for variant in cfg['variants']:
                predictions_for_query = ps[r['group']][variant]
                caches = {k: ScoreCache(atoms[r['fl_id']], prepared[k], cfg, predictions_for_query) for k in cfg['candidate_ids']}
                ranked = []
                for key in cfg['candidate_ids']:
                    alignment = align(units[r['fl_id']], prepared[key], caches[key], cfg, 'tokens')
                    decoded = decode(alignment, atoms[r['fl_id']], atoms[key], predictions_for_query, cfg, 'ordered')
                    ranked.append({'source_id': key, **label_anchor_origins(decoded, predictions_for_query)})
                ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                strengths = [max(align(ordered_units(units[r['fl_id']], order), prepared[k], caches[k], cfg, 'tokens')['strength']
                                 for k in cfg['candidate_ids']) for order in permutations[r['group']]]
                raw.append({'group': r['group'], 'split': r['split'], 'variant': variant,
                            'rankings': ranked, 'shuffle_strengths': strengths})
            print(f'Computed {r["group"]}', flush=True)
        thresholds = {v: max(a['strength'] for r in raw if r['variant'] == v and r['split'] == 'development'
                              for a in r['rankings'] if docs[a['source_id']]['source_group'] != r['group'])+1e-6
                      for v in cfg['variants']}
        rows = []
        for r in benchmark['records']:
            for variant in cfg['variants']:
                if not r['available']:
                    rows.append({'group': r['group'], 'split': r['split'], 'variant': variant, 'status': 'source_unavailable',
                                 'reason': r['reason'], 'reference_edges': None, 'admitted': None, 'source_absent': None})
                    continue
                rr = next(x for x in raw if x['group'] == r['group'] and x['variant'] == variant)
                ranked, threshold = rr['rankings'], thresholds[variant]
                top = ranked[0]
                margin = top['strength']-ranked[1]['strength']
                correct = top['source_id'] == r['source_id']
                conditional = next(a for a in ranked if a['source_id'] == r['source_id'])
                absent = [a for a in ranked if docs[a['source_id']]['source_group'] != r['group']]
                am = absent[0]['strength']-absent[1]['strength']
                rows.append({'group': r['group'], 'split': r['split'], 'variant': variant, 'status': 'scored', 'rankings': ranked,
                    'threshold': threshold, 'candidate_margin': margin, 'top_work_correct': correct,
                    'unique_correct_top1': correct and margin > 1e-9, 'admitted': admission(top, margin, threshold),
                    'correct_source_rank': next(i+1 for i, a in enumerate(ranked) if a['source_id'] == r['source_id']),
                    'retrieved_edges': metrics(top['edges'], r['edges'], correct), 'conditional_edges': metrics(conditional['edges'], r['edges'], True),
                    'source_absent': {'top': absent[0], 'margin': am, 'false_admission': admission(absent[0], am, threshold)},
                    'shuffle': {'strengths': rr['shuffle_strengths'], 'exceed_or_equal_observed': sum(s >= top['strength'] for s in rr['shuffle_strengths']),
                                'repetitions': len(rr['shuffle_strengths']), 'identity_allowed': False}})
        summaries = [summarize(rows, split, v) for v in cfg['variants'] for split in ('development', 'fresh')]
        report = {'experiment_id': cfg['experiment_id'], 'thresholds': thresholds, 'results': rows, 'summaries': summaries,
                  'alias_audit': read(root/'benchmarks/inputs/register_v5_alias_audit.json'), 'new_supported_lexical_entries': 0,
                  'evidence': 'Single-work register development hypotheses; selected two fresh works, one source unavailable.'}
        dump_json(out/'raw_scores.json', raw)
        dump_json(out/'report.json', report)
        dump_json(out/'summary.json', {'thresholds': thresholds, 'summaries': summaries})
        lines = ['# Experiment 5: scoped lexical aliases', '', 'Two fresh works selected, one source available. No selected-sample alignment recall is claimed.', '',
                 '| Panel | Variant | Available/selected | Unique correct top-1 | Correct admissions | Edge precision | Recall on available references | Absent false/evaluated |',
                 '|---|---|---:|---:|---:|---:|---:|---:|']
        for s in summaries:
            e = s['retrieved_edges']
            lines.append(f'| {s["split"]} | {s["variant"]} | {s["available"]}/{s["selected"]} | {s["unique_correct_top1"]}/{s["selected"]} | {s["correct_admissions"]}/{s["selected"]} | {e["correct"]}/{e["proposed"]} | {e["correct"]}/{e["reference"]} | {s["source_absent_false_admissions"]}/{s["source_absent_evaluated"]} |')
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
                        reference_coverage_complete=False,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}', elapsed_seconds=time.monotonic()-started)
        dump_json(out/'manifest.json', manifest)
        raise
    return out
