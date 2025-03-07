from utils.MovementUtils import MovementUtils
from utils.sheets.LocalSheetUtils import LocalSheetUtils
from utils.misc.EmbedUtils import EmbedUtils
from utils.pathfinding.PathfindingUtils import PathfindingUtils
from utils.misc.TemplateUtils import TemplateUtils
from utils.misc.CollectionUtils import CollectionUtils
import settings as settings
import discord
import time
import re
import random
import pandas as pd

class MovementService:
    def __init__(self, bot):
        self.bot = bot
        self.movement_utils = MovementUtils()
        self.local_sheet_utils = LocalSheetUtils()
        self.embed_utils = EmbedUtils()
        self.pathfinding_utils = PathfindingUtils()
        self.template_utils = TemplateUtils()
        self.collection_utils = CollectionUtils()

    async def create_template_movement(self, ctx): 
        template = await self.collection_utils.ask_question(
            ctx, self.bot,
            "**Send me the Movement Template now Pookie, Grrrr.**", str
        )
        if template is None:
            return False

        try:
            movement = self.template_utils.parse_movement_template(template)
        except ValueError:
            return False

        movement_type = "army" if movement.get("navy") == ['None'] else "fleet"

        # Pathfind
        path, terrain_values = self.pathfinding_utils.retrieve_movement_path(
            movement_type, movement.get("origin"),
            movement.get("destination"), movement.get("avoid")
        )

        if path is None:
            return False

        base_minutes_per_hex = self.movement_utils.get_minutes_per_hex(movement)

        # Calculate terrain mod minutes per hex
        terrain_mod_minutes_per_hex = base_minutes_per_hex * (sum(terrain_values)/len(terrain_values))

        movement_uid = f"{random.randint(0, 1000)}_{int(time.time())}"

        # Prepare data for sheet
        commanders = ', '.join(movement.get("commanders")) if movement.get("commanders") else "None"
        army = ', '.join(movement.get("army")) if movement.get("army") else "None"
        navy = ', '.join(movement.get("navy")) if movement.get("navy") else "None"
        siege = ', '.join(movement.get("siege")) if movement.get("siege") else "None"
        path_str = ', '.join(path) if path else "None"
        terrain_str = ', '.join(map(str, terrain_values)) if terrain_values else "None"

        success = await self.announce_departure(movement, movement_uid, path, terrain_values, base_minutes_per_hex, terrain_mod_minutes_per_hex, navy)
        if not success:
            return False

        # Create movement in sheet
        return self.local_sheet_utils.write_to_row(
            "Movements",
            [movement_uid, movement.get("player"), movement_type, commanders, army, navy, siege,
            movement.get("intent"), path_str, terrain_str, path[0] if path else "None", base_minutes_per_hex, 
            terrain_mod_minutes_per_hex, 0, movement.get("arrival")]
        )
    
    async def announce_departure(self, movement, uid, path, terrain_values, base_minutes_per_hex, terrain_mod_minutes_per_hex, navy):
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error fetching channel: {e}")
                return False
        
        total_minutes = len(path) * terrain_mod_minutes_per_hex
        message = movement.get("departure")
        if message == "None":
            await channel.send(f"- {'Ships' if navy != 'None' else 'Men'} depart {movement.get('origin')} || UID: {uid}, ETC: {total_minutes} minutes ||")
        else:
            await channel.send(f"- {message} || UID: {uid}, ETC: {total_minutes} minutes ||")

        try:
            user_id = int(re.sub(r'[^\d]', '', movement.get("player")))
            user = await self.bot.fetch_user(user_id)
        except Exception as e:
            print(f"Error fetching user: {e}")
            return False

        try:
            await user.send(
                "**Movement queued successfully**",
                embed=self.embed_utils.set_info_embed_from_list(
                    ["Movement UID", "Path", "Base Minutes per Hex", "Terrain Mod Minutes per Hex"],
                    [uid, " → ".join(path), base_minutes_per_hex, terrain_mod_minutes_per_hex]
                    )
            )
        except discord.errors.Forbidden:
            print("Cannot DM user")
        return True

    def retrieve_all_movements(self):
        movements_df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if movements_df is None or movements_df.empty:
            return "No active movements"
            
        try:
            return "\n".join(
                f"UID: {row['Movement UID']}, Player: {row['Player']}, Type: {row['Movement Type']}, "
                f"Terrain Values: {row['Terrain Values']}, Minutes/Hex: {row['Terrain Mod Minutes per Hex']}, Message: {row['Message']}"
                for _, row in movements_df.iterrows()
            )
        except KeyError as e:
            print(f"Missing column: {e}")
            return "Error retrieving movements"

    def retrieve_user_movements(self, user_id):
        movements_df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if movements_df is None or movements_df.empty:
            return "No movements found"
            
        user_movements = movements_df[movements_df['Player'] == user_id]
        if user_movements.empty:
            return "No movements for this user"
            
        try:
            return "\n".join(
                f"UID: {row['Movement UID']}, Path: [{row['Path']}], Terrain: [{row['Terrain Values']}], Intent: {row['Intent']}"
                for _, row in user_movements.iterrows()
            )
        except KeyError as e:
            print(f"Missing column: {e}")
            return "Error retrieving user movements"

    def retrieve_movement(self, uid):
        movements_df = self.local_sheet_utils.get_sheet_by_name("Movements")
        if movements_df is None or movements_df.empty:
            return None
        
        movement = movements_df[movements_df['Movement UID'] == uid]
        if movement.empty:
            return None
        
        row = movement.iloc[0]  # row is a Pandas Series

        # Convert Series into column names and values
        column_headings = list(row.index)  # Extract column names
        data = list(row.values)  # Extract corresponding values

        return self.embed_utils.set_info_embed_from_list(column_headings, data)

    def retreat_movement(self, uid):
        movements_df = self.local_sheet_utils.get_sheet_by_name("Movements")
        print(movements_df)
        if movements_df is None or movements_df.empty:
            return False

        mask = movements_df['Movement UID'] == uid
        print(mask)
        if not mask.any():
            return False

        row = movements_df.loc[mask].iloc[0]
        # Split on comma then strip whitespace
        path = [p.strip() for p in row['Path'].split(',')]
        current_hex = row['Current Hex']

        print(current_hex)
        print(path)
        if current_hex not in path:
            return False

        current_index = path.index(current_hex)
        new_path = path[current_index::-1]
        new_terrain = [t.strip() for t in row['Terrain Values'].split(',')][current_index::-1]

        movements_df.loc[mask, 'Path'] = ', '.join(new_path)
        movements_df.loc[mask, 'Terrain Values'] = ', '.join(new_terrain)
        movements_df.loc[mask, 'Intent'] = 'Retreat'
        movements_df.loc[mask, 'Minutes since last Hex'] = 0

        print(movements_df)
        
        # Convert the DataFrame to list-of-lists (header first) before updating.
        data_list = [movements_df.columns.tolist()] + movements_df.values.tolist()
        print(data_list)
        return self.local_sheet_utils.update_sheet_by_name("Movements", data_list)

    def cancel_movement(self, uid):
        movements_df = self.local_sheet_utils.get_sheet_by_name("Movements")
        print(movements_df)
        if movements_df is None:
            return False

        original_count = len(movements_df)
        movements_df = movements_df[movements_df['Movement UID'] != uid]
        print(movements_df)
        if len(movements_df) == original_count:
            return False

        return self.local_sheet_utils.update_sheet_by_name("Movements", movements_df)

    async def retrieve_path(self, ctx, origin, destination, avoid):
        movement_type = await self.collection_utils.ask_question(
            ctx, self.bot,
            "Is the movement for an **army** or a **fleet**?", str
        )

        siege = await self.collection_utils.ask_question(
            ctx, self.bot,
            "Does the movement have any Siege? **(y/n)**", str
        )

        # If either question wasn't answered properly
        if not movement_type or siege is None:
            await ctx.send("Are you retarded? I even highlighted the right answers :sob:")
            return None, None  # Return a tuple with `None` values

        # Determine base minutes per hex based on composition
        if movement_type == "fleet":
            base_minutes_per_hex = 1
        else:
            base_minutes_per_hex = 2 if siege.lower() in ["n", "no"] else 3

        # Retrieve the movement path
        path, terrain_values = self.pathfinding_utils.retrieve_movement_path(
            movement_type, origin,
            destination, avoid
        )
        average_terrain_mod = sum(terrain_values)/len(terrain_values)

        if not path:  # If pathfinding failed, return empty path
            return [], 0

        # Calculate terrain mod minutes per hex
        terrain_mod_minutes_per_hex = base_minutes_per_hex * average_terrain_mod

        # Return the path and total time (impacted by terrain mod minutes per hex)
        return path, len(path) * terrain_mod_minutes_per_hex
        
    def retrieve_hex_info(self, hex_id):
        map_df = self.local_sheet_utils.get_sheet_by_name("Map")
        if map_df is None or map_df.empty:
            return None
            
        hex_data = map_df[map_df['Hex'] == hex_id]
        if hex_data.empty:
            return None
            
        row = hex_data.iloc[0]
        return self.embed_utils.create_hex_embed(row)