"""Freeze the full paired panel without invoking any alignment scorer."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.editorial_v7 import VARIANTS
from fl_decipher.synthetic_v7 import EDITS, generate

ROOT = Path(__file__).resolve().parents[1]


def main():
    cp, bp = ROOT/'experiments/kamri_editorial_v7.json', ROOT/'benchmarks/kamri_editorial_v7.json'
    if cp.exists() or bp.exists():
        raise ValueError('Preserve existing freeze')
    cfg = json.loads((ROOT/'experiments/kamri_register_v5.json').read_text())
    for k in ('seed', 'shuffle_repetitions', 'development_groups', 'fresh_groups'):
        cfg.pop(k)
    cfg.update(experiment_id='kamri_editorial_v7', registration='experiments/kamri_editorial_v7.md', variants=VARIANTS,
               calibration_seeds=[7401, 7402], fresh_seeds=list(range(7501, 7509)),
               conditions=list(range(16)), edits=EDITS, repetition_bins=8, shuffle_seed=7831, shuffle_repetitions=10,
               prediction_variant='gated_aliases')
    old = json.loads((ROOT/'benchmarks/kamri_register_v5.json').read_text())
    v6 = json.loads((ROOT/'benchmarks/kamri_correspondence_v6.json').read_text())
    bench = {'schema_version': 7, 'status': 'frozen_before_model_execution', 'fresh_condition_denominator': 128,
             'fresh_world_denominator': 8, 'calibration_condition_denominator': 32, 'calibration_world_denominator': 2,
             'fresh_real_source_works': 0, 'documents': {}, 'records': []}
    for r in old['records']:
        if not r['available']:
            continue
        bench['records'].append({**r, 'case_id': 'real_'+r['group'], 'dataset': 'real', 'split': 'real_development',
                                  'candidate_ids': cfg['candidate_ids'], 'token_pairs': None})
        for k in [r['fl_id'], *cfg['candidate_ids']]:
            bench['documents'][k] = old['documents'][k]
    for r in v6['records'][1:]:
        bench['records'].append({**r, 'case_id': 'real_models_magic_'+r['packet'], 'dataset': 'real', 'split': 'real_audit',
                                  'candidate_ids': cfg['candidate_ids'], 'token_pairs': None})
        bench['documents'][r['fl_id']] = v6['documents'][r['fl_id']]
    lexicon = json.loads((ROOT/cfg['lexicon_path']).read_text())
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        for seed in seeds:
            for mask in cfg['conditions']:
                packet = generate(seed, mask, lexicon)
                case = f'editorial_{seed}_m{mask:02d}'
                ids = [case+f'_candidate_{i}' for i in range(4)]
                fk = case+'_query'
                packetpath = ROOT/'data/synthetic_v7'/f'{case}.packet.json'
                if packetpath.exists():
                    raise ValueError(f'Preserve {packetpath}')
                dump_json(packetpath, packet)
                for k, text, kind in [(fk, packet['fl_text'], 'fl'), *[(k, text, 'source') for k, text in zip(ids, packet['candidate_texts'], strict=True)]]:
                    receipt = snapshot(ROOT/'data/raw', f'synthetic://editorial-v7/{k}', content=text.encode(),
                                       acquisition_kind='synthetic_generated', locator=f'seed={seed}; mask={mask}; paired world')
                    doc = normalized_document(k, receipt, text, kind=kind, group=f'world_{seed}',
                                              transformations=['Registered paired editorial generator; exact generated text; no HTTP'])
                    path = ROOT/'data/synthetic_v7'/f'{k}.json'
                    if path.exists():
                        raise ValueError(f'Preserve {path}')
                    dump_json(path, doc)
                    bench['documents'][k] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes()),
                        'text_sha256': doc['text_sha256'], 'raw_sha256': receipt['sha256'], 'source_group': doc['source_group']}
                bench['records'].append({'case_id': case, 'group': f'world_{seed}', 'dataset': 'synthetic', 'split': split,
                    'seed': seed, 'mask': mask, 'edits': packet['edits'], 'fl_id': fk, 'candidate_ids': ids,
                    'source_id': ids[packet['answer_index']], 'edges': packet['edges'], 'token_pairs': packet['token_pairs'],
                    'fl_token_ids': packet['fl_token_ids'], 'source_token_ids': packet['source_token_ids'],
                    'conflicted_fl_spans': packet['conflicted_fl_spans'], 'packet_path': str(packetpath.relative_to(ROOT)),
                    'semantic_gold': False})
    dump_json(cp, cfg)
    paths = [v['path'] for v in bench['documents'].values()] + [r['packet_path'] for r in bench['records'] if r['dataset'] == 'synthetic']
    paths += [str(cp.relative_to(ROOT)), cfg['registration'], cfg['lexicon_path'], 'benchmarks/kamri_register_v5.json',
              'benchmarks/kamri_correspondence_v6.json', 'pyproject.toml', 'uv.lock']
    bench['input_hashes'] = {p: digest((ROOT/p).read_bytes()) for p in paths}
    bench['raw_acquisition_hashes'] = {}
    for k, info in bench['documents'].items():
        doc = json.loads((ROOT/info['path']).read_text())
        bench['raw_acquisition_hashes'][doc['snapshot']['artifact']] = info['raw_sha256']
    dump_json(bp, bench)
    print(f'Frozen {len(bench["records"])} queries: 12 real development/audit, 32 calibration conditions, 128 fresh conditions from 8 worlds.')


if __name__ == '__main__':
    main()
