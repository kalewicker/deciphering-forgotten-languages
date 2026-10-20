import unittest
from fl_decipher.quotation_attribution_v69 import freeze_target,safe_url,ledger,html_view,native_presence,MARKER

QUOTE='One complete target sentence with enough distinct words to form the fixed prefix for this test.'
TITLE='Quantum Semantic Fields and Universals'
def result(title,url,text):return f'{title} ({url})\n[test] [wordlim: 200] Content type: text/html\n{text}\n'
def response(text):return {'response':text,'error':None}
def target():return {'text':QUOTE,'phrases':[QUOTE,' '.join(QUOTE.split()[:12])]}


class QuotationAttributionTests(unittest.TestCase):
    def test_safe_urls_keep_queries_strip_fragments_reject_credentials_and_local(self):
        self.assertEqual(safe_url('https://example.org/a?q=b#page1'),'https://example.org/a?q=b')
        for u in ['http://example.org','https://x@example.org','https://example.org:99/a','https://localhost/a','https://127.0.0.1/a','https://internal.local/a','file:///a']:
            self.assertIsNone(safe_url(u))

    def test_complete_query_gate_and_one_slot(self):
        text=result('a','https://example.org/a',QUOTE)+result('b','https://example.org/b',QUOTE)
        r=ledger([response(text),response('')],target(),[],TITLE)
        self.assertEqual(r['selected']['url'],'https://example.org/a')
        self.assertEqual([h['nominated'] for h in r['calls'][0]['hits']],[True,False])

    def test_echoes_partial_snippets_and_unattributed_text_are_retained(self):
        text=result('fl','https://forgottenlanguages.org/a',QUOTE)+result('partial','https://example.org/a','One complete ... enough words')
        r=ledger([response(text),response(QUOTE)],target(),[],TITLE)
        self.assertIsNone(r['selected']);self.assertEqual(r['calls'][0]['attributable_hits'],2);self.assertEqual(r['calls'][1]['attributable_hits'],0)

    def test_prefix_only_can_nominate_but_not_claim_full_target(self):
        r=ledger([response(''),response(result('prefix','https://example.org/a',target()['phrases'][1]))],target(),[],TITLE)
        self.assertEqual(r['selected']['query_index'],1);self.assertFalse(r['selected']['complete_target_visible_in_discovery'])

    def test_title_only_and_embedded_suffix_are_not_phrase_witnesses(self):
        r=ledger([response(result(QUOTE,'https://example.org/a','different body')),response('')],target(),[],TITLE)
        self.assertIsNone(r['selected'])
        phrase=target()['phrases'][1]
        r=ledger([response(''),response(result('body','https://example.org/a',phrase+'extra'))],target(),[],TITLE)
        self.assertIsNone(r['selected'])

    def test_duplicate_and_known_registry_flags(self):
        text=result('a','https://example.org/a',QUOTE)
        r=ledger([response(text),response(text)],target(),['https://example.org/a'],TITLE)
        self.assertTrue(r['calls'][0]['hits'][0]['recorded_url_in_frozen_registry']);self.assertTrue(r['calls'][1]['hits'][0]['duplicate_returned_url'])

    def test_mismatched_boundary_markers_prevent_nomination(self):
        text=result('a','https://example.org/a',QUOTE)+'extra [wordlim: 20]\n'
        r=ledger([response(text),response('')],target(),[],TITLE)
        self.assertFalse(r['calls'][0]['response_format_supported']);self.assertIsNone(r['selected'])

    def test_witnesses_have_exact_response_local_spans(self):
        text='preface\n'+result('a','https://example.org/a',QUOTE)
        row=ledger([response(text),response('')],target(),[],TITLE)['calls'][0]['hits'][0]
        for w in row['witnesses']:self.assertEqual(text[slice(*w['response_span'])],w['source_quote'])

    def test_html_scope_excludes_runtime_but_keeps_broad_body(self):
        r=html_view(b'<html><title>T</title><body>menu<p>text</p><script>hidden</script><template>hidden</template></body></html>')
        self.assertEqual(r['text'],'menu text');self.assertEqual(r['titles'],['T'])

    def test_native_controls_preserve_negative_and_casefold_whitespace(self):
        r=native_presence('Heading\n'+QUOTE.upper(),QUOTE)
        self.assertTrue(r['complete_target_visible']);self.assertTrue(r['controls_passed'])
        self.assertFalse(native_presence(QUOTE+' '+MARKER,QUOTE)['controls_passed'])

    def test_target_is_bound_to_original_span_and_eighteen_tokens(self):
        words=' '.join(str(i) for i in range(18));text=words+' '*(125-len(words))
        inventory={'blocks':[{'block_id':0,'run_id':3,'body_span':[0,1],'text':'x'}, {'block_id':1,'run_id':4,'body_span':[790,915],'text':text}]}
        r=freeze_target(inventory,{'text':'x'*790+text});self.assertEqual(len(r['requests']),2)
        inventory['blocks'][1]['run_id']=5
        with self.assertRaises(ValueError):freeze_target(inventory,{'text':'x'*790+text})
