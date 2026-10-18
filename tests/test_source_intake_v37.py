import unittest
from fl_decipher.source_intake_v37 import identity, search_hits, nominate, citation, citation_metadata, select_sources, source_material


class IntakeTests(unittest.TestCase):
    def test_permalink_identity_preserves_real_query(self):
        self.assertEqual(identity('http://example.org/x?m=0#p'), identity('https://example.org/x'))
        self.assertNotEqual(identity('https://example.org/x?a=1'), identity('https://example.org/x?a=2'))
        self.assertIsNone(identity('https://user:password@example.org/x'))

    def test_only_organic_dated_posts_and_fixed_two_slots(self):
        host = 'https://forgottenlanguages-full.forgottenlanguages.org'
        response = '\n'.join(f'Title ({host}{path})\nREF [wordlim: 200] excerpt' for path in ['/2020/01/', '/2020/01/a.html', '/2020/01/b.html', '/2020/01/c.html'])
        result = nominate([{'query_index': 0, 'response': response}, {'query_index': 1, 'response': 'Empty search results'}], [])
        self.assertEqual(len(result['nominees']), 2)
        self.assertEqual([r['rank'] for r in result['nominees']], [1, 2])
        self.assertEqual(result['hit_ledger'][-1]['exclusion_reason'], 'outside_two_post_slots')
        self.assertEqual(sum(s['post_id'] is None for s in result['slots']), 2)

    def test_explicit_identifier_versions_and_pdf_route(self):
        c = citation('http://arxiv.org/abs/hep-ph/0209057v1')
        self.assertEqual(c['identifier'], 'arxiv:hep-ph/0209057')
        self.assertEqual(c['request_url'], 'https://arxiv.org/pdf/hep-ph/0209057v1')
        self.assertEqual(citation('https://arxiv.org/pdf/2301.12345v2.pdf')['identifier'], 'arxiv:2301.12345')
        self.assertIsNone(citation('https://unverified-upload.example/paper.pdf'))

    def test_body_links_in_document_order_and_no_navigation(self):
        html = '<a href="https://doi.org/10.1234/nav">navigation</a><div class="post-body">https://arxiv.org/abs/2001.12345 <a href="https://doi.org/10.1234/next">next</a></div>'
        m = citation_metadata(html)
        self.assertEqual([c['identifier'] for c in m['eligible_citations']], ['arxiv:2001.12345', 'doi:10.1234/next'])

    def test_exposed_identifier_not_renominated_as_new_version(self):
        posts = [{'post_id': 'p', 'metadata': {'eligible_citations': [citation('https://arxiv.org/abs/2001.12345v2'), citation('https://doi.org/10.1234/new')]}}]
        result = select_sources(posts, {'urls': ['https://arxiv.org/pdf/2001.12345v1']})
        self.assertEqual(len(result['selected']), 1)
        self.assertEqual(result['candidate_ledger'][0]['exclusion_reason'], 'known_exposed_identifier_or_url')

    def test_first_four_are_fixed_without_success_based_replacement(self):
        posts = [{'post_id': 'p', 'metadata': {'eligible_citations': [citation(f'https://doi.org/10.1234/{i}') for i in range(6)]}}]
        result = select_sources(posts, {'urls': []})
        self.assertEqual(len(result['selected']), 4)
        self.assertEqual(result['candidate_ledger'][4]['exclusion_reason'], 'four_work_cap_reached')
        self.assertTrue(all(not s['untouched_test_eligible'] for s in result['selected']))

    def test_pdf_magic_does_not_admit_verified_prose(self):
        result = source_material(b'%PDF-1.7 fixture', {'transport_complete': True})
        self.assertEqual(result['representation'], 'raw_pdf_unreviewed')
        self.assertFalse(result['source_prose_verified'])
        self.assertFalse(result['review_ready'])

    def test_transport_failure_is_retained(self):
        self.assertFalse(source_material(b'%PDF-', {'transport_complete': False})['transport_available'])


if __name__ == '__main__':
    unittest.main()
