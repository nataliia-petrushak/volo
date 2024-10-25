from typing import AsyncIterator

from starlette.websockets import WebSocket
from langchain_aws import BedrockLLM
from langchain_aws.chat_models import bedrock

from core import settings


class BedrockService:
    def __init__(self) -> None:
        self.client = BedrockLLM(
            credentials_profile_name=settings.AWS_PROFILE_NAME,
            aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
            aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            model_id=settings.MODEL_ID,
            streaming=True,
            region=settings.REGION_NAME,
            model_kwargs={"temperature": 0.5}
        )

    @staticmethod
    def form_request_body(user_input: str) -> list:
        system_message = bedrock.SystemMessage(content="You are a helpful assistant.")
        human_message = bedrock.HumanMessage(content=user_input)
        return [system_message, human_message]

    async def process_response(self, user_input: str) -> AsyncIterator[str]:
        format_user_input = self.form_request_body(user_input)
        request = bedrock.convert_messages_to_prompt_llama3(format_user_input)
        async for event in self.client.astream(request):
            yield event

    async def stream_chat_response(self, websocket: WebSocket, user_input: str) -> None:
        """
        Streams chat response using Amazon Bedrock for real-time token streaming.
        """

        try:
            async for chunk in self.process_response(user_input):
                await websocket.send_text(chunk)

        except Exception as e:
            print(f"Error: {str(e)}")
