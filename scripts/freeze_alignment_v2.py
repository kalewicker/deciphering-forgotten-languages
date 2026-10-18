"""Freeze audited structural edges and all inputs before model execution."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'benchmarks/kamri_alignment_v2.json'
 if out.exists():raise ValueError('Already frozen; create a new benchmark for changes')
 old=json.loads((ROOT/'benchmarks/kamri_excerpt_v1.json').read_text())
 docs={};records=[]
 for r in old['records']:
  for path in [r['fl_path'],r['source_path']]:docs[Path(path).stem]=path
  records.append({'group':r['group'],'split':'development','fl_id':Path(r['fl_path']).stem,
    'references':{Path(r['source_path']).stem:[{'fl_index':l['fl_index'],'source_index':l['source_index']} for l in r['links']]},'note':r['note']})
 for group in ['gad_johnson','western_esoterism','manichaean_hymn']:
  docs['source_'+group]=f'data/normalized/source_{group}.json'
 for group in ['western_esoterism','manichaean_hymn']:docs['fl_'+group]=f'data/normalized/fl_{group}.json'
 records[[r['group'] for r in records].index('gad_seer')]['references']['source_gad_johnson']=[{'fl_index':i,'source_index':i} for i in range(7)]
 for group,edges,note in [
  ('western_esoterism',[(0,11),(1,12),(2,13),(2,14),(3,15),(4,16),(5,17),(5,18),(6,19)],'Opening Comment passage, printed page 65; i.e. creates two source splits. FL paraphrases and omits terminology; structural links are provisional, no semantic gold.'),
  ('manichaean_hymn',[(0,0),(1,1),(2,2),(3,3),(4,3),(5,4)],'Verses 223–226. Source verse 225 joins two FL sentences. Editorial Wisdom parenthesis retained. No automatic positional lexical references.')]:
  records.append({'group':group,'split':'fresh','fl_id':'fl_'+group,'references':{'source_'+group:[{'fl_index':i,'source_index':j} for i,j in edges]},'note':note})
 frozen={}
 for doc_id,path in docs.items():
  p=ROOT/path;d=json.loads(p.read_text()); ss=sentences(d['text'],doc_id)
  frozen[doc_id]={'path':path,'sha256':digest(p.read_bytes()),'text_sha256':d['text_sha256'],'raw_sha256':d['snapshot']['sha256'],'source_group':d['source_group'],'sentence_count':len(ss)}
 for r in records:
  fl=json.loads((ROOT/frozen[r['fl_id']]['path']).read_text());fs=sentences(fl['text'],r['fl_id'])
  for source_id,edges in r['references'].items():
   en=json.loads((ROOT/frozen[source_id]['path']).read_text());es=sentences(en['text'],source_id)
   for edge in edges:
    f,e=fs[edge['fl_index']],es[edge['source_index']]
    edge.update(fl_span=[f.start,f.end],source_span=[e.start,e.end],state='single_analyst_structural_correspondence',semantic_gold=False)
 cfg=json.loads((ROOT/'experiments/kamri_excerpt_v1.json').read_text())
 dump_json(ROOT/'experiments/kamri_alignment_v2.json',{'experiment_id':'kamri_alignment_v2','registration':'experiments/kamri_alignment_v2.md','development_groups':[r['group'] for r in records if r['split']=='development'],'fresh_groups':['western_esoterism','manichaean_hymn'],'baseline':cfg['alignment'],'lexical_method':{'structural_weight':.6,'lexical_weight':.4,'match_floor':.72,'gap_penalty':.35,'minimum_links':3},'lexicon_rules':cfg['lexicon'],'lexicon_path':'runs/000001_kamri_excerpt_baseline/lexicon.json','seed':1731,'shuffle_repetitions':20})
 inputs=[*docs.values(),'experiments/kamri_alignment_v2.json','experiments/kamri_alignment_v2.md','runs/000001_kamri_excerpt_baseline/lexicon.json','benchmarks/inputs/alignment_v2_acquisition.json']
 dump_json(out,{'schema_version':2,'status':'frozen_before_model_execution','documents':frozen,'records':records,'input_hashes':{p:digest((ROOT/p).read_bytes()) for p in inputs},'annotation':'Single analyst, ordered structural spans; many-to-many edges retained in denominator. No independently validated semantic labels.'})
 print(out)
if __name__=='__main__':main()
