import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from .db import Session
from .models import Outbox, Order, now
from .paypal import get_client
from .services import reconcile

def tick():
    with Session() as db:
        job=db.scalar(select(Outbox).where(Outbox.status=='PENDING',Outbox.available_at<=now()).order_by(Outbox.available_at).with_for_update(skip_locked=True).limit(1))
        if not job:return False
        job.attempts+=1
        resolved=reconcile(db,db.get(Order,job.order_id),get_client())
        job.status='DONE' if resolved else ('EXHAUSTED' if job.attempts>=6 else 'PENDING')
        job.available_at=(datetime.now(timezone.utc)+timedelta(seconds=min(300,2**job.attempts))).isoformat();db.commit();return True
if __name__=='__main__':
    while True:
        if not tick():time.sleep(2)
