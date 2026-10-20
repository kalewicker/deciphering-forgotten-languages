"""Separate offline reconstruction of E65; does not import production E65 code."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup,NavigableString,Tag
from fl_decipher.source_intake_v37 import citation
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def main():
    run=ROOT/'runs/000065_textual_references';check_hashes(run)
    cfg=read('experiments/textual_references_v65.json');pre=read('data/v65/preflight.json');manifest=read('runs/000065_textual_references/manifest.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/textual_references_v65.json']==sha('experiments/textual_references_v65.json')
    assert read('runs/000064_archive_admission/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['network_request_budget']==cfg['source_selection_budget']==0 and cfg['preparatory_exposure_disclosed'] is True
    raw=(ROOT/cfg['raw']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
    dom={id(t):i for i,t in enumerate(soup.select('*'))};bodies=soup.select('div.post-body');assert len(bodies)==1
    body=bodies[0];children=list(body.children);child_ids={id(n):i for i,n in enumerate(children)}
    nodes=[n for n in body.descendants if isinstance(n,NavigableString)];node_ids={id(n):i for i,n in enumerate(nodes)}
    for t in body.find_all(['script','style','noscript']):t.decompose()
    leaves=[];runs=[];pieces=[];offset=0
    for child in children:
        # Removed runtime children no longer have this parent.
        if child.parent is not body:continue
        strings=list(child._all_strings(strip=False)) if isinstance(child,Tag) else [child] if type(child) in body.MAIN_CONTENT_STRING_TYPES else []
        strings=[n for n in strings if str(n).strip()]
        if not strings:continue
        start=offset+bool(pieces);leaf_ids=[]
        for node in strings:
            value=str(node).strip();a=offset+bool(pieces);offset=a+len(value)
            leaves.append({'body_text_node_index':node_ids[id(node)],'span':[a,offset],'text':value,
                'direct_child_index':child_ids[id(child)],'parent_dom_tag_index':dom[id(node.parent)]})
            leaf_ids.append(len(leaves)-1);pieces.append(value)
        runs.append({'run_id':len(runs),'direct_child_index':child_ids[id(child)],'owner_tag':child.name if isinstance(child,Tag) else None,
            'owner_dom_tag_index':dom[id(child)] if isinstance(child,Tag) else None,'span':[start,offset],'leaf_ids':leaf_ids})
    text=' '.join(pieces);export=read(cfg['export'])
    assert text==body.get_text(' ',strip=True)==export['text'] and len(text)==export['unicode_characters']
    assert sha(cfg['raw'])==export['parent_sha256'] and hashlib.sha256(text.encode()).hexdigest()==export['text_sha256']
    for r in runs:r['text']=text[slice(*r['span'])]
    boundary=[r['run_id'] for r in runs if r['owner_tag']=='div' and r['text'].startswith('Aissen, Judith (2003).')]
    refs=[]
    for r in runs[boundary[0]:] if len(boundary)==1 else []:
        years=[]
        for m in re.finditer(r'\d+',r['text']):
            if len(m.group())==4 and m.group()[:2] in ['18','19','20']:
                years.append({'literal':m.group(),'span':[r['span'][0]+m.start(),r['span'][0]+m.end()]})
        refs.append({'reference_id':len(refs),'run_id':r['run_id'],'span':r['span'],'text':r['text'],'year_witnesses':years,
            'identifier_occurrence_ids':[],'resolution_status':'no_recognized_direct_identifier'})
    # Independently enumerate the admitted label forms and bare DOI candidates.
    candidates=[]
    for label in re.finditer(r'(?i)(?<!\w)(?:arxiv(?:\.org)?\s*:\s*|doi\s*:\s*|https?://(?:dx\.)?doi\.org/)',text):
        end=label.end()
        while end<len(text) and not text[end].isspace():end+=1
        while end>label.end() and text[end-1] in '.,;)]}':end-=1
        candidates.append((label.start(),label.end(),end,'arxiv' if text[label.start():label.start()+5].lower()=='arxiv' else 'doi'))
    for token in re.finditer(r'(?i)(?<![\w./])10\.[0-9]{4,9}/\S+',text):
        if any(a<=token.start()<c for a,b,c,k in candidates):continue
        end=token.end()
        while end>token.start() and text[end-1] in '.,;)]}':end-=1
        candidates.append((token.start(),token.start(),end,'doi'))
    known={c['identifier'] for u in read(cfg['known_exposure'])['urls'] if (c:=citation(u))}
    occurrences=[];first={}
    for a,b,c,kind in sorted(candidates):
        literal=text[b:c];owners=[r for r in runs if r['span'][0]<=a and c<=r['span'][1]]
        if kind=='arxiv':m=re.fullmatch(r'([0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[a-z-]+)?/[0-9]{7})(v[1-9][0-9]*)?',literal,re.I)
        else:m=re.fullmatch(r'10\.[0-9]{4,9}/\S+',literal,re.I)
        valid=m is not None and len(owners)==1
        identifier=kind+':'+(m[1] if kind=='arxiv' else literal).lower() if valid else None
        version=m[2] if valid and kind=='arxiv' else None
        ref_ids=[r['reference_id'] for r in refs if r['span'][0]<=a and c<=r['span'][1]];i=len(occurrences)
        occurrences.append({'occurrence_id':i,'kind':kind,'span':[a,c],'token_span':[b,c],'literal':literal,'identifier':identifier,
            'declared_version':version,'version_status':'explicit' if version else 'unspecified' if kind=='arxiv' else 'not_applicable',
            'run_id':owners[0]['run_id'] if len(owners)==1 else None,'reference_ids':ref_ids,
            'status':'recognized_syntax_only' if valid else 'cross_run_token' if len(owners)!=1 else 'malformed_identifier',
            'duplicate_of_occurrence':first.get(identifier) if identifier else None,
            'prior_registry_status':'identifier_recorded' if identifier in known else 'identifier_not_recorded_in_frozen_inventory' if identifier else 'not_applicable'})
        if identifier and identifier not in first:first[identifier]=i
        for j in ref_ids:
            refs[j]['identifier_occurrence_ids'].append(i)
            if identifier:refs[j]['resolution_status']='identifier_syntax_recovered_metadata_unverified'
    expected={'raw_parent_sha256':sha(cfg['raw']),'text_sha256':export['text_sha256'],'unicode_characters':len(text),
        'leaves':leaves,'runs':runs,'boundary_match_run_ids':boundary,'tail_status':'located_exposed_boundary' if len(boundary)==1 else 'unresolved_boundary',
        'references':refs,'identifier_occurrences':occurrences,'recognized_identifiers':list(first),'known_identifier_matches':sorted(set(first)&known),
        'network_requests':0,'source_candidates_selected':0,'source_identity_admitted':False,'untouched_test_eligible':False}
    assert read('data/v65/reference_inventory.json')==expected
    report=read('runs/000065_textual_references/report.json')
    counts={'body_characters':len(text),'included_text_leaves':len(leaves),'nonempty_owner_runs':len(runs),'boundary_matches':len(boundary),
        'tail_status':expected['tail_status'],'reference_rows':len(refs)}
    counts['reference_rows_with_recognized_identifier']=sum(r['resolution_status']=='identifier_syntax_recovered_metadata_unverified' for r in refs)
    counts['reference_rows_without_recognized_identifier']=len(refs)-counts['reference_rows_with_recognized_identifier']
    counts.update({'identifier_occurrences':len(occurrences),'malformed_or_cross_run_occurrences':sum(o['identifier'] is None for o in occurrences),
        'recognized_identifiers':list(first),'known_identifier_matches':expected['known_identifier_matches']})
    for k,v in counts.items():assert report[k]==v,k
    for k in ['research_network_requests','source_candidates_selected','source_requests','alignment_or_lexical_scores','new_connected_works_confirmed','independent_reviews_admitted','untouched_test_units_admitted','semantic_or_source_identity_admissions']:assert report[k]==0
    assert report['historical_e63_outcome_preserved'] is True and report['historical_e63_gate_value'] is False
    assert read('data/v63/target_gate.json')['passed'] is False and read('data/v64/admission_decision.json')['limited_admission'] is True
    assert sorted(p.name for p in (ROOT/'data/v65').iterdir())==['preflight.json','reference_inventory.json']
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=64;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==64
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000065_textual_references/manifest.json'),
        'all_text_leaves_owner_runs_reference_rows_identifier_spans_replayed':True,'production_v65_functions_not_imported':True,
        'shared_components':['BeautifulSoup html.parser','sealed E37 URL recognizer for exposure comparison'],
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'verification_network_requests':0,
        'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'counts':counts,'prior_runs_preserved':prior}
    out=ROOT/'reports/000065_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
