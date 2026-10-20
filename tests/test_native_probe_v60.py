from pathlib import Path
import unittest
from fl_decipher.native_probe_v60 import command, inventory, observation, summarize

URL = 'https://physicsworld.com/?s=ANITA'
CONTRACT = {'url': URL, 'connect_timeout_seconds': 8, 'total_timeout_seconds': 20, 'max_body_bytes': 4194304,
            'user_agent': 'FL-Decipher registered native-search layout probe v60'}
HEADERS = b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 200\r\ncontent-type: text/html; charset=UTF-8\r\n\r\n'
RECEIPT = {'transport_complete': True, 'http_status': 200, 'curl_returncode': 0, 'final_url': URL,
           'num_redirects': 0, 'content_type': 'text/html; charset=UTF-8'}


class NativeProbeTests(unittest.TestCase):
    def test_one_get_command_has_no_follow_or_retry(self):
        cmd = command(Path('/tmp/probe'), CONTRACT)
        self.assertNotIn('--location', cmd)
        self.assertEqual(cmd[cmd.index('--request') + 1], 'GET')
        for key in ['--retry', '--max-redirs']: self.assertEqual(cmd[cmd.index(key) + 1], '0')
        self.assertEqual(cmd[-1], URL)
        for flag in ['--cookie', '--cookie-jar', '--user', '--data']: self.assertNotIn(flag, cmd)

    def test_all_occurrences_include_navigation_duplicates_and_empty_anchor(self):
        raw = b'<title>Search</title><body><nav><a href="/a/test/">nav</a></nav><main class="results"><h1>ANITA</h1><h2>heading</h2><a href="/a/test/">hit?</a><a href="/a/other/"></a><a href="https://evil.test/a/x/">external</a></main></body>'
        r = inventory(raw, URL, 'ANITA')
        self.assertEqual(len(r['anchors']), 4)
        self.assertEqual([a['anchor_index'] for a in r['anchors']], list(range(4)))
        self.assertEqual(r['anchors'][0]['article_key_diagnostic'], r['anchors'][1]['article_key_diagnostic'])
        self.assertEqual(r['anchors'][2]['text'], '')
        self.assertIsNone(r['anchors'][3]['article_key_diagnostic'])
        self.assertEqual(r['anchors'][1]['ancestors'][-1]['classes'], ['results'])
        self.assertTrue(all(not a['search_hit_attributed'] for a in r['anchors']))

    def test_base_href_retains_links_but_disables_resolution(self):
        r = inventory(b'<base href="https://evil.test/"><a href="/a/test/">x</a>', URL, 'ANITA')
        self.assertFalse(r['link_resolution_supported'])
        self.assertEqual(r['anchors'][0]['href'], '/a/test/')
        self.assertIsNone(r['anchors'][0]['resolved_url'])
        self.assertEqual(r['anchors'][0]['diagnostic_reason'], 'base_href_present')

    def test_malformed_href_and_query_urls_are_not_admitted(self):
        r = inventory(b'<a href="https://[broken">bad</a><a href="/a/test/?s=x">query</a><a href="/a/test/#x">fragment</a>', URL, 'ANITA')
        self.assertEqual(r['anchors'][0]['diagnostic_reason'], 'malformed_href')
        self.assertTrue(all(a['article_key_diagnostic'] is None for a in r['anchors']))

    def test_complete_html_is_not_search_validation(self):
        r = observation(b'<h1>Search</h1>', HEADERS, RECEIPT, CONTRACT, ['access denied'])
        self.assertTrue(r['complete_direct_html_observation'])
        self.assertFalse(r['native_search_function_validated'])

    def test_redirect_error_partial_and_challenge_fail_without_replacement(self):
        cases = [(b'<h1>Access denied</h1>', HEADERS, RECEIPT),
                 (b'<h1>x</h1>', b'HTTP/2 301\r\nlocation: https://physicsworld.com/search/\r\ncontent-type: text/html\r\n\r\n', RECEIPT | {'http_status': 301}),
                 (b'partial', HEADERS, RECEIPT | {'transport_complete': False, 'curl_returncode': 28}),
                 (b'<h1>x</h1>', HEADERS, RECEIPT | {'final_url': 'https://physicsworld.com/'}),
                 (b'<h1>x</h1>', HEADERS + HEADERS, RECEIPT),
                 (b'x', b'HTTP/2 200\r\ncontent-type: application/json\r\n\r\n', RECEIPT | {'content_type': 'application/json'})]
        for body, headers, receipt in cases:
            with self.subTest(receipt=receipt): self.assertFalse(observation(body, headers, receipt, CONTRACT, ['access denied'])['complete_direct_html_observation'])

    def test_summary_counts_diagnostics_never_candidates(self):
        raw = b'<form action="/"><input name="s" value="ANITA"><input type="hidden" name="nonce" value="private"></form><a href="/a/test/">a</a><a href="/a/test/">b</a>'
        layout = inventory(raw, URL, 'ANITA'); obs = observation(raw, HEADERS, RECEIPT, CONTRACT, [])
        r = summarize(layout, obs, RECEIPT)
        self.assertEqual((r['anchor_occurrences'], r['unique_strict_article_urls_diagnostic_only'], r['duplicate_strict_article_url_occurrences']), (2, 1, 1))
        self.assertEqual(layout['search_input_values'], [{'form_index': 0, 'control_index': 0, 'value': 'ANITA'}])
        self.assertTrue(r['query_echo_in_search_input'])
        for key in ['search_hits_attributed', 'candidate_nominations', 'article_captures', 'alignment_or_semantic_scores']: self.assertEqual(r[key], 0)
        self.assertIsNone(r['search_result_container_selector'])
