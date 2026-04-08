from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest
from src.Domain.Entity.Group import Group
from src.Domain.ValueObject.LinkSettings import LinkSettings
from src.Domain.Repository.GroupRepository import GroupRepository


class RegisterGroup:
    """Orchestrates the logic to register a new group in the system."""

    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def execute(self, request: RegisterGroupRequest) -> Group:
        existing_group = await self.repository.find_by_id(request.chat_id)

        if existing_group:
            # Update critical fields including language if they re-register
            existing_group.title = request.title
            existing_group.invite_link = request.invite_link
            existing_group.member_count = request.member_count
            existing_group.language = request.language

            await self.repository.save(existing_group)
            return existing_group

        settings = LinkSettings(require_approval=request.require_approval)

        new_group = Group(
            chat_id=request.chat_id,
            title=request.title,
            owner_id=request.owner_id,
            invite_link=request.invite_link,
            chat_type=request.chat_type,
            settings=settings,
            language=request.language,  # Persisting the language choice
            member_count=request.member_count
        )

        await self.repository.save(new_group)
        return new_group