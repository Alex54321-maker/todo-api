import jwt
from jwt.exceptions import PyJWTError
from config import settings

def decode_access_token(token: str):
    try:
        # Убираем "Bearer ", если он передался вместе с токеном
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except PyJWTError:
        return None

