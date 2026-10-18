"""One-shot neutral handoff; zero independent returns are fabricated."""
from datetime import datetime,timezone
from pathlib import Path
import json
from fl_decipher.review_handoff_v25 import build_packet, encoded, sha, template, validate_return

ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'experiments/kamri_review_handoff_v25.json').read_text())
    preflight=json.loads((ROOT/'data/v25/preflight.json').read_text())
    for field in ['input_hashes','code_hashes']:
        for p,h in preflight[field].items():
            assert sha((ROOT/p).read_bytes()) == h,p
    out=ROOT/'runs/000025_kamri_review_handoff';out.mkdir(exist_ok=False)
    manifest={'experiment_id':cfg['experiment_id'],'stage':'external_review_handoff','state':'running',
              'started_at_utc':datetime.now(timezone.utc).isoformat(),'model_executed':False,
              'input_hashes':preflight['input_hashes'],'code_hashes':preflight['code_hashes']}
    (out/'manifest.json').write_bytes(encoded(manifest))
    try:
        rows=[]
        for n in cfg['nominees']:
            record=build_packet(ROOT,ROOT/'data/v25/packets'/n['id'],n)
            packet=ROOT/record['packet'];material=json.loads((packet/'material_manifest.json').read_text())
            blank=json.loads((packet/'review_return_template.json').read_text())
            assert blank == template(n['id'],record['manifest_sha256'])
            validation=validate_return(blank,material,record['manifest_sha256'],
                {'fl':(packet/'fl_post.txt').read_text(),'source':(packet/'publisher_window.txt').read_text()})
            assert validation['structurally_valid'] is False and validation['ready_for_adjudication'] is False
            record['blank_template_validation']=validation;rows.append(record)
        report={'experiment_id':cfg['experiment_id'],'engineering_state':'handoff_ready',
                'review_state':'awaiting_independent_return','review_route':'external_reviewer',
                'packet_denominator':2,'packets_prepared':len(rows),'records':rows,
                'independent_reviews_returned':0,'independent_reviews_completed':0,
                'source_identity_admissions':0,'semantic_labels_admitted':0,'untouched_test_units_admitted':0,
                'evaluation_metrics':None,'external_messages_sent':0,'new_network_requests':0,
                'prior_predictions_included':False,'candidate_pairing_disclosed':True,'model_executed':False}
        (out/'report.json').write_bytes(encoded(report))
        (out/'report.md').write_text('# Step 25: external review handoff\n\n'
            +'Two self-contained packets are ready. Candidate source identities are disclosed; prior predictions are excluded. '
            +'Blank templates correctly fail return validation. Both packets await an external independent return. '
            +'Reviews, source/semantic admissions and untouched admissions remain zero; evaluation metrics are unavailable. '
            +'No external message, network request, model or PDF re-analysis occurred.\n')
        manifest.update(state='completed',outcome='handoff_ready_independent_return_pending',
                        finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        input_hashes=preflight['input_hashes']|{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (ROOT/'data/v25').rglob('*') if p.is_file()},
                        output_hashes={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        (out/'manifest.json').write_bytes(encoded(manifest))
        print(json.dumps({k:report[k] for k in ['engineering_state','review_state','packets_prepared','independent_reviews_returned']},indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');(out/'manifest.json').write_bytes(encoded(manifest));raise


if __name__ == '__main__':
    main()
