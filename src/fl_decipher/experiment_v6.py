"""Frozen Misinfons audit: separate retrieval from reference-guided diagnostics."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import sys
import time

from .corpus import digest, dump_json
from .correspondence_v6 import audit
from .experiment_v4 import metrics
from .experiment_v5 import nonidentity_orders
from .passage_v3 import PreparedSource, ScoreCache, ordered_units, protected_groups
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
        if k not in ('experiment_id', 'registration', 'variants', 'seed', 'development_groups', 'fresh_groups'):
            assert cfg[k] == old[k], k
    assert cfg['variants'] == ['baseline', 'gated_aliases'] and cfg['aliases'] == ALIASES
    thresholds = read(root/'runs/000005_kamri_scoped_register/report.json')['thresholds']
    assert cfg['thresholds'] == {v: thresholds[v] for v in cfg['variants']}
    assert bench['selected_within_article_denominator'] == 2 and bench['fresh_independent_works'] == 0
    assert len(bench['records']) == 3 and all(r['available'] for r in bench['records'])
    docs = {}
    for k, info in bench['documents'].items():
        d = read(root/info['path'])
        assert digest((root/info['path']).read_bytes()) == info['sha256']
        assert digest(d['text'].encode()) == info['text_sha256'] == d['text_sha256']
        assert digest((root/d['snapshot']['artifact']).read_bytes()) == info['raw_sha256']
        docs[k] = d
    opening = next(r for r in read(root/'benchmarks/kamri_register_v5.json')['records'] if r['group'] == 'models_magic')
    assert bench['records'][0]['edges'] == opening['edges']
    assert bench['records'][0]['fl_id'] == opening['fl_id']
    seen = set()
    for r in bench['records']:
        assert r['group'] == 'models_magic' and r['source_id'] == 'source_models_magic'
        fa, sa = sentences(docs[r['fl_id']]['text']), sentences(docs[r['source_id']]['text'])
        for f in fa:
            assert f.text not in seen, 'Duplicate atom across selected blocks'
            seen.add(f.text)
        for e in r['edges']:
            assert e['fl_span'] == [fa[e['fl_index']].start, fa[e['fl_index']].end]
            assert e['source_span'] == [sa[e['source_index']].start, sa[e['source_index']].end]
            assert not e['semantic_gold']
    return docs


def run(root, run_id):
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError(run_id)
    bp = root/'benchmarks/kamri_correspondence_v6.json'
    cfg, bench = read(root/'experiments/kamri_correspondence_v6.json'), read(bp)
    docs = validate(root, bench, cfg)
    out = root/'runs'/run_id
    out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(root/'src/fl_decipher').glob('*.py'), *(root/'scripts').glob('*.py'), *(root/'tests').glob('*.py')])
    manifest = {'run_id': run_id, 'experiment_id': cfg['experiment_id'], 'state': 'running',
                'started_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
                'input_hashes': {**bench['input_hashes'], **bench['raw_acquisition_hashes'], str(bp.relative_to(root)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(root)): digest(p.read_bytes()) for p in code},
                'selected_within_article_denominator': 2, 'fresh_independent_works': 0}
    dump_json(out/'manifest.json', manifest)
    started = time.monotonic()
    try:
        atoms = {k: sentences(d['text'], k) for k, d in docs.items()}
        units = {k: protected_groups(atoms[k], d['text'], cfg['abbreviations']) for k, d in docs.items()}
        prepared = {k: PreparedSource(atoms[k], units[k]) for k in cfg['candidate_ids']}
        lexicon = read(root/cfg['lexicon_path'])
        rng = random.Random(cfg['seed'])
        orders = {r['packet']: nonidentity_orders(len(atoms[r['fl_id']]), cfg['shuffle_repetitions'], rng) for r in bench['records']}
        dump_json(out/'permutations.json', orders)
        rows, predicted, gates = [], {}, {}
        # Retrieval never receives reference edges or reference-guided diagnostic output.
        for r in bench['records']:
            packet, key = r['packet'], r['fl_id']
            predicted[packet] = {}
            for v in cfg['variants']:
                ps, gates[packet] = predictions(atoms[key], lexicon, cfg['lexicon_rules'], v)
                predicted[packet][v] = ps
                caches = {k: ScoreCache(atoms[key], prepared[k], cfg, ps) for k in cfg['candidate_ids']}
                ranked = []
                for sk in cfg['candidate_ids']:
                    a = align(units[key], prepared[sk], caches[sk], cfg, 'tokens')
                    a = label_anchor_origins(decode(a, atoms[key], atoms[sk], ps, cfg, 'ordered'), ps)
                    ranked.append({'source_id': sk, **a})
                ranked.sort(key=lambda a: (-a['strength'], a['source_id']))
                strengths = [max(align(ordered_units(units[key], o), prepared[k], caches[k], cfg, 'tokens')['strength']
                                 for k in cfg['candidate_ids']) for o in orders[packet]]
                margin = ranked[0]['strength']-ranked[1]['strength']
                absent = [a for a in ranked if docs[a['source_id']]['source_group'] != r['group']]
                am = absent[0]['strength']-absent[1]['strength']
                conditional = next(a for a in ranked if a['source_id'] == r['source_id'])
                correct = ranked[0]['source_id'] == r['source_id']
                rows.append({'packet': packet, 'split': r['split'], 'variant': v, 'rankings': ranked,
                             'threshold': cfg['thresholds'][v], 'candidate_margin': margin, 'top_work_correct': correct,
                             'unique_correct_top1': correct and margin > 1e-9,
                             'admitted': admission(ranked[0], margin, cfg['thresholds'][v]),
                             'correct_source_rank': next(i+1 for i, a in enumerate(ranked) if a['source_id'] == r['source_id']),
                             'conditional_edges': metrics(conditional['edges'], r['edges'], True),
                             'retrieved_edges': metrics(ranked[0]['edges'], r['edges'], correct),
                             'query_tokens': sum(len(a.tokens) for a in atoms[key]),
                             'prediction_count': sum(p['prediction'] is not None for row in ps for p in row),
                             'admission_capacity_met': len(atoms[key]) >= cfg['minimum_fl_atoms'],
                             'source_absent': {'top': absent[0], 'margin': am, 'false_admission': admission(absent[0], am, cfg['thresholds'][v])},
                             'shuffle': {'strengths': strengths, 'repetitions': len(strengths), 'unique_orders': len({tuple(o) for o in orders[packet]}),
                                         'exceed_or_equal_observed': sum(s >= ranked[0]['strength'] for s in strengths), 'identity_allowed': False}})
            print(f'Computed {packet}', flush=True)
        dump_json(out/'predictions.json', predicted)
        dump_json(out/'gates.json', gates)
        dump_json(out/'retrieval.json', rows)
        # The annotation-guided audit starts only after the retrieval output is saved.
        diagnostics = []
        for r in bench['records']:
            for v in cfg['variants']:
                fk, sk = r['fl_id'], r['source_id']
                diagnostics.append({'packet': r['packet'], 'variant': v,
                    **audit(atoms[fk], atoms[sk], docs[fk]['text'], docs[sk]['text'], r['edges'],
                            units[fk], units[sk], predicted[r['packet']][v], cfg)})
        dump_json(out/'diagnostics.json', diagnostics)
        report = {'experiment_id': cfg['experiment_id'], 'selected_within_article_denominator': 2,
                  'available_within_article_blocks': 2, 'independent_source_works': 1, 'fresh_independent_works': 0,
                  'new_supported_lexical_entries': 0, 'semantic_gold': False, 'thresholds': cfg['thresholds'],
                  'results': rows, 'diagnostics': diagnostics,
                  'limitations': ['Single article and source work; inspected analyst structural labels',
                                  'Indexed FL excerpt, not raw current HTML', 'Reference-guided token paths are hypotheses, not semantic gold',
                                  'Two-atom continuation cannot meet unchanged three-atom admission rule', 'Altruist source remains unavailable']}
        dump_json(out/'report.json', report)
        lines = ['# Experiment 6: Misinfons correspondence audit', '', 'Two within-article blocks selected and available; zero independent fresh works.', '',
                 '| Packet | Variant | Source rank / 10 | Admitted | Conditional edges | Coverage | Positive reference proposals |',
                 '|---|---|---:|---|---:|---:|---:|']
        for r, d in zip(rows, diagnostics, strict=True):
            e = r['conditional_edges']
            lines.append(f'| {r["packet"]} | {r["variant"]} | {r["correct_source_rank"]} | {r["admitted"]} | {e["correct"]}/{e["reference"]} | {r["prediction_count"]}/{r["query_tokens"]} | {d["positive_feasible_reference_proposals"]}/{d["feasible_reference_proposals"]} |')
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}', elapsed_seconds=time.monotonic()-started)
        dump_json(out/'manifest.json', manifest)
        raise
    return out
