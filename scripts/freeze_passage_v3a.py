"""Rebuild the audited preparation amendment from retained inputs; never overwrite a freeze.

This helper was saved after the final run. It is preparation tooling and was not
part of that run's code-hash set. Execution uses only the frozen artifacts.
"""
import json
from pathlib import Path
from fl_decipher.corpus import digest,dump_json
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]

def main():
 out=ROOT/'benchmarks/kamri_passage_v3a.json'
 if out.exists():raise ValueError('Final preparation already frozen; use a new experiment ID')
 benchmark=json.loads((ROOT/'benchmarks/kamri_passage_v3.json').read_text())
 cfg=json.loads((ROOT/'experiments/kamri_passage_v3.json').read_text())
 path=ROOT/'data/normalized/fl_models_magic_v3a.json'
 d=json.loads(path.read_text())
 benchmark['documents'].pop('fl_models_magic')
 benchmark['documents'][d['id']]={'path':str(path.relative_to(ROOT)),'sha256':digest(path.read_bytes()),'text_sha256':d['text_sha256'],'raw_sha256':d['snapshot']['sha256'],'source_group':'models_magic','sentence_count':7}
 record=next(r for r in benchmark['records'] if r['group']=='models_magic');record['fl_id']=d['id']
 f=sentences(d['text'])[6]
 en=json.loads((ROOT/'data/normalized/source_models_magic.json').read_text());s=sentences(en['text'])[63]
 record['edges'].append({'fl_index':6,'source_index':63,'fl_span':[f.start,f.end],'source_span':[s.start,s.end],'state':'single_analyst_structural_correspondence','semantic_gold':False})
 record['note']+=' Seventh opening sentence corresponds to the morphic-fields discussion; fits original word cap.'
 cfg.update(experiment_id='kamri_passage_v3a',preparation_amendment='experiments/kamri_passage_v3a_amendment.md')
 configpath=ROOT/'experiments/kamri_passage_v3a.json'
 if configpath.exists():raise ValueError('Final configuration already frozen')
 dump_json(configpath,cfg)
 inputs=[v['path'] for v in benchmark['documents'].values()]+['experiments/kamri_passage_v3a.json','experiments/kamri_passage_v3.md',cfg['preparation_amendment'],cfg['lexicon_path'],'benchmarks/inputs/passage_v3a_acquisition.json']
 benchmark['input_hashes']={p:digest((ROOT/p).read_bytes()) for p in inputs}
 benchmark['supersedes_preparation']='benchmarks/kamri_passage_v3.json'
 dump_json(out,benchmark)
 print(out)
if __name__=='__main__':main()
