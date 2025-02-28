import os
import pandas as pd
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils

class AdminService:
    def __init__(self):
        self.google_sheet_utils = GoogleSheetUtils()

    def update_google_sheets(self):
        sheet_names = ["Status", "Movements"]
    
        for sheet in sheet_names:
            file_path = f"src/sheets/{sheet}.csv"
            try:
                # Read the CSV file using pandas.
                df = pd.read_csv(file_path, encoding='utf-8')
                # Convert the DataFrame into a list of lists.
                data = df.values.tolist()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return False

            # Write the data to the corresponding Google Sheet.
            result = self.google_sheet_utils.overwrite_sheet_by_name(sheet, data)
            if not result:
                return False
                
        # All sheets updated successfully.
        return True

    def download_google_sheets(self):
        sheet_names = ["Status", "Movements"]
        directory = "src/sheets"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        for sheet in sheet_names:
            data = self.google_sheet_utils.get_sheet_by_name(sheet)
            if data:
                print(f"Downloading {sheet}.")
                # Convert the downloaded data (assumed to be a list of lists) into a DataFrame.
                df = pd.DataFrame(data)
                file_path = f"{directory}/{sheet}.csv"
                try:
                    df.to_csv(file_path, index=False, encoding='utf-8')
                except Exception as e:
                    print(f"Error writing {file_path}: {e}")
        return True

    def change_game_status(self, status):
        file_path = "src/sheets/Status.csv"
        try:
            # Read the Status.csv without a header (assuming the first column is the label).
            df = pd.read_csv(file_path, header=None, encoding='utf-8')
            # Update the second column for the row where the first column is "Game Status".
            df.loc[df[0] == "Game Status", 1] = status
            # Write the updated DataFrame back to the CSV file without headers.
            df.to_csv(file_path, index=False, header=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error updating game status in {file_path}: {e}")
            return False
