"""Freeze the bounded acquisition failure as evidence, without invoking a model."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.natural_v12 import NOMINATIONS, opening, reference_gate, utc, validate_denominators
from fl_decipher.text import sentences

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def main():
    bp=ROOT/'benchmarks/kamri_natural_v12.json'
    if bp.exists():
        raise ValueError('Preserve existing acquisition freeze')
    cfg=read(ROOT/'experiments/kamri_natural_v12.json')
    assert cfg['nominations']==NOMINATIONS
    assert cfg['registration_sha256']==digest((ROOT/cfg['registration']).read_bytes())
    historical_paths=set()
    for p in (ROOT/'benchmarks').glob('kamri_*.json'):
        b=read(p)
        for info in b.get('documents',{}).values():
            if info['path'].startswith('data/normalized/'):
                historical_paths.add(info['path'])
    historical_paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'data/normalized').glob('*.json'))
    olddocs={p:read(ROOT/p) for p in sorted(historical_paths)}
    lexical_groups={g for item in read(ROOT/cfg['frozen_lexicon']).values() for c in item['candidates'] for g in c['independent_groups']}
    inputs={'azazel_opening.txt':'liber_azazel','vile_opening.txt':'vile_darkness'}
    documents={}; records=[]; novelty=[]
    for name,key in inputs.items():
        nomination=next(n for n in NOMINATIONS if n['id']==key)
        original=(ROOT/'data/v12/indexed'/name).read_text()
        text=opening(original,cfg['fl_word_cap'],numbered=key=='liber_azazel')
        receipt=snapshot(ROOT/'data/v12/raw',nomination['fl_url'],content=original.encode(),
                         acquisition_kind='indexed_web_excerpt',locator='Opening indexed Kamri text inspected 2026-10-01; imported selected units only; no raw/current HTTP claim')
        docid='fl_'+key+'_v12'; path=ROOT/'data/v12/normalized'/f'{docid}.json'
        if path.exists():raise ValueError(f'Preserve {path}')
        doc=normalized_document(docid,receipt,text,kind='fl',group=nomination['component'],
            transformations=['Exclude title/navigation/bibliography; collapse whitespace',
                             'Opening complete sentences up to 180 whitespace words; no backfill',
                             'Rejoin parser semicolon/colon atoms before full-stop selection',
                             'Remove leading numbered verse labels' if key=='liber_azazel' else 'No drop-cap repair'])
        dump_json(path,doc)
        documents[docid]={'path':str(path.relative_to(ROOT)),'sha256':digest(path.read_bytes()),'text_sha256':doc['text_sha256']}
        fi=[{'uid':key+f':{j:04d}','atom_index':i,'span':[t.start,t.end],'form':t.normalized}
            for j,(i,t) in enumerate((i,t) for i,a in enumerate(sentences(text)) for t in a.tokens)]
        roster=[x['uid'] for x in fi if x['form'] in ('warċa','mirnaķ','misndin')]
        exact_duplicates=[{'historical_document':p,'text':a.text} for p,d in olddocs.items() if d['kind']=='fl'
                          for a in sentences(text) if len(a.tokens)>=8 and a.text in {b.text for b in sentences(d['text'])}]
        titles=['liber azazel'] if key=='liber_azazel' else ['book of vile darkness','book of exalted deeds']
        mentions=[p for p,d in olddocs.items() if any(t in re.sub(r'\s+',' ',d['text']).lower() for t in titles)]
        novel=not mentions and not exact_duplicates and nomination['component'] not in lexical_groups
        novelty.append({'id':key,'component':nomination['component'],'historical_title_mentions':mentions,
                        'long_exact_fl_duplicates':exact_duplicates,'represented_in_lexicon_groups':nomination['component'] in lexical_groups,
                        'novel_in_declared_corpus':novel})
        gate=reference_gate(source_prose=False,authority_verified=False,extraction_reviewed=False,passage_reviewed=False,component_novel=novel)
        records.append(dict(nomination,fl_id=docid,fl_tokens=fi,roster_surface_uids=roster,
            fl_whitespace_words=len(text.split()),fl_atom_count=len(sentences(text)),
            acquisition_status='indexed_third_party_preview_only' if key=='liber_azazel' else 'catalogue_only_archive_dark',
            reason=('Nominated Scribd index exposes preview prose from Vex Nation with AI-enhanced title; no verified author/publisher copy. '
                    'The current raw Scribd response has no opening prose; nominated PDF is HTTP 404; source-site DNS failure repeats outside sandbox.' if key=='liber_azazel' else
                    'Open Library resolves the 2002 Monte Cook edition but exposes no chapter prose. Linked Internet Archive item metadata reports is_dark=true and exposes no files. '
                    'Unverified third-party uploads and the different 2011 edition are not substituted.'),
            gate=gate,references=None,lexical_accuracy=None,controls=None,semantic_gold=False))
    dump_json(ROOT/'benchmarks/inputs/natural_v12_novelty.json',{'lexicon_groups':sorted(lexical_groups),
        'historical_document_paths':sorted(historical_paths),'historical_source_groups':sorted({d['source_group'] for d in olddocs.values()}),
        'records':novelty,'limits':'Declared persisted corpus and long exact FL sentences only; no archive-wide fuzzy duplicate or unknown-source proof',
        'connected_component_rule':'Vile/Exalted books connected by public inventory entry 18; one selected representative, never count later linked articles as independent'})
    # Preserve the indexed source preview as a quarantined observation, never benchmark prose.
    preview=ROOT/'data/v12/indexed/azazel_source_preview.txt'
    receipt=snapshot(ROOT/'data/v12/raw','https://www.scribd.com/doc/47586429/Liber-Azazel',content=preview.read_bytes(),
        acquisition_kind='indexed_third_party_preview',locator='First three numbered units in cached public index; provenance unverified; not an admitted source packet')
    dump_json(ROOT/'data/v12/quarantined_preview.json',{'status':'quarantined_unverified_provenance','receipt':receipt,'source_scope_complete':False,'reference_eligible':False,'used_for_predictions':False})
    receipts=[read(p) for p in sorted((ROOT/'data/v12/acquisition').glob('*/receipt.json'))]
    first=min(x['started_at_utc'] for x in receipts)
    assert cfg['registration_file_mtime_utc']<first
    assert len({x['requested_url'] for x in receipts if x['requested_url'] in NOMINATIONS[0]['source_routes']})==3
    assert len({x['requested_url'] for x in receipts if x['requested_url'] in NOMINATIONS[1]['source_routes']})==2
    ledger={'experiment_id':'kamri_natural_v12','stage':'acquisition_eligibility','status':'completed_no_reference_eligible_pairs',
            'selected_works':2,'selected_queries':2,'selected_components':2,'fl_indexed_queries_acquired':2,'fl_raw_queries_acquired':0,
            'admissible_source_packets':0,'quarantined_indexed_previews':1,'reference_eligible_queries':0,'evaluated_queries':0,
            'model_executed':False,'metrics':None,'new_supported_lexical_entries':0,'records':records,
            'source_attempt_receipts':[str(p.relative_to(ROOT)) for p in sorted((ROOT/'data/v12/acquisition').glob('*/receipt.json'))],
            'distinct_direct_source_routes':5,'raw_requests':6,
            'sandbox_retry':'Same theisticsatanism.com URL rerun outside sandbox after curl DNS failure, unchanged failure; no new discovery route or source replacement',
            'registration_sha256':cfg['registration_sha256'],'registration_before_raw_attempts':True,
            'acquisition_first_attempt_at_utc':first,'references_sealed_at_utc':utc(),
            'historical_unavailable_altruist':'Unchanged experiment-5 selected denominator and archive; no retry in v12'}
    validate_denominators(ledger)
    dump_json(ROOT/'benchmarks/inputs/natural_v12_acquisition.json',ledger)
    paths=[str(p.relative_to(ROOT)) for p in (ROOT/'data/v12').rglob('*') if p.is_file()]
    paths+=['experiments/kamri_natural_v12.md','experiments/kamri_natural_v12.json','benchmarks/inputs/natural_v12_acquisition.json',
            'benchmarks/inputs/natural_v12_novelty.json',cfg['frozen_lexicon'],'experiments/kamri_conflict_v11.json','pyproject.toml','uv.lock']
    dump_json(bp,{'schema_version':12,'status':'frozen_acquisition_eligibility_result','selected_work_denominator':2,'selected_query_denominator':2,
                  'reference_eligible_queries':0,'model_executed':False,'documents':documents,'ledger':'benchmarks/inputs/natural_v12_acquisition.json',
                  'input_hashes':{p:digest((ROOT/p).read_bytes()) for p in sorted(set(paths))}})
    print('Frozen 2 selected packets, 2 indexed FL excerpts, 0 eligible English/reference packets; no model executed.')


if __name__=='__main__':
    main()
