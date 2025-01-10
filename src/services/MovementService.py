from utils.MovementUtils import MovementUtils
from utils.sheets.LocalSheetUtils import LocalSheetUtils
from utils.misc.EmbedUtils import EmbedUtils
from utils.pathfinding.PathfindingUtils import PathfindingUtils
from utils.misc.TemplateUtils import TemplateUtils
from utils.misc.CollectionUtils import CollectionUtils
import time

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
        
        print('-'*150)
        print(movement)

        movement_type = "army" if movement.get("navy") == ['None'] else "fleet"

        # Pathfind.
        path = self.pathfinding_utils.retrieve_movement_path(movement_type, movement.get("origin"), 
                                                             movement.get("destination"), movement.get("avoid"))

        # Determine minutes per tile based on composition.
        if movement.get("navy"):
            minutes_per_tile = 1
        else:
            minutes_per_tile = 2 if movement.get("siege") is None else 3

        movement_uid = f"{movement.get('player')}_{int(time.time())}"

        # Create Movement in Sheets.
        return self.local_sheet_utils.write_to_row(
            "Movements",
            [movement_uid, movement.get("player"), movement_type, movement.get("army"), movement.get("navy"), movement.get("siege"), 
             movement.get("intent"), path, path[0], minutes_per_tile, 0]
             )
        