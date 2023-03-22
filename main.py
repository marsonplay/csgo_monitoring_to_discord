import discord
from discord.ext import commands
import valve.source.a2s
import asyncio

BOT_TOKEN = ""  # токен бота
SERVER_ADDRESS = ("1.2.3.4", 12345)
CHANNEL_ID = 1234567890  # ID вашего текстового канала
TIME = 300  # 300 = 5 минут
ROLE_ID = 1234567890  # ID роли для упоминания

# функция для чтения ключевых слов из файла
def read_keywords():
    with open('keywords.txt', 'r') as file:
        KEYWORDS = [line.strip() for line in file]
    return KEYWORDS

print(read_keywords())

# функция для записи ключевых слов в файл
def write_keywords(keywords):
    with open('keywords.txt', 'w') as file:
        for keyword in keywords:
            file.write(keyword + '\n')

# функция для добавления ключевого слова
def add_keyword(keyword):
    keywords = read_keywords()
    if keyword not in keywords:
        keywords.append(keyword)
        write_keywords(keywords)

# функция для удаления ключевого слова
def remove_keyword(keyword):
    keywords = read_keywords()
    if keyword in keywords:
        keywords.remove(keyword)
        write_keywords(keywords)

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def update_server_info():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    role = channel.guild.get_role(ROLE_ID)
    while not bot.is_closed():
        with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
            info = server.info()
            players = []
            for player in server.players()["players"]:
                if player["name"]:
                    players.append(player["name"])
            player_count = len(players)
            message = f"{player_count}/{info['max_players']} {info['server_name']}\n"
            message += "\nPlayers:\n" + "\n".join(players) if players else "Нет игроков в сети."
            filtered_players = []
            for player in players:
                for keyword in read_keywords():
                    if keyword.lower() in player.lower():
                        filtered_players.append(player)
                        break
                else:
                    continue
                break
            if not filtered_players:
                message += "\nИгроки не найдены фильтром."
            else:
                message += "Игрок найден:\n" + "\n".join(filtered_players)
                await channel.send(f"{role.mention}, игрок найден: {', '.join(filtered_players)}")
            await channel.send(f"```{message}```")
        await asyncio.sleep(TIME)

@bot.event
async def on_ready():
    print(f"Logged bot in as {bot.user.name} ({bot.user.id})")
    bot.loop.create_task(update_server_info())

@bot.command(name="players", aliases=["p"])
async def show_players(ctx):
    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
        players = []
        for player in server.players()["players"]:
            if player["name"]:
                players.append(player["name"])
        if players:
            await ctx.send("```Список игроков на сервере:\n" + "\n".join(players) + "```")
        else:
            await ctx.send("На сервере нет игроков.")

@bot.command(name="filters", aliases=["f"])
async def show_filters(ctx):
    if not read_keywords():
        await ctx.send("Фильтр пустой.")
        return
    message = "\n".join(f"{i}. {keyword}" for i, keyword in enumerate(read_keywords()))
    await ctx.send("```Список игроков в фильтре:\n" + message + "```")

@bot.command(name='add')
async def add(ctx, keyword):
    add_keyword(keyword)
    await ctx.send(f'Keyword "{keyword}" added.')

@bot.command(name='remove')
async def remove(ctx, keyword):
    remove_keyword(keyword)
    await ctx.send(f'Keyword "{keyword}" removed.')

bot.run(BOT_TOKEN)