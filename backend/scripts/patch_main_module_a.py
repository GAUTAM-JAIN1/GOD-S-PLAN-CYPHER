with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update list_domains
old_list = """            strict_policies=strict_policies,
            elevenlabs_agent_id=p.elevenlabs_agent_id,
            created_at=str(p.created_at),
            updated_at=str(p.updated_at)
        ))
    return response"""

new_list = """            strict_policies=strict_policies,
            elevenlabs_agent_id=p.elevenlabs_agent_id,
            compiled_by=getattr(p, "compiled_by", "CrewAI Multi-Agent Trained") or "CrewAI Multi-Agent Trained",
            crew_execution_log_json=getattr(p, "crew_execution_log_json", "[]") or "[]",
            created_at=str(p.created_at),
            updated_at=str(p.updated_at)
        ))
    return response"""

assert old_list in content, "old_list not found"
content = content.replace(old_list, new_list, 1)

# 2. Update get_domain
old_get = """        strict_policies=strict_policies,
        elevenlabs_agent_id=p.elevenlabs_agent_id,
        created_at=str(p.created_at),
        updated_at=str(p.updated_at)
    )

# ----------------- DOMAIN DELETION & ENTITY EXTRACTION -----------------
@app.delete("/api/domains/{domain_id}")
async def delete_domain_endpoint(domain_id: str, session: AsyncSession = Depends(get_db_session)):
    \"\"\"Deletes domain profile and cascades cleans from ledger and holds.\"\"\"
    stmt = select(DomainProfileModel).where(DomainProfileModel.id == domain_id)"""

new_get = """        strict_policies=strict_policies,
        elevenlabs_agent_id=p.elevenlabs_agent_id,
        compiled_by=getattr(p, "compiled_by", "CrewAI Multi-Agent Trained") or "CrewAI Multi-Agent Trained",
        crew_execution_log_json=getattr(p, "crew_execution_log_json", "[]") or "[]",
        created_at=str(p.created_at),
        updated_at=str(p.updated_at)
    )

# ----------------- DOMAIN DELETION & ENTITY EXTRACTION -----------------
CORE_STARTER_DOMAINS = {"brew-bite-cafe", "smilecare-dental", "apex-gurgaon-realty", "quickkart-d2c", "quickkart-d2c-support", "urban-chai-co"}

@app.delete("/api/domains/{domain_id}")
async def delete_domain_endpoint(domain_id: str, session: AsyncSession = Depends(get_db_session)):
    \"\"\"Deletes domain profile and cascades cleans from ledger and holds.\"\"\"
    if domain_id in CORE_STARTER_DOMAINS:
        raise HTTPException(status_code=403, detail="Core starter domains are locked for evaluation and cannot be deleted.")

    stmt = select(DomainProfileModel).where(DomainProfileModel.id == domain_id)"""

assert old_get in content, "old_get not found"
content = content.replace(old_get, new_get, 1)

# 3. Update compile_domain
old_compile = """# ----------------- ARCHITECTURE COMPILATION -----------------
@app.post("/api/domains/compile", response_model=CompileDomainResponse)
async def compile_domain(req: CompileDomainRequest, session: AsyncSession = Depends(get_db_session)):
    # Clean business name if user passed raw sentence (Fixes Bug 5.1)
    clean_name = req.business_name
    if len(clean_name) > 28 or any(w in clean_name.lower() for w in ["mere", "naam", "hai", "ka naam", "hum"]):
        clean_name = await extract_clean_business_name(req.business_name)

    logger.info(f"Initiating architecture compilation for: {clean_name} ({req.domain_type})")
    
    compiled = await compile_domain_architecture(
        business_name=clean_name,
        domain_type=req.domain_type,
        owner_instructions=req.owner_instructions,
        parsed_catalog_text=req.parsed_catalog_text or ""
    )"""

new_compile = """# ----------------- ARCHITECTURE COMPILATION -----------------
@app.post("/api/domains/compile", response_model=CompileDomainResponse)
async def compile_domain(req: CompileDomainRequest, session: AsyncSession = Depends(get_db_session)):
    logger.info(f"Initiating CrewAI 3-Agent Architecture Compilation for: {req.business_name} ({req.domain_type})")
    
    from backend.services.crew_compiler import execute_crew_pipeline
    
    compiled = await execute_crew_pipeline(
        business_name=req.business_name,
        domain_type=req.domain_type,
        owner_instructions=req.owner_instructions,
        parsed_catalog_text=req.parsed_catalog_text or "",
        broadcast_func=ws_manager.broadcast
    )"""

assert old_compile in content, "old_compile not found"
content = content.replace(old_compile, new_compile, 1)

# 4. Update compile_domain persistence
old_persist = """    if existing:
        existing.name = clean_name
        existing.domain_type = req.domain_type
        existing.system_prompt = compiled.system_prompt
        existing.first_message = compiled.first_message
        existing.catalog_json = catalog_json
        existing.policies_json = policies_json
        existing.pydantic_code = compiled.pydantic_literal_code
    else:
        new_profile = DomainProfileModel(
            id=domain_id,
            name=clean_name,
            domain_type=req.domain_type,
            tagline=f"Custom AI Agent ({req.domain_type})",
            system_prompt=compiled.system_prompt,
            first_message=compiled.first_message,
            voice_id=req.voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID,
            language_code="hi-IN",
            turn_timeout_ms=420,
            catalog_json=catalog_json,
            policies_json=policies_json,
            pydantic_code=compiled.pydantic_literal_code
        )
        session.add(new_profile)"""

new_persist = """    clean_name = req.business_name
    # Extract clean business name from compiled pydantic or catalog if available
    if compiled.domain_id and compiled.domain_id != "custom-agent":
        clean_name = " ".join(w.capitalize() for w in compiled.domain_id.split("-"))

    exec_log_json = json.dumps(compiled.crew_execution_log or [])
    compiled_by_str = compiled.compiled_by or "CrewAI 3-Agent Pipeline (Llama-3.3-70B)"

    if existing:
        existing.name = clean_name
        existing.domain_type = req.domain_type
        existing.system_prompt = compiled.system_prompt
        existing.first_message = compiled.first_message
        existing.catalog_json = catalog_json
        existing.policies_json = policies_json
        existing.pydantic_code = compiled.pydantic_literal_code
        existing.compiled_by = compiled_by_str
        existing.crew_execution_log_json = exec_log_json
    else:
        new_profile = DomainProfileModel(
            id=domain_id,
            name=clean_name,
            domain_type=req.domain_type,
            tagline=f"Custom AI Agent ({req.domain_type})",
            system_prompt=compiled.system_prompt,
            first_message=compiled.first_message,
            voice_id=req.voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID,
            language_code="hi-IN",
            turn_timeout_ms=420,
            catalog_json=catalog_json,
            policies_json=policies_json,
            pydantic_code=compiled.pydantic_literal_code,
            compiled_by=compiled_by_str,
            crew_execution_log_json=exec_log_json
        )
        session.add(new_profile)"""

assert old_persist in content, "old_persist not found"
content = content.replace(old_persist, new_persist, 1)

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("backend/main.py successfully patched for Module A!")
