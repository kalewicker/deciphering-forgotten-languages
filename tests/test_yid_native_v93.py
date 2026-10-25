import unittest
from fl_decipher.yid_native_v93 import assess,compare,normalize
U='https://example.org/post'
def page(body,extra=''):return (f'<link rel="canonical" href="{U}">'+extra+'<div class="post-body">'+body+'</div>').encode()
class NativeTests(unittest.TestCase):
 def test_inline_unicode_and_blocks(self):
  r=assess(page('<p>α<span>β</span><br>γ</p>'),U,U,U,['αβ\nγ'])
  self.assertEqual(r['comparison']['literal']['matched'],1)
  self.assertEqual(''.join(c['text'] for c in r['extraction_chunks']),r['extracted_text'])
 def test_hidden_excluded(self):
  r=assess(page('a<script>bad</script><style>bad</style><noscript>bad</noscript><template>bad</template><!--bad-->b'),U,U,U,['ab','bad'])
  self.assertEqual(r['comparison']['literal']['matched'],1)
 def test_identity_conflict_and_unknown(self):
  for extra,final in [('<meta property="og:url" content="other">',U),('',None)]:
   self.assertIsNone(assess(page('a',extra),U,U,final,['a'])['comparison'])
 def test_body_count_not_zero_matches(self):
  r=assess(page('a','<div class="post-body">b</div>'),U,U,U,['a'])
  self.assertFalse(r['admissible']);self.assertIsNone(r['comparison'])
 def test_whitespace_separate(self):
  r=assess(page('a\u00a0  b'),U,U,U,['a b'])
  self.assertEqual(r['comparison']['literal']['matched'],0);self.assertEqual(r['comparison']['whitespace']['matched'],1)
 def test_order_missing_duplicates(self):
  r=compare('aba aba',['aba','missing','aba','aba'])
  self.assertEqual(r['matched'],3);self.assertEqual(r['ordered_matched'],2);self.assertEqual(r['rows'][0]['count'],2)
 def test_invalid_utf8(self):self.assertIsNone(assess(b'\xff',U,U,U,['a'])['comparison'])
 def test_no_case_or_accent_repair(self):self.assertNotEqual(normalize('Á'),normalize('a'))
