import hashlib
import unittest
from bs4 import BeautifulSoup
from fl_decipher.textual_references_v65 import recover


def fixture(html):
    raw=('<div class="post-body">'+html+'</div>').encode()
    body=BeautifulSoup(raw,'html.parser').select_one('div.post-body')
    for t in body.find_all(['script','style','noscript']):t.decompose()
    text=body.get_text(' ',strip=True)
    export={'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'parent_sha256':hashlib.sha256(raw).hexdigest()}
    return raw,export


class TextualReferencesTests(unittest.TestCase):
    def recover(self,html,known=()):return recover(*fixture(html),known)

    def test_repeated_text_gets_distinct_spans(self):
        r=self.recover('<div>same</div><div>same</div>')
        self.assertEqual([x['span'] for x in r['runs']],[[0,4],[5,9]])

    def test_tail_keeps_unresolved_and_nested_text(self):
        r=self.recover('<div>before</div><div>Aissen, Judith (2003). <b>Title</b></div><div>malformed entry</div>')
        self.assertEqual(len(r['references']),2)
        self.assertEqual(r['references'][0]['year_witnesses'][0]['literal'],'2003')
        self.assertEqual(r['references'][1]['resolution_status'],'no_recognized_direct_identifier')

    def test_missing_or_ambiguous_boundary_abstains(self):
        for html in ['<div>no marker</div>','<div>Aissen, Judith (2003).</div>'*2]:
            r=self.recover(html)
            self.assertEqual(r['references'],[])
            self.assertEqual(r['tail_status'],'unresolved_boundary')

    def test_versions_duplicates_and_known_registry(self):
        r=self.recover('<div>arXiv.org:0812.0349. arxiv:0812.0349v2; arxiv:hep-ph/0209057v1</div>', ['https://arxiv.org/abs/0812.0349'])
        o=r['identifier_occurrences']
        self.assertEqual([x['declared_version'] for x in o],[None,'v2','v1'])
        self.assertEqual(o[1]['duplicate_of_occurrence'],0)
        self.assertEqual(o[0]['literal'],'0812.0349')
        self.assertEqual(r['known_identifier_matches'],['arxiv:0812.0349'])

    def test_malformed_and_cross_owner_rejected(self):
        r=self.recover('<div>arxiv:bad arxiv:0812.0349evil arxiv:0812.0349v0</div><div>arxiv:</div><div>0812.0349</div>')
        self.assertEqual(r['recognized_identifiers'],[])
        self.assertEqual([x['status'] for x in r['identifier_occurrences']],['malformed_identifier']*3+['cross_run_token'])

    def test_runtime_and_comments_excluded(self):
        r=self.recover('<div>yes<!--arxiv:0812.0349--><script>arxiv:0812.0349</script><style>bad</style><noscript>bad</noscript></div>')
        self.assertEqual(r['unicode_characters'],3)
        self.assertEqual(r['identifier_occurrences'],[])

    def test_doi_overlap_and_bare_doi(self):
        r=self.recover('<div>doi:10.1234/abc; https://doi.org/10.1234/abc 10.55555/xyz doi:bad</div>')
        self.assertEqual(len(r['identifier_occurrences']),4)
        self.assertEqual(r['recognized_identifiers'],['doi:10.1234/abc','doi:10.55555/xyz'])
        self.assertEqual(r['identifier_occurrences'][1]['duplicate_of_occurrence'],0)

    def test_changed_export_refused(self):
        raw,e=fixture('<div>hello</div>');e['text']='changed'
        with self.assertRaises(ValueError):recover(raw,e,[])
