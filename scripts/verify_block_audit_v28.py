"""Independent DOM recursion, geometry grouping, concordance and provenance audit."""
from pathlib import Path
from collections import Counter
from itertools import groupby
from statistics import median
from bisect import bisect_left
from datetime import datetime,timezone
import hashlib,json,re,subprocess,sys,unicodedata

ROOT=Path(__file__).resolve().parents[1]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())


def reference_html(raw,export):
    from bs4 import BeautifulSoup
    from bs4.element import Tag,NavigableString,CData
    soup=BeautifulSoup(raw,'html.parser');body=soup.select('div.post-body');assert len(body)==1;body=body[0]
    removed=Counter(n.name for n in body.select('script,style,noscript'))
    for n in body.select('script,style,noscript'):n.decompose()
    def walk(parent,path,chain):
        for i,node in enumerate(parent.contents):
            at=path+f'/{node.name if isinstance(node,Tag) else "#text"}[{i}]'
            yield node,at,chain
            if isinstance(node,Tag):yield from walk(node,at,chain+[(node,at)])
    entries=list(walk(body,'post-body',[(body,'post-body')]));atoms=[];events=[];empty=0;ignored=Counter()
    block_tags={'p','blockquote','li','h1','h2','h3','h4','h5','h6','td','th','div','nav','section','article'}
    for ordinal,(node,path,chain) in enumerate(entries):
        if isinstance(node,Tag):
            if node.name in ['br','img','hr']:events.append({'dom_event':ordinal,'dom_path':path,'tag':node.name,'attributes':dict(node.attrs)})
            continue
        if type(node) not in (NavigableString,CData):ignored[type(node).__name__]+=1;continue
        full=str(node);text=full.strip()
        if not text:empty+=1;continue
        parents=list(reversed(chain));tags=[p.name for p,_ in parents];owner,owner_path=next((p,at) for p,at in parents if p.name in block_tags)
        if 'nav' in tags:role='navigation_markup'
        elif 'blockquote' in tags:role='quotation_markup'
        elif set(tags)&{'h1','h2','h3','h4','h5','h6'}:role='heading_markup'
        elif 'li' in tags:role='list_markup'
        elif 'p' in tags:role='paragraph_markup'
        else:role='untyped_block'
        start=sum(len(a['text']) for a in atoms)+len(atoms)
        atoms.append({'atom_id':f'a{len(atoms):04d}','dom_event':ordinal,'dom_path':path,'owner_path':owner_path,'owner_tag':owner.name,
                      'role':role,'ancestor_tags':tags,'links':[{'dom_path':at,'href':p.get('href')} for p,at in parents if p.name=='a'],
                      'emphasis_tags':[t for t in tags if t in ['strong','em','b','i']],
                      'decoded_dom_text':full,'trim_start':len(full)-len(full.lstrip()),'trim_end':len(full.rstrip()),
                      'start':start,'end':start+len(text),'text':text})
    flat=body.get_text(' ',strip=True);assert atoms and export==flat+'\n'
    assert flat==' '.join(a['text'] for a in atoms)
    joins=[{'start':a['end'],'end':b['start'],'text':' '} for a,b in zip(atoms,atoms[1:])]
    assert all(j['end']-j['start']==1 for j in joins)
    blocks=[]
    for owner,items in groupby(atoms,key=lambda a:a['owner_path']):
        group=list(items);key=f'b{len(blocks):03d}';a,b=group[0]['start'],group[-1]['end'];text=flat[a:b]
        for atom in group:atom['block_id']=key
        blocks.append({'block_id':key,'owner_path':owner,'owner_tag':group[0]['owner_tag'],'role':group[0]['role'],
                       'start':a,'end':b,'atom_ids':[a['atom_id'] for a in group],'text':text,
                       'link_only':all(a['links'] for a in group),'all_emphasized':all(a['emphasis_tags'] for a in group),
                       'starts_with_quote':text.startswith(('"','“','‘')),'ends_with_quote':text.endswith(('"','”','’'))})
    ordinals=[a['dom_event'] for a in atoms]
    for event in events:
        i=bisect_left(ordinals,event['dom_event']);event['preceding_export_end']=atoms[i-1]['end'] if i else 0
        event['following_export_start']=atoms[i]['start'] if i<len(atoms) else len(flat)
    ordered=sorted([(a['start'],a['end'],a['text']) for a in atoms]+[(j['start'],j['end'],j['text']) for j in joins])
    assert ''.join(t for _,_,t in ordered)==flat and all(a[1]==b[0] for a,b in zip(ordered,ordered[1:]))
    return {'flat_text':flat,'flat_code_points':len(flat),'saved_export_code_points':len(export),'export_suffix':{'start':len(flat),'end':len(export),'text':'\n'},
            'atoms':atoms,'joins':joins,'blocks':blocks,'zero_text_events':events,'empty_strings_omitted':empty,
            'excluded_tags':dict(removed),'ignored_string_types':dict(ignored),'exact_reconstruction':True,'exact_partition':True}


def lex(text):
    parts=[]
    for word,items in groupby(enumerate(text),lambda x:x[1].isalnum() or unicodedata.category(x[1])[0]=='M'):
        run=list(items)
        if word and any(c.isalnum() for _,c in run):
            a,b=run[0][0],run[-1][0]+1;parts.append((unicodedata.normalize('NFC',text[a:b]).casefold(),a,b))
    return parts


def reference_concordance(query,target):
    q=[t[0] for t in lex(query)];t=lex(target);matches=[]
    if q:
        for i in range(len(t)-len(q)+1):
            if [x[0] for x in t[i:i+len(q)]]==q:
                a,b=t[i][1],t[i+len(q)-1][2];matches.append({'start':a,'end':b,'text':target[a:b]})
    return {'status':['unmapped','unique','ambiguous'][min(2,len(matches))],'matches':matches}


def reference_citations(text):
    pattern=re.compile(r'\[\s*\d+(?:\s*,\s*\d+)*\s*\]')
    return [{'start':m.start(),'end':m.end(),'text':m.group(),'key':''.join(m.group().split())} for m in pattern.finditer(text)]


def reference_page(page,raw,legacy):
    groups=[]
    for orientation in [True,False]:
        remaining=sorted([w for w in page['words'] if w['upright']==orientation],key=lambda w:(w['top'],w['x0'],w['word_index']))
        while remaining:
            anchor=remaining[0]['top'];n=next((i for i,w in enumerate(remaining) if w['top']-anchor>3),len(remaining))
            groups.append((orientation,remaining[:n]));remaining=remaining[n:]
    candidates=[]
    filtered=[e for e in page['horizontal_edges'] if e['top']>=.55*page['height'] and e['x1']-e['x0']>=.2*page['width'] and e['x0']<=.35*page['width']]
    for e in sorted(filtered,key=lambda e:(e['top'],e['x0'],e['x1'],e['edge_index'])):
        match=None
        for c in candidates:
            if max(abs(e[k]-c[k]) for k in ['top','x0','x1'])<=1:match=c;break
        if match is None:candidates.append({k:e[k] for k in ['top','x0','x1']}|{'edge_indices':[e['edge_index']]})
        else:match['edge_indices'].append(e['edge_index'])
    selected=candidates[0] if candidates else None;lines=[]
    for orientation,group in groups:
        ws=sorted(group,key=lambda w:(w['x0'],w['word_index']));text=' '.join(w['text'] for w in ws)
        x0,x1=min(w['x0'] for w in ws),max(w['x1'] for w in ws);top,bottom=min(w['top'] for w in ws),max(w['bottom'] for w in ws)
        size=round(median([w['size'] for w in ws]),6)
        if not orientation:role='rotated_text'
        elif re.fullmatch(r'\d{1,4}',text):role='numeric_only_line'
        elif selected is not None and top>=selected['top']:
            role='footnote_candidate' if size<=.95*page['modal_font_size'] else 'below_rule_unresolved'
        elif bottom<=.08*page['height']:role='upper_band_text'
        elif size>1.15*page['modal_font_size']:role='larger_font_text'
        else:role='body_or_unresolved'
        lines.append({'word_indices':[w['word_index'] for w in ws],'upright':orientation,'text':text,
                      'x0':x0,'x1':x1,'top':top,'bottom':bottom,'median_font_size':size,'role_hint':role})
    lines.sort(key=lambda l:(l['top'],l['x0'],not l['upright']))
    for i,line in enumerate(lines):
        line['line_id']=page['id']+f':line:{i:03d}'
        line['raw_page_concordance']=reference_concordance(line['text'],raw)
        line['legacy_window_concordance']=reference_concordance(line['text'],legacy)
    assert Counter(i for l in lines for i in l['word_indices'])==Counter(range(len(page['words'])))
    old=reference_citations(legacy);citation_rows=[]
    for c in reference_citations(raw):
        matches=[m for m in old if m['key']==c['key']]
        citation_rows.append(c|{'legacy_occurrences':matches,'represented_in_legacy_form':bool(matches)})
    return {'page_id':page['id'],'work':page['work'],'pdf_page_one_based':page['pdf_page_one_based'],'candidate_rules':candidates,
            'selected_rule':selected,'lines':lines,'all_words_assigned_once':True,'numeric_citations':citation_rows}


def reference_fl_span(r,m,export):
    s=r['span'];assert type(s['start']) is type(s['end']) is int and 0<=s['start']<s['end']<=len(export)
    assert export[s['start']:s['end']]==s['text'];overlaps=[]
    for a in m['atoms']:
        start,end=max(s['start'],a['start']),min(s['end'],a['end'])
        if start<end:overlaps.append({'atom_id':a['atom_id'],'block_id':a['block_id'],'start':start,'end':end,'text':export[start:end]})
    ids=list(dict.fromkeys(o['block_id'] for o in overlaps))
    return r|{'atom_intersections':overlaps,'block_ids':ids,'crosses_block_runs':len(ids)>1}


def reference_source_span(r,pages,legacy):
    s=r['span'];assert type(s['start']) is type(s['end']) is int and 0<=s['start']<s['end']<=len(legacy)
    assert legacy[s['start']:s['end']]==s['text'];lines=[]
    for p in pages:
        if p['work']!=r['work']:continue
        for line in p['lines']:
            overlaps=[]
            for hit in line['legacy_window_concordance']['matches']:
                a,b=max(s['start'],hit['start']),min(s['end'],hit['end'])
                if a<b:overlaps.append({'start':a,'end':b,'text':legacy[a:b]})
            if overlaps:lines.append({'line_id':line['line_id'],'page_id':p['page_id'],'pdf_page_one_based':p['pdf_page_one_based'],
                                      'role_hint':line['role_hint'],'overlaps':overlaps})
    return r|{'candidate_line_intersections':lines,'resolution':'candidate_intersections_only' if lines else 'unmapped'}


def geometry_replay():
    import pdfplumber
    cfg=read('experiments/kamri_block_audit_v28.json');saved=read('data/v28/pdf_geometry.json');rows=[]
    assert pdfplumber.__version__==saved['pdfplumber_version']==cfg['pdfplumber_version']
    for work in cfg['works']:
        with pdfplumber.open(ROOT/work['pdf']) as pdf:
            for number in work['pages']:
                page=pdf.pages[number-1]
                found=page.extract_words(x_tolerance=3,y_tolerance=3,use_text_flow=False,keep_blank_chars=False,extra_attrs=['size'],split_at_punctuation=False,expand_ligatures=False)
                words=[]
                for i,w in enumerate(found):
                    words.append({'word_index':i,'text':w['text'],'upright':bool(w.get('upright',True)),
                                  **{k:round(float(w[k]),6) for k in ['x0','x1','top','bottom','size']}})
                edges=[]
                for i,e in enumerate(page.edges):
                    if e.get('orientation')=='h':edges.append({'edge_index':i,**{k:round(float(e[k]),6) for k in ['x0','x1','top','bottom']}})
                sizes=Counter(round(float(c['size']),3) for c in page.chars if c['text'].strip())
                modal=sorted(sizes,key=lambda size:(sizes[size],size),reverse=True)[0]
                rows.append({'id':f'{work["id"]}:pdf:{number:03d}','work':work['id'],'pdf_page_one_based':number,
                             'width':round(float(page.width),6),'height':round(float(page.height),6),
                             'modal_font_size':modal,'words':words,'horizontal_edges':edges})
    assert saved['state']=='completed' and saved['pages']==rows and len(rows)==8
    print(json.dumps({'pdf_primitive_pages_verified':8,'words_verified':sum(len(p['words']) for p in rows)}))


def main():
    import bs4
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/kamri_block_audit_v28.json');pre=read('data/v28/preflight.json');bench=read('benchmarks/kamri_block_audit_v28.json')
    out=ROOT/'runs/000028_kamri_block_audit';manifest=check_hashes(out);report=read('runs/000028_kamri_block_audit/report.json')
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for p,h in hashes.items():assert sha((ROOT/p).read_bytes())==h,p
    assert bs4.__version__==cfg['beautifulsoup_version'] and unicodedata.unidata_version==cfg['unicode_version']
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']<manifest['finished_at_utc']
    assert [w['pages'] for w in cfg['works']]==[[90,91,92,93,94],[1,2,3]]
    assert (cfg['line_anchor_tolerance'],cfg['footnote_rule_min_top_fraction'],cfg['footnote_rule_min_width_fraction'],cfg['footnote_rule_max_left_fraction'],cfg['edge_merge_tolerance'],cfg['footnote_max_font_fraction'],cfg['upper_band_max_bottom_fraction'],cfg['large_font_min_fraction'])==(3,.55,.2,.35,1,.95,.08,1.15)
    raw_pages={p['id']:p for p in read('data/v27/page_views.json')['pages']};geometry=read('data/v28/pdf_geometry.json')
    assert geometry['state']=='completed' and len(geometry['pages'])==8
    fl={};exports={};legacy={}
    for w in cfg['works']:
        key=w['id'];exports[key]=(ROOT/w['fl_export']).read_text();legacy[key]=(ROOT/w['legacy_source']).read_text()
        fl[key]=reference_html((ROOT/w['archive_html']).read_bytes(),exports[key])
    pdf=[reference_page(p,raw_pages[p['id']]['text'],legacy[p['work']]) for p in geometry['pages']]
    assert read('runs/000028_kamri_block_audit/html_maps.json')==fl
    assert read('runs/000028_kamri_block_audit/pdf_maps.json')==pdf
    appendix=read('data/v26/evidence_spans.json');contexts=read('data/v27/frozen.json')['queries'];flrefs=[];srcrefs=[]
    for r in appendix['pairs']+appendix['unmatched_english_blocks']:
        ref={'reference_id':r['id'],'kind':'appendix_pair' if 'source_span' in r else 'reported_english_block','work':r['packet'],'span':r['fl_span']}
        flrefs.append(reference_fl_span(ref,fl[r['packet']],exports[r['packet']]))
        if 'source_span' in r:srcrefs.append(reference_source_span({'reference_id':r['id'],'work':r['packet'],'span':r['source_span'],'reported_pdf_page':r['pdf_page']},pdf,legacy[r['packet']]))
    for q in contexts:
        ref={'reference_id':'v27:'+q['id'],'kind':'v27_context','work':q['packet'],'span':{'start':q['fl_char_start'],'end':q['fl_char_end'],'text':q['text']}}
        flrefs.append(reference_fl_span(ref,fl[q['packet']],exports[q['packet']]))
    assert len(flrefs)==16 and len(srcrefs)==9
    assert read('runs/000028_kamri_block_audit/fl_references.json')==flrefs and read('runs/000028_kamri_block_audit/source_references.json')==srcrefs
    # Summaries are checked explicitly against the independently rebuilt maps.
    summary=read('runs/000028_kamri_block_audit/summary.json');assert report['summary']==summary
    for key,s in zip(fl,summary['fl'],strict=True):
        v=fl[key]
        assert s=={'work':key,'flat_code_points':len(v['flat_text']),'saved_export_code_points':len(exports[key]),'atoms':len(v['atoms']),
                   'block_runs':len(v['blocks']),'join_separators':len(v['joins']),'structural_roles':dict(Counter(b['role'] for b in v['blocks'])),
                   'link_only_runs':sum(b['link_only'] for b in v['blocks']),'explicit_quote_runs':sum(b['role']=='quotation_markup' for b in v['blocks']),
                   'zero_text_events':dict(Counter(e['tag'] for e in v['zero_text_events'])),'exact_reconstruction':True,'exact_partition':True}
    def covered(spans):
        # Interval endpoint sweep independently counts union lengths.
        events=[]
        for s in spans:events.extend([(s['start'],1),(s['end'],-1)])
        level=0;last=0;total=0
        for x,change in sorted(events):
            if level:total+=x-last
            level+=change;last=x
        return total
    for p,s in zip(pdf,summary['pdf_pages'],strict=True):
        assert s=={'page_id':p['page_id'],'lines':len(p['lines']),'words':sum(len(l['word_indices']) for l in p['lines']),
                   'role_hints':dict(Counter(l['role_hint'] for l in p['lines'])),'candidate_rules':len(p['candidate_rules']),
                   'raw_mapping_status':dict(Counter(l['raw_page_concordance']['status'] for l in p['lines'])),
                   'legacy_mapping_status':dict(Counter(l['legacy_window_concordance']['status'] for l in p['lines'])),
                   'raw_unique_mapped_span_code_points':covered([m for l in p['lines'] if l['raw_page_concordance']['status']=='unique' for m in l['raw_page_concordance']['matches']]),
                   'raw_any_mapped_span_code_points':covered([m for l in p['lines'] for m in l['raw_page_concordance']['matches']]),
                   'numeric_citation_occurrences':len(p['numeric_citations']),
                   'numeric_citation_occurrences_unrepresented_in_legacy':sum(not c['represented_in_legacy_form'] for c in p['numeric_citations'])}
    assert summary['fl_references_mapped']==16 and summary['source_references']==9
    assert summary['fl_references_crossing_block_runs']==sum(r['crosses_block_runs'] for r in flrefs)
    assert summary['source_references_without_line_candidates']==sum(not r['candidate_line_intersections'] for r in srcrefs)
    assert report['engineering_integrity']=={'two_exact_FL_reconstructions':True,'two_exact_FL_partitions':True,
                                            'all_eight_pages_mapped':True,'all_words_assigned_once':True,'all_reference_spans_valid':True}
    assert report['engineering_integrity_passed'] is True
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    for key in ['source_identities_admitted','semantic_labels_admitted','independent_reviews_admitted','untouched_test_units_admitted','new_network_requests']:assert report[key]==0,key
    assert report['model_executed'] is report['target_rescored'] is False and manifest['code_hashes']==pre['code_hashes']
    visual=read('data/v28/visual_review.json');assert visual['pages_reviewed']==8 and visual['independent_semantic_review'] is False
    assert visual['image_hashes']=={r['image']:r['image_sha256'] for r in raw_pages.values()}
    proc=subprocess.run([cfg['pdf_runtime'],str(Path(__file__).resolve()),'--geometry'],check=True,capture_output=True,text=True)
    primitives=json.loads(proc.stdout);preserved=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent!=out:check_hashes(path.parent);preserved.append(path.parent.name)
    assert len(preserved)==27
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha((ROOT/name).read_bytes())==h,name
    receipt={'state':'verified','run_manifest_sha256':sha((out/'manifest.json').read_bytes()),'FL_maps_verified':2,'PDF_pages_verified':8,
             'FL_references_verified':16,'source_reference_maps_verified':9,'PDF_primitives':primitives,'prior_runs_preserved':preserved,
             'semantic_labels_admitted':0,'scientific_acceptance':None}
    target=ROOT/'reports/000028_verification.json'
    if target.exists():
        old=json.loads(target.read_text());assert {k:v for k,v in old.items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--geometry']:geometry_replay()
    else:main()
