"""Receipt-schema correction only; E59 declarations and decision rules unchanged."""
import hashlib


def receipt_matches(receipt, raw):
    body = receipt.get('artifacts', {}).get('body.bin', {})
    return (receipt.get('transport_complete') is True and body.get('sha256') == hashlib.sha256(raw).hexdigest()
            and body.get('bytes') == len(raw))
