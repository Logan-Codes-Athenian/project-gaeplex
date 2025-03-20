import os
import pandas as pd
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils

class AdminService:
    def __init__(self):
        self.google_sheet_utils = GoogleSheetUtils()

    def update_google_sheets(self):
        sheet_names = ["Status", "Movements", "Armies"]

        for sheet in sheet_names:
            file_path = f"src/sheets/{sheet}.csv"
            try:
                # Read the CSV file using pandas.
                df = pd.read_csv(file_path, encoding='utf-8')
                # Prepend the header row (column names) to the list of data rows.
                data = [df.columns.tolist()] + df.values.tolist()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return False

            # Write the data (including headers) to the corresponding Google Sheet.
            result = self.google_sheet_utils.overwrite_sheet_by_name(sheet, data)
            if not result:
                return False

        # All sheets updated successfully.
        return True

    def download_google_sheets(self):
        sheet_names = ["Status", "Movements", "Armies"]
        directory = "src/sheets"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        for sheet in sheet_names:
            data = self.google_sheet_utils.get_sheet_by_name(sheet)
            if data:
                print(f"Downloading {sheet}.")
                # Assume the first row is the header.
                header = data[0]
                rows = data[1:]
                # Create the DataFrame with explicit column names.
                df = pd.DataFrame(rows, columns=header)
                file_path = f"{directory}/{sheet}.csv"
                try:
                    df.to_csv(file_path, index=False, encoding='utf-8')
                except Exception as e:
                    print(f"Error writing {file_path}: {e}")
        return True

    def change_game_status(self, status):
        file_path = "src/sheets/Status.csv"
        try:
            # Read the CSV normally so that pandas uses the first row as header.
            df = pd.read_csv(file_path, encoding='utf-8')
            # Update the value in the "Game Status" column in the first (and only) row.
            df.loc[0, "Game Status"] = status
            # Write the updated DataFrame back to CSV, preserving the header.
            df.to_csv(file_path, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error updating game status in {file_path}: {e}")
            return False
