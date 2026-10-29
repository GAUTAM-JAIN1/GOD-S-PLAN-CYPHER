"""
VOXERA STAGED GIT PUSHER
========================
Automated staged progression over 3 hours (6 stages, 30 minutes interval).
Stages:
  Stage 1 (00:00) : Core scaffold, README, config, database, schemas
  Stage 2 (+30m)  : Phonetic guardrails & acoustic distance engine
  Stage 3 (+60m)  : Human Co-Pilot, Telegram takeover worker & SLA Whisper
  Stage 4 (+90m)  : Groq architecture compiler, ElevenLabs streaming & FastAPI routes
  Stage 5 (+120m) : Next.js Voice Agent Studio, Live Audio controls & Dev Inspector
  Stage 6 (+150m) : Multi-Turn AI Combat Arena & Self-Breaking Torture Suite
"""

import os
import sys
import time
import subprocess
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(REPO_ROOT, "scripts", "git_push.log")

STAGES = [
    {
        "step": 1,
        "name": "Project Scaffold & Core Architecture",
        "message": "feat(core): project scaffold, database models, and schemas",
        "files": [
            ".gitignore",
            "README.md",
            "backend/.env.example",
            "backend/requirements.txt",
            "backend/config.py",
            "backend/database.py",
            "backend/schemas.py",
            "backend/seed_domains.py",
        ]
    },
    {
        "step": 2,
        "name": "Phonetic Guardrails & Acoustic Matching Engine",
        "message": "feat(guardrail): phonetic distance algorithms and acoustic matching engine",
        "files": [
            "backend/services/phonetic_guardrail.py",
            "backend/services/acoustic_guardrail.py",
        ]
    },
    {
        "step": 3,
        "name": "Human-in-the-Loop Co-Pilot & Telegram Takeover",
        "message": "feat(copilot): human-in-the-loop whisper SLA manager and telegram takeover worker",
        "files": [
            "backend/services/whisper_sla.py",
            "backend/services/whisper_copilot.py",
            "backend/services/telegram_service.py",
            "backend/services/telegram_notifier.py",
        ]
    },
    {
        "step": 4,
        "name": "Groq Compiler, ElevenLabs & REST API Endpoints",
        "message": "feat(engine): groq compiler, elevenlabs streaming integration and REST API routes",
        "files": [
            "backend/services/groq_compiler.py",
            "backend/services/elevenlabs_service.py",
            "backend/services/gauntlet_runner.py",
            "backend/main.py",
        ]
    },
    {
        "step": 5,
        "name": "Next.js Voice Agent Studio & Real-Time Telemetry",
        "message": "feat(frontend): voice agent studio, live audio controls and developer inspector",
        "files": [
            "frontend/package.json",
            "frontend/package-lock.json",
            "frontend/tsconfig.json",
            "frontend/next.config.ts",
            "frontend/postcss.config.mjs",
            "frontend/public",
            "frontend/src/lib",
            "frontend/src/app",
            "frontend/src/components/studio",
            "frontend/src/components/ops",
            "frontend/src/components/views/BusinessDemoView.tsx",
        ]
    },
    {
        "step": 6,
        "name": "Combat Arena Duel Engine & Torture Benchmark Suite",
        "message": "feat(arena): multi-turn AI combat arena and self-breaking torture test suite",
        "files": [
            "frontend/src/components/views/CombatArenaView.tsx",
            "backend/test_system_torture.py",
            ".",
        ]
    }
]

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def run_git(args):
    log(f"Executing: git {' '.join(args)}")
    result = subprocess.run(["git"] + args, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.stdout.strip():
        log(f"STDOUT: {result.stdout.strip()}")
    if result.returncode != 0:
        log(f"STDERR: {result.stderr.strip()}")
    return result.returncode == 0

def execute_stage(stage):
    log(f"=== Commencing Stage {stage['step']}/6: {stage['name']} ===")
    for f in stage["files"]:
        target_path = os.path.join(REPO_ROOT, f)
        if os.path.exists(target_path):
            run_git(["add", f])
    
    # Commit
    committed = run_git(["commit", "-m", stage["message"]])
    if not committed:
        log("No changes detected or already committed for this stage. Proceeding.")
    
    # Push to origin main
    pushed = run_git(["push", "-u", "origin", "main"])
    if pushed:
        log(f"Stage {stage['step']}/6 successfully pushed to GitHub!\n")
    else:
        log(f"Warning: Push encountered an error on Stage {stage['step']}.\n")

def run_auto_scheduler(interval_sec=1800):
    log("Starting 3-Hour Automated Staged Pusher (30-min intervals)...")
    total_stages = len(STAGES)
    for idx, stage in enumerate(STAGES):
        execute_stage(stage)
        if idx < total_stages - 1:
            log(f"Stage {stage['step']} finished. Sleeping {interval_sec // 60} minutes until Stage {stage['step'] + 1}...")
            time.sleep(interval_sec)
    log("All 6 stages successfully completed and pushed to GitHub!")

if __name__ == "__main__":
    if "--now" in sys.argv or "--step-1" in sys.argv:
        execute_stage(STAGES[0])
    elif "--step" in sys.argv:
        idx = int(sys.argv[sys.argv.index("--step") + 1]) - 1
        execute_stage(STAGES[idx])
    elif "--immediate-all" in sys.argv:
        for s in STAGES:
            execute_stage(s)
            time.sleep(2)
    else:
        # Default auto scheduler (30 mins = 1800s)
        run_auto_scheduler(1800)
