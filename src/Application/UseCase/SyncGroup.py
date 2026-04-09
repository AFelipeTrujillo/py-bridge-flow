class SyncGroup:
    def __init__(self, repository, register_use_case):
        self.repository = repository
        self.register_use_case = register_use_case

    async def execute(self, chat, user_id):
        # 1. Verificar si ya está en la DB
        existing = await self.repository.find_by_id(chat.id)
        if existing and existing.status == "approved":
            return "already_active"

        # 2. El bot debe ser admin para obtener el invite_link
        # Si no puede obtenerlo, es que no tiene permisos
        try:
            invite_link = chat.invite_link
            member_count = 0  # Se puede actualizar luego

            # Usamos la lógica de registro que ya tienes
            await self.register_use_case.execute(
                chat_id=chat.id,
                title=chat.title,
                owner_id=user_id,
                invite_link=invite_link,
                chat_type=chat.type,
                language="es"  # Default
            )
            return "success"
        except Exception:
            return "missing_permissions"