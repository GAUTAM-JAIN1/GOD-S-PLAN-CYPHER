"""
VOXERA MODULE 7: 3-PHASE AGENT TEST SUITE CLI RUNNER
=====================================================
100% Real Code, Zero Mocks.
Executes:
Phase 1: In-Domain Test (Happy Path + Info Missing Hallucination Gate)
Phase 2: Out-of-Domain Strike Ladder (Strikes 1-4 + Decay Mechanism)
Phase 3: Brutal Attack & Cost Shield (3A Security + 3B Cost Shield)
"""

import asyncio
import sys
import os
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db
from backend.services.module_7_test_suite import run_master_module_7_suite

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

async def main():
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}   VOXERA MODULE 7: 3-PHASE COMPREHENSIVE AGENT TEST SUITE   {RESET}")
    print(f"{BOLD}{CYAN}   (In-Domain, Strike Ladder, Brutal Attacks & Cost Shield)   {RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

    await init_db()
    domain_id = "brew-bite-cafe"
    if len(sys.argv) > 1:
        domain_id = sys.argv[1]

    print(f"Target Active Domain: {BOLD}{domain_id}{RESET}")
    t0 = time.perf_counter()

    try:
        report = await run_master_module_7_suite(domain_id)
    except Exception as e:
        print(f"{RED}Fatal execution error: {e}{RESET}")
        sys.exit(1)

    total_time = time.perf_counter() - t0

    # Phase 1 Summary
    p1 = report["phases"]["phase_1_in_domain"]
    print(f"\n{BOLD}[PHASE 1: IN-DOMAIN TEST SUITE]{RESET} ({p1['elapsed_ms']}ms)")
    print(f"  Passed: {GREEN}{p1['passed_tests']}/{p1['total_tests']}{RESET}")
    for res in p1["results"]:
        status = f"{GREEN}PASS{RESET}" if res["passed"] else f"{RED}FAIL{RESET}"
        print(f"    [{status}] {res['name']} ({res['latency_ms']}ms) -> {res['details']}")

    # Phase 2 Summary
    p2 = report["phases"]["phase_2_out_of_domain"]
    print(f"\n{BOLD}[PHASE 2: OUT-OF-DOMAIN STRIKE LADDER & DECAY]{RESET} ({p2['elapsed_ms']}ms)")
    print(f"  Passed: {GREEN}{p2['passed_tests']}/{p2['total_tests']}{RESET}")
    for res in p2["results"]:
        status = f"{GREEN}PASS{RESET}" if res["passed"] else f"{RED}FAIL{RESET}"
        print(f"    [{status}] {res['name']} ({res['latency_ms']}ms) -> {res['details']}")

    # Phase 3 Summary
    p3 = report["phases"]["phase_3_brutal_attack"]
    print(f"\n{BOLD}[PHASE 3: BRUTAL ATTACK & COST SHIELD]{RESET} ({p3['elapsed_ms']}ms)")
    print(f"  Passed: {GREEN}{p3['passed_tests']}/{p3['total_tests']}{RESET}")
    for res in p3["results"]:
        status = f"{GREEN}PASS{RESET}" if res["passed"] else f"{RED}FAIL{RESET}"
        print(f"    [{status}] {res['name']} ({res['latency_ms']}ms) -> {res['details']}")

    # Final Verdict
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    all_passed = (report["failed_tests"] == 0)
    verdict_color = GREEN if all_passed else RED
    verdict_text = "PASSED ALL PHASES" if all_passed else "FAILURES DETECTED"
    print(f"{BOLD}FINAL VERDICT: {verdict_color}{verdict_text}{RESET} ({report['passed_tests']}/{report['total_tests']} tests passed, {report['pass_percentage']}%)")
    print(f"Total Execution Time: {total_time:.2f}s")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
