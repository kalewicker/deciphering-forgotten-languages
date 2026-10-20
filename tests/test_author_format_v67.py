import unittest
from fl_decipher.arxiv_feasibility_v66 import metadata
from fl_decipher.author_format_v67 import parse_author, author_witnesses, assess_metadata, assess_first_page

CFG={'metadata_url':'https://arxiv.org/abs/0812.0349v1','pdf_url':'https://arxiv.org/pdf/0812.0349v1',
     'expected_title':'Nonlocality without nonlocality','author_family':'weinstein','author_initial':'s','base_id':'0812.0349',
     'citation_year':2008,'post_date_cutoff':'2013-10-28','maximum_pdf_pages':40}
HTML='''<meta name="citation_title" content="Nonlocality without nonlocality"><meta name="citation_author" content="Weinstein, Steven"><meta name="citation_arxiv_id" content="0812.0349"><meta name="citation_date" content="2008/12/01"><div class="submission-history"><b>[v1]</b> Mon, 1 Dec 2008 12:00:00 UTC (10 KB)</div>'''
def receipt(kind='metadata'):
    return {'transport_complete':True,'http_status':200,'num_redirects':0,'final_url':CFG[kind+'_url'],'content_type':'text/html; charset=utf-8' if kind=='metadata' else 'application/pdf'}


class AuthorFormatTests(unittest.TestCase):
    def test_both_author_orders_parse_to_same_components(self):
        a=parse_author('Weinstein, Steven');b=parse_author(' Steven   Weinstein ')
        self.assertEqual((a['given'],a['family']),(b['given'],b['family']))
        self.assertEqual(a['form'],'family_comma_given')

    def test_initials_middle_names_and_internal_punctuation(self):
        self.assertEqual(parse_author('Weinstein, S. A.')['given'],['s','a'])
        self.assertEqual(parse_author("Anne-Marie O'Neill")['family'],"o'neill")

    def test_ambiguous_lists_suffixes_and_malformed_tokens_abstain(self):
        for value in ['',None,'Weinstein','W, Steven','Weinstein,',' , Steven','Weinstein, Steven, Jr.','Steven and Alan Weinstein',
                      'Steven Weinstein; Alan Other','Steven & Alan Weinstein','Steven / Weinstein','Steven1 Weinstein','Steven Weinstein Jr.',
                      'Steven Weinstein III','Weinstein, Steven Other, Alan','Steven.. Weinstein','van Weinstein, Steven','李 明']:
            with self.subTest(value=value):self.assertIsNone(parse_author(value))

    def test_corrected_gate_preserves_exact_failed_e66_replay(self):
        raw=HTML.encode();old=metadata(raw,receipt(),CFG);r=assess_metadata(raw,receipt(),CFG,old)
        self.assertFalse(old['passed']);self.assertTrue(r['passed']);self.assertEqual(r['e66_metadata_replay'],old)
        for k,v in old['checks'].items():
            if k!='single_compatible_author':self.assertEqual(r['checks'][k],v)

    def test_changed_saved_assessment_is_refused(self):
        raw=HTML.encode();old=metadata(raw,receipt(),CFG);old['passed']=True
        with self.assertRaises(ValueError):assess_metadata(raw,receipt(),CFG,old)

    def test_actual_author_mismatch_or_duplicate_is_still_failure(self):
        for raw in [HTML.replace('Weinstein, Steven','Other, Steven').encode(),HTML.replace('Weinstein, Steven','Weinstein, Alan').encode(),
                    (HTML+'<meta name="citation_author" content="Weinstein, Steven">').encode()]:
            self.assertFalse(assess_metadata(raw,receipt(),CFG,metadata(raw,receipt(),CFG))['passed'])

    def test_non_author_failure_is_not_repaired(self):
        raw=HTML.replace('Nonlocality without nonlocality','Other title').encode()
        r=assess_metadata(raw,receipt(),CFG,metadata(raw,receipt(),CFG))
        self.assertFalse(r['passed']);self.assertIn('single_matching_title',r['unmet'])

    def test_pdf_name_matches_both_forms_and_original_coordinates_are_not_claimed(self):
        name=parse_author('Weinstein, Steven')
        for text in ['Steven\nWeinstein','Weinstein,Steven','Weinstein, Steven']:
            hits=author_witnesses(text,name);self.assertTrue(hits)
            a,b=hits[0]['normalized_span'];self.assertEqual(' '.join(text.casefold().split())[a:b],hits[0]['normalized_witness'])

    def test_pdf_substrings_initial_expansion_and_missing_given_names_rejected(self):
        name=parse_author('Weinstein, Steven Alan')
        for text in ['Steven Weinstein','S. A. Weinstein','Steven Alan Weinsteinson','XSteven Alan Weinstein','Alan Steven Weinstein']:
            self.assertEqual(author_witnesses(text,name),[])

    def test_pdf_identity_and_unchanged_version_transport_bounds(self):
        text='arXiv:0812.0349v1 Nonlocality without nonlocality Steven Weinstein';name=parse_author('Weinstein, Steven')
        self.assertTrue(assess_first_page(text,4,4,receipt('pdf'),CFG,name)['passed'])
        for bad in [text.replace('v1','v2'),text.replace('Nonlocality','Other'),text.replace('Steven','Alan')]:
            self.assertFalse(assess_first_page(bad,4,4,receipt('pdf'),CFG,name)['passed'])
        self.assertFalse(assess_first_page(text,4,5,receipt('pdf'),CFG,name)['passed'])
        self.assertFalse(assess_first_page(text,41,41,receipt('pdf'),CFG,name)['passed'])
        self.assertFalse(assess_first_page(text,4,4,receipt('pdf')|{'num_redirects':1},CFG,name)['passed'])
