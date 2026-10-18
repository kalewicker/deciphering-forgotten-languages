"""Export fixed FL-only extension inputs and seal lookups before reference review."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.transfer_v18 import predict
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 cfg=read(ROOT/'experiments/kamri_transfer_v18.json')
 for p,sha in cfg['input_hashes'].items():assert digest((ROOT/p).read_bytes())==sha,p
 c=read(ROOT/cfg['candidates']);a=read(ROOT/'data/v15/parsed_annotations.json')['articles'];targets=[]
 for entry,g in [(3,'nichiren_images'),(13,'dark_side_light')]:
  article=a[entry-1]
  for u in article['units'][4:8]:targets.append({'uid':u['uid'],'component':g,'number':u['number'],'fl':u['fl'],
    'original_url':article['original_url'],'origin':'author-provided FL transcription; independent historical coverage checked only during reference review'})
 assert [t['uid'] for t in targets]==cfg['unit_uids']
 dump_json(ROOT/'data/v18/targets.json',{'selected_at_utc':utc(),'units':targets,'unit_denominator':8,'reading_english_exported':False})
 predictions=[predict(t,c) for t in targets]
 out=ROOT/'data/v18/frozen_predictions.json';assert not out.exists()
 dump_json(out,{'sealed_at_utc':utc(),'predictor':'frozen positional candidate lookup','model_executed':True,'translation_model_executed':False,
  'new_lexical_induction_executed':False,'unit_denominator':8,'token_denominator':sum(u['token_denominator'] for u in predictions),'units':predictions,
  'candidate_sha256':digest((ROOT/cfg['candidates']).read_bytes()),'target_sha256':digest((ROOT/'data/v18/targets.json').read_bytes()),'target_reference_english_used':False})
 dump_json(ROOT/'data/v18/prediction_seal.json',{'predictions_sha256':digest(out.read_bytes()),'candidate_sha256':digest((ROOT/cfg['candidates']).read_bytes()),
  'target_sha256':digest((ROOT/'data/v18/targets.json').read_bytes()),'sealed_at_utc':utc(),'unit_denominator':8,'semantic_gold':False})
 print('Sealed',len(predictions),'units and',sum(u['token_denominator'] for u in predictions),'target tokens before reference preparation')
if __name__=='__main__':main()
