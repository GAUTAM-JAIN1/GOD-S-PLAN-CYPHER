import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import httpx
from dotenv import dotenv_values
import sqlite3

env_vars = dotenv_values("backend/.env")
key = env_vars.get("ELEVENLABS_API_KEY")

async def check_and_reprovision():
    headers = {"xi-api-key": key}
    conn = sqlite3.connect("voxera.db")
    rows = conn.execute("SELECT id, name, system_prompt, first_message, voice_id, language_code, elevenlabs_agent_id FROM domain_profiles").fetchall()
    
    from backend.services.elevenlabs_service import build_convai_agent_payload

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check existing agents on this new account
        list_resp = await client.get("https://api.elevenlabs.io/v1/convai/agents", headers=headers)
        account_agents = {}
        if list_resp.status_code == 200:
            for ag in list_resp.json().get("agents", []):
                account_agents[ag.get("name")] = ag.get("agent_id")
        print(f"Existing agents in this new account: {len(account_agents)}")

        for r in rows:
            domain_id, name, system_prompt, first_message, voice_id, language_code, old_agent_id = r
            expected_name = f"Voxera — {name}"
            
            # Check if old_agent_id exists in this account
            agent_exists = False
            if old_agent_id:
                chk = await client.get(f"https://api.elevenlabs.io/v1/convai/agents/{old_agent_id}", headers=headers)
                if chk.status_code == 200:
                    agent_exists = True

            if not agent_exists:
                print(f"Provisioning fresh agent for '{name}' on new ElevenLabs account...")
                payload = build_convai_agent_payload(
                    business_name=name,
                    system_prompt=system_prompt,
                    first_message=first_message,
                    voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",
                    language_code=language_code or "hi-IN"
                )
                create_resp = await client.post("https://api.elevenlabs.io/v1/convai/agents/create", json=payload, headers=headers)
                if create_resp.status_code == 200:
                    new_agent_id = create_resp.json().get("agent_id")
                    print(f"[CREATED] {domain_id} -> {new_agent_id}")
                    conn.execute("UPDATE domain_profiles SET elevenlabs_agent_id = ? WHERE id = ?", (new_agent_id, domain_id))
                    conn.commit()
                else:
                    print(f"[FAIL] {domain_id} creation error: {create_resp.status_code} - {create_resp.text}")
            else:
                print(f"[ALREADY EXISTS] {domain_id} -> {old_agent_id}")

    conn.close()

asyncio.run(check_and_reprovision())

