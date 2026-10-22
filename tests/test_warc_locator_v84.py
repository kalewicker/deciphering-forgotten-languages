import json,unittest
from fl_decipher.warc_locator_v84 import *
SRC={'item':'safe-item','file':'one.warc.gz','reference':'safe-item/one.warc.gz'}
REC=dict(zip(FIELDS[:5],['20260222130841','https://example.com/','200','text/html','A'*32]))
def loc(**kw):
 r=REC|{'filename':SRC['file'],'offset':'100','length':'200'}|kw
 return json.dumps([FIELDS,[r[k] for k in FIELDS]]).encode()
def item(**kw):return json.dumps({'metadata':{'identifier':SRC['item']},'files':[{'name':SRC['file'],'size':'500',**kw}]}).encode()
class WarcLocatorTests(unittest.TestCase):
 def test_safe_header_derivation(self):
  self.assertEqual(source(b'x-archive-src: safe-item/one.warc.gz\r\n'),SRC)
  for s in ['../one.warc.gz','safe-item/../one.warc.gz','safe-item/file.txt']:
   with self.assertRaises(AssertionError):source(('x-archive-src: '+s).encode())
 def test_missing_redacted_fields(self):
  for raw in [b'[]',b'{}',b'notjson',loc(offset='-'),loc(length=None)]:self.assertFalse(locator(raw,REC,SRC)['eligible'])
 def test_exact_record_and_size_cap(self):
  self.assertTrue(locator(loc(),REC,SRC)['eligible'])
  for kw in [{'timestamp':'20260101000000'},{'filename':'other.warc.gz'},{'length':'2097153'},{'offset':100}]:self.assertFalse(locator(loc(**kw),REC,SRC)['eligible'])
 def test_range_bounds(self):
  l=locator(loc(),REC,SRC);i=inventory(item(),SRC)
  self.assertEqual(decision(l,i,SRC)['range'],'bytes=100-299')
  self.assertFalse(decision(l,i|{'file_size':299},SRC)['bounded_record_feasible'])
 def test_private_unknown_flags(self):
  for value in [True,'true',None,'unknown',1]:self.assertFalse(inventory(item(private=value),SRC)['eligible'])
  for value in [False,'false',0,'0']:self.assertTrue(inventory(item(private=value),SRC)['eligible'])
 def test_duplicate_files_bad_sizes(self):
  x=json.loads(item());x['files']*=2;self.assertFalse(inventory(json.dumps(x).encode(),SRC)['eligible'])
  for size in [True,0,'-',-1]:self.assertFalse(inventory(item(size=size),SRC)['eligible'])
if __name__=='__main__':unittest.main()
