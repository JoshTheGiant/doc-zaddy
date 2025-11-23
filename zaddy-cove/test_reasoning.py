#!/usr/bin/env python3
"""
test_reasoning.py — Stage 4.0 Interactive Reasoning Engine (Metta + Hybrid Logic)

- Prompts yes/no for 10 symptoms
- Injects facts into a fresh Atomspace
- Performs hybrid inference in Python (rules map symptom sets -> diseases)
- Asserts detected diseases into Atomspace and fetches treatments
- Prints colored summary + JSON-style export
"""

from hyperon import MeTTa
import json
import sys

# ANSI colors (safe fallback if terminal doesn't support)
CSI = "\033["
RESET = CSI + "0m"
BOLD = CSI + "1m"
GREEN = CSI + "32m"
YELLOW = CSI + "33m"
RED = CSI + "31m"
CYAN = CSI + "36m"
MAGENTA = CSI + "35m"

def color(text, code):
    return f"{code}{text}{RESET}"

# --- Symptom list (10) and mapping to display-friendly labels
SYMPTOMS = [
    ("fever", "Fever"),
    ("cough", "Cough"),
    ("fatigue", "Fatigue"),
    ("headache", "Headache"),
    ("sore_throat", "Sore throat"),
    ("nausea", "Nausea"),
    ("vomiting", "Vomiting"),
    ("diarrhea", "Diarrhea"),
    ("loss_of_taste", "Loss of taste/smell"),
    ("chills", "Chills"),
]

# --- Disease definitions (for hybrid inference)
# Each disease lists required POSITIVE symptoms (all must be present)
# and optional negative checks (like not having X). You can expand later.
DISEASE_RULES = {
    "flu": {
        "requires": ["fever", "cough", "chills"],
        "optional": ["fatigue", "headache", "sore_throat"],
        "treatment": "Rest, hydration, symptomatic care; see physician if severe"
    },
    "common_cold": {
        "requires": ["cough", "sore_throat"],
        "optional": ["headache"],
        "treatment": "Rest, fluids, warm fluids and lozenges"
    },
    "malaria": {
        "requires": ["fever", "fatigue", "chills"],
        "optional": ["headache", "vomiting"],
        "treatment": "Seek medical care: antimalarial therapy as prescribed"
    },
    "typhoid": {
        "requires": ["fever", "headache"],
        "optional": ["nausea", "diarrhea"],
        "treatment": "Antibiotics under medical supervision; hydration"
    },
    "covid19": {
        "requires": ["fever", "loss_of_taste"],
        "optional": ["cough", "fatigue", "sore_throat"],
        "treatment": "Isolation, symptomatic care; get tested and follow local guidance"
    },
    "food_poisoning": {
        "requires": ["nausea", "vomiting", "diarrhea"],
        "optional": ["fever"],
        "treatment": "Hydration, electrolyte replacement; seek care if severe"
    },
}

# --- Helper: prompt yes/no robustly
def ask_yes_no(prompt, default=False):
    try:
        while True:
            ans = input(prompt + " (y/n): ").strip().lower()
            if ans in ("y", "yes"):
                return True
            if ans in ("n", "no"):
                return False
            if ans == "" and default is not None:
                return default
            print("Please answer 'y' or 'n'.")
    except KeyboardInterrupt:
        print("\n" + color("User aborted.", RED))
        sys.exit(1)

# --- Flatten/normalize helper for Metta returns (keeps it robust) ---
def flatten_and_normalize(res):
    out = []
    def walk(x):
        if x is None:
            return
        if isinstance(x, (list, tuple)):
            for el in x:
                walk(el)
        else:
            s = str(x).strip()
            # remove surrounding quotes
            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                s = s[1:-1]
            # trim parentheses if present and consider tokens
            if s.startswith("(") and s.endswith(")"):
                inner = s[1:-1].strip()
                parts = inner.split()
                if parts:
                    # pick last token if meaningful
                    s = parts[-1].strip('"').strip("'")
            if s.lower() in ("true", "false", "None".lower()):
                return
            if s != "":
                out.append(s)
    walk(res)
    # unique preserving order
    seen = set()
    uniq = []
    for e in out:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq

# --- Main procedure ---
def main():
    print(color("=== ASI Agent: Interactive Diagnosis (Stage 4.0) ===", BOLD))
    print()

    # Initialize MeTTa and force a fresh atomspace
    metta = MeTTa()
    metta.run("!(clear-space! &self)")
    metta.run("!(bind &self &self)")

    # Inject static reasoning atoms (capabilities)
    metta.run('!(add-atom &self (= (agent-type autonomous) True))')
    metta.run('!(add-atom &self (= (capability reasoning) True))')
    metta.run('!(add-atom &self (= (capability data-access) True))')

    print(color("Interactive symptom intake — answer y/n for each symptom.\n", CYAN))

    # collect responses
    responses = {}
    for key, label in SYMPTOMS:
        resp = ask_yes_no(f"{label}?")
        responses[key] = resp
        # assert symptom into atomspace as (symptom "name") True
        # using quoted symptom names for robustness
        metta.run(f'!(add-atom &self (= (symptom "{key}") {str(resp)}))')

    print()
    print(color("🔍 Running hybrid inference...", MAGENTA))
    # Build normalized symptom list
    raw_sym = metta.run('!(match &self (= (symptom $S) True) $S)')
    symptoms = flatten_and_normalize(raw_sym)
    # The keys in DISEASE_RULES are names like 'fever' or 'loss_of_taste' etc.
    # make sure normalization uses our symptom keys (they already do)
    print("Active symptoms:", color(", ".join(symptoms) if symptoms else "None", YELLOW))
    print()

    # Hybrid inference
    detected = []
    reason_details = {}
    for disease, rule in DISEASE_RULES.items():
        requires = rule.get("requires", [])
        optional = rule.get("optional", [])
        # check required symptoms are all present
        if all(req in symptoms for req in requires):
            # disease considered present
            detected.append(disease)
            # capture which required/optional were seen
            seen_reqs = [r for r in requires if r in symptoms]
            seen_opts = [o for o in optional if o in symptoms]
            reason_details[disease] = {"matched_required": seen_reqs, "matched_optional": seen_opts}

            # assert into metta for downstream queries
            metta.run(f'!(add-reduct &self (= (disease {disease}) True))')

    # Print results (pretty)
    print(color("=== Diagnosis Summary ===", BOLD))
    if detected:
        for d in detected:
            t = DISEASE_RULES[d]["treatment"]
            print(color(f"• {d.upper()}", GREEN), "-", color(t, CYAN))
            # also try to pull treatment atom if present in metta (if you loaded treatments)
            t_fetch = metta.run(f'!(match &self (= (treatment {d}) $T) $T)')
            fetched = flatten_and_normalize(t_fetch)
            if fetched:
                print("  (KB treatment):", fetched[0])
            # show reason
            rd = reason_details.get(d, {})
            if rd:
                print("  Reason: required matched ->", rd["matched_required"], "; optional matched ->", rd["matched_optional"])
    else:
        print(color("No diseases detected from current symptom set.", YELLOW))

    # JSON-style export
    export = {
        "symptoms": {k: v for k, v in responses.items()},
        "detected_diseases": detected,
        "reason_details": reason_details,
    }
    print()
    print(color("=== JSON Summary ===", BOLD))
    print(json.dumps(export, indent=2))

    print()
    print(color("✅ Done — Stage 4.0 interactive run complete.", MAGENTA))

if __name__ == "__main__":
    main()
