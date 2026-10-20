"""Replay card/anchor decisions without importing production v61 functions."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def clean(t): return ' '.join(t.split())
def strict_key(url):
    if url is None: return None
    try:
        u = urlsplit(url)
        if u.scheme != 'https' or u.hostname != 'physicsworld.com' or u.port not in (None,443) or u.username is not None or u.password is not None or u.query or u.fragment: return None
        if re.fullmatch(r'/a/[a-z0-9]+(?:-[a-z0-9]+)*/?',u.path): return 'https://physicsworld.com'+u.path.rstrip('/')+'/'
    except (ValueError,TypeError): pass
    return None

def broad_safe(url):
    try:
        u=urlsplit(url)
        return u.scheme=='https' and u.hostname=='physicsworld.com' and u.port in (None,443) and u.username is None and u.password is None and u.path.startswith('/a/') and '?' not in url and '#' not in url
    except (ValueError,TypeError): return False


def main():
    cfg=read('experiments/result_attribution_v61.json'); pre=read('data/v61/preflight.json'); saved=read('data/v61/attribution.json')
    run=ROOT/'runs/000061_result_attribution'; manifest=read('runs/000061_result_attribution/manifest.json'); report=read('runs/000061_result_attribution/report.json')
    check_hashes(run)
    for p,h in pre['hashes'].items(): assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items(): assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/result_attribution_v61.json']==sha('experiments/result_attribution_v61.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['network_request_budget']==0 and read('data/v60/observation.json')['complete_direct_html_observation']
    raw=(ROOT/cfg['raw']).read_bytes(); receipt=read(cfg['receipt']); prior=read(cfg['prior_registry'])
    assert sha(cfg['raw'])==receipt['artifacts']['body.bin']['sha256'] and len(raw)==receipt['artifacts']['body.bin']['bytes']
    soup=BeautifulSoup(raw,'html.parser'); schema=cfg['schema']; url=cfg['url']
    tags=soup.select('*'); positions={id(t):i for i,t in enumerate(tags)}; anchors=soup.select('a[href]'); anchor_ids={id(t):i for i,t in enumerate(anchors)}
    bodies=soup.select('body'); mains=soup.select(schema['main_selector']); containers=soup.select(schema['container_selector']); cards=soup.select(schema['card_selector'])
    page_checks={'one_search_body':len(bodies)==1 and 'search' in bodies[0].get('class',[]) and 'search-results' in bodies[0].get('class',[]),
        'one_registered_main':len(mains)==1,'one_registered_container':len(containers)==1,
        'exact_title':[clean(t.get_text(' ',strip=True)) for t in soup.select('title')]==[schema['expected_title']],
        'exact_query_heading':[clean(t.get_text(' ',strip=True)) for t in soup.select(schema['heading_selector'])]==[schema['expected_heading']],
        'no_base_href':len(soup.select('base[href]'))==0}
    assert saved['page_checks']==page_checks and saved['page_attribution_supported']==all(page_checks.values())
    assert len(cards)==len(saved['cards'])
    card_ids={id(t):i for i,t in enumerate(cards)}; expected_rows=[]; seen={}
    def node(t):return {'dom_tag_index':positions[id(t)],'text':t.get_text(' ',strip=True)}
    for i,c in enumerate(cards):
        infos=[t for t in c.children if getattr(t,'name',None)=='div' and 'listing-block__info' in t.get('class',[])]
        title_nodes=[a for d in infos for h in d.children if getattr(h,'name',None)=='h3' and 'listing-block__title' in h.get('class',[]) for a in h.children if getattr(a,'name',None)=='a' and a.has_attr('href')]
        images=[t for t in c.children if getattr(t,'name',None)=='a' and 'listing-block__image' in t.get('class',[]) and t.has_attr('href')]
        snippets=[p for d in infos for p in d.children if getattr(p,'name',None)=='p']
        dates=c.select('time,[datetime],.date,.listing-block__date'); resolved=[]
        for a in title_nodes+images:
            try:resolved.append(urljoin(url,a['href']) if page_checks['no_base_href'] else None)
            except (ValueError,TypeError):resolved.append(None)
        title=clean(title_nodes[0].get_text(' ',strip=True)) if len(title_nodes)==1 else None
        checks={'page_checks_pass':all(page_checks.values()),'direct_child_of_registered_container':len(containers)==1 and c.parent is containers[0],
            'no_nested_listing_cards':all(id(p) not in card_ids for p in c.parents) and not any(t is not c and id(t) in card_ids for t in c.descendants),
            'one_info_block':len(infos)==1,'one_title_link':len(title_nodes)==1,'one_image_link':len(images)==1,
            'one_nonempty_snippet':len(snippets)==1 and bool(snippets[0].get_text(' ',strip=True)), 'nonempty_title':bool(title),
            'title_attribute_consistent':len(title_nodes)==1 and ('title' not in title_nodes[0].attrs or clean(title_nodes[0]['title'])==title),
            'title_image_same_safe_url':len(resolved)==2 and resolved[0]==resolved[1] and broad_safe(resolved[0])}
        attributed=all(checks.values()); chosen=resolved[0] if len(title_nodes)==1 and resolved else None; key=strict_key(chosen)
        duplicate=seen.get(chosen) if chosen else None
        if chosen and chosen not in seen:seen[chosen]=i
        expected_rows.append({'card_index':i,'dom_tag_index':positions[id(c)],'checks':checks,'structurally_attributed':attributed,'failed_checks':[k for k,v in checks.items() if not v],
            'title':title,'title_links':[{**node(t),'anchor_index':anchor_ids[id(t)],'href':t['href']} for t in title_nodes],
            'image_links':[{**node(t),'anchor_index':anchor_ids[id(t)],'href':t['href']} for t in images], 'snippets':[node(t) for t in snippets],
            'date_markers':[{**node(t),'tag':t.name,'datetime':t.get('datetime')} for t in dates],
            'date_status':'markers_require_later_validation' if dates else 'not_supplied_in_registered_card_channels',
            'resolved_url':chosen,'strict_article_key':key,'strict_url_usable':bool(attributed and key),
            'strict_url_reason':'usable_for_future_registration' if attributed and key else 'strict_article_url_rejected' if attributed else 'card_schema_rejected',
            'duplicate_of_card_index':duplicate,'prior_registry_tags':prior['article_exposures'].get(key,[]),
            'previously_captured_in_registry':key in prior['captured_article_keys'] if key else False,
            'exposure_status':'exposed_development_data','article_eligibility_assessed':False,'nominated':False})
    assert expected_rows==saved['cards']
    ledger=[]; exposures={k:list(v) for k,v in prior['article_exposures'].items()}
    for i,a in enumerate(anchors):
        owners=[card_ids[id(p)] for p in a.parents if id(p) in card_ids]; role='outside_listing_cards'
        if len(owners)>1:role='ambiguous_nested_card_ownership'
        elif len(owners)==1:
            r=expected_rows[owners[0]]
            if not r['structurally_attributed']:role='rejected_card_link'
            elif any(t['anchor_index']==i for t in r['title_links']):role='attributed_title_link'
            elif any(t['anchor_index']==i for t in r['image_links']):role='attributed_image_duplicate'
            else:role='supporting_card_link'
        try:resolved=urljoin(url,a['href']) if page_checks['no_base_href'] else None
        except (ValueError,TypeError):resolved=None
        key=strict_key(resolved)
        row={'anchor_index':i,'dom_tag_index':positions[id(a)],'href':a['href'],'text':a.get_text(' ',strip=True),'resolved_url':resolved,
            'strict_article_key':key,'owner_card_indices':owners,'role':role,'prior_registry_tags':prior['article_exposures'].get(key,[]),'exposure_status':'exposed_development_data'}
        ledger.append(row)
        if key:exposures.setdefault(key,[]).append(f'v60_saved_search:anchor{i:03d}')
    assert ledger==saved['anchor_ledger']
    old=read('data/v60/layout.json')['anchors'];assert len(old)==len(ledger)==115
    for a,b in zip(old,ledger):
        for k in ['anchor_index','dom_tag_index','href','text','resolved_url']:assert a[k]==b[k]
        assert a['article_key_diagnostic']==b['strict_article_key']
    registry={'scope':'Frozen v58 registry plus every strict article URL in saved v60 anchors; incomplete lifetime exposure and source grouping',
        'article_exposures':{k:sorted(set(v)) for k,v in sorted(exposures.items())},'captured_article_keys':prior['captured_article_keys'],
        'all_listing_urls_exposed':sorted({r['resolved_url'] for r in expected_rows if r['resolved_url']})}
    assert saved['exposure_registry']==registry and set(saved)=={'page_checks','page_attribution_supported','cards','anchor_ledger','exposure_registry'}
    usable=[r for r in expected_rows if r['strict_url_usable']]
    expected={'experiment_id':'result_attribution_v61','research_network_requests':0,'page_attribution_supported':all(page_checks.values()),
        'listing_card_denominator':len(cards),'structurally_attributed_cards':sum(r['structurally_attributed'] for r in expected_rows),
        'rejected_card_schemas':sum(not r['structurally_attributed'] for r in expected_rows),'strict_url_usable_cards':len(usable),
        'unique_strict_article_urls':len({r['strict_article_key'] for r in usable}),
        'strict_url_rejected_attributed_cards':sum(r['structurally_attributed'] and not r['strict_url_usable'] for r in expected_rows),
        'cards_without_date_markers':sum(not r['date_markers'] for r in expected_rows),'previously_captured_usable_cards':sum(r['previously_captured_in_registry'] for r in usable),
        'anchor_occurrences_accounted':len(ledger),'anchor_role_counts':dict(sorted(Counter(r['role'] for r in ledger).items())),
        'nominations':0,'article_eligibility_assessments':0,'new_article_captures':0,'numeric_or_alignment_scores':0,
        'opaque_meanings_or_source_identities_admitted':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'future_challenge':{'candidate_slots':2,'minimum_window_bag_capacity':6,'numeric_window_cap':11,'status':'requires_new_registration_before_intake',
            'stop_after_fixed_batch':True,'if_no_capable_comparator':'close_this_discovery_route_as_feasibility_limited'},'previous_results_preserved':True}
    assert report==expected
    assert sorted(p.name for p in (ROOT/'data/v61').iterdir())==['attribution.json','preflight.json']
    previous=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=60
        check_hashes(p.parent);previous.append(p.parent.name)
    assert len(previous)==60
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000061_result_attribution/manifest.json'),'original_115_anchor_occurrences_and_card_accounting_replayed':True,
        'listing_cards_verified':len(cards),'structurally_attributed_cards':expected['structurally_attributed_cards'],'strict_url_usable_cards':len(usable),
        'exposure_union_and_capture_status_preserved':True,'production_v61_functions_not_imported':True,'shared_html_parser':'BeautifulSoup html.parser',
        'strict_url_predicate_reimplemented':True,'verification_network_requests':0,'article_eligibility_or_quantity_correspondence_validated':False,
        'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':previous}
    out=ROOT/'reports/000061_verification.json'
    if out.exists():assert {k:v for k,v in json.loads(out.read_text()).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(previous)},indent=2))


if __name__=='__main__':main()
