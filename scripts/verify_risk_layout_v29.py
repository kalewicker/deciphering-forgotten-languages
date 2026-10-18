"""Independent glyph/raster replay and derivative accounting; no primary imports."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,statistics,subprocess,sys,unicodedata

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def reference_raster(gray,w,h,pw,ph):
    candidates=[]
    for y in range(h):
        if y < (55*h+99)//100:continue
        row=bytes(int(v<=128) for v in gray[y*w:(y+1)*w])
        for match in re.finditer(b'\x01+',row):
            if match.end()-match.start()>=.2*w and match.start()<=.35*w:
                candidates.append({'y':y,'x0':match.start(),'x1':match.end()})
    merged=[]
    for c in candidates:
        for g in merged:
            if c['y']-g[-1]['y']<=2 and abs(c['x0']-g[0]['x0'])<=2 and abs(c['x1']-g[0]['x1'])<=2:
                g.append(c);break
        else:merged.append([c])
    rows=[]
    for g in merged:
        x0=min(c['x0'] for c in g);x1=max(c['x1'] for c in g);y0=g[0]['y'];y1=g[-1]['y']+1
        rows.append({'pixel_runs':g,'pixel_box':[x0,y0,x1,y1],'x0':round(x0/w*pw,6),'x1':round(x1/w*pw,6),
                     'top':round(y0/h*ph,6),'bottom':round(y1/h*ph,6)})
    return rows


def reference_tokens(s):
    starts=[];ends=[];active=False
    for i in range(len(s)):
        keep=s[i].isalnum() or unicodedata.category(s[i])[0]=='M'
        if keep and not active:starts.append(i)
        if active and not keep:ends.append(i)
        active=keep
    if active:ends.append(len(s))
    return [(unicodedata.normalize('NFC',s[a:b]).casefold(),a,b) for a,b in zip(starts,ends,strict=True)]


def reference_concordance(q,t):
    a=reference_tokens(q);b=reference_tokens(t);forms=tuple(v[0] for v in a);hits=[]
    for j in range(len(b)):
        if forms and tuple(v[0] for v in b[j:j+len(a)])==forms:
            start,end=b[j][1],b[j+len(a)-1][2]
            hits.append({'start':start,'end':end,'text':t[start:end]})
    return {'status':{0:'unmapped',1:'unique'}.get(len(hits),'ambiguous'),'matches':hits}


def reference_citations(s):
    rows=[]
    for m in re.finditer(r'\[\s*\d+(?:\s*,\s*\d+)*\s*\]',s):
        rows.append({'start':m.start(),'end':m.end(),'text':s[m.start():m.end()],'key':''.join(m.group().split())})
    return rows


def reference_groups(page):
    chars=page['chars'];h=page['height'];dirs=[];bases=[];ems=[]
    for c in chars:
        m=tuple(c['matrix'][:4]);d={(1.,0.,0.,1.):'upright',(0.,1.,-1.,0.):'quarter_turn'}.get(m,'unknown')
        dirs.append(d);bases.append(round(h-c['matrix'][5],6) if d=='upright' else c['matrix'][4])
        ems.append(round(c['x1']-c['x0'],6) if d=='quarter_turn' else c['size'])
    initial=[]
    for direction in ['upright','quarter_turn']:
        remaining=sorted([i for i,d in enumerate(dirs) if d==direction],key=lambda i:(bases[i],i))
        while remaining:
            anchor=bases[remaining[0]];stop=1
            while stop<len(remaining) and bases[remaining[stop]]<=anchor+2:stop+=1
            initial.append((direction,anchor,remaining[:stop]));remaining=remaining[stop:]
    initial.extend(('unknown',bases[i],[i]) for i,d in enumerate(dirs) if d=='unknown')
    med=[statistics.median(ems[i] for i in g[2]) for g in initial]
    graph={i:[] for i in range(len(initial))}
    for i,(d,b,_) in enumerate(initial):
        for j,(e,c,_) in enumerate(initial):
            if i!=j and d==e=='upright' and med[i]<=med[j]*.8 and b<=c<=b+6:graph[i].append(j)
    moves={}
    for i in graph:
        eligible=[j for j in graph[i] if len(graph[j])==0]
        if eligible:moves[i]=sorted(eligible,key=lambda j:(initial[j][1]-initial[i][1],min(initial[j][2])))[0]
    attachments=[{'from_group':i,'to_group':j,'char_indices':initial[i][2],
                  'from_baseline':initial[i][1],'to_baseline':initial[j][1]} for i,j in moves.items()]
    groups=[]
    for i,(d,b,indices) in enumerate(initial):
        if i in moves:continue
        ids=indices+[c for j,t in moves.items() if t==i for c in initial[j][2]]
        ids=sorted(ids,key=lambda k:((chars[k]['x0'] if d=='upright' else -chars[k]['bottom']) if d!='unknown' else k,k))
        groups.append({'orientation':d,'baseline':b,'original_group':i,'indices':ids})
    groups.sort(key=lambda g:({'upright':0,'quarter_turn':1,'unknown':2}[g['orientation']],g['baseline'],min(g['indices'])))
    return groups,attachments,ems


def verify_page(source,saved,raw,legacy):
    groups,attachments,ems=reference_groups(source);chars=source['chars']
    assert saved['attachments']==attachments and len(saved['lines'])==len(groups)
    native=''.join(c['text'] for c in chars);assert saved['native_glyph_text']==native
    native_cursor=0
    for i,c in enumerate(chars):
        assert c['index']==i and c['native_start']==native_cursor
        native_cursor+=len(c['text']);assert c['native_end']==native_cursor
    pieces=[];fragments=[];offset=0;membership=[]
    frequencies=Counter(round(ems[i],3) for i,c in enumerate(chars) if c['text'].strip() and tuple(c['matrix'][:4])==(1.,0.,0.,1.))
    modal=sorted(frequencies,key=lambda k:(frequencies[k],k))[-1];assert saved['modal_em']==modal
    rule=sorted(source['raster_rules'],key=lambda r:(r['top'],r['x0']))[0] if source['raster_rules'] else None
    assert saved['selected_rule']==rule and saved['raster_rules']==source['raster_rules']
    for num,(group,line) in enumerate(zip(groups,saved['lines'],strict=True)):
        ids=group['indices'];direction=group['orientation'];lid=source['id']+f':line:{num:03d}';start=offset;line_text=''
        for position,i in enumerate(ids):
            c=chars[i]
            if position:
                j=ids[position-1];previous=chars[j]
                gap=c['x0']-previous['x1'] if direction=='upright' else previous['top']-c['bottom'] if direction=='quarter_turn' else 0
                has_space=(bool(previous['text']) and previous['text'][-1].isspace()) or (bool(c['text']) and c['text'][0].isspace())
                if gap>.15*min(ems[j],ems[i]) and not has_space:
                    pieces.append({'kind':'inferred_space','start':offset,'end':offset+1,'text':' ','line_id':lid,'left_char':j,'right_char':i,'gap':round(gap,6),'reason':'geometric_gap'})
                    offset+=1;line_text+=' '
            pieces.append({'kind':'glyph','start':offset,'end':offset+len(c['text']),'text':c['text'],'line_id':lid,
                           'char_index':i,'native_start':c['native_start'],'native_end':c['native_end']})
            offset+=len(c['text']);line_text+=c['text'];membership.append(i)
        top=min(chars[i]['top'] for i in ids);bottom=max(chars[i]['bottom'] for i in ids);size=statistics.median(ems[i] for i in ids)
        hint='body_or_unresolved'
        if direction=='quarter_turn':hint='rotated_margin_candidate'
        elif direction=='unknown':hint='orientation_unresolved'
        elif re.fullmatch(r'\d{1,4}',line_text.strip()) and top>=source['height']*.85:hint='page_number_candidate'
        elif rule is not None and top>rule['top']:hint='footnote_candidate' if size<=modal*.95 else 'below_rule_unresolved'
        elif bottom<=source['height']*.15:hint='upper_band_candidate'
        expected={'line_id':lid,'orientation':direction,'baseline':group['baseline'],'original_group':group['original_group'],'char_indices':ids,
                  'start':start,'end':offset,'text':line_text,'x0':min(chars[i]['x0'] for i in ids),'x1':max(chars[i]['x1'] for i in ids),
                  'top':top,'bottom':bottom,'median_em':size,'role_hint':hint,
                  'raw_page_concordance':reference_concordance(line_text,raw),'legacy_window_concordance':reference_concordance(line_text,legacy)}
        assert line==expected,(lid,'line differs')
        pieces.append({'kind':'line_separator','start':offset,'end':offset+1,'text':'\n','line_id':lid,'reason':'synthetic_line_ending'})
        offset+=1;fragments.append(line_text+'\n')
    assert sorted(membership)==list(range(len(chars))) and saved['pieces']==pieces and saved['text']==''.join(fragments)
    cursor=0
    for piece in saved['pieces']:
        assert piece['start']==cursor and saved['text'][cursor:piece['end']]==piece['text'];cursor=piece['end']
    assert cursor==len(saved['text']) and saved['exact_native_accounting'] is saved['exact_derivative_partition'] is True
    assert saved['raw_numeric_citations']==reference_citations(raw) and saved['derivative_numeric_citations']==reference_citations(saved['text'])
    assert saved['page_id']==source['id'] and saved['pdf_page_one_based']==source['pdf_page_one_based']
    return True


def reference_continuities(pages):
    rows=[]
    for i in range(len(pages)-1):
        a=[l for l in pages[i]['lines'] if l['role_hint']=='body_or_unresolved']
        b=[l for l in pages[i+1]['lines'] if l['role_hint']=='body_or_unresolved']
        l=a[-1] if a else None;r=b[0] if b else None
        lm=re.search(r'([^\W\d_]+)-\s*$',l['text']) if l else None;rm=re.match(r'\s*([^\W\d_]+)',r['text']) if r else None
        rows.append({'left_page':pages[i]['pdf_page_one_based'],'right_page':pages[i+1]['pdf_page_one_based'],
                     'left_line':l,'right_line':r,'continuation_candidate':bool(lm and rm and rm.group(1)[0].islower()),
                     'left_fragment':lm.group(1)+'-' if lm else None,'right_fragment':rm.group(1) if rm else None,'joined_text_created':False})
    return rows


def primitive_replay():
    import pdfplumber,PIL
    from PIL import Image
    cfg=read('experiments/risk_layout_derivative_v29.json');saved=read('data/v29/primitives.json');pages=[]
    assert (pdfplumber.__version__,PIL.__version__)==(cfg['pdfplumber_version'],cfg['pillow_version'])
    with pdfplumber.open(ROOT/cfg['pdf']) as doc:
        for spec in cfg['pages']:
            page=doc.pages[spec['pdf_page_one_based']-1];chars=[];offset=0
            for i,c in enumerate(page.chars):
                row={'index':i,'text':c['text'],'native_start':offset,'native_end':offset+len(c['text']),
                     'matrix':list(map(lambda x:round(float(x),6),c['matrix'])),'fontname':c['fontname'],'upright':bool(c['upright'])}
                row.update({k:round(float(c[k]),6) for k in ['x0','x1','top','bottom','size']});chars.append(row);offset=row['native_end']
            with Image.open(ROOT/spec['image']) as image:
                gray=image.convert('L');w,h=gray.size;rules=reference_raster(gray.tobytes(),w,h,float(page.width),float(page.height))
            pages.append({'id':spec['id'],'pdf_page_one_based':spec['pdf_page_one_based'],'width':float(page.width),'height':float(page.height),
                          'image':spec['image'],'image_width':w,'image_height':h,'chars':chars,'raster_rules':rules})
    assert saved['state']=='completed' and saved['pages']==pages
    print(json.dumps({'pages':len(pages),'glyphs':sum(len(p['chars']) for p in pages),'raster_rules':sum(len(p['raster_rules']) for p in pages)}))


def main():
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/risk_layout_derivative_v29.json');pre=read('data/v29/preflight.json');bench=read('benchmarks/risk_layout_derivative_v29.json')
    out=ROOT/'runs/000029_risk_layout_derivative';manifest=check_hashes(out)
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for name,h in hashes.items():assert sha(name)==h,name
    assert cfg['parameters']=={'dark_threshold':128,'rule_min_top_fraction':.55,'rule_min_width_fraction':.2,'rule_max_left_fraction':.35,'pixel_merge_tolerance':2,'baseline_tolerance':2,'satellite_font_fraction':.8,'satellite_max_baseline_distance':6,'gap_em_fraction':.15,'footnote_font_fraction':.95,'upper_band_fraction':.15,'page_number_top_fraction':.85}
    assert [p['pdf_page_one_based'] for p in cfg['pages']]==[1,2,3] and cfg['page_denominator']==3
    primitive=read('data/v29/primitives.json');pages=read('runs/000029_risk_layout_derivative/pages.json');report=read('runs/000029_risk_layout_derivative/report.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<primitive['extracted_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']<manifest['finished_at_utc']
    assert len(pages)==len(primitive['pages'])==3 and manifest['code_hashes']==pre['code_hashes']
    raw={p['id']:p for p in read('data/v27/page_views.json')['pages']};legacy=(ROOT/cfg['legacy_source']).read_text()
    expected_summary=[]
    for source,p in zip(primitive['pages'],pages,strict=True):
        verify_page(source,p,raw[source['id']]['text'],legacy)
        assert (out/f"risk_math_{p['pdf_page_one_based']:03d}.txt").read_text()==p['text']
        expected_summary.append({'page_id':p['page_id'],'glyphs':len(source['chars']),'native_code_points':len(p['native_glyph_text']),
                                 'derivative_code_points':len(p['text']),'lines':len(p['lines']),'inferred_spaces':sum(v['kind']=='inferred_space' for v in p['pieces']),
                                 'role_hints':dict(Counter(l['role_hint'] for l in p['lines'])),'raster_rule_candidates':len(p['raster_rules']),
                                 'raw_mapping_status':dict(Counter(l['raw_page_concordance']['status'] for l in p['lines'])),
                                 'legacy_mapping_status':dict(Counter(l['legacy_window_concordance']['status'] for l in p['lines'])),
                                 'raw_citation_keys':dict(Counter(c['key'] for c in p['raw_numeric_citations'])),
                                 'derivative_citation_keys':dict(Counter(c['key'] for c in p['derivative_numeric_citations']))})
    assert report['summary']==expected_summary
    assert report['v28_descriptive_baseline']==[p for p in read('runs/000028_kamri_block_audit/summary.json')['pdf_pages'] if p['page_id'].startswith('risk_math:')]
    continuity=reference_continuities(pages);assert read('runs/000029_risk_layout_derivative/continuities.json')==continuity
    gate={'complete_glyph_and_piece_accounting':True,'single_rotated_lane':[sum(l['orientation']=='quarter_turn' for l in p['lines']) for p in pages]==[1,0,0],
          'two_note_regions':pages[0]['selected_rule'] is None and all(p['selected_rule'] is not None and any(l['role_hint']=='footnote_candidate' for l in p['lines']) for p in pages[1:]),
          'unjoined_page_edge':any(r['left_page']==2 and r['right_page']==3 and r['continuation_candidate'] and r['left_fragment']=='as-' and r['right_fragment']=='tronomy' for r in continuity)}
    assert report['engineering_components']==gate and report['automatic_engineering_gate_passed']==all(gate.values())
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    for key in ['semantic_labels_admitted','source_identities_admitted','independent_reviews_admitted','untouched_test_units_admitted','new_network_requests']:assert report[key]==0
    assert report['model_executed'] is report['target_rescored'] is False and report['visual_QA_required'] is True
    visual=read('data/v29/visual_review.json');assert visual['pages_reviewed']==3 and visual['independent_semantic_review'] is False
    assert visual['image_hashes']=={p['image']:p['image_sha256'] for p in cfg['pages']}
    assert manifest['finished_at_utc']<visual['reviewed_at_utc']
    proc=subprocess.run([cfg['pdf_runtime'],str(Path(__file__).resolve()),'--primitives'],check=True,capture_output=True,text=True)
    primitives=json.loads(proc.stdout);preserved=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent!=out:check_hashes(path.parent);preserved.append(path.parent.name)
    assert len(preserved)==28
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    receipt={'state':'verified','run_manifest_sha256':sha('runs/000029_risk_layout_derivative/manifest.json'),
             'pages_verified':3,'primitives_verified':primitives,'engineering_components':gate,
             'engineering_gate_passed':all(gate.values()) and visual['engineering_layout_expectations_confirmed'],
             'visual_receipt_sha256':sha('data/v29/visual_review.json'),'prior_runs_preserved':preserved,
             'semantic_labels_admitted':0,'scientific_acceptance':None}
    target=ROOT/'reports/000029_verification.json'
    if target.exists():assert {k:v for k,v in json.loads(target.read_text()).items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--primitives']:primitive_replay()
    else:main()
