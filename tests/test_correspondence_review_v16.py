from itertools import product
import unittest
from fl_decipher.correspondence_review_v16 import extract_html,whole_statement_matches,ordered_nonoverlapping,gates,positional_hypotheses
class CorrespondenceReviewTests(unittest.TestCase):
 def test_heading_does_not_merge_with_source_statement(self):
  d=extract_html(b'<title>Example</title><article><p><strong>A heading</strong></p><p>A complete sentence. Another sentence.</p></article>','article')
  hit=whole_statement_matches('A complete sentence.',d)
  self.assertEqual(len(hit),1);self.assertEqual(hit[0]['text'],'A complete sentence.');self.assertTrue(hit[0]['complete_statement']);self.assertEqual(d['text'][slice(*hit[0]['span'])],hit[0]['text'])
 def test_contained_fragment_does_not_become_full_statement(self):
  d=extract_html(b'<title>Example</title><article><p>Before a matching phrase after.</p></article>','article')
  self.assertFalse(whole_statement_matches('a matching phrase',d))
 def test_unfinished_statement_not_admitted(self):
  d=extract_html(b'<title>Example</title><article><p>An unfinished fragment</p></article>','article')
  self.assertFalse(whole_statement_matches('An unfinished fragment',d)[0]['complete_statement'])
 def test_paraphrase_not_admitted(self):
  d=extract_html(b'<title>Example</title><article><p>A good idea.</p></article>','article')
  self.assertFalse(whole_statement_matches('A fine idea.',d))
 def test_ambiguous_and_overlapping_order_fails(self):
  self.assertFalse(ordered_nonoverlapping([[{'span':[0,9]},{'span':[10,19]}]]))
  self.assertFalse(ordered_nonoverlapping([[{'span':[4,10]}],[{'span':[8,18]}]]))
  self.assertTrue(ordered_nonoverlapping([[{'span':[4,10]}],[{'span':[11,18]}]]))
 def test_every_gate_combination(self):
  keys=['source_authority','english_statements_unique_complete','fl_statements_unique_complete','ordered_nonoverlapping','current_raw_fl','independent_semantic_review','component_novel']
  for vs in product((False,True),repeat=7):
   r=gates(**dict(zip(keys,vs,strict=True)));dev=all(vs[:4])
   self.assertEqual(r['development_correspondence_review_eligible'],dev)
   self.assertEqual(r['current_raw_reference_eligible'],dev and vs[4])
   self.assertEqual(r['semantic_training_eligible'],dev and vs[4] and vs[5])
   self.assertEqual(r['untouched_test_eligible'],all(vs))
 def test_hyphenated_tokens_and_offsets_are_hypotheses(self):
  result=positional_hypotheses('Fa so la.','A thirty-two.',fl_offset=5,english_offset=10)
  self.assertEqual(len(result),3);self.assertEqual(result[1]['english_span'],[12,18]);self.assertIn('not a lexical meaning label',result[0]['status'])
  self.assertFalse(positional_hypotheses('Fa.','Two words.'))
if __name__=='__main__':unittest.main()
