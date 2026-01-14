import asyncio
import os
import hashlib
import base64
import json
from app.services import smart_id_service

# Mock imports/setup if needed
# The service uses os.getenv, so it should work with defaults (Demo Env)

async def test_smart_id_flow():
    national_id = "10101010005" # Another Demo User
    print(f"--- Testing Smart-ID Initiation for {national_id} ---")
    
    # generate dummy hash
    data_to_sign = os.urandom(32)
    digest = hashlib.sha256(data_to_sign).digest()
    encoded_hash = base64.b64encode(digest).decode('utf-8')
    
    # 1. Initiate
    session_data = await smart_id_service.initiate_authentication(national_id, encoded_hash)
    
    if not session_data:
        print("FAILED: No session data returned.")
        return

    session_id = session_data.get("sessionID")
    print(f"SUCCESS: Session ID: {session_id}")
    
    # 2. Poll Status
    print(f"--- Polling status for {session_id} ---")
    for _ in range(5):
        await asyncio.sleep(2)
        status = await smart_id_service.check_session_status(session_id)
        if not status:
            print("FAILED: Status check returned None")
            continue
            
        state = status.get("state")
        print(f"Current State: {state}")
        
        if state == "COMPLETE":
            print("SUCCESS: Flow complete!")
            print(json.dumps(status, indent=2))
            return
        
    print("TIMED OUT waiting for completion (User needs to accept on their device in real life)")

if __name__ == "__main__":
    asyncio.run(test_smart_id_flow())
