import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import engine


@pytest.fixture
def db_session():
    """A session bound to a transaction that's rolled back after the test.

    Runs against the same database as DATABASE_URL — nothing written here
    is ever committed, so it's safe to run against a dev database that
    already has real data in it.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
