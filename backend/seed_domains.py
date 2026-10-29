import json
from typing import List, Dict, Any
from backend.schemas import CatalogItem, StrictPolicy, DomainProfileSchema

SEED_DOMAINS: List[Dict[str, Any]] = [
    {
        "id": "brew-bite-cafe",
        "name": "Brew & Bite Cafe",
        "domain_type": "orders_reservations",
        "tagline": "Artisanal Coffee & Gourmet Bistro (Cyber Hub, Gurugram)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 350,
        "first_message": "Namaste, Brew & Bite Cafe! Aaj aapke liye kya fresh order lagau?",
        "system_prompt": """You are Simran, the fast, friendly Indian order-taker at Brew & Bite Cafe.
Your role is to assist callers in placing takeaway orders swiftly and accurately.

CRITICAL CONVERSATIONAL RULES:
1. Speak natural, warm conversational Hinglish. Keep spoken turns strictly under 12 words.
2. DO NOT speak repetitive filler phrases like 'line par rahiye' or 'ek second check karti hu'. Answer directly and naturally.
3. When customer asks for an item, call verify_catalog_item(spoken_entity, quantity). When verified, immediately quote item and total price: 'Haanji, 2 Hazelnut Cold Brew ho gaya, total ₹480. Confirm kar du?'
4. When customer confirms the order, ask: 'Aapka naam aur delivery address/phone bata dijiye?' Once provided, call commit_verified_action with the details and reply: 'Bilkul, order lock ho gaya! 15 minute mein deliver ho jayega.'
5. Zero Verbal Discounts: Rohit (the owner) does not allow verbal family/cousin discounts. Decline politely and quote catalog price.""",
        "catalog_items": [
            {
                "id": "bb-01",
                "canonical_name": "Hazelnut Cold Brew",
                "category": "Cold Coffees",
                "price_inr": 240.0,
                "unit_or_duration": "350ml Glass Bottle",
                "phonetic_aliases": ["hazel nut", "cold brew hazelnut", "hezalnat brew", "hazelnut coffee", "nut cold brew"],
                "allowed_modifiers": ["Extra Shot", "Oat Milk", "Almond Milk", "Sugar Free"]
            },
            {
                "id": "bb-02",
                "canonical_name": "Classic Iced Americano",
                "category": "Cold Coffees",
                "price_inr": 180.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["iced americano", "ice americano", "americano cold", "black coffee with ice"],
                "allowed_modifiers": ["Double Shot", "Less Ice", "Extra Ice"]
            },
            {
                "id": "bb-03",
                "canonical_name": "Vietnamese Shakerato",
                "category": "Specialty Coffee",
                "price_inr": 260.0,
                "unit_or_duration": "250ml",
                "phonetic_aliases": ["vietnam shakerato", "shakerato", "condensed milk coffee", "sweet vietnamese coffee"],
                "allowed_modifiers": ["Less Sweet", "Extra Condensed Milk"]
            },
            {
                "id": "bb-04",
                "canonical_name": "Matcha Green Tea Latte",
                "category": "Tea & Lattes",
                "price_inr": 290.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["matcha latte", "green matcha", "japani green tea latte", "iced matcha", "latte"],
                "allowed_modifiers": ["Oat Milk", "Iced", "Hot"]
            },
            {
                "id": "bb-09",
                "canonical_name": "Caramel Artisan Latte",
                "category": "Tea & Lattes",
                "price_inr": 310.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["caramel latte", "caramel macchiato", "sweet caramel latte", "artisan latte", "latte"],
                "allowed_modifiers": ["Oat Milk", "Almond Milk", "Extra Caramel Drizzle", "Iced", "Hot"]
            },
            {
                "id": "bb-05",
                "canonical_name": "Smoked Paneer Ciabatta Panini",
                "category": "Gourmet Bites",
                "price_inr": 320.0,
                "unit_or_duration": "1 Grilled Panini",
                "phonetic_aliases": ["paneer panini", "smoked paneer sandwich", "ciabatta panini", "paneer bread toast"],
                "allowed_modifiers": ["Extra Cheese", "Spicy Jalapenos", "Gluten Free Bread"]
            },
            {
                "id": "bb-06",
                "canonical_name": "Truffle Mushroom Melt",
                "category": "Gourmet Bites",
                "price_inr": 360.0,
                "unit_or_duration": "1 Grilled Sandwich",
                "phonetic_aliases": ["mushroom melt", "truffle sandwich", "mushroom cheese toast", "truffle toast"],
                "allowed_modifiers": ["Extra Truffle Oil", "Crispy Crust"]
            },
            {
                "id": "bb-07",
                "canonical_name": "Belgian Chocolate Tiramisu",
                "category": "Desserts",
                "price_inr": 280.0,
                "unit_or_duration": "1 Box (180g)",
                "phonetic_aliases": ["tiramisu", "chocolate tiramisu", "belgian tiramisu", "tiramisu box"],
                "allowed_modifiers": ["Extra Cocoa Dusting"]
            },
            {
                "id": "bb-08",
                "canonical_name": "Lotus Biscoff Cheesecake",
                "category": "Desserts",
                "price_inr": 310.0,
                "unit_or_duration": "1 Slice",
                "phonetic_aliases": ["biscoff cheesecake", "lotus cheesecake", "biscoff slice", "cheesecake"],
                "allowed_modifiers": ["Warm Drizzle"]
            }
        ],
        "strict_policies": [
            {
                "id": "pol-bb-01",
                "rule": "Mandatory read-back: confirm item name, quantity, and total price ₹ before finalizing.",
                "severity": "CRITICAL",
                "enforcement_action": "REJECT_WITHOUT_CONFIRMATION"
            },
            {
                "id": "pol-bb-02",
                "rule": "Zero verbal or cousin/family discounts without manager live approval.",
                "severity": "CRITICAL",
                "enforcement_action": "POLITE_DECLINE"
            },
            {
                "id": "pol-bb-03",
                "rule": "Ambiguous noisy audio must trigger holding whisper co-pilot gate.",
                "severity": "HIGH",
                "enforcement_action": "TRIGGER_WHISPER_HOLD"
            }
        ],
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Brew & Bite Cafe
from typing import Literal
from pydantic import BaseModel, Field

CafeMenuItem = Literal[
    "Hazelnut Cold Brew",
    "Classic Iced Americano",
    "Vietnamese Shakerato",
    "Matcha Green Tea Latte",
    "Smoked Paneer Ciabatta Panini",
    "Truffle Mushroom Melt",
    "Belgian Chocolate Tiramisu",
    "Lotus Biscoff Cheesecake"
]

class OrderItemVerification(BaseModel):
    item: CafeMenuItem
    quantity: int = Field(default=1, ge=1, le=20)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float"""
    },
    {
        "id": "smilecare-dental",
        "name": "SmileCare Dental & Multi-Specialty Clinic",
        "domain_type": "medical_clinics",
        "tagline": "Laser Dentistry & Implant Center (Indiranagar, Bengaluru)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 420,
        "first_message": "Namaste, SmileCare Dental Clinic! Dr. Sharma ke yahan consultation ke liye call kiya hai?",
        "system_prompt": """You are Priya, the empathetic medical receptionist at SmileCare Dental & Multi-Specialty Clinic.
Your role is to schedule appointments, provide official consultation fee details, and triage emergency dental pain.

STRICT MEDICAL RECEPTION RULES:
1. Speak soothing, reassuring Hinglish with high medical courtesy. Max 14 words per turn.
2. NEVER prescribe medications or provide diagnosis over the phone.
3. If caller reports unbearable pain (score > 8) or acute bleeding, immediately trigger request_human_intervention.
4. Consultation fee is ₹600. Laser Root Canal is ₹4,500. Ultrasonic scaling is ₹1,200. Always verify exact slot with verify_catalog_item.""",
        "catalog_items": [
            {
                "id": "sc-01",
                "canonical_name": "General Specialist Consultation",
                "category": "OPD & Diagnostic",
                "price_inr": 600.0,
                "unit_or_duration": "30 mins slot",
                "phonetic_aliases": ["doctor consultation", "checkup", "teeth checkup", "consultation fee", "opd visit"],
                "allowed_modifiers": ["First Time Visit", "Follow-up Visit"]
            },
            {
                "id": "sc-02",
                "canonical_name": "Root Canal Treatment (Single Sitting)",
                "category": "Endodontics",
                "price_inr": 4500.0,
                "unit_or_duration": "45 mins slot",
                "phonetic_aliases": ["root canal", "rct", "single sitting rct", "daant ka root canal", "nerve treatment"],
                "allowed_modifiers": ["Laser Assisted", "Microscopic RCT"]
            },
            {
                "id": "sc-03",
                "canonical_name": "Ultrasonic Scaling & Polishing",
                "category": "Preventive Care",
                "price_inr": 1200.0,
                "unit_or_duration": "30 mins slot",
                "phonetic_aliases": ["scaling", "teeth cleaning", "polishing", "tartar removal", "daant safai"],
                "allowed_modifiers": ["Deep Scaling", "Stain Removal"]
            },
            {
                "id": "sc-04",
                "canonical_name": "Dental Crown (Zirconia Ceramic)",
                "category": "Prosthodontics",
                "price_inr": 6000.0,
                "unit_or_duration": "1 Unit Cap",
                "phonetic_aliases": ["crown", "dental cap", "zirconia cap", "ceramic cap", "daant ki topi"],
                "allowed_modifiers": ["10-Year Warranty", "Premium Translucent"]
            },
            {
                "id": "sc-05",
                "canonical_name": "Teeth Whitening (In-Office Laser)",
                "category": "Cosmetic Care",
                "price_inr": 7500.0,
                "unit_or_duration": "60 mins procedure",
                "phonetic_aliases": ["teeth whitening", "laser bleaching", "smile brightening", "daant chamkana"],
                "allowed_modifiers": ["Sensitivity Guard"]
            }
        ],
        "strict_policies": [
            {
                "id": "pol-sc-01",
                "rule": "Zero phone prescriptions or diagnostic commitments under Medical Council guidelines.",
                "severity": "CRITICAL",
                "enforcement_action": "POLITE_DECLINE"
            },
            {
                "id": "pol-sc-02",
                "rule": "Acute pain triage (>8/10 or swelling) escalates immediately to Clinic Manager.",
                "severity": "CRITICAL",
                "enforcement_action": "ESCALATE_TRANSFER"
            }
        ],
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for SmileCare Dental
from typing import Literal
from pydantic import BaseModel, Field

ClinicService = Literal[
    "General Specialist Consultation",
    "Root Canal Treatment (Single Sitting)",
    "Ultrasonic Scaling & Polishing",
    "Dental Crown (Zirconia Ceramic)",
    "Teeth Whitening (In-Office Laser)"
]

class ClinicBookingVerification(BaseModel):
    service: ClinicService
    patient_name: str
    preferred_slot: str
    fee_inr: float"""
    },
    {
        "id": "apex-gurgaon-realty",
        "name": "Apex Gurgaon Realty",
        "domain_type": "real_estate",
        "tagline": "Luxury High-Rise & Commercial Real Estate (Golf Course Ext. Road)",
        "language_code": "en-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 420,
        "first_message": "Good day, Apex Gurgaon Realty. Looking for luxury residential apartments or commercial retail?",
        "system_prompt": """You are Aarav, senior client relationship host at Apex Gurgaon Realty.
Your objective is to qualify high-net-worth real estate buyers, present verified luxury listings, and schedule private site visits.

OPERATING GUIDELINES:
1. Maintain sophisticated, polished Indian English tone. Max 15 words per turn.
2. Verify buyer budget bracket and location preference (Sector 65, Golf Course Road, Sector 42).
3. Do not quote unauthorized developer discounts over phone. Site visit appointments require 24h prior slot reservation.""",
        "catalog_items": [
            {
                "id": "ar-01",
                "canonical_name": "3BHK Ultra-Luxury Apartment (Sector 65)",
                "category": "Luxury Residential",
                "price_inr": 32500000.0,
                "unit_or_duration": "2,450 sq.ft Carpet",
                "phonetic_aliases": ["3bhk sector 65", "three bhk luxury", "sector 65 apartment", "golf course ext 3bhk"],
                "allowed_modifiers": ["Park Facing", "High Floor 20+"]
            },
            {
                "id": "ar-02",
                "canonical_name": "4BHK Sky Penthouse with Private Terrace (Sector 42)",
                "category": "Super Luxury Penthouses",
                "price_inr": 78000000.0,
                "unit_or_duration": "5,200 sq.ft Duplex",
                "phonetic_aliases": ["4bhk penthouse", "sky penthouse sector 42", "duplex penthouse", "terrace penthouse"],
                "allowed_modifiers": ["Private Plunge Pool", "4 Covered Car Parks"]
            },
            {
                "id": "ar-03",
                "canonical_name": "Grade-A Commercial Retail Space (Sector 54)",
                "category": "Commercial Properties",
                "price_inr": 19500000.0,
                "unit_or_duration": "1,150 sq.ft Double Height",
                "phonetic_aliases": ["commercial shop", "retail space sector 54", "golf course road shop"],
                "allowed_modifiers": ["Road Facing", "Pre-Leased Brand"]
            },
            {
                "id": "ar-04",
                "canonical_name": "Private VIP Site Visit Schedule",
                "category": "Concierge Services",
                "price_inr": 0.0,
                "unit_or_duration": "Dedicated Chauffeur Pick",
                "phonetic_aliases": ["site visit", "property visit", "inspection appointment", "dekhne aana hai"],
                "allowed_modifiers": ["Weekend Slot", "Weekday Slot"]
            }
        ],
        "strict_policies": [
            {
                "id": "pol-ar-01",
                "rule": "Site visit scheduling requires buyer phone number and tentative move-in timeframe.",
                "severity": "CRITICAL",
                "enforcement_action": "COLLECT_PHONE"
            },
            {
                "id": "pol-ar-02",
                "rule": "Never negotiate unofficial developer discounts over phone.",
                "severity": "HIGH",
                "enforcement_action": "DEFLECT_TO_IN_PERSON"
            }
        ],
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Apex Gurgaon Realty
from typing import Literal
from pydantic import BaseModel, Field

RealtyProperty = Literal[
    "3BHK Ultra-Luxury Apartment (Sector 65)",
    "4BHK Sky Penthouse with Private Terrace (Sector 42)",
    "Grade-A Commercial Retail Space (Sector 54)",
    "Private VIP Site Visit Schedule"
]

class RealtyInterestVerification(BaseModel):
    property: RealtyProperty
    buyer_budget_cr: float
    preferred_site_visit_date: str"""
    },
    {
        "id": "quickkart-d2c",
        "name": "QuickKart D2C Support",
        "domain_type": "support_collections",
        "tagline": "Instant Commerce Logistics & Operations (10-Minute Delivery)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 400,
        "first_message": "Hello, QuickKart Priority Support! Aapka order track karne mein madad kar sakti hu?",
        "system_prompt": """You are Neha, fast-paced customer care resolution executive at QuickKart instant delivery.
Your goal is to handle delayed delivery inquiries, missing item complaints, and return pickups with zero friction.

RULES OF ENGAGEMENT:
1. Maximum 12 words per turn. High-speed, energetic Hinglish tone.
2. Always ask for 9-digit Order ID (#QK-XXXXX) before providing status or refunds.
3. For spoiled/damaged items up to ₹500, trigger instant wallet refund tool. Above ₹500, require photo inspection or agent transfer.""",
        "catalog_items": [
            {
                "id": "qk-01",
                "canonical_name": "Instant Order Live Status Check",
                "category": "Order Tracking",
                "price_inr": 0.0,
                "unit_or_duration": "Instant ETA Lookup",
                "phonetic_aliases": ["order status", "kahan pahuncha order", "track delivery", "rider location"],
                "allowed_modifiers": ["Rider Contact Number"]
            },
            {
                "id": "qk-02",
                "canonical_name": "Damaged Item Wallet Refund",
                "category": "Claims & Resolution",
                "price_inr": 0.0,
                "unit_or_duration": "Instant Credit",
                "phonetic_aliases": ["refund", "item damaged", "kharab samaan", "paise wapas", "wallet credit"],
                "allowed_modifiers": ["QuickKart Cash", "Source Bank UPI"]
            },
            {
                "id": "qk-03",
                "canonical_name": "Express Return Pickup Window",
                "category": "Returns",
                "price_inr": 50.0,
                "unit_or_duration": "20 Mins Rider Slot",
                "phonetic_aliases": ["return pickup", "wapas le jao", "return order", "pickup slot"],
                "allowed_modifiers": ["Doorstep Sealed Bag"]
            }
        ],
        "strict_policies": [
            {
                "id": "pol-qk-01",
                "rule": "Refunds > ₹1000 require human supervisor approval or escalation.",
                "severity": "CRITICAL",
                "enforcement_action": "ESCALATE_TRANSFER"
            },
            {
                "id": "pol-qk-02",
                "rule": "Order tracking requires valid 9-digit order number.",
                "severity": "HIGH",
                "enforcement_action": "PROMPT_ORDER_ID"
            }
        ],
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for QuickKart D2C
from typing import Literal
from pydantic import BaseModel, Field

SupportAction = Literal[
    "Instant Order Live Status Check",
    "Damaged Item Wallet Refund",
    "Express Return Pickup Window"
]

class SupportTicketVerification(BaseModel):
    action: SupportAction
    order_id: str
    issue_category: str"""
    }
]
