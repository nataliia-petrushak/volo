from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    AWS_SERVER_PUBLIC_KEY: str
    AWS_SERVER_SECRET_KEY: str
    AWS_SESSION_TOKEN: str
    AWS_PROFILE_NAME: str
    REGION_NAME: str
    MODEL_ID: str

    ELEVENLABS_ACCESS_KEY: str
    ELEVENLABS_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB"
    ELEVENLABS_MODEL_NAME: str = "eleven_multilingual_v2"

    model_config = SettingsConfigDict(env_file=".env")


settings = AppSettings()
