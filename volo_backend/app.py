from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import io
import boto3
from faster_whisper import WhisperModel
from starlette.websockets import WebSocketDisconnect, WebSocketState
import logging
import json

from text_to_speech import ElevenLabsProcessor
from config import settings

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

app = FastAPI()

bedrock_client = boto3.client('bedrock-runtime', 
                      aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY, 
                      aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY, 
                      region_name=settings.REGION_NAME,
                      aws_session_token=settings.AWS_SESSION_TOKEN
                      )

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
    Streams chat response using Amazon Bedrock for real-time token streaming.
    """
    request_body = {
        "prompt": ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful assistant.<|eot_id|>"
                   f"<|start_header_id|>user<|end_header_id|>{user_input}<|eot_id|>"
                   "<|start_header_id|>assistant<|end_header_id|>"),
        "max_gen_len": 128,
        "temperature": 0.5
    }
    
    try:
        streaming_response  = bedrock_client.invoke_model_with_response_stream(
                modelId=settings.MODEL_ID,
                body=json.dumps(request_body)
            )
        
        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if "generation" in chunk:
                await websocket.send_text(chunk["generation"])
    except Exception as e:
        print(f"Error: {str(e)}")


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
