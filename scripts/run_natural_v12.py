"""One offline acquisition-gate result; deliberately contains no scorer call."""
from pathlib import Path
import platform
import sys
import time

from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v7 import read
from fl_decipher.natural_v12 import utc, validate_denominators

ROOT=Path(__file__).resolve().parents[1]


def main():
    bp=ROOT/'benchmarks/kamri_natural_v12.json';b=read(bp)
    for p,sha in b['input_hashes'].items():
        assert digest((ROOT/p).read_bytes())==sha,p
    ledger=read(ROOT/b['ledger']);validate_denominators(ledger)
    assert ledger['reference_eligible_queries']==0, 'Eligible packets require a separately frozen model execution; do not discard them.'
    out=ROOT/'runs/000012_kamri_natural_acquisition';out.mkdir(parents=True,exist_ok=False)
    code=sorted([*(ROOT/'src/fl_decipher').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')])
    manifest={'run_id':out.name,'experiment_id':'kamri_natural_v12','stage':'acquisition_eligibility','state':'running',
        'model_executed':False,'started_at_utc':utc(),'python':sys.version,'platform':platform.platform(),
        'selected_work_denominator':2,'selected_query_denominator':2,'reference_eligible_queries':0,
        'input_hashes':b['input_hashes']|{str(bp.relative_to(ROOT)):digest(bp.read_bytes())},
        'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json',manifest);start=time.monotonic()
    try:
        assert ledger['references_sealed_at_utc']<=manifest['started_at_utc']
        report={'experiment_id':'kamri_natural_v12','outcome':ledger['status'],'stage':'acquisition_eligibility',
                'model_executed':False,'new_supported_lexical_entries':0,'semantic_gold':False,
                'selected_works':2,'selected_queries':2,'selected_components':2,'reference_eligible_queries':0,
                'evaluated_queries':0,'metrics':None,'results':ledger['records'],
                'acquisition_ledger':b['ledger'],'evidence':'Two selected failures retained; not an accuracy result or successful transfer test'}
        dump_json(out/'report.json',report)
        lines=['# Experiment 12: natural acquisition/eligibility pilot','',
               'Completed acquisition outcome: two selected works, two indexed FL excerpts, zero reference-eligible pairs. No model executed; accuracy and rejection metrics unavailable.','',
               '| Work | FL words | FL parser atoms | Acquisition status | Reference eligible |',
               '|---|---:|---:|---|---|']
        for r in ledger['records']:
            lines.append(f'| {r["title"]} | {r["fl_whitespace_words"]} | {r["fl_atom_count"]} | {r["acquisition_status"]} | No |')
        lines+=['','No substitutions, meanings or models promoted. Indexed previews and failed raw attempts remain preserved.']
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed',outcome=ledger['status'],finished_at_utc=utc(),elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
        dump_json(out/'manifest.json',manifest)
    except Exception as exc:
        manifest.update(state='failed',error=f'{type(exc).__name__}: {exc}',elapsed_seconds=time.monotonic()-start)
        dump_json(out/'manifest.json',manifest);raise
    print(out)


if __name__=='__main__':
    main()
