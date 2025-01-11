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

                