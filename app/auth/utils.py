# auth/utils.py

# Re-saved as UTF-8
from passlib.context import CryptContext
import hashlib
import os

# Setup password hashing context
# Using bcrypt is a good secure default
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hashes a plain password using the configured context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def calculate_verification_code(digest: bytes) -> str:
    """
    Calculates the 4-digit verification code from a hash digest.
    If the API host points to the Smart-ID demo environment, it always returns '0000'.
    """
    # THE FIX: Check if we are using the demo environment
    api_host = os.getenv("SMARTID_API_HOST", "")
    if "demo.sk.ee" in api_host:
        return "0000"

    # Otherwise, calculate the code normally for production
    # Get the last 2 bytes of the digest
    two_bytes = digest[-2:]
    # Interpret these two bytes as a big-endian integer and calculate modulo 10000
    integer_value = int.from_bytes(two_bytes, 'big') % 10000
    # Format as a 4-digit string with leading zeros
    return f"{integer_value:04d}"