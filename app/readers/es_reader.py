import re
import json
import requests
from readers.abc_reader import Reader


class ES(Reader):
    '''
    Documentation here:
    https://www.elastic.co/guide/en/elasticsearch/reference/6.7/sql-rest.html
    '''
    def __init__(self, url='http://127.0.0.1:9200',
                 scroll_size=10000, timeout='90s'):
        self.url = url
        self.scroll_size = scroll_size
        self.timeout = timeout

    def _query(self, query, url='', method='GET'):
        '''
        Params
        ======
        - query (dict): Json data send to Elasticsearch
        - url    (str): Url on which we send the json
        - method (str): GET or POST
        '''
        if method == 'GET':
            response = requests.get(self.url, json=query)

        elif method == 'POST':
            response = requests.post(self.url + url, json=query)

        if response.status_code != 200:
            raise Exception('Error, connection to ES')

        return json.loads(response.text)

    def sql_query(self, sql_query):
        '''
        Params
        ======
        - sql_query (str): SQL query sent to ES

        Usage
        =====
        for row in ES.sql_query(sql_query):
            pass
        '''
        query = {
            'query': sql_query,
            'fetch_size': self.scroll_size,
            'request_timeout': self.timeout
        }

        response = self._query(query, '/_xpack/sql?format=json', 'POST')

        if 'rows' not in response:
            raise Exception('Error, connection to ES')

        cursor = response['cursor']
        columns = response['columns']

        n_cols = len(response['columns'])

        for row in response['rows']:
            yield row[:n_cols]

        while True:
            response = self._query(
                {'cursor': cursor},
                '/_xpack/sql?format=json',
                'POST'
            )

            if response is None or 'rows' not in response:
                raise Exception('Error, connection to ES')

            for row in response['rows']:
                yield row[:n_cols]

            if 'cursor' not in response:
                break

            cursor = response['cursor']

    def sql_query_bucket(self, sql_query, bucket=[]):
        '''
        Params
        ======
        - sql_query    (str): SQL query, the rows must be ordered by 'bucket' !
        - bucket      (list): List of column index to use to create buckets

        Usage
        =====
        for bucket, rows in ES.sql_query_bucket(sql_query, 0):
            for row in rows:
                pass
        '''
        if not bucket:
            yield '-', self.sql_query(sql_query)

        else:
            def bucket_iter():
                yield bucket_iter.row

                for row in bucket_iter.iter:
                    bucket_value = [row[b] for b in bucket]

                    if bucket_value != bucket_iter.bucket_value:
                        bucket_iter.row = row
                        bucket_iter.bucket_value = bucket_value
                        break

                    yield row

                else:
                    bucket_iter.stop = True

            bucket_iter.iter = self.sql_query(sql_query)
            bucket_iter.row = next(bucket_iter.iter)
            bucket_iter.bucket_value = [bucket_iter.row[b] for b in bucket]
            bucket_iter.stop = False

            while not bucket_iter.stop:
                b_iter = bucket_iter()

                yield bucket_iter.bucket_value, b_iter

                # If we break the loop
                # We should pass to the next bucket
                for _ in b_iter:
                    pass

    def columns(self, sql_query):
        '''
        Params
        ======
        - sql_query (str): SQL query

        Return
        ======
        A list of columns names
        '''
        query = {
            'query': sql_query,
            'fetch_size': self.scroll_size,
            'request_timeout': self.timeout,
            'filter': {
                'range': {'page_count': {'lt': 0}}
            }
        }
        response = self._query(query, '/_xpack/sql?format=json', 'POST')

        if 'columns' not in response:
            raise Exception('Error, connection to ES')

        return [col['name'] for col in response['columns']]

    def n_rows(self, sql_query):
        total_rows = 0
        for _ in self.sql_query(sql_query):
            total_rows += 1
        return total_rows
