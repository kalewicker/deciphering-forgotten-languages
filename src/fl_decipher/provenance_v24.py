"""Bounded transport and representation diagnostics; no correspondence scoring."""
import base64
import gzip
import hashlib
import io
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(raw):
    return {'bytes': len(raw), 'sha256': sha(raw),
            'sha1_base32': base64.b32encode(hashlib.sha1(raw).digest()).decode()}


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def decode_entity(raw, encoding, maximum):
    encoding = (encoding or 'identity').strip().lower()
    if encoding in ('identity', ''):
        decoded = raw
    elif encoding == 'gzip':
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            decoded = stream.read(maximum + 1)
    else:
        raise ValueError('unsupported content encoding: ' + encoding)
    if len(decoded) > maximum:
        raise ValueError('decoded size exceeds registered limit')
    return decoded


def window_gate(pages, counts):
    return (len(counts) == 2 and counts[0] == counts[1] and len(pages) == 5
            and [p['page_one_based'] for p in pages] == [90, 91, 92, 93, 94]
            and all(p['text_nonempty'] and p['text_equal'] and p['dimensions_equal']
                    and p['pixels_equal'] for p in pages))


def valid_redirect(url, original, count, maximum):
    p, o = urllib.parse.urlsplit(url), urllib.parse.urlsplit(original)
    return (count <= maximum and p.scheme == 'https' and p.hostname == o.hostname
            and p.port in (None, 443) and p.username is None and p.password is None)


class FiniteRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, original, directory, maximum):
        self.original, self.directory, self.maximum = original, directory, maximum
        self.trace = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed = valid_redirect(newurl, self.original, len(self.trace) + 1, self.maximum)
        self.trace.append({'from': req.full_url, 'to': newurl, 'status': code,
                           'allowed': allowed, 'headers': list(headers.items())})
        dump(self.directory/'redirects.json', self.trace)
        if not allowed:
            raise urllib.error.HTTPError(req.full_url, code, 'redirect refused', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire_child(directory, route, cfg):
    """Parent enforces a wall deadline; no automatic retry/proxy/cookie handler."""
    ctx = ssl.create_default_context()
    assert ctx.check_hostname and ctx.verify_mode == ssl.CERT_REQUIRED
    runtime = {'python': sys.version, 'executable': sys.executable, 'openssl': ssl.OPENSSL_VERSION,
               'verify_mode': int(ctx.verify_mode), 'check_hostname': ctx.check_hostname,
               'trust_store': ctx.cert_store_stats(), 'proxy_policy': 'explicit_empty',
               'accept_encoding': 'identity', 'content_decoding_automatic': False}
    dump(directory/'client.json', runtime)
    redirects = FiniteRedirects(route['url'], directory, cfg['max_redirects'])
    dump(directory/'redirects.json', [])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=ctx), redirects)
    request = urllib.request.Request(route['url'], headers={
        'User-Agent': cfg['user_agent'], 'Accept-Encoding': 'identity'}, method='GET')
    result = {'http_status': None, 'final_url': None, 'read_complete': False, 'error': None}
    response = None
    try:
        try:
            response = opener.open(request, timeout=cfg['socket_timeout_seconds'])
        except urllib.error.HTTPError as error:
            response = error
            result['error'] = f'HTTPError: {error.code} {error.reason}'
        with response:
            result.update(http_status=response.code, final_url=response.geturl())
            dump(directory/'headers.json', list(response.headers.items()))
            (directory/'headers.txt').write_text(str(response.headers))
            total = 0
            with (directory/'body.bin').open('xb') as stream:
                while True:
                    part = response.read1(min(65536, cfg['max_body_bytes'] + 1 - total))
                    if not part:
                        result['read_complete'] = True
                        break
                    stream.write(part);stream.flush();total += len(part)
                    if total > cfg['max_body_bytes']:
                        result['error'] = 'received body exceeds registered limit'
                        break
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    dump(directory/'child_result.json', result)
