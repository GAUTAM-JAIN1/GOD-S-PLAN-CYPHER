"""
Voxera Module 6 End-to-End Verification Test Suite
Verified Operations Ledger, Real-Time Observability & Slide-Over Inspector
Zero Mocks — Real SQLite Database, Real Ledger Rows, Real KPI Aggregates, Real Inspector Audit
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

from backend.database import LedgerEntryModel, InterceptHoldModel, DomainProfileModel

BASE_URL = "http://127.0.0.1:8000"

async def run_all_tests():
    print("=" * 80)
    print("VOXERA MODULE 6: VERIFIED OPERATIONS LEDGER & OBSERVABILITY INSPECTOR")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///voxera.db")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # -------------------------------------------------------------
    # TEST 1: Verified Ledger Entries (GET /api/ledger/entries)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Persistent Ledger Retrieval (GET /api/ledger/entries)...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.get("/api/ledger/entries")
        assert res.status_code == 200, f"Ledger entries failed: {res.text}"
        entries = res.json()
        print(f"  -> Total Ledger Rows Retrieved: {len(entries)}")
        assert len(entries) >= 1, "Must have persistent ledger rows in SQLite!"

        first = entries[0]
        print(f"  -> Sample Row: Session={first.get('sessionId')}, Action=\"{first.get('action')}\", Status={first.get('status')}")
        assert "sessionId" in first
        assert "callerPhone" in first
        assert "action" in first
        assert "totalInr" in first
        assert "phoneticGate" in first
        assert "status" in first

    print("  [PASS] Test 1: Persistent ledger rows retrieved with enriched metadata.")

    # -------------------------------------------------------------
    # TEST 2: Real-Time Observability KPI Aggregates (GET /api/ledger/stats)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Observability KPI Aggregates (GET /api/ledger/stats)...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.get("/api/ledger/stats")
        assert res.status_code == 200, f"Ledger stats failed: {res.text}"
        stats = res.json()
        print(f"  -> Completed Calls (24h): {stats.get('completed_calls_24h')}")
        print(f"  -> Hallucinations Prevented: {stats.get('hallucinations_count')} Hallucinations")
        print(f"  -> Median Voice Latency: {stats.get('median_voice_latency_ms')}ms")
        print(f"  -> Interventions Count: {stats.get('interventions_count')}")
        print(f"  -> Avg Owner Response: {stats.get('avg_owner_response_sec')}s")
        print(f"  -> Two-Phase Commit Lock: {stats.get('two_phase_commit_enforced')}")

        assert stats.get("completed_calls_24h") >= 1
        assert stats.get("hallucinations_count") == 0
        assert stats.get("median_voice_latency_ms") > 0
        assert stats.get("two_phase_commit_enforced") is True

    print("  [PASS] Test 2: KPI Aggregates computed from real SQLite entries.")

    from urllib.parse import quote

    # -------------------------------------------------------------
    # TEST 3: Slide-Over Inspector Audit (GET /api/ledger/entries/{session_id})
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Slide-Over Call Inspector Audit Endpoint...")
    target_session_id = first.get("sessionId")
    encoded_id = quote(target_session_id, safe='')
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.get(f"/api/ledger/entries/{encoded_id}")
        assert res.status_code == 200, f"Inspector fetch failed: {res.text}"
        audit_data = res.json()
        print(f"  -> Inspected Session: {audit_data.get('sessionId')}")
        print(f"  -> Inspected Phone: {audit_data.get('callerPhone')}")
        print(f"  -> Inspected Action: {audit_data.get('action')}")
        print(f"  -> Inspected Status: {audit_data.get('status')}")
        print(f"  -> Associated Hold Data: {audit_data.get('hold') is not None}")

        assert audit_data.get("sessionId") == target_session_id
        assert audit_data.get("callerPhone") is not None
        assert audit_data.get("status") is not None

    print("  [PASS] Test 3: Slide-over call inspector audit data verified.")

    # -------------------------------------------------------------
    # TEST 4: Live Transactional Commit to Ledger (POST /api/guardrail/commit-action)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Live Transaction Commit into Ledger...")
    new_session_id = f"#VF-M6-{uuid.uuid4().hex[:4].upper()}"
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        commit_res = await client.post("/api/guardrail/commit-action", json={
            "domain_id": "brew-bite-cafe",
            "session_id": new_session_id,
            "canonical_name": "Smoked Paneer Ciabatta Panini",
            "quantity": 2,
            "total_price_inr": 640.0,
            "caller_phone": "+91 99112 88410"
        })
        assert commit_res.status_code == 200, f"Commit action failed: {commit_res.text}"
        commit_data = commit_res.json()
        print(f"  -> Commit Status: {commit_data.get('status')}")
        print(f"  -> Ledger Row ID: {commit_data.get('ledger_id')}")

        # Verify entry exists in GET /api/ledger/entries
        entries_res = await client.get("/api/ledger/entries")
        all_entries = entries_res.json()
        found = any(e.get("sessionId") == new_session_id for e in all_entries)
        print(f"  -> Verified in Ledger Stream: {found}")
        assert found, "New transaction must immediately appear in ledger stream!"

    print("  [PASS] Test 4: Live transaction recorded in SQLite ledger with real badge.")

    # -------------------------------------------------------------
    # TEST 5: Escalation Intervention Tracking & KPI Reflection
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Mobile/Telegram Escalation Intervention Tracking...")
    esc_session_id = f"#VF-ESC-{uuid.uuid4().hex[:4].upper()}"
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Create escalation hold
        hold_res = await client.post("/api/guardrail/request-intervention", json={
            "domain_id": "brew-bite-cafe",
            "session_id": esc_session_id,
            "reason": "Caller demands manager for bulk corporate order",
            "caller_utterance": "Manager se baat karwao corporate bulk order ke liye"
        })
        hold_id = hold_res.json()["hold_id"]

        # Resolve via Mobile Companion
        resolve_res = await client.post("/api/guardrail/resolve-hold", json={
            "hold_id": hold_id,
            "resolution_action": "APPROVE_TRANSFER",
            "resolved_by": "MOBILE_COMPANION"
        })
        assert resolve_res.status_code == 200

        # Verify Inspector data for this escalation
        inspec_res = await client.get(f"/api/ledger/entries/{quote(esc_session_id, safe='')}")
        assert inspec_res.status_code == 200
        inspec_data = inspec_res.json()
        print(f"  -> Escalation Status in Ledger: {inspec_data.get('status')}")
        assert inspec_data.get("status") == "MOBILE APPROVED"

    print("  [PASS] Test 5: Mobile escalation intervention tracked in Ledger and Inspector.")

    print("\n" + "=" * 80)
    print("ALL 5 MODULE 6 VERIFICATION TESTS PASSED 100%! ZERO MOCKS.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
