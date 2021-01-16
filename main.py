# bot.py
import os
import discord
# from discord.utils import get
# from discord.ext import commands
from dotenv import load_dotenv
import re
import time
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
guild = discord.Guild


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    text = message.content.lower()
    if message.author == client.user:
        return
    if text.startswith('!cloudme'):
        cmd = text.split()
        if len(cmd) < 2:
            await message.channel.send('generating word cloud of{0.author}'.format(message))
            params = {'author': message.author,
                      'users': [
                          message.author],
                      'channels': []}
            await getHistory(params)
        else:
            text = text.replace("!cloudme ", "")
            # parse(text, message.author)


def parse(text):
    cmds = {"users": none,
            "channels": none,
            "picture": none,
            "range:": none
            }
    if text.find("user=") == -1 & text.find("users=") == -1:
        u = text.find("users=")+5

    c = text.find("channel=")+8
    p = text.find("picture=")+8
    cmds = sorted([u, c, p])
    print(cmds)

    print(c)
    print(text[cmds[0]:cmds[1]])
    # users = users.split(',')
    # users = list(map(str.strip,users))
    # print(users)


async def getHistory(params):
    data = pd.DataFrame(columns=['content', 'time', 'author'])

    # Create list of channels to iterate over
    if params["channels"] == None:
        params["channels"] = getChannels()

    # As an example, I've set the limit to 10000
    async for channel in params["channels"]:
        async for msg in channel.history(limit=100):
            if msg.author == params["author"]:
                data = data.append({'content': msg.content,
                                    'time': msg.created_at,
                                    'author': msg.author.name}, ignore_index=True)
                if len(data) == limit:
                    break
    file_location = "data.csv"  # Set the string to where you want the file to be saved to
    data.to_csv(file_location)


def getChannels():
    channelList = []
    for guild in client.guilds:
        for channel in guild.channels:
            if channel.type == 'text':
                channelList.append(channel)
    return channelList


def generateWordCloud(params):
    if "users" not in params:
        params["users"] = params["author"]

    wordcloud = WordCloud().generate("tits")
    location = "wordclouds/test.png"
    wordcloud.to_file(location)
    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")


client.run(TOKEN)


# message.content.matchAll()
# (?=(users?=))
# (?<=(user=|sers=))\s?(\w*(,\s?)\w*)*
# def getHistory():
# async for msg in message.channel.history(limit=10000)
# msg = 'Hi {0.author.mention}'.format(message)
# await message.channel.send(msg)
# userPattern = r"users?\s*=\s*(.+)"
#     channelPattern = r"channel?\s*=\s*(.+)"
