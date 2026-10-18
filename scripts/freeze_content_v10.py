"""Freeze paired availability/anchor panels and matched negatives before scoring."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.content_v10 import BACKGROUNDS, VARIANTS, CONTENT_FORMS
from fl_decipher.synthetic_v10 import generate, CONDITIONS

ROOT = Path(__file__).resolve().parents[1]


def main():
    cp, bp = ROOT/'experiments/kamri_content_v10.json', ROOT/'benchmarks/kamri_content_v10.json'
    if cp.exists() or bp.exists():
        raise ValueError('Preserve existing freeze')
    cfg = json.loads((ROOT/'experiments/kamri_coverage_v9.json').read_text())
    cfg.update(experiment_id='kamri_content_v10', registration='experiments/kamri_content_v10.md', variants=VARIANTS,
               backgrounds=BACKGROUNDS, calibration_seeds=list(range(10401, 10433)), fresh_seeds=list(range(10501, 10533)),
               conditions=CONDITIONS, shuffle_seed=10331, content_forms=CONTENT_FORMS, primary_family='content_renamed')
    old = json.loads((ROOT/'benchmarks/kamri_coverage_v9.json').read_text())
    bench = {'schema_version': 10, 'status': 'frozen_before_model_execution', 'fresh_condition_denominator': 576,
             'fresh_world_denominator': 32, 'calibration_condition_denominator': 576, 'calibration_world_denominator': 32,
             'fresh_real_source_works': 0, 'documents': {}, 'records': []}
    for r in old['records']:
        if r['dataset'] != 'real':
            continue
        record = dict(r)
        bench['records'].append(record)
        for k in [r['fl_id'], *r['candidate_ids']]:
            bench['documents'][k] = old['documents'][k]
    lexicon = json.loads((ROOT/cfg['lexicon_path']).read_text())
    from fl_decipher.lexicon import predict
    from fl_decipher.text import sentences
    for meaning, form in CONTENT_FORMS.items():
        p = predict(sentences(form+'.')[0], lexicon, cfg['lexicon_rules'])[0]
        assert p['prediction'] == meaning, 'Frozen roster is not eligible'
    for split, seeds in [('calibration', cfg['calibration_seeds']), ('fresh', cfg['fresh_seeds'])]:
        for seed in seeds:
            for condition in cfg['conditions']:
                packet = generate(seed, **condition, lexicon=lexicon)
                case = f'content_{seed}_{condition["density"]}_{condition["extent"]}_{condition["family"]}'
                ids = [case+f'_candidate_{i}' for i in range(4)]; fk = case+'_query'
                packetpath = ROOT/'data/synthetic_v10'/f'{case}.packet.json'
                if packetpath.exists():
                    raise ValueError(f'Preserve {packetpath}')
                dump_json(packetpath, packet)
                for k, text, kind in [(fk, packet['fl_text'], 'fl'), *[(k, text, 'source') for k, text in zip(ids, packet['candidate_texts'], strict=True)]]:
                    receipt = snapshot(ROOT/'data/raw', f'synthetic://content-v10/{k}', content=text.encode(),
                                       acquisition_kind='synthetic_generated', locator=f'seed={seed}; {condition}; v10 frozen content capacity')
                    doc = normalized_document(k, receipt, text, kind=kind, group=f'world_{seed}',
                                              transformations=['V7 skeleton with fixed content-density probes and matched controls; no HTTP'])
                    path = ROOT/'data/synthetic_v10'/f'{k}.json'
                    if path.exists():
                        raise ValueError(f'Preserve {path}')
                    dump_json(path, doc)
                    bench['documents'][k] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes()),
                        'text_sha256': doc['text_sha256'], 'raw_sha256': receipt['sha256'], 'source_group': doc['source_group']}
                bench['records'].append({'case_id': case, 'group': f'world_{seed}', 'dataset': 'synthetic', 'split': split,
                    'seed': seed, **condition, 'fl_id': fk, 'candidate_ids': ids,
                    'source_id': ids[packet['answer_index']], 'edges': packet['edges'], 'token_pairs': packet['token_pairs'],
                    'fl_token_ids': packet['fl_token_ids'], 'source_token_ids': packet['source_token_ids'],
                    'content_query_uids': packet['content_query_uids'], 'probe_positions': packet['probe_positions'], 'unavailable_query_uids': packet['unavailable_query_uids'], 'candidate_roles': packet['candidate_roles'], 'packet_path': str(packetpath.relative_to(ROOT)), 'semantic_gold': False})
    dump_json(cp, cfg)
    paths = [v['path'] for v in bench['documents'].values()] + [r['packet_path'] for r in bench['records'] if r['dataset'] == 'synthetic']
    paths += [str(cp.relative_to(ROOT)), cfg['registration'], cfg['lexicon_path'], 'benchmarks/kamri_coverage_v9.json',
              'experiments/kamri_coverage_v9.json', 'pyproject.toml', 'uv.lock']
    bench['input_hashes'] = {p: digest((ROOT/p).read_bytes()) for p in paths}
    bench['raw_acquisition_hashes'] = {}
    for info in bench['documents'].values():
        doc = json.loads((ROOT/info['path']).read_text())
        bench['raw_acquisition_hashes'][doc['snapshot']['artifact']] = info['raw_sha256']
    dump_json(bp, bench)
    print(f'Frozen {len(bench["records"])} queries: 576 calibration + 576 fresh conditions (32 worlds each), 12 real diagnostics.')


if __name__ == '__main__':
    main()
