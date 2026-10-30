import re
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional, Literal
import rapidfuzz.fuzz as fuzz
import jellyfish
from metaphone import doublemetaphone
from pydantic import BaseModel, Field, create_model, ValidationError
from backend.schemas import CatalogItem

logger = logging.getLogger("voxera.phonetic_guardrail")

# Multi-word Hinglish conversational phrases to strip before word tokenization
HINGLISH_PHRASES = [
    "laga do", "lagado", "kar do", "kardo", "kr do", "krdo",
    "de do", "dedo", "bna do", "banado", "likh lo", "likhlo",
    "daal do", "dal do", "pack kardo", "pack kar do", "pack krdo",
    "kijiye na", "kar dijiye", "kr dijiye"
]

# Common Hinglish conversational fillers, polite markers, and action words
HINGLISH_STOPWORDS = {
    "bhaiya", "bhai", "sir", "madam", "mam", "plate", "plates", "glass", "cup",
    "portion", "wala", "wali", "wale", "karna", "krna", "lagao", "laga", "kijiye",
    "kijiyega", "dijiye", "chahiye", "please", "zara", "aur", "bhi", "pack",
    "order", "dena", "mujhe", "hume", "mera", "mere", "meri", "liye", "likho",
    "ekdum", "thoda", "jaldi"
}

# Sizing descriptors extracted as modifiers
SIZE_MODIFIERS = {"medium", "regular", "large", "small", "half", "full"}

# Number words mapping to quantities
HINGLISH_NUMBERS = {
    "ek": 1, "one": 1, "1": 1,
    "do": 2, "two": 2, "2": 2,
    "teen": 3, "three": 3, "3": 3,
    "chaar": 4, "char": 4, "four": 4, "4": 4,
    "paanch": 5, "panch": 5, "five": 5, "5": 5,
    "che": 6, "six": 6, "6": 6,
    "saat": 7, "sat": 7, "seven": 7, "7": 7,
    "aath": 8, "ath": 8, "eight": 8, "8": 8,
    "nau": 9, "nine": 9, "9": 9,
    "das": 10, "ten": 10, "10": 10
}

# Ambient noise fillers and single-syllable fragments to reject on barge-in
NOISE_FILLERS = {"uh", "um", "umm", "uhh", "hmm", "hm", "haan", "ha", "aah", "the", "ah", "oh"}

# Stopwords and escalation triggers that immediately grant barge-in or human takeover
BARGE_IN_STOPWORDS = {"ruko", "wait", "cancel", "nahi", "hold", "bhaiya", "listen", "chup", "stop", "manager"}

def is_background_noise_or_filler(utterance: str) -> Tuple[bool, str]:
    """
    Evaluates whether an utterance is background noise, breath, or meaningless filler.
    Rejects fragments with < 2 meaningful words unless a critical stopword is present.
    """
    words = [re.sub(r"[^\w]", "", w.lower()).strip() for w in utterance.split()]
    words = [w for w in words if w]
    if not words:
        return True, "EMPTY_AUDIO"

    has_stopword = any(w in BARGE_IN_STOPWORDS for w in words)
    if has_stopword:
        return False, "CRITICAL_STOPWORD_DETECTED"

    meaningful = [w for w in words if w not in NOISE_FILLERS and len(w) > 1]
    if len(meaningful) < 2:
        return True, f"NOISE_FRAGMENT (<2 words: '{utterance.strip()}')"

    return False, "MEANINGFUL_SPEECH"

def strip_hinglish_stopwords_and_extract_qty(
    raw_utterance: str, default_qty: int = 1
) -> Tuple[str, int, List[str]]:
    """
    Cleans Hinglish fillers, extracts spoken quantities and modifiers.
    Example: 'bhaiya do medium hezalnat cold brew wala laga do' -> ('hezalnat cold brew', 2, ['medium'])
    """
    clean = raw_utterance.lower().strip()

    # Step A1: Strip multi-word action phrases first
    for phrase in HINGLISH_PHRASES:
        clean = re.sub(r"\b" + phrase + r"\b", " ", clean)

    clean = re.sub(r"[^\w\s]", " ", clean)
    words = clean.split()

    extracted_qty = default_qty
    extracted_modifiers: List[str] = []
    filtered_words: List[str] = []

    for w in words:
        if w in HINGLISH_NUMBERS and extracted_qty == default_qty:
            extracted_qty = HINGLISH_NUMBERS[w]
        elif w.isdigit() and 1 <= int(w) <= 25 and extracted_qty == default_qty:
            extracted_qty = int(w)
        elif w in SIZE_MODIFIERS:
            extracted_modifiers.append(w)
        elif w not in HINGLISH_STOPWORDS:
            filtered_words.append(w)

    filtered_entity = " ".join(filtered_words).strip()
    # Fallback to original text if everything got stripped
    if not filtered_entity:
        filtered_entity = raw_utterance.strip()

    return filtered_entity, extracted_qty, extracted_modifiers

def normalize_indic_phonetics(text: str) -> str:
    """
    Normalizes Indian English and Hinglish phoneme variations:
    - ph -> f, v -> w, z -> j, sh -> s
    - Aspirates: bh->b, kh->k, dh->d, th->t, gh->g, ch->c
    - Elongated vowels: aa->a, ee->i, oo->u, ou->o
    """
    clean = text.lower().strip()
    clean = re.sub(r"[^\w\s]", " ", clean)

    # Consonant substitutions for Indian accents
    clean = clean.replace("ph", "f").replace("v", "w").replace("z", "j").replace("sh", "s")

    # Aspirates
    clean = clean.replace("bh", "b").replace("kh", "k").replace("dh", "d")
    clean = clean.replace("th", "t").replace("gh", "g").replace("ch", "c")

    # Double/Elongated vowels
    clean = clean.replace("aa", "a").replace("ee", "i").replace("oo", "u").replace("ou", "o")

    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def compute_double_metaphone_similarity(text1: str, text2: str) -> float:
    """
    Computes normalized Levenshtein similarity on primary & secondary Double-Metaphone codes.
    Uses jellyfish.levenshtein_distance on metaphone.doublemetaphone representations.
    """
    norm1 = normalize_indic_phonetics(text1)
    norm2 = normalize_indic_phonetics(text2)

    dm1 = doublemetaphone(norm1)
    dm2 = doublemetaphone(norm2)

    max_sim = 0.0
    for code1 in dm1:
        if not code1:
            continue
        for code2 in dm2:
            if not code2:
                continue
            max_len = max(len(code1), len(code2))
            if max_len == 0:
                continue
            dist = jellyfish.levenshtein_distance(code1, code2)
            sim = max(0.0, 1.0 - (dist / max_len))
            if sim > max_sim:
                max_sim = sim

    return max_sim

def calculate_entity_match_score(spoken_clean: str, item: CatalogItem) -> float:
    """
    Computes composite score: S = 0.60 * S_lex + 0.40 * S_phon
    Evaluates against canonical_name AND all phonetic_aliases.
    - S_lex = max(WRatio, token_sort_ratio, partial_ratio) / 100.0
    - S_phon = Double-Metaphone normalized Levenshtein similarity
    """
    best_item_score = 0.0
    all_targets = [item.canonical_name] + (item.phonetic_aliases or [])

    for target in all_targets:
        target_clean = target.lower().strip()

        # 1. Lexical Score (WRatio, token_sort_ratio, token_set_ratio, weighted partial_ratio)
        raw_w_ratio = fuzz.WRatio(spoken_clean, target_clean) / 100.0
        sort_ratio = fuzz.token_sort_ratio(spoken_clean, target_clean) / 100.0
        raw_set_ratio = fuzz.token_set_ratio(spoken_clean, target_clean) / 100.0
        
        # Word coverage penalty: Prevents generic 1-word aliases (e.g. 'latte') from hijacking specific multi-word items (e.g. 'Matcha Green Tea Latte')
        q_words = spoken_clean.split()
        t_words = target_clean.split()
        if len(q_words) > 1 and len(t_words) < len(q_words):
            word_overlap = len(set(q_words) & set(t_words)) / len(q_words)
            set_ratio = raw_set_ratio * (0.35 + 0.65 * word_overlap)
            length_ratio = len(target_clean) / len(spoken_clean)
            if length_ratio < 0.65:
                w_ratio = raw_w_ratio * (0.45 + 0.55 * length_ratio)
            else:
                w_ratio = raw_w_ratio
        else:
            set_ratio = raw_set_ratio
            w_ratio = raw_w_ratio

        raw_part_ratio = fuzz.partial_ratio(spoken_clean, target_clean) / 100.0
        
        # Substring Probability Refinement: weight partial_ratio by symmetric length overlap
        # Prevents short sub-word targets (e.g. 'latte') from matching 100% on long specific queries (e.g. 'matcha green tea latte')
        target_len = max(len(target_clean), 1)
        query_len = max(len(spoken_clean), 1)
        len_ratio = min(target_len, query_len) / max(target_len, query_len)
        coverage_factor = min(1.0, 0.30 + 0.70 * len_ratio)
        weighted_part_ratio = raw_part_ratio * coverage_factor
        
        s_lex = max(w_ratio, sort_ratio, set_ratio * 0.95, weighted_part_ratio)

        # 2. Phonetic Score using Double-Metaphone
        s_phon = compute_double_metaphone_similarity(spoken_clean, target_clean)

        # When lexical match is strong (e.g. clear item name or subset words spoken),
        # do not penalize with missing syllable distance
        if s_lex >= 0.90:
            composite = max(s_lex, 0.60 * s_lex + 0.40 * s_phon)
        else:
            composite = 0.60 * s_lex + 0.40 * s_phon

        if composite > best_item_score:
            best_item_score = composite

    return round(best_item_score, 4)

def build_dynamic_pydantic_validator(domain_id: str, catalog_items: List[CatalogItem]):
    """
    Constructs a dynamic Pydantic v2 model at runtime locking canonical item names via Literal.
    """
    valid_names = tuple(item.canonical_name for item in catalog_items)
    DomainItemEnum = Literal[valid_names]  # type: ignore

    clean_id = "".join(c for c in domain_id if c.isalnum()) or "Domain"

    return create_model(
        f"DynamicGuardrail_{clean_id}",
        canonical_item=(DomainItemEnum, ...),
        quantity=(int, Field(default=1, ge=1, le=25)),
        unit_price_inr=(float, Field(gt=0.0)),
        total_price_inr=(float, Field(gt=0.0)),
        modifiers=(List[str], Field(default_factory=list)),
    )

def evaluate_hardened_entity(
    raw_spoken_entity: str,
    domain_id: str,
    catalog_items: List[CatalogItem],
    requested_qty: int = 1,
    modifiers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Hardened Acoustic-Pydantic Decision Engine:
    1. Strips Hinglish stopwords, extracts spoken quantities and modifiers
    2. Runs Double-Metaphone + RapidFuzz composite scoring
    3. Calculates Top-2 candidates with exact relative probability math: P1 = round(S1 / (S1 + S2) * 100)%
    4. Ambiguity Trap Penalty: If S1 >= 0.85 and (S1 - S2) < 0.12, caps S1 at 0.68 to force WHISPER_HOLD
    5. Validates through runtime Dynamic Pydantic v2 Model
    6. Issues cryptographic Two-Phase verification token on pass
    """
    if not catalog_items:
        return {
            "success": False,
            "match_type": "CATALOG_EMPTY",
            "score": 0.0,
            "is_ambiguous": False,
            "instruction": "Catalog is empty. Please configure business catalog first.",
        }

    # Step 1: Hinglish Stopword & Quantity Cleaning
    filtered_entity, extracted_qty, extracted_mods = strip_hinglish_stopwords_and_extract_qty(
        raw_spoken_entity, default_qty=requested_qty
    )
    combined_modifiers = list(set((modifiers or []) + extracted_mods))

    # Step 2: Score against all catalog items
    scored_candidates: List[Tuple[CatalogItem, float]] = []
    for item in catalog_items:
        score = calculate_entity_match_score(filtered_entity, item)
        scored_candidates.append((item, score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    top_item, raw_top_score = scored_candidates[0]
    second_item, raw_second_score = (
        scored_candidates[1] if len(scored_candidates) > 1 else (None, 0.0)
    )

    # Step 3: Relative Probability Math on candidate match scores
    # P1 = round(S1 / (S1 + S2) * 100)%, P2 = 100% - P1
    total_score_sum = raw_top_score + raw_second_score
    if total_score_sum > 0:
        p1 = round((raw_top_score / total_score_sum) * 100)
        p2 = 100 - p1
    else:
        p1, p2 = 50, 50

    # Step 4: Top-2 Candidate Ambiguity Trap Rule
    # If S1 >= 0.85 BUT gap (S1 - S2) < 0.12, cap S1 at 0.68 to force WHISPER_HOLD (< 0.85)
    is_ambiguous = False
    final_top_score = raw_top_score

    if second_item and raw_top_score >= 0.85 and (raw_top_score - raw_second_score) < 0.12:
        is_ambiguous = True
        logger.info(
            f"Ambiguity Trap Triggered! Top 1 '{top_item.canonical_name}' ({raw_top_score}) vs "
            f"Top 2 '{second_item.canonical_name}' ({raw_second_score}). Gap {raw_top_score - raw_second_score:.4f} < 0.12. "
            f"Score capped to 0.68 to force WHISPER_HOLD."
        )
        final_top_score = 0.68

    top_candidates = [
        {
            "id": top_item.id,
            "canonical_name": top_item.canonical_name,
            "price_inr": top_item.price_inr,
            "score": final_top_score,
            "probability_pct": p1,
        }
    ]
    if second_item:
        top_candidates.append({
            "id": second_item.id,
            "canonical_name": second_item.canonical_name,
            "price_inr": second_item.price_inr,
            "score": raw_second_score,
            "probability_pct": p2,
        })

    total_price = top_item.price_inr * extracted_qty

    # Step 5: Runtime Dynamic Pydantic Model Validation (if S >= 0.85 and not ambiguous)
    if final_top_score >= 0.85 and not is_ambiguous:
        try:
            DynamicValidator = build_dynamic_pydantic_validator(domain_id, catalog_items)
            validated_record = DynamicValidator(
                canonical_item=top_item.canonical_name,
                quantity=extracted_qty,
                unit_price_inr=top_item.price_inr,
                total_price_inr=total_price,
                modifiers=combined_modifiers,
            )

            # Generate Unique Two-Phase Verification Token
            token = f"tok_{uuid.uuid4().hex[:12]}"

            instruction = (
                f"MATCH_VERIFIED [token={token}]: {extracted_qty}x {top_item.canonical_name}, Total ₹{int(total_price)}. "
                f"MANDATORY: Speak this exact item and total price ₹{int(total_price)} back to the caller and ask 'Kya main isse lock kar du?'. "
                f"Only after caller says YES, call commit_verified_action."
            )

            return {
                "success": True,
                "match_type": "DETERMINISTIC_PASS",
                "score": final_top_score,
                "verification_token": token,
                "is_ambiguous": False,
                "filtered_entity": filtered_entity,
                "matched_item": top_item.model_dump(),
                "quantity": extracted_qty,
                "unit_price_inr": top_item.price_inr,
                "total_price_inr": total_price,
                "modifiers": combined_modifiers,
                "candidates": top_candidates,
                "instruction": instruction,
            }
        except ValidationError as val_err:
            logger.error(f"Dynamic Pydantic ValidationError: {val_err}")
            return {
                "success": False,
                "match_type": "VALIDATION_FAILED",
                "score": final_top_score,
                "is_ambiguous": False,
                "instruction": f"Order blocked: Dynamic Schema validation error: {str(val_err)}",
            }
    elif is_ambiguous or final_top_score >= 0.45:
        # Score in [0.45, 0.85) or Ambiguity Trap -> Caller actually attempted an item name with uncertainty -> Low Confidence Intercept Hold
        hold_reason_desc = (
            f"Ambiguity detected between Top 2 items (P1={p1}%, P2={p2}%)"
            if is_ambiguous
            else f"Audio confidence is {final_top_score:.2f} (< 0.85)"
        )
        holding_msg = (
            f"WHISPER_HOLD [{hold_reason_desc}]: Holding triggered for caller disambiguation. "
            f"Speak politely: 'Ek second hold kijiyega, main aapka exact item confirm kar rahi hu...'"
        )
        return {
            "success": False,
            "match_type": "WHISPER_HOLD",
            "score": final_top_score,
            "verification_token": None,
            "is_ambiguous": is_ambiguous,
            "filtered_entity": filtered_entity,
            "matched_item": top_item.model_dump(),
            "quantity": extracted_qty,
            "unit_price_inr": top_item.price_inr,
            "total_price_inr": total_price,
            "modifiers": combined_modifiers,
            "candidates": top_candidates,
            "instruction": holding_msg,
        }
    else:
        # Score < 0.45: Normal conversation, greeting, question, or no item mentioned
        return {
            "success": False,
            "match_type": "NO_ITEM_MENTIONED",
            "score": final_top_score,
            "verification_token": None,
            "is_ambiguous": False,
            "filtered_entity": filtered_entity,
            "matched_item": None,
            "quantity": 1,
            "unit_price_inr": 0.0,
            "total_price_inr": 0.0,
            "modifiers": [],
            "candidates": [],
            "instruction": "No specific catalog item recognized.",
        }

def match_multi_item_order(utterance: str, catalog_items: List[CatalogItem]) -> List[Dict[str, Any]]:
    """
    Splits multi-item order utterances on conjunctions ('aur', 'and', ',', '+', 'plus')
    and runs Double-Metaphone + fuzzy matching on each segment against real catalog items.
    Returns list of matched item dictionaries with canonical_name, price_inr, quantity, and score.
    """
    segments = re.split(r'\b(?:aur|and|plus|,|\+)\b', utterance, flags=re.IGNORECASE)
    matched_results: List[Dict[str, Any]] = []

    for seg in segments:
        s_clean = seg.strip()
        if not s_clean or len(s_clean) < 3:
            continue
        clean_ent, qty, _ = strip_hinglish_stopwords_and_extract_qty(s_clean)
        best_item = None
        best_score = 0.0

        for it in catalog_items:
            score = calculate_entity_match_score(clean_ent, it)
            if score > best_score:
                best_score = score
                best_item = it

        if best_item and best_score >= 0.65:
            matched_results.append({
                "item": best_item,
                "canonical_name": best_item.canonical_name,
                "price_inr": best_item.price_inr,
                "quantity": qty,
                "score": best_score,
                "total_price_inr": best_item.price_inr * qty
            })

    return matched_results

