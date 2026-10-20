import unittest
from bs4 import BeautifulSoup
from fl_decipher.offline_intake_v54 import evaluate

URL = 'https://physicsworld.com/a/example/'
ALIAS = 'https://physicsworld.com/example/'
SPEC = {'id': 'fixture', 'url': URL, 'expected_title': 'Antarctic neutrinos', 'v50_ready_unchanged': False}
CFG = {'source_selector': 'article[id^="post-"] > div.entry-content', 'minimum_paragraph_runs': 3,
       'minimum_run_characters': 1000, 'date_min': '2000-01-01', 'date_max': '2018-09-30',
       'challenge_signatures': ['verify you are human']}
RECEIPT = {'transport_complete': True, 'http_status': 200, 'curl_returncode': 0, 'final_url': URL}


def raw_page(date='2017-01-01', og=URL, heading='', extra='', paragraphs=None):
    paragraphs = paragraphs if paragraphs is not None else ''.join('<div><p>' + 'Antarctic neutrinos measurement. ' * 16 + '</p></div>' for _ in range(3))
    return (f'<html><head><title>Antarctic neutrinos - Physics World</title><meta property="og:title" content="Antarctic neutrinos">'
            f'<link rel="canonical" href="{URL}"><meta property="og:url" content="{og}">'
            f'<meta property="article:published_time" content="{date}">'
            '<script type="application/ld+json">{"@type":"NewsArticle","headline":"Antarctic neutrinos"}</script>'
            f'{extra}</head><body>{heading}<article id="post-1"><div class="entry-content">{paragraphs}</div></article></body></html>').encode()


def body(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    return soup.body.get_text(' ', strip=True)


def result(raw=None, route=None, receipt=None, expected_body=None):
    raw = raw if raw is not None else raw_page()
    return evaluate(raw, receipt or RECEIPT, SPEC, CFG, body(raw) if expected_body is None else expected_body, route)


class OfflineIntakeTests(unittest.TestCase):
    def test_missing_h1_with_three_titles_and_nested_paragraphs_eligible(self):
        r = result(); self.assertTrue(r['development_capture_eligible'])
        self.assertEqual(r['paragraph_run_count'], 3); self.assertFalse(r['v50_ready_unchanged'])
        self.assertFalse(r['independent_source_group_admitted']); self.assertFalse(r['untouched_test_unit_admitted'])

    def test_present_h1_must_agree_but_is_not_cardinality_gate(self):
        self.assertTrue(result(raw_page(heading='<h1>Antarctic neutrinos</h1>' * 2))['development_capture_eligible'])
        r = result(raw_page(heading='<h1>Other</h1>'))
        self.assertEqual(r['unmet'], ['present_h1_values_match'])

    def test_exact_observed_alias_binding_required(self):
        route = {'current_alias_supported': True, 'checks': {k: True for k in ['complete_200', 'html_content_type',
                 'consistent_publisher_chain', 'canonical_matches_frozen', 'three_title_channels_match_frozen']},
                 'requested_url': ALIAS, 'expected_canonical_url': URL, 'final_url': URL,
                 'category': 'observed_redirect_to_canonical', 'num_redirects': 1}
        raw = raw_page(og=ALIAS)
        self.assertFalse(result(raw)['development_capture_eligible'])
        self.assertTrue(result(raw, route)['development_capture_eligible'])
        for change in [{'requested_url': ALIAS.rstrip('/')}, {'final_url': 'https://physicsworld.com/a/other/'},
                       {'current_alias_supported': False}, {'checks': {}}, {'checks': {'complete_200': False}}, {'num_redirects': 0}]:
            self.assertFalse(result(raw, route | change)['development_capture_eligible'])

    def test_missing_or_conflicting_titles_fail_despite_h1(self):
        raw = raw_page(heading='<h1>Antarctic neutrinos</h1>')
        for edited in [raw.replace(b'"headline":"Antarctic neutrinos"', b'"headline":"Other"'),
                       raw.replace(b'property="og:title"', b'property="other"'),
                       raw.replace(b'</head>', b'<title>Other</title></head>')]:
            self.assertIn('three_metadata_title_channels_agree', result(edited)['unmet'])

    def test_dates_keep_hard_bounds_and_all_values(self):
        for date in ['2000-01-01', '2018-09-30T23:59:00+00:00']:
            self.assertTrue(result(raw_page(date=date))['development_capture_eligible'])
        for date in ['1999-12-31', '2018-10-01', '2026-10-06', '', 'invalid']:
            self.assertFalse(result(raw_page(date=date))['development_capture_eligible'])
        r = result(raw_page(extra='<meta property="article:published_time" content="2016-01-01">'))
        self.assertIn('publication_date_agrees', r['unmet'])

    def test_form_text_cannot_supply_volume_or_topic(self):
        raw = raw_page(paragraphs='<form><p>' + 'Antarctic neutrinos. ' * 100 + '</p></form><p>x</p><p>y</p><p>z</p>')
        r = result(raw); self.assertEqual(r['paragraph_run_characters'], 3)
        self.assertIn('minimum_run_characters', r['unmet'])
        raw = raw_page(paragraphs='<form><p>' + 'Antarctic neutrinos. ' * 100 + '</p></form>')
        self.assertIn('minimum_nonempty_paragraph_runs', result(raw)['unmet'])

    def test_frozen_body_mismatch_and_duplicate_container_fail_closed(self):
        self.assertIn('scope_and_accounting_valid', result(expected_body='wrong')['unmet'])
        raw = raw_page().replace(b'</body>', b'<article id="post-2"><div class="entry-content"></div></article></body>')
        self.assertIn('scope_and_accounting_valid', result(raw)['unmet'])

    def test_transport_identity_and_challenge_failures(self):
        for change in [{'http_status': 404}, {'transport_complete': False}, {'curl_returncode': 28},
                       {'final_url': 'https://physicsworld.com/a/other/'}]:
            self.assertFalse(result(receipt=RECEIPT | change)['development_capture_eligible'])
        raw = raw_page().replace(b'</body>', b'<div>verify you are human</div></body>')
        self.assertIn('no_challenge_text', result(raw)['unmet'])
        raw = raw_page(extra='<link rel="canonical" href="https://physicsworld.com/a/other/">')
        self.assertIn('all_canonical_fields_match', result(raw)['unmet'])


if __name__ == '__main__': unittest.main()
