import json, logging, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from .config import settings
from .db import get_db
from .models import Merchant, Order, BuyerToken, Incident, Recorder, Webhook, Investigation, ReplayRun, Audit
from .paypal import get_client
from .services import digest, create_order, capture, reconcile, record, enqueue
from .investigator import investigate
from .replay import SCENARIOS, run_scenario
app=FastAPI(title='CheckoutGuard',version='1.0.0')
logging.basicConfig(level=logging.INFO)
@app.middleware('http')
async def correlation(request:Request,call_next):
    cid=uuid.uuid4().hex; response=await call_next(request); response.headers['X-Correlation-ID']=cid
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
        response.headers['Referrer-Policy']='no-referrer'
    logging.info(json.dumps({'correlation_id':cid,'method':request.method,'status':response.status_code})); return response

def merchant(x_api_key:str=Header(default=''),db=Depends(get_db)):
    m=db.scalar(select(Merchant).where(Merchant.key_hash==digest(x_api_key)))
    if not m: raise HTTPException(401,'Merchant API key required')
    return m
def scoped_order(db,m,oid):
    o=db.scalar(select(Order).where(Order.id==oid,Order.merchant_id==m.id))
    if not o: raise HTTPException(404,'Order not found')
    return o
def scoped_incident(db,m,iid):
    i=db.get(Incident,iid)
    if not i: raise HTTPException(404,'Incident not found')
    return i,scoped_order(db,m,i.order_id)
def serialize_order(o):return {k:getattr(o,k) for k in ('id','state','amount','currency','mode','checked_at','capture_id')}
@app.get('/health')
def health(db=Depends(get_db)):
    db.execute(text('SELECT 1'));return {'status':'ok','payment_mode':settings().payment_mode}
@app.get('/api/config')
def public_config():return {'payment_mode':settings().payment_mode,'demo_faults_enabled':settings().demo_faults_enabled}
@app.post('/api/checkout/orders')
def checkout(m=Depends(merchant),db=Depends(get_db),client=Depends(get_client)):
    o,token,approval=create_order(db,m,client,settings().payment_mode)
    return {**serialize_order(o),'buyer_token':token,'approval_url':approval,'provider_order_id':o.provider_id}
class CaptureRequest(BaseModel):
    order_id:str
    drop_response:bool=False
@app.post('/api/paypal/capture')
def capture_route(body:CaptureRequest,m=Depends(merchant),db=Depends(get_db),client=Depends(get_client)):
    if body.drop_response and not settings().demo_faults_enabled:raise HTTPException(403,'Demo faults disabled')
    return capture(db,scoped_order(db,m,body.order_id),client,body.drop_response)
@app.get('/api/orders/{oid}')
def get_order(oid:str,m=Depends(merchant),db=Depends(get_db)):return serialize_order(scoped_order(db,m,oid))
@app.post('/api/orders/{oid}/reconcile')
def reconcile_route(oid:str,m=Depends(merchant),db=Depends(get_db),client=Depends(get_client)):
    o=scoped_order(db,m,oid);reconcile(db,o,client);return serialize_order(o)
@app.post('/api/orders/{oid}/report')
def report_problem(oid:str,m=Depends(merchant),db=Depends(get_db)):
    from .services import incident
    o=scoped_order(db,m,oid);i=incident(db,o);db.commit();return {'incident_id':i.id}
@app.get('/api/buyer/status/{token}')
def buyer_status(token:str,db=Depends(get_db)):
    t=db.get(BuyerToken,digest(token))
    if not t or t.revoked or t.expires_at<=datetime.now(timezone.utc).isoformat():raise HTTPException(404,'Status link invalid or expired')
    o=db.get(Order,t.order_id)
    return {'state':o.state,'amount':o.amount,'currency':o.currency,'order_ref':o.id,'last_checked':o.checked_at,'next_step':'Payment confirmed. No further payment is needed.' if o.state=='CONFIRMED' else ('Payment failed. Contact the merchant to start a new checkout.' if o.state=='FAILED' else 'We are checking your payment. Please do not pay again yet.')}
@app.delete('/api/orders/{oid}/buyer-tokens')
def revoke(oid:str,m=Depends(merchant),db=Depends(get_db)):
    scoped_order(db,m,oid)
    for t in db.scalars(select(BuyerToken).where(BuyerToken.order_id==oid)):t.revoked=True
    db.commit();return {'revoked':True}
@app.post('/api/paypal/webhooks')
async def webhook(request:Request,db=Depends(get_db),client=Depends(get_client)):
    raw=bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk)>262144:raise HTTPException(413,'Webhook too large')
        raw.extend(chunk)
    try:event=json.loads(raw)
    except ValueError:raise HTTPException(400,'Invalid JSON')
    if not isinstance(event,dict) or not isinstance(event.get('id'),str):raise HTTPException(400,'Missing event ID')
    try:verified=client.verify_webhook(dict(request.headers),event)
    except Exception:raise HTTPException(503,'Verification unavailable; retry delivery')
    if not verified:
        db.add(Audit(action='webhook.signature_rejected'));db.commit();raise HTTPException(400,'Invalid webhook signature')
    from .services import accept_verified_webhook
    return accept_verified_webhook(db,event)
@app.get('/api/incidents')
def incidents(m=Depends(merchant),db=Depends(get_db)):
    rows=db.execute(select(Incident,Order).join(Order).where(Order.merchant_id==m.id).order_by(Incident.created_at.desc())).all()
    return [{'id':i.id,'title':i.title,'severity':i.severity,'created_at':i.created_at,'order_id':o.id,'state':o.state,'amount':o.amount,'mode':o.mode,'checked_at':o.checked_at} for i,o in rows]
@app.get('/api/incidents/{iid}')
def detail(iid:str,m=Depends(merchant),db=Depends(get_db)):
    i,o=scoped_incident(db,m,iid)
    events=db.scalars(select(Recorder).where(Recorder.order_id==o.id).order_by(Recorder.observed_at)).all()
    latest=db.scalar(select(Investigation).where(Investigation.incident_id==iid).order_by(Investigation.created_at.desc()))
    return {'incident_id':i.id,'title':i.title,**serialize_order(o),'events':[{k:getattr(e,k) for k in ('id','source','event_type','payload','occurred_at','observed_at')} for e in events],'investigation':latest.report if latest else None}
class InvestigationRequest(BaseModel):customer_message:str=Field(default='',max_length=4000)
@app.post('/api/incidents/{iid}/investigate')
def investigation(iid:str,body:InvestigationRequest,m=Depends(merchant),db=Depends(get_db)):
    facts=detail(iid,m,db);facts.pop('investigation',None);result=investigate(facts,body.customer_message)
    db.add(Investigation(incident_id=iid,report=result));db.add(Audit(merchant_id=m.id,action='investigation.created'));db.commit();return result
@app.get('/api/replay/scenarios')
def scenarios(m=Depends(merchant)):return SCENARIOS
@app.post('/api/replay/{scenario}')
def replay(scenario:str,m=Depends(merchant),db=Depends(get_db)):
    result=run_scenario(scenario);r=ReplayRun(merchant_id=m.id,scenario=scenario,result=result);db.add(r);db.commit();return {'id':r.id,**result}
@app.get('/api/replay')
def history(m=Depends(merchant),db=Depends(get_db)):
    return [{'id':r.id,'scenario':r.scenario,'created_at':r.created_at,**r.result} for r in db.scalars(select(ReplayRun).where(ReplayRun.merchant_id==m.id).order_by(ReplayRun.created_at.desc()).limit(20))]

# Same-origin production bundle; Vite's proxy supplies the same contract in development.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
DIST=Path(__file__).resolve().parents[2]/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/{path:path}',include_in_schema=False)
    def spa(path:str):
        if path.startswith(('api/','health/')):raise HTTPException(404,'Not found')
        return FileResponse(DIST/'index.html',headers={'Cache-Control':'no-cache','Referrer-Policy':'no-referrer'})
