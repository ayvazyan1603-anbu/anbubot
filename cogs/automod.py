import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os
import re
from collections import defaultdict

load_dotenv()

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_limit = int(os.getenv("SPAM_LIMIT", 5))
        self.spam_window = int(os.getenv("SPAM_WINDOW", 10))
        self.message_cache = defaultdict(lambda: None)
        self.spam_cache = defaultdict(list)
        self.tg_pattern = re.compile(r'https?://(www\.)?(t\.me|telegram\.me)', re.IGNORECASE)
        self.discord_invite_pattern = re.compile(r'(https?://)?(www\.)?(discord\.(gg|com/invite|me|io|li|plus)/[a-zA-Z0-9\-]+)', re.IGNORECASE)
        self.allowed_discord_invites = set()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        self.message_cache[message.id] = {
            "author": message.author,
            "content": message.content,
            "channel": message.channel
        }

        user_id = message.author.id
        now = message.created_at.timestamp()

        self.spam_cache[user_id].append(message)
        self.spam_cache[user_id] = [
            msg for msg in self.spam_cache[user_id]
            if now - msg.created_at.timestamp() <= self.spam_window
        ]

        if len(self.spam_cache[user_id]) >= self.spam_limit:
            try:
                await message.channel.delete_messages(self.spam_cache[user_id])
            except disnake.HTTPException:
                pass

            try:
                await message.author.send(
                    "Вы слишком быстро отправляете сообщения."
                )
            except disnake.Forbidden:
                pass

            self.spam_cache[user_id].clear()
            return

        if self.tg_pattern.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, ссылки Telegram запрещены.",
                delete_after=5
            )
            return

        matches = self.discord_invite_pattern.findall(message.content)
        if matches:
            found = {m[2].split("/")[-1] for m in matches}
            if not found.issubset(self.allowed_discord_invites):
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, сторонние Discord-инвайты запрещены.",
                    delete_after=5
                )
                return

def setup(bot):
    bot.add_cog(AutoMod(bot))