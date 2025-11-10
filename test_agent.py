import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.plugins import silero, cartesia, groq, deepgram

# Import enhanced functionality
from enhanced_agents import setup_filler_filtering, FillerWordConfig

load_dotenv()

# Setup filler word filtering BEFORE creating agents
config = setup_filler_filtering()

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    # Create session with standard SDK
    session = agents.AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2-general", language="en-US"),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=deepgram.TTS(),
    )
    
    # Apply filler word config to session options
    config.apply_to_options(session.options)
    
    agent = agents.Agent(
        instructions="You are a helpful assistant. Keep responses brief.",
    )
    
    await session.start(agent, room=ctx.room)
    print("Agent running with filler word filtering")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))