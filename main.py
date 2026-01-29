import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = disnake.Intents.all()
bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None
)
FOOTER_TEXT = "Разработано ANBU Coding | Bots"

@bot.event
async def on_ready():
    print(f"{bot.user} is ready! | Connected to ANBU Coding | Bots")
    activity = disnake.Activity(
        type=disnake.ActivityType.watching, 
        name="ANBU Coding | Bots"
    )
    await bot.change_presence(status=disnake.Status.online, activity=activity)

@bot.event
async def on_command_error(ctx: commands.Context, error):
    COLOR_INFO = 0x2b2d31
    COLOR_CRITICAL = 0xff4747
    BOT_ICON = bot.user.display_avatar.url

    def create_base_embed(title, color):
        embed = disnake.Embed(title=title, color=color)
        embed.set_author(name=f"Запрос от {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=FOOTER_TEXT, icon_url=BOT_ICON)
        return embed

    if isinstance(error, commands.CommandNotFound):
        embed = create_base_embed("[ СТАТУС : НЕИЗВЕСТНО ] 🔗", COLOR_INFO)
        embed.add_field(name="Причина", value="Вызванная команда не зарегистрирована в системе.", inline=False)
        embed.add_field(name="Инструкция", value=f"Проверьте синтаксис или введите `{ctx.prefix}help`.", inline=False)
        await ctx.reply(embed=embed, delete_after=60)

    elif isinstance(error, commands.MissingPermissions):
        embed = create_base_embed("[ СТАТУС : ОТКАЗАНО ] 🔐", COLOR_CRITICAL)
        perms = ", ".join([f"`{p.replace('_', ' ').title()}`" for p in error.missing_permissions])
        embed.add_field(name="Причина", value="У вас недостаточно прав доступа.", inline=False)
        embed.add_field(name="Требуется", value=perms, inline=True)
        embed.add_field(name="Ваш статус", value="Ограничен", inline=True)
        await ctx.send(embed=embed)

    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_base_embed("[ СТАТУС : ОЖИДАНИЕ ] ⏳", COLOR_INFO)
        embed.add_field(name="Причина", value="Слишком частое использование команды.", inline=False)
        embed.add_field(name="Повтор через", value=f"`{error.retry_after:.2f} сек.`", inline=True)
        embed.add_field(name="Режим", value="Защита от спама", inline=True)
        await ctx.send(embed=embed)

    elif isinstance(error, commands.MissingRequiredArgument):
        embed = create_base_embed("[ СТАТУС : ОШИБКА ВВОДА ] 🚫", COLOR_CRITICAL)
        embed.add_field(name="Причина", value=f"Отсутствует обязательный параметр: `{error.param.name}`", inline=False)
        embed.add_field(name="Пример", value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`", inline=False)
        await ctx.send(embed=embed)

    elif isinstance(error, commands.MemberNotFound):
        embed = create_base_embed("[ СТАТУС : ЦЕЛЬ НЕ НАЙДЕНА ] 👥", COLOR_CRITICAL)
        embed.add_field(name="Причина", value="Указанный пользователь не обнаружен в базе данных сервера.", inline=False)
        embed.add_field(name="Инструкция", value="Упомяните пользователя через @ или используйте ID.", inline=False)
        await ctx.send(embed=embed)

    else:
        print(f"[ERROR] {error}")
        embed = create_base_embed("[ СТАТУС : КРИТИЧЕСКИЙ СБОЙ ] ⚠️", COLOR_CRITICAL)
        embed.add_field(name="Код ошибки", value=f"```py\n{str(error)[:1000]}```", inline=False)
        await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = disnake.Embed (
        title="[ ПОМОЩЬ : СПИСОК КОМАНД ]"
    )
    embed.add_field(name="Казино", value="dice - сыграть в кости | .dice <member> <bet> \nslots - сыграть в слоты | .slots <bet>\n bj - сыграть в БлекДжек | .bj <bet>", inline=False)
    embed.add_field(name="Экономика", value="balance - посмотреть баланс | .balance <member> \nbuy - приобрести товар из магазина  | .buy <item-id>\n collect - получить деньги | .collect\n crime - заработать деньги на криминале | .crime\n ecolb - посмотреть список самых богатих на сервере | .ecolb\n inv - посмотреть инвентарь | .inv <member>\n shop - посмотреть магазин | .shop\n work - заработать деньги | .work ", inline=False)
    embed.add_field(name="Модерация", value="report - вызвать модератора/менеджера в чат | .report <reason>")
    embed.set_author(name=f"Запрос от {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT, icon_url=bot.user.display_avatar.url)

    await ctx.reply(embed=embed)





if __name__ == "__main__":
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    
    bot.run(os.getenv("TOKEN"))