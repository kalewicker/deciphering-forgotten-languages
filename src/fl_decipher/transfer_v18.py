"""Frozen positional lookup and fail-closed development transfer accounting."""
from fractions import Fraction
from .text import tokens

def ratio(a,b):
    if not b:return None
    f=Fraction(a,b);return {'numerator':f.numerator,'denominator':f.denominator,'value':float(f)}

def predict(target,candidates):
    conflicts={f['fl_form'] for f in candidates['conflicted_forms']}
    rows=[]
    for i,t in enumerate(tokens(target['fl'])):
        predictions={}
        for name in ('primary','secondary'):
            item=candidates[name].get(t.normalized)
            predictions[name]={'form':item['paired_english_form'] if item else None,
                'abstention_reason':None if item else 'conflicted_training_form' if t.normalized in conflicts else 'outside_frozen_candidate_set'}
        rows.append({'uid':target['uid']+f':t{i:03d}','index':i,'fl_form':t.normalized,
            'fl_surface':t.surface,'fl_span':[t.start,t.end],**predictions})
    return {'uid':target['uid'],'component':target['component'],'tokens':rows,'token_denominator':len(rows)}

def reference_gate(*,source_authority,source_statement_complete,source_continuation_orderly,
                   historical_fl_unique_complete,equal_token_counts):
    requirements=locals();assert all(type(x) is bool for x in requirements.values())
    return {'development_positional_score_eligible':all(requirements.values()),
        'requirements':requirements,'unmet':[k for k,v in requirements.items() if not v],
        'semantic_training_eligible':False,'untouched_test_eligible':False}

def evaluate(predictions,references,orders=None):
    refs={r['uid']:r for r in references};rows=[];unit_out=[]
    stats={name:{'all_tokens':0,'predictions':0,'abstentions':0,'evaluated_predictions':0,
        'verified_positional_matches':0,'positional_conflicts':0,'unscoreable_predictions':0} for name in ('primary','secondary')}
    for unit in predictions:
        ref=refs[unit['uid']];english=ref['source_tokens'];order=orders[unit['uid']] if orders else list(range(len(english)))
        assert sorted(order)==list(range(len(english)))
        eligible=ref['gate']['development_positional_score_eligible']
        if eligible:assert len(english)==len(unit['tokens'])
        counts={name:{'predictions':0,'abstentions':0,'verified_positional_matches':0,'positional_conflicts':0,'unscoreable_predictions':0} for name in ('primary','secondary')}
        for token in unit['tokens']:
            result={'uid':token['uid'],'unit_uid':unit['uid'],'component':unit['component'],'index':token['index'],
                'fl_form':token['fl_form'],'fl_span':token['fl_span'],'reference_form':english[order[token['index']]]['form'] if eligible else None,
                'gate_eligible':eligible}
            for name in ('primary','secondary'):
                pred=token[name]['form'];s=stats[name];s['all_tokens']+=1
                if pred is None:status='abstained';s['abstentions']+=1;counts[name]['abstentions']+=1
                else:
                    s['predictions']+=1;counts[name]['predictions']+=1
                    if not eligible:status='unscoreable';s['unscoreable_predictions']+=1;counts[name]['unscoreable_predictions']+=1
                    else:
                        s['evaluated_predictions']+=1
                        status='matched' if pred==result['reference_form'] else 'conflict'
                        key='verified_positional_matches' if status=='matched' else 'positional_conflicts'
                        s[key]+=1;counts[name][key]+=1
                result[name]={'prediction':pred,'status':status,'abstention_reason':token[name]['abstention_reason']}
            rows.append(result)
        unit_out.append({'uid':unit['uid'],'component':unit['component'],'token_denominator':len(unit['tokens']),
            'gate':ref['gate'],'primary':counts['primary'],'secondary':counts['secondary']})
    for s in stats.values():
        assert s['all_tokens']==s['predictions']+s['abstentions']
        assert s['predictions']==s['verified_positional_matches']+s['positional_conflicts']+s['unscoreable_predictions']
        s['prediction_coverage']=ratio(s['predictions'],s['all_tokens'])
        s['supported_agreement_all_predictions']=ratio(s['verified_positional_matches'],s['predictions'])
        s['conditional_agreement_scoreable_predictions']=ratio(s['verified_positional_matches'],s['evaluated_predictions'])
    return {'units':unit_out,'tokens':rows,'stats':stats,'unit_denominator':len(predictions),
        'eligible_units':sum(refs[u['uid']]['gate']['development_positional_score_eligible'] for u in predictions)}
