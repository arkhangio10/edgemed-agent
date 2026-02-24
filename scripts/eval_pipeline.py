#!/usr/bin/env python3
"""Evaluation pipeline: runs extraction on synthetic notes and computes metrics.

Usage:
    python scripts/eval_pipeline.py [--notes data/synthetic_notes.json]
                                     [--truth data/ground_truth.json]
                                     [--output eval_results.json]

Metrics:
    - Field-level F1 / exact match for medications, allergies, problems
    - Critical recall for allergies and medications (safety-critical)
    - Average / median / P95 latency per note
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.schemas import ClinicalRecord
from shared.validator import validate
from local.services.local_extraction import LocalExtractor


def normalize(s: str) -> str:
    return s.strip().lower()


def fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio() >= threshold


def compute_set_metrics(
    predicted: list[str], ground_truth: list[str], fuzzy: bool = True
) -> dict:
    if not ground_truth and not predicted:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not ground_truth:
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0}
    if not predicted:
        return {"precision": 1.0, "recall": 0.0, "f1": 0.0}

    tp = 0
    matched_gt = set()
    for p in predicted:
        for i, g in enumerate(ground_truth):
            if i in matched_gt:
                continue
            if fuzzy and fuzzy_match(p, g):
                tp += 1
                matched_gt.add(i)
                break
            elif not fuzzy and normalize(p) == normalize(g):
                tp += 1
                matched_gt.add(i)
                break

    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(ground_truth) if ground_truth else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def extract_med_names(meds: list) -> list[str]:
    names = []
    for m in meds:
        if isinstance(m, dict):
            names.append(m.get("name", ""))
        elif hasattr(m, "name"):
            names.append(m.name)
        else:
            names.append(str(m))
    return [n for n in names if n]


def extract_allergy_substances(allergies: list) -> list[str]:
    substances = []
    for a in allergies:
        if isinstance(a, dict):
            substances.append(a.get("substance", ""))
        elif hasattr(a, "substance"):
            substances.append(a.substance)
        else:
            substances.append(str(a))
    return [s for s in substances if s]


def extract_problem_descriptions(problems: list) -> list[str]:
    descs = []
    for p in problems:
        if isinstance(p, dict):
            descs.append(p.get("description", ""))
        elif hasattr(p, "description"):
            descs.append(p.description)
        else:
            descs.append(str(p))
    return [d for d in descs if d]


def evaluate_single(
    predicted: ClinicalRecord, gt_record: dict, latency_ms: float
) -> dict:
    pred_meds = extract_med_names(predicted.medications)
    gt_meds = extract_med_names(gt_record.get("medications", []))

    pred_allergies = extract_allergy_substances(predicted.allergies)
    gt_allergies = extract_allergy_substances(gt_record.get("allergies", []))

    pred_problems = extract_problem_descriptions(predicted.assessment)
    gt_problems = extract_problem_descriptions(gt_record.get("assessment", []))

    meds_metrics = compute_set_metrics(pred_meds, gt_meds)
    allergy_metrics = compute_set_metrics(pred_allergies, gt_allergies)
    problem_metrics = compute_set_metrics(pred_problems, gt_problems, fuzzy=True)

    flags = validate(predicted)

    return {
        "medications_f1": meds_metrics["f1"],
        "medications_precision": meds_metrics["precision"],
        "medications_recall": meds_metrics["recall"],
        "allergies_f1": allergy_metrics["f1"],
        "allergies_precision": allergy_metrics["precision"],
        "allergies_recall": allergy_metrics["recall"],
        "problems_f1": problem_metrics["f1"],
        "problems_precision": problem_metrics["precision"],
        "problems_recall": problem_metrics["recall"],
        "critical_recall_allergies": allergy_metrics["recall"],
        "critical_recall_medications": meds_metrics["recall"],
        "completeness_score": flags.completeness_score,
        "missing_fields_count": len(flags.missing_fields),
        "contradictions_count": len(flags.contradictions),
        "latency_ms": latency_ms,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate extraction pipeline")
    parser.add_argument("--notes", default="data/synthetic_notes.json")
    parser.add_argument("--truth", default="data/ground_truth.json")
    parser.add_argument("--output", default="eval_results.json")
    parser.add_argument("--summary", default="eval_summary.csv")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent.parent
    notes = json.loads((base / args.notes).read_text(encoding="utf-8"))
    ground_truth = json.loads((base / args.truth).read_text(encoding="utf-8"))

    gt_by_id = {g["note_id"]: g["record"] for g in ground_truth}

    extractor = LocalExtractor()
    per_note_results = []
    latencies = []

    print(f"Evaluating {len(notes)} notes...")

    for note in notes:
        note_id = note["note_id"]
        gt_record = gt_by_id.get(note_id)
        if gt_record is None:
            print(f"  WARNING: No ground truth for {note_id}, skipping")
            continue

        start = time.perf_counter()
        predicted = extractor.extract(note["note_text"], note.get("locale", "en"))
        latency_ms = (time.perf_counter() - start) * 1000

        metrics = evaluate_single(predicted, gt_record, latency_ms)
        metrics["note_id"] = note_id
        per_note_results.append(metrics)
        latencies.append(latency_ms)

    if not per_note_results:
        print("No results to evaluate!")
        return

    all_latencies = latencies
    all_latencies.sort()

    aggregate = {
        "total_notes": len(per_note_results),
        "medications_f1": round(mean(r["medications_f1"] for r in per_note_results), 4),
        "allergies_f1": round(mean(r["allergies_f1"] for r in per_note_results), 4),
        "problems_f1": round(mean(r["problems_f1"] for r in per_note_results), 4),
        "critical_recall_allergies": round(mean(r["critical_recall_allergies"] for r in per_note_results), 4),
        "critical_recall_medications": round(mean(r["critical_recall_medications"] for r in per_note_results), 4),
        "avg_completeness": round(mean(r["completeness_score"] for r in per_note_results), 4),
        "avg_latency_ms": round(mean(all_latencies), 2),
        "median_latency_ms": round(median(all_latencies), 2),
        "p95_latency_ms": round(all_latencies[int(len(all_latencies) * 0.95)], 2),
    }

    output = {
        "aggregate": aggregate,
        "per_note": per_note_results,
    }

    output_path = base / args.output
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nResults written to {args.output}")

    summary_path = base / args.summary
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in aggregate.items():
            writer.writerow([k, v])
    print(f"Summary written to {args.summary}")

    print("\n=== AGGREGATE METRICS ===")
    for k, v in aggregate.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
