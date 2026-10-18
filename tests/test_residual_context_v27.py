import unittest
from fl_decipher.source_specificity_v26 import tokens
from fl_decipher.residual_context_v27 import context,windows,score

PHRASE='alpha bravo charlie delta epsilon foxtrot golf hotel'


class ResidualContextTests(unittest.TestCase):
    def test_positive_run_threshold_and_maximal_deduplication(self):
        r=score(PHRASE,'prefix '+PHRASE+' suffix',set())
        self.assertEqual(r['score'],[8,5]);self.assertTrue(r['qualifies'])
        self.assertEqual(len(r['matches']),1);self.assertEqual(r['matches'][0]['query_span']['text'],PHRASE)
        shorter=' '.join(PHRASE.split()[:-1]);r=score(shorter,shorter,set())
        self.assertEqual(r['score'],[7,4]);self.assertFalse(r['qualifies'])

    def test_blocked_token_is_barrier_and_never_bridges_neighbors(self):
        self.assertEqual(score('alpha bravo BLOCK charlie delta','alpha bravo charlie delta',{'block'})['score'],[0,0])
        r=score(PHRASE,PHRASE,{'delta'})
        self.assertEqual(r['score'][0],4);self.assertFalse(r['qualifies'])
        for m in r['matches']:self.assertNotIn('delta',m['source_span']['text'])

    def test_seed_rejects_repetitive_or_only_short_word_sequences(self):
        for text in [' '.join(['xqframe']*160),'alpha bravo alpha bravo alpha bravo alpha bravo','a be in to a be in to']:
            self.assertEqual(score(text,text,set())['score'],[0,0])

    def test_case_punctuation_and_unicode_raw_quotes_remain_auditable(self):
        query='🧭 '+PHRASE.upper();source=PHRASE.replace('charlie delta','charlie,\n delta')
        r=score(query,source,set());self.assertTrue(r['qualifies'])
        m=r['matches'][0]
        for key,text in [('query_span',query),('source_span',source)]:
            s=m[key];self.assertEqual(text[s['start']:s['end']],s['text'])
        self.assertEqual(score('cafe bravo charlie delta','café bravo charlie delta',set())['score'],[0,0])

    def test_repeated_occurrences_keep_all_maximal_match_pairs(self):
        q=PHRASE+' BLOCK '+PHRASE;r=score(q,PHRASE,{'block'})
        self.assertEqual(len(r['matches']),2);self.assertEqual(r['score'],[8,5])

    def test_fl_context_is_fixed_at_forty_tokens_each_side(self):
        text=' '.join('word'+str(i) for i in range(120));ts=tokens(text)
        r=context(text,[{'start':ts[50]['start'],'end':ts[54]['end']}])
        self.assertEqual((r['fl_token_start'],r['fl_token_end'],r['token_count']),(10,95,85))
        self.assertEqual(text[r['fl_char_start']:r['fl_char_end']],r['text'])

    def test_windows_preserve_final_start_and_raw_codepoint_mapping(self):
        text='🧭 '+' '.join('word'+str(i) for i in range(171));d={'id':'d','source_group':'g','text':text}
        rows=windows(d)
        self.assertEqual([r['token_start'] for r in rows],[0,11])
        self.assertEqual(len(windows(d,200,80)),1)
        for r in rows:self.assertEqual(text[r['char_start']:r['char_end']],r['text'])

    def test_reversal_does_not_retain_a_forward_literal_run(self):
        reversed_text=' '.join(reversed(PHRASE.split()))
        self.assertEqual(score(PHRASE,reversed_text,set())['score'],[0,0])

    def test_seed_extension_matches_independent_diagonal_run_search(self):
        from scripts.verify_residual_context_v27 import reference_score
        samples=[PHRASE,PHRASE+' BLOCK '+PHRASE,'alpha bravo charlie delta x alpha bravo charlie delta',
                 ' '.join(reversed(PHRASE.split())),' '.join(['xqframe']*12),'']
        for query in samples:
            for source in samples:
                for blocked in [set(),{'block','delta'}]:
                    self.assertEqual(score(query,source,blocked),reference_score(query,source,blocked))


if __name__=='__main__':unittest.main()
