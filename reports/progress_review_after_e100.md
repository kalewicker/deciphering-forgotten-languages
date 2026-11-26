# Methodology review after E100

We can now trace one Yid post's opaque lines to a saved article and its proposed English prose to two continuous Burton excerpts. The open question is whether the opaque wording helps identify which English passage goes with which line. Our current evidence would survive shuffling the proposed pairings if the opaque roster and ordered English roster were kept separately. That observation identifies a missing test.

| Question | Evidence to date | Unit and limit |
|---|---|---|
| Is the Yid collection usable? | E92 accounted for 3,485 candidate pairs across 86 documents. E93 and E94 found all 301 selected first lines literally in the three saved posts, in order. | Three preselected format-development examples. Their agreement gives no estimate for the other 83 posts. |
| Does the English correspond to a documented work? | E99 found 0/22 literal matches and 22/22 ordered matches after whitespace collapse. E100 found only whitespace in all 20 internal gaps. | One named source claim in one post. The 22 renderings belong to two excerpts, with a backward page jump. E95 found eight catalog claims across the three posts, only one with external page ranges. |
| Is there linguistic structure or validated meaning? | E79 improved next-category prediction by 0.072877 bits per target across 13 exposed Kamri groups. | An adaptive development result on a different language label. Independent semantic benchmark capacity remains 0/4 qualifying works. |

The E91 review recommended combining format development with the complete census. E92 delivered that milestone. Fixed specimens, separate literal and whitespace results, and local preservation of failures paid off in E93–E100. E96–E100 also show a cost: five numbered steps addressed acquisition, pagination, extraction, wording and continuity for a single source claim. In future, identify the claim and its decision rule first. Treat acquisition and extractor development as logged stages of that study, allow fixture development on disclosed examples, and freeze the scoring implementation before measuring outcomes. Keep failed attempts visible and count the scientific result at the level of the claim.

## Recommended next decision

Close the Burton wording investigation. Use the 22 exposed pairs for one preregistered development test of **pairing specificity**. Can a rule learned from other rows use repeated opaque forms to rank the package-assigned English row above plausible alternatives from the same passage?

- Omit the heading. Hide ordinals, page positions and catalog metadata from the scorer. Select distractors within the same excerpt by a deterministic length rule. Retain ties, rows lacking alternatives and abstentions. Freeze the candidate sets and handling of shared names, numbers and punctuation before scoring.
- Keep a scored row and its candidate English rows out of the data used to learn token associations. Compare the frozen rule with a length-only baseline and a control that permutes the training pairings within excerpts. Use identical candidates for every comparison. Report pairwise wins, ties, losses and coverage over all 22 rows and separately for the 18-row and four-row excerpts.
- Before looking at scores, specify the minimum usable coverage and advantage over both controls that would justify a new-source test. If the four-row excerpt or sparse vocabulary leaves too little training support, record that feasibility limit. If performance tracks the controls, close this rule. A pass justifies a separately reserved source-group replication. All outcomes remain development evidence because these pairings are author proposals and the work is exposed.

The controlled pairing test could distinguish text-specific associations from two independently correct rosters. A semantic accuracy claim still needs independent passage adjudication and reserved source groups. Track progress by corroborated posts, distinct source works, pairing tests with controls and independently reviewed works. Keep test-suite totals as engineering verification. This review launches no experiment.

Evidence: [Yid census](000092_interpretation.md), [first native save](000093_interpretation.md), [two-post panel](000094_interpretation.md), [source claims](000095_interpretation.md), [wording](000099_interpretation.md), [continuity](000100_interpretation.md), [Kamri development result](000079_interpretation.md), [earlier strategy review](progress_review_after_e91.md).
