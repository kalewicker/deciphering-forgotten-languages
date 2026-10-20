import copy
import unittest
from fl_decipher.final_challenge_v62 import nominate, conditional_alias, capacity, compare, closeout


def anchors(keys):return [{'kind':'number','key':'number:'+str(k),'anchor_index':i,'unit':0,'span':[2*i,2*i+1],'value':str(k)} for i,k in enumerate(keys)]
def rep(keys):return {'available':True,'inventory':{'anchors':anchors(keys)},'units':[{'unit':0,'span':[0,100],'text':'x'*100}],'quote_masks':[]}
def card(i,url,title='Antarctic neutrino detector',valid=True):return {'card_index':i,'strict_article_key':url if valid else None,'resolved_url':url,'strict_url_usable':valid,'structurally_attributed':True,'title':title,'snippets':[{'text':'ANITA'}]}


class FinalChallengeTests(unittest.TestCase):
    def test_saved_order_two_slots_prior_capture_and_duplicate_preserved(self):
        rows=[card(0,'https://physicsworld.com/a/old/'),card(1,'https://physicsworld.com/a/new/'),card(2,'https://physicsworld.com/a/new/'),card(3,'https://physicsworld.com/a/other/'),card(4,'https://physicsworld.com/a/over/')]
        prior={'captured_article_keys':[rows[0]['resolved_url']],'article_exposures':{rows[1]['resolved_url']:['known_search_link']}}
        r=nominate({'cards':rows,'exposure_registry':prior})
        self.assertEqual([s['nominee']['card_index'] for s in r['slots']],[1,3])
        self.assertEqual([r['cards'][i]['decision_reason'] for i in [0,2,4]],['previously_captured_url','duplicate_returned_url','slot_cap'])
        self.assertEqual(r['slots'][0]['nominee']['prior_exposure_tags'],['known_search_link'])

    def test_topic_and_strict_url_failures_leave_empty_slots(self):
        r=nominate({'cards':[card(0,'bad',valid=False),card(1,'https://physicsworld.com/a/x/','Anita personal biography')],
                    'exposure_registry':{'captured_article_keys':[],'article_exposures':{}}})
        self.assertEqual(r['occupied_slots'],0);self.assertTrue(all(s['nominee'] is None for s in r['slots']))

    def test_native_failure_stops_capacity_even_if_bag_would_match(self):
        r=capacity({'development_capture_eligible':False},rep([1,2,3,4,5,6]),anchors([1,2,3,4,5,6]))
        self.assertEqual(r['status'],'not_evaluated_native_ineligible');self.assertIsNone(r['windows']);self.assertFalse(r['qualifying_comparator'])
        self.assertIsNone(compare([],None,r,{}))

    def test_window_capacity_six_not_whole_bag_or_three_type_gate(self):
        native={'development_capture_eligible':True};target=anchors([1,2,3,4,5,6,6])
        self.assertTrue(capacity(native,rep([1,2,3,4,5,6]),target)['qualifying_comparator'])
        self.assertEqual(capacity(native,rep([1,2,6,6]),target)['maximum_window_bag_capacity'],4)
        r=capacity(native,rep([1,2,3]+[99]*11+[4,5,6]),target)
        self.assertEqual(r['maximum_window_bag_capacity'],3);self.assertFalse(r['qualifying_comparator'])
        self.assertEqual(len(r['windows']),7)

    def test_empty_and_unavailable_representations_and_fixed_parameters(self):
        native={'development_capture_eligible':True}
        r=capacity(native,rep([]),anchors([1]));self.assertEqual(r['windows'][0]['bag_capacity'],0)
        self.assertFalse(capacity(native,{'available':False},[])['qualifying_comparator'])
        with self.assertRaises(ValueError):capacity(native,rep([]),[],minimum=3)

    def test_comparison_keeps_all_controls_and_tied_reference(self):
        cfg={'numeric_budget':11,'seed':'scaffold46-20261019','draws_per_shuffle_family':16,'minimum_shared_numeric_types':3,
             'control_families':['reverse','within_paragraph_reverse','anchor_shuffle','paragraph_shuffle']}
        target=anchors([1,2,3,4,5,6]);p=rep([1,2,3,4,5,6]);screen=capacity({'development_capture_eligible':True},p,target)
        r=compare(target,p,screen,cfg)
        self.assertEqual(len(r['assessment']['controls']),34);self.assertTrue(r['candidate_ties_reference']);self.assertFalse(r['reference_strictly_exceeds_candidate'])

    def test_conditional_alias_does_not_fetch_when_other_native_gate_failed(self):
        raw=b'<html><head><title>Test - Physics World</title><meta property="og:title" content="Test"><meta property="og:url" content="https://physicsworld.com/test/"><link rel="canonical" href="https://physicsworld.com/a/test/"><script type="application/ld+json">{"@type":"Article","headline":"Test"}</script></head></html>'
        receipt={'transport_complete':True,'final_url':'https://physicsworld.com/a/test/'};spec={'url':receipt['final_url'],'expected_title':'Test'}
        p={'checks':{'all_og_urls_bound':False,'publication_date_in_window':False}}
        self.assertIsNone(conditional_alias(raw,receipt,spec,p)['request_url'])
        p['checks']['publication_date_in_window']=True
        self.assertEqual(conditional_alias(raw,receipt,spec,p)['request_url'],'https://physicsworld.com/test/')

    def test_empty_batch_closes_without_vacuous_specificity_success(self):
        slots=[{'occupied':False,'native_eligible':False,'capacity':{'qualifying_comparator':False,'status':'empty_slot'},'comparison':None} for _ in range(2)]
        r=closeout(slots);self.assertEqual(r['closure'],'closed_feasibility_limited');self.assertIsNone(r['reference_specificity_gate_among_capable'])
        self.assertEqual(r['empty_slots'],2);self.assertEqual(r['additional_batches_authorized'],0)
