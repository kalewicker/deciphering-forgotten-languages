# Experiment 2 registration (before aligner execution)

Registered 2026-09-30. Exploratory source-edition and sentence-alignment experiment.

Primary questions: does a different English edition repair the Tamar mismatch; does a frozen lexical-anchor aligner generalize to two new source works?

- Development: all five v1 groups, including the previously tested dark_side_light.
- Fresh evaluation: western_esoterism (Daemonium Saturni, 2018-12-04) and manichaean_hymn (Lańşdan Wanlah, 2018-10-20). These were nominated by an existing public source report, not discovered blindly. Missing acquisition or unusable extraction stays in the selected denominator of two; no replacement.
- FL sample: opening complete sentences up to 180 whitespace words, using indexed extracts because direct host acquisition is locally filtered. No full-page claim.
- English source pool: five unchanged v1 documents, Johnson Gad translation (same gad_seer work), Larsen thesis printed pages 65–69, and Tsui Chi translation source packet. Record exact extracted scope and hashes before execution. This is fixed-pool ranking, not open-web discovery.
- Reference links: one analyst reviews passage order and exact text spans before running either aligner. Labels are structural correspondences, not independently validated semantic translations. Reordered, split, or ambiguous correspondences may be ineligible for 1:1 evaluation and must be disclosed.
- Baseline: unchanged v1 structural scoring, floor 0.78, gap 0.35, minimum 3 links.
- New method: structural/lexical blend, 0.60 structural and 0.40 multiset lexical agreement over predictions supported by the frozen v1 lexicon and its original eligibility rules. Missing lexical predictions contribute neutral 0.50. Floor 0.72, gap 0.35, minimum 3 links. No lexical induction, contextual fixes, or parameter search in this experiment.
- Lexical score: number of frozen predicted words present in candidate sentence, counting multiplicity, divided by number of emitted predictions. This is an auxiliary anchor score; common function words are not semantic proof.
- Edition ablation: run each method with original Gad edition only and Johnson edition only. Both editions remain one work for ranking and all source-absent controls.
- Admission: independently for each method and pool, threshold = maximum wrong-work strength across all five development groups + 1e-6. Require 3 links. No fresh evaluation outcomes used to set thresholds.
- Controls: source absent (remove every edition of the correct work), 20 FL sentence permutations per group, RNG seed 1731. Report shuffle strength distribution and exceedances, not calibrated p-values.
- Primary endpoints: fresh work top-1 count / 2 selected groups; correct passage precision and recall; fresh source-absent false admissions / 2. Development and edition diagnostics reported separately. All runs, failures, input/code/output hashes retained.
- Stop rule: one final run after synthetic tests and source audit. Any subsequent tuning makes these two groups development data and requires a new run ID. No automatic acceptance of lexical claims.
