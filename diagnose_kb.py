from hyperon import MeTTa

m = MeTTa()
m.run('!(include reasoning.metta)')

print("=== ALL FACTS IN KB ===")
dump = m.run('!(match &self $pattern $pattern)')
for fact in dump:
    print(fact)
