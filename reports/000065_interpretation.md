# Experiment 65: one explicit unlinked identifier recovered from 29 reference rows

The registered offline recovery is complete. The saved development post has
**29 reference-tail rows**. Exactly **one** has a recognized direct identifier:
`arxiv:0812.0349`, printed in the Weinstein entry as `arXiv.org:0812.0349`.
The other **28 rows** remain unresolved for direct identifier retrieval; they
have not been discarded, repaired or declared unidentifiable by author/title.
No source was selected or requested, and no passage comparison was performed.

This is an explicitly exposed development exercise. Preparatory inspection had
already revealed the bibliography layout, opening Aissen entry and Weinstein
identifier before registration. The successful recovery is not a blind
prediction or evidence that the post's opaque text conveys the cited work.
E64's earlier **zero recognized URL identifiers** remains correct for its
URL-only scope. E65 adds a separate textual-metadata scope without editing it.

## Fixed-scope accounting

| Quantity | Result |
| --- | ---: |
| Saved post/body derivatives | 1 / 1 |
| Original-coordinate Unicode characters | 12,344 |
| Included nonempty text leaves | 70 |
| Nonempty direct-child owner runs | 48 |
| Matches to the disclosed reference-tail boundary | 1 |
| Retained reference-tail rows | 29 |
| Reference rows with recognized identifier syntax | 1 |
| Reference rows without recognized direct identifier | 28 |
| Identifier occurrences, whole-body scope | 1 |
| Malformed/cross-owner identifier occurrences | 0 |
| Duplicate recognized occurrences | 0 |
| Recognized identifiers in frozen known-URL inventory | 0 |
| Source selections / source requests / research requests | 0 / 0 / 0 |

All retained text reproduces E64 exactly. Leaf coordinates come from DOM
traversal, including distinct positions for repeated text. The reference tail
starts at character 7605 and ends at 12344. The fixed disclosed marker is a
snapshot-specific boundary, not a general bibliography detector. Every nonempty
owner run after that boundary is retained, without author/year eligibility
filters. Literal year witnesses do not authenticate publication dates.

The identifier is in reference row **27** (zero-based), owner run **46**. Its
full labelled witness is at Unicode span **[12104, 12123)**; the identifier token
is **[12114, 12123)**. The entry itself spans **[12051, 12124)**. These coordinates
refer to the sealed E64 body text, not raw HTML byte offsets. Leading zeroes are
preserved. No explicit version suffix is present, so its version is
**unspecified**, not inferred as v1. The displayed author, title and 2008 year
remain unverified citation metadata; identifier syntax is not successful source
resolution or a pinned edition.

The complete scan covers labelled arXiv/arXiv.org identifiers, labelled DOI
identifiers/doi.org URLs and bare syntactic DOI tokens throughout the body,
including before the reference tail. It does not infer identifiers from topics,
opaque text or author/title searches. No recognized identifier occurs outside
the tail. The frozen known-URL inventory lacks this identifier, but that
inventory is incomplete: absence does not establish novelty, independent work
grouping, lack of earlier exposure or untouched test eligibility.

## Verification and stop

Eight new adversarial fixtures cover repeated strings, complete-tail retention,
missing/duplicate boundaries, explicit and unspecified versions, duplicate/known
identifiers, malformed and cross-owner tokens, runtime/comment exclusion, DOI
overlap and export refusal. **492 full-workspace tests** and **453 isolated-public
snapshot tests** pass; the same **39** archive-dependent tests are excluded
publicly. The separate verifier reproduces all 70 leaves, 48 owner runs, 29
reference rows, year witnesses and the complete identifier inventory without
importing production E65 functions. It shares BeautifulSoup parsing and the
sealed E37 URL recognizer used only for exposure comparison. This same-agent
verification is not independent scientific review.

All **64 prior run manifests and historical deliverable seals** remain intact.
E63's original gate is still false; E64's restricted metadata view is unchanged;
E62's ANITA/publisher route remains closed. There are zero new confirmed
connected works, independent reviews, untouched units, lexical/alignment scores
or semantic/source-identity admissions. Natural-benchmark capacity remains unmet.
See [verification](000065_verification.json) and the new deliverable seal.
Raw/derived outputs stay local in `data/v65/{preflight,reference_inventory}.json`
and `runs/000065_textual_references`.

The next useful bounded step is a separately registered **single-identifier
arXiv source-feasibility acquisition**. Fix selection to the first recovered
recognized identifier in the tail, set request/redirect/byte limits in advance,
verify the record's title/authors and version history, freeze a dated edition,
and retain a mismatch/unavailable outcome without replacement. Bundle routine
metadata/capture checks into that acquisition rather than adding another HTML
identity audit. Any later passage relationship test requires its own fixed
comparison scope and controls; no semantic test is authorized by this recovery.
