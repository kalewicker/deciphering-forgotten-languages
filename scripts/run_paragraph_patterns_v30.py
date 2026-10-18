"""Run the frozen structural diagnostic once; failed criteria are preserved."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from fl_decipher.paragraph_patterns_v30 import evaluate

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def main():
    cfg=read('experiments/paragraph_patterns_v30.json');pre=read('data/v30/preflight.json');bench=read('benchmarks/paragraph_patterns_v30.json')
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for name,h in hashes.items():assert sha(name)==h,name
    out=ROOT/'runs/000030_paragraph_patterns';out.mkdir(exist_ok=False)
    manifest={'experiment_id':cfg['experiment_id'],'state':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),
              'input_hashes':bench['input_hashes']|{'benchmarks/paragraph_patterns_v30.json':sha('benchmarks/paragraph_patterns_v30.json')},'code_hashes':pre['code_hashes']}
    write(out/'manifest.json',manifest)
    try:
        frozen=read('data/v30/frozen.json')
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']
        result=evaluate(frozen);candidates=result['null_unit_order'];registry=frozen['registry']
        report={'experiment_id':cfg['experiment_id'],'structural_development_criterion_passed':result['gate']['passed'],
                'query_denominator':3,'source_work_denominator':2,'FL_registry_units':len(registry['fl_units']),
                'source_registry_units':len(registry['source_units']),'source_candidates':len(candidates),
                'natural_comparisons':3*len(candidates),'null_panels':len(result['nulls']),
                'null_comparisons':3*len(candidates)*len(result['nulls']),'null_unit_order':candidates,
                'unique_expected_units':sum(l['natural_decision']['nominated']==l['expected_unit_id'] for l in result['query_ledgers']),
                'source_absent_nominations':sum(l['source_work_absent_decision']['nominated'] is not None for l in result['query_ledgers']),
                'opaque_positive_qualifications':sum(l['opaque_positive_qualifies'] for l in result['query_ledgers']),
                'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'model_executed':False,'target_rescored':False,'new_network_requests':0,
                'scope':'Exposed paragraph-level substitution-pattern diagnostic; no semantic gold or source-identity acceptance'}
        for name in ['query_ledgers','controls','nulls','gate']:write(out/(name+'.json'),result[name])
        write(out/'report.json',report)
        (out/'report.md').write_text('# Experiment 30: paragraph repetition patterns\n\n'
             +f"Structural development criterion: {result['gate']['passed']}. Unique expected units: {report['unique_expected_units']}/3. Opaque positive qualifications: {report['opaque_positive_qualifications']}/3.\n\n"
             +'All natural/control scores, fingerprint witnesses, 199 complete shuffled-panel maxima and abstentions are retained. Semantic metrics and scientific acceptance remain null.\n')
        manifest.update(state='completed',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='structural_development_criterion_met' if result['gate']['passed'] else 'structural_development_criterion_not_met',
                        output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='manifest.json'})
        write(out/'manifest.json',manifest)
        print(json.dumps({'report':report,'gate':result['gate'],'queries':[{k:l[k] for k in ['query_id','eligible_query_fingerprint_types','natural_decision','source_work_absent_decision','search_max_null_tail']} for l in result['query_ledgers']]},indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');write(out/'manifest.json',manifest);raise


if __name__=='__main__':main()
