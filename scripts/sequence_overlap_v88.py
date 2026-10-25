"""Register and execute one read-only audit; never fit or predict."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from fl_decipher.sequence_overlap_v88 import matches, coverage, aggregate, macro

ROOT = Path(__file__).resolve().parents[1]
REG = 'experiments/sequence_overlap_v88.json'
OUT = 'runs/000088_sequence_overlap'
CODE = ['experiments/sequence_overlap_v88.md', 'src/fl_decipher/sequence_overlap_v88.py',
        'scripts/sequence_overlap_v88.py', 'scripts/verify_sequence_overlap_v88.py',
        'tests/test_sequence_overlap_v88.py']


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    dest = ROOT/path
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def prepare():
    paths = set(CODE)
    for version in (76, 77, 79, 87):
        seal = f'reports/{version:06}_deliverable_seal.json'
        paths.add(seal)
        for path, digest in read(seal)['deliverable_hashes'].items():
            assert sha(path) == digest, path
            paths.add(path)
    write(REG, {'experiment_id': 'sequence_overlap_v88', 'registered_at_utc': now(),
                'input_hashes': {p: sha(p) for p in sorted(paths)},
                'lengths': list(range(2, 9)), 'groups': 13, 'units': 98, 'pairs': 1918,
                'new_predictions': False, 'network_requests': 0,
                'purpose': 'exposed_development_exact_overlap_accounting'})
    print('Frozen exact-overlap audit; no corpus overlap computed.')


def run():
    reg = read(REG)
    for path, digest in reg['input_hashes'].items():
        assert sha(path) == digest, path
    (ROOT/OUT).mkdir(exist_ok=False)
    manifest = {'experiment_id': 'sequence_overlap_v88', 'state': 'running',
                'started_at_utc': now(), 'input_hashes': reg['input_hashes'] | {REG: sha(REG)},
                'new_predictions': False, 'network_requests': 0}
    write(OUT+'/manifest.json', manifest)
    try:
        original = read('runs/000079_context_guard/report.json')
        groups = [f['group'] for f in original['folds']]
        units = [r for r in read('runs/000076_order_corpus/unit_ledger.json')
                 if r['exclusion'] is None and r['group'] in groups]
        assert len(groups) == len(set(groups)) == 13 and len(units) == 98
        lookup = {r['uid']: r for r in units}
        assert len(lookup) == 98
        folds = []
        for fi, group in enumerate(groups):
            saved = read(f'runs/000079_context_guard/fold_{fi:02}.json')
            assert saved['group'] == group
            assert saved['training_groups'] == [g for g in groups if g != group]
            held = [r for r in units if r['group'] == group]
            train = [r for r in units if r['group'] != group]
            occurrences = matches(held, train)
            covered = coverage(occurrences)
            ledger = []
            for j, target in enumerate(saved['targets']):
                uid, a, b = target['uid'], target['context_index'], target['target_index']
                r = lookup[uid]
                assert r['group'] == group and b == a+1 and r['tokens'][b]['pair_from_previous']
                binding = r['canonical_binding']
                lengths = sorted(covered.get((uid, a, b), set()))
                u, p = saved['unigram_probabilities'][j], saved['observed_probabilities'][j]
                assert 0 < u <= 1 and 0 < p <= 1
                ledger.append({'uid': uid, 'context_index': a, 'target_index': b,
                               'source_path': binding['path'],
                               'context_span': [binding['start']+r['tokens'][a][k] for k in ('start', 'end')],
                               'target_span': [binding['start']+r['tokens'][b][k] for k in ('start', 'end')],
                               'covered_lengths': lengths, 'max_covered_length': max(lengths, default=0),
                               'unigram_probability': u, 'saved_probability': p,
                               'changed': p != u, 'gain': math.log2(p/u)})
            stats = aggregate(ledger)
            assert math.isclose(stats['total']['contribution'], saved['observed']['gain'], abs_tol=1e-12)
            folds.append({'group': group, 'units': len(held), 'occurrence_matches': len(occurrences), **stats})
            write(OUT+f'/fold_{fi:02}.json', {'group': group, 'matches': occurrences, 'targets': ledger})
        summary = macro(folds)
        assert summary['total']['pairs'] == 1918
        assert summary['total']['changed_predictions'] == 311
        assert math.isclose(summary['total']['contribution'], original['summary']['macro_gain'], abs_tol=1e-12)
        report = {'experiment_id': 'sequence_overlap_v88', 'groups': 13, 'units': 98,
                  'pairs': 1918, 'folds': folds, 'macro': summary, 'new_predictions': False,
                  'network_requests': 0, 'new_confirmation_units': 0,
                  'semantic_benchmark_qualifying_works': 0, 'e79_gate_retested': False}
        write(OUT+'/report.json', report)
        manifest.update(state='complete', finished_at_utc=now(), output_hashes={
            str(p.relative_to(ROOT)): sha(str(p.relative_to(ROOT)))
            for p in sorted((ROOT/OUT).glob('*.json')) if p.name != 'manifest.json'})
        print(json.dumps({k: v for k, v in report.items() if k not in ('folds', 'macro')}, indent=2))
        print(json.dumps(summary, indent=2))
    except Exception as error:
        manifest.update(state='failed', finished_at_utc=now(), error=repr(error))
        raise
    finally:
        (ROOT/OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    {'prepare': prepare, 'run': run}[parser.parse_args().action]()
