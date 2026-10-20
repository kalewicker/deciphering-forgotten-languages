import unittest
from fl_decipher.additional_intake_v55 import article_key, prior_inventory, nominate, alias_plan, prospective_decision, capacity


def hit(slug, title='Antarctic neutrino detector'):
    return f'{title} (https://physicsworld.com/a/{slug}/)\nref [wordlim: 200] Published: unknown\nAntarctic neutrinos.\n\n'


class AdditionalIntakeTests(unittest.TestCase):
    def test_prior_inventory_covers_old_results_and_resolved_links(self):
        prior = prior_inventory({'article_exposures': {'https://physicsworld.com/a/old/': ['known']}},
            {'queries': [{'hits': [{'url': 'https://physicsworld.com/a/search/'}]}]},
            [{'path': 'fixture', 'url': 'https://physicsworld.com/a/native/', 'raw': b'<a href="/a/link/">x</a><a href="https://evil.example/a/other/">x</a>'}])
        self.assertEqual(len(prior['excluded_article_keys']), 4)
        self.assertIn('fixture:link', prior['article_exposures']['https://physicsworld.com/a/link/'])

    def test_first_eligible_one_per_query_and_prior_exclusions(self):
        prior = {'article_exposures': {'https://physicsworld.com/a/old/': ['link']}, 'excluded_article_keys': ['https://physicsworld.com/a/old/']}
        result = nominate([{'error': None, 'response': hit('old') + hit('one') + hit('two')},
                           {'error': None, 'response': hit('two') + hit('three') + hit('four')}], prior)
        self.assertEqual([s['nominee']['url'] for s in result['slots']], ['https://physicsworld.com/a/one/', 'https://physicsworld.com/a/three/'])
        self.assertEqual(result['queries'][0]['hits'][0]['decision_reason'], 'prior_recorded_url_exposure')
        self.assertEqual(result['queries'][1]['hits'][0]['decision_reason'], 'duplicate_returned_url')

    def test_failures_and_unsupported_search_keep_two_empty_slots(self):
        result = nominate([{'error': 'timeout', 'response': ''}, {'error': None, 'response': {'unsupported': 1}}],
                          {'article_exposures': {}, 'excluded_article_keys': []})
        self.assertEqual(len(result['slots']), 2); self.assertEqual(result['occupied_slots'], 0)

    def test_url_safety_has_no_inferred_a_or_query_normalization(self):
        for bad in ['https://physicsworld.com/example/', 'https://physicsworld.com/a/example/?x=1',
                    'http://physicsworld.com/a/example/', 'https://u@physicsworld.com/a/example/',
                    'https://physicsworld.com/a/%65xample/', 'https://physicsworld.com/a/example//']:
            self.assertIsNone(article_key(bad))
        self.assertEqual(article_key('https://physicsworld.com/a/example'), 'https://physicsworld.com/a/example/')

    def page(self, og='https://physicsworld.com/example/', extra=''):
        return (f'<html><head><title>Antarctic neutrinos</title><meta property="og:title" content="Antarctic neutrinos">'
            f'<link rel="canonical" href="https://physicsworld.com/a/example/"><meta property="og:url" content="{og}">'
            '<meta property="article:published_time" content="2017-01-01">'
            '<script type="application/ld+json">{"@type":"Article","headline":"Antarctic neutrinos"}</script>'
            f'{extra}</head><body><article id="post-1"><div class="entry-content">' + '<p>' + 'Antarctic neutrinos. ' * 60 + '</p></div></article></body></html>').encode()

    def specs(self):
        return ({'id': 'fixture', 'url': 'https://physicsworld.com/a/example/', 'expected_title': 'Antarctic neutrinos', 'v50_ready_unchanged': None},
                {'transport_complete': True, 'http_status': 200, 'curl_returncode': 0, 'final_url': 'https://physicsworld.com/a/example/'})

    def test_only_one_safe_observed_alternate_is_reserved(self):
        spec, receipt = self.specs()
        self.assertEqual(alias_plan(self.page(), receipt, spec)['request_url'], 'https://physicsworld.com/example/')
        for raw in [self.page(og=spec['url']), self.page(og='https://evil.example/example/'),
                    self.page(extra='<meta property="og:url" content="https://physicsworld.com/other/">')]:
            self.assertIsNone(alias_plan(raw, receipt, spec)['request_url'])
        self.assertIsNone(alias_plan(self.page(), receipt | {'transport_complete': False}, spec)['request_url'])

    def test_new_route_provenance_does_not_claim_historical_evidence(self):
        spec, receipt = self.specs(); cfg = {'source_selector': 'article[id^="post-"] > div.entry-content',
            'minimum_paragraph_runs': 3, 'minimum_run_characters': 1000, 'date_min': '2000-01-01', 'date_max': '2018-09-30', 'challenge_signatures': []}
        route = {'current_alias_supported': True, 'requested_url': 'https://physicsworld.com/example/',
            'expected_canonical_url': spec['url'], 'final_url': spec['url'], 'category': 'observed_redirect_to_canonical', 'num_redirects': 1,
            'checks': {k: True for k in ['complete_200', 'html_content_type', 'consistent_publisher_chain', 'canonical_matches_frozen', 'three_title_channels_match_frozen']}}
        r = prospective_decision(self.page(), receipt, spec, cfg, route)
        self.assertEqual(r['og_url_bindings'][0]['binding'], 'saved_v55_redirect')
        self.assertEqual(r['route_evidence_origin'], 'v55'); self.assertFalse(r['untouched_test_unit_admitted'])
        self.assertFalse(r['development_capture_eligible'])  # One p cannot satisfy the unchanged three-run minimum.

    def test_capacity_keeps_old_slots_and_excludes_reference(self):
        rows = [{'slot_id': 'q00s00', 'development_capture_eligible': True}, {'slot_id': 'q01s00', 'development_capture_eligible': False}]
        r = capacity(['q01s00', 'q01s01'], rows)
        self.assertEqual((r['cumulative_slot_denominator'], r['cumulative_eligible_candidates'], r['candidate_shortage']), (6, 3, 1))
        self.assertFalse(r['cumulative_capture_capacity_met']); self.assertFalse(r['reference_counted_as_candidate'])
        rows[1]['development_capture_eligible'] = True
        self.assertTrue(capacity(['q01s00', 'q01s01'], rows)['cumulative_capture_capacity_met'])


if __name__ == '__main__': unittest.main()
