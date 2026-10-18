"""Archive frozen development-reference review; no model or lexical induction."""
from pathlib import Path
import json,sys,platform,time
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 bp=ROOT/'benchmarks/kamri_correspondence_review_v16.json';b=read(bp)
 for p,sha in b['input_hashes'].items():assert digest((ROOT/p).read_bytes())==sha,p
 review=read(ROOT/b['review']);assert review['stats']['units']==8 and len(review['passages'])==2 and not review['model_executed'] and not review['lexicons_used']
 out=ROOT/'runs/000016_kamri_correspondence_review';out.mkdir(exist_ok=False)
 code=sorted([*(ROOT/'src/fl_decipher').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')])
 m={'run_id':out.name,'experiment_id':b['experiment_id'],'stage':'development_correspondence_review','state':'running',
  'started_at_utc':utc(),'model_executed':False,'python':sys.version,'platform':platform.platform(),
  'input_hashes':b['input_hashes']|{str(bp.relative_to(ROOT)):digest(bp.read_bytes())},'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
 dump_json(out/'manifest.json',m);start=time.monotonic()
 try:
  assert b['frozen_at_utc']<=m['started_at_utc'] and review['reviewed_at_utc']<=b['frozen_at_utc']
  dump_json(out/'unit_ledger.json',{'units':review['units'],'denominator':8})
  dump_json(out/'passage_gates.json',{'passages':review['passages'],'denominator':2})
  dump_json(out/'proposed_annotation_errata.json',read(ROOT/'data/v16/proposed_annotation_errata.json'))
  dump_json(out/'report.json',{k:v for k,v in review.items() if k!='units'})
  md='# Experiment 16: bounded correspondence review\n\nEight fixed units, the first four from each of two previously exposed passages, are retained. This is a v15-informed development/reference review, not held-out evaluation.\n\nBoth current publisher HTML sources downloaded with HTTP 200. Both current FL requests failed with curl 35 TLS protocol-version alerts. The registered exact historical indexed FL excerpts preserve all eight selected statements; they remain historical evidence, not current raw captures. Four registered routes, four raw requests, no retry, substitute or bypass.\n\nAll eight proposed English units match unique, complete original source statements. Both four-statement sequences are ordered and nonoverlapping in source and historical FL views. Two passages pass the indexed-evidence development correspondence gate. Zero pass current raw-FL provenance, independent semantic training or untouched-test gates.\n\n| Unit | FL whitespace | Reading English whitespace | Original English whitespace | FL project tokens | Original English project tokens | Source match |\n|---|---:|---:|---:|---:|---:|---|\n'
  for r in review['units']:
   c=r['counts'];md+=f"| {r['uid']} | {c['fl_whitespace']} | {c['reading_english_whitespace']} | {c['original_english_whitespace']} | {c['fl_project_tokens']} | {c['original_english_project_tokens']} | {r['english_statement_matches'][0]['policy'] if r['english_statement_matches'] else 'missing'} |\n"
  s=review['stats'];md+=f"\nWhitespace equality holds for {s['equal_reading_whitespace_count_pairs']}/8 reading-edition pairs and {s['equal_original_whitespace_count_pairs']}/8 original-source pairs. The project's Unicode tokenizer splits hyphenated compounds and ignores standalone punctuation: all {s['equal_project_token_count_pairs']}/8 pairs have equal counts. This resolves the selected Nichiren count discrepancies under that tokenizer; it does not reproduce or validate the aggregate public 713/978 claim.\n\n{s['unvalidated_positional_hypotheses']} word-position pairings are serialized explicitly as unvalidated hypotheses, with offsets in independent FL/source documents. Equal counts and source identity do not establish those meanings or rule out local reordering. The fixed opposite-source diagnostics yield {s['wrong_source_exact_or_normalized_match_units']}/8 literal/normalized matches; this is not a measured classifier false-admission rate.\n\nThe errata propose S024 -> S015 and S036 -> S027, plus the same S015 correction in the title note. Original article bytes and translations are unchanged. Per-unit confidence remains unavailable.\n\nParagraph-aware source segmentation prevents an unpunctuated section heading from becoming part of the following statement. The full extracted body and paragraph text are both retained. Whole-body differences versus historical extractions are separately recorded and are not interpreted as edition changes without evidence.\n\nNo model executed, shared lexicons were not used, and no semantic labels or new test fold were admitted. Next, independent review must test the positional hypotheses against actual word-order/meaning evidence; raw FL provenance still needs a legitimate source or supplied capture.\n"
  (out/'report.md').write_text(md)
  m.update(state='completed',outcome='two_indexed_development_passages_reviewed_raw_fl_unavailable',finished_at_utc=utc(),elapsed_seconds=time.monotonic()-start,
   output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
  dump_json(out/'manifest.json',m);print(out)
 except Exception as e:
  m.update(state='failed',error=f'{type(e).__name__}: {e}');dump_json(out/'manifest.json',m);raise
if __name__=='__main__':main()
