from utils.sheets.LocalSheetUtils import LocalSheetUtils

class MovementUtils:
    def __init__(self):
        self.local_sheet_utils = LocalSheetUtils()

    def get_minutes_per_hex(self, movement):
        # 1) Load Seasons.csv
        df = self.local_sheet_utils.get_sheet_by_name("Seasons")
        if df is None or df.empty:
            raise RuntimeError("Could not load Seasons.csv")

        # 2) Find which column is marked 'x'
        cs = df[df["Army Type"] == "Current Season"]
        if cs.empty:
            raise RuntimeError("No 'Current Season' row in Seasons.csv")
        cs = cs.iloc[0]

        season_col = None
        for col in ["Spring", "Summer", "Autumn", "Winter", "Custom"]:
            if str(cs[col]).strip().lower() == "x":
                season_col = col
                break
        if season_col is None:
            raise RuntimeError("No season selected in Seasons.csv")

        # 3) Decide which Army Type to look up
        #    Note: movement.get("navy") etc. are lists, possibly ['None'] or empty.
        has_navy  = bool(movement.get("navy")) and movement.get("navy") != ["None"]
        has_siege = bool(movement.get("siege")) and movement.get("siege") != ["None"]

        # cavalry-only: every unit mention is cavalry-like AND no siege
        army_units = movement.get("army", [])
        cav_terms  = {"cavalry", "cav", "upstart noble band", "frankish knights"}
        cav_only   = (
            army_units
            and all(any(c in unit.lower() for c in cav_terms) for unit in army_units)
            and not has_siege
        )

        if has_navy:
            lookup_row = "has Ships"
        elif has_siege:
            lookup_row = "has Siege"
        elif cav_only:
            lookup_row = "cavalry"
        else:
            lookup_row = "army"

        # 4) Extract the minutes-per-hex from the DataFrame row
        series = df.loc[df["Army Type"] == lookup_row, season_col]
        if series.empty:
            raise RuntimeError(f"No row '{lookup_row}' in Seasons.csv")
        
        raw = series.iloc[0]
        try:
            # allow floats, strings like "1.0", numeric types, etc.
            minutes = int(float(raw))
        except Exception:
            raise RuntimeError(
                f"Invalid numeric value in Seasons.csv at {lookup_row}/{season_col}: {raw!r}"
            )
        
        return minutes

        
    def get_army_breakdown(self, army_uid):
        # Retrieve the Armies sheet as a DataFrame
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            print("Army DF is Empty..")
            return False, ["nan"], ["nan"], ["nan"], ["nan"], ["nan"]

        # Locate the row where the 'Army UID' matches the provided army_uid
        army = armies_df[armies_df['Army UID'] == army_uid]
        if army.empty:
            print("Army UID info empty")
            return False, ["nan"], ["nan"], ["nan"], ["nan"], ["nan"]

        # Get the first matching row
        row = army.iloc[0]
        print(f"Row:\n{row}")
        
        # Retrieve the breakdown values; defaulting to "None" if a column is missing or empty
        commanders = row.get('Commanders', "nan")
        current_hex = row.get('Current Hex', False)
        troops = row.get('Troops', "nan")
        navy = row.get('Navy', "nan")
        siege = row.get('Siege', "nan")

        # Ensure the values are strings before attempting to split.
        commanders = str(commanders)
        troops = str(troops)
        navy = str(navy)
        siege = str(siege)

        # Convert comma-separated strings into lists, stripping any extra spaces.
        commanders_list = [item.strip() for item in commanders.split(',')] if commanders != "None" else ["nan"]
        troops_list = [item.strip() for item in troops.split(',')] if troops != "None" else ["nan"]
        navy_list = [item.strip() for item in navy.split(',')] if navy != "None" else ["nan"]
        siege_list = [item.strip() for item in siege.split(',')] if siege != "None" else ["nan"]

        print(True, commanders_list, current_hex, troops_list, navy_list, siege_list)
        return True, commanders_list, current_hex, troops_list, navy_list, siege_list
