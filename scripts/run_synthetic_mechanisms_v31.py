"""Freeze oracle-free predictions before reading generator truth for assessment."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from fl_decipher.synthetic_mechanisms_v31 import predict,assess

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')


def main():
    cfg=read('experiments/synthetic_mechanisms_v31.json');pre=read('data/v31/preflight.json');bench=read('benchmarks/synthetic_mechanisms_v31.json')
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for name,h in hashes.items():assert sha(name)==h,name
    out=ROOT/'runs/000031_synthetic_mechanisms';out.mkdir(exist_ok=False)
    manifest={'experiment_id':cfg['experiment_id'],'state':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),
              'input_hashes':bench['input_hashes']|{'benchmarks/synthetic_mechanisms_v31.json':sha('benchmarks/synthetic_mechanisms_v31.json')},'code_hashes':pre['code_hashes']}
    write(out/'manifest.json',manifest)
    try:
        prep=read('data/v31/preparation_receipt.json')
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<prep['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']
        public=read('data/v31/public_cases.json');predictions=predict(public)
        write(out/'predictions.json',predictions)
        prediction_receipt={'predictions_frozen_at_utc':datetime.now(timezone.utc).isoformat(),'predictions_sha256':sha('runs/000031_synthetic_mechanisms/predictions.json'),
                            'oracle_used_for_predictions':False,'panels':len(predictions['panels']),'distinct_pairs':len(predictions['pair_scores'])}
        write(out/'prediction_receipt.json',prediction_receipt)
        # Oracle metadata is first loaded only after all predictor outputs are saved.
        oracle=read('data/v31/oracle.json');availability=read('data/v31/availability.json')
        assessment=assess(public,oracle,availability,predictions)
        write(out/'assessment.json',assessment)
        report={'experiment_id':cfg['experiment_id'],'engineering_calibration_passed':assessment['engineering_calibration']['passed'],
                'synthetic_candidate_admission_passed':assessment['admission_gate']['passed'],'parents':40,'queries':200,'panels':1000,
                'distinct_pair_scores':len(predictions['pair_scores']),'metrics':assessment['metrics'],'oracle_used_for_predictions':False,
                'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_targets_rescored':0,'new_network_requests':0,'model_executed':False,
                'scope':'Known synthetic lineage and fixed v30 features only; no natural-source or meaning admission'}
        write(out/'report.json',report)
        (out/'report.md').write_text('# Experiment 31: synthetic mechanism calibration\n\n'
          +f"Engineering calibration: {report['engineering_calibration_passed']}. Synthetic candidate admission: {report['synthetic_candidate_admission_passed']}. All 1,000 fixed panels retained.\n\n"
          +'Opaque prediction outputs precede oracle assessment. Full pair witnesses, lineage outcomes, paired-world equalities, mechanism metrics and failed gate components remain saved. No natural target is rescored.\n')
        manifest.update(state='completed',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='synthetic_calibration_complete_admission_gate_met' if report['synthetic_candidate_admission_passed'] else 'synthetic_calibration_complete_admission_gate_not_met',
                        output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='manifest.json'})
        write(out/'manifest.json',manifest)
        print(json.dumps({'report':report,'engineering':assessment['engineering_calibration'],'admission_gate':assessment['admission_gate']},indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');write(out/'manifest.json',manifest);raise


if __name__=='__main__':main()
