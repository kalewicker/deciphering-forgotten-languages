import io
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from fl_decipher.yid_archive_v90 import allowed_url,download_url,inventory,transport


def sample(members):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,body in members:z.writestr(name,body)
    return stream.getvalue()


class ArchiveTests(unittest.TestCase):
    def inspect(self,raw):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'a.zip';path.write_bytes(raw)
            return inventory(path)

    def test_exact_download_transform(self):
        url='https://www.dropbox.com/scl/fi/a/x.zip?rlkey=b&st=c&dl=0'
        self.assertEqual(download_url(url),url[:-1]+'1')
        with self.assertRaises(AssertionError):download_url(url+'&dl=0')

    def test_redirect_domains_and_credentials(self):
        for u in ['https://dl.dropboxusercontent.com/a','https://www.dropbox.com/a','https://dropbox.com:443/a']:
            self.assertTrue(allowed_url(u))
        for u in ['http://dropbox.com/a','https://dropbox.com.evil.test/a','https://evildropbox.com/a',
                  'https://u:p@dropbox.com/a','https://dropbox.com:444/a','https://dropbox.com/a#x']:
            self.assertFalse(allowed_url(u))

    def test_transport_entity_checks(self):
        hop={'url':'https://dropbox.com/a','status':200,'headers':[('Content-Length','3')],'body_bytes':3}
        self.assertTrue(transport([hop],True,3))
        self.assertFalse(transport([hop],False,3))
        self.assertFalse(transport([hop|{'headers':[('Content-Length','4')]}],True,3))
        self.assertFalse(transport([hop|{'headers':[('Content-Encoding','gzip')]}],True,3))
        self.assertFalse(transport([hop|{'status':403}],True,3))

    def test_complete_inventory_and_duplicates_without_extraction(self):
        r=self.inspect(sample([('folder/',b''),('folder/a.txt',b'abc'),('b.txt',b'abc'),('c.bin',b'different')]))
        self.assertTrue(r['integrity_pass']);self.assertEqual(len(r['entries']),4)
        self.assertEqual(r['duplicate_classes'][0]['member_indices'],[1,2])
        self.assertEqual(r['suffix_counts'],{'bin':1,'txt':2})

    def test_unsafe_paths_keep_full_denominator(self):
        r=self.inspect(sample([('../a.txt',b'a'),('C:/b.txt',b'b'),('a\\b.txt',b'c'),('ok.txt',b'd')]))
        self.assertFalse(r['metadata_pass']);self.assertEqual(len(r['entries']),4)
        self.assertTrue(all(e['read_status']=='not_read' for e in r['entries']))

    def test_name_collisions_and_file_ancestors(self):
        r=self.inspect(sample([('A.txt',b'a'),('a.txt',b'b'),('parent',b'c'),('parent/child',b'd')]))
        self.assertIn('name_collision',r['entries'][0]['metadata_reasons'])
        self.assertIn('file_ancestor',r['entries'][3]['metadata_reasons'])

    def test_symlink_rejected(self):
        info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
        self.assertIn('unsafe_type',self.inspect(sample([(info,b'target')]))['entries'][0]['metadata_reasons'])

    def test_encrypted_flag_rejected(self):
        raw=bytearray(sample([('a.txt',b'abc')]))
        central=raw.index(b'PK\x01\x02');struct.pack_into('<H',raw,central+8,1)
        self.assertIn('encrypted',self.inspect(raw)['entries'][0]['metadata_reasons'])

    def test_metadata_limits_before_member_reads(self):
        with patch('fl_decipher.yid_archive_v90.MAX_MEMBER',2):
            r=self.inspect(sample([('a.txt',b'abc')]))
        self.assertIn('member_size_limit',r['entries'][0]['metadata_reasons'])
        self.assertEqual(r['entries'][0]['read_status'],'not_read')

    def test_crc_corruption_fails_without_partial_pass(self):
        raw=bytearray(sample([('a.txt',b'abc')]))
        central=raw.index(b'PK\x01\x02');struct.pack_into('<I',raw,central+16,0)
        r=self.inspect(raw)
        self.assertTrue(r['metadata_pass']);self.assertFalse(r['integrity_pass'])
        self.assertEqual(r['entries'][0]['read_status'],'failed')

    def test_empty_or_nonzip_rejected(self):
        self.assertFalse(self.inspect(b'<html>preview</html>')['zip_readable'])
        self.assertIn('empty_archive',self.inspect(sample([]))['archive_reasons'])


if __name__=='__main__':unittest.main()
