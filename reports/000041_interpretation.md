# Experiment 41: an external English quotation lead

The one registered full-quotation search returned a complete quote00 match in
the visible result for Physics World's
[Mysterious radio signals could be from new type of neutrino](https://physicsworld.com/a/mysterious-radio-signals-could-be-from-new-type-of-neutrino/).
That result displays **17 July 2018** and attributes the quoted statement to
Gorham. It is the first eligible external hit and the sole nominated lead.
This is an indexed discovery result; no native page or historical snapshot was
captured, and original quotation provenance is not authenticated.

## Fixed scope and complete result accounting

The [registration](../experiments/quotation_discovery_v41.md) and
[request arguments](../experiments/quotation_discovery_v41.json) were sealed
before acquisition. The query was complete quote00, all 147 Unicode characters,
wrapped in double quotes. It is unchanged from the v38/v39 ledger. There was
**one search call containing one query**, no retries and no subsequent page
opens, captures, downloads, other searches or rescoring. Hidden search-service
operations and enforcement of exact-phrase syntax are not observable.

The complete tool-returned response is saved locally in
[search_response.json](../data/v41/search_response.json); it is not a raw HTTP
capture. The [discovery ledger](../data/v41/discovery_ledger.json) inventories
all seven identifiable results, including unrelated material. Whole-quote
matching uses the unchanged NFC/casefold/whitespace rule from v38.

| Service rank, zero-based | Returned location | Complete quote visible? | Decision |
|---|---|---|---|
| 0 | Physics World article | Yes | First eligible external lead; nominated |
| 1 | Existing dated FL target | Yes | Existing target; excluded |
| 2 | Seniorennet archive, ID 2164169 | Yes | Recognizable repost credit to Mysterious Universe; excluded |
| 3 | Seniorennet archive, ID 2164104 | Yes | Repeated credited repost; excluded |
| 4 | Scribd document | No | No complete quote in returned text |
| 5 | FL October 2018 index | No | Other FL page; excluded |
| 6 | Seniorennet archive, ID 2164179 | No | No complete quote in returned text |

There are **4/7 returned results with the complete quote visible**, including
the target and reposts, and **1 eligible external lead**. Each of the four
matching results contains two occurrences in its returned text, generally a
summary and an expanded excerpt. These are repeated display occurrences, not
independent corroboration. The ledger retains exact response-local Unicode
spans, source-token witnesses, result boundaries, hashes, repost-credit evidence
and the displayed date witness. No partial phrase was submitted as a new query.

## What this establishes and leaves open

An external location for the complete English quotation is now a concrete lead.
The displayed date would precede the FL post's nominal date, but neither date
establishes a captured historical sequence or a direction of copying. Reposts
do not establish independent source works. No raw article, complete-page
coverage, original authorship, immediate opaque-FL source identity, word meaning,
independent review or untouched natural test unit is admitted. Semantic metrics
and scientific acceptance remain null; natural-benchmark capacity stays unmet.
Experiments 38 and 39 retain their original query sets and outcomes.

## Verification, publication and next step

The [separate verifier](../scripts/verify_quotation_discovery_v41.py) checks the
freeze, full request, timestamps, all result boundaries, whole-quote occurrence
counts and exact witnesses, exclusions and lead selection. All **40 prior runs
and deliverable seals are intact**. The verifier was written after acquisition;
it independently reconstructs counts and boundaries, but is same-agent
engineering verification rather than independent scientific review. See the
[verification receipt](000041_verification.json) and
[immutable report](../runs/000041_quotation_discovery/report.json).

The full local suite passes **337/337** tests. An isolated public export passes
**298/298**; the same 39 archive-dependent tests remain explicitly excluded.
No old sealed code, test or artifact was modified. The standing end-of-turn
commit/push rule is recorded in [AGENTS.md](../AGENTS.md) and
[PUBLICATION.md](../PUBLICATION.md). New evidence stays on the local archive
branch; public protocols, reports and tooling go to `main`.

Next bounded step: register **one native HTML acquisition of the selected
Physics World URL**, preserving any failure, then check identity, complete
quote00 presence and attribution in the saved representation. Further queries,
historical authentication and opaque-passage alignment need their own scopes.
No follow-up acquisition was made in experiment 41.
