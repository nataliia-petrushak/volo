import typing

from elevenlabs import stream
from elevenlabs.client import ElevenLabs

from core import settings
from services.bedrock import BedrockService


class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_ACCESS_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model = settings.ELEVENLABS_MODEL_NAME
        self.bedrock_service = BedrockService()

    async def process_user_input(self, user_input: str) -> typing.AsyncIterator[str]:
        sentence = ""

        async for chunk in self.bedrock_service.process_response(user_input):
            sentence += chunk
            if chunk in ".!?":
                yield sentence
                sentence = ""

    async def to_sound(self, user_input: str, websocket) -> None:
        async for sentence in self.process_user_input(user_input=user_input):
            audio = self.client.generate(
                text=sentence,
                voice=self.voice_id,
                model=self.model,
                stream=True
            )
            audio_stream = stream(audio)
            await websocket.send_bytes(audio_stream)
