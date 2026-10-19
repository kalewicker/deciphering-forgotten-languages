import unittest
from fl_decipher.context_dossier_v45 import build, body_paragraphs, fenced, parts


class ContextDossierTests(unittest.TestCase):
    def fixture(self, duplicate=False):
        p = '<p>Alan Watson: shared words.</p>'
        raw = ('<html><body><p>Before.</p>' + p + (p if duplicate else '') + '<p>After.</p></body></html>').encode()
        source, _ = body_paragraphs(raw)
        query = 'New shared words. Giselian beacon'
        target = 'opaque ' + query + ' trailing'
        a = query.index('shared'); b = a + len('shared words.')
        s = source.index('shared')
        q = {'text': query, 'span': [7, 7 + len(query)]}
        w = {'query_char_span': [a, b], 'source_char_span': [s, s + b - a],
             'target_char_span': [7 + a, 7 + b], 'query_fragment': query[a:b], 'source_fragment': source[s:s + b - a]}
        return raw, source, target, q, w

    def test_partitions_and_fixed_context_reassemble_without_trimming(self):
        args = self.fixture(); d = build(*args, context_characters=3)
        self.assertEqual(d['status'], 'context_available')
        self.assertEqual(''.join(r['text'] for r in d['target_partition']), args[3]['text'])
        self.assertEqual(''.join(r['text'] for r in d['source_partition']), d['selected_paragraph']['text'])
        self.assertEqual([p['paragraph_index'] for p in d['publisher_window']], [0, 1, 2])
        for row in d['target_partition']:
            self.assertEqual(args[2][slice(*row['global_span'])], row['text'])
        checks = {c['check_id']: c['present'] for c in d['context_checks']}
        self.assertTrue(checks['beacon_phrase:target_quote'])
        self.assertFalse(checks['beacon_phrase:publisher_body'])

    def test_duplicate_paragraph_cannot_manufacture_unique_context(self):
        d = build(*self.fixture(duplicate=True))
        self.assertEqual(d['status'], 'unavailable_paragraph_identity')
        self.assertIsNone(d['context_checks'])

    def test_changed_witness_or_export_fails_before_interpretation(self):
        args = list(self.fixture()); args[4] = dict(args[4], query_fragment='altered')
        with self.assertRaisesRegex(ValueError, 'fixed witness'):
            build(*args)
        args = list(self.fixture()); args[0] = args[0].replace(b'Before.', b'Changed.')
        with self.assertRaisesRegex(ValueError, 'frozen v42'):
            build(*args)

    def test_empty_suffix_and_untrusted_code_fence_are_preserved(self):
        rows = parts('ab MATCH', 3, 8, 10)
        self.assertEqual(rows[-1]['text'], '')
        self.assertEqual(rows[-1]['global_span'], [18, 18])
        wrapped = fenced('```\n<script>not executed</script>')
        self.assertTrue(wrapped.startswith('````text\n'))
        self.assertTrue(wrapped.endswith('\n````\n'))
