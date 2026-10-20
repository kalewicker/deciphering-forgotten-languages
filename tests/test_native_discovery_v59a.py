import hashlib
import unittest
from fl_decipher.native_discovery_v59a import receipt_matches


class ReceiptSchemaCorrectionTests(unittest.TestCase):
    def test_receipts_with_and_without_path(self):
        raw = b'frozen body'
        artifact = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        for body in [artifact, artifact | {'path': '/original/local/path'}]:
            self.assertTrue(receipt_matches({'transport_complete': True, 'artifacts': {'body.bin': body}}, raw))

    def test_hash_size_and_transport_must_all_match(self):
        raw = b'frozen body'
        body = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'path': '/original/local/path'}
        for change in [{'sha256': '0' * 64}, {'bytes': len(raw) + 1}]:
            self.assertFalse(receipt_matches({'transport_complete': True, 'artifacts': {'body.bin': body | change}}, raw))
        for flag in [False, None, 1]:
            self.assertFalse(receipt_matches({'transport_complete': flag, 'artifacts': {'body.bin': body}}, raw))
        self.assertFalse(receipt_matches({}, raw))
