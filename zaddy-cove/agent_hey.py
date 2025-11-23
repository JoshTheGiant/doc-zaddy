import os

# Force uAgents server port before importing library
os.environ.setdefault("UAGENTS_SERVER_PORT", "8001")
os.environ.setdefault("UAGENTS_PORT", "8001")

from uagents import Agent, Context, Model
from dotenv import load_dotenv
import asyncio

# Load env
load_dotenv()

# Read hello agent address from file
try:
    with open("hello_agent_address.txt", "r") as f:
        HELLO_AGENT_ADDRESS = f.read().strip()
except FileNotFoundError:
    # Fallback to environment variable or default
    HELLO_AGENT_ADDRESS = os.getenv(
        "HELLO_AGENT_ADDRESS",
        "agent1qdp98dwvyjxua7xnzdscw3gqjpk5amx3f0scdt9z6pys7ra0t4zyjrkxmcy"
    )

class Greeting(Model):
    message: str

hey_agent = Agent(
    name="agent_hey",
    seed="agent_hey_secret_seed",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"]
)

@hey_agent.on_interval(period=5.0)
async def send_greeting(ctx: Context):
    ctx.logger.info(f"📤 Sending greeting to hello_agent ({HELLO_AGENT_ADDRESS})...")
    try:
        await ctx.send(HELLO_AGENT_ADDRESS, Greeting(message="Hello from agent_hey!"))
    except Exception as e:
        ctx.logger.error(f"Error sending greeting: {e}")

@hey_agent.on_message(model=Greeting)
async def handle_reply(ctx: Context, sender: str, msg: Greeting):
    ctx.logger.info(f"📥 Received reply from {sender}: {msg.message}")

if __name__ == "__main__":
    hey_agent.run()