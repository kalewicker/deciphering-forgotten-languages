"""Freeze, independently verify fixed windows, then score once."""
import json,hashlib,argparse
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.burton_extract_v99 import windows,score
from replay_burton_extract_v99 import replay
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000099_burton_extract';REG='experiments/burton_extract_v99.json'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,o):
 with (ROOT/p).open('x') as f:json.dump(o,f,indent=2,ensure_ascii=False);f.write('\n')
def freeze():
 old=read('experiments/burton_extract_v99_development.json')['input_hashes']
 for p,h in old.items():assert sha(p)==h,p
 paths=set(old)|{'experiments/burton_extract_v99_development.json','experiments/burton_extract_v99_rules.md','src/fl_decipher/burton_extract_v99.py','scripts/burton_extract_v99.py','scripts/replay_burton_extract_v99.py','scripts/verify_burton_extract_v99.py','tests/test_burton_extract_v99.py'}|{str(p.relative_to(ROOT)) for p in (ROOT/'data/v99').glob('*') if p.is_file()}
 write(REG,{'frozen_at_utc':now(),'input_hashes':{p:sha(p) for p in sorted(paths)},'target_denominator':22})
 print('Extraction and scoring frozen.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False);m={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}};write(OUT+'/manifest.json',m)
 try:
  html=(ROOT/'data/v98/acquisition/body.bin').read_bytes().decode('utf-8');result=windows(html);independent=replay(html);assert result==independent
  write(OUT+'/extraction.json',result)
  write(OUT+'/window_verification.json',{'verified_at_utc':now(),'extraction_sha256':sha(OUT+'/extraction.json'),'full_text_and_offsets_agree':True,'window_lengths':[len(w) for w in result['windows']],'targets_loaded':False})
  target=read('data/v96/targets.json')['targets'];assert [t['package_ordinal'] for t in target]==list(range(2,24))
  comparisons=score(result['windows'],[t['text'] for t in target]);write(OUT+'/comparison.json',comparisons)
  report={'experiment_id':'burton_extract_v99','comparison_completed_at_utc':now(),'target_denominator':22,'page_windows':[[254,256],[252,253]],'window_lengths':[len(w) for w in result['windows']],
          'literal':{k:comparisons['literal'][k] for k in ['matched','ordered_matched']},'whitespace':{k:comparisons['whitespace'][k] for k in ['matched','ordered_matched']},
          'literal_missing_package_ordinals':[i+2 for i,r in enumerate(comparisons['literal']['rows']) if not r['occurrences']],
          'whitespace_missing_package_ordinals':[i+2 for i,r in enumerate(comparisons['whitespace']['rows']) if not r['occurrences']],
          'network_requests':0,'semantic_benchmark_qualifying_works':0,'new_confirmation_units':0}
  write(OUT+'/report.json',report);m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in (ROOT/OUT).glob('*.json') if p.name!='manifest.json'});print(json.dumps(report,indent=2))
 except Exception as e:m.update(state='failed',error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);{'freeze':freeze,'run':run}[p.parse_args().action]()
