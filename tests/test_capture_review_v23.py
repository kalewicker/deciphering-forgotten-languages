from pathlib import Path
import importlib.util
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from fl_decipher.capture_review_v23 import resource_key, select_archive, extract_post, request, review_form


def nominee():
    return {'id': 'test', 'fl_title': 'The Fixed Post', 'fl_url': 'https://example.org/2019/fixed.html', 'archive_cutoff': '20261014120000'}


def metadata(**change):
    row = {'timestamp': '20250101000000', 'original': 'http://example.org/2019/fixed.html', 'statuscode': '200', 'mimetype': 'text/html', 'digest': 'D'} | change
    fields = ['timestamp', 'original', 'statuscode', 'mimetype', 'digest']
    return json.dumps([fields, [row[k] for k in fields]]).encode()


def html(body='Whole post prose.', title='The Fixed Post'):
    return (f'<html><title>{title}</title><link rel="canonical" href="https://example.org/2019/fixed.html"><div class="post-body">{body}</div></html>').encode()


def receipt(final='https://example.org/2019/fixed.html'):
    return {'transport_complete': True, 'final_url': final}


class CaptureReviewTests(unittest.TestCase):
    def test_single_exact_cutoff_record_selects_one_dated_replay(self):
        s = select_archive(metadata(), nominee())
        self.assertTrue(s['eligible'])
        self.assertEqual(s['replay_url'], 'https://web.archive.org/web/20250101000000id_/http://example.org/2019/fixed.html')
        self.assertEqual(resource_key(nominee()['fl_url']), resource_key('http://example.org:80/2019/fixed.html'))

    def test_missing_ambiguous_wrong_scope_and_future_metadata_fail_closed(self):
        for raw in [b'[]', b'<html>blocked</html>', metadata(timestamp='20261014120001'), metadata(original='https://wrong.org/2019/fixed.html'),
                    metadata(statuscode='403'), metadata(mimetype='application/pdf'), metadata(timestamp='bad'), metadata(original=3)]:
            self.assertFalse(select_archive(raw, nominee())['eligible'])
        rows = json.loads(metadata());rows.append(rows[1]);self.assertFalse(select_archive(json.dumps(rows).encode(), nominee())['eligible'])
        self.assertIsNone(resource_key('file:///private/data'))
        self.assertIsNone(resource_key('https://name:password@example.org/2019/fixed.html'))
        self.assertIsNone(resource_key('https://example.org:8000/2019/fixed.html'))

    def test_post_extraction_retains_headings_superscripts_and_mixed_language(self):
        r = extract_post(html('<h2>Heading</h2>FL prose.<sup>1</sup> English preface.<script>untrusted()</script>'), receipt(), nominee())
        self.assertTrue(r['eligible']);self.assertTrue(r['current_raw_fl']);self.assertFalse(r['archival_raw_fl'])
        self.assertIn('Heading', r['text']);self.assertIn('1', r['text']);self.assertIn('English preface.', r['text']);self.assertNotIn('untrusted', r['text'])

    def test_bad_transport_title_body_and_challenge_are_not_raw_post_admissions(self):
        for raw, rr in [(html(), {'transport_complete': False}), (html(title='Wrong Post'), receipt()),
                        (html()+b'<div class="post-body">second</div>', receipt()), (html('Verify you are human'), receipt()),
                        (b'<title>The Fixed Post</title>', receipt())]:
            self.assertFalse(extract_post(raw, rr, nominee())['eligible'])

    def test_archival_identity_is_not_current_raw_and_redirect_timestamp_is_bound(self):
        s = select_archive(metadata(), nominee());r = extract_post(html(), receipt(s['replay_url']), nominee(), s)
        self.assertTrue(r['archival_raw_fl']);self.assertFalse(r['current_raw_fl']);self.assertEqual(r['capture_timestamp'], '20250101000000')
        self.assertFalse(extract_post(html(), receipt(s['replay_url'].replace('20250101000000', '20240101000000')), nominee(), s)['eligible'])

    def test_request_preserves_failure_and_fixed_bounds_without_network(self):
        limits = {'pdf_max_bytes': 12000000, 'fl_metadata_max_bytes': 2000000, 'connect_timeout_seconds': 15,
                  'total_timeout_seconds': 30, 'max_redirects': 3, 'user_agent': 'fixed'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('fl_decipher.capture_review_v23.subprocess.run', return_value=SimpleNamespace(stdout=b'https://example.org\n000', stderr=b'TLS error', returncode=35)) as call:
                r = request(root, 'route', 'https://example.org', limits, 'native')
            self.assertFalse(r['transport_complete']);self.assertEqual(r['curl_returncode'], 35);self.assertEqual(r['stderr'], 'TLS error')
            command = call.call_args.args[0]
            self.assertIn('--max-filesize', command);self.assertIn('2000000', command);self.assertIn('--compressed', command);self.assertNotIn('--insecure', command)
            self.assertEqual(command[:2], ['curl', '--disable'])
            self.assertTrue((root/'route/receipt.json').exists())
            with self.assertRaises(FileExistsError):request(root, 'route', 'https://example.org', limits, 'native')

    def test_independent_review_fields_are_blank_and_no_labels_admitted(self):
        r = review_form(nominee())
        self.assertIsNone(r['reviewer_name']);self.assertIsNone(r['independent_of_prior_predictions'])
        self.assertEqual(r['word_correspondences'], []);self.assertFalse(r['review_completed']);self.assertFalse(r['semantic_training_eligible'])

    def test_prepare_guards_existing_review_directory_before_any_write(self):
        p = Path(__file__).resolve().parents[1]/'scripts/prepare_capture_review_v23.py';s = importlib.util.spec_from_file_location('capture_prepare_test', p)
        m = importlib.util.module_from_spec(s);s.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);(root/'data/v23/review_packets').mkdir(parents=True)
            with self.assertRaises(FileExistsError):m.prepare(root)
            self.assertFalse((root/'data/v23/frozen_review.json').exists())

if __name__ == '__main__':
    unittest.main()
