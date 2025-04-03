import re
import discord
import settings as settings
from discord.ext import commands, tasks
from utils.pathfinding.PathfindingUtils import PathfindingUtils
from utils.sheets.LocalSheetUtils import LocalSheetUtils
from utils.misc.EmbedUtils import EmbedUtils

class StatusBackgroundController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path_finding_utils = PathfindingUtils()
        self.map = self.path_finding_utils.retrieve_digital_map()
        # Completion times in minutes for each status type.
        self.status_completion_time_in_mins = {"Siege": 180, "Raid": 1, "Embark": 30, "Disembark": 30} # TODO: Change raid to 120 again
        self.local_sheet_utils = LocalSheetUtils()
        self.embed_utils = EmbedUtils()
        self.armies = {}  # Dictionary to store armies in memory.
        self.load_armies()  # Load armies from the "Armies" sheet.
        self.load_status_timers()  # Load persisted status timers from StatusTimers.csv.
        self.update_status.start()  # Start the background update task.

    def load_armies(self):
        df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if df is None or df.empty:
            print("Error: Could not retrieve data for 'Armies'.")
            return

        for _, row in df.iterrows():
            uid = row["Army UID"]
            player = row["Player"]
            current_hex = row["Current Hex"]
            commanders = row["Commanders"]
            troops = row["Troops"]
            navy = row["Navy"]
            siege = row["Siege"]
            status = row["Status"]

            self.armies[uid] = {
                'player': player,
                'current_hex': current_hex,
                'commanders': commanders,
                'troops': troops,
                'navy': navy,
                'siege': siege,
                'status': status,
                'status_timer': self.status_completion_time_in_mins.get(status.title(), None)
            }

    def load_status_timers(self):
        """
        Loads in-progress status timers from the StatusTimers.csv sheet.
        For each row, if the army is already in memory, overwrite its timer.
        If the army is not in memory, discard that row.
        Then update the sheet with only the valid rows.
        """
        df = self.local_sheet_utils.get_sheet_by_name("StatusTimers")
        if df is None or df.empty:
            print("No status timers to load.")
            return

        # Filter only the rows for armies that exist in memory.
        valid_df = df[df["Army UID"].isin(self.armies.keys())]
        # Overwrite in-memory timers with persisted ones.
        for _, row in valid_df.iterrows():
            uid = row["Army UID"]
            try:
                timer = int(row["Status Timer"])
            except (ValueError, TypeError):
                continue
            self.armies[uid]["status_timer"] = timer

        # Update the StatusTimers sheet with only the valid rows.
        new_data = [list(valid_df.columns)] + valid_df.values.tolist()
        self.local_sheet_utils.update_sheet_by_name("StatusTimers", new_data)

    def save_status_timers(self):
        """
        Saves the current in-progress status timers to StatusTimers.csv.
        Only saves armies that have a valid (non-None) status timer.
        The format is: Army UID, Status, Status Timer.
        Here, we use the army's current status as the Status.
        """
        rows = [["Army UID", "Status", "Status Timer"]]
        for uid, army in self.armies.items():
            timer = army.get("status_timer")
            if timer is not None:
                rows.append([uid, army["status"], timer])
        self.local_sheet_utils.update_sheet_by_name("StatusTimers", rows)

    @tasks.loop(minutes=1)  # Runs every minute.
    async def update_status(self):
        if self.is_paused():
            return

        # Retrieve latest armies data (as a DataFrame) from the "Armies" sheet.
        df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if df is None or df.empty:
            print("Error: Could not retrieve data for 'Armies'.")
            return

        # Update in-memory data from the DataFrame.
        await self.update_in_memory_data_from_sheet(df)

        # Iterate through the in-memory armies.
        for uid, army in list(self.armies.items()):
            try:
                status_timer = int(army['status_timer'])
            except (ValueError, TypeError):
                continue

            # If timer reaches 0, complete the status.
            if status_timer == 0:
                await self.complete_status(uid)
            else:
                self.armies[uid]['status_timer'] = status_timer - 1

        # After processing, persist the updated timers.
        self.save_status_timers()

    async def complete_status(self, uid):
        army = self.armies[uid]
        current_hex = army['current_hex']

        # Resolve the channel.
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error: Unable to fetch channel with ID {channel_id}. Exception: {e}")
                return

        # Announce completion in the channel.
        message_text = f"- The Army: {uid} has finished {army['status']} in {current_hex}."
        await channel.send(message_text)

        # Notify the player via DM.
        try:
            user_id = int(re.sub(r'[^\d]', '', army['player']))
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            print(f"Error: Invalid user ID format in data['player']: {army['player']}")
            return
        except discord.errors.HTTPException as e:
            print(f"Error: Unable to fetch user with ID {user_id}. Exception: {e}")
            return

        try:
            embed = self.embed_utils.set_info_embed_from_list(
                [
                    "Embed Title",
                    "Commanders",
                    "Troops",
                    "Navy",
                    "Siege",
                    "Status"
                ],
                [
                    f"Army UID: {uid} finished {army['status']} at {current_hex}.",
                    army['commanders'],
                    army['troops'],
                    army['navy'],
                    army['siege'],
                    army['status']
                ]
            )
            await user.send(f"**Your army {uid} has finished {army['status']} pookie :)**", embed=embed)
        except discord.errors.Forbidden:
            print(f"Can't DM user: {user}.")

        # Update in-memory army status to Stationary and delete its timer.
        self.armies[uid]['status'] = "Stationary"
        self.armies[uid]['status_timer'] = None
        print(f"Army {uid} status set to Stationary in memory.")

        # Update the Armies sheet: set the row's 'Status' column to "Stationary"
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            return

        row_index = armies_df.index[armies_df['Army UID'] == uid]
        if row_index.empty:
            print(f"No matching army found for UID {uid}.")
        else:
            armies_df.loc[row_index, 'Status'] = "Stationary"
            try:
                self.local_sheet_utils.update_sheet_by_name("Armies", armies_df)
                print(f"Updated Army {uid} to Stationary status in sheet.")
            except Exception as e:
                print(f"Error updating army status: {e}")

    def is_paused(self):
        sheet_values = self.local_sheet_utils.get_sheet_by_name("Status")
        if sheet_values is None or sheet_values.empty:
            print("Error: Could not retrieve data for 'Status'.")
            return True
        if sheet_values.shape[0] == 0 or sheet_values.shape[1] == 0:
            print("Error: 'Status' sheet is missing data.")
            return True
        status = sheet_values.iloc[0, 0]
        return status != "Unpaused"

    async def update_in_memory_data_from_sheet(self, df):
        current_uids_in_sheet = set()
        for _, row in df.iterrows():
            uid = row["Army UID"]
            current_uids_in_sheet.add(uid)

            player = row["Player"]
            current_hex = row["Current Hex"]
            commanders = row["Commanders"]
            troops = row["Troops"]
            navy = row["Navy"]
            siege = row["Siege"]
            status = row["Status"]

            if uid not in self.armies:
                status_timer = self.status_completion_time_in_mins.get(status.title(), None)
                self.armies[uid] = {
                    'player': player,
                    'current_hex': current_hex,
                    'commanders': commanders,
                    'troops': troops,
                    'navy': navy,
                    'siege': siege,
                    'status': status,
                    'status_timer': status_timer
                }
                if status_timer is not None:
                        await self.announce_status_change(uid, status, status_timer)
            else:
                status_in_memory = self.armies[uid]['status']
                status_timer_in_memory = self.armies[uid]['status_timer']
                if status_in_memory != status:
                    new_status_timer = self.status_completion_time_in_mins.get(status.title(), None)
                    self.armies[uid].update({
                        'current_hex': current_hex,
                        'status': status,
                        'status_timer': new_status_timer
                    })
                    if status_timer_in_memory is not None:
                        await self.announce_status_interrupt(uid, status_in_memory)
                    if new_status_timer is not None:
                        await self.announce_status_change(uid, status, new_status_timer)
        self.remove_deleted_armies(current_uids_in_sheet)

    def remove_deleted_armies(self, current_uids_in_sheet):
        uids_to_delete = set(self.armies.keys()) - current_uids_in_sheet
        for uid in uids_to_delete:
            print(f"Removing deleted army from memory: {uid}")
            del self.armies[uid]

    async def announce_status_interrupt(self, uid, previous_status):
        """Announces that an army’s previous status was interrupted."""
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error: Unable to fetch channel with ID {channel_id}. Exception: {e}")
                return
        army = self.armies.get(uid)
        if not army:
            print(f"Error: Army {uid} not found in memory.")
            return
        location = army["current_hex"]
        message = f"- The Army **{uid}** has stopped **{previous_status}** early at **{location}**."
        await channel.send(message)

    async def announce_status_change(self, uid, new_status, status_timer):
        """Announces that an army has started a new status."""
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Error: Unable to fetch channel with ID {channel_id}. Exception: {e}")
                return
        army = self.armies.get(uid)
        if not army:
            print(f"Error: Army {uid} not found in memory.")
            return
        location = army["current_hex"]
        message = f"- The Army **{uid}** has started to **{new_status}** at **{location}**. It will complete in **{status_timer}** minutes."
        await channel.send(message)

async def setup(bot):
    await bot.add_cog(StatusBackgroundController(bot))
