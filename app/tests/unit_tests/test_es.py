import json
import unittest
from helpers.singletons import es
import os


class TestES(unittest.TestCase):
    def setUp(self):
        self.test_doc = json.load(open("/app/tests/unit_tests/files/doc_for_es_testing.json"))
        self.path_sorted_doc = '/app/tests/unit_tests/files/sorted_docs [Time-LogonType-LogHost-UserName-LogonID].json'
        self.path_sorted_doc_scan_duration = '/app/tests/unit_tests/files/sorted_docs_for_scan_duration.json'
        self.path_mapping = '/app/tests/unit_tests/files/mapping.json'

    def _hash(self, data):
        data = str(data)
        import hashlib
        m = hashlib.md5()
        m.update(data.encode('utf-8'))
        return m.hexdigest()

    def test_onthot_encode(self):
        self.assertEqual(es.get_field_by_path(self.test_doc, 'OsqueryFilter.md5'), 'cb2a1c2ea227f0338e7f3a8bc03c3d6e')
        self.assertEqual(es.get_field_by_path(self.test_doc, 'meta.logged_in_users_details.time'), '1529997655')

    def test_get_fields_by_path(self):
        self.assertEqual(
            es.get_fields_by_path(
                self.test_doc,
                ['OsqueryFilter.md5', 'meta.logged_in_users_details.time']
            ),
            ['cb2a1c2ea227f0338e7f3a8bc03c3d6e', '1529997655']
        )

    def test_get_type(self):
        mapping = json.load(open(self.path_mapping))

        def custom_get_mapping(*args, index=None):
            return mapping

        es.conn = es
        es.conn.indices = es
        es.conn.indices.get_mapping = custom_get_mapping
        es.settings.config.set('general', 'es_index_pattern', 'host_events')
        es.settings.config.set('general', 'timestamp_field', 'Time')

        self.assertEqual(es.get_type('SubjectLogonID'), 'text')

    def test_time_based_scan(self):
        tmp_scan = es.scan
        tmp_get_type = es.get_type

        def custom_es_scan(**args):
            data = open(self.path_sorted_doc)
            for line in data:
                yield json.loads(line)
            data.close()

        def custom_get_type(**args):
            return "Doesn't matter because we overwrite es.scan..."

        # Overwrite functions which read the ES database
        es.scan = custom_es_scan
        es.get_type = custom_get_type

        aggregator = 'LogonType'
        fields_value_to_correlate = ['LogHost', 'UserName', 'LogonID']
        lucene_query = es.filter_by_query_string('(EventID:4624 OR EventID:4634) AND _exists_:LogonID AND _exists_:LogHost AND (LogonType: 2 OR LogonType: 9)')

        aggregations = []

        h = ''

        n_docs = 0

        for aggregation, documents in es.time_based_scan(
            aggregator=aggregator,
            fields_value_to_correlate=fields_value_to_correlate,
            query_fields=None,
            lucene_query=lucene_query,
            drop_if_unknow_end=True
        ):
            aggregations.append(aggregation)

            for i, (doc, start, duration) in enumerate(documents):
                h = self._hash(doc['_id'] + h)
                n_docs += 1

        self.assertEqual(aggregations, [2, 9])
        self.assertEqual(h, '5b6d661503e83bb2f8551cceee62940b')
        self.assertEqual(n_docs, 1219)

        es.scan = tmp_scan
        es.get_type = tmp_get_type

    def test_duration_scan(self):
        tmp_scan = es.scan
        tmp_get_type = es.get_type

        def custom_es_scan(**args):
            data = open(self.path_sorted_doc_scan_duration)
            for line in data:
                yield json.loads(line)
            data.close()

        def custom_get_type(**args):
            return "Doesn't matter because we overwrite es.scan..."

        # Overwrite functions which read the ES database
        es.scan = custom_es_scan
        es.get_type = custom_get_type
        es.settings.config.set('general', 'timestamp_field', 'Time')

        aggregator = 'LogonType'
        fields_value_to_correlate = ['LogHost', 'UserName', 'LogonID']
        lucene_query = es.filter_by_query_string('(EventID:4624 OR EventID:4634) AND _exists_:LogonID AND _exists_:LogHost AND (LogonType: 2 OR LogonType: 9)')

        aggregations = []

        h = ''

        n_docs = 0

        for aggregation, documents in es.scan_duration(
            aggregator=aggregator,
            lucene_query=lucene_query,
            start_condition={"EventID": 4624},
            end_condition={"EventID": 4634},
            fields_value_to_correlate=fields_value_to_correlate,
            drop_if_unknow_start=True,
            drop_if_unknow_end=True
        ):
            aggregations.append(aggregation)

            for i, (doc, start, duration) in enumerate(documents):
                h = self._hash(doc['_id'] + h)
                n_docs += 1

        self.assertEqual(aggregations, [0, 2, 3])
        self.assertEqual(h, 'b0ab322a6edb72f6ade8d7db0306336e')
        self.assertEqual(n_docs, 16047)

        es.scan = tmp_scan
        es.get_type = tmp_get_type
