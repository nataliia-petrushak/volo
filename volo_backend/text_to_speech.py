import typing

from elevenlabs import stream
from elevenlabs.client import ElevenLabs, AsyncElevenLabs  # can also use async
from ollama import AsyncClient


class ElevenLabsProcessor:
    def __init__(self):
        self.client = ElevenLabs(api_key="sk_3696db65df41b93a7a83c3a71aef921ec78d9c1e9390b2d3")
        self.async_client = AsyncElevenLabs(api_key="sk_3696db65df41b93a7a83c3a71aef921ec78d9c1e9390b2d3")

    async def process(
        self,
        input: str,
    ) -> typing.AsyncIterator[str]:
        message = {
            "role": "user",
            "content": input
        }

        sentence = ""
        async for part in await AsyncClient().chat(
                model="llama3.2:1b", messages=[message], stream=True
        ):
            print(part["message"]["content"])
            
            sentence += part["message"]["content"]
            if part["message"]["content"] in ".!?":
                yield sentence
                sentence = ""

    async def to_sound(
        self,
        input: str,
        websocket,
        voice_id: str = "pNInz6obpgDQGcFmaJgB",
        model: str = "eleven_multilingual_v2"
    ) -> None:
        async for sentence in self.process(input=input):
            audio = self.client.generate(
                text=sentence,
                voice=voice_id,
                model=model,
                stream=True
            )
            audio_stream = stream(audio)
            await websocket.send_bytes(audio_stream)
    
    async def test_process(
        self,
        input: str,
    ) -> typing.AsyncIterator[str]:
        message = {
            "role": "user",
            "content": input
        }

        sentence = ""
        async for part in await AsyncClient().chat(
                model="llama3.2:1b", messages=[message], stream=True
        ):
            sentence += part["message"]["content"]
            if part["message"]["content"] in ".!?":
                yield sentence
                sentence = ""
    
    async def test_to_sound(
        self,
        input: str,
        websocket,
        voice_id: str = "pNInz6obpgDQGcFmaJgB",
        model: str = "eleven_multilingual_v2"
    ) -> None:
        audio = await self.async_client.generate(
            text=self.test_process(input),
            voice=voice_id,
            model=model,
            stream=True
        )

        async for audio_chunk in stream(audio):
            await websocket.send_bytes(audio_chunk)
