from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AUTH_SERVICE_URL: str
    USER_SERVICE_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()