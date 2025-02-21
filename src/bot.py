import csv
import os
import discord
from discord.ext import commands
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils
import settings as settings

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
    await notify_game_master()

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

async def notify_game_master():
    # Fetch the GameMaster's user and send a notification
    id = settings.GamemasterID
    try:
        user = await client.fetch_user(id)
        status = await get_game_status()
        if status is not None:
            await user.send(f"Bot is started, game is currently {status}.")
        else:
            await user.send(f"Bot is started, game Status Unavailable.")
    except discord.errors.HTTPException as e:
        print(f"Error: Unable to fetch user with ID {id}. Exception: {e}")

async def get_game_status():
    try:
        # Read the CSV file
        with open(f"src/sheets/Status.csv", mode='r', newline='') as file:
            reader = csv.reader(file)
            data = list(reader)  # Convert the CSV rows into a list of lists

        # Loop through each row to find "Game Status" in the first column
        for row in data:
            if row[0] == "Game Status":
                return row[1]  
    except Exception:
        return None
    
    return None

# Use a fallback for TOKEN in case it's not in the environment
client.run(os.environ.get("TOKEN", settings.TOKEN))
