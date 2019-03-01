import unittest
import helpers.utils
from millify import millify
import numpy as np


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_ip_ranges(self):
        if not helpers.utils.match_ip_ranges("127.0.0.1", ["127.0.0.0/24"]):
            raise AssertionError("Error matching IP ranges!")

        if not helpers.utils.match_ip_ranges("127.0.0.1", ["127.0.0.1/32"]):
            raise AssertionError("Error matching IP ranges!")

        if helpers.utils.match_ip_ranges("127.0.0.1", ["192.0.0.1/16"]):
            raise AssertionError("Error matching IP ranges!")

    def test_shannon_entropy(self):
        _str = "dummy"
        entropy = helpers.utils.shannon_entropy(_str)
        self.assertAlmostEqual(entropy, 1.921928094887)

        _str = ""
        entropy = helpers.utils.shannon_entropy(_str)
        self.assertAlmostEqual(entropy, 0)

    def test_millify(self):
        mill_str = millify(25000)
        self.assertEqual(mill_str, "25k")

        # This is a bug in the library!!
        mill_str = millify(999999)
        self.assertEqual(mill_str, "1000k")

        mill_str = millify(1000000)
        self.assertEqual(mill_str, "1M")

    def test_flatten_sentence(self):
        test_sentence = ["test", "123"]
        self.assertEqual("test - 123", helpers.utils.flatten_sentence(test_sentence))

        test_sentence = ["test", ["123", "234"]]  # Too complex, we don't flatten this, there is no reasonable way
        self.assertEqual(None, helpers.utils.flatten_sentence(test_sentence))

        test_sentence = 1
        self.assertEqual("1", helpers.utils.flatten_sentence(test_sentence))

        test_sentence = [1, 2]
        self.assertEqual("1 - 2", helpers.utils.flatten_sentence(test_sentence))

        test_sentence = None
        self.assertEqual(None, helpers.utils.flatten_sentence(test_sentence))

        test_sentence = "test"
        self.assertEqual("test", helpers.utils.flatten_sentence(test_sentence))

    # fields: {hostname: [WIN-DRA, WIN-EVB], draman}
    # output: [[WIN-DRA, draman], [WIN-EVB, draman]]
    def test_flatten_fields_into_sentences(self):
        sentence_format = ["hostname", "username"]
        fields = dict({"hostname": ["WIN-A", "WIN-B"], "username": "draman"})

        res = helpers.utils.flatten_fields_into_sentences(fields, sentence_format)

        expected_res = [['WIN-A', 'draman'], ['WIN-B', 'draman']]
        self.assertEqual(res, expected_res)

        fields = dict({"hostname": ["WIN-A", "WIN-B"], "username": ["evb", "draman"]})
        res = helpers.utils.flatten_fields_into_sentences(fields, sentence_format)

        expected_res = [['WIN-A', 'evb'], ['WIN-B', 'evb'], ['WIN-A', 'draman'], ['WIN-B', 'draman']]
        self.assertEqual(res, expected_res)

        fields = dict({"hostname": ["WIN-A", "WIN-A"], "username": ["evb", "draman"]})
        res = helpers.utils.flatten_fields_into_sentences(fields, sentence_format)

        # In our implementation, duplicates are allowed!
        expected_res = [['WIN-A', 'evb'], ['WIN-A', 'evb'], ['WIN-A', 'draman'], ['WIN-A', 'draman']]
        self.assertEqual(res, expected_res)

        # More complex example
        sentence_format = ["intro", "event_type", "source_ip", "ip_summary_legacy", "info"]
        fields = {'intro': ['Intro 1', 'Intro 2'], 'event_type': 'test_event', 'source_ip': '8.8.8.8', 'ip_summary_legacy': ['Summary 1', 'Summary 2'], 'info': ['Info 1', 'Info 2']}

        sentences = helpers.utils.flatten_fields_into_sentences(fields=fields, sentence_format=sentence_format)

        expected_sentences_length = 1
        for k, v in fields.items():
            if type(v) is list:
                expected_sentences_length = expected_sentences_length * len(v)

        self.assertEqual(len(sentences), expected_sentences_length)

    def test_replace_placeholder_fields_with_values(self):
        res = helpers.utils.replace_placeholder_fields_with_values(placeholder="this one has no placeholders", fields=None)
        self.assertEqual(res, "this one has no placeholders")

        res = helpers.utils.replace_placeholder_fields_with_values(placeholder="this one has {one} placeholders", fields=dict({"one": "hello"}))
        self.assertEqual(res, "this one has hello placeholders")

        res = helpers.utils.replace_placeholder_fields_with_values(placeholder="{one} {two}!", fields=dict({"one": "hello", "two": "world"}))
        self.assertEqual(res, "hello world!")

    def test_is_base64_encoded(self):
        test_str = None
        res = helpers.utils.is_base64_encoded(test_str)
        self.assertEqual(res, False)

        test_str = "hello world"
        res = helpers.utils.is_base64_encoded(test_str)
        self.assertEqual(res, False)

        test_str = "QVlCQUJUVQ=="
        res = helpers.utils.is_base64_encoded(test_str)
        self.assertEqual(res, "AYBABTU")

        test_str = ""
        res = helpers.utils.is_base64_encoded(test_str)
        self.assertEqual(res, "")

    def test_decision_frontier(self):
        with self.assertRaises(ValueError):
            helpers.utils.get_decision_frontier("does_not_exist", [0, 1, 2], 2, "high")

        # Test percentile - IMPORTANT - the values array is converted into a set before calculating the percentile!
        res = helpers.utils.get_decision_frontier("percentile", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10)
        self.assertEqual(res, 1)

        # Test MAD
        res = helpers.utils.get_decision_frontier("mad", [1, 1, 2, 2, 4, 6, 9], 1, "high")  # MAD should be 2

        median = np.nanmedian([1, 1, 2, 2, 4, 6, 9])
        sensitivity = 1
        mad = 1
        self.assertEqual(median + sensitivity * mad, res)  # 1 = sensitivity, 1 = MAD, median = 2

        res = helpers.utils.get_decision_frontier("mad", [1, 1, 2, 2, 4, 6, 9], 2, "high")  # MAD should be 4
        sensitivity = 2
        self.assertEqual(median + sensitivity * mad, res)  # 2 = sensitivity, 1 = MAD, median = 2

    
