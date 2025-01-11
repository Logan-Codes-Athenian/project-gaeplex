import re
import discord
import settings as settings
from discord.ext import commands, tasks
from utils.sheets.LocalSheetUtils import LocalSheetUtils
from utils.pathfinding.PathfindingUtils import PathfindingUtils
from utils.misc.EmbedUtils import EmbedUtils

class MovementBackgroundController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.local_sheet_utils = LocalSheetUtils()
        self.path_finding_utils = PathfindingUtils()
        self.map = self.path_finding_utils.retrieve_digital_map()
        self.embed_utils = EmbedUtils()
        self.movements = {}  # Dictionary to store movements in memory
        self.load_movements()  # Load movements when the bot starts
        self.update_movements.start()  # Start the background task

    def load_movements(self):
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        if not sheet_values:
            print("Error: Could not retrieve data for 'Movements'.")
            return

        for row in sheet_values[1:]:
            movement_uid, player, movement_type, army, navy, siege, intent, path, current_hex, minutes_per_hex, minutes_since_last_hex = row
            
            self.movements[movement_uid] = {
                'player': player,
                'movement_type': movement_type,
                'army': army,
                'navy': navy,
                'siege': siege,
                'intent': intent,
                'path': path,
                'current_hex': current_hex,
                'minutes_per_hex': int(minutes_per_hex),
                'minutes_since_last_hex': int(minutes_since_last_hex)
            }


    @tasks.loop(minutes=1)  # This will run every minute
    async def update_movements(self):
        # Fetch the latest sheet data before making updates
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        if not sheet_values:
            print("Error: Could not retrieve data for 'Movements'.")
            return
        
        # Create a set of movement UIDs from the sheet
        sheet_uids = {row[0] for row in sheet_values[1:]}
        
        # Add any new movements from the sheet to in-memory storage
        for row in sheet_values[1:]:
            movement_uid = row[0]
            print(f"row:\n{row}")
            if movement_uid not in self.movements:
                path = row[8].split(",")  # Convert path string to list
                self.movements[movement_uid] = {
                    'player': row[1],
                    'movement_type': row[2],
                    'commanders': row[3],
                    'army': row[4],
                    'navy': row[5],
                    'siege': row[6],
                    'intent': row[7],
                    'path': path,
                    'current_hex': row[9],
                    'minutes_per_hex': int(row[10]),
                    'minutes_since_last_hex': int(row[11]),
                }
        
        # Update in-memory movements and prepare data for the sheet
        updated_data = []
        for movement_uid, movement in self.movements.items():
            path = movement['path']
            current_hex = movement['current_hex']
            minutes_per_hex = movement['minutes_per_hex']
            minutes_since_last_hex = movement['minutes_since_last_hex']
            
            # Increment minutes since last hex
            minutes_since_last_hex += 1
            
            # Check if it's time to move to the next hex
            if minutes_since_last_hex >= minutes_per_hex:
                print(path)
                print(path.index(current_hex))
                current_hex_index = path.index(current_hex)
                if current_hex_index < len(path) - 1:
                    current_hex = path[current_hex_index + 1]
                    minutes_since_last_hex = 0
                else:
                    await self.complete_movement(movement_uid)
                    return
            
            # Update the movement in memory
            self.movements[movement_uid].update({
                'current_hex': current_hex,
                'minutes_since_last_hex': minutes_since_last_hex,
            })

            # Prepare updated data for the sheet
            updated_data.append([
                movement_uid,
                movement['player'],
                movement['movement_type'],
                movement['commanders'],
                movement['army'],
                movement['navy'],
                movement['siege'],
                movement['intent'],
                ",".join(path),
                current_hex,
                minutes_per_hex,
                minutes_since_last_hex,
            ])
        
        # Merge updated data with any rows from the sheet that aren't in memory
        for row in sheet_values[1:]:
            if row[0] not in self.movements:
                updated_data.append(row)
        
        # Write the merged data back to the sheet
        self.local_sheet_utils.update_sheet_by_name("Movements", [sheet_values[0]] + updated_data)

    async def complete_movement(self, movement_uid):
        data = self.movements[movement_uid]
        destination = await self.search_map_for_destination(data['current_hex'])
        
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error: Unable to fetch channel with ID {channel_id}. Exception: {e}")
                return

        # Send the movement completion message
        await channel.send(f"- Locals spot {'Ships' if data['navy'] != 'None' else 'Men'} arriving at {destination}. They intend to: {data['intent']}")

        # Extract numeric user ID
        try:
            user_id = int(re.sub(r'[^\d]', '', data['player']))
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            print(f"Error: Invalid user ID format in data['player']: {data['player']}")
            return
        except discord.errors.HTTPException as e:
            print(f"Error: Unable to fetch user with ID {user_id}. Exception: {e}")
            return

        # Notify the player
        await user.send(
            "**Your movement is finished pookie :)**",
            embed=self.embed_utils.set_info_embed_from_list(
                [
                    "Embed Title",
                    "Intent",
                    "Commanders",
                    "Army",
                    "Navy",
                    "Siege",
                    "Starting Hex ID",
                    "Destination",
                    "Path of Hex IDs",
                    "Minutes Per Hex"
                ],
                [
                    f"Movement from {data['path'][0]} to {destination}.",
                    data['intent'],
                    data['commanders'],
                    data['army'],
                    data['navy'],
                    data['siege'],
                    data['path'][0],
                    destination,
                    data['path'],
                    data['minutes_per_hex'],
                ],
            ),
        )

        # Remove the movement from memory
        if movement_uid in self.movements:
            del self.movements[movement_uid]

        # Update the sheet data
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        updated_rows = [sheet_values[0]]  # Keep the header row
        for row in sheet_values[1:]:
            if row[0] != movement_uid:
                updated_rows.append(row)

        self.local_sheet_utils.update_sheet_by_name("Movements", updated_rows)
    
    async def search_map_for_destination(self, destination):
        # Iterate through each row in the map data
        for row in self.map:
            if row["Hex"] == destination:
                # Check if a Holding Name exists for the current hex
                if row.get("Holding Name"):  # Ensure the key exists in the dictionary
                    return row["Holding Name"]
        
        # If no Holding Name is found, return the hex ID
        return destination

async def setup(bot):
    await bot.add_cog(MovementBackgroundController(bot))
