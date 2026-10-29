import asyncio
import time
import json
import uuid
import logging
from typing import Dict, Optional, Any
from sqlalchemy import select
from backend.database import async_session_factory, InterceptHoldModel, LedgerEntryModel
from backend.services.telegram_notifier import telegram_service

logger = logging.getLogger("voxera.whisper_copilot")

class WhisperCopilotSLAManager:
    def __init__(self):
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._deadlines: Dict[str, float] = {} # hold_id -> expires_at_epoch_ms
        self._broadcast_func: Optional[Any] = None

    def set_broadcaster(self, broadcaster):
        self._broadcast_func = broadcaster

    def schedule_sla_timeout(
        self,
        hold_id: str,
        timeout_sec: float = 8.0,
        session_id: str = "#VF-LIVE",
        domain_id: str = "brew-bite-cafe",
        caller_utterance: str = ""
    ) -> float:
        """
        Schedules an async background SLA task that auto-fallbacks after timeout_sec.
        Returns expires_at_epoch_ms.
        """
        # Cancel any previous task on this hold_id
        self.cancel_sla_timeout(hold_id)

        now_ms = time.time() * 1000
        expires_at_ms = now_ms + (timeout_sec * 1000)
        self._deadlines[hold_id] = expires_at_ms

        task = asyncio.create_task(
            self._sla_worker(
                hold_id=hold_id,
                timeout_sec=timeout_sec,
                session_id=session_id,
                domain_id=domain_id,
                caller_utterance=caller_utterance
            )
        )
        self._active_tasks[hold_id] = task
        logger.info(f"Scheduled {timeout_sec}s SLA timeout for hold: {hold_id} (Expires: {expires_at_ms})")
        return expires_at_ms

    def cancel_sla_timeout(self, hold_id: str) -> bool:
        """Cancels active SLA countdown when owner resolves the hold."""
        task = self._active_tasks.pop(hold_id, None)
        self._deadlines.pop(hold_id, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled SLA timeout for hold: {hold_id}")
            return True
        return False

    def get_remaining_sla_seconds(self, hold_id: str) -> float:
        deadline_ms = self._deadlines.get(hold_id)
        if not deadline_ms:
            return 0.0
        remaining = (deadline_ms - (time.time() * 1000)) / 1000.0
        return max(0.0, round(remaining, 1))

    async def _sla_worker(
        self,
        hold_id: str,
        timeout_sec: float,
        session_id: str,
        domain_id: str,
        caller_utterance: str
    ):
        try:
            await asyncio.sleep(timeout_sec)
        except asyncio.CancelledError:
            return

        # SLA Elapsed -> Check DB and execute graceful fallback
        logger.warning(f"8.0s SLA EXPIRED for hold: {hold_id} (Session: {session_id})")
        
        async with async_session_factory() as session:
            try:
                stmt = select(InterceptHoldModel).where(InterceptHoldModel.id == hold_id)
                res = await session.execute(stmt)
                hold = res.scalar_one_or_none()

                if hold and hold.status == "ACTIVE_HOLD":
                    hold.status = "SLA_AUTO_FALLBACK"

                    # Determine domain badge
                    fallback_badge = "ASSISTED HOLD"
                    if "dental" in domain_id or "clinic" in domain_id:
                        fallback_badge = "SLA CALLBACK"
                    elif "realty" in domain_id:
                        fallback_badge = "SLA CALLBACK"

                    # Record real row in ledger_entries
                    entry_id = f"#VF-{uuid.uuid4().hex[:3].upper()}"
                    ledger_entry = LedgerEntryModel(
                        id=entry_id,
                        session_id=session_id,
                        domain_id=domain_id,
                        caller_phone="+91 98712 44321",
                        caller_language="Hinglish",
                        verified_order_summary=f"8.0s SLA Fallback: {hold.spoken_entity or 'Unresolved Audio'}",
                        total_amount_inr=0.0,
                        phonetic_score=hold.phonetic_score,
                        resolution_badge=fallback_badge,
                        details_json=json.dumps({
                            "reason": "SLA_TIMEOUT",
                            "hold_id": hold_id,
                            "caller_utterance": caller_utterance or hold.caller_utterance
                        })
                    )
                    session.add(ledger_entry)
                    await session.commit()

                    fallback_instruction = (
                        "SLA_TIMEOUT: The human co-pilot was unavailable within 8 seconds. "
                        "Politely tell the caller in conversational Hinglish: 'Aapki call line par hai, main aapka order confirm karne ke liye ek baar system mein check kar rahi thi. "
                        "Kya aap please ek baar apna item dobara bata sakte hain?'"
                    )

                    # Broadcast HOLD_SLA_EXPIRED over WebSocket
                    if self._broadcast_func:
                        await self._broadcast_func({
                            "type": "HOLD_SLA_EXPIRED",
                            "hold_id": hold_id,
                            "session_id": session_id,
                            "domain_id": domain_id,
                            "agent_contextual_instruction": fallback_instruction,
                            "status": "SLA_AUTO_FALLBACK",
                            "ledger_id": entry_id
                        })

                    # Telegram push alert
                    await telegram_service.send_sla_timeout_alert(session_id=session_id, hold_id=hold_id)

            except Exception as e:
                logger.error(f"Error executing SLA auto-fallback: {e}", exc_info=True)
            finally:
                self._active_tasks.pop(hold_id, None)
                self._deadlines.pop(hold_id, None)

whisper_sla_manager = WhisperCopilotSLAManager()
