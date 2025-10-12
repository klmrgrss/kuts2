# app/services/smart_id_service.py
import os
import httpx
from typing import Optional, Dict, Any

# It's better to initialize the client inside the functions
# to ensure it picks up the environment variables correctly,
# especially in complex startup scenarios.

async def get_client() -> httpx.AsyncClient:
    """Creates and returns an httpx client with the correct base URL."""
    # Read the environment variable, providing the known-correct default.
    base_url = os.getenv("SMARTID_API_HOST", "https://sid.api.sk.ee/smart-id-rp/v2/")
    return httpx.AsyncClient(base_url=base_url, timeout=30.0)

async def initiate_authentication(national_id: str, country_code: str = "EE") -> Optional[Dict[str, Any]]:
    """
    Initiates an authentication session with the Smart-ID API.

    Args:
        national_id: The user's national identity number.
        country_code: The user's country code (defaults to 'EE').

    Returns:
        A dictionary containing the sessionID if successful, otherwise None.
    """
    relying_party_uuid = os.getenv("SMARTID_RP_UUID")
    relying_party_name = os.getenv("SMARTID_RP_NAME")

    if not relying_party_uuid or not relying_party_name:
        print("--- ERROR [Smart-ID Service]: Relying Party credentials are not configured. ---")
        return None

    endpoint = f"authentication/etsi/PNO{country_code}-{national_id}"
    
    # This is a simplified hash for demonstration. In production, you would generate
    # a proper, non-replayable hash.
    dummy_hash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" # SHA-256 dummy

    payload = {
        "relyingPartyUUID": relying_party_uuid,
        "relyingPartyName": relying_party_name,
        "hash": dummy_hash,
        "hashType": "SHA256",
        "allowedInteractionsOrder": [
            {
                "type": "displayTextAndPIN",
                "displayText60": "Log in to Kuts2?"
            }
        ]
    }

    try:
        async with await get_client() as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        
        response_data = response.json()
        print(f"--- SUCCESS [Smart-ID Service]: Initiated session {response_data.get('sessionID')} ---")
        return response_data

    except httpx.HTTPStatusError as e:
        print(f"--- ERROR [Smart-ID Service]: HTTP error during authentication initiation: {e.response.status_code} - {e.response.text} ---")
    except httpx.ConnectError as e:
        # This will catch DNS errors specifically
        print(f"--- ERROR [Smart-ID Service]: Network connection error: {e} ---")
    except Exception as e:
        print(f"--- ERROR [Smart-ID Service]: An unexpected error occurred during initiation: {e} ---")
    
    return None

async def check_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Checks the status of an ongoing Smart-ID session.

    Args:
        session_id: The ID of the session to check.

    Returns:
        A dictionary containing the full status response, or None on error.
    """
    if not session_id:
        return None
        
    endpoint = f"session/{session_id}"

    try:
        async with await get_client() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
        
        status_data = response.json()
        print(f"--- INFO [Smart-ID Service]: Checked status for session {session_id}. State: {status_data.get('state')} ---")
        return status_data

    except httpx.HTTPStatusError as e:
        print(f"--- ERROR [Smart-ID Service]: HTTP error checking session status: {e.response.status_code} - {e.response.text} ---")
    except httpx.ConnectError as e:
        print(f"--- ERROR [Smart-ID Service]: Network connection error while checking status: {e} ---")
    except Exception as e:
        print(f"--- ERROR [Smart-ID Service]: An unexpected error occurred checking status: {e} ---")

    return None