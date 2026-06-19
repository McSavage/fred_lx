import psycopg
import pytest

from fred_lx.config import settings
from fred_lx.storage.postgres_store import apply_schema, connect


def _postgres_reachable() -> bool:
    try:
        with connect():
            return True
    except psycopg.OperationalError:
        return False


@pytest.fixture
def pg_conn():
    if not _postgres_reachable():
        pytest.skip(f"Postgres not reachable at {settings.postgres_host}:{settings.postgres_port}")

    conn = connect()
    apply_schema(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM treasury_par_yields WHERE source = 'test'")
        conn.commit()
        yield conn
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM treasury_par_yields WHERE source = 'test'")
        conn.commit()
        conn.close()
