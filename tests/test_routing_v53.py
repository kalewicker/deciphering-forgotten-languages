import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from fl_decipher.routing_v53 import assess, capture, command, header_blocks, publisher_key

ALIAS = 'https://physicsworld.com/example/'
CANON = 'https://physicsworld.com/a/example/'
SPEC = {'id': 'fixture', 'og_url': ALIAS, 'canonical_url': CANON, 'expected_title': 'Example',
        'old_body_sha256': '0' * 64, 'v50_ready_unchanged': False}
LIMITS = {'connect_timeout_seconds': 8, 'total_timeout_seconds': 20, 'max_redirects': 3,
          'max_body_bytes': 4194304, 'user_agent': 'FL-Decipher registered routing audit v53'}
BODY = b'''<html><head><title>Example \xe2\x80\x93 Physics World</title>
<link rel="canonical" href="https://physicsworld.com/a/example/">
<meta property="og:title" content="Example"><meta property="og:url" content="https://physicsworld.com/example/">
<script type="application/ld+json">{"@graph":[{"@type":"NewsArticle","headline":"Example"}]}</script>
</head><body><h2>Example</h2></body></html>'''


def receipt(final=CANON, redirects=1, code=0, status=200):
    return {'final_url': final, 'num_redirects': redirects, 'curl_returncode': code, 'http_status': status,
            'transport_complete': code == 0 and status == 200, 'content_type': 'text/html; charset=UTF-8'}


class RoutingTests(unittest.TestCase):
    def test_keys_preserve_a_distinction_and_reject_unsafe(self):
        self.assertNotEqual(publisher_key(ALIAS), publisher_key(CANON))
        self.assertEqual(publisher_key(CANON), publisher_key(CANON.rstrip('/')))
        for url in ['http://physicsworld.com/example/', 'https://evil.com/example/',
                    'https://user@physicsworld.com/example/', ALIAS + '?x=1', ALIAS + '#x',
                    'https://physicsworld.com:444/example/', 'https://physicsworld.com/%65xample/',
                    'https://physicsworld.com:bad/example/']:
            self.assertIsNone(publisher_key(url))

    def test_redirect_relative_location_proxy_and_early_hints(self):
        headers = b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 103\r\n\r\nHTTP/2 301\r\nLocation: /a/example/\r\n\r\nHTTP/2 200\r\nContent-Type: text/html\r\nSet-Cookie: private\r\n\r\n'
        result = assess(BODY, headers, receipt(), SPEC)
        self.assertEqual(result['category'], 'observed_redirect_to_canonical')
        self.assertEqual(len(result['header_inventory']['ignored_transport_or_informational']), 2)
        self.assertNotIn('private', json.dumps(result))
        self.assertFalse(result['v50_ready_unchanged'])

    def test_served_alias_requires_no_redirect_and_matching_metadata(self):
        result = assess(BODY, b'HTTP/2 200\n\n', receipt(ALIAS, 0), SPEC)
        self.assertEqual(result['category'], 'observed_served_alias')
        self.assertEqual(result['metadata']['h1_inventory'], [])

    def test_missing_duplicate_or_conflicting_metadata_fails(self):
        for body in [BODY.replace(b'<title>', b'<other>').replace(b'</title>', b'</other>'),
                     BODY.replace(b'</head>', b'<link rel="canonical" href="https://physicsworld.com/a/other/"></head>'),
                     BODY.replace(b'"headline":"Example"', b'"headline":"Other"'),
                     BODY.replace(b'</head>', b'<script type="application/ld+json">broken</script></head>')]:
            self.assertEqual(assess(body, b'HTTP/2 200\n\n', receipt(ALIAS, 0), SPEC)['category'], 'unresolved')

    def test_inconsistent_chains_and_failures_retained(self):
        for headers, rec in [(b'HTTP/2 200\n\n', receipt()),
            (b'HTTP/2 301\nLocation: /a/example/\nLocation: /a/other/\n\nHTTP/2 200\n\n', receipt()),
            (b'HTTP/2 200\nLocation: /a/example/\n\n', receipt(ALIAS, 0)),
            (b'HTTP/2 404\n\n', receipt(ALIAS, 0, status=404)),
            (b'', receipt(ALIAS, 0, code=28, status=0))]:
            self.assertEqual(assess(BODY, headers, rec, SPEC)['category'], 'unresolved')

    def test_cross_host_and_unexpected_final_are_not_alias_support(self):
        headers = b'HTTP/2 301\nLocation: https://elsewhere.example/a/example/\n\nHTTP/2 200\n\n'
        self.assertFalse(assess(BODY, headers, receipt('https://elsewhere.example/a/example/'), SPEC)['current_alias_supported'])
        headers = b'HTTP/2 301\nLocation: /a/other/\n\nHTTP/2 200\n\n'
        self.assertFalse(assess(BODY, headers, receipt('https://physicsworld.com/a/other/'), SPEC)['current_alias_supported'])

    def test_command_limits_and_no_retry(self):
        args = command(Path('/unused'), ALIAS, LIMITS)
        for flag, expected in [('--retry', '0'), ('--max-redirs', '3'), ('--max-time', '20'),
                               ('--connect-timeout', '8'), ('--max-filesize', '4194304'),
                               ('--proto', '=https'), ('--proto-redir', '=https')]:
            self.assertEqual(args[args.index(flag) + 1], expected)
        self.assertEqual(args[1], '--disable')

    def test_capture_failure_is_one_attempt_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('fl_decipher.routing_v53.subprocess.run', return_value=SimpleNamespace(returncode=28, stdout=b'', stderr=b'timeout')) as run:
                result = capture(root, SPEC, LIMITS)
                self.assertFalse(result['transport_complete']); self.assertEqual(run.call_count, 1)
                self.assertEqual(result['curl_returncode'], 28)
                with self.assertRaises(FileExistsError): capture(root, SPEC, LIMITS)
                self.assertEqual(run.call_count, 1)


if __name__ == '__main__': unittest.main()
