from copy import deepcopy
import unittest
from fl_decipher.review_handoff_v25 import sha,template,validate_return


class ReviewHandoffTests(unittest.TestCase):
    def setUp(self):
        self.texts={'fl':'A 🧭 é line.\n','source':'An example source.\n'}
        self.manifest={'nominee_id':'test','members':{n:{'sha256':sha(self.texts[k].encode())} for k,n in [('fl','fl_post.txt'),('source','publisher_window.txt')]}}
        self.blank=template('test','packet-sha')
        self.valid=deepcopy(self.blank)
        self.valid.update(reviewer={'name':'SYNTHETIC TEST REVIEWER','kind':'human','identifier':'fixture-only',
            'independent_of_prior_predictions':True,'prior_exposure':'Synthetic fixture; no real reviewer.'},
            review_completed=True,completed_at_utc='2026-10-15T00:00:00+00:00',statement_boundaries_checked=False,
            language_observations=[{'fl_span':{'start':2,'end':3,'text':'🧭'},'language':'unknown',
                                   'certainty':'unknown','notes':'Fixture only; no language inference.'}],
            uncertainty_notes=['No source identity established by this fixture.'])

    def check(self,value,texts=None):
        return validate_return(value,self.manifest,'packet-sha',texts or self.texts)

    def test_blank_template_is_not_a_return(self):
        result=self.check(self.blank)
        self.assertFalse(result['structurally_valid']);self.assertGreater(len(result['errors']),5)

    def test_entirely_uncertain_review_is_valid_without_forcing_matches(self):
        r=self.check(self.valid)
        self.assertTrue(r['ready_for_adjudication']);self.assertFalse(r['independence_externally_verified'])
        self.assertFalse(r['source_identity_admitted']);self.assertEqual(r['semantic_labels_admitted'],0)

    def test_support_and_rejection_require_scoped_evidence(self):
        for status,relationship,field in [('supported','supports','evidence_pairs'),('rejected','contradicts','counterexamples')]:
            value=deepcopy(self.valid);value['source_relationship']=status
            self.assertFalse(self.check(value)['structurally_valid'])
            value[field]=[{'fl_span':{'start':0,'end':1,'text':'A'},'source_span':{'start':0,'end':2,'text':'An'},
                           'basis':'other','relationship':relationship,'notes':'Synthetic evidence; no real source claim.'}]
            result=self.check(value)
            self.assertTrue(result['structurally_valid']);self.assertFalse(result['source_identity_admitted'])

    def test_unicode_codepoints_not_utf8_bytes_or_utf16_units(self):
        self.assertTrue(self.check(self.valid)['structurally_valid'])
        for end in [4,6,999,True]:
            value=deepcopy(self.valid);value['language_observations'][0]['fl_span']['end']=end
            self.assertFalse(self.check(value)['structurally_valid'])

    def test_packet_text_and_quote_tampering_rejected(self):
        value=deepcopy(self.valid);value['packet_manifest_sha256']='stale'
        self.assertFalse(self.check(value)['structurally_valid'])
        texts=dict(self.texts);texts['source']+='changed'
        self.assertFalse(self.check(self.valid,texts)['structurally_valid'])
        value=deepcopy(self.valid);value['language_observations'][0]['fl_span']['text']='different'
        self.assertFalse(self.check(value)['structurally_valid'])

    def test_false_independence_and_semantic_admission_attempt_fail_closed(self):
        value=deepcopy(self.valid);value['reviewer']['independent_of_prior_predictions']=False
        self.assertFalse(self.check(value)['structurally_valid'])
        for field in ['semantic_training_eligible','accepted_word_meanings','untouched_test_eligible']:
            value=deepcopy(self.valid);value[field]=True
            self.assertFalse(self.check(value)['structurally_valid'])

    def test_malformed_structure_and_non_utc_date_rejected(self):
        for field,bad in [('reviewer',[]),('evidence_pairs',{}),('language_observations',None),
                          ('completed_at_utc','2026-10-15T00:00:00'),('coverage','accepted'),
                          ('schema_version',True),('uncertainty_notes',[])]:
            value=deepcopy(self.valid);value[field]=bad
            self.assertFalse(self.check(value)['structurally_valid'])


if __name__ == '__main__':
    unittest.main()
