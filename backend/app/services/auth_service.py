import base64
import hashlib
import hmac
import re
from datetime import UTC, datetime, timedelta
from secrets import token_bytes

import jwt

from app.core.config import get_settings


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email_format(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    params = {"n": 2**14, "r": 8, "p": 1}
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=params["n"],
        r=params["r"],
        p=params["p"],
        dklen=32,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    key_b64 = base64.b64encode(key).decode("ascii")
    return f"scrypt${params['n']}${params['r']}${params['p']}${salt_b64}${key_b64}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_b64, key_b64 = stored_hash.split("$", maxsplit=5)
        if algorithm != "scrypt":
            return False

        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_key = base64.b64decode(key_b64.encode("ascii"))
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected_key),
        )
        return hmac.compare_digest(derived_key, expected_key)
    except Exception:
        return False


def create_access_token(subject: str) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.auth_access_token_expire_minutes * 60
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    payload = {
        "sub": subject,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "type": "access",
    }

    token = jwt.encode(payload, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)
    return token, expires_in
