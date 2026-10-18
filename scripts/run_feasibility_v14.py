"""Immutable one-work feasibility outcome; no predictions or scorer execution."""
from pathlib import Path
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v7 import read
from fl_decipher.natural_v12 import utc

ROOT = Path(__file__).resolve().parents[1]


def main():
    bp = ROOT/'benchmarks/kamri_feasibility_v14.json'; b = read(bp)
    for p, sha in b['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    ledger = read(ROOT/b['ledger'])
    assert ledger['selected_queries'] == 1 and len(ledger['records']) == 1
    assert ledger['reference_eligible_queries'] == ledger['evaluated_queries'] == 0
    assert ledger['metrics'] is None and not ledger['model_executed']
    assert ledger['records'][0]['references'] is None
    out = ROOT/'runs/000014_kamri_source_feasibility'; out.mkdir(parents=True, exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    manifest = {'run_id':out.name, 'experiment_id':ledger['experiment_id'], 'stage':ledger['stage'],
        'state':'running', 'model_executed':False, 'started_at_utc':utc(), 'python':sys.version,
        'platform':platform.platform(), 'selected_query_denominator':1,
        'input_hashes':b['input_hashes'] | {str(bp.relative_to(ROOT)):digest(bp.read_bytes())},
        'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest); start = time.monotonic()
    try:
        assert ledger['references_sealed_at_utc'] <= manifest['started_at_utc']
        report = ledger | {'acquisition_ledger':b['ledger'],
            'evidence':'Source-first acquisition succeeds for one opening preview, but concrete correspondence remains unresolved; no natural scoring result.'}
        dump_json(out/'report.json', report)
        (out/'report.md').write_text('# Experiment 14: remaining Kamri source-component feasibility\n\n'
            'One selected source work/component and query. A publisher-hosted 2013 opening preview (380 words) and indexed FL opening (174 words) are preserved. Zero eligible reference pairs; no model executed. Accuracy and false-admission rates unavailable.\n\n'
            'Religious Architecture remains a provisional lead. Every equal-index parser-atom token count differs; this does not prove the work is unrelated to the post. No correspondence labels were invented from topic similarity.\n\n'
            'Conservative co-occurrence audit: 24 inventory posts, 22 source-work nodes, 14 components; 13 already exposed before this stage. The last previously unexposed component is now an unresolved feasibility observation. The current inventory provides no further untouched component.\n\n'
            'Three source searches, three raw source requests, one raw metadata request, and a failed XML link conservatively charged against the fourth source route. One target FL index search and one failed page open. No restricted-route bypass, replacements or promoted meanings.\n')
        manifest.update(state='completed', outcome=ledger['status'], finished_at_utc=utc(),
            elapsed_seconds=time.monotonic()-start,
            output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
    except Exception as exc:
        manifest.update(state='failed', error=f'{type(exc).__name__}: {exc}')
        dump_json(out/'manifest.json', manifest); raise
    print(out)


if __name__ == '__main__':
    main()
