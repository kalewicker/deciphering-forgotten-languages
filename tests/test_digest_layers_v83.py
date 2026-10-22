import base64,hashlib,json,unittest
from fl_decipher.digest_layers_v83 import *
def row():
 return json.dumps([['timestamp','original','statuscode','mimetype','digest'],['20260101000000','https://example.com/','200','text/html','A'*32]]).encode()
class DigestLayerTests(unittest.TestCase):
 def test_exact_cdx_and_malformed(self):
  self.assertEqual(cdx_record(row())['digest'],'A'*32)
  for raw in [b'[]',b'not json',row().replace(b'"digest"',b'"other"')]:
   with self.assertRaises((ValueError,AssertionError)):cdx_record(raw)
 def test_overlapping_positions_and_zeros(self):
  self.assertEqual(positions(b'aaaa','aa'),[0,1,2]);self.assertEqual(positions(b'none','wombat.js'),[])
 def test_headers_preserve_repeats_and_ignore_connect(self):
  raw=b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 200\r\nContent-Encoding: gzip\r\nContent-Encoding: br\r\n\r\n'
  h=headers(raw);self.assertTrue(h[0]['ignored']);self.assertFalse(h[1]['ignored'])
  self.assertEqual(h[1]['fields']['content-encoding'],['gzip','br'])
 def test_signatures(self):
  r=describe(b'\x1f\x8bmore',b'',[],{},'A'*32);self.assertTrue(r['prefix_signatures']['gzip'])
  r=describe(b'\xef\xbb\xbfmore',b'',[],{},'A'*32);self.assertTrue(r['prefix_signatures']['utf8_bom'])
 def test_hashes_and_size_layers(self):
  b=b'unchanged';digest=base64.b32encode(hashlib.sha1(b).digest()).decode()
  r=describe(b,b'HTTP/2 200\r\nContent-Encoding: gzip\r\n\r\n',['curl','--compressed'],{'size_download':2},digest)
  self.assertTrue(r['saved_body_matches_cdx']);self.assertTrue(r['download_size_differs_from_saved'])
  self.assertFalse(r['prefix_signatures']['gzip'])
 def test_every_marker_and_missing_metadata_retained(self):
  r=describe(b'wombat.js',b'',[],{},'A'*32)
  self.assertEqual(set(r['marker_positions']),set(MARKERS));self.assertEqual(r['marker_positions']['wombat.js'],[0])
  self.assertIsNone(r['telemetry_size_download']);self.assertFalse(r['download_size_differs_from_saved'])
if __name__=='__main__':unittest.main()
