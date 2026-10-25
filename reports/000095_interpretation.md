# E95: source claims are uneven; no explicit package-to-source span map is supplied

The fixed audit covers **all 8 source-catalog claims for candidates 01, 43 and 86**.
All eight have a citation and literal URL; seven have a Role field. Only one gives
explicit external passage locations: the printed page ranges claimed for candidate
01's 22 prose units. None of the eight entries supplies an explicit mapping from
package pair ordinals to source passage spans.

These are findings about what the supplied catalog specifies, not whether the
sources exist or support its translations. No source was fetched or independently
verified. Missing information here may exist in the author's other artifacts.

## Scope, exposure and evidence

The [protocol](../experiments/source_claim_audit_v95.md) and
[registration](../experiments/source_claim_audit_v95.json) fixed candidates 01, 43
and 86 and every associated source bullet before this audit's inspection. Candidate
01's catalog entry had already been exposed during E92 development; the complete
catalog had been machine-parsed then. The audit is not blind or independent review.

Exact E92 row/claim spans were checked against the saved archive's SOURCES member.
The selected rows and all **24 citation/URL/Role evidence spans** are preserved
locally. No new HTML inspection, source fetch, text comparison, model run or corpus
selection occurred. Manual classifications were authored after reading the entries,
as planned for a descriptive audit; the report does not present them as predictions.

| Candidate | Claims | What the catalog specifies | Remaining limitation |
|---|---:|---|---|
| 01 | 2 | A local heading parallel identified as S002; an external exact-wording claim for all 22 prose units, first printed pages 254–256 then 252–253 | The external unit ID and prose count are not an explicit package-ordinal/source-span map; wording claim remains untested |
| 43 | 5 | One ordered primary-source claim for 34/36 units; title/context and embedded-English source claims; a site-authored question bridge and one-word answer described through contextual constraints | No ordinal subset for the 34 units, no page ranges, and no package row IDs for the two bridges |
| 86 | 1 | One citation and PDF locator | No Role field, coverage statement, passage locator or unit mapping |

Candidate 43's main source is named as a Richard Sproat article. Other entries
name Ian Hodder and a Susan Pearce-edited collection, and two point to the native
post itself. The 34-of-36 count and two site-authored descriptions must not be
converted into a verified disjoint partition of the 36 package units. The catalog
does not supply that mapping. Its embedded-English claim is not, by itself,
evidence for the meanings of opaque text.

Candidate 86 names Philip E. Gibbs's *Consciousness Bootstrapped*. The absence of
a Role field means its exact relationship to the 242 package pairs is unspecified
in this entry. It does not show that the citation is wrong or that no alignment
exists elsewhere.

## Strongest next falsifiable question

The most concrete next candidate is **01's second claim**: the Burton work,
*The Jew, The Gypsy and El Islam*, with printed pages 254–256 followed by 252–253.
Its explicit page ranges and claimed 22-unit prose coverage make a bounded wording
test more specific than an open-ended search over candidate 43 or 86's sources.
The catalog supplies a Gutenberg text locator, but retrieval feasibility has not
been tested. This is a lead, not a verified edition or source match.

A next protocol should freeze one exact offered source representation and a small
acquisition budget, establish whether its edition/page markers actually support
those printed ranges, and compare **all 22 claimed prose renderings**, in order,
against only those ranges. Explicitly exclude the separately claimed heading.
Any assignment of package ordinals to those prose units must be documented as a
new test hypothesis, not an existing author-provided map. Preserve absent page
markers, edition ambiguity, mismatches and discontinuities; do not search other
editions or enlarge the window after results. If page ranges cannot be bound in
the offered representation, stop that test as unresolved rather than silently
searching the whole work.

Even a successful wording test would establish correspondence of the supplied
English to a cited source passage, not independent translation accuracy, direction
of copying or uniquely identified opaque word meanings. A later falsification
design needs alternatives/controls and independent review before semantic claims.
E95 does not launch acquisition or that comparison.

## Result and limits

The earlier browser-save matches resolve text correspondence for three exposed
examples. This audit shows why they cannot yet be used as a uniformly labeled
parallel corpus: source relationships vary, and per-unit evidence links are not
explicitly supplied by these entries. The reading edition's omitted evidence
labels remain an obstacle; we did not recreate them from fluent English.

All eight claims remain in the ledger, including weak and contextual ones.
No independence, language identity, translation validity or benchmark admission
was inferred. Semantic capacity remains **0/4**, with zero new untouched units.
The audit is complete; more page collection or model tuning is not pending.

## Verification and publication

A separate read-only verifier imports no audit recorder. It checks registration
and output hashes, complete 3-post/8-claim coverage, all 24 exact evidence spans,
field counts and printed-page specificity. It checks the integrity of manual
assessments, not their independent scholarly correctness. Its code was written
after the audit; that timing is disclosed.

All prior E92/E93/E94 deliverable seals were checked before inspection. E94's
sealed artifacts also match the preceding local evidence checkpoint at closeout.
Local links, Python syntax and diff whitespace were checked. No model or comparator
code changed, so their suites were not rerun: E94's 675 workspace and 636 isolated
public passes remain historical results. Audit replay passed on the saved evidence.

Public main contains this aggregate report, protocol, audit recorder and verifier.
Full catalog entries, locators and assessment evidence remain local-only. Replay:

```sh
.venv/bin/python scripts/verify_source_claim_audit_v95.py
```

The recorder is single-use and refuses an existing run directory. Do not rerun it
to revise a finding; future corrections require new versioned artifacts.
