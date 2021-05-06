from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel, Channel, Dialog, InputUser, User, Chat
import yaml
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='telegram.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def start(config):
    client = TelegramClient(config["session_name"], 
                            config["api_id"], 
                            config["api_hash"])
    client.start()

    input_entities = []
    output_channel_entities = []
    for d in client.iter_dialogs():
        if 'User' == type(d.entity).__name__ and d.entity.username in config["input_user_usernames"]:
            input_entities.append(InputUser(d.entity.id, d.entity.access_hash))
        if 'Channel' == type(d.entity).__name__ and d.name in config["input_channel_names"]:
            input_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
        if 'Channel' == type(d.entity).__name__ and d.name in config["output_channel_names"]:
            output_channel_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
            
    if not output_channel_entities:
        logger.error(f"Could not find any output channels in the user's dialogs")
        sys.exit(1)

    if not input_entities:
        logger.error(f"Could not find any input channels or users in the user's dialogs")
        sys.exit(1)
        
    logging.info(f"Listening on {len(input_entities)} input channels/users. Forwarding messages to {len(output_channel_entities)} channels.")
    
    @client.on(events.NewMessage(chats=input_entities))
    async def handler(event):
        for output_channel in output_channel_entities:
            await client.forward_messages(output_channel, event.message)

    client.run_until_disconnected()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} {{CONFIG_PATH}}")
        sys.exit(1)
    with open(sys.argv[1], 'rb') as f:
        config = yaml.safe_load(f)
    start(config)
