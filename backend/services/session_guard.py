"""
VOXERA SESSION GUARD & COST SHIELD (MODULE 7)
==============================================
Backend-enforced Session Integrity, Off-Topic Strike Ladder, Security Boundary & Cost Shield.
100% Real Code, Zero Mocks. Limits are strictly enforced in Python logic, never prompt-only.

Features:
1. Off-Topic Strike Ladder (Strikes 1-4 with Decay Mechanism).
2. Token/Cost Exhaustion Shield (Duration Cap, Turn Cap, Length Cap, Repeat Loop, Silence Timeout, Rate Limiting).
3. Security Boundary Validator (Two-Phase Token Integrity, Replay Defense, Cross-Domain Defense, Boundary Quantities, SQL/Injection Sanitization).
"""

import time
import re
import uuid
import logging
import asyncio
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from sqlalchemy import select
from backend.database import async_session_factory, PendingVerificationModel, DomainProfileModel
from backend.services.groq_compiler import get_groq_client, get_best_groq_model

logger = logging.getLogger("voxera.session_guard")

# Maximum parameters enforced in code
MAX_CALL_DURATION_SEC = 600.0     # 10 minutes max call duration
MAX_SESSION_TURNS = 30           # 30 turns per call max
MAX_UTTERANCE_CHARS = 500        # 500 chars max per utterance
MAX_TOOL_CALLS_PER_TURN = 10     # Max tool calls allowed in 1 turn
MAX_TOOL_CALLS_PER_SESSION = 30  # Max tool calls per session
MAX_CONSECUTIVE_SILENCE = 3      # 3 empty/silence utterances triggers hangup
REPEAT_LOOP_THRESHOLD = 3        # Repeating identical utterance 3 times triggers loop defense
RATE_LIMIT_CALLS_PER_MIN = 5     # Max 5 calls per minute per caller phone

# Strike Ladder Warning Texts (Injected deterministically by backend)
STRIKE_MESSAGES = {
    1: "Short polite redirect: I am exclusively configured to assist with orders and inquiries for {business_name}.",
    2: "Firm redirect: I can only assist with verified {business_name} services. Please let me know what you would like to order or book.",
    3: "Final warning: This line is reserved for {business_name}. Continued off-topic queries will immediately disconnect the call.",
    4: "Call terminated: Off-topic limit reached. Thank you for contacting {business_name}, goodbye."
}

class SessionState:
    def __init__(self, session_id: str, domain_id: str, caller_phone: str = "+91 98712 00000", start_time: Optional[float] = None):
        self.session_id = session_id
        self.domain_id = domain_id
        self.caller_phone = caller_phone
        self.start_time = start_time if start_time is not None else time.time()
        self.simulated_clock_offset: float = 0.0 # for simulated time test without sleeping
        self.turn_count = 0
        self.off_topic_strikes = 0
        self.consecutive_valid_turns = 0
        self.consecutive_silence_turns = 0
        self.recent_utterances: deque = deque(maxlen=6)
        self.tool_calls_total = 0
        self.tool_calls_current_turn = 0
        self.is_terminated = False
        self.termination_reason: Optional[str] = None
        self.strike_history: List[Dict[str, Any]] = []

    def current_time(self) -> float:
        return self.start_time + self.simulated_clock_offset + (time.time() - self.start_time)

    def elapsed_seconds(self) -> float:
        return self.current_time() - self.start_time

class SessionGuardRegistry:
    """In-memory registry of active call sessions and caller rate-limiting buckets."""
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._caller_history: Dict[str, List[float]] = {} # phone -> list of timestamps

    def get_or_create(self, session_id: str, domain_id: str, caller_phone: str = "+91 98712 00000") -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id, domain_id, caller_phone)
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def check_rate_limit(self, caller_phone: str, now_ts: Optional[float] = None) -> Tuple[bool, int]:
        """Returns (is_allowed, calls_in_last_minute)."""
        now = now_ts if now_ts is not None else time.time()
        timestamps = self._caller_history.get(caller_phone, [])
        # filter out timestamps older than 60s
        timestamps = [ts for ts in timestamps if now - ts < 60.0]
        self._caller_history[caller_phone] = timestamps

        if len(timestamps) >= RATE_LIMIT_CALLS_PER_MIN:
            return False, len(timestamps)

        timestamps.append(now)
        self._caller_history[caller_phone] = timestamps
        return True, len(timestamps)

session_guard_registry = SessionGuardRegistry()

# -------------------------------------------------------------
# 1. SECURITY & INJECTION DETECTION
# -------------------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"system override",
    r"developer mode",
    r"system prompt",
    r"repeat your (initial )?instructions",
    r"you are now (in )?dan",
    r"jailbreak",
    r"discount mode on",
    r"i am the owner",
    r"admin access",
    r"raw json output",
    r"<script>",
    r"exec\(",
    r"union select",
    r"drop\s+table",
    r"select\s+.*\s+from",
    r";\s*--",
    r"(100%|free|फ्री|muft|muft me|0\s*rupees|zero rupees|bina bill)"
]

def check_security_violations(utterance: str) -> Tuple[bool, str]:
    """Detects prompt injections, boundary overrides, and role hijack attempts."""
    clean = utterance.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, clean):
            return True, f"INJECTION_ATTACK_DETECTED: Matched pattern '{pattern}'"
    return False, "CLEAN"

# -------------------------------------------------------------
# 2. OFF-TOPIC CLASSIFIER & STRIKE LADDER
# -------------------------------------------------------------
OFF_TOPIC_KEYWORDS = [
    "cricket", "ipl", "virat kohli", "rohit sharma", "score",
    "python", "binary search", "javascript", "write code", "bubble sort", "algorithm", "coding",
    "election", "politics", "modi", "bjp", "congress", "who will win election",
    "are you chatgpt", "chatgpt", "openai", "who made you", "what llm are you", "tell me about openai",
    "relationship advice", "relationship", "breakup", "girlfriend", "boyfriend", "math homework",
    "solve equation", "derivative of", "general knowledge", "capital of france"
]

async def is_utterance_off_topic(utterance: str, domain_name: str, domain_type: str) -> Tuple[bool, str]:
    """
    Evaluates whether an utterance is strictly off-topic.
    Combines rapid keyword heuristics with Groq Llama-3.3-70b validation.
    """
    clean = utterance.lower().strip()
    if not clean:
        return False, "EMPTY"

    # Fast pattern match
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in clean:
            return True, f"OFF_TOPIC_KEYWORD: '{kw}'"

    # Deep LLM check if ambiguous
    client = get_groq_client()
    if client:
        try:
            model = get_best_groq_model(client)
            prompt = (
                f"You are a strict conversational classifier for a {domain_type} business named '{domain_name}'.\n"
                f"Determine if this caller utterance is relevant to {domain_name} ({domain_type}), OR completely off-topic (e.g. cricket, math, general AI, politics, coding).\n"
                f"Utterance: \"{utterance}\"\n"
                f"Answer strictly 'IN_DOMAIN' or 'OFF_TOPIC'."
            )
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=6,
                temperature=0.0
            )
            answer = (resp.choices[0].message.content or "").strip().upper()
            if "OFF_TOPIC" in answer:
                return True, "OFF_TOPIC_LLM_CLASSIFIED"
            return False, "IN_DOMAIN"
        except Exception as e:
            logger.warning(f"Groq off-topic classification error ({e}), relying on deterministic heuristics.")

    return False, "IN_DOMAIN"

def evaluate_strike_ladder(session: SessionState, is_off_topic: bool, business_name: str) -> Dict[str, Any]:
    """
    Enforces the 4-strike ladder with -1 strike decay per 3 consecutive valid turns.
    Strike 1: Polite redirect
    Strike 2: Firm redirect
    Strike 3: Final warning
    Strike 4: Call terminated (end_call)
    """
    if is_off_topic:
        session.off_topic_strikes += 1
        session.consecutive_valid_turns = 0
        strike_num = min(4, session.off_topic_strikes)
        
        msg_template = STRIKE_MESSAGES.get(strike_num, STRIKE_MESSAGES[4])
        action_msg = msg_template.format(business_name=business_name)

        is_call_ended = (strike_num >= 4)
        if is_call_ended:
            session.is_terminated = True
            session.termination_reason = "OFF_TOPIC_STRIKE_4_REACHED"

        record = {
            "turn": session.turn_count,
            "strike": strike_num,
            "action": "TERMINATE_CALL" if is_call_ended else f"STRIKE_{strike_num}_INJECTED",
            "message": action_msg
        }
        session.strike_history.append(record)

        return {
            "status": "OFF_TOPIC_STRIKE",
            "strike": strike_num,
            "should_end_call": is_call_ended,
            "injected_system_instruction": action_msg
        }
    else:
        # In-domain turn -> Apply decay mechanism: -1 strike per 3 valid turns
        session.consecutive_valid_turns += 1
        decayed = False
        if session.consecutive_valid_turns >= 3 and session.off_topic_strikes > 0:
            session.off_topic_strikes = max(0, session.off_topic_strikes - 1)
            session.consecutive_valid_turns = 0
            decayed = True

        return {
            "status": "IN_DOMAIN_VALID",
            "strike": session.off_topic_strikes,
            "decayed": decayed,
            "should_end_call": False,
            "injected_system_instruction": None
        }

# -------------------------------------------------------------
# 3. COST EXHAUSTION & SHIELD CHECKS
# -------------------------------------------------------------
def evaluate_cost_shield(
    session: SessionState,
    utterance: str,
    simulated_elapsed_sec: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates resource and cost-exhaustion vectors.
    Returns (is_blocked, violation_reason).
    """
    if session.is_terminated:
        return True, f"SESSION_ALREADY_TERMINATED: {session.termination_reason}"

    session.turn_count += 1
    clean = utterance.strip()

    # 1. Utterance Length Cap
    if len(clean) > MAX_UTTERANCE_CHARS:
        return True, f"UTTERANCE_TOO_LONG: {len(clean)} characters exceeds {MAX_UTTERANCE_CHARS} limit"

    # 2. Turn Cap
    if session.turn_count > MAX_SESSION_TURNS:
        session.is_terminated = True
        session.termination_reason = "MAX_SESSION_TURNS_EXCEEDED"
        return True, f"TURN_CAP_EXCEEDED: Session reached {MAX_SESSION_TURNS} turns cap"

    # 3. Call Duration Cap (Supports simulated clock)
    elapsed = simulated_elapsed_sec if simulated_elapsed_sec is not None else session.elapsed_seconds()
    if elapsed > MAX_CALL_DURATION_SEC:
        session.is_terminated = True
        session.termination_reason = "MAX_CALL_DURATION_EXCEEDED"
        return True, f"DURATION_CAP_EXCEEDED: Call duration {int(elapsed)}s exceeds {int(MAX_CALL_DURATION_SEC)}s limit"

    # 4. Silence Holding
    if not clean or clean.lower() in ["", "...", "silence", "[silence]"]:
        session.consecutive_silence_turns += 1
        if session.consecutive_silence_turns >= MAX_CONSECUTIVE_SILENCE:
            session.is_terminated = True
            session.termination_reason = "SILENCE_TIMEOUT"
            return True, f"SILENCE_TIMEOUT: {MAX_CONSECUTIVE_SILENCE} consecutive empty turns detected"
    else:
        session.consecutive_silence_turns = 0

    # 5. Repeat Loop Flooding
    if clean:
        session.recent_utterances.append(clean.lower())
        if len(session.recent_utterances) >= REPEAT_LOOP_THRESHOLD:
            # Check if all recent utterances are identical
            last_n = list(session.recent_utterances)[-REPEAT_LOOP_THRESHOLD:]
            if len(set(last_n)) == 1:
                return True, f"REPEAT_LOOP_ATTACK: Utterance repeated {REPEAT_LOOP_THRESHOLD} consecutive times"

    return False, None

# -------------------------------------------------------------
# 4. TOKEN INTEGRITY & SECURITY BOUNDARIES
# -------------------------------------------------------------
async def validate_token_integrity(
    token: str,
    session_id: str,
    domain_id: str,
    requested_quantity: int
) -> Tuple[bool, str]:
    """
    Strict Two-Phase Token Validation in SQLite:
    - Token must exist
    - Belong to matching session
    - Belong to matching domain
    - Not expired (< 300 seconds)
    - Not already committed
    - Quantity within bounds [1, 50]
    """
    # Boundary quantity check
    if requested_quantity < 1 or requested_quantity > 50:
        return False, f"BOUNDARY_VIOLATION: Quantity {requested_quantity} is outside allowed range [1, 50]"

    # Fake / invalid format check
    if not token or len(token) < 10 or not (token.lower().startswith("tok_") or token.lower().startswith("tok-")):
        return False, "INVALID_TOKEN_FORMAT: Token is missing or malformed"

    async with async_session_factory() as db:
        stmt = select(PendingVerificationModel).where(PendingVerificationModel.token == token)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            return False, "TOKEN_NOT_FOUND: Token does not exist in SQLite pending_verifications"

        if record.status == "COMMITTED":
            return False, "TOKEN_REPLAY_ATTACK: Token has already been committed and consumed"

        if record.status == "EXPIRED":
            return False, "TOKEN_EXPIRED: Token TTL has expired"

        if record.domain_id != domain_id:
            return False, f"CROSS_DOMAIN_ATTACK: Token belongs to domain '{record.domain_id}', not '{domain_id}'"

        if record.session_id != session_id:
            return False, f"CROSS_SESSION_ATTACK: Token belongs to session '{record.session_id}', not '{session_id}'"

        # Check TTL (5 minutes = 300 seconds)
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
        if age_seconds > 300.0:
            record.status = "EXPIRED"
            await db.commit()
            return False, f"TOKEN_EXPIRED: Token age {int(age_seconds)}s exceeds 300s TTL"

        return True, "TOKEN_VALIDATED"
