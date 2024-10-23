import json
import typing

from elevenlabs import stream
from elevenlabs.client import ElevenLabs  # can also use async

from core import settings
from services.bedrock import BedrockService


class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_ACCESS_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model = settings.ELEVENLABS_MODEL_NAME
        self.bedrock_service = BedrockService()

    def process_user_input(self, user_input: str) -> typing.Generator:
        sentence = ""
        streaming_response = self.bedrock_service.send_request(user_input)

        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if "generation" in chunk:
                sentence += chunk["generation"]
                if chunk["generation"] in ".!?":
                    yield sentence
                    sentence = ""

    async def to_sound(self, user_input: str, websocket) -> None:
        for sentence in self.process_user_input(user_input=user_input):
            audio = self.client.generate(
                text=sentence,
                voice=self.voice_id,
                model=self.model,
                stream=True
            )
            audio_stream = stream(audio)
            await websocket.send_bytes(audio_stream)
