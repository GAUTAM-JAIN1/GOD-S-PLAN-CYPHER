import time
import re
import uuid
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timezone

logger = logging.getLogger("voxera.brutal_shield")

DB_PATH = "voxera.db"

# -------------------------------------------------------------
# 1. HARDWARE WEBRTC NOISE GATE & 2-WORD MEANINGFUL BARGE-IN
# -------------------------------------------------------------
STOP_KEYWORDS = {
    "ruko", "wait", "cancel", "stop", "hold", "nahi", 
    "bhaiya suno", "arre suno", "suno", "chup", "ek minute"
}

FILLER_NOISE_TOKENS = {
    "hmm", "uh", "uhh", "haan", "ok", "okay", "achha", 
    "the", "aah", "um", "er", "oh", "ha", "ji", "hmmm"
}

def is_meaningful_barge_in(transcript: str, rms_db: float = -20.0) -> bool:
    """
    Decides whether a user utterance is loud and meaningful enough to interrupt active AI speech.
    1. Real-Time -35dB RMS Energy Gate: Rejects quieter audio frames.
    2. Explicit Stop Keywords: Immediately allows barge-in (e.g. 'ruko', 'wait', 'cancel', 'stop').
    3. 2-Word Filter: Rejects single-word filler/noise ('hmm', 'uh', 'uhh', 'haan', 'ok', 'the').
    """
    if rms_db < -35.0:
        return False

    clean = transcript.strip().lower()
    if not clean:
        return False

    # Check explicit stop keywords
    for kw in STOP_KEYWORDS:
        if kw in clean:
            return True

    words = [w for w in re.findall(r'\b[a-zA-Z\u0900-\u097F]+\b', clean) if w]
    if len(words) < 2:
        return False

    # If all words are noise/fillers, reject
    if all(w in FILLER_NOISE_TOKENS for w in words):
        return False

    return True

# -------------------------------------------------------------
# 2. PRE-LLM BRUTALSHIELD FLOOD & PROMPT-INJECTION KILL-SWITCH
# -------------------------------------------------------------
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"jailbreak",
    r"repeat\s+after\s+me",
    r"you\s+are\s+now",
    r"developer\s+mode",
    r"prompt\s+injection",
    r"bypass\s+security",
    r"pretend\s+you\s+are",
    r"dump\s+instructions",
    r"extract\s+system\s+prompt"
]

class BrutalShieldManager:
    def __init__(self):
        self.session_timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.blacklisted_sessions: set = set()
        self.off_topic_strikes: Dict[str, int] = defaultdict(int)
        self.consecutive_valid_turns: Dict[str, int] = defaultdict(int)

    def log_shield_termination_to_db(self, session_id: str, domain_id: str, reason: str, action: str):
        """Persists termination entry directly to SQLite ledger_entries."""
        try:
            conn = sqlite3.connect(DB_PATH)
            entry_id = f"#SHIELD-{uuid.uuid4().hex[:8]}"
            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()
            time_str = now.strftime("%H:%M:%S")
            conn.execute("""
                INSERT INTO ledger_entries 
                (id, session_id, domain_id, caller_phone, caller_language, verified_order_summary, 
                 total_amount_inr, phonetic_score, resolution_badge, details_json, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                session_id,
                domain_id or "system",
                "+91 Security Shield",
                "English/Hinglish",
                f"[{action}]: {reason}",
                0.0,
                0.0,
                action,
                f'{{"reason": "{reason}", "badge": "{action}"}}',
                time_str,
                now_iso
            ))
            conn.commit()
            conn.close()
            logger.info(f"Recorded {action} for session {session_id} in SQLite ledger_entries.")
        except Exception as e:
            logger.error(f"Failed to log shield termination to SQLite: {e}")

    def check_brutal_shield(self, session_id: str, utterance: str, domain_id: str = "") -> Dict[str, Any]:
        """
        0ms Pre-LLM Security Gate.
        Returns: { 'blocked': bool, 'status': str, 'reason': str, 'call_terminated': bool, 'reply': str }
        """
        now = time.perf_counter()

        if session_id in self.blacklisted_sessions:
            return {
                "blocked": True,
                "status": "SESSION_BLACKLISTED",
                "reason": "SESSION_PREVIOUSLY_TERMINATED",
                "call_terminated": True,
                "reply": "Call has been terminated by the security shield."
            }

        # 1. Rate Velocity / Flood Check: > 3 requests in 4.0 seconds
        dq = self.session_timestamps[session_id]
        # Purge timestamps older than 4.0s
        while dq and (now - dq[0]) > 4.0:
            dq.popleft()
        dq.append(now)

        if len(dq) > 3:
            self.blacklisted_sessions.add(session_id)
            self.log_shield_termination_to_db(
                session_id=session_id,
                domain_id=domain_id,
                reason="High-velocity request spam (>3 reqs in 4.0s)",
                action="TERMINATED BY SHIELD"
            )
            return {
                "blocked": True,
                "status": "FLOOD_BLOCKED",
                "reason": "RAPID_FIRE_FLOOD_ATTACK",
                "call_terminated": True,
                "reply": "Call terminated: Flood attack rate limit exceeded."
            }

        # 2. Prompt Injection Scanner
        clean = utterance.strip().lower()
        for pat in PROMPT_INJECTION_PATTERNS:
            if re.search(pat, clean):
                self.blacklisted_sessions.add(session_id)
                self.log_shield_termination_to_db(
                    session_id=session_id,
                    domain_id=domain_id,
                    reason=f"Prompt injection pattern matched: '{pat}'",
                    action="TERMINATED BY SHIELD"
                )
                return {
                    "blocked": True,
                    "status": "PROMPT_INJECTION_BLOCKED",
                    "reason": "PROMPT_INJECTION_ATTACK",
                    "call_terminated": True,
                    "reply": "Security alert: Prompt injection detected. Call terminated."
                }

        return {"blocked": False}

    def evaluate_off_topic_strike(
        self,
        session_id: str,
        utterance: str,
        domain_name: str,
        domain_type: str = "business",
        domain_id: str = ""
    ) -> Dict[str, Any]:
        """
        Enforces 2-Strike Off-Topic Call Termination Law.
        Strike 1: Polite redirect to business domain.
        Strike 2: Immediate terminate_call(reason="OFF_TOPIC_2_STRIKES") + SQLite record.
        """
        clean = utterance.strip().lower()
        off_topic_keywords = [
            "virat kohli", "cricket", "ipl", "score", "match", 
            "python", "bubble sort", "binary search", "coding", "javascript", 
            "algorithm", "write code", "weather", "politics", "election", 
            "bjp", "congress", "who will win", "are you chatgpt", "chatgpt", 
            "openai", "stock market", "relationship advice", "girlfriend", 
            "boyfriend", "math homework", "solve equation"
        ]

        is_off_topic = any(kw in clean for kw in off_topic_keywords)

        if is_off_topic:
            self.off_topic_strikes[session_id] += 1
            self.consecutive_valid_turns[session_id] = 0
            strike_count = self.off_topic_strikes[session_id]

            if strike_count == 1:
                return {
                    "is_off_topic": True,
                    "strike": 1,
                    "call_terminated": False,
                    "reason": "OFF_TOPIC_STRIKE_1",
                    "reply": f"Maaf kijiyega, yeh {domain_name} ki official line hai. Main sirf hamare menu aur services mein madad kar sakti hu."
                }
            else:
                self.blacklisted_sessions.add(session_id)
                self.log_shield_termination_to_db(
                    session_id=session_id,
                    domain_id=domain_id,
                    reason="Persistent off-topic queries reached Strike 2",
                    action="CALL ENDED (OFF-TOPIC)"
                )
                return {
                    "is_off_topic": True,
                    "strike": strike_count,
                    "call_terminated": True,
                    "reason": "OFF_TOPIC_2_STRIKES",
                    "reply": "Aapki baat hamare business se related nahi hai, isliye main yeh call end kar rahi hu. Dhanyawad!"
                }
        else:
            # In-domain turn -> apply decay (-1 strike per 3 valid turns)
            self.consecutive_valid_turns[session_id] += 1
            if self.consecutive_valid_turns[session_id] >= 3 and self.off_topic_strikes[session_id] > 0:
                self.off_topic_strikes[session_id] -= 1
                self.consecutive_valid_turns[session_id] = 0

            return {
                "is_off_topic": False,
                "strike": self.off_topic_strikes[session_id],
                "call_terminated": False,
                "reason": None,
                "reply": None
            }

brutal_shield = BrutalShieldManager()
