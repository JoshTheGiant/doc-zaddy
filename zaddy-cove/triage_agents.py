from uagents import Agent, Context, Protocol, Model, Bureau
import subprocess
import re
import os

def run_metta(query):
    try:
        temp_script = "/mnt/c/Users/Danidebz/Documents/zaddy-cove/zaddy-cove/temp_query.metta"
        with open(temp_script, "w") as f:
            f.write(f"""
! include /app/symptom_reasoning.metta
{query}
""")
        result = subprocess.run(
            ["podman", "run", "--rm", "-v", "/mnt/c/Users/Danidebz/Documents/zaddy-cove/zaddy-cove:/app", "docker.io/trueagi/hyperon:latest", "metta", "/app/temp_query.metta"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if os.path.exists(temp_script):
            os.remove(temp_script)
        if result.returncode != 0:
            print(f"MeTTa error: {result.stderr}")
            return ["Unknown condition"]
        output_lines = result.stdout.strip().split("\n")
        diagnosis = output_lines[0].strip('[]') if output_lines else "Unknown condition"
        print(f"✅ MeTTa: {diagnosis}")
        return [diagnosis]
    except Exception as e:
        print(f"MeTTa failed: {e}")
        return ["Unknown condition"]

class SymptomMessage(Model):
    text: str

class DiagnosisMessage(Model):
    text: str

triage_agent = Agent(name="TriageAgent", port=8000)
action_agent = Agent(name="ActionAgent", port=8001)

triage_protocol = Protocol("TriageProtocol")

@triage_protocol.on_message(model=SymptomMessage)
async def handle_symptoms(ctx: Context, sender: str, msg: SymptomMessage):
    ctx.logger.info(f"Symptoms: {msg.text}")
    symptoms = re.findall(r'\w+', msg.text.lower())
    result = run_metta(f'!(diagnosis "{" ".join(symptoms)}")')
    diagnosis = result[0].strip('[]') if result else "Unknown condition"
    diagnosis_msg = DiagnosisMessage(text=f"Analyzed: {msg.text} -> {diagnosis}")
    await ctx.send(action_agent.address, diagnosis_msg)

@triage_protocol.on_message(model=DiagnosisMessage)
async def handle_action(ctx: Context, sender: str, msg: DiagnosisMessage):
    ctx.logger.info(f"Diagnosis: {msg.text}")
    ctx.logger.info("✅ Action complete")

triage_agent.include(triage_protocol)
action_agent.include(triage_protocol)

@triage_agent.on_event("startup")
async def send_test(ctx: Context):
    ctx.logger.info("🚀 Starting test")
    await ctx.send(triage_agent.address, SymptomMessage(text="fever and cough"))

bureau = Bureau()
bureau.add(triage_agent)
bureau.add(action_agent)

if __name__ == "__main__":
    bureau.run()