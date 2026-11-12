"""Username/password accounts with salted PBKDF2 hashes (stdlib only)."""
import hashlib
import hmac
import re
import secrets

from par import db

ITERATIONS = 200_000
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password, stored):
    try:
        _, iterations, salt, digest = stored.split("$")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(check, digest)


def sign_up(username, password):
    """Returns (user, error)."""
    username = username.strip()
    if not USERNAME_RE.match(username):
        return None, "Username must be 3–30 characters: letters, numbers, . _ or -"
    if len(password) < 6:
        return None, "Password must be at least 6 characters."
    if db.get_user(username):
        return None, "That username is taken."
    return db.create_user(username, hash_password(password)), None


def sign_in(username, password):
    user = db.get_user(username.strip())
    if not user or not verify_password(password, user["pw_hash"]):
        return None, "Incorrect username or password."
    return user, None
