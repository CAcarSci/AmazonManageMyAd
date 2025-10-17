import os
from contextlib import contextmanager
import psycopg


@contextmanager
def get_conn():
    url = os.environ["DATABASE_URL"].replace("+psycopg", "")
    with psycopg.connect(url, autocommit=True) as conn:
        yield conn
