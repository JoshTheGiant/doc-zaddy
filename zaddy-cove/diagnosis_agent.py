#!/usr/bin/env python3
"""diagnose.py + FastAPI server

Enhanced CLI + API diagnosis tool using MeTTa reasoning.
"""

import argparse
import logging
import os
import re
from typing import Dict, List, Tuple

from hyperon import MeTTa
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("diagnose")

# ----------------- Helpers -----------------

def normalize_token(token: str) -> str:
    token = str(token or "").strip().lower()
    token = re.sub(r"\s+", "_", token)
    token = re.sub(r"[^\w\-_]", "", token)
    return token

SYNONYMS = {
    "fever": ["fever", "pyrexia", "high_temperature"],
    "cough": ["cough", "coughing"],
    "sore_throat": ["sore_throat", "throat_pain"],
    "shortness_of_breath": ["shortness_of_breath", "sob", "breathless"],
    "runny_nose": ["runny_nose", "rhinorrhea"],
}

SYN_MAP: Dict[str, str] = {}
for canonical, variants in SYNONYMS.items():
    for v in variants:
        SYN_MAP[v] = canonical

def apply_synonym(s: str) -> str:
    s = normalize_token(s)
    return SYN_MAP.get(s, s)

# ----------------- Safe MeTTa Wrapper -----------------

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

# ----------------- Domain logic -----------------

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
    return metta.match_values("(has-symptom $disease $symptom)", "$disease")

def disease_symptoms(disease: str) -> List[str]:
    pat = f"(has-symptom {normalize_token(disease)} $symptom)"
    return metta.match_values(pat, "$symptom")

def score_diseases(user_symptoms: List[str]) -> List[Tuple[str, int, int]]:
    user_norm = [apply_synonym(s) for s in user_symptoms]
    user_norm = [normalize_token(s) for s in user_norm if s]
    if not user_norm:
        return []

    diseases = set(all_diseases())
    scores: List[Tuple[str, int, int]] = []
    for d in diseases:
        db_syms = [normalize_token(s) for s in disease_symptoms(d)]
        if not db_syms:
            continue
        matched = sum(1 for us in user_norm if us in db_syms)
        scores.append((d, matched, len(db_syms)))

    scores.sort(key=lambda x: (x[1], (x[1] / x[2] if x[2] else 0), -x[2]), reverse=True)
    return scores

# ----------------- CLI -----------------

def main(kb_path: str):
    print("🤖 Starting Diagnosis Agent (CLI Mode)")
    loaded = load_kb_file(kb_path)
    if not loaded:
        log.info("Falling back to minimal KB.")
        fallback_kb = "(has-symptom flu fever) (has-symptom flu cough)"
        metta.load_kb_string(fallback_kb)

    test = metta.exists("(has-symptom flu fever)")
    log.info("[TEST] flu-fever exists: %s", test)

    print("Enter symptoms separated by space (type 'exit' to quit). Example: fever cough")
    try:
        while True:
            user = input("Symptoms: ").strip()
            if not user:
                continue
            if user.lower() in ("exit", "quit"):
                print("Goodbye")
                break
            tokens = user.split()
            scores = score_diseases(tokens)
            if not scores:
                print("No diagnosis could be produced.")
                continue
            print("Top candidates:")
            for disease, matched, total in scores[:10]:
                if matched == 0:
                    continue
                fraction = matched / total if total else 0
                print(f" - {disease}  (matched: {matched}/{total}, score: {fraction:.2f})")

    except KeyboardInterrupt:
        print("\nGoodbye")

# ----------------- FastAPI Web API -----------------

class SymptomInput(BaseModel):
    symptoms: List[str]

app = FastAPI(title="Diagnosis Agent API")

@app.on_event("startup")
def startup_event():
    kb_path = "reasoning.metta"
    if not load_kb_file(kb_path):
        log.warning("Using fallback KB.")
        metta.load_kb_string("(has-symptom flu fever) (has-symptom flu cough)")

@app.post("/diagnose")
def diagnose_api(data: SymptomInput):
    scores = score_diseases(data.symptoms)
    if not scores:
        return {"message": "No diagnosis could be produced."}
    return {
        "results": [
            {
                "disease": d,
                "matched": m,
                "total": t,
                "confidence": round(m / t, 2) if t else 0
            } for d, m, t in scores[:10] if m > 0
        ]
    }

# ----------------- Entrypoint -----------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kb', default='reasoning.metta', help='Path to reasoning.metta file')
    args = parser.parse_args()
    main(args.kb)
