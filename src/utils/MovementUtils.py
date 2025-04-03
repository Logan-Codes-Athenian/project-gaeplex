from utils.sheets.LocalSheetUtils import LocalSheetUtils

class MovementUtils:
    def __init__(self):
        self.local_sheet_utils = LocalSheetUtils()

    def get_minutes_per_hex(self, movement):
        # Determine base minutes per hex based on composition.
        print(f"get_minutes_per_hex for:\n{movement}")

        print(movement.get("navy"))

        # Check if navy is not equal to ['None']
        if movement.get("navy") != ['None']:
            print(30)
            return 1 # TODO: CHANGE THIS TO 30 AGAIN
        
        # Since army is already a list, no need to split
        army_units = movement.get("army", [])
        print(f"Army Units:\n{army_units}")
        cav_terms = {"cavalry", "cav", "upstart noble band", "frankish knights"}
        
        # Check if army is not empty and all elements are cavalry-related
        cav_only = bool(army_units) and all(
            any(cav in unit.lower() for cav in cav_terms) for unit in army_units
        )
        print(f"Cav Only: {cav_only}")
        
        if cav_only and movement.get("siege") == ['None']:
            print(15)
            return 1 # TODO: CHANGE THIS TO 15 AGAIN
        elif movement.get("siege") != ['None']:
            print(60)
            return 1 # TODO: CHANGE THIS TO 60 AGAIN
        else:
            print(30)
            return 1 # TODO: CHANGE THIS TO 30 AGAIN
        
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
