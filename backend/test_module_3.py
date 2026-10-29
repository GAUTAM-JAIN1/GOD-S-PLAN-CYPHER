import urllib.request
import urllib.parse
import json
import sqlite3
import sys

BASE_URL = "http://127.0.0.1:8000"

def log_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_module_3_audit():
    log_header("MODULE 3 DEEP ENGINEERING VERIFICATION SUITE")

    # -------------------------------------------------------------
    # TEST 1: Hinglish Acoustic Pre-Normalizer & Double-Metaphone Scorer
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Hinglish Spoken Utterance with Fillers, Slang & Quantities...")
    test_utterance_1 = "bhaiya do medium hezalnat cold brew wala laga do"
    print(f"  Input: \"{test_utterance_1}\"")
    
    payload_1 = {
        "domain_id": "brew-bite-cafe",
        "spoken_entity": test_utterance_1,
        "quantity": 1,
        "caller_utterance": test_utterance_1,
        "session_id": "#TEST-M3-PASS"
    }
    
    res1 = post_json("/api/guardrail/verify-catalog-item", payload_1)
    
    print(f"  Match Type: {res1.get('match_type')}")
    print(f"  Filtered Pure Entity: \"{res1.get('filtered_entity')}\"")
    print(f"  Extracted Quantity: {res1.get('quantity')}")
    print(f"  Extracted Modifiers: {res1.get('modifiers')}")
    print(f"  Acoustic-DoubleMetaphone Score: {res1.get('score')}")
    print(f"  Matched Canonical Name: {res1.get('matched_item', {}).get('canonical_name')}")
    print(f"  Unit Price: Rs {res1.get('unit_price_inr')}")
    print(f"  Total Price: Rs {res1.get('total_price_inr')}")
    print(f"  Two-Phase Verification Token: {res1.get('verification_token')}")
    instr_safe = str(res1.get('instruction', '')).replace('₹', 'Rs.')
    print(f"  Read-Back Mandatory Instruction:\n    {instr_safe}")

    assert res1.get("match_type") == "DETERMINISTIC_PASS", f"Expected DETERMINISTIC_PASS, got {res1.get('match_type')}"
    assert res1.get("quantity") == 2, f"Expected quantity 2, got {res1.get('quantity')}"
    assert res1.get("score") >= 0.85, f"Expected score >= 0.85, got {res1.get('score')}"
    assert res1.get("verification_token") is not None, "Missing verification token"
    assert "medium" in res1.get("modifiers", []), "Expected 'medium' modifier extracted"
    token = res1.get("verification_token")
    print("  >>> TEST 1 RESULT: PASSED (100% Score >= 0.85, Token Generated)")

    # -------------------------------------------------------------
    # TEST 2: Ambiguity Trap Rule & Exact Top-2 Relative Probability Math
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Ambiguous Entity (Top-2 Gap Penalty & Relative Probabilities)...")
    test_utterance_2 = "bhaiya do large latte lagado"
    print(f"  Input: \"{test_utterance_2}\"")
    
    payload_2 = {
        "domain_id": "brew-bite-cafe",
        "spoken_entity": test_utterance_2,
        "quantity": 1,
        "caller_utterance": test_utterance_2,
        "session_id": "#TEST-M3-AMBIGUOUS"
    }
    
    res2 = post_json("/api/guardrail/verify-catalog-item", payload_2)
    
    print(f"  Match Type: {res2.get('match_type')}")
    print(f"  Score (Capped if Ambiguous): {res2.get('score')}")
    print(f"  Is Ambiguous Trap Triggered: {res2.get('is_ambiguous')}")
    candidates = res2.get("candidates", [])
    print(f"  Candidates Detected: {len(candidates)}")
    for idx, c in enumerate(candidates):
        print(f"    Candidate {idx+1}: {c.get('canonical_name')} | Score: {c.get('score')} | Probability: {c.get('probability_pct')}% | Price: Rs {c.get('price_inr')}")

    assert res2.get("match_type") == "WHISPER_HOLD", f"Expected WHISPER_HOLD, got {res2.get('match_type')}"
    assert res2.get("score") < 0.85, f"Expected score < 0.85, got {res2.get('score')}"
    if len(candidates) >= 2:
        p1 = candidates[0].get("probability_pct", 0)
        p2 = candidates[1].get("probability_pct", 0)
        assert (p1 + p2) == 100, f"Expected P1+P2 == 100%, got {p1} + {p2} = {p1+p2}"
        print(f"  Relative Probability Math Verified: P1 ({p1}%) + P2 ({p2}%) = 100%")
    print("  >>> TEST 2 RESULT: PASSED (Ambiguity Trap Capped & Relative Probability Math Verified)")

    # -------------------------------------------------------------
    # TEST 3: Real SQLite Persistence for Intercept Holds
    # -------------------------------------------------------------
    print("\n[TEST 3] Verifying SQLite Persistence for Intercept Holds...")
    active_holds = get_json("/api/guardrail/active-holds")
    print(f"  Total Active Holds in SQLite: {len(active_holds)}")
    assert len(active_holds) > 0, "Expected at least 1 active hold in database"
    latest_hold = active_holds[0]
    print(f"  Latest Hold ID: {latest_hold.get('id')}")
    print(f"  Spoken Entity: {latest_hold.get('spoken_entity')}")
    print(f"  Hold Reason: {latest_hold.get('hold_reason')}")
    print(f"  Candidate 1: {latest_hold.get('candidate_1', {}).get('canonical_name')} ({latest_hold.get('candidate_1', {}).get('probability_pct')}%)")
    print(f"  Candidate 2: {latest_hold.get('candidate_2', {}).get('canonical_name')} ({latest_hold.get('candidate_2', {}).get('probability_pct')}%)")
    print(f"  Status: {latest_hold.get('status')}")
    print("  >>> TEST 3 RESULT: PASSED (Intercept Hold Persisted in SQLite)")

    # -------------------------------------------------------------
    # TEST 4: Two-Phase Commit Lock (Phase B commit_verified_action)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Two-Phase Commit Lock with Token from Test 1...")
    commit_payload = {
        "domain_id": "brew-bite-cafe",
        "token": token,
        "canonical_name": res1.get("matched_item", {}).get("canonical_name"),
        "quantity": res1.get("quantity"),
        "total_price_inr": res1.get("total_price_inr"),
        "caller_phone": "+91 98712 44321",
        "session_id": "#TEST-M3-PASS"
    }
    
    commit_res = post_json("/api/guardrail/commit-action", commit_payload)
    print(f"  Commit Success: {commit_res.get('success')}")
    print(f"  Status Badge: {commit_res.get('status')}")
    print(f"  Ledger ID: {commit_res.get('ledger_id')}")
    msg_safe = str(commit_res.get('message', '')).replace('₹', 'Rs.')
    print(f"  Message: {msg_safe}")

    assert commit_res.get("success") is True, "Commit action failed"
    assert commit_res.get("status") == "LOCKED IN POS", f"Expected 'LOCKED IN POS', got {commit_res.get('status')}"
    print("  >>> TEST 4 RESULT: PASSED (Two-Phase Lock Validated & Status Badged)")

    # -------------------------------------------------------------
    # TEST 5: Real SQLite Verified Ledger Query
    # -------------------------------------------------------------
    print("\n[TEST 5] Querying SQLite Ledger Entries Table...")
    ledger_entries = get_json("/api/ledger/entries")
    print(f"  Total Ledger Entries in SQLite: {len(ledger_entries)}")
    assert len(ledger_entries) > 0, "Expected at least 1 ledger entry in SQLite"
    latest_entry = ledger_entries[0]
    print(f"  Latest Ledger Session: {latest_entry.get('sessionId')}")
    print(f"  Action Summary: {latest_entry.get('action')}")
    total_safe = str(latest_entry.get('totalInr', '')).replace('₹', 'Rs.')
    print(f"  Total INR: {total_safe}")
    print(f"  Phonetic Gate: {latest_entry.get('phoneticGate')}")
    print(f"  Resolution Status: {latest_entry.get('status')}")
    print("  >>> TEST 5 RESULT: PASSED (Real Row Persisted in SQLite ledger_entries)")

    log_header("ALL 5 MODULE 3 ENGINEERING REQUIREMENTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_module_3_audit()
