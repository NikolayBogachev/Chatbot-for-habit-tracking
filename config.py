
import os

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    URL_DB: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    URL: str
    REFRESH_TOKEN_EXPIRE_DAYS: int

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        extra = "forbid"


config = Settings()
