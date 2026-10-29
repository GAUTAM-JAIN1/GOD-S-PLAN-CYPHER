import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import httpx
from backend.services.elevenlabs_service import build_convai_agent_payload, get_elevenlabs_headers
import sqlite3

async def sync_all_agents():
    conn = sqlite3.connect("voxera.db")
    rows = conn.execute("SELECT id, name, system_prompt, first_message, voice_id, language_code, elevenlabs_agent_id FROM domain_profiles").fetchall()
    conn.close()

    headers = get_elevenlabs_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        for r in rows:
            domain_id, name, system_prompt, first_message, voice_id, language_code, agent_id = r
            if not agent_id:
                continue
            payload = build_convai_agent_payload(
                business_name=name,
                system_prompt=system_prompt,
                first_message=first_message,
                voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",
                language_code=language_code or "hi-IN"
            )
            url_patch = f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}"
            try:
                resp = await client.patch(url_patch, json=payload, headers=headers)
                if resp.status_code == 200:
                    print(f"[OK] Synced {domain_id} ({name}) -> {agent_id}")
                else:
                    print(f"[ERR] Failed {domain_id}: {resp.status_code} - {resp.text[:150]}")
            except Exception as e:
                print(f"[EXC] {domain_id}: {e}")

asyncio.run(sync_all_agents())
