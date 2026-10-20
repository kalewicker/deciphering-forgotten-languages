import base64
import hashlib
import unittest
from fl_decipher.new_material_v63 import choose_post,recover,sources
from fl_decipher.dated_capture_scope_v38 import archive_selection

URL='https://forgottenlanguages-full.forgottenlanguages.org/2013/10/quantum-semantic-fields-and-universals.html?m=0'
RAW=b'<html><head><title>Quantum Semantic Fields and Universals</title><link rel="canonical" href="https://forgottenlanguages-full.forgottenlanguages.org/2013/10/quantum-semantic-fields-and-universals.html"></head><body><div class="post-body">opaque example <a href="https://arxiv.org/abs/1234.5678v1">Citation</a></div></body></html>'
TS='20260110222100';REPLAY='https://web.archive.org/web/'+TS+'id_/'+URL
CFG={'fl_url':URL,'title_prefix':'Quantum Semantic Fields and Universals','archive_cutoff':'20261020000000'}
HEAD=b'HTTP/2 200\r\nMemento-Datetime: Sat, 10 Jan 2026 22:21:00 GMT\r\n\r\n'


def selection(raw=RAW):return {'eligible':True,'replay_url':REPLAY,'record':{'timestamp':TS,'original':URL,'digest':base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')}}


class NewMaterialTests(unittest.TestCase):
    def test_original_order_selects_first_non_anita_without_replacement(self):
        rows={'nominees':[{'post_id':'post00'},{'post_id':'post01'},{'post_id':'post02'}]}
        self.assertEqual(choose_post(rows),{'post_id':'post01'})
        self.assertIsNone(choose_post({'nominees':[]}))

    def test_exact_cdx_original_and_digest_required(self):
        import json
        row=[['timestamp','original','statuscode','mimetype','digest'],[TS,URL,'200','text/html',selection()['record']['digest']]]
        self.assertTrue(archive_selection(json.dumps(row).encode(),CFG)['eligible'])
        row[1][1]=URL.split('?')[0]
        self.assertFalse(archive_selection(json.dumps(row).encode(),CFG)['eligible'])
        self.assertFalse(archive_selection(b'[]',CFG)['eligible'])

    def test_query_bearing_replay_and_observed_canonical_binding(self):
        r=recover(RAW,HEAD,{'transport_complete':True,'final_url':REPLAY},selection(),CFG)
        self.assertTrue(r['passed']);self.assertTrue(r['raw_post']);self.assertFalse(r['untouched_test_eligible'])
        self.assertIn('opaque example',r['body_text'])

    def test_bad_digest_memento_identity_or_duplicate_body_fail_closed(self):
        cases=[(RAW,HEAD,{'transport_complete':True,'final_url':REPLAY},selection()|{'record':selection()['record']|{'digest':'A'*32}}),
               (RAW,HEAD.replace(b'22:21:00',b'22:20:00'),{'transport_complete':True,'final_url':REPLAY},selection()),
               (RAW,HEAD,{'transport_complete':True,'final_url':REPLAY.split('?')[0]},selection()),
               (RAW.replace(b'</body>',b'<div class="post-body">second</div></body>'),HEAD,{'transport_complete':True,'final_url':REPLAY},selection()),
               (RAW.replace(b'<title>',b'<title>verify you are human '),HEAD,{'transport_complete':True,'final_url':REPLAY},selection())]
        for raw,head,receipt,sel in cases:
            with self.subTest(receipt=receipt):self.assertFalse(recover(raw,head,receipt,sel,CFG)['passed'])

    def test_first_unrecorded_arxiv_identifier_only_not_known_or_doi(self):
        raw=b'<div class="post-body"><a href="https://doi.org/10.1000/test">doi</a><a href="https://arxiv.org/abs/1234.5678v1">known</a><a href="https://arxiv.org/abs/2345.6789v2">new</a><a href="https://arxiv.org/abs/3456.7890v1">over cap</a></div>'
        r=sources(raw,['https://arxiv.org/pdf/1234.5678v3'])
        self.assertEqual(r['selected']['request_url'],'https://arxiv.org/pdf/2345.6789v2')
        self.assertEqual([x['reason'] for x in r['source_candidate_ledger']],['not_arxiv_route','known_exposed_identifier','selected_first_unrecorded_arxiv_identifier','single_source_cap'])
        self.assertFalse(r['novel_connected_work_confirmed'])

    def test_unlinked_text_identifiers_and_missing_body_do_not_invent_sources(self):
        self.assertIsNone(sources(b'<div class="post-body">arXiv:1234.5678</div>',[])['selected'])
        self.assertIsNone(sources(b'<div>https://arxiv.org/abs/1234.5678</div>',[])['selected'])
