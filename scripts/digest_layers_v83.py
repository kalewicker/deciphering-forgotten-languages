"""Freeze/run a single offline comparison of two saved byte representations."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.digest_layers_v83 import cdx_record,describe
ROOT=Path(__file__).resolve().parents[1];REG='experiments/digest_layers_v83.json';OUT='runs/000083_digest_layers'
CODE=['experiments/digest_layers_v83.md','src/fl_decipher/digest_layers_v83.py','scripts/digest_layers_v83.py',
      'scripts/verify_digest_layers_v83.py','tests/test_digest_layers_v83.py']
CASES=[{'id':'E63','index':'data/v63/acquisition/metadata/body.bin','selection':'data/v63/archive_selection.json',
        'base':'data/v63/acquisition/replay','telemetry':'curl_stdout.bin'},
       {'id':'E82','index':'data/v82/acquisition/label_index/body.bin','selection':'data/v82/label_index.json',
        'base':'data/v82/acquisition/label_replay','telemetry':'stdout.bin'}]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def prepare():
 seal='reports/000082_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 paths=CODE+[seal]
 for c in CASES:
  paths += [c['index'],c['selection']]+[c['base']+'/'+n for n in ['body.bin','headers.txt','receipt.json',c['telemetry']]]
  if c['id']=='E82':paths.append(c['base']+'/intent.json')
 write(REG,{'experiment_id':'digest_layers_v83','registered_at_utc':now(),'cases':CASES,
 'input_hashes':{p:sha(p) for p in paths},'network_requests':0})
 print('Frozen offline two-capture diagnosis.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'digest_layers_v83','state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
 write(OUT+'/manifest.json',m)
 try:
  cases=[]
  for c in reg['cases']:
   base=c['base'];receipt=read(base+'/receipt.json');body=(ROOT/base/'body.bin').read_bytes()
   info=receipt['artifacts']['body.bin'];expected=info['sha256']
   assert hashlib.sha256(body).hexdigest()==expected
   command=receipt['command'] if c['id']=='E63' else read(base+'/intent.json')['command']
   record=cdx_record((ROOT/c['index']).read_bytes());saved=read(c['selection'])
   selected=saved['record'] if c['id']=='E63' else saved['selection']['record'];assert record==selected
   evidence=describe(body,(ROOT/base/'headers.txt').read_bytes(),command,read(base+'/'+c['telemetry']),record['digest'])
   cases.append({'id':c['id'],'receipt_integrity':True,'cdx_extraction_reproduced':True,'record':record,**evidence})
  report={'experiment_id':'digest_layers_v83','cases':cases,'e82_mismatch_reproduced':not cases[1]['saved_body_matches_cdx'],
 'cause_identified':False,'cause_status':'unresolved','encoded_wire_or_original_WARC_bytes_in_registered_inputs':False,
 'network_requests':0,'body_transformations':0,'candidate_selection':False,'new_predictions':False,
 'e82_gate_value':False,'semantic_benchmark_qualifying_works':0}
  write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={OUT+'/report.json':sha(OUT+'/report.json')})
  for c in cases:print(json.dumps({k:c[k] for k in ['id','body_bytes','saved_body_matches_cdx','curl_compressed','telemetry_size_download','prefix_signatures','marker_positions']}))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.action]()
