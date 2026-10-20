# Experiment 61: ten attributed search cards, nine strict URLs, no article admissions

The offline audit attributes **10/10 listing cards** in the exact saved E60
response. **Nine** have URLs usable under the unchanged E55 strict article-URL
predicate. One card, at zero-based index seven, has a percent-encoded path and
remains strictly rejected; its title, snippet, both links and structural result
attribution are retained. No URL decoding or rule relaxation rescues it.

Every original **115 anchor occurrences** has exactly one accounted role:

| Role | Occurrences |
| --- | ---: |
| Attributed card title | 10 |
| Duplicate image link for that card | 10 |
| Supporting card links, such as category links | 20 |
| Outside listing cards | 75 |
| Total | 115 |

Ten cards are not twenty independent hits, and all 115 page anchors are not
search results. The parser preserves original DOM indices, decoded hrefs,
resolved URLs, text including empty image-anchor text, and duplicate occurrences.
The complete ledger exactly reproduces E60 before adding these classifications.
All page and card structural checks pass; no malformed or out-of-scope card is
silently removed. Adversarial fixtures retain those failures when present.

## What this enables and what remains unavailable

The fixed schema binds each card to the unique main-content result column,
one title link, matching image link and nonempty snippet. Page title, query
heading, body classes and base handling constrain the declared context. This
supports result attribution for this exposed static page; it is not evidence
that the parser generalizes to unseen layouts or that publisher search has
measured precision/recall. The registration explicitly discloses the markup
inspection used to design it.

**None of the ten cards supplies date markers in the registered card channels.**
All ten remain date-unavailable, with no dates inferred from image filenames,
ranking or snippet wording. Native article date/title/scope checks must still be
applied by any later intake. No article eligibility, topic nomination or numeric
feasibility assessment is made here.

Two of the nine strict URLs were already captured in the frozen exposure
registry. Its union with every strict article URL in the full saved response
grows from **50 to 57 URL entries**; the **seven captured article keys remain
unchanged**. All ten resolved listing URLs, including the strict rejection,
are also retained as exposed. Seven new registry entries are not seven new
independent sources or untouched works. The registry is explicitly incomplete
lifetime exposure and source-group evidence.

The local outputs are `data/v61/preflight.json`, `data/v61/attribution.json` and
`runs/000061_result_attribution/{report,manifest}.json`. Source HTML and detailed
third-party snippets remain local. There were **zero research network requests,
new captures, nominations, alignment/numeric scores or scientific admissions**.
E58's empty slots, E56/E57 results and all earlier failures remain fixed.

## Applying the progress-review recommendation

This audit adopts the reviewed planning constraints for the next separately
registered intake/challenge: **two fixed candidate slots**, unchanged native
eligibility and exposure rules to be frozen before nomination, and a comparator
window of at most **eleven numeric anchors** with numeric multiset overlap
capacity **at least six**. The original E58 three-type screen is not amended.
Capacity six is necessary to challenge the reference's fixed score of six; it
is not sufficient evidence of equivalent quantities, meaningful order or source
identity. A capable candidate must undergo the frozen comparison and controls.

The remaining discovery batch is final for this route/cohort. Preserve every
failed or empty slot. If it supplies no capable comparator, close this route as
feasibility-limited, without replacement searches or an expanded batch. If a
capable comparator is obtained, retain its comparison outcome, including ties
or failures, and close the batch. Natural decipherment remains unvalidated in
either case. Broader expansion depends on new independent review or fresh
source-group evidence; same-agent verification does not supply that evidence.

## Verification and next step

Seven new adversarial fixtures pass. **462 full-workspace tests** and **423
isolated-public snapshot tests** pass; the same 39 archive-dependent cases remain
explicitly excluded publicly. The separate verifier reproduces the page/card
predicates, all original indices, title/snippet/date/link records, role counts,
exposure union and unchanged capture status without importing production v61
functions. Its strict URL predicate is separately implemented. It shares
BeautifulSoup parsing and is not independent scientific review.

All **60 previous run manifests and historical deliverable seals** remain
intact. See [verification](000061_verification.json) and the new deliverable seal.
No new opaque meaning, quantity correspondence, immediate source identity,
independent review or untouched test unit is admitted. Natural-benchmark capacity
remains unmet.

Next: preregister the final fixed two-slot intake/challenge using this attributed
page, including nomination order, exposure exclusions, native requirements,
request/conditional-alias limits, capacity screening, comparison controls and
stopping outcomes. Complete capture validation and any permitted comparison as
phases of that bounded experiment. No such acquisition or scoring is part of E61.
