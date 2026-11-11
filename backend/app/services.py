import hashlib, secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from .models import Order, Operation, Recorder, Incident, BuyerToken, Outbox, now
from .truth import derive_truth

def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def record(db, order, kind, payload, source='payment_service'):
    event = Recorder(order_id=order.id, source=source, event_type=kind, payload=payload)
    db.add(event); db.flush(); return event

def incident(db, order):
    found = db.scalar(select(Incident).where(Incident.order_id == order.id))
    if not found:
        found = Incident(order_id=order.id); db.add(found); db.flush()
    return found

def enqueue(db, order): db.add(Outbox(order_id=order.id))

def restore_fake(db, order, client):
    if order.mode == 'simulated' and order.provider_id not in client.orders:
        events = db.scalars(select(Recorder).where(Recorder.order_id == order.id).order_by(Recorder.observed_at.desc())).all()
        for e in events:
            if e.event_type in ('provider.capture', 'provider.created'):
                client.orders[order.provider_id] = e.payload; return

def create_order(db, merchant, client, mode):
    order = Order(merchant_id=merchant.id, mode=mode); db.add(order); db.flush()
    op = Operation(order_id=order.id, kind='create'); db.add(op); db.flush()
    token = secrets.token_urlsafe(32)
    db.add(BuyerToken(token_hash=digest(token), order_id=order.id, expires_at=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()))
    record(db, order, 'intent.created', {'amount': order.amount, 'currency': order.currency, 'mode': mode})
    db.commit() # durable intent/idempotency key BEFORE provider request
    try:
        resource = client.create_order(op.request_key, order.id)
        order.provider_id = resource['id']; op.status = 'RESOLVED'
        record(db, order, 'provider.created', resource, mode); db.commit()
        return order, token, next((x['href'] for x in resource.get('links', []) if x['rel'] in ('approve','payer-action')), None)
    except Exception:
        order.state = 'UNKNOWN'; incident(db, order)
        record(db, order, 'create.uncertain', {'operation_id': op.id}); db.commit()
        raise HTTPException(502, 'Provider unavailable. Do not assume payment failed.')

def apply_resource(db, order, resource):
    if resource.get('id') != order.provider_id: raise ValueError('Provider resource does not match order')
    units = resource.get('purchase_units', [])
    if len(units) != 1 or units[0].get('reference_id') != order.id: raise ValueError('Provider reference mismatch')
    captures = units[0].get('payments', {}).get('captures', [])
    for c in captures:
        if c.get('amount', {}).get('value') != order.amount or c.get('amount', {}).get('currency_code') != order.currency:
            raise ValueError('Provider capture amount mismatch')
    order.state = derive_truth(resource, order.state); order.checked_at = now()
    for c in captures:
        if c.get('status') == 'COMPLETED': order.capture_id = c['id']
    if order.state in ('CONFIRMED','FAILED'):
        op = db.scalar(select(Operation).where(Operation.order_id == order.id, Operation.kind == 'capture'))
        if op: op.status = 'RESOLVED'

def capture(db, order, client, drop=False):
    if not order.provider_id: raise HTTPException(409, 'Order creation is unresolved')
    # Unique constraint wins across threads/processes; never issue another provider call.
    op = Operation(order_id=order.id, kind='capture'); db.add(op)
    try:
        db.flush()
        record(db, order, 'capture.requested', {'operation_id': op.id}); enqueue(db, order)
        db.commit()
    except IntegrityError:
        db.rollback(); db.refresh(order)
        return {'state': order.state, 'duplicate_blocked': True, 'capture_id': order.capture_id}
    try:
        restore_fake(db, order, client)
        resource = client.capture_order(order.provider_id, op.request_key)
        record(db, order, 'provider.capture', resource, order.mode)
        if drop:
            # A worker may have confirmed the order while the provider call was in flight.
            db.execute(update(Order).where(Order.id == order.id, Order.state != 'CONFIRMED')
                       .values(state='UNKNOWN'))
            incident(db, order)
            record(db, order, 'demo.response_dropped', {'simulated_fault': True})
            db.commit()
            raise HTTPException(504, 'Demo: capture response lost. Check private payment status; do not pay again.')
        apply_resource(db, order, resource); db.commit()
    except HTTPException: raise
    except Exception:
        if order.state != 'CONFIRMED': order.state = 'UNKNOWN'
        incident(db, order)
        record(db, order, 'capture.uncertain', {'operation_id': op.id}); db.commit()
    return {'state': order.state, 'duplicate_blocked': False, 'capture_id': order.capture_id}

def reconcile(db, order, client):
    try:
        restore_fake(db, order, client)
        resource = client.get_order(order.provider_id)
        apply_resource(db, order, resource)
        record(db, order, 'reconcile.resource', resource, order.mode)
        db.commit(); return order.state in ('CONFIRMED', 'FAILED')
    except Exception:
        if order.state != 'CONFIRMED': order.state = 'UNKNOWN'
        order.checked_at = now()
        record(db, order, 'reconcile.unavailable', {'next_step': 'Check provider again; do not retry payment'})
        db.commit(); return False

def accept_verified_webhook(db, event):
    """Called only after adapter verification, or from an isolated labeled replay."""
    from .models import Webhook
    if db.get(Webhook,event['id']): return {'duplicate':True}
    try:
        db.add(Webhook(id=event['id'],payload=event)); db.flush()
        resource=event.get('resource',{})
        pid=resource.get('supplementary_data',{}).get('related_ids',{}).get('order_id')
        if event.get('event_type','').startswith('CHECKOUT.ORDER.'):pid=resource.get('id')
        o=db.scalar(select(Order).where(Order.provider_id==pid))
        if o:record(db,o,'webhook.received',event,'verified_webhook' if o.mode=='sandbox' else 'simulated_webhook');enqueue(db,o)
        db.commit();return {'accepted':True}
    except IntegrityError:
        db.rollback();return {'duplicate':True}
