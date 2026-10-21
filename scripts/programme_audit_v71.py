"""Read-only E1–E70 preservation and registered claim audit; requires local archive."""
import argparse
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = 'experiments/programme_audit_v71.json'


def read(path):
    return json.loads((ROOT / path).read_text())


def audit():
    cfg = read(REGISTRATION)
    checks = []

    @lru_cache(maxsize=None)
    def digest(path):
        h = sha256()
        with (ROOT / path).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def check(label, operation):
        try:
            passed = bool(operation())
            error = None
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            passed, error = False, str(exc)
        checks.append({'check': label, 'passed': passed, 'error': error})

    for path, expected in cfg['input_hashes'].items():
        check('frozen:' + path, lambda p=path, e=expected: digest(p) == e)
    # The registration fixes the inventory; later runs do not change this audit.
    check('manifest_denominator_70', lambda: len(cfg['manifests']) == 70)
    check('run_ids_1_through_70', lambda: sorted(
        int(Path(p).parent.name[:6]) for p in cfg['manifests']) == list(range(1, 71)))
    check('seal_denominator_56', lambda: len(cfg['seals']) == 56)
    check('seal_ids_15_through_70', lambda: sorted(
        int(Path(p).name[:6]) for p in cfg['seals']) == list(range(15, 71)))
    for path in cfg['manifests']:
        try:
            manifest = read(path)
        except (OSError, ValueError) as exc:
            checks.append({'check': path, 'passed': False, 'error': str(exc)})
            continue
        check(path + ':completed', lambda m=manifest: m['state'] == 'completed')
        for field in ('input_hashes', 'code_hashes', 'output_hashes', 'artifact_hashes'):
            for name, expected in manifest.get(field, {}).items():
                if field == 'input_hashes' and Path(path).parent.name.startswith('000001'):
                    check(path + ':' + field + ':' + name,
                          lambda n=name, e=expected: sha256(read(
                              'data/normalized/' + n + '.json')['text'].encode()).hexdigest() == e)
                else:
                    target = str(Path(path).parent / name) if field in (
                        'output_hashes', 'artifact_hashes') else name
                    check(path + ':' + field + ':' + name,
                          lambda p=target, e=expected: digest(p) == e)
    for path in cfg['seals']:
        try:
            seal = read(path)
        except (OSError, ValueError) as exc:
            checks.append({'check': path, 'passed': False, 'error': str(exc)})
            continue
        for name, expected in seal['deliverable_hashes'].items():
            check(path + ':' + name, lambda p=name, e=expected: digest(p) == e)
    for claim in cfg['claims']:
        def matches(c=claim):
            value = read(c['path'])
            for part in c['pointer'].split('/')[1:]:
                key = part.replace('~1', '/').replace('~0', '~')
                value = value[int(key)] if isinstance(value, list) else value[key]
            return type(value) is type(c['expected']) and value == c['expected']
        check('claim:' + claim['id'], matches)
    return {
        'experiment_id': 'programme_audit_v71',
        'registration_sha256': digest(REGISTRATION),
        'historical_manifests': len(cfg['manifests']),
        'historical_seals': len(cfg['seals']),
        'registered_claims': len(cfg['claims']),
        'checks_evaluated': len(checks),
        'checks_failed': sum(not c['passed'] for c in checks),
        'integrity_passed': all(c['passed'] for c in checks),
        'network_requests': 0,
        'historical_algorithms_rerun': False,
        'independent_scientific_review': False,
        'natural_benchmark_capacity_met': False,
        'semantic_admissions': 0,
        'checks': checks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = audit()
    if args.verify:
        if json.loads(args.output.read_text()) != result:
            raise SystemExit('Saved audit does not match current reconstruction')
    else:
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
    if not result['integrity_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
