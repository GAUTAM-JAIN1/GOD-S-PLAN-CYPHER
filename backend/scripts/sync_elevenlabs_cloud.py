import asyncio
import json
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath("."))

import httpx
from backend.services.elevenlabs_service import provision_elevenlabs_agent, get_elevenlabs_headers

async def sync_all_agents():
    conn = sqlite3.connect("voxera.db")
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, name, system_prompt, first_message, voice_id, language_code, elevenlabs_agent_id, catalog_json 
        FROM domain_profiles
    """).fetchall()
    
    print("=" * 60)
    print("SYNCHRONIZING ALL DOMAINS TO REAL ELEVENLABS CLOUD AGENTS")
    print("=" * 60)
    
    for row in rows:
        dom_id, name, sys_prompt, first_msg, voice_id, lang, agent_id, catalog_json = row
        print(f"\nProcessing: {name} ({dom_id})...")
        
        catalog = json.loads(catalog_json or "[]")
        
        # Build structured category catalog summary
        cats = {}
        for it in catalog:
            c_name = it.get("category", "General")
            if c_name not in cats:
                cats[c_name] = []
            cats[c_name].append(f"{it.get('canonical_name')}: Rs {int(it.get('price_inr', 0))}")
        
        cat_blocks = []
        for c_name, items in cats.items():
            cat_blocks.append(f"Category '{c_name}':\n  " + "\n  ".join(f"- {i}" for i in items))
        cat_summary = "\n\n".join(cat_blocks)
        
        grounded_prompt = f"""{sys_prompt}

VERIFIED LIVE BUSINESS CATALOG (ABSOLUTE GROUND TRUTH - ZERO EXTERNAL ITEMS):
{cat_summary}

STRICT PROHIBITION ON HALLUCINATION:
- You ONLY sell and offer the exact items listed in the verified catalog above!
- ABSOLUTELY NEVER offer pizza, burgers, chowmein, chaap, fries, or any food not in the catalog.
- If caller asks 'kya kya hai?' or 'menu batao', state ONLY the main category names: '{", ".join(cats.keys())}'.
- When caller asks for a specific category, mention 2-3 items with prices.
- Spoken turns MUST NEVER exceed 18 words in authentic Indian Hinglish."""

        res = await provision_elevenlabs_agent(
            business_name=name,
            system_prompt=grounded_prompt,
            first_message=first_msg,
            voice_id=voice_id,
            language_code=lang or "hi",
            existing_agent_id=agent_id
        )
        
        print(f"Result for {dom_id}: status={res.status}, agent_id={res.agent_id}, success={res.success}")
        if res.success and res.agent_id:
            c.execute("UPDATE domain_profiles SET elevenlabs_agent_id = ? WHERE id = ?", (res.agent_id, dom_id))
            conn.commit()
            print(f"Locked agent_id {res.agent_id} in SQLite for {dom_id}")
        else:
            print(f"Error message: {res.message}")

    print("\n" + "=" * 60)
    print("ALL ELEVENLABS AGENTS SYNCHRONIZED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(sync_all_agents())
