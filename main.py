import discord
from discord.ext import commands
import valve.source.a2s
import asyncio

BOT_TOKEN = ""  # токен бота
SERVER_ADDRESS = ("1.2.3.4", 12345)
CHANNEL_ID = 1234567890  # ID вашего текстового канала
TIME = 300  # 300 = 5 минут задержка между опросами
ROLE_ID = 1234567890 # ID роли для упоминания
KEYWORDS = ['1', '2', '3', '4']  # Глобальная переменная для ключевых слов

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
                for keyword in KEYWORDS:
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

@bot.command()
async def players(ctx):
    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
        players = []
        for player in server.players()["players"]:
            if player["name"]:
                players.append(player["name"])
        if players:
            await ctx.send("```Список игроков на сервере:\n" + "\n".join(players) + "```")
        else:
            await ctx.send("На сервере нет игроков.")

bot.run(BOT_TOKEN)