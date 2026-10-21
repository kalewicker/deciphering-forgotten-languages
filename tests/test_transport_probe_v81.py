import json,unittest
from scripts.transport_probe_v81 import classify
URL='https://example.com/'
def py(status=200,**kw):
 return json.dumps({'status':status,'url':URL,'headers':[],'verification_enabled':True,'method':'HEAD','body_read':False,**kw}).encode()
class TransportTests(unittest.TestCase):
 def test_http_error_still_establishes_response(self):
  self.assertEqual(classify('python',URL,0,False,py(403))['classification'],'http_response_observed')
 def test_connection_error_is_unresolved(self):
  self.assertEqual(classify('python',URL,0,False,py(None))['classification'],'transport_unresolved')
 def test_redirect_not_followed(self):
  self.assertEqual(classify('python',URL,0,False,py(302))['http_status'],302)
  self.assertFalse(classify('python',URL,0,False,py(url=URL+'changed'))['metadata_valid'])
 def test_limits_and_malformed(self):
  for raw in [b'',b'not-json',b'x'*65537]:self.assertFalse(classify('python',URL,0,False,raw)['metadata_valid'])
  self.assertFalse(classify('python',URL,0,True,py())['metadata_valid'])
 def test_verification_and_no_body_required(self):
  self.assertFalse(classify('python',URL,0,False,py(verification_enabled=False))['metadata_valid'])
  self.assertFalse(classify('python',URL,0,False,py(body_read=True))['metadata_valid'])
 def test_curl_evidence(self):
  raw=json.dumps({'http_code':200,'url_effective':URL,'num_redirects':0,'ssl_verify_result':0}).encode()
  self.assertTrue(classify('curl',URL,0,False,raw,b'HTTP/1.1 200 OK\r\n')['metadata_valid'])
  self.assertFalse(classify('curl',URL,35,False,raw,b'HTTP/1.1 200 OK\r\n')['metadata_valid'])
  self.assertFalse(classify('curl',URL,0,False,raw,b'HTTP/1.1 403 Forbidden\r\n')['metadata_valid'])
if __name__=='__main__':unittest.main()
