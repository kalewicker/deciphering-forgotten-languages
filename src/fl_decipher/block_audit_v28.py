"""Traceable structural maps; ambiguities never become semantic labels."""
from collections import Counter
from statistics import median
import re
from bs4 import BeautifulSoup
from bs4.element import Tag,NavigableString,CData
from .source_specificity_v26 import tokens,occurrences

BLOCKS={'p','blockquote','li','h1','h2','h3','h4','h5','h6','td','th','div','nav','section','article'}
CITATION=re.compile(r'\[\s*\d+(?:\s*,\s*\d+)*\s*\]')


def dom_paths(body):
    paths={id(body):'post-body'}
    for parent in [body,*body.find_all(True)]:
        for i,node in enumerate(parent.contents):
            paths[id(node)]=paths[id(parent)]+f'/{node.name if isinstance(node,Tag) else "#text"}[{i}]'
    return paths


def html_map(raw,export):
    soup=BeautifulSoup(raw,'html.parser');bodies=soup.select('div.post-body');assert len(bodies)==1
    body=bodies[0];excluded=Counter(n.name for n in body.select('script,style,noscript'))
    for node in body.select('script,style,noscript'):node.decompose()
    paths=dom_paths(body);desc=list(body.descendants);atoms=[];joins=[];cursor=0;empty=0;ignored=Counter()
    events=[]
    for ordinal,node in enumerate(desc):
        if isinstance(node,Tag):
            if node.name in ['br','img','hr']:
                events.append({'dom_event':ordinal,'dom_path':paths[id(node)],'tag':node.name,'attributes':dict(node.attrs)})
            continue
        if type(node) not in (NavigableString,CData):
            ignored[type(node).__name__]+=1;continue
        raw_text=str(node);value=raw_text.strip()
        if not value:empty+=1;continue
        if atoms:joins.append({'start':cursor,'end':cursor+1,'text':' '});cursor+=1
        ancestors=[];p=node.parent
        while p is not None:
            ancestors.append(p)
            if p is body:break
            p=p.parent
        owner=next((p for p in ancestors if p.name in BLOCKS),body)
        tags=[p.name for p in ancestors]
        role=('navigation_markup' if 'nav' in tags else 'quotation_markup' if 'blockquote' in tags else
              'heading_markup' if any(t in tags for t in ['h1','h2','h3','h4','h5','h6']) else
              'list_markup' if 'li' in tags else 'paragraph_markup' if 'p' in tags else 'untyped_block')
        atoms.append({'atom_id':f'a{len(atoms):04d}','dom_event':ordinal,'dom_path':paths[id(node)],
                      'owner_path':paths[id(owner)],'owner_tag':owner.name,'role':role,'ancestor_tags':tags,
                      'links':[{'dom_path':paths[id(p)],'href':p.get('href')} for p in ancestors if p.name=='a'],
                      'emphasis_tags':[t for t in tags if t in ['strong','em','b','i']],
                      'decoded_dom_text':raw_text,'trim_start':len(raw_text)-len(raw_text.lstrip()),'trim_end':len(raw_text.rstrip()),
                      'start':cursor,'end':cursor+len(value),'text':value})
        cursor+=len(value)
    flat=' '.join(a['text'] for a in atoms)
    assert atoms,'empty post body'
    assert export==flat+'\n','saved FL export differs from registered DOM reconstruction'
    blocks=[]
    for atom in atoms:
        if not blocks or blocks[-1]['owner_path']!=atom['owner_path']:
            blocks.append({'block_id':f'b{len(blocks):03d}','owner_path':atom['owner_path'],'owner_tag':atom['owner_tag'],
                           'role':atom['role'],'start':atom['start'],'end':atom['end'],'atom_ids':[]})
        block=blocks[-1];block['end']=atom['end'];block['atom_ids'].append(atom['atom_id']);atom['block_id']=block['block_id']
    byid={a['atom_id']:a for a in atoms}
    for block in blocks:
        aa=[byid[i] for i in block['atom_ids']];block['text']=flat[block['start']:block['end']]
        block['link_only']=all(bool(a['links']) for a in aa)
        block['all_emphasized']=all(bool(a['emphasis_tags']) for a in aa)
        block['starts_with_quote']=block['text'].startswith(('"','“','‘'))
        block['ends_with_quote']=block['text'].endswith(('"','”','’'))
    for event in events:
        prior=[a for a in atoms if a['dom_event']<event['dom_event']];later=[a for a in atoms if a['dom_event']>event['dom_event']]
        event['preceding_export_end']=prior[-1]['end'] if prior else 0
        event['following_export_start']=later[0]['start'] if later else len(flat)
    partition=sorted([{'start':a['start'],'end':a['end'],'text':a['text'],'kind':'atom'} for a in atoms]+[j|{'kind':'join'} for j in joins],key=lambda r:r['start'])
    assert ''.join(p['text'] for p in partition)==flat
    assert all(a['end']==b['start'] for a,b in zip(partition,partition[1:]))
    return {'flat_text':flat,'flat_code_points':len(flat),'saved_export_code_points':len(export),
            'export_suffix':{'start':len(flat),'end':len(export),'text':'\n'},'atoms':atoms,'joins':joins,'blocks':blocks,
            'zero_text_events':events,'empty_strings_omitted':empty,'excluded_tags':dict(excluded),
            'ignored_string_types':dict(ignored),'exact_reconstruction':True,'exact_partition':True}


def line_map(page):
    words=page['words'];groups=[]
    for upright in [True,False]:
        current=None
        for w in sorted([w for w in words if w['upright']==upright],key=lambda w:(w['top'],w['x0'],w['word_index'])):
            if current is None or abs(w['top']-current['anchor_top'])>3:
                current={'anchor_top':w['top'],'upright':upright,'words':[]};groups.append(current)
            current['words'].append(w)
    rules=[]
    for edge in sorted(page['horizontal_edges'],key=lambda e:(e['top'],e['x0'],e['x1'],e['edge_index'])):
        if not (edge['top']>=.55*page['height'] and edge['x1']-edge['x0']>=.2*page['width'] and edge['x0']<=.35*page['width']):continue
        old=next((r for r in rules if all(abs(edge[k]-r[k])<=1 for k in ['top','x0','x1'])),None)
        if old:old['edge_indices'].append(edge['edge_index'])
        else:rules.append({k:edge[k] for k in ['top','x0','x1']}|{'edge_indices':[edge['edge_index']]})
    rule=rules[0] if rules else None;lines=[]
    for g in groups:
        ws=sorted(g['words'],key=lambda w:(w['x0'],w['word_index']));text=' '.join(w['text'] for w in ws)
        a,b=min(w['x0'] for w in ws),max(w['x1'] for w in ws);top,bottom=min(w['top'] for w in ws),max(w['bottom'] for w in ws)
        size=round(median(w['size'] for w in ws),6)
        role=('rotated_text' if not g['upright'] else 'numeric_only_line' if re.fullmatch(r'\d{1,4}',text) else
              'footnote_candidate' if rule and top>=rule['top'] and size<=.95*page['modal_font_size'] else
              'below_rule_unresolved' if rule and top>=rule['top'] else
              'upper_band_text' if bottom<=.08*page['height'] else
              'larger_font_text' if size>1.15*page['modal_font_size'] else 'body_or_unresolved')
        lines.append({'word_indices':[w['word_index'] for w in ws],'upright':g['upright'],'text':text,
                      'x0':a,'x1':b,'top':top,'bottom':bottom,'median_font_size':size,'role_hint':role})
    lines.sort(key=lambda r:(r['top'],r['x0'],not r['upright']))
    for i,line in enumerate(lines):line['line_id']=page['id']+f':line:{i:03d}'
    assert sorted(i for line in lines for i in line['word_indices'])==list(range(len(words)))
    return {'page_id':page['id'],'work':page['work'],'pdf_page_one_based':page['pdf_page_one_based'],
            'candidate_rules':rules,'selected_rule':rule,'lines':lines,'all_words_assigned_once':True}


def concordance(query,target):
    matches=occurrences(target,[query])[0] if tokens(query) else []
    return {'status':'unique' if len(matches)==1 else 'ambiguous' if matches else 'unmapped','matches':matches}


def citations(text):
    return [{'start':m.start(),'end':m.end(),'text':m.group(),'key':re.sub(r'\s+','',m.group())} for m in CITATION.finditer(text)]


def pdf_map(page,raw_page,legacy):
    result=line_map(page)
    for line in result['lines']:
        line['raw_page_concordance']=concordance(line['text'],raw_page)
        line['legacy_window_concordance']=concordance(line['text'],legacy)
    legacy_citations=citations(legacy)
    result['numeric_citations']=[c|{'legacy_occurrences':[m for m in legacy_citations if m['key']==c['key']],
                                  'represented_in_legacy_form':any(m['key']==c['key'] for m in legacy_citations)} for c in citations(raw_page)]
    return result


def fl_reference(reference,mapping,export):
    s=reference['span'];assert type(s['start']) is type(s['end']) is int and 0<=s['start']<s['end']<=len(export)
    assert export[s['start']:s['end']]==s['text']
    hits=[]
    for atom in mapping['atoms']:
        a,b=max(atom['start'],s['start']),min(atom['end'],s['end'])
        if a<b:hits.append({'atom_id':atom['atom_id'],'block_id':atom['block_id'],'start':a,'end':b,'text':export[a:b]})
    block_ids=list(dict.fromkeys(h['block_id'] for h in hits))
    return reference|{'atom_intersections':hits,'block_ids':block_ids,'crosses_block_runs':len(block_ids)>1}


def source_reference(reference,pages,legacy):
    s=reference['span'];assert type(s['start']) is type(s['end']) is int and 0<=s['start']<s['end']<=len(legacy)
    assert legacy[s['start']:s['end']]==s['text'];hits=[]
    for page in pages:
        if page['work']!=reference['work']:continue
        for line in page['lines']:
            overlaps=[]
            for match in line['legacy_window_concordance']['matches']:
                a,b=max(match['start'],s['start']),min(match['end'],s['end'])
                if a<b:overlaps.append({'start':a,'end':b,'text':legacy[a:b]})
            if overlaps:hits.append({'line_id':line['line_id'],'page_id':page['page_id'],
                                     'pdf_page_one_based':page['pdf_page_one_based'],'role_hint':line['role_hint'],'overlaps':overlaps})
    return reference|{'candidate_line_intersections':hits,'resolution':'unmapped' if not hits else 'candidate_intersections_only'}


def union_size(spans):
    total=0;end=0
    for a,b in sorted((s['start'],s['end']) for s in spans):
        total+=max(0,b-max(a,end));end=max(end,b)
    return total


def summarize(fl_maps,pdf_maps,fl_refs,source_refs):
    fl=[]
    for work,m in fl_maps.items():
        fl.append({'work':work,'flat_code_points':m['flat_code_points'],'saved_export_code_points':m['saved_export_code_points'],
                   'atoms':len(m['atoms']),'block_runs':len(m['blocks']),'join_separators':len(m['joins']),
                   'structural_roles':dict(Counter(b['role'] for b in m['blocks'])),
                   'link_only_runs':sum(b['link_only'] for b in m['blocks']),
                   'explicit_quote_runs':sum(b['role']=='quotation_markup' for b in m['blocks']),
                   'zero_text_events':dict(Counter(e['tag'] for e in m['zero_text_events'])),
                   'exact_reconstruction':m['exact_reconstruction'],'exact_partition':m['exact_partition']})
    pages=[]
    for p in pdf_maps:
        pages.append({'page_id':p['page_id'],'lines':len(p['lines']),'words':sum(len(l['word_indices']) for l in p['lines']),
                      'role_hints':dict(Counter(l['role_hint'] for l in p['lines'])),
                      'candidate_rules':len(p['candidate_rules']),
                      'raw_mapping_status':dict(Counter(l['raw_page_concordance']['status'] for l in p['lines'])),
                      'legacy_mapping_status':dict(Counter(l['legacy_window_concordance']['status'] for l in p['lines'])),
                      'raw_unique_mapped_span_code_points':union_size([m for l in p['lines'] if l['raw_page_concordance']['status']=='unique' for m in l['raw_page_concordance']['matches']]),
                      'raw_any_mapped_span_code_points':union_size([m for l in p['lines'] for m in l['raw_page_concordance']['matches']]),
                      'numeric_citation_occurrences':len(p['numeric_citations']),
                      'numeric_citation_occurrences_unrepresented_in_legacy':sum(not c['represented_in_legacy_form'] for c in p['numeric_citations'])})
    return {'fl':fl,'pdf_pages':pages,'fl_references_mapped':len(fl_refs),'fl_references_crossing_block_runs':sum(r['crosses_block_runs'] for r in fl_refs),
            'source_references':len(source_refs),'source_references_without_line_candidates':sum(not r['candidate_line_intersections'] for r in source_refs)}
