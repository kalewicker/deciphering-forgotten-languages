# Experiment 16: bounded correspondence review

Eight fixed units, the first four from each of two previously exposed passages, are retained. This is a v15-informed development/reference review, not held-out evaluation.

Both current publisher HTML sources downloaded with HTTP 200. Both current FL requests failed with curl 35 TLS protocol-version alerts. The registered exact historical indexed FL excerpts preserve all eight selected statements; they remain historical evidence, not current raw captures. Four registered routes, four raw requests, no retry, substitute or bypass.

All eight proposed English units match unique, complete original source statements. Both four-statement sequences are ordered and nonoverlapping in source and historical FL views. Two passages pass the indexed-evidence development correspondence gate. Zero pass current raw-FL provenance, independent semantic training or untouched-test gates.

| Unit | FL whitespace | Reading English whitespace | Original English whitespace | FL project tokens | Original English project tokens | Source match |
|---|---:|---:|---:|---:|---:|---|
| 03:001 | 25 | 24 | 25 | 25 | 25 | ordered_words |
| 03:002 | 34 | 32 | 34 | 34 | 34 | ordered_words |
| 03:003 | 26 | 24 | 24 | 26 | 26 | exact |
| 03:004 | 20 | 20 | 21 | 20 | 20 | ordered_words |
| 13:001 | 37 | 37 | 37 | 37 | 37 | exact |
| 13:002 | 30 | 30 | 30 | 30 | 30 | exact |
| 13:003 | 14 | 14 | 14 | 14 | 14 | exact |
| 13:004 | 26 | 26 | 26 | 26 | 26 | exact |

Whitespace equality holds for 5/8 reading-edition pairs and 6/8 original-source pairs. The project's Unicode tokenizer splits hyphenated compounds and ignores standalone punctuation: all 8/8 pairs have equal counts. This resolves the selected Nichiren count discrepancies under that tokenizer; it does not reproduce or validate the aggregate public 713/978 claim.

212 word-position pairings are serialized explicitly as unvalidated hypotheses, with offsets in independent FL/source documents. Equal counts and source identity do not establish those meanings or rule out local reordering. The fixed opposite-source diagnostics yield 0/8 literal/normalized matches; this is not a measured classifier false-admission rate.

The errata propose S024 -> S015 and S036 -> S027, plus the same S015 correction in the title note. Original article bytes and translations are unchanged. Per-unit confidence remains unavailable.

Paragraph-aware source segmentation prevents an unpunctuated section heading from becoming part of the following statement. The full extracted body and paragraph text are both retained. Whole-body differences versus historical extractions are separately recorded and are not interpreted as edition changes without evidence.

No model executed, shared lexicons were not used, and no semantic labels or new test fold were admitted. Next, independent review must test the positional hypotheses against actual word-order/meaning evidence; raw FL provenance still needs a legitimate source or supplied capture.

Evidence and interpretation

The selected source originals are [Nichiren Library, Opening the Eyes of Wooden and Painted Images](https://www.nichirenlibrary.org/en/wnd-1/Content/11) and [Theosophical Society, The Dark Side of Light](https://www.theosophical.org/publications/quest-magazine/the-dark-side-of-light). The two current HTML bodies, acquisition receipts, complete paragraph text and source sentence spans are preserved under `data/v16`. The FL side is explicitly the exact historical indexed snapshot. No author-provided translation is counted as an independent source original.

The tokenizer finding applies only to these eight selected units. Hyphenated compounds explain the reading-edition Nichiren word-count discrepancies, while extra whitespace-separated punctuation in the source HTML can alter whitespace counts again. All eight independently recovered source statements and corresponding FL units have equal project token counts. This makes one-to-one positions possible; it does not establish that the positions express the same meanings or that clauses were not reordered.

A token-sequence comparison finds no changed words between the historical Nichiren body and the current body. For Dark Side of Light, the only added ordered-word sequences are the author byline and two section headings: three words, four words, and four words respectively. The selected source statements are unchanged. This explains the recorded extraction drift without asserting that the publisher revised the article. The independently preserved paragraph boundaries also prevent a heading from contaminating the following sentence's token count.

The reviewed eligibility is deliberately narrow. Two four-unit passages are acceptable for reconstruction/development correspondence under historical indexed evidence. Zero current-raw-FL passages, independently reviewed lexical labels or untouched test units are admitted. The nomination was informed by experiment 15 and both components were already exposed. No statistical claim or population success rate is attached to this development selection.

The proposed corrections are local metadata errata only: [readable errata](000016_proposed_errata.md) and [machine-readable errata](../data/v16/proposed_annotation_errata.json). They do not map the aggregate confidence totals to individual sentences and do not change proposed translation wording. The original ZIP and article hashes remain unchanged.

118 tests passed. The independent verifier re-extracts source paragraphs, segments complete statements within each paragraph, checks every original span and fixed wrong-source occurrence, verifies all 212 positional-hypothesis spans/forms, recomputes count and gate outcomes, and checks all fifteen historical manifests. Automated verification does not supply a second semantic annotator. The two TLS protocol alerts are retained as failed acquisition receipts; no alternate host, retry or challenge bypass was used.

The next falsifiable step is a preregistered cross-unit consistency diagnostic on these frozen positional hypotheses: retain all selected units, measure how repeated FL forms map across independent statements/components, and preserve conflicts. Keep it in development and keep shared lexicons out. Genuine word-meaning acceptance needs independent evidence beyond equal counts; raw FL provenance remains unresolved.

Artifacts: [registration](../experiments/kamri_correspondence_pilot_v16.md), [immutable manifest](../runs/000016_kamri_correspondence_review/manifest.json), [all eight units and positional hypotheses](../runs/000016_kamri_correspondence_review/unit_ledger.json), [passage gates](../runs/000016_kamri_correspondence_review/passage_gates.json), [independent verification](000016_verification.json), and [source-drift explanation](000016_extraction_drift_review.json).

Reproduce verification with `.venv/bin/python scripts/verify_correspondence_review_v16.py`; run the test suite with `.venv/bin/python -m unittest discover -s tests -q`. Preparation and run scripts refuse to overwrite their existing directories.
