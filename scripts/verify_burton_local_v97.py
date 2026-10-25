"""Read-only integrity and candidate-marker replay; no target-wording search."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/burton_local_v97.json');intake=read('runs/000097_burton_local/intake.json')
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 assert reg['registered_at_utc']<=intake['inspected_at_utc']
 assert intake['script_sha256']==sha('scripts/burton_local_v97.py')
 raw=(ROOT/'data/v97/pg57208.txt').read_bytes();text=raw.decode('utf-8');assert len(raw)==555341 and intake['strict_utf8']
 header=read('data/v97/header.json');assert header=={'span':[0,10000],'text':text[:10000]}
 found=[]
 for m in re.finditer(r'\[[^\]\r\n]*\]|\{[^}\r\n]*\}|(?m:^[ \t]*[0-9]+[ \t]*\r?$)',text):
  token=m[0]
  inside=token[1:-1] if token[0] in '[{' else token.strip()
  x=re.fullmatch(r'(?:(?:pg\.?|page|p\.?)\s*)?([0-9]+)',inside,re.I)
  if x:found.append((m.start(),m.end(),int(x[1]),token))
 saved=read('data/v97/markers.json')
 assert found==[(m['span'][0],m['span'][1],m['number'],m['literal']) for m in saved]
 assert len(found)==intake['marker_count']==443
 assert not any(252<=m[2]<=257 for m in found)
 assert read('data/v97/boundary_contexts.json')==[]
 report=read('runs/000097_burton_local/report.json');assert not report['page_binding_admitted'] and report['wording_counts'] is None and not report['comparison_executed']
 for e in read('data/v97/metadata_evidence.json'):assert text[slice(*e['span'])]==e['text'] and e['span'][1]<=10000
 print(json.dumps({'verified':True,'bytes':len(raw),'candidate_markers':443,'required_boundaries_found':0,'comparison_executed':False},indent=2))
if __name__=='__main__':main()
