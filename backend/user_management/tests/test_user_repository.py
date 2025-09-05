import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from user_management.user_repository import UserRepository
from user_management.models import CreateUserRequest, UpdateUserRequest, AddPreferenceRequest
from unittest.mock import AsyncMock

test_url = "https://www.google.com/url?sa=i&url=https%3A%2F%2Funsplash.com%2Fs%2Fphotos%2Fimage&psig=AOvVaw3rjzDHLkqbyfpgr31b8uoa&ust=1753339002216000&source=images&cd=vfe&opi=89978449&ved=0CBYQjRxqFwoTCKCR_PSu0o4DFQAAAAAdAAAAABAE"

@pytest.fixture
def mock_db_manager():
    mock = AsyncMock()
    mock.get_connection.return_value.__aenter__.return_value = AsyncMock()
    return mock

@pytest.fixture
def user_repo(mock_db_manager):
    return UserRepository(mock_db_manager)

@pytest.mark.asyncio
async def test_create_user(user_repo, mock_db_manager):
    mock_conn = mock_db_manager.get_connection.return_value.__aenter__.return_value
    mock_conn.fetchrow.return_value = {
        "id": uuid4(),
        "clerk_user_id": "user_abc",
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "avatar_url": test_url,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "is_active": True
    }

    user_data = CreateUserRequest(
        clerk_user_id="user_abc",
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        avatar_url=test_url
    )

    user = await user_repo.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_add_user_preference(user_repo, mock_db_manager):
    mock_conn = mock_db_manager.get_connection.return_value.__aenter__.return_value
    mock_conn.execute.return_value = "INSERT 0 1"

    result = await user_repo.add_user_preference(
        uuid4(),
        AddPreferenceRequest(
            type="music",
            value="jazz",
            weight=0.9
        )
    )

    assert result is True

@pytest.mark.asyncio
async def test_get_current_mood(user_repo, mock_db_manager):
    mock_conn = mock_db_manager.get_connection.return_value.__aenter__.return_value
    mock_conn.fetchrow.return_value = {
        "mood": "happy",
        "intensity": "high",
        "context": "work success",
        "created_at": datetime.utcnow()
    }

    mood = await user_repo.get_current_mood(uuid4())

    assert mood is not None
    assert mood.mood == "happy"
    assert mood.intensity == "high"

@pytest.mark.asyncio
async def test_update_user(user_repo, mock_db_manager):
    mock_conn = mock_db_manager.get_connection.return_value.__aenter__.return_value
    mock_conn.fetchrow.return_value = {
        "id": uuid4(),
        "clerk_user_id": "user_abc",
        "email": "updated@example.com",
        "username": "updateduser",
        "first_name": "Updated",
        "last_name": "Name",
        "avatar_url": test_url,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "is_active": True
    }

    update_data = UpdateUserRequest(
        username="updateduser",
        first_name="Updated",
        last_name="Name",
        avatar_url=test_url
    )

    user = await user_repo.update_user(uuid4(), update_data)

    assert user.username == "updateduser"
    assert user.first_name == "Updated"

