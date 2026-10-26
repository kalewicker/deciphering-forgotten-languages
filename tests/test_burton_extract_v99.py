import unittest
from fl_decipher.burton_extract_v99 import extract,score
class ExtractTests(unittest.TestCase):
 def test_shared_container_unlabelled_anchor(self):
  t,p=extract('before<span class="pagenum"><a id="Page_2"></a><a id="Page_3"></a>[Pg 3]middle</span>after')
  self.assertEqual(t,'beforemiddleafter');self.assertEqual([x['label_status'] for x in p],['unlabelled','labelled']);self.assertEqual([x['text_offset'] for x in p],[6,6])
 def test_nested_container_keeps_prose(self):
  t,p=extract('<span class="pagenum"><a id="Page_1"></a>[Pg 1]one<span class="pagenum"><a id="Page_2"></a>[Pg 2]two</span>three</span>')
  self.assertEqual(t,'onetwothree');self.assertEqual(p[1]['text_offset'],3)
 def test_inline_whitespace_and_roman(self):
  t,p=extract('a<span class="pagenum"><a id="Page_iv"></a> [Pg iv] b</span>c')
  self.assertEqual(t,'a  bc');self.assertEqual(p[0]['label'],'[Pg iv]')
 def test_wrong_label_rejected(self):
  with self.assertRaises(AssertionError):extract('<a id="Page_1"></a>[Pg 2]')
 def test_missing_label_explicit(self):
  t,p=extract('<a id="Page_1"></a>text');self.assertEqual(t,'text');self.assertEqual(p[0]['label_status'],'unlabelled')
 def test_unrelated_label_text_retained(self):self.assertEqual(extract('a [Pg 2] b')[0],'a [Pg 2] b')
 def test_exclusions_boundaries(self):self.assertEqual(extract('<p>a<i>b</i><br>c<script>x</script></p>')[0],'\nab\nc\n')
 def test_fixed_matching_no_join_and_no_punctuation_repair(self):
  r=score(['a b','c—d'],['b c','c-d','a b']);self.assertEqual(r['literal']['matched'],1)
