import json
import unittest
from fl_decipher.dated_capture_scope_v38 import normalized, literal_hits, indexed_export, quote_spans, archive_selection, dated_gate


class CaptureScopeTests(unittest.TestCase):
    def test_normalization_and_exact_source_witness(self):
        text = 'prefix Cafe\u0301  STRAßE\nnext suffix'
        hits = literal_hits('CAFÉ strasse next', text)
        self.assertEqual(len(hits), 1)
        a, b = hits[0]['source_span']
        self.assertEqual(text[a:b], hits[0]['source_quote'])
        self.assertEqual(normalized(text[a:b]), 'café strasse next')

    def test_no_dehyphenation_or_page_join(self):
        self.assertEqual(literal_hits('experimental', 'experi-\nmental'), [])
        self.assertEqual(len(literal_hits('aba', 'ababa')), 2)

    def test_indexed_lineage_keeps_exact_parent_slices(self):
        parent = 'L27: exclude\nL28: first\nL29: \ue200cite\ue2021†label\ue201\nL30: last\nL31: outside'
        result = indexed_export(parent, 28, 30)
        self.assertEqual(result['text'], 'first\nlabel\nlast')
        for r in result['lineage']:
            self.assertEqual(parent[slice(*r['parent_span'])], r['parent_quote'])
            self.assertEqual(result['text'][slice(*r['derived_span'])], r['derived_text'])

    def test_quote_denominator_includes_named_string_and_multiline(self):
        result = quote_spans('"ANITA" and “two\nlines” then " " then "last"')
        self.assertEqual([q['text'] for q in result], ['ANITA', 'two\nlines', 'last'])

    def test_archive_exact_original_and_digest_are_not_relaxed(self):
        cfg = {'fl_url': 'https://example.org/a', 'archive_cutoff': '20261018000000'}
        header = ['timestamp','original','statuscode','mimetype','digest']
        row = ['20260101000000',cfg['fl_url'],'200','text/html','A'*32]
        self.assertTrue(archive_selection(json.dumps([header,row]).encode(),cfg)['eligible'])
        row[1] = 'http://example.org/a'
        self.assertFalse(archive_selection(json.dumps([header,row]).encode(),cfg)['eligible'])
        row[1], row[4] = cfg['fl_url'], '-'
        self.assertFalse(archive_selection(json.dumps([header,row]).encode(),cfg)['eligible'])

    def test_redirect_memento_is_not_final_memento(self):
        cfg = {'fl_url':'https://example.org/a','fl_title':'title','archive_cutoff':'20261018000000'}
        meta = json.dumps([['timestamp','original','statuscode','mimetype','digest'],['20260101000000',cfg['fl_url'],'200','text/html','A'*32]]).encode()
        r = {'transport_complete':False}
        headers = 'HTTP/1.1 302 Found\r\nMemento-Datetime: Thu, 01 Jan 2026 00:00:00 GMT\r\n\r\nHTTP/2 200 OK\r\nServer: fixture\r\n\r\n'
        result = dated_gate(cfg,{'transport_complete':True},meta,r,b'',headers)
        self.assertIsNone(result['memento_timestamp'])
        self.assertFalse(result['passed'])


if __name__ == '__main__': unittest.main()
