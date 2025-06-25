from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather,
    search_web,
    send_email,
    get_time,
    set_reminder,
    currency_converter,
    generate_password,
    get_joke,
    generate_qr_code,
    parse_git_repo_url,
    generate_code_snippet,
    get_stock_price,
    get_news,
    create_agenda,
    calculate_roi,
    ask_openai_coding,
    search_files,
    send_email_with_attachment
)
load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
            voice="Aoede",
            temperature=0.8,
        ),
            tools=[
                # Regular user tools
                get_weather,
                search_web,
                send_email,
                send_email_with_attachment,  # New email with attachment tool
                search_files,  # New file search tool
                get_time,
                set_reminder,
                currency_converter,
                generate_password,
                get_joke,
                generate_qr_code,
                
                # Developer tools
                ask_openai_coding,  # OpenAI coding tool for all coding questions
                parse_git_repo_url,
                generate_code_snippet,
                
                # Business professional tools
                get_stock_price,
                get_news,
                create_agenda,
                calculate_roi
            ],

        )
        


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))