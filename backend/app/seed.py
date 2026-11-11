from .db import Session
from .models import Merchant
from .config import settings
from .services import digest

def seed():
    with Session() as db:
        m=db.get(Merchant,'demo')
        if not m:db.add(Merchant(id='demo',name='Northstar Supply',key_hash=digest(settings().merchant_api_key)))
        else:m.key_hash=digest(settings().merchant_api_key)
        db.commit()
if __name__=='__main__':seed()
