import discord
import asyncio
import json
import logging
from discord import app_commands
import aiohttp
import datetime

def load_config():
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.critical("The config.json file was not found.")
        raise
    except json.JSONDecodeError:
        logging.critical("config.json is not a valid JSON file.")
        raise
    except Exception as e:
        logging.critical(f"An unexpected error occurred while loading config.json: {e}")
        raise

config = load_config()
discord_bot_token = config["discord_bot_token"]
server_id = config["server_id"]

class HamSearch(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def command_tree(self):
        self.tree.copy_global_to(guild=discord.Object(id=server_id))
        await self.tree.sync(guild=discord.Object(id=server_id))

client = HamSearch(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Command to search for a callsign
@client.tree.command(name="ham", description="Search for a callsign.")
async def ham(interaction: discord.Interaction, callsign: str):
    url = f"https://callook.info/{callsign}/json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    # Check if the 'current' key exists in the data
    if 'current' not in data:
        await interaction.response.send_message(f"Callsign '{callsign}' not found.", ephemeral=True)
        return

    # Create the embed
    embed = discord.Embed(title="🎙️ Callsign Information 🎙️", color=0xFF4000)
    embed.add_field(name="Callsign", value=data['current']['callsign'], inline=False)
    embed.add_field(name="Operator Class", value=data['current']['operClass'], inline=False)
    embed.add_field(name="Name", value=data['name'], inline=False)
    embed.add_field(name="Address", value=f"{data['address']['line1']}, {data['address']['line2']}", inline=False)
    embed.add_field(name="Grant Date", value=data['otherInfo']['grantDate'], inline=False)
    embed.add_field(name="Expiration Date", value=data['otherInfo']['expiryDate'], inline=False)
    embed.add_field(name="Gridsquare", value=data['location']['gridsquare'], inline=False)

    # Create a hyperlink to Google Maps using the coordinates
    latitude = data['location']['latitude']
    longitude = data['location']['longitude']
    google_maps_url = f"http://maps.google.com/maps?q={latitude},{longitude}"
    embed.add_field(name="Coordinates", value=f"[{latitude}, {longitude}]({google_maps_url})", inline=False)

    embed.add_field(name="FCC Registration Number (FRN)", value=data['otherInfo']['frn'], inline=False)
    embed.add_field(name="FCC URL", value=data['otherInfo']['ulsUrl'], inline=False)

    await interaction.response.send_message(embed=embed)

    # Log the username, callsign, and current date and time to a text file
    with open("logs", "a") as log_file:
        log_file.write(f"User: {interaction.user.name}, Callsign: {callsign}, Date and Time: {datetime.datetime.now()}\n")

# Function to run the bot
def run_discord_bot():
    try:
        client.run(config["discord_bot_token"])
    except Exception as e:
        logging.error(f"An error occurred while running the bot: {e}")
    finally:
        if client:
            asyncio.run(client.close())

if __name__ == "__main__":
    run_discord_bot()
    
