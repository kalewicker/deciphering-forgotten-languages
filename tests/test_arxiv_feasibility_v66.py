import unittest
from fl_decipher.arxiv_feasibility_v66 import metadata,first_page_checks,select

CFG={'metadata_url':'https://arxiv.org/abs/0812.0349v1','pdf_url':'https://arxiv.org/pdf/0812.0349v1',
     'expected_title':'Nonlocality without nonlocality','author_family':'weinstein','author_initial':'s','base_id':'0812.0349',
     'citation_year':2008,'post_date_cutoff':'2013-10-28','maximum_pdf_pages':40}
HTML='''<meta name="citation_title" content="Nonlocality without nonlocality"><meta name="citation_author" content="Steven Weinstein"><meta name="citation_arxiv_id" content="0812.0349"><meta name="citation_date" content="2008/12/01"><div class="submission-history"><b>[v1]</b> Mon, 1 Dec 2008 12:00:00 UTC (10 KB)</div>'''
def receipt(kind='metadata'):
    return {'transport_complete':True,'http_status':200,'num_redirects':0,'final_url':CFG[kind+'_url'],'content_type':'text/html; charset=utf-8' if kind=='metadata' else 'application/pdf'}


class ArxivFeasibilityTests(unittest.TestCase):
    def test_native_record_passes_without_inferring_citation_version(self):
        r=metadata(HTML.encode(),receipt(),CFG)
        self.assertTrue(r['passed']);self.assertTrue(r['citation_version_unspecified']);self.assertFalse(r['actual_fl_source_edition_established'])

    def test_wrong_or_duplicate_title_fails(self):
        for html in [HTML.replace('Nonlocality without nonlocality','Wrong'),HTML+'<meta name="citation_title" content="Nonlocality without nonlocality">']:
            self.assertFalse(metadata(html.encode(),receipt(),CFG)['checks']['single_matching_title'])

    def test_author_and_id_mismatch_fail(self):
        r=metadata(HTML.replace('Steven Weinstein','Alan Other').replace('content="0812.0349"','content="0812.0348"').encode(),receipt(),CFG)
        self.assertFalse(r['checks']['single_compatible_author']);self.assertFalse(r['checks']['single_matching_arxiv_identifier'])

    def test_missing_invalid_duplicate_or_nonconsecutive_history_fails(self):
        for html in [HTML.replace('class="submission-history"','class="other"'),HTML.replace('1 Dec 2008','99 Dec 2008'),HTML.replace('[v1]','[v0]'),HTML.replace('[v1]','[v2]'),HTML.replace('</div>','<b>[v1]</b> Mon, 1 Dec 2008 12:00:00 UTC</div>')]:
            self.assertFalse(metadata(html.encode(),receipt(),CFG)['checks']['complete_consistent_version_history'])

    def test_year_and_weekday_checks(self):
        self.assertFalse(metadata(HTML.replace('2008','2009').encode(),receipt(),CFG)['passed'])
        self.assertFalse(metadata(HTML.replace('Mon,','Tue,').encode(),receipt(),CFG)['passed'])

    def test_redirect_or_version_stripping_transport_rejected(self):
        for r in [receipt()|{'num_redirects':1},receipt()|{'final_url':'https://arxiv.org/abs/0812.0349'},receipt()|{'http_status':403}]:
            self.assertFalse(metadata(HTML.encode(),r,CFG)['checks']['complete_exact_native_html'])

    def test_pdf_version_title_author_and_page_bounds(self):
        text='arXiv:0812.0349v1 Nonlocality without nonlocality Steven Weinstein'
        self.assertTrue(first_page_checks(text,4,4,receipt('pdf'),CFG,['Steven Weinstein'])['passed'])
        for bad in [text.replace('v1','v2'),text.replace('Nonlocality','Other'),text.replace('Steven','Someone')]:
            self.assertFalse(first_page_checks(bad,4,4,receipt('pdf'),CFG,['Steven Weinstein'])['passed'])
        self.assertFalse(first_page_checks(text,41,41,receipt('pdf'),CFG,['Steven Weinstein'])['passed'])
        self.assertFalse(first_page_checks(text,4,5,receipt('pdf'),CFG,['Steven Weinstein'])['passed'])

    def test_selection_is_reference_order_not_global_occurrence_order(self):
        inv={'references':[{'reference_id':0,'span':[1,2],'text':'entry','identifier_occurrence_ids':[1,0]}],
             'identifier_occurrences':[{'identifier':'arxiv:2222.2222','kind':'arxiv','token_span':[1,2],'declared_version':None},
                                       {'identifier':'arxiv:1111.1111','kind':'arxiv','token_span':[1,2],'declared_version':None}]}
        self.assertEqual(select(inv)['identifier'],'arxiv:1111.1111')

    def test_no_valid_identifier_abstains(self):
        self.assertIsNone(select({'references':[],'identifier_occurrences':[]}))
