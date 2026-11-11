from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .db import Base
from .models import Merchant, Recorder, Webhook
from .paypal import FakePayPalClient
from .services import create_order, capture, reconcile, digest

SCENARIOS = {
    'response-lost': 'Capture succeeds, browser response is lost, lookup confirms one capture.',
    'repeated-capture': 'Repeated capture requests are blocked by a durable operation key.',
    'out-of-order': 'Duplicate and stale notifications cannot regress a completed payment.',
    'unresolved': 'Provider remains unavailable; payment stays uncertain and retries are blocked.'
}
def run_scenario(scenario):
    if scenario not in SCENARIOS: raise HTTPException(422, 'Choose a predefined scenario')
    # Isolated database and brand-new adapter: never reads environment credentials.
    engine = create_engine('sqlite:///:memory:'); Base.metadata.create_all(engine)
    client = FakePayPalClient()
    with Session(engine, expire_on_commit=False) as db:
        m=Merchant(id='replay',name='Isolated simulator',key_hash=digest('replay')); db.add(m); db.commit()
        order, _, _ = create_order(db,m,client,'simulated')
        client.unresolved = scenario=='unresolved'
        try: capture(db,order,client,drop=scenario=='response-lost')
        except HTTPException as e:
            if e.status_code != 504: raise
        first = order.state
        reconcile(db,order,client)
        duplicate = capture(db,order,client)
        webhook_duplicate = None
        if scenario in ('response-lost','out-of-order'):
            from .services import accept_verified_webhook
            event={'id':'SIM-WH-1','event_type':'PAYMENT.CAPTURE.COMPLETED','resource':{'supplementary_data':{'related_ids':{'order_id':order.provider_id}}}}
            accept_verified_webhook(db,event)
            webhook_duplicate=accept_verified_webhook(db,event)['duplicate']
            reconcile(db,order,client)
        if scenario=='out-of-order':
            # Deliver stale resources after completion through the same truth transition function.
            from .services import apply_resource, record
            stale={'id':order.provider_id,'purchase_units':[{'reference_id':order.id}], 'status':'APPROVED'}
            for _ in range(2):
                apply_resource(db,order,stale); record(db,order,'simulated.stale_notification',stale,'simulator')
            db.commit()
        assertions=[{'name':'At most one provider capture','expected':1 if scenario!='unresolved' else 0,'actual':client.capture_count}, {'name':'Duplicate attempt blocked','expected':True,'actual':duplicate['duplicate_blocked']}, {'name':'Truth matches evidence','expected':'UNKNOWN' if scenario=='unresolved' else 'CONFIRMED','actual':order.state}]
        if scenario=='response-lost': assertions.append({'name':'Lost response preserves uncertainty','expected':'UNKNOWN','actual':first})
        if webhook_duplicate is not None: assertions.append({'name':'Duplicate webhook has no second business effect','expected':True,'actual':webhook_duplicate})
        for a in assertions: a['passed']=a['expected']==a['actual']
        trace=[{'id':e.id,'event_type':e.event_type,'payload':e.payload,'observed_at':e.observed_at} for e in db.scalars(select(Recorder).order_by(Recorder.observed_at))]
        result={'mode':'SIMULATED','passed':all(a['passed'] for a in assertions),'assertions':assertions,'trace':trace}
    engine.dispose(); return result
