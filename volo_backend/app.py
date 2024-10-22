import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from ollama import AsyncClient
import io
from faster_whisper import WhisperModel
from starlette.websockets import WebSocketDisconnect, WebSocketState

from text_to_speech import ElevenLabsProcessor
import logging

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

app = FastAPI()

# sio = socketio.AsyncServer(cors_allowed_origins="http://localhost:3000", async_mode='asgi')
# socket_app = socketio.ASGIApp(sio)
# app.mount("/", socket_app)

#
# @sio.on("connect")
# async def connect(sid, env):
#     print("New Client Connected to This id :" + " " + str(sid))
#     await sio.emit("send_msg", "Hello from Server")
#
#
# @sio.on("disconnect")
# async def disconnect(sid):
#     print("Client Disconnected: "+" "+str(sid))
#
#
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_chat_response(websocket: WebSocket, user_input: str):
    """
    Streams chat response using Ollama's AsyncClient for real-time token streaming.
    """
    # Prepare the message for Ollama's chat
    message = {
        "role": "user",
        "content": user_input
    }

    # Initiate streaming with Ollama's AsyncClient
    async for part in await AsyncClient().chat(
            model="llama3.2:1b", messages=[message], stream=True
    ):
        # Send each part of the message content as it's generated
        await websocket.send_text(part["message"]["content"])
        await asyncio.sleep(0)
        # Yield control to allow continuous streaming


@app.websocket("/text-to-text/ws")
async def text_to_text(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()

        # Stream the chat response back to the frontend
        await stream_chat_response(websocket, user_input)

        await websocket.send_text("[END]")  # Signal the end of streaming


@app.websocket("/text-to-speech/ws")
async def text_to_speech(websocket: WebSocket):
    eleven_labs = ElevenLabsProcessor()
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()

        # Stream the chat response back to the frontend
        await eleven_labs.to_sound(input=user_input, websocket=websocket)
        await websocket.send_text("[END]")


@app.websocket("/voice-to-voice/ws")
async def voice_to_voice(websocket: WebSocket):
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    result = ""
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_bytes()
            segments, info = model.transcribe(io.BytesIO(message), language="en", beam_size=3)
            for segment in segments:
                result += segment.text
        except WebSocketDisconnect:
            break
    print(result)




if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
