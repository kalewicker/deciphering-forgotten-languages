import unittest
from fl_decipher.native_quote_v42 import inspect_page


class NativeQuoteTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {'source_url': 'https://example.org/article/', 'expected_title': 'A title',
                    'quote': {'text': 'A complete quotation'}, 'minimum_visible_characters': 1,
                    'challenge_signatures': ['verify you are human']}
        self.receipt = {'transport_complete': True, 'final_url': self.cfg['source_url']}

    def page(self, body, canonical='https://example.org/article/'):
        return (f'<html><head><link rel="canonical" href="{canonical}"></head>'
                f'<body><h1>A title</h1>{body}</body></html>').encode()

    def test_transport_or_identity_failure_is_unavailable_not_absence(self):
        raw = self.page('<p>A complete quotation</p>')
        result = inspect_page(raw, {'transport_complete': False}, self.cfg)
        self.assertIsNone(result['quote_present'])
        result = inspect_page(self.page('<p>A complete quotation</p>', 'https://other.org/'), self.receipt, self.cfg)
        self.assertFalse(result['material_available'])
        self.assertIsNone(result['quote_present'])

    def test_embedded_script_is_excluded_and_split_paragraphs_do_not_form_quote(self):
        raw = self.page('<script>A complete quotation</script><p>A complete</p><p>different quotation</p>')
        result = inspect_page(raw, self.receipt, self.cfg)
        self.assertTrue(result['material_available'])
        self.assertFalse(result['quote_present'])
        self.assertNotIn('A complete quotation', result['text'])

    def test_attribution_window_and_body_witnesses_are_preserved(self):
        raw = self.page('<p>Gorham explains.</p><p>“A complete quotation,” he says.</p><p>Next context.</p>')
        result = inspect_page(raw, self.receipt, self.cfg)
        self.assertTrue(result['quote_present'])
        context = result['contexts'][0]
        self.assertTrue(context['gorham_name_visible'] and context['he_says_visible'])
        self.assertEqual([p['paragraph_index'] for p in context['window']], [0, 1, 2])
        for span in context['body_paragraph_spans']:
            self.assertEqual(result['text'][slice(*span)], context['quote_paragraph'])
        self.assertFalse(context['attribution_authenticated'])
