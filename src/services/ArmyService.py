import discord
import time
import random

from utils.sheets.LocalSheetUtils import LocalSheetUtils
from utils.misc.TemplateUtils import TemplateUtils
from utils.misc.CollectionUtils import CollectionUtils
from utils.misc.EmbedUtils import EmbedUtils

class ArmyService:
    def __init__(self, bot):
        self.bot = bot
        self.collection_utils = CollectionUtils()
        self.template_utils = TemplateUtils()
        self.local_sheet_utils = LocalSheetUtils()
        self.embed_utils = EmbedUtils()

    async def create_template_army(self, ctx): 
        template = await self.collection_utils.ask_question(
            ctx, self.bot,
            "**Send the Completed Army Template:**", str
        )
        if template is None:
            return False

        try:
            army = self.template_utils.parse_army_template(template)
        except ValueError:
            return False

        army_uid = f"{random.randint(0, 1000)}_{int(time.time())}"

        # Prepare data for sheet
        player = army.get("player")
        current = army.get("current") # Get the current hex from template
        commanders = ', '.join(army.get("commanders")) if army.get("commanders") else "None"
        troops = ', '.join(army.get("troops")) if army.get("troops") else "None"
        navy = ', '.join(army.get("navy")) if army.get("navy") else "None"
        siege = ', '.join(army.get("siege")) if army.get("siege") else "None"
        status = "Stationary" # Defaults to Stationary. Can be defending, moving, ambushing, raiding, besieging, disembarking, embarking

        # Create army in sheet
        return self.local_sheet_utils.write_to_row(
            "Armies",
            [army_uid, player, current, commanders, troops, navy, siege, status]
        )
    
    def retrieve_all_armies(self):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return "No armies found."
            
        try:
            return "\n".join(
                f"UID: {row['Army UID']}, Player: {row['Player']}, Current Hex: {row['Current Hex']}, Status: {row['Status']}"
                for _, row in armies_df.iterrows()
            )
        except KeyError as e:
            print(f"Missing column: {e}")
            return "Error retrieving armies."
        
    def retrieve_user_armies(self, user_id):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return "No armies found."
            
        user_armies = armies_df[armies_df['Player'] == user_id]
        if user_armies.empty:
            return "No armies for this user"
            
        try:
            return "\n".join(
                f"UID: {row['Army UID']}, Player: {row['Player']}, Current Hex: {row['Current Hex']}, Status: {row['Status']}"
                for _, row in user_armies.iterrows()
            )
        except KeyError as e:
            print(f"Missing column: {e}")
            return "Error retrieving user armies."
        
    def retrieve_army(self, uid):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return None
        
        army = armies_df[armies_df['Army UID'] == uid]
        if army.empty:
            return None
        
        row = army.iloc[0]  # row is a Pandas Series

        # Convert Series into column names and values
        column_headings = list(row.index)  # Extract column names
        data = list(row.values)  # Extract corresponding values

        return self.embed_utils.set_info_embed_from_list(column_headings, data)
    
    def retrieve_user_army(self, army_uid, user_id):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return None

        army = armies_df[armies_df['Army UID'] == army_uid]
        if army.empty:
            return None

        row = army.iloc[0]  # row is a Pandas Series

        # Verify the user_id matches the 'Player' field in the movement
        if row['Player'] != user_id:
            return None

        # Convert the Series into column names and values for the embed
        column_headings = list(row.index)
        data = list(row.values)
        
        return self.embed_utils.set_info_embed_from_list(column_headings, data)

    def delete_army(self, uid):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None:
            return False

        original_count = len(armies_df)
        armies_df = armies_df[armies_df['Army UID'] != uid]
        if len(armies_df) == original_count:
            return False

        return self.local_sheet_utils.update_sheet_by_name("Armies", armies_df)

    def change_army_status(self, uid, new_status):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return False

        # Locate the row where the 'Army UID' matches the given uid
        row_index = armies_df.index[armies_df['Army UID'] == uid]
        if row_index.empty:
            return False

        # Update the 'Status' column for the matching row(s)
        armies_df.loc[row_index, 'Status'] = new_status

        # Write the updated DataFrame back to the CSV
        return self.local_sheet_utils.update_sheet_by_name("Armies", armies_df)

    def announce_army_status_change(self, uid, status):
        pass