import csv
import os
import urllib.parse
import discord
from discord.ext import commands
# from pymongo.mongo_client import MongoClient
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils
import settings as settings

"""Mongodb Migration in slow progress."""

intents = discord.Intents.all()

# List of cogs to load
cogs: list = ["controllers.MovementController", "controllers.AdminController", "controllers.background.MovementBackgroundController"]

client = commands.Bot(command_prefix=settings.Prefix, help_command=None, intents=intents)
sheet_utils = GoogleSheetUtils()

@client.event
async def on_ready():
    # Use a fallback for BotStatus
    await client.change_presence(
        status=discord.Status.online, 
        activity=discord.Game(os.environ.get("BOTSTATUS", settings.BotStatus))
    )

    # await connect_mongodb()
    await download_sheets()
    
    # Load all cogs
    for cog in cogs:
        try:
            print(f"Loading cog {cog}")
            await client.load_extension(cog)
            print(f"Loaded cog {cog}")
        except Exception as e:
            exc = "{}: {}".format(type(e).__name__, e)
            print(f"Failed to load cog {cog}\n{exc}")
    
    print("Bot is ready!")

"""
async def connect_mongodb():
    username = urllib.parse.quote_plus(settings.username)
    password = urllib.parse.quote_plus(settings.password)
    
    uri = f"mongodb+srv://{username}:{password}@gaeplex.kbw9i.mongodb.net/?retryWrites=true&w=majority&appName=gaeplex"

    # Create a new client and connect to the server
    mongo_client = MongoClient(uri)

    # Send a ping to confirm a successful connection
    try:
        mongo_client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
"""


async def download_sheets():
    google_sheet_utils = GoogleSheetUtils()
    # Download sheets.
    sheet_names = ["Status", "Movements", "Map"]

    # Ensure the directory exists
    directory = "src/sheets"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for sheet in sheet_names:
        data = google_sheet_utils.get_sheet_by_name(sheet)
        if data:
            print(f"Downloading {sheet}.")
            with open(f"{directory}/{sheet}.csv", mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)

# Use a fallback for TOKEN in case it's not in the environment
client.run(os.environ.get("TOKEN", settings.TOKEN))
