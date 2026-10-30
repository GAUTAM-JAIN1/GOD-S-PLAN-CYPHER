import urllib.request
import json
import time

turns = [
    "Namaste",
    "Khane me kya kya hai?",
    "Panini me kya options hain?",
    "French fries milenge kya?",
    "Ek hazelnut cold brew aur ek smoked paneer panini pack kar do",
    "Theek hai confirm kar do"
]

history = []
session_id = f"test_flow_session_{int(time.time())}"

print("=" * 60)
print("TESTING BREW & BITE CAFE CATEGORY-FIRST CONVERSATIONAL FLOW")
print("=" * 60)

for idx, t in enumerate(turns, 1):
    payload = json.dumps({
        "domain_id": "brew-bite-cafe",
        "user_utterance": t,
        "session_id": session_id,
        "conversation_history": history
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/voice/live-turn",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    
    reply = data["reply"]
    history.append({"role": "user", "content": t})
    history.append({"role": "assistant", "content": reply})
    
    word_count = len(reply.split())
    latency = data.get("llm_latency_ms", 0)
    print(f"\n[Turn {idx}] User: \"{t}\"")
    print(f"Agent ({latency}ms, {word_count} words): \"{reply}\"")
    if data.get("order_committed"):
        print(f">>> [POS COMMIT EVENT] Item: {data.get('committed_item')} | Total: Rs {data.get('committed_total')}")
    
    time.sleep(1.0)

print("\n" + "=" * 60)
print("ALL TURNS COMPLETED SUCCESSFULLY!")
print("=" * 60)
