"""Source-continuation references, independent of target proposed English/predictions."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.correspondence_review_v16 import statements,whole_statement_matches
from fl_decipher.text import tokens
from fl_decipher.transfer_v18 import reference_gate
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 began=utc();cfg=read(ROOT/'experiments/kamri_transfer_v18.json');pred=read(ROOT/'data/v18/frozen_predictions.json');seal=read(ROOT/'data/v18/prediction_seal.json')
 assert pred['sealed_at_utc']<=seal['sealed_at_utc']<began and digest((ROOT/'data/v18/frozen_predictions.json').read_bytes())==seal['predictions_sha256']
 targets=read(ROOT/'data/v18/targets.json')['units'];training=read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units'];references=[];anchors=[]
 for g in cfg['components']:
  sd=read(ROOT/f'data/v16/normalized/{g}_source.json');fd=read(ROOT/f'data/v16/normalized/{g}_fl.json')
  anchor=next(u for u in training if u['component']==g and u['uid'].endswith(':004'))['english_statement_matches'][0]
  ss=statements(sd);ids=[i for i,s in enumerate(ss) if s['span']==anchor['span'] and s['text']==anchor['text']]
  assert len(ids)==1
  selected=[(i,s) for i,s in enumerate(ss) if i>ids[0] and s['terminal_punctuation']][:4]
  assert len(selected)==4
  anchors.append({'component':g,'training_anchor_uid':next(u['uid'] for u in training if u['component']==g and u['uid'].endswith(':004')),
    'source_anchor_span':anchor['span'],'source_anchor_text':anchor['text'],'source_statement_index':ids[0],
    'selected_statement_indices':[i for i,s in selected],'rule':'next four complete paragraph-local statements after fixed source anchor'})
  tt=[t for t in targets if t['component']==g];assert len(tt)==4
  previous_end=anchor['span'][1]
  for target,(i,s) in zip(tt,selected,strict=True):
   assert s['span'][0]>=previous_end;previous_end=s['span'][1]
   fm=whole_statement_matches(target['fl'],fd);ft=tokens(target['fl']);et=tokens(s['text'],s['span'][0])
   full_fl=len(fm)==1 and fm[0]['complete_statement'] and [t.normalized for t in tokens(fm[0]['text'])]==[t.normalized for t in ft]
   gate=reference_gate(source_authority=sd['source_authority_reviewed'],source_statement_complete=s['terminal_punctuation'],
    source_continuation_orderly=True,historical_fl_unique_complete=bool(full_fl),equal_token_counts=len(ft)==len(et))
   references.append({'uid':target['uid'],'component':g,'source_document':f'data/v16/normalized/{g}_source.json','fl_document':f'data/v16/normalized/{g}_fl.json',
    'source_statement_index':i,'source_block_id':s['block_id'],'source_statement':s['text'],'source_span':s['span'],
    'source_tokens':[{'index':j,'surface':t.surface,'form':t.normalized,'span':[t.start,t.end]} for j,t in enumerate(et)],
    'target_token_count':len(ft),'source_token_count':len(et),'historical_fl_statement_matches':fm,
    'fl_provenance':'historical indexed excerpt only','current_raw_fl':False,'gate':gate,'semantic_gold':False})
 result={'preparation_started_at_utc':began,'reviewed_at_utc':utc(),'prediction_seal_sha256':digest((ROOT/'data/v18/prediction_seal.json').read_bytes()),
  'unit_denominator':8,'anchors':anchors,'units':references,'reviewer':'single analyst source-continuation and correspondence qualification',
  'target_proposed_english_used':False,'semantic_gold':False,'assessment':'References recovered by source-only continuation order; historical coverage and equal-count gates fixed before scoring.'}
 path=ROOT/'data/v18/frozen_references.json';assert not path.exists();dump_json(path,result)
 dump_json(ROOT/'data/v18/reference_seal.json',{'sealed_at_utc':utc(),'references_sha256':digest(path.read_bytes()),'prediction_seal_sha256':digest((ROOT/'data/v18/prediction_seal.json').read_bytes())})
 inputs=[*(ROOT/'data/v18').glob('*.json'),ROOT/'experiments/kamri_transfer_v18.json']
 hashes=cfg['input_hashes']|{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in inputs}
 dump_json(ROOT/'benchmarks/kamri_transfer_v18.json',{'experiment_id':cfg['experiment_id'],'frozen_at_utc':utc(),'input_hashes':hashes,'unit_denominator':8,
  'token_denominator':pred['token_denominator'],'predictions':'data/v18/frozen_predictions.json','references':'data/v18/frozen_references.json'})
 print(json.dumps([{'uid':r['uid'],'fl_tokens':r['target_token_count'],'source_tokens':r['source_token_count'],'unmet':r['gate']['unmet']} for r in references],indent=2))
if __name__=='__main__':main()
