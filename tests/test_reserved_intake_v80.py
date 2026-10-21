import unittest
from fl_decipher.reserved_intake_v80 import *
URL='https://'+HOST+'/2026/01/one.html'
def html(url=URL):
 return f'<link rel="canonical" href="{url}"><h3 class="post-title"><a href="{URL}">Title</a></h3><div class="post-body">opaque fixture</div><a rel="tag" href="{LABEL}">Kamri</a>'
class ReservedIntakeTests(unittest.TestCase):
 def test_strict_urls(self):
  self.assertEqual(key(URL+'?m=0'),URL);self.assertIsNone(key(URL+'?m=0',True))
  for u in [URL.replace('https:','http:'),URL+'#x',URL.replace(HOST,'evil.test'),URL.replace(HOST,HOST+':443')]:self.assertIsNone(key(u,True))
 def test_order_exposure_duplicate_cap(self):
  urls=[URL,URL]+[URL.replace('one',str(i)) for i in range(6)]
  raw=''.join(f'<h3 class="post-title"><a href="{u}">T</a></h3>' for u in urls).encode()
  r=select(raw,{URL});self.assertEqual([x['index'] for x in r['selected']],[2,3,4,5])
  self.assertEqual([r['candidates'][i]['reason'] for i in [0,1,6]],['previously_recorded','duplicate','over_cap'])
 def test_base_blocks_selection(self):
  r=select(('<base href="https://evil.test">'+html()).encode(),set());self.assertEqual(r['selected'],[])
 def test_positive_and_conflicting_identity(self):
  self.assertTrue(all(post_checks(html().encode(),{'url':URL,'title':'Title'}).values()))
  self.assertFalse(post_checks(html('https://evil.test').encode(),{'url':URL,'title':'Title'})['no_identity_conflict'])
 def test_body_and_label(self):
  r=post_checks((html()+'<div class="post-body">extra</div>').replace('>Kamri<','>Other<').encode(),{'url':URL,'title':'Title'})
  self.assertFalse(r['one_nonempty_body']);self.assertFalse(r['kamri_label'])
 def test_transport_failure_and_challenge(self):
  receipt={'curl_returncode':0,'http_status':200,'final_url':URL,'num_redirects':0,'content_type':'text/html'}
  headers=b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
  self.assertTrue(all(transport(b'<html>ok</html>',headers,receipt,URL).values()))
  self.assertFalse(transport(b'Verify you are human',headers,receipt,URL)['no_challenge'])
  self.assertFalse(transport(b'x',headers,receipt,URL+'x')['exact_url'])
if __name__=='__main__':unittest.main()
