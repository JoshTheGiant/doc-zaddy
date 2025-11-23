# debug_reasoning.py
import os
import traceback
from hyperon import MeTTa

def try_run(metta, cmd):
    """Utility to run and safely print MeTTa results."""
    print(f"\n--- metta.run({cmd!r}) ---")
    try:
        res = metta.run(cmd)
        print("RESULT:", res)
    except Exception:
        traceback.print_exc()

def main():
    cwd = os.getcwd()
    print("CWD:", cwd)

    kb_name = "reasoning.metta"
    kb_path = os.path.join(cwd, kb_name)
    print("KB path:", kb_path)
    print("KB exists?:", os.path.exists(kb_path))

    # Preview file contents
    if os.path.exists(kb_path):
        print("\n--- reasoning.metta CONTENT (first 4000 chars) ---")
        with open(kb_path, "r", encoding="utf-8", errors="replace") as f:
            print(f.read(4000))
        print("--- end file preview ---\n")

    # Initialize MeTTa
    metta = MeTTa()

    # === Register + Import the reasoning module properly ===
    register_cmd = f'!(register-module! "{kb_path}")'
    import_cmd = "!(import! &self reasoning)"
    try_run(metta, register_cmd)
    try_run(metta, import_cmd)

    # === Run your reasoning queries ===

    # 1. Agent Type + Reasoning Capability
    q1 = """
!(match &self (= (agent-type) $T)
   (match &self (= (capability "reasoning") True)
      (list $T True)))
"""
    try_run(metta, q1)

    # 2. Can diagnose patient?
    q2 = """
!(let $Reqs (match &self (= (requires "diagnose-patient" $Cap) True) $Cap)
   (let $GoalActive (match &self (= (goal "diagnose-patient") True) True)
      (let $AllCaps (all $Reqs (match &self (= (capability $Reqs) True) True))
         (and $GoalActive $AllCaps))))
"""
    try_run(metta, q2)

    # 3. Can optimize treatment?
    q3 = """
!(let $Reqs (match &self (= (requires "optimize-treatment" $Cap) True) $Cap)
   (let $GoalActive (match &self (= (goal "optimize-treatment") True) True)
      (let $AllCaps (all $Reqs (match &self (= (capability $Reqs) True) True))
         (and $GoalActive $AllCaps))))
"""
    try_run(metta, q3)

    # 4. List all facts to verify KB contents
    try_run(metta, '!(match &self (= $A $B) (list $A $B))')

if __name__ == "__main__":
    main()
