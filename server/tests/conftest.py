import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure server root is on python path
server_root = Path(__file__).resolve().parent.parent
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))

from app.main import app
from app.workers.handlers import register_all_handlers
from app.workers.queue import task_queue

@pytest.fixture(scope="session", autouse=True)
def setup_app():
    register_all_handlers()
    task_queue.start()

@pytest.fixture
def client():
    return TestClient(app)

