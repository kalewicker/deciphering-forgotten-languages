"""Registered exhaustive gap search with equally searched nulls and fixed controls."""
from pathlib import Path
import json
import platform
import random
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.gap_v19 import search, control_order, tail

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())

def main():
    cp = ROOT/'experiments/kamri_gap_v19.json'
    cfg = read(cp)
    bp = ROOT/'benchmarks/kamri_gap_v19.json'
    benchmark = read(bp)
    for path, sha in benchmark['input_hashes'].items():
        assert digest((ROOT/path).read_bytes()) == sha, path
    evidence = read(ROOT/benchmark['evidence'])
    prediction, reference = evidence['prediction'], evidence['reference']
    assert cfg['registered_at_utc'] < evidence['sealed_at_utc'] <= benchmark['frozen_at_utc']
    assert evidence['gap_gate']['development_gap_score_eligible']
    assert len(prediction['tokens']) == cfg['fl_token_denominator'] == 21
    assert len(reference['source_tokens']) == cfg['source_token_denominator'] == cfg['gap_denominator'] == 22
    assert cfg['permutations'] == 999 and cfg['p_max'] == 0.01
    out = ROOT/'runs/000019_kamri_single_gap'
    out.mkdir(exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    flags = {'model_executed': True, 'model_kind': 'exhaustive single-gap search using frozen positional predictions',
             'translation_model_executed': False, 'new_lexical_induction_executed': False, 'shared_lexicons_used': False}
    manifest = {'run_id': out.name, 'experiment_id': cfg['experiment_id'], 'stage': cfg['stage'],
                'state': 'running', 'started_at_utc': utc(), **flags,
                'seed': cfg['seed'], 'permutation_denominator': 999, 'unit_denominator': 1,
                'fl_token_denominator': 21, 'source_token_denominator': 22, 'gap_denominator': 22,
                'python': sys.version, 'platform': platform.platform(),
                'input_hashes': benchmark['input_hashes'] | {str(bp.relative_to(ROOT)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic()
    try:
        observed = search(prediction, reference, include_alignments=True)
        dump_json(out/'observed_alignments.json', observed)
        dump_json(out/'evidence.json', evidence)
        controls = []
        for name in cfg['controls']:
            order = control_order(name, 22)
            controls.append({'name': name, 'order': order, 'search': search(prediction, reference, order)})
        dump_json(out/'fixed_controls.json', controls)
        count = observed['maxima']['primary']['matches']
        rng = random.Random(cfg['seed'])
        permutations, values = [], []
        for number in range(999):
            order = list(range(22))
            rng.shuffle(order)
            result = search(prediction, reference, order)
            value = result['maxima']['primary']['matches']
            values.append(value)
            permutations.append({'number': number, 'order': order, 'search': result,
                                 'greater_or_equal_to_observed': value >= count, 'exact_tie': value == count})
        dump_json(out/'permutations.json', permutations)
        available = observed['maxima']['primary']['predictions'] > 0 and evidence['gap_gate']['development_gap_score_eligible']
        test = {'available': available, 'statistic': 'maximum primary matches over all 22 gap positions',
                'observed_max_matches': count, 'null_permutations': 999,
                **tail(count, values), 'registered_p_max': cfg['p_max']}
        if not available:
            test['p_one_sided'] = None
        test['development_gap_criterion_met'] = bool(available and test['p_one_sided']['value'] <= cfg['p_max'])
        report = {'experiment_id': cfg['experiment_id'], 'stage': cfg['stage'], **flags,
                  'unit_uid': cfg['unit_uid'], 'unit_denominator': 1, 'fl_token_denominator': 21,
                  'source_token_denominator': 22, 'gap_denominator': 22,
                  'original_v18_gate': evidence['original_v18_gate'], 'gap_gate': evidence['gap_gate'],
                  'observed': {k: v for k, v in observed.items() if k != 'alignments'},
                  'direct_index_comparator': {'description': 'No internal gap; English index 21 remains unpaired. Not equal-length eligibility.',
                                              'gap': 21, 'stats': observed['alignments'][21]['stats']},
                  'primary_test': test, 'fixed_controls': controls,
                  'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0, 'current_raw_fl': False,
                  'limits': ['One previously exposed development unit, not held-out generalization',
                             'Historical indexed FL evidence only', 'All maximizers retained; no secondary or proper-name tie-break',
                             'English source unchanged; unpaired token retained with its original identity and offsets',
                             'Positional alignments remain hypotheses, not semantic gold']}
        dump_json(out/'report.json', report)
        md = '# Experiment 19: exhaustive single-token-gap diagnostic\n\n'
        md += 'One exposed development unit (03:007), 21 FL tokens and 22 original English source tokens. All 22 gaps are searched in observed, fixed-control and shuffled orders. English tokens are retained with original identities and source offsets; one is unpaired in each hypothesis.\n\n'
        md += f"Primary maximum: {count}/{observed['maxima']['primary']['predictions']} frozen predictions, gaps {observed['maxima']['primary']['gaps']}. Secondary descriptive maximum: {observed['maxima']['secondary']['matches']}/{observed['maxima']['secondary']['predictions']}, gaps {observed['maxima']['secondary']['gaps']}. Maximizer intersection: {observed['maximizer_intersection']}. All indices are zero-based.\n\n"
        md += f"Primary max-search one-sided p = {test['p_one_sided']['value'] if available else 'unavailable'}; {test['greater_or_equal']}/999 null maxima meet or exceed the observed maximum, including {test['exact_ties']} exact ties. Registered criterion p <= 0.01: {'met' if test['development_gap_criterion_met'] else 'not met'}. Secondary scores remain descriptive.\n\n"
        md += '| Gap | Unpaired original English token | Primary matches | Secondary matches |\n|---:|---|---:|---:|\n'
        for a in observed['alignments']:
            md += f"| {a['gap']} | {a['unpaired_source_token']['surface']} | {a['stats']['primary']['matches']} | {a['stats']['secondary']['matches']} |\n"
        md += '\n| Control | Maximum primary matches | Maximum secondary matches |\n|---|---:|---:|\n'
        for c in controls:
            md += f"| {c['name']} | {c['search']['maxima']['primary']['matches']} | {c['search']['maxima']['secondary']['matches']} |\n"
        md += '\nA primary unique gap requires exactly one primary maximizer. Secondary agreement and its intersection cannot choose among primary ties. The original v18 equal-length failure is preserved. The new gate permits only this registered development gap diagnostic. No current raw FL, word meanings, semantic training labels or untouched test units are admitted.\n'
        (out/'report.md').write_text(md)
        manifest.update(state='completed', outcome='conditional_development_gap_signal' if test['development_gap_criterion_met'] else 'registered_development_gap_criterion_not_met',
                        finished_at_utc=utc(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
        print(json.dumps({'maxima': observed['maxima'], 'intersection': observed['maximizer_intersection'], 'primary_test': test}, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}')
        dump_json(out/'manifest.json', manifest)
        raise

if __name__ == '__main__':
    main()
