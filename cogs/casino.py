import disnake
from disnake.ext import commands
import asyncio
import random



class DiceView(disnake.ui.View):
    def __init__(self, challenger, target, bet, economy_cog):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.target = target
        self.bet = bet
        self.economy = economy_cog

    @disnake.ui.button(label="Принять вызов", style=disnake.ButtonStyle.green, emoji="🎲")
    async def accept_dice(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.target.id:
            return await interaction.send("Этот вызов не для вас!", ephemeral=True)

        if self.economy.get_balance(self.challenger.id) < self.bet:
            return await interaction.send("У автора вызова больше нет денег для игры!", ephemeral=True)
        if self.economy.get_balance(self.target.id) < self.bet:
            return await interaction.send("У вас недостаточно денег для принятия вызова!", ephemeral=True)

        self.stop()
        button.disabled = True
        await interaction.response.edit_message(view=self)

        self.economy.add_money(self.challenger.id, -self.bet)
        self.economy.add_money(self.target.id, -self.bet)

        embed = disnake.Embed(title="[ КАЗИНО : КОСТИ ] 🎲", description="Бросаем кости...", color=0x2b2d31)
        game_msg = await interaction.channel.send(embed=embed)
        
        await asyncio.sleep(1.5)

        roll_1 = random.randint(1, 6)
        roll_2 = random.randint(1, 6)
        
        while roll_1 == roll_2:
            roll_2 = random.randint(1, 6)

        winner = self.challenger if roll_1 > roll_2 else self.target
        prize = self.bet * 2
        self.economy.add_money(winner.id, prize)

        embed.description = (
            f"**{self.challenger.display_name}** выбросил: `{roll_1}`\n"
            f"**{self.target.display_name}** выбросил: `{roll_2}`\n\n"
            f"🏆 Победил {winner.mention} и забрал `{prize} 💵`!"
        )
        embed.color = 0x00ff00
        await game_msg.edit(embed=embed)



class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.symbols = ["🍒", "🍋", "🍇", "🔔", "💎", "💰"]

    @commands.command(name="dice")
    async def dice(self, ctx, member: disnake.Member, bet: int):
        if member.id == ctx.author.id:
            return await ctx.send("Вы не можете играть с самим собой!")
        if member.bot:
            return await ctx.send("Боты не играют в азартные игры!")
        if bet <= 0:
            return await ctx.send("Ставка должна быть больше нуля!")

        economy = self.bot.get_cog("Economy")


        if economy.get_balance(ctx.author.id) < bet:
            return await ctx.send("У вас недостаточно средств для такой ставки!")
        
        if economy.get_balance(member.id) < bet:
            return await ctx.send(f"У {member.display_name} недостаточно денег, чтобы принять этот вызов.")

        embed = disnake.Embed(
            title="[ КАЗИНО : ВЫЗОВ ] 🎲",
            description=f"{member.mention}, пользователь {ctx.author.mention} вызывает вас на игру в кости!\nСтавка: `{bet} 💵`",
            color=0x2b2d31
        )
        embed.set_footer(text="У вас есть 60 секунд на принятие.")
        
        view = DiceView(ctx.author, member, bet, economy)
        await ctx.send(content=member.mention, embed=embed, view=view)

    @commands.command(name="slots")
    async def slots(self, ctx, bet: int):
        economy = self.bot.get_cog("Economy")
        if not economy:
            return await ctx.send("❌ Ошибка: Модуль экономики не загружен!")

        if bet <= 0:
            return await ctx.send("❌ Ставка должна быть больше нуля!")
        
        balance = economy.get_balance(ctx.author.id)
        if balance < bet:
            return await ctx.send(f"❌ Недостаточно средств! Ваш баланс: `{balance} 💵`")
        economy.add_money(ctx.author.id, -bet)

        embed = disnake.Embed(
            title="[ КАЗИНО : СЛОТЫ ] 🎰",
            description=f"Ставка: `{bet} 💵` \n\n**[ ⌛ | ⌛ | ⌛ ]**",
            color=0x2b2d31
        )
        msg = await ctx.send(embed=embed)

        for _ in range(3):
            await asyncio.sleep(0.2)
            s1, s2, s3 = random.choices(self.symbols, k=3)
            embed.description = f"Ставка: `{bet} 💵` \n\n**[ {s1} | {s2} | {s3} ]**"
            await msg.edit(embed=embed)
        res = random.choices(self.symbols, k=3)
        
        multiplier = 0
        if res[0] == res[1] == res[2]:
            multiplier = 5  
        elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
            multiplier = 2  

        reward = bet * multiplier
        
        if multiplier > 0:
            economy.add_money(ctx.author.id, reward) 
            result_text = f"**ПОБЕДА!** Вы получили `{reward} 💵`"
            embed.color = 0x00ff00
        else:
            result_text = "**ПРОИГРЫШ.**"
            embed.color = 0xff4747

        embed.description = f"Ставка: `{bet} 💵` \n\n**[ {res[0]} | {res[1]} | {res[2]} ]**\n\n{result_text}"
        new_balance = economy.get_balance(ctx.author.id)
        embed.set_footer(text=f"Ваш баланс: {new_balance} 💵")
        
        await msg.edit(embed=embed)

def setup(bot):
    bot.add_cog(Casino(bot))