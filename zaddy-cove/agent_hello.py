import os
from uagents import Agent, Context, Model
from dotenv import load_dotenv

load_dotenv()

class Greeting(Model):
    message: str

hello_agent = Agent(
    name="hello_agent",
    seed="hello_agent_secret_seed",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"]
)

# Save agent address to file
with open("hello_agent_address.txt", "w") as f:
    f.write(hello_agent.address)

@hello_agent.on_message(model=Greeting)
async def handle_greeting(ctx: Context, sender: str, msg: Greeting):
    ctx.logger.info(f"📥 Received greeting from {sender}: {msg.message}")
    await ctx.send(sender, Greeting(message="Hello back from hello_agent!"))

if __name__ == "__main__":
    hello_agent.run()