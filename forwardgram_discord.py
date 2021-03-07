import discord
from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel, Channel, Dialog, InputUser, User, Chat
import yaml
import sys
import logging
import pprint
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)



def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))


def start(config):
    
    # setup the Telegram client
    telegram_client = TelegramClient(config["session_name"], 
                            config["api_id"], 
                            config["api_hash"])
    telegram_client.start()

    #setup telegram output channels
    telegram_output_channel_entities = []
    for d in telegram_client.iter_dialogs():
        if 'Channel' == type(d.entity).__name__ and d.name in config["output_channel_names"]:
            telegram_output_channel_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
    if not telegram_output_channel_entities:
        logger.error(f"Could not find any Telegram output channels in the user's dialogs")
        sys.exit(1)
    logging.info(f"Forwarding messages to {len(telegram_output_channel_entities)} Telegram channels.")
    
    
    if 'discord_token_auth' in config and 'discord_input_guild_name' in config and 'discord_channel_names' in config:
        #setup discord client
        discord_client = discord.Client()
        discord_subscribed_channels = []

        #setup guilds (servers) and channels
        @discord_client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(discord_client))
            for guild in discord_client.guilds:
                if guild.name == config["discord_input_guild_name"]:
                    print("Starting Discord forwarder on server '"+guild.name+"'")
                    print("Forwarding the following channels:")
                    for channel in guild.channels:
                        if channel.name in config["discord_channel_names"]:
                            print(channel)
                            discord_subscribed_channels.append(channel)
                        
        # Wait for messages and reply (debug) or forward to telegram
        @discord_client.event
        async def on_message(message):
            if message.author == discord_client.user:
                return
            if message.content.startswith('$hello'):
                if message.channel in discord_subscribed_channels:
                    await message.channel.send('Hello!')
            else:
                if message.channel in discord_subscribed_channels:
                    for output_channel in telegram_output_channel_entities:
                        if len(message.attachments) == 1:
                            for attachment in message.attachments:
                                await telegram_client.send_file(output_channel, attachment.url, caption=message.content)
                        elif len(message.attachments) > 1:
                            if message.content.length > 0:
                                await telegram_client.send_message(output_channel, message.content) 
                            for attachment in message.attachments:
                                await telegram_client.send_file(output_channel, attachment.url)
                        else:
                            await telegram_client.send_message(output_channel, message.content)

        # run the Discord listening service
        discord_client.run(config["discord_token_auth"], bot=False)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} {{CONFIG_PATH}}")
        sys.exit(1)
    with open(sys.argv[1], 'rb') as f:
        config = yaml.safe_load(f)
    start(config)
