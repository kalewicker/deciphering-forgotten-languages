"""Bounded read-only source inventory and lexical date witnesses; never run TeX."""
import gzip
import hashlib
import io
from pathlib import PurePosixPath
import re
import tarfile

EXPANDED_LIMIT = 64 * 1024 * 1024
MEMBER_LIMIT = 1000
FILE_LIMIT = 4 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory(raw):
    """Return regular-file bytes in memory; reject unsafe or oversized containers."""
    try:
        compressed = raw.startswith(b'\x1f\x8b')
        if compressed:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                raw = stream.read(EXPANDED_LIMIT + 1)
        if len(raw) > EXPANDED_LIMIT:
            raise ValueError('expanded byte limit')
        files = {}
        try:
            archive = tarfile.open(fileobj=io.BytesIO(raw), mode='r:')
        except tarfile.ReadError:
            # Single TeX submissions are supported only with a documentclass marker.
            if len(raw) > FILE_LIMIT or b'\\documentclass' not in raw or b'\x00' in raw:
                raise ValueError('unsupported container or non-TeX single file')
            files['single_source.tex'] = raw
            return {'available': True, 'format': 'gzip-single-tex' if compressed else 'single-tex',
                    'expanded_bytes': len(raw)}, files
        with archive:
            members = 0
            total = 0
            seen = set()
            for member in archive:
                members += 1
                name = member.name
                parts = PurePosixPath(name).parts
                if (members > MEMBER_LIMIT or not name or name.startswith('/') or '..' in parts
                        or '\\' in name or re.match(r'^[A-Za-z]:', name) or name in seen):
                    raise ValueError('unsafe, duplicate, or excessive member names')
                seen.add(name)
                if member.isdir():
                    continue
                if not member.isfile() or member.size < 0 or member.size > FILE_LIMIT:
                    raise ValueError('nonregular or oversized member')
                total += member.size
                if total > EXPANDED_LIMIT:
                    raise ValueError('member byte limit')
                stream = archive.extractfile(member)
                content = stream.read(FILE_LIMIT + 1)
                if len(content) != member.size:
                    raise ValueError('member size mismatch')
                files[name] = content
        return {'available': True, 'format': 'gzip-tar' if compressed else 'tar',
                'expanded_bytes': len(raw), 'member_count': members}, files
    except (ValueError, OSError, EOFError, tarfile.TarError) as error:
        return {'available': False, 'reason': str(error)}, {}


def date_witnesses(text):
    """Lexical witnesses on non-comment line prefixes, not a TeX interpreter."""
    result = []
    offset = 0
    pattern = re.compile(r'\\(?:date|today|documentclass|maketitle)\b|\\begin\s*\{document\}')
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        # TeX percent comments, ignoring percent signs with an odd escape count.
        end = len(line)
        for match in re.finditer('%', line):
            preceding = len(line[:match.start()]) - len(line[:match.start()].rstrip('\\'))
            if preceding % 2 == 0:
                end = match.start()
                break
        for match in pattern.finditer(line[:end]):
            result.append({'command': match.group(), 'span': [offset + match.start(), offset + match.end()],
                           'line': line_number, 'line_span': [offset, offset + len(line)], 'line_text': line})
        offset += len(line)
    return result
