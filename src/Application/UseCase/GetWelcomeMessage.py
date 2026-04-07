class GetWelcomeMessage:
    """Logic to generate the welcome text and instructions."""

    async def execute(self, user_full_name: str) -> str:
        return (
            f"Hello, {user_full_name}! 👋\n\n"
            "I am **NexusBot**, the bridge between Telegram communities.\n\n"
            "**What can I do for you?**\n"
            "• 📢 **Auto-Share:** I share your group link in a network of partner groups every day.\n"
            "• 📈 **Growth:** Get more members and detailed join-request metrics.\n\n"
            "**How to start?**\n"
            "1. Add me to your group as an **Administrator**.\n"
            "2. Give me the 'Invite Users via Link' permission.\n"
            "3. I will message you here to complete the setup!"
        )