"""Independent immutable byte/header reconstruction without E83 imports."""
import base64,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000083_digest_layers/'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/digest_layers_v83.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/digest_layers_v83.json':sha('experiments/digest_layers_v83.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000082_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 markers=['BEGIN WAYBACK TOOLBAR INSERT','END WAYBACK TOOLBAR INSERT','wombat.js','bundle-playback.js','web-static.archive.org','__wm.init','WB_wombat_Init']
 fields=['content-type','content-encoding','content-length','transfer-encoding','x-archive-orig-content-type','x-archive-orig-content-encoding','x-archive-orig-content-length','x-archive-orig-transfer-encoding','memento-datetime','x-archive-src']
 cases=[]
 assert [c['id'] for c in reg['cases']]==['E63','E82']
 for c in reg['cases']:
  base=ROOT/c['base'];body=(base/'body.bin').read_bytes();receipt=json.loads((base/'receipt.json').read_text())
  assert hashlib.sha256(body).hexdigest()==receipt['artifacts']['body.bin']['sha256']
  assert len(body)==receipt['artifacts']['body.bin']['bytes'] if c['id']=='E63' else len(body)>0
  command=receipt['command'] if c['id']=='E63' else json.loads((base/'intent.json').read_text())['command']
  a=json.loads((ROOT/c['index']).read_bytes());assert a[0]==['timestamp','original','statuscode','mimetype','digest'] and len(a)==2 and len(a[1])==5
  assert all(type(x) is str for x in a[1]);record=dict(zip(a[0],a[1]));assert re.fullmatch('[A-Z2-7]{32}',record['digest'])
  selected=read(c['selection']);assert record==(selected['record'] if c['id']=='E63' else selected['selection']['record'])
  blocks=[]
  for chunk in re.split(rb'\r?\n\r?\n',(base/'headers.txt').read_bytes()):
   lines=chunk.decode('iso-8859-1').splitlines()
   if not lines:continue
   found=re.match(r'^HTTP/\S+\s+(\d+)(?:\s+(.*))?$',lines[0])
   if not found:continue
   status=int(found[1]);reason=(found[2] or '').strip().casefold();values={f:[] for f in fields}
   for line in lines[1:]:
    if ':' not in line:continue
    k,v=line.split(':',1)
    if k.casefold() in values:values[k.casefold()].append(v.strip())
   blocks.append({'status':status,'ignored':status<200 or reason=='connection established','fields':values})
  apps=[b for b in blocks if not b['ignored']];final=apps[-1]['fields'] if apps else {f:[] for f in fields}
  telemetry=json.loads((base/c['telemetry']).read_bytes());size=telemetry.get('size_download')
  digest=hashlib.sha1(body).digest();expected=base64.b32decode(record['digest'])
  signatures={'gzip':body[:2]==bytes([31,139]),'utf8_bom':body[:3]==bytes([239,187,191]),
    'utf16_le_bom':body[:2]==bytes([255,254]),'utf16_be_bom':body[:2]==bytes([254,255])}
  positions={s:[m.start() for m in re.finditer(b'(?='+re.escape(s.encode())+b')',body)] for s in markers}
  cases.append({'id':c['id'],'receipt_integrity':True,'cdx_extraction_reproduced':True,'record':record,
   'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'body_sha1_base32':base64.b32encode(digest).decode(),
   'cdx_digest':record['digest'],'saved_body_matches_cdx':digest==expected,'header_blocks':blocks,'final_fields':final,
   'curl_compressed':command.count('--compressed')>0,'telemetry_size_download':size,
   'download_size_differs_from_saved':size is not None and size!=len(body),'prefix_signatures':signatures,'marker_positions':positions})
 report={'experiment_id':'digest_layers_v83','cases':cases,'e82_mismatch_reproduced':not cases[1]['saved_body_matches_cdx'],
 'cause_identified':False,'cause_status':'unresolved','encoded_wire_or_original_WARC_bytes_in_registered_inputs':False,
 'network_requests':0,'body_transformations':0,'candidate_selection':False,'new_predictions':False,'e82_gate_value':False,'semantic_benchmark_qualifying_works':0}
 assert report==read(OUT+'report.json')
 print(json.dumps({'verified':True,'captures':2,'markers_per_capture':7,'e82_mismatch_reproduced':report['e82_mismatch_reproduced'],
                   'cause_status':'unresolved','network_requests':0,'e82_gate_value':False},indent=2))
if __name__=='__main__':main()
