import abc


class Reader(abc.ABC):
    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def sql_query_bucket(self, sql_query, bucket):
        '''
        Params
        ======
        - sql_query    (str): SQL query, the rows must be ordered by 'bucket' !
        - bucket      (list): List of column index to use to create buckets

        Usage
        =====
        for bucket, rows in ES.sql_query_bucket(sql_query, [0]):
            for row in rows:
                pass
        '''
        pass

    @abc.abstractmethod
    def n_rows(self, sql_query):
        '''
        Return the totals number of rows in the response
        '''
        pass

    @abc.abstractmethod
    def columns(self, sql_query):
        '''
        Return a list of columns name
        '''
        pass
