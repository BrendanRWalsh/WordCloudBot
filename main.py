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
        await message.channel.send('generating word cloud of {0.author}'.format(message))
        params = {'author': message.author,
                    'guild':message.guild,
                    'postTo': message.channel,
                    'users': [
                        message.author],
                    'channels': None,
                    'range': 100}
        parse(text,params)


def parse(text,params):
    cmd = text.split()
    if len(cmd) < 2:
        print('generating word cloud of '+str(message.author))

        await getHistory(params)
    else:
        if cmd[1]=="help" | cmd[1]=="?":
            embed = discord.Embed(title="How to use:", colour=discord.Colour(0x6a5cae))
            embed.set_footer(text="hosted at https://github.com/BrendanRWalsh/WordCloudBot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
            embed.add_field(name="-----------------", value="!cloudme [parameters]")
            embed.add_field(name="users= [name|id]", value="list of users to generate cloud of e.g. \"users= Dagon, Cthulu, John\". Default= self. Ensure commas \",\" are between users.")
            embed.add_field(name="channels= [name|id]", value="list of channels to generate cloud from e.g. \"channels= Cultist talk, general_worship\". Default= all. Ensure commas \",\" are between channels.")
            embed.add_field(name="picture= [url]", value="define an image to base cloud on. Default= user avater/guild image. Low-resolution images create bad word clouds!")
            embed.add_field(name="mask= [true/false]", value="Choose to automatically mask image based on colour. Default = False.")
            embed.add_field(name="mask_colour= [name/hex]", value="Choose which colour to mask out. Default = white / FFFFFF.")
            await params["postTo"].send(embed=embed)

    # cmds = {"users": none,
    #         "channels": none,
    #         "picture": none,
    #         "range:": none
    #         }
    # if text.find("user=") == -1 & text.find("users=") == -1:
    #     u = text.find("users=")+5

    # c = text.find("channel=")+8
    # p = text.find("picture=")+8
    # cmds = sorted([u, c, p])
    # print(cmds)

    # print(c)
    # print(text[cmds[0]:cmds[1]])
    # users = users.split(',')
    # users = list(map(str.strip,users))
    # print(users)


async def getHistory(params):
    words = {}
    # Create list of channels to iterate over
    if not params["channels"]:
        params["channels"] = getChannels(params["guild"])

    # iterate over channels and return word counts
    for channel in params["channels"]:
        async for msg in channel.history(limit=10000):
            if msg.author in params["users"]:
                content = msg.content.lower()
                for i in [";", ";", ",", ".", "(", ")", "[", "]", "{", "}", "`", "~", "=", "+", "/", "\\"]:
                    content = content.replace(i, " ")
                content = content.split()
                for word in content:
                    if word[0].isalpha() and len(word) > 2 and len(word) < 10 and not word.startswith("html") and not word.startswith("http") and word not in ["the", "and", "that", "have", "for", "not", "with", "you", "this", "but"]:
                        if word in words:
                            words[word] += 1
                        else:
                            words[word] = 1
    words = {k: v for k, v in sorted(
        words.items(), key=lambda item: item[1], reverse=True)}
    await generateWordCloud(words, params)


def getChannels(guild):
    return guild.text_channels


async def generateWordCloud(text, params):
    avatar = requests.get(params["author"].avatar_url)
    image = Image.open(BytesIO(avatar.content))
    colouring = np.array(image)
    stopwords = set(STOPWORDS)
    filename = "wordclouds/"+str(params["author"])+".png"
    wc = WordCloud(width=image.width, relative_scaling=0.2, stopwords=stopwords, height=image.height, mode="RGB", min_font_size=1,
                   max_words=2000, repeat=True, font_step=1, max_font_size=int(image.width/15))
    wc.generate_from_frequencies(text)
    image_colors = ImageColorGenerator(colouring)
    # show
    fig, axes = plt.subplots(1, 3)
    axes[0].imshow(wc, interpolation="bilinear")
    # recolor wordcloud and show
    # we could also give color_func=image_colors directly in the constructor
    axes[1].imshow(wc.recolor(color_func=image_colors),
                   interpolation="bilinear")
    axes[2].imshow(colouring, cmap=plt.cm.gray, interpolation="bilinear")
    wc.to_file(filename)
    f = discord.File(filename)
    await params["postTo"].send('Wordcloud for ' + str(params["author"]) + ' complete!')
    await params["postTo"].send(file=f)

client.run(TOKEN)