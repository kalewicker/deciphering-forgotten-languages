import tempfile, unittest, zipfile, stat
from pathlib import Path
from fl_decipher.dataset_audit_v15 import archive_inventory,parse_article,occurrences,locate,prepare_views
class DatasetAuditTests(unittest.TestCase):
 def bad_zip(self,entries):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'a.zip'
   with zipfile.ZipFile(p,'w') as z:
    for name,text in entries:z.writestr(name,text)
   with self.assertRaises(ValueError):archive_inventory(p)
 def test_archive_traversal_rejected(self): self.bad_zip([('../a.txt','x')])
 def test_archive_executable_rejected(self):self.bad_zip([('run.py','x')])
 def test_archive_duplicates_rejected(self):self.bad_zip([('a.txt','x'),('a.txt','y')])
 def test_archive_symlink_rejected(self):
  i=zipfile.ZipInfo('a.txt');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16
  self.bad_zip([(i,'target')])
 def test_reading_locator_excluded_and_western_retained(self):
  a=parse_article('Title\nLanguage: Kamri Western\nTranslation status: Complete: 2/2 units translated.\n1.\nKamri Western:\nFa so.\n\nEnglish:\nOne two.\n\nAzazel, verse 2\n\n2.\nKamri Western:\nLa.\n\nEnglish:\nThree.\n\nTRANSLATION NOTE\nNo omitted units.','25-test.txt')
  self.assertEqual([x['english'] for x in a['units']],['One two.','Three.']);self.assertEqual(a['units'][0]['language'],'Kamri Western')
 def test_ordered_words_require_whole_boundaries(self):
  self.assertFalse(occurrences('he','the theatre','ordered_words'));self.assertEqual(occurrences('he','he he','ordered_words'),[[0,2],[3,5]])
 def test_normalization_is_not_paraphrase(self):
  self.assertTrue(occurrences('A, B!','a b','ordered_words'));self.assertFalse(occurrences('A better world','An improved world','ordered_words'))
 def test_all_occurrences_and_document_identity_retained(self):
  docs={'wrong':{'text':'One two. One two.','source_group':'wrong'}}
  hits=locate('One two.',docs,prepare_views(docs));self.assertEqual(hits[0]['occurrence_count'],2);self.assertEqual(hits[0]['source_group'],'wrong')
if __name__=='__main__':unittest.main()
