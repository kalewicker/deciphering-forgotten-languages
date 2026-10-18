"""Neutral external-review packets and fail-closed return validation."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


INSTRUCTIONS = '''# External source and passage review

The proposed publisher source is disclosed as a candidate, not an established match.
The FL material is a dated archive, not a current-site capture. Both research groups
were previously exposed development material. Your task is independent source and
passage review, not translation from an unknown language or held-out evaluation.

Read material_manifest.json first. Inspect the fixed publisher page images and
the archived FL body. The unchanged full publisher PDF is included for provenance;
restrict evidence pairs to the supplied publisher window text and fixed pages.
Record out-of-window coverage needs in uncertainty_notes; do not silently expand
the window. Text exports retain extraction artifacts, footnotes and page-edge
continuations. PDF/image layout governs reading; exact saved text governs offsets.

Declare your identity, human/automated role, identifier, prior exposure and whether
you are independent of the project's prior predictions. This declaration is evidence
to assess, not proof of independence. No prior predictions or reading translations
are supplied. The candidate pairing is disclosed, so this is not blinded retrieval.

Copy review_return_template.json into a new file. Leave packet originals unchanged.
Record language-scope observations, boundary checks, source relationship and source
coverage. Supported, rejected and uncertain findings are equally welcome. Empty
evidence/counterexample lists are permitted for an uncertain finding. Support or
rejection needs at least one scoped evidence pair; do not manufacture one to finish.
Explain uncertainty and distinguish literal shared-language quotations/citations
from inferred relationships, copied names and structural resemblance. Names, counts,
word order or plausible paraphrase cannot establish unknown-language word meanings.

Span offsets are half-open [start,end) Python Unicode code-point offsets in the
exact bundled UTF-8 fl_post.txt or publisher_window.txt, including whitespace and
the final newline. Each span's text must equal that exact slice. Do not count UTF-8
bytes or UTF-16 code units. Both texts' hashes and lengths are in the manifest.

Use source_relationship supported/rejected/uncertain; coverage full/partial/none/
uncertain. For each evidence or counterexample pair, use relationship supports/
contradicts/uncertain and basis literal_shared_language/citation/name_only/
structural_only/other. Include notes explaining what the evidence can establish.
No word-gloss field is provided. Language labels can be unknown or tentative.

Each language_observations item has these exact keys:
    {"fl_span": {"start": INTEGER, "end": INTEGER, "text": "EXACT SLICE"},
     "language": "YOUR OBSERVATION", "certainty": "certain|tentative|unknown",
     "notes": "BASIS AND LIMITS"}
Each evidence_pairs or counterexamples item has these exact keys:
    {"fl_span": {"start": INTEGER, "end": INTEGER, "text": "EXACT FL SLICE"},
     "source_span": {"start": INTEGER, "end": INTEGER, "text": "EXACT SOURCE SLICE"},
     "basis": "ONE BASIS FROM THE LIST ABOVE", "relationship": "supports|contradicts|uncertain",
     "notes": "WHAT THIS PAIR DOES AND DOES NOT SUPPORT"}
These are field guides, not JSON values to copy literally. Set review_completed true
only when finished and completed_at_utc to an ISO timestamp with +00:00 or Z.
For human reviewers, identifier can be your name plus a chosen stable review ID;
for an automated reviewer, use a distinct run/session identifier. prior_exposure
must describe exposure, including an explicit statement when there was none.

A structurally valid return is ready only for adjudication. It cannot itself admit
source identity, semantic labels or untouched-test status. Completed review and
scientific acceptance are separate. Return your new JSON file to the project owner;
no email address, external upload or contact is configured by this packet.
'''


def template(nominee_id, packet_sha):
    return {'schema_version': 1, 'nominee_id': nominee_id, 'packet_manifest_sha256': packet_sha,
            'reviewer': {'name': None, 'kind': None, 'identifier': None,
                         'independent_of_prior_predictions': None, 'prior_exposure': None},
            'review_completed': False, 'completed_at_utc': None, 'language_observations': [],
            'source_relationship': 'uncertain', 'coverage': 'uncertain',
            'statement_boundaries_checked': None, 'evidence_pairs': [], 'counterexamples': [],
            'uncertainty_notes': []}


def validate_return(value, manifest, manifest_sha, texts):
    """Record review claims for later adjudication; never auto-admit a label."""
    errors = []
    expected = set(template(manifest['nominee_id'], manifest_sha))
    nonempty = lambda v: isinstance(v, str) and bool(v.strip())
    def keys(obj, fields, at):
        if not isinstance(obj, dict):
            errors.append(at+': expected object');return False
        if set(obj) != set(fields):
            errors.append(at+': missing or unrecognized fields')
        return True
    def span(s, text, at):
        if not keys(s, ['start','end','text'], at):
            return
        start,end = s.get('start'),s.get('end')
        if type(start) is not int or type(end) is not int or not (0 <= start < end <= len(text)):
            errors.append(at+': invalid Unicode code-point bounds')
        elif s.get('text') != text[start:end]:
            errors.append(at+': quote differs from exact saved slice')
    if not keys(value, expected, 'return'):
        return result(errors)
    if value.get('schema_version') != 1 or type(value.get('schema_version')) is not int:
        errors.append('schema_version: expected integer 1')
    for key,expected_value in [('nominee_id',manifest['nominee_id']),('packet_manifest_sha256',manifest_sha)]:
        if value.get(key) != expected_value:
            errors.append(key+': packet binding mismatch')
    for key,name in [('fl','fl_post.txt'),('source','publisher_window.txt')]:
        if key not in texts or sha(texts[key].encode('utf-8')) != manifest['members'][name]['sha256']:
            errors.append(name+': saved text hash mismatch')
    reviewer = value.get('reviewer')
    if keys(reviewer,['name','kind','identifier','independent_of_prior_predictions','prior_exposure'],'reviewer'):
        for key in ['name','identifier','prior_exposure']:
            if not nonempty(reviewer.get(key)):
                errors.append('reviewer.'+key+': explicit declaration required')
        if reviewer.get('kind') not in ['human','automated']:
            errors.append('reviewer.kind: human or automated required')
        if reviewer.get('independent_of_prior_predictions') is not True:
            errors.append('reviewer.independent_of_prior_predictions: true declaration required')
    if value.get('review_completed') is not True:
        errors.append('review_completed: unfinished return')
    try:
        stamp=datetime.fromisoformat(value.get('completed_at_utc'))
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('UTC required')
    except (ValueError,TypeError):
        errors.append('completed_at_utc: explicit UTC timestamp required')
    if type(value.get('statement_boundaries_checked')) is not bool:
        errors.append('statement_boundaries_checked: explicit true/false required')
    if value.get('source_relationship') not in ['supported','rejected','uncertain']:
        errors.append('source_relationship: invalid assessment')
    if value.get('coverage') not in ['full','partial','none','uncertain']:
        errors.append('coverage: invalid scope')
    observations=value.get('language_observations')
    if not isinstance(observations,list) or not observations:
        errors.append('language_observations: at least one scoped observation required')
    else:
        for i,obs in enumerate(observations):
            at=f'language_observations[{i}]'
            if keys(obs,['fl_span','language','certainty','notes'],at):
                span(obs.get('fl_span'),texts.get('fl',''),at+'.fl_span')
                if not nonempty(obs.get('language')) or not nonempty(obs.get('notes')) or obs.get('certainty') not in ['certain','tentative','unknown']:
                    errors.append(at+': language, certainty and explanatory notes required')
    for name in ['evidence_pairs','counterexamples']:
        pairs=value.get(name)
        if not isinstance(pairs,list):
            errors.append(name+': expected list');continue
        for i,pair in enumerate(pairs):
            at=f'{name}[{i}]'
            if keys(pair,['fl_span','source_span','basis','relationship','notes'],at):
                span(pair.get('fl_span'),texts.get('fl',''),at+'.fl_span')
                span(pair.get('source_span'),texts.get('source',''),at+'.source_span')
                if pair.get('basis') not in ['literal_shared_language','citation','name_only','structural_only','other']:
                    errors.append(at+': invalid evidence basis')
                if pair.get('relationship') not in ['supports','contradicts','uncertain'] or not nonempty(pair.get('notes')):
                    errors.append(at+': relationship and notes required')
    if value.get('source_relationship') in ['supported','rejected'] and not (value.get('evidence_pairs') or value.get('counterexamples')):
        errors.append('source_relationship: support/rejection requires scoped evidence')
    notes=value.get('uncertainty_notes')
    if not isinstance(notes,list) or not notes or not all(nonempty(x) for x in notes):
        errors.append('uncertainty_notes: nonempty explicit limitations required')
    return result(errors)


def result(errors):
    return {'structurally_valid': not errors, 'ready_for_adjudication': not errors, 'errors': errors,
            'independence_externally_verified': False, 'source_identity_admitted': False,
            'semantic_labels_admitted': 0, 'untouched_test_units_admitted': 0}


def build_packet(root, destination, nominee):
    destination.mkdir(parents=True,exist_ok=False)
    contents = {name:(root/path).read_bytes() for name,path in nominee['members'].items()}
    contents['INSTRUCTIONS.md'] = INSTRUCTIONS.encode('utf-8')
    for name,data in contents.items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest={'schema_version':1,'nominee_id':nominee['id'],'fl_url':nominee['fl_url'],
              'publisher_url':nominee['publisher_url'],'archive_timestamp':nominee['archive_timestamp'],
              'publisher_pages_one_based':nominee['pages_one_based'],'fl_material':'dated_archive',
              'candidate_source_pairing_disclosed':True,'prior_predictions_included':False,
              'source_relationship_accepted':False,'whole_post_source_coverage_established':False,
              'previously_exposed_development_group':True,'offset_basis':'half-open Python Unicode code points in exact UTF-8 text, including final newline',
              'text_code_point_lengths':{name:len(contents[name].decode('utf-8')) for name in ['fl_post.txt','publisher_window.txt']},
              'members':{name:{'sha256':sha(data),'bytes':len(data)} for name,data in sorted(contents.items())}}
    raw=encoded(manifest);(destination/'material_manifest.json').write_bytes(raw)
    (destination/'review_return_template.json').write_bytes(encoded(template(nominee['id'],sha(raw))))
    archive=destination.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(p for p in destination.rglob('*') if p.is_file()):
            info=zipfile.ZipInfo(str(path.relative_to(destination)),date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644 << 16
            z.writestr(info,path.read_bytes())
    return {'nominee_id':nominee['id'],'packet':str(destination.relative_to(root)),
            'zip':str(archive.relative_to(root)),'zip_sha256':sha(archive.read_bytes()),
            'manifest_sha256':sha(raw),'members':len(manifest['members'])+2,
            'review_state':'awaiting_independent_return'}
