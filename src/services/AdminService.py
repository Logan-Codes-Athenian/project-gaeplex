import csv
from utils.sheets.GoogleSheetUtils import GoogleSheetUtils

class AdminService:
    def __init__(self):
        self.sheet_utils = GoogleSheetUtils()

    def update_google_sheets(self):
        sheet_names = ["Movements"]
    
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