import sys, os
sys.path.insert(0, os.path.abspath("."))
import httpx
from dotenv import dotenv_values

env_vars = dotenv_values("backend/.env")
key = env_vars.get("ELEVENLABS_API_KEY")

if not key:
    print("ERROR: ELEVENLABS_API_KEY is not set or empty in backend/.env")
    sys.exit(1)

print(f"Checking key: {key[:6]}...{key[-4:] if len(key) > 10 else ''}")

headers = {"xi-api-key": key}
try:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get("https://api.elevenlabs.io/v1/user/subscription", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            tier = data.get("tier", "unknown")
            char_count = data.get("character_count", 0)
            char_limit = data.get("character_limit", 0)
            print(f"[SUCCESS] ElevenLabs API Key is VALID!")
            print(f"Tier: {tier} | Usage: {char_count} / {char_limit} characters (Remaining: {char_limit - char_count})")
        else:
            print(f"[FAIL] ElevenLabs API returned HTTP {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Error testing ElevenLabs key: {e}")
