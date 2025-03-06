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
        df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if df is None or df.empty:
            print("Error: Could not retrieve data for 'Movements'.")
            return

        for _, row in df.iterrows():
            uid = row["Movement UID"]
            player = row["Player"]
            movement_type = row["Movement Type"]
            commanders = row["Commanders"]
            army = row["Army"]
            navy = row["Navy"]
            siege = row["Siege"]
            intent = row["Intent"]
            path = row["Path"]
            terrain_values = row["Terrain Values"]
            current_hex = row["Current Hex"]
            base_minutes_per_hex = row["Base Minutes per Hex"]
            terrain_mod_minutes_per_hex = row["Terrain Mod Minutes per Hex"]
            minutes_since_last_hex = row["Minutes since last Hex"]
            message = row["Message"]

            self.movements[uid] = {
                'player': player,
                'movement_type': movement_type,
                'commanders': commanders,
                'army': army,
                'navy': navy,
                'siege': siege,
                'intent': intent,
                'path': [hex.strip() for hex in str(path).split(",")],
                'terrain_values': [val.strip() for val in str(terrain_values).split(",")],
                'current_hex': str(current_hex).strip(),
                'base_minutes_per_hex': int(base_minutes_per_hex),
                'terrain_mod_minutes_per_hex': int(terrain_mod_minutes_per_hex),
                'minutes_since_last_hex': int(minutes_since_last_hex),
                'message': message
            }

    @tasks.loop(minutes=1)  # This will run every minute
    async def update_movements(self):
        if self.is_paused():
            return

        # Retrieve latest sheet data (as a DataFrame)
        df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if df is None or df.empty:
            print("Error: Could not retrieve data for 'Movements'.")
            return

        # Update in-memory data from the DataFrame
        self.update_in_memory_data_from_sheet(df)

        updated_data = []
        # Iterate through your in-memory movements dictionary
        for uid, movement in self.movements.items():
            # Ensure path and terrain_values are lists of strings
            path = [hex.strip() for hex in movement['path']]
            # Note: if terrain_values is already a list, no need to split it again
            terrain_values = movement['terrain_values']
            current_hex = movement['current_hex'].strip()
            terrain_mod_minutes_per_hex = movement['terrain_mod_minutes_per_hex']
            minutes_since_last_hex = movement['minutes_since_last_hex'] + 1  # Increment minutes

            # Check if it's time to move to the next hex
            if minutes_since_last_hex >= terrain_mod_minutes_per_hex:
                try:
                    current_index = path.index(current_hex)
                except ValueError:
                    print(f"Warning: {current_hex} not found in path for movement {uid}")
                    continue

                if current_index < len(path) - 1:
                    current_hex = path[current_index + 1]
                    minutes_since_last_hex = 0
                else:
                    await self.complete_movement(uid)
                    return  # Optionally, exit early if a movement is completed

            # Update the movement in memory
            self.movements[uid].update({
                'current_hex': current_hex,
                'minutes_since_last_hex': minutes_since_last_hex,
            })

            # Prepare updated data for the sheet as a list (matching the CSV columns)
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
                ",".join(terrain_values) if isinstance(terrain_values, list) else terrain_values,
                current_hex,
                movement['base_minutes_per_hex'],
                movement['terrain_mod_minutes_per_hex'],
                minutes_since_last_hex,
                movement['message']
            ])

        # Merge updated data with any rows from the DataFrame that aren't in memory
        header = list(df.columns)
        # Convert the DataFrame to a list of dictionaries for easier lookup
        sheet_rows = df.to_dict(orient="records")
        for row in sheet_rows:
            uid = row["Movement UID"]
            if uid not in self.movements:
                # Convert the dictionary back to a list matching the header order
                merged_row = [row.get(col, "") for col in header]
                updated_data.append(merged_row)

        # Write the header plus updated rows back to the sheet
        all_data = [header] + updated_data
        self.local_sheet_utils.update_sheet_by_name("Movements", all_data)

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

        # Send the movement completion message in the channel
        if data['message'] == "None":
            message_text = (
                f"- Locals spot {'Ships' if data['navy'] != 'None' else 'Men'} arriving at {destination}. "
                f"They intend to: {data['intent']} || {uid} ||"
            )
        else:
            message_text = f"- {data['message']} || {uid} ||"
        await channel.send(message_text)

        # Notify the player via DM
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
            embed = self.embed_utils.set_info_embed_from_list(
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
                    "Terrain Values for Hexes along Path",
                    "Base Minutes Per Hex",
                    "Terrain Mod Minutes Per Hex",
                    "Movement UID"
                ],
                [
                    f"Movement from {data['path'][0]} to {destination}.",
                    data['intent'],
                    data.get('commanders', 'N/A'),
                    data['army'],
                    data['navy'],
                    data['siege'],
                    data['path'][0],
                    destination,
                    data['path'],
                    data['terrain_values'],
                    data['base_minutes_per_hex'],
                    data['terrain_mod_minutes_per_hex'],
                    uid
                ]
            )
            await user.send("**Your movement is finished pookie :)**", embed=embed)
        except discord.errors.Forbidden:
            print(f"Can't DM user: {user}.")

        # Remove the movement from memory
        if uid in self.movements:
            del self.movements[uid]

        # Update the sheet: remove the row with this uid
        df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if df is None or df.empty:
            return

        # Remove duplicate header rows if any
        if "Movement UID" in df.columns:
            df = df[df["Movement UID"] != "Movement UID"]

        # Filter out the row with the given UID
        updated_df = df[df["Movement UID"] != uid]

        # Convert the updated DataFrame back to a list of lists (header + data)
        header = list(updated_df.columns)
        data_rows = updated_df.values.tolist()
        all_data = [header] + data_rows
        self.local_sheet_utils.update_sheet_by_name("Movements", all_data)
    
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

        # Check if DataFrame is empty or missing expected columns
        if sheet_values is None or sheet_values.empty:
            print("Error: Could not retrieve data for 'Status'.")
            return True

        # Ensure the DataFrame has at least one row and one column before accessing
        if sheet_values.shape[0] == 0 or sheet_values.shape[1] == 0:
            print("Error: 'Status' sheet is missing data.")
            return True

        # Access the first value safely
        status = sheet_values.iloc[0, 0]  # Use `iloc` for position-based indexing

        return status != "Unpaused"
    
    def update_in_memory_data_from_sheet(self, df):
        current_uids_in_sheet = set()
        for _, row in df.iterrows():
            uid = row["Movement UID"]
            current_uids_in_sheet.add(uid)
            
            if uid not in self.movements:
                path_str = str(row["Path"]).strip()
                terrain_values_str = str(row["Terrain Values"]).strip()
                # Remove surrounding brackets if they exist.
                if terrain_values_str.startswith("[") and terrain_values_str.endswith("]"):
                    terrain_values_str = terrain_values_str[1:-1]
                
                self.movements[uid] = {
                    'player': row["Player"],
                    'movement_type': row["Movement Type"],
                    'commanders': row["Commanders"],
                    'army': row["Army"],
                    'navy': row["Navy"],
                    'siege': row["Siege"],
                    'intent': row["Intent"],
                    'path': [hex.strip() for hex in path_str.split(",")],
                    'terrain_values': [val.strip() for val in terrain_values_str.split(",")],
                    'current_hex': str(row["Current Hex"]).strip(),
                    'base_minutes_per_hex': int(row["Base Minutes per Hex"]),
                    'terrain_mod_minutes_per_hex': int(row["Terrain Mod Minutes per Hex"]),
                    'minutes_since_last_hex': int(row["Minutes since last Hex"]),
                    'message': row["Message"]
                }
            else:
                # Update existing movement if necessary (for example, if intent is "Retreat")
                intent = row["Intent"]
                if intent == "Retreat":
                    new_path = str(row["Path"]).strip()
                    terrain_values = str(row["Terrain Values"]).strip()
                    # Remove surrounding brackets from terrain values.
                    if terrain_values.startswith("[") and terrain_values.endswith("]"):
                        terrain_values = terrain_values[1:-1]
                        
                    new_path_list = [hex.strip() for hex in new_path.split(",")]
                    terrain_values_list = [val.strip() for val in terrain_values.split(",")]

                    # Reverse the path and terrain values.
                    reversed_path = new_path_list[::-1]
                    reversed_terrain_values = terrain_values_list[::-1]

                    current_hex = str(row["Current Hex"]).strip()
                    reversed_path[0] = current_hex
                    # Do NOT override reversed_terrain_values[0]

                    self.movements[uid].update({
                        'path': reversed_path,
                        'terrain_values': reversed_terrain_values,
                        'intent': intent,
                        'minutes_since_last_hex': 0,
                        'message': row["Message"]
                    })

        # Remove deleted movements from memory.
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
            current_hex = row[10]  # Column index for current_hex in updated_data
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