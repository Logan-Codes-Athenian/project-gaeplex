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

        try:
            movement = self.template_utils.parse_movement_template(template)
        except ValueError:
            return False

        print('-' * 150)
        print(movement)

        movement_type = "army" if movement.get("navy") == ['None'] else "fleet"

        # Pathfind.
        path = self.pathfinding_utils.retrieve_movement_path(
            movement_type, movement.get("origin"),
            movement.get("destination"), movement.get("avoid")
        )

        # Determine minutes per tile based on composition.
        if movement.get("navy"):
            minutes_per_tile = 1
        else:
            minutes_per_tile = 2 if movement.get("siege") is None else 3

        movement_uid = f"{movement.get('origin')}_{int(time.time())}"

        # Prepare list fields as comma-separated strings
        commanders = ', '.join(movement.get("commanders")) if movement.get("commanders") else "None"
        army = ', '.join(movement.get("army")) if movement.get("army") else "None"
        navy = ', '.join(movement.get("navy")) if movement.get("navy") else "None"
        siege = ', '.join(movement.get("siege")) if movement.get("siege") else "None"
        path_str = ', '.join(path) if path else "None"

        success = await self.announce_departure(ctx, movement, movement_uid, path, minutes_per_tile)
        if not success:
            return False

        # Create Movement in Sheets.
        return self.local_sheet_utils.write_to_row(
            "Movements",
            [movement_uid, movement.get("player"), movement_type, commanders, army, navy, siege,
            movement.get("intent"), path_str, path[0] if path else "None", minutes_per_tile, 0,
            movement.get("arrival")]
        )
    
    async def announce_departure(self, ctx, movement, uid, path, minutes_per_tile):
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error: Unable to fetch channel with ID {channel_id}. Exception: {e}")
                return False

        message = movement.get("departure")
        # Send the movement completion message
        if message == "None":
            await channel.send(f"- {'Ships' if movement.get('navy') != 'None' else 'Men'} are spotted departing {movement.get('origin')}\nMovement UID: {uid}")
        else:
            await channel.send(f"- {message}\nMovement UID: {uid}")

        # Extract numeric user ID
        try:
            user_id = int(re.sub(r'[^\d]', '', movement.get("player")))
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            print(f"Error: Invalid user ID format in data['player']: {movement.get('player')}")
            return False
        except discord.errors.HTTPException as e:
            print(f"Error: Unable to fetch user with ID {user_id}. Exception: {e}")
            return False

        # Notify the player
        await user.send(
            "**Your movement has been queued Pookie. It will begin on Unpause. :)**",
            embed=self.embed_utils.set_info_embed_from_list(
                [
                    "Embed Title",
                    "Intent",
                    "Commanders",
                    "Army",
                    "Navy",
                    "Siege",
                    "Origin",
                    "Destination",
                    "Path of Hex IDs",
                    "Minutes Per Hex",
                    "Movement UID"
                ],
                [
                    f"Movement from {movement.get('origin')} to {movement.get('destination')}.",
                    movement.get("intent"),
                    movement.get("commanders"),
                    movement.get("army"),
                    movement.get("navy"),
                    movement.get("siege"),
                    movement.get("origin"),
                    movement.get("destination"),
                    path,
                    minutes_per_tile,
                    uid
                ],
            ),
        )
        return True
    
    def retrieve_all_movements(self):
        movement_info = []

        # Retrieve data from the "Movements" sheet
        movements = self.local_sheet_utils.get_sheet_by_name("Movements")
        
        # Check if data was retrieved successfully
        if not movements:
            return False
        
        # Extract header and rows
        header = movements[0]  # The first row is the header
        rows = movements[1:]   # Remaining rows contain data

        # Get indices for the required columns
        try:
            uid_index = header.index("Movement UID")
            player_index = header.index("Player")
            path_index = header.index("Path")
            intent_index = header.index("Intent")
        except ValueError:
            return False

        # Iterate through the rows and extract relevant information
        for row in rows:
            try:
                movement_uid = row[uid_index]
                player = row[player_index]
                path = row[path_index]
                intent = row[intent_index]
                # Format and append the movement information
                movement_info.append(f"UID: {movement_uid}, Player: {player}, Path: [{path}], Intent: {intent}")
            except IndexError:
                print(f"Warning: Skipped a row due to missing data - {row}")

        # Combine all rows into a single string with newline separators
        return "\n".join(movement_info)
    
    def retrieve_movement(self, uid):
        # Retrieve data from the "Movements" sheet
        movements = self.local_sheet_utils.get_sheet_by_name("Movements")
        
        # Check if data was retrieved successfully
        if not movements:
            return False
        
        # Extract header and rows
        header = movements[0]  # The first row is the header
        rows = movements[1:]   # Remaining rows contain data

        # Get indices for the required columns
        try:
            uid_index = header.index("Movement UID")
            player_index = header.index("Player")
            movement_type_index = header.index("Movement Type")
            commanders_index = header.index("Commanders")
            army_index = header.index("Army")
            navy_index = header.index("Navy")
            siege_index = header.index("Siege")
            intent_index = header.index("Intent")
            path_index = header.index("Path")
            current_hex_index = header.index("Current Hex")
            minutes_per_hex_index = header.index("Minutes per Hex")
            minutes_since_last_hex_index = header.index("Minutes since last Hex")
            message_index = header.index("Message")
        except ValueError:
            return False

        # Iterate through the rows and extract relevant information
        for row in rows:
            try:
                if row[uid_index] == uid:
                    # Format and return the movement embed
                    return self.embed_utils.set_info_embed_from_list(
                        [
                            "Embed Title",
                            "Player",
                            "Movement Type",
                            "Intent",
                            "Commanders",
                            "Army",
                            "Navy",
                            "Siege",
                            "Path of Hex IDs",
                            "Current Hex ID",
                            "Minutes Per Hex",
                            "Minutes Since Last Hex",
                            "Arrival Message"
                        ],
                        [
                            f"Retrieved Movement: {uid}",
                            row[player_index],
                            row[movement_type_index],
                            row[intent_index],
                            row[commanders_index],
                            row[army_index],
                            row[navy_index],
                            row[siege_index],
                            row[path_index],
                            row[current_hex_index],
                            row[minutes_per_hex_index],
                            row[minutes_since_last_hex_index],
                            row[message_index]
                        ],
                    )
            except IndexError:
                print(f"Error: missing data - {row}")
                return False
            
        return False

                    