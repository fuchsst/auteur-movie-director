"""Root pytest configuration for backend tests"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
