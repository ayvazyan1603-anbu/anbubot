import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

COLOR_INFO = 0x2b2d31      
COLOR_SUCCESS = 0x00ff00   
COLOR_ERROR = 0xff4747     
COLOR_WARN = 0xffff00    
FOOTER_TEXT = "Разработано ANBU Coding | Bots"

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv("LOG_CHANNEL_ID"))
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID"))
        self.default_role_id = int(os.getenv("DEFAULT_ROLE_ID"))
        self.message_cache = defaultdict(lambda: None)

    def create_log_embed(self, title, color, user=None):
        embed = disnake.Embed(title=title, color=color, timestamp=disnake.utils.utcnow())
        if user:
            embed.set_author(name=f"Объект: {user.name}", icon_url=user.display_avatar.url)
        embed.set_footer(text=FOOTER_TEXT, icon_url=self.bot.user.display_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = member.guild.get_role(self.default_role_id)
        if role:
            await member.add_roles(role)
        
        welcome_ch = self.bot.get_channel(self.welcome_channel_id)
        if welcome_ch:
            embed = disnake.Embed(
                title="[ СИСТЕМА : НОВЫЙ ДОСТУП ] 👤",
                description="**Добро пожаловать в `ANBU Coding`!**\n\nИзучите <#1204473623943970866> и приступайте к работе.",
                color=0xffffff,
                timestamp=disnake.utils.utcnow()
            )
            embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
            embed.set_footer(text="Система ANBU • Автоматизация", icon_url=self.bot.user.display_avatar.url)
            await welcome_ch.send(f"|| {member.mention} ||", embed=embed)

        log_ch = self.bot.get_channel(self.log_channel_id)
        if log_ch:
            embed = self.create_log_embed("[ ЛОГ : ПРИБЫТИЕ ] 📥", COLOR_SUCCESS, member)
            embed.add_field(name="Аккаунт", value=member.mention, inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_ch = self.bot.get_channel(self.log_channel_id)
        if log_ch:
            embed = self.create_log_embed("[ ЛОГ : УБЫТИЕ ] 📤", COLOR_ERROR, member)
            embed.add_field(name="Аккаунт", value=f"{member.name}#{member.discriminator}", inline=True)
            embed.add_field(name="Статус", value="Покинул сервер", inline=True)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        log_ch = self.bot.get_channel(self.log_channel_id)
        if not log_ch:
            return

        content = message.content or "*(Вложения или Embed)*"
        embed = self.create_log_embed("[ ЛОГ : УДАЛЕНИЕ ДАННЫХ ] 🗑️", COLOR_ERROR, message.author)
        embed.add_field(name="Источник", value=message.channel.mention, inline=True)
        embed.add_field(name="Автор", value=message.author.mention, inline=True)
        embed.add_field(name="Содержимое", value=f"```\n{content}```", inline=False)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        log_ch = self.bot.get_channel(self.log_channel_id)
        if not log_ch: 
            return

        embed = self.create_log_embed("[ ЛОГ : ПРАВКА ДАННЫХ ] 📝", COLOR_WARN, before.author)
        embed.add_field(name="Канал", value=before.channel.mention, inline=True)
        embed.add_field(name="Переход", value=f"[К сообщению]({after.jump_url})", inline=True)
        embed.add_field(name="Было", value=f"```\n{before.content}```", inline=False)
        embed.add_field(name="Стало", value=f"```\n{after.content}```", inline=False)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles: 
            return

        log_ch = self.bot.get_channel(self.log_channel_id)
        if not log_ch: 
            return

        added = [role for role in after.roles if role not in before.roles]
        removed = [role for role in before.roles if role not in after.roles]

        for role in added:
            embed = self.create_log_embed("[ ЛОГ : РОЛЬ ВЫДАНА ] 🔐", COLOR_SUCCESS, after)
            embed.add_field(name="Объект", value=after.mention, inline=True)
            embed.add_field(name="Роль", value=role.mention, inline=True)
            await log_ch.send(embed=embed)

        for role in removed:
            embed = self.create_log_embed("[ ЛОГ : РОЛЬ СНЯТА ] 🔓", COLOR_ERROR, after)
            embed.add_field(name="Объект", value=after.mention, inline=True)
            embed.add_field(name="Роль", value=role.mention, inline=True)
            await log_ch.send(embed=embed)

def setup(bot):
    bot.add_cog(Logging(bot))