"""Post-result independent extraction/metric replay; shared BeautifulSoup parser."""
import json,hashlib,re
from pathlib import Path
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Doctype
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def main():
 reg=read('experiments/yid_native_panel_v94_execution.json');m=read('runs/000094_yid_native_panel/manifest.json')
 assert m['state']=='complete' and reg['frozen_at_utc']<=m['started_at_utc']
 for mapping in [reg['input_hashes'],m['input_hashes'],m['output_hashes']]:
  for p,h in mapping.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 docs=read('data/v94/targets.json')['documents'];slots=read('data/v94/capture_inventory.json')['slots'];results=read('runs/000094_yid_native_panel/comparison.json');report=read('runs/000094_yid_native_panel/report.json');final=read('data/v94/final_url_confirmation.json')['final_urls']
 assert [d['number'] for d in docs]==[43,86] and [d['denominator'] for d in docs]==[36,242]
 files=0
 for d,s,out,row in zip(docs,slots,results,report['posts']):
  assert d['number']==s['number']==out['number']==row['number'];r=out['result'];u=d['requested_url']
  for e in s['entries']:
   raw=(ROOT/e['path']).read_bytes();assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'];files+=1
  raw=(ROOT/s['main_path']).read_bytes();assert len(raw)<=16*1024*1024;html=raw.decode('utf-8');soup=BeautifulSoup(html,'html.parser')
  ids=re.findall(r'<!--\s*saved from url=\(\d+\)([^\s<>]+)\s*-->',html)
  ids += [t.get('href','') for t in soup.find_all('link') if 'canonical' in t.get('rel',[])]+[t.get('content','') for t in soup.find_all('meta') if t.get('property')=='og:url']
  assert ids==r['identity_values'] and ids and all(x==u for x in ids)
  assert s['requested_url']==final[str(d['number'])]==u
  bodies=[t for t in soup.find_all(True) if 'post-body' in t.get('class',[])];assert len(bodies)==1
  stack=[(bodies[0],False)];pieces=[]
  while stack:
   node,leave=stack.pop()
   if isinstance(node,(Comment,Doctype)):continue
   if isinstance(node,NavigableString):pieces.append(str(node));continue
   if not isinstance(node,Tag) or node.name in {'script','style','noscript','template'}:continue
   if node.name=='br':pieces.append('\n');continue
   if node.name in {'p','div','li','h1','h2','h3','h4','h5','h6','blockquote','pre'}:pieces.append('\n')
   if not leave:stack.append((node,True));stack.extend((c,False) for c in reversed(list(node.children)))
  text=''.join(pieces);assert text==r['extracted_text'];pos=0
  for c in r['extraction_chunks']:
   assert c['span']==[pos,pos+len(c['text'])] and text[slice(*c['span'])]==c['text'];pos=c['span'][1]
  assert pos==len(text)
  for mode in ['literal','whitespace']:
   view=text if mode=='literal' else ' '.join(text.split());cursor=0;matched=ordered=0
   if mode=='whitespace':assert view==r['normalized_text']
   assert len(r['comparison'][mode]['rows'])==len(d['targets'])==d['denominator']
   for t,rr in zip(d['targets'],r['comparison'][mode]['rows']):
    needle=t['text'] if mode=='literal' else ' '.join(t['text'].split())
    spans=[[mm.start(),mm.start()+len(needle)] for mm in re.finditer('(?='+re.escape(needle)+')',view)]
    assert spans==rr['occurrences'] and len(spans)==rr['count'];chosen=next((x for x in spans if x[0]>=cursor),None);assert chosen==rr['ordered_span'];matched+=bool(spans)
    if chosen:ordered+=1;cursor=chosen[1]
   assert row['counts'][mode]=={'matched':matched,'ordered_matched':ordered}
   assert r['comparison'][mode]['matched']==matched and r['comparison'][mode]['ordered_matched']==ordered
  assert r['admissible'] and row['admissible'] and not r['reasons'] and not row['reasons']
 assert report['fixed_targets']==report['compared_targets']==278 and report['fixed_posts']==report['compared_posts']==2 and report['unavailable_targets']==0
 print(json.dumps({'verified':True,'posts':2,'targets':278,'preserved_files':files,'verifier_written_after_result':True,'shared_parser':'BeautifulSoup/html.parser'},indent=2))
if __name__=='__main__':main()
