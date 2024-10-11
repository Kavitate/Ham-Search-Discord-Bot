import discord
import asyncio
import json
import logging
import aiohttp
import datetime
from bs4 import BeautifulSoup
import re
from math import radians, sin, cos, sqrt, atan2

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
server_id = config['server_id']

class HamSearch(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        print(f'Logged in as {self.user}.')

client = HamSearch()

# Command Logging
def log_command(interaction: discord.Interaction, command_name: str, *args):
    with open("logs.txt", "a") as log_file:
        log_file.write(f"User: {interaction.user.name}, Command: {command_name}, Args: {args}, Date and Time: {datetime.datetime.now()}\n")

# Callsign Search Command
@client.tree.command(name="ham", description="Search for a callsign.")
async def ham(interaction: discord.Interaction, callsign: str):
    log_command(interaction, "ham", callsign)
    url = f"https://callook.info/{callsign}/json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    # Check if the 'current' key exists in the data
    if 'current' not in data:
        await interaction.response.send_message(f"Callsign '{callsign}' not found.", ephemeral=True)
        return

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

# Conditions Command
@client.tree.command(name="conditions", description="Get the latest band conditions.")
async def conditions(interaction: discord.Interaction):
    log_command(interaction, "conditions")
    embed = discord.Embed(title="Latest Band Conditions", color=0xFF4000)
    embed.set_image(url="https://www.hamqsl.com/solar101vhfpic.php")
    await interaction.response.send_message(embed=embed)

# Logbook Command
@client.tree.command(name="logbook", description="Retrieve logbook stats for a callsign.")
async def logbook(interaction: discord.Interaction, callsign: str):
    log_command(interaction, "logbook", callsign)
    url = f"https://logbook.qrz.com/lbstat/{callsign}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await interaction.response.send_message(f"Failed to retrieve logbook stats for '{callsign}'.", ephemeral=True)
                return
            html = await resp.text()

    soup = BeautifulSoup(html, 'html.parser')

    # Scrape QSO and confirmed numbers
    logbook_totals_text = soup.get_text()

    qso_match = re.search(r'(\d+)\s+QSOs', logbook_totals_text)
    confirmed_match = re.search(r'(\d+)\s+confirmed', logbook_totals_text)

    if not qso_match or not confirmed_match:
        await interaction.response.send_message(f"Logbook stats for '{callsign}' not found.\n\nThis is either because the callsign is invalid or the operator does not use QRZ for logging.", ephemeral=True)
        return

    qso_number = int(qso_match.group(1))
    confirmed_number = int(confirmed_match.group(1))

    qso_number_formatted = "{:,}".format(qso_number)
    confirmed_number_formatted = "{:,}".format(confirmed_number)

    embed = discord.Embed(title="🗒️ Logbook Stats 🗒️", color=0xFF4000)
    embed.add_field(name="Callsign", value=callsign, inline=False)
    embed.add_field(name="QSOs", value=qso_number_formatted, inline=True)
    embed.add_field(name="Confirmed", value=confirmed_number_formatted, inline=True)

    await interaction.response.send_message(embed=embed)

# Distance calculation
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat / 2) * sin(dLat / 2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) * sin(dLon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_km = R * c
    distance_miles = distance_km * 0.621371
    return distance_km, distance_miles

# Distance Command
@client.tree.command(name="distance", description="Calculate the distance between two callsigns.")
async def distance(interaction: discord.Interaction, callsign1: str, callsign2: str):
    log_command(interaction, "distance", callsign1, callsign2)
    url1 = f"https://callook.info/{callsign1}/json"
    url2 = f"https://callook.info/{callsign2}/json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url1) as resp1, session.get(url2) as resp2:
            data1 = await resp1.json()
            data2 = await resp2.json()

    if 'location' not in data1 or 'location' not in data2:
        await interaction.response.send_message("One or both callsigns not found.", ephemeral=True)
        return

    lat1, lon1 = float(data1['location']['latitude']), float(data1['location']['longitude'])
    lat2, lon2 = float(data2['location']['latitude']), float(data2['location']['longitude'])

    distance_km, distance_miles = haversine(lat1, lon1, lat2, lon2)

    google_maps_url = f"http://maps.google.com/maps?saddr={lat1},{lon1}&daddr={lat2},{lon2}"

    embed = discord.Embed(title="📏 Distance Between Callsigns 📏", color=0xFF4000)
    embed.add_field(name="Callsign 1", value=callsign1, inline=True)
    embed.add_field(name="Callsign 2", value=callsign2, inline=True)
    embed.add_field(name="Distance", value=f"{distance_miles:,.2f} miles / {distance_km:,.2f} km", inline=False)
    embed.add_field(name="Map", value=f"[View on Google Maps]({google_maps_url})", inline=False)

    await interaction.response.send_message(embed=embed)

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
