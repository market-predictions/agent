import json
import unittest
from pathlib import Path

class RouterPolicyTests(unittest.TestCase):
    def test_free_route_exclusion(self):
        c = json.loads((Path(__file__).resolve().parents[1] / 'runtime/freellmapi.default.json').read_text())
        self.assertEqual({k['platform'] for k in c['keys']}, {'kilo', 'ovh'})
        self.assertEqual(c['routing']['strategy'], 'balanced')
        self.assertEqual(len(c['models']), 1)
        self.assertIs(c['models'][0]['enabled'], False)
        self.assertIs(c['models'][0]['fallbackEnabled'], False)
