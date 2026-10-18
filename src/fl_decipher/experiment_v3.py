"""Frozen factorial passage experiment, with no learning from fresh queries."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import sys
import time

from .alignment_v2 import edge_metrics, without_work
from .corpus import digest, dump_json
from .lexicon import predict
from .passage_v3 import PreparedSource, ScoreCache, align, ordered_units, protected_groups
from .text import normal, sentences


def read(path):
    return json.loads(path.read_text())


def validate(root, benchmark, cfg):
    dev, fresh = set(cfg['development_groups']), set(cfg['fresh_groups'])
    if dev & fresh:
        raise ValueError('Source-group leakage')
    for path, sha in benchmark['input_hashes'].items():
        if digest((root / path).read_bytes()) != sha:
            raise ValueError(f'Input changed after freeze: {path}')
    docs = {}
    for key, info in benchmark['documents'].items():
        d = read(root / info['path'])
        if digest(d['text'].encode()) != info['text_sha256'] or d['source_group'] != info['source_group']:
            raise ValueError('Invalid normalized document')
        raw = Path(d['snapshot']['artifact'])
        if not raw.is_absolute():
            raw = root / raw
        if digest(raw.read_bytes()) != info['raw_sha256']:
            raise ValueError('Raw artifact changed after freeze')
        docs[key] = d
    seen = {}
    for r in benchmark['records']:
        group = r['group']
        if r['split'] != ('fresh' if group in fresh else 'development'):
            raise ValueError('Split mismatch')
        if docs[r['source_id']]['source_group'] != group or docs[r['fl_id']]['source_group'] != group:
            raise ValueError('Reference identity mismatch')
        fs, ss = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        for s in fs:
            key = normal(' '.join(s.text.split()))
            if key in seen and seen[key] != group:
                raise ValueError('Duplicate FL sentence across groups')
            seen[key] = group
        for e in r['edges']:
            f, s = fs[e['fl_index']], ss[e['source_index']]
            if e['fl_span'] != [f.start, f.end] or e['source_span'] != [s.start, s.end]:
                raise ValueError('Reference span changed')
    if {r['group'] for r in benchmark['records']} != dev | fresh:
        raise ValueError('Missing selected query; retain selected denominator in failure report')
    if len(fresh) != benchmark['selected_fresh_denominator']:
        raise ValueError('Selected denominator changed')
    return docs


def factorial_differences(summaries, variants):
    by_id = {s['variant']: s for s in summaries}
    pairs = []
    for factor in ('boundary', 'max_block', 'scoring'):
        other = [k for k in ('boundary', 'max_block', 'scoring') if k != factor]
        levels = ('legacy', 'protected') if factor == 'boundary' else ((1, 2) if factor == 'max_block' else ('structural', 'lexical'))
        for before in variants:
            if before[factor] != levels[0]:
                continue
            after = next(v for v in variants if v[factor] == levels[1] and all(v[k] == before[k] for k in other))
            a, b = by_id[before['id']], by_id[after['id']]
            pairs.append({'factor': factor, 'before': before['id'], 'after': after['id'],
                          'deltas': {k: b[k] - a[k] for k in ('fresh_top1', 'fresh_correct_admissions', 'fresh_correct_edges',
                                    'fresh_proposed_edges', 'fresh_absent_false_admissions', 'development_conditional_correct_edges')}})
    return pairs


def run(root: Path, run_id: str) -> Path:
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError('Run ID must be a simple directory name')
    cfgpath, benchpath = root / 'experiments/kamri_passage_v3a.json', root / 'benchmarks/kamri_passage_v3a.json'
    cfg, benchmark = read(cfgpath), read(benchpath)
    docs = validate(root, benchmark, cfg)
    out = root / 'runs' / run_id
    out.mkdir(parents=True, exist_ok=False)
    code_paths = sorted([*(root / 'src/fl_decipher').glob('*.py'), *(root / 'scripts').glob('*.py'), *(root / 'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
                'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
                'input_hashes': {**benchmark['input_hashes'], str(benchpath.relative_to(root)): digest(benchpath.read_bytes())},
                'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code_paths}, 'selected_fresh_denominator': 2}
    dump_json(out / 'manifest.json', manifest)
    started = time.monotonic()
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        source_ids = cfg['candidate_ids']
        groups = {k: d['source_group'] for k, d in docs.items()}
        if len({groups[k] for k in source_ids}) != 9:
            raise ValueError('Candidate collection must contain nine distinct works')
        lexicon = read(root / cfg['lexicon_path'])
        predictions = {r['group']: [predict(s, lexicon, cfg['lexicon_rules']) for s in atoms[r['fl_id']]] for r in benchmark['records']}
        rng = random.Random(cfg['seed'])
        permutations = {}
        for r in benchmark['records']:
            orders = []
            for _ in range(cfg['shuffle_repetitions']):
                order = list(range(len(atoms[r['fl_id']])))
                rng.shuffle(order)
                orders.append(order)
            permutations[r['group']] = orders
        dump_json(out / 'predictions.json', predictions)
        dump_json(out / 'permutations.json', permutations)
        prepared = {}
        for boundary in ('legacy', 'protected'):
            prepared[boundary] = {}
            for key in source_ids:
                units = [(i,) for i in range(len(atoms[key]))] if boundary == 'legacy' else protected_groups(atoms[key], docs[key]['text'], cfg['abbreviations'])
                prepared[boundary][key] = PreparedSource(atoms[key], units)
        raw_rows = []
        for r in benchmark['records']:
            group, fl_id = r['group'], r['fl_id']
            for boundary in ('legacy', 'protected'):
                base_groups = [(i,) for i in range(len(atoms[fl_id]))] if boundary == 'legacy' else protected_groups(atoms[fl_id], docs[fl_id]['text'], cfg['abbreviations'])
                caches = {key: ScoreCache(atoms[fl_id], prepared[boundary][key], cfg, predictions[group]) for key in source_ids}
                variants = [v for v in cfg['variants'] if v['boundary'] == boundary]
                observed, shuffles = {}, {v['id']: [] for v in variants}
                orders = [list(range(len(atoms[fl_id]))), *permutations[group]]
                for ordinal, order in enumerate(orders):
                    units = ordered_units(base_groups, order)
                    for v in variants:
                        ranked = sorted([{'source_id': key, **align(units, prepared[boundary][key], caches[key], cfg,
                                         max_block=v['max_block'], scoring=v['scoring'])} for key in source_ids],
                                        key=lambda a: (-a['strength'], a['source_id']))
                        if ordinal == 0:
                            observed[v['id']] = ranked
                        else:
                            shuffles[v['id']].append(ranked[0]['strength'])
                for v in variants:
                    raw_rows.append({'group': group, 'split': r['split'], 'variant': v['id'],
                                     'rankings': observed[v['id']], 'shuffle_strengths': shuffles[v['id']]})
                del caches
            print(f"completed query {group}", flush=True)
        results, summaries = [], []
        references = {r['group']: r for r in benchmark['records']}
        for v in cfg['variants']:
            rows = [r for r in raw_rows if r['variant'] == v['id']]
            threshold = max(a['strength'] for r in rows if r['split'] == 'development' for a in r['rankings']
                            if groups[a['source_id']] != r['group']) + 1e-6
            admitted = lambda a: a['strength'] >= threshold and a['minimum_links_met']
            for r in rows:
                group, ranked = r['group'], r['rankings']
                ref = references[group]['edges']
                correct = next(a for a in ranked if groups[a['source_id']] == group)
                top = ranked[0]
                top_correct = groups[top['source_id']] == group
                retrieved = edge_metrics(top['edges'], ref if top_correct else [])
                retrieved.update(reference_edges=len(ref), recall=retrieved['correct_edges'] / len(ref))
                absent = without_work({a['source_id']: a for a in ranked}, group, groups)
                absent_top = sorted(absent.values(), key=lambda a: (-a['strength'], a['source_id']))[0]
                r.update(top_work_correct=top_correct, correct_work_rank=ranked.index(correct) + 1,
                         admitted=admitted(top), threshold=threshold, retrieved_alignment=retrieved,
                         conditional_correct_source_alignment=edge_metrics(correct['edges'], ref),
                         source_absent={'removed_source_ids': [k for k in source_ids if groups[k] == group],
                                        'top': absent_top, 'false_admission': admitted(absent_top)},
                         shuffle={'strengths': r.pop('shuffle_strengths'), 'denominator': cfg['shuffle_repetitions']},
                         annotation_note=references[group]['note'])
                r['shuffle']['exceed_or_equal_observed'] = sum(x >= top['strength'] for x in r['shuffle']['strengths'])
                results.append(r)
            fresh = [r for r in rows if r['split'] == 'fresh']
            dev = [r for r in rows if r['split'] == 'development']
            summaries.append({'variant': v['id'], 'factors': v, 'threshold': threshold, 'fresh_selected': 2, 'fresh_available': len(fresh),
                'fresh_missing': 2 - len(fresh), 'fresh_top1': sum(r['top_work_correct'] for r in fresh),
                'fresh_correct_admissions': sum(r['top_work_correct'] and r['admitted'] for r in fresh),
                'fresh_absent_false_admissions': sum(r['source_absent']['false_admission'] for r in fresh),
                'fresh_correct_edges': sum(r['retrieved_alignment']['correct_edges'] for r in fresh),
                'fresh_proposed_edges': sum(r['retrieved_alignment']['proposed_edges'] for r in fresh),
                'fresh_reference_edges': sum(len(references[r['group']]['edges']) for r in fresh),
                'development_top1': sum(r['top_work_correct'] for r in dev),
                'development_conditional_correct_edges': sum(r['conditional_correct_source_alignment']['correct_edges'] for r in dev),
                'development_conditional_proposed_edges': sum(r['conditional_correct_source_alignment']['proposed_edges'] for r in dev),
                'development_reference_edges': sum(len(references[r['group']]['edges']) for r in dev)})
        differences = factorial_differences(summaries, cfg['variants'])
        report = {'summaries': summaries, 'factorial_differences': differences, 'results': results,
                  'new_lexical_claims': 0, 'annotation': benchmark['annotation'], 'classification': 'exploratory_engineering',
                  'limitations': ['Two nominated fresh source works; no blind discovery', 'Indexed FL excerpts, not raw/current full pages',
                                  'Uneven English candidate scopes', 'Single-analyst structural edges, not semantic gold',
                                  'Cartesian block edges may overlink and are penalized in precision',
                                  'Protected boundaries change effective-unit normalization',
                                  'Thresholds calibrated separately on development negatives; not guarantees',
                                  'Alternate register kept unchanged; common-word lexical anchors can mislead']}
        dump_json(out / 'report.json', report)
        lines = ['# Experiment 3: passage alignment factorial', '', 'All eight variants use match floor 0.72. Seven existing groups are development; two selected groups are fresh. No new lexical claims or semantic accuracy are measured.', '',
                 '| Variant | Fresh top-1 / selected | Correct admissions | Absent false admissions | Correct / proposed / reference edges | Dev conditional correct / proposed / reference edges |',
                 '|---|---:|---:|---:|---:|---:|']
        for s in summaries:
            lines.append(f"| {s['variant']} | {s['fresh_top1']}/2 | {s['fresh_correct_admissions']}/2 | {s['fresh_absent_false_admissions']}/2 | {s['fresh_correct_edges']}/{s['fresh_proposed_edges']}/{s['fresh_reference_edges']} | {s['development_conditional_correct_edges']}/{s['development_conditional_proposed_edges']}/{s['development_reference_edges']} |")
        lines += ['', '## Query outcomes', '', '| Variant | Group | Split | Rank | Admitted | Retrieved correct / proposed / reference | Conditional correct / reference | Shuffle ≥ observed |', '|---|---|---|---:|---|---:|---:|---:|']
        for r in results:
            a, c = r['retrieved_alignment'], r['conditional_correct_source_alignment']
            lines.append(f"| {r['variant']} | {r['group']} | {r['split']} | {r['correct_work_rank']} | {r['admitted']} | {a['correct_edges']}/{a['proposed_edges']}/{a['reference_edges']} | {c['correct_edges']}/{c['reference_edges']} | {r['shuffle']['exceed_or_equal_observed']}/20 |")
        lines += ['', '## Evidence and interpretation limits', '', benchmark['annotation'], '',
                  'Legacy/protected refers to boundary handling. One/multi refers to 1:1 or up-to-2:2 effective units; protected units can themselves contain multiple original atoms. Metrics always use original atomic identities, keeping the same reference denominator. Every inferred Cartesian edge is counted, so merging cannot gain recall without exposing extra-edge errors.', '',
                  'Source identification and annotation are withheld from scoring. Variant-specific thresholds use only development queries; fresh English candidates belong to the fixed pool and may be development distractors. Source-absent controls remove all correct-work editions. Shuffles rebuild adjacent blocks from each permuted atom order, not cached merged rows. The exact v1 lexicon is reused without register normalization.', '',
                  'The 12 matched-factor contrasts are saved in report.json. Eight methods on two fresh inputs are correlated comparisons, not sixteen independent trials. No winner was selected for a second execution.', '', '## Limitations', '']
        lines += ['- ' + x for x in report['limitations']]
        (out / 'report.md').write_text('\n'.join(lines) + '\n')
        manifest.update(state='completed', completed_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started,
                        summaries=summaries, output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out / 'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=repr(exc), elapsed_seconds=time.monotonic() - started)
        dump_json(out / 'manifest.json', manifest)
        raise
    return out
