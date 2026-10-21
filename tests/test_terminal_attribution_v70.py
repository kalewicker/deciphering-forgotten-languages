import unittest
from fl_decipher.terminal_attribution_v70 import freeze_batch,select_batch,evaluate_slot,terminal_decision

def block(i,text):return {'block_id':i,'run_id':i+3,'body_span':[0,len(text)],'text':text}
def response(title,url,text):return {'response':f'{title} ({url})\n[x] [wordlim: 200]\n{text}\n','error':None}
def batch():
    text=' '.join(f'token{i}' for i in range(30));b=freeze_batch({'blocks':[block(3,text),block(5,text)]},{'text':text});return b

class TerminalAttributionTests(unittest.TestCase):
    def test_fixed_prefix_suffix_requests_and_complete_target_retained(self):
        b=batch();self.assertEqual(len(b['requests']),4)
        for t in b['targets']:
            self.assertEqual(len(t['phrases'][0].split()),12);self.assertEqual(len(t['phrases'][1].split()),12);self.assertEqual(t['token_count'],30)

    def test_bad_body_slice_or_missing_block_refused(self):
        with self.assertRaises(ValueError):freeze_batch({'blocks':[]},{'text':''})
        t=' '.join(['a']*30)
        with self.assertRaises(ValueError):freeze_batch({'blocks':[block(3,t),block(5,t)]},{'text':'different'})

    def test_same_selected_url_captured_once_for_two_slots(self):
        b=batch();r=response('paper','https://example.org/p',b['targets'][0]['text']);s=select_batch([r,r,r,r],b,[],'FL title')
        self.assertEqual(s['unique_capture_urls'],['https://example.org/p']);self.assertEqual(s['slots'][1]['capture_owner_slot'],'b03');self.assertTrue(s['slots'][1]['reuses_capture'])

    def test_distinct_urls_preserve_two_capture_slots(self):
        b=batch();t=b['targets'][0]['text'];r=response('a','https://example.org/a',t);q=response('b','https://example.org/b',t)
        s=select_batch([r,r,q,q],b,[],'FL title');self.assertEqual(len(s['unique_capture_urls']),2)

    def test_echo_only_leaves_both_slots_empty(self):
        b=batch();r=response('FL','https://forgottenlanguages.org/a',b['targets'][0]['text']);s=select_batch([r]*4,b,[],'FL title')
        self.assertEqual(s['unique_capture_urls'],[]);self.assertTrue(all(x['capture_owner_slot'] is None for x in s['slots']))

    def test_prefix_only_native_presence_cannot_pass_complete_target(self):
        t=batch()['targets'][0];source={'text':t['phrases'][0],'representation_ready':True,'pages':[]}
        self.assertFalse(evaluate_slot(t,source)['complete_target_criterion_passed'])

    def test_full_target_needs_controls_and_pdf_visual_gate(self):
        t=batch()['targets'][0];source={'text':t['text'],'representation_ready':True,'pages':[{'page':1}]}
        self.assertTrue(evaluate_slot(t,source)['complete_target_criterion_passed']);self.assertFalse(evaluate_slot(t,source,False)['complete_target_criterion_passed'])
        source['text']+=' flv69absencecontrol20261020';self.assertFalse(evaluate_slot(t,source)['complete_target_criterion_passed'])

    def test_empty_source_and_two_failures_close_route(self):
        ts=batch()['targets'];rows=[evaluate_slot(t,None) for t in ts];r=terminal_decision(rows)
        self.assertTrue(r['wording_discovery_route_closed']);self.assertEqual(r['outcome'],'closed_feasibility_limited')

    def test_one_full_target_allows_only_future_design_and_preserves_denominator(self):
        ts=batch()['targets'];rows=[evaluate_slot(ts[0],{'text':ts[0]['text'],'representation_ready':True,'pages':[]}),evaluate_slot(ts[1],None)]
        r=terminal_decision(rows);self.assertEqual(r['native_complete_target_successes'],1);self.assertFalse(r['opaque_source_identity_or_meaning_admitted'])
        with self.assertRaises(ValueError):terminal_decision(rows[:1])
