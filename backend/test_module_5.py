"""
Voxera Module 5 End-to-End Verification Test Suite
Adversarial Gauntlet & Self-Healing Prompt Patcher (3-Agent Groq Loop)
Zero Mocks — Real SQLite Database, Real Multi-Scenario Engine, Real Phonetic Guardrail Tool, Real Auto-Patching
"""

import sys
import os
import asyncio
import json
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import DomainProfileModel, GauntletRunModel
from backend.services.gauntlet_runner import gauntlet_runner_service, AUTO_HEAL_RULE_PREFIX
from backend.services.phonetic_guardrail import calculate_entity_match_score

BASE_URL = "http://127.0.0.1:8000"

async def run_all_tests():
    print("=" * 80)
    print("VOXERA MODULE 5: PRE-DEPLOY ADVERSARIAL GAUNTLET & SELF-HEALING VERIFICATION")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///voxera.db")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # -------------------------------------------------------------
    # TEST 1: Full 3-Scenario Gauntlet Execution (Cafe Domain)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing 3-Scenario Adversarial Gauntlet against 'brew-bite-cafe'...")
    await gauntlet_runner_service.reset_domain_vulnerability("brew-bite-cafe")
    cafe_result = await gauntlet_runner_service.run_gauntlet(
        domain_id="brew-bite-cafe",
        force_vulnerability_demo=True
    )

    print(f"  -> Run ID: {cafe_result.run_id}")
    print(f"  -> Scenarios Passed: {cafe_result.scenarios_passed} / 3")
    print(f"  -> Auto-Healed Leaks: {cafe_result.auto_healed_count}")
    print(f"  -> Mean Latency: {cafe_result.mean_latency_ms}ms")

    assert cafe_result.scenarios_passed == 3, "All 3 scenarios must pass or be auto-healed!"
    assert len(cafe_result.scenarios) == 3, "Must return exactly 3 scenarios!"

    s1 = cafe_result.scenarios[0]
    s2 = cafe_result.scenarios[1]
    s3 = cafe_result.scenarios[2]

    print(f"\n  Scenario 1: {s1.title} -> Status: {s1.status}")
    print(f"    Attacker: \"{s1.attacker_utterance}\"")
    print(f"    Post-Patch Response: \"{s1.post_patch_agent_response.replace('₹', 'Rs.')}\"")
    assert s1.status == "AUTO-PATCHED", f"Scenario 1 must be AUTO-PATCHED, got {s1.status}"
    assert s1.vulnerability_detected is True, "Vulnerability must be detected in demo mode!"
    assert s1.patched_guardrail_rule is not None
    assert AUTO_HEAL_RULE_PREFIX in s1.patched_guardrail_rule

    print(f"\n  Scenario 2: {s2.title} -> Status: {s2.status}")
    print(f"    Tool Validation: {s2.tool_validation_summary.replace('₹', 'Rs.')}")
    assert s2.status == "PASS"

    print(f"\n  Scenario 3: {s3.title} -> Status: {s3.status}")
    print(f"    Tool Validation: {s3.tool_validation_summary.replace('₹', 'Rs.')}")
    assert s3.status == "PASS"

    print("  [PASS] Test 1: Full 3-Scenario Gauntlet execution completed cleanly.")

    # -------------------------------------------------------------
    # TEST 2: Real Self-Healing Auto-Patch Injection into SQLite
    # -------------------------------------------------------------
    print("\n[TEST 2] Verifying Physical Auto-Patch Injection in SQLite 'domain_profiles'...")
    async with async_session() as db:
        stmt = select(DomainProfileModel).where(DomainProfileModel.id == "brew-bite-cafe")
        profile = (await db.execute(stmt)).scalar_one_or_none()
        assert profile is not None, "Domain profile must exist in SQLite!"

        policies = json.loads(profile.policies_json or "[]")
        has_auto_heal_policy = any(AUTO_HEAL_RULE_PREFIX in p.get("rule", "") for p in policies)
        print(f"  -> Total Strict Policies in DB: {len(policies)}")
        print(f"  -> Auto-Healed Rule in Policies: {has_auto_heal_policy}")
        assert has_auto_heal_policy, "Auto-healed policy must be physically persisted in policies_json!"

        has_auto_heal_prompt = AUTO_HEAL_RULE_PREFIX in profile.system_prompt
        print(f"  -> Auto-Healed Rule in System Prompt: {has_auto_heal_prompt}")
        assert has_auto_heal_prompt, "Auto-healed rule must be appended to system_prompt!"

    print("  [PASS] Test 2: Physical auto-patch in SQLite database verified.")

    # -------------------------------------------------------------
    # TEST 3: Full 3-Scenario Gauntlet Execution (Dental Domain via HTTP API)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Gauntlet HTTP API on 'smilecare-dental'...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        await client.post("/api/gauntlet/reset-vulnerability", json={"domain_id": "smilecare-dental"})
        res = await client.post("/api/gauntlet/run", json={
            "domain_id": "smilecare-dental",
            "force_vulnerability_demo": True
        })
        assert res.status_code == 200, f"Gauntlet API failed: {res.text}"
        dental_data = res.json()
        print(f"  -> Dental Run ID: {dental_data['run_id']}")
        print(f"  -> Scenarios Passed: {dental_data['scenarios_passed']}")
        assert dental_data["scenarios_passed"] == 3

        d_s1 = dental_data["scenarios"][0]
        print(f"  -> Dental Scenario 1 Attacker: \"{d_s1['attacker_utterance']}\"")
        assert "Dr. Sharma" in d_s1["attacker_utterance"] or "Root Canal" in d_s1["attacker_utterance"]
        assert d_s1["status"] == "AUTO-PATCHED"

    print("  [PASS] Test 3: Domain-specific dental gauntlet executed via REST API.")

    # -------------------------------------------------------------
    # TEST 4: Persistence and Retrieval via GET /api/gauntlet/latest
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Gauntlet Run Persistence & Retrieval via GET /api/gauntlet/latest...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.get("/api/gauntlet/latest?domain_id=brew-bite-cafe")
        assert res.status_code == 200, f"Latest gauntlet endpoint failed: {res.text}"
        latest_data = res.json()
        print(f"  -> Has Run: {latest_data.get('has_run')}")
        print(f"  -> Latest Run ID: {latest_data.get('run_id')}")
        assert latest_data.get("has_run") is True
        assert latest_data.get("domain_id") == "brew-bite-cafe"
        assert len(latest_data.get("scenarios", [])) == 3

        # Verify SQLite gauntlet_runs table has real row
        async with async_session() as db:
            stmt = select(GauntletRunModel).where(GauntletRunModel.domain_id == "brew-bite-cafe")
            runs = (await db.execute(stmt)).scalars().all()
            print(f"  -> Total Gauntlet Runs in SQLite: {len(runs)}")
            assert len(runs) >= 1, "Must have at least 1 persisted gauntlet run in SQLite!"

    print("  [PASS] Test 4: Gauntlet run persistence and retrieval verified.")

    # -------------------------------------------------------------
    # TEST 5: Reset Vulnerability (Stage Demo Mode)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Reset Vulnerability Endpoint (Stage Demo Reset)...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.post("/api/gauntlet/reset-vulnerability", json={
            "domain_id": "brew-bite-cafe"
        })
        assert res.status_code == 200, f"Reset vulnerability failed: {res.text}"
        reset_data = res.json()
        print(f"  -> Reset Message: {reset_data.get('message')}")
        assert reset_data.get("success") is True

        # Verify SQLite profile no longer has [AUTO-HEALED GUARDRAIL]
        async with async_session() as db:
            stmt = select(DomainProfileModel).where(DomainProfileModel.id == "brew-bite-cafe")
            profile = (await db.execute(stmt)).scalar_one_or_none()
            policies = json.loads(profile.policies_json or "[]")
            has_auto_heal = any(AUTO_HEAL_RULE_PREFIX in p.get("rule", "") for p in policies)
            prompt_has_heal = AUTO_HEAL_RULE_PREFIX in profile.system_prompt
            print(f"  -> After Reset: Policy in policies_json = {has_auto_heal}, in system_prompt = {prompt_has_heal}")
            assert not has_auto_heal, "Auto-healed policy must be removed after reset!"
            assert not prompt_has_heal, "Auto-healed prompt must be cleaned after reset!"

    print("  [PASS] Test 5: Reset vulnerability verified. Ready for repeated live stage demonstrations.")

    print("\n" + "=" * 80)
    print("ALL 5 MODULE 5 VERIFICATION TESTS PASSED 100%! ZERO MOCKS.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
