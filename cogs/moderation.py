import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
COLOR_INFO = 0x2B2D31
COLOR_CRITICAL = 0xFF4747
FOOTER_TEXT = "ANBU Coding | Bots"


class ReportButtons(disnake.ui.View):
    def __init__(self, author, reason, channel_origin, report_channel):
        super().__init__(timeout=60)
        self.author = author
        self.reason = reason
        self.channel_origin = channel_origin
        self.report_channel = report_channel

    @disnake.ui.button(label="Вызвать модератора", style=disnake.ButtonStyle.red, emoji="🛡️")
    async def call_mod(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author.id:
            return await interaction.send("Это не ваш запрос.", ephemeral=True)
        
        role_id = int(os.getenv("MOD_ROLE_ID"))
        await self.send_report(interaction, "Модерация", f"<@&{role_id}>")

    @disnake.ui.button(label="Вызвать менеджера", style=disnake.ButtonStyle.blurple, emoji="👨‍💻")
    async def call_manager(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.author.id:
            return await interaction.send("Это не ваш запрос.", ephemeral=True)
            
        role_id = int(os.getenv("DEFAULT_ROLE_ID"))
        await self.send_report(interaction, "Менеджмент", f"<@&{role_id}>")

    async def send_report(self, interaction, department, role_mention):
        embed = disnake.Embed(title="[ СИГНАЛ : ТРЕВОГА ] 🚨", color=COLOR_CRITICAL)
        embed.set_author(name=f"От: {self.author.display_name}", icon_url=self.author.display_avatar.url)
        embed.add_field(name="Отдел", value=department, inline=True)
        embed.add_field(name="Источник", value=self.channel_origin.mention, inline=True)
        embed.add_field(name="Суть обращения", value=f"```\n{self.reason}```", inline=False)
        embed.set_footer(text=FOOTER_TEXT, icon_url=interaction.bot.user.display_avatar.url)
        
        await self.report_channel.send(content=role_mention, embed=embed)
        await interaction.response.edit_message(content="✅ **Запрос успешно передан в штаб ANBU.**", embed=None, view=None)
        self.stop()

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mod_role_id = int(os.getenv("MOD_ROLE_ID"))
        self.muted_role_id = int(os.getenv("MUTED_ROLE_ID"))
        self.warns = {}

    def has_mod_role():
        async def predicate(ctx):
            mod_role = disnake.utils.get(ctx.guild.roles, id=int(os.getenv("MOD_ROLE_ID")))
            return mod_role in ctx.author.roles
        return commands.check(predicate)

    def create_anbu_embed(self, title, color, member=None):
        embed = disnake.Embed(title=title, color=color, timestamp=disnake.utils.utcnow())
        if member:
            embed.set_author(name=f"Объект: {member.display_name if hasattr(member, 'display_name') else member}", 
                             icon_url=member.display_avatar.url if hasattr(member, 'display_avatar') else None)
        embed.set_footer(text=FOOTER_TEXT, icon_url=self.bot.user.display_avatar.url)
        return embed

    @commands.command()
    @has_mod_role()
    async def mute(self, ctx, member: disnake.Member, time: int = None, *, reason="Нарушение протокола"):
        role = ctx.guild.get_role(self.muted_role_id)
        if not role: 
            return await ctx.send("Роль мута не найдена.")
        await member.add_roles(role, reason=reason)
        
        embed = self.create_anbu_embed("[ СТАТУС : ИЗОЛЯЦИЯ ] 🔇", COLOR_CRITICAL, member)
        embed.add_field(name="Исполнитель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Срок", value=f"{time} мин." if time else "Бессрочно", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_thumbnail(url="https://i.imgur.com/7S8fS9S.png")
        await ctx.send(embed=embed)

        if time:
            await asyncio.sleep(time * 60)
            if role in member.roles:
                await member.remove_roles(role)
                u_embed = self.create_anbu_embed("[ СТАТУС : ДОСТУП ВОССТАНОВЛЕН ] 🔊", disnake.Color.green(), member)
                u_embed.description = "Автоматическая деактивация режима изоляции."
                await ctx.send(embed=u_embed)

    @commands.command()
    @has_mod_role()
    async def unmute(self, ctx, member: disnake.Member):
        role = ctx.guild.get_role(self.muted_role_id)
        if role not in member.roles: 
            return await ctx.send("Объект не в муте.")
        await member.remove_roles(role)
        embed = self.create_anbu_embed("[ СТАТУС : ДОСТУП ВОССТАНОВЛЕН ] 🔊", disnake.Color.green(), member)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @has_mod_role()
    async def kick(self, ctx, member: disnake.Member, *, reason="Нарушение"):
        embed = self.create_anbu_embed("[ СТАТУС : ИЗГНАНИЕ ] 👢", disnake.Color.orange(), member)
        embed.add_field(name="Исполнитель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await member.kick(reason=reason)
        await ctx.send(embed=embed)

    @commands.command()
    @has_mod_role()
    async def ban(self, ctx, member: disnake.Member, *, reason="Критическое нарушение"):
        embed = self.create_anbu_embed("[ СТАТУС : ЛИКВИДАЦИЯ ] 🔨", COLOR_CRITICAL, member)
        embed.add_field(name="Исполнитель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.set_thumbnail(url="https://i.imgur.com/r8kX9Xz.png")
        await member.ban(reason=reason)
        await ctx.send(embed=embed)

    @commands.command()
    @has_mod_role()
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        
        embed = self.create_anbu_embed("[ СТАТУС : ПОМИЛОВАНИЕ ] 🔓", disnake.Color.green())
        embed.add_field(name="Пользователь", value=f"{user} (`{user.id}`)", inline=True)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        embed.add_field(name="Инструкция", value="Объект исключен из черного списка системы.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @has_mod_role()
    async def warn(self, ctx, member: disnake.Member, *, reason="Предупреждение"):
        self.warns[member.id] = self.warns.get(member.id, 0) + 1
        count, limit = self.warns[member.id], int(os.getenv("WARN_LIMIT", 3))

        embed = self.create_anbu_embed("[ СТАТУС : ПРЕДУПРЕЖДЕНИЕ ] ⚠️", disnake.Color.orange(), member)
        embed.add_field(name="Прогресс", value=f"`{count} / {limit}`", inline=True)
        embed.add_field(name="Исполнитель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await ctx.send(embed=embed)

        if count >= limit:
            self.warns[member.id] = 0
            role = ctx.guild.get_role(self.muted_role_id)
            if role:
                await member.add_roles(role)
                a_embed = self.create_anbu_embed("[ СТАТУС : АВТО-БЛОКИРОВКА ] 🚫", COLOR_CRITICAL, member)
                a_embed.description = "Превышение лимита. Объект изолирован."
                await ctx.send(embed=a_embed)

    @commands.command()
    async def report(self, ctx, *, reason):
        channel = self.bot.get_channel(1204473623943970867)
        if not channel: 
            return await ctx.send("Ошибка связи.")
        
        embed = disnake.Embed(title="[ СИСТЕМА : ОБРАТНАЯ СВЯЗЬ ] 📩", color=COLOR_INFO)
        embed.description = f"Создание отчета по факту: `{reason}`\n\n**Выберите отдел:**"
        embed.set_footer(text=FOOTER_TEXT, icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed, view=ReportButtons(ctx.author, reason, ctx.channel, channel))

def setup(bot):
    bot.add_cog(Moderation(bot))