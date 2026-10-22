import base64,hashlib,json,unittest
from fl_decipher.archive_intake_v82 import *
URL=LABEL;STAMP='20260101000000';BODY=b'<html><title>FL: Kamri</title></html>'
def record(**kw):
 r={'timestamp':STAMP,'original':URL,'statuscode':'200','mimetype':'text/html','digest':base64.b32encode(hashlib.sha1(BODY).digest()).decode()};r.update(kw)
 return json.dumps([list(r),list(r.values())]).encode()
class ArchiveIntakeTests(unittest.TestCase):
 def test_exact_record(self):
  r=selection(record(),URL,'20261022000000');self.assertTrue(r['eligible']);self.assertIn(STAMP+'id_/',r['replay_url'])
 def test_missing_ambiguous_malformed(self):
  for raw in [b'[]',b'bad',json.dumps(json.loads(record())+[json.loads(record())[1]]).encode()]:self.assertFalse(selection(raw,URL,'20261022000000')['eligible'])
 def test_identity_time_and_digest(self):
  for kw in [{'original':URL+'?m=0'},{'timestamp':'20271301000000'},{'timestamp':'20270101000000'},{'digest':'bad'},{'statuscode':'302'}]:
   self.assertFalse(selection(record(**kw),URL,'20261022000000')['eligible'])
 def test_digest_and_memento(self):
  pick=selection(record(),URL,'20261022000000');hdr=b'HTTP/1.1 200 OK\r\nMemento-Datetime: Thu, 01 Jan 2026 00:00:00 GMT\r\n\r\n'
  self.assertTrue(all(archive_checks(BODY,hdr,pick).values()))
  self.assertFalse(archive_checks(BODY+b'changed',hdr,pick)['body_digest_matches_cdx'])
  self.assertFalse(archive_checks(BODY,b'',pick)['memento_matches_cdx'])
 def test_label_conflict_and_title(self):
  self.assertTrue(all(label_checks(BODY).values()))
  self.assertFalse(label_checks(BODY.replace(b'Kamri',b'Other'))['one_kamri_title'])
  self.assertFalse(label_checks(BODY+b'<link rel="canonical" href="https://evil.test">')['no_label_identity_conflict'])
 def test_cdx_parameters(self):
  from urllib.parse import urlsplit,parse_qs
  q=parse_qs(urlsplit(cdx_url(URL,'20261022000000')).query)
  self.assertEqual(q['url'],[URL]);self.assertEqual(q['limit'],['-1']);self.assertEqual(q['filter'],['statuscode:200','mimetype:text/html'])
if __name__=='__main__':unittest.main()
