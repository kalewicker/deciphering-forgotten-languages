"""Frozen-source-group experiment runner; no network or LLM calls."""
from __future__ import annotations

import json
import platform
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .alignment import local_align, rank_sources
from .corpus import digest, dump_json
from .lexicon import induce, predict
from .text import sentences


def validate(root: Path, config: dict, benchmark: dict, config_path: Path) -> dict:
    if set(config["train_groups"]) & set(config["test_groups"]):
        raise ValueError("Source group leakage across train/test")
    if benchmark["config_sha256"] != digest(config_path.read_bytes()):
        raise ValueError("Configuration changed after benchmark freeze")
    docs = {}
    groups = set()
    fl_sentence_splits = {}
    for record in benchmark["records"]:
        group = record["group"]
        if group in groups:
            raise ValueError("Duplicate benchmark group")
        groups.add(group)
        expected_split = "test" if group in config["test_groups"] else "train"
        if record["split"] != expected_split:
            raise ValueError("Benchmark split mismatch")
        for kind in ("fl", "source"):
            path = root / record[f"{kind}_path"]
            if digest(path.read_bytes()) != record[f"{kind}_document_sha256"]:
                raise ValueError(f"Document changed after freeze: {path}")
            doc = json.loads(path.read_text())
            if digest(doc["text"].encode()) != doc["text_sha256"]:
                raise ValueError("Normalized text hash mismatch")
            artifact = Path(doc["snapshot"]["artifact"])
            if digest(artifact.read_bytes()) != doc["snapshot"]["sha256"]:
                raise ValueError("Acquisition artifact hash mismatch")
            if doc["source_group"] != group:
                raise ValueError("Source grouping mismatch")
            docs[doc["id"]] = doc
            if kind == "fl":
                for s in sentences(doc["text"], doc["id"]):
                    key = " ".join(t.normalized for t in s.tokens)
                    prior = fl_sentence_splits.get(key)
                    if prior and prior != record["split"]:
                        raise ValueError("Exact duplicate FL sentence across train/test")
                    fl_sentence_splits[key] = record["split"]
    if groups != set(config["train_groups"]) | set(config["test_groups"]):
        raise ValueError("Missing registered source groups")
    return docs


def save_database(path: Path, docs: dict, sentence_map: dict, lexicon: dict, benchmark: dict):
    db = sqlite3.connect(path)
    db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE documents(id TEXT PRIMARY KEY, source_group TEXT, kind TEXT, metadata_json TEXT);
        CREATE TABLE sentences(id TEXT PRIMARY KEY, document_id TEXT REFERENCES documents(id), start INTEGER, end INTEGER);
        CREATE TABLE pairs(id TEXT PRIMARY KEY, source_group TEXT, split TEXT, fl_sentence TEXT REFERENCES sentences(id),
                           source_sentence TEXT REFERENCES sentences(id), positional_eligible INTEGER, semantic_gold INTEGER);
        CREATE TABLE claims(form TEXT, meaning TEXT, state TEXT, candidate_fraction REAL, PRIMARY KEY(form, meaning));
        CREATE TABLE evidence(form TEXT, meaning TEXT, pair_id TEXT REFERENCES pairs(id), fl_start INTEGER, fl_end INTEGER,
                              source_start INTEGER, source_end INTEGER, FOREIGN KEY(form,meaning) REFERENCES claims(form,meaning));
    """)
    for doc in docs.values():
        db.execute("INSERT INTO documents VALUES(?,?,?,?)", (doc["id"], doc["source_group"], doc["kind"], json.dumps(doc, ensure_ascii=False)))
        for sentence in sentence_map[doc["id"]]:
            db.execute("INSERT INTO sentences VALUES(?,?,?,?)", (sentence.id, doc["id"], sentence.start, sentence.end))
    for record in benchmark["records"]:
        for link in record["links"]:
            fs = sentence_map["fl_" + record["group"]][link["fl_index"]]
            es = sentence_map["source_" + record["group"]][link["source_index"]]
            db.execute("INSERT INTO pairs VALUES(?,?,?,?,?,?,?)", (link["id"], record["group"], record["split"], fs.id, es.id,
                                                                    link["positional_eligible"], link["semantic_gold"]))
    for form, entry in lexicon.items():
        for candidate in entry["candidates"]:
            db.execute("INSERT INTO claims VALUES(?,?,?,?)", (form, candidate["meaning"], entry["state"], candidate["candidate_fraction"]))
            for evidence in candidate["evidence"]:
                db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)", (form, candidate["meaning"], evidence["pair_id"],
                                                                          *evidence["fl_span"], *evidence["source_span"]))
    db.commit()
    db.close()


def run(root: Path, config_path: Path, benchmark_path: Path, run_id: str | None = None) -> Path:
    config, benchmark = json.loads(config_path.read_text()), json.loads(benchmark_path.read_text())
    docs = validate(root, config, benchmark, config_path)
    sentence_map = {key: sentences(doc["text"], key) for key, doc in docs.items()}
    # Source collection is allowed in retrieval; answer labels are not passed to ranker.
    sources = {key: value for key, value in sentence_map.items() if docs[key]["kind"] == "source"}
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    if not run_id or Path(run_id).name != run_id or run_id in (".", ".."):
        raise ValueError("Run ID must be a single directory name")
    out = root / "runs" / run_id
    out.mkdir(parents=True, exist_ok=False)
    code_files = list((root / "src/fl_decipher").glob("*.py")) + list((root / "scripts").glob("*.py"))
    code_files += [root / "pyproject.toml", root / "uv.lock"]
    manifest = {"run_id": run_id, "state": "running", "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "experiment_id": config["experiment_id"], "python": platform.python_version(),
                "config_sha256": digest(config_path.read_bytes()), "benchmark_sha256": digest(benchmark_path.read_bytes()),
                "code_hashes": {str(p.relative_to(root)): digest(p.read_bytes()) for p in code_files if p.exists()},
                "input_hashes": {k: v["text_sha256"] for k, v in docs.items()}, "configuration": config,
                "classification": "exploratory engineering; no validated semantic accuracy"}
    dump_json(out / "manifest.json", manifest)
    try:
        retrieval, training_pairs = [], []
        for record in benchmark["records"]:
            group = record["group"]
            fs = sentence_map["fl_" + group]
            ranked = rank_sources(fs, sources, config["alignment"])
            expected = "source_" + group
            rank = next(i + 1 for i, item in enumerate(ranked) if item["source_id"] == expected)
            expected_alignment = next(item for item in ranked if item["source_id"] == expected)
            reference = {(x["fl_index"], x["source_index"]) for x in record["links"]}
            proposed = {(x["fl_index"], x["source_index"]) for x in expected_alignment["links"]}
            hits = len(reference & proposed)
            retrieval.append({"group": group, "split": record["split"], "expected_source_rank": rank,
                              "rankings": ranked, "reference_links": len(reference), "proposed_links": len(proposed),
                              "correct_links": hits, "alignment_precision": hits / len(proposed) if proposed else None,
                              "alignment_recall": hits / len(reference),
                              "audit_note": record["note"]})
            if record["split"] == "train":
                for link in record["links"]:
                    if link["positional_eligible"]:
                        training_pairs.append((link["id"], group, fs[link["fl_index"]], sources[expected][link["source_index"]]))
        lexicon = induce(training_pairs)
        dump_json(out / "lexicon.json", lexicon)

        # Training-only wrong-source maxima define a conservative engineering rejection rule.
        negatives = [item for result in retrieval if result["split"] == "train" for item in result["rankings"]
                     if item["source_id"] != "source_" + result["group"]]
        rejection_floor = max((x["strength"] for x in negatives), default=0) + 1e-6
        rng = random.Random(config["controls"]["seed"])
        controls = []
        for result in retrieval:
            group = result["group"]
            expected = "source_" + group
            best = result["rankings"][0]
            eligible = bool(best.get("minimum_links_met") and best["strength"] > rejection_floor)
            result["source_admitted_by_training_rule"] = eligible
            wrong = [x for x in result["rankings"] if x["source_id"] != expected][0]
            absent_accept = bool(wrong.get("minimum_links_met") and wrong["strength"] > rejection_floor)
            shuffled = []
            fs = sentence_map["fl_" + group]
            for _ in range(config["controls"]["sentence_shuffle_repetitions"]):
                order = rng.sample(fs, len(fs))
                shuffled.append(local_align(order, sources[expected], config["alignment"])["strength"])
            controls.append({"group": group, "source_absent_best": wrong["source_id"],
                             "source_absent_score": wrong["strength"], "source_absent_false_accept": absent_accept,
                             "ordered_true_source_score": next(x["strength"] for x in result["rankings"] if x["source_id"] == expected),
                             "sentence_shuffle_scores": shuffled,
                             "sentence_shuffle_mean": sum(shuffled) / len(shuffled) if shuffled else None})

        predictions = []
        for record in benchmark["records"]:
            if record["split"] != "test":
                continue
            group = record["group"]
            for link in record["links"]:
                fs = sentence_map["fl_" + group][link["fl_index"]]
                predicted = predict(fs, lexicon, config["lexicon"])
                # Prediction is complete BEFORE consulting the held-out source reference.
                es = sources["source_" + group][link["source_index"]]
                reference = [t.normalized for t in es.tokens] if link["positional_eligible"] else None
                for i, token in enumerate(predicted):
                    token["positional_reference"] = reference[i] if reference is not None else None
                    token["agrees_with_positional_reference"] = token["prediction"] == reference[i] if reference is not None and token["prediction"] else None
                predictions.append({"pair_id": link["id"], "fl_text": fs.text, "tokens": predicted,
                                    "gloss": " ".join(t["prediction"] or f"[{t['surface']}]" for t in predicted),
                                    "semantic_accuracy_validated": False})
        all_tokens = [token for sentence in predictions for token in sentence["tokens"]]
        emitted = [t for t in all_tokens if t["prediction"] is not None]
        scored = [t for t in emitted if t["agrees_with_positional_reference"] is not None]
        correct = sum(t["agrees_with_positional_reference"] for t in scored)
        known = sum(t["candidate"] is not None for t in all_tokens)
        metrics = {"registered_groups": len(benchmark["records"]), "reviewed_sentence_pairs": sum(len(r["links"]) for r in benchmark["records"]),
                   "training_positional_pairs": len(training_pairs), "lexical_forms_proposed": len(lexicon),
                   "held_out_tokens": len(all_tokens), "held_out_seen_tokens": known, "held_out_emitted_tokens": len(emitted),
                   "held_out_abstained_tokens": len(all_tokens) - len(emitted),
                   "seen_token_coverage": known / len(all_tokens) if all_tokens else None,
                   "supported_prediction_coverage": len(emitted) / len(all_tokens) if all_tokens else None,
                   "positional_reference_agreements": correct, "positional_reference_scored_predictions": len(scored),
                   "positional_reference_agreement": correct / len(scored) if scored else None,
                   "semantic_translation_accuracy": None, "training_negative_rejection_floor": rejection_floor}
        report = {"metrics": metrics, "retrieval": retrieval, "controls": controls,
                  "limitations": config["limitations"], "annotation_method": benchmark["annotation_method"]}
        dump_json(out / "report.json", report)
        dump_json(out / "predictions.json", predictions)
        save_database(out / "evidence.sqlite", docs, sentence_map, lexicon, benchmark)
        write_report(out / "report.md", report, run_id)
        artifacts = [p for p in out.iterdir() if p.name != "manifest.json"]
        manifest.update(state="completed", completed_at_utc=datetime.now(timezone.utc).isoformat(),
                        artifact_hashes={p.name: digest(p.read_bytes()) for p in artifacts}, metrics=metrics)
        dump_json(out / "manifest.json", manifest)
        return out
    except Exception as exc:
        manifest.update(state="failed", error=f"{type(exc).__name__}: {exc}")
        dump_json(out / "manifest.json", manifest)
        raise


def write_report(path: Path, report: dict, run_id: str):
    m = report["metrics"]
    lines = [f"# Kamri excerpt pilot — {run_id}", "", "Classification: exploratory engineering result.", "",
             "Five indexed FL excerpts and five nominated source works. Four source groups train the lexical baseline; one is held out.",
             "Public source leads and a single analyst's structural audit were available. Semantic translation accuracy is unverified.", "",
             "## Source retrieval and passage alignment", "",
             "Ranker sees the full five-document source pool and FL text; it receives no bibliography, answer identity, or dictionary.", "",
             "| Group | Split | Correct source rank | Reviewed links recovered | Proposed links | Rule admits top source |",
             "|---|---|---:|---:|---:|---|"]
    for r in report["retrieval"]:
        lines.append(f"| {r['group']} | {r['split']} | {r['expected_source_rank']} | {r['correct_links']}/{r['reference_links']} | {r['proposed_links']} | {r['source_admitted_by_training_rule']} |")
    lines += ["", "Alignment recovery is evaluated within the nominated source. Wrong-source rankings are preserved separately.", "",
              "## Lexical prediction", "",
              f"- Training pairs admitted to positional induction: {m['training_positional_pairs']}.",
              f"- Proposed lexical forms: {m['lexical_forms_proposed']}.",
              f"- Held-out tokens seen in the training lexicon: {m['held_out_seen_tokens']}/{m['held_out_tokens']}.",
              f"- Held-out predictions meeting support requirements: {m['held_out_emitted_tokens']}/{m['held_out_tokens']}.",
              f"- Abstentions: {m['held_out_abstained_tokens']}/{m['held_out_tokens']}.",
              f"- Agreement with projected source positions: {m['positional_reference_agreements']}/{m['positional_reference_scored_predictions']} emitted, scorable predictions.",
              "- Independent semantic translation accuracy: **not measured**.", "",
              "The lexicon uses reviewed, equal-length training links, not automatic retrieval output. Gad is retained in retrieval but excluded from lexical induction because wording and positions differ.",
              "Candidate frequencies are not calibrated probabilities. Predictions require two observations, two source groups, and at least 0.8 candidate fraction. Unsupported words remain bracketed in predictions.json.", "",
              "## Controls", "",
              f"Rejection floor, chosen from training wrong-source maxima only: {m['training_negative_rejection_floor']:.6f}. This is an engineering rule, not a calibrated false-positive guarantee.", "",
              "| Group | Ordered correct-source score | Mean shuffled score | Source-absent best score | False admission with source absent |",
              "|---|---:|---:|---:|---|"]
    for c in report["controls"]:
        lines.append(f"| {c['group']} | {c['ordered_true_source_score']:.4f} | {c['sentence_shuffle_mean']:.4f} | {c['source_absent_score']:.4f} | {c['source_absent_false_accept']} |")
    lines += ["", "All 20 shuffle scores per group, wrong candidates, gaps, and links are stored in report.json.", "",
              "## Audit findings", ""]
    for r in report["retrieval"]:
        lines.append(f"- {r['group']}: {r['audit_note']}")
    lines += ["", "## Limits and next work", ""] + [f"- {x}." for x in report["limitations"]]
    lines += ["", "Next: obtain raw FL snapshots through an available authorized access path; independently review token/phrase mappings; resolve source-edition differences; expand to more source groups and full passages. This held-out sample becomes development data if used to tune a revised model.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
