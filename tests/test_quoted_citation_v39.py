import unittest
from fl_decipher.quoted_citation_v39 import assess_queries, frozen_queries


def fixture_queries():
    return [{'quote_id':f'quote{i:02d}','span':[0,1],'text':f'fixture unique phrase {i}',
             'language_or_meaning_admitted':False} for i in range(8)]


class FixedQuotationAccountingTests(unittest.TestCase):
    def test_unavailable_paper_is_not_eight_negative_results(self):
        r=assess_queries(fixture_queries(),[],[],False)
        self.assertEqual(r['quote_denominator'],8)
        self.assertEqual(r['query_outcomes_unavailable'],8)
        self.assertIsNone(r['quotes_with_literal_source_presence'])
        self.assertIsNone(r['primary_long_block_presence'])
        self.assertTrue(all(q['source_hits'] is None for q in r['quotes']))

    def test_instrument_name_alone_cannot_pass_long_block_question(self):
        q=fixture_queries()
        r=assess_queries(q,[{'page':1,'text':q[1]['text']}],[],True)
        self.assertEqual(r['quotes_with_literal_source_presence'],1)
        self.assertTrue(r['expanded_name_literal_presence'])
        self.assertEqual(r['long_quotes_with_literal_presence'],0)
        self.assertFalse(r['primary_long_block_presence'])

    def test_empty_source_page_remains_unavailable(self):
        r=assess_queries(fixture_queries(),[{'page':1,'text':'other material'},{'page':2,'text':''}],[],True)
        self.assertEqual(r['source_page_denominator'],2)
        self.assertEqual(len(r['positive_controls']),2)
        self.assertEqual(r['positive_controls_unavailable'],1)
        self.assertEqual(r['query_outcomes_unavailable'],8)
        self.assertIsNone(r['primary_long_block_presence'])

    def test_changed_frozen_query_is_rejected(self):
        text=' '.join('"'+q['text']+'"' for q in fixture_queries())
        from fl_decipher.dated_capture_scope_v38 import quote_spans
        old={'quotes':quote_spans(text)}
        self.assertEqual(len(frozen_queries(text,old)),8)
        old['quotes'][0]['text']='changed answer'
        with self.assertRaises(AssertionError):frozen_queries(text,old)


if __name__=='__main__':unittest.main()
