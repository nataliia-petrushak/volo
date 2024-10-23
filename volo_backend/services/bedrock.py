import json
from typing import Generator

import boto3
from starlette.websockets import WebSocket

from core import settings


class BedrockService:
    def __init__(self) -> None:
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
            aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
            region_name=settings.REGION_NAME,
            aws_session_token=settings.AWS_SESSION_TOKEN
        )

    @staticmethod
    def form_request_body(user_input: str) -> dict:
        return {
            "prompt": (
                f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful assistant.<|eot_id|>
                <|start_header_id|>user<|end_header_id|>{user_input}<|eot_id|>
                <|start_header_id|>assistant<|end_header_id|>"""),
            "max_gen_len": 512,
            "temperature": 0.5
        }

    def send_request(self, user_input: str):
        request = self.form_request_body(user_input)
        return self.client.invoke_model_with_response_stream(
            modelId=settings.MODEL_ID,
            body=json.dumps(request)
        )

    def process_response(self, user_input: str) -> Generator:
        streaming_response = self.send_request(user_input)

        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if "generation" in chunk:
                yield chunk["generation"]

    async def stream_chat_response(self, websocket: WebSocket, user_input: str) -> None:
        """
        Streams chat response using Amazon Bedrock for real-time token streaming.
        """

        try:
            for chunk in self.process_response(user_input):
                await websocket.send_text(chunk)

        except Exception as e:
            print(f"Error: {str(e)}")
