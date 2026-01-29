import disnake
from disnake.ext import commands
import json
import os
import random
import datetime

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "levels.json"
        self.users = self.load_data()
        self.cooldowns = {} 

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.users, f, indent=4)

    def get_next_lvl_xp(self, level):
        xp = 100
        for _ in range(level):
            xp = int(xp * 1.25)
        return xp

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        if user_id in self.cooldowns:
            if (message.created_at.timestamp() - self.cooldowns[user_id]) < 3:
                return

        if user_id not in self.users:
            self.users[user_id] = {"xp": 0, "level": 0}

        xp_gain = random.randint(5, 10)
        self.users[user_id]["xp"] += xp_gain
        self.cooldowns[user_id] = message.created_at.timestamp()

        current_xp = self.users[user_id]["xp"]
        current_lvl = self.users[user_id]["level"]
        xp_needed = self.get_next_lvl_xp(current_lvl)

        if current_xp >= xp_needed:
            self.users[user_id]["level"] += 1
            self.users[user_id]["xp"] = current_xp - xp_needed
            try:
                emb = disnake.Embed(
                    title="🆙 Новый уровень!",
                    description=f"{message.author.mention}, поздравляем! Вы достигли **{self.users[user_id]['level']}** уровня!",
                    color=0x2b2d31
                )
                emb.set_footer(text="Разработано ANBU Coding | Bots")
                await message.channel.send(embed=emb, delete_after=15)
            except:
                pass
    @commands.command(name="rang", aliases=["rank"])
    async def rank(self, ctx, member: disnake.Member = None):
        member = member or ctx.author
        user_id = str(member.id)

        lvl = self.users[user_id]["level"]
        current_xp = self.users[user_id]["xp"]
        needed_xp = self.get_next_lvl_xp(lvl)
        percentage = int((current_xp / needed_xp) * 10)
        progress_bar = "🟩" * percentage + "⬜" * (10 - percentage)

        emb = disnake.Embed(
            title=f"[ УРОВЕНЬ : РАНГ ]",
            color=0x2b2d31,
            timestamp=datetime.datetime.now()
        )
        
        emb.set_thumbnail(url=member.display_avatar.url)
        emb.set_author(name=f"Запрос от {ctx.author.display_name}")
        emb.add_field(name="Уровень", value=f"**{lvl}**", inline=True)
        emb.add_field(name="Опыт", value=f"**{current_xp} / {needed_xp}**", inline=True)
        emb.add_field(
            name=f"Прогресс ({int((current_xp/needed_xp)*100)}%)", 
            value=f"{progress_bar}", 
            inline=False
        )
        emb.set_footer(text="Разработано ANBU Coding | Bots", icon_url=ctx.bot.user.display_avatar.url)
        await ctx.send(embed=emb)




    @commands.command(name="top", aliases=["leaderboard", "lb"])
    async def leaderboard(self, ctx):
        """Показать таблицу лидеров по уровню"""
        if not self.users:
            return await ctx.send("Таблица лидеров пока пуста.")
        sorted_users = sorted(
            self.users.items(), 
            key=lambda x: (x[1]['level'], x[1]['xp']), 
            reverse=True
        )

        emb = disnake.Embed(
            title="🏆 Таблица лидеров чата",
            description="Топ-10 самых активных участников сервера\n",
            color=0x2b2d31,
            timestamp=datetime.datetime.now()
        )

        for index, (user_id, data) in enumerate(sorted_users[:10], start=1):
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"ID: {user_id}"
            medal = ""
            if index == 1: medal = "🥇"
            elif index == 2: medal = "🥈"
            elif index == 3: medal = "🥉"
            else: medal = f"**{index}.**"

            emb.add_field(
                name=f"{medal} {name}",
                value=f"Уровень: **{data['level']}** | Опыт: **{data['xp']}**",
                inline=False
            )

        emb.set_footer(text="Разработано ANBU Coding | Bots")
        if ctx.guild.icon:
            emb.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.send(embed=emb)

        self.save_data()

def setup(bot):
    bot.add_cog(Levels(bot))