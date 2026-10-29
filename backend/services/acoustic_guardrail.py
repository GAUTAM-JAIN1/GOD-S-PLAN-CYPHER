"""
Authoritative compatibility wrapper for acoustic_guardrail / phonetic_guardrail.
Unifies all imports to backend.services.phonetic_guardrail.
"""
from backend.services.phonetic_guardrail import (
    calculate_entity_match_score,
    evaluate_hardened_entity,
    compute_token_coverage,
    phonetic_soundalike_keys,
)

__all__ = [
    "calculate_entity_match_score",
    "evaluate_hardened_entity",
    "compute_token_coverage",
    "phonetic_soundalike_keys",
]
