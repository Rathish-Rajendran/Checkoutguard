from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return uuid.uuid4().hex
def now(): return datetime.now(timezone.utc).isoformat()
class Merchant(Base):
    __tablename__ = 'merchants'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str]
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey('merchants.id'))
    provider_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    state: Mapped[str] = mapped_column(default='PENDING')
    amount: Mapped[str] = mapped_column(default='49.00')
    currency: Mapped[str] = mapped_column(default='USD')
    mode: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)
    checked_at: Mapped[str] = mapped_column(default=now)
    capture_id: Mapped[str | None]
class Operation(Base):
    __tablename__ = 'payment_operations'
    __table_args__ = (UniqueConstraint('order_id', 'kind'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'))
    kind: Mapped[str]
    status: Mapped[str] = mapped_column(default='IN_FLIGHT')
    request_key: Mapped[str] = mapped_column(default=uid, unique=True)
class BuyerToken(Base):
    __tablename__ = 'buyer_status_tokens'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'))
    expires_at: Mapped[str]
    revoked: Mapped[bool] = mapped_column(default=False)
class Recorder(Base):
    __tablename__ = 'flight_recorder_events'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: 'evt_'+uid())
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'))
    source: Mapped[str]
    event_type: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    occurred_at: Mapped[str] = mapped_column(default=now)
    observed_at: Mapped[str] = mapped_column(default=now)
class Webhook(Base):
    __tablename__ = 'webhook_events'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    received_at: Mapped[str] = mapped_column(default=now)
class Outbox(Base):
    __tablename__ = 'outbox'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'))
    status: Mapped[str] = mapped_column(default='PENDING')
    attempts: Mapped[int] = mapped_column(default=0)
    available_at: Mapped[str] = mapped_column(default=now)
class Incident(Base):
    __tablename__ = 'incidents'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'), unique=True)
    title: Mapped[str] = mapped_column(default='Checkout needs verification')
    severity: Mapped[str] = mapped_column(default='medium')
    created_at: Mapped[str] = mapped_column(default=now)
class Investigation(Base):
    __tablename__ = 'investigations'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    report: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
class ReplayRun(Base):
    __tablename__ = 'replay_runs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey('merchants.id'))
    scenario: Mapped[str]
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
class Audit(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    merchant_id: Mapped[str | None]
    action: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)

# The application recorder is append-only, including ORM bulk writes.
from sqlalchemy import event
from sqlalchemy.orm import Session
@event.listens_for(Session, 'before_flush')
def immutable_events(db, *_):
    if any(isinstance(obj, Recorder) for obj in list(db.dirty) + list(db.deleted)):
        raise ValueError('Flight Recorder events are append-only')
