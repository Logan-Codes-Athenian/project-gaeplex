import csv
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils

class AdminService:
    def __init__(self):
        self.sheet_utils = GoogleSheetUtils()
        self.google_sheet_utils = GoogleSheetUtils()

    def update_google_sheets(self):
        sheet_names = ["status", "Movements"]
    
        for sheet in sheet_names:
            # Open the local CSV file and read its contents
            with open(f"src/sheets/{sheet}.csv", mode='r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)  # Convert the CSV rows into a list of lists

                # Write the data to the corresponding Google Sheet
                result = self.google_sheet_utils.overwrite_sheet_by_name(sheet, data)

                # Sheet does not Backup as expected.
                if not result:
                    return False
                
        # All Sheets Backup as expected.
        return True
    
    def change_game_status(self, status):
        try:
            # Read the CSV file
            with open(f"src/sheets/Status.csv", mode='r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)  # Convert the CSV rows into a list of lists

            # Loop through each row to find "Game Status" in the first column
            for row in data:
                if row[0] == "Game Status":
                    row[1] = status  # Update the second column with the new status
                    break  # Exit the loop once we've found and updated the row

            # Write the updated data back to the CSV file
            with open(f"src/sheets/Status.csv", mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)  # Write all rows back to the file

            return True
        except Exception:
            return False

