# E65: offline textual-reference recovery in the admitted development post

This development registration follows E64 and preparatory inspection of the
saved post's tail and direct-child layout. Before registration we saw the
Aissen opening entry, bibliography-like tail, Weinstein entry, and unlinked
`arXiv.org:0812.0349`. This is an exposed recovery exercise, not blind discovery.
No network request, source selection, passage comparison or semantic scoring is
permitted. E63's failed gate and E62's closed ANITA route remain unchanged.

## Fixed scope and complete accounting

Use only E63's sealed raw bytes and E64's admitted 12,344-character derivative.
Require exactly one div.post-body. Preserve original DOM tag indices and raw
parent hash; exclude script/style/noscript and join stripped text leaves with
one space, exactly reproducing E64. Map each included text leaf by traversal,
never by searching for its first occurrence. Unicode spans are half-open.
Partition text into runs owned by its direct post-body child; retain any direct
text child as its own run. Retain all nonempty runs, even outside the reference
tail. Empty layout nodes add no text. Reject an export mismatch.

The disclosed boundary is the unique direct-child div whose joined text begins
`Aissen, Judith (2003).`. Retain every nonempty run from that child through the
end as a reference-tail row, without author/year validity filters or repairs.
If the boundary is missing or ambiguous, preserve all runs, report an unresolved
tail and select no replacement. This is a snapshot-specific development scope,
not a general bibliography detector or authenticated reference list. Record
all literal four-digit 18xx/19xx/20xx year witnesses, without inferring dates.

Scan the *entire* derivative, including outside the tail, for case-insensitive
labelled arXiv/arXiv.org colon tokens, labelled DOI colon tokens or doi.org URLs,
and unlabelled 10.<4-9 digits>/<nonspace> DOI tokens. Retain malformed labelled
occurrences and duplicate identifiers. Strip only terminal . , ; ) ] } from the
token. Require the complete arXiv token to be modern 4digits.4-5digits or legacy
letters/hyphens[.letters/hyphens]/7digits, optionally v<positive integer>;
DOIs require 10.<4-9 digits>/<nonspace>. Syntax recognition is not resolution.
Record exact prefix/token spans, literal spellings, declared version separately,
base identifier, reference membership and duplicate-of position. No joins across
reference rows create a token; reject a token spanning multiple owner runs.
An absent explicit arXiv version remains unspecified, never inferred as v1.
Overlapping DOI detections coalesce into the earlier labelled occurrence.

Compare recognized base identifiers with the frozen E63 known-URL inventory
using the sealed E37 URL recognizer. Absence from that incomplete inventory
means only 'not recorded', not a new work, independent source or untouched unit.
All reference rows without a recognized identifier remain unresolved for direct
identifier retrieval; author/title-only recovery is outside this budget.

## Outcome and stop

Write a complete run/leaf/reference/identifier inventory and counts, including
zero-reference/no-valid-identifier outcomes. Do not rank references by topic or
opaque text, silently repair metadata, search titles or request an identifier.
Successful recovery means exact original-coordinate replay and complete fixed
scope accounting; it does not require finding an identifier. A future separately
registered acquisition may select a recovered identifier under a fixed rule,
verify title/authors/version history, freeze an edition and check exposure before
any passage relationship test. No natural-benchmark capacity is gained here.

Freeze protocol, inputs, implementation and targeted adversarial fixtures before
execution. A separate same-agent verifier reconstructs leaf offsets/runs and
identifier witnesses without importing production E65 functions, validates
all 64 prior manifests/seals and preserves the old false E63 gate. This remains
engineering verification, not independent scientific review. Keep raw and
derived research outputs local; publish only registration/code/tests/report and
small verification/seal receipts.
