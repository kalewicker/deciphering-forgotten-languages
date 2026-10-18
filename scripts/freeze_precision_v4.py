"""Freeze the registered controlled corpus without invoking an alignment model."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.synthetic_v4 import FAMILIES, generate

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'benchmarks/kamri_precision_v4.json'
    cfgpath = ROOT / 'experiments/kamri_precision_v4.json'
    if output.exists() or cfgpath.exists():
        raise ValueError('Freeze already exists; preserve it')
    cfg = json.loads((ROOT / 'experiments/kamri_passage_v3a.json').read_text())
    cfg.update(experiment_id='kamri_precision_v4', registration='experiments/kamri_precision_v4.md',
               reference_tokens=20, token_gap=-.75, token_exact=2., token_mismatch=-2.,
               token_unknown=.5, edge_minimum_pairs=2, real_shuffle_seed=4731,
               synthetic_shuffle_seed=4831, real_shuffle_repetitions=20,
               synthetic_shuffle_repetitions=10, calibration_seeds=list(range(4301, 4309)),
               fresh_seeds=list(range(4401, 4441)), families=list(FAMILIES),
               variants=[{'id': f'{r}_{e}', 'reward': r, 'decoder': e}
                         for r in ('effective', 'tokens') for e in ('cartesian', 'ordered')])
    for key in ('development_groups', 'fresh_groups', 'seed', 'shuffle_repetitions', 'preparation_amendment'):
        cfg.pop(key, None)
    original = json.loads((ROOT / 'benchmarks/kamri_passage_v3a.json').read_text())
    benchmark = {'schema_version': 4, 'status': 'frozen_before_model_execution',
                 'selected_fresh_denominator': 40, 'calibration_denominator': 8,
                 'documents': dict(original['documents']), 'records': []}
    for record in original['records']:
        benchmark['records'].append({**record, 'dataset': 'real', 'split': 'development',
                                      'candidate_ids': cfg['candidate_ids'], 'token_pairs': None})
    lexicon = json.loads((ROOT / cfg['lexicon_path']).read_text())
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        for index, seed in enumerate(seeds):
            family = FAMILIES[index % len(FAMILIES)]
            packet = generate(seed, family, lexicon)
            case = f'synthetic_{seed}'
            fl_id = case + '_query'
            candidate_ids = [case + f'_candidate_{i}' for i in range(4)]
            for key, text, kind in [(fl_id, packet['fl_text'], 'fl'),
                                    *[(key, text, 'source') for key, text in zip(candidate_ids, packet['candidate_texts'], strict=True)]]:
                receipt = snapshot(ROOT / 'data/raw', f'synthetic://precision-v4/{key}', content=text.encode(),
                                   acquisition_kind='synthetic_generated', locator=f'seed={seed}; family={family}')
                document = normalized_document(key, receipt, text, kind=kind, group=case,
                                               transformations=['Registered seeded synthetic generator; no HTTP acquisition'])
                path = ROOT / 'data/synthetic_v4' / f'{key}.json'
                dump_json(path, document)
                benchmark['documents'][key] = {'path': str(path.relative_to(ROOT)),
                    'sha256': digest(path.read_bytes()), 'text_sha256': document['text_sha256'],
                    'raw_sha256': receipt['sha256'], 'source_group': case}
            benchmark['records'].append({'group': case, 'dataset': 'synthetic', 'split': split,
                'family': family, 'seed': seed, 'fl_id': fl_id, 'candidate_ids': candidate_ids,
                'source_id': candidate_ids[packet['answer_index']], 'edges': packet['edges'],
                'token_pairs': packet['token_pairs'], 'fl_token_ids': packet['fl_token_ids'],
                'source_token_ids': packet['source_token_ids'], 'substitution_key': packet['substitution_key'],
                'note': 'Constructed substitution identity truth; original frozen function hypotheses agree by construction.'})
    dump_json(cfgpath, cfg)
    paths = [v['path'] for v in benchmark['documents'].values()]
    paths += ['experiments/kamri_precision_v4.md', str(cfgpath.relative_to(ROOT)),
              'benchmarks/kamri_passage_v3a.json', cfg['lexicon_path']]
    benchmark['input_hashes'] = {p: digest((ROOT/p).read_bytes()) for p in paths}
    dump_json(output, benchmark)
    print(f'Frozen {len(benchmark["records"])} queries, {len(benchmark["documents"])} documents: {output}')


if __name__ == '__main__':
    main()
