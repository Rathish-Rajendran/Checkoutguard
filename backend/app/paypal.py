import threading
from typing import Protocol
import httpx
from .config import settings

class PayPalClient(Protocol):
    def create_order(self, key: str, reference: str) -> dict: ...
    def capture_order(self, order_id: str, key: str) -> dict: ...
    def get_order(self, order_id: str) -> dict: ...
    def verify_webhook(self, headers: dict, event: dict) -> bool: ...

class FakePayPalClient:
    """No credentials or network access. Resources survive worker restarts via recorder evidence."""
    def __init__(self):
        self.orders = {}; self.capture_count = 0; self.lock = threading.Lock()
        self.unresolved = False
    def create_order(self, key, reference):
        resource = {'id': 'SIM-'+reference, 'status': 'APPROVED', 'purchase_units': [{'reference_id': reference, 'amount': {'value': '49.00', 'currency_code': 'USD'}}]}
        self.orders[resource['id']] = resource
        return resource
    def capture_order(self, order_id, key):
        with self.lock:
            resource = self.orders[order_id]
            if self.unresolved: raise TimeoutError('Simulated provider unavailable')
            if not resource['purchase_units'][0].get('payments'):
                resource['purchase_units'][0]['payments'] = {'captures': [{'id': 'SIM-CAP-'+key, 'status': 'COMPLETED', 'amount': {'value': '49.00', 'currency_code': 'USD'}}]}
                resource['status'] = 'COMPLETED'; self.capture_count += 1
            return resource
    def get_order(self, order_id):
        if self.unresolved: raise TimeoutError('Simulated provider unavailable')
        return self.orders[order_id]
    def verify_webhook(self, headers, event): return False

class SandboxPayPalClient:
    base = 'https://api-m.sandbox.paypal.com'
    def request(self, method, path, *, key=None, body=None):
        s = settings()
        with httpx.Client(timeout=20) as client:
            auth = client.post(self.base+'/v1/oauth2/token', auth=(s.paypal_client_id, s.paypal_client_secret), data={'grant_type': 'client_credentials'})
            auth.raise_for_status()
            headers = {'Authorization': 'Bearer '+auth.json()['access_token']}
            if key: headers['PayPal-Request-Id'] = key
            response = client.request(method, self.base+path, headers=headers, json=body)
            response.raise_for_status()
            return response.json()
    def create_order(self, key, reference):
        return self.request('POST', '/v2/checkout/orders', key=key, body={'intent': 'CAPTURE', 'purchase_units': [{'reference_id': reference, 'amount': {'currency_code': 'USD', 'value': '49.00'}}], 'payment_source': {'paypal': {'experience_context': {'return_url': settings().public_url+'/checkout', 'cancel_url': settings().public_url+'/checkout', 'user_action': 'PAY_NOW'}}}})
    def capture_order(self, order_id, key): return self.request('POST', '/v2/checkout/orders/'+order_id+'/capture', key=key, body={})
    def get_order(self, order_id): return self.request('GET', '/v2/checkout/orders/'+order_id)
    def verify_webhook(self, headers, event):
        required = ['paypal-auth-algo', 'paypal-cert-url', 'paypal-transmission-id', 'paypal-transmission-sig', 'paypal-transmission-time']
        if not all(headers.get(k) for k in required): return False
        result = self.request('POST', '/v1/notifications/verify-webhook-signature', body={
            'auth_algo': headers[required[0]], 'cert_url': headers[required[1]], 'transmission_id': headers[required[2]], 'transmission_sig': headers[required[3]], 'transmission_time': headers[required[4]], 'webhook_id': settings().paypal_webhook_id, 'webhook_event': event})
        return result.get('verification_status') == 'SUCCESS'

fake = FakePayPalClient()
def get_client(): return SandboxPayPalClient() if settings().payment_mode == 'sandbox' else fake
