"""Read untrusted plain-text annotations and locate independent textual evidence."""
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
import zipfile


def archive_inventory(path):
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        names = [x.filename for x in entries]
        if len(names) != len(set(names)) or len(entries) > 100:
            raise ValueError('Duplicate names or excessive member count')
        if sum(x.file_size for x in entries) > 20_000_000:
            raise ValueError('Expanded size exceeds audit bound')
        for x in entries:
            p = PurePosixPath(x.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in x.filename or len(p.parts)!=1:
                raise ValueError('Unsafe archive path')
            if stat.S_ISLNK(x.external_attr >> 16) or p.suffix != '.txt':
                raise ValueError('Only regular plain-text members admitted')
            if x.file_size > 2_000_000:
                raise ValueError('Oversized member')
        return [{'name':x.filename, 'bytes':x.file_size, 'compressed_bytes':x.compress_size, 'crc32':x.CRC} for x in entries]


def unpack(path, target):
    inventory = archive_inventory(path)
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(path) as z:
        for row in inventory:
            raw=z.read(row['name']); raw.decode('utf-8-sig')
            (target/row['name']).write_bytes(raw)
    return inventory


def field(text, label):
    match=re.search(r'(?m)^'+re.escape(label)+r': (.*)$',text)
    return match.group(1) if match else None


def parse_article(text, filename):
    starts=list(re.finditer(r'(?m)^(\d+)\.\s*\n(?=Kamri(?: Western)?:)',text))
    rows=[]
    for i,start in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(text)
        chunk=text[start.end():end]
        km=re.match(r'(Kamri(?: Western)?):\s*\n',chunk)
        em=re.search(r'(?m)^English:\s*\n',chunk)
        if km is None or em is None:
            raise ValueError(f'Missing pair label in {filename}')
        english=chunk[em.end():]
        stop=re.search(r'(?m)^(?:Paragraph\b|Verse\b|TRANSLATION NOTE\b|MATERIAL UNCERTAINTY\b|END OF TRANSLATION\b)',english)
        if stop:
            english=english[:stop.start()]
        fl=chunk[km.end():em.start()].strip()
        # Reading editions place the next paragraph/source locator after a blank
        # line. Keep that context as metadata; it is not translated prose.
        english=english.strip().split('\n\n',1)[0].strip()
        rows.append({'uid':f'{filename[:2]}:{int(start.group(1)):03d}', 'number':int(start.group(1)),
            'fl':fl, 'english':english, 'language':km.group(1),
            'annotation_span':[start.start(),end],
            'fl_words':len(fl.split()),'english_words':len(english.split())})
    claimed=field(text,'Translation status') or ''
    count=re.search(r'(\d+)/(\d+) units',claimed)
    basis=text.split('SOURCE BASIS\n',1)[-1].split('SENTENCE-BY-SENTENCE TRANSLATION',1)[0]
    notes=text.split('MATERIAL UNCERTAINTY\n',1)[1] if 'MATERIAL UNCERTAINTY\n' in text else None
    return {'file':filename,'entry':int(filename[:2]),'title':text.splitlines()[0],
        'language':field(text,'Language'),'original_url':field(text,'Original post'),
        'claimed_status':claimed,'claimed_unit_count':int(count.group(2)) if count else None,
        'claimed_verification':field(text,'Verification'),
        'source_basis':[line[2:].strip() for line in basis.splitlines() if line.startswith('- ')],
        'uncertainty_notes':notes,'units':rows}


def words(text):
    return re.findall(r"\w+(?:['’]\w+)*",unicodedata.normalize('NFKC',text).casefold())


def occurrences(needle, haystack, policy):
    """Return evidence offsets in the given view; normalized offsets are explicit."""
    if policy=='exact':
        a,b=needle,haystack
    elif policy=='whitespace':
        a,b=' '.join(needle.split()),' '.join(haystack.split())
    elif policy=='ordered_words':
        a,b=' '.join(words(needle)),' '.join(words(haystack))
    else:
        raise ValueError(policy)
    if not a:
        return []
    hits=[]; pos=0
    while (pos:=b.find(a,pos))>=0:
        end=pos+len(a)
        if policy!='ordered_words' or ((pos==0 or b[pos-1]==' ') and (end==len(b) or b[end]==' ')):
            hits.append([pos,end])
        pos+=1
    return hits


def compare(text, docs, *, group=None):
    matches=[]
    for docid,doc in docs.items():
        for policy in ('exact','whitespace','ordered_words'):
            hits=occurrences(text,doc['text'],policy)
            if hits:
                matches.append({'document_id':docid,'source_group':doc['source_group'],
                    'policy':policy,'occurrences':hits,'occurrence_count':len(hits),
                    'offset_basis':'Unicode code points in '+('exact saved text' if policy=='exact' else policy+' normalized view'),
                    'expected_group':group is None or doc['source_group']==group})
                break
    return matches


def normalized_view(text, policy):
    if policy == 'exact':
        return text
    if policy == 'whitespace':
        return ' '.join(text.split())
    if policy == 'ordered_words':
        return ' '.join(words(text))
    raise ValueError(policy)


def prepare_views(docs):
    return {key: {p: normalized_view(d['text'], p) for p in
                  ('exact', 'whitespace', 'ordered_words')} for key, d in docs.items()}


def locate(text, docs, views):
    matches = []
    for key, doc in docs.items():
        for policy in ('exact', 'whitespace', 'ordered_words'):
            needle = normalized_view(text, policy)
            haystack = views[key][policy]
            hits = []; pos = 0
            if not needle:
                continue
            while (pos := haystack.find(needle, pos)) >= 0:
                end = pos + len(needle)
                if policy != 'ordered_words' or ((pos == 0 or haystack[pos-1] == ' ') and
                                                (end == len(haystack) or haystack[end] == ' ')):
                    hits.append([pos, end])
                pos += 1
            if hits:
                matches.append({'document_id': key, 'source_group': doc['source_group'],
                    'policy': policy, 'occurrences': hits, 'occurrence_count': len(hits),
                    'offset_basis': 'Unicode code points in ' + policy + ' view'})
                break
    return matches
