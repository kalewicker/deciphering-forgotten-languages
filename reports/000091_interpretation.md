# E91: all documents accounted for; locators are centralized and layout unresolved

The complete offline census accounts for **180 archive entries** and decodes all
**89 document files** as strict UTF-8. The 86 numbered candidate files each occur
**exactly once, byte for byte, inside the combined edition**. These representations
must not be counted as independent material.

The index contains **86 distinct native article-shaped URL literals**. The
individual candidate files contain no URL literals, so a future provenance adapter
must link them to the index/catalog rather than infer provenance from filenames.
No link was fetched and no literal URL was authenticated as a native FL capture.

The fixed standalone-number/colon-label reader recognizes **zero numbered blocks**
and zero original-locator/language fields in the candidate files. This is an
unresolved schema result, not evidence that the documents contain no pairs or that
their language is absent. No real-layout repair was made after inspection. A usable
unit census and source-group capacity assessment remain unlaunched.

## Frozen procedure and complete denominators

The [protocol](../experiments/yid_schema_v91.md), code, nine synthetic fixtures,
verifier and E90 sealed archive were
[hash-bound](../experiments/yid_schema_v91.json) before document decoding. Every
nonpackaging regular member was checked against its E90 byte count and SHA-256,
then decoded without BOM/newline/Unicode normalization. Packaging remained opaque;
no document was extracted into an ordinary file, rendered or executed.

| Member disposition | Count |
|---|---:|
| Numbered article-candidate files | 86 |
| Index / sources catalog / combined edition | 1 / 1 / 1 |
| Packaging members, opaque by path | 90 |
| Directory entries | 1 |
| Unknown filename roles | 0 |
| Decoded documents / decode failures | 89 / 0 |
| Missing / repeated candidate filename numbers in 01..86 | 0 / 0 |

The 86 candidate names form a complete numbered set. That is filename accounting,
not verification of 86 genuine posts, separate source works, language identity or
semantic correctness. The author-claimed post count remains unverified.

## Exact duplication of representations

All **86/86 complete individual member byte strings** have one exact occurrence
inside ALL-TRANSLATIONS.txt. All 86 also have one match under the separately declared
boundary-newline view; the full-member result needs no such trimming. Complete
member hashes remain distinct, as E90 reported, while the combined representation
contains their entire contents. No document or duplicate was deleted.

The local containment ledger preserves exact byte offsets in the combined member,
with both original and boundary-newline counts. Text-field and URL spans instead
use Unicode code-point offsets in exact decoded members. These coordinate systems
are explicit and are never interchanged. A later corpus must avoid counting
individual and combined copies as separate observations.

## Locator inventory and parser limitations

| Document role | Native article-shaped URL occurrences | External URL occurrences |
|---|---:|---:|
| 86 individual candidate files | 0 | 0 |
| Combined edition | 0 | 0 |
| Index | 86 | 0 |
| Sources catalog | 108 | 271 |
| All decoded documents | 194 | 271 |

The index's 86 native-shaped literals are distinct. Across all documents there
are **312 distinct literal URL strings**; repeated occurrences stay visible.
URLs were captured literally, including any trailing punctuation, and checked
only for fixed syntax/host/path categories. They do not establish that a source
exists, matches a Yid passage, names a distinct work or creates an independent
group. This census does not join index rows to article candidates or adjudicate
external source identities.

All 86 candidate files have zero markers under the registered rule requiring
an integer followed by a period on its own line. Consequently no Yid/English
candidate blocks were produced, and the complete document is retained as its
prefix region. No text was omitted to force a partition. The zero paired-block
count is therefore a parser-recognition limit, not an estimate of the archive's
actual unit count.

No registered original-post or language fields were recognized in those files.
Because there is no recognized numbered marker, the scanner's nominal header
window covers the full candidate document. Its 68 other colon-field matches may
include ordinary body material and are not promoted to trustworthy headers.
The combined copy likewise has 68 matches; the index has two and the sources
catalog 258. Every field value/span remains recorded locally, but a true metadata
schema needs a dedicated adapter. A generic field match is not a verified header.

## Stop and next bounded step

E91 is complete and stopped. Do not repair its parser, reinterpret its zero as
missing content, or convert the 86 filenames/URLs into confirmed posts or groups.
The next justified task is a separately registered **format inspection and new
versioned adapter**, connecting individual documents with their index/catalog
locators and recognizing actual unit syntax. Discovery examples and inspected
format choices must be disclosed before the adapter is frozen for a complete
new census. Preserve unsupported layouts and missing/conflicting joins, with no
selection based on translations or model performance.

That work can use the already saved package; no new download is needed. Only a
later representation/corroboration and connected-group capacity decision can
justify a model panel. The documents are exposed annotations, with English
renderings and source claims quarantined as hypotheses. Prior payload exposure
is unknown. E79's Kamri development pass remains unconfirmed by new material;
this different declared-label resource is not a same-language confirmation.

No model, prediction, lexicon induction, native/source download, language
verification, source-identity admission, group admission or semantic review ran.
Natural semantic benchmark capacity remains **0/4 qualifying works**. All previous
sealed results, including stopped acquisition routes, remain unchanged.

## Verification and publication

The separate [offline verifier](../scripts/verify_yid_schema_v91.py) imports no
production census code. It reconstructs the member roles, exact decoded fields
and URL spans using line-oriented scanning, all prefix/block partitions, complete
combined byte occurrences and aggregate counts. Shared ZIP/regex libraries are
disclosed. Computational agreement does not independently authenticate native
text or validate the author's meanings. All twenty E90 sealed artifacts match
both their seals and the preceding local evidence checkpoint.

**653 workspace tests and 614 isolated-public tests pass**, with the same 39
archive-dependent exclusions. Nine new fixtures cover role/unknown/decode-failure
accounting, exact Unicode/BOM/CRLF offsets, locator restrictions and conflicts,
complete block partitions, malformed labels, auxiliary headers and both byte
containment modes. Unexpected inline layouts remain unsupported in the fixtures
and in the registered procedure; no after-result fallback was added.

Document bytes, title/header values, URLs, block and containment ledgers remain
local-only. Public main contains code, protocol, fixtures and aggregate reports
under PUBLICATION.md. Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_yid_schema_v91.py
```

Preparation and execution are single-use and refuse to overwrite their paths.
