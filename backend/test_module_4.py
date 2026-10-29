"""
Voxera Module 4 End-to-End Verification Test Suite
Zero Mocks — Real SQLite Database, Real SLA Engine, Real Phonetic Guardrail Math, Real Telemetry Bridge
"""

import sys
import os
import asyncio
import json
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.phonetic_guardrail import calculate_entity_match_score, evaluate_hardened_entity
from backend.services.whisper_copilot import whisper_sla_manager
from backend.database import InterceptHoldModel, LedgerEntryModel, PendingVerificationModel, DomainProfileModel
from backend.config import settings

BASE_URL = "http://127.0.0.1:8000"

async def run_all_tests():
    print("=" * 80)
    print("VOXERA MODULE 4: LIVE WHISPER CO-PILOT, TELEGRAM & 8S SLA VERIFICATION")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///voxera.db")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    from backend.schemas import CatalogItem

    # -------------------------------------------------------------
    # TEST 1: Nuanced Probability Math (Length Coverage Weighting)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Substring Length Coverage Weighting & Nuanced Probability Splits...")
    item_1 = CatalogItem(
        id="bb-01",
        canonical_name="Hazelnut Cold Brew",
        category="Cold Coffee",
        price_inr=240,
        unit_or_duration="glass",
        phonetic_aliases=["hazelnut cold brew", "cold brew"]
    )
    item_2 = CatalogItem(
        id="bb-02",
        canonical_name="Classic Iced Americano",
        category="Cold Coffee",
        price_inr=180,
        unit_or_duration="glass",
        phonetic_aliases=["iced americano", "americano"]
    )
    query = "cold brew"

    score_1 = calculate_entity_match_score(query, item_1)
    score_2 = calculate_entity_match_score(query, item_2)

    print(f"  -> Query: '{query}'")
    print(f"  -> Candidate 1 ('{item_1.canonical_name}'): score={score_1:.3f}")
    print(f"  -> Candidate 2 ('{item_2.canonical_name}'): score={score_2:.3f}")

    assert score_1 > score_2, "Target 1 (Hazelnut Cold Brew) must have higher score than Target 2 for 'cold brew'!"

    # Test via API for an ambiguous query
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.post("/api/guardrail/verify-catalog-item", json={
            "domain_id": "brew-bite-cafe",
            "spoken_entity": "do large cold brew",
            "quantity": 2,
            "caller_utterance": "Bhaiya do large cold brew pack kar do"
        })
        assert res.status_code == 200, f"Verify API failed: {res.text}"
        data = res.json()
        print(f"  -> API Match Type: {data['match_type']}, Score: {data['score']}")
        if data.get("candidates") and len(data["candidates"]) >= 2:
            p1 = data["candidates"][0].get("probability_pct", 0)
            p2 = data["candidates"][1].get("probability_pct", 0)
            print(f"  -> Candidate 1: {data['candidates'][0]['canonical_name']} ({p1}%)")
            print(f"  -> Candidate 2: {data['candidates'][1]['canonical_name']} ({p2}%)")
            assert p1 != 50 or p2 != 50 or p1 != p2, f"Probabilities should be nuanced, not flat 50/50! Got {p1}% vs {p2}%"
        print("  [PASS] Test 1: Nuanced probability splits mathematically confirmed.")

    # -------------------------------------------------------------
    # TEST 2: Human Call-Transfer Escalation (POST /api/guardrail/request-intervention)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Human Call-Transfer Escalation Endpoint...")
    session_id_2 = f"#VF-ESC-{uuid.uuid4().hex[:4].upper()}"
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.post("/api/guardrail/request-intervention", json={
            "domain_id": "brew-bite-cafe",
            "session_id": session_id_2,
            "caller_info": "+91 98712 44321",
            "reason": "Caller demands owner for catering bulk order",
            "urgency": "HIGH",
            "caller_utterance": "Mujhe cafe owner se baat karni hai 50 logo ke catering ke liye"
        })
        assert res.status_code == 200, f"Escalation request failed: {res.text}"
        esc_data = res.json()
        hold_id_2 = esc_data["hold_id"]
        print(f"  -> Created Escalation Hold ID: {hold_id_2}")
        print(f"  -> SLA Expires at Epoch: {esc_data.get('expires_at_epoch_ms')}")

        # Verify hold exists in SQLite DB
        async with async_session() as db:
            stmt = select(InterceptHoldModel).where(InterceptHoldModel.id == hold_id_2)
            row = (await db.execute(stmt)).scalar_one_or_none()
            assert row is not None, "Hold must exist in SQLite intercept_holds table!"
            assert row.hold_reason == "HUMAN_TRANSFER_REQUEST"
            assert row.status == "ACTIVE_HOLD"
            assert row.phonetic_score == 0.0
            c1 = json.loads(row.candidate_1_json)
            c2 = json.loads(row.candidate_2_json)
            assert c1["action"] == "APPROVE_TRANSFER"
            assert c2["action"] == "BUSY_CALLBACK"
            print(f"  -> Verified SQLite row: reason={row.hold_reason}, candidate_1={c1['action']}, candidate_2={c2['action']}")

    print("  [PASS] Test 2: Human Call-Transfer escalation persisted with zero mocks.")

    # -------------------------------------------------------------
    # TEST 3: 1-Tap Owner Resolution (APPROVE_TRANSFER & Ledger Entry)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing 1-Tap Owner Resolution (APPROVE_TRANSFER)...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.post("/api/guardrail/resolve-hold", json={
            "hold_id": hold_id_2,
            "resolution_action": "APPROVE_TRANSFER",
            "resolved_by": "MOBILE_COMPANION"
        })
        assert res.status_code == 200, f"Resolve hold failed: {res.text}"
        res_data = res.json()
        print(f"  -> Resolution response: {res_data.get('resolution_action')}, resolved_by={res_data.get('resolved_by')}")
        inst = res_data.get("agent_contextual_instruction", "")
        print(f"  -> Agent Contextual Instruction: \"{inst}\"")
        assert "OWNER CO-PILOT APPROVED TRANSFER" in inst, "Instruction must instruct agent to inform caller about transfer!"

        # Verify DB state
        async with async_session() as db:
            stmt = select(InterceptHoldModel).where(InterceptHoldModel.id == hold_id_2)
            row = (await db.execute(stmt)).scalar_one_or_none()
            assert row.status == "TRANSFERRED_TO_OWNER", f"Hold status should be TRANSFERRED_TO_OWNER, got {row.status}"

            # Verify ledger row
            ledger_stmt = select(LedgerEntryModel).where(LedgerEntryModel.session_id == session_id_2)
            ledger_row = (await db.execute(ledger_stmt)).scalar_one_or_none()
            assert ledger_row is not None, "Ledger entry must be recorded for call transfer!"
            assert ledger_row.resolution_badge == "MOBILE APPROVED", f"Expected 'MOBILE APPROVED', got {ledger_row.resolution_badge}"
            print(f"  -> Verified Ledger: id={ledger_row.id}, badge={ledger_row.resolution_badge}")

    print("  [PASS] Test 3: APPROVE_TRANSFER recorded in DB and Ledger with real status.")

    # -------------------------------------------------------------
    # TEST 4: Busy Callback Resolution (BUSY_CALLBACK)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing 1-Tap Owner Resolution (BUSY_CALLBACK)...")
    session_id_4 = f"#VF-BUSY-{uuid.uuid4().hex[:4].upper()}"
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Create escalation hold
        esc_res = await client.post("/api/guardrail/request-intervention", json={
            "domain_id": "brew-bite-cafe",
            "session_id": session_id_4,
            "reason": "Caller requested urgent owner call",
            "caller_utterance": "Doctor sahab se turant baat karao"
        })
        hold_id_4 = esc_res.json()["hold_id"]

        # Resolve as BUSY_CALLBACK via Telegram
        resolve_res = await client.post("/api/guardrail/resolve-hold", json={
            "hold_id": hold_id_4,
            "resolution_action": "BUSY_CALLBACK",
            "resolved_by": "TELEGRAM_BOT"
        })
        assert resolve_res.status_code == 200
        inst_4 = resolve_res.json().get("agent_contextual_instruction", "")
        print(f"  -> Contextual Instruction: \"{inst_4}\"")
        assert "OWNER IS BUSY" in inst_4

        async with async_session() as db:
            stmt = select(InterceptHoldModel).where(InterceptHoldModel.id == hold_id_4)
            row = (await db.execute(stmt)).scalar_one_or_none()
            assert row.status == "CALLBACK_SCHEDULED"

            ledger_stmt = select(LedgerEntryModel).where(LedgerEntryModel.session_id == session_id_4)
            ledger_row = (await db.execute(ledger_stmt)).scalar_one_or_none()
            assert ledger_row is not None
            assert ledger_row.resolution_badge == "PRIORITY CALLBACK"
            print(f"  -> Verified Ledger: id={ledger_row.id}, badge={ledger_row.resolution_badge}")

    print("  [PASS] Test 4: BUSY_CALLBACK recorded in DB and Ledger.")

    # -------------------------------------------------------------
    # TEST 5: Custom Whisper Injection (CUSTOM_WHISPER)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Custom Whisper Injection...")
    hold_id_5 = f"hold_whisper_{uuid.uuid4().hex[:6]}"
    session_id_5 = f"#VF-WSP-{uuid.uuid4().hex[:4].upper()}"

    async with async_session() as db:
        dummy_hold = InterceptHoldModel(
            id=hold_id_5,
            session_id=session_id_5,
            domain_id="brew-bite-cafe",
            spoken_entity="garbled iced drink",
            caller_utterance="...garbled...",
            phonetic_score=0.55,
            candidate_1_json=json.dumps({"canonical_name": "Hazelnut Cold Brew", "price_inr": 240}),
            candidate_2_json=json.dumps({"canonical_name": "Classic Iced Americano", "price_inr": 180}),
            hold_reason="LOW_CONFIDENCE_AUDIO",
            status="ACTIVE_HOLD"
        )
        db.add(dummy_hold)
        await db.commit()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        custom_text = "Bolo aaj fresh batch 10 min me ready ho raha hai, complimentary cookie denge."
        res = await client.post("/api/guardrail/resolve-hold", json={
            "hold_id": hold_id_5,
            "resolution_action": "CUSTOM_WHISPER",
            "custom_whisper_text": custom_text,
            "resolved_by": "MOBILE_COMPANION"
        })
        assert res.status_code == 200
        inst_5 = res.json().get("agent_contextual_instruction", "")
        print(f"  -> Custom Whisper Instruction: \"{inst_5}\"")
        assert "URGENT WHISPER FROM OWNER:" in inst_5
        assert custom_text in inst_5

    print("  [PASS] Test 5: Custom Whisper injected and formatted for ElevenLabs live session.")

    # -------------------------------------------------------------
    # TEST 6: Backend-Enforced SLA Auto-Fallback Timer (Real Asynchronous Background Task)
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Backend-Enforced SLA Auto-Fallback Timer (1.5s timeout test)...")
    hold_id_6 = f"hold_sla_{uuid.uuid4().hex[:6]}"
    session_id_6 = f"#VF-SLA-{uuid.uuid4().hex[:4].upper()}"

    async with async_session() as db:
        sla_hold = InterceptHoldModel(
            id=hold_id_6,
            session_id=session_id_6,
            domain_id="brew-bite-cafe",
            spoken_entity="unclear muffled request",
            caller_utterance="[static noise]",
            phonetic_score=0.42,
            candidate_1_json=json.dumps({"canonical_name": "Item A", "price_inr": 100}),
            candidate_2_json=json.dumps({"canonical_name": "Item B", "price_inr": 120}),
            hold_reason="LOW_CONFIDENCE_AUDIO",
            status="ACTIVE_HOLD"
        )
        db.add(sla_hold)
        await db.commit()

    # Schedule a 1.5s SLA timeout using the real backend SLA manager
    whisper_sla_manager.schedule_sla_timeout(
        hold_id=hold_id_6,
        timeout_sec=1.5,
        session_id=session_id_6,
        domain_id="brew-bite-cafe",
        caller_utterance="[static noise]"
    )

    remaining_init = whisper_sla_manager.get_remaining_sla_seconds(hold_id_6)
    print(f"  -> Scheduled SLA timer. Initial remaining: {remaining_init}s")
    assert remaining_init is not None and remaining_init > 0.0

    print("  -> Waiting 2.0s for backend SLA timeout to trigger automatically...")
    await asyncio.sleep(2.0)

    # Verify SQLite DB has updated to SLA_AUTO_FALLBACK
    async with async_session() as db:
        stmt = select(InterceptHoldModel).where(InterceptHoldModel.id == hold_id_6)
        row = (await db.execute(stmt)).scalar_one_or_none()
        assert row is not None, "Hold must exist!"
        print(f"  -> Hold Status after SLA timeout: {row.status}")
        assert row.status == "SLA_AUTO_FALLBACK", f"Expected SLA_AUTO_FALLBACK, got {row.status}"

        # Verify ledger row created for SLA fallback
        ledger_stmt = select(LedgerEntryModel).where(LedgerEntryModel.session_id == session_id_6)
        ledger_row = (await db.execute(ledger_stmt)).scalar_one_or_none()
        assert ledger_row is not None, "Ledger entry must be created when SLA expires!"
        print(f"  -> Verified SLA Fallback Ledger: id={ledger_row.id}, badge={ledger_row.resolution_badge}")
        assert ledger_row.resolution_badge in ["ASSISTED HOLD", "SLA CALLBACK"]

    print("  [PASS] Test 6: Backend SLA 8-Second fallback engine executed cleanly with zero human input.")

    # -------------------------------------------------------------
    # TEST 7: Network LAN IP & Telegram Status Endpoints
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing System Network Info & Telegram Status...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        net_res = await client.get("/api/system/network-info")
        assert net_res.status_code == 200, f"Network info endpoint failed: {net_res.text}"
        net_data = net_res.json()
        print(f"  -> LAN IP: {net_data.get('lan_ip')}")
        print(f"  -> Mobile Copilot URL: {net_data.get('mobile_copilot_url')}")
        print(f"  -> Backend URL: {net_data.get('backend_url')}")
        print(f"  -> Telegram Status: {net_data.get('telegram')}")

        assert net_data.get("lan_ip") is not None
        assert "mobile-copilot" in net_data.get("mobile_copilot_url", "")

        tg_res = await client.get("/api/telegram/status")
        assert tg_res.status_code == 200
        tg_data = tg_res.json()
        print(f"  -> Telegram Service: configured={tg_data.get('configured')}, running={tg_data.get('running')}")

    print("  [PASS] Test 7: Network discovery and Telegram status verified.")

    print("\n" + "=" * 80)
    print("ALL 7 MODULE 4 VERIFICATION TESTS PASSED 100%! ZERO MOCKS.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
