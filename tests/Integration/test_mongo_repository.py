import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.Infrastructure.Persistence.MongoGroupRepository import MongoGroupRepository
from src.Domain.Entity.Group import Group
from src.Domain.ValueObject.LinkSettings import LinkSettings

@pytest_asyncio.fixture
async def db_collection():
    """Setup a clean test database and teardown after test."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_superbot_db"]
    yield db
    # Cleanup: drop the test database after the test
    await client.drop_database("test_superbot_db")

@pytest.mark.asyncio
async def test_mongo_save_and_find(db_collection):
    # Arrange
    repo = MongoGroupRepository(db_collection)
    group = Group(
        chat_id=999,
        title="Integration Group",
        owner_id=111,
        invite_link="https://t.me/test",
        language="es",
        settings=LinkSettings(require_approval=True)
    )

    # Act
    await repo.save(group)
    found_group = await repo.find_by_id(999)

    # Assert
    assert found_group is not None
    assert found_group.title == "Integration Group"
    assert found_group.language == "es"
    assert found_group.settings.require_approval is True