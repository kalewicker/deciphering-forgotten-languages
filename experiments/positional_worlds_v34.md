# Experiment 34: paired-world positional identifiability

Register before generating v34 fixtures or measuring outcomes. This is an
exposed synthetic diagnostic, not natural-language or independent holdout evidence.
Preserve v32/v33 and all earlier outputs, code and seals.

## Fixed universe and public interface

Use all six seen-group parent passages for training key 11 from frozen v32,
with their bijective queries. One key avoids repeating the same source under
four alias keys. Enumerate all 63 adjacent source sites per 64-token passage:
378 site rows, with blocked/unmapped endpoint sites explicitly excluded.
Eligibility requires both source/query endpoints unblocked and the frozen
mapping at every nonblocked query position consistent with its identity parent.
Never select sites using alignment or origin outcomes.

For every eligible site create two worlds: identity lineage and a single adjacent
swap. Build the swapped query by exchanging its two alias tokens; its origin
vector exchanges the same indices. Both worlds retain the same source. Equal
symbols must have equal aliases under this one key; unequal-symbol swaps are
controls that change query bytes. Do not otherwise perturb the sequences.

Predictor inputs contain only full source/query text views with offsets and
blocked flags. Content-address observations by canonical JSON of those views;
no key, passage, world, swap index, relation label or origin is passed to the
predictor. Keep the site/world registry and origins in a separate oracle.
Deduplicate observations by content, but retain every eligible site and both
worlds in assessment denominators. This is computational reuse, not attrition.

Freeze code before fixture generation, freeze fixtures before prediction, and
save predictions before loading the oracle for assessment. Run the unchanged
v32 decoder/indel aligner and v33 all-optimal-match audit per observation. Do
not learn a mapping, change gap costs/coverage/tie breaking, rank candidates or
rescore natural targets. Keep full traces, possible matches and both token ledgers.

## Separate targets and fixed tests

Primary ambiguity demonstration: there must be at least one equal-symbol site
and one unequal-symbol control. Every equal-symbol pair must have byte-identical
public input and different strict origins at exactly its two affected indices;
both worlds must yield identical predictions. Every unequal-symbol control must
have different public input. Verify a constructive bound per collision: for any
fixed candidate index at each affected query position, at most one of the two
worlds calls it origin-exact. Under balanced two-world scoring a deterministic
point policy using these inputs can get at most 2/4 affected calls exact if it
answers both positions in both worlds. Abstention reduces coverage; returning
both possible origins is a set-valued answer, not a point ancestry claim. This
is a bound under these two possible histories without a world label, not an
estimated probability or impossibility conditional on the full known generator.

Separately test the falsifiable safety hypothesis that the frozen forced-only
policy returns no wrong strict origin at affected positions in unequal-symbol
swap worlds, with at least one affected forced return across those worlds for
nonvacuity. Report failure or zero coverage without tuning. Different public
inputs permit discrimination of these two histories; they do not ensure unique
ancestry among all histories or successful recovery by a monotonic aligner.

For representative and forced-only policies report emitted matches, strict-origin
exact counts, symbol-compatible counts, precision fractions, and coverage over
all query tokens and separately over exactly two affected positions/world.
Symbol-compatible means the returned source form equals the source form at the
generator origin. This permits exchange of identical source occurrences. It is
implied by correct frozen aliases plus the allowed-match rule in these fixtures:
report it as a consistency check, never independent accuracy or word meaning.
Keep full-world and affected-position scores separate; unchanged context must
not hide failure at the manipulated positions. Report equal/unequal relation
and identity/swap strata, all excluded sites and all content-reuse counts.

## Verification and limits

An independent verifier reconstructs all six parent/query selections, offsets,
eligible/excluded sites, both worlds, content hashes and origin vectors without
calling the new generator. Replay the frozen predictor via independent v32
maximum-LCS/decode and v33 mandatory-edge implementations. Recompute every
score/certificate, check original model immutability and all 33 earlier run
inventories and seals. Unit tests must include invisible equal swaps, visible
unequal swaps, the exact balanced bound, set-valued versus point answers,
barrier exclusions, repeated observations and wrong-origin compatibility.

No external/neural model or independent reviewer is used. Natural scientific
acceptance and semantic metrics remain null; source identities, meanings,
independent reviews and untouched admissions remain zero. No new source data.
