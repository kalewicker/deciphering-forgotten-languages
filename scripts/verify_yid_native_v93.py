"""Post-result read-only replay, independent of production comparator imports."""
import json,hashlib,re
from pathlib import Path
from bs4 import BeautifulSoup,NavigableString,Comment,Doctype,Tag
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def main():
 reg=read('experiments/yid_native_v93_execution.json');m=read('runs/000093_yid_native/manifest.json')
 assert m['state']=='complete' and reg['frozen_at_utc']<=m['started_at_utc']
 for mapping in [reg['input_hashes'],m['input_hashes'],m['output_hashes']]:
  for p,h in mapping.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 inv=read('data/v93/capture_inventory.json')
 for e in inv['entries']:
  raw=(ROOT/e['path']).read_bytes();assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
 result=read('runs/000093_yid_native/comparison.json');target=read('data/v93/targets.json');u=target['requested_url']
 raw=(ROOT/'data/v93/capture/page.html').read_bytes();assert len(raw)<=16*1024*1024
 soup=BeautifulSoup(raw.decode('utf-8'),'html.parser')
 ids=re.findall(r'<!--\s*saved from url=\(\d+\)([^\s<>]+)\s*-->',raw.decode('utf-8'))
 ids += [t.get('href','') for t in soup.find_all('link') if 'canonical' in t.get('rel',[])]
 ids += [t.get('content','') for t in soup.find_all('meta') if t.get('property')=='og:url']
 assert ids==result['identity_values'] and ids and all(x==u for x in ids)
 assert inv['reported_url']==read('data/v93/final_url_confirmation.json')['reported_final_url']==u
 bodies=[t for t in soup.find_all(True) if 'post-body' in t.get('class',[])];assert len(bodies)==1
 # Stack walk emits entry/exit events; no production extraction code is imported.
 stack=[(bodies[0],False)];pieces=[]
 blocks={'p','div','li','h1','h2','h3','h4','h5','h6','blockquote','pre'}
 while stack:
  node,leave=stack.pop()
  if isinstance(node,(Comment,Doctype)):continue
  if isinstance(node,NavigableString):pieces.append(str(node));continue
  if not isinstance(node,Tag) or node.name in {'script','style','noscript','template'}:continue
  if node.name=='br':pieces.append('\n');continue
  if node.name in blocks:pieces.append('\n')
  if not leave:
   stack.append((node,True));stack.extend((c,False) for c in reversed(list(node.children)))
 text=''.join(pieces);assert text==result['extracted_text']
 pos=0
 for chunk in result['extraction_chunks']:
  assert chunk['span']==[pos,pos+len(chunk['text'])] and text[slice(*chunk['span'])]==chunk['text'];pos=chunk['span'][1]
 assert pos==len(text)
 counts={}
 for mode in ['literal','whitespace']:
  view=text if mode=='literal' else ' '.join(text.split());cursor=0;matched=ordered=0
  if mode=='whitespace':assert view==result['normalized_text']
  assert len(result['comparison'][mode]['rows'])==len(target['targets'])==23
  for t,r in zip(target['targets'],result['comparison'][mode]['rows']):
   needle=t['text'] if mode=='literal' else ' '.join(t['text'].split())
   spans=[[m.start(),m.start()+len(needle)] for m in re.finditer('(?='+re.escape(needle)+')',view)]
   assert spans==r['occurrences'] and len(spans)==r['count']
   chosen=next((s for s in spans if s[0]>=cursor),None);assert chosen==r['ordered_span']
   matched+=bool(spans)
   if chosen:ordered+=1;cursor=chosen[1]
  counts[mode]={'denominator':23,'matched':matched,'ordered_matched':ordered}
  for k,v in counts[mode].items():assert result['comparison'][mode][k]==v
 assert read('runs/000093_yid_native/report.json')['counts']==counts
 print(json.dumps({'verified':True,'capture_files':len(inv['entries']),'literal_matches':counts['literal']['matched'],'ordered_matches':counts['literal']['ordered_matched'],'verifier_written_after_result':True,'shared_parser':'BeautifulSoup/html.parser'},indent=2))
if __name__=='__main__':main()
