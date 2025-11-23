# debug_diagnosis.py
import os, traceback
from hyperon import MeTTa

def try_run(m, cmd, label=None):
    if label: print(f"\n--- {label} ---")
    print(f"metta.run({cmd!r})")
    try:
        r = m.run(cmd)
        print("RESULT:", r)
        return r
    except Exception as e:
        print("EXCEPTION:", e)
        traceback.print_exc()
        return None

def main():
    cwd = os.getcwd()
    print("CWD:", cwd)
    reasoning_path = os.path.join(cwd, "reasoning.metta")
    diag_path = os.path.join(cwd, "diagnosis.metta")

    print("\nPaths:")
    print(" - reasoning.metta:", reasoning_path, "exists?", os.path.exists(reasoning_path))
    print(" - diagnosis.metta:", diag_path, "exists?", os.path.exists(diag_path))

    if os.path.exists(diag_path):
        print("\n--- diagnosis.metta (first 4000 chars) ---")
        with open(diag_path, "r", encoding="utf-8", errors="replace") as f:
            print(f.read(4000))
        print("--- end file preview ---\n")
    else:
        print("\nERROR: diagnosis.metta not found. Create it first.\n")
        return

    m = MeTTa()

    # Load reasoning.metta (existing core)
    print("\n--- Register + import reasoning.metta ---")
    try_run(m, f'!(register-module! "{reasoning_path}")', "register reasoning")
    try_run(m, "!(import! &self reasoning)", "import reasoning")

    # Quick check: does capability reasoning exist?
    try_run(m, '!(match &self (= (capability "reasoning") True) True)', "check capability 'reasoning'")

    # Attempt 1: register + import diagnosis module
    print("\n--- Register + import diagnosis.metta (attempt) ---")
    try_run(m, f'!(register-module! "{diag_path}")', "register diagnosis")
    try_run(m, "!(import! &self diagnosis)", "import diagnosis")

    # Focused queries after import attempt
    try_run(m, '!(match &self (= (symptom $S) True) $S)', "match symptoms")
    try_run(m, '!(match &self (= (disease-rule $D) $R) (list $D $R))', "list disease-rule atoms")
    try_run(m, '!(match &self (= (disease "flu") $X) $X)', "disease flu raw")
    try_run(m, '!(match &self (= (disease "cold") $X) $X)', "disease cold raw")
    try_run(m, '!(match &self (= (treatment "flu") $T) $T)', "treatment flu")

    # Try evaluating the disease-rule via eval (directly in MeTTa)
    try_run(m, '!(eval (disease-rule "flu"))', "eval(disease-rule \"flu\") direct")
    try_run(m, '!(match &self (= (disease-rule "flu") $R) $R)', "disease-rule flu via match")

    # If import didn't add atoms, try injecting file contents directly
    print("\n--- Now: inject diagnosis.metta contents directly into &self (fallback) ---")
    with open(diag_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    # wrap content in a single metta.run call
    print("\nInjecting content into MeTTa atomspace (metta.run of file contents)...")
    try:
        res = m.run(content)
        print("RESULT of direct injection:", res)
    except Exception as e:
        print("EXCEPTION during direct injection:", e)
        traceback.print_exc()

    # Re-run focused queries after injection
    print("\n--- Focused queries after direct injection ---")
    try_run(m, '!(match &self (= (symptom $S) True) $S)', "match symptoms (after inject)")
    try_run(m, '!(match &self (= (disease-rule $D) $R) (list $D $R))', "list disease-rule atoms (after inject)")
    try_run(m, '!(eval (disease-rule "flu"))', "eval(disease-rule \"flu\") (after inject)")
    try_run(m, '!(match &self (= (disease "flu") $X) $X)', "disease flu raw (after inject)")
    try_run(m, '!(match &self (= (treatment "flu") $T) $T)', "treatment flu (after inject)")

    # Final: try the high-level diagnosis query you use in script
    print("\n--- Final: high-level disease match (after inject) ---")
    try_run(m, '!(match &self (= (disease $D) True) $D)', "match (disease $D) True (after inject)")

if __name__ == "__main__":
    main()
