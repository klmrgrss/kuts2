# app/services/smart_id_service.py
import os
import httpx
from typing import Optional, Dict, Any

async def get_client() -> httpx.AsyncClient:
    """Creates and returns an httpx client with the correct base URL and a reasonable timeout."""
    base_url = os.getenv("SMARTID_API_HOST", "https://sid.demo.sk.ee/smart-id-rp/v2/")
    return httpx.AsyncClient(base_url=base_url, timeout=20.0)

async def initiate_authentication(national_id: str, encoded_hash: str, country_code: str = "EE") -> Optional[Dict[str, Any]]:
    """Initiates an authentication session with the Smart-ID API."""
    relying_party_uuid = os.getenv("SMARTID_RP_UUID", "00000000-0000-4000-8000-000000000000")
    relying_party_name = os.getenv("SMARTID_RP_NAME", "DEMO")

    endpoint = f"authentication/etsi/PNO{country_code}-{national_id}"
    
    payload = {
        "relyingPartyUUID": relying_party_uuid, 
        "relyingPartyName": relying_party_name,
        "hash": encoded_hash,
        "hashType": "SHA256",
        "nonce": "KUTS2-DEMO-NONCE",
        # THE FIX: Remove the certificateLevel parameter to allow the service to use the default.
        # "certificateLevel": "QUALIFIED", 
        "allowedInteractionsOrder": [{"type": "displayTextAndPIN", "displayText60": "Log in to Kuts2?"}],
        "requestProperties": {
            "shareMdClientIpAddress": True
        }
    }

    try:
        async with await get_client() as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
        
        response_data = response.json()
        print(f"--- SUCCESS [Smart-ID Service]: Initiated session {response_data.get('sessionID')} ---")
        return response_data

    except httpx.HTTPStatusError as e:
        print(f"--- ERROR [Smart-ID Service]: HTTP error during initiation: {e.response.status_code} - Body: {e.response.text} ---")
    except httpx.RequestError as e:
        print(f"--- ERROR [Smart-ID Service]: Network connection error: {e} ---")
    except Exception as e:
        print(f"--- ERROR [Smart-ID Service]: An unexpected error occurred during initiation: {e} ---")
    
    return None

async def check_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Checks the status of an ongoing Smart-ID session using long-polling.
    """
    if not session_id:
        return None

    endpoint = f"session/{session_id}?timeoutMs=15000"

    try:
        async with await get_client() as client:
            response = await client.get(endpoint)
            response.raise_for_status()
        
        status_data = response.json()
        print(f"--- INFO [Smart-ID Service]: Checked status for session {session_id}. State: {status_data.get('state')} ---")
        return status_data

    except httpx.HTTPStatusError as e:
        print(f"--- ERROR [Smart-ID Service]: HTTP error checking status: {e.response.status_code} - Body: {e.response.text} ---")
    except httpx.ReadTimeout:
        print(f"--- INFO [Smart-ID Service]: Long-poll timeout for session {session_id}. Continuing to poll. ---")
        return {"state": "RUNNING"}
    except httpx.RequestError as e:
        print(f"--- ERROR [Smart-ID Service]: Network connection error while checking status: {e} ---")
    except Exception as e:
        print(f"--- ERROR [Smart-ID Service]: An unexpected error occurred checking status: {e} ---")

    return None