import base64
import hashlib
import unittest
from fl_decipher.archive_admission_v64 import adjudicate,export_body,inspect_citations

URL='https://forgottenlanguages-full.forgottenlanguages.org/2013/10/test.html?m=0'
TITLE='Known post title'
TS='20260111041840'
REPLAY='https://web.archive.org/web/'+TS+'id_/'+URL
CFG={'fl_url':URL,'title_prefix':TITLE,'nominee':{'title':TITLE}}
HEAD=b'HTTP/2 200\r\nMemento-Datetime: Sun, 11 Jan 2026 04:18:40 GMT\r\n\r\n'

def page(extra='',body='Neutral material'):
    return ('<html><head><title>Forgotten Languages Full: '+TITLE+'</title>'+extra+'</head><body><h3 class="post-title"><a href="'+URL+'">'+TITLE+'</a></h3><a href="'+URL+'" rel="bookmark">time</a><div class="post-body">'+body+'</div></body></html>').encode()

def decision(raw,header=HEAD,receipt=None):
    selection={'eligible':True,'replay_url':REPLAY,'record':{'timestamp':TS,'original':URL,'digest':base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')}}
    return adjudicate(raw,header,receipt or {'transport_complete':True,'final_url':REPLAY},selection,CFG),selection


class ArchiveAdmissionTests(unittest.TestCase):
    def test_missing_metadata_needs_archive_chain_and_both_affirmative_permalinks(self):
        d,s=decision(page())
        self.assertFalse(d['e63_gate_recomputed']);self.assertTrue(d['limited_admission'])
        self.assertEqual(d['identity_metadata_status'],'absent')
        self.assertEqual(d['allowed_use'],'offline_citation_metadata_inspection')
        self.assertFalse(d['source_acquisition_authorized'])

    def test_present_metadata_conflict_is_not_ignored(self):
        d,_=decision(page('<link rel="canonical" href="https://evil.test/">'))
        self.assertFalse(d['limited_admission']);self.assertEqual(d['identity_metadata_status'],'conflicting')
        d,_=decision(page('<meta property="og:url" content="'+URL+'">'))
        self.assertTrue(d['limited_admission']);self.assertTrue(d['e63_gate_recomputed'])

    def test_absent_duplicate_or_wrong_permalink_and_wrong_title_fail_closed(self):
        raw=page()
        cases=[raw.replace(b'rel="bookmark"',b'rel="other"'),raw.replace(b'</body>',('<a rel="bookmark" href="'+URL+'">extra</a></body>').encode()),
               raw.replace(('href="'+URL+'" rel="bookmark"').encode(),('href="'+URL.split('?')[0]+'" rel="bookmark"').encode()),
               raw.replace(b'<title>Forgotten Languages Full: Known post title</title>',b'<title>Different</title>')]
        for sample in cases:
            with self.subTest(sample=sample):self.assertFalse(decision(sample)[0]['limited_admission'])

    def test_archive_digest_memento_and_final_url_are_still_required(self):
        raw=page();d,s=decision(raw)
        s['record']['digest']='A'*32
        self.assertFalse(adjudicate(raw,HEAD,{'transport_complete':True,'final_url':REPLAY},s,CFG)['limited_admission'])
        self.assertFalse(decision(raw,HEAD.replace(b'04:18:40',b'04:18:41'))[0]['limited_admission'])
        self.assertFalse(decision(raw,receipt={'transport_complete':True,'final_url':REPLAY.split('?')[0]})[0]['limited_admission'])

    def test_export_preserves_text_and_parent_but_excludes_runtime_nodes(self):
        raw=page(body='A <b>B</b><script>bad()</script><style>bad</style><noscript>bad</noscript> C')
        d,s=decision(raw);out=export_body(raw,d,s,URL)
        self.assertEqual(out['text'],'A B C')
        self.assertEqual(out['parent_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertFalse(out['semantic_training_eligible']);self.assertFalse(out['untouched_test_eligible'])

    def test_all_url_occurrences_duplicates_and_literal_locators_are_retained(self):
        raw=page(body='<a href="https://arxiv.org/abs/1234.5678v1">paper</a> https://arxiv.org/pdf/1234.5678v2 <a href="https://example.org/image.png">image</a><script>https://arxiv.org/abs/9999.9999</script>')
        d,_=decision(raw);r=inspect_citations(raw,d,['https://arxiv.org/abs/1234.5678v3'])
        self.assertEqual(r['url_occurrence_denominator'],3);self.assertEqual(r['recognized_identifier_count'],1)
        self.assertEqual(r['occurrences'][1]['duplicate_identifier_of_occurrence'],0)
        self.assertEqual(r['occurrences'][1]['origin']['channel'],'literal_text_url')
        self.assertEqual(r['known_identifier_matches'],['arxiv:1234.5678'])
        self.assertTrue(all(not x['selected_for_acquisition'] for x in r['occurrences']))

    def test_unsafe_and_malformed_urls_are_rejected_without_disappearing(self):
        raw=page(body='<a href="https://arxiv.org:81/abs/1234.5678">port</a><a href="https://@arxiv.org/abs/1234.5678">auth</a><a href="https://[broken">bad</a>')
        d,_=decision(raw);r=inspect_citations(raw,d,[])
        self.assertEqual(r['url_occurrence_denominator'],3);self.assertEqual(r['recognized_identifier_count'],0)

    def test_rejected_material_has_no_export_or_citation_inventory(self):
        raw=page('<meta property="og:url" content="https://evil.test/">');d,s=decision(raw)
        self.assertIsNone(export_body(raw,d,s,URL));self.assertIsNone(inspect_citations(raw,d,[]))
