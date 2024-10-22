from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    AWS_SERVER_PUBLIC_KEY: str
    AWS_SERVER_SECRET_KEY: str
    REGION_NAME: str
    MODEL_ID: str
    AWS_SESSION_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env")


settings = AppSettings()
