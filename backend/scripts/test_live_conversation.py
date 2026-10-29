import urllib.request
import json
import time

url = "http://localhost:8000/api/voice/live-turn"

def post_json(data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    dur_ms = (time.time() - t0) * 1000
    return res, dur_ms

# Turn 1: "आज का नहीं चाहिए। खाने में क्या-क्या है?"
payload_1 = {
    "domain_id": "dharma-dhaba",
    "user_utterance": "आज का नहीं चाहिए। खाने में क्या-क्या है?",
    "session_id": "test-session-judge-demo-1",
    "conversation_history": []
}

res1, dur1 = post_json(payload_1)
print(f"--- Turn 1 responded in {dur1:.1f}ms ---")
print("Agent Reply:", res1.get("reply"))
print("LLM Latency:", res1.get("llm_latency_ms"), "ms | Total Latency:", res1.get("total_latency_ms"), "ms")

# Turn 2: "अ, एक paneer की सब्जी और चार रोटी करवा दीजिए।"
payload_2 = {
    "domain_id": "dharma-dhaba",
    "user_utterance": "अ, एक paneer की सब्जी और चार रोटी करवा दीजिए।",
    "session_id": "test-session-judge-demo-1",
    "conversation_history": [
        {"role": "user", "content": "आज का नहीं चाहिए। खाने में क्या-क्या है?"},
        {"role": "assistant", "content": res1.get("reply", "")}
    ]
}

res2, dur2 = post_json(payload_2)
print(f"\n--- Turn 2 responded in {dur2:.1f}ms ---")
print("Agent Reply:", res2.get("reply"))
print("LLM Latency:", res2.get("llm_latency_ms"), "ms | Total Latency:", res2.get("total_latency_ms"), "ms")
