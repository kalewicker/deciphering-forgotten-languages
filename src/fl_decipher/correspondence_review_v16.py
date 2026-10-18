"""Bounded textual correspondence review, with separate provenance and meaning gates."""
from pathlib import Path
import re
from bs4 import BeautifulSoup
from .dataset_audit_v15 import words,occurrences
from .text import sentences,tokens

def extract_html(raw,selector):
    soup=BeautifulSoup(raw,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    body=soup.select_one(selector)
    if body is None:raise ValueError('Registered body selector missing')
    for node in body.select('script,style,noscript,sup,h1,h2,h3,h4'):
        node.decompose()
    full=body.get_text(' ',strip=True)
    # Keep paragraph boundaries: an unpunctuated section heading must not merge
    # with the first sentence of the following paragraph. Preserve headings in full.
    paragraphs=[p.get_text(' ',strip=True) for p in body.find_all('p') if p.get_text(' ',strip=True)]
    text='\n\n'.join(paragraphs)
    blocks=[];offset=0
    for i,p in enumerate(paragraphs):
        blocks.append({'id':i,'text':p,'span':[offset,offset+len(p)]});offset+=len(p)+2
    return {'html_title':title,'full_body_text':full,'text':text,'blocks':blocks,
            'transformations':['BeautifulSoup registered body selector '+selector,
              'remove scripts/styles/noscript/superscript references and h1-h4 headings',
              'full body text retained; separate p-node text joined with two newlines',
              'retain heading-only paragraphs separately; sentence segmentation never crosses paragraph boundaries',
              'no lexical replacements, Unicode accent repairs or paraphrase matching']}

def statements(document):
    result=[]
    for block in document['blocks']:
        for sent in sentences(block['text']):
            result.append({'block_id':block['id'],'text':sent.text,
                'span':[block['span'][0]+sent.start,block['span'][0]+sent.end],
                'terminal_punctuation':bool(re.search(r'[.!?][\"”’\']*$',sent.text))})
    return result

def whole_statement_matches(proposal,document):
    ans=[]
    for s in statements(document):
        if words(proposal)!=words(s['text']):continue
        policy='exact' if proposal==s['text'] else 'whitespace' if ' '.join(proposal.split())==' '.join(s['text'].split()) else 'ordered_words'
        ans.append(s|{'policy':policy,'complete_statement':s['terminal_punctuation']})
    return ans

def gates(*,source_authority,english_statements_unique_complete,fl_statements_unique_complete,
          ordered_nonoverlapping,current_raw_fl,independent_semantic_review,component_novel):
    values=locals();assert all(type(x) is bool for x in values.values())
    dev=all((source_authority,english_statements_unique_complete,fl_statements_unique_complete,ordered_nonoverlapping))
    return {'development_correspondence_review_eligible':dev,
            'current_raw_reference_eligible':dev and current_raw_fl,
            'semantic_training_eligible':dev and current_raw_fl and independent_semantic_review,
            'untouched_test_eligible':dev and current_raw_fl and independent_semantic_review and component_novel,
            'requirements':values}

def ordered_nonoverlapping(matches):
    if not matches or any(len(m)!=1 for m in matches):return False
    spans=[m[0]['span'] for m in matches]
    return all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))

def positional_hypotheses(fl,english,*,fl_offset=0,english_offset=0):
    f,e=tokens(fl,fl_offset),tokens(english,english_offset)
    if len(f)!=len(e):return []
    return [{'index':i,'fl_form':a.normalized,'fl_surface':a.surface,'fl_span':[a.start,a.end],
             'english_form':b.normalized,'english_surface':b.surface,'english_span':[b.start,b.end],
             'status':'unvalidated positional hypothesis; not a lexical meaning label'}
            for i,(a,b) in enumerate(zip(f,e,strict=True))]
