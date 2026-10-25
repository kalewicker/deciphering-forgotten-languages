"""Bounded ZIP metadata/integrity inspection; never extract or parse documents."""
from collections import Counter, defaultdict
import hashlib
import re
import stat
import unicodedata
from urllib.parse import urlsplit
import zipfile
import zlib

MAX_BODY = 64*1024*1024
MAX_ENTRIES = 1000
MAX_TOTAL = 256*1024*1024
MAX_MEMBER = 32*1024*1024
MAX_RATIO = 1000


def allowed_url(url):
    try:
        u = urlsplit(url)
        host = (u.hostname or '').lower()
        return (u.scheme == 'https' and not u.username and not u.password and
                u.port in (None, 443) and not u.fragment and
                any(host == base or host.endswith('.'+base)
                    for base in ('dropbox.com', 'dropboxusercontent.com')))
    except ValueError:
        return False


def download_url(offered):
    assert allowed_url(offered) and urlsplit(offered).hostname == 'www.dropbox.com'
    assert offered.endswith('&dl=0') and offered.count('dl=') == 1
    return offered[:-1]+'1'


def transport(hops, complete, aggregate_bytes):
    if not hops:
        return False
    last = hops[-1]
    headers = {k.lower(): [] for k, _ in last['headers']}
    for k, v in last['headers']:
        headers[k.lower()].append(v)
    encoding = headers.get('content-encoding', [])
    length = headers.get('content-length', [])
    try:
        length_ok = not length or (len(length) == 1 and int(length[0]) == last['body_bytes'])
    except ValueError:
        length_ok = False
    return bool(complete and last['status'] == 200 and allowed_url(last['url']) and
                0 < last['body_bytes'] <= aggregate_bytes <= MAX_BODY and length_ok and
                (not encoding or encoding == ['identity']))


def inventory(path):
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        return {'zip_readable': False, 'entries': [], 'archive_reasons': ['unreadable_zip'],
                'metadata_pass': False, 'integrity_pass': False, 'error': type(error).__name__,
                'duplicate_classes': [], 'suffix_counts': {}}
    with archive:
        infos = archive.infolist()
        entries = []
        names = []
        for i, info in enumerate(infos):
            name = info.orig_filename
            isdir = info.is_dir()
            clean = name[:-1] if isdir else name
            parts = clean.split('/')
            reasons = []
            if (not clean or name.startswith('/') or '\\' in name or
                re.match(r'^[A-Za-z]:', name) or any(p in ('', '.', '..') for p in parts) or
                any(ord(c) < 32 or ord(c) == 127 for c in name)):
                reasons.append('unsafe_name')
            mode = info.external_attr >> 16
            typ = stat.S_IFMT(mode)
            if typ not in (0, stat.S_IFREG, stat.S_IFDIR) or (typ == stat.S_IFDIR and not isdir) or (typ == stat.S_IFREG and isdir):
                reasons.append('unsafe_type')
            if info.flag_bits & 1:
                reasons.append('encrypted')
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                reasons.append('unsupported_compression')
            if info.file_size > MAX_MEMBER:
                reasons.append('member_size_limit')
            if info.file_size and (not info.compress_size or info.file_size > MAX_RATIO*info.compress_size):
                reasons.append('ratio_limit')
            if isdir and info.file_size:
                reasons.append('nonempty_directory')
            normalized = unicodedata.normalize('NFC', clean).casefold()
            names.append(normalized)
            entries.append({'index': i, 'name': name, 'bytes': info.file_size,
                            'compressed_bytes': info.compress_size, 'crc32': info.CRC,
                            'compression': info.compress_type, 'flags': info.flag_bits,
                            'unix_type': typ, 'directory': isdir, 'header_offset': info.header_offset,
                            'metadata_reasons': reasons, 'read_status': 'not_read'})
        counts = Counter(names)
        files = {n for n, e in zip(names, entries) if not e['directory']}
        for n, e in zip(names, entries):
            if counts[n] > 1:
                e['metadata_reasons'].append('name_collision')
            if any('/'.join(n.split('/')[:j]) in files for j in range(1,len(n.split('/')))):
                e['metadata_reasons'].append('file_ancestor')
        reasons = []
        if not infos:
            reasons.append('empty_archive')
        if len(infos) > MAX_ENTRIES:
            reasons.append('entry_limit')
        if sum(i.file_size for i in infos if not i.is_dir()) > MAX_TOTAL:
            reasons.append('total_size_limit')
        metadata_pass = not reasons and all(not e['metadata_reasons'] for e in entries)
        result = {'zip_readable': True, 'entries': entries, 'archive_reasons': reasons,
                  'metadata_pass': metadata_pass, 'integrity_pass': False,
                  'duplicate_classes': [], 'suffix_counts': dict(sorted(Counter(
                      (e['name'].rsplit('/',1)[-1].rsplit('.',1)[-1].lower()
                       if '.' in e['name'].rsplit('/',1)[-1] else '<none>')
                      for e in entries if not e['directory']).items()))}
        if not metadata_pass:
            return result
        total = 0
        for info, entry in zip(infos, entries):
            if info.is_dir():
                entry['read_status'] = 'directory'
                continue
            try:
                digest = hashlib.sha256(); size = 0; crc = 0
                with archive.open(info) as stream:
                    while block := stream.read(65536):
                        size += len(block); total += len(block)
                        if size > MAX_MEMBER or total > MAX_TOTAL:
                            raise ValueError('actual_size_limit')
                        digest.update(block); crc = zlib.crc32(block, crc)
                if size != info.file_size or crc != info.CRC:
                    raise ValueError('size_or_crc_mismatch')
                entry.update(read_status='verified', actual_bytes=size,
                             sha256=digest.hexdigest(), crc_verified=True)
            except Exception as error:
                entry.update(read_status='failed', error=type(error).__name__)
                return result
        classes = defaultdict(list)
        for e in entries:
            if not e['directory']:
                classes[e['sha256'], e['actual_bytes']].append(e['index'])
        result['duplicate_classes'] = [
            {'sha256': h, 'bytes': size, 'member_indices': indices}
            for (h,size),indices in sorted(classes.items()) if len(indices) > 1]
        result['integrity_pass'] = True
        return result
