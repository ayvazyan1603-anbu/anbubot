import disnake
from disnake.ext import commands
import json
import os
import random

DB_PATH = "economy.json"
PHRASES_PATH = "phrases.json"
SHOP_PATH = "shop.json"
ADMIN_ROLE_ID = 1218632775859572736

ROLE_REWARDS = {
    "default": 200            
}



class BlackjackView(disnake.ui.View):
    def __init__(self, ctx, bet, economy):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bet = bet
        self.economy = economy
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4

    def draw_card(self):
        return random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])

    def get_score(self, hand):
        score = sum(hand)
        if score > 21 and 11 in hand:
            hand[hand.index(11)] = 1
            return sum(hand)
        return score

    def create_embed(self, title="[ КАЗИНО : БЛЕКДЖЕК ] 🃏", color=0x2b2d31, finished=False):
        p_score = self.get_score(self.player_hand)
        d_score = self.get_score(self.dealer_hand)
        
        dealer_display = ", ".join(map(str, self.dealer_hand)) if finished else f"{self.dealer_hand[0]}, ??"
        
        embed = disnake.Embed(title=title, color=color)
        embed.set_author(name=f"Игра {self.ctx.author.display_name}", icon_url=self.ctx.author.display_avatar.url)
        embed.add_field(name="Ваши карты", value=f"Рука: `{', '.join(map(str, self.player_hand))}`\nСчет: `{p_score}`", inline=True)
        embed.add_field(name="Карты дилера", value=f"Рука: `{dealer_display}`\nСчет: `{d_score if finished else '??'}`", inline=True)
        embed.set_footer(text=f"Ставка: {self.bet} 💵", icon_url=self.ctx.bot.user.display_avatar.url)
        return embed

    @disnake.ui.button(label="Взять", style=disnake.ButtonStyle.grey, emoji="➕")
    async def hit(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.ctx.author.id: return
        
        self.player_hand.append(self.draw_card())
        score = self.get_score(self.player_hand)
        
        if score > 21:
            self.stop()
            await interaction.response.edit_message(embed=self.create_embed("💥 ПЕРЕБОР! ВЫ ПРОИГРАЛИ", 0xff4747, True), view=None)
        else:
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @disnake.ui.button(label="Стоп", style=disnake.ButtonStyle.blurple, emoji="✋")
    async def stand(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.ctx.author.id:
            return await interaction.send("Это не ваша игра!", ephemeral=True)
        self.stop()
        is_lucky_game = random.random() < 0.6
        
        while self.get_score(self.dealer_hand) < 17:
            if is_lucky_game and self.get_score(self.dealer_hand) > self.get_score(self.player_hand):
                break
            self.dealer_hand.append(self.draw_card())

        p_score = self.get_score(self.player_hand)
        d_score = self.get_score(self.dealer_hand)

        if d_score > 21 or p_score > d_score:
            result_title = "ВЫ ВЫИГРАЛИ!"
            color = 0x00ff00
            self.economy.add_money(self.ctx.author.id, self.bet * 2)
        elif p_score == d_score:
            result_title = "НИЧЬЯ (Возврат)"
            color = 0xffff00
            self.economy.add_money(self.ctx.author.id, self.bet)
        else:
            result_title = "ДИЛЕР ПОБЕДИЛ"
            color = 0xff4747

        await interaction.response.edit_message(embed=self.create_embed(result_title, color, True), view=None)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DB_PATH): return {}
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_data(self):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_user_data(self, user_id):
        uid = str(user_id)
        
        if uid not in self.data:
            self.data[uid] = {"balance": 0, "inventory": []}
            return self.data[uid]
    
        if isinstance(self.data[uid], int):
            old_balance = self.data[uid]
            self.data[uid] = {
                "balance": old_balance,
                "inventory": []
            }
            self.save_data()
            
        return self.data[uid]

    def get_balance(self, user_id):
        return self.get_user_data(user_id)["balance"]

    def add_money(self, user_id, amount):
        uid = str(user_id)
        user = self.get_user_data(uid)
        user["balance"] += amount
        self.save_data()

    def load_shop(self):
        if not os.path.exists(SHOP_PATH): return []
        with open(SHOP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


    def get_random_phrase(self, category):
        if not os.path.exists(PHRASES_PATH):
            return "Действие выполнено успешно!"
        with open(PHRASES_PATH, "r", encoding="utf-8") as f:
            phrases = json.load(f)
            return random.choice(phrases.get(category, ["Успех!"]))
        

    def save_shop(self, data):
        with open(SHOP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    @commands.command(name="eco-leaderboard", aliases=["ecotop", "ecolb"])
    async def ecoleaderboard(self, ctx):
        """Просмотр самых богатых пользователей сервера."""
        # Получаем данные и фильтруем их (на случай, если в базе есть странные записи)
        # Сортируем по балансу в обратном порядке (от большего к меньшему)
        sorted_users = sorted(
            self.data.items(), 
            key=lambda item: item[1].get("balance", 0) if isinstance(item[1], dict) else 0, 
            reverse=True
        )

        embed = disnake.Embed(
            title="[ ЭКОНОМИКА : СПИСОК ЛИДЕРОВ ] 🏆",
            color=0x2b2d31,
            description="Топ-10 самых богатых пользователей сервера\n\n"
        )

        top_limit = 10
        count = 0
        
        for user_id, user_data in sorted_users:
            if count >= top_limit:
                break
                
            # Пытаемся найти пользователя на сервере, чтобы отобразить его имя
            member = ctx.guild.get_member(int(user_id))
            if member:
                name = member.display_name
            else:
                # Если пользователя нет на сервере, пишем "Ушедший пользователь"
                name = f"User({user_id})"
            
            balance = user_data.get("balance", 0)
            
            # Добавляем медальки для топ-3
            medal = ""
            if count == 0: medal = "🥇 "
            elif count == 1: medal = "🥈 "
            elif count == 2: medal = "🥉 "
            else: medal = f"**{count + 1}.** "

            embed.description += f"{medal} {name} — `{balance} 💵`\n"
            count += 1

        if count == 0:
            embed.description = "Список пуст."

        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy(self, ctx, item_number: int):
        shop = self.load_shop()
        user = self.get_user_data(ctx.author.id)
        
        if item_number < 1 or item_number > len(shop):
            return await ctx.send("❌ Товара с таким номером не существует!")
        
        item = shop[item_number - 1]
        item_name = item["name"]
        item_price = item["price"]

        if user["balance"] < item_price:
            return await ctx.send(f"❌ Недостаточно средств! Вам нужно еще `{item_price - user['balance']} 💵`")

        user["balance"] -= item_price
        user["inventory"].append(item_name)
        self.save_data()

        embed = disnake.Embed(
            title="[ МАГАЗИН : ПОКУПКА ] ✅",
            description=f"Вы успешно приобрели **{item_name}**!",
            color=0x2b2d31
        )
        embed.add_field(name="Списано", value=f"`{item_price} 💵`", inline=True)
        embed.add_field(name="Ваш баланс", value=f"`{user['balance']} 💵`", inline=True)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="inventory", aliases=["inv", "items"])
    async def inventory(self, ctx, member: disnake.Member = None):
        target = member or ctx.author
        user = self.get_user_data(target.id)
        inventory = user.get("inventory", [])

        embed = disnake.Embed(
            title=f"[ ИНВЕНТАРЬ : {target.display_name} ] 🎒",
            color=0x2b2d31
        )

        if not inventory:
            embed.description = "Инвентарь пуст."
        else:
            items_list = "\n".join([f"• {name}" for name in inventory])
            embed.description = items_list

        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="shop")
    async def shop(self, ctx):
        items = self.load_shop()
        
        embed = disnake.Embed(
            title="[ МАГАЗИН : ТОВАРЫ ] 🛒",
            color=0x2b2d31,
            description="Используйте `.buy [номер]`, чтобы купить товар (скоро добавим)."
        )

        if not items:
            embed.description = "В магазине пока нет товаров."
        else:
            for i, item in enumerate(items, 1):
                embed.add_field(
                    name=f"{i}. {item['name']} — {item['price']} 💵",
                    value=f"*{item['description']}*",
                    inline=False
                )
        
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.slash_command(name="additem", description="Добавить новый предмет в магазин (Только для Админов)")
    async def additem(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        name: str, 
        price: int, 
        description: str
    ):
        if not any(role.id == ADMIN_ROLE_ID for role in inter.author.roles):
            return await inter.response.send_message("У вас недостаточно прав для этой команды!", ephemeral=True)

        if price < 0:
            return await inter.response.send_message("Цена не может быть отрицательной!", ephemeral=True)

        shop_data = self.load_shop()
        new_item = {
            "name": name,
            "price": price,
            "description": description
        }
        shop_data.append(new_item)
        self.save_shop(shop_data)

        embed = disnake.Embed(
            title="[ МАГАЗИН : ОБНОВЛЕНИЕ ] ✅",
            description=f"Предмет **{name}** успешно добавлен в магазин.",
            color=0x2b2d31
        )
        embed.add_field(name="Цена", value=f"{price} 💵", inline=True)
        embed.set_footer(text="Разработано ANBU Coding | Bots")
        
        await inter.response.send_message(embed=embed)

    @commands.command(name="work")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def work(self, ctx):
        user_id = str(ctx.author.id)
        reward = random.randint(100, 200)
        self.add_money(user_id, reward)
        
        message = self.get_random_phrase("work_messages")
        
        embed = disnake.Embed(
            title="[ СТАТУС : РАБОТА ] ⚒️",
            description=f"{message}",
            color=0x2b2d31
        )
        embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Заработок", value=f"`{reward} 💵`", inline=True)
        embed.add_field(name="Баланс", value=f"`{self.get_balance(user_id)} 💵`", inline=True)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="crime")
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def crime(self, ctx):
        user_id = str(ctx.author.id)
        current_balance = self.get_balance(user_id)
        
        if random.random() < 0.4:
            lost_money = int(current_balance * 0.5)
            self.add_money(user_id, -lost_money)
            
            embed = disnake.Embed(
                title="[ СТАТУС : ПРОВАЛ ] 🚨",
                description="Вас поймала полиция при попытке совершить преступление!",
                color=0xff4747
            )
            embed.add_field(name="Штраф", value=f"`-{lost_money} 💵`", inline=True)
            embed.add_field(name="Остаток", value=f"`{self.get_balance(user_id)} 💵`", inline=True)
            embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
            
            return await ctx.send(embed=embed)

        reward = random.randint(200, 500)
        self.add_money(user_id, reward)
        
        message = self.get_random_phrase("crime_messages")
        
        embed = disnake.Embed(
            title="[ СТАТУС : КРИМИНАЛ ] 🔫",
            description=f"{message}",
            color=0x2b2d31
        )
        embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Добыча", value=f"`{reward} 💵`", inline=True)
        embed.add_field(name="Баланс", value=f"`{self.get_balance(user_id)} 💵`", inline=True)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="collect")
    @commands.cooldown(1, 14400, commands.BucketType.user)
    async def collect(self, ctx):
        user_id = str(ctx.author.id)
        reward = ROLE_REWARDS["default"]
        user_roles_ids = [role.id for role in ctx.author.roles]
        for role_id, amount in ROLE_REWARDS.items():
            if role_id in user_roles_ids:
                reward = amount
                break
        self.add_money(user_id, reward)
        new_balance = self.get_balance(user_id)

        embed = disnake.Embed(
            title="[ ЭКОНОМИКА : ПОЛУЧЕНИЕ ] 💰",
            description=f"Вы успешно получили ежедневную награду!",
            color=0x2b2d31
        )
        embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Сумма", value=f"`{reward}$`", inline=True)
        embed.add_field(name="Ваш баланс", value=f"`{new_balance}$`", inline=True)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)



    @commands.command(name="balance", aliases=["money", "bal"])
    async def balance(self, ctx, member: disnake.Member = None):
        target = member or ctx.author
        user_id = str(target.id)
        
        amount = self.get_balance(user_id)

        embed = disnake.Embed(
            title="[ СТАТУС : ИНФОРМАЦИЯ ] 💳",
            color=0x2b2d31
        )
        
        if target == ctx.author:
            description = f"Ваш текущий баланс составляет: `{amount} 💵`"
        else:
            description = f"Баланс пользователя {target.mention} составляет: `{amount} 💵`"
            
        embed.description = description
        embed.set_author(name=f"Запрос от {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Разработано ANBU Coding | Bots", icon_url=self.bot.user.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="bj", aliases=["blackjack"])
    async def blackjack(self, ctx, bet: int):
        economy = self.bot.get_cog("Economy")
        if not economy: return await ctx.send("Модуль экономики не найден.")
        
        if bet <= 0: return await ctx.send("Ставка должна быть больше 0!")
        if economy.get_balance(ctx.author.id) < bet:
            return await ctx.send("У вас недостаточно денег!")

        economy.add_money(ctx.author.id, -bet)
        view = BlackjackView(ctx, bet, economy)
        await ctx.send(embed=view.create_embed(), view=view)





    

def setup(bot):
    bot.add_cog(Economy(bot))
    
    
    