import unittest
from itertools import product,combinations
from fl_decipher.source_specificity_v26 import score,windows,frame,masked,corrected_spellings,aggregate,decide,tokens


class SpecificityTests(unittest.TestCase):
    def test_unicode_boundaries_and_exact_raw_offsets(self):
        text='🧭 ZAZEL, zazél zazel\u0301.\n'
        r=score(text,['zazel'])
        self.assertEqual(r['score'],[1,1]);self.assertEqual(r['occurrences'],[[{'start':2,'end':7,'text':'ZAZEL'}]])
        self.assertEqual(tokens('e\u0301')[0]['form'],'é')

    def test_order_partial_reverse_and_repeated_occurrences(self):
        self.assertEqual(score('c b a',['a','b','c'])['score'],[3,1])
        self.assertEqual(score('b a b c',['a','b','c'])['score'],[3,3])
        self.assertEqual(score('a c',['a','b','c'])['score'],[2,2])
        self.assertEqual(score('a a a',['a','b','c'])['score'],[1,1])

    def test_overlapping_anchor_tokens_cannot_form_nonoverlap_chain(self):
        self.assertEqual(score('a b c',['a b','b c'])['score'],[2,1])
        self.assertEqual(score('a b b c',['a b','b c'])['score'],[2,2])

    def test_windows_keep_final_short_and_stride_boundaries(self):
        d={'id':'d','source_group':'g','text':'  a b c d e f g h i j k\n'}
        r=windows(d,4)
        self.assertEqual([w['word_start'] for w in r],[0,2,4,6,7])
        for w in r:self.assertEqual(w['text'],d['text'][w['char_start']:w['char_end']])
        self.assertEqual(len(windows(d,20)),1)
        self.assertEqual(windows(d,20)[0]['word_count'],11)

    def test_copied_anchor_frame_can_fool_source_absent_nomination(self):
        anchors=['first name','second','third'];text=frame(anchors,20)
        self.assertEqual(len(text.split()),20);self.assertTrue(score(text,anchors)['qualifies'])
        s=score(text,anchors);lure={'document_id':'lure','score':s['score'],'qualifies':s['qualifies']}
        self.assertEqual(decide([lure])['nominated'],'lure')
        self.assertIsNone(decide([lure,lure|{'document_id':'real'}])['nominated'])
        self.assertEqual(score(frame(anchors,20,True),anchors)['score'],[3,1])

    def test_masks_all_matches_and_preserves_other_tokens(self):
        text='a b c / a b c; keep'
        m=masked(text,['a b','b c'])
        self.assertEqual(m,'xqmasked xqmasked xqmasked / xqmasked xqmasked xqmasked; keep')

    def test_spelling_counterfactual_is_not_fuzzy_matching(self):
        t='possibile possibilites impossibile possibilitesx'
        self.assertEqual(corrected_spellings(t),'possible possibilities impossibile possibilitesx')
        self.assertEqual(score(corrected_spellings(t),['possibile','possibilites'])['score'],[0,0])

    def test_document_max_retains_every_tied_window(self):
        rows=[{'window_id':'w1','document_id':'d','source_group':'g','score':[2,2],'qualifies':True},
              {'window_id':'w2','document_id':'d','source_group':'g','score':[2,2],'qualifies':True},
              {'window_id':'w3','document_id':'e','source_group':'h','score':[1,1],'qualifies':False}]
        a=aggregate(rows);self.assertEqual(a[0]['best_window_ids'],['w1','w2'])
        self.assertEqual(decide(a)['nominated'],'d');self.assertIsNone(decide(a[1:])['nominated'])
        self.assertEqual(decide([])['reason'],'empty_panel')

    def test_chain_dynamic_program_matches_small_exhaustive_oracle(self):
        for size in range(5):
            for words in product(['a','b','c'],repeat=size):
                for anchors in [['a','b','c'],['a b','b c'],['a','a b','c']]:
                    positions=[]
                    for anchor in anchors:
                        target=tuple(anchor.split())
                        positions.append([(i,i+len(target)) for i in range(len(words)-len(target)+1) if words[i:i+len(target)]==target])
                    def exists(indices,last=0):
                        return not indices or any(exists(indices[1:],end) for start,end in positions[indices[0]] if start>=last)
                    best=max(n for n in range(len(anchors)+1) if any(exists(indices) for indices in combinations(range(len(anchors)),n)))
                    self.assertEqual(score(' '.join(words),anchors)['score'],[sum(bool(p) for p in positions),best])


if __name__ == '__main__':
    unittest.main()
