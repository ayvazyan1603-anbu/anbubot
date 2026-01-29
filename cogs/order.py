import disnake
from disnake.ext import commands
import asyncio
import datetime
import random
import string
import os
import json

ADMIN_ROLE_ID = 1155448625057497130
LOGS_CHANNEL_ID = 1204533208797155358

class OrderDetailsModal(disnake.ui.Modal):
    def __init__(self, service, difficulty, budget, cog):
        self.service = service
        self.difficulty = difficulty
        self.budget = budget
        self.cog = cog

        components = [
            disnake.ui.TextInput(
                label="Сроки выполнения",
                placeholder="Например: 1 неделя",
                custom_id="deadline",
                max_length=50
            ),
            disnake.ui.TextInput(
                label="Техническое задание",
                placeholder="Опишите требования подробно...",
                custom_id="requirements",
                style=disnake.TextInputStyle.paragraph,
                max_length=1000
            ),
        ]
        super().__init__(title="Оформление заказа", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        deadline = inter.text_values["deadline"]
        requirements = inter.text_values["requirements"]
        order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        self.cog.orders[order_id] = {
            "client_id": inter.author.id,
            "service": self.service,
            "difficulty": self.difficulty,
            "budget": self.budget,
            "deadline": deadline,
            "status": "🟡 Pending",
            "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        self.cog.save_orders()

        guild = inter.guild
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        
        category = disnake.utils.get(guild.categories, name="ЗАКАЗЫ")
        channel = await guild.create_text_channel(
            name=f"order-{order_id}",
            overwrites=overwrites,
            category=category,
            topic=f"Заказчик: {inter.author.name} | ID: {inter.author.id}"
        )

        emb = disnake.Embed(title=f"📦 Новый заказ: #{order_id}", color=0x2b2d31, timestamp=datetime.datetime.now())
        emb.add_field(name="👤 Клиент", value=inter.author.mention, inline=True)
        emb.add_field(name="🛠 Услуга", value=f"{self.service}", inline=True)
        emb.add_field(name="📈 Сложность", value=self.difficulty, inline=True)
        emb.add_field(name="💰 Бюджет", value=f"`{self.budget}`", inline=True)
        emb.add_field(name="⏳ Сроки", value=deadline, inline=True)
        emb.add_field(name="📊 Статус", value="🟡 **Pending**", inline=True)
        emb.add_field(name="📝 ТЗ", value=f"```\n{requirements}\n```", inline=False)
        emb.set_footer(text=f"Order ID: {order_id} | {self.cog.footer_text}")
        
        await channel.send(embed=emb, view=OrderManagementView(self.cog))
        await inter.response.send_message(f"✅ Заказ создан! Канал: {channel.mention}", ephemeral=True)

class OrderManagementView(disnake.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def change_status(self, inter, status_text, color):
        is_admin = inter.author.get_role(ADMIN_ROLE_ID) or inter.author.guild_permissions.administrator
        if not is_admin:
            return await inter.response.send_message("У вас нет прав!", ephemeral=True)
            
        order_id = inter.channel.name.replace("order-", "").upper()
        if order_id in self.cog.orders:
            self.cog.orders[order_id]["status"] = status_text
            self.cog.save_orders()

        emb = inter.message.embeds[0]
        emb.color = color
        for i, field in enumerate(emb.fields):
            if "Статус" in field.name:
                emb.set_field_at(i, name="📊 Статус", value=status_text, inline=True)
                break
        await inter.response.edit_message(embed=emb)

    @disnake.ui.button(label="Discussion", style=disnake.ButtonStyle.blurple, custom_id="st_disc")
    async def st_disc(self, btn, inter): await self.change_status(inter, "🔵 **In Discussion**", 0x3498db)

    @disnake.ui.button(label="In Progress", style=disnake.ButtonStyle.secondary, custom_id="st_prog")
    async def st_prog(self, btn, inter): await self.change_status(inter, "🟣 **In Progress**", 0x9b59b6)

    @disnake.ui.button(label="Completed", style=disnake.ButtonStyle.green, custom_id="st_comp")
    async def st_comp(self, btn, inter): await self.change_status(inter, "🟢 **Completed**", 0x2ecc71)

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red, custom_id="st_canc")
    async def st_canc(self, btn, inter): await self.change_status(inter, "🔴 **Cancelled**", 0xe74c3c)

class OrderCreateView(disnake.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.service = None
        self.difficulty = None

    @disnake.ui.select(
        placeholder="1. Выберите услугу",
        options=[
            disnake.SelectOption(label="Discord-бот", emoji="🤖"),
            disnake.SelectOption(label="Telegram-бот", emoji="📱"),
            disnake.SelectOption(label="Веб-сайт", emoji="🌐"),
            disnake.SelectOption(label="Дизайн", emoji="🎨"),
            disnake.SelectOption(label="3D-моделирование", emoji="🧱"),
        ]
    )
    async def select_service(self, select: disnake.ui.Select, inter: disnake.MessageInteraction):
        self.service = select.values[0]
        
        self.clear_items()
        diff_select = disnake.ui.Select(
            placeholder="2. Выберите сложность",
            options=[
                disnake.SelectOption(label="Базовый"),
                disnake.SelectOption(label="Средний"),
                disnake.SelectOption(label="Продвинутый"),
            ]
        )

        async def diff_cb(i: disnake.MessageInteraction):
            self.difficulty = diff_select.values[0]
            await i.response.send_modal(
                OrderDetailsModal(self.service, self.difficulty, "Не указан", self.cog)
            )

        diff_select.callback = diff_cb
        self.add_item(diff_select)
        await inter.response.edit_message(
            content=f"Выбрана услуга: **{self.service}**\nТеперь укажите сложность проекта:", 
            view=self
        )
class Orders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_file = "orders.json"
        self.footer_text = "ANBU Coding | Bots"
        self.orders = self.load_orders()

    def load_orders(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: 
                return {}
        return {}

    def save_orders(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.orders, f, ensure_ascii=False, indent=4)

    @commands.slash_command(name="order")
    async def order_group(self, inter): pass


    @order_group.sub_command(name="create", description="Создать новый заказ")
    async def order_create(self, inter):
        await inter.response.send_message("Оформление заказа:", view=OrderCreateView(self), ephemeral=True)

    @order_group.sub_command(name="history", description="История заказов")
    async def order_history(self, inter, 
                            member: disnake.Member = None, 
                            status: str = commands.Param(None, choices=["Pending", "Discussion", "In Progress", "Completed", "Cancelled"]),
                            service: str = commands.Param(None, choices=["Discord-бот", "Telegram-бот", "Веб-сайт", "Дизайн", "3D-моделирование"])):
        
        is_admin = inter.author.get_role(ADMIN_ROLE_ID) or inter.author.guild_permissions.administrator
        search_id = (member.id if member else inter.author.id) if is_admin else inter.author.id

        emb = disnake.Embed(title="📋 История заказов", color=0x2b2d31)
        count = 0
        for oid, data in self.orders.items():
            if data["client_id"] == search_id:
                if status and status not in data["status"]: continue
                if service and data["service"] != service: continue
                
                emb.add_field(
                    name=f"Заказ #{oid}",
                    value=f"**Услуга:** {data['service']}\n**Статус:** {data['status']}\n**Дата:** {data['date']}",
                    inline=True
                )
                count += 1
                if count >= 24: break

        if count == 0: return await inter.response.send_message("Заказы не найдены.", ephemeral=True)
        await inter.response.send_message(embed=emb, ephemeral=True)

    @order_group.sub_command(name="close", description="Закрыть тикет")
    async def order_close(self, inter):
        if not (inter.author.get_role(ADMIN_ROLE_ID) or inter.author.guild_permissions.administrator):
            return await inter.response.send_message("Нет прав!", ephemeral=True)
        if "order-" in inter.channel.name:
            await inter.response.send_message("Удаление...")
            await asyncio.sleep(3)
            await inter.channel.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(OrderManagementView(self))

def setup(bot):
    bot.add_cog(Orders(bot))
    