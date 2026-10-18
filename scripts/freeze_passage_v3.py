"""Freeze source spans and matched-threshold variants before scoring."""
import itertools,json
from pathlib import Path
from fl_decipher.corpus import digest,dump_json
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'benchmarks/kamri_passage_v3.json'
 if out.exists():raise ValueError('Benchmark already frozen; use a new experiment ID')
 old=json.loads((ROOT/'benchmarks/kamri_alignment_v2.json').read_text())
 docs={k:dict(v) for k,v in old['documents'].items() if k!='source_gad_seer'}
 records=[]
 for r in old['records']:
  source='source_gad_johnson' if r['group']=='gad_seer' else next(iter(r['references']))
  records.append({'group':r['group'],'split':'development','fl_id':r['fl_id'],'source_id':source,'edges':r['references'][source],'note':r['note']})
 for group in ['risk_math','models_magic']:
  for kind in ['fl','source']:
   key=kind+'_'+group;p=ROOT/'data/normalized'/f'{key}.json';d=json.loads(p.read_text())
   docs[key]={'path':str(p.relative_to(ROOT)),'sha256':digest(p.read_bytes()),'text_sha256':d['text_sha256'],'raw_sha256':d['snapshot']['sha256'],'source_group':group,'sentence_count':len(sentences(d['text']))}
 for group,edges,note in [
  ('risk_math',[(0,12),(1,13),(2,14),(3,15)],'Section 2 opening on PDF page 2. Four ordered structural correspondences; final compound-token count differs. Citation stripping declared; no independently checked semantic meanings.'),
  ('models_magic',[(0,55),(1,56),(1,57),(2,58),(3,59),(4,60),(5,61),(5,62)],'Information Model subsection. Opening modifies topic/date wording; FL sentence 1 combines source premises, and source e.g. splits the final FL sentence. Alternate register retained. Provisional structural audit, no semantic gold.')]:
  fl_id='fl_'+group;source_id='source_'+group
  fs=sentences(json.loads((ROOT/docs[fl_id]['path']).read_text())['text']);ss=sentences(json.loads((ROOT/docs[source_id]['path']).read_text())['text'])
  labels=[]
  for i,j in edges:
   f,s=fs[i],ss[j];labels.append({'fl_index':i,'source_index':j,'fl_span':[f.start,f.end],'source_span':[s.start,s.end],'state':'single_analyst_structural_correspondence','semantic_gold':False})
  records.append({'group':group,'split':'fresh','fl_id':fl_id,'source_id':source_id,'edges':labels,'note':note})
 variants=[{'id':f'{boundary}_{spans}_{scoring}','boundary':boundary,'max_block':1 if spans=='one' else 2,'scoring':scoring} for boundary,spans,scoring in itertools.product(['legacy','protected'],['one','multi'],['structural','lexical'])]
 v1=json.loads((ROOT/'experiments/kamri_excerpt_v1.json').read_text())
 cfg={'experiment_id':'kamri_passage_v3','registration':'experiments/kamri_passage_v3.md','development_groups':[r['group'] for r in records if r['split']=='development'],'fresh_groups':['risk_math','models_magic'],'candidate_ids':[k for k in docs if k.startswith('source_')],'variants':variants,'weights':v1['alignment']['weights'],'match_floor':.72,'gap_penalty':.35,'merge_penalty':.04,'minimum_fl_atoms':3,'structural_weight':.6,'lexical_weight':.4,'lexicon_path':'runs/000001_kamri_excerpt_baseline/lexicon.json','lexicon_rules':v1['lexicon'],'abbreviations':['i.e.','e.g.','Mr.','Mrs.','Ms.','Dr.','Prof.','vs.','etc.'],'seed':2731,'shuffle_repetitions':20}
 configpath=ROOT/'experiments/kamri_passage_v3.json';dump_json(configpath,cfg)
 inputs=[v['path'] for v in docs.values()]+['experiments/kamri_passage_v3.json','experiments/kamri_passage_v3.md',cfg['lexicon_path'],'benchmarks/inputs/passage_v3_acquisition.json']
 dump_json(out,{'schema_version':3,'status':'frozen_before_model_execution','documents':docs,'records':records,'selected_fresh_denominator':2,'input_hashes':{p:digest((ROOT/p).read_bytes()) for p in inputs},'annotation':'Single-analyst structural atomic edges; many-to-many Cartesian inferred edges are all scored, including extras. Semantic_gold=False throughout.'})
 print(out)
if __name__=='__main__':main()
