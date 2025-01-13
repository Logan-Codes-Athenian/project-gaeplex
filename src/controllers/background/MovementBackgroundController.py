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
            uid, player, movement_type, commanders, army, navy, siege, intent, path, current_hex, minutes_per_hex, minutes_since_last_hex, message = row
            
            self.movements[uid] = {
                'player': player,
                'movement_type': movement_type,
                'commanders': commanders,
                'army': army,
                'navy': navy,
                'siege': siege,
                'intent': intent,
                'path': [hex.strip() for hex in path.split(",")],  # Clean path here
                'current_hex': current_hex.strip(),  # Clean current_hex here
                'minutes_per_hex': int(minutes_per_hex),
                'minutes_since_last_hex': int(minutes_since_last_hex),
                'message': message
            }


    @tasks.loop(minutes=1)  # This will run every minute
    async def update_movements(self):
        is_paused = self.is_paused()
        if is_paused: # If true, game is paused, do anything.
            return
        
                # Fetch the latest sheet data before making updates
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        if not sheet_values:
            print("Error: Could not retrieve data for 'Movements'.")
            return

        self.update_in_memory_data_from_sheet(sheet_values)
        
        # Update in-memory movements and prepare data for the sheet
        updated_data = []
        for uid, movement in self.movements.items():
            path = [hex.strip() for hex in movement['path']]  # Clean path
            current_hex = movement['current_hex'].strip()  # Clean current_hex
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
                    await self.complete_movement(uid)
                    return
            
            # Update the movement in memory
            self.movements[uid].update({
                'current_hex': current_hex,
                'minutes_since_last_hex': minutes_since_last_hex,
            })

            # Prepare updated data for the sheet
            updated_data.append([
                uid,
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
                movement['message']
            ])
        
        # Merge updated data with any rows from the sheet that aren't in memory
        for row in sheet_values[1:]:
            if row[0] not in self.movements:
                updated_data.append(row)

        await self.check_for_army_collision(updated_data)
        
        # Write the merged data back to the sheet
        self.local_sheet_utils.update_sheet_by_name("Movements", [sheet_values[0]] + updated_data)

    async def complete_movement(self, uid):
        data = self.movements[uid]
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
        if data['message'] == "None":
            await channel.send(f"- Locals spot {'Ships' if data['navy'] != 'None' else 'Men'} arriving at {destination}. They intend to: {data['intent']} || {uid} ||")
        else:
            await channel.send(f"- {data['message']} || {uid} ||")

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

        try: 
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
                        "Minutes Per Hex",
                        "Movement UID"
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
                        uid
                    ],
                ),
            )
        except discord.errors.Forbidden:
            print("Can't DM user.")

        # Remove the movement from memory
        if uid in self.movements:
            del self.movements[uid]

        # Update the sheet data
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        updated_rows = [sheet_values[0]]  # Keep the header row
        for row in sheet_values[1:]:
            if row[0] != uid:
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
    
    def is_paused(self):
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Status")
        if not sheet_values:
            print("Error: Could not retrieve data for 'Status'.")
            return True
        
        for row in sheet_values:
            if row[0] == "Game Status":
                if row[1] == "Unpaused":
                    return False
                else:
                    return True
        return True
    
    def update_in_memory_data_from_sheet(self, sheet_values):                
        # Update existing movements and add new movements from the sheet
        current_uids_in_sheet = set()
        for row in sheet_values[1:]:
            uid = row[0]
            current_uids_in_sheet.add(uid)
            
            # Add new movements or update existing ones
            if uid not in self.movements:
                path = row[8].split(",")  # Convert path string to list
                self.movements[uid] = {
                    'player': row[1],
                    'movement_type': row[2],
                    'commanders': row[3],
                    'army': row[4],
                    'navy': row[5],
                    'siege': row[6],
                    'intent': row[7],
                    'path': [hex.strip() for hex in path],  # Clean path here
                    'current_hex': row[9].strip(),  # Clean current_hex here
                    'minutes_per_hex': int(row[10]),
                    'minutes_since_last_hex': int(row[11]),
                    'message': row[12]
                }
            else:
                # Update existing movement if intent changes to "Retreat"
                intent = row[7]
                if intent == "Retreat":
                    new_path = row[8]
                    if isinstance(new_path, str):
                        new_path = [hex.strip() for hex in new_path.split(",")]  # Clean path
                    self.movements[uid]['path'] = new_path
                    self.movements[uid]['intent'] = intent
                    self.movements[uid]['minutes_since_last_hex'] = 0
                    self.movements[uid]['message'] = row[12]

        # Remove deleted movements
        self.remove_deleted_movements(current_uids_in_sheet)

    def remove_deleted_movements(self, current_uids_in_sheet):
        uids_to_delete = set(self.movements.keys()) - current_uids_in_sheet
        for uid in uids_to_delete:
            print(f"Removing deleted movement from memory: {uid}")
            del self.movements[uid]
    
    async def check_for_army_collision(self, updated_data):
        # Check for armies on the same hex and notify GameMaster
        hex_army_map = {}  # Map hex IDs to lists of army UIDs
        for row in updated_data:
            uid = row[0]
            current_hex = row[9]  # Column index for current_hex in updated_data
            if current_hex not in hex_army_map:
                hex_army_map[current_hex] = []
            hex_army_map[current_hex].append(uid)

        # Notify GameMaster about armies on the same hex
        for hex_id, army_uids in hex_army_map.items():
            if len(army_uids) > 1:  # Only notify if multiple armies are on the same hex
                await self.notify_gm_army_collision(hex_id, army_uids)

    async def notify_gm_army_collision(self, hex_id, army_uids):
        # Fetch the GameMaster's user and send a notification
        id = settings.GamemasterID
        try:
            user = await self.bot.fetch_user(id)
            await user.send(
                f"**Army Collision Notification**\n"
                f"``Multiple armies found on tile {hex_id}!``\n"
                f"Movement UIDs:\n- {', '.join(army_uids)}"
            )
        except discord.errors.HTTPException as e:
            print(f"Error: Unable to fetch user with ID {id}. Exception: {e}")

async def setup(bot):
    await bot.add_cog(MovementBackgroundController(bot))
