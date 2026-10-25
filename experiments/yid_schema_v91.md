# E91: complete package schema and declared-provenance census

## Purpose and scope

E90 acquired an intact 180-entry archive and stopped before reading documents.
Census its saved bytes offline to establish what representations and declared
locators are present before proposing any Yid corpus or predictor. This is
exposed third-party annotation, not native FL authentication or semantic gold.
Member names/sizes and E90's duplicate metadata were inspected for design; no
content schema was inspected before this registration.

Freeze this protocol, new implementation/tests/verifier, E90's seal and all its
bound artifacts before decoding. Inspect all 180 entries in central order.
Directory entries are directories; names under __MACOSX/ are packaging by path
only and remain opaque. Other regular members are assigned fixed filename roles:
00-INDEX.txt index, SOURCES.txt source catalog, ALL-TRANSLATIONS.txt combined;
NN-*.txt with NN in 01..86 are article candidates; everything else is other.
Roles and numbering do not authenticate articles or post count. Retain all missing,
repeated or extra candidate numbers, malformed files and decode failures.

No network, extraction to ordinary files, rendering, instructions execution,
source download, prediction, lexicon induction, mask construction or grouping.
Read each nonpackaging regular member directly from the sealed ZIP; verify its
E90 SHA-256 and byte count before strict UTF-8 decoding. Keep BOM/newlines/raw
Unicode intact; never repair encoding or replace a failed document. All span
coordinates are Unicode code points in the exact decoded member, except combined
byte-containment offsets, explicitly labeled as bytes in the original member.

## Fixed descriptive measurements

For every decodable document record full hash/size, first nonempty-line title
candidate and all header fields before the first numbered-block marker. A header
field is an ASCII-letter label followed by a colon, on one line; record exact
label/value spans without interpreting the value as truth. Treat normalized label
names 'original post', 'original url', 'post url', 'fl url' as declared original
locators, and 'language' as a declared language field. Normalization of FIELD
NAMES only is strip/lower/collapse-whitespace. Values retain exact non-horizontal-
whitespace spans. Record missing, repeated and conflicting fields separately.
A valid declared native locator must be absolute http/https, exact FL native host,
/YYYY/MM/slug.html path, no userinfo, explicit port, query or fragment. Do not fix
http, queries, trailing punctuation or alternate hosts to manufacture validity.
Every locator remains a supplied claim, even if syntactically valid.

Also inventory all literal http/https URL-shaped strings in every decoded
member, with exact spans and classification (native-article-shaped, other-native,
external, malformed). Match until whitespace or a literal angle bracket/quote;
retain trailing punctuation as captured, without repair. No link is fetched or
assumed to identify a source work. Shared or distinct URLs do not create verified
independent groups. Count raw occurrences and distinct literal strings separately.

For article-candidate files, partition the entire document into a prefix plus
numbered blocks. Markers are lines containing an integer followed by '.' and
optional horizontal whitespace, with no other text. Preserve each ordinal and
number; do not assume all markers are actual sentence boundaries. Within each
block, enumerate standalone Yid: and English: label lines. A structurally paired
candidate has exactly one of each, in Yid-then-English order, with nonempty
whitespace-trimmed regions after each label. The English region extends to the
end of the numbered block; trailing notes may remain and are NOT silently clipped.
This is a candidate field span, not verified sentence segmentation or a gold
English rendering. Retain missing/duplicate/reversed/empty-label block reasons.
Retain all blocks and a complete prefix/block coordinate partition. Never select
only successful blocks for a corpus or silently coerce inline/alternate labels.
Report whether marker numbers are consecutive from one; failure is descriptive.
Unit counts are structural candidate counts, not corroborated FL sentences.

For every article-candidate file, measure all exact occurrences of its FULL raw
member bytes inside the combined member. Separately measure a declared boundary-
newline view, removing only CR/LF bytes at the two ends of the candidate. Keep both
counts and offsets even if they differ. Neither mode normalizes interior content,
rescues an admission gate or establishes source identity. Combined editions and
individual files are not independent observations. Do not count their prose twice
for capacity. No near-duplicate text search or source alignment in this census.

## Outputs, verification and stop

Save all 180 member dispositions, text-header/URL/block ledgers, complete byte
containment records, per-file failures and aggregate counts locally. Public main
contains code, fixtures, registration and aggregate interpretation, not document
contents. A schema census has no scientific pass threshold: preserve all observed
layouts, including zero paired blocks or unknown locators. This protocol is fixed
before inspection; do not repair a parser after seeing unexpected real layouts.
Any necessary future format adapter requires a separate registration.

Synthetic fixtures precede freezing and cover exact offsets, header conflicts,
strict locator rules, label order/empties, complete partition, BOM/newlines,
complete-versus-boundary-newline containment and unknown/decode-failed members.
A separate verifier imports no production census code. It checks archive/member
hashes, role counts, metadata/URL spans, all block partitions and complete combined
containment, and reproduces aggregate accounting with a separate line-oriented
implementation. Shared ZIP and regex libraries are disclosed. This is computational
record verification, not independent review of meanings or source claims.

Stop after this one census regardless of what is present. A later native-text
corroboration, connected-group/corpus capacity assessment, schema adapter or model
comparison needs its own justification and protocol. Do not designate these
annotations untouched, infer corpus size from filenames, use English claims as
answers, authenticate a language, promote source identity or confirm E79's Kamri
result on another declared label. All prior sealed results and failures remain
unchanged. New semantic benchmark admissions remain 0/4 qualifying works.
