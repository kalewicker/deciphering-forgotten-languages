import unittest
from fl_decipher.heading_scope_v51 import audit

URL = 'https://physicsworld.com/a/fixture/'
SELECTOR = 'article[id^="post-"] > div.entry-content'


def page(content, title='A title', og='A title', canonical=URL, extra=''):
    return (f'<html><head><title>{title} – Physics World</title><meta property="og:title" content="{og}">'
            f'<link rel="canonical" href="{canonical}"><meta property="og:url" content="{URL}">{extra}</head>'
            f'<body><article id="post-1"><div class="entry-content">{content}</div></article></body></html>').encode()


def inspect(raw): return audit(raw, 'A title', URL, URL, SELECTOR)


class HeadingScopeTests(unittest.TestCase):
    def test_metadata_agreement_does_not_create_a_missing_h1_or_eligibility(self):
        result = inspect(page('<p>Body.</p>'))
        self.assertTrue(result['descriptive_metadata_agreement']); self.assertEqual(result['h1_count'], 0)
        self.assertNotIn('ready_for_future_registration', result)

    def test_conflicting_empty_title_or_identity_does_not_count_as_agreement(self):
        for raw in [page('<p>Body.</p>', og='Other title'), page('<p>Body.</p>', og=''),
                    page('<p>Body.</p>', canonical='https://physicsworld.com/a/other/')]:
            self.assertFalse(inspect(raw)['descriptive_metadata_agreement'])

    def test_jsonld_article_only_graph_and_malformed_scripts_preserved(self):
        extra = '<script type="application/ld+json">{"@graph":[{"@type":"NewsArticle","headline":"A title"},{"@type":"Thing","headline":"Other"}]}</script>'
        extra += '<script type="application/ld+json">broken</script>'
        result = inspect(page('<p>Body.</p>', extra=extra))
        self.assertEqual(len(result['article_jsonld_records']), 1); self.assertEqual(len(result['jsonld_errors']), 1)
        self.assertIn('article_headline', result['nonempty_metadata_title_families'])

    def test_split_body_title_and_all_duplicate_occurrences_have_original_spans(self):
        result = inspect(page('<h2>A <span>title</span></h2><p>A title</p>'))
        self.assertEqual(len(result['body_title_occurrences']), 2)
        self.assertEqual(result['h1_count'], 0)
        for r in result['body_title_occurrences']: self.assertEqual(result['body_text'][slice(*r['span'])], 'A title')

    def test_inline_direct_p_leaves_stay_included_nested_paragraphs_do_not(self):
        result = inspect(page('<p>One <em>inline</em> tail.</p><div><p>Nested.</p></div><p></p>'))
        self.assertEqual(result['included_leaf_count'], 3); self.assertEqual(result['excluded_leaf_count'], 1)
        self.assertEqual(result['direct_p_text'], 'One inline tail.')
        self.assertEqual(len(result['paragraph_units']), 2)

    def test_excluded_categories_and_form_priority_are_exhaustive(self):
        content = '<h2>Section</h2><figure><figcaption>Caption</figcaption></figure><blockquote>Quote</blockquote>'
        content += '<ul><li>List</li></ul><table><tr><td>Cell</td></tr></table><form><ul><li>Form list</li></ul></form>Loose'
        result = inspect(page(content))
        self.assertEqual(result['excluded_category_counts'], {'blockquote': 1, 'figure': 1, 'form': 1, 'heading': 1, 'list': 1, 'other': 1, 'table': 1})
        self.assertEqual(sum(result['excluded_category_characters'].values()), sum(len(r['stripped_text']) for r in result['text_leaves']))

    def test_comments_and_scripts_are_not_static_text_leaves(self):
        result = inspect(page('<p>Body<!-- hidden -->.</p><script>Secret</script>'))
        self.assertEqual(result['container_text'], 'Body .'); self.assertTrue(result['all_static_container_text_in_direct_p'])

    def test_duplicate_paragraph_mapping_and_ambiguous_container_are_explicit(self):
        result = inspect(page('<p>Repeat</p><p>Repeat</p>'))
        self.assertTrue(all(p['span'] is None and p['body_mapping_count'] == 2 for p in result['paragraph_units']))
        with self.assertRaises(ValueError): inspect(b'<html><body></body></html>')
