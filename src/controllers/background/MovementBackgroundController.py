import re
import discord
import pandas as pd
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
        self.collisions = {} # hex_id -> set(of army_uids) GM has been notified on
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
            army_uid = row["Army UID"]
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
                'army_uid': army_uid,
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
        # Iterate over a static copy of movements to avoid dictionary size changes
        for uid, movement in list(self.movements.items()):
            # Ensure path and terrain_values are lists of strings
            path = [hex.strip() for hex in movement['path']]
            terrain_values = movement['terrain_values']
            current_hex = movement['current_hex'].strip()
            terrain_mod_minutes_per_hex = movement['terrain_mod_minutes_per_hex']
            minutes_since_last_hex = movement['minutes_since_last_hex'] + 1  # Increment minutes

            self.update_army_position(movement['army_uid'], current_hex, "Moving")

            # Check if it's time to move to the next hex
            if minutes_since_last_hex >= terrain_mod_minutes_per_hex:
                try:
                    current_index = path.index(current_hex)
                except ValueError:
                    print(f"Warning: {current_hex} not found in path for movement {uid}")
                    continue

                if current_index < len(path) - 2:
                    # Move to the next hex in the path.
                    current_hex = path[current_index + 1]
                    minutes_since_last_hex = 0
                elif current_index == len(path) - 2:  # Final hex condition.
                    await self.complete_movement(uid)
                    return  
                    # Changed from Continue, since i would need to reload data from sheet to memory.
                    # This is done at the start of this method...maybe look into as an improvement.

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
                movement['army_uid'],
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
        sheet_rows = df.to_dict(orient="records")
        for row in sheet_rows:
            uid = row["Movement UID"]
            if uid not in self.movements:
                merged_row = [row.get(col, "") for col in header]
                updated_data.append(merged_row)

        all_data = [header] + updated_data
        await self.check_for_army_collision(updated_data)
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
        print(f" {'===='*50} {data['message']}")
        msg = data['message']
        if pd.isna(msg):

            has_navy = True if data['navy'] != "['nan']" else False
            unit_type = 'Ships' if has_navy else 'Men'
            message_text = (
                f"- Locals spot {unit_type} arriving at {destination}. "
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
                    "Movement UID",
                    "Army UID"
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
                    uid,
                    data['army_uid']
                ]
            )
            await user.send("**Your movement is finished pookie :)**", embed=embed)
        except discord.errors.Forbidden:
            print(f"Can't DM user: {user}.")

        # Update the Army's position and status.
        self.update_army_position(data['army_uid'], destination, data['intent'])

        # Remove the movement from memory
        if uid in self.movements:
            del self.movements[uid]
            print(f"Movement {uid} removed from memory.")

        # Update the Movements CSV to permanently remove this movement
        df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if df is None or df.empty:
            print("**complete_movement Error: Movements sheet is empty.**")
            return

        print(f"Before filtering: {df}")
        df["Movement UID"] = df["Movement UID"].astype(str).str.strip()
        uid = str(uid).strip()
        df = df[df["Movement UID"] != uid]
        print(f"After filtering: {df}")

        try:
            self.local_sheet_utils.update_sheet_by_name("Movements", df)
            print(f"Successfully removed movement {uid} and updated Movements.csv.")
        except Exception as e:
            print(f"Error writing to Movements.csv: {e}")

    def update_army_position(self, army_uid, new_hex, new_status):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            print("Error: Could not retrieve Armies data.")
            return
        
        # Ensure both are strings for comparison
        armies_df['Army UID'] = armies_df['Army UID'].astype(str)
        army_uid = str(army_uid)

        # Locate the row(s) where the 'Army UID' matches the provided army_uid
        row_index = armies_df.index[armies_df['Army UID'] == army_uid]
        if row_index.empty:
            print(f"No matching army found for UID {army_uid}.")
            return

        # Update the army's current hex and status
        armies_df.loc[row_index, 'Current Hex'] = new_hex
        armies_df.loc[row_index, 'Status'] = new_status

        try:
            self.local_sheet_utils.update_sheet_by_name("Armies", armies_df)
            print(f"Updated Army {army_uid} with new hex {new_hex} and status {new_status}.")
        except Exception as e:
            print(f"Error updating army status: {e}")
        
    async def search_map_for_destination(self, destination):
        # Iterate through each row in the map data
        for row in self.map:
            if row["Hex"] == destination:
                holding = row.get("Holding Name")
                # Only return the holding name if it is not "FALSE" (i.e. a valid name)
                if holding and holding != "FALSE":
                    return holding
        # If no valid Holding Name is found, return the hex ID
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
                    'army_uid': row["Army UID"],
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
        """
        Includes both moving and stationary armies in collision detection.
        """
        hex_army_map = {}

        # 1. Moving armies from updated_data (Movements sheet)
        for row in updated_data:
            uid = row[3]  # Army UID
            hex_id = row[11]  # Current Hex
            hex_army_map.setdefault(hex_id, set()).add(uid)

        # 2. Include non-moving armies from Armies sheet
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is not None and not armies_df.empty:
            armies_df['Army UID'] = armies_df['Army UID'].astype(str)
            armies_df['Current Hex'] = armies_df['Current Hex'].astype(str)
            armies_df['Status'] = armies_df['Status'].astype(str)

            for _, row in armies_df.iterrows():
                uid = row["Army UID"]
                hex_id = row["Current Hex"]
                status = row["Status"].lower()

                if status not in ["moving"]:  # Only include non-moving units
                    hex_army_map.setdefault(hex_id, set()).add(uid)

        current_collisions = {}

        for hex_id, army_uids in hex_army_map.items():
            if len(army_uids) < 2:
                if hex_id in self.collisions:
                    await self.notify_gm_army_departure(hex_id, set(self.collisions[hex_id]), army_uids)
                    del self.collisions[hex_id]
                continue

            current_set = army_uids
            prev_set = self.collisions.get(hex_id, set())

            if not prev_set:
                await self.notify_gm_army_collision(hex_id, current_set)
            else:
                new_armies = current_set - prev_set
                if new_armies:
                    await self.notify_gm_army_collision(hex_id, current_set, initial=False)

            current_collisions[hex_id] = current_set

        self.collisions = current_collisions

    async def notify_gm_army_collision(self, hex_id, army_uids, initial: bool = True):
        try:
            gm = await self.bot.fetch_user(settings.GamemasterID)
        except Exception as e:
            print(f"Error fetching GM user: {e}")
            return

        if initial:
            title = f"🛡️ Army Collision Detected on {hex_id}"
            body = "Multiple armies have arrived on the same tile:\n"
        else:
            title = f"➕ Additional Army Joined Collision on {hex_id}"
            body = "Updated list of armies on the tile:\n"

        status_map = self.get_army_status_map()

        lines = []
        for uid in sorted(army_uids):
            status = status_map.get(uid, "Unknown")
            lines.append(f"- {uid} ({status})")

        body += "\n".join(lines)

        try:
            await gm.send(f"**{title}**\n```{body}```")
        except discord.errors.Forbidden:
            print(f"Could not DM GM ({settings.GamemasterID}).")

    async def notify_gm_army_departure(self, hex_id, previous_set, current_set):
        try:
            gm = await self.bot.fetch_user(settings.GamemasterID)
        except Exception as e:
            print(f"Error fetching GM user: {e}")
            return

        departed = previous_set - current_set
        if not departed:
            return

        title = f"➖ Army Departed Collision on {hex_id}"
        body = "Some armies have left this tile.\n\n"

        status_map = self.get_army_status_map()

        body += "❌ Departed:\n"
        body += "\n".join(f"- {uid} ({status_map.get(uid, 'Unknown')})" for uid in sorted(departed))

        if current_set:
            body += "\n\n✅ Still present:\n"
            body += "\n".join(f"- {uid} ({status_map.get(uid, 'Unknown')})" for uid in sorted(current_set))
        else:
            body += "\n\nAll armies have now left this tile."

        try:
            await gm.send(f"**{title}**\n```{body}```")
        except discord.errors.Forbidden:
            print(f"Could not DM GM ({settings.GamemasterID}).")

    def get_army_status_map(self):
        """Return a dict of Army UID -> Status from the Armies sheet."""
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            print("Warning: Could not load Armies for status lookup.")
            return {}

        armies_df['Army UID'] = armies_df['Army UID'].astype(str)
        armies_df['Status'] = armies_df['Status'].astype(str)
        return dict(zip(armies_df['Army UID'], armies_df['Status']))

async def setup(bot):
    await bot.add_cog(MovementBackgroundController(bot))