"""Exact, unit-aware diagnostics for frozen positional hypotheses, not meanings."""
from collections import Counter,defaultdict
from fractions import Fraction
from itertools import combinations
import random


def rational(value):
    return None if value is None else {'numerator':value.numerator,'denominator':value.denominator,'value':float(value)}


def observations(ledger):
    rows=[]
    for unit in ledger:
        for h in unit['positional_hypotheses']:
            rows.append({'uid':f"{unit['uid']}:t{h['index']:03d}",'unit_uid':unit['uid'],'component':unit['component'],
                'index':h['index'],'fl_form':h['fl_form'],'english_form':h['english_form'],
                'fl_surface':h['fl_surface'],'english_surface':h['english_surface'],
                'fl_span':h['fl_span'],'english_span':h['english_span'],
                'status':'frozen unvalidated positional hypothesis'})
    return rows


def group_forms(rows):
    groups=defaultdict(list)
    for row in rows:groups[row['fl_form']].append(row)
    return groups


def measure(rows,scope='global'):
    if scope not in ('global','within_component','between_components'):
        raise ValueError(scope)
    total=Fraction(0);form_count=unit_pairs=occurrence_pairs=equal_pairs=0
    for group in group_forms(rows).values():
        units=defaultdict(list)
        for row in group:units[row['unit_uid']].append(row)
        values=[]
        for a,b in combinations(sorted(units),2):
            same=units[a][0]['component']==units[b][0]['component']
            if scope=='within_component' and not same:continue
            if scope=='between_components' and same:continue
            ca=Counter(x['english_form'] for x in units[a]);cb=Counter(x['english_form'] for x in units[b])
            den=sum(ca.values())*sum(cb.values());num=sum(n*cb[e] for e,n in ca.items())
            values.append(Fraction(num,den));unit_pairs+=1;occurrence_pairs+=den;equal_pairs+=num
        if values:total+=sum(values,Fraction(0))/len(values);form_count+=1
    return {'scope':scope,'eligible_forms':form_count,'distinct_unit_pairs':unit_pairs,
        'occurrence_pairs':occurrence_pairs,'equal_occurrence_pairs':equal_pairs,
        'macro_form_cross_unit_agreement':rational(total/form_count if form_count else None),
        'occurrence_weighted_agreement':rational(Fraction(equal_pairs,occurrence_pairs) if occurrence_pairs else None)}


def form_ledger(rows):
    result=[]
    for form,group in sorted(group_forms(rows).items()):
        units=sorted({x['unit_uid'] for x in group});components=sorted({x['component'] for x in group})
        counts=Counter(x['english_form'] for x in group);by_component={}
        for component in components:
            subset=[x for x in group if x['component']==component]
            by_component[component]={'units':sorted({x['unit_uid'] for x in subset}),
                'english_counts':dict(sorted(Counter(x['english_form'] for x in subset).items())),
                'occurrences':len(subset)}
        repeated=len(units)>=2;strict=repeated and len(counts)==1
        lead=len(components)>=2 and len(counts)==1 and all(len(x['units'])>=2 for x in by_component.values())
        result.append({'fl_form':form,'occurrences':len(group),'unit_uids':units,'components':components,
            'english_counts':dict(sorted(counts.items())),'occurrence_uids':[x['uid'] for x in group],
            'english_outcomes':len(counts),'cross_unit_repeated':repeated,
            'within_unit_repetition_only':len(group)>1 and not repeated,
            'strict_global_positional_consistency':strict,'conflicting_repeated_form':repeated and len(counts)>1,
            'cross_component_review_lead':lead,'by_component':by_component,
            'semantic_training_eligible':False,'untouched_test_eligible':False,
            'agreement':measure(group)['macro_form_cross_unit_agreement']})
    return result


def summary(rows):
    registry=form_ledger(rows)
    strict={c:sum(len(r['by_component'].get(c,{}).get('units',[]))>=2 and
                  len(r['by_component'][c]['english_counts'])==1 for r in registry if c in r['by_component'])
            for c in sorted({x['component'] for x in rows})}
    return {'occurrences':len(rows),'units':len({x['unit_uid'] for x in rows}),
        'components':len({x['component'] for x in rows}),'form_types':len(registry),
        'cross_unit_repeated_types':sum(r['cross_unit_repeated'] for r in registry),
        'within_unit_repetition_only_types':sum(r['within_unit_repetition_only'] for r in registry),
        'strict_global_types':sum(r['strict_global_positional_consistency'] for r in registry),
        'conflicting_repeated_types':sum(r['conflicting_repeated_form'] for r in registry),
        'cross_component_types':sum(len(r['components'])>=2 for r in registry),
        'cross_component_review_leads':sum(r['cross_component_review_lead'] for r in registry),
        'strict_types_by_component':strict,
        'global':measure(rows),'within_component':measure(rows,'within_component'),
        'between_components':measure(rows,'between_components')}


def units_by_uid(rows):
    units=defaultdict(list)
    for row in rows:units[row['unit_uid']].append(row)
    for uid,unit in units.items():
        unit.sort(key=lambda r:r['index'])
        assert [x['index'] for x in unit]==list(range(len(unit))),uid
    return dict(sorted(units.items()))


def apply_orders(rows,orders,source_units=None):
    units=units_by_uid(rows);source_units=source_units or {}
    assert set(orders)==set(units)
    result=[]
    for uid,unit in units.items():
        source=source_units.get(uid,uid);english=units[source];order=orders[uid]
        assert len(unit)==len(english) and sorted(order)==list(range(len(unit)))
        for row,j in zip(unit,order,strict=True):
            candidate=english[j]
            result.append(row|{'english_form':candidate['english_form'],'english_surface':candidate['english_surface'],
                'english_span':candidate['english_span'],'english_origin_unit':source,'english_origin_index':j})
    return result


def control_orders(rows,kind,swap):
    units=units_by_uid(rows);orders={};source_units={}
    for uid,unit in units.items():
        order=list(range(len(unit)))
        if kind.startswith('rotate_'):
            k=int(kind.split('_')[1])%len(order);order=order[-k:]+order[:-k] if k else order
        elif kind=='reverse':order.reverse()
        elif kind=='length_matched_swap':
            if uid in swap:source_units[uid]=next(x for x in swap if x!=uid)
        else:raise ValueError(kind)
        orders[uid]=order
    if kind=='length_matched_swap':
        equal_pairs=[(a,b) for a,b in combinations(units,2) if len(units[a])==len(units[b])]
        assert equal_pairs==[tuple(swap)]
    return orders,source_units


def permutation_orders(rows,seed,count):
    rng=random.Random(seed);units=units_by_uid(rows)
    for number in range(count):
        orders={}
        for uid,unit in units.items():
            order=list(range(len(unit)));rng.shuffle(order);orders[uid]=order
        yield number,orders


def primary_fraction(metrics):
    ratio=metrics['global']['macro_form_cross_unit_agreement']
    return None if ratio is None else Fraction(ratio['numerator'],ratio['denominator'])
