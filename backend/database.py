import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from sqlalchemy import String, Text, DateTime, Integer, Float, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"timeout": 30.0}
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enforce SQLite WAL mode and busy timeout to completely prevent 'database is locked' errors
    under high-concurrency voice streaming turns.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.close()

class Base(DeclarativeBase):
    pass

class DomainProfileModel(Base):
    __tablename__ = "domain_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    domain_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tagline: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    first_message: Mapped[str] = mapped_column(String(256), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(64), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), default="hi-IN")
    turn_timeout_ms: Mapped[int] = mapped_column(Integer, default=420)
    elevenlabs_agent_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Serialized JSON structures
    catalog_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    policies_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    pydantic_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    compiled_by: Mapped[Optional[str]] = mapped_column(String(128), default="CrewAI Multi-Agent Trained")
    crew_execution_log_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="[]")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PendingVerificationModel(Base):
    __tablename__ = "pending_verifications"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_price_inr: Mapped[float] = mapped_column(Float, default=0.0)
    phonetic_score: Mapped[float] = mapped_column(Float, default=1.0)
    caller_phone: Mapped[str] = mapped_column(String(32), default="+91 98712 00000")
    status: Mapped[str] = mapped_column(String(32), default="VERIFIED_AWAITING_READBACK") # VERIFIED_AWAITING_READBACK, COMMITTED, EXPIRED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    domain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    caller_phone: Mapped[str] = mapped_column(String(32), default="+91 98712 XXXXX")
    caller_language: Mapped[str] = mapped_column(String(32), default="Hinglish")
    verified_order_summary: Mapped[str] = mapped_column(String(256), nullable=False)
    total_amount_inr: Mapped[float] = mapped_column(Float, default=0.0)
    phonetic_score: Mapped[float] = mapped_column(Float, default=1.0)
    resolution_badge: Mapped[str] = mapped_column(String(64), default="LOCKED IN POS") # LOCKED IN POS, CALENDAR SYNCED, ASSISTED HOLD, RESOLVED
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    timestamp: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now(timezone.utc).strftime("%H:%M:%S"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class InterceptHoldModel(Base):
    __tablename__ = "intercept_holds"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    domain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    spoken_entity: Mapped[str] = mapped_column(String(128), nullable=False)
    caller_utterance: Mapped[str] = mapped_column(Text, default="")
    phonetic_score: Mapped[float] = mapped_column(Float, default=0.0)
    candidate_1_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    candidate_2_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    hold_reason: Mapped[str] = mapped_column(String(64), default="LOW_CONFIDENCE_AUDIO") # LOW_CONFIDENCE_AUDIO, HUMAN_TRANSFER_REQUEST
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE_HOLD") # ACTIVE_HOLD, RESOLVED_CANDIDATE_1, RESOLVED_CANDIDATE_2, TRANSFERRED, TIMED_OUT
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class GauntletRunModel(Base):
    __tablename__ = "gauntlet_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scenarios_passed: Mapped[int] = mapped_column(Integer, default=3)
    auto_healed_count: Mapped[int] = mapped_column(Integer, default=1)
    mean_latency_ms: Mapped[int] = mapped_column(Integer, default=320)
    scenarios_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

async def init_db():
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA busy_timeout=30000;"))
        await conn.run_sync(Base.metadata.create_all)
        
        # Ensure migration columns exist in domain_profiles
        try:
            await conn.execute(text("ALTER TABLE domain_profiles ADD COLUMN compiled_by VARCHAR(128) DEFAULT 'CrewAI Multi-Agent Trained';"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE domain_profiles ADD COLUMN crew_execution_log_json TEXT DEFAULT '[]';"))
        except Exception:
            pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
