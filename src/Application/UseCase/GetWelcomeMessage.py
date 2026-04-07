class GetWelcomeMessage:
    """Logic to generate the welcome text in multiple languages."""

    def execute(self, user_full_name: str, lang: str = None) -> str:
        messages = {
            "en": (
                f"Hello, {user_full_name}! 👋\n\n"
                "I am **NexusBot**, the bridge between Telegram communities.\n"
                "To register a group, add me as an admin there!"
            ),
            "es": (
                f"¡Hola, {user_full_name}! 👋\n\n"
                "Soy **NexusBot**, el puente entre comunidades de Telegram.\n"
                "Para registrar un grupo, ¡añádeme como admin allí!"
            )
        }

        if lang in messages:
            return messages[lang]

        # Default bilingual message if no language is set
        return (
            f"Hello {user_full_name}! / ¡Hola!\n\n"
            "Please select your language / Por favor selecciona tu idioma:"
        )