import discord
from discord.ext import commands
import valve.source.a2s
import asyncio
from datetime import datetime, timedelta

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

previous_players_nicks = []
previous_filtered_players = []
join_players = []
leave_players = []
players_nicks = []

async def update_server_info():
    global previous_filtered_players
    channel = bot.get_channel(CHANNEL_ID)

    with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
        info = server.info()
        players = []

        for player in server.players()["players"]:
            if player["name"]:
                players.append(player)
        player_count = len(players)
        server_name = info['server_name']
        half_length = len(server_name) // 2
        first_half = server_name[:half_length]
        map_name = info['map']
        map_name_full = map_name
        max_length = 30  # Максимальная длина строки
        map_name_length = len(map_name)
        server_name_length = len(first_half)

        if map_name_length > max_length - server_name_length:
            map_name = map_name[:max_length - server_name_length - 1] + "..."
        message = f"{player_count}/{info['max_players']} " + first_half + f" {map_name.rjust(max_length - server_name_length, ' ')}\n"
        print(message)
        filtered_players = []

        for player in players:
            for keyword in read_keywords():
                if keyword.lower() in player["name"].lower():
                    filtered_players.append(player["name"])
                    break
            else:
                continue
            break
        message2 = None

        if filtered_players:
            new_players = set(filtered_players) - set(previous_filtered_players)
            message2 = "Игрок найден:\n" + "\n".join(new_players)
            if new_players:
                await channel.send(f"<@&{ROLE_ID}> {new_players}")
                previous_filtered_players = filtered_players
                #print("debug1")
            else:
                message2 = None
        return players, filtered_players, message, message2, player_count, info, map_name_full

async def loop_bot():
    await bot.wait_until_ready()
    global previous_filtered_players
    global previous_players_nicks
    global players_nicks
    global join_players
    global leave_players
    channel = bot.get_channel(CHANNEL_ID)

    while not bot.is_closed():
        #print("Цикл")
        players, filtered_players, message, message2, player_count, info, map_name_full = await update_server_info()
        #if filtered_players != previous_filtered_players:
        #    channel = bot.get_channel(CHANNEL_ID)
        #    role = channel.guild.get_role(ROLE_ID)
        #    if filtered_players:
        #        await channel.send(f"{role.mention}, ОБНАРУЖЕН!: {', '.join(filtered_players)}")
        players_nicks = []

        for player in valve.source.a2s.ServerQuerier(SERVER_ADDRESS).players()["players"]:
            if player["name"]:
                players_nicks.append(player["name"])

        print("player2: " + str(players_nicks))
        print("prev_player: " + str(previous_players_nicks))
        current_time = datetime.now()
        new_time = current_time + timedelta(hours=2)
        result = new_time.strftime("%H:%M")
        result1 = new_time.strftime("%H_%M")
        topic1 = f"{result} | {player_count}/{info['max_players']} Players | {map_name_full}"

        if players:
            topic1 += "\nPlayers:\n"
            for player in sorted(players, key=lambda p: p['score'], reverse=True):
                nickname = player["name"].ljust(30)
                score = str(player["score"]).rjust(4)
                topic1 += f"{nickname} ({score})\n"
        else:
            topic1 += "No player online"

        await channel.edit(topic=topic1)
        await channel.edit(name=f"{result1} {player_count} Players")

        for player in players_nicks:
            if player not in previous_players_nicks:
                if player in filtered_players:
                    channel = bot.get_channel(CHANNEL_ID)
                    green_embed = discord.Embed(title='', description=f':white_check_mark: {player} Подключился', color=0x00ff00)
                    await channel.send(embed=green_embed)
                    print(f"{player} Подключился")

        for player in previous_players_nicks:
            if player not in players_nicks:
                if player in filtered_players:
                    channel = bot.get_channel(CHANNEL_ID)
                    red_embed = discord.Embed(title='', description=f':x: {player} Отключился', color=0xff0000)
                    await channel.send(embed=red_embed)
                    print(f"{player} Отключился")
        if players_nicks != previous_players_nicks:
            continue
            #channel = bot.get_channel(CHANNEL_ID)
            #await channel.send(f"```{message}```")
            #print("debug2")
        if message2 != None:
            continue
            #channel = bot.get_channel(CHANNEL_ID)
            #await channel.send(f"<@&{ROLE_ID}> {message2}")
            #print("debug3")
        previous_players_nicks = players_nicks
        previous_filtered_players = filtered_players
        await asyncio.sleep(TIME)

@bot.command(name="players", aliases=["p"])
async def show_players(ctx):
    players, filtered_players, message, message2, player_count, info, map_name_full = await update_server_info()
    if players:
        message += "\nPlayers:\n"
        for player in sorted(players, key=lambda p: p['score'], reverse=True):
            nickname = player["name"].ljust(30)
            score = str(player["score"]).rjust(4)
            message += f"{nickname} ({score})\n"
    else:
        message += "Нет игроков в сети."
    await ctx.send(f"```{message}```")

@bot.event
async def on_ready():
    print(f"Logged bot in as {bot.user.name} ({bot.user.id})")
    bot.loop.create_task(loop_bot())

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