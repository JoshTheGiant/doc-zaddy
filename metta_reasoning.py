from hyperon import MeTTa

# Initialize MeTTa space once globally
metta = MeTTa()

# --- 1. Load Facts (Rewrite Rules) ---
metta_knowledge = """
(= (agent-type) "autonomous")
(= (capability) "reasoning")
"""
metta.run(metta_knowledge)

# --- 2. Query 1: Explicit Binding with 'let' ---
# 1. Bind the result of (agent-type) to $Type.
# 2. Bind the result of (capability) to $Cap.
# 3. Construct the list using the bound values.
result = metta.run("""
!(let $Type (agent-type)
    (let $Cap (capability)
        (list $Type $Cap)))
""")
print("MeTTa Results:", result)

# --- 3. Query 2: Simple Fact Retrieval ---
query_result = metta.run("!(agent-type)")
print("Agent Type Query:", query_result)