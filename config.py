
import os

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        extra = "forbid"


config = Settings()
