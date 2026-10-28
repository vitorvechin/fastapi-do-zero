from contextlib import contextmanager
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fast_zero.app import app
from fast_zero.database import get_session
from fast_zero.models import User as UserModel
from fast_zero.models import table_registry


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    try:
        table_registry.metadata.create_all(engine)

        with Session(engine) as db_session:
            yield db_session

    finally:
        table_registry.metadata.drop_all(engine)
        engine.dispose()


@contextmanager  # Allows this function to be used with a "with" statement
def _mock_db_time(*, model, time=datetime(2026, 10, 20)):

    # Underscored function name to indicate it's intended for internal use only
    def fake_time_hook(_mapper, _connection, target):
        if hasattr(target, 'created_at'):
            target.created_at = time

        if hasattr(target, 'updated_at'):
            target.updated_at = time

    event.listen(model, 'before_insert', fake_time_hook)

    try:
        yield time

    finally:
        event.remove(model, 'before_insert', fake_time_hook)


@pytest.fixture
def mock_db_time():
    return _mock_db_time


@pytest.fixture
def user(session: Session):
    mock_user = UserModel(
        username='test', email='test@test.com', password='test123'
    )

    session.add(mock_user)
    session.commit()
    session.refresh(mock_user)

    return mock_user
