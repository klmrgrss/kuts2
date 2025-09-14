# tests/auth/test_utils.py
from app.auth.utils import get_password_hash, verify_password

def test_password_hashing():
    """
    Tests that a password can be hashed and then successfully verified.
    Also tests that verification fails for an incorrect password.
    """
    password = "my-super-secret-password-123"
    hashed_password = get_password_hash(password)

    # The 'assert' keyword is the core of pytest.
    # If the condition is True, the test passes silently.
    # If the condition is False, the test fails and reports an error.

    # 1. Assert that the correct password verifies successfully.
    assert verify_password(password, hashed_password)

    # 2. Assert that an incorrect password does NOT verify.
    assert not verify_password("wrong-password", hashed_password)
