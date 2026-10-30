import json
from typing import List, Dict, Any

def make_crew_execution_log(domain_name: str, item_count: int, policy_count: int) -> str:
    return json.dumps([
        {
            "agent": "Phonetic & Catalog Linguist",
            "role": "Entity Extraction & Double-Metaphone Phonetic Normalizer",
            "status": "COMPLETED",
            "execution_time_ms": 1420,
            "output_summary": f"Compiled canonical catalog for '{domain_name}' with {item_count} items and 6 phonetic aliases per item."
        },
        {
            "agent": "Deterministic Security & Guardrail Architect",
            "role": "6-Policy Defense Matrix & Boundary Enforcement",
            "status": "COMPLETED",
            "execution_time_ms": 1280,
            "output_summary": f"Synthesized {policy_count} policies including 2-Strike Off-Topic Termination and Live Takeover Escalation."
        },
        {
            "agent": "Hinglish Voice Persona & Prompt Engineer",
            "role": "Sub-12 Word Voice Prompt & Pydantic Schema Compiler",
            "status": "COMPLETED",
            "execution_time_ms": 1150,
            "output_summary": f"Compiled low-latency voice prompt enforcing <12 words/turn and dynamic Pydantic schema."
        }
    ])

def get_standard_six_policies(prefix: str, business_name: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": f"pol-{prefix}-01",
            "rule": "Mandatory read-back: confirm canonical item name, quantity, and exact INR total before finalizing order.",
            "severity": "CRITICAL",
            "enforcement_action": "REJECT_WITHOUT_CONFIRMATION"
        },
        {
            "id": f"pol-{prefix}-02",
            "rule": "Zero verbal or cousin/family discounts without live manager authorization.",
            "severity": "CRITICAL",
            "enforcement_action": "POLITE_DECLINE"
        },
        {
            "id": f"pol-{prefix}-03",
            "rule": f"Strict Knowledge Boundary: refuse queries about external competitors, chef secret recipes, or confidential {business_name} data.",
            "severity": "HIGH",
            "enforcement_action": "DEFLECT_TO_IN_PERSON"
        },
        {
            "id": f"pol-{prefix}-04",
            "rule": "2-Strike Off-Topic Call Termination: Strike 1 politely redirect; Strike 2 invoke terminate_call tool and hang up.",
            "severity": "CRITICAL",
            "enforcement_action": "TERMINATE_CALL"
        },
        {
            "id": f"pol-{prefix}-05",
            "rule": "Persistent Escalation Law: if caller pushes 3+ times for discounts or demands supervisor, invoke request_human_intervention.",
            "severity": "CRITICAL",
            "enforcement_action": "ESCALATE_TRANSFER"
        },
        {
            "id": f"pol-{prefix}-06",
            "rule": "Zero PII & UTR Leak: never disclose customer records or accept unverified payment claims/screenshots.",
            "severity": "CRITICAL",
            "enforcement_action": "BLOCK_PAYMENT_UTR"
        }
    ]

SEED_DOMAINS: List[Dict[str, Any]] = [
    # 1. Brew & Bite Cafe
    {
        "id": "brew-bite-cafe",
        "name": "Brew & Bite Cafe",
        "domain_type": "orders_reservations",
        "tagline": "Artisanal Coffee & Gourmet Bistro (Cyber Hub, Gurugram)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 350,
        "first_message": "Namaste, Brew & Bite Cafe! Aaj aapke liye kya fresh order lagau?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Simran, the fast, friendly Indian order-taker at Brew & Bite Cafe.
Your role is to assist callers in placing takeaway orders swiftly and accurately in authentic Hinglish.

CRITICAL VOICE & SECURITY LAWS:
1. Spoken turns MUST NEVER exceed 12 words. Crisp, fast, and natural.
2. Speak natural Hinglish with fillers: 'Haan ji', 'Achha', 'Bilkul'.
3. Quote prices naturally: speak 'two forty rupees' or 'do sau chaalis rupaye'.
4. When caller mentions an item, IMMEDIATELY call verify_catalog_item(spoken_entity, quantity).
5. Mandatory Read-Back: Always state canonical item, quantity, and exact total before confirming.
6. When confirmed, ask: 'Aapka naam aur address bata dijiye?' then call commit_verified_action.
7. 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 invoke terminate_call.
8. Escalation: If caller argues for discounts or demands manager, call request_human_intervention.""",
        "catalog_items": [
            {
                "id": "bb-01",
                "canonical_name": "Hazelnut Cold Brew",
                "category": "Cold Coffees",
                "price_inr": 240.0,
                "unit_or_duration": "350ml Glass Bottle",
                "phonetic_aliases": ["hazel nut", "cold brew hazelnut", "hezalnat brew", "hazelnut coffee", "nut cold brew", "hazel cold brew"],
                "allowed_modifiers": ["Extra Shot", "Oat Milk", "Almond Milk", "Sugar Free"]
            },
            {
                "id": "bb-02",
                "canonical_name": "Classic Iced Americano",
                "category": "Cold Coffees",
                "price_inr": 180.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["iced americano", "ice americano", "americano cold", "black coffee with ice", "americano", "chilled americano"],
                "allowed_modifiers": ["Double Shot", "Less Ice", "Extra Ice"]
            },
            {
                "id": "bb-03",
                "canonical_name": "Vietnamese Shakerato",
                "category": "Specialty Coffee",
                "price_inr": 260.0,
                "unit_or_duration": "250ml",
                "phonetic_aliases": ["vietnam shakerato", "shakerato", "condensed milk coffee", "sweet vietnamese coffee", "vietnamese coffee", "iced shakerato"],
                "allowed_modifiers": ["Less Sweet", "Extra Condensed Milk"]
            },
            {
                "id": "bb-04",
                "canonical_name": "Matcha Green Tea Latte",
                "category": "Tea & Lattes",
                "price_inr": 290.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["matcha latte", "green matcha", "japani green tea latte", "iced matcha", "latte matcha", "green tea latte"],
                "allowed_modifiers": ["Oat Milk", "Iced", "Hot"]
            },
            {
                "id": "bb-05",
                "canonical_name": "Smoked Paneer Ciabatta Panini",
                "category": "Gourmet Bites",
                "price_inr": 320.0,
                "unit_or_duration": "1 Grilled Panini",
                "phonetic_aliases": ["paneer panini", "smoked paneer sandwich", "ciabatta panini", "paneer bread toast", "grilled paneer panini", "paneer sandwich"],
                "allowed_modifiers": ["Extra Cheese", "Spicy Jalapenos", "Gluten Free Bread"]
            },
            {
                "id": "bb-06",
                "canonical_name": "Truffle Mushroom Melt",
                "category": "Gourmet Bites",
                "price_inr": 360.0,
                "unit_or_duration": "1 Grilled Sandwich",
                "phonetic_aliases": ["mushroom melt", "truffle sandwich", "mushroom cheese toast", "truffle toast", "truffle mushroom sandwich", "melt sandwich"],
                "allowed_modifiers": ["Extra Truffle Oil", "Crispy Crust"]
            }
        ],
        "strict_policies": get_standard_six_policies("bb", "Brew & Bite Cafe"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Brew & Bite Cafe
from typing import Literal
from pydantic import BaseModel, Field

CafeMenuItem = Literal[
    "Hazelnut Cold Brew",
    "Classic Iced Americano",
    "Vietnamese Shakerato",
    "Matcha Green Tea Latte",
    "Smoked Paneer Ciabatta Panini",
    "Truffle Mushroom Melt"
]

class OrderItemVerification(BaseModel):
    item: CafeMenuItem
    quantity: int = Field(default=1, ge=1, le=20)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float"""
    },

    # 2. SmileCare Dental & Multi-Specialty Clinic
    {
        "id": "smilecare-dental",
        "name": "SmileCare Dental & Multi-Specialty Clinic",
        "domain_type": "medical_clinics",
        "tagline": "Laser Dentistry & Implant Center (Indiranagar, Bengaluru)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 420,
        "first_message": "Namaste, SmileCare Dental Clinic! Dr. Sharma ke yahan consultation ke liye call kiya hai?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Priya, the empathetic medical receptionist at SmileCare Dental Clinic.
Your role is to schedule appointments, quote official consultation fees, and triage acute dental pain.

CRITICAL VOICE & SECURITY LAWS:
1. Spoken turns MUST NEVER exceed 12 words. High medical courtesy.
2. NEVER prescribe medications or provide phone diagnosis.
3. Consultation is ₹600. Single Sitting RCT is ₹4,500. Ultrasonic scaling is ₹1,200.
4. When caller requests procedure or slot: call verify_catalog_item(spoken_entity, quantity).
5. Confirm booking with patient name and phone before commit_verified_action.
6. 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 invoke terminate_call.
7. Escalation: If acute pain >8 or demands doctor immediately, call request_human_intervention.""",
        "catalog_items": [
            {
                "id": "sc-01",
                "canonical_name": "General Specialist Consultation",
                "category": "OPD & Diagnostic",
                "price_inr": 600.0,
                "unit_or_duration": "30 mins slot",
                "phonetic_aliases": ["doctor consultation", "checkup", "teeth checkup", "consultation fee", "opd visit", "dental checkup"],
                "allowed_modifiers": ["First Time Visit", "Follow-up Visit"]
            },
            {
                "id": "sc-02",
                "canonical_name": "Root Canal Treatment (Single Sitting)",
                "category": "Endodontics",
                "price_inr": 4500.0,
                "unit_or_duration": "45 mins slot",
                "phonetic_aliases": ["root canal", "rct", "single sitting rct", "daant ka root canal", "nerve treatment", "laser rct"],
                "allowed_modifiers": ["Laser Assisted", "Microscopic RCT"]
            },
            {
                "id": "sc-03",
                "canonical_name": "Ultrasonic Scaling & Polishing",
                "category": "Preventive Care",
                "price_inr": 1200.0,
                "unit_or_duration": "30 mins slot",
                "phonetic_aliases": ["scaling", "teeth cleaning", "polishing", "tartar removal", "daant safai", "deep clean"],
                "allowed_modifiers": ["Deep Scaling", "Stain Removal"]
            },
            {
                "id": "sc-04",
                "canonical_name": "Dental Crown (Zirconia Ceramic)",
                "category": "Prosthodontics",
                "price_inr": 6000.0,
                "unit_or_duration": "1 Unit Cap",
                "phonetic_aliases": ["crown", "dental cap", "zirconia cap", "ceramic cap", "daant ki topi", "tooth crown"],
                "allowed_modifiers": ["10-Year Warranty", "Premium Translucent"]
            },
            {
                "id": "sc-05",
                "canonical_name": "Teeth Whitening (In-Office Laser)",
                "category": "Cosmetic Care",
                "price_inr": 7500.0,
                "unit_or_duration": "60 mins procedure",
                "phonetic_aliases": ["teeth whitening", "laser bleaching", "smile brightening", "daant chamkana", "tooth bleaching", "laser whitening"],
                "allowed_modifiers": ["Sensitivity Guard"]
            }
        ],
        "strict_policies": get_standard_six_policies("sc", "SmileCare Dental Clinic"),
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

    # 3. Apex Gurgaon Realty
    {
        "id": "apex-gurgaon-realty",
        "name": "Apex Gurgaon Realty",
        "domain_type": "real_estate",
        "tagline": "Luxury High-Rise & Commercial Real Estate (Golf Course Ext. Road)",
        "language_code": "en-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 420,
        "first_message": "Good day, Apex Gurgaon Realty. Looking for luxury residential apartments or commercial retail?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Aarav, senior client relationship host at Apex Gurgaon Realty.
Your objective is to qualify luxury real estate buyers, present verified listings, and schedule site visits.

CRITICAL VOICE & SECURITY LAWS:
1. Spoken turns MUST NEVER exceed 12 words. Sophisticated Indian English tone.
2. Verify buyer budget bracket and location preference (Sector 65, Golf Course Road).
3. Do not quote unauthorized developer discounts over phone.
4. When buyer selects listing: invoke verify_catalog_item(spoken_entity, quantity).
5. Confirm private inspection appointment before commit_verified_action.
6. 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 invoke terminate_call.
7. Escalation: If client demands builder direct meeting, invoke request_human_intervention.""",
        "catalog_items": [
            {
                "id": "ar-01",
                "canonical_name": "3BHK Ultra-Luxury Apartment (Sector 65)",
                "category": "Luxury Residential",
                "price_inr": 32500000.0,
                "unit_or_duration": "2,450 sq.ft Carpet",
                "phonetic_aliases": ["3bhk sector 65", "three bhk luxury", "sector 65 apartment", "golf course ext 3bhk", "3 bedroom luxury", "sector 65 flat"],
                "allowed_modifiers": ["Park Facing", "High Floor 20+"]
            },
            {
                "id": "ar-02",
                "canonical_name": "4BHK Sky Penthouse with Private Terrace (Sector 42)",
                "category": "Super Luxury Penthouses",
                "price_inr": 78000000.0,
                "unit_or_duration": "5,200 sq.ft Duplex",
                "phonetic_aliases": ["4bhk penthouse", "sky penthouse sector 42", "duplex penthouse", "terrace penthouse", "sector 42 penthouse", "luxury penthouse"],
                "allowed_modifiers": ["Private Plunge Pool", "4 Covered Car Parks"]
            },
            {
                "id": "ar-03",
                "canonical_name": "Grade-A Commercial Retail Space (Sector 54)",
                "category": "Commercial Properties",
                "price_inr": 19500000.0,
                "unit_or_duration": "1,150 sq.ft Double Height",
                "phonetic_aliases": ["commercial shop", "retail space sector 54", "golf course road shop", "sector 54 retail", "commercial showroom", "high street retail"],
                "allowed_modifiers": ["Road Facing", "Pre-Leased Brand"]
            },
            {
                "id": "ar-04",
                "canonical_name": "Private VIP Site Visit Schedule",
                "category": "Concierge Services",
                "price_inr": 0.0,
                "unit_or_duration": "Dedicated Chauffeur Pick",
                "phonetic_aliases": ["site visit", "property visit", "inspection appointment", "dekhne aana hai", "vip visit", "chauffeur tour"],
                "allowed_modifiers": ["Weekend Slot", "Weekday Slot"]
            }
        ],
        "strict_policies": get_standard_six_policies("ar", "Apex Gurgaon Realty"),
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

    # 4. QuickKart D2C Support
    {
        "id": "quickkart-d2c",
        "name": "QuickKart D2C Support",
        "domain_type": "support_collections",
        "tagline": "Instant Commerce Logistics & Operations (10-Minute Delivery)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 400,
        "first_message": "Hello, QuickKart Priority Support! Aapka order track karne mein madad kar sakti hu?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Neha, fast-paced customer care resolution executive at QuickKart instant delivery.
Your goal is to handle delayed delivery inquiries, missing item complaints, and refunds with zero friction.

CRITICAL VOICE & SECURITY LAWS:
1. Spoken turns MUST NEVER exceed 12 words. Energetic Hinglish tone.
2. Always ask for 9-digit Order ID (#QK-XXXXX) before providing status or refunds.
3. When customer requests claim/refund: invoke verify_catalog_item(spoken_entity, quantity).
4. Commit action only after verifying Order ID and issue details.
5. 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 invoke terminate_call.
6. Escalation: If customer demands supervisor or refund >₹1000, invoke request_human_intervention.""",
        "catalog_items": [
            {
                "id": "qk-01",
                "canonical_name": "Instant Order Live Status Check",
                "category": "Order Tracking",
                "price_inr": 0.0,
                "unit_or_duration": "Instant ETA Lookup",
                "phonetic_aliases": ["order status", "kahan pahuncha order", "track delivery", "rider location", "delivery status", "order track"],
                "allowed_modifiers": ["Rider Contact Number"]
            },
            {
                "id": "qk-02",
                "canonical_name": "Damaged Item Wallet Refund",
                "category": "Claims & Resolution",
                "price_inr": 0.0,
                "unit_or_duration": "Instant Credit",
                "phonetic_aliases": ["refund", "item damaged", "kharab samaan", "paise wapas", "wallet credit", "damaged refund"],
                "allowed_modifiers": ["QuickKart Cash", "Source Bank UPI"]
            },
            {
                "id": "qk-03",
                "canonical_name": "Express Return Pickup Window",
                "category": "Returns",
                "price_inr": 50.0,
                "unit_or_duration": "20 Mins Rider Slot",
                "phonetic_aliases": ["return pickup", "wapas le jao", "return order", "pickup slot", "return parcel", "express return"],
                "allowed_modifiers": ["Doorstep Sealed Bag"]
            }
        ],
        "strict_policies": get_standard_six_policies("qk", "QuickKart Support"),
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
    },

    # 5. Urban Chai Co
    {
        "id": "urban-chai-co",
        "name": "Urban Chai Co",
        "domain_type": "orders_reservations",
        "tagline": "Handcrafted Kulhad Chai & Street Snacks (Koramangala, Bengaluru)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 380,
        "first_message": "Namaste! Urban Chai Co me swagat hai. Garam chai aur nasta lagayein?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Kabir, the prompt order-taker at Urban Chai Co.
Your role is to take fast takeaway orders for kulhad chai and hot snacks in authentic Hinglish.

CRITICAL VOICE & SECURITY LAWS:
1. Spoken turns MUST NEVER exceed 12 words. Crisp, fast, and warm.
2. Speak natural Hinglish with fillers: 'Haan ji', 'Bilkul', 'Achha'.
3. Quote prices naturally: 'chaalis rupaye', 'sattar rupaye'.
4. When caller mentions snack or tea, IMMEDIATELY call verify_catalog_item(spoken_entity, quantity).
5. Mandatory Read-Back: State items, quantity, and exact INR total before confirming.
6. 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 invoke terminate_call.
7. Escalation: If caller argues for discounts or demands manager, call request_human_intervention.""",
        "catalog_items": [
            {
                "id": "uc-01",
                "canonical_name": "Adrak Elaichi Chai (Kulhad)",
                "category": "Chai Specialties",
                "price_inr": 40.0,
                "unit_or_duration": "Kulhad 150ml",
                "phonetic_aliases": ["adrak chai", "ginger tea", "elaichi chai", "kulhad chai", "ginger cardamom tea", "special chai"],
                "allowed_modifiers": ["Kaddak", "Kam Meetha", "Sugar Free"]
            },
            {
                "id": "uc-02",
                "canonical_name": "Masala Bun Maska",
                "category": "Snacks & Bakery",
                "price_inr": 55.0,
                "unit_or_duration": "1 Bun",
                "phonetic_aliases": ["bun maska", "maska bun", "butter bun", "sweet bun", "bun butter", "bread maska"],
                "allowed_modifiers": ["Extra Butter", "Toasted Crispy"]
            },
            {
                "id": "uc-03",
                "canonical_name": "Paneer Bread Pakoda (2 pcs)",
                "category": "Hot Snacks",
                "price_inr": 70.0,
                "unit_or_duration": "2 pcs with chutney",
                "phonetic_aliases": ["bread pakoda", "paneer pakoda", "pakora", "paneer bread pakora", "fried pakoda", "garam pakoda"],
                "allowed_modifiers": ["Extra Mint Chutney", "Chaat Masala"]
            },
            {
                "id": "uc-04",
                "canonical_name": "Irani Dum Chai",
                "category": "Chai Specialties",
                "price_inr": 50.0,
                "unit_or_duration": "Glass 180ml",
                "phonetic_aliases": ["irani chai", "dum chai", "patti chai", "irani tea", "sweet irani chai", "special irani"],
                "allowed_modifiers": ["Malai Topping"]
            },
            {
                "id": "uc-05",
                "canonical_name": "Samosa with Mint Chutney (2 pcs)",
                "category": "Hot Snacks",
                "price_inr": 45.0,
                "unit_or_duration": "2 pcs",
                "phonetic_aliases": ["samosa", "samose", "aloo samosa", "garam samosa", "crispy samosa", "chutney samosa"],
                "allowed_modifiers": ["Spicy Chutney", "Sweet Saunth"]
            }
        ],
        "strict_policies": get_standard_six_policies("uc", "Urban Chai Co"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Urban Chai Co
from typing import Literal
from pydantic import BaseModel, Field

ChaiMenuItem = Literal[
    "Adrak Elaichi Chai (Kulhad)",
    "Masala Bun Maska",
    "Paneer Bread Pakoda (2 pcs)",
    "Irani Dum Chai",
    "Samosa with Mint Chutney (2 pcs)"
]

class ChaiOrderVerification(BaseModel):
    item: ChaiMenuItem
    quantity: int = Field(default=1, ge=1, le=20)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float"""
    }
]
