from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from urllib.parse import urlsplit

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', hide_input_in_errors=True)
    database_url: str = 'sqlite:///./checkoutguard.db'
    payment_mode: str = 'simulated'
    merchant_api_key: str = 'local-demo-key-change-me'
    paypal_client_id: str = ''
    paypal_client_secret: str = ''
    paypal_webhook_id: str = ''
    public_url: str = 'http://localhost:5173'
    ai_provider: str = 'ollama'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5:3b'
    ollama_timeout_seconds: float = Field(default=120, gt=0, le=600)
    demo_faults_enabled: bool = True
    @model_validator(mode='after')
    def validate_mode(self):
        if self.ai_provider not in ('ollama', 'deterministic'):
            raise ValueError('AI_PROVIDER must be ollama or deterministic')
        endpoint = urlsplit(self.ollama_base_url)
        if endpoint.scheme not in ('http', 'https') or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path not in ('', '/'):
            raise ValueError('OLLAMA_BASE_URL must be an HTTP(S) origin without credentials or a path')
        if not self.ollama_model.strip():
            raise ValueError('OLLAMA_MODEL must not be empty')
        if self.database_url.startswith(('postgres://', 'postgresql://')):
            self.database_url = 'postgresql+psycopg://' + self.database_url.split('://', 1)[1]
        if self.payment_mode not in ('simulated', 'sandbox'):
            raise ValueError('Only simulated and sandbox payments are supported')
        if self.payment_mode == 'sandbox' and not (self.paypal_client_id and self.paypal_client_secret and self.paypal_webhook_id):
            raise ValueError('Sandbox requires PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET and PAYPAL_WEBHOOK_ID')
        if self.payment_mode == 'sandbox' and len(self.merchant_api_key) < 32:
            raise ValueError('Sandbox requires a custom MERCHANT_API_KEY of at least 32 characters')
        if self.payment_mode == 'sandbox':
            origin = urlsplit(self.public_url)
            local = origin.hostname in ('localhost', '127.0.0.1', '::1')
            if (not origin.hostname or origin.username is not None or origin.password is not None
                    or origin.path or origin.query or origin.fragment
                    or not (origin.scheme == 'https' or (local and origin.scheme == 'http'))):
                raise ValueError('PUBLIC_URL must be an HTTPS origin or an HTTP loopback origin')
        return self

@lru_cache
def settings(): return Settings()
