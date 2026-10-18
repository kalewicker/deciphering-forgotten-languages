# Experiment 34: paired-world positional identifiability

The paired-world demonstration passes: thirteen equal-symbol sites have
identical public input but different token ancestry. The frozen predictor cannot
distinguish their two histories from those inputs. The separate nonvacuous
forced-match safety hypothesis fails: in 329 unequal-symbol swap worlds it
returns **zero of the 658 affected positions**.

These findings distinguish an information limit in the offered history pair
from a limitation of the frozen monotonic alignment model. They do not change
the failed v33 strict-origin result or establish natural-language meanings.

## Registered universe

All six exposed v32 seen-group passages under alias key 11 are used. Each has
64 tokens and 63 adjacent sites. Using one key avoids counting identical source
passages again under the other three trained keys.

- All 378 site rows remain in the registry.
- 36 sites touch a blocked, consequently unmapped endpoint and have no worlds.
  The two exclusion-reason counts both describe those same 36 sites, not 72.
- The 342 eligible sites comprise thirteen equal-symbol sites and 329
  unequal-symbol sites. Each contributes identity and single-swap histories:
  684 assessed worlds.
- There are 335 distinct public observations: six identity observations and
  329 changed-query observations. The other 349 world occurrences reuse content.
  Every world remains in the assessment denominator.

Predictor inputs contain only source/query text, token offsets and blocked flags.
Observation identifiers hash that content; they encode no world, passage, swap
index, relation or origin. The unchanged v32 decoder/indel aligner and v33
all-optimal-match audit run once per distinct observation. All 335 alignments
meet the unchanged v32 coverage threshold. No retrieval panel is reranked.

The site/world registry and origins are separate from predictor inputs.
Code freezes before fixture generation, fixtures before prediction, and the
prediction file before origin assessment. The v32 mapping remains unchanged.
This is an exposed synthetic diagnostic, not an independent holdout.

## Exact ancestry at the affected positions

Each world has exactly two affected query positions. Unchanged context is scored
separately and cannot dilute the primary intervention result.

| History stratum | Worlds | Affected positions | Representative: exact / returned | Forced: exact / returned |
|---|---:|---:|---:|---:|
| Equal symbols, identity | 13 | 26 | 26 / 26 | 26 / 26 |
| Equal symbols, swapped | 13 | 26 | 0 / 26 | 0 / 26 |
| Unequal symbols, identity | 329 | 658 | 658 / 658 | 658 / 658 |
| Unequal symbols, swapped | 329 | 658 | 329 / 330 | 0 / 0 |

The last forced precision is undefined because nothing is returned. Its coverage
is 0/658. The registered hypothesis required both zero wrong affected returns
and at least one return across the unequal-symbol swap worlds. The zero-error
condition holds vacuously; the nonvacuity condition fails. This is not an
accepted safety guarantee or successful recovery of swapped positions.

The representative policy returns 330/658 unequal-swap affected positions with
329 exact origins and one wrong origin. In passage 0, swap site 13, query index
14 is returned at source index 15 instead of origin 13; both source occurrences
are `symbol8`. That return is optional across optimal paths.

## Identical input cannot identify these two histories

For every one of the thirteen equal-symbol sites, exchanging the two source
occurrences changes their origin labels without changing query text, source
text, offsets or model input. The deterministic content-only predictor therefore
returns the same alignment in both worlds. It keeps visible order: both affected
positions are origin-exact in the identity world and wrong in the swapped world.

Every collision has a constructive certificate enumerating every candidate
source index at each affected query position. A fixed point answer is exact in
at most one of the two worlds. If both positions are answered in both worlds,
the maximum is two exact calls out of four. The frozen policies reach that
balanced bound: 26/52 exact affected calls across the thirteen pairs.

Abstention can reduce coverage, but cannot reveal the hidden history. Returning
the two-origin union covers both histories as a set-valued answer; it does not
identify either origin as a unique point. The stored union sets are oracle
certificates, not predictions from a new inference method.

This bound concerns the two offered histories without a world label. It is
not a probability estimate, a claim about natural-language history frequencies,
or an impossibility claim conditional on a known recipe that specifies which
history occurred. The 329 unequal-symbol controls all change public input;
that permits discrimination between their two histories but does not guarantee
unique ancestry among all conceivable transformations.

## Visible symbol compatibility is a different target

The registered compatibility check accepts a return when its source symbol equals
the symbol at the generator origin, allowing exchange of identical occurrences.
All emitted matches pass this check, including the 26 wrong equal-swap origins.
This follows from correct frozen aliases and the permitted-match rule in these
fixtures. It is a consistency check, not independent alignment accuracy,
semantic evaluation or new word meaning.

The distinction also prevents a misleading full-context conclusion. In the
unequal-symbol swap worlds, representative full-sequence precision is
19,726/19,740 (99.929%). Forced full-sequence precision is 19,345/19,345, with
91.874% coverage over all 21,056 query tokens. Those apparently strong totals
coexist with forced abstention at every manipulated position.

Across all 684 worlds, the representative traces contain 41,395 matches and
forty origin disagreements: 26 at equal-swap affected positions, one at an
unequal-swap affected position, and thirteen outside the affected positions in
unequal-swap worlds. Forced filtering removes all fourteen unequal-world
disagreements while discarding 381 correct returns; the 26 equal-swap
disagreements remain. Identity worlds and shared contexts are reused many
times. None of these counts is an independent-trial estimate.

## Verification and artifacts

All 295 tests pass. New tests cover invisible and visible swaps, exhaustive
deterministic point answers with abstention on a tiny fixture, set-valued bounds,
barrier/unmapped exclusions, complete denominators after content reuse, wrong
origins with compatible symbols, metadata exclusion and observation-order
invariance.

The independent verifier reconstructs every site, public view, offset, content
hash and origin vector without the new generator. Independent v32 maximum-LCS
and v33 mandatory-edge implementations replay all 335 predictions; all 684
world scores, collision certificates, aggregate counts and hypothesis outcomes
agree. All 33 earlier run inventories and deliverable seals verify unchanged.
Independent implementation is not an external independent reviewer.

Primary evidence:

- [Registration](../experiments/positional_worlds_v34.md) and
  [code/input preflight](../data/v34/preflight.json).
- [Public observations](../data/v34/public_observations.json),
  [complete site/origin registry](../data/v34/oracle.json) and
  [fixture receipt](../data/v34/preparation_receipt.json).
- [Frozen predictions](../runs/000034_positional_worlds/predictions.json),
  [prediction receipt](../runs/000034_positional_worlds/prediction_receipt.json),
  [world scores and certificates](../runs/000034_positional_worlds/assessment.json)
  and [immutable report](../runs/000034_positional_worlds/report.json).
- [Independent verification](000034_verification.json) and
  [post-run exact token/offset witnesses](000034_witnesses.json), including all
  forty representative origin disagreements and all thirteen collision certificates.

```sh
uv run python scripts/verify_positional_worlds_v34.py
```

Natural scientific acceptance and semantic metrics remain null. No source
identity, meaning, independent review or untouched test admission occurs.
No natural target is rescored, external/neural model run or new source acquired.

## Next evidence boundary

Stop v34 with the collision demonstration established and the nonvacuous forced
safety hypothesis failed. Register a bounded adjacent-transposition alignment
test using the frozen mapping and v34 observations. Assess the same affected
positions and add identity, unknown-token, barrier and rejection controls before
scoring. Preserve equal-symbol collision worlds and their strict-origin errors;
any set-valued or abstaining ancestry output must remain distinct from point
recovery. A richer operation should be evaluated for recoverable local-order
changes without granting ancestry certainty from identical observations.
