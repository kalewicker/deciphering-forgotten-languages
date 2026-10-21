# E72: fresh Codex review completed; source relationship remains uncertain

One fresh Codex session reviewed the unchanged **Risk mathematics** packet under
the user's requested automated route. Its first return reports an **uncertain
source relationship**, one tentative structural pair and unmatched English
material. The unchanged E25 validator accepts its structure, and a separate
check confirms all seven span records (six distinct spans) against the exact supplied text. This is
useful source-disclosed development evidence, with no admitted opaque meanings,
source identity, independent scientific review or untouched benchmark unit.

The [fresh-session guide](000072_fresh_session_guide.md) explains the tested
memory controls. The [registration](../experiments/automated_packet_review_v72.md)
fixed the packet, three-page window, neutral prompt and one-review budget before
launch. There was no resume/fork, second packet, second model attempt, prompt
tuning or reviewer correction loop. No human reviewer was contacted.

## Findings and adjudication

| Returned observation | Conservative reading |
|---|---|
| Repeated opening forms in adjacent opaque units resemble repeated subjects in source paragraphs. | A structural lead only. The sole evidence pair is explicitly uncertain; it establishes neither a statement correspondence nor a translation. |
| English weapons-policy and legal claims in the FL post lack counterparts in the supplied window. | Evidence against a simple complete-coverage account within pages 1–3. It does not exclude an opaque relationship, other source material or material outside the window. |
| Trailing references and several English topics remain unmatched; source metadata and technical distinctions cannot be mapped confidently into opaque prose. | Preserve unmatched regions and uncertainty. Topic overlap supplies no immediate-source identification. |
| Footnotes/page-edge continuations complicate text order. | Retain original extraction bytes and use the page images for layout. The reviewer reported these issues; this turn did not independently adjudicate every visual detail. |

The reviewer found no distinctive literal quotation or matching citation that
establishes this candidate pairing within the fixed window. That is a scoped
automated assessment, not an exhaustive proof of absence or a calibrated
source-specificity test.

Two fields require care. The return says `coverage: partial`, but its explanation
restricts that to topical overlap and a possible structural lead. **Accepted
source coverage remains unestablished**; the return is preserved unchanged.
Its counterexample pairs an English legal/operational passage with the source's
abstract. Those two spans differ, but that alone cannot establish absence
throughout the window or disprove source derivation. Treat the broader absence
claim as the reviewer's reading judgment, not a verified semantic contradiction.

The automated reviewer declares no visible prior-prediction exposure and sets
the template's exposure-independence boolean true. That declaration is consistent
with the supplied prompt and visible tool trace. It does not certify training
independence, lack of pretrained familiarity, independent semantic truth or
independence from the model family used for earlier work.

## Fresh-session and isolation evidence

The coordinator in this chat has prior project exposure. The reviewer received
only the neutral task prompt, fixed packet and three publisher image attachments.
The standalone `codex exec` used per-run memory-use and memory-generation
settings set to false, the memories feature disabled, an ephemeral session,
ignored user config and zero project-instruction bytes. Hooks, plugins/apps,
subagents, browser tools and web search were disabled. Model tool networking was
disabled; authentication and the Codex inference service remained operational.
Global preferences, memories and historical packets were not edited.

The first deterministic probe revealed that a broad home-directory deny still
allowed `MEMORY.md` to be read. The model was **not launched**. The original
probe, code and registration remain preserved. A separately registered
[revision](../experiments/automated_packet_review_v72_revision1.md) added explicit
memory/session directory denies. Its probe could read the packet, could not
write it, and received permission failures on five existing files: memory
registry, memory summary, saved session, project report and unrelated temporary
canary. No missing-file error was substituted for denied access.

The resulting one-turn session completed three successful Python commands:
protocol/template inspection; packet hash and complete text inspection; exact
span calculation. The visible commands read only packet files and used standard
library calculations. They contain no external file lookup or network request.
All three page images were attached; full visual inspection is the reviewer's
self-report. The returned JSON agrees with the final event in the retained trace.

These controls and probes establish a substantially cleaner review context.
They are not a proof against every side channel, unseen backend behavior or
correlated model error. CLI version was recorded as `0.163.0-alpha.10.2`; the
invocation used the CLI default model, whose exact identifier was not separately
captured. Do not invent a model/version identity from its self-description.

## Outcome and verification

The [public receipt](000072_verification.json) records nine preserved packet
members, seven manifest member hash/length checks, two exact text lengths and
seven exact span records (six distinct spans). The prior failed probe and corrected successful probe
are retained, along with prompt/config hashes, timing, session ID, first raw
return, CLI events, stderr and the unchanged validator's receipt. These generated
materials remain local in `data/v72/` and `runs/000072_automated_packet_review/`.
No source document, full review return or raw tool trace is published.

Automated review access is now demonstrated for this isolated packet. Independent
scientific review remains unresolved; the natural benchmark still has **0/4**
qualifying works under its unchanged two-development/two-test rule. Existing
exposed material is not promoted into an untouched fold. E62/E70 stay closed and
synthetic feature expansion stays stopped. This completes the registered review
pilot; no second review or new acquisition is launched here.

The full workspace suite passed **541 tests**. An isolated public export passed
**502 tests**, with the same 39 archive-dependent exclusions. The new verifier
reconstructs input preservation, exact spans, probe states, first-return binding
and attempt accounting; it does not independently verify opaque semantics.

Verify the retained evidence offline with:

```sh
.venv/bin/python scripts/verify_packet_review_v72.py
```

This verifier requires the local archive. The historical preparation/launch
scripts are single-use records; do not rerun them into existing evidence paths.
