# Interpretation of the first Kamri excerpt experiment

Run: `000001_kamri_excerpt_baseline`, completed September 30, 2026.

The result supports continuing with source-assisted decipherment. A small structural aligner located four nominated source works without a dictionary or bibliographic answers. It also recovered the complete five-sentence held-out passage. This is a useful baseline for a larger experiment, with substantial acquisition and evaluation limits.

## Scope

The sample comprises 30 sentence correspondences from five short indexed excerpts. The source pool contains only the five nominated works, including the correct sources. It does not represent a search across hundreds of documents or the open web.

Four source groups were assigned to training and one to testing before model execution. The frozen benchmark records source identity, exact character spans, data hashes, and a single analyst's structural review. Fourteen training links were admitted to positional lexical induction; other links remained in retrieval evaluation.

## What worked

| Measure | Result | Interpretation |
|---|---:|---|
| Correct source ranked first | 4/5 excerpts | Useful retrieval on a very small nominated pool |
| Reviewed links recovered in the correct source | 21/30 | Includes the failed Tamar passage |
| Held-out reviewed links recovered | 5/5 | Structural alignment transferred to one source group |
| Proposed training lexical forms | 153 | Hypotheses, not a verified dictionary |
| Held-out tokens seen in training | 65/141 | 46.1% seen-form coverage |
| Held-out supported candidates emitted | 52/141 | 36.9% prediction coverage |
| Held-out abstentions | 89/141 | Unresolved tokens remain visible |
| Positional-reference agreement | 49/52 emitted predictions | Conditional agreement under the positional assumption |
| Independent semantic accuracy | Unmeasured | No independent semantic gold labels |

Most emitted candidates are grammatical words, such as articles, conjunctions, and prepositions. High agreement on these words does not establish recovery of the meaning-bearing vocabulary or a reconstructed grammar. The 89 unresolved tokens are a central result, not an inconvenience to smooth over with a language model.

All three emitted-candidate disagreements involve `ńi`: training supports the candidate “of” across three source groups, while the projected held-out English word is “into.” This suggests a useful next investigation into contextual mappings, adaptation, or the positional assumption. It does not establish which explanation is correct. The dictionary and frozen model were not changed after observing these errors.

Source-absent controls admitted no candidate for the held-out excerpt under the training-derived rule. Training negatives helped set that rule, so rejecting those training negatives is not an independent validation of its false-positive rate. Sentence shuffling reduced mean alignment scores for the four successfully retrieved groups. Tamar's score stayed low.

## What failed

Tamar's correct source ranked second. The aligner recovered none of its seven reviewed sentence correspondences and proposed one incorrect link within that work. The local alignment rule rejected its top source candidate.

The [FL Tamar excerpt](https://forgottenlanguages-full.forgottenlanguages.org/2018/12/tamar.html) and the downloaded [Words of Gad the Seer](https://www.pseudepigrapha.com/WordsOfTheSeerGad.html) share names and an ordered narrative, while differing in wording and token positions. This could involve a source-edition difference, adaptation, or both. This experiment does not distinguish those explanations. Even an equal token count in its first sentence does not justify positional lexical mapping.

The remaining audit also found unequal-length links in the Golden Age, Nichiren, and Christisis excerpts. Heading removal, verse-label removal, and hyphen splitting are declared preprocessing decisions, with original acquisition bytes preserved. They do not remove genuine wording differences.

## Sources and evidence

The initial leads came from the [public Kamri report](https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/). We inspected nominated source passages instead of importing its lexicon or translations. The reference audit remains a single analyst review of structure, not independent semantic validation.

| Source group | FL excerpt | Downloaded English work |
|---|---|---|
| golden_age | [Sadwa ńi mafńi Nalmdin](https://forgottenlanguages-full.forgottenlanguages.org/2018/10/sadwa-ni-mafni-nalmdin.html) | [The Golden Age Restored](https://www.alchemywebsite.com/goldnage.html) |
| nichiren_images | [Natndir şu Kitvaķ](https://forgottenlanguages-full.forgottenlanguages.org/2018/11/natndir-su-kitvak.html) | [Opening the Eyes of Wooden and Painted Images](https://www.nichirenlibrary.org/en/wnd-1/Content/11) |
| gad_seer | [Tamar](https://forgottenlanguages-full.forgottenlanguages.org/2018/12/tamar.html) | [Words of Gad the Seer](https://www.pseudepigrapha.com/WordsOfTheSeerGad.html) |
| christisis | [Dadċu daddaš misrdir](https://forgottenlanguages-full.forgottenlanguages.org/2020/10/dadcu-daddas-misrdir.html) | [Christisis archive OCR](https://archive.org/download/christisishigher00clym/christisishigher00clym_djvu.txt) |
| dark_side_light | [Şu daċrlir kafmęį ladsdan](https://forgottenlanguages-full.forgottenlanguages.org/2020/01/su-dacrlir-kafmei-ladsdan.html) | [The Dark Side of Light](https://www.theosophical.org/publications/quest-magazine/the-dark-side-of-light) |

Raw FL HTML remains unavailable in this local run. Indexed excerpts are labeled accordingly and may be stale. Christisis was read as archive OCR, with no visual verification against the original scan.

## Next scientific step

Preserve the baseline and investigate the source-edition problem before increasing linguistic complexity. Acquire full FL snapshots, independently review token or phrase mappings, and choose additional untouched source groups. Phrase alignment and a statistical word aligner can then be compared against this baseline with coverage and false matches reported separately.

Use the present held-out excerpt as development data if its observed errors inform the next model. It must not become a repeatedly tuned blind test.
