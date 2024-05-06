import os
import random

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv
import mariadb

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()

server_id = 1236635410793234553


async def db_insert(id, role, url, username):
    conn = mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_UHOST"),
        database=os.getenv("DB_NAME"))
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Users (discord_id ,role,avatar_url,username,password) VALUES (?, ?, ?, ?, ?)",
                    (id, role, url, username, "Nothing"))
    except mariadb.Error as e:
        print(f"Error: {e}")
    conn.commit()
    print(f"Last Inserted ID: {cur.lastrowid}")
    conn.close()


@bot.tree.command(
    name="update",
    description="update database",
    guild=discord.Object(id=server_id))
async def db_update(interaction):
    conn = mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_UHOST"),
        database=os.getenv("DB_NAME"),
        autocommit=True)

    cur = conn.cursor()
    cur.execute("SELECT discord_id FROM Users")

    Channel_id = interaction.channel_id
    Channel = bot.get_guild(server_id).get_channel(Channel_id)
    conn.close()

    for discord_id in cur:

        conn2 = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_UHOST"),
            database=os.getenv("DB_NAME"),
            autocommit=True)
        cur2 = conn2.cursor()

        found = False
        async for member in bot.get_guild(server_id).fetch_members():
            if member.id == discord_id[0]:
                found = True

        if not found:
            cur2.execute("DELETE FROM Users WHERE discord_id = %d", (discord_id[0],))
            await Channel.send("User id :"+ str(discord_id[0]) + " data has been Deleted")
        elif found:
            Updated_user = bot.get_guild(server_id).get_member(discord_id[0])
            user_role = Updated_user.top_role.name
            user_avatar_url = Updated_user.avatar.url
            print(str(discord_id[0]) + " \ " + Updated_user.name + " \ " + user_role + " \ " + user_avatar_url)
            cur2.execute("UPDATE Users SET role = %s , avatar_url = %s, username = %s WHERE discord_id = %d", (user_role,user_avatar_url,Updated_user.name,(discord_id[0])))
            await Channel.send(Updated_user.name + " data has been updated")

        conn2.close()

    await Channel.send("Database has been updated!")


@bot.tree.command(
    name="purge",
    description="purge chat",
    guild=discord.Object(id=server_id))
@commands.has_guild_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
@app_commands.describe(amount="The amount of messages that should be deleted.")
async def purge(interaction, amount: int) -> None:
    await interaction.channel.send("Deleting . . .")
    purged_messages = await interaction.channel.purge(limit=amount + 1)
    embed = discord.Embed(
        description=f"**{interaction.user}** cleared **{len(purged_messages)-1}** messages!",
        color=0xBEBEFE,
    )
    await interaction.channel.send(embed=embed)

@bot.tree.command(
    name="sync",
    description="sync comands",
    guild=discord.Object(id=server_id))
async def sync(interaction):
    await bot.tree.sync(guild=discord.Object(id=server_id))
    await interaction.response.send_message("Done")



@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("EMS"))
    print("Ready!")


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1236637474139406418)
    embed = discord.Embed(
        title="Welcome", description="Welcome to OHED", color=0xFF0000
    )
    embed.set_author(name="Ocean Hospital EMS Department", url="", icon_url="")
    embed.add_field(name=member.name, value="", inline=False)
    role = discord.utils.get(member.guild.roles, name="TRAINEE")
    await member.add_roles(role)
    await db_insert(member.id, member.top_role.name, member.avatar.url, member.name)
    await channel.send(embed=embed)

bot.run(os.getenv("TOKEN"))
