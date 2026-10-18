# Experiment 2 completed: editions matter; sentence alignment remains partial

The frozen lexical/structural method ranked both newly selected source works first in the seven-work candidate collection and admitted both under development-derived thresholds. It recovered **6 of 15 reviewed correspondence edges** and proposed no incorrect edges in these two cases. The unchanged structural baseline ranked **1 of 2** works first, admitted neither, and recovered **1 of 15** edges through its top-ranked sources.

This is useful engineering progress on a tiny known-source sample. It is not independently validated semantic translation accuracy or blind discovery of sources.

## Registered comparison and result

The [registration](../experiments/kamri_alignment_v2.md), [frozen benchmark](../benchmarks/kamri_alignment_v2.json), and [complete immutable report](../runs/000002_kamri_alignment_editions/report.md) retain the rules, audited spans, rankings, gaps, and controls. All five experiment-1 groups were treated as development data. Two additional groups were selected before model execution; both were acquired, and neither was replaced based on performance.

| Endpoint on two fresh groups | Structural baseline | Frozen lexical/structural method |
|---|---:|---:|
| Correct source ranked first | 1/2 | 2/2 |
| Correct source admitted | 0/2 | 2/2 |
| Correct / proposed correspondence edges | 1/3 | 6/6 |
| Edge recall | 1/15 (6.7%) | 6/15 (40.0%) |
| Source-absent false admissions | 0/2 | 0/2 |

These fresh results are the same in both Gad edition pools. They are repeated comparisons of the same two inputs, not four independent trials. A refusal to admit a source requires either insufficient strength or fewer than three linked sentences; top-1 ranking alone is not admission.

The new method uses only the exact lexical artifact from experiment 1, filtered by the original support requirements. It adds multiset agreement with emitted candidates to structural similarity. No fresh-group evidence was used to train this lexicon; **no new lexical claims were induced**. The two methods also use different match floors (0.78 versus 0.72). Consequently, this comparison measures the combined method change; it does not isolate the causal contribution of lexical anchors. A matched-floor ablation is needed for that.

## Tamar: strong evidence for an edition mismatch

With the original mirrored English edition, the unchanged structural baseline ranked Tamar second and recovered **0/7** reviewed edges. Substituting the Ken Johnson edition, the same baseline ranked the Gad work first and recovered **7/7**. The lexical method recovered **3/7** with the original edition and **7/7** with Johnson.

| Sentence index | FL tokens | Original English tokens | Johnson English tokens |
|---|---:|---:|---:|
| 0 | 19 | 19 | 19 |
| 1 | 34 | 39 | 34 |
| 2 | 29 | 24 | 29 |
| 3 | 31 | 29 | 31 |
| 4 | 19 | 18 | 19 |
| 5 | 16 | 19 | 16 |
| 6 | 31 | 28 | 31 |

The seven Johnson token counts exactly match the FL counts. Visual inspection of PDF page 38 confirmed the opening passage and repaired three extraction-fragmented English words. This supports an edition-mismatch explanation for the first failure. It does not prove an exact generating text or validate all token meanings: the passage contains name substitutions, quotation differences, and bracketed editorial content. Neither edition creates a separate independent source work.

The original Gad input contains the broader work, whereas Johnson is a Chapter 13 packet. Candidate scope therefore differs in the edition comparison. Better recovery at the audited opening passage and the exact token-count vector are the strongest edition evidence; the rank change alone cannot exclude effects of candidate scope.

## What the fresh samples expose

The [Larsen thesis passage](https://lucris.lub.lu.se/ws/files/4282366/1259363.pdf), printed page 65, corresponds to the opening of [Daemonium Saturni aš misre taşdi](https://forgottenlanguages-full.forgottenlanguages.org/2018/12/daemonium-saturni-as-misre-tasdi.html). The source packet covers printed pages 65–69. The frozen sentence parser breaks at “i.e.” twice, creating two one-to-many correspondences. FL also paraphrases or shortens some terminology. The new method recovered the middle three edges, **3/9**, and ranked the thesis packet first. The structural baseline ranked it fifth in the original-edition pool and fourth in the Johnson pool, with one correct edge conditional on being given the correct source.

The [Tsui Chi translation](https://mbingenheimer.net/tools/bibls/tsui.1943.pdf), verses 223–226, corresponds to the opening of [Lańşdan Wanlah](https://forgottenlanguages-full.forgottenlanguages.org/2018/10/lansdan-wanlah.html). The retained source packet covers verses 223–234, visually inspected on PDF pages 22–23 (printed 195–196). Verse 225 is one source sentence but two FL sentences. The new method recovered the first three edges, **3/6**. The baseline recovered only the first edge and could not meet the three-link admission requirement. All 20 baseline sentence shuffles tied its observed strength, showing how a single strong sentence ignores passage order.

Across the two fresh groups there are 13 FL sentences and 15 reference edges. Even an ideal 1:1 monotonic aligner can recover at most 12/15 edges under the retained boundaries. The observed 6/15 result is still well below that ceiling: sentence boundary problems explain only part of the missing alignment. More flexible phrase alignment must also handle wording differences.

## Controls, evidence, and practical limits

For each method and edition pool, admission thresholds were fixed from the maximum wrong-work strength on the five development groups plus 1e-6. No fresh outcome set a threshold. The source-absent control removes every candidate edition belonging to the correct work. No false admissions occurred in either fresh group; two negatives are insufficient to estimate a reliable false-positive rate. Development negatives also calibrated the rule and are not independent validation.

Twenty shared FL sentence permutations per group were generated with RNG seed 1731. No fresh lexical-method shuffle matched or exceeded the observed strength in either group. These are descriptive controls, not calibrated p-values or evidence of semantic correctness.

Direct FL access remains filtered locally. All FL inputs are bounded indexed excerpts, not raw HTML or complete/current articles. The two new extracts contain 146 and 163 whitespace words, respectively. Source works were nominated by a [public Kamri source report](https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/), then checked against primary text. Candidate selection, uneven packet scopes, and a single analyst's structural annotations limit generalization. There are no independent semantic gold labels.

The [verification receipt](000002_verification.json) confirms saved input/code/output hashes, raw-artifact hashes, Unicode span locations, seven works per pool, fixed denominators, controls, and unchanged first-run artifacts. Fourteen unit and synthetic tests passed before execution. The final run completed in approximately four seconds after preparation; PDF inspection and source audit were separate preparation work.

## Next experiment

A registered many-to-many passage aligner with explicit abbreviation handling is the most direct next step. Use these seven groups as development material, compare anchor/no-anchor methods at identical match floors, and reserve additional source works for fresh evaluation. Before expanding lexical induction, audit actual token/phrase correspondences and retain uncertain meanings rather than relying on equal token counts.

## Reproduce offline

```sh
uv sync --frozen
uv run python scripts/run_alignment_v2.py --run-id replay_000002
uv run python scripts/verify_alignment_v2.py
```

Choose a new run ID; existing directories cannot be overwritten. The verifier targets the saved original run. PDF preparation used bundled pypdf and a PDFium rendering fallback after the local Poppler font configuration failed; experiment execution requires only the declared project environment and retained normalized/raw data. Normalized documents and acquisition artifacts are retained locally and must accompany any relocated checkout. Do not re-download into frozen inputs.
