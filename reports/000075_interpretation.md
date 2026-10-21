# E75: reviewer rejects both deliberately false literal clues

The one fresh Codex session passes the registered literal-control test:
**3/3 genuine claims supported, 2/2 false claims rejected, zero false supports**,
with no uncertain/missing cases. All five IDs and ten quote records are valid.
This demonstrates discrimination on these supplied literal controls, not natural
source-review reliability, independent scientific review or opaque FL meanings.

The [registration](../experiments/reviewer_controls_v75.md) fixed this new component
question before execution. E74's five genuine clues alone could not test rejection
of a false supplied claim. E75 therefore used a private known-truth key and
controlled claim changes against unchanged text. It did not repeat a natural
source judgment, modify either document, change an old score or reopen the
stopped alignment/pattern programme.

## All five fixed cases

Every claim used the same rule: both exact supplied spans must contain every
listed whole anchor, in the listed order without overlap, after NFC/casefold
and whitespace collapse. No punctuation, spelling or accent repair was allowed.
Anonymous case order was fixed by SHA-256, without a seed search or replacement.

| Case | Registered construction | Key | First judgment |
|---|---|---|---|
| C01 | Same three names asserted in reverse order in the unchanged W2 spans | Rejected | Rejected |
| C02 | FL `Daemonium Saturni` span paired with the source's different `Intelligentia Saturni` span | Rejected | Rejected |
| C03 | Three personal names in their actual order | Supported | Supported |
| C04 | The `zazel` / `Zazel` name under the stated casefold rule | Supported | Supported |
| C05 | The exact embedded expression from W1 | Supported | Supported |

For C01 the reviewer correctly noted that all names are individually present
but their order differs from the claim. For C02 it correctly found the full
claimed label absent from the supplied source span, despite the shared Saturn
word. The three genuine judgments also agree with the exact rule. The return
does not rely merely on the existence of a supplied clue or on loose topic
similarity for these cases.

These are **five dependent controls in one exposed work**, not five independent
natural passages. C01/C03 reuse the same text with a changed order assertion;
the other controls draw on the existing Western clues. The negative cases were
deliberately constructed and comparatively clear under this precise rubric.
Zero false supports out of two is not an estimate of a population error rate,
nor evidence that subtle semantic/source errors would be detected. E74/E75
also differ in task/rubric, so this is not a controlled causal comparison between
the two review procedures.

## Answer-key and execution boundary

The reviewer received only two unchanged text exports, anonymous claims, a blank
return template and a material manifest. It did not receive the original W IDs,
construction tags, positive/negative counts, answer key, previous review outputs,
project code or memory. The full PDF and images were not supplied: this test is
about exact exported text, not visual layout or capture fidelity.

All inputs, code, claim order and the private oracle were hash-bound before the
one model attempt. The read-only isolated directory contained exactly those
five supplied files. The prelaunch probe received permission failures on memory,
summary, session, project history, another temporary file **and the private
oracle**. Supplied claims were readable and workspace writes denied. The fresh
standalone session used the established memory/config/project-instruction/tool-
network restrictions. Global preferences and memories were not changed.

The first raw return and full event trace were retained. A prediction receipt
bound their SHA-256 hashes before the assessor parsed the oracle for scoring;
integrity checks had already verified its frozen hash. The coordinator defined
and knew the constructions; only the reviewing session lacked the supplied
answer key. Do not describe the coordinator as blinded or these exposed source
texts as untouched evaluation material.

The saved trace contains three successful commands: directory/file listing,
manifest/template/claim reading, and Python integrity/literal matching checks.
The visible commands use supplied files and show no oracle, project-history or
network lookup. The final event's JSON agrees with the preserved raw return.
The CLI default model was used; the exact model identifier was not separately
captured. Runtime probes and trace inspection do not prove absence of every
side channel, pretrained familiarity or correlated model error.

## Independent accounting and checks

The verifier imports neither the primary predicate nor the assessor. It rebuilds
the anonymous cases from the old appendix and independently enumerates all
ordered anchor-occurrence combinations, rather than the primary greedy regex
chain. Both methods agree with the frozen key and every returned judgment. It
also verifies the supplied hashes, original quote slices, full denominator,
prediction-before-assessment receipt, isolation probe and one-attempt chronology.
The [public receipt](000075_verification.json) records the passing registered
component gate. Implementation independence is not independent scientific review.

Six new fixture tests cover case/whitespace/Unicode normalization, reverse-order
membership, a wrong full label with a shared suffix, word boundaries/nonoverlap,
an always-supporting false judgment, uncertainty and missing/malformed returns.
All **553 workspace tests** and **514 isolated-public tests** pass; the same
39 archive-dependent exclusions remain. E74's sealed evidence and all historical
tracked files were preserved.

## Decision and stopping point

This closes the single registered control batch with a narrow positive result:
the reviewer can verify these explicit literal propositions and reject both
planted errors. Keep the rejection controls in future separately justified
review protocols, without treating this result as a semantic or source-identity
admission. Do not run another batch or feed corrections/key information back to
this session to improve the result.

The missing natural evidence has not changed. Immediate source identity, opaque
meanings, independent-review admissions and untouched test units remain absent;
natural-benchmark capacity is still **0/4 qualifying works**. E62/E70 stay closed
and synthetic feature expansion stays stopped. The next substantive research
proposal still needs an independently testable constraint beyond repeated
recognition of the same anchors. This component pass is not authorization for
another natural rescore, packet review, larger source window or search.

Raw inputs, private key, first return, trace and prediction receipt remain local
in `data/v75/`; the accounting report and manifest are in
`runs/000075_reviewer_controls/`. They are checkpointed on the local-only evidence
branch. Public `main` contains only code, tests, registration and small reports.
Reconstruct retained evidence offline with:

```sh
.venv/bin/python scripts/verify_reviewer_controls_v75.py
```

This requires the excluded local archive. Preparation, execution and assessment
are single-use records; do not rerun them into existing output paths.
