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
            path = path.split(",")  # Convert path string to list
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
        updated_data = []
        
        for movement_uid, movement in self.movements.items():  # Use items() to access the UID and its data
            path = movement['path']
            current_hex = movement['current_hex']
            minutes_per_hex = movement['minutes_per_hex']
            minutes_since_last_hex = movement['minutes_since_last_hex']
            
            # Update Minutes Since Last Hex
            minutes_since_last_hex += 1  # Increment by 1 minute
            
            # Check if it's time to move to the next hex
            if minutes_since_last_hex >= minutes_per_hex:
                # Update Current Hex to the next one in the path
                current_hex_index = path.index(current_hex)
                
                if current_hex_index < len(path) - 1:
                    # Move to the next hex
                    current_hex = path[current_hex_index + 1]
                    minutes_since_last_hex = 0  # Reset minutes since last hex
                else:
                    # If it's the last hex, trigger complete movement
                    await self.complete_movement(movement_uid)  # Call the complete movement function
                    current_hex = path[-1]  # Ensure the last hex is set
                
            # Update the movement in memory
            self.movements[movement_uid].update({
                'current_hex': current_hex,
                'minutes_since_last_hex': minutes_since_last_hex
            })

            # Append the updated data to write it back to the sheet
            updated_data.append([
                movement_uid,
                movement['player'],
                movement['movement_type'],
                movement['army'],
                movement['navy'],
                movement['siege'],
                movement['intent'],
                ",".join(path),
                current_hex,
                minutes_per_hex,
                minutes_since_last_hex
            ])
        
        # Write the updated data back to the sheet
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        self.local_sheet_utils.update_sheet_by_name("Movements", [sheet_values[0]] + updated_data)

    async def complete_movement(self, movement_uid):
        data = self.movements[movement_uid]
        destination = await self.search_map_for_destination(data['current_hex'])
        channel = self.bot.get_channel(settings.MOVEMENTS_CHANNEL) #  Gets channel from settings.py
        await channel.send(f"- People spot {'Ships' if data['navy'] is not None else 'Men'} arrives at {destination}.\nThey intend to: {data['intent']}")
        
        # Send player embed dm of movement info.
        user = await self.bot.fetch_user(data['player'])
        await user.send(
                "**Your movement is finished pookie :)**",
                embed=self.embed_utils.set_info_embed_from_list(
                    [
                        "Embed Title",
                        "Intent",
                        "Army",
                        "Navy",
                        "Siege",
                        "Starting Hex ID", 
                        "Destination", 
                        "Path of Hex IDs",
                        "Minutes Per Hex", 
                        "Estimated Time to Completion"
                    ],
                    [
                        f"Movement from {data['path'][0]} to {destination}.", 
                        data['intent'],
                        data['army'],
                        data['navy'],
                        data['siege'],
                        data['path'][0],
                        destination, 
                        data['path'],
                        data['minutes_per_hex']
                    ]
                )
            )

        # Remove the movement from memory
        if movement_uid in self.movements:
            del self.movements[movement_uid]
        
        # Remove the movement from the sheet (Overwrite the entire sheet minus the completed movement)
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Movements")
        updated_rows = [sheet_values[0]]  # Keep the header row
        
        for row in sheet_values[1:]:
            if row[0] != movement_uid:  # Ensure to compare the UID in the first column
                updated_rows.append(row)
        
        # Overwrite the sheet without the completed movement
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
