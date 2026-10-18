import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from email.message import Message
from fl_decipher.provenance_v24 import acquire_child, decode_entity, fingerprint, valid_redirect, window_gate


class ProvenanceTests(unittest.TestCase):
    def test_identity_and_gzip_are_distinct_preserved_representations(self):
        body = b'fixed archival body';entity = gzip.compress(body, mtime=0)
        self.assertEqual(decode_entity(entity, 'gzip', 100), body)
        self.assertNotEqual(fingerprint(entity), fingerprint(body))
        self.assertEqual(decode_entity(body, None, 100), body)

    def test_expansion_and_unknown_encoding_fail_closed(self):
        with self.assertRaises(ValueError):
            decode_entity(gzip.compress(b'a'*10000), 'gzip', 100)
        with self.assertRaises(ValueError):
            decode_entity(b'body', 'br', 100)
        with self.assertRaises((EOFError, OSError)):
            decode_entity(b'bad gzip', 'gzip', 100)

    def test_exact_limit_not_truncation(self):
        self.assertEqual(decode_entity(b'ab', 'identity', 2), b'ab')
        with self.assertRaises(ValueError):
            decode_entity(b'abc', 'identity', 2)

    def test_redirect_limits_scheme_host_and_credentials(self):
        origin = 'https://example.org/a'
        self.assertTrue(valid_redirect('https://example.org/b', origin, 3, 3))
        for url in ['http://example.org/b', 'https://evil.example/b', 'https://u:p@example.org/b', 'https://example.org:444/b']:
            self.assertFalse(valid_redirect(url, origin, 1, 3))
        self.assertFalse(valid_redirect(origin, origin, 4, 3))

    def test_window_requires_every_page_and_all_modalities(self):
        pages = [{'page_one_based': n, 'text_nonempty': True, 'text_equal': True,
                  'dimensions_equal': True, 'pixels_equal': True} for n in range(90, 95)]
        self.assertTrue(window_gate(pages, [357, 357]))
        self.assertFalse(window_gate(pages, [357, 358]))
        self.assertFalse(window_gate(pages[:-1], [357, 357]))
        for field in ['text_nonempty', 'text_equal', 'dimensions_equal', 'pixels_equal']:
            changed = [dict(p) for p in pages];changed[2][field] = False
            self.assertFalse(window_gate(changed, [357, 357]))

    def test_client_preserves_encoded_body_and_secure_context(self):
        class Reply(io.BytesIO):
            code = 200
            headers = Message()
            headers['Content-Encoding'] = 'gzip'
            def geturl(self):
                return 'https://example.org/a'
        entity = gzip.compress(b'fixed text',mtime=0)
        class Opener:
            def open(self,request,timeout):
                assert request.get_header('Accept-encoding') == 'identity'
                assert timeout == 15
                return Reply(entity)
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.build_opener',return_value=Opener()) as build:
            path=Path(tmp)
            acquire_child(path,{'url':'https://example.org/a'}, {'max_redirects':3,'user_agent':'test','socket_timeout_seconds':15,'max_body_bytes':100})
            self.assertEqual((path/'body.bin').read_bytes(),entity)
            self.assertTrue(json.loads((path/'child_result.json').read_text())['read_complete'])
            https=build.call_args.args[1]
            self.assertTrue(https._context.check_hostname)
            self.assertEqual(int(https._context.verify_mode),2)

    def test_client_retains_partial_body_after_read_error(self):
        class Reply(io.BytesIO):
            code=200
            headers=Message()
            def geturl(self):
                return 'https://example.org/a'
            def read1(self,n):
                if self.tell():
                    raise OSError('interrupted transfer')
                return super().read1(n)
        class Opener:
            def open(self,request,timeout):
                return Reply(b'partial')
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.build_opener',return_value=Opener()):
            path=Path(tmp)
            acquire_child(path,{'url':'https://example.org/a'},{'max_redirects':3,'user_agent':'test','socket_timeout_seconds':15,'max_body_bytes':100})
            result=json.loads((path/'child_result.json').read_text())
            self.assertEqual((path/'body.bin').read_bytes(),b'partial')
            self.assertFalse(result['read_complete'])
            self.assertIn('interrupted transfer',result['error'])


if __name__ == '__main__':
    unittest.main()
