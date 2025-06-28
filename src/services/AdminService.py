import os
import pandas as pd
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils
from utils.sheets.LocalSheetUtils  import LocalSheetUtils
from utils.misc.EmbedUtils import EmbedUtils

class AdminService:
    def __init__(self):
        self.google_sheet_utils = GoogleSheetUtils()
        self.local_sheet_utils  = LocalSheetUtils()
        self.embed_utils        = EmbedUtils()

    def update_google_sheets(self):
        """ Push all local CSV sheets up to their Google Sheet counterparts. """
        sheet_names = ["Status", "Movements", "Armies", "StatusTimers"]
        for sheet in sheet_names:
            # 1) Read local CSV (with locking)
            df = self.local_sheet_utils.get_sheet_by_name(sheet)
            if df is None or df.empty:
                print(f"Error: {sheet} is empty or missing.")
                continue # Dataframe can be empty, so continue

            # 2) Prepare data list-of-lists (include header)
            payload = [df.columns.tolist()] + df.values.tolist()

            # 3) Overwrite Google Sheet
            ok = self.google_sheet_utils.overwrite_sheet_by_name(sheet, payload)
            if not ok:
                print(f"Error writing to Google sheet: {sheet}")
                return False # Error Writing to Google Sheets is bad, so returns False.

        return True # If it reaches here, non-empty Dataframes have been written fine.

    def download_google_sheets(self):
        """ Pull all named Google Sheets down into local CSV files. """
        sheet_names = ["Status", "Movements", "Armies", "Seasons"]
        directory   = self.local_sheet_utils.DIR

        for sheet in sheet_names:
            data = self.google_sheet_utils.get_sheet_by_name(sheet)
            if not data:
                print(f"No data from Google sheet: {sheet}")
                continue

            # First row = header
            header   = data[0]
            rows     = data[1:]
            df       = pd.DataFrame(rows, columns=header)

            ok = self.local_sheet_utils.update_sheet_by_name(sheet, df)
            if not ok:
                print(f"Error writing local CSV for: {sheet}")
        return True

    def change_game_status(self, status):
        """ Update the single-row Status.csv → Game Status column. """
        # 1) Read current file
        df = self.local_sheet_utils.get_sheet_by_name("Status")
        if df is None or df.empty:
            return False

        # 2) Modify in-memory
        df.loc[0, "Game Status"] = status

        # 3) Write it back
        return self.local_sheet_utils.update_sheet_by_name("Status", df)

    def change_season(self, season):
        """ Mark a new Current Season in Seasons.csv (only one 'x' per row). """
        season = season.capitalize()
        valid  = ["Spring", "Summer", "Autumn", "Winter", "Custom"]
        if season not in valid:
            return False

        # 1) Load
        df = self.local_sheet_utils.get_sheet_by_name("Seasons")
        if df is None:
            return False

        # 2) Clear all season markers on the 'Current Season' row
        mask = df["Army Type"] == "Current Season"
        for col in valid:
            df.loc[mask, col] = ""
        #    …then set our chosen season
        df.loc[mask, season] = "x"

        # 3) Save
        return self.local_sheet_utils.update_sheet_by_name("Seasons", df)

    def get_current_season_embed(self):
        """
        Returns a discord.Embed showing the current season and per‐army movement times,
        or None if no valid season is set.
        """
        df = self.local_sheet_utils.get_sheet_by_name("Seasons")
        if df is None:
            return None

        # 1) Find the 'Current Season' row
        cs_row = df[df["Army Type"] == "Current Season"]
        if cs_row.empty:
            return None
        cs = cs_row.iloc[0]

        # 2) Detect which column has the 'x'
        season = None
        valid_seasons = ["Spring", "Summer", "Autumn", "Winter", "Custom"]
        for col in valid_seasons:
            if str(cs[col]).strip().lower() == "x":
                season = col
                break
        if not season:
            return None

        # 3) Build column headings and data lists
        army_types = df[df["Army Type"] != "Current Season"]["Army Type"].tolist()
        # e.g. ["army", "has Siege", "has Ships", "cavalry"]

        # Now produce the movement‐times strings
        times = df[df["Army Type"] != "Current Season"][season].tolist()
        # e.g. [45, 60, 45, 30]

        # Format them with units:
        formatted_times = [f"{t} mins/hex" for t in times]

        # column_headings[0] will be used as Embed.title, others as field names
        column_headings = ["Season"] + army_types
        data            = [season] + formatted_times

        # 4) Generate and return the embed
        return self.embed_utils.set_info_embed_from_list(column_headings, data)
    
    async def update_custom_season_with_template(self, custom_times):
        # 1) Load the CSV
        df = self.local_sheet_utils.get_sheet_by_name("Seasons")
        if df is None:
            print("set_custom_movement_times: could not load Seasons.csv")
            return False

        # 2) Map template keys → CSV 'Army Type' values
        mapping = {
            "army":    "army",
            "siege":   "has Siege",
            "naval":   "has Ships",
            "cavalry": "cavalry"
        }

        # 3) Write each custom-time into the 'Custom' column
        for key, csv_name in mapping.items():
            if key not in custom_times:
                print(f"set_custom_movement_times: missing key '{key}'")
                return False

            # Ensure it’s an integer string (optional extra validation)
            try:
                val = int(custom_times[key])
            except ValueError:
                print(f"set_custom_movement_times: invalid integer for '{key}': {custom_times[key]}")
                return False

            # Place it into the DataFrame
            df.loc[df["Army Type"] == csv_name, "Custom"] = str(val)

        # 4) Persist the CSV
        ok = self.local_sheet_utils.update_sheet_by_name("Seasons", df)
        if not ok:
            print("set_custom_movement_times: failed to write Seasons.csv")
        return ok
        
