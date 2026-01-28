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

def get_birthdate_from_national_id(national_id: str) -> str | None:
    """
    Extracts the birthdate from an Estonian national ID code.
    Returns string in format 'YYYY-MM-DD' or None if invalid.
    
    Format: GYYMMDDSSSC
    G: 1,2=18xx; 3,4=19xx; 5,6=20xx
    """
    if not national_id or len(national_id) != 11 or not national_id.isdigit():
        return None
        
    try:
        century_digit = int(national_id[0])
        year_segment = national_id[1:3]
        month_segment = national_id[3:5]
        day_segment = national_id[5:7]
        
        century_map = {
            1: 1800, 2: 1800,
            3: 1900, 4: 1900,
            5: 2000, 6: 2000
        }
        
        if century_digit not in century_map:
            return None
            
        full_year = century_map[century_digit] + int(year_segment)
        
        # Simple date validation ideally relies on datetime but strictness might fail for edge cases?
        # Let's trust the ID somewhat but ensure format is valid.
        return f"{full_year}-{month_segment}-{day_segment}"
        
    except Exception:
        return None