"""Panel accounting around the unchanged E93 comparator."""
from fl_decipher.yid_native_v93 import assess

def panel(documents,slots,read_bytes):
    assert len(documents)==len(slots)==2
    assert [d['number'] for d in documents]==[43,86]
    assert {s['number'] for s in slots}=={43,86}
    assert all(s['status'] in ('supplied','unavailable') for s in slots), 'pending slots cannot run'
    results=[];rows=[]
    for d in documents:
        slot=next(s for s in slots if s['number']==d['number'])
        assert len(d['targets'])==d['denominator']
        if slot['status']=='unavailable':
            r={'admissible':False,'reasons':['reported_acquisition_unavailable'],'comparison':None}
        else:
            r=assess(read_bytes(slot['main_path']),d['requested_url'],slot['requested_url'],slot['final_url'],[t['text'] for t in d['targets']])
        results.append({'number':d['number'],'result':r})
        rows.append({'number':d['number'],'denominator':d['denominator'],'admissible':r['admissible'],'reasons':r['reasons'],
                     'counts':{k:{key:v[key] for key in ['matched','ordered_matched']} for k,v in r['comparison'].items()} if r['comparison'] is not None else None})
    total=sum(d['denominator'] for d in documents);available=sum(r['denominator'] for r in rows if r['admissible'])
    return {'results':results,'report':{'posts':rows,'fixed_posts':2,'fixed_targets':total,'compared_posts':sum(r['admissible'] for r in rows),'compared_targets':available,'unavailable_targets':total-available,'network_requests':0,'new_confirmation_units':0,'semantic_benchmark_qualifying_works':0}}
