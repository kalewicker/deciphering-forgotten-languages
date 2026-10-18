import importlib.util
from pathlib import Path
import unittest
from fl_decipher.synthetic_mechanisms_v31 import prepare,predict,assess,aliases,transformed,profile
from fl_decipher.paragraph_patterns_v30 import fingerprints

SPEC=importlib.util.spec_from_file_location('independent_synthetic_v31',Path(__file__).resolve().parents[1]/'scripts/verify_synthetic_mechanisms_v31.py')
REF=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(REF)
MINI={'keys':[5],'profiles':[{'id':'small','kind':'hash','length':28,'vocabulary':6,'barrier_period':17},
                            {'id':'short','kind':'short','length':8,'barrier_period':17}],
      'mechanisms':['bijective','insertion','deletion','contextual','reordering'],
      'scenarios':['present','absent','collision','impostor_only','anchor_frame']}


class SyntheticMechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public,cls.oracle,cls.availability=prepare(MINI)
        cls.predictions=predict(cls.public)
        cls.assessment=assess(cls.public,cls.oracle,cls.availability,cls.predictions)

    def test_independent_generator_and_availability(self):
        self.assertEqual((self.public,self.oracle,self.availability),REF.reference_prepare(MINI))
        self.assertEqual((len(self.oracle['bases']),len(self.oracle['queries']),len(self.public['cases'])),(2,10,50))

    def test_exact_bijective_origin_and_alias(self):
        bases={b['base_id']:b for b in self.oracle['bases']}
        for q in self.oracle['queries']:
            if q['mechanism']!='bijective':continue
            b=bases[q['base_id']];source=self.public['views'][b['view_ids']['parent']]['tokens'];query=self.public['views'][q['query_view_id']]['tokens']
            self.assertEqual(q['origins'],list(range(len(source))))
            for s,t in zip(source,query,strict=True):
                self.assertEqual(t['form'],s['form'] if s['blocked'] else b['alias_table'][s['form']][0])

    def test_inserted_tokens_have_null_origins(self):
        forms=[f'a{i}' for i in range(14)];table=aliases(forms,0,1)
        fs,trace=transformed(forms,table,0,1,'insertion')
        self.assertEqual(len(fs),16)
        self.assertEqual([i for i,o in enumerate(trace['origins']) if o is None],[7,15])
        self.assertEqual(trace['insertions'],[{'query_index':7,'source_index':6},{'query_index':15,'source_index':13}])
        self.assertEqual(trace['deleted_indices'],[])

    def test_deleted_positions_are_retained_in_oracle(self):
        forms=[f'a{i}' for i in range(14)]
        _,trace=transformed(forms,aliases(forms,0,1),0,1,'deletion')
        self.assertEqual(trace['deleted_indices'],[6,13])
        self.assertEqual(len(trace['origins']),12)

    def test_contextual_alias_parities(self):
        forms=['a','b','a','a','b','copiedanchor0','a'];table=aliases(forms,0,1)
        fs,trace=transformed(forms,table,0,1,'contextual')
        self.assertEqual(trace['alias_parities'],[0,0,1,0,1,None,1])
        self.assertEqual(fs[5],'copiedanchor0')
        self.assertNotEqual(fs[0],fs[2]);self.assertEqual(fs[0],fs[3])

    def test_reordering_has_exact_nonmonotonic_origin_trace(self):
        forms=[f'a{i}' for i in range(16)]
        _,trace=transformed(forms,aliases(forms,0,1),0,1,'reordering')
        self.assertEqual(trace['origins'],[0,1,2,3,4,5,7,6,8,9,10,11,12,14,13,15])
        self.assertEqual(trace['deleted_indices'],[])

    def test_all_synthetic_raw_offsets_are_exact(self):
        for v in self.public['views'].values():
            for t in v['tokens']:self.assertEqual(v['text'][t['start']:t['end']],t['form'])

    def test_equivalent_impostor_changes_raw_text_not_features(self):
        b=self.oracle['bases'][0];a=self.public['views'][b['view_ids']['parent']];c=self.public['views'][b['view_ids']['impostor']]
        self.assertNotEqual(a['text'],c['text']);self.assertEqual(profile(a),profile(c))
        self.assertTrue(self.availability['equivalence_certificates'][0]['profile_equal'])

    def test_unavailable_queries_remain_and_abstain(self):
        unavailable={q['query_view_id'] for q in self.oracle['queries'] if not self.availability['views'][q['query_view_id']]['feature_available']}
        ps={p['case_id']:p for p in self.predictions['panels']};tested=0
        for c in self.public['cases']:
            if c['query_view_id'] in unavailable:
                self.assertIsNone(ps[c['case_id']]['decision']['nominated']);tested+=1
        self.assertGreaterEqual(tested,25)
        self.assertEqual(len(self.assessment['case_outcomes']),50)

    def test_anchor_frames_have_no_eligible_patterns(self):
        for b in self.oracle['bases']:self.assertEqual(fingerprints(self.public['views'][b['view_ids']['frame']]),{})

    def test_paired_worlds_have_equal_observations(self):
        self.assertEqual(len(self.assessment['paired_worlds']),10)
        for w in self.assessment['paired_worlds']:
            self.assertTrue(w['features_equal'] and w['scores_equal'] and w['decisions_equal'])
        self.assertNotIn('oracle',self.public)
        self.assertEqual(set(self.public),{'views','cases'})

    def test_complete_independent_prediction_and_assessment(self):
        expected=REF.reference_predict(self.public)
        self.assertEqual(self.predictions,expected)
        self.assertEqual(self.assessment,REF.reference_assess(self.public,self.oracle,self.availability,expected))
        self.assertFalse(self.assessment['admission_gate']['passed'])


if __name__=='__main__':unittest.main()
