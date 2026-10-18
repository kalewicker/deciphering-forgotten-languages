# Experiment 12: natural source acquisition and eligibility

Completed and independently verified on 2026-10-01. **Neither of the two selected source works produced a reference-eligible pair under the registered acquisition and provenance rules.** Both indexed FL openings were acquired, but the English evidence was inadequate. No retrieval, lexical prediction, admission or translation model was executed. Accuracy and rejection metrics are unavailable, not zero. No model or meaning is promoted.

This is the completed acquisition stage of the natural-validation pilot. Natural transfer and lexical validation remain unfinished because they require eligible English/reference packets. The result says nothing about whether those missing evaluations would succeed.

## Fixed selection and scope

The [registration](../experiments/kamri_natural_v12.md) selected two unused source works from the [public Kamri inventory](https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/): *Liber Azazel* (entry 9) and Monte Cook's 2002 *Book of Vile Darkness* (entry 15, chapter 1). These source identities were discovery leads, not accepted reference answers. Selection preceded fetching their FL passages and direct English acquisition; it did not depend on roster occurrences, success or model scores. There were no replacements.

The D&D source component includes both *Book of Vile Darkness* and *Book of Exalted Deeds* because inventory entry 18 reportedly combines them. Only one representative work/query was selected from that component. Future acquisitions of linked articles or the other book must not be counted as independent of it. Both selected components are absent from the persisted natural development corpus and frozen lexical support. The [novelty audit](../benchmarks/inputs/natural_v12_novelty.json) checks all 25 historical normalized documents, their declared source groups, lexical evidence groups and long exact FL sentences. This is a declared-corpus audit, not archive-wide duplicate detection or proof about unidentified sources.

The fixed acquisition allowance was two source-discovery queries per work, at most three distinct direct source routes per work, and one URL-restricted FL index search plus one indexed page open when needed. FL selection used opening complete sentences up to 180 whitespace words, excluding numbered labels, titles, navigation and bibliography. It stopped when the next complete sentence exceeded the cap and did not backfill. Semicolon/colon parser atoms were joined until a full sentence ended, so clauses did not silently become complete sentences. No drop-cap repair was needed.

The English scope was the opening of Azazel book I or Vile Darkness chapter 1, up to 2,000 words at complete sentence boundaries. An unverified upload, bibliographic record or isolated preview could not substitute for an inspectable source packet with adequate provenance. The immutable registration contained the selection and rules before acquisition. The [machine-readable configuration](../experiments/kamri_natural_v12.json) was materialized afterward and explicitly records that chronology; it is not represented as a pre-acquisition configuration seal.

## Acquisition outcome

| Selected work | FL opening | English evidence | Eligible references | Model evaluated |
|---|---|---|---|---|
| Liber Azazel | Indexed opening, 146 words / 11 parser atoms | Unverified cached third-party preview; current raw page lacks that opening; PDF 404; source-site DNS failure | Unavailable | No |
| Book of Vile Darkness | Indexed opening, 176 words / 11 parser atoms | Catalogue record; linked archive item is dark and exposes no files | Unavailable | No |

**Liber Azazel.** The nominated [Scribd index](https://www.scribd.com/doc/47586429/Liber-Azazel) displays source prose uploaded by “Vex Nation,” with an AI-enhanced title and no verified author attribution. The first three numbered units were saved as a quarantined indexed observation; they are not a complete nominated English packet or accepted reference gold. A current direct HTTP request returned 200, but its raw body did not contain the indexed opening. That difference is preserved rather than treating cached index text as current HTTP content.

The [MagicGate PDF route](https://www.magicgatebg.com/Books/Aleister%20Crowley/Liber%20Azazel.pdf) appeared in discovery but returned HTTP 404 with an HTML body during direct acquisition. Its folder name does not establish authorship. No PDF was acquired, rendered or accepted as scan-checked evidence. A candidate source-site homepage at `theisticsatanism.com` failed DNS resolution. The same request was repeated outside the sandbox to distinguish environment restrictions from an actual DNS failure, with the same result. Both receipts are saved. This was one disclosed environment diagnostic on the same route, not an additional search route, replacement source or model retry.

**Book of Vile Darkness.** The [Open Library record](https://openlibrary.org/books/OL8144288M/Book_of_Vile_Darkness) resolves the nominated 2002 Monte Cook edition and ISBN 9780786926503, but provides no chapter prose. Its linked [Internet Archive item](https://archive.org/details/bookviledarkness00cook) returned metadata with `is_dark: true` and no file listing in the [saved raw response](../data/v12/acquisition/vile_darkness_2/body.bin). No restricted file route was attempted. Discovery also returned third-party copies and material from a different 2011 edition; these were not substituted under the registered source-admissibility rule.

This is a bounded failure to acquire eligible packets through the selected routes. It is not a claim that no valid copy exists elsewhere, or that the public correspondence leads are false.

## Denominators and missing evidence

| Quantity | Result |
|---|---:|
| Selected works / query packets / source components | 2 / 2 / 2 |
| Indexed FL packets acquired | 2 |
| Raw/current FL pages acquired | 0 |
| Distinct direct English/source routes | 5 |
| Raw requests including the disclosed DNS diagnostic | 6 |
| Quarantined indexed English previews | 1 |
| Admissible full English packets | 0 |
| Reference-eligible pairs | 0 |
| Actually model-evaluated pairs | 0 |
| Accuracy, lexical agreement and false-admission metrics | Unavailable |

The [frozen acquisition ledger](../benchmarks/inputs/natural_v12_acquisition.json) retains both selected packets, all 322 selected FL token identities and spans, original roster-surface occurrences, unmet evidence gates, null references and null lexical accuracy. There are zero roster occurrences in the fixed Azazel opening and one in the Vile opening; these are surface counts, not lexical predictions or validated meanings. The selections were not extended to find more favorable occurrences. Even a later successful source acquisition would provide a very small roster check at this scope.

The FL inputs are explicitly dated indexed excerpts, which can differ from the live pages. They are not raw HTML snapshots or complete articles. Earlier Altruist unavailability and its experiment-5 selected denominator remain unchanged; that source was not retried here.

Known-evidence-matched negatives, source-absent model controls, reviewed alignment metrics and frozen real admission thresholds were conditional on obtaining an eligible pair. Since none cleared the acquisition/reference gate, none of those model evaluations occurred. They have null/unavailable results; zero false admissions must not be inferred from zero evaluations. The unchanged v11 model remains available for a future properly frozen continuation.

## Verification and reproducibility

All **92 tests** passed. Six new tests verify all combinations of the required evidence gates, strict Boolean inputs, complete-sentence cap behavior without backfill, numbered-label handling, and preservation of selected denominators and unavailable metrics. Existing tests remain unchanged.

The [independent verification receipt](000012_verification.json) checks registration/configuration/ledger/input/raw/code/output hashes, finite discovery counts and the disclosed sandbox diagnostic, an independent full-sentence selection implementation, every FL token span, HTTP/status evidence, dark archive metadata, quarantine, missing references and null metrics, declared source novelty, the absence of prediction/threshold/score artifacts, and all eleven historical run archives. No execution-frozen code was edited after the offline result was recorded.

The [completed manifest](../runs/000012_kamri_natural_acquisition/manifest.json) is the durable status authority for the **acquisition/eligibility stage**, with `model_executed: false`. The [immutable report](../runs/000012_kamri_natural_acquisition/report.json), [frozen benchmark](../benchmarks/kamri_natural_v12.json), [discovery log](../data/v12/discovery/search_log.json) and raw acquisition receipts preserve the outcome. Initial discovery responses are represented by clearly labeled analyst summaries; later index/metadata tool responses were saved in full. No claim of complete search provenance is made for the unsaved initial responses.

Verification is offline:

```sh
.venv/bin/python scripts/verify_natural_v12.py
```

Acquisition, preparation and run scripts refuse to overwrite their existing directories or freezes. Repeating acquisition requires a separately registered continuation with fresh artifact IDs; repeatedly invoking the scripts is not a way to create new evidence.

## Next requirement

Obtain an inspectable English copy with defensible author/publisher/library provenance for a selected source, or register a separate bounded discovery panel for different unused components. Keep the two v12 failures and their denominator intact. A continuation must establish edition and exact source scope, freeze reviewed passage/occurrence references before scoring, and retain missing or unsupported occurrences. New source text must not enter lexicon induction before its frozen evaluation.

Additional independent human review is still needed for semantic labels. Positional compatibility, a retrieved source, or a public author's proposed translation cannot by itself promote the world/lord/made meanings. The acquisition result gives no reason to tune a scoring model; its immediate constraint is missing admissible source evidence.
