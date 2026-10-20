import json
import unittest
from fl_decipher.native_discovery_v59 import audit, request_url, root_url, summary, TEMPLATE, QUERY_INPUT


def fixture(form='<form action="https://physicsworld.com"><input type="search" name="s"><button type="submit">Search</button></form>', template=TEMPLATE):
    schema = {'@graph': [{'@type': 'WebSite', 'potentialAction': [{'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': template}, 'query-input': QUERY_INPUT}]}]}
    return (form + '<script type="application/ld+json">' + json.dumps(schema) + '</script>').encode()


class NativeDiscoveryTests(unittest.TestCase):
    def test_nested_declarations_and_default_get(self):
        row = audit(fixture(), 'https://physicsworld.com/a/test/', 'ANITA')
        self.assertTrue(row['route_declarations_agree'])
        self.assertEqual(row['search_actions'][0]['json_path'], '$.@graph[0].potentialAction[0]')
        self.assertEqual(row['proposed_request_url'], 'https://physicsworld.com/?s=ANITA')
        self.assertFalse(row['live_transport_tested'])

    def test_safe_route_and_query_encoding(self):
        for url in ['http://physicsworld.com', 'https://physicsworld.com.evil/', 'https://u@physicsworld.com/', 'https://@physicsworld.com/', 'https://physicsworld.com/?', 'https://physicsworld.com/#', 'https://physicsworld.com:81/', 'https://physicsworld.com/?x=1', 'https://physicsworld.com/#x', 'https://physicsworld.com/wp-json/']:
            self.assertIsNone(root_url(url))
        self.assertEqual(request_url('a & b/雪'), 'https://physicsworld.com/?s=a+%26+b%2F%E9%9B%AA')
        with self.assertRaises(ValueError): request_url(' ')

    def test_unsafe_or_ambiguous_forms_fail_closed(self):
        for form in ['<form action="https://evil.test"><input name="s"></form>', '<form action="/" method="post"><input name="s"></form>', '<form action="/"><input name="s" disabled></form>', '<form action="/"><input name="s"><input name="s"></form>', '<form action="/"><input name="s"><input type="hidden" name="nonce" value="secret"></form>', '<form action="/"><input name="s"><button formaction="https://evil.test">Go</button></form>', '<form action="/" id="q"><input name="s"></form><input name="extra" form="q">', '<base href="https://evil.test"><form action="/"><input name="s"></form>', '<form action="/"><fieldset disabled><input name="s"></fieldset></form>', '<form><input name="s"></form>']:
            with self.subTest(form=form): self.assertFalse(audit(fixture(form), 'https://physicsworld.com/a/test/', 'ANITA')['route_declarations_agree'])

    def test_conflicting_schema_and_forms_retained(self):
        raw = fixture() + fixture(template='https://physicsworld.com/?q={search_term_string}')
        row = audit(raw, 'https://physicsworld.com/', 'ANITA')
        self.assertEqual(len(row['search_actions']), 2)
        self.assertFalse(row['route_declarations_agree'])
        raw = fixture() + b'<form action="https://evil.test"><input name="s"></form>'
        self.assertEqual(len(audit(raw, 'https://physicsworld.com/', 'ANITA')['search_forms']), 2)
        self.assertFalse(audit(raw, 'https://physicsworld.com/', 'ANITA')['route_declarations_agree'])

    def test_malformed_or_missing_schema_not_rescued(self):
        raw = fixture() + b'<script type="application/ld+json">{broken</script>'
        self.assertFalse(audit(raw, 'https://physicsworld.com/', 'ANITA')['route_declarations_agree'])
        for raw in [b'<form action="/"><input name="s"></form>', fixture(form='')]:
            self.assertFalse(audit(raw, 'https://physicsworld.com/', 'ANITA')['route_declarations_agree'])

    def test_api_declarations_do_not_invent_search_routes(self):
        raw = b'<link rel="https://api.w.org/" href="https://physicsworld.com/wp-json/"><link rel="alternate" type="application/json" href="https://physicsworld.com/wp-json/wp/v2/posts/1"><link type="application/json+oembed" rel="alternate" href="https://physicsworld.com/wp-json/oembed/1.0/embed">'
        row = audit(raw, 'https://physicsworld.com/', 'ANITA')
        self.assertEqual(len(row['api_links_not_selected']), 3)
        self.assertIsNone(row['proposed_request_url'])

    def test_uniform_gate_retains_failed_denominator(self):
        good = audit(fixture(), 'https://physicsworld.com/', 'ANITA')
        bad = audit(b'', 'https://physicsworld.com/', 'ANITA')
        result = summary([good, bad], 'ANITA')
        self.assertEqual((result['capture_denominator'], result['supported_captures']), (2, 1))
        self.assertFalse(result['uniform_saved_declaration_gate'])
        self.assertIsNone(result['proposed_request_url'])
        self.assertFalse(summary([], 'ANITA')['uniform_saved_declaration_gate'])
