import json
from typing import List, Dict, Any

def make_crew_execution_log(domain_name: str, item_count: int, policy_count: int) -> str:
    return json.dumps([
        {
            "agent": "Phonetic & Catalog Linguist",
            "role": "Entity Extraction & Double-Metaphone Phonetic Normalizer",
            "status": "COMPLETED",
            "execution_time_ms": 1420,
            "output_summary": f"Compiled canonical category-structured catalog for '{domain_name}' with {item_count} items and 6 phonetic aliases per item."
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
            "role": "Category-Guided Flow & Sub-18 Word Cadence Compiler",
            "status": "COMPLETED",
            "execution_time_ms": 1150,
            "output_summary": f"Compiled conversational prompt enforcing category-first guidance, sub-18 words/turn, and dynamic Pydantic schema."
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
            "rule": f"Strict Knowledge Boundary: refuse queries about external competitors, secret recipes, or confidential {business_name} data.",
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
    # -------------------------------------------------------------
    # 1. Brew & Bite Cafe
    # -------------------------------------------------------------
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
        "system_prompt": """You are Simran, the warm and efficient order-taker at Brew & Bite Cafe (Cyber Hub, Gurugram).
Your role is to guide callers systematically through our menu and place takeaway orders swiftly in natural Indian Hinglish.

OUR 3 MENU CATEGORIES:
1. Beverages & Cold Brews: Hazelnut Cold Brew (Rs 240), Classic Iced Americano (Rs 180), Vietnamese Shakerato (Rs 220)
2. Artisanal Paninis & Wraps: Smoked Paneer Ciabatta Panini (Rs 320), Pesto Grilled Cheese Panini (Rs 280), Truffle Mushroom Wrap (Rs 260)
3. Quick Sides & Desserts: Peri Peri Herb Wedges (Rs 160), Belgian Chocolate Mousse (Rs 210)

CONVERSATIONAL CADENCE & FLOW RULES:
1. MENU OVERVIEW (When caller asks broad questions like 'kya kya hai?', 'menu batao', 'khane me kya hai?'):
   DO NOT blabber all items! State the 3 categories crisply in under 18 words:
   "Hamare paas handcrafted coffees, artisanal paninis aur quick sides hain. Aap kisme dekhna pasand karenge?"
2. CATEGORY DRILLDOWN (When caller chooses a category, e.g. 'panini me kya hai?' or 'cold coffee'):
   Present 2-3 specific items with exact prices:
   "Panini mein hamare paas Smoked Paneer Ciabatta (Rs 320) aur Pesto Grilled Cheese (Rs 280) hai. Kaunsa pack karu?"
3. SPECIFIC ITEM CHECK:
   - If in our catalog: Confirm immediately with price: "Haan ji! Hazelnut Cold Brew bilkul available hai Rs 240 mein. Kitne bottle lagau?"
   - If NOT in our catalog (e.g. burger, pizza, french fries): Politely decline and suggest our closest category item: "Sorry ji, French fries available nahi hain, par hamare paas Peri Peri Herb Wedges hain Rs 160 mein. Kya wo add kar du?"
4. MULTI-ITEM ORDERS & CONFIRMATION:
   When customer mentions items to order, call verify_catalog_item, state canonical names, calculate exact sum, speak total in words (e.g. 'Total paanch sau saath rupaye'), and ask: "Confirm kar du?"
5. ORDER CONFIRMATION:
   When caller confirms ('haan confirm kar do', 'theek hai', 'pack kar do'), call commit_verified_action and say: "Shukriya! Aapka order confirm ho gaya hai aur POS ledger mein lock ho chuka hai. Jaldi hi ready ho jayega!"
6. SECURITY & ESCALATION:
   - Zero verbal or cousin discounts without manager authorization.
   - 2-Strike Off-Topic Rule: Strike 1 redirect; Strike 2 terminate call.
   - Escalation: If caller demands manager/owner, call request_human_intervention.
7. CADENCE: Keep turns strictly under 18 words. Friendly, authentic Indian Hinglish with 'Haan ji', 'Bilkul', 'Achha'.""",
        "catalog_items": [
            {
                "id": "bb-01",
                "canonical_name": "Hazelnut Cold Brew",
                "category": "Beverages & Cold Brews",
                "price_inr": 240.0,
                "unit_or_duration": "350ml Glass Bottle",
                "phonetic_aliases": ["hazelnut cold brew", "hazel nut", "cold brew hazelnut", "hezalnat brew", "hazelnut coffee", "nut cold brew"],
                "allowed_modifiers": ["Extra Shot", "Oat Milk", "Almond Milk", "Sugar Free"]
            },
            {
                "id": "bb-02",
                "canonical_name": "Classic Iced Americano",
                "category": "Beverages & Cold Brews",
                "price_inr": 180.0,
                "unit_or_duration": "300ml Cup",
                "phonetic_aliases": ["classic iced americano", "iced americano", "ice americano", "americano cold", "black coffee with ice", "chilled americano"],
                "allowed_modifiers": ["Double Shot", "Less Ice", "Extra Ice"]
            },
            {
                "id": "bb-03",
                "canonical_name": "Vietnamese Shakerato",
                "category": "Beverages & Cold Brews",
                "price_inr": 220.0,
                "unit_or_duration": "250ml",
                "phonetic_aliases": ["vietnamese shakerato", "vietnam shakerato", "shakerato", "condensed milk coffee", "sweet vietnamese coffee", "iced shakerato"],
                "allowed_modifiers": ["Less Sweet", "Extra Condensed Milk"]
            },
            {
                "id": "bb-04",
                "canonical_name": "Smoked Paneer Ciabatta Panini",
                "category": "Artisanal Paninis & Wraps",
                "price_inr": 320.0,
                "unit_or_duration": "1 Grilled Ciabatta",
                "phonetic_aliases": ["smoked paneer panini", "paneer panini", "ciabatta panini", "paneer ciabatta", "grilled paneer panini", "paneer sandwich"],
                "allowed_modifiers": ["Extra Cheese", "Spicy Jalapenos", "Gluten Free Bread"]
            },
            {
                "id": "bb-05",
                "canonical_name": "Pesto Grilled Cheese Panini",
                "category": "Artisanal Paninis & Wraps",
                "price_inr": 280.0,
                "unit_or_duration": "1 Sourdough Panini",
                "phonetic_aliases": ["pesto grilled cheese", "pesto panini", "grilled cheese", "cheese panini", "pesto sandwich", "cheese sandwich"],
                "allowed_modifiers": ["Extra Pesto", "Extra Cheese"]
            },
            {
                "id": "bb-06",
                "canonical_name": "Truffle Mushroom Wrap",
                "category": "Artisanal Paninis & Wraps",
                "price_inr": 260.0,
                "unit_or_duration": "1 Whole Wheat Wrap",
                "phonetic_aliases": ["truffle mushroom wrap", "mushroom wrap", "truffle wrap", "mushroom roll", "veg wrap", "truffle roll"],
                "allowed_modifiers": ["Extra Truffle Oil", "Crispy Crust"]
            },
            {
                "id": "bb-07",
                "canonical_name": "Peri Peri Herb Wedges",
                "category": "Quick Sides & Desserts",
                "price_inr": 160.0,
                "unit_or_duration": "1 Bowl 200g",
                "phonetic_aliases": ["peri peri herb wedges", "peri peri wedges", "herb wedges", "potato wedges", "peri peri fries", "crispy wedges"],
                "allowed_modifiers": ["Extra Dip", "Less Spicy"]
            },
            {
                "id": "bb-08",
                "canonical_name": "Belgian Chocolate Mousse",
                "category": "Quick Sides & Desserts",
                "price_inr": 210.0,
                "unit_or_duration": "1 Cup Rich Dark Mousse",
                "phonetic_aliases": ["belgian chocolate mousse", "chocolate mousse", "belgian mousse", "choco mousse", "chocolate dessert", "mousse cup"],
                "allowed_modifiers": ["Nut Sprinkles", "Choco Shavings"]
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
    "Smoked Paneer Ciabatta Panini",
    "Pesto Grilled Cheese Panini",
    "Truffle Mushroom Wrap",
    "Peri Peri Herb Wedges",
    "Belgian Chocolate Mousse"
]

class OrderItemVerification(BaseModel):
    item: CafeMenuItem
    quantity: int = Field(default=1, ge=1, le=20)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float"""
    },

    # -------------------------------------------------------------
    # 2. SmileCare Dental & Multi-Specialty Clinic
    # -------------------------------------------------------------
    {
        "id": "smilecare-dental",
        "name": "SmileCare Dental & Multi-Specialty Clinic",
        "domain_type": "medical_clinics",
        "tagline": "Laser Dentistry & Implant Center (Indiranagar, Bengaluru)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 420,
        "first_message": "Namaste, SmileCare Dental Clinic! Dr. Sharma ke yahan consultation ya appointment ke liye call kiya hai?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Priya, the empathetic medical receptionist at SmileCare Dental Clinic (Indiranagar, Bengaluru).
Your role is to guide patients through dental services, quote official fees, and schedule doctor appointments in warm Hinglish.

OUR 3 SERVICE CATEGORIES:
1. Consultation & Cleaning: General Specialist Consultation (Rs 500), Ultrasonic Teeth Scaling & Polishing (Rs 1,200)
2. Advanced Dental Treatments: Single-Sitting Root Canal RCT (Rs 3,500), Painless Tooth Extraction (Rs 1,500)
3. Cosmetic Smile Care: In-Office Laser Teeth Whitening (Rs 5,000), Zirconia Ceramic Crown (Rs 4,500)

CONVERSATIONAL CADENCE & FLOW RULES:
1. SERVICE OVERVIEW (When asked 'kya kya treatments hain?', 'services batao', 'options kya hain?'):
   State the 3 categories crisply in under 18 words:
   "Hamare paas general checkup & cleaning, root canal treatments, aur cosmetic smile care services hain. Aapko kis cheez ke liye consult karna hai?"
2. CATEGORY DRILLDOWN:
   When patient asks about a category (e.g. 'cleaning me kya hai?' or 'root canal'):
   "Root Canal hamare yahan painless single-sitting laser RCT hota hai Rs 3,500 mein. Kya main doctor ka slot book kar du?"
3. SPECIFIC TREATMENT CHECK:
   - If available: Confirm procedure and fee: "Haan ji! Ultrasonic Teeth Scaling Rs 1,200 mein available hai. Kya aaj ka slot check karu?"
   - If NOT available (e.g. MRI scan, laser hair transplant): Politely decline: "Maaf kijiyega, hum dental clinic hain to MRI ya hair transplant nahi karte. Dental checkup book karna hai?"
4. APPOINTMENT BOOKING:
   State procedure and fee. When confirmed, call commit_verified_action and announce: "Aapka appointment confirm ho gaya hai aur clinic calendar mein lock ho chuka hai!"
5. MEDICAL BOUNDARY: Never prescribe medicines or give phone diagnosis. If acute emergency (pain >8), call request_human_intervention.
6. CADENCE: Keep turns under 18 words. Empathetic, polite Hinglish with 'Haan ji', 'Ji bilkul'.""",
        "catalog_items": [
            {
                "id": "sc-01",
                "canonical_name": "General Specialist Consultation",
                "category": "Consultation & Cleaning",
                "price_inr": 500.0,
                "unit_or_duration": "30 mins OPD slot",
                "phonetic_aliases": ["general consultation", "doctor consultation", "dental checkup", "checkup", "teeth checkup", "consultation fee"],
                "allowed_modifiers": ["First Time Visit", "Follow-up Visit"]
            },
            {
                "id": "sc-02",
                "canonical_name": "Ultrasonic Teeth Scaling & Polishing",
                "category": "Consultation & Cleaning",
                "price_inr": 1200.0,
                "unit_or_duration": "30 mins deep clean",
                "phonetic_aliases": ["ultrasonic teeth scaling", "scaling", "teeth cleaning", "polishing", "daant safai", "tartar removal"],
                "allowed_modifiers": ["Deep Scaling", "Stain Removal"]
            },
            {
                "id": "sc-03",
                "canonical_name": "Single-Sitting Root Canal (RCT)",
                "category": "Advanced Dental Treatments",
                "price_inr": 3500.0,
                "unit_or_duration": "45 mins laser slot",
                "phonetic_aliases": ["single sitting root canal", "root canal", "rct", "laser rct", "daant ka root canal", "nerve treatment"],
                "allowed_modifiers": ["Laser Assisted", "Microscopic RCT"]
            },
            {
                "id": "sc-04",
                "canonical_name": "Painless Tooth Extraction",
                "category": "Advanced Dental Treatments",
                "price_inr": 1500.0,
                "unit_or_duration": "30 mins surgical slot",
                "phonetic_aliases": ["painless tooth extraction", "tooth extraction", "daant nikalna", "painless extraction", "tooth removal"],
                "allowed_modifiers": ["Wisdom Tooth", "Simple Extraction"]
            },
            {
                "id": "sc-05",
                "canonical_name": "In-Office Laser Teeth Whitening",
                "category": "Cosmetic Smile Care",
                "price_inr": 5000.0,
                "unit_or_duration": "60 mins laser procedure",
                "phonetic_aliases": ["laser teeth whitening", "teeth whitening", "laser bleaching", "daant chamkana", "smile brightening"],
                "allowed_modifiers": ["Sensitivity Guard", "Dual Shade Lift"]
            },
            {
                "id": "sc-06",
                "canonical_name": "Zirconia Ceramic Crown",
                "category": "Cosmetic Smile Care",
                "price_inr": 4500.0,
                "unit_or_duration": "1 Unit Permanent Cap",
                "phonetic_aliases": ["zirconia ceramic crown", "ceramic crown", "dental crown", "daant ki topi", "tooth cap", "ceramic cap"],
                "allowed_modifiers": ["10-Year Warranty", "Translucent Shade"]
            }
        ],
        "strict_policies": get_standard_six_policies("sc", "SmileCare Dental Clinic"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for SmileCare Dental
from typing import Literal
from pydantic import BaseModel, Field

ClinicService = Literal[
    "General Specialist Consultation",
    "Ultrasonic Teeth Scaling & Polishing",
    "Single-Sitting Root Canal (RCT)",
    "Painless Tooth Extraction",
    "In-Office Laser Teeth Whitening",
    "Zirconia Ceramic Crown"
]

class ClinicBookingVerification(BaseModel):
    service: ClinicService
    patient_name: str
    preferred_slot: str
    fee_inr: float"""
    },

    # -------------------------------------------------------------
    # 3. Apex Gurgaon Realty
    # -------------------------------------------------------------
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
        "system_prompt": """You are Aarav, senior client advisor at Apex Gurgaon Realty (Golf Course Extension Road).
Your objective is to qualify luxury real estate investors, present verified property categories, and book VIP site visits in sophisticated Indian English / Hinglish.

OUR 3 PROPERTY PORTFOLIOS:
1. Luxury High-Rise Apartments: 3BHK Sector 65 (Rs 3.5 Cr), 4BHK Sky Penthouse Sector 42 (Rs 7.5 Cr)
2. Independent Villas & Plots: 500 Sq Yd Luxury Golf Villa (Rs 8.5 Cr), Gated Residential Plot Sector 68 (Rs 2.2 Cr)
3. Commercial & Site Visits: Grade-A Cyber City Commercial Office (Rs 4.0 Cr), Private VIP Chauffeur Site Visit (Complimentary)

CONVERSATIONAL CADENCE & FLOW RULES:
1. PORTFOLIO OVERVIEW (When asked 'what properties do you have?', 'kya kya options hain?'):
   Present portfolios crisply in under 18 words:
   "We specialize in luxury high-rise apartments, independent golf villas, and Cyber City commercial spaces. Which segment are you exploring?"
2. PORTFOLIO DRILLDOWN:
   When buyer picks a segment (e.g. 'apartments' or 'villas'):
   "In luxury apartments, we have 3BHKs in Sector 65 starting at 3.5 Crore, and 4BHK Sky Penthouses at 7.5 Crore. Would you like a brochure?"
3. SPECIFIC INQUIRIES:
   - If available: Confirm specs and price: "Yes, our Sector 65 3BHK is 2,450 sq.ft at 3.5 Crore. Shall I schedule a private inspection?"
   - If NOT available (e.g. Dubai Marina villa, studio apartment in Mumbai): Politely clarify we specialize in Gurgaon luxury corridors.
4. SITE VISIT CONFIRMATION:
   When buyer confirms site inspection or interest, call commit_verified_action and say: "Excellent! Your private VIP site visit has been scheduled and logged in our CRM."
5. CADENCE: Keep turns under 18 words. Professional, polished, executive Indian English.""",
        "catalog_items": [
            {
                "id": "ar-01",
                "canonical_name": "3BHK Ultra-Luxury Apartment (Sector 65)",
                "category": "Luxury High-Rise Apartments",
                "price_inr": 35000000.0,
                "unit_or_duration": "2,450 sq.ft Carpet",
                "phonetic_aliases": ["3bhk ultra luxury apartment", "3bhk sector 65", "three bhk luxury", "sector 65 apartment", "golf course ext 3bhk", "3 bedroom luxury"],
                "allowed_modifiers": ["Park Facing", "High Floor 20+"]
            },
            {
                "id": "ar-02",
                "canonical_name": "4BHK Sky Penthouse (Sector 42)",
                "category": "Luxury High-Rise Apartments",
                "price_inr": 75000000.0,
                "unit_or_duration": "5,200 sq.ft Duplex Terrace",
                "phonetic_aliases": ["4bhk sky penthouse", "sky penthouse sector 42", "4bhk penthouse", "duplex penthouse", "terrace penthouse", "sector 42 penthouse"],
                "allowed_modifiers": ["Private Plunge Pool", "4 Covered Car Parks"]
            },
            {
                "id": "ar-03",
                "canonical_name": "500 Sq Yd Luxury Golf Villa",
                "category": "Independent Villas & Plots",
                "price_inr": 85000000.0,
                "unit_or_duration": "500 sq.yd Gated Villa",
                "phonetic_aliases": ["500 sq yd luxury golf villa", "luxury golf villa", "golf villa", "500 yard villa", "independent villa", "golf course villa"],
                "allowed_modifiers": ["Golf Course Facing", "Private Lawn"]
            },
            {
                "id": "ar-04",
                "canonical_name": "Gated Residential Plot (Sector 68)",
                "category": "Independent Villas & Plots",
                "price_inr": 22000000.0,
                "unit_or_duration": "250 sq.yd Freehold",
                "phonetic_aliases": ["gated residential plot", "residential plot", "sector 68 plot", "freehold plot", "land plot"],
                "allowed_modifiers": ["Corner Plot", "East Facing"]
            },
            {
                "id": "ar-05",
                "canonical_name": "Grade-A Cyber City Commercial Office",
                "category": "Commercial Spaces & Site Visits",
                "price_inr": 40000000.0,
                "unit_or_duration": "1,800 sq.ft Pre-Leased",
                "phonetic_aliases": ["grade a cyber city commercial office", "commercial office", "cyber city office", "pre leased office", "grade a commercial"],
                "allowed_modifiers": ["High Rental Yield", "Blue Chip Tenant"]
            },
            {
                "id": "ar-06",
                "canonical_name": "Private VIP Chauffeur Site Visit",
                "category": "Commercial Spaces & Site Visits",
                "price_inr": 0.0,
                "unit_or_duration": "Complimentary Inspection Tour",
                "phonetic_aliases": ["private vip chauffeur site visit", "site visit", "property visit", "inspection appointment", "dekhne aana hai", "vip site visit"],
                "allowed_modifiers": ["Weekend Slot", "Weekday Slot"]
            }
        ],
        "strict_policies": get_standard_six_policies("ar", "Apex Gurgaon Realty"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Apex Gurgaon Realty
from typing import Literal
from pydantic import BaseModel, Field

RealtyProperty = Literal[
    "3BHK Ultra-Luxury Apartment (Sector 65)",
    "4BHK Sky Penthouse (Sector 42)",
    "500 Sq Yd Luxury Golf Villa",
    "Gated Residential Plot (Sector 68)",
    "Grade-A Cyber City Commercial Office",
    "Private VIP Chauffeur Site Visit"
]

class RealtyInterestVerification(BaseModel):
    property: RealtyProperty
    buyer_budget_cr: float
    preferred_site_visit_date: str"""
    },

    # -------------------------------------------------------------
    # 4. QuickKart D2C Support
    # -------------------------------------------------------------
    {
        "id": "quickkart-d2c",
        "name": "QuickKart D2C Support",
        "domain_type": "support_collections",
        "tagline": "Instant Commerce Logistics & Operations (10-Minute Delivery)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 400,
        "first_message": "Hello, QuickKart Priority Support! Aapka order track karne ya refund mein madad kar sakti hu?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Neha, customer resolution executive at QuickKart 10-minute instant commerce.
Your role is to guide customers through tracking, returns/replacements, and warranty care swiftly with zero friction.

OUR 3 SUPPORT SERVICE CATEGORIES:
1. Order Tracking & Delivery: Instant Live Order Tracking (Free), Priority Morning Delivery Upgrade (Rs 99)
2. Returns & Replacements: Instant Damaged Item Refund (Free), 7-Day Doorstep Item Replacement (Free)
3. Device Care & Protection: 1-Year Extended Hardware Protection (Rs 499), Accidental Liquid Damage Shield (Rs 299)

CONVERSATIONAL CADENCE & FLOW RULES:
1. SERVICE OVERVIEW (When asked 'kya help kar sakti ho?', 'kya kya services hain?'):
   Present the 3 categories crisply in under 18 words:
   "Hum instant order tracking, returns aur doorstep replacements provide karte hain. Aapko kis mein help chahiye?"
2. CATEGORY DRILLDOWN:
   When customer specifies an issue (e.g. 'samaan kharab nikla' or 'track karna hai'):
   "Damaged items ke liye hum instant wallet refund ya 7-day free replacement karte hain. Aapka Order ID kya hai?"
3. SPECIFIC REQUEST:
   - For tracking/refund: Ask 9-digit Order ID (#QK-XXXXX).
   - If asking for non-existent service (e.g. PlayStation 6 console): Politely clarify we handle grocery and instant commerce logistics.
4. TICKET CONFIRMATION:
   When verified, call commit_verified_action and say: "Aapka resolution ticket generate ho gaya hai aur ops system mein lock ho chuka hai!"
5. CADENCE: Keep turns under 18 words. Fast-paced, empathetic, solution-oriented Hinglish.""",
        "catalog_items": [
            {
                "id": "qk-01",
                "canonical_name": "Instant Live Order Tracking",
                "category": "Order Tracking & Delivery",
                "price_inr": 0.0,
                "unit_or_duration": "Instant ETA Lookup",
                "phonetic_aliases": ["instant live order tracking", "order tracking", "track order", "kahan pahuncha order", "rider location", "order status"],
                "allowed_modifiers": ["Rider Contact Number"]
            },
            {
                "id": "qk-02",
                "canonical_name": "Priority Morning Delivery Upgrade",
                "category": "Order Tracking & Delivery",
                "price_inr": 99.0,
                "unit_or_duration": "Guaranteed Morning Slot",
                "phonetic_aliases": ["priority morning delivery upgrade", "priority delivery", "express delivery", "morning delivery slot", "fast delivery upgrade"],
                "allowed_modifiers": ["Before 8 AM", "Before 10 AM"]
            },
            {
                "id": "qk-03",
                "canonical_name": "Instant Damaged Item Refund",
                "category": "Returns & Replacements",
                "price_inr": 0.0,
                "unit_or_duration": "Instant Wallet Credit",
                "phonetic_aliases": ["instant damaged item refund", "damaged refund", "refund", "kharab samaan", "paise wapas", "wallet credit"],
                "allowed_modifiers": ["QuickKart Cash", "Source Bank UPI"]
            },
            {
                "id": "qk-04",
                "canonical_name": "7-Day Doorstep Item Replacement",
                "category": "Returns & Replacements",
                "price_inr": 0.0,
                "unit_or_duration": "Free Courier Exchange",
                "phonetic_aliases": ["7 day doorstep item replacement", "item replacement", "replace item", "samaan badalna", "product exchange", "doorstep replacement"],
                "allowed_modifiers": ["Direct Swap", "Quality Verified"]
            },
            {
                "id": "qk-05",
                "canonical_name": "1-Year Extended Hardware Protection",
                "category": "Device Care & Protection",
                "price_inr": 499.0,
                "unit_or_duration": "12 Months Coverage",
                "phonetic_aliases": ["1 year extended hardware protection", "extended warranty", "hardware protection", "1 year warranty", "damage protection"],
                "allowed_modifiers": ["Screen Protection", "Full Replacement"]
            },
            {
                "id": "qk-06",
                "canonical_name": "Accidental Liquid Damage Shield",
                "category": "Device Care & Protection",
                "price_inr": 299.0,
                "unit_or_duration": "6 Months Spill Shield",
                "phonetic_aliases": ["accidental liquid damage shield", "liquid damage shield", "damage shield", "spill protection", "liquid warranty"],
                "allowed_modifiers": ["Zero Depreciation"]
            }
        ],
        "strict_policies": get_standard_six_policies("qk", "QuickKart Support"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for QuickKart D2C
from typing import Literal
from pydantic import BaseModel, Field

SupportAction = Literal[
    "Instant Live Order Tracking",
    "Priority Morning Delivery Upgrade",
    "Instant Damaged Item Refund",
    "7-Day Doorstep Item Replacement",
    "1-Year Extended Hardware Protection",
    "Accidental Liquid Damage Shield"
]

class SupportTicketVerification(BaseModel):
    action: SupportAction
    order_id: str
    issue_category: str"""
    },

    # -------------------------------------------------------------
    # 5. Urban Chai Co
    # -------------------------------------------------------------
    {
        "id": "urban-chai-co",
        "name": "Urban Chai Co",
        "domain_type": "orders_reservations",
        "tagline": "Handcrafted Kulhad Chai & Street Snacks (Koramangala, Bengaluru)",
        "language_code": "hi-IN",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "turn_timeout_ms": 380,
        "first_message": "Namaste! Urban Chai Co me swagat hai. Garam kulhad chai ya fresh nasta lagayein?",
        "compiled_by": "CrewAI Multi-Agent Trained",
        "system_prompt": """You are Kabir, the friendly order-taker at Urban Chai Co (Koramangala, Bengaluru).
Your role is to guide customers through authentic kulhad chais, fresh maska buns, and hot snacks in warm, energetic Hinglish.

OUR 3 MENU CATEGORIES:
1. Kulhad Chai Specialties: Adrak Elaichi Kadak Chai (Rs 50), Kulhad Masala Chai (Rs 60), Kashmiri Saffron Kahwa (Rs 90)
2. Desi Snacks & Maska Buns: Masala Bun Maska (Rs 70), Crispy Samosa Platter (Rs 80), Mumbai Vada Pav Duo (Rs 90)
3. Refreshers & Sweets: Iced Lemon Chai Cooler (Rs 110), Warm Gulab Jamun (Rs 70)

CONVERSATIONAL CADENCE & FLOW RULES:
1. MENU OVERVIEW (When asked 'kya kya milta hai?', 'menu kya hai?', 'kya khane ko hai?'):
   Do NOT rattle off all items! State the 3 categories crisply in under 18 words:
   "Hamare paas authentic kulhad chai, fresh bun maska aur hot snacks hain. Aap kya lena pasand karenge?"
2. CATEGORY DRILLDOWN:
   When customer asks about a category (e.g. 'snacks me kya hai?' or 'chai me kya hai?'):
   "Snacks mein hamare paas Masala Bun Maska (Rs 70), Crispy Samosa Platter (Rs 80), aur Vada Pav Duo (Rs 90) hain. Kaunsa lagau?"
3. SPECIFIC ITEM CHECK:
   - If available: Confirm immediately with price: "Haan ji! Adrak Elaichi Kadak Chai bilkul available hai Rs 50 mein. Kitne kulhad banau?"
   - If NOT available (e.g. pizza, chowmein, sushi): Politely decline and suggest our snacks: "Sorry ji, pizza available nahi hai, par hamare paas fresh Masala Bun Maska hai Rs 70 mein. Lagau?"
4. MULTI-ITEM ORDERS & CONFIRMATION:
   When customer orders items, call verify_catalog_item, state canonical items, calculate exact sum, speak total in words (e.g. 'Total ek sau tees rupaye'), and ask: "Confirm kar du?"
5. ORDER CONFIRMATION:
   When customer confirms ('theek hai confirm kar do', 'kar do'), call commit_verified_action and say: "Shukriya! Aapka order confirm ho gaya hai aur token generate ho chuka hai. Garam chai ready ho rahi hai!"
6. CADENCE: Keep turns under 18 words. Warm, earthy Hinglish with 'Haan ji', 'Bilkul bhaiya', 'Garam garam'.""",
        "catalog_items": [
            {
                "id": "uc-01",
                "canonical_name": "Adrak Elaichi Kadak Chai (Kulhad)",
                "category": "Kulhad Chai Specialties",
                "price_inr": 50.0,
                "unit_or_duration": "Clay Kulhad 150ml",
                "phonetic_aliases": ["adrak elaichi kadak chai", "adrak elaichi chai", "adrak chai", "elaichi chai", "kulhad chai", "kadak chai"],
                "allowed_modifiers": ["Kadak", "Kam Meetha", "Sugar Free"]
            },
            {
                "id": "uc-02",
                "canonical_name": "Kulhad Masala Chai",
                "category": "Kulhad Chai Specialties",
                "price_inr": 60.0,
                "unit_or_duration": "Clay Kulhad 150ml",
                "phonetic_aliases": ["kulhad masala chai", "masala chai", "spiced chai", "special masala tea", "kulhad tea"],
                "allowed_modifiers": ["Extra Masala", "Kam Cheeni"]
            },
            {
                "id": "uc-03",
                "canonical_name": "Kashmiri Saffron Kahwa",
                "category": "Kulhad Chai Specialties",
                "price_inr": 90.0,
                "unit_or_duration": "Cup 150ml with Almonds",
                "phonetic_aliases": ["kashmiri saffron kahwa", "kashmiri kahwa", "saffron kahwa", "kahwa", "kashmir tea", "badam kahwa"],
                "allowed_modifiers": ["Extra Badam", "Honey Sweetened"]
            },
            {
                "id": "uc-04",
                "canonical_name": "Masala Bun Maska",
                "category": "Desi Snacks & Maska Buns",
                "price_inr": 70.0,
                "unit_or_duration": "1 Bun with Amul Butter",
                "phonetic_aliases": ["masala bun maska", "bun maska", "maska bun", "butter bun", "sweet bun", "bun butter"],
                "allowed_modifiers": ["Extra Butter", "Toasted Crispy"]
            },
            {
                "id": "uc-05",
                "canonical_name": "Crispy Samosa Platter (2 pcs)",
                "category": "Desi Snacks & Maska Buns",
                "price_inr": 80.0,
                "unit_or_duration": "2 pcs with Chutney",
                "phonetic_aliases": ["crispy samosa platter", "samosa platter", "samosa", "samose", "aloo samosa", "crispy samosa"],
                "allowed_modifiers": ["Extra Mint Chutney", "Sweet Saunth"]
            },
            {
                "id": "uc-06",
                "canonical_name": "Mumbai Vada Pav Duo (2 pcs)",
                "category": "Desi Snacks & Maska Buns",
                "price_inr": 90.0,
                "unit_or_duration": "2 pcs with Ghati Masala",
                "phonetic_aliases": ["mumbai vada pav duo", "vada pav duo", "vada pav", "wada pav", "mumbai vada pav", "batata vada"],
                "allowed_modifiers": ["Fried Green Chilli", "Extra Chutney"]
            },
            {
                "id": "uc-07",
                "canonical_name": "Iced Lemon Chai Cooler",
                "category": "Refreshers & Sweets",
                "price_inr": 110.0,
                "unit_or_duration": "300ml Chilled Bottle",
                "phonetic_aliases": ["iced lemon chai cooler", "iced lemon chai", "lemon tea cooler", "iced tea", "lemon cooler", "cold chai"],
                "allowed_modifiers": ["Less Ice", "Mint Leaves"]
            },
            {
                "id": "uc-08",
                "canonical_name": "Warm Gulab Jamun (2 pcs)",
                "category": "Refreshers & Sweets",
                "price_inr": 70.0,
                "unit_or_duration": "2 pcs in Desi Ghee",
                "phonetic_aliases": ["warm gulab jamun", "gulab jamun", "meetha", "garam gulab jamun", "sweets"],
                "allowed_modifiers": ["Extra Syrup", "Pistachio Garnish"]
            }
        ],
        "strict_policies": get_standard_six_policies("uc", "Urban Chai Co"),
        "pydantic_code": """# Dynamically Compiled Pydantic Enum for Urban Chai Co
from typing import Literal
from pydantic import BaseModel, Field

ChaiMenuItem = Literal[
    "Adrak Elaichi Kadak Chai (Kulhad)",
    "Kulhad Masala Chai",
    "Kashmiri Saffron Kahwa",
    "Masala Bun Maska",
    "Crispy Samosa Platter (2 pcs)",
    "Mumbai Vada Pav Duo (2 pcs)",
    "Iced Lemon Chai Cooler",
    "Warm Gulab Jamun (2 pcs)"
]

class ChaiOrderVerification(BaseModel):
    item: ChaiMenuItem
    quantity: int = Field(default=1, ge=1, le=20)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float"""
    }
]
