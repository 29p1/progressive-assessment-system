from pathlib import Path
import sys

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


@pytest.fixture
def app():
    mock_client = mongomock.MongoClient()
    test_db = mock_client["test_progressive_assessment"]
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "MONGO_DB": test_db,
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
