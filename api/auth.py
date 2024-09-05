from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import config


class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return cls.pwd_context.hash(password)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt

    @classmethod
    def decode_access_token(cls, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            return payload
        except JWTError:
            return None

    @classmethod
    def create_refresh_token(cls, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt

    @classmethod
    def decode_refresh_token(cls, token: str) -> Optional[dict]:
        """
        Декодирует refresh token.

        **Параметры**:
        - `token` (str): Токен, который нужно декодировать.

        **Возвращает**:
        - `dict`: Полезная нагрузка токена, если декодирование успешно.
        - `None`: Если токен недействителен или истёк.
        """
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            return payload
        except JWTError:
            return None


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)
#
#
# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)
#
#
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
#     return encoded_jwt
#
#
# def decode_access_token(token: str) -> Optional[dict]:
#     try:
#         payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
#         return payload
#     except JWTError:
#         return None
#
#
# def create_refresh_token(data: dict, expires_delta: timedelta):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + expires_delta
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
#     return encoded_jwt
#
#
# def decode_refresh_token(token: str) -> Optional[dict]:
#     """
#     Декодирует refresh token.
#
#     **Параметры**:
#     - `token` (str): Токен, который нужно декодировать.
#
#     **Возвращает**:
#     - `dict`: Полезная нагрузка токена, если декодирование успешно.
#     - `None`: Если токен недействителен или истёк.
#     """
#     try:
#         payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
#         return payload
#     except JWTError:
#         return None
#
#
