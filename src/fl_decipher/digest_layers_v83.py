"""Byte-structure accounting; no body transformation or content selection."""
import base64,hashlib,json,re
MARKERS=['BEGIN WAYBACK TOOLBAR INSERT','END WAYBACK TOOLBAR INSERT','wombat.js','bundle-playback.js',
         'web-static.archive.org','__wm.init','WB_wombat_Init']
FIELDS=['content-type','content-encoding','content-length','transfer-encoding',
        'x-archive-orig-content-type','x-archive-orig-content-encoding','x-archive-orig-content-length',
        'x-archive-orig-transfer-encoding','memento-datetime','x-archive-src']

def cdx_record(raw):
 value=json.loads(raw)
 assert type(value) is list and len(value)==2 and value[0]==['timestamp','original','statuscode','mimetype','digest']
 assert type(value[1]) is list and len(value[1])==5 and all(type(s) is str for s in value[1])
 result=dict(zip(value[0],value[1]));assert re.fullmatch('[A-Z2-7]{32}',result['digest'])
 return result

def headers(raw):
 blocks=[];current=None
 for line in raw.decode('iso-8859-1').splitlines():
  if m:=re.match(r'^HTTP/\S+\s+(\d+)(?:\s+(.*))?$',line):
   current={'status':int(m[1]),'ignored':int(m[1])<200 or (m[2] or '').strip().lower()=='connection established','fields':{k:[] for k in FIELDS}}
   blocks.append(current)
  elif current is not None and ':' in line:
   key,value=line.split(':',1)
   if key.lower() in current['fields']:current['fields'][key.lower()].append(value.strip())
  elif not line:current=None
 return blocks

def positions(raw,marker):
 out=[];start=0;needle=marker.encode('ascii')
 while (i:=raw.find(needle,start))>=0:out.append(i);start=i+1
 return out

def describe(body,header_bytes,command,telemetry,expected):
 blocks=headers(header_bytes);app=[b for b in blocks if not b['ignored']]
 final=app[-1]['fields'] if app else {k:[] for k in FIELDS}
 digest=base64.b32encode(hashlib.sha1(body).digest()).decode().rstrip('=')
 return {'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'body_sha1_base32':digest,
 'cdx_digest':expected,'saved_body_matches_cdx':digest==expected,'header_blocks':blocks,'final_fields':final,
 'curl_compressed':'--compressed' in command,'telemetry_size_download':telemetry.get('size_download'),
 'download_size_differs_from_saved':telemetry.get('size_download') is not None and telemetry['size_download']!=len(body),
 'prefix_signatures':{'gzip':body.startswith(b'\x1f\x8b'),'utf8_bom':body.startswith(b'\xef\xbb\xbf'),
 'utf16_le_bom':body.startswith(b'\xff\xfe'),'utf16_be_bom':body.startswith(b'\xfe\xff')},
 'marker_positions':{s:positions(body,s) for s in MARKERS}}
