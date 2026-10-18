import importlib.util
from pathlib import Path
from math import comb
import unittest
from fl_decipher.synthetic_transfer_v32 import training,learn,view,decode,align,decision,prepare_tests,predict,assess

SPEC=importlib.util.spec_from_file_location('independent_transfer_v32',Path(__file__).resolve().parents[1]/'scripts/verify_synthetic_transfer_v32.py')
REF=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(REF)
MINI={'training_keys':[7],'unseen_keys':[101],'training_passages_per_key':2,'training_cycles':3,'trained_classes':24,
      'test_passages':1,'test_length':32,'barrier_period':17,'groups':['seen','sparse_unknown','dense_unknown','unseen_key'],
      'mechanisms':['bijective','insertion','deletion','contextual','reordering'],
      'scenarios':['present','absent','impostor_only','parent_plus_impostor','duplicate_parent']}


def supervised(uid,qs,ss):
    return {'unit_id':uid,'query':view(qs),'source':view(ss),'aligned_positions':[[i,i] for i in range(len(qs))]}


class SyntheticTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train=training(MINI);cls.model=learn(cls.train)
        cls.public,cls.oracle,cls.availability=prepare_tests(MINI,cls.model)
        cls.predictions=predict(cls.public,cls.model)
        cls.assessment=assess(cls.public,cls.oracle,cls.availability,cls.predictions)

    def test_training_and_mapping_independently_reconstructed(self):
        self.assertEqual(self.train,REF.reference_training(MINI))
        self.assertEqual(self.model,REF.reference_learn(self.train))
        self.assertEqual(len(self.model['entries']),24)
        self.assertTrue(all(len(e['support_units'])==2 for e in self.model['entries'].values()))

    def test_repeated_positions_do_not_create_two_units(self):
        data={'units':[supervised('same',['a','a'],['symbol0','symbol0'])]}
        m=learn(data);self.assertEqual(m['entries'],{})
        self.assertEqual(m['ledger']['a']['status'],'insufficient_support')

    def test_conflict_is_not_resolved_by_majority(self):
        data={'units':[supervised('u1',['a','a'],['symbol0','symbol0']),supervised('u2',['a'],['symbol1'])]}
        m=learn(data);self.assertNotIn('a',m['entries']);self.assertEqual(m['ledger']['a']['status'],'conflict')
        self.assertEqual(m,REF.reference_learn(data))

    def test_key_specific_aliases_can_share_a_source_symbol(self):
        data={'units':[supervised('u1',['a','b'],['symbol0','symbol0']),supervised('u2',['a','b'],['symbol0','symbol0'])]}
        m=learn(data);self.assertEqual({e['source_form'] for e in m['entries'].values()},{'symbol0'})
        self.assertEqual(set(m['entries']),{'a','b'})

    def test_unknown_and_blocked_tokens_never_receive_filled_labels(self):
        model={'entries':{'a':{'source_form':'symbol0'},'copiedanchor0':{'source_form':'bad'}},'ledger':{}}
        q=view(['a','novel','copiedanchor0']);d=decode(q,model)
        self.assertEqual([r['source_form'] for r in d],['symbol0',None,None])
        self.assertEqual([r['status'] for r in d],['mapped','unseen','blocked'])

    def test_global_gap_path_preserves_every_token(self):
        q=view(['a','inserted','b']);c=view(['symbol0','symbol1'])
        d=decode(q,{'entries':{'a':{'source_form':'symbol0'},'b':{'source_form':'symbol1'}},'ledger':{}})
        result=align(q,c,d);self.assertEqual(result,REF.reference_align(q,c,d))
        self.assertEqual((result['matched_tokens'],result['edit_cost']),(2,1))
        self.assertIn([1,None],result['trace'])

    def test_repeated_symbols_have_multiple_optimal_operation_paths(self):
        q=view(['a','a']);c=view(['symbol0']);d=decode(q,{'entries':{'a':{'source_form':'symbol0'}},'ledger':{}})
        r=align(q,c,d);self.assertEqual(r,REF.reference_align(q,c,d))
        self.assertEqual(r['optimal_operation_paths'],2)
        self.assertEqual(r['trace'],[[0,None],[1,0]])

    def test_all_unknown_paths_count_without_forced_matches(self):
        q=view(['a','b']);c=view(['symbol0','symbol1','symbol2']);d=decode(q,{'entries':{},'ledger':{}})
        r=align(q,c,d);self.assertEqual(r['matched_tokens'],0)
        self.assertEqual((r['edit_cost'],r['optimal_operation_paths']),(5,comb(5,2)))
        self.assertEqual(r,REF.reference_align(q,c,d))

    def test_exact_coverage_boundary_and_minimum_match_count(self):
        known=[f'a{i}' for i in range(24)];source=[f'symbol{i}' for i in range(24)]
        model={'entries':{q:{'source_form':s} for q,s in zip(known,source,strict=True)},'ledger':{}}
        q=view(known+[f'u{i}' for i in range(6)]);c=view(source+[f'x{i}' for i in range(6)])
        self.assertTrue(align(q,c,decode(q,model))['qualifies'])
        longer=view(known+[f'u{i}' for i in range(7)])
        self.assertFalse(align(longer,c,decode(longer,model))['qualifies'])
        c['tokens'][0]['form']='wrong'
        self.assertFalse(align(q,c,decode(q,model))['qualifies'])

    def test_duplicate_tie_abstains_even_when_parent_qualifies(self):
        gold=next(c for c in self.oracle['cases'] if c['group']=='seen' and c['mechanism']=='bijective' and c['scenario']=='duplicate_parent')
        result=next(p for p in self.predictions['panels'] if p['case_id']==gold['case_id'])
        self.assertIsNone(result['decision']['nominated'])
        self.assertEqual(result['decision']['top_unit_ids'],['slot0','slot4'])

    def test_mapping_distinguishes_structurally_equivalent_impostor(self):
        gold=next(c for c in self.oracle['cases'] if c['group']=='seen' and c['mechanism']=='bijective' and c['scenario']=='parent_plus_impostor')
        p=next(p for p in self.predictions['panels'] if p['case_id']==gold['case_id'])
        self.assertEqual(p['decision']['nominated'],'slot0')
        self.assertTrue(all(c['anonymous_profile_equal'] for c in self.availability['equivalence_certificates']))

    def test_withheld_types_and_unseen_keys_stay_unmapped(self):
        self.assertFalse(any(e['source_form'] in {f'symbol{i}' for i in range(24,32)} for e in self.model['entries'].values()))
        for q in self.oracle['queries']:
            if q['group']=='unseen_key':
                self.assertTrue(all(t['source_form'] is None for t in self.predictions['decoded_queries'][q['query_view_id']]))

    def test_supported_seen_mechanisms_transfer_on_small_fixture(self):
        supported=[c for c in self.assessment['case_outcomes'] if c['group']=='seen' and c['mechanism']!='contextual' and c['scenario']=='present']
        self.assertEqual(len(supported),4)
        self.assertTrue(all(c['outcome']=='correct_parent' for c in supported))

    def test_all_public_offsets_and_oracle_separation(self):
        self.assertEqual(set(self.public),{'views','cases'})
        for v in self.public['views'].values():
            for t in v['tokens']:self.assertEqual(v['text'][t['start']:t['end']],t['form'])
        self.assertEqual((len(self.oracle['bases']),len(self.oracle['queries']),len(self.public['cases'])),(4,20,100))

    def test_complete_independent_generation_paths_metrics_and_decisions(self):
        self.assertEqual((self.public,self.oracle,self.availability),REF.reference_tests(MINI,self.model))
        expected=REF.reference_predict(self.public,self.model);self.assertEqual(self.predictions,expected)
        self.assertEqual(self.assessment,REF.reference_assess(self.public,self.oracle,self.availability,expected))


if __name__=='__main__':unittest.main()
