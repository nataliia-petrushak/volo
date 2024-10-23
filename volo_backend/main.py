import io
import uvicorn
import logging

from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from services import ElevenLabsService, BedrockService


logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/text-to-text/ws")
async def text_to_text(websocket: WebSocket, bedrock_service: BedrockService = Depends(BedrockService)):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()

        # Stream the chat response back to the frontend
        await bedrock_service.stream_chat_response(websocket, user_input)
        await websocket.send_text("[END]")  # Signal the end of streaming


@app.websocket("/text-to-speech/ws")
async def text_to_speech(
        websocket: WebSocket, eleven_labs: ElevenLabsService = Depends(ElevenLabsService)
) -> None:
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()

        # Stream the chat response back to the frontend
        await eleven_labs.to_sound(user_input=user_input, websocket=websocket)
        await websocket.send_text("[END]")


@app.websocket("/voice-to-voice/ws")
async def voice_to_voice(websocket: WebSocket):
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    result = ""
    await websocket.accept()
    # while True:
    # try:
    print("start receiving")
    message = await websocket.receive_bytes()
    print("received")
    segments, info = model.transcribe(io.BytesIO(message), language="en", beam_size=3)
    for segment in segments:
        result += segment.text
    # except WebSocketDisconnect:
    #     break
    print(result)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
