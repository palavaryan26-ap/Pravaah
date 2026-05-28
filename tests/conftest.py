import os
import pytest
from fastapi.testclient import TestClient

from pravaah.app.core.config import reset_config
from pravaah.app.main import create_app

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["PRAVAAH_DATABASE_URL"] = "sqlite+aiosqlite:///./test_pravaah.db"
    os.environ["PRAVAAH_AI__ENABLED"] = "true"
    os.environ["PRAVAAH_AI__PROVIDER"] = "mock"
    reset_config()
    yield
    # Cleanup DB file after tests
    if os.path.exists("./test_pravaah.db"):
        os.remove("./test_pravaah.db")


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient."""
    from pravaah.app.core.registry import registry
    registry.clear()
    
    app = create_app()
    # TestClient automatically runs lifespan events (plugin loading/db init)
    with TestClient(app) as c:
        yield c
