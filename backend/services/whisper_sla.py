"""
Authoritative compatibility wrapper for whisper_sla_manager.
Unifies all imports to backend.services.whisper_copilot.
"""
from backend.services.whisper_copilot import (
    WhisperCopilotSLAManager,
    whisper_sla_manager,
)

__all__ = ["WhisperCopilotSLAManager", "whisper_sla_manager"]
