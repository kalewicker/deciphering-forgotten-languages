# Experiment 63: a different post's raw snapshot is saved; admission gate fails

This pilot recovers **209,306 raw HTML bytes** for the first E37 nominee outside
the ANITA post: Quantum Semantic Fields and Universals. The archive record,
exact query-bearing replay URL, timestamp, SHA1 digest, known title and unique
nonempty post body agree. **Nine of ten registered post checks pass.** The page
has **no canonical or og:url fields**, so the registered identity-metadata
requirement fails. The admitted-target export is unavailable, and citation
selection/source acquisition are skipped as registered.

Raw availability has advanced; accepted material readiness has not. The run's
`archival_target_recovered: false` and `post_recovery_unavailable` describe
failure of the combined admission gate, not absence of a downloaded snapshot.
The complete bytes, headers, telemetry, gate and receipts remain preserved.

| Component | Observed outcome |
| --- | --- |
| Post choice | Original E37 post01, first non-post00 nominee, not a new content-based ranking |
| Archive index | HTTP200; one exact original URL, including m=0 |
| Raw replay | HTTP200; no redirect; exact selected replay URL |
| Capture timestamp | 2026-01-11 04:18:40 UTC |
| CDX SHA1 digest | B42DVQZQYYN4UKT6CANAKNVPKRETRELQ; matches decoded saved body |
| Final-response Memento timestamp | Matches the selected record |
| Title and post body | Expected title present; exactly one nonempty post-body |
| Canonical / og:url metadata | Zero fields; required metadata check fails |
| Citation and source stages | Skipped, not assessed as having zero citations |

Raw replay SHA-256:
`750cdd667b03b53724b7589b9b66dbbf46aef0e6e1d07e6b7251bc409961a59e`.

## Why this was the next evidence route

E62 closed the ANITA/native-publisher comparator route. E37 had also nominated
three different FL posts, but only indexed material and incomplete citation
metadata were available for them. The fixed first remaining nominee provides a
bounded opportunity to recover different source-first material without another
search or extending the closed comparator cohort. It is already exposed
through its search/indexed record; it is not an untouched test post or a
confirmed new connected source group.

The exact original URL retains its saved m=0 query. No canonical/mobile URL
alternative, second timestamp, other post or replacement citation was attempted.
The known-exposure input preserves the original E37 URLs and later known arXiv
works. No proposed translation or lexical answer was used to select the post.

The three-route budget permitted one index, one exact replay and at most one
new explicit arXiv source. Actual use was **two routes and two application
responses**, with zero new searches, retries, redirects, source requests or
opaque-text comparisons. The unused source slot remains in the denominator.
No bibliography was extracted after the gate failed; no statement about the
post's actual citation inventory follows from the skipped stage.

## Interpretation and design limit

The failed field is a schema requirement I registered for this pilot. The
independent archive URL/digest/time/title checks pass, while the HTML does not
supply the required identity metadata. Missing fields do not by themselves
show that the saved page is the wrong post. They also cannot be counted as
passing a requirement that explicitly demanded their presence.

The correct recorded result is therefore **raw snapshot saved, registered
admission failed**. No criterion is relaxed and no E63 output is rewritten to
turn the result positive. Why the template lacks the fields is not established.
A later offline provenance adjudication could assess whether the exact archive
chain justifies a different representation/admission policy. Any changed policy
would be a disclosed development revision, not a successful replay of this
preregistered gate. Another live download would not be justified merely to
seek a template with more favorable metadata.

The capture is dated 2026, despite a 2013 date in the post URL. It does not
authenticate the publication-year wording, current text, copying direction,
source relationship, full-source coverage or any opaque meaning. The pilot
adds no confirmed new connected work, independent review, semantic label,
source-identity admission or untouched test unit. Qualifying reviewed works
remain zero and the natural-benchmark capacity remains unmet.

## Verification and next bounded decision

Six new fixtures cover original nomination order, exact original/query/digest
requirements, query-bearing replay and canonical binding, bad digest/Memento/
identity/body/challenge cases, explicit source identifier order/known-work
exclusions/cap, and missing eligible citations. **476 local tests** and **437
isolated-public snapshot tests** pass; the same 39 archive-dependent tests are
explicitly excluded publicly.

The separate verifier reproduces request commands, timing, receipts and hashes;
the exact CDX record; Memento/digest/title/body/identity checks; the skipped
citation/source stages; and complete route/slot accounting. It does not import
the production v63 gate functions, but shares BeautifulSoup HTML parsing. The
source-acquisition branch is fixture-tested only and was not exercised on a new
natural source. Same-agent verification is not independent scientific review.
All **62 earlier run manifests and historical deliverable seals** remain intact.
See [verification](000063_verification.json).

Detailed raw material remains local in `data/v63/acquisition/{metadata,replay}`;
the known-exposure snapshot is `data/v63_registration/known_exposure.json` and
the completed run is `runs/000063_new_material`. No old evidence was overwritten.

Next: one **offline provenance/admission decision on these saved bytes**, explicitly
separating the strong archive-chain observations from missing HTML metadata.
Preserve E63's failure and require any proposed changed policy to document its
exposure, scope and limitations before downstream use. This step needs no new
post or source request. ANITA's comparator route remains closed, and review
access/source-group novelty must still be resolved before broader evaluation.
