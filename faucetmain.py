from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import discord

#import sqlite3
#from sqlite3 import Error
import os.path
import os
import time

import random
from captcha.image import ImageCaptcha

import config

rpc_connection = 'http://{0}:{1}@{2}:{3}'.format(config.rpc_user, config.rpc_password, config.ip, config.rpc_port)
prefix=config.PREFIX
#by joe_land1

#faucet_time_logs=the timer for the faucet itself
#usr - captcah stuff and the wallet for withdrawl

client = discord.Client()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if client.user.id == message.author.id:
        return

    wallet = AuthServiceProxy(rpc_connection)

    #read dm to see if captcha
    if message.guild is None:
        if os.path.isfile("faucet_usr/"+str(message.author.id)+"_captcha_image.png")== True:
            user_reply=message.content

            #check the time
            timestamp_created = 0
            with open("faucet_usr/"+str(message.author.id)+"_captcha_timestamp.txt", 'r') as f:
                for line in f:
                    try:
                        timestamp_created = float(line)
                    except:
                        raise
            print(time.time())
            print(timestamp_created)
            if time.time()-timestamp_created<=30 and time.time()-timestamp_created>=1:
                f=open("faucet_usr/"+str(message.author.id)+"_captcha_answer.txt", "r")
                captcha_answer = f.read()
                f.close()

                f=open("faucet_usr/"+str(message.author.id)+"_addres.txt", "r")
                address= f.read()
                f.close()

                if captcha_answer==user_reply:
                    await faucetsend(message, wallet, address)
                else:
                    await message.author.send("incorrec, please request another captcha in the server")

                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_image.png")
                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_timestamp.txt")
                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_answer.txt")
                os.remove("faucet_usr/"+str(message.author.id)+"_addres.txt")


            else:
                print("invalid time")
                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_image.png")
                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_timestamp.txt")
                os.remove("faucet_usr/"+str(message.author.id)+"_captcha_answer.txt")
                os.remove("faucet_usr/"+str(message.author.id)+"_addres.txt")

    else:
        if message.channel.id == config.CHANNEL:
            if message.content==prefix+"help":
                await helpmenue(message)

            if message.content.startswith(prefix+'faucet'):

                toaddress = message.content.split(" ")[1]
                validatestatus=wallet.validateaddress(toaddress)

                if validatestatus["isvalid"]==True:

                    #create captcha stuffs
                    letters = "0123456789abcdefghijklmnopqrstuvwxyz?!()@"
                    captcha_answer=''.join(random.choice(letters) for i in range(config.CAPTCHALENGTH))

                    image_captcha = ImageCaptcha()

                    captcha_image_file_name = "faucet_usr/"+str(message.author.id)+"_captcha_image.png"
                    image = image_captcha.generate_image(captcha_answer)
                    image_captcha.write(captcha_answer, captcha_image_file_name)

                    captcha_answer_file_name = "faucet_usr/"+str(message.author.id)+"_captcha_answer.txt"
                    f=open(captcha_answer_file_name, "+w")
                    f.write(captcha_answer)
                    f.close()

                    captcha_timestamp = "faucet_usr/"+str(message.author.id)+"_captcha_timestamp.txt"
                    f=open(captcha_timestamp, "+w")
                    f.write(str(time.time()))
                    f.close()

                    destination_address = "faucet_usr/"+str(message.author.id)+"_addres.txt"
                    f=open(destination_address, "+w")
                    f.write(toaddress)
                    f.close()

                    print("captcha generated")
                    await message.author.send(file=discord.File(captcha_image_file_name))
                    print(captcha_answer)

                else:
                    x = client.get_channel(config.CHANNEL)
                    await x.send("invalid address")



@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def sendmessage(ctx, txid):

    f=open("faucet_usr/"+str(ctx.author.id)+"_addres.txt", "r")
    address= f.read()
    f.close()

    embed = discord.Embed(
        title="**Block explorer**",
        url='https://1explorer.sugarchain.org/tx/{0}'.format(txid), color=0x0043ff)
    embed.add_field(
        value="Amount sent: "+str(config.AMOUNT),
        name=address)

    x = client.get_channel(config.CHANNEL)

    await x.send(embed=embed)
    print("reward sent")

async def faucetsend(message, wallet, toaddress):
    authoridfile='faucet_time_logs/'+str(message.author.id)+'.txt'
    #test to see if person has ever used faucet
    if os.path.isfile(authoridfile)==False:
        f=open(authoridfile,"+w")
        f.write(str(time.time()))
        f.close

        txid = wallet.sendfrom(config.FAUCET_SOURCE,toaddress, config.AMOUNT)
        if len(txid) == 64:
            await sendmessage(message, txid)

    #if person has use faucet before
    else:
        contents = 0 # Initialize this as zero value - we'll add to it to ensure it stays an int
        with open(authoridfile, 'r') as f:
            for line in f:
                try:
                    contents = float(line)
                except:
                    raise

        if time.time()-float(contents)>=config.TIME:
            txid = wallet.sendfrom(config.FAUCET_SOURCE,toaddress, config.AMOUNT)

            os.remove(authoridfile)
            f=open(authoridfile, "+a")
            f.write(str(time.time()))
            f.close()

            if len(txid) == 64:
                await sendmessage(message, txid)

        #if the time is smaller than the specified amount of seconds
        else:
            await message.channel.send("You must wait "+str(int((config.TIME-(time.time()-float(contents)))/60))+" minutes before you can use the faucet again.")

async def helpmenue(message):

    x = client.get_channel(config.CHANNEL)

    embed=discord.Embed(title="Sugarchain Faucet", color=0x0000ff)
    embed.add_field(name="How to use me", value="Type in `"+config.PREFIX+"faucet [coin address]`\nThen solve the captcha in DM\nIf the faucet was successful, it will display a link to the transaction")
    embed.add_field(name="Creator", value="<@"+str(config.OWNER_ID)+">")
    #embed.add_field(name="Donations:", value="BTC - 1Ejgoagvjc7Wzg4nMAF2oeoKeDxDjv4wic\nBCH - qz89j3xxq34tud50sgksmewddr7dum3njvlpd85cxc\nSugar - sugar1q4v54slhzzzkhtvtsq6pttlwufft8m5js8a2wtf" , inline=False)

    await x.send(embed=embed)

client.run(config.TOKEN)
