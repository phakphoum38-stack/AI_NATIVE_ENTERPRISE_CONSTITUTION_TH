from fastapi import Header,HTTPException
from .config import settings

def require_token(authorization: str|None=Header(default=None)):
    expected=f"Bearer {settings.api_token}"
    if authorization!=expected: raise HTTPException(status_code=401,detail="Invalid or missing API token")
    return "api-user"
