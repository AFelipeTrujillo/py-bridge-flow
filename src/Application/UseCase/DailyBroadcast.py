class DailyBroadcast:
    def __init__(self, group_repo):
        self.group_repo = group_repo

    def _format_count(self, count: int) -> str:
        if count < 1000: return str(count)
        if count < 10000: return f"+{count / 1000:.1f}K"
        return f"+{int(count / 1000)}K"

    async def execute(self, lang: str):

        groups = await self.group_repo.find_all_approved()
        if not groups: return None

        if lang == "es":
            h = "🌟 **¡RESUMEN DIARIO!** 🌟\n_Toca el nombre para unirte_\n\n---\n"
            f = "\n---\n📢 *Canales* | 👥 *Grupos*"
        else:
            h = "🌟 **DAILY SUMMARY!** 🌟\n_Tap the name to join_\n\n---\n"
            f = "\n---\n📢 *Channels* | 👥 *Groups*"  


        body = ""
        for g in groups:
            members = self._format_count(g.member_count)
            icon = "📢" if g.chat_type == "channel" else "👥"
            body += f"🔹 [{g.title}]({g.invite_link})  `{members}`  {icon}\n"

        return h + body + f