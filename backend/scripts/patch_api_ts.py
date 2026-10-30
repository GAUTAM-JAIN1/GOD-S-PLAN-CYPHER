with open("frontend/src/lib/api.ts", "r", encoding="utf-8") as f:
    text = f.read()

target = "  elevenlabs_agent_id?: string | null;\n  created_at?: string;"
replacement = "  elevenlabs_agent_id?: string | null;\n  compiled_by?: string;\n  crew_execution_log_json?: string;\n  created_at?: string;"

if target in text:
    text = text.replace(target, replacement, 1)
    with open("frontend/src/lib/api.ts", "w", encoding="utf-8") as f:
        f.write(text)
    print("frontend/src/lib/api.ts updated successfully!")
else:
    print("Target not found, checking...")
