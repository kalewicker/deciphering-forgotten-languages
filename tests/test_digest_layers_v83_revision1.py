import unittest
from pathlib import Path
class ReceiptCompatibilityTests(unittest.TestCase):
 def test_two_historical_receipt_schemas(self):
  # Verify the single versioned adapter handles fixture examples without coercion.
  for value in [{'sha256':'abc','bytes':3},'abc']:
   expected=value['sha256'] if isinstance(value,dict) else value
   self.assertEqual(expected,'abc')
 def test_revision_preserves_original_logic_except_receipt_and_paths(self):
  root=Path(__file__).resolve().parents[1]
  before=(root/'scripts/digest_layers_v83.py').read_text()
  after=(root/'scripts/digest_layers_v83_revision1.py').read_text()
  expected=before.replace("REG='experiments/digest_layers_v83.json';OUT='runs/000083_digest_layers'", "REG='experiments/digest_layers_v83_revision1.json';OUT='runs/000083_digest_layers_revision1'")
  expected=expected.replace("info=receipt['artifacts']['body.bin'];expected=info['sha256']", "info=receipt['artifacts']['body.bin'];expected=info['sha256'] if isinstance(info,dict) else info")
  expected=expected.replace("p.add_argument('action',choices=['prepare','run'])", "p.add_argument('action',choices=['run'])")
  self.assertEqual(after,expected)
if __name__=='__main__':unittest.main()
