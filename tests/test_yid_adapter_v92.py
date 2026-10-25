import unittest
from fl_decipher.yid_adapter_v92 import units,catalog,join,census

U='https://forgottenlanguages-full.forgottenlanguages.org/2020/01/example.html'
I=f'Preface\n\n1. Title\n   File: 01-example.txt\n   Original: {U}\n   Sentence pairs: 1\n'
S=f'Preface\n\n1. Title\nTranslation file: 01-example.txt\nOriginal post: {U}\nSources:\n- Citation\n  URL: https://example.org/source\n  Role: Claim only\n'

class AdapterTests(unittest.TestCase):
    def test_exact_unicode_crlf_partition(self):
        t='\r\nα\r\nEnglish\r\n \t\r\nlast\r\n'
        p=units(t)
        self.assertEqual(''.join(t[a['span'][0]:a['span'][1]] for a in p),t)
        self.assertEqual(t[slice(*p[1]['candidate_yid_span'])],'α')
        self.assertTrue(p[1]['paired_candidate']);self.assertFalse(p[3]['paired_candidate'])
    def test_no_silent_pairing_across_blank(self):
        for t in ['one\n\ntwo','one\ntwo\nthree','one','']:
            self.assertEqual(sum(x.get('paired_candidate',False) for x in units(t)),0)
    def test_unicode_line_separator_not_split(self):
        p=units('a\u2028b\nEnglish')
        self.assertTrue(p[0]['paired_candidate']);self.assertEqual(p[0]['lines'][0]['value'],'a\u2028b')
    def test_exact_catalog_join(self):
        result=join('01-example.txt',1,units('a\nb'),catalog(I),catalog(S,True))
        self.assertTrue(result['resolved_layout_and_join']);self.assertEqual(result['declared_pairs'],1)
    def test_duplicate_fields_and_rows_fail(self):
        for x in [I+'   File: 01-example.txt\n',I+I]:
            r=join('01-example.txt',1,units('a\nb'),catalog(x),catalog(S,True))
            self.assertFalse(r['resolved_layout_and_join'])
    def test_conflict_and_count_fail(self):
        r=join('01-example.txt',1,units('a\nb\n\nc\nd'),catalog(I),catalog(S.replace('/example.html','/other.html'),True))
        self.assertIn('locator_conflict',r['reasons']);self.assertIn('declared_count_mismatch',r['reasons'])
    def test_claims_spans_and_unmatched_rows(self):
        s=S+'- Second\n  Role: Uncertain\n'
        c=catalog(s,True);self.assertEqual(len(c['rows'][0]['claims']),2)
        for claim in c['rows'][0]['claims']:
            self.assertTrue(s[slice(*claim['span'])].startswith('- '))
        r=census({'01-example.txt':'a\nb','00-INDEX.txt':I.replace('01-example.txt','99-missing.txt'),'SOURCES.txt':s})
        self.assertEqual(r['summary']['unresolved_index_rows'],1)
        self.assertEqual(r['summary']['resolved_documents'],0)
    def test_duplicate_representations_excluded_missing_aux_reported(self):
        r=census({'01-example.txt':'a\nb','ALL-TRANSLATIONS.txt':'a\nb','00-INDEX.txt':'- YID-LEXICON.txt — listed\n'+I,'SOURCES.txt':S})
        self.assertEqual(r['summary']['parsed_candidate_pairs'],1)
        self.assertEqual(r['summary']['missing_index_named_auxiliary_files'],['YID-LEXICON.txt'])
    def test_empty_document_is_unresolved(self):
        r=join('01-example.txt',1,[],catalog(I.replace('pairs: 1','pairs: 0')),catalog(S,True))
        self.assertIn('empty_document',r['reasons'])
