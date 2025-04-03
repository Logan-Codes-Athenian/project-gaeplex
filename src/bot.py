import os
import discord
import pandas as pd
from discord.ext import commands
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils
from utils.sheets.LocalSheetUtils import LocalSheetUtils
import settings as settings

intents = discord.Intents.all()

# List of cogs to load
cogs: list = [
    "controllers.MovementController", 
    "controllers.AdminController",
    "controllers.ArmyController", 
    "controllers.background.MovementBackgroundController",
    "controllers.background.StatusBackgroundController"
]

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
    await notify_game_master()

async def download_sheets():
    google_sheet_utils = GoogleSheetUtils()
    local_sheet_utils = LocalSheetUtils()
    # Download sheets.
    sheet_names = ["Status", "Movements", "Armies", "StatusTimers", "Map"]

    for sheet in sheet_names:
        data = google_sheet_utils.get_sheet_by_name(sheet)
        if data:
            print(f"Downloading {sheet}.")
            # Use LocalSheetUtils to write the data safely.
            local_sheet_utils.update_sheet_by_name(sheet, data)

async def notify_game_master():
    # Fetch the GameMaster's user and send a notification
    id = settings.GamemasterID
    try:
        user = await client.fetch_user(id)
        status = await get_game_status()
        if status is not None:
            await user.send(f"Bot is started, game is currently {status}.")
        else:
            await user.send("Bot is started, game Status Unavailable.")
    except discord.errors.HTTPException as e:
        print(f"Error: Unable to fetch user with ID {id}. Exception: {e}")

async def get_game_status():
    file_path = "src/sheets/Status.csv"
    try:
        # Let pandas use the first row as header
        df = pd.read_csv(file_path, encoding='utf-8')
        # Return the value in the 'Game Status' column from the first row
        return df.iloc[0]["Game Status"]
    except Exception as e:
        print(f"Error reading game status from {file_path}: {e}")
        return None

# Use a fallback for TOKEN in case it's not in the environment
client.run(os.environ.get("TOKEN", settings.TOKEN))
