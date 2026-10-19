import unittest
from fl_decipher.publisher_intake_v50 import article_key, inspect_page, nominate, publication_dates, response_text, result_headers, topical


def hit(title, slug):
    return f'{title} (https://physicsworld.com/a/{slug}/)\nmarker [wordlim: 200] Published: earlier\nAntarctic neutrinos coverage.\n\n'


class PublisherIntakeTests(unittest.TestCase):
    def test_only_exact_native_article_urls_are_accepted(self):
        self.assertEqual(article_key('https://physicsworld.com/a/example'), 'https://physicsworld.com/a/example/')
        for bad in ['http://physicsworld.com/a/x/', 'https://physicsworld.com.evil/a/x/', 'https://x@physicsworld.com/a/x/',
                    'https://physicsworld.com:444/a/x/', 'https://physicsworld.com/a/x/?q=1', 'https://physicsworld.com/a/x/#z',
                    'https://physicsworld.com/a/', 'https://physicsworld.com/a/x/y/', None]:
            self.assertIsNone(article_key(bad))

    def test_topical_words_do_not_match_substrings(self):
        self.assertTrue(topical('ANITA neutrino'))
        self.assertTrue(topical('Antarctic NEUTRINOS'))
        self.assertFalse(topical('anitarian neutrinoid'))
        self.assertFalse(topical('neutrinos only'))

    def test_header_attribution_keeps_exact_spans_and_supported_text_blocks(self):
        text = 'preamble\n' + hit('ANITA neutrinos', 'one') + hit('Antarctic neutrino radio', 'two')
        rows = result_headers(text)
        self.assertEqual(len(rows), 2)
        for r in rows: self.assertEqual(text[slice(*r['response_span'])], r['response_text'])
        self.assertEqual(response_text({'content': [{'type': 'text', 'text': text}]}), text)
        self.assertIsNone(response_text({'unexpected': text}))
        self.assertEqual(result_headers('Title (https://physicsworld.com/a/x/)\nno metadata'), [])

    def test_first_appearances_caps_old_source_and_exposure_are_preserved(self):
        old = 'https://physicsworld.com/a/old/'; linked = 'https://physicsworld.com/a/a/'
        prior = {'captured_article_keys': [old], 'article_exposures': {linked: ['prior_raw_link']}}
        responses = [{'error': None, 'response': hit('ANITA neutrino', 'old') + hit('ANITA neutrino', 'a') + hit('ANITA neutrino', 'b') + hit('ANITA neutrino', 'c')},
                     {'error': None, 'response': hit('ANITA neutrino', 'a') + hit('ANITA neutrino', 'c') + hit('ANITA neutrino', 'd')}]
        result = nominate(responses, prior, 2)
        self.assertEqual([s['nominee']['url'] if s['nominee'] else None for s in result['slots']],
                         [linked, 'https://physicsworld.com/a/b/', 'https://physicsworld.com/a/d/', None])
        self.assertEqual(result['slots'][0]['nominee']['prior_exposure_tags'], ['prior_raw_link'])
        self.assertEqual(result['queries'][1]['hits'][1]['decision_reason'], 'duplicate_returned_url')

    def test_search_failure_and_unsupported_response_keep_empty_slots(self):
        result = nominate([{'error': 'failure', 'response': ''}, {'error': None, 'response': {'bad': 1}}],
                          {'captured_article_keys': [], 'article_exposures': {}}, 2)
        self.assertEqual(len(result['slots']), 4); self.assertEqual(result['occupied_slots'], 0)

    def test_publication_dates_missing_conflicting_or_invalid_fail(self):
        self.assertEqual(publication_dates(['2018-07-17T13:03:49Z']), (['2018-07-17'], True))
        for values in [[], ['nonsense'], ['2018-01-01', '2019-01-01']]: self.assertFalse(publication_dates(values)[1])

    def page(self, canonical='https://physicsworld.com/a/test/', published='2018-07-17', text='Antarctic neutrinos paragraph', title='A title'):
        return (f'<html><head><link rel="canonical" href="{canonical}"><meta property="article:published_time" content="{published}"></head>'
                f'<body><h1>{title}</h1><article id="post-1"><div class="entry-content"><p>{text}</p><p>Second body.</p><p>Third body.</p>'
                '<form><p>Nested excluded.</p></form></div></article></body></html>').encode()

    def config(self):
        return {'source_selector': 'article[id^="post-"] > div.entry-content', 'minimum_paragraphs': 3, 'minimum_paragraph_characters': 1,
                'date_min': '2000-01-01', 'date_max': '2018-09-30', 'challenge_signatures': ['verify you are human']}

    def test_native_scope_uses_all_direct_paragraphs_and_exact_title_identity(self):
        result = inspect_page(self.page(), {'transport_complete': True, 'final_url': 'https://physicsworld.com/a/test/'},
                              {'url': 'https://physicsworld.com/a/test/', 'title': 'A title – Physics World'}, self.config())
        self.assertTrue(result['ready_for_future_registration']); self.assertEqual(result['paragraph_count'], 3)
        self.assertNotIn('Nested excluded.', [p['text'] for p in result['paragraph_units']])
        for p in result['paragraph_units']: self.assertEqual(result['body_text'][slice(*p['span'])], p['text'])

    def test_native_transport_date_identity_title_and_challenge_failures(self):
        nominee = {'url': 'https://physicsworld.com/a/test/', 'title': 'A title'}
        receipt = {'transport_complete': True, 'final_url': nominee['url']}
        for raw in [self.page(published='2020-01-01'), self.page(published='bad'), self.page(canonical='https://physicsworld.com/a/other/'),
                    self.page(title='Wrong title'), self.page(text='verify you are human')]:
            self.assertFalse(inspect_page(raw, receipt, nominee, self.config())['ready_for_future_registration'])
        self.assertFalse(inspect_page(self.page(), receipt | {'transport_complete': False}, nominee, self.config())['ready_for_future_registration'])

    def test_ambiguous_paragraph_mapping_cannot_become_feasible(self):
        raw = self.page().replace(b'<p>Third body.</p>', b'<p>Second body.</p>')
        result = inspect_page(raw, {'transport_complete': True, 'final_url': 'https://physicsworld.com/a/test/'},
                              {'url': 'https://physicsworld.com/a/test/', 'title': 'A title'}, self.config())
        self.assertFalse(result['checks']['unique_nonempty_paragraph_mapping'])
