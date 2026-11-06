import hashlib
import hmac
import secrets

ITERACIONES = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERACIONES).hex()
    return f"{salt}${h}"


def verificar_password(password: str, guardado: str) -> bool:
    try:
        salt, h = guardado.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERACIONES).hex()
    return hmac.compare_digest(calc, h)


def nuevo_token() -> str:
    return secrets.token_urlsafe(32)
