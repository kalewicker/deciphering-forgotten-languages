import json
from pathlib import Path
import tempfile
import unittest

from fl_decipher.alignment import local_align
from fl_decipher.corpus import digest, dump_json, html_text
from fl_decipher.experiment import validate
from fl_decipher.lexicon import induce, predict
from fl_decipher.text import normal, sentences, tokens

CONFIG = {"weights": {"length": .55, "punctuation": .2, "repetition": .2, "anchors": .05},
          "match_floor": .78, "gap_penalty": .35, "minimum_links": 3}


class PilotTests(unittest.TestCase):
    def test_unicode_offsets_survive_normalization_and_hyphen_splitting(self):
        text = "Ţaţuh t\u0327aţuh thirty-two Buddha’s."
        ts = tokens(text)
        self.assertEqual(ts[0].normalized, ts[1].normalized)
        self.assertEqual([t.normalized for t in ts[2:]], ["thirty", "two", "buddha's"])
        for t in ts:
            self.assertEqual(text[t.start:t.end], t.surface)
        for s in sentences(text):
            self.assertEqual(text[s.start:s.end], s.text)

    def test_headings_and_verse_labels_do_not_become_words(self):
        raw = b"<body><h2>Header</h2><p>XIII</p><p>289 And Solomon lived.</p><p><strong>Another heading</strong></p><p>He spoke.</p></body>"
        self.assertEqual(html_text(raw, verse_labels=True), "And Solomon lived. He spoke.")

    def test_local_alignment_recovers_known_key_with_source_gap(self):
        # Distinct repetition patterns and lengths, exact known token substitution.
        plain = []
        for i in range(12):
            words = ["the", f"bird{i}", "sees", "the", f"tree{i}"] + [f"extra{k}" for k in range(i)]
            plain.append(" ".join(words) + ".")
        vocab = {w for s in plain for w in s.rstrip(".").split()}
        key = {w: f"ţ{k}a" for k, w in enumerate(sorted(vocab))}
        cipher = [" ".join(key[w] for w in s.rstrip(".").split()) + "." for s in plain]
        source = plain[:6] + ["Unrelated extra material with a very different structure?"] + plain[6:]
        result = local_align(sentences(" ".join(cipher)), sentences(" ".join(source)), CONFIG)
        expected = {(i, i if i < 6 else i + 1) for i in range(12)}
        self.assertEqual({(x["fl_index"], x["source_index"]) for x in result["links"]}, expected)
        self.assertIn({"side": "source", "index": 6}, result["gaps"])

    def test_same_structure_is_not_independent_semantic_confirmation(self):
        a = sentences("aa bb aa.")
        b = sentences("cat dog cat.")
        c = sentences("sun moon sun.")
        self.assertEqual(local_align(a, b, CONFIG)["strength"], local_align(a, c, CONFIG)["strength"])

    def test_lexicon_support_counts_independent_groups_and_abstains(self):
        fs, es = sentences("ţu na ţu.")[0], sentences("the bird the.")[0]
        lex = induce([("a1", "a", fs, es), ("a2", "a", fs, es)])
        cfg = {"minimum_observations": 2, "minimum_source_groups": 2, "minimum_candidate_fraction": .8}
        self.assertTrue(all(t["prediction"] is None for t in predict(fs, lex, cfg)))
        lex = induce([("a1", "a", fs, es), ("b1", "b", fs, es)])
        output = predict(sentences("ţu unknown.")[0], lex, cfg)
        self.assertEqual(output[0]["prediction"], "the")
        self.assertIsNone(output[1]["prediction"])
        self.assertEqual(lex["ţu"]["state"], "proposed")

    def test_source_group_leakage_fails_before_run(self):
        cfg = {"train_groups": ["same"], "test_groups": ["same"]}
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate(Path("."), cfg, {}, Path("unused"))

    def test_modified_input_fails_hash_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {"train_groups": ["a"], "test_groups": []}
            dump_json(root / "config.json", cfg)
            (root / "input.json").write_text("changed")
            benchmark = {"config_sha256": digest((root / "config.json").read_bytes()),
                         "records": [{"group": "a", "split": "train", "fl_path": "input.json",
                                      "fl_document_sha256": digest(b"original")}]}
            with self.assertRaisesRegex(ValueError, "changed after freeze"):
                validate(root, cfg, benchmark, root / "config.json")


if __name__ == "__main__":
    unittest.main()
