import hashlib
import hmac
import posixpath
from urllib.parse import urlencode, urljoin, urlparse, urlunparse
from api.config import settings


def verify_signature(id: str, signature: str) -> bool:
    mac = hmac.new(settings.SIGNATURE_SECRET.encode(), id.encode(), hashlib.sha256)
    expected_sig = mac.hexdigest()
    return hmac.compare_digest(expected_sig, signature)

def generate_sig(id: str) -> str:
    return hmac.new(settings.SIGNATURE_SECRET.encode(), id.encode(), hashlib.sha256).hexdigest()

def generate_webhook_url(id: str)->str:
    sig = {"sig": generate_sig(id)}
    
    base_url = settings.APP_BASE_URL
    if not base_url.endswith("/"):
        base_url += "/"

    full_path = posixpath.join("webhook", id)
    full_url = urljoin(base_url, full_path)

    parsed_url = urlparse(full_url)
    new_query = urlencode(sig)

    return urlunparse(parsed_url._replace(query=new_query))