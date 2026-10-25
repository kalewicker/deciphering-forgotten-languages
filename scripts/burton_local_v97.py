"""Single-use header/marker inventory; no target text loading or matching."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'(?im)(?:\[(?:(?:pg\.?|page|p\.?)\s*)?([0-9]+)\]|\{(?:(?:pg\.?|page|p\.?)\s*)?([0-9]+)\}|^[ \t]*([0-9]+)[ \t]*\r?$)')
def write(p,o):
 with (ROOT/p).open('x') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 reg=json.loads((ROOT/'experiments/burton_local_v97.json').read_text())
 for p,h in reg['input_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 out=ROOT/'runs/000097_burton_local';out.mkdir(exist_ok=False)
 raw=(ROOT/'data/v97/pg57208.txt').read_bytes();text=None;failure=None
 if len(raw)>8388608:failure='oversized'
 else:
  try:text=raw.decode('utf-8')
  except UnicodeDecodeError:failure='utf8_decode_failed'
 markers=[]
 if text is not None:
  for m in PATTERN.finditer(text):
   n=int(next(g for g in m.groups() if g is not None))
   markers.append({'number':n,'span':[m.start(),m.end()],'literal':m[0],'context_span':[max(0,m.start()-150),min(len(text),m.end()+150)] if n in reg['required_boundaries'] else None})
  write('data/v97/header.json',{'span':[0,min(10000,len(text))],'text':text[:10000]})
  write('data/v97/markers.json',markers)
  selected=[dict(m,context=text[slice(*m['context_span'])]) for m in markers if m['context_span']]
  write('data/v97/boundary_contexts.json',selected)
  print(text[:10000]);print(json.dumps({'marker_count':len(markers),'required_counts':{str(n):sum(m['number']==n for m in markers) for n in reg['required_boundaries']},'contexts':selected},ensure_ascii=False,indent=2))
 write('runs/000097_burton_local/intake.json',{'inspected_at_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'bytes':len(raw),'strict_utf8':text is not None,'failure':failure,'marker_count':len(markers),'required_counts':{str(n):sum(m['number']==n for m in markers) for n in reg['required_boundaries']},'wording_search_executed':False})
if __name__=='__main__':main()
