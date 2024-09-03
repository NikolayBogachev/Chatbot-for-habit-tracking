from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    TOKEN: str
    URL: str

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '.env')


config = Settings()
