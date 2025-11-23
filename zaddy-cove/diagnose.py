#!/usr/bin/env python3
"""
diagnose.py — robust diagnosis CLI with weighted scoring, synonyms, and concise explanations.

Usage:
    python3 diagnose.py --kb reasoning.metta [--top N] [--explain]

Flags:
    --kb PATH     Path to reasoning.metta (default: reasoning.metta)
    --top N       Show top N candidates (default: 5)
    --explain     Show concise differences between top candidate and others
"""

import argparse
import logging
import os
import re
import math
from typing import Dict, List, Tuple

from hyperon import MeTTa

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("diagnose")

# ---------------- Helpers & Synonyms ----------------

def normalize_token(token: str) -> str:
    token = str(token or "").strip().lower()
    token = re.sub(r"\s+", "_", token)
    token = re.sub(r"[^\w\-_]", "", token)
    return token

# Extended synonyms map — expand as you see fit
SYNONYMS = {
    "fever": ["fever", "pyrexia", "high_temperature", "temp"],
    "cough": ["cough", "coughing"],
    "sore_throat": ["sore_throat", "throat_pain"],
    "runny_nose": ["runny_nose", "rhinorrhea", "runny"],
    "shortness_of_breath": ["shortness_of_breath", "sob", "breathless"],
    "fatigue": ["fatigue", "tiredness", "lethargy"],
    "nausea": ["nausea", "queasy"],
    "vomiting": ["vomiting", "throwing_up", "emesis"],
    "diarrhea": ["diarrhea", "loose_stool"],
    "abdominal_pain": ["abdominal_pain", "stomach_pain", "belly_pain"],
    "headache": ["headache", "head_pain"],
    "rash": ["rash", "skin_rash"],
    "chest_pain": ["chest_pain", "pressure_chest"],
    "joint_pain": ["joint_pain", "arthralgia"],
    "dizziness": ["dizziness", "lightheadedness"],
    "feverish": ["feverish", "fever"],
    "bleeding": ["bleeding", "hemorrhage", "bloody"],
    "discharge": ["discharge", "vaginal_discharge"],
    "eye_pain": ["eye_pain", "ocular_pain"],
}

# invert synonyms => canonical form map
SYN_MAP: Dict[str, str] = {}
for canonical, variants in SYNONYMS.items():
    for v in variants:
        SYN_MAP[normalize_token(v)] = normalize_token(canonical)

def apply_synonym(s: str) -> str:
    s2 = normalize_token(s)
    return SYN_MAP.get(s2, s2)

# ---------------- Safe MeTTa wrapper ----------------

class SafeMeTTa:
    def __init__(self):
        self.metta = MeTTa()

    def load_kb_string(self, s: str) -> bool:
        try:
            self.metta.run(s)
            log.info("KB loaded into MeTTa")
            return True
        except Exception as e:
            log.exception("Failed to load KB string: %s", e)
            return False

    def _safe_run(self, query: str):
        try:
            return self.metta.run(query)
        except Exception as e:
            log.exception("metta.run failed for query: %s", query)
            return None

    def match_values(self, pattern: str, template: str = "$res") -> List[str]:
        q = f"!(match &self {pattern} {template})"
        raw = self._safe_run(q)
        vals: List[str] = []
        if not raw:
            return vals
        for row in raw:
            if not row:
                continue
            for atom in row:
                s = str(atom).strip()
                if not s or s.startswith("$"):
                    continue
                vals.append(s)
        return vals

    def exists(self, pattern: str) -> bool:
        q = f"!(match &self {pattern} $res)"
        raw = self._safe_run(q)
        if not raw:
            return False
        for row in raw:
            if row:
                return True
        return False

# ---------------- Domain: load & index KB ----------------

metta = SafeMeTTa()

def load_kb_file(path: str) -> bool:
    if not os.path.exists(path):
        log.warning("KB file not found: %s", path)
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return metta.load_kb_string(content)
    except Exception as e:
        log.exception("Failed to read KB file: %s", e)
        return False

def all_diseases() -> List[str]:
    return list(set(metta.match_values("(has-symptom $disease $symptom)", "$disease")))

def disease_symptoms(disease: str) -> List[str]:
    pat = f"(has-symptom {normalize_token(disease)} $symptom)"
    return [normalize_token(s) for s in metta.match_values(pat, "$symptom")]

# Build symptom frequency map (used for weighting)
def symptom_frequencies(diseases: List[str]) -> Dict[str, int]:
    freq: Dict[str, int] = {}
    for d in diseases:
        syms = disease_symptoms(d)
        for s in set(syms):
            freq[s] = freq.get(s, 0) + 1
    return freq

# ---------------- Scoring functions ----------------

def compute_weighted_scores(user_symptoms_raw: List[str]) -> List[Tuple[str, float, int, int]]:
    """
    Returns list of tuples:
      (disease, weighted_score_fraction, matched_count, total_count)

    weighted_score_fraction = (sum weights for matched symptoms) / (sum weights for all disease symptoms)
    where weight(s) = log(1 + total_diseases / freq(s))  (rare symptoms higher weight)
    """
    user_norm = [apply_synonym(s) for s in user_symptoms_raw]
    user_norm = [normalize_token(s) for s in user_norm if s]
    if not user_norm:
        return []

    diseases = all_diseases()
    freq = symptom_frequencies(diseases)
    total_diseases = len(diseases) if diseases else 1

    def weight(sym: str) -> float:
        # inverse-frequency style weight (smaller freq -> larger weight)
        f = freq.get(sym, 1)
        return math.log(1.0 + (total_diseases / f))

    scored = []
    for d in diseases:
        db_syms = disease_symptoms(d)
        if not db_syms:
            continue
        db_unique = list(dict.fromkeys(db_syms))  # preserve order but unique
        matched = 0
        matched_weight = 0.0
        total_weight = 0.0
        for s in db_unique:
            w = weight(s)
            total_weight += w
            if s in user_norm:
                matched += 1
                matched_weight += w
        frac = (matched_weight / total_weight) if total_weight > 0 else 0.0
        scored.append((d, frac, matched, len(db_unique)))
    # Sort by weighted fraction desc, then matched count desc, then smaller total_count
    scored.sort(key=lambda x: (x[1], x[2], -x[3]), reverse=True)
    return scored

# ---------------- Explanation mode (concise diffs) ----------------

def concise_diff(top_disease: str, other_disease: str, max_items: int = 3) -> str:
    top_syms = set(disease_symptoms(top_disease))
    other_syms = set(disease_symptoms(other_disease))
    common = sorted(list(top_syms & other_syms))
    only_top = sorted(list(top_syms - other_syms))
    only_other = sorted(list(other_syms - top_syms))

    parts = []
    if common:
        parts.append(f"shares {min(len(common), max_items)} symptom(s): {', '.join(common[:max_items])}")
    if only_top:
        parts.append(f"{top_disease} unique: {', '.join(only_top[:max_items])}")
    if only_other:
        parts.append(f"{other_disease} unique: {', '.join(only_other[:max_items])}")
    if not parts:
        return "no key symptom differences captured."
    return " | ".join(parts)

# ---------------- CLI ----------------

def main(kb_path: str, top_n: int = 5, explain: bool = False):
    print("🤖 Starting Diagnosis Agent (weighted matching + synonyms) — Demo only")
    loaded = load_kb_file(kb_path)
    if not loaded:
        log.info("Falling back to a small embedded KB")
        metta.load_kb_string("(has-symptom flu fever) (has-symptom flu cough) (has-symptom flu fatigue)")

    diseases = all_diseases()
    log.info("[INFO] diseases loaded: %d", len(diseases))

    print("Enter symptoms separated by space (type 'exit' to quit). Example: fever cough\n")
    try:
        while True:
            user = input("Symptoms: ").strip()
            if not user:
                continue
            if user.lower() in ("exit", "quit"):
                print("Goodbye")
                break

            tokens = user.split()
            scored = compute_weighted_scores(tokens)
            if not scored:
                print("No matches (check spelling / try synonyms).")
                continue

            # present top N where matched_count > 0
            presented = 0
            print("\nTop candidates:")
            for disease, frac, matched, total in scored:
                if presented >= top_n:
                    break
                if matched == 0:
                    continue
                # show both weighted fraction and simple matched fraction
                simple_frac = matched / total if total else 0.0
                print(f" - {disease}  (matched: {matched}/{total}, weighted_score: {frac:.2f}, simple_score: {simple_frac:.2f})")
                presented += 1

            if presented == 0:
                print("No disease shares your symptoms directly. Try adding more symptoms or synonyms.")
                continue

            # concise explanation/differences vs top candidate
            if explain and presented > 0:
                top = None
                # find first shown disease as top
                for disease, frac, matched, total in scored:
                    if matched > 0:
                        top = disease
                        break
                if top:
                    print("\nConcise differences vs top candidate:")
                    shown = 0
                    for disease, frac, matched, total in scored:
                        if disease == top:
                            continue
                        if shown >= (top_n - 1):
                            break
                        if matched == 0:
                            continue
                        diff = concise_diff(top, disease, max_items=3)
                        print(f" - vs {disease}: {diff}")
                        shown += 1

            print("")  # blank line between queries

    except KeyboardInterrupt:
        print("\nGoodbye")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", default="reasoning.metta", help="Path to reasoning.metta file")
    parser.add_argument("--top", type=int, default=5, help="How many top candidates to show")
    parser.add_argument("--explain", action="store_true", help="Show concise differences between top candidate and others")
    args = parser.parse_args()
    main(kb_path=args.kb, top_n=args.top, explain=args.explain)
