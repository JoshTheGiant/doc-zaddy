# patient_agent.py
from uagents import Agent, Context
from pydantic import BaseModel
import json, os, logging

logging.basicConfig(level=logging.INFO)

print("🧍 Starting Patient Agent...")

# === Message Schemas (must match diagnosis_agent) ===
class SymptomsMessage(BaseModel):
    symptoms: list[str]

class DiagnosisMessage(BaseModel):
    detected_diseases: list[str]
    treatments: dict[str, str]

# === Agent Configuration ===
patient_agent = Agent(
    name="patient_agent",
    seed="patient_agent_seed",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"]
)

# === Load Diagnosis Agent Address ===
REGISTRY_FILE = "agent_registry.json"
DIAGNOSIS_ADDR = None

if os.path.exists(REGISTRY_FILE):
    try:
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
            DIAGNOSIS_ADDR = data.get("diagnosis_agent")
            if DIAGNOSIS_ADDR:
                print(f"[patient_agent]: Found diagnosis address in registry: {DIAGNOSIS_ADDR}")
    except Exception as e:
        print(f"[patient_agent]: ⚠️ Error reading registry: {e}")

if not DIAGNOSIS_ADDR:
    print("[patient_agent]: ⚠️ No diagnosis address found. Please set agent_registry.json or FALLBACK_DIAG_ADDR.")

# === Helper: Load symptoms from file or fallback ===
def get_symptoms():
    json_path = "symptoms.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
                if "symptoms" in data:
                    return data["symptoms"]
        except Exception as e:
            print(f"[patient_agent]: ⚠️ Error loading symptoms file: {e}")

    # Manual or default fallback
    print("[patient_agent]: No valid symptoms.json found. Using default symptoms for test.")
    return ["fever", "headache"]

# === Handler for Diagnosis Response ===
@patient_agent.on_message(model=DiagnosisMessage)
async def handle_diagnosis(ctx: Context, sender: str, msg: DiagnosisMessage):
    ctx.logger.info("Diagnosis result received from diagnosis agent.")
    print("\n=== 🩺 Diagnosis Result ===")
    for disease, treatment in msg.treatments.items():
        print(f"• {disease}: {treatment}")
    print("✅ Interaction complete.\n")

# === Main Routine ===
@patient_agent.on_interval(period=10.0)
async def send_symptoms(ctx: Context):
    if not DIAGNOSIS_ADDR:
        ctx.logger.warning("Diagnosis address unavailable — skipping message.")
        return

    symptoms = get_symptoms()
    ctx.logger.info(f"Sending symptoms to diagnosis agent: {symptoms}")
    await ctx.send(DIAGNOSIS_ADDR, SymptomsMessage(symptoms=symptoms))

# === Run Agent ===
if __name__ == "__main__":
    print("[patient_agent]: Starting on port 8002")
    patient_agent.run()
