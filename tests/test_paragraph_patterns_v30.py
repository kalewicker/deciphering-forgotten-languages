import importlib.util
from pathlib import Path
from collections import Counter
import unittest
from fl_decipher.paragraph_patterns_v30 import view,control,fingerprints,scored,decide,null_order,shuffled,evaluate

SPEC=importlib.util.spec_from_file_location('independent_patterns_v30',Path(__file__).resolve().parents[1]/'scripts/verify_paragraph_patterns_v30.py')
REF=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(REF)
TEXT='a b a c b d e f g h a i b j a k l b a m'


def unit(text=TEXT,identity='u',work='work',blocked=()):
    return {'unit_id':identity,'work':work,'candidate':True,**view(text,blocked)}


class ParagraphPatternTests(unittest.TestCase):
    def test_opaque_renaming_preserves_patterns(self):
        q=unit()|{'id':'q'};c=control(q,'opaque')
        self.assertEqual(set(fingerprints(q)),set(fingerprints(c)))
        self.assertNotEqual([t['form'] for t in q['tokens']],[t['form'] for t in c['tokens']])
        self.assertTrue(scored(fingerprints(q),fingerprints(c),c)['qualifies'])

    def test_unique_and_single_repeated_type_are_ineligible(self):
        self.assertEqual(fingerprints(unit('a b c d e f g h i j')), {})
        self.assertEqual(fingerprints(unit('a a a a b c d e f g')), {})

    def test_equality_requires_two_way_consistency(self):
        a=unit('a b a c b d e f g h');b=unit('a b c d b e f g h i')
        self.assertEqual(scored(fingerprints(a),fingerprints(b),b)['score'],0)
        self.assertEqual(fingerprints(a),REF.oracle_index(a))

    def test_barriers_are_not_removed_or_bridged(self):
        q=unit('a b a c b d e f g h',blocked=['c'])
        self.assertEqual(len(q['tokens']),10)
        self.assertEqual(fingerprints(q),{})
        self.assertEqual(fingerprints(q),REF.oracle_index(q))

    def test_repeated_occurrences_count_as_one_type(self):
        phrase='a b a c b d e f g h';u=unit(phrase+' barrier '+phrase,blocked=['barrier'])
        index=fingerprints(u)
        self.assertEqual(len(index),1)
        self.assertEqual(len(next(iter(index.values()))),2)
        row=scored(index,index,u)
        self.assertEqual(row['score'],1);self.assertFalse(row['qualifies'])

    def test_all_raw_witness_offsets_and_unicode_profile(self):
        text='Été beta e\u0301te\u0301 gamma beta delta epsilon zeta eta theta'
        u=unit(text)
        self.assertEqual(view(text,[]),REF.lexical(text,[]))
        self.assertEqual(fingerprints(u),REF.oracle_index(u))
        for occurrences in fingerprints(u).values():
            for r in occurrences:self.assertEqual(text[r['start']:r['end']],r['text'])

    def test_ties_and_threshold_abstain(self):
        tied=[{'unit_id':'b','score':3},{'unit_id':'a','score':3}]
        self.assertIsNone(decide(tied)['nominated'])
        self.assertEqual(decide(tied)['top_unit_ids'],['a','b'])
        self.assertIsNone(decide([{'unit_id':'a','score':1}])['nominated'])
        self.assertEqual(decide([{'unit_id':'a','score':2}])['nominated'],'a')
        self.assertEqual(decide([]),REF.oracle_decision([]))

    def test_anchor_frame_has_no_unmasked_repetition(self):
        q=unit(blocked=['a','b'])|{'id':'q'};c=control(q,'anchor_frame')
        self.assertEqual([t['blocked'] for t in c['tokens']],[t['blocked'] for t in q['tokens']])
        self.assertEqual(fingerprints(c),{})

    def test_complete_null_order_and_histogram_preservation(self):
        u=unit(blocked=['a']);order=null_order(u,0);s=shuffled(u,order)
        self.assertEqual(sorted(order),[i for i,t in enumerate(u['tokens']) if not t['blocked']])
        self.assertEqual(order,null_order(u,0));self.assertNotEqual(order,null_order(u,1))
        self.assertEqual(Counter(t['form'] for t in s['tokens']),Counter(t['form'] for t in u['tokens']))
        for a,b in zip(u['tokens'],s['tokens'],strict=True):
            if a['blocked']:self.assertEqual(a,b)
        with self.assertRaises(AssertionError):shuffled(u,order[:-1])

    def test_reverse_control_reverses_barrier_positions(self):
        q=unit(blocked=['a'])|{'id':'q'};c=control(q,'reverse')
        self.assertEqual([t['form'] for t in c['tokens']],[t['form'] for t in reversed(q['tokens'])])
        self.assertEqual([t['blocked'] for t in c['tokens']],[t['blocked'] for t in reversed(q['tokens'])])

    def test_pairwise_oracle_matches_each_window(self):
        for blocked in [[],['a'],['i','j'],['a','b','c']]:
            u=unit(blocked=blocked)
            self.assertEqual(fingerprints(u),REF.oracle_index(u))

    def test_complete_natural_control_null_and_failed_gate_replay(self):
        queries=[unit(identity='fl'+str(i),work='A' if i<2 else 'B')|{'id':'q'+str(i),'expected_unit_id':'sourceA' if i<2 else 'sourceB'} for i in range(3)]
        source_a=control(queries[0],'opaque')|{'unit_id':'sourceA','work':'A','candidate':True}
        source_b=unit('one two three four five six seven eight nine ten eleven twelve','sourceB','B')
        sources=[source_a,source_b]
        frozen={'registry':{'queries':queries,'source_units':sources},
                'controls':[control(q,k)|{'query_id':q['id']} for q in queries for k in ['opaque','anchor_frame','reverse']],
                'null_orders':[{'draw':d,'orders':{u['unit_id']:null_order(u,d) for u in sources}} for d in range(199)]}
        result=evaluate(frozen);oracle=REF.oracle_evaluation(frozen,sources,queries)
        for k,v in oracle.items():self.assertEqual(result[k],v,k)
        self.assertFalse(result['gate']['passed'])
        self.assertEqual(len(result['query_ledgers']),3)
        self.assertIsNone(result['query_ledgers'][0]['source_work_absent_decision']['nominated'])


if __name__=='__main__':unittest.main()
