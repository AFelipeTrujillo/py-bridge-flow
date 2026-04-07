import pytest
from unittest.mock import AsyncMock, MagicMock
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest
from src.Domain.Entity.Group import Group


@pytest.mark.asyncio
async def test_register_new_group_success():
    """Test that a group is correctly created if it doesn't exist."""

    # Arrange: Mock the repository
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)
    mock_repo.save = AsyncMock()

    use_case = RegisterGroup(mock_repo)

    request = RegisterGroupRequest(
        chat_id=123,
        title="Test Group",
        owner_id=456,
        invite_link="https://t.me/+link",
        require_approval=True,
        member_count=100,
        language="en"
    )

    # Act
    result = await use_case.execute(request)

    # Assert
    assert isinstance(result, Group)
    assert result.chat_id == 123
    assert result.language == "en"
    assert result.settings.require_approval is True

    # Verify repository was called
    mock_repo.find_by_id.assert_called_once_with(123)
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_existing_group():
    """Test that the Use Case updates the data if the group already exists."""

    # Arrange
    existing_group = MagicMock(spec=Group)
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=existing_group)
    mock_repo.save = AsyncMock()

    use_case = RegisterGroup(mock_repo)

    request = RegisterGroupRequest(
        chat_id=123,
        title="Updated Title",
        owner_id=456,
        invite_link="https://newlink.com",
        require_approval=False,
        member_count=150,
        language="es"
    )

    # Act
    await use_case.execute(request)

    # Assert
    # Check if existing group fields were updated
    assert existing_group.title == "Updated Title"
    assert existing_group.language == "es"
    mock_repo.save.assert_called_once_with(existing_group)