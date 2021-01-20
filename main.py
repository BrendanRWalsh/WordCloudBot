import os
import discord
from dotenv import load_dotenv
import re
import time
import datetime
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from PIL import Image
import requests
from io import BytesIO
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

# Discord
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()
guild = discord.Guild
trackerLimit=10000
# log onto discord service
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

#Listen event
@client.event
async def on_message(message):
    text = message.content.lower()
    if message.author == client.user:
        return
    #Prefix check
    if text.startswith('!cloud'):
        #set paramaters to operate on
        
        params = {'author': message.author,
                    'guild':message.guild,
                    'parentChannel': message.channel,
                    'users': [
                        message.author],
                    'channels': None,
                    'range': datetime.datetime.now() - datetime.timedelta(days=100),
                    'image': None,
                    'Mask': False,
                    'Mask_colour':"white"}
        await parse(text,params)

# Interprate text from user
async def parse(text,params):
    cmd = text.split()

    # check if the user submitted any parameters or 
    if len(cmd) < 2 or cmd[1]=="help" or cmd[1]=="?":
        # if user called without params or help commands
        embed = discord.Embed(title="How to use:", colour=discord.Colour(0x6a5cae))
        embed.set_footer(text="github.com/BrendanRWalsh/WordCloudBot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        embed.add_field(name="-----------------", value="!cloudme [parameters]")
        embed.add_field(name="users= [name|id]", value="list of users to generate cloud of e.g. \"users= Dagon, Cthulu, John\". Alias \"me\" for own cloud. Ensure commas \",\" are between users.")
        embed.add_field(name="channels= [name|id]", value="list of channels to generate cloud from e.g. \"channels= Cultist talk, general_worship\". Default= all. Ensure commas \",\" are between channels.")
        embed.add_field(name="date= [days | d/m/y]", value="how far back to read messages. Bare numbers will be interpretited as days. Default = 100 days")
        embed.add_field(name="picture= [url]", value="define an image to base cloud on. Default= user avater/guild image. Low-resolution images create bad word clouds!")
        embed.add_field(name="mask= [true/false]", value="Choose to automatically mask image based on colour. Default = False.")
        embed.add_field(name="mask_colour= [name/hex]", value="Choose which colour to mask out. Default = white / FFFFFF.")
        embed.add_field(name="Quick generate:", value="!cloud me")
        await params["parentChannel"].send(embed=embed)
    else if cmd[1]=="me":
        await params["parentChannel"].send('generating word cloud of ' + str(params["author"] + "..."))
        print('generating word cloud of '+str(params["author"]))
        await getHistory(params)
    else:
        None
    return True


async def getHistory(params):
    words = {}
    # Create list of channels to iterate over
    if not params["channels"]:
        params["channels"] = getChannels(params["guild"])

    # iterate over channels and return word counts
    for channel in params["channels"]:
        async for msg in channel.history(limit=trackerLimit):
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
            if msg.created_at < params['range']:
                break
    words = {k: v for k, v in sorted(
        words.items(), key=lambda item: item[1], reverse=True)}
    if not words:
        await params["parentChannel"].send("Sorry, not enough words in this server for me to make a word cloud with these paramaters, try again later! (or spam the channels for a bit)")
    else:    
        await generateWordCloud(words, params)


def getChannels(guild):
    return guild.text_channels

async def getConfirmation(params):
    embed = discord.Embed(title="Confirm details", colour=discord.Colour(0x6a5cae))
        embed.set_footer(text="github.com/BrendanRWalsh/WordCloudBot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        embed.add_field(name="Users:", value=params["users"])
        embed.add_field(name="Channels:", value=params["channels"])
        embed.add_field(name="Range:", value=params["range"])
        embed.add_field(name="Image:", value=params["image"])
        embed.add_field(name="Mask:", value=params["mask"])
        embed.add_field(name="Mask_colour:", value=params["mask_colour"])
        msg = await params["parentChannel"].send(embed=embed)
        await msg.add_reaction('✔️')
        await msg.add_reaction('❌')
        def check(reaction, user):
            if user == params["author"] and str(reaction.emoji) == '✔️':
                generateWordCloud(text,params)
                return True
            if user == params["author"] and str(reaction.emoji) == '❌':
                await params["parentChannel"].send('Generation Cancelled')
                break
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await channel.send('👎')
        else:
            await channel.send('👍')

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
    print(('Wordcloud for ' + str(params["author"]) + ' complete!'))
    await params["parentChannel"].send('Wordcloud for ' + str(params["author"]) + ' complete!')
    await params["parentChannel"].send(file=f)

client.run(TOKEN)