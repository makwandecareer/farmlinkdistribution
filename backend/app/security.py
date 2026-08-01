import base64, hashlib, hmac, json, os, time
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from .config import get_settings

settings = get_settings()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        alg, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if alg != "pbkdf2_sha256": return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def create_access_token(subject: str, role: str) -> str:
    header = {"alg":"HS256","typ":"JWT"}
    now = int(time.time())
    payload = {"sub":subject,"role":role,"iat":now,"exp":now + settings.access_token_minutes * 60}
    h = _b64(json.dumps(header,separators=(",",":")).encode())
    p = _b64(json.dumps(payload,separators=(",",":")).encode())
    sig = _b64(hmac.new(settings.secret_key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

def decode_access_token(token: str) -> dict:
    try:
        h,p,s = token.split(".")
        expected = _b64(hmac.new(settings.secret_key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(s, expected): raise ValueError("bad signature")
        payload = json.loads(_unb64(p))
        if int(payload["exp"]) < int(time.time()): raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
