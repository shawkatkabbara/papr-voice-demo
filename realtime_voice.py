#!/usr/bin/env python3
"""
OpenAI Realtime API integration for voice input/output
"""

import asyncio
import json
import os
import base64
from typing import Callable, Optional
import websockets
from openai import AsyncOpenAI

class RealtimeVoiceClient:
    """Client for OpenAI Realtime API with voice capabilities"""

    def __init__(self, api_key: str, on_query: Optional[Callable] = None):
        self.api_key = api_key
        self.on_query = on_query  # Callback when user query is detected
        self.ws = None
        self.client = AsyncOpenAI(api_key=api_key)
        self.conversation_id = None

    async def connect(self):
        """Connect to OpenAI Realtime API via WebSocket"""
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

        self.ws = await websockets.connect(url, extra_headers=headers)
        print("✅ Connected to OpenAI Realtime API")

        # Configure session
        await self.send_config()

    async def send_config(self):
        """Configure the session with voice settings"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful AI assistant with access to the user's personal memories via PAPR. When answering questions, you'll receive relevant context from their memory database. Be conversational and helpful.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        await self.ws.send(json.dumps(config))

    async def send_audio(self, audio_data: bytes):
        """Send audio input to the API"""
        audio_b64 = base64.b64encode(audio_data).decode()
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        await self.ws.send(json.dumps(message))

    async def commit_audio(self):
        """Commit the audio buffer for processing"""
        message = {"type": "input_audio_buffer.commit"}
        await self.ws.send(json.dumps(message))

    async def send_text(self, text: str, context: Optional[str] = None):
        """Send text message with optional memory context"""
        content = text
        if context:
            content = f"[Context from user's memories:\n{context}\n]\n\nUser query: {text}"

        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": content
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(message))

        # Request response
        response_message = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
            }
        }
        await self.ws.send(json.dumps(response_message))

    async def listen(self):
        """Listen for responses from the API"""
        async for message in self.ws:
            data = json.loads(message)
            event_type = data.get("type")

            if event_type == "conversation.item.input_audio_transcription.completed":
                # User speech transcribed
                transcript = data.get("transcript", "")
                print(f"🎤 User said: {transcript}")

                # Trigger query callback
                if self.on_query and transcript:
                    await self.on_query(transcript)

            elif event_type == "response.audio_transcript.delta":
                # AI response text (streaming)
                delta = data.get("delta", "")
                print(f"🤖 AI: {delta}", end="", flush=True)

            elif event_type == "response.audio.delta":
                # AI response audio chunk
                audio_b64 = data.get("delta", "")
                # Here you would play the audio
                # For now, we'll skip audio playback in the demo

            elif event_type == "response.done":
                print("\n✅ Response complete")

            elif event_type == "error":
                print(f"❌ Error: {data.get('error', {})}")

    async def close(self):
        """Close the connection"""
        if self.ws:
            await self.ws.close()
            print("🔌 Disconnected from OpenAI Realtime API")


async def test_realtime():
    """Test the realtime voice client"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    async def on_query_handler(query: str):
        print(f"📝 Query detected: {query}")
        # Here you would trigger memory search

    client = RealtimeVoiceClient(api_key, on_query=on_query_handler)

    try:
        await client.connect()

        # Test with text
        await client.send_text("Hello! Tell me about my recent work.")

        # Listen for responses
        await client.listen()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_realtime())
