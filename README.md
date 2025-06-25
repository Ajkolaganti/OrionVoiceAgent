# Orion Voice Agent

A voice-enabled AI agent that uses LiveKit for real-time communication.

## Features

- Real-time voice interaction
- Integration with LiveKit for audio streaming
- Support for various AI services (OpenAI, Deepgram, etc.)

## Environment Variables

The following environment variables need to be set in your runtime environment:

- `LIVEKIT_URL` - Your LiveKit server URL
- `LIVEKIT_API_KEY` - Your LiveKit API key
- `LIVEKIT_API_SECRET` - Your LiveKit API secret
- AI service keys (OpenAI, Deepgram, etc.)

## Running with Docker

```bash
docker build -t orion-voice-agent .

# Run with environment variables
docker run -e LIVEKIT_URL=your_livekit_url \
           -e LIVEKIT_API_KEY=your_api_key \
           -e LIVEKIT_API_SECRET=your_api_secret \
           -e OPENAI_API_KEY=your_openai_key \
           -p 8000:8000 \
           orion-voice-agent
```

## Installation Without Docker

```bash
pip install -r requirements.txt
python agent.py
```

## Project Structure

- `agent.py` - Main application entry point
- `tools.py` - Helper functions and tools
- `prompts.py` - AI prompt templates
- `Dockerfile` - Container configuration