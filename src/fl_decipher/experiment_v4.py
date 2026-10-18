"""One frozen execution of the registered precision/mass experiment."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .lexicon import predict
from .passage_v3 import PreparedSource, ScoreCache, ordered_units, protected_groups
from .precision_v4 import admission, align, block_reward, decode
from .synthetic_v4 import FAMILIES
from .text import sentences


def read(path):
    return json.loads(path.read_text())


def validate(root, benchmark, cfg):
    for path, sha in benchmark['input_hashes'].items():
        if digest((root/path).read_bytes()) != sha:
            raise ValueError(f'Frozen input changed: {path}')
    docs = {}
    for key, info in benchmark['documents'].items():
        path = root/info['path']
        if digest(path.read_bytes()) != info['sha256']:
            raise ValueError(f'Document changed: {key}')
        doc = read(path)
        if digest(doc['text'].encode()) != info['text_sha256']:
            raise ValueError(key)
        raw = Path(doc['snapshot']['artifact'])
        if not raw.is_absolute():
            raw = root/raw
        if digest(raw.read_bytes()) != info['raw_sha256']:
            raise ValueError(f'Raw changed: {key}')
        docs[key] = doc
    real = [r for r in benchmark['records'] if r['dataset'] == 'real']
    fresh = [r for r in benchmark['records'] if r['split'] == 'fresh']
    calibration = [r for r in benchmark['records'] if r['split'] == 'calibration']
    assert len(real) == 9 and all(r['split'] == 'development' for r in real)
    assert len(fresh) == benchmark['selected_fresh_denominator'] == 40
    assert len(calibration) == benchmark['calibration_denominator'] == 8
    assert [r['seed'] for r in calibration] == cfg['calibration_seeds']
    assert [r['seed'] for r in fresh] == cfg['fresh_seeds']
    assert all(sum(r['family'] == f for r in fresh) == 5 for f in FAMILIES)
    for r in benchmark['records']:
        fa, sa = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        assert r['source_id'] in r['candidate_ids']
        for e in r['edges']:
            f, s = fa[e['fl_index']], sa[e['source_index']]
            assert e['fl_span'] == [f.start, f.end] and e['source_span'] == [s.start, s.end]
        if r['dataset'] == 'synthetic':
            assert len(r['candidate_ids']) == 4
            fi = {item['uid']: item for item in r['fl_token_ids']}
            si = {item['uid']: item for item in r['source_token_ids'] if item['uid'] is not None}
            assert {p['uid'] for p in r['token_pairs']} == fi.keys() & si.keys()
            for p in r['token_pairs']:
                f, s = fi[p['uid']], si[p['uid']]
                assert p['fl_span'] == f['span'] and p['source_span'] == s['span']
                assert p['fl_index'] == f['atom_index'] and p['source_index'] == s['atom_index']
                assert any([t.start, t.end] == p['fl_span'] for t in fa[p['fl_index']].tokens)
                assert any([t.start, t.end] == p['source_span'] for t in sa[p['source_index']].tokens)
            assert {(p['fl_index'], p['source_index']) for p in r['token_pairs']} == {(e['fl_index'], e['source_index']) for e in r['edges']}
    return docs


def metrics(predicted, reference, correct_source, token=False):
    if predicted is None:
        return None
    if token:
        key = lambda e: (tuple(e['fl_span']), tuple(e['source_span']))
    else:
        key = lambda e: (e['fl_index'], e['source_index'])
    proposed, gold = {key(e) for e in predicted}, {key(e) for e in reference}
    correct = len(proposed & gold) if correct_source else 0
    return {'correct': correct, 'proposed': len(proposed), 'reference': len(gold),
            'extra': len(proposed)-correct, 'precision': correct/len(proposed) if proposed else None,
            'recall': correct/len(gold) if gold else None}


def aggregate(rows, name, variant):
    result = {'variant': variant, 'panel': name, 'selected': len(rows),
              'unique_correct_top1': sum(r['unique_correct_top1'] for r in rows),
              'correct_admissions': sum(r['admitted'] and r['top_work_correct'] for r in rows),
              'wrong_admissions': sum(r['admitted'] and not r['top_work_correct'] for r in rows),
              'source_absent_false_admissions': sum(r['source_absent']['false_admission'] for r in rows)}
    for field in ('retrieved_edges', 'conditional_edges', 'retrieved_tokens'):
        entries = [r[field] for r in rows if r[field] is not None]
        if not entries:
            result[field] = None
            continue
        counts = {key: sum(e[key] for e in entries) for key in ('correct', 'proposed', 'reference', 'extra')}
        counts['precision'] = counts['correct']/counts['proposed'] if counts['proposed'] else None
        counts['recall'] = counts['correct']/counts['reference'] if counts['reference'] else None
        result[field] = counts
    return result


def metamorphic(raw, refs, atoms, groups, cfg):
    result, seen = [], set()
    def effective(ids, units):
        inside = [u for u in units if any(i in ids for i in u)]
        flat = tuple(i for u in inside for i in u)
        return len(inside) if flat == tuple(ids) else None
    for row in raw:
        if row['dataset'] != 'real':
            continue
        r = refs[row['group']]
        for a in row['rankings']:
            for block in a['blocks']:
                fi, si = block['fl_atoms'], block['source_atoms']
                identity = (row['group'], a['source_id'], tuple(fi), tuple(si))
                if identity in seen:
                    continue
                seen.add(identity)
                legacy = (len(fi), len(si))
                protected = (effective(fi, groups[r['fl_id']]), effective(si, groups[a['source_id']]))
                if any(x is None or x > 2 for x in protected) or max(legacy) > 2:
                    continue
                fw = sum(len(atoms[r['fl_id']][i].tokens) for i in fi)
                sw = sum(len(atoms[a['source_id']][i].tokens) for i in si)
                entry = {'group': row['group'], 'source_id': a['source_id'], 'fl_atoms': fi,
                         'source_atoms': si, 'similarity': block['similarity'], 'fl_words': fw, 'source_words': sw,
                         'legacy_units': list(legacy), 'protected_units': list(protected)}
                for mode in ('effective', 'tokens'):
                    before = block_reward(block['similarity'], *legacy, fw, sw, cfg, mode)
                    after = block_reward(block['similarity'], *protected, fw, sw, cfg, mode)
                    entry[mode] = {'legacy_reward': before, 'protected_reward': after, 'difference': after-before}
                result.append(entry)
    return result


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    cfgpath, benchpath = root/'experiments/kamri_precision_v4.json', root/'benchmarks/kamri_precision_v4.json'
    cfg, benchmark = read(cfgpath), read(benchpath)
    docs = validate(root, benchmark, cfg)
    out = root/'runs'/run_id
    out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
                'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
                'platform': platform.platform(), 'selected_fresh_denominator': 40,
                'input_hashes': {**benchmark['input_hashes'], str(benchpath.relative_to(root)): digest(benchpath.read_bytes())},
                'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    started = time.monotonic()
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        groups = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
        lexicon = read(root/cfg['lexicon_path'])
        refs = {r['group']: r for r in benchmark['records']}
        predictions = {r['group']: [predict(s, lexicon, cfg['lexicon_rules']) for s in atoms[r['fl_id']]] for r in benchmark['records']}
        rngs = {'real': random.Random(cfg['real_shuffle_seed']), 'synthetic': random.Random(cfg['synthetic_shuffle_seed'])}
        permutations = {}
        for r in benchmark['records']:
            count = 0 if r['split'] == 'calibration' else cfg[r['dataset']+'_shuffle_repetitions']
            orders = []
            for _ in range(count):
                order = list(range(len(atoms[r['fl_id']])))
                rngs[r['dataset']].shuffle(order)
                orders.append(order)
            permutations[r['group']] = orders
        dump_json(out/'predictions.json', predictions)
        dump_json(out/'permutations.json', permutations)
        prepared = {k: PreparedSource(atoms[k], groups[k]) for k in {s for r in benchmark['records'] for s in r['candidate_ids']}}
        raw = []
        for index, r in enumerate(benchmark['records']):
            fa, ps = atoms[r['fl_id']], predictions[r['group']]
            caches = {k: ScoreCache(fa, prepared[k], cfg, ps) for k in r['candidate_ids']}
            for mode in ('effective', 'tokens'):
                ranked = [{'source_id': k, **align(groups[r['fl_id']], prepared[k], caches[k], cfg, mode)} for k in r['candidate_ids']]
                ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                shuffled = []
                for order in permutations[r['group']]:
                    units = ordered_units(groups[r['fl_id']], order)
                    shuffled.append(max(align(units, prepared[k], caches[k], cfg, mode)['strength'] for k in r['candidate_ids']))
                raw.append({'group': r['group'], 'dataset': r['dataset'], 'split': r['split'],
                            'family': r.get('family'), 'reward': mode, 'rankings': ranked,
                            'shuffle_strengths': shuffled})
            print(f'Computed {index+1}/57: {r["group"]}', flush=True)
        thresholds = {}
        for dataset, split in [('real', 'development'), ('synthetic', 'calibration')]:
            for mode in ('effective', 'tokens'):
                values = [a['strength'] for r in raw if r['dataset'] == dataset and r['split'] == split and r['reward'] == mode
                          for a in r['rankings'] if a['source_id'] != refs[r['group']]['source_id']]
                thresholds[dataset+'_'+mode] = max(values)+1e-6
        rows = []
        for rawrow in raw:
            r = refs[rawrow['group']]
            for decoder in ('cartesian', 'ordered'):
                ranked = [{'source_id': a['source_id'], **decode(a, atoms[r['fl_id']], atoms[a['source_id']], predictions[r['group']], cfg, decoder)}
                          for a in rawrow['rankings']]
                top = ranked[0]
                margin = top['strength']-ranked[1]['strength']
                threshold = thresholds[r['dataset']+'_'+rawrow['reward']]
                # All editions of the real work are removed by work identity.
                absent = [a for a in ranked if (docs[a['source_id']]['source_group'] != r['group'] if r['dataset'] == 'real'
                                               else a['source_id'] != r['source_id'])]
                absent_margin = absent[0]['strength']-absent[1]['strength']
                conditional = next(a for a in ranked if a['source_id'] == r['source_id'])
                correct = top['source_id'] == r['source_id']
                row = {k: rawrow[k] for k in ('group', 'dataset', 'split', 'family', 'reward')}
                row.update(variant=rawrow['reward']+'_'+decoder, decoder=decoder, rankings=ranked,
                           threshold=threshold, candidate_margin=margin, top_work_correct=correct,
                           unique_correct_top1=correct and margin > 1e-9,
                           admitted=admission(top, margin, threshold),
                           retrieved_edges=metrics(top['edges'], r['edges'], correct),
                           conditional_edges=metrics(conditional['edges'], r['edges'], True),
                           retrieved_tokens=metrics(top['token_pairs'], r['token_pairs'], correct, token=True) if r['dataset'] == 'synthetic' else None,
                           source_absent={'top': absent[0], 'margin': absent_margin,
                                          'false_admission': admission(absent[0], absent_margin, threshold)},
                           shuffle={'strengths': rawrow['shuffle_strengths'], 'repetitions': len(rawrow['shuffle_strengths']),
                                    'exceed_or_equal_observed': sum(v >= top['strength'] for v in rawrow['shuffle_strengths'])})
                rows.append(row)
        summaries = []
        for variant in cfg['variants']:
            own = [r for r in rows if r['variant'] == variant['id']]
            for split in ('development', 'calibration', 'fresh'):
                summaries.append(aggregate([r for r in own if r['split'] == split], split, variant['id']))
            for family in FAMILIES:
                summaries.append(aggregate([r for r in own if r['split'] == 'fresh' and r['family'] == family], 'fresh_'+family, variant['id']))
        metamorph = metamorphic(raw, refs, atoms, groups, cfg)
        report = {'experiment_id': cfg['experiment_id'], 'evidence': 'synthetic engineering evaluation; nine real development diagnostics',
                  'thresholds': thresholds, 'results': rows, 'summaries': summaries,
                  'metamorphic': metamorph, 'new_lexical_claims': 0, 'fresh_real_source_works': 0}
        dump_json(out/'report.json', report)
        dump_json(out/'raw_scores.json', raw)
        lines = ['# Experiment 4: reward mass and internal precision', '',
                 'Forty fresh synthetic cases; eight synthetic calibration cases; nine real development works. No semantic decipherment claim.', '',
                 '| Panel | Variant | Unique correct top-1 | Correct admissions | Edge precision | Edge recall | Absent false admissions |',
                 '|---|---|---:|---:|---:|---:|---:|']
        for s in summaries:
            e = s['retrieved_edges']
            lines.append(f'| {s["panel"]} | {s["variant"]} | {s["unique_correct_top1"]}/{s["selected"]} | {s["correct_admissions"]}/{s["selected"]} | {e["correct"]}/{e["proposed"]} | {e["correct"]}/{e["reference"]} | {s["source_absent_false_admissions"]}/{s["selected"]} |')
        lines += ['', 'Ordered token paths use frozen lexical anchors and a positional prior. Cartesian variants make no token-pair claim.', '',
                  'Full rankings, provisional token pairs, conditional metrics, family counts, controls, and direct boundary rewards are saved in report.json.']
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        dump_json(out/'summary.json', {'thresholds': thresholds, 'summaries': summaries,
            'metamorphic_pairs': len(metamorph),
            'effective_changed_rewards': sum(abs(e['effective']['difference']) > 1e-12 for e in metamorph),
            'token_changed_rewards': sum(abs(e['tokens']['difference']) > 1e-12 for e in metamorph),
            'maximum_token_reward_difference': max((abs(e['tokens']['difference']) for e in metamorph), default=0.)})
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        elapsed_seconds=time.monotonic()-started,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}', elapsed_seconds=time.monotonic()-started)
        dump_json(out/'manifest.json', manifest)
        raise
    return out
