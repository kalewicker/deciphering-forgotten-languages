import unittest

from fl_decipher.reviewer_controls_v75 import ordered_anchors, assess


class LiteralControlTests(unittest.TestCase):
    def test_whitespace_case_and_unicode_normalization(self):
        ok, _ = ordered_anchors(' A\n  cafe\u0301; ZAZEL ', ['a', 'café', 'zazel'])
        self.assertTrue(ok)

    def test_membership_is_insufficient_when_order_is_reversed(self):
        self.assertFalse(ordered_anchors('Pico Ficino Posidonius', ['Posidonius', 'Ficino', 'Pico'])[0])

    def test_shared_suffix_does_not_match_wrong_full_label(self):
        self.assertFalse(ordered_anchors('Intelligentia Saturni', ['Daemonium Saturni'])[0])

    def test_word_boundaries_and_nonoverlap(self):
        self.assertFalse(ordered_anchors('azazel zazelx _zazel', ['zazel'])[0])
        self.assertFalse(ordered_anchors('a b', ['a b', 'b'])[0])
        self.assertTrue(ordered_anchors('a b a b', ['a b', 'a b'])[0])

    def test_always_supporting_false_claim_cannot_pass(self):
        spans = {'start': 0, 'end': 1, 'text': 'a'}
        cases = [{'case_id': 'C1', 'fl_span': spans, 'source_span': spans}]
        value = {'reviewer': {'name': 'fixture', 'kind': 'automated', 'identifier': 'fixture',
                            'prior_exposure': 'Controlled fixture.'},
                 'completed_at_utc': '2026-10-21T00:00:00+00:00', 'review_completed': True,
                 'judgments': [{'case_id': 'C1', 'disposition': 'supported', 'fl_span': spans,
                                'source_span': spans, 'explanation': 'Fixture only.'}],
                 'limitations': ['No semantic evaluation.']}
        result = assess(value, cases, [{'case_id': 'C1', 'expected': 'rejected'}],
                        {'fl': 'a', 'source': 'a'}, 'fixture')
        self.assertTrue(result['schema_and_quotes_complete'])
        self.assertEqual(result['false_supported'], 1)
        self.assertFalse(result['literal_control_gate'])
        value['judgments'][0]['disposition'] = 'uncertain'
        result = assess(value, cases, [{'case_id': 'C1', 'expected': 'rejected'}],
                        {'fl': 'a', 'source': 'a'}, 'fixture')
        self.assertEqual(result['false_rejected'], 0)
        self.assertEqual(result['uncertain_or_missing'], 1)
        self.assertFalse(result['literal_control_gate'])

    def test_missing_and_malformed_returns_fail_with_full_denominator(self):
        cases = [{'case_id': 'C1', 'fl_span': {}, 'source_span': {}}]
        for value in [None, {}, {'judgments': [{'case_id': []}]}]:
            result = assess(value, cases, [{'case_id': 'C1', 'expected': 'supported'}],
                            {'fl': '', 'source': ''}, 'fixture')
            self.assertFalse(result['literal_control_gate'])
            self.assertEqual(result['case_denominator'], 1)


if __name__ == '__main__':
    unittest.main()
