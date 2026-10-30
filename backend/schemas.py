from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CatalogItem(BaseModel):
    id: str
    canonical_name: str
    category: str = "General"
    price_inr: float
    unit_or_duration: str = "item"
    phonetic_aliases: List[str] = Field(default_factory=list)
    allowed_modifiers: List[str] = Field(default_factory=list)

class StrictPolicy(BaseModel):
    id: str
    rule: str
    severity: str = "CRITICAL"
    enforcement_action: str

class DomainProfileSchema(BaseModel):
    id: str
    name: str
    domain_type: str
    tagline: str
    system_prompt: str
    first_message: str
    voice_id: str
    language_code: str = "hi-IN"
    turn_timeout_ms: int = 420
    catalog_items: List[CatalogItem] = Field(default_factory=list)
    strict_policies: List[StrictPolicy] = Field(default_factory=list)
    elevenlabs_agent_id: Optional[str] = None
    compiled_by: Optional[str] = "CrewAI Multi-Agent Trained"
    crew_execution_log_json: Optional[str] = "[]"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CompileDomainRequest(BaseModel):
    domain_id: Optional[str] = None
    domain_type: str
    business_name: str
    owner_instructions: str
    parsed_catalog_text: Optional[str] = ""
    voice_id: Optional[str] = None

class CompileDomainResponse(BaseModel):
    success: bool
    domain_id: str
    system_prompt: str
    first_message: str
    catalog_items: List[CatalogItem]
    strict_policies: List[StrictPolicy]
    pydantic_literal_code: str
    compiled_by: Optional[str] = "CrewAI 3-Agent Pipeline (Llama-3.3-70B)"
    crew_execution_log: Optional[List[Dict[str, Any]]] = None
    raw_tokens_used: Optional[int] = 0
    error: Optional[str] = None

class LiveRefineRequest(BaseModel):
    domain_id: str
    refine_instruction: str

class LiveRefineResponse(BaseModel):
    success: bool
    diff_applied: List[str]
    updated_system_prompt: str
    updated_first_message: str
    elevenlabs_synced: bool
    error: Optional[str] = None

class ProvisionAgentRequest(BaseModel):
    domain_id: str
    voice_id: Optional[str] = None

class ProvisionAgentResponse(BaseModel):
    success: bool
    agent_id: Optional[str] = None
    status: str
    payload_preview: Dict[str, Any] = Field(default_factory=dict)
    message: str
    use_browser_tts: bool = False

class ScribeSTTResponse(BaseModel):
    success: bool
    transcription: str
    confidence: float
    duration_seconds: float
    engine: str
    error: Optional[str] = None
    use_browser_tts: bool = False

class PDFParseResponse(BaseModel):
    success: bool
    filename: str
    page_count: int
    extracted_text: str
    preview_items_detected: int
    error: Optional[str] = None

class GauntletScenarioResult(BaseModel):
    scenario_id: int
    suite_id: Optional[str] = None
    title: str
    attack_vector: str
    attacker_utterance: str
    initial_agent_response: str
    tool_validation_summary: str
    status: str  # "PASS", "AUTO-PATCHED", "FAIL"
    latency_ms: int
    vulnerability_detected: bool
    patched_guardrail_rule: Optional[str] = None
    post_patch_agent_response: Optional[str] = None
    evaluator_diff: str
    duel_transcript: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class GauntletRunRequest(BaseModel):
    domain_id: str
    force_vulnerability_demo: bool = True
    selected_suites: Optional[List[str]] = None

class GauntletRunResponse(BaseModel):
    success: bool
    run_id: str
    domain_id: str
    scenarios_passed: int
    auto_healed_count: int
    mean_latency_ms: int
    scenarios: List[GauntletScenarioResult]
    created_at: str

class ResetVulnerabilityRequest(BaseModel):
    domain_id: str
