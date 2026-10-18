"""Run immutable complete-denominator textual and metadata audit, without a model."""
from collections import Counter
from pathlib import Path
import json,platform,sys,time
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.dataset_audit_v15 import locate,prepare_views,words,parse_article
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 bp=ROOT/'benchmarks/kamri_dataset_audit_v15.json'; b=read(bp)
 for p,sha in b['input_hashes'].items():assert digest((ROOT/p).read_bytes())==sha,p
 out=ROOT/'runs/000015_kamri_dataset_audit';out.mkdir(exist_ok=False)
 code=sorted([*(ROOT/'src/fl_decipher').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')])
 m={'run_id':out.name,'experiment_id':b['experiment_id'],'stage':b['stage'],'state':'running','started_at_utc':utc(),
 'model_executed':False,'python':sys.version,'platform':platform.platform(),
 'input_hashes':b['input_hashes']|{str(bp.relative_to(ROOT)):digest(bp.read_bytes())},
 'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
 dump_json(out/'manifest.json',m);start=time.monotonic()
 try:
  articles=read(ROOT/'data/v15/parsed_annotations.json')['articles'];inv=read(ROOT/'data/v14/inventory_components.json');components=read(ROOT/'data/v14/component_audit.json')['components']
  posts={p['entry']:p['works'] for p in inv['posts']}; posts[25]=posts[22]
  docs={key:read(ROOT/v['path']) for key,v in b['documents'].items()};aliases=inv['prior_component_aliases'];views=prepare_views(docs)
  rows=[]; summaries=[]
  for a in articles:
   assert [u['number'] for u in a['units']]==list(range(1,len(a['units'])+1))
   assert len(a['units'])==a['claimed_unit_count']
   comp=next(c for c in components if set(posts[a['entry']]).intersection(c)); current=[]
   for u in a['units']:
    assert u['fl'] and u['english']
    hits={}
    for side in ('fl','english'):
     candidates=locate(u[side],{k:d for k,d in docs.items() if d['kind']==('fl' if side=='fl' else 'source')},views)
     for hit in candidates:
      d=docs[hit['document_id']];group=d['source_group']; expanded=set(aliases.get(group,[group]))
      hit['expected_component']=bool(expanded.intersection(comp))
      hit['expected_article']=d['url']==a['original_url'] if side=='fl' else None
      hit['scope_accepted']=hit['expected_component'] and (side=='english' or hit['expected_article'])
      hit['provenance']=b['documents'][hit['document_id']]['provenance']
      hit['authoritative_source']=b['documents'][hit['document_id']]['authoritative_source']
     hits[side]=candidates
    f=[h for h in hits['fl'] if h['scope_accepted']];e=[h for h in hits['english'] if h['scope_accepted']]
    trusted=[h for h in e if h['authoritative_source']]
    r={'uid':u['uid'],'article':a['entry'],'number':u['number'],'component':comp,'language':u['language'],
     'fl_words':u['fl_words'],'english_words':u['english_words'],'equal_whitespace_counts':u['fl_words']==u['english_words'],
     'english_matches':hits['english'],'fl_matches':hits['fl'],
     'english_corroborated':bool(e),'fl_corroborated':bool(f),'both_corroborated':bool(f and e),
     'authoritative_english_corroborated':bool(trusted),'both_with_authoritative_english':bool(f and trusted),
     'short_text_requires_special_review':len(words(u['english']))<8 or len(words(u['fl']))<8,
     'occurrence_ambiguity':any(h['occurrence_count']>1 for h in e+f),
     'confidence':'unmapped aggregate only' if a['entry']==7 else 'author complete-alignment claim; no per-unit calibrated confidence',
     'status':'both textual views corroborated; correspondence review pending' if f and e else 'English only corroborated' if e else 'FL only corroborated' if f else 'no scoped independent full-unit match',
     'semantic_gold':False,'semantic_training_eligible':False,'untouched_test_eligible':False}
    rows.append(r); current.append(r)
   summaries.append({'entry':a['entry'],'title':a['title'],'language':a['language'],'units':len(current),'component':comp,
    **{k:sum(r[k] for r in current) for k in ['english_corroborated','fl_corroborated','both_corroborated','both_with_authoritative_english','equal_whitespace_counts']},
    'full_article_both_texts_corroborated':all(r['both_corroborated'] for r in current),
    'source_basis':a['source_basis'],'original_url':a['original_url'],'source_alignment_claim':a['claimed_verification']})
  combined=(ROOT/'data/v15/quarantine/ALL-TRANSLATIONS.txt').read_text(encoding='utf-8-sig')
  combined_exact={a['file']:combined.count((ROOT/'data/v15/quarantine'/a['file']).read_text(encoding='utf-8-sig').strip()) for a in articles}
  assert all(n==1 for n in combined_exact.values())
  lexcounts={name:sum(' — ' in line and line.strip() not in ('Kamri — English','Kamri Western — English') for line in (ROOT/'data/v15/quarantine'/name).read_text().splitlines()) for name in ['KAMRI-LEXICON.txt','KAMRI-WESTERN-VERIFIED-LEXICON.txt']}
  proper=[u for a in articles if a['language']=='Kamri' for u in a['units']]
  western=articles[24]['units'];paired=articles[21]['units'];assert len(western)==len(paired)==48
  western_comparison=[{'western_uid':w['uid'],'kamri_uid':k['uid'],'same_whitespace_english':' '.join(w['english'].split())==' '.join(k['english'].split()),'same_ordered_english_words':words(w['english'])==words(k['english'])} for w,k in zip(western,paired,strict=True)]
  duplicates={'fl':[{'sha256':s,'uids':ids} for s,ids in duplicate_groups(articles,'fl').items() if len(ids)>1],
              'english':[{'sha256':s,'uids':ids} for s,ids in duplicate_groups(articles,'english').items() if len(ids)>1]}
  stats={'article_editions':len(articles),'kamri_articles':24,'kamri_units':len(proper),'western_units':len(western),'all_units':len(rows),
   'kamri_fl_whitespace_words':sum(u['fl_words'] for u in proper),'kamri_english_whitespace_words':sum(u['english_words'] for u in proper),
   'kamri_equal_whitespace_count_units':sum(u['fl_words']==u['english_words'] for u in proper),
   **{k:sum(r[k] for r in rows) for k in ['english_corroborated','fl_corroborated','both_corroborated','authoritative_english_corroborated','both_with_authoritative_english','occurrence_ambiguity','short_text_requires_special_review']},
   'fully_corroborated_articles':sum(a['full_article_both_texts_corroborated'] for a in summaries),'semantic_training_eligible':0,'untouched_test_eligible':0}
  findings=[{'id':'count_claim_not_reproduced','public_claim':{'fl_tokens':22599,'english_tokens':22769,'same_count_units':713},'method':'whitespace splitting after reading-edition locator exclusion','conclusion':'Package does not reproduce published figures with this method; original tokenizer/edition may differ. Not proof of false underlying analysis.'},
   {'id':'stale_uncertainty_locators','article':7,'references':[{'label':'S024','matching_reading_edition_unit':15,'forms':['daċkęį','kirglar','saċvęį']},{'label':'S036','matching_reading_edition_unit':27,'english':'I know priests who control several temples as though the temples were their private property.'}], 'confidence_counts':{'high':20,'medium':14,'low':2},'per_unit_confidence_mapping':None},
   {'id':'western_english_editions_differ','same_whitespace_english':sum(x['same_whitespace_english'] for x in western_comparison),'same_ordered_english_words':sum(x['same_ordered_english_words'] for x in western_comparison),'denominator':48,'conclusion':'Reading editions differ; do not use as identical positional English labels. Does not refute claimed common underlying passage.'},
   {'id':'source_gold_incomplete','conclusion':'Package contains annotations and lexicons, no original English source copies or full original FL captures. Per-unit occurrence/edition provenance is incomplete. Textual corroboration is not independent semantic gold.'},
   {'id':'component_refinement','new_cited_work_nodes':['lazer_2018','pennycook_rand_2018','nyhan_reifler_2015'],'attach_to_existing_component':next(c for c in components if 'models_magic' in c),'proposed_nodes':25,'proposed_components':14,'status':'bibliographic nominations only; v14 topology unchanged'}]
  report={'experiment_id':b['experiment_id'],'stage':b['stage'],'model_executed':False,'stats':stats,'articles':summaries,'findings':findings,
   'lexicon_entry_counts':lexcounts,'lexicons_used_for_induction':False,'combined_exact_article_occurrences':combined_exact,
   'duplicate_units':duplicates,'source_routes':read(ROOT/'data/v15/evidence_registry.json')['source_routes'],
   'limits':['Existing FL snapshots are indexed excerpts, not complete raw posts.','Full-unit English match absence can reflect limited source coverage, paraphrase, edition changes or extraction; it is not a disproved source attribution.','Whole-unit sequence matches and equal word counts do not validate wordwise meaning.','Eight-word flag is a descriptive short-text warning, not a preregistered scoring/admission threshold.','Single-analyst audit; semantic correspondence is not independently reviewed.']}
  dump_json(out/'unit_ledger.json',{'denominator':len(rows),'rows':rows});dump_json(out/'western_comparison.json',western_comparison)
  dump_json(out/'split_readiness.json',{'components':components,'all_components_previously_exposed':True,'article_component_assignments':{str(a['entry']):a['component'] for a in summaries},'semantic_training_eligible_uids':[],'untouched_test_eligible_uids':[],'both_textual_views_review_leads':[r['uid'] for r in rows if r['both_corroborated']],'status':'No complete independently reviewed semantic split admitted; keep all annotations quarantined.'})
  dump_json(out/'report.json',report)
  md='# Experiment 15: public alignment-package audit\n\n'+f"All {stats['all_units']} units accounted for: 978 Kamri across 24 posts, plus 48 Western units. The combined file duplicates each reading edition exactly once. The 459/296-entry lexicons remain quarantined.\n\n"+f"Independent saved evidence corroborates {stats['english_corroborated']} English units, {stats['fl_corroborated']} FL units, and both views for {stats['both_corroborated']} units. Of those, {stats['both_with_authoritative_english']} have a source hosted by its publisher, author repository or institution and reviewed extraction. Zero entire articles have both views fully corroborated. These counts include short or ambiguous strings; see every occurrence and qualification in unit_ledger.json. They are textual review leads, not validated translations.\n\n"+'| Entry | Article | Units | English | FL | Both | Both with authoritative English |\n|---|---|---:|---:|---:|---:|---:|\n'
  for a in summaries:md+=f"| {a['entry']} | {a['title']} | {a['units']} | {a['english_corroborated']} | {a['fl_corroborated']} | {a['both_corroborated']} | {a['both_with_authoritative_english']} |\n"
  md+='\nThe reading editions yield 22,600 Kamri whitespace words and 22,614 English words, with 654/978 equal-count units. The public 22,599/22,769 and 713/978 figures are not reproduced under that method; edition/tokenizer differences remain unresolved. Article 7’s S024 and S036 uncertainty notes refer to current units 15 and 27. Its aggregate 20/14/2 confidence counts cannot be assigned to individual rows. All 48 Western English renderings differ from their corresponding Kamri renderings.\n\nFive source routes were encountered; three were fetched raw. The Harvard accountability source returned 405 and MDPI returned 403; two unverified mirrors were excluded. The official misinformation roundup was acquired. Fourteen relevant pages across four persisted PDFs were inspected. Christisis remains unreviewed scan OCR, Gad remains a mirror/edition issue, and the alchemical source edition remains qualified. Missing full-unit matches are unresolved, not proof of incorrect translations.\n\nFourteen conservative source components remain the split boundaries; all have prior exposure. Three additionally cited research papers attach to the existing Models of Magic component and create no untouched component. No model ran, no meanings were promoted, no semantic training labels or new test folds were admitted.\n\nThe next useful work is to repair annotation locators and obtain complete original FL/source passages for a narrowly registered correspondence review, with an independently reviewed subset and source-group evaluation boundaries.\n'
  (out/'report.md').write_text(md)
  m.update(state='completed',outcome='package_accounted_for_with_unresolved_reference_coverage',finished_at_utc=utc(),elapsed_seconds=time.monotonic()-start,output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
  dump_json(out/'manifest.json',m);print(json.dumps(stats,indent=2))
 except Exception as exc:
  m.update(state='failed',error=f'{type(exc).__name__}: {exc}');dump_json(out/'manifest.json',m);raise

def duplicate_groups(articles,side):
 groups={}
 for a in articles:
  for u in a['units']:groups.setdefault(digest(' '.join(u[side].split()).encode()),[]).append(u['uid'])
 return groups
if __name__=='__main__':main()
