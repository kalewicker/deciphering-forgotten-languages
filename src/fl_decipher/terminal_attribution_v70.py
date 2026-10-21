"""Fixed two-block batch with per-block ledgers and deduplicated native slots."""
import hashlib
from fl_decipher.quotation_attribution_v69 import ledger,native_presence

IDS=(3,5)


def freeze_batch(inventory,export):
    selected=[]
    for bid in IDS:
        matches=[b for b in inventory['blocks'] if b['block_id']==bid]
        if len(matches)!=1:raise ValueError('requires one fixed block per ID')
        b=matches[0];a,z=b['body_span']
        if export['text'][a:z]!=b['text'] or len(b['text'].split())<24:raise ValueError('target binding or token count failed')
        words=b['text'].split();phrases=[' '.join(words[:12]),' '.join(words[-12:])]
        selected.append({'slot_id':f'b{bid:02d}','block_id':bid,'run_id':b['run_id'],'body_span':b['body_span'],'text':b['text'],
            'text_sha256':hashlib.sha256(b['text'].encode()).hexdigest(),'token_count':len(words),'phrases':phrases,
            'requests':[{'search_query':[{'q':'"'+q+'"'}],'response_length':'long'} for q in phrases]})
    return {'targets':selected,'selection_after_prior_exposure':True,
        'block_ledger':[{'block_id':b['block_id'],'run_id':b['run_id'],'body_span':b['body_span'],'selected':b['block_id'] in IDS,
            'reason':'fixed_next_exposed_English_block' if b['block_id'] in IDS else 'earlier_closed_E69_target' if b['block_id']==1 else 'not_registered_target'} for b in inventory['blocks']],
        'requests':[r for t in selected for r in t['requests']]}


def select_batch(responses,batch,known_urls,echo_title):
    slots=[];owners={}
    if len(responses)!=4:raise ValueError('exactly four response records required')
    for i,target in enumerate(batch['targets']):
        result=ledger(responses[i*2:i*2+2],target,known_urls,echo_title);chosen=result['selected'];owner=None
        if chosen:
            owner=owners.setdefault(chosen['url'],target['slot_id'])
        slots.append({'slot_id':target['slot_id'],'block_id':target['block_id'],'global_query_indices':[2*i,2*i+1],
            'ledger':result,'capture_owner_slot':owner,'reuses_capture':bool(owner and owner!=target['slot_id'])})
    return {'slots':slots,'native_slot_denominator':2,'unique_capture_urls':list(owners),'maximum_unique_captures':2}


def evaluate_slot(target,source,visual_ok=True):
    presence=native_presence(source['text'],target['text']) if source and source['representation_ready'] else None
    success=bool(presence and presence['complete_target_visible'] and presence['controls_passed'] and visual_ok)
    return {'slot_id':target['slot_id'],'block_id':target['block_id'],'source_available':bool(source and source['representation_ready']),
        'presence':presence,'pdf_visual_gate_passed':visual_ok if source and source.get('pages') else None,'complete_target_criterion_passed':success}


def terminal_decision(rows):
    if len(rows)!=2:raise ValueError('preserve the two-slot denominator')
    count=sum(r['complete_target_criterion_passed'] for r in rows)
    return {'native_complete_target_successes':count,'native_slot_denominator':2,
        'wording_discovery_route_closed':count==0,'outcome':'closed_feasibility_limited' if count==0 else 'bounded_native_quote_observed',
        'opaque_source_identity_or_meaning_admitted':False}
