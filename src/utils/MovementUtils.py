from utils.sheets.LocalSheetUtils import LocalSheetUtils

class MovementUtils:
    def __init__(self):
        self.local_sheet_utils = LocalSheetUtils()

    def get_minutes_per_hex(self, troops_list, navy_list, siege_list):
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
        has_navy = navy_list and navy_list != ["nan"] and navy_list != ["None"]
        has_siege = siege_list and siege_list != ["nan"] and siege_list != ["None"]

        cav_keywords = {"cavalry", "cav", "upstart noble band", "frankish knights"}

        def is_cavalry(unit_str):
            unit_str = unit_str.strip().lower()
            parts = unit_str.split()
            unit_type = " ".join(parts[1:]) if len(parts) > 1 else parts[0]
            return any(term in unit_type for term in cav_keywords)

        cav_only = troops_list and all(is_cavalry(unit) for unit in troops_list) and not has_siege

        print(f"[DEBUG] Parsed Troops: {troops_list}, Cav-only: {cav_only}")

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
            minutes = int(float(raw))  # supports strings like "60.0"
        except Exception:
            raise RuntimeError(
                f"Invalid numeric value in Seasons.csv at {lookup_row}/{season_col}: {raw!r}"
            )

        return minutes

    def get_army_breakdown(self, army_uid):
        armies_df = self.local_sheet_utils.get_sheet_by_name("Armies")
        if armies_df is None or armies_df.empty:
            print("Army DF is Empty..")
            return False, ["nan"], ["nan"], ["nan"], ["nan"], ["nan"]

        army = armies_df[armies_df['Army UID'] == army_uid]
        if army.empty:
            print("Army UID info empty")
            return False, ["nan"], ["nan"], ["nan"], ["nan"], ["nan"]

        row = army.iloc[0]
        print(f"Row:\n{row}")

        # Fetch raw values
        commanders = row.get('Commanders', "nan")
        current_hex = row.get('Current Hex', False)
        troops = row.get('Troops', "nan")
        navy = row.get('Navy', "nan")
        siege = row.get('Siege', "nan")

        # Normalize to strings
        commanders = str(commanders)
        troops = str(troops)
        navy = str(navy)
        siege = str(siege)

        # Parse lists from CSV string values
        def parse_list(value):
            return [item.strip() for item in value.split(',')] if value.lower() not in {"none", "nan"} else ["nan"]

        commanders_list = parse_list(commanders)
        troops_list = parse_list(troops)
        navy_list = parse_list(navy)
        siege_list = parse_list(siege)

        print(True, commanders_list, current_hex, troops_list, navy_list, siege_list)
        return True, commanders_list, current_hex, troops_list, navy_list, siege_list
