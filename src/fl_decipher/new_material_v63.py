"""One non-ANITA archived-post recovery; citation metadata only, no correspondence."""
import base64
from email.utils import parsedate_to_datetime
import hashlib
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from fl_decipher.dated_capture_scope_v38 import archive_selection
from fl_decipher.source_intake_v37 import citation, citation_metadata


def norm(s):return ' '.join(s.casefold().split())
def choose_post(nominations):
    rows=nominations['nominees']
    # Original E37 order, excluding its ANITA post00; no new ranking.
    return next((r for r in rows if r['post_id']!='post00'),None)


def recover(raw,headers,receipt,selection,cfg):
    soup=BeautifulSoup(raw,'html.parser');bodies=soup.select('div.post-body')
    titles=[t.get_text(' ',strip=True) for t in soup.select('title,.post-title')]
    canonical=[t.get('href','') for t in soup.select('link[rel~=canonical]')]
    canonical+=[t.get('content','') for t in soup.select('meta[property="og:url"]')]
    expected=urlsplit(cfg['fl_url']);identity=False
    try:
        identity=bool(canonical) and all((u.scheme,u.hostname,u.path,u.query) in [(expected.scheme,expected.hostname,expected.path,''),(expected.scheme,expected.hostname,expected.path,'m=0')] for value in canonical for u in [urlsplit(value)])
    except ValueError:pass
    text=None
    if len(bodies)==1:
        for t in bodies[0].select('script,style,noscript'):t.decompose()
        text=bodies[0].get_text(' ',strip=True)
    memento=None
    blocks=re.split(r'\r?\n\r?\n',headers.decode('iso-8859-1'))
    response_blocks=[b for b in blocks if re.match(r'HTTP/\S+\s+\d+',b)]
    if response_blocks:
        values=re.findall(r'^memento-datetime:\s*(.+?)\s*$',response_blocks[-1],re.I|re.M)
        if len(values)==1:
            try:memento=parsedate_to_datetime(values[0]).strftime('%Y%m%d%H%M%S')
            except (ValueError,TypeError,OverflowError):pass
    record=selection.get('record');digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
    checks={'archive_selection_eligible':selection['eligible'],'replay_complete_200':receipt.get('transport_complete') is True,
        'exact_replay_url':receipt.get('final_url')==selection.get('replay_url'),
        'single_post_body':len(bodies)==1,'known_title_present':any(norm(cfg['title_prefix']) in norm(t) for t in titles),
        'all_native_identity_fields_bound':identity,'body_nonempty':bool(text),
        'no_challenge':not any(v in raw.decode(errors='replace').casefold() for v in ['cf-chl-','verify you are human','checking your browser','enable javascript and cookies to continue']),
        'memento_matches_cdx':bool(record and memento==record['timestamp']),
        'body_digest_matches_cdx':bool(record and digest==record['digest'])}
    passed=all(checks.values())
    return {'checks':checks,'passed':passed,'unmet':[k for k,v in checks.items() if not v],'titles':titles,'identity_urls':canonical,
        'capture_timestamp':record['timestamp'] if record else None,'memento_timestamp':memento,'body_sha1_base32':digest,
        'body_text':text if passed else None,'body_text_sha256':hashlib.sha256(text.encode()).hexdigest() if passed else None,
        'representation':'dated_archival_post_body_export' if passed else 'unavailable_or_rejected','raw_post':passed,
        'current_post':False,'historical_publication_wording_authenticated':False,'opaque_text_compared':False,'untouched_test_eligible':False}


def sources(raw,known_urls):
    metadata=citation_metadata(raw.decode('utf-8',errors='replace'));known={c['identifier'] for u in known_urls if (c:=citation(u))};seen=set();ledger=[];chosen=None
    for c in metadata['eligible_citations']:
        reason=('not_arxiv_route' if c['kind']!='arxiv' else 'known_exposed_identifier' if c['identifier'] in known else
                'duplicate_identifier' if c['identifier'] in seen else 'single_source_cap' if chosen is not None else 'selected_first_unrecorded_arxiv_identifier')
        seen.add(c['identifier']);row={**c,'reason':reason,'selected':reason=='selected_first_unrecorded_arxiv_identifier'};ledger.append(row)
        if row['selected']:chosen=c
    return {'all_citation_metadata':metadata,'source_candidate_ledger':ledger,'selected':chosen,
        'novel_connected_work_confirmed':False,'prior_absence_is_not_independence':True,'source_identity_admitted':False}
