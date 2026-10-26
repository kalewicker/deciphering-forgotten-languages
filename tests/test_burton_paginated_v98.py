import unittest
from fl_decipher.burton_paginated_v98 import extract,matches
class BurtonTests(unittest.TestCase):
 def test_inline_page_label_removed_without_space(self):
  text,pages=extract('ab<span class="pagenum"><a id="Page_252"></a>[Pg 252]</span><i>cd</i>')
  self.assertEqual(text,'abcd');self.assertEqual(pages[0]['text_offset'],2)
 def test_label_conflict_rejected(self):
  with self.assertRaises(AssertionError):extract('<span class="pagenum"><a id="Page_252"></a>[Pg 253]</span>')
 def test_junction_cannot_match(self):self.assertEqual(matches(['abc','def'],['cde'])['matched'],0)
 def test_order_jump_missing_duplicate(self):
  r=matches(['ab ab','cd'],['ab','missing','ab','cd','ab'])
  self.assertEqual(r['matched'],4);self.assertEqual(r['ordered_matched'],3)
 def test_hidden_and_blocks(self):
  text,pages=extract('<p>a<i>b</i><br>c<script>bad</script><!--bad--></p>')
  self.assertEqual(text,'\nab\nc\n')
 def test_no_spelling_repair(self):self.assertEqual(matches(['word—word'],['word-word'])['matched'],0)
