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
import requests
from io import BytesIO
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
            await message.channel.send('generating word cloud of {0.author}'.format(message))
            print('generating word cloud of {0.author}')
            params = {'author': message.author,
                      'postTo': message.channel,
                      'users': [
                          message.author],
                      'channels': None,
                      'range': 100}
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
    words = {}
    # Create list of channels to iterate over
    if not params["channels"]:
        params["channels"] = getChannels()

    # iterate over channels and return word counts
    for channel in params["channels"]:
        async for msg in channel.history():
            if msg.author in params["users"]:
                content = msg.content.split()
                for word in content:
                    if word[0].isalpha() and len(word) > 2 and not word.startswith("html") and not word.startswith("http"):
                        if word in words:
                            words[word] += 1
                        else:
                            words[word] = 1

                # if len(data) == limit:
                    # break
                # if msg.crated_at > params["range"]:
                    # break
    words = {k: v for k, v in sorted(
        words.items(), key=lambda item: item[1], reverse=True)}

    await generateWordCloud(list(words.keys()),params)


def getChannels():
    channelList = []
    for guild in client.guilds:
        channelList = guild.text_channels
    return channelList


async def generateWordCloud(text,params):
    avatar = requests.get(params["author"].avatar_url)
    colouring = np.array(Image.open(BytesIO(avatar.content)))
    stopwords = set(STOPWORDS)
    filename = "wordclouds/"+str(params["author"])+".png"
    wc = WordCloud(stopwords=stopwords,mask=colouring,max_words=2000)
    wc.generate(" ".join(text))
    image_colors = ImageColorGenerator(colouring)
    # show
    fig, axes = plt.subplots(1, 3)
    axes[0].imshow(wc, interpolation="bilinear")
    # recolor wordcloud and show
    # we could also give color_func=image_colors directly in the constructor
    axes[1].imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    axes[2].imshow(colouring, cmap=plt.cm.gray, interpolation="bilinear")
    wc.to_file(filename)
    f = discord.File(filename)
    await params["postTo"].send(file=f)

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
# data = data.append({'content': msg.content,
#                     'time': msg.created_at,
#                     'author': msg.author.name}, ignore_index=True)
# file_location = "data.csv"  # Set the string to where you want the file to be saved to
# data.to_csv(file_location)
# data = pd.DataFrame(columns=['content', 'time', 'author'])
    # # Display the generated image:
    # plt.imshow(wordcloud, interpolation='bilinear')
    # plt.axis("off")