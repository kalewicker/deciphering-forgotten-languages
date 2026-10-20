"""Fixed cited-work metadata/first-page checks, without passage correspondence."""
from datetime import datetime, timezone
import re
import unicodedata
from bs4 import BeautifulSoup


def norm(value):return ' '.join(unicodedata.normalize('NFC',value).casefold().split())
def select(inventory):
    for reference in inventory['references']:
        for i in reference['identifier_occurrence_ids']:
            occurrence=inventory['identifier_occurrences'][i]
            if occurrence['identifier'] and occurrence['kind']=='arxiv':
                return {'identifier':occurrence['identifier'],'reference_id':reference['reference_id'],'occurrence_id':i,
                        'citation_span':reference['span'],'identifier_span':occurrence['token_span'],'citation_text':reference['text'],
                        'citation_declared_version':occurrence['declared_version'],'edition_policy':'prospectively_choose_v1_if_native_history_verifies'}
    return None


def transport(receipt,url,content_type):
    return bool(receipt.get('transport_complete') is True and receipt.get('http_status')==200
                and receipt.get('num_redirects')==0 and receipt.get('final_url')==url
                and (receipt.get('content_type') or '').split(';')[0].strip().lower()==content_type)


def metadata(raw,receipt,cfg):
    soup=BeautifulSoup(raw,'html.parser')
    def values(name):return [t.get('content','') for t in soup.find_all('meta',attrs={'name':name})]
    titles=values('citation_title');authors=values('citation_author');ids=values('citation_arxiv_id');dates=values('citation_date')
    containers=soup.select('.submission-history');histories=[t.get_text(' ',strip=True) for t in containers]
    rows=[];labels=[]
    for ci,text in enumerate(histories):
        matches=list(re.finditer(r'\[v([0-9]+)\]',text))
        for i,m in enumerate(matches):
            labels.append(int(m[1]));tail=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
            d=re.match(r'\s*([A-Za-z]{3},\s+[0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\s+UTC)',tail)
            stamp=None
            if d:
                try:
                    parsed=datetime.strptime(d[1],'%a, %d %b %Y %H:%M:%S UTC').replace(tzinfo=timezone.utc)
                    if parsed.strftime('%a')==d[1][:3]:stamp=parsed.isoformat()
                except ValueError:pass
            rows.append({'container_index':ci,'version':int(m[1]),'literal_date':d[1] if d else None,'submitted_at_utc':stamp})
    ordered=sorted(rows,key=lambda r:r['version']);v1=[r for r in rows if r['version']==1]
    history_ok=bool(len(containers)==1 and rows and labels and len(set(labels))==len(labels)
        and sorted(labels)==list(range(1,len(rows)+1)) and all(r['submitted_at_utc'] for r in rows)
        and [r['submitted_at_utc'] for r in ordered]==sorted(r['submitted_at_utc'] for r in ordered))
    citation_date=None
    if len(dates)==1:
        try:citation_date=datetime.strptime(dates[0],'%Y/%m/%d').date().isoformat()
        except ValueError:pass
    author_ok=False
    if len(authors)==1:
        words=norm(authors[0]).split()
        author_ok=len(words)>=2 and words[-1]==cfg['author_family'] and words[0].startswith(cfg['author_initial'])
    checks={'complete_exact_native_html':transport(receipt,cfg['metadata_url'],'text/html'),
        'single_matching_title':len(titles)==1 and norm(titles[0])==norm(cfg['expected_title']),
        'single_compatible_author':author_ok,'single_matching_arxiv_identifier':len(ids)==1 and ids[0] in [cfg['base_id'],cfg['base_id']+'v1'],
        'complete_consistent_version_history':history_ok,
        'v1_cited_year_and_before_post_date':bool(history_ok and len(v1)==1 and v1[0]['submitted_at_utc'][:4]==str(cfg['citation_year']) and v1[0]['submitted_at_utc'][:10]<cfg['post_date_cutoff']),
        'single_citation_date_in_cited_year':bool(citation_date and citation_date[:4]==str(cfg['citation_year']))}
    return {'checks':checks,'passed':all(checks.values()),'unmet':[k for k,v in checks.items() if not v],
        'native_titles':titles,'native_authors':authors,'native_arxiv_ids':ids,'native_citation_dates':dates,'parsed_citation_date':citation_date,
        'history_container_texts':histories,'history_rows':rows,'selected_edition':'v1' if all(checks.values()) else None,
        'citation_version_unspecified':True,'actual_fl_source_edition_established':False}


def first_page_checks(text,pages,other_pages,receipt,cfg,authors):
    hay=norm(text)
    checks={'complete_exact_native_pdf':transport(receipt,cfg['pdf_url'],'application/pdf'),
        'page_count_bound_and_parsers_agree':0<pages<=cfg['maximum_pdf_pages'] and pages==other_pages,
        'version_marker_in_first_page':bool(re.search(r'(?<![\w.])'+re.escape(cfg['base_id'])+r'v1(?![\w])',text)),
        'title_in_first_page':norm(cfg['expected_title']) in hay,
        'metadata_author_in_first_page':len(authors)==1 and norm(authors[0]) in hay}
    return {'checks':checks,'passed':all(checks.values()),'unmet':[k for k,v in checks.items() if not v]}
