import hashlib
import unittest
from fl_decipher.textual_references_v65 import recover
from fl_decipher.passage_presence_v68 import target_scope,source_scope,Matcher,assess,tokens,MARKER
from bs4 import BeautifulSoup


def target(html):
    raw=('<div class="post-body">'+html+'</div>').encode();text=BeautifulSoup(raw,'html.parser').div.get_text(' ',strip=True)
    e={'text':text,'parent_sha256':hashlib.sha256(raw).hexdigest(),'text_sha256':hashlib.sha256(text.encode()).hexdigest()}
    return raw,e,recover(raw,e,[])
def pages(*texts):return source_scope([{'page':i+1,'text':s} for i,s in enumerate(texts)])


class PassagePresenceTests(unittest.TestCase):
    def test_complete_structural_scope_keeps_repeated_and_opaque_blocks(self):
        raw,e,i=target('<center>copy</center><div align="center">title</div><div align="justify">same</div><div align="justify">same</div><div align="justify">å opaque</div><div>Aissen, Judith (2003).</div><div align="justify">tail</div>')
        t=target_scope(raw,e,i)
        self.assertEqual([b['text'] for b in t['blocks']],['same','same','å opaque']);self.assertEqual(len(t['ledger']),7)
        self.assertNotEqual(t['blocks'][0]['body_span'],t['blocks'][1]['body_span'])

    def test_boundary_and_export_mismatch_refused(self):
        raw,e,i=target('<div align="justify">text</div><div>Aissen, Judith (2003).</div>')
        i['boundary_match_run_ids']=[]
        with self.assertRaises(ValueError):target_scope(raw,e,i)
        raw,e,i=target('<div align="justify">text</div><div>Aissen, Judith (2003).</div>');e['text']='changed'
        with self.assertRaises(ValueError):target_scope(raw,e,i)

    def test_complete_twelve_token_windows_and_short_block_primary(self):
        text=' '.join(map(str,range(14)));t=target_scope(*target('<div align="justify">'+text+'</div><div align="justify">short</div><div>Aissen, Judith (2003).</div>'))
        self.assertEqual([b['secondary_query_count'] for b in t['blocks']],[3,0]);self.assertEqual(len(t['queries']),5)
        self.assertTrue(all(len(q['normalized_tokens'])==12 for q in t['queries'] if q['kind']=='window12'))

    def test_unicode_case_and_whitespace_normalization(self):
        m=Matcher(pages('Straße  CAFÉ\nword'))
        self.assertTrue(m.hits(['strasse','café','word']))
        self.assertEqual(tokens('CAFE\u0301')[0]['normalized'],'café')

    def test_punctuation_and_hyphenation_are_literal(self):
        m=Matcher(pages('word, non-\nlocality'))
        self.assertEqual(m.hits(['word']),[]);self.assertEqual(m.hits(['nonlocality']),[])

    def test_overlapping_occurrences_and_original_spans(self):
        m=Matcher(pages('a a a'))
        self.assertEqual([h['source_token_span'] for h in m.hits(['a','a'])],[[0,2],[1,3]])
        self.assertEqual([h['page_spans'][0]['span'] for h in m.hits(['a','a'])],[[0,3],[2,5]])

    def test_cross_page_and_empty_page_document_coordinates(self):
        s=pages('first a','','b last');h=Matcher(s).hits(['a','b'])[0]
        self.assertEqual(h['page_spans'],[{'page':1,'span':[6,7],'quote':'a'},{'page':3,'span':[0,1],'quote':'b'}])
        self.assertEqual(h['document_span'],[6,10])

    def test_controls_use_own_page_prefix_and_global_negative(self):
        t=target_scope(*target('<div align="justify">not present</div><div>Aissen, Judith (2003).</div>'))
        r=assess(t,pages('a b c','a b c'))
        self.assertTrue(r['controls_passed']);self.assertEqual(len(r['positive_controls']),2);self.assertFalse(r['results'][0]['present'])

    def test_empty_source_or_marker_collision_fails_controls(self):
        t=target_scope(*target('<div align="justify">text</div><div>Aissen, Judith (2003).</div>'))
        self.assertFalse(assess(t,pages(''))['controls_passed'])
        self.assertFalse(assess(t,pages(MARKER+' word'))['controls_passed'])
        with self.assertRaises(ValueError):Matcher(pages('a')).hits([])

    def test_indexed_matcher_equals_exhaustive_sequences(self):
        values=['a','b','a','b','a','c']*5;s=pages(' '.join(values));matcher=Matcher(s)
        for n in [1,2,11,12,13,25]:
            for start in range(0,len(values)-n+1,3):
                q=values[start:start+n];expected=[[i,i+n] for i in range(len(values)-n+1) if values[i:i+n]==q]
                self.assertEqual([h['source_token_span'] for h in matcher.hits(q)],expected)
