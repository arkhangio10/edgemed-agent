#!/usr/bin/env python3
"""Generate deterministic synthetic clinical notes with ground-truth structured JSON.

Usage:
    python scripts/generate_synth_dataset.py [--count 50] [--seed 42]

Outputs:
    data/synthetic_notes.json   — list of {note_id, note_text, locale}
    data/ground_truth.json      — list of {note_id, record: ClinicalRecord, flags}
    data/sample_notes/          — 3 representative .txt files for the demo UI
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

SEED = 42

# ── Building blocks ──────────────────────────────────────────────────

FIRST_NAMES = ["Maria", "James", "Sofia", "Ahmed", "Yuki", "Priya", "Carlos",
               "Emily", "David", "Fatima", "Wei", "Sarah", "Juan", "Aisha"]

LAST_NAMES = ["Garcia", "Smith", "Patel", "Kim", "Johnson", "Lee", "Brown",
              "Williams", "Chen", "Martinez", "Lopez", "Singh", "Wilson"]

CHIEF_COMPLAINTS = [
    "chest pain", "shortness of breath", "headache", "abdominal pain",
    "back pain", "cough and fever", "dizziness", "joint pain",
    "fatigue", "sore throat", "skin rash", "anxiety",
    "diabetes follow-up", "hypertension follow-up", "medication review",
    "annual physical", "post-surgical follow-up", "pregnancy check-up",
]

MEDICATIONS_POOL = [
    {"name": "Lisinopril", "dose": "10mg", "frequency": "daily", "route": "PO"},
    {"name": "Metformin", "dose": "500mg", "frequency": "BID", "route": "PO"},
    {"name": "Atorvastatin", "dose": "40mg", "frequency": "daily", "route": "PO"},
    {"name": "Omeprazole", "dose": "20mg", "frequency": "daily", "route": "PO"},
    {"name": "Amlodipine", "dose": "5mg", "frequency": "daily", "route": "PO"},
    {"name": "Metoprolol", "dose": "25mg", "frequency": "BID", "route": "PO"},
    {"name": "Albuterol", "dose": "2 puffs", "frequency": "PRN", "route": "inhaled"},
    {"name": "Prednisone", "dose": "10mg", "frequency": "daily", "route": "PO"},
    {"name": "Gabapentin", "dose": "300mg", "frequency": "TID", "route": "PO"},
    {"name": "Sertraline", "dose": "50mg", "frequency": "daily", "route": "PO"},
    {"name": "Aspirin", "dose": "81mg", "frequency": "daily", "route": "PO"},
    {"name": "Glipizide", "dose": "5mg", "frequency": "daily", "route": "PO"},
    {"name": "Ibuprofen", "dose": "400mg", "frequency": "TID", "route": "PO"},
    {"name": "Acetaminophen", "dose": "500mg", "frequency": "PRN", "route": "PO"},
]

ALLERGIES_POOL = [
    {"substance": "Penicillin", "reaction": "rash", "severity": "moderate"},
    {"substance": "Sulfa", "reaction": "hives", "severity": "moderate"},
    {"substance": "Codeine", "reaction": "nausea and vomiting", "severity": "mild"},
    {"substance": "Latex", "reaction": "contact dermatitis", "severity": "mild"},
    {"substance": "Aspirin", "reaction": "bronchospasm", "severity": "severe"},
    {"substance": "Iodine contrast", "reaction": "anaphylaxis", "severity": "severe"},
    {"substance": "Amoxicillin", "reaction": "rash", "severity": "moderate"},
    {"substance": "NSAIDs", "reaction": "GI bleeding", "severity": "moderate"},
]

PROBLEMS_POOL = [
    {"description": "Type 2 diabetes mellitus", "status": "chronic"},
    {"description": "Essential hypertension", "status": "chronic"},
    {"description": "Hyperlipidemia", "status": "chronic"},
    {"description": "Acute coronary syndrome", "status": "active"},
    {"description": "Community-acquired pneumonia", "status": "active"},
    {"description": "Generalized anxiety disorder", "status": "chronic"},
    {"description": "Chronic low back pain", "status": "chronic"},
    {"description": "GERD", "status": "chronic"},
    {"description": "Migraine headache", "status": "active"},
    {"description": "Urinary tract infection", "status": "active"},
    {"description": "Osteoarthritis", "status": "chronic"},
    {"description": "Major depressive disorder", "status": "active"},
    {"description": "Asthma exacerbation", "status": "active"},
    {"description": "Iron deficiency anemia", "status": "active"},
]

RED_FLAG_SCENARIOS = [
    (["chest pain"], ["Chest pain"]),
    (["shortness of breath"], ["Shortness of breath"]),
    (["severe headache", "worst headache of life"], ["Severe pain"]),
]

PLANS_POOL = [
    "Continue current medications, follow up in 3 months",
    "Order CBC, CMP, lipid panel. Follow up to review results in 2 weeks",
    "Start physical therapy, reassess in 4 weeks",
    "Increase {med} dosage, recheck labs in 6 weeks",
    "Refer to {specialty} for further evaluation",
    "EKG stat, troponins q6h, cardiology consult",
    "Start antibiotics ({med}), follow up in 3 days if not improving",
    "CT scan of {area}, follow up with results",
]

SPECIALTIES = ["cardiology", "endocrinology", "orthopedics", "neurology",
               "gastroenterology", "pulmonology", "psychiatry"]
AREAS = ["abdomen", "chest", "head", "lumbar spine", "pelvis"]

FOLLOW_UPS = [
    "Return in 2 weeks",
    "Return in 1 month",
    "Return in 3 months",
    "Follow up in 6 weeks",
    "Reassess in 6 hours",
    "Return in 2 weeks for medication review",
]


def generate_note(rng: random.Random, note_idx: int) -> tuple[dict, dict]:
    """Generate one synthetic note and its ground truth."""
    note_id = f"synth-{note_idx:04d}"
    age = rng.randint(18, 85)
    sex = rng.choice(["male", "female"])
    cc = rng.choice(CHIEF_COMPLAINTS)

    num_meds = rng.randint(0, 5)
    meds = rng.sample(MEDICATIONS_POOL, min(num_meds, len(MEDICATIONS_POOL)))

    use_nkda = rng.random() < 0.3
    if use_nkda:
        allergies_gt = [{"substance": "NKDA", "reaction": None, "severity": None}]
    else:
        num_allergies = rng.randint(0, 3)
        allergies_gt = rng.sample(ALLERGIES_POOL, min(num_allergies, len(ALLERGIES_POOL)))

    num_problems = rng.randint(1, 4)
    problems = rng.sample(PROBLEMS_POOL, min(num_problems, len(PROBLEMS_POOL)))

    red_flags: list[str] = []
    for triggers, flags in RED_FLAG_SCENARIOS:
        if any(t in cc.lower() for t in triggers):
            red_flags = flags
            break

    plan_tmpl = rng.choice(PLANS_POOL)
    plan = plan_tmpl.format(
        med=meds[0]["name"] if meds else "medication",
        specialty=rng.choice(SPECIALTIES),
        area=rng.choice(AREAS),
    )

    follow_up = rng.choice(FOLLOW_UPS)

    hpi = (
        f"{age}yo {sex} presents with {cc}. "
        f"Symptoms started {rng.randint(1, 14)} days ago. "
        f"Patient reports {rng.choice(['gradual onset', 'sudden onset', 'intermittent symptoms'])}. "
        f"{'No significant past medical history.' if rng.random() < 0.2 else 'Past medical history includes ' + problems[0]['description'] + '.'}"
    )

    summary = (
        f"Patient is a {age}-year-old {sex} presenting with {cc}. "
        f"Currently on {len(meds)} medications. "
        f"{'No known allergies.' if use_nkda else f'{len(allergies_gt)} documented allergies.'}"
    )

    # ── Build note text ──
    lines = [f"CC: {cc.title()}"]
    lines.append(f"HPI: {hpi}")

    if meds:
        med_strs = [f"{m['name']} {m['dose']} {m['frequency']}" for m in meds]
        lines.append(f"Medications: {', '.join(med_strs)}")
    else:
        lines.append("Medications: None")

    if use_nkda:
        lines.append("Allergies: NKDA")
    elif allergies_gt:
        allergy_strs = []
        for a in allergies_gt:
            s = a["substance"]
            if a.get("reaction"):
                s += f" ({a['reaction']})"
            allergy_strs.append(s)
        lines.append(f"Allergies: {', '.join(allergy_strs)}")
    else:
        lines.append("Allergies: None documented")

    prob_strs = [f"{i+1}. {p['description']}" for i, p in enumerate(problems)]
    lines.append(f"Assessment: {' '.join(prob_strs)}")
    lines.append(f"Plan: {plan}")
    lines.append(f"Follow-up: {follow_up}")

    note_text = "\n".join(lines)

    note_obj = {
        "note_id": note_id,
        "note_text": note_text,
        "locale": "en",
    }

    gt_obj = {
        "note_id": note_id,
        "record": {
            "chief_complaint": cc.title(),
            "hpi": hpi,
            "assessment": problems,
            "plan": plan,
            "medications": meds,
            "allergies": allergies_gt,
            "red_flags": red_flags,
            "follow_up": follow_up,
            "patient_summary_plain_language": summary,
        },
    }

    return note_obj, gt_obj


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic clinical notes")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "sample_notes").mkdir(exist_ok=True)

    notes = []
    ground_truths = []

    for i in range(args.count):
        note, gt = generate_note(rng, i)
        notes.append(note)
        ground_truths.append(gt)

    (data_dir / "synthetic_notes.json").write_text(
        json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (data_dir / "ground_truth.json").write_text(
        json.dumps(ground_truths, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for idx in range(min(3, len(notes))):
        (data_dir / "sample_notes" / f"sample_{idx+1:02d}.txt").write_text(
            notes[idx]["note_text"], encoding="utf-8"
        )

    print(f"Generated {len(notes)} synthetic notes (seed={args.seed})")
    print(f"  -> data/synthetic_notes.json")
    print(f"  -> data/ground_truth.json")
    print(f"  -> data/sample_notes/ ({min(3, len(notes))} samples)")


if __name__ == "__main__":
    main()
