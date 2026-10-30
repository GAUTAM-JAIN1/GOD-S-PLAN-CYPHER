import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable, List
import httpx
from sqlalchemy import select, delete, text

from backend.config import settings

logger = logging.getLogger("voxera.telegram_service")

class TelegramService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN or ""
        self.owner_chat_id = settings.TELEGRAM_CHAT_ID or None
        self.is_running = False
        self.bot_username: Optional[str] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._resolve_callback: Optional[Callable] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.bot_token.strip() and not self.bot_token.startswith("your_"))

    async def load_persisted_chat_id(self):
        """Loads permanently saved paired_chat_id from SQLite system_configs table."""
        try:
            from backend.database import async_session_factory, SystemConfigModel, SystemSettingModel
            async with async_session_factory() as session:
                res = await session.execute(
                    select(SystemConfigModel).where(SystemConfigModel.key == "telegram_paired_chat_id")
                )
                setting = res.scalar_one_or_none()
                if setting and setting.value and setting.value.strip():
                    self.owner_chat_id = setting.value.strip()
                    logger.info(f"Loaded persisted Telegram Paired Chat ID from SQLite system_configs: {self.owner_chat_id}")
                    return self.owner_chat_id
                
                # Check legacy system_settings
                res2 = await session.execute(
                    select(SystemSettingModel).where(SystemSettingModel.key == "telegram_paired_chat_id")
                )
                setting2 = res2.scalar_one_or_none()
                if setting2 and setting2.value and setting2.value.strip():
                    self.owner_chat_id = setting2.value.strip()
                    await self.persist_chat_id(self.owner_chat_id)
                    return self.owner_chat_id
        except Exception as e:
            logger.warning(f"Could not load telegram_paired_chat_id from SQLite: {e}")

        # Fallback to settings.TELEGRAM_CHAT_ID from .env
        if settings.TELEGRAM_CHAT_ID and settings.TELEGRAM_CHAT_ID.strip():
            self.owner_chat_id = settings.TELEGRAM_CHAT_ID.strip()
            await self.persist_chat_id(self.owner_chat_id)
        return self.owner_chat_id

    async def persist_chat_id(self, chat_id: str):
        """Permanently saves paired_chat_id into SQLite system_configs table."""
        self.owner_chat_id = str(chat_id).strip()
        try:
            from backend.database import async_session_factory, SystemConfigModel, SystemSettingModel
            async with async_session_factory() as session:
                # 1. Save to system_configs
                res = await session.execute(
                    select(SystemConfigModel).where(SystemConfigModel.key == "telegram_paired_chat_id")
                )
                setting = res.scalar_one_or_none()
                if setting:
                    setting.value = self.owner_chat_id
                else:
                    session.add(SystemConfigModel(key="telegram_paired_chat_id", value=self.owner_chat_id))
                
                # 2. Mirror to system_settings
                res2 = await session.execute(
                    select(SystemSettingModel).where(SystemSettingModel.key == "telegram_paired_chat_id")
                )
                setting2 = res2.scalar_one_or_none()
                if setting2:
                    setting2.value = self.owner_chat_id
                else:
                    session.add(SystemSettingModel(key="telegram_paired_chat_id", value=self.owner_chat_id))

                await session.commit()
                logger.info(f"Persisted Telegram Chat ID {self.owner_chat_id} into SQLite system_configs.")
        except Exception as e:
            logger.error(f"Failed to persist telegram_paired_chat_id into SQLite: {e}")

    async def auto_discover_chat_id_from_telegram(self):
        """Calls getUpdates once on startup to auto-discover latest chat.id if someone messaged offline."""
        if not self.is_configured:
            return
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?limit=5"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for up in reversed(updates):
                        msg = up.get("message") or up.get("callback_query", {}).get("message")
                        if msg and "chat" in msg:
                            c_id = str(msg["chat"]["id"])
                            if not self.owner_chat_id:
                                await self.persist_chat_id(c_id)
                                logger.info(f"Auto-discovered offline Telegram Chat ID: {c_id}")
                            break
        except Exception as e:
            logger.warning(f"Telegram auto-discovery getUpdates check failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured,
            "running": self.is_running,
            "paired_chat_id": self.owner_chat_id,
            "bot_username": self.bot_username
        }

    def set_resolve_callback(self, callback: Callable):
        self._resolve_callback = callback

    async def send_message(self, text: str, reply_markup: Optional[Dict[str, Any]] = None, target_chat_id: Optional[str] = None) -> bool:
        dest_chat_id = target_chat_id or self.owner_chat_id
        if not self.is_configured or not dest_chat_id:
            logger.warning("Telegram not configured or no destination chat ID.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": dest_chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Telegram alert sent successfully to {dest_chat_id}")
                    return True
                logger.error(f"Telegram sendMessage failed: {res.status_code} {res.text}")
                # Store to pending_alerts for retry
                await self._store_pending_alert(dest_chat_id, text, reply_markup)
                return False
        except Exception as e:
            logger.error(f"Telegram HTTP error: {e}")
            # Store to pending_alerts for retry when network returns
            await self._store_pending_alert(dest_chat_id, text, reply_markup)
            return False

    async def _store_pending_alert(self, chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None):
        """Stores a failed Telegram alert into pending_alerts table for background retry."""
        try:
            from backend.database import async_session_factory
            async with async_session_factory() as session:
                from sqlalchemy import text as sql_text
                alert_id = str(uuid.uuid4())
                markup_json = json.dumps(reply_markup) if reply_markup else None
                await session.execute(sql_text(
                    "INSERT INTO pending_alerts (id, chat_id, text, reply_markup, retries) "
                    "VALUES (:id, :chat_id, :text, :markup, 0)"
                ), {"id": alert_id, "chat_id": chat_id, "text": text, "markup": markup_json})
                await session.commit()
                logger.info(f"Stored pending Telegram alert {alert_id} for retry.")
        except Exception as ex:
            logger.error(f"Failed to store pending alert: {ex}")

    async def flush_pending_alerts(self):
        """Retries all pending_alerts. Called periodically from the polling loop."""
        try:
            from backend.database import async_session_factory
            from sqlalchemy import text as sql_text
            async with async_session_factory() as session:
                rows = await session.execute(sql_text(
                    "SELECT id, chat_id, text, reply_markup, retries FROM pending_alerts ORDER BY created_at ASC LIMIT 20"
                ))
                alerts = rows.fetchall()
                if not alerts:
                    return

                for row in alerts:
                    alert_id, chat_id, msg_text, markup_str, retries = row
                    reply_markup = json.loads(markup_str) if markup_str else None

                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    payload = {"chat_id": chat_id, "text": msg_text, "parse_mode": "Markdown"}
                    if reply_markup:
                        payload["reply_markup"] = reply_markup

                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            res = await client.post(url, json=payload)
                            if res.status_code == 200:
                                await session.execute(sql_text("DELETE FROM pending_alerts WHERE id = :id"), {"id": alert_id})
                                logger.info(f"Flushed pending alert {alert_id} successfully.")
                            else:
                                await session.execute(sql_text(
                                    "UPDATE pending_alerts SET retries = :r WHERE id = :id"
                                ), {"r": retries + 1, "id": alert_id})
                    except Exception:
                        await session.execute(sql_text(
                            "UPDATE pending_alerts SET retries = :r WHERE id = :id"
                        ), {"r": retries + 1, "id": alert_id})

                await session.commit()
        except Exception as ex:
            logger.debug(f"flush_pending_alerts error: {ex}")

    async def send_hold_alert(
        self,
        hold_id: str,
        session_id: str,
        domain_id: str,
        caller_utterance: str,
        score: float,
        candidates: list,
        hold_reason: str = "LOW_CONFIDENCE_AUDIO"
    ) -> bool:
        if not self.is_configured or not self.owner_chat_id:
            return False

        if hold_reason == "HUMAN_TRANSFER_REQUEST":
            text = (
                f"🚨 *VOXERA CALL TRANSFER ESCALATION*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"*Session:* `{session_id}`\n"
                f"*Domain:* `{domain_id}`\n"
                f"*Caller Request:* \"{caller_utterance}\"\n\n"
                f"⚡ *Action Required: Choose live transfer, priority callback, or takeover:*"
            )
            inline_keyboard = [
                [{"text": "📞 Connect / Takeover Now", "callback_data": f"resolve:{hold_id}:APPROVE_TRANSFER"}],
                [{"text": "⏳ Busy — AI Priority Callback (10m)", "callback_data": f"resolve:{hold_id}:BUSY_CALLBACK"}],
                [{"text": "✅ Mark Resolved", "callback_data": f"resolve:{hold_id}:RESOLVED"}]
            ]
        else:
            c1 = candidates[0] if len(candidates) > 0 else {}
            c2 = candidates[1] if len(candidates) > 1 else {}
            
            c1_name = c1.get("canonical_name", "Option A")
            c1_prob = c1.get("probability_pct", 50)
            c1_price = int(c1.get("price_inr", 0))

            c2_name = c2.get("canonical_name", "Option B")
            c2_prob = c2.get("probability_pct", 50)
            c2_price = int(c2.get("price_inr", 0))

            text = (
                f"⚠️ *VOXERA LIVE WHISPER HOLD*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"*Session:* `{session_id}`\n"
                f"*Domain:* `{domain_id}`\n"
                f"*Heard Audio:* \"{caller_utterance}\"\n"
                f"*Confidence Score:* `{score:.2f}` (< 0.85 Threshold)\n\n"
                f"*Top Probability Candidates:*\n"
                f"1️⃣ {c1_name} ({c1_prob}% · ₹{c1_price})\n"
                f"2️⃣ {c2_name} ({c2_prob}% · ₹{c2_price})\n\n"
                f"⏱️ *8.0s Auto-Fallback SLA Active — 1-Tap Resolve:*"
            )
            inline_keyboard = [
                [{"text": f"1️⃣ {c1_name} ({c1_prob}% · ₹{c1_price})", "callback_data": f"resolve:{hold_id}:CANDIDATE_1"}],
                [{"text": f"2️⃣ {c2_name} ({c2_prob}% · ₹{c2_price})", "callback_data": f"resolve:{hold_id}:CANDIDATE_2"}],
                [{"text": "📞 Takeover Call", "callback_data": f"resolve:{hold_id}:TAKEOVER_CALL"}]
            ]

        reply_markup = {"inline_keyboard": inline_keyboard}
        return await self.send_message(text, reply_markup=reply_markup)

    async def send_takeover_alert(
        self,
        domain_name: str,
        caller_info: str,
        utterance: str,
        order_summary: str,
        hold_id: Optional[str] = None
    ) -> bool:
        """Dispatches mandatory Bug 4 Trigger 2 Live Takeover alert."""
        if not self.is_configured or not self.owner_chat_id:
            return False

        h_id = hold_id or "live_call"
        text = (
            f"🚨 *LIVE CALL TAKEOVER ACTIVE*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"*Domain:* {domain_name}\n"
            f"*Caller:* `{caller_info}`\n"
            f"*Last Utterance:* \"{utterance}\"\n"
            f"*Order Summary:* {order_summary}\n\n"
            f"⚡ *Select an action to intervene or bridge audio:*"
        )
        inline_keyboard = [
            [{"text": "📞 Approve Call Transfer", "callback_data": f"resolve:{h_id}:APPROVE_TRANSFER"}],
            [{"text": "⏳ Busy — AI Callback", "callback_data": f"resolve:{h_id}:BUSY_CALLBACK"}],
            [{"text": "1️⃣ Confirm Candidate 1", "callback_data": f"resolve:{h_id}:CONFIRM_CANDIDATE_1"}]
        ]
        return await self.send_message(text, reply_markup={"inline_keyboard": inline_keyboard})

    async def send_test_alert(self, test_chat_id: Optional[str] = None) -> bool:
        """Sends immediate test alert for UI diagnostic validation."""
        target = test_chat_id or self.owner_chat_id
        if not target:
            return False
        text = (
            f"⚡ *VOXERA TELEGRAM DIAGNOSTIC ALERT*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Status: **Operational & Verified**\n"
            f"Paired Chat ID: `{target}`\n"
            f"Bot: @{self.bot_username or 'voxeraabot'}\n\n"
            f"Your Telegram Co-Pilot is 100% active. All live call takeovers, ambiguous holds, and SLA fallbacks will push here instantly."
        )
        inline_keyboard = [
            [{"text": "✅ Test Button Acknowledged", "callback_data": "test:ack"}]
        ]
        return await self.send_message(text, reply_markup={"inline_keyboard": inline_keyboard}, target_chat_id=target)

    async def send_sla_timeout_alert(self, session_id: str, hold_id: str) -> bool:
        text = (
            f"⏱️ *VOXERA 8.0s SLA TIMEOUT*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"*Session:* `{session_id}`\n"
            f"*Hold ID:* `{hold_id}`\n\n"
            f"⚠️ Owner response timeout elapsed. Agent activated graceful Hinglish callback fallback."
        )
        return await self.send_message(text)

    async def answer_callback_query(self, callback_query_id: str, text: str = "Dispatched"):
        if not self.is_configured:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
        except Exception as e:
            logger.error(f"Failed to answer callback query: {e}")

    async def edit_message_text(self, chat_id: int | str, message_id: int, new_text: str):
        if not self.is_configured:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/editMessageText"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": new_text,
                    "parse_mode": "Markdown"
                })
        except Exception as e:
            logger.error(f"Failed to edit Telegram message: {e}")

    async def auto_recover_chat_id_from_recent_updates(self):
        """Auto-recovers recent sender chat_id on startup if paired_chat_id is missing."""
        if not self.is_configured or self.owner_chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params={"offset": -10, "limit": 10})
                if resp.status_code == 200:
                    updates = resp.json().get("result", [])
                    for update in reversed(updates):
                        msg = update.get("message") or update.get("callback_query", {}).get("message")
                        if msg and "chat" in msg:
                            found_id = str(msg["chat"]["id"])
                            logger.info(f"Auto-recovered Telegram Paired Chat ID from recent updates: {found_id}")
                            await self.persist_chat_id(found_id)
                            break
        except Exception as ex:
            logger.debug(f"Could not auto-recover chat_id from recent updates: {ex}")

    async def start_polling(self):
        """Starts background getUpdates long-polling loop with permanent SQLite persistence."""
        if not self.is_configured:
            logger.info("Telegram Bot Token not configured. Long-polling skipped.")
            return

        self.is_running = True
        logger.info("Starting Telegram Bot Long-Polling Worker...")

        # 1. Load persisted chat_id from SQLite
        await self.load_persisted_chat_id()

        # 2. Fetch bot identity
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://api.telegram.org/bot{self.bot_token}/getMe")
                if resp.status_code == 200:
                    data = resp.json().get("result", {})
                    self.bot_username = data.get("username")
                    logger.info(f"Telegram Bot connected: @{self.bot_username}")
        except Exception as ex:
            logger.warning(f"Could not reach Telegram API on startup: {ex}")

        # 3. Auto-recover chat_id from recent updates if still None
        if not self.owner_chat_id:
            await self.auto_recover_chat_id_from_recent_updates()

        offset = 0
        while self.is_running:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {"offset": offset, "timeout": 10}
                
                async with httpx.AsyncClient(timeout=15.0) as client:
                    if not self.bot_username:
                        try:
                            me_resp = await client.get(f"https://api.telegram.org/bot{self.bot_token}/getMe")
                            if me_resp.status_code == 200:
                                self.bot_username = me_resp.json().get("result", {}).get("username")
                        except Exception:
                            pass

                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        updates = resp.json().get("result", [])
                        for update in updates:
                            offset = update["update_id"] + 1

                            # Handle Callback Query (Button Press)
                            if "callback_query" in update:
                                cb = update["callback_query"]
                                cb_id = cb["id"]
                                data = cb.get("data", "")
                                message = cb.get("message", {})
                                chat_id = str(message.get("chat", {}).get("id"))
                                message_id = message.get("message_id")

                                if not self.owner_chat_id:
                                    await self.persist_chat_id(chat_id)

                                if data.startswith("resolve:"):
                                    parts = data.split(":")
                                    if len(parts) >= 3:
                                        hold_id = parts[1]
                                        action = parts[2]
                                        
                                        await self.answer_callback_query(cb_id, f"Dispatched: {action}")
                                        
                                        if self._resolve_callback:
                                            await self._resolve_callback(
                                                hold_id=hold_id if hold_id != "live_call" else None,
                                                resolution_action=action,
                                                custom_whisper_text="",
                                                resolved_by="TELEGRAM_BOT"
                                            )

                                        if chat_id and message_id:
                                            await self.edit_message_text(
                                                chat_id, message_id,
                                                f"✅ *RESOLVED VIA TELEGRAM:* `{action}`\n"
                                                f"Action `{action}` dispatched to live Voxera session."
                                            )
                                elif data == "test:ack":
                                    await self.answer_callback_query(cb_id, "Diagnostic Confirmed!")
                                    if chat_id and message_id:
                                        await self.edit_message_text(
                                            chat_id, message_id,
                                            "✅ *DIAGNOSTIC TEST PASSED*\nTelegram Co-Pilot is connected and interactive."
                                        )

                            # Handle Direct Text Messages
                            elif "message" in update:
                                msg = update["message"]
                                chat_id = str(msg["chat"]["id"])
                                text = msg.get("text", "").strip()

                                # Persist chat_id permanently
                                if not self.owner_chat_id or text.startswith("/start"):
                                    await self.persist_chat_id(chat_id)

                                if text.startswith("/start"):
                                    await self.send_message(
                                        f"✅ *Voxera Co-Pilot Paired!*\n"
                                        f"━━━━━━━━━━━━━━━━━━\n"
                                        f"Owner Chat ID: `{chat_id}` (Saved permanently to SQLite)\n\n"
                                        f"You will now receive instant push alerts for <0.85 Confidence Holds, Live Call Transfers, and Takeover Requests. "
                                        f"Tap the buttons on your phone to resolve calls in real time!\n\n"
                                        f"💡 *Tip:* While a call is active, reply to this chat with any text to inject a *Live Whisper* directly into the agent's ear.",
                                        target_chat_id=chat_id
                                    )
                                elif text:
                                    # Treat plain text reply as custom whisper into the active hold
                                    if self._resolve_callback:
                                        res = await self._resolve_callback(
                                            hold_id=None,
                                            resolution_action="CUSTOM_WHISPER",
                                            custom_whisper_text=text,
                                            resolved_by="TELEGRAM_BOT"
                                        )
                                        if res.get("success"):
                                            await self.send_message(f"🗣️ *Whisper Injected:* \"{text}\"\nAgent received owner instruction.", target_chat_id=chat_id)
                                        else:
                                            await self.send_message(f"ℹ️ Received: \"{text}\". (No active call currently on hold to inject whisper).", target_chat_id=chat_id)
                    elif resp.status_code in (401, 404):
                        logger.error(f"Telegram Bot Token invalid ({resp.status_code}). Stopping polling.")
                        self.is_running = False
                        break
                    # Flush any pending alerts each polling cycle
                    await self.flush_pending_alerts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Telegram polling loop tick: {e}")
                await asyncio.sleep(2.0)

    def stop_polling(self):
        self.is_running = False
        if self._polling_task:
            self._polling_task.cancel()

telegram_service = TelegramService()
TelegramNotifierService = TelegramService
