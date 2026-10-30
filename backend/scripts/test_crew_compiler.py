import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from backend.services.crew_compiler import execute_crew_pipeline

async def test_crew():
    res = await execute_crew_pipeline(
        business_name="arre bhai mere naye restaurant ka naam Royal Punjab Tadka hai hum dal makhani 280 rupaye aur butter naan 60 rupaye me dete hai",
        domain_type="restaurant",
        owner_instructions="Pure vegetarian punjabi dhaba cuisine with quick parcel service"
    )
    print("SUCCESS:", res.success)
    print("DOMAIN ID:", res.domain_id)
    print("COMPILED BY:", res.compiled_by)
    print("CATALOG ITEMS COUNT:", len(res.catalog_items))
    for it in res.catalog_items:
        print(f" - {it.canonical_name}: Rs {it.price_inr} | Aliases ({len(it.phonetic_aliases)}): {it.phonetic_aliases}")
    print("STRICT POLICIES COUNT:", len(res.strict_policies))
    for pol in res.strict_policies:
        print(f" - [{pol.id}] ({pol.enforcement_action}): {pol.rule}")
    print("CREW EXECUTION LOG:")
    for log in res.crew_execution_log:
        print(" *", log)

asyncio.run(test_crew())

