from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, UserRole
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials: raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_access_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Account unavailable")
    return user

def ceo_user(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.CEO.value: raise HTTPException(status_code=403, detail="CEO access required")
    return user
