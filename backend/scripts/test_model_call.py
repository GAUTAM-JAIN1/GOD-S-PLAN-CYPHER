import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.services.groq_compiler import get_groq_client
import json

client = get_groq_client()
resp = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {"role": "system", "content": "You are an entity extractor. Return ONLY valid JSON: {\"clean_name\": \"...\"}"},
        {"role": "user", "content": "arre bhai mere naye restaurant ka naam Royal Punjab Tadka hai"}
    ],
    max_tokens=60,
    temperature=0.1
)
print("Qwen output:", resp.choices[0].message.content.strip())
