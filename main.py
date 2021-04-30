import os
import discord
from dotenv import load_dotenv
import re
import time
import datetime
import random
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from PIL import Image
import requests
from io import BytesIO
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import asyncio

# Discord
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().default()
intents.members = True
client = discord.Client(intents=intents)
guild = discord.Guild
trackerLimit = 1000
minImageSize = [400,400]
maxImageSize = [800,800]
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
        print("called by" + str(message.author))
        params = {'author': message.author,
                    'guild':message.guild,
                    'parentChannel': message.channel,
                    'users': [],
                    'channels': None,
                    'range': datetime.datetime.now() - datetime.timedelta(days=100),
                    'image': None,
                    'mask': False,
                    'mask_colour':"white"}
        await parse(text,params,message)

# check for urls in text body
def findURL(text):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,text)
    return [x[0] for x in url]

# Interprate text from user
async def parse(text,params,message):
    cmd = text.split()
    # check if the user submitted any parameters or 
    if len(cmd) < 2 or cmd[1]=="help" or cmd[1]=="?":
        # if user called without params or help commands
        embed = discord.Embed(title="How to use:", colour=discord.Colour(0x6a5cae))
        embed.set_footer(text="github.com/BrendanRWalsh/WordCloudBot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        embed.add_field(name="Quick generate:", value="!cloud me")
        await params["parentChannel"].send(embed=embed)
    if cmd[1]=="me":
        params["users"].append(message.author)
    url = findURL(text)
    if len(url)== 0:
        params["image"] = params["author"].avatar_url
    else:
        params["image"] = url
    if len(message.mentions) > 0:
        for member in message.mentions:
            print(int(member.id))
            usr = message.guild.get_member(int(member.id))
            print(usr)
            params["users"].append(usr)
    await message.delete()
    await getConfirmation(params)
    return True


async def getHistory(params):
    words = {}
    # Create list of channels to iterate over
    if not params["channels"]:
        params["channels"] = getChannels(params["guild"])
    msgCount = 0
    # iterate over channels and return word counts
    for channel in params["channels"]:
        print("reading messages of" + channel.mention)
        try:
            async for msg in channel.history(limit=trackerLimit):
                if msgCount > trackerLimit:
                    break
                if msg.author in params["users"]:
                    msgCount += 1
                    content = msg.content.lower()
                    if "www" not in content and "http" not in content:
                        for i in [";", ":", "(", ")", "[", "]", "{", "}", "`", "~", "=", "+", "/", "\\"]:
                            content = content.replace(i, " ")
                        for i in ["~","\`","@","#","$","%","^","&","*","_","+","=","|",">","<",".",",","?","!"]:
                            content = content.replace(i, "")
                        content = content.split()
                        for word in content:
                            if word[0].isalpha() and len(word) > 3 and len(word) < 10 and not word.startswith("html") and not word.startswith("http") and word not in ["that","have","with","this","from","they","will","would","there","their","what","about","which","when","make","like","time","just","know","take","people","into","year","your","good","some","could","them","other","than","then","look","only","come","over","think","also","back","after","work","first","well","even","want","because","these","give","most"]:
                                if word in words:
                                    words[word] += 1
                                else:
                                    words[word] = 1
                if msg.created_at < params['range']:
                    break
        except Exception as e: 
            print(e)
        if msgCount > trackerLimit:
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
    eUsers = []
    for u in params["users"]:
        eUsers.append(u.name)
    eUsers = ", ".join(eUsers)
    eChannels = []
    if not params["channels"]:
        eChannels = "everything"
    else:
        for c in params["channels"]:
            eChannels.append(c.name)
        eChannels = ", ".join(eChannels)
    embed = discord.Embed(title="Confirm details", colour=discord.Colour(0x6a5cae))
    # embed.set_footer(text="github.com/BrendanRWalsh/WordCloudBot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    # embed.add_field(name="Users:", value=eUsers)
    # embed.add_field(name="Channels:", value=eChannels)
    # embed.add_field(name="Range:", value=params["range"])
    embed.add_field(name="Image:", value=params["image"])
    # embed.add_field(name="Mask:", value=params["mask"])
    # embed.add_field(name="Mask_colour:", value=params["mask_colour"])
    embed.add_field(name="This may take some time", value="You will be pinged with your completed work of art.")
    embed.set_thumbnail(url=params["image"])
    msg = await params["parentChannel"].send(embed=embed)
    await msg.add_reaction('✔️')
    await msg.add_reaction('❌')
     
    def check(reaction, user):
        if user == params["author"] and str(reaction.emoji) == '✔️':
            return True
        if user == params["author"] and str(reaction.emoji) == ('❌'):            
            return True
    try:
        reaction, user = await client.wait_for('reaction_add',timeout=60.0,check=check)
    except asynchio.TimeoutError:
        await msg.delete()
    else:
        await msg.delete()
        if str(reaction.emoji) == '✔️':
            await params["parentChannel"].send('generating word cloud of ' + str(params["author"]) + "...")
            print('generating word cloud of '+str(params["author"]))
            await getHistory(params)

async def generateWordCloud(text, params):
    try:
        print("reading image")
        imageFile = requests.get(params["image"])
        image = Image.open(BytesIO(imageFile.content))
        # convert gif to frame
        #if image.is_animated:
        image = image.convert('RGBA')
    except Exception as e:
        msg = await params["parentChannel"].send("I AM ERROR")
        print("error in avatar read")
        print(e)
    #Script to resize small images
    #needs more power to run
    #if image.size[0] < minImageSize[0] or image.size[0] > maxImageSize[0]:
    #    wpercent = (minImageSize[0] / float(image.size[0]))
    #    hsize = int((float(image.size[1]) * float(minImageSize[0])))
    #    image = image.resize((minImageSize[0], hsize), Image.ANTIALIAS)
    colouring = np.array(image)
    stopwords = set(STOPWORDS)
    userName= ''.join(e for e in str(params["author"]) if e.isalnum())
    filename = "wordclouds/"+userName+".png"
    try:
        imgScale = 2400 / image.size[0]
        wc = WordCloud(scale = imgScale, width=image.width, relative_scaling=0.2, stopwords=stopwords, height=image.height, mode="RGBA", min_font_size=1,max_words=2000, repeat=True, font_step=1, max_font_size=int(image.width/15))
    except Exception as e:
        print(e)
        imgScale = 1
        wc = WordCloud(scale = imgScale, width=image.width, relative_scaling=0.2, stopwords=stopwords, height=image.height, min_font_size = 1,max_words = 2000, repeat =True, font_step=1,max_font_size=int(imaage.widhtth/15))
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
    #overlay image
    try:
        background = Image.open(filename)
        if image.width < 400:
            ratio = 400 /image.width
            image = image.resize((400,image.height*ratio),Image.ANTIALIAS)
        background = background.resize((image.width,image.height),Image.ANTIALIAS)
        image.putalpha(30)
        background.paste(image,(0,0),image)
        background.save(filename)
    except Exception as e:
        print(e)
        print("overlay failed, defualting to base image")
    f = discord.File(filename)
    print(('Wordcloud for ' + str(params["author"]) + ' complete!'))
    embed = discord.Embed(title="ART", colour=discord.Colour(0x6a5cae))
    why = ["This is your fault","Look at what you've done","Very cool","this is difinitely a thing..","Wow thats...um...yeah","are you proud of yourself?","this was a mistake","What is done can not be undone","Un-make this","They say there are no mistakes, but...","uh"]
    msg = await params["parentChannel"].send(params["author"].mention+" "+random.choice(why))
    # await params["parentChannel"].send('Wordcloud for ' + params["author"].mention() + ' complete!')
    await params["parentChannel"].send(file=f)
    os.remove(filename)

client.run(TOKEN)
