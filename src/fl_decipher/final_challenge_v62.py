"""Final fixed search-cohort challenge; no replacement discovery or threshold tuning."""
from collections import Counter
from fl_decipher.additional_intake_v55 import alias_plan
from fl_decipher.publisher_intake_v50 import topical
from fl_decipher.panel_scaffold_v56 import assessment


def nominate(attribution):
    prior=attribution['exposure_registry']; seen=set(); rows=[]; selected=[]
    for card in attribution['cards']:
        key=card['strict_article_key']; duplicate=key is not None and key in seen
        if key:seen.add(key)
        topic=topical((card['title'] or '')+'\n'+' '.join(r['text'] for r in card['snippets']))
        reason=('unattributed_card' if not card['structurally_attributed'] else 'invalid_article_url' if not card['strict_url_usable'] else
                'duplicate_returned_url' if duplicate else 'previously_captured_url' if key in prior['captured_article_keys'] else
                'topic_terms_missing' if not topic else 'slot_cap' if len(selected)==2 else 'selected_first_eligible')
        row={'card_index':card['card_index'],'url':card['resolved_url'],'title':card['title'],'article_key':key,
             'prior_exposure_tags':prior['article_exposures'].get(key,[]),'topical':topic,'decision_reason':reason,'nominated':reason=='selected_first_eligible'}
        rows.append(row)
        if row['nominated']:selected.append(row)
    return {'card_denominator':len(rows),'cards':rows,'occupied_slots':len(selected),
            'slots':[{'slot_id':f's{i:02d}','nominee':selected[i] if i<len(selected) else None} for i in range(2)]}


def conditional_alias(raw,receipt,spec,preliminary):
    observed=alias_plan(raw,receipt,spec)
    other_pass=all(v for k,v in preliminary['checks'].items() if k!='all_og_urls_bound')
    permitted=observed['request_url'] is not None and other_pass
    return {'observed_alias_plan':observed,'all_other_native_checks_pass':other_pass,
            'request_url':observed['request_url'] if permitted else None,
            'reason':'sole_unbound_og_url_can_be_checked' if permitted else 'no_alias_needed_or_other_native_gate_failed'}


def capacity(native,rep,target,budget=11,minimum=6):
    if budget!=11 or minimum!=6:raise ValueError('fixed eleven-anchor windows and six capacity')
    result={'status':'not_evaluated_native_ineligible','numeric_representation_available':None,'numeric_anchor_count':None,
        'numeric_budget':budget,'minimum_window_bag_capacity':minimum,'windows':None,'maximum_window_bag_capacity':None,
        'meets_capacity_requirement':None,'qualifying_comparator':False}
    if not native['development_capture_eligible']:return result
    result['numeric_representation_available']=rep is not None and rep['available']
    if not result['numeric_representation_available']:
        result.update(status='representation_unavailable',meets_capacity_requirement=False);return result
    source=[r for r in rep['inventory']['anchors'] if r['kind']=='number'];left=Counter(r['key'] for r in target if r['kind']=='number')
    n=len(source);width=min(n,budget);windows=[]
    for start in range(n-width+1):
        part=source[start:start+width];right=Counter(r['key'] for r in part)
        windows.append({'numeric_span':[start,start+width],'anchor_indices':[r['anchor_index'] for r in part],
                        'bag_capacity':sum((left&right).values())})
    maximum=max(w['bag_capacity'] for w in windows)
    result.update(status='evaluated',numeric_anchor_count=n,windows=windows,maximum_window_bag_capacity=maximum,
                  meets_capacity_requirement=maximum>=minimum,qualifying_comparator=maximum>=minimum)
    return result


def compare(target,rep,screen,cfg):
    if not screen['qualifying_comparator']:return None
    scored=assessment(target,rep,cfg)
    value=scored['observed']['capped_scan']['maximum_lcs']
    return {'assessment':scored,'reference_score_unchanged':6,
        'reference_strictly_exceeds_candidate':6>value if scored['functional_checks_passed'] else None,
        'candidate_ties_reference':value==6 if scored['functional_checks_passed'] else None,
        'candidate_exceeds_reference':value>6 if scored['functional_checks_passed'] else None}


def closeout(slots):
    if len(slots)!=2:raise ValueError('retain both registered slots')
    capable=[s for s in slots if s['capacity']['qualifying_comparator']];compared=[s for s in capable if s['comparison'] is not None]
    functional=bool(compared) and len(compared)==len(capable) and all(s['comparison']['assessment']['functional_checks_passed'] for s in compared)
    return {'experiment_id':'final_challenge_v62','nomination_slot_denominator':2,'occupied_slots':sum(s['occupied'] for s in slots),
        'empty_slots':sum(not s['occupied'] for s in slots),'native_eligible_candidates':sum(s['native_eligible'] for s in slots),
        'capacity_screens_evaluated':sum(s['capacity']['status']=='evaluated' for s in slots),'qualifying_comparators':len(capable),
        'registered_feasibility_gate':bool(capable),'both_slots_qualified':len(capable)==2,'comparisons_evaluated':len(compared),
        'reference_specificity_gate_among_capable':all(s['comparison']['reference_strictly_exceeds_candidate'] for s in compared) if functional else None,
        'closure':'closed_after_fixed_comparison' if capable else 'closed_feasibility_limited',
        'discovery_route_closed':True,'additional_batches_authorized':0,'new_search_requests':0,'pagination_requests':0,
        'source_identities_admitted':0,'opaque_meanings_admitted':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'previous_results_preserved':True}
