"""Run frozen-map prediction before test-origin assessment, preserving failures."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from fl_decipher.synthetic_transfer_v32 import predict,assess

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def payload_sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')


def main():
    cfg=read('experiments/synthetic_transfer_v32.json');pre=read('data/v32/preflight.json');bench=read('benchmarks/synthetic_transfer_v32.json')
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert sha(p)==h,p
    out=ROOT/'runs/000032_synthetic_transfer';out.mkdir(exist_ok=False)
    manifest={'experiment_id':cfg['experiment_id'],'state':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),
              'input_hashes':bench['input_hashes']|{'benchmarks/synthetic_transfer_v32.json':sha('benchmarks/synthetic_transfer_v32.json')},'code_hashes':pre['code_hashes']}
    write(out/'manifest.json',manifest)
    try:
        train=read('data/v32/training_receipt.json');frozen=read('data/v32/frozen_mapping.json');prep=read('data/v32/test_preparation_receipt.json')
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<train['prepared_at_utc']<frozen['learned_at_utc']<prep['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']
        public=read('data/v32/public_cases.json');model=frozen['model'];before=payload_sha(model)
        predictions=predict(public,model);after=payload_sha(model);assert before==after
        write(out/'predictions.json',predictions)
        prediction_receipt={'predictions_frozen_at_utc':datetime.now(timezone.utc).isoformat(),'predictions_sha256':sha('runs/000032_synthetic_transfer/predictions.json'),
            'oracle_used_for_predictions':False,'model_payload_sha256_before':before,'model_payload_sha256_after':after,
            'mapping_file_sha256':sha('data/v32/frozen_mapping.json'),'panels':len(predictions['panels']),'pair_alignments':len(predictions['pair_scores'])}
        write(out/'prediction_receipt.json',prediction_receipt)
        oracle=read('data/v32/oracle.json');availability=read('data/v32/availability.json')
        assessment=assess(public,oracle,availability,predictions);write(out/'assessment.json',assessment)
        complete=True
        for p in predictions['pair_scores'].values():
            n=len(public['views'][p['query_view_id']]['tokens']);m=len(public['views'][p['candidate_view_id']]['tokens'])
            complete=complete and [i for i,j in p['trace'] if i is not None]==list(range(n)) and [j for i,j in p['trace'] if j is not None]==list(range(m))
            complete=complete and p['edit_cost']==n+m-2*p['matched_tokens']
        engineering={'training_model_precedes_tests':True,'mapping_unchanged':before==after,'all_2100_panels_scored':len(predictions['panels'])==2100,
                     'all_2520_pair_paths_accounted':len(predictions['pair_scores'])==2520 and complete,
                     'all_84_equivalent_and_duplicate_controls':len(availability['equivalence_certificates'])==84 and all(c['anonymous_profile_equal'] and c['duplicate_bytes_equal'] for c in availability['equivalence_certificates'])}
        report={'experiment_id':cfg['experiment_id'],'engineering_integrity':engineering,'engineering_integrity_passed':all(engineering.values()),
                'synthetic_transfer_gate_passed':assessment['synthetic_transfer_gate']['passed'],'training_units':len(read('data/v32/training.json')['units']),
                'mapping_entries':len(model['entries']),'parents':84,'queries':420,'panels':2100,'pair_alignments':len(predictions['pair_scores']),
                'metrics':assessment['metrics'],'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_targets_rescored':0,'new_network_requests':0,'model_executed':False,
                'scope':'Supervised symbolic mapping transfer and indel alignment on fixed synthetic fixtures; no natural-language admission'}
        write(out/'report.json',report)
        (out/'report.md').write_text('# Experiment 32: frozen mapping transfer\n\n'
             +f"Engineering integrity: {report['engineering_integrity_passed']}. Synthetic transfer criterion: {report['synthetic_transfer_gate_passed']}. All 420 queries and 2,100 panels retained.\n\n"
             +'The mapping freezes before test generation. Predictions precede origin-oracle assessment. Exact operation-path ambiguity and positional-origin disagreement remain visible. Natural semantic acceptance is null.\n')
        manifest.update(state='completed',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='synthetic_transfer_criterion_met' if report['synthetic_transfer_gate_passed'] else 'synthetic_transfer_criterion_not_met',
                        output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='manifest.json'})
        write(out/'manifest.json',manifest)
        print(json.dumps({'engineering':engineering,'gate':assessment['synthetic_transfer_gate'],'seen_mechanisms':assessment['metrics']['by_group_mechanism']['seen'],
                          'scenarios':assessment['metrics']['by_scenario'],'qualified_alignment_positions':[assessment['metrics']['qualified_parent_exact_origin_matches'],assessment['metrics']['qualified_parent_returned_matches']]},indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');write(out/'manifest.json',manifest);raise


if __name__=='__main__':main()
