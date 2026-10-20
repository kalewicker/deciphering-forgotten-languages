"""Fixed quote discovery ledger; snippets are observations, never instructions."""
import hashlib
import ipaddress
import re
from urllib.parse import urlsplit,urlunsplit
from bs4 import BeautifulSoup
from fl_decipher.publisher_intake_v50 import response_text,result_headers
from fl_decipher.dated_capture_scope_v38 import literal_hits,normalized

MARKER='flv69absencecontrol20261020'


def bounded_hits(query,text):
    needle=normalized(query);hay=normalized(text);found=[]
    for h in literal_hits(query,text):
        a,b=h['normalized_span']
        if re.match(r'\w',needle[0]) and a and re.match(r'\w',hay[a-1]):continue
        if re.match(r'\w',needle[-1]) and b<len(hay) and re.match(r'\w',hay[b]):continue
        found.append(h)
    return found


def freeze_target(inventory,export):
    block=inventory['blocks'][1]
    if block['block_id']!=1 or block['run_id']!=4 or block['body_span']!=[790,915] or export['text'][790:915]!=block['text']:
        raise ValueError('frozen target mismatch')
    words=block['text'].split()
    if len(words)!=18:raise ValueError('target token count mismatch')
    phrases=[block['text'],' '.join(words[:12])]
    return {'block_id':1,'run_id':4,'body_span':[790,915],'text':block['text'],'text_sha256':hashlib.sha256(block['text'].encode()).hexdigest(),
        'selection_after_prior_exposure':True,'selection_ledger':[{'block_id':b['block_id'],'run_id':b['run_id'],'body_span':b['body_span'],'selected':b['block_id']==1,
        'reason':'fixed_first_previously_exposed_English_block' if b['block_id']==1 else 'not_registered_target'} for b in inventory['blocks']],
        'phrases':phrases,'requests':[{'search_query':[{'q':'"'+p+'"'}],'response_length':'long'} for p in phrases]}


def safe_url(url):
    try:
        p=urlsplit(url);host=p.hostname
        if p.scheme!='https' or not host or p.username is not None or p.password is not None or p.port not in (None,443) or any(c.isspace() for c in url):return None
        if host=='localhost' or '.' not in host or host.endswith(('.localhost','.local','.internal')):return None
        try:
            if not ipaddress.ip_address(host).is_global:return None
        except ValueError:pass
        return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))
    except (ValueError,TypeError):return None


def ledger(responses,target,known_urls,post_title):
    calls=[];seen=set();selected=None
    for qi,saved in enumerate(responses):
        text=response_text(saved['response']) if saved['error'] is None else None
        rows=result_headers(text) if text is not None else []
        markers=len(re.findall(r'\[wordlim(?::|\s)',text)) if text is not None else 0
        supported=text is not None and markers==len(rows)
        entries=[]
        for row in rows:
            url=safe_url(row['url']);host=(urlsplit(url).hostname or '') if url else ''
            snippet_start=sum(len(line) for line in row['response_text'].splitlines(keepends=True)[:2])
            snippet=row['response_text'][snippet_start:]
            phrase_hits=bounded_hits(target['phrases'][qi],snippet);full_hits=bounded_hits(target['text'],snippet)
            echo=bool('forgottenlanguages' in host or host.endswith(('.blogspot.com','.blogger.com')) or host in ['blogspot.com','blogger.com']
                or normalized(post_title) in normalized(row['response_text']) or 'quantum-semantic-fields-and-universals' in row['response_text'].casefold())
            duplicate=url in seen if url else False
            if url:seen.add(url)
            eligible=bool(supported and url and phrase_hits and not echo and not duplicate)
            reason='unsupported_response_boundaries' if not supported else 'unsafe_or_non_https_url' if url is None else 'recognizable_fl_echo' if echo else 'duplicate_returned_url' if duplicate else 'registered_query_phrase_not_visible' if not phrase_hits else 'native_slot_already_filled' if selected else 'selected_first_eligible_query_phrase_lead'
            nominated=reason=='selected_first_eligible_query_phrase_lead'
            witnesses=[]
            for kind,hits in [('registered_query_phrase',phrase_hits),('complete_target',full_hits)]:
                for h in hits:witnesses.append({'kind':kind,**h,'source_span':[snippet_start+h['source_span'][0],snippet_start+h['source_span'][1]],
                    'normalized_coordinate_scope':'snippet_after_two_header_lines','response_span':[row['response_span'][0]+snippet_start+h['source_span'][0],row['response_span'][0]+snippet_start+h['source_span'][1]]})
            entry={**row,'snippet_span':[snippet_start,len(row['response_text'])],'capture_url':url,'query_phrase_visible':bool(phrase_hits),'complete_target_visible':bool(full_hits),'witnesses':witnesses,
                'recognizable_fl_echo':echo,'duplicate_returned_url':duplicate,'recorded_url_in_frozen_registry':bool(url and url in {safe_url(u) for u in known_urls}),
                'eligible_query_phrase_lead':eligible,'decision_reason':reason,'nominated':nominated}
            entries.append(entry)
            if nominated:selected={'query_index':qi,'rank':row['rank'],'url':url,'original_returned_url':row['url'],'title':row['title'],'complete_target_visible_in_discovery':bool(full_hits)}
        calls.append({'query_index':qi,'response_text':text,'response_text_sha256':hashlib.sha256(text.encode()).hexdigest() if text is not None else None,
            'response_format_supported':supported,'wordlim_marker_count':markers,'attributable_hits':len(rows),'hits':entries})
    return {'calls':calls,'selected':selected,'search_call_denominator':2,'native_slot_denominator':1,'search_engine_exact_matching_observable':False,
        'independence_or_untouched_status_established':False,'source_identity_admitted':False}


def html_view(raw):
    soup=BeautifulSoup(raw,'html.parser')
    titles=[t.get_text(' ',strip=True) for t in soup.select('title')]
    for t in soup.select('script,style,noscript,template,svg,canvas'):t.decompose()
    bodies=soup.select('body');text=bodies[0].get_text(' ',strip=True) if len(bodies)==1 else ''
    return {'body_count':len(bodies),'text':text,'titles':titles,'no_challenge':not any(v in text.casefold() for v in ['cf-chl-','verify you are human','checking your browser','enable javascript and cookies to continue'])}


def native_presence(text,target):
    hits=literal_hits(target,text)
    first=next((line for line in text.splitlines() if line.strip()),'');positive=' '.join(first.split()[:12]);positive_hits=literal_hits(positive,text) if positive else []
    negative=target+' '+MARKER;negative_hits=literal_hits(negative,text);collision=MARKER in normalized(text) or MARKER in normalized(target)
    return {'complete_target_hits':hits,'complete_target_visible':bool(hits),
        'positive_control':{'query':positive,'hits':positive_hits,'passed':bool(positive_hits)},
        'negative_control':{'query':negative,'hits':negative_hits,'marker_collision':collision,'passed':not negative_hits and not collision},
        'controls_passed':bool(positive_hits) and not negative_hits and not collision}
