"""A lightweight wrapper around pymysqlpool.
"""

import logging
import pymysql
from pymysqlpool import ConnectionPool

version = "0.1"
version_info = (0, 1, 0, 0)


class Connection(object):
    """A lightweight wrapper around pymysqlpool.
    """
    def __init__(self, **kwargs):
        self.host = kwargs.get("host", "") + ":" + str(kwargs.get("port", ""))
        self._db_args = kwargs
        self._conn_pool = ConnectionPool(**kwargs)

    def __del__(self):
        self.close()

    def close(self):
        """Closes this database connection."""
        if getattr(self, "_db", None) is not None:
            self._conn_pool.close()
            self._conn_pool = None

    def reconnect(self):
        """Closes the existing database connection and re-opens it."""
        self.close()
        self._conn_pool = ConnectionPool(**self._db_args)

    def iter(self, query, *parameters):
        """Returns an iterator for the given query and parameters."""
        with self._conn_pool.cursor() as cursor:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            for row in cursor:
                yield Row(zip(column_names, row))

    def query(self, query, *parameters):
        """Returns a row list for the given query and parameters."""
        with self._conn_pool.cursor() as cursor:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            return [Row(zip(column_names, row)) for row in cursor]

    def execute_procedure(self,proc_name,*parameter):
        with self._conn_pool.cursor() as cursor:
            ret1 = cursor.callproc(proc_name, args=parameter)
            cursor.execute('select 1')
            result = cursor.fetchall()
            return result


    def get(self, query, *parameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        else:
            return rows[0]

    # rowcount is a more reasonable default return value than lastrowid,
    # but for historical compatibility execute() must return lastrowid.
    def execute(self, query, *parameters):
        """Executes the given query, returning the lastrowid from the query."""
        return self.execute_lastrowid(query, *parameters)

    def execute_lastrowid(self, query, *parameters):
        """Executes the given query, returning the lastrowid from the query."""
        with self._conn_pool.cursor() as cursor:
            self._execute(cursor, query, parameters)
            return cursor.lastrowid

    def execute_rowcount(self, query, *parameters):
        """Executes the given query, returning the rowcount from the query."""
        with self._conn_pool.cursor() as cursor:
            self._execute(cursor, query, parameters)
            return cursor.rowcount

    def executemany(self, query, parameters):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.
        """
        return self.executemany_lastrowid(query, parameters)

    def executemany_lastrowid(self, query, parameters):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.
        """
        with self._conn_pool.cursor() as cursor:
            cursor.executemany(query, parameters)
            return cursor.lastrowid

    def executemany_rowcount(self, query, parameters):
        """Executes the given query against all the given param sequences.

        We return the rowcount from the query.
        """
        with self._conn_pool.cursor() as cursor:
            cursor.executemany(query, parameters)
            return cursor.rowcount

    def _execute(self, cursor, query, parameters):
        try:
            return cursor.execute(query, parameters)
        except pymysql.OperationalError:
            logging.error("Error connecting to MySQL on %s", self.host)
            raise


class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
