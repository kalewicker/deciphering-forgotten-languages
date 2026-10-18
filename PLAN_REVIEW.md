# FL-Decipher: proposed revisions and initial research plan

Status: planning proposal, September 30, 2026. No decipherment claims have been validated by this project yet.

This review follows the supplied 60-section plan. It preserves its evidence-first principle and long-term ambition, while moving the first falsifiable experiment ahead of archive-wide infrastructure.

## 1. Change the first objective

The first objective should be:

> On a small, frozen corpus, recover independently checkable source alignments, learn lexical correspondences, and measure predictions on untouched source groups while rejecting plausible false matches.

The complete archive, language inventory, grammars, family graph, translator, and autonomous laboratory remain later objectives. They should not all be prerequisites for this experiment.

Replace “complete FL corpus” with “versioned corpus snapshot with measured acquisition coverage.” Completeness needs an enumeration method, retrieval date, expected and retrieved URL lists, failed fetches, and explicit exclusions. The live site can change.

## 2. Audit the claimed starting point

Sections 15 and 52–55 treat Kamri and Yid as already cracked calibration environments. Use the public reports as leads, then audit examples before treating them as reference answers.

- The [Kamri report](https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/) claims continuous source matches for 23 of 24 posts. Its source list includes several posts drawing from the same work, and it marks one post provisional.
- The [Yid report](https://www.reddit.com/r/ForgottenLanguages/comments/1v2be1i/all_86_yid_posts_from_forgotten_languages/) distinguishes source matches from contextual reconstructions and describes changes to names, locations, and technical terms. It also acknowledges incomplete word correspondence.

These are primary reports by the person making the claims, not independent validation by this project. Reading the reports does not verify their statistics or translations.

Create a benchmark manifest containing FL URL, FL snapshot hash, source identity and edition, source snapshot hash, exact passage locations, proposed correspondences, editorial differences, annotation author, and review status. A source pair can have verified document identity while individual token meanings remain unresolved.

If enough reliable examples cannot be established, benchmark construction is the next task. Do not substitute fluent public translations for missing evidence.

## 3. Separate four questions

| Question | Input available during evaluation | Output |
|---|---|---|
| Source retrieval | FL passage, declared metadata, fixed source collection | Ranked documents or no adequate candidate |
| Passage alignment | FL passage and candidate source | Explicit span correspondences, gaps, and alternatives |
| Lexicon prediction | Frozen training lexicon/model and held-out FL text | Token or phrase candidates and abstentions |
| Linguistic translation | Frozen linguistic model and held-out FL text | Evidence-supported glosses and translation |

Run retrieval separately with bibliography available and withheld. Also distinguish a fixed collection containing the true source from open-world search, where that source may be missing.

Never score a retrieved English passage as if it were an independent translation. Preserve differences such as omitted clauses and substituted entities. Evaluate those differences separately.

The distinction is already present in section 34, but it must govern training, metrics, and admission of evidence throughout the system.

## 4. Protect evaluation from leakage

The article-level and sentence-level holdouts in sections 15, 40, and 53 are insufficient on their own.

Before splitting, group:

- passages from the same underlying source work, including editions and mirrors;
- exact and near-duplicate FL passages;
- known parallel versions across FL labels;
- composite articles connected to several source works.

Assign connected groups to training, development, or test. Shared vocabulary across independent sources is expected; duplicated source passages across splits are leakage. If grouping produces too few independent groups, acquire more examples or report the limitation instead of forcing a nominal 80/20 split.

Freeze the test manifest before tuning. Hold test translations, lexical labels, and source identities out of training and model prompts. Test source documents may appear in the retrieval collection, but their answer keys must remain hidden and their matches must not enter the training lexicon before scoring.

Use development data for method changes and threshold selection. Record every final test invocation; repeated feedback from a test makes it development data. Active learning must use a separate acquisition pool.

An LLM might already recognize public examples. Declare LLM-assisted evaluation separately and include an algorithmic baseline and freshly generated synthetic cases with private transformation keys.

## 5. Compare mechanisms before inferring grammar

The plan lists alternative mechanisms but does not specify how to distinguish them. Start with competing models:

1. Stable token substitution with preserved order.
2. Substitution with multiple forms or contextual alternatives.
3. Phrase mappings and local reordering.
4. A shared base transformation plus article, date, or register variation.
5. Morphological rules that predict unseen forms.
6. Mixed transformations, copied templates, or material with no recoverable semantic mapping.

Compare held-out prediction and model complexity. A larger dictionary can memorize the training corpus; a grammar should explain more with fewer exceptions and predict new observations.

Add synthetic cases with known keys: substitution, homophonic alternatives, inserted/deleted tokens, phrase replacement, reordering, affixation, mixed segments, and unrelated or meaningless material. Separate the expected solvable cases from cases that should trigger abstention.

Do not call a shared spelling prefix a stem without predictive evidence. Test a proposed affix on lexemes and source groups excluded from its induction. Include non-concatenative changes and accidental similarity as alternatives.

English dependency projection is an annotation hypothesis. An English-shaped transformed passage alone cannot establish that a separately generalizing FL grammar has been reconstructed.

## 6. Make the smallest useful pipeline

Initial flow:

```text
audited sample and frozen splits
  -> lossless snapshots and span-preserving parsing
  -> structural source retrieval
  -> local sequence alignment with gaps
  -> lexical baseline
  -> held-out scoring and rejection tests
  -> evidence report
```

Use Python, SQLite, a parser, and a small CLI first. Add scikit-learn when a measured task needs it. Defer PyTorch, semantic embeddings, FAISS, graph infrastructure, a web API, and agents until a demonstrated bottleneck warrants them.

Use a normal package layout such as `src/fl_decipher/`, with `benchmarks/`, `experiments/`, `runs/`, and `reports/` alongside it. Large raw artifacts should be addressed by content hash rather than committed as ordinary code files.

Represent claims, evidence, and dependencies in SQLite. Graph visualization can be a derived view; it does not require a graph database.

## 7. Improve retrieval and alignment

Sections 9–14 need candidate generation before detailed comparison. Avoid computing all sentence pairs across the archive.

- Index rare numerals, formulas, named strings, punctuation patterns, and sentence-count ranges.
- Retrieve a bounded candidate set, then align paragraph or sentence windows.
- Treat word-length preservation as a feature to test. A word-replacement system need not preserve character lengths.
- Keep alternate tokenizations or boundaries for ambiguous cases; record which segmentation produced a match.
- Support null matches, split/merged sentences, omissions, insertions, and changes of source within an article.
- Permit locally monotonic blocks with reordered blocks rather than assuming a single global order.
- Penalize weak matches and allow partial coverage. Do not force an alignment through the whole article.

Begin with positional word alignment as a baseline, then compare a statistical aligner on verified sentence pairs. [fast_align](https://github.com/clab/fast_align) is an established candidate that takes tokenized parallel sentences; its output would still require validation here.

Use embeddings initially for known-language source indexing and metadata search. Multilingual encoders are trained using particular language resources; their documented success does not establish semantic correspondence for an unseen FL system. That limitation is an inference from the training setup described in [Artetxe and Schwenk (2019)](https://aclanthology.org/Q19-1038/), and should be tested rather than assumed away.

## 8. Replace confidence arithmetic with measurable uncertainty

The multiplicative formula in section 23 is a heuristic score, not a calibrated probability. Its factors can be correlated, and dependencies may reuse the same observation.

Store separately:

- raw method score and method version;
- evidence type;
- claim review state;
- supporting and contradicting observations;
- independent source-group count;
- calibrated probability, only when supported by sufficient held-out labels.

Use states such as `proposed`, `supported`, `reviewed`, `rejected`, and `superseded`. A model-generated hypothesis remains a proposal until observations support it. Evidence classes should describe how a claim was obtained; they should not imply an automatic numerical certainty ranking.

Choose abstention thresholds on development data. Report precision versus coverage and calibration by task; retrieval, alignment, lexical mapping, and grammar need different assessments. [Guo et al. (2017)](https://proceedings.mlr.press/v70/guo17a.html) provides relevant background on the difference between model confidence and measured correctness, not a ready-made confidence model for this project.

Preserve the possibility that every listed lexical candidate is wrong. A distribution normalized only over nominated meanings can otherwise look certain even when the correct answer is absent.

## 9. Prevent circular evidence amplification

The feedback loop in sections 14, 20–26, and 47 needs an explicit admission boundary.

Example failure:

```text
tentative dictionary -> candidate source alignment
candidate alignment -> same dictionary gets stronger
stronger dictionary -> candidate alignment appears confirmed
```

Record observations separately from deductions. A dependency path returning to its originating evidence cannot count as new independent support. Different agents, editions, copied passages, or translation paths do not automatically supply independent evidence.

Use immutable knowledge snapshots for each run:

1. Generate candidates using the frozen snapshot.
2. Validate them against declared observations and controls.
3. Record accepted claims in a new snapshot.
4. Mark dependent outputs stale when an ancestor is rejected or revised.
5. Recompute affected outputs with the new version.

Keep historical outputs accessible. Begin with conservative invalidation, rather than pretending an exact confidence update can be calculated for every dependency.

## 10. Strengthen controls and metrics

Use hard negatives matched for topic, approximate length, quotations, equations, and repeated boilerplate. Include incorrect cited documents and cases where the true source is deliberately absent.

Measure the strongest false match produced by the entire search procedure, including its candidate ranking and alignment windows. A threshold tested on a few arbitrary sentence pairs does not establish its false-match rate after thousands of comparisons.

Use shuffled controls with a declared purpose. Shuffling sentence order tests sequence evidence but leaves token counts intact; unchanged lexical scores under that control need not be a bug.

| Component | Primary measures |
|---|---|
| Corpus | Enumerated/retrieved/parsed counts; failed pages; sampled extraction errors |
| Retrieval | Recall@k, reciprocal rank, performance with the source absent |
| Alignment | Reviewed span precision/recall; false alignments; unmatched coverage |
| Lexicon | Token-weighted and type-weighted accuracy; content/function words; coverage |
| Morphology | Accuracy on held-out lexemes and forms; exception rate |
| Translation | Meaning-bearing errors, omissions, unsupported additions, abstention coverage |
| Evidence system | Traceability, independent support counts, correct invalidation after retraction |

Report denominators and uncertainty. Unknowns, failed imports, unretrieved sources, and rejected matches stay visible in their relevant denominators. Word coverage and sentence fluency are insufficient measures of translation accuracy.

## 11. Preserve data and reproducibility

Add raw response bytes, acquisition timestamps, final and requested URLs, response status, encoding, content hashes, and parser versions to the corpus contract. Preserve PDF page references and distinguish native extraction from OCR. Record unavailable source documents explicitly.

Separate structural block types (`paragraph`, `heading`, `quote`, `list`, `formula`, `bibliography`) from language annotations. A paragraph can contain several languages, and a quote can also be in an unknown language. Store language annotations on spans with provisional labels.

Keep raw Unicode and source offsets. Use explicit, versioned normalized views; NFC can be a default comparison view, while diacritic removal should be an optional search feature. Do not silently merge distinct symbols. Preserve offset maps through normalization and tokenization.

Each run manifest should identify data hashes, split manifest, code revision, configuration, seeds, dependency lock, external model versions and settings, and artifacts. Store prompts and responses for model-assisted steps and timestamped queries/results for web search. Live web rediscovery and LLM calls are not guaranteed reproducible merely because a seed was stored.

For crawling, inspect the site's access rules, enumerate before fetching, cache and resume requests, and use conservative request rates. Keep local research copies distinct from exports; source URLs, hashes, and passage offsets can support public evidence reports without bundling every source document.

## 12. Refine comparative and historical claims

Character clusters are provisional orthographic groups. They can reflect script, topic, author, date, text length, or generator settings rather than language ancestry. Test stability across sample sizes, feature choices, and topic-balanced subsets.

Separate edges for shared source passages, lexical similarity, systematic form transformations, common grammar, and hypothesized derivation. Demonstrate repeated correspondences on held-out items before inferring family relationships. Shared English order or a shared source alone is insufficient.

Publication chronology records observed usage, not necessarily language evolution. Compare date effects against genre and register. A hidden interlingua remains a speculative hypothesis unless it makes predictions that simpler shared-source models cannot explain.

Replace the single “translated” ladder in section 58 with independent status dimensions: source recovery, lexical coverage, alignment quality, grammatical prediction, unseen-text performance, and dialect/date transfer. These do not necessarily advance together.

Do not label unmatched paragraphs “original FL prose.” Use “source not identified.” Failure to locate a source establishes neither originality nor successful translation.

## 13. Proposed milestones and decision gates

| Milestone | Deliverable | Decision gate |
|---|---|---|
| A. Audit and freeze | A few independently checked Kamri examples, source groups, exact spans, negative candidates, and split manifest | Answers have inspectable backing; enough independent groups exist for the intended evaluation |
| B. Offline baseline | Parser, structural retrieval, local alignment, lexical baseline, and run report | Known synthetic transformations work as specified; null cases can be rejected; failures have traceable causes |
| C. Real held-out pilot | Separate retrieval, alignment, and lexicon results across untouched source groups | Report useful precision/coverage and false-match behavior against simple baselines; choose development thresholds before test |
| D. Transfer pilot | Limited Yid, Kamri Western, or one source-rich unknown sample | Show reproducible transfer beyond copied passages; retain failures and unmatched text |
| E. Expand corpus | Versioned archive snapshot and provisional language map | Acquisition coverage, parser quality, deduplication, and indexing are measured |
| F. Reconstruct and expose | Predictive morphology/grammar and an evidence-linked translation interface | Claims survive held-out tests appropriate to their scope |
| G. Automate | Bounded research scheduler, dependency invalidation, optional agents | Automatic updates preserve the same evidence and evaluation rules |

Five articles are a useful engineering smoke test, not a sufficient accuracy claim. Choose pilot size based on independent source groups and annotation effort. Numerical success thresholds should be specified after inspecting the available sample and development controls, then frozen before final scoring.

Stop an unsuccessful branch with a recorded result, not a polished reconstruction. Low lexical coverage may justify more independent data; poor alignment may justify a better model. Neither result automatically invalidates the entire project.

The [Twenty-second-century consciousness article](https://forgottenlanguages-full.forgottenlanguages.org/2026/08/twenty-second-century-consciousness.html) can be a tracked case study with fixed inputs and unresolved spans. Without independently established reference answers, it is not an accuracy benchmark. If earlier interpretations influenced development, it should not be advertised as a blind test.

## 14. Recommended first implementation task

Build a reproducible Kamri pilot that accepts saved FL/source snapshots and a benchmark manifest, proposes local passage alignments, emits a lexical baseline, and produces a report with rejection controls and held-out source-group scores.

Start by auditing the source pairs. This is the smallest complete experiment that can tell us whether the larger architecture is worth expanding and what its next bottleneck actually is.
