import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from backend.config import settings
from backend.schemas import CatalogItem, StrictPolicy, CompileDomainResponse, LiveRefineResponse

logger = logging.getLogger("voxera.groq_compiler")

SYSTEM_COMPILER_PROMPT = """You are the Principal Voice AI Architecture Compiler for VOXERA.
Your task is to take a business description, domain type, owner instructions, and optional catalog text, and compile them into a production-hardened Voice AI Agent specification.

CRITICAL VOICE REALISM LAWS (NON-NEGOTIABLE):
1. TURN LENGTH: Spoken turns must be strictly under 15 words. Keep clauses punchy and direct.
2. INDIAN ACCENT & HINGLISH PROSODY: Keep speech crisp and rapid. Embed concise micro-acknowledgments ('Haan ji, bilkul', 'Achha, got it'). Never say robotic fillers like 'line par rahiye' or 'ek second check karti hu'.
3. SPOKEN NUMBERS & PRICES: Explicitly instruct the agent to speak numbers and prices naturally (e.g., 'two forty rupees' or 'do sau chaalis rupaye', NEVER raw symbols like '₹240').
4. BARGE-IN & TIMEOUT: 400ms-450ms turn timeout sensitivity. If caller interrupts, agent must stop speaking immediately.
5. DETERMINISTIC TOOL CALLS: The agent must call verify_catalog_item(spoken_entity, quantity, modifiers) whenever an item, service, or booking is requested. No hallucinated items.
6. MANDATORY READ-BACK: The agent MUST read back the canonical item name, quantity, and total price before confirming.
7. MANDATORY CUSTOMER DETAILS: Once caller confirms the order or service, the agent MUST ask for customer details ('Order confirm karne ke liye aapka naam aur delivery address/phone number bata dijiye?') before calling commit_verified_action.
8. HUMAN INTERVENTION: If caller asks to speak to manager, owner, doctor, or supervisor, immediately invoke request_human_intervention tool.

You must output a strictly valid JSON object adhering to this schema:
{
  "system_prompt": "Complete, production-ready system prompt for ElevenLabs voice agent",
  "first_message": "Short, punchy greeting under 10 words in natural Hinglish/English",
  "catalog_items": [
    {
      "id": "unique-id",
      "canonical_name": "Exact Name",
      "category": "Category",
      "price_inr": 240.0,
      "unit_or_duration": "e.g., 350ml or 45 mins",
      "phonetic_aliases": ["alias1", "sound-alike 2"],
      "allowed_modifiers": ["mod1", "mod2"]
    }
  ],
  "strict_policies": [
    {
      "id": "pol-1",
      "rule": "Policy text",
      "severity": "CRITICAL",
      "enforcement_action": "Action to take"
    }
  ]
}
Output ONLY the JSON object. Do not include markdown codeblocks or preamble."""

LIVE_REFINE_SYSTEM_PROMPT = """You are the VOXERA Prompt & Schema Diff Engine.
The user wants to refine an existing Voice AI Agent prompt and policies using a natural language instruction.
You must update the system_prompt and first_message according to the instruction, and output a JSON object:
{
  "updated_system_prompt": "The refined system prompt",
  "updated_first_message": "The refined first message",
  "diff_applied": [
    "+ Applied: Short summary of change 1",
    "+ Applied: Short summary of change 2"
  ]
}
Output ONLY the raw JSON object."""

def get_groq_client() -> Optional[Groq]:
    if settings.has_groq:
        return Groq(api_key=settings.GROQ_API_KEY)
    return None

_cached_groq_model: Optional[str] = None
_cached_fast_groq_model: Optional[str] = "llama-3.1-8b-instant"

def get_best_groq_model(client: Optional[Groq] = None) -> str:
    global _cached_groq_model
    if _cached_groq_model:
        return _cached_groq_model
    
    preferred_models = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "openai/gpt-oss-20b",
        "llama3-70b-8192",
        "allam-2-7b",
        "llama-3.1-8b-instant"
    ]
    if not client:
        client = get_groq_client()
    if client:
        try:
            available_ids = {m.id for m in client.models.list().data}
            for candidate in preferred_models:
                if candidate in available_ids:
                    _cached_groq_model = candidate
                    logger.info(f"Using Groq model: {_cached_groq_model}")
                    return _cached_groq_model
            text_models = [m for m in available_ids if "whisper" not in m and "guard" not in m and "orpheus" not in m]
            if text_models:
                _cached_groq_model = text_models[0]
                return _cached_groq_model
        except Exception as e:
            logger.warning(f"Could not list Groq models: {e}")
            
    _cached_groq_model = "openai/gpt-oss-120b"
    return _cached_groq_model

def get_fast_groq_model(client: Optional[Groq] = None) -> str:
    """
    Ultra-Fast model for live conversational turns and multi-turn combat arena (<180ms latency).
    Prioritizes models with direct generation (qwen/qwen3.8-27b) over reasoning models (gpt-oss-20b)
    to eliminate token starvation, empty responses, and long pauses.
    """
    global _cached_fast_groq_model
    if _cached_fast_groq_model:
        return _cached_fast_groq_model

    fast_candidates = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b"
    ]
    if not client:
        client = get_groq_client()
    if client:
        try:
            available_ids = {m.id for m in client.models.list().data}
            for candidate in fast_candidates:
                if candidate in available_ids:
                    _cached_fast_groq_model = candidate
                    logger.info(f"Using Fast Groq model for live turns: {_cached_fast_groq_model}")
                    return _cached_fast_groq_model
            text_models = [m for m in available_ids if "whisper" not in m and "guard" not in m and "orpheus" not in m]
            if text_models:
                _cached_fast_groq_model = text_models[0]
                return _cached_fast_groq_model
        except Exception as e:
            logger.warning(f"Could not list fast Groq models: {e}")

    _cached_fast_groq_model = "llama-3.1-8b-instant"
    return _cached_fast_groq_model

def generate_pydantic_literal_code(domain_name: str, items: List[CatalogItem]) -> str:
    cleaned_name = "".join(c for c in domain_name if c.isalnum()) or "Domain"
    item_names = [f'    "{item.canonical_name}"' for item in items]
    literal_items = ",\n".join(item_names)
    
    return f"""# Dynamically Compiled Pydantic Enum for {domain_name}
from typing import Literal
from pydantic import BaseModel, Field

{cleaned_name}Item = Literal[
{literal_items}
]

class VerifiedActionModel(BaseModel):
    selected_entity: {cleaned_name}Item
    quantity: int = Field(default=1, ge=1, le=50)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float
    caller_phone: str"""

async def compile_domain_architecture(
    business_name: str,
    domain_type: str,
    owner_instructions: str,
    parsed_catalog_text: str = ""
) -> CompileDomainResponse:
    client = get_groq_client()
    
    if not client:
        return CompileDomainResponse(
            success=False,
            domain_id=business_name.lower().replace(" ", "-"),
            system_prompt="",
            first_message="",
            catalog_items=[],
            strict_policies=[],
            pydantic_literal_code="",
            error="GROQ_API_KEY is not configured in backend/.env. Please set GROQ_API_KEY to enable live Llama-3.3-70b compilation."
        )

    user_prompt = f"""Business Name: {business_name}
Domain Type: {domain_type}
Owner Custom Instructions:
{owner_instructions}

Parsed Catalog / Document Text:
{parsed_catalog_text if parsed_catalog_text else 'No external PDF uploaded. Generate a rich, canonical 6-8 item catalog suitable for this business type with realistic Indian Rupee prices and phonetic aliases.'}"""

    try:
        active_model = get_best_groq_model(client)
        completion = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": SYSTEM_COMPILER_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        raw_response = completion.choices[0].message.content
        data = json.loads(raw_response)
        
        catalog_items = [CatalogItem(**item) for item in data.get("catalog_items", [])]
        strict_policies = [StrictPolicy(**pol) for pol in data.get("strict_policies", [])]

        # Ground system prompt with absolute catalog truth so the model NEVER invents items or prices
        menu_summary = "\n".join([f"- {it.canonical_name}: ₹{int(it.price_inr)} ({it.category})" for it in catalog_items])
        raw_prompt = data.get("system_prompt", "")
        grounded_system_prompt = f"""{raw_prompt}

VERIFIED LIVE CATALOG & PRICING (ABSOLUTE GROUND TRUTH - ZERO HALLUCINATION):
{menu_summary if menu_summary else 'No items in catalog.'}

CRITICAL BUSINESS & CONVERSATIONAL RULES:
1. OUTPUT: Output ONLY the direct spoken words to the caller. Do not output markdown, bullet points, asterisks, or tool call syntax.
2. MENU QUERIES: When caller asks what is on the menu or what items/services are available, ONLY mention the exact items listed above. NEVER invent or offer unlisted items.
3. UNAVAILABLE ITEMS: If caller asks for any item NOT on this menu, politely inform them that it is not available, and recommend 1-2 available items from the catalog.
4. ORDER VERIFICATION: When caller orders items, state the canonical item, quantity, and exact price, then ask for confirmation.
5. CADENCE: Keep spoken responses under 20 words in natural, friendly Indian Hinglish/English."""

        pydantic_code = generate_pydantic_literal_code(business_name, catalog_items)
        tokens_used = completion.usage.total_tokens if completion.usage else 0

        return CompileDomainResponse(
            success=True,
            domain_id=business_name.lower().replace(" ", "-"),
            system_prompt=grounded_system_prompt,
            first_message=data.get("first_message", f"Namaste, {business_name}! How may I help you?"),
            catalog_items=catalog_items,
            strict_policies=strict_policies,
            pydantic_literal_code=pydantic_code,
            raw_tokens_used=tokens_used
        )

    except Exception as e:
        logger.error(f"Groq compilation error: {e}", exc_info=True)
        return CompileDomainResponse(
            success=False,
            domain_id=business_name.lower().replace(" ", "-"),
            system_prompt="",
            first_message="",
            catalog_items=[],
            strict_policies=[],
            pydantic_literal_code="",
            error=f"Groq Compilation Failed: {str(e)}"
        )

async def live_refine_agent(
    current_system_prompt: str,
    current_first_message: str,
    refine_instruction: str
) -> LiveRefineResponse:
    client = get_groq_client()
    
    if not client:
        return LiveRefineResponse(
            success=False,
            diff_applied=[],
            updated_system_prompt=current_system_prompt,
            updated_first_message=current_first_message,
            elevenlabs_synced=False,
            error="GROQ_API_KEY is not configured in backend/.env."
        )

    prompt = f"""CURRENT SYSTEM PROMPT:
{current_system_prompt}

CURRENT FIRST MESSAGE:
{current_first_message}

OWNER REFINE INSTRUCTION:
{refine_instruction}"""

    try:
        active_model = get_best_groq_model(client)
        completion = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": LIVE_REFINE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        data = json.loads(completion.choices[0].message.content)
        return LiveRefineResponse(
            success=True,
            diff_applied=data.get("diff_applied", [f"+ Applied: {refine_instruction}"]),
            updated_system_prompt=data.get("updated_system_prompt", current_system_prompt),
            updated_first_message=data.get("updated_first_message", current_first_message),
            elevenlabs_synced=False
        )

    except Exception as e:
        logger.error(f"Live refine error: {e}", exc_info=True)
        return LiveRefineResponse(
            success=False,
            diff_applied=[],
            updated_system_prompt=current_system_prompt,
            updated_first_message=current_first_message,
            elevenlabs_synced=False,
            error=f"Refine Failed: {str(e)}"
        )

async def extract_clean_business_name(raw_text: str) -> str:
    """
    Extracts a clean, proper-case business name from user input or spoken description.
    Fixes Bug 5.1 ('hay Mere restaurant ka naam Dhar' naive string slicing).
    Handles English, Hinglish, and mixed inputs.
    """
    text = raw_text.strip()
    if not text:
        return "Custom Voice Agent"

    # Quick heuristic check for common Hinglish prefixes before invoking LLM
    import re
    hinglish_match = re.search(
        r"(?:hey|hi|hello)?\s*(?:mere|mera|hamara|apna)?\s*(?:restaurant|cafe|clinic|hospital|store|dukaan|shop|hotel|business)?\s*ka\s*naam\s+([A-Za-z0-9\s'&]+?)(?:\s+hai|\s+aur|\s+h\b|\s+in|\s+for|\s+hum|$)",
        text,
        re.IGNORECASE
    )
    if hinglish_match:
        extracted = hinglish_match.group(1).strip()
        if len(extracted) > 2:
            return " ".join(word.capitalize() for word in extracted.split())

    client = get_groq_client()
    if client:
        try:
            fast_model = get_fast_groq_model(client)
            prompt = (
                f"Extract ONLY the clean, concise, proper-case business/entity name from this text. "
                f"Do not include conversational filler words like 'mere restaurant ka naam', 'hey', 'hai', 'aur hum'.\n"
                f"Text: \"{text}\"\n"
                f"Return JSON: {{\"business_name\": \"Clean Name\"}}"
            )
            completion = client.chat.completions.create(
                model=fast_model,
                messages=[
                    {"role": "system", "content": "You extract clean business names from natural language instructions. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            extracted = data.get("business_name", "").strip()
            if extracted and len(extracted) >= 2 and not extracted.lower().startswith("mere"):
                return extracted
        except Exception as e:
            logger.warning(f"Groq business name extraction fallback: {e}")

    # Fallback heuristic: strip common conversational prefixes
    clean = re.sub(
        r"^(?:hey|hi|hello|namaste|sunlo|bhaiya)?\s*(?:mere|mera|apna|hamara)?\s*(?:restaurant|cafe|clinic|hotel|store)?\s*(?:ka\s*naam|name\s*is)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    ).strip()
    clean = clean.split(" in ")[0].split(" for ")[0].split(" aur ")[0].split(" hai ")[0]
    words = clean.split()[:4]
    candidate = " ".join(words).strip()
    return " ".join(w.capitalize() for w in candidate.split()) if candidate else "Custom Voice Agent"

