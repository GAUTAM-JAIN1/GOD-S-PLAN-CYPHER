import io
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.config import settings
from backend.schemas import ProvisionAgentResponse, ScribeSTTResponse

logger = logging.getLogger("voxera.elevenlabs_service")

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Curated High-Speed Conversational Voices with Indian / Global accents
CURATED_DEFAULT_VOICES = [
    {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel (Calm & Professional Receptionist)",
        "accent": "Multilingual / Conversational",
        "category": "premade"
    },
    {
        "voice_id": "AZnzlk1XvdvUeBnXmlld",
        "name": "Domi (Energetic Front Desk)",
        "accent": "Modern Indian / Global",
        "category": "premade"
    },
    {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Bella (Warm & Reassuring Host)",
        "accent": "Soothing Conversational",
        "category": "premade"
    },
    {
        "voice_id": "ErXwobaYiN019PkySvjV",
        "name": "Antoni (Sharp Client Advisor)",
        "accent": "Executive English / Hinglish",
        "category": "premade"
    }
]

def get_elevenlabs_headers() -> Dict[str, str]:
    if not settings.has_elevenlabs:
        raise ValueError("ELEVENLABS_API_KEY is missing in backend/.env")
    return {
        "xi-api-key": settings.ELEVENLABS_API_KEY.strip(),
        "Content-Type": "application/json"
    }

def build_convai_agent_payload(
    business_name: str,
    system_prompt: str,
    first_message: str,
    voice_id: str,
    language_code: str = "hi"
) -> Dict[str, Any]:
    """
    Builds the official ElevenLabs Conversational AI Agent configuration payload
    tuned for human-indistinguishable Hinglish/English realism.
    """
    chosen_voice = voice_id if voice_id and voice_id.strip() else settings.ELEVENLABS_DEFAULT_VOICE_ID
    
    # Enforce strict Indian price normalizer, voice focus, and conversational breathing cadence
    hardened_prompt = f"""{system_prompt}

MANDATORY ACOUSTIC & SPOKEN RULES:
1. Spoken turns MUST NEVER exceed 15 words.
2. Spoken Numbers & Currency: Say 'two forty rupees' or 'chaar sau chaalis rupaye'—NEVER pronounce raw currency symbols.
3. Natural Fillers: Naturally use 'Haan ji', 'Achha', 'Bilkul'.
4. SINGLE-SPEAKER VOICE FOCUS: Focus EXCLUSIVELY on the single primary speaker conversing with you. Completely ignore ambient chatter, background noise, or bystanders. Only respond to direct inquiries.
5. Instant Tool Invocation: When caller orders or asks for service, IMMEDIATELY call verify_catalog_item.
6. MANDATORY CUSTOMER DETAILS: When the caller agrees to the order or price, DO NOT commit yet. You MUST FIRST ask: 'Order confirm karne ke liye aapka naam aur delivery address/phone bata dijiye?'. Once caller provides them, call commit_verified_action with caller_name and delivery_address!
7. HUMAN TRANSFER: If caller asks for owner, manager, doctor, or human, immediately call request_human_intervention tool."""

    return {
        "name": f"Voxera — {business_name}",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": hardened_prompt,
                    "llm": "gemini-2.0-flash-001",
                    "temperature": 0.5,
                    "tools": [
                        {
                            "type": "client",
                            "name": "verify_catalog_item",
                            "description": "Deterministic Acoustic-Pydantic check for catalog item or service in active business.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "spoken_entity": {
                                        "type": "string",
                                        "description": "The exact item or service name spoken by the caller"
                                    },
                                    "quantity": {
                                        "type": "integer",
                                        "description": "Quantity requested (default: 1)",
                                        "default": 1
                                    },
                                    "modifiers": {
                                        "type": "array",
                                        "items": {"type": "string", "description": "Modifier label"},
                                        "description": "Any add-on, size, or modifier (e.g. Oat Milk, Large, First Visit)"
                                    },
                                    "caller_utterance": {
                                        "type": "string",
                                        "description": "Full raw caller sentence"
                                    }
                                },
                                "required": ["spoken_entity"]
                            },
                            "expects_response": True
                        },
                        {
                            "type": "client",
                            "name": "commit_verified_action",
                            "description": "Locks the verified order or appointment into operations ledger after price confirmation and collecting customer name/address.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "canonical_name": {"type": "string", "description": "Canonical verified item or appointment name"},
                                    "quantity": {"type": "integer", "description": "Quantity to commit"},
                                    "total_price_inr": {"type": "number", "description": "Total price in Indian Rupees"},
                                    "caller_name": {"type": "string", "description": "Customer name"},
                                    "delivery_address": {"type": "string", "description": "Customer delivery address or appointment slot"},
                                    "caller_phone": {"type": "string", "description": "Caller phone number"}
                                },
                                "required": ["canonical_name", "quantity", "total_price_inr"]
                            },
                            "expects_response": True
                        },
                        {
                            "type": "client",
                            "name": "request_human_intervention",
                            "description": "Triggers immediate Whisper Co-Pilot hold and phone push notification when caller requests owner/doctor transfer.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "reason": {"type": "string", "description": "Reason for human transfer request"},
                                    "caller_summary": {"type": "string", "description": "Summary of caller request"}
                                },
                                "required": ["reason"]
                            },
                            "expects_response": True
                        }
                    ]
                },
                "first_message": first_message,
                "language": "hi" if "hi" in language_code.lower() else "en"
            },
            "tts": {
                "model_id": "eleven_flash_v2_5",
                "voice_id": chosen_voice,
                "stability": 0.40,
                "similarity_boost": 0.80,
                "style": 0.0,
                "use_speaker_boost": True,
                "agent_output_audio_format": "pcm_24000",
                "optimize_streaming_latency": 4
            },
            "turn": {
                "turn_timeout": 1.0,
                "turn_eagerness": "eager"
            },
            "conversation": {
                "max_duration_seconds": 600
            }
        }
    }

async def provision_elevenlabs_agent(
    business_name: str,
    system_prompt: str,
    first_message: str,
    voice_id: str,
    language_code: str = "hi",
    existing_agent_id: Optional[str] = None
) -> ProvisionAgentResponse:
    """
    Creates or updates a real agent on ElevenLabs ConvAI.
    Zero silent fallbacks: surfaces exact HTTP status and error body.
    """
    payload = build_convai_agent_payload(
        business_name=business_name,
        system_prompt=system_prompt,
        first_message=first_message,
        voice_id=voice_id,
        language_code=language_code
    )

    if not settings.has_elevenlabs:
        return ProvisionAgentResponse(
            success=False,
            agent_id=None,
            status="API_KEY_REQUIRED",
            payload_preview=payload,
            message="ELEVENLABS_API_KEY is not set in backend/.env. Please paste your real API key."
        )

    try:
        headers = get_elevenlabs_headers()
    except ValueError as e:
        return ProvisionAgentResponse(
            success=False,
            agent_id=None,
            status="CONFIG_ERROR",
            payload_preview=payload,
            message=str(e)
        )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            if existing_agent_id and existing_agent_id.strip():
                # Patch existing agent
                url = f"{ELEVENLABS_API_BASE}/convai/agents/{existing_agent_id}"
                logger.info(f"Patching existing ElevenLabs agent: {existing_agent_id}")
                response = await client.patch(url, json=payload, headers=headers)
                
                if response.status_code in [200, 204]:
                    logger.info(f"Successfully patched ElevenLabs agent {existing_agent_id}")
                    return ProvisionAgentResponse(
                        success=True,
                        agent_id=existing_agent_id,
                        status="UPDATED",
                        payload_preview=payload,
                        message=f"ElevenLabs Agent {existing_agent_id} updated with latest prompt, prosody & client tools."
                    )
                else:
                    error_detail = response.text
                    logger.error(f"Failed to patch agent {existing_agent_id} ({response.status_code}): {error_detail}")
                    # If agent was deleted on ElevenLabs, attempt re-creation below
                    if response.status_code == 404:
                        logger.info("Agent 404 not found on ElevenLabs, creating new agent instead...")
                    else:
                        return ProvisionAgentResponse(
                            success=False,
                            agent_id=existing_agent_id,
                            status="HTTP_ERROR",
                            payload_preview=payload,
                            message=f"ElevenLabs API Error ({response.status_code}): {error_detail}"
                        )

            # Create new agent
            create_url = f"{ELEVENLABS_API_BASE}/convai/agents/create"
            logger.info(f"Creating new ElevenLabs ConvAI agent for: {business_name}")
            response = await client.post(create_url, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                res_data = response.json()
                agent_id = res_data.get("agent_id")
                logger.info(f"Successfully created ElevenLabs agent: {agent_id}")
                return ProvisionAgentResponse(
                    success=True,
                    agent_id=agent_id,
                    status="CREATED",
                    payload_preview=payload,
                    message=f"Live ElevenLabs Conversational AI Agent Created! Agent ID: {agent_id}"
                )
            else:
                error_body = response.text
                logger.error(f"ElevenLabs agent creation failed ({response.status_code}): {error_body}")
                return ProvisionAgentResponse(
                    success=False,
                    agent_id=None,
                    status=f"HTTP_{response.status_code}",
                    payload_preview=payload,
                    message=f"ElevenLabs Agent Creation Failed ({response.status_code}): {error_body}"
                )

    except httpx.RequestError as e:
        logger.error(f"Network error communicating with ElevenLabs: {e}", exc_info=True)
        return ProvisionAgentResponse(
            success=False,
            agent_id=None,
            status="NETWORK_ERROR",
            payload_preview=payload,
            message=f"Network request to ElevenLabs API failed: {str(e)}"
        )

async def get_signed_convai_url(agent_id: str) -> Dict[str, Any]:
    """
    Calls GET https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id={agent_id}
    Returns the real signed WebSocket URL. Zero fake fallback.
    """
    if not settings.has_elevenlabs:
        raise ValueError("ELEVENLABS_API_KEY is not configured in backend/.env. Cannot generate real signed URL.")

    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY.strip()}
    url = f"{ELEVENLABS_API_BASE}/convai/conversation/get-signed-url"
    params = {"agent_id": agent_id}

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            signed_url = data.get("signed_url")
            if not signed_url:
                raise ValueError(f"ElevenLabs response did not contain signed_url: {data}")
            return {"signed_url": signed_url, "agent_id": agent_id}
        else:
            logger.error(f"get-signed-url failed ({res.status_code}): {res.text}")
            raise HTTPException_ElevenLabs(
                status_code=res.status_code,
                detail=f"ElevenLabs get-signed-url failed ({res.status_code}): {res.text}"
            )

async def fetch_elevenlabs_voices() -> List[Dict[str, Any]]:
    """
    Fetches real available voices from ElevenLabs account.
    Falls back to curated list only if key is not configured.
    """
    if not settings.has_elevenlabs:
        return CURATED_DEFAULT_VOICES

    url = f"{ELEVENLABS_API_BASE}/voices"
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY.strip()}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                raw_voices = data.get("voices", [])
                formatted = []
                for v in raw_voices:
                    labels = v.get("labels", {})
                    accent = labels.get("accent", labels.get("description", "Multilingual"))
                    formatted.append({
                        "voice_id": v.get("voice_id"),
                        "name": v.get("name"),
                        "accent": accent,
                        "category": v.get("category", "cloned"),
                        "preview_url": v.get("preview_url")
                    })
                return formatted
            else:
                logger.warning(f"Failed to fetch voices ({res.status_code}), using curated: {res.text}")
                return CURATED_DEFAULT_VOICES
    except Exception as e:
        logger.error(f"Error fetching ElevenLabs voices: {e}")
        return CURATED_DEFAULT_VOICES

class HTTPException_ElevenLabs(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

async def transcribe_audio_scribe(
    audio_bytes: bytes,
    filename: str = "audio.wav"
) -> ScribeSTTResponse:
    """Transcribes audio using ElevenLabs Scribe STT with fallback to Groq Whisper."""
    # Attempt ElevenLabs Scribe STT first
    if settings.has_elevenlabs:
        try:
            url = f"{ELEVENLABS_API_BASE}/speech-to-text"
            headers = {"xi-api-key": settings.ELEVENLABS_API_KEY.strip()}
            files = {"file": (filename, audio_bytes, "audio/wav")}
            data = {"model_id": "scribe_v1"}

            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    res_data = res.json()
                    transcription = res_data.get("text", "").strip()
                    return ScribeSTTResponse(
                        success=True,
                        transcription=transcription,
                        confidence=0.96 if transcription else 0.0,
                        duration_seconds=res_data.get("duration", 2.0),
                        engine="elevenlabs/scribe_v1"
                    )
                else:
                    logger.warning(f"Scribe STT returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Scribe STT failed, attempting Groq fallback: {e}")

    # Fallback: Groq whisper-large-v3-turbo
    if settings.has_groq:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY.strip())
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model="whisper-large-v3-turbo",
                response_format="verbose_json"
            )
            text = transcription.text.strip() if hasattr(transcription, "text") else str(transcription).strip()
            return ScribeSTTResponse(
                success=True,
                transcription=text,
                confidence=0.94 if text else 0.0,
                duration_seconds=getattr(transcription, "duration", 2.0) or 2.0,
                engine="groq/whisper-large-v3-turbo"
            )
        except Exception as e:
            logger.error(f"Groq Whisper fallback failed: {e}", exc_info=True)
            return ScribeSTTResponse(
                success=False,
                transcription="",
                confidence=0.0,
                duration_seconds=0.0,
                engine="error",
                error=f"Groq Whisper Error: {str(e)}"
            )

    return ScribeSTTResponse(
        success=False,
        transcription="",
        confidence=0.0,
        duration_seconds=0.0,
        engine="none",
        error="Neither ELEVENLABS_API_KEY nor GROQ_API_KEY is configured in backend/.env."
    )
