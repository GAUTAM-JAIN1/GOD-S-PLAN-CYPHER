import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import httpx
from backend.config import settings
from backend.services.elevenlabs_service import build_convai_agent_payload, get_elevenlabs_headers
import sqlite3

async def sync_agent():
    conn = sqlite3.connect("voxera.db")
    row = conn.execute("SELECT id, name, system_prompt, first_message, voice_id, language_code, elevenlabs_agent_id FROM domain_profiles WHERE id = 'dharma-dhaba'").fetchone()
    conn.close()

    if not row:
        print("Dharma Dhaba not found")
        return

    domain_id, name, system_prompt, first_message, voice_id, language_code, current_agent_id = row
    print("Current agent_id on ElevenLabs:", current_agent_id)

    payload = build_convai_agent_payload(
        business_name=name,
        system_prompt=system_prompt,
        first_message=first_message,
        voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",
        language_code=language_code or "hi-IN"
    )

    headers = get_elevenlabs_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check current agent on ElevenLabs
        url_get = f"https://api.elevenlabs.io/v1/convai/agents/{current_agent_id}"
        resp_get = await client.get(url_get, headers=headers)
        print("GET agent status:", resp_get.status_code)
        if resp_get.status_code == 200:
            agent_data = resp_get.json()
            curr_prompt = agent_data.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("prompt", "")
            print("Snippet of current prompt on ElevenLabs:\n", curr_prompt[:300].encode('ascii', 'replace').decode())

            # Now PATCH the agent on ElevenLabs with the updated prompt and settings!
            url_patch = f"https://api.elevenlabs.io/v1/convai/agents/{current_agent_id}"
            resp_patch = await client.patch(url_patch, json=payload, headers=headers)
            print("PATCH agent status:", resp_patch.status_code)
            if resp_patch.status_code == 200:
                print("SUCCESSFULLY UPDATED ElevenLabs agent with fresh authentic dhaba prompt!")
            else:
                print("PATCH failed:", resp_patch.text)
        else:
            print("Agent not found, let's create a fresh one")

asyncio.run(sync_agent())
