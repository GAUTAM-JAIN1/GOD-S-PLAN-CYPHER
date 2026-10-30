import sqlite3
import json
from datetime import datetime, timezone
import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.seed_domains import SEED_DOMAINS, make_crew_execution_log

conn = sqlite3.connect("voxera.db")
cursor = conn.cursor()

# 1. Ensure columns exist
cols = [c[1] for c in cursor.execute("PRAGMA table_info(domain_profiles)").fetchall()]
if "compiled_by" not in cols:
    cursor.execute("ALTER TABLE domain_profiles ADD COLUMN compiled_by VARCHAR(128) DEFAULT 'CrewAI Multi-Agent Trained'")
if "crew_execution_log_json" not in cols:
    cursor.execute("ALTER TABLE domain_profiles ADD COLUMN crew_execution_log_json TEXT DEFAULT '[]'")

# 2. Physically delete any corrupted/broken domains (like "hay Mere restaurant...")
cursor.execute("DELETE FROM domain_profiles WHERE id LIKE '%hay%' OR name LIKE '%hay%' OR name LIKE '%mere restaurant%'")
print(f"Deleted broken/corrupted domains. Rows affected: {cursor.rowcount}")

now_str = datetime.now(timezone.utc).isoformat()

# 3. Seed / Update the 5 Core Domains
for dom in SEED_DOMAINS:
    dom_id = dom["id"]
    name = dom["name"]
    dom_type = dom["domain_type"]
    tagline = dom["tagline"]
    sys_prompt = dom["system_prompt"]
    first_msg = dom["first_message"]
    voice_id = dom["voice_id"]
    lang = dom["language_code"]
    timeout = dom["turn_timeout_ms"]
    catalog_json = json.dumps(dom["catalog_items"])
    policies_json = json.dumps(dom["strict_policies"])
    pydantic_code = dom["pydantic_code"]
    compiled_by = dom.get("compiled_by", "CrewAI Multi-Agent Trained")
    exec_log = make_crew_execution_log(name, len(dom["catalog_items"]), len(dom["strict_policies"]))

    cursor.execute("SELECT id FROM domain_profiles WHERE id = ?", (dom_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE domain_profiles 
            SET name=?, domain_type=?, tagline=?, system_prompt=?, first_message=?,
                voice_id=?, language_code=?, turn_timeout_ms=?, catalog_json=?,
                policies_json=?, pydantic_code=?, compiled_by=?, crew_execution_log_json=?, updated_at=?
            WHERE id=?
        """, (name, dom_type, tagline, sys_prompt, first_msg, voice_id, lang, timeout, catalog_json, policies_json, pydantic_code, compiled_by, exec_log, now_str, dom_id))
        print(f"[UPDATED] {dom_id} ({name}) -> {compiled_by}")
    else:
        cursor.execute("""
            INSERT INTO domain_profiles 
            (id, name, domain_type, tagline, system_prompt, first_message, voice_id, language_code, turn_timeout_ms, catalog_json, policies_json, pydantic_code, compiled_by, crew_execution_log_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dom_id, name, dom_type, tagline, sys_prompt, first_msg, voice_id, lang, timeout, catalog_json, policies_json, pydantic_code, compiled_by, exec_log, now_str, now_str))
        print(f"[INSERTED] {dom_id} ({name}) -> {compiled_by}")

# Also ensure quickkart-d2c-support alias exists if quickkart-d2c is seeded
cursor.execute("SELECT catalog_json, policies_json, pydantic_code, system_prompt, first_message, voice_id, language_code, turn_timeout_ms, compiled_by, crew_execution_log_json FROM domain_profiles WHERE id='quickkart-d2c'")
qk = cursor.fetchone()
if qk:
    cursor.execute("SELECT id FROM domain_profiles WHERE id='quickkart-d2c-support'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO domain_profiles 
            (id, name, domain_type, tagline, system_prompt, first_message, voice_id, language_code, turn_timeout_ms, catalog_json, policies_json, pydantic_code, compiled_by, crew_execution_log_json, created_at, updated_at)
            VALUES ('quickkart-d2c-support', 'QuickKart D2C Support', 'support_collections', 'Instant Commerce Logistics & Operations (10-Minute Delivery)', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (qk[3], qk[4], qk[5], qk[6], qk[7], qk[0], qk[1], qk[2], qk[8], qk[9], now_str, now_str))
        print("[INSERTED] quickkart-d2c-support alias profile")
    else:
        cursor.execute("""
            UPDATE domain_profiles 
            SET catalog_json=?, policies_json=?, pydantic_code=?, system_prompt=?, first_message=?,
                voice_id=?, language_code=?, turn_timeout_ms=?, compiled_by=?, crew_execution_log_json=?, updated_at=?
            WHERE id='quickkart-d2c-support'
        """, (qk[0], qk[1], qk[2], qk[3], qk[4], qk[5], qk[6], qk[7], qk[8], qk[9], now_str))
        print("[UPDATED] quickkart-d2c-support alias profile")

conn.commit()
conn.close()
print("All 5 Pre-Built Enterprise Domains successfully locked & synced in SQLite!")
