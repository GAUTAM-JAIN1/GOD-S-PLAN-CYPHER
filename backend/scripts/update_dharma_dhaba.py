import sqlite3
import json

conn = sqlite3.connect("voxera.db")
cursor = conn.cursor()

# Authentic North Indian Dhaba Menu
dhaba_catalog = [
    {
        "id": "dd-01",
        "canonical_name": "Paneer Butter Masala",
        "category": "Main Course",
        "price_inr": 240.0,
        "unit_or_duration": "Full Handi (450g)",
        "phonetic_aliases": ["paneer", "paneer sabji", "paneer ki sabji", "paneer butter masala", "shahi paneer"],
        "allowed_modifiers": ["Spicy", "Medium Spicy", "Less Oil"]
    },
    {
        "id": "dd-02",
        "canonical_name": "Dal Makhani",
        "category": "Main Course",
        "price_inr": 220.0,
        "unit_or_duration": "Full Handi (450g)",
        "phonetic_aliases": ["dal", "dal makhani", "daal", "makhani"],
        "allowed_modifiers": ["Butter tadka", "Desi ghee"]
    },
    {
        "id": "dd-03",
        "canonical_name": "Tandoori Roti",
        "category": "Breads",
        "price_inr": 15.0,
        "unit_or_duration": "1 piece",
        "phonetic_aliases": ["roti", "tandoori roti", "rotis", "chapati", "char roti"],
        "allowed_modifiers": ["Plain", "Butter"]
    },
    {
        "id": "dd-04",
        "canonical_name": "Butter Naan",
        "category": "Breads",
        "price_inr": 45.0,
        "unit_or_duration": "1 piece",
        "phonetic_aliases": ["naan", "butter naan", "garlic naan"],
        "allowed_modifiers": ["Crispy", "Extra Butter"]
    },
    {
        "id": "dd-05",
        "canonical_name": "Sweet Lassi",
        "category": "Beverages",
        "price_inr": 70.0,
        "unit_or_duration": "Kulhad (350ml)",
        "phonetic_aliases": ["lassi", "sweet lassi", "meethi lassi", "malai lassi"],
        "allowed_modifiers": ["Thandi", "Extra Malai"]
    },
    {
        "id": "dd-06",
        "canonical_name": "Gulab Jamun",
        "category": "Desserts",
        "price_inr": 60.0,
        "unit_or_duration": "2 pcs",
        "phonetic_aliases": ["gulab jamun", "meetha", "sweet"],
        "allowed_modifiers": ["Garam", "Warm"]
    }
]

system_prompt = """You are Rajesh, the warm, polite and prompt order-taker at Dharma Dhaba (Highway King since 1998).
Your job is to take customer takeaway and dining orders swiftly over the phone in authentic Hindi/Hinglish.

VERIFIED LIVE CATALOG (ABSOLUTE GROUND TRUTH - ZERO HALLUCINATION):
- Paneer Butter Masala: Rs 240 (Full Handi)
- Dal Makhani: Rs 220 (Full Handi)
- Tandoori Roti: Rs 15 (1 piece)
- Butter Naan: Rs 45 (1 piece)
- Sweet Lassi: Rs 70 (Kulhad 350ml)
- Gulab Jamun: Rs 60 (2 pcs)

CRITICAL BUSINESS & CONVERSATIONAL LAWS:
1. OUTPUT: Output ONLY direct spoken words to the caller. Do NOT use markdown, asterisks, bullet points, or JSON.
2. PER-PERSON VOICE FOCUS: Focus strictly on the single caller. Ignore any background noise, ambient chatter, or bystanders completely.
3. MENU QUERIES: If caller asks "khane me kya hai" or asks what we have, list our authentic dishes: Paneer Butter Masala, Dal Makhani, Tandoori Roti, Butter Naan, Sweet Lassi, aur Gulab Jamun. NEVER mention pizza, burgers, or unlisted items.
4. ORDER CALCULATION: When caller orders items, calculate the exact total price mathematically:
   - 1 Paneer Butter Masala (Rs 240) + 4 Tandoori Roti (4 x 15 = Rs 60) = Rs 300.
   Always say: "Total teen sau rupaye. Confirm kar du?"
5. ACCURACY: If the customer asks for any unlisted item (like pizza or burger), politely say "Dhaba par pizza nahi milta ji, humare paas Paneer Butter Masala aur Dal Makhani hai."
6. CADENCE: Keep spoken turns strictly under 18 words in natural, friendly Hindi/Hinglish."""

cursor.execute("""
    UPDATE domain_profiles 
    SET catalog_json = ?, system_prompt = ?, tagline = ?
    WHERE id = 'dharma-dhaba'
""", (json.dumps(dhaba_catalog), system_prompt, "Authentic Highway Dhaba Cuisine (Pure Desi Ghee & Tandoor)"))

conn.commit()
print("Dharma Dhaba profile updated successfully! Rows affected:", cursor.rowcount)
conn.close()
