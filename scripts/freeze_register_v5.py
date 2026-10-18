"""Freeze development aliases and independently audited fresh source spans."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.register_v5 import ALIASES
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT/'benchmarks/kamri_register_v5.json'
    cfgpath = ROOT/'experiments/kamri_register_v5.json'
    if out.exists() or cfgpath.exists():
        raise ValueError('Preserve existing freeze')
    old = json.loads((ROOT/'benchmarks/kamri_passage_v3a.json').read_text())
    cfg = json.loads((ROOT/'experiments/kamri_precision_v4.json').read_text())
    cfg = {k: v for k, v in cfg.items() if k not in ('variants', 'real_shuffle_seed', 'synthetic_shuffle_seed', 'real_shuffle_repetitions',
        'synthetic_shuffle_repetitions', 'calibration_seeds', 'fresh_seeds', 'families')}
    cfg.update(experiment_id='kamri_register_v5', registration='experiments/kamri_register_v5.md',
               variants=['baseline', 'universal_aliases', 'gated_aliases'], aliases=ALIASES,
               gate_minimum_distinct=2, gate_minimum_total=3, seed=5731, shuffle_repetitions=20,
               development_groups=[r['group'] for r in old['records']],
               fresh_groups=['capra_foreword', 'accidental_altruist'])
    benchmark = {'schema_version': 5, 'status': 'frozen_before_model_execution', 'selected_fresh_denominator': 2,
                 'documents': dict(old['documents']), 'records': [{**r, 'split': 'development', 'available': True} for r in old['records']]}
    for group in cfg['fresh_groups']:
        key = 'fl_'+group+'_v5'
        keys = [key]+(['source_capra_foreword_v5'] if group == 'capra_foreword' else [])
        for doc_id in keys:
            path = ROOT/'data/normalized'/f'{doc_id}.json'
            d = json.loads(path.read_text())
            benchmark['documents'][doc_id] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes()),
                'text_sha256': d['text_sha256'], 'raw_sha256': d['snapshot']['sha256'], 'source_group': group}
        record = {'group': group, 'fl_id': key, 'source_id': 'source_'+group+'_v5', 'split': 'fresh',
                  'available': group == 'capra_foreword', 'edges': None,
                  'note': 'Selected before scoring; independently published source nominated by public report.'}
        if record['available']:
            fs = sentences(json.loads((ROOT/benchmark['documents'][key]['path']).read_text())['text'])
            ss = sentences(json.loads((ROOT/benchmark['documents'][record['source_id']]['path']).read_text())['text'])
            # Visual/text audit of publisher PDF page 7, printed x, before any model scores.
            assert len(fs) == 6 and ss[17].text.startswith('In modern physics,')
            record['edges'] = [{'fl_index': i, 'source_index': 17+i, 'fl_span': [f.start, f.end],
                               'source_span': [ss[17+i].start, ss[17+i].end],
                               'state': 'single_analyst_structural_correspondence', 'semantic_gold': False}
                              for i, f in enumerate(fs)]
            record['note'] += ' Six opening FL statements follow six consecutive Capra statements; first four equal token counts; source scan checked.'
            cfg['candidate_ids'].append(record['source_id'])
        else:
            record.update(status='source_unavailable', reference_coverage='unavailable',
                          reason='Finite public-source acquisition returned subscription HTML and abstract, not chapter prose; retain selected denominator.')
        benchmark['records'].append(record)
    dump_json(cfgpath, cfg)
    paths = [v['path'] for v in benchmark['documents'].values()]
    paths += [cfg['registration'], str(cfgpath.relative_to(ROOT)), cfg['lexicon_path'], 'benchmarks/kamri_passage_v3a.json',
              'benchmarks/kamri_precision_v4.json', 'benchmarks/inputs/register_v5_alias_audit.json',
              'benchmarks/inputs/register_v5_acquisition.json', 'pyproject.toml', 'uv.lock']
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/'data/v5').glob('*.json')]
    paths += ['data/v5/capra_frontmatter.pdf', 'data/v5/qa/capra_page7.png']
    regression = json.loads((ROOT/'benchmarks/kamri_precision_v4.json').read_text())
    paths += [regression['documents'][r['fl_id']]['path'] for r in regression['records'] if r['dataset'] == 'synthetic']
    benchmark['input_hashes'] = {p: digest((ROOT/p).read_bytes()) for p in paths}
    benchmark['raw_acquisition_hashes'] = {}
    for p in (ROOT/'data/v5').glob('*.receipt.json'):
        receipt = json.loads(p.read_text())
        benchmark['raw_acquisition_hashes'][receipt['artifact']] = receipt['sha256']
    dump_json(out, benchmark)
    print(f'Frozen 9 development + 2 selected fresh (1 available), {len(cfg["candidate_ids"])} candidates')


if __name__ == '__main__':
    main()
