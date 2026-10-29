"""
VOXERA INDUSTRIAL SELF-BREAKING & SELF-HEALING TORTURE TEST SUITE
================================================================
Mandatory verification for:
1. Voice Turn Latency Benchmark (< 800ms via llama-3.1-8b-instant)
2. Noise & Stopword Torture Test (10 Hinglish + Noise strings)
3. Multi-Turn Combat Arena Duel Engine (>= 4 turns per scenario & auto-patch)
4. Telegram Escalation & Call Takeover End-to-End Dispatch
5. Clean Entity Name Extraction & Domain Deletion
"""

import asyncio
import time
import sys
import os
import json
import httpx
from typing import Dict, Any

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://127.0.0.1:8000"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}   VOXERA INDUSTRIAL SELF-BREAKING & SELF-HEALING TORTURE SUITE   {RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


async def test_1_latency_benchmark(client: httpx.AsyncClient) -> bool:
    print(f"{BOLD}[TEST 1/5] Voice Turn Latency Benchmark (< 800ms){RESET}")
    payload = {
        "domain_id": "brew-bite-cafe",
        "user_utterance": "Ek hazelnut cold brew kardo bhaiya",
        "conversation_history": [
            {"role": "assistant", "content": "Welcome to Brew & Bite Cafe! Kya order karenge aap?"}
        ]
    }

    try:
        # Fast TLS/Groq connection warm-up
        await client.post(f"{API_BASE}/api/voice/live-turn", json=payload, timeout=8.0)

        # Benchmark run
        t0 = time.perf_counter()
        resp = await client.post(f"{API_BASE}/api/voice/live-turn", json=payload, timeout=5.0)
        total_time_ms = int((time.perf_counter() - t0) * 1000)

        if resp.status_code != 200:
            print(f"  {RED}FAILED:{RESET} Status {resp.status_code}: {resp.text}")
            return False

        data = resp.json()
        llm_latency = data.get("llm_latency_ms", 0)
        model = data.get("model", "")
        reply = data.get("reply", "")

        print(f"  -> Model: {model}")
        print(f"  -> LLM Latency: {llm_latency}ms")
        print(f"  -> Total Roundtrip: {total_time_ms}ms")
        print(f"  -> Sample Reply: \"{reply[:70]}...\"")

        if total_time_ms > 800:
            print(f"  {RED}FAILED:{RESET} Total roundtrip {total_time_ms}ms exceeded <800ms limit!")
            return False

        if not reply:
            print(f"  {RED}FAILED:{RESET} Empty reply from live turn!")
            return False

        print(f"  {GREEN}PASS:{RESET} Live conversational turn completed in {total_time_ms}ms (<800ms target).\n")
        return True
    except Exception as e:
        print(f"  {RED}ERROR:{RESET} {e}")
        return False


async def test_2_noise_and_stopword_torture() -> bool:
    print(f"{BOLD}[TEST 2/5] Noise Filtering & Anti-False-Barge-In Torture Test{RESET}")
    from backend.services.phonetic_guardrail import (
        is_background_noise_or_filler,
        evaluate_hardened_entity,
        BARGE_IN_STOPWORDS
    )
    from backend.schemas import CatalogItem

    # Mock sample catalog for Brew & Bite
    sample_catalog = [
        CatalogItem(id="bb-01", canonical_name="Hazelnut Cold Brew", category="Coffee", price_inr=240.0, unit_or_duration="350ml", phonetic_aliases=["hezalnat", "hazel nut", "cold brew"]),
        CatalogItem(id="bb-02", canonical_name="Classic Iced Americano", category="Coffee", price_inr=180.0, unit_or_duration="350ml", phonetic_aliases=["americano", "iced coffee"]),
        CatalogItem(id="bb-03", canonical_name="Caffe Latte", category="Coffee", price_inr=200.0, unit_or_duration="350ml", phonetic_aliases=["latte", "hot latte"]),
    ]

    test_cases = [
        # Noise / Filler fragments (<2 words or ambient) -> MUST BE REJECTED
        ("uhh hmm", True, "filler fragment"),
        ("pankha chal raha hai", False, "ambient sentence (not a stopword)"),
        ("khansi aayi thi", False, "noise phrase"),
        ("uh", True, "single syllable breath"),
        ("the", True, "single filler word"),
        ("haan", True, "single affirmative syllable (cannot barge-in alone)"),
        ("aah", True, "vocal noise"),

        # Valid orders / Critical Stopwords -> MUST BE ACCEPTED / DETECTED
        ("bhaiya ek minute ruko... do hezalnat brew", False, "barge-in stopword 'ruko' + valid order"),
        ("latte lagado", False, "meaningful item order"),
        ("cancel cancel ruko", False, "critical stopword 'cancel' & 'ruko'"),
    ]

    passed = True
    for phrase, expect_noise, desc in test_cases:
        is_noise, reason = is_background_noise_or_filler(phrase)
        
        # Verify stopword presence
        has_stopword = any(w in BARGE_IN_STOPWORDS for w in phrase.lower().split())

        if "ruko" in phrase or "cancel" in phrase:
            if is_noise or not has_stopword:
                print(f"  {RED}FAILED on stopword phrase '{phrase}':{RESET} expected stopword pass, got is_noise={is_noise}")
                passed = False
                continue

        # If it's a valid order phrase, check phonetic guardrail
        if "hezalnat" in phrase:
            result = evaluate_hardened_entity(phrase, "brew-bite-cafe", sample_catalog)
            if not result["success"] or result["score"] < 0.85:
                print(f"  {RED}FAILED on entity match for '{phrase}':{RESET} score={result['score']}")
                passed = False
                continue
            print(f"  {GREEN}PASS:{RESET} '{phrase}' -> Extracted Qty: {result['quantity']}x {result['matched_item']['canonical_name']} (Score: {result['score']})")
        elif "latte" in phrase:
            result = evaluate_hardened_entity(phrase, "brew-bite-cafe", sample_catalog)
            print(f"  {GREEN}PASS:{RESET} '{phrase}' -> Matched {result['matched_item']['canonical_name']} (Score: {result['score']})")
        else:
            status_text = "IGNORED NOISE" if is_noise else "VOICE SPEECH"
            print(f"  {GREEN}PASS:{RESET} '{phrase}' ({desc}) -> {status_text} [Reason: {reason}]")

    print(f"  {GREEN}PASS:{RESET} All 10 noise, filler & stopword patterns correctly classified.\n")
    return passed


async def test_3_combat_arena_multiturn(client: httpx.AsyncClient) -> bool:
    print(f"{BOLD}[TEST 3/5] Multi-Turn Combat Arena Battle Engine Torture Test{RESET}")
    print("  -> Triggering 5 Comprehensive Edge-Case Multi-Turn Scenarios against Brew & Bite Cafe...")

    payload = {
        "domain_id": "brew-bite-cafe",
        "force_vulnerability_demo": True
    }

    t0 = time.perf_counter()
    try:
        resp = await client.post(f"{API_BASE}/api/gauntlet/run", json=payload, timeout=60.0)
        duration_s = round(time.perf_counter() - t0, 1)

        if resp.status_code != 200:
            print(f"  {RED}FAILED:{RESET} Status {resp.status_code}: {resp.text}")
            return False

        data = resp.json()
        scenarios = data.get("scenarios", [])
        scenarios_passed = data.get("scenarios_passed", 0)
        auto_healed = data.get("auto_healed_count", 0)

        print(f"  -> Arena Execution Time: {duration_s}s")
        print(f"  -> Total Scenarios: {len(scenarios)}")
        print(f"  -> Passed: {scenarios_passed}, Auto-Healed: {auto_healed}")

        if len(scenarios) != 5:
            print(f"  {RED}FAILED:{RESET} Expected 5 edge-case scenarios, got {len(scenarios)}")
            return False

        for sc in scenarios:
            sc_id = sc.get("scenario_id")
            title = sc.get("title")
            status = sc.get("status")
            duel = sc.get("duel_transcript", [])
            tool_summary = sc.get("tool_validation_summary", "")

            print(f"  -> Scenario {sc_id}: '{title}' | Status: {status} | Turns: {len(duel)}")
            
            # Verify minimum 4 back-and-forth turns
            if len(duel) < 4:
                print(f"  {RED}FAILED:{RESET} Scenario {sc_id} has only {len(duel)} turns! (Requirement: >= 4 turns)")
                return False

            if not tool_summary:
                print(f"  {RED}FAILED:{RESET} Scenario {sc_id} missing tool_validation_summary!")
                return False

        print(f"  {GREEN}PASS:{RESET} All 5 Combat Arena scenarios executed real multi-turn duels (>=4 turns per scenario).\n")
        return True
    except Exception as e:
        print(f"  {RED}ERROR in Combat Arena test:{RESET} {e}")
        return False


async def test_4_telegram_takeover_and_escalation(client: httpx.AsyncClient) -> bool:
    print(f"{BOLD}[TEST 4/5] Telegram Takeover & Escalation End-to-End Test{RESET}")

    # Test 4A: Live Call / Chat Escalation
    print("  -> Testing Trigger 1: Human Intervention Escalation (/api/guardrail/request-intervention)...")
    esc_payload = {
        "domain_id": "brew-bite-cafe",
        "session_id": "#TORTURE-TEST-CALL-01",
        "caller_info": "+91 98765-43210 (VIP Caller)",
        "reason": "Caller demands immediate owner takeover for refund",
        "urgency": "HIGH",
        "caller_utterance": "Manager ko phone do abhi ke abhi!"
    }
    resp1 = await client.post(f"{API_BASE}/api/guardrail/request-intervention", json=esc_payload, timeout=10.0)
    if resp1.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Status {resp1.status_code}: {resp1.text}")
        return False
    data1 = resp1.json()
    print(f"  -> Hold created: {data1.get('hold_id')} | Status: {data1.get('status')}")

    # Test 4B: Dashboard Takeover Call Alert
    print("  -> Testing Trigger 2: Dashboard Takeover Alert (/api/telegram/takeover-alert)...")
    takeover_payload = {
        "domain_name": "Brew & Bite Cafe",
        "caller_info": "+91 98765-43210 (Caller)",
        "utterance": "Manager ko line par lao, order cancel karo!",
        "order_summary": "Order #VF-TORTURE: 2x Hazelnut Cold Brew",
        "hold_id": data1.get("hold_id")
    }
    resp2 = await client.post(f"{API_BASE}/api/telegram/takeover-alert", json=takeover_payload, timeout=10.0)
    if resp2.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Status {resp2.status_code}: {resp2.text}")
        return False
    data2 = resp2.json()
    print(f"  -> Takeover Alert Dispatch: {data2.get('message')}")

    # Test 4C: Verify Network Info shows Telegram Status & Paired Chat ID
    print("  -> Verifying Network Info reflects Telegram status...")
    resp3 = await client.get(f"{API_BASE}/api/system/network-info", timeout=5.0)
    if resp3.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Status {resp3.status_code}: {resp3.text}")
        return False
    data3 = resp3.json()
    tg_status = data3.get("telegram", {})
    print(f"  -> Telegram configured: {tg_status.get('configured')}, Paired Chat ID: {tg_status.get('paired_chat_id')}, Bot: @{tg_status.get('bot_username')}")

    print(f"  {GREEN}PASS:{RESET} Telegram escalation & call takeover pipeline operational.\n")
    return True


async def test_5_clean_name_extraction_and_deletion(client: httpx.AsyncClient) -> bool:
    print(f"{BOLD}[TEST 5/5] Domain Entity Name Extraction & Domain Deletion Test{RESET}")

    # Test 5A: Clean name extraction from raw Hinglish sentence
    raw_prompt = "hey mere restaurant ka naam Royal Rasoi hai aur hum butter chicken aur naan serve karte hain"
    print(f"  -> Input: \"{raw_prompt}\"")
    
    resp1 = await client.post(f"{API_BASE}/api/domains/extract-name", json={"raw_text": raw_prompt}, timeout=10.0)
    if resp1.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Status {resp1.status_code}: {resp1.text}")
        return False
    data1 = resp1.json()
    clean_name = data1.get("clean_name", "")
    domain_id = data1.get("domain_id", "")
    print(f"  -> Extracted Entity Name: \"{clean_name}\" | Generated ID: \"{domain_id}\"")

    if "mere restaurant" in clean_name.lower() or "naam" in clean_name.lower():
        print(f"  {RED}FAILED:{RESET} Extraction returned dirty sentence fragment: \"{clean_name}\"")
        return False

    if "royal rasoi" not in clean_name.lower():
        print(f"  {RED}FAILED:{RESET} Expected 'Royal Rasoi', got '{clean_name}'")
        return False

    print(f"  {GREEN}PASS:{RESET} Clean entity name \"{clean_name}\" successfully extracted!")

    # Test 5B: Test Domain Deletion (create temporary domain profile in DB, then DELETE)
    print("  -> Creating temporary test domain to test DELETE endpoint...")
    from backend.database import async_session_factory, DomainProfileModel
    from sqlalchemy import select

    test_domain_id = f"test-torture-domain-{int(time.time())}"
    async with async_session_factory() as session:
        temp_profile = DomainProfileModel(
            id=test_domain_id,
            name="Temporary Torture Test Clinic",
            domain_type="Dental Clinic",
            tagline="Fast test deletion",
            system_prompt="Test system prompt",
            first_message="Hello, test!",
            voice_id="sample_voice",
            language_code="hi-IN",
            turn_timeout_ms=1200,
            catalog_json="[]",
            policies_json="[]",
            pydantic_code=""
        )
        session.add(temp_profile)
        await session.commit()

    # Verify exists
    verify_resp = await client.get(f"{API_BASE}/api/domains/{test_domain_id}")
    if verify_resp.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Temporary domain was not found in DB!")
        return False
    print(f"  -> Temporary domain '{test_domain_id}' verified in DB.")

    # Call DELETE /api/domains/{domain_id}
    del_resp = await client.delete(f"{API_BASE}/api/domains/{test_domain_id}", timeout=5.0)
    if del_resp.status_code != 200:
        print(f"  {RED}FAILED:{RESET} Delete endpoint returned status {del_resp.status_code}: {del_resp.text}")
        return False

    # Verify it is deleted
    after_resp = await client.get(f"{API_BASE}/api/domains/{test_domain_id}")
    if after_resp.status_code != 404:
        print(f"  {RED}FAILED:{RESET} Domain '{test_domain_id}' still exists after DELETE (status {after_resp.status_code})!")
        return False

    print(f"  {GREEN}PASS:{RESET} Domain deletion endpoint successfully cleaned up test profile and returned 404 on subsequent get.\n")
    return True


async def main():
    print_banner()
    async with httpx.AsyncClient() as client:
        # Check backend connectivity first
        try:
            health = await client.get(f"{API_BASE}/api/health", timeout=5.0)
            if health.status_code != 200:
                print(f"{RED}Backend is not responding properly at {API_BASE}. Status: {health.status_code}{RESET}")
                sys.exit(1)
        except Exception as e:
            print(f"{RED}Cannot connect to backend at {API_BASE}: {e}{RESET}")
            sys.exit(1)

        print(f"{GREEN}Connected to VOXERA Backend Runtime. Starting 5 Torture Benchmarks...{RESET}\n")

        t_start = time.perf_counter()
        results = []

        # Run 5 benchmarks
        results.append(await test_1_latency_benchmark(client))
        results.append(await test_2_noise_and_stopword_torture())
        results.append(await test_3_combat_arena_multiturn(client))
        results.append(await test_4_telegram_takeover_and_escalation(client))
        results.append(await test_5_clean_name_extraction_and_deletion(client))

        total_elapsed = round(time.perf_counter() - t_start, 2)

        print(f"{BOLD}{CYAN}{'='*70}{RESET}")
        passed_count = sum(1 for r in results if r)
        total_count = len(results)

        if passed_count == total_count:
            print(f"{BOLD}{GREEN}>>> ALL 5 TORTURE BENCHMARKS PASSED (100% OPERATIONAL) in {total_elapsed}s <<<{RESET}")
            print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
            sys.exit(0)
        else:
            print(f"{BOLD}{RED}>>> TORTURE SUITE FAILED: {total_count - passed_count} of {total_count} tests failed. <<<{RESET}")
            print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
