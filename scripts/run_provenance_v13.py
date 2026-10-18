"""Persist the registered zero-eligible outcome; no scorer imports or calls."""
from pathlib import Path
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v7 import read
from fl_decipher.natural_v12 import utc
from fl_decipher.provenance_v13 import validate_result

ROOT = Path(__file__).resolve().parents[1]


def main():
    bp = ROOT/'benchmarks/kamri_provenance_v13.json'; b = read(bp)
    for p, sha in b['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    ledger = read(ROOT/b['ledger'])
    validate_result(ledger, read(ROOT/'benchmarks/inputs/natural_v12_acquisition.json'))
    assert ledger['reference_eligible_queries'] == 0, 'An eligible panel requires a separately frozen model execution'
    out = ROOT/'runs/000013_kamri_source_provenance'; out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    manifest = {'run_id':out.name, 'experiment_id':ledger['experiment_id'], 'stage':ledger['stage'],
        'state':'running', 'model_executed':False, 'started_at_utc':utc(),
        'python':sys.version, 'platform':platform.platform(), 'selected_query_denominator':2,
        'input_hashes':b['input_hashes'] | {str(bp.relative_to(ROOT)):digest(bp.read_bytes())},
        'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest); started = time.monotonic()
    try:
        assert ledger['references_sealed_at_utc'] <= manifest['started_at_utc']
        report = {k:ledger[k] for k in ('experiment_id', 'stage', 'status', 'selected_works',
            'selected_queries', 'selected_components', 'reference_eligible_queries', 'evaluated_queries',
            'model_executed', 'metrics', 'new_supported_lexical_entries', 'inspectable_publisher_work_excerpts',
            'eligible_scoped_source_packets', 'records', 'raw_requests', 'distinct_source_routes', 'discovery_queries')}
        report.update(semantic_gold=False, acquisition_ledger=b['ledger'],
            evidence='One verified publisher work excerpt does not match the frozen passage; neither selected query is reference eligible.')
        dump_json(out/'report.json', report)
        (out/'report.md').write_text('# Experiment 13: source-provenance continuation\n\n'
            'Two selected works retained; one inspectable archived publisher excerpt; zero eligible scoped pairs. No model executed; accuracy and rejection metrics unavailable.\n\n'
            '| Work | New evidence | Passage eligible |\n|---|---|---|\n'
            '| Liber Azazel | Primary author lead does not establish authorship; linked endpoints fail DNS | No |\n'
            '| Book of Vile Darkness | Archived Monte Cook / 2002 publisher excerpt covers Juiblex, not chapter one | No |\n\n'
            'Eight discovery queries, eight distinct source/provenance routes, nine raw requests including one disclosed external DNS diagnostic. The two v12 FL openings and all prior outcomes are retained. No meanings or models promoted.\n')
        manifest.update(state='completed', outcome=ledger['status'], finished_at_utc=utc(),
            elapsed_seconds=time.monotonic()-started,
            output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}')
        dump_json(out/'manifest.json', manifest); raise
    print(out)


if __name__ == '__main__':
    main()
