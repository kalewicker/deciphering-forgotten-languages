import unittest
from fl_decipher.yid_schema_v91 import scan,role,native_locator,containment,summary

HOST='https://forgottenlanguages-full.forgottenlanguages.org'
TEXT='\ufeffTitle\r\nLanguage: Yid\r\nOriginal post: '+HOST+'/2020/01/test.html\r\n\r\n1.\r\nYid:\r\n  ä β  \r\nEnglish:\r\n  A B.  \r\n'


class SchemaTests(unittest.TestCase):
    def test_roles_unknown_and_packaging(self):
        self.assertEqual([role(n) for n in ['x/01-a.txt','x/00-INDEX.txt','x/SOURCES.txt','x/ALL-TRANSLATIONS.txt','__MACOSX/._a.txt','x/87-a.txt']],
                         ['article_candidate','index','sources','combined','packaging','other'])
        self.assertEqual(role('x/',True),'directory')

    def test_unicode_offsets_and_bom_newlines(self):
        r=scan(TEXT,True)
        self.assertEqual(r['characters'],len(TEXT));self.assertEqual(r['title_candidate']['value'],'\ufeffTitle')
        for field in r['header_fields']:self.assertEqual(TEXT[slice(*field['value_span'])],field['value'])
        self.assertEqual(TEXT[slice(*r['blocks'][0]['yid_region'])],'ä β')
        self.assertEqual(TEXT[slice(*r['blocks'][0]['english_region'])],'A B.')
        self.assertTrue(r['blocks'][0]['paired_candidate'])

    def test_conflicts_and_repeats_are_not_repaired(self):
        r=scan('Language: Yid\nLanguage: Other\nOriginal post: '+HOST+'/2000/01/a.html\nOriginal URL: '+HOST+'/2000/01/b.html\n',True)
        self.assertTrue(r['locator_repeated']);self.assertTrue(r['locator_conflict']);self.assertTrue(r['language_conflict'])
        self.assertEqual(len(r['declared_locators']),2)

    def test_strict_locator_and_url_offsets(self):
        good=HOST+'/2020/01/a.html';self.assertTrue(native_locator(good))
        for u in [good+'?x=1',good+'#x',good+',',good.replace('.org/','.org:443/'),good.replace('https://','https://u@')]:
            self.assertFalse(native_locator(u))
        r=scan('See '+good+' and https://example.test/a).')
        self.assertEqual(r['urls'][1]['value'],'https://example.test/a).')
        for u in r['urls']:self.assertEqual(('See '+good+' and https://example.test/a).')[slice(*u['span'])],u['value'])

    def test_bad_blocks_preserved_and_complete_partition(self):
        text='prefix\n1.\nYid:\n A\nEnglish:\n B\n3.\nEnglish:\n C\nYid:\n D\n4.\nYid:\n\nEnglish:\n X\n5.\nYid:\n Y\n'
        r=scan(text,True);self.assertEqual(len(r['blocks']),4);self.assertFalse(r['marker_numbers_consecutive'])
        self.assertEqual(sum(b['paired_candidate'] for b in r['blocks']),1)
        spans=[r['header_span']]+[b['span'] for b in r['blocks']]
        self.assertEqual(spans[0][0],0);self.assertEqual(spans[-1][1],len(text))
        self.assertTrue(all(a[1]==b[0] for a,b in zip(spans,spans[1:])))
        self.assertIn('label_order',r['blocks'][1]['reasons'])
        self.assertIn('empty_yid_region',r['blocks'][2]['reasons'])
        self.assertIn('english_label_count',r['blocks'][3]['reasons'])

    def test_duplicate_labels_and_inline_layout_unresolved(self):
        r=scan('1.\nYid:\n A\nYid:\n B\nEnglish:\n C\n',True)
        self.assertIn('yid_label_count',r['blocks'][0]['reasons'])
        r=scan('1.\nYid: A\nEnglish: B\n',True)
        self.assertFalse(r['blocks'][0]['paired_candidate'])

    def test_exact_and_boundary_newline_containment_separate(self):
        self.assertEqual(containment(b'abc\n',b'xxabcxx')['full_member'],[])
        self.assertEqual(containment(b'abc\n',b'xxabcxx')['boundary_newline_view'],[[2,5]])
        self.assertEqual(len(containment(b'abc',b'abcabc')['full_member']),2)
        self.assertEqual(containment(b'\n',b'abc')['boundary_newline_view'],[])

    def test_all_statuses_retained_in_summary(self):
        rows=[{'role':'article_candidate','status':'decode_failed'}, {'role':'other','status':'decoded','scan':scan('unknown')},
              {'role':'packaging','status':'opaque_packaging'},{'role':'directory','status':'directory'}]
        r=summary(rows,[])
        self.assertEqual(r['members'],4);self.assertEqual(r['decoded_documents'],1)
        self.assertEqual(r['statuses']['decode_failed'],1);self.assertEqual(r['decoded_article_candidates'],0)

    def test_auxiliary_header_stops_at_marker_without_creating_blocks(self):
        r=scan('Language: Header\n1.\nLanguage: Body\n')
        self.assertEqual(r['declared_languages'],['Header']);self.assertEqual(r['blocks'],[])


if __name__=='__main__':unittest.main()
